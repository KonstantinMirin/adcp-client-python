"""Every name upstream's kept machinery imports from our type surface RESOLVES.

**Why this file exists, and it is a defect report rather than a preference.**  Three
defects landed on this branch in one day, and all three are the same sentence -- *a name
that should resolve does not* -- and all three were invisible to ``./check``:

* ``src/adcp/types/__init__.py`` was an EMPTY file created with ``touch``.
  ``import adcp.types`` SUCCEEDED and exported nothing, so every consumer got
  ``AttributeError`` on a name the package is meant to carry.  An empty module is a
  valid module; nothing in the fast loop reads a module for what it exports.
* ``src/adcp/types/compat.py`` did not exist at all, and the flat module imports it.
  Silent until something reached it.
* a function one module calls was deleted from another by a file copy between branches
  with different bases.  The branch was broken for three commits and ``./check`` stayed
  green the whole time, because ``./check`` does not reach the grading path.

``./check`` reads the COMPILER (emitted / refused / approximated).  It never imports
upstream's machinery, so no number it prints moves when our surface stops carrying a
name that machinery asks for.  This file is the reading that moves.

**THE POPULATION IS DERIVED AND IS NEVER LISTED.**  There is no table of expected names
here, because a hand-written list of names is an allowlist: it goes stale on the first
upstream file that imports something new, and it would make the gate's own blind spot
exactly the change the gate is for.  The population is a function of upstream's own
source -- :func:`pairs` parses every file of the kept machinery and reads its imports --
so an upstream file that starts importing a new name enlarges this gate by itself.

WHAT IS IN THE POPULATION, and the two decisions it rests on.

*The files*: every ``.py`` under ``src/adcp/`` EXCLUDING ``src/adcp/types/``.  That
subtree is OUR surface; the rest is upstream's kept machinery, which is the party whose
imports are the subject.  Measured on this branch: 371 files, 99 of which import from
``adcp.types`` at module scope.

*The imports*: ``ImportFrom`` nodes AT MODULE SCOPE, resolved to an absolute module that
is ``adcp.types`` or under it.  "Module scope" means the statements that run when the
module is imported, which is the module body plus -- recursively -- the bodies of
module-scope ``if`` and ``try``, and NOT the body of a ``def`` or a ``class``.  Three
consequences of that definition, each measured rather than assumed:

* **an ``if TYPE_CHECKING:`` import IS in the population** (663 of 1,423 pairs here).
  It is a module-scope import; what differs is only WHO reads it.  A missing name there
  does not abort the import, it fails the type checker and every
  ``typing.get_type_hints`` call over the annotations it feeds -- and this repository
  grades a type checker (``tests/test_type_checker.py``), so the name is owed either
  way.  :func:`report` keeps the two apart as ``aborts`` and ``annotations_only``,
  because the repair is the same and the urgency is not.
* **a FUNCTION-LOCAL import is NOT** (199 pairs here, excluded).  It runs when the
  function is called, so a missing name there costs one call path and not the file --
  a different hazard, with a different blast radius, and it would dilute the
  attribution below.  Twelve of those 199 sit inside methods of a class, which is
  function-local and not class-scope.
* **a CLASS-SCOPE import would be in the population**, since a class body runs at
  import; there are NONE on this branch (measured zero), so the clause costs nothing
  and is stated rather than argued.

**WHAT ``ImportFrom`` SEMANTICS ARE, because the gate has to be the interpreter's own.**
``from M import N`` imports ``M``, then takes ``N`` as an attribute of it, and failing
that imports the submodule ``M.N``.  :func:`resolves` is those three steps in that
order; a name that is only ever a submodule (``from adcp.types import compat``) resolves
by the third, and no gate reading ``dir(M)`` alone would see it.

**THE ATTRIBUTION IS THE USEFUL HALF.**  Because the imports are at module scope, one
absent name takes the whole file and every name that file carried -- so the reading that
helps is not "226 names are absent" but "65 files cannot import, and here is what each
one is missing".  :func:`test_every_name_one_source_file_imports_resolves` is therefore
parametrized BY SOURCE FILE: the subject is the casualty, and its failure message is the
repair list for that one file.
:func:`test_every_module_of_the_type_surface_carries_what_is_asked_of_it` is the same
population on the other axis -- the subject is the module where the repair LANDS, and it
names the files that die with it.  Two axes over one derivation, because "who dies" and
"who must change" are different questions and a lane needs both.

**THIS GATE IS RED, AND THAT IS THE CORRECT STATE.**  Measured on ``dropin/gate`` at
3d1e5379f: 1,423 pairs, 792 resolve, 405 blocked by a module that does not import, 226
blocked by 155 names a module does not carry, 65 source files unable to import.  The
figures are not pinned here -- a pin would be one tree's reading of a quantity two other
lanes are moving right now -- and the gate is not scoped, xfailed or allowlisted to make
it green.  A red gate with a named reason per subject is a work list; a green gate with
a narrowed population is the thing this project forbids.  ``adcp-client-python-fwvm``
owns the names, and the ``adcp.types.domains.**`` tree owns the modules.

**THE TREE GRADED IS THE ONE A FRESH RUN EMITS**, which is ``tests/conftest.py``'s
binding and not a choice this file makes: the generated half of ``adcp.types``
(``_schemas/``, ``constraints.py``, ``envelopes.py``) resolves from the fresh compile
that ``tests/fresh.py`` materialises, the hand-authored half from ``src/``.  That is
``docs/plan/architecture.md``'s rule that grading reads the emitted tree and the
committed one is an artifact, and it is why this gate cannot be satisfied by committing a
module the compiler does not produce.

:func:`test_the_reading_catches_an_absent_name` is the fire probe: a scratch package is
built whose module is missing one name, and each of the three readings is asserted to
redden on the defect it is for and to stay quiet on the control.  Without it this file
would be a test that passes when nothing happens.
"""

