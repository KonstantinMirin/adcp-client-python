# salesagent-j3k2l.18 — the `allOf` shapes step 4's row defers

Started from `00c7dd4d47bf7fa6cb6eff1d14be8134febabff8` (`emit/from-scratch`), clean.
Baseline, re-measured in this tree rather than quoted: `emit` over all 1,054 portable
documents gives **401 emitted + 653 refused = 1,054**.

## 1. The population, measured before anything was built

The ticket says 65 documents and `41 / 15 / 9`. At this sha it is **67**, and the
split by POSITION is `41 / 10 / 16`. Both numbers are reported with the classifier
that produced them, because the ticket's did not travel with one:

* **root** — the refusal's pointer is `""`.
* **property** — the pointer is exactly `/properties/<key>`.
* **nested** — anything else (`/oneOf/0`, `/properties/x/items`, `/definitions/y`, …).

The 67 are every document `emit` refuses with keyword `allOf` and the deferral
detail `this step lowers no such keyword (a later D2 row does)` — i.e.
`compiler.check_keywords`, not `lower.product`'s own refusal. (A 68th document
refuses on `allOf` with a real reason: `VendorPricing is not a class, so it cannot
be a base`. It is not this population.)

### By position and by WHAT THE CONJUNCTS ARE

| n | position | the set of conjunct kinds at that node |
|---|---|---|
| 33 | root | bare `$ref` (a base) |
| 4 | property | bare `$ref` (a base) |
| 4 | property | a rule keyword: `if`,`then` |
| 3 | nested | a rule keyword: `else`,`if`,`then` |
| 3 | nested | a rule keyword: `else`,`if` + a rule keyword: `if`,`then` |
| 2 | nested | a rule keyword: `not` + bare `$ref` |
| 2 | nested | bare `$ref` (a base) |
| 2 | nested | a rule keyword: `if`,`then` |
| 2 | root | a rule keyword: `not` + bare `$ref` |
| 2 | root | a rule keyword: `if`,`then` + bare `$ref` |
| 1 | nested | a composition: `anyOf` + a rule keyword: `if`,`then` |
| 1 | nested | bare `$ref` + inline with `properties` |
| 1 | nested | a composition: `anyOf` + a rule keyword: `not` |
| 1 | nested | a rule keyword: `if`,`then` + bare `$ref` |
| 1 | root | a rule keyword: `if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` + a rule keyword: `if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` + `if`,`then` + `not` |
| 1 | property | bare `$ref` + inline `properties` + `additionalProperties`,`allOf` |
| 1 | property | bare `$ref` + inline with `properties` |

### Which ROW claims each refusing document

| n | position | claiming selector |
|---|---|---|
| 41 | root | `union_root` |
| 11 | nested | `union_root` |
| 10 | property | `is_object_root` |
| 3 | nested | `is_object_root` |
| 2 | nested | `composes_at_the_root` |

**All 41 root refusals are `union_root`'s.** Not one is `composes_at_the_root`'s:
that selector excludes a root carrying `oneOf`/`anyOf`, and `union_root` excludes
nothing, so a root carrying BOTH keywords is the union row's and `lower_union`'s
keyword screen refuses it on `allOf`. The deferral message is wrong about who defers
— step 4's row was never going to see these.

What the 41 compose: **37 conjuncts reference `core/version-envelope.json`** and
**33 reference `core/protocol-envelope.json`**. These are D7's envelope strata, on
the task-response documents D7 names.

**32 of the 41 have `allOf` as their ONLY live root conjunct** — 30 declare
`properties: {}` (present and empty) and 2 declare no `properties` at all. So for 32
documents the root `allOf` is the single thing between them and emitting.

## 2. THE UNIT, chosen from where the nodes sit

Three positions, two units, and **neither is a `ROWS` row**:

* **A nested or property-position `allOf` (26 documents) is not a root**, so it has
  no row and no selector — the bead's own note. The unit is **one arm on
  `emit._decide`**, beside the `$ref`, `enum`, typeless, null, multi-type, object,
  array and scalar arms, delegating to the lowering step 4 already has.
  `lower.product.lower_root` is already position-neutral: it takes `(doc, name,
  pointer, mod)`, reads the pointer, and `declare_object` names the node it is given.
  Nothing new is built; the function is renamed `lower_composition` because it is no
  longer only a root's.
