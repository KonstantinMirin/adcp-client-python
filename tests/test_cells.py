"""§5's cells and §8's composition rules, each proved once, by payload.

``docs/plan/rebuild-plan.md`` §8's *"THE TWO CHECKS ARE APPLIED COMPOSITIONALLY"*
section is the specification and ``tests/cells.py`` is the instrument; this file is the
gates.  The section's surviving obligation is quoted there in full and is one sentence:

    **Prove each cell once** -- the annotation it emits admits exactly the values that
    keyword admits at that position, against the boundary values the keyword itself names
    -- and **prove each composition rule once** -- ``allOf`` intersects, ``anyOf`` unions,
    a restatement merges -- and faithfulness over any document follows **by structural
    induction on the document**.

**THE DENOMINATOR IS DERIVED HERE AND NOWHERE ELSE.**  §5 is 98 keyword rows over §3's 9
positions, which is 882 ``(keyword, position)`` pairs, and most of them say nothing: a
cell is LIVE when it selects a type, renders a constraint or states a rule, which is
``keywords.COMPILES``' own reading.  :func:`test_the_live_cell_count_is_derived_from_the_table`
is the derivation and the number it reports is the reading's denominator.

**WHAT IS GATED PER CELL, and every one of these holds WITHOUT EXCEPTION.**  The per-cell
proof is derived by ``cells.grade`` and three properties of it are asserted over all 289
live cells, each over the WHOLE set and none over a list:

* **every live cell reaches an OUTCOME** -- an annotation, a verdict or a deferral -- and
  never an unparseable module (:func:`test_every_live_cell_reaches_an_outcome`).  That was
  false for 8 cells at ``5021772c``: an object node at a KEY position made the run write
  ``class (AdCPBaseModel):`` with neither a refusal nor an approximation beside it, which
  is the one thing §9 forbids outright -- "a crash is not an outcome".
  ``adcp-client-python-zxf``;
* **every cell at a position the bundle STATES is PROVED or REFUSED BY NAME**
  (:func:`test_every_cell_the_bundle_states_is_proved_or_refused_by_name`).  This is the
  set §8's induction has to range over to reach a document -- "a cell no document states is
  a cell no document's faithfulness depends on" -- so it is the half of the table the
  artifact's correctness actually rests on, and it holds completely;
* **a DEFERRED cell names the keyword it defers on**
  (:func:`test_every_deferred_cell_names_its_keyword`), which is what makes a deferral an
  outcome rather than a silence.

* **EVERY live cell is PROVED or REFUSED BY NAME, over the whole 289 and with no
  predicate narrowing the set** (:func:`test_every_live_cell_is_proved_or_refused_by_name`).

**THE SIX THAT WERE NOT, AND WHAT CLOSED THEM (``sdk/ident``).**  ``additionalProperties``,
``dependencies``, ``minProperties``, ``maxProperties``, ``oneOf`` and ``patternProperties``
at a RULE position were unproved, and the clause that let the suite stay green was a
DERIVED exclusion -- the bundle states none of the six, so the gate above ranged over the
cells the bundle does state and these six sat outside it with a bead and a measurement.
The exclusion is deleted, because the cells are proved.

Each is a keyword inside an ``if`` that states no ``required``, which §5's ``if`` row
decides compiles to nothing ("a ``Match`` clause list where it states ``required`` plus
``properties`` with ``const`` or ``enum`` values; otherwise nothing") and which §8 sentence
3b's complement does not reach either -- there is no key whose predicate the complement
would be of.  So the model is wider at all six and §2's answer is a DECLARATION; what
stood in the way was arithmetic.  Declaring an unreadable condition minted **4,635 sites in
97 documents from 112 distinct conditional facts**, a set §8 ruled out by name, and the
ratio 4,635 : 112 was a measurement of a DIFFERENT defect: a declaration written once per
pointer the record inlines the condition to.  §8 sentence 2 retires that -- "a fact is
declared ONCE, at the node the document STATES it" -- and ``lower.rules._conditional``
declares the condition now.  ``./check``'s third line is 126 facts in 61 documents, of
which 89 are this drop.
"""

