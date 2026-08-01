# Changelog

## 2.0.0

- Direction Spec用JSON Schemaを追加
- PRD Schemaを全面拡張し、Direction Specの決定・根拠・制約・未決事項を保持
- `prd.json`をSingle Source of Truthへ変更
- `init_prd.py`と`render_prd.py`を追加
- トレーサビリティでsource ID実在確認、Direction参照確認、推論のみの確定要求検出を追加
- 100点モデルを構想書の配点と一致
- 曖昧表現、TBD、測定不能KPI、スコープ矛盾を重大判定へ反映
- 一括Quality GateとMarkdown/JSONレビュー報告を追加
- 正常系・異常系テストを追加

## 1.0.0

- 初期MVP
