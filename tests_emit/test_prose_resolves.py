"""A docstring that names a path or a symbol is CHECKED, not reviewed.

**Why this file exists, and it is a defect report rather than a preference.**  Two
docstrings this SDK ships to consumers asserted a surface that does not exist.
``adcp/types/constraints.py`` told a consumer that "every other type this SDK emits is
reachable at ``adcp.types.<domain>.<Name>``" -- there is no domain module, and every
consumer import today is the private ``adcp.types._schemas`` path.
``adcp/types/__init__.py`` pointed at "the binding table in step 9" for a step that has
landed and owns no binding table.  Both shipped, both were read by the audience they were
addressed to, and **nothing failed while they were false**, which is the whole mechanism:
a docstring claiming a property is not evidence the property holds.

The claims that went wrong are the ones a machine can settle.  A dotted import path either
imports or it does not; a cross-reference either names a live symbol or it does not.  So
this file asserts the two:

* **Clause 1 -- the shipped paths resolve.**  Every ``adcp``-rooted dotted path in the
  prose of the hand-authored package imports, and a trailing capitalised segment is an
  attribute of the module it is named under.
* **Clause 2 -- no shipped path is a TEMPLATE.**  A path with a ``<placeholder>`` segment
  cannot be checked by importing it, and it is exactly the shape that shipped false.  A
  sentence describing a surface that does not exist yet must cite the document that owns
  it instead of spelling a path a reader will try.  :data:`PLACEHOLDERS_ALLOWED` is empty
  and may only shrink.
* **Clause 3 -- the GENERATOR's copies obey both.**  ``constraints.py`` and
  ``envelopes.py`` are generated, so their prose lives in ``codegen/render.py`` as two
  string constants.  Grading only the committed tree would pass a reintroduction until
  someone regenerated; the constants are read directly here as well.
* **Clause 4 -- every DOTTED cross-reference resolves**, over the compiler's prose and the
  package's.  This is the other half of the same defect: ``emit._decide`` was named as the
  live per-node dispatch in eleven places after §14 step 5 moved it to
  ``codegen/lower/decide.py``, and the first sentence a lane picking up step 5 would read
  was the stalest one in the tree.

**What is deliberately NOT graded, with the measurement that says why, and both figures
are re-derivable by running the clauses over a widened harvest.**

A BARE role -- ``:attr:`drops```, ``:func:`declare``` -- names a symbol in the scope the
prose sits in, and most of those are ``#:`` attribute comments in a class body whose
enclosing scope a line-oriented harvest does not recover.  Widening clause 4 to bare roles
takes its population from 404 references to over 1,500 and its failures from 0 to about
80, and reading those shows them to be class attributes the resolver cannot see rather
than prose defects.  A check that reddens on its own resolver's blind spot is worse than
no check, so the rule ranges over DOTTED references, which name their own scope.

**Also not graded: a double-backticked ``module.symbol`` spelling.**  Harvested the same
way, that set is 847 references naming something of these two packages, of which 62 in 20
files do not resolve -- and the great majority are prose about a symbol that was DELETED.
"It was in ``emit.content_key`` and step 5 removed it" is TRUE, names a dead symbol on
purpose, and no mechanical reading tells it from a stale present-tense claim.  Grading it
needs either a tense judgement, which no check has, or a 62-entry allowlist of
hand-written justifications, which is a row of its own and not a line in this file.  A
Sphinx role is different IN KIND: writing ``:func:`X``` declares that ``X`` is live, and a
writer describing a removed symbol reaches for plain backticks.  That asymmetry is why the
role set is gradeable at zero and the backtick set is not.

Perturbed, each clause separately, in
:func:`test_each_rule_catches_the_prose_it_is_for`.  A rule nothing can break is a finding
about the rule.
"""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "adcp"
WALK = ROOT / "codegen"

#: The GENERATED per-document modules, excluded from the prose population by PATH.  Their
#: docstrings are the bundle's own ``description`` text copied through the renderer, so a
#: sentence in one is upstream's words and not this repository's -- and the AdCP protocol
#: spells capability keys ``adcp.attestations``, ``adcp.capability_changes...``,
#: ``adcp.principal``, which read as dotted module paths and are not.  Measured: 19
#: ``adcp``-rooted paths appear in the prose of the whole package, and 12 of the 13
#: distinct ones are protocol keys from this subtree.  What is NOT excluded is
#: ``constraints.py`` and ``envelopes.py``, which are generated BESIDE the tree and whose
#: prose this repository writes (clause 3).
GENERATED_SUBTREE = "_schemas"

