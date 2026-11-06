"""The approximation INSTRUMENT, and the proof that each half fails when it should.

``docs/plan/architecture.md`` section 14 step 8 is "the approximation, end to end, with no
cell widened", and that exit condition is what makes this file necessary rather than
optional: with ``APPROXIMATED`` at 0 over the whole bundle, every check the step adds is
green over an empty set, and an instrument graded over an empty set is graded by nothing.
So every arm here is exercised on a CONSTRUCTED pair -- a hand-written class, a hand-built
declaration, and a document the two are put to a draw against -- and each clause is
asserted in BOTH directions: it catches the defect it is for, and it does not fire on the
faithful case beside it.

``docs/plan/rebuild-plan.md`` section 8 says what stops a declaration from being an
allowlist, and it is the accepts obligation: "Nobody can add an entry to make a failure go
away without the model actually widening at that pointer, because the accepts draw then
has to accept the values the keyword distinguishes."  That obligation
(``harness.check_widening``) is the instrument perturbed here in both directions, beside
the one equality the other KIND of declaration is held to: the set of unions declaring an
UNDERDETERMINED approximation equals the set section 4's derivation cannot separate
(``harness.underdetermined_census``, at the end of this file).

The set equality between the keywords the document-side fold ranges over and the keywords
a declaration renders is held by ``tests/test_keywords.py`` over ``harness.FOLDED_FACTS``
and ``keywords.rendered_at``, which is where a set equality between two derivations
belongs; this file does not restate it.
"""

from __future__ import annotations

import importlib
import pathlib
from typing import Any, ClassVar

import pytest
from jsonschema import Draft7Validator
from pydantic import Field

from adcp.types._base import (
    APPROXIMATIONS,
    KINDS,
    UNDERDETERMINED,
    WIDENED,
    AdCPBaseModel,
    Approximation,
    SchemaRef,
    schema_at,
)
from codegen import attribution, bundle, compiler, emit, harness, ir, keywords, patch, render
from codegen.keywords import Effect, Position, Rung
from codegen.lower.approximate import approximate, attribution_for, declare, rung_for
from codegen.refusal import BuildFailure
from tests import compared
from tests.nodeset import claimed

DOC = "core/probe.json"

#: The pinned bundle the population below is read over, which is the one every other
#: census in ``tests/`` is taken against.
#:
#: **THE PATCHED ONE, because that is the bundle the graded TREE was emitted from**
#: (``codegen.patch.for_build``, the same derivation ``tests/fresh.py`` and ``./check``
#: take).  Read as the published path alone, the census below asked this bundle for a
#: document the patch set adds -- ``core/country-code.json`` -- and raised
#: ``FileNotFoundError`` inside its own loop, which is
#: ``docs/plan/architecture.md``'s "A CHECK THAT DIES IN ITS OWN SETUP ... is
#: indistinguishable from a check that has nothing to report" reached through "AN OVERRIDE
#: THE BUILD DOES NOT APPLY IS A LIE, AND THE GATE IS ON THE ARTIFACT": the population is
#: the emitted tree's pairs, so the bundle this reads their documents out of has to be the
#: bundle they were emitted from or the two range over different inputs.
BUNDLE = patch.for_build(pathlib.Path("schemas/cache/3.2"))


def _ref(pointer: str = "#") -> SchemaRef:
    return SchemaRef(DOC, pointer)


# --------------------------------------------------------------------------- #
# the cell's rung: section 3's field, and its None-ness
# --------------------------------------------------------------------------- #
def test_every_cell_that_compiles_to_something_carries_a_rung_and_no_other_does() -> None:
    """Section 3's biconditional, over every cell of the table rather than a sample.

    "``widens_to`` ... is ``None`` for a keyword that states no fact about an instance --
    ``$comment``, ``title``, ``errorMessage``, the registry data keys -- because there is
    nothing to drop and a rung would be a decision about a non-decision."

    Asserted as an equality between two derivations and not as a spot check: the
    population is every cell the table holds, so a row added without a rung reddens here
    rather than at the first document that needs one, where it would be a
    ``BuildFailure`` from ``rung_for``.
    """
    wrong: list[str] = []
    for keyword, row in keywords.TABLE.items():
        for where, cell in (("default", row.default), *((str(p), c) for p, c in row.at.items())):
            if keywords.states_a_fact(cell.effect) != (cell.widens_to is not None):
                wrong.append(f"{keyword} at {where}: {cell.effect} / {cell.widens_to}")
    assert wrong == [], wrong
    # The control, so the clause above cannot be green over a table where nothing compiles
    # and nothing carries a rung.
    carried = [
        c.widens_to
        for row in keywords.TABLE.values()
        for c in (row.default, *row.at.values())
        if c.widens_to is not None
    ]
    assert len(carried) > 50, len(carried)
    assert set(carried) <= set(keywords.Rung), sorted(set(carried) - set(keywords.Rung))


def test_the_four_rungs_section_5_states_are_the_rungs_the_cells_carry() -> None:
    """Section 5's "(b) Rows whose answer is a declared widening", cell by cell.

    The section names a rung for four rows and one position override, and each is asserted
    against the cell here with the sentence that decides it.  Every other rung follows the
    stated rule in ``keywords._RUNG``'s own comment, which these four are the cross-check
    on: a rule that disagreed with any of the four named rows would be the wrong rule.
    """
    # "**``uniqueItems`` and ``contains`` where even a named type cannot hold the rule.**
    # Rung KEYWORD: the array is ``list[X]`` and the duplicate or existential check is the
    # schema half's alone."
    assert keywords.cell("uniqueItems", Position.PROP).widens_to is Rung.KEYWORD
    assert keywords.cell("contains", Position.PROP).widens_to is Rung.KEYWORD
    # "**A list-valued ``items``.**  Rung JOIN: ``list[A | B | ...]`` over the positional
    # schemas, dropping position and arity."
    assert keywords.cell("items", Position.PROP).widens_to is Rung.JOIN
    assert keywords.cell("items", Position.ROOT).widens_to is Rung.JOIN
    # "**An ``allOf`` restatement that neither matches nor narrows.** ... Rung KEYWORD: the
    # field takes the base's declaration and the restatement's extra facts are dropped."
    assert keywords.cell("allOf", Position.CONJ).widens_to is Rung.KEYWORD
    # "**An empty intersection** -- two disjoint type words, two disjoint enums. ... Rung
    # TOP".  A conjunct is at CONJ, and the cell differs there from the keyword's own rung,
    # which is section 3's test of a position override existing at all.
    assert keywords.cell("type", Position.CONJ).widens_to is Rung.TOP
    assert keywords.cell("enum", Position.CONJ).widens_to is Rung.TOP
    assert keywords.cell("type", Position.PROP).widens_to is Rung.TYPE
    assert keywords.cell("enum", Position.PROP).widens_to is Rung.KEYWORD
    # Section 2's own second-rung example: "``format: uri`` beside ``maxLength`` -> the
    # constrained ``str``, the format riding as ``json_schema_extra``."
    assert keywords.cell("format", Position.PROP).widens_to is Rung.TYPE


