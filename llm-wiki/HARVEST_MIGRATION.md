# HARVEST_MIGRATION — Data Wiki HarvestからProject Knowledge Harvestへの改修仕様

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`
>
> このドキュメントは本プロジェクトで最重要の実装仕様。AWSインフラではなく、**Harvest Agentの知能をData Wiki向けからProject Knowledge向けへどう置き換えるか**を定義する。

## 1. 目的

元RepoのHarvestは、Glue / Athena / Redshiftを調査してDataset / Table / Metric / Join等のData Wikiを生成する。

今回のTargetは、複数種類のProject Sourceを読み、既存Wikiと照合しながらProject Knowledgeを継続編集すること。

```text
Before
Data Sources
  ↓
Data Understanding
  ↓
Dataset / Table Knowledge Authoring

After
Project Sources
  ↓
Evidence Understanding
  ↓
Knowledge Candidate Extraction
  ↓
Existing Knowledge Comparison
  ↓
Knowledge Reconciliation
  ↓
Project Knowledge Authoring
```

最重要ポイントは、SourceごとのMarkdownを作ることではなく、**同一KnowledgeをSourceをまたいで継続管理すること**。

## 2. 再利用するHarvest基盤

元Repoから可能な限り以下を継承する。

```text
deepagents supervisor
LangGraph
FilesystemBackend
OKFGuardMiddleware
LinkGraph
subagent fan-out
reviewer pattern
S3 Files / bundle publish
CloudWatch / OpenTelemetry tracing
safe publish / versioning
```

つまりAgent Framework自体は原則変更しない。

変更するのは主に以下。

```text
Source model
Domain model
Authoring skill
System / subagent prompts
Grounding tools
Reconciliation logic
Reviewer criteria
```

## 3. 元Repo固有機能の置換マップ

| Data Wiki側 | Project Knowledge側 |
|---|---|
| Glue database | Project |
| Table | Knowledge Concept / Artifact / Source |
| Column | Source detail / Requirement detail等 |
| Metric | Requirement / Decision / Project rule等 |
| Join | Knowledge relation / Link |
| Glue metadata snapshot | Normalized Evidence snapshot |
| `run_sql` | Source / Managed KB evidence verification |
| `sample_rows` | Source excerpt / evidence lookup |
| table-author | knowledge-author |
| cross-dataset discovery | cross-source / cross-knowledge reconciliation |
| Data reviewer | Project Knowledge reviewer |
| dataset bundle | project knowledge bundle |

これは単純な名前置換ではない。Data Wikiの「正しいData semanticsを調査する」知能を、Project Wikiの「Source間の意味を統合する」知能へ置き換える。

## 4. Source Adapter Architecture

Harvest本体をSource Typeから分離する。

```text
                    SourceAdapter
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   MeetingAdapter   DocumentAdapter   FutureAdapter
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Normalized Evidence
```

### 4.1 MVP Adapters

#### MeetingAdapter

対象:

- 議事録Markdown
- 議事録PDF
- 議事録DOCX
- 会議PPTX / report

抽出候補:

```text
meeting date
participants
agenda
statements
conclusions
open questions
action statements
source sections
```

#### DocumentAdapter

対象:

- specification
- design document
- report
- presentation

抽出候補:

```text
document title
version
section headings
requirements
decisions / rationale
constraints
risks
issues
references
```

### 4.2 Normalized Evidence Contract

Source Adapterは最低限次の形へ正規化する。

```yaml
source_id: stable-source-id
source_type: meeting | specification | design | report | other
project: project-a
source_uri: s3://... or original URI
title: ...
occurred_at: 2026-08-08T...
created_at: ...
authors: []
participants: []
content: |
  normalized source text
metadata: {}
```

必要ならSection単位のEvidence locatorを持つ。

```yaml
sections:
  - section_id: sec-001
    heading: Architecture Decision
    text: ...
    source_locator: page=4 / heading=...
