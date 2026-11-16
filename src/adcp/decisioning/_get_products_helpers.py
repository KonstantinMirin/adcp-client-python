"""Fields-projection helper for ``MediaBuyHandler.get_products``.

When a buyer supplies ``GetProductsRequest.fields`` (a 30-value enum,
``min_length=1``), the framework drops unrequested product fields before
returning the response.  This module owns that post-processing.

Three categories of ``Product`` fields are **always** passed through
regardless of the buyer's selection:

1. **Required-by-schema fields** — ``Product.model_fields`` entries where
   ``field_info.is_required()`` is True.  These seven fields cannot be
   ``None`` and the model cannot be constructed without them:
   ``product_id``, ``name``, ``description``, ``publisher_properties``,
   ``delivery_type``, ``pricing_options``, ``reporting_capabilities``.

2. **Non-enum declared fields** — optional ``Product.model_fields`` entries
   that have no corresponding ``GetProductsField`` enum value
   (``allowed_actions``, ``cancellation_policy``, ``ext``,
   ``material_submission``, ``measurement_readiness``, ``measurement_terms``,
   ``performance_standards``, ``property_targeting_allowed``,
   ``vendor_metric_optimization``).  The enum does not name them so a buyer
   has no mechanism to opt in or out; the framework leaves them unchanged.

3. **Extension fields** — keys present in ``Product.__pydantic_extra__``
   (the model carries ``extra='allow'``).  These are seller-defined
   extension fields not named by the spec; the framework passes them through
   unconditionally.

When ``params.fields`` is ``None`` or empty the handler guard
(``if params.fields:``) prevents this function from being called at all;
no copy is made.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from adcp.types import GetProductsField, GetProductsResponse, Product
from adcp.types.domains.media_buy.get_products_request import Fields as _RequestOnlyField
from adcp.types.domains.media_buy.product_fields import ProductResponseField

logger = logging.getLogger(__name__)

#: What ``GetProductsRequest.fields`` actually declares: a union of two
#: generated enums (38 + 17 members). The public ``GetProductsField`` alias
#: resolves to a third, 53-member enum that the request never holds — one of
#: the names #1360 measured as typed a variant off its referent. Accept every
#: spelling: the projection reads only ``.value``, which all three carry.
_FieldSelection = GetProductsField | ProductResponseField | _RequestOnlyField

# ---------------------------------------------------------------------------
# Module-level constants derived from the live model so they stay in sync
# with schema regenerations.
# ---------------------------------------------------------------------------

#: All schema-required Product fields.  The projection must keep these
#: regardless of what the buyer requested — they cannot be None and the
#: model cannot be constructed without them.
def _names_a_rule_needs(model: type) -> frozenset[str]:
    """Every field name the model's own rules mention.

    **PER-FIELD REQUIREDNESS IS NOT ALL THE REQUIREDNESS THERE IS**, and projecting on it
    alone produced a Product the document refuses.  `core/product.json` states an `anyOf`
    over `required: ['format_ids']` and `required: ['format_options']` -- "Products MUST
    carry `format_ids`, `format_options`, or both during the 3.x migration window" -- which
    lowers to

        RequiredGroups(groups=(('format_ids',), ('format_options',)), combinator='anyOf')

    Neither member is individually required, so neither appeared in a set built from
    `is_required()`, both were dropped, and :func:`_project_product_fields`'s own
    revalidation then failed with "none of these groups is present, the document requires
    at least one".

    `ConditionalRequired.require` has the same exposure one step along: keeping a trigger
    and dropping the field it requires breaks the rule just as surely.

    **ONLY WHAT PRESENCE DECIDES, which is narrower than "every name a rule mentions".**
    Collecting every name was the first attempt and it was wrong: it pulled in each
    `UniqueItems(key=...)` -- `catalog_types`, `video_placement_types`,
    `sponsored_placement_types` and the rest -- and an ABSENT array satisfies
    `uniqueItems` trivially, so keeping those protects nothing and silently widens the
    projection the buyer asked to narrow.  By the same reading a `forbid` name and a
    `when` trigger are both safe to drop: dropping a forbidden field cannot break a
    prohibition, and dropping a trigger stops the conditional firing at all.
    """
    names: set[str] = set()
    for rule in getattr(model, "_adcp_rules", ()) or ():
        for group in getattr(rule, "groups", ()) or ():
            names.update(group)
        names.update(getattr(rule, "require", ()) or ())
    return frozenset(names)


_REQUIRED_PRODUCT_FIELDS: frozenset[str] = frozenset(
    k for k, v in Product.model_fields.items() if v.is_required()
)

#: Names a RULE binds, which is a DIFFERENT set from the one above and kept apart from it.
#:
#: :data:`_REQUIRED_PRODUCT_FIELDS` means "cannot be None and the model cannot be
#: constructed without them", and callers assert exactly that of it.  A group member is
#: not that: `core/product.json` needs `format_ids` OR `format_options`, so neither is
#: individually non-None and folding them into that set makes the claim false.  What they
#: share is only that PROJECTION MUST NOT DROP THEM, which is what this set is for.
_RULE_BOUND_PRODUCT_FIELDS: frozenset[str] = _names_a_rule_needs(Product)

#: Every string value in the GetProductsField enum (the buyer selection
#: surface, 30 values).
_GET_PRODUCTS_FIELD_VALUES: frozenset[str] = frozenset(f.value for f in GetProductsField)

#: Optional Product.model_fields keys that have no GetProductsField enum
#: entry.  A buyer cannot request or exclude these; the framework always
#: passes them through.
_NON_ENUM_PRODUCT_FIELDS: frozenset[str] = (
    frozenset(Product.model_fields.keys()) - _GET_PRODUCTS_FIELD_VALUES
)


def _project_product_fields(
    response: GetProductsResponse,
    fields: Sequence[_FieldSelection],
) -> GetProductsResponse:
    """Drop unrequested product fields from *response*.

    Keeps: all required-by-schema fields, all non-enum declared fields,
    all extension (``extra='allow'``) fields, and any explicitly requested
    fields.  Drops only: optional enum-declared fields the buyer did not
    request.

    The caller must ensure *fields* is non-empty (the handler guard
    ``if params.fields:`` enforces this).
    """
    requested = frozenset(f.value for f in fields)
    keep_declared = (
        _REQUIRED_PRODUCT_FIELDS
        | _RULE_BOUND_PRODUCT_FIELDS
        | requested
        | _NON_ENUM_PRODUCT_FIELDS
    )

    if response.products is None:
        return response

    projected: list[Product] = []
    for p in response.products:
        raw = p.model_dump(mode="json")
        # Extra keys: present in the serialised dict but not declared in
        # model_fields.  model_dump() with extra='allow' emits them at the
        # top level alongside declared fields.
        extra_keys = frozenset(raw.keys()) - frozenset(Product.model_fields.keys())
        all_keep = keep_declared | extra_keys
        filtered = {k: v for k, v in raw.items() if k in all_keep}
        projected.append(Product.model_validate(filtered))

    logger.debug("[adcp.decisioning] fields projection applied to %d product(s)", len(projected))
    return response.model_copy(update={"products": projected})