def test_a_position_override_for_a_rung_renders_a_grid_clause_only_when_it_has_one() -> None:
    """``keywords.py``'s own rule, in BOTH its cases.

    "An override whose ``compiles`` is EMPTY renders no clause: it records a cell the
    default sentence already covers in prose."  ``tests/test_keywords.py`` holds the grids
    themselves; this asserts the mechanism the two CONJ overrides rely on, so a later row
    cannot give one a sentence and silently change the committed document.

    **This test asserted BOTH overrides were empty and ``enum``'s stopped being empty**
    (``adcp-client-python-10l.109``).  §5's ``enum`` row at CONJ gained a decided sentence
    -- "beside a ``$ref`` whose target is an enumeration → §2's intersection of the two
    vocabularies" -- and the grid moved with it, which is the OPPOSITE of the silent change
    the test exists to forbid: the clause is in the committed document, and
    ``test_keywords.py`` is what holds it there.  So the claim is read the way the rule is
    written -- empty renders nothing, non-empty renders its own clause AND the committed
    grid carries it -- rather than as a pin on which of the two cells happens to be empty.
    """
    assert keywords.TABLE["type"].at[Position.CONJ].compiles == ""
    said = keywords.TABLE["enum"].at[Position.CONJ].compiles
    assert said, "enum's CONJ override is empty again; the clause below is then a stale pin"
    # The one obligation the emptiness was standing in for: whatever the override says is
    # in the generated region of the committed document.  Read out of the document rather
    # than restated here, so this cannot pass against a sentence nobody published.
    grids = (
        pathlib.Path(__file__).resolve().parents[1] / "docs" / "plan" / "rebuild-plan.md"
    ).read_text()
    assert said.strip() in grids, said


def test_a_rung_cannot_be_asked_of_a_cell_that_states_no_fact() -> None:
    """Section 3: "a handler that asks for one is a ``BuildFailure``".

    "The keyword states no fact, so a widening against it would be a declaration with
    nothing to declare" -- an obligation :func:`harness.check_widening` could never
    discharge, because there is no fact at that pointer for it to draw against.
    """
    assert keywords.cell("title", Position.ROOT).effect is Effect.NAME
    with pytest.raises(BuildFailure, match="states no fact"):
        rung_for("title", Position.ROOT)
    with pytest.raises(BuildFailure, match="states no fact"):
        rung_for("$comment", Position.ROOT)
    # And the other direction: a cell that DOES state a fact answers.
    assert rung_for("uniqueItems", Position.PROP) is Rung.KEYWORD


def test_a_keyword_with_no_row_takes_the_top_rung() -> None:
    """Section 7: "``Any`` and not a narrower rung, because an unrowed keyword's reach is
    unknown: draft-07 ignores it, so the document may be narrower than ``Any`` and can
    never be wider, and ``Any`` is the one rung that is safe without knowing what the
    keyword does."
    """
    assert keywords.cell("frobnicate", Position.ROOT) is None
    assert rung_for("frobnicate", Position.ROOT) is Rung.TOP
    assert approximate(_ref(), "frobnicate", Position.ROOT, {"a": 1}).rung == Rung.TOP


def test_the_table_refuses_to_import_with_a_rung_missing_or_a_rung_with_nothing_to_drop() -> None:
    """``keywords._with_rungs``'s two guards, which are what keep the biconditional true
    at import rather than at the first document that needs a rung.

    Perturbed on a table of one row each way, because the committed table satisfies both
    and a guard nothing exercises is a guard that may not resolve.
    """
    compiling = keywords.Row(keywords.Cell(Effect.TYPE, True, None, "x"), grid=keywords.VALUES)
    inert = keywords.Row(keywords.Cell(Effect.NOTHING, False, None, "x"))
    with pytest.raises(ValueError, match="no entry in _RUNG"):
        keywords._with_rungs({"unrowed": compiling})
    with pytest.raises(ValueError, match="no cell that compiles to"):
        keywords._with_rungs({"type": inert})


# --------------------------------------------------------------------------- #
# the attribution: derived for ours, a registry entry for upstream
# --------------------------------------------------------------------------- #
def test_an_ours_attribution_is_the_cells_own_address_and_is_derived() -> None:
    """Section 2: "The attribution is therefore the **cell's own address** and is derived,
    not stored: a reader goes from a widened field to the row that decided it, and that
    row says why."

    So the address names the SECTION and the row, and the section is a projection of the
    cells (``keywords.grid_of``) rather than a second list.
    """
    assert keywords.address("uniqueItems") == f"{keywords.DOCUMENT} §5 arrays/uniqueItems"
    assert keywords.address("description") == f"{keywords.DOCUMENT} §6 admitted/description"
    # ``errorMessage`` was §7's one row and reads §6 now: the section a reader goes to is
    # the PROJECTION of the cell, so moving the cell moved the address with it and no
    # second list had to be edited.
    assert keywords.address("errorMessage") == f"{keywords.DOCUMENT} §6 admitted/errorMessage"
    assert keywords.address("frobnicate") == f"{keywords.DOCUMENT} §7 (no row): frobnicate"
    assert attribution_for(DOC, "#/properties/x", "uniqueItems") == keywords.address("uniqueItems")


def test_a_site_level_entry_wins_over_the_cells_address_in_one_lookup(monkeypatch) -> None:
    """Section 3: "One lookup, no precedence to get wrong: a site-level entry is more
    specific than a keyword-level one."

    And section 2's reason for the registry existing at all: "the same keyword widens by
    our decision at one site and by an upstream defect at another" -- which is what the
    second half asserts, on the same keyword at a different pointer.
    """
    issue = attribution.Issue("adcontextprotocol/adcp#8472", "the document should state the bound")
    monkeypatch.setattr(
        attribution, "REGISTRY", {(DOC, "#/properties/x", "uniqueItems"): issue}
    )
    assert attribution_for(DOC, "#/properties/x", "uniqueItems") == issue.attribution
    assert attribution_for(DOC, "#/properties/y", "uniqueItems") == keywords.address("uniqueItems")


def test_an_attribution_entry_with_no_issue_is_a_build_failure() -> None:
    """Section 3: "An entry in the registry with no issue reference is a ``BuildFailure``
    and not a missing field, which is the semantics document's section 9 rule ('an
    exemption names an upstream issue, or it is this SDK's own decision') made mechanical."

    Both halves: the entry cannot be CONSTRUCTED, and the registry-level reading answers
    for a mapping assembled from something other than a literal.
    """
    with pytest.raises(BuildFailure, match="names an upstream issue"):
        attribution.Issue("", "a summary with no issue behind it")
    with pytest.raises(BuildFailure, match="states no summary"):
        attribution.Issue("example/schema#1", "   ")
    assert attribution.malformed() == ()
    assert attribution.malformed({(DOC, "#", "uniqueItems"): "a free-text note"}) == (
        (DOC, "#", "uniqueItems"),
    )


def test_the_registry_is_empty_which_is_this_steps_exit_condition() -> None:
    """Section 14 step 8 widens no cell, so there is no widening to attribute.

    Asserted rather than assumed, because the figure a later row moves has to have a
    measured starting point: step 10's exit condition is "every upstream attribution names
    a live issue", and this is the 0 it starts from.
    """
    assert attribution.REGISTRY == {}


