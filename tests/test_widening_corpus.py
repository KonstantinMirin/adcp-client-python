"""§8's OBLIGATION draws too, and this is where those draws are held.

``tests/test_accepts_corpus.py`` grades the store for ``harness.check_accepts``' one draw
per pair.  ``harness.check_widening`` draws several more times per pair -- a value class
at the declared pointer, an intermediate node on the way to the declaration's instance
location, and the pair's node conjoined with a demand -- and held none of them, which
``adcp-client-python-3be.25`` measured as the pole of a run whose accepts draws were ALL
replayed from the committed floor.  The reading, over the 53 pairs of the graded
population that carry a widened declaration:

==================================================  =========  ======  ============
``check_widening`` on one pair                      node bytes  draws       seconds
==================================================  =========  ======  ============
``core/async-response-data.json#/anyOf/28``         4,716,939        7         246.7
``core/async-response-data.json#/anyOf/34``         6,907,017        2  >600, cut off
==================================================  =========  ======  ============

242.6 s of the first is ``_reached`` drawing ONE 4,619,199-byte intermediate node TWICE,
117.9 s and 122.8 s, because the declaration has two value classes and each asks for the
same base; 600.4 s of the second is one such draw that had not returned when the
measurement cut it.  ``harness._Draws`` carries the rest of the reading and the key.

What is graded here, and each clause is a way the store could be wrong:

1. **A base draw is PAID once and REPLAYED after**, through the real check and read off
   the report's own counters rather than off a call count.  Shown at all three sites --
   the value class, the intermediate node and the demanded base -- because which one a
   pair pays depends on whether its accepts draw produced an instance at all, and holding
   one and not the others would move the pole instead of removing it.
2. **A replayed run grades the same WITNESS and reports the same verdict.**  The draw is
   not reproducible (``harness.corpus_key``'s docstring measures it), so a store is a
   statement about which witness the suite grades: the floor's, before the cache's, and
   the same one in every lane.
3. **THE HELD VALUE IS NOT TRUSTED, AND NOTHING NEW HAD TO BE WRITTEN FOR THAT.**  A base
   is placed and the placed payload is offered to the DOCUMENT before the entry point sees
   anything, so a held base the document refuses makes the declaration ``unproved`` and
   the pair reddens.  Asserted, because the absence of a ``corpus_defect`` here rests on
   it entirely.
4. **IT IS A SEPARATE KEY SPACE AND A SEPARATE DIRECTORY.**
   ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` asserts in BOTH
   directions that the accepts floor holds no entry the graded population does not ask
   for, and a widening entry landing in that directory would make a landed gate read red
   on nothing being wrong.  Two tests here read that from both sides: a widening draw
   leaves the accepts key space untouched, and the accepts key itself does not move
   because ``corpus_key`` grew a ``position`` argument.
5. **No run writes the committed floor**, which is ``corpus.Layered``'s rule and is what
   lets a floor be read by default.

**WHAT IS NOT HERE, STATED RATHER THAN OMITTED.**  There is no currency gate over the
widening floor -- no equality saying "every position the graded population asks for has a
committed entry".  The accepts floor has one because its live key set is readable without
drawing anything; this space's is not, and ``corpus.WIDENING_COMMITTED``'s comment carries
the measurement: which positions the population asks for depends on which borrowed base
hosted the declaration's location, so deriving the set exactly means running the
obligation, and on a cold floor that costs the very draws the gate would be reporting are
owed.  A gate over the cheap SUPERSET would demand entries for draws that never happen.
That is a decision for ``docs/plan/architecture.md`` and not something to leave implied.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, ClassVar

import pytest

import corpus as corpus_module
from adcp.types._base import AdCPBaseModel, SchemaRef
from codegen import harness
from codegen.harness import check_widening, corpus_key
from codegen.keywords import Position
from codegen.lower.approximate import approximate
from nodeset import claimed

REPO = Path(__file__).resolve().parents[1]

DOC = "core/probe.json"


def _ref(pointer: str = "#") -> SchemaRef:
    return SchemaRef(DOC, pointer)


#: **One document that drives all three draw sites of §8's obligation**, which is what a
#: store for them has to be graded against.  ``box`` is OPTIONAL, so:
#:
#: * a declaration on ``box.tags``' ``uniqueItems`` makes ``harness.value_classes`` derive
#:   a RESTRICTION and the check draws a value from it -- the first site, paid for every
#:   declaration there is;
#: * a borrowed instance that omits ``box`` makes ``harness._reached`` draw ``box``'s own
#:   subschema so the location exists -- the second site, and the one the measurement found
#:   costing;
#: * no borrowed instance at all leaves ``_reached`` nothing to fill in, every borrowed
#:   candidate fails, and ``harness._bases`` draws the node CONJOINED with the demand --
#:   the third site, and the one the row was filed about.
#:
#: Small on purpose: what is graded is the holding and the key, and a document whose draw
#: took a minute would grade the same thing a hundred times slower.
NESTED: dict[str, Any] = {
    "type": "object",
    "properties": {
        "box": {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}
            },
            "required": ["tags"],
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}

AT = "#/properties/box/properties/tags"


class Boxed(AdCPBaseModel, extra="forbid"):
    """The model section 5's ``uniqueItems`` row widens to: ``list[str]``, no rule."""

    __adcp_schema__: ClassVar[SchemaRef] = _ref()

    class Box(AdCPBaseModel, extra="forbid"):
        tags: list[str]

    box: Box | None = None


