#!/usr/bin/env python3
"""Visual Plan v8のDirection・Locked Layout・Renderer契約を検証する。"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import yaml

from validate_visual_plan_v7 import validate_v7


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


def contract_sha256(layout: dict) -> str:
    contract = {
        "grid_id": layout.get("grid_id"), "locked": layout.get("locked", []),
        "adjustable": layout.get("adjustable", []), "content_limits": layout.get("content_limits", {}),
        "slot_frames": layout.get("slot_frames", {}),
    }
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def registry(manifest_path: Path, manifest: dict, key: str, collection: str, errors: list[str]) -> dict[str, dict]:
    target = resolve(manifest_path.parent, manifest.get("registries", {}).get(key))
    if target is None or not target.is_file():
        errors.append(f"design_system.registries.{key}: 実在するファイルが必要です")
        return {}
    document = load(target)
    items = document.get(collection) if isinstance(document, dict) else None
    if not isinstance(items, list):
        errors.append(f"design_system.registries.{key}: {collection}配列が必要です")
        return {}
    return {item.get("id"): item for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}


FUNNEL_TOKENS = ("funnel", "漏斗", "taper", "narrow", "細く", "先細", "縮小")
INDEPENDENT_COHORT_TOKENS = ("母数が異", "異なる母数", "同一母集団ではなく", "別母集団", "非連続")


def main_component(slide: dict) -> str | None:
    entries = slide.get("component_plan", [])
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("slot") == "main":
                return entry.get("component")
    resolution = slide.get("design_resolution", {})
    return resolution.get("component_hint") if isinstance(resolution, dict) else None


def flattened_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(flattened_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flattened_text(item) for item in value)
    return str(value) if value is not None else ""


def validate_v8(path: Path, data: dict) -> list[str]:
    compatible = copy.deepcopy(data)
    compatible["version"] = 7
    preliminary_source = data.get("source", {}) if isinstance(data, dict) else {}
    preliminary_manifest = resolve(path.parent, preliminary_source.get("design_system_manifest")) if isinstance(preliminary_source, dict) else None
    if preliminary_manifest and preliminary_manifest.is_file():
        compatible.setdefault("source", {})["design_system_sha256"] = sha256(preliminary_manifest)
    errors = validate_v7(path, compatible)
    source = data.get("source", {})
    deck = data.get("deck", {})
    if not isinstance(source, dict) or not isinstance(deck, dict):
        return errors
    manifest_path = resolve(path.parent, source.get("design_system_manifest"))
    if manifest_path is None or not manifest_path.is_file():
        return errors
    manifest = load(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("version") != 2:
        errors.append("source.design_system_manifest: v8ではversion 2が必要です")
        return errors
    expected_design_system_hash = design_system_fingerprint(manifest_path, manifest)
    if source.get("design_system_sha256") != expected_design_system_hash:
        errors.append(f"source.design_system_sha256: {expected_design_system_hash}にしてください")
    direction_path = resolve(path.parent, source.get("design_direction_scout"))
    if direction_path is None or not direction_path.is_file():
        errors.append("source.design_direction_scout: 選択済みScoutを指定してください")
        direction = {}
    else:
        if source.get("design_direction_sha256") != sha256(direction_path):
            errors.append(f"source.design_direction_sha256: {sha256(direction_path)}にしてください")
        direction = load(direction_path)
        if not isinstance(direction, dict) or direction.get("status") != "selected" or not isinstance(direction.get("selected"), dict):
            errors.append("source.design_direction_scout: status=selectedが必要です")
            direction = {}
    if isinstance(direction, dict) and direction:
        direction_source = direction.get("source", {})
        if direction_source.get("deck_plan_sha256") != source.get("deck_plan_sha256"):
            errors.append("source.design_direction_scout: Deck Plan fingerprintが一致しません")
        if direction_source.get("design_system_sha256") != expected_design_system_hash:
            errors.append("source.design_direction_scout: Design System fingerprintが一致しません")

    layouts = registry(manifest_path, manifest, "role_layouts", "role_layouts", errors)
    components = registry(manifest_path, manifest, "components", "components", errors)
    component_contracts = registry(manifest_path, manifest, "component_contracts", "components", errors)
    grids = registry(manifest_path, manifest, "layout_grids", "grids", errors)
    styles = registry(manifest_path, manifest, "style_profiles", "style_profiles", errors)
    densities = registry(manifest_path, manifest, "density_profiles", "density_profiles", errors)
    sequences = registry(manifest_path, manifest, "deck_sequences", "deck_sequences", errors)
    semantic_contracts = registry(
        manifest_path, manifest, "semantic_visual_contracts", "components", errors
    )
    router_path = resolve(manifest_path.parent, manifest.get("registries", {}).get("renderer_router"))
    router = load(router_path) if router_path and router_path.is_file() else {}
    routes = router.get("routes", []) if isinstance(router, dict) else []

    design_system = deck.get("design_system", {})
    if not isinstance(design_system, dict):
        errors.append("deck.design_system: オブジェクトで必須です")
        design_system = {}
    style_id = design_system.get("style_profile")
    if style_id not in styles:
        errors.append("deck.design_system.style_profile: 未登録です")
    selected_style = direction.get("selected", {}).get("style_profile") if isinstance(direction, dict) else None
    if selected_style and style_id != selected_style:
        errors.append("deck.design_system.style_profile: Design Directionの選択と一致させてください")
    if design_system.get("density_profile") not in densities:
        errors.append("deck.design_system.density_profile: 未登録です")
    if design_system.get("deck_sequence") not in sequences:
        errors.append("deck.design_system.deck_sequence: 未登録です")
    if deck.get("anti_slop_acknowledged") is not True:
        errors.append("deck.anti_slop_acknowledged: trueで必須です")
    exceptions = design_system.get("anti_slop_exceptions", [])
    if not isinstance(exceptions, list):
        errors.append("deck.design_system.anti_slop_exceptions: 配列にしてください")
    else:
        allowed_path = resolve(manifest_path.parent, manifest.get("registries", {}).get("anti_slop_rules"))
        anti_doc = load(allowed_path) if allowed_path and allowed_path.is_file() else {}
        allowed = set(anti_doc.get("allow_with_rationale", [])) if isinstance(anti_doc, dict) else set()
        for index, item in enumerate(exceptions, start=1):
            if not isinstance(item, dict) or item.get("id") not in allowed or not item.get("reason"):
                errors.append(f"deck.design_system.anti_slop_exceptions[{index}]: 許可IDと理由が必要です")

    deck_plan_path = resolve(path.parent, source.get("deck_plan"))
    deck_plan = load(deck_plan_path) if deck_plan_path and deck_plan_path.is_file() else {}
    plan_slides = {item.get("slide_id"): item for item in deck_plan.get("slides", []) if isinstance(item, dict)} if isinstance(deck_plan, dict) else {}
    visual_slides = data.get("slides", [])
    for index, slide in enumerate(visual_slides, start=1):
        if not isinstance(slide, dict):
            continue
        location = f"slides[{index}]"
        resolution = slide.get("design_resolution", {})
        layout = layouts.get(resolution.get("role_layout")) if isinstance(resolution, dict) else None
        if layout is None:
            continue
        if resolution.get("grid_id") != layout.get("grid_id") or resolution.get("grid_id") not in grids:
            errors.append(f"{location}.design_resolution.grid_id: Role Layoutの登録値と一致させてください")
        expected_contract = contract_sha256(layout)
        if resolution.get("layout_contract_sha256") != expected_contract:
            errors.append(f"{location}.design_resolution.layout_contract_sha256: {expected_contract}にしてください")
        if resolution.get("slot_frames") != layout.get("slot_frames", {}):
            errors.append(f"{location}.design_resolution.slot_frames: Role Layoutの実座標契約と一致させてください")
        resolved_variant = resolution.get("variant")
        if resolved_variant not in {"primary", "alternate", "dense"}:
            errors.append(f"{location}.design_resolution.variant: 未対応です")
        adjustments = slide.get("layout_adjustments")
        if not isinstance(adjustments, dict):
            errors.append(f"{location}.layout_adjustments: オブジェクトで必須です")
        else:
            invalid = set(adjustments) - set(layout.get("adjustable", []))
            locked = set(adjustments) & set(layout.get("locked", []))
            if invalid:
                errors.append(f"{location}.layout_adjustments: 変更不可項目があります {sorted(invalid)}")
            if locked:
                errors.append(f"{location}.layout_adjustments: locked項目を変更できません {sorted(locked)}")

        plan_slide = plan_slides.get(slide.get("slide_id"), {})
        relationship = plan_slide.get("relationship") if isinstance(plan_slide, dict) else None
        route = next((item for item in routes if item.get("relationship") == relationship), None)
        strategy = slide.get("visual_strategy", {})
        decision = strategy.get("renderer_decision", {}) if isinstance(strategy, dict) else {}
        selected = decision.get("selected") if isinstance(decision, dict) else None
        if route and selected != route.get("preferred") and not decision.get("override_rationale"):
            errors.append(f"{location}.visual_strategy.renderer_decision.override_rationale: Router規則を外す場合は必須です")
        planned_components: set[str] = set()
        for component_index, entry in enumerate(slide.get("component_plan", []), start=1):
            if not isinstance(entry, dict):
                continue
            component_id = entry.get("component")
            planned_components.add(component_id)
            component = components.get(component_id, {})
            contract = component_contracts.get(component_id)
            if contract is None:
                errors.append(f"{location}.component_plan[{component_index}]: Component Contractがありません")
                continue
            variant = entry.get("variant", resolved_variant)
            if variant not in contract.get("variants", component.get("variants", [])):
                errors.append(
                    f"{location}.component_plan[{component_index}].variant: "
                    f"{component_id}で未宣言です"
                )
            if "content" in entry:
                errors.append(
                    f"{location}.component_plan[{component_index}].content: "
                    "内容はDeck PlanからCompose時に流し込み、Visual Planへ複製しないでください"
                )
            token_overrides = entry.get("token_overrides", {})
            if token_overrides and (
                not isinstance(token_overrides, dict)
                or set(token_overrides) - {"accent", "accent2", "warning", "danger", "success", "font"}
            ):
                errors.append(
                    f"{location}.component_plan[{component_index}].token_overrides: "
                    "許可された意味トークンだけを指定してください"
                )
        component_hint = resolution.get("component_hint")
        if component_hint and component_hint not in planned_components:
            errors.append(f"{location}.design_resolution.component_hint: component_planの実体と一致しません")

        main_id = main_component(slide)
        semantic = semantic_contracts.get(main_id, {})
        grammar = strategy.get("visual_grammar", {}) if isinstance(strategy, dict) else {}
        checks = (
            ("pattern_family", strategy.get("pattern_family"), semantic.get("pattern_families")),
            ("visual_grammar.spatial_model", grammar.get("spatial_model"), semantic.get("spatial_models")),
            ("visual_grammar.primary_primitive", grammar.get("primary_primitive"), semantic.get("primary_primitives")),
        )
        if semantic:
            for field, actual, allowed in checks:
                if isinstance(allowed, list) and actual not in allowed:
                    errors.append(
                        f"{location}.{field}: main component {main_id}の意味契約では{allowed}から選んでください"
                    )

        visual_text = flattened_text(strategy).lower()
        funnel_like = any(token.lower() in visual_text for token in FUNNEL_TOKENS)
        plan_text = flattened_text(plan_slide).lower()
        cohort_state = strategy.get("cohort_continuity") if isinstance(strategy, dict) else None
        if funnel_like:
            if cohort_state != "continuous":
                errors.append(
                    f"{location}.visual_strategy.cohort_continuity: 漏斗・先細り表現はcontinuousのみ使用できます"
                )
            if any(token.lower() in plan_text for token in INDEPENDENT_COHORT_TOKENS):
                errors.append(
                    f"{location}.visual_strategy: Deck Planが異なる母集団を示すため漏斗・先細り表現は使用できません"
                )

    repetition_policy = deck.get("repetition_policy", "strict")
    if isinstance(visual_slides, list) and repetition_policy != "consistent":
        valid_slides = [slide for slide in visual_slides if isinstance(slide, dict)]
        for previous, current in zip(valid_slides, valid_slides[1:]):
            previous_resolution = previous.get("design_resolution", {})
            current_resolution = current.get("design_resolution", {})
            same_layout = (
                isinstance(previous_resolution, dict)
                and isinstance(current_resolution, dict)
                and previous_resolution.get("role_layout") == current_resolution.get("role_layout")
            )
            same_component = main_component(previous) == main_component(current)
            strategy = current.get("visual_strategy", {})
            rationale = strategy.get("adjacent_repetition_rationale") if isinstance(strategy, dict) else None
            if same_layout and same_component and not rationale:
                errors.append(
                    f"slides[{current.get('slide_number')}].visual_strategy.adjacent_repetition_rationale: "
                    "隣接ページで同じRole Layoutとmain componentを使う場合は反復理由が必要です"
                )
    return errors
