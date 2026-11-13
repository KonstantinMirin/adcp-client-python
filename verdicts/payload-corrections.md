# The payloads that contradict the envelope

**`core/protocol-envelope.json` states `required: ['status']`, every task response composes
it through an `allOf`, and upstream's suite is full of payloads that omit it.** Their suite
is green anyway, because their generator wrote `status: Literal['completed'] = 'completed'`
— a value the document states nowhere. The default is what makes an incomplete payload
validate, so not reproducing it is what makes the payload visible. **The correction is to
the payload. Not to the class, not to an assertion, and not by deselection.**

Figures are from `python -m survey causes`, which reads pytest's own report and groups by
cause. Every one is over **4 chunks read** with `/proc/vmstat` at `oom_kill 75`, and every
comparison is against this branch's own merge-base — **never against another lane's output
directory.** The first version of §1 broke that rule and is withdrawn there.

---

## 1. The figures — RE-MEASURED, and the first set WITHDRAWN

**THE FIRST VERSION OF THIS SECTION WAS WRONG AND THE ERROR WAS THE BASELINE.** It quoted
`--since /srv/ws/dropin-keyless`, which is **another lane's output directory**. Keyless
graded `6d6c29586bea`, which is not an ancestor of this branch, so "passed 10,572 → 11,634
(+1,062)" was the difference between **two changes** and not the effect of this one. The
`nocanon status` before-figure of 216 came from the same place. Both are withdrawn. The
instrument now refuses that comparison by reading the commit each run graded; it was right
to.

Re-measured against the **canonical trunk baseline**, which is this branch's own
merge-base. Validated first: a run of 480e6ed58 built in this lane's own worktree
reproduces `/srv/ws/dropin-trunk` exactly — 10,765 passed / 1,039 failed / 12 errors of
13,817 collected, and 0 in every REGRESSED/FIXED bucket — so the banked baseline is sound
and this lane's numbers sit on it.

```
python -m survey causes /srv/ws/dropin-status --since /srv/ws/dropin-trunk
   graded 480e6ed58e2e -> 8845eef16efa          (one line of work)

   COLLECTED              13,817 -> 15,285   (+1,468)
   REGRESSED                                       0
   FIXED                                         154
   newly collected and failing                    39
   corrections applied     48 rows / 23 files / 97 sites
                           (46 adding `status`, 2 adding `budget`)
   4 chunks read           oom_kill 75 before and after
```

**The three figures, together and never one alone: 154 FIXED, 0 REGRESSED, 48 corrections
over 97 sites.** `passed 10,765 → 11,842` and `failed 1,051 → 936` are printed too but are
**not subtractable** across a population that grew by 1,468 — a test that did not run before
cannot have regressed, and the split above is the honest reading.

**+1,468 more tests RUN is a result in its own right**, and it is the provisioning fix, not
the payload rows: 39 of those newly-collected tests fail, and they are failures the suite
could not previously see rather than failures this branch caused.

### Fourth round, and the row is now fully accounted

Re-read on the banked baseline, 30 more correctable sites were still in this lane's row;
51 rows now, and `nocanon status` reads **42**, every one of which this lane may not touch:

```
nocanon status      258 (trunk baseline) -> 72 -> 42
  28   the pinned row deliberately WITHDRAWN (§2); the emitter closes it, bead rgra
  13   OURS, in files this lane's write scope excludes --
       server/principal.py:487/:471/:374 (9), decisioning/refine.py:238 (3),
       client.py:2006 (1, and it is a `raise`, not a construction)
   1   the JSON vector whose correction would put a test's assertion in question (§7)
  ---
   0   payload sites this lane may correct and has not
```

**One row covered 28 tests on its own.** `test_feed_mirror.py`'s client stub funnels every
caller's body through a single dict before validating it, so the correction goes there
rather than into 28 callers — and *before* the `**body` splat, so a caller stating its own
`status` still wins. The `TaskResult(status=TaskStatus.COMPLETED, …)` on the next line is
the stub saying what its scenario means.

