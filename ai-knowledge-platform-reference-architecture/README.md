# AIナレッジ基盤の完成形とユースケース別の最適構成

> Managed Knowledge Base / AgentCore Memory / LLM Wiki / Ontology / GraphRAG を、何でも全部入れるのではなく、ユースケースに応じて必要な層だけ組み合わせるためのリファレンスアーキテクチャ。

最終更新: 2026-08-07

---

## 1. この設計の結論

AIエージェント向けのナレッジ基盤は、次の5つを分けて考えると整理しやすい。

- **Managed KB = 証拠**
- **AgentCore Memory = 経験**
- **LLM Wiki = 承認済み知識**
- **Ontology = 正式な意味・関係・ルール**
- **GraphRAG = 関係探索の強化**

重要なのは、これらを最初から全部実装しないこと。

```text
原文を探したいか                → Managed KB
前回の続きから始めたいか        → AgentCore Memory
整理した知識を共有したいか      → LLM Wiki
正式な意味・関係で判定したいか  → Ontology
間接的な関係を探索したいか      → GraphRAG
```

---

## 2. 完成形リファレンスアーキテクチャ

```text
                         利用者 / Copilot / ChatGPT
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │ AgentCore Runtime / Agent  │
                    │ Router・Planning・Tools    │
                    └───────┬────────────┬───────┘
                            │            │
                   Recall   │            │ Write back
                            ▼            ▼
                 ┌──────────────────────────┐
                 │ AgentCore Memory         │
                 │                          │
                 │ ・セッション状態          │
                 │ ・ユーザー設定            │
                 │ ・Semantic Memory        │
                 │ ・Episodic Memory        │
                 │ ・Reflection             │
                 └────────────┬─────────────┘
                              │
                        知識化候補
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Knowledge / Context Plane                      │
│                                                                  │
│  ┌────────────────────┐ ┌────────────────────┐ ┌──────────────┐ │
│  │ Managed KB         │ │ LLM Wiki           │ │ Ontology     │ │
│  │ Agentic Retrieval  │ │ Git / Markdown     │ │ Accelerator  │ │
│  │                    │ │                    │ │              │ │
│  │ 原文・証拠          │ │ 承認済み知識        │ │ 正式な意味   │ │
│  │ 議事録・設計書      │ │ 標準手順            │ │ 型・関係     │ │
│  │ 技術資料・ログ      │ │ 設計判断            │ │ 制約・ルール │ │
│  └─────────┬──────────┘ └─────────▲──────────┘ └──────┬───────┘ │
│            │                      │                   │         │
│            │        ┌─────────────┴────────────┐      │         │
│            └───────▶│ Knowledge Curation      │◀─────┘         │
│                     │                          │                 │
│                     │ ・出典確認               │                 │
│                     │ ・重複／矛盾チェック      │                 │
│                     │ ・Reviewer Agent         │                 │
│                     │ ・人による承認            │                 │
│                     │ ・知識の昇格／廃止         │                 │
│                     └──────────────────────────┘                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
                    回答・判断・コード実装
                             │
                             ▼
                  結果・経験をMemoryへ戻す
```

GraphRAGは常設の中心機能ではなく、**Managed KBの検索だけでは複数文書間の間接関係を拾い切れない領域で追加評価する機能**として扱う。

```text
Managed KB
   │
   ├── Agentic Retrieval: 質問を分解し、複数回検索する
   │
   └── 必要に応じて GraphRAG を別途評価
          └─ 文書から抽出された関係をたどる
```

---

## 3. 各コンポーネントの役割

| コンポーネント | 一言で言うと | 主な保存・管理対象 | 主な問い |
|---|---|---|---|
| Managed KB | 証拠 | 議事録、設計書、規程、技術資料、ログ | 原文には何と書かれているか？ |
| AgentCore Memory | 経験 | セッション、ユーザー設定、作業履歴、Episode、Reflection | 前回何をしたか？何が成功したか？ |
| LLM Wiki | 承認済み知識 | 標準手順、設計判断、Playbook、用語、FAQ | 現在の推奨・標準は何か？ |
| Ontology | 正式な意味・ルール | 概念、型、関係、制約、業務ルール | 正式な関係は何か？この判断はルール上正しいか？ |
| GraphRAG | 関係探索 | 文書から抽出されたエンティティ・関係 | 間接的につながる情報は何か？ |

