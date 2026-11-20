"""The five rule tables, and the one assertion that a difference between them is STATED.

``codegen/keywords.py`` is the declaration: one cell per keyword per position, 105
keywords over 9 positions.  Four other tables project it, and each one is read on a
DIFFERENT PATH through the compiler:

| table                       | file                     | keyed by                 |
|-----------------------------|--------------------------|--------------------------|
| ``Effect`` per ``Position`` | ``codegen/keywords.py``  | keyword x position       |
| ``DESCENDS``                | ``codegen/bundle.py``    | keyword (read at ROOT)   |
| ``RENDERED``                | ``codegen/intersect.py`` | keyword, at PROP         |
| ``SPELLING``                | ``codegen/constraints.py``| keyword                 |
| ``FORMAT_TYPES``            | ``codegen/lower/scalars.py``| a ``format`` VALUE    |

**THE DEFECT CLASS THIS FILE EXISTS FOR, and it is not a hypothetical.**
``intersect.RENDERED`` was the literal ``("default", "description")`` and ``deprecated``
was missing from it, so a ``deprecated: true`` the document states was dropped wherever a
field was reached through a reference: **21 fields on 11 classes**, ten of them
``adcp_major_version`` on a request root, where ``core/version-envelope.json`` states
``{"deprecated": true, "x-removed-in": "4.0.0"}`` -- a buyer reading
``ListProductsRequest``'s field metadata was not told the field is removed in 4.0.
Fixed at ``79965885f``; the exposure is ``adcp-client-python-ahbe`` and is what this
grades.

**NOTHING COUNTED IT, AND THAT IS THE EXPOSURE RATHER THAN THE BUG.** A keyword honoured
on the direct path and dropped on the intersection path moves no counter:
``states_a_fact(ANNOTATION)`` is ``False``, so there is no rung for
:func:`codegen.lower.approximate.approximate` to record and ``./check``'s ``approximated``
cannot move; ``Cell.reported`` is ``False``, so ``carries_nothing`` holds nothing either.
Both of §10's two channels are silent by construction and the drop is UNDECLARED.

**AND THE ONE INSTRUMENT THAT READS KEYWORD LITERALS COULD NOT SEE IT.**
``survey.arch_audit.keyword_collections`` -- §3's census, gated by
``tests/test_keywords.py`` -- names 19 literal keyword collections outside
``codegen/keywords.py``, and NONE of the five tables is among them.  Measured:

* ``RENDERED``'s three entries include two of the census's ``DRAFT07`` names and its
  ``FLOOR`` is **three**, so the site was one keyword short of visible;
* ``SPELLING``'s eight entries include ``multipleOf``, which the census's own
  ``DRAFT07`` set omits, so its ``len(hits) == len(vals)`` clause rejects the site;
* ``FORMAT_TYPES`` is keyed by a ``format`` VALUE and holds no keyword at all;
* ``DESCENDS`` is a derivation and not a literal.

So a census of SITES cannot grade this, which is why what follows grades CONTENTS.

## What "agree" means here, because it is not set equality

``RENDERED`` is deliberately a SUBSET of what ``Effect`` renders, and three of the four
projections are proper subsets of their domain.  Equality would be the wrong assertion and
a snapshot of today's membership would be the wrong one too -- it goes green again the
moment someone updates it, which is exactly what a drifting literal does.  So the
assertion is: **each projection equals a DERIVATION of the declaration, and every
difference from that derivation is a declared entry carrying its reason.**
:data:`STATED` is that declaration.  Three consequences, and they are the point:

* a keyword that ENTERS a domain -- a new rendered annotation, a new bound, a new
  asserted format -- is in the derivation and not in the projection, and reddens here;
* a difference that is DELIBERATE costs one :data:`STATED` entry and a sentence, which is
  the cost the ``deprecated`` drop never paid;
* a :data:`STATED` entry that stops differing reddens too
  (:func:`test_no_stated_difference_is_stale`), so the list shrinks when a repair lands
  and cannot accumulate dead rows.

## The differences this file found, which are LIVE and declared rather than fixed

Both are outside this lane's write scope and are reported on ``adcp-client-python-ahbe``:

1. **``deprecated`` at ROOT and at BRANCH renders nothing, where §6 says it renders into
   the class.** ``docs/plan/rebuild-plan.md`` §6's own line -- which
   ``tests/test_keywords.py`` GENERATES from this cell's prose -- reads "ROOT / BRANCH ->
   the class's ``json_schema_extra``", and the cell beside that sentence is
   ``rendered=False``.  Measured: no class-level ``json_schema_extra`` is emitted anywhere
   in the tree, and the bundle states ``deprecated`` at **27 document roots** and **278
   BRANCH nodes** -- ``core/format.json`` among them, the document ``CLAUDE.md`` singles
   out as ``deprecated: true`` as a whole, whose class says nothing about it.  The repair
   is in ``codegen/render.py``, which a sibling lane owns this cycle.
2. **The compiler's asserted-format set and the SDK runtime's differ by three.**
   ``emit.asserted_formats``'s docstring claims "the set this walk gates on and the set
   the runtime enforces are one set and cannot drift".  Measured: it has drifted by
   ``hostname``, ``uri-template`` and ``uuid`` -- the compiler reads the DOCUMENT'S draft
   (``validator_for(doc).FORMAT_CHECKER``, 13 checkers installed) and
   ``adcp.validation.schema_loader._build_format_checker`` builds the GLOBAL
   ``FormatChecker()`` (16).  All three are stated by the bundle, so at those nodes the
   model accepts what the bundled schema refuses, which is the shape the ``format: email``
   defect had at 100 divergences.  Which side moves is the owner's call and is not this
   table's to take; ``79965885f`` named ``uuid`` and the other two are this audit's.
"""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Any, NamedTuple

