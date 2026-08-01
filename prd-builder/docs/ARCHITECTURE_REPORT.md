# Grill-me DirectionとPRD Builderを接続したAI駆動開発プロセス構想

## 1. 背景

AIコーディングエージェントにより、要件から設計・実装・テストまでをAIで支援できるようになった。一方、顧客との打ち合わせで語られる要望は曖昧で、そのままコードへ変換すると「実装は速いが、作る方向が間違っている」という問題が起きる。

たとえば「生成AIで議事録を効率化したい」という発言の本質は、作成時間ではなく、決定事項の抜け漏れ、担当者・期限の不明確さ、過去の判断経緯を検索できないことかもしれない。そのため、次の段階を分離する。

```text
顧客の発言や資料から方向性を探索する
        ↓
採用する方向性を製品要求として定義する
        ↓
製品要求を実装・検証可能な仕様へ変換する
        ↓
設計・実装・テストを実行する
```

本構想では、各段階を次のコンポーネントで担う。

```text
Grill-me Direction
        ↓
Direction Spec
        ↓
PRD Builder
        ↓
PRD
        ↓
Executable Spec
        ↓
Superpowers
```

## 2. 全体コンセプト

顧客との打ち合わせ、議事録、既存資料、Knowledge Base、過去の意思決定を使い、質問によって方向性を掘り下げ、その結果をAI駆動開発へ接続する。全体を4層に分ける。

### 2.1 Discovery / Direction層

```text
顧客との打ち合わせ
議事録・既存資料・KB・Memory
        ↓
Grill-me Direction
        ↓
Direction Spec
```

### 2.2 Product Definition層

```text
Direction Spec
        ↓
PRD Builder
        ↓
PRD Quality Gate
        ↓
PRD
```

### 2.3 Software Definition層

```text
PRD
        ↓
Spec Expansion
        ↓
Executable Spec
        ↓
基本設計・アーキテクチャ
        ↓
実装計画
```

### 2.4 Execution層

```text
タスク分解
        ↓
TDD
        ↓
コード生成
        ↓
レビュー・検証
        ↓
Spec・PRD・Directionへのフィードバック
```

PRDは、人間・顧客の合意と開発AIの実行をつなぐ重要な中間成果物として扱う。

## 3. Grill-me Directionの役割

Grill-me Directionは議事録生成Skillではなく、顧客が言語化できていない課題を発見し、選択肢を比較し、進む方向を決める意思決定支援Skillである。

主な責務は次のとおり。

- 顧客の要望と本質的な課題を分離する
- 手段から目的を逆算する
- 過去の議事録や判断との矛盾を検出する
- 複数の方向性を提示する
- 利点、欠点、リスクを比較する
- 推奨方向を提示する
- 対象範囲と対象外を決める
- 判断根拠と未決事項を残す

例として「議事録作成を自動化したい」という要望では、次の意思決定ツリーをたどる。

```text
顧客の要望
「議事録作成を自動化したい」
        ↓
本当の問題は何か
├─ 作成時間が長い
├─ 決定事項が抜ける
├─ 担当者と期限が曖昧
└─ 過去の会議を検索できない
        ↓
最も避けたい損失は何か
├─ 工数増加
├─ 対応漏れ
├─ 認識齟齬
└─ 監査証跡の不足
        ↓
方向性候補
├─ 議事録全文の自動生成
├─ 決定事項とActionの抽出
├─ 会議ナレッジ検索
└─ 要件・設計への自動連携
        ↓
採用方向
「全文生成より、決定事項・担当者・期限の確実な抽出を優先する」
```

この結果をDirection Specとして保存する。

## 4. Direction Spec

Direction Specは、Grill-me DirectionからPRD Builderへ渡す契約である。最終結論だけでなく、不採用案とその理由も保存し、条件変更時に判断を再評価できるようにする。

```text
direction-spec/
├─ problem.md
├─ target-users.md
├─ desired-outcomes.md
├─ selected-direction.md
├─ rejected-options.md
├─ decision-rationale.md
├─ scope.md
├─ out-of-scope.md
├─ constraints.md
├─ assumptions.md
├─ risks.md
├─ open-questions.md
└─ source-traceability.md
```

