# 仕様駆動開発（SDD）の現在地

## OpenSpec × Superpowers × LLM Wiki / OKF で考える AI 時代の開発プロセス

> 更新日: 2026-08-08
>
> 本レポートは、2026年8月公開の「仕様駆動開発の消費期限」を起点に、OpenSpec、Superpowers、LLM Wiki、Open Knowledge Format（OKF）、ADR、Agent Harness の役割を整理し、現在の Agentic Development における実践的な構成をまとめたものです。

---

## 1. 結論

2026年時点では、仕様駆動開発（Spec-Driven Development: SDD）が不要になったわけではありません。むしろ、**SDDが一つの仕組みの中に抱えていた役割を分解し、それぞれ最適な仕組みに移す方向**が強くなっています。

本レポートでは、現在の有力な役割分担を次のように整理します。

```text
OpenSpec
= What / Change
= 今回、何を作る・何を変えるか

Superpowers / Skills
= How
= どう設計・実装・テスト・レビューするか

LLM Wiki / OKF
= What We Know
= プロジェクトについて何が分かっているか

ADR
= Why
= なぜその設計判断をしたか

Agent Harness
= Execute & Verify
= 実装・テスト・検証をどう自律実行するか
```

つまり、AI時代の開発では次の構成が分かりやすいです。

```text
Human Intent
     ↓
OpenSpec
     ↓
Coding Agent
     ↓
Superpowers / Skills
     ↓
Tools / MCP
     ↓
Code / Test / Verification
     ↓
ADR + LLM Wiki / OKF
     ↓
Next Development Context
```

一言で表現すると、

> **OpenSpecで「何を作るか」を合意し、Superpowersで「どう作るか」を標準化し、LLM Wiki / OKFで「何を学んだか」を蓄積する。**

これが、従来型SDDをそのまま重厚化するよりも、現在のCoding Agentの能力に合わせやすい構成です。

---

## 2. SDDとは何だったのか

SDDは、Vibe CodingのようにAIへ直接実装を依頼するのではなく、まず仕様を定義してから実装する考え方です。

代表的なワークフローは次の通りです。

```text
Kiro
Requirements
   ↓
Design
   ↓
Tasks
   ↓
Implementation

Spec Kit
Specify
   ↓
Plan
   ↓
Tasks
   ↓
Implementation

OpenSpec
Proposal
   ↓
Specs
   ↓
Design
   ↓
Tasks
   ↓
Implementation
```

2026年8月公開の「仕様駆動開発の消費期限」では、SDDの実用上の役割は大きく2つに分解されています。

1. **AI Workflow**
   - 仕様 → 設計 → タスク化 → 実装という開発手順をAgentへ伝える
2. **Agent用ドキュメント管理・長期記憶**
   - システム仕様やプロジェクトContextをAgentが後から参照できるようにする

この二つを一つのSpec体系で扱っていたのが、従来型SDDと考えると分かりやすくなります。

参考: https://speakerdeck.com/watany/expiration-date-of-sdd

---

## 3. なぜ「SDDの消費期限」が議論されるのか

大きな理由は、Coding Agentの自走能力が急速に向上したことです。

従来は、人間が細かいRequirementsやDesign、Tasksまで作成しなければAIが正しく実装できませんでした。

```text
Human
  ↓
Requirements
  ↓
Design
  ↓
Tasks
  ↓
AI Implementation
```

一方、現在のCoding Agentは、コードベースを探索し、設計を考え、計画を立て、タスクを分解し、実装・テスト・レビューまで進められるようになっています。

```text
Human Intent
     ↓
Coding Agent
     ├─ Explore
     ├─ Plan
     ├─ Task decomposition
     ├─ Implementation
     ├─ Test
     └─ Review
```

そのため、特に **spec-first の役割はPlan ModeやAgent Harnessへ吸収されつつある**と考えられます。

「仕様駆動開発の消費期限」でも、事前タスクリストに従って実装する流れはAgent Harness側へ一般化し、長期記憶についてもSpec以外の代替手段が登場していると整理されています。

ただし、これはSpecが不要という意味ではありません。

AIが高速に実装できるほど、人間側では次の問題が大きくなります。

