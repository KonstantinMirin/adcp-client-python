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
  type.  So :data:`MODEL_LAYER` is importable by ``codegen/render.py``, and by the
  verifier (which reads emitted classes and is the other side of the boundary), and by
  nothing else -- with ONE named exception, :data:`MODEL_LAYER_EXCEPTIONS`, which says
  what forces it and which row retires it.  :data:`SECTION_8_BANS` is the section's own
  list of paths, asserted to be inside the graded population so an exemption cannot
  quietly take one of them out of it.
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
#: package that may name the model layer (§8).  ``render.py`` is it, and it is the whole
#: of §8's exemption -- ``ir.py`` carries the declarations and is banned like the rest.
RENDERER = frozenset({"render.py"})

#: **§8's ban, by the paths the section names**, so the rule is graded where the document
#: puts it and not only wherever the exemptions happen to leave: "nothing in
#: ``schema/``, ``lower/``, ``ir.py``, ``keywords.py`` or ``bundle.py`` imports
#: ``pydantic``, ``pydantic_core`` or ``datamodel_code_generator``".  Asserted as a
#: SUBSET of the graded population (:func:`_walk_population`), which is wider -- the
#: whole package less the renderer and the verifier -- so the named paths cannot fall out
#: of the grade when a module is added or renamed.  ``schema/`` arrives with §14 step 5
#: and the prefix already resolves it.
SECTION_8_BANS = ("lower/", "schema/", "ir.py", "keywords.py", "bundle.py")

#: **EMPTY, and §14 step 7 is the row that emptied it.**  It held one entry:
#: ``compiler.field_name`` asked what pydantic's ``BaseModel`` carries, because a document
#: key that spells an attribute of it is no field at all -- measured on
#: ``core/truncation-sentinel.json``'s ``_truncation``, which was silently absent from the
#: model -- and the answer is a fact about pydantic rather than about the bundle.
#:
#: The entry said step 7 "has to answer it", by moving §4's name rules into
#: ``codegen/lower/names.py`` -- a path §8 DOES ban.  It is answered by moving the READING
#: the other way: ``render.RESERVED`` derives the set in the one module §8 allows to know
#: the model layer, the run hands it to the walk as data, and ``names.field_name`` takes
#: it as an argument.  So no module outside :data:`RENDERER` and :data:`VERIFIER` names
#: the model layer at all.  A hand-written entry names itself and can be audited; this
#: mapping may SHRINK and may not grow, and there is nothing left in it to shrink.
MODEL_LAYER_EXCEPTIONS: dict[str, str] = {}

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
#: **``codegen.compiler`` is GONE from this set, which is §14 step 5's own clearance.**
#: §14 step 4 moved the renderer out of ``compiler.py`` and the set did not shrink by it,
#: because the renderer was never what forced the entry: ``harness.py`` took
#: ``compiler.escape_key`` and ``compiler.node_at`` -- a JSON Pointer segment speller and
#: its inverse, which §11 puts in the SOURCE layer and not in the walk.
#:
#: Row .4 measured why the obvious move was WRONG then, as the ``codegen`` modules each
#: import pulls in: ``codegen.compiler`` reached 4 (``compiler``, ``ir``, ``keywords``,
#: ``refusal``) and ``codegen.bundle`` reached 8 -- those four plus ``bundle``,
#: ``lower``, ``lower.rules`` and ``lower.union``, because ``bundle`` imported two
#: LOWERINGS for its root selectors.  §9's reason is that the verifier must not read the
#: walk, so trading one named import for a transitive reach into ``codegen.lower`` would
#: have bought the ratchet a line and cost the section its point.
#:
#: §14 step 5 deletes those root selectors (``docs/plan/architecture.md`` §5: "there is
#: no second table of root selectors"), and the two that read a lowering -- ``union_root``
#: and ``states_an_object_rule`` -- are now ``tests/populations.py``'s.  So ``bundle.py``
#: imports no lowering, the pair moved there, and the verifier imports no module of the
#: walk at all.  :func:`test_the_verifier_reaches_no_module_of_the_walk_transitively` is
#: what holds the transitive half, so the move cannot be undone by an import added to
#: ``bundle.py`` later.
#:
#: A hand-written entry names itself and can be audited, where a rule wide enough to
#: admit it would admit the walk as well: this set may SHRINK and may not grow.
VERIFIER_MAY_IMPORT = frozenset(
    {
        "codegen.keywords",
        "codegen.bundle",
        "codegen.refusal",
        "codegen.dump_exemptions",
    }
)

