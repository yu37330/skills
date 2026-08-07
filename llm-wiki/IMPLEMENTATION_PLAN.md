# Project Knowledge Wiki 実装計画

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`

## 1. 実装方針

元Repoの完成度が高い部分を壊さず、Data Wiki固有部分だけをProject Knowledge向けへ差し替える。

```text
Keep
  OKF Core
  Link / Backlink
  S3 Bundle
  S3 Vectors
  Reindex pipeline
  Consumption MCP
  Chat framework
  DynamoDBSaver
  UI / Graph View
  Observability

Change
  Harvest domain model
  Source access model
  Knowledge reconciliation
  UI terminology
  Chat knowledge access
  Authentication integration

Integrate
  Existing AgentCore Gateway
  Existing Managed KB
```

## 2. Target Architecture

```text
Existing Fargate Front
        │
        ▼
Chat Agent / AgentCore Runtime
        │ MCP
        ▼
Existing AgentCore Gateway
        │
   ┌────┴────┐
   ▼         ▼
Wiki MCP   Managed KB
 NEW        EXISTING
   │           │
   ▼           ▼
Project Wiki Raw Evidence
   │
 ┌─┴────────────┐
 ▼              ▼
Links        S3 Vectors
```

生成側:

```text
Project Sources
      ↓
Source Adapter
      ↓
Normalized Evidence
      ↓
Knowledge Extraction
      ↓
Existing Wiki Search
      ↓
Knowledge Reconciliation
CREATE / UPDATE / REINFORCE / CONFLICT / IGNORE
      ↓
OKF Markdown
      ↓
S3
      ↓
EventBridge → SQS → Reindex Lambda → Titan V2 → S3 Vectors
```

## 3. 実装Phase

### Phase 0 — Baseline固定

目的: 元Repoをそのまま動作させ、変更前の基準を作る。

- upstream commitを固定
- LICENSE確認
- Harvest Runtime確認
- Consumption MCP Runtime確認
- Chat Runtime確認
- S3 Bundle確認
- S3 Vectors semantic_search確認
- Link / Backlink確認
- DynamoDBSaver確認
- CloudWatch trace確認

成果物:

```text
baseline commit SHA
baseline deployment notes
baseline smoke test
```

### Phase 1 — Project Knowledge Schema

対象:

- `services/okf_core`
- Harvest skill / prompt

定義:

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

作業:

- stable ID rule
- lifecycle/status rule
- source provenance rule
- naming/path rule
- Link rule
- frontmatter validation

推奨構成:

```text
wiki/
  index.md
  projects/
  topics/
  decisions/
  requirements/
  actions/
  risks/
  issues/
  artifacts/
  meetings/
  entities/
```

### Phase 2 — Source Adapter Layer

対象:

```text
services/harvest
```

Data Source固有処理をHarvestのKnowledge Logicから分離する。

```text
SourceAdapter
  ├─ MeetingAdapter
  ├─ DocumentAdapter
  └─ FutureAdapter
```

MVP input:

```text
Markdown/Text
PDF
DOCX
PPTX
```

出力は共通Normalized Evidence。

```text
source_id
source_type
project
source_uri
title
occurred_at / created_at
author / participants
content
metadata
```

### Phase 3 — Project Knowledge Harvest Agent改修

**最重要Phase。**

対象:

```text
services/harvest
```

Pipeline:

```text
Normalized Evidence
  ↓
Source Analysis
  ↓
Knowledge Candidate Extraction
  ↓
Search Existing Wiki
  ↓
Knowledge Reconciliation
  ↓
Create / Edit Pages
  ↓
Generate Links
  ↓
Review
  ↓
OKF Guard / Lint
  ↓
