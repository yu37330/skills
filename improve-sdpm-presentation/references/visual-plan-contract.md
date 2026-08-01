# Visual Plan契約

Visual PlanをDeck Planとslide JSONの間に置く「見せ方の正本」として扱う。新規作成は`version: 8`を使う。検証スクリプトは既存成果物向けにversion 1〜7も受け付ける。

## version 8のDirection・Locked Layout接続

v8はv7へDesign Direction Scout、Design Knowledge、Locked Layout、Renderer Router、Anti-Slopを追加する。

```yaml
version: 8
source:
  deck_plan: specs/deck-plan.yaml
  deck_plan_sha256: 0123456789abcdef...
  design_system_manifest: ../../../../../assets/design-system/manifest.yaml
  design_system_sha256: 0123456789abcdef...
  design_direction_scout: specs/design-direction-scout.yaml
  design_direction_sha256: 0123456789abcdef...
deck:
  design_system:
    composition_grammar: answer_pyramid
    theme: executive
    style_profile: executive_clarity
    density_profile: D2
    deck_sequence: decision_first
    anti_slop_exceptions: []
  anti_slop_acknowledged: true
slides:
  - slide_id: evidence-gap
    slide_number: 4
    design_resolution:
      role: evidence
      role_layout: chart_insight_premium
      variant: primary
      grid_id: chart_insight_68_32
      layout_contract_sha256: 0123456789abcdef...
      slot_frames:
        header: {x: 0.65, y: 0.55, w: 12.0, h: 0.82}
        main: {x: 0.65, y: 1.62, w: 8.25, h: 4.86}
        annotation: {x: 9.18, y: 2.05, w: 3.22, h: 2.65}
        footer: {x: 0.65, y: 6.92, w: 12.0, h: 0.25}
      component_hint: chart.insight
      selection_reason: Deck Planのdata_proofとcomparisonから解決
    layout_adjustments:
      annotation_count: 1
    component_plan:
      - {component: headline.fact, slot: header}
      - {component: chart.insight, slot: main, variant: primary}
      - {component: annotation.chart_callout, slot: annotation}
      - {component: evidence_footer.full, slot: footer}
```

`source`のファイル参照はVisual PlanからのPOSIX形式相対パスにする。`layout_contract_sha256`は`slot_frames`を含み、PPTX ShapeのAlt Textには`slot`、`frameEmu`、`bboxEmu`を残す。

- `style_profile`はScoutの選択と一致させる。
- `layout_adjustments`にはRole Layoutの`adjustable`だけを書く。`locked`は変更しない。
- Renderer Routerの推奨を外す場合は`visual_strategy.renderer_decision.override_rationale`を書く。
- Anti-Slop例外はmanifestの`allow_with_rationale`にあるIDと理由を指定する。
- Premium 15では`executive`＝Consulting Classic、`editorial`＝Editorial Premium、`technical`＝Technical / Dataとして、Component内部の構図・読み順・タイポグラフィ差を保持する。Theme変更でRole Layout IDは変えない。
- `component_hint`は見せ方の候補であり、Deck Planの内容を複製しない。Component PlanはID、slot、任意のvariantと許可済み`token_overrides`だけを持つ。
- Component Contractのrequired／variants／content_limitsを検証する。座標、内部余白、線、影、フォントサイズはComponent Engineへ任せる。

## version 7のDesign System接続

v7はv6の責任分離を維持し、抽象的なPatternを完成済みのRole LayoutとNative Componentへ解決する。

```yaml
version: 7
source:
  deck_plan: specs/deck-plan.yaml
  deck_plan_sha256: 0123456789abcdef...
  design_system_manifest: C:/Users/.../.codex/skills/spec-driven-presentation-maker/assets/design-system/manifest.yaml
  design_system_sha256: 0123456789abcdef...
deck:
  design_system:
    composition_grammar: answer_pyramid
    theme: executive
slides:
  - slide_id: evidence-gap
    slide_number: 4
    design_resolution:
      role: evidence
      role_layout: evidence_metric_gap
      variant: primary
    component_plan:
      - {component: label.fact_tag, slot: tag}
      - {component: headline.fact, slot: header}
      - {component: metric_pair.gap, slot: main}
      - {component: annotation.so_what, slot: interpretation}
      - {component: evidence_footer.full, slot: footer}
```

Composition GrammarとThemeはdeck単位の正本とし、各ページへ複製しない。各ページはRole、Role Layout、variant、Semantic SlotとComponentだけを保持する。Component Planへ見出し文、数値、示唆本文を複製せず、Deck PlanからCompose時に流し込む。