# --------------------------------------------------------------------------- #
# the declaration in the ARTIFACT: section 7's write and the consumer's read
# --------------------------------------------------------------------------- #
def test_an_approximation_is_minted_in_one_place_and_reads_its_rung_off_the_cell() -> None:
    """Section 2: ``approximate`` "is to an approximation what ``Refusal``'s constructors
    were to a kind: the ONE place a widening is minted, reading the rung off the cell."
    """
    one = approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True)
    assert one == Approximation(
        document=DOC,
        pointer="#/properties/tags",
        keyword="uniqueItems",
        kind=WIDENED,
        rung="KEYWORD",
        fact=True,
        attribution=keywords.address("uniqueItems"),
    )
    assert one.kind in KINDS
    with pytest.raises(BuildFailure, match="not one of section 2's two kinds"):
        approximate(_ref(), "uniqueItems", Position.PROP, True, kind="PROBABLY_FINE")


def test_a_handler_reaches_the_one_producer_through_one_accumulator() -> None:
    """Section 2's other half: "a refusal is absorbing, an approximation is ADDITIVE".

    :func:`codegen.lower.approximate.declare` is the call a handler makes, and it is
    :func:`approximate` plus the accumulation -- so the minting stays in one function and
    the append stays in one function beside it.  Section 6 names the order the accumulator
    has to keep: "the parser built each node's children in document order, and
    concatenation preserves it", which is a property of the walk and not of any handler,
    and it only stays one if there is one appender.

    The pointer is spelled through ``compiler.schema_ref`` -- the sole producer of the
    spelling ``__adcp_schema__`` uses -- so what a handler passes is its NODE's pointer
    and the ``#`` is not a handler's to write.
    """
    mod = compiler.Module(document=DOC)
    assert mod.approximations == []
    declare(mod, "/properties/tags", "uniqueItems", Position.PROP, True)
    declare(mod, "/properties/other", "maxLength", Position.PROP, 4)
    assert mod.approximations == [
        approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True),
        approximate(_ref("#/properties/other"), "maxLength", Position.PROP, 4),
    ], mod.approximations
    # The ``#`` and the document are the one spelling's, not the caller's.
    assert [a.pointer for a in mod.approximations] == [
        "#/properties/tags",
        "#/properties/other",
    ]
    assert {a.document for a in mod.approximations} == {DOC}
    # A kind travels through unchanged, which is what the UNDERDETERMINED row needs: it is
    # the one caller that does not take the default (section 2 gives it one instance).
    declare(mod, "/oneOf", "oneOf", Position.ROOT, OVERLAPPING["oneOf"], kind=UNDERDETERMINED)
    assert mod.approximations[-1].kind == UNDERDETERMINED


def test_the_declaration_renders_as_a_constructor_expression_the_consumer_reads_back() -> None:
    """Section 7: ``render.py`` writes it "onto the class ... and ``verify/`` reads it as a
    consumer reads any other class attribute."

    The round trip is the claim: the emitted text is EXECUTED here and the value that comes
    back out is the value that went in, so the artifact's spelling and the declaration are
    one thing rather than two.
    """
    one = approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True)
    decl = ir.ClassDecl(name="Probe", ref=_ref(), fields=())
    text = render.declaration(decl, (one,)).text
    assert APPROXIMATIONS in text
    namespace: dict[str, Any] = {
        "AdCPBaseModel": AdCPBaseModel,
        "Approximation": Approximation,
        "SchemaRef": SchemaRef,
        "ClassVar": ClassVar,
    }
    exec(compile(text, "<probe>", "exec"), namespace)  # the artifact is the subject
    assert harness.declarations_of(namespace["Probe"]) == (one,)


def test_nothing_is_written_where_nothing_was_approximated() -> None:
    """Section 14 step 8's byte-exact check, held at the one line that would move it.

    ``render._approximation_lines``'s own docstring carries the reasoning; this is the
    assertion, in both directions.
    """
    decl = ir.ClassDecl(name="Probe", ref=_ref(), fields=())
    assert APPROXIMATIONS not in render.declaration(decl, ()).text
    one = approximate(_ref(), "uniqueItems", Position.ROOT, True)
    assert APPROXIMATIONS in render.declaration(decl, (one,)).text


def test_the_declaration_is_never_a_json_schema_extra() -> None:
    """Section 7: "*Where it must NOT go.*  Not into ``Field(json_schema_extra=...)``."

    That would put the approximation into ``model_json_schema()``, where it would become a
    fact the model's own rendered schema states and the document does not.  The declaration
    is a class attribute precisely because a verifier has to be able to read it off the
    class while the schema the class renders stays the document's.

    Asserted in both places: the attribute is reachable on the CLASS
    (:func:`harness.declarations_of`) and absent from ``model_json_schema()`` at every
    depth.
    """
    one = approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True)

    class Probe(AdCPBaseModel):
        __adcp_schema__: ClassVar[SchemaRef] = _ref()
        __adcp_approximations__: ClassVar[tuple[Approximation, ...]] = (one,)
        tags: list[str]

    rendered = Probe.model_json_schema()
    assert harness.declarations_of(Probe) == (one,)
    assert APPROXIMATIONS not in repr(rendered)
    assert "approximat" not in repr(rendered).lower()


def test_a_declaration_is_read_off_the_class_that_declares_it_and_not_off_its_base() -> None:
    """``declarations_of`` reads ``vars`` and not ``getattr``, and this is the defect that
    forces it: a union branch subclasses its base, and the base at ``#`` declares
    everything in the document.

    Read through ``getattr`` a branch would claim its base's declarations and the equality
    would pass over a widening nothing at that branch widened.  ``graded()`` already draws
    the same line for ``__adcp_schema__``.
    """
    one = approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True)

    class Base(AdCPBaseModel):
        __adcp_approximations__: ClassVar[tuple[Approximation, ...]] = (one,)

    class Branch(Base):
        pass

    assert harness.declarations_of(Base) == (one,)
    assert harness.declarations_of(Branch) == ()


def test_a_declaration_is_carried_by_every_declaration_whose_node_contains_it() -> None:
    """``render.declared_at``'s containment rule, which the pairing forces.

    A pair is graded over its own node and the whole subtree under it, and the obligation
    that proves a declaration walks the declaration's pointer from the pair's OWN node
    (:func:`harness.check_widening`), so a fact at ``#/properties/x/maxLength`` is reached
    from the root class's node as well as from the nested class's own.  A declaration
    carried only by the nearest enclosing class would be put to a draw at one of those
    pairs and be unknown to the other.
    """
    inner = approximate(_ref("#/properties/x/properties/y"), "uniqueItems", Position.PROP, True)
    assert render.declared_at((inner,), _ref("#")) == (inner,)
    assert render.declared_at((inner,), _ref("#/properties/x")) == (inner,)
    assert render.declared_at((inner,), _ref("#/properties/x/properties/y")) == (inner,)
    assert render.declared_at((inner,), _ref("#/properties/z")) == ()
    # The separator is part of the prefix, so a sibling whose name EXTENDS another's is not
    # contained by it.
    assert render.declared_at((inner,), _ref("#/properties/xy")) == ()
    # And a declaration of another document is never this one's.
    assert render.declared_at((inner,), SchemaRef("core/other.json", "#")) == ()