---

## 4. AgentCore Memory と LLM Wiki は一部競合する

両者とも「過去の情報を再利用する」ため、役割は一部重なる。

### AgentCore Memory に寄せるもの

- 現在のタスク状態
- ユーザーの好み
- 過去セッション
- 実行したツール
- 作業途中の判断
- 成功・失敗した手順
- 未解決事項
- 類似タスクのEpisode
- Reflectionによる改善候補

```text
「前回どうやったか」
「今どこまで進んでいるか」
「次にどう動くべきか」
```

### LLM Wiki に寄せるもの

- 承認された設計判断
- 正式なアーキテクチャ
- 標準手順
- 継続利用するベストプラクティス
- 障害対応Playbook
- プロジェクト用語集
- 何度も確認される調査結果
- 複数エージェントで共有する知識

```text
「組織として何を知っているか」
「現在の標準は何か」
「なぜこの設計になったか」
```

### 推奨: Memory から Wiki へ知識を昇格する

```text
会話・Agent実行・ツール結果
          ↓
AgentCore Memory
          ↓
Semantic / Episodic Memory
          ↓
Reflection
          ↓
知識化候補を抽出
          ↓
原文・証拠をManaged KBで確認
          ↓
重複・矛盾チェック
          ↓
Reviewer Agent / 人による承認
          ↓
LLM Wikiへ昇格
```

Memoryの内容をそのまま正式知識にしないことが重要。

---

## 5. Managed KB と LLM Wiki の関係

両方を検索対象にする場合でも、原文と整理済み知識を同じ優先度で扱わない。

### 推奨メタデータ

```yaml
doc_type:
  - raw_document
  - meeting_minutes
  - decision
  - wiki
  - playbook

knowledge_status:
  - draft
  - reviewed
  - approved
  - deprecated

authority:
  - primary_source
  - derived
  - curated
```

### 検索優先順位の例

**現在の標準を聞かれた場合**

```text
approved Wiki / Playbook
    > approved Decision
    > 議事録
    > 原文ログ
```

**証拠を聞かれた場合**

```text
原文・正式文書
    > 議事録
    > Wiki
    > Memory
```

---

## 6. Ontology の位置付け

Ontologyは「Wikiをきれいにするための機能」ではなく、Agentが直接参照する意味・ルール基盤。

例:

```text
製品
 └─ 構成される → 部品

部品
 └─ 製造される → 工程

工程
 ├─ 使用する → 設備
 └─ 出力する → 品質特性

不具合
 ├─ 発生した → 工程
 ├─ 関係する → 設備
 ├─ 影響する → 品質特性
 └─ 対応される → 対策
```

Ontologyの更新はMemoryやWikiから完全自動で行わない。

```text
知識候補
   ↓
ドメイン専門家による確認
   ↓
Ontology変更案
   ↓
整合性・ルール検証
   ↓
正式反映
```

---

## 7. GraphRAG と Agentic Retrieval の違い

### Managed KB + Agentic Retrieval

```text
質問
 ↓
LLMが質問を分解
 ↓
複数回検索
 ↓
情報が十分か評価
 ↓
不足なら追加検索
 ↓
統合回答
```

得意:

- 比較
- 調査
- 要約
- 複数文書の統合
- 条件を変えながら検索する質問

### GraphRAG

```text
文書取り込み
 ↓
エンティティ・関係を抽出
 ↓
Graphを構築
 ↓
検索時にベクトル検索 + 関係探索
```

得意:

- 共通エンティティを起点にした探索
- 文書間の間接的な関係
- 複数ホップの探索
- 「関連するものを広めに拾う」検索

