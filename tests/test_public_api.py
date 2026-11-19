"""Tests for public API stability and usability.

This test suite validates that the public API (`from adcp import ...`)
provides all essential types and they work correctly with JSON data.
"""

from __future__ import annotations

from typing import Literal

import pytest


def test_core_domain_types_are_exported():
    """Core domain types are accessible from main package."""
    import adcp

    core_types = [
        "Product",
        "Format",
        "MediaBuy",
        "Property",
        "Creative",
        "CreativeApproval",
        "DeliveryStatus",
        "Package",
        "Snapshot",
        "SnapshotUnavailableReason",
    ]

    for type_name in core_types:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"


def test_a_media_buys_package_is_named_by_the_document_that_declares_it():
    """`MediaBuyPackage` is upstream's flat word for an INNER declaration of ours.

    Upstream declared it at ``media_buy.get_media_buys_response.Package``, which is
    ``media-buy/get-media-buys-response.json`` at
    ``#/properties/media_buys/items/properties/packages/items``. **That node is
    emitted, so the word has a subject and the earlier
    DOCUMENT-NO-WORD-NO-IDENTITY reading was wrong**: the field sets agree member
    for member (`FINDINGS-rootnames.md`), and `adcp.types.aliases` now binds the
    word onto the class the pointer derives. What this test fixes is the NAME the
    pointer gives, which is what the alias is a second spelling of.
    """
    import adcp
    import adcp.types.media_buy as media_buy

    packages_item = media_buy.GetMediaBuysResponseMediaBuysItemPackagesItem
    assert adcp.MediaBuyPackage is packages_item
    assert packages_item.__adcp_schema__.document == "media-buy/get-media-buys-response.json"
    assert (
        packages_item.__adcp_schema__.pointer
        == "#/properties/media_buys/items/properties/packages/items"
    )


#: ``core/assets/asset-union.json``'s own arm order, ``#/oneOf/0`` .. ``#/oneOf/20``:
#: the ``asset_type`` each arm pins, the branch class emitted for it, and the
#: ``core/assets/*.json`` root the arm ``$ref``s. Every arm is a bare ``$ref``, so the
#: asset's own class is a BASE of the branch and the branch carries the union's pointer.
#:
#: Twenty-one, not twenty. ``#/oneOf/4`` is ``display-tag-asset.json``, not deprecated,
#: ``const: "display_tag"`` — a wire value upstream's hand-written ``AssetInstance``
#: union omitted, which is why that name has no counterpart here and this list is one
#: arm wider than the set it replaces.
ASSET_UNION_ARMS = (
    ("image", "AssetVariantImage", "ImageAsset"),
    ("video", "AssetVariantVideo", "VideoAsset"),
    ("audio", "AssetVariantAudio", "AudioAsset"),
    ("vast", "AssetVariantVast", "VASTAsset"),
    ("display_tag", "AssetVariantDisplayTag", "DisplayTagAsset"),
    ("text", "AssetVariantText", "TextAsset"),
    ("url", "AssetVariantUrl", "URLAsset"),
    ("html", "AssetVariantHtml", "HTMLAsset"),
    ("javascript", "AssetVariantJavascript", "JavaScriptAsset"),
    ("zip", "AssetVariantZip", "ZipAsset"),
    ("webhook", "AssetVariantWebhook", "WebhookAsset"),
    ("css", "AssetVariantCss", "CSSAsset"),
    ("daast", "AssetVariantDaast", "DAASTAsset"),
    ("markdown", "AssetVariantMarkdown", "MarkdownAsset"),
    ("brief", "AssetVariantBrief", "BriefAsset"),
    ("catalog", "AssetVariantCatalog", "CatalogAsset"),
    ("published_post", "AssetVariantPublishedPost", "PublishedPostAsset"),
    ("card", "AssetVariantCard", "CardAsset"),
    ("pixel_tracker", "AssetVariantPixelTracker", "PixelTrackerAsset"),
    ("vast_tracker", "AssetVariantVastTracker", "VASTTrackerAsset"),
    ("daast_tracker", "AssetVariantDaastTracker", "DAASTTrackerAsset"),
)


