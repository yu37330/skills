#!/usr/bin/env python3
"""Direction Specから情報欠落のないPRD骨格を作成する。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import dump_json, load_json


def _slug(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    return value or "PRODUCT"


def _normalize_users(users: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, user in enumerate(users, start=1):
        if isinstance(user, dict):
            result.append(
                {
                    "id": user.get("id", f"USR-{index:03d}"),
                    "name": user.get("name", ""),
                    "needs": list(user.get("needs", [])),
                }
            )
        else:
            result.append({"id": f"USR-{index:03d}", "name": str(user), "needs": []})
    return result


def build_prd_skeleton(direction_spec: dict[str, Any]) -> dict[str, Any]:
    """Direction Specの決定情報を保持したPRD骨格を返す。"""
    product_name = direction_spec.get("product_name") or direction_spec["project_name"]
    now = datetime.now(timezone.utc).isoformat()
    source_ids = [
        source["source_id"]
        for source in direction_spec.get("sources", [])
        if isinstance(source, dict) and source.get("source_id")
    ]
    questions = []
    for index, question in enumerate(direction_spec.get("open_questions", []), start=1):
        questions.append(
            {
                "id": question.get("id", f"Q-{index:03d}"),
                "question": question.get("question", ""),
                "blocking": bool(question.get("blocking", False)),
                "owner": question.get("owner", ""),
                "due_date": question.get("due_date"),
                "source_ids": list(question.get("source_ids", [])),
            }
        )

    return {
        "metadata": {
            "schema_version": "2.0.0",
            "prd_id": f"PRD-{_slug(str(product_name))}",
            "project_name": direction_spec["project_name"],
            "product_name": product_name,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
        "executive_summary": "",
        "background": "",
        "problem_statement": direction_spec["problem_statement"],
        "product_goal": "",
        "target_users": _normalize_users(direction_spec["target_users"]),
        "user_needs": [],
        "value_proposition": "",
        "desired_outcomes": list(direction_spec["desired_outcomes"]),
        "selected_direction": direction_spec["selected_direction"],
        "decision_rationale": direction_spec["decision_rationale"],
        "scope": list(direction_spec["scope"]),
        "out_of_scope": list(direction_spec["out_of_scope"]),
        "user_scenarios": [],
        "functional_requirements": [],
        "non_functional_requirements": [],
        "data_requirements": [],
        "ai_requirements": {
            "applicable": False,
            "inputs": [],
            "outputs": [],
            "quality_evaluation": [],
            "error_handling": [],
            "human_in_the_loop": [],
            "evidence": [],
        },
        "security_compliance": [],
        "dependencies": [],
        "constraints": list(direction_spec.get("constraints", [])),
        "assumptions": list(direction_spec.get("assumptions", [])),
        "risks": list(direction_spec.get("risks", [])),
        "release_strategy": [],
        "success_metrics": [],
        "open_questions": questions,
        "decision_log": [
            {
                "id": "DEC-001",
                "decision": direction_spec["selected_direction"],
                "rationale": direction_spec["decision_rationale"],
                "owner": direction_spec.get("decision_owner", ""),
                "date": direction_spec.get("decision_date"),
                "source_ids": source_ids,
            }
        ],
        "traceability": [],
        "sources": list(direction_spec["sources"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Direction SpecからPRD骨格を作成します。")
    parser.add_argument("direction_spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        direction_spec = load_json(args.direction_spec)
        prd = build_prd_skeleton(direction_spec)
        dump_json(args.output, prd)
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"エラー: Direction SpecからPRDを作成できません: {exc}")
        return 2

    print(f"PRD骨格を作成しました: {args.output}")
    print("注意: 空欄、要求、成功指標を補完してからQuality Gateを実行してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
