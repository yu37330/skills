# LLM Wiki / 議事録Wiki 最終アーキテクチャレポート

> Final: 2026-08-08
>
> Base: `aws-samples/sample-okf-llm-wiki`
>
> 前提: 既存Fargate Front、既存ユーザー認証、既存AgentCore Gateway、Gateway接続済みManaged Knowledge Baseを利用する。

## 1. Executive Summary

最終構成は、`sample-okf-llm-wiki` のWiki生成・検索機構をできるだけ維持し、Data Wiki固有のHarvest処理のみを議事録・業務文書向けへ変更する。

Knowledgeを次の4層に分ける。

```text
Raw Evidence Layer
  Managed KB / Raw Documents

Compiled Knowledge Layer
  OKF Markdown on S3

Knowledge Navigation Layer
  Link / Backlink + S3 Vectors + Wiki MCP

Knowledge Access / Reasoning Layer
  AgentCore Gateway + Chat Agent
```

役割は明確に分離する。

```text
Raw Source        = Source of Truth / Evidence
OKF Wiki          = Compiled Knowledge
Link / Backlink   = Structural Navigation
S3 Vectors        = Semantic Wiki Navigation
Managed KB        = Raw Evidence Retrieval
AgentCore Gateway = Unified Knowledge Access
Chat Agent        = Reasoning / User Interaction
DynamoDBSaver     = Conversation State
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
               S3 OKF Wiki
            Compiled Knowledge
                   ▲
                   │
       ┌───────────┴────────────┐
       │ Harvest Agent          │
       │ deepagents / LangGraph │
       │ AgentCore Runtime      │
       └───────────┬────────────┘
                   ▲
                   │
        Meeting / PDF / DOCX / PPTX
```

## 3. Agent / Runtime構成

### 3.1 Harvest Agent

- 実行基盤: Amazon Bedrock AgentCore Runtime
- Framework: deepagents / LangGraph
- 役割: Knowledge Writer / Compiler
- 主な再利用対象:
  - FilesystemBackend
  - OKFGuardMiddleware
  - Subagents
  - Reviewer
  - LinkGraph
  - CloudWatch / OTEL trace

元RepoではGlue / Athena / RedshiftからData Wikiを生成する。

```text
Before
Glue / Athena / Redshift
        ↓
Harvest Agent
        ↓
Dataset / Table / Metric Wiki
```

今回変更する。

```text
After
Meeting / Documents
        ↓
Harvest Agent
        ↓
Meeting / Topic / Decision / Action / Risk
        ↓
OKF Wiki
```

最大の開発対象はこのHarvest Agentである。

### 3.2 Consumption MCP

- 実行基盤: AgentCore Runtime
- Framework: FastMCP
- Protocol: MCP
- 役割: Wiki Tool Server

主なTool:

```text
list_domains
list_directory
read_page
glob
grep
get_backlinks
semantic_search
```

今回、Consumption MCPを既存AgentCore Gatewayの新しいTargetとして登録する。

### 3.3 Chat Agent

- 実行基盤: AgentCore Runtime
- Framework: LangGraph / LangChain
- Pattern: ReAct / tool calling
- Conversation state: DynamoDBSaver

元RepoではWikiの`ConsumptionTools`をin-processで直接importする。

```text
Current sample
Chat Agent
   ↓
ConsumptionTools
```

今回のTo-Beでは社内共通GatewayをKnowledge Access Layerとして使う。

```text
To-Be
Chat Agent
   ↓ MCP
Existing AgentCore Gateway
   ├─ Wiki MCP
   └─ Managed KB
```

Network Hopは1段増えるが、Knowledge interface、Tool discovery、policy、observabilityを共通化できるメリットを優先する。

## 4. Knowledge Storage / Retrieval

### 4.1 S3 OKF Wiki

S3上のMarkdownがCompiled Knowledgeの正本。

```text
S3 Bundle
  └─ OKF Markdown
      ├─ Meeting
      ├─ Topic
      ├─ Decision
      ├─ Action
      └─ Risk
```

S3はversioningを維持し、Harvest失敗・誤更新からrollback可能な設計を継承する。

### 4.2 Link / Backlink

明示的なWiki Linkから関係をたどる。

例:

```text
Meeting → Decision
Meeting → Action
Decision → Topic
Decision → Source Meeting
Action → Decision
Topic → Related Decisions
```

MVPでは重いOntologyを導入せず、Markdown Link / BacklinkをLightweight Graphとして使う。

### 4.3 S3 Vectors

S3 Vectorsは残す。

目的はRaw Document RAGではなく、**読むべきWiki Conceptを意味から発見すること**。

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

