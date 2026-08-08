# OpenWiki Brains Writer Integration — AWS OKF Data Wikiへの追加Writer方針

> Decision: 2026-08-08
>
> Base Platform: `aws-samples/sample-okf-llm-wiki`
>
> Additional Writer: `langchain-ai/openwiki` Personal mode / OpenWiki Brains
>
> Canonical Knowledge Format: **Open Knowledge Format (OKF) v0.2**

## 1. 結論

AWS Samplesの`sample-okf-llm-wiki`をKnowledge Platformのベースとして維持し、**OpenWiki Brainsを追加のWiki Writerとして組み込む**。

AWS Harvest AgentをOpenWiki Brainsへ完全置換しない。

```text
                         Writer Layer

              ┌──────────────────────────────┐
              │                              │
              ▼                              ▼
      OpenWiki Brains                 AWS Harvest Agent
      Meeting / Project               Data / Process
      Knowledge Writer                Knowledge Writer
              │                              │
              └──────────────┬───────────────┘
                             ▼
                       OKF Adapter
                             ▼
                    Canonical OKF v0.2
                             ▼
                            S3
                  Knowledge Source of Truth
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
      Link / Backlink     S3 Vectors       History
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                         Common MCP
                             ▼
                         Common UI
                             ▼
                       Consumer Agent
```

設計原則は次の一文に集約する。

> **OKFを共通契約にし、Writerはプラガブルにする。**

## 2. Writerの役割分担

### OpenWiki Brains

主に非構造化・業務ナレッジを扱う。

```text
Meeting Minutes
Project Documents
Design Notes
Reports
Issues
Future Connectors
      ↓
OpenWiki Brains
      ↓
Living Project Knowledge Wiki
```

特に議事録では、会議ファイルを単純に保存するのではなく、複数会議をまたいで以下のKnowledgeを継続更新することを狙う。

- Project
- Topic
- Decision
- Requirement
- Action
- Risk
- Issue
- Artifact
- Meeting

評価ポイントは、**新規ページ生成数ではなく、既存Knowledgeを適切にUPDATE / REINFORCEできるか**とする。

### AWS Harvest Agent

主に構造化データ・工程データの理解を担当する。

```text
Glue / Redshift
      ↓
Metadata
      ↓
Athena sample_rows / run_sql
      ↓
Grain / Join / Metric / Gotcha Verification
      ↓
AWS Harvest Agent
      ↓
Data / Process Knowledge Wiki
```

AWS Harvest Agentは単なるMarkdown Generatorではなく、実データを確認しながらData Knowledgeを検証できることが強みである。

そのため、工程分析用途では当面維持する。

## 3. なぜ完全置換しないか

OpenWiki BrainsとAWS Harvest Agentは得意領域が異なる。

| 項目 | OpenWiki Brains | AWS Harvest Agent |
|---|---|---|
| 議事録・一般文書 | ◎ | △ |
| 継続的なWiki Maintenance | ◎ | ○ |
| Markdown Link生成 | ◎ | ○ |
| OKF出力 | ○ | ○ |
| Glue Metadata理解 | △ | ◎ |
| Athena実データ検証 | △ | ◎ |
| Grain / Join検証 | △ | ◎ |
| S3 Vectors連携 | Platform側で利用 | ◎ |
| MCP / UI | Platform側を利用 | ◎ |

AWS HarvestをOpenWikiへ完全置換すると、現時点では以下の能力を再実装する必要がある。

```text
Glue discovery
Athena run_sql
sample_rows
Grain verification
Join verification
Reviewer
Incremental Harvest
Harvest state management
```

そのため、**Writer追加方式の方が小さな改修で双方の長所を利用できる**。

## 4. AWSサンプルをKnowledge Platformとして再定義する

AWS Samplesを「Data Wiki専用アプリ」ではなく、次の共通基盤として扱う。

```text
OKF Storage Platform
+ Semantic Index
+ Wiki Navigation
+ MCP
+ UI
```

Keepする機能:

- S3 OKF Bundle
- S3 Versioning
- Link / Backlink
- Graph View
- S3 Vectors
- Semantic Search
- Reindex Pipeline
- Wiki MCP
- Control API
- React UI
- History / Diff
- AgentCore integration
- CloudWatch / OTEL

Writerが何であるかを、S3以降のConsumer Layerから分離する。

## 5. OpenWiki Brainsの配置

OpenWiki Brainsは**Wiki Authoring Engine**として扱う。

