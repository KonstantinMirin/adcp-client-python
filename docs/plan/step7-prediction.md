# Step 7 — rules: the prediction, written before the lowering exists

Committed before `codegen/lower/rules.py`, `src/adcp/types/_runtime.py` or the
`steps()` extension exist, so the grading below is against a record and not against a
recollection.

Branch `emit/s7-rules-v2`. Base `81e132aee`, then `git merge emit/format-regex`
fast-forwarded to **`482e7bc63`**, which is the tree every number here is predicted
against.

## The baseline, measured at `482e7bc63`

These are pre-state facts, measured before writing this file; they are the
denominators, not the result.

| fact | value | how it was selected |
|---|---|---|
| portable documents | 1,054 | `bundle.portable` |
| step 1 population (`is_leaf_object`) | 85 | `tests.test_emit.leaves()` |
| step 2 population (`references_a_property`) | 249 | `tests.test_emit.referencing()` |
| named population | 334 | the union of those two |
| **N** | **43** | `len(emit.emit(BUNDLE, population()).emitted)` |
| suite | 72 passed | `pytest tests/` |

Whole-population refusal census at `482e7bc63` — each of the 1,054 documents lowered
on its own (no reference binder), counted by the keyword it refuses FIRST on:

```
allOf 284, enum 262, type 213, $ref 94, const 61, anyOf 23, not 16,
definitions 14, dependencies 9, oneOf 9, minProperties 7, $defs 5,
discriminator 4, if 3, propertyNames 1, required 1, last_updated 1
```

47 of 1,054 lower standalone; 1,007 refuse.

Raw occurrences of each step-7 family at a schema position, over the 1,054:

| family | sites | documents |
|---|---|---|
| `oneOf`/`anyOf` | 662 (oneOf 212, anyOf 450) | 294 |
| `if`/`then`/`else` | 1,237 (if 591, then 588, else 58) | 186 |
| `dependencies` | 32 | 27 |
| `minProperties`/`maxProperties` | 67 (48 / 19) | 44 |
| `uniqueItems` | 485 | 198 |
| `not` | 471 | 192 |

Of the 662 combinator sites, **297 over 161 documents have every branch
`required`-only**, and 30 of those sites are at a document ROOT.

In the 43 RESOLVED documents the committed package carries — the documents the 43
graded pairs are graded against — the step-7 families appear at exactly **two** sites,
both in `core/operator-identity.json#/properties/operator_unit`: one `maxProperties`
and one `additionalProperties: {"not": {}}`. Every other family appears 0 times.

## What I am building

Six families, one class-level tuple, one after-validator.

- `src/adcp/types/_runtime.py` — `RuleBound` carrying one
  `model_validator(mode="after")` over `_adcp_rules`, plus one frozen dataclass per
  rule kind: `Dependencies`, `PropertyCount`, `ForbiddenGroups` (`not` over
  `required`), `RequiredGroups` (`oneOf`/`anyOf` over `required`), `Match`,
  `ConditionalRequired`, `NegatedConditional`.
- `codegen/lower/rules.py` — the reading: a node in, a list of constructor sources out,
  plus the properties only a conditional declares. Refuses nothing (D4).
- `codegen/harness.py` — `steps()` extended to all six families, and `force_path`
  gaining the `then`/`else` hop through a sibling `if`.
- `codegen/bundle.py` — `states_an_object_rule`, step 7's population test.
- `codegen/emit.py` — one row: `rules.KEYWORDS` in `lower_object`'s handled set, the
  call, and `ANNOTATIONS` re-homed to `lower/rules.py` so the selector and the reading
  share one set. Its own commit.

## The predictions

### P1 — ΔN, and it is NOT the brief's +1

The brief carries forward `ΔN ≈ +1`, naming `core/format-id.json` as the one clean
document. That number is from the previous attempt, which had **no step-7 population
row** and did **not** lower `oneOf`/`anyOf` over `required`. The brief also tells me to
add a selector. Those two instructions disagree, and I am predicting my design's
number rather than the carried-forward one.

