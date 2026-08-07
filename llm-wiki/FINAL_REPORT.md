# Project Knowledge Wiki 最終アーキテクチャレポート

> Final: 2026-08-08
>
> Base: `aws-samples/sample-okf-llm-wiki`
>
> 前提: 既存Fargate Front、既存ユーザー認証、既存AgentCore Gateway、Gateway接続済みManaged Knowledge Baseを利用する。

## 1. Executive Summary

本プロジェクトは「議事録Wiki」ではなく、**Project Knowledge Wiki**を構築する。

議事録は最初に対応するSource Typeの1つであり、将来的には仕様書、設計資料、課題票、レポート、SharePoint、Teams、GitHub等へSourceを拡張できる設計とする。

元Repoの以下は極力維持する。

```text
OKF Core
S3 Bundle / Versioning
Link / Backlink
S3 Vectors
Consumption MCP
Chat Agent
DynamoDBSaver
EventBridge / SQS / Reindex
UI / Graph View
Observability / Terraform
```

最大改修対象はHarvest Agentであり、Data Wiki固有の知識生成を、**Project Knowledge Compilation / Reconciliation**へ置き換える。

Knowledgeを4層に分ける。

```text
Raw Evidence Layer
  Existing Managed KB / Project Sources

Compiled Knowledge Layer
  Project Knowledge Wiki / OKF Markdown on S3

Knowledge Navigation Layer
  Link / Backlink + S3 Vectors + Wiki MCP

Knowledge Access / Reasoning Layer
  Existing AgentCore Gateway + Chat Agent
```

## 2. Final Architecture

```text
                         ┌──────────────────────┐
                         │        User          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         Existing Fargate Front
                         Existing Authentication
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │ Chat Agent                 │
                    │ LangGraph / LangChain      │
                    │ AgentCore Runtime          │
                    │ DynamoDBSaver              │
                    └─────────────┬──────────────┘
                                  │ MCP
                                  ▼
                    ┌────────────────────────────┐
                    │ Existing AgentCore Gateway│
                    │ Unified Knowledge Access   │
                    └─────────────┬──────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   ▼                             ▼
       ┌──────────────────────┐       ┌──────────────────────┐
       │ Wiki MCP Target      │       │ Managed KB Target    │
       │ NEW Gateway Target   │       │ EXISTING             │
       └──────────┬───────────┘       └──────────┬───────────┘
                  │                              │
                  ▼                              ▼
       Consumption MCP                     Managed KB
       AgentCore Runtime                   Raw Evidence
                  │
          ┌───────┴─────────┐
          ▼                 ▼
   Link / Backlink      S3 Vectors
   Structural Search    Semantic Search
          │                 │
          └────────┬────────┘
                   ▼
           S3 Project Wiki
            OKF Markdown
         Compiled Knowledge
                   ▲
                   │
       ┌───────────┴─────────────────┐
       │ Project Knowledge Harvest   │
       │ deepagents / LangGraph      │
       │ AgentCore Runtime           │
       └───────────┬─────────────────┘
                   ▲
                   │
           Project Source Adapters
      ┌────────────┼───────────────┐
      ▼            ▼               ▼
   Meeting      Documents      Future Sources
 PDF/DOCX/PPTX  Specs/Reports  Tickets/SharePoint/...
```

## 3. SourceとKnowledgeを分離する

Project Wikiの設計で最重要なのは、**SourceとKnowledgeを同一視しないこと**。

### Source / Evidence

```text
Meeting minutes
Specification
Design document
Report
Presentation
Issue / Ticket
Email / Chat
```

### Compiled Knowledge

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

MeetingはSource provenanceを保持するKnowledge Typeでもあるが、DecisionやRequirementなどは複数Sourceを横断して継続更新される。

例:

```text
Meeting A ─┐
Spec v3  ──┼─→ Decision: AgentCore Gateway採用
Report   ──┘
```

別Sourceが同じDecisionを裏付けても新しいDecision Pageを作らず、既存Pageを`reinforce`する。

## 4. Agent / Runtime構成

### 4.1 Project Knowledge Harvest Agent

- Runtime: Amazon Bedrock AgentCore Runtime
- Framework: deepagents / LangGraph
- Role: Knowledge Writer / Compiler