- なぜこの変更をしたのか分からない
- どの要件を満たすコードなのか分からない
- Agentが生成した大量の差分をレビューできない
- チーム内でシステム理解が追いつかない
- AI生成コードをブラックボックスとして受け入れてしまう

このような **認知負債・理解負債** を抑えるため、人間とAgentが共有できる「軽い型」は依然として重要です。

したがって現在の方向性は、

```text
SDDを捨てる
```

ではなく、

```text
重いSDD
   ↓
必要な部分だけ残す
   ↓
役割を分離する
```

と考える方が適切です。

---

## 4. OpenSpecの位置付け ― What / Change

OpenSpecは、人間とAIの間で「今回何を変更するのか」を合意するための軽量な仕様管理レイヤーです。

公式ドキュメントでは、OpenSpecを **lightweight agreement layer** と表現しています。

基本的な考え方は、

> agree first, then build confidently

です。

OpenSpecでは、現在の仕様と今回の変更を分離します。

```text
openspec/
├── specs/
│   ├── auth/
│   │   └── spec.md
│   └── payments/
│       └── spec.md
│
└── changes/
    └── add-remember-me/
        ├── proposal.md
        ├── design.md
        ├── tasks.md
        └── specs/
```

`specs/` は現在のシステム仕様、`changes/` は今回の変更を表します。

つまりOpenSpecは、巨大な仕様書を毎回作るのではなく、**仕様のGit diff** のような形でChangeを管理します。

```text
Current Spec
     ↓
Change Proposal
     ↓
Spec Delta
     ↓
Design
     ↓
Tasks
     ↓
Implementation
     ↓
Verify
     ↓
Archive
     ↓
Current Specへ反映
```

この構造はPRレビューとも相性が良く、コードを見る前に「何を変えたかったのか」を確認できます。

参考: https://openspec.dev/docs/overview

### OpenSpecが持つべきもの

- 今回の変更目的
- Scope / Out of Scope
- Requirement
- Acceptance Criteria
- 必要に応じたDesign
- 実装Task

### OpenSpecへ入れ過ぎないもの

- TDDの一般的な進め方
- Git運用手順
- 毎回共通するDebugging手法
- プロジェクト全体の長期Knowledge
- 過去の障害調査結果すべて

これらは別の仕組みに分離した方がよいでしょう。

---

## 5. Superpowersの位置付け ― How

Superpowersは、Agentic Skills Framework兼Software Development Methodologyです。

OpenSpecが「今回何を作るか」を管理するのに対して、Superpowersは **「どう作るか」** をAgentへ教えます。

主なSkillsには次のようなものがあります。

- brainstorming
- writing-plans
- test-driven-development
- systematic-debugging
- subagent-driven-development
- executing-plans
- requesting-code-review
- receiving-code-review
- verification-before-completion
- using-git-worktrees
- finishing-a-development-branch

Superpowersの基本Workflowは概ね次のようになります。

```text
Brainstorming
    ↓
Design refinement
    ↓
Writing Plans
    ↓
Subagent-driven Development
    ↓
TDD
RED → GREEN → REFACTOR
    ↓
Code Review
    ↓
Verification
```

参考: https://github.com/obra/superpowers

### Superpowersは過去のベストプラクティスなのか

「過去のもの」という理解は適切ではありません。

Superpowersは2026年現在も活発に更新されており、TDD、Systematic Debugging、Verification、Subagent Developmentなど、Agent開発で引き続き重要な実践をSkillsとして提供しています。

一方、「仕様駆動開発の消費期限」の資料では、SuperpowersのようなベストプラクティスSkills群について、**個別の推奨プロセスとしては良いが、チーム全体のワークフローの型としては不足する**と評価されています。

つまり、

```text
OpenSpec
= 開発の「型」

Superpowers
= 開発の「技」
```

という関係が分かりやすいです。

両者は競合ではなく補完関係です。

---

## 6. LLM Wiki / OKFの位置付け ― What We Know

SDDの長期記憶としての役割は、今後LLM WikiやOKFへ分離していくことが考えられます。

LLM Wikiは、Agentや人間がプロジェクトについて学んだ知識を継続的に蓄積する仕組みです。

例えば次のような情報です。

