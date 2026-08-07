# Project Knowledge Wiki 実装計画 — OKF v0.2準拠

> Final: 2026-08-08
>
> Base Repo: `aws-samples/sample-okf-llm-wiki`
>
> Knowledge Format: **Open Knowledge Format (OKF) v0.2**

## 1. 実装方針

元Repoの完成度が高い部分を壊さず、Data Wiki固有部分だけをProject Knowledge向けへ差し替える。

```text
Keep
  S3 Bundle / versioning
  Link / Backlink
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
  OKF frontmatter / lifecycle conventions
  UI terminology
  Chat knowledge access
  Authentication integration

Integrate
  Existing AgentCore Gateway
  Existing Managed KB
```

`OKF_V02_PROFILE.md`をKnowledge Format実装の正本とする。

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
Project Sources
      ↓
Source Adapter
      ↓
Normalized Evidence
      ↓
Knowledge Extraction
      ↓
Existing OKF Search
      ↓
Knowledge Reconciliation
CREATE / UPDATE / REINFORCE / CONFLICT / IGNORE
      ↓
OKF v0.2 Authoring
      ↓
Review / Guard
      ↓
index.md / log.md update
      ↓
S3 Publish
      ↓
EventBridge → SQS → Reindex Lambda → Titan V2 → S3 Vectors
```

## 3. Phase 0 — Baseline固定

目的: 元Repoをそのまま動作させ、変更前の基準を作る。

- upstream commit固定
- LICENSE確認
- Harvest Runtime確認
- Consumption MCP Runtime確認
- Chat Runtime確認
- S3 Bundle確認
- S3 Vectors `semantic_search`確認
- Link / Backlink確認
- DynamoDBSaver確認
- CloudWatch trace確認

成果物:

```text
baseline commit SHA
baseline deployment notes
baseline smoke test
```

## 4. Phase 1 — OKF v0.2 Compliance Layer

最初にKnowledge Formatの契約を固定する。

対象:

```text
services/okf_core
services/harvest guard / skill
```

実装:

- Concept YAML frontmatter validation
- non-empty `type`必須
- `index.md` / `log.md` reserved filename handling
- root `index.md`の`okf_version: "0.2"`
- `sources[].resource` validation
- `generated.by` / `generated.at`
- `verified` list / bare mapping compatibility
- actor convention
- `status: draft|stable|deprecated`
- `stale_after: YYYY-MM-DD`
- unknown extension keys preservation
- v0.1 `timestamp`を新規生成しない
- body `# Citations`をCanonicalにしない

成果物:

```text
OKF validator
OKF fixture set
canonical Project Knowledge examples
```

## 5. Phase 2 — Project Knowledge Schema

Project固有Typeを定義する。

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

Project固有fieldはOKF extensionとして設計する。

例:

```yaml
status: stable
project_id: project-a
decision_id: gateway-adoption
decision_state: active
```

重要: OKF `status`をBusiness stateとして使わない。

定義:

- stable ID rule
- business lifecycle rule
- path / naming rule
- Markdown Link rule
- source provenance rule
- stale policy

推奨構成:

```text
wiki/
  index.md
  log.md
  projects/
  topics/
  decisions/
  requirements/
  actions/
  risks/
  issues/
  artifacts/
  meetings/
  references/
```

## 6. Phase 3 — Source Adapter Layer

対象: `services/harvest`

Data Source固有処理をKnowledge Logicから分離する。

```text
SourceAdapter
  ├─ MeetingAdapter
  ├─ DocumentAdapter
  └─ FutureAdapter
```

MVP Input:

- Markdown / Text
- PDF
- DOCX
- PPTX

共通Normalized Evidence:

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

`source_uri`は最終的にOKF`sources[].resource`へ変換可能であること。

## 7. Phase 4 — Project Knowledge Harvest Agent

**最重要Phase。**

対象: `services/harvest`

```text
Normalized Evidence
  ↓
Source Analysis
  ↓
Knowledge Candidate Extraction
  ↓
Search Existing OKF
  ↓
Knowledge Reconciliation
  ↓
OKF Authoring
  ↓
Link / Index / Log update
  ↓
Reviewer
  ↓
OKF Guard
  ↓
Publish
```

