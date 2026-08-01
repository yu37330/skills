#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdpm_native_components import list_components  # noqa: E402


def main() -> int:
    registry_path = ROOT / "assets" / "contracts" / "components.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    registered = {item["id"] for item in registry["components"]}
    implemented = set(list_components())
    errors: list[str] = []
    if registered != implemented:
        errors.append(f"registryと実装が不一致: only_registry={sorted(registered - implemented)}, only_code={sorted(implemented - registered)}")
    for item in registry["components"]:
        if not item.get("description"):
            errors.append(f"descriptionがありません: {item['id']}")
        if not item.get("variants"):
            errors.append(f"variantsがありません: {item['id']}")
    theme_dir = ROOT / "assets" / "tokens"
    themes = list(theme_dir.glob("*.json"))
    if len(themes) < 5:
        errors.append(f"themeが不足しています: {len(themes)}")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION OK: components={len(implemented)}, themes={len(themes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