#: The modules of the WALK, by dotted name: §9's own list, "Never ``codegen.schema``,
#: ``codegen.lower``, ``codegen.ir``, ``codegen.render``, ``codegen.emit``", plus
#: ``codegen.compiler`` and ``codegen.constraints``, which §12 says that module dissolves
#: into.  Read by the transitive test below, which is what makes
#: :data:`VERIFIER_MAY_IMPORT`'s shrink durable: a permitted module that IMPORTS one of
#: these puts the walk back in the verifier's reach through the back door, which is
#: exactly what the root selectors did.
THE_WALK = frozenset(
    {
        "codegen.schema",
        "codegen.lower",
        "codegen.ir",
        "codegen.render",
        "codegen.emit",
        "codegen.compiler",
        "codegen.constraints",
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


def _module_name(path: Path) -> str:
    """The dotted name of one module of ``codegen/``.

    ``codegen/lower/union.py`` is ``codegen.lower.union`` and ``codegen/lower/__init__.py``
    is ``codegen.lower``, which is the name an importer of the PACKAGE binds -- so the
    transitive closure below follows a package's own ``__init__`` imports as edges of the
    package, which is what they are.
    """
    parts = path.relative_to(PKG).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(("codegen", *parts))


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
    assert set(MODEL_LAYER_EXCEPTIONS) <= present, set(MODEL_LAYER_EXCEPTIONS) - present
    assert _walk_population(), "§8 is graded over no module"
    assert _verifier_population(), "§9 is graded over no module"


def test_section_8_bans_the_model_layer_where_the_section_names_it() -> None:
    """§8's named paths are inside the graded population, and the exemptions are not.

    The graded population is derived -- the package less the renderer and the verifier --
    so a module added under ``lower/`` is banned without anyone listing it.  What a
    derivation cannot say is that the SECTION's own list is covered: an exemption added
    by file name could quietly take ``ir.py`` or ``bundle.py`` out of the grade, and the
    rule would stay green over a smaller set.  So the list is asserted against the
    population rather than used as it.

    ``schema/`` has no module yet (§14 step 5 writes it) and the prefix is listed anyway:
    a path with no file contributes nothing here, and the day it has one it is graded
    without this file changing.
    """
    graded = {_rel(p) for p in _walk_population()}
    named = {rel for rel in graded if rel.startswith(SECTION_8_BANS) or rel in SECTION_8_BANS}
    assert named, graded
    for path in SECTION_8_BANS:
        if path.endswith("/"):
            continue
        assert path in graded, (
            f"§8 bans the model layer in {path} and it is not in the graded population; "
            f"an exemption has taken it out"
        )
    assert not (named & (RENDERER | VERIFIER | set(MODEL_LAYER_EXCEPTIONS))), (
        "a path §8 bans by name is also exempted"
    )


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
    found = _model_layer_violations(path)
    excuse = MODEL_LAYER_EXCEPTIONS.get(_rel(path))
    if excuse is not None:
        # A named exception, graded in the other direction: it must still be VIOLATING,
        # or it is an entry nothing forces and the set has to shrink.
        assert found, (
            f"{_rel(path)} is excused from §8 for {excuse!r} and imports nothing of the "
            "model layer; MODEL_LAYER_EXCEPTIONS may only shrink, so drop the entry"
        )
        return
    assert found == [], (
        f"{_rel(path)} imports {found}; §8 puts the model layer "
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


def test_the_verifier_reaches_no_module_of_the_walk_transitively() -> None:
    """§9's reason, read through the import graph rather than through one statement.

    "The verifier grades an emitted class against the document it names, and it does so
    without reading the walk."  A test over the verifier's OWN import statements holds
    the letter of that: it is why :data:`VERIFIER_MAY_IMPORT` is a hand-written set.  It
    does not hold the reason, and row .4 measured exactly how -- ``codegen.bundle`` is
    permitted and used to import ``codegen.lower.rules`` and ``codegen.lower.union`` for
    its root selectors, so ``import codegen.bundle`` reached eight ``codegen`` modules
    and the walk was in the verifier's reach through the back door.

    §14 step 5 deletes the selectors and the pointer speller the verifier needed moves
    into ``bundle.py``, so ``codegen.compiler`` left the permitted set.  **This is what
    keeps it out**: a module the verifier may import must not reach a module of the walk,
    whatever a later row adds to it.  Closed transitively over the package's own import
    statements, so an edge added two modules away reddens here and not in a review.
    """
    graph = {_module_name(path): set(_named(path)) for path in _modules()}
    reached: dict[str, set[str]] = {}
    for start in sorted(VERIFIER_MAY_IMPORT):
        seen: set[str] = set()
        queue = [start]
        while queue:
            name = queue.pop()
            for edge in graph.get(name, ()):  # a module with no entry is not ours
                if edge in seen or not edge.startswith("codegen"):
                    continue
                seen.add(edge)
                queue.append(edge)
        reached[start] = seen
    walked = {
        start: sorted(seen & THE_WALK) for start, seen in reached.items() if seen & THE_WALK
    }
    assert walked == {}, (
        f"a module §9 permits the verifier reaches the walk: {walked}; §9's reason is "
        "that one body of code answering both halves agrees with itself by construction, "
        "and a transitive edge makes that true without any import statement saying so"
    )
    # The control: the closure is NON-EMPTY, so the assertion above is not satisfied by a
    # resolver that resolved nothing.  ``codegen.bundle`` reaches ``codegen.keywords`` and
    # ``codegen.refusal``, which is two of the eight it reached before this row.
    assert reached["codegen.bundle"], reached


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
        "from codegen.bundle import escape_key\nimport jsonschema": [],
        "from codegen import ir, render": ["codegen.ir", "codegen.render"],
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


# --------------------------------------------------------------------------- #
# §7: the IR is COMPLETE, so nothing before render.py holds a string of Python
# --------------------------------------------------------------------------- #
#: The statement kinds a string of PYTHON is.  A string that parses as a bare
#: expression is prose as far as this rule is concerned -- every docstring and every
#: refusal detail in the package is one -- so the test asks for a STATEMENT: an
#: assignment, an annotated assignment, a ``def``, a ``class``, an import, a ``return``.
#: Those are what the walk used to format: class-body lines
#: (``_adcp_rules: ClassVar[...] = (...)``, ``_branch_models: ClassVar[...] = ()``), an
#: alias statement (``X = Annotated[...]``), a module trailer
#: (``X._branch_models = (...)``) and a root binding
#: (``strict_validate = strict_alias(...)``).
PYTHON_STATEMENTS = (
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Import,
    ast.ImportFrom,
    ast.Return,
    ast.For,
    ast.While,
    ast.If,
    ast.With,
    ast.Raise,
    ast.Assert,
)


def _string_literals(tree: ast.AST) -> list[tuple[int, str]]:
    """Every string a module holds, f-strings included, with the line it sits on.

    An f-string is read as its TEMPLATE, with each interpolation replaced by an
    identifier: an f-string spelling ``_adcp_rules: ClassVar[...] = (`` plus an
    interpolated body is a Python statement whatever the body holds, and a rule that
    only looked at plain strings would miss every one of the four texts §7 names,
    because all four were f-strings.
    """
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.lineno, node.value))
        elif isinstance(node, ast.JoinedStr):
            out.append(
                (
                    node.lineno,
                    "".join(
                        part.value
                        if isinstance(part, ast.Constant) and isinstance(part.value, str)
                        else "_interpolated"
                        for part in node.values
                    ),
                )
            )
    return out


def _python_text(path: Path) -> list[str]:
    """Every string in ``path`` that parses as a Python STATEMENT."""
    found = []
    for lineno, text in _string_literals(ast.parse(path.read_text())):
        try:
            parsed = ast.parse(text)
        except (SyntaxError, ValueError):
            continue
        if any(isinstance(statement, PYTHON_STATEMENTS) for statement in parsed.body):
            found.append(f"line {lineno}: {text.splitlines()[0][:90]!r}")
    return found


@pytest.mark.parametrize("path", _walk_population(), ids=_rel)
def test_nothing_before_the_renderer_holds_a_string_of_python(path: Path) -> None:
    """§7.  "There is an IR between a decided node and emitted text, and it is complete:
    nothing before ``render.py`` holds a string of Python."

    That is the section's own word -- COMPLETE -- and it is a test rather than a style
    note, because the four texts it replaced were each produced by a different module and
    each for a defensible local reason: ``lower/rules.py`` formatted the ``_adcp_rules``
    line, ``compiler`` appended it to a class's ``body_lines`` and wrote a root's two
    binding statements, ``lower/union.py`` wrote the base's four attributes and the
    module trailer, and ``constraints.py`` wrote the alias module's own statements.  A
    declaration carrying one is a layer boundary that exists in the docstrings and not in
    the code.

    Graded over the same population as §8 and in the same file, because the two rules are
    one judgement from two sides: the walk DECIDES and the renderer WRITES.  §8 is about
    the import and this is about the output, and a module can satisfy either alone -- a
    hand-rolled text emitter imports no pydantic at all, and that is the arrangement that
    dropped three of three schema defaults and all 142 property descriptions.

    Asked of STATEMENTS and not of strings, so a docstring, a refusal detail and a
    pointer stay what they are; :data:`PYTHON_STATEMENTS` says which kinds and why.
    """
    found = _python_text(path)
    assert found == [], (
        f"{_rel(path)} holds {found}; §7 says the IR is complete -- a declaration "
        "carries the decision and codegen/render.py writes every string"
    )


def test_the_python_text_rule_catches_the_four_texts_it_replaced(tmp_path: Path) -> None:
    """The instrument, on the four texts §7 names and on the strings that stay prose.

    Without this a reader cannot tell the rule from one that resolves nothing, and the
    package is clean -- so the only exercise the rule would otherwise get is a future
    violation.  The f-string cases are the ones that matter: all four texts §7 replaced
    interpolated a decided value, so a rule reading plain strings alone would be green
    over every one of them.
    """
    caught = (
        'x = "_adcp_rules: ClassVar[tuple[Rule, ...]] = (\\n    )"',
        'x = f"_adcp_rules: ClassVar[tuple[Rule, ...]] = (\\n{body}    )"',
        'x = f\'_BRANCH_DISCRIMINATOR: ClassVar[str] = "{on}"\'',
        'x = f"{symbol} = {annotation}"',
        'x = f"{symbol}._branch_models = ({names},)"',
        'x = f\'strict_validate = strict_alias(__adcp_schema__, "{s}", {s})\'',
        "x = 'def _branch_combinator(cls) -> str:\\n    return 0'",
    )
    prose = (
        '"""A docstring, which parses as an expression and is not a statement."""',
        'x = "a sibling of $ref, which draft-07 ignores"',
        'x = f"{pointer}/properties/{key}"',
        'x = f"two nodes in this document derive the class name {name!r}"',
        # The one shape that reads like code and is not: a keyword's ``compiles``
        # sentence quoting the semantics document inside prose.
        'x = "generically, as `type NonEmptyList[T] = Annotated[list[T], Field(...)]`"',
    )
    probe = tmp_path / "probe.py"
    for source in caught:
        probe.write_text(source + "\n")
        assert _python_text(probe), source
    for source in prose:
        probe.write_text(source + "\n")
        assert _python_text(probe) == [], source


# --------------------------------------------------------------------------- #
# §4's one reading, and §14 step 5's carrier, held by name
# --------------------------------------------------------------------------- #
#: Where a raw mapping may be read, and what forces each one.  ``docs/plan/architecture.md``
#: §4: "``codegen/schema/parse.py`` is the one function that reads a raw mapping", and §6:
#: "the parser walks the raw document once and builds the whole tree; after it, no layer
#: walks a mapping."  Two readers stay at the DECLARATION level and the design decides
#: both by name, so neither is an exemption:
#:
#: * ``codegen/lower/rules.py`` -- §4 keeps a node at RULE as a rule SOURCE on the
#:   enclosing node (``nodes.Base.rules``) and names this module its only reader;
#: * ``codegen/lower/union.py`` -- §4 "Names"'s three branch rules and §4's dispatch
#:   derivation are readings of a branch's own DECLARATION (its title, its ``const`` pin,
#:   its ``required`` set), which ``nodes.Union.branch_raw`` is the carrier for;
#: * ``codegen/compiler.py`` -- §6 keeps ``restatement``, ``intersection`` and
#:   ``at_least_as_tight`` as pure functions over DECLARATIONS, because §2's intersection
#:   rule merges two declarations of one property and hands the merged one back to
#:   ``parse``.  ``nodes.Conjunct.raw``, ``nodes.Base.declared`` and
#:   ``nodes.Union.branch_raw`` are the three typed carriers that reading is given.
#: ``codegen/emit.py`` is NOT in this set and §14 step 7 is what removed it.  It held
#: ``_composed_nodes``, the pointers a document's root ``allOf`` NAMES -- a fact about the
#: bundle's reference GRAPH, which §11 puts in the source layer.  It is ``bundle.composed``
#: now, a projection of ``bundle.edges``'s one scan, which is also the merge of two passes
#: over the bundle that function's own docstring named as its upgrade path.  This set may
#: SHRINK and may not grow.
MAY_READ_A_DECLARATION = frozenset(
    {
        "schema/parse.py",
        "lower/rules.py",
        "lower/union.py",
        "compiler.py",
    }
)

#: The field name §14 step 5 allowed on a node DURING the conversion and deleted at the
#: end of it: "during this step a node may carry its originating mapping ... **the step is
#: not complete until that carrier is deleted**, and its deletion is the step's last
#: commit: a tree that still has it has not finished step 5, and no later step may read
#: it."
CARRIER = "raw"


def test_no_node_carries_the_mapping_it_was_parsed_from() -> None:
    """§14 step 5's exit condition, asserted on the kinds rather than reviewed.

    The carrier was ``nodes.Base.raw`` and the step's own sentence is that no later step
    may read it.  A field is the only way one could: a handler holding a node cannot
    reach the document otherwise, because ``parse`` is handed the mapping and returns
    nodes.  So the assertion is that no kind of §4's table declares one -- which also
    reddens if a later row reintroduces it under the same name to get a reading done
    quickly.

    ``nodes.Conjunct`` is the ONE declaration in this module that does carry ``raw``, and
    it is not a node: §2's intersection rule merges two DECLARATIONS of one property and
    hands the merged one back to ``parse``, so a conjunct is read as a declaration and
    the node it becomes is the composed node.  It is asserted PRESENT, so the clause
    above cannot be satisfied by deleting the sanctioned carrier too.
    """
    from dataclasses import fields as dataclass_fields

    from codegen.schema import nodes

    kinds = [
        value
        for value in vars(nodes).values()
        if isinstance(value, type) and issubclass(value, nodes.Base)
    ]
    # §4's table, BY NAME and not by count: the kinds are closed (draft-07 fixes them and
    # the table lists every one), so the population this clause ranges over is a
    # declaration rather than a census of today's module.
    assert {k.__name__ for k in kinds} == {
        "Base",
        "Reference",
        "Enumeration",
        "Constant",
        "Composition",
        "Union",
        "Object",
        "Mapping_",
        "Array",
        "Scalar",
        "MultiType",
        "Null",
        "Typeless",
    }, sorted(k.__name__ for k in kinds)
    carrying = {
        kind.__name__
        for kind in kinds
        if CARRIER in {f.name for f in dataclass_fields(kind)}
    }
    assert carrying == set(), (
        f"{sorted(carrying)} carry {CARRIER!r}: §14 step 5's migration carrier is deleted "
        "and no later step may read it -- a handler reads node fields, and a declaration "
        "a reading genuinely needs gets a carrier nodes.py names (Conjunct.raw, "
        "Base.rules, Base.declared, Union.branch_raw)"
    )
    assert CARRIER in {f.name for f in dataclass_fields(nodes.Conjunct)}, (
        "nodes.Conjunct is a DECLARATION and not a node, and §2's intersection rule is "
        "why it carries one; the clause above must not be green because this went too"
    )


def test_the_parser_is_the_only_entry_that_reads_a_raw_mapping() -> None:
    """§4's "one function that reads a raw mapping", read through the call graph.

    Asserted as the set of MODULES that call ``codegen.schema.parse.parse``, because the
    entry is what a second traversal would have to come through: every other module takes
    a node and reads its fields.  Three callers and each is a position ``parse`` is
    re-entered at rather than a second walk of one mapping:

    * ``codegen/emit.py`` -- the document ROOT, once per document (``lower_document``);
    * ``codegen/compiler.py`` -- a ``definitions`` entry at DEF, parsed on demand when a
      ``$ref`` names it (§5: "an entry nothing references is not declared"), and the
      MERGED declaration §2's intersection rule hands back (``_parsed_property``).

    Named BY SITE and not by count: the set is ``{module, enclosing function}``, so a
    fourth entry has to be added here with the sentence that re-enters the parser for it.

    Resolved by AST, for the module docstring's reasons: a lazy import inside a function
    body and a relative ``from ..schema import parse`` are both invisible to a grep.
    """
    sites: set[tuple[str, str]] = set()
    for path in _modules():
        rel = _rel(path)
        if rel.startswith("schema/"):
            continue  # the parser's own recursion is the one traversal
        tree = ast.parse(path.read_text())
        for holder in ast.walk(tree):
            if not isinstance(holder, ast.FunctionDef):
                continue
            for node in ast.walk(holder):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "parse"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in {"schema", "parse", "schema_parse", "nodes_parse"}
                ):
                    sites.add((rel, holder.name))
    assert sites == {
        # the document ROOT, once per document (§5's one path)
        ("emit.py", "lower_document"),
        # a ``definitions`` entry at DEF, parsed when a ``$ref`` names it (§5)
        ("compiler.py", "decide"),
        # the MERGED declaration §2's intersection rule hands back (§6)
        ("compiler.py", "_parsed_property"),
    }, sorted(sites)


