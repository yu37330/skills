# 企業内AIにおける情報取得方式とユースケース設計（2026年版）

**作成日：2026年8月4日**

## エグゼクティブサマリー

企業内AIの情報取得は、「RAGかエージェントか」という二者択一ではありません。実務上は、情報源、取得方式、制御方式、検証方式の4層を分離し、質問の種類に応じて組み合わせます。RAGは非構造文書から関連箇所を取得する検索基盤であり、Agentic RAGは検索を質問分解・再検索・証拠評価によって制御する仕組みです。現在の設備状態、承認済み設計版、在庫・品質実績などは、RAGではなく業務DB・API・ログをSource of Truthとして直接参照します。

**結論：** 単純な正式事実はメタデータ付きEvidence RAGまたは決定的なDB検索、複数資料の背景・理由・因果分析はAgentic RAG、関係性や影響範囲はGraphRAG、コード探索はSymbol・AST・Git検索、現在状態はDB・API・ログ、重大判断は人間承認を中心に設計します。

## 1. 基本モデル

- **情報源**：原本、Drive/S3、Git、PLM、MES、QMS、ERP、ログ
- **取得方式**：全文検索、ベクトルRAG、ハイブリッド、Evidence RAG、GraphRAG、SQL、API、コード検索
- **制御方式**：固定ワークフロー、Tool-using Agent、Agentic Retrieval、Agentic RAG
- **検証方式**：原文、版数、適用日、業務システム、矛盾検知、回答保留、人間承認

## 2. 情報取得方式

### 全文・キーワード検索
型番、設備番号、エラーコード、規格番号、関数名など、正確な文字列の検索に向きます。

### ベクトルRAG
表現揺れや言い換えに強い一方、数値・否定・最新版・適用範囲・権威性を保証しません。

### ハイブリッドRAG
全文検索と意味検索を組み合わせ、リランキングします。企業文書では標準的な初期構成です。

推奨順序：

```text
Identity / ACL filter
  ↓
Metadata filter
  ↓
Keyword + Vector hybrid search
  ↓
Managed reranking
  ↓
Original source read
```

### メタデータ付きEvidence RAG
文書種別、承認状態、版数、発効日、対象設備・製品・拠点、原本URIで候補を限定します。正式事実の候補検索に使います。

### GraphRAG
設備―仕様―変更要求―不具合―担当者などの関係を検索します。影響分析、意思決定履歴、横断探索に向きます。単一仕様値や現在状態の確認には過剰です。

### 原文直接読解／Long Context
対象文書が明確で、文書数が少なく、表・注記・前後関係が重要な場合は、章・ページ・見出し構造を保持して直接読解します。必ずチャンクRAGを通す必要はありません。

### マルチモーダルRAG
PDF内の図、表、画像、設備レイアウト、波形、回路図などを検索・読解します。本文だけでなく、表構造、図とキャプション、脚注、ページ番号を保持するDocument Intelligence Layerが重要です。

### SQL・API・ログ参照
現在値、実績、件数、履歴、状態は業務DB・API・ログへ直接照会します。

### コード専用検索
全文、Symbol、AST、Call Graph、Git履歴、PR・Issue、CIログを組み合わせます。

## 3. 制御方式

- **固定ワークフロー**：規程・正式仕様など再現性重視
- **Tool-using Agent**：RAG、SQL、API、Git等を選択
- **Agentic Retrieval**：質問をサブクエリへ分解して並列検索
- **Agentic RAG**：計画→検索→証拠評価→再検索→統合→回答
- **Multi-Agent**：検索、反証、専門領域、統合を役割分担
- **Deep Research型**：広範な情報源を長い手順で探索
- **Human-in-the-loop**：重大判断で人間が証拠・結論を承認

Agentic RAGを上位互換として一律適用するのではなく、質問の複雑度・リスクでルーティングします。

| 条件 | 推奨方式 |
|---|---|
| 対象文書と検索条件が明確 | 固定ワークフロー |
| 表現揺れを含む単一論点 | ハイブリッドRAG |
| 複数文書を横断 | Agentic Retrieval |
| 検索結果を見て次の探索を変える | Agentic RAG |
| 法務・安全・品質の重大判断 | Human Review |

## 4. 会議情報のユースケース

### データ層

