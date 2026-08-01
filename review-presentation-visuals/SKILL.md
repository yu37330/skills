---
name: review-presentation-visuals
description: PowerPointを全ページPNGと4辺QAクロップで確認し、PPTX構造、内容Diff、日本語Lint、画像類似度、Design Direction、Locked Layout、Anti-Slop、Design System準拠、Native ComponentのShape実体を機械証跡として固定する。3秒理解、意思決定、洗練度、編集可能性を独立評価し、納品判定する。
---

# 資料ビジュアルレビュー

Production v9統合版。Review v8の契約を保ち、Native Components v4のShape実体、Component Contract、テーマ別構図差を独立検証する。

完成画像を根拠に資料品質を評価し、再生成可能な修正指示へ変換する。欠陥の有無だけでなく、短時間の理解、図解の必然性、資料全体の表現リズムを評価する。

## 必須方針

- PPTXだけで判断せず、全ページを同じ条件でPNG化する。
- Review v8ではRender Manifestと各ページ上下左右15%のQAクロップを先に作る。
- PPTX監査、内容Diff、日本語Lint、視覚指標を機械生成し、自己申告値で置き換えない。
- Visual Plan v8がある場合はDesign System監査を実行し、選択済みDirection、Locked Layout契約、Component Plan、Design Token、Anti-Slop指標を検証する。Locked Layoutは契約Hashだけでなく、Shapeの実座標を`x/y ±0.05 inch`、`w/h ±0.05 inchまたは2%`で照合する。
- main componentと視覚文法の意味契約、漏斗の母集団連続性、隣接ページのRole Layout・main component反復、左→右主読順の矢印端点を機械監査する。
- Native Components v4はPowerPoint Shape Name／Alt Textの`SDPM::<component_id>::<role>`を読み、Visual Planの計画とPPTX実体をページ単位で照合する。
- Premium Galleryでは同一Componentの`executive`、`editorial`、`technical`が3つの異なる構図署名を持つことを確認する。単一Themeの実デッキでは非該当とする。
- Component Contractの推奨上限、平均Native Element Ratio 0.8以上、汎用カードGridへの退化を機械証跡と原寸画像の両方で確認する。
- 各ページを原寸で確認し、一覧画像でも流れ、密度、シルエットの反復を確認する。
- 一覧画像や複数画像ビューの切り抜きを、文字欠落やはみ出しの根拠にしない。
- 見ていないページを`inspected_slides`へ含めない。
- 内容の正誤はBrief、Outline、原稿と照合する。
- 単なる好みをIssueにしない。
- 各評価軸に、画像で確認できる根拠と残る留保を書く。
- 機械証跡から作る参照点は`score_kind: machine_assisted_reference`と明示し、人間による独立比較評価と混同しない。
- 9点以上は「重大な欠陥がない」だけで与えず、同種の実務資料より優れている観察事実を`benchmark_evidence`へ書く。
- Issueが0件でも、3秒理解テストと表現反復テストを省略しない。
- 採点だけで終わらず、Visual Planまたはslide JSONへ戻せるパッチ指示を作る。
- 自分が生成した資料を評価する場合も基準を緩めない。比較時はA/Bを別々に採点してから差分を見る。
- 文字切れ、欠落、重なり、必須要素の非表示は総合点で相殺せず、納品ハードゲートを`fail`にする。
- PowerPoint実機で未確認のRendererは無条件PASSにせず、`delivery_status: pass_with_rendering_caveat`として制約を明示する。

## レビュー手順

### 1. 入力を準備する

次をそろえる。

- 対象PPTX
- 全ページのPNG
- ページ一覧画像
- Brief、Outline、Visual Plan（存在する場合）
- 比較時は生成方法を伏せたA/B識別子

レンダリング失敗、ページ欠落、解像度不一致を採点前に解消する。

Review v8では次を実行し、生成されたコンタクトシートと4辺クロップを確認する。

```powershell
python scripts/build_review_evidence.py output.pptx preview evaluation `
  --renderer "PowerPoint" --baseline baseline.pptx --visual-plan specs/visual-plan.yaml `
  --repetition-policy strict

# 個別実行が必要な場合
python scripts/build_render_manifest.py preview evaluation/render-manifest.json `
  --renderer "PowerPoint" --pptx output.pptx --expected-slides 10
