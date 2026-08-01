#!/usr/bin/env python3
"""Visual Plan v7/v8と完成PPTXのDesign System・Anti-Slop準拠を監査する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import PurePosixPath
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

TRACE_PATTERN = re.compile(r"^SDPM::([^:]+)::([^:]+)")
SLOT_PATTERN = re.compile(r"::slot=([^:]+)")
FRAME_PATTERN = re.compile(r"::frameEmu=(-?\d+),(-?\d+),(\d+),(\d+)")
BBOX_PATTERN = re.compile(r"::bboxEmu=(-?\d+),(-?\d+),(\d+),(\d+)")
EMU_PER_INCH = 914400
PREMIUM_COMPONENTS = {
    "narrative.executive_summary", "narrative.key_message_evidence", "chart.insight",
    "narrative.findings_implications", "strategy.house", "strategy.issue_tree",
    "strategy.portfolio_matrix", "strategy.capability_map", "strategy.value_driver_tree",
    "strategy.initiative_portfolio", "execution.roadmap", "execution.gantt",
    "execution.governance", "execution.kpi_cascade", "narrative.recommendation_actions",
}

SEMANTIC_EQUAL_AREA_COMPONENTS = {
    "narrative.findings_implications", "strategy.capability_map",
    "strategy.initiative_portfolio", "execution.gantt",
    "execution.governance", "execution.kpi_cascade",
}
FUNNEL_TOKENS = ("funnel", "漏斗", "taper", "narrow", "細く", "先細", "縮小")
INDEPENDENT_COHORT_TOKENS = ("母数が異", "異なる母数", "同一母集団ではなく", "別母集団", "非連続")


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


def resolve(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if re.match(r"^[A-Za-z]:[\\/]", value) and not path.is_absolute():
        return path
    return path if path.is_absolute() else (base / path).resolve()


def load(path: Path) -> object:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def design_system_fingerprint(path: Path, manifest: dict) -> str:
    entries = {"manifest": sha256(path)}
    for group in ("registries", "themes"):
        values = manifest.get(group, {}) if isinstance(manifest, dict) else {}
        if isinstance(values, dict):
            for key, value in values.items():
                target = resolve(path.parent, value)
                if target and target.is_file():
                    entries[f"{group}:{key}"] = sha256(target)
    implementation = manifest.get("implementation", []) if isinstance(manifest, dict) else []
    if isinstance(implementation, list):
        for index, value in enumerate(implementation):
            target = resolve(path.parent, value)
            if target and target.is_file():
                entries[f"implementation:{index}:{target.name}"] = sha256(target)
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def flatten_token_values(value: object, colors: set[str], sizes: set[float]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", item):
                colors.add(item[1:].upper())
            elif key == "fontSizes" and isinstance(item, dict):
                sizes.update(float(number) for number in item.values() if isinstance(number, (int, float)))
            elif key == "componentFontScale" and isinstance(item, list):
                sizes.update(float(number) for number in item if isinstance(number, (int, float)))
            else:
                flatten_token_values(item, colors, sizes)
    elif isinstance(value, list):
        for item in value:
            flatten_token_values(item, colors, sizes)


def extract_pptx_style_values(path: Path) -> tuple[list[str], list[float], int, dict]:
    colors: list[str] = []
    sizes: list[float] = []
    slide_count = 0
    gradient_count = 0
    glow_count = 0
    shape_count = 0
    rounded_count = 0
    equal_area_slide_ratios: list[float] = []
    image_targets: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        slide_count = len(names)
        for name in names:
            root = ET.fromstring(archive.read(name))
            slide_rectangle_areas: list[int] = []
            gradient_count += len(root.findall(".//a:gradFill", NS))
            glow_count += len(root.findall(".//a:glow", NS))
            for geometry in root.findall(".//a:prstGeom", NS):
                shape_count += 1
                preset = geometry.attrib.get("prst", "")
                if preset in {"roundRect", "round1Rect", "round2DiagRect", "round2SameRect", "snipRoundRect"}:
                    rounded_count += 1
            for shape in root.findall(".//p:sp", NS):
                geometry = shape.find("p:spPr/a:prstGeom", NS)
                transform = shape.find("p:spPr/a:xfrm", NS)
                ext = transform.find("a:ext", NS) if transform is not None else None
                if geometry is not None and geometry.attrib.get("prst") in {"rect", "roundRect", "round1Rect"} and ext is not None:
                    cx, cy = ext.attrib.get("cx"), ext.attrib.get("cy")
                    if isinstance(cx, str) and cx.isdigit() and isinstance(cy, str) and cy.isdigit():
                        slide_rectangle_areas.append(round(int(cx) * int(cy) / 10**10))
            slide_area_counts = Counter(slide_rectangle_areas)
            repeated_on_slide = sum(count for count in slide_area_counts.values() if count >= 3)
            equal_area_slide_ratios.append(
                repeated_on_slide / len(slide_rectangle_areas) if slide_rectangle_areas else 0.0
            )
            rel_name = str(PurePosixPath(name).parent / "_rels" / f"{PurePosixPath(name).name}.rels")
            rel_map: dict[str, str] = {}
            if rel_name in archive.namelist():
                rel_root = ET.fromstring(archive.read(rel_name))
                rel_map = {
                    node.attrib.get("Id", ""): node.attrib.get("Target", "")
                    for node in rel_root.findall("rel:Relationship", NS)
                }
            for blip in root.findall(".//a:blip", NS):
                relationship_id = blip.attrib.get(f"{{{NS['r']}}}embed")
                target = rel_map.get(relationship_id or "")
                if target:
                    image_targets.append(target)
            colors.extend(
                node.attrib["val"].upper() for node in root.findall(".//a:srgbClr", NS)
                if re.fullmatch(r"[0-9A-Fa-f]{6}", node.attrib.get("val", ""))
            )
            for tag in ("rPr", "defRPr", "endParaRPr"):
                for node in root.findall(f".//a:{tag}", NS):
                    value = node.attrib.get("sz")
                    if isinstance(value, str) and value.isdigit():
                        sizes.append(int(value) / 100)
    image_counts = Counter(image_targets)
    repeated_images = sum(count for count in image_counts.values() if count >= 2)
    metrics = {
        "gradient_fill_count": gradient_count,
        "glow_effect_count": glow_count,
        "rounded_rectangle_ratio": round(rounded_count / shape_count, 4) if shape_count else 0.0,
        "equal_area_rectangle_ratio": round(max(equal_area_slide_ratios), 4) if equal_area_slide_ratios else 0.0,
        "equal_area_rectangle_ratio_by_slide": {
            str(index): round(value, 4) for index, value in enumerate(equal_area_slide_ratios, start=1)
        },
        "repeated_image_hash_ratio": round(repeated_images / len(image_targets), 4) if image_targets else 0.0,
    }
    return colors, sizes, slide_count, metrics


def ratio(values: list[object], allowed: set[object]) -> float:
    if not values:
        return 1.0
    return round(sum(value in allowed for value in values) / len(values), 4)


def extract_component_traceability(path: Path) -> dict:
    """Shape Name／Alt TextからNative Componentの使用実体を抽出する。"""
    slides: list[dict] = []
    component_signatures: dict[str, list[tuple]] = {}
    total_shapes = 0
    native_shapes = 0
    traced_shapes = 0
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda value: int(re.search(r"(\d+)", PurePosixPath(value).name).group(1)),
        )
        for slide_number, name in enumerate(names, start=1):
            root = ET.fromstring(archive.read(name))
            records: list[dict] = []
            signature_parts: dict[str, list[tuple]] = {}
            shape_nodes = (
                list(root.findall(".//p:sp", NS))
                + list(root.findall(".//p:cxnSp", NS))
                + list(root.findall(".//p:graphicFrame", NS))
                + list(root.findall(".//p:pic", NS))
            )
            total_shapes += len(shape_nodes)
            native_shapes += sum(node.tag != f"{{{NS['p']}}}pic" for node in shape_nodes)
            for node in shape_nodes:
                props = node.find(".//p:cNvPr", NS)
                if props is None:
                    continue
                candidates = [props.attrib.get("name", ""), props.attrib.get("title", ""), props.attrib.get("descr", "")]
                match = next((TRACE_PATTERN.match(value) for value in candidates if TRACE_PATTERN.match(value)), None)
                if match is None:
                    continue
                component_id, role = match.groups()
                description = props.attrib.get("descr", "")
                transform = node.find(".//a:xfrm", NS)
                offset = transform.find("a:off", NS) if transform is not None else None
                extent = transform.find("a:ext", NS) if transform is not None else None
                geometry = (
                    node.find(".//a:prstGeom", NS).attrib.get("prst")
                    if node.find(".//a:prstGeom", NS) is not None else node.tag.rsplit("}", 1)[-1]
                )
                part = (
                    geometry,
                    int(offset.attrib.get("x", 0)) if offset is not None else 0,
                    int(offset.attrib.get("y", 0)) if offset is not None else 0,
                    int(extent.attrib.get("cx", 0)) if extent is not None else 0,
                    int(extent.attrib.get("cy", 0)) if extent is not None else 0,
                    role,
                )
                signature_parts.setdefault(component_id, []).append(part)
                records.append({
                    "component_id": component_id,
                    "role": role,
                    "shape_name": props.attrib.get("name"),
                    "alt_text": description,
                    "layout_slot": (
                        SLOT_PATTERN.search(description).group(1)
                        if SLOT_PATTERN.search(description) else None
                    ),
                    "component_frame_emu": (
                        [int(value) for value in FRAME_PATTERN.search(description).groups()]
                        if FRAME_PATTERN.search(description) else None
                    ),
                    "generated_bbox_emu": (
                        [int(value) for value in BBOX_PATTERN.search(description).groups()]
                        if BBOX_PATTERN.search(description) else None
                    ),
                    "actual_bbox_emu": [part[1], part[2], part[3], part[4]],
                })
            traced_shapes += len(records)
            for component_id, parts in signature_parts.items():
                component_signatures.setdefault(component_id, []).append(tuple(sorted(parts)))
            slides.append({
                "slide_number": slide_number,
                "component_ids": sorted({item["component_id"] for item in records}),
                "traced_shape_count": len(records),
                "records": records,
            })
    premium_differences = {}
    for component_id in sorted(PREMIUM_COMPONENTS):
        signatures = component_signatures.get(component_id, [])
        if len(signatures) >= 3:
            premium_differences[component_id] = {
                "observed_slides": len(signatures),
                "unique_composition_signatures": len(set(signatures)),
                "pass": len(set(signatures)) >= 3,
            }
    return {
        "slides": slides,
        "traced_shape_count": traced_shapes,
        "total_shape_count": total_shapes,
        "native_element_ratio": round(native_shapes / total_shapes, 4) if total_shapes else 1.0,
        "trace_coverage_ratio": round(traced_shapes / total_shapes, 4) if total_shapes else 1.0,
        "premium_theme_composition": premium_differences,
        "premium_theme_composition_pass": (
            all(item["pass"] for item in premium_differences.values())
            if premium_differences else None
        ),
    }


def _bbox_matches(actual: list[int], expected: list[int]) -> bool:
    """位置は±0.05inch、寸法は±0.05inchまたは2%以内を許容する。"""
    position_tolerance = round(0.05 * EMU_PER_INCH)
    if any(abs(actual[index] - expected[index]) > position_tolerance for index in (0, 1)):
        return False
    for index in (2, 3):
        tolerance = max(position_tolerance, round(abs(expected[index]) * 0.02))
        if abs(actual[index] - expected[index]) > tolerance:
            return False
    return True


def locked_layout_geometry_violations(
    traceability: dict,
    planned_slides: list[dict],
    layouts: dict[str, dict],
) -> list[dict]:
    """生成時座標の改変とRole Layout slot frameからの逸脱を検出する。"""
    violations: list[dict] = []
    records_by_slide = {
        item.get("slide_number"): item.get("records", [])
        for item in traceability.get("slides", [])
    }
    for slide_number, slide in enumerate(planned_slides, start=1):
        if not isinstance(slide, dict):
            continue
        resolution = slide.get("design_resolution", {})
        layout = layouts.get(resolution.get("role_layout"), {}) if isinstance(resolution, dict) else {}
        slot_frames = layout.get("slot_frames", {}) if isinstance(layout, dict) else {}
        records = records_by_slide.get(slide_number, [])
        for record in records:
            generated = record.get("generated_bbox_emu")
            actual = record.get("actual_bbox_emu")
            if not generated:
                violations.append({
                    "slide_number": slide_number,
                    "component_id": record.get("component_id"),
                    "role": record.get("role"),
                    "kind": "missing_generated_bbox",
                })
            elif not _bbox_matches(actual, generated):
                violations.append({
                    "slide_number": slide_number,
                    "component_id": record.get("component_id"),
                    "role": record.get("role"),
                    "kind": "shape_moved_or_resized",
                    "expected_bbox_emu": generated,
                    "actual_bbox_emu": actual,
                })
        for entry in slide.get("component_plan", []):
            if not isinstance(entry, dict):
                continue
            component_id, slot = entry.get("component"), entry.get("slot")
            expected_frame = slot_frames.get(slot)
            if not isinstance(expected_frame, dict):
                violations.append({
                    "slide_number": slide_number, "component_id": component_id,
                    "slot": slot, "kind": "missing_slot_frame_contract",
                })
                continue
            expected_emu = [
                round(float(expected_frame[key]) * EMU_PER_INCH)
                for key in ("x", "y", "w", "h")
            ]
            matches = [
                record for record in records
                if record.get("component_id") == component_id and record.get("layout_slot") == slot
            ]
            if not matches:
                violations.append({
                    "slide_number": slide_number, "component_id": component_id,
                    "slot": slot, "kind": "missing_component_slot_trace",
                })
                continue
            observed_frames = {tuple(record["component_frame_emu"]) for record in matches if record.get("component_frame_emu")}
            if not observed_frames:
                violations.append({
                    "slide_number": slide_number, "component_id": component_id,
                    "slot": slot, "kind": "missing_component_frame",
                })
            elif any(not _bbox_matches(list(frame), expected_emu) for frame in observed_frames):
                violations.append({
                    "slide_number": slide_number, "component_id": component_id,
                    "slot": slot, "kind": "component_frame_outside_locked_slot",
                    "expected_frame_emu": expected_emu,
                    "observed_frames_emu": [list(frame) for frame in sorted(observed_frames)],
                })
    return violations


def component_contract_violations(traceability: dict, contracts: dict[str, dict]) -> list[dict]:
    """Shape roleの連番から、明白な推奨上限超過を機械検出する。"""
    violations: list[dict] = []
    for slide in traceability.get("slides", []):
        roles_by_component: dict[str, set[int]] = {}
        for record in slide.get("records", []):
            match = re.search(
                r"(?:item|row|branch|phase|task|level|evidence|driver|choice|initiative|bar|group)_(\d+)",
                record.get("role", ""),
            )
            if match:
                roles_by_component.setdefault(record["component_id"], set()).add(int(match.group(1)))
        for component_id, indexes in roles_by_component.items():
            limits = contracts.get(component_id, {}).get("content_limits", {})
            range_maxima: list[int] = []
            for value in limits.values() if isinstance(limits, dict) else []:
                if isinstance(value, str):
                    range_maxima.extend(
                        int(match.group(2))
                        for match in re.finditer(r"(\d+)\s*[～~-]\s*(\d+)", value)
                    )
            if range_maxima and len(indexes) > max(range_maxima):
                violations.append({
                    "slide_number": slide.get("slide_number"),
                    "component_id": component_id,
                    "observed_items": len(indexes),
                    "recommended_max": max(range_maxima),
                })
    return violations


def flattened_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(flattened_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flattened_text(item) for item in value)
    return str(value) if value is not None else ""


def main_component(slide: dict) -> str | None:
    for entry in slide.get("component_plan", []):
        if isinstance(entry, dict) and entry.get("slot") == "main":
            return entry.get("component")
    resolution = slide.get("design_resolution", {})
    return resolution.get("component_hint") if isinstance(resolution, dict) else None


def connector_direction_violations(path: Path, planned_slides: list[dict]) -> list[dict]:
    """左→右が主読順のmain componentで逆向き矢印を検出する。"""
    violations: list[dict] = []
    with zipfile.ZipFile(path) as archive:
        for slide_number, slide in enumerate(planned_slides, start=1):
            if not isinstance(slide, dict):
                continue
            strategy = slide.get("visual_strategy", {})
            grammar = strategy.get("visual_grammar", {}) if isinstance(strategy, dict) else {}
            motif = strategy.get("motif_fingerprint", {}) if isinstance(strategy, dict) else {}
            if grammar.get("reading_path") != "left_to_right" or motif.get("connector_usage") != "dominant":
                continue
            name = f"ppt/slides/slide{slide_number}.xml"
            if name not in archive.namelist():
                continue
            root = ET.fromstring(archive.read(name))
            centers: dict[str, float] = {}
            for node in list(root.findall(".//p:sp", NS)) + list(root.findall(".//p:pic", NS)) + list(root.findall(".//p:graphicFrame", NS)):
                props = node.find(".//p:cNvPr", NS)
                transform = node.find(".//a:xfrm", NS)
                offset = transform.find("a:off", NS) if transform is not None else None
                extent = transform.find("a:ext", NS) if transform is not None else None
                if props is not None and offset is not None and extent is not None:
                    centers[props.attrib.get("id", "")] = int(offset.attrib.get("x", 0)) + int(extent.attrib.get("cx", 0)) / 2
            expected_component = main_component(slide)
            for connector in root.findall(".//p:cxnSp", NS):
                props = connector.find(".//p:cNvPr", NS)
                trace = " ".join([
                    props.attrib.get("name", "") if props is not None else "",
                    props.attrib.get("descr", "") if props is not None else "",
                ])
                if expected_component and f"SDPM::{expected_component}::" not in trace:
                    continue
                start = connector.find("p:nvCxnSpPr/p:cNvCxnSpPr/a:stCxn", NS)
                end = connector.find("p:nvCxnSpPr/p:cNvCxnSpPr/a:endCxn", NS)
                head = connector.find("p:spPr/a:ln/a:headEnd", NS)
                tail = connector.find("p:spPr/a:ln/a:tailEnd", NS)
                if start is None or end is None:
                    continue
                start_x = centers.get(start.attrib.get("id", ""))
                end_x = centers.get(end.attrib.get("id", ""))
                if start_x is None or end_x is None or start_x == end_x:
                    continue
                head_arrow = head is not None and head.attrib.get("type", "none") != "none"
                tail_arrow = tail is not None and tail.attrib.get("type", "none") != "none"
                reverse = (head_arrow and start_x > end_x) or (tail_arrow and start_x < end_x)
                if reverse:
                    violations.append({
                        "slide_number": slide_number,
                        "component_id": expected_component,
                        "shape_name": props.attrib.get("name") if props is not None else None,
                        "reading_path": "left_to_right",
                    })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Design System準拠を監査します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("visual_plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-token-match-ratio", type=float, default=0.7)
    args = parser.parse_args()
    pptx = args.pptx.resolve()
    visual_plan_path = args.visual_plan.resolve()
    visual_plan = load(visual_plan_path)
    errors: list[str] = []
    plan_version = visual_plan.get("version") if isinstance(visual_plan, dict) else None
    if not isinstance(visual_plan, dict) or plan_version not in {7, 8}:
        errors.append("Visual Plan version 7または8を指定してください")
        visual_plan = {}
    source = visual_plan.get("source", {}) if isinstance(visual_plan, dict) else {}
    manifest_path = resolve(visual_plan_path.parent, source.get("design_system_manifest")) if isinstance(source, dict) else None
    if manifest_path is None or not manifest_path.is_file():
        errors.append("Design System manifestが見つかりません")
        manifest = {}
    else:
        manifest = load(manifest_path)
        expected_design_hash = design_system_fingerprint(manifest_path, manifest) if plan_version == 8 else sha256(manifest_path)
        if source.get("design_system_sha256") != expected_design_hash:
            errors.append("Design System manifestのSHA-256が一致しません")

    registries = manifest.get("registries", {}) if isinstance(manifest, dict) else {}
    components_path = resolve(manifest_path.parent, registries.get("components")) if manifest_path and isinstance(registries, dict) else None
    contracts_path = resolve(manifest_path.parent, registries.get("component_contracts")) if manifest_path and isinstance(registries, dict) else None
    layouts_path = resolve(manifest_path.parent, registries.get("role_layouts")) if manifest_path and isinstance(registries, dict) else None
    semantic_path = resolve(manifest_path.parent, registries.get("semantic_visual_contracts")) if manifest_path and isinstance(registries, dict) else None
    components_doc = load(components_path) if components_path and components_path.is_file() else {}
    contracts_doc = load(contracts_path) if contracts_path and contracts_path.is_file() else {}
    layouts_doc = load(layouts_path) if layouts_path and layouts_path.is_file() else {}
    semantic_doc = load(semantic_path) if semantic_path and semantic_path.is_file() else {}
    components = {item.get("id"): item for item in components_doc.get("components", []) if isinstance(item, dict)} if isinstance(components_doc, dict) else {}
    component_contracts = {
        item.get("id"): item for item in contracts_doc.get("components", []) if isinstance(item, dict)
    } if isinstance(contracts_doc, dict) else {}
    layouts = {item.get("id"): item for item in layouts_doc.get("role_layouts", []) if isinstance(item, dict)} if isinstance(layouts_doc, dict) else {}
    semantic_contracts = {
        item.get("id"): item for item in semantic_doc.get("components", []) if isinstance(item, dict)
    } if isinstance(semantic_doc, dict) else {}
    deck_plan_path = resolve(visual_plan_path.parent, source.get("deck_plan")) if isinstance(source, dict) else None
    deck_plan = load(deck_plan_path) if deck_plan_path and deck_plan_path.is_file() else {}
    deck_plan_slides = {
        item.get("slide_id"): item for item in deck_plan.get("slides", []) if isinstance(item, dict)
    } if isinstance(deck_plan, dict) else {}

    component_ids: set[str] = set()
    layout_ids: set[str] = set()
    planned_components_by_slide: dict[int, set[str]] = {}
    planned_box_dominant_slides: set[int] = set()
    semantic_visual_violations: list[dict] = []
    funnel_guard_violations: list[dict] = []
    adjacent_repetition_violations: list[dict] = []
    planned_slides = visual_plan.get("slides", []) if isinstance(visual_plan, dict) else []
    for index, slide in enumerate(planned_slides, start=1):
        if not isinstance(slide, dict):
            errors.append(f"slides[{index}]がオブジェクトではありません")
            continue
        resolution = slide.get("design_resolution", {})
        layout_id = resolution.get("role_layout") if isinstance(resolution, dict) else None
        layout = layouts.get(layout_id)
        if layout is None:
            errors.append(f"slides[{index}]のRole Layoutが未登録です")
            continue
        layout_ids.add(layout_id)
        if plan_version == 8:
            contract = {
                "grid_id": layout.get("grid_id"), "locked": layout.get("locked", []),
                "adjustable": layout.get("adjustable", []), "content_limits": layout.get("content_limits", {}),
                "slot_frames": layout.get("slot_frames", {}),
            }
            payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            expected_contract = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if resolution.get("layout_contract_sha256") != expected_contract:
                errors.append(f"slides[{index}]のLocked Layout契約が一致しません")
            if resolution.get("slot_frames") != layout.get("slot_frames", {}):
                errors.append(f"slides[{index}]のLocked Layout実座標契約が一致しません")
            adjustments = slide.get("layout_adjustments", {})
            if not isinstance(adjustments, dict) or set(adjustments) - set(layout.get("adjustable", [])):
                errors.append(f"slides[{index}]に変更不可のLayout調整があります")
        seen_slots: set[str] = set()
        for entry in slide.get("component_plan", []):
            if not isinstance(entry, dict):
                continue
            component_id, slot = entry.get("component"), entry.get("slot")
            component = components.get(component_id)
            if component is None or slot not in component.get("slots", []):
                errors.append(f"slides[{index}]のComponentまたはslotが未登録です")
            else:
                component_ids.add(component_id)
                planned_components_by_slide.setdefault(index, set()).add(component_id)
            seen_slots.add(slot)
        if set(layout.get("slots", [])) - seen_slots:
            errors.append(f"slides[{index}]の必須slotが不足しています")
        strategy = slide.get("visual_strategy", {})
        grammar = strategy.get("visual_grammar", {}) if isinstance(strategy, dict) else {}
        if isinstance(grammar, dict) and (
            grammar.get("container_dependency") == "high"
            or grammar.get("primary_primitive") == "container_cards"
        ):
            planned_box_dominant_slides.add(index)
        component_id = main_component(slide)
        semantic = semantic_contracts.get(component_id, {})
        semantic_checks = (
            ("pattern_family", strategy.get("pattern_family") if isinstance(strategy, dict) else None, semantic.get("pattern_families")),
            ("spatial_model", grammar.get("spatial_model") if isinstance(grammar, dict) else None, semantic.get("spatial_models")),
            ("primary_primitive", grammar.get("primary_primitive") if isinstance(grammar, dict) else None, semantic.get("primary_primitives")),
        )
        for field, actual, allowed in semantic_checks:
            if semantic and isinstance(allowed, list) and actual not in allowed:
                violation = {
                    "slide_number": index, "component_id": component_id,
                    "field": field, "actual": actual, "allowed": allowed,
                }
                semantic_visual_violations.append(violation)
                errors.append(f"slides[{index}]の{field}が{component_id}の意味契約と一致しません")
        visual_text = flattened_text(strategy).lower()
        if any(token.lower() in visual_text for token in FUNNEL_TOKENS):
            plan_slide = deck_plan_slides.get(slide.get("slide_id"), {})
            plan_text = flattened_text(plan_slide).lower()
            cohort_state = strategy.get("cohort_continuity") if isinstance(strategy, dict) else None
            if cohort_state != "continuous" or any(token.lower() in plan_text for token in INDEPENDENT_COHORT_TOKENS):
                violation = {
                    "slide_number": index, "cohort_continuity": cohort_state,
                    "reason": "漏斗・先細り表現に連続母集団の証拠がない",
                }
                funnel_guard_violations.append(violation)
                errors.append(f"slides[{index}]は異なる／未確認の母集団を漏斗・先細りで表現しています")

    repetition_policy = visual_plan.get("deck", {}).get("repetition_policy", "strict") if isinstance(visual_plan.get("deck"), dict) else "strict"
    if repetition_policy != "consistent":
        valid_slides = [slide for slide in planned_slides if isinstance(slide, dict)]
        for previous, current in zip(valid_slides, valid_slides[1:]):
            previous_resolution = previous.get("design_resolution", {})
            current_resolution = current.get("design_resolution", {})
            same_layout = previous_resolution.get("role_layout") == current_resolution.get("role_layout")
            same_component = main_component(previous) == main_component(current)
            strategy = current.get("visual_strategy", {})
            rationale = strategy.get("adjacent_repetition_rationale") if isinstance(strategy, dict) else None
            if same_layout and same_component and not rationale:
                violation = {
                    "slide_number": current.get("slide_number"),
                    "role_layout": current_resolution.get("role_layout"),
                    "component_id": main_component(current),
                }
                adjacent_repetition_violations.append(violation)
                errors.append(f"slides[{current.get('slide_number')}]は隣接ページと同じRole Layout・main componentです")

    design_system = visual_plan.get("deck", {}).get("design_system", {}) if isinstance(visual_plan.get("deck"), dict) else {}
    theme_id = design_system.get("theme") if isinstance(design_system, dict) else None
    themes = manifest.get("themes", {}) if isinstance(manifest, dict) else {}
    theme_path = resolve(manifest_path.parent, themes.get(theme_id)) if manifest_path and isinstance(themes, dict) else None
    token_colors: set[str] = set()
    token_sizes: set[float] = set()
    if theme_path and theme_path.is_file():
        theme = load(theme_path)
        base_path = resolve(manifest_path.parent, themes.get("base")) if isinstance(theme, dict) and theme.get("extends") == "base" else None
        if base_path and base_path.is_file():
            flatten_token_values(load(base_path), token_colors, token_sizes)
        flatten_token_values(theme, token_colors, token_sizes)
    else:
        errors.append("Visual Planで指定したThemeが見つかりません")

    if plan_version == 8:
        direction_path = resolve(visual_plan_path.parent, source.get("design_direction_scout"))
        if direction_path is None or not direction_path.is_file():
            errors.append("Design Direction Scoutが見つかりません")
        else:
            if source.get("design_direction_sha256") != sha256(direction_path):
                errors.append("Design Direction ScoutのSHA-256が一致しません")
            direction = load(direction_path)
            selected_style = direction.get("selected", {}).get("style_profile") if isinstance(direction, dict) else None
            if direction.get("status") != "selected" or selected_style != design_system.get("style_profile"):
                errors.append("選択済みDesign DirectionとVisual Planが一致しません")

    pptx_colors, pptx_sizes, slide_count, anti_metrics = extract_pptx_style_values(pptx)
    traceability = extract_component_traceability(pptx)
    geometry_violations = (
        locked_layout_geometry_violations(traceability, planned_slides, layouts)
        if plan_version == 8 else []
    )
    for violation in geometry_violations:
        errors.append(
            f"slides[{violation['slide_number']}]のLocked Layout実座標違反: "
            f"{violation.get('component_id')} / {violation.get('kind')}"
        )
    trace_by_slide = {
        item["slide_number"]: set(item.get("component_ids", []))
        for item in traceability.get("slides", [])
    }
    traceability_missing: list[dict] = []
    for slide_number, planned in planned_components_by_slide.items():
        required = {
            component_id for component_id in planned
            if components.get(component_id, {}).get("implementation") in {
                "native_components_v4", "native_components_v4_alias"
            }
        }
        missing = sorted(required - trace_by_slide.get(slide_number, set()))
        if missing:
            traceability_missing.append({"slide_number": slide_number, "component_ids": missing})
            errors.append(
                f"slides[{slide_number}]のNative Component実体がPPTX Shape Name／Alt Textにありません: {missing}"
            )
    contract_violations = component_contract_violations(traceability, component_contracts)
    for violation in contract_violations:
        errors.append(
            f"slides[{violation['slide_number']}]の{violation['component_id']}が"
            f"推奨上限{violation['recommended_max']}件を超えています"
        )
    if traceability.get("native_element_ratio", 0) < 0.8:
        errors.append("平均Native Element Ratioが0.8未満です")
    if traceability.get("premium_theme_composition_pass") is False:
        errors.append("Premium 15のTheme差が構図差として確認できません")
    connector_violations = connector_direction_violations(pptx, planned_slides)
    for violation in connector_violations:
        errors.append(
            f"slides[{violation['slide_number']}]の左→右主読順に対して矢印端点が逆です"
        )
    color_ratio = ratio(pptx_colors, token_colors)
    size_ratio = ratio(pptx_sizes, token_sizes)
    token_match_ratio = round((color_ratio + size_ratio) / 2, 4)
    if slide_count != len(planned_slides):
        errors.append("PPTXとVisual Planのページ数が一致しません")
    anti_slop_failures: list[str] = []
    if plan_version == 8:
        anti_path = resolve(manifest_path.parent, registries.get("anti_slop_rules")) if manifest_path else None
        anti_doc = load(anti_path) if anti_path and anti_path.is_file() else {}
        exceptions = design_system.get("anti_slop_exceptions", []) if isinstance(design_system, dict) else []
        exception_ids = {item.get("id") for item in exceptions if isinstance(item, dict) and item.get("reason")}
        metric_map = {
            "gradient_fill": "gradient_fill_count", "glow_effect": "glow_effect_count",
            "rounded_rectangle_ratio": "rounded_rectangle_ratio",
            "equal_area_rectangle_ratio": "equal_area_rectangle_ratio",
            "repeated_image_hash_ratio": "repeated_image_hash_ratio",
        }
        equal_area_by_slide = anti_metrics.get("equal_area_rectangle_ratio_by_slide", {})
        if isinstance(equal_area_by_slide, dict):
            audited_equal_area = [
                float(value)
                for slide_number, value in equal_area_by_slide.items()
                if int(slide_number) in planned_box_dominant_slides and not (
                    planned_components_by_slide.get(int(slide_number), set())
                    & SEMANTIC_EQUAL_AREA_COMPONENTS
                )
            ]
            anti_metrics["equal_area_rectangle_ratio_raw"] = anti_metrics.get(
                "equal_area_rectangle_ratio", 0
            )
            anti_metrics["equal_area_rectangle_ratio"] = (
                round(max(audited_equal_area), 4) if audited_equal_area else 0.0
            )
        for rule in anti_doc.get("avoid", []) if isinstance(anti_doc, dict) else []:
            if not isinstance(rule, dict) or rule.get("id") in exception_ids or rule.get("machine_signal") == "human_review":
                continue
            metric = metric_map.get(rule.get("machine_signal"))
            if metric is None:
                continue
            value = anti_metrics.get(metric, 0)
            limit = rule.get("max_ratio", rule.get("max_count"))
            if isinstance(limit, (int, float)) and value > limit:
                anti_slop_failures.append(f"{rule.get('id')}: {value} > {limit}")
    passed = not errors and not anti_slop_failures and token_match_ratio >= args.min_token_match_ratio
    result = {
        "version": 2 if plan_version == 8 else 1,
        "source_pptx": str(pptx),
        "source_pptx_sha256": sha256(pptx),
        "visual_plan": str(visual_plan_path),
        "visual_plan_sha256": sha256(visual_plan_path),
        "design_system_manifest": str(manifest_path) if manifest_path else None,
        "design_system_manifest_sha256": (
            design_system_fingerprint(manifest_path, manifest) if plan_version == 8 and manifest_path and manifest_path.is_file()
            else sha256(manifest_path) if manifest_path and manifest_path.is_file() else None
        ),
        "slide_count": slide_count,
        "pass": passed,
        "summary": {
            "planned_component_count": len(component_ids),
            "planned_role_layout_count": len(layout_ids),
            "explicit_color_token_match_ratio": color_ratio,
            "explicit_font_size_token_match_ratio": size_ratio,
            "design_token_match_ratio": token_match_ratio,
            "minimum_design_token_match_ratio": args.min_token_match_ratio,
            "component_traceability": "pptx_shape_name_and_alt_text",
            "component_traceability_pass": not traceability_missing,
            "native_element_ratio": traceability.get("native_element_ratio"),
            "component_trace_coverage_ratio": traceability.get("trace_coverage_ratio"),
            "premium_theme_composition_pass": traceability.get("premium_theme_composition_pass"),
            "component_contract_pass": not contract_violations,
            "semantic_visual_fit_pass": not semantic_visual_violations,
            "funnel_guard_pass": not funnel_guard_violations,
            "adjacent_repetition_pass": not adjacent_repetition_violations,
            "connector_direction_pass": not connector_violations,
            "locked_layout_contract_pass": not any("Locked Layout" in error for error in errors),
            "locked_layout_geometry_pass": not geometry_violations,
            "design_direction_selection_traceability_pass": not any("Design Direction" in error for error in errors),
            "anti_slop_pass": not anti_slop_failures,
            "anti_slop_metrics": anti_metrics,
        },
        "observations": {
            "unmatched_colors": sorted(set(pptx_colors) - token_colors),
            "unmatched_font_sizes": sorted(set(pptx_sizes) - token_sizes),
            "errors": errors,
            "anti_slop_failures": anti_slop_failures,
            "component_traceability_missing": traceability_missing,
            "component_contract_violations": contract_violations,
            "semantic_visual_violations": semantic_visual_violations,
            "funnel_guard_violations": funnel_guard_violations,
            "adjacent_repetition_violations": adjacent_repetition_violations,
            "connector_direction_violations": connector_violations,
            "locked_layout_geometry_violations": geometry_violations,
            "premium_theme_composition": traceability.get("premium_theme_composition", {}),
            "limitation": (
                "単一Themeの実デッキではTheme間構図差は非該当。"
                "Premium Galleryで同一Componentの3 Themeを比較する"
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Design System監査を作成しました: {args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
