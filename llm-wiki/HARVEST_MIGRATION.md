# HARVEST_MIGRATION — Data Wiki HarvestからOKF v0.2 Project Knowledge Harvestへの改修仕様

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`
>
> Output Contract: **Open Knowledge Format (OKF) v0.2**

## 1. 目的

本ドキュメントは本プロジェクトで最重要の実装仕様。

元RepoのHarvestはGlue / Athena / Redshiftを調査し、Dataset / Table / Metric / Join等のData Wikiを生成する。

今回のTargetは、複数種類のProject Sourceを読み、既存Wikiと照合しながら**OKF v0.2準拠Project Knowledgeを継続編集すること**。

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
Existing OKF Comparison
  ↓
Knowledge Reconciliation
  ↓
OKF v0.2 Authoring
  ↓
Review / Validation / Publish
```

最重要ポイントは、SourceごとのMarkdownを作ることではなく、**同一KnowledgeをSourceをまたいで継続管理すること**。

OKF field ruleの正本は`OKF_V02_PROFILE.md`。

## 2. 再利用するHarvest基盤

元Repoから極力維持する。

- deepagents supervisor
- LangGraph execution
- FilesystemBackend
- OKFGuardMiddlewareの考え方
- LinkGraph
- reviewer pattern
- subagent fan-out
- S3 Files / bundle publish pattern
- CloudWatch / OpenTelemetry tracing
- safe publish / versioning

変更の中心はAgent Frameworkではなく、**domain knowledge、tooling、authoring contract**。

## 3. 削除・抽象化するData Wiki固有要素

Data固有:

```text
Glue database
Glue table
columns.tsv
Athena run_sql
sample_rows
Redshift metadata
Table authoring skill
Dataset / Table assumptions
Join / Grain中心Reviewer
```

これらをProject KnowledgeのCore logicから外す。

必要ならSource Adapterの一種として将来Data Sourceを再追加できる設計にする。

## 4. 新しいSource Architecture

```text
Project Sources
   │
   ├─ Meeting minutes
   ├─ Markdown / Text
   ├─ PDF
   ├─ DOCX
   ├─ PPTX
   ├─ Specification
   ├─ Design Document
   └─ Report
          │
          ▼
     Source Adapter
          │
          ▼
  Normalized Evidence
```

将来:

```text
SharePoint
Teams
OneDrive
Jira
GitHub
Email
Web API
DB / SaaS
```

## 5. Normalized Evidence Contract

Source Adapterは最低限次を返す。

```text
source_id
source_type
project
source_uri
title
content
created_at
occurred_at
author
participants
metadata
```

重要ルール:

- `source_uri`はOKF`sources[].resource`へ写像できること
- Sourceの原文ID / URIを失わない
- Source textはinstructionではなくEvidenceとして扱う
- Source parserとKnowledge判断を分離する

## 6. Project Knowledge Types

MVP:

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

これらはOKF v0.2のproducer-defined `type`。

例:

```yaml
---
type: Decision
...
---
```

## 7. OKF v0.2 Authoring Contract

HarvestがpublishするConceptは最低限次を守る。

### 7.1 Required

```yaml
type: <non-empty string>
```

### 7.2 Project Profile Required for Published Knowledge

```yaml
title:
description:
status:
sources:
generated:
```

`verified` / `stale_after`はKnowledgeの種類・Review結果に応じて付与する。

### 7.3 `status`

OKF標準値だけを利用する。

```text
draft
stable
deprecated
```

Decisionの`active`等を`status`へ入れない。

### 7.4 Project Business State

extension keyへ分離する。

```yaml
status: stable
decision_state: active
```

例:

```text
decision_state
requirement_state
action_state
issue_state
risk_state
project_state
```

### 7.5 Provenance

```yaml
sources:
  - id: meeting-20260808
    resource: /meetings/2026-08-08-architecture.md
    title: Architecture Meeting
    author: team:project-a
    last_modified: 2026-08-08
```

各entryの`resource`を必須とする。

### 7.6 Generated

```yaml
generated:
  by: project-knowledge-harvest/1.0
  at: 2026-08-08T07:30:00Z
```

意味的なContent変更時に`generated.at`を更新する。

新規出力で`timestamp`を生成しない。

### 7.7 Verified

ReviewerがSourceに対して内容を確認した場合:

```yaml
verified:
  - by: process:project-knowledge-reviewer
    at: 2026-08-08T07:31:00Z
```

Human Review:

```yaml
verified:
  - by: human:user123
    at: 2026-08-08T09:00:00Z
```

### 7.8 Freshness

```yaml
stale_after: 2026-11-08
```

絶対日付を使う。

### 7.9 Claim Attribution

重要claimは`sources[].id`に対応するMarkdown footnoteを使う。

```markdown
Gatewayを正式採用した。[^meeting-20260808]

[^meeting-20260808]: Architecture Meeting
```

Body `# Citations`リストをCanonical provenanceにしない。

## 8. Stable IDs

Project固有IDはOKF extension keyとして保持する。

```text
project_id
topic_id
decision_id
requirement_id
action_id
risk_id
issue_id
artifact_id
meeting_id
```