python scripts/audit_pptx.py output.pptx evaluation/pptx-audit.json
python scripts/lint_japanese_pptx.py output.pptx evaluation/japanese-lint.json
python scripts/extract_visual_metrics.py output.pptx preview evaluation/visual-metrics.json
python scripts/diff_pptx.py baseline.pptx output.pptx evaluation/content-diff.json
python scripts/audit_design_system.py output.pptx specs/visual-plan.yaml evaluation/design-system-audit.json
```

### 2. 機械的欠陥を確認する

次を`critical`として先に確認する。

- 意図しない重なり、はみ出し、欠落、文字切れ
- 読めない文字サイズやコントラスト
- 壊れた画像、図、コネクタ
- 原稿と異なる数値、主張、ページ欠落
- 未解決プレースホルダー

`critical`を確定する前に、対象PNGを単独・原寸で再表示し、4辺クロップとPPTX監査の該当テキストを照合する。表示とソースが矛盾する場合は同一条件で再レンダリングする。ソースに文字が存在してもPNG上で欠けていれば`critical`とする。

### 3. 3秒理解と表現反復を検査する

各ページでタイトルと最初に目に入る要素だけを見て、想定メッセージを再現する。

- `pass`: 主張と方向性を再現できる。
- `partial`: 話題は分かるが、結論または関係性が曖昧。
- `fail`: 話題も主張も誤認する、または入口がない。

一覧画像では、意味上の反復、視覚文法、反復モチーフを分けて検査する。各ページの空間構成、主役図形、読み順、箱依存、結論帯、ノード形状、線の性格、署名モチーフを記録する。さらに縮小表示で似て見えるページ群を高・中の類似クラスへまとめる。

### 4. 固定ルーブリックで評価する

[品質ルーブリック](references/quality-rubric.md)を読み、新規レビューはversion 8の16軸を1〜10点で評価する。`component_craft`ではRole Layoutの必然性、Semantic Slot、部品の寸法・余白・文字階層、主役部品の使い分けを見る。各軸に`evidence`と`caveat`を残し、9点以上には`benchmark_evidence`を追加する。

### 5. 修正指示を作る

[Review出力契約](references/review-contract.md)に従い、`evaluation/review.yaml`を作る。

- `critical`、`major`、`minor`の順に並べる。
- `target`へページ内の位置またはオブジェクト参照を書く。
- `evidence`へ画像で確認できる現象を書く。
- `action`へ移動、サイズ、構成変更、文言短縮などの具体策を書く。
- `patch_hint`へ修正種別と戻し先を書く。
- 単なる装飾上の好みは記録しない。

### 6. 契約を検証する

```powershell
python scripts/validate_review.py evaluation/review.yaml
```

総合点、合否、検査ページ、Issue件数、3秒理解の網羅、9点以上の根拠を検証する。

## version 8の合否条件

次をすべて満たした場合だけ`pass: true`とする。

- `overall_score >= 80`
- 全16軸が7以上
- `critical_issues == 0`かつ`major_issues == 0`
- 3秒理解テストに`fail`がない
- 表現反復テストが`pass`
- 視覚文法テストが`pass`
- サムネイル類似性テストが`pass`
- 内容維持を確認済み
- `slide_count`と検査ページが一致する
- Render Manifest内の全PNGと4辺クロップのハッシュが一致する
- Render Manifestの`render_fidelity`と`host_application_verified`がReviewと一致する。PowerPoint実機未確認時は`rendering_caveat`を必須とする
- PPTX監査、日本語Lint、視覚指標が対象PPTXのSHA-256と一致する
- Design System監査が対象PPTX・Visual Plan・manifestと一致し、Design Token一致率が0.7以上である
- Native Componentを計画したページではShape Name／Alt TextのComponent実体が欠落せず、平均Native Element Ratioが0.8以上である
- Premium GalleryではPremium 15の3 Theme構図差とComponent Contract監査がpassである
- Locked Layout契約と選択済みDesign Directionの追跡がpassである
- グラデーション、Glow、角丸箱・等価カード・画像反復のAnti-Slop監査がpassである
- 改善案件では内容Diffがpassし、タイトル、数値、出典、固有語、ノート、グラフデータが維持される
- 日本語Lintにerrorがない
- ネイティブ要素率と機械抽出したサムネイル類似率が閾値内である
- `render_integrity`、`mandatory_elements`、`content_integrity`、`editability`、`design_system_integrity`、`anti_slop_integrity`、`design_direction_integrity`の納品ゲートがすべて`pass`
- 各納品ゲートの`checked_slides`が全ページを含み、`failed_slides`が空
- コンサル品質テストが`pass`

## 比較評価

- `scripts/prepare_blind_review.py`で候補名をA/B/Cへランダム化し、評価者へ`blind-key.json`を渡さない。
- AとBを先入観なく独立に採点する。
- 同じ原稿、ページ数、メッセージ、画像解像度を使う。
- 総合点だけでなく、軸別差、3秒理解、手直し時間を比較する。
- 情報欠落や編集可能性低下を、見た目の改善と相殺しない。
- 差が10点未満なら改善効果は未確定とする。
- 人間のブラインド評価がなければ、PoC実証済みとは表現しない。

## 出力

YAMLには、対象、スコアと根拠、3秒理解、意味上の反復、視覚文法とモチーフのフィンガープリント、サムネイル類似クラス、ページ別Issue、優先修正一覧、合否を含める。スクリーンショット上だけで直さず、Visual Plan、slide JSON、Design Tokenのどこを変えるかを示す。
