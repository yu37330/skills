# Review出力契約

新規レビューは`version: 8`を使う。検証スクリプトは既存成果物向けにversion 1〜7も受け付ける。

## version 8のDirection・Locked Layout・Anti-Slop証跡

v8はv7の16軸を維持し、次をハードゲートとして追加する。

```yaml
version: 8
assessment_scope:
  score_kind: machine_assisted_reference
  human_comparison_performed: false
  interpretation: 総合点は機械証跡を満たす参照評価であり、人間の独立比較評価を代替しない。
deck:
  delivery_status: pass
render_evidence:
  manifest: render-manifest.json
  renderer: PowerPoint
  render_fidelity: host_application
  host_application_verified: true
  rendering_caveat: PowerPoint実機で確認済み
machine_evidence:
  design_system_report: {path: design-system-audit.json, sha256: ...}
  thresholds:
    min_average_native_element_ratio: 0.8
    max_high_similarity_cluster_ratio: 0.4
    min_design_token_match_ratio: 0.7
    max_gradient_fill_count: 0
    max_glow_effect_count: 0
delivery_gates:
  anti_slop_integrity:
    verdict: pass
    evidence: グラデーション、Glow、角丸箱、等価カード、画像反復を機械監査
    checked_slides: [1, 2, 3]
    failed_slides: []
  design_direction_integrity:
    verdict: pass
    evidence: 選択済みScout、Style Profile、完成PNGの特徴を照合
    checked_slides: [1, 2, 3]
    failed_slides: []
tests:
  design_direction_fidelity:
    representative_slide: 1
    observed_traits: [強いサイズ差, 左揃え, 白黒＋1アクセント]
    conflicting_traits: []
    verdict: pass
```

機械監査はScout選択の追跡を保証する。完成画像が選択方向に見えるかは`design_direction_fidelity`で原寸PNGを観察して判定する。
Locked Layout監査はVisual Planの`slot_frames`、Shapeへ記録した生成時bbox、PPTX上の現在bboxを照合する。許容差は位置`±0.05 inch`、幅・高さ`±0.05 inchまたは2%`とし、移動・リサイズをハードゲートで検出する。
PowerPoint実機確認済みは`deck.delivery_status: pass`、それ以外のRendererは`pass_with_rendering_caveat`とし、未確認範囲を`rendering_caveat`へ記録する。

## version 7のDesign System証跡

v7はv6の機械証跡と納品ゲートを維持し、次を追加する。

```yaml
version: 7
machine_evidence:
  design_system_report:
    path: design-system-audit.json
    sha256: ...
  thresholds:
    min_average_native_element_ratio: 0.8
    max_high_similarity_cluster_ratio: 0.4
    min_design_token_match_ratio: 0.7
delivery_gates:
  design_system_integrity:
    verdict: pass
    evidence: Role Layout、Component Plan、Design Token一致を確認
    checked_slides: [1, 2, 3]
    failed_slides: []
```

`scores`と`score_evidence`にはv6の15軸に`component_craft`を加えた16軸を含める。Design System監査がfailの場合、`design_system_integrity`をfailにし、Review全体を不合格とする。

Native Components v4を使う場合、Design System監査には`component_traceability_pass`、`native_element_ratio`、`component_contract_pass`を含める。PPTXのShape Name／Alt TextからVisual PlanのComponent実体を確認できない場合は`design_system_integrity`をfailにする。Premium Galleryでは`premium_theme_composition_pass`も必須とする。

## version 6の機械証跡

v6はv5の15軸、Render Manifest、納品ゲートを維持し、次を追加する。

```yaml
version: 6
deck:
  deck_type: executive_decision
  repetition_policy: strict
machine_evidence:
  audit_report:
    path: pptx-audit.json
    sha256: ...
  visual_metrics_report:
    path: visual-metrics.json
    sha256: ...
  japanese_lint_report:
    path: japanese-lint.json
    sha256: ...
  content_diff_report:
    required: true
    path: content-diff.json
    sha256: ...
  thresholds:
    min_average_native_element_ratio: 0.8
    max_high_similarity_cluster_ratio: 0.4
```

初回資料など比較元がない場合は`content_diff_report: {required: false}`とする。それ以外の3レポートは必須である。各JSONのSHA-256、対象PPTXのSHA-256、ページ数を実ファイルと照合する。

`repetition_policy`に応じて、dominantモチーフ、サムネイル類似率、必要な視覚文法種類数を調整する。`strict`は経営意思決定・提案、`balanced`は分析、`consistent`は定例報告・研修向けである。

## version 5の互換項目

