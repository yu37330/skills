from __future__ import annotations

import copy
from pathlib import Path

from check_traceability import check_traceability
from common import load_json
from init_prd import build_prd_skeleton
from render_prd import render_prd
from run_quality_gate import run_gate
from score_prd import score_prd
from validate_direction_spec import schema_errors as direction_schema_errors
from validate_direction_spec import semantic_findings
from validate_prd import schema_errors as prd_schema_errors

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests" / "scenarios"
TEMPLATES = ROOT / "templates"


def test_valid_direction_spec_passes_schema_and_semantics() -> None:
    data = load_json(SCENARIOS / "complete-direction-spec.json")
    schema = load_json(TEMPLATES / "direction-spec.schema.json")
    assert direction_schema_errors(data, schema) == []
    blockers, _ = semantic_findings(data)
    assert blockers == []


def test_empty_open_questions_is_valid() -> None:
    data = load_json(SCENARIOS / "empty-open-questions.json")
    schema = load_json(TEMPLATES / "direction-spec.schema.json")
    assert direction_schema_errors(data, schema) == []
    blockers, _ = semantic_findings(data)
    assert blockers == []


def test_invalid_direction_types_are_rejected() -> None:
    data = load_json(SCENARIOS / "invalid-types-direction-spec.json")
    schema = load_json(TEMPLATES / "direction-spec.schema.json")
    assert direction_schema_errors(data, schema)


def test_blocking_question_stops_direction_spec() -> None:
    data = load_json(SCENARIOS / "blocking-open-question.json")
    blockers, _ = semantic_findings(data)
    assert any("Blocking" in item for item in blockers)


def test_valid_prd_passes_schema_traceability_and_score() -> None:
    prd = load_json(SCENARIOS / "valid-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    schema = load_json(TEMPLATES / "prd.schema.json")
    assert prd_schema_errors(prd, schema) == []
    errors, _, _ = check_traceability(prd, direction)
    assert errors == []
    result = score_prd(prd, direction)
    assert result["status"] == "passed"
    assert result["score"] >= 90


def test_missing_source_id_is_rejected() -> None:
    prd = load_json(SCENARIOS / "missing-source-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    errors, _, _ = check_traceability(prd, direction)
    assert any("存在しないsource_id" in item for item in errors)


def test_inferred_only_confirmed_requirement_is_rejected() -> None:
    prd = load_json(SCENARIOS / "inferred-must-prd.json")
    errors, _, _ = check_traceability(prd, None)
    assert any("推論またはdraft情報だけ" in item for item in errors)


def test_unmeasurable_metric_is_blocker() -> None:
    prd = load_json(SCENARIOS / "unmeasurable-kpi-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    result = score_prd(prd, direction)
    assert result["status"] == "rejected"
    assert any("測定可能ではありません" in item for item in result["blockers"])


def test_ambiguous_must_requirement_is_blocker() -> None:
    prd = load_json(SCENARIOS / "ambiguous-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    result = score_prd(prd, direction)
    assert any("Must要求に未修飾の曖昧表現" in item for item in result["blockers"])


def test_tbd_in_major_requirement_is_blocker() -> None:
    prd = load_json(SCENARIOS / "blocking-tbd-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    result = score_prd(prd, direction)
    assert any("未確定表現" in item for item in result["blockers"])


def test_init_prd_preserves_direction_information() -> None:
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    prd = build_prd_skeleton(direction)
    assert prd["selected_direction"] == direction["selected_direction"]
    assert prd["decision_rationale"] == direction["decision_rationale"]
    assert prd["constraints"] == direction["constraints"]
    assert prd["open_questions"][0]["question"] == direction["open_questions"][0]["question"]
    assert prd["decision_log"][0]["decision"] == direction["selected_direction"]


def test_rendered_markdown_contains_critical_sections() -> None:
    prd = load_json(SCENARIOS / "valid-prd.json")
    markdown = render_prd(prd)
    assert "Selected Direction and Rationale" in markdown
    assert "Bedrock上で利用可能なモデル" in markdown
    assert "精度評価用データを誰が承認するか" in markdown
    assert "FR-001" in markdown
    assert "NFR-001" in markdown


def test_run_quality_gate_rejects_schema_error() -> None:
    prd = load_json(SCENARIOS / "valid-prd.json")
    direction = load_json(SCENARIOS / "complete-direction-spec.json")
    prd_schema = load_json(TEMPLATES / "prd.schema.json")
    direction_schema = load_json(TEMPLATES / "direction-spec.schema.json")
    broken = copy.deepcopy(prd)
    broken["target_users"] = "全員"
    result = run_gate(broken, prd_schema, direction, direction_schema)
    assert result["status"] == "rejected"
    assert result["prd_schema_errors"]
