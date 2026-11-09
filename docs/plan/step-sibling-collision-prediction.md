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
FAILED tests/test_emit.py::test_the_step_result_is_counted_over_the_whole_population
FAILED tests/test_emit.py::test_the_harness_steps_every_one_of_d6s_six_families
FAILED tests/test_emit.py::test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded
3 failed, 575 passed in 849.69s (0:14:09)
```

All three are the integrator's stale constants. The run before the retry commit was
`5 failed, 572 passed in 853.44s`, its two extra failures being
`test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none` and
`test_every_class_passes_all_three_checks[core/inventory-list-application.json#]` — both the one
lost pair, both now green.

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
| 2 | 0 pairs move from refused to pass | 0 moved that way. The fix commit moved **1 the other way** — `core/inventory-list-application.json#` to `refuses:harness_error`, 436 `pass` — and the retry commit returns it, so the delivered tip is **437 `pass`** | **wrong at the fix commit, right at the tip**, and the miss is what found the retry — see below |
| 3 | `no_constraint_to_step` stays 11 | 11, measured. The excused list was 12 at the fix commit and is the committed 11 at the tip, every one with `step_sites=0` | **right**, though I predicted the count and it is the list that is asserted |
| 4 | `graded_instances` rises above the committed 31923 | **32,059** at the tip (32,053 at the fix commit), against the committed 31923 and the brief's 32,031 baseline. Also measured: `compared` 4,276, `model_facts` 896, `added` 0, all unchanged | **right** |
| 5 | `test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it` fully green, `then` (80, 80), `not` (60, 60) | passes. Measured directly: `then (80, 80, 4 sites)`, `not (60, 60, 3 sites)`, every other family unchanged | **right** |
| 6 | `STEP7_SITES` keeps exactly one mismatching row, `uniqueItems` | **five** rows mismatch: `anyOf` 444/450, `minProperties` 47/48, `not` 439/469, `then` 582/585, `uniqueItems` 462/479. The test reports only `uniqueItems` because its loop asserts in dict insertion order and stops at the first failure | **wrong** |
| 7 | both conflicting tests pass, unweakened, neither fixture changed | `tests/test_harness_steps.py` 17 of 17 pass, including `test_an_unsteppable_site_is_reported_rather_than_passed`; `test_an_unsatisfiable_step_is_no_evidence_and_not_a_harness_error` passes. No fixture touched | **right** |
| 8 | `test_two_different_bounds_at_one_location_stay_two_steps` stays green | passes | **right** |
| fire | inverting the flag reddens each test in turn | with the flag inverted on the step object: the witness fixture reports `no_evidence` (the lane's test asserts `harness_error`) and the complement fixture reports `harness_error` (step 7's test asserts `no_evidence`) | **right** |

## Prediction 2 is the one worth reading

I predicted the metric could not lose a pair and the fix commit lost one, which is the defect the
bead describes doing exactly what the bead says it does. The third commit gets it back by
grading the site rather than by admitting it ungraded; what follows is the diagnosis that found
both. `core/inventory-list-application.json#`
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

So for a group stepped at every position the honest verdict is `harness_error`, reported with its
collider named (`/:discriminator`, `/:oneOf`, `/:type`, `/:x-adcp-validation`).

**I then wrote "there is no fix for the site", and that was wrong.** I had answered "can this
witness be built" when the question is "is the keyword graded at that pointer", and I had the
measurement that answers it sitting in an earlier probe. The next section is the correction.

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
| `core/inventory-list-application.json#/oneOf/0` `required drops 'list_type'` | `/:discriminator`, `/:oneOf` — and this one is RECOVERED by the third commit; see below |
| `core/reference-renderer.json` — 14 of its 17 steps | **nothing at the instance location**. The ORIGINAL resolved document does not generate, which is the obstacle these run into — but it is not a per-site explanation: 3 of its 17 steps do generate, the two `required` ones being those that drop the heavy nested subtree. See the correction below. |

`core/catalog-item-availability-state.json`, `core/demographic-targeting-resolution.json`,
`core/targeting.json` and `protocol/sync-principal-request.json` did not finish stepping inside
the budget this ran under, so they are **unmeasured here**, not measured as clean.

---

# The handed-back question: was the site really ungradeable?

It was not, and "no fix exists for the site" was me answering "can this witness be built"
instead of "is the keyword graded at that pointer". Measured.

**The array has 7 members and `steps()` already emits one step per member**, so there is no
witness to re-choose — `required: [a, b, c]` is three steps, not one step with a choice of
property. At `/oneOf/0` and `/oneOf/1`, both:
`['list_type', 'effect', 'agent_url', 'list_id', 'resolved_at', 'evaluated_at', 'summary']`.
The root states `discriminator: {"propertyName": "list_type"}`, so the discriminator is
`list_type`.

**6 of the 7 members grade 25 of 25**, at the suite's own budget. Only `list_type` reported
`harness_error`. Asked of the document directly, with one instance DRAWN and each member
deleted in turn, all 7 deletions are refused and `required` is among the violated keywords every
time. So the keyword at that pointer was never ungraded; one member-fact was.

**And that member is gradeable too.** The step holds two positions because both branches state
it. Stepping both forbids `list_type` in both branches, after which an instance omitting it
matches neither and the root `oneOf` has nothing to pick. Stepping ONE leaves the other branch
requiring it, so exactly one branch can match: 6 of 25 examples bite, and the original refuses
every one on `{'oneOf': 6, 'required': 6}`. Landed as the third commit, which retries a witness
group one position at a time before reporting it.

Over the 448 emitted pairs with that in: **437 `pass`, 11 `no_constraint_to_step`, 0
`harness_error`, 32,059 refuses-check instances, 4,276 document facts compared, 896 model-only
facts, 0 narrowings.** No N is spent.

## How narrow the fix is

Over the 38 `harness_error` sites in 8 documents and 115 steps:

| | count |
|---|---|
| `required` steps | 14 of 38 |
| ...at a pointer where ANOTHER member of the same array IS graded | **6 of 14** |
| holding more than one position, so the retry can reach them | **0 of 38** |

By keyword: `required` 14, `enum` 7, `pattern` 5, `minimum` 3, `additionalProperties` 2,
`dependencies` 2, `minItems` 2, `uniqueItems` 2, `minLength` 1.

**So the retry reaches exactly one site in the whole measured population** — the emitted pair.
It is as narrow as a fix gets. The 6 `required` sites with a graded sibling member are all in
`core/reference-renderer.json`: five at `/`, where `required drops 'provenance'` grades, and one
at `/properties/provenance`, where `drops 'source_repository'` grades. For those the keyword at
the pointer is graded and only the individual member-fact is not; none of them holds a second
position, so nothing recovers them.

**A correction to my own earlier claim.** I said the original resolved
`core/reference-renderer.json` not generating explains all 14 of its unsteppable sites. It does
not: **3 of its 17 steps DO generate**, and the two that are `required` steps are the ones that
drop `provenance` and `source_repository` — the heavy nested required subtree. Removing it makes
the object generable. So the document's ungenerability is the obstacle those sites run into, not
a blanket per-site explanation, and the docstring on `contradicting` says so.

# The four documents that did not finish

**The budget was wall clock**, cut at roughly 60 minutes per document at `examples=10` per site,
while three other lanes were running their own suites on the same machine.

**They are not a different problem.** Resolution is cheap and `steps()` is instant; the wall is
site count times one strategy build over the resolved document:

| document | raw | resolved | resolve | `steps()` sites |
|---|---|---|---|---|
| `core/catalog-item-availability-state.json` | 2,976 B | 16,488 B | 0.1 s | 61 |
| `core/demographic-targeting-resolution.json` | 4,185 B | 21,112 B | 0.1 s | 139 |
| `protocol/sync-principal-request.json` | 13,336 B | 53,515 B | 0.1 s | 117 |
| `core/targeting.json` | 23,569 B | 144,448 B | 0.7 s | 737 |
| `core/media-buy-frequency-cap.json` (the control, which finished) | 641 B | 3,487 B | 0.0 s | 23 |

Three to thirty-two times the site count of the one that finished.

**A longer budget does finish them, demonstrated rather than extrapolated.** Re-run on the final
tree, `core/catalog-item-availability-state.json` completed: **61 steps in 1,245.7 s, 20.4 s per
site** — 34 graded, 6 `no_evidence`, 21 `harness_error`, every one of the 21 with an EMPTY
collider, so that document is a generation-cost case like `core/reference-renderer.json` and not
a collision case. At that rate, and it is an upper bound because three other lanes held the
machine: `protocol/sync-principal-request.json` ≈ 40 min, `core/demographic-targeting-resolution.json`
≈ 47 min, `core/targeting.json` ≈ 4.2 h. Those three were cut again to give the suite the
machine, so they stay **unmeasured** and are not claimed clean.

With that document in, the full measured population is **9 documents, 176 steps: 102 graded, 59
`harness_error`, 15 `no_evidence`**. The other 8 were stepped before the retry commit, which
cannot have changed them: 0 of their 38 `harness_error` sites holds more than one position, and
the retry only fires on a group that does.

# The twelfth entry

It was `core/inventory-list-application.json#`, and it was **not** a document that states
nothing to step: 16 step sites and 375 graded instances, with outcome `refuses:harness_error`.
Nor was it a bookkeeping artefact. `test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none`
collects `outcome != "pass"` while its name says "the documents that state none", and its own
docstring anticipates precisely this case — "A pair that landed there for any other reason — a
model defect, a generator failure — would not satisfy this." It was the test working as
designed, reporting a pair that landed there for another reason. With the retry in, the list is
back to the committed 11, every one `no_constraint_to_step` with `step_sites=0`.

## The two constants this leaves red, and the exact edits

`tests/test_emit.py` is untouched on this branch — deliberately, because a sibling lane holds an
uncommitted edit to it. Both remaining failures are the integrator's, and every figure either
one needs is measured here.

1. **`STEP7_SITES`: five rows**, which is also the whole of why
   `test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` is red, since it
   reads the same census. `anyOf` 450 -> 444, `minProperties` 48 -> 47, `not` 469 -> 439,
   `then` 585 -> 582, `uniqueItems` 479 -> 462; the six-family total 2,405 -> 2,348. Every one is
   the grouping merging genuine restatements. Only `uniqueItems` is reported by the test, because
   its loop asserts in dict insertion order and stops at the first failure. The pre-fix and
   post-fix census, same tree and same process, over the 1,054 portable documents:
   `then` 224 -> 582, `not` 314 -> 439, `else` 45 -> 58, `anyOf` 438 -> 444, `oneOf` 210 -> 212.
2. **`test_the_step_result_is_counted_over_the_whole_population`: one row.**
   `graded_instances` 31923 -> **32,059**. Everything else in that test is already right at the
   tip and measured: 448 pairs, 437 `pass`, 11 `no_constraint_to_step`, `compared` 4,276,
   `model_facts` 896, `added` 0.

`test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none` needs **no edit**:
the list is the committed 11 again.