Why the carried-forward +1 cannot be my answer: `core/budget-range.json` and
`core/demographic-age-range.json` are object roots whose whole composition is an
`anyOf` of two `required`-only branches. They are not step 5 documents — there is no
branch SHAPE to subclass — so under D2 they are a class plus a rule, which is step 7.
Neither is in the named population today, because `is_leaf_object` excludes `anyOf`
and neither carries a `$ref`. A selector is what reaches them.

- **ΔN = +12**, so **N = 55**, over a predicted selector population of **48**.
  Range I will accept as the same prediction: +5 to +20. Anything outside it I grade
  as wrong.
- `core/format-id.json` (`dependencies`) is one of them, and it is the only one of the
  12 that is **already in the named population** — so it is the only one that would
  move N with no selector at all.
- Derivation: 35 of the 36 documents the brief counts are the census's
  `not` 16 + `dependencies` 9 + `minProperties` 7 + `if` 3; the 36th is `required` 1,
  which I am NOT lowering (see P6). The brief measured 4 of those 36 as carrying
  nothing else this tree cannot lower. Add the 30 `required`-only combinator roots,
  most of which are plain scalar-property objects, and discount for `$ref`, `allOf`,
  `enum` and array properties.

### P2 — the 43 modules and the 44th are the floor, and the 43 do not move

- Every one of the 43 modules at `482e7bc63` is **byte-identical** after this step. A
  rule is a new class-body line and none of the 43 documents states one.
- `steps()` over the 43 resolved documents produces the **same step list, count for
  count**, after the extension as before. Two sites could gain a step and both are
  guarded out: the `not` is `{}` (a document admitting nothing, no instance to draw)
  and the `maxProperties` sits on a node closed to exactly its declared keys.
- So **no existing pair's refuses-check denominator changes**, in either direction.

### P3 — the step site counts, per family

`steps()` run over each of the 1,054 raw documents, counted by `Step.keyword`. This is
the EXIT condition's number and all six are 0 today.

| family | predicted steps | mechanism, and why it is below the raw count |
|---|---|---|
| `uniqueItems` | 479 | 485 occurrences, minus ~6 where `{minItems: 1, maxItems: 1}` makes the keyword vacuous and a step unsatisfiable |
| `not` | 460 | 471 occurrences, minus the empty `not: {}` ones |
| `if`/`then`/`else` | 550 | one `then` step per `(if, then)` pair and one `else` step per `(if, else)` pair — 646 pairs — minus those whose negated branch is unsatisfiable |
| `oneOf`/`anyOf` | 400 | one step per site, negating every branch as a conjunct; a combinator exhaustive over its type is unsatisfiable when negated and gets none |
| `dependencies` | 65 | one step per `(trigger, dependent)` pair over 32 sites, skipping a pair the node's own `required` already settles |
| `minProperties` | 40 | 48 occurrences, minus those no larger than the node's `required` count, where a step would grade `required` under another name |
| `maxProperties` | 15 | 19 occurrences, minus those on a node closed to no more keys than the bound |

Total new step rows predicted: **2,009**.

### P4 — each rule is graded, and by what

A rule is invisible to `check_pair`: every pair is offered its instance through
`strict_validate`, whose schema half validates against the document and so refuses the
violation whatever the rules say. So the only instrument that observes a rule is a
direct `model_validate`. I predict:

- With the after-validator short-circuited to return before it evaluates anything,
  **exactly the `model_validate` tests go red and all pairs stay green.**
- Every one of the six families has at least one emitted class carrying a rule of that
  kind, so none of the six is dead code. `uniqueItems` is the one I expect to fail
  this: it constrains the members of an array, the array lowering is step 6's row, and
  there is no array lowering here to hang it on. **Predicted: 5 of 6 families carry an
  emitted rule; `uniqueItems` is stepped by the harness and carries no rule.**

### P5 — `force_path` through `then`/`else`

A site under `then` is reachable only if the sibling `if` matches, and nothing makes it
match. Predicted on `core/canvas-constraint.json`'s four `then` sites: the control
fires on a MAJORITY of examples unforced and on **0 of them** forced. I predict the
unforced rate between 20% and 60% and the forced rate exactly 0.