Embeddingは1 Concept = 1 Vectorを基本とし、Title / Type / Description / Tags / Overviewを中心にVector化する既存設計を継承する。

更新フローも維持する。

```text
S3 OKF change
   ↓
EventBridge
   ↓
SQS
   ↓
Reindex Lambda
   ↓
Titan V2
   ↓
S3 Vectors
```

DynamoDB FreshnessによるS3 sequencer管理・retry設計も維持する。

### 4.4 Managed Knowledge Base

既存Managed KBはRaw Evidence検索に利用する。

```text
Raw Meeting / PDF / PPTX / DOCX / Formal Docs
                    ↓
             Existing Managed KB
                    ↓
              Retrieve / Agentic Retrieval
```

LLM WikiとManaged KBは競合しない。

```text
LLM Wiki   = 整理された現在の理解
Managed KB = 正式な原文とEvidence
```

## 5. Gatewayを中心にしたKnowledge Access

既存AgentCore Gatewayは今回の正式なKnowledge Access Layerとする。

```text
Existing AgentCore Gateway
        │
        ├─ Existing Managed KB Target
        │
        └─ New Wiki MCP Target
```

これによりChat Agentだけでなく、将来的にClaude Code、Copilot、工程分析Agent、その他業務Agentも同じMCP interfaceを利用できる。

```text
Chat Agent
Coding Agent
Business Agent
Process Analysis Agent
          │
          ▼
AgentCore Gateway
          │
     ┌────┴────┐
     ▼         ▼
 Wiki MCP   Managed KB
```

## 6. Query Routing Policy

Chat AgentにはKnowledge Sourceの使い分けを明示する。

### Wiki優先

- 現在何が決まっているか
- ProjectのCurrent State
- Decision一覧
- Action一覧
- Topicの整理
- 会議間の関係
- 過去Decisionとの関係

### Managed KB優先

- 原文を確認したい
- 正確な数値・表現
- 発言のEvidence
- Citation
- Wikiに要約されなかった詳細

### Hybrid

```text
Question
  ↓
Wikiで現在の理解を取得
  ↓
Managed KBで原文検証
  ↓
Answer + Citation
```

例: 「設備Aの停止原因と、その根拠を教えて」

```text
Wiki      → 現在整理された原因
Managed KB→ 議事録原文 / 資料
Chat Agent→ 両方を統合して回答
```

## 7. Conversation Memory

Chat Agentの会話状態は既存DynamoDBSaverを維持する。

```text
LangGraph
   ↓
DynamoDBSaver
   ↓
DynamoDB Chat Checkpoints
```

役割:

- Messages
- Tool Calls
- Checkpoints
- Pending state
- Thread continuation

大きなCheckpointは既存実装どおりS3へoffload可能。

これはLong-term semantic memoryではない。AgentCore MemoryはMVPでは追加しない。

## 8. DynamoDBの役割

当面Vector Storeには変更しない。

```text
DynamoDB
├─ Registry
├─ Freshness
├─ Chat Checkpoints
├─ Chat Threads
└─ Annotations
```

DynamoDB Vector Searchは将来候補だが、S3 Vectorsの既存実装が完成度高く、移行メリットがMVPリスクを上回らないため今回は見送る。

## 9. Authentication / Authorization

Application user authenticationは既存Fargate / Dashboard側を利用し、新しいCognito login systemは構築しない。

一方でAWS内部では以下を維持する。

- IAM execution roles
- AgentCore / Gateway authorization
- S3 / DynamoDB least privilege
- Service-to-service credentials
- CloudWatch trace access control

つまり、`新規Cognitoを作らない` と `AWS内部認可をなくす` は別である。

## 10. LLM Wiki Knowledge Model

初期Knowledge Type:

### Meeting

- `meeting_id`
- `meeting_date`
- `project`
- `participants`
- `sources`
- `status`
- `generated`
- `verified`

### Topic

- `topic_id`
- `title`
- `project`
- `related_meetings`
- `related_decisions`
- `related_actions`
- `sources`
- `status`

### Decision

- `decision_id`
- `decision`
- `reason`
- `decided_at`
- `project`
- `related_topics`
- `sources`
- `status`

### Action

- `action_id`
- `description`
- `owner`
- `due_date`
- `status`
- `project`
- `source`

### Risk

- `risk_id`
- `description`
- `impact`
- `mitigation`
- `status`
- `project`
- `sources`

## 11. Incremental Knowledge Compilation

Harvestは単純な「議事録→要約」ではなく、既存Wikiを参照してKnowledgeの状態を判断する。

