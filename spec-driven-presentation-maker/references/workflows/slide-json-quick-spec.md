# Slide JSON Quick Spec

一般的な社内・経営資料で使う最小仕様。画像、チャート、表、アーキテクチャなど追加要素が必要な場合だけ、対応ガイドまたは完全版`slide-json-spec`を読む。

## スライド

```json
{
  "layout": "Title Only",
  "background": "#FFFFFF",
  "placeholders": {"0": ""},
  "notes": "発表者ノート\n---\n出典URLまたは資料名",
  "elements": []
}
```

## テキスト

```json
{
  "type": "textbox",
  "x": 120, "y": 80, "width": 1600, "height": 100,
  "text": "結論型の見出し",
  "fontSize": 30,
  "fontFamily": "Yu Gothic",
  "fontColor": "#1F2937",
  "bold": true,
  "marginTop": 0
}
```

## ラベル付き図形

```json
{
  "type": "shape",
  "shape": "rectangle",
  "x": 120, "y": 240, "width": 480, "height": 180,
  "fill": "#EAF1F8",
  "line": "none",
  "text": "図形内のラベル",
  "fontSize": 20,
  "fontColor": "#1F497D",
  "align": "center",
  "verticalAlign": "middle"
}
```

図形と同じ座標へラベル用textboxを重ねない。図形の`text`を使う。

## 線

```json
{
  "type": "line",
  "x1": 200, "y1": 500, "x2": 1500, "y2": 500,
  "color": "#94A3B8",
  "lineWidth": 1.5
}
```

## 共通品質条件

- 1920×1080基準では外周48px以内へ必須文字を置かない。
- タイトル、主図、補足、出典の強さを明確に分ける。
- 本文を縮小して押し込まず、短縮、再構成、ページ分割の順で解決する。
- 影は意味のある浮上表現だけに使う。
- 色はDesign Tokenから取得し、ページ単位で追加しない。
- 全ページに同じ下部結論帯を置かない。
- 重要ページは根拠だけで終わらせず、図内の注釈または示唆へ接続する。