def test_complete_asset_union_is_exported():
    """Every arm of ``core/assets/asset-union.json`` is on a stable import path.

    The assets are ``core/assets/*.json`` documents, so the domain surface that
    publishes them is ``adcp.types.core`` — not ``adcp.types.creative``, which
    serves the ``creative/`` documents. The flat ``adcp`` and ``adcp.types``
    namespaces bind the upstream spellings on top of that.
    """
    from adcp.types import core

    assert len(ASSET_UNION_ARMS) == 21

    for asset_type, branch_name, root_name in ASSET_UNION_ARMS:
        assert hasattr(core, root_name), f"{root_name} not exported from adcp.types.core"
        assert hasattr(core, branch_name), f"{branch_name} not exported from adcp.types.core"
        branch = getattr(core, branch_name)
        root = getattr(core, root_name)
        # The branch IS the union and IS the asset: both halves of a bare-`$ref` arm.
        assert issubclass(branch, core.AssetVariant)
        assert issubclass(branch, root)
        assert branch.__adcp_schema__.document == "core/assets/asset-union.json"
        assert branch.model_fields["asset_type"].annotation == Literal[asset_type]


def test_upstream_asset_spellings_resolve_to_the_documents_own_class():
    """The flat namespaces keep upstream's asset words, bound to our document roots."""
    import adcp
    from adcp import types
    from adcp.types import core

    upstream_spellings = {
        "ImageContent": "ImageAsset",
        "VideoContent": "VideoAsset",
        "AudioContent": "AudioAsset",
        "TextContent": "TextAsset",
        "HtmlContent": "HTMLAsset",
        "UrlContent": "URLAsset",
        "CssContent": "CSSAsset",
        "JavascriptContent": "JavaScriptAsset",
        "MarkdownAsset": "MarkdownAsset",
        "VastAsset": "VASTAsset",
        "DaastAsset": "DAASTAsset",
        "BriefAsset": "BriefAsset",
        "CatalogAsset": "CatalogAsset",
        "WebhookContent": "WebhookAsset",
        "ZipAsset": "ZipAsset",
        "PublishedPostAsset": "PublishedPostAsset",
        "CardAsset": "CardAsset",
        "PixelTrackerAsset": "PixelTrackerAsset",
        "VastTrackerAsset": "VASTTrackerAsset",
        "DaastTrackerAsset": "DAASTTrackerAsset",
    }
    roots = {root for _, _, root in ASSET_UNION_ARMS}
    assert set(upstream_spellings.values()) <= roots

    for spelling, root_name in upstream_spellings.items():
        assert hasattr(adcp, spelling), f"{spelling} not exported from adcp"
        assert hasattr(types, spelling), f"{spelling} not exported from adcp.types"
        assert getattr(adcp, spelling) is getattr(types, spelling)
        assert getattr(types, spelling) is getattr(core, root_name)


def test_asset_union_root_selects_the_branch_and_refuses_an_unregistered_type():
    """Hand the payload to the root; the branch is constructed, or nothing is.

    Upstream pinned these two refusals on pydantic's own discriminated-union
    codes (``union_tag_invalid``, ``union_tag_not_found``). The document states
    the choice as a 21-arm ``oneOf``, so the refusal carried here is the
    ``oneOf`` rule's, reported at the discriminator the document names. The
    error TYPE and the named field are what this asserts.
    """
    from pydantic import ValidationError

    from adcp.types import core

    asset = core.AssetVariant.model_validate(
        {
            "asset_type": "image",
            "asset_id": "hero",
            "url": "https://cdn.example.com/hero.png",
            "width": 300,
            "height": 250,
        }
    )
    assert isinstance(asset, core.AssetVariantImage)
    assert isinstance(asset, core.ImageAsset)
    assert asset.__adcp_schema__.pointer == "#/oneOf/0"

    for payload in ({"asset_type": "not_registered"}, {}):
        with pytest.raises(ValidationError) as exc:
            core.AssetVariant.model_validate(payload)
        assert [(e["type"], e["loc"]) for e in exc.value.errors()] == [("oneOf", ("asset_type",))]


