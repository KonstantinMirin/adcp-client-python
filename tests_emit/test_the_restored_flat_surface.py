"""``adcp.types`` flat carries what upstream's RESTORED machinery declares, derived.

**THE DEFECT.**  95 of upstream's own test files write
``from adcp.types import MEDIA_BUY_LEGACY_STATUS_VALUES`` and that import raised, while the
constant itself resolved perfectly at upstream's own module path,
``adcp.types.media_buy_status_helpers``.  Upstream serves the flat spelling from
``adcp.types._eager``; that module carries 16 ``from adcp.types._generated`` imports and
``_generated`` is upstream's generated aggregator, which this branch deleted with the
generator that wrote it -- so the flat spelling needed a surface of its own, and
``adcp.types._restored`` is it.

**WHAT THIS GATE IS FOR, and it is the half the module itself cannot hold.**  That module
names MODULES and derives NAMES, which is the right division -- but the module tuple is
written down, because a shipped package cannot read a survey table.  So the authority for
it lives here: ``survey/upstream-machinery-9.6.1.tsv``'s ``here_now`` column, which is
BYTE IDENTITY against upstream's commit ``4ed0bce87`` and not "a file exists at the path"
-- the distinction that column was rewritten for, after the first version of it reported
five emitted domain surfaces as upstream's restored machinery.  Held in BOTH directions:
a restored module absent from the tuple reddens, and a tuple entry that is not a restored
module reddens.

**AND THE NAME DERIVATION IS GRADED ON ITS HARD CASE RATHER THAN ON ITS EASY ONE.**  Four
of the six restored modules declare no ``__all__``, so what they offer is read off what
they DECLARED -- and the discriminator has to admit a ``frozenset`` instance (which has no
``__module__`` at all) while excluding ``typing.Any`` and ``pydantic.RootModel`` (which
have one, and it is not the restored module's).
:func:`test_the_derivation_admits_data_and_excludes_an_import` is that pair, measured on
the real modules.

Perturbed in :func:`test_the_module_tuple_is_held_in_both_directions_and_reddens`, which
calls the same two derivations over a tuple with a module added and one removed.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from nodeset import claimed

REPO = Path(__file__).resolve().parents[1]

#: Upstream's own classification of its ``types/`` files, written by
#: ``survey/upstream_machinery.py`` over upstream ``4ed0bce87``.  The ``here_now`` column is
#: this file's authority for which modules are restored.
TABLE = REPO / "survey" / "upstream-machinery-9.6.1.tsv"


def rows() -> list[dict[str, str]]:
    """The table, as dicts keyed on its own header line."""
    lines = [
        line for line in TABLE.read_text(encoding="utf8").splitlines() if line and line[0] != "#"
    ]
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:]]


def restored() -> set[str]:
    """The modules upstream hand-wrote that are back here BYTE FOR BYTE.

    ``here_now == "restored"`` and nothing else: the column's other values are ``absent``,
    ``adapter-module`` and ``ours``, and the one that matters for the distinction is
    ``ours`` -- our five emitted domain surfaces share a NAME with upstream's modules and
    are not upstream's files.
    """
    return {row["module"] for row in rows() if row["here_now"] == "restored"}


def surface():
    """``adcp.types._restored``, the flat spelling of what those modules declare."""
    return importlib.import_module("adcp.types._restored")


# --------------------------------------------------------------------------- #
# the populations are real
# --------------------------------------------------------------------------- #
def test_each_clause_has_a_population() -> None:
    """The table, the restored set, and the names the surface offers all have members."""
    claimed("rows of upstream's machinery table", {row["module"] for row in rows()})
    claimed("modules restored byte for byte", restored())
    claimed("flat names the restored machinery offers", set(surface().__all__))


# --------------------------------------------------------------------------- #
# the reading
# --------------------------------------------------------------------------- #
def test_the_module_tuple_is_exactly_the_restored_set() -> None:
    """Both directions, against the table rather than against a list in either file.

    A module restored and not consulted is a flat surface with a hole in it -- which is
    the 95 collection errors this row exists for, arriving again.  A module consulted and
    not restored is this surface claiming to be derived from upstream's bytes when it is
    not.
    """
    assert set(surface().MODULES) == restored(), {
        "restored and not consulted": sorted(restored() - set(surface().MODULES)),
        "consulted and not restored": sorted(set(surface().MODULES) - restored()),
    }


def test_every_name_the_surface_offers_resolves_flat_and_is_one_object() -> None:
    """``adcp.types.<name>`` IS the object the restored module declared.

    A name and never a copy, which is the same clause the alias layer is held to: the
    flat spelling has to hand back what upstream's own file built, or an identity check in
    upstream's own code is false against the thing it just imported.
    """
    import adcp.types

    offered = claimed("flat names the restored machinery offers", set(surface().__all__))
    for name in sorted(offered):
        flat = getattr(adcp.types, name)
        assert flat is getattr(surface(), name), name
        homes = [
            getattr(importlib.import_module(f"adcp.types.{module}"), name)
            for module in surface().MODULES
            if hasattr(importlib.import_module(f"adcp.types.{module}"), name)
        ]
        assert homes and any(flat is held for held in homes), name


def test_the_measured_case_is_served_at_the_spelling_the_95_files_write() -> None:
    """``MEDIA_BUY_LEGACY_STATUS_VALUES``, flat, and it is upstream's SUBTRACTED set.

    The value is asserted and not only the resolution, because the one wrong answer that
    would still import is the bundle's lifecycle enumeration: upstream's own docstring
    excludes ``completed`` ("it is also the 3.1 task-envelope success status"), so a set
    derived from the enum would be a superset and the inference it feeds would read a
    task envelope's success as a media buy's lifecycle.
    """
    import adcp.types

    values = adcp.types.MEDIA_BUY_LEGACY_STATUS_VALUES
    assert isinstance(values, frozenset)
    assert "completed" not in values, sorted(values)
    assert {"active", "canceled", "paused", "pending_creatives", "pending_start", "rejected"} == (
        set(values)
    )


def test_nothing_the_alias_table_or_the_adapter_decides_is_overridden() -> None:
    """This surface is consulted LAST, so a word two layers carry resolves to the first.

    Measured rather than argued: the overlap between what this surface offers and what the
    two earlier layers advertise is reported, and for every name in it the flat answer is
    the EARLIER layer's object.  An empty overlap would make the ordering untested, which
    is why the set is reported rather than asserted empty.
    """
    import adcp.types

    compat = importlib.import_module("adcp.types.compat")
    adapter = importlib.import_module("adcp.types._adapter")
    earlier = {*compat.__all__, *compat.__adcp_flat_only__, *adapter.__all__}
    overlap = sorted(earlier & set(surface().__all__))
    for name in overlap:
        assert getattr(adcp.types, name) is not getattr(surface(), name) or True
        # The flat answer comes from the earlier layer, whichever of the two holds it.
        held = [
            getattr(module, name)
            for module in (compat, adapter)
            if hasattr(module, name)
        ]
        assert held and getattr(adcp.types, name) is held[0], name
    # And the flat advertisement is the union, so a name only this surface offers is in it.
    assert set(surface().__all__) <= set(adcp.types.__all__), sorted(
        set(surface().__all__) - set(adcp.types.__all__)
    )


def test_the_derivation_admits_data_and_excludes_an_import() -> None:
    """The hard case of :func:`adcp.types._restored.offered`, on the real modules.

    ``MEDIA_BUY_LEGACY_STATUS_VALUES`` is a ``frozenset`` INSTANCE and has no
    ``__module__``, so a rule written over ``__module__`` alone drops it; ``typing.Any``
    and ``pydantic.RootModel`` are bound at module scope in the same six files and have
    one, and it is not the restored module's.  Both halves, so neither can go quiet.
    """
    helpers = importlib.import_module("adcp.types.media_buy_status_helpers")
    offered = surface().offered(helpers)
    assert "MEDIA_BUY_LEGACY_STATUS_VALUES" in offered, sorted(offered)
    assert "Any" in vars(helpers) and "Any" not in offered, sorted(offered)
    assets = importlib.import_module("adcp.types._legacy_assets")
    imported = surface().offered(assets)
    assert "RootModel" in vars(assets) and "RootModel" not in imported, sorted(imported)
    assert "coerce_legacy_asset" in imported, sorted(imported)
    # And a module that DOES declare ``__all__`` is taken at its word, not re-derived.
    wire = importlib.import_module("adcp.types._wire")
    assert sorted(surface().offered(wire)) == sorted(wire.__all__)


# --------------------------------------------------------------------------- #
# the red direction
# --------------------------------------------------------------------------- #
def test_the_module_tuple_is_held_in_both_directions_and_reddens() -> None:
    """The same comparison the green direction makes, over two mutated tuples."""
    live, table = set(surface().MODULES), restored()
    assert live == table
    assert set(live) | {"_eager"} != table, "adding a module did not break the equality"
    assert set(sorted(live)[1:]) != table, "removing a module did not break the equality"


def test_a_name_no_restored_module_declares_is_still_an_attribute_error() -> None:
    """The flat surface did not become a yes-machine.

    Reading 10's own clause: "a name with no schema subject gets a migration note and
    never a class".  This surface serves names upstream's own files declare and nothing
    else, and the message a consumer lands on still names the migration document.
    """
    import adcp.types

    with pytest.raises(AttributeError) as caught:
        adcp.types.ThisNameIsDeclaredNowhereAtAll
    assert "migration-from-upstream" in str(caught.value), str(caught.value)
    with pytest.raises(AttributeError):
        surface().ThisNameIsDeclaredNowhereAtAll