1. Raw Transcript：音声認識原文
2. Clean Transcript：話者・誤字・区切りを整えた全文
3. Topic：論点別整理
4. Minutes：正式議事録
5. Decision Store：決定、状態、適用日、Owner、根拠URI
6. Domain/Evidence：仕様、標準、過去事例、業務システム

### 質問別の取得方式

- 「何が話されたか」：Clean Transcript＋Knowledge RAG
- 「何が決まったか」：Decision Store＋正式議事録
- 「なぜ決まったか」：Agentic RAGで決定、議論、比較資料、過去事例を横断
- 「標準に適合するか」：Decision＋Evidence RAG＋仕様DBの照合
- 「未完了Actionは何か」：Action Storeの構造化検索

## 5. 多種多様な社内文章

- **Knowledge Index**：議事録、メール、メモ、検討資料。発見・背景・類似事例用
- **Evidence Index**：承認済み仕様、標準、規程、変更通知、正式決定。断定根拠候補用
- **Source of Truth**：PLM、MES、QMS、ERP、CRM。現在状態・実績用
- **Archive**：旧版・廃止資料。通常検索から除外

代表例：

- 類似プロジェクト探索：Agentic Retrieval＋Federated Search
- 正式なAI利用ルール：固定ワークフロー＋Evidence RAG＋原文確認
- 専門家探索：Knowledge RAG＋人物・プロジェクトGraph
- アーキテクチャの決定理由：Agentic RAG＋GraphRAG＋ADR/PR検索
- 最新版の特定：文書管理メタデータ／DMS API

## 6. コーディングエージェント

- 関数・クラスの場所：全文／Symbol検索
- 呼び出し元：AST、参照検索、Call Graph
- 処理内容：対象コード直接読解＋README・仕様書RAG
- 仕様と実装の一致：Evidence RAG＋コード検索＋テスト
- 変更理由：git log/blame、PR、Issue、ADR、議事録
- 類似バグ：Issue/PR/CIログ＋Agentic Retrieval
- CI修正：ログ→コード→依存→過去PR→テスト

## 7. その他のユースケース

- **設備異常**：SQL・時系列ログ＋Evidence/Knowledge RAG＋Agentic Investigation
- **設計変更影響**：GraphRAG＋PLM API＋文書RAG
- **規程・品質監査**：Evidence RAG＋ルール評価＋Human-in-the-loop
- **顧客対応**：CRM/QMS/チケットAPI＋メール・報告書RAG
- **技術調査**：Deep Research＋Web＋社内RAG＋GitHub・論文

## 8. セキュリティとガバナンス

### Identity-aware Retrieval

```text
User Identity
  ↓
Authorization / ACL Filter
  ↓
Metadata Filter
  ↓
Hybrid Retrieval
```

検索後に隠すのではなく、権限のない文書を検索候補に入れません。推奨メタデータ：`allowed_users`、`allowed_groups`、`denied_users`、`denied_groups`、`classification`、`information_owner`、`retention_policy`、`export_allowed`。

### プロンプトインジェクション対策

RAGで取得した文書は知識データであり、信頼できる命令ではありません。

- 文書内の命令を実行しない
- データと命令を分離する
- ツール呼び出しをAllowlist化する
- 書き込み操作は人間承認を要求する
- Research Agentは原則読み取り専用とする
- 不審文書を隔離する

## 9. 鮮度・版数・時間軸

推奨メタデータ：

```text
source_updated_at
indexed_at
index_version
content_hash
sync_status
deleted_at
valid_from
valid_to
transaction_from
transaction_to
supersedes
superseded_by
```

Decision Storeは、業務上いつ有効だったかを表す`valid_time`と、システムにいつ登録されたかを表す`transaction_time`を分離します。

## 10. 評価・可観測性

### 通常RAG

- Retrieval Recall / Precision
- MRR / nDCG
- 引用正確性
- 回答忠実性
- 回答完全性

### Agentic RAG

- 質問分解の正しさ
- 検索先・ツール選択
- ツール引数の正しさ
- 必要証拠の網羅率
- 不要検索回数
- 停止判断の正しさ
- 矛盾検出率
- 回答保留率
- 権限違反率

記録対象：Query Trace、Document IDs、Metadata Filters、Reranking Scores、Tool Calls、Evidence Used/Rejected、Token/Cost/Latency、Final Decision。

## 11. 推奨アーキテクチャ

