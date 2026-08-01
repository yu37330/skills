#!/usr/bin/env python3
"""資料ビジュアルレビューYAML v1〜v8の契約と採点を検証する。"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAMLが必要です。実行環境へpyyamlを追加してください。") from exc


WEIGHTS_V1 = {
    "message_clarity": 20, "visual_hierarchy": 20, "information_structure": 15,
    "layout_craft": 15, "readability": 10, "consistency": 10, "editability": 10,
}
WEIGHTS_V2 = {
    "message_clarity": 15, "visual_hierarchy": 15, "information_structure": 12,
    "semantic_visual_fit": 12, "layout_craft": 12, "readability": 10,
    "consistency": 8, "visual_variety": 8, "editability": 8,
}
WEIGHTS_V3 = {
    "message_clarity": 14, "visual_hierarchy": 14, "information_structure": 11,
    "semantic_visual_fit": 11, "layout_craft": 11, "readability": 9,
    "consistency": 8, "archetype_variety": 6, "visual_grammar_variety": 10,
    "editability": 6,
}
WEIGHTS_V5 = {
    "message_clarity": 8,
    "decision_clarity": 9,
    "executive_headline": 8,
    "evidence_to_insight": 10,
    "visual_hierarchy": 9,
    "information_structure": 8,
    "semantic_visual_fit": 8,
    "layout_craft": 8,
    "readability": 7,
    "consistency": 4,
    "archetype_variety": 4,
    "visual_grammar_variety": 5,
    "deck_rhythm": 5,
    "page_economy": 4,
    "editability": 3,
}
WEIGHTS_V7 = {
    "message_clarity": 8,
    "decision_clarity": 9,
    "executive_headline": 8,
    "evidence_to_insight": 10,
    "visual_hierarchy": 9,
    "information_structure": 8,
    "semantic_visual_fit": 8,
    "layout_craft": 7,
    "readability": 7,
    "consistency": 3,
    "archetype_variety": 3,
    "visual_grammar_variety": 4,
    "deck_rhythm": 4,
    "page_economy": 3,
    "editability": 2,
    "component_craft": 7,
}
SEVERITIES = {"critical", "major", "minor"}
PATCH_KINDS = {"recompose", "move", "resize", "rewrite", "replace_visual", "change_style"}
DESTINATIONS = {"visual_plan", "slide_json", "design_tokens", "source_content"}
THREE_SECOND_VERDICTS = {"pass", "partial", "fail"}
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
DELIVERY_GATES = {"render_integrity", "mandatory_elements", "content_integrity", "editability"}
DESIGN_SYSTEM_GATE = "design_system_integrity"
V8_GATES = {"anti_slop_integrity", "design_direction_integrity"}
DECK_TYPES = {"executive_decision", "proposal", "analysis_report", "operating_review", "training"}
REPETITION_POLICIES = {"strict", "balanced", "consistent"}


def configure_utf8_console() -> None:
    """Windows端末でも日本語の診断結果をUTF-8で出力する。"""
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


def resolve_path(base: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path if path.is_absolute() else base / path


def infer_render_fidelity(renderer: object) -> str:
    normalized = str(renderer or "").lower().replace(" ", "")
    if "powerpoint" in normalized:
        return "host_application"
    if "libreoffice" in normalized:
        return "office_compatible"
    if any(token in normalized for token in ("sourceparity", "source-parity", "cpu")):
        return "source_parity"
    return "unknown"


def expected_render_delivery_status(path: Path, evidence: object) -> str:
    if not isinstance(evidence, dict):
        return "fail"
    manifest_path = resolve_path(path.parent, evidence.get("manifest"))
    if manifest_path is None or not manifest_path.is_file():
        return "fail"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return "fail"
    fidelity = manifest.get("render_fidelity") or infer_render_fidelity(manifest.get("renderer"))
    return "pass" if fidelity == "host_application" and manifest.get("host_application_verified") is True else "pass_with_rendering_caveat"


def validate_render_evidence(
    path: Path, evidence: object, slide_count: int, errors: list[str], version: int = 5
) -> bool:
    location = "render_evidence"
    if not isinstance(evidence, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    for key in ("manifest", "renderer", "full_size_reviewed_slides", "edge_reviewed_slides"):
        if evidence.get(key) in (None, "", []):
            errors.append(f"{location}.{key}: 必須です")
    expected = list(range(1, slide_count + 1))
    for key in ("full_size_reviewed_slides", "edge_reviewed_slides"):
        values = evidence.get(key)
        if not isinstance(values, list) or sorted(values) != expected:
            errors.append(f"{location}.{key}: 全スライド番号を含めてください")
    manifest_path = resolve_path(path.parent, evidence.get("manifest"))
    if manifest_path is None or not manifest_path.is_file():
        errors.append(f"{location}.manifest: ファイルが見つかりません")
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{location}.manifest: 読み込めません: {exc}")
        return False
    if manifest.get("slide_count") != slide_count:
        errors.append(f"{location}.manifest.slide_count: {slide_count}にしてください")
    if manifest.get("renderer") != evidence.get("renderer"):
        errors.append(f"{location}.renderer: manifestと一致させてください")
    if version >= 8:
        fidelity = manifest.get("render_fidelity") or infer_render_fidelity(manifest.get("renderer"))
        host_verified = manifest.get("host_application_verified") is True
        if fidelity not in {"host_application", "office_compatible", "source_parity", "unknown"}:
            errors.append(f"{location}.manifest.render_fidelity: 未対応です")
        if evidence.get("render_fidelity") != fidelity:
            errors.append(f"{location}.render_fidelity: manifestと一致させてください")
        if evidence.get("host_application_verified") is not host_verified:
            errors.append(f"{location}.host_application_verified: manifestと一致させてください")
        if not host_verified and not evidence.get("rendering_caveat"):
            errors.append(f"{location}.rendering_caveat: 実機未確認時は必須です")
    entries = manifest.get("slides")
    if not isinstance(entries, list) or len(entries) != slide_count:
        errors.append(f"{location}.manifest.slides: {slide_count}件必要です")
        return False
    numbers = []
    for index, entry in enumerate(entries, start=1):
        item_location = f"{location}.manifest.slides[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_location}: オブジェクトにしてください")
            continue
        number = entry.get("slide_number")
        if isinstance(number, int):
            numbers.append(number)
        crop_keys = ["top_crop", "bottom_crop"]
        if version >= 6:
            crop_keys.extend(["left_crop", "right_crop"])
        for key in (
            "file", "sha256", "width", "height", "top_crop", "top_crop_sha256",
            "bottom_crop", "bottom_crop_sha256",
        ):
            if entry.get(key) in (None, "", []):
                errors.append(f"{item_location}.{key}: 必須です")
        image_path = resolve_path(manifest_path.parent, entry.get("file"))
        if image_path is None or not image_path.is_file():
            errors.append(f"{item_location}.file: PNGが見つかりません")
        elif file_sha256(image_path) != entry.get("sha256"):
            errors.append(f"{item_location}.sha256: PNGと一致しません")
        if version >= 6:
            for key in ("left_crop", "left_crop_sha256", "right_crop", "right_crop_sha256"):
                if entry.get(key) in (None, "", []):
                    errors.append(f"{item_location}.{key}: 必須です")
        for key in crop_keys:
            crop = resolve_path(manifest_path.parent, entry.get(key))
            if crop is None or not crop.is_file():
                errors.append(f"{item_location}.{key}: QAクロップが見つかりません")
            elif file_sha256(crop) != entry.get(f"{key}_sha256"):
                errors.append(f"{item_location}.{key}_sha256: QAクロップと一致しません")
    if sorted(numbers) != expected:
        errors.append(f"{location}.manifest.slides: 1から連番にしてください")
    return not any(error.startswith(location) for error in errors)


def load_machine_report(
    review_path: Path, entry: object, location: str, errors: list[str], required: bool = True
) -> dict | None:
    if not isinstance(entry, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return None
    if required is False and entry.get("required") is False:
        return None
    report_path = resolve_path(review_path.parent, entry.get("path"))
    if report_path is None or not report_path.is_file():
        errors.append(f"{location}.path: ファイルが見つかりません")
        return None
    expected_hash = entry.get("sha256")
    actual_hash = file_sha256(report_path)
    if expected_hash != actual_hash:
        errors.append(f"{location}.sha256: {actual_hash}にしてください")
    try:
        return json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{location}: JSONを読み込めません: {exc}")
        return None


def validate_machine_evidence(
    review_path: Path, evidence: object, deck: dict, slide_count: int, errors: list[str], version: int
) -> bool:
    location = "machine_evidence"
    if not isinstance(evidence, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    source_path = resolve_path(review_path.parent, deck.get("source"))
    if source_path is None or not source_path.is_file():
        errors.append("deck.source: Review v6〜v8では実在するPPTXを指定してください")
        return False
    source_hash = file_sha256(source_path)
    audit = load_machine_report(review_path, evidence.get("audit_report"), f"{location}.audit_report", errors)
    metrics = load_machine_report(review_path, evidence.get("visual_metrics_report"), f"{location}.visual_metrics_report", errors)
    lint = load_machine_report(review_path, evidence.get("japanese_lint_report"), f"{location}.japanese_lint_report", errors)
    diff_entry = evidence.get("content_diff_report")
    diff_required = not isinstance(diff_entry, dict) or diff_entry.get("required") is not False
    diff = load_machine_report(review_path, diff_entry, f"{location}.content_diff_report", errors, diff_required)
    design = None
    if version in {7, 8}:
        design = load_machine_report(
            review_path, evidence.get("design_system_report"), f"{location}.design_system_report", errors
        )
    passed = True
    for name, report in (("audit_report", audit), ("visual_metrics_report", metrics), ("japanese_lint_report", lint)):
        if not isinstance(report, dict):
            passed = False
            continue
        if report.get("source_pptx_sha256") != source_hash:
            errors.append(f"{location}.{name}: 対象PPTXのSHA-256と一致しません")
            passed = False
        if report.get("slide_count") != slide_count:
            errors.append(f"{location}.{name}.slide_count: {slide_count}にしてください")
            passed = False
    if isinstance(lint, dict) and lint.get("pass") is not True:
        passed = False
    if diff_required:
        if not isinstance(diff, dict):
            passed = False
        else:
            if diff.get("after_pptx_sha256") != source_hash:
                errors.append(f"{location}.content_diff_report: afterが対象PPTXと一致しません")
                passed = False
            if diff.get("preservation_pass") is not True:
                passed = False
    if version in {7, 8}:
        if not isinstance(design, dict):
            passed = False
        else:
            if design.get("source_pptx_sha256") != source_hash:
                errors.append(f"{location}.design_system_report: 対象PPTXのSHA-256と一致しません")
                passed = False
            if design.get("slide_count") != slide_count:
                errors.append(f"{location}.design_system_report.slide_count: {slide_count}にしてください")
                passed = False
            if design.get("pass") is not True:
                passed = False
            if version == 8:
                summary = design.get("summary", {})
                for key in ("locked_layout_contract_pass", "design_direction_selection_traceability_pass", "anti_slop_pass"):
                    if summary.get(key) is not True:
                        passed = False
    thresholds = evidence.get("thresholds")
    if not isinstance(thresholds, dict):
        errors.append(f"{location}.thresholds: オブジェクトで必須です")
        thresholds = {}
    repetition_policy = deck.get("repetition_policy", "strict")
    motif_limit = repetition_limits(slide_count, repetition_policy)[0]
    expected_thresholds = {
        "min_average_native_element_ratio": 0.8,
        "max_high_similarity_cluster_ratio": motif_limit,
    }
    if version in {7, 8}:
        expected_thresholds["min_design_token_match_ratio"] = 0.7
    if version == 8:
        expected_thresholds.update({"max_gradient_fill_count": 0, "max_glow_effect_count": 0})
    for key, expected in expected_thresholds.items():
        if thresholds.get(key) != expected:
            errors.append(f"{location}.thresholds.{key}: {expected}にしてください")
    if isinstance(metrics, dict):
        summary = metrics.get("summary", {})
        if summary.get("average_native_element_ratio", 0) < 0.8:
            passed = False
        if summary.get("largest_high_similarity_cluster_ratio", 1) > motif_limit + 1e-9:
            passed = False
    if version in {7, 8} and isinstance(design, dict):
        if design.get("summary", {}).get("design_token_match_ratio", 0) < 0.7:
            passed = False
        if version == 8:
            anti_metrics = design.get("summary", {}).get("anti_slop_metrics", {})
            if anti_metrics.get("gradient_fill_count", 1) > 0 or anti_metrics.get("glow_effect_count", 1) > 0:
                passed = False
    return passed


def validate_delivery_gates(gates: object, slide_count: int, errors: list[str], version: int = 5) -> bool:
    location = "delivery_gates"
    if not isinstance(gates, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    passed = True
    expected = list(range(1, slide_count + 1))
    required_gates = set(DELIVERY_GATES)
    if version in {7, 8}:
        required_gates.add(DESIGN_SYSTEM_GATE)
    if version == 8:
        required_gates.update(V8_GATES)
    for name in sorted(required_gates):
        gate = gates.get(name)
        gate_location = f"{location}.{name}"
        if not isinstance(gate, dict):
            errors.append(f"{gate_location}: オブジェクトで必須です")
            passed = False
            continue
        if gate.get("verdict") not in {"pass", "fail"}:
            errors.append(f"{gate_location}.verdict: pass/failから選んでください")
            passed = False
        elif gate.get("verdict") != "pass":
            passed = False
        if gate.get("evidence") in (None, "", []):
            errors.append(f"{gate_location}.evidence: 必須です")
        checked = gate.get("checked_slides")
        if not isinstance(checked, list) or sorted(checked) != expected:
            errors.append(f"{gate_location}.checked_slides: 全スライド番号を含めてください")
        failed = gate.get("failed_slides")
        if not isinstance(failed, list) or any(
            not isinstance(number, int) or number not in expected for number in failed
        ):
            errors.append(f"{gate_location}.failed_slides: 有効なスライド番号の配列にしてください")
        elif gate.get("verdict") == "pass" and failed:
            errors.append(f"{gate_location}.failed_slides: passでは空配列にしてください")
        elif gate.get("verdict") == "fail" and not failed:
            errors.append(f"{gate_location}.failed_slides: failでは1件以上必要です")
    return passed


def validate_consulting_quality_test(test: object, slide_count: int, errors: list[str]) -> bool:
    location = "tests.consulting_quality"
    if not isinstance(test, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    for key in (
        "decision_visible_by_slide", "evidence_to_implication_slides",
        "evidence_to_action_slides", "showpiece_slides", "page_economy_failed_slides", "verdict",
    ):
        if key not in test:
            errors.append(f"{location}.{key}: 必須です")
    decision_slide = test.get("decision_visible_by_slide")
    if not isinstance(decision_slide, int) or not 1 <= decision_slide <= slide_count:
        errors.append(f"{location}.decision_visible_by_slide: 1〜{slide_count}の整数にしてください")
    decision_pass = isinstance(decision_slide, int) and 1 <= decision_slide <= min(2, slide_count)
    combined: set[int] = set()
    for key in ("evidence_to_implication_slides", "evidence_to_action_slides"):
        values = test.get(key)
        if not isinstance(values, list) or any(not isinstance(number, int) or not 1 <= number <= slide_count for number in values):
            errors.append(f"{location}.{key}: 有効なスライド番号の配列にしてください")
        else:
            combined.update(values)
    minimum_linked = max(1, math.ceil(slide_count * 0.4))
    linkage_pass = len(combined) >= minimum_linked
    showpieces = test.get("showpiece_slides")
    if not isinstance(showpieces, list) or any(not isinstance(number, int) or not 1 <= number <= slide_count for number in showpieces):
        errors.append(f"{location}.showpiece_slides: 有効なスライド番号の配列にしてください")
        showpiece_pass = False
    else:
        min_showpiece = 2 if slide_count >= 10 else 1
        max_showpiece = 3 if slide_count >= 6 else slide_count
        showpiece_pass = min_showpiece <= len(set(showpieces)) <= max_showpiece
    economy_failed = test.get("page_economy_failed_slides")
    economy_pass = isinstance(economy_failed, list) and not economy_failed
    if not isinstance(economy_failed, list):
        errors.append(f"{location}.page_economy_failed_slides: 配列にしてください")
    expected = decision_pass and linkage_pass and showpiece_pass and economy_pass
    expected_verdict = "pass" if expected else "fail"
    if test.get("verdict") != expected_verdict:
        errors.append(f"{location}.verdict: {expected_verdict}にしてください")
    return expected


def validate_design_direction_test(test: object, slide_count: int, errors: list[str]) -> bool:
    location = "tests.design_direction_fidelity"
    if not isinstance(test, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    representative = test.get("representative_slide")
    traits = test.get("observed_traits")
    conflicts = test.get("conflicting_traits")
    if not isinstance(representative, int) or not 1 <= representative <= slide_count:
        errors.append(f"{location}.representative_slide: 1〜{slide_count}の整数にしてください")
    if not isinstance(traits, list) or len(traits) < 3 or any(not str(item).strip() for item in traits):
        errors.append(f"{location}.observed_traits: 完成PNGで確認した特徴を3件以上指定してください")
    if not isinstance(conflicts, list):
        errors.append(f"{location}.conflicting_traits: 配列で必須です")
        conflicts = []
    expected = isinstance(representative, int) and 1 <= representative <= slide_count and isinstance(traits, list) and len(traits) >= 3 and not conflicts
    verdict = "pass" if expected else "fail"
    if test.get("verdict") != verdict:
        errors.append(f"{location}.verdict: {verdict}にしてください")
    return expected


def calculate_score(scores: dict[str, int], weights: dict[str, int]) -> int:
    weighted = sum(scores[name] * weight for name, weight in weights.items())
    return round(weighted / 100 * 10)


def is_complete_score_set(scores: dict, weights: dict[str, int]) -> bool:
    return all(isinstance(scores.get(name), int) and 1 <= scores[name] <= 10 for name in weights)


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


def repetition_limits(slide_count: int, policy: str) -> tuple[float, int, float, int]:
    strict_motif = max_motif_ratio_limit(slide_count)
    motif = strict_motif if policy == "strict" else max(strict_motif, 0.6 if policy == "balanced" else 0.8)
    distinct = required_distinct_count(slide_count)
    distinct = max(1, distinct - (1 if policy == "balanced" else 2 if policy == "consistent" else 0))
    box = 0.6 if policy == "strict" else 0.7 if policy == "balanced" else 0.8
    reading_run = 2 if policy == "strict" else 3 if policy == "balanced" else 4
    return motif, distinct, box, reading_run


def repeated_runs(
    fingerprints: list[dict], key_names: tuple[str, ...], minimum_length: int = 3
) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[dict] = []
    sentinel = {"slide_number": -1, **{key: "__end__" for key in key_names}}
    for item in fingerprints + [sentinel]:
        signature = tuple(item.get(key) for key in key_names)
        current_signature = tuple(current[-1].get(key) for key in key_names) if current else None
        if not current or signature == current_signature:
            current.append(item)
            continue
        if len(current) >= minimum_length:
            runs.append([entry["slide_number"] for entry in current])
        current = [item]
    return runs


def normalize_runs(value: object) -> list[list[int]] | None:
    if not isinstance(value, list):
        return None
    normalized: list[list[int]] = []
    for run in value:
        if not isinstance(run, list) or not run or any(not isinstance(number, int) for number in run):
            return None
        normalized.append(run)
    return normalized


def validate_visual_grammar_test(
    test: object,
    slide_count: int,
    issue_counts_by_dimension: Counter[tuple[str, str]],
    errors: list[str],
    version: int = 3,
    repetition_policy: str = "strict",
) -> bool:
    location = "tests.visual_grammar"
    if not isinstance(test, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    if not test.get("method"):
        errors.append(f"{location}.method: 必須です")

    motif_limit, expected_distinct, box_limit, reading_limit = repetition_limits(slide_count, repetition_policy)
    thresholds = test.get("thresholds")
    if not isinstance(thresholds, dict):
        errors.append(f"{location}.thresholds: オブジェクトで必須です")
        thresholds = {}
    expected_thresholds = {
        "max_box_dominant_ratio": box_limit,
        "max_takeaway_band_ratio": box_limit,
        "min_distinct_spatial_models": expected_distinct,
        "min_distinct_primary_primitives": expected_distinct,
        "max_consecutive_same_reading_path": reading_limit,
    }
    if version in {4, 5}:
        expected_thresholds.update({
            "max_shared_motif_ratio": motif_limit,
            "max_node_line_dominant_ratio": motif_limit,
            "min_distinct_visual_textures": expected_distinct,
        })
    for key, expected in expected_thresholds.items():
        if thresholds.get(key) != expected:
            errors.append(f"{location}.thresholds.{key}: {expected}にしてください")

    fingerprints = test.get("slide_fingerprints")
    if not isinstance(fingerprints, list):
        errors.append(f"{location}.slide_fingerprints: 配列で必須です")
        fingerprints = []
    valid_fingerprints: list[dict] = []
    numbers: list[int] = []
    for index, fingerprint in enumerate(fingerprints, start=1):
        item_location = f"{location}.slide_fingerprints[{index}]"
        if not isinstance(fingerprint, dict):
            errors.append(f"{item_location}: オブジェクトにしてください")
            continue
        required_keys = [
            "slide_number", "spatial_model", "primary_primitive", "reading_path",
            "container_dependency", "takeaway_band", "evidence",
        ]
        if version in {4, 5}:
            required_keys.extend([
                "visual_texture", "dominant_node_shape", "node_usage", "connector_usage",
                "connector_character", "signature_tokens",
            ])
        for key in required_keys:
            if fingerprint.get(key) in (None, "", []):
                errors.append(f"{item_location}.{key}: 必須です")
        number = fingerprint.get("slide_number")
        if isinstance(number, int):
            numbers.append(number)
        else:
            errors.append(f"{item_location}.slide_number: 整数にしてください")
        base_valid = True
        for key, allowed in (
            ("spatial_model", SPATIAL_MODELS),
            ("primary_primitive", PRIMARY_PRIMITIVES),
            ("reading_path", READING_PATHS),
            ("container_dependency", CONTAINER_DEPENDENCIES),
        ):
            if fingerprint.get(key) not in allowed:
                errors.append(f"{item_location}.{key}: 未対応の値です")
                base_valid = False
        if not isinstance(fingerprint.get("takeaway_band"), bool):
            errors.append(f"{item_location}.takeaway_band: true/falseにしてください")
            base_valid = False
        motif_valid = True
        if version in {4, 5}:
            for key, allowed in (
                ("visual_texture", VISUAL_TEXTURES),
                ("dominant_node_shape", NODE_SHAPES),
                ("node_usage", MOTIF_USAGES),
                ("connector_usage", MOTIF_USAGES),
                ("connector_character", CONNECTOR_CHARACTERS),
            ):
                if fingerprint.get(key) not in allowed:
                    errors.append(f"{item_location}.{key}: 未対応の値です")
                    motif_valid = False
            tokens = fingerprint.get("signature_tokens")
            if not isinstance(tokens, list) or not tokens:
                errors.append(f"{item_location}.signature_tokens: 1件以上の配列にしてください")
                motif_valid = False
            elif any(token not in MOTIF_TOKENS for token in tokens) or len(tokens) != len(set(tokens)):
                errors.append(f"{item_location}.signature_tokens: 対応値を重複なく指定してください")
                motif_valid = False
        if isinstance(number, int) and base_valid and motif_valid:
            valid_fingerprints.append(fingerprint)

    if sorted(numbers) != list(range(1, slide_count + 1)):
        errors.append(f"{location}.slide_fingerprints: 全スライドを1回ずつ含めてください")
    valid_fingerprints.sort(key=lambda item: item["slide_number"])

    box_slides = sorted(
        item["slide_number"] for item in valid_fingerprints
        if item["primary_primitive"] == "container_cards" or item["container_dependency"] == "high"
    )
    takeaway_slides = sorted(item["slide_number"] for item in valid_fingerprints if item["takeaway_band"])
    box_ratio = round(len(box_slides) / slide_count, 2)
    takeaway_ratio = round(len(takeaway_slides) / slide_count, 2)
    distinct_spatial = len({item["spatial_model"] for item in valid_fingerprints})
    distinct_primitives = len({item["primary_primitive"] for item in valid_fingerprints})
    grammar_runs = repeated_runs(valid_fingerprints, ("spatial_model", "primary_primitive", "reading_path"))
    reading_runs = repeated_runs(valid_fingerprints, ("reading_path",))

    metrics = test.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{location}.metrics: オブジェクトで必須です")
        metrics = {}
    expected_metrics: dict[str, object] = {
        "box_dominant_slides": box_slides,
        "box_dominant_ratio": box_ratio,
        "takeaway_band_slides": takeaway_slides,
        "takeaway_band_ratio": takeaway_ratio,
        "distinct_spatial_models": distinct_spatial,
        "distinct_primary_primitives": distinct_primitives,
    }
    motif_pass = True
    if version in {4, 5}:
        node_line_slides = sorted(
            item["slide_number"] for item in valid_fingerprints
            if item["node_usage"] == "dominant" and item["connector_usage"] == "dominant"
        )
        node_line_ratio = round(len(node_line_slides) / slide_count, 2)
        distinct_textures = len({item["visual_texture"] for item in valid_fingerprints})
        shared_motifs = {
            token: sorted(item["slide_number"] for item in valid_fingerprints if token in item["signature_tokens"])
            for token in sorted(MOTIF_TOKENS)
        }
        shared_motifs = {token: slides for token, slides in shared_motifs.items() if slides}
        max_shared_ratio = round(max((len(slides) for slides in shared_motifs.values()), default=0) / slide_count, 2)
        expected_metrics.update({
            "node_line_dominant_slides": node_line_slides,
            "node_line_dominant_ratio": node_line_ratio,
            "distinct_visual_textures": distinct_textures,
            "shared_motifs": shared_motifs,
            "max_shared_motif_ratio": max_shared_ratio,
        })
        motif_pass = (
            node_line_ratio <= motif_limit
            and max_shared_ratio <= motif_limit
            and distinct_textures >= expected_distinct
        )
    for key, expected in expected_metrics.items():
        if metrics.get(key) != expected:
            errors.append(f"{location}.metrics.{key}: {expected}にしてください")
    for key, expected in (
        ("repeated_grammar_runs", grammar_runs),
        ("repeated_reading_path_runs", reading_runs),
    ):
        supplied = normalize_runs(metrics.get(key))
        if supplied is None:
            errors.append(f"{location}.metrics.{key}: 番号配列の配列にしてください")
        elif supplied != expected:
            errors.append(f"{location}.metrics.{key}: {expected}にしてください")

    expected_pass = (
        len(valid_fingerprints) == slide_count
        and box_ratio <= box_limit
        and takeaway_ratio <= box_limit
        and distinct_spatial >= expected_distinct
        and distinct_primitives >= expected_distinct
        and not grammar_runs
        and not reading_runs
        and motif_pass
    )
    expected_verdict = "pass" if expected_pass else "fail"
    if test.get("verdict") != expected_verdict:
        errors.append(f"{location}.verdict: {expected_verdict}にしてください")
    if not expected_pass and issue_counts_by_dimension[("visual_grammar_variety", "major")] < 1:
        errors.append("visual_grammar_variety: 視覚文法テストfailではmajor Issueが1件以上必要です")
    return expected_pass


def validate_thumbnail_similarity_test(
    test: object,
    slide_count: int,
    issue_counts_by_dimension: Counter[tuple[str, str]],
    errors: list[str],
    repetition_policy: str = "strict",
) -> bool:
    location = "tests.thumbnail_similarity"
    if not isinstance(test, dict):
        errors.append(f"{location}: オブジェクトで必須です")
        return False
    if not test.get("method"):
        errors.append(f"{location}.method: 必須です")
    limit = repetition_limits(slide_count, repetition_policy)[0]
    threshold = test.get("threshold")
    if not isinstance(threshold, dict) or threshold.get("max_high_similarity_cluster_ratio") != limit:
        errors.append(f"{location}.threshold.max_high_similarity_cluster_ratio: {limit}にしてください")
    clusters = test.get("clusters")
    if not isinstance(clusters, list):
        errors.append(f"{location}.clusters: 配列で必須です")
        clusters = []
    high_clusters: list[list[int]] = []
    for index, cluster in enumerate(clusters, start=1):
        item_location = f"{location}.clusters[{index}]"
        if not isinstance(cluster, dict):
            errors.append(f"{item_location}: オブジェクトにしてください")
            continue
        slides = cluster.get("slides")
        traits = cluster.get("shared_traits")
        strength = cluster.get("strength")
        if (
            not isinstance(slides, list) or len(slides) < 2
            or len(slides) != len(set(slides))
            or any(not isinstance(number, int) or not 1 <= number <= slide_count for number in slides)
        ):
            errors.append(f"{item_location}.slides: 2件以上の重複しない有効なページ番号にしてください")
            slides = []
        if not isinstance(traits, list) or not traits:
            errors.append(f"{item_location}.shared_traits: 1件以上の配列にしてください")
        if strength not in {"high", "medium"}:
            errors.append(f"{item_location}.strength: high/mediumから選んでください")
        if not cluster.get("evidence"):
            errors.append(f"{item_location}.evidence: 必須です")
        if strength == "high" and slides:
            high_clusters.append(sorted(slides))
    high_clusters.sort(key=lambda slides: (-len(slides), slides))
    largest = high_clusters[0] if high_clusters else []
    ratio = round(len(largest) / slide_count, 2)
    metrics = test.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{location}.metrics: オブジェクトで必須です")
        metrics = {}
    if metrics.get("largest_high_similarity_cluster") != largest:
        errors.append(f"{location}.metrics.largest_high_similarity_cluster: {largest}にしてください")
    if metrics.get("largest_high_similarity_cluster_ratio") != ratio:
        errors.append(f"{location}.metrics.largest_high_similarity_cluster_ratio: {ratio}にしてください")
    expected_pass = ratio <= limit
    expected_verdict = "pass" if expected_pass else "fail"
    if test.get("verdict") != expected_verdict:
        errors.append(f"{location}.verdict: {expected_verdict}にしてください")
    if not expected_pass and issue_counts_by_dimension[("visual_grammar_variety", "major")] < 1:
        errors.append("visual_grammar_variety: サムネイル類似性failではmajor Issueが1件以上必要です")
    return expected_pass


def validate(path: Path, data_override: dict | None = None) -> list[str]:
    data = data_override if data_override is not None else yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["ルートはオブジェクトである必要があります"]

    version = data.get("version")
    original_version = version
    if version not in {1, 2, 3, 4, 5, 6, 7, 8}:
        errors.append("version: 1〜8のいずれかを指定してください")
    scoring_version = 5 if version in {6, 7, 8} else version
    weights = WEIGHTS_V7 if original_version in {7, 8} else WEIGHTS_V5 if scoring_version == 5 else WEIGHTS_V3 if scoring_version in {3, 4} else WEIGHTS_V2 if scoring_version == 2 else WEIGHTS_V1
    version = scoring_version
    dimensions = set(weights)

    deck = data.get("deck")
    if not isinstance(deck, dict):
        return errors + ["deck: オブジェクトである必要があります"]
    required_deck = [
        "source", "slide_count", "inspected_slides", "critical_issues",
        "scores", "overall_score", "pass",
    ]
    if scoring_version in {2, 3, 4, 5}:
        required_deck.extend(["major_issues", "minor_issues", "score_evidence"])
    if original_version in {6, 7, 8}:
        required_deck.extend(["deck_type", "repetition_policy"])
    if original_version == 8:
        required_deck.append("delivery_status")
    for key in required_deck:
        if key not in deck:
            errors.append(f"deck.{key}: 必須です")
    repetition_policy = deck.get("repetition_policy", "strict")
    if original_version in {6, 7, 8}:
        if deck.get("deck_type") not in DECK_TYPES:
            errors.append("deck.deck_type: 未対応の値です")
        if repetition_policy not in REPETITION_POLICIES:
            errors.append("deck.repetition_policy: strict/balanced/consistentから選んでください")
            repetition_policy = "strict"

    slide_count = deck.get("slide_count")
    inspected = deck.get("inspected_slides", [])
    if not isinstance(slide_count, int) or slide_count < 1:
        errors.append("deck.slide_count: 1以上の整数にしてください")
    if not isinstance(inspected, list) or len(set(inspected)) != len(inspected):
        errors.append("deck.inspected_slides: 重複のない配列にしてください")
    elif isinstance(slide_count, int) and sorted(inspected) != list(range(1, slide_count + 1)):
        errors.append("deck.inspected_slides: 全スライド番号を含めてください")

    render_evidence_valid = True
    delivery_pass = True
    machine_pass = original_version not in {6, 7, 8}
    if scoring_version == 5 and isinstance(slide_count, int) and slide_count >= 1:
        render_evidence_valid = validate_render_evidence(path, data.get("render_evidence"), slide_count, errors, original_version)
        if original_version == 8:
            expected_status = expected_render_delivery_status(path, data.get("render_evidence"))
            if deck.get("delivery_status") != expected_status:
                errors.append(f"deck.delivery_status: {expected_status}にしてください")
        delivery_pass = validate_delivery_gates(data.get("delivery_gates"), slide_count, errors, original_version)
        if original_version in {6, 7, 8}:
            machine_pass = validate_machine_evidence(path, data.get("machine_evidence"), deck, slide_count, errors, original_version)
            if not machine_pass and delivery_pass:
                errors.append("delivery_gates: 機械証跡がfailの場合は対応する納品ゲートをfailにしてください")

    scores = deck.get("scores", {})
    if not isinstance(scores, dict):
        errors.append("deck.scores: オブジェクトにしてください")
    else:
        for name in weights:
            value = scores.get(name)
            if not isinstance(value, int) or not 1 <= value <= 10:
                errors.append(f"deck.scores.{name}: 1〜10の整数にしてください")

    if version in {2, 3, 4, 5}:
        evidence_map = deck.get("score_evidence", {})
        if not isinstance(evidence_map, dict):
            errors.append("deck.score_evidence: オブジェクトにしてください")
            evidence_map = {}
        for name in weights:
            entry = evidence_map.get(name)
            if not isinstance(entry, dict):
                errors.append(f"deck.score_evidence.{name}: オブジェクトで必須です")
                continue
            for key in ("evidence", "caveat"):
                if entry.get(key) in (None, "", []):
                    errors.append(f"deck.score_evidence.{name}.{key}: 必須です")
            if isinstance(scores, dict) and isinstance(scores.get(name), int) and scores[name] >= 9:
                if entry.get("benchmark_evidence") in (None, "", []):
                    errors.append(f"deck.score_evidence.{name}.benchmark_evidence: 9点以上では必須です")

    issue_counts: Counter[str] = Counter()
    issue_counts_by_dimension: Counter[tuple[str, str]] = Counter()
    issue_ids: set[str] = set()
    slide_numbers_in_output: list[int] = []
    slide_verdicts: dict[int, str] = {}
    slides = data.get("slides", [])
    if not isinstance(slides, list):
        errors.append("slides: 配列にしてください")
        slides = []
    for slide_index, slide in enumerate(slides, start=1):
        location_slide = f"slides[{slide_index}]"
        if not isinstance(slide, dict):
            errors.append(f"{location_slide}: オブジェクトにしてください")
            continue
        slide_number = slide.get("slide_number")
        if isinstance(slide_number, int):
            slide_numbers_in_output.append(slide_number)
        elif version in {2, 3, 4, 5}:
            errors.append(f"{location_slide}.slide_number: 整数で必須です")

        if version in {2, 3, 4, 5}:
            test = slide.get("three_second_test")
            if not isinstance(test, dict):
                errors.append(f"{location_slide}.three_second_test: オブジェクトで必須です")
            else:
                for key in ("expected_message", "observed_message", "verdict", "visual_anchor", "obstacle"):
                    if test.get(key) in (None, "", []):
                        errors.append(f"{location_slide}.three_second_test.{key}: 必須です")
                verdict = test.get("verdict")
                if verdict not in THREE_SECOND_VERDICTS:
                    errors.append(f"{location_slide}.three_second_test.verdict: pass/partial/failから選んでください")
                elif isinstance(slide_number, int):
                    slide_verdicts[slide_number] = verdict

        issues = slide.get("issues", [])
        if not isinstance(issues, list):
            errors.append(f"{location_slide}.issues: 配列にしてください")
            continue
        for issue_index, issue in enumerate(issues, start=1):
            location = f"{location_slide}.issues[{issue_index}]"
            if not isinstance(issue, dict):
                errors.append(f"{location}: オブジェクトにしてください")
                continue
            for key in ("id", "dimension", "severity", "target", "evidence", "action", "expected_effect", "patch_hint"):
                if issue.get(key) in (None, "", []):
                    errors.append(f"{location}.{key}: 必須です")
            issue_id = issue.get("id")
            if issue_id in issue_ids:
                errors.append(f"{location}.id: 重複しています")
            issue_ids.add(issue_id)
            dimension = issue.get("dimension")
            severity = issue.get("severity")
            if dimension not in dimensions:
                errors.append(f"{location}.dimension: 未対応の値です")
            if severity not in SEVERITIES:
                errors.append(f"{location}.severity: 未対応の値です")
            else:
                issue_counts[severity] += 1
                if dimension in dimensions:
                    issue_counts_by_dimension[(dimension, severity)] += 1
                if version in {2, 3, 4, 5} and severity == "critical":
                    verification = issue.get("verification")
                    if not isinstance(verification, dict):
                        errors.append(f"{location}.verification: criticalではオブジェクトで必須です")
                    else:
                        if verification.get("full_size_recheck") is not True:
                            errors.append(f"{location}.verification.full_size_recheck: trueで必須です")
                        if not verification.get("source_crosscheck"):
                            errors.append(f"{location}.verification.source_crosscheck: 必須です")
                        if verification.get("confidence") != "high":
                            errors.append(f"{location}.verification.confidence: highにしてください")
            hint = issue.get("patch_hint", {})
            if not isinstance(hint, dict):
                errors.append(f"{location}.patch_hint: オブジェクトにしてください")
            else:
                if hint.get("kind") not in PATCH_KINDS:
                    errors.append(f"{location}.patch_hint.kind: 未対応の値です")
                if hint.get("destination") not in DESTINATIONS:
                    errors.append(f"{location}.patch_hint.destination: 未対応の値です")
                if not hint.get("object_ref"):
                    errors.append(f"{location}.patch_hint.object_ref: 必須です")

    if deck.get("critical_issues") != issue_counts["critical"]:
        errors.append(f"deck.critical_issues: {issue_counts['critical']}にしてください")
    if version in {2, 3, 4, 5}:
        if deck.get("major_issues") != issue_counts["major"]:
            errors.append(f"deck.major_issues: {issue_counts['major']}にしてください")
        if deck.get("minor_issues") != issue_counts["minor"]:
            errors.append(f"deck.minor_issues: {issue_counts['minor']}にしてください")
        if isinstance(slide_count, int) and sorted(slide_numbers_in_output) != list(range(1, slide_count + 1)):
            errors.append("slides: 全スライドを1回ずつ含めてください")
    if version == 5 and issue_counts["critical"] > 0 and delivery_pass:
        errors.append("delivery_gates: critical Issueがある場合は少なくとも1件をfailにしてください")

    failed_slides: list[int] = []
    pattern_pass = False
    content_verified = False
    grammar_pass = version not in {3, 4, 5}
    similarity_pass = version not in {4, 5}
    consulting_pass = version != 5
    direction_pass = original_version != 8
    if version in {2, 3, 4, 5}:
        tests = data.get("tests")
        if not isinstance(tests, dict):
            errors.append("tests: オブジェクトで必須です")
            tests = {}
        three_second = tests.get("three_second", {})
        if not isinstance(three_second, dict):
            errors.append("tests.three_second: オブジェクトにしてください")
            three_second = {}
        if not three_second.get("method"):
            errors.append("tests.three_second.method: 必須です")
        groups = {
            "pass": three_second.get("passed_slides", []),
            "partial": three_second.get("partial_slides", []),
            "fail": three_second.get("failed_slides", []),
        }
        grouped: list[int] = []
        for name, values in groups.items():
            if not isinstance(values, list):
                errors.append(f"tests.three_second.{name}: 配列にしてください")
            else:
                grouped.extend(values)
        if isinstance(slide_count, int) and sorted(grouped) != list(range(1, slide_count + 1)):
            errors.append("tests.three_second: 全スライドを重複なく分類してください")
        for number, verdict in slide_verdicts.items():
            if number not in groups.get(verdict, []):
                errors.append(f"slides[{number}].three_second_test.verdict: tests.three_secondと一致させてください")
        failed_slides = groups.get("fail", []) if isinstance(groups.get("fail"), list) else []

        repetition = tests.get("pattern_repetition", {})
        if not isinstance(repetition, dict):
            errors.append("tests.pattern_repetition: オブジェクトにしてください")
        else:
            if repetition.get("verdict") not in {"pass", "fail"}:
                errors.append("tests.pattern_repetition.verdict: pass/failから選んでください")
            if not isinstance(repetition.get("repeated_runs"), list):
                errors.append("tests.pattern_repetition.repeated_runs: 配列にしてください")
            pattern_pass = repetition.get("verdict") == "pass"

        preservation = tests.get("content_preservation", {})
        if not isinstance(preservation, dict):
            errors.append("tests.content_preservation: オブジェクトにしてください")
        else:
            if not isinstance(preservation.get("verified"), bool):
                errors.append("tests.content_preservation.verified: true/falseで必須です")
            if not preservation.get("evidence"):
                errors.append("tests.content_preservation.evidence: 必須です")
            content_verified = preservation.get("verified") is True

        if version in {3, 4, 5} and isinstance(slide_count, int) and slide_count >= 1:
            grammar_pass = validate_visual_grammar_test(
                tests.get("visual_grammar"), slide_count, issue_counts_by_dimension, errors, version, repetition_policy
            )
        if version in {4, 5} and isinstance(slide_count, int) and slide_count >= 1:
            similarity_pass = validate_thumbnail_similarity_test(
                tests.get("thumbnail_similarity"), slide_count, issue_counts_by_dimension, errors, repetition_policy
            )
        if version == 5 and isinstance(slide_count, int) and slide_count >= 1:
            consulting_pass = validate_consulting_quality_test(
                tests.get("consulting_quality"), slide_count, errors
            )
            if original_version == 8:
                direction_pass = validate_design_direction_test(
                    tests.get("design_direction_fidelity"), slide_count, errors
                )

    if isinstance(scores, dict) and is_complete_score_set(scores, weights):
        calculated = calculate_score(scores, weights)
        if deck.get("overall_score") != calculated:
            errors.append(f"deck.overall_score: {calculated}にしてください")
        if version in {2, 3, 4, 5}:
            for name, score in scores.items():
                if score >= 9 and (
                    issue_counts_by_dimension[(name, "critical")] > 0
                    or issue_counts_by_dimension[(name, "major")] > 0
                ):
                    errors.append(f"deck.scores.{name}: critical/major Issueがあるため9点以上にできません")
                if score == 10 and any(issue_counts_by_dimension[(name, severity)] > 0 for severity in SEVERITIES):
                    errors.append(f"deck.scores.{name}: Issueがあるため10点にできません")
            if version in {3, 4, 5} and (not grammar_pass or not similarity_pass) and scores.get("visual_grammar_variety", 10) >= 7:
                errors.append("deck.scores.visual_grammar_variety: 視覚文法または類似性テストfailでは6点以下にしてください")
            expected_pass = (
                calculated >= 80
                and all(value >= 7 for value in scores.values())
                and issue_counts["critical"] == 0
                and issue_counts["major"] == 0
                and not failed_slides
                and pattern_pass
                and grammar_pass
                and similarity_pass
                and content_verified
                and render_evidence_valid
                and delivery_pass
                and consulting_pass
                and direction_pass
                and machine_pass
                and isinstance(slide_count, int)
                and sorted(inspected) == list(range(1, slide_count + 1))
            )
        else:
            expected_pass = (
                calculated >= 80
                and scores["message_clarity"] >= 7
                and scores["visual_hierarchy"] >= 7
                and issue_counts["critical"] == 0
                and isinstance(slide_count, int)
                and sorted(inspected) == list(range(1, slide_count + 1))
            )
        if deck.get("pass") is not expected_pass:
            errors.append(f"deck.pass: {str(expected_pass).lower()}にしてください")

    if not isinstance(data.get("prioritized_actions"), list):
        errors.append("prioritized_actions: 配列で必須です")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("使用法: python validate_review.py <review.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ファイルが見つかりません: {path}")
        return 2
    errors = validate(path)
    if errors:
        print("Reviewの検証に失敗しました:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Reviewは有効です。")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
