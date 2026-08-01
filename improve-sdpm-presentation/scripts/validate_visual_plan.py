#!/usr/bin/env python3
"""Visual Plan v1〜v8の契約を検証する。"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAMLが必要です。実行環境へpyyamlを追加してください。") from exc


INTENTS = {
    "title", "executive_summary", "comparison", "process", "architecture",
    "timeline", "before_after", "cause_effect", "matrix", "data_insight",
    "decision", "roadmap", "one_pager",
}
RELATIONSHIPS = {
    "none", "parallel", "comparison", "sequence", "cause_effect", "hierarchy",
    "containment", "connection", "distribution", "change_over_time",
}
PATTERN_FAMILIES = {
    "hero", "narrative", "comparison", "flow", "network", "matrix", "chart",
    "timeline", "roadmap", "table", "card_grid", "one_pager",
}
CHANGE_LEVELS = {"compose", "repair", "recompose", "transform"}
RENDERERS = {"sdpm_native", "baoyu_diagram", "visual_explainer", "imagegen"}
INTEGRATION_MODES = {"native", "embed_svg", "rebuild_from_prototype", "embed_raster"}
DENSITIES = {"low", "medium", "high"}
SPATIAL_MODELS = {
    "hero", "stack", "radial", "matrix", "linear_horizontal", "linear_vertical",
    "network", "editorial_split", "timeline", "form", "freeform",
}
PRIMARY_PRIMITIVES = {
    "typography", "layers", "axes", "circular_path", "trace_line", "kpi",
    "network_nodes", "decision_gates", "form_fields", "container_cards", "image",
}
READING_PATHS = {
    "focal", "left_to_right", "top_to_bottom", "radial", "scan_columns",
    "z_pattern", "spatial",
}
CONTAINER_DEPENDENCIES = {"low", "medium", "high"}
VISUAL_TEXTURES = {
    "typographic", "node_link", "axis_plot", "area_composition", "trace",
    "kpi_editorial", "form", "table", "image",
}
NODE_SHAPES = {"none", "circle", "rectangle", "rounded_rectangle", "mixed"}
MOTIF_USAGES = {"none", "supporting", "dominant"}
CONNECTOR_CHARACTERS = {"none", "thin_straight", "thin_curved", "thick_band", "mixed"}
MOTIF_TOKENS = {
    "circular_nodes", "numbered_nodes", "rounded_cards", "thin_straight_connectors",
    "thin_curved_connectors", "thick_directional_band", "large_color_fields",
    "axis_frame", "typographic_focal", "form_rules",
}
PLAN_MODES = {"precompose", "improve"}
SLIDE_PURPOSES = {
    "key_message", "data_proof", "comparison", "root_cause", "synthesis",
    "recommendation", "decision_matrix", "roadmap", "action_plan",
}
HEADLINE_TYPES = {"fact", "insight", "recommendation", "decision"}
EVIDENCE_LINKAGES = {
    "evidence_only", "evidence_with_annotation", "evidence_to_implication",
    "evidence_to_action",
}
DENSITY_ROLES = {"breathe", "build", "proof", "climax", "action"}
COMPOSITION_BIASES = {"asymmetric", "balanced", "centered", "full_bleed"}
SAFE_AREA_POLICIES = {"strict", "standard"}


def configure_utf8_console() -> None:
    """Windows端末でも日本語の診断結果をUTF-8で出力する。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def require(mapping: dict, key: str, location: str, errors: list[str]) -> object | None:
    value = mapping.get(key)
    if value in (None, "", []):
        errors.append(f"{location}.{key}: 必須です")
    return value


def required_distinct_count(slide_count: int) -> int:
    if slide_count >= 10:
        return 5
    if slide_count >= 6:
        return 4
    if slide_count >= 3:
        return 3
    return slide_count


def max_motif_ratio_limit(slide_count: int) -> float:
    if slide_count >= 6:
        return 0.4
    if slide_count >= 3:
        return 0.67
    return 1.0