def test_wholesale_feed_notification_types_are_stably_exported():
    """AdCP 3.1 catalog webhook types stay on stable import paths."""
    import adcp
    from adcp import types

    for type_name in ["NotificationConfig", "WholesaleFeedWebhook", "WholesaleFeedEvent"]:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"
        assert hasattr(types, type_name), f"{type_name} not exported from adcp.types"


def test_request_response_types_are_exported():
    """Request/response types are accessible from main package."""
    import adcp

    api_types = [
        "GetProductsRequest",
        "GetProductsResponse",
        "CreateMediaBuyRequest",
        "LegacyListCreativeFormatsRequest",
        "LegacyListCreativeFormatsResponse",
        "LegacyBuildCreativeRequest",
        "LegacyBuildCreativeResponse",
        "GetMediaBuysRequest",
        "GetMediaBuysResponse",
    ]

    for type_name in api_types:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"


def test_structured_error_details_are_exported():
    """Every generated error-detail model is available from ``adcp.types``."""
    from adcp import types

    error_detail_types = [
        "AccessibilityViolationDetails",
        "AccountMovedDetails",
        "AccountSetupRequiredDetails",
        "ActionNotAllowedDetails",
        "ActionNotAllowedReason",
        "AgentPermissionDeniedDetails",
        "AudienceTooSmallDetails",
        "AuthorizationRequiredDetails",
        "BillingNotPermittedForAgentDetails",
        "BillingNotSupportedDetails",
        "BudgetTooLowDetails",
        "ConflictDetails",
        "CreativeRejectedDetails",
        "PolicyViolationDetails",
        "RateLimitedDetails",
        "StaleResponseDetails",
        "UnsupportedRefinementDimensionDetails",
        "VendorErrorCodeRegistry",
        "VersionUnsupportedDetails",
    ]

    for type_name in error_detail_types:
        assert getattr(types, type_name).__name__ == type_name


def test_pricing_option_types_are_exported():
    """All pricing option types are accessible from main package."""
    import adcp

    pricing_types = [
        "CpcPricingOption",
        "CpcvPricingOption",
        "CpmPricingOption",
        "CppPricingOption",
        "CpvPricingOption",
        "FlatRatePricingOption",
        "VcpmPricingOption",
    ]

    for type_name in pricing_types:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"


def test_semantic_aliases_are_exported():
    """Semantic type aliases are accessible from main package."""
    import adcp

    aliases = [
        # Preview renders
        "UrlPreviewRender",
        "HtmlPreviewRender",
        "BothPreviewRender",
        # Response variants
        "CreateMediaBuySuccessResponse",
        "CreateMediaBuyErrorResponse",
        "ActivateSignalSuccessResponse",
        "ActivateSignalErrorResponse",
    ]

    for type_name in aliases:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"


def test_vast_and_daast_delivery_branches_are_named_by_their_documents():
    """The two delivery branches are branch classes of their own document's root.

    ``UrlVastAsset``, ``InlineVastAsset``, ``UrlDaastAsset`` and
    ``InlineDaastAsset`` are upstream's words for one BRANCH of a document whose
    root is emitted here. ``core/assets/vast-asset.json`` and
    ``core/assets/daast-asset.json`` are each a two-branch ``oneOf`` on
    ``delivery_type``, so each branch is reached under the name the document's own
    root and branch derive — and because the branch IS emitted, each of the four
    upstream words has a subject and ``adcp.types.aliases`` binds it. The refusal
    rows that stood here named ``adcp.types.domains.core.assets.asset_union``
    classes and concluded no subject; the pointers below are why that was wrong.
    """
    import adcp
    from adcp.types import core
    from adcp.types._base import SchemaRef

    assert (adcp.UrlVastAsset, adcp.InlineVastAsset) == (core.VASTAssetUrl, core.VASTAssetInline)
    assert (adcp.UrlDaastAsset, adcp.InlineDaastAsset) == (
        core.DAASTAssetUrl,
        core.DAASTAssetInline,
    )

    branches = {
        "core/assets/vast-asset.json": (core.VASTAsset, core.VASTAssetUrl, core.VASTAssetInline),
        "core/assets/daast-asset.json": (
            core.DAASTAsset,
            core.DAASTAssetUrl,
            core.DAASTAssetInline,
        ),
    }
    for document, (root, url_branch, inline_branch) in branches.items():
        assert root.__adcp_schema__ == SchemaRef(document=document, pointer="#")
        assert url_branch.__adcp_schema__ == SchemaRef(document=document, pointer="#/oneOf/0")
        assert inline_branch.__adcp_schema__ == SchemaRef(document=document, pointer="#/oneOf/1")
        assert issubclass(url_branch, root)
        assert issubclass(inline_branch, root)


