from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_INTEGRATED_TOKEN_DIR = PACKAGE_ROOT / "assets" / "design-system" / "tokens"
_STANDALONE_TOKEN_DIR = PACKAGE_ROOT / "assets" / "tokens"
DEFAULT_TOKEN_DIR = _INTEGRATED_TOKEN_DIR if _INTEGRATED_TOKEN_DIR.is_dir() else _STANDALONE_TOKEN_DIR


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_theme(theme: str = "base", overrides: dict[str, Any] | None = None, token_dir: Path | None = None) -> dict[str, Any]:
    token_dir = token_dir or DEFAULT_TOKEN_DIR
    base_path = token_dir / "base.json"
    if not base_path.exists():
        raise FileNotFoundError(f"base themeが見つかりません: {base_path}")
    base = json.loads(base_path.read_text(encoding="utf-8-sig"))
    if theme != "base":
        candidates = [token_dir / f"{theme}.json", token_dir / f"{theme.replace('_', '-')}.json"]
        selected = next((path for path in candidates if path.exists()), None)
        if selected is None:
            available = sorted(path.stem for path in token_dir.glob("*.json"))
            raise ValueError(f"未対応themeです: {theme}. available={available}")
        base = _deep_merge(base, json.loads(selected.read_text(encoding="utf-8-sig")))
    if overrides:
        normalized: dict[str, Any] = {}
        color_keys = set(base.get("colors", {})) | {"background", "surface", "text", "muted", "primary", "accent", "warning", "line"}
        if any(key in overrides for key in color_keys):
            normalized["colors"] = {key: overrides[key] for key in color_keys if key in overrides}
        if "font" in overrides:
            normalized.setdefault("fonts", {})["ja"] = overrides["font"]
        for key, value in overrides.items():
            if key not in color_keys | {"font"}:
                normalized[key] = value
        base = _deep_merge(base, normalized)
    return base


def color(tokens: dict[str, Any], key: str, fallback: str = "#000000") -> str:
    return str(tokens.get("colors", {}).get(key, fallback))


def font(tokens: dict[str, Any], locale: str = "ja") -> str:
    return str(tokens.get("fonts", {}).get(locale) or tokens.get("fonts", {}).get("ja") or "Yu Gothic UI")


def display_font(tokens: dict[str, Any]) -> str:
    return str(tokens.get("fonts", {}).get("display") or font(tokens))


def font_size(tokens: dict[str, Any], key: str, fallback: int) -> int:
    return int(tokens.get("fontSizes", {}).get(key, fallback))


def spacing(tokens: dict[str, Any], index: int, fallback: float) -> float:
    values = tokens.get("spacing", [])
    try:
        return float(values[index])
    except (IndexError, TypeError, ValueError):
        return fallback


def shadow(tokens: dict[str, Any], level: str = "card") -> dict[str, Any] | None:
    value = tokens.get("effects", {}).get(level)
    return deepcopy(value) if isinstance(value, dict) else None
