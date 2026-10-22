# An absolute `$ref` that names a node inside another document — the prediction

`salesagent-j3k2l.14`. Committed before any line of the fix exists, so the grading
below is against a record and not against a recollection.

Branch `sdk/j3k2l14-fragment-ref`, worktree `/Users/konst/projects/acp-j3k2l14`, off
`emit/from-scratch` at **`fc9a880594caac2c01ee7a663d848528c80bdb49`** with a clean
tree. Every number here is predicted against that sha.

**Not graded here:** the step-path verdicts (`pass`, `no_constraint_to_step`,
`graded_instances`). That tree carries four known-failing step tests and a
`graded_instances` constant one revision behind, from a merge the integrator is
repairing; `codegen/harness.py` belongs to another lane. Everything below is
bundle-side — the reference graph, the resolver, the lowering — and none of it reads
the step path.

## The baseline, measured at `fc9a880` before this file was written

Two instruments, named, because the bead records a figure the two disagree about.

**Instrument R — READING the reference graph.** `bundle.references` (the schema-position
walk) over `bundle.portable`, with `bundle.document_for` on each URI's document half.

| fact | value |
|---|---|
| portable documents | 1,054 |
| `$ref` sites at a schema position | 4,200 |
| … absolute, no fragment | 3,682 |
| … absolute, carrying a fragment | 113 |
| … local (`#/…`) | 405 |
| distinct `$ref` URIs | 968 = 738 plain + 76 absolute-with-fragment + 154 local |
| documents carrying an absolute fragment ref DIRECTLY | **34** |
| … reaching one through the closure | **88** |
| … unaffected | **966** |
| documents carrying a LOCAL fragment ref directly | 45 |
| … reaching one through the closure | 135 |
| closure of EITHER kind | **151** |
| distinct absolute fragment targets | **76**, in **19** documents |
| absolute refs naming no bundle document | 0 |
| fragment pointers naming no node in their target | 0 |

The bead's 34 / 88 / 966 / 76 reproduce exactly. `document_for`'s own docstring says
"the remaining 230 carry a fragment" — 230 = 76 + 154, so that figure lumps the local
refs in with the absolute ones, and instrument R agrees with it.

**Instrument S — RUNNING the resolver.** A replica of `bundle.resolved`'s store loop,
which is where it raises, with the O(paths) inlining skipped.

| fact | value |
|---|---|
| documents `bundle.resolved` raises for | **151** of 1,054 |
| … on a local-fragment URI | 93 |
| … on an absolute-with-fragment URI | 58 |
| … inside the absolute-fragment closure (88) | 88 |
| … inside the local-fragment closure (135) | 135 |
| … in NEITHER closure | **0** |
| documents with no `$ref` at all (returned as read) | 364 |

**The 311 is not reproducible by any instrument I ran.** Nine candidates: instrument R
direct and closure (34 / 88); instrument S (151); a blanket walk (one that descends
`examples`, `const` and `default`, which the plan forbids) direct and closure (76 / 151);
the store loop over all 1,625 files with the projections included, under both spellings
of `known` (672 / 672); refusals whose keyword is `$ref` (227); refusals whose detail
mentions a fragment URI (4). **There is no ~223 residual.** The real gap between the
bead's 88 and the resolver's own figure is 63, and it is entirely the LOCAL `#/$defs/…`
refs the bead does not name: `document_for`'s first line is `if "#" in uri: return None`,
and a local ref's first character is `#`, so the same gate closes on both kinds.

**The lowering, at `fc9a880`, over all 1,054 (`emit.emit`'s own walk — `bind`, the memo
and the cycle rule — with the file pass left off).**

| fact | value |
|---|---|
| lowered | 394 |
| refused | 660 |
| refused on the fragment gate DIRECTLY ("names no document of this bundle") | **4** |
| refused because a target is refused (any cause) | 214 |
| of the 34: lowered / refused | 0 / 34 |
| of the 88: lowered / refused | 0 / 88 |
| of the 966: lowered / refused | 394 / 572 |
| of the 394 that lower, how many `bundle.resolved` raises for | **0** |

That last row is the structural fact the whole prediction turns on: **the refusal gate
and the resolution gate coincide exactly today.** Nothing crashes, because every document
whose resolution would raise also refuses in the lowering first. The cost is 151
documents that can never emit, which is what blocks `salesagent-j3k2l.8`.

The four gate refusals, and what their target does on its own:

