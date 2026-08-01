#!/usr/bin/env python3
"""Role LayoutへGrid由来の実座標契約を埋め込み、二重管理を検出可能にする。"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Role Layoutへslot_framesを同期します")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    grid_path = root / "assets" / "design-system" / "catalog" / "layout-grids.yaml"
    layout_path = root / "assets" / "design-system" / "role-layouts" / "registry.yaml"
    grid_doc = yaml.safe_load(grid_path.read_text(encoding="utf-8-sig"))
    layout_doc = yaml.safe_load(layout_path.read_text(encoding="utf-8-sig"))
    grids = {item["id"]: item for item in grid_doc["grids"]}
    for layout in layout_doc["role_layouts"]:
        grid = grids[layout["grid_id"]]
        layout["slot_frames"] = {
            slot: dict(grid["slots"][slot])
            for slot in layout.get("slots", [])
            if slot in grid.get("slots", {})
        }
    layout_path.write_text(
        yaml.safe_dump(layout_doc, allow_unicode=True, sort_keys=False, width=140),
        encoding="utf-8",
    )
    print(f"Role Layout実座標を同期しました: {len(layout_doc['role_layouts'])}件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
