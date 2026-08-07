# LLM Wiki / 議事録Wiki 改修要件定義

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`

## 1. 目的

既存`sample-okf-llm-wiki`をベースとして、Data Wiki向け実装を議事録・業務文書向けLLM Wikiへ改修する。

既存社内基盤を優先利用する。

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed Knowledge Base Target

新しい独自RAGやGraph基盤を作るのではなく、既存RepoのOKF / Link / S3 Vectors / MCPを活用する。

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
  - → Meeting / Document Harvest
- Dataset / Table中心のKnowledge Model
  - → Meeting / Topic / Decision / Action / Risk
- Chat Agentの`ConsumptionTools` direct import
  - → Existing AgentCore Gateway経由MCP
- Cognito UI Login依存
  - → Existing application authentication boundaryに適合

### 2.3 新規追加

- Meeting Wiki schema
- Document source adapter
- Existing GatewayへのWiki MCP Target登録
- Wiki / Managed KB routing policy
- Raw evidence citation policy
- Meeting Wiki UI terminology

### 2.4 今回スコープ外

元Repoから削除するものではなく、MVPでは追加しないもの。

- DynamoDB Vector Search migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- New custom vector DB
- New custom RAG platform

## 3. Functional Requirements

### FR-01 Source Input

議事録・業務文書をHarvest対象として入力できること。

MVP対象:

- Markdown / text
- PDF
- DOCX
- PPTX

将来:

- SharePoint
- Teams
- OneDrive
- Web API
- DB / SaaS connector

### FR-02 Knowledge Extraction

Harvest Agentは最低限以下を抽出すること。

- Meeting
- Topic
- Decision
- Action
- Risk
- Source provenance

### FR-03 Existing Wiki Search

新規Sourceを処理する前に既存Wikiを検索し、Knowledge単位で以下を判断すること。

- create
- update
- reinforce
- conflict
- ignore

### FR-04 Duplicate Control

同一Decision / Topic / Actionのページ乱造を防ぐこと。

Semantic search、title、ID、link contextを組み合わせて既存ページ候補を取得する。

### FR-05 Conflict Handling

Source間で内容が矛盾する場合、無言で上書きしないこと。

最低限:

- conflict状態を検出
- sourceを保持
- current / supersededの区別を可能にする
- Human reviewへ回せること

### FR-06 Provenance

Knowledge Pageから元Meeting / documentへたどれること。

最低限frontmatterに以下を持つ。

```text
sources
generated
verified
status
updated_at
```

### FR-07 Stable IDs

以下にstable IDを持たせる。

```text
meeting_id
topic_id
decision_id
action_id
risk_id
```

### FR-08 Link / Backlink

関連KnowledgeをMarkdown Linkとして表現し、Backlink検索できること。

### FR-09 Semantic Wiki Search

既存S3 Vectorsを利用し、意味からWiki Conceptを検索できること。

Vector searchは回答本文ではなくCandidate Concept discoveryに利用する。

### FR-10 Wiki Read

検索結果は`read_page`等でS3上の正式なOKF Markdownを読み直して回答へ利用すること。

### FR-11 Managed KB Raw Retrieval

既存Managed KBからRaw Source Evidenceを取得できること。

### FR-12 Gateway Integration

既存AgentCore Gatewayに以下の2 Targetが存在する状態にする。

```text
Target 1: Existing Managed KB
Target 2: Wiki MCP
```

### FR-13 Chat Agent Gateway Access

Chat Agentは既存Gateway MCP endpointを利用してKnowledge Toolを発見・利用できること。

### FR-14 Query Routing

Chat Agentは質問内容に応じて以下を選択すること。

```text
Current knowledge / relationship
→ Wiki MCP

Raw wording / numbers / source evidence / citation
→ Managed KB

Complex question
→ Wiki → Managed KB verification
```

### FR-15 Citation

Evidence依存の回答ではRaw Source citationを返せること。

### FR-16 Conversation State

既存DynamoDBSaverを利用し、同一threadでConversationを継続できること。

### FR-17 UI

Data Wiki用語をMeeting Wiki用語へ変更する。

MVP UI:

- Projects
- Sources
- Meetings
- Harvest status
- Wiki browser
- Graph View
- Chat panel

## 4. Knowledge Model

### Meeting

必須候補:

```yaml
meeting_id:
meeting_date:
project:
participants:
sources:
status:
generated:
verified:
updated_at:
```

### Topic

```yaml
topic_id:
title:
project:
related_meetings:
related_decisions:
related_actions:
sources:
status:
```

### Decision

```yaml
decision_id:
decision:
reason:
decided_at:
project:
related_topics:
sources:
status:
```

### Action

```yaml
action_id:
description:
owner:
due_date:
status:
project:
source:
```

### Risk

```yaml
risk_id:
description:
impact:
mitigation:
status:
project:
sources:
```

## 5. Retrieval Requirements

### Wiki Search

```text
Link / Backlink
→ Explicit relationship

