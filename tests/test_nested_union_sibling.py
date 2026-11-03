"""The sibling screen of a NESTED union: §6's ``discriminator`` row, and the ``type`` word.

Two names are not refused beside a nested ``oneOf``/``anyOf`` and each is here for its
own reason, which is why both are graded in this one module -- the screen is one line and
a reader who changes it has to meet both.

**``type``, and §5(a)'s first bullet is the decision** (``adcp-client-python-10l.21``):
"A plain keyword beside a ``oneOf``/``anyOf``.  §4's union section already decides it --
*every keyword beside the combinator compiles onto the base, and every branch inherits
it* ... No widening; the keyword compiles."  §14 step 9 lists it first among the faithful
rows.  The screened sentence says a sibling has "no slot for a fact of its own" on an
``ir.TypeRef`` -- true, and it does not reach this keyword, because the word is never
carried on the union's type at all: ``schema.parse._union`` hands every branch
``applied=<the word>``, so the fact is IN THE BRANCHES.  That is graded below -- the word
reaching every branch node, through the production parser -- and not read off the table.

Measured over the 1,054 portable documents at ``9e759de``: 21 nodes reach this screen and
**12 state the word and nothing else beside the combinator**; admitting it took ``emitted``
845 -> 871 with no module of the tree changing by one byte.

**``discriminator``**:
``salesagent-j3k2l.67``.  ``union.ROOT_CLAIMS`` admitted the keyword at a root union
with the reason written beside it -- it constrains nothing, so ignoring it cannot make
the model wider than its document, and it is READ there as the property §4 "Names" takes
a branch's name from.  ``union.nested``'s screen refused it, on a sentence whose stated
mechanism is a CONSTRAINING sibling's: the fact has nowhere to go on an
``ir.TypeRef``, so dropping it would leave the model wider than its document at that
very pointer.

That mechanism does not reach this keyword, and both halves are graded here:

* the keyword constrains nothing, which §6's own row states -- "Nothing on the class.
  It names a branch where that branch pins more than one ``const``, and separately it
  CONFIRMS a dispatch key the branches already state -- it does not establish one";
* nothing is dropped that any reading carries: the cell's ``rendered`` is ``False``, so
  the keyword is outside ``harness.FOLDED_FACTS`` -- the set the document-side fold
  ranges over, ``keywords.rendered_at`` -- and a nested union's node holds no fact for
  it either way.  Asserted as the CELL, in both directions, by
  :func:`test_the_screen_admits_exactly_the_one_name`.

A constraining sibling still refuses, which is the perturbation under each assertion: the
screen was narrowed by two names and not opened.

**AND A THIRD ANSWER, which is neither an admission nor a refusal**
(``adcp-client-python-10l.34``).  §8 widened its union-branch pairing rule to a union at
ANY position on 2026-10-27, and with it: "a sibling beside a union lowers by COMPOSITION,
and nothing is approximated.  The siblings become a base class; each branch becomes a
subclass narrowing what it narrows; the union is over the subclasses."  So a sibling a
CLASS carries does not reach this screen's sentence at all -- ``union.lower`` sends the
node to ``union.lower_union``, the ROOT position's own reader -- and what the screen is
left refusing is a sibling no class carries.  Four things are graded below and each is a
different claim:

* the SELECTOR is derived and not listed (``union.carried_by_a_class`` is
  ``lower.composition.COMPOSING`` plus the node's own rule sources, minus the two the ``A | B``
  arm answers for), so a keyword §5 later compiles onto a class joins it with no edit
  here;
* the 9 documents the old sentence refused are exactly the bundle's population for it,
  derived off the bundle, and NONE of them refuses on a sibling carrier any more;
* ``account/sync-accounts-request.json`` -- §8's own measured case -- emits the shape §8
  names, read off the classes the run WROTE: the base names the union's node and carries
  the siblings, each branch is a subclass of it narrowing requiredness, and the union is
  over the subclasses;
* a sibling no class carries still refuses on the screen's own sentence, which is the
  perturbation: the screen was narrowed by a derived set and not opened.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from compiled import compiled
from nodeset import claimed, partitions

from codegen import bundle, emit, keywords
from codegen.lower import composition, names
from codegen.lower import union as lower_union
from codegen.schema import nodes
from codegen.schema import parse as schema_parse

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
DRAFT = "http://json-schema.org/draft-07/schema#"

#: The two union keywords, read off the module under test rather than retyped.
UNION = lower_union.UNION


def _sites(document: dict) -> list[str]:
    """Every pointer of a document that is a union carrying a ``discriminator``."""
    found: list[str] = []

    def walk(node: Any, pointer: str) -> None:
        if isinstance(node, dict):
            if (
                any(isinstance(node.get(kw), list) for kw in UNION)
                and "discriminator" in node
            ):
                found.append(pointer or "/")
            for key, value in node.items():
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{pointer}/{i}")

    walk(document, "")
    return found


def _nested_sites() -> dict[str, list[str]]:
    """The bundle's NESTED ``discriminator``-beside-a-union sites, by document.

    A ROOT site is left out: the table already admits the keyword there, and this
    row is about the other position.
    """
    out = {}
    for document in sorted(bundle.portable(BUNDLE)):
        nested = [p for p in _sites(bundle.read(BUNDLE, document)) if p != "/"]
        if nested:
            out[document] = nested
    return out


def test_the_position_this_row_is_about_is_a_real_population() -> None:
    """The sites and the documents, named and non-empty, so the assertions below are not
    a derivation that selects nothing.

    Partitioned by what the keyword's admission does for each document, because the two
    outcomes are different and their sum is not a number: one document EMITS, and the
    rest refuse one pointer deeper on keywords other rows own.  Which keyword each waits
    on is those rows' fact and moves when they land, so it is not pinned here.
    """
    sites = _nested_sites()
    documents = claimed("documents carrying a nested discriminator", set(sites))
    claimed(
        "nested discriminator sites", [(d, p) for d, ps in sites.items() for p in ps]
    )
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    partitions(
        documents,
        emits=documents & set(out.emitted),
        refuses_elsewhere=documents - set(out.emitted),
    )
    # NOT on this keyword, anywhere in the run, chains included: that is the whole of
    # what the admission changes about the report.
    assert [d for d, r in out.refusals.items() if r["keyword"] == "discriminator"] == []
    assert [
        d
        for d, r in out.refusals.items()
        if "discriminator: a sibling of a nested" in r["detail"]
    ] == []


#: The phrase that identifies :data:`union._NESTED_SIBLING` in a refusal's own sentence.
#: ONE spelling, because three checks read it -- the perturbation below, the whole-run
#: exit condition and its per-document form -- and a phrase retyped at each is three
#: readings of one sentence for two of them to drift from.
_CARRIER = "no slot for a fact of its own"


def test_a_constraining_sibling_of_a_nested_union_still_refuses() -> None:
    """The perturbation: the screen was narrowed by ONE NAME.

    The same node with a ``minLength`` beside the union states a fact about the instance
    with nowhere to go on an ``ir.TypeRef``, so it refuses on
    :data:`union._NESTED_SIBLING` -- and it refuses on THAT keyword, not on the
    ``discriminator`` beside it, which is the attribution a refusal report is for.
    """
    admitted = _fixture(_NESTED)
    refused = _fixture(_constrained(_NESTED))
    try:
        out = emit.emit(admitted, ["root.json"])
        assert not out.refusals, out.refusals

        blocked = emit.emit(refused, ["root.json"])
        assert "root.json" in blocked.refusals, blocked.emitted
        row = blocked.refusals["root.json"]
        assert (row["keyword"], row["pointer"]) == ("minLength", "/properties/goal"), (
            row
        )
        assert _CARRIER in row["detail"], row
    finally:
        shutil.rmtree(admitted)
        shutil.rmtree(refused)


def test_the_keyword_is_read_at_this_position_and_not_merely_tolerated() -> None:
    """``discriminator.propertyName`` is §4's FIRST DISPATCH SOURCE and names nothing.

    **This test asserted the opposite and §4 decided against it** (rung 2 reads EVERY pin,
    2026-10-29; ``adcp-client-python-10l.78``).  The premise was that two pinned
    properties is "the case where the keyword decides, because ``_const_pin`` takes a
    single pin without it and refuses to choose between two by spelling" -- so the keyword
    chose, and without it the branches had no identity at all.  Rung 2 now reads every pin
    in the document's own key order, which is an answer the keyword is not needed for: the
    two branches below are ``XARound`` and ``XBSquare`` whether the union nominates a
    property or not.

    So what is graded here is the keyword's REMAINING role, and it is asserted in both
    directions: ``dispatch_key`` reads it (it is §4's first dispatch source, which decides
    whether the base carries ``Field(discriminator=…)``), and the branch NAMES are
    identical with it and without it.  A reading that let it back into the naming path
    reddens on the second assertion.

    :func:`union.branch_identity` is the one reading of §4's rungs and :func:`union.nested`
    is one of its two callers, so this is the nested position's naming and not the root's.
    """
    branches = [
        {
            "type": "object",
            "properties": {"kind": {"const": "a"}, "shape": {"const": "round"}},
        },
        {
            "type": "object",
            "properties": {"kind": {"const": "b"}, "shape": {"const": "square"}},
        },
    ]
    # The keyword is READ ONCE, by ``union.dispatch_key`` off the union node's own
    # annotations -- the cell CONSTRAINS NOTHING (§6), so the parser puts it there -- and
    # the two readings that want it are handed the property it names rather than the
    # node.  Both unions below go through the production parse, so what is graded is the
    # node the walk builds.
    keyed = _union_node({"discriminator": {"propertyName": "kind"}, "oneOf": branches})
    bare = _union_node({"oneOf": branches})
    assert lower_union.dispatch_key(keyed) == "kind"
    assert lower_union.dispatch_key(bare) is None
    # §4 "Names"'s rules are ``lower/names.py``'s and the DECLARATION reading that feeds
    # them is this module's (``_naming_facts``), which is the seam §14 step 7 drew: the
    # walk extracts the three facts and the pass decides which one wins.
    def identity(branch: Any, key: str | None) -> str | None:
        # ``key`` is accepted and deliberately NOT passed: §4's rung 2 takes no nominated
        # property, and ``_naming_facts`` has no parameter for one.  The helper keeps the
        # argument so the two calls below read as the two cases they are.
        assert key is None or isinstance(key, str)
        hop = lower_union._naming_facts(  # the test is the caller
            branch, branch.get("properties")
        )
        # §4's branch rules answer with the branch's own SEGMENTS now
        # (``adcp-client-python-10l.50``), because which of the facts wins decides
        # whether the parent's spelling is part of the name: a ``const`` pin is spelled
        # ON it and a title names itself.  The parent here is a chain of one, ``X``, and
        # what is compared is the name that chain spells.
        #
        # §4's FOURTH rung answers ``None`` here and that is this position's own rule:
        # ``_naming_facts`` reads the three DECLARED facts and ``union.nested`` records no
        # INDEX, because a nested union's branch is a member type that needs no name of
        # its own (``adcp-client-python-10l.41``).  So "no identity at all" below is still
        # the exact claim -- a ROOT union's branch would take ``XBranch<i>``.
        segments = names.branch_identity(hop, ("X",))
        return None if segments is None else "".join(segments)

    named = claimed(
        "branch identities under the keyword",
        [identity(b, lower_union.dispatch_key(keyed)) for b in branches],
    )
    # BOTH pins, in the document's own key order: ``kind`` then ``shape``.
    assert named == {"XARound", "XBSquare"}, sorted(named)
    # And the SAME names with the keyword gone, which is the half that says the keyword
    # is a dispatch source and not a naming input.
    assert {identity(b, lower_union.dispatch_key(bare)) for b in branches} == named


def _union_node(declaration: dict[str, Any]) -> Any:
    """One union declaration as the node the walk builds for it, at a nested position."""
    return schema_parse.parse(
        declaration,
        pointer="/properties/goal",
        position=keywords.Position.PROP,
        source=schema_parse.Source(document="probe.json"),
    )


# --------------------------------------------------------------------------- #
# the fixtures and the two helpers, all through the production pipeline
# --------------------------------------------------------------------------- #
#: A document whose one nested union carries the keyword and nothing else.  Object root
#: with a ``title``, so the root is a class the emitter names.
_NESTED: dict[str, Any] = {
    "$schema": DRAFT,
    "title": "Goal Holder",
    "type": "object",
    "additionalProperties": False,
    "required": ["goal"],
    "properties": {
        "goal": {
            "description": "The outcome to plan against.",
            "discriminator": {"propertyName": "kind"},
            "oneOf": [
                {
                    "type": "object",
                    "title": "Metric Goal",
                    "additionalProperties": False,
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string", "const": "metric"}},
                },
                {
                    "type": "object",
                    "title": "Event Goal",
                    "additionalProperties": False,
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string", "const": "event"}},
                },
            ],
        }
    },
}


def _constrained(document: dict) -> dict:
    """The same document with a CONSTRAINING sibling beside the same union."""
    out = json.loads(json.dumps(document))
    out["properties"]["goal"]["minLength"] = 3
    return out


def _fixture(document: dict) -> Path:
    """A bundle directory holding one ``root.json``."""
    at = Path(tempfile.mkdtemp())
    (at / "root.json").write_text(json.dumps(document))
    return at


def _declared(out: emit.Emitted, document: str) -> list[Any]:
    """Every class the run wrote for ``document``, by importing what it wrote.

    The WRITTEN package rather than the rendered text, for ``test_ref_branch_union``'s
    reason: a class carrying a union is exactly the shape that can render and not import.
    """
    at = Path(tempfile.mkdtemp())
    try:
        emit.write(out, at / "pkg", None)
        sys.path.insert(0, str(at))
        try:
            for name in [n for n in sys.modules if n == "pkg" or n.startswith("pkg.")]:
                del sys.modules[name]
            module = importlib.import_module(
                "pkg." + emit.module_path(document).replace("/", ".")
            )
        finally:
            sys.path.remove(str(at))
        return [
            value
            for value in vars(module).values()
            if isinstance(value, type)
            and getattr(value, "__adcp_schema__", None) is not None
            and value.__adcp_schema__.document == document
        ]
    finally:
        shutil.rmtree(at)


def test_the_refusal_sentence_names_no_owner_for_the_position() -> None:
    """A verdict needs no row, and the sentence that said it did sent a reader looking
    for an owner that does not exist.

    :data:`union._NESTED_SIBLING` is the detail text 44 documents carry, so the sentence
    was the most-read text in the module's refusals.  It is complete without the clause,
    and this asserts the clause is gone rather than trusting the edit.
    """
    assert "needs a row" not in lower_union._NESTED_SIBLING
    assert "ROOT_CONJUNCTS" not in lower_union._NESTED_SIBLING
    assert lower_union._NESTED_SIBLING.endswith(
        "no declaration can carry the widening there"
    )


# --------------------------------------------------------------------------- #
# the second name: ``type``, which the parser puts in every branch
# --------------------------------------------------------------------------- #
def _typed_nested_sites() -> dict[str, list[str]]:
    """Every NESTED union of the bundle stating a ``type`` word beside the combinator.

    Read off each document as the bundle states it, so the population is a property of
    the bundle and not of what the run happened to reach -- a document refused one
    pointer earlier still carries the site.
    """
    out: dict[str, list[str]] = {}

    def walk(node: Any, pointer: str, found: list[str]) -> None:
        if isinstance(node, dict):
            if (
                any(isinstance(node.get(kw), list) for kw in UNION)
                and isinstance(node.get("type"), str)
                and pointer != ""
            ):
                found.append(pointer)
            for key, value in node.items():
                walk(value, f"{pointer}/{key}", found)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{pointer}/{i}", found)

    for document in sorted(bundle.portable(BUNDLE)):
        found: list[str] = []
        walk(bundle.read(BUNDLE, document), "", found)
        if found:
            out[document] = found
    return out


def test_the_type_word_beside_a_nested_union_reaches_every_branch() -> None:
    """The MECHANISM, through the production parser: the union tells every branch.

    §5(a)'s first bullet is the decision and ``schema.parse._union`` is the whole of the
    implementation -- ``applied=<the word>`` per branch, which is §6's "a child never
    reconstructs its parent" and ``_base.applied_schema``'s own rule.  So what is graded
    is that the word is ON each branch node, which is why nothing has to be conjoined at a
    pointer the document does not state and why the union's own ``ir.TypeRef`` needs no
    slot for it.

    Asserted over the BUNDLE's own sites rather than over a fixture, and in both
    directions: a branch stating its own word keeps it (``applied_schema``'s "a node's own
    ``type`` always wins"), and a branch stating none takes the union's.

    **No branch of this population states a DIFFERENT word, measured**: over the records
    of the 1,054 portable documents, 21,498 branches of a worded union state no word, 5,661
    restate the same one and **0 state another**.  So the empty intersection §5(b) decides
    (two disjoint type words) has no site here and no arm is written for it.
    """
    sites = _typed_nested_sites()
    claimed("documents with a worded nested union", set(sites), inside=set(bundle.portable(BUNDLE)))
    pairs = claimed(
        "worded nested union sites", [(d, p) for d, ps in sites.items() for p in ps]
    )
    told: list[tuple[str, str]] = []
    kept: list[tuple[str, str]] = []
    unions: list[tuple[str, str]] = []
    a_rule: list[tuple[str, str]] = []
    for document, pointer in sorted(pairs):
        node = bundle.node_at(bundle.read(BUNDLE, document), pointer)
        parsed = schema_parse.parse(
            node,
            pointer=pointer,
            position=keywords.Position.PROP,
            source=schema_parse.Source(document=document),
        )
        if not isinstance(parsed, nodes.Union):
            # A combinator whose every branch constrains only key PRESENCE is a RULE and
            # not a union at all (§5's ``oneOf``/``anyOf`` row, ``rules.presence_only``),
            # so the parser's arm order classifies the node on what is left -- and this
            # screen never sees it.  Partitioned below rather than filtered silently.
            a_rule.append((document, pointer))
            continue
        unions.append((document, pointer))
        for branch in parsed.branches:
            # The union TOLD it, whatever the branch states: ``applied`` is the enclosing
            # assertion and is the same field at every branch.
            assert branch.applied == node["type"], (document, pointer, branch.pointer)
            own = bundle.node_at(bundle.read(BUNDLE, document), branch.pointer).get("type")
            (kept if own is not None else told).append((document, branch.pointer))
            assert own in (None, node["type"]), (document, branch.pointer, own)
    # Every site accounted for by exactly one answer: the parser read it as a union, or
    # the combinator was a presence rule and this screen is not the reader.
    partitions(pairs, a_nested_union=unions, a_presence_rule=a_rule)
    # And every BRANCH of the union sites accounted for by which half of
    # ``applied_schema``'s rule answered it.
    partitions(
        set(told) | set(kept),
        takes_the_enclosing_word=told,
        states_its_own=kept,
    )
    assert told, "no branch takes the word, so the clause above holds vacuously"


def test_the_screen_admits_exactly_the_one_name() -> None:
    """The narrowing is one name, and the TABLE is where it is written.

    This module used to carry a ``NESTED_HANDLED`` set naming ``discriminator`` here,
    beside ``compiler.ANNOTATIONS`` naming every other member of §6's table -- one
    decision in two places, differing only in the position each reached.  §6's own row
    carries no position split, so ``codegen.keywords`` admits the keyword at every
    position and this module names nothing: asserted as the CELL, in both directions.
    """
    from codegen import keywords
    from codegen.keywords import Effect, Position

    for position in Position:
        answer = keywords.cell("discriminator", position)
        assert answer is not None and answer.effect is Effect.NOTHING, position
        assert not answer.rendered, position
    # The other direction: this module holds no keyword set for a screen to read, so
    # there is no second place for §6's row to drift to.
    assert not [name for name in vars(lower_union) if name.endswith("_HANDLED")]


# --------------------------------------------------------------------------- #
# the third answer: a sibling a CLASS carries, which COMPOSES (§8)
# --------------------------------------------------------------------------- #
#: Every SITE of the bundle at which §8's composition rule fires, as a SET of
#: ``(document, pointer)`` pairs (§8's own instrument for a figure that is not monotone:
#: "what is pinned instead is the SET, named by document").  It is pinned here and
#: DERIVED below off the bundle, in both directions, which is what makes a nineteenth
#: site loud rather than silently absent -- a list of paths is complete with respect to
#: itself.
#:
#: **The documents of :data:`THE_CARRIERS_OWN_DOCUMENTS` are the subset whose EARLIEST obstruction was
#: the sibling carrier**; the other documents refuse earlier on something else and reach
#: the site only once those rows land, which is why the two sets are different sizes and
#: why neither is the other's measure.
#:
#: **IT IS A RATCHET AND NO LONGER AN EQUALITY, AND TWO ENTRIES LEFT** (2026-11-04,
#: ``adcp-client-python-99m``).  The equality was red:
#:
#:     pinned and not derived: ('core/canonical-forecast-point.json', '/properties/viewability')
#:                             ('core/forecast-point.json', '/properties/viewability')
#:
#: and a site LEAVING is not a finding about this row.  Both nodes state an ``anyOf`` of
#: one branch forbidding four metrics and one requiring ``standard``, and
#: ``schema.presence_clause`` reads a branch stating ONLY a ``not`` over required groups
#: as a presence clause with an empty required group -- so ``presence_only`` is ``True``
#: at both, the node lowers to a RULE on the enclosing class, and there is no nested
#: union left to compose a sibling.  Measured: ``presence_only({"anyOf": [...]},
#: Position.PROP)`` is ``True`` for both.  ``tests/test_union_disjointness.py``'s
#: ``_INSEPARABLE_CONSTRAINTS`` records the same two nodes leaving the same way, for the
#: same commit, in as many words -- "the derivation moved and the name did not move with
#: it" -- so this is the second reader of one parser change, and the first one had already
#: written down what to do about it.
#:
#: So the entries are removed (the pin FOLLOWING the behaviour) and the direction is
#: stated, which is what the equality was standing in front of.  **This set may SHRINK
#: and may not GROW**: what the row needs is that no site appears it has not been
#: measured over -- "a nineteenth site reddens here instead of being quietly absent from
#: a list" -- and a site the parser stops reading as a nested union is the parser
#: changing and not this carrier failing.  The containment is the loud half; the exit
#: condition below, that no document is refused on the carrier's sentence, is what says
#: the remaining sites are HANDLED and is total over the run.
COMPOSING_SITES = frozenset(
    {
        ("account/sync-accounts-request.json", "/properties/accounts/items"),
        ("brand.json", "/definitions/color_ref"),
        (
            "compliance/comply-test-controller-response.json",
            "/oneOf/6/properties/recorded_calls/items",
        ),
        ("core/format.json", "/properties/renders/items"),
        ("core/format.json", "/properties/assets/items/oneOf/0"),
        ("creative/preview-creative-response.json", "/oneOf/1/properties/results/items"),
        ("creative/validate-input-request.json", "/properties/targets/items"),
        ("formats/canonical/coordinated_placements.json", "/properties/components/items"),
        (
            "formats/canonical/coordinated_placements.json",
            "/properties/components/items/anyOf/1",
        ),
        (
            "formats/canonical/seller_rendered_stateful_display.json",
            "/properties/transitions/items",
        ),
        ("governance/sync-plans-request.json", "/properties/plans/items/properties/budget"),
        ("media-buy/decline-proposals-response.json", "/properties/results/items"),
        ("media-buy/get-reporting-status-response.json", "/oneOf/0"),
        ("media-buy/get-reporting-status-response.json", "/oneOf/1"),
        ("media-buy/proposal-refinement.json", "/oneOf/1"),
        ("media-buy/refine-proposals-response.json", "/properties/results/items"),
    }
)

#: The documents whose refusal WAS the sibling carrier -- group G2 of
#: ``docs/plan/reasons-vs-rows.md``, 42 documents blocked and 34 of them chained.  They
#: are the ones among the nodes reaching this screen that state a sibling beyond the
#: ``type`` word, and every one of them is a site of :data:`COMPOSING_SITES`, asserted
#: below -- which is what makes this a group the carrier APPLIES to rather than a group
#: somebody wrote down.
#:
#: **RENAMED FROM ``THE_NINE`` AND NOW HOLDS SEVEN** (2026-11-04,
#: ``adcp-client-python-99m``).  ``core/canonical-forecast-point.json`` and
#: ``core/forecast-point.json`` left for the reason :data:`COMPOSING_SITES` records
#: above: ``schema.presence_clause`` reads their ``/properties/viewability`` as a
#: presence clause, so the node lowers to a rule and has no nested union composing a
#: sibling.  The containment below was RED on exactly those two, and it was right -- the
#: set's own definition ties membership to having such a site, so a document that stops
#: having one has to leave.
#:
#: The NAME went with them, because a constant called ``THE_NINE`` holding seven entries
#: is the same staleness one level up: a count in an identifier cannot follow the
#: behaviour, and nothing here needs to know how many there are.
THE_CARRIERS_OWN_DOCUMENTS = frozenset(
    {
        "account/sync-accounts-request.json",
        "compliance/comply-test-controller-response.json",
        "core/format.json",
        "creative/preview-creative-response.json",
        "formats/canonical/coordinated_placements.json",
        "formats/canonical/seller_rendered_stateful_display.json",
        "governance/sync-plans-request.json",
    }
)

#: §8's own measured case, and the one document of 3.2 the widening EMITS.  The other 8
#: each report a next obstruction of their own, by name, keyword and pointer, and which
#: one is those rows' fact rather than this one's -- so it is not pinned here.
MEASURED_CASE = "account/sync-accounts-request.json"
AT = "/properties/accounts/items"

#: The four keywords whose subtree is a RULE position, excluded from the derivation
#: below for ``harness.inseparable_unions``' own reason: §3 of the semantics document
#: says that under a conditional "a keyword describes what a rule tests, so no type is
#: lowered from it", so the walk never lowers a union there and no sibling of one needs a
#: carrier.  Measured: 4 of the 22 sites the derivation finds without this clause sit
#: inside a ``then``, and 2 of their documents emit today.
_A_RULE_POSITION = ("if", "then", "else", "not")


def _composing_nested_sites() -> dict[str, list[str]]:
    """Every NESTED union of the bundle stating a sibling a CLASS carries.

    DERIVED, by asking :func:`union.composes_its_siblings` of the node the production
    parser builds for it -- the predicate under test, over the bundle's own text, so the
    population is a property of the bundle and not of what the run happened to reach.
    Parsed at ``PROP`` for ``_union_node``'s reason: the position reaches the predicate
    only through ``compiler.rules_at``, whose rule cells are the same at every position a
    class can sit at, and the ROOT position is excluded by the pointer because §4 gives a
    root the base-plus-subclasses shape whatever it states beside the combinator.
    """
    out: dict[str, list[str]] = {}

    def walk(node: Any, pointer: str, found: list[str], document: str) -> None:
        if isinstance(node, dict):
            if pointer != "" and any(isinstance(node.get(kw), list) for kw in UNION):
                parsed = schema_parse.parse(
                    node,
                    pointer=pointer,
                    position=keywords.Position.PROP,
                    source=schema_parse.Source(document=document),
                )
                if isinstance(parsed, nodes.Union) and lower_union.composes_its_siblings(
                    parsed
                ):
                    found.append(pointer)
            for key, value in node.items():
                if key in _A_RULE_POSITION:
                    continue
                walk(value, f"{pointer}/{key}", found, document)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{pointer}/{i}", found, document)

    for document in sorted(bundle.portable(BUNDLE)):
        found: list[str] = []
        walk(bundle.read(BUNDLE, document), "", found, document)
        if found:
            out[document] = found
    return out


def test_the_population_the_widening_is_about_is_derived_off_the_bundle() -> None:
    """The sites, DERIVED, and the sibling carrier gone from the whole run's report.

    Three claims.  Every DERIVED site is one :data:`COMPOSING_SITES` has been measured
    over, so a nineteenth site reddens here instead of being quietly absent from a list.
    The 9 documents the carrier refused are a subset of its documents, which is what says
    the pinned nine name real sites rather than a group somebody wrote down.  And no
    document of the run -- chains included -- is refused on the sentence any more, which
    is the exit condition: the fact has a carrier rather than those 9 having moved
    somewhere the report cannot see.

    **The first claim is a CONTAINMENT and not an equality** (2026-11-04): the data's own
    comment says which direction is the obligation and why the other one reddened on a
    parser change that is not this row's.  The exit condition is what makes the
    containment enough -- it ranges over the whole run and names any document the carrier
    still stops.
    """
    sites = _composing_nested_sites()
    documents = claimed("documents whose nested union composes a sibling", set(sites))
    pairs = claimed(
        "composing nested union sites",
        [(d, p) for d, ps in sites.items() for p in ps],
    )
    unmeasured = sorted(pairs - COMPOSING_SITES)
    assert unmeasured == [], (
        f"{len(unmeasured)} composing nested-union site(s) this row has not been "
        f"measured over: {unmeasured}.  COMPOSING_SITES may SHRINK and may not GROW; a "
        "new site needs its own reading, not an entry."
    )
    assert THE_CARRIERS_OWN_DOCUMENTS <= documents, sorted(
        THE_CARRIERS_OWN_DOCUMENTS - documents
    )
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    assert [d for d, r in out.refusals.items() if _CARRIER in r["detail"]] == []
    # Partitioned rather than summed: one of the nine emits and the other eight report a
    # next obstruction that belongs to another row.
    partitions(
        THE_CARRIERS_OWN_DOCUMENTS,
        emits=THE_CARRIERS_OWN_DOCUMENTS & set(out.emitted),
        refuses_on_its_own_next_obstruction=THE_CARRIERS_OWN_DOCUMENTS
        - set(out.emitted),
    )
    assert MEASURED_CASE in out.emitted, out.refusals.get(MEASURED_CASE)
    # And each of the eight is refused on something OTHER than the sibling carrier, which
    # is the per-document form of the exit condition above: the carrier is not what stops
    # it.
    #
    # **It reads the SENTENCE and not the POINTER** (``adcp-client-python-10l.58``).  It
    # asked that the refusal's POINTER be none of the document's composing sites, which
    # was the same question for as long as the only refusal that could be reported at
    # such a node was this carrier's.  It is not any more:
    # ``formats/canonical/coordinated_placements.json``'s branch at
    # ``/properties/components/items/anyOf/1`` is ITSELF a union composing siblings, so
    # once the enclosing union's branch screen reaches that branch the refusal it returns
    # -- another row's, on the branch's nested ``oneOf``, with this carrier's sentence
    # nowhere in it -- is reported AT a composing site.  The pointer was a PROXY for the
    # sentence; the claim is about the sentence, so the sentence is what is read, in the
    # one spelling the whole-run check above uses.
    for document in sorted(THE_CARRIERS_OWN_DOCUMENTS - set(out.emitted)):
        assert _CARRIER not in out.refusals[document]["detail"], out.refusals[document]


def test_the_selector_is_derived_from_two_declarations_and_not_listed_here() -> None:
    """``union.carried_by_a_class`` reads the TABLE and the NODE, and nothing retyped.

    Both sources are load-bearing and each is graded on a keyword only it supplies:
    ``properties`` is in :data:`lower.composition.COMPOSING`, which is the one declaration of what
    a composing class consumes, and ``dependencies`` is NOT -- it reaches the set only
    because ``compiler.rules_at`` reads it off this node as a rule source.  §8's measured
    case states both, so a selector that dropped either source would answer differently
    about the one document the widening emits.

    The two names the ``A | B`` arm answers for come OUT, asserted directly: the
    combinator is the node's own kind and the ``type`` word is in every branch already
    (the first half of this module).
    """
    node = _union_node(bundle.node_at(bundle.read(BUNDLE, MEASURED_CASE), AT))
    assert isinstance(node, nodes.Union), type(node).__name__
    carried = lower_union.carried_by_a_class(node)
    assert "properties" in composition.COMPOSING
    assert "properties" in carried
    assert "dependencies" not in composition.COMPOSING
    assert "dependencies" in carried, sorted(carried)
    assert node.combinator not in carried and "type" not in carried, sorted(carried)
    # A value constraint beside a combinator of shapes is in NEITHER source, which is
    # what leaves the screen's own sentence a reachable answer.
    assert "minLength" not in carried
    assert lower_union.composes_its_siblings(node)
    # And the other direction, over a nested union of the SAME bundle that states nothing
    # beside the combinator: the predicate says no, so such a node keeps the one type.
    bare = _union_node({"oneOf": [{"$ref": "#/definitions/a"}, {"$ref": "#/definitions/b"}]})
    assert isinstance(bare, nodes.Union)
    assert not lower_union.composes_its_siblings(bare), sorted(
        lower_union.carried_by_a_class(bare)
    )


#: The clause §8 WITHDREW, pinned as ABSENT (``adcp-client-python-10l.47``).  §5's cell
#: read "Shapes nested -> one type ``A | B``; a sibling beside it refuses" after §8 had
#: already decided the composition answer at a union in ANY position, so the one document
#: disagreed with itself for as long as the two readings coexisted.  A VALUE pin: the
#: copy is read by the assertion below and by nothing else, so a copy that went stale can
#: only redden.
WITHDRAWN = "a sibling beside it refuses"

#: The triple the four readers of §3 derive from, pinned beside the prose.  The
#: correction is a SENTENCE change and must be only that: the effect decides admission
#: and whether a handler owes a lowering, ``rendered`` decides the set the document-side
#: fold carries, and ``descends`` decides where the walk takes the branches.
_UNION_CELL = (keywords.Effect.TYPE, False, keywords.Position.BRANCH)


def test_the_cell_the_four_readers_read_states_the_composition_answer() -> None:
    """§5's own text, which is the cell's, agrees with §8 -- and no reader is a new one.

    The acceptance this row is about: the cell states the base-plus-branches answer for a
    sibling a CLASS carries, keeps ``A | B`` for a union stating nothing beside the
    combinator, and keeps the refusal for a sibling NO class carries -- which is the
    screen's own sentence, graded above and reachable by
    ``test_a_constraining_sibling_of_a_nested_union_still_refuses``.

    Four claims, and the last two are what say the edit added no fifth copy.

    * ONE CELL answers at ROOT and at every nested position.  The union row declares no
      ``PROP``/``ELEM``/``MAPV`` override, so ``keywords.cell`` hands back the row's
      default at each -- the same object -- and the widening cannot be written at one
      position and withheld at another.
    * The withdrawn clause is gone and the refusal is CONDITIONAL on the carrier.
    * The four readers of architecture §3 still read this cell, and each answer is a
      function of the pinned triple and not of the prose: admission and lowering off the
      effect, the fold's set off ``rendered``, the descent off ``descends``.
    * The prose reaches NO reader under ``codegen/``.  ``compiler._screen`` is the one
      place a cell's ``compiles`` becomes a refusal's detail, and it reads it only where
      the effect is ``REFUSE``; this cell's is ``TYPE``, so the sentence is read by the
      grid renderer in ``tests/test_keywords.py`` and by nothing else.  That is why the
      cell may say what a class CARRIES and must not enumerate which keywords those are:
      ``union.carried_by_a_class`` derives that set, and a list here would be a copy with
      no reader to keep it honest.
    """
    answer = keywords.cell("oneOf", keywords.Position.ROOT)
    assert answer is not None
    for position in (
        keywords.Position.PROP,
        keywords.Position.ELEM,
        keywords.Position.MAPV,
    ):
        assert keywords.cell("oneOf", position) is answer, position
    # ``anyOf`` is ``oneOf``'s row: ``_with_rungs`` rebuilds each cell, so the two are
    # EQUAL rather than identical, and the correction reached both because there is one
    # declaration above that assignment.
    for position in (keywords.Position.ROOT, keywords.Position.PROP):
        assert keywords.cell("anyOf", position) == answer, position

    assert WITHDRAWN not in answer.compiles, answer.compiles
    assert "A sibling a CLASS carries" in answer.compiles, answer.compiles
    assert "at a union in ANY position" in answer.compiles, answer.compiles
    assert "A sibling no class carries refuses" in answer.compiles, answer.compiles
    # And the clause that is still TRUE survived: a nested union stating nothing beside
    # the combinator is one type, which is what ``union.nested`` is for.
    assert "with nothing beside the combinator" in answer.compiles, answer.compiles

    assert (answer.effect, answer.rendered, answer.descends) == _UNION_CELL, answer
    at = keywords.Position.PROP
    # admission and lowering: a TYPE effect is a fact the node's own kind consumes, so the
    # screen admits it only where the handler claims it, and ``union.nested`` is what does.
    assert keywords.lowers(answer)
    assert "oneOf" in keywords.combinators(at)
    assert "oneOf" not in keywords.rule_sources(at)
    # the fold: the rendered column is the set the document-side fold carries, and a
    # combinator is read by DESCENDING it rather than carried as a value.
    assert "oneOf" not in keywords.rendered_at(at)
    # descent: where the walk takes the branches, which is the position they are parsed at.
    assert keywords.descends_at(at)["oneOf"] is keywords.Position.BRANCH
    # the prose reaches no reader through the screen: ``_screen`` quoted ``compiles`` on a
    # REFUSE cell and on nothing else, and §14 step 8 retired the effect -- so the
    # sentence is the GRID's alone now, which is what the round-trip in
    # ``tests/test_keywords.py`` grades it as.
    assert "REFUSE" not in keywords.Effect.__members__


def test_the_measured_case_emits_the_shape_section_8_names() -> None:
    """§8's decided lowering, read off the classes the run WROTE.

    "The siblings become a base class; each branch becomes a subclass narrowing what it
    narrows; the union is over the subclasses."  Each clause is asserted on the imported
    classes rather than on the rendered text, for ``_declared``'s reason -- a class
    carrying a union is exactly the shape that can render and not import:

    * the base names the union's own node, carries every one of the 16 declared
      properties as a field, and states the node's ``additionalProperties: true``;
    * each branch is a SUBCLASS of that base and names its own ``#/<kw>/<i>`` pointer;
    * the branch narrows requiredness and nothing else -- the three names its own
      ``required`` lists are required on it, and it declares no field the base does not;
    * the union is installed, so a payload comes back as the arm it satisfies and not as
      the base.
    """
    read = bundle.read(BUNDLE, MEASURED_CASE)
    node = bundle.node_at(read, AT)
    out = compiled(BUNDLE, [MEASURED_CASE])
    assert MEASURED_CASE in out.emitted, out.refusals.get(MEASURED_CASE)
    classes = {c.__adcp_schema__.pointer: c for c in _declared(out, MEASURED_CASE)}
    base = classes[f"#{AT}"]
    assert set(node["properties"]) <= set(base.model_fields), sorted(
        set(node["properties"]) - set(base.model_fields)
    )
    assert base.model_config.get("extra") == "allow", base.model_config
    # No field of the base is REQUIRED: the node states no ``required`` of its own, so
    # every one of the 16 is optional there and requiredness is each branch's own fact.
    assert [n for n, f in base.model_fields.items() if f.is_required()] == []
    for i, branch in enumerate(node["oneOf"]):
        arm = classes[f"#{AT}/oneOf/{i}"]
        assert issubclass(arm, base) and arm is not base, arm
        assert set(arm.model_fields) == set(base.model_fields), arm
        required = {n for n, f in arm.model_fields.items() if f.is_required()}
        assert required == set(branch["required"]), (arm, sorted(required))
    arms = tuple(classes[f"#{AT}/oneOf/{i}"] for i in range(len(node["oneOf"])))
    assert base._branch_models == arms, base._branch_models