from __future__ import annotations

import ast
import collections
import functools
import importlib
import sys
from pathlib import Path
from typing import NamedTuple

import pytest
from nodeset import claimed

#: The repository root, and the two halves of the tree this gate is about.  ``SURFACE``
#: is ours and is the thing asked; ``MACHINERY`` is upstream's and is the thing asking.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MACHINERY = SRC / "adcp"
SURFACE = MACHINERY / "types"

#: The import root the population is about.  A pair is in scope when its module is this
#: name or lives under it; ``adcp.types`` ITSELF counts, because the flat namespace is
#: where defect 1 above was and ``from adcp.types import X`` is how a consumer reaches it.
PACKAGE = "adcp.types"


def _package(path: Path) -> str:
    """The PACKAGE a file in ``src/`` is imported inside, which is what anchors a
    relative import.

    ``__package__`` and not ``__name__``, and the difference is the whole reason this is
    a function: for ``src/adcp/foo.py`` it is ``adcp``, and for
    ``src/adcp/sub/__init__.py`` it is ``adcp.sub`` -- a package's ``__init__`` anchors
    inside ITSELF, so ``from .x import y`` there means ``adcp.sub.x`` and the same
    spelling in ``adcp/sub.py`` would mean ``adcp.x``.  There are no relative imports
    into ``adcp.types`` on this branch (measured zero), so nothing today depends on
    getting this right -- which is exactly why it is written to be right rather than to
    be enough.  Dropping the filename is the whole rule in both cases, and the two cases
    are why: ``adcp/sub/__init__.py`` loses ``__init__.py`` to leave ``adcp.sub``, and
    ``adcp/sub.py`` loses ``sub.py`` to leave ``adcp``.
    """
    return ".".join(path.relative_to(SRC).parts[:-1])


def _absolute(node: ast.ImportFrom, package: str) -> str | None:
    """``from .x import y`` as the absolute module it names, from inside ``package``."""
    if node.level == 0:
        return node.module
    anchor = package.split(".")[: len(package.split(".")) - node.level + 1]
    if not anchor or not anchor[0]:
        return None
    return ".".join(anchor + ([node.module] if node.module else []))


class Pair(NamedTuple):
    """One ``(module, name)`` an upstream file asks our surface for, with its site.

    A tuple so a pair is hashable and sorts, which is what lets the two axes below be
    two groupings of ONE derivation rather than two derivations that can disagree.
    """

    file: str
    module: str
    name: str
    line: int
    #: Under a module-scope ``if TYPE_CHECKING:``, so an absent name fails the type
    #: checker and ``get_type_hints`` rather than the import itself.
    type_checking: bool

    def __str__(self) -> str:
        return f"{self.module}.{self.name}"