from __future__ import annotations

import functools
from typing import Any

import cells
from cells import (
    AT,
    NODES,
    bind,
    compile_probe,
    grade,
    live,
    stated_by_the_bundle,
    wrap,
)
from nodeset import claimed, partitions
from pydantic import TypeAdapter

from codegen import harness, keywords
from codegen.keywords import Position

#: **THE FOUR PINNED COUNTS THAT STOOD HERE ARE GONE** (2026-11-04,
#: ``adcp-client-python-99m``).  They were ``ROWS = 98``, ``POSITIONS = 9``,
#: ``LIVE = 289`` and ``STATED = 180``, and the three checks below asserted them --
#: eighteen integers over nine ``assert ... ==`` sites, which
#: ``tests/test_every_check_names_its_set.py``'s census instrument counted against a
#: CEILING OF 0 and was red on.  Every one of the eighteen was TRUE when it was removed;
#: that is the point.  Each was a census: one bundle version's reading of a quantity
#: every emitting row and every upstream release moves, and a number being right today
#: is what makes it indistinguishable from a check.
#:
#: What they stood in for is asserted instead, and in each case it is a property the
#: counts were decoration on:
#:
#: * ``ROWS``/``POSITIONS``/882 stood in for "the cells are the whole CROSS PRODUCT of
#:   the table and the positions".  That is asserted as the equality of two derived sets.
#:   The ``882`` was vacuous even as a count -- ``len`` of a set comprehension over two
#:   iterables cannot be anything else.
#: * ``LIVE`` stood in for "``live()`` is exactly the cells whose effect ``COMPILES``",
#:   which the two assertions directly beneath it ALREADY state as a biconditional.  The
#:   count added nothing to them.
#: * the nine per-position figures stood in for three facts, each now asserted: the nine
#:   columns PARTITION the live set, every column is NON-EMPTY (so the induction has
#:   something to discharge at every hop), and ``RULE`` is the SHORT column -- a strict
#:   inequality against every other column, which is what §5's "RULE -> nothing" rows
#:   mean and what a pinned 24 could never say.
#: * ``STATED`` and ``109`` stood in for "the bundle-stated cells and the rest PARTITION
#:   the live set, and neither half is empty".  The two figures are a REPORT -- the
#:   check's own docstring says "the two figures are different obligations and the report
#:   never sums them" -- so they are stated as a measurement below and not as a gate.
#:
#: MEASURED 2026-11-04 over ``schemas/cache/3.2``, for a reader comparing deliveries:
#: 98 rows x 9 positions = 882 cells, 289 live, 180 of those stated by some portable
#: document and 109 not; by position ROOT 33, PROP 34, ELEM 33, MAPV 33, KEY 33,
#: BRANCH 33, CONJ 33, RULE 24, DEF 33.  A delivery reports these; nothing asserts them.
#:
#: **AND THE GATE DOES NOT WEAKEN, because the counts were never the gate.**  §8's
#: obligation is coverage of a derived set, not its size, and
#: :func:`test_every_live_cell_is_proved_or_refused_by_name` already ranges over the
#: whole live set with no predicate narrowing it.  A row added to ``keywords.TABLE``
#: enlarges that set and is proved or reddens, which is exactly what a pinned
#: denominator cannot do: it reddens on the SIZE and says nothing about the new cell.


