#!/usr/bin/env python3
"""自己完結SVGの構造と安全性を検証する。"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
FORBIDDEN_TAGS = {"script", "foreignObject", "iframe", "object", "embed"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_viewbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = re.split(r"[\s,]+", value.strip())
    if len(parts) != 4:
        return None
    try:
        numbers = tuple(float(part) for part in parts)
    except ValueError:
        return None
    return numbers if numbers[2] > 0 and numbers[3] > 0 else None


def validate(path: Path) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    stats = {"elements": 0, "text_elements": 0, "external_references": 0}
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"SVGを解析できません: {exc}"], warnings, stats

    if local_name(root.tag) != "svg":
        errors.append("ルート要素はsvgである必要があります。")
        return errors, warnings, stats
    if not root.tag.startswith(f"{{{SVG_NS}}}"):
        errors.append("SVG名前空間がありません。")

    viewbox = parse_viewbox(root.attrib.get("viewBox"))
    if not viewbox:
        errors.append("有効なviewBoxがありません。")
    if root.attrib.get("role") != "img":
        warnings.append("ルート要素に role=img を設定してください。")
    if not root.attrib.get("aria-labelledby"):
        warnings.append("aria-labelledby がありません。")

    has_title = has_desc = False
    ids: list[str] = []
    for element in root.iter():
        stats["elements"] += 1
        tag = local_name(element.tag)
        if tag == "title":
            has_title = True
        elif tag == "desc":
            has_desc = True
        elif tag == "text":
            stats["text_elements"] += 1
            text = "".join(element.itertext()).strip()
            if len(text) > 160:
                warnings.append(f"長すぎるtext要素があります: {text[:30]}…")
        if tag in FORBIDDEN_TAGS:
            errors.append(f"禁止要素 <{tag}> が含まれています。")

        element_id = element.attrib.get("id")
        if element_id:
            ids.append(element_id)
        for name, value in element.attrib.items():
            attr = local_name(name).lower()
            lowered = value.strip().lower()
            if attr.startswith("on"):
                errors.append(f"イベント属性 {attr} は使用できません。")
            if "javascript:" in lowered:
                errors.append(f"JavaScript参照を含む属性 {attr} があります。")
            if attr in {"href", "src"}:
                if lowered.startswith(("http://", "https://", "//", "file:")):
                    stats["external_references"] += 1
                    errors.append(f"外部参照は使用できません: {value}")
                elif lowered and not lowered.startswith(("#", "data:")):
                    parsed = urlparse(value)
                    if parsed.scheme:
                        errors.append(f"許可されていない参照です: {value}")
            if attr == "style" and "url(http" in lowered:
                errors.append("style内に外部URLがあります。")

    if len(ids) != len(set(ids)):
        errors.append("id属性が重複しています。")
    if not has_title:
        errors.append("title要素がありません。")
    if not has_desc:
        errors.append("desc要素がありません。")
    if stats["text_elements"] == 0:
        warnings.append("text要素がありません。文字がパス化されていないか確認してください。")
    if path.stat().st_size > 5 * 1024 * 1024:
        warnings.append("SVGが5MBを超えています。不要な要素を削減してください。")
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="SVGの構造と安全性を検証します。")
    parser.add_argument("input", type=Path, help="入力SVG")
    parser.add_argument("--report", type=Path, help="検証結果JSON")
    args = parser.parse_args()

    errors, warnings, stats = validate(args.input)
    result = {
        "status": "error" if errors else "ok",
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
        "input": str(args.input.resolve()),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