#: The identifiers a RAW MAPPING is read through in this package, so the guard below can
#: tell one from a node's own field: ``node.annotations[...]`` is a field and
#: ``conjunct.get(...)`` is a declaration.  A name and not a type, because the type is what
#: a static check cannot have -- and that is the point: the rule is about WHICH MODULE may
#: hold a mapping at all, not about which line reads it.
A_MAPPING = frozenset({"doc", "declaration", "conjunct", "branch", "sub", "raw", "node", "child"})

#: The decision layer, which is where §4's rule bites.  ``bundle.py`` owns every file read
#: and every fact derived from a document (§4), and ``harness.py`` reads the document of
#: record because that is what a verifier does (§9), so neither is in scope here.
DECIDES = ("compiler.py", "emit.py", "lower/", "schema/")


def _declaration_reads(path: Path) -> set[str]:
    """Every subscript or ``.get`` this module performs on a raw mapping."""
    tree = ast.parse(path.read_text())
    out: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in A_MAPPING
        ):
            out.add(f"{node.func.value.id}.get")
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in A_MAPPING
        ):
            out.add(f"{node.value.id}[...]")
    return out


@pytest.mark.parametrize(
    "path",
    [p for p in _modules() if _rel(p).startswith(DECIDES)],
    ids=_rel,
)
def test_only_the_named_modules_read_a_declaration(path: Path) -> None:
    """The other half of §4's rule: which modules of the DECISION layer may hold a mapping.

    Whether one line reads a declaration or a node's own mapping-valued field is not
    decidable from the syntax -- ``annotations``, ``rules`` and ``declared`` are mappings
    and are read with a subscript like anything else.  What IS decidable is which modules
    do it at all, and :data:`MAY_READ_A_DECLARATION` is that set with the sentence forcing
    each entry.  So this is a RATCHET on the set: a module outside it that acquires one
    has to be added here, in front of a reader, with the sentence that permits it.

    ``lower/union.py`` is the entry §14 step 5 removed, and it is the measurement that
    makes this check non-vacuous: the row found it reading a branch list, a root's
    ``type``, a root's four conjunct-ish siblings and a mapping per branch off the
    document, and all four are fields now (``nodes.Union``).  What it reads is
    ``branch_raw``, a carrier ``nodes.py`` names -- so it is still in the set below, for
    §4 "Names"'s declaration-level reading and for nothing else.

    ``emit.py`` left the set in the same commit: it read the document's ``title`` to
    derive the module symbol before the parse, and ``nodes.Base.title`` is that reading
    now.
    """
    reads = _declaration_reads(path)
    assert not reads or _rel(path) in MAY_READ_A_DECLARATION, (
        f"{_rel(path)} reads {sorted(reads)} off a raw mapping; §4 makes "
        "codegen/schema/parse.py the one function that reads one, and the "
        f"declaration-level readers the design names are "
        f"{sorted(MAY_READ_A_DECLARATION - {'schema/parse.py'})}"
    )


