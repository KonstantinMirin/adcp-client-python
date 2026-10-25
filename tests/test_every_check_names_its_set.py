"""Section 8's last paragraph, enforced on this suite's own source.

    "A check is exhaustive over the set of nodes it claims, or it does not exist.  A
    check that enumerates a subset reports on that subset only, and says so."

Two things go wrong, and each has a ratchet here because each grew back once the rule
was only written down.  ``salesagent-j3k2l.15`` was "bound the suite: exhaustive over a
population, or deleted" and it is CLOSED; the surface was 63% non-exhaustive again when
``salesagent-j3k2l.47`` measured it, because the rule had no instrument.

**1. A CENSUS EQUALITY.**  ``assert len(emitted) == 42``.  It is one tree's reading of a
quantity every emitting row moves, so two rows in flight compute two different correct
values for it and no merge resolves that by picking a side -- the figure
``graded_properties == 567`` sat red on trunk and red on a branch at once, pinned at
neither, for weeks.  0 and 1 are not censuses: ``== 0`` is "this part is empty", which
the design asks for, and ``== 1`` is "exactly one", a claim about a single node.

**2. A CHECK THAT DOES NOT NAME THE SET IT RANGES OVER.**  A loop over a set derived
from the bundle or the emitted tree, with no assertion that the set has members.  A
derivation that selects nothing passes every assertion over it and is indistinguishable
from a working check: measured twice on this epic, once where 0 graded pairs held the
shape a fold was gated on, and once where a census of 90 copies reddened only when the
population grew to 92.

Both are RATCHETS over the counts below: they may fall and they may not rise.  A ratchet
and not a gate, because the residue is real -- a local fixture's ``examples=7`` is not a
census, and a few loops genuinely range over something named elsewhere in the same test
-- and a gate would be satisfied by spelling around the instrument.

THE INSTRUMENTS ARE IN THIS FILE and are deliberately simple AST readings.  Each was
fire-probed by breaking it on purpose; the probes are recorded on
``salesagent-j3k2l.47``.
"""

from __future__ import annotations

import ast
import pathlib

from tests.nodeset import claimed

TESTS = pathlib.Path(__file__).resolve().parent

#: Per file, the number of census equalities at ``salesagent-j3k2l.47``.  It was 230
#: before that row, measured by the instrument below: test_emit 138, test_enum 28,
#: test_applied_schema 21, test_emit_product 21, test_fragment_ref 17,
#: test_dump_exemptions 3, test_harness_halves 2.  What is left is local fixtures
#: (``examples=7``), facts about
#: pydantic's own rendering (``maxLength: 2083`` on ``HttpUrl``) and facts a named
#: document states (``['const'] == 3``) -- none of them a count over a derived set.
CENSUS_CEILING = {
    "test_emit.py": 13,
    "test_emit_product.py": 5,
    "test_enum.py": 4,
    "test_harness_halves.py": 2,
}

#: Per file, the number of test functions that range over a set derived from the bundle
#: or the emitted tree without naming it.  ``tests/nodeset.py``'s ``claimed`` is how a
#: check names one, and ``partitions`` names several at once.
UNNAMED_CEILING: dict[str, int] = {}

#: The derivations a check ranges over.  Each one reads the bundle or the emitted tree,
#: so a loop over it is a loop over a set whose size is a property of the inputs rather
#: than of the test -- which is exactly the set section 8 asks to be named.
DERIVATIONS = frozenset(
    {
        "portable",
        "population",
        "graded",
        "graded_reports",
        "nodes",
        "named_nodes",
        "root_enums",
        "emitted_enum_classes",
        "leaves",
        "referencing",
        "enums",
        "composing",
        "union_roots",
        "container_roots",
        "object_rules",
        "fragment_refs",
        "census",
        "emitted_unions",
        "emitted_union_bases",
        "emitted_union_aliases",
    }
)

#: ``claimed`` names a set and refuses an empty one; ``partitions`` names several and
#: refuses an empty whole.  A bare ``assert <set>`` does the first job too, so it counts.
NAMERS = frozenset({"claimed", "partitions"})


