# Amazon Bedrock AgentCore Memory 設計ガイド

> 初学者が全体像を理解し、実装者が設計判断を行い、さらに業務エージェントへ応用するための整理資料。
>
> HTML版: [`bedrock_agentcore_memory_guide_ja.html`](./bedrock_agentcore_memory_guide_ja.html)

## 1. この資料の目的

Amazon Bedrock AgentCore Memory は、エージェントに「前回までの会話・ユーザーの好み・過去の経験・作業状態」を持たせるためのマネージドなメモリ機能です。

ただし、AgentCore Memoryを単純に「RAGの代わり」「何でも保存するデータベース」と捉えると設計を誤りやすくなります。

本資料では、次の3つを明確にします。

1. AgentCore Memoryは何を保存するためのものか
2. Bedrock Knowledge Base、業務DB、S3、ログとどう役割分担するか
3. 工程分析エージェントのような業務エージェントへどう組み込むか

---

## 2. 30秒で理解する

AgentCore Memoryの基本は次のように整理できます。

```text
ユーザー / 業務担当者
        │
        ▼
     Agent
        │
        ├───────────────┐
        │               │
        ▼               ▼
Short-term Memory   Long-term Memory
現在の会話・作業状態   過去から残す価値のある記憶
        │               │
        └───────┬───────┘
                │
                ▼
       次のAgent実行へ再利用
```

重要なのは、**Memoryは「エージェントが仕事を継続するための文脈」を保存するもの**だという点です。

一方で、正式文書や最新の業務データはKnowledge Baseや業務DBを正本にします。

```text
Memory      = 誰が、何を考え、何を試し、どこまで進んだか
Knowledge   = 正式な文書に何と書かれているか
Business DB = 現在の業務状態・数値がどうなっているか
Logs        = 実際に何が実行されたか
```

この境界を最初に決めることが最も重要です。

---

## 3. 「記憶」と「ナレッジ」は違う

AgentCore Memoryを理解する上で最初に押さえたいのが、MemoryとKnowledgeの違いです。

### Memoryに向いているもの

- ユーザーの好み
- 過去の依頼傾向
- 前回までの作業状態
- 過去に立てた仮説
- 過去に試した分析方法
- 分析結果の要約
- 過去の経験から得られた教訓
- 会話の要約

### Knowledge Baseに向いているもの

- 設計標準
- 作業標準
- FMEA
- 設備仕様書
- 品質基準
- 過去トラブル報告書
- 議事録
- 正式な社内文書

### 業務DBに向いているもの

- 生産実績
- センサーデータ
- 品質測定値
- 設備状態
- 現在の在庫
- 最新の工程条件

Memoryは正本ではありません。

```text
「前回、圧力条件を原因候補として調べた」
→ Memory

「圧力の標準設定値は0.45 MPaである」
→ Knowledge Base / 正式DB

「現在の設備圧力は0.51 MPaである」
→ 業務DB / 時系列DB
```

---

## 4. Short-term MemoryとLong-term Memory

### 4.1 Short-term Memory

Short-term Memoryは、現在進行中のセッションや会話の履歴を扱います。

代表的には次の情報です。

- 現在の会話
- 現在調査している対象
- 直前のツール実行結果
- 現在の分析条件
- 現在の仮説

工程分析エージェントなら、次のような情報です。

```text
対象工程 = Press-02
対象期間 = 2026-07-01 ～ 2026-07-31
対象品番 = ABC123
現在の仮説 = 温度上昇が不良率に影響している可能性
直前に実行した分析 = 温度 × 不良率の相関分析
```

### 4.2 Long-term Memory

Long-term Memoryは、セッションをまたいで再利用する価値がある情報を保存します。

例えば次のようなものです。

```text
ユーザーは工程別比較を先に確認する傾向がある
Press-02では過去に金型温度と不良率の関係を調査済み
設備停止直後のデータは外れ値として扱うことが多い
2026-07の分析では温度単独では原因と判断できなかった
```