```text
New Source
   ↓
Parse / Extract
   ↓
Search Existing Wiki
   ↓
Classify
   ├─ create
   ├─ update
   ├─ reinforce
   ├─ conflict
   └─ ignore
   ↓
Generate / Edit OKF
   ↓
Link / Backlink validation
   ↓
Publish
```

重要ルール:

1. 同じKnowledge Pageを乱造しない
2. Decision変更時に履歴を消さない
3. Source provenanceを必須にする
4. Conflictを無言で上書きしない
5. Link切れを検査する
6. Harvest失敗で現在のpublished Wikiを壊さない

## 12. Level Model

### Level 1 — Structured Wiki

OKF Markdown + YAML + Source provenance。

### Level 2 — Navigable Wiki

Link / Backlink + Wiki Tools + Graph View。

### Level 3 — Semantic + Evidence

S3 Vectors + Managed KB + Citation。

**今回のMVP目標。**

### Level 4 — Self Improving Knowledge

Evaluation / Feedback / Annotation / Freshness / Conflict Detection / Re-Harvest。

### Level 5 — Graph / Semantic Model

Thin Ontology / Typed Relation / Knowledge Graph / GraphRAG。

明確なユースケースが出た場合だけ追加する。

## 13. Existing / Change / Add / Out of Scope

### 現行から継承

- OKF Core
- Harvest framework
- S3 Bundle / versioning
- Link / Backlink
- S3 Vectors
- semantic_search
- Consumption MCP
- Chat Agent framework
- DynamoDBSaver
- UI / Graph View
- EventBridge / SQS / Lambda
- CloudWatch / OTEL
- Terraform

### 現行から変更

- Data Harvest → Meeting / Document Harvest
- Dataset / Table model → Meeting / Topic / Decision / Action / Risk
- Chat Agent direct ConsumptionTools → AgentCore Gateway MCP
- Cognito UI依存 → Existing application auth boundary

### 既存社内環境と統合

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed KB Target

### 新規追加

- Wiki MCPを既存Gateway Targetへ登録
- Meeting Wiki schema / prompt / skills
- Wiki + Managed KB routing policy

### 今回スコープ外

- DynamoDB Vector migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- New custom vector DB
- New custom RAG platform

## 14. MVP Acceptance Criteria

1. 議事録・業務文書を入力できる
2. Harvest AgentがMeeting / Topic / Decision / Action / Riskを抽出できる
3. 既存Wikiを検索してcreate/update/reinforceを判断できる
4. OKF MarkdownをS3にpublishできる
5. Link / Backlinkが生成・検索できる
6. S3 Vectors semantic_searchが動く
7. Consumption MCPからread/searchできる
8. Wiki MCPを既存Gateway Targetとして利用できる
9. 既存Managed KB Targetを同じGatewayから利用できる
10. Chat AgentがGateway経由で両Tool群を使える
11. Wiki → Evidence verificationができる
12. Raw source Citationを返せる
13. DynamoDBSaverで会話を継続できる
14. Failed harvestがpublished Wikiを破壊しない
15. CloudWatch / OTELでAgent・Tool traceを確認できる

## 15. Development Priority

```text
Priority 1
Harvest Agent品質

Priority 2
OKF Meeting Wiki schema

Priority 3
Wiki MCP → Existing Gateway

Priority 4
Chat Agent → Gateway routing

Priority 5
UI adjustment

Priority 6
Evaluation / operational hardening
```

AWS infrastructureをゼロから作るプロジェクトではない。最重要なのはHarvestがKnowledgeを正しくcompile/updateできるかである。

## 16. Schedule Estimate

既存Repo、既存Fargate、既存Auth、既存Gateway、既存Managed KBを使う場合:

- PoC: 3〜5営業日
- 社内MVP: 5〜10営業日
- Production hardening: 3〜6週間

## 17. Final Decision

最終方針は以下。

```text
Raw Evidence
      ↓
Existing Managed KB

Raw Documents
      ↓
Harvest Agent
      ↓
OKF Wiki
      ↓
Link / Backlink + S3 Vectors
      ↓
Wiki MCP

Wiki MCP + Managed KB
      ↓
Existing AgentCore Gateway
      ↓
Chat / Business / Coding Agents
```

> **LLM Wikiで整理された理解を持ち、Managed KBで原文Evidenceを持ち、AgentCore Gatewayで両者を統一Knowledge InterfaceとしてAgentへ提供する。**

この構成を議事録Wiki MVPの最終アーキテクチャとする。

## References

- Base Repo: https://github.com/aws-samples/sample-okf-llm-wiki
- AgentCore Gateway: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- Managed KB Gateway Connector: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connector-managed-kb.html
- Bedrock Knowledge Bases: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
