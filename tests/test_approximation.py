"""The approximation INSTRUMENT, and the proof that each half fails when it should.

``docs/plan/architecture.md`` section 14 step 8 is "the approximation, end to end, with no
cell widened", and that exit condition is what makes this file necessary rather than
optional: with ``APPROXIMATED`` at 0 over the whole bundle, every check the step adds is
green over an empty set, and an instrument graded over an empty set is graded by nothing.
So every arm here is exercised on a CONSTRUCTED pair -- a hand-written class, a hand-built
declaration, and a document the two are compared against -- and each clause is asserted in
BOTH directions: it catches the defect it is for, and it does not fire on the faithful
case beside it.

``docs/plan/rebuild-plan.md`` section 8 names the two set equalities and says why they are
the whole of this row:

1. "The comparison's keyword set equals the set the declaration renders."  Held by
   ``tests/test_every_check_names_its_set.py`` over ``keywords.rendered_at``, which is
   where a set equality between two derivations belongs; this file does not restate it.
2. "**The approximated set equals the declared set.**  Every *approximated* fact has a
   declaration (or it is *missing*), and every declaration has an *approximated* fact (or
   it is *over-declared*).  Both directions, for the reason the first equality has them: a
   set checked in one direction is complete with respect to itself, and what it omits
   passes."

Section 8 also says what stops the second from being an allowlist, and it is the accepts
obligation: "Nobody can add an entry to make a failure go away without the model actually
widening at that pointer, because the accepts draw then has to accept the values the
keyword distinguishes.  A declaration is a claim with two instruments pointed at it."  Both
instruments are perturbed here.
"""

from __future__ import annotations

import importlib
from typing import Any, ClassVar

import pytest
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
from codegen import attribution, bundle, compiler, emit, harness, ir, keywords, render
from codegen.harness import Pair
from codegen.keywords import Effect, Position, Rung
from codegen.lower.approximate import approximate, attribution_for, declare, rung_for
from codegen.refusal import BuildFailure

DOC = "core/probe.json"


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


def test_a_position_override_for_a_rung_renders_no_grid_clause() -> None:
    """The two CONJ overrides must not move the generated grids, and here is why they do not.

    ``keywords.py``'s own rule: "An override whose ``compiles`` is EMPTY renders no clause:
    it records a cell the default sentence already covers in prose."
    ``tests/test_keywords.py`` holds the grids themselves; this asserts the mechanism the
    two overrides rely on, so a later row cannot give one a sentence and silently change
    the committed document.
    """
    for keyword in ("type", "enum"):
        assert keywords.TABLE[keyword].at[Position.CONJ].compiles == ""


def test_a_rung_cannot_be_asked_of_a_cell_that_states_no_fact() -> None:
    """Section 3: "a handler that asks for one is a ``BuildFailure``".

    "The keyword states no fact, so a widening against it would be a declaration with
    nothing to declare, and section 8 would report it as *over-declared* forever."
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
    assert keywords.address("errorMessage") == f"{keywords.DOCUMENT} §7 refused/errorMessage"
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
        attribution.Issue("adcontextprotocol/adcp#1", "   ")
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
    exec(compile(text, "<probe>", "exec"), namespace)  # noqa: S102 -- the artifact is the subject
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
    """Section 7: "*Where it must NOT go.*  Not into ``Field(json_schema_extra=...)``.
    That would put the approximation into ``model_json_schema()``, where section 8 of the
    semantics document would read it as a fact the model states and the document does not
    -- *added*, a defect.  The declaration is a class attribute precisely because it has to
    be invisible to the comparison's own subject and visible to the comparison."

    Asserted on the rendered class's own schema, which is the comparison's subject: the
    attribute is reachable on the CLASS and absent from ``model_json_schema()`` at every
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

    A pair's comparison descends from its own node into the whole subtree, so a fact at
    ``#/properties/x/maxLength`` is reported by the root pair as well as by the nested
    class's own pair; a declaration carried only by the nearest enclosing class would leave
    the root pair reporting it *missing*.
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