#: An ``adcp``-rooted dotted path as prose spells one, placeholder segments included so
#: that clause 2 can see them.  Anchored on the package root rather than on any dotted
#: identifier, because the claim being graded is "a consumer can import this".
PATH = re.compile(r"\badcp(?:\.(?:<[^>`\s]+>|[A-Za-z_]\w*))+")

#: A Sphinx cross-reference role.  The roles that name a code object; a role naming a
#: document (``:doc:``) or a term is not a symbol claim.
ROLE = re.compile(r":(?:func|class|meth|attr|data|exc|mod):`~?([A-Za-z_][\w.]*)`")

#: **EMPTY, and the whole point of the file.**  A shipped docstring may not spell an
#: import path with a ``<placeholder>`` segment: it cannot be checked by importing it, and
#: the one that existed -- ``adcp.types.<domain>.<Name>`` in ``constraints.py`` -- was
#: false for the entire time it shipped.  Prose that needs to describe a surface which
#: does not exist cites the document that owns it (``docs/plan/surface-goal.md``,
#: ``docs/plan/unimplemented.md`` A-2) rather than spelling a path a reader will type.
#: This set may SHRINK and may not grow.
PLACEHOLDERS_ALLOWED: frozenset[str] = frozenset()

#: The two module docstrings the renderer OWNS, by the name of the constant that holds
#: each.  Derived from ``codegen.render`` rather than listed as text, so a third one added
#: later is graded by the clause that names this tuple.
RENDERED_DOCSTRINGS = ("CONSTRAINTS_DOCSTRING", "ENVELOPES_DOCSTRING")

#: The two root packages whose prose this file grades.  A reference outside them --
#: ``typing.Annotated``, ``pydantic.AnyUrl``, ``datetime.date`` -- is a reference a
#: docstring may make and is not this file's to settle.
ROOTS = frozenset({"adcp", "codegen"})

_MISSING = object()


