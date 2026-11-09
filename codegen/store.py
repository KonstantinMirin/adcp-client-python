"""Where a BUNDLE-WIDE answer is held between processes, keyed on what it is a function of.

**Why this exists, measured.**  §1's domain-scope collision rule is two passes
(``docs/plan/rebuild-plan.md`` §9), and pass one ranges over the DOMAIN's documents rather
than the run's.  The design is right and §9 rules on it; the price is that a run naming one
document pays a walk over every domain its closure touches, and nearly every domain reaches
``core``.  Measured on ``4eff4354`` over ``schemas/cache/3.2``: a one-document run of
``compliance/comply-test-controller-request.json`` -- a four-document domain -- cost
**144.1 s**, of which **34.5 s** is the closure walk the run owes anyway and the rest is
pass one, paid three times over by §4's repetition.  ``registries/v1-canonical-mapping.json``
is one document whose own walk is **0.61 s** and cost **112.1 s**.  A whole-population cold
``./check`` went from 130.4 s to **353.2 s**.

**§9 names the answer and this module is it**: "the export symbols are a function of the
bundle, so they key on the bundle's content exactly as ``tests/compiled.py`` keys a compile.
A miss costs the walk, a hit costs nothing, and a content address cannot go stale -- which
is why this is not the second derived artifact the corpus argument was about."

``tests/compiled.py`` holds the same two layers over a whole compile and argues its own
correctness; **this module cannot reuse it, because ``codegen`` may not import ``tests``**
(``tests/test_import_rule.py`` holds the direction).  So the argument is copied here along
with the two specifics that matter, and both are copied rather than restated loosely:

**1. THE KEY COVERS THE COMPILER'S OWN SOURCE, and that is the whole correctness
argument.**  The answer is a function of three things -- the bundle, the set asked for, and
``codegen/`` itself -- and the third is the one a cache gets wrong.  A key over the bundle
alone would serve yesterday's census to a lane that just edited ``lower/names.py``, and
every name it then exported would describe code it did not run.  So the key is a digest over
**every ``.py`` under ``codegen/``**, the package modules the walk reads, the bundle's name
and the members of the set asked for -- edit one line of the compiler and the key moves, so
there is nothing to invalidate by hand and nothing to remember.

**2. EVERY FAILURE PATH FALLS THROUGH TO COMPUTING.**  A missing entry, an unreadable one, a
pickle from another Python, a race, a store on a full disk -- each is a MISS, never an error
and never a silently different answer.  That property is what makes this store unable to
affect a verdict: the worst it can do is cost the walk it was there to save.  Nothing here
raises and nothing here returns a default; :func:`held` either hands back a value it
unpickled or the value ``compute()`` returned.

**AND AN ENTRY NOTHING HAS ASKED FOR IS DROPPED BY THE NEXT RUN THAT ASKS.**  The compile
store beside this one reached 103 entries of 842,068,270 bytes -- 55 GB on a root filesystem
at 96% -- because nothing pruned it, and 50.2 GB of that was removed by hand.  A retention
rule a human runs is the same amount of disk as no rule, so the rule runs on the ask:
:data:`KEPT_SECONDS` states it and :func:`_prune` is the act, called from :func:`_asked_for`
on the hit and on the miss alike.

**ONE STORE HOLDS ONE KIND OF ANSWER.**  :data:`STORE` is named for what it holds, because
the key is a digest of (compiler, bundle, set) and says nothing about WHICH question was
asked of them -- two kinds of answer under one directory would collide on one key and each
would be handed the other's pickle.  A second kind of answer gets a second directory and a
second constant, which is one line and cannot be got wrong by accident.
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import os
import pickle
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

#: This checkout, which the bundle is named RELATIVE TO in the key (:func:`_bundle_name`).
REPO = Path(__file__).resolve().parents[1]

#: Where an answer is held between processes.  Gitignored and **SHARED ACROSS WORKTREES**,
#: for ``tests/compiled.py``'s measured reason and with its safety: the key is a digest of
#: every ``.py`` under ``codegen/`` plus the bundle and the set asked for, so two checkouts
#: holding the same compiler compute the same key and the same bytes, and a checkout that
#: does not never collides.  ``ADCP_CACHE`` overrides the location -- the same variable the
#: compile store reads, so a lane points both at one directory with one name -- and the
#: default is beside the checkouts rather than inside one.
CACHE_ROOT = Path(os.environ.get("ADCP_CACHE") or Path(__file__).resolve().parents[2] / ".adcp-cache")

#: Pass one of §1's domain-scope collision rule, per (compiler, bundle, domain set).  Named
#: for the answer it holds, which is the module docstring's one-kind-per-store rule.
STORE = CACHE_ROOT / "domain-exports"

#: The modules of the emitted PACKAGE the walk reads as a consumer reads them, and which are
#: therefore inputs to it exactly as ``codegen/`` is.
#:
#: **Named, and not a glob over ``src/adcp/``**: ``src/adcp/types/_schemas/`` is the walk's
#: OUTPUT, so a glob would key each entry on the previous run's result and no entry would
#: ever be hit again.  These two are hand-written and are the whole of what ``codegen``
#: imports from the package -- ``_base`` for ``applied_schema``, ``SchemaRef`` and the
#: approximation kinds, ``_runtime`` for the rule dataclasses.  ``tests/compiled.py`` keys a
#: compile on them for the same reason and with the same list; a name is in both or the two
#: stores disagree about what an answer is a function of.
_PACKAGE_INPUTS = ("src/adcp/types/_base.py", "src/adcp/types/_runtime.py")


@functools.cache
def compiler_digest() -> str:
    """A digest over every ``.py`` of ``codegen/`` and the package modules it READS, so an
    edit to anything an answer is a function of moves the key.

    Sorted by path, with the path in the digest beside the bytes, so adding an empty module
    changes the answer and renaming one does too.  Cached per process because the source
    cannot change under a running interpreter that has already imported it.

    **A RUNTIME perturbation moves nothing here, and that is what :func:`perturbed` is
    for.**  ``mock.patch`` and a bare attribute assignment both change what the walk does
    without changing a byte of source, so a process that has done either is no longer
    described by this digest and must not touch the store at all.
    """
    paths = [*sorted((REPO / "codegen").rglob("*.py")), *(REPO / p for p in _PACKAGE_INPUTS)]
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(REPO).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _bundle_name(bundle: Path) -> str:
    """The bundle in the key: its path RELATIVE TO THIS CHECKOUT, in posix form.

    **The spelling and not the caller's spelling of it**, which is
    ``adcp-client-python-q3a``'s finding on the compile store and cost one copy of an 842 MB
    answer per spelling: the path went into the key as the caller wrote it, and the entry
    points spell it differently -- ``./check`` has ``Path("schemas/cache/3.2")`` and every
    module under ``tests/`` has ``REPO / "schemas" / "cache" / "3.2"``.  Relative to the
    checkout and not merely absolute, because the store is shared across worktrees: an
    absolute path makes the key a function of the directory a lane happened to clone into,
    so two worktrees holding one compiler would compute two keys and write one answer twice.

    Over the PATH and never over the bundle's CONTENT, which is the tempting repair and the
    expensive one: the set asked for is already in the key, and a digest over 836 MB of
    resolved JSON would be paid on every lookup to answer what the path answers for free.
    A bundle OUTSIDE this checkout keeps its resolved absolute path -- it is a different
    bundle and there is nothing to name it relative to.
    """
    resolved = Path(bundle).resolve()
    try:
        return resolved.relative_to(REPO).as_posix()
    except ValueError:
        return resolved.as_posix()


def key(bundle: Path, over: Iterable[str]) -> str:
    """The key an answer about ``bundle`` and ``over`` is held under.

    Public because a reader of the store has to be able to name an entry without inferring
    it from what is left in the directory -- which is how
    ``tests/test_the_compile_store.py`` grades the compile store's own wiring, and how the
    wiring of this one is graded.
    """
    h = hashlib.sha256()
    h.update(compiler_digest().encode())
    h.update(_bundle_name(bundle).encode())
    for member in over:
        h.update(b"\x00")
        h.update(member.encode())
    return h.hexdigest()


#: How long an entry is kept after the last time a run ASKED FOR IT.
#:
#: **The retention is over the entry's mtime, and the mtime is refreshed on every ask**
#: (:func:`_asked_for`), so it reads "when a lane last wanted this answer" and not "when
#: this compiler revision was built".  That is the rule, and it is the one rule here: an
#: entry nothing has asked for in twelve hours is a compiler revision no checkout holds any
#: more, and it goes.  Nothing else is consulted -- not the number of entries, not the free
#: space, not which revision is trunk -- because every one of those needs a reader to agree
#: about what the right answer is, and this one does not.
#:
#: **Twelve hours, which is ``tests/compiled.py``'s and ``tests/fresh.py``'s figure for the
#: two stores beside this one**, and for their reason: ``pyproject.toml``'s own measurement
#: of this suite is a 55-minute full run, so an entry a live run is reading was asked for
#: inside the last hour and is eleven hours from eligible.  The margin is the first half of
#: the safety argument.
#:
#: **The second half is that a lost race costs a walk and never a verdict**, which is the
#: module docstring's second property and the whole reason a prune is allowed here at all.
#: A reader is one ``read_bytes()`` of a complete pickle: an unlink after it opens the file
#: leaves the inode alive until it closes, and an unlink before it opens is ``ENOENT`` --
#: which :func:`held` already treats as a miss, exactly as it treats a pickle from another
#: Python.  So the worst this rule can do to a concurrent worker is the walk, and there is
#: no third outcome in which it hands anybody a different answer.
KEPT_SECONDS = 12 * 60 * 60


def _prune(store: Path, keep: str) -> None:
    """Drop every entry of ``store`` that nothing has asked for in :data:`KEPT_SECONDS`.

    ``keep``'s own entry is never dropped, whatever its mtime: the ask that triggers a prune
    may not be the ask the prune cuts off.  The EXEMPTION IS THE ENTRY AND NOT THE KEY,
    which is a distinction the compile store was already paying for -- it held an abandoned
    ``<key>.<pid>.tmp`` of 842,068,270 bytes under the LIVE key, which a rule exempting that
    whole prefix would never remove.  A staging file therefore goes by mtime like anything
    else, and that cannot reach a LIVE writer's: writing advances the file's mtime as it
    goes, so a staging file in flight is seconds old and not twelve hours.

    Best effort in every direction, like the write in :func:`held`: a failure here can only
    cost disk.
    """
    cutoff = time.time() - KEPT_SECONDS
    for path in store.iterdir():
        if path.name == f"{keep}.pickle":
            continue
        try:
            if path.stat().st_mtime >= cutoff:
                continue
            path.unlink()
        except OSError:
            continue


def _asked_for(entry: Path, held_under: str) -> None:
    """Record that ``held_under`` was wanted now, and drop what nothing has wanted since.

    Called on the hit and on the miss, so the rule runs wherever the store is touched and
    there is nothing for a lane to remember to run -- which is the half the compile store
    did not have when it reached 55 GB.
    """
    try:
        os.utime(entry)
    except OSError:
        pass
    try:
        _prune(STORE, keep=held_under)
    except OSError:
        pass


#: Whether this process's answers are still a function of the compiler's SOURCE, which is
#: what :func:`compiler_digest` -- and therefore the key -- is a digest of.  Read by
#: :func:`held` and moved only by :func:`perturbed`.
_A_FUNCTION_OF_THE_SOURCE = True


@contextlib.contextmanager
def perturbed() -> Iterator[None]:
    """For a caller that has changed a module of the walk at RUN TIME: inside this block the
    store is neither read nor written.

    **This is ``tests/test_no_cached_compile_under_a_perturbation.py``'s rule arriving one
    layer down, and it is the one hazard this store adds that the key cannot answer for.**
    That rule is "a test that perturbs the compiler calls ``emit.emit`` directly, because
    ``tests/compiled.py``'s key is a digest of ``codegen/``'s source and a runtime patch does
    not move it".  A store behind ``emit.emit`` itself makes calling it directly insufficient,
    in both directions and both of them measured on the suite as it stands:

    * a spy or a tracer DELEGATES, so the answer is unchanged -- but a hit means pass one
      never runs, and the comment at four of the five sites says in as many words that "the
      walk has to RUN";
    * a perturbation that changes BEHAVIOUR -- ``keywords.TABLE`` without a row,
      ``lower.composition.lower_composition`` without its root arm -- computes a census under a
      compiler no source describes and, on a miss, WRITES it under the honest key.  Every
      later run of that key would then export names a compiler nobody runs derived, which is
      exactly the staleness the key exists to make impossible.

    So a perturbing caller says so, and the store stays a function of the source.  The flag
    is restored in a ``finally``: a raise inside the block is the perturbation's own
    business and must not leave the store switched off for the rest of the process.
    """
    global _A_FUNCTION_OF_THE_SOURCE
    before = _A_FUNCTION_OF_THE_SOURCE
    _A_FUNCTION_OF_THE_SOURCE = False
    try:
        yield
    finally:
        _A_FUNCTION_OF_THE_SOURCE = before


def held(bundle: Path, over: Iterable[str], compute: Callable[[], T]) -> T:
    """``compute()``, held on disk under a content address of (the compiler, ``bundle``,
    ``over``).

    ``over`` is the SET ASKED FOR, as an iterable of strings read in the order given: the
    caller's own ordering is in the key, so two callers asking in two orders get two entries
    rather than one of them being handed an answer to a question it did not ask.  A caller
    whose answer does not depend on the order sorts before it calls.

    **Every failure path falls through to ``compute()``** -- the module docstring's second
    property, and the reason this returns a value and raises nothing.  The write is atomic
    (temp file, then ``os.replace``) because runs are parallel and two workers race for one
    key; two racers compute the same bytes, so the loser costs a rename and changes nothing.
    A half-written pickle read by a sibling would be a corrupt answer rather than a miss,
    which is the one outcome the rename makes unrepresentable.
    """
    if not _A_FUNCTION_OF_THE_SOURCE:
        return compute()
    held_under = key(bundle, over)
    entry = STORE / f"{held_under}.pickle"
    try:
        out = pickle.loads(entry.read_bytes())
    except Exception:
        pass
    else:
        _asked_for(entry, held_under)
        return out
    out = compute()
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        staged = entry.with_suffix(f".{os.getpid()}.tmp")
        staged.write_bytes(pickle.dumps(out, protocol=pickle.HIGHEST_PROTOCOL))
        os.replace(staged, entry)
    except Exception:
        pass
    _asked_for(entry, held_under)
    return out
