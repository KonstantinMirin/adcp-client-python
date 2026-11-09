"""One compile per population per process, shared by every test that asks for it.

**Why this exists, measured.**  62 call sites across 11 test files call
``emit.emit(BUNDLE, <a whole population>)``, and one such call is **97.4 s** over the
1,054 portable documents.  Uncached that is 6,039 s of CPU recompiling the same pinned
bundle, which after ``adcp-client-python-10l.51`` took the graded pass to 39.6 s was the
whole of a 22-minute warm run.  The bundle is pinned, the compiler is deterministic, and
the output is identical at all 62 sites; so it is compiled once and read 62 times.

**The key is the POPULATION and never nothing**, because there are three of them and they
do not agree:

================================================  =========  ================
population                                        documents  census
================================================  =========  ================
``sorted(bundle.portable(BUNDLE))``                   1,054  909 / 145
``tests.populations.population()``                      991  a different one
``sorted(bundle.portable(fresh.SECOND))``             1,138  bundle 3.3's own
================================================  =========  ================

A cache keyed on the bundle alone would hand one denominator's result to a caller asking
for the other, silently, and every figure downstream would be wrong by 63 documents.  So
the key carries the population as a tuple, and :func:`compiled` is the only way in.

The first figure is read against the PUBLISHED 3.2 bundle and ``BUNDLE`` is the patched
one, where ``bundle.portable`` answers 1,059; that staleness is
``adcp-client-python-82m.33``'s and is left where its owner can see it.  The third row is
the SECOND BUNDLE (``tests/fresh.py``'s ``SECOND``), whose one reader is
``tests/test_the_second_bundle.py``: **72.0 s cold over its 1,138 portable documents**,
measured on this box, and a stat warm.

**Two layers, because one process is not the unit.**  ``functools.cache`` does not cross
a process, so in-process alone every one of the ten xdist workers pays the compile for
every population it touches -- measured at 280 s each on a loaded box, over the two
populations live when that was measured, so about 9 minutes of wall clock.  So there is a
second layer on disk and the first worker to want a population compiles it for all of them.

**THE DISK KEY COVERS THE COMPILER'S OWN SOURCE, and that is the whole correctness
argument.**  The output is a function of three things -- the bundle, the population, and
``codegen/`` itself -- and the third is the one a cache gets wrong.  A key over the bundle
alone would serve yesterday's compile to a lane that just edited ``lower/union.py``, and
every figure it then reported would describe code it did not run.  So the key is a digest
over the bundle's bytes, the population's members, and **every ``.py`` under
``codegen/``** -- edit one line of the compiler and the key moves, so there is nothing to
invalidate by hand and nothing to remember.

An entry is written atomically (temp file, then ``os.replace``) because ten workers race
for the same key, and a half-written pickle read by a sibling would be a corrupt
:class:`Emitted` rather than a miss.  A read that fails for any reason falls through to
compiling, so the cache can only cost time, never correctness.

**THE KEY NAMES THE BUNDLE AND NOT THE CALLER'S SPELLING OF IT**, which is
``adcp-client-python-q3a``'s first finding and cost one copy of an 842 MB answer per
spelling: the path went into the key as the caller wrote it, and the two entry points write
it differently.  :func:`_bundle_name` is the normalisation and carries the measurement.

**AND AN ENTRY NOTHING HAS ASKED FOR IS DROPPED BY THE NEXT RUN THAT ASKS**, which is the
same row's second finding and the reason the first one was expensive rather than merely
untidy: an entry is permanent, so the store grew by 842 MB per (compiler revision x
spelling x population) until a human removed 98 entries of 103 by hand.
:data:`KEPT_SECONDS` states the rule and :func:`_prune` is the act; both are safe for
exactly the reason above -- the worst a missing entry can do is cost a compile.

``adcp-client-python-10l.51``'s finding is the warning this follows.  ``graded_reports()``
was already ``functools.cache``d and its docstring claimed the cache made its pole one
pass instead of three -- but three of its four readers landed on different workers and
each paid in full.  A cache's SCOPE has to be checked against how the suite distributes.
Here it is: every caller of this function compiles at most once per worker, and the
suite's ``--dist=loadgroup`` does not change that.

**Nothing mutates the result**, checked over all 62 sites before this landed: every use
is a read.  An :class:`Emitted` is a dataclass of dicts, so a mutating caller would
corrupt every later reader in its process -- :func:`compiled` is therefore documented as
returning a SHARED value, and a test that needs to mutate one must call
``emit.emit`` directly and say why.
"""

