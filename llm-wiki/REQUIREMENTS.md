# Project Knowledge Wiki 改修要件定義 — OKF v0.2準拠

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`
>
> Knowledge Format: **Open Knowledge Format (OKF) v0.2**

## 1. 目的

既存`sample-okf-llm-wiki`をベースとして、Data Wiki向け実装を**Project Knowledge Wiki**へ改修する。

議事録は最初のSource Typeの1つとし、アーキテクチャを議事録専用にはしない。

既存社内基盤を優先利用する。

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed Knowledge Base Target

Knowledgeの保存形式はOKF v0.2を正式採用する。S3 / S3 Vectors / Managed KB / AgentCore GatewayはOKFが規定しないRuntime / Serving Layerとして組み合わせる。

OKF準拠ルールの正本は`OKF_V02_PROFILE.md`とする。

## 2. Scope分類

### 2.1 現行から継承

- `services/okf_core`
- Harvest agent framework
- S3 OKF bundle / versioning
- Link / Backlink
- S3 Vectors semantic index
- Reindex pipeline
- Consumption MCP / FastMCP
- Chat Agent / LangGraph
- DynamoDBSaver
- Registry / Freshness / Annotations
- UI基本構造 / Graph View
- CloudWatch / OpenTelemetry
- Terraform

### 2.2 現行から変更

- Glue / Athena / Redshift中心のData Harvest
  - → Project Knowledge Harvest
- Dataset / Table中心Knowledge Model
  - → Project Knowledge Model
- Data source access
  - → Source Adapter abstraction
- Frontmatter convention
  - → OKF v0.2 Compliance Profile
- Chat Agentの`ConsumptionTools` direct import
  - → Existing AgentCore Gateway経由MCP
- Cognito UI Login依存
  - → Existing application authentication boundaryへ適合

### 2.3 新規追加

- Project Knowledge schema
- Source Adapter layer
- Normalized Evidence contract
- Knowledge Reconciler
- OKF v0.2 authoring / validation rules
- `index.md` / `log.md` maintenance
- Project Knowledge authoring skill / prompts
- Existing GatewayへのWiki MCP Target登録
- Wiki / Managed KB routing policy
- Raw evidence citation policy
- Project Knowledge UI terminology

### 2.4 今回スコープ外

- DynamoDB Vector Search migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- New custom vector DB
- New custom RAG platform

## 3. OKF v0.2 Conformance Requirements

### OKF-01 Concept Frontmatter

`index.md` / `log.md`を除く全Concept `.md`はparse可能なYAML frontmatterを持つこと。

### OKF-02 Required Type

全Conceptに非空`type`を必須とする。

OKFは固定taxonomyを持たないため、Project固有Typeを利用可能。

### OKF-03 Reserved Files

`index.md`と`log.md`をConcept文書として使用しない。

### OKF-04 Bundle Version

bundle-root `index.md`に以下を宣言する。

```yaml
---
okf_version: "0.2"
---
```

subdirectoryの`index.md`にはfrontmatterを付けない。

### OKF-05 Progressive Disclosure

`index.md`をAgent / Humanが個別Conceptを開く前のDirectory Indexとして利用する。

Entryには可能な限りConceptの`description`を含める。

### OKF-06 Update Log

`log.md`をscope単位の更新履歴として利用する。

- newest first
- date headingは`YYYY-MM-DD`
- Creation / Update / Deprecation等の変更概要を記録

### OKF-07 Provenance

Project KnowledgeのProvenanceはOKF v0.2の`sources`をCanonicalとする。

各`sources` entryの`resource`を必須とする。

推奨:

```yaml
sources:
  - id: meeting-20260808
    resource: /meetings/2026-08-08-architecture.md
    title: Architecture Meeting
    author: team:project-a
    last_modified: 2026-08-08
```

### OKF-08 Per-Claim Attribution

重要claimをSourceへ結びつける場合、Markdown footnote labelと`sources[].id`を一致させる。

### OKF-09 Generated

publish対象Knowledgeには次を必須とする。

```yaml
generated:
  by: project-knowledge-harvest/1.0
  at: 2026-08-08T07:30:00Z
```

新規出力でlegacy`timestamp`を使用しない。

### OKF-10 Verified

Review / Verification実施時は`verified`を記録する。

```yaml
verified:
  - by: process:project-knowledge-reviewer
    at: 2026-08-08T07:31:00Z