## version 6の責任分離

- Deck Plan v3: 主張、見出し、根拠ID、`so_what`、意思決定、ページの役割を保持する。
- Visual Plan v6: `slide_id`でDeck Planを参照し、空間構成、主役図形、読み順、Renderer、密度、モチーフ、セーフエリアだけを保持する。
- `key_message`、`consulting_frame`、`executive_headline`、`primary_evidence`をVisual Planへ複製しない。
- `deck_plan_sha256`で承認済み内容の変更を検出する。

```yaml
version: 6
source:
  deck_plan: specs/deck-plan.yaml
  deck_plan_sha256: 0123456789abcdef...
  art_direction: specs/art-direction.html
deck:
  mode: precompose
  preserve_slide_count: true
  rhythm:
    density_sequence: [low, medium, high]
    max_consecutive_same_pattern: 2
  visual_grammar_policy:
    max_box_dominant_ratio: 0.6
    max_takeaway_band_ratio: 0.6
    min_distinct_spatial_models: 3
    min_distinct_primary_primitives: 3
    max_consecutive_same_reading_path: 2
  motif_policy:
    max_dominant_motif_ratio: 0.67
    max_node_line_dominant_ratio: 0.67
    min_distinct_visual_textures: 3
  renderer_policy:
    all_native_rationale: 単純図解とグラフで構成できるため
slides:
  - slide_id: answer
    slide_number: 1
    intent: decision
    attention_order: [headline, visual_anchor, implication]
    visual_strategy:
      pattern: executive_hero
      pattern_family: hero
      change_level: compose
      renderer: sdpm_native
      integration_mode: native
      emphasis: showpiece
      density: low
      rationale: Deck Planの判断事項を一つの焦点で示すため
      composition_bias: asymmetric
      safe_area: {title: strict, footer: strict, edge_inset_px: 48}
      renderer_decision:
        considered: [sdpm_native]
        selected: sdpm_native
        reason: 編集可能な大見出しと数値で表現できるため
      visual_grammar:
        spatial_model: hero
        primary_primitive: typography
        reading_path: focal
        container_dependency: low
        takeaway_band: false
        distinctive_feature: 左上の大見出しと右下の単一数値
      motif_fingerprint:
        visual_texture: typographic
        node_usage: none
        connector_usage: none
        signature_tokens:
          - {token: typographic_focal, role: dominant}
          - {token: thin_straight_connectors, role: supporting}
        dominant_motif: 大見出しの単一焦点
    constraints: {preserve_content: true, editable_required: true, max_text_blocks: 4}
    acceptance:
      visual_anchor: 判断文
      must_show: [Deck Planで指定した根拠と示唆の区別]
      must_avoid: [端部の文字切れ]
```

`signature_tokens`の共有率上限は`role: dominant`だけに適用する。補助線など`supporting`の共通利用は過剰判定しない。

資料タイプと反復方針はDeck Plan v3から読み込む。`strict`、`balanced`、`consistent`の順に、必要な多様性を緩和し、定例報告や研修の意図的反復を許容する。

## version 5の互換構造

v5はv4の視覚文法とモチーフ制御に、初稿前の設計、意思決定型ストーリー、エグゼクティブ見出し、根拠から示唆への接続、見せ場、タイトル・フッターのセーフエリアを追加する。

```yaml
version: 5
deck:
  mode: precompose
  decision_to_make: 90日PoCを開始するか
  governing_thought: 導入量ではなく変える業務と測る価値を設計する
  consulting_quality_policy:
    min_advanced_headline_ratio: 0.4
    min_evidence_to_implication_ratio: 0.4
    min_showpiece_slides: 2
    max_showpiece_slides: 3
slides:
  - slide_number: 1
    consulting_frame:
      slide_purpose: key_message
      headline_type: insight
      executive_headline: AI導入の次は価値を生む業務と成果指標へ接続する
      primary_evidence: 導入拡大と企業価値の未接続
      so_what: 今日決めるのは候補選定と90日PoCの開始
      decision_relevance: 会議の判断事項を冒頭で示す
      evidence_linkage: evidence_to_action
      attention_order: [headline, primary_evidence, so_what]
      remove_if_possible: [説明的な副題, 装飾目的の影]
      showpiece: true
      density_role: climax
    visual_strategy:
      change_level: compose
      composition_bias: asymmetric
      safe_area:
        title: strict
        footer: strict
        edge_inset_px: 48
```