- このAPIは何のために存在するか
- データモデルの意味
- customer_id と account_id の関係
- 過去の障害原因
- よく使う分析方法
- 特定ライブラリ利用時の注意点
- 過去の調査結果
- システム間の関係
- 業務ルール

これは今回だけの変更仕様ではなく、次回以降も利用するKnowledgeです。

### OKF

Googleは2026年6月にOpen Knowledge Format（OKF）を公開しました。

OKFは、**LLM-wiki patternをportable / interoperableな形式として標準化するOpen Specification**です。

OKF v0.1では、MarkdownとYAML frontmatterを中心にKnowledgeを表現します。

```text
knowledge/
├── index.md
├── systems/
│   └── auth.md
├── data/
│   └── customer.md
└── incidents/
    └── timeout-2026-07.md
```

参考: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/

### OpenSpecとLLM Wikiの違い

```text
OpenSpec
────────────────────
今回何を変更する？

短期〜中期
Change中心


LLM Wiki / OKF
────────────────────
このプロジェクトについて何を知っている？

長期
Knowledge中心
```

SpecをKnowledge Baseとして肥大化させず、長期KnowledgeをWikiへ分離するのがポイントです。

---

## 7. ADRの位置付け ― Why

LLM Wikiが「何が分かっているか」を管理するのに対して、ADR（Architecture Decision Record）は **「なぜそうしたのか」** を管理します。

例えば、

- なぜPostgreSQLではなくDynamoDBを採用したか
- なぜ同期APIではなく非同期処理にしたか
- なぜManaged KBを採用したか
- なぜこの認証方式にしたか
- なぜこのライブラリを採用したか

といった判断です。

コードや最終仕様だけでは、代替案と判断理由は失われがちです。

したがって、

```text
OpenSpec
= What Changed

Superpowers
= How to Build

LLM Wiki
= What We Know

ADR
= Why We Decided
```

と分けることで情報の責務が明確になります。

---

## 8. Agent Harnessの位置付け ― Execute & Verify

現在のCoding Agentでは、単にコードを生成するだけではなく、Agent Harnessが重要になっています。

Agent Harnessは、Agentが安全かつ再現可能に仕事を実行するための仕組みです。

例えば、

- repository exploration
- planning
- task decomposition
- tool execution
- subagent execution
- test execution
- lint / type check
- verification
- review
- retry
- context management

などを含みます。

これにより、SDDが担っていた「事前に作ったタスクリストを順番に実行する」という部分はHarness側へ吸収されていきます。

```text
OpenSpec
   ↓
Change Intent
   ↓
Agent Harness
   ├─ Plan
   ├─ Explore
   ├─ Execute
   ├─ Test
   ├─ Verify
   └─ Review
```

そのため、将来的にはSpecを細かい実装手順まで書き込むよりも、Agentが判断するために必要なIntent、Constraint、Acceptance Criteriaを明確にすることの方が重要になります。

---

## 9. 推奨アーキテクチャ

以上を統合すると、現在のAgentic Developmentの有力な構成は次のようになります。

```text
                         Human
                           │
                        Intent
                           │
                           ▼
                    ┌────────────┐
                    │  OpenSpec  │
                    │------------│
                    │ What       │
                    │ Change     │
                    │ Acceptance │
                    └─────┬──────┘
                          │
                          ▼
                    Coding Agent
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
       Superpowers       Tools      LLM Wiki
        / Skills        MCP/CLI       / OKF
             │            │            │
       How to work        │       What we know
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                    Agent Harness
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Code          Test        Verify
                          │
                          ▼
                        Review
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
                ADR            LLM Wiki
                Why          Knowledge Update
```

---

## 10. 開発するほどAgentが賢くなるKnowledge Loop

この構成の本当の価値は、1回の開発フローではなくKnowledge Loopにあります。

### 1回目

```text
Human Intent
     ↓
OpenSpec
     ↓
Superpowers
     ↓
Implementation
     ↓
Verification
     ↓
ADR + LLM Wiki
     ↓
Knowledge
```

### 2回目以降

```text
Human Intent
     ↓
LLM Wiki / ADR検索
     ↓
Relevant Context取得
     ↓
OpenSpec
     ↓
Superpowers
     ↓
Implementation
     ↓
新しいKnowledge
     ↓
LLM Wiki更新
```

つまり、