元Repo:

```text
Glue / Athena / Redshift
        ↓
Harvest Agent
        ↓
Dataset / Table / Metric Wiki
```

To-Be:

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
        ↓
Project Wiki
```

再利用:

- deepagents supervisor
- subagents
- reviewer
- FilesystemBackend
- OKFGuardMiddleware
- LinkGraph
- CloudWatch / OTEL tracing

置換対象:

- Glue/Table前提
- table-author等のData固有subagent
- run_sql/sample_rows中心のgrounding
- Data Wiki authoring prompt / skill

### 4.2 Consumption MCP

- Runtime: AgentCore Runtime
- Framework: FastMCP
- Role: Wiki Tool Server

基本Toolは維持。

```text
list_domains
list_directory
read_page
glob
grep
get_backlinks
semantic_search
```

Data Wiki固有のTool description / terminologyをProject Wikiへ変更し、既存AgentCore GatewayのWiki MCP Targetとして登録する。

### 4.3 Chat Agent

- Runtime: AgentCore Runtime
- Framework: LangGraph / LangChain
- Pattern: ReAct / Tool Calling
- Conversation State: DynamoDBSaver

元Repoでは`ConsumptionTools`をin-process利用するが、To-Beでは既存Gatewayを正式なKnowledge Access Layerにする。

```text
Chat Agent
   ↓ MCP
Existing AgentCore Gateway
   ├─ Wiki MCP
   └─ Existing Managed KB
```

## 5. Project Knowledge Model

MVPで扱うコアType:

### Project
Project全体の目的、状態、重要Knowledgeへの入口。

### Topic
会議や文書をまたぐ継続テーマ。

### Decision
決定事項とそのLifecycle。Project Wikiの中心Knowledgeの1つ。

推奨Lifecycle:

```text
proposed → active → superseded / cancelled
```

### Requirement
要求、仕様、制約、受入条件。

### Action
Owner、Due、Statusを持つ実行事項。

### Risk
将来起こり得るリスク、Impact、Mitigation。

### Issue
既に発生している問題、Blocker、調査事項。

### Artifact
仕様書、設計書、成果物などProject資産へのKnowledge Entry。

### Meeting
会議自体の概要と、その会議から生じたDecision / Action / Topicへの入口。

将来必要になればSystem / Component / Team / Person / Milestone / Changeを追加する。

## 6. Knowledge Reconciliation — Harvestの本丸

HarvestはSourceを要約するだけでは不十分。

新Sourceを既存Wikiと照合し、Knowledgeごとに次を判定する。

```text
CREATE
  既存Wikiに存在しない新しいKnowledge

UPDATE
  同一Knowledgeの状態・内容が変わった

REINFORCE
  別Sourceが既存Knowledgeを裏付けた

CONFLICT
  既存KnowledgeとSourceが矛盾する

IGNORE
  Knowledgeとして追加・更新価値がない
```

例:

```text
8/1  Gatewayを使う方向で検討
8/8  Gatewayを正式採用
8/15 Gateway案を撤回
```

望ましい結果:

```text
decisions/adopt-agentcore-gateway.md

status: cancelled
sources:
  - 2026-08-01 meeting
  - 2026-08-08 meeting
  - 2026-08-15 meeting

history:
  proposed → active → cancelled
```

3ページのDecisionを乱造しない。

詳細は`HARVEST_MIGRATION.md`を正本とする。

## 7. Grounding / Provenance

元RepoではGlue metadataと`run_sql` / `sample_rows`が事実確認手段になる。

Project Wikiでは次へ置き換える。

```text
Normalized Source Text
Original Source location
Existing Managed KB retrieval
Existing Wiki
Source metadata
```

Knowledge Pageは必ずSource provenanceを保持する。

最低限:

```text
sources
generated
verified
status
updated_at
```

重要なDecision / Requirement / RiskをSourceなしでpublishしない。

## 8. S3 OKF Wiki

S3上のOKF MarkdownがCompiled Knowledgeの正本。

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

Versioning、safe publish、rollbackの既存設計を維持する。

## 9. Link / Backlink

Markdown Link / BacklinkをLightweight Graphとして利用する。

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

MVPでHeavy Ontologyは導入しない。

## 10. S3 Vectors

S3 Vectorsはそのまま維持する。

目的はRaw Document RAGではなく、読むべきWiki Conceptを意味から発見すること。

```text
Question
   ↓
