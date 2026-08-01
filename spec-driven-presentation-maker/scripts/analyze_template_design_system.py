#!/usr/bin/env python3
"""既存PPTXのMaster/Layout/Placeholder/ThemeをDesign System資産へ抽出する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"p": P, "a": A, "r": R}
EMU_PER_INCH = 914400


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def inch(value: str | None) -> float:
    return round(int(value or 0) / EMU_PER_INCH, 3)


def suitable_roles(name: str) -> list[str]:
    lower = name.lower()
    rules = [
        (("title", "cover", "表紙"), ["title"]),
        (("comparison", "compare", "比較"), ["comparison", "decision"]),
        (("chart", "graph", "グラフ"), ["evidence"]),
        (("timeline", "roadmap", "工程"), ["action"]),
        (("section", "divider", "区切"), ["title"]),
    ]
    for tokens, roles in rules:
        if any(token in lower for token in tokens):
            return roles
    return ["evidence", "synthesis"]


def placeholder_record(shape: ET.Element) -> dict | None:
    placeholder = shape.find(".//p:ph", NS)
    if placeholder is None:
        return None
    transform = shape.find(".//a:xfrm", NS)
    off = transform.find("a:off", NS) if transform is not None else None
    ext = transform.find("a:ext", NS) if transform is not None else None
    return {
        "type": placeholder.attrib.get("type", "body"),
        "idx": int(placeholder.attrib.get("idx", "0")),
        "x": inch(off.attrib.get("x") if off is not None else None),
        "y": inch(off.attrib.get("y") if off is not None else None),
        "w": inch(ext.attrib.get("cx") if ext is not None else None),
        "h": inch(ext.attrib.get("cy") if ext is not None else None),
    }


def build_contact_sheet(preview_dir: Path, output: Path) -> bool:
    images = sorted(preview_dir.glob("*.png"))
    if not images:
        return False
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    thumbs = []
    for image_path in images:
        with Image.open(image_path) as image:
            item = image.convert("RGB")
            item.thumbnail((480, 270))
            thumbs.append((image_path.name, item.copy()))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 500, rows * 310), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        x = (index % cols) * 500 + 10
        y = (index // cols) * 310 + 10
        sheet.paste(image, (x, y))
        draw.text((x, y + 275), name, fill="#222222")
    sheet.save(output)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerPointテンプレートをDesign System資産へ解析します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    pptx = args.pptx.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    layouts = []
    placeholder_counts: Counter[str] = Counter()
    with zipfile.ZipFile(pptx) as archive:
        names = archive.namelist()
        layout_names = sorted(
            (name for name in names if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)),
            key=lambda value: int(re.search(r"(\d+)", Path(value).stem).group(1)),
        )
        for number, name in enumerate(layout_names, start=1):
            root = ET.fromstring(archive.read(name))
            layout_name = root.attrib.get("matchingName") or root.attrib.get("type") or f"layout_{number:02d}"
            placeholders = []
            for shape in root.findall(".//p:sp", NS):
                record = placeholder_record(shape)
                if record:
                    placeholders.append(record)
                    placeholder_counts[record["type"]] += 1
            slots = {f"{item['type']}_{item['idx']}": f"placeholder:{item['idx']}" for item in placeholders}
            body_capacity = {
                f"{item['type']}_{item['idx']}_chars": max(24, int(item["w"] * item["h"] * 22))
                for item in placeholders if item["type"] not in {"title", "ctrTitle", "dt", "ftr", "sldNum"}
            }
            layouts.append({
                "layout_id": f"template_layout_{number:02d}", "name": layout_name,
                "suitable_roles": suitable_roles(layout_name), "slots": slots,
                "placeholders": placeholders, "content_limits": body_capacity,
            })

        theme_name = next((name for name in names if re.fullmatch(r"ppt/theme/theme\d+\.xml", name)), None)
        colors: dict[str, str] = {}
        fonts: dict[str, str | None] = {}
        if theme_name:
            theme_root = ET.fromstring(archive.read(theme_name))
            scheme = theme_root.find(".//a:clrScheme", NS)
            if scheme is not None:
                for child in list(scheme):
                    color = child.find("a:srgbClr", NS) or child.find("a:sysClr", NS)
                    if color is not None:
                        colors[child.tag.split("}")[-1]] = color.attrib.get("val") or color.attrib.get("lastClr")
            major = theme_root.find(".//a:fontScheme/a:majorFont/a:latin", NS)
            minor = theme_root.find(".//a:fontScheme/a:minorFont/a:latin", NS)
            fonts = {"major_latin": major.attrib.get("typeface") if major is not None else None, "minor_latin": minor.attrib.get("typeface") if minor is not None else None}

        master_count = len([name for name in names if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", name)])
        embedded_images = len([name for name in names if name.startswith("ppt/media/")])

    theme = {"version": 1, "source": str(pptx), "master_count": master_count, "layout_count": len(layouts), "colors": colors, "fonts": fonts}
    inventory = {"version": 1, "placeholder_types": dict(placeholder_counts), "embedded_image_count": embedded_images, "layout_count": len(layouts)}
    (output / "theme.json").write_text(json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "layout-index.yaml").write_text(yaml.safe_dump({"version": 1, "layouts": layouts}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (output / "component-inventory.yaml").write_text(yaml.safe_dump(inventory, allow_unicode=True, sort_keys=False), encoding="utf-8")
    guideline = [
        "# テンプレート視覚ガイド", "", f"- Master: {master_count}", f"- Layout: {len(layouts)}",
        f"- Theme colors: {', '.join(colors.values()) or '未抽出'}", f"- Fonts: {fonts}", "",
        "## 運用ルール", "", "- 背景画像として貼らず、Master／Layout／Placeholderを利用する。",
        "- 各Layoutのcontent_limitsを超える場合は、文字縮小より別Layoutを選ぶ。",
        "- suitable_rolesを候補絞込みに使い、人間がvisual-guidelineを確認して誤分類を修正する。", "",
    ]
    (output / "visual-guideline.md").write_text("\n".join(guideline), encoding="utf-8")
    rendered = bool(args.preview_dir and build_contact_sheet(args.preview_dir.resolve(), output / "preview-contact-sheet.png"))
    (output / "preview-status.yaml").write_text(yaml.safe_dump({"rendered": rendered, "reason": None if rendered else "PNGレンダリング入力なし"}, allow_unicode=True), encoding="utf-8")
    print(f"テンプレート解析を作成しました: {output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
