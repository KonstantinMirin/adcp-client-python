# Findings — the 47 reporting and reporting-conformance failures

Baseline `test-results/before.json`: `failed=399, error=5, passed=14680, total=17910`.
TASK.md's trunk reads `failed=398, error=5, passed=14681, total=17910`. The single
deviation is **outside this file list** and is recorded under "The baseline" below. All
fourteen files in scope carried exactly the counts TASK.md states, 47 of 47.

Each failure sorted into one of the three grounds TASK.md names, before anything was
touched:

| ground | count |
|---|---|
| a fixture short a key the envelope or a conditional requires, or one the document contradicts | 28 |
| a name or a default the previous generator bound | 12 |
| genuine reporting behaviour — one of them a real SDK defect | 7 |

**35 repaired, 12 left red on purpose**: 5 are one SDK defect, and 7 need a file outside
this worktree's write scope. A second SDK defect is reported here too; it left no test
red, because the three tests that surfaced it grade a model that is faithful.

Nothing was deleted. Every repaired test still grades its subject.

Measured from the two artifacts — `test-results/before.json` → `test-results/after.json`:
in-scope **47 → 12**, and **0 tests newly failing anywhere in the suite**.

---

## The two SDK defects — STOP, reported, not repaired

### 1. `_restore_confirmation` builds the receipts response without its envelope `status`

**`src/adcp/reporting/submissions/models.py:563`. Five failures, left red.**

```
tests/conformance/reporting/test_reporting_buyer_submissions.py           (4)
tests/conformance/reporting/test_reporting_buyer_submission_validation.py (1)
```

Every one of them fails as `ReportingSubmissionError: SUBMISSION_HISTORY_CORRUPT`, raised
from `validate_submission` with the real cause swallowed into a `logger.debug`. Measured
by raising that logger:

```
confirmation history refused: ValidationError: status [missing]
```

`_restore_confirmation` rebuilds a response from the retained sanitized evidence with

```python
response = SyncReportingReceiptsResponse.model_validate({"results": results})
```

and `status` is not in it. The stored evidence is a results array only, so restore is the
one place that has to re-supply the envelope's own field.

**The emitted type is faithful and the call is wrong.**
`media-buy/sync-reporting-receipts-response.json` composes
`core/protocol-envelope.json` through `allOf`, and that document's own description is
unambiguous: *"The `status` field is REQUIRED on every task response envelope, including
synchronous metadata responses … Agents shipping responses without a top-level `status`
are non-conformant regardless of whether the task body schema would otherwise validate."*
The response document then pins it, `"status": {"const": "completed"}`. Measured on the
class: `status: Literal['completed']`, required, no default. This is the conjunction
correction `_buyer_submission_support.py` already carries in a comment — the previous
generator dropped the `allOf`-composed half, which is why the call was written without it.

**It is not a test-only path.** `validate_submission` is reached from
`ReportingSubmissionIntentStore.get` via `store.py:_current`, and `_restore_confirmation`
runs whenever the `CONFIRMATIONS` cache does not already hold the proof — i.e. after any
process restart or cache eviction. A buyer reading back its own stored submission gets
`SUBMISSION_HISTORY_CORRUPT` for evidence that is intact.

**Proven, without editing `src/`** — the shim supplies the pinned literal and nothing else:

```
as shipped      -> RAISED ReportingSubmissionError SUBMISSION_HISTORY_CORRUPT
status injected -> True   (store.get(SCOPE) == result.submission)
```

The repair is `{"status": "completed", "results": results}` at that line. `src/` is
outside this worktree's write scope.

### 2. The client sends an exact-revision delivery read the document refuses

**`src/adcp/client.py:3206`, `AdCPClient.get_media_buy_delivery`. Reported; the three
tests that surfaced it are repaired against the model, which is faithful.**

`media-buy/get-media-buy-delivery-request.json` states `default: false` for the ten
aggregate selectors at `#/properties` and forbids their **presence** in exact mode at
`#/allOf/1/then/not`. The client dumps with `exclude_none=True` alone, which materialises
those defaults. Measured on an exact request:

```
model_dump(mode="json", exclude_none=True)                     document REFUSES
model_dump(mode="json", exclude_none=True, exclude_unset=True) document accepts
```

So an exact-revision read issued through the public client carries
`include_package_daily_breakdown: false` and `include_window_breakdown: false` and is
non-conformant on the wire. The model is right in both spellings — it writes a default
the document states — and only the dump keyword decides what reaches a seller. The same
`exclude_none=True`-alone spelling appears at the other send sites in `client.py`; this
one is the measured case.

