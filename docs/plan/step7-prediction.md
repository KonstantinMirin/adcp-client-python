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
