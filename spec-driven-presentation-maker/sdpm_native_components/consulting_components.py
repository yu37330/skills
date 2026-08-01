from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from .models import Frame
from .primitives import circle, gradient, line, shape, textbox
from .text import fit_font_size, normalize_text
from .theme import color, display_font, font_size, shadow

Builder = Callable[[str, Frame, dict[str, Any], dict[str, Any], str], tuple[list[dict[str, Any]], list[str]]]


def _num(value: Any) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(match.group()) if match else None


def _mix(a: str, b: str, ratio: float) -> str:
    a = a.lstrip("#")
    b = b.lstrip("#")
    vals = [round(int(a[i:i+2], 16) * (1-ratio) + int(b[i:i+2], 16) * ratio) for i in (0, 2, 4)]
    return "#" + "".join(f"{v:02X}" for v in vals)


def _panel(component_id: str, frame: Frame, tokens: dict[str, Any], role: str, *, fill_key: str = "surface", line_key: str | None = None, top_rule: str | None = None, strong: bool = False) -> list[dict[str, Any]]:
    elements = [shape(frame, tokens, fill_key=fill_key, line_key=line_key, shadow=shadow(tokens, "hero" if strong else "card"), component_id=component_id, role=role)]
    if top_rule:
        elements.append(shape(Frame(frame.x, frame.y, frame.width, 6), tokens, shape_name="rectangle", fill_key=top_rule, line_key=None, component_id=component_id, role=f"{role}_rule"))
    return elements


def _fit(text: str, frame: Frame, preferred: int, minimum: int = 13, max_lines: int = 5) -> tuple[int, list[str]]:
    return fit_font_size(text, frame.width, frame.height, preferred, minimum, max_lines)


def _narrative_executive_summary(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items:
        raise ValueError("narrative.executive_summaryにはcontent.itemsが必要です")
    max_items = 5 if variant != "dense" else 6
    items = items[:max_items]
    left_ratio = .27 if variant == "alternate" else .2
    num_col, body = frame.split_h([left_ratio, 1-left_ratio], gap=28)
    rows = body.split_v([1] * len(items), gap=12)
    num_rows = num_col.split_v([1] * len(items), gap=12)
    elements: list[dict[str, Any]] = []
    for i, (item, nf, rf) in enumerate(zip(items, num_rows, rows, strict=True)):
        key = normalize_text(item.get("color_key") or ("accent" if i == 0 else "accent2"))
        elements.append(textbox(nf, f"{i+1:02d}", tokens, 24 if variant != "dense" else 19, color_key=key, bold=True, align="center", vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role=f"index_{i}"))
        elements.append(line(nf.x + nf.width * .72, nf.y + nf.height * .18, nf.x + nf.width * .72, nf.y + nf.height * .82, tokens, key, 3, component_id=component_id, role=f"index_rule_{i}"))
        title = normalize_text(item.get("title") or item.get("headline"))
        body_text = normalize_text(item.get("body") or item.get("implication"))
        title_frame, body_frame = rf.split_h([.43, .57], gap=22)
        size, warnings = _fit(title, title_frame, 20 if variant != "dense" else 17, 14, 3)
        elements.append(textbox(title_frame, title, tokens, size, bold=True, vertical_align="middle", line_spacing_pct=95, component_id=component_id, role=f"title_{i}"))
        elements.append(textbox(body_frame, body_text, tokens, 15 if variant != "dense" else 13, color_key="muted", vertical_align="middle", line_spacing_pct=105, component_id=component_id, role=f"body_{i}"))
        if i < len(items)-1:
            elements.append(line(rf.x, rf.y + rf.height + 6, rf.x + rf.width, rf.y + rf.height + 6, tokens, "line", 1, component_id=component_id, role=f"divider_{i}"))
    return elements, []


def _narrative_findings_implications(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items:
        raise ValueError("narrative.findings_implicationsにはcontent.itemsが必要です")
    rows = frame.split_v([1] * len(items), gap=14)
    elements: list[dict[str, Any]] = []
    for i, (item, row) in enumerate(zip(items, rows, strict=True)):
        finding, arrow, implication = row.split_h([.46, .08, .46], gap=14)
        key = normalize_text(item.get("color_key") or ("accent" if i == 0 else "accent2"))
        elements.append(shape(finding, tokens, fill_key="surfaceAlt", line_key=None, component_id=component_id, role=f"finding_bg_{i}"))
        elements.append(shape(Frame(finding.x, finding.y, 8, finding.height), tokens, shape_name="rectangle", fill_key=key, line_key=None, component_id=component_id, role=f"finding_rule_{i}"))
        elements.append(textbox(finding.inset(24, 12, 18, 12), normalize_text(item.get("finding")), tokens, 17 if variant != "dense" else 14, bold=True, vertical_align="middle", component_id=component_id, role=f"finding_{i}"))
        elements.append(line(arrow.x + 4, arrow.y + arrow.height/2, arrow.x + arrow.width - 4, arrow.y + arrow.height/2, tokens, key, 3, arrow_end="triangle", component_id=component_id, role=f"arrow_{i}"))
        elements.append(textbox(implication, normalize_text(item.get("implication")), tokens, 17 if variant != "dense" else 14, color_key="primary", bold=True, vertical_align="middle", line_spacing_pct=100, component_id=component_id, role=f"implication_{i}"))
    return elements, []


def _narrative_scr(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    values = [normalize_text(content.get(k)) for k in ("situation", "complication", "resolution")]
    labels = ["SITUATION", "COMPLICATION", "RESOLUTION"]
    keys = ["accent2", "warning", "accent"]
    frames = frame.split_h([.9, .9, 1.15], gap=26)
    elements: list[dict[str, Any]] = []
    for i, (f, value, label, key) in enumerate(zip(frames, values, labels, keys, strict=True)):
        if i == 2:
            elements.append(shape(f, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), 1), (1, _mix(color(tokens, "primary"), color(tokens, "accent"), .35), 1)], 0), shadow=shadow(tokens, "hero"), component_id=component_id, role="resolution_bg"))
            text_key = "white"
        else:
            elements += _panel(component_id, f, tokens, f"panel_{i}", fill_key="surface", top_rule=key)
            text_key = "text"
        inner = f.inset(26, 24, 26, 24)
        tag, body = inner.split_v([.2, .8], gap=10)
        elements.append(textbox(tag, label, tokens, 11, color_key=("accent" if i == 2 else key), bold=True, char_spacing=1.6, vertical_align="middle", component_id=component_id, role=f"label_{i}"))
        size, warnings = _fit(value, body, 22 if variant != "dense" else 18, 14, 5)
        elements.append(textbox(body, value, tokens, size, color_key=text_key, bold=True, vertical_align="middle", line_spacing_pct=100, component_id=component_id, role=f"body_{i}"))
        if i < 2:
            x1 = f.x + f.width + 5
            x2 = frames[i+1].x - 5
            y = frame.y + frame.height/2
            elements.append(line(x1, y, x2, y, tokens, keys[i+1], 3, arrow_end="triangle", component_id=component_id, role=f"transition_{i}"))
    return elements, []