import fresh

from codegen import bundle, emit, intersect, ir, keywords, render
from codegen.constraints import CONTAINER_SPELLING, SPELLING
from codegen.keywords import Effect, Position
from codegen.lower.scalars import FORMAT_TYPES

#: The bundle a run reads, from the ONE declaration of it (``fresh.BUNDLE``) and not a
#: literal, for ``tests_emit/test_reported_drop.py``'s measured reason: a module holding
#: its own PUBLISHED path grades a document set the emitted classes did not come from.
BUNDLE = Path(fresh.BUNDLE)

#: The grids whose keywords constrain a SCALAR, and the ones whose keywords constrain a
#: CONTAINER.  ``Row.grid`` is §5's keyword FAMILY and is derivable from no other column,
#: which is why a domain over families is read off it rather than listed here.
SCALAR_GRIDS = frozenset({keywords.STRINGS, keywords.NUMBERS})
CONTAINER_GRIDS = frozenset({keywords.ARRAYS, keywords.OBJECTS})


class Stated(NamedTuple):
    """One difference between a projection and its derivation, and why it is there."""

    #: The table the difference is in, as the dotted name a reader greps for.
    table: str
    #: The key the difference is at: a keyword, a ``keyword@POSITION``, or a format value.
    key: str
    #: Why.  A sentence, because a reader of a failing assertion needs the reason and not
    #: a flag -- and because writing one is the cost that makes a deliberate difference
    #: deliberate.
    reason: str


