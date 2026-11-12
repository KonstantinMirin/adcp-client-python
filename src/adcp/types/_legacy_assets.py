"""Pure, opt-in normalization of pre-v3 creative asset dictionaries."""

from collections.abc import Mapping
from functools import cache
from typing import Any, Literal, get_args, get_origin


def discriminator_values(union: type) -> frozenset[str]:
    """Every value the discriminator takes across one union's emitted branches.

    **READS THE DECLARATION, NEVER A TYPE EXPRESSION'S LAYOUT.** This compiler states a
    discriminated union as a BASE CLASS plus one child per branch: ``_BRANCH_DISCRIMINATOR``
    names the keyword the document discriminates on and ``_branch_models`` is the registry of
    branches, each pinning its own value as a ``Literal`` on that field. So the set of values
    the union routes is a question the base can be ASKED, and the answer is derived from the
    branches that exist rather than from where they sit inside a nested annotation.

    The reading it replaces was ``get_args(X)[0]`` -- the first argument of an
    ``Annotated[Union[...], Field(discriminator=...)]``, which is upstream's generator's
    layout and not a fact any document states. Against a base class ``get_args`` answers
    ``()``, so the subscript raised ``IndexError`` and took 26 tests with it. A type
    expression's argument order is a property of whoever wrote the expression; a branch
    registry is a property of the document.

    Raises ``AttributeError`` where ``union`` is not a dispatching base. **There is no
    fallback and there must not be**: a silent default is how the dead derivation went
    unnoticed through a whole release, and an empty answer here would make every key-name
    inference below quietly stop working while every caller kept returning a value.
    """
    keyword: str = union._BRANCH_DISCRIMINATOR  # type: ignore[attr-defined]
    if not keyword:
        raise AttributeError(f"{union.__name__} declares no _BRANCH_DISCRIMINATOR to read")
    values: set[str] = set()
    for branch in union._branch_models:  # type: ignore[attr-defined]
        field = branch.model_fields.get(keyword)
        if field is None:
            continue
        annotation = field.annotation
        # The branch pins its own value, which is a ``Literal`` of one member at every
        # branch of this bundle; a branch that pins nothing contributes nothing rather
        # than contributing the field's type.
        if get_origin(annotation) is Literal:
            values.update(str(member) for member in get_args(annotation))
    return frozenset(values)


@cache
def _known_asset_types() -> frozenset[str]:
    """Every ``asset_type`` the pinned schema's canonical asset union routes.

    Derived from the emitted ``AssetVariant`` branches rather than listed here, so a schema
    bump that adds an asset type (as 3.2 added ``display_tag``) extends key-name inference in
    the same regeneration. Imported on first use: the generated asset graph is not needed to
    import the legacy helpers.
    """
    from adcp.types.core import AssetVariant

    return discriminator_values(AssetVariant)


def infer_asset_type(asset_key: str, asset: Mapping[str, Any]) -> str | None:
    """Infer a missing discriminator from an exact key, then field presence.

    Keys naming any asset_type the pinned schema declares (``display_tag``,
    ``card``, ...) take precedence over fields. Otherwise URL plus both
    dimensions implies image, URL alone implies url, and content implies text.
    Unknown keys without those fields return None for validation to diagnose.
    This function does not inspect or replace an existing discriminator.
    """
    if asset_key in _known_asset_types():
        return asset_key
    if "url" in asset:
        return "image" if "width" in asset and "height" in asset else "url"
    if "content" in asset:
        return "text"
    return None


def coerce_legacy_asset(asset_key: str, asset: Mapping[str, Any]) -> dict[str, Any]:
    """Copy an asset, infer missing asset_type, and demote dimensionless images.

    An image with a URL but missing either dimension becomes a url asset;
    any remaining width/height is removed. Existing discriminators otherwise
    survive unchanged, including unknown values. This normalizes rather than
    validates: malformed or ambiguous assets still fail normal model validation.
    Nested values are preserved; neither the input mapping nor its values are
    modified.
    """
    out = dict(asset)
    if "asset_type" not in out:
        inferred = infer_asset_type(asset_key, out)
        if inferred is not None:
            out["asset_type"] = inferred
    if out.get("asset_type") == "image" and not ("width" in out and "height" in out):
        if "url" in out:
            out.pop("width", None)
            out.pop("height", None)
            out["asset_type"] = "url"
    return out


def coerce_legacy_assets(assets: Mapping[str, Any]) -> dict[str, Any]:
    """Copy an asset mapping and normalize each dictionary with legacy rules.

    Non-mapping values and unknown keys are retained for model validation.
    Every mapping value is copied, so repeated normalization is idempotent
    without modifying stored rows or caller-owned dictionaries.
    """
    return {
        key: coerce_legacy_asset(key, value) if isinstance(value, Mapping) else value
        for key, value in assets.items()
    }