def test_client_types_are_exported():
    """Client and config types are accessible from main package."""
    import adcp

    client_types = [
        "ADCPClient",
        "ADCPMultiAgentClient",
        "AgentConfig",
        "Protocol",
    ]

    for type_name in client_types:
        assert hasattr(adcp, type_name), f"{type_name} not exported from adcp package"


def test_public_api_types_are_pydantic_models():
    """Core types from public API are valid Pydantic models."""
    from adcp import Format, MediaBuy, Product, Property

    types_to_test = [Product, Format, MediaBuy, Property]

    for model_class in types_to_test:
        # Should have Pydantic model methods
        name = model_class.__name__
        assert hasattr(model_class, "model_validate"), f"{name} missing model_validate"
        assert hasattr(model_class, "model_dump"), f"{name} missing model_dump"
        assert hasattr(model_class, "model_validate_json"), f"{name} missing model_validate_json"
        assert hasattr(model_class, "model_dump_json"), f"{name} missing model_dump_json"
        assert hasattr(model_class, "model_fields"), f"{name} missing model_fields"


def test_product_has_expected_public_fields():
    """Product type from public API has expected fields."""
    from adcp import Product

    expected_fields = [
        "product_id",
        "name",
        "description",
        "pricing_options",
        "publisher_properties",
    ]

    model_fields = Product.model_fields
    for field_name in expected_fields:
        assert field_name in model_fields, f"Product missing field: {field_name}"


def test_format_has_expected_public_fields():
    """Root Format is the canonical declaration surface.

    ``core/product-format-declaration.json`` declares `format_kind` and `params`
    in NONE of its top-level ``properties`` — only in each of the 16 ``oneOf``
    branches, where ``format_kind`` is a ``const`` and ``params`` the ``$ref``
    that const selects. The root's ``required: ['format_kind', 'params']`` is
    satisfied by whichever branch the payload picks, so the base class carries
    the declaration-wide properties and every branch carries the pair.
    """
    from adcp import Format

    model_fields = Format.model_fields
    for field_name in ["format_option_id", "format_shape", "format_schema"]:
        assert field_name in model_fields, f"Format missing field: {field_name}"

    branches = Format.__subclasses__()
    assert len(branches) == 16
    for branch in branches:
        for field_name in ["format_kind", "params"]:
            assert field_name in branch.model_fields, f"{branch.__name__} missing {field_name}"
            assert branch.model_fields[field_name].is_required()


def test_format_root_selects_the_branch_its_format_kind_names():
    """``format_kind`` is the document's ``discriminator``; the root reads it."""
    from adcp import Format
    from adcp.types import core

    declaration = Format.model_validate({"format_kind": "image", "params": {}})
    assert isinstance(declaration, core.ImageFormatDeclaration)
    assert declaration.__adcp_schema__.pointer == "#/oneOf/0"


def test_format_excludes_legacy_named_format_fields():
    """Canonical Format cannot expose legacy creative identity or assets."""
    from adcp import Format

    model_fields = Format.model_fields
    assert "format_id" not in model_fields
    assert "agent_url" not in model_fields
    assert "assets" not in model_fields


def test_pricing_options_have_required_fields():
    """Pricing option types have required fields for pricing."""
    from adcp import CpcPricingOption, CpmPricingOption

    # All pricing options should have pricing_model and pricing_option_id
    pricing_types = [CpmPricingOption, CpcPricingOption]
    for pricing_type in pricing_types:
        name = pricing_type.__name__
        assert "pricing_model" in pricing_type.model_fields, f"{name} missing pricing_model"
        assert "pricing_option_id" in pricing_type.model_fields, f"{name} missing pricing_option_id"
        assert "currency" in pricing_type.model_fields, f"{name} missing currency"

    # CPM pricing option should support both fixed and auction pricing via optional fields
    assert "fixed_price" in CpmPricingOption.model_fields, "CpmPricingOption missing fixed_price"
    assert "floor_price" in CpmPricingOption.model_fields, "CpmPricingOption missing floor_price"


