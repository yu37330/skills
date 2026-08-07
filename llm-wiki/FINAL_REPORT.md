# Project Knowledge Wiki 最終アーキテクチャレポート — OKF v0.2準拠

> Final: 2026-08-08
>
> Base: `aws-samples/sample-okf-llm-wiki`
>
> Knowledge Format: **Open Knowledge Format (OKF) v0.2**
>
> 前提: Existing Fargate Front、Existing Authentication、Existing AgentCore Gateway、Gateway接続済みManaged Knowledge Baseを利用する。

## 1. Executive Summary

本システムは、AWS Samplesの`sample-okf-llm-wiki`をベースに、Data Wiki固有のHarvest知能を**Project Knowledge Compilation / Reconciliation**へ変更する。

議事録は最初のSource Typeであり、最終ターゲットは議事録Wikiではなく**Project Knowledge Wiki**である。

Knowledgeは4層に分離する。

```text
Raw Evidence Layer
  Raw Project Sources + Existing Managed KB

Compiled Knowledge Layer
  OKF v0.2 Bundle on S3

Knowledge Navigation Layer
  Markdown Links / Backlinks + S3 Vectors + Wiki MCP

Knowledge Access / Reasoning Layer
  Existing AgentCore Gateway + Chat Agent
```

役割:

```text
Raw Source        = Evidence / Source Material
OKF v0.2          = Canonical Knowledge Format
S3 OKF Bundle     = Compiled Knowledge Source of Truth
Link / Backlink   = Structural Navigation
S3 Vectors        = Semantic Concept Discovery
Managed KB        = Raw Evidence Retrieval
AgentCore Gateway = Unified Knowledge Access
Harvest Agent     = OKF Producer
Chat Agent        = OKF Consumer / Reasoning
DynamoDBSaver     = Conversation State
```

## 2. Final Architecture

```text
                         User
                          │
                          ▼
                Existing Fargate Front
                Existing Authentication
                          │
                          ▼
                ┌─────────────────────┐
                │ Chat Agent          │
                │ LangGraph/LangChain │
                │ AgentCore Runtime   │
                │ DynamoDBSaver       │
                └──────────┬──────────┘
                           │ MCP
                           ▼
                ┌─────────────────────┐
                │ Existing AgentCore  │
                │ Gateway             │
                └──────────┬──────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
        ┌────────────────┐  ┌──────────────────┐
        │ Wiki MCP       │  │ Existing         │
        │ Gateway Target │  │ Managed KB Target│
        └───────┬────────┘  └────────┬─────────┘
                │                    │
                ▼                    ▼
        Consumption MCP         Raw Evidence
        AgentCore Runtime
                │
         ┌──────┴──────┐
         ▼             ▼
   Link / Backlink   S3 Vectors
         │         Semantic Discovery
         └──────┬──────┘
                ▼
          S3 OKF v0.2 Bundle
         Compiled Knowledge
                ▲
                │
       ┌────────┴─────────┐
       │ Harvest Agent    │
       │ deepagents       │
       │ LangGraph        │
       └────────┬─────────┘
                ▲
                │
        Project Sources
 Meeting / Spec / Design / Report / Issue
```

## 3. OKF v0.2を正式Knowledge Formatとして採用

本システムはOKFを単なる「Markdownっぽい形式」としてではなく、**v0.2 Compliance Profileを持つ正式なKnowledge Format**として扱う。

### Conformance Minimum

- `index.md` / `log.md`以外のConcept `.md`はvalid YAML frontmatterを持つ
- `type`は必須
- `index.md` / `log.md`はreserved filename
- root `index.md`に`okf_version: "0.2"`
- Unknown Type / extension keysを許容・保持

### Project Profileで標準化するOptional Families

- `sources` — provenance
- `generated` — producer / meaningful last change
- `verified` — verification / trust
- `status` — OKF lifecycle
- `stale_after` — freshness

詳細な正本は`OKF_V02_PROFILE.md`。

## 4. OKF LifecycleとProject Lifecycleを分離

OKF標準`status`は次だけを使用する。

```text
draft
stable
deprecated
```

Business stateはproducer-defined extensionへ分離する。

