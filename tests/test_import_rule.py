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

#: The ONE module outside :data:`RENDERER` that still names the model layer, with what
#: forces it.  ``compiler.field_name`` asks what pydantic's ``BaseModel`` carries, because
#: a document key that spells an attribute of it is no field at all -- measured on
#: ``core/truncation-sentinel.json``'s ``_truncation``, which was silently absent from the
#: model -- and the answer is a fact about pydantic, not about the bundle.
#:
#: §8's own ban list does not name ``compiler.py``: the section bans the model layer in
#: ``schema/``, ``lower/``, ``ir.py``, ``keywords.py`` and ``bundle.py``, which is where
#: §14 steps 5 and 7 distribute this module's contents.  **Step 7 is the row that retires
#: this entry**, by moving D3's name rules into ``codegen/lower/names.py`` -- a path §8
#: DOES ban -- so the reading has to become data the naming pass reads rather than an
#: import the walk makes.  A hand-written entry names itself and can be audited; this
#: mapping may SHRINK and may not grow.
MODEL_LAYER_EXCEPTIONS = {
    "compiler.py": (
        "field_name reads what pydantic's BaseModel carries; §14 step 7 moves D3's name "
        "rules into lower/names.py, where §8's ban applies, and has to answer it"
    ),
}

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
#: §14 step 4 moved the renderer out of ``compiler.py`` and this set did NOT shrink by
#: it, because the renderer was never what forced the one entry §9 does not permit:
#: ``harness.py`` takes ``compiler.escape_key`` and ``compiler.node_at`` -- a JSON Pointer
#: segment speller and its inverse, which §11 puts in the SOURCE layer (``bundle.py``,
#: already permitted here) and not in the walk.
#:
#: **Moving the pair to ``bundle.py`` today makes the rule greener and the coupling
#: wider, which is why it waits.**  Measured, as the ``codegen`` modules each import
#: pulls in: ``codegen.compiler`` reaches 4 (``compiler``, ``ir``, ``keywords``,
#: ``refusal``), and ``codegen.bundle`` reaches 8 -- those four plus ``bundle``,
#: ``lower``, ``lower.rules`` and ``lower.union``, because ``bundle`` imports two
#: LOWERINGS for its root selectors.  §9's reason is that the verifier must not read the
#: walk, so trading one named import for a transitive reach into ``codegen.lower`` buys
#: the ratchet a line and costs the section its point.  **§14 step 5 is the row that
#: retires this entry**: it deletes the root selectors from ``bundle.py`` along with
#: ``content_key``, ``object_constrained`` and the HANDLED sets, and the pointer speller
#: can then move to a ``bundle`` that reaches no lowering.
#:
#: A hand-written entry names itself and can be audited, where a rule wide enough to
#: admit it would admit the walk as well: this set may SHRINK and may not grow.
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
