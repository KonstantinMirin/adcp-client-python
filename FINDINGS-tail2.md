# Findings from the tail2 fixture lane

All four files in this lane's task are green. Nothing was left red. These are two things
measured on the way that are NOT fixture problems and that I could not act on inside the
write scope (`tests/test_literal_discriminator_defaults.py`,
`tests/test_negotiation.py`, `tests/test_delivery_manifest_readback.py`,
`tests/test_reporting_frozen_read_corrections.py`), plus one note for a neighbouring lane.

---

## 1. TWO DECISION DOCUMENTS DISAGREE ABOUT THE PINNED DEFAULT, AND THE INDEX CITES THE LOSING ONE

**This is a defect of the DECLARATION, not of the emission — and it is in the decision index
itself, which is the one place CLAUDE.md sends a reader to settle exactly this.**

`tests/test_literal_discriminator_defaults.py` asserted that a required property pinned by
`const` defaults on the Python route: `TextContent(content='hello')` constructs,
`UrlVastAsset(url=...)` constructs. I corrected the file AGAINST that, and the reason is
below — but the reader who checks my work against the index will find the index agreeing with
the test I changed.

| source | what it says | when |
| --- | --- | --- |
| `docs/plan/rebuild-plan.md` §2, THE DECISIONS INDEXED, row 9 | "**A required property the document PINS to one value may default to it.** … `ImageAsset(url=…, width=…, height=…)` supplies `asset_type="image"` itself, because `const` states it." | — |
| `verdicts/a-pinned-default-is-the-documents-own.md` | the same, with the route split spelled out: the Python route supplies the value, the JSON route and `strict_validate` keep refusing the omission | commit `3833a120b`, 2026-11-13 **00:16** |
| `docs/reading-a-document.md` §3 | "**A DISCRIMINATOR'S TAG IS EXTRACTED BEFORE DEFAULTS APPLY.** So a default cannot rescue an absent discriminator under a field-name discriminator." Measured: 277 discriminator positions, all 277 required. | — |
| `docs/migration-from-upstream.md`, Worked example 2 | "**We do not add the defaults back**: a class that supplies a required `const` for you admits a payload the document refuses, and the whole point of the branch classes is that they do not." Shows `DAASTAssetUrl(url=...)` raising. | commit `c2edb2ea6`, 2026-11-13 **13:06** |

Measured on the emission: **the pinned default is not implemented at all.**
`ImageAsset(url=…, width=300, height=250)` — the verdict's own worked example — raises
`asset_type Field required`, and `codegen/ir.py`/`codegen/render.py` have no predicate for it
(the only hits for "pins" are a comment on the `const` row).

I resolved it toward the emission, on three grounds: the migration document is the later of the
two writings; `reading-a-document.md` §3 makes the default technically inert for discriminators,
which is where the verdict's own examples all live; and the verdict's "Where it goes" section is
written as work owed rather than work done.

**That resolution is mine and it is not the owner's.** What is owed is one of two edits, and
only the owner can pick:

* if the verdict stands, the index row is right, the emitter owes the predicate, and
  `migration-from-upstream.md`'s worked example 2 contradicts a decision taken thirteen hours
  before it; or
* if the migration document stands, **the index row and the verdict are stale and should be
  struck or marked**, because the row's "what a consumer sees" column currently describes a
  construction that raises.

The cost of leaving it is the exact cost §2 opens by measuring: the next lane to meet a
`Field required` at a `const` property will read the index, find row 9, and file the emission
as a defect — which is the 1,239-pair rediscovery the index exists to prevent, running in the
other direction.

---

## 2. REVISION-ONLY CONSUMER-STATUS BINDING IS UNREACHABLE FROM ANY DOCUMENT-VALID PAYLOAD

`src/adcp/reporting/_reconcile.py` supports binding a consumer status to an obligation by
`reporting_revision_id` alone, with no `reporting_obligation_id` — the ledger retains
`consumer_statuses[0].reporting_obligation_id is None` and resolves the owner through the exact
revision. **No payload the pinned bundle admits can reach it.**

`core/reporting-consumer-status.json` makes the owner's requiredness a conjunction, and every
member of the `consumer_status` enum is covered:

| `consumer_status` | `allOf` branch | what it says about `reporting_obligation_id` |
| --- | --- | --- |
| `received` | `allOf[0].then` | **required**, with `reporting_revision_id` and `observed_revision_content_sha256` |
| `obligation_missing` | `allOf[1].then` | **forbidden**, and so is `reporting_revision_id` |
| `revision_missing` | `allOf[2].then` | **required**; `reporting_revision_id` forbidden |
| `unreadable` | `allOf[3].then` | **required**, with `reporting_revision_id` and `failure_code` |
| `content_mismatch` | `allOf[4].then` | **required**, with three more |

So a status either names its owner or names neither key. Asked directly, the document's own
validator for the owner-less `received` status points at `['allOf', 0, 'then', 'required']`,
and `load_reporting_ledger` refuses the page with `STATUS_READ_FAILED` before the binding code
is reached.

This is not a fixture problem and I did not treat it as one: the fixture half that exercised it
is now the document's refusal (see `test_a_received_status_without_its_owner_is_not_readable`).
The open question is about `src/`, and it is a question rather than a defect:

* if the tolerance is for **already-typed legacy records** — rows parsed under an earlier schema
  and carried forward in process, never re-read from the wire — then it is live, and what is
  owed is a comment saying so, because its only test reached it through a wire payload;
* if it was meant to tolerate a wire payload, it is dead code under 3.2.0-rc.6 and the honest
  move is to delete it rather than keep a path no peer can exercise.

---

## 3. NOTE FOR WHOEVER OWNS `tests/test_reporting_frozen_read_safety.py`

That file is not in my write scope and I did not touch it. It has 6 failures, and **2 of its
distinct causes are the two I fixed in `test_reporting_frozen_read_corrections.py`** — the
measurement transfers directly:

* `test_legacy_typed_status_without_owner_uses_exact_revision_binding` pops
  `reporting_obligation_id` from a `received` status. That is finding 2 above: `allOf[0].then`
  requires it, and the read fails with `STATUS_READ_FAILED`.
* `test_rejected_predecessors_and_only_the_accepted_current_leaf_satisfy[adjustment]` fails with
  `frozen adjustment counts do not match current leaves`, which is the
  `pending_adjustment_count` cause: `_response` supplies `pending_adjustment_count=0` because
  `core/reporting-obligation.json` allOf[7] requires it pinned `const: 0` for a
  `consumer_receipt` owner at healthy/complete health, and a fixture that then removes the
  accepted receipt leaves the `0` behind as a false declaration over a history with one pending
  adjustment.

Its other failures (`test_every_page_requires_the_frozen_total`,
`test_frozen_metadata_is_checked_including_wholly_legacy_pages[health-*]`,
`test_health_finality_and_exact_revision_selectors_cannot_hide_history`) I did not diagnose.