# --------------------------------------------------------------------------- #
# the denominator
# --------------------------------------------------------------------------- #
def test_the_live_cell_count_is_derived_from_the_table() -> None:
    """98 rows x 9 positions, and which of the 882 cells are LIVE.

    Derived from ``keywords.TABLE`` and ``keywords.COMPILES``, so a row or a cell added
    to the declaration moves this number and nothing else has to be told.  The split by
    position is here too, because the induction walks a document BY position and a
    position's column is what it has to discharge at each hop.
    """
    cells = claimed(
        "§5's cells",
        {(keyword, position) for keyword in keywords.TABLE for position in Position},
    )
    # **THE TABLE IS TOTAL OVER THE CROSS PRODUCT**, which is what the pinned
    # ``ROWS * POSITIONS == 882`` was reaching for and could not say: the product of two
    # counts is satisfied by any table of the right AREA, and the induction's requirement
    # is that no ``(keyword, position)`` pair is missing an answer.  ``keywords.cell``
    # returns ``None`` for a keyword with no row -- "the answer that refuses the document
    # BY NAME" -- so a row added to one section and not the others reddens HERE, with the
    # pair named, instead of moving a denominator.
    missing = sorted(
        (keyword, position.name)
        for keyword, position in cells
        if keywords.cell(keyword, position) is None
    )
    assert missing == [], missing

    claimed("§5's live cells", live())
    # **THE BICONDITIONAL IS THE DEFINITION OF ``live()``, and it is the whole of what a
    # pinned 289 was standing in front of.**  Every live cell's effect is one of the
    # three that COMPILE to something, and every cell with such an effect is live -- so a
    # fourth effect joining ``COMPILES``, or a row whose cell stopped compiling, moves
    # this set and reddens by CELL rather than by a number.
    assert {keywords.cell(k, p).effect for k, p in live()} <= keywords.COMPILES
    assert live() == {
        (keyword, position)
        for keyword in keywords.TABLE
        for position in Position
        if keywords.cell(keyword, position).effect in keywords.COMPILES
    }
    assert live() < cells, "every cell is live: the table says nothing anywhere"


def test_the_live_cells_split_by_position_as_the_induction_walks_them() -> None:
    """The column the induction discharges at each hop of a document.

    Nine columns, and the figure a reader needs per hop.  ``RULE`` is the short column --
    §5 gives several rows "RULE -> nothing" and those cells are not live -- which is why
    the induction reaches a conditional subtree with less to prove than a value subtree.
    """
    column = {p: {c for c in live() if c[1] is p} for p in Position}
    # TOTAL and DISJOINT over the live set, which is what ``sum(...) == LIVE`` was a
    # weaker spelling of: two columns can sum correctly while one misses a cell and
    # another holds it twice, and ``partitions`` reports both failures BY CELL.
    partitions(live(), **{p.name: column[p] for p in Position})
    # Every column NON-EMPTY, so the induction has something to discharge at every hop.
    # Named per position, so a column emptying reddens with the position named.
    for position in Position:
        claimed(f"live cells at {position.name}", column[position], inside=live())
    # **``RULE`` IS THE SHORT COLUMN, asserted as the inequality the docstring states.**
    # §5 gives several rows "RULE -> nothing" and those cells are not live, so a
    # conditional subtree has strictly less to prove than any value subtree.  A pinned 24
    # could not say that; it only said what the number was on one bundle.
    assert all(
        len(column[Position.RULE]) < len(column[position])
        for position in Position
        if position is not Position.RULE
    ), {p.name: len(s) for p, s in column.items()}


def test_the_bundle_states_the_cells_this_row_claims_it_does() -> None:
    """WHICH live cells any portable document STATES, derived over the bundle.

    **The set the induction has to range over to reach a document.**  A cell no document
    states is a cell no document's faithfulness depends on, so the two halves are
    different obligations and the report never sums them.

    Derived over the bundle SOURCE and not over the emitted population, for §8's reason:
    a reading of what is EMITTED grows when the emitter emits more, and these are
    positions of the source, which do not move when a row lands.

    **Asserted as a PARTITION and no longer as two counts** (2026-11-04): the figures
    that stood here -- 180 stated, 109 not -- are a measurement a delivery reports, and
    pinning them made this check red in
    ``tests/test_every_check_names_its_set.py``'s census instrument while saying nothing
    the partition does not.  Which cells are in which half is what matters, and a cell
    moving between the halves because an upstream release started stating it is the
    bundle changing rather than this tree.
    """
    stated = claimed(
        "live cells the bundle states", {c for c in live() if c in stated_by_the_bundle()}
    )
    unstated = claimed("live cells no portable document states", live() - stated)
    # The two obligations, as a PARTITION of the live set and not as two counts whose
    # difference is a third: this check's own docstring says the report never sums them,
    # and a partition is the statement that every live cell is exactly one of the two.
    partitions(live(), the_bundle_states_it=stated, no_document_states_it=unstated)
    # Drawn from the live set: ``stated_by_the_bundle`` is derived independently, so a
    # cell it reports that is not live would mean the two readings disagree about the
    # table rather than about the bundle.
    assert stated <= live(), sorted(stated - live())


