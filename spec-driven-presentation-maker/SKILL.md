---
name: spec-driven-presentation-maker
description: 根拠資料から意思決定型のストーリーを設計し、3方向の実物プレビュー、文脈別Design Knowledge、Locked Role Layout、Native Components v4のPremium 15を使って、洗練された編集可能なPowerPointを初稿から生成する。新規資料、提案書、社内説明、経営会議資料、既存PPTX・テンプレート活用に使用する。
---

# PPTX Maker

Production v9統合版。成果物契約はDeck Plan v3、Visual Plan v8、Review v8を維持し、Native Components v4を生成層へ接続する。

根拠、主張、意思決定、視覚設計を先に固定し、PowerPointをJSONから生成する。
All paths in this file are relative to this SKILL.md. `cd` to this directory before running commands.

## CLI

```bash
uv run python3 scripts/pptx_builder.py {command} [args]
python scripts/native_components.py list
python scripts/native_components.py build input.json output.json
```

**Critical constraint:** Do NOT make any decisions about slide structure, content, design, or layout before loading the workflow. The workflow files contain the full process including briefing, outline, and art direction. Wait until the workflow is loaded and follow it step by step.

WindowsではCLI起動時にUTF-8を自動設定する。外部ラッパー側でも必要なら`PYTHONIOENCODING=utf-8`を指定する。

依頼内容からモードが明確なら選択肢を聞き直さず、該当フローへ進む。曖昧な場合だけ次を提示する。

A. New presentation — create slides from scratch
B. Edit existing PPTX — modify a provided file
C. Hand-edit sync — continue from a user-edited PPTX
D. Create style — build a reusable style guide

## Workflow A: New Presentation

When no existing PPTX is provided.

- 要件、対象読者、用途、時間、ページ数、入力資料が揃っている、または承認を1回にまとめる指定がある場合：
  → `uv run python3 scripts/pptx_builder.py workflows create-new-1-fast-track`
- 要件を対話しながら決める場合：
  → `uv run python3 scripts/pptx_builder.py workflows create-new-1-briefing`

高速フローでは、Brief、Outline、Deck Plan、Art Direction要約を一度に提示して承認を得る。承認後は途中確認を挟まず生成・全ページReviewまで進む。

## Workflow B: Edit Existing PPTX

When an existing PPTX is provided. Web UI / API path is preferred:
`upload_file` returns `guideInstruction:
"read_guides([\"import-pptx\"])"` automatically. For CLI flows, run
`uv run python3 scripts/pptx_builder.py guides import-pptx` to start.

## Workflow C: Hand-Edit Sync

When the user hand-edits the generated PPTX in PowerPoint and then asks for further changes.
→ Run `uv run python3 scripts/pptx_builder.py workflows create-new-4-hand-edit-sync` to start.

## Workflow D: Create Style

When the user wants to create a new reusable style guide.
→ Run `uv run python3 scripts/pptx_builder.py workflows create-style` to start.

## 初稿品質と効率の共通原則

- 入力資料を繰り返し読み直さず、最初に`specs/evidence-index.yaml`へ根拠ID、数値、対象、n数、出典位置を保存する。
- `specs/deck-plan.yaml` version 3を内容の正本とし、全ページの主張、根拠、示唆、意思決定との関係を先に設計する。
- Art Direction前にDesign Direction Scoutで同じ代表ページをSafe／Reference-led／Boldの3案へ可視化し、抽象語だけで方向を決めない。ブランドはガイド、既存PPTX、公式サイトの保存物、内蔵哲学の順で採用する。
- `specs/visual-plan.yaml` version 8を見せ方の正本とし、Deck Planの`slide_id`を参照して空間構成、主役図形、読み順、密度、Renderer、Locked Role Layout、Component Planを決める。内容項目を複製しない。
- [Design System](references/design-system.md)を使い、`slide_purpose`、`relationship`、`headline_type`、`evidence_linkage`からComposition Grammar、Role Layout、Semantic Slot、Native Componentへ解決する。ThemeからRole Layoutを選ばない。
- Resolverは見出し文字数、根拠・項目数、注釈文字数をRole LayoutとComponent Contractの上限へ照合し、`primary`→`dense`→代替Layoutの順に選ぶ。Dense上限を超える場合は生成せずValidation Errorにする。
- Context Modelで会議種別、対象者、時間からStyle Profile、Density Profile、Deck Sequenceを決め、採用後だけ完全仕様を読む。
- Role Layoutの`locked`と`slot_frames`は変更せず、`adjustable`だけをVisual Planの`layout_adjustments`で調整する。Shape Name／Alt Textへslot、割当frame、生成時bboxを残す。
- Renderer RouterでNative、Diagram、Infographic試作、Visual Explainer試作、Imageを意味と編集性から選ぶ。試作は必要ならNativeへ再構築する。
- Anti-Slop規則で汎用グラデーション、無作為なGlow、等価カード量産、過剰なPill、画像反復を避ける。
- 高頻度部品は`scripts/native_components.py`でslide JSON fragmentを生成し、座標と装飾をページごとに書き直さない。Premium 15は`executive`、`editorial`、`technical`で構図・読み順・タイポグラフィまで変わるため、色替えへ退化させない。
- LLMはComponent ID、外枠frame、Deck Planからのcontent、theme、variant、許可済みtoken overrideだけを指定し、部品内部の座標・余白・線・影・文字縮小を生成しない。
- Component Engineの`componentId`、`sourceComponentId`、`componentRole`を保持し、PPTXではShape Name／Alt Textの`SDPM::<component_id>::<role>`、`slot`、`frameEmu`、`bboxEmu`をReview証跡にする。
- Visual Plan、Scout、Design Resolutionのファイル参照は成果物からのPOSIX形式相対パスで保存し、作成元PCの絶対パスを残さない。
- Design System fingerprintにはRegistry・Contract・Theme・GridだけでなくComponent描画実装も含める。
- Visual Plan生成前に`semantic-visual-contracts.yaml`を参照し、main componentと`pattern_family`、`spatial_model`、`primary_primitive`の意味を一致させる。
- 母集団が異なる、または連続性が未確認の数値を、漏斗・先細り・段階離脱として描かない。
- 全仕様、全Componentsを一括読込しない。索引を読み、採用した要素のガイドだけを段階的に読む。
- 座標、余白、セーフエリア、表のセル幅など再現可能な計算はCLIやレイアウト機能へ任せる。
- 代表ページで文字計測を校正した後、各ページを完成単位で作り、要素単位の過剰な計測を避ける。
- 初回PPTXをPNG化し、全ページを原寸と一覧で確認する。問題があるページだけJSONへ戻して修正し、最後に全ページを再確認する。
- Deck Plan生成時にEvidence Indexを実照合し、生成後はPPTX構造監査、内容Diff、日本語Lintを実行する。
- タイトル、必須タグ、出典、ページ番号などの必須要素は、存在だけでなく完成PNG上の表示を確認する。
