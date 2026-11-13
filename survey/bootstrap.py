"""The alias layer stubbed, so a generator can run on a tree its own output must import.

**THE DEFECT IS A CYCLE AND IT IS THE SAME ONE TWICE.**  Every generator of this layer
asks one question -- *what names does the surface already bind* -- and asks it by
IMPORTING the surface.  But the surface resolves a name THROUGH this layer, so the
generator cannot run on a tree whose correct output it is about to produce.  It only ever
worked because the layer's previous output happened to import.

``survey/emit_legacy_names.py`` already met the smaller form of this and already has the
repair: its already-served check read **its own previous output** and reported 1,802 of
1,817 words as redundant, so it now writes a placeholder over ``legacy_names.py`` before
importing the surface.  **That repair is right and incomplete.**  It stubs ONE file;
``survey/adapter_surface.py``'s phase 3 stubs none, and the cycle needs every member of
the layer gone.

MEASURED, on a tree where ``core/format.json#`` has been renamed ``LegacyFormat`` and the
layer is therefore stale:

* with ``legacy_names.py`` and ``_adapter.py`` stubbed, ``adcp.types._schemas`` imports and
  so does ``adcp.types`` -- so there is **no deeper layering violation**, and the stub is
  the right instrument rather than a static read;
* but ``adapter_surface.py`` phase 3 still failed, and the chain names the missing member:
  ``codegen.patch`` -> ``codegen.bundle`` -> ``adcp.types.__getattr__`` ->
  **``_restored.__getattr__``** -> ``_restored._surface()`` ->
  ``import adcp.types.projections`` -> four names only this layer provides.

So ``_restored.py`` is a member too, and a set that named two of the five would have gone
on failing for a third reason.

**THE SET IS DERIVED FROM THE FACADE'S OWN CONSULT ORDER AND IS NOT LISTED TWICE.**
``adcp/types/__init__.py``'s ``__getattr__`` is the one authority on which modules resolve
a name, and it names them in ``importlib.import_module`` calls.  Reading those is how this
module knows the set, so a member added to the facade joins the stub automatically and a
member removed from it leaves.  A hand list here would be a second statement of the
facade's own structure and would go stale exactly when it mattered.

**THE STUB BINDS NOTHING, which is the property that makes it a repair rather than the
defect one layer along.**  A stub that re-exported the previous run's names would answer
the generator's question with the stale tree's answer -- which is the 1,802-of-1,817 defect
restated.  A docstring-only module binds nothing, so a name only this layer provides raises
``AttributeError`` during generation and the generator learns that it does not yet exist.

**AND IT SAYS WHAT IT DID.**  The files stubbed are printed, and so are the names that then
failed to resolve: a generator running against a stubbed layer is running against a
DIFFERENT tree from the one a consumer sees, and a reader of its output is entitled to know
which names that changed the answer for.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterator
from pathlib import Path

#: Where the facade states which modules resolve a name.  Read rather than restated.
FACADE = Path("src/adcp/types/__init__.py")

#: The one module the facade does NOT name, because ``_restored`` reaches it by its own
#: fallback rather than through the facade: measured, this is what ``_restored._surface()``
#: imports and what broke phase 3 after the other members were stubbed.  Named here because
#: the facade cannot name it and a reader needs to know the set is "what the facade
#: consults, plus what those consult in turn".
BENEATH = ("adcp.types.projections",)

#: **A MEMBER IS A FILE THE ALIAS LAYER GENERATES, which is a narrower set than "what the
#: facade consults" and the distinction is load-bearing.**  The facade also consults
#: ``adcp.types._surface._flat`` -- ``codegen/emit.py``'s cross-domain consolidation, part
#: of the EMITTED tree.  Stubbing that would hide real declarations and answer the
#: generator's question wrongly in the other direction: it would report names the walk
#: genuinely emits as absent.  So membership is read off each file's OWN provenance marker,
#: which is the same "derived and not listed twice" rule the set itself follows -- a file
#: whose header says a ``survey/`` generator wrote it is this layer's, and one that says
#: ``codegen`` is the tree's.
#:
#: **READ AS A PATH AND NOT AS A MARKER'S WORDING, because the wording is not uniform.**
#: ``_restored.py`` says only "GENERATED" with no generator named, and it is the member
#: whose absence broke phase 3 -- so a screen keyed on the marker's text dropped exactly
#: the file the measurement had just identified.  What IS uniform is the layout: the
#: emitted tree lives under ``_surface/`` and ``_schemas/`` (``codegen/emit.py`` writes
#: both), and every other module the facade resolves through is this layer's.  So the
#: screen is the package path, which ``docs/plan/rebuild-plan.md`` §1 fixes and no
#: generator's prose can drift from.
EMITTED = ("adcp.types._surface", "adcp.types._schemas")

STUB = (
    '"""Stubbed by survey/bootstrap.py for one generation pass.\n\n'
    'This module binds NOTHING on purpose: a generator asking "what does the surface\n'
    'already bind" must not be answered with the previous run\'s answer.\n\n'
    'survey/bootstrap.py carries the measurement.  The generator rewrites this file\n'
    'before it exits.\n"""\n\n'
    '#: EMPTY AND NOT ABSENT, which is the one structural fact a stub still owes.  A\n'
    '#: generator asks this layer what it exports -- adapter_surface.demand reads it --\n'
    '#: and an absent __all__ raises AttributeError at the ASKING rather than at a name,\n'
    '#: which tells the generator nothing about the tree.  Empty is the truthful answer:\n'
    '#: this module exports nothing yet, so every name still raises when it is looked up.\n'
    '__all__: list[str] = []\n'
)



