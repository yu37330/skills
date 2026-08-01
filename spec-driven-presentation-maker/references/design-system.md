# Theme-independent PowerPoint Design System

内容から編集可能な部品へ落とすときに読む。方向、文脈、Layout、Component、Rendererをページごとに再発明しない。

## v8の層構造

- Design Direction Scout: 同じ代表ページのSafe／Reference-led／BoldをSVGで比較し、採用後だけ完全Style Profileを読む。
- Design Knowledge Catalog: Context Model、Style Profile、Density Profile、Deck Sequence、Layout Gridを保持する。
- Design Tokens: 色、書体、余白、線、角、影を定義する。
- Native Components: 見出し、数値、比較、示唆、出典、判断、行動欄を編集可能な要素で作る。
- Locked Role Layouts: 意味スロットと正確なGridを定義し、`locked`と`adjustable`を分ける。
- Composition Grammars: デッキ全体の論理と密度のリズムを制御する。
- Renderer Router: 関係性と編集要件からNative／Diagram／Infographic試作／Visual Explainer試作／Imageを選ぶ。
- Anti-Slop: 汎用グラデーション、Glow、等価カード量産、Pill過多、画像反復を検出する。

構造はテーマから選ばない。Deck Planの`slide_purpose`と`relationship`からRole Layoutを選び、その後にThemeを適用する。

## 標準手順

```powershell
python scripts/validate_design_system.py assets/design-system/manifest.yaml
python scripts/scout_design_directions.py `
  specs/deck-plan.yaml assets/design-system/manifest.yaml specs/design-direction-scout.yaml
# 3案確認後、選択を固定する
python scripts/scout_design_directions.py `
  specs/deck-plan.yaml assets/design-system/manifest.yaml specs/design-direction-scout.yaml --select safe
python scripts/resolve_design_system.py `
  specs/deck-plan.yaml assets/design-system/manifest.yaml specs/design-resolution.yaml `
  --direction-scout specs/design-direction-scout.yaml
```

Design ResolutionをVisual Plan v8へ転記する。

- `deck.design_system.composition_grammar`、`theme`
- `deck.design_system.style_profile`、`density_profile`、`deck_sequence`
- `slides[].design_resolution`、`layout_adjustments`、`component_plan`

Visual Plan v8検証後、Composeでは`role_layout`のslot順と`layout_contract_sha256`を守る。見出し、主張、根拠本文はDeck Planから取得し、Component Planへ複製しない。

## Native Component

高頻度部品は次でslide JSON fragmentへ変換する。

```powershell
python scripts/native_components.py component-input.json component-elements.json
```

入力例：

```json
{
  "component": "metric_pair.gap",
  "frame": {"x": 180, "y": 280, "width": 1560, "height": 360},
  "content": {
    "left": {"value": "91.6%", "label": "業務効率化・迅速化"},
    "right": {"value": "3.9%", "label": "売上・利益向上"},
    "separator": "vs"
  },
  "tokens": {"primary": "#17365D", "accent": "#2E75B6"}
}
```

`native_components.*`実装がある部品はスクリプトを優先する。`slide_json_native`はRole LayoutのslotとDesign Tokenを使う。

## 変更規則

- 同じ役割でも登録済みvariantだけを使う。
- `locked`に列挙された余白、タイトル位置、基準線、列比率を変更しない。調整は`adjustable`だけに限定する。
- Theme変更でRole LayoutやComponent IDを変更しない。
- 同じRole Layoutを資料タイプの連続上限より多く並べない。
- `footer`や`tag`の補助部品は統一してよい。`main`の主役部品とシルエットを意味に応じて変える。
- 未登録部品を使う場合は、先にregistryへID、slot、実装、編集可能性を登録する。
- 外部Rendererの試作は元データを保存し、編集可能性が必要ならNativeへ再構築する。

## テンプレートを使う場合

```powershell
python scripts/analyze_template_design_system.py template.pptx template-analysis
```

`theme.json`、`layout-index.yaml`、`component-inventory.yaml`、`visual-guideline.md`を確認する。レンダリング済みPNGがある場合は`--preview-dir`で`preview-contact-sheet.png`も作る。テンプレートを背景画像化せず、Master／Layout／Placeholderを使う。