S3 Vectors
→ Semantic page discovery

read_page
→ Authoritative compiled page content
```

### Raw Search

```text
Existing Managed KB
→ Original meeting/documents
→ Evidence / citation
```

### Hybrid Answer

```text
Wiki understanding
      ↓
Raw verification
      ↓
Answer + Citation
```

## 6. Non-Functional Requirements

### NFR-01 Reliability

Harvest失敗時に現在publishedされているWikiを破壊しないこと。

### NFR-02 Idempotency

同一S3 event / reindex eventが再処理されてもVectorの重複や不整合を起こさないこと。

既存sequencer / overwrite-by-key設計を維持する。

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
- LLM calls
- Tool calls
- Gateway calls
- Managed KB retrieval
- Chat Agent calls
- reindex errors / DLQ

### NFR-05 Cost

MVPでは以下を新規導入しないことでコストと複雑性を抑える。

- Neptune
- GraphRAG
- New Vector DB
- AgentCore Long-term Memory

### NFR-06 Portability

OKF Markdown自体はAWSサービスに閉じず、人間・Agentが直接読める形式を維持する。

## 7. Component Modification Requirements

### `services/harvest`

最大改修対象。

- Glue/Table前提を抽象化
- Meeting/document adapters追加
- Prompt / Skill変更
- Meeting / Topic / Decision / Action / Risk extraction
- Existing Wiki lookup
- Duplicate / conflict decision
- Source provenance

### `services/okf_core`

基本再利用。

追加:

- Meeting Wiki schema validation
- stable IDs
- frontmatter conventions

### `services/control_api`

変更:

- Dataset registration UI/API → Project / source registration
- Harvest trigger / status
- Meeting/wiki browse API

### `services/incremental`

Glue event前提を変更。

- S3/document update event
- scoped re-harvest

### `services/reindex`

原則そのまま。

- S3 Vectors維持
- Metadataで必要に応じてMeeting Wiki向け属性を追加

### `services/consumption_mcp`

基本再利用。

- Wiki terminologyの調整
- Meeting / Topic等を扱えるTool description
- Gateway Targetとして接続

### `services/chat`

Frameworkは再利用。

変更:

- in-process ConsumptionToolsをGateway MCP clientへ置換/抽象化
- Wiki + Managed KB routing prompt
- Citation handling

### `infra/durable`

基本維持。

- S3
- S3 Vectors
- DynamoDB

Cognitoは社内既存認証設計に合わせて削除または無効化する。

### `infra/compute`

- Existing GatewayへのWiki MCP target integration
- Runtime authを既存社内方式へ適合
- Existing Gateway / KB resourceを新規作成しない

### `ui`

- Dataset中心UI → Project / Meeting中心UI
- Existing authに統合
- Chat panelは再利用
- Graph View再利用

## 8. Acceptance Criteria

- [ ] Meeting source投入
- [ ] Harvest実行
- [ ] Meeting page生成
- [ ] Topic page生成
- [ ] Decision page生成
- [ ] Action page生成
- [ ] Risk page生成
- [ ] Existing page update判定
- [ ] Source provenance保持
- [ ] Link生成
- [ ] Backlink検索
- [ ] S3 Vectors semantic search
- [ ] `read_page`で正式OKF取得
- [ ] Wiki MCP Gateway Target登録
- [ ] Existing Managed KB Targetとの共存
- [ ] Chat Agent → Gateway MCP
- [ ] Wiki / KB routing
- [ ] Raw Citation
- [ ] DynamoDBSaver conversation continuation
- [ ] Failed harvest rollback/safe publish
- [ ] CloudWatch trace

## 9. Definition of Done

MVP完了条件は、単に議事録からMarkdownを生成することではない。

> **新しい議事録を既存Wikiと照合し、Knowledgeをcreate/updateし、Linkを維持し、Chat AgentがGateway経由でWikiとRaw Evidenceを使い分けてCitation付き回答を返せること。**