def _narrative_recommendation_actions(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    recommendation = normalize_text(content.get("recommendation"))
    actions = list(content.get("actions") or [])
    left, right = frame.split_h([.62, .38], gap=34)
    elements: list[dict[str, Any]] = []
    elements.append(shape(left, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), 1), (1, _mix(color(tokens, "primary"), color(tokens, "accent2"), .35), 1)], 0), shadow=shadow(tokens, "hero"), component_id=component_id, role="recommendation_bg"))
    inner = left.inset(34, 28, 34, 28)
    elements.append(textbox(Frame(inner.x, inner.y, inner.width, 28), "RECOMMENDATION", tokens, 11, color_key="accent", bold=True, char_spacing=1.8, vertical_align="middle", component_id=component_id, role="label"))
    text_frame = inner.inset(top=42)
    size, warnings = _fit(recommendation, text_frame, 30 if variant != "dense" else 24, 17, 5)
    elements.append(textbox(text_frame, recommendation, tokens, size, color_key="white", bold=True, vertical_align="middle", line_spacing_pct=96, component_id=component_id, role="recommendation"))
    rows = right.split_v([1] * max(len(actions), 1), gap=12)
    for i, (action, row) in enumerate(zip(actions, rows, strict=False)):
        key = "accent" if i == 0 else "accent2"
        elements.append(circle(Frame(row.x, row.y + row.height/2 - 19, 38, 38), str(i+1), tokens, key, component_id, f"index_{i}", 12))
        elements.append(textbox(row.inset(left=54, right=4), normalize_text(action.get("text") if isinstance(action, dict) else action), tokens, 16 if variant != "dense" else 14, bold=True, vertical_align="middle", component_id=component_id, role=f"action_{i}"))
        if i < len(actions)-1:
            elements.append(line(row.x + 54, row.y + row.height, row.x + row.width, row.y + row.height, tokens, "line", 1, component_id=component_id, role=f"divider_{i}"))
    return elements, warnings


