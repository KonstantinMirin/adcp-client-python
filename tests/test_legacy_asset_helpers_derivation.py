"""The legacy helpers' asset types are DERIVED, and adding a branch is how that is proved.

**WHY THIS FILE EXISTS, and it is a defect report rather than a preference.**
``src/adcp/types/_legacy_assets.py``'s docstring claimed the set was "derived from the
generated ``AssetVariant`` arms rather than listed here, so a schema bump that adds an asset
type (as 3.2 added ``display_tag``) extends key-name inference in the same regeneration".
The claim was true of the intent and false of the mechanism: the derivation read
``get_args(AssetVariant)[0]`` -- the first argument of upstream's generator's
``Annotated[Union[...], Field(discriminator=...)]`` -- and against this compiler's emission,
where a discriminated union is a BASE CLASS plus one child per branch, ``get_args`` answers
``()`` and the subscript raised ``IndexError``. **26 tests of the drop-in run died on it**,
and nothing in this repository asked whether the set was still being derived.

So the property is asserted here, in the only way that can distinguish a derivation from a
list: **add a branch and require the new value to appear.** A hard-coded set passes every
assertion about the 21 values the bundle states today and fails this one.

**THE UNION UNDER TEST IS BUILT HERE AND IS NOT ``AssetVariant``.**  A branch cannot be added
to an emitted class -- ``_branch_models`` is written by the run and a late subclass does not
join it -- so the test declares its own dispatching base, reads it, adds a branch, and reads
it again.  That grades the DERIVATION, which is what went dead; the emitted union's own 21
values are asserted separately below off the document's own registry so both halves are
covered.
"""

from __future__ import annotations

from typing import ClassVar, Literal

import pytest

from adcp.types._base import AdCPBaseModel, BranchDispatchMixin
from adcp.types._legacy_assets import discriminator_values, infer_asset_type


def _a_union(*values: str) -> type:
    """A dispatching base with one branch per value, declared the way the emitter declares one.

    The two carriers are the whole of what :func:`discriminator_values` reads --
    ``_BRANCH_DISCRIMINATOR`` for the keyword and ``_branch_models`` for the registry -- and
    they are assigned after the classes exist, which is the order the emitted modules use.
    """

    class Base(BranchDispatchMixin, AdCPBaseModel):
        _branch_models: ClassVar[tuple[type[AdCPBaseModel], ...]] = ()
        _BRANCH_DISCRIMINATOR: ClassVar[str] = "asset_type"

    branches = []
    for value in values:
        branch = type(
            f"Branch{value.title().replace('_', '')}",
            (Base,),
            {"__annotations__": {"asset_type": Literal[value]}, "asset_type": value},  # type: ignore[valid-type]
        )
        branches.append(branch)
    Base._branch_models = tuple(branches)
    return Base


def test_a_branch_added_to_the_union_appears_in_the_derived_set() -> None:
    """The property the old mechanism claimed and did not have.

    A list of asset types passes the first assertion and fails the second; only a reading of
    the branch registry passes both.
    """
    union = _a_union("image", "url", "text")
    assert discriminator_values(union) == {"image", "url", "text"}

    extra = type(
        "BranchHologram",
        (union,),
        {"__annotations__": {"asset_type": Literal["hologram"]}, "asset_type": "hologram"},  # type: ignore[valid-type]
    )
    union._branch_models = (*union._branch_models, extra)  # type: ignore[attr-defined]
    assert discriminator_values(union) == {"image", "url", "text", "hologram"}


def test_a_branch_removed_from_the_union_leaves_the_derived_set() -> None:
    """The other direction, which a stale list also passes: a retired type stops being known."""
    union = _a_union("image", "url", "text")
    union._branch_models = union._branch_models[:-1]  # type: ignore[attr-defined]
    assert discriminator_values(union) == {"image", "url"}


def test_the_derivation_refuses_a_class_with_no_discriminator_rather_than_answering_empty() -> None:
    """**NO SILENT FALLBACK**, which is the clause that makes the fix a fix.

    An empty answer would make every key-name inference quietly stop working while every
    caller went on returning a value -- which is exactly how the dead derivation survived a
    release.  A class with no discriminator raises; a class with no branches answers the empty
    set and says so by being empty, which the caller below is asserted against.
    """

    class NotAUnion(AdCPBaseModel):
        pass

    with pytest.raises(AttributeError):
        discriminator_values(NotAUnion)


def test_the_emitted_asset_union_is_what_key_name_inference_reads() -> None:
    """The live half: the helper's answer IS the emitted union's branch values.

    Stated as an equality against the union rather than against a literal set, so a bundle
    that adds an asset type moves both sides together and this test keeps grading the join
    rather than a number.
    """
    from adcp.types._legacy_assets import _known_asset_types
    from adcp.types.core import AssetVariant

    derived = discriminator_values(AssetVariant)
    assert derived, "the emitted asset union routes no value -- the derivation is dead again"
    assert _known_asset_types() == derived
    # The 3.2 addition the helper's docstring cites by name, which is the one value whose
    # presence proves the inference reaches a type the bundle added after the helper was
    # written.
    assert "display_tag" in derived
    assert infer_asset_type("display_tag", {}) == "display_tag"


def test_an_unknown_key_falls_through_to_field_presence_and_not_to_a_default() -> None:
    """The caller's own contract, so a derivation that over-answers is caught here too.

    A key naming no asset type must reach the field rules; if the derived set ever contained
    every string the first branch would swallow this.
    """
    assert infer_asset_type("whatever", {"url": "u", "width": 1, "height": 2}) == "image"
    assert infer_asset_type("whatever", {"url": "u"}) == "url"
    assert infer_asset_type("whatever", {"content": "c"}) == "text"
    assert infer_asset_type("whatever", {}) is None