def _edge(pointer: str, *, local: bool, target: str | None, into: str) -> bundle.Edge:
    """One reference site, as ``bundle.edges`` records it."""
    return bundle.Edge(
        document=DOC,
        pointer=pointer,
        position=Position.PROP,
        uri=("#" + into) if local else f"https://example/{target}#{into}",
        local=local,
        target=None if local else target,
        into=into,
        conjunct_of_root=False,
    )


def test_a_declaration_travels_with_the_fact_it_is_about() -> None:
    """**§8, decided 2026-10-27**: "a reference carries its target's declarations to the
    referring pointer, re-pointed by the same resolution that carried the facts."

    "The second equality compares two sets of ``(pointer, keyword)`` pairs, so it holds
    only while both sides agree on the pointer -- and they do not, by default.  A
    declaration is minted at the NODE's pointer; the comparison reports a fact at the
    pointer it WALKED."

    **The two resolutions move a declaration differently and each one's own behaviour is
    what decides it**, which is the whole of what is asserted here:

    * a LOCAL reference is resolved by REPLACING the referring node with its target, so the
      declaration MOVES -- an entry left at ``#/definitions/x`` is a declaration no pair
      reaches, which §8 reports as *over-declared*;
    * a REMOTE one is inlined by ``bundle.record`` as a deep COPY, so the declaration is
      COPIED and the target document keeps its own for its own pairs.
    """
    entry = approximate(_ref("#/definitions/versions"), "uniqueItems", Position.DEF, True)
    deeper = approximate(_ref("#/definitions/versions/items"), "pattern", Position.ELEM, "^a+$")
    local = _edge("/properties/versions", local=True, target=None, into="/definitions/versions")

    moved = emit.repointed(DOC, (entry, deeper), (local,), {})
    assert [one.pointer for one in moved] == [
        "#/properties/versions",
        "#/properties/versions/items",
    ]
    # The suffix below the fragment is kept exactly, and so is the fact and the rung.
    assert [one.keyword for one in moved] == ["uniqueItems", "pattern"]
    assert [one.fact for one in moved] == [True, "^a+$"]
    assert all(one.document == DOC for one in moved)
    # MOVED and not copied: the entry's own pointer is gone, because the normalisation
    # replaced the node and no pair reads the entry.
    assert "#/definitions/versions" not in {one.pointer for one in moved}

    # Two references to ONE entry carry it to BOTH, because both pointers are walked.
    twice = emit.repointed(
        DOC,
        (entry,),
        (local, _edge("/properties/also", local=True, target=None, into="/definitions/versions")),
        {},
    )
    assert {one.pointer for one in twice} == {"#/properties/versions", "#/properties/also"}

    # A REMOTE reference COPIES, and the target keeps its own -- it emits its own module
    # and its own pairs grade it there.
    target = "core/target.json"
    theirs = Approximation(
        document=target,
        pointer="#/properties/tags",
        keyword="uniqueItems",
        kind=WIDENED,
        rung=Rung.KEYWORD.value,
        fact=True,
        attribution=keywords.address("uniqueItems"),
    )
    carried = emit.repointed(
        DOC,
        (),
        (_edge("/properties/held", local=False, target=target, into=""),),
        {target: (theirs,)},
    )
    assert [(one.document, one.pointer) for one in carried] == [
        (DOC, "#/properties/held/properties/tags")
    ]
    # A FRAGMENT reference re-points off the fragment and not off the root.
    fragment = emit.repointed(
        DOC,
        (),
        (_edge("/properties/held", local=False, target=target, into="/properties/tags"),),
        {target: (theirs,)},
    )
    assert [one.pointer for one in fragment] == ["#/properties/held"]
    # A target that REFUSED has no module and contributes nothing.
    assert emit.repointed(
        DOC, (), (_edge("/properties/held", local=False, target=target, into=""),), {}
    ) == ()
    # And a declaration outside the fragment does not travel: the resolution carried the
    # node at the fragment and nothing else.
    assert emit.repointed(
        DOC,
        (),
        (_edge("/properties/held", local=False, target=target, into="/properties/other"),),
        {target: (theirs,)},
    ) == ()