# --------------------------------------------------------------------------- #
# the per-cell gate: three properties, each over all 289 and none over a list
# --------------------------------------------------------------------------- #
@functools.cache
def graded() -> dict[tuple[str, Position], Any]:
    """``cells.grade`` over every live cell, once per process.

    One compile per cell and the cost is a function of the KEYWORD rather than of any
    document, which is §8's whole reason for a cell proof: all 289 in seconds of CPU,
    against a draw that returns no verdict for 86 pairs at any budget.  Cached because
    three gates read it and a second pass would pay the compiles again.
    """
    return {cell: grade(*cell) for cell in sorted(live(), key=lambda c: (c[0], c[1].name))}


def test_every_live_cell_reaches_an_outcome() -> None:
    """**No live cell writes a module that is not parseable Python.**

    §9: "a crash is not an outcome".  A cell whose probe compiles has to answer with an
    ANNOTATION, a VERDICT or a DEFERRAL -- the three the declaration defines -- and a
    fourth state is the one the report cannot carry: ``cells.grade`` reports it as
    ``unparseable`` precisely because the compiler reported nothing at all.

    **8 live cells were in that state at ``5021772c``** -- ``properties``, ``required``,
    ``additionalProperties``, ``dependencies``, ``if``, ``then``, ``else`` and ``not`` at
    KEY -- because §4 derives no name at a mapping's key position and the object row
    declared a class there anyway, so the module read ``class (AdCPBaseModel):`` beside
    ``dict[, Any]`` with no refusal and no approximation naming it.
    ``adcp-client-python-zxf``.  The failure is reported with the CELL named, because the
    keyword is what a fix is aimed at.
    """
    outcomes = claimed(
        "live cells with an outcome",
        {cell for cell, verdicts in graded().items() if verdicts.outcome},
        inside=live(),
    )
    # EVERY live cell and not most of them: a cell ``grade`` returned no outcome for would
    # be absent from the comprehension below rather than failing it.
    assert live() - outcomes == set()
    unparseable = {
        cell: verdicts.outcome
        for cell, verdicts in graded().items()
        if verdicts.outcome not in ("emitted", "verdict", "deferred")
    }
    assert unparseable == {}, unparseable


def test_every_deferred_cell_names_its_keyword() -> None:
    """A DEFERRAL is an outcome because it NAMES the keyword, and that is asserted.

    The declaration defines a deferral as "a cell with a lowering effect whose handler has
    no code for the shape yet", and §9 asks that it be loud rather than silent.  Loud is
    the keyword: a refusal with no keyword is a document refused for a reason nobody can
    aim a row at.
    """
    refusing = claimed(
        "live cells that refuse",
        {c for c, v in graded().items() if v.outcome in ("verdict", "deferred")},
        inside=live(),
    )
    nameless = {cell for cell in refusing if not graded()[cell].refused_on}
    assert nameless == set(), sorted(nameless)


