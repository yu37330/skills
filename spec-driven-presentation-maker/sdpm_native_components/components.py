from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from .models import Frame
from .primitives import circle, gradient, line, pill, shape, textbox
from .text import fit_font_size, join_nonempty, normalize_text
from .theme import color, display_font, font_size, shadow

Builder = Callable[[str, Frame, dict[str, Any], dict[str, Any], str], tuple[list[dict[str, Any]], list[str]]]


def _mix(a: str, b: str, ratio: float) -> str:
    a = a.lstrip("#"); b = b.lstrip("#")
    vals = [round(int(a[i:i+2], 16) * (1-ratio) + int(b[i:i+2], 16) * ratio) for i in (0, 2, 4)]
    return "#" + "".join(f"{v:02X}" for v in vals)


def _num(value: Any) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(m.group()) if m else None



def _metric_safe_size(value: str, width: float, preferred: int, minimum: int = 28) -> int:
    clean = value.replace("\n", "")
    weighted = sum(1.0 if ord(ch) > 255 else 0.92 for ch in clean) or 1.0
    width_cap = int(width / (weighted * 1.30))
    return max(minimum, min(preferred, width_cap))


def _soft_panel(component_id: str, frame: Frame, tokens: dict[str, Any], role: str, *, fill_key: str = "surface", top_rule: str | None = None, strong: bool = False) -> list[dict[str, Any]]:
    elements = [shape(frame, tokens, fill_key=fill_key, line_key=None, shadow=shadow(tokens, "hero" if strong else "card"), component_id=component_id, role=role)]
    if top_rule:
        elements.append(shape(Frame(frame.x, frame.y, frame.width, 7 if strong else 5), tokens, shape_name="rectangle", fill_key=top_rule, line_key=None, component_id=component_id, role=f"{role}_rule"))
    return elements


def _headline(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    text = normalize_text(content.get("text") or content.get("headline"))
    kind = component_id.split(".")[1]
    size, warnings = fit_font_size(text, frame.width, frame.height, font_size(tokens, "slideTitle", 40) - (4 if variant == "dense" else 0), 22, 3)
    elements: list[dict[str, Any]] = []
    if kind == "fact":
        kicker = normalize_text(content.get("kicker") or "FACT")
        kf = Frame(frame.x, frame.y, min(frame.width * .25, 230), 28)
        elements.append(textbox(kf, kicker.upper(), tokens, 12, color_key="accent2", bold=True, vertical_align="middle", char_spacing=1.8, component_id=component_id, role="kicker"))
        elements.append(line(frame.x, frame.y + 36, frame.x + frame.width, frame.y + 36, tokens, "line", 1, component_id=component_id, role="rule"))
        tf = Frame(frame.x, frame.y + 52, frame.width, max(1, frame.height - 52))
        elements.append(textbox(tf, text, tokens, size, bold=True, vertical_align="middle", line_spacing_pct=92, component_id=component_id, role="headline"))
    elif kind == "insight":
        band_w = max(12, min(20, frame.width * .018))
        elements.append(shape(Frame(frame.x, frame.y, band_w, frame.height), tokens, shape_name="rectangle", fill_key="accent", line_key=None, component_id=component_id, role="accent"))
        tf = frame.inset(left=band_w + 30)
        elements.append(textbox(tf, text, tokens, size + (3 if variant == "primary" else 0), bold=True, vertical_align="middle", line_spacing_pct=90, component_id=component_id, role="headline"))
    elif kind == "recommendation":
        num = normalize_text(content.get("number") or "01")
        nf, tf = frame.split_h([.17, .83], gap=24)
        elements.append(textbox(nf, num, tokens, min(size + 22, 64), color_key="warning", bold=True, align="center", vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role="number"))
        elements.append(line(tf.x, tf.y + 8, tf.x, tf.y + tf.height - 8, tokens, "warning", 4, component_id=component_id, role="rule"))
        elements.append(textbox(tf.inset(left=28), text, tokens, size, bold=True, vertical_align="middle", line_spacing_pct=92, component_id=component_id, role="headline"))
    else:  # decision
        bg = gradient([(0, color(tokens, "primary"), 1), (1, _mix(color(tokens, "primary"), color(tokens, "accent2"), .4), 1)], 0)
        elements.append(shape(frame, tokens, fill_key="primary", line_key=None, gradient=bg, shadow=shadow(tokens, "hero"), component_id=component_id, role="background"))
        inner = frame.inset(32, 18, 32, 18)
        kf, tf = inner.split_v([.22, .78], gap=6)
        elements.append(textbox(kf, normalize_text(content.get("kicker") or "DECISION"), tokens, 12, font_color=_mix(color(tokens, "white"), color(tokens, "accent"), .3), bold=True, char_spacing=1.6, vertical_align="middle", component_id=component_id, role="kicker"))
        elements.append(textbox(tf, text, tokens, size, color_key="white", bold=True, vertical_align="middle", line_spacing_pct=90, component_id=component_id, role="headline"))
    return elements, warnings


def _label(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    kind = component_id.split(".")[1]
    defaults = {"fact_tag": ("事実", "accent2"), "interpretation_tag": ("解釈", "accent"), "proposal_tag": ("提案", "warning")}
    if kind == "section":
        text = normalize_text(content.get("text") or "SECTION")
        elements = [textbox(frame, text.upper(), tokens, 13, color_key="accent", bold=True, vertical_align="middle", char_spacing=2.2, component_id=component_id, role="label")]
        elements.append(line(frame.x, frame.y + frame.height - 2, frame.x + min(frame.width, 110), frame.y + frame.height - 2, tokens, "accent", 3, component_id=component_id, role="rule"))
        return elements, []
    text_default, key = defaults[kind]
    text = normalize_text(content.get("text") or text_default)
    mark = Frame(frame.x, frame.y + frame.height * .22, 8, frame.height * .56)
    elements = [shape(mark, tokens, shape_name="rectangle", fill_key=key, line_key=None, component_id=component_id, role="mark")]
    elements.append(textbox(frame.inset(left=18), text, tokens, 13, color_key=key, bold=True, vertical_align="middle", char_spacing=.6, component_id=component_id, role="tag"))
    return elements, []


def _metric_big(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    value = normalize_text(content.get("value") or "—")
    label = normalize_text(content.get("label"))
    note = normalize_text(content.get("note"))
    elements: list[dict[str, Any]] = []
    if variant == "alternate":
        vf, df = frame.split_h([.58, .42], gap=34)
        elements.append(shape(Frame(vf.x, vf.y + vf.height * .12, vf.width * .84, vf.height * .76), tokens, fill_key="surfaceAlt", line_key=None, opacity=.75, component_id=component_id, role="wash"))
        preferred = _metric_safe_size(value, vf.width, font_size(tokens, "hero", 76) + 4, 34)
        size, warnings = fit_font_size(value, vf.width, vf.height, preferred, 34, 2)
        elements.append(textbox(vf.inset(left=12), value, tokens, size, color_key="accent", bold=True, vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role="value"))
        elements.append(line(df.x, df.y + 20, df.x, df.y + df.height - 20, tokens, "line", 1.5, component_id=component_id, role="divider"))
        body = join_nonempty([label, note], "\n")
        elements.append(textbox(df.inset(left=26), body, tokens, font_size(tokens, "lead", 26), bold=True, vertical_align="middle", line_spacing_pct=105, component_id=component_id, role="detail"))
        return elements, warnings
    rows = frame.split_v([.7, .19, .11] if note else [.76, .24], gap=4)
    preferred = font_size(tokens, "hero", 76) + (8 if variant == "primary" else -20)
    preferred = _metric_safe_size(value, rows[0].width, preferred, 30)
    size, warnings = fit_font_size(value, rows[0].width, rows[0].height, preferred, 30, 2)
    align = "left" if variant == "primary" else "center"
    elements.append(textbox(rows[0], value, tokens, size, color_key="accent", bold=True, align=align, vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role="value"))
    elements.append(textbox(rows[1], label, tokens, font_size(tokens, "body", 18) + 2, bold=True, align=align, vertical_align="middle", component_id=component_id, role="label"))
    if note:
        elements.append(textbox(rows[2], note, tokens, font_size(tokens, "caption", 13), color_key="muted", align=align, vertical_align="middle", component_id=component_id, role="note"))
    return elements, warnings


def _metric_delta(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    before, after = normalize_text(content.get("before")), normalize_text(content.get("after"))
    delta, label = normalize_text(content.get("delta")), normalize_text(content.get("label"))
    elements: list[dict[str, Any]] = []
    top, bottom = frame.split_v([.72, .28], gap=8)
    left, mid, right = top.split_h([.9, .32, 1.15], gap=14)
    size = font_size(tokens, "metric", 62) + (6 if variant == "primary" else -6)
    size = min(_metric_safe_size(before, left.width, size, 30), _metric_safe_size(after, right.width, size, 30))
    elements.append(textbox(left, before, tokens, size, color_key="muted", bold=True, align="right", vertical_align="middle", component_id=component_id, role="before"))
    elements.append(line(mid.x + 8, mid.y + mid.height / 2, mid.x + mid.width - 8, mid.y + mid.height / 2, tokens, "accent", 5, arrow_end="triangle", component_id=component_id, role="arrow"))
    elements.append(textbox(right, after, tokens, size + 8, color_key="accent", bold=True, align="left", vertical_align="middle", component_id=component_id, role="after"))
    badge = bottom.inset(left=bottom.width * .28, right=bottom.width * .28, top=3, bottom=3)
    elements.append(shape(badge, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), 1), (1, color(tokens, "accent2"), 1)], 0), text=join_nonempty([delta, label], "  "), size=15, text_color_key="white", bold=True, component_id=component_id, role="delta"))
    return elements, []


