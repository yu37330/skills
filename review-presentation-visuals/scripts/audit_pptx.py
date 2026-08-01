#!/usr/bin/env python3
"""PPTXの内容・ノート・グラフ・編集可能性を機械監査する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}
SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?")
TERM_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+._/-]{1,}\b")
SOURCE_RE = re.compile(r"(?:出典|参考|Source|SOURCE)\s*[:：]", re.IGNORECASE)


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def relationships(archive: zipfile.ZipFile, part: str) -> dict[str, str]:
    folder, name = posixpath.split(part)
    rel_path = posixpath.join(folder, "_rels", name + ".rels")
    try:
        root = ET.fromstring(archive.read(rel_path))
    except KeyError:
        return {}
    result: dict[str, str] = {}
    for rel in root.findall("pr:Relationship", NS):
        rel_id, target = rel.get("Id"), rel.get("Target")
        if rel_id and target and not target.startswith(("http://", "https://")):
            result[rel_id] = posixpath.normpath(posixpath.join(folder, target))
    return result


def ordered_text_lines(shape: ET.Element) -> list[str]:
    lines: list[str] = []
    for paragraph in shape.findall(".//a:p", NS):
        current = ""
        for child in list(paragraph):
            tag = child.tag.rsplit("}", 1)[-1]
            if tag in {"r", "fld"}:
                current += "".join(node.text or "" for node in child.findall(".//a:t", NS))
            elif tag == "br":
                lines.append(current)
                current = ""
        if current or not lines:
            lines.append(current)
    return [line for line in lines if line != ""]


def shape_title(shape: ET.Element) -> bool:
    placeholder = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
    return placeholder is not None and placeholder.get("type") in {"title", "ctrTitle"}


def element_area(element: ET.Element) -> int:
    ext = element.find(".//a:xfrm/a:ext", NS)
    if ext is None:
        ext = element.find(".//p:xfrm/a:ext", NS)
    try:
        return int(ext.get("cx", "0")) * int(ext.get("cy", "0")) if ext is not None else 0
    except ValueError:
        return 0


def chart_values(archive: zipfile.ZipFile, slide_part: str, root: ET.Element) -> list[str]:
    rels = relationships(archive, slide_part)
    values: list[str] = []
    for frame in root.findall(".//p:graphicFrame", NS):
        for chart in frame.findall(".//c:chart", NS):
            target = rels.get(chart.get(f"{{{NS['r']}}}id", ""))
            if not target or target not in archive.namelist():
                continue
            chart_root = ET.fromstring(archive.read(target))
            values.extend(normalize_text(node.text or "") for node in chart_root.findall(".//c:v", NS))
    return values


def notes_text(archive: zipfile.ZipFile, slide_part: str, root: ET.Element) -> str:
    rels = relationships(archive, slide_part)
    notes_target = None
    for rel_id, target in rels.items():
        if "/notesSlides/" in target:
            notes_target = target
            break
    if not notes_target or notes_target not in archive.namelist():
        return ""
    notes_root = ET.fromstring(archive.read(notes_target))
    chunks: list[str] = []
    for shape in notes_root.findall(".//p:sp", NS):
        placeholder = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder is not None and placeholder.get("type") in {"hdr", "ftr", "dt", "sldNum"}:
            continue
        chunks.extend(ordered_text_lines(shape))
    return normalize_text("\n".join(chunks))


def audit_pptx(path: Path) -> dict:
    path = path.resolve()
    slides: list[dict] = []
    with zipfile.ZipFile(path) as archive:
        presentation_root = ET.fromstring(archive.read("ppt/presentation.xml"))
        slide_size = presentation_root.find("p:sldSz", NS)
        slide_area = 1
        if slide_size is not None:
            slide_area = max(1, int(slide_size.get("cx", "1")) * int(slide_size.get("cy", "1")))
        slide_parts = sorted(
            (name for name in archive.namelist() if SLIDE_RE.match(name)),
            key=lambda name: int(SLIDE_RE.match(name).group(1)),
        )
        for slide_number, slide_part in enumerate(slide_parts, start=1):
            root = ET.fromstring(archive.read(slide_part))
            shapes = root.findall(".//p:sp", NS)
            connectors = root.findall(".//p:cxnSp", NS)
            pictures = root.findall(".//p:pic", NS)
            graphic_frames = root.findall(".//p:graphicFrame", NS)
            shape_type_counts: dict[str, int] = {}
            rectangle_area = 0
            ellipse_area = 0
            for shape in shapes:
                geometry = shape.find("./p:spPr/a:prstGeom", NS)
                shape_type = geometry.get("prst") if geometry is not None else "custom_or_text"
                shape_type_counts[shape_type] = shape_type_counts.get(shape_type, 0) + 1
                area = element_area(shape)
                if shape_type in {"rect", "roundRect"}:
                    rectangle_area += area
                elif shape_type == "ellipse":
                    ellipse_area += area
            picture_area = sum(element_area(picture) for picture in pictures)
            blocks: list[dict] = []
            title = ""
            all_lines: list[str] = []
            for shape in shapes:
                lines = ordered_text_lines(shape)
                if not lines:
                    continue
                text = normalize_text("\n".join(lines))
                block_font_sizes = [
                    int(value) / 100
                    for node in shape.findall(".//*[@sz]")
                    if (value := node.get("sz")) and value.isdigit()
                ]
                blocks.append({
                    "text": text,
                    "explicit_lines": lines,
                    "is_title": shape_title(shape),
                    "min_font_size_pt": min(block_font_sizes) if block_font_sizes else None,
                })
                all_lines.extend(lines)
                if shape_title(shape) and not title:
                    title = text
            text = normalize_text("\n".join(all_lines))
            content_inventory = "".join(sorted(character for character in text if not character.isspace()))
            font_sizes = [
                int(value) / 100
                for node in root.findall(".//*[@sz]")
                if (value := node.get("sz")) and value.isdigit()
            ]
            chart_cache = chart_values(archive, slide_part, root)
            notes = notes_text(archive, slide_part, root)
            source_lines = sorted({normalize_text(line) for line in all_lines if SOURCE_RE.search(line)})
            numbers = sorted(NUMBER_RE.findall(text))
            terms = sorted({term for term in TERM_RE.findall(text) if not term.isdigit()})
            native_elements = len(shapes) + len(connectors) + len(graphic_frames)
            total_elements = native_elements + len(pictures)
            native_ratio = round(native_elements / total_elements, 4) if total_elements else 1.0
            slides.append({
                "slide_number": slide_number,
                "title": title,
                "text": text,
                "text_sha256": sha256_bytes(text.encode("utf-8")),
                "content_inventory_sha256": sha256_bytes(content_inventory.encode("utf-8")),
                "text_blocks": blocks,
                "numbers": numbers,
                "source_lines": source_lines,
                "proper_terms": terms,
                "notes": notes,
                "notes_sha256": sha256_bytes(notes.encode("utf-8")),
                "chart_values": chart_cache,
                "chart_data_sha256": sha256_bytes(json.dumps(chart_cache, ensure_ascii=False).encode("utf-8")),
                "structure": {
                    "shape_count": len(shapes),
                    "connector_count": len(connectors),
                    "picture_count": len(pictures),
                    "graphic_frame_count": len(graphic_frames),
                    "shape_type_counts": shape_type_counts,
                    "rectangle_area_ratio": round(rectangle_area / slide_area, 4),
                    "ellipse_area_ratio": round(ellipse_area / slide_area, 4),
                    "raster_image_area_ratio": round(picture_area / slide_area, 4),
                    "native_element_ratio": native_ratio,
                    "min_font_size_pt": min(font_sizes) if font_sizes else None,
                },
            })
    return {
        "version": 1,
        "source_pptx": str(path),
        "source_pptx_sha256": sha256_file(path),
        "slide_count": len(slides),
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTX構造監査JSONを作成します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit_pptx(args.pptx)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PPTX監査結果を作成しました: {args.output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
