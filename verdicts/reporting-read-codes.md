# Reporting read codes — why the specific diagnosis never ran, per code

~101 tests across four of upstream's reporting files build a receipt chain with a deliberate
defect, expect `ReportingReconciliationError` with the code naming that defect, and get
`STATUS_READ_FAILED`. Read off the run artifact at `/srv/ws/dropin-full/junit/chunk-*.json`
and never re-enumerated by a run.

```
tests/test_reporting_frozen_read_safety.py       68
tests/test_reporting_frozen_read_corrections.py  16
tests/test_reporting_reconciliation.py           13
tests/test_reporting_revision_ownership.py        4
```

**ONE CAUSE, and it is the payload's.** The refusal is CORRECT, the document states the
requirement, and the model is not to be weakened.

---

## The `except`, named with its file and line

`src/adcp/reporting/_reconcile.py`, two sites inside the paging loop:

| line | guarded call | mapped to |
|---|---|---|
| ~487 | `GetReportingStatusRequest.model_validate(payload)` | `INVALID_STATUS_REQUEST` |
| ~495 | `await client.get_reporting_status(page_request)` | `STATUS_READ_FAILED` |

The second is the masker. Confirmed by running one failing test and reading the traceback:
the raise at `_reconcile.py:450` (pre-change numbering) fires because `result is None`, and
`result` is `None` because `except Exception` swallowed what the client raised.

**AND WHAT IT CAUGHT, read rather than guessed.** The test's stub is
`Pages.get_reporting_status`, which itself calls
`GetReportingStatusResponse.model_validate(deepcopy(page))` — so the exception is **our model
refusing the test's own page**, raised inside the client call and flattened by the `except`:

```
2 validation errors for GetReportingStatusResponse
completed.periods.periods.0.schedule.period_anchor
  required when alignment='billing_cycle' [type=required, input_value=None]
completed.periods.periods.0.schedule.period_timezone
  required when alignment='billing_cycle' [type=required, input_value=None]
```

Of the 4 pages `_pages()` builds, 3 validate and 1 does not. Both
`test_reporting_frozen_read_safety.py` and `test_reporting_frozen_read_corrections.py`
produce exactly this, 2 refusals each.

---

## WHOSE IT IS: the refusal is CORRECT and the payload contradicts its document

Derived by walking from the response to the field's declaring class, not inferred from the
field name:

| step | |
|---|---|
| the response branch declaring `periods` | `SuccessfulLookup` |
| `periods` annotation | `list[ReportingObligation] \| None` |
| `ReportingObligation` | `core/reporting-obligation.json#` |
| `ReportingObligation.schedule` | `ReportingSchedule` |
| `ReportingSchedule` | **`core/reporting-schedule.json#`** |

Our class carries
`ConditionalRequired(when=(Match(key='alignment', present=True, allowed=('billing_cycle',)),), require=('period_anchor', 'period_timezone'))`.

**The document states exactly that**, at `core/reporting-schedule.json#/allOf/0`:

```json
"if":   {"properties": {"alignment": {"const": "billing_cycle"}}, "required": ["alignment"]}
"then": {"required": ["period_anchor", "period_timezone"]}
```

The `else` branch of the same node states the other half — `alignment: "source_timezone"`
requires `period_timezone` and **forbids** `period_anchor` — so the conditional is the
document's own design and not an incidental read.

**The test's payload:**

```python
"schedule": {"period_duration": "P1M", "alignment": "billing_cycle", "delivery_sla": "P1D"}
```

`alignment: "billing_cycle"` with neither `period_anchor` nor `period_timezone`. The document
refuses it; our model refuses it; upstream's generated model admitted it because their
generator does not lower `if`/`then` into a rule.

**So the generic code is the honest answer for THAT payload.** The chain walk that produces
`INVALID_RECEIPT_CHAIN`, `LEDGER_COUNT_MISMATCH`, `IMMUTABLE_RECORD_CHANGED`,
`INVALID_LEDGER_DEPENDENCY`, `SNAPSHOT_CHANGED` and `LEDGER_LIMIT_EXCEEDED` cannot run,
because the response it would walk does not exist — and it should not, for a payload the
document refuses. **Nothing in the model is weakened and nothing is widened.**

