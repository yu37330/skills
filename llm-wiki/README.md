# LLM Wiki — RAGとの違い、成熟度Level、AWSでの実装方針

> 最終確認: 2026-08-07
>
> このドキュメントは、LLM Wikiを「RAGの代替製品」ではなく、**LLM/Agentが継続的に編集するKnowledge Modeling / Knowledge Compilationのパターン**として整理する。

## 1. 結論

LLM Wikiの本質は、質問時に原文チャンクを検索して毎回その場で意味を組み立てるのではなく、**事前にLLM/Agentが原文を読み、意味単位のMarkdownページへ整理し、ページ間の関係をリンクとして蓄積・更新すること**にある。

```text
Traditional RAG
Raw Documents
    ↓
Chunk / Embed
    ↓
Vector / Hybrid Retrieval
    ↓
LLMが質問時に意味を再構成

LLM Wiki
Raw Documents
    ↓
Harvest / Knowledge Acquisition Agent
    ↓
意味単位のWikiページへ編集
    ↓
Markdown + Metadata + Links
    ↓
検索 / 関係探索
    ↓
LLMが整理済み知識を利用
```

重要なのは、LLM WikiとRAGは排他的ではないこと。

- **LLM Wiki = Knowledgeをどう整理・維持するか**
- **Managed KB / Vector Search = 整理済みKnowledgeをどう探すか**
- **Link / Backlink = 明示的な関係をどうたどるか**
- **GraphRAG = より複雑な関係推論をどう行うか**

今回のAWS構成では、**OKF Markdownを正本にして、検索をAmazon Bedrock Managed Knowledge Baseへ任せる**のが有力。

---

## 2. RAGとLLM Wikiの違い

| 観点 | Traditional RAG | LLM Wiki |
|---|---|---|
| Knowledgeの正本 | 原文ドキュメント | 原文 + 整理済みWiki |
| 主な単位 | Chunk | Concept / Meeting / Decision / Actionなど意味単位のページ |
| 整理タイミング | Query時 | Ingest / Harvest時 |
| 関係 | Metadataや類似度中心 | Wiki Linkで明示的に保持 |
| 継続更新 | 原文再Index | 既存Wikiとの照合、追記、統合、更新 |
| 人が読む | 原文中心 | Wiki自体を直接読める |
| Agentが読む | Retriever経由のChunk | Wikiページ + Search + Link traversal |
| 出典 | Chunkのsource metadata | Wikiページから原文へのprovenanceを保持 |
| 強み | 原文検索、Evidence retrieval | 意思決定、概念、背景、関係、知識の継続蓄積 |

### 「議事録をManaged KBに入れるだけ」との違い

普通の議事録RAGは次の形になる。

```text
meeting-2026-08-01.md
meeting-2026-08-07.md
meeting-2026-08-14.md
        ↓
Managed KB
```

LLM WikiではHarvest時に再編集する。

```text
raw meeting
    ↓
Harvest
    ↓
meeting/
  2026-08-07-architecture.md

decision/
  adopt-managed-kb.md

action/
  build-meeting-wiki-poc.md

topic/
  knowledge-platform.md

concept/
  agentcore-runtime.md
```

この「何を1ページにするか」「既存ページへ統合するか」「どこへLinkを張るか」がLLM Wikiの価値になる。

---

## 3. OKFをKnowledgeの正本にする

Open Knowledge Format (OKF) v0.2は、Knowledgeを次の非常に単純な形式で表す。

```text
Markdown
+
YAML frontmatter
+
standard Markdown links
```

例:

```markdown
---
type: Decision
title: Managed KBを検索基盤として採用
status: active
sources:
  - resource: /meetings/2026-08-07-architecture.md
---

# Managed KBを検索基盤として採用

## Decision
議事録LLM Wikiの検索レイヤーにAmazon Bedrock Managed Knowledge Baseを採用する。

## Rationale
- Vector Storeの運用を持たない
- Hybrid Searchを利用する
- Agentic Retrievalを利用する

## Related
- [2026-08-07 アーキテクチャ会議](/meetings/2026-08-07-architecture.md)
- [議事録Wiki PoC](/topics/meeting-wiki-poc.md)
- [AgentCore Gateway](/concepts/agentcore-gateway.md)
```