**And one site is inside a `pytest.raises` and still qualified.**
`test_trusted_match_validation.py` asserts a *pattern* refusal
(`match="String should match pattern"`) on a payload that also omits `status`; the omission
pre-empts the refusal the test asserts, so supplying what the document requires lets the
asserted refusal be the one that happens. The row is justified by the document either way
— which is the test that keeps this distinct from editing an assertion.

**`nocanon`'s other row moved the way `presence`'s did into mine:** *a conditional the
document states and the payload does not satisfy* went 69 → 75, because payloads that used
to stop at the missing `status` now get further and fail on a conditional. Same tests,
further along.

### My own subject, isolated by the shared cause rule

| `nocanon` cause | baseline | after | |
|---|---|---|---|
| `status`: the envelope requires it and the payload omits it | **258** | **72** | 186 closed |
| the drop-in venv is missing a dependency upstream's suite imports | **58** | **6** | 52 closed |
| a conditional the document states and the payload does not satisfy | 69 | 69 | not this lane's subject |

28 of the 72 remaining are the pinned row deliberately withdrawn (§2). The baseline's
`status` row reads 258 rather than the 216 first quoted because `presence`'s landing
reclassified payloads that used to fail on a `None` and now get far enough to fail on the
missing `status` — same tests, further along.

### The one reported regression, and why it is not one

`survey causes` reports `REGRESSED: 1` —
`tests/test_validate_platform_warnings.py::test_v3_reference_seller_passes_with_no_warnings`.
**In the baseline that test was `skipped`, not passed**, so it cannot have regressed; the
REGRESSED bucket is counting a skip as a pass. By node-id set, *passed-in-baseline ∧
failing-now* is **0** and *failed-in-baseline ∧ passing-now* is **154**.

The failure itself is real and belongs to another lane: `MediaBuyFeatures` resolves to
`SignalsFeatures`, so `GetAdCPCapabilitiesResponseMediaBuy.features` refuses it — an
ambiguous flat name. It pre-exists at **9 failures in the baseline** and reads **32** here,
the extra 23 being instances in `test_property_list_integration.py` and this file, which
only import at all because of the provisioning fix. Newly visible, not newly broken, and
handed to whoever owns the flat-name resolution.

---

## 2. The line, and the one row that came back out

A row may exist only where the document **refuses** the payload, and may add only a value
the document **admits**. Both halves were measured before anything was written.

**Resolving the conjunction is what the first half needed, and the branch pointers are why.**
Each failing class carries `__adcp_schema__`, and reading `required` *at* that pointer says
`status` is required at response roots and **not** at `#/oneOf/N` branches — which would
have made `CreateMediaBuySuccess`, `BuildCreativeSuccess`, `SyncCreativesSuccess` and the
`PreviewCreative*` arms findings rather than corrections. That reading is wrong. The `allOf`
that composes the envelope is a **sibling** of the `oneOf`, so it binds every branch: the
conjunction at a branch is the branch's own `required` *plus every ancestor's*. Resolved that
way, **54 of 54 distinct (class, field) pairs are required by their document** — the nine
that first read otherwise were nested `loc` paths my resolver had not descended, and each
resolves to a document that requires the key:

| read as | why | resolved |
|---|---|---|
| `#/oneOf/N` says no | the envelope's `allOf` is the `oneOf`'s sibling, not its child | required |
| `PreviewCreativeResponse.variant.status` | `variant` is the `response_type` **discriminator value** of `#/oneOf/2`, not a property | required |
| `RefineProposalsResponse.results.0.revised.proposals.0.…purchases.0.start_time` | `revised` is the `outcome` discriminator; the path runs through `core/canonical-proposal.json` → `commercial-terms.json`, whose `purchases.items` requires `start_time` and `end_time` | required |
| `Envelope.reporting.configuration_task` | a test-local `BaseModel`; the field is on `ReportingDeliveryCapabilities`, which requires it | required |

