# Project Knowledge Wiki 改修要件定義

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`

## 1. 目的

既存`sample-okf-llm-wiki`をベースとして、Data Wiki向け実装を**Project Knowledge Wiki**へ改修する。

議事録は最初に対応するSource Typeの1つとし、アーキテクチャを議事録専用にはしない。

既存社内基盤を優先利用する。

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed Knowledge Base Target

新しい独自RAGやGraph基盤を作るのではなく、既存RepoのOKF / Link / S3 Vectors / MCP / Chatを活用する。

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
- Dataset / Table中心のKnowledge Model
  - → Project Knowledge Model
- Data source access
  - → Source Adapter abstraction
- Chat Agentの`ConsumptionTools` direct import
  - → Existing AgentCore Gateway経由MCP
- Cognito UI Login依存
  - → Existing application authentication boundaryへ適合

### 2.3 新規追加

- Project Knowledge schema
- Source Adapter layer
- Normalized Evidence contract
- Knowledge Reconciler
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

## 3. Source Requirements

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

各Adapterは共通のNormalized Evidenceへ変換する。

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

Knowledge Pageは必ず元Sourceへたどれること。

## 4. Project Knowledge Model Requirements

### FR-04 Knowledge Types

MVPで最低限以下を扱うこと。

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

IDはSource filenameだけに依存させず、Sourceが増えても同じKnowledgeを継続更新できること。

### FR-06 Project

ProjectはWikiのトップレベルコンテキストとして扱う。

最低限:

```yaml
project_id:
title:
status:
summary:
sources:
updated_at:
```

### FR-07 Topic

会議・文書をまたぐ継続テーマを表現する。

### FR-08 Decision

DecisionはLifecycleを管理できること。

推奨status:

```text
proposed
active
superseded
cancelled
```

変更時に旧履歴・旧Sourceを消さないこと。

### FR-09 Requirement

仕様、要求、制約、受入条件をKnowledgeとして維持できること。

### FR-10 Action

Owner / Due / Statusを保持できること。

### FR-11 Risk / Issue

Riskは将来発生可能性、Issueは既に発生している問題として区別できること。

### FR-12 Artifact

仕様書、設計書、成果物等のProject資産をKnowledge Entryとして表現できること。

### FR-13 Meeting

Meeting Pageは会議の要約だけでなく、その会議から生じたTopic / Decision / Action等への入口になること。

## 5. Knowledge Compilation Requirements

### FR-14 Knowledge Extraction

SourceからKnowledge Candidateを抽出すること。

```text
Source
  ↓
Normalized Evidence
  ↓
Knowledge Candidates
```

### FR-15 Existing Wiki Search

新規Sourceを処理する前に既存Wikiを検索すること。

候補検索には以下を組み合わせる。

- stable ID
- exact title / normalized key
- S3 Vectors semantic search
- type
- project
- Link context
- source provenance

### FR-16 Knowledge Reconciliation

Knowledge Candidateごとに次を判定すること。

```text
CREATE
UPDATE
REINFORCE
CONFLICT
IGNORE
```

#### CREATE
既存Wikiに同一Knowledgeがない。

#### UPDATE
同一Knowledgeだが状態・内容が変化した。

#### REINFORCE
別Sourceが既存Knowledgeを裏付ける。Sourceを追加し、必要に応じてconfidence / verified情報を更新する。

#### CONFLICT
既存Knowledgeと新Sourceが矛盾する。無言で上書きしない。

#### IGNORE
Project Knowledgeとして新規価値がない。

### FR-17 Duplicate Control

Sourceごとに同一Decision / Requirement / Topic等のページを乱造しないこと。

### FR-18 Conflict Handling

Conflict時には最低限以下を保持する。

- conflicting source
- current knowledge
- proposed change
- conflict reason
- review required flag

自動解消はMVP必須としない。

### FR-19 Provenance

全Knowledge Pageに最低限以下を持つ。

```text
sources
generated
verified
status
updated_at
```

重要なDecision / Requirement / RiskをSourceなしでpublishしない。

### FR-20 History Preservation

Knowledgeの状態変更時、過去の判断・Sourceを消さない。

特にDecision / Requirement / IssueのLifecycleを追跡できること。

## 6. Link / Navigation Requirements

### FR-21 Link / Backlink

関連KnowledgeをMarkdown Linkとして表現し、Backlink検索できること。

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

### FR-22 Semantic Wiki Search

既存S3 Vectorsを利用し、意味からWiki Conceptを検索できること。

Vector searchは回答本文ではなくCandidate Concept discoveryに利用する。

### FR-23 Wiki Read

検索結果は`read_page`等でS3上の正式なOKF Markdownを読み直して回答へ利用すること。

## 7. Managed KB / Gateway Requirements

### FR-24 Managed KB Raw Retrieval

既存Managed KBからRaw Source Evidenceを取得できること。

### FR-25 Gateway Integration

既存AgentCore Gatewayに以下のTargetが存在する状態にする。

```text
Target 1: Existing Managed KB
Target 2: Wiki MCP
```

新規Gateway / Managed KBを作成しない。

### FR-26 Chat Agent Gateway Access

Chat Agentは既存Gateway MCP endpointを利用してKnowledge Toolを発見・利用できること。

### FR-27 Query Routing

Chat Agentは質問内容に応じて以下を選択する。

```text
Current project knowledge / relationship
→ Wiki MCP

Raw wording / number / evidence / citation
→ Managed KB

