# Prediction: the 9 `enum: [False, True]` missing facts, before the change exists

Base: `64131600f` (acp-fresh trunk). Branch `sdk/j3k2l28-conjuncts`.
Instrument: `tests/test_emit.py`'s `graded()` / `pair_of()` through
`codegen.harness.check_pair(..., max_steps=0)` — comparison only, no step sites
walked — summed over the whole graded population.

## What is measured on the base, before anything changes

1034 pairs, `added 0`, `missing 11`, `differs 0`. The 11 are carried by **seven**
documents, not nine (the brief said nine; the brief is counting facts):

| document | missing |
|---|---|
| `formats/canonical/agent_placement.json` | `/properties/experimental/enum`, `/properties/v1_translatable/enum` |
| `formats/canonical/native_in_feed.json` | the same two |
| `formats/canonical/responsive_creative.json` | the same two |
| `formats/canonical/sponsored_placement.json` | the same two |
| `formats/canonical/image_carousel.json` | `/properties/v1_translatable/enum` |
| `a2ui/component.json` | `/properties/component/additionalProperties/description` |
| `a2ui/surface.json` | the same, one level deeper |

Nine `enum` facts over five documents, and two a2ui mapping-value descriptions
over two. Only the nine are this lane's.

## The salesagent-j3k2l.36 diagnosis: VERIFIED, not taken on trust

Probed directly on `formats/canonical/agent_placement.json`, reading the resolved
document the package carries:

* the document's OWN `/properties/experimental` is `{"default": true,
  "description": "..."}` — it states no `type` at all;
* its single `allOf` conjunct declares the same property as
  `{"enum": [false, true]}` — the resolver's finite-type rewrite of the base's
  `{"type": "boolean", "description": ...}`, with the `type` and every annotation
  dropped;
* `_composed` gap-fills that conjunct's `enum` into the node, so the composed
  node carries `enum: [false, true]` and still no `type`;
* `_uncanonicalized` at the node matches only a node that is EXACTLY
  `{"enum": [False, True]}`, so it does not fire and returns `rewritten=False`;
* `_constrains_nothing("enum", node)` is `False`, because its gate correctly
  requires `type == "boolean"` and the node has no type.

Every link measured. The diagnosis holds.

## Where the .36 diagnosis is wrong in its detail, and my prediction says so

The brief says the prescribed fix makes "the existing gate fire on its own
terms". **It will not fire, and it should not have to.** `_uncanonicalized`
REPLACES the canonical node rather than annotating it: `{"enum": [false, true]}`
comes back as `{"type": "boolean"}`. So once the conjunct is uncanonicalized
before gap-filling, the node receives `type: boolean` and **there is no `enum`
fact at the node at all** — nothing for `_constrains_nothing` to be asked about.

The fact is folded one canonicalization earlier, by the one that owns the
rewrite, and the accepted set still gets graded: the document side now states
`type: boolean` and the model states `type: boolean`, so the pair compares that
instead. `compared` loses an `enum` at each of the nine sites and gains a `type`.

I predict `ComparisonResult.constrains_nothing` gains **zero** entries from this
change.

## The numbers predicted

| | base `64131600f` | after |
|---|---|---|
| pairs | 1034 | 1034 |
| `added` | 0 | **0** |
| `missing` | 11 | **2** |
| `differs` | 0 | **0** |
| documents carrying a fact | 7 | **2** (`a2ui/component.json`, `a2ui/surface.json`) |
| `emitted` | 686 of 1054 | 686 of 1054 |
| `accounted` | 1053 | 1053 |
| `deferred` | 0 | 0 |

`missing` bottoms out at 2, not 0. The two a2ui facts are a plan decision
(`compiler.Type` has no slot for an annotation on an INNER type, and
`containers._inner` refuses a CONSTRAINT there for the same reason) and are
deliberately left.

The emitter counts are predicted unchanged because the change is in the
COMPARISON, which no emitting code path reads.

## The 12 negative fold cases

**None of them move.** All twelve call `_constrains_nothing` directly with a
hand-written node, and this change does not touch that function or its gate. If
any of the twelve flips to folding, the forbidden widening has been done and the
change is wrong.

The one in the list that is the real discriminator — `{"enum": [False, True]}`
with no declared type — must keep comparing, and it will: `_uncanonicalized`
rewrites a conjunct that IS that node to `{"type": "boolean"}`, which is the
same accepted set written the resolver's way; a node the DOCUMENT itself states
bare is not a conjunct and is not rewritten.

## The risk this change carries, named before it is run

`compare_schema` uses `_uncanonicalized`'s `rewritten` flag to admit a
MODEL-ONLY `description` or `default` at a node the resolver stripped. Consider a
property whose own restatement is EMPTY and whose conjunct is the finite rewrite:
today `_composed` produces exactly `{"enum": [false, true]}`, `_uncanonicalized`
matches at the node, `rewritten` is `True`, and a model-only `description` is
admitted. After this change the node is `{"type": "boolean"}`, which is not a
canonical form, `rewritten` is `False`, and that `description` would be reported
as **`added`** — breaking the one invariant that matters, the direction in which
a class is narrower than its document.

I predict **no such site exists in the 1054-document bundle** and `added` stays
0. If `added` rises, this is the cause, and the fix is for `_composed` to carry
the rewrite flag out rather than for the node-level admission to be widened.

## The two probes

1. a conjunct stating a fact the model lacks (a real constraint, not the boolean
   domain) — `missing` must name it;
2. a conjunct stating `enum: [false]` — not the full boolean domain — must still
   be compared and reported. This is the one that distinguishes the fix from the
   forbidden widening of `_constrains_nothing`.

Both predicted to hold.
