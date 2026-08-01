# PRD: 会議Action抽出システム

> このMarkdownは`prd.json`から自動生成しています。直接編集しないでください。

- PRD ID: `PRD-meeting-action-extractor`
- Status: `review`
- Schema Version: `2.0.0`

## 1. Executive Summary

会議文字起こしから決定事項、担当者、期限、根拠発言を抽出し、対応漏れと認識齟齬を減らす。

## 2. Background

現在は会議終了後に参加者が手作業でActionを整理しており、共有まで平均45分を要し、担当者や期限の記載漏れが発生している。

## 3. Problem Statement

会議後に決定事項、担当者、期限が共有されず、対応漏れと認識齟齬が継続的に発生している。

## 4. Product Goal

会議終了後5分以内に、参加者が決定事項とActionを根拠発言付きで確認できる状態を実現する。

## 5. Target Users

| ID | User | Needs |
|---|---|---|
| USR-001 | プロジェクトリーダー | 会議直後に決定事項と担当者を確認したい |
| USR-002 | 会議参加者 | 自分のActionと期限を根拠発言付きで確認したい |

## 6. User Needs

- 会議終了直後に対応事項を一覧で確認したい
- 担当者や期限が明示されていない項目を誤確定せず確認したい

## 7. Value Proposition

全文議事録の読み直しをせず、実行に必要な決定事項とActionだけを根拠付きで確認できる。

## 8. Desired Outcomes

- 会議終了後5分以内にActionを確認できる
- 対応漏れ件数を現状比50%以上削減する

## 9. Selected Direction and Rationale

**Selected Direction**

議事録全文生成より、決定事項・担当者・期限・根拠発言の抽出を優先する。

**Decision Rationale**

顧客ヒアリングで最大損失が議事録作成工数ではなく、対応漏れと認識齟齬であると確認されたため。

## 10. Success Metrics

| ID | Metric | Baseline | Target | Measurement | Frequency | Owner | Source |
|---|---|---|---|---|---|---|---|
| MET-001 | Action確認可能時間 | 平均45分 | 会議終了後5分以内 | 会議終了時刻からレビュー画面表示時刻までを監視ログで計測する | リリース後30日間は毎日、その後は週次 | Product Owner | meeting-2026-07-31 |
| MET-002 | 対応漏れ件数 | 月10件 | 月5件以下 | 期限超過かつ未着手のAction件数を月次で集計する | 月次 | Project Manager | meeting-2026-07-31 |

## 11. Scope

- 日本語会議文字起こしから決定事項、担当者、期限、根拠発言を抽出する

## 12. Out of Scope

- 会議音声の文字起こし
- 英語会議への対応

## 13. User Scenarios

| ID | Actor | Situation | Goal | Outcome |
|---|---|---|---|---|
| SCN-001 | プロジェクトリーダー | 会議終了直後 | 決定事項と未確定Actionを確認する | 根拠発言付き一覧をレビューし、担当者と期限を確定できる |

## 14. Functional Requirements

| ID | Priority | Status | Requirement | Rationale | Direction | Source |
|---|---|---|---|---|---|---|
| FR-001 | Must | confirmed | システムは日本語会議文字起こしから決定事項、担当者、期限、根拠発言を抽出して一覧表示する。 | 会議後の対応漏れと認識齟齬を防ぐため。 | selected_direction, scope[0] | meeting-2026-07-31 |
| FR-002 | Must | confirmed | システムは担当者または期限が発言内に明示されていない場合、その項目を未確定として人間レビューへ送る。 | AIが存在しない担当者や期限を確定値として出力することを防ぐため。 | decision_rationale, risks[0] | meeting-2026-07-31 |

## 15. Non-functional Requirements

