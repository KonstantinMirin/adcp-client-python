"""Strict adopter fields and cached union validation use supported public imports."""

from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel
from typing_extensions import assert_type

from adcp.types import (
    CanonicalFormatKindStr,
    Format,
    VendorPricingOption,
    VendorPricingOptionUnion,
    require_canonical_format_kind,
    validate_union,
)


class StrictFormat(Format):
    format_kind: CanonicalFormatKindStr


class StrictKinds(BaseModel):
    format_kind: CanonicalFormatKindStr | None = None
    format_kinds: list[CanonicalFormatKindStr]


SupportedKind = Annotated[
    str, AfterValidator(require_canonical_format_kind(["image", "future_kind"]))
]


class SellerKinds(BaseModel):
    format_kind: SupportedKind


strict = StrictFormat(format_kind="image", params={})
assert_type(strict.format_kind, str)
kinds = StrictKinds(format_kinds=["image"])
assert_type(kinds.format_kind, str | None)
assert_type(kinds.format_kinds, list[str])
assert_type(validate_union(StrictFormat, {"format_kind": "image", "params": {}}), StrictFormat)

price = validate_union(
    VendorPricingOption,
    {"pricing_option_id": "price-1", "model": "cpm", "cpm": 2.0, "currency": "USD"},
)
same_price = validate_union(VendorPricingOptionUnion, price)
assert_type(same_price, Any)