**And the second half is where one row had to come out.** The suite's
`_buyer_submission_support.py` built a `SyncReportingReceiptsResponse` without `status`, 28
tests reached it, this lane corrected it — and cited the document's `const: 'completed'` as
the *strongest* justification a row could have. **That reading is backwards.** Where the node
pins the property to one value the instance is choosing nothing, so supplying it writes the
document back into its own instances; the omission is the emitter's to close, on the Python
route, with the JSON route still refusing it. A payload correction is for a node that admits
**several** values, where the instance is the only thing that can say which. The pair that
settles it sits in one bundle: `SyncReportingReceiptsResponse.status` is pinned to
`'completed'` and `GetProductsResponse.status` is the full nine-member `TaskStatus`, so the
question is asked of the **node** and never of the property's name
(`verdicts/a-pinned-default-is-the-documents-own.md`, bead `adcp-client-python-rgra`).

The row is gone and its 28 tests are back to failing. `_PINNED` is kept in the file as a
**disqualification** rather than a reason — the test is written down instead of remembered.
Measured over the 48 rows that remain, rows at a pinned node: **0**.

The values the rows do add, and what fixes each:

* **`completed`** — returned synchronously and in full, no `task_id` minted and no handoff,
  so the task the envelope asks about is finished. Several of these payloads are already
  wrapped by the suite's own `TaskResult(status=TaskStatus.COMPLETED, data=…)`, which is the
  test stating what its own scenario means.
* **`failed`** — `tests/test_catalog_types.py`'s payload is the `#/oneOf/1` **error** arm and
  carries an `errors` list and nothing else. `completed` would contradict the arm the payload
  itself chose.
* **`submitted`** — `media-buy/build-creative-response.json#/oneOf/2`, where the response has
  no finished creative to return.

Every value was checked against the class's own `model_fields['status']` annotation: all of
them resolve to the full `TaskStatus`, so each is admitted where it is written.

---

## 3. The mechanism: data in this repository, applied by the build

The substituted tree is disposable (§8a) and `regenerate.py --audit` reports a hand-edited
file as `UPSTREAM EDITED` — a fork beginning. So nothing in the tree is edited by hand. The
rows live in `survey/dropin/payload_fixes.py`, each carrying the document and pointer that
refuses the payload, and `regenerate.py` applies them at **step 5c**. The tree stays
regenerable and every correction stays readable as a row.

**Three row kinds, because the payload reaches the model three ways** — and each one exists
because the previous could not reach a site that was measured. A row also says whether its
value is written `verbatim`: `budget` is `type: number`, and `"5000.0"` is a string the
document refuses as firmly as it refused the omission, so the row says which rather than the
applier guessing from the characters.

| kind | reaches | keyed on |
|---|---|---|
| `Construction` | `Cls(…)` and `Cls.model_validate({…})` | the class **as that file spells it**, by AST; skips any construction already stating the keyword |
| `ViaHelper` | `validate_union(Cls, {…})` — upstream's own test helper, spanning several lines | the helper and the type it is handed |
| `Literal` | a bare dict a helper returns, or a wire string the test serialises | exact source text through the payload's opening brace |

`Construction` names a **class and a file, not a line**, so a row survives upstream moving
code around inside the file.

**A row that does not apply is an error, not a skip.** `apply` asserts each row's site count
exactly and stops the build on the first disagreement, because a stale correction that
silently corrects less than it claims is the failure mode worth refusing. There is no
allowlist and no tolerance. Every row was finally re-measured against **upstream's pristine
tree** (`/srv/ws/wt-upbase`), not against a tree these corrections had already touched:
**48 rows, 0 disagreeing.**

### Two defects of my own, both found by running it

**The applier read the last brace in an anchor instead of the first.** Three corrections
landed inside a *nested* object — `"query_summary": {"status": "completed", …}` and
`"seller_extra": {"status": "completed", …}` — which states the envelope's task status on a
sub-object that has none, leaves the payload still refused, and adds a key the document never
asked for. An anchor opens at the payload it names, so the first brace is the payload's.

**Each round of corrections revealed the next payload down.** A file's first refused payload
stops the reader before the rest, so the junit names only the earlier site: correcting
`test_account_lifecycle.py`'s capabilities payload exposed two `validate_union` sites behind
it, and correcting those exposed a third round. The second and third rounds were **derived
from the run that followed the first**, never guessed ahead of it.

