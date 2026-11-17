# FINDINGS — the SDK built and sent payloads its own documents refuse

Every change in this lane is the DOCUMENT's answer. Where the document had no answer, nothing
was invented and the site is recorded below instead.

The oracle throughout is `strict_validate`, which reaches the schema half through
`adcp.types._base._refuse_at` and so resolves the requiredness CONJUNCTION — a property's own
node AND every ancestor's that applies to the same instance.

---

## The ground, in one sentence

`core/protocol-envelope.json` lists `status` in its own `#/required` and says why it matters:

> Agents shipping responses without a top-level `status` are non-conformant regardless of
> whether the task body schema would otherwise validate.

Every response document composes that envelope through `allOf`. So `status` is required at a
site whose task body never mentions it — which is exactly why these call sites were written
without it. The previous generator dropped the composed half; it no longer does, so `status` is
now a required field on the models and these sites raised `ValidationError` rather than merely
shipping a non-conformant payload.

---

## A. Responses built without the envelope `status` — FIXED

| site | document | pointer | value | why that value |
|---|---|---|---|---|
| `server/principal.py` get_principal `unconfigured` | `protocol/get-principal-response.json` | `#/allOf/1` `required:["status"]` | `completed` | the document's own `examples` |
| `server/principal.py` get_principal `recognized` | same | same | `completed` | the document's own `examples` |
| `server/principal.py` sync_principal `validated` (dry run) | `protocol/sync-principal-response.json` | same | `completed` | envelope: "Synchronous tasks … normally emit `completed`" |
| `server/principal.py` sync_principal `applied` | same | same | `completed` | the document's own `example` |
| `server/principal.py` `_current_response` `current` | `protocol/get-principal-response.json` | same | `completed` | the document's own `examples` |
| `decisioning/refine.py` `project_refine_response` | `media-buy/get-products-response.json` | `#/allOf/1` | `completed` | see below |
| `reporting/submissions/models.py` `_restore_confirmation` | `media-buy/sync-reporting-receipts-response.json` | `#/properties/status` `{"const":"completed"}` | `completed` | the only admissible value |
| `examples/hello_seller.py` × 6 stubs | per-tool response documents | `#/allOf/1` | `completed` | envelope's `status` description |

Three of the five principal values are literally transcribed from the documents' own
`examples`. The one value that is not — the dry-run branch, which has no example — is the
envelope's stated norm for a synchronous task; the dry run ran to completion and
`result.action` carries what it *would* have done.

**Neither principal document admits `completed` by accident.** Each states exactly one explicit
pin, at `#/if`–`#/then`: when `result.kind` is `failed`, `status` must be in
`["failed","rejected"]`. That constrains only the failure branch, which already emitted
`rejected`. All six response paths of `PrincipalService` are now accepted by their documents.

### `refine.py` — `rejected` was ruled out, not merely passed over

`media-buy/get-products-response.json` states no root `required` at all, so a task-body read
says `status` is optional and the conjunction says required. The alternative value is excluded
by the document, not by preference: `#/allOf/3` sends `status: "rejected"` to
`#/definitions/Shared5`, whose `required: ["status","reason"]` describes "a terminal business
outcome … [the seller] deliberately declines", and `#/allOf/2` forbids `reason`/`suggestions`
on any other status. A per-ask `refinement_applied[].status` of `unable`
(`#/definitions/Shared76`: `applied`/`partial`/`unable`) is a task-body outcome and does not
demote the envelope.

### `models.py` — the one site where the value was never a choice

`media-buy/sync-reporting-receipts-response.json` pins it twice: `status` is in the document's
OWN root `required: ["status","results"]`, and `#/properties/status` is
`{"const": "completed"}` — "Receipt batches complete synchronously with one result per
submitted receipt." Measured:

```
{"results": […]}                          REFUSED  status [missing]
{"status": "failed",    "results": […]}   REFUSED  status 'completed' was expected
{"status": "completed", "results": […]}   ACCEPTED
```

So "re-supply the status the retained evidence implies" resolves to the single admissible
literal. A retained per-item `result: "failed"` does not demote it — that is a task-body
outcome at `#/properties/results/items/anyOf/4` ("Failed reporting receipt"), and the batch it
was retained from did complete.

`status` is **not** part of the retained bytes: `_confirmation` returns
`canonical_json_utf8_v1` over a normalized list of
`{reporting_receipt_id, result, errors, receipt}`. The exact-byte round-trip proof is therefore
unchanged. Measured end to end on the cold-cache path that actually runs
`_restore_confirmation`:

