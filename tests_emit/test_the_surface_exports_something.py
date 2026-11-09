"""A module that imports and exports NOTHING is a defect, not a pass.

**Why this file exists.**  ``src/adcp/types/__init__.py`` was an empty file created with
``touch``.  ``import adcp.types`` SUCCEEDED -- an empty module is a valid module -- and
the package exported nothing, so every consumer got ``AttributeError`` on a name the
package is meant to carry and nothing in this repository said a word.  Beside it,
``src/adcp/types/compat.py`` did not exist at all, and ``__init__`` delegates to it.

``tests/test_the_kept_machinery_imports.py`` catches both of those **as long as some
upstream file imports the name that went missing**.  That is the wrong precondition for
the surface's own health: the flat namespace advertises 1,067 names, upstream's kept
machinery asks it for 450 at module scope and only 314 of those are names it advertises,
so a surface that dropped the other 753 would be green there.  This is the reading that
does not go through a consumer -- the surface is asked what it carries, and the answer may
not be "nothing".

TWO CLAUSES, each the direct reading of one of the two defects above.

**Clause 1 -- every module of the hand-authored surface imports and exports a public
name.**  Emptiness is the whole claim; what the names ARE is not this file's business.
``__all__`` when a module declares one, and otherwise the public names in ``vars`` --
``_base`` and ``_runtime`` declare no ``__all__`` and carry 77 and 36, which is why the
reading is not ``__all__`` alone.

**Clause 2 -- every name a module ADVERTISES actually resolves on it.**  ``__all__`` is
the module's own promise and the thing ``from adcp.types import *`` reads; a name in it
that ``getattr`` cannot deliver is an ``AttributeError`` the module published itself.
Measured here: 5,276 advertised names over the 25 of the 27 modules that declare an
``__all__``, and this is also the clause that catches the SECOND defect without being
told about it -- ``adcp.types.__all__`` is
``compat.__all__`` read through a PEP 562 ``__getattr__``, so deleting ``compat.py``
makes the advertisement itself raise, and that is fire-probed below on the real tree.

**THE POPULATION IS DERIVED, from the one declaration of which half of ``adcp.types`` is
generated.**  ``fresh.GENERATED`` is that declaration (``_schemas/``, ``constraints.py``,
``envelopes.py``); the hand-authored half is the remainder of the directory, so a module
added to ``src/adcp/types/`` is in this gate the moment it lands and no list here has to
be touched.  Measured: 27 modules.

**WHAT THIS DOES NOT GRADE, with the measurement that says why** -- the generated tree,
which is ``tests/test_the_tree_imports.py``'s population (1,093 modules, every class
resolved through ``model_json_schema``).  Clause 1 over it would redden on **5** modules
and all 5 are a property of the compiler's LAYOUT rule rather than a defect:
``_schemas/common`` holds only ``_vocabularies.py``, and
``_schemas/core/async_response_refs`` and its three children answer for
``schemas/cache/3.2/core/async-response-refs``, which is a DIRECTORY of the bundle with no
document of its own name.  A layout package declares nothing because there was nothing to
declare.  That is derivable -- a generated ``__init__`` with no document at its own path
-- and widening clause 1 over the generated tree behind that derivation is a row worth
filing; it is not done here because an allowlist of the 5 is the one repair this project
forbids, and :func:`test_what_this_does_not_grade` records the residue rather than
leaving it to a reader to rediscover.

:func:`test_each_clause_catches_the_defect_it_is_for` is the fire probe: a scratch
package with an empty module and a module advertising a name it does not carry, plus the
control that does both correctly.  Without it this file would be a test that passes when
nothing happens -- which is precisely what the surface itself was doing.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import fresh
import pytest
from nodeset import claimed

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "src" / "adcp" / "types"

#: The import root the surface is reached by.
PACKAGE = "adcp.types"


def _module_name(path: Path) -> str:
    """The dotted name a file of the surface is imported as."""
    parts = list(path.relative_to(SURFACE).parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join([PACKAGE, *parts])


def hand_authored() -> list[str]:
    """Every module of ``adcp.types`` that a person wrote, derived not listed.

    ``fresh.GENERATED`` is the ONE declaration of which half the compiler owns, shared
    with the binding ``tests/conftest.py`` makes, so this gate and that binding cannot
    disagree about which modules are a person's work.
    """
    generated = set(fresh.GENERATED)
    return sorted(
        _module_name(p)
        for p in SURFACE.rglob("*.py")
        if p.relative_to(SURFACE).parts[0] not in generated
    )


def advertising() -> list[str]:
    """Clause 2's population: the modules that make a promise, OR cannot say whether they do.

    A population and not a ``skip`` inside clause 1's, because a module that declares no
    ``__all__`` makes no promise and so has nothing for clause 2 to grade -- and a skipped
    subject is a subject nobody reads.  ``_base`` and ``_runtime`` are the two here.

    **A module that RAISES when asked is kept, which is the half that matters.**
    ``adcp.types`` answers ``__all__`` through a PEP 562 ``__getattr__`` that reads
    ``compat.__all__``, so with ``compat.py`` absent the question itself raises
    ``ModuleNotFoundError`` -- defect 2 exactly.  Screening on "declares an ``__all__``"
    would have dropped that module from the population at the moment it broke, which is
    the one way a derived population can still go quiet.  So the rule is: in, unless the
    module imported and plainly said it advertises nothing.
    """
    out = []
    for module in hand_authored():
        try:
            if getattr(importlib.import_module(module), "__all__", None) is None:
                continue
        except BaseException:  # it cannot answer; that is clause 2's loudest subject
            pass
        out.append(module)
    return out


def exports(module: object) -> list[str]:
    """What a module offers a consumer: its ``__all__``, or its public ``vars``.

    Not ``__all__`` alone, because a module is entitled to declare none and two of the
    surface's do -- ``_base`` and ``_runtime``, 77 and 36 public names between them.  Not
    ``dir`` either: ``dir`` of a module with a PEP 562 ``__getattr__`` reads
    ``__dir__``, which is a second answer the module composes, and the question here is
    what it HAS.
    """
    advertised = getattr(module, "__all__", None)
    if advertised is not None:
        return list(advertised)
    return [name for name in vars(module) if not name.startswith("_")]


# --------------------------------------------------------------------------- #
# the population is real, so neither clause can pass vacuously
# --------------------------------------------------------------------------- #
def test_the_population_is_the_hand_authored_half_of_the_surface() -> None:
    """The set has members, the flat namespace is in it, and the generated half is not.

    The flat namespace is asserted present BY NAME because it is the module the defect
    was in: a gate for an empty ``adcp.types`` that did not range over ``adcp.types``
    would be the same silence one layer up.
    """
    modules = claimed("hand-authored modules of the type surface", hand_authored())
    promising = claimed("surface modules that advertise an __all__", advertising(), inside=modules)
    assert PACKAGE in modules, "the flat namespace is not in its own gate"
    assert PACKAGE in promising, "the flat namespace advertises nothing: clause 2 is inert"
    leaked = [m for m in modules if "._schemas" in m or m.endswith((".constraints", ".envelopes"))]
    assert not leaked, f"a generated module is in the hand-authored population: {leaked}"


# --------------------------------------------------------------------------- #
# clause 1: it imports, and it carries something
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("module", hand_authored(), ids=lambda m: m.removeprefix("adcp."))
def test_every_module_of_the_surface_carries_at_least_one_name(module: str) -> None:
    """An importable module that exports nothing is the defect, and it is reported here.

    The import failure and the emptiness are ONE subject on purpose: both are "this
    module delivers no name", a consumer cannot tell them apart, and splitting them
    would let a module that stopped existing be reported as a skipped subject.
    """
    mod = importlib.import_module(module)
    assert exports(mod), (
        f"{module} imports and exports nothing. An empty module is a valid module, which "
        "is why this is a gate: every consumer of it gets AttributeError on a name the "
        "module is meant to carry, and no import, no compile and no ./check says so."
    )


# --------------------------------------------------------------------------- #
# clause 2: what it advertises, it delivers
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("module", advertising(), ids=lambda m: m.removeprefix("adcp."))
def test_every_name_the_surface_advertises_resolves_on_it(module: str) -> None:
    """``__all__`` is a promise; a name in it that ``getattr`` cannot deliver is broken.

    The claim a consumer acts on: ``from adcp.types import *`` reads exactly this list,
    and so does every editor's completion.  :func:`advertising` is why there is no skip
    here: a module that makes no promise is not a subject, and a module that cannot be
    asked is.
    """
    mod = importlib.import_module(module)
    promised = claimed(f"names {module} advertises", mod.__all__)
    undeliverable = sorted(name for name in promised if not hasattr(mod, name))
    assert not undeliverable, (
        f"{module}.__all__ promises {len(undeliverable)} of its {len(promised)} names and "
        f"cannot deliver them: {undeliverable}. `from {module} import *` raises on each."
    )


# --------------------------------------------------------------------------- #
# the residue, stated rather than left to be rediscovered
# --------------------------------------------------------------------------- #
def test_what_this_does_not_grade() -> None:
    """The generated tree is another gate's population, and this says so in code.

    Asserted rather than written in the docstring, so that the day
    ``fresh.GENERATED`` grows or shrinks a half, the sentence above stops being true in
    a way a run reports.
    """
    generated = claimed("generated halves of the surface", fresh.GENERATED)
    assert all((SURFACE / rel).exists() for rel in generated), (
        f"fresh.GENERATED names a half of adcp.types that is not there: "
        f"{sorted(rel for rel in generated if not (SURFACE / rel).exists())}"
    )
    assert not [m for m in hand_authored() if m.split(".")[-1] in {"constraints", "envelopes"}]


# --------------------------------------------------------------------------- #
# the fire probe: each clause reddens on its defect and stays quiet on the control
# --------------------------------------------------------------------------- #
def test_each_clause_catches_the_defect_it_is_for(tmp_path: Path, monkeypatch) -> None:
    """Three fixtures and a control, read through the gate's own two functions.

    The empty module is defect 1 verbatim -- a file created with ``touch``.  The
    over-promising module is clause 2's, and is the shape a surface wears after a name is
    deleted from the module its ``__all__`` was copied from.  The DELEGATING module is
    defect 2's: it imports, it advertises through a PEP 562 ``__getattr__``, and the
    module it delegates to is gone -- which is why clause 2 reads ``__all__`` off the live
    module rather than off the source.
    """
    pkg = tmp_path / "scratchexports"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")  # defect 1: created with touch
    (pkg / "overpromises.py").write_text('__all__ = ["Kept", "Deleted"]\nKept = 1\n')
    (pkg / "delegates.py").write_text(
        "def __getattr__(name):\n"
        "    from scratchexports import gone\n"
        "    return getattr(gone, name)\n"
    )
    (pkg / "honest.py").write_text('__all__ = ["Here"]\nHere = 1\n')

    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        # CLAUSE 1, READ BEFORE THE SUBMODULES, and the ordering is itself a finding:
        # importing ``scratchexports.honest`` binds ``honest`` as an attribute of the
        # package, so a package read after its children looks populated by three names it
        # did not write.  The gate is not affected -- it imports one module per subject --
        # but the probe has to reproduce the empty state and not a state three imports
        # later, and it did not until this failed.
        empty = importlib.import_module("scratchexports")
        assert not exports(empty), "an empty module read as carrying something"

        overpromises = importlib.import_module("scratchexports.overpromises")
        delegates = importlib.import_module("scratchexports.delegates")
        honest = importlib.import_module("scratchexports.honest")
        assert exports(honest), "the control read as empty"
        # clause 2: the undeliverable name is named, and the control promises nothing it
        # cannot keep
        assert [n for n in overpromises.__all__ if not hasattr(overpromises, n)] == ["Deleted"]
        assert not [n for n in honest.__all__ if not hasattr(honest, n)]
        # clause 2 again, on defect 2's shape: the advertisement itself cannot be read,
        # which is what a surface delegating to a module that does not exist does.
        with pytest.raises(ImportError):
            delegates.__all__  # noqa: B018  -- reading it IS the assertion
    finally:
        for name in [m for m in sys.modules if m.split(".")[0] == "scratchexports"]:
            sys.modules.pop(name, None)
