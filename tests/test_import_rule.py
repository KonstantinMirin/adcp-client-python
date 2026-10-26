"""The two import boundaries that are about DESIGN, asserted rather than trusted.

``docs/plan/architecture.md`` §10 says which two those are, and why there used to be
a third.  The third was a prohibition on the LOWERINGS: a module under
``codegen/lower/`` could name ``codegen.compiler`` and ``codegen.refusal`` and
nothing else of this package, because ``codegen.emit`` held the dispatch table and
imported every lowering -- so an import back the other way closed a cycle, and under
``runpy`` (``python -m codegen.emit``) that cycle resolved into TWO module objects
rather than into an ``ImportError``.  ``codegen.emit`` was bound once as ``__main__``
and once under its own name, and a class held by identity across that boundary is two
classes.

``codegen/__main__.py`` is the structural fix and it retires that rule.  ``python -m
codegen`` executes a file no module of the compiler imports, so ``codegen.emit`` is
imported once by name on every path, and a caller reaching the per-node decision by
name reaches the ONE decider.  The rule it replaced was never about design -- it was a
workaround for the double binding, and its price was callables carried on
:class:`codegen.compiler.Module` so that the walk could reach ``emit`` without naming
it.  Those are gone with it.

What remains are the two boundaries the architecture decides on their own merits:

* **§8 -- no Pydantic in the walk.**  The seam with ``datamodel-code-generator``'s
  model layer is one-way: the walk DECIDES and the renderer WRITES.  A node's
  decision expressed as a ``DataType``, a ``Field`` or an ``Annotated`` is a decision
  made in the renderer's vocabulary, which is how a rendering detail comes to decide a
  type.  So :data:`MODEL_LAYER` is importable by the renderer, and by the verifier
  (which reads emitted classes and is the other side of the boundary), and by nothing
  else.
* **§9 -- no walk in the verifier.**  One body of code deciding what the model states
  and what the document states agrees with itself by construction, so a defect in it
  is green on BOTH sides.  The verifier therefore reads the document of record and the
  emitted package, and never the walk that produced them.

Resolved by AST and not by grep, for three reasons a text search gets wrong:

* ``from codegen import compiler, emit`` is one statement naming two modules, and a
  line-oriented search reports the line rather than the names.
* ``from . import emit`` and ``from .. import emit`` name the same module without the
  string ``codegen`` appearing anywhere, so a grep for ``codegen.emit`` misses them
  entirely.  :func:`_resolved` walks the relative level the way Python does.
* a lazy ``import codegen.emit`` inside a function body is a dodge indistinguishable
  from a comment to a grep.

So the walk visits every ``Import`` and ``ImportFrom`` node at any depth, including
one inside a function, a ``try`` or an ``if TYPE_CHECKING`` block -- a
``TYPE_CHECKING`` import is still a violation, because it hides the dependency from
the type checker without removing it.

Perturbed, and each half separately: ``import pydantic`` in
``codegen/lower/containers.py`` reddens
:func:`test_the_walk_does_not_import_the_model_layer` and names that module; ``from
codegen import emit`` in ``codegen/harness.py`` reddens
:func:`test_the_verifier_does_not_import_the_walk` and names that import.  A rule
nothing can break is a finding about the rule.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "codegen"

#: Every PACKAGE under ``codegen``, dotted, derived from the tree rather than written
#: out: it decides which ``from X import y`` statements can reach a MODULE through
#: ``y``, and a subpackage added later must not quietly stop being resolved.
PACKAGES = frozenset(
    {"codegen"}
    | {
        ".".join(("codegen", *d.relative_to(PKG).parts))
        for d in PKG.rglob("*")
        if d.is_dir() and (d / "__init__.py").exists()
    }
)

#: §8's banned names.  Three spellings of the model layer: ``pydantic`` is the
#: runtime, ``pydantic_core`` its validator, and ``datamodel_code_generator`` the code
#: generator whose MODEL layer this package drives.  A dotted submodule of any of them
#: is the same import and is matched by prefix.
MODEL_LAYER = frozenset({"pydantic", "pydantic_core", "datamodel_code_generator"})

#: The RENDERER, by path under ``codegen/``: the one module on the walk's side of the
#: package that may name the model layer (§8).  ``compiler.py`` is today's spelling of
#: it -- §11 splits it into ``ir.py`` and ``render.py``, and the ban then applies to
#: ``ir.py`` too.
RENDERER = frozenset({"compiler.py"})

#: The VERIFIER, by path under ``codegen/``.  It grades an emitted class, so it reads
#: the emitted package and therefore pydantic: §8 exempts ``verify/`` by name, and
#: these two files are today's spelling of it.  ``harness.py`` runs the three checks
#: and ``dump_exemptions.py`` holds what the dump check strikes.
VERIFIER = frozenset({"harness.py", "dump_exemptions.py"})

#: §9's permitted import set for the verifier, under ``codegen``.  ``codegen.keywords``
#: is the DECLARATION -- §9 names it first, "for the compared set", and §9's own reason
#: says why it is not a hole: "sharing DATA is a different matter from sharing a
#: READING: the keyword table is the declared semantics, and both halves must read the
#: same declaration or the grade means nothing."  ``codegen.bundle`` is the document of
#: record and the document set; ``codegen.refusal`` is how a refusal the run recorded is
#: read; ``codegen.dump_exemptions`` is the verifier's own other half.
#:
#: ``codegen.compiler`` is the one entry §9 does NOT permit, and it is written here
#: because ``harness.py`` takes ``compiler.escape_key`` -- a JSON Pointer segment
#: speller, which §11 puts in the source layer and not in the walk.  A hand-written
#: entry names itself and can be audited, where a rule wide enough to admit it would
#: admit the walk as well: this set may SHRINK and may not grow, and §14 step 4
#: retires this entry by moving the renderer out of ``compiler.py``.
VERIFIER_MAY_IMPORT = frozenset(
    {
        "codegen.keywords",
        "codegen.bundle",
        "codegen.refusal",
        "codegen.dump_exemptions",
        "codegen.compiler",
    }
)


def _modules() -> list[Path]:
    """Every module of ``codegen/``, recursively, ``__init__`` included.

    ``__init__`` is not exempt: it is imported whenever any module of its package is,
    so an import there is the same dependency through a different file.
    """
    return sorted(p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts)


def _rel(path: Path) -> str:
    return str(path.relative_to(PKG))


def _package_of(path: Path) -> tuple[str, ...]:
    """The package a module lives in, for resolving a relative import.

    A probe outside the tree (:func:`test_the_rule_catches_each_spelling` writes one
    into ``tmp_path``) is read as a module directly under ``codegen/``, which is the
    position that makes ``from . import emit`` name ``codegen.emit``.
    """
    try:
        return ("codegen", *path.relative_to(PKG).parts[:-1])
    except ValueError:
        return ("codegen",)


def _resolved(node: ast.Import | ast.ImportFrom, package: tuple[str, ...]) -> list[str]:
    """Every MODULE one import statement names.

    ``import a.b`` names ``a.b``.  ``from a.b import c`` names ``a.b``, and names
    ``a.b.c`` too when ``a.b`` is one of :data:`PACKAGES`, where ``c`` could be a
    submodule -- ``from codegen import emit`` and ``from codegen.lower
    import union`` are the two spellings that reach a module without naming it in the
    ``module`` slot.  A relative ``from . import x`` / ``from ..y import z`` resolves
    against ``package`` by dropping ``level - 1`` trailing parts, which is what
    ``importlib`` does: level 1 is the module's own package.
    """
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    base = list(package[: len(package) - (node.level - 1)]) if node.level else []
    if node.module:
        base += node.module.split(".")
    stem = ".".join(base)
    if stem in PACKAGES:
        return [stem, *(f"{stem}.{a.name}" for a in node.names)]
    return [stem]


def _imports(path: Path) -> list[ast.Import | ast.ImportFrom]:
    tree = ast.parse(path.read_text())
    return [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def _named(path: Path) -> list[str]:
    """Every module name the file at ``path`` imports, at any depth."""
    package = _package_of(path)
    return sorted({name for node in _imports(path) for name in _resolved(node, package)})


def _model_layer_violations(path: Path) -> list[str]:
    return [
        name
        for name in _named(path)
        if name in MODEL_LAYER or any(name.startswith(m + ".") for m in MODEL_LAYER)
    ]


def _walk_violations(path: Path) -> list[str]:
    out = []
    for node in _imports(path):
        if isinstance(node, ast.Import) and any(a.name == "codegen" for a in node.names):
            # A bare ``import codegen`` binds the package and reaches every submodule
            # already imported elsewhere in the process, so it is a violation on its
            # own.  ``from codegen import bundle`` is not: it names ONE submodule, and
            # the bare stem :func:`_resolved` also returns for it is skipped below.
            out.append("codegen")
    for name in _named(path):
        if not name.startswith("codegen."):
            continue
        if name in VERIFIER_MAY_IMPORT:
            continue
        out.append(name)
    return sorted(set(out))


def test_the_package_has_modules_to_grade() -> None:
    """The denominator.  A rule measured over an empty set is green and says
    nothing, and the lowering rule this file replaced was once measured over a
    package holding only a docstring."""
    assert len(_modules()) > 5, _modules()


def test_each_rule_has_a_population_and_the_file_sets_are_real() -> None:
    """And each half of the package is non-empty under its own rule.

    :data:`RENDERER` and :data:`VERIFIER` are written by name, so a module renamed
    out from under this file would silently move into the graded set or out of it --
    which, for ``VERIFIER``, would leave §9 green over nothing.  Both are checked
    against the tree.
    """
    present = {_rel(p) for p in _modules()}
    assert RENDERER <= present, RENDERER - present
    assert VERIFIER <= present, VERIFIER - present
    assert _walk_population(), "§8 is graded over no module"
    assert _verifier_population(), "§9 is graded over no module"


def _walk_population() -> list[Path]:
    """Every module §8 bans the model layer in: the package less the renderer and the
    verifier, which are the two sides of that boundary."""
    return [p for p in _modules() if _rel(p) not in RENDERER | VERIFIER]


def _verifier_population() -> list[Path]:
    return [p for p in _modules() if _rel(p) in VERIFIER]


@pytest.mark.parametrize("path", _walk_population(), ids=_rel)
def test_the_walk_does_not_import_the_model_layer(path: Path) -> None:
    """§8.  The walk decides; the renderer writes.

    ``Type("pydantic.AwareDatetime")`` is a Python symbol the semantics document
    names in its ``format`` row, and NAMING a symbol is not a Pydantic idiom -- it is
    a string in a decided type.  Constructing a ``Field``, a ``ConfigDict``, an
    ``Annotated`` or a ``DataType`` is, and only the renderer does it, which is why
    the rule is about the IMPORT and not about the string.
    """
    assert _model_layer_violations(path) == [], (
        f"{_rel(path)} imports {_model_layer_violations(path)}; §8 puts the model layer "
        f"behind {sorted(RENDERER)} and the verifier, and a node's decision expressed in "
        "the renderer's vocabulary is a rendering detail deciding a type"
    )


@pytest.mark.parametrize("path", _verifier_population(), ids=_rel)
def test_the_verifier_does_not_import_the_walk(path: Path) -> None:
    """§9.  The verifier grades the emitted class against the document of record and
    reads neither the walk that decided it nor the renderer that wrote it.

    One body of code answering both halves agrees with itself by construction, so a
    defect in it is green on both sides and the grade means nothing.
    """
    assert _walk_violations(path) == [], (
        f"{_rel(path)} imports {_walk_violations(path)} of this package; §9 permits "
        f"{sorted(VERIFIER_MAY_IMPORT)} and nothing else -- a verifier that reads the walk "
        "grades the walk against itself"
    )


def test_the_rule_catches_each_spelling(tmp_path: Path) -> None:
    """The instrument, on the spellings a grep gets wrong and on the non-violations.

    Without this, a resolver that resolved nothing would pass over a package whose
    modules are all clean, and the perturbations in the module docstring would be the
    only thing that ever exercised it.
    """
    walk_cases = {
        "import codegen.emit": ["codegen.emit"],
        "from codegen import emit": ["codegen.emit"],
        # A relative import resolves the way ``importlib`` does: level 1 is the
        # module's own package, so for a module directly under ``codegen/``
        # ``from . import emit`` names ``codegen.emit``.
        "from . import emit": ["codegen.emit"],
        "from codegen.lower import union": ["codegen.lower", "codegen.lower.union"],
        "from codegen.constraints import resolve": ["codegen.constraints"],
        "import codegen": ["codegen"],
        "def f():\n    from codegen import emit": ["codegen.emit"],
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from codegen import emit": [
            "codegen.emit"
        ],
        "from codegen import bundle\nfrom codegen.refusal import Refusal": [],
        "from codegen.compiler import escape_key\nimport jsonschema": [],
    }
    model_cases = {
        "import pydantic": ["pydantic"],
        "from pydantic import BaseModel": ["pydantic"],
        "import pydantic_core": ["pydantic_core"],
        "from datamodel_code_generator.model import DataModelFieldBase": [
            "datamodel_code_generator.model"
        ],
        "from adcp.types._base import SchemaRef\nimport json": [],
    }
    probe = tmp_path / "probe.py"
    for source, expected in walk_cases.items():
        probe.write_text(source + "\n")
        assert _walk_violations(probe) == expected, source
    for source, expected in model_cases.items():
        probe.write_text(source + "\n")
        assert _model_layer_violations(probe) == expected, source
