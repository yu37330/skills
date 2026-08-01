---
name: new-phase-2-compose
description: "Phase 2: Compose slides — design then build with measure feedback"
category: workflow
---

# Phase 2: Compose

Design then build each slide. Build is iterative — place components, measure, adjust.

## Design = Direction × Knowledge × Locked Layout × Native Components × Grammar

Slide design is formed by three layers:
- **Style** (art-direction.html) — visual tokens: colors, typography, spacing, decoration
- **Components** — building blocks: how to construct each element (card, icon-label, table, etc.)
- **Patterns** — composition thinking: how to arrange components to express a message

Design Systemの登録要素は初稿時の契約として扱う。未登録の構成を即興で増やさず、既存Role Layoutのvariantで解決できない場合だけregistryへ追加する。
Do not shy away from complex compositions or subtle decoration — details that carry
no information still carry craft. The audience feels the difference.
Bold layouts — asymmetry, extreme size contrast, generous whitespace, full-bleed visuals —
create impact. Safe, centered, evenly-spaced arrangements are forgettable.
The slide-json-spec gives you the full vocabulary of what's possible; components and patterns
show how others have used that vocabulary. Use them as a springboard, not a ceiling.
Style decides *how it looks*. Components decide *what to use*. Patterns decide *how to compose*.

**Before starting:**

```bash
python scripts/validate_deck_plan.py specs/deck-plan.yaml
python scripts/validate_design_system.py assets/design-system/manifest.yaml
python ../improve-sdpm-presentation/scripts/validate_visual_plan.py specs/visual-plan.yaml
uv run python3 scripts/pptx_builder.py examples patterns
```

`specs/deck-plan.yaml`がない既存案件では、OutlineとArt Directionから先に作成する。全仕様と全Componentsを一括で読まない。採用した要素に必要な仕様とガイドだけを読む。

- テキスト、図形、線だけ：`workflows slide-json-quick-spec`
- 表：追加で`guides table`
- グラフ：該当する`guides chart-bar|chart-line|chart-pie`
- アーキテクチャ／フロー：`guides arch-layout-engine`
- Gridが必要なページだけ：`guides grid`
- Componentsは候補一覧を確認し、採用する種類だけ読む。`components/all`は禁止する。

**Reminder:** Read relevant guides as needed before building elements. When a slide contains a chart, read the corresponding guide (`guides chart-bar`, `guides chart-line`, or `guides chart-pie`). When a slide is an **architecture / system / flow diagram** (anything you'd describe as "what connects to what"), read `guides arch-layout-engine` and build it with the layout engine (the `arch_diagram` MCP tool, or `pptx_builder.py layout`) — it auto-routes the arrows and minimizes crossings, so you never hand-place icon/arrow coordinates. Only fall back to hand-placement (`guides arch-elements`) for fine-tuning or non-flow art.

Slides that share a label prefix in the outline share a visual base — use override (inheritance) to build them. The base slide carries the common elements; each derived slide adds or highlights its part. Slide transitions between them create animation effects.

---

## Procedure

```
load(slide-json-spec, grid-guide, components)
patterns = read("examples patterns")   # read the full catalog once

calibrate(first representative slide)
for slide in slides:
    read(deck-plan entry + selected pattern only)
    write(complete slide JSON once)
    measure(complete slide)
    patch only if lint or measurement fails
```

最初の代表ページでタイトル、本文、注記の文字計測を校正する。以後はページを完成単位で書いて計測し、要素単位の測定を繰り返さない。例外は、長いタイトル、密集表、特殊フォント、初使用レイアウトだけとする。

JSONファイルは書込み失敗を避けるため1ページずつ保存する。ただし、デザイン判断はDeck Planで全ページ分を先に完了し、ページごとに再検討しない。
Writing all slides in a single operation risks output truncation and write failure — always write per slide.

---

## Design

For each slide, think through what to say and how to show it — together.

1. `specs/deck-plan.yaml`から内容を、`specs/visual-plan.yaml`から見せ方を読み、どちらもページごとに再決定しない
2. Visual Plan v8の`design_resolution`と`component_plan`をそのまま使い、Role Layoutのslot順へDeck Planの内容を流し込む
3. `grid_id`と`layout_contract_sha256`を守り、`layout_adjustments`以外の座標規則を即興変更しない
4. Art DirectionのDesign Tokenを適用する。Theme変更でRole Layout IDは変えない。Premium 15ではThemeをDesign System選択として扱い、Component Engine内の構図・読み順・タイポグラフィ差を保持する
5. `native_components_v4`実装がある部品は`scripts/native_components.py`を使い、同じ部品を手書きしない。LLMが出すのはComponent ID、外枠frame、Deck Planから流し込むcontent、theme、variant、許可済みtoken overrideだけとする
6. Visual Planで選択済みのPatternと、必要なら代替候補1件だけを読む。全Patternをページごとに再読しない
7. Renderer Routerの選択を使い、外部試作は必要ならNativeへ再構築する
8. Visual Planの密度列、見せ場、空間構成、主役図形、読み順、視覚テクスチャ、dominantモチーフ上限、`composition_bias`、`safe_area`を守る
9. 完成画像がRole Layoutの意図と一致しない場合は、座標微調整ではなくRole Layoutのvariantへ戻る

Native Componentが返す`componentId`、`sourceComponentId`、`componentRole`は削除しない。PPTX BuilderがShape NameとAlt Textへ`SDPM::<component_id>::<role>`として保存し、Review v8が完成PPTXの実体を監査する。

### Token Discipline

The **active style** is `specs/art-direction.html` (created in Phase 1) — the Source of Truth for design tokens. It is a living document: new tokens can be added during Phase 2 when the design requires values not yet defined (e.g. a new accent color for a diagram, a new font size role). Add the token to `:root` first, then use it in slide JSON.

Every `fontSize` and hex color in the slide JSON **must** come from a token defined in
the active style's `:root`. No ad-hoc values.

- **fontSize** — use only values that appear as `--fs-*` variables (e.g. 14, 20, 24, 28, 36, 48).
  If the design needs a size that doesn't exist, add a new `--fs-*` token to art-direction.html
  first, then use it.
  - At `generate` time, fontSize values are checked against `--fs-*` tokens in the active style.
    Out-of-token values produce warnings (build still succeeds). Resolve before delivery.
- **hex color** — use only values that appear as `--*` color variables. If the design needs a
  color that doesn't exist, add a new token to art-direction.html first, then use it.
  Colors embedded in inline directives (e.g. `{{#FF9900:text}}`) are subject to the same rule.
  - Not automatically validated at build time — self-check before delivery.

### Shape Text Discipline

When a shape needs a label, write the label in the shape's `text` (or
`paragraphs` / `items`) property. **Never** layer a separate `textbox` on top
of a shape with the same bounding box to add a label. This anti-pattern is
the single most common cause of label/shape collision in generated decks.

