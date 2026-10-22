# Prediction: a step whose mutation a sibling keyword defeats

`salesagent-j3k2l.13`. Written and committed before the fix is measured, so the grading below
cannot be retrofitted. `docs/plan/rebuild-plan.md` §6 is the contract.

Started from `emit/from-scratch` at **fc9a880594caac2c01ee7a663d848528c80bdb49**, clean tree,
on branch `sdk/j3k2l13-exclusive-step`. Four tests are red at that sha — three step tests of
the D13 seam and the refuses lane's own — because `codegen/harness.py` was auto-merged and both
sides had changed it. The integrator diagnosed that and partitioned it; two stale constants and
the whole-population metric constant are theirs, not mine.

## What I measured before predicting, each number with its population

Three facts, because each one moves what the fix has to be. The instrument for all three is
`codegen.harness` at the starting sha, documents resolved by `bundle.resolved`, strategies drawn
exactly as `check_refuses` draws them.

**1. None of the bead's documents is in the graded population.** `graded()` is 448 pairs over
**383 documents**; **0 of the 13 documents** the bead names appears in it. So "each one refuses
its pair today" is not a statement about the 448-pair metric — those documents have no pair
yet. They block step 9, which is what the bead's first line says.

**2. The bead names 13 documents, not 14.** Its own list has 13 rows summing to 19 sites
(4 + 3 + 2 and ten 1s). Reported, not re-decided.

**3. The 19 is a sample, not the inventory.** The bead measured the **four steps `check_pair`
samples by its own spread**, so a document contributes at most 4. Over **all** steps of the
9 documents whose probe has returned, **44 sites** will not generate, against 19 for the whole
13 under the spread. `core/reference-renderer.json` alone is 14 of 17 steps.

**4. The causes are not the one the bead names.** Partitioned over those 44, in this order:

| cause | what it is | count / 44 |
|---|---|---|
| `document` | the ORIGINAL resolved document does not generate either, so no step over it can | 14 (all of `core/reference-renderer.json`) |
| `position` | another position at the same instance location still states a contradicting keyword — an `allOf` conjunct's own `enum`/`minimum`, or a grouped `then` holding several different conditions | 29 |
| `node` | a sibling keyword AT THE STEPPED NODE defeats the mutation — **the bead's stated mechanism** | **0** |

The one site that generates after a same-node drop
(`protocol/sync-agent-notification-configs-request.json#/properties/notification_configs`,
`maxItems 16 -> exactly 17`, dropping `items`) is not a contradiction: `items` is a complex
object schema and 17 draws of it over-filter. Dropping it buys generation cost, not
satisfiability.

**So I will not write a generic same-node sibling-dropping mechanism.** It is measured at 0 of
44 sites, and `maxLength`, `minLength`, `enum` and `maxItems` already pop their own colliders by
hand where it mattered. Writing the general case would be a mechanism with no population.

## What the fix is instead