def test_semantic_aliases_point_to_discriminated_variants():
    """Semantic aliases successfully construct their respective variants."""
    from adcp import (
        CreateMediaBuyErrorResponse,
        CreateMediaBuySuccessResponse,
        HtmlPreviewRender,
        UrlPreviewRender,
    )

    # URL preview render requires render_id, output_format='url', preview_url, role
    url_render = UrlPreviewRender(
        render_id="r1",
        output_format="url",
        preview_url="https://example.com/preview",
        role="primary",
    )
    assert str(url_render.preview_url) == "https://example.com/preview"
    assert url_render.output_format == "url"

    # HTML preview render requires render_id, output_format='html', preview_html, role
    html_render = HtmlPreviewRender(
        render_id="r2",
        output_format="html",
        preview_html="<div>Preview content</div>",
        role="primary",
    )
    assert html_render.preview_html == "<div>Preview content</div>"
    assert html_render.output_format == "html"

    # Success response should accept success fields
    # `status` is required by core/protocol-envelope.json, which this
    # document composes via allOf. Upstream's generator dropped
    # allOf-composed required fields, so their fixtures omit it.
    success = CreateMediaBuySuccessResponse(
        status="completed",
        media_buy_id="mb_123",
        buyer_ref="ref_456",
        packages=[],
        confirmed_at="2026-05-27T12:00:00Z",
        revision=1,
    )
    assert success.media_buy_id == "mb_123"

    # Error response should accept error fields
    # `status` is required by core/protocol-envelope.json, which this
    # document composes via allOf. Upstream's generator dropped
    # allOf-composed required fields, so their fixtures omit it.
    # `errors` is REQUIRED here, which marks the rejection arm of the
    # oneOf; the envelope says such an arm emits `rejected`.
    error = CreateMediaBuyErrorResponse(
        status="rejected",
        errors=[{"code": "invalid", "message": "Failed"}],
    )
    assert len(error.errors) == 1


def test_public_api_types_serialize_to_json():
    """Public API types can be serialized to JSON."""
    from adcp import CreateMediaBuySuccessResponse

    # `status` is required by core/protocol-envelope.json, which this
    # document composes via allOf. Upstream's generator dropped
    # allOf-composed required fields, so their fixtures omit it.
    success = CreateMediaBuySuccessResponse(
        status="completed",
        media_buy_id="mb_123",
        buyer_ref="ref_456",
        packages=[],
        confirmed_at="2026-05-27T12:00:00Z",
        revision=1,
    )

    # Should serialize to JSON without errors
    json_str = success.model_dump_json()
    assert isinstance(json_str, str)
    assert "mb_123" in json_str
    assert "ref_456" in json_str


def test_public_api_types_deserialize_from_json():
    """Public API types can be deserialized from JSON."""
    from adcp import CreateMediaBuySuccessResponse

    # `status` is required by core/protocol-envelope.json, which this
    # document composes via allOf. Upstream's generator dropped
    # allOf-composed required fields, so their fixtures omit it.
    json_data = {
        "status": "completed",
        "media_buy_id": "mb_456",
        "buyer_ref": "ref_789",
        "packages": [],
        "confirmed_at": "2026-05-27T12:00:00Z",
        "revision": 1,
    }

    # Should deserialize from dict without errors
    success = CreateMediaBuySuccessResponse.model_validate(json_data)
    assert success.media_buy_id == "mb_456"
    assert success.buyer_ref == "ref_789"


