from __future__ import annotations

from pathlib import Path
from typing import Any

from .components import BUILDERS
from .models import ComponentResult, Frame
from .theme import load_theme

SUPPORTED_VARIANTS = {"primary", "alternate", "dense"}

# V8で公開済みのIDを残しつつ、v4の実装へ安全に移行する。
# 呼び出し側では旧IDをそのまま使用でき、生成要素には移行先を
# sourceComponentIdとして残す。
COMPONENT_ALIASES = {
    "chart.highlight_bar": "chart.insight",
    "chart.trend_line": "chart.line_forecast",
    "process.stage": "process.stage_flow",
    "synthesis.spine": "synthesis.causal_spine",
    "synthesis.system_map": "framework.hub_spoke",
}


def build_component(
    component_id: str,
    frame: dict[str, Any] | Frame,
    content: dict[str, Any] | None = None,
    *,
    theme: str = "base",
    variant: str = "primary",
    token_overrides: dict[str, Any] | None = None,
    token_dir: Path | None = None,
    layout_slot: str | None = None,
) -> ComponentResult:
    resolved_component_id = COMPONENT_ALIASES.get(component_id, component_id)
    if resolved_component_id not in BUILDERS:
        raise ValueError(f"未対応componentです: {component_id}")
    if variant not in SUPPORTED_VARIANTS:
        raise ValueError(f"未対応variantです: {variant}. supported={sorted(SUPPORTED_VARIANTS)}")
    resolved_frame = frame if isinstance(frame, Frame) else Frame.from_dict(frame)
    tokens = load_theme(theme, token_overrides, token_dir)
    elements, warnings = BUILDERS[resolved_component_id](
        resolved_component_id, resolved_frame, content or {}, tokens, variant
    )
    # 複合部品の内部で再利用したPrimitive/Componentを、呼び出し元の部品として監査できるよう統一する。
    for element in elements:
        original = element.get("componentId")
        if original and original != component_id:
            element["sourceComponentId"] = original
        element["componentId"] = component_id
        element["componentFrame"] = resolved_frame.as_dict()
        if layout_slot:
            element["layoutSlot"] = layout_slot
    return ComponentResult(
        elements=elements,
        component_id=component_id,
        variant=variant,
        theme=theme,
        warnings=warnings,
        metadata={
            "editable": True,
            "element_count": len(elements),
            "library_version": "4.1.0-sdpm-v9",
            "resolved_component_id": resolved_component_id,
            "legacy_alias": component_id in COMPONENT_ALIASES,
        },
    )


def list_components() -> list[str]:
    return sorted(set(BUILDERS) | set(COMPONENT_ALIASES))