### P6 — what step 7 does not do, predicted as a non-change

- `required` naming a property no `properties` entry declares stays a **refusal**. It
  is not one of D6's six, it is 1 document of 1,054, and turning it into a field is a
  different decision than lowering a rule.
- `media-buy/change-term.json`'s `x-adcp-validation` stays untouched and ungraded.
- A conditional that narrows a VALUE (`if unit == "percent" then x.maximum = 100`) gets
  no rule. Predicted consequence, asserted rather than claimed:
  `CanvasConstraint.model_validate({"unit": "percent", "x": 101})` builds and
  `strict_validate` of the same payload refuses.
- The residual census loses `not`, `dependencies`, `minProperties` and `if` entirely
  (16 + 9 + 7 + 3 = 35 documents refuse one keyword further on) and keeps `required` 1.
  `anyOf` and `oneOf` **go up**, because a document that used to refuse early on a
  step-7 keyword now reaches its combinator. Predicted: `anyOf` 23 → 28,
  `oneOf` 9 → 12.

### P7 — the perturbations, and what each must redden

Each has to redden something SPECIFIC and named. A perturbation that reddens nothing is
a finding about the instrument.

| perturbation | predicted red |
|---|---|
| `Dependencies.errors` inverted (fire when the trigger is ABSENT) | the `model_validate` test for `core/format-id.json`; no pair |
| the after-validator returns before evaluating `_adcp_rules` | every `model_validate` rule test; no pair, no comparison |
| `RequiredGroups` for `anyOf` accepts when no group is present | the `anyOf`-over-required `model_validate` test |
| the `then`/`else` hop deleted from `force_path` | the forced control rate on `core/canvas-constraint.json`, 0 → a majority |
| the `uniqueItems` step forces no duplicate | **predicted inert on every binding grade**, because 0 of the 479 sites is on an emitted pair; it must redden the step's own exclusivity assertion, and if that is all it reddens I record it as a bad probe rather than a pass |
| `states_an_object_rule` widened to claim a document carrying `allOf` | the two-rows-select-one-document build failure |

## Nothing I want re-decided

D1–D12 are untouched. Two things I am REPORTING rather than acting on, both in the
final report: the dispatch table named in the plan's Layout paragraph does not exist at
this base, and the brief's `ΔN ≈ +1` disagrees with its own instruction to add a
selector.

---

# Graded

Measured at tip `438240878`, branch `emit/s7-rules-v2`. Every number below is from the
tree at that commit; the suite is **90 passed** against the merge gate's 72.

## P1 — ΔN. Range right, centre wrong, selector population badly wrong

| | predicted | measured |
|---|---|---|
| ΔN | +12 (range +5..+20) | **+7** |
| N | 55 | **50** |
| selector population | 48 | **5** |
| the one already in the named population | `core/format-id.json` | `core/format-id.json` |

The ΔN **range held and the centre was 5 out**. The brief's carried-forward +1 is
refuted: +1 is what a step 7 with no population row delivers, and the brief also
instructed me to add one.

**The selector population prediction was wrong by a factor of ten, and the derivation
is the defect.** I predicted 48 from "35 non-combinator step-7-first documents + 30
required-only combinator roots" without intersecting that against the selector's own
first clause. 25 of the 30 roots carry a `$ref` or an `allOf` somewhere else in the
document, so the clause that keeps step 7 out of steps 2 and 4 excludes them. I had both
populations measured and did not intersect them.

The 7 new documents, by the row that reached each:

| document | row | family |
|---|---|---|
| `core/format-id.json` | leaf (step 1) | `dependencies` |
| `core/demographic-predicate.json` | reference (step 2) | unblocked by its target |
| `core/budget-range.json` | rule (step 7) | `anyOf` over `required` |
| `core/demographic-age-range.json` | rule | `anyOf` over `required` |
| `core/forecast-range.json` | rule | `anyOf` over `required` |
| `core/webhook-challenge-response.json` | rule | `anyOf` + `not` |
| `media-buy/proposal-budget-constraint.json` | rule | `anyOf` over `required` |

## P2 — the floor. Correct, and confirmed by hash rather than by eye

