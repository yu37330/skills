# Scope Definition Rules

## In Scope

今回のリリースで提供する能力、対象データ、対象利用者、対象業務を記載する。

## Out of Scope

今回扱わない能力、データ、利用者、地域、言語、運用範囲を明記する。

## 検査ルール

- In ScopeとOut of Scopeに同一内容を含めない
- 「その他」「必要なものすべて」のような無制限表現を避ける
- 技術部品名だけでスコープを定義しない
- 将来候補はOut of ScopeまたはRelease Strategyへ分離する
- Won't要求とOut of Scopeの内容を整合させる

## 変更ルール

採用方向に影響するスコープ変更は、PRDだけで確定せずDirection Specの再承認へ戻す。
