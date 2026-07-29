#!/usr/bin/env python3
"""One-pager Specを標準ライブラリだけで検証する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED = {
    "spec_version", "title", "core_message", "audience", "purpose", "language",
    "source", "canvas", "visual_direction", "reading_order", "modules", "footer",
    "assumptions",
}
EVIDENCE_TYPES = {"fact", "consensus", "insight", "caution"}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["ルートはJSONオブジェクトである必要があります。"], warnings

    missing = sorted(REQUIRED - data.keys())
    if missing:
        errors.append(f"必須フィールドがありません: {', '.join(missing)}")

    for key in ("title", "core_message", "audience", "purpose", "language"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            errors.append(f"{key} は空でない文字列にしてください。")

    message = data.get("core_message", "")
    if isinstance(message, str) and len(message) > 120:
        warnings.append("core_message が120文字を超えています。1文へ圧縮してください。")

    canvas = data.get("canvas")
    safe_margin = 0.0
    canvas_width = canvas_height = 0.0
    if not isinstance(canvas, dict):
        errors.append("canvas はオブジェクトにしてください。")
    else:
        for key in ("width", "height", "safe_margin"):
            if not is_number(canvas.get(key)):
                errors.append(f"canvas.{key} は数値にしてください。")
        if is_number(canvas.get("width")):
            canvas_width = float(canvas["width"])
            if not 800 <= canvas_width <= 4000:
                errors.append("canvas.width は800〜4000にしてください。")
        if is_number(canvas.get("height")):
            canvas_height = float(canvas["height"])
            if not 600 <= canvas_height <= 4000:
                errors.append("canvas.height は600〜4000にしてください。")
        if is_number(canvas.get("safe_margin")):
            safe_margin = float(canvas["safe_margin"])
            if safe_margin < 16:
                errors.append("canvas.safe_margin は16以上にしてください。")

    visual = data.get("visual_direction")
    style_name = ""
    if not isinstance(visual, dict):
        errors.append("visual_direction はオブジェクトにしてください。")
    else:
        style_name = visual.get("style", "") if isinstance(visual.get("style"), str) else ""
        for key in ("layout", "style", "density", "palette", "typography"):
            if key not in visual:
                errors.append(f"visual_direction.{key} がありません。")

    if style_name == "editorial-knowledge-map":
        narrative = data.get("narrative")
        if not isinstance(narrative, dict):
            errors.append("editorial-knowledge-map では narrative が必要です。")
        else:
            for key in ("archetype", "opening_thesis", "closing_thesis", "tensions"):
                if key not in narrative:
                    errors.append(f"narrative.{key} がありません。")
            for key in ("archetype", "opening_thesis", "closing_thesis"):
                if key in narrative and (not isinstance(narrative[key], str) or not narrative[key].strip()):
                    errors.append(f"narrative.{key} は空でない文字列にしてください。")
            if "tensions" in narrative and not isinstance(narrative["tensions"], list):
                errors.append("narrative.tensions は配列にしてください。")

        if isinstance(visual, dict):
            palette = visual.get("palette")
            required_colors = {"background", "surface", "navy", "blue", "teal", "gold", "text", "muted", "line"}
            if not isinstance(palette, dict):
                errors.append("editorial-knowledge-map では palette が必要です。")
            else:
                missing_colors = sorted(required_colors - palette.keys())
                if missing_colors:
                    errors.append(f"editorial-knowledge-map の配色が不足しています: {', '.join(missing_colors)}")
            typography = visual.get("typography")
            if isinstance(typography, dict):
                title_px = typography.get("title_px")
                body_px = typography.get("body_px")
                if is_number(title_px) and title_px < 52:
                    warnings.append("editorial-knowledge-map のタイトルは52px以上を推奨します。")
                if is_number(body_px) and body_px < 15:
                    errors.append("editorial-knowledge-map の本文は15px以上にしてください。")

    modules = data.get("modules")
    ids: list[str] = []
    main_count = 0
    if not isinstance(modules, list):
        errors.append("modules は配列にしてください。")
        modules = []
    elif not 3 <= len(modules) <= 9:
        errors.append("modules は3〜9個にしてください。")
    elif not 5 <= len(modules) <= 7:
        warnings.append("modules は5〜7個が推奨です。")

    for index, module in enumerate(modules):
        path = f"modules[{index}]"
        if not isinstance(module, dict):
            errors.append(f"{path} はオブジェクトにしてください。")
            continue
        for key in ("id", "role", "heading", "summary", "importance", "evidence_type", "evidence_ids", "content", "placement"):
            if key not in module:
                errors.append(f"{path}.{key} がありません。")
        module_id = module.get("id")
        if isinstance(module_id, str) and module_id:
            ids.append(module_id)
        else:
            errors.append(f"{path}.id は空でない文字列にしてください。")
        if module.get("role") == "main":
            main_count += 1
        importance = module.get("importance")
        if not isinstance(importance, int) or isinstance(importance, bool) or not 1 <= importance <= 5:
            errors.append(f"{path}.importance は1〜5の整数にしてください。")
        if module.get("evidence_type") not in EVIDENCE_TYPES:
            errors.append(f"{path}.evidence_type が不正です。")
        if not isinstance(module.get("evidence_ids"), list):
            errors.append(f"{path}.evidence_ids は配列にしてください。")
        if not isinstance(module.get("content"), list):
            errors.append(f"{path}.content は配列にしてください。")

        placement = module.get("placement")
        if not isinstance(placement, dict):
            errors.append(f"{path}.placement はオブジェクトにしてください。")
            continue
        values: dict[str, float] = {}
        for key in ("x", "y", "width", "height"):
            if not is_number(placement.get(key)):
                errors.append(f"{path}.placement.{key} は数値にしてください。")
            else:
                values[key] = float(placement[key])
        if len(values) == 4 and canvas_width and canvas_height:
            if values["width"] <= 0 or values["height"] <= 0:
                errors.append(f"{path}.placement の幅と高さは正数にしてください。")
            if values["x"] < safe_margin or values["y"] < safe_margin:
                errors.append(f"{path}.placement がセーフマージンより外側です。")
            if values["x"] + values["width"] > canvas_width - safe_margin:
                errors.append(f"{path}.placement がキャンバス右端を超えます。")
            if values["y"] + values["height"] > canvas_height - safe_margin:
                errors.append(f"{path}.placement がキャンバス下端を超えます。")

    if len(ids) != len(set(ids)):
        errors.append("module id が重複しています。")
    if not 1 <= main_count <= 2:
        errors.append("role=main のmoduleは1〜2個にしてください。")

    order = data.get("reading_order")
    if not isinstance(order, list):
        errors.append("reading_order は配列にしてください。")
    elif len(order) != len(set(order)) or set(order) != set(ids):
        errors.append("reading_orderには全module idを重複なく含めてください。")

    if not isinstance(data.get("assumptions"), list):
        errors.append("assumptions は配列にしてください。")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="One-pager Specを検証します。")
    parser.add_argument("input", type=Path, help="One-pager Spec JSON")
    parser.add_argument("--report", type=Path, help="検証結果JSON")
    args = parser.parse_args()

    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        errors, warnings = validate(data)
    except (OSError, json.JSONDecodeError) as exc:
        errors, warnings = [f"JSONを読み込めません: {exc}"], []

    result = {
        "status": "error" if errors else "ok",
        "errors": errors,
        "warnings": warnings,
        "input": str(args.input.resolve()),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
