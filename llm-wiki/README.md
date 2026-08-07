# LLM Wiki — 最終版

> 最終更新: 2026-08-08
>
> ベース実装: `aws-samples/sample-okf-llm-wiki`
>
> 方針: 元Repoを極力そのまま活かし、Data Wiki向けHarvestを議事録・業務文書向けLLM Wikiへ変更する。既存のFargate Front / 認証 / AgentCore Gateway / Managed Knowledge Baseを利用する。

## 1. 結論

今回のLLM Wikiは、RAGを置き換えるものではない。

- **Raw Source / Managed KB** = 正式な原文・証拠を探す
- **LLM Wiki / OKF** = Agentが整理したCompiled Knowledge
- **Link / Backlink** = Knowledge間の明示的な関係をたどる
- **S3 Vectors** = 意味から読むべきWikiページを探す
- **AgentCore Gateway** = WikiとRaw Evidenceを統一MCPとして公開する
- **Chat Agent** = WikiとEvidenceを使い分けてReasoningする
- **DynamoDBSaver** = Chat AgentのConversation Stateを保持する

最終構成では、既存Gatewayにすでに接続されているManaged KBをそのまま利用し、**Wiki MCPをGateway Targetとして追加する**。

```text
                         User
                          │
                          ▼
              Existing Fargate Front
              Existing Authentication
                          │
                          ▼
                 Chat Agent
              LangGraph / AgentCore
                 DynamoDBSaver
                          │ MCP
                          ▼
              Existing AgentCore Gateway
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         Wiki MCP               Managed KB
    AgentCore Runtime          Existing Target
              │                   Raw Evidence
      ┌───────┴────────┐
      ▼                ▼
Link / Backlink    S3 Vectors
      │           Semantic Search
      └───────┬────────┘
              ▼
          S3 OKF Wiki
      Compiled Knowledge
              ▲
              │
       Harvest Agent
   deepagents / LangGraph
              ▲
              │
      Meeting / Docs / PDF
```

## 2. LLM WikiとRAGの違い

Traditional RAGは、原文をChunk化して質問時に検索し、LLMがその場で意味を再構成する。

LLM Wikiは、Harvest時に原文を読み、Decision / Topic / Actionなどの**意味単位のKnowledge Page**へ整理し、既存ページとの統合・Link生成・更新まで行う。

```text
Traditional RAG
Raw Documents
   ↓
Chunk / Embed
   ↓
Retrieve
   ↓
Query時に意味を再構成

LLM Wiki
Raw Documents
   ↓
Harvest Agent
   ↓
Semantic Knowledge Compilation
   ↓
OKF Markdown + Links
   ↓
Search / Traverse / Read
```

今回の設計では両者を組み合わせる。

```text
LLM Wiki   → 整理された理解
Managed KB → 原文Evidence
```

## 3. 元Repoから残すもの

`sample-okf-llm-wiki` の以下は基本的に継承する。

- OKF Core
- Harvest Agent framework
- Link / Backlink
- S3 Bundle
- S3 Vectors
- `semantic_search`
- Consumption MCP / FastMCP
- Chat Agent / LangGraph
- DynamoDBSaver
- EventBridge / SQS / Reindex Lambda
- Titan Text Embeddings V2
- UI / Graph View
- CloudWatch / OpenTelemetry
- Terraform

特にS3 Vectorsは、Raw Document RAGではなく**Wiki Page Discovery用のSemantic Index**としてそのまま残す。

## 4. 今回大きく変えるもの

### Harvest

```text
Before
Glue / Athena / Redshift
        ↓
Dataset / Table / Metric Wiki

After
Meeting / PDF / DOCX / PPTX
        ↓
Meeting / Topic / Decision / Action / Risk Wiki
```

### Chat AgentのKnowledge Access

元RepoではChat Agentが`ConsumptionTools`をin-processで直接利用する。

最終To-Beでは、既存社内Gatewayを正式なKnowledge Access Layerとして利用する。

```text
Chat Agent
    ↓ MCP
Existing AgentCore Gateway
    ├─ Wiki MCP Target      ← 今回追加
    └─ Managed KB Target    ← 既存
```

## 5. AgentCore構成

| Runtime | Framework | 役割 |
|---|---|---|
| Harvest Agent | deepagents / LangGraph | Knowledge Writer |
| Consumption MCP | FastMCP | Wiki Tool Server |
| Chat Agent | LangGraph / LangChain | Knowledge Consumer |

AgentはHarvest AgentとChat Agentの2つ。Consumption MCPはAgentではなくTool Server。

## 6. Knowledge Retrievalの役割分担

| 機構 | 役割 |
|---|---|
| Link / Backlink | 明示的な関係をたどる |
| S3 Vectors | 意味からWiki Conceptを発見する |
| `read_page` | S3上の正式なOKF本文を読む |
| Managed KB | Raw Source / Evidenceを検索する |
| AgentCore Gateway | Wiki + Managed KBを統一MCP化する |

例:

- 「今何が決まっている？」→ Wiki優先
- 「その根拠の原文は？」→ Managed KB優先
- 「停止原因と根拠を教えて」→ Wikiで理解 → Managed KBで検証

## 7. 今回追加しないもの

MVPでは以下を追加しない。

- DynamoDB Vector Search
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- 新規Custom Vector DB
- 新規Custom RAG Platform

DynamoDB Vector Searchは有望だが、既存S3 Vectors実装がFreshness / Retry / Metadata Filter / Terraformまで完成しているため、MVPでは変更しない。

## 8. LLM Wiki Level

### Level 1 — Structured Wiki
OKF Markdown + YAML + Source provenance。

### Level 2 — Navigable Wiki
Link / Backlink + Wiki Tools + Graph View。

### Level 3 — Semantic + Evidence
S3 Vectors + Managed KB + Citation。**今回のMVP到達点。**

### Level 4 — Self Improving Knowledge
Evaluation / Feedback / Annotation / Conflict Detection / Re-Harvest。

### Level 5 — Graph / Semantic Model
Thin Ontology / Typed Relations / GraphRAG。必要なユースケースが出た場合のみ追加。

## 9. 最終方針

このプロジェクトの中心はAWSインフラを新規構築することではなく、**Harvest AgentのKnowledge Compilation品質**を高めることにある。

> LLM Wikiで「整理された理解」を持ち、Managed KBで「正式な原文」を持ち、AgentCore Gatewayで両者を1つのKnowledge InterfaceとしてAgentへ提供する。

詳細:

- [FINAL_REPORT.md](./FINAL_REPORT.md) — 最終アーキテクチャレポート
- [REQUIREMENTS.md](./REQUIREMENTS.md) — 改修要件定義
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — 実装計画・対象ファイル・MVP順序

## 10. 参考

- Base Repo: https://github.com/aws-samples/sample-okf-llm-wiki
- AgentCore Gateway: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- Managed KB Connector: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connector-managed-kb.html
- Bedrock Knowledge Bases: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html

ライセンスはベースRepoの`LICENSE`を再確認し、社内改修時も必要なライセンス表記を保持すること。