OKFではConcept間のMarkdown Linkが関係を表す。OKF v0.2の標準Linkは**untyped edge**であり、`depends_on`や`supersedes`のようなRelation Typeは標準必須仕様ではない。Typed RelationはLevel 3での拡張として扱う。

---

# 4. LLM WikiのLevel

## Level 1 — Markdown Wiki

### 構成

```text
Markdown
+
YAML metadata
+
Wiki / Markdown Links
```

### できること

- LLMが原文から意味単位のKnowledge Pageを生成
- Entity / Concept / Decisionなどでページを分離
- ページ間をLink
- Gitでdiff / review / rollback
- Obsidian、Logseq、MkDocsなどで人も閲覧
- Agentが`read_page` / `grep`などで直接読む

### 得意な質問

- この概念は何か
- このDecisionの内容は何か
- この会議で何が決まったか
- 関連ページは何か

### 代表例

- `aws-samples/sample-kiro-llm-wiki`
- Open Knowledge Format (OKF)
- Obsidian / Logseqは閲覧・編集UIとして利用可能

### 位置づけ

小規模PoCならLevel 1だけでも成立する。ただし、ページ数が増えると「どのページを最初に読むか」が課題になる。

---

## Level 2 — Searchable / Navigable LLM Wiki

### 構成

```text
Level 1
+
Backlinks
+
Link Graph / Graph View
+
Semantic / Vector / Hybrid Search
```

### できること

Level 1に加えて次が可能になる。

- 質問からSemantic Searchで入口となるWikiページを発見
- そのページのLinks / Backlinksから周辺Knowledgeを取得
- 1〜2 hop程度の関連Knowledge探索
- Graph ViewでKnowledge全体を俯瞰
- 検索で見つけたページと、明示的にLinkされたページを組み合わせて回答

### 典型的なRetrieval

```text
User Question
    ↓
Semantic / Hybrid Search
    ↓
Seed Wiki Pages
    ↓
read_page
    ↓
Links / Backlinks
    ↓
Related Wiki Pages
    ↓
Grounded Answer
```

### 得意な質問

- Managed KB採用までの経緯は？
- このDecisionに関係する過去会議は？
- このTopicに関連するDecisionとActionは？
- このConceptを参照しているページは？

### 代表例

#### AWS `sample-okf-llm-wiki`

現在のサンプルは以下を持つ。

- OKF Markdown on S3
- NetworkXによるLink / Backlink Graph
- `get_backlinks`
- S3 Vectorsによる`semantic_search`
- AgentCore Runtime上のHarvest Agent
- AgentCore Runtime上のConsumption MCP
- React UIのLink Graph

#### `nashsu/llm_wiki`

- Markdown / wikilinks
- Knowledge Graph
- LanceDB Vector Semantic Search
- Graph Expansion
- Community Detection

### 今回の推奨Level

**議事録LLM WikiはLevel 2を初期完成形とする。**

ただしSemantic Searchを自前S3 Vectorsで維持するのではなく、最新の**Amazon Bedrock Managed Knowledge Base**へ置き換える / 併用する。

---

## Level 3 — Typed Knowledge Graph / GraphRAG

### 構成

```text
Level 2
+
Typed Relations
+
Graph Index / Graph DB
+
Graph Query / GraphRAG
```

例:

```text
Meeting
  ─DECIDED→ Decision

Decision
  ─SUPERSEDES→ Decision

Decision
  ─CREATES→ Action

Action
  ─OWNED_BY→ Team

Decision
  ─AFFECTS→ Project
```

### できること

- Relation Typeを指定した確定的探索
- N-hop relation traversal
- shortest path
- 関係条件を含むQuery
- GraphRAGによる複数関係の推論
- Ontology / Property Graphとの統合

### 得意な質問

- このDecisionに置き換えられた旧Decisionをすべて出して
- Project Aに影響し、かつRisk BにつながるDecisionは？
- Person X → Decision → Project → Riskの経路を示して