```text
User Question
  ↓
Identity / Authorization
  ↓
Intent・Complexity・Risk Router
  ├─ Deterministic Retrieval
  │    ├─ Metadata Filter
  │    ├─ Hybrid Search
  │    ├─ Reranking
  │    └─ Original Source Read
  ├─ Long Context / Document Structure Read
  ├─ Agentic Retrieval / Agentic RAG
  │    ├─ Query Decomposition
  │    ├─ Evidence Search
  │    ├─ DB・API・Log
  │    ├─ Graph Search
  │    └─ Evidence Sufficiency Check
  ├─ Coding Agent
  │    ├─ Symbol / AST / Call Graph
  │    ├─ Git / PR / Issue
  │    ├─ Specification RAG
  │    └─ Test Execution
  └─ Human Review
       ↓
Evidence Verification Layer
  ├─ Authority
  ├─ Provenance
  ├─ Version
  ├─ Valid Time
  ├─ Freshness
  ├─ ACL
  ├─ Completeness
  ├─ Contradiction
  ├─ Prompt Injection
  └─ Unverified Items
```

## 12. Amazon Bedrock Managed Knowledge Baseがカバーする範囲

Managed Knowledge Baseは、文書RAG基盤の次の領域をマネージド化します。

### カバーする範囲

- S3、Google Drive、SharePoint、Confluence等からの取り込み
- PDF、Office文書、スキャン、図表の解析
- Chunking、Embedding、ベクトルインデックス管理
- キーワード＋ベクトルのハイブリッド検索
- Managed Reranking
- Metadata Filter
- Agentic Retrieval、質問分解、複数回検索の一部
- 一部コネクタでのACL情報取り込みと検索フィルター
- CloudWatch等による同期・検索・ログ監視
- AgentCore Gateway／MCP経由でのツール公開

### 別途設計が必要な範囲

- 利用者認証と最終的な認可境界
- MES、PLM、QMS、ERPの業務データを正とする設計
- Decision Store／Action Store
- 文書・システムの優先順位と業務ルール
- Symbol／AST／Call Graphなどのコード解析
- BOM・設備関係を表す業務Graph／Ontology
- 法務・品質・安全上のHuman Review
- 書き込み・業務実行・アクション制御
- 独自評価、ガバナンス、モデルリスク管理

### 位置づけ

```text
Amazon Bedrock Managed Knowledge Base
＝ 文書取り込み・解析・検索・再ランキング・一部Agentic Retrievalを管理するRAG基盤

Agent / Agentic RAG
＝ Managed KB、DB、API、Graph、コード、原文を使い分ける制御層

Source of Truth
＝ PLM、MES、QMS、ERP、Decision Storeなどの正式情報源

ルール・責任者
＝ 競合する情報のうち、何を正とするか決定する主体
```

Managed KBは想定以上に広い範囲をカバーしますが、企業内の正解管理や業務責任までは代替しません。ACL連動も検索フィルターとして有効ですが、独立した認証・認可境界として扱わない設計が必要です。

## 13. 推奨回答スキーマ

1. 確認できた事実
2. 適用条件・基準日時
3. 根拠と原文位置
4. 推論・解釈
5. 矛盾する情報
6. 未確認事項
7. 次に確認すべき情報
8. 必要な承認者

## 14. 実装ロードマップ

1. 文書分類、メタデータ、ACL、ハイブリッド検索、リランキング、原文リンク
2. Decision/Action Store、Evidence Index、業務API接続、鮮度管理
3. Query Router、質問分解、証拠不足・矛盾検知、回答保留
4. Meeting、Coding、Investigation、Policy Agent、MCP／Tool Gateway
5. GraphRAG、評価データセット、Observability、コスト最適化、Human Review

## 結論

RAGは非構造文書検索の重要な基盤ですが、事実確認の主体ではありません。Agentic RAGは、RAG・全文検索・GraphRAG・SQL・API・原文読解を選択・反復・統合する制御層です。単純な事実検索は決定的に、複雑な調査はエージェンティックに、現在状態はDB・APIで、重大判断は人間を含めて行う構成が適切です。

Amazon Bedrock Managed Knowledge Baseは、文書の取り込み、解析、インデックス、検索、リランキング、一部Agentic Retrievalまでを広くマネージド化できます。一方で、Source of Truth、Decision Store、コード解析、業務Graph、認可境界、責任判断は別レイヤーとして設計する必要があります。
