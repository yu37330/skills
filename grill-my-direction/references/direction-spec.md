# Direction Spec v2

Direction Specを最終結論ではなく、問題理解から実験までを保持する中間表現として作る。

## 意味構造

```yaml
core_tension:
  statement: 中心的な葛藤

desired_change:
  from: 現状
  to: 目指す状態

root_causes:
  - cause: 原因仮説
    evidence: 観察・認識・予測・仮説の根拠
    confidence: 0.0

opportunities:
  - id: O01
    opportunity: 望む変化へ近づく機会
    affected_people: 対象
    importance: 0.0

direction_candidates:
  - id: D01
    direction: 方向候補
    opportunity_ids: [O01]
    solves: [解決すること]
    does_not_solve: [解決しないこと]
    risks: [リスク]
    assumptions: [成立前提]
    leverage: [活用資産]
    minimum_experiment: 候補を小さく確かめる行動

selected_direction:
  id: D01
  rationale: 選択理由

evaluation_metrics:
  - name: 評価指標
    definition: 分子・分母・判定方法
    unit_of_analysis: 何を1件とするか
    denominator: 評価対象の母数
    baseline: 現状値と出典、または未確認
    threshold: 継続・撤退条件、または未確認
    threshold_status: confirmed | proposed | unknown
    severity_guardrail: 重大事象の個別停止条件

next_experiments:
  - hypothesis: 検証仮説
    smallest_action: 最小行動
    success_signal: 成功・失敗の観察条件

unresolved_branches:
  - branch_id: B01
    reason: 未解決・保留理由
    revisit_trigger: 再検討条件
    relation: blocks | required_before | informs
```

`leverage`には既に使える経験、能力、データ、関係、制度などの資産を書く。閾値、リスク、成立条件を資産として入れない。

描画用`issues.kind`は、`observed`を`事実`、`reported`を`認識`、`forecast`を`予測`、`assumption`を`仮説`、`unknown`を`未確認`へ対応させる。各issueに`evidence_type`も保持する。本人や関係者の認識を`事実`へ昇格させない。

一つのissueには一つの証拠種別だけを入れる。「退職予定6人」という観察事実と「独り立ち平均18か月との認識」を同じ`事実`カードへ入れない。表示枠を超える場合は、重要度の低い主張を`evidence`または`open_questions`へ移す。

SVGレンダラーは、従来形式の `problem`、`key_question`、`issues`、`direction`、`decisions`、`next_actions`、`risks`、`open_questions`、`evidence` をそのまま受け付ける。v2の意味構造だけが渡された場合は、不足する描画フィールドを機械的に導出し、内容を独立に創作しない。