# --------------------------------------------------------------------------- #
# EQUALITY TWO, direction one: a decided widening is *approximated* and not *missing*
# --------------------------------------------------------------------------- #
#: A document stating one fact the model below does not carry: section 5's ``uniqueItems``
#: row at the KEYWORD rung, which is the row section 5 names first.
WIDE_DOCUMENT = {
    "type": "object",
    "properties": {"tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}},
    "required": ["tags"],
    "additionalProperties": False,
}


# The model section 5's ``uniqueItems`` row widens to: ``list[str]``, no rule.  No
# docstring on any probe class here, and that is load-bearing rather than terse: pydantic
# renders one as ``description`` and the comparison would then report an ``added`` fact of
# the test's own making, which would redden every clause below for the wrong reason.
class Wide(AdCPBaseModel, extra="forbid"):
    __adcp_schema__: ClassVar[SchemaRef] = _ref()
    tags: list[str]


def _declaration_for_tags() -> Approximation:
    return approximate(
        _ref("#/properties/tags"), "uniqueItems", Position.PROP, True
    )


def test_an_undeclared_widening_is_missing_and_a_declared_one_is_approximated() -> None:
    """**Section 8's fifth outcome, and the perturbation that proves the split.**

    "*missing* keeps its old meaning exactly -- the document states a compared fact, the
    model does not, and nothing declares it -- and it is the only one of the six that the
    directive leaves as a defect in the undeclared direction.  So the directive does not
    loosen this check; it moves its subject from 'is the fact there' to 'is its absence
    declared, attributed and proved wide'."

    Both directions on ONE model and ONE document, so the only variable is the
    declaration: with none the fact is *missing* and the pair reddens; with one it is
    *approximated* and the pair passes with the figure reported.
    """
    bare = harness.compare_schema(WIDE_DOCUMENT, Wide)
    assert [m for m in bare.missing if "uniqueItems" in m], bare.missing
    assert bare.approximated == []
    assert bare.outcome == "model_drops_a_fact"

    declared = harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(_declaration_for_tags(),))
    assert declared.missing == [], declared.missing
    assert len(declared.approximated) == 1, declared.approximated
    assert "rung KEYWORD" in declared.approximated[0]
    assert keywords.address("uniqueItems") in declared.approximated[0]
    assert declared.approximated_at == [(DOC, "#/properties/tags", "uniqueItems")]
    assert declared.outcome == "pass"


def test_a_declaration_at_another_pointer_does_not_excuse_this_one() -> None:
    """The declaration is keyed by POINTER and keyword, so it excuses one site and no other.

    Without this the split would be a keyword-level allowlist, which is exactly what
    section 8's second equality exists to prevent: "an allowlist is a set a human writes
    and a check consults."
    """
    elsewhere = approximate(_ref("#/properties/other"), "uniqueItems", Position.PROP, True)
    res = harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(elsewhere,))
    assert [m for m in res.missing if "uniqueItems" in m], res.missing
    assert res.approximated == []


def test_a_declaration_is_rebased_onto_the_pairs_own_pointer() -> None:
    """A nested pair's comparison reports a pair-relative pointer and a declaration carries
    an absolute one, so the two meet by subtracting the pair's own pointer.

    Asserted by grading the SAME node as a nested pair: the declaration is unchanged and
    the ``at`` is what moves, so a mistake in the rebasing shows as the fact going
    *missing*.
    """
    node = WIDE_DOCUMENT["properties"]["tags"]
    declared = (approximate(_ref("#/properties/tags"), "uniqueItems", Position.PROP, True),)
    rebased = harness.compare_schema(
        node, list[str], declared=declared, at="#/properties/tags", position=Position.PROP
    )
    assert rebased.approximated_at == [(DOC, "#/properties/tags", "uniqueItems")]
    # And with the wrong base the fact is *missing*, which is what the rebasing buys.
    wrong = harness.compare_schema(
        node, list[str], declared=declared, at="#", position=Position.PROP
    )
    assert wrong.approximated == []
    assert [m for m in wrong.missing if "uniqueItems" in m], wrong.missing


# --------------------------------------------------------------------------- #
# EQUALITY TWO, direction two: a declaration the model does not need is OVER-DECLARED
# --------------------------------------------------------------------------- #
# The same document, rendered FAITHFULLY: the ``uniqueItems`` fact is stated.
class Faithful(AdCPBaseModel, extra="forbid"):
    __adcp_schema__: ClassVar[SchemaRef] = _ref()
    tags: list[str] = Field(json_schema_extra={"uniqueItems": True})