Titan Text Embeddings V2
   ↓
S3 Vectors semantic_search
   ↓
Candidate Concept IDs
   ↓
read_page
   ↓
S3 OKF Markdown
```

既存の1 Concept = 1 Vector、EventBridge → SQS → Reindex Lambda、sequencer dedup、retry / DLQを維持する。

## 11. Existing Managed KB

Managed KBはRaw Evidence検索に利用する。

```text
Raw Project Sources
        ↓
Existing Managed KB
        ↓
Retrieve / Agentic Retrieval
```

役割分担:

```text
Project Wiki = 整理された現在の理解
Managed KB   = 正式な原文・Evidence
```

## 12. Existing AgentCore Gateway

既存Gatewayを正式なKnowledge Access Layerとする。

```text
Existing AgentCore Gateway
   ├─ Existing Managed KB Target
   └─ New Wiki MCP Target
```

将来的にChat Agent以外の業務Agentも同じInterfaceを利用できる。

## 13. Query Routing Policy

### Wiki優先

- ProjectのCurrent State
- 現在有効なDecision
- Topic summary
- Action / Issue / Risk
- Knowledge間の関係

### Managed KB優先

- 正確な原文
- 数値
- Source Evidence
- Citation
- Wikiへ落としていない詳細

### Hybrid

```text
Wikiで理解
  ↓
Managed KBで検証
  ↓
Answer + Citation
```

## 14. Conversation Memory

既存DynamoDBSaverを維持する。

これはConversation Checkpointであり、Long-term Semantic Memoryではない。

MVPではAgentCore Memoryを追加しない。

## 15. Authentication / Authorization

User Authenticationは既存Fargate / Dashboard境界を利用する。

AWS内部では以下を維持する。

- IAM execution role
- Gateway / target authorization
- S3 / DynamoDB least privilege
- Service-to-service credentials
- CloudWatch access control

## 16. Scope分類

### 継承

- OKF Core
- Harvest framework
- S3 Bundle / versioning
- Link / Backlink
- S3 Vectors
- Consumption MCP
- Chat framework
- DynamoDBSaver
- UI / Graph View
- Reindex pipeline
- Observability / Terraform

### 変更

- Data Harvest → Project Knowledge Harvest
- Glue/Table model → Project Knowledge Model
- Data source access → Source Adapter abstraction
- Chat direct tools → Existing AgentCore Gateway
- Cognito UI依存 → Existing application auth boundary

### 既存環境と統合

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed KB Target

### 追加

- Wiki MCP Gateway Target
- Project Knowledge schema
- Source Adapter layer
- Knowledge Reconciler
- Project Knowledge authoring skill / prompt
- Wiki + KB routing policy

### MVPスコープ外

- DynamoDB Vector migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Heavy Ontology
- New custom vector DB / RAG

## 17. MVP Scope

対応Source:

```text
Meeting minutes
Markdown / text
PDF
DOCX
PPTX
```

必須Knowledge:

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

MVP完成条件は、単に議事録からMarkdownを生成することではない。

> **複数のProject Sourceを既存Wikiと照合し、Knowledgeをcreate / update / reinforce / conflictとして継続管理し、Chat AgentがGateway経由でWikiとRaw Evidenceを使い分けてCitation付き回答を返せること。**

## 18. Final Principle

このシステムの本質はKnowledge Storageではなく、**Knowledge Compilation + Reconciliation**。

```text
Raw Evidence
      ↓
Knowledge Extraction
      ↓
Existing Knowledge Comparison
      ↓
Knowledge Reconciliation
      ↓
Structured Project Wiki
      ↓
Semantic / Structural Navigation
      ↓
Evidence Verification
      ↓
Agent Reasoning
```

Project Wikiで「整理された理解」を持ち、Managed KBで「正式な原文」を持ち、AgentCore Gatewayで両者を1つのKnowledge Interfaceとして提供する。
