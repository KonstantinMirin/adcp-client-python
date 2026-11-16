"""Differential contract between structural models and canonical schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

import adcp.types as public_types
from adcp import get_adcp_spec_version
from adcp.validation import validate_request, validate_response

_FIXTURES = Path(__file__).parent / "fixtures"
_CASES: list[dict[str, Any]] = json.loads((_FIXTURES / "validation-parity-cases.json").read_text())
_ALLOWED_DIVERGENCES: dict[str, dict[str, str]] = json.loads(
    (_FIXTURES / "validation-model-divergences.json").read_text()
)


def _pydantic_accepts(model: type[BaseModel], payload: dict[str, Any]) -> bool:
    try:
        model.model_validate(payload)
    except ValidationError:
        return False
    return True


def _canonical_accepts(case: dict[str, Any]) -> bool:
    validate = validate_request if case["direction"] == "request" else validate_response
    return validate(case["tool"], case["payload"]).valid


def test_validation_parity_fixtures_match_both_runtime_paths() -> None:
    """Each fixture pins the current Pydantic and canonical outcomes."""
    for case in _CASES:
        model = getattr(public_types, case["model"])
        assert _pydantic_accepts(model, case["payload"]) is case["pydantic_valid"], case["id"]
        assert _canonical_accepts(case) is case["canonical_valid"], case["id"]


def test_every_model_schema_divergence_is_explicitly_allowlisted() -> None:
    """No canonical negative may silently pass Pydantic without a rationale."""
    actual = {
        case["id"] for case in _CASES if case["pydantic_valid"] and not case["canonical_valid"]
    }
    assert actual == set(_ALLOWED_DIVERGENCES)
    for case_id, decision in _ALLOWED_DIVERGENCES.items():
        assert decision["keyword"], case_id
        assert decision["reason"], case_id


def test_no_fixture_is_stricter_in_canonical_schema_than_declared() -> None:
    """A changed generator outcome requires updating the reviewed decision."""
    declared = {case["id"]: case for case in _CASES}
    assert set(_ALLOWED_DIVERGENCES) <= set(declared)
    for case_id in _ALLOWED_DIVERGENCES:
        case = declared[case_id]
        assert case["pydantic_valid"] is True
        assert case["canonical_valid"] is False


def test_x_adcp_validation_constrains_in_intent_and_not_in_the_document() -> None:
    """`x-adcp-validation` is a key the document's own draft ignores, at BOTH halves.

    rebuild-plan §6 states the decision by name: *"`x-adcp-validation` constrains
    in intent and not in the document, so a model enforcing it would be narrower
    than its document (upstream: `adcontextprotocol/adcp#8472`)"*.

    `media-buy/change-term.json` carries no `allOf` and no conditional; the
    action/constraint compatibility it wants sits under
    `x-adcp-validation.verifier_constraints` as a table of prose and lists. So
    the payload below -- a `budget` constraint on a `pause` right, which that
    table calls incompatible -- is admitted by the model AND by
    `strict_validate`, because the document admits it. What stood here expected a
    refusal from the previous emission's hand-written targeted validator.
    """
    spec_version = get_adcp_spec_version()
    bundle = spec_version if "-" in spec_version else ".".join(spec_version.split(".")[:2])
    schema_path = (
        Path(__file__).parents[1] / "schemas" / "cache" / bundle / "media-buy" / "change-term.json"
    )
    schema = json.loads(schema_path.read_text())
    constraints = schema["x-adcp-validation"]["verifier_constraints"]
    assert "constraint_action_compatibility" in constraints
    assert "pause" not in constraints["constraint_action_compatibility"]["budget"]
    assert [key for key in schema if key.startswith("allOf") or key in ("if", "not")] == []

    incompatible = {
        "term_id": "right_pause",
        "action": "pause",
        "service_mode": "self_serve",
        "constraints": {"kind": "budget", "max_delta_percent": 10},
    }
    assert public_types.MediaBuyChangeTerm.model_validate(incompatible).action == "pause"
    public_types.MediaBuyChangeTerm.strict_validate(incompatible)
