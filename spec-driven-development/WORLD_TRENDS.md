# 世界で進む Agentic Engineering への転換

## ― SDD から「Light Spec × Skills × Knowledge × Agent Harness」へ

> 更新日: 2026-08-08
>
> 本レポートは、`spec-driven-development/README.md` で整理した OpenSpec / Superpowers / LLM Wiki / OKF の役割分担を、米国・中国・日本の動向と照らし合わせて整理したものです。
>
> 結論から言えば、2026年の世界的な流れは「SDDを捨てる」ことではなく、**SDDが抱えていた役割を Light Spec、Skills、Knowledge、Agent Harness に分解し、Agent中心の開発環境へ再構成すること**にあります。

---

## 1. エグゼクティブサマリー

2024〜2025年のAIコーディングでは、Vibe Codingの反動としてSpec-Driven Development（SDD）が急速に広がりました。AIへいきなりコードを書かせるのではなく、Requirements、Design、Tasksなどを先に作り、その仕様に沿って実装させる方法です。

一方、2026年になるとCoding Agent自身が、コードベース探索、計画、タスク分解、実装、テスト、レビューまで担えるようになりました。その結果、詳細なSpecですべてを事前定義するよりも、人間はIntentやAcceptance Criteriaを明確にし、実装方法はSkillsへ、長期知識はRepository KnowledgeやWikiへ、実行と検証はAgent Harnessへ分離する方向が強くなっています。

世界の代表的な動きを抽象化すると、次のようになります。

```text
2024
AI Coding Assistant

Human
  ↓
Prompt
  ↓
AI
  ↓
Code


2025
Spec-Driven Development

Human
  ↓
Requirements
  ↓
Design
  ↓
Tasks
  ↓
AI Implementation


2026
Agentic Engineering

Human Intent
     ↓
Light Spec / Plan
     ↓
Coding Agent
     ↓
Skills + Tools + Knowledge
     ↓
Agent Harness
     ↓
Code / Test / Review
     ↓
Knowledge Update
```

この構造では、役割を次のように分解できます。

```text
OpenSpec / Plan
= What
= 今回、何を作る・何を変えるか

Superpowers / Skills
= How
= どう設計・実装・テスト・レビューするか

LLM Wiki / OKF / Repo Knowledge
= What We Know
= このプロジェクトについて何が分かっているか

ADR
= Why
= なぜその設計判断をしたか

Agent Harness
= Execute & Verify
= どう実行し、テストし、検証するか
```

重要なのは、OpenSpec、Superpowers、LLM Wikiという個別ツールが世界標準になることではありません。

**What / How / Knowledge / Why / Execution を分離するアーキテクチャ自体が、世界的に共通化しつつある**ことが重要です。

---

## 2. 世界共通で起きている5つの変化

### 2.1 Specは「全部を書く場所」から「合意レイヤー」へ

従来型SDDでは、Requirement、Design、Task、Contextなど多くの情報をSpec体系に保持する傾向がありました。

しかし現在は、Specを次のように限定する方向が強くなっています。

- 今回のGoal
- Scope / Out of Scope
- Requirement
- Constraint
- Acceptance Criteria
- 必要な場合のみDesign

つまり、SpecはAgentへ詳細な実装手順を教える巨大マニュアルではなく、**人間とAgentが「何を実現するか」について認識を合わせる軽量な契約**へ変化しています。

---

### 2.2 実装方法論はSkillsへ移る

TDD、Systematic Debugging、Code Review、Verificationなどは、案件ごとにSpecへ書き直す必要がありません。

これらは再利用可能な「How」であるため、SkillsやRulesとして切り出す方が合理的です。

```text
今回何を作る？
→ Spec / Plan

どう作る？
→ Skills / Rules
```

Superpowersはこの「How」のレイヤーを代表する実装例です。

---

### 2.3 長期ContextはRepository Knowledge / Wikiへ移る

Agentが毎回ゼロからコードベースを理解するのは非効率です。