def test_a_declaration_the_model_does_not_need_is_over_declared() -> None:
    """**Section 8's sixth outcome, and the perturbation that proves it.**

    "***over-declared*** -- an approximation is declared at a pointer and keyword where the
    model DOES state the fact.  A defect, and the mirror of *missing*.  Without it the
    declarations rot: a cell gets written, the widening stops happening, the declaration
    stays, and it then hides the next real gap at the same pointer behind a stale excuse."

    The perturbation is the row LANDING: the faithful model states the fact the widened one
    dropped, and the declaration is the one left behind.  Both directions on one model: with
    the stale declaration the pair reddens, without it the pair passes.
    """
    assert harness.compare_schema(WIDE_DOCUMENT, Faithful).outcome == "pass"
    stale = harness.compare_schema(
        WIDE_DOCUMENT, Faithful, declared=(_declaration_for_tags(),)
    )
    assert len(stale.over_declared) == 1, stale.over_declared
    assert "outlives its widening" in stale.over_declared[0]
    assert stale.outcome == "declaration_outlived_its_widening"
    assert stale.approximated == []


def test_a_declaration_for_a_fact_the_document_does_not_state_is_over_declared_too() -> None:
    """Section 9: "**Never approximate on a keyword the walk itself inserted.**  An
    approximation must name something the document states, or the document is blamed for
    the compiler's own rewriting -- and the declaration then cannot be checked, because
    section 8 looks for the fact in the document and does not find it."

    Here the model states a bound its document does not, which the comparison already
    reports as *added*; the declaration beside it names a fact the document never stated,
    so it is over-declared as well -- and the two lines say different things to a reader.
    """
    document = {"type": "object", "properties": {"name": {"type": "string"}}}

    class Narrow(AdCPBaseModel):
        __adcp_schema__: ClassVar[SchemaRef] = _ref()
        name: str = Field(max_length=10)

    invented = approximate(_ref("#/properties/name"), "maxLength", Position.PROP, 10)
    res = harness.compare_schema(document, Narrow, declared=(invented,))
    assert [a for a in res.added if "maxLength" in a], res.added
    assert len(res.over_declared) == 1, res.over_declared


# --------------------------------------------------------------------------- #
# the RUN-LEVEL equality, which is the one that cannot be complete with respect to itself
# --------------------------------------------------------------------------- #
def _pair(model: Any, declared: tuple[Approximation, ...], *, ref: SchemaRef | None = None) -> Pair:
    ref = ref or _ref()
    return Pair(
        name=f"{ref.document}{ref.pointer}",
        schema=WIDE_DOCUMENT,
        model=model,
        accept=model.strict_validate if hasattr(model, "strict_validate") else model,
        document=WIDE_DOCUMENT,
        ref=ref,
        declared=declared,
    )


def _report(comparison: harness.ComparisonResult) -> harness.PairReport:
    return harness.PairReport(name="probe", comparison=comparison)


