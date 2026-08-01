from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Frame:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Frame":
        required = ("x", "y", "width", "height")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"frameに必須項目がありません: {', '.join(missing)}")
        frame = cls(*(float(value[key]) for key in required))
        if frame.width <= 0 or frame.height <= 0:
            raise ValueError("frame.widthとframe.heightは正数にしてください")
        return frame

    def inset(self, left: float = 0, top: float = 0, right: float = 0, bottom: float = 0) -> "Frame":
        return Frame(
            self.x + left,
            self.y + top,
            max(1.0, self.width - left - right),
            max(1.0, self.height - top - bottom),
        )

    def split_h(self, ratios: list[float], gap: float = 0) -> list["Frame"]:
        if not ratios or any(r <= 0 for r in ratios):
            raise ValueError("ratiosは正数の配列にしてください")
        available = self.width - gap * (len(ratios) - 1)
        total = sum(ratios)
        cursor = self.x
        result: list[Frame] = []
        for ratio in ratios:
            width = available * ratio / total
            result.append(Frame(cursor, self.y, width, self.height))
            cursor += width + gap
        return result

    def split_v(self, ratios: list[float], gap: float = 0) -> list["Frame"]:
        if not ratios or any(r <= 0 for r in ratios):
            raise ValueError("ratiosは正数の配列にしてください")
        available = self.height - gap * (len(ratios) - 1)
        total = sum(ratios)
        cursor = self.y
        result: list[Frame] = []
        for ratio in ratios:
            height = available * ratio / total
            result.append(Frame(self.x, cursor, self.width, height))
            cursor += height + gap
        return result

    def as_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 2), "y": round(self.y, 2), "width": round(self.width, 2), "height": round(self.height, 2)}


@dataclass
class ComponentResult:
    elements: list[dict[str, Any]]
    component_id: str
    variant: str
    theme: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "elements": self.elements,
            "warnings": self.warnings,
            "metadata": {
                "component_id": self.component_id,
                "variant": self.variant,
                "theme": self.theme,
                **self.metadata,
            },
        }