#: **EVERY DIFFERENCE BETWEEN A PROJECTION AND ITS DERIVATION, STATED.**  This list may
#: SHRINK and may not grow quietly: a new entry is a new undeclared drop made declared,
#: which is a decision with a reader, and an entry that stops differing fails
#: :func:`test_no_stated_difference_is_stale` rather than sitting here forever.
STATED: tuple[Stated, ...] = (
    Stated(
        "codegen.constraints.SPELLING",
        "uniqueItems",
        "A fact a TypeRef carries (``ir.FACTS``) that spells no scalar and no container "
        "ALIAS: §5 gives it a RULE on the nearest class plus a "
        "``json_schema_extra={'uniqueItems': true}`` beside it, and its cell is the one "
        "RULE in the table with ``rendered=True`` for exactly that reason.  An alias "
        "name is a function of the constraint set, and a rule enforced on the "
        "constructor is not part of the shape the name describes.",
    ),
    Stated(
        "codegen.lower.scalars.FORMAT_TYPES",
        "hostname",
        "Stated by the bundle at 49 nodes in 18 documents and asserted by NO document's "
        "own draft here: ``jsonschema``'s draft-07 checker needs ``fqdn`` installed for "
        "it and this environment does not have it.  So the format rides as "
        "``json_schema_extra`` and the class is exactly as wide as its document, which "
        "is §2's direction.  It is in :data:`RUNTIME_DRIFT` as well, because the SDK's "
        "own checker DOES assert it.",
    ),
    Stated(
        "codegen.lower.scalars.FORMAT_TYPES",
        "uri-template",
        "Stated by the bundle at 199 nodes in 52 documents and asserted by no document's "
        "own draft here, which needs ``uritemplate`` installed.  Same reading as "
        "``hostname``, and in :data:`RUNTIME_DRIFT` for the same reason.",
    ),
    Stated(
        "codegen.keywords.Effect",
        "deprecated@ROOT",
        "§6's line says 'ROOT / BRANCH -> the class's ``json_schema_extra``' and the "
        "cell carries ``rendered=False``; no class-level ``json_schema_extra`` is "
        "emitted anywhere in the tree.  27 document roots state the keyword, "
        "``core/format.json`` among them.  The repair is in ``codegen/render.py``, which "
        "a sibling lane owns this cycle (``adcp-client-python-ahbe``).",
    ),
    Stated(
        "codegen.keywords.Effect",
        "deprecated@BRANCH",
        "The same cell as ``deprecated@ROOT`` -- ``_group((ROOT, BRANCH), ...)`` writes "
        "one cell at both -- at the 278 BRANCH nodes the bundle states the keyword at.",
    ),
)

#: **WHERE AN ``ANNOTATION`` CELL'S FACT LANDS, for the cells the rendered schema does not
#: carry.**  ``Effect.ANNOTATION`` is "a fact a lowering CARRIES rather than compiles", so
#: a cell with ``rendered=False`` carries it somewhere that ``model_json_schema()`` cannot
#: show -- and "somewhere" has to be nameable, or the cell is the ``deprecated`` drop
#: again.  Keyed by keyword, because the destination is the keyword's and not the
#: position's.
#:
#: ``None`` is the answer that it lands NOWHERE, and it is not a free one: every position
#: of such a keyword then owes a :data:`STATED` entry
#: (:func:`test_every_annotation_cell_names_where_its_fact_lands`).
CARRIED_TO: dict[str, str | None] = {
    "enumDescriptions": "the enum member docstrings, which a rendered schema has no slot "
    "for; ``render.py`` writes them into the class body.",
    "x-enum-descriptions": "the bundle's prefixed spelling of ``enumDescriptions``, to "
    "the same place.",
    # Nowhere, at ROOT and at BRANCH: §6's line says the class's ``json_schema_extra``
    # and the emitted tree has 0 class-level ``json_schema_extra`` sites.  At PROP the
    # cell is ``rendered=True`` and ``Field(deprecated=True)`` carries it, which is a
    # different cell and not this one.
    "deprecated": None,
}

#: **THE PROBE, and it is not a fourth table.**  ``RENDERED`` is now
#: ``keywords.rendered_annotations_at(PROP)`` and so cannot disagree with the declaration
#: -- which leaves the half a derivation cannot close: whether ``render._field``, the code
#: that writes the field, carries the keyword at all.  That is what went wrong, in the
#: other direction, for the whole life of the literal.
#:
#: Each entry says how to SET the keyword on an ``ir.Field`` and how to READ it back off
#: the rendered field.  A keyword entering the derived set with no entry here fails
#: :func:`test_the_rendered_annotations_are_what_the_renderer_writes` with "no probe",
#: which is the red that forces an author to say where the renderer carries it.
PROBES: dict[str, tuple[dict[str, Any], str]] = {
    "default": ({"default": "probe"}, "default"),
    "description": ({"description": "probe"}, "extras.description"),
    "deprecated": ({"deprecated": True}, "extras.deprecated"),
}

#: The formats the SDK's RUNTIME validator asserts that the DOCUMENTS' own draft does not
#: -- difference 2 of the module docstring, declared so a FOURTH is a failure.  Each one is
#: a node where ``strict_validate``'s schema half refuses a value the class accepts.
RUNTIME_DRIFT = frozenset({"hostname", "uri-template", "uuid"})