* **A root `allOf` beside a root union (41 documents)** is a change in
  `lower/union.py`: `allOf` joins `ROOT_CONJUNCTS`, the mechanism that module already
  has for `properties` / `required` / `additionalProperties`.
* `ROWS` stays six rows. `bundle`'s selectors are unchanged.

## 3. WHY the 41 refuse rather than emit, and the probe that decides it

`lower_union` already refuses a root `properties`, `required` or
`additionalProperties`, for a reason about the GRADER and not about a missing
lowering: such a keyword is a conjunction with every branch, a branch class carrying
it states a fact its own `#/<kw>/<i>` node does not, and **there is no JSON pointer to
the conjunction for the branch to name**.

A root `allOf` is in that position exactly. If the conjuncts became bases of the
union base, every branch would inherit them (the branches subclass the base — §4), so
each branch class would carry `adcp_version`, `adcp_major_version`, `status`,
`context`, … while its own `#/oneOf/<i>` node states none of them.

This is a conflict between two parts of the closed plan, so it is measured and not
argued. **PROBE P1:** bind the root `allOf`'s bare-`$ref` conjuncts as bases on the
union base, emit `media-buy/create-media-buy-response.json` (one of the 32), and grade
the pair.

## 4. PREDICTIONS

Written before any code was changed or any probe run.