```

## 5. Knowledge Model

MVPのKnowledge Typeは以下。

```text
Project
Topic
Decision
Requirement
Action
Risk
Issue
Artifact
Meeting
```

### 5.1 Project

Project全体の入口。

### 5.2 Topic

複数Sourceをまたぐ継続テーマ。

例:

```text
Authentication architecture
AgentCore Gateway integration
Production rollout
```

### 5.3 Decision

「何を決めたか」を継続管理する。

推奨Lifecycle:

```text
proposed → active → superseded / cancelled
```

必須要素候補:

```yaml
decision_id:
title:
status:
decision:
rationale:
decided_at:
project:
sources: []
related_topics: []
related_requirements: []
updated_at:
```

### 5.4 Requirement

要求 / 制約 / acceptance criteria。

推奨Lifecycle:

```text
draft → active → changed / retired
```

### 5.5 Action

```text
open → in_progress → done / cancelled
```

### 5.6 Risk

将来起こり得る事象。

```text
open → mitigated / accepted / closed
```

### 5.7 Issue

既に発生している問題。

```text
open → investigating → resolved / closed
```

### 5.8 Artifact

仕様書、設計書、成果物等のProject資産。

### 5.9 Meeting

会議そのものを表現し、Decision / Action / Topicへの入口とする。

## 6. Stable ID Strategy

Source filenameをKnowledge IDにしない。

悪い例:

```text
decision-2026-08-08-gateway.md
```

会議ごとにDecisionが増殖する。

良い例:

```text
decisions/adopt-agentcore-gateway.md
```

同一Knowledgeを継続更新する。

ID生成は次を組み合わせる。

```text
project
knowledge type
normalized subject / canonical key
known aliases
existing semantic match
```

LLMだけにID決定を完全委譲しない。

## 7. Harvest Agent Logical Architecture

推奨論理構成:

```text
Project Knowledge Harvest Supervisor
        │
        ├─ Source Analyst
        │    └─ normalized evidence理解
        │
        ├─ Knowledge Extractor / Author
        │    └─ candidate knowledge生成
        │
        ├─ Knowledge Reconciler
        │    └─ existing Wikiとの比較・更新判定
        │
        ├─ Link Builder
        │    └─ relationships生成
        │
        └─ Reviewer
             └─ evidence / duplicate / conflict / schema検証
```

実装上は必ずしも5 Agentに分ける必要はない。

元Repoのsubagent fan-outを活かしつつ、責務を分離する。

## 8. Recommended Subagent Design

### 8.1 `source-analyst`

役割:

- Sourceの種類を理解
- Section構造を整理
- Project contextを把握
- Candidate extractionに必要なEvidenceを提示

書き込み権限は不要でもよい。

### 8.2 `knowledge-author`

役割:

- Project Knowledge Candidateを作る
- Source locator / provenanceを付ける
- Type / status / related conceptsを提案

### 8.3 `knowledge-reconciler`

最重要。

役割:

- Existing Wiki検索
- candidate同一性判定
- CREATE / UPDATE / REINFORCE / CONFLICT / IGNORE決定
- lifecycle変更判定
- history preservation

### 8.4 `reviewer`

役割:

- Evidenceにない事実を作っていないか
- Duplicateがないか
- lifecycleが不正でないか
- Conflictを隠していないか
- Sourceがあるか
- Link / frontmatterが正しいか

## 9. Existing Wiki Search Strategy

新SourceからCandidateを抽出した後、必ず既存Wikiを検索する。

探索順序の推奨:

```text
1. stable ID / canonical key
2. exact / normalized title
3. same project + same knowledge type
4. S3 Vectors semantic_search
5. backlinks / related topic context
6. read_pageで候補本文確認
```

Semantic similarityだけで同一Knowledgeと確定しない。

同一性判定には、project / type / subject / lifecycle / source / linksを使う。

## 10. Reconciliation Decision Contract

Reconcilerは明示的な結果を返す。

```yaml
action: CREATE | UPDATE | REINFORCE | CONFLICT | IGNORE
knowledge_type: Decision
target_concept_id: decisions/adopt-agentcore-gateway
confidence: 0.93
reason: same project and subject; new source changes status from proposed to active
source_evidence:
  - source_id: meeting-2026-08-08
    locator: decision-section
changes:
  status:
    from: proposed
    to: active
  add_sources:
    - meeting-2026-08-08