```yaml
version: 5
render_evidence:
  manifest: render-manifest.json
  renderer: PowerPoint
  full_size_reviewed_slides: [1, 2, 3]
  edge_reviewed_slides: [1, 2, 3]
delivery_gates:
  render_integrity:
    verdict: pass
    evidence: 全ページ原寸と上下端クロップで文字切れ・欠落なし
    checked_slides: [1, 2, 3]
    failed_slides: []
  mandatory_elements:
    verdict: pass
    evidence: Brief必須のタイトル、区分タグ、出典をPNG上で確認
    checked_slides: [1, 2, 3]
    failed_slides: []
  content_integrity:
    verdict: pass
    evidence: 数値、主張、根拠、ノートを正本と照合
    checked_slides: [1, 2, 3]
    failed_slides: []
  editability:
    verdict: pass
    evidence: 主要要素をPowerPointネイティブ要素として確認
    checked_slides: [1, 2, 3]
    failed_slides: []
tests:
  consulting_quality:
    decision_visible_by_slide: 1
    evidence_to_implication_slides: [1, 3]
    evidence_to_action_slides: [5]
    showpiece_slides: [1, 5]
    page_economy_failed_slides: []
    verdict: pass
```

`render_evidence.manifest`は`scripts/build_render_manifest.py`で作る。検証時にPNG、上下端クロップ、ハッシュ、ページ数を実ファイルと照合する。

各`delivery_gates`は`checked_slides`で全ページを列挙する。`verdict: pass`では`failed_slides: []`、`fail`では欠陥のあるページ番号を1件以上記録する。

v5の`scores`と`score_evidence`は[品質ルーブリック](quality-rubric.md)の15軸をすべて含める。

## version 4の互換項目

```yaml
version: 4
deck:
  source: improved/improved.pptx
  slide_count: 2
  inspected_slides: [1, 2]
  critical_issues: 0
  major_issues: 0
  minor_issues: 1
  scores:
    message_clarity: 8
    visual_hierarchy: 8
    information_structure: 8
    semantic_visual_fit: 8
    layout_craft: 8
    readability: 8
    consistency: 8
    archetype_variety: 8
    visual_grammar_variety: 8
    editability: 9
  score_evidence:
    message_clarity: {evidence: 全ページのタイトルが結論文で主図と一致する, caveat: 2ページ目は補足文がやや長い}
    visual_hierarchy: {evidence: 視覚的な入口が各ページ1つに限定されている, caveat: なし}
    information_structure: {evidence: 比較軸と処理順が構図だけで判別できる, caveat: なし}
    semantic_visual_fit: {evidence: 結論はヒーロー、処理は一方向フローで表現されている, caveat: なし}
    layout_craft: {evidence: 整列、余白、線の接続に破綻がない, caveat: 2ページ目の下余白がやや狭い}
    readability: {evidence: 原寸表示で文字切れと低コントラストがない, caveat: 補足文の行長が長い}
    consistency: {evidence: 同じ意味に同じ色と形を使用している, caveat: なし}
    archetype_variety: {evidence: ヒーローとフローを意味に合わせて使い分けている, caveat: 2ページ資料のため評価範囲は限定的}
    visual_grammar_variety: {evidence: 焦点型タイポグラフィと横方向カード列でシルエットが異なる, caveat: 2ページ資料のため評価範囲は限定的}
    editability:
      evidence: 文字と単純図解がPowerPointネイティブ要素である
      caveat: SVG部分は図形単位で直接編集できない
      benchmark_evidence: 同種資料で多い全面画像化を避け、主要文言を直接編集できる
  overall_score: 81
  pass: true
tests:
  three_second:
    method: タイトルと最初に目に入る要素だけで主張を再現
    passed_slides: [1, 2]
    partial_slides: []
    failed_slides: []
  pattern_repetition:
    verdict: pass
    repeated_runs: []
  visual_grammar:
    method: 原寸PNGと一覧画像から空間構成、主役図形、読み順、箱依存、結論帯を観察
    thresholds:
      max_box_dominant_ratio: 0.6
      max_takeaway_band_ratio: 0.6
      min_distinct_spatial_models: 2
      min_distinct_primary_primitives: 2
      max_consecutive_same_reading_path: 2
      max_shared_motif_ratio: 1.0
      max_node_line_dominant_ratio: 1.0
      min_distinct_visual_textures: 2
    slide_fingerprints:
      - slide_number: 1
        spatial_model: hero
        primary_primitive: typography
        reading_path: focal
        container_dependency: low
        takeaway_band: false
        visual_texture: typographic
        dominant_node_shape: none
        node_usage: none
        connector_usage: supporting
        connector_character: thin_straight
        signature_tokens: [typographic_focal]
        evidence: 大見出しが単独の焦点を作る
      - slide_number: 2
        spatial_model: linear_horizontal
        primary_primitive: container_cards
        reading_path: left_to_right
        container_dependency: high
        takeaway_band: true
        visual_texture: node_link
        dominant_node_shape: rounded_rectangle
        node_usage: dominant
        connector_usage: dominant
        connector_character: thin_straight
        signature_tokens: [rounded_cards, thin_straight_connectors]
        evidence: 3枚のカードを左から右へ読む
    metrics:
      box_dominant_slides: [2]
      box_dominant_ratio: 0.5
      takeaway_band_slides: [2]
      takeaway_band_ratio: 0.5
      distinct_spatial_models: 2
      distinct_primary_primitives: 2
      repeated_grammar_runs: []
      repeated_reading_path_runs: []
      node_line_dominant_slides: [2]
      node_line_dominant_ratio: 0.5
      distinct_visual_textures: 2
      shared_motifs:
        typographic_focal: [1]
        rounded_cards: [2]
        thin_straight_connectors: [2]
      max_shared_motif_ratio: 0.5
    verdict: pass
  thumbnail_similarity:
    method: ラベルを読まず縮小一覧の部品・線・シルエットで類似ページをまとめる
    threshold:
      max_high_similarity_cluster_ratio: 1.0
    clusters: []
    metrics:
      largest_high_similarity_cluster: []
      largest_high_similarity_cluster_ratio: 0.0
    verdict: pass
  content_preservation:
    verified: true
    evidence: Outlineの主張、数値、ページ数、発表者ノートを照合
slides:
  - slide_number: 1
    title: 統合基盤が研究を加速する
    three_second_test:
      expected_message: 統合基盤が研究を加速する
      observed_message: 統合基盤が中心である
      verdict: pass
      visual_anchor: 中央の統合基盤
      obstacle: なし
    issues: []
  - slide_number: 2
    title: データから実装までを一方向につなぐ
    three_second_test:
      expected_message: データから実装までを一方向につなぐ
      observed_message: 3段階の実装フロー
      verdict: pass
      visual_anchor: 左から右への太い矢印
      obstacle: 補足文がやや長い
    issues:
      - id: S2-I1
        dimension: readability
        severity: minor
        target: 下部の補足文
        evidence: 1行が長く、視線移動が大きい
        action: 2文を1文へ短縮し、最大行長を約25文字にする
        expected_effect: 主図から補足への移動が速くなる
        patch_hint:
          kind: rewrite
          destination: slide_json
          object_ref: slide-2.footer-note
prioritized_actions:
  - issue_id: S2-I1
    reason: 読みやすさの唯一の残課題であるため
```