def _declaration() -> Any:
    return approximate(_ref(AT), "uniqueItems", Position.PROP, True)


def _accept(payload: Any) -> Any:
    """The production shape: the document decides, then the class builds."""
    import jsonschema

    jsonschema.Draft7Validator(NESTED).validate(payload)
    return Boxed.model_validate(payload)


class Held:
    """``corpus.Store``'s interface over a dict, so a test can perturb one entry.

    ``tests/test_accepts_corpus.py``'s own ``Held`` and for its reason: what these tests
    judge is what the HARNESS does with what it is handed, and the real store's own
    obligations are graded against the real thing further down.
    """

    def __init__(self, entries: dict[str, Any] | None = None) -> None:
        self.entries: dict[str, Any] = dict(entries or {})
        self.gets: list[str] = []
        self.puts: list[str] = []

    def get(self, key: str) -> Any:
        self.gets.append(key)
        return self.entries.get(key)

    def put(self, key: str, instances: list[Any]) -> None:
        self.puts.append(key)
        self.entries[key] = instances


# --------------------------------------------------------------------------- #
# 1. a base draw is paid once and replayed after, at all three sites
# --------------------------------------------------------------------------- #
def test_every_base_the_obligation_draws_is_paid_once_and_replayed_after() -> None:
    """**THE ROW, read off the check's own report over all three of its draw sites.**

    The obligation runs three times against ONE store, in the three states that decide
    which site draws: a borrowed instance that already hosts the location (the value class
    alone), one that does not (the value class and the intermediate node), and none at all
    (the value class and the demanded base).  Each state is run twice.  The first run of
    each pays its draws and replays nothing; the second pays NOTHING and replays what the
    first held -- and reaches the same verdict, which is the clause that makes the store a
    relocation rather than a change of subject.

    **The counters and not a call count**, because what is being claimed is a property of
    the CHECK and not of this test's ability to patch ``one_instance``: ``drawn`` and
    ``replayed`` are on :class:`harness.WideningResult` for exactly
    ``AcceptsResult.replayed``'s reason, so a reader of a green pair can see which run paid
    for its evidence.

    The three states are run against one store on purpose: the positions are named by the
    declared POINTER, so the value-class draw is one key across all three and the later
    states are already warm on it.  That is the across-pairs sharing the row is for, in
    miniature -- the measurement found the same declaration paying the same draw once per
    value class, once per pair of a document, and once per run.
    """
    one = (_declaration(),)
    store = Held()
    states = {
        "a borrowed instance that hosts the location": ({"box": {"tags": ["a", "b"]}},),
        "a borrowed instance that does not": ({},),
        "no borrowed instance at all": (),
    }
    paid: dict[str, int] = {}
    for state, instances in states.items():
        cold = check_widening(NESTED, _accept, one, instances=instances, corpus=store, identity=DOC)
        warm = check_widening(NESTED, _accept, one, instances=instances, corpus=store, identity=DOC)
        paid[state] = cold.drawn
        assert warm.drawn == 0, (
            f"{state}: the second run paid {warm.drawn} draws the first had already held"
        )
        assert warm.replayed >= 1, f"{state}: nothing was replayed, so nothing was held"
        assert (cold.outcome, cold.accepted, cold.unproved, cold.narrowings) == (
            warm.outcome,
            warm.accepted,
            warm.unproved,
            warm.narrowings,
        ), f"{state}: the replayed run reached a different verdict\n{cold}\n{warm}"
        assert cold.outcome == "pass", (state, cold.unproved, cold.narrowings)

    # **Each state drew something the one before it had not**, which is what says all
    # three sites are reached and held rather than one of them three times.  The first
    # state pays the value class; the second adds the intermediate node; the third runs
    # with a store already holding the value class and pays the demanded base alone.
    assert paid["a borrowed instance that hosts the location"] >= 1, paid
    assert paid["a borrowed instance that does not"] >= 1, paid
    assert paid["no borrowed instance at all"] >= 1, paid

    # And every draw paid is one KEY: the three sites name three derivations and no two of
    # them collide, which :func:`test_the_positions_the_three_sites_name_are_three_different_keys`
    # reads from the key function's side.
    assert len(set(store.puts)) == sum(paid.values()), (
        f"the draws and the keys do not correspond: {sum(paid.values())} draws, "
        f"{len(set(store.puts))} distinct keys"
    )
    assert len(set(store.puts)) >= 3, sorted(set(store.puts))