```yaml
status: stable
decision_state: active
```

例:

```text
Decision    → decision_state
Requirement → requirement_state
Action      → action_state
Issue       → issue_state
Risk        → risk_state
Project     → project_state
```

これにより、OKF consumerのlifecycle解釈とProject業務状態を混同しない。

## 5. Canonical OKF Concept

```yaml
---
type: Decision
title: AgentCore GatewayをKnowledge Access Layerとして採用
description: Wiki MCPとManaged KBを既存Gateway経由で利用する。
tags: [agentcore, knowledge-platform]
status: stable
stale_after: 2026-11-08
sources:
  - id: meeting-20260808
    resource: /meetings/2026-08-08-architecture.md
    title: Architecture Meeting
    author: team:project-a
    last_modified: 2026-08-08
generated:
  by: project-knowledge-harvest/1.0
  at: 2026-08-08T07:30:00Z
verified:
  - by: process:project-knowledge-reviewer
    at: 2026-08-08T07:31:00Z
project_id: project-a
decision_id: decision-agentcore-gateway
decision_state: active
---
```

重要claimは`sources[].id`と同じlabelのMarkdown footnoteでattributionできる。

## 6. Bundle Structure

```text
wiki/
├─ index.md
├─ log.md
├─ projects/
├─ topics/
├─ decisions/
├─ requirements/
├─ actions/
├─ risks/
├─ issues/
├─ artifacts/
├─ meetings/
└─ references/
```

root `index.md`はbundle version宣言と全体入口。各directoryの`index.md`はprogressive disclosure、`log.md`はdate-grouped update historyとして利用する。

## 7. Project Knowledge Model

MVP Type:

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

OKFは固定taxonomyを持たないため、これらは合法なproducer-defined typeである。

## 8. Harvest Agent — 最大の改修対象

### Before

```text
Glue / Athena / Redshift
        ↓
Data Understanding
        ↓
Dataset / Table / Metric Wiki
```

### To-Be

```text
Project Sources
      ↓
Source Adapter
      ↓
Normalized Evidence
      ↓
Knowledge Candidate Extraction
      ↓
Existing OKF Search
      ↓
Knowledge Reconciliation
      ├─ CREATE
      ├─ UPDATE
      ├─ REINFORCE
      ├─ CONFLICT
      └─ IGNORE
      ↓
OKF v0.2 Authoring
      ↓
Reviewer
      ↓
OKF Guard / Lint
      ↓
Publish
```

本質は「Sourceごとの文書生成」ではなく、Sourceをまたいだ**living knowledge maintenance**。

### CREATE
新Knowledge。review前は`status: draft`、publish後は`stable`。

### UPDATE
同一Knowledgeの意味・状態変化。stable IDを維持し`generated.at`を更新する。

### REINFORCE
別Sourceが既存Knowledgeを裏付ける。Conceptを増やさず`sources`を追加する。

### CONFLICT
無言で上書きせずReviewへ回す。

### IGNORE
Project Knowledgeとして追加価値なし。

## 9. Provenance / Trust / Freshness

### Provenance

`sources`をCanonicalにする。各entryの`resource`は必須。

### Trust

```text
verifiedなし      → unverified
machine verifier  → machine-confirmed
human:* verifier  → human-reviewed
```

Trust scoreをfrontmatterへ固定値として保存しない。

### Freshness

`stale_after: YYYY-MM-DD`を利用する。

`updated_at`を補助fieldとして残すことは可能だが、意味的な最終変更時刻は`generated.at`をCanonicalとする。

## 10. Link / Backlink

OKF v0.2ではConcept間Relationはstandard Markdown links。

```markdown
このDecisionは[旧Decision](/decisions/old-decision.md)を置き換える。
```

Linkはuntyped edge。Relationの意味は周辺proseで表す。

MVPではNeptuneやHeavy Ontologyを追加せず、Markdown Link + BacklinkをLightweight Graphとして使う。

## 11. S3 Vectors

S3 Vectorsは維持する。

```text
Question
   ↓
Titan Text Embeddings V2
   ↓
S3 Vectors
   ↓
Candidate OKF Concepts
   ↓
read_page
   ↓
S3 OKF Markdown
```