This was already filed as `adcp-client-python-u7qa` and a sibling test in
`test_reporting_exact_request_models.py` already carried the correction; the three
failures here are now spelled the same way, with the client site named in the comment.

---

## Out of this worktree's write scope — 7 failures, one two-line repair

```
tests/conformance/reporting/test_reporting_production_lifecycle.py (4)
tests/conformance/reporting/test_reporting_production_scope.py     (2)
tests/conformance/reporting/test_reporting_projection_rc6.py       (1)
```

All seven are `ValueError: offering must satisfy the complete public contract`, raised by
`ReportingProductionOffering.__post_init__` and originating in the shared fixture at
**`tests/conformance/reporting/_production_support.py:560-575`**, which is not on this
worktree's file list.

The `ValueError` hides the cause. Measured by re-running the named validator:

```
ERR PATH ['reporting_profile'] | 'canonicalization_contract_version' is a required property
ERR PATH ['reporting_profile'] | 'canonicalization_media_type'       is a required property
```

`core/reporting-delivery-offering.json#/allOf/1` is `if reconciliation_mode const
"consumer_receipt" -> then reporting_profile required ['canonicalization_id',
'canonicalization_contract_version', 'canonicalization_media_type',
'canonicalization_uri', 'canonicalization_sha256']`. The reconciled fixture sets exactly
that `reconciliation_mode` and states three of the five. Both missing keys are `const`:

```python
"canonicalization_contract_version": "1.0",
"canonicalization_media_type": "application/vnd.adcp.reporting-canonicalization+json",
```

Proven without editing the file — shimming only those two consts into the profile builds
the harness (`HARNESS BUILT OK: DurableHarness`). Whoever owns
`_production_support.py` can close all seven with those two lines.

Note that the two `test_reporting_production_scope.py` cases run the server in a
subprocess, which resolves `adcp` through the venv's editable `.pth` to
`/srv/ws/adcp-client-python/src` — a sibling worktree. The fixture is still this tree's.

---

## Repaired — 35 failures

One commit per ground.

### `test_reporting_currency.py` — 6, fixture short the envelope's `status`

The delivery-response fixture stated only the node's own half of the conjunction.
`GetMediaBuyDeliveryResponse.model_validate` refused it, the inline source reported
`PROVIDER_TRANSIENT`/"the reporting source raised ValidationError", and the currency
check these six cases exist to grade was never reached. RE-POINTED by stating
`"status": "completed"`. `delivery["status"]` is a different node — the media buy's own
lifecycle word — and is untouched.

### `test_reporting_reconciliation_transitions.py` — 7, a conditional's required key

The hand-built periods projection sets `reconciliation_mode='consumer_receipt'` on a
healthy period, which is the antecedent of `core/reporting-obligation.json#/allOf/7`.
That conditional requires `pending_adjustment_count` and pins it `const: 0`. The
projection never stated it; the scenario commits no adjustment, so zero is the truth as
well as the pin.

### `test_reporting_reconciliation_store.py` — 1, graded at the wrong node

The adjustment and adjustment-receipt wire shapes were graded by handing a two-key dict
to `GetReportingStatusResponse`. That envelope's `completed` branch carries a three-branch
`oneOf` over `view` whose summary branch **forbids** `adjustments` and whose periods and
revision branches each require nine further keys. The envelope was never the subject.
RE-POINTED at `core/reporting-adjustment.json` and
`core/reporting-adjustment-receipt.json` through the classes that name them — the idiom
this file already used for `ReportingMaterialization`.

### The empty scope — 4 (`test_reporting_scope_models.py` 3, `test_reporting_production_scope.py` 1)

`core/reporting-delivery-config.json#/properties/scope` states `minProperties: 1` beside
`maxProperties: 1` and `additionalProperties: false`: exactly one selector, and `{}` names
none. Four cases passed `{}` and expected it to read back as `{"all_media_buys": true}` —
the previous emission's hand-written default, stated by no node of bundle 3.2. Inventing
a selector the caller did not write is the one thing a scope test exists to prevent.
RE-POINTED, not deleted: `{}` moved into the refusal cases, so `minProperties` is still
graded.

### `test_reporting_capability_models.py` — 6, two grounds