def _module_scope(body: list[ast.stmt], *, type_checking: bool):
    """Every ``ImportFrom`` that RUNS when the module is imported, with its guard.

    Descends ``if`` and ``try`` because neither opens a scope and both execute at import;
    does not descend ``def`` or ``class``, which is the line the docstring draws.  A
    ``try`` body is not screened out even when its handler catches ``ImportError``: there
    are none in this population, and a guarded import that silently degrades is the
    shape defect 2 above wore, so the screen would have to be argued for rather than
    assumed.
    """
    for stmt in body:
        if isinstance(stmt, ast.ImportFrom):
            yield stmt, type_checking
        elif isinstance(stmt, ast.If):
            guard = type_checking or "TYPE_CHECKING" in ast.unparse(stmt.test)
            yield from _module_scope(stmt.body, type_checking=guard)
            yield from _module_scope(stmt.orelse, type_checking=type_checking)
        elif isinstance(stmt, ast.Try):
            for part in (stmt.body, stmt.orelse, stmt.finalbody):
                yield from _module_scope(part, type_checking=type_checking)
            for handler in stmt.handlers:
                yield from _module_scope(handler.body, type_checking=type_checking)


def machinery() -> list[Path]:
    """Upstream's kept machinery: ``src/adcp`` with our own surface taken out."""
    return sorted(p for p in MACHINERY.rglob("*.py") if SURFACE not in p.parents and p != SURFACE)


@functools.cache
def pairs() -> tuple[Pair, ...]:
    """Every ``(module, name)`` the kept machinery asks of :data:`PACKAGE`, derived.

    Cached because both axes and the census read it and the parse is the same answer
    every time; the cache holds AST results only, so it is safe before the fresh binding.
    """
    found: list[Pair] = []
    for path in machinery():
        here = _package(path)
        tree = ast.parse(path.read_text(), filename=str(path))
        for node, type_checking in _module_scope(tree.body, type_checking=False):
            module = _absolute(node, here)
            if module != PACKAGE and not (module or "").startswith(f"{PACKAGE}."):
                continue
            for alias in node.names:
                if alias.name == "*":
                    # A star import asks for whatever the module exports, so there is no
                    # pair to resolve and the EMPTY-SURFACE reading is the one that
                    # answers for it.  None on this branch; reported, not skipped, so a
                    # new one does not vanish into this loop.
                    found.append(Pair(str(path), module, "*", node.lineno, type_checking))
                    continue
                found.append(Pair(str(path), module, alias.name, node.lineno, type_checking))
    return tuple(found)


@functools.cache
def _imported(module: str) -> object | str:
    """The module, or the one-line reason it did not import.

    One import per module per process whatever asks, and the failure is RETURNED rather
    than raised: the obligation ranges over every pair, and the first unimportable module
    would otherwise hide every pair behind it -- the same shape as the defect this file
    reports.
    """
    try:
        return importlib.import_module(module)
    except BaseException as exc:  # a module can fail by any means; all of them count
        return f"{type(exc).__name__}: {exc}"


def resolves(module: str, name: str) -> bool | str:
    """``from <module> import <name>``, by the interpreter's own three steps.

    ``True``, ``False`` when the module imports and does not carry the name, or the
    module's own failure as a string -- three outcomes and not two, because "the module
    is absent" and "the module is there and the name is not" are different repairs owned
    by different lanes.
    """
    mod = _imported(module)
    if isinstance(mod, str):
        return mod
    if name == "*":
        public = getattr(mod, "__all__", None) or [n for n in vars(mod) if n[:1] != "_"]
        return bool(public)
    try:
        if hasattr(mod, name):  # step 2: an attribute, including a PEP 562 __getattr__
            return True
    except BaseException:
        return False
    return not isinstance(_imported(f"{module}.{name}"), str)  # step 3: a submodule


def report() -> dict[str, dict]:
    """The whole population resolved once, grouped both ways.

    ``by_file`` is the casualty list and ``by_module`` the repair list; both are built
    here from one pass so the two axes cannot report different totals.
    """
    by_file: dict[str, dict[str, list[Pair]]] = collections.defaultdict(
        lambda: {"aborts": [], "annotations_only": []}
    )
    by_module: dict[str, dict] = collections.defaultdict(
        lambda: {"why": None, "absent": set(), "askers": set()}
    )
    resolving: list[Pair] = []
    for pair in pairs():
        outcome = resolves(pair.module, pair.name)
        if outcome is True:
            resolving.append(pair)
            continue
        where = "annotations_only" if pair.type_checking else "aborts"
        by_file[pair.file][where].append(pair)
        entry = by_module[pair.module]
        entry["askers"].add(pair.file)
        if isinstance(outcome, str):
            entry["why"] = outcome
        else:
            entry["absent"].add(pair.name)
    return {"by_file": dict(by_file), "by_module": dict(by_module), "resolving": resolving}


