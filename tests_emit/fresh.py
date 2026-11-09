"""The generated half of ``adcp.types``, as a FRESH run emits it, on disk and BOUND.

``docs/plan/architecture.md`` (2026-10-29) decides what grading reads:

    The schema is pinned and the drawn instances are content-addressed, so what a class
    is graded against is a function of the bundle and the compiler alone.  **Grading
    therefore reads the tree a fresh run emits.  The committed tree is an ARTIFACT,
    verified by one byte-compare, and is never the subject.**

This module is the whole of how the suite obeys that, and it has to be a module rather
than a line in each reader for one reason: ``graded()`` reads the tree by IMPORTING it,
and a Python process has exactly one ``adcp.types.constraints``.  An emitted module says
``from adcp.types.constraints import StrMatchingA828669D`` -- an ABSOLUTE name -- so a
fresh ``_schemas`` imported beside the COMMITTED alias module resolves its aliases
through that module, and an alias this run mints that the committed one does not carry is
exactly the defect the arrangement exists to report.  So the generated half moves
TOGETHER or not at all, which is one decision about one package and is taken here.

**WHAT THE READING WAS.**  At the row that wrote this (``adcp-client-python-3be.1``) the
committed tree had been found to carry no module for some documents a fresh run emits and
to differ byte for byte on others, so every census over ``src/`` graded a mixture of two
compilers; most of the import-path collisions and one stale decision then on the board
were invisible in ``src/`` and visible in a fresh run.  The second failure was worse than
the first: ``graded()`` runs at PARAMETRIZE time, so one committed module that did not
import collected ZERO tests from ``tests/test_emit.py`` -- and the obligation that exists
to report such a module was one of the tests it took down.  Regenerate, then grade; the
order is the whole rule.

**WHAT IS FRESH AND WHAT IS NOT, and the split is not a convenience.**  ``_base.py`` and
``_runtime.py`` are HAND-WRITTEN: no run emits them, they are INPUTS to the compile
(``tests/compiled.py``'s key covers them for that reason), and ``src/`` is their source of
truth.  ``_schemas/``, ``constraints.py`` and ``envelopes.py`` are the run's OUTPUT.  So
``adcp.types.__path__`` gets the fresh directory in FRONT of ``src/adcp/types`` rather
than instead of it: the three generated entries resolve to this run's, the two
hand-written ones to the checkout's, and nothing is copied that a run produces.  The
fall-through can only reach a direct child of ``adcp.types``, and the three generated ones
are asserted present below -- once ``_schemas`` resolves fresh, its own ``__path__`` holds
the fresh directory alone, so no module BELOW it can come from ``src/``.

**THE WRITE IS SHARED ON DISK, like the compile and for the same measured reason.**  The
tree is ~840 MB, almost all of it the resolved JSON a document's ``strict_validate`` reads
through ``importlib.resources`` -- so ten xdist workers each writing their own copy would
be ~8 GB of transient disk and ten writes to answer one question, which is worse than the
staleness it replaces.  The directory is named by ``tests.compiled.digest`` -- the key the
COMPILE is held under, so it moves on the compiler's own source, the package modules the
compile reads, the bundle and the population -- and the first process to want it writes it
under an exclusive lock while the others wait.  A run that finds it present pays a
directory stat and no compile at all: the key is a digest over source bytes, not over the
compile's result, so the steady-state cost of this module is hashing ``codegen/``.

An entry is published by RENAMING a complete staging directory into place, so the named
path never exists half-written; a reader that finds it can import from it.
"""

from __future__ import annotations

import fcntl
import functools
import importlib
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

from compiled import CACHE_ROOT, compiled, digest

from codegen import bundle, emit, patch

REPO = Path(__file__).resolve().parents[1]

#: **The PUBLISHED 3.2 bundle, as the repository ships it and with no patch set applied.**
#:
#: Declared here because it is a BUNDLE and this module is where a bundle is declared, and
#: because the readers that legitimately want it are a real set rather than an oversight:
#: an addition is REFUSED where the node already states the keyword
#: (:func:`codegen.patch.additions`), so a check of the override table read against the
#: patched bundle would refuse every entry in it and call that the defect being gone.
#: ``tests/test_patch_8525.py``, ``tests/test_judgment_table.py`` and
#: ``tests/test_a_patch_set_reaches_the_tree.py`` are those readers.
#:
#: **IT IS NOT THE BUNDLE A RUN READS AND IS NOT A SPELLING OF ONE**
#: (``adcp-client-python-2mli``, ``adcp-client-python-fr4r``).  Measured: it is portable over
#: 1,054 documents against :data:`BUNDLE`'s 1,059, and the five only the patched one holds --
#: ``core/country-code.json``, ``core/currency-code.json``, ``core/domain-name.json``,
#: ``core/https-url.json``, ``core/idempotency-key.json`` -- are documents ``patches/8525``
#: ADDS.  A module that grades the fresh TREE while ranging over this name asks the tree for
#: a document this bundle does not contain, which is ``fr4r``'s ``KeyError``.
PUBLISHED = REPO / "schemas" / "cache" / "3.2"

