"""**NO READING OF THE GRADING PATH CARRIES A DEPTH BOUND**, asserted rather than reviewed.

``docs/plan/architecture.md`` §9: *"A time budget, a depth limit, a cap on examples: each
is a parameter added so that an explosion stops being visible, and every pair such a
budget cuts is a check that did not run, recorded as though something had been learned."*
``docs/plan/final-state.md`` reading 1 spells the same rule as a property of the three
checks: *"NO CHECK CARRIES A BUDGET, A DEPTH LIMIT OR AN EXAMPLE COUNT.  Each of the three
terminates structurally."*

**WHY THIS FILE IS A GATE AND NOT A REVIEW, which is ``adcp-client-python-hzio.7``'s whole
subject.**  Two bounds stood on this path and each carried a docstring saying it was a
guard that the walk did not actually terminate on.  Both sentences were false and both
survived because nothing read them:

* ``harness._FIXTURE_DEPTH = 12`` said *"the guard that terminates the walk is the visited
  SET below and this is only a bound on an unreasonable answer"*.  Raised to 10,000 over
  this bundle the answer MOVED at **73 of the 4,567** raw nodes that have a fixture
  position at all, and ``core/creative-representation.json#`` went from **79 positions to
  144**.  The visited set is consulted on the ``$ref`` hop alone; what the 12 cut was the
  PLAIN subschema descent, which terminates on the document being finite and needs no
  number.
* ``harness._OWN_DEPTH = 8`` said the fold *"has to reach the same depth"* as the
  composition.  Raised to 10,000 over the **215,019** record nodes of this bundle the four
  readings it bounded moved at **1,358** of them, and
  ``account/list-accounts-response.json``'s root went from **9 stated patterns to 24**.

Each of those four readings is the INPUT half of a witness derivation
(``harness.refused_witnesses``, ``harness.admitted_witnesses``), so a truncated reading is
a witness never built and a check that never ran -- §9's "recorded as though something had
been learned", arriving as arithmetic.

**THE CLAUSES, and each is read off the ANSWER or off the SOURCE, never off a second copy
of the walk.**  A test that re-implemented the descent to measure its depth would be the
divergence ``docs/plan/architecture.md`` §11 forbids; so clause 1 reads the returned
pointers, clause 2 reads ``codegen.bundle.nodes``' own descent, and clause 3 reads the
module's source.
"""

from __future__ import annotations

import ast
import pathlib
import sys

import constructed
import pytest
from fresh import BUNDLE

from codegen import bundle, harness

MODULE = pathlib.Path(harness.__file__)

#: Every function of ``codegen/harness.py`` that recursively descends a document or a
#: record and therefore once carried a number.  Named, because a bound reintroduced in a
#: function nobody listed is a bound nobody grades -- and clause 3 asserts the list is
#: still a list of live functions, so a rename reddens here rather than silently emptying
#: the population.
UNBOUNDED = (
    "referring_positions",
    "own_facts",
    "conditionals",
    "declared_keys",
    "property_declarations",
    "stated_patterns",
)

#: The one document whose fixture walk reaches deepest, and the reading is its own: 196
#: positions at its root, the deepest at 32 pointer segments.  **A NAMED DOCUMENT and not
#: the whole bundle**, because asking ``referring_positions`` for every raw node of every
#: document costs 87.5 s and this clause needs one answer the bound could not have given.
DEEPEST = "media-buy/create-media-buy-request.json"


@pytest.fixture(scope="module")
def raw():
    """``bundle.read`` memoised for this module, which is the reader the walk takes."""
    held: dict[str, object] = {}

    def read(document: str):
        if document not in held:
            held[document] = bundle.read(BUNDLE, document)
        return held[document]

    return read


# --------------------------------------------------------------------------- #
# clause 1: the fixture walk reaches past every bound that stood on it
# --------------------------------------------------------------------------- #
def test_the_fixture_walk_returns_a_position_deeper_than_the_bound_it_carried(raw) -> None:
    """**Read off the ANSWER**: a returned pointer deeper than 12 segments is a position
    ``_FIXTURE_DEPTH = 12`` could not have returned.

    The relative pointer ``harness.Referring`` carries accumulates one segment per
    structural hop, so its segment count IS the depth the walk reached -- which is why this
    needs no instrument inside the walk and no second copy of it.  The assertion is a
    strict inequality against the bound rather than an equality on 32, because the depth is
    a property of the deepest document (§9: *"a structural terminator means that maximum is
    a property of the deepest document rather than of a constant"*) and a bundle bump may
    move it.  What may NOT move is that it exceeds a constant nobody chose any more.
    """
    found = harness.referring_positions(raw, DEEPEST, "#", frozenset(bundle.portable(BUNDLE)))
    assert found, f"{DEEPEST} states no fixture position at its root"
    deepest = max(len([s for s in one.pointer.split("/") if s]) for one in found)
    assert deepest > 12, (
        f"{DEEPEST}# reaches {deepest} pointer segments over {len(found)} positions; "
        "a walk that cannot pass 12 is one a depth bound is still cutting"
    )


