#!/usr/bin/env python3
"""PRD JSONまたはMarkdown内の曖昧表現を検出する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import AMBIGUOUS_TERMS, find_terms, has_measurement_hint, load_json


def detect_in_json(data: dict[str, Any]) -> list[dict[str, str]]:
    """JSON内の曖昧語を検出し、数値条件の有無も返す。"""
    findings = find_terms(data, AMBIGUOUS_TERMS)
    for finding in findings:
        finding["qualified"] = "yes" if has_measurement_hint(finding["text"]) else "no"
    return findings


def detect_in_text(text: str) -> list[dict[str, str]]:
    """Markdownなどのプレーンテキストから曖昧語を検出する。"""
    findings: list[dict[str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for term in AMBIGUOUS_TERMS:
            if term in line:
                findings.append(
                    {
                        "path": f"line:{line_no}",
                        "term": term,
                        "text": line.strip(),
                        "qualified": "yes" if has_measurement_hint(line) else "no",
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="曖昧表現を検出します。")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    if args.input.suffix.lower() == ".json":
        try:
            findings = detect_in_json(load_json(args.input))
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"エラー: JSON形式が不正です: {exc}")
            return 2
    else:
        findings = detect_in_text(args.input.read_text(encoding="utf-8"))

    if not findings:
        print("曖昧表現は検出されませんでした。")
        return 0

    for finding in findings:
        print(
            f"- {finding['path']}: {finding['term']} "
            f"(数値・条件あり={finding['qualified']}) | {finding['text']}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