#: **The bundle a run reads**: :data:`PUBLISHED` with every patch set the BUILD applies
#: (:data:`codegen.patch.BUILD`).  ``./check`` reads the same derivation, so the fast loop's
#: figures and the gate's range over ONE input -- which they did not before this line, when
#: the override table was applied in two test files and in no compile path.
BUNDLE = patch.for_build(PUBLISHED)

#: **The SECOND bundle the goal is verified against**, published and unpatched: the patch
#: sets are written against 3.2's documents and :func:`codegen.patch.additions` refuses a
#: row whose node already states the keyword, so there is no patched derivation of this one
#: to read.
#:
#: Declared HERE rather than spelled in the module that grades it, for
#: ``adcp-client-python-lzzj.11``'s reason: a test module naming a bundle path of its own is
#: a second bundle in a run whose tree came from the first, and 36 modules did that before
#: the sweep behind that row.  A reader that wants the other bundle takes it from this name.
SECOND = REPO / "schemas" / "cache" / "3.3"

#: The package set every reader of this tree needs to turn a document into a FILE.
#:
#: ``emit.module_file(document, packages)`` is the only reading that answers "which file
#: holds this document's module", and it needs the package set because a document whose
#: path is also a directory's is written to ``<path>/__init__.py``
#: (``docs/plan/architecture.md``, the layout rule beside ``write``, 2026-10-29).  Held
#: HERE, beside the tree the readers open, and as a constant rather than a call at each
#: site: ``bundle.package_roots`` is "a function of the BUNDLE and not of the run's
#: document set", so one value serves every reader and no reader can be handed a set
#: derived from its own population by accident.
PACKAGES = bundle.package_roots(BUNDLE)

#: Where a materialised tree is held between processes.  Beside the compile store and
#: gitignored for the same reason: it is derived, and a committed one would be a tree a
#: reader could edit into a result no compiler produced.
STORE = CACHE_ROOT / "fresh-tree"

#: How long a tree is kept after it was last asked for.
#:
#: A tree is ~840 MB and the key moves on every edit to ``codegen/``, so with no prune an
#: epic's worth of lanes fills the disk the compile store already holds 39 GB in.  The
#: margin is what makes the prune safe rather than the interval: ``pyproject.toml``'s own
#: measurement of this suite is a 55-minute full run, and a tree's mtime is refreshed
#: every time this module hands it out, so a tree in use is hours from eligible.  The
#: hazard being bounded is real and not hypothetical -- ``_base._document`` reads a
#: document's JSON LAZILY, so removing a tree a live worker still holds open would turn
#: into a validation error three files away rather than an ImportError at the start.
KEPT_SECONDS = 12 * 60 * 60

#: The generated children of ``adcp.types``, which this run writes and ``src/`` must not
#: be allowed to answer for.  ``emit.write`` puts the first under ``_schemas`` and the
#: others BESIDE it (``Emitted.beside``), and every one is asserted present in the
#: materialised directory: a missing one would fall through ``adcp.types.__path__`` to the
#: committed module, which is the mixture of two compilers this module exists to end.
#:
#: ``domains`` is v9.6's module layout as a COMPATIBILITY MIRROR of the fresh ``_schemas``
#: (``codegen/mirror``), and it is here for the rule's own reason rather than for the
#: mixture it could cause: the mirror resolves ``adcp.types._schemas.<rest>`` by NAME at
#: import time, so it follows whichever tree is bound and cannot mirror the committed one
#: while the rest of the grade reads the fresh one.  What a fall-through WOULD hide is the
#: artifact itself going stale, and that is what the entry closes.
GENERATED = ("_schemas", "constraints.py", "envelopes.py", "domains")

