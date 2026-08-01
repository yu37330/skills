#!/usr/bin/env python3
"""PPTX構造とPNGから客観的な視覚指標を抽出する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops

from audit_pptx import audit_pptx


SLIDE_NUMBER = re.compile(r"(\d+)(?!.*\d)")


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dhash(image: Image.Image, size: int = 16) -> str:
    gray = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(gray.get_flattened_data()) if hasattr(gray, "get_flattened_data") else list(gray.getdata())
    bits = []
    for y in range(size):
        row = y * (size + 1)
        bits.extend(pixels[row + x] > pixels[row + x + 1] for x in range(size))
    value = sum((1 << index) for index, bit in enumerate(bits) if bit)
    return f"{value:0{size * size // 4}x}"


def hash_similarity(left: str, right: str) -> float:
    xor = int(left, 16) ^ int(right, 16)
    bit_count = getattr(xor, "bit_count", None)
    distance = bit_count() if callable(bit_count) else bin(xor).count("1")
    return round(1 - distance / (len(left) * 4), 4)


def image_metrics(path: Path) -> dict:
    with Image.open(path) as source:
        image = source.convert("RGB")
        background = Image.new("RGB", image.size, image.getpixel((0, 0)))
        diff = ImageChops.difference(image, background).convert("L")
        mask = diff.point(lambda value: 255 if value > 18 else 0)
        bbox = mask.getbbox()
        histogram = mask.histogram()
        non_background = histogram[255]
        total = image.width * image.height
        whitespace = round(1 - non_background / total, 4)
        if bbox:
            small_width = 240
            small_height = max(1, round(image.height * small_width / image.width))
            small = mask.resize((small_width, small_height), Image.Resampling.NEAREST)
            values = list(small.get_flattened_data()) if hasattr(small, "get_flattened_data") else list(small.getdata())
            points = [(index % small_width, index // small_width) for index, value in enumerate(values) if value]
            centroid = [
                round(sum(point[0] for point in points) / len(points) / small_width, 4),
                round(sum(point[1] for point in points) / len(points) / small_height, 4),
            ] if points else [0.5, 0.5]
        else:
            centroid = [0.5, 0.5]
        # 共通ヘッダー／フッターだけで「似たページ」と判定しないよう、
        # 本文帯のレイアウトHashを別に固定する。
        content_top = round(image.height * 0.18)
        content_bottom = max(content_top + 1, round(image.height * 0.91))
        content_mask = mask.crop((0, content_top, image.width, content_bottom))
        return {
            "width": image.width,
            "height": image.height,
            "sha256": file_sha256(path),
            "whitespace_ratio": whitespace,
            "visual_centroid": centroid,
            "dhash": dhash(image),
            "layout_dhash": dhash(mask.convert("RGB")),
            "content_layout_dhash": dhash(content_mask.convert("RGB")),
        }


def clusters(slides: list[dict], threshold: float) -> list[list[int]]:
    """前景レイアウトHashが相互に近いページだけを同じクラスへまとめる。"""
    groups: list[list[dict]] = []
    for slide in slides:
        placed = False
        for group in groups:
            if all(
                hash_similarity(
                    slide["png"].get("content_layout_dhash", slide["png"]["layout_dhash"]),
                    member["png"].get("content_layout_dhash", member["png"]["layout_dhash"]),
                )
                >= threshold
                for member in group
            ):
                group.append(slide)
                placed = True
                break
        if not placed:
            groups.append([slide])
    result = [sorted(item["slide_number"] for item in group) for group in groups if len(group) >= 2]
    return sorted(result, key=lambda group: (-len(group), group))


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTXとPNGの視覚指標を抽出します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("png_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--similarity-threshold", type=float, default=0.65)
    args = parser.parse_args()
    audit = audit_pptx(args.pptx)
    pngs: dict[int, Path] = {}
    for path in args.png_dir.glob("*.png"):
        if "contact" in path.stem.lower():
            continue
        match = SLIDE_NUMBER.search(path.stem)
        if match:
            pngs[int(match.group(1))] = path
    expected = list(range(1, audit["slide_count"] + 1))
    if sorted(pngs) != expected:
        print(f"PNGが全ページそろっていません: {sorted(pngs)}")
        return 1
    slides: list[dict] = []
    for audit_slide in audit["slides"]:
        number = audit_slide["slide_number"]
        slides.append({
            "slide_number": number,
            "structure": audit_slide["structure"],
            "png": image_metrics(pngs[number]),
        })
    groups = clusters(slides, args.similarity_threshold)
    result = {
        "version": 1,
        "source_pptx_sha256": audit["source_pptx_sha256"],
        "slide_count": audit["slide_count"],
        "similarity_threshold": args.similarity_threshold,
        "slides": slides,
        "summary": {
            "average_native_element_ratio": round(sum(slide["structure"]["native_element_ratio"] for slide in slides) / len(slides), 4),
            "raster_dominant_slides": [slide["slide_number"] for slide in slides if slide["structure"]["native_element_ratio"] < 0.5],
            "high_similarity_clusters": groups,
            "largest_high_similarity_cluster_ratio": round((len(groups[0]) if groups else 0) / len(slides), 4),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"視覚指標を作成しました: {args.output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