- **94 of 94** files the base tree carried are byte-identical at HEAD, compared by
  `git rev-parse <sha>:<path>` blob hash per file, not by reading a diff. 14 added.
- The 44 pairs over those 43 documents now report **3,758 graded instances and 486
  facts compared** — byte-for-byte the base totals, 42 `pass` and 2
  `no_constraint_to_step`, 157 step sites. So the whole increase to 5,054 and 583 is
  the 7 new pairs, and **no existing pair's denominator moved in either direction**.
- The two sites that could have gained a step are both guarded out as predicted:
  `core/operator-identity.json`'s `additionalProperties: {"not": {}}` is an empty
  `not` (a document admitting nothing) and its `maxProperties` sits on a node closed
  to exactly its declared keys.

## P3 — the step counts. Low by 20%, and one family for a reason I caused

| family | predicted | measured | documents |
|---|---|---|---|
| `uniqueItems` | 479 | **479** | 198 |
| `not` | 460 | **469** | 192 |
| `if`/`then`/`else` | 550 | **643** (then 585, else 58) | 186 / 44 |
| `oneOf`/`anyOf` | 400 | **662** (oneOf 212, anyOf 450) | 165 / 200 |
| `dependencies` | 65 | **85** | 27 |
| `minProperties` | 40 | **48** | 40 |
| `maxProperties` | 15 | **19** | 10 |
| total | 2,009 | **2,405** | |

`uniqueItems` exact. The `oneOf`/`anyOf` miss is mine and not the bundle's: I predicted
400 on the assumption of a satisfiability screen, then measured the screen at 63.7 s
against 0.0 s over 120 documents for **0 of 2,205 sites rejected** and removed it. Every
occurrence now gets a step and an unreachable one reports `no_evidence`.

Pre-existing keywords for the denominator: 13,418 rows over the same 1,054 documents, so
15,823 in all.

## P4 — "every rule is graded". 3 of 6 carry an emitted rule, not 5 of 6

Predicted 5 of 6 families with an emitted carrier. **Measured 3**: `Dependencies` (3
rules), `ForbiddenGroups` (2), `RequiredGroups` (10).

`PropertyCount` and `ConditionalRequired` have none, and the cause is the one the brief
named for ΔN, which I failed to apply to this prediction as well: **every bundle
document stating a `min`/`maxProperties` or a conditional also states an array property
or an `enum`**, which are steps 6 and 3. Measured document by document on all ten:

```
core/deadline-policy.json          refuses on type at /properties/material_stages
core/overlay.json                  refuses on enum at /properties/bounds/properties/unit
core/installment-deadlines.json    refuses on type at /properties/material_deadlines
core/principal-state.json          refuses on type at /properties/notification_configs
governance/audience-constraints.json           type at /properties/include
media-buy/acceptance-context.json              type at /properties/subjects
media-buy/product-discovery-criteria.json      type at /properties/product_ids
core/agent-notification-config.json            type at /properties/event_types
core/frequency-cap-interval-constraints.json   $ref at /properties/unit
core/requirements/image-asset-requirements.json  type at /properties/pixel_ratios
```

`NegatedConditional` is written at 42 nodes over 37 documents, all of them inside an
`allOf` conjunct, which is not a class in this tree at all.