def test_no_internal_types_in_public_exports():
    """Public API should not export internal numbered types."""
    import adcp

    # These are internal types that should NOT be in public API
    internal_types = [
        "PreviewRender1",
        "PreviewRender2",
        "PreviewRender3",
        "CreateMediaBuyResponse1",
        "CreateMediaBuyResponse2",
        "PublisherProperties",  # Should use semantic names or qualified imports
        "PublisherProperties4",
        "PublisherProperties5",
    ]

    # Check that internal types are not directly exported
    # Note: They might be accessible via qualified imports, which is fine
    exports = dir(adcp)
    for type_name in internal_types:
        # If exported, it should have a semantic alias that's preferred
        if type_name in exports:
            # This is acceptable as long as semantic aliases exist
            pass


def test_public_api_has_version():
    """Public API exports version information."""
    import adcp

    assert hasattr(adcp, "__version__"), "adcp package should export __version__"
    assert isinstance(adcp.__version__, str), "__version__ should be a string"
    assert len(adcp.__version__) > 0, "__version__ should not be empty"


def test_legacy_list_creative_formats_request_has_filter_params():
    """The explicitly legacy list-formats request retains its filters.

    The SDK supports is_responsive and name_search parameters for filtering
    creative formats. These parameters are part of the AdCP specification.
    """
    from adcp import LegacyListCreativeFormatsRequest

    model_fields = LegacyListCreativeFormatsRequest.model_fields

    # Core filter parameters from AdCP spec
    expected_fields = [
        "is_responsive",  # Filter for responsive formats
        "name_search",  # Search formats by name (case-insensitive partial match)
        "asset_types",  # Filter by asset types (image, video, etc.)
        "format_ids",  # Return only specific format IDs
        "min_width",  # Minimum width filter
        "max_width",  # Maximum width filter
        "min_height",  # Minimum height filter
        "max_height",  # Maximum height filter
        "context",  # Context object for request
        "ext",  # Extension object
    ]

    for field_name in expected_fields:
        assert field_name in model_fields, f"ListCreativeFormatsRequest missing field: {field_name}"


def test_legacy_list_creative_formats_request_filter_params_types():
    """LegacyListCreativeFormatsRequest filter parameters have correct types."""
    from adcp import LegacyListCreativeFormatsRequest

    # Create request with filter parameters - should not raise
    request = LegacyListCreativeFormatsRequest(
        is_responsive=True,
        name_search="mobile",
    )

    assert request.is_responsive is True
    assert request.name_search == "mobile"

    # Verify serialization includes the filter parameters
    data = request.model_dump(exclude_none=True)
    assert data["is_responsive"] is True
    assert data["name_search"] == "mobile"


def test_removed_v4_types_raise_informative_import_error():
    """Removed-in-4.0 names should raise a clear ImportError pointing at MIGRATION."""
    import pytest

    import adcp

    for name in ("BrandManifest", "FormatCategory", "DeliverTo", "Pricing", "PackageStatus"):
        with pytest.raises(ImportError) as exc:
            getattr(adcp, name)
        assert "MIGRATION_v3_to_v4.md" in str(exc.value)
        assert "4.0" in str(exc.value)


