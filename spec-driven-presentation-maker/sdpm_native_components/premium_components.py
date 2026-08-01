from __future__ import annotations

"""Premium consulting components.

These builders intentionally change composition by design system, not merely color.
Supported design systems are mapped from themes:
- executive -> consulting_classic
- editorial -> editorial_premium
- technical -> technical_data
Other themes fall back to consulting_classic.
"""

import math
import re
from collections.abc import Callable
from typing import Any

from .models import Frame
from .primitives import circle, gradient, line, pill, shape, textbox
from .text import fit_font_size, normalize_text
from .theme import color, display_font, font_size, shadow

Builder = Callable[[str, Frame, dict[str, Any], dict[str, Any], str], tuple[list[dict[str, Any]], list[str]]]


def _design(tokens: dict[str, Any]) -> str:
    tid = str(tokens.get("id", "executive"))
    if tid == "editorial":
        return "editorial_premium"
    if tid in {"technical", "data-report", "data_report"}:
        return "technical_data"
    return "consulting_classic"


def _mix(a: str, b: str, ratio: float) -> str:
    a = a.lstrip("#"); b = b.lstrip("#")
    vals = [round(int(a[i:i+2], 16) * (1-ratio) + int(b[i:i+2], 16) * ratio) for i in (0, 2, 4)]
    return "#" + "".join(f"{v:02X}" for v in vals)


def _num(value: Any) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(m.group()) if m else None


def _fit(text: str, frame: Frame, preferred: int, minimum: int = 14, max_lines: int = 4) -> tuple[int, list[str]]:
    return fit_font_size(text, frame.width, frame.height, preferred, minimum, max_lines)


def _rule_label(component_id: str, frame: Frame, text: str, tokens: dict[str, Any], role: str, *, key: str = "accent") -> list[dict[str, Any]]:
    return [
        textbox(frame, text.upper(), tokens, 11, color_key=key, bold=True, char_spacing=1.7,
                vertical_align="middle", component_id=component_id, role=role),
        line(frame.x, frame.y + frame.height - 2, frame.x + min(frame.width, 110), frame.y + frame.height - 2,
             tokens, key, 2.5, component_id=component_id, role=f"{role}_rule"),
    ]


def _soft_bg(component_id: str, frame: Frame, tokens: dict[str, Any], role: str, *, key: str = "surfaceAlt", opacity: float = .68) -> dict[str, Any]:
    return shape(frame, tokens, fill_key=key, line_key=None, opacity=opacity, component_id=component_id, role=role)


def _metric_chip(component_id: str, frame: Frame, value: str, label: str, tokens: dict[str, Any], role: str, *, key: str = "accent", dark: bool = False) -> list[dict[str, Any]]:
    bg_key = "primary" if dark else "surface"
    text_key = "white" if dark else "text"
    els = [shape(frame, tokens, fill_key=bg_key, line_key=None if dark else "line", line_width=1,
                 shadow=shadow(tokens, "card") if dark else None, component_id=component_id, role=f"{role}_bg")]
    vf, lf = frame.inset(16, 12, 16, 12).split_v([.62, .38], gap=2)
    els.append(textbox(vf, value, tokens, 28, color_key=("white" if dark else key), bold=True,
                       align="center", vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role=f"{role}_value"))
    els.append(textbox(lf, label, tokens, 11, color_key=("white" if dark else "muted"), bold=True,
                       align="center", vertical_align="middle", component_id=component_id, role=f"{role}_label"))
    return els


# ---------------------------------------------------------------------------
# 1 Executive Summary
# ---------------------------------------------------------------------------