def test_the_positions_the_three_sites_name_are_three_different_keys() -> None:
    """The key is the pair's identity AND the position, and the positions do not collide.

    ``harness.corpus_key``'s ``position`` is what makes several draws within one pair
    several questions; this reads that the three derivations the obligation draws from get
    three addresses, that a position moves the key, and that the SAME position in the same
    pair is one key however often it is asked for.
    """
    spelled = [
        ("class", AT, "uniqueItems", "2 distinct members"),
        ("reached", "/properties/box/properties/tags", 0),
        ("demand", ["box", "tags"]),
    ]
    keys = [corpus_key(DOC, position=p) for p in spelled]
    assert len(set(keys)) == len(spelled), keys
    assert keys[0] == corpus_key(DOC, position=spelled[0]), "a key is not stable"
    # A different pair of the same document asks a different question at the same position.
    other = corpus_key({"document": DOC, "pointer": "#/properties/box"}, position=spelled[0])
    assert other not in keys, "the position answered without the pair's identity"


def test_a_pair_with_no_store_draws_exactly_as_it_always_did() -> None:
    """``corpus=None`` is the old path, and the report says so by its own counters.

    Every caller in ``tests/test_approximation.py`` is this one, so it is the behaviour the
    relocation may not touch: the draws are paid, nothing is held, and the verdict is the
    verdict.
    """
    res = check_widening(NESTED, _accept, (_declaration(),), instances=({},))
    assert res.outcome == "pass", (res.unproved, res.narrowings)
    assert res.replayed == 0
    assert res.drawn >= 1, "a run with no store drew nothing, so the counter is not reading"


def test_a_store_with_no_identity_beside_it_raises_rather_than_keying_on_the_schema() -> None:
    """``check_accepts``' rule, for the same defect and with the same absence of a fallback.

    The schemas this check draws from are DERIVED from the one it is handed -- restricted,
    walked, conjoined -- and the one it is handed is ``bundle.record``'s rendering of a
    document.  So an identity taken from it moves whenever the compiler moves, and every
    held value is redrawn for a bundle nobody touched (``harness.corpus_key``).  A caller
    with nothing static to offer passes ``corpus=None`` and draws.
    """
    import pytest

    with pytest.raises(ValueError, match="STATIC identity"):
        check_widening(NESTED, _accept, (_declaration(),), instances=({},), corpus=Held())
    # and the two ends of the same rule: no store at all, and a store with an identity
    assert check_widening(NESTED, _accept, (_declaration(),), instances=({},)).outcome == "pass"
    assert (
        check_widening(
            NESTED, _accept, (_declaration(),), instances=({},), corpus=Held(), identity=DOC
        ).outcome
        == "pass"
    )


