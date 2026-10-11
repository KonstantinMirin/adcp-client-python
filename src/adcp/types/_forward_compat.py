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
in-place. That needs no exemption -- ``adcp.types.domains.<domain>.<schema>`` is
a public address and only the flat ``adcp.types._generated`` namespace is
forbidden, which is why ALLOWED_FILES in test_import_layering.py does not name
this module.
"""

from __future__ import annotations

from copy import copy
from typing import Any, cast

from pydantic import (
    BaseModel,
)
from pydantic.fields import FieldInfo

from adcp.types.aliases import FormatAssetUnion, GroupFormatAssetUnion, RepeatableAssetGroup
from adcp.types.canonical_creative import CreateMediaBuyRequest as _PublicCreateMediaBuyRequest
from adcp.types.canonical_creative import UpdateMediaBuyRequest as _PublicUpdateMediaBuyRequest
from adcp.types.domains.core.format import Format
from adcp.types.domains.core.reporting_webhook import (
    ReportingWebhook as _GeneratedReportingWebhook,
)
from adcp.types.domains.media_buy.accept_proposal_request import (
    AcceptProposalRequest as _GeneratedAcceptProposalRequest,
)
from adcp.types.domains.media_buy.buy_products_request import (
    BuyProductsRequest as _GeneratedBuyProductsRequest,
)
from adcp.types.domains.media_buy.control_media_buy_request import (
    ControlMediaBuyRequest as _GeneratedControlMediaBuyRequest,
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
    _patch_model_field(Format, "assets", list[FormatAssetUnion] | None)
    Format.model_rebuild(force=True)

    _patch_model_field(RepeatableAssetGroup, "assets", list[GroupFormatAssetUnion])
    cast(type[BaseModel], RepeatableAssetGroup).model_rebuild(force=True)


_apply_forward_compat()
