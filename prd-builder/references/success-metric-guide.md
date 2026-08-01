# Success Metric Guide

## 必須要素

各成功指標には次を持たせる。

- Metric ID
- 指標名
- 現状値
- 目標値
- 測定方法
- 測定頻度
- Owner
- 根拠資料ID

## 良い例

```json
{
  "id": "MET-001",
  "metric": "Action確認可能時間",
  "baseline": "平均45分",
  "target": "会議終了後5分以内",
  "measurement": "会議終了時刻からレビュー画面表示時刻までを監視ログで計測する",
  "frequency": "リリース後30日間は毎日、その後は週次",
  "owner": "Product Owner",
  "source_ids": ["meeting-2026-07-31"]
}
```

## 悪い例

- 作業を効率化する
- 高精度を実現する
- 利用者満足度を向上する
- リアルタイムに表示する

目標値または測定方法がない指標はQuality Gateで重大問題とする。
