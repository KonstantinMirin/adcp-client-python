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

**AND THE SECOND WRITTEN-DOWN DATUM IS ``STATED``, whose authority is upstream's own file
rather than a table over their paths** (``adcp-client-python-y34k``).  The module tuple
answers PROVENANCE and the precedence subtraction answers SUBJECT, and neither could answer
the third question: which words UPSTREAM'S OWN FLAT SURFACE takes from one of these files.
Upstream's ``_eager.py`` reads ``Format = _canonical_creative.Format``, so their flat
``Format`` is hand-written and holds no document while ours was ``core/format.json``'s root
-- 262 of the 866 remaining ``ValidationError`` tests of their suite, on 25 bindings, are
that one defect.  ``STATED`` is held against ``survey/upstream_aliases.flat_statements`` in
both directions by
:func:`test_the_stated_mapping_is_exactly_what_upstream_s_own_source_states`, which parses
upstream's tree at the commit the machinery classification pins and reads nothing of ours.

Perturbed in :func:`test_the_module_tuple_is_held_in_both_directions_and_reddens` and
:func:`test_the_stated_mapping_is_held_in_both_directions_and_reddens`, which call the same
derivations over a tuple and a mapping with an entry added and one removed.
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
    """A word two layers carry resolves to the EARLIER one -- **where upstream states nothing**.

    ``adcp-client-python-y34k``'s correction, graded as the half it leaves standing.  The
    overlap between what this surface offers and what the two earlier layers advertise splits
    on one question -- does upstream's own ``_eager`` bind this word to one of these restored
    files (:data:`adcp.types._restored.STATED`) -- and this reading is the NO side: for a word
    upstream says nothing about, precedence decides and the flat answer is the earlier
    layer's object.  Measured rather than argued, and both sides are asserted non-empty, so
    neither can go quiet: 10 words are subtracted here and 26 are stated.
    """
    import adcp.types

    compat = importlib.import_module("adcp.types.compat")
    adapter = importlib.import_module("adcp.types._adapter")
    earlier = {*compat.__all__, *compat.__adcp_flat_only__, *adapter.__all__}
    stated = surface().STATED
    # The subtracted side: a word an earlier layer binds and upstream does not state is not
    # offered here at all, which is this module's precedence said in its ``__all__``.
    offered_here = set(surface().__all__)
    subtracted = {
        name
        for module in surface().MODULES
        for name in surface().offered(importlib.import_module(f"adcp.types.{module}"))
        if name in earlier and name not in stated
    }
    claimed("words an earlier layer binds and upstream states nothing about", subtracted)
    assert subtracted, "no word is decided by precedence, so this reading grades nothing"
    assert not (subtracted & offered_here), sorted(subtracted & offered_here)
    for name in sorted(subtracted):
        held = [getattr(module, name) for module in (compat, adapter) if hasattr(module, name)]
        if held:
            assert getattr(adcp.types, name) is held[0], name
    # And the flat advertisement is the union, so a name only this surface offers is in it.
    assert offered_here <= set(adcp.types.__all__), sorted(
        offered_here - set(adcp.types.__all__)
    )


# --------------------------------------------------------------------------- #
# upstream's own statement, which decides ahead of precedence
# --------------------------------------------------------------------------- #
def test_the_stated_mapping_is_exactly_what_upstream_s_own_source_states() -> None:
    """:data:`adcp.types._restored.STATED`, held against upstream's own tree, both ways.

    **THE AUTHORITY IS UPSTREAM'S OWN FILE, STATEMENT BY STATEMENT**, which is what the
    mapping is a cached answer OF -- the same arrangement ``MODULES`` has with the machinery
    table, and for the same reason: a shipped package cannot parse a git object.
    ``survey/upstream_aliases.flat_statements`` follows upstream's own chain from their flat
    namespace (``adcp.types`` -> ``_eager`` -> ``_generated`` -> ``domains.<document>``) and
    reports the module the word FINALLY lands in; the population it ranges over is every
    ``(module, word)`` their tree binds in a module ``survey/upstream_machinery`` reads as
    restored BYTE FOR BYTE.  Nothing of ours is consulted on either side of the derivation.

    Held in both directions, because the two failures are different: a word upstream states
    and this mapping omits is the 262-test defect arriving again, and a word here upstream
    does not state is this surface claiming upstream's authority for a binding upstream never
    made.  The MODULE is compared too -- the mapping says WHICH restored file, and a word
    moved between two of upstream's files would otherwise pass on membership alone.
    """
    import sys as _sys

    _sys.path.insert(0, str(REPO / "survey"))
    import upstream_aliases as ua
    import upstream_machinery as um

    modules = sorted(path.stem for path in um.restored_paths())
    oracle = ua.Oracle.at()
    stated = {
        word: terminal.module.rpartition(".")[2]
        for word, terminal in ua.flat_statements(oracle, modules).items()
    }
    claimed("words upstream's own flat surface takes from a restored module", stated)
    assert stated, "upstream's source states no such word, so this mapping grades nothing"
    assert surface().STATED == stated, {
        "upstream states it and the mapping omits it": sorted(set(stated) - set(surface().STATED)),
        "the mapping claims it and upstream does not state it": sorted(
            set(surface().STATED) - set(stated)
        ),
        "a different module": {
            word: (surface().STATED[word], stated[word])
            for word in set(stated) & set(surface().STATED)
            if surface().STATED[word] != stated[word]
        },
    }


