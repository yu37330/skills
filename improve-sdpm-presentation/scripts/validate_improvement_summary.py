#!/usr/bin/env python3
"""改善サマリーYAML v1/v2/v3の契約とPoC状態を検証する。"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAMLが必要です。実行環境へpyyamlを追加してください。") from exc


STATUSES = {"pending_human_validation", "partially_validated", "validated", "failed"}
CHANGE_LEVELS = {"repair", "recompose", "transform"}


def validate(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["ルートはオブジェクトである必要があります"]
    version = data.get("version")
    if version not in {1, 2, 3}:
        errors.append("version: 1、2、3のいずれかを指定してください")
    for key in (
        "source", "slide_count", "revisions_used", "scores", "preservation",
        "editability", "changed_slides", "unresolved_issues", "automated_visual_pass",
        "human_validation", "poc_status",
    ):
        if key not in data:
            errors.append(f"{key}: 必須です")
    if version in {2, 3} and "visual_grammar" not in data:
        errors.append("visual_grammar: version 2以降では必須です")
    if version == 3 and "motif_similarity" not in data:
        errors.append("motif_similarity: version 3では必須です")

    revisions = data.get("revisions_used")
    if not isinstance(revisions, int) or not 0 <= revisions <= 2:
        errors.append("revisions_used: 0〜2の整数にしてください")

    slide_count = data.get("slide_count", {})
    if not isinstance(slide_count, dict):
        errors.append("slide_count: オブジェクトにしてください")
    else:
        baseline = slide_count.get("baseline")
        improved = slide_count.get("improved")
        if not isinstance(baseline, int) or baseline < 1 or not isinstance(improved, int) or improved < 1:
            errors.append("slide_count.baseline/improved: 1以上の整数にしてください")
        elif baseline != improved:
            errors.append("slide_count: ベースラインと改善版を一致させてください")

    scores = data.get("scores", {})
    if not isinstance(scores, dict):
        errors.append("scores: オブジェクトにしてください")
    else:
        for key in ("baseline", "final", "delta"):
            if not isinstance(scores.get(key), int):
                errors.append(f"scores.{key}: 整数で必須です")
        if all(isinstance(scores.get(key), int) for key in ("baseline", "final", "delta")):
            expected_delta = scores["final"] - scores["baseline"]
            if scores["delta"] != expected_delta:
                errors.append(f"scores.delta: {expected_delta}にしてください")

    if version in {2, 3}:
        grammar = data.get("visual_grammar", {})
        if not isinstance(grammar, dict):
            errors.append("visual_grammar: オブジェクトにしてください")
            grammar = {}
        baseline_grammar = grammar.get("baseline", {})
        final_grammar = grammar.get("final", {})
        delta_grammar = grammar.get("delta", {})
        for section_name, section in (("baseline", baseline_grammar), ("final", final_grammar)):
            if not isinstance(section, dict):
                errors.append(f"visual_grammar.{section_name}: オブジェクトにしてください")
                continue
            for key in ("box_dominant_ratio", "takeaway_band_ratio"):
                value = section.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                    errors.append(f"visual_grammar.{section_name}.{key}: 0〜1の数値にしてください")
            for key in ("distinct_spatial_models", "distinct_primary_primitives"):
                value = section.get(key)
                if not isinstance(value, int) or value < 1:
                    errors.append(f"visual_grammar.{section_name}.{key}: 1以上の整数にしてください")
        if not isinstance(delta_grammar, dict):
            errors.append("visual_grammar.delta: オブジェクトにしてください")
        elif isinstance(baseline_grammar, dict) and isinstance(final_grammar, dict):
            for key in ("box_dominant_ratio", "takeaway_band_ratio"):
                baseline_value = baseline_grammar.get(key)
                final_value = final_grammar.get(key)
                if isinstance(baseline_value, (int, float)) and isinstance(final_value, (int, float)):
                    expected = round(final_value - baseline_value, 2)
                    if delta_grammar.get(key) != expected:
                        errors.append(f"visual_grammar.delta.{key}: {expected}にしてください")

    if version == 3:
        motif = data.get("motif_similarity", {})
        if not isinstance(motif, dict):
            errors.append("motif_similarity: オブジェクトにしてください")
            motif = {}
        baseline_motif = motif.get("baseline", {})
        final_motif = motif.get("final", {})
        delta_motif = motif.get("delta", {})
        ratio_keys = (
            "node_line_dominant_ratio", "max_shared_motif_ratio",
            "largest_thumbnail_cluster_ratio",
        )
        for section_name, section in (("baseline", baseline_motif), ("final", final_motif)):
            if not isinstance(section, dict):
                errors.append(f"motif_similarity.{section_name}: オブジェクトにしてください")
                continue
            for key in ratio_keys:
                value = section.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                    errors.append(f"motif_similarity.{section_name}.{key}: 0〜1の数値にしてください")
            value = section.get("distinct_visual_textures")
            if not isinstance(value, int) or value < 1:
                errors.append(f"motif_similarity.{section_name}.distinct_visual_textures: 1以上の整数にしてください")
        if not isinstance(delta_motif, dict):
            errors.append("motif_similarity.delta: オブジェクトにしてください")
        elif isinstance(baseline_motif, dict) and isinstance(final_motif, dict):
            for key in ratio_keys:
                baseline_value = baseline_motif.get(key)
                final_value = final_motif.get(key)
                if isinstance(baseline_value, (int, float)) and isinstance(final_value, (int, float)):
                    expected = round(final_value - baseline_value, 2)
                    if delta_motif.get(key) != expected:
                        errors.append(f"motif_similarity.delta.{key}: {expected}にしてください")
            baseline_value = baseline_motif.get("distinct_visual_textures")
            final_value = final_motif.get("distinct_visual_textures")
            if isinstance(baseline_value, int) and isinstance(final_value, int):
                expected = final_value - baseline_value
                if delta_motif.get("distinct_visual_textures") != expected:
                    errors.append(f"motif_similarity.delta.distinct_visual_textures: {expected}にしてください")
            for key in ("distinct_spatial_models", "distinct_primary_primitives"):
                baseline_value = baseline_grammar.get(key)
                final_value = final_grammar.get(key)
                if isinstance(baseline_value, int) and isinstance(final_value, int):
                    expected = final_value - baseline_value
                    if delta_grammar.get(key) != expected:
                        errors.append(f"visual_grammar.delta.{key}: {expected}にしてください")

    preservation = data.get("preservation", {})
    if not isinstance(preservation, dict):
        errors.append("preservation: オブジェクトにしてください")
        preservation = {}
    for key in ("content", "order", "speaker_notes"):
        if not isinstance(preservation.get(key), bool):
            errors.append(f"preservation.{key}: true/falseで必須です")

    editability = data.get("editability", {})
    if not isinstance(editability, dict):
        errors.append("editability: オブジェクトにしてください")
    else:
        if not isinstance(editability.get("maintained"), bool):
            errors.append("editability.maintained: true/falseで必須です")
        if not isinstance(editability.get("limitations"), list):
            errors.append("editability.limitations: 配列で必須です")

    changed_slides = data.get("changed_slides", [])
    if not isinstance(changed_slides, list):
        errors.append("changed_slides: 配列にしてください")
    else:
        for index, slide in enumerate(changed_slides, start=1):
            if not isinstance(slide, dict):
                errors.append(f"changed_slides[{index}]: オブジェクトにしてください")
                continue
            if not isinstance(slide.get("slide_number"), int) or slide["slide_number"] < 1:
                errors.append(f"changed_slides[{index}].slide_number: 1以上の整数にしてください")
            if slide.get("change_level") not in CHANGE_LEVELS:
                errors.append(f"changed_slides[{index}].change_level: 未対応の値です")
            if not slide.get("reason"):
                errors.append(f"changed_slides[{index}].reason: 必須です")

    if not isinstance(data.get("unresolved_issues"), list):
        errors.append("unresolved_issues: 配列にしてください")
    if not isinstance(data.get("automated_visual_pass"), bool):
        errors.append("automated_visual_pass: true/falseで必須です")
    if version in {2, 3} and data.get("automated_visual_pass") is True:
        final_grammar = data.get("visual_grammar", {}).get("final", {}) if isinstance(data.get("visual_grammar"), dict) else {}
        improved_count = slide_count.get("improved") if isinstance(slide_count, dict) else None
        required_distinct = 5 if isinstance(improved_count, int) and improved_count >= 10 else 4 if isinstance(improved_count, int) and improved_count >= 6 else min(improved_count or 1, 3)
        box_ratio = final_grammar.get("box_dominant_ratio")
        band_ratio = final_grammar.get("takeaway_band_ratio")
        if isinstance(box_ratio, (int, float)) and box_ratio > 0.6:
            errors.append("automated_visual_pass: 最終版の箱優位率が0.6を超えるためtrueにできません")
        if isinstance(band_ratio, (int, float)) and band_ratio > 0.6:
            errors.append("automated_visual_pass: 最終版の結論帯率が0.6を超えるためtrueにできません")
        for key in ("distinct_spatial_models", "distinct_primary_primitives"):
            value = final_grammar.get(key)
            if isinstance(value, int) and value < required_distinct:
                errors.append(f"automated_visual_pass: final.{key}が{required_distinct}未満のためtrueにできません")
        if version == 3:
            final_motif = data.get("motif_similarity", {}).get("final", {}) if isinstance(data.get("motif_similarity"), dict) else {}
            motif_limit = 0.4 if isinstance(improved_count, int) and improved_count >= 6 else 0.67 if isinstance(improved_count, int) and improved_count >= 3 else 1.0
            for key in (
                "node_line_dominant_ratio", "max_shared_motif_ratio",
                "largest_thumbnail_cluster_ratio",
            ):
                value = final_motif.get(key)
                if isinstance(value, (int, float)) and value > motif_limit:
                    errors.append(f"automated_visual_pass: final.{key}が{motif_limit}を超えるためtrueにできません")
            value = final_motif.get("distinct_visual_textures")
            if isinstance(value, int) and value < required_distinct:
                errors.append(
                    f"automated_visual_pass: final.distinct_visual_texturesが{required_distinct}未満のためtrueにできません"
                )

    human = data.get("human_validation", {})
    if not isinstance(human, dict):
        errors.append("human_validation: オブジェクトにしてください")
        human = {}
    for key in ("blind_test_completed", "manual_edit_time_recorded", "second_topic_tested"):
        if not isinstance(human.get(key), bool):
            errors.append(f"human_validation.{key}: true/falseで必須です")
    if not isinstance(human.get("participants"), int) or human.get("participants", -1) < 0:
        errors.append("human_validation.participants: 0以上の整数にしてください")

    status = data.get("poc_status")
    if status not in STATUSES:
        errors.append("poc_status: 未対応の値です")
    fully_validated = (
        data.get("automated_visual_pass") is True
        and all(preservation.get(key) is True for key in ("content", "order", "speaker_notes"))
        and human.get("blind_test_completed") is True
        and isinstance(human.get("participants"), int)
        and human["participants"] >= 1
        and human.get("manual_edit_time_recorded") is True
        and human.get("second_topic_tested") is True
    )
    if status == "validated" and not fully_validated:
        errors.append("poc_status: 人間評価・手直し時間・別題材テスト完了まではvalidatedにできません")
    if data.get("automated_visual_pass") is False and status not in {"failed", "partially_validated"}:
        errors.append("poc_status: 自動評価不合格時はfailedまたはpartially_validatedにしてください")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("使用法: python validate_improvement_summary.py <improvement-summary.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ファイルが見つかりません: {path}")
        return 2
    errors = validate(path)
    if errors:
        print("改善サマリーの検証に失敗しました:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("改善サマリーは有効です。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