def test_the_declaration_rule_is_not_vacuous() -> None:
    """The control: the modules the rule PERMITS really do read a mapping.

    A guard whose detector finds nothing is green for free, which is the defect this
    file's own module docstring names about a grep.  So each permitted entry is asserted
    to have at least one read -- the parser's own ``raw``, the rule lowering's rule
    sources, and the intersection rule's conjuncts -- and the decision layer's other
    modules are asserted to have none, which is the state §14 step 5 leaves.
    """
    found = {
        _rel(p): _declaration_reads(p)
        for p in _modules()
        if _rel(p).startswith(DECIDES) and _declaration_reads(p)
    }
    assert set(found) == set(MAY_READ_A_DECLARATION), sorted(found)
    for rel in sorted(MAY_READ_A_DECLARATION):
        assert found[rel], rel


# --------------------------------------------------------------------------- #
# section 2's refusal rule: a refusal is a VALUE, and one exception stays an exception
# --------------------------------------------------------------------------- #
#: The one exception class the compiler still raises, and the module it lives in.
#: ``docs/plan/architecture.md`` section 2: "a defect in the compiler itself -- two
#: selectors claiming one node, two constraints deriving one alias name -- stays an
#: exception (``BuildFailure``) that no layer catches, because it is not an outcome of any
#: document and the run must stop on it."
BUILD_FAILURE = "BuildFailure"

