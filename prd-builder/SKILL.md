---
name: prd-builder
description: >
  承認済みDirection Spec、顧客議事録、既存資料から、根拠追跡可能なPRDを生成・検証する。
  Grill-me Directionの後段で使用し、方向性の再探索ではなく、決定内容の構造化、
  不足確認、品質評価、Executable Specへの引き渡しを担当する。
version: 2.0.0
---

# PRD Builder

## 目的

このSkillは、Grill-me Directionなどで合意された方向性を、レビュー可能かつ後工程で利用可能なProduct Requirements Documentへ変換する。

このSkillは、ゼロから製品の方向性を探索しない。入力されたDirection Specを尊重し、次を実行する。

1. Direction SpecのSchema、承認状態、整合性を確認する
2. 議事録・既存資料から不足する根拠を補完する
3. Direction Specの決定、根拠、制約、未決事項を欠落なくPRDへ移送する
4. `prd.json`をSingle Source of TruthとしてPRDを生成する
5. 曖昧性、矛盾、TBD、測定不能KPI、根拠不整合を検出する
6. 要求と根拠のトレーサビリティを残す
7. Quality Gate通過後にExecutable Spec Builderへ引き渡す

## 責務境界

```text
Grill-me Direction
= 何を作るべきかを探索し、方向性を決める

PRD Builder
= 決めた方向性を製品要求へ構造化し、品質を検査する

Executable Spec Builder
= 製品要求を実装・検証可能な条件へ変換する

Superpowers
= 設計、計画、TDD、実装、レビューを実行する
```

PRD Builderは、方向性を根拠なく変更しない。方向性の変更が必要になった場合は、PRD内で変更せず、Direction Specの再承認へ戻す。

## このSkillを使う条件

次のすべてを満たすときに使う。

- `direction-spec.json`または同等のDirection Specが存在する
- 解決する課題、対象ユーザー、採用方向、対象範囲が定義されている
- `approval_status`が`approved`である
- Blockingな未決事項が残っていない

次の場合は、先にGrill-me Directionへ戻す。

- 解決すべき課題自体が未定
- 複数案のどれを採用するか決まっていない
- 対象ユーザーや提供価値が大きく揺れている
- 顧客または責任者の承認がない
- Blockingな未決事項が残っている

## 入力

### 必須入力

- Direction Spec
- プロジェクト名
- PRD作成対象の製品または機能

### 推奨入力

- 顧客議事録
- 過去の決定事項
- 既存システム資料
- 業務フロー
- セキュリティ、法規、社内規程
- 類似案件
- 既存PRD
- KB検索結果
- AgentCore Memory

## 出力

```text
prd-output/
├─ prd.json
├─ prd.md
├─ prd-review-report.md
├─ prd-review-report.json
├─ open-questions.md
├─ decision-traceability.md
└─ source-map.json
```

`prd.json`を唯一の正本とする。`prd.md`、レビュー報告、未決事項、トレーサビリティ表は`prd.json`から生成する。MarkdownとJSONを別々に手修正してはならない。

## 実行手順

### Step 1: 入力資料を確認する

Direction Specと関連資料を読み、次を抽出する。

- 解決する課題
- 対象ユーザー
- 期待する成果
- 採用した方向性
- 採用しなかった方向性
- 判断根拠
- スコープ
- 対象外
- 制約
- 前提
- リスク
- 未決事項
- 承認状態
- 情報源

Direction Specに書かれていない内容を、推測で確定事項にしてはいけない。

### Step 2: Direction Specを検証する

次を実行する。

```bash
python scripts/validate_direction_spec.py <direction-spec.json>
```

次のいずれかに該当する場合はPRD生成を停止する。

- Schema違反
- `approval_status`が`approved`ではない
- Blockingな未決事項が存在する
- 採用方向とスコープが矛盾する
- スコープと対象外が重複する
- 重要な決定に根拠資料がない

不足確認が必要な場合、質問は一度に一問とし、推奨回答を添える。資料から確認できる事項は質問せず、自分で確認する。

### Step 3: PRD JSONの骨格を作る

次を実行して、Direction Specの情報をPRDへ欠落なく移送する。

```bash
python scripts/init_prd.py <direction-spec.json> <prd.json>
```

最低限、次をそのまま保持する。

