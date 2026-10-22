# Prediction: the refuses check and a keyword restated under a root `allOf`

Written and committed before the fix, so the grading below cannot be retrofitted.
`salesagent-j3k2l.10` owns the harness; `docs/plan/rebuild-plan.md` §6 is the contract.

## The defect, reproduced

A document whose root and whose `allOf` conjunct both state the same keyword gets one step
site per POSITION. Stepping one position leaves the other stating the original bound, and the
conjunction of the two admits no instance, so the step grades nothing and costs a step site.

Reproduced on a root `allOf` restating `required`, `minLength` and `minItems`: **6 of 6 sites
report `harness_error`**, in three different exception shapes —

| site | outcome |
|---|---|
| `/required` and `/allOf/0/required` | `Unsatisfiable: Unable to satisfy assumptions of body` (the filter exhausts) |
| `/properties/label/minLength` and its conjunct twin | `InvalidArgument: Cannot have max_size=2 < min_size=3` |
| `/properties/tags/minItems` and its conjunct twin | `Unsatisfiable: Cannot generate test cases from empty strategy` |

`harness_error` is a pair-level failure (`PairReport.outcome` admits only `pass` and
`no_evidence`), so a restating document cannot be graded green at all today. D7's amendment
makes restatement the normal case, which is why this is now blocking rather than an edge.

## The option I expect to take

**Option 1: mutate every position stating that keyword at the same instance location.** The
document states ONE fact about one instance location through two schema positions, so one step
is the truthful unit and pushing the instance out once is what the check means.

Mechanism I expect to write: `steps()` keys each site by `(instance location, keyword)`, where
the instance location is the site's pointer with the applicator hops that do not move the
instance cursor removed — `allOf/<i>`, `anyOf/<i>`, `oneOf/<i>`, `then`, `else`. `if` and
`not` stay, because a step under either does not push an instance out of the document at all
(it makes the condition fail, or satisfies the negation) and grouping them would state a fact
the document does not state. One `Step` per group; `materialize` applies each member position's
own rewrite.

Why this stays correct where a group spans `anyOf` branches, which are NOT conjoined: the
ORIGINAL document still decides whether an instance violates anything (`check_refuses` calls
`violated_keywords` against the original), so a group that pushes out only some branches
reports a fired control, not a false pass. Grouping cannot manufacture a pass; it can only
restore a denominator.

I expect NOT to need the two other options. Skipping the site records an ungraded restatement
for 47 composition sites that D7 makes routine, and mutating only the least-constraining
position leaves the tighter one deciding, so the step is not exclusive and the control fires.

## What I expect to change, in numbers

1. **The reproduction above**: 6 sites -> 3, all three stepped, no `harness_error`.
2. **A document stating each keyword once**: site count and every per-site outcome unchanged.
   This is the invariant the grouping must not disturb, and most of the bundle is this case.
3. **The population**: I expect the grouping to merge **200–450 positions** into roughly half
   that many steps, over **80–200 of the 1,054 portable documents**. The denominator for the
   exposure is the 1,054 portable documents, counted with `$defs`/`definitions` walked.
4. **Residual**: a contradiction between the stepped keyword and a DIFFERENT keyword in a
   conjunct (`maxLength` stepped up against a conjunct's `pattern`) is not a restatement and
   grouping does not fix it. I expect **0–20 such sites** to remain `harness_error` after the
   fix.
5. **A new not-stepped outcome name**: I expect NOT to add one. §6 requires a site the check
   cannot step to be reported as not-stepped and never as passed; `harness_error` already
   satisfies both, and it is loud. If measurement (4) finds residual sites in documents the
   emitter must grade green, that judgement flips and I will name the outcome
   `unsatisfiable_step` as a not-stepped verdict that contributes nothing to the denominator —
   decided on the measured count, not in advance.
6. **The suite**: unchanged pass count plus the new tests. No existing test should move.

## D1–D13

I expect this to need no decision change: the grouping is a property of the harness's own
instrument, and §6 already says what a zero denominator means. If it turns out to need one, I
stop and report.
