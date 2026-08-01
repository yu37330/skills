#!/usr/bin/env python3
"""PRD Builderの共通処理。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

AMBIGUOUS_TERMS = (
    "なるべく",
    "高精度",
    "使いやすい",
    "十分な",
    "必要に応じて",
    "適切に",
    "原則として",
    "可能な限り",
    "リアルタイム",
    "大量",
    "迅速に",
    "柔軟に",
)

TBD_TERMS = (
    "TBD",
    "TODO",
    "未定",
    "要確認",
    "後で決める",
)

MEASUREMENT_HINT = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|秒|分|時間|日|件|回|人|ms|s|min|hour)?|以内|以上|以下|未満|超)",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    """JSONファイルを辞書として読み込む。"""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("JSONのルートはobjectである必要があります。")
    return data


def dump_json(path: Path, data: Any) -> None:
    """JSONをUTF-8で整形保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    """比較用に空白と記号差を弱める。"""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[、。,.・:：;；()（）\[\]【】\-ー_]", "", text)
    return text


def iter_text_nodes(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    """JSON内のすべての文字列とパスを列挙する。"""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_text_nodes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_text_nodes(child, f"{path}[{index}]")


def find_terms(value: Any, terms: Iterable[str]) -> list[dict[str, str]]:
    """JSON内に含まれる指定語と場所を返す。"""
    findings: list[dict[str, str]] = []
    for path, text in iter_text_nodes(value):
        for term in terms:
            if term.lower() in text.lower():
                findings.append({"path": path, "term": term, "text": text})
    return findings


def has_measurement_hint(value: Any) -> bool:
    """数値、単位、比較条件などの測定可能性を示す表現があるか確認する。"""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    text = str(value).strip()
    return bool(text and MEASUREMENT_HINT.search(text))


def is_blank(value: Any) -> bool:
    """空値か確認する。0やfalseは空としない。"""
    return value is None or value == "" or value == [] or value == {}


def source_index(prd: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """source_idをキーに情報源を索引化する。"""
    index: dict[str, dict[str, Any]] = {}
    for source in prd.get("sources", []):
        if isinstance(source, dict) and source.get("source_id"):
            index[str(source["source_id"])] = source
    return index


def all_requirements(prd: dict[str, Any]) -> list[dict[str, Any]]:
    """機能要求と非機能要求をまとめて返す。"""
    requirements: list[dict[str, Any]] = []
    for key in ("functional_requirements", "non_functional_requirements"):
        values = prd.get(key, [])
        if isinstance(values, list):
            requirements.extend(item for item in values if isinstance(item, dict))
    return requirements


def resolve_direction_ref(direction_spec: dict[str, Any], ref: str) -> tuple[bool, Any]:
    """`scope[0]`のような簡易参照をDirection Specから解決する。"""
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?", ref)
    if not match:
        return False, None
    field, index_text = match.groups()
    if field not in direction_spec:
        return False, None
    value: Any = direction_spec[field]
    if index_text is not None:
        if not isinstance(value, list):
            return False, None
        index = int(index_text)
        if index >= len(value):
            return False, None
        value = value[index]
    return True, value


def unique_ids(items: Iterable[dict[str, Any]], field: str = "id") -> tuple[bool, list[str]]:
    """ID重複を検出する。"""
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in items:
        value = str(item.get(field, ""))
        if not value:
            continue
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    return not duplicates, duplicates


def scope_overlaps(scope: list[Any], out_of_scope: list[Any]) -> list[str]:
    """In ScopeとOut of Scopeの重複を返す。"""
    out_map = {normalize_text(item): str(item) for item in out_of_scope if normalize_text(item)}
    overlaps: list[str] = []
    for item in scope:
        normalized = normalize_text(item)
        if normalized and normalized in out_map:
            overlaps.append(str(item))
    return overlaps
