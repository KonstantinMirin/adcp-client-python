"""Forward-compatibility and generated-model composition patches.

Patches Format.assets and RepeatableAssetGroup.assets at import
time so responses containing novel asset_type values (e.g., 'pixel_tracker')
parse as UnknownFormatAsset / UnknownGroupAsset instead of raising a cascade
of ValidationErrors that zero out the entire list_creative_formats response.

This module is intentionally NOT auto-generated. It lives outside
the generated tree and is preserved across codegen runs (generate_types.py only
wipes src/adcp/types/domains/).

Import order: comes after _ergonomic in types/__init__.py (alphabetical by
underscore-preserved sort). Importing this module directly triggers import of
adcp.types.aliases as a side effect (via ``from adcp.types.aliases import …``)
so there is no circular-import risk and no strict ordering requirement against
aliases in __init__.py.

Import layering: this module imports directly from the generated tree (like
aliases.py and _ergonomic.py) because it must patch the generated classes
in-place. It is therefore listed in ALLOWED_FILES in test_import_layering.py.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import copy, deepcopy
from types import GenericAlias
from typing import Annotated, Any, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    model_validator,
)
from pydantic.fields import FieldInfo

from adcp.types._split_root import shared_base
from adcp.types.aliases import FormatAssetUnion, GroupFormatAssetUnion, RepeatableAssetGroup
from adcp.types.base import AdCPBaseModel
from adcp.types.canonical_creative import CreateMediaBuyRequest as _PublicCreateMediaBuyRequest
from adcp.types.canonical_creative import UpdateMediaBuyRequest as _PublicUpdateMediaBuyRequest
from adcp.types.domains.core.creative_manifest import CreativeManifest
from adcp.types.domains.core.creative_variant import CreativeVariant
from adcp.types.domains.core.format import Format
from adcp.types.domains.core.mcp_webhook_payload import McpWebhookPayload
from adcp.types.domains.core.reporting_webhook import (
    ReportingWebhook as _GeneratedReportingWebhook,
)
from adcp.types.domains.core.version_envelope import AdcpVersionEnvelope
from adcp.types.domains.creative.get_creative_delivery_response import (
    Creative as DeliveryCreative,
)
from adcp.types.domains.creative.get_creative_delivery_response import (
    GetCreativeDeliveryResponse,
)
from adcp.types.domains.creative.preview_creative_response import PreviewCreativeResponse3
from adcp.types.domains.media_buy.accept_proposal_request import (
    AcceptProposalRequest as _GeneratedAcceptProposalRequest,
)
from adcp.types.domains.media_buy.build_creative_response import (
    BuildCreativeResponse1,
    BuildCreativeResponse3,
    BuildCreativeResponse4,
)
from adcp.types.domains.media_buy.build_creative_response import (
    Creative as BuildCreative,
)
from adcp.types.domains.media_buy.build_creative_response import (
    Variant as BuildCreativeVariant,
)
from adcp.types.domains.media_buy.buy_products_request import (
    BuyProductsRequest as _GeneratedBuyProductsRequest,
)
from adcp.types.domains.media_buy.control_media_buy_request import (
    ControlMediaBuyRequest as _GeneratedControlMediaBuyRequest,
)
from adcp.types.domains.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisher,
)
from adcp.types.domains.trusted_match.offer import Offer
from adcp.types.domains.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouter,
)

# The generated classes carry ``operation_id`` -- ``PIN_GAP_FIELDS`` in
# scripts/generate_types.py declares it on core/reporting-webhook.json and the
# generator emits it, so all five nesting request schemas get it by generation.
# A TYPE_CHECKING shadow used to restate the field on each of those five plus
# one per split-root branch; a generated field needs no static view.
ReportingWebhook = _GeneratedReportingWebhook
AcceptProposalRequest = _GeneratedAcceptProposalRequest
BuyProductsRequest = _GeneratedBuyProductsRequest
ControlMediaBuyRequest = _GeneratedControlMediaBuyRequest
CreateMediaBuyRequest = _PublicCreateMediaBuyRequest
UpdateMediaBuyRequest = _PublicUpdateMediaBuyRequest


class _ManifestReadbackModel(AdCPBaseModel):
    """Independent from strict inputs: tolerant instances must not validate as them."""

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _normalize_readback(cls, data: Any) -> Any:
        if isinstance(data, AdCPBaseModel) and not isinstance(data, cls):
            return data.model_dump(mode="python")
        return data


class _VersionedManifestReadbackModel(AdcpVersionEnvelope, _ManifestReadbackModel):
    """Keep the shared version envelope on build response nodes."""


def _manifest_readback_clone(
    name: str,
    source: type[AdCPBaseModel],
    overrides: dict[str, Any],
    *,
    validators: dict[str, Any] | None = None,
) -> type[AdCPBaseModel]:
    # Copy all field constraints without inheriting the strict source model.
    # A tolerant subclass would pass its parent's default instance validation.
    fields: dict[str, Any] = {
        key: (overrides.get(key, field.annotation), deepcopy(field))
        for key, field in source.model_fields.items()
    }
    return create_model(
        name,
        __base__=(
            _VersionedManifestReadbackModel
            if issubclass(source, AdcpVersionEnvelope)
            else _ManifestReadbackModel
        ),
        __module__=__name__,
        __validators__=validators,
        **fields,
    )


def _normalize_readback_manifest(data: Any) -> Any:
    # Pydantic binds the generated validator proxy to a callable at runtime.
    # The validator is declared on the shared base: the branches differ in which
    # fields they require and forbid, not in how a manifest's assets normalize.
    normalize = cast(Callable[[Any], Any], shared_base(CreativeManifest)._coerce_standalone_assets)
    return normalize(data)


_ReadbackCreativeManifest = _manifest_readback_clone(
    "_ReadbackCreativeManifest",
    # The tolerant readback model is not one branch's shape -- it accepts a manifest
    # instance of either -- so it clones the base they share.
    shared_base(CreativeManifest),
    # No field override: ``format_kind`` is generated as ``str`` (see
    # OPEN_VOCABULARY_SCHEMAS in scripts/generate_types.py), so there is nothing
    # left to widen. What this clone still carries is instance normalization —
    # a readback node accepts a manifest INSTANCE of a sibling class, which a
    # plain pydantic model field does not.
    {},
    validators={
        # Preserve the generated manifest's standalone-asset normalization,
        # without inheriting from the input model.
        "_coerce_standalone_assets": model_validator(mode="before")(_normalize_readback_manifest),
    },
)
_DeliveryVariant = _manifest_readback_clone(
    "_DeliveryVariant",
    CreativeVariant,
    {"manifest": _ReadbackCreativeManifest | None},
)
_BuildReadbackVariant = _manifest_readback_clone(
    "_BuildReadbackVariant",
    BuildCreativeVariant,
    {"creative_manifest": _ReadbackCreativeManifest},
)
_BuildReadbackCreative = _manifest_readback_clone(
    "_BuildReadbackCreative",
    BuildCreative,
    {
        # This constraint is inside the optional union in the generated type,
        # so it must stay on the non-None branch when replacing that annotation.
        "variants": Annotated[GenericAlias(list, _BuildReadbackVariant), Field(min_length=1)]
        | None,
    },
)
_ReadbackOffer = _manifest_readback_clone(
    "_ReadbackOffer",
    Offer,
    {"creative_manifest": _ReadbackCreativeManifest | None},
)


def _patch_model_field(model: type[BaseModel], field_name: str, new_annotation: Any) -> None:
    """Replace a Pydantic model field's annotation in-place.

    Sets both model_fields (the FieldInfo dict Pydantic uses for schema
    generation) and __annotations__ (for introspection), then forces a
    schema rebuild. Preserves all constraints and metadata from the original field.
    """
    old_fi = model.model_fields.get(field_name)
    if old_fi is None:
        model.model_fields[field_name] = FieldInfo(annotation=new_annotation)
    else:
        # Keep every generated constraint and piece of field metadata. Rebuilding
        # a FieldInfo from only its default and description silently drops items
        # such as min_length, which matters for composability patches on lists.
        new_fi = copy(old_fi)
        new_fi.annotation = new_annotation
        model.model_fields[field_name] = new_fi
    model.__annotations__[field_name] = new_annotation


def _apply_forward_compat() -> None:
    """Apply open-union, capability, and public-model compatibility patches."""
    # Response manifests retain unknown future kinds because the field is
    # ``str`` everywhere. These patches thread the readback NODES through the
    # generated response classes, which is what lets a response accept a
    # manifest instance of a sibling class. Nothing here is about strictness:
    # no model refuses a format kind in either direction, and checking the
    # vocabulary is the caller's through ``adcp.types.is_canonical_format_kind``
    # (see adcp.types.canonical_creative).
    # ``format_kind`` needs no patch: it is generated as ``str``, so a response
    # retains an unknown kind without one.
    _patch_model_field(DeliveryCreative, "variants", GenericAlias(list, _DeliveryVariant))
    DeliveryCreative.model_rebuild(force=True)
    GetCreativeDeliveryResponse.model_rebuild(force=True)

    _patch_model_field(PreviewCreativeResponse3, "manifest", _ReadbackCreativeManifest | None)
    PreviewCreativeResponse3.model_rebuild(force=True)
    _patch_model_field(BuildCreativeResponse1, "creative_manifest", _ReadbackCreativeManifest)
    BuildCreativeResponse1.model_rebuild(force=True)
    _patch_model_field(
        BuildCreativeResponse3, "creative_manifests", GenericAlias(list, _ReadbackCreativeManifest)
    )
    BuildCreativeResponse3.model_rebuild(force=True)
    _patch_model_field(
        BuildCreativeResponse4, "creatives", GenericAlias(list, _BuildReadbackCreative)
    )
    BuildCreativeResponse4.model_rebuild(force=True)

    for response in (ContextMatchResponseRouterPublisher, ContextMatchResponseProviderRouter):
        _patch_model_field(response, "offers", GenericAlias(list, _ReadbackOffer))
        response.model_rebuild(force=True)

    # This eager wrapper captured build/preview validators before the patches.
    # Rebuilding it re-resolves AdcpAsyncResponseData, a union type alias, so
    # completed task callbacks retain typed manifests.
    McpWebhookPayload.model_rebuild(force=True)

    _patch_model_field(Format, "assets", list[FormatAssetUnion] | None)
    Format.model_rebuild(force=True)

    _patch_model_field(RepeatableAssetGroup, "assets", list[GroupFormatAssetUnion])
    cast(type[BaseModel], RepeatableAssetGroup).model_rebuild(force=True)


_apply_forward_compat()
