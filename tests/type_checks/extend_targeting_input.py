"""The exact public mutation variant supports adopter subclasses and all facades."""

from typing import cast

from pydantic import Field
from typing_extensions import assert_type

from adcp import TargetingOverlayInput as RootInput
from adcp.types import PackageRequest, PackageUpdate, TargetingOverlay, TargetingOverlayInput
from adcp.types.buyer import TargetingOverlayInput as BuyerInput
from adcp.types.media_buy import TargetingOverlayInput as MediaBuyInput

root_type: type[TargetingOverlayInput] = RootInput
buyer_type: type[TargetingOverlayInput] = BuyerInput
media_buy_type: type[TargetingOverlayInput] = MediaBuyInput


class InternalTargetingInput(TargetingOverlayInput):
    workflow_id: str = Field(exclude=True)


overlay = InternalTargetingInput(geo_countries=None, workflow_id="wf-1181")
created = PackageRequest.model_validate(
    {"product_id": "product-1", "pricing_option_id": "price-1", "targeting_overlay": overlay}
)
updated = PackageUpdate.model_validate({"package_id": "package-1", "targeting_overlay": overlay})

# The STATIC type is the generated declaration, ``TargetingOverlayInput | None``.
# The readback union is wider at runtime: ``_forward_compat`` widens the field
# to admit beta.14 ``TargetingOverlay`` objects, carrying the ``SkipJsonSchema``
# arm, the left-to-right union mode and a per-model core schema with it — a
# runtime mutation no source annotation expresses, so no type checker sees it.
# These assertions previously read the wider union out of
# ``canonical_creative.pyi``, which hand-transcribed the patch result; the stub
# is deleted -- it declared 35 classes while leaving 759 of their runtime fields
# undeclared across 33 of them, 40 of those required, and declared one field the
# runtime does not have -- so the static claim is now the generated one, and the
# wider runtime union is graded by the identity assertions below and by
# tests/test_targeting_overlay_compat.py.
assert_type(created.targeting_overlay, TargetingOverlayInput | None)
assert_type(updated.targeting_overlay, TargetingOverlayInput | None)
assert_type(overlay.workflow_id, str)
assert created.targeting_overlay is overlay
assert updated.targeting_overlay is overlay


class LegacyTargeting(TargetingOverlay):
    workflow_id: str = Field(exclude=True)


legacy = LegacyTargeting(workflow_id="beta14-1181")
legacy_update = PackageUpdate.model_validate(
    {"package_id": "package-1", "targeting_overlay": legacy}
)
assert_type(legacy_update.targeting_overlay, TargetingOverlayInput | None)
# The beta.14 arm is the half the static annotation does not carry, so the
# identity check has to say so explicitly rather than read as non-overlapping.
assert cast(object, legacy_update.targeting_overlay) is legacy