| referrer | names | the target's own outcome |
|---|---|---|
| `core/catalog-selection.json` | `core/catalog.json#/properties/type` | refused on `pattern` at `/properties/gtins/items` (D5's alias module — `salesagent-j3k2l.12`) |
| `core/package-delivery-metric-value.json` | `core/delivery-metric-aggregate.json#/oneOf/0` | refused on `allOf` at `/oneOf/0` |
| `core/requirements/daast-asset-requirements.json` | `core/daast-tracker-constraints.json#/definitions/daast_versions` | refused on `definitions` at `/` |
| `media-buy/product-purchase-input.json` | `media-buy/product-purchase.json#/properties/product_id` | refused on `$ref` at `/properties/pricing` (chain) |

**18 of the 19 fragment-target documents are refused on a keyword of their own.** The one
that lowers is `core/version-envelope.json` (`AdCPVersionEnvelope`), named at
`/properties/adcp_version` and `/properties/adcp_major_version` by 12 referrers — and all
12 refuse on another keyword: `$ref` 4, `not` 3, `allOf` 2, `type` 2, `dependencies` 1.

## What I am going to build

1. **`bundle.document_for` splits the fragment off and matches the document half.** Its
   "None for a fragment" clause is the gate this bead removes; the real rule is "None when
   no trailing run of segments is a document of this bundle".
2. **`bundle.resolved` keys its store on the DOCUMENT URI and skips a local ref.** Probed,
   both halves: `harness.resolve` resolves `#/definitions/x` against the referrer with an
   EMPTY store, and it follows a fragment itself when the store holds the target under the
   document URI — but raises `_RefResolutionError` when the store is keyed on the full URI
   including the fragment, which is how it is keyed today. So a fragment ref would fail
   even with its target in the store; the key is the bug, not only the `None`.
3. **`Module` records pointer → symbol**, written in `Module.declare`, which every
   declaration already passes through and which already receives the pointer.
4. **`Module` carries `named`: the pointers of its own nodes that a `$ref` elsewhere in the
   BUNDLE names**, computed once per run from the bundle rather than from the run's document
   set, so a module's content stays a function of (bundle, this package) and not of who
   else was in the run.
5. **A named node that is not already a class gets an alias in its own module**, named by
   D3's existing nested rule (parent + `pascal_case(property)` — the `name_hint` the walk
   already computes), and the node's type becomes that symbol so the constraint has ONE
   spelling in the module.
6. **`emit.bind` resolves a fragment to the target module's symbol at that pointer**, and
   refuses by name, pointer and keyword with the fragment named when the target declares
   none.

## The predictions

| # | prediction | value |
|---|---|---|
| P1 | documents `bundle.resolved` raises for, after | **0** of 1,054 (from 151) |
| P2 | of the 88, how many become resolvable | **88** of 88 — and 63 more, the local-fragment-only ones, for 151 of 151 |
| P3 | of the 88, how many EMIT | **0** |
| P4 | of the 88, how many are refused on a keyword of their own | **88** — the 4 gate refusals become chain refusals naming the target's real keyword (`pattern`, `allOf`, `definitions`, `$ref`), the other 84 keep the keyword they already refuse on |
| P5 | new CLASSES in the emitted tree | **0** |
| P6 | new nested ALIASES in the emitted tree | **2**, both in `core/version_envelope.py`: `AdCPVersionEnvelopeAdcpVersion` and `AdCPVersionEnvelopeAdcpMajorVersion` — the only fragment-target pointers in a document that lowers |
| P7 | N (emitted modules) | **383, unchanged.** It must not drop and I do not expect it to rise: the population that this unblocks is gated behind its targets' own keywords, and `salesagent-j3k2l.12` is what opens `core/catalog.json` |
| P8 | graded pairs | **448, unchanged** (383 roots + 65 nested). A nested alias is not a class and carries no `__adcp_schema__`, so `graded()` does not collect it |
| P9 | files in the committed tree that change | **1** — `src/adcp/types/_schemas/core/version_envelope.py`. No schema artifact changes: a document's resolved form is written only for a document that emits, and no newly-resolvable document emits |
| P10 | the schema comparison for `core/version-envelope.json` | **stays green.** Measured on a constructed pair: moving a `description` onto the alias puts it INSIDE the optional's `anyOf` branch rather than beside it, while `pattern`, `minimum` and `maximum` stay put. The comparison unwraps a single null branch as absence, so I predict it does not see the move. **This is the prediction I am least sure of**; if it reddens, the fix is to leave the description on the field and name only the constraints |
| P11 | the LOCAL-fragment import path | **not built.** 0 of the 394 documents that lower carry a local fragment in their closure, and the 45 that carry one directly all refuse on `definitions`/`$defs` — the keyword a local fragment points through. The resolution half is fixed because `resolved` is what raises; the import half has a population of zero and gets built when a document reaches it, which is this plan's own rule for `propertyNames`/`enum` and the root-array row |

## Grading

Filled in after the measurement, in this file, saying which predictions were wrong.
