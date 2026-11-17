"""What became of issue #742's open-union forward compatibility.

#742 made ``Format.assets`` and a repeatable group's ``assets`` TOLERATE an
``asset_type`` this pin has no class for: the undeclared value landed on a
fallback class and kept its unknown keys as extras. That tolerance was a
WIDENING -- `core/format.json` states the slot as a CLOSED ``oneOf`` over the
asset types it declares, 21 individual and 21 group, and an undeclared value is
a value the document refuses. Section 2 licenses a widening only where a
keyword cannot be expressed, and a ``oneOf`` can be; the old one came from a
hand-written frozenset in ``aliases.py`` plus a fallback class, which is also
how it fell 7 behind the individual classes and 9 behind the group ones.

So this emission takes no fallback at the slot, and these tests grade the
closed union instead: an undeclared or malformed ``asset_type`` is refused
there, every declared one reaches its own class, and the population is derived
from the document rather than listed.

``UnknownFormatAsset`` and ``UnknownGroupAsset`` still resolve -- to
``$defs/baseIndividualAsset`` and ``$defs/baseGroupAsset``, the nodes the
branches inherit. Those nodes state that ``asset_type`` is REQUIRED and state
nothing about its type, which is section 5's required-with-no-declaration, so
the base alone admits any value for the key. The refusal is the slot's.
"""

from __future__ import annotations

from typing import get_args

import pytest

# `FormatAssetUnion` and `GroupFormatAssetUnion` are refused on the flat surface
# as Annotated expressions with no document behind them, and in this emission
# there is nothing for them to name separately: an open `asset_type` union IS its
# base, which dispatches a payload to the branch it satisfies and keeps an
# undeclared `asset_type` on the base itself. So the union and the fallback are
# one class -- `BaseIndividualAsset`, already bound as `UnknownFormatAsset` --
# and that identity is what this file now pins.
from adcp.types.domains.core import format as format_module
from adcp.types.domains.core.format import Assets94
from adcp.types.domains.core.format import LegacyFormat as Format
from pydantic import TypeAdapter, ValidationError

from adcp.types import (
    ImageFormatAsset,
    RepeatableAssetGroup,
    UnknownFormatAsset,
    UnknownGroupAsset,
)


def _make_format_id(name: str) -> dict:
    return {"agent_url": "https://test.example.com", "id": name}


def _pinned_asset_type(model: type) -> str | None:
    """The one ``asset_type`` a branch pins, read off its annotation.

    The document states the discriminator with a `const`, which this emission
    lowers to ``Literal["image"]`` and leaves REQUIRED -- so the pin is in the
    annotation and not in a field default. Reading ``.default`` here found
    nothing at all and took the whole module with it at import.
    """
    field = getattr(model, "model_fields", {}).get("asset_type")
    if field is None:
        return None
    pins = get_args(field.annotation)
    if len(pins) != 1 or not isinstance(pins[0], str):
        return None
    return pins[0]


def _declared_asset_types(base: type) -> dict[str, type]:
    """``asset_type`` -> the class this pin generated for it, for one asset base.

    Read off the live classes rather than listed, which is the whole point: the
    union's own vocabulary is derived the same way, so a schema refresh moves
    both together. Asserted non-empty because a derivation that matches nothing
    passes everything.
    """
    found = {
        pinned: value
        for value in vars(format_module).values()
        if isinstance(value, type)
        and issubclass(value, base)
        and value is not base
        and (pinned := _pinned_asset_type(value)) is not None
    }
    assert found, f"no generated subclass of {base.__name__} declares an asset_type"
    return found


def _an_undeclared_asset_type(base: type) -> str:
    """An ``asset_type`` this pin has no class for, checked against the ones it has."""
    candidate = "x_future_asset_type"
    assert candidate not in _declared_asset_types(base), (
        f"{candidate!r} became a declared asset_type; pick another stand-in, and "
        "check whether the tests below were grading routing or only acceptance"
    )
    return candidate


_UNDECLARED_INDIVIDUAL = _an_undeclared_asset_type(format_module.BaseIndividualAsset)
_UNDECLARED_GROUP = _an_undeclared_asset_type(format_module.BaseGroupAsset)