既存から極力残す:

- deepagents supervisor
- subagents
- reviewer
- FilesystemBackend
- OKFGuardMiddleware
- LinkGraph
- tracing

詳細は`HARVEST_MIGRATION.md`。

## 8. Phase 5 — Knowledge Reconciler

入力:

```text
Knowledge Candidate
Existing OKF Candidates
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
- normalized key / title
- project
- type
- semantic similarity
- links
- `sources`
- business lifecycle
- OKF lifecycle

### CREATE

新Concept。生成中は`status: draft`、review成功後`stable`。

### UPDATE

stable IDを維持し本文・extension fieldsを変更。`generated.at`更新。

内容が意味的に変わった場合、古い`verified`を現内容の確認結果として誤利用しない。

### REINFORCE

同一Conceptへ`sources`追加。必要ならverification event追加。

### CONFLICT

自動上書きしない。`review_required: true`等のextensionを付与してReviewへ。

### IGNORE

変更なし。

## 9. Phase 6 — OKF Provenance / Trust / Freshness

Authoring pipelineへ以下を組み込む。

### Provenance

```yaml
sources:
  - id: source-key
    resource: /path-or-uri
```

重要claimはfootnote labelで`sources[].id`へ結ぶ。

### Trust

```yaml
generated:
  by: project-knowledge-harvest/1.0
  at: ...
verified:
  - by: process:project-knowledge-reviewer
    at: ...
```

### Freshness

```yaml
stale_after: YYYY-MM-DD
```

## 10. Phase 7 — Reviewer / Grounding変更

元Repo:

```text
Glue metadata
run_sql
sample_rows
```

To-Be:

```text
source text
source metadata
existing OKF Wiki
Managed KB retrieval when needed
```

Reviewer checks:

- Sourceにない事実を作っていない
- Duplicateを作っていない
- Existing Knowledgeを誤上書きしていない
- Conflictを隠していない
- `type`がある
- `sources[].resource`がある
- `generated`がある
- `status`がOKF値だけ
- Business stateがextensionへ分離
- Linkが妥当
- claim attributionが妥当
- `index.md` / `log.md`が整合

## 11. Phase 8 — `index.md` / `log.md`

Harvest publish時に関連scopeを更新する。

### Root index

```yaml
---
okf_version: "0.2"
---
```

root以外の`index.md`はfrontmatterなし。

### Index body

Concept / subdirectoryのTitle + descriptionを一覧化し、progressive disclosureに利用する。

### Log

```markdown
# Directory Update Log

## 2026-08-08
* **Update**: ...
* **Creation**: ...
```

newest first。

## 12. Phase 9 — Source / Control API変更

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

## 13. Phase 10 — S3 Vectors維持確認

対象:

```text
services/reindex
services/okf_core/src/okf_core/embedding.py
services/okf_aws/src/okf_aws/embeddings.py
```

原則維持:

- Titan Text Embeddings V2
- 512 dimensions
- cosine
- 1 Concept = 1 Vector
- deterministic vector key
- EventBridge / SQS / Lambda
- sequencer dedup
- retry / DLQ

`index.md` / `log.md`をVector Conceptとして扱わない。

互換性優先で既存`dataset`をProject相当として利用する案を第一候補とする。

## 14. Phase 11 — Consumption MCP OKF対応

対象: `services/consumption_mcp`

基本Toolは残す。

```text
list_domains
list_directory
read_page
glob
grep
get_backlinks
semantic_search
```

追加対応:

- Project terminology
- unknown Type / extension tolerance
- `verified` bare mapping compatibility
- `status: deprecated` awareness
- `stale_after` awareness
- trust tier derivation
- `sources`をEvidence Bridgeとして返却可能にする

## 15. Phase 12 — Existing AgentCore Gateway統合

新規Gatewayは作らない。

```text
Existing AgentCore Gateway
   ├─ Existing Managed KB Target
   └─ Wiki MCP Target  ← ADD
```

確認:

- Tool discovery
- IAM / auth
- namespace
- trace

## 16. Phase 13 — Chat AgentをGatewayへ変更

対象: `services/chat`

Current:

```text
Chat Agent
  ↓