Long-term Memoryによって、エージェントは毎回ゼロから仕事を始めなくて済みます。

---

## 5. AgentCore Memoryの基本単位

設計時に重要な概念は次のとおりです。

### Actor

「誰の記憶か」を識別する単位です。

```text
actor_id = user_123
```

ユーザー単位だけでなく、業務要件によってはチームやエージェント単位に設計する場合もあります。

### Session

一連の会話や作業を識別する単位です。

```text
session_id = investigation_20260807_001
```

### Event

会話やツール実行など、そのセッション内で発生した出来事です。

```text
User message
Assistant message
Tool execution
Tool result
```

### Memory Record

長期的に保存され、後のセッションで検索される記憶です。

---

## 6. Long-term Memoryの4つの組み込み戦略

現在のAgentCore Memoryでは、代表的に次の4種類の戦略を使えます。

### 6.1 Semantic Memory

ユーザーや業務に関する事実・意味情報を保存します。

```text
ユーザーはPress-02を担当している
対象製品はABCシリーズである
分析対象として設備温度をよく確認する
```

向いている用途:

- ユーザー情報
- 業務上の事実
- 継続的なコンテキスト

### 6.2 User Preference Memory

ユーザーの好みや回答スタイルを保存します。

```text
グラフは日別よりロット別を好む
分析結果は原因候補を先に提示してほしい
SQLよりPythonコードを好む
```

向いている用途:

- UI/UXの個人最適化
- 回答形式
- 分析スタイル

### 6.3 Session Summary Memory

過去のセッションを要約して保存します。

```text
2026-07-31の分析:
Press-02の不良率増加を調査。
温度・圧力・停止時間を比較したが、温度単独では説明できず。
次回は材料ロットとの組み合わせを確認する予定。
```

向いている用途:

- 前回の続き
- 長い会話の圧縮
- 調査・分析の引き継ぎ

### 6.4 Episodic Memory

過去の経験やエピソードから、再利用できる教訓や行動パターンを保存します。

```text
設備異常の原因分析では、
単一特徴量の相関だけで判断すると誤判定しやすかった。
停止イベント前後の時系列分割が有効だった。
```

向いている用途:

- 過去の成功・失敗の再利用
- エージェントの経験学習
- トラブルシューティング
- 分析手順の改善

---

## 7. Memory Strategyの選び方

最初から全戦略を有効にする必要はありません。

### 初期PoC

```text
Session Summary
+ Semantic Memory
```

この2つから始めるのがおすすめです。

理由は、

- 前回の続きを実現しやすい
- 価値を説明しやすい
- 保存内容を人間が確認しやすい

ためです。

### ユーザー個別最適化を行う場合

```text
+ User Preference
```

### 過去の分析経験を再利用したい場合

```text
+ Episodic Memory
```

工程分析エージェントでは、最終的には次の組み合わせが有力です。

```text
Semantic        : 工程・設備・分析対象に関する継続情報
User Preference : 分析者の好み
Session Summary : 調査の続き
Episodic        : 過去分析の教訓
```

---

## 8. AgentCore Memoryは自動でプロンプトへ入るわけではない

重要な設計ポイントです。

Memoryへ保存しただけでは、次回のAgentが自動的にすべての記憶を利用するわけではありません。

基本的な流れは次のようになります。

```text
User Request
    │
    ▼
Intent / Context判断
    │
    ▼
Memory Retrieval
    │
    ├─ Semantic
    ├─ Preference
    ├─ Summary
    └─ Episodic
    │
    ▼
必要なMemoryだけ選択
    │
    ▼
Prompt / Contextへ注入
    │
    ▼
Agent Reasoning
```

つまり、**Memory Retrieval自体もエージェント設計の一部**です。

---

## 9. Context Hydrationという考え方

業務エージェントでは、ユーザーの質問を受けた直後に必要なコンテキストをまとめて取得する設計が有効です。