Publish
```

既存の以下は極力残す。

- deepagents supervisor
- subagents
- reviewer
- FilesystemBackend
- OKFGuardMiddleware
- LinkGraph
- tracing

詳細仕様は`HARVEST_MIGRATION.md`。

### Phase 4 — Knowledge Reconciler

Harvestの本丸を独立責務として実装する。

入力:

```text
Knowledge Candidate
Existing Wiki Candidates
Source Evidence
```

出力:

```text
CREATE
UPDATE
REINFORCE
CONFLICT
IGNORE
```

判定材料:

- stable ID
- normalized key/title
- project
- type
- semantic similarity
- existing links
- source provenance
- status/lifecycle

特にDecision / Requirement / Issueは履歴を保持する。

### Phase 5 — Grounding / Reviewer変更

元RepoのData grounding:

```text
Glue metadata
run_sql
sample_rows
```

をProject Evidence groundingへ変更する。

```text
source text
source metadata
existing Wiki
Managed KB retrieval when needed
```

Reviewer確認:

- Sourceにない事実を作っていない
- Duplicateを作っていない
- 既存Knowledgeを誤上書きしていない
- Conflictを隠していない
- Source provenanceがある
- Linkが有効
- required frontmatterがある

### Phase 6 — Source / Control API変更

対象:

```text
services/control_api
services/incremental
```

変更:

```text
Dataset registration
→ Project / Source registration

Glue change event
→ Document / Source update event
```

MVPではSource Connectorを増やしすぎない。

### Phase 7 — S3 Vectors維持確認

対象:

```text
services/reindex
services/okf_core/src/okf_core/embedding.py
services/okf_aws/src/okf_aws/embeddings.py
```

原則変更しない。

維持:

- Titan Text Embeddings V2
- 512 dimensions
- cosine
- 1 Concept = 1 Vector
- deterministic vector key
- EventBridge / SQS / Lambda
- sequencer dedup
- retry / DLQ

互換性を優先し、既存`dataset`をProject相当として利用する案を第一候補とする。

必要ならmetadataだけProject Knowledge向けに拡張する。

### Phase 8 — Consumption MCP Project Knowledge対応

対象:

```text
services/consumption_mcp
```

基本Toolを残す。

```text
list_domains
list_directory
read_page
glob
grep
get_backlinks
semantic_search
```

変更は主にTool description / terminology / Project Knowledge path理解。

### Phase 9 — Existing AgentCore Gateway統合

新規Gatewayは作らない。

```text
Existing AgentCore Gateway
   ├─ Existing Managed KB Target
   └─ Wiki MCP Target  ← ADD
```

作業:

- Consumption MCP Runtime endpoint確認
- Gateway Target登録
- Tool discovery確認
- IAM / auth確認
- CloudWatch trace確認

成功条件: 同じGateway endpointからWiki ToolとManaged KB Toolを発見できること。

### Phase 10 — Chat AgentをGatewayへ変更

対象:

```text
services/chat
```

Current:

```text
Chat Agent
  ↓
ConsumptionTools direct import
```

To-Be:

```text
Chat Agent
  ↓
MCP client
  ↓
Existing AgentCore Gateway
  ├─ Wiki MCP
  └─ Managed KB
```

維持:

- LangGraph
- model factory
- DynamoDBSaver
- SSE / FastAPI
- thread handling

変更:

- Gateway MCP client
- Tool discovery
- namespace handling
- routing prompt
- citation handling
- Gateway error handling

### Phase 11 — Query Routing Prompt

Chat Agent System PromptへPolicyを追加する。

```text
Use Wiki when:
- current project state
- current decision
- topic summary
- action / issue / risk
- relationships

Use Managed KB when:
- exact source wording
- evidence
- citation
- exact number
- raw detail

For important factual answers:
1. understand with Wiki
2. verify with Managed KB
3. answer with source citation
```

### Phase 12 — UI変更

対象:

```text
ui/
```

変更:

```text
Domains / Datasets
→ Projects / Sources

Data Harvest
→ Knowledge Harvest

