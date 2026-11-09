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

Branch tip `bf1a1ed6b`, nine commits off `fc9a880`: the prediction, `codegen/compiler.py` on
its own (a sibling lane holds the lowerings), the mechanism, then the fixes and the test work
below.

**The suite, whole, final line and nothing sampled:**

```
5 failed, 588 passed in 1218.28s (0:20:18)
```

```
FAILED tests/test_emit.py::test_the_step_result_is_counted_over_the_whole_population
FAILED tests/test_emit.py::test_the_harness_steps_every_one_of_d6s_six_families
FAILED tests/test_emit.py::test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it
FAILED tests/test_emit.py::test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded
FAILED tests/test_harness_steps.py::test_an_unsteppable_site_is_reported_rather_than_passed
```

**Those five are inherited, and they are the five the integrator named before this branch
existed** -- four step-path failures from a merge of `fix/refuses-conjunct-step` into
`emit/from-scratch` that auto-merged `codegen/harness.py` textually, plus the
`graded_instances` constant one revision behind. This branch touches none of
`codegen/harness.py`, `tests/test_emit.py`, `tests/test_harness_steps.py` or `codegen/lower/*`,
so they are topologically not its. **Zero additional failures**, and no step-path verdict
(`pass`, `no_constraint_to_step`, `graded_instances`) is measured or relied on anywhere in this
file.

The run was launched at `3d71f02d4`; the two commits after it touch only
`tests/test_fragment_ref.py`, one of them AST-identical whitespace (proved by `ast.dump`) and
one strengthening a single assertion. `tests/test_fragment_ref.py` was run on its own at
`bf1a1ed6b`: **16 passed**.

| # | predicted | measured | |
|---|---|---|---|
| P1 | `resolved` raises 0 of 1,054 | 0 of 1,054, from 151 | right |
| P2 | 88 + 63 = 151 of 151 become resolvable | 151 of 151 | right |
| P3 | 0 of the 88 emit | 0 | right |
| P4 | 88 refused on a keyword of their own; the 4 become chain refusals | 88 refused; the 4 now name `pattern`, `allOf`, `definitions` and a chained `$ref`; 0 refusals anywhere still say "names no document of this bundle" | right, but see D4 |
| P5 | 0 new classes | 0 | right |
| P6 | 2 new nested aliases, `AdCPVersionEnvelopeAdcpVersion` and `AdCPVersionEnvelopeAdcpMajorVersion` | exactly those two | right |
| P7 | N = 383 | 383 over the named population of 981, 616 refused. Over the WHOLE 1,054: 394 emitted / 660 refused, both unchanged | right |
| P8 | graded pairs 448 | 448 (224 classes + 224 module-level aliases) | right |
| P9 | 1 file of the tree changes | 1: `src/adcp/types/_schemas/core/version_envelope.py` | right |
| P10 | the comparison stays green | identical before and after: 9 compared, 2 model-only facts, 0 missing, 0 differs, 0 added | right |
| P11 | the local-fragment IMPORT path is not built | not built; only the resolution half, which is where `resolved` raises | right |

**Eleven for eleven is not a good sign on its own, so say why.** These were written after
the baseline above was measured, not before it, and the baseline is what made them easy: once
you know that 18 of the 19 fragment-target documents refuse on a keyword of their own, P3
through P9 follow. The predictions that would have been hard are the ones about the MECHANISM,
and four of those are things the build found and the sheet does not mention. Those are the
content:

**D1 — `document_for`'s own fragment split was dead production code.** The sheet's build item
1 says "`document_for` splits the fragment off and matches the document half", and it was
written that way. It is wrong: every caller needs BOTH halves, so every caller splits before
asking, and a split inside `document_for` is unreachable from any live call. Found by breaking
the change on purpose — reverting that clause reddened one unit test of itself and nothing
else, while the real gate kept working. `split_ref` is now the one reading and `document_for`
reads no `#` at all. **A probe that reddens only a test of the line you changed is telling you
the line is not load-bearing.**

**D2 — 10 of the 76 named nodes are THEMSELVES a `$ref`, and the design did not cover them.**
Build item 5 says "a named node that is not already a class gets an alias", and the
implementation asks `decided.type.local`. A `$ref` node comes back `local` too, with a symbol
the target module IMPORTED rather than declared — so it gets no entry in `Module.declared` and
the reference refuses. Binding it anyway would make a fragment reference a re-export, where
section 2's rule is an import of a symbol the target DECLARES. The 10 sit in 3 documents
(`core/catalog.json`, `core/targeting.json`, `media-buy/product-purchase.json`), all three
refused on a keyword of their own, so 0 are reachable: refused with that reason named, rather
than a re-export built for an empty population. The step whose population reaches one decides
whether the chain is followed to the declaring module.