def test_containment_stops_at_a_section_boundary_because_the_obligation_does() -> None:
    """``render.declared_at``'s ONE exception, and the direction that makes it one.

    A ``definitions`` / ``$defs`` entry is CONTAINED by the root's pointer and describes
    no instance location the root's own class can reach: an entry is reached only by a
    ``$ref``, which is another class's node, and draft-07 gives a section no assertion
    behaviour.  §8 reads the same boundary from the other side -- ``harness.locations``
    takes no frontier item inside an entry because "it has no instance location, which is
    §8's own reading of why such a declaration belongs to the entry's own pair" -- and the
    obligation refuses the pointer outright with "the pointer describes no instance
    location, so no drawn value can be placed at it".  Carried across it, one fact is
    counted once as a pass at the entry's pair and once as ``unproved_widening`` at the
    root's.

    Both arms, because dropping one direction is how the fix becomes a hole: the entry's
    OWN class keeps every declaration inside it (an entry AT ``ref`` is not between), and
    an ``allOf``/``anyOf``/``properties`` hop is unaffected, which
    :func:`test_a_declaration_is_carried_by_every_declaration_whose_node_contains_it`
    above states over the same function.
    """
    inside = approximate(_ref("#/definitions/profile/allOf/0"), "uniqueItems", Position.DEF, True)
    entries = frozenset({"/definitions/profile"})

    # The root CONTAINS it and cannot reach it, so it is not carried there.
    assert render.declared_at((inside,), _ref("#"), entries) == ()
    # The entry's own class is where the obligation can put it, so it is carried there.
    assert render.declared_at((inside,), _ref("#/definitions/profile"), entries) == (inside,)
    assert render.declared_at((inside,), _ref("#/definitions/profile/allOf/0"), entries) == (
        inside,
    )
    # With no census the function is the containment it always was, which is the
    # fail-safe direction: a module built outside a run drops nothing.
    assert render.declared_at((inside,), _ref("#")) == (inside,)
    # A pointer that is not a section entry does not become one by being spelled below a
    # declared node: the census is a reading of the DOCUMENT and not of the spelling.
    plain = approximate(_ref("#/properties/x/allOf/0"), "uniqueItems", Position.PROP, True)
    assert render.declared_at((plain,), _ref("#"), entries) == (plain,)


def test_no_declaration_the_tree_carries_is_one_its_pair_cannot_put_to_a_draw() -> None:
    """**The equality the rule above is stated as, over the emitted population.**

    Two derivations of one set, neither a literal:

    * what the OBLIGATION can do -- for every pair of the tree and every non-underdetermined
      declaration it carries, whether ``harness._steps`` walks the declaration's pointer
      from that pair's own node to an instance location.  A ``None`` there is the
      ``unproved_widening`` the pair reports under its own name;
    * what the SECTION BOUNDARY says -- ``bundle.reaches``, the predicate
      ``bundle.undecidable_references`` already asks of a reference over the same boundary,
      with the pair's own pointer as the reach.

    The claim is that the first set is EMPTY and that the second is what empties it, so the
    gate is not vacuous: the set of declarations the boundary excludes is named, asserted
    non-empty, and asserted to be exactly the set the walk could not reach before the rule
    landed.  At the row that wrote this the bundle states three of them --
    ``core/bidding-policy-capability.json#`` carrying
    ``#/definitions/policy_profile/allOf/{0,1}/if`` and
    ``core/targeting-overlay-support.json#`` carrying
    ``#/definitions/daypartSupport/anyOf/1/allOf/0/if`` -- and every one is also carried,
    and proved, at the entry's own pair.

    **Over the tree a fresh run emits**, which is what ``docs/plan/architecture.md`` makes
    grading read, and through the same pairing every other reader of it uses
    (``tests/compared.pairs``).
    """
    rows = [
        (f"{ref.document}{ref.pointer}", ref, declared)
        for ref, model, accept, module in compared.pairs()
        for declared in (
            harness.declarations_of(
                model if isinstance(model, type) else importlib.import_module(module)
            ),
        )
    ]
    claimed("graded pairs", {name for name, _, _ in rows})
    #: document -> every declaration SOME pair of that document carries, by site.  The
    #: whole declared set of the tree, which is what the two derivations below range over.
    stated: dict[str, dict[tuple[str, str, str], Any]] = {}
    for _, ref, declared in rows:
        for one in declared:
            stated.setdefault(ref.document, {})[harness.site_of(one)] = one
    claimed("documents the tree declares a fact for", set(stated))

    #: (pair, site) the obligation's own walk cannot reach from that pair's node.  A
    #: ``None`` from ``_steps`` is the ``unproved_widening`` the pair reports by name.
    unreachable: set[tuple[str, tuple[str, str, str]]] = set()
    #: (pair, site) CONTAINED by the pair's pointer and kept off it by the boundary.
    excluded: set[tuple[str, tuple[str, str, str]]] = set()
    #: site -> the pairs that do carry it, so the second half can ask where it is proved.
    owners: dict[tuple[str, str, str], set[str]] = {}
    for name, ref, declared in rows:
        entries = bundle.section_entries(bundle.read(BUNDLE, ref.document))
        node = schema_at(ref)
        for one in declared:
            owners.setdefault(harness.site_of(one), set()).add(name)
            if one.kind == UNDERDETERMINED:
                continue  # §2: no draw can see one, so the obligation claims none
            if harness._steps(_relative(ref, one.pointer), node, _stated(ref)) is None:
                unreachable.add((name, harness.site_of(one)))
        for site, one in stated.get(ref.document, {}).items():
            if render.declared_at((one,), ref) and not render.declared_at((one,), ref, entries):
                excluded.add((name, site))

    assert unreachable == set(), sorted(unreachable)
    claimed("declarations the section boundary keeps off a pair", excluded)
    # **The other half, which is what keeps the exclusion from being a way to hide an
    # unprovable declaration**: every site kept off a pair is carried by a pair that CAN
    # put it to a draw, so one fact is still proved once.
    for name, site in sorted(excluded):
        where = owners.get(site, set())
        assert where, (name, site, "kept off every pair and carried by none")
        for owner, ref, _ in rows:
            if owner in where:
                one = stated[ref.document][site]
                if one.kind == UNDERDETERMINED:
                    continue
                assert harness._steps(
                    _relative(ref, one.pointer), schema_at(ref), _stated(ref)
                ) is not None, (owner, site)


def _relative(ref: SchemaRef, pointer: str) -> str:
    """``pointer`` read from ``ref``'s own node, exactly as the obligation reads it.

    ``harness.check_widening``'s own two lines, so this test asks the walk the question
    the obligation asks it and not a second spelling of it.
    """
    return "" if pointer == ref.pointer else pointer[len(ref.pointer.rstrip("/")) :]


