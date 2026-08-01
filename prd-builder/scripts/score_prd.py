#!/usr/bin/env python3
"""構造化PRDを100点モデルで採点する。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from check_traceability import check_traceability
from common import (
    AMBIGUOUS_TERMS,
    TBD_TERMS,
    all_requirements,
    find_terms,
    has_measurement_hint,
    load_json,
    normalize_text,
    scope_overlaps,
)

CATEGORY_WEIGHTS = {
    "問題と背景の明確性": 10,
    "対象ユーザーの明確性": 10,
    "提供価値の明確性": 10,
    "スコープの明確性": 10,
    "対象外の明確性": 5,
    "成功指標の測定可能性": 10,
    "機能要求の明確性": 10,
    "非機能要求の明確性": 10,
    "制約・依存関係": 5,
    "リスクと前提": 5,
    "意思決定の根拠": 5,
    "出典トレーサビリティ": 10,
}


def _ratio_score(valid: int, total: int, weight: int) -> int:
    if total <= 0:
        return 0
    return round(weight * valid / total)


def _contains_unqualified_ambiguity(value: str) -> bool:
    return any(term in value for term in AMBIGUOUS_TERMS) and not has_measurement_hint(value)


def _contains_tbd(value: Any) -> bool:
    text = str(value)
    return any(term.lower() in text.lower() for term in TBD_TERMS)


def score_prd(
    prd: dict[str, Any],
    direction_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """PRDの点数、重大問題、改善指摘を返す。"""
    scores: dict[str, int] = {}
    findings: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    # 1. 問題と背景
    problem_score = 0
    if len(str(prd.get("problem_statement", ""))) >= 35:
        problem_score += 5
    else:
        findings.append("problem_statementに発生状況と損失を追加してください。")
    if len(str(prd.get("background", ""))) >= 30:
        problem_score += 3
    else:
        findings.append("backgroundが短く、現状説明が不足しています。")
    if len(str(prd.get("product_goal", ""))) >= 20 and not _contains_unqualified_ambiguity(str(prd.get("product_goal", ""))):
        problem_score += 2
    else:
        findings.append("product_goalを測定可能または具体的な状態で記載してください。")
    scores["問題と背景の明確性"] = problem_score

    # 2. 対象ユーザー
    users = [item for item in prd.get("target_users", []) if isinstance(item, dict)]
    user_score = 0
    if users:
        user_score += 4
        if all(str(item.get("name", "")).strip() for item in users):
            user_score += 3
        if all(item.get("needs") for item in users) and prd.get("user_needs"):
            user_score += 3
        else:
            findings.append("対象ユーザーごとのneedsを明記してください。")
    else:
        findings.append("target_usersが定義されていません。")
    scores["対象ユーザーの明確性"] = user_score

    # 3. 提供価値
    value_score = 0
    if len(str(prd.get("value_proposition", ""))) >= 25:
        value_score += 5
    else:
        findings.append("value_propositionを具体化してください。")
    outcomes = prd.get("desired_outcomes", [])
    if outcomes and all(len(str(item)) >= 8 for item in outcomes):
        value_score += 5
    else:
        findings.append("desired_outcomesを具体化してください。")
    scores["提供価値の明確性"] = value_score

    # 4, 5. スコープ
    scope = prd.get("scope", [])
    out_scope = prd.get("out_of_scope", [])
    overlaps = scope_overlaps(scope, out_scope)
    scope_score = 6 if scope and all(len(str(item)) >= 8 for item in scope) else 0
    if not scope_score:
        findings.append("scopeを具体的な対象能力として記載してください。")
    if not overlaps:
        scope_score += 4
    else:
        blockers.append("scopeとout_of_scopeが重複しています: " + ", ".join(overlaps))
    scores["スコープの明確性"] = scope_score
    out_scope_score = 5 if out_scope and not overlaps else 0
    if not out_scope:
        findings.append("out_of_scopeを明記してください。")
    scores["対象外の明確性"] = out_scope_score

    # 6. 成功指標
    metrics = [item for item in prd.get("success_metrics", []) if isinstance(item, dict)]
    valid_metrics = 0
    for metric in metrics:
        metric_id = metric.get("id", "(IDなし)")
        target = metric.get("target")
        measurement = str(metric.get("measurement", ""))
        valid = (
            bool(metric.get("metric"))
            and not _contains_tbd(target)
            and not _contains_tbd(measurement)
            and has_measurement_hint(target)
            and len(measurement) >= 10
            and bool(metric.get("frequency"))
            and bool(metric.get("owner"))
            and bool(metric.get("source_ids"))
            and not _contains_unqualified_ambiguity(str(target))
            and not _contains_unqualified_ambiguity(measurement)
        )
        if valid:
            valid_metrics += 1
        else:
            blockers.append(f"{metric_id}: 成功指標が測定可能ではありません。")
    scores["成功指標の測定可能性"] = _ratio_score(valid_metrics, len(metrics), 10)

    # 7. 機能要求
    functional = [item for item in prd.get("functional_requirements", []) if isinstance(item, dict)]
    valid_functional = 0
    for requirement in functional:
        rid = requirement.get("id", "(IDなし)")
        text = str(requirement.get("requirement", ""))
        valid = (
            bool(re.fullmatch(r"FR-[0-9]{3}", str(rid)))
            and len(text) >= 20
            and len(str(requirement.get("rationale", ""))) >= 10
            and bool(requirement.get("direction_refs"))
            and bool(requirement.get("source_ids"))
            and not _contains_tbd(text)
            and not _contains_unqualified_ambiguity(text)
        )
        if valid:
            valid_functional += 1
        else:
            findings.append(f"{rid}: 機能要求を具体化し、根拠と測定条件を追加してください。")
        if _contains_tbd(text):
            blockers.append(f"{rid}: 主要要求に未確定表現があります。")
        if requirement.get("priority") == "Must" and _contains_unqualified_ambiguity(text):
            blockers.append(f"{rid}: Must要求に未修飾の曖昧表現があります。")
    scores["機能要求の明確性"] = _ratio_score(valid_functional, len(functional), 10)

    # 8. 非機能要求
    non_functional = [item for item in prd.get("non_functional_requirements", []) if isinstance(item, dict)]
    valid_non_functional = 0
    for requirement in non_functional:
        rid = requirement.get("id", "(IDなし)")
        text = str(requirement.get("requirement", ""))
        measurement = str(requirement.get("measurement", ""))
        target = requirement.get("target")
        valid = (
            bool(re.fullmatch(r"NFR-[0-9]{3}", str(rid)))
            and bool(requirement.get("category"))
            and len(text) >= 20
            and len(measurement) >= 10
            and has_measurement_hint(target)
            and bool(requirement.get("direction_refs"))
            and bool(requirement.get("source_ids"))
            and not _contains_tbd(text + measurement + str(target))
            and not _contains_unqualified_ambiguity(text + measurement + str(target))
        )
        if valid:
            valid_non_functional += 1
        else:
            findings.append(f"{rid}: 非機能要求の測定方法と目標値を具体化してください。")
        if _contains_tbd(text + measurement + str(target)):
            blockers.append(f"{rid}: 非機能要求に未確定表現があります。")
    scores["非機能要求の明確性"] = _ratio_score(valid_non_functional, len(non_functional), 10)

    # 9. 制約・依存関係
    constraint_score = 0
    if "constraints" in prd:
        constraint_score += 3
        if not prd.get("constraints"):
            warnings.append("constraintsは評価済みの空配列です。制約なしの根拠をレビューしてください。")
    if "dependencies" in prd:
        constraint_score += 2
        if not prd.get("dependencies"):
            warnings.append("dependenciesは評価済みの空配列です。依存関係なしの根拠をレビューしてください。")
    scores["制約・依存関係"] = constraint_score

    # 10. リスクと前提
    risk_score = 0
    if "assumptions" in prd:
        risk_score += 2
    if "risks" in prd:
        risk_score += 3
    scores["リスクと前提"] = risk_score

    # 11. 意思決定の根拠
    decision_score = 0
    if len(str(prd.get("selected_direction", ""))) >= 15:
        decision_score += 2
    if len(str(prd.get("decision_rationale", ""))) >= 15:
        decision_score += 2
    if prd.get("decision_log"):
        decision_score += 1
    scores["意思決定の根拠"] = decision_score

    if direction_spec is not None:
        if direction_spec.get("approval_status") != "approved":
            blockers.append("Direction Specがapprovedではありません。")
        if normalize_text(prd.get("selected_direction", "")) != normalize_text(direction_spec.get("selected_direction", "")):
            blockers.append("PRDのselected_directionがDirection Specと一致しません。")
        blocking_questions = [
            item.get("id", "(IDなし)")
            for item in direction_spec.get("open_questions", [])
            if isinstance(item, dict) and item.get("blocking") is True
        ]
        if blocking_questions:
            blockers.append("Direction SpecにBlockingな未決事項があります: " + ", ".join(blocking_questions))

    # 12. トレーサビリティ
    trace_errors, trace_warnings, stats = check_traceability(prd, direction_spec)
    blockers.extend(trace_errors)
    warnings.extend(trace_warnings)
    total_requirements = stats["requirements"]
    covered = stats["requirements_with_traceability"]
    trace_score = _ratio_score(covered, total_requirements, 10)
    if trace_errors:
        trace_score = min(trace_score, 5)
    scores["出典トレーサビリティ"] = trace_score

    # 全体の曖昧語とTBDを追加検査する。
    ambiguous = find_terms(prd, AMBIGUOUS_TERMS)
    for item in ambiguous:
        if not has_measurement_hint(item["text"]):
            warnings.append(f"曖昧表現: {item['path']} | {item['term']}")
    tbd = find_terms(prd, TBD_TERMS)
    for item in tbd:
        # open_questionsの質問文自体は未確定内容を管理する場所なので、重大扱いしない。
        if ".open_questions[" not in item["path"]:
            blockers.append(f"未確定表現: {item['path']} | {item['term']}")

    # 重複を除き、順序を保つ。
    blockers = list(dict.fromkeys(blockers))
    findings = list(dict.fromkeys(findings))
    warnings = list(dict.fromkeys(warnings))

    score = sum(scores.values())
    if blockers:
        status = "rejected"
    elif score >= 90:
        status = "passed"
    elif score >= 80:
        status = "conditional"
    else:
        status = "rejected"

    return {
        "score": score,
        "status": status,
        "category_scores": scores,
        "blockers": blockers,
        "findings": findings,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PRD JSONを100点モデルで採点します。")
    parser.add_argument("prd", type=Path)
    parser.add_argument("--direction-spec", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
        direction_spec = load_json(args.direction_spec) if args.direction_spec else None
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"エラー: JSON形式が不正です: {exc}")
        return 2

    result = score_prd(prd, direction_spec)
    print(f"PRD Score: {result['score']}/100")
    for category, score in result["category_scores"].items():
        print(f"- {category}: {score}/{CATEGORY_WEIGHTS[category]}")
    for blocker in result["blockers"]:
        print(f"- 重大: {blocker}")
    for finding in result["findings"]:
        print(f"- 改善: {finding}")
    for warning in result["warnings"]:
        print(f"- 警告: {warning}")
    print(f"判定: {result['status']}")

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
