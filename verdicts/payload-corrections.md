# The payloads that contradict the envelope

**`core/protocol-envelope.json` states `required: ['status']`, every task response composes
it through an `allOf`, and upstream's suite is full of payloads that omit it.** Their suite
is green anyway, because their generator wrote `status: Literal['completed'] = 'completed'`
— a value the document states nowhere. The default is what makes an incomplete payload
validate, so not reproducing it is what makes the payload visible. **The correction is to
the payload. Not to the class, not to an assertion, and not by deselection.**

Figures are from `python -m survey causes`, which reads pytest's own report and groups by
cause. Every one is over **4 chunks read** with `/proc/vmstat` at `oom_kill 75`.

---

## 1. The three figures, and never one alone

PLACEHOLDER_FIGURES

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
Measured over the 46 remaining rows, rows at a pinned node: **0**.

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
because the previous could not reach a site that was measured:

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
**46 rows, 0 disagreeing.**

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

## 6. Left failing, named

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

`survey causes --since` reported **70 newly failing** for this run, and the label reads as a
regression. Checked by node-id set against the same two reports: **69 of the 70 were not
collected in the baseline at all and 1 was skipped; the count of tests that passed before and
fail now is 0.** They are in `test_property_list_integration.py` (23),
`conformance/signing/test_webhook_sender_e2e.py` (14) and the other files whose imports the
baseline venv could not satisfy — so they are the provisioning fix making previously
invisible failures visible, which is the opposite of a regression. The rule may want to split
*passed-before-now-failing* from *newly-collected-and-failing*; the first is a gate, the
second is coverage arriving.

---

## 7. Gates

```
./check     emitted 1059 / refused 0, primary 0 / chained 0,
            approximated 383 facts in 148 documents     (unmoved)
oom_kill    75 before and after every run
chunks      4 read on every figure quoted here
newly failing, by node-id SET (passed before, failing now)   0
rows at a pinned node                                        0
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