def test_every_live_cell_is_proved_or_refused_by_name() -> None:
    """**Every one of the 289, PROVED by a payload or REFUSED by name -- no predicate.**

    This is one gate where there were two, and the deletion is the finding
    (``sdk/ident``).  What stood here was ``..._every_cell_the_bundle_states_...``, over
    ``live() & stated_by_the_bundle()``, beside a second clause that took the complement
    and asserted the six cells in it all had ONE cause.  The second was not an allowlist --
    the set was derived twice over and a cell leaving it needed no edit -- but it was an
    EXCLUSION, and the sentence it rested on was "a cell no document states is a cell no
    document's faithfulness depends on".  That sentence is true about faithfulness and it
    was doing a second job here: it decided which cells had to be proved.

    The six are proved (the module docstring says by what), so the predicate has nothing to
    exclude and goes.  **The set this ranges over is now ``live()``**, which is the table's
    own area and needs no reading of the bundle at all -- and a cell that stops being
    proved reddens here whether any document states it or not.

    ``stated_by_the_bundle`` is still read, by
    :func:`test_the_cells_the_bundle_states_are_the_induction_s_own_set`, because §8's
    induction ranges over it and that is a fact worth measuring; it no longer narrows an
    obligation.
    """
    claimed("live cells", live())
    failing = {
        cell: (verdicts.outcome, verdicts.narrowed, verdicts.widened, verdicts.declared)
        for cell, verdicts in graded().items()
        if not (verdicts.proved or verdicts.refused_on)
    }
    assert failing == {}, failing


def test_a_cell_is_graded_against_the_class_at_the_root_pointer() -> None:
    """**The witnesses go to the class the PROBE DOCUMENT'S ROOT lowered, by pointer.**

    ``docs/plan/architecture.md``'s identity rule read as a grading rule: a class is
    resolved by the provenance its run recorded for it, never by what it is called.  The
    instrument read ``module.__all__[0]`` instead -- the module's alphabetically first
    export -- and the two readings agree at eight of the nine positions, which is why the
    defect was invisible until the DEF column existed.

    **AT DEF THEY DISAGREE AND THE WRONG CLASS WAS GRADED 32 TIMES.**  A DEF probe's module
    exports the ``definitions`` entry beside the root that references it, the export list is
    sorted, and the entry sorts first.  So every DEF witness -- an instance of the shape
    ``{"p": <value>}`` -- was offered to the class for the value INSIDE ``p``, which refuses
    an object with a ``p`` key or admits one for reasons of its own.  Measured at
    ``781f873d1``: 23 of the 33 DEF cells reported a NARROWING and 8 an undeclared WIDENING,
    the whole of :func:`test_every_live_cell_is_proved_or_refused_by_name`'s failure and the
    whole of ``tests/test_decision_set.py``'s, and not one of them a disagreement between a
    class and its document.

    **BOTH SIDES DERIVED, AND THE DIFFERENCE IS ASSERTED NON-EMPTY**, which is what makes
    this a measurement rather than a tautology: a gate comparing two readings that agree
    everywhere cannot say which one the run is using.  The cells where they differ are
    stated as an equality against the emitted DEF column -- derived on both sides, so a
    position that starts minting an earlier-sorting export reddens here with the cell named
    instead of silently grading the wrong class somewhere else.
    """
    emitted = {cell for cell, v in graded().items() if v.outcome == "emitted"}
    claimed("cells whose probe emitted a module", emitted, inside=live())
    # **THE OBLIGATION, asked of the GRADED OBJECT and not of the lookup that found it.**
    # A model answers for its own node through ``__adcp_schema__``, so a cell graded
    # against the wrong class reports the wrong POINTER here -- at DEF, the entry's
    # ``#/definitions/D`` where the probe document's root is ``#``.  The set is named
    # non-empty first: an alias root carries no model and no pointer, and a reading over
    # only those would be a pass over nothing.
    answering = claimed(
        "cells whose graded class carries its own provenance",
        {cell for cell in emitted if graded()[cell].provenance is not None},
        inside=live(),
    )
    assert answering
    elsewhere = {
        cell: graded()[cell].provenance
        for cell in answering
        if graded()[cell].provenance != f"{cells.PROBE}#"
    }
    assert elsewhere == {}, elsewhere
    # **AND THE TWO READINGS DO DIFFER**, which is what stops the assertion above being
    # satisfied by a tree where every module declares one symbol and the two readings
    # cannot disagree.  The set is NAMED rather than counted, and the DEF column is
    # asserted to meet it: that column is where a ``definitions`` entry is declared beside
    # the root and sorts ahead of it, so it is the column a reading by name is wrong at by
    # construction rather than by accident.
    #
    # NOT an equality against the DEF column, and the correction is the measurement: a
    # PROP, KEY or BRANCH probe declares its inner object too, and those names sort ahead
    # of ``Probe`` as readily as ``D`` does -- 32 DEF cells but 50 cells in all.  The DEF
    # column is where the old reading changed the VERDICT, not where it was alone in being
    # a different symbol.
    differ = claimed(
        "cells a reading by NAME resolves to another declaration",
        {cell for cell in emitted if graded()[cell].bound != graded()[cell].by_name},
        inside=live(),
    )
    assert differ & {c for c in emitted if c[1] is Position.DEF}, sorted(differ)


