# Traceability Rules

## 目的

各要求が、どのDirection Spec項目、顧客発言、正式資料、規程、推論に基づくかを追跡できる状態にする。

## 必須項目

各機能要求・非機能要求に対し、`traceability`へ次を記載する。

- `requirement_id`
- `direction_refs`
- `source_ids`
- `evidence`
- `confidence`

## source_idルール

- `source_ids`は`PRD.sources`に実在する必要がある
- IDだけを付けるのではなく、`evidence`へ具体的な発言や決定を要約する
- `source_type`、`status`、`authority`、`confidence`を保持する
- 同一`source_id`を重複定義しない

## 確定要求の根拠

- `confirmed`なMust要求は、承認済みDirection Specまたは`status: approved`の情報源を必要とする
- `inferred`だけを根拠に`confirmed`へ昇格させない
- 参考資料だけで顧客業務の確定要求を作る場合は、Ownerの承認を記録する

## Direction Spec参照

`direction_refs`は、次のような実在する項目を指す。

- `selected_direction`
- `decision_rationale`
- `scope[0]`
- `constraints[0]`
- `desired_outcomes[1]`

Direction SpecをQuality Gateへ渡した場合、参照先の実在性を自動検査する。