**One: the catch site cannot tell two shapes apart, and that is the design conflict.**
`check_refuses` catches `Unsatisfiable` once. Step 7 needs it recorded as `no_evidence` (an
`if`/`then` whose condition implies its branch; a combinator exhaustive over its own type), and
the refuses lane needs it reported as `harness_error` (a `maxLength` stepped up against a
conjunct's `const`). Both have a passing test on their own branch and neither may move.

The distinction I expect to write is **what the rewrite CONSTRUCTS**. Five step families —
`not`, `then`, `else`, `anyOf`, `oneOf` — rewrite the site to the document's own statement
NEGATED, which is exactly the set of instances the document refuses there. Nothing of the
harness's choosing enters it, so an empty result is the DOCUMENT's property: no instance
violates that keyword at that site, which is `no_evidence`. Every other family substitutes a
bound the harness CHOSE (`maxLength n` becomes "exactly n+1", `minimum n` becomes
"maximum n-1"), so an empty result is a property of that choice and says nothing about the
document — a harness limitation, which is `harness_error`. The flag is set by the emitting
branch, which is the only place that knows which it built.

**Two: name the collider on every reported site.** A `harness_error` from this cause will carry
the keywords stated at the same INSTANCE LOCATION that the step did not rewrite —
`/allOf/0/properties/label:const` for the fixture, the three `then` branches' `const`/`minimum`
for `core/macro-encoding.json#/properties/depth`. An empty list is itself the signal that
nothing at that location contradicts the step and the document does not generate.

**Three: `then` is no longer stepped at all, and the grouping key is why.** `steps()` admits two
positions into one group when they state the same keyword at the same instance location with the
same `describe`, on the stated premise that "the text is derived from the stated value by the
emitting branch, so equal descriptions mean interchangeable rewrites". That premise is FALSE for
the five families whose rewrite reads the node: `if/then -> the condition, the branch negated`
contains no value at all, so `core/account-timezone-capability.json`'s four conjuncts — four
different `if` conditions on one instance location — become ONE step whose materialization
demands `mode` be `seller_fixed` and `account_fixed` at once. `core/macro-encoding.json` is the
same shape with three. I expect to make the group key carry the stated value for exactly those
five families, so two positions group only when they state the same thing.

## The predictions

1. **Of the 19 named sites, I expect 0 to become steppable through same-node sibling
   exclusion** — measured above as 0 of 44. The sites that stop being unsteppable are the
   grouped negating ones, which split into one step per stated value: `core/macro-encoding.json`
   `/allOf/0` `then` (3 positions) and `core/creative-approval-scope.json` `/allOf/0` `then`
   (2 positions). **2 of the 44 measured sites**; both are `then`. Every other site stays
   unsteppable and becomes REPORTED with its collider named.
2. **Pairs moving from refused to pass: 0.** The 448 pairs hold 0 refusals today (437 `pass` +
   11 `no_constraint_to_step` = 448) and none of the 13 documents is among them.
3. **`no_constraint_to_step` stays 11.** Splitting a group raises a document's step count and
   can never take its last step away, so a document with zero sites still has zero.
4. **`graded_instances` over the 448 pairs RISES** above the committed 31923. Split groups are
   more steps and each draws its own examples. I cannot predict the value and will not guess
   one; the constant is the integrator's to re-measure.
5. **`test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it` goes fully
   green**, including the two rows that are red now: `then` back to `(80, 80)` from
   `(0, 0)` and `not` back to `(60, 60)` from `(40, 40)`. The integrator called `not 60 -> 40`
   a legitimate consequence of the grouping and theirs to re-measure; I predict it is not
   legitimate — `not {"required": ["fixed_timezone"]}` and
   `not {"required": ["supported_timezones"]}` describe identically and are two facts — so the
   committed constant is already right and nothing needs editing.
6. **`STEP7_SITES` keeps exactly one mismatching row, `uniqueItems`.** `then`, `not`, `else`,
   `anyOf` and `oneOf` return to their committed census counts; `uniqueItems` stays at the
   merged `(462, 198)` against a committed `(479, 198)`, because its `describe` already carries
   the stated bound and its grouping is a true restatement. That row is the integrator's.
   Consequently `test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` and
   `test_the_harness_steps_every_one_of_d6s_six_families` stay red on that row alone.
7. **Both of the conflicting tests pass, unweakened.**
   `test_an_unsatisfiable_step_is_no_evidence_and_not_a_harness_error` steps `anyOf`, a
   complement family, so `no_evidence`. `test_an_unsteppable_site_is_reported_rather_than_passed`
   steps `maxLength`, a witness family, so `harness_error`. Neither fixture changes.
8. **`test_two_different_bounds_at_one_location_stay_two_steps` stays green**, and that is why
   cross-position neutralisation is not on the table: it asserts that stepping `minLength 3`
   against a conjunct's `minLength 5` is never reported as `pass`. Neutralising the other
   position would make it pass and redden the test.

## The fire probe

A classification that cannot return the other answer is not a verdict. I will invert the
complement flag and show the red: with the five families marked as witnesses,
`test_an_unsatisfiable_step_is_no_evidence_and_not_a_harness_error` must fail; with every family
marked a complement, `test_an_unsteppable_site_is_reported_rather_than_passed` must fail.

---

# The grading

Measured on `sdk/j3k2l13-exclusive-step`. Every number says the population it is over.

The suite at the delivered tip, in full:

```
FAILED tests/test_emit.py::test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none
FAILED tests/test_emit.py::test_every_class_passes_all_three_checks[core/inventory-list-application.json#]
FAILED tests/test_emit.py::test_the_step_result_is_counted_over_the_whole_population
FAILED tests/test_emit.py::test_the_harness_steps_every_one_of_d6s_six_families
FAILED tests/test_emit.py::test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded
5 failed, 572 passed in 853.44s (0:14:13)
```

The same five, with the same reasons, as the run at the fix commit before its docstring-only
amend (`5 failed, 572 passed in 1097.62s`); `git diff 486e83a8d 4b5ba8892 -- codegen/harness.py`
is entirely inside one docstring.

Against the starting sha I did not run the suite myself, so what follows is the integrator's
named set of four, not my measurement. Two of those four are now GREEN:
`test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it` and
`tests/test_harness_steps.py::test_an_unsteppable_site_is_reported_rather_than_passed`. Two are
still red on their `uniqueItems` row. Of my five, two are NEW and are my change's doing —
`test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none` and
`test_every_class_passes_all_three_checks[core/inventory-list-application.json#]` — and
`test_the_step_result_is_counted_over_the_whole_population` is red at a different assertion
than it would have been at the starting sha.

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | 0 of the sites become steppable through same-node sibling exclusion; 2 sites stop being unsteppable, both grouped `then` | 0 same-node mechanism written. `core/macro-encoding.json` 2 unsteppable -> 1, `core/creative-approval-scope.json` 3 -> 2; both deltas are the `then` group splitting | **right** |
| 2 | 0 pairs move from refused to pass | 0 moved that way, and **1 moved the other way**: `core/inventory-list-application.json#` went `pass` -> `refuses:harness_error`, so the 448 pairs are 436 `pass`, not 437 | **wrong**, and the miss is the point — see below |
| 3 | `no_constraint_to_step` stays 11 | the excused list is 12 entries: the same 11 plus `core/inventory-list-application.json#`, which is a `refuses:harness_error` and not a 12th `no_constraint_to_step` | **right on the count, and incomplete** — I predicted the count and not the list, and it is the list that is asserted |
| 4 | `graded_instances` rises above the committed 31923 | not isolated: the whole-population test asserts `pass == 437` first and stops there, so the sum was never reached on this tree | **ungraded** |
| 5 | `test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it` fully green, `then` (80, 80), `not` (60, 60) | passes. Measured directly: `then (80, 80, 4 sites)`, `not (60, 60, 3 sites)`, every other family unchanged | **right** |
| 6 | `STEP7_SITES` keeps exactly one mismatching row, `uniqueItems` | **five** rows mismatch: `anyOf` 444/450, `minProperties` 47/48, `not` 439/469, `then` 582/585, `uniqueItems` 462/479. The test reports only `uniqueItems` because its loop asserts in dict insertion order and stops at the first failure | **wrong** |
| 7 | both conflicting tests pass, unweakened, neither fixture changed | `tests/test_harness_steps.py` 17 of 17 pass, including `test_an_unsteppable_site_is_reported_rather_than_passed`; `test_an_unsatisfiable_step_is_no_evidence_and_not_a_harness_error` passes. No fixture touched | **right** |
| 8 | `test_two_different_bounds_at_one_location_stay_two_steps` stays green | passes | **right** |
| fire | inverting the flag reddens each test in turn | with the flag inverted on the step object: the witness fixture reports `no_evidence` (the lane's test asserts `harness_error`) and the complement fixture reports `harness_error` (step 7's test asserts `no_evidence`) | **right** |

## Prediction 2 is the one worth reading

I predicted the metric could not lose a pair and it lost one, which is the defect the bead
describes doing exactly what the bead says it does. `core/inventory-list-application.json#`
passed with one site silently ungraded: a `required` step over `/oneOf/0` and `/oneOf/1`
dropping `list_type`, the root `discriminator`'s own propertyName. Both branches require it and
their `const` values are what tell the branches apart, so the stepped document admits nothing
and `hypothesis` raised. Under the old single catch that was `no_evidence`, which is in
`PairReport`'s admitted set, so the pair reported `pass`.

**It is not an over-report, and that was measured rather than argued.** A valid instance drawn
from the document with `list_type` deleted is refused by the document, on `['oneOf', 'required']`
— three drawn instances, all three. So an instance violating that `required` exists; the harness
could not build one. `no_evidence` would have been the false claim "the document has none", and
that settles a question I was unsure of while writing the fix: `required` is **not** a complement
family, however exactly `not: {required: [k]}` negates the keyword at its own node, because the
node is a `oneOf` branch and what the document refuses is decided above it.

So the honest verdict is `harness_error`, the pair is refused by name with its collider named
(`/:discriminator`, `/:oneOf`, `/:type`, `/:x-adcp-validation`), and N is 436 of 448 rather than
437. There is no fix for the site: an instance omitting the discriminator violates `oneOf` as
well, so none violates exactly this keyword, and the step cannot be made exclusive without
inventing a constraint the document does not state.

## What the measurement says about the bead's own mechanism

The bead names "a DIFFERENT keyword at the same instance location contradicts the mutation" and
calls for the step to be made EXCLUSIVE against the colliding sibling. Over the 9 of its 13
documents I could resolve and step within budget, **0 of 44 unsteppable sites is a same-node
collision**: at every one, dropping the keys the original states at the stepped node and the
rewrite left untouched leaves the document unsatisfiable. The colliders are at OTHER positions
sharing the instance location — an `allOf` conjunct's own `enum`, a conditional `then` branch's
`minimum`, a root `oneOf` — and neutralising those is forbidden by
`test_two_different_bounds_at_one_location_stay_two_steps`, which asserts that stepping
`minLength 3` against a conjunct's `minLength 5` is never reported as `pass`.

So the exit is met by the second of its two arms: **reported, with the colliding sibling named**.
Measured over the 8 documents whose full step list ran, 115 steps: 68 graded, 38 `harness_error`,
9 `no_evidence`. Named colliders, one per class:

| site | collider named |
|---|---|
| `core/macro-encoding.json#/properties/depth` `minimum 0` | `/allOf/0/then/properties/depth:const`, `/allOf/1/then/properties/depth:minimum`, `/allOf/2/then/properties/depth:const` |
| `core/postal-country-system.json#/properties/system` `enum of 23` | ten `anyOf` branches' `enum`/`const` at `/anyOf/<i>/properties/system` |
| `core/creative-approval-scope.json#/properties/approval_status/allOf/0` `enum of 4` | `/properties/approval_status/allOf/1:enum` |
| `core/brand-response-authorization-result.json#/properties/trust` `enum of 2` | `/oneOf/0/properties/trust:const`, `/oneOf/1/properties/trust:const` |
| `core/inventory-list-application.json#/oneOf/0` `required drops 'list_type'` | `/:discriminator`, `/:oneOf` |
| `core/reference-renderer.json` — all 14 | **nothing at the instance location**: the ORIGINAL resolved document does not generate, so no step over it can |

`core/catalog-item-availability-state.json`, `core/demographic-targeting-resolution.json`,
`core/targeting.json` and `protocol/sync-principal-request.json` did not finish stepping inside
the budget this ran under, so they are **unmeasured here**, not measured as clean.

## Three constants this leaves red, and what each one needs

`tests/test_emit.py` is untouched on this branch — deliberately, because a sibling lane holds an
uncommitted edit to it.

1. `STEP7_SITES`: five rows. `anyOf` 450 -> 444, `minProperties` 48 -> 47, `not` 469 -> 439,
   `then` 585 -> 582, `uniqueItems` 479 -> 462. Every one is the grouping merging genuine
   restatements, and the same five rows are what
   `test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` reads. The pre-fix
   and post-fix census, same tree, same process, over the 1,054 portable documents:
   `then` 224 -> 582, `not` 314 -> 439, `else` 45 -> 58, `anyOf` 438 -> 444, `oneOf` 210 -> 212;
   D6's six families 1,844 -> 2,348 against a committed 2,405.
2. `test_the_step_result_is_counted_over_the_whole_population`: `pass` 437 -> 436. The remaining
   assertions in that test were never reached, so `no_constraint_to_step`, `graded_instances`,
   `compared` and `model_facts` are unmeasured on this tree and need one run to settle.
3. `test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none`: the expected
   list needs `core/inventory-list-application.json#` — but it is a `refuses:harness_error` and
   not a document that states nothing to step, so the test's own premise ("a pair that landed
   there for any other reason would not satisfy this") says the list is the wrong place for it.
   That is a decision about the metric, not a constant to bump, and it is not mine to take.