```text
Raw Meeting Sources
       ↓
OpenWiki Brains
       ↓
Local OKF Working Copy
       ↓
OKF Normalizer / Adapter
       ↓
S3 OKF Bundle
```

OpenWiki標準のlocal filesystem前提は維持し、S3をSource of Truthにする。

Fargateの場合:

```text
S3
├─ meeting-raw/
└─ meeting-wiki/
       │
       ▼
ECS Fargate Task
       │
       ├─ S3 meeting-raw → local workspace
       ├─ S3 meeting-wiki → local workspace
       │
       ├─ OpenWiki Brains update
       │
       └─ local wiki → S3 meeting-wiki
       │
       ▼
Task終了
```

Fargate local filesystemは一時Workspaceであり、永続Storageとして扱わない。

```text
S3              = Source of Truth
Fargate local   = Working Copy / Cache
OpenWiki Brains = Wiki Authoring Engine
```

## 6. PoCのS3同期方式

最初のPoCでは専用S3 Connectorを実装せず、`aws s3 sync`を利用する。

概念:

```bash
# 1. Raw Source取得
aws s3 sync s3://knowledge/meeting-raw/ /work/meetings/

# 2. 前回Wiki取得
aws s3 sync s3://knowledge/meeting-wiki/ /work/wiki/

# 3. OpenWiki Brainsで更新
openwiki personal --update

# 4. 更新WikiをPublish
aws s3 sync /work/wiki/ s3://knowledge/meeting-wiki/ --delete
```

データ量が増えた段階で、差分同期または専用S3 Connectorへ移行する。

## 7. OKF Version Boundary

Writer実装のバージョンと、Platformが採用するOKF Versionを分離する。

現時点ではOpenWikiが出力するOKF versionと、社内Canonical Formatが一致しない可能性があるため、WriterとS3の間にNormalizerを置く。

```text
OpenWiki Brains
      ↓
OpenWiki Native OKF
      ↓
OpenWiki Adapter
      ↓
OKF v0.2 Normalizer
      ↓
Canonical OKF v0.2
      ↓
S3
```

将来OpenWikiがOKF v0.2以降へ正式対応した場合は、Adapter / Normalizerのみを更新する。

S3以降の以下は原則変更しない。

```text
S3
S3 Vectors
Link / Backlink
MCP
UI
Consumer Agent
```

## 8. WikiEngine Interface

Writerを交換可能にするため、薄いInterfaceを設ける。

```python
class WikiEngine:
    def initialize(self, source_path: str, wiki_path: str):
        ...

    def update(self, source_path: str, wiki_path: str):
        ...

    def validate(self, wiki_path: str):
        ...
```

実装例:

```text
WikiEngine
├─ OpenWikiBrainEngine
└─ AwsDataWikiEngine
```

Writer固有ロジックをPlatformへ漏らさない。

## 9. Common UI

UIはWriter別に新規作成せず、AWS SampleのOKF Viewerを共通化する。

```text
Knowledge Portal

[ Meeting / Project Wiki ]
        ↓
OpenWiki Brains Writer

[ Engineering Data Wiki ]
        ↓
AWS Harvest Writer

        ↓ 共通

Browse
Graph
Backlink
Search
History
Diff
```

共通化しやすい機能:

- Markdown Viewer
- Concept Tree
- Link
- Backlink
- Graph
- History
- Diff
- Semantic Search

Writer固有画面:

### OpenWiki Brains

- Meeting Upload / Source Sync
- Update Brain
- Writer Status

### AWS Harvest

- Glue / Dataset selection
- Harvest
- Athena/Data source configuration
- Incremental Harvest status

## 10. S3 Vectorsは共通利用する

OpenWiki Brains自身に独自Vector DBを追加しない。

OpenWikiが生成したOKFもS3へPublishした後、AWS Sampleの既存Index Pipelineへ流す。

```text
OpenWiki Brains
      ↓
OKF
      ↓
S3
      ↓
Titan Embeddings
      ↓
S3 Vectors
      ↓
semantic_search
```

これによりOpenWiki側はAuthoringに集中できる。

```text
OpenWiki Brains = Writer / Knowledge Builder
AWS Platform     = Storage / Index / Retrieval / Viewer
```

## 11. MCPも共通化する

WriterごとにMCPを作らず、Canonical OKFに対する共通Wiki MCPを提供する。

代表Tool:

```text
list_directory
read_page
grep
get_backlinks
semantic_search
```

Consumer AgentからWriterの存在を意識させない。

