---
name: create-one-pager-svg
description: 長文記事、議事録、調査資料、仕様書を再分析し、内容まで読んで理解できる高密度な1枚図へ再構成して、画像生成モデルを使わずSVGとPNGを生成・検証する。ユーザーが「記事全体を1枚で俯瞰したい」「説明なしで伝わる図解」「One-pager」「高密度インフォグラフィック」「SVGで成果物を作りたい」と依頼したときに使用する。
---

# Create One-pager SVG

原文の要約ではなく、伝達目的に合わせて情報を再構成し、編集可能なSVGを作る。PNGはSVGから派生生成する。画像生成モデルは使用しない。

## 実行原則

- 原文の事実と作成者の再構成を混同しない。
- 「一目で主張が分かる」と「読めば内容まで分かる」を両立する。
- 既定は `dense-modules × editorial-knowledge-map` とする。技術構成が主題なら `process-architecture × blueprint-technical` へ切り替える。
- One-pager Specを、内容設計と描画の契約として必ず保存する。
- SVGを作っただけで完了せず、構造検証、PNG化、目視確認まで行う。
- 原文にない固有名詞、数値、因果関係を追加しない。

## 入力

最低限、原文ファイルまたは貼り付け本文を受け取る。指定がなければ次を採用し、Specの `assumptions` に記録する。

- audience: 原文の想定読者
- purpose: 記事全体を説明なしで俯瞰させる
- language: `ja`
- aspect_ratio: `16:10`
- density: `high`
- style: `editorial-knowledge-map`
- output_formats: `svg`, `png`

## ワークフロー

### 1. 原文を正規化する

ファイル入力では次を実行する。

```powershell
python scripts/normalize_source.py 入力ファイル --output normalized-source.md
```

貼り付け本文では同等の処理を行い、`normalized-source.md` として保存する。本文の意味、数値、見出し順は変更しない。

### 2. 内容を構造化する

`references/content-planning.md` を読み、以下を抽出して `content-structure.json` に保存する。

- 中心主張候補
- 背景、課題、仕組み、具体例、効果、制約、示唆
- 人物・組織・技術・数値・関係
- 原文に明記された事実と、統合して得た共通認識
- 出典位置を持つEvidence Ledger

### 3. 何を1枚で伝えるか決める

中心メッセージを1文に絞る。候補を内部で比較し、対象読者にとって「この記事を読む意味」が最も伝わるものを選ぶ。原文の見出し順をそのまま誌面化しない。

### 4. One-pager Specを作る

`references/one-pager-spec.md` を読み、`one-pager-spec.json` を作る。作成後に検証する。

```powershell
python scripts/validate_spec.py one-pager-spec.json --report spec-validation.json
```

エラーがあれば先へ進まず修正する。

### 5. 1枚の情報構成を考える

重要度に差をつけ、原則5〜7モジュールへ圧縮する。

1. 主役となる中心図または主張
2. 読者が理解に必要な背景・課題
3. 仕組み・関係・プロセス
4. 具体例または根拠
5. 効果・価値
6. 制約・留意点
7. 実務への示唆

内容に合わない項目は無理に入れない。モジュールを均等サイズにしない。

記事や会議録に「広がる可能性」と「失ってはいけないもの」の両方がある場合は、`references/editorial-knowledge-map.md` の `possibility-core-guardrails` を第一候補にする。可能性だけで終わらせず、中心の協働構造、新しく生まれる問い、実践原則、結論まで通す。

### 6. SVG上の視覚レイアウトを考える

`references/layout-and-style.md` を読み、内容に合うレイアウトとスタイルを決める。タイトル、中心、補助、出典の順に視覚階層を付ける。座標、寸法、余白、モジュール間の関係をSpecの `canvas` と `modules[].placement` に確定する。

`editorial-knowledge-map` を選んだ場合は `references/editorial-knowledge-map.md` と `assets/editorial-knowledge-map-tokens.json` も使用する。

### 7. SVGコードを生成する

`references/svg-production.md` を読み、単一の自己完結SVGを生成する。

- `viewBox` を必須とする。
- テキストをパス化しない。
- 外部画像、外部フォント、JavaScript、`foreignObject` を使わない。
- アイコンや装飾はSVGプリミティブで描く。
- 文章は自動改行に頼らず、`tspan` で明示的に改行する。
- タイトルと説明文を含むアクセシビリティ要素を入れる。

### 8. SVGを検証する

まず構造検証を行う。

```powershell
python scripts/validate_svg.py infographic.svg --report svg-validation.json
```

次にPNGへ変換する。`sharp` が必要。

```powershell
node scripts/render_png.cjs infographic.svg infographic.png --scale 2
```

PNGを画像表示ツールで必ず目視し、次を確認する。

- タイトルだけで主題が分かる
- 視線が主役から補足へ流れる
- 小さな文字でも読み取れる
- 文字切れ、重なり、孤立した線がない
- 事実、共通認識、示唆、留意点を区別できる
- 情報量が薄すぎず、原文の貼り付けにもなっていない
- 冒頭の主張帯と末尾の結論帯が同じメッセージを別表現で支えている
- 太い見出し、白い本文カード、線画アイコンが情報階層を助けている

問題があればSpecまたはSVGを修正し、最大3回を目安に再検証する。

### 9. 成果物を保存する

同じ出力フォルダへ次を保存する。

```text
normalized-source.md
content-structure.json
one-pager-spec.json
infographic.svg
infographic.png
spec-validation.json
svg-validation.json
manifest.json
```

最後にManifestを生成する。

```powershell
python scripts/create_manifest.py 出力フォルダ --output manifest.json
```

完了時はSVG、PNG、Specへのリンクと、採用した `layout × style`、残っている警告を簡潔に報告する。

## 失敗条件

次の場合は完成扱いにしない。

- 原文にない事実を主要メッセージへ含めた
- SpecまたはSVG検証にエラーが残る
- PNGを生成または目視確認していない
- 本文が読めない大きさ、または要点だけで内容が伝わらない
- 出典または再構成ラベルがない