```text
Development
     ↓
Knowledge
     ↓
Next Development Context
     ↓
Better Development
```

という循環を作ります。

これにより、Agentは毎回ゼロからコードベースを理解する必要がなくなり、開発を繰り返すほどプロジェクト固有の知識を利用できるようになります。

LLM Wikiの本質は単なるRAG検索ではなく、**Development → Knowledge → Next Context のKnowledge Loopを作ること**にあります。

---

## 11. 情報の置き場所

実務では、情報を次のように分類すると分かりやすくなります。

| 情報 | 主な置き場所 | 寿命 |
|---|---|---|
| 今回何を変更するか | OpenSpec | 短期〜中期 |
| Acceptance Criteria | OpenSpec | 短期〜中期 |
| 今回のDesign | OpenSpec / Design Doc | 中期 |
| 実装Task | OpenSpec / Plan | 短期 |
| TDDの進め方 | Superpowers / Skills | 長期・再利用 |
| Debugging手法 | Superpowers / Skills | 長期・再利用 |
| Review手法 | Superpowers / Skills | 長期・再利用 |
| コーディング規約 | AGENTS.md / Skills | 長期 |
| 重要な設計判断 | ADR | 長期 |
| システム知識 | LLM Wiki / OKF | 長期 |
| 過去の障害・調査結果 | LLM Wiki / OKF | 長期 |
| 実行・テスト・検証 | Agent Harness | 実行時 |

重要なのは、**Everything in Spec にしないこと**です。

---

## 12. 変更規模による使い分け

すべての変更でOpenSpecを作る必要はありません。

### Level 0: 小変更

対象:

- typo
- 小さなbug fix
- 明確な1ファイル修正

```text
Human Intent
   ↓
Agent Plan
   ↓
Implementation
   ↓
Test
```

OpenSpecは不要です。

### Level 1: 通常変更

対象:

- 数ファイルにまたがる変更
- API追加
- 既存機能変更

```text
OpenSpec
   ↓
Superpowers
   ↓
Implementation
   ↓
Verification
```

### Level 2: 中〜大規模変更

対象:

- 新機能
- Architecture変更
- Database schema変更
- 他チームへの影響あり

```text
OpenSpec
   ↓
Design Review
   ↓
Superpowers
   ↓
Implementation
   ↓
Review / Verification
   ↓
ADR
   ↓
LLM Wiki Update
```

### Level 3: 継続的Agent Development

```text
OpenSpec
    +
Superpowers / Skills
    +
LLM Wiki / OKF
    +
ADR
    +
Agent Harness
    +
MCP / Tools
```

ここまで来ると、単なるAI Codingではなく、プロジェクト固有Knowledgeを持ったAgentic Development Platformになります。

---

## 13. AI-DLCとの関係

AI-DLCは、AI時代のSoftware Development Lifecycle全体を再設計する包括的な考え方です。

一方、OpenSpecやSuperpowersはより局所的・軽量に導入できます。

「仕様駆動開発の消費期限」では、AI-DLCについて、理念とWorkflowの導入に加えて既存プロセスや会社標準との整合まで必要になり、実務導入には「重かった」と評価されています。

これに対し、Skillsだけではチーム共通の「型」が不足するため、その中間としてOpenSpecが採用されています。

```text
AI-DLC
────────────────────
開発Lifecycle全体
強力
導入は重い

OpenSpec
────────────────────
変更管理の型
軽量
チーム導入しやすい

Superpowers
────────────────────
実装ベストプラクティス
非常に軽量
再利用しやすい
```

したがって、まずOpenSpec + Skillsから始め、必要に応じてAI-DLCの思想を取り込む進め方も現実的です。

---

## 14. 「SDDの消費期限」の本当の意味

SDDの消費期限とは、「SDDが使えなくなる日」を意味するのではありません。

AI Agentの能力が上がるにつれて、SDDで明示的に管理していた部分の一部がAgent自身の能力へ吸収されます。

```text
守
SDDの型を使う
  ↓
破
不要なSpecを削る
  ↓
離
Plan / Skills / Knowledge / Harnessへ役割分離
```

という「守破離」で考えると理解しやすくなります。

特にチーム開発では、AIの生成速度が上がるほど人間の理解速度がボトルネックになります。