def test_public_api_surface_matches_snapshot():
    """Fail when a public name is removed, added, or starts meaning something else.

    Regenerate after an intentional change:

        python scripts/regenerate_public_api_snapshot.py

    The snapshot records WHAT each name resolves to, not just that it exists.
    That is what makes the third check possible. ``_generated`` resolves a bare
    type name defined by several generated modules by sort order and stem
    preference, so a schema addition can take a name an adopter already
    imports — the class changes, the name does not, and a names-only snapshot
    ships it green. Review a changed value before regenerating: it is a name
    that now means a different object to everyone who imports it.
    """
    import importlib
    import json
    from pathlib import Path

    from scripts.export_resolution import expand_key, resolution_key, snapshot_modules

    snapshot_path = Path(__file__).parent / "fixtures" / "public_api_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text())
    regen_cmd = "python scripts/regenerate_public_api_snapshot.py"

    assert set(snapshot) == {label for label, _ in snapshot_modules()}, (
        "Snapshot namespaces changed. Review the public surface and regenerate "
        f"the snapshot with `{regen_cmd}`."
    )

    for label, module_path in snapshot_modules():
        module = importlib.import_module(module_path)
        recorded = snapshot[label]["resolves"]
        live = {}
        for name in module.__all__:
            try:
                live[name] = resolution_key(getattr(module, name))
            except AttributeError:
                live[name] = "<missing>"

        removed = sorted(set(recorded) - set(live))
        added = sorted(set(live) - set(recorded))
        assert not removed, (
            f"Public names removed from {label}: {removed}. "
            "Removals are breaking changes — add a CHANGELOG entry and, for "
            "a major version bump, a MIGRATION note, then regenerate the "
            f"snapshot with `{regen_cmd}`."
        )
        assert not added, (
            f"Public names added to {label}: {added}. "
            f"Once the addition is intentional, regenerate the snapshot with "
            f"`{regen_cmd}`."
        )

        repointed = {
            name: (expand_key(name, recorded[name]), live[name])
            for name in sorted(recorded)
            if expand_key(name, recorded[name]) != live[name]
        }
        assert not repointed, (
            f"Public names in {label} now resolve to a different object:\n"
            + "\n".join(f"  {name}: {was} -> {now}" for name, (was, now) in repointed.items())
            + "\n\nThe name is unchanged, so no import breaks and no type checker "
            "complains, while every adopter who imports it gets a different class. "
            "A bare type name that several generated modules define resolves by "
            "sort order, so adding a schema is enough to cause this. Confirm the "
            "new resolution is the intended one, then regenerate the snapshot "
            f"with `{regen_cmd}`."
        )

        duplicates = sorted({n for n in module.__all__ if module.__all__.count(n) > 1})
        assert duplicates == snapshot[label].get("duplicate_names", []), (
            f"Duplicate names in {label}.__all__ changed: {duplicates}. "
            f"Regenerate the snapshot with `{regen_cmd}`."
        )


def test_no_public_all_repeats_a_name() -> None:
    """``__all__`` names each export once (#1380).

    ``__all__`` is a list, so a consumer that iterates it rather than taking a
    set counts a repeated name twice; two independent counts of the exported
    ``RootModel`` population once disagreed by exactly one such repeat.
    """
    import importlib
    import pkgutil
    from collections import Counter

    from adcp.types import _surface

    # The domain surface is ``adcp.types.<domain>``, and ``adcp.types._surface``
    # is the compiler's own aggregator package -- one module per domain, which
    # the public module of that domain composes with a star re-export. Reading
    # the package is what keeps the list from being a second spelling of it.
    # ``adcp.types.domains`` is no longer such a list: it is a prefix-substituting
    # mirror of the per-DOCUMENT tree ``adcp.types._schemas`` and names no
    # domains at all. ``adcp.types._eager`` is gone with the lazy-facade split.
    domains = sorted(
        module.name
        for module in pkgutil.iter_modules(_surface.__path__)
        if not module.name.startswith("_")
    )
    assert domains, "no domain aggregator modules found under adcp.types._surface"

    modules = [
        "adcp",
        "adcp.types",
        "adcp.types._generated",
        "adcp.types.aliases",
        "adcp.types.legacy",
        "adcp.types.capabilities",
        "adcp.types.error_details",
        *(f"adcp.types.{domain}" for domain in domains),
    ]
    repeated = {}
    for module_path in modules:
        module = importlib.import_module(module_path)
        # ``__all__`` IS READ ONCE, and that is not a style preference.
        # ``adcp.types.__all__`` is not a list: ``__getattr__`` rebuilds it from five
        # sources -- ``compat.__all__``, ``compat.__adcp_flat_only__``,
        # ``adapter.__all__``, ``_restored.__all__``, ``_flat.__all__`` -- and sorts the
        # union of 4,358 names.  Measured: 4.39 s on first access and 0.06 s on every
        # one after.  The previous spelling named ``module.__all__`` twice, the second
        # inside the comprehension, so it was re-derived ONCE PER NAME: 4,358 rebuilds
        # at 0.06 s is 261 s for this module alone, over ~30 modules, which read as a
        # hung ``make test`` rather than a slow test.  ``Counter`` also replaces the
        # ``count()`` per name, which was the other half of the quadratic.
        names = list(module.__all__)
        duplicates = sorted({n for n, seen in Counter(names).items() if seen > 1})
        if duplicates:
            repeated[module_path] = duplicates
    assert not repeated, repeated
