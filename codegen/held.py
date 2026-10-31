"""Where a drawn instance is HELD between runs: the store, and nothing about a path.

**Why this module exists and is not ``codegen/harness.py``.**  ``docs/plan/architecture.md``
§9 divides the two: "the verifier grades an emitted class against the document it names,
and it does so without reading the walk" -- its import set is ``jsonschema``,
``hypothesis``, ``hypothesis_jsonschema``, ``pydantic`` and the five ``codegen`` modules §9
names, and nothing about a directory layout is among them.  A cache that opened a file from
inside ``harness`` would be the hole, because what makes that module able to grade output
that does not exist yet is that it reads nothing but its arguments.  So ``harness``
computes the key (``harness.corpus_key``) and this module opens the file, and the seam
between them is two methods: ``get(key)`` and ``put(key, instances)``.

**Why it is not ``tests/corpus.py`` either, which is where this code was.**  There are now
TWO callers that need a store and they are on opposite sides of the suite boundary: the
suite's grading pass, and ``codegen/__main__.py``, which grades the tree the run just wrote
so that the run can write §10's per-pair verdict table.  A store the run cannot import is a
run that grades every pair cold -- 2,015.6 s over the population where a warm pass is 39.6
s -- so ``python -m codegen`` would either take hours or write a table with no verdicts in
it.  ``tests/corpus.py`` imports every name from here and keeps the paragraphs that are
about the SUITE's use of it; this module is the mechanism and the two directories, and it
is in ``codegen/`` because the RUN is one of its readers.

**The paths are HERE and the floor's is inside ``tests/`` all the same**, which looks
backwards and is not.  The floor is a committed artifact OF THE REPOSITORY and the run is a
reader of it; its directory is under ``tests/`` because the population it answers for is
the suite's, and a repository path is already something ``codegen/__main__.py`` states --
``codegen.emit.TREE`` is ``src/adcp/types/_schemas``.  What would be backwards is the
verifier knowing either one, and it knows neither.

``codegen.harness`` does not import this module and must not; nothing here imports
``codegen.harness``.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

#: The repository root, reached the way ``tests/test_import_rule.py`` reaches it.
ROOT = Path(__file__).resolve().parents[1]

#: **THE CROSS-WORKTREE CACHE.  It is a build artifact; :data:`COMMITTED` is the floor it
#: starts from, and that split is this row's whole change** (``adcp-client-python-3be.22``).
#:
#: What stood here was the argument AGAINST committing the corpus, and it was sound when it
#: was written: *"a committed corpus is a second derived artifact whose currency has no
#: instrument.  A stale entry here is silently correct -- its key stops matching, the pair
#: draws, and nothing reddens -- so 'the committed corpus is up to date' would be an
#: obligation nothing grades, and the gate for it would have to redden on any in-flight
#: record change, which is correct work."*
#:
#: **The last clause is the load-bearing one and it is now false.**  The key hashed
#: ``bundle.record`` -- this package's own inlining -- so any compiler edit invalidated
#: every entry: a committed corpus would have been permanently stale behind a permanently
#: red gate, and the gate would have been reddening on in-flight work rather than on a
#: changed question.  ``harness.corpus_key``'s argument is now ``bundle.source_identities``
#: -- the document's own raw bytes, the raw bytes of its reference closure, the example
#: count, the format strategies and the generator version.  **A compiler edit moves no
#: key.  Only a bundle bump or a generator bump does**, and each of those is a deliberate,
#: reviewable event with a redraw attached.  So the obligation that had no instrument has
#: one: ``test_every_graded_pair_has_a_committed_entry_under_the_current_key``.
#:
#: And the size was never the obstacle.  Re-measured 2026-10-30 over the whole graded
#: population at ``accepts_examples=1``: the reading is ``Store.bytes_held`` over
#: ``Store.entries``, and it is **0.4 MB of content at a mean of 131 bytes an entry** -- a
#: ``du -sh`` of the same directory reads 15 MB, which is block overhead on thousands of
#: tiny files and not content.  A drawn instance is nothing like the record it came from:
#: ``media-buy/get-media-buy-delivery-response.json#`` is 5.19 MB of record and its
#: instance is 882 bytes, because the record's size is 308 inlined COPIES of the same
#: subtrees and an instance needs one value per position, not one per copy.
#:
#: **SHARED ACROSS WORKTREES, because the key is a content address and a worktree is not
#: one of its inputs** (measured 2026-10-29).  ``harness.corpus_key`` hashes the caller's
#: static identity for the draw, the example count, the format strategies and the generator
#: version; the identity ``test_emit.identity_of`` hands it is a document's BUNDLE-RELATIVE
#: name, its pointer and a digest of raw bytes, so none of those is where the checkout sits
#: and an entry one lane draws answers every other lane's question about the same document.
#: **It now reaches FURTHER across lanes than it did**, for the same reason the key moved at
#: all: a lane holding a different inliner used to compute a different key for the same
#: document, so sharing the store shared nothing with it.  Held per worktree it did not:
#: **7,343 entries across nine
#: stores holding 1,830 unique keys**, so 5,513 draws were paid again for an answer another
#: store already had -- at 0.15 s to 2,356 s each.  The two lanes with the emptiest stores
#: (8 entries and 0) were the two whose validation ran longest.
#:
#: A lane that makes a document emit for the FIRST time is what fills this, and that is why
#: sharing matters more than it looks: the cold draw is the price of SUCCESS, and paid per
#: worktree it is charged once to the lane that earned it and again to every lane that
#: merges it. ``ADCP_CACHE`` overrides the location; the default is beside the checkouts
#: rather than inside one, so no worktree owns it.
#:
#: Concurrency-safe without a lock for the reason ``put`` already is: one file per key,
#: written to a temporary and ``os.replace``\\ d into place, and two lanes computing the
#: same key compute the same bytes.
CACHE_ROOT = Path(os.environ.get("ADCP_CACHE") or ROOT.parent / ".adcp-cache")

DIRECTORY = CACHE_ROOT / "accepts-corpus"

#: **THE COMMITTED FLOOR: the drawn corpus, in the tree, under the current key.**
#:
#: ``docs/plan/architecture.md`` ("The drawn corpus is COMMITTED", 2026-10-30) decides it
#: and :data:`CACHE_ROOT`'s comment carries the reasoning.  What this constant has to get
#: right is the PATH, and it has two requirements that come from different places:
#:
#: * **The suite reads it by DEFAULT**, with no environment variable and no flag -- a fresh
#:   checkout is the case the commit exists for, so a floor reached only by opting in would
#:   be a floor a fresh checkout does not have.  So it is derived from :data:`ROOT` and has
#:   no ``ADCP_`` override; ``ADCP_CACHE`` still moves the CACHE, which is the half that is
#:   allowed to be somewhere else.
#: * **No lane can invalidate it by editing the compiler**, which is a property of the KEY
#:   and not of the path -- and it is the property that makes a path inside the tree
#:   admissible at all.  ``harness.corpus_key`` hashes ``bundle.source_identities``, so
#:   what moves these file names is a bundle bump or a generator bump.
#:
#: Under ``tests/`` because the population it answers for is the suite's
#: (``test_emit.graded()``) and the gate over it lives next to it; HYPHENATED so it is not
#: an importable package name sitting among the test modules.  It is not in
#: ``[tool.setuptools.packages.find]``'s ``where``, so none of it reaches the wheel: the
#: shipped artifact is the packaged records, and a drawn instance is evidence about them.
COMMITTED = ROOT / "tests" / "accepts-corpus"


class Store:
    """``get``/``put`` over a content-addressed directory, and nothing else.

    One file per key, under a two-character prefix directory so no single directory holds
    all 1,664.  The key is already a hash, so a file name needs no escaping and two
    different schemas cannot land on one path.

    **Written by rename, because every run is parallel.**  ``pyproject.toml`` sets
    ``-n auto --maxprocesses=10``, so ten workers draw at once and two of them can draw the
    same pair -- ``graded_reports`` grades the whole population on one worker while the
    parametrised test spreads the same pairs across the others.  A partial file would be
    read as a short entry, which ``corpus_defect`` reddens; ``os.replace`` is atomic within
    a filesystem, so a reader sees either the previous bytes or the whole new ones.  Two
    writers racing on one key write the SAME bytes -- the key is the content address of
    their common input -- so the loser of the race costs a rename and changes nothing.

    **A value that does not survive the round trip is NOT held.**  ``hypothesis`` draws
    values JSON cannot carry faithfully -- a ``nan``, which is not equal to itself -- and an
    entry that read back as something else would redden a pair that had been green.  So the
    write re-reads its own text and keeps the entry only where it is equal to what went in.
    The cost of declining is one re-draw per run for that pair, which is the safe direction.
    """

    def __init__(self, directory: Path = DIRECTORY) -> None:
        self.directory = Path(directory)
        #: Measurements, for the caller that wants to report cold against warm.
        self.hits = 0
        self.misses = 0
        self.held = 0
        self.declined = 0

    def _path(self, key: str) -> Path:
        return self.directory / key[:2] / f"{key}.json"

    def get(self, key: str) -> list[Any] | None:
        """The held instances, or ``None`` for a key this store has never been given.

        A file this process cannot read or parse answers ``None`` -- a MISS, so the pair
        draws.  That is the one place a silent fallback is right, and the reason is which
        question it answers: an unreadable file is not an entry, so there is nothing for
        the harness to grade and nothing to hide.  An entry that PARSES and says the wrong
        thing is the dangerous case, and this module does not decide that one:
        ``harness.corpus_defect`` does, out loud.
        """
        try:
            held = json.loads(self._path(key).read_text())
        except (OSError, ValueError):
            self.misses += 1
            return None
        self.hits += 1
        return held if isinstance(held, list) else []

    def put(self, key: str, instances: list[Any]) -> None:
        """Hold ``instances`` under ``key``, or decline and hold nothing."""
        try:
            text = json.dumps(instances, ensure_ascii=True, allow_nan=True)
            if json.loads(text) != instances:
                self.declined += 1
                return
        except (TypeError, ValueError):
            self.declined += 1
            return
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
            os.replace(tmp, path)
            self.held += 1
        except OSError:  # a store that cannot be written is a store that holds nothing
            self.declined += 1
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def files(self) -> list[Path]:
        return sorted(self.directory.rglob("*.json"))

    def keys(self) -> set[str]:
        """Every key this store holds a file for, which is the gate's left-hand side.

        A reading of the DIRECTORY and not a list anybody maintains, so the equality
        ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` asserts is
        derived on both sides -- ``codegen.dump_exemptions``' shape again.
        """
        return {path.stem for path in self.directory.rglob("*.json")}

    def entries(self) -> int:
        return sum(1 for _ in self.directory.rglob("*.json"))

    def bytes_held(self) -> int:
        return sum(p.stat().st_size for p in self.directory.rglob("*.json"))


class Layered:
    """The COMMITTED floor, then the shared cache; and only the cache is ever WRITTEN.

    Two stores and one rule in each direction, because the two halves answer different
    questions and swapping either rule gives the drift the commit was made to remove.

    **READ: the floor first.**  Both stores are content-addressed under one key, so for a
    key they both hold they hold an answer to the same question -- but not necessarily the
    same BYTES, because the draw itself is not reproducible (``corpus_key``'s own docstring
    measures it: a small share of pairs draw a different instance on a second pass).  So
    which store answers decides which witness the suite grades, and the point of
    committing the corpus is that every lane, every fresh checkout and CI grade the same
    one.  Read the cache first and a lane with a warm cache grades a witness the tree does
    not carry; the gate would be green locally on an entry nobody can review.

    **WRITE: the cache only.**  A run that wrote the floor would make the committed corpus
    a thing the suite edits -- it would dirty the working tree, it would promote whatever
    a lane's own key space happened to need, and
    ``test_no_run_writes_a_corpus_entry_inside_the_checkout`` is what reads that.  Promotion
    is deliberate: ``--write-corpus``.

    **A miss on both is exactly what it was** -- a key no store has been given, so the
    pair draws, the cache holds the result, and the gate reports that the floor is short
    of the population.  The gate is the thing that says the floor needs refilling; this
    class never decides it.

    **And a floor entry the DOCUMENT refuses is still a defect and not a miss.**  Nothing
    here re-validates -- ``harness.corpus_defect`` does, on every read, which is why a
    committed entry cannot pass quietly when it is wrong: the floor answers, the document
    refuses the answer, and the pair reports ``accepts:corpus_rejected``.  Falling through
    to the cache on a rejected floor entry would be precisely the silent repair that
    hides a stale commit, so ``get`` does not look at the value it returns.
    """

    def __init__(self, floor: Store, cache: Store) -> None:
        self.floor = floor
        self.cache = cache

    def get(self, key: str) -> list[Any] | None:
        held = self.floor.get(key)
        return self.cache.get(key) if held is None else held

    def put(self, key: str, instances: list[Any]) -> None:
        self.cache.put(key, instances)

    def promote(self, keys: set[str]) -> tuple[int, list[str]]:
        """Copy the cache's answer for each of ``keys`` into the floor.

        ``--write-corpus``' one action, and the only code in this project that writes the
        floor.  It copies and never draws: the draw is a parallel suite run, and a
        promotion that drew would be the 2,000-second serial pass this row exists to
        remove.  Returns what it wrote and the keys the cache could not answer, which the
        caller reports -- a key neither store holds means the draw has not been run.

        Idempotent, and it writes through :meth:`Store.put`, so the floor gets the same
        round-trip check the cache does: an entry that does not survive JSON is declined
        in both places rather than committed in one.
        """
        wrote, absent = 0, []
        for key in sorted(keys):
            if self.floor.get(key) is not None:
                continue
            held = self.cache.get(key)
            if held is None:
                absent.append(key)
                continue
            self.floor.put(key, held)
            wrote += 1
        return wrote, absent


#: The COMMITTED floor as a store of its own, so the gate can read it ALONE.  That is not
#: a convenience: the obligation is "every graded pair has a COMMITTED entry", and a gate
#: reading :data:`STORE` would be satisfied by a warm cache on the machine it ran on and
#: red on every other -- which is an instrument that reports where it was run.
FLOOR = Store(COMMITTED)

#: The cross-worktree cache as a store of its own.
CACHE = Store(DIRECTORY)

#: The one store the suite's population tests share, so the two passes over the graded
#: population -- ``graded_reports`` and the parametrised per-pair test -- fill and read one
#: corpus rather than two.  A module-level object and not a fixture, for
#: ``test_emit.graded_reports``' own reason: the readers are module functions, not tests.
STORE = Layered(FLOOR, CACHE)


# --------------------------------------------------------------------------- #
# §8's OBLIGATION draws too, and its draws are a second key space
# --------------------------------------------------------------------------- #
#: **THE WIDENING CHECK'S OWN DRAWS, held the same way and in a SEPARATE DIRECTORY**
#: (``adcp-client-python-3be.25``).
#:
#: ``harness.check_accepts`` draws once per pair and everything above holds it.
#: ``harness.check_widening`` draws several more times per pair -- a value class, an
#: intermediate node on the way to an instance location, the pair's node conjoined with a
#: demand -- and held none of them, which the row measured as the pole of a run whose
#: accepts draws were ALL replayed from :data:`COMMITTED`: 246.7 s on one pair of
#: ``core/async-response-data.json`` with 242.6 s of it in a single repeated draw, and over
#: 600 s on another without finishing.  ``harness._Draws`` carries the reading and the key;
#: this is only where it lands.
#:
#: **WHY A SECOND DIRECTORY AND NOT A SECOND KEY IN THE FIRST, which is a decision and not
#: a tidiness.**  ``harness.corpus_key``'s ``position`` already makes a widening key
#: unable to collide with an accepts key, so one directory would hold both correctly --
#: and would break the instrument over the first.
#: ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` asserts the
#: equality in BOTH directions, including ``extra == set()``: the committed floor may hold
#: no entry the graded population asks for.  That side reads :meth:`Store.keys`, a
#: ``rglob`` of the DIRECTORY, so widening entries landing there would make a landed gate
#: read red on nothing being wrong -- and the only repair available would be to teach the
#: accepts gate the other key space, which is one obligation grading two populations and
#: the way an assertion stops asserting.  ``--write-corpus``' prune has the same shape from
#: the other side: it unlinks every floor key the accepts population does not ask for, and
#: in one directory that is every widening entry, every time.
#:
#: So: two directories, two floors, two caches, and each equality over its own population.
#: ``tests/test_widening_corpus.py::test_a_held_widening_base_lands_in_no_accepts_key_space``
#: is the reading, and it is the one that would have caught the merge.
WIDENING_DIRECTORY = CACHE_ROOT / "widening-corpus"