def _census_ints(node: ast.AST, consts: dict[str, ast.AST]) -> list[int]:
    """Every census integer an ``==`` comparator exposes, through containers and names.

    Two spellings hide a census from a scan for a literal beside an ``==``, and both
    were in this suite in quantity: an int inside a tuple, list, set or dict
    (``assert (a, b) == (76, 397)``), and an int behind a module-level constant
    (``assert len(reports) == PAIRS_PIN``).  Thirteen of the second kind were in
    ``test_emit.py`` alone, each re-pointed by hand at every emitting row.
    """
    if isinstance(node, ast.Constant):
        v = node.value
        return [v] if isinstance(v, int) and not isinstance(v, bool) and v >= 2 else []
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [n for e in node.elts for n in _census_ints(e, consts)]
    if isinstance(node, ast.Dict):
        return [n for e in node.values if e is not None for n in _census_ints(e, consts)]
    if isinstance(node, ast.Name) and node.id in consts:
        return _census_ints(consts[node.id], {})
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        # ``A_PIN - B_PIN`` is two pins.  Multiplication and floor division are not
        # followed: ``["x"] * (len(steps) // 2)`` derives a shape from the data.
        return _census_ints(node.left, consts) + _census_ints(node.right, consts)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return _census_ints(consts.get(node.value.id, ast.Pass()), {})
    return []


def _module_constants(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        t.id: n.value
        for n in tree.body
        if isinstance(n, (ast.Assign, ast.AnnAssign))
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(t, ast.Name) and n.value is not None
    }


def census_equalities(path: pathlib.Path) -> list[tuple[int, list[int]]]:
    """Every ``assert ... == <census>`` in one file, with its line and its integers."""
    tree = ast.parse(path.read_text())
    consts = _module_constants(tree)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
            continue
        for op, comparator in zip(node.test.ops, node.test.comparators):
            if isinstance(op, ast.Eq) and (ints := _census_ints(comparator, consts)):
                found.append((node.lineno, ints))
    return found


def _called(node: ast.AST) -> str:
    f = getattr(node, "func", None)
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _ranges_over_a_derivation(fn: ast.AST) -> bool:
    """Does this function iterate something read off the bundle or the emitted tree.

    A derivation consumed by ``next(...)`` WITH NO DEFAULT is excluded, and the reason
    is the behaviour the rule is about rather than the spelling: ``next(g for g in
    graded() if ...)`` RAISES ``StopIteration`` on an empty derivation, so it cannot
    pass vacuously and there is nothing for a non-emptiness assertion to add.  A
    ``next(..., default)`` is not excluded, because that one does go quiet.
    """
    guarded: set[int] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and _called(node) == "next" and len(node.args) == 1:
            guarded.update(id(n) for n in ast.walk(node.args[0]))
    for node in ast.walk(fn):
        if id(node) in guarded:
            continue
        iterables = []
        if isinstance(node, (ast.For, ast.AsyncFor)):
            iterables = [node.iter]
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            iterables = [g.iter for g in node.generators]
        for it in iterables:
            if any(_called(inner) in DERIVATIONS for inner in ast.walk(it)):
                return True
    return False


def _names_its_set(fn: ast.AST) -> bool:
    """Does it say the set has members.

    Two spellings, and both are a POSITIVE truthiness claim over something derived:
    ``claimed`` / ``partitions`` from ``tests.nodeset``, which refuse an empty set by
    construction, and a bare ``assert <expression>`` -- ``assert sites, "no site was
    graded"``, ``assert [d for d in documents if ...]``, ``assert n_sites and
    n_documents``.  An ``assert x == y`` does NOT count: it holds for two empty sets.
    Neither does ``assert not x``, which is the claim that a part IS empty.

    **AND A BARE ASSERT INSIDE THE LOOP DOES NOT COUNT**, which this missed until it
    was probed: ``for g in graded(): assert g.ref.document`` is a PER-MEMBER claim and
    an empty derivation runs the loop zero times, so it cannot fire -- which is the
    exact failure mode the rule is about.  Only an assertion the function reaches
    whatever the derivation returned is a claim about the SET, so the search does not
    descend into a loop body.  ``claimed`` and ``partitions`` are counted wherever they
    appear, because they take the set as an argument and are not per-member.
    """
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and _called(node) in NAMERS:
            return True
    return _asserts_a_set(fn.body if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) else [])