## score_evidence

- 全評価軸に`evidence`と`caveat`を書く。
- 9点以上の軸には`benchmark_evidence`を書く。
- `evidence`は「問題なし」ではなく、画像やPPTX構造で確認した事実を書く。
- `caveat`がない場合も`なし`と明記する。

## criticalの二重確認

`severity: critical`のIssueには次を追加する。

```yaml
verification:
  full_size_recheck: true
  source_crosscheck: slide JSONのタイトル全文と単独表示した原寸PNGを照合した
  confidence: high
```

`full_size_recheck`は対象PNGを単独・原寸表示した場合だけtrueにする。`source_crosscheck`にはPPTX、slide JSON、Outlineのどれと照合したかを書く。`confidence`は`high`だけを受け付ける。

## 3秒理解テスト

全スライドを`passed_slides`、`partial_slides`、`failed_slides`のいずれか1つへ分類し、各スライドにも同じ`verdict`を記録する。

## 視覚文法テスト

- `slide_fingerprints`は全スライドを1回ずつ含める。
- 箱優位は`primary_primitive: container_cards`または`container_dependency: high`とする。
- `repeated_grammar_runs`は、`spatial_model`、`primary_primitive`、`reading_path`が同じページが3ページ以上連続した番号列を記録する。
- `repeated_reading_path_runs`は、同じ`reading_path`が3ページ以上連続した番号列を記録する。
- 比率と種類数はフィンガープリントから再計算する。推測値を書かない。
- 6〜9ページは空間構成と主役図形が各4種類以上、10ページ以上は各5種類以上必要とする。
- 箱優位率または結論帯率が0.6を超える、種類数が不足する、反復runがある場合は`verdict: fail`とする。
- 視覚文法がfailなら`visual_grammar_variety`にmajor Issueを1件以上付ける。

version 4では各フィンガープリントに`visual_texture`、`dominant_node_shape`、`node_usage`、`connector_usage`、`connector_character`、`signature_tokens`を追加する。同じ署名モチーフまたはノード＋線が主役のページ比率は、6ページ以上で0.4以下とする。

## サムネイル類似性テスト

- ラベルを読まず、縮小一覧の形、線、余白、明暗面だけで似て見えるページをクラス化する。
- `clusters`へ`slides`、`shared_traits`、`strength: high|medium`、`evidence`を書く。
- 最大の`high`クラス比率は、6ページ以上で0.4以下とする。3〜5ページは0.67、1〜2ページは1.0とする。
- 閾値超過時は`visual_grammar_variety`のmajor Issueを1件以上付け、スコアを6以下にする。

## patch_hint

- `kind`: `recompose`、`move`、`resize`、`rewrite`、`replace_visual`、`change_style`
- `destination`: `visual_plan`、`slide_json`、`design_tokens`、`source_content`

内容変更が必要なら`source_content`を指定し、自動適用しない。

## overall_score

品質ルーブリックの重みで計算する。手計算せず、`scripts/validate_review.py`で検証する。
