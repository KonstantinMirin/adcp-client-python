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
document.  So the key is over ``catalogue.admitted_identities`` instead: what a document
ADMITS with every ``$ref`` resolved to the node it names, and the instances it STATES and
ADMITS, which is where the closure the record's self-containment used to buy now comes
from.  There is still no edge list anybody maintains -- the graph is read off the ``$ref``
strings the documents write -- and a hand-maintained map would be the second copy §3
forbids.  **It is admission and not BYTES, which is the other half of the same sentence**
(``adcp-client-python-lzzj.8``): keyed on a document's raw text, an acceptance-preserving
rewrite of the bundle redrew the whole population -- 1,054 of 1,054 identities moved on
22,338 differences no validator can see, 854 of them a trailing newline -- so an
improvement to the schema cost exactly what a regression cost.  Keyed on admission, 0 of
1,054 move.

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

**AND IT IS NOW TWO STORES, BECAUSE THE DRAWN CORPUS IS COMMITTED** (decided 2026-10-30,
``docs/plan/architecture.md`` "The drawn corpus is COMMITTED").  :data:`COMMITTED` is a
tracked directory in this tree and :data:`DIRECTORY` is the cross-worktree cache beside
the checkouts; :class:`Layered` composes them, and the composition is one sentence in
each direction -- **the floor is read FIRST and only the cache is ever written.**  Which
half each obligation belongs to:

* **The floor answers before the cache**, so every lane, every fresh checkout and CI
  grade the SAME held instance.  Read the cache first and a lane with a warm cache would
  be grading a witness nothing in the tree carries, which is the drift the commit
  exists to remove.
* **No run writes the floor.**  A draw's result goes to the cache, so a run cannot
  dirty the working tree and a lane cannot promote an entry by accident.  Promotion is
  ``--write-corpus`` (``tests/conftest.py``), the same affordance
  ``docs/plan/rebuild-plan.md``'s generated grids already have for the same reason: a
  derived artifact in the tree, an equality that grades it, and one flag that rewrites
  it when the derivation has deliberately moved.
* **The cache is therefore what it always was** -- the place a key the tree does not
  carry yet gets answered from, which is the lane that makes a document emit for the
  first time and every lane that merges it.

``tests/test_accepts_corpus.py``'s
``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` is the gate the
paragraph the commit replaced said could not exist, and it reads the FLOOR ALONE for the
first reason above.

**THE STORE AND THE TWO DIRECTORIES MOVED TO ``codegen/held.py``, AND THIS MODULE IS THE
SUITE'S READING OF THEM** (``adcp-client-python-82m.4``).  Nothing above changes: the key is
still the harness's, the paths are still the two this file always named, the floor is still
read first and only the cache is ever written.  What changed is WHO ELSE needs a store.
``docs/plan/architecture.md`` §10 requires the RUN to write one row per graded pair, so
``codegen/__main__.py`` grades the tree it just wrote -- and a run that cannot reach the
held instances grades 2,793 pairs cold, which is 2,015.6 s against a 39.6 s warm pass. A
store under ``tests/`` is a store the run cannot import, so the MECHANISM and the two
directory names are in ``codegen/held.py`` and every name this module used to define is
imported from there under the name it always had. ``codegen/held.py``'s own docstring
carries why the floor's path is still inside ``tests/`` and why the verifier still knows
neither path.

**AND THE WIDENING STORE DOES NOT MEET "COLD == WARM", WHICH IS A MEASUREMENT AND NOT A
PROPERTY OF THE ACCEPTS TABLE ABOVE** (``adcp-client-python-luik``/``-d5zb``;
``verdicts/budget.md`` carries the method). The table above compares cold against warm for
the ACCEPTS store and reports every verdict identical in both. The same comparison on the
WIDENING store does not have that result, because the pairs whose draw is unbounded are
exactly the pairs whose entries the cache supplies:

====================================================  ===============  ==========
``check_pair``, no budget set anywhere                           cold        warm
====================================================  ===============  ==========
``media-buy/refine-proposals-response.json#``          did not finish     9.12 s
``media-buy/get-media-buys-response.json#``            did not finish     0.82 s
====================================================  ===============  ==========

Cold is :data:`WIDENING_FLOOR` alone -- the committed 290 entries -- and warm is that floor
with a lane's :data:`WIDENING_CACHE` in front of it, 530 entries written by the runs that
took the figures. **So a warm lane cannot see the defect at all**, and two rows were filed
and a bound was defended on figures that a warm cache had already answered. Every figure
in ``verdicts/budget.md`` is cold for that reason, and the reading a lane owes a draw-cost
measurement is this one: move the cache aside, then measure.

This is not an argument for deleting the cache. It is the reason the accepts table's
"every verdict was identical" sentence may not be read across to this store: there the
cache replaces a draw that TERMINATES, and here it replaces one that does not.
"""

from __future__ import annotations

from codegen.held import (
    CACHE,
    CACHE_ROOT,
    COMMITTED,
    DIRECTORY,
    FLOOR,
    ROOT,
    STORE,
    WIDENING_CACHE,
    WIDENING_COMMITTED,
    WIDENING_DIRECTORY,
    WIDENING_FLOOR,
    WIDENING_STORE,
    Layered,
    Store,
)

__all__ = [
    "CACHE",
    "CACHE_ROOT",
    "COMMITTED",
    "DIRECTORY",
    "FLOOR",
    "ROOT",
    "STORE",
    "WIDENING_CACHE",
    "WIDENING_COMMITTED",
    "WIDENING_DIRECTORY",
    "WIDENING_FLOOR",
    "WIDENING_STORE",
    "Layered",
    "Store",
]