## 5. PRD Builderが必要な理由

一般的なPRD Skillは、ユーザーから直接アイデアを聞き、Discovery質問を行ってPRDを作る。前段にGrill-me Directionがある構成でそのまま利用すると、質問の重複、決定済み方向の再検討、判断根拠の欠落、合意事項の埋没、トレーサビリティの喪失が起きる。

したがって、独自PRD Builderは次の流れにする。

```text
Direction Spec
        ↓
整合性検査
        ↓
不足項目だけ質問
        ↓
PRD
```

## 6. PRD Builderの責務

```text
Grill-me Direction
= 何を作るべきかを探索し、方向性を決める

PRD Builder
= 決めた方向性を製品要求へ変換する

Executable Spec Builder
= 製品要求を実装・検証可能な条件へ変換する

Superpowers
= 設計、計画、TDD、実装、レビューを行う
```

### 6.1 Direction Specの検証

- 必須項目の存在
- 決定事項と根拠の対応
- スコープと対象外の矛盾
- 未決事項がPRD作成を妨げるか
- 顧客承認が必要な項目の残存

### 6.2 関連情報の補完

- 顧客議事録の具体的発言
- KBの業務制約・既存システム情報
- AgentCore Memoryなどの過去の意思決定
- 類似案件のPRD・設計資料
- 法規、社内規程、セキュリティ条件

### 6.3 PRDへの構造化

- プロダクトの目的、解決課題、対象ユーザー、提供価値
- ユースケース、スコープ、対象外
- 機能要求、非機能要求、データ要求
- KPI・成功指標
- 制約、依存関係、リスク、前提、未決事項

### 6.4 品質検査

- 曖昧な表現
- 測定不能なKPI
- TBD・TODO・未定項目
- 要求間の矛盾
- 根拠のない要求
- 対象ユーザー不明の要求
- 受入条件へ展開できない要求

## 7. 既存Skillから取り込む要素

### 7.1 Awesome Copilot系PRD Skill

PRDの基本構造、Discovery・分析・スコープ整理・PRD生成の処理構成、自己完結フォルダ、テンプレート・スクリプト同梱の考え方を採用する。ただしDiscoveryはGrill-me Directionへ分離する。

### 7.2 Requirements Clarity

100点満点のPRD品質スコア、不足項目の自動検出、曖昧性検査、対象を絞った追加質問、一定スコア未満では進ませない品質ゲートを取り込む。

### 7.3 product-on-purposeのPM Skill群

PRD Builderにすべてを持たせず、後段を分離する。

```text
PRD Builder
        ↓
PRD
        ↓
Spec Expansion Skills
├─ user-stories
├─ acceptance-criteria
├─ edge-cases
├─ business-rules
├─ data-contracts
└─ non-functional-requirements
        ↓
Executable Spec
```

### 7.4 phurynのPM Skill群

「なぜ今取り組むのか」、顧客セグメント、価値提案、成功指標、事業目標との関係、段階導入を参考にし、技術要件だけでなく顧客価値をPRDに残す。

### 7.5 Superpowers

SuperpowersはPRD作成より、PRDまたはExecutable Specを受け取った後の設計・実装工程に適する。brainstorming、writing-plans、TDD、デバッグ、レビューを担当する。

## 8. PRD Builder Skillの推奨構成

```text
prd-builder/
├─ SKILL.md
├─ references/
│  ├─ direction-spec-contract.md
│  ├─ prd-writing-guide.md
│  ├─ prd-quality-model.md
│  ├─ requirement-language-rules.md
│  ├─ scope-definition-rules.md
│  ├─ success-metric-guide.md
│  ├─ traceability-rules.md
│  └─ examples/
├─ templates/
│  ├─ prd-template.md
│  ├─ prd.schema.json
│  ├─ review-report-template.md
│  ├─ open-questions-template.md
│  └─ traceability-template.md
├─ scripts/
│  ├─ validate_direction_spec.py
│  ├─ validate_prd.py
│  ├─ score_prd.py
│  ├─ detect_ambiguity.py
│  ├─ detect_tbd.py
│  └─ check_traceability.py
└─ tests/
   ├─ scenarios/
   └─ expected/
```

