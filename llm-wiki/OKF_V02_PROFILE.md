# OKF v0.2 Compliance Profile — Project Knowledge Wiki

> Final: 2026-08-08
>
> Normative base: Open Knowledge Format (OKF) v0.2
>
> Base implementation: `aws-samples/sample-okf-llm-wiki`

## 1. 目的

本Project Knowledge Wikiは、Knowledgeの保存形式として **Open Knowledge Format (OKF) v0.2** を正式採用する。

OKFはRuntime、Vector DB、MCP、RAG、Agent Frameworkを規定しない。したがって、本システムでは次の役割分担とする。

```text
OKF v0.2       = Knowledge Format
S3             = OKF BundleのSource of Truth
S3 Vectors     = OKF Concept Discovery用Semantic Index
Managed KB     = Raw Evidence Retrieval
AgentCore MCP  = Knowledge Access
Harvest Agent  = OKF Producer
Chat Agent     = OKF Consumer
```

## 2. Conformance Rule

本システムでpublishするOKF Bundleは最低限、以下を満たす。

1. `index.md` / `log.md` を除くすべての`.md` Conceptにparse可能なYAML frontmatterを持つ。
2. すべてのConcept frontmatterに非空の`type`を持つ。
3. `index.md` / `log.md` はOKF v0.2のreserved filenameとして扱い、Concept文書には使わない。
4. bundle root `index.md` に `okf_version: "0.2"` を宣言する。
5. Unknown extension keysは許容し、round-trip時に保持する。

## 3. Bundle Structure

```text
wiki/
├─ index.md
├─ log.md
├─ projects/
│  ├─ index.md
│  └─ project-a.md
├─ topics/
├─ decisions/
├─ requirements/
├─ actions/
├─ risks/
├─ issues/
├─ artifacts/
├─ meetings/
└─ references/        # optional
```

Directory構造はProject Knowledgeの都合で自由に設計する。OKFは固定taxonomyを要求しない。

## 4. Root `index.md`

bundle-root `index.md` だけはfrontmatterを許容し、version宣言のみに利用する。

```markdown
---
okf_version: "0.2"
---

# Project Knowledge Wiki

## Projects

* [Project A](projects/project-a.md) - Project Aの現在状態と主要Knowledgeへの入口。

## Knowledge

* [Decisions](decisions/) - 現在および過去の意思決定。
* [Requirements](requirements/) - 要件・制約・受入条件。
* [Issues](issues/) - 発生済み問題。
```

subdirectoryの`index.md`はfrontmatterを持たず、progressive disclosure用の目次として利用する。

## 5. `log.md`

`log.md`はscope単位の更新履歴を記録する。日付はISO 8601 `YYYY-MM-DD`、新しい日付を上に置く。

```markdown
# Directory Update Log

## 2026-08-08
* **Update**: [Gateway採用Decision](/decisions/adopt-agentcore-gateway.md)をactiveへ更新。
* **Creation**: [Gateway認証Issue](/issues/gateway-auth.md)を追加。

## 2026-08-01
* **Creation**: Gateway採用Decisionを作成。
```

## 6. Concept Frontmatter — Canonical Profile

OKF v0.2で必須なのは`type`のみだが、本ProjectではTrust / Provenance / Lifecycleを重視するため、publish対象には次を標準プロファイルとして要求する。

```yaml
---
type: Decision
title: AgentCore GatewayをKnowledge Access Layerとして採用
description: Wiki MCPとManaged KBを既存Gateway経由で利用する。
tags:
  - agentcore
  - knowledge-platform

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

`project_id`、`decision_id`、`decision_state`等はOKF v0.2が許容するproducer-defined extension keysである。

## 7. `status`の厳格な使い分け

OKF標準`status`は次の3値だけを使用する。

```text
draft       = 未レビュー / 不完全
stable      = 消費可能な現行Knowledge（省略時もstable）
deprecated  = 履歴・Link維持のため残すが、現行ではない
```

Project固有のBusiness Lifecycleは別キーへ分離する。

### Decision

```yaml
status: stable
decision_state: active
```

`decision_state`:

```text
proposed
active
superseded
cancelled
```

### Requirement

```yaml
status: stable
requirement_state: approved
```

例:

```text
draft
proposed
approved
changed
retired
```

### Action / Issue / Risk

OKF `status`を業務進捗に流用しない。

```yaml
status: stable
action_state: open
issue_state: investigating
risk_state: monitoring
```

Concept自体が現行ではなくなった場合のみ `status: deprecated` を使う。

## 8. Provenance — `sources`

`source`や独自Citation配列は正本にしない。OKF v0.2の`sources`を使用する。

各entryでは`resource`を必須とする。

```yaml
sources:
  - id: architecture-v3
    resource: /artifacts/system-architecture-v3.md
    title: System Architecture v3
    author: team:architecture
    last_modified: 2026-08-07
```

`id`は本文でclaim単位のattributionを行う場合に必須とする。

```markdown
GatewayをKnowledge Access Layerとして正式採用する。[^meeting-20260808]

[^meeting-20260808]: Architecture Meeting
```

footnote labelと`sources[].id`をjoin keyとして扱う。

## 9. Trust — `generated` / `verified`

### generated

現在のcontentを誰が生成・更新したかを記録する。

```yaml
generated:
  by: project-knowledge-harvest/1.0
  at: 2026-08-08T07:30:00Z