### 実装候補

- OKFに独自Typed Relation metadataを追加
- Amazon Neptune / Neo4jなどへ派生Graphを構築
- LlamaIndex Property Graph / LightRAG / Microsoft GraphRAGなどのGraph技術を必要に応じて利用

### 注意

Level 3はOKFコア仕様の必須要件ではない。**最初からLevel 3へ行かず、Level 2で不足する関係Queryが明確になった段階で追加する。**

---

# 5. Level別に何が変わるか

| Capability | L1 | L2 | L3 |
|---|:---:|:---:|:---:|
| Markdown Knowledge Page | ✅ | ✅ | ✅ |
| YAML Metadata | ✅ | ✅ | ✅ |
| Wiki / Markdown Link | ✅ | ✅ | ✅ |
| Provenance / Source | ✅ | ✅ | ✅ |
| Backlink | △ | ✅ | ✅ |
| Graph View | △ | ✅ | ✅ |
| Semantic / Vector Search | ❌ | ✅ | ✅ |
| Hybrid Retrieval | ❌ | ✅ | ✅ |
| Link traversal | 手動/Agent | ✅ | ✅ |
| Typed Relation | ❌ | ❌/任意 | ✅ |
| Graph DB | ❌ | ❌ | ✅ |
| Graph Query | ❌ | 限定的 | ✅ |
| GraphRAG | ❌ | ❌ | ✅ |
| 運用複雑度 | Low | Medium | High |

---

# 6. 議事録WikiでのKnowledge Model

初期Schemaは次を推奨する。

```text
meeting
  会議そのもの

decision
  決定事項。後から参照したいKnowledgeの中心。

action
  実行事項、Owner、Due、Status

topic
  会議をまたぐ継続テーマ

risk
  リスク、懸念、Blocker

concept
  技術、製品、方式、社内用語

entity
  Project / Team / Systemなど
```

### Linkルール

```text
meeting → decision
meeting → action
meeting → topic

decision → source meeting
decision → topic
decision → related concept

action → source meeting
action → related decision

topic → related decisions
```

Level 2ではLinkのTypeを厳密なOntologyとして定義しなくてもよい。

---

# 7. Harvest Agentが重要な理由

LLM Wikiの品質は検索エンジンよりも**Harvest時の編集ルール**に強く依存する。

Harvest Agentには最低限、次のルールを持たせる。

1. 新規議事録を読む
2. 既存のDecision / Topic / Conceptを検索する
3. 同じKnowledgeの新規ページを乱造しない
4. 既存ページへ追記・統合できる場合は更新する
5. Decision変更時は旧Decisionを消さず、履歴とSourceを保持する
6. 原文Meetingへのprovenanceを必須にする
7. Link切れを検査する
8. frontmatter / schemaを検査する
9. Review後にpublished Wikiへ反映する

これは通常のRAGの「chunking」より一段上で、**AgentによるSemantic Knowledge Compilation**と考えると分かりやすい。

---

# 8. Managed Knowledge Baseとの組み合わせ

Amazon Bedrock Managed Knowledge Baseは2026-06-17にGAしたFully Managed RAGで、現在は以下をサービス側で管理できる。

- Data ingestion
- Managed vector storage
- Embedding
- Hybrid search
- Managed reranking
- Agentic Retrieval
- Multi-modal parsing
- AgentCore Gateway native integration

Managed KBはS3をData Sourceとして利用できるため、Harvestが生成した`published/`配下のOKF Markdownをそのまま取り込む。

```text
                 Harvest Agent
                      ↓
                 OKF Markdown
                 S3 published/
                      ↓
          ┌───────────┴───────────┐
          ↓                       ↓
   Link / Backlink          Managed KB
          ↓                       ↓
     Wiki Tools             Managed Retrieval
          └───────────┬───────────┘
                      ↓
               AgentCore Gateway
                    MCP
                      ↓
               Consumer Agent
```

### 役割分担

```text
Managed KB
  「内容・意味から何を読むべきか」を探す

Link / Backlink
  「そのページと明示的につながるKnowledge」をたどる

OKF Markdown
  Knowledgeそのものの正本
```