def test_the_fixture_walk_closes_a_reference_cycle_on_the_pointer(raw) -> None:
    """**The terminator, exercised**: a document referring to itself returns rather than
    recurses, and nothing but the visited set makes that true.

    ``docs/plan/architecture.md`` §9: *"A reference reaching a pointer whose construction is
    already in progress is a back edge."*  With the depth bound gone, ``seen`` is the only
    thing standing between this walk and a hang, so it is put to a cycle here rather than
    assumed from the one the bundle happens to hold.  The recursion limit is lowered for the
    call so that a walk which did NOT close would fail as a ``RecursionError`` inside this
    test instead of taking the interpreter down.
    """
    cycle = {
        "a.json": {"properties": {"next": {"$ref": "b.json#"}}},
        "b.json": {"properties": {"back": {"$ref": "a.json#"}}},
    }
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(400)
    try:
        found = harness.referring_positions(cycle.__getitem__, "a.json", "#", frozenset(cycle))
    finally:
        sys.setrecursionlimit(limit)
    assert [one.pointer for one in found] == ["/properties/next"], found


# --------------------------------------------------------------------------- #
# clause 2: "anywhere under it" is a claim only an unbounded walk can make
# --------------------------------------------------------------------------- #
def test_every_pattern_a_record_states_is_one_stated_patterns_reaches() -> None:
    """``harness.stated_patterns`` says *"every ``pattern`` this node states anywhere under
    it"*, and this is that sentence as an equality in the one direction it has.

    **The left-hand side is ``codegen.bundle.nodes``' own descent** -- the table's descent
    column, which ``docs/plan/architecture.md`` §11 names as the one owner of "what is a
    subnode" -- so neither side of this is a copy of the other's walk.  The relation is
    ``⊇`` and not ``==`` on purpose: ``stated_patterns`` reads every mapping VALUE, so it
    also reaches a ``pattern`` at a position the descent column does not descend to, and
    that surplus is the function's own claim rather than a defect.

    Measured on this bundle: **0 of 215,019 record nodes** state a pattern this reading
    misses, and the whole sweep costs under a second over the 2,584 nodes the grading path
    actually asks for (0.83 s, 8,581 patterns) -- which is the answer to the deleted
    bound's own stated fear that "a graded node reaches 683,849 bytes".
    """
    short: dict[str, list[str]] = {}
    checked = 0
    for document, record in constructed.records().items():
        for pointer, node in bundle.nodes(record):
            if not isinstance(node, dict):
                continue
            checked += 1
            reached = set(harness.stated_patterns(node))
            own = {
                inner["pattern"]
                for _, inner in bundle.nodes(node)
                if isinstance(inner, dict) and isinstance(inner.get("pattern"), str)
            }
            if isinstance(node.get("pattern"), str):
                own.add(node["pattern"])
            if own - reached:
                short[f"{document}{pointer}"] = sorted(own - reached)
    assert checked, "no record node was read"
    assert not short, short


# --------------------------------------------------------------------------- #
# clause 3: the source carries no bound to reintroduce
# --------------------------------------------------------------------------- #
def test_no_reading_of_the_grading_path_declares_a_depth_parameter() -> None:
    """**A cap may not return as a default argument** (``adcp-client-python-hzio.6``): *"a
    parameter with a generous default is the same cap with a politer name; what is forbidden
    is the existence of a knob whose setting can turn a check off."*

    So the reading is over the SIGNATURE and over the names each function closes on: no
    parameter spelled ``depth``, and no reference to a module constant whose name ends in
    ``_DEPTH``.  Both halves are needed -- the bounds that stood here were one of each: a
    ``depth: int = 0`` parameter on four functions and a module constant read by two.
    """
    tree = ast.parse(MODULE.read_text())
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = [name for name in UNBOUNDED if name not in functions]
    assert not missing, f"{missing} is named here and is not a function of {MODULE.name}"
    carried: dict[str, list[str]] = {}
    for name in UNBOUNDED:
        node = functions[name]
        args = node.args
        parameters = [
            a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs) if a.arg == "depth"
        ]
        constants = sorted(
            {
                inner.id
                for inner in ast.walk(node)
                if isinstance(inner, ast.Name) and inner.id.endswith("_DEPTH")
            }
        )
        if parameters or constants:
            carried[name] = [*parameters, *constants]
    assert not carried, carried
