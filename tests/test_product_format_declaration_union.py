"""Authoring declarations use generated branches and the schema's root rules."""

from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from typing import Any, get_args

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

import adcp
from adcp.types import (
    CanonicalFormatImage,
    CanonicalFormatKind,
    Format,
    LegacyProductFormatDeclaration,
    ProductFormatDeclaration,
    validate_union,
)
from adcp.types.domains.core.product_format_declaration import (
    ProductFormatDeclaration as GeneratedProductFormatDeclaration,
)
from adcp.validation.schema_loader import get_named_validator

_REF = {"agent_url": "https://creative.example.com", "id": "display_300x250"}
_SCHEMA = {"uri": "https://formats.example.com/custom.json", "digest": "sha256:" + "a" * 64}


def _payload(kind: str = "image") -> dict[str, Any]:
    data: dict[str, Any] = {"format_kind": kind, "params": {}}
    if kind == "custom":
        data.update(format_shape="roadblock", format_schema=_SCHEMA, canonical_formats_only=True)
    elif kind == "seller_rendered_stateful_display":
        data["params"] = {
            "states": [
                {
                    "state_id": "initial",
                    "anchoring": "inline",
                    "breakpoints": [{"breakpoint_id": "desktop", "width": 300, "height": 250}],
                    "close_affordance": False,
                }
            ],
            "initial_state_id": "initial",
            "user_controls": {"dismissible": False, "user_collapsible": False},
        }
    elif kind == "coordinated_placements":
        data["params"] = {
            "components": [
                {
                    "component_id": identifier,
                    "placement_ref": {"placement_id": identifier},
                    "required": True,
                    "format_option_ref": {
                        "scope": "product",
                        "format_option_id": f"{identifier}_image",
                    },
                }
                for identifier in ("left", "right")
            ]
        }
    return data


def test_public_name_is_the_generated_union_with_validation_metadata() -> None:
    assert adcp.ProductFormatDeclaration is ProductFormatDeclaration
    assert ProductFormatDeclaration is not Format
    assert get_args(ProductFormatDeclaration)[0] is get_args(GeneratedProductFormatDeclaration)[0]
    assert LegacyProductFormatDeclaration is GeneratedProductFormatDeclaration


@pytest.mark.parametrize("kind", [kind.value for kind in CanonicalFormatKind])
def test_all_sixteen_generated_branches_are_reachable(kind: str) -> None:
    result = validate_union(ProductFormatDeclaration, _payload(kind))
    assert result.format_kind == kind
    assert type(result).__module__ == "adcp.types.domains.core.product_format_declaration"
    assert type(result) is type(
        TypeAdapter(GeneratedProductFormatDeclaration).validate_python(_payload(kind))
    )


def test_params_are_typed_and_round_trip_with_the_discriminator() -> None:
    result = validate_union(
        ProductFormatDeclaration, {"format_kind": "image", "params": {"width": 300, "height": 250}}
    )
    assert isinstance(result.params, CanonicalFormatImage)
    assert result.params.width == 300
    assert result.model_dump(mode="json", exclude_unset=True) == {
        "format_kind": "image",
        "params": {"width": 300.0, "height": 250.0},
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"canonical_formats_only": True, "v1_format_ref": [_REF]},
        {"canonical_formats_only": True, "v1_format_ref": None},
        {"capability_id": "creative-agent-only"},
        {"publisher_domain": "publisher.example.com"},
        {"tracker_execution_contract": None},
        {"format_shape": None},
        {"format_schema": _SCHEMA},
        {"locale_policy": {"accepted_language_ranges": ["en"]}},
    ],
)
def test_every_root_rule_rejects_with_its_schema_keyword(changes: dict[str, Any]) -> None:
    payload = {**_payload(), **changes}
    validator = get_named_validator("core/product-format-declaration.json")
    assert validator is not None
    expected = next(
        validator.evolve(schema={"allOf": validator.schema["allOf"]}).iter_errors(payload)
    )
    with pytest.raises(ValidationError) as exc:
        validate_union(ProductFormatDeclaration, payload)
    assert exc.value.errors()[0]["type"] == expected.validator


@pytest.mark.parametrize(
    "changes",
    [
        {"v1_format_ref": [_REF]},
        {"canonical_formats_only": True},
        {"publisher_domain": "publisher.example.com", "format_option_id": "image_1"},
        {"locale_policy": {"accepted_language_ranges": ["en"]}, "canonical_formats_only": True},
    ],
)
def test_conforming_root_rule_combinations_still_validate(changes: dict[str, Any]) -> None:
    payload = {**_payload(), **changes}
    assert validate_union(ProductFormatDeclaration, payload).format_kind == "image"


def test_custom_declarations_need_the_source_schemas_complete_contract() -> None:
    assert validate_union(ProductFormatDeclaration, _payload("custom")).format_kind == "custom"
    with pytest.raises(ValidationError):
        validate_union(ProductFormatDeclaration, {"format_kind": "custom", "params": {}})
    without_projection = _payload("custom")
    without_projection.pop("canonical_formats_only")
    with pytest.raises(ValidationError):
        validate_union(ProductFormatDeclaration, without_projection)


def test_existing_generated_instances_preserve_explicit_presence_and_omit_defaults() -> None:
    original = TypeAdapter(GeneratedProductFormatDeclaration).validate_python(_payload())
    assert "v1_format_ref" not in original.model_fields_set
    assert validate_union(ProductFormatDeclaration, original) is original
    invalid = original.model_copy(update={"canonical_formats_only": True, "v1_format_ref": None})
    with pytest.raises(ValidationError) as exc:
        validate_union(ProductFormatDeclaration, invalid)
    assert exc.value.errors()[0]["type"] == "not"


@pytest.mark.parametrize(
    "changes",
    [{"params": {"nested": {"api_token": "credential"}}}, {"upstream_secret": "credential"}],
)
def test_credential_screening_survives_the_public_rebinding(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="credential-shaped key"):
        validate_union(ProductFormatDeclaration, {**_payload(), **changes})


def test_validation_does_not_mutate_the_buyers_document() -> None:
    payload = {**_payload(), "v1_format_ref": [_REF]}
    original = copy.deepcopy(payload)
    validate_union(ProductFormatDeclaration, payload)
    assert payload == original


def test_authoring_union_can_be_used_in_adopter_models() -> None:
    class ProductCatalog(BaseModel):
        format_options: list[ProductFormatDeclaration]

    result = ProductCatalog.model_validate({"format_options": [_payload()]})
    assert result.format_options[0].format_kind == "image"
    with pytest.raises(ValidationError):
        ProductCatalog.model_validate(
            {
                "format_options": [
                    {**_payload(), "canonical_formats_only": True, "v1_format_ref": [_REF]}
                ]
            }
        )


def test_open_consumer_format_and_params_helper_remain_available() -> None:
    future = Format(format_kind="future_kind", params={})
    assert future.model_dump()["format_kind"] == "future_kind"
    image = Format(format_kind="image", params={"width": 300})
    assert image.params_as(CanonicalFormatImage).width == 300


def test_concurrent_authoring_validation_uses_independent_resolvers() -> None:
    def validate_batch(_: int) -> None:
        for _ in range(20):
            assert validate_union(ProductFormatDeclaration, _payload()).format_kind == "image"
            with pytest.raises(ValidationError):
                validate_union(
                    ProductFormatDeclaration,
                    {**_payload(), "canonical_formats_only": True, "v1_format_ref": [_REF]},
                )

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(validate_batch, range(4)))
