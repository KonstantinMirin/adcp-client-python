# ruff: noqa: E501
"""Capability sub-models surfaced from the bundled ``get_adcp_capabilities_response`` schema.

Adopters declaring ``DecisioningCapabilities`` for a platform (see
:mod:`adcp.decisioning.platform`) need access to the full set of
typed capability sub-models — ``Account``, ``MediaBuy``, ``Targeting``,
``GeoMetros``, ``Idempotency`` etc. The generated Pydantic classes
already exist in
``adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response``,
but three of them (``Account``, ``MediaBuy``, ``Creative``) collide on
name with unrelated wire types already exported from :mod:`adcp.types`.

This module sits in the import-architecture whitelist (alongside
``stable.py``, ``aliases.py``, ``_ergonomic.py``) for direct
``generated_poc`` imports. It pulls the capabilities sub-models out
under disambiguated names, so the colliding three don't shadow the
wire types when re-exported from :mod:`adcp.types`. Adopters never
import from this module directly — :mod:`adcp.decisioning.capabilities`
is the canonical adopter-facing namespace and re-aliases the three
disambiguated names back to their wire-spec form.

Layering::

    generated_poc/bundled/protocol/get_adcp_capabilities_response.py
        ↓ (this module — disambiguates colliding names)
    adcp.types.capabilities
        ↓ (re-exported from)
    adcp.types.__init__
        ↓ (re-aliased to wire-spec names within submodule namespace)
    adcp.decisioning.capabilities  ← adopter-facing import path
"""

from __future__ import annotations

from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    A2ui,
    Adcp,
    AgeRestriction,
    AttributionWindow,
    AudienceTargeting,
    Avatar,
    Brand,
    Commerce,
    ComplianceTesting,
    Components,
    CompromiseNotification,
    ConversionTracking,
    CreativeSpecs,
    Endpoint,
    Execution,
    Features,
    GeoMetros,
    GeoPostalAreas,
    GeoProximity,
    Governance,
    Idempotency,
    Identity,
    KeyOrigins,
    KeywordTargets,
    MatchingLatencyHours,
    Modalities,
    NegativeKeywords,
    Portfolio,
    RequestSigning,
    Signals,
    Specialism,
    SponsoredIntelligence,
    SupportedProtocol,
    Targeting,
    Transport,
    TrustedMatch,
    Video,
    Voice,
    WebhookSigning,
)

# Top-level capability protocol blocks.
#
# Three names (``Account``, ``MediaBuy``, ``Creative``) collide with
# wire types in :mod:`adcp.types`. Imported here under
# ``CapabilitiesAccount`` / ``CapabilitiesMediaBuy`` /
# ``CapabilitiesCreative`` so the re-export from :mod:`adcp.types`
# doesn't shadow the wire types. The submodule
# :mod:`adcp.decisioning.capabilities` re-aliases them back to ``Account``
# / ``MediaBuy`` / ``Creative`` within its own namespace, so adopters
# writing the ``DecisioningCapabilities`` declaration get the wire-spec
# names.
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    Account as CapabilitiesAccount,
)

# ``Capabilities`` (line 580 of the generated module) is the SI-block's
# inner ``capabilities`` field type — modalities / components / commerce
# / a2ui / mcp_apps. Re-aliased here as ``SiCapabilities`` to disambiguate
# from :class:`adcp.decisioning.DecisioningCapabilities` and to make the
# import site self-documenting.
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    Capabilities as SiCapabilities,
)
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    Creative as CapabilitiesCreative,
)

# ``Idempotency`` ships as a ``oneOf`` on the wire (``IdempotencySupported``
# vs ``IdempotencyUnsupported``) — the codegen names them ``Idempotency``
# and ``Idempotency3`` (with the numbered variant covering the
# ``supported: false`` arm). Surface the union halves under stable
# semantic names so adopters can construct either side without remembering
# which numbered variant is which.
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    Idempotency as IdempotencySupported,
)
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    Idempotency3 as IdempotencyUnsupported,
)
from adcp.types.generated_poc.bundled.protocol.get_adcp_capabilities_response import (
    MediaBuy as CapabilitiesMediaBuy,
)

__all__ = [
    "A2ui",
    "Adcp",
    "AgeRestriction",
    "AttributionWindow",
    "AudienceTargeting",
    "Avatar",
    "Brand",
    "CapabilitiesAccount",
    "CapabilitiesCreative",
    "CapabilitiesMediaBuy",
    "Commerce",
    "ComplianceTesting",
    "Components",
    "CompromiseNotification",
    "ConversionTracking",
    "CreativeSpecs",
    "Endpoint",
    "Execution",
    "Features",
    "GeoMetros",
    "GeoPostalAreas",
    "GeoProximity",
    "Governance",
    "Idempotency",
    "IdempotencySupported",
    "IdempotencyUnsupported",
    "Identity",
    "KeyOrigins",
    "KeywordTargets",
    "MatchingLatencyHours",
    "Modalities",
    "NegativeKeywords",
    "Portfolio",
    "RequestSigning",
    "Signals",
    "SiCapabilities",
    "Specialism",
    "SponsoredIntelligence",
    "SupportedProtocol",
    "Targeting",
    "Transport",
    "TrustedMatch",
    "Video",
    "Voice",
    "WebhookSigning",
]