```

Human確認は`human:<id>` conventionを使用する。

### OKF-11 Trust Tier

Trust scoreをfrontmatterへ固定保存しない。

Consumerは`verified`から以下を導出する。

```text
unverified
machine-confirmed
human-reviewed
```

### OKF-12 Lifecycle Status

OKF標準`status`は次の3値だけを利用する。

```text
draft
stable
deprecated
```

省略時は`stable`として扱う。

### OKF-13 Business Lifecycle Separation

Decision / Requirement / Action / Issue / Risk等の業務状態をOKF`status`に保存しない。

producer-defined extension keyを使う。

```yaml
status: stable
decision_state: active
```

### OKF-14 Freshness

Knowledgeの鮮度には`stale_after: YYYY-MM-DD`を使用する。

Conceptの意味的な最終変更時刻は`generated.at`をCanonicalとする。

### OKF-15 Links

Concept間関係はstandard Markdown linksをCanonicalとする。

bundle-relative absolute linkを推奨する。

```markdown
[Gateway Requirement](/requirements/gateway-access.md)
```

Linkはuntyped edgeであり、relation semanticsは周辺proseで表現する。

### OKF-16 Extensions

Project固有fieldを許容する。

例:

```text
project_id
decision_id
decision_state
requirement_state
action_state
issue_state
risk_state
review_required
```

Consumer / Writerはunknown keysをround-trip時に破壊しない。

### OKF-17 Consumer Tolerance

Consumerは次を理由にConceptを拒否しない。

- Unknown `type`
- Unknown extension key
- Missing optional trust fields
- Broken cross-link
- Missing optional subdirectory `index.md`

## 4. Source Requirements

### FR-01 Source Input

Project SourceをHarvest対象として入力できること。

MVP対象:

- Meeting minutes
- Markdown / text
- PDF
- DOCX
- PPTX
- Specification / Design Doc / Reportとして扱う上記ファイル

将来:

- SharePoint
- Teams
- OneDrive
- Jira / issue tracker
- GitHub
- Email
- Web API
- DB / SaaS connector

### FR-02 Source Adapter

Harvest本体をSource固有仕様から分離すること。

```text
SourceAdapter
  ├─ MeetingAdapter
  ├─ DocumentAdapter
  └─ Future adapters
```

各Adapterは共通Normalized Evidenceへ変換する。

最低限:

```text
source_id
source_type
project
source_uri
created_at / occurred_at
title
author / participants
content
metadata
```

### FR-03 Raw Evidence Preservation

Sourceの原文・URI・IDを失わないこと。

Knowledge Pageは`sources[].resource`から元Evidenceへたどれること。

## 5. Project Knowledge Model Requirements

### FR-04 Knowledge Types

MVPで以下を扱う。

- Project
- Topic
- Decision
- Requirement
- Action
- Risk
- Issue
- Artifact
- Meeting

### FR-05 Stable IDs

各Knowledge Typeにstable IDを持たせる。

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

これらはOKF extension keysとして保持する。

### FR-06 Project

Projectはトップレベルコンテキスト。

```yaml
project_id:
project_state:
```

OKF共通fieldは`type/title/description/status/sources/generated/verified/stale_after`を使用する。

### FR-07 Topic

会議・文書をまたぐ継続テーマを表現する。

### FR-08 Decision

Decision business lifecycle:

```text
proposed
active
superseded
cancelled
```

保存先は`decision_state`。

旧履歴・旧Sourceを消さない。

### FR-09 Requirement

仕様、要求、制約、受入条件を維持する。

業務状態は`requirement_state`。

### FR-10 Action

Owner / Due / business stateを保持する。

業務状態は`action_state`。

### FR-11 Risk / Issue

RiskとIssueを区別する。

業務状態は`risk_state` / `issue_state`。

### FR-12 Artifact

仕様書、設計書、成果物等のProject資産をKnowledge Entryとして表現する。

### FR-13 Meeting

Meeting Pageは会議要約だけでなく、その会議から生じたTopic / Decision / Action等への入口とする。

## 6. Knowledge Compilation Requirements

### FR-14 Knowledge Extraction

SourceからKnowledge Candidateを抽出する。

### FR-15 Existing Wiki Search

新規Source処理前に既存OKF Bundleを検索する。

候補検索:

- stable ID
- exact title / normalized key
- S3 Vectors semantic search
- type
- project
- Link context
- source provenance

### FR-16 Knowledge Reconciliation

Candidateごとに次を判定する。

```text
CREATE
UPDATE
REINFORCE
CONFLICT
IGNORE
```

### FR-17 CREATE

新Conceptを生成する。

Review前は`status: draft`、publish可能になったら`status: stable`。

### FR-18 UPDATE

同一Conceptを更新する。

- stable ID維持
- `generated.at`更新
- `sources`更新
- content変更後は過去`verified`をそのまま「現内容の検証済み」と誤解しない設計にする

### FR-19 REINFORCE

別Sourceが既存Knowledgeを裏付ける場合、新Conceptを作らず`sources`を追加する。

必要に応じて`verified`を追加する。

### FR-20 CONFLICT

既存KnowledgeとSourceが矛盾する場合、無言で上書きしない。

最低限:

- conflicting source
- current knowledge
- proposed change
- conflict reason
- `review_required` extension

必要に応じ`status: draft`としてHuman Reviewへ回す。

### FR-21 IGNORE

Project Knowledgeとして新規価値がない場合publish変更しない。

### FR-22 Duplicate Control

Sourceごとに同一Decision / Requirement / Topic等のConceptを乱造しない。

### FR-23 History Preservation

Knowledgeの状態変更時、過去の判断・Sourceを消さない。

同一ConceptのBusiness state変化は原則stable IDを維持する。

旧Conceptを別Conceptへ完全置換する場合、旧Conceptを`status: deprecated`としてLink / Historyを維持する。

## 7. Link / Navigation Requirements

### FR-24 Link / Backlink

関連KnowledgeをMarkdown Linkとして表現しBacklink検索できること。

例:

```text
Project → Topic
Topic → Decision
Decision → Requirement
Decision → Artifact
Decision → Meeting
Action → Decision
Issue → Decision
Risk → Requirement
Meeting → Decision / Action / Topic
```

Relation TypeをOKF標準fieldとして捏造しない。

### FR-25 Semantic Wiki Search

既存S3 Vectorsを利用し、意味からOKF Conceptを検索できること。

Vector SearchはCandidate Concept Discoveryに利用する。

### FR-26 Wiki Read

検索後は`read_page`等でS3上の正式なOKF Markdownを読み直す。

### FR-27 Index / Log Update

Concept publishに合わせて影響scopeの`index.md` / `log.md`を更新できること。

## 8. Managed KB / Gateway Requirements

### FR-28 Managed KB Raw Retrieval

既存Managed KBからRaw Source Evidenceを取得できること。

### FR-29 Gateway Integration

Existing Gatewayに次のTargetがある状態にする。

```text
Target 1: Existing Managed KB
Target 2: Wiki MCP
```

新規Gateway / Managed KBを作らない。

### FR-30 Chat Agent Gateway Access

Chat AgentはExisting Gateway MCP endpointを利用する。

### FR-31 Query Routing

```text
Current project knowledge / relationship
→ Wiki MCP

