# SDPM接続契約

## precompose接続

SDPMが初稿を作る前に、選択済みDesign Direction、Deck Plan v3、Design Systemを解決し、Visual Plan v8を作る。`deck.mode: precompose`、全ページの`change_level: compose`とする。Deck Plan、Scout、Design System manifestのSHA-256を保存する。

SDPMはVisual Planの次をslide JSONへ反映する。

- 見出し、主根拠、`so_what`、意思決定はDeck Planから反映する。
- `visual_strategy.pattern_family`、`visual_grammar`、`motif_fingerprint`
- `composition_bias`、`safe_area`
- `attention_order`、`emphasis`、`density`
- `deck.design_system`、`design_resolution`、`layout_adjustments`、`component_plan`
- Renderer Routerの選択とAnti-Slop制約

初稿生成後はReview v8を実行し、Visual Planの全面再作成ではなくIssueのあるページだけを差分修正する。内容変更が必要なIssueだけDeck Planへ戻し、自動適用しない。

## 入力の優先順位

1. ユーザーが承認したBrief、Outline、Art Direction
2. SDPMが生成したslide JSONと`deck.json`
3. ベースラインPPTXから抽出した情報

上位入力と下位入力が矛盾する場合は、上位を優先する。主張や数値を推測で補わない。

## 入力が不足する場合

- Briefなし: Outlineと元原稿から対象読者、目的、制約を抽出し、仮Briefを作って明示する。
- Outlineなし: PPTXの各ページから主メッセージを抽出し、仮Outlineを作って明示する。
- Art Directionなし: `assets/design-tokens.json`を仮の既定値として使う。
- slide JSONなし: `$spec-driven-presentation-maker`の既存PPTX取り込み手順を使う。
- PPTXなし: SDPMでベースラインを生成してから比較を開始する。

## 変更してよいもの

- 余白、位置、サイズ、配色、書体、強調方法
- 意味を変えない範囲の文言短縮
- 図解、グラフ、表現パターン
- 視覚的な読み順

## 承認なしで変更しないもの

- ページ数
- 主張、数値、固有名詞、根拠
- 話の順番
- 対象読者と用途

## 出力

ベースラインを上書きしない。Visual Plan、改善後slide JSON、Visual Skillの元ファイル、PPTX、全ページPNG、評価YAMLを同じ実行単位で保存する。