#: The exceptions a module of ``codegen/`` may still raise, by class name, each with what
#: makes it NOT an outcome of a document.  A refusal is a property of a DOCUMENT and is
#: returned; everything here is a property of the COMPILER, of its CALLER, or of the
#: filesystem, and stops the run.  This set may SHRINK and may not grow.
#:
#: * ``BuildFailure`` and ``AliasCollision`` -- section 2's own two, the second a subclass
#:   of the first.
#: * ``TypeError`` -- ``Refusal.__init__`` on a kind/``through=`` mismatch, and
#:   ``render.declaration`` on a declaration kind it has no rendering for.  Both are a
#:   caller of this compiler getting the call wrong, which no document can cause.
#: * ``ValueError`` -- ``refusal.is_a_verdict`` handed a delegating kind (the caller read
#:   ``kind`` where it meant ``resolved``) and ``bundle.read`` handed a document whose root
#:   is not an object, which is the FILE and not a node the walk reached.
MAY_RAISE = frozenset({BUILD_FAILURE, "AliasCollision", "TypeError", "ValueError"})

#: The population the :data:`MAY_RAISE` clause ranges over: every module of ``codegen/``
#: that is NOT the verifier.  Section 9 keeps the verifier separate from the walk and it
#: has an exception of its own -- ``harness._DumpRefused``, raised inside the accepts
#: check's hypothesis body and caught BY NAME one frame out so the verdict is
#: ``model_dropped_a_fact`` rather than the generic ``model_error`` -- which is a
#: GRADING verdict about one drawn instance and not a refusal of any document.  The
#: ``Refusal`` clauses below range over the whole package, because "nothing raises one
#: and nothing catches one" holds of the verifier too.



