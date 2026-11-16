"""Public-API surface for canonical-formats types (AdCP 3.1).

Guards that the canonical-formats types are reachable from
:mod:`adcp.types` (rather than only from a domain path). Failures
here mean adopter code that does ``from adcp.types import …`` will
break — the public surface is part of the contract.
"""

from __future__ import annotations

import adcp.types as types

# Every name here is this emission's, derived by §4: a document's root takes
# the document's title and a NESTED node takes ``pascal_case(property)``
# prefixed by its declaring position. So ``asset_source`` is named for the
# format that declares it (and there are TWO of them, which is why there is no
# one ``CanonicalAssetSource``), ``seller_preference`` is named for the
# "Product Format Declaration" document, and the mapping registry's nested
# nodes carry the chain down from its root.
_EXPECTED_EXPORTS = (
    # Kind enum + projection ref
    "CanonicalFormatKind",
    "CanonicalProjectionReference",
    "CanonicalFormatHostedAudioAssetSource",
    "CanonicalFormatNativeInFeedAssetSource",
    "CanonicalProjectionSlotOverride",
    # Declaration
    "ProductFormatDeclaration",
    "ProductFormatDeclarationSellerPreference",
    # 13 canonical format classes
    "CanonicalFormatBase",
    "CanonicalFormatBaseCompositionModel",
    "CanonicalFormatImage",
    "CanonicalFormatHtml5Banner",
    "CanonicalFormatDisplayTag",
    "CanonicalFormatImageCarousel",
    "CanonicalFormatHostedVideo",
    "CanonicalFormatVastVideo",
    "CanonicalFormatHostedAudio",
    "CanonicalFormatDaastAudio",
    "CanonicalFormatNativeInFeed",
    "CanonicalFormatResponsiveCreative",
    "CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement",
    "CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven",
    # Pixel tracker asset
    "PixelTrackerAsset",
    "PixelTrackerEvent",
    "PixelTrackerMethod",
    # Registry types
    "V1V2CanonicalFormatMappingRegistry",
    "V1CanonicalMapping",
    "V1PatternFormatIdGlob",
    "V1PatternStructural",
    "V1V2CanonicalFormatMappingRegistryMappingsItem",
    "V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural",
    "V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions",
    "V1V2CanonicalFormatMappingRegistryMappingsItemV2",
    # Error envelope sub-enums (for SDK-source advisory construction)
    "Recovery",
    "Source",
)


def test_canonical_formats_symbols_present_on_adcp_types() -> None:
    """Every expected name is reachable as ``adcp.types.<name>``."""
    missing = [name for name in _EXPECTED_EXPORTS if not hasattr(types, name)]
    assert not missing, f"missing public-API exports: {missing}"


def test_canonical_formats_symbols_in_dunder_all() -> None:
    """Every expected name appears in ``adcp.types.__all__``."""
    declared = set(getattr(types, "__all__", []))
    missing = [name for name in _EXPECTED_EXPORTS if name not in declared]
    assert not missing, f"public-API exports not declared in __all__: {missing}"


def test_canonical_format_kind_has_16_values() -> None:
    """Adding/removing a canonical kind is a wire-breaking change — pin the count."""
    from adcp.types import CanonicalFormatKind

    assert len(CanonicalFormatKind) == 16


def test_sdk_id_reachable_via_public_package_path() -> None:
    """``SDK_ID`` is documented as importable from :mod:`adcp.canonical_formats`.

    It's resolved lazily via module ``__getattr__`` so this also
    exercises that dispatch path against the documented import.
    """
    from adcp.canonical_formats import SDK_ID

    assert isinstance(SDK_ID, str)
    assert SDK_ID.startswith("adcontextprotocol-adcp-python@")


def test_sdk_id_uses_canonical_distribution_prefix() -> None:
    """Dev installs and wheel installs MUST emit the same ``sdk_id`` prefix
    so the multi-hop ``(code, field, sdk_id)`` dedup contract holds across
    deployment shapes."""
    from adcp.canonical_formats import SDK_ID

    prefix, _, _ = SDK_ID.partition("@")
    assert prefix == "adcontextprotocol-adcp-python"


def test_canonical_kind_values_match_spec() -> None:
    """The 16 wire values are the canonical-formats vocabulary; lock them in."""
    from adcp.types import CanonicalFormatKind

    actual = {k.value for k in CanonicalFormatKind}
    expected = {
        "image",
        "html5",
        "display_tag",
        "image_carousel",
        "video_hosted",
        "video_vast",
        "audio_hosted",
        "audio_vast",
        "audio_daast",
        "sponsored_placement",
        "native_in_feed",
        "responsive_creative",
        "agent_placement",
        "seller_rendered_stateful_display",
        "coordinated_placements",
        "custom",
    }
    assert actual == expected