```
before   ReportingSubmissionError: SUBMISSION_HISTORY_CORRUPT
after    validate_submission passes
```

### On swallowing the cause — DELIBERATELY LEFT AS IS

The `logger.debug` in `validate_submission` was not the defect; the malformed construction was,
and it sent a user hunting for corrupted data when the SDK's own restore path was what was
malformed.

The suppression itself is a **declared decision with a stated reason**.
`adcp._redaction.refused_at` drops pydantic's `msg` and `input` because pydantic interpolates
the input value into `msg` (`input_value='sk-live-…'`), and the payload here is retained seller
evidence. It keeps precisely the fault and not the data — the debug line for this very bug read

```
ValidationError: status [missing], results [too_short]
```

which names the fault exactly. Promoting that cause onto the raised `ReportingSubmissionError`
would move retained-evidence detail into a buyer-visible error, which is the thing the
redaction exists to prevent. With the construction fixed,
`SUBMISSION_HISTORY_CORRUPT` again fires only for history that is genuinely corrupt.

### `hello_seller.py` — and one slot that was mis-filled, not empty

`create_media_buy` and `update_media_buy` were not missing `status`; they were putting
`"active"` in it, a value `enums/task-status.json` does not contain, so every branch of their
`oneOf` refused it. The owning field says where it belongs, in its own words at
`create-media-buy-response.json#/oneOf/0/properties/media_buy_status`:

> This field carries the media buy lifecycle state; top-level `status` is reserved for the
> protocol-envelope TaskStatus (`completed` on synchronous success).

So `active` moved to `media_buy_status`, whose enum does contain it. Measured: with the success
branch's own `confirmed_at`/`revision` present,
`{"status":"completed","media_buy_status":"active",…}` is ACCEPTED.

Four stubs that gained `status` became fully conformant (`get_media_buys`,
`list_creative_formats_legacy`, `list_creatives`, `provide_performance_feedback`).

---

## B. Send sites that materialised a default the document forbids — SURVEYED IN FULL

The defect is the dump keyword, not the model: the model states the default the document
states, and `exclude_none=True` ALONE materialises it. Where a document forbids a field's
**presence**, that turns a legal request into a refused one.

**All 80 request classes** reachable from a `client.py` send site were scanned for a field
carrying a non-`None` model default whose presence some `not`/`required` in its own document
forbids. Zero unresolved. Exactly three matched.

| class | method(s) | verdict |
|---|---|---|
| `GetMediaBuyDeliveryRequest` | `get_media_buy_delivery`, `get_media_buy_delivery_legacy` | **CHANGED** |
| `LegacyBuildCreativeRequest` | `build_creative_legacy` | **CHANGED** |
| `SyncCatalogsRequest` | `sync_catalogs` | **LEFT ALONE** — see below |

### Changed

Both pointers are `if <mode selector present> then not {anyOf:[…required…]}` — a prohibition
on PRESENCE, keyword `not` over `required`.

`media-buy/get-media-buy-delivery-request.json#/allOf/1` — if `reporting_revision_id` is
present (`#/definitions/Shared1`), none of ten aggregate selectors may be. Two carry
`default: false`.

```
exclude_none=True                     {"reporting_revision_id":"rev_1",
                                       "include_package_daily_breakdown":false,
                                       "include_window_breakdown":false}   REFUSED
exclude_none=True, exclude_unset=True {"reporting_revision_id":"rev_1"}    ACCEPTED
```

`media-buy/build-creative-request.json#/allOf/7` — if `creative_representation_set` is
present, none of twenty-three generation knobs may be. Representation-set resolution is "a
seller-bound, deterministic, single-output selection mode. It cannot generate, transform,
refine, evaluate, sample, or fan out content" (`$comment`). Two carry defaults,
`max_variants: 1` and `keep_mode: "keep_all"`.

`get_media_buy_delivery_legacy` takes the SAME request document as the canonical method — the
legacy projection changes the response type, not what the request may carry.

### The hazard was measured, not assumed

The stated hazard is that a site which must send an explicit value would silently stop sending
it. It does not arise at either site:

* a field the caller set explicitly stays in `model_fields_set` and still ships —
  `include_window_breakdown=False` in non-exact mode survives, as does `max_variants=5`;