def members(facade: Path = FACADE) -> list[str]:
    """Every module the facade resolves a name THROUGH, in the order it consults them.

    Read off the ``importlib.import_module("adcp.types...")`` calls in the facade's own
    ``__getattr__``, so this is the facade's statement and not a copy of it.  ``_schemas``
    is excluded by construction -- it is where declarations LIVE rather than a resolver,
    and the measurement above confirms it imports with the layer gone.
    """
    found = re.findall(r'import_module\(\s*"(adcp\.types[\w.]*)"', facade.read_text())
    src = facade.parent
    out: list[str] = []
    for name in [*found, *BENEATH]:
        #: The EMITTED tree is not this layer and must not be stubbed: stubbing it would
        #: report names the walk genuinely emits as absent, which is the generator's
        #: question answered wrongly in the other direction.
        if name.startswith(EMITTED) or name in out:
            continue
        if _path_of(name, src).exists():
            out.append(name)
    return out


def _path_of(module: str, src: Path) -> Path:
    rel = module.removeprefix("adcp.types").lstrip(".").replace(".", "/")
    direct = src / f"{rel}.py" if rel else src / "__init__.py"
    return direct if direct.exists() else src / rel / "__init__.py"


@contextlib.contextmanager
def with_the_layer_stubbed(
    src: Path = Path("src/adcp/types"), facade: Path = FACADE, announce: bool = True
) -> Iterator[list[Path]]:
    """Every member of the alias layer replaced by a binding-nothing stub, then restored.

    Restored on the way out INCLUDING on an exception, because a generator that died
    half-way must not leave the tree unimportable -- the next thing a lane does is read a
    traceback, and it needs the tree it had.  A generator that SUCCEEDS has rewritten these
    files itself, and its own output is what the restore then puts back; so the restore
    reads each file at exit rather than trusting what it saved.
    """
    stubbed: list[Path] = []
    held: dict[Path, str] = {}
    for module in members(facade):
        path = _path_of(module, src)
        if not path.exists():
            continue
        held[path] = path.read_text()
        path.write_text(STUB)
        stubbed.append(path)
    if announce:
        print(f"stubbed {len(stubbed)} members of the alias layer:")
        for path in stubbed:
            print(f"    {path}")
    try:
        yield stubbed
    finally:
        for path, text in held.items():
            #: Only where the generator did NOT rewrite it: a file still holding the stub
            #: is one the pass never reached, and leaving it stubbed is how a half-finished
            #: run becomes an unimportable tree.
            if path.read_text() == STUB:
                path.write_text(text)


def unresolved(names: list[str], src: Path = Path("src/adcp/types")) -> list[str]:
    """Which of ``names`` do not resolve with the layer stubbed -- said rather than implied.

    A generator running against a stubbed layer grades a DIFFERENT tree from the one a
    consumer sees.  This is the difference, by name, so the generator's own report can
    carry it instead of a reader discovering it from an output that is quietly short.
    """
    import importlib

    surface = importlib.import_module("adcp.types")
    out = []
    for name in names:
        try:
            getattr(surface, name)
        except AttributeError:
            out.append(name)
    return out
