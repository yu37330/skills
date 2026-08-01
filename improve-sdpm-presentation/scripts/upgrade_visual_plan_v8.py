#!/usr/bin/env python3
"""Visual Plan v7へv8のDirection・Locked Layout・Renderer解決を安全に追加する。"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual Plan v7をv8へ移行します")
    parser.add_argument("visual_plan_v7", type=Path)
    parser.add_argument("design_resolution_v2", type=Path)
    parser.add_argument("design_direction_scout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--anti-slop-exception", action="append", default=[], metavar="ID=理由",
        help="登録済みAnti-Slop例外を理由付きで指定します",
    )
    args = parser.parse_args()
    plan_path = args.visual_plan_v7.resolve()
    resolution_path = args.design_resolution_v2.resolve()
    direction_path = args.design_direction_scout.resolve()
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8-sig"))
    resolution = yaml.safe_load(resolution_path.read_text(encoding="utf-8-sig"))
    direction = yaml.safe_load(direction_path.read_text(encoding="utf-8-sig"))
    if not isinstance(plan, dict) or plan.get("version") != 7:
        print("ERROR: Visual Plan version 7を指定してください")
        return 1
    if not isinstance(resolution, dict) or resolution.get("version") != 2:
        print("ERROR: Design Resolution version 2を指定してください")
        return 1
    if not isinstance(direction, dict) or direction.get("status") != "selected":
        print("ERROR: 選択済みDesign Direction Scoutを指定してください")
        return 1
    resolved = {item.get("slide_id"): item for item in resolution.get("slides", []) if isinstance(item, dict)}
    for slide in plan.get("slides", []):
        item = resolved.get(slide.get("slide_id"))
        if not item:
            print(f"ERROR: slide_id={slide.get('slide_id')}のDesign Resolutionがありません")
            return 1
        slide["design_resolution"] = item["design_resolution"]
        slide["layout_adjustments"] = item.get("layout_adjustments", {})
        slide["component_plan"] = item["component_plan"]
        route = item.get("renderer_decision", {})
        strategy = slide.get("visual_strategy", {})
        selected = route.get("selected", "sdpm_native")
        considered = list(dict.fromkeys([selected, route.get("fallback")]))
        strategy["renderer"] = selected
        strategy["integration_mode"] = {
            "sdpm_native": "native", "baoyu_diagram": "embed_svg",
            "visual_explainer": "rebuild_from_prototype", "imagegen": "embed_raster",
        }.get(selected, "native")
        strategy["renderer_decision"] = {
            "considered": [value for value in considered if value],
            "selected": selected,
            "reason": route.get("reason", "Renderer Router規則による"),
        }
    plan["version"] = 8
    plan["source"]["design_direction_scout"] = str(direction_path)
    plan["source"]["design_direction_sha256"] = sha256(direction_path)
    plan["source"]["design_system_manifest"] = resolution["source"]["design_system_manifest"]
    plan["source"]["design_system_sha256"] = resolution["source"]["design_system_sha256"]
    exceptions = []
    for value in args.anti_slop_exception:
        if "=" not in value or not value.split("=", 1)[1].strip():
            print("ERROR: --anti-slop-exceptionはID=理由で指定してください")
            return 1
        exception_id, reason = value.split("=", 1)
        exceptions.append({"id": exception_id.strip(), "reason": reason.strip()})
    plan["deck"]["design_system"] = {**resolution["deck"], "anti_slop_exceptions": exceptions}
    plan["deck"]["anti_slop_acknowledged"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Visual Plan v8を作成しました: {args.output}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