```

`generated.by`は必須。Project profileでは`generated.at`も必須とする。

旧`timestamp`は新規出力では使用しない。

### verified

Source / resourceに対する確認イベントを記録する。

```yaml
verified:
  - by: process:project-knowledge-reviewer
    at: 2026-08-08T07:31:00Z
  - by: human:user123
    at: 2026-08-08T09:00:00Z
```

Actor convention:

```text
<producer>/<version>  Agent / Tool
human:<id>            Human
process:<id>          Automated Process
```

Trust Tierは保存せず、consumerが`verified`から導出する。

```text
verifiedなし        → unverified
machineのみ          → machine-confirmed
human:*を含む        → human-reviewed
```

## 10. Freshness — `stale_after`

Knowledgeの鮮度管理にはOKF標準`stale_after`を使用する。

```yaml
stale_after: 2026-11-08
```

絶対日付`YYYY-MM-DD`とし、`today >= stale_after`でstaleと判定する。

Project固有の`updated_at`は補助的に残してもよいが、Conceptの最終意味変更時刻のCanonical値は`generated.at`とする。

## 11. Links / Backlinks

OKF v0.2のRelationはstandard Markdown linkを使う。

推奨はbundle-relative absolute link。

```markdown
- [Project A](/projects/project-a.md)
- [Gateway Requirement](/requirements/gateway-access.md)
```

Linkそのものはuntyped edge。`depends_on` / `supersedes`等をOKF標準Relation Typeとして扱わない。

Relationの意味は周辺proseで示す。

```markdown
このDecisionは[旧Gateway Decision](/decisions/old-gateway.md)を置き換える。
```

必要ならproducer-defined extensionとして補助fieldを持てるが、Portableな関係の正本はMarkdown linkと本文とする。

## 12. Project Knowledge Types

OKFは固定taxonomyを持たないため、Project固有Typeをそのまま利用する。

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

必要に応じて将来追加可能。

```text
System
Component
Milestone
Change
Reference
Attested Computation
```

Unknown Typeをconsumerが拒否してはならない。

## 13. Knowledge ReconciliationとOKF Lifecycle

Harvestの判定とOKF lifecycleを混同しない。

```text
CREATE
  → 新Concept。review前はstatus:draft、publish後status:stable

UPDATE
  → 同じConceptを更新。generated.at更新。内容変更後はverifiedを再評価

REINFORCE
  → sources追加。必要ならverified追加。Conceptは同一IDを維持

CONFLICT
  → 自動上書きしない。status:draftまたはreview_required extensionでHuman Reviewへ

IGNORE
  → publish変更なし
```

旧Knowledgeを置き換える場合:

```text
旧Concept: status: deprecated
新Concept: status: stable
```

ただし同一DecisionのBusiness state変化だけならConceptを乱造せず、同一stable IDを更新し`decision_state`とhistoryを維持する。

## 14. OKF Producer Rules — Harvest Agent

Harvest Agentはpublish前に次を保証する。

- Concept `.md` はvalid YAML frontmatterを持つ
- `type`は必須
- `status`は`draft|stable|deprecated`のみ
- `sources[].resource`必須
- Source-dependentな重要claimには可能な限りfootnote attribution
- `generated.by` / `generated.at`必須
- Reviewer実行時は`verified`を追記
- `timestamp`を新規生成しない
- Body `# Citations`を正本にしない
- Linkはstandard Markdown link
- bundle root `index.md`に`okf_version: "0.2"`
- `index.md` / `log.md`をConceptとして扱わない
- Unknown extension keysを破壊しない

## 15. Consumer Rules — MCP / Chat Agent

Consumerは次を守る。

- Unknown `type` / extension keyでConceptを拒否しない
- optional trust fieldsが欠けても読み取り可能
- bare mappingの`verified`は1-element listとして扱う
- `status: deprecated`を現行回答の第一候補にしない
- `stale_after`超過を警告・rankingへ反映する
- `verified`からtrust tierを導出する
- Broken LinkをBundle不正として拒否しない
- `sources`をRaw Evidence VerificationへのBridgeとして利用する

## 16. Attested Computation

MVPのProject Knowledge Wikiでは必須としない。

将来、工程分析・KPI・正式計算ロジックをWikiに蓄積する場合は、OKF v0.2の`type: Attested Computation`を利用候補とする。

これにより「計算方法の定義」と「その計算が指定手順で実行されたか」をKnowledgeとして扱える。

## 17. Definition of OKF v0.2 Ready

以下を満たした状態を本Projectの`OKF v0.2 Ready`とする。

- [ ] root `index.md` に `okf_version: "0.2"`
- [ ] Concept文書にvalid YAML frontmatter
- [ ] `type`必須
- [ ] reserved file semantics準拠
- [ ] `sources[].resource`準拠
- [ ] `generated`準拠
- [ ] `verified`準拠
- [ ] `status`をOKF lifecycleとして利用
- [ ] Project lifecycleをextension keysへ分離
- [ ] `stale_after`対応
- [ ] claim attribution footnote対応
- [ ] Markdown link / backlink対応
- [ ] `log.md`更新
- [ ] Consumerがunknown keys/typesを許容
- [ ] v0.1 `timestamp` / body `# Citations`を新規生成しない

## 18. 参考

- OKF v0.2 Specification: `GoogleCloudPlatform/knowledge-catalog/okf/SPEC.md`
- Base Repo: `aws-samples/sample-okf-llm-wiki`