review_required: false
```

Reconciliation結果自体をTraceへ残す。

## 11. CREATE Rules

CREATEは以下の場合。

- 同一Project内に同一Knowledge候補がない
- semantic candidateがあってもSubjectが異なる
- lifecycle上別Conceptとして扱うべき

CREATE時も既存Topic / Project / Artifact等へのLinkを生成する。

## 12. UPDATE Rules

UPDATE例:

- Decision statusがproposed → active
- Requirement内容がVersion更新で変更
- Action due date / owner / statusが変更
- Issue statusがinvestigating → resolved

UPDATE時:

- old Sourceを削除しない
- previous state / historyを保持
- updated_atを更新
- new sourceを追加

## 13. REINFORCE Rules

同じKnowledgeを別Sourceが裏付ける場合。

例:

```text
Meeting: Gateway採用
Spec: Gatewayを正式architectureとして記載
```

結果:

```text
Decisionを新規作成しない
sourcesへSpec追加
verified状態を必要に応じて更新
ArtifactとのLink追加
```

## 14. CONFLICT Rules

例:

```text
Meeting A: Cognitoを採用
Spec v3: Cognitoは使用しない
```

自動で片方を消さない。

最低限:

```yaml
status: conflict
conflicting_sources: []
current_state: ...
proposed_state: ...
review_required: true
```

Decision lifecycleとして明確な後続決定が確認できる場合はUPDATE / supersedeとして扱えるが、曖昧ならCONFLICT。

## 15. IGNORE Rules

以下はKnowledge Pageを作らない候補。

- 単なる挨拶
- 重複した言い換え
- Project状態へ影響しない一時的会話
- Source内だけで完結し、再利用価値がない細部

ただし原文はManaged KBに残るため、Wikiに落とさなくてもEvidence retrieval可能。

## 16. Decision Lifecycle Example

### Source 1

```text
2026-08-01 Meeting
Gatewayを使う方向で検討する
```

結果:

```text
CREATE Decision
status = proposed
```

### Source 2

```text
2026-08-08 Meeting
AgentCore Gatewayを正式採用する
```

結果:

```text
UPDATE same Decision
proposed → active
add source
```

### Source 3

```text
Architecture Spec v3
Gateway経由でManaged KBとWiki MCPを利用する
```

結果:

```text
REINFORCE same Decision
add Artifact link
add source
```

### Source 4

```text
2026-08-15 Meeting
Gateway案を撤回する
```

結果:

```text
UPDATE same Decision
active → cancelled
keep full source history
```

## 17. Requirement Lifecycle Example

```text
Spec v1: response latency < 5 sec
Spec v2: response latency < 3 sec
```

同一RequirementとしてUPDATEし、旧値とSource履歴を保持する。

単純に`requirement-latency-v1.md` / `v2.md`を乱造しない。

## 18. Meeting Processing Policy

MeetingはMVPで重要なSource Typeだが、Meeting中心にKnowledge Modelを設計しない。

Meeting処理:

```text
Meeting Source
  ↓
Meeting Page
  +
Topic candidates
Decision candidates
Action candidates
Risk / Issue candidates
Requirement candidates when present
```

Meeting PageはSource単位なので毎会議作成してよい。

一方Topic / Decision / Requirement / Risk等は会議をまたいでReconcileする。

## 19. Document Processing Policy

仕様書・設計書もMeetingと同じPipelineへ入れる。

```text
Spec / Design Doc
  ↓
Artifact Page
  +
Requirement candidates
Decision candidates
Risk / Issue candidates
Topic candidates
```

Meeting SourceだけがKnowledge生成の中心ではない。

## 20. Grounding Strategy

元RepoのData Wikiでは、Catalog metadataだけでなく`run_sql` / `sample_rows`で事実確認する。

Project WikiではGroundingを次へ置き換える。

```text
Primary
- Source text / section
- Source metadata / locator

Secondary
- Existing Project Wiki
- Existing Managed KB raw retrieval
```

重要なclaimをSource EvidenceなしでAuthoringしない。

## 21. Managed KBとの関係

Harvest時も必要に応じてManaged KBをEvidence lookupとして使えるが、Managed KBをKnowledge Authoringの正本にはしない。

```text
Raw Source / Managed KB = Evidence
Project Wiki            = Compiled Knowledge
```

HarvestでSourceが直接利用可能な場合は直接Sourceを優先し、Managed KBはcross-source verificationや原文探索に使う。

## 22. Link Generation Rules

推奨Link:

```text
Project → Topics / Decisions / Requirements / Risks / Issues
Topic → Decisions / Requirements / Meetings / Artifacts
Decision → Topic / Requirement / Artifact / Meeting / Issue
Requirement → Decision / Artifact / Risk / Issue
Action → Decision / Meeting / Issue
Risk → Requirement / Decision / Mitigation Artifact
Issue → Decision / Requirement / Action / Meeting
Artifact → Requirements / Decisions / Topics
Meeting → Decisions / Actions / Topics / Issues
```

MVPではLink Typeを厳密なOntologyとしてDBへ登録しない。

## 23. Reviewer Policy

Reviewerは最低限以下をFail条件として扱う。

```text
Hallucinated claim
Missing source provenance
Duplicate concept creation
Silent conflict overwrite
Invalid lifecycle transition
Broken link
Missing required frontmatter
Source locator mismatch
Project scope mismatch
```

重要なDecision / Requirement / Riskの低confidence変更はHuman Reviewへ回せる設計にする。

## 24. Safe Publish

元Repoの「published bundleを壊さない」設計を維持する。

```text
Working bundle
  ↓
