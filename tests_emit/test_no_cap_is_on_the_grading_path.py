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

**AND FOUR MORE WENT WITH ``merge(bounds)``, each measured BEFORE it was touched and each
one that never fired** -- the frontier walk's ``depth: int = 32``, ``_ARM_DEPTH = 4``,
``_COMPOSE_DEPTH = 16`` and ``_normalize``'s inline ``16``.  Instrumented at their own
guards over the whole graded population (all 2,586 pairs of
``test_emit.graded_reports``): the frontier walk is entered 1,236 times and reaches depth
**5**, ``_violating`` 1,715 times and reaches depth **4**, ``_composed`` 10,292 times and
reaches depth **2**, and ``_normalize`` 2,178 times, **every one at depth 0**.  So all four
cut 0 nodes, which is ``witness._STORE_HOPS``' reading and not ``_FIXTURE_DEPTH``'s -- and
they go anyway, because §9's rule does not turn on whether a cap is reached today and the
next bundle rather than this reading would decide when 32, 4 and 16 began to cut.  A third
docstring was refuted on the way: ``_ARM_DEPTH``'s said *"the bound is above the measured
shape and not tuned to it"* and the measured shape reaches the bound exactly, with a margin
of one hop.

**THE CLAUSES, and each is read off the ANSWER or off the SOURCE, never off a second copy
of the walk.**  A test that re-implemented the descent to measure its depth would be the
divergence ``docs/plan/architecture.md`` §11 forbids; so clause 1 reads the returned
pointers, clause 2 reads ``codegen.bundle.nodes``' own descent, clause 3 reads the module's
source, clause 4 reads four ANSWERS a bundle cannot exhibit, and clause 5 is the one whose
population does not empty as the constants go.
"""

from __future__ import annotations

import ast
import pathlib
import sys

import constructed
import pytest
from fresh import BUNDLE
from nodeset import claimed

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
    #: The four ``merge(bounds)`` removed: the frontier walk's ``depth: int = 32``,
    #: ``_ARM_DEPTH = 4``, ``_COMPOSE_DEPTH = 16`` and ``_normalize``'s inline 16.
    "locations",
    "_violating",
    "_normalize",
    "_composed",
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


# --------------------------------------------------------------------------- #
# clause 4: the four bounds of ``merge(bounds)``, each read off the ANSWER
# --------------------------------------------------------------------------- #
#: A nest deeper than any of the four numbers that stood on this path, so one input
#: answers for all of them: 20 is past ``_ARM_DEPTH``'s 4 and past the 16 that
#: ``_COMPOSE_DEPTH`` and ``_normalize`` carried, and 40 is past the frontier walk's 32.
#: **Constructed and not drawn from the bundle, which is the point of the clauses below.**
#: This bundle's deepest reading is 5 frontier levels, 4 arm levels, 2 conjunct levels and
#: 0 reference hops -- measured over all 2,586 pairs -- so no document of it can exhibit a
#: truncation, and a clause that asked one to would be green for free on a bundle whose
#: numbers happened to be small. What the four bounds would have cut is the bundle AFTER
#: the one anybody measured, and that is a statement about the READING, so it is put to the
#: reading directly.
PAST_EVERY_BOUND = 20
PAST_THE_FRONTIER_BOUND = 40


def test_the_frontier_walk_reaches_past_the_bound_it_carried() -> None:
    """**Read off the ANSWER**: a frontier item under 40 levels of ``allOf`` is one
    ``locations(depth=32)`` could not return.

    The walk's own guard was ``left <= 0`` over a counter seeded from that parameter, so a
    node nested past it returned the empty frontier -- not a smaller one. Every location
    lost there is a subtree the accepts draw then paid in full, which is
    ``_FIXTURE_DEPTH``'s failure exactly (``harness.referring_positions``' own comment: *"65
    fixture positions at one node were silently dropped, and every dropped position is a
    subtree the accepts draw paid in full"*).

    The termination that replaced it is the one the walk always had: every hop descends
    into a sub-mapping of the node handed in, no ``$ref`` is followed because a reference is
    a string in a record, so the descent runs out of a finite tree.
    """
    node: dict = {"properties": {"x": {"type": "string", "maxLength": 3}}}
    for _ in range(PAST_THE_FRONTIER_BOUND):
        node = {"allOf": [node]}
    found = harness.locations(node)
    assert [one.at for one in found] == ["/x"], found
    assert found[0].pointers == ("/allOf/0" * PAST_THE_FRONTIER_BOUND + "/properties/x",)


def test_a_conditional_arm_is_descended_past_the_bound_it_carried() -> None:
    """**Read off the ANSWER**: a witness from an arm nested 7 keys deep is one
    ``_ARM_DEPTH = 4`` could not derive.

    ``harness._violating`` is the input half of ``refused_witnesses``, so an arm the bound
    cut is a witness never built and a refuses-check that did not run -- and the pair still
    reads ``pass``, on the witnesses that WERE offered. That is §9's *"recorded as though
    something had been learned"*, which is why this is read off the derivation and not off
    the cap.

    **AND THE BOUND'S MARGIN WAS MEASURED AT ZERO**: over the whole graded population the
    descent reaches depth 4, which is the bound, so the first document to nest one key
    further would have been truncated in silence. The constant's own comment claimed the
    opposite -- *"the bound is above the measured shape and not tuned to it"* -- which is a
    third docstring on this path refuted by instrumenting it.
    """
    arm: dict = {"required": ["leaf"]}
    instance: dict = {"leaf": 1}
    for _ in range(7):
        arm = {"properties": {"k": arm}}
        instance = {"k": instance}
    witnesses = list(harness._violating(arm, instance))
    assert [keyword for _, keyword, _ in witnesses] == ["required"], witnesses
    candidate, _, how = witnesses[0]
    assert how.count("at 'k'") == 7, how
    assert harness.conforms(arm, candidate) is False, candidate


def test_a_local_pointer_chain_longer_than_the_bound_is_read_to_its_end() -> None:
    """**Read off the ANSWER, for both readings that carried a 16**: the fact at the far end
    of a 20-link chain arrives at the composed pointer.

    ``_normalize``'s was an inline ``depth > 16`` and ``_composed``'s was
    ``_COMPOSE_DEPTH``, and both cut the same shape -- a chain of LOCAL pointers, which
    ``codegen.bundle.record`` leaves exactly as the document writes them. Past the
    sixteenth link each reading returned the node it had reached, which states nothing in
    ``FOLDED_FACTS``, so every fact the chain's end declares was ABSENT at the composing
    pointer and ``check_widening`` reported ``unproved`` for a fact the document plainly
    states.

    Both halves are asserted here because the deleted constant's own comment argued the two
    readings must cut ALIKE (*"two instruments that cut a traversal at different places
    disagree about node identity"*). They now agree by terminating on the same fact -- the
    pointer already followed -- so the agreement is read as one answer over one chain
    length rather than as two numbers being equal.
    """
    links = {
        f"N{i}": {"$ref": f"#/definitions/N{i + 1}"} for i in range(PAST_EVERY_BOUND)
    }
    links[f"N{PAST_EVERY_BOUND}"] = {"type": "string", "maxLength": 7}
    root = {"definitions": links}
    assert harness._normalize(root["definitions"]["N0"], root) == {
        "type": "string",
        "maxLength": 7,
    }

    chain = {
        f"C{i}": {"allOf": [{"$ref": f"#/definitions/C{i + 1}"}]}
        for i in range(PAST_EVERY_BOUND)
    }
    chain[f"C{PAST_EVERY_BOUND}"] = {"type": "object", "required": ["deep"]}
    composing = {"definitions": chain}
    assert harness._composed(composing["definitions"]["C0"], composing) == {
        "type": "object",
        "required": ["deep"],
    }


def test_a_self_referential_pointer_chain_settles_on_the_pointer() -> None:
    """**The terminator, exercised**: the hazard the deleted ``16`` named in its own
    comment -- ``# a self-referential $defs chain`` -- closes on the pointer instead.

    With both numbers gone, ``followed`` is the only thing standing between these readings
    and a hang, so the three shapes that can close a cycle are put to them rather than
    assumed from the one the bundle happens to hold: a node's own ``$ref``, an ``allOf``
    conjunct that is a bare pointer, and a union BRANCH that is one. The third is the one a
    pointer set at the reference hop alone would miss -- ``_branch_target`` resolves the
    branch, so the fold descends into the node the pointer names and would arrive back at
    the same node with nothing to tell it so.

    The recursion limit is lowered for the calls so that a reading which did NOT close
    fails as a ``RecursionError`` in this test rather than taking the interpreter down --
    ``test_the_fixture_walk_closes_a_reference_cycle_on_the_pointer``'s own device.

    Each answer is ``{}`` or the node's own keys: a declined hop leaves the member as the
    document writes it, which states no fact in ``FOLDED_FACTS``, so the fact is absent at
    the composed pointer rather than invented there. That is the fail-safe direction both
    readings already take for a pointer naming nothing.
    """
    reference = {"definitions": {"A": {"$ref": "#/definitions/B"}, "B": {"$ref": "#/definitions/A"}}}
    conjunct = {
        "definitions": {
            "A": {"allOf": [{"$ref": "#/definitions/B"}], "title": "A"},
            "B": {"allOf": [{"$ref": "#/definitions/A"}], "title": "B"},
        }
    }
    branch = {"definitions": {"A": {"anyOf": [{"$ref": "#/definitions/A"}, {"type": "null"}]}}}
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(400)
    try:
        assert harness._normalize(reference["definitions"]["A"], reference) == {}
        assert harness._composed(conjunct["definitions"]["A"], conjunct) == {"title": "A"}
        assert harness._normalize(branch["definitions"]["A"], branch) == {}
    finally:
        sys.setrecursionlimit(limit)


# --------------------------------------------------------------------------- #
# clause 5: the repetitions, which is the population that does not empty
# --------------------------------------------------------------------------- #
def test_every_recursion_this_module_performs_counts_only_what_the_input_states() -> None:
    """**THE POPULATION IS THE RECURSIONS AND NOT THE CONSTANTS**, which is the only reason
    this clause says anything.

    :func:`test_no_reading_of_the_grading_path_declares_a_depth_parameter` reads a NAMED
    list of functions for a parameter spelled ``depth`` and for a constant whose name ends
    ``_DEPTH``.  Both halves range over the CAPS' OWN SPELLING, so both go green over an
    empty set the moment the last one is deleted -- ``docs/plan/final-state.md``'s *"a check
    that passes when nothing happens decides nothing"* -- and neither could see
    ``_normalize``'s bound at all, because it was an inline ``16`` in no constant and no
    signature.  ``tests_emit/test_witness_construction.py``'s
    ``test_every_repetition_this_module_performs_counts_something_the_input_states`` is the
    same correction for ``codegen/verify/witness.py``, made when ``_STORE_HOPS`` went; this
    is it for this module, stated over RECURSION rather than over ``range()`` because
    recursion is the form a tree walker repeats in.

    **The population is every call edge inside a cycle of this module's own call graph**, so
    it holds as long as the module walks a tree at all -- which is what the module is for,
    and which no deletion of a constant can empty.  For each such edge a COUNTER is an
    argument of the form ``parameter ± literal``: the shape a hop count travels in, and the
    shape all four deleted bounds travelled in (``left - 1`` three times in the frontier
    walk, ``depth + 1`` once each in ``_violating`` and ``_composed`` and twice in
    ``_normalize``).

    **And the assertion is over what that counter's GUARD compares against, because that is
    where a cap differs from a position.**  ``_fixtured``'s ``rebuilt`` hands on ``i + 1``
    and stops at ``i == len(_segments)`` -- a number the INPUT states, the pointer's own
    length -- so it repeats exactly as far as its input goes.  A guard comparing the counter
    to an integer LITERAL or to one of this module's own integer CONSTANTS stops the walk at
    a number nobody read off the document, and every node past it is a reading that did not
    happen.

    **THE SCOPE: the guard is read in the function that HANDS THE COUNTER ON**, because a
    counter and the comparison that cuts it are one decision and belong in one function --
    and that is where all four of ``merge(bounds)``' bounds sat, and where
    ``_FIXTURE_DEPTH``'s and ``_OWN_DEPTH``' sat before them.  **One counter in this module
    is cut elsewhere and it is named rather than caught: ``Fixtures.reduced``'s ``depth: int
    = 8``**, handed on by ``_derived_pin`` as ``depth - 1`` and cut by ``_pin``'s ``depth <=
    0`` one frame away.  It is measured and it FIRES -- 273 of 1,696 ``_pin`` calls over the
    whole graded population, re-entering to the full 8 -- and it is not this lane's, for the
    reason ``BUDGET = 30`` and ``check_accepts``' ``examples: int = 25`` are not: when it
    expires ``_pin`` returns ``NONE`` and *"the position then stands as the document states
    it"*, so no location, no fact and no witness is lost and the whole of what it bounds is
    how much SAVING is computed before the draw is paid in full.  Every one of the four
    bounds this clause does catch dropped an ANSWER instead -- a frontier item, a witness, a
    folded fact -- which is the difference, and the cost that makes the fifth one's removal
    a draw question is ``adcp-client-python-2i99``'s and ``-5pb``'s.
    """
    tree = ast.parse(MODULE.read_text())
    #: ``(the qualified name, the node)`` per function, and the QUALIFICATION is the point:
    #: this module declares several nested walks spelled ``walk``, so a map keyed on the
    #: bare name keeps one of them and silently drops the others -- including
    #: ``locations``', which is one of the four this clause exists to have caught.
    functions = _functions_of(tree)
    spellings = {name.rsplit(".", 1)[-1] for name, _ in functions}
    constants = _integer_constants_of(tree)

    calls = {name: _calls_of(node, spellings) for name, node in functions}
    graph = {
        name: {callee for callee, _ in found}
        for name, found in calls.items()
    }
    recursive = _reaches_itself(graph, {name.rsplit(".", 1)[-1] for name in graph})
    edges = {
        (name, callee)
        for name, found in calls.items()
        if name.rsplit(".", 1)[-1] in recursive
        for callee, _ in found
        if callee in recursive
    }
    claimed("recursive call edges of codegen/harness.py", edges)

    capped: dict[str, list[str]] = {}
    for name, node in functions:
        if name.rsplit(".", 1)[-1] not in recursive:
            continue
        for callee, call in calls[name]:
            if callee not in recursive:
                continue
            for counter in _counters_handed_on(call):
                for guard in _guards_on(node, counter):
                    if _is_a_number_this_module_chose(guard, constants):
                        capped.setdefault(f"{name} -> {callee}", []).append(
                            f"{counter} stopped at {ast.unparse(guard)}"
                        )
    assert not capped, (
        f"{capped}: a recursion of this module counts its own hops and stops at a number "
        "nobody read off the document, so every node past it is a reading that did not "
        "happen (docs/plan/final-state.md reading 1)"
    )


def _functions_of(tree: ast.Module) -> list[tuple[str, ast.AST]]:
    """Every function this module declares, under a name that is unique in it.

    The name is the chain of enclosing ``def``/``class`` statements.  A bare name is not
    unique here -- ``walk`` is declared inside several readings -- and a map keyed on one
    keeps whichever came last, which is how a clause over the module's recursions can range
    over a population that silently omits most of them.
    """
    out: list[tuple[str, ast.AST]] = []

    def take(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                if not isinstance(child, ast.ClassDef):
                    out.append((name, child))
                take(child, f"{name}.")
            else:
                take(child, prefix)

    take(tree, "")
    return out


def _integer_constants_of(tree: ast.Module) -> set[str]:
    """This module's own integer constants, read off the module BODY.

    **And not off ``ast.walk``**, which is the distinction ``witness.py``'s clause was
    written wrong first and then measured: walking the whole tree collects every LOCAL
    assignment too, so a quantifier minimum the document states reads as a number this
    module chose and the clause forbids the reading instead of the cap.
    """
    return {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int)
        if not isinstance(node.value.value, bool)
    }


def _calls_of(holder: ast.AST, spellings: set[str]) -> list[tuple[str, ast.Call]]:
    """Every call this function's OWN body makes to a function of this module.

    A nested ``def``'s calls belong to the nested ``def``, which ``ast.walk`` cannot tell:
    without the exclusion the enclosing reading owns its inner walk's recursion and a
    counter is attributed to a function that declares no guard on it.

    The callee is read as a SPELLING -- ``name(...)`` or ``self.name(...)`` -- because that
    is how Python resolves it at the call site, and a method and a module function spelled
    alike are one edge for this clause's purpose either way.
    """
    nested = {
        inner
        for statement in holder.body  # type: ignore[attr-defined]
        for node in ast.walk(statement)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for inner in ast.walk(node)
    }
    out = []
    for node in ast.walk(holder):
        if node in nested or not isinstance(node, ast.Call):
            continue
        function = node.func
        spelling = (
            function.id
            if isinstance(function, ast.Name)
            else function.attr
            if isinstance(function, ast.Attribute)
            else None
        )
        if spelling in spellings:
            out.append((spelling, node))
    return out


def _reaches_itself(graph: dict[str, set[str]], spellings: set[str]) -> set[str]:
    """Every spelling of this module that its own calls can come back to.

    The transitive closure and not a direct self-call: ``Fixtures.reduced`` re-enters itself
    through ``_pin``, ``_derived_pin`` and ``value``, so a clause reading direct recursion
    alone would not see a counter handed around a cycle of four at all.
    """
    reach: dict[str, set[str]] = {}
    for name, edges in graph.items():
        reach.setdefault(name.rsplit(".", 1)[-1], set()).update(edges)
    for name in spellings:
        reach.setdefault(name, set())
    while True:
        grown = False
        for name in reach:
            wider = reach[name] | {
                further for edge in reach[name] for further in reach.get(edge, ())
            }
            if wider != reach[name]:
                reach[name] = wider
                grown = True
        if not grown:
            return {name for name in reach if name in reach[name]}


def _counters_handed_on(call: ast.Call) -> list[str]:
    """The parameters this call hands on as ``parameter ± literal``."""
    out = []
    for argument in (*call.args, *(keyword.value for keyword in call.keywords)):
        if not isinstance(argument, ast.BinOp) or not isinstance(argument.op, (ast.Add, ast.Sub)):
            continue
        out.extend(
            side.id for side in (argument.left, argument.right) if isinstance(side, ast.Name)
        )
    return out


def _guards_on(holder: ast.AST, counter: str) -> list[ast.expr]:
    """What this function compares ``counter`` against, which is where it stops."""
    out: list[ast.expr] = []
    for node in ast.walk(holder):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        if not any(isinstance(one, ast.Name) and one.id == counter for one in operands):
            continue
        out.extend(
            one for one in operands if not (isinstance(one, ast.Name) and one.id == counter)
        )
    return out


def _is_a_number_this_module_chose(guard: ast.expr, constants: set[str]) -> bool:
    """Is this bound an integer nobody read off the document?

    An integer literal and one of this module's own integer constants are the two spellings.
    ``len(...)``, a subscript and an attribute are the INPUT's own numbers and are exactly
    what a repetition is allowed to stop at.
    """
    if isinstance(guard, ast.Constant):
        return isinstance(guard.value, int) and not isinstance(guard.value, bool)
    return isinstance(guard, ast.Name) and guard.id in constants