そこで、次のような情報を長期Knowledgeとして保持する方向が強まっています。

- Architecture
- Domain Knowledge
- Data Model
- Business Rules
- Past Incidents
- Runbook
- Tech Stack
- Module Responsibility
- Interface Contract
- 過去の調査・実装で得た知見

この動きは、OpenAIのRepository Knowledge、GoogleのOKF、中国QoderのRepo Wiki / Knowledge Cardsなどに共通しています。

---

### 2.4 Agent HarnessがSDDの「実行部分」を吸収する

Coding Agentは単なるコード生成器ではなくなっています。

現在は、Agent Harnessが次の処理を担います。

```text
Explore
 ↓
Plan
 ↓
Task decomposition
 ↓
Implement
 ↓
Test
 ↓
Verify
 ↓
Review
 ↓
Retry
```

そのため、Spec側で細かい実装手順を完全に固定する必要性は下がります。

---

### 2.5 人間の役割が「Coding」から「Steering」へ移る

AI Agentの能力が上がるほど、人間の価値はコード入力速度ではなくなります。

今後は、

```text
Goal
Architecture
Constraints
Evaluation
Review
Judgement
```

を担う比重が高くなります。

OpenAIのHarness Engineeringで使われている表現で言えば、

> Humans steer. Agents execute.

という方向です。

---

# 3. 米国の動向

## 3.1 OpenAI ― Harness Engineering

2026年2月、OpenAIはCodexを利用した大規模なAgent-first開発の経験を「Harness Engineering」として公開しました。

この事例では、3人規模のチームがCodexを中心に開発を行い、約100万行規模のコードベースを構築しています。重要なのはコード生成量ではなく、開発方法そのものです。

OpenAIが強調しているのは、

> Humans steer. Agents execute.

という考え方です。

人間は直接コードを書くことよりも、Agentが正しく開発できるEnvironment、Intent、Feedback Loopを設計します。

### 巨大AGENTS.mdをやめた

OpenAIは当初、Agentへ必要な情報を巨大な`AGENTS.md`へ集約しようとしました。しかし、Context Windowを圧迫し、重要度が分からなくなり、情報が陳腐化しやすいため失敗したと説明しています。

現在は、短い`AGENTS.md`を「目次」として使い、Repository Knowledgeを構造化された`docs/`へ分離しています。

```text
AGENTS.md
   │
   │  Agent向けの地図
   ▼
ARCHITECTURE.md

docs/
├── design-docs/
├── exec-plans/
├── generated/
├── product-specs/
├── references/
├── DESIGN.md
├── RELIABILITY.md
├── SECURITY.md
└── ...
```

OpenAIはこのRepository Knowledgeを **System of Record** として扱っています。

### Planも軽重を使い分ける

OpenAIでは、すべてを重いExecution Planにしません。

```text
Small Change
→ Ephemeral Lightweight Plan

Complex Change
→ Execution Plan
   ├─ Progress
   ├─ Decisions
   └─ Version Controlled
```

この構成は、OpenSpecの「必要な変更だけ軽量Specとして管理する」という考え方と非常に近いものです。

### 注目ポイント

OpenAIの事例から見えるのは、

```text
巨大なSpec / Instruction
        ↓
小さなEntry Point
        ↓
Relevant Knowledgeを探索
        ↓
Agentが自律実行
```

というProgressive Disclosure型のContext Engineeringです。

参考:
- https://openai.com/index/harness-engineering/

---

## 3.2 Anthropic ― Plan Mode + CLAUDE.md + Skills + Subagents

Claude Codeも同じ方向に進んでいます。

AnthropicはClaude Codeの基本的なAgent Loopを、

```text
Read
 ↓
Plan
 ↓
Act
 ↓
Observe
```

と説明しています。

さらに2026年の公式講座では、次の要素を組み合わせてチームへ展開する方法を紹介しています。

```text
Plan Mode
CLAUDE.md
Skills
Plugins
Subagents
MCP
```