def _stated(ref: SchemaRef) -> Any:
    """``ref``'s node AS THE DOCUMENT STATES IT, through the obligation's own derivation.

    The second half of the sentence above: a leading ``allOf`` index in a declaration's
    pointer is an index into the list the DOCUMENT states, and ``applied_schema`` splices
    the enclosing node's conjuncts in front of it at a union branch
    (``harness.node_as_stated``).  Asked here through that function and not re-derived, so
    this census ranges over the set the grade acts in -- which is
    ``docs/plan/architecture.md``'s "A READER DERIVES ITS KEY FROM THE ACCESSOR THE GRADE
    READS THROUGH" applied to the reader that decides whether the grade can reach a site.
    """
    return harness.node_as_stated(schema_at(SchemaRef(ref.document, "#")), ref.pointer)


def test_a_fact_is_declared_once_at_the_node_the_document_states_it() -> None:
    """**§8 sentence 2, decided 2026-11-03**: "a fact is declared ONCE, at the node the
    document STATES it, and never once per pointer the record inlines it to ... An
    approximation's identity is ``(stating document, stating pointer, keyword)``, and
    every inlined occurrence resolves to it."

    **THIS REPLACES THE OPPOSITE CLAUSE AND ITS TEST.**  What stood here asserted that a
    declaration TRAVELS -- a local reference moved it to the referring pointer and a
    remote one copied the target's to the referrer -- and §8 names that as the defect:
    "the record resolves references by copying, so a declaration per pointer turns a
    hundred-odd facts into tens of thousands and the declared set stops being readable".
    Measured over the 1,054 portable documents: the walk mints **37 declarations in 32
    documents** and the travelling rule reported **178 in 70**.  So the function is gone
    and :func:`emit.declared_once` is what a finished module's declaration set is.

    Three clauses, each one the rule's own:

    * a declaration the walk minted is KEPT at the pointer the walk minted it at, which
      is the pointer the document states the keyword at;
    * one identity is one entry, however many times the walk reaches it;
    * a declaration whose stating document is not this one belongs to that document's
      module and is dropped here (§8: "a fact is declared only by the STATING document's
      own module").
    """
    entry = approximate(_ref("#/definitions/versions"), "uniqueItems", Position.DEF, True)
    deeper = approximate(_ref("#/definitions/versions/items"), "pattern", Position.ELEM, "^a+$")

    kept = emit.declared_once(DOC, (entry, deeper))
    assert [one.pointer for one in kept] == [
        "#/definitions/versions",
        "#/definitions/versions/items",
    ]
    assert [one.keyword for one in kept] == ["uniqueItems", "pattern"]
    assert [one.fact for one in kept] == [True, "^a+$"]

    # ONE identity is ONE entry, and the FIRST of a repeat is the one kept, so the
    # document order section 6 depends on survives.
    assert emit.declared_once(DOC, (entry, entry, deeper)) == (entry, deeper)

    # A declaration of ANOTHER document is that document's module's and not this one's.
    theirs = Approximation(
        document="core/target.json",
        pointer="#/properties/tags",
        keyword="uniqueItems",
        kind=WIDENED,
        rung=Rung.KEYWORD.value,
        fact=True,
        attribution=keywords.address("uniqueItems"),
    )
    assert emit.declared_once(DOC, (theirs,)) == ()
    assert emit.declared_once(DOC, (entry, theirs)) == (entry,)


def test_the_identity_is_read_off_the_node_whose_keyword_the_fact_is() -> None:
    """**§8: "THE IDENTITY IS READ OFF THE NODE WHOSE KEYWORD THE FACT IS."**

    ``emit.stated_where_declared`` is that sentence as a gate: a declaration's pointer
    must name a node the document states its keyword at, or no obligation can discharge
    it -- ``harness.check_widening`` walks exactly that pointer into exactly that
    document.  The walk reads the document's own text, so the declaring handler's pointer
    IS the stating pointer; this is what makes that a measurement rather than an
    assumption, and ``emit.emit`` raises a ``BuildFailure`` on a sentence.

    The UNDERDETERMINED spelling is the one case where the pointer carries the keyword as
    its last segment -- ``lower.union`` declares at ``<stated_at>/<combinator>`` because
    the combinator is what is underdetermined -- and the node that states it is one
    segment up.
    """
    doc = {
        "type": "object",
        "properties": {"tags": {"type": "array", "uniqueItems": True}},
        "oneOf": [{"required": ["a"]}, {"required": ["b"]}],
    }
    at = approximate(
        _ref("#/properties/tags"), "uniqueItems", Position.PROP, True
    )
    assert emit.stated_where_declared(at, doc) is None

    # The union's own spelling: the pointer ends in the combinator and the node is up one.
    union = approximate(_ref("#/oneOf"), "oneOf", Position.ROOT, (), kind=UNDERDETERMINED)
    assert emit.stated_where_declared(union, doc) is None

    # A pointer naming no node of the document.
    missing = approximate(_ref("#/properties/gone"), "uniqueItems", Position.PROP, True)
    assert emit.stated_where_declared(missing, doc) == (
        "/properties/gone names no node of the document"
    )

    # A pointer naming a node that states no such keyword, which is the declaration
    # ``check_widening`` reports as "the document states no such keyword".
    silent = approximate(_ref("#/properties/tags"), "maxItems", Position.PROP, 3)
    assert emit.stated_where_declared(silent, doc) == (
        "the node at /properties/tags states no 'maxItems'"
    )

    # A pointer naming something that is not a schema at all.
    listed = approximate(_ref("#/type"), "uniqueItems", Position.PROP, True)
    assert emit.stated_where_declared(listed, doc) == (
        "/type names a str, not a schema"
    )


