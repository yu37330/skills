from __future__ import annotations

from typing import Any

from .models import Frame
from .theme import color, font


def with_meta(element: dict[str, Any], component_id: str, role: str) -> dict[str, Any]:
    element["componentId"] = component_id
    element["componentRole"] = role
    return element


def textbox(
    frame: Frame,
    text: str,
    tokens: dict[str, Any],
    size: int,
    color_key: str = "text",
    bold: bool = False,
    align: str = "left",
    vertical_align: str = "top",
    margin: float = 0,
    component_id: str = "",
    role: str = "text",
    font_color: str | None = None,
    line_spacing_pct: int | None = None,
    fill: str | None = None,
    opacity: float | None = None,
    rotation: float = 0,
    font_family: str | None = None,
    italic: bool = False,
    shadow: str | dict[str, Any] | None = None,
    char_spacing: float | None = None,
) -> dict[str, Any]:
    size = max(12, size)
    element: dict[str, Any] = {
        "type": "textbox",
        **frame.as_dict(),
        "text": text,
        "fontSize": size,
        "fontFamily": font_family or font(tokens),
        "fontColor": font_color or color(tokens, color_key),
        "bold": bold,
        "italic": italic,
        "align": align,
        "verticalAlign": vertical_align,
        "marginLeft": margin,
        "marginRight": margin,
        "marginTop": margin,
        "marginBottom": margin,
    }
    if line_spacing_pct is not None:
        element["lineSpacingPct"] = line_spacing_pct
    if fill is not None:
        element["fill"] = fill
    if opacity is not None:
        element["opacity"] = opacity
    if rotation:
        element["rotation"] = rotation
    if shadow:
        element["shadow"] = shadow
    if char_spacing is not None:
        element["charSpacing"] = char_spacing
    return with_meta(element, component_id, role)


def shape(
    frame: Frame,
    tokens: dict[str, Any],
    shape_name: str = "rounded_rectangle",
    fill_key: str = "surface",
    line_key: str | None = "line",
    line_width: float | None = None,
    text: str = "",
    size: int = 16,
    text_color_key: str = "text",
    bold: bool = False,
    align: str = "center",
    vertical_align: str = "middle",
    margin: float = 8,
    component_id: str = "",
    role: str = "shape",
    fill: str | None = None,
    line: str | None = None,
    font_color: str | None = None,
    gradient: dict[str, Any] | None = None,
    opacity: float | None = None,
    shadow: str | dict[str, Any] | None = None,
    rotation: float = 0,
) -> dict[str, Any]:
    size = max(12, size)
    element: dict[str, Any] = {
        "type": "shape",
        "shape": shape_name,
        **frame.as_dict(),
        "fill": fill or color(tokens, fill_key),
        "line": line if line is not None else (color(tokens, line_key) if line_key else "none"),
        "lineWidth": line_width if line_width is not None else tokens.get("shape", {}).get("lineWidth", 1),
        "text": text,
        "fontSize": size,
        "fontFamily": font(tokens),
        "fontColor": font_color or color(tokens, text_color_key),
        "bold": bold,
        "align": align,
        "verticalAlign": vertical_align,
        "marginLeft": margin,
        "marginRight": margin,
        "marginTop": margin,
        "marginBottom": margin,
    }
    if gradient:
        element["gradient"] = gradient
    if opacity is not None:
        element["opacity"] = opacity
    if shadow:
        element["shadow"] = shadow
    if rotation:
        element["rotation"] = rotation
    return with_meta(element, component_id, role)


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    tokens: dict[str, Any],
    color_key: str = "line",
    width: float = 1.5,
    arrow_end: str | None = None,
    dashed: bool = False,
    component_id: str = "",
    role: str = "line",
    color_value: str | None = None,
    opacity: float | None = None,
) -> dict[str, Any]:
    element: dict[str, Any] = {
        "type": "line",
        "x1": round(x1, 2), "y1": round(y1, 2), "x2": round(x2, 2), "y2": round(y2, 2),
        "color": color_value or color(tokens, color_key),
        "lineWidth": width,
    }
    if arrow_end:
        element["arrowEnd"] = arrow_end
    if dashed:
        element["dash"] = "dash"
    if opacity is not None:
        element["lineOpacity"] = opacity
    return with_meta(element, component_id, role)


def pill(frame: Frame, text: str, tokens: dict[str, Any], fill_key: str, text_color: str, component_id: str, role: str, size: int = 13) -> dict[str, Any]:
    return shape(
        frame, tokens, shape_name="rounded_rectangle", fill_key=fill_key, line_key=None,
        text=text, size=size, bold=True, margin=4, component_id=component_id, role=role,
        font_color=text_color,
    )


def circle(frame: Frame, text: str, tokens: dict[str, Any], fill_key: str, component_id: str, role: str, size: int = 16, font_color: str = "#FFFFFF", line_key: str | None = None) -> dict[str, Any]:
    side = min(frame.width, frame.height)
    centered = Frame(frame.x + (frame.width - side) / 2, frame.y + (frame.height - side) / 2, side, side)
    return shape(
        centered, tokens, shape_name="oval", fill_key=fill_key, line_key=line_key,
        text=text, size=size, bold=True, margin=2, component_id=component_id, role=role,
        font_color=font_color,
    )


def gradient(stops: list[tuple[float, str, float | None]], angle: float = 0) -> dict[str, Any]:
    return {
        "type": "linear",
        "angle": angle,
        "stops": [
            {"position": pos, "color": col, **({"opacity": opacity} if opacity is not None else {})}
            for pos, col, opacity in stops
        ],
    }