```text
User Query
   │
   ▼
Context Hydration
   │
   ├─ AgentCore Memory
   │    ├─ 前回の調査
   │    ├─ ユーザー設定
   │    └─ 過去の経験
   │
   ├─ Managed Knowledge Base
   │    └─ 正式文書
   │
   ├─ Business DB
   │    └─ 最新データ
   │
   └─ Graph / Ontology
        └─ 関係性
   │
   ▼
Unified Context
   │
   ▼
Agent
```

この方式ならMemoryだけに責任を持たせず、複数の情報源を適切に使い分けられます。

---

## 10. Namespace設計

Long-term Memoryを本番で使う場合、Namespace設計は非常に重要です。

Namespaceは「どの記憶空間に保存するか」を整理するために使います。

例えば次のような構造です。

```text
/user/{user_id}/semantic
/user/{user_id}/preferences
/user/{user_id}/summary

/project/{project_id}/episodes

/process/{process_id}/analysis
```

ただし、Namespaceへ情報を詰め込みすぎると設計が複雑になります。

基本原則は、

```text
Namespace = 大きな隔離境界
Metadata  = その中の絞り込み
```

です。

---

## 11. Metadata設計

業務エージェントでは、Memory RecordにMetadataを付与すると検索精度が大きく改善します。

工程分析なら次のようなMetadataが考えられます。

```json
{
  "plant": "plant_a",
  "line": "line_01",
  "process": "press",
  "equipment": "press_02",
  "product": "abc123",
  "analysis_type": "quality_issue",
  "status": "completed"
}
```

検索時は、

```text
1. Namespaceで大きく絞る
2. Metadataで業務条件を絞る
3. Semantic Searchで意味的に近いMemoryを探す
```

という順番が扱いやすいです。

---

## 12. Memory / Knowledge Base / DB / Graphの役割分担

工程分析エージェントでは、次の構成が分かりやすいです。

```text
                    Consumer Agent
                          │
                          ▼
                  Context Hydration
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
AgentCore Memory     Managed KB          Business DB
      │                   │                   │
      │                   │                   │
過去の分析             正式文書              最新データ
ユーザー設定           FMEA                  センサー
仮説                   標準書                品質実績
経験                   議事録                工程条件
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                          ▼
                 Graph / Thin Ontology
                          │
                          ▼
              工程・設備・品質の関係探索
```

### Memory

「前に何をしたか」を扱う。

### Managed Knowledge Base

「正式資料に何と書かれているか」を扱う。

### Business DB

「今どうなっているか」を扱う。

### Graph / Thin Ontology

「何と何が関係しているか」を扱う。

この4つを分離すると、責務が明確になります。

---

## 13. 工程分析エージェントへの適用

### 13.1 典型的な分析

ユーザー:

```text
Press-02の不良率が昨日から上がっている原因を調べて
```

AgentはまずMemoryから過去の文脈を取得します。

```text
過去にPress-02で温度を調査済み
温度単独では説明できなかった
次回は材料ロットを見る予定だった
```

次にKnowledge Baseから関連する正式知識を取得します。

```text
FMEA
設備仕様
品質基準
過去トラブル報告
```

さらに業務DBから最新データを取得します。

```text
温度
圧力
材料ロット
停止履歴
不良率
```

これによってAgentは、単にRAG検索するのではなく、

```text
過去の調査
+ 正式知識
+ 現在データ
```

を組み合わせて分析できます。

### 13.2 分析後にMemoryへ残すもの

分析結果をすべてMemoryへコピーする必要はありません。

残す価値があるものだけを要約して保存します。

```text
Issue:
Press-02で2026-08-07に不良率上昇。

Finding:
材料ロット切替後に増加。
温度・圧力では説明できなかった。

Action:
材料Lot X23の成分差を確認。

Lesson:
Press-02では設備条件だけでなく材料ロットを早期確認する。
```

これが次回の分析でEpisodic Memoryとして役立ちます。

---

## 14. 「薄いオントロジー」とMemoryの組み合わせ

工程分析では、最初から巨大な正式オントロジーを作る必要はありません。

次のような最低限の関係だけを定義します。