# --------------------------------------------------------------------------- #
# the widened pair the obligation is graded on, and the attribution it carries
# --------------------------------------------------------------------------- #
#: A document stating one fact the model below does not carry: section 5's ``uniqueItems``
#: row at the KEYWORD rung, which is the row section 5 names first.
WIDE_DOCUMENT = {
    "type": "object",
    "properties": {"tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}},
    "required": ["tags"],
    "additionalProperties": False,
}


# The model section 5's ``uniqueItems`` row widens to: ``list[str]``, no rule.
class Wide(AdCPBaseModel, extra="forbid"):
    __adcp_schema__: ClassVar[SchemaRef] = _ref()
    tags: list[str]


def _declaration_for_tags() -> Approximation:
    return approximate(
        _ref("#/properties/tags"), "uniqueItems", Position.PROP, True
    )


def test_an_attribution_the_registry_does_not_hold_is_a_defect() -> None:
    """Section 2: the attribution "is a choice of two and not a free-text note".

    The verifier's half of section 9's grader row, perturbed three ways: a note that is
    neither a cell address nor a registry entry, a rung outside section 2's ladder, and a
    kind outside its two.  Each is a declaration a reader would believe and no derivation
    supports.
    """
    good = _declaration_for_tags()
    assert harness.unattributed([good]) == []
    assert harness.unattributed([good._replace(attribution="because it was hard")]), "a note"
    assert harness.unattributed([good._replace(rung="MOSTLY")]), "a rung off the ladder"
    assert harness.unattributed([good._replace(kind="SORT_OF")]), "a kind off the pair"
    assert harness.unattributed(
        [good._replace(attribution="example/schema#1: unfiled")]
    ), "an upstream reference with no registry entry"


# --------------------------------------------------------------------------- #
# the ACCEPTS OBLIGATION: a widening is PROVED, not believed
# --------------------------------------------------------------------------- #
def test_the_accepts_obligation_passes_a_real_widening_and_fails_a_narrowing() -> None:
    """**Section 8's accepts obligation, and the perturbation that is its whole point.**

    "An approximation is a claim about this check, and this check is what proves it ... for
    every fact an approximation drops, the draw takes the values that keyword distinguishes
    -- the same coverage classes below -- and the class must accept every one of them.  An
    approximation that still refuses a value the document admits is a NARROWING wearing a
    declaration, and it fails here, by value and by pointer.  This is what keeps
    'approximated' from being an allowlist."

    The two models differ in one thing: ``Wide`` drops the ``uniqueItems`` rule and accepts
    everything the document's array admits, and ``Narrowed`` wears the SAME declaration
    while refusing a list of one member.  The declaration is identical, so the only thing
    that can tell them apart is the draw -- which is the claim.
    """
    one = _declaration_for_tags()
    proved = harness.check_widening(
        WIDE_DOCUMENT, Wide.model_validate, (one,), instances=({"tags": ["a", "b"]},)
    )
    assert proved.outcome == "pass", (proved.narrowings, proved.unproved)
    assert proved.accepted >= 1

    # A model wearing the SAME declaration and TIGHTER than its document: three members
    # at least, which the document does not ask for.
    class Narrowed(AdCPBaseModel, extra="forbid"):
        __adcp_schema__: ClassVar[SchemaRef] = _ref()
        tags: list[str] = Field(min_length=3)

    caught = harness.check_widening(
        WIDE_DOCUMENT, Narrowed.model_validate, (one,), instances=({"tags": ["a", "b"]},)
    )
    assert caught.outcome == "narrowing_wearing_a_declaration", (caught.narrowings, caught.unproved)
    assert "#/properties/tags/uniqueItems" in caught.narrowings[0]
    assert "2 distinct members" in caught.narrowings[0]
    assert "the class refuses it" in caught.narrowings[0]


#: **Row ``.10``'s LIVE NARROWING, and what this row's obligation measures about it.**
#: The epic's note: ``core/attestation-capabilities.json``, property
#: ``accepted_claim_types``: "the element states ``{"type":"string","format":"uri"}`` and
#: nothing about length, while the model's element carries ``minLength: 1, maxLength:
#: 2083``.  Those are pydantic ``HttpUrl``'s own bounds, which section 5's ``format`` row
#: brings in with the type, and they make the model NARROWER than its document."
#:
#: ``test_emit.py::test_an_arrays_bound_is_the_lists_and_not_its_elements`` is the
#: known-red test that documents it and row ``.10`` owns the fix.  This is the measurement
#: this row owes: does the accepts obligation CATCH it.
NARROWED = "core/attestation-capabilities.json"
NARROWED_AT = "#/properties/accepted_claim_types/items"


def test_the_accepts_obligation_catches_row_10s_live_narrowing() -> None:
    """**It does, by value and by pointer, and it finds three more of the same shape.**

    Measured through the PRODUCTION entry point -- ``strict_validate`` on the emitted
    class, against the document of record -- with the same declaration row ``.10`` would
    write when its ``format`` cell widens.  The obligation reports four narrowings where
    the document admits the value and the class refuses it:

    * ``urn:ietf:rfc:3986``, ``file:///tmp/a`` and ``mailto:a@example.com`` -- ``url_scheme``.
      These are the NAMED CEILING ``render.CONSTRAINTS_DOCSTRING`` already records:
      "``HttpUrl`` still refuses ``urn:`` and ``file:``, which is a named ceiling rather
      than an oversight."  The obligation does not know a ceiling from a defect and should
      not: it reports that the class refuses a value RFC 3986 admits, which is true of all
      four, and whose of the four are decided is the reading a row makes of the report.
    * a 2,220-character ``https`` URL -- ``url_too_long``, which is row ``.10``'s own
      defect and the one the known-red test is about.
    *
    **Why the ANSWER IS NOT A PASS TODAY, and this test is green anyway.**  The obligation
    fires only where a declaration claims something, and this row declares nothing: the
    ``format`` cell is unwidened, ``APPROXIMATED`` is 0, and the four narrowings are
    therefore not reported by any run.  What is asserted here is the INSTRUMENT: given the
    declaration row ``.10`` will write, the obligation refuses it.  So the answer row
    ``.10`` inherits is that it cannot declare this widening -- section 9's "an
    approximation that narrows is not an approximation ... Widen by another rung -- to
    ``Any`` if nothing else carries it -- rather than declaring the narrowing."

    **And the three classes the draw alone would never have reached is the whole of section
    8's covering rule.**  ``hypothesis_jsonschema`` honours ``format: uri`` and draws a
    short ``http://``, which the class accepts: the accepts check has been green on this
    node forever.  "A sampling draw reports only the values it drew -- so it can run green
    forever against a type that refuses a whole class of admissible value."
    """
    record = schema_at(SchemaRef(NARROWED, "#"))
    node = harness.at(record, NARROWED_AT[1:])
    assert node == {"format": "uri", "type": "string"}, node
    model = importlib.import_module(
        "adcp.types._schemas.core.attestation_capabilities"
    ).AttestationCapabilities

    drawn_from = harness.resolve(record, store={}, referrer=record)
    seen: list[Any] = []
    accepts = harness.check_accepts(
        drawn_from, model.strict_validate, examples=1, seen=seen, ref=SchemaRef(NARROWED, "#")
    )
    assert accepts.outcome == "pass", accepts.detail  # the SAMPLING draw is green
    assert seen, "the measurement needs one instance the document admits"

    declaration = approximate(SchemaRef(NARROWED, NARROWED_AT), "format", Position.ELEM, "uri")
    res = harness.check_widening(
        drawn_from, model.strict_validate, (declaration,), instances=seen[:1]
    )
    assert res.outcome == "narrowing_wearing_a_declaration", (res.unproved, res.narrowings)
    refused = {line.split(" -- ")[0].split(": ", 1)[1] for line in res.narrowings}
    assert refused == {
        "a URN (uri)",
        "a file URL (uri)",
        "a mailto URI (uri)",
        "a URL longer than 2,083 characters (uri)",
    }, sorted(refused)
    # Row ``.10``'s own defect, named by the pydantic error the epic's note names.
    assert [line for line in res.narrowings if "url_too_long" in line], res.narrowings
    # And the pointer is the element's and not the list's, which is what the known-red
    # test's own name is about.
    assert all(NARROWED_AT in line for line in res.narrowings), res.narrowings


def test_a_declaration_whose_classes_cannot_be_enumerated_is_unproved_and_not_a_pass() -> None:
    """Section 9: "A check is exhaustive over the set of nodes it claims, or it does not
    exist.  A check that enumerates a subset reports on that subset only, and says so."

    Three shapes reach it, and each is a widening nobody has proved rather than a pass: a
    pointer that describes no instance location, a keyword the document does not state at
    that pointer, and a keyword with no value-class derivation.
    """
    document = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "propertyNames": {"maxLength": 4},
        "minProperties": 1,
    }
    unplaceable = approximate(_ref("#/propertyNames"), "maxLength", Position.KEY, 4)
    res = harness.check_widening(document, lambda x: x, (unplaceable,), instances=({"name": "a"},))
    assert res.outcome == "unproved_widening"
    assert "describes no instance location" in res.unproved[0]

    absent = approximate(_ref("#/properties/name"), "maxLength", Position.PROP, 4)
    res = harness.check_widening(document, lambda x: x, (absent,), instances=({"name": "a"},))
    assert res.outcome == "unproved_widening"
    assert "states no such keyword" in res.unproved[0]

    assert harness.value_classes("frobnicate", {"frobnicate": 1}) == ()
    unrowed = approximate(_ref("#"), "frobnicate", Position.ROOT, 1)
    res = harness.check_widening(
        {**document, "frobnicate": 1}, lambda x: x, (unrowed,), instances=({"name": "a"},)
    )
    assert res.outcome == "unproved_widening"
    assert "no value class is derivable" in res.unproved[0]


