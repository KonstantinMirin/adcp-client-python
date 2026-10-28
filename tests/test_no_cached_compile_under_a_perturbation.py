"""A test that perturbs the compiler may not read the compile cache.

**The defect this forbids, found by two lanes independently on 2026-10-28.**
``tests/compiled.py`` keys one compile on a digest of every ``.py`` under ``codegen/``,
which is what makes it safe to share: edit the compiler and the key moves.  **A runtime
perturbation moves nothing.**  ``mock.patch`` and a bare attribute assignment both change
behaviour without changing a byte of source, so a cached entry is handed back and the
perturbation never runs.

Two tests did it and failed in two different ways, which is why a grep would not have
caught either reliably:

* ``tests/test_conj_rule_beside_a_type.py`` installed a SPY and called the cache.  Green
  cold, red warm, with nothing changed between the runs -- a cache hit unpickles a result
  the spy never saw, so the collected set comes back empty and the test's population
  assertion fails on a denominator of zero.
* ``tests/test_emit_product.py`` ran a PERTURBATION whose delta is graded against the
  unperturbed compile.  Worse than a crash: both halves share one cache entry, so the
  delta is zero against itself and the test passes while measuring nothing.

So the rule is **any test that perturbs the compiler at run time calls ``emit.emit``
directly**, and this test is why it cannot drift back.

**Both forms are detected, because only one of them was.** The first sweep looked for a
``compiled(...)`` call inside a ``with mock.patch(...)`` block and found one of the two --
the other assigns ``compiler._the_conjuncts_own_type = spy`` and restores it in a
``finally``, which no ``with`` statement contains.  A rule that catches one spelling of a
defect is a rule that reports the other as absent.
"""

import ast
import pathlib

#: The names whose assignment or patching changes the walk's behaviour without changing
#: its source.  Read as a PREFIX of the module a test imports, so ``compiler.anything``
#: and ``lower.union.anything`` are both perturbations: the test does not need to know
#: which attribute matters, only that a module of the walk was written to.
WALK = ("compiler", "emit", "bundle", "render", "harness", "keywords", "lower", "parse")


def _perturbs(node: ast.AST) -> bool:
    """Does this statement change a walk module's behaviour at run time?"""
    if isinstance(node, ast.With):
        return any(
            isinstance(item.context_expr, ast.Call)
            and "patch" in ast.unparse(item.context_expr.func)
            for item in node.items
        )
    if isinstance(node, ast.Assign):
        return any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id in WALK
            for target in node.targets
        )
    return False


def _cached_calls(node: ast.AST) -> list[int]:
    return [
        child.lineno
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == "compiled"
    ]


def test_no_test_reads_the_compile_cache_under_a_perturbation() -> None:
    """Over every test module, so a file added later is graded without anyone remembering.

    The population is asserted non-empty first: "no test does this" is free over a tree
    with no ``compiled`` callers at all, and this file would then pass while saying
    nothing -- which is the shape of the defect it exists to forbid.
    """
    offences: list[str] = []
    callers = 0
    for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
        tree = ast.parse(path.read_text())
        callers += len(_cached_calls(tree))
        for node in ast.walk(tree):
            if not _perturbs(node):
                continue
            # An assignment perturbs from its own line to the end of its enclosing
            # function, not just within a block, so for an Assign the scope is the
            # function that holds it.  Found by the lane: the spy's call sat in a
            # ``try`` beside the assignment and no ``with`` contained either.
            scope = node if isinstance(node, ast.With) else _function_holding(tree, node)
            for line in _cached_calls(scope) if scope is not None else []:
                if line >= node.lineno:
                    offences.append(f"{path.name}:{line} reads the cache under a perturbation")
    assert callers, "the denominator is empty: no test calls compiled() at all"
    assert not offences, "\n".join(offences)


def _function_holding(tree: ast.AST, target: ast.AST) -> ast.AST | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
            child is target for child in ast.walk(node)
        ):
            return node
    return None