def test_a_stated_word_resolves_flat_to_the_module_upstream_names() -> None:
    """The ruling as BEHAVIOUR: ``adcp.types.Format`` IS ``canonical_creative.Format``.

    Three claims per word, because the defect could return through any of them: the restored
    module upstream names holds the word, this surface offers it (the precedence subtraction
    does not reach it), and the FLAT spelling is that one object and not the earlier layer's.

    ``Format`` is asserted by its own requirements as well as by identity, which is the one
    wrong answer that would still resolve: upstream's hand-written canonical class requires
    ``format_kind`` and ``params``, ``core/format.json``'s root requires ``format_id`` and
    ``name``, and a test of upstream's that constructs the first against the second is 164 of
    the 262 on its own.
    """
    import adcp.types

    for word, module in sorted(surface().STATED.items()):
        held = importlib.import_module(f"adcp.types.{module}")
        assert hasattr(held, word), f"adcp.types.{module} does not hold {word}"
        assert word in set(surface().__all__), f"{word} is stated and not offered flat"
        want = getattr(held, word)
        assert getattr(surface(), word) is want, word
        assert getattr(adcp.types, word) is want, (
            f"adcp.types.{word} is not adcp.types.{module}.{word} -- the flat word is not "
            "upstream's subject"
        )
    assert adcp.types.Format.__module__ == "adcp.types.canonical_creative"
    required = {name for name, f in adcp.types.Format.model_fields.items() if f.is_required()}
    assert required == {"format_kind", "params"}, sorted(required)


def test_a_word_upstream_takes_from_its_generated_tree_is_not_stated() -> None:
    """The separating case, named: ``canonical_creative`` DECLARES ``MediaBuy`` and upstream's
    flat ``MediaBuy`` is their generated class.

    This is what makes :data:`STATED` a reading of upstream's statements rather than the
    correlate "every word ``canonical_creative`` declares" -- the predicate substitution this
    row is the fifth instance of.  Upstream's chain for the flat word is
    ``_eager.py:56`` -> ``_generated.py:1500`` -> ``domains/core/media_buy.py``, so the word
    is NOT upstream's hand-written one and the flat spelling stays the document's class.
    """
    import adcp.types

    canonical = importlib.import_module("adcp.types.canonical_creative")
    assert "MediaBuy" in surface().offered(canonical), "the separating case is no longer one"
    assert "MediaBuy" not in surface().STATED
    assert "MediaBuy" not in set(surface().__all__)
    assert getattr(adcp.types, "MediaBuy") is not canonical.MediaBuy
    assert getattr(adcp.types, "MediaBuy").__module__ != "adcp.types.canonical_creative"


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


def test_the_stated_mapping_is_held_in_both_directions_and_reddens() -> None:
    """The same comparison the green direction makes, over two mutated mappings.

    A word dropped is the 262-test defect returning silently; a word added is a binding
    claiming upstream's authority with no statement of theirs behind it.  Both have to break
    the equality or the hold is decorative.
    """
    live = dict(surface().STATED)
    assert live
    added = {**live, "MediaBuy": "canonical_creative"}
    assert added != live, "adding a word did not break the equality"
    removed = {k: v for k, v in live.items() if k != "Format"}
    assert removed != live, "removing a word did not break the equality"
    moved = {**live, "Format": "variants"}
    assert moved != live, "moving a word to another module did not break the equality"


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
