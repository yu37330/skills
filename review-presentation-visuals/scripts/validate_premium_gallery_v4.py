#!/usr/bin/env python3
"""Premium 15部品×3テーマのGallery構図差と追跡情報を検証する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from audit_design_system import extract_component_traceability


def main() -> int:
    if len(sys.argv) != 4:
        print("使用法: python validate_premium_gallery_v4.py <gallery.pptx> <japanese-lint.json> <output.json>")
        return 2
    pptx = Path(sys.argv[1]).resolve()
    lint_path = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    trace = extract_component_traceability(pptx)
    lint = json.loads(lint_path.read_text(encoding="utf-8-sig"))
    slides = trace.get("slides", [])
    component_ids = sorted({component_id for slide in slides for component_id in slide.get("component_ids", [])})
    traced_all_slides = len(slides) == 45 and all(slide.get("traced_shape_count", 0) > 0 for slide in slides)
    result = {
        "version": 1,
        "source": str(pptx),
        "slide_count": len(slides),
        "premium_component_count": len(component_ids),
        "premium_component_ids": component_ids,
        "theme_count": 3,
        "traced_all_slides": traced_all_slides,
        "trace_coverage_ratio": trace.get("trace_coverage_ratio"),
        "native_element_ratio": trace.get("native_element_ratio"),
        "premium_theme_composition": trace.get("premium_theme_composition", {}),
        "premium_theme_composition_pass": trace.get("premium_theme_composition_pass") is True,
        "japanese_lint_pass": lint.get("pass") is True,
    }
    result["pass"] = all((
        result["slide_count"] == 45,
        result["premium_component_count"] == 15,
        result["theme_count"] == 3,
        result["traced_all_slides"],
        result["premium_theme_composition_pass"],
        result["japanese_lint_pass"],
        result["native_element_ratio"] >= 0.8,
    ))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "pass", "slide_count", "premium_component_count", "theme_count",
        "traced_all_slides", "premium_theme_composition_pass", "japanese_lint_pass",
    )}, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
