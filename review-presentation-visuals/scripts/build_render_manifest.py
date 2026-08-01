#!/usr/bin/env python3
"""全ページPNG、上下左右QAクロップ、コンタクトシートの証跡を作る。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageDraw
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillowが必要です。") from exc


SLIDE_NUMBER = re.compile(r"(\d+)(?!.*\d)")


def configure_utf8_console() -> None:
    """Windows端末でも日本語の診断結果をUTF-8で出力する。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path, base: Path) -> str:
    return Path(os.path.relpath(path, base)).as_posix()


def collect_pngs(png_dir: Path) -> list[tuple[int, Path]]:
    slides: list[tuple[int, Path]] = []
    for path in png_dir.glob("*.png"):
        if "contact" in path.stem.lower():
            continue
        match = SLIDE_NUMBER.search(path.stem)
        if match:
            slides.append((int(match.group(1)), path))
    slides.sort()
    return slides


def infer_render_fidelity(renderer: str) -> str:
    normalized = renderer.lower().replace(" ", "")
    if "powerpoint" in normalized:
        return "host_application"
    if "libreoffice" in normalized:
        return "office_compatible"
    if any(token in normalized for token in ("sourceparity", "source-parity", "cpu")):
        return "source_parity"
    return "unknown"


def build_contact_sheet(items: list[tuple[int, Path]], output: Path) -> None:
    columns = 2 if len(items) <= 10 else 3
    thumb_width = 720
    margin = 24
    label_height = 42
    rendered: list[tuple[int, Image.Image]] = []
    for number, path in items:
        with Image.open(path) as source:
            image = source.convert("RGB")
            thumb_height = round(image.height * thumb_width / image.width)
            rendered.append((number, image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)))
    cell_height = max(image.height for _, image in rendered) + label_height
    rows = math.ceil(len(rendered) / columns)
    sheet = Image.new(
        "RGB",
        (columns * thumb_width + (columns + 1) * margin, rows * cell_height + (rows + 1) * margin),
        "#E5E7EB",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (number, image) in enumerate(rendered):
        row, column = divmod(index, columns)
        x = margin + column * (thumb_width + margin)
        y = margin + row * cell_height
        sheet.paste(ImageOps.expand(image, border=1, fill="#94A3B8"), (x, y))
        draw.text((x, y + image.height + 10), f"Slide {number}", fill="#111827")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Manifestを作成します")
    parser.add_argument("png_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--renderer", required=True)
    parser.add_argument(
        "--render-fidelity",
        choices=("host_application", "office_compatible", "source_parity", "unknown"),
        help="省略時はrenderer名から推定します",
    )
    parser.add_argument("--pptx", type=Path)
    parser.add_argument("--expected-slides", type=int)
    args = parser.parse_args()

    png_dir = args.png_dir.resolve()
    output = args.output.resolve()
    items = collect_pngs(png_dir)
    if not items:
        print("スライドPNGが見つかりません。")
        return 1
    numbers = [number for number, _ in items]
    expected = args.expected_slides or len(items)
    if numbers != list(range(1, expected + 1)):
        print(f"スライド番号が1〜{expected}の連番ではありません: {numbers}")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    crop_dir = output.parent / "edge-crops"
    crop_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = output.parent / "contact-sheet.png"
    build_contact_sheet(items, sheet_path)

    base = output.parent
    entries = []
    expected_size = None
    for number, path in items:
        with Image.open(path) as source:
            image = source.convert("RGB")
            size = image.size
            expected_size = expected_size or size
            if size != expected_size:
                print(f"PNG寸法が不一致です: {path.name} {size} != {expected_size}")
                return 1
            edge_height = max(1, round(image.height * 0.15))
            edge_width = max(1, round(image.width * 0.15))
            top = crop_dir / f"slide-{number:02d}-top.png"
            bottom = crop_dir / f"slide-{number:02d}-bottom.png"
            left = crop_dir / f"slide-{number:02d}-left.png"
            right = crop_dir / f"slide-{number:02d}-right.png"
            image.crop((0, 0, image.width, edge_height)).save(top)
            image.crop((0, image.height - edge_height, image.width, image.height)).save(bottom)
            image.crop((0, 0, edge_width, image.height)).save(left)
            image.crop((image.width - edge_width, 0, image.width, image.height)).save(right)
        entries.append({
            "slide_number": number,
            "file": relative(path.resolve(), base),
            "sha256": sha256(path),
            "width": size[0],
            "height": size[1],
            "top_crop": relative(top, base),
            "top_crop_sha256": sha256(top),
            "bottom_crop": relative(bottom, base),
            "bottom_crop_sha256": sha256(bottom),
            "left_crop": relative(left, base),
            "left_crop_sha256": sha256(left),
            "right_crop": relative(right, base),
            "right_crop_sha256": sha256(right),
        })

    render_fidelity = args.render_fidelity or infer_render_fidelity(args.renderer)
    manifest = {
        "version": 2,
        "renderer": args.renderer,
        "render_fidelity": render_fidelity,
        "host_application_verified": render_fidelity == "host_application",
        "source_pptx": relative(args.pptx.resolve(), base) if args.pptx else None,
        "source_pptx_sha256": sha256(args.pptx) if args.pptx else None,
        "slide_count": len(entries),
        "contact_sheet": relative(sheet_path, base),
        "slides": entries,
    }
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Render Manifestを作成しました: {output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