### 実務上の位置付け

```text
Agentic Retrieval
= まず使う汎用検索

GraphRAG
= 検索漏れが問題になった関係探索領域で追加評価

Ontology
= 正式な関係・ルールを定義する
```

GraphRAGはOntologyの代替ではない。

---

# 8. 5つの基本パターン

## Pattern A: 検索型

```text
Agent + Managed KB
```

用途:

- FAQ
- 社内文書検索
- 規程検索
- 製品マニュアル検索

最もシンプルな構成。

---

## Pattern B: 継続作業型

```text
Agent + AgentCore Memory + Managed KB
```

用途:

- 個人業務アシスタント
- 案件管理
- 長期調査
- 会話をまたぐ業務支援

Memoryが主役。

---

## Pattern C: 知識蓄積型

```text
Agent + Memory + Managed KB + LLM Wiki
```

用途:

- コーディングエージェント
- 技術調査
- 設計知識
- 会議・意思決定
- 障害対応Playbook

Agentの経験をチーム知識に昇格させる用途に向く。

---

## Pattern D: 正式判断型

```text
Agent + Managed KB + Ontology + LLM Wiki
```

必要に応じてMemoryを追加。

用途:

- 品質保証
- 法規対応
- 契約判定
- 承認プロセス
- 設計ルール検証

「LLMがそう思った」ではなく、正式な意味・ルールで判断する必要がある領域。

---

## Pattern E: 関係探索型

```text
Agent + Managed KB / GraphRAG + Ontology + Memory
```

用途:

- 製造工程の原因探索
- サプライチェーン影響分析
- 複雑な障害調査
- 製品・部品・設備の関係探索

基本方針:

```text
GraphRAG = 発見
Ontology = 検証
```

---

# 9. ユースケース別の必要機能

凡例:

- **◎**: 必須・中心機能
- **○**: 有効
- **△**: 条件次第
- **―**: 通常不要

| ユースケース | Managed KB | Memory | LLM Wiki | Ontology | GraphRAG |
|---|:---:|:---:|:---:|:---:|:---:|
| 社内文書検索・FAQ | ◎ | △ | △ | ― | ― |
| 個人業務アシスタント | ○ | ◎ | △ | ― | ― |
| 議事録・決定事項管理 | ◎ | ◎ | ○ | △ | △ |
| コーディングエージェント | ○ | ◎ | ◎ | ― | ― |
| カスタマーサポート | ◎ | ○ | ◎ | △ | ― |
| 製造工程の原因探索 | ◎ | ◎ | ○ | ◎ | △ |
| 品質保証・監査 | ◎ | △ | ○ | ◎ | ― |
| 調査・技術動向分析 | ◎ | ○ | ◎ | △ | △ |

---

# 10. ユースケース詳細

## 10.1 社内文書検索・FAQ

### 推奨

```text
Agent
  ↓
Managed KB + Agentic Retrieval
```

KBだけで開始する。

追加条件:

- 会話をまたいで文脈を保持したい → Memory
- FAQや標準回答を人が管理したい → LLM Wiki

---

## 10.2 個人業務アシスタント

### 推奨

```text
AgentCore Runtime / Agent
       ├─ AgentCore Memory
       └─ Managed KB
```

Memory:

- 担当案件
- 前回の作業
- 未完了事項
- 出力形式
- 成功・失敗の経験

Managed KB:

- 会社資料
- 正式文書
- 規程

---

## 10.3 議事録・決定事項管理

### 推奨

```text
Teams会議・資料
       ↓
S3 / Document Source
 ├─ raw transcript
 ├─ clean transcript
 ├─ minutes
 └─ decisions
       ↓
Managed KB
       │
       ├─────────────┐
       ▼             ▼
AgentCore Memory   LLM Wiki
作業状態・経緯     承認済み決定・標準
       │             │
       └──────┬──────┘
              ▼
            Agent
```

最初からOntologyを作らず、DecisionやActionをJSONで構造化してもよい。

例:

