# LLM Wiki / 議事録Wiki 実装計画

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`

## 1. 実装方針

今回の基本方針は、元Repoの完成度が高い部分を壊さず、Data Wiki固有部分だけを差し替えること。

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
OKF Wiki    Raw Evidence
   │
 ┌─┴────────────┐
 ▼              ▼
Links        S3 Vectors
```

生成側:

```text
Meeting / Docs
      ↓
Harvest Agent
      ↓
Existing Wiki Search
      ↓
create / update / reinforce / conflict
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
- Terraform構成確認
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

### Phase 1 — Meeting Wiki Schema

対象:

- `services/okf_core`
- Harvest skill / prompt

作業:

- Meeting / Topic / Decision / Action / Risk schema定義
- stable ID rule
- source provenance rule
- status rule
- naming/path rule
- Link rule

推奨Wiki構成:

```text
wiki/
  index.md
  overview.md
  meetings/
  topics/
  decisions/
  actions/
  risks/
  projects/
  entities/
```

### Phase 2 — Harvest Agent改修

対象:

```text
services/harvest
```

最重要Phase。

現在:

```text
Glue / Athena / Redshift
```

から、

```text
DocumentSource interface
  ├─ Markdown/Text
  ├─ PDF
  ├─ DOCX
  └─ PPTX
```

へ変更する。

Pipeline:

```text
Source
  ↓
Parse
  ↓
Classify
  ↓
Extract candidate knowledge
  ↓
Search existing Wiki
  ↓
Duplicate / Conflict detection
  ↓
Create / Edit pages
  ↓
Generate links
  ↓
Guard / lint
  ↓
Review
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

### Phase 3 — Source / Control API変更

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
→ Document / S3 source update event
```

MVPではSource種類を増やしすぎない。

最初はS3上のMarkdown/PDF/DOCX/PPTXで十分。

### Phase 4 — S3 Vectors維持確認

対象:

```text
services/reindex
services/okf_core/src/okf_core/embedding.py
services/okf_aws/src/okf_aws/embeddings.py
```

基本的には変更しない。

維持:

- Titan Text Embeddings V2
- 512 dimensions
- cosine
- 1 Concept = 1 Vector
- deterministic vector key
- EventBridge / SQS / Lambda
- sequencer dedup
- retry / DLQ

必要ならMetadataのみ拡張する。

既存:

```text
data_domain
dataset
table
type
tags
```

MVP案:

```text
data_domain
dataset (= project)
type
tags
```

互換性を優先し、`dataset`をProjectとして使えばreindex変更を最小化できる。

### Phase 5 — Consumption MCP Meeting対応

対象:

```text
services/consumption_mcp
```

既存Toolを基本的に残す。

```text
list_domains
list_directory
read_page
glob
grep
get_backlinks
semantic_search
```

変更は主にTool description / terminology。

Data Wiki固有説明をMeeting Wikiへ置き換える。

### Phase 6 — Existing AgentCore Gateway統合

新規Gatewayは作らない。

既存構成:

```text
Existing AgentCore Gateway
   └─ Existing Managed KB Target
```

変更後:

```text
Existing AgentCore Gateway
   ├─ Existing Managed KB Target
   └─ Wiki MCP Target
```

作業:

- Consumption MCP Runtime endpoint確認
- Gateway Target登録
- Tool discovery確認
- IAM / auth確認
- CloudWatch trace確認

成功条件:

同じGateway endpointからWiki ToolとManaged KB Toolを発見できること。

### Phase 7 — Chat AgentをGatewayへ変更

対象:

```text
services/chat
```

現在:

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

主な変更:

- Gateway MCP client
- Tool discovery
- Tool naming / namespace handling
- Routing prompt
- Citation response handling
- Gateway error handling

Chat AgentのLangGraph / DynamoDBSaver / SSE部分は維持する。

### Phase 8 — Query Routing Prompt

Chat AgentのSystem Promptに以下のPolicyを追加する。

```text
Use Wiki when:
- current decision
- project state
- relationships
- topic summary
- action status

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

### Phase 9 — UI変更

対象:

```text
ui/
```

変更:

```text
Domains / Datasets
→ Projects / Sources

Data Harvest
→ Meeting Harvest

Dataset Browser
→ Wiki Browser
```

維持:

- Browse pattern
- Graph View
- Chat panel
- Harvest status

既存Fargate Front / Authに合わせてCognito依存を外す。

### Phase 10 — E2E / Evaluation

代表Question Setを作る。

例:

```text
Q1. 今回の会議で何が決まった？
Q2. Project Aの現在のDecisionは？
Q3. このDecisionの根拠は？
Q4. 過去のDecisionから何が変わった？
Q5. 未完了Actionは？
Q6. このTopicに関連するMeetingは？
Q7. 原文ではどう書かれていた？
```

評価軸:

- Knowledge extraction accuracy
- duplicate rate
- conflict detection
- link correctness
- semantic search recall
- raw evidence retrieval
- citation correctness
- answer faithfulness
- latency
- cost

## 4. Component Change Map

| Component | 方針 | 改修量 |
|---|---|---:|
| `services/harvest` | Meeting Wiki化 | 大 |
| `services/okf_core` | schema追加 | 中 |
| `services/control_api` | source/project化 | 中 |
| `services/incremental` | document update化 | 中 |
| `services/reindex` | 原則維持 | 小 |
| `services/consumption_mcp` | terminology / Gateway | 小〜中 |
| `services/chat` | direct tools → Gateway | 中 |
| `infra/durable` | 基本維持 / Cognito整理 | 小〜中 |
| `infra/compute` | Existing Gateway integration | 中 |
| `ui` | Meeting Wiki terminology | 中 |

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
- Meeting schema
- Source input固定

### Day 2

- Harvest Agent Meeting対応
- Meeting / Topic / Decision抽出

### Day 3

- Action / Risk
- Existing Wiki update
- Link / Backlink
- S3 Vectors確認

### Day 4

- Consumption MCP Meeting対応
- Existing GatewayへWiki MCP Target追加
- GatewayからManaged KB + Wiki Tool確認

### Day 5

- Chat Agent Gateway接続
- Routing Prompt
- Wiki + Raw Evidence E2E

### Day 6〜8

- UI調整
- conflict / duplicate改善
- Citation
- trace / error handling

### Day 9〜10

- E2E evaluation
- hardening
- internal demo / documentation

## 7. Estimate

```text
PoC                 3〜5営業日
Internal MVP        5〜10営業日
Production hardening 3〜6週間
```

最大の不確実性はInfrastructureではなくHarvest品質。

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
2. HarvestだけMeeting Wiki化
       ↓
3. Wiki Retrievalが壊れていないことを確認
       ↓
4. Existing GatewayへWiki MCP追加
       ↓
5. Chat AgentをGatewayへ接続
       ↓
6. Existing Managed KBとのHybrid回答
       ↓
7. UI / Evaluation
```

最初から全レイヤーを同時に改修しない。特にS3 Vectors / reindexは完成度が高いため、Harvest改修と切り離して扱う。

## 10. Final Implementation Principle

> **元Repoの「Knowledgeを作る・Linkする・Semanticに探す」部分は残し、社内の既存Gateway / Managed KBを「Knowledge Access / Evidence」側へ接続する。**

これにより改修範囲をHarvest中心へ集中できる。
