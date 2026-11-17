"""Public models compose with generated capability models without dict conversion.

Two premises this file was built on are gone, and both are decisions.

**There is one tree.** The file imported each class twice -- once from
``adcp.types`` and once from ``adcp.types.domains.bundled...`` -- and asserted
the two were distinct objects with equal wire schemas, which is what an identity
patch across two generated trees needs policing. This emission compiles one
bundle into one tree, there is no ``bundled`` package, and section 4's "one
class per SUBJECT, not per position" is why: the same subject cannot have a
second class to drift from.

**A constrained scalar is not a class.** ``PublisherDomain`` is declared
DOCUMENT-NO-WORD-NO-IDENTITY and ``PrimaryCountry`` resolves to an ``Annotated``
string carrying the document's pattern. Section 4's own rule is that an alias
names a CONSTRAINT and never a concept, because one pattern sits at several
positions and a concept name is right for one of them and wrong for the rest.
So a publisher domain travels as a ``str`` the pattern admits, and the claim
left to make about it is that the constraint still binds -- which
``test_composability_patch_preserves_generated_field_constraints`` and
``test_a_portfolio_refuses_a_domain_the_pattern_does_not_admit`` make.
"""

from __future__ import annotations

import inspect
from typing import Any, get_args

import pytest
from adcp.types.domains.protocol.get_adcp_capabilities_response import (
    AcceptancePolicyDiscovery as GeneratedAcceptancePolicyDiscovery,
)
from pydantic import BaseModel, TypeAdapter, ValidationError

import adcp.types as public_types
import adcp.types.capabilities as capability_types
from adcp.decisioning.capabilities import MediaBuy, Portfolio
from adcp.types import AcceptancePolicyDiscovery


def _model_references(annotation: Any) -> list[type[BaseModel]]:
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return [annotation]
    return [model for arg in get_args(annotation) for model in _model_references(arg)]


def test_public_models_compose_with_capability_models() -> None:
    discovery = AcceptancePolicyDiscovery(
        catalog_url="https://example.com/acceptance-policy-catalog.json",
        catalog_digest=f"sha256:{'a' * 64}",
    )
    media_buy = MediaBuy(acceptance_policy_discovery=discovery)
    assert media_buy.acceptance_policy_discovery is discovery

    portfolio = Portfolio(
        publisher_domains=["publisher.example"],
        primary_countries=["US"],
    )
    assert portfolio.publisher_domains == ["publisher.example"]
    assert portfolio.primary_countries == ["US"]


def test_capability_dicts_parse_to_canonical_public_models() -> None:
    media_buy = MediaBuy.model_validate(
        {
            "acceptance_policy_discovery": {
                "catalog_url": "https://example.com/acceptance-policy-catalog.json",
                "catalog_digest": f"sha256:{'b' * 64}",
            }
        }
    )
    assert isinstance(media_buy.acceptance_policy_discovery, AcceptancePolicyDiscovery)

    portfolio = Portfolio.model_validate(
        {"publisher_domains": ["publisher.example"], "primary_countries": ["US"]}
    )
    assert portfolio.publisher_domains == ["publisher.example"]
    assert portfolio.primary_countries == ["US"]


def test_composability_patch_preserves_generated_field_constraints() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        Portfolio(publisher_domains=[])


def test_a_portfolio_refuses_a_domain_the_pattern_does_not_admit() -> None:
    """The constraint travels with the type even though no class carries a name.

    ``core/publisher-property-selector.json``'s domain pattern is lowercase
    dot-separated LDH labels; this is what remains to say once the concept name
    is gone, and it is the half a ``str`` field could silently lose.
    """
    with pytest.raises(ValidationError):
        Portfolio(publisher_domains=["Publisher.Example"])
    with pytest.raises(ValidationError):
        Portfolio(publisher_domains=["publisher.example"], primary_countries=["usa"])


def test_the_public_name_and_the_generated_one_are_one_object() -> None:
    """One class per subject, so there is no second object to drift from.

    This replaces a parametrized check that the public class and a second,
    ``bundled`` generated class were DISTINCT with equal wire schemas. The
    ``bundled`` tree does not exist, and ``TypeAdapter`` equality is kept as the
    reading that would still catch a split if one reappeared.
    """
    assert AcceptancePolicyDiscovery is GeneratedAcceptancePolicyDiscovery
    assert (
        TypeAdapter(AcceptancePolicyDiscovery).json_schema()
        == TypeAdapter(GeneratedAcceptancePolicyDiscovery).json_schema()
    )


def test_every_capability_name_collision_is_two_different_subjects() -> None:
    """A nested class the flat name does not bind must be a DIFFERENT subject.

    This replaces a pinned list of four reviewed collisions. The list said
    "these are intentionally different concepts that happen to share a schema
    name" and then asked only that the set of NAMES match, so a collision
    between two classes of the SAME subject -- the thing section 4 forbids --
    would have satisfied it as long as somebody had written the name down.

    The reading it should have had is in the classes: each carries
    ``__adcp_schema__``, so "different concept" is a measurable claim and a
    collision is admissible exactly when the two pointers differ. Three of the
    four pinned rows are gone because the nested class IS the public one now,
    which is the same rule being satisfied rather than policed.
    """
    collisions: dict[tuple[str, str, str], tuple[object, object]] = {}

    for export_name in capability_types.__all__:
        capability_model = getattr(capability_types, export_name)
        if not inspect.isclass(capability_model) or not issubclass(capability_model, BaseModel):
            continue
        for field_name, field in capability_model.model_fields.items():
            for nested_model in _model_references(field.annotation):
                public_model = getattr(public_types, nested_model.__name__, None)
                if (
                    inspect.isclass(public_model)
                    and issubclass(public_model, BaseModel)
                    and nested_model is not public_model
                ):
                    collisions[(export_name, field_name, nested_model.__name__)] = (
                        getattr(nested_model, "__adcp_schema__", None),
                        getattr(public_model, "__adcp_schema__", None),
                    )

    assert collisions, "the sweep found no collisions at all, so it grades nothing"
    same_subject = {
        where: pointers for where, pointers in collisions.items() if pointers[0] == pointers[1]
    }
    assert not same_subject, (
        "a nested class and the public class of the same name state the SAME "
        f"subject, which section 4 forbids: {same_subject}"
    )
    assert all(
        nested is not None and public is not None for nested, public in collisions.values()
    ), f"a colliding class carries no __adcp_schema__ to compare: {collisions}"