- `selected_direction`
- `decision_rationale`
- `desired_outcomes`
- `scope`
- `out_of_scope`
- `constraints`
- `assumptions`
- `risks`
- `open_questions`
- `sources`
- 承認済み決定を表す`decision_log`

### Step 4: 製品要求を構造化する

`templates/prd.schema.json`と`references/prd-writing-guide.md`に従い、`prd.json`を完成させる。

原則は次のとおり。

- 「何を、誰に、なぜ」を中心に書く
- 実装方法を過度に固定しない
- 要求は検証可能な文章にする
- Must / Should / Could / Won'tを区別する
- 対象外を必ず明記する
- 成功指標には基準値、目標値、測定方法、測定頻度、責任者を持たせる
- 根拠不明な要求は`hypothesis`または`unconfirmed`とする
- `confirmed`な要求は承認済み根拠を持たせる
- AI機能では、誤回答、根拠提示、Human-in-the-loop、評価方法を明記する

### Step 5: トレーサビリティを作る

各機能要求・非機能要求について、`traceability`に次を残す。

- `requirement_id`
- `direction_refs`
- `source_ids`
- `evidence`
- `confidence`

次のルールを守る。

- `source_ids`は`PRD.sources`に実在するIDだけを使う
- Direction Specを渡した場合、`direction_refs`は実在する項目を指す
- `confirmed`なMust要求を`inferred`情報だけで確定しない
- 根拠発言または判断内容を`evidence`へ記録する
- 顧客の正式決定、参考資料、AI推論を区別する

### Step 6: Quality Gateを実行する

```bash
python scripts/run_quality_gate.py \
  <prd.json> \
  --direction-spec <direction-spec.json> \
  --report <prd-review-report.md> \
  --report-json <prd-review-report.json>
```

100点モデルは次のとおり。

- 問題と背景の明確性: 10
- 対象ユーザーの明確性: 10
- 提供価値の明確性: 10
- スコープの明確性: 10
- 対象外の明確性: 5
- 成功指標の測定可能性: 10
- 機能要求の明確性: 10
- 非機能要求の明確性: 10
- 制約・依存関係: 5
- リスクと前提: 5
- 意思決定の根拠: 5
- 出典トレーサビリティ: 10

次は点数に関係なく重大問題とする。

- Schema違反
- Blockingな未決事項
- 主要要求のTBD、TODO、未定、要確認
- Must要求の根拠IDが存在しない
- 確定要求が推論情報だけに依存している
- 重要KPIが測定不能
- スコープと対象外が重複
- 顧客合意済み方向とPRDが矛盾
- Direction Specが未承認

### Step 7: Markdownと補助成果物を生成する

```bash
python scripts/render_prd.py <prd.json> <prd.md>
```

必要に応じて、`open_questions`、`traceability`、`sources`から補助成果物を生成する。生成物は`prd.json`から再生成可能な状態にする。

### Step 8: 後段へ引き渡す

Quality Gateが合格した場合のみ、次へ渡す。

- user-stories
- acceptance-criteria
- edge-cases
- business-rules
- data-contracts
- non-functional-requirements
- executable-spec-builder
- architecture / Superpowers brainstorming

80〜89点の条件付き合格は、人間の承認なしに自動で後段へ進めない。

## 出力時の最終確認

- PRDの目的が一文で説明できる
- 対象ユーザーと利用状況が明確
- 課題と提供価値が対応する
- Direction Specの方向性と判断根拠が残っている
- スコープと対象外が重複していない
- 主要要求に一意なIDがある
- KPIが測定可能
- 制約、依存関係、リスク、前提が分離されている
- BlockingとNon-blockingの未決事項が分離されている
- 各要求の根拠が実在する
- AI推論と顧客決定が区別されている
- 後段へ渡すべき未展開項目が明確

## 禁止事項

- Direction Specで決めた方向性を、根拠なく変更しない
- 顧客が言っていない要求を`confirmed`として追加しない
- 実装手段をPRDの中心にしない
- MarkdownとJSONを別々の正本として管理しない
- 存在しない`source_id`を記載しない
- AIの推論を顧客の決定として扱わない
- 曖昧な要求をQuality Gateで見逃さない
- KPIなしで「改善する」「高品質にする」と書かない
- 条件付き合格を無承認で後段へ流さない