- `deck.mode`: `precompose`または`improve`
- `headline_type`: `fact`、`insight`、`recommendation`、`decision`
- `evidence_linkage`: `evidence_only`、`evidence_with_annotation`、`evidence_to_implication`、`evidence_to_action`
- `density_role`: `breathe`、`build`、`proof`、`climax`、`action`
- `composition_bias`: `asymmetric`、`balanced`、`centered`、`full_bleed`
- `change_level`: precomposeでは`compose`、improveでは`repair`、`recompose`、`transform`

showpieceは根拠だけで終わらせず、`evidence_to_implication`以上へ接続する。

## version 4の互換構造

```yaml
version: 4
source:
  briefing: specs/brief.md
  outline: specs/outline.md
  art_direction: specs/art-direction.html
  baseline_pptx: baseline/baseline.pptx
deck:
  goal: 読者が理解すべきこと
  audience: 対象読者
  preserve_slide_count: true
  design_tokens: assets/design-tokens.json
  rhythm:
    max_consecutive_same_pattern: 2
    density_sequence: [low, medium, medium, high, low]
  visual_grammar_policy:
    max_box_dominant_ratio: 0.6
    max_takeaway_band_ratio: 0.6
    max_consecutive_same_spatial_model: 2
    max_consecutive_same_reading_path: 2
    min_distinct_spatial_models: 4
    min_distinct_primary_primitives: 4
  motif_policy:
    max_shared_motif_ratio: 0.4
    max_node_line_dominant_ratio: 0.4
    min_distinct_visual_textures: 4
  renderer_policy:
    all_native_rationale: ''
slides:
  - slide_id: architecture
    slide_number: 3
    key_message: AgentCoreを中心に既存資産を統合する
    intent: architecture
    relationship: connection
    content_hierarchy:
      primary: AgentCore
      secondary: [Knowledge Base, Lambda, MCP]
      supporting: [接続方法, 処理の流れ]
    visual_strategy:
      pattern: hub_and_spoke
      pattern_family: network
      change_level: transform
      renderer: baoyu_diagram
      integration_mode: embed_svg
      emphasis: central_component
      density: medium
      rationale: 接続関係と中心を文章より短時間で把握できるため
      renderer_decision:
        considered: [sdpm_native, baoyu_diagram]
        selected: baoyu_diagram
        reason: 接続線の管理と再利用可能なSVG保存に適するため
      visual_grammar:
        spatial_model: network
        primary_primitive: network_nodes
        reading_path: spatial
        container_dependency: low
        takeaway_band: false
        distinctive_feature: 中央ノードから四方へ伸びる非対称接続
      motif_fingerprint:
        visual_texture: node_link
        dominant_node_shape: circle
        node_usage: dominant
        connector_usage: dominant
        connector_character: thin_straight
        signature_tokens: [circular_nodes, thin_straight_connectors]
        dominant_motif: 中央円と四本の放射線
    constraints:
      preserve_content: true
      editable_required: true
      max_text_blocks: 6
    acceptance:
      three_second_message: AgentCoreが統合の中心である
      visual_anchor: 中央のAgentCoreノード
      must_show: [中心と周辺の関係, 処理方向]
      must_avoid: [交差する矢印, 長文説明]
```

## 選択肢

- `intent`: `title`、`executive_summary`、`comparison`、`process`、`architecture`、`timeline`、`before_after`、`cause_effect`、`matrix`、`data_insight`、`decision`、`roadmap`、`one_pager`
- `relationship`: `none`、`parallel`、`comparison`、`sequence`、`cause_effect`、`hierarchy`、`containment`、`connection`、`distribution`、`change_over_time`
- `pattern_family`: `hero`、`narrative`、`comparison`、`flow`、`network`、`matrix`、`chart`、`timeline`、`roadmap`、`table`、`card_grid`、`one_pager`
- `change_level`: `repair`、`recompose`、`transform`
- `density`: `low`、`medium`、`high`
- `spatial_model`: `hero`、`stack`、`radial`、`matrix`、`linear_horizontal`、`linear_vertical`、`network`、`editorial_split`、`timeline`、`form`、`freeform`
- `primary_primitive`: `typography`、`layers`、`axes`、`circular_path`、`trace_line`、`kpi`、`network_nodes`、`decision_gates`、`form_fields`、`container_cards`、`image`
- `reading_path`: `focal`、`left_to_right`、`top_to_bottom`、`radial`、`scan_columns`、`z_pattern`、`spatial`
- `container_dependency`: `low`、`medium`、`high`
- `visual_texture`: `typographic`、`node_link`、`axis_plot`、`area_composition`、`trace`、`kpi_editorial`、`form`、`table`、`image`
- `dominant_node_shape`: `none`、`circle`、`rectangle`、`rounded_rectangle`、`mixed`
- `node_usage`、`connector_usage`: `none`、`supporting`、`dominant`
- `connector_character`: `none`、`thin_straight`、`thin_curved`、`thick_band`、`mixed`
- `signature_tokens`: `circular_nodes`、`numbered_nodes`、`rounded_cards`、`thin_straight_connectors`、`thin_curved_connectors`、`thick_directional_band`、`large_color_fields`、`axis_frame`、`typographic_focal`、`form_rules`

