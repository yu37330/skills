---
name: improve-sdpm-presentation
description: SDPMのDeck Plan v3を内容の正本として参照し、初稿作成前または生成後にVisual Plan v8で見せ方だけを設計する。選択済みDesign Direction、Locked Role Layout、Renderer Router、Native Components v4のPremium 15を使い、内容・根拠・ノートを守りながら洗練度と資料全体のリズムを改善する。
---

# SDPM資料ビジュアル改善

Production v9統合版。Visual Plan v8の契約を保ち、Native Components v4とPremium Role Layoutを差分改善へ接続する。

SDPMの「何を伝えるか」を正本として維持し、「何を最初に見せ、根拠から何を判断させるか」を初稿前から設計する。生成後は全体を無条件に作り直さず、ReviewのIssueへ対応する差分修正を優先する。

## モード

- `precompose`: Deck Plan v3と選択済みDesign Directionを参照してDesign ResolutionとVisual Plan v8を作り、SDPMの初稿生成へ渡す。ベースラインPPTXは不要。
- `improve`: 生成済みPPTXとPNGを評価し、内容を維持して修正する。従来の利用方法。

指定がなければ、PPTXが存在する場合は`improve`、存在しない場合は`precompose`を選ぶ。

## 必須方針

- Deck Plan v3を内容の唯一の正本として扱い、Visual Planへ見出し、根拠、`so_what`を複製しない。
- ページ数、順序、主張、数値、根拠を既定では変更しない。変更が必要ならユーザー承認を得る。
- 各ページの改善レベルを`repair`、`recompose`、`transform`から選び、全ページを同じカード型へ寄せない。
- 各ページのエグゼクティブ見出し、主根拠、`so_what`、意思決定との関係はDeck Planから参照する。
- 情報の関係と図解形式を一致させる。項目数だけでカード、表、フローを選ばない。
- テキスト、単純図解、グラフはPowerPointネイティブ要素を優先する。
- 外部Visual Skillを使う場合も、SVG、HTML、プロンプトなどの元データを保存する。
- ラスター化で編集可能性が落ちる場合は事前に明示する。
- 初回生成または改善後に全ページをPNG化し、`$review-presentation-visuals` version 8で評価する。
- 修正は初回改善後に最大2回とする。同じ問題が再発したらループを止め、生成規則またはレンダリング方式の原因を報告する。
- 自動評価の合格とPoC実証を混同しない。人間のブラインド比較と手直し時間が未測定なら、PoC状態は`pending_human_validation`とする。

## 入力を確認する

次の順で利用可能な入力を確認する。

1. `specs/brief.md`または同等のBrief
2. `specs/evidence-index.yaml`または根拠一覧
3. `specs/outline.md`または同等のOutline
4. `specs/deck-plan.yaml`（存在する場合）
5. `specs/art-direction.html`または`art-direction.md`
6. SDPMのslide JSONと`deck.json`（improveの場合）
7. ベースラインPPTXと全ページのプレビューPNG（improveの場合）

不足時は[SDPM接続契約](references/sdpm-integration.md)を読む。SDPMの新規実行が必要なら、`$spec-driven-presentation-maker`を先に完了する。

## 改善ワークフロー

### 1. モードと正本を固定する

- `precompose`ではBrief、Outline、Evidence Index、Art Directionを固定し、初稿前のVisual Planを作る。
- `improve`では元PPTXを上書きせず保存し、全ページを同一条件でPNG化する。
- ページ数、主メッセージ、主要根拠、発表者ノート、編集可能性を記録する。
- `improve`では`$review-presentation-visuals`でベースラインを先に採点する。
- `baseline/`、`improved/`、`specs/`、`evaluation/`を用意する。precomposeではbaselineを空で作らない。

### 2. Design Systemへ解決し、Visual Plan v8を作る

[Visual Plan契約](references/visual-plan-contract.md)と[視覚設計ルール](references/visual-planning-rules.md)を読み、Design Resolutionを参照して`specs/visual-plan.yaml`を作る。