class TestTheSlotIsAClosedUnion:
    """An ``asset_type`` the document does not declare is refused at the slot."""

    def test_an_undeclared_individual_asset_type_is_refused(self):
        with pytest.raises(ValidationError) as refused:
            Format.model_validate(
                {
                    "format_id": _make_format_id("test"),
                    "name": "Test",
                    "assets": [
                        {
                            "asset_id": "impression_tracker",
                            "asset_type": _UNDECLARED_INDIVIDUAL,
                            "item_type": "individual",
                            "required": False,
                        },
                    ],
                }
            )
        assert "oneOf" in {error["type"] for error in refused.value.errors()}

    def test_an_undeclared_group_asset_type_is_refused(self):
        with pytest.raises(ValidationError) as refused:
            Assets94.model_validate(
                {
                    "asset_group_id": "slide",
                    "item_type": "repeatable_group",
                    "required": True,
                    "min_count": 1,
                    "max_count": 5,
                    "assets": [
                        {
                            "asset_id": "track",
                            "asset_type": _UNDECLARED_GROUP,
                            "required": False,
                        },
                    ],
                }
            )
        # A group slot's branches pin `asset_type` with a `const`, and the group
        # list is not itself a `oneOf` node, so the refusal arrives as the
        # literal error from the branch rather than as a `oneOf` error.
        assert "literal_error" in {error["type"] for error in refused.value.errors()}

    def test_extra_keys_do_not_buy_an_undeclared_type_a_way_in(self):
        """The fallback used to keep unknown keys in ``__pydantic_extra__``."""
        with pytest.raises(ValidationError):
            Format.model_validate(
                {
                    "format_id": _make_format_id("test"),
                    "name": "Test",
                    "assets": [
                        {
                            "asset_id": "track",
                            "asset_type": _UNDECLARED_INDIVIDUAL,
                            "item_type": "individual",
                            "required": False,
                            "tracking_url": "https://example.com/track",
                            "fire_on": "impression",
                        },
                    ],
                }
            )

    def test_a_declared_asset_type_still_parses(self):
        """Closing the union did not cost the types the document DOES declare."""
        fmt = Format.model_validate(
            {
                "format_id": _make_format_id("test"),
                "name": "Test",
                "assets": [
                    {
                        "asset_id": "hero",
                        "asset_type": "image",
                        "item_type": "individual",
                        "required": True,
                    },
                ],
            }
        )
        assert fmt.assets is not None
        asset = fmt.assets[0]
        assert isinstance(asset, ImageFormatAsset)
        assert asset.asset_type == "image"

    def test_a_mixed_list_is_refused_for_the_one_undeclared_member(self):
        with pytest.raises(ValidationError):
            Format.model_validate(
                {
                    "format_id": _make_format_id("mixed"),
                    "name": "Mixed",
                    "assets": [
                        {
                            "asset_id": "img",
                            "asset_type": "image",
                            "item_type": "individual",
                            "required": True,
                        },
                        {
                            "asset_id": "tracker",
                            "asset_type": _UNDECLARED_INDIVIDUAL,
                            "item_type": "individual",
                            "required": False,
                        },
                    ],
                }
            )

    def test_repeatable_group_still_routes_correctly(self):
        """RepeatableAssetGroup (item_type='repeatable_group') still parses."""
        fmt = Format.model_validate(
            {
                "format_id": _make_format_id("carousel"),
                "name": "Carousel",
                "assets": [
                    {
                        "asset_group_id": "slide",
                        "item_type": "repeatable_group",
                        "required": True,
                        "min_count": 2,
                        "max_count": 5,
                        "assets": [
                            {"asset_id": "img", "asset_type": "image", "required": True},
                        ],
                    },
                ],
            }
        )
        assert fmt.assets is not None
        assert isinstance(fmt.assets[0], RepeatableAssetGroup)

    def test_a_declared_group_asset_type_still_parses(self):
        from adcp.types import ImageFormatGroupAsset

        group = Assets94.model_validate(
            {
                "asset_group_id": "product",
                "item_type": "repeatable_group",
                "required": True,
                "min_count": 1,
                "max_count": 10,
                "assets": [
                    {
                        "asset_id": "img",
                        "asset_type": "image",
                        "required": True,
                    },
                ],
            }
        )
        assert isinstance(group.assets[0], ImageFormatGroupAsset)


