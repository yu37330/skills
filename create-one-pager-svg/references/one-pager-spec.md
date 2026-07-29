# One-pager Spec

One-pager Specは内容設計、誌面設計、SVG生成の唯一の中間契約とする。

## 必須構造

```json
{
  "spec_version": "1.0",
  "title": "1枚図のタイトル",
  "subtitle": "任意の補助タイトル",
  "core_message": "この1枚で伝える中心メッセージ",
  "audience": "対象読者",
  "purpose": "読後に理解・判断・行動してほしいこと",
  "language": "ja",
  "narrative": {
    "archetype": "possibility-core-guardrails",
    "opening_thesis": "効率化だけではない中心主張",
    "closing_thesis": "図全体を統合する到達点",
    "tensions": [
      {"left": "広がる可能性", "right": "守るべきもの", "resolution": "協働構造"}
    ]
  },
  "source": {
    "title": "原文タイトル",
    "uri": "パスまたはURL",
    "retrieved_at": null
  },
  "canvas": {
    "width": 1600,
    "height": 1000,
    "aspect_ratio": "16:10",
    "safe_margin": 32
  },
  "visual_direction": {
    "layout": "dense-modules",
    "style": "editorial-knowledge-map",
    "density": "high",
    "icon_style": "monoline",
    "section_header_style": "solid-or-subtle-gradient",
    "card_style": "white-outline",
    "palette": {
      "background": "#FFFFFF",
      "surface": "#FFFFFF",
      "navy": "#08245B",
      "blue": "#0B4AA2",
      "blue_light": "#EAF1FB",
      "teal": "#007C89",
      "teal_light": "#E8F5F6",
      "gold": "#B47B00",
      "gold_light": "#FFF5D9",
      "text": "#16233A",
      "muted": "#53637A",
      "line": "#B8C7D9"
    },
    "typography": {
      "font_family": "Noto Sans JP, Yu Gothic, Meiryo, sans-serif",
      "title_px": 60,
      "heading_px": 28,
      "body_px": 17,
      "caption_px": 14,
      "title_weight": 800,
      "heading_weight": 700,
      "body_weight": 500
    }
  },
  "reading_order": ["M01", "M02"],
  "modules": [
    {
      "id": "M01",
      "role": "main",
      "heading": "主役の見出し",
      "summary": "短い説明",
      "importance": 5,
      "evidence_type": "consensus",
      "evidence_ids": ["E01"],
      "content": [
        {"type": "step", "label": "段階名", "detail": "説明"}
      ],
      "placement": {
        "x": 480,
        "y": 220,
        "width": 640,
        "height": 390
      }
    }
  ],
  "footer": {
    "source_label": "出典：原文タイトル",
    "legend": ["事実", "共通認識", "示唆", "留意点"],
    "notes": []
  },
  "assumptions": []
}
```

## 制約

- `spec_version`, `title`, `core_message`, `audience`, `purpose`, `language`, `source`, `canvas`, `visual_direction`, `reading_order`, `modules`, `footer`, `assumptions` を必須とする。
- `editorial-knowledge-map` では `narrative` を必須とし、冒頭主張と結論を対応させる。
- canvasは800〜4000px、safe marginは16px以上とする。
- moduleは3〜9個、推奨5〜7個とする。
- module IDは一意とし、reading_orderに全IDを一度ずつ含める。
- `importance` は1〜5とし、`main` は1〜2個に限定する。
- `evidence_type` は `fact`, `consensus`, `insight`, `caution` のいずれかとする。
- placementはsafe margin内に収める。
- モジュール同士の重なりは、意図した前景表現以外では禁止する。