- Deck Planの`slide_id`、`relationship`、`key_slides`を参照し、内容を書き直さない。
- `composition_grammar`、`theme`、`role_layout`、`variant`、`component_plan`をDesign Systemの登録値から選び、抽象的なPattern名だけで終わらせない。Premium 15はComponent Contractのvariantsとcontent_limitsも確認する。
- Design Direction Scoutの選択、Style Profile、Density Profile、Deck Sequenceを一致させる。
- `grid_id`と`layout_contract_sha256`を固定し、`layout_adjustments`にはRole Layoutの`adjustable`だけを書く。`locked`を動かさない。
- Theme変更でRole Layoutを変えない。ページ構造は`slide_purpose`、`relationship`、`headline_type`、`evidence_linkage`で選ぶ。Premium 15ではThemeごとのComponent内部構図差を保持する。
- 専用部品が必要な場合は`design_resolution.component_hint`を使う。Visual Planへ見出し、根拠、数値、`so_what`を複製しない。
- LLMは部品内部の座標・余白・線・影・フォントサイズを生成せず、Component ID、slot、variant、許可済みtoken overrideだけを選ぶ。
- `pattern_family`は関係を最短で伝える形式から選ぶ。
- main componentはDesign Systemの`semantic-visual-contracts.yaml`に適合させる。`pattern_family`、`spatial_model`、`primary_primitive`の名前だけを変えて、同じ部品を別構図と申告しない。
- 母集団が連続する漏斗だけ`cohort_continuity: continuous`を指定できる。異なる母数や連続性不明の比較では漏斗・先細りを使わない。
- `visual_grammar`で、完成画像に現れる空間構成、主役図形、読み順、箱依存、結論帯を先に設計する。
- `motif_fingerprint`で、視覚テクスチャ、線の使い方、反復部品を原子レベルで記録し、各tokenを`dominant`または`supporting`に分類する。
- `change_level`で欠陥修正か、再構成か、表現変換かを明示する。
- 3秒理解の期待メッセージはDeck Planの`executive_headline`を参照し、Visual Planでは`visual_anchor`だけを定義する。
- Deck Planの`key_slides`だけを`emphasis: showpiece`にし、それ以外は`standard`にする。
- `safe_area`でタイトルとフッターを保護し、長い日本語タイトルの切れを防ぐ。
- 同じ`pattern_family`を3ページ以上連続させない。必要なら理由を記録する。
- `repetition_policy: consistent`以外で、隣接ページに同じRole Layoutとmain componentを使う場合は`adjacent_repetition_rationale`を必須とする。
- `card_grid`は独立・並列な項目にだけ使い、選択理由を記録する。
- 図解名が異なっても、同じ角丸箱、矢印、中央ラベル、下部結論帯で見えるなら同一系統として扱う。
- `visual_grammar_policy`で箱優位率、結論帯率、読み順の連続、空間構成と主役図形の種類数を制御する。
- `motif_policy`でdominantモチーフの共有率と、ノード＋線が主役のページ比率を制御する。補助線などsupportingモチーフは共有率へ含めない。
- Deck Planの`deck_type`と`repetition_policy`に応じ、定例報告・研修では意図的反復を許容する。
- Renderer Routerの推奨を採用し、外す場合だけ`override_rationale`を残す。全ページNativeでもよいが、資料全体の理由を必須にする。
- `anti_slop_acknowledged: true`を指定し、例外は登録済みIDと理由を明記する。
- Art Directionがなければ`assets/design-tokens.json`を既定値として使う。

```powershell
python scripts/validate_visual_plan.py specs/visual-plan.yaml
```

### 3. 表現手段を選ぶ

- `sdpm_native`: テキスト、表、グラフ、単純な比較・プロセス。
- `baoyu_diagram`: 構造、接続、処理フローをSVGで表すと理解が大きく改善する場合。
- `visual_explainer`: 複雑な比較や全体構造を試作し、原則PowerPointへ再構築する場合。
- `imagegen`: 写真・情緒的イラストが本質的な場合。文字や精密図解には使わない。

編集可能性の扱いは[Visual Plan契約](references/visual-plan-contract.md)に従う。

### 4. 初稿または改善版を生成する

- `precompose`ではVisual PlanをSDPMのDeck Planとslide JSONへ反映し、初稿を生成する。
- `improve`ではReviewの`patch_hint`を優先し、該当するVisual Planまたはslide JSONだけを変更する。
- Art Directionの色、フォント、余白トークンを守る。
- 本文を縮小して押し込まず、短縮、再構成、表現変換の順で解決する。
- タイトル、主図、補足の強さを分け、`visual_anchor`を最初に見せる。
- 意図しない重なり、はみ出し、欠落、孤立改行、低コントラスト、交差コネクタを解消する。
- タイトル、区分タグ、出典は上端・下端の原寸QAで表示を確認する。ソースに存在するだけでは合格としない。
- 隣接ページのシルエットと密度を一覧画像で確認する。
- Visual Planの`visual_grammar`と完成PNGを照合し、名前だけの多様化になっていないか確認する。
- 一覧画像を縮小表示し、異なる図解名でも同じ部品と線で同じシルエットに見えるページ群を確認する。
- `improved/`へPPTX、slide JSON、Visual Skillの元データを保存する。

### 5. 評価して最大2回差分修正する

- 初回改善を`review-iteration-1.yaml`で評価する。
- `critical`、`major`、3秒理解の`fail`、不適切な反復の順で修正する。
- 修正はVisual Planまたはslide JSONへ戻し、PNGだけを加工しない。
- 修正1回目をiteration 2、修正2回目をiteration 3として評価する。
- 次をすべて満たしたら自動評価を終了する。
  - `overall_score >= 80`
  - すべての評価軸が7以上
  - `critical_issues == 0`かつ`major_issues == 0`
  - 3秒理解テストに`fail`がない
  - 視覚文法テストが`pass`
  - サムネイル類似性テストが`pass`
  - 全スライドを原寸と一覧で検査済み
  - Review v8のDesign System、Locked Layout、Design Direction、Anti-Slop監査と納品ハードゲートがすべて`pass`

比較PoCでは[テスト手順](references/test-protocol.md)に従う。

## 成果物

```text
specs/visual-plan.yaml
baseline/baseline.pptx
baseline/preview/*.png
evaluation/baseline-review.yaml
improved/improved.pptx
improved/slide-json/*.json
improved/preview/*.png
evaluation/review-iteration-1.yaml
evaluation/improvement-summary.yaml
```

`improvement-summary.yaml`は[改善サマリー契約](references/improvement-summary-contract.md)に従い、次で検証する。

```powershell
python scripts/validate_improvement_summary.py evaluation/improvement-summary.yaml
```
