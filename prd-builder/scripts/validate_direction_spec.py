#!/usr/bin/env python3
"""Direction Spec JSONをSchemaと意味ルールで検証する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    print("エラー: jsonschema が必要です。pip install -r requirements.txt を実行してください。")
    sys.exit(2)

from common import load_json, scope_overlaps, unique_ids


def schema_errors(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """JSON Schema違反を読みやすい文字列で返す。"""
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "(root)"
        errors.append(f"{location}: {error.message}")
    return errors


def semantic_findings(
    data: dict[str, Any],
    *,
    allow_unapproved: bool = False,
    allow_blocking: bool = False,
) -> tuple[list[str], list[str]]:
    """Schemaでは表現しにくい整合性違反と警告を返す。"""
    blockers: list[str] = []
    warnings: list[str] = []

    if not allow_unapproved and data.get("approval_status") != "approved":
        blockers.append("approval_statusがapprovedではありません。")

    blocking_questions = [
        item.get("id", "(IDなし)")
        for item in data.get("open_questions", [])
        if isinstance(item, dict) and item.get("blocking") is True
    ]
    if blocking_questions and not allow_blocking:
        blockers.append("Blockingな未決事項があります: " + ", ".join(blocking_questions))

    overlaps = scope_overlaps(data.get("scope", []), data.get("out_of_scope", []))
    if overlaps:
        blockers.append("scopeとout_of_scopeが重複しています: " + ", ".join(overlaps))

    ok, duplicates = unique_ids(
        [item for item in data.get("sources", []) if isinstance(item, dict)],
        field="source_id",
    )
    if not ok:
        blockers.append("source_idが重複しています: " + ", ".join(duplicates))

    if len(str(data.get("problem_statement", ""))) < 35:
        warnings.append("problem_statementが短く、損失や発生状況が十分でない可能性があります。")

    if not data.get("decision_owner"):
        warnings.append("decision_ownerが未設定です。正式運用では決定責任者を指定してください。")

    if not data.get("decision_date"):
        warnings.append("decision_dateが未設定です。正式運用では決定日を指定してください。")

    return blockers, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Direction Specを検証します。")
    parser.add_argument("direction_spec", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "templates" / "direction-spec.schema.json",
    )
    parser.add_argument("--allow-unapproved", action="store_true")
    parser.add_argument("--allow-blocking", action="store_true")
    args = parser.parse_args()

    try:
        data = load_json(args.direction_spec)
        schema = load_json(args.schema)
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"エラー: JSON形式が不正です: {exc}")
        return 2

    errors = schema_errors(data, schema)
    blockers, warnings = semantic_findings(
        data,
        allow_unapproved=args.allow_unapproved,
        allow_blocking=args.allow_blocking,
    )

    if errors:
        print("不合格: Direction SpecがSchemaに準拠していません。")
        for error in errors:
            print(f"- {error}")
    for blocker in blockers:
        print(f"- 重大: {blocker}")
    for warning in warnings:
        print(f"- 警告: {warning}")

    if errors or blockers:
        return 1

    print("合格: Direction SpecのSchema、承認状態、整合性を確認しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