---

## 4. The SDK's own sites: ours, not a payload

`dispatch.py:1770` was named as a construction emitting a status-less response. **It is the
`except _ValidationError` re-raise**, not a construction: the error originates inside the
platform delegate — the test's own stub — and the dispatcher only wraps it. So those 29 are
payload corrections after all, and they are in the rows above.

**`handler.py:2628` is a genuine one, and it is fixed at the source.** The time-budget
timeout path returned `GetProductsResponse.model_validate(project_incomplete_response(…))`,
and that dict carries `products` and `incomplete` and no `status` — a document this SDK's own
protocol refuses, which any conforming peer would reject rather than merely a test. The value
is what the branch knows: the deadline fired, the platform coroutine was cancelled, no task
is handed off and no `task_id` is minted, so there is nothing to poll; what the seller did not
finish is carried by `incomplete[]`, which is the field the spec provides for exactly that.

**A second defect sits behind it, in a file this lane may not edit.**
`project_incomplete_response` (`src/adcp/decisioning/time_budget.py:273`) emits
`"estimated_wait": None`, and its own docstring says *"`estimated_wait` is omitted
(`None`)"* — conflating omitted with present-and-null. The document admits no null there, so
the response still fails after `status` is supplied:

```
incomplete.0.estimated_wait
  Input should be a valid dictionary or instance of EstimatedWait [input_value=None]
```

That is the `presence` lane's subject and `time_budget.py` is its file. **Named, not touched.**

### Three more of ours, each outside this lane's write scope

| site | the payload | lane |
|---|---|---|
| `src/adcp/server/principal.py:374` | `{"result": {"kind": "unconfigured"}, "context": …}` — and the **same function** states `"status": "rejected"` four lines below, so one branch of one function states the field and its neighbour does not | `presence` |
| `src/adcp/decisioning/refine.py:238` | `GetProductsResponse(products=…, proposals=…, refinement_applied=…)` | `presence` |
| `src/adcp/client.py:2006` | a `raise`, not a construction: the payload is the agent's wire response the test mocks, so this is not an SDK emission defect | — |

---

## 5. The provisioning: read out of upstream's own declaration

58 failures were not failures. `provision()` named four packages — `pytest`,
`pytest-xdist`, `pytest-asyncio`, `pytest-json-report` — and upstream's suite imports more:
**41 files died on `asgi_lifespan`, 5 on `respx`, 3 on `freezegun`**, and every one was
counted as a failure rather than as a missing package.

Appending three names fixes today and goes stale silently on the next bump, so the set is
read out of **their** declaration: `_their_test_extra` finds the extra of upstream's own
`pyproject.toml` that declares `pytest`, and the install becomes `-e ".[dev]"`. The extra is
identified **by what it contains, not by its name**, and `None` is reported rather than
papered over — a tree whose test dependencies are undeclared is a finding.
`pytest-json-report` stays named explicitly, with a comment: it is the reporter this harness
reads its figures out of, not a dependency their suite has.

### The fourth row is not a `rootdir` question

`No module named 'tests.test_decisioning_serve'` (4 tests) is not a path problem. **The build
deletes that file.** `tests/test_decisioning_serve.py` is row 51 of
`survey/dropin/upstream-tests-about-their-generator.txt`, so `drop_their_generator_tests`
unlinks it — while `tests/test_server_supported_versions.py`, which survives, does
`from tests.test_decisioning_serve import _BarePlatform` at four call sites.

Two things are wrong and neither is mine to change:

1. **The file's subject is not their generator.** Its docstring is *"Unit tests for
   `adcp.decisioning.serve`"* and it holds **40 test functions** about
   `create_adcp_server_from_platform` and `serve`. It names `datamodel_code_generator`
   nowhere and `types/domains` nowhere. Deleting it removes 40 behavioural tests from the
   denominator.
2. **The deletion has no dangling-importer check.** `drop_their_generator_tests` verifies
   that every declared path *is* a file and then unlinks it; nothing asks whether a surviving
   file imports from it. That is the same defect class this lane caught in `csj0` with
   `tests/conformance/_round_trip.py`, where a `git rm` would have broken a live importer.