Skill作成もプロセス文書に対するTDDとして扱い、正常系・異常系シナリオで失敗を確認しながら改善する。

## 9. 入力

### 必須入力

- Direction Spec
- 顧客との打ち合わせ議事録
- プロジェクト基本情報

### 任意入力

- 過去の議事録、既存PRD、既存システム資料、業務フロー
- 社内規程、セキュリティ要件、法規制
- KB検索結果、AgentCore Memory、類似案件

情報源には信頼度と状態を付与する。

```yaml
source_id: meeting-2026-07-31
source_type: meeting_transcript
status: approved
authority: customer
confidence: high
meeting_date: 2026-07-31
```

顧客の正式決定、担当者発言、AI推論、参考情報を区別する。

## 10. 出力

```text
prd-output/
├─ prd.md
├─ prd.json
├─ prd-review-report.md
├─ open-questions.md
├─ decision-traceability.md
└─ source-map.json
```

- `prd.md`: 人間がレビューする正式PRD
- `prd.json`: 後段エージェント用の構造化データ
- `prd-review-report.md`: 品質スコア、曖昧性、不足、矛盾、警告
- `open-questions.md`: 確定に必要な追加確認
- `decision-traceability.md`: 要求と顧客発言・Direction Spec・資料・過去決定の対応

## 11. 推奨PRD構造

1. Executive Summary
2. Background
3. Problem Statement
4. Product Goal
5. Target Users
6. User Needs
7. Value Proposition
8. Desired Outcomes
9. Success Metrics
10. Scope
11. Out of Scope
12. User Scenarios
13. Functional Requirements
14. Non-functional Requirements
15. Data Requirements
16. Security and Compliance
17. Dependencies
18. Constraints
19. Assumptions
20. Risks
21. Release Strategy
22. Open Questions
23. Decision Log
24. Source Traceability

PRDは「何を、誰のために、なぜ作るか」を定義する。API詳細、クラス構造、関数単位の設計はExecutable Specまたは基本設計へ分離する。

## 12. PRD Quality Gate

100点満点の評価モデルを使用する。

| 評価項目 | 配点 |
|---|---:|
| 問題と背景の明確性 | 10 |
| 対象ユーザーの明確性 | 10 |
| 提供価値の明確性 | 10 |
| スコープの明確性 | 10 |
| 対象外の明確性 | 5 |
| 成功指標の測定可能性 | 10 |
| 機能要求の明確性 | 10 |
| 非機能要求の明確性 | 10 |
| 制約・依存関係 | 5 |
| リスクと前提 | 5 |
| 意思決定の根拠 | 5 |
| 出典トレーサビリティ | 10 |
| **合計** | **100** |

判定基準は次のとおり。

- 90点以上: 後工程へ進行可能
- 80〜89点: 警告付きでレビューへ進行
- 79点以下: 不足項目を確認して再生成
- 重大な矛盾: スコアに関係なく停止
- 重要項目にTBD・TODO・未定: 顧客または責任者の確認が必要

## 13. Executable Specとの境界

```text
PRD
人間・顧客・プロダクト中心
「何を、誰のために、なぜ作るか」

Executable Spec
開発者・AIエージェント中心
「どの条件を満たせば完成なのか」
```

PRD例:

> 会議終了後5分以内に、決定事項、担当者、期限を確認できるようにする。

Executable Spec例:

```yaml
input:
  - transcript
  - speaker_metadata
  - meeting_datetime
output:
  decisions:
    - description
    - owner
    - due_date
    - evidence_text
acceptance_criteria:
  - 担当者が明示されていない場合は未確定とする
  - 推測した担当者を確定値として出力しない
  - 各決定事項に根拠発言を付与する
  - 指定JSON Schemaへ準拠する
  - 同一内容の決定事項を重複排除する
```

