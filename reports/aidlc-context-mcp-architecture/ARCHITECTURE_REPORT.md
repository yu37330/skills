# AI-DLC v2 × Context MCP アーキテクチャ構想

## 1. 構想の目的

本構想は、GitHub Copilot、Claude Code、Amazon QなどのAIコーディングクライアントから、AI-DLC v2による再現性の高い開発プロセスを実行しながら、個人の記憶、プロジェクト固有の意思決定、チーム・組織の知識、根拠となる原文を適切に取得・保存・再利用する基盤を整備するものである。

単なるRAG付きコーディングエージェントではなく、個人知をプロジェクトへ適用し、プロジェクトで得た学びを組織知へ昇格させる循環を目指す。

![全体アーキテクチャ](./architecture.png)

## 2. 基本的な役割分担

本構成では、AI-DLC、MCP、GitHub、AgentCore Memory、Bedrock Knowledge Base、S3を異なる責務として扱う。

| 構成要素 | 主な責務 | 保存するContext |
|---|---|---|
| AI-DLC v2 | 要件定義、設計、実装、承認、ビルド・テストの進行 | 開発プロセスの規則と工程 |
| GitHub | コード、設計、AI-DLC成果物の正本 | プロジェクト固有のContext |
| AgentCore Memory | 個人・担当者・担当チームの傾向や経験 | Preference、Semantic、Episodic Memory |
| Bedrock Knowledge Base | 組織標準、設計パターン、過去事例の検索 | チーム・組織のKnowledge |
| S3 | 原文、正式文書、監査証跡の正本 | Raw、Normalized、Approved、Audit |
| MCP / AgentCore Gateway | 各保存先や機能へアクセスする共通インターフェース | 原則として永続状態を持たない |
| Context Assembler | 必要なContextの取得・優先順位付け・統合 | AI-DLCへ渡す一時Context |

## 3. AI-DLC v2で残るContext

AI-DLC v2は、長い会話履歴を保持し続けるのではなく、開発中に決まった内容をリポジトリ内のMarkdown成果物として固定する。主な保存先は `aidlc-docs/` であり、次のような情報を残す。

```text
aidlc-docs/
├── aidlc-state.md
├── audit.md
├── inception/
│   ├── requirements/
│   ├── user-stories/
│   └── application-design/
└── construction/
    ├── plans/
    ├── functional-design/
    ├── infrastructure-design/
    └── build-and-test/
```

`aidlc-state.md` は工程の現在地、`requirements/` は承認済みの要求、`application-design/` は構成と設計判断、`audit.md` は質問・回答・承認の証跡、`build-and-test/` はビルド・テスト結果を表す。

会話をリセットした後は、`aidlc-state.md` と現在工程の計画・承認済み成果物を読み直すことで作業を再開する。したがって、AI-DLCのContextは「このプロジェクトで何を決め、どこまで進み、次に何を行うか」を表すプロジェクトMemoryと位置づけられる。

## 4. 個人知・プロジェクト知・組織知の関係

Contextは次の4層に分ける。

```text
個人・担当者の記憶
AgentCore Memory
        ↓
プロジェクト固有の知識と状態
AI-DLC v2 + GitHub
        ↓
チーム・組織で再利用する知識
Bedrock Knowledge Base
        ↓
根拠となる原文・正式文書
S3
```

### 4.1 AgentCore Memory

「誰が普段どのように判断するか」を保存する。例えば、設計を固めてから実装する、保守性を優先する、過去にLambdaの分割過多を問題視した、といった傾向である。正式なプロジェクト決定の保存先にはしない。

### 4.2 AI-DLC v2とGitHub

「このプロジェクトで何を決めたか」を保存する。要求、スコープ、設計判断、承認状態、進捗、テスト結果、変更理由をコードと同じリポジトリで管理する。

### 4.3 Bedrock Knowledge Base

「他の担当者や他のプロジェクトでも利用できるか」という観点で、組織標準、過去事例、設計パターン、一般化した教訓を検索可能にする。

### 4.4 S3

議事録、顧客仕様書、正式な標準文書、監査ログなど、検索結果の根拠となる原本を保存する。Bedrock Knowledge Baseは検索用であり、原本の正本はS3とする。

## 5. MCP構成

MCPはContextの保存先ではなく、Contextや実行機能へのアクセス層として設計する。PoCでは1つのMCPサーバーに論理的なツール群をまとめてもよい。本番ではAgentCore Gatewayを共通入口にし、権限境界に応じて内部を分離する。

```text
AgentCore Gateway
├── Project Context Tools
├── Knowledge Tools
├── Memory Tools
├── Source Tools
└── Ingestion Tools
```

### 5.1 Project Context Tools

- `get_project_context`
- `get_aidlc_state`
- `read_project_file`
- `search_repository`
- `list_changed_files`
- `write_aidlc_artifact`
- `commit_changes`
- `create_pull_request`

最重要ツールは `get_project_context` である。これは `aidlc-state.md`、現在工程の計画、承認済み要求・設計、最近の変更、関連コードをまとめて返す。

### 5.2 Knowledge Tools

- `search_knowledge`
- `get_knowledge_source`
- `search_architecture_standards`
- `search_past_projects`

検索結果には、本文だけでなく、文書種別、承認状態、優先度、更新日時、原文URIなどを付与する。

