# Project Knowledge Wiki — 最終版

> 最終更新: 2026-08-08
>
> ベース実装: `aws-samples/sample-okf-llm-wiki`
>
> 方針: 元RepoのOKF / Link / S3 Vectors / MCP / Chat / Observabilityを極力そのまま活かし、Data Wiki固有のHarvestを**Project Knowledge Harvest**へ変更する。議事録はWikiそのものではなく、最初に対応するSource Typeの1つとして扱う。既存のFargate Front / 認証 / AgentCore Gateway / Managed Knowledge Baseを利用する。

## 1. 結論

今回作るものは「議事録Wiki」ではなく、**Project Knowledge Wiki**。

議事録、仕様書、設計資料、報告資料、課題票など複数Sourceから、Projectで継続利用したいKnowledgeを意味単位へ整理・更新する。

```text
Project Sources
  ├─ Meeting minutes
  ├─ PDF / DOCX / PPTX
  ├─ Specification / Design Doc
  ├─ Report
  ├─ Issue / Ticket             Future
  ├─ SharePoint / Teams         Future
  └─ GitHub / DB / SaaS         Future
            │
            ▼
Project Knowledge Harvest Agent
            │
            ▼
Knowledge Reconciliation
create / update / reinforce / conflict / ignore
            │
            ▼
Project Knowledge Wiki
  ├─ Project
  ├─ Topic
  ├─ Decision
  ├─ Requirement
  ├─ Action
  ├─ Risk
  ├─ Issue
  ├─ Artifact
  └─ Meeting
```

Knowledge基盤の役割は次の通り。

- **Raw Source / Managed KB** = 正式な原文・証拠
- **LLM Wiki / OKF** = Agentが編集したCompiled Project Knowledge
- **Link / Backlink** = Knowledge間の明示的な関係
- **S3 Vectors** = 意味から読むべきWikiページを探すSemantic Index
- **AgentCore Gateway** = WikiとRaw Evidenceを統一MCPとして公開するKnowledge Access Layer
- **Chat Agent** = WikiとEvidenceを使い分けてReasoningする
- **DynamoDBSaver** = Chat AgentのConversation State

## 2. 最終アーキテクチャ

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
        S3 Project Wiki
      Compiled Knowledge
              ▲
              │
Project Knowledge Harvest Agent
      deepagents / LangGraph
              ▲
              │
     Project Source Adapters
```

Gatewayには既存Managed KB Targetがすでにあるため、今回追加する中心は**Wiki MCP Target**。

## 3. 議事録の位置づけ

議事録は重要だが、Knowledge Modelそのものではない。

```text
Meeting Minutes = Source / Evidence
Meeting Page    = Sourceを整理したKnowledge Page
Decision        = 会議をまたいで維持するProject Knowledge
Topic           = 継続テーマ
Action          = 実行事項
Risk / Issue    = 継続管理対象
Requirement     = 仕様・要求
Artifact        = 設計書・仕様書・成果物
```

MVPでは議事録・PDF・DOCX・PPTXから始めるが、Harvest本体はSource非依存にする。

## 4. LLM WikiとRAGの違い

Traditional RAGはRaw DocumentをChunk化し、Query時に意味を再構成する。

Project Knowledge WikiはHarvest時に原文を読み、既存Wikiと照合してKnowledgeを編集する。

```text
Traditional RAG
Raw Documents
   ↓
Chunk / Embed
   ↓
Retrieve
   ↓
Query時に意味を再構成

Project Knowledge Wiki
Project Sources
   ↓
Harvest
   ↓
Knowledge Extraction
   ↓
Existing Wiki Search
   ↓
Knowledge Reconciliation
   ↓
OKF Markdown + Links
   ↓
Search / Traverse / Read
```

今回の設計では両者を組み合わせる。

```text
Project Wiki → 整理された現在の理解
Managed KB   → 正式な原文Evidence
```

## 5. 元Repoから残すもの

- OKF Core
- Harvest Agent framework
- Link / Backlink
- S3 Bundle / Versioning
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

特にS3 VectorsはRaw Document RAGではなく、**Wiki Page Discovery用Semantic Index**として残す。

## 6. 今回大きく変えるもの

### Harvest

```text
Before
Glue / Athena / Redshift
        ↓