# --------------------------------------------------------------------------- #
# 2. which WITNESS is graded: the floor's, before the cache's
# --------------------------------------------------------------------------- #
def test_the_floor_answers_before_the_cache_so_every_lane_grades_one_witness() -> None:
    """``corpus.Layered``'s read rule, for the space this row adds.

    Not a performance detail: the draw is not reproducible (``harness.corpus_key``'s
    docstring measures it over the accepts draw), so two stores holding one key can hold
    two different instances of the same question -- and which one answers decides which
    base the obligation places and therefore which payload the entry point is offered.
    The floor is given the base a reader of the tree would see and the cache a different
    one, and the payload that reaches ``accept`` carries the floor's.
    """
    position = ("reached", "/properties/box/properties/tags", 0)
    key = corpus_key(DOC, position=position)
    floor = Held({key: [{"tags": ["committed"]}]})
    cache = Held({key: [{"tags": ["cached"]}]})
    offered: list[Any] = []

    def watching(payload: Any) -> Any:
        offered.append(payload)
        return _accept(payload)

    res = check_widening(
        NESTED,
        watching,
        (_declaration(),),
        instances=({},),
        corpus=corpus_module.Layered(floor, cache),  # type: ignore[arg-type]
        identity=DOC,
    )
    assert res.outcome == "pass", (res.unproved, res.narrowings)
    assert offered, "nothing reached the entry point, so no witness was graded"
    assert key in floor.gets and res.replayed >= 1, (floor.gets, res.replayed)
    assert floor.puts == [], "a run wrote the committed floor"


def test_a_held_base_the_document_refuses_never_reaches_the_entry_point() -> None:
    """**Why this store needs no ``corpus_defect`` of its own, asserted and not assumed.**

    The accepts store re-offers every held instance to the DOCUMENT before it may count,
    because nothing downstream would.  Here something does, and it is older than this row:
    a base is PLACED and ``check_widening`` offers the placed payload to the document
    before the entry point is shown anything (``conforms(schema, attempt)``).  So the
    obligation's verdict is never a statement about a payload the document refuses,
    however wrong the held base is.  Two readings, and the second is the one that bounds
    the damage:

    * **A poisoned base changes no verdict while a sound candidate remains.**  That is not
      a repair the store performs -- it is the candidate walk the check already had, which
      ``check_widening``'s own docstring calls a FREE CHOICE among bases: "The walk cannot
      turn a narrowing into a pass: a candidate is skipped only where the DOCUMENT refuses
      the placed payload."  So the entry point sees a payload the document admits, and the
      poisoned one is counted and discarded.
    * **A poisoned base with NO candidate behind it reddens**, as ``unproved``, with the
      document's own reason -- it does not fall through to a fresh draw, which is the
      silent repair ``corpus.Layered``'s docstring refuses for the same reason: a store
      that redrew around its own bad entry would make a stale commit invisible.

    The poison is a ``box`` carrying a key ``additionalProperties: false`` forbids, so
    nothing but ignoring what was handed back could make it pass.
    """
    import jsonschema

    poison = [{"tags": ["a"], "smuggled": True}]
    step = ("reached", "/properties/box/properties/tags", 0)
    reached = corpus_key(DOC, position=step)
    demand = corpus_key(DOC, position=("demand", ["box", "tags"]))
    offered: list[Any] = []

    def watching(payload: Any) -> Any:
        offered.append(payload)
        return _accept(payload)

    res = check_widening(
        NESTED, watching, (_declaration(),), instances=({},),
        corpus=Held({reached: poison}), identity=DOC,
    )
    assert res.outcome == "pass", (res.outcome, res.narrowings, res.unproved)
    assert offered, "nothing reached the entry point, so the clause below is vacuous"
    for payload in offered:
        jsonschema.Draft7Validator(NESTED).validate(payload)  # the document admits it

    # Poison the LAST candidate there is: with no borrowed instance, the demanded base is
    # the only one, so there is nothing to fall through to.
    alone = check_widening(
        NESTED, _accept, (_declaration(),), instances=(),
        corpus=Held({demand: poison}), identity=DOC,
    )
    assert alone.outcome == "unproved_widening", (alone.outcome, alone.narrowings, alone.unproved)
    assert alone.accepted == 0
    assert "the document refuses" in alone.unproved[0], alone.unproved
    # The control: the same run with nothing held is a PASS, so the clause above is about
    # the held base and not about this document.
    assert (
        check_widening(
            NESTED, _accept, (_declaration(),), instances=(), corpus=Held(), identity=DOC
        ).outcome
        == "pass"
    )