Author
  ↓
Reconcile
  ↓
Review
  ↓
Guard / Lint
  ↓
Finalize
  ↓
Published bundle
```

途中失敗では現行published Wikiを変更しない。

## 25. Incremental Processing

同一Source再投入はidempotentにする。

Source fingerprint / source_idを使い、同じSourceによるSource重複追加を防ぐ。

Source更新時:

```text
same source_id + new version
  ↓
re-extract
  ↓
reconcile affected knowledge only
```

可能であれば全Wiki再生成を避ける。

## 26. S3 Vectorsとの関係

S3 VectorsはKnowledge ReconcilerのExisting Wiki Candidate Searchにも利用する。

```text
Candidate Knowledge text
  ↓
semantic_search
  ↓
possible existing concepts
  ↓
read_page
  ↓
Reconciler decision
```

つまりS3 VectorsはChat検索だけでなくHarvestのDuplicate Controlにも有効。

## 27. Prompt / Skill Design

Authoring methodologyはPromptへ巨大に埋め込むのではなく、元Repoと同様Skillへ分離する。

推奨:

```text
skills/project-knowledge-authoring/
  SKILL.md
  references/
    knowledge-model.md
    reconciliation.md
    provenance.md
    lifecycle.md
    review-rules.md
    source-adapters.md
```

PromptにはRuntime factsと現在のTaskだけを渡す。

## 28. Observability

Traceで最低限以下を見えるようにする。

```text
source_id
project
candidate count
existing candidate ids
reconciliation action
reconciliation reason / confidence
created concepts
updated concepts
conflicts
review findings
publish status
```

LLM trajectoryだけでなくReconciliation Decisionが監査可能であることが重要。

## 29. Test Strategy

### Unit

- Source Adapter parse
- stable ID / normalization
- lifecycle transition
- reconciliation deterministic rules
- source dedup
- frontmatter validation

### Agent / Golden Tests

代表Source Setを固定する。

```text
Meeting A: Gateway検討
Meeting B: Gateway採用
Spec v3: Gateway architecture記載
Issue: Gateway認証問題
Meeting C: Gateway撤回
```

期待結果:

```text
Decision Page = 1
Decision lifecycle preserved
Sources = all relevant sources
Artifact link present
Issue linked
No duplicate Decision
Conflict / update correctly classified
```

### E2E

```text
Source ingest
→ Harvest
→ S3 OKF
→ Link/Backlink
→ S3 Vectors
→ Wiki MCP
→ Gateway
→ Chat Agent
→ Managed KB verification
→ Citation answer
```

## 30. Migration Order

```text
1. Baseline固定
2. Project Knowledge schema
3. Source Adapter
4. Meeting inputでKnowledge extraction
5. Existing Wiki search
6. Knowledge Reconciler
7. Reviewer / safe publish
8. Document inputを同Pipelineへ追加
9. S3 Vectors duplicate search確認
10. Gateway / Chat / Managed KB E2E
```

MeetingだけでPhase 4〜7を完成させ、その後DocumentAdapterを追加する。

これによりPoCは早く作れる一方、設計はMeeting専用にならない。

## 31. Definition of Done for Harvest Migration

Harvest改修の完成条件:

- [ ] Source Adapter abstractionがある
- [ ] Meeting以外のDocumentも同じNormalized Evidenceへ変換できる
- [ ] Project Knowledge Candidateを抽出できる
- [ ] Existing Wikiを必ず検索する
- [ ] CREATE / UPDATE / REINFORCE / CONFLICT / IGNOREを判定する
- [ ] Decision / Requirement等のLifecycleを保持する
- [ ] Duplicate Pageを抑制する
- [ ] Source provenance / locatorを保持する
- [ ] Linkを生成する
- [ ] Reviewerがhallucination / duplicate / conflictを検査する
- [ ] Harvest失敗でpublished Wikiを壊さない
- [ ] Reconciliation DecisionをTraceできる

## 32. Final Principle

> **議事録をWiki化するのではなく、Project SourceをEvidenceとして読み、既存Knowledgeと照合しながらProjectの「現在の理解」を継続編集する。**

このHarvest Reconciliation品質がProject Knowledge Wiki全体の価値を決める。
