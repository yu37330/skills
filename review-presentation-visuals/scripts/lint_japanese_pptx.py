#!/usr/bin/env python3
"""日本語PPTで機械判定可能な改行・文字サイズ問題を検出する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from audit_pptx import audit_pptx


JP_CHAR = re.compile(r"[一-龯ぁ-んァ-ヶ々〆ヵヶ]")
BAD_LINE_START = re.compile(r"^[、。，．・：；？！）］｝】』」〉》〕％%]" )
NUMBER_ONLY_END = re.compile(r"^\s*[-+]?\d[\d,]*(?:\.\d+)?\s*$")
UNIT_START = re.compile(r"^(?:%|％|円|人|社|件|年|月|日|倍|ポイント|pt|GB|MB|TB)")


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def lint(report: dict, min_font_size: float, source_min_font_size: float) -> dict:
    issues: list[dict] = []
    for slide in report["slides"]:
        number = slide["slide_number"]
        title = slide.get("title", "")
        if len(title) > 44:
            issues.append({"slide_number": number, "severity": "warning", "code": "TITLE_WRAP_RISK", "evidence": f"タイトルが{len(title)}文字で3行化の可能性"})
        for block_index, block in enumerate(slide.get("text_blocks", []), start=1):
            lines = block.get("explicit_lines", [])
            minimum = block.get("min_font_size_pt")
            is_source = bool(re.search(r"(?:出典|参考|Source)\s*[:：]", block.get("text", ""), re.IGNORECASE))
            threshold = source_min_font_size if is_source else min_font_size
            if isinstance(minimum, (int, float)) and minimum < threshold:
                code = "SOURCE_FONT_TOO_SMALL" if is_source else "FONT_TOO_SMALL"
                issues.append({"slide_number": number, "severity": "error", "code": code, "evidence": f"文字列ブロック{block_index}の最小文字サイズ{minimum:g}ptが下限{threshold:g}pt未満"})
            if block.get("is_title") and len(lines) > 2:
                issues.append({"slide_number": number, "severity": "error", "code": "TITLE_THREE_LINES", "evidence": f"タイトルに{len(lines)}行の明示改行"})
            for line_index, line in enumerate(lines):
                stripped = line.strip()
                if len(stripped) == 1 and JP_CHAR.fullmatch(stripped):
                    issues.append({"slide_number": number, "severity": "warning", "code": "ORPHAN_SINGLE_CHAR", "evidence": f"文字列ブロック{block_index}に1文字行「{stripped}」"})
                if BAD_LINE_START.search(stripped):
                    issues.append({"slide_number": number, "severity": "error", "code": "BAD_PUNCTUATION_START", "evidence": f"行頭禁則文字「{stripped[:1]}」"})
                if line_index + 1 < len(lines):
                    next_line = lines[line_index + 1].strip()
                    if NUMBER_ONLY_END.search(stripped) and UNIT_START.search(next_line):
                        issues.append({"slide_number": number, "severity": "error", "code": "NUMBER_UNIT_SPLIT", "evidence": f"数字「{stripped}」と単位「{next_line}」が分断"})
                    if stripped and next_line and stripped[-1].isascii() and stripped[-1].isalpha() and next_line[0].isascii() and next_line[0].isalpha():
                        issues.append({"slide_number": number, "severity": "warning", "code": "ASCII_WORD_SPLIT_RISK", "evidence": f"英字の途中改行候補「{stripped[-8:]} / {next_line[:8]}」"})
    return {
        "version": 1,
        "source_pptx_sha256": report["source_pptx_sha256"],
        "slide_count": report["slide_count"],
        "pass": not any(issue["severity"] == "error" for issue in issues),
        "limitations": ["PowerPointの自動折返しはOOXMLに行情報がないため4辺クロップで補完する"],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="日本語PPT Lintを実行します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-font-size", type=float, default=12.0)
    parser.add_argument("--source-min-font-size", type=float, default=9.0)
    args = parser.parse_args()
    result = lint(audit_pptx(args.pptx), args.min_font_size, args.source_min_font_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"日本語PPT Lintを作成しました: {args.output}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