Managed KBを正本にはしない。IndexやManaged Retrievalは再構築可能な**派生検索レイヤー**として扱う。

### Gateway

Managed KBはAgentCore Gatewayのnative connector targetとして公開でき、次のMCP toolsを提供する。

- `Retrieve` — single hybrid search
- `AgenticRetrieveStream` — query planning + iterative retrieval + reranking + optional citation-backed synthesis

またAgentCore Gatewayは既存MCP Serverをtargetとして集約できるため、Wiki ToolsとManaged KB Toolsを1つのGateway MCP URLへまとめられる。

---

# 9. なぜManaged KBだけではなくWikiを作るのか

Managed KBだけでも高性能なRAGは構築できる。しかし、それだけでは次が曖昧になりやすい。

- 何をKnowledge Unitとするか
- DecisionとMeetingを分けるか
- 過去Decisionと最新Decisionをどう扱うか
- 会議をまたぐTopicをどう育てるか
- 明示的なLinkをどこへ張るか
- Source / Provenanceをどこまで保持するか
- 人が直接読めるKnowledge Corpusをどう維持するか

したがって、今回の設計は次の分担とする。

```text
LLM Wiki / OKF
  = Knowledge Modeling

Harvest Agent
  = Knowledge Compilation / Maintenance

Managed KB
  = Managed Retrieval

Link / Backlink
  = Explicit Relationship Navigation

Consumer Agent
  = Reasoning / Answering
```

---

# 10. 推奨ロードマップ

## Phase 1 — Meeting LLM Wiki / Level 1

- OKF Markdown
- meeting / decision / action / topic / risk / concept / entity
- Harvest Agent
- Source / provenance
- Link validation

## Phase 2 — Level 2（初期完成形）

- Link / Backlink Index
- Graph View
- Managed Knowledge Base
- Hybrid Retrieval
- Agentic Retrieval
- AgentCore Gateway
- Wiki Tools + Managed KB Tools

## Phase 3 — Evaluation

- Traditional RAGとの回答品質比較
- Managed KB `Retrieve` vs `AgenticRetrieveStream`
- Link expansion有無の比較
- Decision / Action抽出品質
- Source citation coverage
- Duplicate Knowledge率

## Phase 4 — Level 3は必要時のみ

- Typed Relation
- Graph DB
- GraphRAG
- Process Wikiとの接続

---

# 11. 参考実装

### AWS

- sample-okf-llm-wiki  
  https://github.com/aws-samples/sample-okf-llm-wiki
- sample-kiro-llm-wiki  
  https://github.com/aws-samples/sample-kiro-llm-wiki
- sample-knowledge-acquisition-skill  
  https://github.com/aws-samples/sample-knowledge-acquisition-skill

### Format

- Open Knowledge Format (OKF)  
  https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf

### LLM Wiki OSS

- nashsu/llm_wiki  
  https://github.com/nashsu/llm_wiki

### Wiki UIの参考

- Logseq (OSS)  
  https://github.com/logseq/logseq
- Obsidian（Markdown Wikiとして有名。OSSではない）  
  https://obsidian.md/

### AWS Managed Knowledge Base

- GA announcement (2026-06-17)  
  https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-bedrock-managed-knowledge-base/
- Managed vs Customer-managed KB  
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-build-managed.html
- AgentCore Gateway Managed KB connector  
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connector-managed-kb.html

---

# 12. 現時点の推奨

今回の議事録用途は、**Level 2を狙う**。

```text
Fargate
  UI / existing authentication
        ↓
AgentCore Runtime
  Meeting Harvest Agent
        ↓
OKF Markdown on S3
        ↓
┌─────────────────┬────────────────────┐
│                 │                    │
Link / Backlink   Managed Knowledge Base
│                 │
Wiki Tools        Retrieve / AgenticRetrieveStream
│                 │
└────────┬────────┘
         ↓
 AgentCore Gateway
         ↓
 Consumer Agent
```

**KnowledgeをWikiとして作る部分を自前で持ち、Retrievalの重い部分をAWS Managed Serviceへ任せる**のがポイント。
