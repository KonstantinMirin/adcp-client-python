"""One compile per population per process, shared by every test that asks for it.

**Why this exists, measured.**  62 call sites across 11 test files call
``emit.emit(BUNDLE, <a whole population>)``, and one such call is **97.4 s** over the
1,054 portable documents.  Uncached that is 6,039 s of CPU recompiling the same pinned
bundle, which after ``adcp-client-python-10l.51`` took the graded pass to 39.6 s was the
whole of a 22-minute warm run.  The bundle is pinned, the compiler is deterministic, and
the output is identical at all 62 sites; so it is compiled once and read 62 times.

**The key is the POPULATION and never nothing**, because there are two of them and they
do not agree:

================================================  =========  ================
population                                        documents  census
================================================  =========  ================
``sorted(bundle.portable(BUNDLE))``                   1,054  909 / 145
``tests.populations.population()``                      991  a different one
================================================  =========  ================

A cache keyed on the bundle alone would hand one denominator's result to a caller asking
for the other, silently, and every figure downstream would be wrong by 63 documents.  So
the key carries the population as a tuple, and :func:`compiled` is the only way in.

**Two layers, because one process is not the unit.**  ``functools.cache`` does not cross
a process, so in-process alone every one of the ten xdist workers pays the compile for
every population it touches -- measured at 280 s each on a loaded box, two populations, so
about 9 minutes of wall clock.  So there is a second layer on disk and the first worker to
want a population compiles it for all of them.

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
from collections.abc import Iterable
from pathlib import Path

from codegen import emit

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
    root = Path(__file__).resolve().parent.parent
    paths = [*sorted((root / "codegen").rglob("*.py")), *(root / p for p in _PACKAGE_INPUTS)]
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(root).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _key(bundle: str, population: tuple[str, ...]) -> str:
    h = hashlib.sha256()
    h.update(_compiler_digest().encode())
    h.update(bundle.encode())
    for document in population:
        h.update(b"\x00")
        h.update(document.encode())
    return h.hexdigest()


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
    held = STORE / f"{_key(bundle, population)}.pickle"
    try:
        return pickle.loads(held.read_bytes())
    except Exception:
        pass
    out = emit.emit(Path(bundle), list(population))
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        staged = held.with_suffix(f".{os.getpid()}.tmp")
        staged.write_bytes(pickle.dumps(out, protocol=pickle.HIGHEST_PROTOCOL))
        os.replace(staged, held)
    except Exception:
        pass
    return out


def compiled(bundle: Path, population: Iterable[str]) -> emit.Emitted:
    """``emit.emit(bundle, population)``, compiled once per process.

    The returned value is SHARED with every other caller in this process.  Read it; do
    not mutate it.
    """
    return _compiled(str(bundle), tuple(population))
