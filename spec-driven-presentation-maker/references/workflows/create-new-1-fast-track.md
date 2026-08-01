# Phase 1 Fast Track: Single Approval

要件が十分に与えられた新規資料を、1回の承認で初稿生成へ進める。質問を分割せず、不足情報、推奨案、変更可能な前提をまとめて提示する。

## 成果物

- `specs/brief.md`
- `specs/evidence-index.yaml`
- `specs/outline.md`
- `specs/deck-plan.yaml`（version 3、内容の正本）
- `specs/design-direction-scout.yaml`と代表ページ3案SVG
- `specs/design-resolution.yaml`（Design Systemの自動解決結果）
- `specs/visual-plan.yaml`（version 8、見せ方の正本）
- `specs/art-direction.md`または`specs/art-direction.html`

承認前にPPTXを生成しない。ユーザー承認後は途中確認を挟まずCompose、Review、Polishまで進む。

## 1. 入力を一度だけ索引化する

入力資料を読み、資料作成に使う根拠だけを`specs/evidence-index.yaml`へ保存する。

```yaml
version: 1
materials:
  - id: source-1
    file: source.pdf
claims:
  - id: AI_ADOPTION_58
    statement: AI導入・試験利用は58.0%
    value: 58.0%
    source_id: source-1
    source_location: p.25, 図表3-1
    population: 国内企業 n=1,794
    response_type: 単一回答
    claim_type: fact
```

- 原稿にない数値や主張を追加しない。
- 同じ資料を後工程で全文再読せず、根拠IDから必要箇所だけ再確認する。
- 推論と提案には`claim_type: interpretation|proposal`を付け、根拠事実と区別する。

## 2. Briefとストーリーをまとめて設計する

Briefには、対象読者、利用場面、時間、ページ数、中心問い、主メッセージ、期待する意思決定・行動、制約を記載する。

Outlineは1ページ1主張とし、次を確認する。

- 1～2ページ目で「今日決めること」が分かる。
- 各ページが`fact`、`insight`、`recommendation`、`decision`のどれかを担う。
- 根拠提示だけで終わらず、重要ページは示唆または行動へ接続する。
- 同じ役割、同じ密度、同じKPI表現を3ページ連続させない。
- 最後は判断、担当、期限、次のステップへ着地する。

## 3. Deck Plan v3を作る

[Deck Plan契約](deck-plan-contract.md)を読み、`specs/deck-plan.yaml`を作成する。

```powershell
python scripts/validate_deck_plan.py specs/deck-plan.yaml
```

10ページでは内容上の重要ページを`key_slides`へ2〜3ページ指定する。Deck PlanへPattern、Renderer、密度、モチーフを書かない。

## 4. Design Directionを3案で比較する

代表ページをSafe／Reference-led／Boldの同一内容で作る。スタイル名だけを並べず、SVGを実際に提示する。ブランド資産はブランドガイド、既存PPTX、公式サイト保存物、内蔵Design Philosophyの順で採用する。

```powershell
python scripts/scout_design_directions.py `
  specs/deck-plan.yaml assets/design-system/manifest.yaml specs/design-direction-scout.yaml
```

単一承認では推奨案を明示し、Brief／Outline／Deck Planと同時に方向選択を得る。選択後、`--select safe|reference_led|bold`でScoutを固定する。

## 5. Art Directionへ確定する

ユーザーの用途とテンプレートから、スタイル、テンプレート、フォント、色、影、余白、密度を一案に絞って提案する。明示指定がなければ、次を既定とする。

- 白または明るい無彩色背景
- 影は原則なし。意味のある浮上表現だけに限定
- 色は状態、分類、強調の意味にだけ使用
- 非対称構成と余白で階層を作る
- 必須注記は投影で判読できるサイズを確保

## 6. Design Systemへ解決し、Visual Plan v8を作る

Deck Plan v3と選択済みScoutのSHA-256を固定し、[Design System](../design-system.md)でContext、Composition Grammar、Theme、Locked Role Layout、Renderer、Component Planへ解決する。その結果を使い、`$improve-sdpm-presentation`の`precompose`モードでVisual Plan v8を作る。

```powershell
python scripts/validate_design_system.py assets/design-system/manifest.yaml
python scripts/resolve_design_system.py specs/deck-plan.yaml assets/design-system/manifest.yaml specs/design-resolution.yaml --direction-scout specs/design-direction-scout.yaml
```

- `slide_id`と順序をDeck Planへ一致させる。
- 見出し、根拠、`so_what`、意思決定を複製しない。
- Deck Planの`key_slides`だけを`emphasis: showpiece`にする。
- `deck_type`と`repetition_policy`に応じて視覚多様性の上限を選ぶ。
- `signature_tokens`は`dominant`と`supporting`を区別する。
- `role_layout`、`variant`、`component_plan`はDesign Resolutionから引き継ぎ、ページごとに再選択しない。

```powershell
python scripts/validate_deck_plan.py specs/deck-plan.yaml
python ..\improve-sdpm-presentation\scripts\validate_visual_plan.py specs/visual-plan.yaml
```

## 7. 一度だけ承認を求める

Brief、Outline、Deck Plan、代表ページ3案と推奨方向をまとめて提示する。不足情報もこの時点でまとめて質問する。承認後に方向を固定し、Art Direction、Visual Plan v8、Composeへ進む。

承認後は`create-new-2-compose`へ進む。詳細化範囲、スタイル、テンプレート、フォントを個別に再確認しない。ただしユーザーが未決事項として残した項目だけ確認する。
