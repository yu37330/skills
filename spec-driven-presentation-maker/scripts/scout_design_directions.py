#!/usr/bin/env python3
"""代表ページの3方向プレビューを作り、採用後だけ完全なStyle Profileを読み込む。"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml

from validate_design_system import design_system_fingerprint


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_ref(target: Path, base: Path) -> str:
    """Scout成果物の配置先を基準にPOSIX形式の相対参照を返す。"""
    return os.path.relpath(target.resolve(), base.resolve()).replace(os.sep, "/")


def shorten(text: object, limit: int) -> str:
    value = str(text or "").strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def brand_source(args: argparse.Namespace) -> dict:
    candidates = [
        ("brand_guide", args.brand_guide),
        ("reference_pptx", args.reference_pptx),
        ("official_website_snapshot", args.website_snapshot),
    ]
    for kind, value in candidates:
        if value:
            path = value.resolve()
            if not path.is_file():
                raise ValueError(f"{kind}が見つかりません: {path}")
            return {"kind": kind, "path": str(path), "sha256": sha256(path)}
    return {"kind": "built_in_design_philosophy", "path": None, "sha256": None}


def extract_brand_spec(source: dict) -> dict:
    path_value = source.get("path")
    if not path_value:
        return {"status": "not_provided", "colors": [], "fonts": []}
    path = Path(path_value)
    colors: list[str] = []
    fonts: list[str] = []
    if path.suffix.lower() == ".pptx":
        try:
            with zipfile.ZipFile(path) as archive:
                theme_name = next((name for name in archive.namelist() if re.fullmatch(r"ppt/theme/theme\d+\.xml", name)), None)
                if theme_name:
                    root = ET.fromstring(archive.read(theme_name))
                    colors = [
                        f"#{node.attrib['val'].upper()}" for node in root.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                        if re.fullmatch(r"[0-9A-Fa-f]{6}", node.attrib.get("val", ""))
                    ]
                    fonts = [
                        node.attrib["typeface"] for node in root.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}latin")
                        if node.attrib.get("typeface")
                    ]
        except (OSError, zipfile.BadZipFile, ET.ParseError):
            return {"status": "extraction_failed", "colors": [], "fonts": []}
    elif path.suffix.lower() in {".css", ".svg", ".html", ".htm", ".md", ".txt"}:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        colors = [value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}\b", text)]
        fonts = [
            value.strip(" '\"") for value in re.findall(r"font-family\s*:\s*([^;}{]+)", text, flags=re.I)
            if value.strip()
        ]
    else:
        return {"status": "requires_external_extraction", "colors": [], "fonts": []}
    return {"status": "extracted" if colors or fonts else "no_tokens_found", "colors": list(dict.fromkeys(colors))[:8], "fonts": list(dict.fromkeys(fonts))[:4]}


def render_svg(path: Path, candidate: dict, headline: str, evidence: str, implication: str) -> None:
    preview = candidate["preview"]
    background = preview["background"]
    text = preview["text"]
    accent = preview["accent"]
    line = preview["line"]
    mode = candidate["candidate_id"]
    if mode == "safe":
        visual = f'''<rect x="708" y="222" width="382" height="238" rx="4" fill="{accent}"/>
<text x="754" y="337" font-size="78" font-weight="700" fill="#FFFFFF">01</text>
<text x="754" y="392" font-size="24" fill="#FFFFFF">{html.escape(evidence)}</text>'''
    elif mode == "reference_led":
        visual = f'''<line x1="90" y1="241" x2="1110" y2="241" stroke="{line}" stroke-width="2"/>
<rect x="90" y="278" width="620" height="226" fill="none" stroke="{line}"/>
<rect x="742" y="278" width="368" height="226" fill="{accent}"/>
<text x="122" y="346" font-size="22" fill="{text}">EVIDENCE</text>
<text x="122" y="406" font-size="32" font-weight="700" fill="{text}">{html.escape(evidence)}</text>
<text x="774" y="350" font-size="22" fill="#FFFFFF">IMPLICATION</text>
<text x="774" y="409" font-size="29" font-weight="700" fill="#FFFFFF">{html.escape(implication)}</text>'''
    else:
        visual = f'''<rect x="0" y="0" width="330" height="675" fill="{accent}"/>
<text x="72" y="330" font-size="116" font-weight="700" fill="#FFFFFF">01</text>
<line x1="380" y1="220" x2="1090" y2="220" stroke="{line}" stroke-width="2"/>
<text x="380" y="301" font-size="28" fill="{text}">{html.escape(evidence)}</text>
<text x="380" y="418" font-size="34" font-weight="700" fill="{accent}">{html.escape(implication)}</text>'''
    title_x = 380 if mode == "bold" else 90
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
<rect width="1200" height="675" fill="{background}"/>
<g font-family="Yu Gothic, Arial, sans-serif">{visual}</g>
<text x="{title_x}" y="74" font-family="Yu Gothic, Arial, sans-serif" font-size="18" font-weight="700" fill="{accent}">{candidate['label']}</text>
<text x="{title_x}" y="132" font-family="Yu Gothic, Arial, sans-serif" font-size="34" font-weight="700" fill="{text}">{html.escape(headline)}</text>
<text x="90" y="626" font-family="Yu Gothic, Arial, sans-serif" font-size="16" fill="{line}">同じ主張を異なる視覚文法で比較する代表プレビュー</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Design Directionを3案の実物プレビューで探索します")
    parser.add_argument("deck_plan", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--select", choices=["safe", "reference_led", "bold"])
    parser.add_argument("--brand-guide", type=Path)
    parser.add_argument("--reference-pptx", type=Path)
    parser.add_argument("--website-snapshot", type=Path)
    args = parser.parse_args()
    output_base = args.output.resolve().parent

    deck_path = args.deck_plan.resolve()
    manifest_path = args.manifest.resolve()
    deck_plan = yaml.safe_load(deck_path.read_text(encoding="utf-8-sig"))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(deck_plan, dict) or deck_plan.get("version") != 3:
        print("ERROR: Deck Plan version 3を指定してください")
        return 1
    if not isinstance(manifest, dict) or manifest.get("version") != 2:
        print("ERROR: Design System manifest version 2を指定してください")
        return 1

    index_path = (manifest_path.parent / manifest["registries"]["style_selection_index"]).resolve()
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    profiles = {item["id"]: item for item in index["profiles"]}
    deck_type = deck_plan.get("deck", {}).get("deck_type", "executive_decision")
    source = brand_source(args)
    brand_spec = extract_brand_spec(source)
    safe_map = {
        "executive_decision": "executive_clarity", "proposal": "executive_clarity",
        "analysis_report": "swiss_evidence", "operating_review": "data_report_precision",
        "training": "industrial_technical",
    }
    safe_style = safe_map.get(deck_type, "executive_clarity")
    reference_style = "swiss_evidence" if source["kind"] == "built_in_design_philosophy" else safe_style
    bold_style = "editorial_narrative" if safe_style != "editorial_narrative" else "japanese_minimal"
    candidate_specs = [
        ("safe", "Safe｜堅実", safe_style),
        ("reference_led", "Reference-led｜参照準拠", reference_style),
        ("bold", "Bold｜大胆", bold_style),
    ]
    slides = deck_plan.get("slides", [])
    key_numbers = set(deck_plan.get("deck", {}).get("key_slides", []))
    representative = next((item for item in slides if item.get("slide_number") in key_numbers), slides[0] if slides else {})
    headline = shorten(representative.get("executive_headline"), 26)
    evidence = shorten(representative.get("primary_evidence"), 25)
    implication = shorten(representative.get("so_what"), 25)
    preview_dir = (args.preview_dir or args.output.parent / "design-direction-previews").resolve()
    preview_dir.mkdir(parents=True, exist_ok=True)
    candidates = []
    for candidate_id, label, style_id in candidate_specs:
        profile = dict(profiles[style_id])
        profile["preview"] = dict(profile["preview"])
        if candidate_id == "reference_led" and brand_spec.get("colors"):
            palette = brand_spec["colors"]
            profile["preview"]["accent"] = palette[0]
            if len(palette) >= 2:
                profile["preview"]["line"] = palette[1]
        candidate = {**profile, "candidate_id": candidate_id, "label": label, "style_profile": style_id}
        preview_path = preview_dir / f"{candidate_id}.svg"
        render_svg(preview_path, candidate, headline, evidence, implication)
        candidates.append({
            "id": candidate_id, "label": label, "style_profile": style_id,
            "preview": relative_ref(preview_path, output_base), "preview_sha256": sha256(preview_path),
        })

    selected = None
    if args.select:
        selected_candidate = next(item for item in candidates if item["id"] == args.select)
        style_path = (manifest_path.parent / manifest["registries"]["style_profiles"]).resolve()
        style_doc = yaml.safe_load(style_path.read_text(encoding="utf-8-sig"))
        style = next(item for item in style_doc["style_profiles"] if item["id"] == selected_candidate["style_profile"])
        selected = {**selected_candidate, "style_spec": style, "style_spec_source": relative_ref(style_path, output_base), "style_spec_sha256": sha256(style_path)}

    if isinstance(source, dict) and isinstance(source.get("path"), str):
        source["path"] = relative_ref(Path(source["path"]), output_base)

    result = {
        "version": 1,
        "status": "selected" if selected else "pending_selection",
        "source": {
            "deck_plan": relative_ref(deck_path, output_base), "deck_plan_sha256": sha256(deck_path),
            "design_system_manifest": relative_ref(manifest_path, output_base), "design_system_sha256": design_system_fingerprint(manifest_path, manifest),
            "style_selection_index": relative_ref(index_path, output_base), "style_selection_index_sha256": sha256(index_path),
            "brand_source": source,
            "brand_spec": brand_spec,
        },
        "representative_slide": representative.get("slide_id"),
        "candidates": candidates,
        "selected": selected,
        "anti_slop_required": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Design Direction Scoutを作成しました: {args.output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