```json
// Wrong — two elements stacked at identical coordinates
{"type": "shape",   "x": 100, "y": 200, "width": 200, "height": 100, ...}
{"type": "textbox", "x": 100, "y": 200, "width": 200, "height": 100,
 "text": "Label", ...}

// Right — single shape with its own text
{"type": "shape", "x": 100, "y": 200, "width": 200, "height": 100,
 "text": "Label", "fontSize": 20,
 "align": "center", "verticalAlign": "middle", ...}
```

When deciding whether the next element should be a `textbox`: if its
position or size would match an existing `shape`, it must NOT be a textbox —
move the text into the shape and stop. A textbox is only the right element
when it stands alone, OR when it occupies a region distinct from any shape
on the slide.

Build emits an "Overlay textbox detected" warning when this anti-pattern
is found in the produced JSON, but the goal is to never write it — by the
time the warning fires, the slide JSON is already wrong.

See `slide-json-spec.md` (shape section, "Labeled shapes — use `text`,
never overlay a textbox") for the full rule and examples.

## Build

Build is not a single pass — it is a loop of place, measure, adjust.

The actual rendered size of an element affects what comes next. A title that wraps to 3 lines
instead of 2 pushes the content area down. A card whose text is wider than expected needs a
different width — which changes the spacing for all cards in the row. You cannot know these
until you measure — and you cannot measure until you write.

ページを完成単位で書き、次で計測する。

```bash
uv run python3 scripts/pptx_builder.py measure {output_json} -p {slide_number}
```

Reports each text element's actual position, size, line count, and text preview.
Compare the actual size against your intended size (the `height` you declared in JSON).
The measure output includes guidance on what to adjust when sizes don't match.

タイトル、本文、出典にはセーフエリアを設ける。タイトルは折返し後の実測高を確保し、上端から48px以上、フッターは下端から48px以上内側に置く。長い日本語タイトルは、フォント縮小より文言短縮または2行用タイトル枠を選ぶ。

If measure reveals that the layout structure itself doesn't work (not just a size tweak, but
the design assumption was wrong — e.g., too much text for a 3-column layout), go back to
Design and rethink the structure. Forcing text into a broken layout produces worse results
than changing the layout.

**coordinate calculation:**
- Decide structure first, then calculate coordinates — computing coordinates before structure makes the layout rigid
- **grid command**: rectangular layouts — rows × columns with items at intersections
- **inline python** (`python3 -c "..."`): everything else — arcs, bezier curves, radial placement, trigonometric positions, color interpolation, any free-form calculation. Use it whenever you need a value that isn't a simple grid intersection
- Relying only on grid produces rectangular arrangements for every slide. Inline python unlocks curves, diagonals, and organic placement that give a deck visual variety
- When both are needed (e.g. arc positions + card internals), use inline python for the outer structure and grid for the inner content

**search-assets:**
- AWS icons have `_dark` and `_light` variants — select based on the template's background color from `analyze-template` Theme Colors (dark background → `_dark`, light background → `_light`)

**build_elements:**
- Do not carry over colors or styles from source slides — always apply the new theme's design guidelines because source styles conflict with the target theme
- Do not use emoji in slide text, titles, or notes — emoji render inconsistently across platforms. Use icons (`search-assets`) instead
- Include reference URLs in `notes` (after `---` separator) when the slide content is based on external sources
- When placing images, maintain the original aspect ratio — run `image-size {path} --width {px}` or `--height {px}` to get the correct dimensions before writing the element. If width-based calculation exceeds the content area height, recalculate with `--height` instead
- When building a code block, use the `code-block` command and include the output via `{"type": "include", "src": "code.json"}`

**custom template:**
- Use layout names from `analyze-template` output in the `layout` field
- When using a layout for the first time, read its detail via `analyze-template {template} --layout {name}` to understand placeholder positions and content areas

---

## Next Step

Once all slides are composed, read `create-new-3-review` and proceed to Phase 3.
Do NOT ask the user for confirmation — continue non-stop.
The user is away once Phase 2 starts. Stopping to ask breaks the flow and delays completion.
