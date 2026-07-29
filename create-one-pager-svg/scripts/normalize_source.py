#!/usr/bin/env python3
"""原文を意味を変えずにUTF-8 Markdownへ正規化する。"""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor(HTMLParser):
    """HTMLから表示テキストを抽出する。"""

    BLOCK_TAGS = {
        "article", "aside", "blockquote", "br", "div", "footer", "h1", "h2",
        "h3", "h4", "h5", "h6", "header", "li", "main", "nav", "p", "section",
        "table", "td", "th", "tr", "ul", "ol",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.ignored_depth += 1
        elif not self.ignored_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif not self.ignored_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp932"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def normalize(text: str, is_html: bool) -> str:
    if is_html:
        parser = TextExtractor()
        parser.feed(text)
        text = "".join(parser.parts)
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[\t\u00a0]+", " ", text)
    lines = [re.sub(r"[ \u3000]+$", "", line) for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="原文をUTF-8 Markdownへ正規化します。")
    parser.add_argument("input", type=Path, help="入力ファイル")
    parser.add_argument("--output", "-o", type=Path, required=True, help="出力ファイル")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"入力ファイルが見つかりません: {args.input}")
    text, encoding = read_text(args.input)
    is_html = args.input.suffix.lower() in {".html", ".htm"} or bool(
        re.search(r"<html\b|<body\b|<!doctype", text[:2000], re.IGNORECASE)
    )
    normalized = normalize(text, is_html)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(normalized, encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "input": str(args.input.resolve()),
        "output": str(args.output.resolve()),
        "detected_encoding": encoding,
        "html_extracted": is_html,
        "characters": len(normalized),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