def _metric_before_after(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    before = content.get("before", {}); after = content.get("after", {})
    left, bridge, right = frame.split_h([.86, .24, 1.14], gap=14)
    elements: list[dict[str, Any]] = []
    elements += _soft_panel(component_id, left, tokens, "before_panel", fill_key="surfaceAlt")
    elements += _metric_big(component_id, left.inset(24), before, tokens, "dense")[0]
    elements.append(shape(bridge.inset(top=bridge.height * .3, bottom=bridge.height * .3), tokens, shape_name="chevron", fill_key="accent", line_key=None, component_id=component_id, role="bridge"))
    elements += _soft_panel(component_id, right, tokens, "after_panel", fill_key="primary", strong=True)
    inner = right.inset(24)
    vf, lf = inner.split_v([.68, .32], gap=2)
    val = normalize_text(after.get("value") or "—")
    preferred = _metric_safe_size(val, vf.width, font_size(tokens, "hero", 76), 34)
    size, warnings = fit_font_size(val, vf.width, vf.height, preferred, 34, 2)
    elements.append(textbox(vf, val, tokens, size, color_key="white", bold=True, align="center", vertical_align="middle", component_id=component_id, role="after_value"))
    elements.append(textbox(lf, normalize_text(after.get("label")), tokens, 18, color_key="white", bold=True, align="center", vertical_align="middle", component_id=component_id, role="after_label"))
    return elements, warnings


def _metric_pair_gap(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    l, r = content.get("left", {}), content.get("right", {})
    implication = normalize_text(content.get("implication")); separator = normalize_text(content.get("separator") or "GAP")
    lv, rv = _num(l.get("value")), _num(r.get("value"))
    if variant == "alternate":
        main, note = frame.split_h([.68, .32], gap=32)
        top, bot = main.split_v([1, 1], gap=18)
        elements = []
        for f, item, key in [(top, l, "accent"), (bot, r, "danger")]:
            elements.append(line(f.x, f.y + f.height - 4, f.x + f.width, f.y + f.height - 4, tokens, key, 6, component_id=component_id, role=f"{key}_bar"))
            elements += _metric_big(component_id, f.inset(bottom=10), item, tokens, "alternate")[0]
        elements.append(shape(note, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), 1), (1, _mix(color(tokens, "primary"), color(tokens, "accent"), .28), 1)], 90), text=implication, size=font_size(tokens, "lead", 26), text_color_key="white", bold=True, align="left", margin=28, shadow=shadow(tokens, "hero"), component_id=component_id, role="implication"))
        return elements, []
    rows = frame.split_v([.72, .28] if implication else [1], gap=12)
    left, center, right = rows[0].split_h([1.18, .28, .82], gap=18)
    elements: list[dict[str, Any]] = []
    elements += _metric_big(component_id, left, l, tokens, "primary")[0]
    elements.append(textbox(center, separator, tokens, 13, color_key="muted", bold=True, align="center", vertical_align="middle", char_spacing=1.2, component_id=component_id, role="separator"))
    elements += _metric_big(component_id, right, r, tokens, "dense")[0]
    base_y = rows[0].y + rows[0].height - 20
    maxv = max(abs(lv or 1), abs(rv or 1), 1)
    lw = left.width * min(abs(lv or maxv) / maxv, 1)
    rw = right.width * min(abs(rv or maxv) / maxv, 1)
    elements.append(shape(Frame(left.x, base_y, lw, 10), tokens, shape_name="rounded_rectangle", fill_key="accent", line_key=None, component_id=component_id, role="left_bar"))
    elements.append(shape(Frame(right.x, base_y, rw, 10), tokens, shape_name="rounded_rectangle", fill_key="danger", line_key=None, component_id=component_id, role="right_bar"))
    if implication:
        elements.append(textbox(rows[1], implication, tokens, font_size(tokens, "lead", 26), bold=True, align="center", vertical_align="middle", component_id=component_id, role="implication"))
    return elements, []