役割として整理すると、

```text
Plan Mode
= 今回の方針

CLAUDE.md
= Repositoryの入口・Project Briefing

Skills / Plugins
= チームの標準・ベストプラクティス

Subagents
= 並列化・役割分担

MCP
= 外部Tools / Dataとの接続
```

となります。

AnthropicはPlan Modeについて、各操作を一つずつ承認するのではなく、**実行前に全体戦略をレビューする方式**として説明しています。

これは、人間の監督ポイントが「個々のTool Call」から「Plan / Strategy」へ上がっていることを示しています。

参考:
- https://www.anthropic.com/webinars/claude-code-foundations
- https://www.anthropic.com/research/trustworthy-agents

---

## 3.3 GitHub Spec Kit ― SDD自身もAgentic化

GitHub Spec Kitは依然としてSDDを強く推進しています。

ただし、現在のSpec Kitは単純な、

```text
Specify
 ↓
Plan
 ↓
Tasks
 ↓
Implement
```

だけのツールではありません。

2026年時点では、Agentic SDDとして、

```text
constitution
 ↓
specify
 ↓
clarify
 ↓
plan
 ↓
checklist
 ↓
tasks
 ↓
analyze
 ↓
implement
 ↓
converge
```

というAgent-driven Workflowへ拡張されています。

特に重要なのは、Clarify、Checklist、AnalyzeなどのQuality Gateが「意味のある曖昧さがある場合に追加する」位置付けになっていることです。

さらにSpec Kit自身が、

- Extensions
- Presets
- Workflows
- Bundles
- 複数Coding Agent Integration

を持つExtensible Harnessへ進化しています。

つまり、SDD側も固定的な文書生成ツールではなく、**Agentic Workflowを構成するHarness**へ近づいています。

参考:
- https://github.github.com/spec-kit/reference/agentic-sdd.html
- https://github.github.com/spec-kit/reference/overview.html

---

## 3.4 Google ― Open Knowledge Format（OKF）

Google Cloudは2026年6月、Open Knowledge Format（OKF）を公開しました。

OKFの重要な主張は、Agentが利用するKnowledgeを、

```text
特定製品の独自DB
```

ではなく、

```text
Portable / InteroperableなFormat
```

として持つことです。

OKF v0.1はMarkdown + YAML frontmatterという非常にシンプルな構成でした。

さらに2026年7月24日に公開されたOKF v0.2では、Agent自身がKnowledgeを書き込む世界を想定し、TrustやProvenanceなどの信頼性が重要テーマになっています。

つまり、Knowledge管理は単なるRAG用データ作成から、

```text
Knowledge
 ↓
Agentが利用
 ↓
Agentが更新
 ↓
Trust / Provenance管理
```

というEngineering対象へ進み始めています。

参考:
- https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/

---

# 4. 中国の動向

## 4.1 Qoder ― Spec + Wiki + Knowledge + Agentを統合

中国系のAgentic Coding Platformを見ると、同じ方向がより製品統合された形で現れています。

代表例がQoderです。

Qoderには、

```text
Quest
Agent Mode
Spec-driven Development
Repo Wiki
Knowledge Cards
Memory
MCP
Subagents / Expert Team
```

などが統合されています。

### Code with Spec

Qoder QuestのSpec-driven Developmentでは、次のWorkflowを持っています。

```text
Requirement clarification
        ↓
Generate Spec
        ↓
Requirement Description
Design Plan
Task Breakdown
Acceptance Criteria
        ↓
Human Review
        ↓
Run Spec
        ↓
Agent Execution
        ↓
Result Review
```

これはSDDを完全に捨てているのではなく、**必要なFeatureではSpecを人間とAgentの合意点として使い、その後の実装はAgentへ委譲する**構成です。

参考:
- https://docs.qoder.com/user-guide/quest/spec-driven

---

## 4.2 Qoder Repo Wiki

QoderにはRepo Wikiがあります。