from __future__ import annotations

import functools
import hashlib
import os
import pickle
import time
from collections.abc import Iterable
from pathlib import Path

from codegen import emit

#: This checkout, which the bundle is named RELATIVE TO in the key (:func:`_bundle_name`).
REPO = Path(__file__).resolve().parents[1]

#: Where a compile is held between processes.  Gitignored: it is derived, and a committed
#: one would be a file a reader could edit into a result no compiler produced.
#:
#: **SHARED ACROSS WORKTREES**, for ``tests/corpus.py``'s reason and with its safety: the
#: key is a digest of every ``.py`` under ``codegen/`` plus the bundle and the population,
#: so two checkouts holding the same compiler compute the same key and the same bytes, and
#: a checkout that does not never collides.  Held per worktree it cost ~9 GB across nine
#: stores to answer questions several of them shared -- a lane sitting at trunk's base pays
#: a 180 s cold compile for a result trunk computed an hour earlier.  ``ADCP_CACHE``
#: overrides the location; the default is beside the checkouts rather than inside one.
CACHE_ROOT = Path(os.environ.get("ADCP_CACHE") or Path(__file__).resolve().parents[2] / ".adcp-cache")

STORE = CACHE_ROOT / "emit-cache"


#: The modules of the emitted PACKAGE that the compiler reads as a consumer reads them,
#: and which are therefore inputs to the compile exactly as ``codegen/`` is.
#:
#: **Named, and not a glob over ``src/adcp/``**: ``src/adcp/types/_schemas/`` is the
#: compile's OUTPUT, so a glob would key each entry on the previous run's result and no
#: entry would ever be hit again.  These two are hand-written and are the whole of what
#: ``codegen`` imports from the package -- ``_base`` for ``applied_schema``,
#: ``SchemaRef`` and the approximation kinds, ``_runtime`` for the rule dataclasses.
_PACKAGE_INPUTS = ("src/adcp/types/_base.py", "src/adcp/types/_runtime.py")

#: **THE COMMITTED ARTIFACTS THE COMPILE READS, which a glob over ``*.py`` cannot see.**
#: ``codegen/published.json`` is upstream's published structures -- the other side of
#: ``codegen.structure``'s join, and therefore an input the emitted text is a function of:
#: regenerate the index against a different revision and every module that binds one of
#: those words changes bytes.  Without it in the key a lane that rebuilds the index alone is
#: served the previous compile, which is the same defect ``_PACKAGE_INPUTS`` exists for, one
#: file type further out.
_DATA_INPUTS = ("codegen/published.json",)