この変換はSpec ExpansionまたはExecutable Spec Builderが担当する。

## 14. Superpowersとの接続

```text
PRDまたはExecutable Spec
        ↓
brainstorming
設計上の不明点と選択肢を整理
        ↓
基本設計・アーキテクチャ
        ↓
writing-plans
実装タスクへ分解
        ↓
TDD
        ↓
コード生成
        ↓
レビュー・検証
```

役割分担は次のとおり。

- 顧客・事業要求の品質: Grill-me Direction + PRD Builder
- 実装可能な仕様の品質: Executable Spec Builder
- 設計・計画・実装の規律: Superpowers

## 15. 推奨最終アーキテクチャ

```text
顧客との打ち合わせ・議事録・資料・KB・Memory
        ↓
┌──────────────────────────┐
│ Grill-me Direction       │
│ 課題探索・比較・意思決定 │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Direction Spec           │
│ 決定・根拠・対象外・制約 │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ PRD Builder              │
│ 製品要求への構造化       │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ PRD Quality Gate         │
│ 曖昧性・不足・矛盾検査   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ PRD                      │
│ 何を・誰に・なぜ作るか   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Spec Expansion           │
│ Story・受入条件・例外    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Executable Spec          │
│ 実装・検証可能な仕様     │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Superpowers              │
│ 設計・計画・TDD・実装    │
└────────────┬─────────────┘
             ↓
実行・評価・レビュー
             ↓
Direction・PRD・Specへ反映
```

## 16. 実装ステップ

### Phase 1: ファイルベースのプロトタイプ

```text
meeting.md
        ↓
Grill-me Direction
        ↓
direction-spec.md
        ↓
PRD Builder
        ↓
prd.md
        ↓
PRD Review
```

CodexまたはClaude Code上でMarkdown中心に検証する。

### Phase 2: 構造化出力

`direction-spec.json`、`prd.json`、`prd-review.json`、`traceability.json`へ移行し、JSON Schemaで自動検証する。

### Phase 3: KB・Memory接続

S3 / Knowledge Base、AgentCore Memory、過去のDecision Logを検索し、根拠付きでPRDへ反映する。

### Phase 4: Executable SpecとSuperpowers接続

```text
PRD
  ↓
Executable Spec Builder
  ↓
Superpowers
  ↓
設計・コード・テスト
```

### Phase 5: レビューと継続更新

実装結果、テスト結果、顧客評価をDirection SpecとPRDへ戻し、文書と実装の乖離を防ぐ。

## 17. 検証題材

最初の題材は「顧客との会議内容をAIで活用したい」が適する。

```text
方向性候補
├─ 議事録全文生成
├─ 決定事項・Action抽出
├─ 過去会議検索
├─ 要件定義書生成
├─ PRD生成
└─ 設計・タスクへの連携
```

方向性により成果物が大きく変わるため、Grill-me Directionの必要性、PRD Builderとの責務分離、Executable Specへの展開を一連で検証できる。

## 18. 結論

推奨する責務分担は次のとおり。

- **Grill-me Direction**: 方向性を探索し、意思決定する
- **Direction Spec**: 決定内容、根拠、対象外、制約を保存する
- **PRD Builder**: Direction Specを製品要求へ構造化する
- **PRD Quality Gate**: 曖昧性、不足、矛盾、トレーサビリティを検査する
- **Spec Expansion**: ユーザーストーリー、受入条件、例外条件へ展開する
- **Executable Spec**: AIが実装・検証できる仕様にする
- **Superpowers**: 設計、計画、TDD、実装、レビューを実行する

最大の特徴は、顧客の言葉を直接コードへ変換しないことである。顧客との対話から方向性を決め、その判断をPRDへ変換し、実行可能な仕様へ展開してからAIコーディングへ渡す。最終的には、顧客対話、組織の記憶、意思決定、製品要求、ソフトウェア設計、実装を一本につなぐAI駆動開発の上流工程基盤を目指す。