Repo Wikiは、RepositoryのコードやDocumentationを解析し、ArchitectureやImplementationのKnowledgeを構造化します。

さらにWikiは静的なDocumentationではなく、Code Changeを追跡して更新されます。

```text
Code / Docs
    ↓
Repo Wiki
    ↓
Project Understanding
    ↓
Agent Context
```

これは、LLM WikiをCoding Platformへ組み込んだ構成と考えることができます。

参考:
- https://docs.qoder.com/ja/user-guide/repo-wiki

---

## 4.3 Qoder Knowledge Cards

Qoderでは、Wikiに加えてKnowledge Cardsを持っています。

Knowledge CardはRepo Wikiと同期して生成され、Agentが直接利用しやすい高密度なKnowledge Unitです。

主に、

- Architecture Documents
- Code Specifications
- Tech Stack
- Module Responsibility
- Dependency
- Engineering Convention

などを保持します。

```text
Repository
    ↓
Knowledge Engine
    ↓
┌──────────────────┐
│ Repo Wiki        │ ← 人間にも読みやすい
├──────────────────┤
│ Knowledge Cards │ ← Agent向け高密度Context
├──────────────────┤
│ Memory           │ ← 長期的な経験・Preference
└──────────────────┘
```

Qoder自身も、WikiをそのままAgentへ与えるだけでは長文から再抽出する必要があるため、AgentがTaskで利用しやすい粒度へ構造化したKnowledge Cardsが必要だと説明しています。

またKnowledge Cardsは`.qoder/repowiki`へ保存してGit管理することもでき、Team Knowledgeとして共有できます。

これは、**人間向けWikiとAgent向けKnowledgeを分離する**という次のステップを示しています。

参考:
- https://docs.qoder.com/user-guide/knowledge-engine/knowledge-cards
- https://qoder.com/en/blog/qoder-knowledge-engine

---

## 4.4 Tencent CodeBuddy ― RulesによるContext Engineering

Tencent CodeBuddyでも、Project Rulesを`.codebuddy/rules`としてRepositoryへ保持できます。

Rulesでは、

- Domain Knowledge
- Project Workflow
- Coding Standard
- Architecture Decision
- Template

などを管理できます。

さらにRuleはPath Patternや関連性に応じて適用できます。

つまり、

```text
巨大なSystem Prompt
```

ではなく、

```text
Task
 ↓
Relevant Ruleを選択
 ↓
Agent Contextへ注入
```

というContext Engineeringです。

参考:
- https://staging-codebuddy.tencent.com/docs/ide/User-guide/Rules

---

# 5. 米国と中国の違い

米国と中国は大きな方向としては非常に近いですが、代表的な製品を見ると実装スタイルに少し違いがあります。

| 領域 | 米国系の代表例 | 中国系の代表例 |
|---|---|---|
| Spec / Plan | Codex Exec Plan、Claude Plan、OpenSpec、Spec Kit | Qoder Code with Spec |
| Agent Rules | AGENTS.md、CLAUDE.md | CodeBuddy Rules |
| Skills | Claude Skills、Codex Skills、Superpowers | Skills / Rules |
| Knowledge | Repository docs、OKF | Repo Wiki、Knowledge Cards |
| Tools | MCP、CLI、Worktree | MCP、Built-in Tools |
| Harness | Codex Harness、Spec Kit Workflow | Quest / Agent Platform |
| Multi-Agent | Codex、Claude Subagents | Qoder Expert Team / Subagents |

代表例から見える傾向としては、米国側は、

```text
AGENTS.md
+
Skills
+
MCP
+
Knowledge
+
Harness
```

のようなComposableな部品を組み合わせる文化が強く見えます。

一方、中国側は、

```text
Spec
+
Wiki
+
Knowledge
+
Memory
+
Agent
+
Review
```

をIDE / Coding Platformの中へ統合する方向が目立ちます。

ただし、これは各代表製品から読み取れる傾向であり、「米国は必ず分散型、中国は必ず統合型」という意味ではありません。