def _dotted(pkg: Path, root: str) -> dict[str, Path]:
    """Every module under ``pkg``, dotted, less the generated per-document subtree."""
    out: dict[str, Path] = {}
    for path in pkg.rglob("*.py"):
        if GENERATED_SUBTREE in path.parts or "__pycache__" in path.parts:
            continue
        parts = list(path.relative_to(pkg).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        out[".".join([root, *parts]) if parts else root] = path
    return out


def _modules() -> dict[str, Path]:
    return {**_dotted(WALK, "codegen"), **_dotted(PKG, "adcp")}


MODULES = _modules()
BY_PATH = {path: dotted for dotted, path in MODULES.items()}
#: Leaf module name -> the dotted names it could be.  Prose writes ``nodes.Union`` and
#: ``compiler.Module`` far more often than the absolute path, and resolving the leaf is
#: what makes those checkable without a second list of aliases.
BY_LEAF: dict[str, list[str]] = {}
for _dotted_name in MODULES:
    BY_LEAF.setdefault(_dotted_name.rsplit(".", 1)[-1], []).append(_dotted_name)


def _self_attributes(cls: type) -> frozenset[str]:
    """The attribute names a class assigns to ``self`` in its own body's methods.

    ``Refusal.resolved`` is set in ``__init__`` and is neither a class attribute nor a
    dataclass field, so neither ``hasattr`` nor ``__annotations__`` sees it -- and
    ``:attr:`Refusal.resolved``` is a correct reference.  Read off the SOURCE, because the
    attribute only exists once an instance does and this check builds none.
    """
    module = MODULES.get(cls.__module__)
    if module is None:
        return frozenset()
    names: set[str] = set()
    for node in ast.walk(ast.parse(module.read_text())):
        if not isinstance(node, ast.ClassDef) or node.name != cls.__name__:
            continue
        for inner in ast.walk(node):
            targets: list[ast.expr] = []
            if isinstance(inner, ast.Assign):
                targets = list(inner.targets)
            elif isinstance(inner, ast.AnnAssign):
                targets = [inner.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    names.add(target.attr)
    return frozenset(names)


def _holds(obj: object, attr: str) -> bool:
    """Does ``obj`` carry ``attr``, including as a declaration with no value yet?

    Three readings, because a frozen dataclass field, an annotation-only slot and an
    attribute assigned in ``__init__`` are all live references and none of them answers
    ``hasattr`` on the class.
    """
    if hasattr(obj, attr):
        return True
    if is_dataclass(obj) and any(f.name == attr for f in dataclass_fields(obj)):
        return True
    if attr in getattr(obj, "__annotations__", {}):
        return True
    return isinstance(obj, type) and attr in _self_attributes(obj)


def resolve(dotted: str) -> bool | None:
    """``True`` it resolves, ``False`` it does not, ``None`` it names nothing of ours.

    The longest importable prefix wins, then the rest is an attribute walk.  ``None`` and
    not ``False`` for a path outside these two packages, because ``typing.Annotated`` and
    ``pydantic.AnyUrl`` are references a docstring may make and are not this file's to
    grade.
    """
    parts = dotted.split(".")
    if parts[0] not in ROOTS:
        return None
    #: The longest prefix that IMPORTS -- asked of the import system and not of the module
    #: tree, because the generated per-document subtree is outside this file's population
    #: and is still perfectly importable, and a path naming one must resolve.
    for cut in range(len(parts), 0, -1):
        try:
            obj: object = importlib.import_module(".".join(parts[:cut]))
        except ModuleNotFoundError:
            continue
        except Exception:
            return False
        for attr in parts[cut:]:
            if not _holds(obj, attr):
                return False
            nxt = getattr(obj, attr, _MISSING)
            if nxt is _MISSING:
                return True
            obj = nxt
        return True
    return False


def _resolves_somewhere(token: str, scope: str | None = None) -> bool | None:
    """``token`` resolved absolutely, under its leaf module, or under ``scope``."""
    head = token.split(".")[0]
    candidates = [token, *(d + token[len(head) :] for d in BY_LEAF.get(head, []))]
    if scope is not None:
        candidates.append(f"{scope}.{token}")
    answers = [resolve(c) for c in candidates]
    if any(a is True for a in answers):
        return True
    return False if any(a is False for a in answers) else None


def prose(path: Path) -> list[str]:
    """Every docstring and every comment in one module, as text.

    Comments are in because ``#:`` attribute documentation is prose a reader reads the
    same way, and two of the stale references this file was written for were in one.
    """
    source = path.read_text()
    out = [
        doc
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and (doc := ast.get_docstring(node))
    ]
    out += [line.strip() for line in source.splitlines() if line.strip().startswith("#")]
    return out


def _package_files() -> list[Path]:
    return sorted(p for p in BY_PATH if p.is_relative_to(PKG))


def _walk_files() -> list[Path]:
    return sorted(p for p in BY_PATH if p.is_relative_to(WALK))


# --------------------------------------------------------------------------- #
# the populations are real, so no clause below can pass vacuously
# --------------------------------------------------------------------------- #
def test_each_clause_has_a_population() -> None:
    """The three populations are non-empty and the excluded subtree is excluded.

    The generated per-document modules outnumber the hand-authored ones by three orders
    of magnitude, so a clause that accidentally ranged over them would drown; and one
    that accidentally ranged over NONE of the package would pass for free.  Both are
    asserted, and the two generated-beside modules are asserted PRESENT by name, because
    they are the ones the shipped defect was in.
    """
    package = {p.relative_to(PKG).as_posix() for p in _package_files()}
    assert package, "no module of the package is graded"
    assert not any(GENERATED_SUBTREE in name.split("/") for name in package), package
    assert {"types/constraints.py", "types/envelopes.py", "types/__init__.py"} <= package, package
    assert len(_walk_files()) > 10, _walk_files()
    assert (PKG / "types" / GENERATED_SUBTREE).is_dir(), "the excluded subtree does not exist"


# --------------------------------------------------------------------------- #
# clause 1 and clause 2: the shipped prose
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", _package_files(), ids=lambda p: p.relative_to(PKG).as_posix())
def test_every_import_path_the_shipped_prose_names_resolves(path: Path) -> None:
    """An ``adcp``-rooted path in a shipped docstring imports, and its name is there.

    This is the clause ``constraints.py`` failed for the whole time it shipped.  The
    failure message names the path and the file, because the repair is always one of two
    things: spell the path that does resolve, or stop spelling a path.
    """
    for text in prose(path):
        for match in PATH.finditer(text):
            token = match.group(0)
            if "<" in token:
                continue  # clause 2's, and it reports them with its own reason
            assert resolve(token) is not False, (
                f"{path.relative_to(ROOT)} names {token!r} and it does not resolve. "
                "A path a consumer can type is a claim about the artifact: either the "
                "path arrives or the sentence goes."
            )


@pytest.mark.parametrize("path", _package_files(), ids=lambda p: p.relative_to(PKG).as_posix())
def test_no_shipped_docstring_states_an_import_path_with_a_placeholder(path: Path) -> None:
    """A ``<placeholder>`` segment in a shipped import path is refused.

    Not because a template is always wrong, but because it is UNCHECKABLE and this is the
    one shape that shipped false: ``adcp.types.<domain>.<Name>`` reads as an instruction,
    the expansion resolves for nothing, and no import could have told a reader.  Prose
    that must describe a surface which has not arrived cites its owner instead --
    ``src/adcp/types/__init__.py`` is the worked example.
    """
    for text in prose(path):
        for match in PATH.finditer(text):
            token = match.group(0)
            if "<" not in token:
                continue
            assert token in PLACEHOLDERS_ALLOWED, (
                f"{path.relative_to(ROOT)} spells the import path {token!r}, which no "
                "import can check. Name a path that resolves, or cite the document that "
                "owns the surface. PLACEHOLDERS_ALLOWED may only shrink."
            )


def test_the_renderer_owns_two_shipped_docstrings_and_both_obey_the_clauses() -> None:
    """Clause 3: the GENERATOR's copy, read before anyone regenerates the tree.

    ``constraints.py`` and ``envelopes.py`` are ``f(bundle, emitter, pinned compiler)``,
    so their prose is a string constant in ``codegen/render.py``.  Grading only the
    committed file would let a reintroduction live in the generator until a regeneration
    carried it out -- and the committed tree is regenerated by a different row, so the gap
    is real rather than theoretical.
    """
    from codegen import render

    for name in RENDERED_DOCSTRINGS:
        text = getattr(render, name)
        for match in PATH.finditer(text):
            token = match.group(0)
            assert "<" not in token or token in PLACEHOLDERS_ALLOWED, (
                f"codegen/render.py's {name} spells {token!r}; it will be written into the "
                "shipped tree and no import can check it"
            )
            if "<" not in token:
                assert resolve(token) is not False, (
                    f"codegen/render.py's {name} names {token!r} and it does not resolve"
                )


# --------------------------------------------------------------------------- #
# clause 4: every dotted cross-reference, over the walk and the package
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "path",
    _walk_files() + _package_files(),
    ids=lambda p: p.relative_to(ROOT).as_posix(),
)
def test_every_dotted_cross_reference_in_the_prose_resolves(path: Path) -> None:
    """A dotted Sphinx role names a live symbol of this tree.

    Writing ``:func:`X``` declares that ``X`` is reachable; a writer describing a symbol
    that was removed reaches for plain backticks instead.  So a dotted role that does not
    resolve is either a rename nobody followed through or prose about a thing that has
    moved -- both of which mislead the next reader, and the ``emit._decide`` family is
    what this clause was written for.
    """
    for text in prose(path):
        for match in ROLE.finditer(text):
            token = match.group(1)
            if "." not in token:
                continue  # bare roles name their enclosing scope; see the module docstring
            assert _resolves_somewhere(token) is not False, (
                f"{path.relative_to(ROOT)} writes :role:`{token}` and it resolves to "
                "nothing. Point it at the symbol that exists, or drop the role and say in "
                "plain words that the symbol is gone."
            )


# --------------------------------------------------------------------------- #
# the rules are breakable, shown rather than asserted
# --------------------------------------------------------------------------- #
def test_each_rule_catches_the_prose_it_is_for(tmp_path: Path) -> None:
    """Each clause reddens on the defect it was written for, and on nothing else.

    Four fixtures: a path that does not import, a placeholder path, a dotted role naming
    a dead symbol, and the control -- the three spellings that are CORRECT and must all
    pass. The control is what stops the rule being "reject every docstring".
    """
    bad_path = tmp_path / "bad_path.py"
    bad_path.write_text('"""Reachable at ``adcp.types.domains.core.Nope``."""\n')
    placeholder = tmp_path / "placeholder.py"
    placeholder.write_text('"""Reachable at ``adcp.types.<domain>.<Name>``."""\n')
    bad_role = tmp_path / "bad_role.py"
    bad_role.write_text('"""The dispatch is :func:`emit._decide`."""\n')
    control = tmp_path / "control.py"
    control.write_text(
        '"""``adcp.types.constraints`` and ``adcp.types._schemas.core.pagination_request``'
        '\n\nand :func:`codegen.lower.decide.decide` and :class:`codegen.compiler.Module`.\n"""\n'
    )

    def paths(path: Path) -> list[str]:
        return [m.group(0) for text in prose(path) for m in PATH.finditer(text)]

    def roles(path: Path) -> list[str]:
        return [
            m.group(1)
            for text in prose(path)
            for m in ROLE.finditer(text)
            if "." in m.group(1)
        ]

    assert [resolve(p) for p in paths(bad_path)] == [False], paths(bad_path)
    assert [("<" in p) for p in paths(placeholder)] == [True], paths(placeholder)
    assert [_resolves_somewhere(r) for r in roles(bad_role)] == [False], roles(bad_role)

    assert all(resolve(p) is not False for p in paths(control)), paths(control)
    assert not any("<" in p for p in paths(control)), paths(control)
    assert all(_resolves_somewhere(r) is not False for r in roles(control)), roles(control)