def test_a_failed_draw_is_held_with_its_reason_so_a_replayed_run_reports_it() -> None:
    """An undrawable position costs a whole generation budget, so the FAILURE is held too.

    ``harness._Draws`` says why: an ``Unsatisfiable`` is the budget spent on filtered
    cases, and a store that held only successes would pay the most expensive draw there is
    on every run.  What makes it safe is the direction -- a held failure keeps the
    declaration ``unproved``, and ``unproved`` is a failure, so the worst a stale one can
    do is report work owed.

    The REASON travels with it, which is the clause this reads: a replayed run reports the
    sentence a drawing run reported, rather than a thinner one that would make the store
    visible in the verdict.  Both halves are read -- the failure is held with its sentence,
    and the sentence comes back out through the CHECK's own ``unproved`` line.
    """
    #: A schema ``hypothesis_jsonschema`` canonicalises to the empty strategy, so the draw
    #: raises rather than returning something.  The whole budget is what that costs.
    empty = {"allOf": [{"type": "string"}, {"type": "integer"}]}
    store = Held()
    draws = harness._Draws(corpus=store, identity=DOC)  # noqa: SLF001
    answer = draws.one(empty, ("class", AT, "uniqueItems", "2 distinct members"), {})
    assert len(answer) == 2 and answer[0] is None, answer
    assert isinstance(answer[1], str) and answer[1], "a held failure carries no reason"
    assert (draws.drawn, draws.replayed) == (1, 0)
    assert harness._Draws(corpus=store, identity=DOC).one(  # noqa: SLF001
        empty, ("class", AT, "uniqueItems", "2 distinct members"), {}
    ) == answer, "the failed draw was paid again"
    held = claimed("held widening answers", store.entries)

    #: And through the CHECK: the position a drawing run would have failed at is seeded
    #: with that run's answer, and the obligation reports ``unproved`` carrying the
    #: sentence rather than a thinner one of its own.
    seeded = Held({next(iter(held)): [None, "the strategy produced no instance (earlier run)"]})
    res = check_widening(
        NESTED, _accept, (_declaration(),), instances=({"box": {"tags": ["a", "b"]}},),
        corpus=seeded, identity=DOC,
    )
    assert res.outcome == "unproved_widening", (res.outcome, res.narrowings, res.unproved)
    assert res.drawn == 0 and res.replayed == 1, (res.drawn, res.replayed)
    assert "earlier run" in res.unproved[0], res.unproved


#: A schema whose draw has no bound worth waiting for and no filtering in it, so what ends
#: the draw below is the BUDGET and nothing else -- an ``Unsatisfiable`` here would be the
#: held-failure case above and not this one.
UNBOUNDED_DRAW: dict[str, Any] = {
    "type": "array",
    "minItems": 2000,
    "items": {
        "type": "object",
        "required": [f"p{i}" for i in range(200)],
        "properties": {f"p{i}": {"type": "string", "minLength": 120} for i in range(200)},
    },
}


def test_a_draw_the_budget_cut_is_not_held_because_a_cut_is_not_an_answer() -> None:
    """**The clause the accepts store has had all along and this one did not**
    (``adcp-client-python-pjc``).

    The paragraph above holds a FAILED draw, which is right: an ``Unsatisfiable`` is a
    whole generation budget spent on filtered cases and it is a fact about the position.
    A CUT is not that.  It says this process stopped asking, and held here it becomes
    evidence: :class:`corpus.Layered` serves it like any other entry and
    ``check_widening`` reports ``unproved_widening`` carrying "could not be drawn:
    OverBudget: ...", a sentence about a budget some other process chose.  Measured on
    ``trusted-match/offer.json#`` -- with the cut entry in place the pair graded in 8.8 s,
    with it removed the same pair did not finish in 600 s -- so the entry was the only
    thing making an unbounded draw look graded.

    Read through the REAL budget and the REAL draw, and both halves: the store holds
    nothing, and the cut reaches the caller as a cut rather than as a position that cannot
    be drawn.
    """
    store = Held()
    draws = harness._Draws(corpus=store, identity=DOC)  # noqa: SLF001
    position = ("class", AT, "uniqueItems", "an unbounded draw")
    with pytest.raises(harness.OverBudget):
        with harness.within(1):
            draws.one(UNBOUNDED_DRAW, position, {})
    assert store.puts == [], f"a budget cut was held as an answer: {store.entries}"
    assert store.entries == {}


