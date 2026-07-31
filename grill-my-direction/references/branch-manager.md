# Branch Manager

## 分岐モデル

各分岐を内部で次のように管理する。対話中はファイル保存しない。

```yaml
id: B01
parent_id: null
topic: 本当に解決したい問題
question_layer: cause
status: ready
answer: null
evidence_refs: []
dependencies: []
outcome_impact: 0.9
uncertainty: 0.8
unlocking_power: 0.9
revisit_trigger: null
```

## 状態

- `discovered`: 新しく見つかった
- `ready`: 親と依存が解決し、質問可能
- `active`: 現在質問中
- `partially_answered`: 有用な回答はあるが質問意図が未充足
- `resolved`: 判断または必要情報が確定
- `deferred`: 理由を付けて後回し
- `blocked`: 親または依存が未解決
- `invalidated`: 親判断の変更で無効
- `revisit_required`: 前提変化により再確認が必要
- `out_of_scope`: 今回は扱わない

## Frontier

`ready`かつ、すべての親・依存が`resolved`または明示的に`deferred`の分岐だけをfrontierへ入れる。複数あっても質問は一問だけにする。

```text
frontier = ready branches with resolved dependencies
next = max(frontier, outcome_impact + uncertainty + unlocking_power)
```

スコアは[questioning-policy.md](questioning-policy.md)の式を使う。

## 更新

1. 回答充足度により`resolved`または`partially_answered`へ更新する
2. 回答から新しい前提・矛盾・候補を分岐として追加する
3. 子分岐の依存関係を再評価する
4. frontierを再計算する
5. 親判断が変わったら、関連する子を`revisit_required`または`invalidated`へ戻す

望む成果または中心課題が変わった場合は、新しい子分岐ではなく問題フレームの更新として扱う。`problem_frame_version`を増やし、旧フレームの分岐を`revisit_required`、`out_of_scope`、または新フレームの依存へ付け替える。ソフト上限に達していても、変更後の重要分岐へ最大3問の再探索枠を与える。

`deferred`には理由と`revisit_trigger`を必須にする。固定の「全何問中何問」ではなく、分岐の状態を進捗として扱う。