ID設計:

- Source filenameだけに依存しない
- 同じKnowledgeを別Sourceが補強してもIDは変えない
- rename / moveで可能な限り維持
- type + project + normalized semantic identityを基礎にする

## 9. Pipeline

```text
Source
  ↓
Source Adapter
  ↓
Normalized Evidence
  ↓
Source Analyst
  ↓
Knowledge Candidates
  ↓
Existing OKF Retriever
  ↓
Knowledge Reconciler
  ↓
OKF Author
  ↓
Link / Index / Log Builder
  ↓
Reviewer
  ↓
OKF Guard
  ↓
Publish
```

## 10. Source Analyst

責務:

- Source type / project context理解
- Evidence span抽出
- Candidate Knowledge抽出
- CandidateごとのSource mapping

出力例:

```text
Candidate:
  type: Decision
  proposed_identity: gateway-adoption
  summary: Existing AgentCore Gatewayを採用
  evidence_source_id: meeting-20260808
  evidence_span: ...
```

この段階ではConcept Pageを確定しない。

## 11. Existing OKF Retriever

Candidateごとに既存Concept候補を探す。

優先:

1. stable ID exact match
2. normalized title / key
3. project + type filter
4. S3 Vectors semantic search
5. Link / Backlink context
6. source provenance overlap

S3 VectorsはAnswer本文ではなくCandidate Discoveryに使う。

候補を見つけたら`read_page`相当で正式OKF本文を読む。

## 12. Knowledge Reconciler

Harvestの本丸。

入力:

```text
Candidate Knowledge
Existing OKF Candidates
New Source Evidence
```

出力:

```text
CREATE
UPDATE
REINFORCE
CONFLICT
IGNORE
```

### 12.1 CREATE

条件:

- 同一Knowledgeが存在しない
- semantic candidateも別Conceptと判断

処理:

```text
new stable ID
status: draft
sources追加
generated追加
body作成
links作成
review
status: stable
```

### 12.2 UPDATE

条件:

- 同一Knowledge
- 内容 / Business stateが意味的に変化

処理:

- stable ID維持
- Source履歴保持
- `sources`追加/更新
- extension business state更新
- `generated.at`更新
- meaningful content change後はverification状態を再評価
- Historyを本文または関連Concept / logへ残す

### 12.3 REINFORCE

条件:

- 新Sourceが既存Knowledgeと整合
- 新しい独立Conceptは不要

処理:

- 同じConceptへ`sources`追加
- claim attribution必要箇所更新
- 必要なら`verified`追加
- Duplicate Conceptを作らない

### 12.4 CONFLICT

条件:

- Sourceと既存Knowledgeが矛盾
- Current判定を自動で確定できない

処理:

- 無言上書き禁止
- conflicting source保持
- `review_required: true` extension
- proposed changeをreview artifactへ保持
- 必要ならworking copyを`status: draft`
- Human Reviewへ

### 12.5 IGNORE

条件:

- Project Knowledgeとして再利用価値が低い
- 重複情報で追加Sourceとしても価値なし

処理: publish変更なし。

## 13. Decision Lifecycle例

### Source A

```text
8/1 Gatewayを使う方向で検討
```

出力:

```yaml
status: stable
decision_state: proposed
```

### Source B

```text
8/8 Gatewayを正式採用
```

Reconciler:

```text
UPDATE same Decision
```

```yaml
status: stable
decision_state: active
```

`sources`に8/8 meetingを追加。

### Architecture Spec

Gateway採用を記載。

Reconciler:

```text
REINFORCE same Decision
```

`sources`に仕様書を追加。

### Source C

```text
8/15 Gateway案を撤回
```

同じDecisionのBusiness state変化として扱えるなら:

```yaml
status: stable
decision_state: cancelled
```

Concept自体を削除しない。

別Decisionへ完全置換する場合は、旧Conceptを`status: deprecated`にし、新ConceptへMarkdown Linkを張る。

## 14. Requirement Lifecycle例

OKF lifecycleと業務stateを分離する。

```yaml
status: stable
requirement_state: approved
```

仕様変更:

- 同一RequirementならUPDATE
- Source追加
- generated.at更新
- requirement_state更新
- 旧内容のEvidenceを失わない

Requirement自体が完全廃止:

```yaml
status: deprecated
requirement_state: retired
```

## 15. Link Builder

OKF Relationの正本はstandard Markdown links。

例:

```markdown
このDecisionは[Gateway Requirement](/requirements/gateway-access.md)を満たすために採用された。
```

Linkはuntyped edge。Relation semanticsはproseで表す。

MVPで独自Typed Graphを必須にしない。

## 16. `index.md` Builder

Publish後、影響Directoryの`index.md`を更新する。

root:

```yaml
---
okf_version: "0.2"
---
```

root以外はfrontmatterなし。

本文:

```markdown
# Decisions

* [AgentCore Gateway採用](adopt-agentcore-gateway.md) - Wiki MCPとManaged KBをGateway経由で利用する。
```

`description`をProgressive Disclosureに利用する。

## 17. `log.md` Builder