Raw Document RAGではなく**OKF Concept Discovery Index**として扱う。

既存の1 Concept = 1 Vector、deterministic key、EventBridge→SQS→Reindex Lambda→Titan V2の更新設計を維持する。

## 12. Managed Knowledge Base

既存Managed KBはRaw Evidence Retrievalに利用する。

```text
Raw Project Sources
        ↓
Existing Managed KB
        ↓
Retrieve / Agentic Retrieval
```

```text
OKF Wiki   = 整理された現在の理解
Managed KB = 正式な原文 / Evidence
```

OKF BundleそのものをManaged KBへ入れることはMVPの前提にしない。OKF discoveryは既存S3 Vectorsが担う。

## 13. AgentCore Gateway

Existing Gatewayを正式なKnowledge Access Layerとする。

```text
Existing AgentCore Gateway
   ├─ Existing Managed KB Target
   └─ Wiki MCP Target
```

Chat AgentもGateway経由へ寄せる。

```text
Chat Agent
   ↓ MCP
Existing Gateway
   ├─ Wiki MCP
   └─ Managed KB
```

## 14. Runtime / Framework

| Runtime | Framework | Role |
|---|---|---|
| Harvest Agent | deepagents / LangGraph | OKF Producer / Knowledge Compiler |
| Consumption MCP | FastMCP | OKF Wiki Tool Server |
| Chat Agent | LangGraph / LangChain | OKF Consumer / Reasoning |

## 15. Query Routing

### Wiki優先

- Current project state
- Decision / Requirement / Action / Issue / Risk
- Topic summary
- Knowledge relationships
- historical transition

### Managed KB優先

- exact wording
- exact number
- source evidence
- citation
- raw details

### Hybrid

```text
Wiki understanding
      ↓
Managed KB verification
      ↓
Answer + Citation
```

## 16. Conversation State

既存DynamoDBSaverを維持する。

```text
LangGraph
   ↓
DynamoDBSaver
   ↓
DynamoDB Chat Checkpoints
```

これはLong-term semantic memoryではない。AgentCore MemoryはMVPでは追加しない。

## 17. Existing / Change / Integrate

### Keep

- OKF Core
- S3 Bundle / versioning
- Link / Backlink
- S3 Vectors
- Reindex pipeline
- Consumption MCP
- Chat framework
- DynamoDBSaver
- UI / Graph View
- CloudWatch / OTEL
- Terraform

### Change

- Data Harvest → Project Knowledge Harvest
- Data source model → Source Adapter
- Data model → Project Knowledge Types
- old frontmatter conventions → OKF v0.2 Profile
- Chat direct tools → Existing Gateway MCP
- Cognito UI dependency → Existing authentication boundary

### Integrate

- Existing Fargate Front
- Existing Authentication
- Existing AgentCore Gateway
- Existing Managed KB Target

## 18. MVPでは追加しない

- DynamoDB Vector migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- New custom vector DB
- New custom RAG platform

## 19. MVP Acceptance

- [ ] root `index.md`に`okf_version: "0.2"`
- [ ] Conceptにvalid frontmatter + `type`
- [ ] `sources` / `generated` / `verified` / `status` / `stale_after`準拠
- [ ] Business stateをextension keysへ分離
- [ ] Meeting / Document source ingest
- [ ] Project Knowledge extraction
- [ ] Reconciliation 5分類
- [ ] Duplicate抑止
- [ ] Conflict review
- [ ] Link / Backlink
- [ ] `index.md` / `log.md`更新
- [ ] S3 Vectors semantic discovery
- [ ] Wiki MCP
- [ ] Existing Gateway + Managed KB共存
- [ ] Chat Agent → Gateway
- [ ] Raw Evidence Citation
- [ ] DynamoDBSaver continuation
- [ ] CloudWatch trace

## 20. Final Principle

> **OKF v0.2をKnowledge Formatとして採用し、Harvest AgentがProject Sourcesを継続的にCompiled Knowledgeへ変換・統合する。S3 VectorsはOKFの発見、Managed KBはRaw Evidence、AgentCore Gatewayは両者への統一アクセスを担当する。**
