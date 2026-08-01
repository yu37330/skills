#!/usr/bin/env python3
"""Theme-independent PowerPoint Design Systemの契約を検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ROLES = {"title", "evidence", "comparison", "synthesis", "recommendation", "decision", "action", "reference"}
DECK_TYPES = {"executive_decision", "proposal", "analysis_report", "operating_review", "training"}


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _load(path: Path) -> object:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _resolve(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def design_system_fingerprint(path: Path, manifest: dict | None = None) -> str:
    """manifest、契約、Theme、描画実装をまとめた再現可能なSHA-256を返す。"""
    manifest = manifest or _load(path)
    entries: dict[str, str] = {"manifest": hashlib.sha256(path.read_bytes()).hexdigest()}
    for group in ("registries", "themes"):
        values = manifest.get(group, {}) if isinstance(manifest, dict) else {}
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            target = _resolve(path.parent, value)
            if target and target.is_file():
                entries[f"{group}:{key}"] = hashlib.sha256(target.read_bytes()).hexdigest()
    implementation = manifest.get("implementation", []) if isinstance(manifest, dict) else []
    if isinstance(implementation, list):
        for index, value in enumerate(implementation):
            target = _resolve(path.parent, value)
            if target and target.is_file():
                entries[f"implementation:{index}:{target.name}"] = hashlib.sha256(target.read_bytes()).hexdigest()
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _unique_ids(items: object, location: str, errors: list[str]) -> dict[str, dict]:
    if not isinstance(items, list) or not items:
        errors.append(f"{location}: 1件以上の配列にしてください")
        return {}
    result: dict[str, dict] = {}
    for index, item in enumerate(items, start=1):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_location}: オブジェクトにしてください")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"{item_location}.id: 空でない文字列にしてください")
        elif item_id in result:
            errors.append(f"{item_location}.id: 重複しています")
        else:
            result[item_id] = item
    return result


def validate_manifest(path: Path) -> tuple[list[str], dict]:
    errors: list[str] = []
    try:
        manifest = _load(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"manifest: 読み込めません: {exc}"], {}
    if not isinstance(manifest, dict) or manifest.get("version") not in {1, 2}:
        return ["manifest.version: 1または2を指定してください"], {}

    registries = manifest.get("registries")
    if not isinstance(registries, dict):
        return ["manifest.registries: オブジェクトで必須です"], {}
    loaded: dict[str, object] = {"manifest": manifest}
    required_registries = ["components", "role_layouts", "grammars"]
    if manifest.get("version") == 2:
        required_registries.extend([
            "component_contracts",
            "layout_grids", "style_profiles", "density_profiles", "context_models",
            "deck_sequences", "renderer_router", "anti_slop_rules", "style_selection_index",
            "semantic_visual_contracts",
        ])
        implementation = manifest.get("implementation")
        if not isinstance(implementation, list) or not implementation:
            errors.append("manifest.implementation: 1件以上の実装ファイル配列が必要です")
        else:
            for index, value in enumerate(implementation):
                target = _resolve(path.parent, value)
                if target is None or not target.is_file():
                    errors.append(f"manifest.implementation[{index}]: 実在するファイルを指定してください")
    for key in required_registries:
        target = _resolve(path.parent, registries.get(key))
        if target is None or not target.is_file():
            errors.append(f"manifest.registries.{key}: 実在するファイルを指定してください")
            continue
        try:
            loaded[key] = _load(target)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"manifest.registries.{key}: 読み込めません: {exc}")

    themes = manifest.get("themes")
    if not isinstance(themes, dict):
        errors.append("manifest.themes: オブジェクトで必須です")
        themes = {}
    theme_data: dict[str, dict] = {}
    for theme_id, value in themes.items():
        target = _resolve(path.parent, value)
        if target is None or not target.is_file():
            errors.append(f"manifest.themes.{theme_id}: 実在するJSONを指定してください")
            continue
        try:
            data = _load(target)
        except (OSError, ValueError) as exc:
            errors.append(f"manifest.themes.{theme_id}: 読み込めません: {exc}")
            continue
        if not isinstance(data, dict) or data.get("id") != theme_id:
            errors.append(f"manifest.themes.{theme_id}: JSON内のidを一致させてください")
        else:
            theme_data[theme_id] = data
    loaded["themes"] = theme_data
    base_theme = theme_data.get("base", {})
    base_font_sizes = base_theme.get("fontSizes", {}) if isinstance(base_theme, dict) else {}
    if not isinstance(base_font_sizes, dict) or base_font_sizes.get("source", 0) < 12:
        errors.append("manifest.themes.base.fontSizes.source: 日本語出典の下限12pt以上にしてください")

    component_doc = loaded.get("components", {})
    components = _unique_ids(component_doc.get("components") if isinstance(component_doc, dict) else None, "components", errors)
    contract_doc = loaded.get("component_contracts", {})
    component_contracts = _unique_ids(
        contract_doc.get("components") if isinstance(contract_doc, dict) else None,
        "component_contracts",
        errors,
    ) if manifest.get("version") == 2 else {}
    try:
        from sdpm_native_components import list_components
        implemented_native_components = set(list_components())
    except (ImportError, OSError, ValueError) as exc:
        implemented_native_components = set()
        errors.append(f"component実装を読み込めません: {exc}")
    for component_id, component in components.items():
        for key in ("kind", "slots", "implementation", "editable"):
            if component.get(key) in (None, "", []):
                errors.append(f"components.{component_id}.{key}: 必須です")
        if component.get("editable") is not True:
            errors.append(f"components.{component_id}.editable: trueにしてください")
        if not isinstance(component.get("slots"), list):
            errors.append(f"components.{component_id}.slots: 配列にしてください")
        implementation = component.get("implementation")
        if implementation in {"native_components_v4", "native_components_v4_alias"}:
            if component_id not in component_contracts:
                errors.append(f"components.{component_id}: Component Contractがありません")
            if component_id not in implemented_native_components:
                errors.append(f"components.{component_id}: Native Component実装がありません")
        variants = component.get("variants")
        if not isinstance(variants, list) or not variants:
            errors.append(f"components.{component_id}.variants: 1件以上の配列にしてください")
    for component_id in component_contracts:
        if component_id not in components:
            errors.append(f"component_contracts.{component_id}: Registryに未登録です")
    loaded["component_map"] = components
    loaded["component_contract_map"] = component_contracts

    semantic_doc = loaded.get("semantic_visual_contracts", {})
    semantic_contracts = _unique_ids(
        semantic_doc.get("components") if isinstance(semantic_doc, dict) else None,
        "semantic_visual_contracts",
        errors,
    ) if manifest.get("version") == 2 else {}
    for component_id, contract in semantic_contracts.items():
        if component_id not in components:
            errors.append(f"semantic_visual_contracts.{component_id}: 未登録componentです")
        for key in ("pattern_families", "spatial_models", "primary_primitives"):
            values = contract.get(key)
            if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
                errors.append(f"semantic_visual_contracts.{component_id}.{key}: 1件以上の文字列配列にしてください")
    loaded["semantic_visual_contract_map"] = semantic_contracts

    grid_doc = loaded.get("layout_grids", {})
    grids = _unique_ids(grid_doc.get("grids") if isinstance(grid_doc, dict) else None, "layout_grids", errors) if manifest.get("version") == 2 else {}
    for grid_id, grid in grids.items():
        slots = grid.get("slots")
        if not isinstance(slots, dict) or not slots:
            errors.append(f"layout_grids.{grid_id}.slots: オブジェクトで必須です")
            continue
        for slot, box in slots.items():
            if not isinstance(box, dict) or any(not isinstance(box.get(key), (int, float)) for key in ("x", "y", "w", "h")):
                errors.append(f"layout_grids.{grid_id}.slots.{slot}: x/y/w/hを数値で指定してください")
    loaded["grid_map"] = grids

    layout_doc = loaded.get("role_layouts", {})
    layouts = _unique_ids(layout_doc.get("role_layouts") if isinstance(layout_doc, dict) else None, "role_layouts", errors)
    for layout_id, layout in layouts.items():
        role = layout.get("role")
        if role not in ROLES:
            errors.append(f"role_layouts.{layout_id}.role: 未対応の値です")
        for key in ("purposes", "variants", "slots", "default_components"):
            if layout.get(key) in (None, "", []):
                errors.append(f"role_layouts.{layout_id}.{key}: 必須です")
        slots = layout.get("slots") if isinstance(layout.get("slots"), list) else []
        defaults = layout.get("default_components")
        if isinstance(defaults, dict):
            for slot, component_id in defaults.items():
                if slot not in slots:
                    errors.append(f"role_layouts.{layout_id}: 未定義slot {slot}を使用しています")
                component = components.get(component_id)
                if component is None:
                    errors.append(f"role_layouts.{layout_id}: 未登録component {component_id}です")
                elif slot not in component.get("slots", []):
                    errors.append(f"role_layouts.{layout_id}: {component_id}はslot {slot}に対応していません")
        else:
            errors.append(f"role_layouts.{layout_id}.default_components: オブジェクトにしてください")
        if manifest.get("version") == 2:
            grid_id = layout.get("grid_id")
            if grid_id not in grids:
                errors.append(f"role_layouts.{layout_id}.grid_id: 未登録gridです")
            locked = layout.get("locked")
            adjustable = layout.get("adjustable")
            if not isinstance(locked, list) or not locked:
                errors.append(f"role_layouts.{layout_id}.locked: 1件以上の配列にしてください")
            if not isinstance(adjustable, list) or not adjustable:
                errors.append(f"role_layouts.{layout_id}.adjustable: 1件以上の配列にしてください")
            if isinstance(locked, list) and isinstance(adjustable, list) and set(locked) & set(adjustable):
                errors.append(f"role_layouts.{layout_id}: lockedとadjustableを重複させないでください")
            if not isinstance(layout.get("content_limits"), dict):
                errors.append(f"role_layouts.{layout_id}.content_limits: オブジェクトで必須です")
            slot_frames = layout.get("slot_frames")
            expected_frames = {
                slot: grids[grid_id].get("slots", {}).get(slot)
                for slot in slots
                if grid_id in grids and slot in grids[grid_id].get("slots", {})
            }
            if slot_frames != expected_frames:
                errors.append(f"role_layouts.{layout_id}.slot_frames: Gridの実座標と一致させてください")
    loaded["layout_map"] = layouts

    grammar_doc = loaded.get("grammars", {})
    grammars = _unique_ids(grammar_doc.get("grammars") if isinstance(grammar_doc, dict) else None, "grammars", errors)
    for grammar_id, grammar in grammars.items():
        if not isinstance(grammar.get("deck_types"), list) or not set(grammar.get("deck_types", [])).issubset(DECK_TYPES):
            errors.append(f"grammars.{grammar_id}.deck_types: 未対応の値があります")
        sequence = grammar.get("sequence")
        if not isinstance(sequence, list) or not sequence or not set(sequence).issubset(ROLES):
            errors.append(f"grammars.{grammar_id}.sequence: 対応roleの配列にしてください")
        if not grammar.get("rule"):
            errors.append(f"grammars.{grammar_id}.rule: 必須です")
    loaded["grammar_map"] = grammars

    if manifest.get("version") == 2:
        style_doc = loaded.get("style_profiles", {})
        styles = _unique_ids(style_doc.get("style_profiles") if isinstance(style_doc, dict) else None, "style_profiles", errors)
        for style_id, style in styles.items():
            if style.get("theme") not in theme_data:
                errors.append(f"style_profiles.{style_id}.theme: 未登録themeです")
            if not isinstance(style.get("rules"), dict) or not style.get("philosophy"):
                errors.append(f"style_profiles.{style_id}: philosophyとrulesが必須です")
        loaded["style_map"] = styles

        density_doc = loaded.get("density_profiles", {})
        densities = _unique_ids(density_doc.get("density_profiles") if isinstance(density_doc, dict) else None, "density_profiles", errors)
        for density_id, density in densities.items():
            if not isinstance(density.get("min_body_pt"), (int, float)) or density.get("min_body_pt", 0) < 12:
                errors.append(f"density_profiles.{density_id}.min_body_pt: 12以上にしてください")
        loaded["density_map"] = densities

        sequence_doc = loaded.get("deck_sequences", {})
        sequences = _unique_ids(sequence_doc.get("deck_sequences") if isinstance(sequence_doc, dict) else None, "deck_sequences", errors)
        loaded["sequence_map"] = sequences
        context_doc = loaded.get("context_models", {})
        contexts = context_doc.get("context_models") if isinstance(context_doc, dict) else None
        if not isinstance(contexts, list) or not contexts:
            errors.append("context_models.context_models: 1件以上の配列にしてください")
        else:
            for index, context in enumerate(contexts, start=1):
                if not isinstance(context, dict):
                    errors.append(f"context_models[{index}]: オブジェクトにしてください")
                    continue
                if context.get("density_profile") not in densities:
                    errors.append(f"context_models[{index}].density_profile: 未登録です")
                if context.get("style_profile") not in styles:
                    errors.append(f"context_models[{index}].style_profile: 未登録です")
                if context.get("deck_sequence") not in sequences:
                    errors.append(f"context_models[{index}].deck_sequence: 未登録です")
        loaded["context_models"] = contexts or []

        router = loaded.get("renderer_router", {})
        if not isinstance(router, dict) or not isinstance(router.get("routes"), list) or not router.get("routes"):
            errors.append("renderer_router.routes: 1件以上の配列にしてください")
        anti_slop = loaded.get("anti_slop_rules", {})
        if not isinstance(anti_slop, dict) or not isinstance(anti_slop.get("avoid"), list) or not anti_slop.get("avoid"):
            errors.append("anti_slop_rules.avoid: 1件以上の配列にしてください")
        selection = loaded.get("style_selection_index", {})
        selection_profiles = selection.get("profiles") if isinstance(selection, dict) else None
        if not isinstance(selection_profiles, list) or len(selection_profiles) < 3:
            errors.append("style_selection_index.profiles: 3件以上必要です")
        else:
            selection_ids = {item.get("id") for item in selection_profiles if isinstance(item, dict)}
            if not selection_ids.issubset(styles):
                errors.append("style_selection_index.profiles: 未登録style_profileがあります")

    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict):
        errors.append("manifest.defaults: オブジェクトで必須です")
        defaults = {}
    for deck_type in DECK_TYPES:
        grammar_id = defaults.get("grammar_by_deck_type", {}).get(deck_type) if isinstance(defaults.get("grammar_by_deck_type"), dict) else None
        theme_id = defaults.get("theme_by_deck_type", {}).get(deck_type) if isinstance(defaults.get("theme_by_deck_type"), dict) else None
        if grammar_id not in grammars:
            errors.append(f"manifest.defaults.grammar_by_deck_type.{deck_type}: 未登録grammarです")
        if theme_id not in theme_data:
            errors.append(f"manifest.defaults.theme_by_deck_type.{deck_type}: 未登録themeです")

    quality = manifest.get("quality") if isinstance(manifest.get("quality"), dict) else {}
    minimums = {
        "minimum_component_count": len(components),
        "minimum_role_layout_count": len(layouts),
        "minimum_grammar_count": len(grammars),
        "minimum_theme_count": len(theme_data),
    }
    if manifest.get("version") == 2:
        minimums.update({
            "minimum_layout_grid_count": len(loaded.get("grid_map", {})),
            "minimum_style_profile_count": len(loaded.get("style_map", {})),
            "minimum_density_profile_count": len(loaded.get("density_map", {})),
        })
    for key, actual in minimums.items():
        expected = quality.get(key)
        if not isinstance(expected, int) or actual < expected:
            errors.append(f"manifest.quality.{key}: 登録数{actual}以下にならない値を指定してください")
    return errors, loaded


def main() -> int:
    parser = argparse.ArgumentParser(description="SDPM Design Systemを検証します")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors, loaded = validate_manifest(args.manifest.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "Design System検証OK: "
        f"components={len(loaded['component_map'])}, "
        f"role_layouts={len(loaded['layout_map'])}, "
        f"grammars={len(loaded['grammar_map'])}, themes={len(loaded['themes'])}, "
        f"grids={len(loaded.get('grid_map', {}))}, styles={len(loaded.get('style_map', {}))}"
    )
    print(f"Design System fingerprint={design_system_fingerprint(args.manifest.resolve(), loaded['manifest'])}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