def test_an_entry_recording_a_budget_cut_is_not_a_held_answer() -> None:
    """:func:`harness.records_a_cut`, over the spellings the shared cache actually held.

    The clause and the gate below are one predicate, so what it reads is worth stating
    directly -- and the inputs are measured rather than invented: 46 entries of the shared
    widening cache recorded a 30 s budget, 99 recorded a 20 s one, and a single entry from
    2026-10-31 spells the class ``_OverBudget`` with an empty message, which is why the
    name is sought anywhere in the sentence rather than only at its front.

    The two it must NOT read as cuts are the two this store exists to hold: a genuine
    undrawable position with its reason, and a drawn JSON ``null``.
    """
    assert harness.records_a_cut([None, "OverBudget: the grade did not finish inside 30 s"])
    assert harness.records_a_cut([None, "OverBudget: the grade did not finish inside 20 s"])
    assert harness.records_a_cut([None, "_OverBudget: "])
    assert not harness.records_a_cut(
        [None, "Unsatisfiable: 459 of 459 test cases failed a .filter() or assume() condition"]
    )
    assert not harness.records_a_cut([None]), "a drawn JSON null is an answer"
    assert not harness.records_a_cut([{"box": {"tags": ["a"]}}])


def test_a_drawn_null_is_an_answer_and_not_a_failure() -> None:
    """The two states are told apart by LENGTH, which is what the one-slot memo had wrong.

    ``_bases``' memo spelled a failed draw ``[None]``, and a document that admits ``null``
    makes a successful draw spell the same thing -- so a legitimate ``null`` base read as
    "this position cannot be drawn" and the declaration was unproved for the instrument's
    own reason.  One element is an answer whatever it is; two is a failure with its reason.
    """
    store = Held()
    nullable = {
        "type": "object",
        "properties": {"box": {"type": ["object", "null"]}},
        "additionalProperties": False,
    }
    position = ("reached", "/properties/box/properties/tags", 0)
    key = corpus_key(DOC, position=position)
    store.entries[key] = [None]
    assert harness._Draws(corpus=store, identity=DOC).one(nullable, position, {}) == [None]
    assert store.puts == [], "an answer of null was redrawn as though it were a failure"
    assert harness._Draws(corpus=Held({key: [None, "why not"]}), identity=DOC).one(
        nullable, position, {}
    ) == [None, "why not"]


# --------------------------------------------------------------------------- #
# 3. two key spaces, and the gate over the first one is unmoved
# --------------------------------------------------------------------------- #
def test_a_held_widening_base_lands_in_no_accepts_key_space() -> None:
    """**THE TRAP THIS ROW WAS MOST LIKELY TO FALL INTO, read from the tree.**

    ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` asserts
    ``extra == set()``: the committed accepts floor holds no entry the graded population
    does not ask for.  That side reads ``corpus.Store.keys``, an ``rglob`` of the
    DIRECTORY -- so a widening entry written into ``tests/accepts-corpus`` would make a
    gate that had just landed read red while nothing was wrong, and ``--write-corpus``'
    prune would delete every widening entry on the way past.

    So the two spaces are two directories, and the reading is behavioural: a real run of
    the obligation against the REAL widening store leaves the accepts floor and the accepts
    cache byte-identical, and the key it writes under is in neither of their key spaces.
    """
    before = (corpus_module.FLOOR.keys(), corpus_module.CACHE.keys())
    store = Held()
    res = check_widening(
        NESTED, _accept, (_declaration(),), instances=({},), corpus=store, identity=DOC
    )
    assert res.outcome == "pass", res.unproved
    written = claimed("keys a widening run writes", set(store.puts))
    assert written & (before[0] | before[1]) == set(), (
        "a widening draw computed a key the accepts corpus already holds"
    )
    assert (corpus_module.FLOOR.keys(), corpus_module.CACHE.keys()) == before, (
        "running the obligation moved the accepts corpus"
    )
    assert corpus_module.WIDENING_FLOOR.directory != corpus_module.FLOOR.directory
    assert corpus_module.WIDENING_CACHE.directory != corpus_module.CACHE.directory