def test_a_mapping_value_has_an_instance_location_and_the_key_is_drawn() -> None:
    """**§8: "Every position a widening can land at has an instance location."**

    "A mapping value -- ``#/properties/x/additionalProperties``, and the same for
    ``patternProperties``.  The location is ``x`` then any key the mapping admits; a key is
    a free choice and the draw makes one, so the location exists and simply was not read."

    Both halves are asserted, because a fixed key would satisfy the first and fail the
    second: 4 of the bundle's 5 mapping-valued widening sites state
    ``propertyNames: {"pattern": ...}``, so the key has to come off the document.  The
    perturbation is the document's own key constraint -- the obligation PASSES where the
    drawn key matches it and reports ``unproved`` where no key can be drawn at all.
    """
    patterned = {
        "type": "object",
        "properties": {
            "scopes": {
                "type": "object",
                "propertyNames": {"pattern": "^[A-Z]{2}$"},
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
            }
        },
    }

    class Mapped(AdCPBaseModel, extra="forbid"):
        __adcp_schema__: ClassVar[SchemaRef] = _ref()
        scopes: dict[str, list[str]] | None = None

    at = "#/properties/scopes/additionalProperties"
    one = approximate(_ref(at), "uniqueItems", Position.MAPV, True)
    # The location is the property then a key the mapping admits, and the key MATCHES.
    path = harness.instance_path(at, patterned)
    assert path, at
    property_segment, key = path
    assert property_segment == "scopes"
    assert harness.conforms({"type": "string", "pattern": "^[A-Z]{2}$"}, key) is not False

    proved = harness.check_widening(
        patterned, Mapped.model_validate, (one,), instances=({"scopes": {}},)
    )
    assert proved.outcome == "pass", (proved.narrowings, proved.unproved)
    assert proved.accepted >= 1

    # **The perturbation, and it is the key and not the pointer**: with no schema to read
    # the key constraint off, the pointer has no location and the widening is unproved
    # rather than placed somewhere the document refuses.
    assert harness.instance_path(at) == ("scopes", harness._ALIEN_KEY)
    unreadable = {
        **patterned,
        "properties": {
            "scopes": {
                **patterned["properties"]["scopes"],
                "propertyNames": {"pattern": "^[A-Z]{2}$", "maxLength": 1},
            }
        },
    }
    assert harness.instance_path(at, unreadable) is None
    blind = harness.check_widening(
        unreadable, Mapped.model_validate, (one,), instances=({"scopes": {}},)
    )
    assert blind.outcome == "unproved_widening"
    assert "describes no instance location" in blind.unproved[0]

    # A ``definitions`` entry still has none, and §8 says it needs none: the rule that a
    # declaration travels with the fact re-points it to the referring pointer first.
    assert harness.instance_path("#/definitions/versions", patterned) is None


def test_an_underdetermined_declaration_is_not_claimed_by_the_accepts_obligation() -> None:
    """Section 2: an UNDERDETERMINED approximation is one "No draw or dump can see", so
    claiming it here would report a pass this check cannot earn.

    Its instrument is the disjointness equality below, and section 8 says so: "that is why
    it needs an instrument of its own."
    """
    invisible = approximate(
        _ref("#/oneOf"), "oneOf", Position.ROOT, [{}, {}], kind=UNDERDETERMINED
    )
    res = harness.check_widening(
        WIDE_DOCUMENT, Wide.model_validate, (invisible,), instances=({"tags": ["a"]},)
    )
    assert res.declarations == 0
    assert res.outcome == "no_declarations"


def test_the_value_classes_cover_the_three_families_section_8_names() -> None:
    """Section 8: "For each keyword the node states, the draw takes the classes that
    keyword distinguishes: every member of an ``enum``, both sides of each bound and the
    bound itself, and for a ``format`` every shape the format's own checker admits rather
    than the shape a generator finds most likely."

    All three families, plus the direction that matters most: a bound's second class is
    DROPPED where the node's other bound forbids it, because a value the document refuses
    says nothing about the class.
    """
    assert [label for label, _ in harness.value_classes("enum", {"enum": ["a", "b", "c"]})] == [
        "enum member 'a'",
        "enum member 'b'",
        "enum member 'c'",
    ]
    bound = harness.value_classes("minLength", {"type": "string", "minLength": 3})
    assert [label for label, _ in bound] == [
        "minLength exactly (3)",
        "minLength one step inside (4)",
    ]
    pinned = harness.value_classes(
        "minLength", {"type": "string", "minLength": 3, "maxLength": 3}
    )
    assert [label for label, _ in pinned] == ["minLength exactly (3)"]
    assert len(harness.value_classes("format", {"type": "string", "format": "uri"})) == len(
        harness.FORMAT_SHAPES["uri"]
    )


def test_every_format_shape_is_one_the_drafts_own_checker_admits() -> None:
    """The table's own claim, asserted against the checker rather than taken on trust.

    A shape the checker refuses is a value the DOCUMENT refuses, so offering it to a class
    would report a narrowing where the schema half had already said no -- which is the
    vacuous FAILURE that mirrors the vacuous pass.
    """
    for fmt, shapes in harness.FORMAT_SHAPES.items():
        node = {"type": "string", "format": fmt}
        for label, value in shapes:
            assert harness.conforms(node, value, validator_cls=harness.validator_for(node)) is not (
                False
            ), f"{fmt}: {label} -> {value[:60]!r} is refused by the draft's own checker"


def test_the_format_shapes_cover_every_format_that_selects_a_python_type() -> None:
    """``FORMAT_SHAPES``'s population is ``lower.scalars.FORMAT_TYPES``, derived.

    A selected type brings its own constraints with it -- which is the whole mechanism of
    row ``.10``'s live narrowing -- so a fourth format that selects one arrives here with
    its shapes or reddens.  Read off the walk's declaration in a TEST, which may import
    both halves where section 9 forbids the verifier itself.
    """
    from codegen.lower.scalars import FORMAT_TYPES

    assert set(harness.FORMAT_SHAPES) == set(FORMAT_TYPES), (
        set(FORMAT_TYPES) ^ set(harness.FORMAT_SHAPES)
    )