### The payload correction, for the lane that owns the data

The fix is DATA in this repository and I am not the owner of that file. For
`survey/dropin/payload_fixes.py`:

> At every site stating the schedule literal
> `{"period_duration": "P1M", "alignment": "billing_cycle", "delivery_sla": "P1D"}`,
> add `"period_anchor"` and `"period_timezone"`, which
> `core/reporting-schedule.json#/allOf/0` requires whenever `alignment == "billing_cycle"`.
> Measured sites: `tests/test_reporting_reconciliation.py:198` and
> `tests/test_reporting_adjustment_evidence.py:489` state it literally; the two
> `frozen_read_*` files reach it through their own `_history()` helper. An alternative that
> touches fewer values is to set `"alignment": "source_timezone"` with `"period_timezone"` —
> the document's other branch — but `billing_cycle` is what the tests' expectations are
> written around, so adding the two keys is the smaller correction.

---

## The per-code table

Every code below is produced by the chain walk, which runs only after the response validates.
None of them is reachable for the payload above, and none is a defect of the code that
produces it.

| expected code | what earns it | why it did not run |
|---|---|---|
| `INVALID_RECEIPT_CHAIN` | a receipt whose predecessor digest does not match | the response never parsed |
| `LEDGER_COUNT_MISMATCH` | `obligation_counts` disagreeing with the rows read | same |
| `IMMUTABLE_RECORD_CHANGED` | a frozen record re-read with a different digest | same |
| `INVALID_LEDGER_DEPENDENCY` | a revision naming a predecessor outside the scope | same |
| `SNAPSHOT_CHANGED` | a snapshot id moving between pages | same |
| `LEDGER_LIMIT_EXCEEDED` | the read budget exceeded, `_reconcile.py` in the same loop | same |

---

## The `except Exception` — it is the CONTRACT at this site, and I did not narrow it

The brief says a broad `except` that flattens every cause into one code is a defect in its own
right whatever I found. **At this site it is not, and upstream's own test pins all four of its
properties.** `tests/test_reporting_frozen_read_corrections.py::test_response_validation_failure_stays_remote_typed_and_redacted`:

```python
assert error.value.code == "STATUS_READ_FAILED"
assert SECRET not in str(error.value)
assert SECRET not in repr(error.value)
assert error.value.__context__ is None
assert error.value.__cause__ is None
```

So the breadth and the placement are both load bearing: narrowing the `except` would let a
provider's own exception through, and raising **inside** it would chain the refused payload
onto the error through `__context__`. `test_transport_or_validation_failure_is_closed_and_does_not_restart`
asserts the same for a provider raising with a secret in its message. Both pass before and
after this change. Changing either would be weakening a redaction guarantee to make a
diagnosis convenient, which is the trade this repository does not make.

**WHAT WAS ACTUALLY WRONG IS THAT THE CAUSE WAS UNOBSERVABLE**, and that is fixed. For a
release, a response the emission correctly refused reported "get_reporting_status could not be
read" and nothing anywhere could say what had been refused — 99 tests, each expecting the
specific code its own chain defect earns, and no way to tell the mask from the thing masked.

`_refused_at` now reports the cause to `logging.getLogger("adcp.reporting._reconcile")` at
DEBUG, **redacted by construction**: for a `ValidationError` it takes each row's `loc` path
and `type` code and nothing else — `msg` and `input` are dropped, because a provider's payload
may hold a credential and that is the thing the redaction exists to keep out. For any other
exception it is the class name alone. Observed:

```
DEBUG adcp.reporting._reconcile: get_reporting_status refused: ValidationError:
  completed.periods.periods.0.schedule.period_anchor [required],
  completed.periods.periods.0.schedule.period_timezone [required]
```

The exception object is byte-identical to before: same code, same message, no `__cause__`, no
`__context__`, nothing of the payload on it.