def _id(path: str) -> str:
    return Path(path).relative_to(MACHINERY).as_posix()


def _importers() -> list[str]:
    """The source files that ask our surface for anything, which are the subjects."""
    return sorted({p.file for p in pairs()})


def _asked_modules() -> list[str]:
    return sorted({p.module for p in pairs()})


# --------------------------------------------------------------------------- #
# the population is real, so no reading below can pass vacuously
# --------------------------------------------------------------------------- #
def test_the_population_is_derived_from_upstreams_own_source() -> None:
    """Every set the readings range over has members, and the excluded halves are out.

    A derivation that selects nothing passes every assertion over it and is
    indistinguishable from a working gate, which is the failure this suite has measured
    twice.  So: the files, the pairs, the asked modules and both scope buckets are each
    claimed, OUR surface is asserted absent from the subjects, and the flat namespace is
    asserted present among the modules asked -- it is where defect 1 was.
    """
    files = claimed("kept machinery files", machinery())
    inside = {str(p) for p in files}
    subjects = claimed("files importing the type surface", _importers(), inside=inside)
    asked = claimed("modules of the type surface asked for", _asked_modules())
    population = claimed("module-scope (module, name) pairs", pairs())

    assert not [p for p in files if SURFACE in Path(p).parents], "our own surface is being graded"
    escaped = [p for p in population if not p.module.startswith(PACKAGE)]
    assert not escaped, f"a pair escaped the root this gate claims: {escaped}"
    assert PACKAGE in asked, "nothing asks the flat namespace, where the empty-surface defect was"
    assert len(subjects) < len(files), "every file imports the surface: the filter is inert"

    # Both scope buckets are real, so neither clause of the TYPE_CHECKING split is a
    # dead branch nobody would notice going empty.
    claimed("pairs that run at import", [p for p in population if not p.type_checking])
    claimed("pairs read only by a type checker", [p for p in population if p.type_checking])


# --------------------------------------------------------------------------- #
# axis 1: the casualty.  one subject per source file that asks anything
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("source", _importers(), ids=_id)
def test_every_name_one_source_file_imports_resolves(source: str) -> None:
    """This file's module-scope imports of our surface all resolve, or it names why.

    THE SUBJECT IS THE FILE AND NOT THE NAME, because the imports are at module scope:
    one absent name takes the whole file and every name that file carried, so the
    quantity a lane can act on is "this file cannot import, and here is its list".
    """
    blocked = {"aborts": [], "annotations_only": []}
    reasons: dict[str, str] = {}
    for pair in [p for p in pairs() if p.file == source]:
        outcome = resolves(pair.module, pair.name)
        if outcome is True:
            continue
        blocked["aborts" if not pair.type_checking else "annotations_only"].append(
            f"line {pair.line}: {pair}"
        )
        if isinstance(outcome, str):
            reasons[pair.module] = outcome

    assert not blocked["aborts"] and not blocked["annotations_only"], (
        f"{_id(source)} imports names our type surface does not resolve.\n"
        f"  aborts at import ({len(blocked['aborts'])}): {sorted(blocked['aborts'])}\n"
        f"  type-checker only ({len(blocked['annotations_only'])}): "
        f"{sorted(blocked['annotations_only'])}\n"
        f"  modules that did not import: {reasons}\n"
        "These are module-scope imports: one absent name takes this whole file. The "
        "repair is a name our surface carries, or upstream's import changed -- never an "
        "entry in a list here."
    )