# --------------------------------------------------------------------------- #
# the UNDERDETERMINED equality
# --------------------------------------------------------------------------- #
#: Two branches an instance can satisfy at once: both open, each requiring a name the other
#: does not declare, so neither forbids anything.  ``tests/test_union_disjointness.py``
#: carries the same shape for the walk's side of the derivation.
OVERLAPPING = {
    "type": "object",
    "oneOf": [
        {"properties": {"a": {"type": "string"}}, "required": ["a"]},
        {"properties": {"b": {"type": "string"}}, "required": ["b"]},
    ],
}

#: The same two branches, CLOSED: each forbids the name the other requires.
SEPARATED = {
    "type": "object",
    "oneOf": [
        {
            "properties": {"a": {"type": "string"}},
            "required": ["a"],
            "additionalProperties": False,
        },
        {
            "properties": {"b": {"type": "string"}},
            "required": ["b"],
            "additionalProperties": False,
        },
    ],
}


def test_the_verifiers_own_derivation_separates_the_pairs_section_4_separates() -> None:
    """A SECOND spelling of ``lower.union.separates``, over the document, and section 9's
    reason: "One body of code deciding what the model states and what the document states
    agrees with itself by construction, so a defect in it is green on BOTH sides."

    All three of section 4's separators, each on a constructed pair, and the overlapping
    case beside each so the derivation is not green for free.

    **The first separator reads SETS and is gated on PRESENCE (2026-10-29,**
    ``adcp-client-python-10l.102``).  So the ``required`` is part of every pair below and
    not decoration: the pair that drops it is the one asserting the gate.
    """
    assert harness.inseparable_unions(OVERLAPPING) == ("#/oneOf",)
    assert harness.inseparable_unions(SEPARATED) == ()

    def union(*branches: dict, required: list[str] | None = None) -> dict:
        node = {"type": "object", "oneOf": list(branches)}
        return node if required is None else {**node, "required": required}

    def pins(value: dict, required: bool = True) -> dict:
        branch: dict = {"properties": {"kind": value}}
        return {**branch, "required": ["kind"]} if required else branch

    # Disjoint sets separate, in all four spellings section 4 names -- a one-member set
    # against a one-member set (which is the single-value reading this generalises), a
    # multi-member set against either, and a set against the COMPLEMENT of a set that
    # contains it.
    for one, other in (
        (pins({"const": "a"}), pins({"enum": ["b"]})),
        (pins({"enum": ["a", "b"]}), pins({"const": "c"})),
        (pins({"enum": ["a", "b"]}), pins({"enum": ["c", "d"]})),
        (pins({"const": "a"}), pins({"not": {"enum": ["a", "b"]}})),
    ):
        assert harness.inseparable_unions(union(one, other)) == (), (one, other)
        assert harness.inseparable_unions(union(other, one)) == (), (one, other)

    # Sets that INTERSECT do not, and nor do two complements: whether their two finite
    # excluded sets cover the value space is not something the branches state.
    for one, other in (
        (pins({"const": "a"}), pins({"const": "a"})),
        (pins({"enum": ["a", "b"]}), pins({"enum": ["b", "c"]})),
        (pins({"enum": ["a", "b"]}), pins({"not": {"enum": ["b"]}})),
        (pins({"not": {"enum": ["a"]}}), pins({"not": {"enum": ["b"]}})),
    ):
        assert harness.inseparable_unions(union(one, other)) == ("#/oneOf",), (one, other)

    # **THE PRESENCE GATE.**  A ``properties`` entry says nothing about an instance that
    # omits the key, so two branches naming disjoint sets for a key neither requires are
    # both satisfied by ``{}`` -- and section 4's "a pair the derivation cannot separate
    # is treated as overlapping" is the answer.  Satisfied either by a BRANCH requiring
    # the key or by the ROOT requiring it of every branch, which is the form the bundle
    # uses: 19,520 of the 70,446 pairs this arm separates get presence from the root
    # alone.
    bare = (pins({"const": "a"}, required=False), pins({"enum": ["b"]}, required=False))
    assert Draft7Validator({"type": "object", **bare[0]}).is_valid({})
    assert harness.inseparable_unions(union(*bare)) == ("#/oneOf",), bare
    assert harness.inseparable_unions(union(*bare, required=["kind"])) == (), bare
    assert harness.inseparable_unions(union(pins({"const": "a"}), bare[1])) == ()


def _at(record: dict) -> dict:
    """``{DOC: (record, origins)}``, which is what ``underdetermined_census`` takes.

    **§8 sentence 2 makes both sides of that equality sets of the IDENTITY** ``(stating
    document, stating pointer)``, so the derived side is read through ``origins`` and an
    inlined occurrence resolves to the site it states.  These probe records have no
    reference in them, so every node states itself and the map is the identity on them --
    built by a walk here rather than by ``bundle.recorded`` because the point of the probe
    is the derivation and not the inliner.
    """
    return {DOC: (record, {id(node): (DOC, pointer) for pointer, node in bundle.nodes(record)})}


def test_the_underdetermined_set_equals_the_inseparable_set_in_both_directions() -> None:
    """**Section 8's UNDERDETERMINED equality, and each direction perturbed.**

    "Its check is section 4's disjointness derivation: **the set of unions declaring one
    equals the set the derivation cannot separate**, in both directions, so a union that
    becomes separable loses its declaration and a union that stops being separable gains
    one."

    Four states: declared and inseparable (equal); declared and separable (a declaration
    the union no longer needs); inseparable and undeclared (a value decided by declaration
    order with nothing saying so); and neither.
    """
    declaration = approximate(
        _ref("#/oneOf"), "oneOf", Position.ROOT, OVERLAPPING["oneOf"], kind=UNDERDETERMINED
    )
    stale, silent = harness.underdetermined_census((declaration,), _at(OVERLAPPING))
    assert (stale, silent) == ([], [])

    stale, silent = harness.underdetermined_census((declaration,), _at(SEPARATED))
    assert len(stale) == 1 and "the derivation separates it" in stale[0]
    assert silent == []

    stale, silent = harness.underdetermined_census((), _at(OVERLAPPING))
    assert stale == []
    assert len(silent) == 1 and "nothing declares it" in silent[0]

    assert harness.underdetermined_census((), _at(SEPARATED)) == ([], [])


def test_a_widened_declaration_is_not_read_as_an_underdetermined_one() -> None:
    """Section 2: the two kinds "are never summed", and the equality ranges over one of them.

    A ``WIDENED`` declaration at a union's pointer is a different claim about a different
    thing -- a fact the annotation does not carry -- so counting it here would make a union
    look declared that nothing declared.
    """
    widened = approximate(_ref("#/oneOf"), "oneOf", Position.ROOT, OVERLAPPING["oneOf"])
    assert widened.kind == WIDENED
    stale, silent = harness.underdetermined_census((widened,), _at(OVERLAPPING))
    assert stale == []
    assert len(silent) == 1
