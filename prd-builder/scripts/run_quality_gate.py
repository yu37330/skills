#!/usr/bin/env python3
"""PRDのSchema、整合性、トレーサビリティ、100点採点を一括実行する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import dump_json, load_json
from score_prd import CATEGORY_WEIGHTS, score_prd
from validate_direction_spec import schema_errors as direction_schema_errors
from validate_direction_spec import semantic_findings as direction_semantic_findings
from validate_prd import schema_errors as prd_schema_errors
from validate_prd import semantic_errors as prd_semantic_errors


def _render_report(result: dict[str, Any]) -> str:
    category_rows = [
        f"| {category} | {score} | {CATEGORY_WEIGHTS[category]} |"
        for category, score in result["category_scores"].items()
    ]
    blockers = "\n".join(f"- {item}" for item in result["blockers"]) or "- なし"
    findings = "\n".join(f"- {item}" for item in result["findings"]) or "- なし"
    warnings = "\n".join(f"- {item}" for item in result["warnings"]) or "- なし"
    return (
        "# PRD Review Report\n\n"
        f"- 判定: **{result['status']}**\n"
        f"- Score: **{result['score']} / 100**\n"
        f"- PRD Schema: **{'pass' if not result['prd_schema_errors'] else 'fail'}**\n"
        f"- Direction Spec: **{'pass' if not result['direction_errors'] else 'fail'}**\n\n"
        "## Category Scores\n\n"
        "| Category | Score | Max |\n|---|---:|---:|\n"
        + "\n".join(category_rows)
        + "\n\n## Blockers\n\n"
        + blockers
        + "\n\n## Findings\n\n"
        + findings
        + "\n\n## Warnings\n\n"
        + warnings
        + "\n"
    )


def run_gate(
    prd: dict[str, Any],
    prd_schema: dict[str, Any],
    direction_spec: dict[str, Any] | None = None,
    direction_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """一括検証結果を返す。"""
    prd_errors = prd_schema_errors(prd, prd_schema)
    prd_errors.extend(prd_semantic_errors(prd))

    direction_errors: list[str] = []
    direction_warnings: list[str] = []
    if direction_spec is not None and direction_schema is not None:
        direction_errors.extend(direction_schema_errors(direction_spec, direction_schema))
        blockers, warnings = direction_semantic_findings(direction_spec)
        direction_errors.extend(blockers)
        direction_warnings.extend(warnings)

    score_result = score_prd(prd, direction_spec)
    blockers = list(score_result["blockers"])
    blockers.extend(f"PRD Schema: {item}" for item in prd_errors)
    blockers.extend(f"Direction Spec: {item}" for item in direction_errors)
    blockers = list(dict.fromkeys(blockers))

    if blockers:
        status = "rejected"
    else:
        status = score_result["status"]

    return {
        **score_result,
        "status": status,
        "blockers": blockers,
        "warnings": list(dict.fromkeys(score_result["warnings"] + direction_warnings)),
        "prd_schema_errors": prd_errors,
        "direction_errors": direction_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PRD Quality Gateを一括実行します。")
    parser.add_argument("prd", type=Path)
    parser.add_argument("--direction-spec", type=Path)
    parser.add_argument(
        "--prd-schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "templates" / "prd.schema.json",
    )
    parser.add_argument(
        "--direction-schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "templates" / "direction-spec.schema.json",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--allow-conditional", action="store_true")
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
        prd_schema = load_json(args.prd_schema)
        direction_spec = load_json(args.direction_spec) if args.direction_spec else None
        direction_schema = load_json(args.direction_schema) if args.direction_spec else None
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"エラー: JSON形式が不正です: {exc}")
        return 2

    result = run_gate(prd, prd_schema, direction_spec, direction_schema)
    print(f"PRD Quality Gate: {result['status']} ({result['score']}/100)")
    for blocker in result["blockers"]:
        print(f"- 重大: {blocker}")
    for finding in result["findings"]:
        print(f"- 改善: {finding}")
    for warning in result["warnings"]:
        print(f"- 警告: {warning}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(_render_report(result), encoding="utf-8")
    if args.report_json:
        dump_json(args.report_json, result)

    if result["status"] == "passed":
        return 0
    if result["status"] == "conditional" and args.allow_conditional:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
