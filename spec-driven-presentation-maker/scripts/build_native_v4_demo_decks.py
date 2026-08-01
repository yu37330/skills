#!/usr/bin/env python3
"""Native Components v4統合後の実デッキ3種と検証契約を生成する。"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdpm_native_components import build_component  # noqa: E402
from sdpm_native_components.theme import load_theme  # noqa: E402


DESIGN_SYSTEM = ROOT / "assets" / "design-system"
MANIFEST = DESIGN_SYSTEM / "manifest.yaml"
OUTPUT_ROOT = ROOT / "references" / "examples" / "native-components-v4" / "demo-decks"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def relative_ref(target: Path, base: Path) -> str:
    """成果物を移動しても解決できるPOSIX形式の相対参照を返す。"""
    return os.path.relpath(target.resolve(), base.resolve()).replace(os.sep, "/")


def design_system_fingerprint() -> str:
    manifest = load_document(MANIFEST)
    entries = {"manifest": sha256(MANIFEST)}
    for group in ("registries", "themes"):
        for key, value in manifest.get(group, {}).items():
            target = resolve(MANIFEST.parent, value)
            if target.is_file():
                entries[f"{group}:{key}"] = sha256(target)
    for index, value in enumerate(manifest.get("implementation", [])):
        target = resolve(MANIFEST.parent, value)
        if target.is_file():
            entries[f"implementation:{index}:{target.name}"] = sha256(target)
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def layout_contract(layout: dict[str, Any]) -> str:
    payload = {
        "grid_id": layout.get("grid_id"),
        "locked": layout.get("locked", []),
        "adjustable": layout.get("adjustable", []),
        "content_limits": layout.get("content_limits", {}),
        "slot_frames": layout.get("slot_frames", {}),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def textbox(
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    size: float,
    color: str,
    *,
    bold: bool = False,
    align: str = "left",
    font: str = "Yu Gothic UI",
    component_id: str | None = None,
    role: str = "text",
    layout_slot: str | None = None,
    component_frame: dict[str, float] | None = None,
) -> dict[str, Any]:
    element = {
        "type": "textbox",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "text": text,
        "fontSize": size,
        "fontFamily": font,
        "fontColor": color,
        "bold": bold,
        "align": align,
        "verticalAlign": "middle",
        "marginLeft": 0,
        "marginRight": 0,
        "marginTop": 0,
        "marginBottom": 0,
    }
    if component_id:
        element.update({"componentId": component_id, "componentRole": role})
        if layout_slot:
            element["layoutSlot"] = layout_slot
        if component_frame:
            element["componentFrame"] = component_frame
    return element


def frame_to_px(frame: dict[str, float]) -> dict[str, float]:
    """13.333×7.5inch Gridを1920×1080座標へ変換する。"""
    return {
        "x": round(frame["x"] * 144, 2),
        "y": round(frame["y"] * 144, 2),
        "width": round(frame["w"] * 144, 2),
        "height": round(frame["h"] * 144, 2),
    }


def line(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1) -> dict[str, Any]:
    return {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "lineWidth": width}


SLIDES = [
    {
        "id": "answer",
        "purpose": "key_message",
        "headline_type": "decision",
        "claim_type": "interpretation",
        "headline": "価値創出には、顧客・業務・実行基盤を一体で変える",
        "component": "narrative.executive_summary",
        "layout": "summary_executive_premium",
        "relationship": "connection",
        "evidence": ["E1"],
        "content": {"headline": "顧客価値・業務設計・実行基盤を同時に変える", "items": [{"title": "顧客を選ぶ", "body": "成果が明確な重点顧客に集中"}, {"title": "業務を変える", "body": "個人利用からプロセス実装へ"}, {"title": "基盤を整える", "body": "データ・人材・統制を横断運用"}, {"title": "90日で判断", "body": "価値KPIで継続可否を決める"}]},
        "intent": "executive_summary", "pattern": "hero", "spatial": "hero", "primitive": "typography", "reading": "focal", "texture": "typographic", "motif": "typographic_focal",
    },
    {
        "id": "evidence",
        "purpose": "data_proof",
        "headline_type": "fact",
        "claim_type": "fact",
        "headline": "導入量より、価値へ接続したユースケースが不足している",
        "component": "chart.insight",
        "layout": "chart_insight_premium",
        "relationship": "comparison",
        "evidence": ["E2"],
        "content": {"items": [{"label": "個人効率化", "value": "82", "highlight": True}, {"label": "部門業務", "value": "55"}, {"label": "全社プロセス", "value": "31"}, {"label": "顧客価値", "value": "18"}], "insight": "利用は広がる一方、変革領域への組込みは限定的", "support": "数値は検証用デモ"},
        "intent": "data_insight", "pattern": "chart", "spatial": "matrix", "primitive": "axes", "reading": "scan_columns", "texture": "axis_plot", "motif": "axis_frame",
    },
    {
        "id": "diagnosis",
        "purpose": "synthesis",
        "headline_type": "insight",
        "claim_type": "interpretation",
        "headline": "部分最適・曖昧なKPI・分断運営が価値化を止める",
        "component": "narrative.findings_implications",
        "layout": "findings_implications_premium",
        "relationship": "connection",
        "evidence": ["E3"],
        "content": {"items": [{"finding": "個人利用で止まり業務責任者が不在", "implication": "業務オーナーを先に置く"}, {"finding": "時間削減だけを成果として追跡", "implication": "顧客・収益KPIへ接続"}, {"finding": "データ・IT・現場が別々に推進", "implication": "横断ガバナンスで統合"}]},
        "intent": "cause_effect", "pattern": "narrative", "spatial": "linear_vertical", "primitive": "trace_line", "reading": "top_to_bottom", "texture": "trace", "motif": "thin_straight_connectors",
    },
    {
        "id": "choice",
        "purpose": "decision_matrix",
        "headline_type": "decision",
        "claim_type": "proposal",
        "headline": "最初の90日は、価値が高く実装可能な領域へ集中する",
        "component": "strategy.portfolio_matrix",
        "layout": "portfolio_matrix_premium",
        "relationship": "comparison",
        "evidence": [],
        "content": {"x_label": "実装容易性", "y_label": "価値インパクト", "quadrant_labels": ["保留", "Quick wins", "再設計", "重点投資"], "items": [{"label": "問い合わせ解決", "x": .80, "y": .78, "highlight": True, "size": 70}, {"label": "需要予測", "x": .58, "y": .72, "size": 55}, {"label": "開発支援", "x": .42, "y": .55, "size": 48}, {"label": "議事録", "x": .82, "y": .28, "size": 36}]},
        "intent": "matrix", "pattern": "matrix", "spatial": "matrix", "primitive": "decision_gates", "reading": "spatial", "texture": "area_composition", "motif": "circular_nodes",
    },
    {
        "id": "capability",
        "purpose": "synthesis",
        "headline_type": "insight",
        "claim_type": "interpretation",
        "headline": "不足はモデルではなく、価値設計と運用能力に集中する",
        "component": "strategy.capability_map",
        "layout": "capability_map_premium",
        "relationship": "comparison",
        "evidence": ["E5"],
        "content": {"groups": [{"title": "顧客", "items": [{"label": "課題定義", "maturity": "2"}, {"label": "価値KPI", "maturity": "1"}, {"label": "検証設計", "maturity": "2"}]}, {"title": "業務", "items": [{"label": "標準化", "maturity": "2"}, {"label": "例外処理", "maturity": "1"}, {"label": "定着運用", "maturity": "2"}]}, {"title": "基盤", "items": [{"label": "データ", "maturity": "2"}, {"label": "人材", "maturity": "2"}, {"label": "統制", "maturity": "1"}]}]},
        "intent": "architecture", "pattern": "card_grid", "spatial": "stack", "primitive": "layers", "reading": "scan_columns", "texture": "table", "motif": "rounded_cards",
    },
    {
        "id": "roadmap",
        "purpose": "roadmap",
        "headline_type": "recommendation",
        "claim_type": "proposal",
        "headline": "90日で設計・実装・判定までを一巡させる",
        "component": "execution.roadmap",
        "layout": "roadmap_premium",
        "relationship": "sequence",
        "evidence": [],
        "content": {"phases": [{"title": "設計", "period": "0-30日", "items": ["業務課題", "価値KPI"]}, {"title": "実装", "period": "31-60日", "items": ["データ接続", "現場検証"]}, {"title": "定着", "period": "61-80日", "items": ["例外処理", "運用標準"]}, {"title": "判定", "period": "81-90日", "items": ["効果測定", "拡大判断"]}]},
        "intent": "roadmap", "pattern": "timeline", "spatial": "timeline", "primitive": "trace_line", "reading": "left_to_right", "texture": "form", "motif": "numbered_nodes",
    },
    {
        "id": "governance",
        "purpose": "action_plan",
        "headline_type": "recommendation",
        "claim_type": "proposal",
        "headline": "価値・実装・リスクを同じ会議体で判断する",
        "component": "execution.governance",
        "layout": "governance_premium",
        "relationship": "sequence",
        "evidence": [],
        "content": {"levels": [{"title": "Steering Committee", "detail": "隔週・投資判断"}, {"title": "Value Office", "detail": "週次・価値/KPI"}, {"title": "Delivery Teams", "detail": "日次・実装/運用"}]},
        "intent": "architecture", "pattern": "network", "spatial": "network", "primitive": "network_nodes", "reading": "top_to_bottom", "texture": "node_link", "motif": "thin_curved_connectors",
    },
    {
        "id": "decision",
        "purpose": "recommendation",
        "headline_type": "decision",
        "claim_type": "proposal",
        "headline": "本日は、対象業務・責任者・価値KPIを決める",
        "component": "narrative.recommendation_actions",
        "layout": "recommendation_actions_premium",
        "relationship": "connection",
        "evidence": [],
        "content": {"recommendation": "対象業務を一つに絞り、業務責任者と価値KPIを置いて90日PoCを開始する", "actions": [{"text": "対象業務と顧客価値を確定"}, {"text": "責任者と横断チームを任命"}, {"text": "90日後の拡大条件を合意"}], "decision": "本日の判断：90日PoCを開始するか"},
        "intent": "decision", "pattern": "hero", "spatial": "editorial_split", "primitive": "typography", "reading": "z_pattern", "texture": "kpi_editorial", "motif": "large_color_fields",
    },
]


DECKS = [
    {"id": "consulting-classic", "label": "Consulting Classic", "theme": "executive", "style": "executive_clarity", "grammar": "answer_pyramid"},
    {"id": "editorial-premium", "label": "Editorial Premium", "theme": "editorial", "style": "editorial_narrative", "grammar": "editorial"},
    {"id": "technical-data", "label": "Technical / Data", "theme": "technical", "style": "industrial_technical", "grammar": "technical_explanation"},
]


def dump_yaml(path: Path, data: Any) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def build_deck(config: dict[str, str], layouts: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> None:
    folder = OUTPUT_ROOT / config["id"]
    folder.mkdir(parents=True, exist_ok=True)
    tokens = load_theme(config["theme"])
    colors = tokens["colors"]
    font = tokens["fonts"]["ja"]

    evidence_index = {
        "version": 1,
        "claims": [
            {"id": "E1", "claim": "価値化には複数領域の一体設計が必要", "source": "統合検証用デモ", "claim_type": "interpretation"},
            {"id": "E2", "claim": "利用段階に偏りがある", "source": "統合検証用デモ", "claim_type": "fact"},
            {"id": "E3", "claim": "部分最適が価値化を阻む", "source": "統合検証用デモ", "claim_type": "interpretation"},
            {"id": "E5", "claim": "価値設計と運用能力に不足がある", "source": "統合検証用デモ", "claim_type": "interpretation"},
        ],
    }
    dump_yaml(folder / "evidence-index.yaml", evidence_index)
    (folder / "brief.md").write_text(f"# Brief\n\n{config['label']}によるNative Components v4統合検証用デモ。\n", encoding="utf-8")
    (folder / "outline.md").write_text("# Outline\n\n" + "\n".join(f"{i+1}. {slide['headline']}" for i, slide in enumerate(SLIDES)) + "\n", encoding="utf-8")
    (folder / "art-direction.html").write_text(f"<!doctype html><meta charset='utf-8'><title>{config['label']}</title><h1>{config['label']}</h1><p>Native Components v4統合検証用。</p>", encoding="utf-8")

    plan_slides = []
    for index, slide in enumerate(SLIDES, start=1):
        linkage = "evidence_to_action" if slide["claim_type"] == "proposal" else "evidence_to_implication"
        plan_slides.append({
            "slide_number": index,
            "slide_id": slide["id"],
            "slide_purpose": slide["purpose"],
            "headline_type": slide["headline_type"],
            "executive_headline": slide["headline"],
            "claim_type": slide["claim_type"],
            "evidence_ids": slide["evidence"],
            "primary_evidence": "統合検証用デモの構造化根拠" if slide["evidence"] else "本資料による提案",
            "so_what": "意思決定または次の行動へ接続する",
            "decision_relevance": "90日PoCの開始条件を具体化する",
            "evidence_linkage": linkage,
            "relationship": slide["relationship"],
            "must_show": ["検証用デモであること", "編集可能なNative要素"],
            "must_avoid": ["外部事実との混同", "因果の断定"],
            "notes_outline": f"{slide['headline']}を説明する。数値は統合検証用デモ。",
        })
    deck_plan = {
        "version": 3,
        "source": {"brief": "brief.md", "outline": "outline.md", "evidence_index": "evidence-index.yaml"},
        "deck": {
            "audience": "経営層・AI/DX推進部門",
            "decision_to_make": "90日PoCを開始するか",
            "governing_thought": "利用量ではなく価値を生む業務と運用を設計する",
            "slide_count": len(SLIDES),
            "approval_mode": "single",
            "deck_type": "executive_decision",
            "repetition_policy": "strict",
            "max_consecutive_same_role": 2,
            "key_slides": [1, 8],
        },
        "slides": plan_slides,
    }
    deck_plan_path = folder / "deck-plan.yaml"
    dump_yaml(deck_plan_path, deck_plan)

    ds_fingerprint = design_system_fingerprint()
    scout = {
        "version": 1,
        "status": "selected",
        "source": {
            "deck_plan": "deck-plan.yaml",
            "deck_plan_sha256": sha256(deck_plan_path),
            "design_system_manifest": relative_ref(MANIFEST, folder),
            "design_system_sha256": ds_fingerprint,
        },
        "representative_slide": "answer",
        "candidates": [{"id": "selected", "label": config["label"], "style_profile": config["style"]}],
        "selected": {"id": "selected", "label": config["label"], "style_profile": config["style"], "style_spec": {"theme": config["theme"]}},
        "anti_slop_required": True,
    }
    scout_path = folder / "design-direction-scout.yaml"
    dump_yaml(scout_path, scout)

    density_sequence = ["low", "high", "medium", "medium", "high", "medium", "low", "low"]
    visual_slides = []
    pptx_slides = []
    for index, slide in enumerate(SLIDES, start=1):
        role_layout = layouts[slide["layout"]]
        slot_frames_px = {
            slot: frame_to_px(frame)
            for slot, frame in role_layout.get("slot_frames", {}).items()
        }
        default_components = dict(role_layout["default_components"])
        default_components["main"] = slide["component"]
        component_plan = [{"component": component, "slot": slot, "variant": "primary"} for slot, component in default_components.items()]
        visual_slides.append({
            "slide_id": slide["id"],
            "slide_number": index,
            "intent": slide["intent"],
            "attention_order": ["headline", "visual_anchor", "implication"],
            "design_resolution": {
                "role": role_layout["role"],
                "role_layout": slide["layout"],
                "variant": "primary",
                "grid_id": role_layout["grid_id"],
                "layout_contract_sha256": layout_contract(role_layout),
                "slot_frames": role_layout.get("slot_frames", {}),
                "component_hint": slide["component"],
            },
            "component_plan": component_plan,
            "visual_strategy": {
                "pattern": f"{slide['component']}_{config['theme']}",
                "pattern_family": slide["pattern"],
                "change_level": "compose",
                "renderer": "sdpm_native",
                "integration_mode": "native",
                "emphasis": "showpiece" if index in {1, 8} else "standard",
                "density": density_sequence[index - 1],
                "rationale": "意味に適合する登録済みPremium Componentを使用するため",
                "renderer_decision": {"considered": ["sdpm_native", "baoyu_diagram"], "selected": "sdpm_native", "reason": f"relationship={slide['relationship']}のRouter規則による"},
                "visual_grammar": {
                    "spatial_model": slide["spatial"],
                    "primary_primitive": slide["primitive"],
                    "reading_path": slide["reading"],
                    "container_dependency": "high" if slide["id"] == "capability" else "low",
                    "takeaway_band": False,
                    "distinctive_feature": f"{slide['component']}固有の構図",
                },
                "motif_fingerprint": {
                    "visual_texture": slide["texture"],
                    "node_usage": "dominant" if slide["id"] == "governance" else "supporting" if slide["id"] in {"choice", "roadmap"} else "none",
                    "connector_usage": "dominant" if slide["id"] == "governance" else "supporting" if slide["id"] in {"diagnosis", "choice", "roadmap"} else "none",
                    "signature_tokens": [{"token": slide["motif"], "role": "dominant"}],
                    "dominant_motif": slide["component"],
                },
                "composition_bias": "asymmetric" if index in {1, 3, 8} else "balanced",
                "safe_area": {"title": "strict", "footer": "strict", "edge_inset_px": 48},
            },
            "constraints": {"preserve_content": True, "editable_required": True, "max_text_blocks": 8},
            "acceptance": {"visual_anchor": slide["headline"], "must_show": ["Component IDの追跡情報"], "must_avoid": ["文字切れ", "重なり"]},
            "layout_adjustments": {},
        })

        elements = [
            textbox(100, 36, 800, 26, f"{config['label'].upper()}｜統合検証用デモ", 12, colors["accent"], bold=True, font=font),
        ]
        header_component = default_components.get("header", "headline.insight")
        header_frame = slot_frames_px["header"]
        elements.append(textbox(**header_frame, text=slide["headline"], size=31, color=colors["primary"], bold=True, font=font, component_id=header_component, role="header", layout_slot="header", component_frame=header_frame))
        elements.append(line(header_frame["x"], header_frame["y"] + header_frame["height"] + 8, header_frame["x"] + header_frame["width"], header_frame["y"] + header_frame["height"] + 8, colors["line"], 1))
        for slot, component in (item for item in default_components.items() if item[0] not in {"header", "main", "footer"}):
            slot_frame = slot_frames_px[slot]
            elements.append(textbox(slot_frame["x"], slot_frame["y"], slot_frame["width"], min(22, slot_frame["height"]), slot.upper(), 12, colors["muted"], align="right", font=font, component_id=component, role=slot, layout_slot=slot, component_frame=slot_frame))
        main_frame = slot_frames_px["main"]
        result = build_component(slide["component"], main_frame, slide["content"], theme=config["theme"], variant="primary", layout_slot="main")
        elements.extend(result.elements)
        footer_component = default_components.get("footer", "evidence_footer.compact")
        footer_frame = slot_frames_px["footer"]
        elements.append(textbox(**footer_frame, text="出典：Native Components v4統合検証用デモ（外部事実ではありません）", size=12, color=colors["muted"], font=font, component_id=footer_component, role="footer", layout_slot="footer", component_frame=footer_frame))
        elements.append(textbox(1740, 1010, 80, 24, f"{index} / {len(SLIDES)}", 12, colors["muted"], bold=True, align="right", font=font))
        pptx_slides.append({"layout": "Title Only", "placeholders": {"0": ""}, "background": colors["background"], "elements": elements, "notes": plan_slides[index - 1]["notes_outline"]})

    visual_plan = {
        "version": 8,
        "source": {
            "deck_plan": "deck-plan.yaml",
            "deck_plan_sha256": sha256(deck_plan_path),
            "design_system_manifest": relative_ref(MANIFEST, folder),
            "design_system_sha256": ds_fingerprint,
            "art_direction": "art-direction.html",
            "design_direction_scout": "design-direction-scout.yaml",
            "design_direction_sha256": sha256(scout_path),
        },
        "deck": {
            "mode": "precompose",
            "preserve_slide_count": True,
            "design_system": {"composition_grammar": config["grammar"], "theme": config["theme"], "style_profile": config["style"], "density_profile": "D2", "deck_sequence": "decision_first", "anti_slop_exceptions": []},
            "rhythm": {"density_sequence": density_sequence, "max_consecutive_same_pattern": 2},
            "visual_grammar_policy": {"max_box_dominant_ratio": .6, "max_takeaway_band_ratio": .6, "min_distinct_spatial_models": 4, "min_distinct_primary_primitives": 4, "max_consecutive_same_reading_path": 2},
            "motif_policy": {"max_dominant_motif_ratio": .4, "max_node_line_dominant_ratio": .4, "min_distinct_visual_textures": 4},
            "renderer_policy": {"all_native_rationale": "登録済みNative Componentだけで編集可能に構成できるため"},
            "anti_slop_acknowledged": True,
        },
        "slides": visual_slides,
    }
    dump_yaml(folder / "visual-plan-v8.yaml", visual_plan)
    deck_json = {"template": "blank-light.pptx", "fonts": {"fullwidth": "Yu Gothic UI", "halfwidth": "Aptos"}, "defaultTextColor": colors["text"], "slides": pptx_slides}
    (folder / "deck.json").write_text(json.dumps(deck_json, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    manifest = load_document(MANIFEST)
    role_path = resolve(MANIFEST.parent, manifest["registries"]["role_layouts"])
    role_document = load_document(role_path)
    layouts = {item["id"]: item for item in role_document["role_layouts"]}
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for config in DECKS:
        build_deck(config, layouts, manifest)
    print(OUTPUT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
