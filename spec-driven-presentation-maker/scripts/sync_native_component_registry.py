#!/usr/bin/env python3
"""Native Components v4の契約とV8 Registryを再現可能に同期する。"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

import yaml


LEGACY_ALIASES = {
    "chart.highlight_bar": "chart.insight",
    "chart.trend_line": "chart.line_forecast",
    "process.stage": "process.stage_flow",
    "synthesis.spine": "synthesis.causal_spine",
    "synthesis.system_map": "framework.hub_spoke",
}

PREMIUM_COMPONENTS = {
    "narrative.executive_summary",
    "narrative.key_message_evidence",
    "chart.insight",
    "narrative.findings_implications",
    "strategy.house",
    "strategy.issue_tree",
    "strategy.portfolio_matrix",
    "strategy.capability_map",
    "strategy.value_driver_tree",
    "strategy.initiative_portfolio",
    "execution.roadmap",
    "execution.gantt",
    "execution.governance",
    "execution.kpi_cascade",
    "narrative.recommendation_actions",
}

THEME_MAPPING = {
    "executive": "consulting_classic",
    "editorial": "editorial_premium",
    "technical": "technical_data",
}


def normalize_text(value):
    if isinstance(value, str):
        return value.replace("乣", "～")
    if isinstance(value, list):
        return [normalize_text(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_text(item) for key, item in value.items()}
    return value


def component_slots(component_id: str) -> list[str]:
    if component_id.startswith("headline."):
        return ["header"]
    if component_id.startswith("label."):
        return ["tag", "kicker"]
    if component_id.startswith("evidence_footer."):
        return ["footer"]
    if component_id.startswith("annotation."):
        return ["annotation", "interpretation"]
    if component_id.startswith("action."):
        return ["main", "action"]
    if component_id.startswith("decision."):
        return ["main", "decision"]
    if component_id.startswith("narrative.recommendation"):
        return ["main", "decision", "action"]
    if component_id.startswith("execution."):
        return ["main", "action"]
    return ["main"]


def add_legacy_contracts(contracts: dict) -> None:
    components = contracts.setdefault("components", [])
    by_id = {item["id"]: item for item in components}
    for legacy_id, target_id in LEGACY_ALIASES.items():
        if legacy_id in by_id:
            by_id[legacy_id]["alias_of"] = target_id
            continue
        target = deepcopy(by_id[target_id])
        target.update({
            "id": legacy_id,
            "description": f"V8互換ID。{target_id}へ解決する。",
            "use_when": "既存V8のDeck PlanまたはRole Layoutとの互換性を維持するとき",
            "avoid_when": f"新規設計では{target_id}を優先する",
            "benchmark_tier": "compatibility",
            "alias_of": target_id,
        })
        components.append(target)


def build_registry(contracts: dict) -> dict:
    items = []
    for contract in sorted(contracts["components"], key=lambda item: item["id"]):
        component_id = contract["id"]
        entry = {
            "id": component_id,
            "kind": contract.get("category", "native_component"),
            "slots": component_slots(component_id),
            "implementation": "native_components_v4_alias" if contract.get("alias_of") else "native_components_v4",
            "editable": True,
            "variants": contract.get("variants", ["primary"]),
            "use_when": contract.get("use_when", ""),
            "avoid_when": contract.get("avoid_when", ""),
            "content_limits": contract.get("content_limits", {}),
            "benchmark_tier": contract.get("benchmark_tier", "core"),
        }
        if contract.get("required") is not None:
            entry["required_content"] = contract.get("required", [])
        if contract.get("optional") is not None:
            entry["optional_content"] = contract.get("optional", [])
        if contract.get("alias_of"):
            entry["alias_of"] = contract["alias_of"]
        if component_id in PREMIUM_COMPONENTS:
            entry["design_systems"] = list(THEME_MAPPING.values())
            entry["theme_mapping"] = THEME_MAPPING
            entry["premium"] = True
        items.append(entry)
    return {"version": 2, "components": items}


def main() -> int:
    parser = argparse.ArgumentParser(description="Component ContractとRegistryを同期します")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="spec-driven-presentation-makerのルート",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    contract_path = root / "assets" / "design-system" / "components" / "contracts.json"
    registry_path = root / "assets" / "design-system" / "components" / "registry.yaml"
    contracts = normalize_text(json.loads(contract_path.read_text(encoding="utf-8-sig")))
    add_legacy_contracts(contracts)
    contracts["version"] = 2
    contracts["library"] = "sdpm-native-components-v4.1-v9"
    contracts["components"] = sorted(contracts["components"], key=lambda item: item["id"])
    contract_path.write_text(json.dumps(contracts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = build_registry(contracts)
    registry_path.write_text(
        yaml.safe_dump(registry, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"Component ContractとRegistryを同期しました: {len(registry['components'])}件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
