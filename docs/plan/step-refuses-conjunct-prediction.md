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

---

# Grading

Measured after the fix, at `8211ace07`. Every number states its denominator.

**The population and what it excludes.** `harness.resolve` resolves **726 of the 1,054
portable documents**; the other 328 are excluded and named — 311 raise on a `$ref` the store
does not carry (many name a `3.2.4` URI the `3.2` bundle has no document for), and 17 exceed a
40-second wall-clock budget. Every population figure below is over those 726, not over 1,054.

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | the reproduction: 6 sites -> 3, all stepped, no `harness_error` | exactly that; each of the 3 reports `pass` against a faithful model with a non-zero denominator | **right** |
| 2 | a document stating each keyword once is untouched | 526 of the 726 have no grouped fact and their step count is identical position for position; the other 200 all have one | **right** |
| 3 | 200–450 positions merged, in 80–200 documents | **17,890 positions merged into 4,341 facts, in 200 documents** (109 of them with a root `allOf`). Total step sites over the population fall from 56,006 to 42,457 | **wrong, by about 40x on positions**; the document count landed at the top of the range, and the range was stated against the wrong denominator |
| 4 | 0–20 residual sites still `harness_error` | **19 of 2,054 steps checked** (0.9%), over 675 of the 726 (51 over a 120s budget). **18 of the 19 are single-position steps** — the pre-existing unsteppable case, not a restatement. Of 114 grouped steps checked, 1 errors | **right, and for a reason the prediction did not state** |
| 5 | no new not-stepped outcome name | none added | **right** |
| 6 | the suite unchanged plus the new tests | 74 before, 91 after; no existing test moved | **right** |

**Where (3) went wrong, and it is worth naming.** The prediction read "47 composition sites in
31 documents tighten requiredness" as the size of the exposure. That is the number of
`required` tightenings a COMPOSITION states; the harness walks a RESOLVED document, where each
such tightening restates every keyword of every property the base declares, at every depth, and
the same base is inlined at every site that references it. `protocol/get-task-status-response.json`
alone falls from 1,911 positions to 256 facts. The lesson is the denominator: a count of
composition sites in the authored schemas is not a count of restated positions in the resolved
ones, and nothing in the prediction connected the two.

**The 19 residual sites, reported rather than fixed.** All 19 fail with hypothesis's
`Unsatisfiable`, which is the stepped document admitting nothing. They are in
`core/reference-renderer.json` (4), `core/demographic-targeting-resolution.json` (3),
`core/demographic-targeting-intent.json` (2), and one each in
`core/brand-response-authorization-result.json`, `core/catalog-item-availability-state.json`,
`core/creative-approval-scope.json`, `core/macro-encoding.json`,
`core/media-buy-frequency-cap.json`, `core/postal-country-system.json`, `core/targeting.json`,
`protocol/get-principal-request.json`, `protocol/sync-agent-notification-configs-request.json`
and `protocol/sync-principal-request.json`. Each is a step contradicting a DIFFERENT keyword
at the same instance location, which is not a restatement and which grouping does not address.
`harness_error` is not in `PairReport`'s admitted set, so each one refuses its pair — which
means **a step that emits one of these 14 documents cannot grade it green until the step is made
exclusive against the colliding sibling**. That is 14 documents of the 726, filed rather than
fixed here: it is pre-existing (18 of 19 have a single position) and outside this ticket.

**Perturbations.** Ten axes were broken on purpose; eight reddened and the two that did not
were findings, not passes. Removing the grouping reddens 10 tests; rewriting only the first
position, 6; dropping `describe` from the admission rule, 63; grouping under `if`/`not`, 1;
keeping the `if` hop instead of refusing to group, 1; not stripping the `allOf` index, 10;
reporting the deepest position, 4; calling a `harness_error` a pass, 3. Forcing only the
reported position reddened nothing until a test was added for the denominator it costs (8 of 25
examples ungraded against 25 of 25) — it now reddens that one test. Forcing each position after
rewriting it reddens nothing and **is not load-bearing**: the docstring claiming the order
mattered was wrong and is removed.