ConsumptionTools direct import
```

To-Be:

```text
Chat Agent
  ↓ MCP client
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
- trust / stale / deprecated handling
- Gateway error handling

## 17. Phase 14 — Query Routing

```text
Use Wiki when:
- current project state
- decisions / requirements
- actions / issues / risks
- topic summary
- relationships

Use Managed KB when:
- exact wording
- evidence
- citation
- exact number
- raw detail

Important factual answer:
1. understand with Wiki
2. inspect OKF provenance/trust/freshness
3. verify with Managed KB
4. answer with source citation
```

## 18. Phase 15 — UI

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

段階導入:

- trust badge
- stale warning
- deprecated indication
- source provenance

## 19. Phase 16 — E2E Evaluation

代表Source Set:

```text
Meeting A: Gatewayを検討
Meeting B: Gatewayを採用
Architecture Spec: Gateway経由でKBとWiki MCPを利用
Issue: Gateway認証エラー
Meeting C: Gateway案を変更/撤回
```

評価:

- OKF conformance
- extraction accuracy
- duplicate rate
- reconciliation accuracy
- business lifecycle correctness
- OKF lifecycle correctness
- provenance completeness
- verification correctness
- stale behavior
- link correctness
- semantic search recall
- evidence retrieval
- citation correctness
- answer faithfulness
- latency / cost

## 20. Component Change Map

| Component | 方針 | 改修量 |
|---|---|---:|
| `services/harvest` | Project Knowledge / OKF v0.2 Producer化 | **大** |
| `services/okf_core` | OKF v0.2 validation + extension schema | 中〜大 |
| `services/control_api` | project/source化 | 中 |
| `services/incremental` | source update化 | 中 |
| `services/reindex` | 原則維持 | 小 |
| `services/consumption_mcp` | OKF consumer + Gateway | 中 |
| `services/chat` | Gateway + trust/citation | 中 |
| `infra/durable` | 基本維持 / Cognito整理 | 小〜中 |
| `infra/compute` | Existing Gateway integration | 中 |
| `ui` | Project Knowledge UI | 中 |

## 21. MVP Day Plan

### Day 1
- Baseline
- OKF v0.2 validator
- canonical fixtures

### Day 2
- Project Knowledge schema
- Source Adapter contract
- Meeting / Document Adapter

### Day 3
- Candidate extraction
- Knowledge Reconciler
- lifecycle split

### Day 4
- provenance / trust / freshness
- Link / index / log
- Reviewer / Guard

### Day 5
- S3 Vectors確認
- Consumption MCP OKF対応
- Existing GatewayへWiki MCP Target

### Day 6
- Chat Agent Gateway接続
- Wiki + Managed KB routing
- Citation

### Day 7〜8
- UI
- duplicate / conflict改善
- trace / error handling

### Day 9〜10
- OKF compliance test
- E2E evaluation
- hardening / demo

## 22. Estimate

```text
PoC                    3〜5営業日
Internal MVP           5〜10営業日
Production hardening   3〜6週間
```

最大の不確実性はInfrastructureではなく、**Knowledge Reconciliation品質とOKF lifecycle / provenanceの正しい維持**。

## 23. Do Not Optimize Early

- DynamoDB Vector migration
- AgentCore Memory
- Neptune
- GraphRAG
- Heavy Ontology
- many source connectors
- automatic conflict resolution
- complex approval workflow

## 24. Recommended Order

```text
1. Baseline
2. OKF v0.2 Compliance Layer
3. Project Knowledge Schema
4. Source Adapter
5. Harvest + Reconciler
6. Provenance / Trust / Freshness / Index / Log
7. Wiki Retrieval回帰確認
8. GatewayへWiki MCP追加
9. Chat Agent Gateway接続
10. Managed KB Hybrid Answer
11. UI / Evaluation
```

## 25. Final Principle

> **Harvestの知能をData理解からProject Knowledge Compilation / Reconciliationへ置き換え、その出力契約をOKF v0.2へ固定する。既存S3 VectorsはOKF発見、Managed KBはRaw Evidence、Existing GatewayはUnified Knowledge Accessとして利用する。**