---

# 6. 日本での議論との関係

本レポートの起点となった「仕様駆動開発の消費期限」では、SDDをそのまま永続的な完成形として扱うのではなく、Coding Agentの進化に合わせて使い方を変える必要性が議論されています。

資料内では、

- AI-DLCは包括的だが導入が重い
- SuperpowersのようなSkillsは優れたベストプラクティスだがチーム共通の型としては不足する
- OpenSpecは人間が理解・レビューするための軽量な型として使いやすい
- 長期記憶はLLM Wiki、ADR、CONTEXT.mdなど別の手段へ分離できる

という整理がされています。

これは米国・中国の動きと非常に整合します。

```text
重いSDD
   ↓
Specの役割を縮小
   ↓
Plan / Skills / Knowledge / Harnessへ分離
```

「SDDの消費期限」は、SDDが不要になるという意味ではなく、

```text
守
SDDの型を使う
 ↓
破
不要なSpecを削る
 ↓
離
Skills / Knowledge / Harnessへ役割分離
```

という守破離として捉えると分かりやすいです。

参考:
- https://speakerdeck.com/watany/expiration-date-of-sdd

---

# 7. 世界の流れはどこへ収束しているか

米国、中国、日本の議論を抽象化すると、かなり共通したArchitectureが見えてきます。

```text
                         Human
                           │
                     Goal / Intent
                           │
                           ▼
                  ┌────────────────┐
                  │ Light Spec     │
                  │ Plan / OpenSpec│
                  └───────┬────────┘
                          │
                          ▼
                    Coding Agent
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
          Skills        Tools       Knowledge
             │          MCP/CLI        │
             │                         │
             │                   LLM Wiki / OKF
             │                   Repo Knowledge
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
                    Agent Harness
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Code          Test        Review
                          │
                          ▼
                    Verification
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
                ADR          Knowledge Update
                 │                 │
                 └────────┬────────┘
                          ▼
                   Next Agent Task
```

この形を一言で表現すると、

> **OpenSpecでWhatを合意し、SkillsでHowを標準化し、LLM Wiki / OKFでWhat We Knowを育て、Agent HarnessでExecute & Verifyする。**

となります。

---

# 8. SDDからContext Engineeringへ

世界の動きをさらに抽象化すると、中心テーマはSDDからContext Engineeringへ移っています。

従来は、

```text
どれだけ詳細なSpecを書くか
```

が重要でした。

これからは、

```text
今のTaskに必要なContextを
必要なAgentへ
必要なタイミングで
どう与えるか
```

が重要になります。

Agentが必要とするContextには、

```text
Current Goal
Current Spec
Architecture
Domain Knowledge
Past Decisions
Relevant Skills
Code
Tools
Constraints
```

があります。

全部を一度にPromptへ入れるのではなく、Taskに応じてRelevant Contextを取得する必要があります。

```text
                  Context Sources
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
    OpenSpec        LLM Wiki          Skills
    Intent          Knowledge          How-to
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                   Coding Agent
```

OpenAIが「巨大AGENTS.mdではなく地図 + docs」としたこと、CodeBuddyがRelevant Rulesを注入すること、QoderがWikiとは別にAgent向けKnowledge Cardsを作ることは、すべてこのContext Engineeringの流れにあります。

---

# 9. Knowledge Loopが次の競争領域

単にWikiを作るだけでは十分ではありません。

重要なのは、開発によって得た知識を次の開発へ戻すことです。

```text
Task
 ↓
Plan / OpenSpec
 ↓
Agent
 ↓
Skills
 ↓
Implementation
 ↓
Test / Review
 ↓
新しいKnowledge
 ↓
LLM Wiki / OKF
 ↓
次のTaskでRetrieval
 ↓
Better Context
 ↓
Better Implementation
```

これをKnowledge Loopと考えることができます。

OpenAIはRepository KnowledgeをSystem of Recordとして運用し、Documentationの陳腐化を検出する仕組みまで取り入れています。