# --------------------------------------------------------------------------- #
# axis 2: the repair site.  one subject per module of our surface that is asked
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("module", _asked_modules(), ids=lambda m: m.removeprefix("adcp."))
def test_every_module_of_the_type_surface_carries_what_is_asked_of_it(module: str) -> None:
    """This module of ours imports, and carries every name the machinery asks of it.

    The other grouping of the same pairs, and the one a lane holding a module works
    from: the failure names the absent names and the upstream files that die for them,
    so the cost of the row is visible beside the row.
    """
    asked = claimed(
        f"names asked of {module}", {p.name for p in pairs() if p.module == module}
    )
    mod = _imported(module)
    askers = sorted(_id(p.file) for p in pairs() if p.module == module)
    assert not isinstance(mod, str), (
        f"{module} does not import ({mod}); {len(askers)} upstream files import "
        f"{len(asked)} names from it at module scope and every one of them dies: {askers}"
    )
    absent = sorted(n for n in asked if resolves(module, n) is not True)
    assert not absent, (
        f"{module} imports but does not carry {len(absent)} of the {len(asked)} names "
        f"asked of it: {absent}\n"
        f"  the files that import from it: {askers}"
    )


# --------------------------------------------------------------------------- #
# the whole population, ranked -- the work list the two open lanes read
# --------------------------------------------------------------------------- #
def test_no_file_of_the_kept_machinery_is_blocked_from_importing_our_surface() -> None:
    """The population in one message, ranked by how many names each file is missing.

    The per-file subjects above are what a lane fixes against; this is what a lane reads
    FIRST, because 65 failing items do not say which of them is the expensive one.  It
    asserts the same thing they do over the same derivation, so it cannot disagree with
    them -- it only orders the answer.
    """
    grouped = report()
    dead = grouped["by_file"]
    claimed("pairs that resolve", grouped["resolving"])
    ranked = sorted(
        (
            (
                len(v["aborts"]) + len(v["annotations_only"]),
                _id(f),
                {k: sorted(str(p) for p in v[k]) for k in v if v[k]},
            )
            for f, v in dead.items()
        ),
        reverse=True,
    )
    assert not ranked, (
        f"{len(ranked)} of the {len(_importers())} files that import our type surface "
        f"cannot, ranked by names missing:\n"
        + "\n".join(f"  {n:4d}  {name}  {what}" for n, name, what in ranked)
    )


# --------------------------------------------------------------------------- #
# the fire probe: the readings redden on the defect, and not on the control
# --------------------------------------------------------------------------- #
def test_the_reading_catches_an_absent_name(tmp_path: Path) -> None:
    """A scratch surface with one name removed, and the three outcomes told apart.

    Four fixtures and all three outcomes of :func:`resolves`, because a gate that cannot
    be shown to redden is a test that passes when nothing happens: a name the module
    carries, a name it does not, a module that is absent, and a SUBMODULE name -- which
    is the one ``dir(module)`` would call absent and the interpreter resolves.  And the
    scope reading is probed on the same tree: a function-local import of an absent name
    is NOT in the population and a ``TYPE_CHECKING`` one is.
    """
    pkg = tmp_path / "scratchsurface"
    (pkg / "types").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "types" / "__init__.py").write_text("KEPT = 1\n")
    (pkg / "types" / "sub.py").write_text("ALSO_KEPT = 2\n")
    sys.path.insert(0, str(tmp_path))
    try:
        assert resolves("scratchsurface.types", "KEPT") is True
        assert resolves("scratchsurface.types", "REMOVED") is False, "an absent name passed"
        assert resolves("scratchsurface.types", "sub") is True, "a submodule read as absent"
        gone = resolves("scratchsurface.types.nosuchmodule", "Anything")
        assert isinstance(gone, str) and "Error" in gone, gone
    finally:
        sys.path.remove(str(tmp_path))

    importer = tmp_path / "importer.py"
    importer.write_text(
        "from typing import TYPE_CHECKING\n"
        "from adcp.types.scratch import AtModuleScope\n"
        "if TYPE_CHECKING:\n"
        "    from adcp.types.scratch import UnderTypeChecking\n"
        "try:\n"
        "    from adcp.types.scratch import InATry\n"
        "except ImportError:\n"
        "    InATry = None\n"
        "def f():\n"
        "    from adcp.types.scratch import FunctionLocal\n"
        "class C:\n"
        "    def m(self):\n"
        "        from adcp.types.scratch import MethodLocal\n"
    )
    tree = ast.parse(importer.read_text())
    seen = {
        alias.name: guard
        for node, guard in _module_scope(tree.body, type_checking=False)
        for alias in node.names
    }
    assert seen == {
        "TYPE_CHECKING": False,
        "AtModuleScope": False,
        "UnderTypeChecking": True,
        "InATry": False,
    }, seen