#: The committed floor for that space, beside :data:`COMMITTED` and for its reasons: read
#: by DEFAULT with no flag and no environment variable, under ``tests/`` because the
#: population it answers for is the suite's, hyphenated so it is not an importable package
#: name, and outside ``[tool.setuptools.packages.find]``'s ``where`` so none of it ships.
#:
#: **IT HAS NO CURRENCY GATE YET AND THAT IS STATED RATHER THAN IMPLIED.**  The accepts
#: floor has one because its live key set is readable without drawing anything
#: (``live_keys()``: an identity, an example count and a format set, per graded pair).
#: This space's is not: which positions the population asks for depends on which borrowed
#: base hosted the declaration's location, so deriving the set exactly means running the
#: obligation -- and on a cold floor that costs the draws the gate would be reporting are
#: owed.  A gate over a SUPERSET would demand entries for draws that never happen and
#: could not be filled.  So what this row ships is the store, the layering and
#: ``--write-corpus``; whether the floor is also graded for currency, and against which
#: derived population, is an open decision for ``docs/plan/architecture.md``.
WIDENING_COMMITTED = ROOT / "tests" / "widening-corpus"

WIDENING_FLOOR = Store(WIDENING_COMMITTED)

WIDENING_CACHE = Store(WIDENING_DIRECTORY)

#: The composition, with :class:`Layered`'s two rules unchanged: the floor answers FIRST so
#: every lane and every fresh checkout grade the same held witness, and only the cache is
#: ever written so no run can dirty the tree.  Both rules matter here for the same measured
#: reason they matter above -- the draw is not reproducible, so which store answers decides
#: which witness is graded.
WIDENING_STORE = Layered(WIDENING_FLOOR, WIDENING_CACHE)
