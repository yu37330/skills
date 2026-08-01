#!/usr/bin/env python3
"""PRD要求の根拠実在性と確定状態を検査する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import all_requirements, load_json, resolve_direction_ref, source_index


def check_traceability(
    prd: dict[str, Any],
    direction_spec: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    """トレーサビリティの重大エラー、警告、統計を返す。"""
    errors: list[str] = []
    warnings: list[str] = []
    sources = source_index(prd)
    requirements = all_requirements(prd)
    requirement_map = {str(item.get("id")): item for item in requirements if item.get("id")}
    trace_entries = {
        str(item.get("requirement_id")): item
        for item in prd.get("traceability", [])
        if isinstance(item, dict) and item.get("requirement_id")
    }

    for requirement_id, requirement in requirement_map.items():
        entry = trace_entries.get(requirement_id)
        if entry is None:
            errors.append(f"{requirement_id}: traceabilityエントリがありません。")
            continue

        requirement_source_ids = set(requirement.get("source_ids", []))
        trace_source_ids = set(entry.get("source_ids", []))
        if requirement_source_ids != trace_source_ids:
            errors.append(
                f"{requirement_id}: 要求とtraceabilityのsource_idsが一致しません。"
            )

        all_source_ids = requirement_source_ids | trace_source_ids
        missing = sorted(source_id for source_id in all_source_ids if source_id not in sources)
        if missing:
            errors.append(
                f"{requirement_id}: PRD.sourcesに存在しないsource_idがあります: {', '.join(missing)}"
            )

        valid_sources = [sources[source_id] for source_id in all_source_ids if source_id in sources]
        statuses = {source.get("status") for source in valid_sources}
        if requirement.get("status") == "confirmed":
            has_approved_source = "approved" in statuses
            has_approved_direction = bool(
                direction_spec and direction_spec.get("approval_status") == "approved"
            )
            if not has_approved_source and not has_approved_direction:
                errors.append(
                    f"{requirement_id}: confirmed要求に承認済み根拠がありません。"
                )
            if statuses and statuses <= {"inferred", "draft"}:
                errors.append(
                    f"{requirement_id}: confirmed要求が推論またはdraft情報だけに依存しています。"
                )

        if requirement.get("priority") == "Must" and not all_source_ids:
            errors.append(f"{requirement_id}: Must要求にsource_idがありません。")

        if not str(entry.get("evidence", "")).strip():
            errors.append(f"{requirement_id}: evidenceがありません。")

        direction_refs = entry.get("direction_refs", [])
        if set(requirement.get("direction_refs", [])) != set(direction_refs):
            errors.append(
                f"{requirement_id}: 要求とtraceabilityのdirection_refsが一致しません。"
            )

        if direction_spec is not None:
            for ref in direction_refs:
                exists, _ = resolve_direction_ref(direction_spec, str(ref))
                if not exists:
                    errors.append(
                        f"{requirement_id}: Direction Specに存在しない参照です: {ref}"
                    )

    orphan_entries = sorted(set(trace_entries) - set(requirement_map))
    if orphan_entries:
        warnings.append(
            "要求が存在しないtraceabilityエントリがあります: " + ", ".join(orphan_entries)
        )

    referenced_source_ids: set[str] = set()
    for requirement in requirements:
        referenced_source_ids.update(str(item) for item in requirement.get("source_ids", []))
    unused_sources = sorted(set(sources) - referenced_source_ids)
    if unused_sources:
        warnings.append(
            "要求から参照されていない情報源があります: " + ", ".join(unused_sources)
        )

    stats = {
        "requirements": len(requirements),
        "traceability_entries": len(trace_entries),
        "requirements_with_traceability": sum(1 for rid in requirement_map if rid in trace_entries),
        "sources": len(sources),
    }
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="要求トレーサビリティを検査します。")
    parser.add_argument("prd", type=Path)
    parser.add_argument("--direction-spec", type=Path)
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
        direction_spec = load_json(args.direction_spec) if args.direction_spec else None
    except FileNotFoundError as exc:
        print(f"エラー: ファイルが見つかりません: {exc.filename}")
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"エラー: JSON形式が不正です: {exc}")
        return 2

    errors, warnings, stats = check_traceability(prd, direction_spec)
    for error in errors:
        print(f"- 重大: {error}")
    for warning in warnings:
        print(f"- 警告: {warning}")

    if errors:
        print("不合格: トレーサビリティに重大な問題があります。")
        return 1

    print(
        "合格: "
        f"{stats['requirements_with_traceability']}/{stats['requirements']}件の要求で"
        "根拠実在性を確認しました。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