def _kpi_row(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items: raise ValueError("kpi.rowにはcontent.itemsが必要です")
    frames = frame.split_h([1] * len(items), gap=18)
    elements: list[dict[str, Any]] = []
    for i, (item, f) in enumerate(zip(items, frames, strict=True)):
        if i:
            elements.append(line(f.x - 9, f.y + 22, f.x - 9, f.y + f.height - 22, tokens, "line", 1.3, component_id=component_id, role="divider"))
        elements += _metric_big(component_id, f.inset(10), item, tokens, "dense")[0]
    return elements, []


def _kpi_tiles(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items: raise ValueError("kpi.tilesにはcontent.itemsが必要です")
    cols = min(3, len(items)); rows_n = math.ceil(len(items) / cols)
    rows = frame.split_v([1] * rows_n, gap=18)
    elements: list[dict[str, Any]] = []
    idx = 0
    keys = ["accent", "accent2", "warning", "success", "danger"]
    for row in rows:
        for f in row.split_h([1] * cols, gap=18):
            if idx >= len(items): break
            item = items[idx]; key = keys[idx % len(keys)]
            elements += _soft_panel(component_id, f, tokens, f"tile_{idx}", top_rule=key)
            elements += _metric_big(component_id, f.inset(22, 16, 22, 16), item, tokens, "dense")[0]
            idx += 1
    return elements, []


def _evidence_footer(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    compact = component_id.endswith("compact")
    elements = [line(frame.x, frame.y, frame.x + frame.width, frame.y, tokens, "line", 1, component_id=component_id, role="rule")]
    if compact:
        text = normalize_text(content.get("text") or join_nonempty([f"出典：{content.get('source','')}", content.get("page", "")], " "))
        elements.append(textbox(frame.inset(top=8), text, tokens, font_size(tokens, "source", 11), color_key="muted", vertical_align="middle", component_id=component_id, role="source"))
        return elements, []
    fields = [normalize_text(content.get(k)) for k in ("claim_type", "source", "page", "figure", "sample", "response_type")]
    widths = [.12, .38, .1, .14, .12, .14]
    frames = frame.inset(top=8).split_h(widths, gap=10)
    for i, (txt, f) in enumerate(zip(fields, frames, strict=True)):
        if not txt: continue
        key = "accent" if i == 0 else "muted"
        elements.append(textbox(f, txt, tokens, font_size(tokens, "source", 11), color_key=key, bold=i == 0, vertical_align="middle", component_id=component_id, role=f"field_{i}"))
    return elements, []


def _annotation(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    kind = component_id.split(".")[1]
    if kind == "chart_callout":
        label = normalize_text(content.get("label")); anchor = content.get("anchor") or {"x": frame.x, "y": frame.y + frame.height}
        bubble = frame.inset(left=frame.width * .12, right=frame.width * .04, top=frame.height * .05, bottom=frame.height * .15)
        elements = [line(float(anchor.get("x", frame.x)), float(anchor.get("y", frame.y + frame.height)), bubble.x, bubble.y + bubble.height * .55, tokens, "accent", 2, component_id=component_id, role="connector")]
        elements.append(shape(bubble, tokens, fill_key="surface", line_key="accent", line_width=2, text=label, size=15, bold=True, align="left", margin=16, shadow=shadow(tokens, "card"), component_id=component_id, role="bubble"))
        return elements, []
    text = normalize_text(content.get("text"))
    if kind == "so_what":
        elements = [shape(frame, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), .96), (1, _mix(color(tokens, "primary"), color(tokens, "accent"), .38), .96)], 0), shadow=shadow(tokens, "hero"), component_id=component_id, role="background")]
        mark = Frame(frame.x + 24, frame.y + 22, 8, frame.height - 44)
        elements.append(shape(mark, tokens, shape_name="rectangle", fill_key="accent", line_key=None, component_id=component_id, role="mark"))
        text_frame = frame.inset(left=52, top=16, right=28, bottom=16)
        preferred = font_size(tokens, "lead", 26) - (3 if variant == "dense" else 0)
        size, warnings = fit_font_size(text, text_frame.width, text_frame.height, preferred, 16, 5)
        elements.append(textbox(text_frame, text, tokens, size, color_key="white", bold=True, vertical_align="middle", line_spacing_pct=95, component_id=component_id, role="text"))
        return elements, warnings
    elements = [shape(frame, tokens, fill_key="surfaceAlt", line_key=None, component_id=component_id, role="background")]
    elements.append(circle(Frame(frame.x + 18, frame.y + frame.height/2 - 16, 32, 32), "!", tokens, "warning", component_id, "icon", 14))
    elements.append(textbox(frame.inset(left=62, top=12, right=20, bottom=12), text, tokens, 14 if variant == "dense" else 15, color_key="muted", vertical_align="middle", component_id=component_id, role="text"))
    return elements, []