Dataset Browser
→ Project Knowledge Browser
```

維持:

- Browse pattern
- Graph View
- Chat panel
- Harvest status

MeetingはProject Knowledge内の1 Viewとして扱う。

### Phase 13 — E2E / Evaluation

代表Source Setを作る。

```text
Meeting A: Gatewayを検討
Meeting B: Gatewayを採用
Architecture Spec: Gateway経由でKBとWiki MCPを利用
Issue: Gateway認証エラー
Meeting C: Gateway案を変更/撤回
```

代表Questions:

```text
Q1. Projectの現在のDecisionは？
Q2. Gateway採用の経緯は？
Q3. そのDecisionの根拠Sourceは？
Q4. 仕様書ではどう定義されている？
Q5. Gateway関連のIssueは？
Q6. 未完了Actionは？
Q7. 過去Decisionから何が変わった？
```

評価軸:

- extraction accuracy
- duplicate rate
- reconciliation accuracy
- lifecycle correctness
- conflict detection
- link correctness
- semantic search recall
- evidence retrieval
- citation correctness
- answer faithfulness
- latency
- cost

## 4. Component Change Map

| Component | 方針 | 改修量 |
|---|---|---:|
| `services/harvest` | Project Knowledge化 | **大** |
| `services/okf_core` | schema / lifecycle追加 | 中 |
| `services/control_api` | project/source化 | 中 |
| `services/incremental` | source update化 | 中 |
| `services/reindex` | 原則維持 | 小 |
| `services/consumption_mcp` | terminology / Gateway | 小〜中 |
| `services/chat` | direct tools → Gateway | 中 |
| `infra/durable` | 基本維持 / Cognito整理 | 小〜中 |
| `infra/compute` | Existing Gateway integration | 中 |
| `ui` | Project Knowledge UI | 中 |

## 5. AWS Environment

### Existing

```text
Fargate Front
Application Authentication
AgentCore Gateway
Managed Knowledge Base
```

### Base Repoから利用

```text
AgentCore Runtime: Harvest
AgentCore Runtime: Consumption MCP
AgentCore Runtime: Chat
S3 Bundle
S3 Vectors
DynamoDB
EventBridge
SQS
Lambda
Bedrock Titan Embeddings
Bedrock Foundation Models
CloudWatch / OTEL
```

### New configuration

```text
Existing Gateway
  + Wiki MCP Target
```

## 6. MVP Day Plan

### Day 1

- Baseline起動
- Project Knowledge schema
- Source Adapter contract

### Day 2

- Meeting / Document Adapter
- Knowledge Candidate extraction

### Day 3

- Knowledge Reconciler
- Decision / Requirement lifecycle
- Source provenance

### Day 4

- Action / Risk / Issue / Artifact
- Link / Backlink
- Reviewer / Guard

### Day 5

- S3 Vectors確認
- Consumption MCP Project Knowledge対応
- Existing GatewayへWiki MCP Target追加

### Day 6

- Chat Agent Gateway接続
- Wiki + Managed KB routing
- Citation

### Day 7〜8

- UI調整
- duplicate / conflict改善
- trace / error handling

### Day 9〜10

- E2E evaluation
- hardening
- internal demo / documentation

## 7. Estimate

```text
PoC                    3〜5営業日
Internal MVP           5〜10営業日
Production hardening   3〜6週間
```

最大の不確実性はInfrastructureではなく、**Knowledge Reconciliation品質**。

## 8. Do Not Optimize Early

MVPで先にやらないもの:

- DynamoDB Vector migration
- AgentCore Memory
- Neptune
- GraphRAG
- Heavy Ontology
- many source connectors
- automatic conflict resolution
- complex approval workflow

## 9. Recommended Development Order

```text
1. 元Repoをそのまま動かす
       ↓
2. Source Adapter + Project Knowledge Schema
       ↓
3. HarvestをProject Knowledge化
       ↓
4. Knowledge Reconcilerを完成させる
       ↓
5. Wiki Retrievalが壊れていないことを確認
       ↓
6. Existing GatewayへWiki MCP追加
       ↓
7. Chat AgentをGatewayへ接続
       ↓
8. Existing Managed KBとのHybrid回答
       ↓
9. UI / Evaluation
```

## 10. Final Implementation Principle

> **元Repoの「Knowledgeを保存・Link・Semanticに探す」部分は残し、Harvestの知能を「Data理解」から「Project Knowledge Compilation / Reconciliation」へ置き換える。既存Gateway / Managed KBはKnowledge Access / Evidence側へ接続する。**

この順序なら議事録からPoCを始めても、議事録専用アーキテクチャにならない。