The two helpers the survivor wants (`_BarePlatform`, `_SalesPlatformWithRequiredMethods`) are
module-level classes, so the import is a fixture dependency and not a reference to anything
generated.

---

## 6. The `anyOf` refusals: 20 are payloads and 9 must not be touched

`adcp-client-python-xuh7` offered 29 bare-combinator refusals as "29 more payloads". **20
are. The other 9 are not, and correcting seven of them would delete the test.** Reproduced:
29 failures, split exactly as the bead's table says — `CreateMediaBuyRequest` 20,
`PostalArea` 3, and six singles.

**The 20 are corrected, and the arm is a semantic choice.** `create-media-buy-request.json`
refuses upstream's payload at the root and at all three arms, each naming something
different. The payload carries `packages` and no `total_budget`, no `budget_allocation` and
no `proposal_id`, so `#/anyOf/0` *"Explicit packages with fixed allocation"* is the arm it
**means** — and that arm's `not: {required: ['proposal_id']}` is already satisfied, while arm
1 is the seller optimising a shared budget and arm 2 is executing an agreed proposal. This
test is neither, so the choice is not the smallest diff. Upstream's own comment beside the
payload agrees: *"create-media-buy-request.json requires packages, a budget, or a proposal"*.
Three sites, two rows, `budget` written `verbatim` because it is `type: number` and `"5000.0"`
is a string the document refuses as firmly as it refused the omission.

**Seven of the nine have a payload that is deliberately invalid, and the test asserts the
refusal — often its exact wording.** Correcting the payload would remove the test's subject:

| test | asserts | why it fails now |
|---|---|---|
| `test_postal_area_compat.py::test_native_postal_country_system_mismatches_fail_closed` ×3 | `pytest.raises(ValueError, match="postal system .* is not valid for country")` | the payload is a deliberate mismatch (DE+zip, NL+plz, US+plz); the refusal is right and says `anyOf ()` instead of naming the mismatch |
| `…::test_targeting_overlay_rejects_mismatched_postal_pair` | `match="postal system 'plz' is not valid for country 'US'"` | same, with an exact message |
| `test_trusted_match_validation.py::test_provider_registration_requires_identity_dimensions_when_identity_match_enabled` | `match="countries is required"` | payload deliberately omits it |
| `test_adagents.py::test_generated_catalog_validates_nested_reference_renderer` | `match="Field required"` | the refusal is correct and the message does not contain the words the test looks for |

**So for these seven the refusal is right and the message is the defect** — which is the
bead's own conclusion about the message, applied to the tests that read it. They resolve when
the `presence` lane lands each branch's attributed reason; no payload row is appropriate and
none was written. `PostalArea` also overlaps `namereach`'s work in that file (4 of its 25
failures are this cause), so it was left alone on that ground too.

**One of the nine is the sharpest expectation-versus-document case in the exercise.**
`tests/test_reporting_adjustment_evidence.py::test_generated_default_does_not_repair_a_missing_required_wire_field`:

```python
raw = adjustment()
del raw["control_total_deltas"][0]["value_type"]
# Generated models accept a default here; the authoritative wire schema does not.
ReportingAdjustment.model_validate(raw)          # expected to SUCCEED
rejected("INVALID_EVIDENCE", lambda: capture(raw))
```

`core/reporting-control-total.json` is a `oneOf` of two arms —
`IntegerReportingControlTotal` and `DecimalReportingControlTotal` — and **both** state
`required: ['name', 'value', 'value_type']`. So the document requires `value_type` under
every branch and our model refuses the deletion correctly. **Upstream's own comment names the
invented default as the thing it is relying on**, and the test's subject is that divergence.
Restoring `value_type` would make line 257 pass and then make `rejected("INVALID_EVIDENCE", …)`
fail, because the payload would be valid. **Left failing, named, not corrected.**

The last two belong elsewhere: `MCPWebhookPayload` carries `"result": None` with the comment
*"Working status may have no result yet"* — a None where the document admits the key's
absence, which is `presence`; and `GetReportingStatusResponse` already states
`"status": "completed"`, its omission being inside `adjustments[0]`, the same
`ReportingAdjustment` family.