**D3 — 3 of the 13 documents that reference only themselves keep a recursive `$ref` after
resolution.** `resolve_all_refs` cannot inline a cycle, so
`core/bidding-policy-capability.json`, `core/placement-presentation.json` and
`governance/reported-outcome-error.json` come back with 4, 8 and 10 references still in them.
All three are refused on `definitions`, so no pair grades a document with a reference left in
it. Named as a ceiling in the test rather than asserted away.

**D4 — the chain refusal satisfied P4's letter and not the exit condition.** With the gate
lifted, the four former gate refusals became `its target core/catalog.json is refused: …` — the
right cause, but naming only the file and not which of its nodes was wanted, where the gate's
message had carried the whole URI. The exit condition for this row is a refusal with the
FRAGMENT named. Fixed in its own commit: `its target core/catalog.json#/properties/type is
refused: …`, bundle-relative, with a reference carrying no fragment unchanged (all 214 existing
chains). **P4 was graded green on a count before the message was read.**

**D5 — `bundle.resolved`'s cost on the newly reachable documents is NOT MEASURED, and the
first version of this entry claimed it was.** The function's own docstring predicts a ceiling
("Step 8 emits the whole population and will meet it"; a 9,109-byte document resolves to
4.8 MB), and opening the gate is what makes those documents reachable, so the ceiling is
plainly the next thing `salesagent-j3k2l.8` pays — but I wrote "a full pass did not finish in
30 minutes, and at least one of the 151 does not finish in 20 seconds" and **neither figure is
evidence.** All four long-running measurements on this box died with exit 144, which is the
memory killer: 15 Python processes from sibling lanes, 3.4 GB of 5 GB swap in use, ~900 MB
free. Two of the four I had killed myself. The 20-second probe printed no over-limit line
before it was killed, so what it actually says is that every document it reached finished
UNDER 20 seconds. A number taken while the box is swapping is not a number.

What IS measured cleanly, in seconds, repeatedly: `emit` over the named population of 981
takes 5.4 s and N is unchanged, so the committed tree's cost did not move — `emit` calls
`resolved` only for a document that EMITS, and no newly resolvable document emits. The ceiling
is real and documented; its size on this population is unmeasured and
`acp-sdkgen/codegen/resolved_cache.py` is the upgrade path the docstring already names. It is
also why the whole-population resolution test is a replica of the store loop with the inlining
left off, which the test says in as many words.

**On the bead's own scope.** The 34 / 88 / 966 / 76 reproduce exactly, and the three stated
non-causes hold under my instruments too. Two corrections: the resolution gate closes on **151**
documents and not 88, because `document_for`'s `if "#" in uri` matched a LOCAL reference as
well; and **311 is not reproducible by any of nine instruments** (listed in the baseline), so
the ~223 residual the bead asks about does not exist — the real gap is the 63 local-only
documents. The `None` was also not the only gate: the store key was the other half, and
removing the `None` alone would have left a fragment reference unresolvable with its target
already read in.

**Each half was broken on purpose**, and these are the tests that redden, all in
`tests/test_fragment_ref.py`:

| half broken | reddens |
|---|---|
| `resolved`'s call site stops splitting | the two resolution tests and both import tests (4) |
| `bind`'s call site stops splitting | both import tests and the chain-refusal test (3) |
| `named_nodes`' call site stops splitting | the naming test, the bundle-function test, the byte compare, the import test (4) |
| the store is keyed on the full URI | the inlining test and both import tests (3) |
| a local reference is looked up as a document | the local-resolution test (1) |
| the empty-store shortcut skips resolution | the local-resolution test (1) |
| a named node gets no symbol | the naming test, the bundle-function test, the byte compare, the import test (4) |
| `named_nodes` reads the run's documents | the same 4 |
| a fragment binds the target's root symbol | the import test (1) |
| two symbols at one pointer are ordered | the duplicate-pointer test (1) |
| the alias leaves its constraints on the property too | the naming test, the bundle-function test, the byte compare (3) |

Nothing is ungraded. The one test no probe reddens is
`test_no_portable_documents_reference_closure_names_a_document_this_bundle_lacks`, and that is
deliberate: it is a CENSUS over the bundle rather than a grader of any one line, so it reddens
on a bundle update that introduces a dangling reference and on nothing else.