Raw wording / exact number / evidence / citation
→ Managed KB

Important factual question
→ Wiki understanding → Managed KB verification
```

### FR-32 Citation

Evidence依存回答ではRaw Source citationを返せること。

OKF本文内のclaim attributionは`sources[].id`とfootnoteを利用できること。

## 9. Conversation Requirements

### FR-33 Conversation State

既存DynamoDBSaverを利用し同一threadでConversationを継続できること。

AgentCore Long-term MemoryはMVPでは追加しない。

## 10. UI Requirements

### FR-34 UI Terminology

Project Knowledge中心へ変更する。

MVP UI:

- Projects
- Sources
- Harvest status
- Knowledge browser
- Meetings
- Decisions / Requirements / Actions / Risks / Issues
- Graph View
- Chat panel

### FR-35 Trust / Freshness Display

可能ならUI / Chatで以下を可視化する。

- unverified / machine-confirmed / human-reviewed
- stale state
- deprecated state
- source list

## 11. Harvest Agent Structure Requirements

### FR-36 Logical Responsibilities

```text
Source Adapter
Knowledge Extractor
Existing Wiki Retriever
Knowledge Reconciler
OKF Author
Link / Index / Log Builder
Reviewer
OKF Guard / Publisher
```

### FR-37 Recommended Subagents

```text
source-analyst
knowledge-author
knowledge-reconciler
reviewer
```

### FR-38 Grounding Replacement

元Repoの`run_sql` / `sample_rows`中心groundingをProject Evidenceへ置き換える。

- source text
- source metadata
- existing OKF Wiki
- Managed KB retrieval when needed

### FR-39 Review

Publish前Reviewerは最低限確認する。

- Sourceにない事実を作っていない
- Duplicateを作っていない
- Existing Knowledgeを誤上書きしていない
- Conflictを隠していない
- `sources[].resource`がある
- `generated`がある
- `status`がOKF値のみ
- Business stateがextensionへ分離されている
- Linkが有効
- important claim attributionが妥当
- `index.md` / `log.md`が整合

詳細は`HARVEST_MIGRATION.md`。

## 12. Consumer Requirements

### FR-40 Unknown Type / Key Tolerance

MCP / ChatはUnknown `type` / extension keyを理由にConceptを拒否しない。

### FR-41 Verified Mapping Compatibility

`verified`が単一mappingの場合も1-element listとして扱う。

### FR-42 Deprecated / Stale Handling

- `status: deprecated`を現行回答の第一候補にしない
- `stale_after`超過Conceptを警告またはrankingへ反映
- staleでも即削除・拒否はしない

## 13. Non-Functional Requirements

### NFR-01 Reliability

Harvest失敗時に現在published Wikiを破壊しない。

### NFR-02 Idempotency

同一Source / S3 event / reindex event再処理で重複・不整合を起こさない。

### NFR-03 Security

新しいUser Login基盤を作らない。

維持:

- IAM least privilege
- Runtime execution role
- Gateway target authorization
- S3 / DynamoDB access control
- service-to-service auth

### NFR-04 Observability

- Harvest agent trace
- Subagent calls
- Reconciliation decision
- OKF validation result
- LLM calls
- Tool calls
- Gateway calls
- Managed KB retrieval
- Chat Agent calls
- reindex errors / DLQ

### NFR-05 Cost

MVPではNeptune / GraphRAG / New Vector DB / AgentCore Long-term Memoryを追加しない。

### NFR-06 Portability

OKF Markdown自体はAWSサービスに閉じず、人間・Agentが直接読める形式を維持する。

## 14. Component Modification Requirements

### `services/harvest`

最大改修対象。

- Source Adapter
- Project Knowledge prompt / skill
- Candidate extraction
- Existing OKF lookup
- Reconciliation
- OKF v0.2 authoring
- provenance / trust / lifecycle
- index / log generation
- Link generation

### `services/okf_core`

- OKF v0.2 validation
- reserved filename rules
- Project extension schemas
- stable IDs
- lifecycle/status conventions
- source / actor helpers

### `services/control_api`

- Dataset registration → Project / Source registration
- Harvest trigger / status
- Knowledge browse API

### `services/incremental`

- Glue event中心 → Document / Source update中心
- scoped re-harvest

### `services/reindex`

原則維持。

- S3 Vectors維持
- Project / type metadata必要時拡張
- `index.md` / `log.md`をConcept vectorとして扱わない既存原則を維持

### `services/consumption_mcp`

- Project Wiki terminology
- OKF trust / lifecycle-aware read
- Gateway Target

### `services/chat`

- in-process tools → Gateway MCP client
- Wiki + Managed KB routing
- Citation
- deprecated / stale / trust handling

### `infra/durable`

基本維持。Cognitoは既存認証設計に合わせて整理。

### `infra/compute`

- Existing GatewayへのWiki MCP target integration
- Existing Gateway / KB resourceを新規作成しない

### `ui`

- Project Knowledge中心UI
- Existing auth統合
- Trust / Freshness表示は段階導入

## 15. Acceptance Criteria

- [ ] root `index.md`に`okf_version: "0.2"`
- [ ] Conceptにvalid YAML + non-empty `type`
- [ ] reserved file semantics準拠
- [ ] `sources[].resource`準拠
- [ ] `generated.by/at`準拠
- [ ] `verified` actor convention準拠
- [ ] `status`が`draft|stable|deprecated`のみ
- [ ] Business lifecycleはextension keys
- [ ] `stale_after`対応
- [ ] important claim footnote attribution
- [ ] `index.md` progressive disclosure
- [ ] `log.md` history
- [ ] Meeting / document source投入
- [ ] Source Adapter → Normalized Evidence
- [ ] Project Knowledge Type生成
- [ ] Existing Wiki Search
- [ ] CREATE / UPDATE / REINFORCE / CONFLICT / IGNORE
- [ ] Duplicate抑止
- [ ] History保持
- [ ] Link / Backlink
- [ ] S3 Vectors semantic discovery
- [ ] Wiki MCP Gateway Target
- [ ] Existing Managed KB共存
- [ ] Chat Agent → Gateway
- [ ] Raw Citation
- [ ] DynamoDBSaver continuation
- [ ] Consumer unknown-key tolerance
- [ ] Failed harvest safe publish
- [ ] CloudWatch trace

## 16. Definition of Done

> **Project Sourcesを既存OKF v0.2 Bundleと照合し、Knowledgeを継続的にcreate/update/reinforceし、Provenance / Trust / Lifecycle / FreshnessをOKF v0.2形式で保持し、Chat AgentがGateway経由でWikiとRaw Evidenceを使い分けて回答できること。**