def test_the_declared_set_equals_the_approximated_set_in_both_directions() -> None:
    """**Section 8's second equality, over the run, and each direction perturbed.**

    "Every *approximated* fact has a declaration (or it is *missing*), and every
    declaration has an *approximated* fact (or it is *over-declared*).  Both directions,
    for the reason the first equality has them: a set checked in one direction is complete
    with respect to itself, and what it omits passes."

    Three states of ONE pair:

    * the widened model with its declaration -- the sets are equal and the census passes;
    * the FAITHFUL model with the declaration left behind -- the declared set is bigger,
      and the pair's own comparison says why (*over-declared*);
    * a declaration at a pointer no pair's comparison reaches -- the declared set is bigger
      and NO pair reports anything, which is the hole a one-directional check leaves and
      the direction this equality closes.
    """
    one = _declaration_for_tags()
    equal = harness.census(
        [(_pair(Wide, (one,)), _report(harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(one,))))]
    )
    assert equal.outcome == "pass"
    assert set(equal.declared) == equal.approximated == {(DOC, "#/properties/tags", "uniqueItems")}
    assert equal.documents == 1

    stale = harness.census(
        [
            (
                _pair(Faithful, (one,)),
                _report(harness.compare_schema(WIDE_DOCUMENT, Faithful, declared=(one,))),
            )
        ]
    )
    assert stale.outcome != "pass"
    assert stale.over_declared, stale
    assert stale.stale == [(DOC, "#/properties/tags", "uniqueItems")]
    assert stale.undeclared_widenings, stale

    # The hole a one-directional check leaves: a declaration at a pointer the comparison
    # never visits is neither *approximated* nor *over-declared* at any pair, so only the
    # run-level set difference can see it.
    unreached = approximate(_ref("#/definitions/dead"), "uniqueItems", Position.DEF, True)
    nowhere = harness.census(
        [
            (
                _pair(Wide, (one, unreached)),
                _report(harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(one, unreached))),
            )
        ]
    )
    assert nowhere.outcome != "pass"
    assert nowhere.stale == [(DOC, "#/definitions/dead", "uniqueItems")]
    assert nowhere.over_declared == [], nowhere.over_declared
    assert "no pair graded that pointer" in nowhere.undeclared_widenings[0]