そのため、今後のSpecは「AIに細かく指示するため」だけではなく、**人間がAIの仕事を理解・レビューするためのフォーマット**としての価値が大きくなります。

---

## 15. SDDからContext Engineeringへ

この流れをさらに進めると、中心テーマはSDDそのものではなくContext Engineeringになります。

従来:

```text
どれだけ詳細なSpecを書くか
```

これから:

```text
Agentが今のTaskに必要なContextを
必要なタイミングで
どう取得するか
```

つまり、

- OpenSpecから今回のIntentを取得
- LLM Wikiから関連Knowledgeを取得
- ADRから過去の判断理由を取得
- Skillsから作業方法を取得
- MCP / Toolsから外部情報を取得

し、必要な情報だけをAgentのContextへ入れる構成です。

```text
                    Context
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   OpenSpec         LLM Wiki        Skills
   Intent           Knowledge       How-to
       │               │               │
       └───────────────┼───────────────┘
                       ▼
                  Coding Agent
```

したがって、軽量SDDとLLM Wikiへの分離は、最終的には **Agent Context Engineeringの設計問題**として捉えることができます。

---

## 16. 推奨する最小導入構成

最初からすべてを導入する必要はありません。

まずは次の構成で十分です。

```text
repo/
├── openspec/
│   ├── specs/
│   └── changes/
│
├── skills/
│   ├── testing/
│   ├── debugging/
│   └── review/
│
├── docs/
│   └── adr/
│
├── knowledge/
│   ├── index.md
│   ├── systems/
│   ├── data/
│   └── incidents/
│
└── AGENTS.md
```

### Step 1

OpenSpecだけ導入し、一定以上の変更をChangeとして管理する。

### Step 2

TDD、Debugging、Review、VerificationなどをSuperpowers / Skills化する。

### Step 3

開発で得られた再利用KnowledgeをLLM Wikiへ蓄積する。

### Step 4

KnowledgeをOKF準拠へ寄せる。

### Step 5

AgentがTask開始時にLLM Wiki / ADRを検索し、Relevant Contextだけを取得する仕組みを追加する。

### Step 6

Agent HarnessとMCPを統合し、実装・テスト・レビューを自律実行する。

---

## 17. 最終整理

現在の流れを最もシンプルに整理すると、次のようになります。

```text
              AI時代の開発
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
     OpenSpec   Superpowers   LLM Wiki
        │           │           │
       What        How      What We Know
        │           │           │
        │           │          OKF
        │           │
        └──────┬────┴─────┬─────┘
               │          │
               ▼          ▼
          Coding Agent    ADR
               │          Why
               ▼
          Agent Harness
               │
               ▼
        Code / Test / PR
               │
               ▼
        Knowledge Update
```

役割を一言でまとめると、

- **OpenSpec = 開発の「型」**
- **Superpowers = 開発の「技」**
- **LLM Wiki / OKF = 開発の「知識」**
- **ADR = 開発の「判断履歴」**
- **Agent Harness = 開発の「実行基盤」**

です。

SDDを重厚化し続けるのではなく、変更Intentだけを軽量Specとして管理し、実装ノウハウをSkillsへ、長期KnowledgeをLLM Wiki / OKFへ、判断理由をADRへ分離する。

この構成にすることで、Agentの能力向上を活かしながら、人間側の認知負債も抑えることができます。

そして最終的には、

> **「仕様書をAIに渡してコードを書かせる開発」から、「プロジェクトKnowledgeを参照しながらAgentが開発し、その結果を再びKnowledgeとして蓄積する開発」へ移行する。**

これが、2026年時点で見えてきているSDDの次の形です。

---

## 参考資料

- 仕様駆動開発の消費期限 — watany / Speaker Deck  
  https://speakerdeck.com/watany/expiration-date-of-sdd

- OpenSpec — Core Concepts  
  https://openspec.dev/docs/overview

- Superpowers — obra/superpowers  
  https://github.com/obra/superpowers

- Introducing the Open Knowledge Format — Google Cloud  
  https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/

---

## 関連キーワード

`Spec-Driven Development` `SDD` `OpenSpec` `Superpowers` `Agent Skills` `LLM Wiki` `Open Knowledge Format` `OKF` `ADR` `Agent Harness` `Context Engineering` `Agentic Development`