```text
Plant
 └─ Line
     └─ Process
         └─ Equipment

Product
 └─ Process

Equipment
 ├─ Sensor
 ├─ Parameter
 └─ FailureMode

FailureMode
 ├─ Cause
 └─ QualityIssue
```

AgentCore Memoryは、その構造の中で「過去にどこを調べたか」「何が有効だったか」を保持します。

つまり、

```text
Thin Ontology = 世界の構造
Memory        = その世界でAgentが経験したこと
KB            = 正式な知識
DB            = 現在の事実
```

という分担ができます。

---

## 15. 最小実装イメージ

概念的な実装フローは次のとおりです。

```python
# 1. セッション中のイベントをMemoryへ保存
save_event(
    actor_id=user_id,
    session_id=session_id,
    messages=conversation
)

# 2. 次回の質問時に関連Memoryを検索
memories = retrieve_memory(
    actor_id=user_id,
    query=user_query,
    namespace="/user/{user_id}/analysis"
)

# 3. Knowledge Baseから正式知識を取得
knowledge = retrieve_knowledge(user_query)

# 4. DBから最新情報を取得
current_data = query_business_data(user_query)

# 5. Contextを統合
context = build_context(
    memories=memories,
    knowledge=knowledge,
    current_data=current_data
)

# 6. Agentへ渡す
answer = agent.run(user_query, context=context)
```

本番では、Memoryを毎回全部取得するのではなく、Intentやタスク種類に応じて検索するMemoryを変えることが重要です。

---

## 16. PoCの進め方

AgentCore Memoryは、小さく導入する方が成功しやすいです。

### Level 1: Session Memory

まずは前回の続きを実現します。

```text
Session Summary
```

評価:

- 前回説明した内容を再説明しなくて済むか
- トークン量が減るか
- 引き継ぎ精度が上がるか

### Level 2: Semantic Memory

継続的なユーザー・業務情報を記憶します。

評価:

- 毎回指定していた条件を省略できるか
- 誤った古い情報を使わないか

### Level 3: Preference Memory

ユーザー別の回答・分析スタイルを最適化します。

### Level 4: Episodic Memory

過去の分析経験を再利用します。

```text
過去の原因分析
↓
成功/失敗
↓
Lesson抽出
↓
次回の分析計画へ利用
```

工程分析エージェントとして本当に価値が出るのは、このLevel 4です。

---

## 17. 評価設計

「Memoryを入れたら便利そう」で終わらせず、評価指標を持つことが重要です。

### Extraction

必要な情報が正しくMemory化されたか。

```text
Precision
Recall
不要なMemory率
```

### Consolidation

同じ情報が重複していないか。

```text
重複率
矛盾率
更新成功率
```

### Retrieval

必要なMemoryを検索できたか。

```text
Recall@K
Precision@K
MRR
```

### Task Impact

Memoryによって業務成果が改善したか。

```text
分析時間
再説明回数
ツール実行回数
原因候補到達時間
ユーザー修正回数
最終回答精度
```

業務エージェントでは、最終的にはRetrieval精度より**Task Impact**を見るべきです。

---

## 18. 本番運用で重要なポイント

### 18.1 Memoryを正本にしない

重要な業務判断は必ず正式DBやKnowledge Baseで再確認します。

### 18.2 Memoryは時間とともに古くなる

ユーザー設定、担当設備、工程条件などは変化します。

古いMemoryをどう更新・削除するかが必要です。

### 18.3 個人Memoryと共有Memoryを分ける

```text
/user/{user_id}/...
/team/{team_id}/...
/project/{project_id}/...
```

を混在させない方が安全です。

### 18.4 何をMemoryへ保存したか観測する

最低限、次を追跡します。

```text
Event
↓
Memory Extraction
↓
Stored Memory
↓
Retrieved Memory
↓
Prompt Injection
↓
Agent Answer
```

### 18.5 削除・訂正経路を用意する

エージェントが誤ったMemoryを作る可能性があります。

管理UIや運用ツールから、