#: Why no fresh tree could be built, or ``""``.
#:
#: **A FINDING and not an exception**, because this module is imported by
#: ``tests/conftest.py`` and a raise there errors the COLLECTION of the whole suite --
#: which is the shape of defect this row exists to remove, arriving from the other side.
#: A compiler that does not run is reported by
#: ``tests/test_the_tree_imports.py::test_the_tree_the_suite_grades_is_one_a_fresh_run_wrote``
#: and by every test that asks for a compile, and the file whose collection used to go
#: down stays collectable.
FAILURE = ""


def population() -> list[str]:
    """The population the SHIPPED tree is emitted from: the bundle's portable set.

    ``tests/test_emit.py``'s ``tree_population`` and not its ``population``, which is the
    union of the seven step selectors and a PROPER PART of this.  The two were one
    function once and ``adcp-client-python-10l.73`` is what that cost: 47 of the tree's
    files were there because an earlier run reached their documents through a ``$ref``,
    so both sides of a byte compare were stale together.
    """
    return sorted(bundle.portable(BUNDLE))


def _prune(keep: str) -> None:
    """Remove every tree but ``keep`` that nothing has asked for in :data:`KEPT_SECONDS`.

    Best effort in every direction: a failure here can only cost disk, never a verdict,
    so it is swallowed exactly as ``tests/compiled.py`` swallows a cache write.
    """
    cutoff = time.time() - KEPT_SECONDS
    for path in STORE.iterdir():
        if path.name.startswith(keep) or path.name.startswith("staging."):
            continue
        try:
            if path.stat().st_mtime >= cutoff:
                continue
        except OSError:
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:  # a ``.lock`` or a ``.failed`` whose key nothing computes any more
            path.unlink(missing_ok=True)


#: How long a RAISE is remembered, so a compiler that does not run is reported once.
#:
#: **Measured, and it is why this exists at all.**  ``tests/compiled.py`` caches a result
#: and never a raise, so a compile that raises is uncached -- and with the materialisation
#: serialised by the lock below, the session process and all ten workers each paid the
#: whole failing compile in turn.  A perturbation that makes ``render.constraints_module``
#: raise ran past twenty minutes without reporting, for a defect ``./check`` states in one
#: compile.  So the raise is held under the SAME key as the result, which is a digest over
#: ``codegen/`` -- a compiler that raises under that key raises under it again, and fixing
#: the compiler moves the key, so there is nothing to invalidate by hand.
#:
#: The TTL is the one thing the key cannot answer for: a failure that is NOT a property of
#: the source -- an OOM kill, a disk full -- would otherwise be remembered for as long as
#: the lane did not edit the compiler.  Longer than a full suite run
#: (``pyproject.toml``'s measurement is 55 minutes) so one run reports one reason, and
#: short enough to clear itself without anyone being told about a file.
FAILED_SECONDS = 2 * 60 * 60


@functools.cache
def _materialised() -> Path:
    """``<store>/<digest>/types``: the generated half of ``adcp.types``, written once.

    Under an exclusive lock on the key, so the ten workers of one run do not each write
    840 MB to answer the same question -- the first writes and the rest stat.  The lock is
    the whole of the concurrency argument and the rename is the whole of the crash
    argument: a staging directory is written under a name no reader looks at and moved
    into place in one syscall, so the published path is complete or absent.

    A compile that RAISES is recorded beside the tree and re-raised by the siblings
    waiting on the lock, for :data:`FAILED_SECONDS`' measured reason.
    """
    key = digest(BUNDLE, population())
    held = STORE / key
    types = held / "types"
    failed = STORE / f"{key}.failed"
    STORE.mkdir(parents=True, exist_ok=True)
    with (STORE / f"{key}.lock").open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        if not types.is_dir():
            try:
                if time.time() - failed.stat().st_mtime < FAILED_SECONDS:
                    raise RuntimeError(f"this compiler already raised:\n{failed.read_text()}")
            except OSError:
                pass
            staging = STORE / f"staging.{key}.{os.getpid()}"
            shutil.rmtree(staging, ignore_errors=True)
            shutil.rmtree(held, ignore_errors=True)  # a previous write died before it
            try:
                emit.write(
                    compiled(BUNDLE, population()),
                    staging / "types" / "_schemas",
                    staging / "types",
                )
            except BaseException:
                try:
                    failed.write_text(traceback.format_exc())
                except OSError:
                    pass
                raise
            failed.unlink(missing_ok=True)
            os.rename(staging, held)
        for rel in GENERATED:
            assert (types / rel).exists(), (
                f"{rel} is generated and the materialised tree does not carry it; "
                "adcp.types would fall through to the committed one and the suite "
                "would grade a mixture of two compilers"
            )
        try:
            os.utime(held)
            _prune(keep=key)
        except OSError:
            pass
    return types


