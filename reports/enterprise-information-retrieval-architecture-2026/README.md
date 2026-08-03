# 企業内AIにおける情報取得方式とユースケース設計（2026年版）

企業内AIの情報取得を、RAG・Agentic RAG・DB/API・GraphRAG・コード検索・人間承認まで含めて整理したレポートです。

## 収録内容

- 情報源・取得方式・制御方式・検証方式の4層モデル
- 会議情報（Raw/Clean Transcript、議事録、Decision Store、Domain Knowledge）の使い分け
- 社内文書横断検索
- コーディングエージェント
- 設備異常・設計変更・規程監査・顧客対応・技術調査
- 2026年時点のベストプラクティス
- Amazon Bedrock Managed Knowledge Baseがカバーする範囲と別途設計が必要な領域

## ファイル

- `enterprise_information_retrieval_report_ja_v2.md`：レポート本文
- `enterprise_information_retrieval_infographic_ja.png`：概要インフォグラフィック

## 中心メッセージ

- 単純な正式事実は、決定的検索またはメタデータ付きEvidence RAGで取得する
- 複数資料の背景・理由・因果分析はAgentic Retrieval／Agentic RAGを使う
- 現在値・実績はDB・API・ログをSource of Truthとして直接参照する
- 重大な法務・品質・安全判断は人間承認を含める
- Managed Knowledge Baseは文書RAG基盤を広くカバーするが、認証境界、Decision Store、業務DBの正しさ、コード解析、業務ルールまでは代替しない