### The ORDER question, answered and not ours to fix

The brief's third case — the specific diagnosis must not be reachable only when an unrelated
field parses — **is live here, and the ordering is in upstream's own stub.**
`Pages.get_reporting_status` validates the whole `GetReportingStatusResponse` before returning
it, so a schedule's anchor decides whether a receipt-chain diagnosis is reachable. Our load
path never sees a response to reorder around: it receives an exception from the client.
Reordering would mean editing upstream's test stub, which is a fork beginning, so it is
reported rather than done. With the payload corrected the question does not arise.

---

## `_consumer.py:430`, the third site, checked in the same pass

`src/adcp/reporting/_consumer.py:430` raises `STATUS_READ_FAILED` for a summary view, and it
is **not** a masker: it has no `except` at all. It calls
`client.get_reporting_status(...)` unguarded and raises only on `not result.success or
response is None`. Left unchanged.


---

## The three figures, measured together

**1. `./check` — unmoved, all three** (run after cause 1 landed, 217 s cold):

```
emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059
kind: verdict 0, deferred 0, chained 0  ->  primary 0, chained 0
approximated 383 facts in 148 documents
```

**2. `make lint` and `make typecheck-all` — red on trunk, and UNMOVED by this change.**
Reported rather than claimed green, because they are not: `lint` is **255 errors** and
`typecheck-all` is **4,118 errors in 694 files** both before and after, measured by stashing
the change and re-running. The bulk is `src/adcp/types/legacy_names.py` and other lanes'
files. My own two source files are clean under `ruff` and contribute 0 of the 4,118.
`make test` was not run to completion: the repository suite is long and the figure that
matters for this row is the drop-in one below; `tests/test_legacy_asset_helpers_derivation.py`
passes 5/5 and `tests/test_reporting_frozen_read_safety.py` is 71 failed / 22 passed both
before and after, which is the payload defect and not this change.

**3. The drop-in suite** —
`survey regenerate --wheel $SP --out /srv/ws/dropin-reporting --run`, digest
`b9b14e1da126cc758646382cddec5dd05b9ecacf91876d76575ec830389427b5`:

| | before | after |
|---|---|---|
| passed | 10,551 | **10,575** |
| failed | 1,253 | **1,229** |
| skipped / errored / xfailed | 2,001 / 12 / 1 | 2,001 / 12 / 1 |
| collected | 13,818 | 13,818 |

**+24 passed, −24 failed.** Cause 1's `IndexError` set goes **26 → 0**; 24 of those 26 now
pass and 2 fail on a different cause further along, which is why the net is 24 and not 26.

**`STATUS_READ_FAILED` assertions remaining: 65**, unchanged — and that is the correct
outcome of this row. They are blocked on the payload correction named above, which is data
this row may not write. The `== 'STATUS_READ_FAILED'` count is 65 of the 101 failures
mentioning the code; the rest mention it in a traceback rather than an assertion.

---
---

# Appendix — the keyless residue: 3 files, 41 failures, four verdicts

Read off `/srv/ws/dropin-keyless/junit/chunk-*.json` and never re-enumerated by a run.
**`chunks read: 4`**, quoted from `survey causes` itself — the whole suite, 13,817 collected,
10,572 passed / 1,232 failed. A run whose report is partial would read as a plausible smaller
number, so the count is checked before any figure below is quoted.

Counts from `survey causes /srv/ws/dropin-keyless`, which puts all three files in the
**RESIDUE** (212 failures no rule claims, 32 with a frame of ours):

| file | residue failures | verdict |
|---|---|---|
| `tests/test_decisioning_webhook_emit.py` | 14 | **PAYLOAD** → `nocanon` |
| `tests/test_reporting_exact_request_models.py` | 10 | **3 OURS** (emission) + **15 EXPECTATION** |
| `tests/conformance/reporting/test_reporting_notification_packaging.py` | 8 | **HARNESS** → provisioning |