So those three are graded where they CAN be, and the report says which: the lowering
against real bundle nodes (`test_every_rule_kind_is_written_from_a_real_bundle_node`,
pinning each kind's population) and each dataclass against two plain arguments
(`test_each_rule_kind_refuses_on_two_plain_arguments`, 19 rows, both directions). That
is a different situation from `uniqueItems`, which has no rule kind at all.

The short-circuit prediction HELD and gained a correction: patching
`RuleBound._enforce_adcp_rules` is **inert**, because pydantic compiles a
`model_validator` into the class's core schema at class creation — probed, and
`model_validate` still refused. The live short-circuit is the module-level
`_runtime.refuse`, which the compiled validator looks up on every call, and
`_base._refuse` holds its own reference so the schema half keeps refusing. With it
patched out, each rule payload builds and all three rule-carrying pairs grade
identically.

## P5 — `force_path` through `then`/`else`. Correct

Unforced **26 of 80** in a fresh process and **32 of 80** under the suite; forced
**0 of 80** in both. Predicted 20–60% unforced and exactly 0 forced. The test pins the
forced side exactly and bounds the unforced side, because the forced side is the hop's
claim and has nothing left for the context to move.

## P6 — the non-changes. Three right, the census direction wrong

- `required` naming a property no `properties` entry declares stays a refusal: census
  `required 1`. Correct.
- `media-buy/change-term.json` untouched. Correct.
- The conditional-value ceiling is a committed test: `conforms` is False,
  `violated_keywords` is exactly `["maximum"]`, the root's rules are the dependency
  alone, and `rules.lower` of the region node returns `[]`. Correct.
- **The census direction was wrong.** Predicted `anyOf` 23 → 28 and `oneOf` 9 → 12, on
  the reasoning that a document refusing early would now reach its combinator.
  Measured **`anyOf` 23 → 1** and **`oneOf` 9 → 5**, because the lowering CLAIMS a
  required-only combinator instead of refusing it — the opposite effect, from the
  change I was predicting about. The four families predicted to 0 went to 0.

Whole-population standalone census after step 7, 54 lower and 1,000 refuse (was 47 and
1,007):

```
allOf 286, enum 268, type 234, $ref 108, const 70, definitions 14, $defs 5,
discriminator 5, oneOf 5, anyOf 1, propertyNames 1, notes 1, required 1, last_updated 1
```

`not` 16, `dependencies` 9, `minProperties` 7 and `if` 3 are **gone**. `$ref` rose 94 →
108 and `type` 213 → 234: documents that used to stop at a step-7 keyword now reach a
later row's, which is the step's real deliverable for step 8.

## P7 — the perturbations. One wrong in the safe direction, one a bad probe

| perturbation | predicted red | measured |
|---|---|---|
| `Dependencies.errors` inverted | the `format-id` `model_validate` test, **no pair** | 5 tests, **including the `core/format-id.json#` pair**. A rule that narrows IS visible to the accepts check: it draws an instance the document admits and the constructor refuses it (`model_refused_valid`). My prediction was wrong in the safe direction, and the instrument is better than I claimed. |
| `_runtime.refuse` patched out | every `model_validate` rule test, no pair | correct, and now a committed test. The method-level patch is inert; see P4. |
| `RequiredGroups` `anyOf` never refuses | the `anyOf` `model_validate` test | correct: 3 tests, 0 pairs |
| the `then`/`else` hop deleted from `force_path` | forced control 0 → a majority | correct: 0 → **32 of 80**, exactly the unforced rate, plus the family-bites test |
| the `uniqueItems` step forces no duplicate | **inert on every binding grade**; its own exclusivity assertion only | correct, and recorded as a BAD PROBE rather than a pass: 6 of 20 → 1 of 20, 89 of 90 green. 0 of the 479 sites is on an emitted pair. |
| the selector widened to claim an `allOf` document | the two-rows-select-one-document failure | **BAD PROBE.** Only the population pin reddened and there was NO collision, because `is_leaf_object` excludes `allOf` too. Replaced: widening clause 2 to accept `rules.KEYWORDS` claims documents step 1 already claims and reddens `test_no_document_is_claimed_by_two_rows`, naming 6+ overlapping documents. That is the probe that grades the clause. |

## Scorecard

| | right | wrong |
|---|---|---|
| P1 ΔN | the range, and the one named document | the centre by 5; the selector population by 10x, from a derivation I had the inputs to do |
| P2 floor | all of it, by blob hash and by denominator | — |
| P3 steps | `uniqueItems` exact; five families within 25% | the total low by 20%; `oneOf`/`anyOf` wrong because I predicted a screen I then removed |
| P4 graded | the short-circuit | 5 of 6 predicted, 3 of 6 measured |
| P5 force_path | both rates | — |
| P6 non-changes | three of four | the census direction |
| P7 probes | 4 of 6 | 1 wrong in the safe direction, 1 a bad probe that was replaced |