def _asserts_a_set(body: list[ast.stmt]) -> bool:
    """A positive truthiness assertion reachable without entering a loop."""
    for stmt in body:
        if isinstance(stmt, ast.Assert):
            test = stmt.test
            if isinstance(test, (ast.Compare, ast.Constant)):
                continue
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                continue
            return True
        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            continue  # a per-member claim: an empty derivation runs it zero times
        nested = [
            inner
            for field in ("body", "orelse", "finalbody")
            for inner in getattr(stmt, field, []) or []
            if isinstance(inner, ast.stmt)
        ]
        nested += [
            inner
            for handler in getattr(stmt, "handlers", []) or []
            for inner in handler.body
        ]
        if nested and _asserts_a_set(nested):
            return True
    return False


def unnamed_derivations(path: pathlib.Path) -> list[str]:
    """Test functions that range over a derivation and never name the set."""
    tree = ast.parse(path.read_text())
    return [
        fn.name
        for fn in tree.body
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        and fn.name.startswith("test_")
        and _ranges_over_a_derivation(fn)
        and not _names_its_set(fn)
    ]


def _suite() -> list[pathlib.Path]:
    return sorted(p for p in TESTS.glob("test_*.py") if p.name != pathlib.Path(__file__).name)


def test_no_check_pins_a_census_as_an_equality_beyond_the_ratchet() -> None:
    """Rule 1, ratcheted per file.  It may fall; it may not rise."""
    files = claimed("suite files", _suite())
    live = {p.name: census_equalities(p) for p in files}
    assert any(live.values()), "the instrument found nothing anywhere: it is broken"

    risen = {
        name: (len([i for _, ints in rows for i in ints]), CENSUS_CEILING.get(name, 0), rows)
        for name, rows in live.items()
        if len([i for _, ints in rows for i in ints]) > CENSUS_CEILING.get(name, 0)
    }
    assert risen == {}, {
        name: {"live": n, "ceiling": ceiling, "sites": [ln for ln, _ in rows]}
        for name, (n, ceiling, rows) in risen.items()
    }
    # And the ceiling itself may not carry a file that no longer has any: a stale entry
    # is a ratchet nobody can lower.
    stale = {
        name: CENSUS_CEILING[name]
        for name in CENSUS_CEILING
        if len([i for _, ints in live.get(name, []) for i in ints]) < CENSUS_CEILING[name]
    }
    assert stale == {}, f"lower these ceilings to the live count: {stale}"


def test_no_check_ranges_over_a_derived_set_without_naming_it() -> None:
    """Rule 2, ratcheted per file.  The non-emptiness is the part that cannot be left out.

    A derivation that selects nothing passes every assertion over it, so a check that
    walks one and never says the set has members is indistinguishable from a working
    check -- and that is not a theoretical failure here: two of them were measured on
    this epic in one day.
    """
    files = claimed("suite files", _suite())
    live = {p.name: unnamed_derivations(p) for p in files}
    assert sum(len(v) for v in live.values()) < sum(
        1 for p in files for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.FunctionDef)
    ), "the instrument flagged everything: it is broken"

    risen = {
        name: (names, UNNAMED_CEILING.get(name, 0))
        for name, names in live.items()
        if len(names) > UNNAMED_CEILING.get(name, 0)
    }
    assert risen == {}, {name: {"unnamed": names, "ceiling": c} for name, (names, c) in risen.items()}
    stale = {
        name: UNNAMED_CEILING[name]
        for name in UNNAMED_CEILING
        if len(live.get(name, [])) < UNNAMED_CEILING[name]
    }
    assert stale == {}, f"lower these ceilings to the live count: {stale}"