def test_a_refusal_is_a_value_and_no_module_raises_or_catches_one() -> None:
    """Section 2's refusal rule, and section 14 step 6's exit condition, by AST.

    "``decide(node, ctx)`` returns ``Lowering | Refusal``.  Every handler has that
    signature.  A refusal is a VALUE a parent returns upward unchanged; **nothing raises
    one and nothing catches one**."  Three clauses, each asserted on the tree rather than
    reviewed:

    * :class:`codegen.refusal.Refusal` is not a subclass of ``Exception``, so ``raise
      Refusal(...)`` is a ``TypeError`` at the raise site and the rule cannot be broken
      by forgetting it.  That is the clause that makes the other two unnecessary in
      principle and worth asserting anyway: a later row that gave the class a base to get
      one raise done quickly would turn the two below green again.
    * no ``raise`` names ``Refusal``, and no module raises any class outside
      :data:`MAY_RAISE` -- so a NEW exception standing in for a refusal is caught here
      too, which a search for the one class name would miss.
    * no ``except`` names ``Refusal``, which is the half section 2 states twice: the
      ``try``/``except Refusal`` in ``compiler.Module.resolve_node`` and the two in
      ``emit.emit`` are what it retires, and "the one ``try`` left in the compiler is
      around nothing".

    AST and not grep, for this file's own reason: ``raise Refusal(...)`` inside a string or
    a docstring is prose, and both documents and several of these modules quote the rule.
    """
    from codegen import refusal as refusal_module

    assert not issubclass(refusal_module.Refusal, Exception), (
        "Refusal subclasses Exception, so it can be raised: §14 step 6 is 'Refusal stops "
        "subclassing Exception', and §2's 'nothing raises one' is held by the type and "
        "not by a convention"
    )
    assert issubclass(refusal_module.BuildFailure, Exception), (
        "BuildFailure is §2's one exception and has to BE one, or the clause above is "
        "green because the compiler has nothing left that stops a run"
    )

    raised: dict[str, set[str]] = {}
    caught: dict[str, set[str]] = {}
    for path in _modules():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and node.exc is not None:
                call = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                name = call.attr if isinstance(call, ast.Attribute) else getattr(call, "id", "")
                if name:
                    raised.setdefault(_rel(path), set()).add(name)
            if isinstance(node, ast.ExceptHandler) and node.type is not None:
                for named in ast.walk(node.type):
                    if isinstance(named, ast.Name):
                        caught.setdefault(_rel(path), set()).add(named.id)
                    elif isinstance(named, ast.Attribute):
                        caught.setdefault(_rel(path), set()).add(named.attr)

    refusing = {rel: names for rel, names in raised.items() if "Refusal" in names}
    assert refusing == {}, (
        f"{sorted(refusing)} raise a Refusal; §2 makes it a value a handler RETURNS and "
        "a parent returns upward unchanged"
    )
    unexpected = {
        rel: sorted(names - MAY_RAISE)
        for rel, names in raised.items()
        if rel not in VERIFIER and names - MAY_RAISE
    }
    assert unexpected == {}, (
        f"{unexpected} raise an exception the design does not name.  A refusal is a "
        f"property of a DOCUMENT and is returned; the classes a module may raise are "
        f"{sorted(MAY_RAISE)}, each a property of the COMPILER or of its caller, and that "
        "set may shrink and may not grow"
    )
    catching = {rel: sorted(names) for rel, names in caught.items() if "Refusal" in names}
    assert catching == {}, (
        f"{sorted(catching)} catch a Refusal; §2: 'nothing raises one and nothing catches "
        "one', and the one try left in this compiler is around nothing"
    )