@functools.cache
def _compiler_digest() -> str:
    """A digest over every ``.py`` of ``codegen/`` and the package modules it READS, so
    an edit to anything the output is a function of moves the key.

    Sorted by path, with the path in the digest beside the bytes, so adding an empty
    module changes the answer and renaming one does too.  Cached per process because the
    source cannot change under a running interpreter that has already imported it.

    **:data:`_PACKAGE_INPUTS` is here because the compile READS them and the module
    docstring's own correctness argument reaches them.**  That argument is "the output is
    a function of three things -- the bundle, the population, and ``codegen/`` itself --
    and the third is the one a cache gets wrong"; it is a function of a fourth, because
    ``bundle.constrained_to_object`` is ``_base.applied_schema`` and ``lower.rules``
    lowers to ``_runtime``'s dataclasses.  Without them a lane that edits
    ``applied_schema`` alone is served the previous compile and every figure it reports
    describes code it did not run -- the exact defect this key exists to prevent, one
    package boundary further out.
    """
    paths = [
        *sorted((REPO / "codegen").rglob("*.py")),
        *(REPO / p for p in _PACKAGE_INPUTS),
        *(REPO / p for p in _DATA_INPUTS),
    ]
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(REPO).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _bundle_name(bundle: str) -> str:
    """The bundle in the key: its path RELATIVE TO THIS CHECKOUT, in posix form.

    **Measured at ``adcp-client-python-q3a``, where one bundle was held under two keys and
    two 842 MB pickles.**  The path went into the key as the CALLER SPELLED IT, and the two
    entry points spell it differently -- ``./check`` has ``Path("schemas/cache/3.2")`` and
    every module under ``tests/`` has ``REPO / "schemas" / "cache" / "3.2"`` -- so at trunk
    ``3f757728`` one population of 1,054 documents and one compiler gave
    ``fc2222b39088cb00...`` relative and ``b7e473ca16f94ddc...`` absolute.  The store held
    the relative one, so a lane that warmed it with the fast loop had not warmed the entry
    the gate reads: ``./check`` and the suite did not share the compile they are documented
    to share, and each spelling cost its own permanent 842 MB.

    **Relative to the checkout and not merely absolute**, which is the half the two
    spellings hide.  The store is SHARED ACROSS WORKTREES on the strength of the key being
    a function of the compiler's bytes (:data:`CACHE_ROOT`) -- and an absolute bundle path
    makes it a function of the directory a lane happened to clone into as well, so two
    worktrees holding the same compiler computed two keys and wrote the same answer twice.
    Named relative, they compute one, and that claim of :data:`CACHE_ROOT`'s becomes true.

    **Over the PATH and never over the bundle's CONTENT**, which was the tempting repair
    and is the expensive one: the population is already in the key, and a digest over 836
    MB of resolved JSON would be paid on every lookup to answer what the path answers for
    free.

    A bundle OUTSIDE this checkout keeps its resolved absolute path.  It is a different
    bundle, there is nothing to name it relative to, and a key that collided with the
    checkout's own would be the one failure this module may not have.
    """
    resolved = Path(bundle).resolve()
    try:
        return resolved.relative_to(REPO).as_posix()
    except ValueError:
        return resolved.as_posix()


def _key(bundle: str, population: tuple[str, ...]) -> str:
    h = hashlib.sha256()
    h.update(_compiler_digest().encode())
    h.update(_bundle_name(bundle).encode())
    for document in population:
        h.update(b"\x00")
        h.update(document.encode())
    return h.hexdigest()


def digest(bundle: Path, population: Iterable[str]) -> str:
    """The key a compile is held under, for a caller holding a DERIVED ARTIFACT of one.

    ``tests/fresh.py`` writes the emitted tree to disk and has to name the directory it
    holds it in.  That name must move on exactly what the compile moves on -- the
    compiler's own source, the package modules the compile reads, the bundle and the
    population -- or a tree one compiler wrote is handed to a lane running another, which
    is the staleness this whole module exists to make impossible one layer down.  So the
    name is THIS function's key rather than a second derivation that could disagree with
    it.
    """
    return _key(str(bundle), tuple(population))


