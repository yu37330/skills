#!/usr/bin/env python3
"""Visual Plan v6の正本分離と視覚品質契約を検証する。"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


PLAN_MODES = {"precompose", "improve"}
INTENTS = {
    "title", "executive_summary", "comparison", "process", "architecture",
    "timeline", "before_after", "cause_effect", "matrix", "data_insight",
    "decision", "roadmap", "one_pager",
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
MOTIF_USAGES = {"none", "supporting", "dominant"}
MOTIF_TOKENS = {
    "circular_nodes", "numbered_nodes", "rounded_cards", "thin_straight_connectors",
    "thin_curved_connectors", "thick_directional_band", "large_color_fields",
    "axis_frame", "typographic_focal", "form_rules",
}
MOTIF_ROLES = {"supporting", "dominant"}
COMPOSITION_BIASES = {"asymmetric", "balanced", "centered", "full_bleed"}
SAFE_AREA_POLICIES = {"strict", "standard"}
FORBIDDEN_CONTENT_KEYS = {
    "key_message", "consulting_frame", "content_hierarchy", "executive_headline",
    "primary_evidence", "so_what", "decision_relevance", "evidence_linkage",
}
POLICY_LIMITS = {
    "strict": {"motif": 0.4, "node_line": 0.4, "pattern_run": 2, "distinct_offset": 0},
    "balanced": {"motif": 0.6, "node_line": 0.6, "pattern_run": 3, "distinct_offset": 1},
    "consistent": {"motif": 0.8, "node_line": 0.8, "pattern_run": 4, "distinct_offset": 2},
}


def require(mapping: dict, key: str, location: str, errors: list[str]) -> object | None:
    value = mapping.get(key)
    if value in (None, "", []):
        errors.append(f"{location}.{key}: 必須です")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def distinct_target(slide_count: int, repetition_policy: str) -> int:
    base = 5 if slide_count >= 10 else 4 if slide_count >= 6 else 3 if slide_count >= 3 else slide_count
    return max(1, base - POLICY_LIMITS[repetition_policy]["distinct_offset"])


def has_overlong_run(values: list[str], limit: int) -> bool:
    previous = None
    run = 0
    for value in values:
        run = run + 1 if value == previous else 1
        previous = value
        if run > limit:
            return True
    return False


def validate_v6(path: Path, data: dict) -> list[str]:
    errors: list[str] = []
    source = data.get("source")
    deck = data.get("deck")
    slides = data.get("slides")
    if not isinstance(source, dict):
        return ["source: オブジェクトで必須です"]
    if not isinstance(deck, dict):
        return ["deck: オブジェクトで必須です"]
    if not isinstance(slides, list) or not slides:
        return ["slides: 1件以上の配列で必須です"]

    deck_plan_path = resolve(path.parent, source.get("deck_plan"))
    if deck_plan_path is None or not deck_plan_path.is_file():
        return ["source.deck_plan: 実在するDeck Plan v3を指定してください"]
    try:
        deck_plan = yaml.safe_load(deck_plan_path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"source.deck_plan: 読み込めません: {exc}"]
    if not isinstance(deck_plan, dict) or deck_plan.get("version") != 3:
        errors.append("source.deck_plan: version 3を指定してください")
        plan_deck, plan_slides = {}, []
    else:
        plan_deck = deck_plan.get("deck", {})
        plan_slides = deck_plan.get("slides", [])
    expected_hash = source.get("deck_plan_sha256")
    actual_hash = sha256(deck_plan_path)
    if expected_hash != actual_hash:
        errors.append(f"source.deck_plan_sha256: {actual_hash}にしてください")

    for key in (
        "mode", "preserve_slide_count", "rhythm", "visual_grammar_policy",
        "motif_policy", "renderer_policy",
    ):
        require(deck, key, "deck", errors)
    mode = deck.get("mode")
    if mode not in PLAN_MODES:
        errors.append("deck.mode: precompose/improveから選んでください")
    if not isinstance(deck.get("preserve_slide_count"), bool):
        errors.append("deck.preserve_slide_count: true/falseにしてください")

    repetition_policy = plan_deck.get("repetition_policy")
    if repetition_policy not in POLICY_LIMITS:
        errors.append("source.deck_plan.deck.repetition_policy: 未対応の値です")
        repetition_policy = "strict"
    key_slides = set(plan_deck.get("key_slides", [])) if isinstance(plan_deck.get("key_slides"), list) else set()
    plan_slide_map = {
        slide.get("slide_id"): slide for slide in plan_slides
        if isinstance(slide, dict) and isinstance(slide.get("slide_id"), str)
    }
    if len(plan_slide_map) != len(plan_slides):
        errors.append("source.deck_plan.slides.slide_id: 一意なIDにしてください")
    if len(slides) != len(plan_slides):
        errors.append("slides: Deck Planと同じ件数にしてください")

    rhythm = deck.get("rhythm", {})
    if not isinstance(rhythm, dict):
        errors.append("deck.rhythm: オブジェクトにしてください")
        rhythm = {}
    for key in ("density_sequence", "max_consecutive_same_pattern"):
        require(rhythm, key, "deck.rhythm", errors)
    density_sequence = rhythm.get("density_sequence")
    if not isinstance(density_sequence, list) or len(density_sequence) != len(slides):
        errors.append("deck.rhythm.density_sequence: slidesと同じ件数にしてください")
        density_sequence = []
    elif any(value not in DENSITIES for value in density_sequence):
        errors.append("deck.rhythm.density_sequence: low/medium/highだけを指定してください")
    expected_pattern_limit = POLICY_LIMITS[repetition_policy]["pattern_run"]
    if rhythm.get("max_consecutive_same_pattern") != expected_pattern_limit:
        errors.append(f"deck.rhythm.max_consecutive_same_pattern: {expected_pattern_limit}にしてください")

    target = distinct_target(len(slides), repetition_policy)
    grammar_policy = deck.get("visual_grammar_policy", {})
    if not isinstance(grammar_policy, dict):
        errors.append("deck.visual_grammar_policy: オブジェクトにしてください")
        grammar_policy = {}
    expected_grammar = {
        "max_box_dominant_ratio": 0.6 if repetition_policy == "strict" else 0.7 if repetition_policy == "balanced" else 0.8,
        "max_takeaway_band_ratio": 0.6 if repetition_policy == "strict" else 0.7 if repetition_policy == "balanced" else 0.8,
        "min_distinct_spatial_models": target,
        "min_distinct_primary_primitives": target,
        "max_consecutive_same_reading_path": expected_pattern_limit,
    }
    for key, expected in expected_grammar.items():
        if grammar_policy.get(key) != expected:
            errors.append(f"deck.visual_grammar_policy.{key}: {expected}にしてください")

    motif_policy = deck.get("motif_policy", {})
    if not isinstance(motif_policy, dict):
        errors.append("deck.motif_policy: オブジェクトにしてください")
        motif_policy = {}
    short_deck_limit = 1.0 if len(slides) <= 2 else 0.67 if len(slides) <= 5 else 0.0
    expected_motif = {
        "max_dominant_motif_ratio": max(POLICY_LIMITS[repetition_policy]["motif"], short_deck_limit),
        "max_node_line_dominant_ratio": max(POLICY_LIMITS[repetition_policy]["node_line"], short_deck_limit),
        "min_distinct_visual_textures": target,
    }
    for key, expected in expected_motif.items():
        if motif_policy.get(key) != expected:
            errors.append(f"deck.motif_policy.{key}: {expected}にしてください")

    ids: list[str] = []
    numbers: list[int] = []
    patterns: list[str] = []
    spatial_models: set[str] = set()
    primitives: set[str] = set()
    reading_paths: list[str] = []
    textures: set[str] = set()
    dominant_tokens: dict[str, set[int]] = {token: set() for token in MOTIF_TOKENS}
    box_slides: set[int] = set()
    band_slides: set[int] = set()
    node_line_slides: set[int] = set()
    selected_renderers: set[str] = set()

    for index, slide in enumerate(slides, start=1):
        location = f"slides[{index}]"
        if not isinstance(slide, dict):
            errors.append(f"{location}: オブジェクトにしてください")
            continue
        forbidden = sorted(FORBIDDEN_CONTENT_KEYS & set(slide))
        if forbidden:
            errors.append(f"{location}: 内容項目はDeck Planだけに置いてください {forbidden}")
        for key in ("slide_id", "slide_number", "intent", "attention_order", "visual_strategy", "constraints", "acceptance"):
            require(slide, key, location, errors)
        slide_id = slide.get("slide_id")
        number = slide.get("slide_number")
        if isinstance(slide_id, str):
            ids.append(slide_id)
        if isinstance(number, int):
            numbers.append(number)
        plan_slide = plan_slide_map.get(slide_id)
        if plan_slide is None:
            errors.append(f"{location}.slide_id: Deck Planに存在しません")
        elif plan_slide.get("slide_number") != number:
            errors.append(f"{location}.slide_number: Deck Planと一致させてください")
        if slide.get("intent") not in INTENTS:
            errors.append(f"{location}.intent: 未対応の値です")
        attention = slide.get("attention_order")
        if not isinstance(attention, list) or len(attention) < 2:
            errors.append(f"{location}.attention_order: 2件以上の配列にしてください")

        strategy = slide.get("visual_strategy")
        if not isinstance(strategy, dict):
            errors.append(f"{location}.visual_strategy: オブジェクトにしてください")
            continue
        for key in (
            "pattern", "pattern_family", "change_level", "renderer", "integration_mode",
            "emphasis", "density", "rationale", "renderer_decision", "visual_grammar",
            "motif_fingerprint", "composition_bias", "safe_area",
        ):
            require(strategy, key, f"{location}.visual_strategy", errors)
        family = strategy.get("pattern_family")
        if family not in PATTERN_FAMILIES:
            errors.append(f"{location}.visual_strategy.pattern_family: 未対応の値です")
        else:
            patterns.append(family)
        change_level = strategy.get("change_level")
        if change_level not in CHANGE_LEVELS:
            errors.append(f"{location}.visual_strategy.change_level: 未対応の値です")
        elif mode == "precompose" and change_level != "compose":
            errors.append(f"{location}.visual_strategy.change_level: precomposeではcomposeにしてください")
        elif mode == "improve" and change_level == "compose":
            errors.append(f"{location}.visual_strategy.change_level: improveではcomposeを使えません")
        renderer = strategy.get("renderer")
        integration = strategy.get("integration_mode")
        if renderer not in RENDERERS:
            errors.append(f"{location}.visual_strategy.renderer: 未対応の値です")
        else:
            selected_renderers.add(renderer)
        if integration not in INTEGRATION_MODES:
            errors.append(f"{location}.visual_strategy.integration_mode: 未対応の値です")
        density = strategy.get("density")
        if density not in DENSITIES:
            errors.append(f"{location}.visual_strategy.density: 未対応の値です")
        elif index <= len(density_sequence) and density != density_sequence[index - 1]:
            errors.append(f"{location}.visual_strategy.density: density_sequenceと一致させてください")
        expected_emphasis = "showpiece" if number in key_slides else "standard"
        if strategy.get("emphasis") != expected_emphasis:
            errors.append(f"{location}.visual_strategy.emphasis: {expected_emphasis}にしてください")

        decision = strategy.get("renderer_decision", {})
        if not isinstance(decision, dict) or decision.get("selected") != renderer or not decision.get("reason"):
            errors.append(f"{location}.visual_strategy.renderer_decision: selectedとreasonを正しく指定してください")
        considered = decision.get("considered") if isinstance(decision, dict) else None
        if not isinstance(considered, list) or renderer not in considered:
            errors.append(f"{location}.visual_strategy.renderer_decision.considered: selectedを含めてください")

        grammar = strategy.get("visual_grammar", {})
        if not isinstance(grammar, dict):
            errors.append(f"{location}.visual_strategy.visual_grammar: オブジェクトにしてください")
        else:
            for key in ("spatial_model", "primary_primitive", "reading_path", "container_dependency", "takeaway_band", "distinctive_feature"):
                require(grammar, key, f"{location}.visual_strategy.visual_grammar", errors)
            spatial = grammar.get("spatial_model")
            primitive = grammar.get("primary_primitive")
            reading = grammar.get("reading_path")
            dependency = grammar.get("container_dependency")
            if spatial not in SPATIAL_MODELS:
                errors.append(f"{location}.visual_strategy.visual_grammar.spatial_model: 未対応の値です")
            else:
                spatial_models.add(spatial)
            if primitive not in PRIMARY_PRIMITIVES:
                errors.append(f"{location}.visual_strategy.visual_grammar.primary_primitive: 未対応の値です")
            else:
                primitives.add(primitive)
            if reading not in READING_PATHS:
                errors.append(f"{location}.visual_strategy.visual_grammar.reading_path: 未対応の値です")
            else:
                reading_paths.append(reading)
            if dependency not in CONTAINER_DEPENDENCIES:
                errors.append(f"{location}.visual_strategy.visual_grammar.container_dependency: 未対応の値です")
            if not isinstance(grammar.get("takeaway_band"), bool):
                errors.append(f"{location}.visual_strategy.visual_grammar.takeaway_band: true/falseにしてください")
            if isinstance(number, int) and (dependency == "high" or primitive == "container_cards"):
                box_slides.add(number)
            if isinstance(number, int) and grammar.get("takeaway_band") is True:
                band_slides.add(number)

        motif = strategy.get("motif_fingerprint", {})
        if not isinstance(motif, dict):
            errors.append(f"{location}.visual_strategy.motif_fingerprint: オブジェクトにしてください")
        else:
            for key in ("visual_texture", "node_usage", "connector_usage", "signature_tokens", "dominant_motif"):
                require(motif, key, f"{location}.visual_strategy.motif_fingerprint", errors)
            texture = motif.get("visual_texture")
            if texture not in VISUAL_TEXTURES:
                errors.append(f"{location}.visual_strategy.motif_fingerprint.visual_texture: 未対応の値です")
            else:
                textures.add(texture)
            node_usage = motif.get("node_usage")
            connector_usage = motif.get("connector_usage")
            if node_usage not in MOTIF_USAGES or connector_usage not in MOTIF_USAGES:
                errors.append(f"{location}.visual_strategy.motif_fingerprint: node_usage/connector_usageが未対応です")
            if isinstance(number, int) and node_usage == connector_usage == "dominant":
                node_line_slides.add(number)
            tokens = motif.get("signature_tokens")
            if not isinstance(tokens, list) or not tokens:
                errors.append(f"{location}.visual_strategy.motif_fingerprint.signature_tokens: 1件以上必要です")
            else:
                seen: set[str] = set()
                for token_index, entry in enumerate(tokens, start=1):
                    token_location = f"{location}.visual_strategy.motif_fingerprint.signature_tokens[{token_index}]"
                    if not isinstance(entry, dict):
                        errors.append(f"{token_location}: tokenとroleを持つオブジェクトにしてください")
                        continue
                    token, role = entry.get("token"), entry.get("role")
                    if token not in MOTIF_TOKENS:
                        errors.append(f"{token_location}.token: 未対応の値です")
                    elif token in seen:
                        errors.append(f"{token_location}.token: 重複しています")
                    else:
                        seen.add(token)
                    if role not in MOTIF_ROLES:
                        errors.append(f"{token_location}.role: supporting/dominantから選んでください")
                    elif role == "dominant" and isinstance(number, int) and token in dominant_tokens:
                        dominant_tokens[token].add(number)

        if strategy.get("composition_bias") not in COMPOSITION_BIASES:
            errors.append(f"{location}.visual_strategy.composition_bias: 未対応の値です")
        safe = strategy.get("safe_area", {})
        if not isinstance(safe, dict):
            errors.append(f"{location}.visual_strategy.safe_area: オブジェクトにしてください")
        else:
            for key in ("title", "footer", "edge_inset_px"):
                require(safe, key, f"{location}.visual_strategy.safe_area", errors)
            if safe.get("title") not in SAFE_AREA_POLICIES or safe.get("footer") not in SAFE_AREA_POLICIES:
                errors.append(f"{location}.visual_strategy.safe_area: title/footerはstrict/standardにしてください")
            if not isinstance(safe.get("edge_inset_px"), int) or not 24 <= safe.get("edge_inset_px", 0) <= 120:
                errors.append(f"{location}.visual_strategy.safe_area.edge_inset_px: 24〜120にしてください")

        constraints = slide.get("constraints", {})
        if not isinstance(constraints, dict):
            errors.append(f"{location}.constraints: オブジェクトにしてください")
        else:
            for key in ("preserve_content", "editable_required", "max_text_blocks"):
                require(constraints, key, f"{location}.constraints", errors)
            if constraints.get("editable_required") is True and integration == "embed_raster":
                errors.append(f"{location}: 編集必須ではembed_rasterを使えません")
        acceptance = slide.get("acceptance", {})
        if not isinstance(acceptance, dict):
            errors.append(f"{location}.acceptance: オブジェクトにしてください")
        else:
            for key in ("visual_anchor", "must_show", "must_avoid"):
                require(acceptance, key, f"{location}.acceptance", errors)
            if "three_second_message" in acceptance:
                errors.append(f"{location}.acceptance.three_second_message: Deck Planのexecutive_headlineを参照し、複製しないでください")

    expected_ids = [slide.get("slide_id") for slide in plan_slides if isinstance(slide, dict)]
    if ids != expected_ids:
        errors.append("slides.slide_id: Deck Planと同じ順序で全IDを含めてください")
    if numbers != list(range(1, len(slides) + 1)):
        errors.append("slides.slide_number: 1から連番にしてください")
    if has_overlong_run(patterns, expected_pattern_limit):
        errors.append("visual_quality: pattern_familyの連続上限を超えています")
    if has_overlong_run(reading_paths, expected_pattern_limit):
        errors.append("visual_quality: reading_pathの連続上限を超えています")
    if len(spatial_models) < target or len(primitives) < target or len(textures) < target:
        errors.append(f"visual_quality: 空間構成・主役図形・視覚テクスチャは各{target}種類以上必要です")
    slide_count = max(1, len(slides))
    if len(box_slides) / slide_count > expected_grammar["max_box_dominant_ratio"] + 1e-9:
        errors.append("visual_quality: 箱優位率が上限を超えています")
    if len(band_slides) / slide_count > expected_grammar["max_takeaway_band_ratio"] + 1e-9:
        errors.append("visual_quality: 結論帯率が上限を超えています")
    if len(node_line_slides) / slide_count > expected_motif["max_node_line_dominant_ratio"] + 1e-9:
        errors.append("visual_quality: ノード＋線主役率が上限を超えています")
    for token, token_slides in dominant_tokens.items():
        if len(token_slides) / slide_count > expected_motif["max_dominant_motif_ratio"] + 1e-9:
            errors.append(f"visual_quality: dominantモチーフ{token}の共有率が上限を超えています")
    if selected_renderers == {"sdpm_native"}:
        renderer_policy = deck.get("renderer_policy", {})
        if not isinstance(renderer_policy, dict) or not renderer_policy.get("all_native_rationale"):
            errors.append("deck.renderer_policy.all_native_rationale: 全ページNativeでは必須です")
    return errors
