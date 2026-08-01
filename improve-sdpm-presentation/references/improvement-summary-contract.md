# 改善サマリー契約

自動評価の合格とPoC実証を分離して記録する。新規作成は`version: 3`を使い、改善前後の視覚文法、反復モチーフ、サムネイル類似性を比較する。既存成果物向けにversion 1と2も受け付ける。

```yaml
version: 3
source:
  baseline: baseline/baseline.pptx
  improved: improved/improved.pptx
slide_count:
  baseline: 10
  improved: 10
revisions_used: 2
scores:
  baseline: 59
  final: 86
  delta: 27
visual_grammar:
  baseline:
    box_dominant_ratio: 0.9
    takeaway_band_ratio: 0.8
    distinct_spatial_models: 3
    distinct_primary_primitives: 2
  final:
    box_dominant_ratio: 0.5
    takeaway_band_ratio: 0.4
    distinct_spatial_models: 6
    distinct_primary_primitives: 6
  delta:
    box_dominant_ratio: -0.4
    takeaway_band_ratio: -0.4
    distinct_spatial_models: 3
    distinct_primary_primitives: 4
motif_similarity:
  baseline:
    node_line_dominant_ratio: 0.7
    max_shared_motif_ratio: 0.6
    largest_thumbnail_cluster_ratio: 0.6
    distinct_visual_textures: 4
  final:
    node_line_dominant_ratio: 0.4
    max_shared_motif_ratio: 0.4
    largest_thumbnail_cluster_ratio: 0.3
    distinct_visual_textures: 6
  delta:
    node_line_dominant_ratio: -0.3
    max_shared_motif_ratio: -0.2
    largest_thumbnail_cluster_ratio: -0.3
    distinct_visual_textures: 2
preservation:
  content: true
  order: true
  speaker_notes: true
editability:
  maintained: true
  limitations: []
changed_slides:
  - slide_number: 4
    change_level: transform
    reason: 交差線を減らし、一方向の処理として再構成した
unresolved_issues: []
automated_visual_pass: true
human_validation:
  blind_test_completed: false
  participants: 0
  manual_edit_time_recorded: false
  second_topic_tested: false
poc_status: pending_human_validation
```

## visual_grammar

- 数値はReview v3の`tests.visual_grammar.metrics`から転記する。
- 比率差は`final - baseline`を小数第2位で記録する。
- 種類数差は`final - baseline`を整数で記録する。
- `automated_visual_pass: true`なら、最終版の箱優位率と結論帯率は0.6以下、10ページ以上なら空間構成と主役図形は各5種類以上必要とする。

## motif_similarity

- 数値はReview v4の視覚文法メトリクスとサムネイル類似性メトリクスから転記する。
- 6ページ以上では、`node_line_dominant_ratio`、`max_shared_motif_ratio`、`largest_thumbnail_cluster_ratio`を0.4以下にする。
- 10ページ以上では`distinct_visual_textures`を5種類以上にする。

## poc_status

- `pending_human_validation`: 自動評価のみ合格、または人間評価・別題材テストが不足。
- `partially_validated`: 人間評価または別題材テストの一部を実施。
- `validated`: 自動評価合格、人間のブラインド評価、手直し時間、別題材テストをすべて実施。
- `failed`: 自動評価不合格、内容維持失敗、または改善効果なし。

`validated`は、`automated_visual_pass: true`、維持条件がすべてtrue、ブラインド評価済み、参加者1名以上、手直し時間記録済み、別題材テスト済みの場合だけ指定する。