def _stated_for(table: str) -> frozenset[str]:
    """The keys :data:`STATED` declares a difference at, for one table."""
    return frozenset(one.key for one in STATED if one.table == table)


class Sites(NamedTuple):
    """The bundle's ``format`` census, read PER DOCUMENT because the gate is."""

    #: format value -> the documents stating it.
    stated: dict[str, set[str]]
    #: format value -> the documents that state it AND whose own draft asserts it.
    #: ``lower.scalars``' gate is ``fmt in mod.asserted``, so this is the set where a
    #: missing ``FORMAT_TYPES`` entry leaves the class wider than the document.
    asserted: dict[str, set[str]]


def _sites() -> Sites:
    """The ``format`` census over the bundle, one document at a time.

    **PER DOCUMENT and never a union, because a bundle is not one draft.**  Measured over
    this one: 1,177 documents declare draft-07, **399 declare 2020-12**, 53 declare no
    ``$schema`` and one names the manifest schema -- and ``uuid`` entered the format
    vocabulary in 2019-09.  So the union of every document's asserted set contains ``uuid``
    while none of the 7 documents that STATE ``format: uuid`` asserts it, and a union-based
    reading of this concludes the opposite of the truth.

    Read through ``bundle.nodes_at`` -- the ONE walk -- so a ``format`` under a ``default``
    or an ``examples`` is not counted: those hold INSTANCE data, where a key named
    ``format`` is a data field whose name collides.
    """
    stated: dict[str, set[str]] = collections.defaultdict(set)
    asserted: dict[str, set[str]] = collections.defaultdict(set)
    for path in sorted(BUNDLE.rglob("*.json")):
        document = path.relative_to(BUNDLE).as_posix()
        node = bundle.read(BUNDLE, document)
        here = emit.asserted_formats(node)
        for _, found, _ in bundle.nodes_at(node):
            value = found.get("format")
            if not isinstance(value, str):
                continue
            stated[value].add(document)
            if value in here:
                asserted[value].add(document)
    return Sites(dict(stated), dict(asserted))


def test_the_descent_column_is_the_same_at_every_position() -> None:
    """``bundle.DESCENDS`` reads the column at ROOT and uses it at all nine positions.

    Its own comment states the precondition and nothing asserted it: "Read at ROOT and
    used at every position, which is a fact about the table rather than an assumption ...
    **A row that ever differed would make this a per-position read, not a second table.**"
    A row that differed would make every reader of ``bundle.DESCENDS`` -- the census walk,
    the reference inliner, the verifier's own descent -- read the wrong child position in
    silence, which is the defect class of this file at the one table that is already a
    derivation.

    Measured: 15 keywords, the same child position at each of the nine.
    """
    root = keywords.descends_at(Position.ROOT)
    assert bundle.DESCENDS == root, "bundle.DESCENDS is no longer the column read at ROOT"
    assert len(root) == 15, f"the descent column is {len(root)} keywords, was 15"
    for position in Position:
        assert keywords.descends_at(position) == root, (
            f"the descent column at {position.value} differs from ROOT's: "
            f"{dict(keywords.descends_at(position))} != {dict(root)}. bundle.DESCENDS "
            "reads ROOT and applies it everywhere, so this has to become a per-position "
            "read before the differing row lands."
        )


