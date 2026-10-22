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
