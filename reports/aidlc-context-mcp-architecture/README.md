# AI-DLC v2 × Context MCP Architecture

AI-DLC v2、GitHub、AgentCore Memory、Bedrock Knowledge Base、S3、MCPを組み合わせたAI駆動開発・Context管理基盤の構想資料です。

## Files

- [`ARCHITECTURE_REPORT.md`](./ARCHITECTURE_REPORT.md): 構想レポート
- [`architecture.png`](./architecture.png): 全体アーキテクチャ図

## Core concept

- AgentCore Memory: 個人・担当者の記憶
- AI-DLC v2 + GitHub: プロジェクト固有の知識・状態
- Bedrock Knowledge Base: チーム・組織の知識
- S3: 原文・正式文書・監査証跡の正本
- MCP / AgentCore Gateway: Contextと機能へのアクセス層
- Context Assembler: 必要なContextの選択・統合・優先順位制御