```json
{
  "decision_id": "DEC-2026-001",
  "status": "approved",
  "owner": "team-a",
  "due_date": "2026-08-31",
  "related_project": "project-x",
  "source_uri": "s3://..."
}
```

---

## 10.4 コーディングエージェント

### 推奨

```text
Coding Agent
  ├─ GitHub / Repository Inspection
  ├─ AgentCore Memory
  ├─ LLM Wiki
  └─ Managed KB
```

分担:

```text
Memory
= 前回どこまで実装したか
= どの修正が失敗したか

LLM Wiki
= リポジトリの設計原則
= 標準ディレクトリ構成
= テスト方法
= デプロイ手順
= 重要な設計判断

Managed KB
= AWS公式資料・仕様書・社内標準
```

Wiki例:

```text
wiki/
├─ architecture/
├─ decisions/
├─ patterns/
├─ failures/
├─ playbooks/
└─ glossary/
```

通常、GraphRAGよりRepository InspectionやCode Graphの方が優先度が高い。

---

## 10.5 カスタマーサポート / ヘルプデスク

### 推奨

```text
問い合わせ
   ↓
Agent
   ├─ Managed KB
   ├─ LLM Wiki / Playbook
   ├─ AgentCore Memory
   └─ 必要に応じて Ontology / Rule
```

- KB = 製品マニュアル・契約・FAQ
- Wiki = 承認済み回答・障害対応Playbook
- Memory = 現在の対応状態・過去やり取り
- Ontology = 製品・契約・プラン・利用条件の関係

---

## 10.6 製造工程の原因探索エージェント

### 推奨

```text
                    原因探索Agent
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 AgentCore Memory    Managed KB       Ontology
 過去の探索履歴      原文・証拠        正式な関係
 仮説・試行結果      不具合報告         製品・部品
 成功・失敗          議事録・設計書     工程・設備
        │                │                │
        └────────┬───────┴────────┬───────┘
                 ▼                ▼
              LLM Wiki       構造化データ
              対策知識        時系列・センサー
              Playbook       品質・設備データ
```

導入順:

```text
Step 1
Managed KB + Memory + 構造化データ検索

Step 2
+ 薄いOntology

Step 3
+ LLM Wikiへの対策知識昇格

Step 4
Agentic Retrievalで拾えない関係探索が残る場合のみGraphRAGをA/B評価
```

この用途ではOntologyを最初から巨大化しない。

初期概念は例えば以下だけでよい。

```text
製品
部品
工程
設備
不具合
原因
対策
設計変更
```

---

## 10.7 品質保証・法規・監査

### 推奨

```text
Agent
 ├─ Managed KB
 ├─ Ontology / Rule Engine
 ├─ 承認済み LLM Wiki
 └─ Audit Log
```

この用途ではMemoryを正本にしない。

```text
Memory
= 作業の参考

Managed KBの正式文書
= 証拠

Ontology / Rule
= 判定基準

承認済みWiki
= 実務手順
```

---

## 10.8 調査・技術動向分析

### 推奨

```text
Research Agent
  ├─ Web / Managed KB
  ├─ AgentCore Memory
  └─ LLM Wiki
```

重要なサイクル:

```text
検索
 ↓
比較
 ↓
評価
 ↓
知識化
 ↓
次回は差分更新
```

LLM Wikiに以下を明示的に残す。

- 現在の推奨構成
- 過去案から変わった点
- 未解決論点
- 主要ソース
- 採用・不採用理由

---

# 11. 共通基盤と用途別機能を分ける

巨大な1つのAgentへ全部入れるのではなく、共通Platformから各Agentが必要な機能を選択する。

```text
                         共通Agent Platform
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
   Coding Agent          Meeting Agent        Cause Analysis Agent
           │                     │                     │
    Memory + Wiki          KB + Memory + Wiki    KB + Memory + Ontology
    GitHub + KB            Decision JSON          構造化データ
                                                + GraphRAG評価
```

### 共通化するもの