def test_the_rendered_annotations_are_what_the_renderer_writes() -> None:
    """Every keyword ``intersect.RENDERED`` names reaches the field ``render._field`` builds.

    **The half a derivation cannot close.**  ``RENDERED`` is
    ``keywords.rendered_annotations_at(PROP)`` now, so the table and the rule cannot
    disagree -- but the table claiming ``rendered=True`` while the renderer writes nothing
    is the same drop from the other end, and that is what a literal hid for the whole life
    of ``("default", "description")``: the cell said rendered, ``render._field`` wrote
    ``Field(deprecated=True)``, and the rule in between carried neither.

    :data:`PROBES` is how the question is asked.  A keyword in the derived set with no
    probe fails here, which is the point: the author of the next rendered annotation says
    where the renderer carries it, or the check is red.
    """
    for keyword in intersect.RENDERED:
        assert keyword in PROBES, (
            f"{keyword!r} is a rendered annotation at PROP with no entry in PROBES, so "
            "nothing here grades whether render._field carries it. Add the probe."
        )
    for keyword, (overrides, reads) in PROBES.items():
        assert keyword in intersect.RENDERED, (
            f"PROBES names {keyword!r} and keywords.rendered_annotations_at(PROP) does "
            "not: the probe is stale, or the cell stopped rendering."
        )
        field = render._field(
            ir.Field(
                name="probe",
                wire="probe",
                type=ir.TypeRef(path="str"),
                required=False,
                **overrides,
            )
        )
        if reads == "default":
            assert field.has_default and field.default == overrides["default"], (
                f"render._field drops {keyword!r}: the rendered field carries no default"
            )
        else:
            _, key = reads.split(".", 1)
            assert field.extras.get(key) == overrides[keyword], (
                f"render._field drops {keyword!r}: the rendered field's extras are "
                f"{field.extras}, with no {key!r}. The cell at PROP says rendered=True "
                "and intersect's restatement rule carries it, so a field that renders "
                "nothing for it is the 21-field drop again."
            )


def test_the_restatement_rule_asks_about_no_constraint() -> None:
    """``RENDERED``'s difference from ``rendered_at(PROP)`` is exactly the LOWERING cells.

    This is the deliberate subset, stated as a derivation rather than asserted as a count:
    ``type``, ``format``, ``enum``, ``const``, ``required``, the bounds and ``uniqueItems``
    render as facts too, and a rule asking "would these two render a different FIELD" must
    not ask about them -- ``intersect.at_least_as_tight`` compares what two declarations
    say about the INSTANCE, and a narrowing reported as an annotation difference would be
    merged as though neither side constrained anything.

    Measured at PROP: 20 rendered keywords, 3 of them annotations, 17 lowering.
    """
    rendered = keywords.rendered_at(Position.PROP)
    annotations = keywords.rendered_annotations_at(Position.PROP)
    assert frozenset(intersect.RENDERED) == annotations, (
        "intersect.RENDERED is no longer the reading of the declaration it is defined as"
    )
    lowering = {
        k
        for k in rendered
        if (c := keywords.cell(k, Position.PROP)) is not None and keywords.lowers(c)
    }
    assert rendered - annotations == lowering, (
        "a keyword rendered at PROP is either an annotation the restatement rule carries "
        "or a constraint at_least_as_tight compares, and this one is neither: "
        f"{sorted(rendered - annotations - lowering)}"
    )
    assert (len(rendered), len(annotations)) == (20, 3), (
        f"PROP renders {len(rendered)} keywords, {len(annotations)} of them annotations; "
        "was (20, 3). A new one is not a failure -- add it to PROBES and update this."
    )


def test_every_annotation_cell_names_where_its_fact_lands() -> None:
    """An ``ANNOTATION`` cell the rendered schema does not carry says where it goes instead.

    ``Effect.ANNOTATION`` is "a fact a lowering CARRIES rather than compiles", so a cell
    with ``rendered=False`` is claiming a destination outside ``model_json_schema()``.
    ``enumDescriptions`` has one -- the enum member docstrings -- and ``deprecated`` at
    ROOT and BRANCH has none, which is difference 1 of the module docstring: §6's own
    generated line says it lands in the class's ``json_schema_extra`` and no such thing is
    emitted.  A cell with neither a destination nor a :data:`STATED` entry is the next
    silent drop, so it fails here.
    """
    unrendered = {
        keyword: sorted(
            position.value
            for position in Position
            if (cell := keywords.cell(keyword, position)) is not None
            and cell.effect is Effect.ANNOTATION
            and not cell.rendered
        )
        for keyword in keywords.TABLE
    }
    unrendered = {k: v for k, v in unrendered.items() if v}
    assert set(unrendered) == set(CARRIED_TO), (
        "an ANNOTATION cell renders nothing and names no destination: "
        f"{sorted(set(unrendered) - set(CARRIED_TO))}; or CARRIED_TO is stale: "
        f"{sorted(set(CARRIED_TO) - set(unrendered))}"
    )
    for keyword, positions in unrendered.items():
        if CARRIED_TO[keyword] is not None:
            continue
        for position in positions:
            assert f"{keyword}@{position}" in _stated_for("codegen.keywords.Effect"), (
                f"{keyword}@{position} is an ANNOTATION that lands nowhere and is not in "
                "STATED, so nothing tells a reader the fact is gone"
            )