QoderはRepo WikiとKnowledge CardsをRepositoryの変更へ追随させています。

Google OKF v0.2は、Agent自身がKnowledgeを書き込む状況でのTrustとProvenanceをテーマにしています。

つまりDocumentationは、

```text
人間が読む静的な資料
```

から、

```text
Agentと人間が共同で育てるEngineering Knowledge
```

へ変わり始めています。

---

# 10. 2026年版 Agentic Engineering Reference Architecture

世界の動向を踏まえると、2026年時点の有力なReference Architectureは次のように整理できます。

```text
Human Intent
     ↓
OpenSpec / Light Plan
     ↓
Coding Agent
     ↓
┌───────────────────────────────┐
│ Context Layer                 │
│                               │
│ Skills / Rules                │
│ ADR                           │
│ LLM Wiki / OKF                │
│ Repository Knowledge          │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Agent Harness                 │
│                               │
│ Explore                       │
│ Plan                          │
│ Execute                       │
│ Test                          │
│ Verify                        │
│ Review                        │
│ Retry                         │
└──────────────┬────────────────┘
               │
               ▼
          Code / PR
               │
               ▼
       Knowledge Update
               │
               └─────────────→ 次のTaskへ
```

---

# 11. このRepositoryで採用するなら

`spec-driven-development/README.md`で整理した構成は、世界の動向と比較してもかなり自然です。

推奨する役割分担は次の通りです。

```text
OpenSpec
= 開発の「型」
= What / Change

Superpowers
= 開発の「技」
= How

LLM Wiki / OKF
= 開発の「知識」
= What We Know

ADR
= 開発の「判断履歴」
= Why

Agent Harness
= 開発の「実行基盤」
= Execute & Verify
```

つまり、特定ベンダーの統合IDEへ全面依存しなくても、OSSや標準Formatを組み合わせて同じArchitectureを構築できます。

```text
OpenSpec
     +
Superpowers / Agent Skills
     +
LLM Wiki / OKF
     +
ADR
     +
Coding Agent Harness
```

これは、Qoderのような統合型Agentic Platformを、ComposableなOSS / Open Standardで再構成するイメージとも言えます。

---

# 12. 導入成熟度

## Level 1 ― Agent Coding

```text
Coding Agent
+
AGENTS.md / CLAUDE.md
+
Plan Mode
+
Skills
```

まずはAgentが安全にRepositoryを理解して開発できる状態を作ります。

---

## Level 2 ― Agentic Development

```text
OpenSpec
+
Skills / Superpowers
+
ADR
+
LLM Wiki / OKF
```

What、How、Why、Knowledgeを分離します。

---

## Level 3 ― Agentic Engineering

```text
Light Spec
+
Skills
+
Knowledge Retrieval
+
Agent Harness
+
Multi-Agent
+
Automatic Verification
+
Automatic Knowledge Update
```

実装・テスト・レビュー・知識更新まで循環させます。

世界の先端事例が現在向かっているのは、このLevel 3です。

---

# 13. 今後注目すべきポイント

今後は「どのCoding Agentが一番賢いか」だけでなく、次の領域が重要になります。

### 1. Knowledgeの標準化

OKFのようなVendor-neutralなKnowledge Formatがどこまで広がるか。

### 2. Agent向けKnowledge表現

人間向けWikiと、Qoder Knowledge CardsのようなAgent向け高密度Contextを分ける流れが進むか。

### 3. Knowledge Trust

Agent自身がKnowledgeを書き始めたときに、Provenance、Freshness、Confidenceをどう管理するか。

### 4. Specの軽量化

全変更へSDDを強制するのではなく、変更リスクに応じてPlan / Light Spec / Detailed Specを使い分ける方法が標準化するか。

### 5. Harnessの差別化

Model性能だけでなく、Test、Verification、Sandbox、Observability、Retry、EvaluationといったHarness品質がAgentの実力を左右するようになるか。

