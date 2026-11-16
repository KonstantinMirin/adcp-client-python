"""Optional boolean constants must not invent capabilities or response state (#1347)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from adcp.types import (
    AcceptancePolicyProfile,
    ControlMediaBuyResponse,
    CreateMediaBuyRequest,
    ListProductsResponse,
    Product,
    RefineProposalsRequest,
)

_GENERATED_DIR = Path(__file__).resolve().parents[1] / "src/adcp/types/domains"
_POSTAL_FLAGS = (
    "us_zip",
    "us_zip_plus_four",
    "gb_outward",
    "gb_full",
    "ca_fsa",
    "ca_full",
    "de_plz",
    "fr_code_postal",
    "au_postcode",
    "ch_plz",
    "at_plz",
)


def test_generated_boolean_literals_have_no_boolean_defaults() -> None:
    """Catch future const-default misfires, including fields wrapped in Annotated."""
    violations = []
    for path in sorted(_GENERATED_DIR.rglob("*.py")):
        fields = (
            field
            for cls in ast.walk(ast.parse(path.read_text()))
            if isinstance(cls, ast.ClassDef)
            for field in cls.body
            if isinstance(field, ast.AnnAssign)
        )
        for node in fields:
            if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, bool):
                continue
            for annotation in ast.walk(node.annotation):
                if (
                    isinstance(annotation, ast.Subscript)
                    and isinstance(annotation.value, ast.Name)
                    and annotation.value.id == "Literal"
                    and isinstance(annotation.slice, ast.Constant)
                    and isinstance(annotation.slice.value, bool)
                ):
                    violations.append(f"{path.relative_to(_GENERATED_DIR)}:{node.lineno}")
    assert not violations, f"Boolean const fields default to phantom data: {violations}"


@pytest.mark.parametrize("field", ["geo_postal_areas", "geo_postal_areas_exclude"])
@pytest.mark.parametrize("support", [{"US": ["zip"]}, {"BR": ["cep"]}, True])
def test_postal_overlay_support_preserves_declared_systems(
    field: str, support: dict[str, list[str]] | bool
) -> None:
    # Exercise the nested product type through the public Product surface.
    adapter = TypeAdapter(Product.model_fields["overlay_support"].annotation)
    payload = {field: support}
    model = adapter.validate_python(payload)
    assert model.model_dump(mode="json", exclude_none=True) == payload


@pytest.mark.parametrize("field", ["geo_postal_areas", "geo_postal_areas_exclude"])
@pytest.mark.parametrize("flag", _POSTAL_FLAGS)
def test_postal_overlay_support_preserves_only_explicit_legacy_flags(field: str, flag: str) -> None:
    adapter = TypeAdapter(Product.model_fields["overlay_support"].annotation)
    payload = {field: {flag: True}}
    model = adapter.validate_python(payload)
    assert model.model_dump(mode="json", exclude_none=True) == payload
    # **The deprecation is this document's own and not a sibling's.** Both fields reach
    # `core/positive-postal-area-support.json`, whose `allOf[0]` is a `$ref` to
    # `core/postal-area-support.json` -- which marks all 11 flags `deprecated: true` --
    # while its `allOf[1]` adds the `const: true` the `pytest.raises` below grades. Under
    # `allOf` both conjuncts apply to the same instance, so the mark is stated AT THIS
    # NODE; the emission agrees about the relation (`class PositivePostalAreaSupport(
    # PostalAreaSupport)`) and then redeclares the 11 flags to carry the `const`, which
    # drops the base's `Field(deprecated=True)`.
    #
    # LEFT RED ON PURPOSE. The repair is `intersect.RENDERED`, which names `default` and
    # `description` as the annotations a narrowing restatement inherits and omits
    # `deprecated` even though `render.py` renders it -- `codegen/` is not this
    # worktree's to write. 21 fields across 11 classes lose a base's mark this way; see
    # FINDINGS-features.md.
    assert type(getattr(model, field)).model_fields[flag].deprecated is True
    with pytest.raises(ValidationError):
        adapter.validate_python({field: {flag: False}})


@pytest.mark.parametrize(
    "response_type,payload",
    [
        (
            ListProductsResponse,
            {"outcome": "listed", "products": [], "feed_version": "v1", "cache_scope": "public"},
        ),
        (
            ListProductsResponse,
            {"outcome": "unchanged", "feed_version": "v1", "cache_scope": "account"},
        ),
        (ControlMediaBuyResponse, {"status": "completed", "media_buy_id": "mb_1", "revision": 1}),
        (ControlMediaBuyResponse, {"status": "submitted", "task_id": "task_1"}),
        (
            ControlMediaBuyResponse,
            {"status": "failed", "errors": [{"code": "INVALID_REQUEST", "message": "Invalid"}]},
        ),
    ],
)
def test_responses_only_emit_replayed_when_supplied(
    response_type: Any, payload: dict[str, Any]
) -> None:
    adapter = TypeAdapter(response_type)
    model = adapter.validate_python(payload)
    assert model.replayed is None
    assert "replayed" not in model.model_dump(mode="json", exclude_none=True)

    replayed = adapter.validate_python({**payload, "replayed": True})
    assert replayed.model_dump(mode="json", exclude_none=True)["replayed"] is True
    with pytest.raises(ValidationError):
        adapter.validate_python({**payload, "replayed": False})


@pytest.mark.parametrize(
    "owner,field,payload,constant_field",
    [
        (CreateMediaBuyRequest, "bidding", {"bid_amount": 5}, "automatic"),
        (Product, "media_buy_support", {"future_capability": True}, "frequency_cap"),
        # `(GetProductsRequest, "required_media_buy_support", {}, "frequency_cap")` was
        # here and the document makes it impossible, not merely wrong.
        # `core/media-buy-support-requirements.json` states `minProperties: 1`, declares
        # exactly two properties, and `dependencies: {"frequency_cap_constraints":
        # ["frequency_cap"]}` -- so a valid instance has at least one property, and the
        # only property that can stand alone IS `frequency_cap`.  No valid payload omits
        # it, so "the constant is omitted rather than defaulted" has nothing to be shown
        # on here.  The three cases left all have a document with an unrelated property to
        # carry the payload.
        (
            AcceptancePolicyProfile,
            "scope",
            {
                "subject_categories": ["alcohol"],
                "applies_to": ["creative"],
                "jurisdictions": ["US"],
            },
            "all_jurisdictions",
        ),
    ],
)
def test_multiline_boolean_constants_preserve_omission(
    owner: Any, field: str, payload: dict[str, Any], constant_field: str
) -> None:
    adapter = TypeAdapter(owner.model_fields[field].annotation)
    model = adapter.validate_python(payload)
    assert constant_field not in model.model_dump(mode="json", exclude_none=True)
    explicit_payload = {} if constant_field == "automatic" else payload
    explicit = adapter.validate_python({**explicit_payload, constant_field: True})
    assert explicit.model_dump(mode="json", exclude_none=True)[constant_field] is True
    with pytest.raises(ValidationError):
        adapter.validate_python({**payload, constant_field: False})


def test_proposal_refinement_does_not_remove_frequency_cap_by_default() -> None:
    request = RefineProposalsRequest.model_validate(
        {
            "idempotency_key": "refine-proposal-001",
            "refinements": [{"proposal_id": "p_1", "action": "revise", "ask": "Extend flight"}],
        }
    )
    refinement = request.model_dump(mode="json", exclude_none=True)["refinements"][0]
    assert "remove_media_buy_frequency_cap" not in refinement
    explicit = RefineProposalsRequest.model_validate(
        {
            "idempotency_key": "refine-proposal-002",
            "refinements": [
                {"proposal_id": "p_1", "action": "revise", "remove_media_buy_frequency_cap": True}
            ],
        }
    )
    assert (
        explicit.model_dump(mode="json", exclude_none=True)["refinements"][0][
            "remove_media_buy_frequency_cap"
        ]
        is True
    )