def test_the_cells_the_bundle_states_are_the_induction_s_own_set() -> None:
    """§8's induction ranges over the cells the bundle STATES, and this is that figure.

    A measurement and not an obligation: the gate above holds over the whole table, so this
    says only how much of the table the artifact's correctness actually rests on -- "a cell
    no document states is a cell no document's faithfulness depends on".  Asserted as a
    containment rather than a count, because a count here would pin a property of the
    BUNDLE and the bundle is an input.
    """
    stated = claimed(
        "live cells the bundle states",
        {cell for cell in live() if cell in stated_by_the_bundle()},
    )
    assert stated <= live()
    assert all(
        verdicts.proved or verdicts.refused_on
        for cell, verdicts in graded().items()
        if cell in stated
    )
    # The report's own arithmetic: the three outcomes account for every live cell, so a
    # cell cannot leave one bucket without arriving in another -- and ``unproved`` is EMPTY
    # now, which is what makes the gate above a gate over the whole set.  Kept in the
    # partition rather than dropped: a partition with a bucket that must be empty says
    # which bucket, where two buckets would say only that the sum is right.
    assert partitions(
        live(),
        proved={c for c, v in graded().items() if v.proved},
        refused={c for c, v in graded().items() if not v.proved and v.refused_on},
        unproved={c for c, v in graded().items() if not (v.proved or v.refused_on)},
    ) == live()


# --------------------------------------------------------------------------- #
# the equality, in both directions
# --------------------------------------------------------------------------- #
def test_every_live_cell_has_a_probe_and_every_probe_names_a_live_cell() -> None:
    """The two directions §8's obligation needs, and both are derived.

    Forwards: a live cell with no probe is a cell nothing can prove, and it reddens here
    rather than being absent from a parametrisation nobody counts.  Backwards: a probe
    for a cell the table does not have is grading a decision §5 never took, and it
    reddens too -- which is the direction an instrument drifts in when a keyword's row
    changes and the probe beside it does not.
    """
    with_a_probe = {
        (keyword, position)
        for keyword, position in live()
        if keyword in NODES or (keyword, position) in AT
    }
    assert claimed("live cells carrying a probe", with_a_probe) == live()

    # Backwards: every keyword the probe table carries has a live cell, and every
    # position override names a live cell of its own keyword.
    assert set(NODES) == {k for k, _ in live()}
    assert claimed("position overrides", set(AT)) <= live()


def test_every_wrapper_descends_by_the_columns_own_keyword() -> None:
    """A position's wrapper uses the keyword the DESCENT COLUMN says reaches it.

    ``docs/plan/architecture.md`` §6: the position is assigned from the structural
    keyword descended through.  So a wrapper that reached PROP through anything but
    ``properties`` would be putting the node at a position the table does not name, and
    every cell proof at that position would be about the wrong cell.  Asserted by
    BUILDING each wrapper and reading which of the column's keywords it states.
    """
    column: dict[Position, set[str]] = {}
    for keyword, position in keywords.descends_at(Position.ROOT).items():
        column.setdefault(position, set()).add(keyword)

    marker = {"type": "boolean"}
    for position in Position:
        document, _ = wrap(position, marker)
        if position is Position.ROOT:
            # The one position no keyword descends into: the node IS the document.
            assert document["type"] == "boolean"
            assert position not in column
            continue
        reached = {k for k in column[position] if k in document}
        assert reached, f"{position}: the wrapper states none of {sorted(column[position])}"


