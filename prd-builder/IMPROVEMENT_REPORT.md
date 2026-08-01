# PRD Builder Skill v2 改善レポート

## 1. 改善対象

初期版は、Direction SpecとPRDの必須項目確認、PRD Markdownの簡易採点、機能要求のsource ID有無確認を行うMVPだった。一方で、項目の型、source IDの実在性、Direction SpecからPRDへの情報欠落、MarkdownとJSONの不一致、曖昧表現や測定不能KPIの合否反映に課題があった。

## 2. 主な原因

- Direction SpecにJSON Schemaがなく、文字列と配列の取り違えを検出できなかった
- PRD採点が見出しと本文長だけに依存していた
- Traceability検査がsource IDの非空確認だけだった
- PRD MarkdownとPRD JSONが独立しており、内容の乖離を防げなかった
- Direction Specのselected_direction、decision_rationale、constraints、open_questionsをPRD Schemaが保持していなかった
- 異常系テストを自動実行するテストコードがなかった

## 3. 修正内容

### P0対応

- `templates/direction-spec.schema.json`を追加
- `templates/prd.schema.json`をv2へ拡張
- `scripts/init_prd.py`でDirection Specの決定情報をPRD骨格へ移送
- `scripts/render_prd.py`で`prd.json`から`prd.md`を生成
- `scripts/check_traceability.py`でsource ID実在性、Direction参照、推論のみの確定要求を検査
- `scripts/score_prd.py`を構想書の100点モデルへ一致
- `scripts/run_quality_gate.py`で全検証を一括実行
- 曖昧表現、TBD、測定不能KPI、スコープ重複を重大判定へ反映

### P1対応

- Direction Specの`approval_status`とBlocking未決事項をゲート条件に追加
- sourceにauthority、confidence、source_uri、evidence_locationを追加
- review reportのMarkdownとJSON出力を追加
- referencesとtemplatesを補完
- 正常系・異常系13件のpytestを追加

## 4. 旧版との主要差分

| 項目 | 旧版 | v2 |
|---|---|---|
| Direction Spec検証 | 必須キーと空値 | JSON Schema、型、承認、Blocking、重複 |
| PRD正本 | MarkdownとJSONが別管理 | JSONをSingle Source of Truth |
| 採点 | 見出し下の文字数 | 構造化項目、測定可能性、要求品質、根拠 |
| Traceability | source_idsが空でない | 実在確認、状態確認、Direction参照、evidence |
| 推論情報 | 区別のみ | inferredだけのconfirmed要求を停止 |
| KPI | 項目存在のみ | target、measurement、frequency、ownerを検査 |
| テスト | サンプル入出力のみ | pytestによる正常・異常系13件 |

## 5. 検証結果

- Python compileall: 合格
- pytest: 13件合格
- 正常系Direction Spec: 合格
- 正常系PRD Schema: 合格
- 正常系Traceability: 4/4件合格
- 正常系Quality Gate: 100/100、passed
- 存在しないsource ID: rejected
- inferredだけのconfirmed要求: rejected
- 測定不能KPI: rejected
- Must要求の曖昧表現: rejected
- 主要要求のTBD: rejected

## 6. 残る限界

ルールベースのQuality Gateは、文書の意味を完全には理解しない。形式的に整った誤要求や、複雑な業務矛盾の検出には、LLMレビューまたは人間レビューを併用する必要がある。v2は決定論的に検出可能な不備を自動停止し、その上で意味レビューへ渡す基盤として設計している。