**No source change this round.** Every verdict is a finding whose fix is outside this row's
write scope, so nothing was edited and no drop-in run was taken — the figures are the
baseline's, and a run of mine would have reported a delta of zero. The lock at
`/srv/ws/.adcp-dropin-run.lock` was not taken for the same reason.

---

## Isolated first: the packaging row is not packaging. `build` is absent from the venv.

5 of the 8 failures in `test_reporting_notification_packaging.py` are
`notification distribution build-sdist-and-wheel: exit 1`. The test redacts its own stderr to
a line count and a digest, so the cause is **proven by hash rather than guessed**:

```
reported: {"lines":1,"sha256":"bc9511e341bf0f7971dbb31e0e331ce0df248aa3aaddc58b0061aec4012b498b",
           "trace":[],"classification":"unclassified"}
candidate: "/srv/ws/dropin-keyless/.venv/bin/python: No module named build\n"
sha256:    bc9511e341bf0f79…  MATCHES,  63 chars,  1 line
```

Reproduced directly: `./.venv/bin/python -m build …` in the drop-in tree answers
`No module named build`, exit 1, in 32 ms — which is the `elapsed_ms=32` the failure reports.

**So it is neither `MANIFEST.in` nor `pyproject.toml` package data, and nothing about types.**
The `build` module is simply not installed in the drop-in venv, and the test shells out to it.
I have therefore **not** touched either file: the brief allows them only if the packaging row
proves it, and the proof points the other way. **The fix is the harness's provisioning step**
(`survey/**`, the drawcost lane): `build` belongs in the drop-in venv beside the siblings the
`== 11. provisioning` step already installs.

One detail worth passing on: their own redaction called this `"classification":"unclassified"`
because its signature table looks for `ModuleNotFoundError`, and python's `-m` launcher writes
`No module named build` instead. A row for the launcher's spelling would classify it.

---

## `test_reporting_exact_request_models.py` — 3 OURS, 15 EXPECTATION

### The 3 that are OURS: a document default materialised onto a field the document forbids

`media-buy/get-media-buy-delivery-request.json` states **both** of these:

| | |
|---|---|
| `#/properties/include_package_daily_breakdown` | `{"type": "boolean", "default": false, …}` |
| `#/allOf/1` | `{"if": {"required": ["reporting_revision_id"]}, "then": {"not": {"anyOf": [… {"required": ["include_package_daily_breakdown"]} …]}}}` |

Our class carries the document's default, `include_package_daily_breakdown = False`, and
pydantic then puts it in the dump. **The proof is a round trip through our own model:**

```python
raw = {"account": {"account_id": "acct_a"}, "reporting_revision_id": "rpr_x",
       "pagination": {"max_results": 100}}
enc = GetMediaBuyDeliveryRequest.model_validate(raw).model_dump(mode="json", exclude_none=True)
# -> {..., "include_package_daily_breakdown": false, "include_window_breakdown": false}
GetMediaBuyDeliveryRequest.model_validate(enc)
# -> REFUSED: include_package_daily_breakdown  forbidden when reporting_revision_id [type=not]
```

**Our own dump of a valid request produces a payload our own model refuses.** That is not a
matter of taste and it is not the test being fussy: a JSON Schema `default` is an annotation —
draft-07 does not let it affect validation and it certainly does not put a key on the instance
— and materialising it as a pydantic default writes a key the document forbids at that
position. `exclude_unset=True` omits it, which is what the absent-unless-set reading would
give for free.

**The blast radius is bounded and measured**: over 3,119 emitted classes, 905 optional fields
carry a non-None default and **4** of them are forbidden by a rule of their own class —

```
media-buy/get-media-buy-delivery-request.json#  GetMediaBuyDeliveryRequest.include_package_daily_breakdown = False
media-buy/get-media-buy-delivery-request.json#  GetMediaBuyDeliveryRequest.include_window_breakdown       = False
media-buy/build-creative-request.json#          BuildCreativeRequest.max_variants                        = 1
media-buy/build-creative-request.json#          BuildCreativeRequest.keep_mode                           = 'keep_all'
```

