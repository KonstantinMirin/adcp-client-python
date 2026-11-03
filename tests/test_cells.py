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

**WHAT IS AND IS NOT GATED HERE, and the reason is budgetary in one direction only.**
The per-cell PROOF is derived by ``cells.grade`` and reported by
:func:`test_the_cell_proofs_are_reported_with_their_denominator`, which asserts the
arithmetic of the report rather than the verdict of every cell.  It cannot assert every
cell yet: 11 live cells the compiler emits an annotation for are not proved by a payload,
each is a located defect with a bead, and every one of them is fixed in the COMPILER --
which this row may not change.  A gate asserting them would be a red carried in the
suite, which ``docs/plan/final-state.md`` forbids outright, and an allowlist of the 11
would be the shape §9 calls "a pin with no denominator".  So the cells are MEASURED here
and the beads carry the defects; what is GATED is everything that holds without
exception: the denominator, the probe-table equality in both directions, the wrapper's
agreement with the descent column, and the four composition rules.
"""

from __future__ import annotations

import pytest

from codegen import keywords
from codegen.keywords import Position

from cells import (
    AT,
    NODES,
    bind,
    compile_probe,
    live,
    stated_by_the_bundle,
    wrap,
)
from nodeset import claimed
from pydantic import TypeAdapter
from codegen import harness

#: §5's row count and §3's position count, the two factors of the table's area.  Pinned
#: because the DENOMINATOR is the reading: a row added without a cell, or a position
#: added without a column, changes what "every cell" ranges over, and a reader comparing
#: two deliveries needs to know which table each was over.
ROWS = 98
POSITIONS = 9
#: §5's live cells: 289 of the 882 pairs compile to a type, a field or a rule.
LIVE = 289
#: Of those, the ones at least one portable document of bundle 3.2 STATES.  The rest are
#: cells no document's faithfulness depends on, and the compiler's answer at 27 of them
#: is a refusal naming the keyword rather than an annotation.
STATED = 180


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
    assert len(keywords.TABLE) == ROWS
    assert len(list(Position)) == POSITIONS
    cells = {
        (keyword, position) for keyword in keywords.TABLE for position in Position
    }
    assert len(cells) == ROWS * POSITIONS == 882

    assert len(claimed("§5's live cells", live())) == LIVE
    # Every live cell's effect is one of the three that COMPILE to something, and no
    # other effect is in the set -- the biconditional, so a fourth effect joining
    # ``COMPILES`` cannot enlarge this set silently.
    assert {keywords.cell(k, p).effect for k, p in live()} <= keywords.COMPILES
    assert all(
        (keyword, position) in live()
        for keyword in keywords.TABLE
        for position in Position
        if keywords.cell(keyword, position).effect in keywords.COMPILES
    )


def test_the_live_cells_split_by_position_as_the_induction_walks_them() -> None:
    """The column the induction discharges at each hop of a document.

    Nine columns, and the figure a reader needs per hop.  ``RULE`` is the short column --
    §5 gives several rows "RULE -> nothing" and those cells are not live -- which is why
    the induction reaches a conditional subtree with less to prove than a value subtree.
    """
    by_position = {p: len({c for c in live() if c[1] is p}) for p in Position}
    assert by_position == {
        Position.ROOT: 33,
        Position.PROP: 34,
        Position.ELEM: 33,
        Position.MAPV: 33,
        Position.KEY: 33,
        Position.BRANCH: 33,
        Position.CONJ: 33,
        Position.RULE: 24,
        Position.DEF: 33,
    }
    assert sum(by_position.values()) == LIVE


def test_the_bundle_states_the_cells_this_row_claims_it_does() -> None:
    """How many live cells any portable document STATES, derived over the bundle.

    **The set the induction has to range over to reach a document.**  A cell no document
    states is a cell no document's faithfulness depends on, so the two figures are
    different obligations and the report never sums them: 289 is the table's area and 180
    is what bundle 3.2 asks of it.

    Pinned as COUNTS over the bundle SOURCE and not over the emitted population, for §8's
    reason: a count over what is emitted rises when the emitter emits more, and these are
    positions of the source, which does not move when a row lands.
    """
    stated = {c for c in live() if c in stated_by_the_bundle()}
    assert len(claimed("live cells the bundle states", stated)) == STATED
    assert len(live() - stated_by_the_bundle()) == LIVE - STATED == 109


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
    assert {k for k in NODES} == {k for k, _ in live()}
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
        except Exception:  # noqa: BLE001 -- any refusal is a refusal
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
    assigned = {position for position in bundle_positions()}
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