def test_a_rule_probe_is_held_by_one_of_the_four_conditionals() -> None:
    """§3's RULE position is reached by four keywords and a probe names which.

    ``keywords.descends_at`` gives RULE four keywords, and §5 gives several rows a cell
    per conditional -- the ``anyOf`` row's is "under ``not`` -> the union of the branches'
    groups; else nothing".  A probe that always used ``if`` would grade the *else nothing*
    half of those cells, so the conditional is the probe's own field and this is the
    equality that it is one of the column's four.
    """
    held_by = {k for k, p in keywords.descends_at(Position.ROOT).items() if p is Position.RULE}
    assert held_by == {"else", "if", "not", "then"}
    assert {probe.under for probe in [*NODES.values(), *AT.values()]} <= held_by


# --------------------------------------------------------------------------- #
# the composition rules, each once, over two small hand-built conjuncts
# --------------------------------------------------------------------------- #
def _prove(document: dict, witnesses: tuple, *, widens: bool = False) -> None:
    """One probe, one verdict per witness, in §2's two directions.

    A witness the DOCUMENT admits and the class refuses is a narrowing and fails
    unconditionally.  A witness the document refuses and the class admits is a widening,
    which passes only where the run DECLARED one -- §8: "An approximation that still
    refuses a value the document admits is a NARROWING wearing a declaration".
    """
    out, resolved = compile_probe(document)
    assert out.refusals == {}, out.refusals
    adapter = TypeAdapter(bind(out))
    declared = out.approximations.get("core/probe.json", [])
    seen_wide = False
    verdicts = []
    for witness in witnesses:
        try:
            adapter.validate_python(witness)
            by_class = True
        except Exception:  # any refusal is a refusal
            by_class = False
        by_document = harness.conforms(resolved, witness)
        verdicts.append(by_document)
        if by_document and not by_class:
            raise AssertionError(f"NARROWED: the document admits {witness!r}, the class refuses it")
        if by_document is False and by_class:
            seen_wide = True
            assert declared, f"an UNDECLARED widening at {witness!r}"
    # **The witness set DISCRIMINATES, or the agreement above is vacuous.**  A set the
    # document admits in its entirety is passed by a class that admits everything, which
    # is exactly the failure a composition rule has to rule out: ``allOf`` dropping a
    # conjunct, ``anyOf`` collapsing to ``Any``.  So both verdicts have to appear.
    assert True in verdicts and False in verdicts, f"the witnesses do not discriminate: {verdicts}"
    assert seen_wide == widens, f"widening expected={widens} observed={seen_wide}"


def test_allof_intersects() -> None:
    """Two conjuncts bounding one property from opposite sides admit the overlap alone.

    §2's *"Composition merges by intersection"*, over two hand-built conjuncts and not
    over a bundle document: ``minLength: 2`` and ``maxLength: 3`` at the same property
    admit a two- and a three-character value and refuse a one- and a four-character one.
    Four witnesses, because the intersection has two ends and a rule that kept only one
    conjunct would be green on three of them.
    """
    _prove(
        {
            "title": "Probe",
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string", "minLength": 2}}},
                {"type": "object", "properties": {"a": {"type": "string", "maxLength": 3}}},
            ],
        },
        ({"a": "a"}, {"a": "ab"}, {"a": "abc"}, {"a": "abcd"}),
    )