Important factual question
→ Wiki understanding → Managed KB verification
```

### FR-28 Citation

Evidence依存の回答ではRaw Source citationを返せること。

## 8. Conversation Requirements

### FR-29 Conversation State

既存DynamoDBSaverを利用し、同一threadでConversationを継続できること。

AgentCore Long-term MemoryはMVPでは追加しない。

## 9. UI Requirements

### FR-30 UI Terminology

Data Wiki / Meeting Wiki専用UIではなくProject Knowledge中心へ変更する。

MVP UI:

- Projects
- Sources
- Harvest status
- Knowledge browser
- Meetings
- Decisions / Actions / Risks等へのNavigation
- Graph View
- Chat panel

## 10. Harvest Agent Structure Requirements

### FR-31 Agent Responsibilities

Harvestは最低限、次の論理責務を持つ。

```text
Source Adapter
Knowledge Extractor
Existing Wiki Retriever
Knowledge Reconciler
Link Builder
Reviewer
Publisher / Guard
```

実装上は必ずしも各責務を別Agentにする必要はないが、責務境界は維持する。

### FR-32 Recommended Subagents

元Repoのtable-author等のData固有SubagentをProject Knowledge向けに置き換える。

推奨:

```text
source-analyst
knowledge-author
knowledge-reconciler
reviewer
```

Knowledge Type別authorへ細分化する場合は、共通Reconciliation規則を共有すること。

### FR-33 Grounding Replacement

元Repoの`run_sql` / `sample_rows`中心のgroundingを、Project Source Evidenceへ置き換える。

最低限:

- source text
- source metadata
- existing Wiki
- Managed KB retrieval when needed

### FR-34 Review

Publish前Reviewerは最低限以下を確認する。

- Sourceにない事実を作っていない
- Duplicate Pageを作っていない
- Existing Knowledgeを誤上書きしていない
- Conflictを隠していない
- Source provenanceがある
- Linkが有効
- required frontmatterを満たす

詳細は`HARVEST_MIGRATION.md`を正本とする。

## 11. Non-Functional Requirements

### NFR-01 Reliability

Harvest失敗時に現在publishedされているWikiを破壊しないこと。

### NFR-02 Idempotency

同一Source / S3 event / reindex eventの再処理で重複や不整合を起こさないこと。

### NFR-03 Security

新しいユーザーLogin基盤を作らない。

ただし以下は維持する。

- IAM least privilege
- Runtime execution role
- Gateway target authorization
- S3 / DynamoDB access control
- service-to-service auth

### NFR-04 Observability

最低限確認可能なもの:

- Harvest agent trace
- Subagent calls
- Reconciliation decision
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

## 12. Component Modification Requirements

### `services/harvest`

最大改修対象。

- Glue/Table前提を抽象化
- Source Adapter追加
- Project Knowledge prompt / skillへ変更
- Knowledge Candidate extraction
- Existing Wiki lookup
- Reconciliation
- Provenance / History
- Project Knowledge link generation

### `services/okf_core`

基本再利用。

追加:

- Project Knowledge schema validation
- stable IDs
- lifecycle/status conventions
- frontmatter conventions

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
- 必要ならProject / type metadataを追加

### `services/consumption_mcp`

基本再利用。

- Project Wiki terminology
- Tool descriptions
- Gateway Targetとして接続

### `services/chat`

Framework / DynamoDBSaver / SSEは再利用。

変更:

- in-process ConsumptionTools → Gateway MCP client
- Wiki + Managed KB routing prompt
- Citation handling

### `infra/durable`

基本維持。

Cognitoは既存認証設計に合わせて削除または無効化する。

### `infra/compute`

- Existing GatewayへのWiki MCP target integration
- Runtime authを既存社内方式へ適合
- Existing Gateway / KB resourceを新規作成しない

### `ui`

- Dataset中心UI → Project Knowledge中心UI
- Existing authへ統合
- Chat / Graph Viewを再利用

## 13. Acceptance Criteria

- [ ] Projectを登録・選択できる
- [ ] Meeting / document sourceを投入できる
- [ ] Source AdapterでNormalized Evidenceへ変換できる
- [ ] Project / Topic / Decision / Requirement / Action / Risk / Issue / Artifact / Meetingを生成できる
- [ ] Existing Wikiを検索できる
- [ ] CREATE / UPDATE / REINFORCE / CONFLICT / IGNOREを判定できる
- [ ] Duplicate Knowledge Pageを抑止できる
- [ ] Decision lifecycleを保持できる
- [ ] Source provenanceを保持できる
- [ ] Link / Backlinkを生成できる
- [ ] S3 Vectors semantic searchが動く
- [ ] `read_page`で正式OKFを取得できる
- [ ] Wiki MCPをExisting Gateway Targetへ登録できる
- [ ] Existing Managed KB Targetと共存できる
- [ ] Chat AgentがGateway MCPを利用できる
- [ ] Wiki / KB routingが動く
- [ ] Raw Citationを返せる
- [ ] DynamoDBSaverでconversation continuationできる
- [ ] Failed harvestでpublished Wikiを壊さない
- [ ] CloudWatchでReconciliationを含むtraceを確認できる

## 14. Definition of Done

MVP完了条件は、議事録からMarkdownを生成することではない。

> **複数種類のProject Sourceを既存Wikiと照合し、Project Knowledgeを継続的にcreate / update / reinforce / conflict管理し、Chat AgentがExisting Gateway経由でWikiとRaw Evidenceを使い分けてCitation付き回答を返せること。**