Dataset / Table / Metric Wiki

After
Project Source Adapters
        ↓
Normalized Evidence
        ↓
Project Knowledge Harvest
        ↓
Project / Topic / Decision / Requirement /
Action / Risk / Issue / Artifact / Meeting
```

最大のポイントはSourceをMarkdown化することではなく、**既存Knowledgeと照合して状態を更新するKnowledge Reconciler**。

### Chat AgentのKnowledge Access

```text
Chat Agent
    ↓ MCP
Existing AgentCore Gateway
    ├─ Wiki MCP Target      ← 今回追加
    └─ Managed KB Target    ← 既存
```

## 7. AgentCore構成

| Runtime | Framework | 役割 |
|---|---|---|
| Project Knowledge Harvest Agent | deepagents / LangGraph | Knowledge Writer / Compiler |
| Consumption MCP | FastMCP | Wiki Tool Server |
| Chat Agent | LangGraph / LangChain | Knowledge Consumer |

AgentはHarvest AgentとChat Agentの2つ。Consumption MCPはTool Server。

## 8. Knowledge Retrieval

| 機構 | 役割 |
|---|---|
| Link / Backlink | 明示的な関係をたどる |
| S3 Vectors | 意味からWiki Conceptを発見 |
| `read_page` | S3上の正式なOKF本文を読む |
| Managed KB | Raw Source / Evidence検索 |
| AgentCore Gateway | Wiki + Managed KBを統一MCP化 |

例:

- 「現在何が決まっている？」→ Wiki優先
- 「なぜそう決まった？」→ Wiki + Managed KB
- 「仕様書の原文は？」→ Managed KB優先
- 「このIssueに関係するDecisionと会議は？」→ Wiki Link / Backlink

## 9. Project Knowledge Model

MVPのコアType:

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

将来必要なら追加:

```text
System
Component
Team
Person
Milestone
Change
```

最初からHeavy Ontologyにはしない。

## 10. Knowledge Reconciliation

Harvestは新Sourceごとに次を判断する。

```text
CREATE     新しいKnowledge
UPDATE     既存Knowledgeの状態・内容が変化
REINFORCE  別Sourceが既存Knowledgeを裏付け
CONFLICT   Source間で矛盾
IGNORE     Knowledgeとして追加価値がない
```

例:

```text
8/1  Gatewayを使う方向で検討
8/8  Gatewayを正式採用
8/15 Gateway案を撤回
```

3つのDecision Pageを乱造するのではなく、同じKnowledgeのLifecycleとしてSourceと履歴を保持する。

## 11. 今回追加しないもの

- DynamoDB Vector Search migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- 新規Custom Vector DB
- 新規Custom RAG Platform

## 12. LLM Wiki Level

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

## 13. 最終方針

このプロジェクトの中心はAWSインフラを増やすことではなく、**Project Knowledge Harvest AgentのKnowledge Compilation / Reconciliation品質**を高めること。

> Project Wikiで「整理された現在の理解」を持ち、Managed KBで「正式な原文」を持ち、AgentCore Gatewayで両者を1つのKnowledge InterfaceとしてAgentへ提供する。

詳細:

- [FINAL_REPORT.md](./FINAL_REPORT.md) — 最終アーキテクチャ
- [REQUIREMENTS.md](./REQUIREMENTS.md) — 改修要件定義
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — 実装計画
- [HARVEST_MIGRATION.md](./HARVEST_MIGRATION.md) — **最重要: Data Wiki Harvest → Project Knowledge Harvest改修仕様**

## 14. 参考

- Base Repo: https://github.com/aws-samples/sample-okf-llm-wiki
- AgentCore Gateway: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- Managed KB Connector: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connector-managed-kb.html
- Bedrock Knowledge Bases: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html

ライセンスはベースRepoの`LICENSE`を再確認し、社内改修時も必要なライセンス表記を保持すること。
