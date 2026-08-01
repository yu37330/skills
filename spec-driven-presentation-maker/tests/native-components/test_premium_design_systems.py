from __future__ import annotations

import unittest

from sdpm_native_components import build_component
from test_smoke import SAMPLES

PREMIUM = [
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
]


def signature(elements: list[dict]) -> tuple:
    return tuple(
        (
            e.get("type"), e.get("shape"),
            round(float(e.get("x", e.get("x1", 0))), 1),
            round(float(e.get("y", e.get("y1", 0))), 1),
            round(float(e.get("width", 0)), 1),
            round(float(e.get("height", 0)), 1),
            e.get("componentRole"),
        )
        for e in elements
    )


class PremiumDesignSystemTest(unittest.TestCase):
    def test_three_design_systems_have_different_compositions(self) -> None:
        for component_id in PREMIUM:
            with self.subTest(component_id=component_id):
                sigs = []
                for theme in ["executive", "editorial", "technical"]:
                    result = build_component(
                        component_id,
                        {"x": 100, "y": 220, "width": 1720, "height": 680},
                        SAMPLES[component_id],
                        theme=theme,
                        variant="primary",
                    )
                    sigs.append(signature(result.elements))
                self.assertEqual(len(set(sigs)), 3, f"themeごとの構図が同一です: {component_id}")


if __name__ == "__main__":
    unittest.main()