def _strategy_house(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    aspiration = normalize_text(content.get("aspiration"))
    choices = list(content.get("choices") or [])
    initiatives = list(content.get("initiatives") or [])
    enablers = list(content.get("enablers") or [])
    foundation = normalize_text(content.get("foundation"))
    elements: list[dict[str, Any]] = []
    roof_h = frame.height * .21
    roof = Frame(frame.x + frame.width*.18, frame.y, frame.width*.64, roof_h)
    elements.append(shape(roof, tokens, shape_name="triangle", fill_key="primary", line_key=None, text=aspiration, size=18 if variant == "dense" else 21, text_color_key="white", bold=True, margin=24, component_id=component_id, role="aspiration"))
    body_y = frame.y + roof_h * .75
    body_h = frame.height * .58
    body = Frame(frame.x + frame.width*.08, body_y, frame.width*.84, body_h)
    col_frames = body.split_h([1] * max(len(choices), 1), gap=14)
    for i, (choice, cf) in enumerate(zip(choices, col_frames, strict=False)):
        elements += _panel(component_id, cf, tokens, f"choice_{i}", fill_key="surface", top_rule=("accent" if i == 0 else "accent2"))
        title = normalize_text(choice.get("title") if isinstance(choice, dict) else choice)
        detail = normalize_text(choice.get("body") if isinstance(choice, dict) else "")
        tf, df = cf.inset(18, 20, 18, 18).split_v([.34, .66], gap=8)
        elements.append(textbox(tf, title, tokens, 16 if variant == "dense" else 18, bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"choice_title_{i}"))
        if detail:
            elements.append(textbox(df, detail, tokens, 13, color_key="muted", align="center", vertical_align="top", component_id=component_id, role=f"choice_body_{i}"))
    initiative_band = Frame(body.x, body.y + body.height*.69, body.width, body.height*.27)
    if initiatives:
        segs = initiative_band.split_h([1] * len(initiatives), gap=8)
        for i, (item, sf) in enumerate(zip(initiatives, segs, strict=True)):
            elements.append(shape(sf, tokens, fill_key="surfaceAlt", line_key=None, text=normalize_text(item), size=12 if variant == "dense" else 13, bold=True, component_id=component_id, role=f"initiative_{i}"))
    enabler_y = body_y + body_h + 12
    enabler_h = frame.height * .09
    if enablers:
        segs = Frame(frame.x + frame.width*.08, enabler_y, frame.width*.84, enabler_h).split_h([1] * len(enablers), gap=8)
        for i, (item, sf) in enumerate(zip(enablers, segs, strict=True)):
            elements.append(shape(sf, tokens, fill_key="accent2", line_key=None, text=normalize_text(item), size=12, text_color_key="white", bold=True, component_id=component_id, role=f"enabler_{i}"))
    foundation_f = Frame(frame.x, frame.y + frame.height*.91, frame.width, frame.height*.09)
    elements.append(shape(foundation_f, tokens, fill_key="primary", line_key=None, text=foundation, size=14, text_color_key="white", bold=True, component_id=component_id, role="foundation"))
    return elements, []


def _strategy_issue_tree(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    root = normalize_text(content.get("root") or "Main question")
    branches = list(content.get("branches") or [])
    if not branches:
        raise ValueError("strategy.issue_treeにはcontent.branchesが必要です")
    root_f = Frame(frame.x, frame.y + frame.height*.34, frame.width*.23, frame.height*.32)
    elements = [shape(root_f, tokens, fill_key="primary", line_key=None, text=root, size=16 if variant == "dense" else 19, text_color_key="white", bold=True, margin=18, shadow=shadow(tokens, "card"), component_id=component_id, role="root")]
    branch_zone = Frame(frame.x + frame.width*.36, frame.y, frame.width*.64, frame.height)
    branch_rows = branch_zone.split_v([1] * len(branches), gap=16)
    trunk_x = frame.x + frame.width*.3
    elements.append(line(root_f.x + root_f.width, root_f.y + root_f.height/2, trunk_x, root_f.y + root_f.height/2, tokens, "accent", 3, component_id=component_id, role="root_connector"))
    elements.append(line(trunk_x, branch_rows[0].y + branch_rows[0].height/2, trunk_x, branch_rows[-1].y + branch_rows[-1].height/2, tokens, "accent", 2, component_id=component_id, role="trunk"))
    for i, (branch, row) in enumerate(zip(branches, branch_rows, strict=True)):
        branch_title = normalize_text(branch.get("title") if isinstance(branch, dict) else branch)
        children = list(branch.get("children") or []) if isinstance(branch, dict) else []
        branch_f, children_f = row.split_h([.38, .62], gap=18)
        elements.append(line(trunk_x, row.y + row.height/2, branch_f.x, row.y + row.height/2, tokens, "accent", 2, arrow_end="triangle", component_id=component_id, role=f"branch_line_{i}"))
        elements.append(shape(branch_f, tokens, fill_key="surfaceAlt", line_key="accent", line_width=1.5, text=branch_title, size=15 if variant == "dense" else 17, bold=True, margin=14, component_id=component_id, role=f"branch_{i}"))
        if children:
            child_frames = children_f.split_h([1] * len(children), gap=10)
            for j, (child, cf) in enumerate(zip(children, child_frames, strict=True)):
                elements.append(shape(cf, tokens, fill_key="surface", line_key="line", text=normalize_text(child), size=12 if variant == "dense" else 13, bold=True, margin=10, component_id=component_id, role=f"child_{i}_{j}"))
    return elements, []


def _strategy_prioritization_matrix(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    x_label = normalize_text(content.get("x_label") or "Feasibility")
    y_label = normalize_text(content.get("y_label") or "Impact")
    plot = frame.inset(left=92, right=34, top=26, bottom=64)
    elements: list[dict[str, Any]] = []
    # quadrant shading
    halves = plot.split_h([1, 1], gap=0)
    for hi, h in enumerate(halves):
        vs = h.split_v([1, 1], gap=0)
        fills = [["surfaceAlt", "surface"], ["surface", "surfaceAlt"]][hi]
        for vi, vf in enumerate(vs):
            elements.append(shape(vf, tokens, shape_name="rectangle", fill_key=fills[vi], line_key=None, component_id=component_id, role=f"quadrant_{hi}_{vi}"))
    elements.append(line(plot.x, plot.y + plot.height, plot.x + plot.width, plot.y + plot.height, tokens, "primary", 2, arrow_end="triangle", component_id=component_id, role="x_axis"))
    elements.append(line(plot.x, plot.y + plot.height, plot.x, plot.y, tokens, "primary", 2, arrow_end="triangle", component_id=component_id, role="y_axis"))
    elements.append(line(plot.x + plot.width/2, plot.y, plot.x + plot.width/2, plot.y + plot.height, tokens, "line", 1, dashed=True, component_id=component_id, role="x_mid"))
    elements.append(line(plot.x, plot.y + plot.height/2, plot.x + plot.width, plot.y + plot.height/2, tokens, "line", 1, dashed=True, component_id=component_id, role="y_mid"))
    elements.append(textbox(Frame(plot.x, plot.y + plot.height + 24, plot.width, 30), x_label, tokens, 13, color_key="muted", bold=True, align="center", component_id=component_id, role="x_label"))
    elements.append(textbox(Frame(frame.x, plot.y, 42, plot.height), y_label, tokens, 13, color_key="muted", bold=True, align="center", vertical_align="middle", rotation=270, component_id=component_id, role="y_label"))
    labels = content.get("quadrant_labels") or ["Low priority", "Quick wins", "Strategic bets", "Major programs"]
    positions = [(plot.x+14, plot.y+plot.height/2+10), (plot.x+plot.width/2+14, plot.y+plot.height/2+10), (plot.x+14, plot.y+10), (plot.x+plot.width/2+14, plot.y+10)]
    for i, (lab, (x, y)) in enumerate(zip(labels, positions, strict=False)):
        elements.append(textbox(Frame(x, y, plot.width/2-28, 24), normalize_text(lab), tokens, 11, color_key=("accent" if i == 3 else "muted"), bold=True, component_id=component_id, role=f"quadrant_label_{i}"))
    for i, item in enumerate(items):
        x = max(0, min(1, float(item.get("x", 0.5))))
        y = max(0, min(1, float(item.get("y", 0.5))))
        size = max(30, min(70, float(item.get("size", 44))))
        px = plot.x + plot.width*x - size/2
        py = plot.y + plot.height*(1-y) - size/2
        key = normalize_text(item.get("color_key") or ("accent" if item.get("highlight") else "accent2"))
        elements.append(shape(Frame(px, py, size, size), tokens, shape_name="oval", fill_key=key, line_key=None, opacity=.9, text=normalize_text(item.get("label")), size=11 if size < 45 else 12, text_color_key="white", bold=True, component_id=component_id, role=f"item_{i}"))
    return elements, []


def _strategy_value_driver_tree(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    root = normalize_text(content.get("root"))
    drivers = list(content.get("drivers") or [])
    root_f = Frame(frame.x, frame.y + frame.height*.37, frame.width*.2, frame.height*.26)
    elements = [shape(root_f, tokens, fill_key="primary", line_key=None, text=root, size=18, text_color_key="white", bold=True, margin=16, component_id=component_id, role="root")]
    middle_zone = Frame(frame.x + frame.width*.32, frame.y, frame.width*.26, frame.height)
    right_zone = Frame(frame.x + frame.width*.68, frame.y, frame.width*.32, frame.height)
    middle_rows = middle_zone.split_v([1] * max(len(drivers), 1), gap=18)
    trunk_x = frame.x + frame.width*.26
    elements.append(line(root_f.x + root_f.width, root_f.y + root_f.height/2, trunk_x, root_f.y + root_f.height/2, tokens, "accent", 3, component_id=component_id, role="root_line"))
    if middle_rows:
        elements.append(line(trunk_x, middle_rows[0].y + middle_rows[0].height/2, trunk_x, middle_rows[-1].y + middle_rows[-1].height/2, tokens, "accent", 2, component_id=component_id, role="trunk"))
    for i, (driver, mf) in enumerate(zip(drivers, middle_rows, strict=False)):
        title = normalize_text(driver.get("title"))
        subdrivers = list(driver.get("subdrivers") or [])
        elements.append(line(trunk_x, mf.y + mf.height/2, mf.x, mf.y + mf.height/2, tokens, "accent", 2, arrow_end="triangle", component_id=component_id, role=f"driver_line_{i}"))
        elements.append(shape(mf, tokens, fill_key="surfaceAlt", line_key="accent", line_width=1.5, text=title, size=15, bold=True, margin=12, component_id=component_id, role=f"driver_{i}"))
        if subdrivers:
            sub_zone = Frame(right_zone.x, mf.y, right_zone.width, mf.height)
            sub_frames = sub_zone.split_h([1] * len(subdrivers), gap=10)
            for j, (sub, sf) in enumerate(zip(subdrivers, sub_frames, strict=True)):
                elements.append(line(mf.x + mf.width, mf.y + mf.height/2, sf.x, sf.y + sf.height/2, tokens, "line", 1.5, component_id=component_id, role=f"sub_line_{i}_{j}"))
                elements.append(shape(sf, tokens, fill_key="surface", line_key="line", text=normalize_text(sub), size=12, bold=True, margin=8, component_id=component_id, role=f"sub_{i}_{j}"))
    return elements, []


def _strategy_capability_map(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    groups = list(content.get("groups") or [])
    if not groups:
        raise ValueError("strategy.capability_mapにはcontent.groupsが必要です")
    rows = frame.split_v([1] * len(groups), gap=16)
    elements: list[dict[str, Any]] = []
    for i, (group, row) in enumerate(zip(groups, rows, strict=True)):
        label_f, items_f = row.split_h([.19, .81], gap=16)
        key = normalize_text(group.get("color_key") or ("accent" if i == 0 else "accent2"))
        elements.append(shape(label_f, tokens, fill_key=key, line_key=None, text=normalize_text(group.get("title")), size=14, text_color_key="white", bold=True, margin=12, component_id=component_id, role=f"group_{i}"))
        items = list(group.get("items") or [])
        item_frames = items_f.split_h([1] * max(len(items), 1), gap=10)
        for j, (item, itf) in enumerate(zip(items, item_frames, strict=False)):
            maturity = normalize_text(item.get("maturity") if isinstance(item, dict) else "")
            label = normalize_text(item.get("label") if isinstance(item, dict) else item)
            fill = "surfaceAlt" if maturity.lower() in {"low", "gap", "1"} else "surface"
            elements.append(shape(itf, tokens, fill_key=fill, line_key="line", text=label, size=12 if variant == "dense" else 13, bold=True, margin=10, component_id=component_id, role=f"capability_{i}_{j}"))
            if maturity:
                elements.append(textbox(Frame(itf.x + itf.width - 34, itf.y + 6, 28, 18), maturity, tokens, 10, color_key=key, bold=True, align="right", component_id=component_id, role=f"maturity_{i}_{j}"))
    return elements, []


def _execution_roadmap(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    phases = list(content.get("phases") or [])
    if not phases:
        raise ValueError("execution.roadmapにはcontent.phasesが必要です")
    phase_frames = frame.split_h([1] * len(phases), gap=14)
    elements: list[dict[str, Any]] = []
    keys = ["accent", "accent2", "warning", "success", "danger"]
    for i, (phase, pf) in enumerate(zip(phases, phase_frames, strict=True)):
        key = normalize_text(phase.get("color_key") or keys[i % len(keys)])
        head, body = pf.split_v([.22, .78], gap=10)
        elements.append(shape(head, tokens, fill_key=key, line_key=None, text=normalize_text(phase.get("title")), size=15, text_color_key="white", bold=True, component_id=component_id, role=f"phase_head_{i}"))
        elements += _panel(component_id, body, tokens, f"phase_body_{i}", fill_key="surface")
        inner = body.inset(16, 16, 16, 16)
        date_f, list_f = inner.split_v([.16, .84], gap=8)
        elements.append(textbox(date_f, normalize_text(phase.get("period")), tokens, 11, color_key=key, bold=True, char_spacing=.8, vertical_align="middle", component_id=component_id, role=f"period_{i}"))
        items = list(phase.get("items") or [])
        text = "\n".join(f"• {normalize_text(x)}" for x in items)
        elements.append(textbox(list_f, text, tokens, 13 if variant == "dense" else 14, color_key="muted", vertical_align="top", line_spacing_pct=110, component_id=component_id, role=f"items_{i}"))
        if i < len(phases)-1:
            elements.append(line(pf.x + pf.width, head.y + head.height/2, phase_frames[i+1].x, head.y + head.height/2, tokens, keys[(i+1) % len(keys)], 2.5, arrow_end="triangle", component_id=component_id, role=f"arrow_{i}"))
    return elements, []


def _execution_gantt(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    periods = list(content.get("periods") or [])
    tasks = list(content.get("tasks") or [])
    if not periods or not tasks:
        raise ValueError("execution.ganttにはcontent.periodsとcontent.tasksが必要です")
    label_w = frame.width * .26
    header_h = frame.height * .13
    label_header = Frame(frame.x, frame.y, label_w, header_h)
    timeline_header = Frame(frame.x + label_w, frame.y, frame.width - label_w, header_h)
    elements = [shape(label_header, tokens, fill_key="primary", line_key=None, text=normalize_text(content.get("label_header") or "WORKSTREAM"), size=12, text_color_key="white", bold=True, component_id=component_id, role="label_header")]
    period_frames = timeline_header.split_h([1] * len(periods), gap=0)
    for i, (period, pf) in enumerate(zip(periods, period_frames, strict=True)):
        elements.append(shape(pf, tokens, shape_name="rectangle", fill_key=("accent" if i == 0 else "surfaceAlt"), line_key="line", text=normalize_text(period), size=11, text_color_key=("white" if i == 0 else "muted"), bold=True, component_id=component_id, role=f"period_{i}"))
    body = Frame(frame.x, frame.y + header_h, frame.width, frame.height - header_h)
    rows = body.split_v([1] * len(tasks), gap=0)
    for i, (task, row) in enumerate(zip(tasks, rows, strict=True)):
        label_f = Frame(row.x, row.y, label_w, row.height)
        timeline_f = Frame(row.x + label_w, row.y, row.width - label_w, row.height)
        elements.append(shape(label_f, tokens, shape_name="rectangle", fill_key=("surfaceAlt" if i % 2 else "surface"), line_key="line", text=normalize_text(task.get("label")), size=12 if variant == "dense" else 13, bold=True, align="left", margin=12, component_id=component_id, role=f"task_{i}"))
        elements.append(shape(timeline_f, tokens, shape_name="rectangle", fill_key=("surfaceAlt" if i % 2 else "surface"), line_key="line", component_id=component_id, role=f"timeline_row_{i}"))
        for p in range(1, len(periods)):
            x = timeline_f.x + timeline_f.width * p / len(periods)
            elements.append(line(x, timeline_f.y, x, timeline_f.y + timeline_f.height, tokens, "line", 1, component_id=component_id, role=f"grid_{i}_{p}"))
        start = max(0, int(task.get("start", 0)))
        end = min(len(periods), int(task.get("end", start + 1)))
        x = timeline_f.x + timeline_f.width * start / len(periods) + 5
        w = timeline_f.width * max(end-start, 1) / len(periods) - 10
        key = normalize_text(task.get("color_key") or ("accent" if i == 0 else "accent2"))
        elements.append(shape(Frame(x, row.y + row.height*.28, max(8, w), row.height*.44), tokens, fill_key=key, line_key=None, component_id=component_id, role=f"bar_{i}"))
        if task.get("milestone") is not None:
            m = int(task.get("milestone"))
            mx = timeline_f.x + timeline_f.width * (m + .5) / len(periods)
            elements.append(shape(Frame(mx-8, row.y + row.height/2 - 8, 16, 16), tokens, shape_name="diamond", fill_key="warning", line_key=None, component_id=component_id, role=f"milestone_{i}"))
    return elements, []


def _execution_workstream_plan(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    workstreams = list(content.get("workstreams") or [])
    if not workstreams:
        raise ValueError("execution.workstream_planにはcontent.workstreamsが必要です")
    cols = frame.split_h([1] * len(workstreams), gap=16)
    elements: list[dict[str, Any]] = []
    keys = ["accent", "accent2", "warning", "success"]
    for i, (ws, col) in enumerate(zip(workstreams, cols, strict=True)):
        key = normalize_text(ws.get("color_key") or keys[i % len(keys)])
        elements += _panel(component_id, col, tokens, f"workstream_{i}", fill_key="surface", top_rule=key)
        inner = col.inset(18, 18, 18, 16)
        title_f, owner_f, body_f, status_f = inner.split_v([.18, .12, .56, .14], gap=6)
        elements.append(textbox(title_f, normalize_text(ws.get("title")), tokens, 17, bold=True, vertical_align="middle", component_id=component_id, role=f"title_{i}"))
        elements.append(textbox(owner_f, normalize_text(ws.get("owner")), tokens, 11, color_key=key, bold=True, vertical_align="middle", component_id=component_id, role=f"owner_{i}"))
        items = "\n".join(f"• {normalize_text(x)}" for x in (ws.get("items") or []))
        elements.append(textbox(body_f, items, tokens, 13 if variant == "dense" else 14, color_key="muted", vertical_align="top", line_spacing_pct=112, component_id=component_id, role=f"items_{i}"))
        elements.append(shape(status_f, tokens, fill_key="surfaceAlt", line_key=None, text=normalize_text(ws.get("status") or ""), size=11, text_color_key=key, bold=True, component_id=component_id, role=f"status_{i}"))
    return elements, []


def _execution_governance(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    levels = list(content.get("levels") or [])
    if not levels:
        raise ValueError("execution.governanceにはcontent.levelsが必要です")
    rows = frame.split_v([1] * len(levels), gap=18)
    elements: list[dict[str, Any]] = []
    widths = [.68, .76, .86, .94]
    for i, (level, row) in enumerate(zip(levels, rows, strict=True)):
        w = row.width * widths[min(i, len(widths)-1)]
        lf = Frame(row.x + (row.width-w)/2, row.y, w, row.height)
        key = normalize_text(level.get("color_key") or ("primary" if i == 0 else "accent" if i == 1 else "accent2"))
        elements.append(shape(lf, tokens, fill_key=(key if i < 2 else "surface"), line_key=(None if i < 2 else key), line_width=1.5, text=normalize_text(level.get("title")), size=16 if variant == "dense" else 18, text_color_key=("white" if i < 2 else "text"), bold=True, margin=18, shadow=shadow(tokens, "card") if i == 0 else None, component_id=component_id, role=f"level_{i}"))
        detail = normalize_text(level.get("detail"))
        if detail:
            elements.append(textbox(Frame(lf.x + lf.width*.48, lf.y, lf.width*.48, lf.height), detail, tokens, 12, color_key=("white" if i < 2 else "muted"), align="right", vertical_align="middle", component_id=component_id, role=f"detail_{i}"))
        if i < len(levels)-1:
            elements.append(line(frame.x + frame.width/2, lf.y + lf.height, frame.x + frame.width/2, rows[i+1].y, tokens, "accent", 2, arrow_end="triangle", component_id=component_id, role=f"connector_{i}"))
    return elements, []


def _execution_raci(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    roles = list(content.get("roles") or [])
    rows_data = list(content.get("rows") or [])
    if not roles or not rows_data:
        raise ValueError("execution.raciにはcontent.rolesとcontent.rowsが必要です")
    label_w = frame.width * .3
    header_h = frame.height * .16
    elements: list[dict[str, Any]] = []
    elements.append(shape(Frame(frame.x, frame.y, label_w, header_h), tokens, shape_name="rectangle", fill_key="primary", line_key=None, text=normalize_text(content.get("label_header") or "ACTIVITY"), size=12, text_color_key="white", bold=True, component_id=component_id, role="header_label"))
    role_frames = Frame(frame.x + label_w, frame.y, frame.width-label_w, header_h).split_h([1] * len(roles), gap=0)
    for i, (role, rf) in enumerate(zip(roles, role_frames, strict=True)):
        elements.append(shape(rf, tokens, shape_name="rectangle", fill_key=("accent" if i == 0 else "surfaceAlt"), line_key="line", text=normalize_text(role), size=11, text_color_key=("white" if i == 0 else "text"), bold=True, component_id=component_id, role=f"role_{i}"))
    rows = Frame(frame.x, frame.y+header_h, frame.width, frame.height-header_h).split_v([1] * len(rows_data), gap=0)
    key_map = {"R": "accent", "A": "primary", "C": "warning", "I": "muted"}
    for i, (row, data) in enumerate(zip(rows, rows_data, strict=True)):
        elements.append(shape(Frame(row.x, row.y, label_w, row.height), tokens, shape_name="rectangle", fill_key=("surfaceAlt" if i%2 else "surface"), line_key="line", text=normalize_text(data.get("activity")), size=12, bold=True, align="left", margin=12, component_id=component_id, role=f"activity_{i}"))
        vals = list(data.get("values") or [])
        cells = Frame(row.x+label_w, row.y, row.width-label_w, row.height).split_h([1] * len(roles), gap=0)
        for j, cf in enumerate(cells):
            val = normalize_text(vals[j] if j < len(vals) else "")
            elements.append(shape(cf, tokens, shape_name="rectangle", fill_key=("surfaceAlt" if i%2 else "surface"), line_key="line", component_id=component_id, role=f"cell_{i}_{j}"))
            if val:
                key = key_map.get(val.upper(), "accent2")
                elements.append(circle(Frame(cf.x+cf.width/2-18, cf.y+cf.height/2-18, 36, 36), val.upper(), tokens, key, component_id, f"raci_{i}_{j}", 12))
    return elements, []


def _execution_initiative_card(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    elements = _panel(component_id, frame, tokens, "card", fill_key="surface", top_rule="accent", strong=True)
    inner = frame.inset(26, 22, 26, 22)
    title_f, owner_f, body_f, metrics_f = inner.split_v([.2, .1, .47, .23], gap=8)
    elements.append(textbox(title_f, normalize_text(content.get("title")), tokens, 20 if variant != "dense" else 17, bold=True, vertical_align="middle", component_id=component_id, role="title"))
    elements.append(textbox(owner_f, normalize_text(content.get("owner")), tokens, 11, color_key="accent", bold=True, char_spacing=.6, vertical_align="middle", component_id=component_id, role="owner"))
    body = normalize_text(content.get("description"))
    elements.append(textbox(body_f, body, tokens, 14 if variant != "dense" else 12, color_key="muted", vertical_align="top", line_spacing_pct=110, component_id=component_id, role="description"))
    metrics = list(content.get("metrics") or [])
    if metrics:
        cells = metrics_f.split_h([1] * len(metrics), gap=10)
        for i, (m, cf) in enumerate(zip(metrics, cells, strict=True)):
            elements.append(shape(cf, tokens, fill_key="surfaceAlt", line_key=None, component_id=component_id, role=f"metric_bg_{i}"))
            vf, lf = cf.inset(10, 8, 10, 8).split_v([.58, .42], gap=2)
            elements.append(textbox(vf, normalize_text(m.get("value")), tokens, 18, color_key=("accent" if i == 0 else "accent2"), bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"metric_value_{i}"))
            elements.append(textbox(lf, normalize_text(m.get("label")), tokens, 10, color_key="muted", bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"metric_label_{i}"))
    return elements, []


def _execution_kpi_cascade(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    top = content.get("top") or {}
    levels = list(content.get("levels") or [])
    elements: list[dict[str, Any]] = []
    top_f = Frame(frame.x + frame.width*.28, frame.y, frame.width*.44, frame.height*.2)
    elements.append(shape(top_f, tokens, fill_key="primary", line_key=None, text=f"{normalize_text(top.get('value'))}\n{normalize_text(top.get('label'))}", size=18, text_color_key="white", bold=True, margin=14, shadow=shadow(tokens, "hero"), component_id=component_id, role="top"))
    current_y = top_f.y + top_f.height
    for li, level in enumerate(levels):
        items = list(level.get("items") or [])
        band_h = (frame.height - top_f.height - 20) / max(len(levels), 1) - 12
        band = Frame(frame.x, current_y + 18, frame.width, band_h)
        cells = band.split_h([1] * max(len(items), 1), gap=14)
        for i, (item, cf) in enumerate(zip(items, cells, strict=False)):
            key = normalize_text(item.get("color_key") or ("accent" if li == 0 else "accent2"))
            elements.append(shape(cf, tokens, fill_key="surface", line_key=key, line_width=1.5, text=f"{normalize_text(item.get('value'))}\n{normalize_text(item.get('label'))}", size=14 if variant == "dense" else 16, bold=True, margin=12, component_id=component_id, role=f"item_{li}_{i}"))
            parent_cx = top_f.x + top_f.width/2 if li == 0 else frame.x + frame.width*(i+.5)/max(len(items),1)
            elements.append(line(parent_cx, current_y, cf.x+cf.width/2, cf.y, tokens, "line", 1.5, component_id=component_id, role=f"connector_{li}_{i}"))
        current_y = band.y + band.height
    return elements, []


def _process_swimlane(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    lanes = list(content.get("lanes") or [])
    stages = list(content.get("stages") or [])
    if not lanes or not stages:
        raise ValueError("process.swimlaneにはcontent.lanesとcontent.stagesが必要です")
    label_w = frame.width * .18
    header_h = frame.height * .14
    elements: list[dict[str, Any]] = []
    elements.append(shape(Frame(frame.x, frame.y, label_w, header_h), tokens, shape_name="rectangle", fill_key="primary", line_key=None, text="OWNER", size=11, text_color_key="white", bold=True, component_id=component_id, role="owner_header"))
    stage_frames = Frame(frame.x+label_w, frame.y, frame.width-label_w, header_h).split_h([1] * len(stages), gap=0)
    for i, (stage, sf) in enumerate(zip(stages, stage_frames, strict=True)):
        elements.append(shape(sf, tokens, shape_name="rectangle", fill_key=("accent" if i == 0 else "surfaceAlt"), line_key="line", text=normalize_text(stage), size=11, text_color_key=("white" if i == 0 else "text"), bold=True, component_id=component_id, role=f"stage_{i}"))
    lane_rows = Frame(frame.x, frame.y+header_h, frame.width, frame.height-header_h).split_v([1] * len(lanes), gap=0)
    for li, (lane, row) in enumerate(zip(lanes, lane_rows, strict=True)):
        elements.append(shape(Frame(row.x, row.y, label_w, row.height), tokens, shape_name="rectangle", fill_key=("surfaceAlt" if li%2 else "surface"), line_key="line", text=normalize_text(lane.get("name")), size=12, bold=True, align="left", margin=12, component_id=component_id, role=f"lane_{li}"))
        grid = Frame(row.x+label_w, row.y, row.width-label_w, row.height)
        cells = grid.split_h([1] * len(stages), gap=0)
        for si, cf in enumerate(cells):
            elements.append(shape(cf, tokens, shape_name="rectangle", fill_key=("surfaceAlt" if li%2 else "surface"), line_key="line", component_id=component_id, role=f"cell_{li}_{si}"))
        for ai, activity in enumerate(lane.get("activities") or []):
            start = max(0, int(activity.get("start", 0)))
            end = min(len(stages), int(activity.get("end", start+1)))
            x = grid.x + grid.width*start/len(stages) + 6
            w = grid.width*max(end-start,1)/len(stages) - 12
            key = normalize_text(activity.get("color_key") or ("accent" if li == 0 else "accent2"))
            af = Frame(x, row.y+row.height*.22, max(10,w), row.height*.56)
            elements.append(shape(af, tokens, fill_key=key, line_key=None, text=normalize_text(activity.get("label")), size=11 if variant == "dense" else 12, text_color_key="white", bold=True, margin=8, component_id=component_id, role=f"activity_{li}_{ai}"))
    return elements, []


def _process_customer_journey(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    stages = list(content.get("stages") or [])
    if not stages:
        raise ValueError("process.customer_journeyにはcontent.stagesが必要です")
    header_h = frame.height*.18
    head_frames = Frame(frame.x, frame.y, frame.width, header_h).split_h([1]*len(stages), gap=10)
    elements: list[dict[str, Any]] = []
    for i, (stage, hf) in enumerate(zip(stages, head_frames, strict=True)):
        key = normalize_text(stage.get("color_key") or ("accent" if i == 0 else "accent2"))
        elements.append(shape(hf, tokens, fill_key=(key if i == 0 else "surfaceAlt"), line_key=(None if i == 0 else key), line_width=1.5, text=normalize_text(stage.get("title")), size=14, text_color_key=("white" if i == 0 else "text"), bold=True, component_id=component_id, role=f"stage_{i}"))
    body = Frame(frame.x, frame.y+header_h+12, frame.width, frame.height-header_h-12)
    row_labels = ["ACTION", "NEED", "PAIN", "MOMENT"]
    label_w = body.width*.13
    row_h = body.height/4
    for ri, label in enumerate(row_labels):
        y = body.y + row_h*ri
        elements.append(textbox(Frame(body.x, y, label_w-10, row_h), label, tokens, 10, color_key=("danger" if label == "PAIN" else "muted"), bold=True, align="right", vertical_align="middle", char_spacing=1, component_id=component_id, role=f"row_label_{ri}"))
        cells = Frame(body.x+label_w, y, body.width-label_w, row_h).split_h([1]*len(stages), gap=10)
        for i, (stage, cf) in enumerate(zip(stages, cells, strict=True)):
            key_map = {"ACTION": "action", "NEED": "need", "PAIN": "pain", "MOMENT": "moment"}
            text = normalize_text(stage.get(key_map[label]))
            fill = "surfaceAlt" if ri%2 else "surface"
            elements.append(shape(cf, tokens, fill_key=fill, line_key=None, text=text, size=11 if variant == "dense" else 12, text_color_key=("danger" if label == "PAIN" else "text"), bold=(label in {"PAIN", "MOMENT"}), margin=10, component_id=component_id, role=f"cell_{ri}_{i}"))
    return elements, []


def _chart_horizontal_bar(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    maxv = float(content.get("max") or max([_num(i.get("value")) or 0 for i in items] or [1]))
    rows = frame.split_v([1]*len(items), gap=8)
    elements: list[dict[str, Any]] = []
    for i, (item, row) in enumerate(zip(items, rows, strict=True)):
        label_f, plot_f, value_f = row.split_h([.31, .57, .12], gap=10)
        value = _num(item.get("value")) or 0
        raw = normalize_text(item.get("value"))
        label = normalize_text(item.get("label"))
        key = normalize_text(item.get("color_key") or ("accent" if item.get("highlight") or i == 0 else "accent2"))
        elements.append(textbox(label_f, label, tokens, 13 if variant == "dense" else 14, bold=True, vertical_align="middle", component_id=component_id, role=f"label_{i}"))
        y = plot_f.y + plot_f.height*.32
        elements.append(line(plot_f.x, y+plot_f.height*.18, plot_f.x+plot_f.width, y+plot_f.height*.18, tokens, "line", 1, component_id=component_id, role=f"baseline_{i}"))
        width = plot_f.width * min(max(value/maxv, 0), 1)
        elements.append(shape(Frame(plot_f.x, y, max(5,width), plot_f.height*.36), tokens, shape_name="rectangle", fill_key=key, line_key=None, component_id=component_id, role=f"bar_{i}"))
        elements.append(textbox(value_f, raw, tokens, 14, color_key=key, bold=True, align="right", vertical_align="middle", component_id=component_id, role=f"value_{i}"))
    return elements, []


def _chart_line_forecast(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    actual = list(content.get("actual") or [])
    forecast = list(content.get("forecast") or [])
    if not actual:
        raise ValueError("chart.line_forecastにはcontent.actualが必要です")
    all_points = actual + forecast
    vals = [_num(p.get("value")) or 0 for p in all_points]
    lo, hi = min(vals), max(vals)
    rng = max(hi-lo, 1)
    plot = frame.inset(left=54, right=30, top=28, bottom=54)
    elements: list[dict[str, Any]] = []
    # horizontal guides
    for g in range(4):
        y = plot.y + plot.height*g/3
        elements.append(line(plot.x, y, plot.x+plot.width, y, tokens, "line", 1, component_id=component_id, role=f"grid_{g}"))
    def point(idx: int, value: float, total: int) -> tuple[float,float]:
        x = plot.x + plot.width*idx/max(total-1,1)
        y = plot.y + plot.height*(1-(value-lo)/rng)
        return x,y
    total = len(all_points)
    prev = None
    for i,p in enumerate(actual):
        x,y = point(i,_num(p.get("value")) or 0,total)
        if prev:
            elements.append(line(prev[0],prev[1],x,y,tokens,"accent",3,component_id=component_id,role=f"actual_line_{i}"))
        elements.append(circle(Frame(x-6,y-6,12,12),"",tokens,"accent",component_id,f"actual_point_{i}",6))
        prev=(x,y)
    if forecast:
        start_idx = len(actual)-1
        prev = point(start_idx, _num(actual[-1].get("value")) or 0, total)
        for j,p in enumerate(forecast, start=1):
            idx=start_idx+j; x,y=point(idx,_num(p.get("value")) or 0,total)
            elements.append(line(prev[0],prev[1],x,y,tokens,"warning",3,dashed=True,component_id=component_id,role=f"forecast_line_{j}"))
            elements.append(circle(Frame(x-6,y-6,12,12),"",tokens,"warning",component_id,f"forecast_point_{j}",6))
            prev=(x,y)
        split_x = point(start_idx,_num(actual[-1].get("value")) or 0,total)[0]
        elements.append(line(split_x,plot.y,split_x,plot.y+plot.height,tokens,"warning",1,dashed=True,component_id=component_id,role="forecast_split"))
        elements.append(textbox(Frame(split_x+8,plot.y,120,24),"FORECAST",tokens,10,color_key="warning",bold=True,char_spacing=1.2,component_id=component_id,role="forecast_label"))
    labels = all_points
    for i,p in enumerate(labels):
        if i in {0,len(actual)-1,total-1} or variant=="dense":
            x,_=point(i,_num(p.get("value")) or 0,total)
            elements.append(textbox(Frame(x-46,plot.y+plot.height+16,92,26),normalize_text(p.get("label")),tokens,10,color_key="muted",bold=True,align="center",component_id=component_id,role=f"x_label_{i}"))
    if content.get("callout"):
        elements.append(textbox(Frame(plot.x+plot.width*.6,plot.y+10,plot.width*.36,70),normalize_text(content.get("callout")),tokens,14,color_key="primary",bold=True,align="right",vertical_align="middle",component_id=component_id,role="callout"))
    return elements, []


def _chart_heatmap(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows = list(content.get("rows") or [])
    cols = list(content.get("columns") or [])
    values = list(content.get("values") or [])
    if not rows or not cols:
        raise ValueError("chart.heatmapにはcontent.rowsとcontent.columnsが必要です")
    label_w = frame.width*.23
    header_h = frame.height*.16
    elements: list[dict[str, Any]] = []
    col_frames = Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*len(cols),gap=4)
    for i,(col,cf) in enumerate(zip(cols,col_frames,strict=True)):
        elements.append(textbox(cf,normalize_text(col),tokens,11,color_key="muted",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"col_{i}"))
    row_frames = Frame(frame.x,frame.y+header_h,frame.width,frame.height-header_h).split_v([1]*len(rows),gap=4)
    palette=["surfaceAlt","accent2","accent","primary"]
    for r,(row,rf) in enumerate(zip(rows,row_frames,strict=True)):
        elements.append(textbox(Frame(rf.x,rf.y,label_w-10,rf.height),normalize_text(row),tokens,12,bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"row_{r}"))
        cells=Frame(rf.x+label_w,rf.y,rf.width-label_w,rf.height).split_h([1]*len(cols),gap=4)
        for c,cf in enumerate(cells):
            val = values[r][c] if r < len(values) and c < len(values[r]) else 0
            idx=max(0,min(3,int(round(float(val)))))
            key=palette[idx]
            elements.append(shape(cf,tokens,fill_key=key,line_key=None,text=normalize_text(val),size=11,text_color_key=("white" if idx>=2 else "text"),bold=True,component_id=component_id,role=f"cell_{r}_{c}"))
    return elements, []


def _chart_scatter_bubble(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or [])
    if not items:
        raise ValueError("chart.scatter_bubbleにはcontent.itemsが必要です")
    x_label=normalize_text(content.get("x_label") or "X")
    y_label=normalize_text(content.get("y_label") or "Y")
    plot=frame.inset(left=70,right=30,top=20,bottom=54)
    elements=[line(plot.x,plot.y+plot.height,plot.x+plot.width,plot.y+plot.height,tokens,"primary",2,arrow_end="triangle",component_id=component_id,role="x_axis"),line(plot.x,plot.y+plot.height,plot.x,plot.y,tokens,"primary",2,arrow_end="triangle",component_id=component_id,role="y_axis")]
    elements.append(textbox(Frame(plot.x,plot.y+plot.height+22,plot.width,26),x_label,tokens,12,color_key="muted",bold=True,align="center",component_id=component_id,role="x_label"))
    elements.append(textbox(Frame(frame.x,plot.y,34,plot.height),y_label,tokens,12,color_key="muted",bold=True,align="center",vertical_align="middle",rotation=270,component_id=component_id,role="y_label"))
    for i,item in enumerate(items):
        x=max(0,min(1,float(item.get("x",.5)))); y=max(0,min(1,float(item.get("y",.5)))); size=max(24,min(86,float(item.get("size",42))))
        px=plot.x+plot.width*x-size/2; py=plot.y+plot.height*(1-y)-size/2; key=normalize_text(item.get("color_key") or ("accent" if item.get("highlight") else "accent2"))
        elements.append(shape(Frame(px,py,size,size),tokens,shape_name="oval",fill_key=key,line_key=None,opacity=.82,text=normalize_text(item.get("label")),size=10 if size<42 else 11,text_color_key="white",bold=True,component_id=component_id,role=f"bubble_{i}"))
    return elements,[]


def _chart_bullet(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or [])
    if not items:
        raise ValueError("chart.bulletにはcontent.itemsが必要です")
    rows=frame.split_v([1]*len(items),gap=14); elements=[]
    for i,(item,row) in enumerate(zip(items,rows,strict=True)):
        maxv=float(item.get("max") or 100); actual=float(_num(item.get("actual")) or 0); target=float(_num(item.get("target")) or 0)
        label_f,plot_f,value_f=row.split_h([.28,.58,.14],gap=12)
        elements.append(textbox(label_f,normalize_text(item.get("label")),tokens,13,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
        track=plot_f.inset(top=plot_f.height*.28,bottom=plot_f.height*.28)
        bands=[(.5,"surfaceAlt"),(.3,"line"),(.2,"accent2")]; x=track.x
        for bi,(ratio,key) in enumerate(bands):
            w=track.width*ratio; elements.append(shape(Frame(x,track.y,w,track.height),tokens,shape_name="rectangle",fill_key=key,line_key=None,opacity=.35 if bi<2 else .22,component_id=component_id,role=f"band_{i}_{bi}")); x+=w
        actual_w=track.width*min(actual/maxv,1); elements.append(shape(Frame(track.x,track.y+track.height*.25,max(5,actual_w),track.height*.5),tokens,shape_name="rectangle",fill_key="primary",line_key=None,component_id=component_id,role=f"actual_{i}"))
        tx=track.x+track.width*min(target/maxv,1); elements.append(line(tx,track.y-4,tx,track.y+track.height+4,tokens,"warning",3,component_id=component_id,role=f"target_{i}"))
        elements.append(textbox(value_f,normalize_text(item.get("actual")),tokens,14,color_key="primary",bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"value_{i}"))
    return elements,[]


def _chart_sensitivity_matrix(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows=list(content.get("rows") or []); cols=list(content.get("columns") or []); values=list(content.get("values") or [])
    if not rows or not cols:
        raise ValueError("chart.sensitivity_matrixにはcontent.rowsとcontent.columnsが必要です")
    label_w=frame.width*.25; header_h=frame.height*.17; elements=[]
    col_frames=Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*len(cols),gap=2)
    for i,(col,cf) in enumerate(zip(cols,col_frames,strict=True)):
        elements.append(shape(cf,tokens,shape_name="rectangle",fill_key="primary",line_key="white",line_width=1,text=normalize_text(col),size=11,text_color_key="white",bold=True,component_id=component_id,role=f"col_{i}"))
    row_frames=Frame(frame.x,frame.y+header_h,frame.width,frame.height-header_h).split_v([1]*len(rows),gap=2)
    for r,(row,rf) in enumerate(zip(rows,row_frames,strict=True)):
        elements.append(shape(Frame(rf.x,rf.y,label_w,rf.height),tokens,shape_name="rectangle",fill_key="surfaceAlt",line_key="white",line_width=1,text=normalize_text(row),size=11,bold=True,align="right",margin=12,component_id=component_id,role=f"row_{r}"))
        cells=Frame(rf.x+label_w,rf.y,rf.width-label_w,rf.height).split_h([1]*len(cols),gap=2)
        for c,cf in enumerate(cells):
            val=float(values[r][c]) if r<len(values) and c<len(values[r]) else 0
            key="danger" if val<0 else "success" if val>0 else "surfaceAlt"
            opacity=min(.85,max(.18,abs(val)/max(1,max(abs(float(v)) for rowv in values for v in rowv)))) if values else .2
            elements.append(shape(cf,tokens,shape_name="rectangle",fill_key=key,line_key="white",line_width=1,opacity=opacity,text=f"{val:+.1f}",size=11,text_color_key=("white" if abs(val)>.4 else "text"),bold=True,component_id=component_id,role=f"cell_{r}_{c}"))
    return elements,[]


CONSULTING_BUILDERS: dict[str, Builder] = {
    "narrative.executive_summary": _narrative_executive_summary,
    "narrative.findings_implications": _narrative_findings_implications,
    "narrative.scr": _narrative_scr,
    "narrative.recommendation_actions": _narrative_recommendation_actions,
    "strategy.house": _strategy_house,
    "strategy.issue_tree": _strategy_issue_tree,
    "strategy.prioritization_matrix": _strategy_prioritization_matrix,
    "strategy.value_driver_tree": _strategy_value_driver_tree,
    "strategy.capability_map": _strategy_capability_map,
    "execution.roadmap": _execution_roadmap,
    "execution.gantt": _execution_gantt,
    "execution.workstream_plan": _execution_workstream_plan,
    "execution.governance": _execution_governance,
    "execution.raci": _execution_raci,
    "execution.initiative_card": _execution_initiative_card,
    "execution.kpi_cascade": _execution_kpi_cascade,
    "process.swimlane": _process_swimlane,
    "process.customer_journey": _process_customer_journey,
    "chart.horizontal_bar": _chart_horizontal_bar,
    "chart.line_forecast": _chart_line_forecast,
    "chart.heatmap": _chart_heatmap,
    "chart.scatter_bubble": _chart_scatter_bubble,
    "chart.bullet": _chart_bullet,
    "chart.sensitivity_matrix": _chart_sensitivity_matrix,
}