def _bound() -> Path:
    """Put the materialised generated half in front of ``src/adcp/types``, and say so.

    Called once, at this module's import, so that importing it IS the binding and no
    reader can be ordered before it.  ``tests/conftest.py`` imports it, which is what
    makes the binding happen before pytest collects a single test module -- a test module
    that imported ``adcp.types._schemas`` first would have bound the committed tree
    irrevocably, and the assertion below is what reports that rather than grading it.
    """
    global FAILURE
    import adcp.types

    try:
        types = _materialised()
    except BaseException:  # the failure is the finding, see FAILURE
        FAILURE = traceback.format_exc()
        # **NOT a fall-through to ``src/``, and this is the one decision here worth
        # arguing with.**  A compiler that did not run leaves the suite with no tree.
        # Letting the committed tree answer for it would keep the collection whole and
        # would make every check that imports a generated class directly -- and there are
        # a dozen -- pass against an artifact nothing produced, which is the mixture of
        # two compilers this module exists to end, in the one state where it is certain.
        #
        # THE COST, MEASURED, because it is not free either: the files that import a
        # generated module at MODULE scope (``test_accepts_corpus``, ``test_emit_product``,
        # ``test_envelope_base``) cannot be collected, and pytest
        # interrupts the run on a collection error, so a whole-suite invocation reports 554
        # of 3,435 collected instead of a failure count.  That is a stop-the-world state
        # with ``./check`` as its instrument and no tree for any check to range over -- it
        # is NOT the failure this row removed, which was ONE unimportable module of 1,054
        # taking a file's collection down, and which is measured green in
        # ``perturb_fresh_grading.sh``.  The directory is named for the reader who lands
        # on the ``ModuleNotFoundError``, because the path appears in it.
        types = STORE / "no-fresh-tree-the-compiler-raised-see-tests-fresh-FAILURE"

    generated = {f"adcp.types.{rel.removesuffix('.py')}" for rel in GENERATED}
    already = sorted(
        f"{name} <- {getattr(module, '__file__', None)}"
        for name, module in list(sys.modules.items())
        if (name in generated or any(name.startswith(f"{g}.") for g in generated))
        and not str(getattr(module, "__file__", "") or "").startswith(str(types))
    )
    assert not already, (
        f"the generated half of adcp.types is already bound outside the fresh tree "
        f"({already[0]}), so this process cannot be made to grade one; whatever "
        "imported it runs before tests/conftest.py"
    )

    if FAILURE:
        # The hand-written half is already resolved (``codegen`` imports ``_base`` and
        # ``_runtime`` before anything here runs, and this asserts that rather than
        # hoping), so dropping ``src/`` from the path can only make a GENERATED import
        # fail -- which is the outcome wanted.
        assert "adcp.types._base" in sys.modules and "adcp.types._runtime" in sys.modules
        adcp.types.__path__[:] = [str(types)]
    elif str(types) not in adcp.types.__path__:
        adcp.types.__path__.insert(0, str(types))
    importlib.invalidate_caches()
    return types


#: The directory holding the generated half: ``_schemas/`` and the two modules beside it.
PACKAGE = _bound()

#: **The tree every check reads.**  Named ``TREE`` because that is what the readers in
#: ``tests/`` already call it, so pointing them here is one line each and a reader of any
#: of them sees the same name mean the same thing.  ``emit.TREE`` stays what it is -- the
#: path the CLI writes the artifact to -- and ``tests/test_emit.py``'s
#: ``test_the_committed_tree_is_what_a_fresh_run_emits`` is the one check that reads it.
TREE = PACKAGE / "_schemas"


def schemas():
    """The fresh tree's package, or ``None`` if no fresh tree was built.

    The ``None`` is why this is a function and not an import: a caller running at
    PARAMETRIZE time cannot raise, because a raise there errors the file's collection
    instead of reddening a test -- and the file whose collection goes down is the one the
    obligation to report this lives in.  :data:`FAILURE` carries the reason and a named
    test reads it.
    """
    try:
        return importlib.import_module(emit.PACKAGE)
    except Exception:  # FAILURE and the named test carry the reason
        return None