#: How long an entry is kept after the last time a run ASKED FOR IT.
#:
#: **The retention is over the entry's mtime, and the mtime is refreshed on every ask**
#: (:func:`_asked_for`), so it reads "when a lane last wanted this compile" and not "when
#: this compiler revision was built".  That is the rule, and it is the one rule here: an
#: entry nothing has asked for in twelve hours is a compiler revision no checkout holds any
#: more, and it goes.  Nothing else is consulted -- not the number of entries, not the free
#: space, not which revision is trunk -- because every one of those needs a reader to agree
#: about what the right answer is, and this one does not.
#:
#: **Twelve hours, which is ``tests/fresh.py``'s figure for the store beside this one**, and
#: for its reason: ``pyproject.toml``'s own measurement of this suite is a 55-minute full
#: run, so an entry a live run is reading was asked for inside the last hour and is eleven
#: hours from eligible.  The margin is the first half of the safety argument.
#:
#: **The second half is that a lost race costs a compile and never a verdict**, which is
#: the module docstring's property and the whole reason a prune is allowed here at all.  A
#: reader is one ``read_bytes()`` of a complete pickle: an unlink after it opens the file
#: leaves the inode alive until it closes, and an unlink before it opens is ``ENOENT`` --
#: which :func:`_compiled` already treats as a miss, exactly as it treats a pickle from
#: another Python.  So the worst this rule can do to a concurrent worker is 280 s, and
#: there is no third outcome in which it hands anybody a different answer.
#:
#: **Measured, and it is why this exists.**  With no prune the store reached 103 entries of
#: 842,068,270 bytes -- 55 GB on a root filesystem at 96% with 81 GB free -- of which 98 had
#: been neither written nor read in eight hours.  Removing those 98 by hand freed 50.2 GB
#: and took the disk to 93%.  A store whose bound is whoever notices is not bounded.
KEPT_SECONDS = 12 * 60 * 60


def _prune(store: Path, keep: str) -> None:
    """Drop every entry of ``store`` that nothing has asked for in :data:`KEPT_SECONDS`.

    ``keep``'s own entry is never dropped, whatever its mtime: the ask that triggers a
    prune may not be the ask the prune cuts off.  The EXEMPTION IS THE ENTRY AND NOT THE
    KEY, which is a distinction the store was already paying for: measured at
    ``adcp-client-python-q3a`` it held an abandoned ``<key>.<pid>.tmp`` of 842,068,270 bytes
    under the LIVE key, which a rule exempting that whole prefix would never remove.  A
    staging file therefore goes by mtime like anything else, and that cannot reach a LIVE
    writer's: writing 842 MB advances the file's mtime as it goes, so a staging file in
    flight is seconds old and not twelve hours.

    Best effort in every direction, like the cache write above: a failure here can only
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


def _asked_for(held: Path, key: str) -> None:
    """Record that ``key`` was wanted now, and drop what nothing has wanted since.

    Called on the hit and on the miss, so the rule runs wherever the store is touched and
    there is nothing for a lane to remember to run -- which is the half
    ``tests/fresh.py``'s store had and this one did not.  ``tests/test_the_compile_store.py``
    grades the rule and this wiring separately.
    """
    try:
        os.utime(held)
    except OSError:
        pass
    try:
        _prune(STORE, keep=key)
    except OSError:
        pass


@functools.cache
def _compiled(bundle: str, population: tuple[str, ...]) -> emit.Emitted:
    """The one compile, keyed by the compiler's source, the bundle and the population.

    The population is a tuple because a list is unhashable, and it is NOT sorted here:
    ``emit.emit`` reads it in order, so sorting would make this function answer a
    question its caller did not ask.  Two callers passing the same documents in
    different orders get two entries, which is correct and costs one extra compile in a
    population nobody passes twice.

    **Every failure path falls through to compiling.**  A missing entry, an unreadable
    one, a pickle from another Python, a race -- each is a miss, never an error and never
    a silently different answer.  That is what makes the disk layer unable to affect a
    verdict: the worst it can do is cost 280 s.
    """
    key = _key(bundle, population)
    held = STORE / f"{key}.pickle"
    try:
        out = pickle.loads(held.read_bytes())
    except Exception:
        pass
    else:
        _asked_for(held, key)
        return out
    out = emit.emit(Path(bundle), list(population))
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        staged = held.with_suffix(f".{os.getpid()}.tmp")
        staged.write_bytes(pickle.dumps(out, protocol=pickle.HIGHEST_PROTOCOL))
        os.replace(staged, held)
    except Exception:
        pass
    _asked_for(held, key)
    return out


def compiled(bundle: Path, population: Iterable[str]) -> emit.Emitted:
    """``emit.emit(bundle, population)``, compiled once per process.

    The returned value is SHARED with every other caller in this process.  Read it; do
    not mutate it.
    """
    return _compiled(str(bundle), tuple(population))