class TestUnknownFormatAssetContract:
    """Structural invariants on the fallback type."""

    def test_requires_asset_id(self):
        """asset_id is required (inherited from BaseIndividualAsset)."""
        with pytest.raises(ValidationError):
            UnknownFormatAsset.model_validate(
                {
                    "asset_type": _UNDECLARED_INDIVIDUAL,
                    "item_type": "individual",
                    "required": False,
                    # asset_id missing
                }
            )

    def test_requires_required_field(self):
        """required is required (inherited from BaseIndividualAsset)."""
        with pytest.raises(ValidationError):
            UnknownFormatAsset.model_validate(
                {
                    "asset_id": "track",
                    "asset_type": _UNDECLARED_INDIVIDUAL,
                    "item_type": "individual",
                    # required missing
                }
            )

    def test_asset_type_is_required_not_empty_default(self):
        """asset_type has no default — a missing discriminator is a real error."""
        with pytest.raises(ValidationError):
            UnknownFormatAsset.model_validate(
                {
                    "asset_id": "track",
                    "item_type": "individual",
                    "required": False,
                    # asset_type missing
                }
            )

    def test_unknown_format_asset_is_unknown_form(self):
        """UnknownFormatAsset carries an asset_type this pin has no class for.

        The vocabulary is derived, not restated. This assertion used to list 14
        asset types by hand — the same stale frozenset the union routed by, in a
        second copy, which is why ``pixel_tracker`` satisfied it while being a
        type the schema declares and the generator had a class for.
        """
        asset = UnknownFormatAsset.model_validate(
            {
                "asset_id": "x",
                "asset_type": _UNDECLARED_INDIVIDUAL,
                "item_type": "individual",
                "required": False,
            }
        )
        assert asset.asset_type not in _declared_asset_types(format_module.BaseIndividualAsset)


class TestMalformedAssetTypeIsAValidationError:
    """A non-string ``asset_type`` must fail validation, not crash the discriminator.

    Asked at the SLOT, which is where the document states the union. The base
    classes admit it: ``$defs/baseIndividualAsset`` requires the key and states
    nothing about its type, so the field is section 5's
    required-with-no-declaration and lowers to ``Any``. Asking the base was
    asking the one node whose own declaration says nothing.
    """

    @pytest.mark.parametrize("asset_type", [["image"], {"kind": "image"}, 7, None])
    def test_the_individual_slot_refuses_it(self, asset_type: object) -> None:
        with pytest.raises(ValidationError):
            Format.model_validate(
                {
                    "format_id": _make_format_id("malformed"),
                    "name": "Malformed",
                    "assets": [
                        {
                            "asset_id": "logo",
                            "item_type": "individual",
                            "required": True,
                            "asset_type": asset_type,
                        }
                    ],
                }
            )

    @pytest.mark.parametrize("asset_type", [["image"], {"kind": "image"}, 7, None])
    def test_the_group_slot_refuses_it(self, asset_type: object) -> None:
        with pytest.raises(ValidationError):
            Assets94.model_validate(
                {
                    "asset_group_id": "slide",
                    "item_type": "repeatable_group",
                    "required": True,
                    "min_count": 1,
                    "max_count": 5,
                    "assets": [
                        {"asset_id": "logo", "required": True, "asset_type": asset_type}
                    ],
                }
            )

    @pytest.mark.parametrize(
        ("base", "item"),
        [
            pytest.param(UnknownFormatAsset, {"item_type": "individual"}, id="individual"),
            pytest.param(UnknownGroupAsset, {}, id="group"),
        ],
    )
    def test_the_base_requires_the_key_and_constrains_nothing(
        self, base: type, item: dict
    ) -> None:
        built = TypeAdapter(base).validate_python(
            {**item, "asset_id": "logo", "required": True, "asset_type": ["image"]}
        )
        assert built.asset_type == ["image"]
        with pytest.raises(ValidationError):
            TypeAdapter(base).validate_python({**item, "asset_id": "logo", "required": True})