---

## 7. Left failing, named

**Expectation disagrees with the document — reported, not repaired.**

`tests/test_negotiated_catalog_purchase.py::test_completed_payload_does_not_invent_newer_response_defaults`
asserts `"status" not in payload` — the projection `_completed_payload` builds for a 3.0
peer. Its input is `_CASES[1]["legacy_response"]`, out of
`tests/conformance/vectors/products-only-brief-compatibility/vectors.json`, which omits
`status`; `media-buy/get-products-response.json#` requires it through the envelope, so
`LegacyGetProductsResponse.model_validate(wire)` fails at line 469 and the assertion is never
reached. **Correcting the vector would put the assertion itself in question** — whether
`status` belongs in a projection for a peer that predates it is a protocol ruling, not
something a payload correction may decide. The payload is also a JSON data file, which none
of the three row kinds reaches. Left failing, with its document and pointer.

**Not the `status` family at all, and measured rather than assumed.** Two rows in the brief
were misfiled: `src/adcp/canonical_formats/projection.py:457` (5) and
`tests/test_rootmodel_proxy.py:32` (7) carry `format_id` + `name` on `Format`, not `status` —
`core/format.json#` is the **v1 named-format definition** and those payloads author v2
`format_kind`. Adding `format_id` + `name` would **invent a v1 format identity**, which the
conversion's own registry forbids: kind → id is not derivable without `v1_format_ref`, which
the seller asserts. That is 118 + 118 failures and it is `drawcost`'s rename, not a payload
defect. With those out, **ours in the `status` family is 38, not 39** — the rest being
`principal.py` (2), `client.py` (1), `refine.py` (1) and `handler.py` (5), with
`dispatch.py`'s 29 being their payload reached through our re-raise.

### One note back on the shared instrument

The `newly failing` label this section originally argued with is **gone** — `--since` now
splits `REGRESSED` from `newly collected and failing`, and the reverse into `FIXED` and
`no longer collected`, which is exactly the distinction that was missing. That reading is
now the instrument's and no longer this verdict's to make.

**One thing is left, and it is small: `REGRESSED` counts a SKIP as a pass.** It reports 1
for `test_v3_reference_seller_passes_with_no_warnings`, whose baseline outcome is `skipped`.
A test that did not run cannot have regressed, by the same argument the split is built on —
so the bucket wants `was == "passed"` rather than `was != failed`. By node-id set with that
condition applied, this branch's regressions are **0**.

---

## 8. Gates

```
./check     emitted 1059 / refused 0, primary 0 / chained 0,
            approximated 383 facts in 148 documents     (unmoved)
oom_kill    75 before and after every run
chunks      4 read on every figure quoted here
REGRESSED, by node-id set (passed in baseline, failing now)  0
   (`--since` reports 1; in the baseline that test was SKIPPED, not passed)
FIXED (failed in baseline, passing now)                      154
newly collected and failing (never ran before)               39
rows at a pinned node                                        0
rows re-measured against upstream's pristine tree            48, 0 disagreeing
baseline validated   a run of 480e6ed58 in this lane's own worktree reproduces
                     /srv/ws/dropin-trunk exactly, 0 in every REGRESSED/FIXED bucket
upstream's retained tests   byte-identical in the repository; corrected only by the
                            build, from committed data, never edited in place
```

No allowlist, no ratchet, no floor, no budget. The row set is derived from the run's own
`longrepr` and each row's justification is read off the bundle; the provisioning set is read
off upstream's `pyproject.toml`; the pinned-node test is read off the node.

Write scope: `verdicts/payload-corrections.md`, `survey/dropin/payload_fixes.py`,
`survey/regenerate.py`, `src/adcp/decisioning/handler.py`. Named and not touched:
`src/adcp/decisioning/time_budget.py`, `src/adcp/server/principal.py`,
`src/adcp/decisioning/refine.py`, `src/adcp/client.py`,
`survey/dropin/upstream-tests-about-their-generator.txt`, `codegen/render.py`.
