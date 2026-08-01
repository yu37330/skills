#!/usr/bin/env python3
"""改善前後PPTXの内容・ノート・グラフデータを機械比較する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_pptx import audit_pptx


FIELDS = {
    "title": "タイトル",
    "content_inventory_sha256": "本文文字在庫",
    "numbers": "数値",
    "source_lines": "出典",
    "proper_terms": "固有語・略語",
    "notes_sha256": "発表者ノート",
    "chart_data_sha256": "グラフデータ",
}


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def compare(before: dict, after: dict) -> dict:
    differences: list[dict] = []
    if before["slide_count"] != after["slide_count"]:
        differences.append({"scope": "deck", "field": "slide_count", "before": before["slide_count"], "after": after["slide_count"]})
    for index in range(min(before["slide_count"], after["slide_count"])):
        left, right = before["slides"][index], after["slides"][index]
        for field, label in FIELDS.items():
            if left.get(field) != right.get(field):
                differences.append({
                    "scope": "slide",
                    "slide_number": index + 1,
                    "field": field,
                    "label": label,
                    "before": left.get(field),
                    "after": right.get(field),
                })
    return {
        "version": 1,
        "before_pptx_sha256": before["source_pptx_sha256"],
        "after_pptx_sha256": after["source_pptx_sha256"],
        "preservation_pass": not differences,
        "differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTX内容Diffを作成します")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = compare(audit_pptx(args.before), audit_pptx(args.after))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PPTX内容Diffを作成しました: {args.output}")
    return 0 if report["preservation_pass"] else 1


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
