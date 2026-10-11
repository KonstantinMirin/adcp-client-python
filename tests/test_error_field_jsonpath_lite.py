"""``error.field`` is ``issues[0].pointer`` translated, and one owner does it.

``core/error.json`` requires it on ``field``, on ``issues`` and on
``issues[].pointer``: ``field`` carries ``packages[0].targeting`` where the
pointer carries ``/packages/0/targeting``.

Three case populations, none of them derived from the translator:

* the arrow examples parsed out of the pinned schema bundle — the spec is the
  authority for what a translation should produce;
* whatever pointers the jsonschema oracle and pydantic emit on real malformed
  payloads, round-tripped;
* hand-authored pointer shapes the spec's examples do not cover.

The first two are asserted non-empty, since an extraction that matched nothing
yields a parametrize that passes.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from pydantic import ValidationError

from adcp.types import CreateMediaBuyRequest
from adcp.validation.pydantic_errors import issues_from_validation_error
from adcp.validation.schema_errors import build_adcp_validation_error_payload
from adcp.validation.schema_validator import (
    ValidationIssue,
    field_to_pointer,
    pointer_to_field,
    validate_request,
)

_SCHEMA_ROOT = pathlib.Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"

#: ``'/packages/0/targeting' -> 'packages[0].targeting'`` as the descriptions
#: write it, in either arrow spelling.
_ARROW = re.compile(r"[`']((?:/[^`' ]+)+)[`']\s*(?:→|->)\s*[`']([^`' ]+)[`']")


def _spec_example_pairs() -> list[tuple[str, str]]:
    """Every pointer -> JSONPath-lite example the pinned bundle states."""
    strings: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            strings.append(node)

    for path in sorted(_SCHEMA_ROOT.rglob("*.json")):
        try:
            walk(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):  # pragma: no cover
            continue
    return sorted(set(_ARROW.findall("\n".join(strings))))


def _real_validation_pointers() -> list[str]:
    """Pointers the two validators emit on real malformed payloads.

    Nested shapes are the point: a translator that only sees one-segment
    pointers is untested.
    """
    payloads: list[object] = [
        {"packages": [{"targeting_overlay": {"geo_countries": [5]}}]},
        {"packages": "not-a-list"},
        {"buyer_ref": 7, "packages": [{"products": [{}]}]},
        {},
        "not-an-object",
        [1, 2],
    ]
    pointers: set[str] = set()
    for payload in payloads:
        outcome = validate_request("create_media_buy", payload)
        pointers.update(issue.pointer for issue in outcome.issues)
        try:
            CreateMediaBuyRequest.model_validate(payload)
        except ValidationError as error:
            pointers.update(issue.pointer for issue in issues_from_validation_error(error))
    return sorted(pointers)


#: Hand-authored. The three shapes with no dotted rendering, plus root.
AUTHORED_EDGE_CASES = [
    "/",
    "/a.b",
    "/a~1b",
    "/a~0b",
    "/0",
    "/x/a.b/y",
    "/ext/vendor.key/value",
    "/details/a'b",
    "/packages/0/optimization_goals/1/event_sources/0",
]

SPEC_PAIRS = _spec_example_pairs()
REAL_POINTERS = _real_validation_pointers()


@pytest.mark.parametrize(("pointer", "expected_field"), SPEC_PAIRS)
def test_spec_stated_examples(pointer, expected_field):
    """The translator reproduces every example the pinned spec states."""
    assert pointer_to_field(pointer) == expected_field


def test_spec_examples_were_actually_found():
    """An extraction that matched nothing yields a parametrize that passes."""
    assert SPEC_PAIRS, f"no arrow examples extracted from {_SCHEMA_ROOT}"


@pytest.mark.parametrize("pointer", REAL_POINTERS)
def test_round_trip_on_real_validation_pointers(pointer):
    """Translating a real pointer and back returns the same pointer."""
    assert field_to_pointer(pointer_to_field(pointer)) == pointer


def test_real_validation_pointers_are_not_empty_and_are_nested():
    """The validators must actually have produced pointers, including deep ones."""
    assert REAL_POINTERS, "no pointers collected from real validation failures"
    assert any(p.count("/") >= 3 for p in REAL_POINTERS), REAL_POINTERS


@pytest.mark.parametrize("pointer", AUTHORED_EDGE_CASES)
def test_round_trip_on_authored_edge_cases(pointer):
    assert field_to_pointer(pointer_to_field(pointer)) == pointer


def test_translation_is_not_the_identity():
    """Every round-trip above would also pass for an identity pair."""
    assert pointer_to_field("/packages/0/targeting") != "/packages/0/targeting"


def _issue(pointer: str) -> ValidationIssue:
    return ValidationIssue(pointer=pointer, message="m", keyword="type", schema_path="")


@pytest.mark.parametrize("pointer", AUTHORED_EDGE_CASES + REAL_POINTERS)
def test_builder_field_is_the_translated_first_pointer(pointer):
    """The dual-write the spec demands, asserted on the builder's output."""
    payload = build_adcp_validation_error_payload("create_media_buy", "request", [_issue(pointer)])
    expected = pointer_to_field(pointer)
    if expected:
        assert payload["field"] == expected
        assert not payload["field"].startswith("/"), "field is still an RFC 6901 pointer"
    else:
        # Root: there is no field path to name, and `field` is not required.
        assert "field" not in payload