def overlong_runs(items: list[tuple[int, str]], limit: int) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[tuple[int, str]] = []
    for item in items + [(-1, "__end__")]:
        if not current or item[1] == current[-1][1]:
            current.append(item)
            continue
        if len(current) > limit:
            runs.append([number for number, _ in current])
        current = [item]
    return runs


def validate(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["ルートはオブジェクトである必要があります"]

    version = data.get("version")
    if version == 8:
        from validate_visual_plan_v8 import validate_v8
        return validate_v8(path, data)
    if version == 7:
        from validate_visual_plan_v7 import validate_v7
        return validate_v7(path, data)
    if version == 6:
        from validate_visual_plan_v6 import validate_v6
        return validate_v6(path, data)
    if version not in {1, 2, 3, 4, 5}:
        errors.append("version: 1〜8のいずれかを指定してください")
    for key in ("source", "deck", "slides"):
        require(data, key, "root", errors)

    source = data.get("source", {})
    if not isinstance(source, dict):
        errors.append("source: オブジェクトである必要があります")

    slides = data.get("slides", [])
    if not isinstance(slides, list) or not slides:
        errors.append("slides: 1件以上の配列である必要があります")
        return errors
    slide_count = len(slides)

    deck = data.get("deck", {})
    max_consecutive_pattern = 2
    density_sequence: list[str] | None = None
    grammar_policy: dict = {}
    motif_policy: dict = {}
    consulting_policy: dict = {}
    plan_mode: str | None = None
    if isinstance(deck, dict):
        for key in ("goal", "audience", "preserve_slide_count"):
            require(deck, key, "deck", errors)
        if version == 5:
            for key in ("mode", "decision_to_make", "governing_thought", "consulting_quality_policy"):
                require(deck, key, "deck", errors)
            plan_mode = deck.get("mode")
            if plan_mode not in PLAN_MODES:
                errors.append("deck.mode: precompose/improveから選んでください")
            policy = deck.get("consulting_quality_policy", {})
            if not isinstance(policy, dict):
                errors.append("deck.consulting_quality_policy: オブジェクトにしてください")
            else:
                consulting_policy = policy
                for key in (
                    "min_advanced_headline_ratio", "min_evidence_to_implication_ratio",
                    "min_showpiece_slides", "max_showpiece_slides",
                ):
                    require(policy, key, "deck.consulting_quality_policy", errors)
                for key in ("min_advanced_headline_ratio", "min_evidence_to_implication_ratio"):
                    value = policy.get(key)
                    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                        errors.append(f"deck.consulting_quality_policy.{key}: 0〜1の数値にしてください")
                min_showpiece = policy.get("min_showpiece_slides")
                max_showpiece = policy.get("max_showpiece_slides")
                if not isinstance(min_showpiece, int) or min_showpiece < 0:
                    errors.append("deck.consulting_quality_policy.min_showpiece_slides: 0以上の整数にしてください")
                if not isinstance(max_showpiece, int) or not isinstance(min_showpiece, int) or max_showpiece < min_showpiece:
                    errors.append("deck.consulting_quality_policy.max_showpiece_slides: min以上の整数にしてください")
        if version in {2, 3, 4, 5}:
            rhythm = require(deck, "rhythm", "deck", errors)
            if isinstance(rhythm, dict):
                max_consecutive_pattern = rhythm.get("max_consecutive_same_pattern")
                density_sequence = rhythm.get("density_sequence")
                if not isinstance(max_consecutive_pattern, int) or not 1 <= max_consecutive_pattern <= 3:
                    errors.append("deck.rhythm.max_consecutive_same_pattern: 1〜3の整数にしてください")
                    max_consecutive_pattern = 2
                if not isinstance(density_sequence, list) or not density_sequence:
                    errors.append("deck.rhythm.density_sequence: 1件以上の配列にしてください")
                    density_sequence = None
                elif any(value not in DENSITIES for value in density_sequence):
                    errors.append("deck.rhythm.density_sequence: low/medium/highだけを指定してください")
            elif rhythm is not None:
                errors.append("deck.rhythm: オブジェクトにしてください")
        if version in {3, 4, 5}:
            policy = require(deck, "visual_grammar_policy", "deck", errors)
            if isinstance(policy, dict):
                grammar_policy = policy
                for key in (
                    "max_box_dominant_ratio", "max_takeaway_band_ratio",
                    "max_consecutive_same_spatial_model", "max_consecutive_same_reading_path",
                    "min_distinct_spatial_models", "min_distinct_primary_primitives",
                ):
                    require(policy, key, "deck.visual_grammar_policy", errors)
                for key in ("max_box_dominant_ratio", "max_takeaway_band_ratio"):
                    value = policy.get(key)
                    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 0.6:
                        errors.append(f"deck.visual_grammar_policy.{key}: 0〜0.6の数値にしてください")
                for key in ("max_consecutive_same_spatial_model", "max_consecutive_same_reading_path"):
                    value = policy.get(key)
                    if not isinstance(value, int) or not 1 <= value <= 3:
                        errors.append(f"deck.visual_grammar_policy.{key}: 1〜3の整数にしてください")
                minimum = required_distinct_count(slide_count)
                for key in ("min_distinct_spatial_models", "min_distinct_primary_primitives"):
                    value = policy.get(key)
                    if not isinstance(value, int) or not minimum <= value <= slide_count:
                        errors.append(
                            f"deck.visual_grammar_policy.{key}: {minimum}〜{slide_count}の整数にしてください"
                        )
            elif policy is not None:
                errors.append("deck.visual_grammar_policy: オブジェクトにしてください")
        if version in {4, 5}:
            motif = require(deck, "motif_policy", "deck", errors)
            if isinstance(motif, dict):
                motif_policy = motif
                for key in (
                    "max_shared_motif_ratio", "max_node_line_dominant_ratio",
                    "min_distinct_visual_textures",
                ):
                    require(motif, key, "deck.motif_policy", errors)
                limit = max_motif_ratio_limit(slide_count)
                for key in ("max_shared_motif_ratio", "max_node_line_dominant_ratio"):
                    value = motif.get(key)
                    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= limit:
                        errors.append(f"deck.motif_policy.{key}: 0〜{limit}の数値にしてください")
                minimum = required_distinct_count(slide_count)
                value = motif.get("min_distinct_visual_textures")
                if not isinstance(value, int) or not minimum <= value <= slide_count:
                    errors.append(
                        f"deck.motif_policy.min_distinct_visual_textures: {minimum}〜{slide_count}の整数にしてください"
                    )
            elif motif is not None:
                errors.append("deck.motif_policy: オブジェクトにしてください")
    else:
        errors.append("deck: オブジェクトである必要があります")

    if version in {2, 3, 4, 5} and density_sequence is not None and len(density_sequence) != slide_count:
        errors.append("deck.rhythm.density_sequence: slidesと同じ件数にしてください")

    ids: set[str] = set()
    numbers: set[int] = set()
    ordered_families: list[tuple[int, str, str | None]] = []
    spatial_models: list[tuple[int, str]] = []
    primary_primitives: set[str] = set()
    reading_paths: list[tuple[int, str]] = []
    box_dominant_slides: list[int] = []
    takeaway_slides: list[int] = []
    selected_renderers: list[str] = []
    visual_textures: set[str] = set()
    motif_slides: dict[str, set[int]] = {token: set() for token in MOTIF_TOKENS}
    node_line_dominant_slides: set[int] = set()
    advanced_headline_slides: set[int] = set()
    implication_slides: set[int] = set()
    showpiece_slides: set[int] = set()

    for index, slide in enumerate(slides, start=1):
        location = f"slides[{index}]"
        if not isinstance(slide, dict):
            errors.append(f"{location}: オブジェクトである必要があります")
            continue
        required_keys = [
            "slide_id", "slide_number", "key_message", "intent", "content_hierarchy",
            "visual_strategy", "constraints", "acceptance",
        ]
        if version in {2, 3, 4, 5}:
            required_keys.append("relationship")
        for key in required_keys:
            require(slide, key, location, errors)

        slide_id = slide.get("slide_id")
        if not isinstance(slide_id, str) or not slide_id.strip():
            errors.append(f"{location}.slide_id: 空でない文字列にしてください")
        elif slide_id in ids:
            errors.append(f"{location}.slide_id: 重複しています")
        else:
            ids.add(slide_id)

        number = slide.get("slide_number")
        if not isinstance(number, int) or number < 1:
            errors.append(f"{location}.slide_number: 1以上の整数にしてください")
        elif number in numbers:
            errors.append(f"{location}.slide_number: 重複しています")
        else:
            numbers.add(number)

        if slide.get("intent") not in INTENTS:
            errors.append(f"{location}.intent: 未対応の値です")
        if version in {2, 3, 4, 5} and slide.get("relationship") not in RELATIONSHIPS:
            errors.append(f"{location}.relationship: 未対応の値です")

        hierarchy = slide.get("content_hierarchy", {})
        if isinstance(hierarchy, dict):
            require(hierarchy, "primary", f"{location}.content_hierarchy", errors)
        else:
            errors.append(f"{location}.content_hierarchy: オブジェクトにしてください")

        strategy = slide.get("visual_strategy", {})
        if not isinstance(strategy, dict):
            errors.append(f"{location}.visual_strategy: オブジェクトにしてください")
            continue
        strategy_keys = ["pattern", "renderer", "integration_mode", "emphasis", "density", "rationale"]
        if version in {2, 3, 4, 5}:
            strategy_keys.extend(["pattern_family", "change_level"])
        if version in {3, 4, 5}:
            strategy_keys.extend(["renderer_decision", "visual_grammar"])
        if version in {4, 5}:
            strategy_keys.append("motif_fingerprint")
        if version == 5:
            strategy_keys.extend(["composition_bias", "safe_area"])
        for key in strategy_keys:
            require(strategy, key, f"{location}.visual_strategy", errors)

        renderer = strategy.get("renderer")
        mode = strategy.get("integration_mode")
        density = strategy.get("density")
        if renderer not in RENDERERS:
            errors.append(f"{location}.visual_strategy.renderer: 未対応の値です")
        else:
            selected_renderers.append(renderer)
        if mode not in INTEGRATION_MODES:
            errors.append(f"{location}.visual_strategy.integration_mode: 未対応の値です")
        if density not in DENSITIES:
            errors.append(f"{location}.visual_strategy.density: low/medium/highから選んでください")

        if version in {2, 3, 4, 5}:
            family = strategy.get("pattern_family")
            if family not in PATTERN_FAMILIES:
                errors.append(f"{location}.visual_strategy.pattern_family: 未対応の値です")
            elif isinstance(number, int):
                ordered_families.append((number, family, strategy.get("repetition_justification")))
            if strategy.get("change_level") not in CHANGE_LEVELS:
                errors.append(f"{location}.visual_strategy.change_level: 未対応の値です")
            elif version == 5:
                change_level = strategy.get("change_level")
                if plan_mode == "precompose" and change_level != "compose":
                    errors.append(f"{location}.visual_strategy.change_level: precomposeではcomposeにしてください")
                if plan_mode == "improve" and change_level == "compose":
                    errors.append(f"{location}.visual_strategy.change_level: improveではrepair/recompose/transformにしてください")
            if family == "card_grid" and not strategy.get("card_grid_justification"):
                errors.append(f"{location}.visual_strategy.card_grid_justification: card_gridでは必須です")
            if density_sequence is not None and index <= len(density_sequence) and density != density_sequence[index - 1]:
                errors.append(f"{location}.visual_strategy.density: deck.rhythm.density_sequenceと一致させてください")

        if version in {3, 4, 5}:
            decision = strategy.get("renderer_decision", {})
            if not isinstance(decision, dict):
                errors.append(f"{location}.visual_strategy.renderer_decision: オブジェクトにしてください")
            else:
                considered = decision.get("considered")
                if not isinstance(considered, list) or not considered:
                    errors.append(f"{location}.visual_strategy.renderer_decision.considered: 1件以上の配列にしてください")
                elif any(item not in RENDERERS for item in considered):
                    errors.append(f"{location}.visual_strategy.renderer_decision.considered: 未対応の値があります")
                elif len(set(considered)) != len(considered):
                    errors.append(f"{location}.visual_strategy.renderer_decision.considered: 重複を除いてください")
                if decision.get("selected") != renderer:
                    errors.append(f"{location}.visual_strategy.renderer_decision.selected: rendererと一致させてください")
                if isinstance(considered, list) and renderer not in considered:
                    errors.append(f"{location}.visual_strategy.renderer_decision.considered: selectedを含めてください")
                require(decision, "reason", f"{location}.visual_strategy.renderer_decision", errors)

            grammar = strategy.get("visual_grammar", {})
            if not isinstance(grammar, dict):
                errors.append(f"{location}.visual_strategy.visual_grammar: オブジェクトにしてください")
            else:
                for key in (
                    "spatial_model", "primary_primitive", "reading_path",
                    "container_dependency", "takeaway_band", "distinctive_feature",
                ):
                    require(grammar, key, f"{location}.visual_strategy.visual_grammar", errors)
                spatial = grammar.get("spatial_model")
                primitive = grammar.get("primary_primitive")
                reading = grammar.get("reading_path")
                dependency = grammar.get("container_dependency")
                takeaway = grammar.get("takeaway_band")
                if spatial not in SPATIAL_MODELS:
                    errors.append(f"{location}.visual_strategy.visual_grammar.spatial_model: 未対応の値です")
                elif isinstance(number, int):
                    spatial_models.append((number, spatial))
                if primitive not in PRIMARY_PRIMITIVES:
                    errors.append(f"{location}.visual_strategy.visual_grammar.primary_primitive: 未対応の値です")
                else:
                    primary_primitives.add(primitive)
                if reading not in READING_PATHS:
                    errors.append(f"{location}.visual_strategy.visual_grammar.reading_path: 未対応の値です")
                elif isinstance(number, int):
                    reading_paths.append((number, reading))
                if dependency not in CONTAINER_DEPENDENCIES:
                    errors.append(f"{location}.visual_strategy.visual_grammar.container_dependency: 未対応の値です")
                if not isinstance(takeaway, bool):
                    errors.append(f"{location}.visual_strategy.visual_grammar.takeaway_band: true/falseにしてください")
                elif takeaway and isinstance(number, int):
                    takeaway_slides.append(number)
                if (primitive == "container_cards" or dependency == "high") and isinstance(number, int):
                    box_dominant_slides.append(number)

        if version in {4, 5}:
            motif = strategy.get("motif_fingerprint", {})
            motif_location = f"{location}.visual_strategy.motif_fingerprint"
            if not isinstance(motif, dict):
                errors.append(f"{motif_location}: オブジェクトにしてください")
            else:
                for key in (
                    "visual_texture", "dominant_node_shape", "node_usage", "connector_usage",
                    "connector_character", "signature_tokens", "dominant_motif",
                ):
                    require(motif, key, motif_location, errors)
                texture = motif.get("visual_texture")
                node_shape = motif.get("dominant_node_shape")
                node_usage = motif.get("node_usage")
                connector_usage = motif.get("connector_usage")
                connector_character = motif.get("connector_character")
                tokens = motif.get("signature_tokens")
                if texture not in VISUAL_TEXTURES:
                    errors.append(f"{motif_location}.visual_texture: 未対応の値です")
                else:
                    visual_textures.add(texture)
                if node_shape not in NODE_SHAPES:
                    errors.append(f"{motif_location}.dominant_node_shape: 未対応の値です")
                if node_usage not in MOTIF_USAGES:
                    errors.append(f"{motif_location}.node_usage: 未対応の値です")
                if connector_usage not in MOTIF_USAGES:
                    errors.append(f"{motif_location}.connector_usage: 未対応の値です")
                if connector_character not in CONNECTOR_CHARACTERS:
                    errors.append(f"{motif_location}.connector_character: 未対応の値です")
                if not isinstance(tokens, list) or not tokens:
                    errors.append(f"{motif_location}.signature_tokens: 1件以上の配列にしてください")
                elif any(token not in MOTIF_TOKENS for token in tokens):
                    errors.append(f"{motif_location}.signature_tokens: 未対応の値があります")
                elif len(tokens) != len(set(tokens)):
                    errors.append(f"{motif_location}.signature_tokens: 重複を除いてください")
                elif isinstance(number, int):
                    for token in tokens:
                        motif_slides[token].add(number)
                if node_usage == "dominant" and connector_usage == "dominant" and isinstance(number, int):
                    node_line_dominant_slides.add(number)

        if version == 5:
            if strategy.get("composition_bias") not in COMPOSITION_BIASES:
                errors.append(f"{location}.visual_strategy.composition_bias: 未対応の値です")
            safe_area = strategy.get("safe_area", {})
            safe_location = f"{location}.visual_strategy.safe_area"
            if not isinstance(safe_area, dict):
                errors.append(f"{safe_location}: オブジェクトにしてください")
            else:
                for key in ("title", "footer", "edge_inset_px"):
                    require(safe_area, key, safe_location, errors)
                for key in ("title", "footer"):
                    if safe_area.get(key) not in SAFE_AREA_POLICIES:
                        errors.append(f"{safe_location}.{key}: strict/standardから選んでください")
                inset = safe_area.get("edge_inset_px")
                if not isinstance(inset, int) or not 24 <= inset <= 120:
                    errors.append(f"{safe_location}.edge_inset_px: 24〜120の整数にしてください")

            frame = slide.get("consulting_frame")
            frame_location = f"{location}.consulting_frame"
            if not isinstance(frame, dict):
                errors.append(f"{frame_location}: オブジェクトで必須です")
            else:
                for key in (
                    "slide_purpose", "headline_type", "executive_headline", "primary_evidence",
                    "so_what", "decision_relevance", "evidence_linkage", "attention_order",
                    "remove_if_possible", "showpiece", "density_role",
                ):
                    if key == "remove_if_possible":
                        if key not in frame or not isinstance(frame.get(key), list):
                            errors.append(f"{frame_location}.{key}: 配列で必須です")
                    else:
                        require(frame, key, frame_location, errors)
                if frame.get("slide_purpose") not in SLIDE_PURPOSES:
                    errors.append(f"{frame_location}.slide_purpose: 未対応の値です")
                headline_type = frame.get("headline_type")
                if headline_type not in HEADLINE_TYPES:
                    errors.append(f"{frame_location}.headline_type: 未対応の値です")
                elif headline_type in {"insight", "recommendation", "decision"} and isinstance(number, int):
                    advanced_headline_slides.add(number)
                linkage = frame.get("evidence_linkage")
                if linkage not in EVIDENCE_LINKAGES:
                    errors.append(f"{frame_location}.evidence_linkage: 未対応の値です")
                elif linkage in {"evidence_to_implication", "evidence_to_action"} and isinstance(number, int):
                    implication_slides.add(number)
                attention = frame.get("attention_order")
                if not isinstance(attention, list) or len(attention) < 2 or any(not str(item).strip() for item in attention):
                    errors.append(f"{frame_location}.attention_order: 2件以上の配列にしてください")
                if not isinstance(frame.get("showpiece"), bool):
                    errors.append(f"{frame_location}.showpiece: true/falseにしてください")
                elif frame.get("showpiece") and isinstance(number, int):
                    showpiece_slides.add(number)
                    if linkage not in {"evidence_to_implication", "evidence_to_action"}:
                        errors.append(f"{frame_location}.evidence_linkage: showpieceではimplication/actionへ接続してください")
                if frame.get("density_role") not in DENSITY_ROLES:
                    errors.append(f"{frame_location}.density_role: 未対応の値です")

        constraints = slide.get("constraints", {})
        if isinstance(constraints, dict):
            for key in ("preserve_content", "editable_required", "max_text_blocks"):
                require(constraints, key, f"{location}.constraints", errors)
            if constraints.get("editable_required") is True and mode == "embed_raster":
                errors.append(f"{location}: 編集必須のスライドでembed_rasterは使えません")
            for key in ("preserve_content", "editable_required"):
                if key in constraints and not isinstance(constraints[key], bool):
                    errors.append(f"{location}.constraints.{key}: true/falseにしてください")
            max_blocks = constraints.get("max_text_blocks")
            if not isinstance(max_blocks, int) or not 1 <= max_blocks <= 12:
                errors.append(f"{location}.constraints.max_text_blocks: 1〜12の整数にしてください")
        else:
            errors.append(f"{location}.constraints: オブジェクトにしてください")

        if version in {2, 3, 4, 5}:
            acceptance = slide.get("acceptance", {})
            if isinstance(acceptance, dict):
                for key in ("three_second_message", "visual_anchor", "must_show", "must_avoid"):
                    require(acceptance, key, f"{location}.acceptance", errors)
            else:
                errors.append(f"{location}.acceptance: オブジェクトにしてください")

    if version in {2, 3, 4, 5} and sorted(numbers) != list(range(1, slide_count + 1)):
        errors.append("slides.slide_number: 1から連番にしてください")

    ordered_families.sort(key=lambda item: item[0])
    run: list[tuple[int, str, str | None]] = []
    for item in ordered_families + [(-1, "__end__", None)]:
        if not run or item[1] == run[-1][1]:
            run.append(item)
            continue
        if len(run) > max_consecutive_pattern and not any(entry[2] for entry in run):
            slide_numbers = ", ".join(str(entry[0]) for entry in run)
            errors.append(
                f"slides[{slide_numbers}]: 同じpattern_familyが{len(run)}ページ連続しています。"
                "repetition_justificationを指定してください"
            )
        run = [item]

    if version in {3, 4, 5} and grammar_policy:
        spatial_models.sort()
        reading_paths.sort()
        max_spatial = grammar_policy.get("max_consecutive_same_spatial_model")
        max_reading = grammar_policy.get("max_consecutive_same_reading_path")
        if isinstance(max_spatial, int):
            for numbers_in_run in overlong_runs(spatial_models, max_spatial):
                errors.append(f"slides{numbers_in_run}: 同じspatial_modelが連続上限を超えています")
        if isinstance(max_reading, int):
            for numbers_in_run in overlong_runs(reading_paths, max_reading):
                errors.append(f"slides{numbers_in_run}: 同じreading_pathが連続上限を超えています")

        distinct_spatial = len({value for _, value in spatial_models})
        min_spatial = grammar_policy.get("min_distinct_spatial_models")
        if isinstance(min_spatial, int) and distinct_spatial < min_spatial:
            errors.append(f"visual_grammar: spatial_modelは{min_spatial}種類以上必要です（実績{distinct_spatial}）")
        min_primitive = grammar_policy.get("min_distinct_primary_primitives")
        if isinstance(min_primitive, int) and len(primary_primitives) < min_primitive:
            errors.append(
                f"visual_grammar: primary_primitiveは{min_primitive}種類以上必要です（実績{len(primary_primitives)}）"
            )

        max_box_ratio = grammar_policy.get("max_box_dominant_ratio")
        box_ratio = len(set(box_dominant_slides)) / slide_count
        if isinstance(max_box_ratio, (int, float)) and box_ratio > max_box_ratio + 1e-9:
            errors.append(
                f"visual_grammar: 箱優位率{box_ratio:.2f}が上限{max_box_ratio:.2f}を超えています"
            )
        max_band_ratio = grammar_policy.get("max_takeaway_band_ratio")
        band_ratio = len(set(takeaway_slides)) / slide_count
        if isinstance(max_band_ratio, (int, float)) and band_ratio > max_band_ratio + 1e-9:
            errors.append(
                f"visual_grammar: 結論帯率{band_ratio:.2f}が上限{max_band_ratio:.2f}を超えています"
            )

        if selected_renderers and set(selected_renderers) == {"sdpm_native"}:
            renderer_policy = deck.get("renderer_policy", {}) if isinstance(deck, dict) else {}
            if not isinstance(renderer_policy, dict) or not renderer_policy.get("all_native_rationale"):
                errors.append("deck.renderer_policy.all_native_rationale: 全ページNativeの場合は必須です")

    if version in {4, 5} and motif_policy:
        min_textures = motif_policy.get("min_distinct_visual_textures")
        if isinstance(min_textures, int) and len(visual_textures) < min_textures:
            errors.append(
                f"motif_fingerprint: visual_textureは{min_textures}種類以上必要です（実績{len(visual_textures)}）"
            )
        max_shared = motif_policy.get("max_shared_motif_ratio")
        if isinstance(max_shared, (int, float)):
            for token, slide_numbers in motif_slides.items():
                ratio = len(slide_numbers) / slide_count
                if ratio > max_shared + 1e-9:
                    errors.append(
                        f"motif_fingerprint: {token}の共有率{ratio:.2f}が上限{max_shared:.2f}を超えています"
                    )
        max_node_line = motif_policy.get("max_node_line_dominant_ratio")
        node_line_ratio = len(node_line_dominant_slides) / slide_count
        if isinstance(max_node_line, (int, float)) and node_line_ratio > max_node_line + 1e-9:
            errors.append(
                f"motif_fingerprint: ノード＋線主役率{node_line_ratio:.2f}が上限{max_node_line:.2f}を超えています"
            )

    if version == 5 and consulting_policy:
        min_headline = consulting_policy.get("min_advanced_headline_ratio")
        headline_ratio = len(advanced_headline_slides) / slide_count
        if isinstance(min_headline, (int, float)) and headline_ratio + 1e-9 < min_headline:
            errors.append(
                f"consulting_quality: 高度見出し率{headline_ratio:.2f}が下限{min_headline:.2f}未満です"
            )
        min_linkage = consulting_policy.get("min_evidence_to_implication_ratio")
        linkage_ratio = len(implication_slides) / slide_count
        if isinstance(min_linkage, (int, float)) and linkage_ratio + 1e-9 < min_linkage:
            errors.append(
                f"consulting_quality: 示唆接続率{linkage_ratio:.2f}が下限{min_linkage:.2f}未満です"
            )
        min_showpiece = consulting_policy.get("min_showpiece_slides")
        max_showpiece = consulting_policy.get("max_showpiece_slides")
        if isinstance(min_showpiece, int) and isinstance(max_showpiece, int):
            if not min_showpiece <= len(showpiece_slides) <= max_showpiece:
                errors.append(
                    f"consulting_quality: showpieceは{min_showpiece}〜{max_showpiece}ページにしてください"
                )

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("使用法: python validate_visual_plan.py <visual-plan.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ファイルが見つかりません: {path}")
        return 2
    errors = validate(path)
    if errors:
        print("Visual Planの検証に失敗しました:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Visual Planは有効です。")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