### 5.3 Memory Tools

- `get_memory_context`
- `get_user_preferences`
- `get_recent_project_memory`
- `save_memory`

Memoryは補助Contextであり、承認済み要求や組織の強制ルールを上書きしない。

### 5.4 Source Tools

- `get_source_document`
- `search_raw_documents`
- `get_document_metadata`

Bedrock Knowledge Baseの回答から、S3上の原文へ追跡できるようにする。

### 5.5 Ingestion Tools

- `upload_to_inbox`
- `start_ingestion`
- `get_ingestion_status`

知識の取り込みはHermesまたは専用パイプラインで行い、分類・正規化・メタデータ付与・レビュー後にKBへ登録する。

## 6. Context Assembler

Context Assemblerは本構成の中核である。ユーザー要求とAI-DLCの現在状態を基に、どのContextを取得するか計画し、MCPツールを呼び出し、重複除去、優先順位付け、Token予算管理を行ったうえでAI-DLC入力を生成する。

Contextの優先順位は次の通りとする。

1. 法令、セキュリティ、組織の強制ルール
2. AI-DLCで承認済みのプロジェクト要求・設計
3. 現在のコードとGitHub上の状態
4. Bedrock Knowledge Baseの過去事例・推奨パターン
5. AgentCore Memoryの個人・担当者の好み

例えば「実装を再開して」という依頼では、次の順に処理する。

1. Intent Routerが `resume_aidlc` と判定する。
2. `aidlc-state.md` を読み、現在工程を確認する。
3. 現在工程の計画、承認済み要求・設計、関連コードを取得する。
4. 必要な組織標準と過去事例をKBから検索する。
5. 個人Memoryを補足Contextとして取得する。
6. Context Assemblerが優先順位に基づき統合する。
7. AI-DLCが正しい工程から再開する。
8. 成果物と状態をGitHubへ保存する。

## 7. 知識取り込みと知識昇格

外部資料は次の流れで取り込む。

```text
会議・メール・仕様書・設計資料
        ↓
Hermes
        ↓
S3 Inbox
        ↓
分類・正規化・メタデータ付与
        ↓
レビュー・承認
        ↓
Bedrock Knowledge Base登録
```

また、AI-DLC成果物からチームKnowledgeへ昇格する逆方向の流れを持たせる。

```text
AI-DLC成果物
        ↓
GitHubで承認
        ↓
再利用価値のある学びを抽出
        ↓
機密情報除去・一般化
        ↓
人またはレビューAgentが承認
        ↓
S3 Approved / Bedrock KBへ登録
```

AI-DLC成果物をすべて自動登録するのではなく、承認済みかつ一般化可能な知識だけを昇格させる。

## 8. 実装対象

### Phase 1：AI-DLCの再開性を成立させる

- AI-DLC v2ルールの導入
- Project Context MCP
- `get_project_context`
- Context Assembler
- GitHub上の `aidlc-docs/` 読み書き

完成条件は、会話をリセットしても正しい工程から再開できることである。

### Phase 2：組織Knowledgeを利用する

- Bedrock Knowledge Base
- Knowledge Tools
- S3原文参照
- 組織標準用AI-DLC Extension

完成条件は、AI-DLCが設計時に組織標準を検索し、採用・非採用理由を成果物へ残せることである。

### Phase 3：個人Memoryを補助利用する

- AgentCore Memory
- Memory Tools
- Preference、Semantic、Episodicの分類
- Memoryと正式な決定の優先順位制御

完成条件は、ユーザーの進め方を参照しつつ、承認済み要求を上書きしないことである。

### Phase 4：知識循環を成立させる

- Hermes / Inbox Pipeline
- Knowledge Promotion Pipeline
- レビュー・承認フロー
- Bedrock Knowledge Baseへの再登録

完成条件は、プロジェクトで得た学びを一般化し、次のプロジェクトから検索できることである。

## 9. 推奨する最初のPoC

最初からすべてを構築せず、1リポジトリ、1ユーザー、1つのAIコーディングクライアントに限定する。

```text
User
  ↓
Claude Code または GitHub Copilot
  ↓
AI-DLC v2
  ↓
Context Assembler
  ↓
Project Context MCP
  ↓
GitHub / aidlc-docs
```

最初の検証テーマは「中断したAI-DLCプロジェクトを、新しいセッションから正しい工程で再開できるか」とする。ここが成立した後、Bedrock Knowledge Base、AgentCore Memory、Hermesを段階的に接続する。

## 10. 最終的な位置づけ

本構成は、AI-DLC v2を開発プロセスエンジン、MCPをContextアクセス層、GitHubをプロジェクトMemory、AgentCore Memoryを個人・担当者Memory、Bedrock Knowledge Baseを組織Knowledge、S3を根拠文書の正本として統合する。

最終的に目指すものは、次の循環である。

```text
個人の経験
  ↓
AI-DLCでプロジェクトへ適用
  ↓
GitHubに要求・設計・結果を記録
  ↓
有効な学びを一般化
  ↓
Bedrock Knowledge Baseへ昇格
  ↓
次のプロジェクトで再利用
```

この循環により、AIコーディング支援を一時的な会話から、個人知・プロジェクト知・組織知が蓄積される継続的なAI駆動開発基盤へ発展させる。
