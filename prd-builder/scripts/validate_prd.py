#!/usr/bin/env python3
"""PRD JSONをSchemaと基本整合性ルールで検証する。"""

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

from common import all_requirements, load_json, scope_overlaps, unique_ids


def schema_errors(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """JSON Schema違反を一覧化する。"""
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "(root)"
        errors.append(f"{location}: {error.message}")
    return errors


def semantic_errors(data: dict[str, Any]) -> list[str]:
    """ID重複とスコープ矛盾を検査する。"""
    errors: list[str] = []

    overlaps = scope_overlaps(data.get("scope", []), data.get("out_of_scope", []))
    if overlaps:
        errors.append("scopeとout_of_scopeが重複しています: " + ", ".join(overlaps))

    groups = [
        (all_requirements(data), "要求ID"),
        ([item for item in data.get("success_metrics", []) if isinstance(item, dict)], "Metric ID"),
        ([item for item in data.get("risks", []) if isinstance(item, dict)], "Risk ID"),
        ([item for item in data.get("open_questions", []) if isinstance(item, dict)], "Question ID"),
        ([item for item in data.get("decision_log", []) if isinstance(item, dict)], "Decision ID"),
    ]
    for items, label in groups:
        ok, duplicates = unique_ids(items)
        if not ok:
            errors.append(f"{label}が重複しています: {', '.join(duplicates)}")

    ok, duplicates = unique_ids(
        [item for item in data.get("sources", []) if isinstance(item, dict)],
        field="source_id",
    )
    if not ok:
        errors.append("source_idが重複しています: " + ", ".join(duplicates))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="PRD JSONを検証します。")
    parser.add_argument("prd", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "templates" / "prd.schema.json",
    )
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
        schema = load_json(args.schema)
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"エラー: JSON形式が不正です: {exc}")
        return 2

    errors = schema_errors(prd, schema)
    errors.extend(semantic_errors(prd))
    if errors:
        print("不合格: PRDに形式または整合性の問題があります。")
        for error in errors:
            print(f"- {error}")
        return 1

    print("合格: PRDはSchemaと基本整合性ルールに準拠しています。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
