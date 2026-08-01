# PRD Builder Skill v2

Grill-me Directionの後段で、承認済みのDirection Specを、根拠追跡可能なPRDへ変換・検証するSkillです。

```text
顧客打ち合わせ・KB・Memory
        ↓
Grill-me Direction
        ↓
Direction Spec
        ↓
PRD Builder
        ↓
PRD Quality Gate
        ↓
Executable Spec / Superpowers
```

## v2の主な改善

- `direction-spec.schema.json`を追加し、型・必須項目・ID形式を検証
- Direction Specの方向性、根拠、制約、未決事項をPRDへ保持
- `prd.json`をSingle Source of Truthとし、`prd.md`を自動生成
- 存在しない`source_id`、推論だけに依存する確定要求を検出
- PDF構想の100点モデルと採点項目を一致
- 曖昧表現、TBD、測定不能KPI、スコープ矛盾をQuality Gateへ反映
- `run_quality_gate.py`でSchema、トレーサビリティ、採点を一括実行
- 正常系・異常系のpytestを追加

## 必要環境

- Python 3.10以上
- `jsonschema`
- テスト実行時のみ`pytest`

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## クイックスタート

### 1. Direction Specを検証

```bash
python scripts/validate_direction_spec.py tests/scenarios/complete-direction-spec.json
```

### 2. Direction SpecからPRDの初期JSONを作成

```bash
python scripts/init_prd.py \
  tests/scenarios/complete-direction-spec.json \
  /tmp/prd.json
```

初期JSONはDirection Specの情報を欠落させないための骨格です。機能要求、非機能要求、成功指標などを補完してからQuality Gateを実行します。

### 3. PRD JSONを検証

```bash
python scripts/validate_prd.py tests/scenarios/valid-prd.json
```

### 4. PRD Markdownを生成

```bash
python scripts/render_prd.py \
  tests/scenarios/valid-prd.json \
  /tmp/prd.md
```

### 5. Quality Gateを一括実行

```bash
python scripts/run_quality_gate.py \
  tests/scenarios/valid-prd.json \
  --direction-spec tests/scenarios/complete-direction-spec.json \
  --report /tmp/prd-review-report.md \
  --report-json /tmp/prd-review-report.json
```

判定は次のとおりです。

- 90点以上: 合格
- 80〜89点: 条件付き合格。ただし自動パイプラインは既定で停止
- 79点以下: 差し戻し
- 重大問題あり: 点数に関係なく差し戻し

条件付き合格をCI上で許容する場合のみ、`--allow-conditional`を指定します。

### 6. テスト

```bash
pytest -q
```

## 標準出力

```text
prd-output/
├─ prd.json                  # Single Source of Truth
├─ prd.md                    # prd.jsonから自動生成
├─ prd-review-report.md
├─ prd-review-report.json
├─ open-questions.md
├─ decision-traceability.md
└─ source-map.json
```

## 導入先

Codex、Claude Code、GitHub CopilotなどのSkillまたはInstructionsとして利用できます。各環境のSkill配置規則に合わせて、このフォルダをコピーしてください。