all four with the document's own default, all four named in a conditional clause of the same
document.

**The keyword is `default` and the fix is where it is lowered**, which is `codegen/**` and not
this row's scope. Reported here rather than done. The narrow reading for whoever takes it: for
an OPTIONAL property, a document `default` should not become the pydantic field default — the
field is absent unless set, and the document's value is an annotation.

### The 15 that are an EXPECTATION on a message, with the behaviour measured as correct

Every one fails with `AssertionError: Regex pattern did not match`. The tests use
`pytest.raises(ValidationError, match=…)` against upstream's own hand-written validator prose:

| the test expects | ours says, in the document's words |
|---|---|
| `exact revision requests forbid aggregate selectors` | `forbidden when reporting_revision_id [type=not]` |
| `pagination requires reporting_revision_id` | `required when pagination [type=required]` |

**The refusal they are testing for does happen — measured, not asserted.** Over the ten
aggregate selectors the document's `#/allOf/1` forbids, with each supplied explicitly as
`None` and as `False`: **20 refused, 0 admitted.** `pagination` without a
`reporting_revision_id` is refused too. So the `pytest.raises` is satisfied and only the
`match=` fails.

That makes these a test expectation on an implementation detail — the wording of a validator
message, which no document states — and not a behavioural obligation. **Named and left
failing.** No model is weakened and no message is reworded to make them green: our message is
the document's own clause, which is the better of the two to ship.

---

## `test_decisioning_webhook_emit.py` — 14 failures, one PAYLOAD cause

All fail the same way: `CreateMediaBuyRequest … is not valid under any of the 3 branches`.
The helper `_make_request` builds

```python
{"account": …, "brand": …, "idempotency_key": …, "start_time": …, "end_time": …,
 # create-media-buy-request.json requires packages, a budget, or a proposal.
 "packages": [{"buyer_ref": "pkg_1", "product_id": "prod_1", "pricing_option_id": "cpm"}]}
```

`media-buy/create-media-buy-request.json#/anyOf` states three branches, and each was read:

| branch | title | requires |
|---|---|---|
| `#/anyOf/0` | Explicit packages with fixed allocation | `packages`, and **each item's `allOf` carries `{"required": ["budget"]}`** |
| `#/anyOf/1` | Explicit packages with seller-optimized allocation | `packages`, `total_budget`, `budget_allocation` |
| `#/anyOf/2` | Committed proposal execution | `proposal_id`, `total_budget` |

Our three branch classes refuse it for exactly those three reasons —
`packages.0.budget` required, `total_budget` required, `proposal_id` required. **No branch of
the document admits the payload, so the refusal is correct.**

The test's own comment is where the misreading is: *"requires packages, a budget, or a
proposal"* reads `budget` as a third alternative, and the document makes it a **per-package
requirement inside branch 0** rather than an alternative to `packages`.

**→ DATA, for the `nocanon` lane.** Add `"budget"` to the package item in
`tests/test_decisioning_webhook_emit.py::_make_request` — the smallest correction, satisfying
`#/anyOf/0` — or add `total_budget` plus `budget_allocation: {"mode": …}` for `#/anyOf/1`.

---

## One rule of the causes table misattributes 101 failures to this lane

`survey causes` reports

```
101  aliasnote  STATUS_READ_FAILED masking the code that names the defect
```

**Those 101 are not a masking defect and they are not this lane's to fix.** The diagnosis
merged at `dac86664e` established both halves: the mask is upstream's own asserted contract
(`test_response_validation_failure_stays_remote_typed_and_redacted` pins the code, the
redaction, and `__context__ is None`), and the cause is a payload that contradicts
`core/reporting-schedule.json#/allOf/0`. The owner's own message confirms the family is now
`nocanon`'s payload data.

So the rule's verdict is right about the signature and wrong about the lane and the cause.
Suggested correction: rename it to the payload family and point it at `nocanon` —
`the schedule payload omits period_anchor/period_timezone under alignment=billing_cycle`,
which is what a reader of the table needs in order not to re-diagnose it.