def executive_summary(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    items = list(content.get("items") or [])
    if not items:
        raise ValueError("narrative.executive_summaryにはcontent.itemsが必要です")
    items = items[:6 if variant == "dense" else 5]
    d = _design(tokens)
    elements: list[dict[str, Any]] = []

    if d == "editorial_premium":
        hero = normalize_text(content.get("headline") or content.get("summary") or items[0].get("title") or items[0].get("headline"))
        left, right = frame.split_h([.42, .58], gap=50)
        elements.append(_soft_bg(component_id, Frame(left.x, left.y, left.width*.86, left.height), tokens, "wash", key="surfaceAlt", opacity=.5))
        elements += _rule_label(component_id, Frame(left.x, left.y, left.width, 30), "EXECUTIVE SUMMARY", tokens, "kicker")
        hf = left.inset(top=58, right=24)
        # 日本語の自動折返しは欧文より1行あたりの実効文字数が少ないため、
        # 末尾1文字の孤立を避ける安全側の上限からフィットさせる。
        size, warnings = _fit(hero, hf, 28 if variant != "dense" else 26, 22, 5)
        elements.append(textbox(hf, hero, tokens, size, color_key="primary", bold=True, vertical_align="top",
                                font_family=display_font(tokens), component_id=component_id, role="hero"))
        rows = right.split_v([1]*len(items), gap=12)
        for i, (item, row) in enumerate(zip(items, rows, strict=True)):
            idx = Frame(row.x, row.y, 58, row.height)
            body = row.inset(left=76)
            title = normalize_text(item.get("title") or item.get("headline"))
            desc = normalize_text(item.get("body") or item.get("implication"))
            elements.append(textbox(idx, f"{i+1:02d}", tokens, 22, color_key="accent", bold=True,
                                    vertical_align="top", font_family=display_font(tokens), component_id=component_id, role=f"index_{i}"))
            title_h = min(34, body.height * .30)
            tf = Frame(body.x, body.y + 8, body.width, title_h)
            df = Frame(body.x, body.y + title_h + 18, body.width, max(28, body.height - title_h - 26))
            elements.append(textbox(tf, title, tokens, 17, bold=True, vertical_align="top", component_id=component_id, role=f"title_{i}"))
            elements.append(textbox(df, desc, tokens, 13, color_key="muted", vertical_align="top", component_id=component_id, role=f"body_{i}"))
            if i < len(items)-1:
                elements.append(line(body.x, row.y + row.height + 5, body.x + body.width, row.y + row.height + 5, tokens, "line", .9, component_id=component_id, role=f"divider_{i}"))
        return elements, warnings

    if d == "technical_data":
        top_h = frame.height*.18
        top = Frame(frame.x, frame.y, frame.width, top_h)
        elements.append(shape(top, tokens, fill_key="primary", line_key=None, component_id=component_id, role="header_bg"))
        elements.append(textbox(top.inset(26, 12, 26, 12), normalize_text(content.get("headline") or "EXECUTIVE SYSTEM STATUS"), tokens,
                                20, color_key="white", bold=True, vertical_align="middle", component_id=component_id, role="headline"))
        rows = Frame(frame.x, frame.y+top_h+18, frame.width, frame.height-top_h-18).split_v([1]*len(items), gap=5)
        for i, (item, row) in enumerate(zip(items, rows, strict=True)):
            index_f, signal_f, title_f, body_f = row.split_h([.08, .10, .34, .48], gap=10)
            key = normalize_text(item.get("color_key") or ("danger" if item.get("status") == "risk" else "accent" if i == 0 else "accent2"))
            elements.append(textbox(index_f, f"S{i+1:02d}", tokens, 11, color_key="muted", bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"index_{i}"))
            elements.append(shape(signal_f.inset(8, row.height*.34, 8, row.height*.34), tokens, fill_key=key, line_key=None, component_id=component_id, role=f"signal_{i}"))
            elements.append(textbox(title_f, normalize_text(item.get("title") or item.get("headline")), tokens, 15 if variant=="dense" else 17, bold=True, vertical_align="middle", component_id=component_id, role=f"title_{i}"))
            elements.append(textbox(body_f, normalize_text(item.get("body") or item.get("implication")), tokens, 13 if variant=="dense" else 14, color_key="muted", vertical_align="middle", component_id=component_id, role=f"body_{i}"))
            elements.append(line(row.x, row.y+row.height, row.x+row.width, row.y+row.height, tokens, "line", .8, component_id=component_id, role=f"row_rule_{i}"))
        return elements, []

    # Consulting classic
    thesis = normalize_text(content.get("headline") or content.get("summary") or "Key conclusions")
    head, body = frame.split_v([.18, .82], gap=18)
    elements += _rule_label(component_id, Frame(head.x, head.y, 260, 28), "EXECUTIVE SUMMARY", tokens, "kicker")
    elements.append(textbox(head.inset(top=34), thesis, tokens, 26 if variant!="dense" else 22, color_key="primary", bold=True,
                            vertical_align="middle", component_id=component_id, role="thesis"))
    rows = body.split_v([1]*len(items), gap=0)
    for i, (item, row) in enumerate(zip(items, rows, strict=True)):
        num_f, title_f, body_f = row.split_h([.08, .36, .56], gap=16)
        key = "accent" if i == 0 else "accent2"
        elements.append(textbox(num_f, f"{i+1}", tokens, 24, color_key=key, bold=True, align="center", vertical_align="middle", component_id=component_id, role=f"index_{i}"))
        elements.append(line(num_f.x+num_f.width-4, row.y+row.height*.18, num_f.x+num_f.width-4, row.y+row.height*.82, tokens, key, 3, component_id=component_id, role=f"index_rule_{i}"))
        elements.append(textbox(title_f, normalize_text(item.get("title") or item.get("headline")), tokens, 17 if variant=="dense" else 19, bold=True, vertical_align="middle", component_id=component_id, role=f"title_{i}"))
        elements.append(textbox(body_f, normalize_text(item.get("body") or item.get("implication")), tokens, 13 if variant=="dense" else 15, color_key="muted", vertical_align="middle", component_id=component_id, role=f"body_{i}"))
        if i < len(items)-1:
            elements.append(line(row.x, row.y+row.height, row.x+row.width, row.y+row.height, tokens, "line", 1, component_id=component_id, role=f"divider_{i}"))
    return elements, []


# ---------------------------------------------------------------------------
# 2 Key Message + Evidence
# ---------------------------------------------------------------------------

def key_message_evidence(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    message = normalize_text(content.get("message") or content.get("headline"))
    evidence = list(content.get("evidence") or content.get("items") or [])
    implication = normalize_text(content.get("implication") or content.get("so_what"))
    if not message or not evidence:
        raise ValueError("narrative.key_message_evidenceにはmessageとevidenceが必要です")
    evidence = evidence[:4]
    d = _design(tokens); elements: list[dict[str, Any]] = []

    if d == "editorial_premium":
        left, right = frame.split_h([.58, .42], gap=48)
        elements += _rule_label(component_id, Frame(left.x, left.y, left.width, 30), "KEY MESSAGE", tokens, "kicker")
        msg_f = left.inset(top=52, right=28, bottom=90)
        size, warnings = _fit(message, msg_f, 42 if variant!="dense" else 34, 22, 6)
        elements.append(textbox(msg_f, message, tokens, size, color_key="primary", bold=True, vertical_align="top",
                                font_family=display_font(tokens), component_id=component_id, role="message"))
        if implication:
            elements.append(textbox(Frame(left.x, left.y+left.height-82, left.width*.9, 72), implication, tokens, 15, color_key="accent", bold=True, vertical_align="middle", component_id=component_id, role="implication"))
        rows = right.split_v([1]*len(evidence), gap=16)
        for i,(ev,row) in enumerate(zip(evidence,rows,strict=True)):
            value = normalize_text(ev.get("value")); label=normalize_text(ev.get("label")); note=normalize_text(ev.get("note"))
            elements.append(line(row.x, row.y, row.x+row.width, row.y, tokens, "line", 1, component_id=component_id, role=f"rule_{i}"))
            vf, df = row.split_h([.38,.62], gap=14)
            elements.append(textbox(vf, value, tokens, 32 if variant!="dense" else 26, color_key=("accent" if i==0 else "primary"), bold=True, vertical_align="middle", font_family=display_font(tokens), component_id=component_id, role=f"value_{i}"))
            elements.append(textbox(df, f"{{{{bold:{label}}}}}\n{note}" if note else label, tokens, 14, color_key="muted", vertical_align="middle", component_id=component_id, role=f"evidence_{i}"))
        return elements, warnings

    if d == "technical_data":
        header = Frame(frame.x, frame.y, frame.width, frame.height*.23)
        elements.append(shape(header, tokens, fill_key="surfaceAlt", line_key=None, component_id=component_id, role="message_bg"))
        elements.append(shape(Frame(header.x,header.y,10,header.height), tokens, shape_name="rectangle", fill_key="accent", line_key=None, component_id=component_id, role="message_rule"))
        elements.append(textbox(header.inset(28,12,20,12), message, tokens, 22 if variant!="dense" else 18, bold=True, vertical_align="middle", component_id=component_id, role="message"))
        grid = Frame(frame.x, header.y+header.height+18, frame.width, frame.height-header.height-18)
        cols = grid.split_h([1]*len(evidence), gap=10)
        for i,(ev,col) in enumerate(zip(evidence,cols,strict=True)):
            elements.append(shape(col,tokens,fill_key="surface",line_key="line",line_width=1,component_id=component_id,role=f"cell_{i}"))
            code_f,val_f,label_f,note_f = col.inset(14,12,14,12).split_v([.12,.38,.22,.28],gap=3)
            elements.append(textbox(code_f,f"EVID-{i+1:02d}",tokens,9,color_key="muted",bold=True,char_spacing=1.0,component_id=component_id,role=f"code_{i}"))
            elements.append(textbox(val_f,normalize_text(ev.get("value")),tokens,30 if variant!="dense" else 24,color_key=("accent" if i==0 else "accent2"),bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role=f"value_{i}"))
            elements.append(textbox(label_f,normalize_text(ev.get("label")),tokens,13,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
            elements.append(textbox(note_f,normalize_text(ev.get("note")),tokens,11,color_key="muted",vertical_align="top",component_id=component_id,role=f"note_{i}"))
        if implication:
            elements.append(textbox(Frame(frame.x,frame.y+frame.height-36,frame.width,32),implication,tokens,11,color_key="accent",bold=True,align="right",vertical_align="middle",component_id=component_id,role="implication"))
        return elements, []

    # classic
    top, bottom = frame.split_v([.34,.66], gap=20)
    msg_f, imp_f = top.split_h([.72,.28],gap=26)
    elements.append(textbox(msg_f,message,tokens,28 if variant!="dense" else 23,color_key="primary",bold=True,vertical_align="middle",component_id=component_id,role="message"))
    if implication:
        elements.append(shape(imp_f,tokens,fill_key="primary",line_key=None,text=implication,size=14,text_color_key="white",bold=True,align="left",margin=18,component_id=component_id,role="implication"))
    cols=bottom.split_h([1]*len(evidence),gap=18)
    for i,(ev,col) in enumerate(zip(evidence,cols,strict=True)):
        key="accent" if i==0 else "accent2"
        elements.append(line(col.x,col.y,col.x+col.width,col.y,tokens,key,5,component_id=component_id,role=f"top_rule_{i}"))
        val_f,label_f,note_f=col.inset(top=16).split_v([.5,.22,.28],gap=3)
        elements.append(textbox(val_f,normalize_text(ev.get("value")),tokens,36 if variant!="dense" else 29,color_key=key,bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role=f"value_{i}"))
        elements.append(textbox(label_f,normalize_text(ev.get("label")),tokens,14,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
        elements.append(textbox(note_f,normalize_text(ev.get("note")),tokens,12,color_key="muted",vertical_align="top",component_id=component_id,role=f"note_{i}"))
    return elements, []


# ---------------------------------------------------------------------------
# 3 Chart + Insight
# ---------------------------------------------------------------------------

def chart_insight(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    items = list(content.get("items") or [])
    insight = normalize_text(content.get("insight") or content.get("message"))
    sub = normalize_text(content.get("support") or content.get("note"))
    if not items:
        raise ValueError("chart.insightにはcontent.itemsが必要です")
    maxv = float(content.get("max") or max([_num(x.get("value")) or 0 for x in items] or [1]))
    d=_design(tokens); elements: list[dict[str,Any]]=[]

    def bars(area: Frame, direct: bool=False, grid: bool=False):
        els=[]; rows=area.split_v([1]*len(items),gap=10 if not grid else 4)
        for i,(item,row) in enumerate(zip(items,rows,strict=True)):
            value=_num(item.get("value")) or 0; raw=normalize_text(item.get("value")); label=normalize_text(item.get("label"))
            key=normalize_text(item.get("color_key") or ("accent" if item.get("highlight") or i==0 else "accent2"))
            lf,pf,vf=row.split_h([.28,.57,.15],gap=8)
            els.append(textbox(lf,label,tokens,12 if variant=="dense" else 14,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
            y=pf.y+pf.height*.33; h=pf.height*.34
            if grid:
                for g in range(1,5):
                    x=pf.x+pf.width*g/5; els.append(line(x,pf.y,x,pf.y+pf.height,tokens,"line",.6,component_id=component_id,role=f"grid_{i}_{g}"))
            else:
                els.append(line(pf.x,y+h/2,pf.x+pf.width,y+h/2,tokens,"line",1,component_id=component_id,role=f"base_{i}"))
            w=max(5,pf.width*min(max(value/maxv,0),1)); els.append(shape(Frame(pf.x,y,w,h),tokens,shape_name="rectangle",fill_key=key,line_key=None,component_id=component_id,role=f"bar_{i}"))
            if direct:
                els.append(textbox(Frame(pf.x+w+6,pf.y,min(90,pf.width-w),pf.height),raw,tokens,12,color_key=key,bold=True,vertical_align="middle",component_id=component_id,role=f"direct_{i}"))
            else:
                els.append(textbox(vf,raw,tokens,13,color_key=key,bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"value_{i}"))
        return els

    if d=="editorial_premium":
        top,bottom=frame.split_v([.38,.62],gap=26)
        elements+=_rule_label(component_id,Frame(top.x,top.y,240,28),"CHART INSIGHT",tokens,"kicker")
        size,warnings=_fit(insight,top.inset(top=46,right=frame.width*.22),36 if variant!="dense" else 30,20,4)
        elements.append(textbox(top.inset(top=46,right=frame.width*.22),insight,tokens,size,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="insight"))
        if sub:
            elements.append(textbox(Frame(top.x+top.width*.78,top.y+50,top.width*.22,top.height-50),sub,tokens,13,color_key="muted",vertical_align="bottom",component_id=component_id,role="support"))
        elements+=bars(bottom,direct=True)
        return elements,warnings

    if d=="technical_data":
        chart,side=frame.split_h([.72,.28],gap=18)
        elements+=bars(chart,direct=True,grid=True)
        elements.append(shape(side,tokens,fill_key="primary",line_key=None,component_id=component_id,role="insight_bg"))
        elements.append(textbox(Frame(side.x+18,side.y+16,side.width-36,24),"INTERPRETATION",tokens,9,color_key="accent",bold=True,char_spacing=1.2,component_id=component_id,role="label"))
        size,warnings=_fit(insight,side.inset(18,56,18,90),22 if variant!="dense" else 18,14,6)
        elements.append(textbox(side.inset(18,56,18,90),insight,tokens,size,color_key="white",bold=True,vertical_align="top",component_id=component_id,role="insight"))
        if sub:
            elements.append(textbox(Frame(side.x+18,side.y+side.height-80,side.width-36,64),sub,tokens,11,color_key="white",vertical_align="bottom",component_id=component_id,role="support"))
        return elements,warnings

    chart,side=frame.split_h([.67,.33],gap=34)
    elements+=bars(chart)
    elements.append(line(side.x,side.y+20,side.x,side.y+side.height-20,tokens,"accent",5,component_id=component_id,role="divider"))
    elements+=_rule_label(component_id,Frame(side.x+24,side.y,side.width-24,26),"WHAT THE DATA SAYS",tokens,"kicker")
    size,warnings=_fit(insight,side.inset(24,52,4,110),25 if variant!="dense" else 21,16,6)
    elements.append(textbox(side.inset(24,52,4,110),insight,tokens,size,color_key="primary",bold=True,vertical_align="top",component_id=component_id,role="insight"))
    if sub:
        elements.append(textbox(Frame(side.x+24,side.y+side.height-96,side.width-28,84),sub,tokens,12,color_key="muted",vertical_align="bottom",component_id=component_id,role="support"))
    return elements,warnings


# ---------------------------------------------------------------------------
# 4 Findings + Implications
# ---------------------------------------------------------------------------

def findings_implications(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    items=list(content.get("items") or [])
    if not items: raise ValueError("narrative.findings_implicationsにはcontent.itemsが必要です")
    items=items[:5]; d=_design(tokens); elements=[]
    if d=="editorial_premium":
        cols=frame.split_h([1]*len(items),gap=28)
        for i,(item,col) in enumerate(zip(items,cols,strict=True)):
            elements.append(textbox(Frame(col.x,col.y,col.width,40),f"0{i+1}",tokens,24,color_key="accent",bold=True,font_family=display_font(tokens),component_id=component_id,role=f"index_{i}"))
            elements.append(line(col.x,col.y+52,col.x+col.width,col.y+52,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            ff,imf=col.inset(top=70).split_v([.47,.53],gap=18)
            elements.append(textbox(ff,normalize_text(item.get("finding")),tokens,18 if variant!="dense" else 15,bold=True,vertical_align="top",component_id=component_id,role=f"finding_{i}"))
            elements.append(textbox(imf,normalize_text(item.get("implication")),tokens,16 if variant!="dense" else 14,color_key="accent",bold=True,vertical_align="top",component_id=component_id,role=f"implication_{i}"))
        return elements,[]
    if d=="technical_data":
        head=Frame(frame.x,frame.y,frame.width,42); body=frame.inset(top=52)
        heads=head.split_h([.08,.42,.08,.42],gap=8)
        for f,t in zip(heads,["ID","OBSERVATION","LINK","ACTION"],strict=True): elements.append(textbox(f,t,tokens,10,color_key="muted",bold=True,char_spacing=.8,vertical_align="middle",component_id=component_id,role=f"header_{t}"))
        rows=body.split_v([1]*len(items),gap=4)
        for i,(item,row) in enumerate(zip(items,rows,strict=True)):
            idx,findf,linkf,impf=row.split_h([.08,.42,.08,.42],gap=8)
            elements.append(shape(row,tokens,fill_key=("surfaceAlt" if i%2 else "surface"),line_key=None,component_id=component_id,role=f"row_bg_{i}"))
            elements.append(textbox(idx,f"F-{i+1:02d}",tokens,10,color_key="accent",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"id_{i}"))
            elements.append(textbox(findf,normalize_text(item.get("finding")),tokens,13 if variant=="dense" else 15,bold=True,vertical_align="middle",component_id=component_id,role=f"finding_{i}"))
            elements.append(line(linkf.x+5,linkf.y+linkf.height/2,linkf.x+linkf.width-5,linkf.y+linkf.height/2,tokens,"accent",2,arrow_end="triangle",component_id=component_id,role=f"arrow_{i}"))
            elements.append(textbox(impf,normalize_text(item.get("implication")),tokens,13 if variant=="dense" else 15,color_key="primary",bold=True,vertical_align="middle",component_id=component_id,role=f"implication_{i}"))
        return elements,[]
    rows=frame.split_v([1]*len(items),gap=14)
    for i,(item,row) in enumerate(zip(items,rows,strict=True)):
        findf,arrowf,impf=row.split_h([.44,.10,.46],gap=12); key="accent" if i==0 else "accent2"
        elements.append(shape(findf,tokens,fill_key="surfaceAlt",line_key=None,component_id=component_id,role=f"finding_bg_{i}"))
        elements.append(shape(Frame(findf.x,findf.y,7,findf.height),tokens,shape_name="rectangle",fill_key=key,line_key=None,component_id=component_id,role=f"rule_{i}"))
        elements.append(textbox(findf.inset(22,10,14,10),normalize_text(item.get("finding")),tokens,15 if variant=="dense" else 17,bold=True,vertical_align="middle",component_id=component_id,role=f"finding_{i}"))
        elements.append(line(arrowf.x+4,arrowf.y+arrowf.height/2,arrowf.x+arrowf.width-4,arrowf.y+arrowf.height/2,tokens,key,2.5,arrow_end="triangle",component_id=component_id,role=f"arrow_{i}"))
        elements.append(textbox(impf,normalize_text(item.get("implication")),tokens,15 if variant=="dense" else 17,color_key="primary",bold=True,vertical_align="middle",component_id=component_id,role=f"implication_{i}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 5 Strategy House
# ---------------------------------------------------------------------------

def strategy_house(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    aspiration=normalize_text(content.get("aspiration")); choices=list(content.get("choices") or []); initiatives=list(content.get("initiatives") or []); enablers=list(content.get("enablers") or []); foundation=normalize_text(content.get("foundation"))
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        top,body,bottom=frame.split_v([.25,.57,.18],gap=16)
        elements+=_rule_label(component_id,Frame(top.x,top.y,230,28),"STRATEGY ARCHITECTURE",tokens,"kicker")
        size,warnings=_fit(aspiration,top.inset(top=42,right=frame.width*.18),34 if variant!="dense" else 28,20,4)
        elements.append(textbox(top.inset(top=42,right=frame.width*.18),aspiration,tokens,size,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="aspiration"))
        cols=body.split_h([1]*max(len(choices),1),gap=28)
        for i,(choice,col) in enumerate(zip(choices,cols,strict=False)):
            elements.append(textbox(Frame(col.x,col.y,col.width,30),f"0{i+1}",tokens,17,color_key="accent",bold=True,component_id=component_id,role=f"index_{i}"))
            elements.append(line(col.x,col.y+40,col.x+col.width,col.y+40,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            tf,df=col.inset(top=56).split_v([.34,.66],gap=8)
            elements.append(textbox(tf,normalize_text(choice.get("title") if isinstance(choice,dict) else choice),tokens,19,bold=True,vertical_align="top",component_id=component_id,role=f"choice_title_{i}"))
            elements.append(textbox(df,normalize_text(choice.get("body") if isinstance(choice,dict) else ""),tokens,14,color_key="muted",vertical_align="top",component_id=component_id,role=f"choice_body_{i}"))
        bands=bottom.split_v([.52,.48],gap=6)
        if initiatives:
            segs=bands[0].split_h([1]*len(initiatives),gap=8)
            for i,(v,sf) in enumerate(zip(initiatives,segs,strict=True)): elements.append(shape(sf,tokens,fill_key="surfaceAlt",line_key=None,text=normalize_text(v),size=12,bold=True,component_id=component_id,role=f"initiative_{i}"))
        text="  •  ".join([*map(normalize_text,enablers),foundation])
        elements.append(textbox(bands[1],text,tokens,12,color_key="primary",bold=True,align="center",vertical_align="middle",component_id=component_id,role="foundation"))
        return elements,warnings
    if d=="technical_data":
        rows=frame.split_v([.18,.47,.17,.18],gap=10)
        elements.append(shape(rows[0],tokens,fill_key="primary",line_key=None,text=aspiration,size=19,text_color_key="white",bold=True,component_id=component_id,role="aspiration"))
        cols=rows[1].split_h([1]*max(len(choices),1),gap=10)
        for i,(choice,col) in enumerate(zip(choices,cols,strict=False)):
            elements.append(shape(col,tokens,fill_key="surface",line_key="accent" if i==0 else "line",line_width=1.5,component_id=component_id,role=f"choice_{i}"))
            code,tf,df=col.inset(12).split_v([.14,.28,.58],gap=3)
            elements.append(textbox(code,f"CHOICE-{i+1:02d}",tokens,8,color_key="muted",bold=True,char_spacing=.7,component_id=component_id,role=f"code_{i}"))
            elements.append(textbox(tf,normalize_text(choice.get("title") if isinstance(choice,dict) else choice),tokens,15,bold=True,vertical_align="middle",component_id=component_id,role=f"choice_title_{i}"))
            elements.append(textbox(df,normalize_text(choice.get("body") if isinstance(choice,dict) else ""),tokens,12,color_key="muted",vertical_align="top",component_id=component_id,role=f"choice_body_{i}"))
        if initiatives:
            segs=rows[2].split_h([1]*len(initiatives),gap=8)
            for i,(v,sf) in enumerate(zip(initiatives,segs,strict=True)): elements.append(shape(sf,tokens,fill_key="accent2",line_key=None,text=normalize_text(v),size=11,text_color_key="white",bold=True,component_id=component_id,role=f"initiative_{i}"))
        segs=rows[3].split_h([.7,.3],gap=8)
        elements.append(shape(segs[0],tokens,fill_key="surfaceAlt",line_key="line",text="ENABLERS  |  "+" / ".join(map(normalize_text,enablers)),size=11,bold=True,align="left",margin=14,component_id=component_id,role="enablers"))
        elements.append(shape(segs[1],tokens,fill_key="primary",line_key=None,text=foundation,size=11,text_color_key="white",bold=True,component_id=component_id,role="foundation"))
        return elements,[]
    # classic house
    roof_h=frame.height*.22; roof=Frame(frame.x+frame.width*.16,frame.y,frame.width*.68,roof_h)
    elements.append(shape(roof,tokens,shape_name="triangle",fill_key="primary",line_key=None,text=aspiration,size=20 if variant!="dense" else 17,text_color_key="white",bold=True,margin=24,component_id=component_id,role="aspiration"))
    body=Frame(frame.x+frame.width*.08,frame.y+roof_h*.72,frame.width*.84,frame.height*.56)
    cols=body.split_h([1]*max(len(choices),1),gap=14)
    for i,(choice,col) in enumerate(zip(choices,cols,strict=False)):
        elements.append(shape(col,tokens,fill_key="surface",line_key="line",shadow=shadow(tokens,"card"),component_id=component_id,role=f"choice_{i}"))
        elements.append(shape(Frame(col.x,col.y,col.width,6),tokens,shape_name="rectangle",fill_key="accent" if i==0 else "accent2",line_key=None,component_id=component_id,role=f"top_rule_{i}"))
        tf,df=col.inset(18,18,18,14).split_v([.34,.66],gap=6)
        elements.append(textbox(tf,normalize_text(choice.get("title") if isinstance(choice,dict) else choice),tokens,17,bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"choice_title_{i}"))
        elements.append(textbox(df,normalize_text(choice.get("body") if isinstance(choice,dict) else ""),tokens,13,color_key="muted",align="center",vertical_align="top",component_id=component_id,role=f"choice_body_{i}"))
    iy=body.y+body.height+10; ih=frame.height*.09
    if initiatives:
        segs=Frame(body.x,iy,body.width,ih).split_h([1]*len(initiatives),gap=8)
        for i,(v,sf) in enumerate(zip(initiatives,segs,strict=True)): elements.append(shape(sf,tokens,fill_key="surfaceAlt",line_key=None,text=normalize_text(v),size=12,bold=True,component_id=component_id,role=f"initiative_{i}"))
    ey=iy+ih+8; eh=frame.height*.075
    if enablers:
        segs=Frame(body.x,ey,body.width,eh).split_h([1]*len(enablers),gap=8)
        for i,(v,sf) in enumerate(zip(enablers,segs,strict=True)): elements.append(shape(sf,tokens,fill_key="accent2",line_key=None,text=normalize_text(v),size=11,text_color_key="white",bold=True,component_id=component_id,role=f"enabler_{i}"))
    elements.append(shape(Frame(frame.x,frame.y+frame.height*.92,frame.width,frame.height*.08),tokens,fill_key="primary",line_key=None,text=foundation,size=13,text_color_key="white",bold=True,component_id=component_id,role="foundation"))
    return elements,[]


# ---------------------------------------------------------------------------
# 6 Issue Tree
# ---------------------------------------------------------------------------

def issue_tree(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    root=normalize_text(content.get("root") or "Main question"); branches=list(content.get("branches") or [])
    if not branches: raise ValueError("strategy.issue_treeにはcontent.branchesが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        left,right=frame.split_h([.36,.64],gap=48)
        elements+=_rule_label(component_id,Frame(left.x,left.y,left.width,28),"ISSUE TREE",tokens,"kicker")
        size,warnings=_fit(root,left.inset(top=52,right=20),34 if variant!="dense" else 28,20,5)
        elements.append(textbox(left.inset(top=52,right=20),root,tokens,size,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="root"))
        cols=right.split_h([1]*len(branches),gap=28)
        for i,(br,col) in enumerate(zip(branches,cols,strict=True)):
            elements.append(textbox(Frame(col.x,col.y,col.width,32),f"0{i+1}",tokens,18,color_key="accent",bold=True,component_id=component_id,role=f"index_{i}"))
            elements.append(line(col.x,col.y+42,col.x+col.width,col.y+42,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            elements.append(textbox(Frame(col.x,col.y+58,col.width,74),normalize_text(br.get("title")),tokens,18,bold=True,vertical_align="top",component_id=component_id,role=f"branch_{i}"))
            children=list(br.get("children") or [])
            y=col.y+150
            for j,ch in enumerate(children):
                elements.append(textbox(Frame(col.x,y,col.width,48),f"— {normalize_text(ch)}",tokens,14,color_key="muted",vertical_align="top",component_id=component_id,role=f"child_{i}_{j}")); y+=56
        return elements,warnings
    if d=="technical_data":
        root_f=Frame(frame.x,frame.y+frame.height*.36,frame.width*.22,frame.height*.28)
        elements.append(shape(root_f,tokens,fill_key="primary",line_key=None,text=root,size=16,text_color_key="white",bold=True,margin=16,component_id=component_id,role="root"))
        zone=Frame(frame.x+frame.width*.30,frame.y,frame.width*.70,frame.height); rows=zone.split_v([1]*len(branches),gap=12)
        root_cx=root_f.x+root_f.width; root_cy=root_f.y+root_f.height/2
        for i,(br,row) in enumerate(zip(branches,rows,strict=True)):
            branch_f,child_zone=row.split_h([.32,.68],gap=16)
            elements.append(shape(branch_f,tokens,fill_key="surfaceAlt",line_key="accent",line_width=1.5,text=f"B{i+1:02d}  {normalize_text(br.get('title'))}",size=13,bold=True,align="left",margin=14,component_id=component_id,role=f"branch_{i}"))
            elements.append(line(root_cx,root_cy,branch_f.x,branch_f.y+branch_f.height/2,tokens,"accent",1.5,component_id=component_id,role=f"root_link_{i}"))
            children=list(br.get("children") or []); cells=child_zone.split_h([1]*max(len(children),1),gap=8)
            for j,(ch,cf) in enumerate(zip(children,cells,strict=False)):
                elements.append(shape(cf,tokens,fill_key="surface",line_key="line",text=f"L{i+1}.{j+1}\n{normalize_text(ch)}",size=11,bold=True,component_id=component_id,role=f"child_{i}_{j}"))
                elements.append(line(branch_f.x+branch_f.width,branch_f.y+branch_f.height/2,cf.x,cf.y+cf.height/2,tokens,"line",1,component_id=component_id,role=f"branch_link_{i}_{j}"))
        return elements,[]
    # classic
    root_f=Frame(frame.x,frame.y+frame.height*.34,frame.width*.23,frame.height*.32)
    elements.append(shape(root_f,tokens,fill_key="primary",line_key=None,text=root,size=18 if variant!="dense" else 15,text_color_key="white",bold=True,margin=18,shadow=shadow(tokens,"card"),component_id=component_id,role="root"))
    zone=Frame(frame.x+frame.width*.31,frame.y,frame.width*.69,frame.height); rows=zone.split_v([1]*len(branches),gap=16)
    rcx=root_f.x+root_f.width; rcy=root_f.y+root_f.height/2
    for i,(br,row) in enumerate(zip(branches,rows,strict=True)):
        bf,cz=row.split_h([.34,.66],gap=16)
        elements.append(shape(bf,tokens,fill_key="surfaceAlt",line_key=None,text=normalize_text(br.get("title")),size=15,bold=True,align="left",margin=16,component_id=component_id,role=f"branch_{i}"))
        elements.append(line(rcx,rcy,bf.x,bf.y+bf.height/2,tokens,"accent" if i==0 else "accent2",2,component_id=component_id,role=f"root_link_{i}"))
        children=list(br.get("children") or []); cells=cz.split_h([1]*max(len(children),1),gap=10)
        for j,(ch,cf) in enumerate(zip(children,cells,strict=False)):
            elements.append(shape(cf,tokens,fill_key="surface",line_key="line",text=normalize_text(ch),size=12,bold=True,component_id=component_id,role=f"child_{i}_{j}"))
            elements.append(line(bf.x+bf.width,bf.y+bf.height/2,cf.x,cf.y+cf.height/2,tokens,"line",1.2,component_id=component_id,role=f"branch_link_{i}_{j}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 7 Portfolio Matrix
# ---------------------------------------------------------------------------

def portfolio_matrix(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    items=list(content.get("items") or []); x_label=normalize_text(content.get("x_label") or "Feasibility"); y_label=normalize_text(content.get("y_label") or "Impact")
    labels=list(content.get("quadrant_labels") or ["Low priority","Quick wins","Reconsider","Strategic bets"])
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        plot=frame.inset(left=70,right=20,top=20,bottom=60)
        elements.append(shape(Frame(plot.x+plot.width/2,plot.y,plot.width/2,plot.height/2),tokens,shape_name="rectangle",fill_key="surfaceAlt",line_key=None,opacity=.65,component_id=component_id,role="highlight_zone"))
        elements.append(line(plot.x,plot.y+plot.height,plot.x+plot.width,plot.y+plot.height,tokens,"text",1.5,arrow_end="triangle",component_id=component_id,role="x_axis")); elements.append(line(plot.x,plot.y+plot.height,plot.x,plot.y,tokens,"text",1.5,arrow_end="triangle",component_id=component_id,role="y_axis"))
        elements.append(line(plot.x+plot.width/2,plot.y,plot.x+plot.width/2,plot.y+plot.height,tokens,"line",1,component_id=component_id,role="v_mid")); elements.append(line(plot.x,plot.y+plot.height/2,plot.x+plot.width,plot.y+plot.height/2,tokens,"line",1,component_id=component_id,role="h_mid"))
        qpos=[(.04,.54),(.55,.54),(.04,.03),(.55,.03)]
        for i,(qx,qy) in enumerate(qpos): elements.append(textbox(Frame(plot.x+plot.width*qx,plot.y+plot.height*qy,plot.width*.40,38),normalize_text(labels[i]),tokens,15,color_key="muted",bold=True,component_id=component_id,role=f"quad_{i}"))
        for i,item in enumerate(items):
            x=max(0,min(1,float(item.get("x",.5)))); y=max(0,min(1,float(item.get("y",.5)))); size=float(item.get("size",44)); key="accent" if item.get("highlight") else "accent2"
            px=plot.x+plot.width*x-size/2; py=plot.y+plot.height*(1-y)-size/2
            elements.append(shape(Frame(px,py,size,size),tokens,shape_name="oval",fill_key=key,line_key=None,opacity=.9,text=normalize_text(item.get("label")),size=10,text_color_key="white",bold=True,component_id=component_id,role=f"item_{i}"))
        elements.append(textbox(Frame(plot.x,plot.y+plot.height+22,plot.width,28),x_label,tokens,12,color_key="muted",bold=True,align="center",component_id=component_id,role="x_label")); elements.append(textbox(Frame(frame.x,plot.y,30,plot.height),y_label,tokens,12,color_key="muted",bold=True,align="center",vertical_align="middle",rotation=270,component_id=component_id,role="y_label"))
        return elements,[]
    if d=="technical_data":
        plot,score=frame.split_h([.77,.23],gap=22); p=plot.inset(left=52,right=16,top=18,bottom=48)
        for g in range(6):
            x=p.x+p.width*g/5; y=p.y+p.height*g/5
            elements.append(line(x,p.y,x,p.y+p.height,tokens,"line",.6,component_id=component_id,role=f"vgrid_{g}")); elements.append(line(p.x,y,p.x+p.width,y,tokens,"line",.6,component_id=component_id,role=f"hgrid_{g}"))
        elements.append(line(p.x,p.y+p.height,p.x+p.width,p.y+p.height,tokens,"primary",2,arrow_end="triangle",component_id=component_id,role="x_axis")); elements.append(line(p.x,p.y+p.height,p.x,p.y,tokens,"primary",2,arrow_end="triangle",component_id=component_id,role="y_axis"))
        ranked=sorted(items,key=lambda z:float(z.get("x",0))*float(z.get("y",0)),reverse=True)
        for i,item in enumerate(items):
            x=max(0,min(1,float(item.get("x",.5)))); y=max(0,min(1,float(item.get("y",.5)))); size=float(item.get("size",38)); key="accent" if item.get("highlight") else "accent2"
            px=p.x+p.width*x-size/2; py=p.y+p.height*(1-y)-size/2
            elements.append(shape(Frame(px,py,size,size),tokens,shape_name="oval",fill_key=key,line_key="white",line_width=1,text=normalize_text(item.get("label")),size=9,text_color_key="white",bold=True,component_id=component_id,role=f"item_{i}"))
        elements.append(textbox(Frame(p.x,p.y+p.height+16,p.width,24),x_label,tokens,10,color_key="muted",bold=True,align="center",component_id=component_id,role="x_label")); elements.append(textbox(Frame(plot.x,p.y,28,p.height),y_label,tokens,10,color_key="muted",bold=True,align="center",vertical_align="middle",rotation=270,component_id=component_id,role="y_label"))
        elements.append(shape(score,tokens,fill_key="surfaceAlt",line_key=None,component_id=component_id,role="score_bg")); elements.append(textbox(Frame(score.x+14,score.y+12,score.width-28,26),"PRIORITY SCORE",tokens,9,color_key="muted",bold=True,char_spacing=1,component_id=component_id,role="score_head"))
        rows=score.inset(14,50,14,14).split_v([1]*max(len(ranked),1),gap=5)
        for i,(item,row) in enumerate(zip(ranked,rows,strict=False)):
            s=float(item.get("x",0))*float(item.get("y",0))*100
            elements.append(textbox(Frame(row.x,row.y,row.width*.6,row.height),normalize_text(item.get("label")),tokens,11,bold=True,vertical_align="middle",component_id=component_id,role=f"score_label_{i}")); elements.append(textbox(Frame(row.x+row.width*.62,row.y,row.width*.38,row.height),f"{s:.0f}",tokens,12,color_key="accent",bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"score_{i}"))
        return elements,[]
    # classic
    plot=frame.inset(left=72,right=22,top=18,bottom=58)
    elements.append(shape(Frame(plot.x+plot.width/2,plot.y,plot.width/2,plot.height/2),tokens,shape_name="rectangle",fill_key="surfaceAlt",line_key=None,opacity=.85,component_id=component_id,role="priority_zone"))
    elements.append(line(plot.x,plot.y+plot.height,plot.x+plot.width,plot.y+plot.height,tokens,"text",2,arrow_end="triangle",component_id=component_id,role="x_axis")); elements.append(line(plot.x,plot.y+plot.height,plot.x,plot.y,tokens,"text",2,arrow_end="triangle",component_id=component_id,role="y_axis")); elements.append(line(plot.x+plot.width/2,plot.y,plot.x+plot.width/2,plot.y+plot.height,tokens,"line",1,dashed=True,component_id=component_id,role="v_mid")); elements.append(line(plot.x,plot.y+plot.height/2,plot.x+plot.width,plot.y+plot.height/2,tokens,"line",1,dashed=True,component_id=component_id,role="h_mid"))
    qpos=[(.03,.53),(.54,.53),(.03,.02),(.54,.02)]
    for i,(qx,qy) in enumerate(qpos): elements.append(textbox(Frame(plot.x+plot.width*qx,plot.y+plot.height*qy,plot.width*.42,32),normalize_text(labels[i]),tokens,12,color_key="muted",bold=True,component_id=component_id,role=f"quad_{i}"))
    for i,item in enumerate(items):
        x=max(0,min(1,float(item.get("x",.5)))); y=max(0,min(1,float(item.get("y",.5)))); size=float(item.get("size",44)); key="accent" if item.get("highlight") else "accent2"
        px=plot.x+plot.width*x-size/2; py=plot.y+plot.height*(1-y)-size/2
        elements.append(shape(Frame(px,py,size,size),tokens,shape_name="oval",fill_key=key,line_key="white",line_width=1,opacity=.9,text=normalize_text(item.get("label")),size=10,text_color_key="white",bold=True,shadow=shadow(tokens,"card") if item.get("highlight") else None,component_id=component_id,role=f"item_{i}"))
    elements.append(textbox(Frame(plot.x,plot.y+plot.height+22,plot.width,26),x_label,tokens,11,color_key="muted",bold=True,align="center",component_id=component_id,role="x_label")); elements.append(textbox(Frame(frame.x,plot.y,34,plot.height),y_label,tokens,11,color_key="muted",bold=True,align="center",vertical_align="middle",rotation=270,component_id=component_id,role="y_label"))
    return elements,[]


# ---------------------------------------------------------------------------
# 8 Capability Map
# ---------------------------------------------------------------------------

def capability_map(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    groups=list(content.get("groups") or [])
    if not groups: raise ValueError("strategy.capability_mapにはcontent.groupsが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        rows=frame.split_v([1]*len(groups),gap=16)
        for gi,(group,row) in enumerate(zip(groups,rows,strict=True)):
            label,body=row.split_h([.18,.82],gap=22)
            elements.append(textbox(label,normalize_text(group.get("title")),tokens,18,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role=f"group_{gi}"))
            elements.append(line(body.x,row.y,body.x+body.width,row.y,tokens,"line",1,component_id=component_id,role=f"rule_{gi}"))
            items=list(group.get("items") or []); cols=body.inset(top=12).split_h([1]*max(len(items),1),gap=22)
            for i,(item,col) in enumerate(zip(items,cols,strict=False)):
                mat=int(_num(item.get("maturity")) or 0)
                elements.append(textbox(Frame(col.x,col.y,col.width,44),normalize_text(item.get("label")),tokens,14,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{gi}_{i}"))
                dots=Frame(col.x,col.y+52,col.width,24).split_h([1]*5,gap=5)
                for j,df in enumerate(dots): elements.append(shape(df.inset(3,5,3,5),tokens,shape_name="oval",fill_key=("accent" if j<mat else "line"),line_key=None,component_id=component_id,role=f"dot_{gi}_{i}_{j}"))
        return elements,[]
    if d=="technical_data":
        max_items=max(len(g.get("items") or []) for g in groups); label_w=frame.width*.18; header_h=frame.height*.13
        elements.append(shape(Frame(frame.x,frame.y,label_w,header_h),tokens,fill_key="primary",line_key=None,text="CAPABILITY",size=10,text_color_key="white",bold=True,component_id=component_id,role="head_cap"))
        cols=Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*max_items,gap=3)
        for i,cf in enumerate(cols): elements.append(shape(cf,tokens,fill_key="primary",line_key=None,text=f"C{i+1:02d}",size=9,text_color_key="white",bold=True,component_id=component_id,role=f"head_{i}"))
        rows=Frame(frame.x,frame.y+header_h+4,frame.width,frame.height-header_h-4).split_v([1]*len(groups),gap=4)
        for gi,(group,row) in enumerate(zip(groups,rows,strict=True)):
            elements.append(shape(Frame(row.x,row.y,label_w,row.height),tokens,fill_key="surfaceAlt",line_key="line",text=normalize_text(group.get("title")),size=12,bold=True,align="left",margin=12,component_id=component_id,role=f"group_{gi}"))
            items=list(group.get("items") or []); cells=Frame(row.x+label_w,row.y,row.width-label_w,row.height).split_h([1]*max_items,gap=3)
            for i,cf in enumerate(cells):
                if i<len(items):
                    item=items[i]; mat=int(_num(item.get("maturity")) or 0); key="danger" if mat<=1 else "warning" if mat==2 else "success"
                    elements.append(shape(cf,tokens,fill_key=key,line_key=None,opacity=.22,text=f"{normalize_text(item.get('label'))}\nM{mat}",size=10,bold=True,component_id=component_id,role=f"cell_{gi}_{i}"))
                else: elements.append(shape(cf,tokens,fill_key="surface",line_key="line",component_id=component_id,role=f"empty_{gi}_{i}"))
        return elements,[]
    # classic columns
    cols=frame.split_h([1]*len(groups),gap=18)
    for gi,(group,col) in enumerate(zip(groups,cols,strict=True)):
        elements.append(shape(Frame(col.x,col.y,col.width,58),tokens,fill_key="primary" if gi==0 else "surfaceAlt",line_key=None,text=normalize_text(group.get("title")),size=15,text_color_key="white" if gi==0 else "primary",bold=True,component_id=component_id,role=f"group_{gi}"))
        items=list(group.get("items") or []); rows=Frame(col.x,col.y+70,col.width,col.height-70).split_v([1]*max(len(items),1),gap=10)
        for i,(item,row) in enumerate(zip(items,rows,strict=False)):
            mat=int(_num(item.get("maturity")) or 0)
            elements.append(shape(row,tokens,fill_key="surface",line_key="line",component_id=component_id,role=f"item_bg_{gi}_{i}"))
            lf,df=row.inset(14,8,14,8).split_h([.62,.38],gap=8)
            elements.append(textbox(lf,normalize_text(item.get("label")),tokens,13,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{gi}_{i}"))
            dots=df.split_h([1]*5,gap=3)
            for j,cf in enumerate(dots): elements.append(shape(cf.inset(3,cf.height*.36,3,cf.height*.36),tokens,shape_name="oval",fill_key=("accent" if j<mat else "line"),line_key=None,component_id=component_id,role=f"dot_{gi}_{i}_{j}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 9 Value Driver Tree
# ---------------------------------------------------------------------------

def value_driver_tree(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    root=normalize_text(content.get("root") or "Enterprise value"); drivers=list(content.get("drivers") or [])
    if not drivers: raise ValueError("strategy.value_driver_treeにはcontent.driversが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        left,right=frame.split_h([.32,.68],gap=44)
        elements+=_rule_label(component_id,Frame(left.x,left.y,left.width,28),"VALUE CREATION",tokens,"kicker")
        size,warnings=_fit(root,left.inset(top=56,bottom=70),36 if variant!="dense" else 30,20,5)
        elements.append(textbox(left.inset(top=56,bottom=70),root,tokens,size,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="root"))
        cols=right.split_h([1]*len(drivers),gap=26)
        for i,(drv,col) in enumerate(zip(drivers,cols,strict=True)):
            elements.append(textbox(Frame(col.x,col.y,col.width,32),f"DRIVER {i+1}",tokens,10,color_key="accent",bold=True,char_spacing=1,component_id=component_id,role=f"code_{i}")); elements.append(line(col.x,col.y+40,col.x+col.width,col.y+40,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            elements.append(textbox(Frame(col.x,col.y+56,col.width,90),normalize_text(drv.get("title")),tokens,20,bold=True,vertical_align="top",component_id=component_id,role=f"driver_{i}"))
            y=col.y+170
            for j,sub in enumerate(drv.get("subdrivers") or []): elements.append(textbox(Frame(col.x,y,col.width,52),f"+  {normalize_text(sub)}",tokens,14,color_key="muted",vertical_align="top",component_id=component_id,role=f"sub_{i}_{j}")); y+=58
        return elements,warnings
    if d=="technical_data":
        root_f=Frame(frame.x,frame.y+frame.height*.38,frame.width*.2,frame.height*.24)
        elements.append(shape(root_f,tokens,fill_key="primary",line_key=None,text=root,size=16,text_color_key="white",bold=True,component_id=component_id,role="root"))
        zone=Frame(frame.x+frame.width*.28,frame.y,frame.width*.72,frame.height); rows=zone.split_v([1]*len(drivers),gap=14)
        for i,(drv,row) in enumerate(zip(drivers,rows,strict=True)):
            df,subs=row.split_h([.35,.65],gap=14)
            elements.append(shape(df,tokens,fill_key="surfaceAlt",line_key="accent",line_width=1.5,text=f"D{i+1:02d}\n{normalize_text(drv.get('title'))}",size=13,bold=True,component_id=component_id,role=f"driver_{i}"))
            elements.append(line(root_f.x+root_f.width,root_f.y+root_f.height/2,df.x,df.y+df.height/2,tokens,"accent",1.5,component_id=component_id,role=f"root_link_{i}"))
            sublist=list(drv.get("subdrivers") or []); cells=subs.split_h([1]*max(len(sublist),1),gap=8)
            for j,(sub,cf) in enumerate(zip(sublist,cells,strict=False)):
                elements.append(shape(cf,tokens,fill_key="surface",line_key="line",text=f"D{i+1}.{j+1}\n{normalize_text(sub)}",size=10,bold=True,component_id=component_id,role=f"sub_{i}_{j}")); elements.append(line(df.x+df.width,df.y+df.height/2,cf.x,cf.y+cf.height/2,tokens,"line",1,component_id=component_id,role=f"sub_link_{i}_{j}"))
        return elements,[]
    # classic
    root_f=Frame(frame.x,frame.y+frame.height*.35,frame.width*.22,frame.height*.3)
    elements.append(shape(root_f,tokens,fill_key="primary",line_key=None,text=root,size=18,text_color_key="white",bold=True,margin=16,shadow=shadow(tokens,"card"),component_id=component_id,role="root"))
    cols=Frame(frame.x+frame.width*.31,frame.y,frame.width*.69,frame.height).split_h([1]*len(drivers),gap=18)
    for i,(drv,col) in enumerate(zip(drivers,cols,strict=True)):
        df=Frame(col.x,col.y+col.height*.12,col.width,col.height*.28)
        elements.append(shape(df,tokens,fill_key="surfaceAlt",line_key=None,text=normalize_text(drv.get("title")),size=16,bold=True,component_id=component_id,role=f"driver_{i}")); elements.append(line(root_f.x+root_f.width,root_f.y+root_f.height/2,df.x,df.y+df.height/2,tokens,"accent" if i==0 else "accent2",1.8,component_id=component_id,role=f"root_link_{i}"))
        subs=list(drv.get("subdrivers") or []); rows=Frame(col.x,col.y+col.height*.52,col.width,col.height*.42).split_v([1]*max(len(subs),1),gap=10)
        for j,(sub,row) in enumerate(zip(subs,rows,strict=False)):
            elements.append(shape(row,tokens,fill_key="surface",line_key="line",text=normalize_text(sub),size=12,bold=True,component_id=component_id,role=f"sub_{i}_{j}")); elements.append(line(df.x+df.width/2,df.y+df.height, row.x+row.width/2,row.y,tokens,"line",1,component_id=component_id,role=f"sub_link_{i}_{j}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 10 Initiative Portfolio
# ---------------------------------------------------------------------------

def initiative_portfolio(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    items=list(content.get("items") or content.get("initiatives") or [])
    if not items: raise ValueError("strategy.initiative_portfolioにはcontent.itemsが必要です")
    items=items[:6]; d=_design(tokens); elements=[]
    if d=="editorial_premium":
        hero=items[0]; left,right=frame.split_h([.48,.52],gap=42)
        elements+=_rule_label(component_id,Frame(left.x,left.y,left.width,28),"PRIORITY INITIATIVE",tokens,"kicker")
        elements.append(textbox(left.inset(top=52,bottom=160),normalize_text(hero.get("title")),tokens,32 if variant!="dense" else 26,color_key="primary",bold=True,vertical_align="top",font_family=display_font(tokens),component_id=component_id,role="hero_title"))
        elements.append(textbox(Frame(left.x,left.y+left.height-145,left.width,72),normalize_text(hero.get("description") or hero.get("body")),tokens,14,color_key="muted",vertical_align="top",component_id=component_id,role="hero_body"))
        elements.append(textbox(Frame(left.x,left.y+left.height-60,left.width,40),f"OWNER  {normalize_text(hero.get('owner'))}",tokens,11,color_key="accent",bold=True,component_id=component_id,role="hero_owner"))
        rows=right.split_v([1]*max(len(items)-1,1),gap=12)
        for i,(item,row) in enumerate(zip(items[1:],rows,strict=False),start=1):
            elements.append(line(row.x,row.y,row.x+row.width,row.y,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            idx,tf,meta=row.inset(top=8).split_h([.1,.62,.28],gap=12)
            elements.append(textbox(idx,f"{i+1:02d}",tokens,17,color_key="accent",bold=True,component_id=component_id,role=f"index_{i}")); elements.append(textbox(tf,normalize_text(item.get("title")),tokens,16,bold=True,vertical_align="middle",component_id=component_id,role=f"title_{i}")); elements.append(textbox(meta,normalize_text(item.get("owner") or item.get("status")),tokens,11,color_key="muted",bold=True,align="right",vertical_align="middle",component_id=component_id,role=f"meta_{i}"))
        return elements,[]
    if d=="technical_data":
        head=Frame(frame.x,frame.y,frame.width,42); cols=head.split_h([.08,.38,.14,.14,.14,.12],gap=4)
        for f,t in zip(cols,["ID","INITIATIVE","VALUE","EFFORT","OWNER","STATUS"],strict=True): elements.append(textbox(f,t,tokens,9,color_key="muted",bold=True,char_spacing=.6,vertical_align="middle",component_id=component_id,role=f"head_{t}"))
        rows=frame.inset(top=50).split_v([1]*len(items),gap=4)
        for i,(item,row) in enumerate(zip(items,rows,strict=True)):
            cells=row.split_h([.08,.38,.14,.14,.14,.12],gap=4); bg="surfaceAlt" if i%2 else "surface"
            elements.append(shape(row,tokens,fill_key=bg,line_key=None,component_id=component_id,role=f"row_bg_{i}"))
            values=[f"I-{i+1:02d}",normalize_text(item.get("title")),normalize_text(item.get("value") or item.get("impact")),normalize_text(item.get("effort")),normalize_text(item.get("owner")),normalize_text(item.get("status"))]
            for j,(f,v) in enumerate(zip(cells,values,strict=True)):
                key="accent" if j in {0,2} else "text"
                elements.append(textbox(f.inset(left=6,right=6),v,tokens,10 if j!=1 else 12,color_key=key,bold=j in {0,1,2},align="center" if j!=1 else "left",vertical_align="middle",component_id=component_id,role=f"cell_{i}_{j}"))
        return elements,[]
    # classic
    rows=frame.split_v([1]*len(items),gap=10)
    for i,(item,row) in enumerate(zip(items,rows,strict=True)):
        idx,titlef,valuef,effortf,ownerf,statusf=row.split_h([.08,.38,.14,.12,.16,.12],gap=10)
        elements.append(textbox(idx,f"{i+1:02d}",tokens,18,color_key="accent" if i==0 else "accent2",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"index_{i}"))
        elements.append(textbox(titlef,normalize_text(item.get("title")),tokens,15,bold=True,vertical_align="middle",component_id=component_id,role=f"title_{i}"))
        elements.append(textbox(valuef,normalize_text(item.get("value") or item.get("impact")),tokens,13,color_key="accent",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"value_{i}"))
        elements.append(textbox(effortf,normalize_text(item.get("effort")),tokens,12,color_key="muted",align="center",vertical_align="middle",component_id=component_id,role=f"effort_{i}"))
        elements.append(textbox(ownerf,normalize_text(item.get("owner")),tokens,12,color_key="muted",align="center",vertical_align="middle",component_id=component_id,role=f"owner_{i}"))
        elements.append(shape(statusf.inset(8,row.height*.27,8,row.height*.27),tokens,fill_key="surfaceAlt",line_key=None,text=normalize_text(item.get("status")),size=10,text_color_key="primary",bold=True,component_id=component_id,role=f"status_{i}"))
        elements.append(line(row.x,row.y+row.height,row.x+row.width,row.y+row.height,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 11 Roadmap
# ---------------------------------------------------------------------------

def roadmap(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    phases=list(content.get("phases") or [])
    if not phases: raise ValueError("execution.roadmapにはcontent.phasesが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        spine_x=frame.x+frame.width*.18; elements.append(line(spine_x,frame.y,spine_x,frame.y+frame.height,tokens,"accent",3,component_id=component_id,role="spine"))
        rows=frame.split_v([1]*len(phases),gap=10)
        for i,(phase,row) in enumerate(zip(phases,rows,strict=True)):
            elements.append(textbox(Frame(frame.x,row.y,frame.width*.14,row.height),normalize_text(phase.get("period")),tokens,16,color_key="accent",bold=True,align="right",vertical_align="top",font_family=display_font(tokens),component_id=component_id,role=f"period_{i}"))
            elements.append(circle(Frame(spine_x-13,row.y+12,26,26),str(i+1),tokens,"primary",component_id,f"node_{i}",9))
            body=Frame(spine_x+34,row.y,frame.x+frame.width-(spine_x+34),row.height)
            elements.append(textbox(Frame(body.x,body.y,body.width,34),normalize_text(phase.get("title")),tokens,19,bold=True,vertical_align="top",component_id=component_id,role=f"title_{i}"))
            items="  •  ".join(normalize_text(x) for x in phase.get("items") or [])
            elements.append(textbox(Frame(body.x,body.y+40,body.width,body.height-40),items,tokens,13,color_key="muted",vertical_align="top",component_id=component_id,role=f"items_{i}"))
        return elements,[]
    if d=="technical_data":
        cols=frame.split_h([1]*len(phases),gap=8)
        for i,(phase,col) in enumerate(zip(phases,cols,strict=True)):
            elements.append(shape(Frame(col.x,col.y,col.width,46),tokens,fill_key="primary" if i==0 else "accent2",line_key=None,text=f"P{i+1:02d}  {normalize_text(phase.get('period'))}",size=10,text_color_key="white",bold=True,component_id=component_id,role=f"head_{i}"))
            elements.append(shape(Frame(col.x,col.y+54,col.width,col.height-54),tokens,fill_key="surface",line_key="line",component_id=component_id,role=f"body_{i}"))
            elements.append(textbox(Frame(col.x+14,col.y+70,col.width-28,58),normalize_text(phase.get("title")),tokens,15,bold=True,vertical_align="top",component_id=component_id,role=f"title_{i}"))
            y=col.y+142
            for j,item in enumerate(phase.get("items") or []):
                elements.append(textbox(Frame(col.x+14,y,col.width-28,42),f"{j+1}. {normalize_text(item)}",tokens,11,color_key="muted",vertical_align="top",component_id=component_id,role=f"item_{i}_{j}")); y+=46
            if i<len(phases)-1: elements.append(line(col.x+col.width,col.y+col.height*.5,cols[i+1].x,cols[i+1].y+cols[i+1].height*.5,tokens,"accent",2,arrow_end="triangle",component_id=component_id,role=f"link_{i}"))
        return elements,[]
    # classic
    cols=frame.split_h([1]*len(phases),gap=12)
    for i,(phase,col) in enumerate(zip(phases,cols,strict=True)):
        if i<len(phases)-1: elements.append(line(col.x+col.width*.55,col.y+col.height*.18,cols[i+1].x+cols[i+1].width*.1,cols[i+1].y+cols[i+1].height*.18,tokens,"accent",3,arrow_end="triangle",component_id=component_id,role=f"arrow_{i}"))
        elements.append(circle(Frame(col.x+col.width*.5-24,col.y+col.height*.12-24,48,48),str(i+1),tokens,"primary" if i==0 else "accent2",component_id,f"node_{i}",13))
        elements.append(textbox(Frame(col.x,col.y+col.height*.22,col.width,36),normalize_text(phase.get("period")),tokens,11,color_key="accent",bold=True,align="center",component_id=component_id,role=f"period_{i}"))
        elements.append(textbox(Frame(col.x,col.y+col.height*.31,col.width,58),normalize_text(phase.get("title")),tokens,16,bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"title_{i}"))
        items="\n".join(f"• {normalize_text(x)}" for x in phase.get("items") or [])
        elements.append(textbox(Frame(col.x+12,col.y+col.height*.47,col.width-24,col.height*.47),items,tokens,12,color_key="muted",align="left",vertical_align="top",line_spacing_pct=112,component_id=component_id,role=f"items_{i}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 12 Gantt
# ---------------------------------------------------------------------------

def gantt(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    periods=list(content.get("periods") or []); tasks=list(content.get("tasks") or [])
    if not periods or not tasks: raise ValueError("execution.ganttにはperiodsとtasksが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        label_w=frame.width*.28; header_h=frame.height*.12
        elements.append(textbox(Frame(frame.x,frame.y,label_w,header_h),"WORKSTREAM",tokens,10,color_key="muted",bold=True,char_spacing=1,vertical_align="middle",component_id=component_id,role="header_label"))
        pfs=Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*len(periods),gap=0)
        for i,(p,pf) in enumerate(zip(periods,pfs,strict=True)): elements.append(textbox(pf,normalize_text(p),tokens,11,color_key="accent",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"period_{i}"))
        rows=Frame(frame.x,frame.y+header_h,frame.width,frame.height-header_h).split_v([1]*len(tasks),gap=5)
        for i,(task,row) in enumerate(zip(tasks,rows,strict=True)):
            elements.append(textbox(Frame(row.x,row.y,label_w-14,row.height),normalize_text(task.get("label")),tokens,13,bold=True,vertical_align="middle",component_id=component_id,role=f"label_{i}"))
            timeline=Frame(row.x+label_w,row.y,row.width-label_w,row.height)
            elements.append(line(timeline.x,row.y+row.height*.5,timeline.x+timeline.width,row.y+row.height*.5,tokens,"line",1,component_id=component_id,role=f"base_{i}"))
            start=max(0,int(task.get("start",0))); end=min(len(periods),int(task.get("end",start+1))); x=timeline.x+timeline.width*start/len(periods); w=timeline.width*max(end-start,1)/len(periods)
            elements.append(shape(Frame(x,row.y+row.height*.34,max(8,w),row.height*.32),tokens,shape_name="rectangle",fill_key="accent" if i==0 else "accent2",line_key=None,component_id=component_id,role=f"bar_{i}"))
            if task.get("milestone") is not None:
                m=int(task.get("milestone")); mx=timeline.x+timeline.width*(m+.5)/len(periods); elements.append(shape(Frame(mx-7,row.y+row.height*.5-7,14,14),tokens,shape_name="diamond",fill_key="warning",line_key=None,component_id=component_id,role=f"milestone_{i}"))
        return elements,[]
    if d=="technical_data":
        label_w=frame.width*.26; header_h=frame.height*.14
        elements.append(shape(Frame(frame.x,frame.y,label_w,header_h),tokens,fill_key="primary",line_key=None,text="TASK / MODULE",size=10,text_color_key="white",bold=True,component_id=component_id,role="head_task"))
        pfs=Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*len(periods),gap=1)
        for i,(p,pf) in enumerate(zip(periods,pfs,strict=True)): elements.append(shape(pf,tokens,fill_key="primary",line_key="white",line_width=1,text=normalize_text(p),size=10,text_color_key="white",bold=True,component_id=component_id,role=f"period_{i}"))
        rows=Frame(frame.x,frame.y+header_h+2,frame.width,frame.height-header_h-2).split_v([1]*len(tasks),gap=2)
        for i,(task,row) in enumerate(zip(tasks,rows,strict=True)):
            elements.append(shape(Frame(row.x,row.y,label_w,row.height),tokens,fill_key="surfaceAlt" if i%2 else "surface",line_key="line",text=f"T{i+1:02d}  {normalize_text(task.get('label'))}",size=10,bold=True,align="left",margin=10,component_id=component_id,role=f"label_{i}"))
            timeline=Frame(row.x+label_w,row.y,row.width-label_w,row.height); cells=timeline.split_h([1]*len(periods),gap=1)
            for j,cf in enumerate(cells): elements.append(shape(cf,tokens,shape_name="rectangle",fill_key="surfaceAlt" if i%2 else "surface",line_key="line",line_width=.6,component_id=component_id,role=f"cell_{i}_{j}"))
            start=max(0,int(task.get("start",0))); end=min(len(periods),int(task.get("end",start+1))); x=timeline.x+timeline.width*start/len(periods)+3; w=timeline.width*max(end-start,1)/len(periods)-6
            elements.append(shape(Frame(x,row.y+row.height*.28,max(6,w),row.height*.44),tokens,shape_name="rectangle",fill_key="accent" if i==0 else "accent2",line_key=None,component_id=component_id,role=f"bar_{i}"))
            if task.get("milestone") is not None:
                m=int(task.get("milestone")); mx=timeline.x+timeline.width*(m+.5)/len(periods); elements.append(shape(Frame(mx-7,row.y+row.height/2-7,14,14),tokens,shape_name="diamond",fill_key="warning",line_key=None,component_id=component_id,role=f"milestone_{i}"))
        return elements,[]
    # classic
    label_w=frame.width*.25; header_h=frame.height*.14
    elements.append(shape(Frame(frame.x,frame.y,label_w,header_h),tokens,fill_key="primary",line_key=None,text="WORKSTREAM",size=11,text_color_key="white",bold=True,component_id=component_id,role="head_task"))
    pfs=Frame(frame.x+label_w,frame.y,frame.width-label_w,header_h).split_h([1]*len(periods),gap=0)
    for i,(p,pf) in enumerate(zip(periods,pfs,strict=True)): elements.append(shape(pf,tokens,fill_key="primary",line_key="white",line_width=1,text=normalize_text(p),size=11,text_color_key="white",bold=True,component_id=component_id,role=f"period_{i}"))
    rows=Frame(frame.x,frame.y+header_h,frame.width,frame.height-header_h).split_v([1]*len(tasks),gap=0)
    for i,(task,row) in enumerate(zip(tasks,rows,strict=True)):
        elements.append(shape(Frame(row.x,row.y,label_w,row.height),tokens,shape_name="rectangle",fill_key="surfaceAlt" if i%2 else "surface",line_key="line",text=normalize_text(task.get("label")),size=12,bold=True,align="left",margin=12,component_id=component_id,role=f"label_{i}"))
        timeline=Frame(row.x+label_w,row.y,row.width-label_w,row.height); elements.append(shape(timeline,tokens,shape_name="rectangle",fill_key="surfaceAlt" if i%2 else "surface",line_key="line",component_id=component_id,role=f"timeline_{i}"))
        for p in range(1,len(periods)):
            x=timeline.x+timeline.width*p/len(periods); elements.append(line(x,timeline.y,x,timeline.y+timeline.height,tokens,"line",1,component_id=component_id,role=f"grid_{i}_{p}"))
        start=max(0,int(task.get("start",0))); end=min(len(periods),int(task.get("end",start+1))); x=timeline.x+timeline.width*start/len(periods)+5; w=timeline.width*max(end-start,1)/len(periods)-10
        elements.append(shape(Frame(x,row.y+row.height*.29,max(8,w),row.height*.42),tokens,shape_name="rectangle",fill_key="accent" if i==0 else "accent2",line_key=None,component_id=component_id,role=f"bar_{i}"))
        if task.get("milestone") is not None:
            m=int(task.get("milestone")); mx=timeline.x+timeline.width*(m+.5)/len(periods); elements.append(shape(Frame(mx-8,row.y+row.height/2-8,16,16),tokens,shape_name="diamond",fill_key="warning",line_key=None,component_id=component_id,role=f"milestone_{i}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 13 Governance
# ---------------------------------------------------------------------------

def governance(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    levels=list(content.get("levels") or [])
    if not levels: raise ValueError("execution.governanceにはcontent.levelsが必要です")
    d=_design(tokens); elements=[]
    if d=="editorial_premium":
        main=levels[0]; left,right=frame.split_h([.47,.53],gap=42)
        elements+=_rule_label(component_id,Frame(left.x,left.y,left.width,28),"GOVERNANCE",tokens,"kicker")
        elements.append(textbox(left.inset(top=54,bottom=130),normalize_text(main.get("title")),tokens,32 if variant!="dense" else 26,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="main_title"))
        elements.append(textbox(Frame(left.x,left.y+left.height-120,left.width,50),normalize_text(main.get("detail")),tokens,14,color_key="accent",bold=True,component_id=component_id,role="main_detail"))
        rows=right.split_v([1]*max(len(levels)-1,1),gap=16)
        for i,(level,row) in enumerate(zip(levels[1:],rows,strict=False),start=1):
            elements.append(line(row.x,row.y,row.x+row.width,row.y,tokens,"line",1,component_id=component_id,role=f"rule_{i}"))
            tf,df=row.inset(top=12).split_h([.56,.44],gap=16)
            elements.append(textbox(tf,normalize_text(level.get("title")),tokens,18,bold=True,vertical_align="middle",component_id=component_id,role=f"title_{i}")); elements.append(textbox(df,normalize_text(level.get("detail")),tokens,13,color_key="muted",align="right",vertical_align="middle",component_id=component_id,role=f"detail_{i}"))
        return elements,[]
    if d=="technical_data":
        rows=frame.split_v([1]*len(levels),gap=14); center=frame.x+frame.width*.48
        for i,(level,row) in enumerate(zip(levels,rows,strict=True)):
            code=Frame(row.x,row.y,row.width*.14,row.height); node=Frame(row.x+row.width*.2,row.y,row.width*.48,row.height); meta=Frame(row.x+row.width*.72,row.y,row.width*.28,row.height)
            key="primary" if i==0 else "accent" if i==1 else "accent2"
            elements.append(textbox(code,f"GOV-{i+1:02d}",tokens,10,color_key="muted",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"code_{i}")); elements.append(shape(node,tokens,fill_key=key if i<2 else "surface",line_key=None if i<2 else key,text=normalize_text(level.get("title")),size=15,text_color_key="white" if i<2 else "text",bold=True,component_id=component_id,role=f"node_{i}")); elements.append(textbox(meta,normalize_text(level.get("detail")),tokens,11,color_key="muted",align="right",vertical_align="middle",component_id=component_id,role=f"detail_{i}"))
            if i<len(levels)-1: elements.append(line(center,node.y+node.height,center,rows[i+1].y,tokens,"accent",1.5,arrow_end="triangle",component_id=component_id,role=f"link_{i}"))
        return elements,[]
    # classic tiers
    rows=frame.split_v([1]*len(levels),gap=18); widths=[.66,.76,.86,.94]
    for i,(level,row) in enumerate(zip(levels,rows,strict=True)):
        w=row.width*widths[min(i,len(widths)-1)]; box=Frame(row.x+(row.width-w)/2,row.y,w,row.height); key="primary" if i==0 else "accent" if i==1 else "accent2"
        elements.append(shape(box,tokens,fill_key=key if i<2 else "surface",line_key=None if i<2 else key,line_width=1.5,text=normalize_text(level.get("title")),size=17,text_color_key="white" if i<2 else "text",bold=True,margin=18,shadow=shadow(tokens,"card") if i==0 else None,component_id=component_id,role=f"level_{i}"))
        if level.get("detail"): elements.append(textbox(Frame(box.x+box.width*.55,box.y,box.width*.42,box.height),normalize_text(level.get("detail")),tokens,12,color_key="white" if i<2 else "muted",align="right",vertical_align="middle",component_id=component_id,role=f"detail_{i}"))
        if i<len(levels)-1: elements.append(line(frame.x+frame.width/2,box.y+box.height,frame.x+frame.width/2,rows[i+1].y,tokens,"accent",2,arrow_end="triangle",component_id=component_id,role=f"link_{i}"))
    return elements,[]


# ---------------------------------------------------------------------------
# 14 KPI Cascade
# ---------------------------------------------------------------------------

def kpi_cascade(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    top=content.get("top") or {}; levels=list(content.get("levels") or []); d=_design(tokens); elements=[]
    if d=="editorial_premium":
        hero=Frame(frame.x,frame.y,frame.width*.38,frame.height)
        elements+=_rule_label(component_id,Frame(hero.x,hero.y,hero.width,28),"KPI CASCADE",tokens,"kicker")
        value=normalize_text(top.get("value")); label=normalize_text(top.get("label"))
        elements.append(textbox(Frame(hero.x,hero.y+58,hero.width,160),value,tokens,58 if variant!="dense" else 48,color_key="accent",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="top_value")); elements.append(textbox(Frame(hero.x,hero.y+220,hero.width,70),label,tokens,18,color_key="primary",bold=True,vertical_align="top",component_id=component_id,role="top_label"))
        right=Frame(frame.x+frame.width*.43,frame.y,frame.width*.57,frame.height); rows=right.split_v([1]*max(len(levels),1),gap=20)
        for li,(level,row) in enumerate(zip(levels,rows,strict=False)):
            items=list(level.get("items") or []); cols=row.split_h([1]*max(len(items),1),gap=22)
            for i,(item,col) in enumerate(zip(items,cols,strict=False)):
                elements.append(line(col.x,col.y,col.x+col.width,col.y,tokens,"line",1,component_id=component_id,role=f"rule_{li}_{i}")); vf,lf=col.inset(top=12).split_v([.58,.42],gap=2); elements.append(textbox(vf,normalize_text(item.get("value")),tokens,28,color_key="accent" if li==0 else "accent2",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role=f"value_{li}_{i}")); elements.append(textbox(lf,normalize_text(item.get("label")),tokens,13,color_key="muted",bold=True,vertical_align="top",component_id=component_id,role=f"label_{li}_{i}"))
        return elements,[]
    if d=="technical_data":
        top_f=Frame(frame.x+frame.width*.32,frame.y,frame.width*.36,frame.height*.18); elements.append(shape(top_f,tokens,fill_key="primary",line_key=None,text=f"{normalize_text(top.get('value'))}\n{normalize_text(top.get('label'))}",size=16,text_color_key="white",bold=True,component_id=component_id,role="top"))
        y=top_f.y+top_f.height+22
        for li,level in enumerate(levels):
            items=list(level.get("items") or []); band=Frame(frame.x,y,frame.width,(frame.height-(y-frame.y)-10)/max(len(levels)-li,1)-8); cells=band.split_h([1]*max(len(items),1),gap=10)
            for i,(item,cf) in enumerate(zip(items,cells,strict=False)):
                code=f"K{li+1}.{i+1}"; elements.append(shape(cf,tokens,fill_key="surface",line_key="accent" if li==0 else "line",line_width=1.2,component_id=component_id,role=f"cell_{li}_{i}")); elements.append(textbox(Frame(cf.x+10,cf.y+8,cf.width-20,18),code,tokens,8,color_key="muted",bold=True,char_spacing=.6,component_id=component_id,role=f"code_{li}_{i}")); elements.append(textbox(Frame(cf.x+10,cf.y+28,cf.width-20,36),normalize_text(item.get("value")),tokens,21,color_key="accent" if li==0 else "accent2",bold=True,component_id=component_id,role=f"value_{li}_{i}")); elements.append(textbox(Frame(cf.x+10,cf.y+66,cf.width-20,cf.height-74),normalize_text(item.get("label")),tokens,11,color_key="muted",bold=True,vertical_align="top",component_id=component_id,role=f"label_{li}_{i}")); parent_x=top_f.x+top_f.width/2 if li==0 else cf.x+cf.width/2; elements.append(line(parent_x,y-22,cf.x+cf.width/2,cf.y,tokens,"line",1,component_id=component_id,role=f"link_{li}_{i}"))
            y=band.y+band.height+16
        return elements,[]
    # classic tree
    top_f=Frame(frame.x+frame.width*.28,frame.y,frame.width*.44,frame.height*.2); elements.append(shape(top_f,tokens,fill_key="primary",line_key=None,text=f"{normalize_text(top.get('value'))}\n{normalize_text(top.get('label'))}",size=18,text_color_key="white",bold=True,margin=14,shadow=shadow(tokens,"hero"),component_id=component_id,role="top")); current_y=top_f.y+top_f.height
    for li,level in enumerate(levels):
        items=list(level.get("items") or []); band_h=(frame.height-top_f.height-20)/max(len(levels),1)-12; band=Frame(frame.x,current_y+18,frame.width,band_h); cells=band.split_h([1]*max(len(items),1),gap=14)
        for i,(item,cf) in enumerate(zip(items,cells,strict=False)):
            key="accent" if li==0 else "accent2"; elements.append(shape(cf,tokens,fill_key="surface",line_key=key,line_width=1.5,text=f"{normalize_text(item.get('value'))}\n{normalize_text(item.get('label'))}",size=15,bold=True,margin=12,component_id=component_id,role=f"item_{li}_{i}")); parent_cx=top_f.x+top_f.width/2 if li==0 else frame.x+frame.width*(i+.5)/max(len(items),1); elements.append(line(parent_cx,current_y,cf.x+cf.width/2,cf.y,tokens,"line",1.5,component_id=component_id,role=f"connector_{li}_{i}"))
        current_y=band.y+band.height
    return elements,[]


# ---------------------------------------------------------------------------
# 15 Decision / Recommendation
# ---------------------------------------------------------------------------

def recommendation_actions(component_id: str, frame: Frame, content: dict[str, Any], tokens: dict[str, Any], variant: str):
    rec=normalize_text(content.get("recommendation")); actions=list(content.get("actions") or []); decision=normalize_text(content.get("decision") or content.get("ask")); d=_design(tokens); elements=[]
    if d=="editorial_premium":
        elements+=_rule_label(component_id,Frame(frame.x,frame.y,250,28),"RECOMMENDATION",tokens,"kicker")
        top,bottom=frame.inset(top=50).split_v([.57,.43],gap=20)
        size,warnings=_fit(rec,top.inset(right=frame.width*.16),38 if variant!="dense" else 31,20,5)
        elements.append(textbox(top.inset(right=frame.width*.16),rec,tokens,size,color_key="primary",bold=True,vertical_align="middle",font_family=display_font(tokens),component_id=component_id,role="recommendation"))
        cols=bottom.split_h([1]*max(len(actions),1),gap=24)
        for i,(action,col) in enumerate(zip(actions,cols,strict=False)):
            elements.append(textbox(Frame(col.x,col.y,col.width,32),f"0{i+1}",tokens,18,color_key="accent",bold=True,component_id=component_id,role=f"index_{i}")); elements.append(line(col.x,col.y+42,col.x+col.width,col.y+42,tokens,"line",1,component_id=component_id,role=f"rule_{i}")); txt=normalize_text(action.get("text") if isinstance(action,dict) else action); elements.append(textbox(Frame(col.x,col.y+58,col.width,col.height-58),txt,tokens,15,bold=True,vertical_align="top",component_id=component_id,role=f"action_{i}"))
        if decision: elements.append(textbox(Frame(frame.x+frame.width*.73,frame.y+8,frame.width*.27,30),decision,tokens,11,color_key="accent",bold=True,align="right",component_id=component_id,role="decision"))
        return elements,warnings
    if d=="technical_data":
        left,right=frame.split_h([.58,.42],gap=20)
        elements.append(shape(left,tokens,fill_key="primary",line_key=None,component_id=component_id,role="rec_bg")); elements.append(textbox(Frame(left.x+20,left.y+16,left.width-40,24),"DECISION PACKAGE",tokens,9,color_key="accent",bold=True,char_spacing=1,component_id=component_id,role="label")); size,warnings=_fit(rec,left.inset(22,54,22,80),24 if variant!="dense" else 20,15,6); elements.append(textbox(left.inset(22,54,22,80),rec,tokens,size,color_key="white",bold=True,vertical_align="top",component_id=component_id,role="recommendation")); elements.append(textbox(Frame(left.x+22,left.y+left.height-62,left.width-44,46),decision,tokens,12,color_key="accent",bold=True,vertical_align="middle",component_id=component_id,role="decision"))
        rows=right.split_v([1]*max(len(actions),1),gap=8)
        for i,(action,row) in enumerate(zip(actions,rows,strict=False)):
            elements.append(shape(row,tokens,fill_key="surfaceAlt",line_key="line",component_id=component_id,role=f"action_bg_{i}")); elements.append(textbox(Frame(row.x+12,row.y,row.width*.14,row.height),f"A{i+1:02d}",tokens,10,color_key="accent",bold=True,align="center",vertical_align="middle",component_id=component_id,role=f"index_{i}")); elements.append(textbox(Frame(row.x+row.width*.18,row.y,row.width*.78,row.height),normalize_text(action.get("text") if isinstance(action,dict) else action),tokens,13,bold=True,vertical_align="middle",component_id=component_id,role=f"action_{i}"))
        return elements,warnings
    # classic
    left,right=frame.split_h([.62,.38],gap=34); elements.append(shape(left,tokens,fill_key="primary",line_key=None,shadow=shadow(tokens,"hero"),component_id=component_id,role="recommendation_bg")); inner=left.inset(34,28,34,28); elements.append(textbox(Frame(inner.x,inner.y,inner.width,28),"RECOMMENDATION",tokens,12,color_key="accent",bold=True,char_spacing=1.8,vertical_align="middle",component_id=component_id,role="label")); size,warnings=_fit(rec,inner.inset(top=42,bottom=46),30 if variant!="dense" else 24,17,5); elements.append(textbox(inner.inset(top=42,bottom=46),rec,tokens,size,color_key="white",bold=True,vertical_align="middle",component_id=component_id,role="recommendation"));
    if decision: elements.append(textbox(Frame(inner.x,inner.y+inner.height-34,inner.width,28),decision,tokens,11,color_key="accent",bold=True,component_id=component_id,role="decision"))
    rows=right.split_v([1]*max(len(actions),1),gap=12)
    for i,(action,row) in enumerate(zip(actions,rows,strict=False)):
        key="accent" if i==0 else "accent2"; elements.append(circle(Frame(row.x,row.y+row.height/2-19,38,38),str(i+1),tokens,key,component_id,f"index_{i}",12)); elements.append(textbox(row.inset(left=54,right=4),normalize_text(action.get("text") if isinstance(action,dict) else action),tokens,16 if variant!="dense" else 14,bold=True,vertical_align="middle",component_id=component_id,role=f"action_{i}"));
        if i<len(actions)-1: elements.append(line(row.x+54,row.y+row.height,row.x+row.width,row.y+row.height,tokens,"line",1,component_id=component_id,role=f"divider_{i}"))
    return elements,warnings


PREMIUM_BUILDERS: dict[str, Builder] = {
    "narrative.executive_summary": executive_summary,
    "narrative.key_message_evidence": key_message_evidence,
    "chart.insight": chart_insight,
    "narrative.findings_implications": findings_implications,
    "strategy.house": strategy_house,
    "strategy.issue_tree": issue_tree,
    "strategy.portfolio_matrix": portfolio_matrix,
    "strategy.prioritization_matrix": portfolio_matrix,
    "strategy.capability_map": capability_map,
    "strategy.value_driver_tree": value_driver_tree,
    "strategy.initiative_portfolio": initiative_portfolio,
    "execution.roadmap": roadmap,
    "execution.gantt": gantt,
    "execution.governance": governance,
    "execution.kpi_cascade": kpi_cascade,
    "narrative.recommendation_actions": recommendation_actions,
}