def test_every_fact_a_type_carries_has_a_spelling() -> None:
    """``SPELLING`` and ``CONTAINER_SPELLING`` cover the bounds, with one stated difference.

    An alias name is a function of the constraint SET -- that is ``SPELLING``'s own
    sentence -- so a bound with no word in it makes two different shapes share one name,
    which is the collision ``constraints`` exists to prevent.  The domain is read off the
    declaration twice over: §5's keyword FAMILY (``Row.grid``) says which grid a keyword
    is in, and ``keywords.RANGES`` / ``ir.FACTS`` say which keywords are bounds at all.

    Measured: the scalar domain is ``SPELLING`` exactly, and the container domain is
    ``CONTAINER_SPELLING`` plus ``uniqueItems``, whose cell is the table's one rendered
    RULE.
    """

    def bounds(grids: frozenset[str]) -> frozenset[str]:
        return frozenset(
            k
            for k in keywords.TABLE
            if keywords.grid_of(k) in grids and (keywords.range_of(k) is not None or k in ir.FACTS)
        )

    spelled = frozenset(k for k, _ in SPELLING)
    assert bounds(SCALAR_GRIDS) == spelled, (
        f"the scalar bounds and SPELLING differ at {sorted(bounds(SCALAR_GRIDS) ^ spelled)}"
    )
    container = frozenset(k for group in CONTAINER_SPELLING.values() for k, _ in group)
    difference = bounds(CONTAINER_GRIDS) - container
    assert difference == _stated_for("codegen.constraints.SPELLING"), (
        f"the container bounds differ from CONTAINER_SPELLING at {sorted(difference)}, "
        f"and STATED declares {sorted(_stated_for('codegen.constraints.SPELLING'))}"
    )
    assert frozenset(ir.FACTS) - spelled - container == difference, (
        "every fact a TypeRef carries spells an alias or is a stated difference; this one "
        f"is neither: {sorted(frozenset(ir.FACTS) - spelled - container - difference)}"
    )


def test_every_asserted_format_the_bundle_states_selects_a_type() -> None:
    """A format the bundle states AND a document's own draft asserts has a type in the table.

    This is the ``format: email`` defect as a rule.  ``email`` was asserted by every
    document stating it, ``FORMAT_TYPES`` had no entry, the format rode as
    ``json_schema_extra`` -- which enforces nothing -- and the model took ``'yes'``,
    ``''`` and ``'!!NOT-VALID!!'`` for 100 divergences over 18 tools before the parity
    screen caught it.  The gate is ``fmt in mod.asserted``, so a format NOT asserted is
    correctly absent and is a :data:`STATED` entry rather than a failure.

    Measured over the bundle's 1,630 documents: 7 format values stated -- ``uri`` at 9,543
    nodes, ``date-time`` at 5,456, ``email`` at 605, ``date`` at 378, ``uri-template`` at
    199, ``hostname`` at 49, ``uuid`` at 18 -- and 4 of the 7 asserted by a document that
    states them.
    """
    sites = _sites()
    assert len(sites.stated) == 7, f"the bundle states {len(sites.stated)} format values, was 7"
    missing = set(sites.asserted) - set(FORMAT_TYPES)
    assert not missing, (
        f"these formats are stated by a document whose OWN draft asserts them, and "
        f"FORMAT_TYPES selects no type for them: {sorted(missing)}. The class is then "
        "WIDER than the document at every node stating one, and nothing declares it -- "
        "which is the `format: email` defect, 100 divergences over 18 tools."
    )
    unasserted = set(sites.stated) - set(sites.asserted) - set(FORMAT_TYPES)
    assert unasserted == _stated_for("codegen.lower.scalars.FORMAT_TYPES"), (
        f"formats stated but asserted by no document stating them, and absent from "
        f"FORMAT_TYPES: {sorted(unasserted)}; STATED declares "
        f"{sorted(_stated_for('codegen.lower.scalars.FORMAT_TYPES'))}"
    )