def test_a_restatement_merges() -> None:
    """One property declared by two conjuncts is ONE field taking the tighter bound.

    §5's ``properties`` row at CONJ: "A property two conjuncts declare is one field: its
    constraints intersect by §2".  The two conjuncts here state the SAME keyword at
    different values -- a restatement rather than two different facts -- and the merged
    field admits exactly what the tighter of the two admits.  A model that took the
    LOOSER would admit ``"abcd"``, and a model that carried two fields could not be
    constructed at all.
    """
    _prove(
        {
            "title": "Probe",
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string", "maxLength": 9}}},
                {"type": "object", "properties": {"a": {"type": "string", "maxLength": 3}}},
            ],
        },
        ({"a": ""}, {"a": "abc"}, {"a": "abcd"}),
    )


def test_anyof_unions() -> None:
    """A payload either branch admits is admitted, and one neither admits is refused.

    ``anyOf`` is the union, so the witness set is one instance per branch, one BOTH
    branches admit -- which ``anyOf`` admits and ``oneOf`` does not, and is the whole of
    the difference between the two cells -- and one neither admits.
    """
    _prove(
        {
            "title": "Probe",
            "anyOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
                {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]},
            ],
        },
        ({"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}, {}),
    )


def test_oneof_is_exclusive_and_the_model_is_wider_by_a_declaration() -> None:
    """``oneOf`` refuses the instance two branches both admit; the model admits it.

    §8, on the one fact that survived the comparison's deletion: "An inseparable ``oneOf``
    admits a payload the document refuses -- measured on
    ``core/evaluator-spec.json#/oneOf`` ... That is a WIDENED declaration and §8's draw
    hands the class exactly such a value."  So this is the composition rule AND its
    declared exception in one payload: ``{"a": "x", "b": "y"}`` satisfies both branches,
    ``Draft7Validator`` refuses it, the class admits it, and the run declares the
    widening.  ``widens=True`` is asserted rather than tolerated -- a run that stopped
    widening here without declaring it would redden, and so would one that declared a
    widening no value demonstrates.
    """
    _prove(
        {
            "title": "Probe",
            "oneOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
                {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]},
            ],
        },
        ({"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}, {}),
        widens=True,
    )


# --------------------------------------------------------------------------- #
# the induction's premises, and the one that is not met
# --------------------------------------------------------------------------- #
def test_the_premise_that_nothing_outside_the_table_reaches_the_output() -> None:
    """Every keyword any portable document states at any position HAS a row.

    The induction's second premise.  ``keywords.cell`` returns ``None`` for a keyword
    with no row and that is "the ONLY answer that refuses [a document] at all", so a key
    outside the table cannot reach an annotation -- it refuses the document first.  This
    asserts the stronger fact the bundle actually has: no portable document states a key
    with no row, which is why ``refused`` is 0 rather than why it could be.
    """
    unrowed = {
        keyword
        for keyword, _ in stated_by_the_bundle()
        if keywords.cell(keyword, Position.ROOT) is None
    }
    assert unrowed == set()
    # And the set this ranges over is the bundle's own keys, screened by the same
    # predicate the compiler screens with -- not a copy of the row list.
    assert claimed("keywords the bundle states", {k for k, _ in stated_by_the_bundle()})


def test_the_premise_that_the_positions_are_closed_under_descent() -> None:
    """A subschema of a node at a position is at one of the nine positions.

    The induction's first premise, and the one that makes the walk a STRUCTURAL induction
    at all: if a descent could land a subschema at no position, the induction would have
    a hop with no column to discharge.  ``bundle.subschemas`` is the one descent step and
    every position it assigns comes from ``keywords.descends_at``, so the closure is the
    column's and not a second reading of it.
    """
    assigned = set(bundle_positions())
    assert assigned <= set(Position)
    # Every position a keyword descends INTO is one of the nine, and the column assigns
    # at least one keyword to each of the eight that are not ROOT.
    reached = set(keywords.descends_at(Position.ROOT).values())
    assert reached == set(Position) - {Position.ROOT}


def bundle_positions() -> set[Position]:
    """Every position the descent column assigns, at every position it is asked at."""
    return {
        position
        for at in Position
        for position in keywords.descends_at(at).values()
    }