def test_the_accepts_key_does_not_move_when_a_position_is_available() -> None:
    """**``corpus_key``'s new argument moves no existing key, BY CONSTRUCTION.**

    The accepts key is the address of the committed floor's entries, so a new field in the
    hashed material would have moved every one of them and left
    ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` red on a bundle
    nobody bumped -- a key change wearing a refactor.  ``position`` is therefore absent
    from the material when no caller names one, and this is the reading: the key a caller
    computes without a position is the key the committed tree is addressed by.

    Pinned against the TREE and not against a literal written here: the digests of the
    files ``tests/accepts-corpus`` holds are what the accepts half replays from, so a
    sample of graded pairs is asked for its key and the floor is asked whether it holds it.
    A literal would pin this test's own arithmetic instead.

    The set is ``claimed`` because it is derived from the graded population: a derivation
    that selected nothing would answer no pair, and "no pair is stranded" would then read
    green on an empty population -- §8's rule, and the reason the sample below is drawn
    from the named set rather than from whatever the derivation happened to yield first.
    """
    import test_emit

    keyed = {
        f"{g.ref.document}{g.ref.pointer}": corpus_key(
            test_emit.identity_of(g.ref), custom_formats=test_emit.FORMAT_STRATEGIES
        )
        for g in test_emit.graded()
    }
    pairs = claimed("graded pairs asked for an accepts key", set(keyed))
    answered = {name for name in pairs if keyed[name] in corpus_module.FLOOR.keys()}
    assert len(answered) > 2000, (
        f"only {len(answered)} of {len(pairs)} graded pairs are answered by the committed "
        "accepts floor; the key moved and every entry is stranded"
    )
    # And a position really does move it, so the clause above is not green because the
    # argument is ignored.
    sample = min(pairs)
    identity = {"document": sample.split("#")[0], "pointer": "#"}
    assert corpus_key(identity) != corpus_key(
        identity, position=("demand", [])
    )


# --------------------------------------------------------------------------- #
# 4. the committed floor: no run writes it, and --write-corpus fills it
# --------------------------------------------------------------------------- #
def test_no_run_writes_a_widening_entry_inside_the_checkout() -> None:
    """``corpus.Layered``'s write rule, for the space this row adds.

    ``test_no_run_writes_a_corpus_entry_inside_the_checkout``'s three readings, over the
    second store: the cache a run WRITES is outside this repository, ``.gitignore`` carries
    the cache directory's name for the case ``ADCP_CACHE`` points one back inside, and
    every file the floor holds is TRACKED -- an untracked entry there is a run that wrote
    the floor or a ``--write-corpus`` nobody committed.
    """
    assert not corpus_module.WIDENING_DIRECTORY.is_relative_to(REPO), (
        f"the widening cache writes inside the checkout: {corpus_module.WIDENING_DIRECTORY}"
    )
    assert corpus_module.WIDENING_STORE.cache.directory == corpus_module.WIDENING_DIRECTORY
    assert corpus_module.WIDENING_STORE.floor.directory == corpus_module.WIDENING_COMMITTED
    name = corpus_module.CACHE_ROOT.name
    done = subprocess.run(
        ["git", "check-ignore", "-q", f"{name}/x"], cwd=REPO, capture_output=True
    )
    assert done.returncode == 0, "git does not ignore a cache directory inside the checkout"

    floor = corpus_module.WIDENING_FLOOR.directory.relative_to(REPO)
    listed = subprocess.run(
        ["git", "ls-files", "--", str(floor)], cwd=REPO, capture_output=True, text=True
    )
    assert listed.returncode == 0, listed.stderr
    tracked = set(listed.stdout.split())
    present = {str(p.relative_to(REPO)) for p in corpus_module.WIDENING_FLOOR.files()}
    assert present - tracked == set(), (
        f"untracked entries in the committed widening corpus -- a run wrote the floor, or "
        f"a --write-corpus was not committed: {sorted(present - tracked)[:5]}"
    )


