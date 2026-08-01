#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdpm_native_components import list_components  # noqa: E402


def main() -> int:
    contract_path = ROOT / "assets" / "design-system" / "components" / "contracts.json"
    registry_path = ROOT / "assets" / "design-system" / "components" / "registry.yaml"
    contracts = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8-sig"))
    contracted = {item["id"] for item in contracts["components"]}
    registered = {item["id"] for item in registry["components"]}
    implemented = set(list_components())
    errors: list[str] = []
    if not (contracted == registered == implemented):
        errors.append(
            "Contract・Registry・実装が不一致: "
            f"contract_only={sorted(contracted - implemented)}, "
            f"registry_only={sorted(registered - implemented)}, "
            f"code_only={sorted(implemented - registered)}"
        )
    if len(implemented) < 73:
        errors.append(f"Component数が不足しています: {len(implemented)}")
    for item in contracts["components"]:
        if not item.get("description"):
            errors.append(f"descriptionがありません: {item['id']}")
        if not item.get("variants"):
            errors.append(f"variantsがありません: {item['id']}")
        registry_item = next((entry for entry in registry["components"] if entry["id"] == item["id"]), {})
        for key in ("kind", "slots", "implementation", "editable", "use_when", "avoid_when", "content_limits"):
            if registry_item.get(key) in (None, "", []):
                errors.append(f"Registry項目が不足しています: {item['id']}.{key}")
    theme_dir = ROOT / "assets" / "design-system" / "tokens"
    themes = list(theme_dir.glob("*.json"))
    if len(themes) < 5:
        errors.append(f"themeが不足しています: {len(themes)}")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION OK: components={len(implemented)}, themes={len(themes)}, contracts={len(contracted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
