"""D13's import rule, asserted rather than trusted.

**A lowering under ``codegen/lower/`` imports ``codegen.compiler`` and
``codegen.refusal``, and nothing else of this package.**

The rule is not stylistic.  ``codegen.emit`` holds the dispatch table and imports
each lowering, so an import back the other way closes a cycle -- and under
``runpy`` (``python -m codegen.emit``) that cycle resolves into TWO module objects
rather than into an ``ImportError``: ``codegen.emit`` is bound once as ``__main__``
and once under its own name, and a class held by identity across that boundary is
two classes.  That is the failure D12 exists to prevent for ``Refusal``, one layer
in, and step 3 hit the ``Refusal`` version of it.

Resolved by AST and not by grep, for three reasons a text search gets wrong:

* ``from codegen import compiler, emit`` is one statement naming two modules, and a
  line-oriented search reports the line rather than the names.
* ``from . import emit`` and ``from .. import emit`` name the same module without
  the string ``codegen`` appearing anywhere, so a grep for ``codegen.emit`` misses
  them entirely.  :func:`_resolved` walks the relative level the way Python does.
* a lazy ``import codegen.emit`` inside a function body is the exact dodge this
  rule exists to close, and it is indistinguishable from a comment to a grep.

So the walk visits every ``Import`` and ``ImportFrom`` node at any depth, including
one inside a function, a ``try`` or an ``if TYPE_CHECKING`` block -- a
``TYPE_CHECKING`` import is still a violation, because it hides the cycle from the
type checker without removing it.

Perturbed: adding ``from codegen import emit`` to one lowering reddens
:func:`test_a_lowering_imports_only_the_compiler_and_the_refusal` and names that
module.  A rule nothing can break is a finding about the rule.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: What a lowering may name under ``codegen``.  Everything else is a violation,
#: including ``codegen.emit``, ``codegen.bundle`` and ``codegen.harness``.
PERMITTED = frozenset({"codegen.compiler", "codegen.refusal"})

LOWER = Path(__file__).resolve().parents[1] / "codegen" / "lower"
#: The package a module under ``codegen/lower/`` lives in, for resolving a relative
#: import the way Python does.
PACKAGE = ("codegen", "lower")


def _modules() -> list[Path]:
    """Every module of the package, ``__init__`` included.

    ``__init__`` is not exempt: it is imported whenever any lowering is, so an
    ``emit`` import there is the same cycle through a different file.
    """
    return sorted(LOWER.glob("*.py"))


def _resolved(node: ast.Import | ast.ImportFrom) -> list[str]:
    """Every MODULE one import statement names.

    ``import a.b`` names ``a.b``.  ``from a.b import c`` names ``a.b``, and names
    ``a.b.c`` too only when ``a.b`` is a package whose ``c`` could be a submodule
    -- which here is the one case ``from codegen import emit``, so the join is
    applied when the stem is ``codegen`` and the symbol reading is taken
    otherwise.  A relative ``from . import x`` / ``from ..y import z`` resolves
    against :data:`PACKAGE` by dropping ``level - 1`` trailing parts, which is what
    ``importlib`` does: level 1 is the module's own package, so ``from . import
    emit`` names ``codegen.lower.emit`` and not ``codegen.emit``.
    """
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    base = list(PACKAGE[: len(PACKAGE) - (node.level - 1)]) if node.level else []
    if node.module:
        base += node.module.split(".")
    stem = ".".join(base)
    if stem in ("codegen", ".".join(PACKAGE)):
        # Every imported name here IS a submodule: ``from codegen import compiler,
        # emit`` and ``from . import enum`` are the two spellings that reach a
        # module without naming it in the ``module`` slot.
        return [stem, *(f"{stem}.{a.name}" for a in node.names)]
    return [stem]


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Import) and any(a.name == "codegen" for a in node.names):
            # A bare ``import codegen`` binds the package and reaches every
            # submodule already imported elsewhere in the process, so it is a
            # violation on its own.
            out.append("codegen")
        for name in _resolved(node):
            if not name.startswith("codegen."):
                continue
            # A submodule of a permitted module is permitted (``codegen.compiler``
            # has none today); anything else under ``codegen`` is not.
            if name in PERMITTED or any(name.startswith(p + ".") for p in PERMITTED):
                continue
            out.append(name)
    return sorted(set(out))


def test_the_package_has_modules_to_grade() -> None:
    """The denominator.  A rule measured over an empty set is green and says
    nothing, and ``codegen/lower/`` held only a docstring on the base."""
    assert _modules(), LOWER


@pytest.mark.parametrize("path", _modules(), ids=lambda p: p.name)
def test_a_lowering_imports_only_the_compiler_and_the_refusal(path: Path) -> None:
    assert _violations(path) == [], (
        f"{path.relative_to(LOWER.parents[1])} imports {_violations(path)} of this package; "
        f"D13 permits {sorted(PERMITTED)} and nothing else -- an import of codegen.emit is a "
        "cycle that runpy resolves into two module objects"
    )


def test_the_rule_catches_each_spelling(tmp_path: Path) -> None:
    """The instrument, on four spellings and one non-violation.

    Without this, a rule that resolved nothing would pass over a package whose
    modules are all clean, and the perturbation in the module docstring would be
    the only thing that ever exercised it.
    """
    cases = {
        "import codegen.emit": ["codegen.emit"],
        "from codegen import emit": ["codegen.emit"],
        # A relative import resolves the way ``importlib`` does: level 1 is the
        # module's own package, so ``from . import emit`` names a SIBLING of the
        # lowering, which the rule forbids along with the package itself -- a
        # lowering reaching another lowering is reaching another shape's decision.
        "from . import emit": ["codegen.lower", "codegen.lower.emit"],
        "from .. import bundle": ["codegen.bundle"],
        "from codegen.harness import resolve": ["codegen.harness"],
        "def f():\n    from codegen import emit": ["codegen.emit"],
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from codegen import emit": [
            "codegen.emit"
        ],
        "from codegen import compiler\nfrom codegen.refusal import Refusal": [],
        "from codegen.compiler import Module\nimport jsonschema": [],
    }
    for source, expected in cases.items():
        probe = tmp_path / "probe.py"
        probe.write_text(source + "\n")
        assert _violations(probe) == expected, source