def test_every_committed_widening_entry_is_a_well_formed_held_answer(pytestconfig) -> None:
    """The floor's entries have the shape ``harness._Draws`` reads back, and nothing else.

    **NOT a currency gate, and the module docstring says why there is none**: this asserts
    the SHAPE of what is committed, not that the population's live positions are all
    covered.  One element is an answer; two is a failure carrying its reason; anything else
    is a file the harness would misread, which is the one way this directory can be wrong
    without a draw noticing.

    ``--write-corpus`` acts here, which is the same affordance the accepts gate and
    ``tests/test_keywords.py``'s grids have and for the same reason -- the thing that knows
    what the tree should contain is the thing that reads it.  It PROMOTES and never draws:
    the draw is a suite run, and the keys promoted are the ones that run left in the shared
    cache.  It does not PRUNE, because pruning needs the live key set and this space has no
    cheap reading of one.
    """
    if pytestconfig.getoption("--write-corpus"):
        wrote, absent = corpus_module.WIDENING_STORE.promote(corpus_module.WIDENING_CACHE.keys())
        print(
            f"--write-corpus: promoted {wrote} widening entries, "
            f"{len(absent)} the cache could not answer; the floor now holds "
            f"{corpus_module.WIDENING_FLOOR.entries()}"
        )
        return
    wrong = {}
    for path in corpus_module.WIDENING_FLOOR.files():
        try:
            held = json.loads(path.read_text())
        except (OSError, ValueError) as e:
            wrong[path.name] = f"unreadable: {e}"
            continue
        if not isinstance(held, list) or not 1 <= len(held) <= 2:
            wrong[path.name] = f"not a one- or two-element list: {str(held)[:80]}"
        elif len(held) == 2 and (held[0] is not None or not isinstance(held[1], str)):
            wrong[path.name] = f"a two-element entry that is not [None, reason]: {str(held)[:80]}"
    assert wrong == {}, wrong
    print(
        f"committed widening corpus: {corpus_module.WIDENING_FLOOR.entries()} entries, "
        f"{corpus_module.WIDENING_FLOOR.bytes_held()} bytes of content"
    )


def test_no_held_widening_entry_records_a_budget_cut() -> None:
    """**THE GATE READING 2 WAS MISSING: a declaration proved by a TIMEOUT is not proved.**

    ``docs/plan/final-state.md`` reading 2 -- "every declaration holds a value that
    demonstrates it... where an entry recording a budget cut is not a value" --
    and ``harness.records_a_cut`` carries why an entry like
    ``[null, "OverBudget: the grade did not finish inside 30 s"]`` is the worst thing this
    directory can hold: it is served like evidence and it is a reading of somebody's clock.

    **BOTH STORES, and each for its own reason.**  The FLOOR because
    ``--write-corpus`` promotes straight out of the cache into the repository, so the floor
    is where a cut becomes permanent and reviewed -- that is the half that makes this a gate
    on the artifact.  The CACHE because that is the store every lane on a machine actually
    grades against (:class:`corpus.Layered` reads the floor first and the cache second), so
    a cut sitting there is a green widening check nobody should believe, on this checkout
    and on every sibling one.  A gate over the floor alone would have been green for the
    whole of the window in which 146 cut entries accumulated in the cache.

    Not an allowlist and nothing to grow: the set is empty or the gate is red, and the
    failure names the files so a lane can read what it is deleting.  A fresh checkout has
    no cache and passes, which is correct -- there is nothing held to disbelieve.
    """
    poisoned: dict[str, str] = {}
    for store, which in (
        (corpus_module.WIDENING_FLOOR, "committed floor"),
        (corpus_module.WIDENING_CACHE, "shared cache"),
    ):
        for path in store.files():
            try:
                entry = json.loads(path.read_text())
            except (OSError, ValueError):
                continue  # the shape gate above owns an unreadable entry
            if harness.records_a_cut(entry):
                poisoned[f"{which}: {path}"] = str(entry)[:120]
    assert poisoned == {}, (
        f"{len(poisoned)} held widening entries record a budget cut rather than a value, so "
        f"every widening verdict that replays one is a statement about a clock: "
        f"{json.dumps(poisoned, indent=2, sort_keys=True)[:4000]}"
    )