Concept変更に合わせてscopeの`log.md`を更新する。

```markdown
# Directory Update Log

## 2026-08-08
* **Update**: [Gateway採用Decision](/decisions/adopt-agentcore-gateway.md)をactiveへ更新。
* **Creation**: [Gateway認証Issue](/issues/gateway-auth.md)を追加。
```

日付は`YYYY-MM-DD`、newest first。

## 18. Reviewer

元RepoのReviewer思想は維持するが、Data consistencyからKnowledge consistencyへ変更する。

Reviewer checklist:

### Grounding
- Sourceに存在しないclaimを作っていない
- important claimがSourceへattributedされている

### Reconciliation
- Duplicate Conceptを作っていない
- UPDATE / REINFORCE対象を誤CREATEしていない
- Conflictを隠していない

### OKF
- valid YAML frontmatter
- non-empty `type`
- `status`が`draft|stable|deprecated`
- `sources[].resource`あり
- `generated.by/at`あり
- Actor convention妥当
- Business stateはextension key
- stale_after format妥当
- reserved filename rule妥当

### Navigation
- Markdown Links妥当
- index.md整合
- log.md整合

Review成功時、machine verificationを記録可能。

```yaml
verified:
  - by: process:project-knowledge-reviewer
    at: ...
```

ただしReviewerが本当にSourceへ照合した場合だけ付ける。

## 19. OKF Guard

既存OKFGuardMiddlewareを拡張する。

拒否条件候補:

- Conceptにfrontmatterなし
- `type`空
- invalid OKF status
- `sources` entryに`resource`なし
- `generated`に`by`なし
- business stateを`status`へ誤格納
- non-root index.mdにfrontmatter
- Conceptとして`index.md` / `log.md`を書こうとする

警告候補:

- missing description
- missing stale_after
- unverified important Decision
- broken link
- missing claim attribution

OKF v0.2自体はoptional field欠落やbroken linksをConformance violationにしないため、**標準違反とProject Quality Gateを区別すること**。

## 20. Publish Semantics

原則:

```text
Working Copy
   ↓
Reconcile
   ↓
Review
   ↓
OKF Validate
   ↓
Index / Log Validate
   ↓
Atomic-ish Publish / existing safe bundle mechanism
   ↓
S3 Events
   ↓
S3 Vectors Reindex
```

Harvest失敗時にcurrent published bundleを壊さない。

## 21. Consumer Compatibility

Harvestが出すOKFは次のconsumer behaviorを想定する。

- Unknown extension keyを保持
- Unknown typeをgeneric conceptとして読める
- verified bare mappingをlistとして扱える
- deprecatedをcurrent answerで優先しない
- stale conceptを警告可能
- sourcesからRaw Evidenceへたどれる

## 22. Recommended Subagent Structure

MVP推奨:

```text
Supervisor
  │
  ├─ source-analyst
  │    Evidence → Candidates
  │
  ├─ knowledge-author
  │    Candidate + Reconcile result → OKF draft
  │
  └─ reviewer
       Evidence + Existing Wiki + Draft → Findings / Verification
```

`knowledge-reconciler`を独立subagentにするか、Supervisor / deterministic helper + LLM判定の組合せにするかは実装時に選べる。

重要なのは責務境界を固定すること。

## 23. Deterministic vs LLM

可能な限りdeterministicにするもの:

- YAML parsing
- OKF field validation
- reserved filename rules
- status enum
- source resource presence
- stable ID exact match
- date format
- Markdown link extraction
- index/log format

LLMが必要なもの:

- Candidate extraction
- semantic identity判断
- UPDATE vs REINFORCE vs CONFLICT
- narrative synthesis
- relation prose

これによりAgentにすべてを丸投げしない。

## 24. Managed KBのHarvest利用

Managed KBは主にConsumerのRaw Evidence Retrievalだが、Harvest Reviewerが追加Evidenceを必要とする場合にも利用可能。

ただし、HarvestのCanonical provenanceは最終的にOKF`sources`へ固定する。

## 25. E2E Test Scenario

Input:

```text
Meeting A: Gateway検討
Meeting B: Gateway採用
Architecture Spec: Gateway採用を正式記載
Issue Report: Gateway認証エラー
Meeting C: Gateway方針変更
```

Expected:

- Meeting ConceptはSource/meeting単位で作成
- Gateway Decisionは乱造せず同じstable IDを維持
- Meeting Bでdecision_state active
- SpecでREINFORCE + sources追加
- Issueは新Issue Concept + Decision Link
- Meeting Cで正しいUPDATE / CONFLICT判定
- OKF statusとbusiness stateが分離
- generated / verified / stale_afterが規約通り
- index.md / log.md更新

## 26. Definition of Done

Harvest移行完了とは、単にProject文書をMarkdown化できることではない。

> **複数Sourceから抽出したKnowledgeを既存OKF v0.2 Bundleと照合し、同一Knowledgeを継続的にCREATE / UPDATE / REINFORCE / CONFLICT判定し、OKF v0.2のProvenance / Trust / Lifecycle / Freshness / Links / Index / Logを正しく維持してpublishできること。**
