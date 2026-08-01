#!/usr/bin/env python3
"""Visual Plan v7のDesign System解決契約を検証する。"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

from validate_visual_plan_v6 import validate_v6


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _load(path: Path) -> object:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _overlong_layout_run(layouts: list[str], limit: int) -> bool:
    previous = None
    run = 0
    for layout in layouts:
        run = run + 1 if layout == previous else 1
        previous = layout
        if run > limit:
            return True
    return False


def validate_v7(path: Path, data: dict) -> list[str]:
    compatible = copy.deepcopy(data)
    compatible["version"] = 6
    errors = validate_v6(path, compatible)

    source = data.get("source", {})
    deck = data.get("deck", {})
    slides = data.get("slides", [])
    manifest_path = _resolve(path.parent, source.get("design_system_manifest")) if isinstance(source, dict) else None
    if manifest_path is None or not manifest_path.is_file():
        errors.append("source.design_system_manifest: 実在するDesign System manifestを指定してください")
        return errors
    if source.get("design_system_sha256") != _sha256(manifest_path):
        errors.append(f"source.design_system_sha256: {_sha256(manifest_path)}にしてください")
    try:
        manifest = _load(manifest_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"source.design_system_manifest: 読み込めません: {exc}")
        return errors
    if not isinstance(manifest, dict) or manifest.get("version") not in {1, 2}:
        errors.append("source.design_system_manifest: version 1または2を指定してください")
        return errors

    def load_registry(name: str, collection: str) -> dict[str, dict]:
        registries = manifest.get("registries", {})
        target = _resolve(manifest_path.parent, registries.get(name) if isinstance(registries, dict) else None)
        if target is None or not target.is_file():
            errors.append(f"design_system.registries.{name}: 実在するファイルが必要です")
            return {}
        document = _load(target)
        items = document.get(collection) if isinstance(document, dict) else None
        if not isinstance(items, list):
            errors.append(f"design_system.registries.{name}: {collection}配列が必要です")
            return {}
        return {item.get("id"): item for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}

    components = load_registry("components", "components")
    layouts = load_registry("role_layouts", "role_layouts")
    grammars = load_registry("grammars", "grammars")
    themes = manifest.get("themes", {}) if isinstance(manifest.get("themes"), dict) else {}

    design_system = deck.get("design_system") if isinstance(deck, dict) else None
    if not isinstance(design_system, dict):
        errors.append("deck.design_system: オブジェクトで必須です")
        design_system = {}
    grammar_id = design_system.get("composition_grammar")
    theme_id = design_system.get("theme")
    if grammar_id not in grammars:
        errors.append("deck.design_system.composition_grammar: 未登録grammarです")
    if theme_id not in themes:
        errors.append("deck.design_system.theme: 未登録themeです")

    deck_plan_path = _resolve(path.parent, source.get("deck_plan")) if isinstance(source, dict) else None
    deck_plan = _load(deck_plan_path) if deck_plan_path and deck_plan_path.is_file() else {}
    plan_slides = {
        item.get("slide_id"): item for item in deck_plan.get("slides", [])
        if isinstance(item, dict) and isinstance(item.get("slide_id"), str)
    } if isinstance(deck_plan, dict) else {}
    role_map = manifest.get("defaults", {}).get("role_by_slide_purpose", {}) if isinstance(manifest.get("defaults"), dict) else {}
    repetition_policy = deck_plan.get("deck", {}).get("repetition_policy", "strict") if isinstance(deck_plan, dict) else "strict"
    layout_run_limit = {"strict": 2, "balanced": 3, "consistent": 4}.get(repetition_policy, 2)
    ordered_layouts: list[str] = []

    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            continue
        location = f"slides[{index}]"
        resolution = slide.get("design_resolution")
        if not isinstance(resolution, dict):
            errors.append(f"{location}.design_resolution: オブジェクトで必須です")
            continue
        for key in ("role", "role_layout", "variant"):
            if resolution.get(key) in (None, "", []):
                errors.append(f"{location}.design_resolution.{key}: 必須です")
        layout_id = resolution.get("role_layout")
        layout = layouts.get(layout_id)
        if layout is None:
            errors.append(f"{location}.design_resolution.role_layout: 未登録layoutです")
            continue
        ordered_layouts.append(layout_id)
        if resolution.get("role") != layout.get("role"):
            errors.append(f"{location}.design_resolution.role: Role Layoutと一致させてください")
        if resolution.get("variant") not in layout.get("variants", []):
            errors.append(f"{location}.design_resolution.variant: Role Layoutのvariantから選んでください")
        plan_slide = plan_slides.get(slide.get("slide_id"), {})
        purpose = plan_slide.get("slide_purpose") if isinstance(plan_slide, dict) else None
        expected_role = role_map.get(purpose)
        if resolution.get("role") != expected_role:
            errors.append(f"{location}.design_resolution.role: slide_purpose={purpose}では{expected_role}にしてください")
        if purpose not in layout.get("purposes", []):
            errors.append(f"{location}.design_resolution.role_layout: slide_purpose={purpose}に対応していません")

        component_plan = slide.get("component_plan")
        if not isinstance(component_plan, list) or not component_plan:
            errors.append(f"{location}.component_plan: 1件以上の配列で必須です")
            continue
        seen_slots: set[str] = set()
        for component_index, entry in enumerate(component_plan, start=1):
            entry_location = f"{location}.component_plan[{component_index}]"
            if not isinstance(entry, dict):
                errors.append(f"{entry_location}: componentとslotを持つオブジェクトにしてください")
                continue
            component_id, slot = entry.get("component"), entry.get("slot")
            component = components.get(component_id)
            if component is None:
                errors.append(f"{entry_location}.component: 未登録componentです")
            elif slot not in component.get("slots", []):
                errors.append(f"{entry_location}.slot: {component_id}が対応しないslotです")
            if slot not in layout.get("slots", []):
                errors.append(f"{entry_location}.slot: Role Layoutに存在しません")
            if slot in seen_slots:
                errors.append(f"{entry_location}.slot: 重複しています")
            elif isinstance(slot, str):
                seen_slots.add(slot)
        missing_slots = set(layout.get("slots", [])) - seen_slots
        if missing_slots:
            errors.append(f"{location}.component_plan: 必須slotが不足しています {sorted(missing_slots)}")

    if _overlong_layout_run(ordered_layouts, layout_run_limit):
        errors.append(f"design_system_quality: 同じrole_layoutは{layout_run_limit}ページを超えて連続できません")
    return errors