def test_the_refusal_rule_is_not_vacuous(tmp_path: Path) -> None:
    """The control: the detector finds each spelling it is meant to.

    A structural guard whose detector sees nothing is green for free.  So a probe module
    is written with the three shapes the clauses above forbid -- a bare ``raise``, an
    attribute-spelled one, and an ``except`` naming the class through its module -- and
    each is asserted found.  ``codegen/`` is also asserted to still raise SOMETHING, so
    the ``MAY_RAISE`` clause cannot be green because every raise was deleted.
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        "from codegen.refusal import Refusal\n"
        "import codegen.refusal as r\n"
        "def a():\n"
        "    raise Refusal('x', '/', 'd', kind=None)\n"
        "def b():\n"
        "    raise r.Refusal('x', '/', 'd', kind=None)\n"
        "def c():\n"
        "    try:\n"
        "        a()\n"
        "    except r.Refusal:\n"
        "        pass\n"
    )
    tree = ast.parse(probe.read_text())
    raised = {
        (node.exc.func.attr if isinstance(node.exc.func, ast.Attribute) else node.exc.func.id)
        for node in ast.walk(tree)
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
    }
    caught = {
        named.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is not None
        for named in ast.walk(node.type)
        if isinstance(named, ast.Attribute)
    }
    assert raised == {"Refusal"}, sorted(raised)
    assert caught == {"Refusal"}, sorted(caught)

    live = {
        node.exc.func.id
        for path in _modules()
        if _rel(path) not in VERIFIER
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
    }
    assert live, "codegen/ raises nothing at all, so the MAY_RAISE clause says nothing"
    assert BUILD_FAILURE in live, (
        f"no module raises {BUILD_FAILURE}: §2's one exception has to be reached by "
        "something, or the division between a document's property and the compiler's is "
        "a claim with no site"
    )