* at `get_media_buy_delivery` the explicit case cannot even arise in exact mode: the **model**
  refuses it first (`forbidden when reporting_revision_id`);
* every value dropped is one the caller never set AND one the document itself states as the
  default (`mode:"execute"`, `preview_output_format:"url"`, `max_variants:1`,
  `keep_mode:"keep_all"`), so a conforming seller reconstitutes the identical request.

### Left alone, and why

`SyncCatalogsRequest` is a **false positive of the presence scan**. Its `#/allOf/1` prohibition
is conditioned on the VALUE, not the presence:

```json
{"not": {"properties": {"dry_run": {"const": true}},
         "required": ["dry_run", "item_availability_updates"]}}
```

The materialised default is `false`, which does not satisfy the inner schema, so the `not`
holds. Measured ACCEPTED as-is with `item_availability_updates` present. Only an explicit
`dry_run=true` is refused — and `exclude_unset=True` would still send that, correctly, because
the request is genuinely contradictory. Separately, `delete_missing` there appears in a `#/if`
selector, so dropping it would change which branch applies.

The remaining 70 send sites materialise no default whose presence any document forbids. Adding
the keyword there would be churn that risks the opposite defect, so it was not done.

---

## Not fixed — recorded instead of guessed

### 1. `cache_scope` on the refine projection

`project_refine_response` is still refused, for a reason unrelated to the envelope:
`media-buy/get-products-response.json#/else/else/else` requires `["products","cache_scope"]`
("Standard response: products[] MUST be present and cache_scope MUST declare the response's
cache layer").

The value is a function of the REQUEST, and the document says so: "When the request did NOT
include `account`, the seller MUST return `cache_scope: 'public'`"; with an `account` the
seller MAY return either `public` or `account`. `project_refine_response(result, refines)`
receives only a `RefineResult` and the `refine[]` list — never the request. Threading it
through would mean editing `decisioning/handler.py`, which is outside this lane's write scope.
There is no value to derive here, only one to invent.

### 2. Task-body gaps in `hello_seller.py` stubs

Four stubs remain refused for shape reasons that are task body, not envelope. Each needs a
field whose value is seller business state this example does not model; authoring a plausible
`revision` or `reporting_period` would be inventing it.

| stub | still required |
|---|---|
| `get_products` | `cache_scope` (`#/else/else/else`) |
| `create_media_buy` | `confirmed_at`, `revision` (`#/oneOf/0/required`) |
| `update_media_buy` | `revision` (`#/oneOf/0/required`) |
| `sync_creatives` | `creatives[].action` |
| `get_media_buy_delivery` | `reporting_period`, `media_buy_deliveries[].status`, `[].by_package` |

These predate this lane and are unchanged by it.

### 3. Three `test_server_principal.py` failures the `status` fix UNMASKED

All nine baseline failures in that file were the same `ValidationError: status` at
`principal.py:374/471/487`. The fix resolves that error in all nine; in three, a second
assertion that the raise had been masking now surfaces. These are **not regressions from this
lane** and **not type defects** — in each case the document states the plain shape the SDK
produces, and the TEST encodes a stale typed-wrapper assumption:

| test | asserts | the document |
|---|---|---|
| `test_sync_persists_state_negotiation_and_exact_replay` | `first.context.correlation_id` | `context` is `{"type":"object","additionalProperties":true}` with NO declared properties — "Opaque correlation data … never parsed by AdCP agents". A plain dict is correct; `correlation_id` is not a declared attribute. |
| `test_suspension_preserves_generation_and_revocation_retires_it` | `destination_refs[0].root` | `#/definitions/Shared19` is `{"type":"string","minLength":1,"maxLength":255}` — a plain constrained string, not a RootModel. |
| `test_seller_declaration_change_emits_without_version_churn` | `[item.root for item in …async_adcp_versions]` | `#/definitions/Shared16` items are `{"type":"string","pattern":"^\\d+\\.\\d+$"}` — plain strings. |

Per this lane's rule ("if you conclude a type is wrong, STOP and report it") these were not
touched: the emitted types are faithful, the expectations are stale, and the `.root` surface is
visibly being worked by other lanes (`test_public_words_resolve.py`, `test_lazy_types.py`,
`test_wire_types.py` all fail in the baseline on the same theme). Rewriting the accessors here
would collide with that work.

---

## Gates

```
./check                        emitted 1059 / refused 0        (unchanged — the compiler was not touched)
ruff check src/ tests/         407 at base, 407 after          (did not grow)
```