```text
├─ AgentCore Runtime / Gateway
├─ Managed KB
├─ AgentCore Memory基盤
├─ Knowledge Curation
├─ 認証・権限
└─ Observability
```

### 用途別に変えるもの

```text
├─ Memory Strategy
├─ Wiki構成
├─ Retrieval設定
├─ Ontology
├─ MCP Tools
└─ 評価データセット
```

---

# 12. 導入ロードマップ

## Step 1: 共通基盤

```text
AgentCore Runtime / Gateway
+ Managed KB
+ AgentCore Memory
```

まず「検索できる」「前回から続けられる」を成立させる。

## Step 2: 用途別に追加

### LLM Wiki

必要条件:

- 同じ知識を何度も再利用する
- 複数エージェント・人で共有する
- 人がレビューしたい
- Gitで履歴を管理したい

### Ontology

必要条件:

- 正式な用語定義が必要
- 関係の型を統制したい
- 業務ルールで判定したい
- LLM推論だけでは許容できない

## Step 3: GraphRAGを必要時だけ評価

評価条件:

- Agentic Retrievalで関係文書の取りこぼしが多い
- 同じ設備・部品・型番が多数の文書に散らばる
- 2〜3ホップ以上の間接関係を探索したい
- Ontologyを正式に作るほどではない
- Graph運用コストを正当化できる

---

# 13. 選定フロー

```text
Q1. 原文や正式文書を検索するか？
    Yes → Managed KB

Q2. セッションをまたいで状態や経験を保持するか？
    Yes → AgentCore Memory

Q3. 同じ調査・説明・手順を何度も再利用するか？
    Yes → LLM Wiki

Q4. 人がレビューして正式知識として管理するか？
    Yes → Knowledge Curation + LLM Wiki

Q5. 概念・関係・制約を厳密に定義するか？
    Yes → Ontology

Q6. 複数文書の間接関係の取りこぼしが問題か？
    Yes → GraphRAGを評価
```

---

# 14. 設計原則

## Principle 1: まず検索とMemoryから始める

最初からOntologyやGraphRAGを入れない。

## Principle 2: Memoryを正式知識にしない

Memoryは経験・状態・学習の保存場所。正式な標準や設計判断はWikiへ昇格する。

## Principle 3: Wikiも原文を置き換えない

Wikiは派生・整理済み知識。証拠が必要な場合はManaged KBから原文へ戻れるようにする。

## Principle 4: Ontologyは薄く始める

全社Ontologyではなく、価値が高い概念・関係だけから始める。

## Principle 5: GraphRAGは課題が見えてから使う

「GraphRAGがあるから使う」のではなく、Agentic Retrievalの評価で検索漏れが確認された場合に導入する。

## Principle 6: すべての知識に出典・状態・権威性を持たせる

最低でも以下を管理する。

```text
source_uri
created_at
updated_at
status
owner
authority
derived_from
```

---

# 15. 最終形

```text
Managed KB
= 証拠

AgentCore Memory
= 経験

LLM Wiki
= 承認された再利用知識

Ontology
= 正式な意味・関係・ルール

GraphRAG
= 関係探索を強化するオプション

AgentCore Agent
= これらを使い分けて回答・判断・実行する主体
```

そして実装上の最重要ルールは次の1行。

> **全部入りを最初から実装するのではなく、ユースケースに応じて必要な層だけ組み合わせる。**

---

# 16. 参考リンク

- Amazon Bedrock Knowledge Bases: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- Managed Knowledge Base: https://docs.aws.amazon.com/bedrock/latest/userguide/kb-build-managed.html
- Agentic Retrieval: https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-agentic-retrieve.html
- Bedrock Knowledge Bases GraphRAG: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-build-graphs.html
- Amazon Bedrock AgentCore Memory: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html
- AgentCore Episodic Memory: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/episodic-memory-strategy.html
- AWS sample Kiro LLM Wiki: https://github.com/aws-samples/sample-kiro-llm-wiki
- AWS Context Ontology Accelerator: https://github.com/aws/context-ontology-accelerator