*A decision already taken (4).* §2's first rule: a Python `None` is ABSENCE, a JSON `null`
is a VALUE. Each promise is a bare `const` outside `required`, and a type that does not
admit `null` permits exactly one way of not supplying it. The emitted JSON Schema
therefore carries the `const` and **no** null branch. The assertion asked for
`{"type": "null"}` in an `anyOf` — the previous emission's `Optional[...]` rendering,
which advertised `null` as a legal wire value at every optional non-nullable property in
the tree. Both routes are now graded: the Python route reads `None` as absence, the JSON
route refuses an explicit `null`.

*A fixture short a key (2).* `#/allOf/3` is `if managed_delivery const true -> then
required ['resource_retention_days', 'authorization_revocation_seconds']`. Two cases
raised the tier flag and stated neither window.

### `test_reporting_exact_request_models.py` — 3

See SDK defect 2. The model is faithful; the dump keyword decides. Three dumps re-spelled
`exclude_unset=True`, including the round trip, whose refusal is symmetric and reports the
document's own reason, "forbidden when reporting_revision_id".

### `test_reporting_frozen_read_safety.py` — 6

Five fixtures the document refuses, so the loader reported `STATUS_READ_FAILED` in place
of the verdict under test, plus one shape no node states.

* **selectors (2)** — `get-reporting-status-request.json#/allOf/3`: the revision view
  requires `reporting_revision_id` and forbids `health` and `finality`; the periods view
  forbids the revision id. One request cannot carry all three. Graded once per legal shape.
* **frozen metadata (2)** — naming a `health` on a page stating no `issues` trips
  `#/allOf/4`, which requires `issues` with `maxItems: 0`. Stated on every page, so the
  last still differs in `health` alone.
* **the frozen total (1)** — both paged views state
  `pagination.required: ["has_more", "total_count"]`, so a page without it is refused by
  the document, not by the loader's guard. Both layers are graded now: the document's
  refusal, and `INCOMPLETE_LEDGER_PAGE` through a response the type already passed.
* **the current leaf (1)** — rejecting the adjustment leaf leaves one adjustment
  unreceipted while the inherited `pending_adjustment_count=0` declared the opposite.
  `#/allOf/7` pins that count to 0 beside a healthy or complete health, so the health
  moves to `waiting` with it.
* **no owner, no binding (1)** — `reporting-consumer-status.json#/allOf/0` requires the
  obligation id, the revision id and the digest **together** for a `received` status, and
  `#/allOf/1` forbids all three for `obligation_missing`, the one status whose owner may
  be absent. "No owner but an exact revision to bind by" has no node behind it. The legal
  spelling is graded instead, and it does not bind:
  `AMBIGUOUS_CONSUMER_STATUS_OWNERSHIP`.

### `test_reporting_adjustment_evidence.py` — 1, a gap that has closed

`core/reporting-control-total.json` is a two-branch `oneOf` and both branches require
`value_type`, so a delta without one reaches no branch. The test asserted the generated
model **admits** it — a previous-generator default over a property the document requires —
leaving the wire schema as the only refusal. Both halves refuse it now, and that is what
is graded. The capture is still graded, with the typed adjustment built before the
deletion, because the helper cannot build one from a mapping with no reachable branch.

### `test_reporting_period_date.py` — 1, not a document question

Whether `US/Pacific`, `PST8PDT` and `Asia/Calcutta` resolve is a property of the
platform's tz database. They are `backward` links and this host's tzdata (2026e, Ubuntu
26.04) ships without that file — measured, `zoneinfo.available_timezones()` holds 486
names and none of the three, while `America/Los_Angeles` and `Asia/Kolkata` resolve. The
code hands the name to `ZoneInfo` and refuses what it refuses. Graded wherever the
database carries the link, skipped per alias where it does not: asserting it
unconditionally grades the host, not the SDK.

---

## The baseline

The one-test deviation from TASK.md's trunk figure is
`tests/test_import_memory.py::test_import_peak_rss_within_budget[adcp.types._eager]`,
outside this file list. It is not an RSS overrun: the probe runs
`.venv/bin/python -I -c "import adcp.types._eager"` and the subprocess raises
`ModuleNotFoundError`. The venv's editable `.pth` lists `/srv/ws/adcp-client-python/src`,
so a bare subprocess resolves `adcp` to a **sibling worktree** other agents are editing,
and neither tree carries `types/_eager.py` now. The test's outcome is not a function of
this worktree. Confirmed with the owner before proceeding.

It passes again in `after.json`, which is the whole of the out-of-scope delta there
(357 → 356) and the same evidence for the diagnosis: the sibling tree moved under it,
twice, while nothing in this worktree touched it either time.