### 6. Human Reviewの再設計

大量に生成されるコードを直接レビューするのではなく、Intent、Spec、Architecture、Evaluation Resultを中心にReviewする方式へ移るか。

---

# 14. 最終結論

世界のAI先進地域を見ると、具体的な製品や用語は違っていても、方向性はかなり共通しています。

```text
重いSpec中心の開発
        ↓
Light Spec / Plan
        ↓
Agentが自律的に実装
        ↓
Skillsで方法論を再利用
        ↓
Knowledgeを外部化
        ↓
HarnessでTest / Verify
        ↓
Knowledgeを更新
```

つまり、2026年の世界的な潮流は、

> **SDDからAgentic Engineeringへ。**

ただしSDDが消えるわけではありません。

Specは、AIへすべてを教える巨大文書から、**人間とAgentがIntentとAcceptance Criteriaを共有するLightweight Agreement Layer**へ役割を変えます。

実装方法論はSkillsへ移ります。

長期KnowledgeはLLM Wiki、Repository Knowledge、OKFへ移ります。

重要な判断理由はADRへ残ります。

実装・Test・ReviewはAgent Harnessへ移ります。

そして、開発で得たKnowledgeが次の開発Contextへ戻るKnowledge Loopが形成されます。

最終的には、

```text
Human
  ↓
Intent
  ↓
Light Spec
  ↓
Agent
  ↓
Skills + Knowledge + Tools
  ↓
Harness
  ↓
Code / Test / Review
  ↓
Knowledge Update
  ↓
Next Development
```

という構造になります。

この観点から見ると、

> **OpenSpecで「What」を合意し、Superpowersで「How」を標準化し、LLM Wiki / OKFで「What We Know」を育て、Agent Harnessで「Execute & Verify」する。**

という構成は、単なるツール選定ではなく、2026年の世界的なAgentic Engineeringの流れをOSS / Open Standardで表現したReference Architectureと考えることができます。

---

## 参考資料

### 日本 / SDDの現在地

- 仕様駆動開発の消費期限 — watany / Speaker Deck  
  https://speakerdeck.com/watany/expiration-date-of-sdd

### 米国

- Harness engineering: leveraging Codex in an agent-first world — OpenAI  
  https://openai.com/index/harness-engineering/

- Claude Code: Foundations — Anthropic  
  https://www.anthropic.com/webinars/claude-code-foundations

- Trustworthy agents in practice — Anthropic  
  https://www.anthropic.com/research/trustworthy-agents

- Agentic SDD — GitHub Spec Kit  
  https://github.github.com/spec-kit/reference/agentic-sdd.html

- Spec Kit Reference  
  https://github.github.com/spec-kit/reference/overview.html

### Knowledge / Open Standard

- Introducing the Open Knowledge Format — Google Cloud  
  https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/

- Open Knowledge Format v0.2 tackles agentic trust — Google Cloud  
  https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/

### 中国

- Qoder Spec-driven Development  
  https://docs.qoder.com/user-guide/quest/spec-driven

- Qoder Repo Wiki  
  https://docs.qoder.com/ja/user-guide/repo-wiki

- Qoder Knowledge Cards  
  https://docs.qoder.com/user-guide/knowledge-engine/knowledge-cards

- A Self-Iterating Knowledge Engine for AI-Native Software Engineering — Qoder  
  https://qoder.com/en/blog/qoder-knowledge-engine

- Tencent CodeBuddy Project Rules  
  https://staging-codebuddy.tencent.com/docs/ide/User-guide/Rules

---

## 関連キーワード

`Agentic Engineering` `Spec-Driven Development` `SDD` `OpenSpec` `Superpowers` `Agent Skills` `LLM Wiki` `Open Knowledge Format` `OKF` `Repository Knowledge` `Knowledge Cards` `ADR` `Agent Harness` `Context Engineering` `Knowledge Loop` `Codex` `Claude Code` `Qoder` `CodeBuddy`
