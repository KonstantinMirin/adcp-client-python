"""A canonical clone enforces every validator its generated source declares.

``canonical_creative.py`` builds the public canonical models with ``create_model``
over the source's bases and a copy of its fields, so the generated class is not in
the clone's MRO. Validators declared on the generated class body — the root-level
required groups ``enforce_root_required_groups`` emits (#1361), the uniqueness and
pairing checks other post-generation fixes inject — reach the clone only because
``_canonical_clone`` carries them across. These tests hold that: a document the
source refuses, the public name refuses too.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import adcp
from adcp.types import canonical_creative

_REQUIRED_GROUP_VALIDATOR = "_require_schema_required_group"


def _canonical_clones() -> dict[str, type[BaseModel]]:
    return {
        name: obj
        for name, obj in vars(canonical_creative).items()
        if isinstance(obj, type)
        and issubclass(obj, BaseModel)
        and getattr(obj, "__adcp_canonical_source__", None) is not None
    }


def _own_validator_names(model: type[BaseModel]) -> set[str]:
    decorators = model.__pydantic_decorators__
    own = vars(model)
    return {
        name for name in (*decorators.model_validators, *decorators.field_validators) if name in own
    }


def test_every_canonical_clone_carries_its_source_model_validators() -> None:
    clones = _canonical_clones()
    assert "CreateMediaBuyRequest" in clones
    missing: dict[str, set[str]] = {}
    for name, clone in clones.items():
        source = clone.__adcp_canonical_source__
        assert source is not None
        carried = set(clone.__pydantic_decorators__.model_validators)
        left_behind = clone.__adcp_canonical_validators_left_behind__
        wanted = {
            validator
            for validator in source.__pydantic_decorators__.model_validators
            if validator in vars(source) and validator not in left_behind
        }
        if wanted - carried:
            missing[name] = wanted - carried
    assert not missing, f"canonical clones dropped source model validators: {missing}"


def test_every_canonical_clone_carries_its_source_field_validators() -> None:
    missing: dict[str, set[str]] = {}
    for name, clone in _canonical_clones().items():
        source = clone.__adcp_canonical_source__
        assert source is not None
        carried = set(clone.__pydantic_decorators__.field_validators)
        left_behind = clone.__adcp_canonical_validators_left_behind__
        wanted = {
            validator
            for validator in source.__pydantic_decorators__.field_validators
            if validator in vars(source) and validator not in left_behind
        }
        if wanted - carried:
            missing[name] = wanted - carried
    assert not missing, f"canonical clones dropped source field validators: {missing}"


def test_a_validator_is_left_behind_only_for_a_field_the_clone_drops() -> None:
    """The clone drops legacy creative identity on purpose; nothing else is skipped."""
    for name, clone in _canonical_clones().items():
        source = clone.__adcp_canonical_source__
        assert source is not None
        for validator, touched in clone.__adcp_canonical_validators_left_behind__.items():
            assert touched, (name, validator)
            assert touched <= set(source.model_fields) - set(clone.model_fields), (
                name,
                validator,
                touched,
            )


def test_canonical_manifest_keeps_its_optional_kind_without_legacy_identity() -> None:
    """``format_id | format_kind`` names a legacy field; the canonical boundary has no
    ``format_id`` to satisfy it, so the group stays on the generated class only."""
    manifest = canonical_creative.CreativeManifest
    assert _REQUIRED_GROUP_VALIDATOR in manifest.__adcp_canonical_validators_left_behind__
    assert manifest.model_validate({"assets": {}}).format_kind is None


def test_before_validators_carry_their_classmethod_binding() -> None:
    """A ``before`` validator is stored as a classmethod; re-decorating the bare
    function hands it ``ValidationInfo`` as ``data`` and Product refused every payload."""
    from adcp.types import Product
    from adcp.types.generated_poc.core.product import Product as Generated

    assert "_coerce_publisher_property_models" in Product.__pydantic_decorators__.model_validators
    assert "_coerce_publisher_property_models" in Generated.__pydantic_decorators__.model_validators


def test_required_group_validators_reach_the_canonical_names() -> None:
    """The gap #1368 documented: the source rejected, the clone accepted."""
    sources_with_groups = {
        name: clone
        for name, clone in _canonical_clones().items()
        if _REQUIRED_GROUP_VALIDATOR
        in clone.__adcp_canonical_source__.__pydantic_decorators__.model_validators
    }
    assert "CreateMediaBuyRequest" in sources_with_groups
    for name, clone in sources_with_groups.items():
        if _REQUIRED_GROUP_VALIDATOR in clone.__adcp_canonical_validators_left_behind__:
            # The group names a legacy identity field the clone drops; see
            # test_a_validator_is_left_behind_only_for_a_field_the_clone_drops.
            continue
        assert _REQUIRED_GROUP_VALIDATOR in clone.__pydantic_decorators__.model_validators, name


_MEDIA_BUY_UNCONDITIONAL_FIELDS: dict[str, Any] = {
    "idempotency_key": "idem-key-0123456789",
    "account": {"account_id": "acct_1"},
    "brand": {"brand_id": "brand_1", "domain": "example.com"},
    "start_time": "2026-11-01T00:00:00Z",
    "end_time": "2026-11-30T00:00:00Z",
}


@pytest.mark.parametrize(
    "model",
    [adcp.CreateMediaBuyRequest, canonical_creative.CreateMediaBuyRequest],
    ids=["adcp", "canonical_creative"],
)
def test_canonical_create_media_buy_request_requires_one_root_anyof_group(
    model: type[BaseModel],
) -> None:
    """A media buy with no packages, no budget and no proposal is refused on every path.

    ``create-media-buy-request.json`` declares the three ways to be a media buy as
    a root ``anyOf``. The generated class gained the rule in #1368; this is the
    controlled probe that showed the public canonical clone still accepted the
    document, held green.
    """
    source = model.__adcp_canonical_source__  # type: ignore[attr-defined]
    with pytest.raises(ValidationError, match="at least one of these field groups"):
        source.model_validate(dict(_MEDIA_BUY_UNCONDITIONAL_FIELDS))
    with pytest.raises(ValidationError, match="at least one of these field groups"):
        model.model_validate(dict(_MEDIA_BUY_UNCONDITIONAL_FIELDS))

    committed = model.model_validate(
        {
            **_MEDIA_BUY_UNCONDITIONAL_FIELDS,
            "proposal_id": "prop_1",
            "total_budget": {"amount": 1000.0, "currency": "USD"},
        }
    )
    assert committed.proposal_id == "prop_1"  # type: ignore[attr-defined]
    assert committed.packages is None  # type: ignore[attr-defined]


def test_canonical_clone_keeps_the_boundary_validator_first() -> None:
    """Carrying source validators must not displace the boundary's own."""
    clone = canonical_creative.CreateMediaBuyRequest
    validators = clone.__pydantic_decorators__.model_validators
    assert "_reject_legacy_creative_identity" in validators
    assert _REQUIRED_GROUP_VALIDATOR in validators
    with pytest.raises(ValidationError, match="legacy creative identity"):
        clone.model_validate(
            {
                **_MEDIA_BUY_UNCONDITIONAL_FIELDS,
                "packages": [
                    {
                        "buyer_ref": "pkg_1",
                        "product_id": "prod_1",
                        "format_ids": [{"agent_url": "https://x.example", "id": "f"}],
                    }
                ],
            }
        )