| # | prediction |
|---|---|
| P1 | The probe reddens. Every BRANCH class of `create-media-buy-response.json` reports `comparison:` with `added` > 0 — one `added` entry per inherited envelope property — and the branch's accepts check reports `model_refused_valid` as well, because `strict_validate` against `#/oneOf/0` draws an instance with no `status` while the class requires one. Two independent checks, both red. The BASE class (naming `#`) grades fine. |
| P2 | So 0 of the 41 emit. All 41 refuse on `allOf`, with `union_root`'s conjunction reason rather than the deferral message. `allOf` goes FIRST in `ROOT_CONJUNCTS`, so the keyword each of the 41 is reported on does not change and the by-keyword refusal profile keeps `allOf` at 68. |
| P3 | Of the 26 property/nested documents, the 8 whose conjunct kinds are a subset of {bare `$ref`, inline with `properties`} reach the lowering. I predict **5 of those 8 emit end to end** and 3 refuse on another keyword elsewhere in their own document. |
| P4 | The other 18 refuse on a non-deferral keyword: `if` for 12, `not` for 3, `anyOf` for 2, `additionalProperties` for 1. |
| P5 | N goes 401 → **406**; refused 653 → **648**; the sum stays 1,054. |
| P6 | `added` stays **0**, `missing` 0, `differs` 0 over the whole graded set. Graded pairs 462 → about **470** (the 5 documents' own classes plus any nested class a composition node declares). |
| P7 | No `ROWS` row is added and no `bundle` selector changes. Rows stay disjoint: 1,033 claimed once, 21 by none, 0 twice. |
| P8 | `tests/test_import_rule.py` stays green: the arm lives in `emit`, which already imports `lower.product`, and `product.py` gains no import. |

## 5. GRADE

**Every number below was measured at base `00c7dd4d4`**, in the worktree
`acp-j3k2l18`, with the baseline re-derived in a detached worktree at that same sha
(401 emitted / 653 refused, which is the bead's own figure). The trunk figures the
coordinator quotes — 406 / 648, 481 pairs, 395 modules — are from a tree carrying
`applied_schema` / `constrained_to_object`, which neither this branch nor
`emit/from-scratch`'s tip at `62b5e7ce2` contains, so none of my numbers is comparable
to them without the merge. §6 below says which of them the merge should move.

| # | prediction | measured | verdict |
|---|---|---|---|
| P1 | the probe reddens: every branch class reports `added` > 0, and the accepts check reports `model_refused_valid` | **UNGRADEABLE — the probe could not run.** Patching this row to bind the conjuncts as bases over all 41: **0 emit.** 35 refuse on the root `properties` below, 4 on a branch `not`, 1 on a branch `type`, 1 on `dependencies`. No branch class ever existed to grade, so `added` and the accepts verdict were never measured | **WRONG about being measurable.** The direction was right for the wrong reason: I predicted a red grade, and what I got was no grade at all |
| P2 | 0 of 41 emit; all 41 report `allOf`; the by-keyword profile keeps `allOf` at 68 | 0 of 41 emit ✓. **37 report `allOf`, not 41**: adding `allOf` to `ROOT_HANDLED` lets the keyword screen reach past it, so 3 move to `not` and 1 to `dependencies`. `allOf` goes **68 → 48** over the bundle | **HALF WRONG.** The emission count held; the attribution claim did not, and "the profile does not move" was simply false |
| P3 | 5 of the 8 lowerable property/nested documents emit | **2**: `core/attribution-window.json` and `core/outcome-measurement.json` | **WRONG**, and over-optimistic by 3 |
| P4 | the other 18 refuse `if` 12 / `not` 3 / `anyOf` 2 / `additionalProperties` 1 | over the 26: `allOf` 10 (9 at a branch, 1 "not a class"), `if` 6, `$ref` 6, `anyOf` 1, `additionalProperties` 1, emits 2 | **WRONG.** I did not predict the `$ref` CHAIN refusals at all — 6 documents whose composition now lowers and whose target is refused — and I did not foresee that 9 would land at a union branch, which `_decide` never reaches |
| P5 | N 401 → 406, refused 653 → 648 | **401 → 403**, refused **653 → 651**, sum 1,054 | **WRONG**, by 3 |
| P6 | `added` 0, `missing` 0, `differs` 0; pairs 462 → about 470 | see the suite line in §7 | — |
| P7 | no row added, no selector changed; rows stay 1,033 / 21 / 0 | `ROWS` is still six rows; `codegen/bundle.py` is untouched | **RIGHT** |
| P8 | `test_import_rule` stays green | `product.py` gained no import; the composition is reached from `emit`, which already imported it | **RIGHT** |

**Score: 2 right, 4 wrong, 1 ungradeable, 1 deferred to the suite.** The two
structural predictions held and every quantitative one was wrong. The sharpest
correction is P1: I wrote a prediction about what a probe would GRADE without first
asking whether the probe had a population, and it had none.

## 6. The design gap, and the mechanism that is already closing it

**Group A's 41 documents cannot be emitted, and the reason is not step 4's.** A root
`allOf` is a conjunction with every branch of a root union. If the conjuncts become
bases of the union base, every branch inherits them (the branches subclass the base —
§4), so each branch class states facts its own `#/<kw>/<i>` node does not. §6 pairs a
class with a JSON POINTER, and the conjunction of `#/allOf/*` with `#/oneOf/<i>` is at
no pointer. This is a direct conflict with D7, which shows a branch class
(`CreateMediaBuyResponse1`) inheriting `AdcpVersionEnvelope` and `ProtocolEnvelope` —
and 37 of the 41 reference `core/version-envelope.json`, 33
`core/protocol-envelope.json`, so this is the bulk of D7's envelope story.

**What the design did not take into consideration: a SchemaRef is a JSON pointer, and
a conjunction is not at one.** §6 assumes every class a row declares names a node the
pointer vocabulary can address. It does for a leaf, a nested object and a branch of a
BARE union; it does not for a branch of a union whose root also asserts something
about the same instance.

**That is the KNOWN CEILING trunk has already named.** `_base.applied_schema`
(`5e4a02e34`) makes a SchemaRef resolve to the node AS THE DOCUMENT APPLIES IT, and its
own docstring says:

> `type` is the ONE fact conjoined … every such node a class is declared at today is a
> union branch — `lower.union.ROOT_CONJUNCTS` refuses a union root that carries
> `properties`, `required` or `additionalProperties`, so `type` is the only assertion
> such a root can make about the instance. KNOWN CEILING: a row whose root asserts more
> than a type about the same instance needs this extended.

So the upgrade path is not in step 4 and not a seventh row: **widen `applied_schema`
from conjoining the enclosing `type` to conjoining everything the enclosing node
asserts unconditionally about the same instance** — its `allOf` conjuncts, its
`properties`, `required` and `additionalProperties`. Then `#/oneOf/<i>` as applied does
carry the envelope facts, the branch class grades, `ROOT_CONJUNCTS` shrinks to nothing
and all four of its entries stop refusing. This change makes that argument STRONGER
rather than weaker: with `allOf` in `ROOT_CONJUNCTS`, `type` remains the only assertion
a union root can make about the instance, which is the premise `applied_schema` rests
on.

**One number of mine the merge should move.** P1's "0 of 41" was measured without
`applied_schema`. Asking the DOCUMENTS instead of the tree — the rule applied by hand,
verbatim from `5e4a02e34` — **17 of the 41 have at least one branch that trunk's rule
repairs**, `brand/verify-brand-claim-request.json` among them (root `type: object`, all
four branches gain an applied type). That document is the only one of the 32 whose
conjunct targets all emit today, so on the merged tree the probe acquires a population
and "0 of 41" must be re-run. The grader argument is untouched by that: `applied_schema`
conjoins `type` alone, so a branch still states the envelope fields its node does not.

**Not affected: every composition this branch lowers owns its own instance.** Measured
over the whole portable population — 307 compositions lowered, 287 at a root and 20
below one, and 0 of the 20 at a shared-instance position (12 `properties/<key>`, 7
`items`, 1 `definitions` entry). The nearest miss is
`core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items`, whose
pointer crosses a branch two instances up and whose own node is an array element. So no
node this branch reads in isolation is a node the document constrains from outside.

## 7. The fire probes, and one that refuted my own reasoning

Each change was made to FAIL, and the emitter re-measured over all 1,054 documents.

| probe | what was removed | measured |
|---|---|---|
| (a) | the `_decide` composition branch | 403 → **401** emitted, deferral refusals 210 → **226**. Load-bearing: it is what emits the 2 and what moves 16 documents off the deferral |
| (b) | `allOf` from `ROOT_CONJUNCTS`, with the keyword screen still admitting it | **403 / 651 — unchanged. 0 new emissions.** Only the deferral count moves, 210 → 211 |
| (c) | the branch-`allOf` refusal, lowering each branch with its conjuncts DROPPED | **403 / 651 — unchanged. 0 new emissions.** Deferral count 210 → 213 |

**Probe (b) refutes the way I was justifying that entry.** It prevents no widening
today, because nothing emits either way; what it changes is the REASON 37 documents
are refused. The widening it forecloses is real but not yet reachable: it arrives at
the first branch repair, and `applied_schema` alone unblocks a branch in 17 of the 41.
Without the entry such a document emits a base that drops its composed bases — which
the comparison catches as `missing`, so a red gate rather than a named refusal. Stated
that way in the code rather than as a widening it prevents now.

**Probe (c) refutes my §6 claim that 2 of the 9 would emit.** With the conjuncts
dropped — which is exactly what the compiler hoist would supply — **0 of the 9 emit.**
They refuse on `uniqueItems` (3), a `$ref` chain (2), a branch `type` (2), an `allOf`
whose base is an alias (1) and a class-name collision (1).

## 8. What I declined to build, and why

**The 9 branch-position compositions.** A branch carrying `allOf` is genuinely
lowerable — the conjuncts sit at the branch's own node, so `harness._composed` folds
them in and the grader has a pointer for every fact. What it needs is the conjuncts
BOUND, and the conjunct reader is the product row's: D13 forbids a lowering importing
another lowering, so landing it means hoisting that reader into `codegen/compiler.py`.
That is what D13 prescribes, and I did not do it — and probe (c) is why rather than
the merge risk I first reached for: **the reachable population is 0.** A ~130-line
move out of a closed step's module, for a derivation that matches nothing, is the
shape D14 names. The step whose own keyword unblocks one of these 9 — `uniqueItems`
(`salesagent-j3k2l.19`) and `applied_schema`'s branch-`type` repair are the two
nearest — is the step that should make the move. The refusal names the mechanism
instead of promising a row.

## 9. The suite

Never run on this branch. The agent that wrote §1–§8 stopped with this section empty
and its tip commit banked as `wip(codegen): bank j3k2l18's uncommitted lane work
unverified`. Everything above is measured at base `00c7dd4d4`, which is 61 commits
behind trunk `29c553504`, so none of it is a statement about any tree that exists now.

---

# 10. RESUMPTION — a new agent, 2026-10-23

The change this row needed **already exists on this branch**. So this section does not
open with a prediction about it: predicting what is already written and already
measurable would be a probe built to confirm its own hypothesis. §10.1 is MEASUREMENT,
taken before anything was edited. §10.2 is the prediction, and it is about the things
that are genuinely still unknown — the regeneration, the four stale constants, and
whether the merge broke anything it does not touch.

## 10.1 Measured first: the two trees, same instrument

Both numbers come from one script run against two checkouts, through
`emit.emit(bundle.portable(BUNDLE))` and the refusal producers' own constants
(`refusal.DEFERRED_TO_A_LATER_ROW`, `refusal.UNRESOLVED_TARGET`,
`refusal.is_a_verdict`) — never a regex over a detail string. Dependency pins are
byte-identical across `00c7dd4d4..29c553504` for `pyproject.toml` and `uv.lock`, so one
venv serves both trees and the comparison is not an environment difference.

| | trunk `29c553504` | merged `5f602c4b1` | delta |
|---|---|---|---|
| portable | 1054 | 1054 | 0 |
| emitted | 578 | 580 | **+2** |
| refused | 476 | 474 | −2 |
| **deferred** (pin ≤ 176) | **176** | **102** | **−74** |
| transitive (pin ≤ 1) | 1 | 1 | 0 |
| verdicts | 299 | 371 | +72 |
| **accounted** (pin ≥ 877) | **877** | **951** | **+74** |
| pending | 177 | 103 | −74 |

**The 82 `allOf` deferrals are gone — all 82, measured by name.** Trunk defers 82
documents on `allOf`; the merged tree defers **0**. Their disposition partitions
exactly:

| n | what became of it |
|---|---|
| 2 | **emitted** |
| 72 | **a verdict** — refused on a keyword this emitter will not lower |
| 8 | still pending, but on ANOTHER keyword a later row owns: `not` +3, `dependencies` +2, `anyOf` +1, `oneOf` +1, `items` +1 |
| **82** | and 2 + 72 + 8 = 82 |

So the row claims all 82 and **74 of them become accounted-for**. The 8 that remain
pending are not this row's to claim: each is a document whose `allOf` now lowers and
which then stops at a different keyword, which is the keyword that is now the reason.

**Where the 82 sat, which is what decided the unit.** 66 nested, 16 at a property,
**0 at a root** — so no row and no selector could have claimed them, and the unit is an
arm on `emit._decide`. The claiming selectors are `union_root` 54, `is_object_root` 23,
`composes_at_the_root` 5: three root kinds, which is exactly why a single row was the
wrong unit (D13 forbids a lowering importing `codegen.emit`, so a row cannot dispatch
three root kinds itself). This is the same correction the issue's own note records for
`.20` and `.16`, and it is confirmed here by measurement rather than inherited.

The coordinator's brief estimated accounted would reach "about 959". It reaches **951**.
The 8-document difference is precisely the 8 above — the brief's estimate assumed all 82
would become accounted-for, and 8 of them stop at a later row's keyword instead.

## 10.2 The predictions, written before the regeneration and the pin edits

Each is about something not yet measured on this tree.

| # | prediction |
|---|---|
| R1 | `test_the_committed_tree_is_what_a_fresh_run_emits` is RED at the merge commit `5f602c4b1`, because both sides moved the generator and neither re-derived the tree. The regeneration ADDS modules and changes no existing one: trunk's committed tree holds its 578, this branch committed `core/attribution_window.py`, and the merged emitter emits 580 — so I expect exactly **1 module added**, `core/outcome_measurement.py`, which §5's grade names as the second of the two documents that emit. If more than one file is added, or any existing file's bytes change, R1 is wrong. |
| R2 | The graded-pair count rises from trunk's 503. `core/attribution-window.json` contributed 3 pairs when measured alone (§5), so I predict **pairs in 506–512** and `pass` rising by the SAME amount, with `no_constraint_to_step` unchanged at 12 and **added 0, missing 0, differs 0** throughout. The symmetric comparison is the thing most likely to catch a composition lowering that inherits a fact the node does not state, so a non-zero `added` here would be the sharpest possible refutation. |
| R3 | The union-root by-keyword profile keeps `allOf` at trunk's **54**, unchanged. The root-conjunct refusal and the branch-composition refusal both report `allOf`, which is the keyword the screen reported before, so the attribution does not move for a root union. |
| R4 | `test_emit_product.py`'s three constants move UP a little and the row's own delta does not: `with_row.emitted` 238 → **239 or 240** (the below-root composition lets the transitive walk reach past a property `allOf` into targets it stopped short of), `with_row − without` 46 → **47 or 48**, and `composing() ∩ emitted` **unchanged at 34**, because that set counts compositions at a ROOT and this arm claims none. |
| R5 | Nothing else reddens. No guard, no import rule, no other suite file — specifically `tests/test_import_rule.py` stays green, because the arm lives in `emit`, which already imports `lower.product`, and `product.py` gains no import. A branch can redden a guard in a file it never touched, so this is a real prediction and not a formality. |
| R6 | The two pins become **deferred ≤ 102** and **accounted ≥ 951**, set to the values measured in §10.1 and not left loose. `transitive` stays at ≤ 1. |

## 10.3 GRADE

<!-- grade -->