```text
Consumer Agent
      ↓
Common Wiki MCP
      ↓
Canonical OKF
```

## 12. 将来のWriter追加

同じ契約でWriterを増やせる。

```text
Writer Layer
├─ OpenWiki Brains
├─ AWS Harvest Agent
├─ GitHub Knowledge Writer
├─ Analysis Report Writer
├─ Specification Writer
└─ Future Enterprise Connector Writer
```

Writer追加条件:

1. Canonical OKFへ変換可能
2. provenanceを失わない
3. stable IDを維持できる
4. Markdown Linkを生成・維持できる
5. S3 Publish Contractを守る

## 13. PoC順序

### Phase 1 — そのまま試す

```text
OpenWiki Brains
→ 議事録10〜20件
→ Wiki生成 / 更新挙動確認

AWS Data Wiki
→ 工程データ
→ Harvest / Data Understanding確認
```

### Phase 2 — OpenWiki Writer追加

```text
OpenWiki Brains
→ local OKF
→ Adapter
→ S3
```

AWS Harvestは無改修で維持する。

### Phase 3 — AWS Retrieval / UI共通化

```text
OpenWiki OKF
      ↓
S3
      ↓
S3 Vectors
      ↓
Common MCP
      ↓
AWS UI
```

### Phase 4 — Consumer Agent統合

```text
Consumer Agent
      ↓
AgentCore Gateway
      ↓
Wiki MCP
      ↓
Meeting Wiki / Data Wiki
```

## 14. PoC Acceptance Criteria

### OpenWiki Brains Writer

- [ ] 議事録10〜20件を処理できる
- [ ] 新規議事録追加時に既存Wikiを更新できる
- [ ] Duplicate Conceptを大量生成しない
- [ ] Decisionの変遷を追える
- [ ] 元Sourceへのprovenanceを保持できる
- [ ] Meaningful Markdown Linksを生成できる
- [ ] Fargate local workspaceで実行できる
- [ ] S3からWorking Copyを復元できる
- [ ] 生成後S3へPublishできる
- [ ] Canonical OKF v0.2へNormalizeできる

### Common Platform

- [ ] OpenWiki生成OKFをAWS UIでBrowseできる
- [ ] Graph / Backlinkが機能する
- [ ] OpenWiki生成ConceptをS3 VectorsへIndexできる
- [ ] semantic_searchで発見できる
- [ ] Common Wiki MCPからread_pageできる
- [ ] AWS Harvest生成Wikiと同じConsumer Agentから利用できる

## 15. 完全置換を検討する条件

将来OpenWiki Brainsが以下を十分提供できる場合、AWS Harvest Agentの完全置換を再検討できる。

- Glue / Catalog discovery
- Athena query execution
- sample_rows
- Grain verification
- Join verification
- Data quality checks
- Reviewer / verifier
- Incremental update
- Production-grade state management

それまでは、工程データWriterとしてAWS Harvest Agentを維持する。

## 16. Architecture Decision

採用する構成:

```text
OpenWiki Brains       AWS Harvest Agent
      │                       │
      │                       │
      └──────────┬────────────┘
                 ▼
          Pluggable Writer Layer
                 ▼
          OKF v0.2 Boundary
                 ▼
                S3
                 ▼
    Link / Backlink + S3 Vectors
                 ▼
               MCP
                 ▼
             Common UI
                 ▼
          Consumer Agent
```

> **OpenWiki BrainsはAWS Harvest Agentの代替ではなく、追加Writerとして導入する。AWS SampleはOKF Knowledge Platformとして再利用し、Storage / Vector Search / MCP / UIを共通化する。WriterとPlatformの境界をOKFに固定することで、OpenWikiやOKFのバージョンアップ時の影響をAdapter層へ限定する。**

## 17. 既存ドキュメントとの優先順位

本ドキュメントは、2026-08-08時点の最新Architecture Decisionとして、以下の既存記述より優先する。

- `FINAL_REPORT.md` 内の「AWS Harvest AgentをProject Knowledge Harvestへ全面変更する」記述
- `HARVEST_MIGRATION.md` 内の「Data Wiki固有Harvestを削除・置換する」記述

これらは将来の**Custom Project Knowledge Writerを自作する場合の参考設計**として残す。

現行PoCでは次を正式方針とする。

```text
Meeting / Project Knowledge → OpenWiki Brains Writer
Engineering Data Knowledge → AWS Harvest Agent
Common Format              → Canonical OKF v0.2
Common Platform            → AWS Sample S3 / S3 Vectors / MCP / UI
```
