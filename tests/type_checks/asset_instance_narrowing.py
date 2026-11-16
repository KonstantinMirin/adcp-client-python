"""Adopter contract for the public creative-asset discriminated union."""

from typing import Literal

from typing_extensions import assert_type

from adcp import AssetInstance
from adcp.types.core import AssetVariantImage, AssetVariantVideo

# **TWO WORDS OF THIS FIXTURE WERE THE PREVIOUS GENERATOR'S SHAPE AND NOT THE DOCUMENT'S.**
#
# ``AssetInstance`` is ``core/assets/asset-union.json#``, and what we emit there is the
# union ROOT -- one class, ``AssetVariant``, with a branch subclass per ``#/oneOf/{0..20}``.
# Narrowing it goes through those branches: ``AssetVariantImage`` subclasses BOTH the root
# and ``core/assets/image-asset.json#``, so the branch is where the union's membership and
# the asset document's fields meet.  Narrowing by the asset document's own class instead
# (``ImageContent``) is the shape upstream's hand-written union had -- a flat union of the
# 20 asset roots -- and against a dispatch root it narrows nothing.
#
# ``AssetInstanceType`` is gone from this fixture and from ``adcp.__all__``: no node of the
# pinned bundle states a FLAT asset-type vocabulary.  The 21 values live as one ``const``
# per branch, so there is no class to re-export and a minted ``Literal[...]`` would be the
# second type the alias layer forbids.  The exhaustive discriminator a narrowing adopter
# wants is each branch's own ``asset_type``, reached below off the narrowed branch.
#
# ``FINDINGS-rootnames.md`` carries the ground for both.


def dimensions(asset: AssetInstance) -> tuple[int, int] | None:
    # Mypy narrows Pydantic model unions by runtime class.
    if isinstance(asset, AssetVariantImage):
        assert_type(asset, AssetVariantImage)
        assert_type(asset.asset_type, Literal["image"])
        return asset.width, asset.height
    if isinstance(asset, AssetVariantVideo):
        assert_type(asset, AssetVariantVideo)
        return asset.width, asset.height
    return None
