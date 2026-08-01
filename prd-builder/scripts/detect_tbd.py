#!/usr/bin/env python3
"""PRD JSONまたはMarkdown内のTBD表現を検出する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import TBD_TERMS, find_terms, load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="TBD、TODO、未定、要確認を検出します。")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    if args.input.suffix.lower() == ".json":
        try:
            findings = find_terms(load_json(args.input), TBD_TERMS)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"エラー: JSON形式が不正です: {exc}")
            return 2
    else:
        text = args.input.read_text(encoding="utf-8")
        findings = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            for term in TBD_TERMS:
                if term.lower() in line.lower():
                    findings.append({"path": f"line:{line_no}", "term": term, "text": line.strip()})

    if not findings:
        print("未確定表現は検出されませんでした。")
        return 0

    for finding in findings:
        print(f"- {finding['path']}: {finding['term']} | {finding['text']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
