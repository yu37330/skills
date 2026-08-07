# Project Knowledge Wiki — OKF v0.2準拠 最終版

> 最終更新: 2026-08-08
>
> ベース実装: `aws-samples/sample-okf-llm-wiki`
>
> Knowledge Format: **Open Knowledge Format (OKF) v0.2**

## 1. 結論

本Project Knowledge Wikiは、AWS上に**OKF v0.2準拠のAgent-maintained Knowledge Wiki**を構築する。

議事録は最初のSource Typeであり、Wiki自体は議事録専用ではない。

```text
Meeting / Specification / Design / Report / Issue / Future Connectors
                              │
                              ▼
                  Project Knowledge Harvest
                              │
                  Knowledge Reconciliation
                              │
                              ▼
                    OKF v0.2 Bundle on S3
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
        Link / Backlink                  S3 Vectors
     Structural Navigation            Semantic Discovery
               │                             │
               └──────────────┬──────────────┘
                              ▼
                           Wiki MCP
                              │
                              ▼
                   Existing AgentCore Gateway
                         ┌────┴────┐
                         ▼         ▼
                      Wiki MCP   Managed KB
                                  Raw Evidence
                         └────┬────┘
                              ▼
                          Chat Agent
```

役割分担:

```text
OKF v0.2         = Knowledge Format
S3 OKF Bundle    = Compiled KnowledgeのSource of Truth
Link / Backlink  = 明示的な関係探索
S3 Vectors       = OKF Conceptを意味から発見
Managed KB       = Raw Evidence Retrieval
AgentCore Gateway= Unified Knowledge Access
Harvest Agent    = OKF Producer
Chat Agent       = OKF Consumer / Reasoning
DynamoDBSaver    = Conversation State
```

## 2. OKFを正式採用する理由

OKFはLLM WikiのRuntime製品ではなく、Knowledgeを人間・Agent双方が読み書きできる形で保存するためのportable format。

本プロジェクトでは以下を正式ルールにする。

- ConceptはMarkdown + YAML frontmatter
- `type`は必須
- root `index.md`に`okf_version: "0.2"`
- `index.md`はprogressive disclosure用
- `log.md`は更新履歴
- provenanceは`sources`
- producer情報は`generated`
- verificationは`verified`
- OKF lifecycleは`status: draft|stable|deprecated`
- freshnessは`stale_after`
- Concept間関係はstandard Markdown links
- Project固有fieldはOKF extension keysとして保持

詳細な正本は [OKF_V02_PROFILE.md](./OKF_V02_PROFILE.md)。

## 3. Project Knowledge Model

OKFは固定taxonomyを要求しないため、Project固有Typeを採用する。

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

議事録、仕様書、設計資料等はSourceであり、Knowledge Typeとは分けて考える。

```text
Source
  Meeting minutes
  PDF / DOCX / PPTX
  Specification
  Design Document
  Report

Knowledge
  Decision
  Requirement
  Topic
  Action
  Risk
  Issue
  Artifact
```

## 4. OKF `status`と業務状態を分離

OKF v0.2の`status`をDecisionやActionの業務状態に流用しない。

```yaml
status: stable
decision_state: active
```

OKF lifecycle:

```text
draft
stable
deprecated
```

Project lifecycleはextension key:

```text
decision_state: proposed | active | superseded | cancelled
action_state: open | in_progress | done | cancelled
issue_state: open | investigating | resolved | closed
risk_state: identified | monitoring | mitigated | closed
```

## 5. Canonical Concept例

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

本文で重要claimをSourceへ結びつける場合は`sources[].id`と同じfootnote labelを使う。

```markdown
GatewayをKnowledge Access Layerとして正式採用する。[^meeting-20260808]

[^meeting-20260808]: Architecture Meeting
```

## 6. Harvestの本質

最大の改修対象はHarvest Agent。

元Repo:

```text
Glue / Athena / Redshift
        ↓
Data Understanding
        ↓
Dataset / Table Wiki
```

To-Be:

```text
Project Sources
      ↓
Source Adapter
      ↓
Normalized Evidence
      ↓
Knowledge Candidate Extraction
      ↓
Existing Wiki Search
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
Review / Guard
      ↓
Publish
```

単なる「議事録→Markdown」ではなく、Sourceをまたいで同一Knowledgeを継続管理する。

詳細は [HARVEST_MIGRATION.md](./HARVEST_MIGRATION.md)。

## 7. S3 Vectorsは維持

S3 VectorsはRaw Document RAGではなく、OKF ConceptのSemantic Discoveryに利用する。

```text
Question
   ↓
Titan V2
   ↓
S3 Vectors
   ↓
Candidate Concept IDs
   ↓
read_page
   ↓
S3 OKF Markdown
```

したがってMVPではDynamoDB Vector Searchへ移行しない。

## 8. Managed KBとの役割分担

```text
OKF Wiki   = 整理された現在の理解
Managed KB = 正式な原文 / Evidence
```

Chat Agentは既存AgentCore Gateway経由で両方を利用する。

```text
Chat Agent
    ↓ MCP
Existing AgentCore Gateway
    ├─ Wiki MCP Target
    └─ Existing Managed KB Target
```

## 9. LLM Wiki Level

### Level 1 — OKF Structured Wiki
OKF v0.2 Markdown + YAML + provenance。

### Level 2 — Navigable Wiki
Link / Backlink + Wiki Tools + Graph View。

### Level 3 — Semantic + Evidence
S3 Vectors + Managed KB + Citation。**MVP到達点。**

### Level 4 — Self Improving Knowledge
Evaluation / Feedback / Conflict Detection / Re-Harvest。

### Level 5 — Graph / Semantic Model
Thin Ontology / Typed Relations / GraphRAG。必要な場合のみ。

## 10. 今回追加しないもの

- DynamoDB Vector migration
- AgentCore Long-term Memory
- Neptune
- GraphRAG
- Full Knowledge Graph
- Heavy Ontology
- 新規Custom Vector DB
- 新規Custom RAG Platform

## 11. 最終ドキュメント

- [FINAL_REPORT.md](./FINAL_REPORT.md) — 最終アーキテクチャ
- [REQUIREMENTS.md](./REQUIREMENTS.md) — 改修要件
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — 実装計画
- [HARVEST_MIGRATION.md](./HARVEST_MIGRATION.md) — Harvest本丸の移行仕様
- [OKF_V02_PROFILE.md](./OKF_V02_PROFILE.md) — **OKF v0.2準拠ルールの正本**

## 12. 参考

- OKF v0.2 Specification: `GoogleCloudPlatform/knowledge-catalog/okf/SPEC.md`
- Base Repo: `aws-samples/sample-okf-llm-wiki`

> **AWS上にOKF v0.2準拠のProject Knowledge Wikiを構築し、Managed KBをRaw Evidence Layer、OKFをCompiled Knowledge Layer、AgentCore GatewayをKnowledge Access Layerとして利用する。**