`repair`は欠陥修正、`recompose`は同じ要素の再配置、`transform`は関係性に合わせた図解形式の変更とする。

## Rendererと統合方法

| renderer | 主用途 | integration_mode | 編集可能性 |
|---|---|---|---|
| `sdpm_native` | 文章、表、グラフ、単純図解 | `native` | PowerPoint上で直接編集可能 |
| `baoyu_diagram` | 構造図、処理フロー | `embed_svg` | SVG単位。元SVGを保存 |
| `visual_explainer` | 複雑な比較、レイアウト試作 | `rebuild_from_prototype` | PowerPointへ再構築 |
| `imagegen` | 写真、情緒的イラスト | `embed_raster` | 画像単位。文字を含めない |

`editable_required: true`なら`embed_raster`を選ばない。`visual_explainer`の画面画像をそのまま貼らず、PowerPointへ再構築する。

各ページの`renderer_decision.considered`に比較した候補を1件以上書き、`selected`を`visual_strategy.renderer`と一致させる。全ページが`sdpm_native`の場合は、`deck.renderer_policy.all_native_rationale`に資料全体で外部Rendererが不要な理由を書く。

## 視覚文法ポリシー

main componentの意味はDesign Systemの`semantic-visual-contracts.yaml`を正本とする。`pattern_family`、`visual_grammar.spatial_model`、`visual_grammar.primary_primitive`は、そのComponentに許可された値から選ぶ。

漏斗、先細り、幅の縮小を使うページは`visual_strategy.cohort_continuity: continuous`を必須とする。Deck Planが異なる母数、別母集団、非連続を示す場合は使用禁止とする。

`repetition_policy: consistent`以外で隣接ページのRole Layoutとmain componentが同一になる場合は、後続ページへ`visual_strategy.adjacent_repetition_rationale`を記録する。理由がなければ別のRole LayoutまたはComponentへ解決する。

- 箱優位ページは、`primary_primitive: container_cards`または`container_dependency: high`のページとする。
- `max_box_dominant_ratio`と`max_takeaway_band_ratio`は0〜0.6にする。
- 同じ`spatial_model`と`reading_path`の連続は、それぞれ指定上限以下にする。
- 6〜9ページの資料は空間構成と主役図形を4種類以上、10ページ以上は5種類以上使う。短い資料はページ数を上限とする。
- `distinctive_feature`は完成画像で見分けられる特徴を書く。単なる図解名や意図を書かない。
- 多様性のためだけに意味の合わない形式へ変えない。

## モチーフポリシー

- 6ページ以上の資料では、同じ`signature_tokens`の共有率と、ノード・線がともに`dominant`のページ比率を0.4以下にする。
- 3〜5ページは上限0.67、1〜2ページは上限1.0とする。
- 6〜9ページは`visual_texture`を4種類以上、10ページ以上は5種類以上使う。
- `dominant_motif`は図解名ではなく、縮小画像でも識別できる部品と配置を書く。
- 箱を消した結果、すべてを丸ノード＋細線へ置き換えない。
- 同じ色を使うこと自体は反復モチーフに数えない。形、線、番号、配置の組合せを数える。

## 反復の制御

- 同じ`pattern_family`の連続は`deck.rhythm.max_consecutive_same_pattern`以下にする。
- 超える場合は、対象スライドの`visual_strategy.repetition_justification`へ伝達上の理由を書く。
- `card_grid`を使う場合は`visual_strategy.card_grid_justification`へ、項目が独立・並列である理由を書く。
- `pattern_family`が異なっても視覚文法が同じなら、多様とはみなさない。

## 検証

`scripts/validate_visual_plan.py`で必須項目、列挙値、編集可能性、密度列、連続パターン、視覚文法、モチーフ共有率、ノード＋線依存率、Renderer判断を検査する。
