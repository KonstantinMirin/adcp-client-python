"""Regression coverage for enum-reference fixes in AdCP 3.1.14."""

from adcp.types import AdcpProtocol, CatalogType, PropertyType
from adcp.types.domains.core.registry_event import (
    RegistryEventAgentVerificationEarnedAgentPayload,
)
from adcp.types.domains.formats.canonical.sponsored_placement import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven,
)
from adcp.types.domains.protocol.get_adcp_capabilities_response import TrustedMatch


def test_registry_badge_role_uses_canonical_protocol_enum() -> None:
    # `core/registry-event.json#/$defs/badgeRole` is what 3.1.14 re-pointed at
    # `enums/adcp-protocol.json`, and the pinned bundle carries that target
    # INLINED into the entry. So the entry is not a wrapper over the enum --
    # it IS the enum, and the one class for it is `AdCPProtocol`. The claim is
    # therefore asked of the only instance location the entry has in this
    # document: the `role` property of the badge-earned payload.
    field = RegistryEventAgentVerificationEarnedAgentPayload.model_fields["role"]
    assert field.annotation is AdcpProtocol

    payload = RegistryEventAgentVerificationEarnedAgentPayload.model_validate(
        {
            "agent_url": "https://agent.example.com",
            "role": "measurement",
            "verified_specialisms": ["brand-safety"],
        }
    )

    assert payload.role is AdcpProtocol.measurement
    assert payload.model_dump(mode="json")["role"] == "measurement"


def test_sponsored_placement_accepts_promotion_catalog_type() -> None:
    declaration = CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven(
        supported_catalog_types=["promotion"]
    )

    assert declaration.supported_catalog_types == [CatalogType.promotion]


def test_trusted_match_accepts_linear_tv_surface() -> None:
    capability = TrustedMatch(surfaces=["linear_tv"])

    assert capability.surfaces == [PropertyType.linear_tv]
