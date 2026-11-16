"""Tests for backward compatibility aliases.

Validates that deprecated type names still import and resolve to the correct
new types. This is the core safety net for the schema sync — consumers using
old names must not get ImportError or silently wrong types.
"""

from __future__ import annotations

import pytest


class TestPricingTypeRenames:
    """Upstream merged auction/fixed variants into single types."""

    def test_cpm_auction_imports_from_adcp(self):
        from adcp import CpmAuctionPricingOption, CpmPricingOption

        assert CpmAuctionPricingOption is CpmPricingOption

    def test_cpm_fixed_rate_imports_from_adcp(self):
        from adcp import CpmFixedRatePricingOption, CpmPricingOption

        assert CpmFixedRatePricingOption is CpmPricingOption

    def test_vcpm_auction_imports_from_adcp(self):
        from adcp import VcpmAuctionPricingOption, VcpmPricingOption

        assert VcpmAuctionPricingOption is VcpmPricingOption

    def test_vcpm_fixed_rate_imports_from_adcp(self):
        from adcp import VcpmFixedRatePricingOption, VcpmPricingOption

        assert VcpmFixedRatePricingOption is VcpmPricingOption

    def test_cpm_auction_imports_from_types(self):
        from adcp.types import CpmAuctionPricingOption, CpmPricingOption

        assert CpmAuctionPricingOption is CpmPricingOption

    def test_vcpm_auction_imports_from_types(self):
        from adcp.types import VcpmAuctionPricingOption, VcpmPricingOption

        assert VcpmAuctionPricingOption is VcpmPricingOption


class TestActivationKeyRenames:
    """Upstream renamed property_id/property_tag to segment_id/key_value."""

    def test_property_id_activation_key_imports(self):
        from adcp import PropertyIdActivationKey, SegmentIdActivationKey

        assert PropertyIdActivationKey is SegmentIdActivationKey

    def test_property_tag_activation_key_imports(self):
        from adcp import KeyValueActivationKey, PropertyTagActivationKey

        assert PropertyTagActivationKey is KeyValueActivationKey

    def test_property_id_imports_from_types(self):
        from adcp.types import PropertyIdActivationKey, SegmentIdActivationKey

        assert PropertyIdActivationKey is SegmentIdActivationKey

    def test_property_tag_imports_from_types(self):
        from adcp.types import KeyValueActivationKey, PropertyTagActivationKey

        assert PropertyTagActivationKey is KeyValueActivationKey


class TestPreviewAliasRenames:
    """PreviewCreativeRequest collapsed into a single class with a request_type
    enum; the per-mode Request aliases (Format/Manifest/Static/Interactive, Single/
    Batch/Variant) are no longer distinct types and their aliases were removed.
    The remaining response aliases are exposed only through the explicit
    legacy surface."""

    def test_preview_creative_static_response(self):
        from adcp import LegacyPreviewCreativeResponse1, LegacyPreviewCreativeSingleResponse

        assert LegacyPreviewCreativeSingleResponse is LegacyPreviewCreativeResponse1

    def test_preview_creative_interactive_response(self):
        from adcp import LegacyPreviewCreativeBatchResponse, LegacyPreviewCreativeResponse2

        assert LegacyPreviewCreativeBatchResponse is LegacyPreviewCreativeResponse2


class TestStatusTypeBackwardCompat:
    """`Status` is DECLINED as a flat word; the delivery statuses keep their path."""

    def test_the_bare_word_status_is_declined_and_says_so(self):
        """Three documents state a `Status`, so the flat namespace binds none of them.

        `adcp.types._surface._flat` states the rule in its own docstring: "A word
        more than one domain publishes is DECLINED rather than resolved to a
        winner ... picking one would hand a consumer a class whose document they
        did not name." The decline is recorded with its candidates, so the answer
        to `from adcp.types import Status` is the candidate list and not a guess.

        What stood here asserted `Status is MediaBuyDeliveryStatus` -- the
        previous generator's resolution of exactly this collision.
        """
        import adcp.types._surface._flat as flat

        assert flat.__adcp_alias_declined__["Status"] == (
            "governance.sync_plans_response.PlansItemStatus",
            "media_buy.get_products_response.RefinementAppliedItemRequestStatus",
            "sponsored_intelligence.si_sponsored_context_receipt.HostReceiptStatus",
        )
        with pytest.raises(ImportError):
            from adcp.types import Status  # noqa: F401

    def test_the_delivery_status_enum_accepts_its_delivery_values(self):
        """The subject the old flat word meant, reached at its own domain path."""
        from adcp.types.media_buy import (
            MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus as DeliveryStatus,
        )

        for value in ["pending", "active", "paused", "completed", "failed"]:
            assert DeliveryStatus(value).value == value


