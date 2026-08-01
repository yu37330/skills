#!/usr/bin/env python3
"""Deck Plan v3をRole LayoutとNative Componentへ解決する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import math
import re
import sys
from pathlib import Path

import yaml

from validate_design_system import design_system_fingerprint, validate_manifest


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_ref(target: Path, base: Path) -> str:
    """Design Resolutionの配置先を基準に移植可能な参照を返す。"""
    return os.path.relpath(target.resolve(), base.resolve()).replace(os.sep, "/")


PREMIUM_LAYOUT_BY_COMPONENT = {
    "narrative.executive_summary": "summary_executive_premium",
    "narrative.key_message_evidence": "key_message_evidence_premium",
    "chart.insight": "chart_insight_premium",
    "narrative.findings_implications": "findings_implications_premium",
    "strategy.house": "strategy_house_premium",
    "strategy.issue_tree": "issue_tree_premium",
    "strategy.portfolio_matrix": "portfolio_matrix_premium",
    "strategy.capability_map": "capability_map_premium",
    "strategy.value_driver_tree": "value_driver_tree_premium",
    "strategy.initiative_portfolio": "initiative_portfolio_premium",
    "execution.roadmap": "roadmap_premium",
    "execution.gantt": "gantt_premium",
    "execution.governance": "governance_premium",
    "execution.kpi_cascade": "kpi_cascade_premium",
    "narrative.recommendation_actions": "recommendation_actions_premium",
}

HINT_ALIASES = {
    "executive_summary": "narrative.executive_summary",
    "key_message_evidence": "narrative.key_message_evidence",
    "chart_insight": "chart.insight",
    "findings_implications": "narrative.findings_implications",
    "strategy_house": "strategy.house",
    "issue_tree": "strategy.issue_tree",
    "portfolio_matrix": "strategy.portfolio_matrix",
    "capability_map": "strategy.capability_map",
    "value_driver_tree": "strategy.value_driver_tree",
    "initiative_portfolio": "strategy.initiative_portfolio",
    "roadmap": "execution.roadmap",
    "gantt": "execution.gantt",
    "governance": "execution.governance",
    "kpi_cascade": "execution.kpi_cascade",
    "recommendation_actions": "narrative.recommendation_actions",
}


def _load_component_hints(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict) and isinstance(data.get("slides"), list):
        return {
            str(item.get("slide_id")): str(item.get("component_hint"))
            for item in data["slides"]
            if isinstance(item, dict) and item.get("slide_id") and item.get("component_hint")
        }
    if isinstance(data, dict):
        return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}
    raise ValueError("component hintsはslide_idとcomponent_hintの対応表にしてください")


def _infer_component_hint(slide: dict) -> str | None:
    purpose = slide.get("slide_purpose")
    relationship = slide.get("relationship")
    linkage = slide.get("evidence_linkage")
    evidence_count = len(slide.get("evidence_ids", [])) if isinstance(slide.get("evidence_ids"), list) else 0
    searchable = " ".join(
        str(slide.get(key) or "") for key in ("executive_headline", "so_what", "must_show", "notes_outline")
    ).lower()
    keyword_map = [
        (("strategy house", "戦略ハウス"), "strategy.house"),
        (("capability map", "ケイパビリティ", "能力マップ"), "strategy.capability_map"),
        (("value driver", "価値ドライバー"), "strategy.value_driver_tree"),
        (("initiative portfolio", "施策ポートフォリオ"), "strategy.initiative_portfolio"),
        (("gantt", "ガント"), "execution.gantt"),
        (("governance", "ガバナンス"), "execution.governance"),
        (("kpi cascade", "kpiツリー", "kpiカスケード"), "execution.kpi_cascade"),
    ]
    for keywords, component_id in keyword_map:
        if any(keyword in searchable for keyword in keywords):
            return component_id
    if purpose == "key_message":
        return "narrative.key_message_evidence" if linkage == "evidence_to_action" or evidence_count >= 2 else "narrative.executive_summary"
    if purpose == "data_proof" and relationship in {"comparison", "change_over_time"}:
        return "chart.insight"
    if purpose == "synthesis" and linkage == "evidence_to_implication":
        return "narrative.findings_implications"
    if purpose == "root_cause" and relationship == "hierarchy":
        return "strategy.issue_tree"
    if purpose == "decision_matrix":
        return "strategy.portfolio_matrix"
    if purpose == "roadmap" and relationship == "sequence":
        return "execution.roadmap"
    if purpose in {"recommendation", "action_plan"} and linkage == "evidence_to_action":
        return "narrative.recommendation_actions"
    return None


def _choose_layout(
    candidates: list[dict],
    slide: dict,
    previous: list[str],
    explicit_hint: str | None = None,
) -> tuple[dict, str, str | None]:
    purpose = slide.get("slide_purpose")
    relationship = slide.get("relationship")
    normalized_hint = HINT_ALIASES.get(explicit_hint or "", explicit_hint)
    component_hint = normalized_hint or _infer_component_hint(slide)
    premium_layout = PREMIUM_LAYOUT_BY_COMPONENT.get(component_hint or "")
    preferred = {
        ("key_message", "connection"): "title_editorial_split",
        ("data_proof", "comparison"): "evidence_metric_gap",
        ("data_proof", "change_over_time"): "evidence_chart_annotation",
        ("comparison", "comparison"): "comparison_gap_asymmetric",
        ("root_cause", "cause_effect"): "synthesis_causal_spine",
        ("synthesis", "connection"): "synthesis_system_map",
        ("recommendation", "connection"): "recommendation_operating_model",
        ("decision_matrix", "comparison"): "decision_matrix_native",
        ("roadmap", "sequence"): "action_roadmap",
        ("action_plan", "sequence"): "action_poc_form",
    }.get((purpose, relationship))
    if premium_layout and any(item.get("id") == premium_layout for item in candidates):
        preferred = premium_layout
        reason = (
            f"component_hint={component_hint}によるPremium Role Layout選択"
            if normalized_hint else
            f"Deck Planのpurpose={purpose}, relationship={relationship}, "
            f"evidence_linkage={slide.get('evidence_linkage')}から{component_hint}を解決"
        )
    else:
        reason = f"V8既定のpurpose={purpose}, relationship={relationship}規則による"
    ordered = sorted(candidates, key=lambda item: item.get("id") != preferred)
    for candidate in ordered:
        if len(previous) < 2 or previous[-2:] != [candidate["id"], candidate["id"]]:
            if preferred and candidate.get("id") != preferred:
                reason += "。3ページ連続を避けるため安全な代替Layoutを選択"
            return candidate, reason, component_hint
    return ordered[0], reason, component_hint


def _contract_sha256(layout: dict) -> str:
    contract = {
        "grid_id": layout.get("grid_id"),
        "locked": layout.get("locked", []),
        "adjustable": layout.get("adjustable", []),
        "content_limits": layout.get("content_limits", {}),
        "slot_frames": layout.get("slot_frames", {}),
    }
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _content_metrics(slide: dict) -> dict[str, int]:
    """Deck PlanだけからLayout選択に必要な文字量・項目量を抽出する。"""
    headline = str(slide.get("executive_headline") or "")
    evidence_ids = slide.get("evidence_ids") if isinstance(slide.get("evidence_ids"), list) else []
    list_keys = (
        "items", "findings", "actions", "phases", "tasks", "levels", "drivers",
        "initiatives", "criteria", "data_points", "must_show",
    )
    explicit_counts = [len(slide.get(key)) for key in list_keys if isinstance(slide.get(key), list)]
    annotation_values = [
        str(slide.get(key) or "")
        for key in ("so_what", "decision_relevance", "primary_evidence")
    ]
    return {
        "headline_chars": len(headline.replace("\n", "")),
        "main_items": max([len(evidence_ids), *explicit_counts, 1]),
        "annotation_chars": max((len(value.replace("\n", "")) for value in annotation_values), default=0),
    }


def _recommended_item_max(contract: dict) -> int | None:
    limits = contract.get("content_limits", {}) if isinstance(contract, dict) else {}
    value = limits.get("recommended_items") if isinstance(limits, dict) else None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        ranges = [int(match.group(2)) for match in re.finditer(r"(\d+)\s*[～~-]\s*(\d+)", value)]
        if ranges:
            return max(ranges)
        numbers = [int(number) for number in re.findall(r"\d+", value)]
        return max(numbers) if numbers else None
    return None


def _capacity(layout: dict, component_contracts: dict[str, dict], variant: str) -> dict[str, int]:
    limits = layout.get("content_limits", {})
    multiplier = 1.25 if variant == "dense" else 1.0
    main_component = layout.get("default_components", {}).get("main")
    contract_max = _recommended_item_max(component_contracts.get(main_component, {}))
    layout_items = int(limits.get("main_items", 1))
    if contract_max is not None:
        layout_items = min(layout_items, contract_max)
    return {
        "headline_chars": max(1, math.floor(int(limits.get("header_chars", 1)) * multiplier)),
        "main_items": max(1, math.floor(layout_items * multiplier)),
        "annotation_chars": (
            0 if int(limits.get("annotation_chars", 0)) == 0
            else max(1, math.floor(int(limits.get("annotation_chars", 0)) * multiplier))
        ),
    }


def _fits_capacity(metrics: dict[str, int], capacity: dict[str, int]) -> bool:
    return (
        metrics["headline_chars"] <= capacity["headline_chars"]
        and metrics["main_items"] <= capacity["main_items"]
        and (capacity["annotation_chars"] == 0 or metrics["annotation_chars"] <= capacity["annotation_chars"])
    )


def _select_layout_variant(
    preferred: dict,
    candidates: list[dict],
    slide: dict,
    component_contracts: dict[str, dict],
) -> tuple[dict, str, dict[str, int], dict[str, int]]:
    """Primary→Dense→代替Layoutの順に容量契約へ適合する構成を選ぶ。"""
    metrics = _content_metrics(slide)
    ordered = [preferred, *(item for item in candidates if item.get("id") != preferred.get("id"))]
    for layout in ordered:
        for variant in ("primary", "dense"):
            if variant not in layout.get("variants", []):
                continue
            main_component = layout.get("default_components", {}).get("main")
            contract = component_contracts.get(main_component, {})
            if variant not in contract.get("variants", ["primary"]):
                continue
            capacity = _capacity(layout, component_contracts, variant)
            if _fits_capacity(metrics, capacity):
                return layout, variant, metrics, capacity
    raise ValueError(
        f"slide_id={slide.get('slide_id')}の情報量がDense上限を超えています: {metrics}。"
        "見出しを短くするか、根拠を分割するか、別Role Layoutを指定してください"
    )


def _audience_class(value: object) -> str:
    text = str(value or "").lower()
    if any(token in text for token in ("経営", "役員", "director", "executive")):
        return "executive"
    if any(token in text for token in ("技術", "専門", "engineer", "specialist")):
        return "specialist"
    return "mixed"


def _resolve_context(loaded: dict, deck: dict) -> dict:
    deck_type = deck.get("deck_type")
    audience = _audience_class(deck.get("audience"))
    duration = deck.get("duration_minutes", 20)
    duration = duration if isinstance(duration, (int, float)) else 20
    matches = [
        item for item in loaded.get("context_models", [])
        if item.get("meeting_type") == deck_type
        and item.get("audience") in {audience, "mixed"}
        and duration <= item.get("duration_max", 10**9)
    ]
    if matches:
        return sorted(matches, key=lambda item: (item.get("audience") != audience, item.get("duration_max", 10**9)))[0]
    return {"density_profile": "D2", "style_profile": "executive_clarity", "deck_sequence": "decision_first"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Deck PlanをDesign Systemへ解決します")
    parser.add_argument("deck_plan", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--theme")
    parser.add_argument("--grammar")
    parser.add_argument("--direction-scout", type=Path)
    parser.add_argument(
        "--component-hints",
        type=Path,
        help="slide_idごとのComponent候補。Deck Planへ座標やThemeを追加せずPremium部品を明示する",
    )
    args = parser.parse_args()

    deck_path = args.deck_plan.resolve()
    manifest_path = args.manifest.resolve()
    errors, loaded = validate_manifest(manifest_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    deck_plan = yaml.safe_load(deck_path.read_text(encoding="utf-8-sig"))
    if not isinstance(deck_plan, dict) or deck_plan.get("version") != 3:
        print("ERROR: Deck Plan version 3を指定してください")
        return 1

    manifest = loaded["manifest"]
    defaults = manifest["defaults"]
    deck = deck_plan.get("deck", {})
    deck_type = deck.get("deck_type")
    context = _resolve_context(loaded, deck)
    direction = None
    if args.direction_scout:
        direction_path = args.direction_scout.resolve()
        direction = yaml.safe_load(direction_path.read_text(encoding="utf-8-sig"))
        if not isinstance(direction, dict) or direction.get("status") != "selected" or not isinstance(direction.get("selected"), dict):
            print("ERROR: 選択済みDesign Direction Scoutを指定してください")
            return 1
        if direction.get("source", {}).get("deck_plan_sha256") != _sha256(deck_path):
            print("ERROR: Design Direction ScoutのDeck Plan SHA-256が一致しません")
            return 1
        if direction.get("source", {}).get("design_system_sha256") != design_system_fingerprint(manifest_path, manifest):
            print("ERROR: Design Direction ScoutのDesign System fingerprintが一致しません")
            return 1
        context["style_profile"] = direction["selected"].get("style_profile")
    style = loaded.get("style_map", {}).get(context.get("style_profile"), {})
    grammar = args.grammar or defaults["grammar_by_deck_type"].get(deck_type)
    theme = args.theme or style.get("theme") or defaults["theme_by_deck_type"].get(deck_type)
    if grammar not in loaded["grammar_map"]:
        print(f"ERROR: 未登録grammarです: {grammar}")
        return 1
    if theme not in loaded["themes"]:
        print(f"ERROR: 未登録themeです: {theme}")
        return 1

    role_by_purpose = defaults["role_by_slide_purpose"]
    try:
        component_hints = _load_component_hints(args.component_hints.resolve() if args.component_hints else None)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: component hintsを読み込めません: {exc}")
        return 1
    resolved_slides: list[dict] = []
    previous_layouts: list[str] = []
    for slide in deck_plan.get("slides", []):
        purpose = slide.get("slide_purpose")
        role = role_by_purpose.get(purpose)
        candidates = [
            layout for layout in loaded["layout_map"].values()
            if layout.get("role") == role and purpose in layout.get("purposes", [])
        ]
        if not candidates:
            print(f"ERROR: slide_id={slide.get('slide_id')}に対応するRole Layoutがありません")
            return 1
        layout, selection_reason, component_hint = _choose_layout(
            candidates,
            slide,
            previous_layouts,
            component_hints.get(str(slide.get("slide_id"))),
        )
        preferred_layout_id = layout["id"]
        try:
            layout, capacity_variant, content_metrics, selected_capacity = _select_layout_variant(
                layout, candidates, slide, loaded["component_contract_map"]
            )
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        if layout["id"] != preferred_layout_id:
            selection_reason += f"。情報量により代替Layout={layout['id']}を選択"
        previous_layouts.append(layout["id"])
        variant = capacity_variant
        if (
            variant == "primary"
            and len(previous_layouts) >= 2
            and previous_layouts[-1] == previous_layouts[-2]
            and "alternate" in layout.get("variants", [])
        ):
            variant = "alternate"
        if capacity_variant == "dense":
            selection_reason += f"。文字量・項目量{content_metrics}がPrimary上限を超えるためdenseを選択"
        components = [
            {
                "component": component_id,
                "slot": slot,
                "variant": (
                    variant if variant in loaded["component_map"].get(component_id, {}).get("variants", [])
                    else "primary"
                ),
            }
            for slot, component_id in layout["default_components"].items()
        ]
        resolved_slides.append({
            "slide_number": slide.get("slide_number"),
            "slide_id": slide.get("slide_id"),
            "design_resolution": {
                "role": role,
                "role_layout": layout["id"],
                "variant": variant,
                "grid_id": layout.get("grid_id"),
                "layout_contract_sha256": _contract_sha256(layout),
                "slot_frames": layout.get("slot_frames", {}),
                "selection_reason": selection_reason,
                "content_metrics": content_metrics,
                "selected_capacity": selected_capacity,
                **({"component_hint": component_hint} if component_hint else {}),
            },
            "layout_adjustments": {},
            "renderer_decision": _renderer_decision(loaded, slide.get("relationship")),
            "component_plan": components,
        })

    output_base = args.output.resolve().parent
    result = {
        "version": 2,
        "source": {
            "deck_plan": _relative_ref(deck_path, output_base),
            "deck_plan_sha256": _sha256(deck_path),
            "design_system_manifest": _relative_ref(manifest_path, output_base),
            "design_system_sha256": design_system_fingerprint(manifest_path, manifest),
            **({
                "design_direction_scout": _relative_ref(args.direction_scout.resolve(), output_base),
                "design_direction_sha256": _sha256(args.direction_scout.resolve()),
            } if args.direction_scout else {}),
        },
        "deck": {
            "composition_grammar": grammar,
            "theme": theme,
            "style_profile": context.get("style_profile"),
            "density_profile": context.get("density_profile"),
            "deck_sequence": context.get("deck_sequence"),
        },
        "slides": resolved_slides,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Design Resolutionを作成しました: {args.output}")
    return 0


def _renderer_decision(loaded: dict, relationship: object) -> dict:
    router = loaded.get("renderer_router", {})
    routes = router.get("routes", []) if isinstance(router, dict) else []
    route = next((item for item in routes if item.get("relationship") == relationship), None)
    if route is None:
        route = {"preferred": "sdpm_native", "fallback": "sdpm_native", "final": "native"}
    return {
        "selected": route.get("preferred"),
        "fallback": route.get("fallback"),
        "final_mode": route.get("final"),
        "reason": f"relationship={relationship}のRenderer Router規則による",
    }


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
