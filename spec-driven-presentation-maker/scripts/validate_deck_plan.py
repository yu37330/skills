#!/usr/bin/env python3
"""SDPM Deck Plan v1〜v3を検証する。"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAMLが必要です。") from exc


PURPOSES = {
    "key_message", "data_proof", "comparison", "root_cause", "synthesis",
    "recommendation", "decision_matrix", "roadmap", "action_plan",
}
HEADLINES = {"fact", "insight", "recommendation", "decision"}
CLAIMS = {"fact", "interpretation", "proposal"}
LINKAGES = {
    "evidence_only", "evidence_with_annotation", "evidence_to_implication",
    "evidence_to_action",
}
DENSITIES = {"low", "medium", "high"}
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
COMPOSITION_BIASES = {"asymmetric", "balanced", "centered", "full_bleed"}
SAFE_AREA_POLICIES = {"strict", "standard"}
DECK_TYPES = {"executive_decision", "proposal", "analysis_report", "operating_review", "training"}
REPETITION_POLICIES = {"strict", "balanced", "consistent"}


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


def repeated_run(values: list[str], limit: int) -> bool:
    run = 0
    previous = None
    for value in values:
        run = run + 1 if value == previous else 1
        previous = value
        if run > limit:
            return True
    return False


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


def resolve_relative(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def load_evidence_claims(plan_path: Path, source: object, errors: list[str]) -> set[str]:
    """Evidence Indexを読み、claims.idの集合を返す。"""
    if not isinstance(source, dict):
        errors.append("source: オブジェクトにしてください")
        return set()
    evidence_path = resolve_relative(plan_path.parent, source.get("evidence_index"))
    if evidence_path is None or not evidence_path.is_file():
        errors.append("source.evidence_index: 実在するEvidence Indexを指定してください")
        return set()
    try:
        evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"source.evidence_index: 読み込めません: {exc}")
        return set()
    claims = evidence.get("claims") if isinstance(evidence, dict) else None
    if not isinstance(claims, list):
        errors.append("source.evidence_index.claims: 配列で必須です")
        return set()
    ids: list[str] = []
    for index, claim in enumerate(claims, start=1):
        claim_id = claim.get("id") if isinstance(claim, dict) else None
        if not isinstance(claim_id, str) or not claim_id.strip():
            errors.append(f"source.evidence_index.claims[{index}].id: 必須です")
        else:
            ids.append(claim_id)
    duplicates = sorted({claim_id for claim_id in ids if ids.count(claim_id) > 1})
    if duplicates:
        errors.append(f"source.evidence_index.claims.id: 重複しています {duplicates}")
    return set(ids)


def validate(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        return ["ルートはオブジェクトにしてください"]
    errors: list[str] = []
    version = data.get("version")
    if version not in {1, 2, 3}:
        errors.append("version: 1、2、3のいずれかにしてください")
    for key in ("source", "deck", "slides"):
        require(data, key, "root", errors)

    deck = data.get("deck", {})
    slides = data.get("slides", [])
    if not isinstance(deck, dict):
        errors.append("deck: オブジェクトにしてください")
        deck = {}
    if not isinstance(slides, list) or not slides:
        return errors + ["slides: 1件以上の配列にしてください"]

    common_deck_keys = ["audience", "decision_to_make", "governing_thought", "slide_count", "approval_mode"]
    common_deck_keys.append("rhythm" if version in {1, 2} else "key_slides")
    for key in common_deck_keys:
        require(deck, key, "deck", errors)
    if version == 3:
        for key in ("deck_type", "repetition_policy", "max_consecutive_same_role"):
            require(deck, key, "deck", errors)
        if deck.get("deck_type") not in DECK_TYPES:
            errors.append("deck.deck_type: 未対応の値です")
        if deck.get("repetition_policy") not in REPETITION_POLICIES:
            errors.append("deck.repetition_policy: strict/balanced/consistentから選んでください")
        elif deck.get("deck_type") in {"executive_decision", "proposal"} and deck.get("repetition_policy") != "strict":
            errors.append("deck.repetition_policy: executive_decision/proposalではstrictにしてください")
        expected_role_limit = {"strict": 2, "balanced": 3, "consistent": 4}.get(deck.get("repetition_policy"))
        if expected_role_limit and deck.get("max_consecutive_same_role") != expected_role_limit:
            errors.append(f"deck.max_consecutive_same_role: {expected_role_limit}にしてください")
    visual_policy: dict = {}
    if version == 2:
        policy = require(deck, "visual_quality_policy", "deck", errors)
        if not isinstance(policy, dict):
            errors.append("deck.visual_quality_policy: オブジェクトにしてください")
        else:
            visual_policy = policy
            for key in (
                "max_box_dominant_ratio", "max_takeaway_band_ratio",
                "max_shared_motif_ratio", "max_node_line_dominant_ratio",
                "max_consecutive_same_reading_path", "min_distinct_spatial_models",
                "min_distinct_primary_primitives", "min_distinct_visual_textures",
            ):
                require(policy, key, "deck.visual_quality_policy", errors)
            for key in ("max_box_dominant_ratio", "max_takeaway_band_ratio"):
                value = policy.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 0.6:
                    errors.append(f"deck.visual_quality_policy.{key}: 0〜0.6の数値にしてください")
            motif_limit = max_motif_ratio_limit(len(slides))
            for key in ("max_shared_motif_ratio", "max_node_line_dominant_ratio"):
                value = policy.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= motif_limit:
                    errors.append(f"deck.visual_quality_policy.{key}: 0〜{motif_limit}の数値にしてください")
            reading_limit = policy.get("max_consecutive_same_reading_path")
            if not isinstance(reading_limit, int) or not 1 <= reading_limit <= 3:
                errors.append("deck.visual_quality_policy.max_consecutive_same_reading_path: 1〜3の整数にしてください")
            minimum = required_distinct_count(len(slides))
            for key in (
                "min_distinct_spatial_models", "min_distinct_primary_primitives",
                "min_distinct_visual_textures",
            ):
                value = policy.get(key)
                if not isinstance(value, int) or not minimum <= value <= len(slides):
                    errors.append(f"deck.visual_quality_policy.{key}: {minimum}〜{len(slides)}の整数にしてください")
    if deck.get("approval_mode") not in {"single", "guided"}:
        errors.append("deck.approval_mode: single/guidedから選んでください")
    if deck.get("slide_count") != len(slides):
        errors.append(f"deck.slide_count: {len(slides)}にしてください")

    rhythm = deck.get("rhythm", {}) if version in {1, 2} else {}
    density_sequence: list[str] = []
    if version in {1, 2}:
        if not isinstance(rhythm, dict):
            errors.append("deck.rhythm: オブジェクトにしてください")
            rhythm = {}
        for key in ("density_sequence", "showpiece_slides", "max_consecutive_same_role", "max_consecutive_same_pattern"):
            require(rhythm, key, "deck.rhythm", errors)
        density_sequence = rhythm.get("density_sequence", [])
        if not isinstance(density_sequence, list) or len(density_sequence) != len(slides):
            errors.append("deck.rhythm.density_sequence: slidesと同じ件数にしてください")
        elif any(value not in DENSITIES for value in density_sequence):
            errors.append("deck.rhythm.density_sequence: low/medium/highだけを使ってください")

    source = data.get("source", {})
    evidence_claims = load_evidence_claims(path, source, errors) if version == 3 else set()
    used_evidence: set[str] = set()

    numbers: list[int] = []
    roles: list[str] = []
    patterns: list[str] = []
    advanced_headlines = 0
    advanced_linkages = 0
    showpieces: list[int] = []
    spatial_models: set[str] = set()
    primary_primitives: set[str] = set()
    reading_paths: list[str] = []
    visual_textures: set[str] = set()
    box_dominant = 0
    takeaway_bands = 0
    node_line_dominant = 0
    motif_counts: dict[str, int] = {token: 0 for token in MOTIF_TOKENS}
    decision_visible_early = False
    for index, slide in enumerate(slides, start=1):
        location = f"slides[{index}]"
        if not isinstance(slide, dict):
            errors.append(f"{location}: オブジェクトにしてください")
            continue
        content_keys = [
            "slide_number", "slide_id", "slide_purpose", "headline_type",
            "executive_headline", "claim_type", "evidence_ids", "primary_evidence",
            "so_what", "decision_relevance", "evidence_linkage", "relationship",
            "must_show", "must_avoid", "notes_outline",
        ]
        if version in {1, 2}:
            content_keys.extend([
                "pattern_family", "spatial_model", "primary_primitive", "reading_path",
                "density", "showpiece", "visual_anchor", "attention_order",
            ])
        for key in content_keys:
            if key in {"evidence_ids", "must_avoid"}:
                if key not in slide or not isinstance(slide.get(key), list):
                    errors.append(f"{location}.{key}: 配列で必須です")
            else:
                require(slide, key, location, errors)
        if version == 2:
            for key in (
                "container_dependency", "takeaway_band", "visual_texture", "node_usage",
                "connector_usage", "signature_tokens", "composition_bias", "safe_area",
            ):
                require(slide, key, location, errors)
        evidence_ids = slide.get("evidence_ids")
        if isinstance(evidence_ids, list):
            if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in evidence_ids):
                errors.append(f"{location}.evidence_ids: 空でない文字列だけを指定してください")
            else:
                used_evidence.update(evidence_ids)
                if version == 3:
                    unknown = sorted(set(evidence_ids) - evidence_claims)
                    if unknown:
                        errors.append(f"{location}.evidence_ids: Evidence Indexに存在しません {unknown}")
        number = slide.get("slide_number")
        if isinstance(number, int):
            numbers.append(number)
        purpose = slide.get("slide_purpose")
        if purpose not in PURPOSES:
            errors.append(f"{location}.slide_purpose: 未対応の値です")
        else:
            roles.append(purpose)
        headline = slide.get("headline_type")
        if headline not in HEADLINES:
            errors.append(f"{location}.headline_type: 未対応の値です")
        elif headline in {"insight", "recommendation", "decision"}:
            advanced_headlines += 1
        claim_type = slide.get("claim_type")
        if claim_type not in CLAIMS:
            errors.append(f"{location}.claim_type: 未対応の値です")
        elif version == 3:
            if claim_type in {"fact", "interpretation"} and not evidence_ids:
                errors.append(f"{location}.evidence_ids: {claim_type}では1件以上必要です")
            expected_claim = {
                "data_proof": "fact",
                "root_cause": "interpretation",
                "synthesis": "interpretation",
                "recommendation": "proposal",
                "decision_matrix": "proposal",
                "roadmap": "proposal",
                "action_plan": "proposal",
            }.get(purpose)
            if expected_claim and claim_type != expected_claim:
                errors.append(f"{location}.claim_type: slide_purpose={purpose}では{expected_claim}にしてください")
        linkage = slide.get("evidence_linkage")
        if linkage not in LINKAGES:
            errors.append(f"{location}.evidence_linkage: 未対応の値です")
        elif linkage in {"evidence_to_implication", "evidence_to_action"}:
            advanced_linkages += 1
        if version in {1, 2}:
            if slide.get("density") not in DENSITIES:
                errors.append(f"{location}.density: low/medium/highから選んでください")
            elif index <= len(density_sequence) and slide.get("density") != density_sequence[index - 1]:
                errors.append(f"{location}.density: density_sequenceと一致させてください")
            if not isinstance(slide.get("showpiece"), bool):
                errors.append(f"{location}.showpiece: true/falseにしてください")
            elif slide.get("showpiece") and isinstance(number, int):
                showpieces.append(number)
            patterns.append(str(slide.get("pattern_family", "")))
        if index <= 2 and (
            slide.get("headline_type") == "decision"
            or slide.get("slide_purpose") in {"key_message", "recommendation", "action_plan"}
        ):
            decision_visible_early = True
        if version == 2:
            spatial_models.add(str(slide.get("spatial_model", "")))
            primary_primitives.add(str(slide.get("primary_primitive", "")))
            reading_paths.append(str(slide.get("reading_path", "")))
            dependency = slide.get("container_dependency")
            if dependency not in CONTAINER_DEPENDENCIES:
                errors.append(f"{location}.container_dependency: 未対応の値です")
            if dependency == "high" or slide.get("primary_primitive") == "container_cards":
                box_dominant += 1
            if not isinstance(slide.get("takeaway_band"), bool):
                errors.append(f"{location}.takeaway_band: true/falseにしてください")
            elif slide.get("takeaway_band"):
                takeaway_bands += 1
            texture = slide.get("visual_texture")
            if texture not in VISUAL_TEXTURES:
                errors.append(f"{location}.visual_texture: 未対応の値です")
            else:
                visual_textures.add(texture)
            node_usage = slide.get("node_usage")
            connector_usage = slide.get("connector_usage")
            if node_usage not in MOTIF_USAGES:
                errors.append(f"{location}.node_usage: 未対応の値です")
            if connector_usage not in MOTIF_USAGES:
                errors.append(f"{location}.connector_usage: 未対応の値です")
            if node_usage == "dominant" and connector_usage == "dominant":
                node_line_dominant += 1
            tokens = slide.get("signature_tokens")
            if not isinstance(tokens, list) or not tokens:
                errors.append(f"{location}.signature_tokens: 1件以上の配列にしてください")
            elif any(token not in MOTIF_TOKENS for token in tokens) or len(tokens) != len(set(tokens)):
                errors.append(f"{location}.signature_tokens: 対応値を重複なく指定してください")
            else:
                for token in tokens:
                    motif_counts[token] += 1
            if slide.get("composition_bias") not in COMPOSITION_BIASES:
                errors.append(f"{location}.composition_bias: 未対応の値です")
            safe_area = slide.get("safe_area")
            if not isinstance(safe_area, dict):
                errors.append(f"{location}.safe_area: オブジェクトにしてください")
            else:
                for key in ("title", "footer", "edge_inset_px"):
                    require(safe_area, key, f"{location}.safe_area", errors)
                for key in ("title", "footer"):
                    if safe_area.get(key) not in SAFE_AREA_POLICIES:
                        errors.append(f"{location}.safe_area.{key}: strict/standardから選んでください")
                inset = safe_area.get("edge_inset_px")
                if not isinstance(inset, int) or not 24 <= inset <= 120:
                    errors.append(f"{location}.safe_area.edge_inset_px: 24〜120の整数にしてください")

    if sorted(numbers) != list(range(1, len(slides) + 1)):
        errors.append("slides.slide_number: 1から連番にしてください")
    if len(slides) >= 6:
        if advanced_headlines / len(slides) < 0.4:
            errors.append("headline_type: insight/recommendation/decisionを40%以上にしてください")
        if advanced_linkages / len(slides) < 0.4:
            errors.append("evidence_linkage: implication/actionへの接続を40%以上にしてください")
    if version in {1, 2}:
        expected_showpieces = rhythm.get("showpiece_slides", [])
        if isinstance(expected_showpieces, list) and sorted(showpieces) != sorted(expected_showpieces):
            errors.append("deck.rhythm.showpiece_slides: 各slide.showpieceと一致させてください")
        if len(slides) >= 10 and not 2 <= len(showpieces) <= 3:
            errors.append("showpiece: 10ページでは2～3ページにしてください")
    else:
        key_slides = deck.get("key_slides")
        if not isinstance(key_slides, list) or any(not isinstance(number, int) or number not in numbers for number in key_slides):
            errors.append("deck.key_slides: 有効なスライド番号の配列にしてください")
        elif len(slides) >= 10 and not 2 <= len(set(key_slides)) <= 3:
            errors.append("deck.key_slides: 10ページでは2〜3ページにしてください")
    role_limit = rhythm.get("max_consecutive_same_role", 2) if version in {1, 2} else deck.get("max_consecutive_same_role", 2)
    pattern_limit = rhythm.get("max_consecutive_same_pattern", 2)
    if isinstance(role_limit, int) and repeated_run(roles, role_limit):
        errors.append("slide_purpose: 連続上限を超えています")
    if version in {1, 2} and isinstance(pattern_limit, int) and repeated_run(patterns, pattern_limit):
        errors.append("pattern_family: 連続上限を超えています")
    if version in {2, 3} and not decision_visible_early:
        errors.append("decision_to_make: 1〜2ページ目で判断事項との関係を明示してください")
    if version == 2 and visual_policy:
        slide_count = len(slides)
        checks = (
            ("max_box_dominant_ratio", box_dominant / slide_count, "箱優位率"),
            ("max_takeaway_band_ratio", takeaway_bands / slide_count, "結論帯率"),
            ("max_node_line_dominant_ratio", node_line_dominant / slide_count, "ノード＋線主役率"),
        )
        for key, actual, label in checks:
            limit = visual_policy.get(key)
            if isinstance(limit, (int, float)) and actual > limit + 1e-9:
                errors.append(f"visual_quality: {label}{actual:.2f}が上限{limit:.2f}を超えています")
        shared_limit = visual_policy.get("max_shared_motif_ratio")
        if isinstance(shared_limit, (int, float)):
            for token, count in motif_counts.items():
                ratio = count / slide_count
                if ratio > shared_limit + 1e-9:
                    errors.append(f"visual_quality: {token}の共有率{ratio:.2f}が上限{shared_limit:.2f}を超えています")
        for key, actual in (
            ("min_distinct_spatial_models", len(spatial_models)),
            ("min_distinct_primary_primitives", len(primary_primitives)),
            ("min_distinct_visual_textures", len(visual_textures)),
        ):
            minimum = visual_policy.get(key)
            if isinstance(minimum, int) and actual < minimum:
                errors.append(f"visual_quality: {key}は{minimum}以上必要です（実績{actual}）")
        reading_limit = visual_policy.get("max_consecutive_same_reading_path")
        if isinstance(reading_limit, int) and repeated_run(reading_paths, reading_limit):
            errors.append("visual_quality: reading_pathの連続上限を超えています")
    if version == 3 and evidence_claims:
        unused = sorted(evidence_claims - used_evidence)
        if unused:
            print(f"警告: Deck Planで未使用のEvidence IDがあります: {unused}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("使用法: python validate_deck_plan.py <deck-plan.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ファイルが見つかりません: {path}")
        return 2
    errors = validate(path)
    if errors:
        print("Deck Planの検証に失敗しました:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Deck Planは有効です。")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