| ID | Category | Status | Requirement | Measurement | Target | Direction | Source |
|---|---|---|---|---|---|---|---|
| NFR-001 | Performance | confirmed | システムは会議終了後に登録された文字起こしを処理し、結果表示までの所要時間を5分以内にする。 | 会議終了時刻からレビュー画面に結果が表示された時刻までを監視ログで計測する。 | 95パーセンタイルで5分以内 | desired_outcomes[0] | meeting-2026-07-31 |
| NFR-002 | Security | confirmed | システムは会議文字起こしと抽出結果を社内認証済み利用者だけが閲覧できるようにする。 | 権限のないテストアカウント100件によるアクセス試験で拒否率を測定する。 | 拒否率100% | constraints[0] | security-standard-001 |

## 16. Data Requirements

- 入力文字起こしには発言者ID、発言本文、発言時刻を含める
- 出力には決定事項、担当者、期限、根拠発言、確定状態を含める

## 17. AI-specific Requirements

- Applicable: `True`

### Inputs
- 日本語会議文字起こし
- 発言者メタデータ
- 会議日時

### Outputs
- 決定事項
- 担当者
- 期限
- 根拠発言
- 確定状態

### Quality Evaluation
- 承認済み評価データセットで決定事項抽出の適合率90%以上を確認する

### Error Handling
- 担当者や期限が明示されない場合は推測せず未確定と出力する

### Human-in-the-loop
- 未確定項目はプロジェクトリーダーがレビューして確定する

### Explainability / Evidence
- 各抽出項目に元の根拠発言と発言時刻を付与する

## 18. Security and Compliance

- 会議文字起こしと抽出結果は社内認証済み利用者に限定する
- 監査ログを180日間保持する

## 19. Dependencies

- 発言者情報付きの日本語会議文字起こしが提供されること

## 20. Constraints

- Bedrock上で利用可能なモデルを使用する

## 21. Assumptions

- 会議文字起こしには発言者情報と会議終了時刻が含まれる

## 22. Risks

| ID | Risk | Impact | Likelihood | Mitigation | Source |
|---|---|---|---|---|---|
| RISK-001 | 発言に担当者が明示されず誤った担当者を推測する可能性がある | high | medium | 担当者が明示されない場合は未確定として人間確認へ送る | meeting-2026-07-31 |

## 23. Release Strategy

- Phase 1で決定事項とAction抽出を限定チームへ提供し、30日間の精度と対応漏れを評価する
- Phase 2で対象会議を拡大する

## 24. Open Questions

| ID | Question | Blocking | Owner | Due Date | Source |
|---|---|---|---|---|---|
| Q-001 | 精度評価用データを誰が承認するか | False | Product Owner | 2026-08-15 | meeting-2026-07-31 |

## 25. Decision Log

| ID | Decision | Rationale | Owner | Date | Source |
|---|---|---|---|---|---|
| DEC-001 | 議事録全文生成より、決定事項・担当者・期限・根拠発言の抽出を優先する。 | 最大損失が対応漏れと認識齟齬であると確認されたため。 | Customer Product Owner | 2026-07-31 | meeting-2026-07-31 |

## 26. Source Traceability

| Requirement ID | Direction Spec | Source | Evidence | Confidence |
|---|---|---|---|---|
| FR-001 | selected_direction, scope[0] | meeting-2026-07-31 | 顧客は全文議事録より決定事項、担当者、期限、根拠発言の確認を優先すると合意した。 | high |
| FR-002 | decision_rationale, risks[0] | meeting-2026-07-31 | 担当者の誤推測が対応漏れにつながるため、明示されない場合は未確定にする方針が合意された。 | high |
| NFR-001 | desired_outcomes[0] | meeting-2026-07-31 | 会議終了後5分以内にActionを確認できることを期待成果として合意した。 | high |
| NFR-002 | constraints[0] | security-standard-001 | 社内セキュリティ標準は会議情報へのアクセスを認証済み利用者に限定している。 | high |

## 27. Sources

| Source ID | Type | Status | Authority | Confidence | URI | Location |
|---|---|---|---|---|---|---|
| meeting-2026-07-31 | meeting_transcript | approved | customer | high | s3://example/meeting-2026-07-31.md | topic: Action管理 |
| security-standard-001 | internal_standard | reference | security_department | high | s3://example/security-standard.md | section: data handling |
