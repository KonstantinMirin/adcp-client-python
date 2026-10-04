"""Public canonical model identity and closed format-kind types (#1141/#1241)."""

from collections.abc import Sequence
from typing import Any

from typing_extensions import assert_type

from adcp.types import (
    CanonicalFormatKind,
    Creative,
    CreativeAsset,
    CreativeManifest,
    DeliveryCreative,
    GetCreativeDeliveryResponse,
)
from adcp.types.canonical_creative import CanonicalBoundaryModel, _DeliveryCreativeVariant


def accepts_canonical_class(model: type[CanonicalBoundaryModel]) -> None:
    pass


accepts_canonical_class(CreativeAsset)

asset = CreativeAsset.model_validate(
    {
        "creative_id": "creative-1",
        "name": "Creative",
        "format_kind": "image",
        "assets": {},
    }
)
assert_type(asset.format_kind, CanonicalFormatKind)


def listed_kind(creative: Creative) -> CanonicalFormatKind:
    assert_type(creative.format_kind, CanonicalFormatKind)
    return creative.format_kind


manifest = CreativeManifest(assets={})
assert_type(manifest.format_kind, CanonicalFormatKind | None)

delivery = DeliveryCreative(
    creative_id="creative-1",
    format_kind="future_canonical_format",
    variants=[],
)
assert_type(delivery.format_kind, CanonicalFormatKind | str | None)


def check_served_manifest(response: GetCreativeDeliveryResponse) -> None:
    for creative in response.creatives:
        # ``variants`` narrows the generated ``list[CreativeVariant]`` to the
        # tolerant delivery row, which pydantic accepts and mypy's invariant
        # list rule does not — so the field is declared ``SchemaVariant`` and
        # reads as ``Any``. Name the element type to keep the assertion below
        # grading something: the row is module-private because it is a readback
        # shape no adopter constructs, which is why the type is spelled here
        # rather than imported from ``adcp.types``.
        variants: Sequence[_DeliveryCreativeVariant] = creative.variants
        for variant in variants:
            if variant.manifest is not None:
                # The tolerant manifest widens the generated
                # ``CanonicalFormatKind | None`` to admit an unknown future
                # kind. A widening override is not expressible either, so this
                # field is ``SchemaVariant`` too and reads as ``Any``. The
                # runtime union is graded by
                # ``test_creative_asset_regression.py``; the deleted stub was
                # the only place the static union was ever stated.
                assert_type(variant.manifest.format_kind, Any)
