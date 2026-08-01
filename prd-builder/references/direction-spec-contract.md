# Direction Spec Contract v2

## 目的

Direction Specは、Grill-me DirectionからPRD Builderへ渡す契約である。最終結論だけでなく、採用しなかった案、判断根拠、対象外、制約、未決事項、情報源を保持する。

## 必須項目

| 項目 | 説明 |
|---|---|
| schema_version | Direction Spec Schemaの版 |
| project_name | プロジェクト名 |
| problem_statement | 解決する課題 |
| target_users | 対象ユーザー |
| desired_outcomes | 期待する成果 |
| selected_direction | 採用する方向性 |
| decision_rationale | 採用理由 |
| scope | 対象範囲 |
| out_of_scope | 対象外 |
| constraints | 制約。存在しない場合は空配列 |
| assumptions | 前提。存在しない場合は空配列 |
| risks | リスク。存在しない場合は空配列 |
| open_questions | 未決事項。存在しない場合は空配列 |
| sources | 根拠資料 |
| approval_status | 承認状態 |

## 推奨項目

- product_name
- rejected_options
- success_hypotheses
- stakeholder_map
- decision_date
- decision_owner

## 判定ルール

### problem_statement

手段ではなく、観測されている損失、阻害要因、業務上の問題を記載する。

悪い例:

> 生成AIを導入する。

良い例:

> 会議後に決定事項と担当者が共有されず、対応漏れが発生している。

### selected_direction

課題に対して優先するアプローチを記載する。

> 議事録全文の生成より、決定事項・担当者・期限の抽出を優先する。

### open_questions

- `blocking: true`: PRD確定前に解消が必要
- `blocking: false`: Executable Specまたは設計工程で確認可能

Blockingな未決事項が1件でもある場合、PRD Builderは自動生成を停止する。

### approval_status

- `draft`: 作成中
- `review`: レビュー中
- `approved`: 顧客または責任者が承認済み
- `rejected`: 採用不可

PRD Builderの通常実行は`approved`だけを受け付ける。

### sources

各情報源には次を持たせる。

- `source_id`
- `source_type`
- `status`
- `authority`
- `confidence`
- `source_uri`または位置情報

AI推論は`status: inferred`とし、顧客決定と区別する。