class TestPublicAPIExports:
    """New types are accessible from the public surface."""

    def test_imports_from_adcp_types(self):
        from adcp.types import (
            UnknownFormatAsset,
            UnknownGroupAsset,
        )

        assert UnknownFormatAsset is format_module.BaseIndividualAsset
        assert UnknownGroupAsset is format_module.BaseGroupAsset


class TestDeclaredAssetTypesAreNotDegraded:
    """Every asset_type this pin generated a class for must reach that class.

    The open union used to route by a hand-written frozenset 7 behind the
    generated individual classes and 9 behind the group ones, so seven
    individual and nine group types arrived on the fallback with their typed
    fields in __pydantic_extra__, while the generated classes for all of them
    sat unused. The union is closed now and the population is derived from the
    emitted branches, so this grades that end to end — at the PARSE level,
    because where a document LANDS is the claim, and counting branches says
    nothing about it.

    Parametrized over the generated classes rather than a list, so an asset type
    a schema refresh adds is covered the moment its class is generated.
    """

    @pytest.mark.parametrize(
        "asset_type,expected",
        sorted(_declared_asset_types(format_module.BaseIndividualAsset).items()),
    )
    def test_each_declared_individual_type_reaches_its_class(
        self, asset_type: str, expected: type
    ) -> None:
        fmt = Format.model_validate(
            {
                "format_id": _make_format_id("declared"),
                "name": "Declared",
                "assets": [
                    {
                        "asset_id": "slot",
                        "asset_type": asset_type,
                        "item_type": "individual",
                        "required": True,
                    }
                ],
            }
        )
        assert fmt.assets is not None
        asset = fmt.assets[0]
        assert type(asset) is expected
        assert type(asset) is not UnknownFormatAsset
        # A degraded asset keeps its type-specific fields as untyped extras, so
        # an empty extra dict is part of what "reached its class" means.
        assert not (asset.__pydantic_extra__ or {})

    @pytest.mark.parametrize(
        "asset_type,expected",
        sorted(_declared_asset_types(format_module.BaseGroupAsset).items()),
    )
    def test_each_declared_group_type_reaches_its_class(
        self, asset_type: str, expected: type
    ) -> None:
        group = Assets94.model_validate(
            {
                "asset_group_id": "slide",
                "item_type": "repeatable_group",
                "required": True,
                "min_count": 1,
                "max_count": 5,
                "assets": [{"asset_id": "slot", "asset_type": asset_type, "required": True}],
            }
        )
        slot = group.assets[0]
        assert type(slot) is expected
        assert type(slot) is not UnknownGroupAsset
        assert not (slot.__pydantic_extra__ or {})

    def test_the_derivation_covers_what_the_pinned_schema_declares(self) -> None:
        """The parametrized population is the schema's, not a subset of it.

        Without this, a generator that stopped emitting a class for one asset
        type would shrink the population above and stay green — the two tests
        would grade fewer rows and say nothing about the one that vanished.
        """
        import json
        from pathlib import Path

        from adcp.validation.version import resolve_bundle_key

        root = Path(__file__).parent.parent
        pinned = (root / "src/adcp/ADCP_VERSION").read_text().strip()
        schema_path = root / "schemas/cache" / resolve_bundle_key(pinned) / "core/format.json"
        assert schema_path.is_file(), f"no pinned format schema at {schema_path}"
        branches = json.loads(schema_path.read_text())["properties"]["assets"]["items"][
            "oneOf"
        ]

        def slot(item_type: str) -> dict:
            matching = [
                branch
                for branch in branches
                if branch.get("properties", {}).get("item_type", {}).get("const") == item_type
            ]
            assert len(matching) == 1, f"expected one {item_type!r} branch, got {len(matching)}"
            return matching[0]

        # The two branches nest to different depths and are selected by their
        # item_type const, not by position.
        individual = {a["properties"]["asset_type"]["const"] for a in slot("individual")["oneOf"]}
        group = {
            a["properties"]["asset_type"]["const"]
            for a in slot("repeatable_group")["properties"]["assets"]["items"]["oneOf"]
        }
        assert individual, "the individual branch declares no asset_type consts"
        assert group, "the repeatable-group branch declares no asset_type consts"
        assert set(_declared_asset_types(format_module.BaseIndividualAsset)) == individual
        assert set(_declared_asset_types(format_module.BaseGroupAsset)) == group
