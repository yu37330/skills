from __future__ import annotations

import re
from typing import Any


_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return _WHITESPACE.sub(" ", str(value)).strip()


def fit_font_size(
    text: str,
    width: float,
    height: float,
    preferred: int,
    minimum: int,
    max_lines: int = 2,
    japanese_ratio: float = 0.95,
) -> tuple[int, list[str]]:
    """簡易的な文字量推定。PowerPoint実測前の安全側フォールバック用。"""
    text = normalize_text(text)
    if not text:
        return preferred, []
    warnings: list[str] = []
    japanese_chars = sum(1 for char in text if ord(char) > 255)
    latin_chars = len(text) - japanese_chars
    weighted_chars = japanese_chars * japanese_ratio + latin_chars * 0.55
    # 1行あたりのおおよその収容文字数。
    capacity = max(1.0, width / (preferred * 0.78)) * max_lines
    vertical_capacity = max(1.0, height / (preferred * 1.35))
    pressure = max(weighted_chars / capacity, max_lines / vertical_capacity)
    if pressure <= 1:
        return preferred, warnings
    candidate = max(minimum, int(preferred / pressure))
    if candidate < preferred:
        warnings.append(f"文字量に応じてフォントを{preferred}ptから{candidate}ptへ縮小しました")
    if candidate == minimum and pressure > preferred / minimum:
        warnings.append("最小フォントでも文字量が多いため、文言短縮またはdense variantを推奨します")
    return candidate, warnings


def join_nonempty(parts: list[str], separator: str = "｜") -> str:
    return separator.join(part for part in (normalize_text(p) for p in parts) if part)
