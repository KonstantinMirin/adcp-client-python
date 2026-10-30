"""Where the accepts check's drawn instances are HELD between runs.

``codegen/harness.py`` computes the key and this module is the only thing that touches a
path, which is ``docs/plan/architecture.md`` §9's division: the verifier "grades an
emitted class against the document it names, and it does so without reading the walk" --
its import set is ``jsonschema``, ``hypothesis``, ``hypothesis_jsonschema``, ``pydantic``
and the five ``codegen`` modules §9 names, and nothing about a directory layout is among
them.  A cache that opened a file from inside ``harness`` would be the hole, because what
makes that module able to grade output that does not exist yet is that it reads nothing
but its arguments.  So the store is the CALLER's, the key is the harness's, and the seam
between them is two methods.

**WHY THIS EXISTS, in one measurement.**  ``harness.check_accepts`` draws with
``hypothesis_jsonschema.from_schema``, and the repetition it pays is inside the library:
``merged`` re-enters ``canonicalish`` for every subschema it sorts
(``_canonicalise.py:631``), so one call on an ALREADY-RESOLVED document re-canonicalises
the same subtrees -- 43.58 s for one 18,301-byte document with the within-call memo, over
600 s without it.  Resolution cannot remove it and the harness's own docstring says so.
Meanwhile every input to the draw is pinned: the bundle is ``schemas/cache/3.2``, the
packaged records are committed artifacts, ``_SETTINGS`` sets ``derandomize``, and
``accepts_examples`` is 1.  The suite therefore recomputed a deterministic corpus from
scratch on every invocation, twice per pair per run -- once in
``test_emit.graded_reports`` and once in the parametrised per-pair test.

Timed on the two documents worth timing, each by itself, cold against warm:

===================================================  =========  ==========  ========
``check_pair`` on one document                       node bytes     cold s    warm s
===================================================  =========  ==========  ========
``core/macro-declaration.json#``                        44,949     151.51     0.013
``media-buy/get-media-buy-delivery-response.json#``  2,701,506   2,356.66     0.389
===================================================  =========  ==========  ========

Of the first, 151.24 s is inside ``from_schema`` -- 99.8% of the pair.  Of the second only
527.07 s is, and the other 1,830 s is the generation the strategy then drives; the corpus
replaces both, because what it holds is the instance and not the strategy.  Over all 1,664
pairs in one process the same comparison is **2,015.6 s cold against 39.6 s warm**, with
1,662 replayed, 0 rejected and every verdict identical.

**WHAT THE KEY IS OVER, AND THE ONE THING IT MUST NOT BE OVER.**  ``harness.corpus_key``
carries the argument; the short form is that the key is the DOCUMENT's and never our
rendering of it.  Keyed on the record -- ``bundle.record``'s output, this package's own
inliner -- the address moved with every change to how we inline, for the share of the
bundle whose record differs from its raw document at all (the reading is ``bundle.record``
against ``bundle.read`` over ``bundle.portable``, and it is most of it), so every entry
below was redrawn at the per-pair cost tabulated above for a change that altered no
document.  So the key is over ``bundle.source_identities`` instead: a document's own raw
bytes and the raw bytes of its reference closure, which is where the closure the record's
self-containment used to buy now comes from.  There is still no edge list anybody
maintains -- the graph is read off the ``$ref`` strings the documents write -- and a
hand-maintained map would be the second copy §3 forbids.

**AND THE DRAW THIS REPLACES IS NOT REPRODUCIBLE.**  Measured before the store was built,
because the answer decided whether to build one: two full passes over the same 1,664 pairs
at the same pinned inputs drew a different instance for **23 of them (1.4%)**, and one
identical 208-pair shard re-run differed from itself on 3.  Not the seed -- ``_SETTINGS``
fixes ``derandomize`` -- not ``PYTHONHASHSEED``, not the recursion limit; process-global
state inside ``hypothesis`` whose lifetime garbage collection governs.  Every verdict was
identical in every one of those runs.  So holding the witness REMOVES drift rather than
adding it: what the scheduler decides today, the key decides from the bundle's bytes, and
the document still decides whether the held value is admissible.

**AND WHAT MAKES A STALE ENTRY SAFE.**  Nothing here decides whether an entry may be
used.  ``harness.corpus_defect`` re-offers every held instance to the DOCUMENT and checks
the count against the obligation before one of them is allowed to count, and a defect is
``accepts:corpus_rejected`` -- a verdict on the pair with zero instances graded, which is
red twice over.  That is ``codegen.dump_exemptions``' shape: a derived equality over the
packaged tree, not a stored list.  This module's whole contract is "answer with exactly
what was stored under this key, or ``None``".
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

#: The repository root, reached the way ``tests/test_import_rule.py`` reaches it.
ROOT = Path(__file__).resolve().parents[1]

#: **A BUILD ARTIFACT and not a committed one, and the SIZE is not what decides that.**
#: Measured over the whole graded population at ``accepts_examples=1``: **160,977 bytes --
#: 0.16 MB -- over 1,661 entries**, the largest single one 6,211 bytes
#: (``core/attestation-capabilities.json#``).  A drawn instance is nothing like the record
#: it came from: ``media-buy/get-media-buy-delivery-response.json#`` is 5.19 MB of record
#: and its instance is 882 bytes, because the record's size is 308 inlined COPIES of the
#: same subtrees and an instance needs one value per position, not one per copy.  So the
#: corpus is small enough to commit, and that option stands open.
#:
#: What keeps it out of the tree is the OTHER half: a committed corpus is a second derived
#: artifact whose currency has no instrument.  A stale entry here is silently correct --
#: its key stops matching, the pair draws, and nothing reddens -- so "the committed corpus
#: is up to date" would be an obligation nothing grades, and the gate for it would have to
#: redden on any in-flight record change, which is correct work.  Regenerated on a miss it
#: cannot go stale at all.  **The cost of that choice is stated rather than hidden: a fresh
#: checkout's first run is a full cold run.**
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

    def entries(self) -> int:
        return sum(1 for _ in self.directory.rglob("*.json"))

    def bytes_held(self) -> int:
        return sum(p.stat().st_size for p in self.directory.rglob("*.json"))


#: The one store the suite's population tests share, so the two passes over the graded
#: population -- ``graded_reports`` and the parametrised per-pair test -- fill and read one
#: corpus rather than two.  A module-level object and not a fixture, for
#: ``test_emit.graded_reports``' own reason: the readers are module functions, not tests.
STORE = Store()
