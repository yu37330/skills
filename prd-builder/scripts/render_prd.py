#!/usr/bin/env python3
"""prd.jsonから人間レビュー用のprd.mdを生成する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import load_json


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")


def _bullets(items: list[Any]) -> str:
    if not items:
        return "- なし"
    return "\n".join(f"- {_escape(item)}" for item in items)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(_escape(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_prd(prd: dict[str, Any]) -> str:
    """PRDをMarkdownへ変換する。"""
    metadata = prd["metadata"]
    lines: list[str] = [
        f"# PRD: {_escape(metadata['product_name'])}",
        "",
        "> このMarkdownは`prd.json`から自動生成しています。直接編集しないでください。",
        "",
        f"- PRD ID: `{_escape(metadata['prd_id'])}`",
        f"- Status: `{_escape(metadata['status'])}`",
        f"- Schema Version: `{_escape(metadata['schema_version'])}`",
    ]

    def section(number: int, title: str, body: str) -> None:
        lines.extend(["", f"## {number}. {title}", "", body or "未記載"])

    section(1, "Executive Summary", prd.get("executive_summary", ""))
    section(2, "Background", prd.get("background", ""))
    section(3, "Problem Statement", prd.get("problem_statement", ""))
    section(4, "Product Goal", prd.get("product_goal", ""))

    users = [
        [item.get("id"), item.get("name"), " / ".join(item.get("needs", []))]
        for item in prd.get("target_users", [])
    ]
    section(5, "Target Users", _table(["ID", "User", "Needs"], users))
    section(6, "User Needs", _bullets(prd.get("user_needs", [])))
    section(7, "Value Proposition", prd.get("value_proposition", ""))
    section(8, "Desired Outcomes", _bullets(prd.get("desired_outcomes", [])))
    section(
        9,
        "Selected Direction and Rationale",
        f"**Selected Direction**\n\n{prd.get('selected_direction', '')}\n\n"
        f"**Decision Rationale**\n\n{prd.get('decision_rationale', '')}",
    )

    metric_rows = [
        [
            item.get("id"), item.get("metric"), item.get("baseline"), item.get("target"),
            item.get("measurement"), item.get("frequency"), item.get("owner"),
            ", ".join(item.get("source_ids", [])),
        ]
        for item in prd.get("success_metrics", [])
    ]
    section(
        10,
        "Success Metrics",
        _table(["ID", "Metric", "Baseline", "Target", "Measurement", "Frequency", "Owner", "Source"], metric_rows),
    )
    section(11, "Scope", _bullets(prd.get("scope", [])))
    section(12, "Out of Scope", _bullets(prd.get("out_of_scope", [])))

    scenario_rows = [
        [item.get("id"), item.get("actor"), item.get("situation"), item.get("goal"), item.get("outcome")]
        for item in prd.get("user_scenarios", [])
    ]
    section(13, "User Scenarios", _table(["ID", "Actor", "Situation", "Goal", "Outcome"], scenario_rows))

    fr_rows = [
        [
            item.get("id"), item.get("priority"), item.get("status"), item.get("requirement"),
            item.get("rationale"), ", ".join(item.get("direction_refs", [])),
            ", ".join(item.get("source_ids", [])),
        ]
        for item in prd.get("functional_requirements", [])
    ]
    section(14, "Functional Requirements", _table(["ID", "Priority", "Status", "Requirement", "Rationale", "Direction", "Source"], fr_rows))

    nfr_rows = [
        [
            item.get("id"), item.get("category"), item.get("status"), item.get("requirement"),
            item.get("measurement"), item.get("target"), ", ".join(item.get("direction_refs", [])),
            ", ".join(item.get("source_ids", [])),
        ]
        for item in prd.get("non_functional_requirements", [])
    ]
    section(15, "Non-functional Requirements", _table(["ID", "Category", "Status", "Requirement", "Measurement", "Target", "Direction", "Source"], nfr_rows))
    section(16, "Data Requirements", _bullets(prd.get("data_requirements", [])))

    ai = prd.get("ai_requirements", {})
    ai_body = "\n".join(
        [
            f"- Applicable: `{ai.get('applicable', False)}`",
            "",
            "### Inputs",
            _bullets(ai.get("inputs", [])),
            "",
            "### Outputs",
            _bullets(ai.get("outputs", [])),
            "",
            "### Quality Evaluation",
            _bullets(ai.get("quality_evaluation", [])),
            "",
            "### Error Handling",
            _bullets(ai.get("error_handling", [])),
            "",
            "### Human-in-the-loop",
            _bullets(ai.get("human_in_the_loop", [])),
            "",
            "### Explainability / Evidence",
            _bullets(ai.get("evidence", [])),
        ]
    )
    section(17, "AI-specific Requirements", ai_body)
    section(18, "Security and Compliance", _bullets(prd.get("security_compliance", [])))
    section(19, "Dependencies", _bullets(prd.get("dependencies", [])))
    section(20, "Constraints", _bullets(prd.get("constraints", [])))
    section(21, "Assumptions", _bullets(prd.get("assumptions", [])))

    risk_rows = [
        [item.get("id"), item.get("risk"), item.get("impact"), item.get("likelihood"), item.get("mitigation"), ", ".join(item.get("source_ids", []))]
        for item in prd.get("risks", [])
    ]
    section(22, "Risks", _table(["ID", "Risk", "Impact", "Likelihood", "Mitigation", "Source"], risk_rows))
    section(23, "Release Strategy", _bullets(prd.get("release_strategy", [])))

    question_rows = [
        [item.get("id"), item.get("question"), item.get("blocking"), item.get("owner"), item.get("due_date"), ", ".join(item.get("source_ids", []))]
        for item in prd.get("open_questions", [])
    ]
    section(24, "Open Questions", _table(["ID", "Question", "Blocking", "Owner", "Due Date", "Source"], question_rows))

    decision_rows = [
        [item.get("id"), item.get("decision"), item.get("rationale"), item.get("owner"), item.get("date"), ", ".join(item.get("source_ids", []))]
        for item in prd.get("decision_log", [])
    ]
    section(25, "Decision Log", _table(["ID", "Decision", "Rationale", "Owner", "Date", "Source"], decision_rows))

    trace_rows = [
        [item.get("requirement_id"), ", ".join(item.get("direction_refs", [])), ", ".join(item.get("source_ids", [])), item.get("evidence"), item.get("confidence")]
        for item in prd.get("traceability", [])
    ]
    section(26, "Source Traceability", _table(["Requirement ID", "Direction Spec", "Source", "Evidence", "Confidence"], trace_rows))

    source_rows = [
        [item.get("source_id"), item.get("source_type"), item.get("status"), item.get("authority"), item.get("confidence"), item.get("source_uri"), item.get("evidence_location")]
        for item in prd.get("sources", [])
    ]
    section(27, "Sources", _table(["Source ID", "Type", "Status", "Authority", "Confidence", "URI", "Location"], source_rows))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="prd.jsonからprd.mdを生成します。")
    parser.add_argument("prd", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
        markdown = render_prd(prd)
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"エラー: PRDをMarkdownへ変換できません: {exc}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"PRD Markdownを生成しました: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