```text
閲覧
訂正
無効化
削除
```

できる設計が必要です。

---

## 19. よくある失敗

### 失敗1: 何でもMemoryへ保存する

結果として検索ノイズが増えます。

**保存する価値がある情報だけを残す**ことが重要です。

### 失敗2: Knowledge Baseの代わりに使う

Memoryは正本ではありません。

### 失敗3: Memoryを毎回大量にPromptへ入れる

Context Windowを圧迫します。

RetrievalとRankingが必要です。

### 失敗4: Namespaceを細かく作りすぎる

運用が複雑になります。

Namespaceは隔離、Metadataは絞り込み、と役割を分けます。

### 失敗5: 評価せずに「賢くなった」と判断する

MemoryなしのBaselineと比較します。

---

## 20. 推奨アーキテクチャ

工程分析エージェントを想定した完成形は次のイメージです。

```text
                 User / Copilot / ChatGPT
                           │
                           ▼
                AgentCore Runtime / Agent
                Router / Planning / Tools
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
 AgentCore Memory     Managed KB      Business Data
          │                │                │
          │                ▼                │
          │                S3               │
          │                                 │
          └────────────┬────────────────────┘
                       │
                       ▼
               Thin Ontology / Graph
                       │
                       ▼
                 Analysis Tools
              Python / SQL / ML / BI
```

Memoryはこの構成の中心ではありますが、すべてをMemoryへ集約しないことが重要です。

---

## 21. 推奨する導入順序

```text
Step 1
AgentCore Runtime
+ Short-term Memory

Step 2
+ Session Summary

Step 3
+ Semantic Memory

Step 4
+ Managed Knowledge Base

Step 5
+ Business DB / Tools

Step 6
+ Episodic Memory

Step 7
+ Thin Ontology / Graph

Step 8
Evaluation / Observability / Governance
```

工程分析エージェントで最初から全部作る必要はありません。

特に、

```text
Session Summary
+ Managed KB
+ Business DB
```

まででかなり実用的なPoCができます。

その後、過去分析を蓄積したくなった段階でEpisodic Memoryを追加するのが現実的です。

---

## 22. この設計での重要原則

最も重要なポイントを5つに絞ると次のとおりです。

1. **Memoryはナレッジベースではない**
2. **正式情報はKB・DBを正本にする**
3. **Memoryは仕事の継続性と経験を持たせるために使う**
4. **Namespace・Metadata・Retrieval設計が品質を決める**
5. **最終評価はMemory検索精度ではなく、業務タスクが改善したかで行う**

工程分析エージェントでは、次の一文で整理できます。

> **Knowledge Baseが「会社の知識」、業務DBが「現在の事実」、薄いオントロジーが「世界の構造」、AgentCore Memoryが「エージェントの経験」を担当する。**

---

## 23. 参考資料

AWS公式資料を中心に、次の順番で読むと理解しやすいです。

1. Amazon Bedrock AgentCore Memory: Building context-aware agents  
   https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/

2. Amazon Bedrock AgentCore Memory Developer Guide  
   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html

3. Get started with AgentCore Memory  
   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-get-started.html

4. awslabs/agentcore-samples  
   https://github.com/awslabs/agentcore-samples

5. Building smarter AI agents: AgentCore long-term memory deep dive  
   https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/

6. Organizing agents' memory at scale: Namespace design patterns  
   https://aws.amazon.com/blogs/machine-learning/organizing-agents-memory-at-scale-namespace-design-patterns-in-agentcore-memory/

7. Long-term Memory Metadata  
   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-memory-metadata.html

8. Long-term Memory and RAG  
   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-ltm-rag.html

---

## 24. ファイル構成

```text
bedrock-agentcore-memory-guide/
├── README.md
└── bedrock_agentcore_memory_guide_ja.html
```

- `README.md`: 設計思想・実装方針をMarkdownで参照するための資料
- `bedrock_agentcore_memory_guide_ja.html`: 初学者から応用者までブラウザで読みやすい説明資料