def test_builder_emits_top_level_issues_and_recovery():
    payload = build_adcp_validation_error_payload(
        "create_media_buy", "request", [_issue("/packages/0/targeting")]
    )
    assert payload["issues"] == payload["details"]["issues"]
    assert payload["recovery"] == "correctable"


def test_builder_omits_field_and_issues_when_there_are_none():
    """``issues`` has no ``minItems``, so an empty list is legal.

    With no ``issues[0]`` there is no source for ``field``, and both fields are
    optional — so neither is emitted.
    """
    payload = build_adcp_validation_error_payload("create_media_buy", "request", [])
    assert "field" not in payload
    assert "issues" not in payload
    assert payload["details"]["issues"] == []


def _handler_request_models() -> list[type]:
    """The request models the handler classes validate ``params`` into.

    Derived from the class bodies, so a handler added later is covered.
    """
    import inspect

    from adcp import types
    from adcp.server.content_standards import ContentStandardsHandler
    from adcp.server.governance import GovernanceHandler
    from adcp.server.sponsored_intelligence import SponsoredIntelligenceHandler

    found: dict[str, type] = {}
    for handler_cls in (ContentStandardsHandler, GovernanceHandler, SponsoredIntelligenceHandler):
        for name, member in vars(handler_cls).items():
            if name.startswith(("_", "handle_")) or not inspect.iscoroutinefunction(member):
                continue
            match = re.search(r"(\w+)\.model_validate\(params\)", inspect.getsource(member))
            if match and (model := getattr(types, match.group(1), None)) is not None:
                found[match.group(1)] = model
    return list(found.values())


HANDLER_REQUEST_MODELS = _handler_request_models()


def test_handler_request_models_were_discovered():
    assert len(HANDLER_REQUEST_MODELS) >= 21, HANDLER_REQUEST_MODELS


@pytest.mark.parametrize("model", HANDLER_REQUEST_MODELS, ids=lambda m: m.__name__)
def test_no_reachable_pointer_names_a_pydantic_internal(model):
    """A pointer must address the buyer's document, not pydantic's validators.

    pydantic's ``loc`` is not a document path: a model-level ``function-after``
    wrapper or a wrapped union prefixes synthetic elements naming the validator
    and the generated branch class, so the pointer no longer resolves against
    what the buyer sent and ``field`` inherits it. No model here does that;
    ``CreateMediaBuyRequest`` does. Wiring such a model to ``invalid_request``
    must fail here rather than on the wire (salesagent-8qela.28).
    """
    for payload in ("x", {}, {"account": "x"}, [1]):
        try:
            model.model_validate(payload)
        except ValidationError as error:
            for issue in issues_from_validation_error(error):
                assert "function-" not in issue.pointer, issue.pointer
                assert "[" not in issue.pointer, issue.pointer
                assert pointer_to_field(issue.pointer).count("['") == 0, issue.pointer


def test_both_lanes_emit_the_same_envelope():
    """The jsonschema oracle and the pydantic projection must not disagree.

    Two routes reach ``VALIDATION_ERROR`` — the oracle through
    ``validate_request``, a handler's pydantic rejection through
    ``invalid_request`` — and both must produce one envelope. Each is given a
    FIELD-LEVEL rejection so the comparison is like for like; a root-level
    rejection legitimately has no ``field``, covered by the builder tests.
    """
    oracle = build_adcp_validation_error_payload(
        "create_media_buy", "request", validate_request("create_media_buy", {"packages": 1}).issues
    )
    try:
        CreateMediaBuyRequest.model_validate({"packages": 1})
        raise AssertionError("payload validated when the test needs it rejected")
    except ValidationError as error:
        handler = build_adcp_validation_error_payload(
            "create_media_buy", "request", issues_from_validation_error(error)
        )

    assert sorted(oracle) == sorted(handler), (sorted(oracle), sorted(handler))
    for payload in (oracle, handler):
        assert payload["recovery"] == "correctable"
        assert payload["issues"] == payload["details"]["issues"]
        assert payload["field"] == pointer_to_field(payload["issues"][0]["pointer"])
        assert not payload["field"].startswith("/")


def test_version_unsupported_field_comes_from_the_translator():
    """VERSION_UNSUPPORTED gets its ``field`` from the translator too."""
    issue = ValidationIssue(
        pointer="/adcp_version",
        message="no bundled request validator",
        keyword="schema_unavailable",
        schema_path="",
    )
    payload = build_adcp_validation_error_payload("create_media_buy", "request", [issue])
    assert payload["code"] == "VERSION_UNSUPPORTED"
    assert payload["field"] == "adcp_version"