def test_the_compiler_and_the_runtime_assert_one_format_set() -> None:
    """``emit.asserted_formats`` and the SDK's runtime checker, which claim to be one set.

    ``asserted_formats``' docstring: "Both halves of ``strict_validate`` assert through the
    same attribute, so the set this walk gates on and the set the runtime enforces are one
    set and cannot drift."  They do not assert through the same attribute -- the compiler
    reads ``validator_for(doc).FORMAT_CHECKER``, the document's own draft, and
    ``schema_loader._build_format_checker`` builds the GLOBAL ``FormatChecker()`` -- and the
    two have drifted by three formats, every one of them stated by the bundle.

    Declared and not fixed: the repair is a decision about which side moves, and
    ``src/adcp/validation/schema_loader.py`` is outside this lane's write scope either way.
    A FOURTH is a failure, which is what this is for.

    Measured per document, which is the only reading that answers it (see :func:`_sites`):
    ``uri-template`` in 52 documents, ``hostname`` in 18, ``uuid`` in 7.
    """
    from adcp.validation.schema_loader import _build_format_checker

    runtime = frozenset(_build_format_checker().checkers)
    sites = _sites()
    drift = {
        fmt: documents - sites.asserted.get(fmt, set())
        for fmt, documents in sites.stated.items()
        if fmt in runtime and documents - sites.asserted.get(fmt, set())
    }
    assert frozenset(drift) == RUNTIME_DRIFT, (
        f"the SDK's runtime format checker asserts {sorted(drift)} at nodes whose own "
        f"document's draft does not; the declared set is {sorted(RUNTIME_DRIFT)}. A new "
        "entry is a new family of nodes where the bundled schema refuses what the class "
        "accepts -- one half of strict_validate against the other."
    )
    assert {f: len(d) for f, d in sorted(drift.items())} == {
        "hostname": 18,
        "uri-template": 52,
        "uuid": 7,
    }, (
        f"the drift's reach moved: { ({f: len(d) for f, d in sorted(drift.items())}) }. The "
        "set is declared, the SIZE is a measurement, and a growing one is worth a reading."
    )


def test_no_table_names_a_keyword_the_declaration_does_not() -> None:
    """The drift in the other direction: a projection naming a keyword with no row.

    A keyword with no row is the one answer that REFUSES a document (``keywords.cell``
    returns ``None``), so a table naming one is a rule the screen would refuse the document
    for -- and ``address()`` has nothing to say about where it was decided.
    """
    named = (
        {("codegen.intersect.RENDERED", k) for k in intersect.RENDERED}
        | {("codegen.constraints.SPELLING", k) for k, _ in SPELLING}
        | {
            ("codegen.constraints.CONTAINER_SPELLING", k)
            for group in CONTAINER_SPELLING.values()
            for k, _ in group
        }
        | {("codegen.bundle.DESCENDS", k) for k in bundle.DESCENDS}
    )
    unrowed = sorted((table, k) for table, k in named if k not in keywords.TABLE)
    assert not unrowed, f"these tables name keywords the declaration has no row for: {unrowed}"


def test_no_stated_difference_is_stale() -> None:
    """A :data:`STATED` entry that no longer differs is deleted, not kept.

    What makes this a ratchet rather than a snapshot: every entry above is asserted LIVE by
    one of the tests in this file, so a repair that closes a difference fails here until the
    row goes.  Without it the list is an allowlist that only grows, which is the shape
    ``review-ratchet-allowlists`` refuses by name.
    """
    for one in STATED:
        assert one.reason.strip(), f"{one.table}/{one.key} states no reason"
        assert one.table in {
            "codegen.keywords.Effect",
            "codegen.constraints.SPELLING",
            "codegen.lower.scalars.FORMAT_TYPES",
        }, f"{one.table} is not one of the tables this file grades"
    keys = [(one.table, one.key) for one in STATED]
    assert len(keys) == len(set(keys)), f"STATED holds a duplicate: {keys}"
    assert len(STATED) == 5, (
        f"STATED declares {len(STATED)} differences, was 5. Fewer is a repair landing and "
        "the number moves with it; more is a new declared drop and needs a reader."
    )
