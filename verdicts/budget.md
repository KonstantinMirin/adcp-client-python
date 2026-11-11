# `BUDGET = 30`: two causes fixed, one pair fixed, and the bound is NOT deleted

`adcp-client-python-luik` and `adcp-client-python-d5zb`, measured together. Both are
repaired and both repairs hold. **The bound stays, because the premise that these two
were the only thing standing between the tree and deleting it is wrong — and that premise
is mine.** I wrote it into both rows after `auw6`, and the measurement below refutes it.

Every figure here is cold unless it says warm: the widening cache moved aside, the
committed floor alone, no budget set anywhere, one pair per process.

## The answer, first

| `check_pair`, cold, no budget | before | `d5zb` alone | both repairs |
| --- | --- | --- | --- |
| `media-buy/refine-proposals-response.json#` | did not finish | 344.99 s | **10.27 s** |
| `media-buy/get-media-buys-response.json#` | did not finish | did not finish | did not finish |

One of the two pairs is fixed outright. The other is not, and what it is now bound by is
neither of the two causes this work owns.

## `d5zb` — the metaschema walk is gone, and the figures move with it

`hypothesis_jsonschema` ends `merged` with `_get_validator_class(out)`
(`_canonicalise.py:853`) **and discards the result**. It is the library asserting that its
own merge of two valid schemas produced a valid schema, and each call is a full
`jsonschema.check_schema` walk of the merged schema with a fresh validator and a fresh URI
join per node.

`harness.validator_classes_shared_within_one_call` already unbounded the library's cache,
which removed the *re*-walks. The residue was the first walk of every distinct merged
schema, and the cache cannot reach that — `merged` produces a new schema each call and
asks about that one. So for one grade the class is now resolved through the library's own
`validator_for` (which reads `$schema` and nothing else) and the walk is not performed.
The root is still walked once per build at `_from_schema.py:219`, so a schema that is not
one is still reported at the door.

Profiled on `get-media-buys-response.json#`, 50 Hz, one pair per process, no budget:

| inclusive share of the pair | before | after |
| --- | --- | --- |
| `jsonschema` `check_schema` | 74.4% (315.8 s) | **1.3% (4.8 s)** |
| `descend` | 75.7% | 1.5% |
| `iter_errors` | 75.9% | 1.9% |
| `evolve` | 20.4% | 0.6% |

## `luik` — the demand is bounded the way the node is bounded

`_bases` builds `{"allOf": [schema, _demanding(path)]}` and hands it to the draw. Only
that one site builds it; the row said `_reached` did too and that was wrong — `_reached`
draws a plain intermediate node.

`_Draws._draw` already reduced the conjunction, so the reason it stayed unbounded was
subtler than "nothing reduces it". A pin says *this location is exactly `v`* and a demand
says *an instance that HAS this location*, and the two contradict wherever `v` does not
carry it. The reduction placed, the conjunction then admitted nothing, and `_draw`'s
fail-safe paid the **unreduced** conjunction in full — 3,326,709 bytes on
`get-media-buys-response.json#`, which is the draw this bound exists to cut.

So `Fixtures.reduced` now takes the demanded instance locations and descends them instead
of pinning them: everything beside the path is pinned, the demanded location is left
exactly as the document states it, and the locations on the way to it are reduced
recursively with the rest of the path still open. `demanded_locations` derives the tokens
from the path alone and spells them exactly as `locations` spells `Location.at`, so the
two readings agree by construction rather than by coincidence.

Two things the implementation got wrong first and the measurement caught:

* the token namespace **restarts** at every re-entry, because `locations` builds `at` from
  the node it is handed. An absolute token compared one level down matches nothing, and
  the consequence was not a lost saving but the wrong one — every location below the
  path's first segment was left unreduced, which is the cost the clause exists to remove.
  The remainder is now relativised and handed on.
* a location that is both the demanded one *and* a prefix of deeper demanded ones must be
  descended, not left standing. The test is now "is anything still owed below this".

`_Draws.unreduced` counts the fall-through, so the figure is readable rather than
inferred.

## What `get-media-buys-response.json#` is now bound by — a third cause

With both repairs, 357 s and still running when the sampler stopped:

| | share | seconds |
| --- | --- | --- |
| `check_widening` | 84.0% | 300.2 |
| `harness.shared` (inclusive) | 62.6% | 223.5 |
| `harness.shared` as the deepest frame of our code | 45.5% | 162.6 |
| `canonicalish` | 63.8% | 227.9 |
| `merged` | 57.6% | 205.8 |
| `Fixtures.reduced` / `_opened` | 24.1% | 86.2 |

and the leaf time is **JSON serialisation**: `raw_decode` 78.3 s, `iterencode` 62.8 s,
`_iterencode_dict` 25.7 s, `_iterencode_list` 6.2 s — **173 s of 357 s, 48% of the pair.**

That is `canonicalisation_shared_within_one_call`'s memo. Its key is a 32-byte digest, but
producing the digest still renders the whole multi-megabyte schema with `json.dumps` on
every call, and the entry is `zlib`-compressed on write and `json.loads`-ed back on every
hit. `adcp-client-python-pcqy` is closed and its close reason says exactly this much —
*"the named site `shared` has moved and still calls `json.dumps` per call, but the key is
now a 32-byte blake2b digest rather than the text, which is the defect the row is
about"* — so the per-call render was explicitly left standing when that row closed. It
needs a row of its own and it is not `luik`'s or `d5zb`'s.

A second observation from the same run: the watchdog thread never fired. `os._exit` from a
timer thread cannot run while the main thread holds the GIL inside the C JSON encoder, so
this pair cannot be interrupted by anything but `SIGALRM` — which is what `harness.within`
uses, and is a second reason the bound cannot simply be removed today.

## And cold is not warm, which is how this pair looked fixed when it was not

Warm, with this worktree's widening cache present (530 entries written by the `auw6`
runs), the two pairs read **0.82 s** and **9.12 s** and both finished. With the cache moved
aside and the committed floor alone (290 entries), neither finished.

The goal's clause is *cold == warm*, and the widening store does not meet it: the pairs
whose draw is unbounded are exactly the pairs whose entries the cache supplies, so a warm
lane cannot see the defect at all. Every figure above is therefore cold. This is recorded
in `tests_emit/corpus.py` beside the accepts store's own cold-against-warm table.

## Why the bound is not deleted

Deleting it today makes `python -m codegen` hang on one pair, uninterruptibly. The bound
is still a defect and still not a setting; what has changed is that the list of causes
behind it is now two shorter and one longer, and each is named:

* `adcp-client-python-luik` — fixed here.
* `adcp-client-python-d5zb` — fixed here.
* the canonicalisation memo's per-call render — new, filed, blocking.

`adcp-client-python-l6xn` owns the deletion and should take it when the third lands.

## Verification

`./check`, warm and cold, identical in all three figures:

```
emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059
kind: verdict 0, deferred 0, chained 0  ->  primary 0, chained 0
approximated 383 facts in 148 documents
```

warm repeat 0.49 s; cold 118.13 s. 105 gate tests pass. `ruff` 16 findings before and
after, `mypy` 126 before and after on the two changed modules. `/proc/vmstat oom_kill` 75
before and after every run.