def _comparison(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    kind = component_id.split(".")[1]
    left_text, right_text = normalize_text(content.get("left")), normalize_text(content.get("right"))
    lt = normalize_text(content.get("left_title") or {"gap":"CURRENT", "before_after":"BEFORE", "current_future":"CURRENT", "pro_con":"PRO"}.get(kind, "LEFT"))
    rt = normalize_text(content.get("right_title") or {"gap":"TARGET", "before_after":"AFTER", "current_future":"FUTURE", "pro_con":"CON"}.get(kind, "RIGHT"))
    elements: list[dict[str, Any]] = []
    if kind == "before_after":
        left, bridge, right = frame.split_h([.9, .22, 1.1], gap=14)
        elements += _soft_panel(component_id, left, tokens, "before", fill_key="surfaceAlt")
        elements.append(textbox(left.inset(26, 22, 26, 22), f"{{{{bold,#61737B:{lt}}}}}\n{left_text}", tokens, 20, color_key="text", vertical_align="middle", line_spacing_pct=110, component_id=component_id, role="before_text"))
        elements.append(shape(bridge.inset(top=bridge.height*.28, bottom=bridge.height*.28), tokens, shape_name="chevron", fill_key="accent", line_key=None, component_id=component_id, role="bridge"))
        elements += _soft_panel(component_id, right, tokens, "after", fill_key="primary", strong=True)
        elements.append(textbox(right.inset(30, 24, 30, 24), f"{{{{bold,#74F2ED:{rt}}}}}\n{{{{bold,#FFFFFF:{right_text}}}}}", tokens, 22, color_key="white", vertical_align="middle", line_spacing_pct=105, component_id=component_id, role="after_text"))
    elif kind == "current_future":
        top, bottom = frame.split_v([.42, .58], gap=18)
        elements.append(textbox(top, left_text, tokens, 23, color_key="muted", bold=True, align="center", vertical_align="middle", component_id=component_id, role="current"))
        elements.append(line(frame.x + frame.width*.12, top.y + top.height - 4, frame.x + frame.width*.88, top.y + top.height - 4, tokens, "accent", 5, arrow_end="triangle", component_id=component_id, role="transition"))
        elements.append(shape(bottom, tokens, fill_key="primary", line_key=None, gradient=gradient([(0, color(tokens, "primary"), 1), (1, color(tokens, "accent2"), .92)], 0), text=right_text, size=25, text_color_key="white", bold=True, margin=26, shadow=shadow(tokens, "hero"), component_id=component_id, role="future"))
    elif kind == "pro_con":
        left, spine, right = frame.split_h([1, .13, 1], gap=18)
        elements += _soft_panel(component_id, left, tokens, "pro", fill_key="surface")
        elements += _soft_panel(component_id, right, tokens, "con", fill_key="surface")
        elements.append(circle(Frame(spine.x, spine.y + spine.height*.18, spine.width, spine.width), "+", tokens, "success", component_id, "plus", 20))
        elements.append(circle(Frame(spine.x, spine.y + spine.height*.62, spine.width, spine.width), "−", tokens, "danger", component_id, "minus", 20))
        elements.append(textbox(left.inset(24), f"{{{{bold,#65B86A:{lt}}}}}\n{left_text}", tokens, 20, vertical_align="middle", line_spacing_pct=110, component_id=component_id, role="pro_text"))
        elements.append(textbox(right.inset(24), f"{{{{bold,#EE6B6E:{rt}}}}}\n{right_text}", tokens, 20, vertical_align="middle", line_spacing_pct=110, component_id=component_id, role="con_text"))
    else:  # gap
        left, gapf, right = frame.split_h([1.12, .18, .88], gap=16)
        elements.append(textbox(left, f"{{{{bold,#00A6A6:{lt}}}}}\n{{{{bold:{left_text}}}}}", tokens, 24, vertical_align="middle", line_spacing_pct=100, component_id=component_id, role="left"))
        elements.append(line(left.x, left.y + left.height - 20, left.x + left.width, left.y + left.height - 20, tokens, "accent", 8, component_id=component_id, role="left_bar"))
        elements.append(textbox(gapf, normalize_text(content.get("separator") or "GAP"), tokens, 12, color_key="muted", bold=True, align="center", vertical_align="middle", rotation=90, char_spacing=1.2, component_id=component_id, role="gap"))
        elements.append(textbox(right, f"{{{{bold,#EE6B6E:{rt}}}}}\n{right_text}", tokens, 20, color_key="muted", vertical_align="middle", line_spacing_pct=105, component_id=component_id, role="right"))
        elements.append(line(right.x, right.y + right.height - 20, right.x + right.width*.46, right.y + right.height - 20, tokens, "danger", 8, component_id=component_id, role="right_bar"))
    return elements, []


def _process_stage_flow(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    stages = list(content.get("stages") or [])
    if not stages: raise ValueError("process.stage_flowにはcontent.stagesが必要です")
    n = len(stages); elements: list[dict[str, Any]] = []
    y = frame.y + frame.height * .36
    elements.append(line(frame.x + 40, y, frame.x + frame.width - 40, y, tokens, "line", 4, component_id=component_id, role="spine"))
    step_w = frame.width / n
    keys = ["accent", "accent2", "warning", "success", "danger"]
    for i, stage in enumerate(stages):
        cx = frame.x + step_w * (i + .5)
        key = keys[i % len(keys)]
        elements.append(circle(Frame(cx-24, y-24, 48, 48), f"{i+1:02d}", tokens, key, component_id, f"node_{i}", 13))
        title_frame = Frame(frame.x + step_w*i + 10, frame.y, step_w-20, frame.height*.25)
        body_frame = Frame(frame.x + step_w*i + 14, y+42, step_w-28, frame.height-(y-frame.y)-48)
        elements.append(textbox(title_frame, normalize_text(stage.get("title")), tokens, 20, color_key="primary", bold=True, align="center", vertical_align="bottom", component_id=component_id, role=f"title_{i}"))
        elements.append(textbox(body_frame, normalize_text(stage.get("body")), tokens, 14 if variant == "dense" else 15, color_key="muted", align="center", vertical_align="top", component_id=component_id, role=f"body_{i}"))
    return elements, []


def _process_gate(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    before, question, yes, no = [normalize_text(content.get(k)) for k in ("before", "question", "yes", "no")]
    left, mid, right = frame.split_h([.7, 1, .9], gap=22)
    elements = [shape(left.inset(top=left.height*.25, bottom=left.height*.25), tokens, fill_key="surfaceAlt", line_key=None, text=before, size=18, bold=True, component_id=component_id, role="before")]
    diamond = mid.inset(left=mid.width*.18, right=mid.width*.18, top=mid.height*.08, bottom=mid.height*.08)
    elements.append(shape(diamond, tokens, shape_name="diamond", fill_key="primary", line_key=None, text=question, size=17 if variant == "dense" else 19, text_color_key="white", bold=True, margin=18, shadow=shadow(tokens, "card"), component_id=component_id, role="gate"))
    elements.append(line(left.x+left.width, frame.y+frame.height/2, diamond.x, frame.y+frame.height/2, tokens, "accent", 3, arrow_end="triangle", component_id=component_id, role="in"))
    yesf, nof = right.split_v([1,1], gap=18)
    elements.append(shape(yesf, tokens, fill_key="success", line_key=None, text=f"YES  {yes}", size=17, text_color_key="white", bold=True, align="left", margin=20, component_id=component_id, role="yes"))
    elements.append(shape(nof, tokens, fill_key="surface", line_key="danger", line_width=2, text=f"NO   {no}", size=17, text_color_key="danger", bold=True, align="left", margin=20, component_id=component_id, role="no"))
    elements.append(line(diamond.x+diamond.width, frame.y+frame.height/2, yesf.x, yesf.y+yesf.height/2, tokens, "success", 2.5, arrow_end="triangle", component_id=component_id, role="yes_line"))
    elements.append(line(diamond.x+diamond.width, frame.y+frame.height/2, nof.x, nof.y+nof.height/2, tokens, "danger", 2.5, arrow_end="triangle", component_id=component_id, role="no_line"))
    return elements, []


def _timeline(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items: raise ValueError("timeline.milestoneにはcontent.itemsが必要です")
    n=len(items); y=frame.y+frame.height*.5; step=frame.width/max(n,1)
    elements=[line(frame.x+step*.25, y, frame.x+frame.width-step*.25, y, tokens, "accent", 4, component_id=component_id, role="spine")]
    for i,item in enumerate(items):
        cx=frame.x+step*(i+.5); top=i%2==0 or variant=="dense"
        elements.append(circle(Frame(cx-18,y-18,36,36), str(i+1), tokens, "accent" if i<n-1 else "primary", component_id, f"node_{i}", 11))
        date_y = y-70 if top else y+36; title_y = y-138 if top else y+72
        elements.append(textbox(Frame(cx-step*.42,date_y,step*.84,28), normalize_text(item.get("date")), tokens, 12, color_key="accent", bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"date_{i}"))
        elements.append(textbox(Frame(cx-step*.42,title_y,step*.84,64), normalize_text(item.get("title")), tokens, 17, bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"title_{i}"))
    return elements, []


def _causal_spine(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items = list(content.get("items") or [])
    if not items:
        items = [{"label":"原因","text":content.get("cause")},{"label":"現象","text":content.get("phenomenon")},{"label":"解釈","text":content.get("interpretation")},{"label":"打ち手","text":content.get("action")}]
    elements: list[dict[str, Any]]=[]
    if variant == "alternate":
        frames=frame.split_h([1]*len(items),gap=10)
        for i,(item,f) in enumerate(zip(items,frames,strict=True)):
            key=["muted","accent2","accent","warning"][i%4]
            elements.append(shape(f, tokens, fill_key="surface", line_key=None, shadow=shadow(tokens,"card"), component_id=component_id, role=f"panel_{i}"))
            elements.append(shape(Frame(f.x,f.y,f.width,8), tokens, shape_name="rectangle", fill_key=key, line_key=None, component_id=component_id, role=f"rule_{i}"))
            elements.append(textbox(f.inset(20,18,20,18), f"{{{{bold,{color(tokens,key)}:{normalize_text(item.get('label'))}}}}}\n{normalize_text(item.get('text'))}", tokens, 17, vertical_align="middle", line_spacing_pct=110, component_id=component_id, role=f"text_{i}"))
        return elements,[]
    rail=Frame(frame.x+frame.width*.08,frame.y,18,frame.height)
    elements.append(shape(rail,tokens,shape_name="rounded_rectangle",fill_key="accent",line_key=None,gradient=gradient([(0,color(tokens,"accent2"),1),(1,color(tokens,"accent"),1)],90),component_id=component_id,role="rail"))
    rows=frame.inset(left=frame.width*.14).split_v([1]*len(items),gap=12)
    for i,(item,row) in enumerate(zip(items,rows,strict=True)):
        elements.append(circle(Frame(rail.x-11,row.y+row.height/2-15,30,30),str(i+1),tokens,"primary",component_id,f"node_{i}",10))
        label_f,text_f=row.split_h([.22,.78],gap=14)
        elements.append(textbox(label_f,normalize_text(item.get("label")),tokens,14,color_key="accent",bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
        elements.append(textbox(text_f,normalize_text(item.get("text")),tokens,18,bold=True,vertical_align="middle",component_id=component_id,role=f"text_{i}"))
    return elements,[]


def _decision_choice(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    question=normalize_text(content.get("question")); options=list(content.get("options") or [])
    selected=content.get("selected")
    qf,of=frame.split_v([.25,.75],gap=16)
    elements=[textbox(qf,question,tokens,font_size(tokens,"lead",26),bold=True,align="center",vertical_align="middle",component_id=component_id,role="question")]
    frames=of.split_h([1]*len(options),gap=18)
    for i,(opt,f) in enumerate(zip(options,frames,strict=True)):
        active=selected in {i,opt.get("label")}
        if active:
            elements.append(shape(f,tokens,fill_key="primary",line_key=None,gradient=gradient([(0,color(tokens,"primary"),1),(1,color(tokens,"accent2"),.95)],0),shadow=shadow(tokens,"hero"),component_id=component_id,role=f"option_{i}"))
        else:
            elements.append(shape(f,tokens,fill_key="surface",line_key="line",line_width=1,component_id=component_id,role=f"option_{i}"))
        lf,df=f.inset(22).split_v([.36,.64],gap=4)
        elements.append(textbox(lf,normalize_text(opt.get("label")),tokens,22,color_key="white" if active else "primary",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"label_{i}"))
        elements.append(textbox(df,normalize_text(opt.get("description")),tokens,15,color_key="white" if active else "muted",align="center",vertical_align="top",component_id=component_id,role=f"desc_{i}"))
    return elements,[]


def _decision_criteria(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    columns=list(content.get("columns") or ["評価軸","基準","判定"]); rows=list(content.get("rows") or [])
    if not rows: rows=[["価値","成果指標が明確","○"],["実行性","責任者とデータがある","△"],["リスク","管理策が定義済み","○"]]
    ratios=[.28,.52,.20] if len(columns)==3 else [1]*len(columns)
    rowfs=frame.split_v([.85]+[1]*len(rows),gap=0); elements=[]
    for i,(c,f) in enumerate(zip(columns,rowfs[0].split_h(ratios),strict=True)):
        elements.append(textbox(f.inset(left=12),normalize_text(c),tokens,13,color_key="muted",bold=True,vertical_align="middle",component_id=component_id,role=f"head_{i}"))
    elements.append(line(frame.x,rowfs[0].y+rowfs[0].height,frame.x+frame.width,rowfs[0].y+rowfs[0].height,tokens,"primary",2,component_id=component_id,role="head_rule"))
    for ri,(row,rf) in enumerate(zip(rows,rowfs[1:],strict=True)):
        cells=rf.split_h(ratios)
        elements.append(line(rf.x,rf.y+rf.height,rf.x+rf.width,rf.y+rf.height,tokens,"line",1,component_id=component_id,role=f"rule_{ri}"))
        for ci,f in enumerate(cells):
            val=normalize_text(row[ci] if ci<len(row) else "")
            if ci==len(cells)-1:
                key="success" if val in {"○","GO","Yes","YES"} else "warning" if val in {"△","HOLD"} else "danger"
                elements.append(circle(f.inset(left=f.width*.35,right=f.width*.35,top=f.height*.25,bottom=f.height*.25),val,tokens,key,component_id,f"judge_{ri}",12))
            else:
                elements.append(textbox(f.inset(left=12),val,tokens,15,bold=ci==0,vertical_align="middle",component_id=component_id,role=f"cell_{ri}_{ci}"))
    return elements,[]


def _matrix_quadrant(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    x_label=normalize_text(content.get("x_label") or "実行難易度"); y_label=normalize_text(content.get("y_label") or "期待価値")
    quadrants=content.get("quadrants") or ["育成","優先","見送り","選択"]
    plot=frame.inset(left=76,top=20,right=24,bottom=62); elements=[]
    # shade priority quadrant
    elements.append(shape(Frame(plot.x+plot.width/2,plot.y,plot.width/2,plot.height/2),tokens,shape_name="rectangle",fill_key="surfaceAlt",line_key=None,opacity=.9,component_id=component_id,role="priority_zone"))
    elements += [line(plot.x,plot.y+plot.height,plot.x+plot.width,plot.y+plot.height,tokens,"text",2,arrow_end="triangle",component_id=component_id,role="x_axis"),line(plot.x,plot.y+plot.height,plot.x,plot.y,tokens,"text",2,arrow_end="triangle",component_id=component_id,role="y_axis")]
    elements.append(line(plot.x+plot.width/2,plot.y,plot.x+plot.width/2,plot.y+plot.height,tokens,"line",1.2,dashed=True,component_id=component_id,role="v_mid")); elements.append(line(plot.x,plot.y+plot.height/2,plot.x+plot.width,plot.y+plot.height/2,tokens,"line",1.2,dashed=True,component_id=component_id,role="h_mid"))
    elements.append(textbox(Frame(plot.x,plot.y+plot.height+18,plot.width,28),x_label,tokens,13,color_key="muted",bold=True,align="center",component_id=component_id,role="x_label")); elements.append(textbox(Frame(frame.x,plot.y,52,plot.height),y_label,tokens,13,color_key="muted",bold=True,align="center",vertical_align="middle",rotation=270,component_id=component_id,role="y_label"))
    qfs=[Frame(plot.x,plot.y,plot.width/2,plot.height/2),Frame(plot.x+plot.width/2,plot.y,plot.width/2,plot.height/2),Frame(plot.x,plot.y+plot.height/2,plot.width/2,plot.height/2),Frame(plot.x+plot.width/2,plot.y+plot.height/2,plot.width/2,plot.height/2)]
    for i,(lab,qf) in enumerate(zip(quadrants,qfs,strict=False)):
        elements.append(textbox(qf.inset(12),normalize_text(lab),tokens,13,color_key="accent" if i==1 else "muted",bold=True,component_id=component_id,role=f"quadrant_{i}"))
    for i,item in enumerate(content.get("items") or []):
        px=plot.x+float(item.get("x",.5))*plot.width; py=plot.y+(1-float(item.get("y",.5)))*plot.height
        key="accent" if item.get("highlight") else "primary"
        elements.append(circle(Frame(px-20,py-20,40,40),str(i+1),tokens,key,component_id,f"item_{i}",11)); elements.append(textbox(Frame(px+26,py-18,150,36),normalize_text(item.get("label")),tokens,12,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
    return elements,[]


def _action_form(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    fields=list(content.get("fields") or [{"label":"対象課題","value":""},{"label":"価値仮説","value":""},{"label":"成果指標","value":""},{"label":"必要データ","value":""},{"label":"判断条件","value":""}])
    cols=2 if variant!="dense" and len(fields)>=4 else 1; rows_n=math.ceil(len(fields)/cols); rowfs=frame.split_v([1]*rows_n,gap=18); elements=[]; idx=0
    for rf in rowfs:
        for f in rf.split_h([1]*cols,gap=22):
            if idx>=len(fields):break
            item=fields[idx]; lf,vf=f.split_v([.28,.72],gap=2)
            elements.append(textbox(lf,normalize_text(item.get("label")),tokens,13,color_key="accent",bold=True,vertical_align="middle",component_id=component_id,role=f"label_{idx}"))
            elements.append(textbox(vf.inset(left=2,right=2),normalize_text(item.get("value")),tokens,16,vertical_align="top",component_id=component_id,role=f"value_{idx}"))
            elements.append(line(vf.x,vf.y+vf.height,vf.x+vf.width,vf.y+vf.height,tokens,"line",1.5,component_id=component_id,role=f"underline_{idx}")); idx+=1
    return elements,[]


def _action_owner_due(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    owner=normalize_text(content.get("owner") or "責任者："); due=normalize_text(content.get("due") or "期限："); status=normalize_text(content.get("status") or "未着手")
    left,mid,right=frame.split_h([.42,.36,.22],gap=18); elements=[]
    for f,lab,val,key in [(left,"OWNER",owner,"accent2"),(mid,"DUE",due,"warning")]:
        elements += _soft_panel(component_id,f,tokens,lab.lower(),fill_key="surface")
        kf,vf=f.inset(18).split_v([.28,.72],gap=2); elements.append(textbox(kf,lab,tokens,11,color_key=key,bold=True,char_spacing=1.4,vertical_align="middle",component_id=component_id,role=f"{lab}_label")); elements.append(textbox(vf,val,tokens,17,bold=True,vertical_align="middle",component_id=component_id,role=f"{lab}_value"))
    elements.append(shape(right,tokens,fill_key="accent",line_key=None,gradient=gradient([(0,color(tokens,"accent"),1),(1,color(tokens,"accent2"),1)],0),text=status,size=15,text_color_key="white",bold=True,shadow=shadow(tokens,"card"),component_id=component_id,role="status"))
    return elements,[]


def _chart_progress_rows(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); maxv=float(content.get("max") or max([_num(i.get("value")) or 0 for i in items] or [100])); rows=frame.split_v([1]*len(items),gap=10); elements=[]
    for i,(item,rf) in enumerate(zip(items,rows,strict=True)):
        label,raw=normalize_text(item.get("label")),normalize_text(item.get("value")); val=_num(raw) or 0
        lf,bf,vf=rf.split_h([.3,.56,.14],gap=12); elements.append(textbox(lf,label,tokens,14,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
        track=bf.inset(top=bf.height*.29,bottom=bf.height*.29); elements.append(shape(track,tokens,shape_name="rounded_rectangle",fill_key="surfaceStrong",line_key=None,component_id=component_id,role=f"track_{i}")); fill=Frame(track.x,track.y,max(8,track.width*min(val/maxv,1)),track.height)
        key=normalize_text(item.get("color_key") or ("accent" if i==0 else "accent2")); elements.append(shape(fill,tokens,shape_name="rounded_rectangle",fill_key=key,line_key=None,gradient=gradient([(0,color(tokens,key),1),(1,_mix(color(tokens,key),color(tokens,"primary"),.2),1)],0),component_id=component_id,role=f"fill_{i}")); elements.append(textbox(vf,raw,tokens,16,color_key="primary",bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"value_{i}"))
    return elements,[]


def _chart_stacked_bar(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); total=sum((_num(i.get("value")) or 0) for i in items) or 1; bar=frame.inset(top=frame.height*.18,bottom=frame.height*.38); elements=[]; x=bar.x; keys=["accent2","warning","danger","accent","success"]
    for i,item in enumerate(items):
        val=_num(item.get("value")) or 0; w=bar.width*val/total; key=normalize_text(item.get("color_key") or keys[i%len(keys)]); sf=Frame(x,bar.y,w,bar.height); elements.append(shape(sf,tokens,shape_name="rectangle",fill_key=key,line_key=None,text=normalize_text(item.get("value")),size=14,text_color_key="white",bold=True,component_id=component_id,role=f"seg_{i}")); x+=w
    legend=Frame(frame.x,bar.y+bar.height+24,frame.width,frame.height-(bar.y+bar.height+24-frame.y)); lfs=legend.split_h([1]*len(items),gap=8)
    for i,(item,lf) in enumerate(zip(items,lfs,strict=True)):
        key=normalize_text(item.get("color_key") or keys[i%len(keys)]); elements.append(shape(Frame(lf.x,lf.y+8,12,12),tokens,shape_name="rectangle",fill_key=key,line_key=None,component_id=component_id,role=f"dot_{i}")); elements.append(textbox(lf.inset(left=20),normalize_text(item.get("label")),tokens,12,color_key="muted",vertical_align="top",component_id=component_id,role=f"legend_{i}"))
    return elements,[]


def _chart_slope(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); left_label=normalize_text(content.get("left_label") or "Before"); right_label=normalize_text(content.get("right_label") or "After")
    plot=frame.inset(left=100,right=100,top=42,bottom=24); vals=[_num(i.get("left")) or 0 for i in items]+[_num(i.get("right")) or 0 for i in items]; lo=min(vals or [0]); hi=max(vals or [1]); rng=max(hi-lo,1); elements=[]
    lx,rx=plot.x,plot.x+plot.width; elements.append(textbox(Frame(lx-80,frame.y,160,30),left_label,tokens,13,color_key="muted",bold=True,align="center",component_id=component_id,role="left_head")); elements.append(textbox(Frame(rx-80,frame.y,160,30),right_label,tokens,13,color_key="muted",bold=True,align="center",component_id=component_id,role="right_head"))
    for i,item in enumerate(items):
        lv,rv=_num(item.get("left")) or 0,_num(item.get("right")) or 0; ly=plot.y+plot.height*(1-(lv-lo)/rng); ry=plot.y+plot.height*(1-(rv-lo)/rng); key="accent" if rv>=lv else "danger"
        elements.append(line(lx,ly,rx,ry,tokens,key,3,component_id=component_id,role=f"slope_{i}")); elements.append(circle(Frame(lx-8,ly-8,16,16),"",tokens,key,component_id,f"left_{i}",8)); elements.append(circle(Frame(rx-8,ry-8,16,16),"",tokens,key,component_id,f"right_{i}",8)); elements.append(textbox(Frame(lx-88,ly-18,78,36),normalize_text(item.get("left")),tokens,12,color_key="text",bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"lv_{i}")); elements.append(textbox(Frame(rx+10,ry-18,110,36),join_nonempty([normalize_text(item.get("right")),normalize_text(item.get("label"))],"  "),tokens,12,color_key="text",bold=True,vertical_align="middle",component_id=component_id,role=f"rv_{i}"))
    return elements,[]


def _chart_waterfall(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); values=[_num(i.get("value")) or 0 for i in items]; cumulative=[]; cur=0
    for i,v in enumerate(values):
        if items[i].get("total"): cur=v
        else: cur+=v
        cumulative.append(cur)
    minv=min([0]+cumulative); maxv=max([1]+cumulative); rng=max(maxv-minv,1); plot=frame.inset(left=40,right=30,top=30,bottom=60); bw=plot.width/max(len(items),1)*.56; gap=plot.width/max(len(items),1); elements=[]; prev=0
    y0=plot.y+plot.height*(maxv/rng)
    elements.append(line(plot.x,y0,plot.x+plot.width,y0,tokens,"line",1,component_id=component_id,role="zero"))
    for i,(item,v,cum) in enumerate(zip(items,values,cumulative,strict=True)):
        x=plot.x+gap*(i+.5)-bw/2; start=0 if item.get("total") else prev; end=cum; top=max(start,end); bottom=min(start,end); ytop=plot.y+plot.height*(maxv-top)/rng; ybottom=plot.y+plot.height*(maxv-bottom)/rng; key="primary" if item.get("total") else "success" if v>=0 else "danger"; bar=Frame(x,ytop,bw,max(6,ybottom-ytop)); elements.append(shape(bar,tokens,shape_name="rectangle",fill_key=key,line_key=None,component_id=component_id,role=f"bar_{i}")); elements.append(textbox(Frame(x-20,bar.y-26,bw+40,22),normalize_text(item.get("value")),tokens,12,color_key=key,bold=True,align="center",component_id=component_id,role=f"value_{i}")); elements.append(textbox(Frame(x-30,plot.y+plot.height+14,bw+60,34),normalize_text(item.get("label")),tokens,11,color_key="muted",bold=True,align="center",vertical_align="top",component_id=component_id,role=f"label_{i}")); prev=cum
    return elements,[]


def _summary_strip(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); frames=frame.split_h([1]*len(items),gap=18); elements=[]; keys=["accent","accent2","warning","danger","success"]
    for i,(item,f) in enumerate(zip(items,frames,strict=True)):
        key=normalize_text(item.get("color_key") or keys[i%len(keys)]); elements += _soft_panel(component_id,f,tokens,f"item_{i}",fill_key="surface",top_rule=key); vf,tf=f.inset(20,18,20,18).split_v([.42,.58],gap=8); raw_value = normalize_text(item.get("value"))
        if " vs " in raw_value.lower():
            parts = re.split(r"\s+vs\s+", raw_value, flags=re.I)
            raw_value = parts[0] + "\nvs " + parts[1] if len(parts) == 2 else raw_value
        preferred = _metric_safe_size(raw_value, vf.width, 34 if variant=="dense" else 40, 20)
        elements.append(textbox(vf,raw_value,tokens,preferred,color_key="primary",bold=True,vertical_align="middle",line_spacing_pct=90,component_id=component_id,role=f"value_{i}")); elements.append(textbox(tf,normalize_text(item.get("text") or item.get("label")),tokens,14,color_key="muted",bold=True,vertical_align="top",line_spacing_pct=110,component_id=component_id,role=f"text_{i}"))
    return elements,[]


def _quote_editorial(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    text=normalize_text(content.get("text")); attribution=normalize_text(content.get("attribution")); elements=[]
    elements.append(textbox(Frame(frame.x,frame.y,frame.width*.18,frame.height*.5),"“",tokens,min(120,int(frame.height*.55)),color_key="accent",bold=True,align="center",vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="quote_mark"))
    tf=frame.inset(left=frame.width*.16,top=10,right=20,bottom=50); size,w=fit_font_size(text,tf.width,tf.height,32 if variant=="primary" else 26,20,4); elements.append(textbox(tf,text,tokens,size,bold=True,vertical_align="middle",line_spacing_pct=105,font_family=display_font(tokens),component_id=component_id,role="quote")); elements.append(line(tf.x,frame.y+frame.height-42,tf.x+90,frame.y+frame.height-42,tokens,"accent",3,component_id=component_id,role="rule")); elements.append(textbox(Frame(tf.x+108,frame.y+frame.height-56,tf.width-108,32),attribution,tokens,13,color_key="muted",bold=True,vertical_align="middle",component_id=component_id,role="attribution")); return elements,w


def _framework_layers(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    items=list(content.get("items") or []); rows=frame.split_v([1]*len(items),gap=12); elements=[]; keys=["primary","accent2","accent","warning","success"]
    for i,(item,f) in enumerate(zip(items,rows,strict=True)):
        inset=i*min(30,frame.width*.035); lf=f.inset(left=inset,right=inset); key=normalize_text(item.get("color_key") or keys[i%len(keys)]); elements.append(shape(lf,tokens,fill_key=key,line_key=None,opacity=1-.06*i,text=normalize_text(item.get("title")),size=17,text_color_key="white",bold=True,align="left",margin=22,component_id=component_id,role=f"layer_{i}")); body=normalize_text(item.get("body"));
        if body: elements.append(textbox(Frame(lf.x+lf.width*.38,lf.y,lf.width*.57,lf.height),body,tokens,14,color_key="white",align="right",vertical_align="middle",component_id=component_id,role=f"body_{i}"))
    return elements,[]


def _framework_hub(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[str]]:
    center=content.get("center") or {}; items=list(content.get("items") or []); cx=frame.x+frame.width/2; cy=frame.y+frame.height/2; radius=min(frame.width,frame.height)*.36; hub=Frame(cx-75,cy-75,150,150); elements=[]
    for i,item in enumerate(items):
        ang=-math.pi/2+2*math.pi*i/max(len(items),1); nx=cx+math.cos(ang)*radius; ny=cy+math.sin(ang)*radius; nf=Frame(nx-70,ny-44,140,88); elements.append(line(cx,cy,nx,ny,tokens,"line",2,component_id=component_id,role=f"connector_{i}")); elements.append(shape(nf,tokens,fill_key="surface",line_key="accent",line_width=2,text=normalize_text(item.get("label")),size=14,bold=True,shadow=shadow(tokens,"card"),component_id=component_id,role=f"node_{i}"))
    elements.append(shape(hub,tokens,shape_name="oval",fill_key="primary",line_key=None,gradient=gradient([(0,color(tokens,"primary"),1),(1,color(tokens,"accent2"),1)],45),text=normalize_text(center.get("label") or center.get("text") or "CORE"),size=20,text_color_key="white",bold=True,shadow=shadow(tokens,"hero"),component_id=component_id,role="hub")); return elements,[]


BUILDERS: dict[str, Builder] = {
    "headline.fact": _headline, "headline.insight": _headline, "headline.recommendation": _headline, "headline.decision": _headline,
    "label.fact_tag": _label, "label.interpretation_tag": _label, "label.proposal_tag": _label, "label.section": _label,
    "metric.big_number": _metric_big, "metric.delta": _metric_delta, "metric.before_after": _metric_before_after, "metric_pair.gap": _metric_pair_gap,
    "kpi.row": _kpi_row, "kpi.tiles": _kpi_tiles,
    "evidence_footer.full": _evidence_footer, "evidence_footer.compact": _evidence_footer,
    "annotation.so_what": _annotation, "annotation.caveat": _annotation, "annotation.chart_callout": _annotation,
    "comparison.gap": _comparison, "comparison.before_after": _comparison, "comparison.current_future": _comparison, "comparison.pro_con": _comparison,
    "process.stage_flow": _process_stage_flow, "process.gate": _process_gate, "timeline.milestone": _timeline, "synthesis.causal_spine": _causal_spine,
    "decision.choice": _decision_choice, "decision.criteria": _decision_criteria, "matrix.quadrant": _matrix_quadrant, "action.form": _action_form, "action.owner_due": _action_owner_due,
    "chart.progress_rows": _chart_progress_rows, "chart.stacked_bar": _chart_stacked_bar, "chart.slope": _chart_slope, "chart.waterfall": _chart_waterfall,
    "insight.summary_strip": _summary_strip, "quote.editorial": _quote_editorial, "framework.layers": _framework_layers, "framework.hub_spoke": _framework_hub,
}


# Consulting-grade extensions (v3)
from .consulting_components import CONSULTING_BUILDERS
BUILDERS.update(CONSULTING_BUILDERS)

# Premium design-system specific overrides (v4)
from .premium_components import PREMIUM_BUILDERS
BUILDERS.update(PREMIUM_BUILDERS)
