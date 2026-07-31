# Direction Graph

Direction Specを直接レイアウトへ流さず、概念と関係を正規化する。

## ノード

- `current_state`: 現在の状態
- `tension`: 中心的な葛藤
- `root_cause`: 原因と根拠
- `opportunity`: 望む変化へ近づく機会
- `direction_candidate`: 比較した方向候補
- `selected_direction`: 選択した方向
- `experiment`: 次の検証
- `unresolved_branch`: 保留・再確認事項

## 関係

- `creates`: 現状が葛藤を生む
- `explains`: 原因が葛藤を説明する
- `reveals`: 葛藤が機会を示す
- `addresses`: 方向候補が`opportunity_ids`で明示した機会へ対処する
- `selected_as`: 候補が選択方向になる
- `tests`: 実験が選択方向を検証する
- `blocks`: 未解決分岐が解消されない限り方向を採れない
- `required_before`: 方向は選べるが、実行前に解決が必要
- `informs`: 結果が実行方法や次段階の判断を改善する

重要なノードが孤立していないか、原因から方向へ飛躍していないか、選択方向に実験があるかを検証する。候補と機会の関係を推測で補わない。未解決という理由だけで`blocks`にせず、方向選択を不可能にする場合だけ使う。Graphはレイアウトではなく意味の正規表現とし、SVGはGraphから描画用フィールドを導出する。

出力は `assets/direction-graph.schema.json` で検証できる。ノードIDは出力内で一意、エッジの `source` と `target` は存在するノードIDに限る。