class TestCatalogGroupBinding:
    """CatalogFieldBinding1 should have a semantic alias."""

    def test_catalog_group_binding_imports(self):
        from adcp.types import CatalogGroupBinding

        assert CatalogGroupBinding is not None

    def test_catalog_group_binding_is_correct_type(self):
        from adcp.types import CatalogGroupBinding
        from adcp.types._generated import CatalogFieldBinding1

        assert CatalogGroupBinding is CatalogFieldBinding1

    def test_catalog_group_binding_has_correct_kind(self):
        from adcp.types import CatalogGroupBinding

        assert "kind" in CatalogGroupBinding.__annotations__


class TestBrandIdentity:
    """Private generated Brand imports have a collision-safe public target."""

    def test_brand_identity_is_one_object_at_its_one_domain_path(self):
        """`brand.json#/definitions/brand` has ONE public path, and two alias words.

        §1: "There is one import path per class, and never a second way to reach
        the same class. ... The one path is the domain surface's." That path is
        `adcp.types.brand.BrandDiscoveryBrand`. `BrandIdentity` is reading 10's
        alias word for it and resolves at the flat compatibility namespace only;
        `adcp.types.buyer` publishes no such name, because the class's declaring
        position is not in that domain.
        """
        from adcp import BrandIdentity as RootBrandIdentity
        from adcp.types import BrandIdentity
        from adcp.types.brand import BrandDiscoveryBrand
        from adcp.types.domains.brand import Brand

        assert RootBrandIdentity is BrandIdentity is BrandDiscoveryBrand is Brand

        import adcp.types.buyer as buyer

        assert not hasattr(buyer, "BrandIdentity")

    def test_brand_identity_preserves_brand_json_shape(self):
        from adcp.types import BrandIdentity

        brand = BrandIdentity(id="acme", names=[{"en": "Acme"}])
        # A scalar root and a mapping root are their own Python values here --
        # §4 compiles both to an alias, so neither carries a `.root` wrapper.
        assert brand.id == "acme"
        assert brand.names[0] == {"en": "Acme"}
        assert len(BrandIdentity.model_fields) == 29

    def test_brand_identity_field_contract_and_collision_separation(self):
        from adcp.types import BrandIdentity
        from adcp.types.domains.protocol.get_adcp_capabilities_response import (
            Brand as CapabilitiesBrand,
        )

        assert BrandIdentity is not CapabilitiesBrand
        assert tuple(BrandIdentity.model_fields) == (
            "id",
            "url",
            "identity_relying_parties",
            "names",
            "keller_type",
            "parent_brand",
            "description",
            "industries",
            "target_audience",
            "logos",
            "colors",
            "fonts",
            "tone",
            "tagline",
            "assets",
            "properties",
            "product_catalog",
            "privacy_policy_url",
            "data_subject_contestation",
            "disclaimers",
            "trademarks",
            "voice_synthesis",
            "avatar",
            "visual_guidelines",
            "agents",
            "brand_agent",
            "rights_agent",
            "contact",
            "collections",
        )


class TestAllBackwardCompatInAll:
    """All backward-compat aliases must appear in __all__."""

    def test_all_compat_aliases_in_types_all(self):
        import adcp.types

        compat_aliases = [
            "CpmAuctionPricingOption",
            "CpmFixedRatePricingOption",
            "VcpmAuctionPricingOption",
            "VcpmFixedRatePricingOption",
            "PropertyIdActivationKey",
            "PropertyTagActivationKey",
        ]
        for alias in compat_aliases:
            assert alias in adcp.types.__all__, f"{alias} missing from types.__all__"

    def test_all_compat_aliases_in_adcp_all(self):
        import adcp

        compat_aliases = [
            "CpmAuctionPricingOption",
            "CpmFixedRatePricingOption",
            "VcpmAuctionPricingOption",
            "VcpmFixedRatePricingOption",
            "PropertyIdActivationKey",
            "PropertyTagActivationKey",
        ]
        for alias in compat_aliases:
            assert alias in adcp.__all__, f"{alias} missing from adcp.__all__"
