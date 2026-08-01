# Deck Plan契約

`specs/deck-plan.yaml`は内容設計の唯一の正本である。新規作成はversion 3を使う。version 1〜2は既存案件の互換入力としてのみ扱う。

Visual Planへ見出し、根拠、`so_what`を複製しない。Visual Planは`slide_id`でこのDeck Planを参照し、見せ方だけを定義する。

## version 3

```yaml
version: 3
source:
  brief: specs/brief.md
  outline: specs/outline.md
  evidence_index: specs/evidence-index.yaml
deck:
  audience: 経営層およびAI・DX推進部門
  decision_to_make: 90日PoCを開始するか
  governing_thought: 導入量ではなく変える業務と測る価値を設計する
  slide_count: 10
  approval_mode: single
  deck_type: executive_decision
  repetition_policy: strict
  max_consecutive_same_role: 2
  key_slides: [1, 6, 10]
slides:
  - slide_number: 1
    slide_id: answer
    slide_purpose: key_message
    headline_type: insight
    executive_headline: AI導入の次は、価値を生む業務と成果指標へ接続する
    claim_type: interpretation
    evidence_ids: [AI_ADOPTION_58, AI_EFFECT_GAP]
    primary_evidence: AI導入拡大と企業価値の未接続
    so_what: 今日決めるのは候補選定と90日PoCの開始
    decision_relevance: 会議の判断事項を冒頭で示す
    evidence_linkage: evidence_to_action
    relationship: connection
    must_show: [根拠と示唆の区別]
    must_avoid: [因果の断定]
    notes_outline: 根拠、解釈、今日の判断事項を説明する
```

## 責任範囲

Deck Planに置くもの：

- 主張とエグゼクティブ見出し
- Evidence ID、主根拠、事実・解釈・提案の区別
- `so_what`、意思決定との関係、根拠から示唆・行動への接続
- ページの役割、論理関係、ノート要旨
- 資料タイプ、反復方針、内容上の重要ページ

Deck Planに置かないもの：

- Renderer、Pattern、空間構成、主役図形、読み順
- 視覚テクスチャ、モチーフ、箱・結論帯
- 密度、座標、セーフエリア

これらはVisual Planの正本とする。

## 列挙値

- `deck_type`: `executive_decision`、`proposal`、`analysis_report`、`operating_review`、`training`
- `repetition_policy`: `strict`、`balanced`、`consistent`
- `slide_purpose`: `key_message`、`data_proof`、`comparison`、`root_cause`、`synthesis`、`recommendation`、`decision_matrix`、`roadmap`、`action_plan`
- `headline_type`: `fact`、`insight`、`recommendation`、`decision`
- `claim_type`: `fact`、`interpretation`、`proposal`
- `evidence_linkage`: `evidence_only`、`evidence_with_annotation`、`evidence_to_implication`、`evidence_to_action`
- `approval_mode`: `single`、`guided`

## Evidence Index照合

Validatorは`source.evidence_index`を実際に読み、次を検査する。

- `evidence_ids`が`claims.id`に存在する
- Evidence Index内でIDが重複していない
- `fact`と`interpretation`に根拠IDがある
- `data_proof`は`fact`、`root_cause`・`synthesis`は`interpretation`、提言・ロードマップ・行動ページは`proposal`である
- 空文字や不正なEvidence IDがない
- Deck Planで未使用のEvidence IDを警告する

## 資料タイプと反復

- `executive_decision`、`proposal`: 原則`strict`
- `analysis_report`: 原則`balanced`
- `operating_review`、`training`: 意図的反復を許す`consistent`を選択可能

反復方針は内容上の役割に適用する。視覚的な反復上限はVisual Plan側で資料タイプに合わせて検証する。

## 品質条件

- 1〜2ページ目で意思決定との関係を示す。
- 6ページ以上では、`insight`、`recommendation`、`decision`を合計40%以上にする。
- 6ページ以上では、`evidence_to_implication`または`evidence_to_action`を合計40%以上にする。
- 10ページでは`key_slides`を2〜3ページにする。
- `executive_headline`は話題名ではなく、ページから得る結論を書く。
- `so_what`は見出しの言い換えではなく、判断または次の論点を書く。

## 検証

```powershell
python scripts/validate_deck_plan.py specs/deck-plan.yaml
```