def test_an_underdetermined_declaration_is_not_stale_for_being_invisible() -> None:
    """Section 8 exempts the one kind no comparison can report, and this holds that.

    "An UNDERDETERMINED approximation (section 2) is invisible to all three checks, and
    that is why it needs an instrument of its own ... The comparison matches, the draw
    accepts and the dump validates, because the annotation admits exactly what the
    document admits."

    :func:`harness.census` is computed FROM the comparison's output, so a kind the
    comparison cannot report could never enter its *approximated* half.  Read without the
    exemption, every UNDERDETERMINED declaration is *over-declared* at every pair forever
    -- which is the one kind section 8 removes from that outcome by name, and the kind
    whose own instrument (:func:`harness.underdetermined_census`) holds it in both
    directions instead.

    **Both directions, and the second is what keeps the exemption from being a hole**: a
    WIDENED declaration at the SAME pointer that no pair reports is still stale, so the
    exemption is about the KIND and not about the pointer.  ``check_widening`` already
    draws this exact line one function away, with this same sentence of section 8 quoted
    at it.
    """
    invisible = approximate(
        _ref("#/oneOf"), "oneOf", Position.ROOT, OVERLAPPING["oneOf"], kind=UNDERDETERMINED
    )
    exempt = harness.census(
        [
            (
                _pair(Wide, (invisible,)),
                _report(harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(invisible,))),
            )
        ]
    )
    assert exempt.stale == [], exempt.stale
    assert exempt.undeclared_widenings == [], exempt.undeclared_widenings
    assert exempt.outcome == "pass", exempt
    # It is still DECLARED, so the figures and the UNDERDETERMINED equality both see it:
    # the exemption is from the *over-declared* outcome and from nothing else.
    assert set(exempt.declared) == {(DOC, "#/oneOf", "oneOf")}
    assert exempt.documents == 1

    # The same pointer, the other kind: a WIDENED declaration no pair reports is stale.
    # Without this the exemption could be read as "a declaration at a combinator is
    # excused", which is a hole of the shape the first direction of this equality closes.
    widened = invisible._replace(kind=WIDENED)
    not_exempt = harness.census(
        [
            (
                _pair(Wide, (widened,)),
                _report(harness.compare_schema(WIDE_DOCUMENT, Wide, declared=(widened,))),
            )
        ]
    )
    assert not_exempt.stale == [(DOC, "#/oneOf", "oneOf")], not_exempt.stale
    assert not_exempt.outcome != "pass"


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
        [good._replace(attribution="adcontextprotocol/adcp#1: unfiled")]
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
        WIDE_DOCUMENT, Wide.model_validate, (one,), instance={"tags": ["a", "b"]}
    )
    assert proved.outcome == "pass", (proved.narrowings, proved.unproved)
    assert proved.accepted >= 1

    # A model wearing the SAME declaration and TIGHTER than its document: three members
    # at least, which the document does not ask for.
    class Narrowed(AdCPBaseModel, extra="forbid"):
        __adcp_schema__: ClassVar[SchemaRef] = _ref()
        tags: list[str] = Field(min_length=3)

    caught = harness.check_widening(
        WIDE_DOCUMENT, Narrowed.model_validate, (one,), instance={"tags": ["a", "b"]}
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
        drawn_from, model.strict_validate, (declaration,), instance=seen[0]
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
    res = harness.check_widening(document, lambda x: x, (unplaceable,), instance={"name": "a"})
    assert res.outcome == "unproved_widening"
    assert "describes no instance location" in res.unproved[0]

    absent = approximate(_ref("#/properties/name"), "maxLength", Position.PROP, 4)
    res = harness.check_widening(document, lambda x: x, (absent,), instance={"name": "a"})
    assert res.outcome == "unproved_widening"
    assert "states no such keyword" in res.unproved[0]

    assert harness.value_classes("frobnicate", {"frobnicate": 1}) == ()
    unrowed = approximate(_ref("#"), "frobnicate", Position.ROOT, 1)
    res = harness.check_widening(
        {**document, "frobnicate": 1}, lambda x: x, (unrowed,), instance={"name": "a"}
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
        patterned, Mapped.model_validate, (one,), instance={"scopes": {}}
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
        unreadable, Mapped.model_validate, (one,), instance={"scopes": {}}
    )
    assert blind.outcome == "unproved_widening"
    assert "describes no instance location" in blind.unproved[0]

    # A ``definitions`` entry still has none, and §8 says it needs none: the rule that a
    # declaration travels with the fact re-points it to the referring pointer first.
    assert harness.instance_path("#/definitions/versions", patterned) is None


def test_an_underdetermined_declaration_is_not_claimed_by_the_accepts_obligation() -> None:
    """Section 2: an UNDERDETERMINED approximation is one "No comparison, draw or dump can
    see", so claiming it here would report a pass this check cannot earn.

    Its instrument is the disjointness equality below, and section 8 says so: "that is why
    it needs an instrument of its own."
    """
    invisible = approximate(
        _ref("#/oneOf"), "oneOf", Position.ROOT, [{}, {}], kind=UNDERDETERMINED
    )
    res = harness.check_widening(
        WIDE_DOCUMENT, Wide.model_validate, (invisible,), instance={"tags": ["a"]}
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
    """
    assert harness.inseparable_unions(OVERLAPPING) == ("#/oneOf",)
    assert harness.inseparable_unions(SEPARATED) == ()
    pinned = {
        "type": "object",
        "oneOf": [
            {"properties": {"kind": {"const": "a"}}},
            {"properties": {"kind": {"enum": ["b"]}}},
        ],
    }
    assert harness.inseparable_unions(pinned) == ()
    same_pin = {
        "type": "object",
        "oneOf": [
            {"properties": {"kind": {"const": "a"}}},
            {"properties": {"kind": {"const": "a"}}},
        ],
    }
    assert harness.inseparable_unions(same_pin) == ("#/oneOf",)


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
    stale, silent = harness.underdetermined_census((declaration,), {DOC: OVERLAPPING})
    assert (stale, silent) == ([], [])

    stale, silent = harness.underdetermined_census((declaration,), {DOC: SEPARATED})
    assert len(stale) == 1 and "the derivation separates it" in stale[0]
    assert silent == []

    stale, silent = harness.underdetermined_census((), {DOC: OVERLAPPING})
    assert stale == []
    assert len(silent) == 1 and "nothing declares it" in silent[0]

    assert harness.underdetermined_census((), {DOC: SEPARATED}) == ([], [])


def test_a_widened_declaration_is_not_read_as_an_underdetermined_one() -> None:
    """Section 2: the two kinds "are never summed", and the equality ranges over one of them.

    A ``WIDENED`` declaration at a union's pointer is a different claim about a different
    thing -- a fact the annotation does not carry -- so counting it here would make a union
    look declared that nothing declared.
    """
    widened = approximate(_ref("#/oneOf"), "oneOf", Position.ROOT, OVERLAPPING["oneOf"])
    assert widened.kind == WIDENED
    stale, silent = harness.underdetermined_census((widened,), {DOC: OVERLAPPING})
    assert stale == []
    assert len(silent) == 1
