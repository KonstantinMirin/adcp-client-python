# The 61 `Field required` failures: what was fixed, and what was not

Measured against `test-results/before.json` (`failed=496, error=5, passed=14565,
total=17893` — matches the trunk figure in `TASK.md`).

Every case below was read through `adcp.types._base._refuse_at`, which resolves the
conjunction, and not off a single node by hand. **No case turned out to be a non-conjunction
— the model is right about requiredness everywhere these 61 land.** The envelope key is
required at `core/protocol-envelope.json`, reached as `#/allOf/1` of each task-response
document; `enums/task-status.json` gives it nine members and `"completed"` is the member
chosen at every site here, which is the member the envelope's own description names for a
synchronous response ("including synchronous metadata responses (e.g.
`get_adcp_capabilities`) where the value is `completed`").

What follows is the residue: cases where the fixture was genuinely short a key the document
requires but where completing it did **not** turn the test green, and cases where the
short-a-key site is not a fixture at all.

---

## 1. The short-a-key site is PRODUCTION code, not a fixture — 15 tests, out of write scope

`TASK.md` puts `src/` and `examples/` out of scope entirely. These fifteen failures are the
same conjunction, but the dict that omits `status` is written by the SDK or by the shipped
example, so no edit inside the test files can reach them.

| tests | site | what it builds without `status` |
|---|---|---|
| `tests/test_server_principal.py` (9) | `src/adcp/server/principal.py:162, 374, 378, 394, 471, 487, 803` | `SyncPrincipalResponse` / `GetPrincipalResponse` via `model_validate` |
| `tests/test_decisioning_refine.py` (3) | `src/adcp/decisioning/refine.py:238` | `GetProductsResponse(products=…, proposals=…, refinement_applied=…)` |
| `tests/test_hello_seller_integration.py` (3) | `examples/hello_seller.py:305, 318, 332` | the stub returns `{"media_buys": []}`, `{"formats": []}`, `{"creatives": …}` |

The three `hello_seller` tests say so in their own names — "returns a wire shape that
satisfies `GetMediaBuysResponse`" — so the example is the thing that is non-conformant, and
`core/protocol-envelope.json` says it plainly: "Agents shipping responses without a
top-level `status` are non-conformant regardless of whether the task body schema would
otherwise validate."

**None of these is a compiler defect.** Each needs one key added at a production site.

---

## 2. `core/reporting-delivery-capabilities.json`: the keys are required, and the tests grade their ABSENCE — 6 tests

* `tests/conformance/reporting/test_reporting_status_capabilities.py` (4)
* `tests/test_reporting_wire_defaults.py` (2)

The document requires `configuration_task` and `status_task` and states each as a `const`,
so the fixture really is short two keys and the values are the document's own. **Supplying
them was measured and then reverted, because each of these tests asserts the ABSENCE of the
very keys the document requires** — completing the fixture cannot make them pass:

```python
assert not any(k.endswith(("_task", "_notification")) for k in raw)
assert "supports_webhook_activity" not in raw and "reliable_reporting_version" not in raw
assert ("managed_delivery" in raw) is (tier != "core")
```

Measured on the dump of a complete, document-valid instance:

```
fields_set: authorization_revocation_seconds automated_recovery_window_seconds
            configuration_task offerings receipt_task resource_retention_days
            status_retention_days status_task supported
dump keys : … configuration_task … managed_delivery … receipt_task reconciled_billing
            … status_task supported supports_webhook_activity
```

Two separate things defeat these assertions, and **both are decisions, not defects**:

1. **The `_task` keys cannot be unset any more.** They are required, so a valid instance
   always carries them and the dump always shows them. The assertion was written when they
   were optional-with-a-default.
2. **A `default: false` is materialized and therefore dumped.** `rebuild-plan.md` §"the
   keyword table", `default` row: "PROP → the field's default". `OmittedNotNull` drops a
   field only when its value is `None`, and `False` is not `None`, so `managed_delivery`,
   `reconciled_billing` and `supports_webhook_activity` appear at every tier.

Repairing these means rewriting what the tests grade — "unset `_task` keys are omitted" has
no instances left, and "false flags are omitted" contradicts the `default` decision. That is
the owner's call, not a fixture completion, so it was not made here.

A third, related measurement, recorded because it reads like a defect and is **declared**:
with the fixture complete, `#/allOf/3` and `#/allOf/4` then demand
`resource_retention_days`, `authorization_revocation_seconds` and `receipt_task` at the
`core` tier, where the document's `if` does not hold (`_refuse_at` accepts that payload).
`__adcp_approximations__` records both pointers as `kind='WIDENED'`, `keyword='if'`,
attributed to `rebuild-plan.md §5 combinators/if` — the lowered `if` reads the flag's
presence, and the flag's `False` default makes it present. So a repaired fixture here owes
three further keys beyond the two `_task` consts.

(The one fixture of this shape that could be completed, because nothing in its test grades
the absence of a `_task` key, **was** completed and is green:
`tests/test_reporting_reconciliation.py::test_capability_uses_public_reporting_delivery_model`.)

---

## 3. The refusal still fires; only the message changed — 2 tests

* `tests/test_codegen_contract_compatibility.py::test_create_media_buy_request_requires_one_root_anyof_group`
* `tests/test_trusted_match_validation.py::test_provider_registration_requires_identity_dimensions_when_identity_match_enabled`

Both payloads are *meant* to be refused and both **are** refused. Only the sentence changed:

| test expects | the refusal now says |
|---|---|
| `at least one of these field groups` | `packages\n  #/anyOf/0 (ExplicitPackagesWithFixedAllocation): Field required` |
| `countries is required` | `countries\n  #/anyOf/1 (TMPProviderRegistrationIdentityMatch): required when identity_match=True` |

There is no key to add — adding one would remove the refusal the test exists for. Fixing
these means rewriting the expected string, and `docs/reading-a-document.md` rule 6 cuts both
ways here: the new message cites the document's own pointer and keyword where the old one
was SDK prose, but whether losing the "at least one of these field groups" explanation is an
improvement or an error-quality regression is a judgement about the SDK's output, not about
the document. Left for the owner.

---

## 4. Fixture completed, test still red on an unrelated pre-existing ground — 2 tests

* `tests/test_lazy_rebuild.py::test_a_deferred_instance_dumps_through_a_plain_pydantic_parent`
  — the probe's `CreateMediaBuyRequest` now carries `#/anyOf/0`'s `budget` and validates.
  The probe then fails one line later, on
  `Parent(item=AdcpAgentsAuthorization.model_construct(root=None)).model_dump(mode="json")`,
  which is `{'item': {}}` where the probe asserts `{'item': None}`. A deferred root model's
  dump, nothing to do with requiredness.
* `tests/test_mixed_legacy_projection_regression.py::test_managed_completion_preserves_rejection_rows[True-inline]`
  — the handler's `SyncCreativesSuccessResponse` now carries the envelope `status`. The test
  then fails with `AttributeError: 'ImageFormatDeclaration' object has no attribute
  'legacy_format_refs'`, which is exactly how its three sibling parametrizations
  (`[False-inline]`, `[False-task]`, `[True-task]`) were already failing before this work.
  The conjunction ground is gone; the file's failure count is unchanged.

Both fixture edits are kept: the key the document requires belongs there either way.

---

## 5. Not a missing key at all — 2 tests

* `tests/test_error_narrowing.py::test_e2e_creative_manifest_missing_width_height_surfaces_actionable_errors`
  — the fixture omits `width`/`height` **on purpose**; the test grades `narrow_union_errors`.
  It fails on `assert all("image" in err["loc"] for err in narrowed)`, because a third error,
  `assets.hero.list[function-wrap[<lambda>()]]: Input should be a valid list`, survives
  narrowing beside the two `missing` ones. An error-narrowing question.
* `tests/test_proposal_lifecycle_e2e.py::test_create_media_buy_rejects_disallowed_pricing_model`
  — the fixture carries **both** `proposal_id` and `packages`, and
  `media-buy/create-media-buy-request.json` forbids that combination in all three root
  groups: `#/anyOf/0` and `#/anyOf/1` state `not: {required: ["proposal_id"]}`, and
  `#/anyOf/2` states `not: {anyOf: [{required:["packages"]}, …]}`. Nothing can be *added*.
  Dropping `proposal_id` makes the request valid but removes the proposal whose recipe
  supplies the pricing overlap the test is about; dropping `packages` removes the subject.
  The scenario as written is not expressible in this document — a question for whoever owns
  §D4, not a fixture edit.

---

## 6. The fixture IS short `status`, and supplying it defeats the test's own assertion — 1 test

`tests/test_negotiated_catalog_purchase.py::test_completed_payload_does_not_invent_newer_response_defaults`

The vector is a 3.0-shaped body read through `LegacyGetProductsResponse`, which is
`media-buy/get-products-response.json` under an upstream spelling
(`src/adcp/types/legacy.py:66`) and so requires the 3.2 envelope `status`. Setting
`wire["status"] = "completed"` validates — and then
`assert "status" not in payload` fails, because the coordinator echoes what it was given.
The assertion reads *absence on the wire* as proof of *not inventing*, and those came apart
the moment the key became required. The edit was reverted; the test is untouched.

Also outside this write scope, the same vector file
(`tests/conformance/vectors/products-only-brief-compatibility/vectors.json`) is read by four
other tests in that file.

---

## Adjacent, not taken

`tests/test_media_buy_store_integration.py` carries four further failures that are the same
family one step on — `status="active"` passed to `CreateMediaBuySuccessResponse` /
`UpdateMediaBuySuccessResponse`, and `"active"` is not one of `enums/task-status.json`'s
nine members. Only the one site inside an assigned `Field required` test was changed
(line 216); lines 152, 267, 314 and 456 are an invented-value family, not an omission, and
were left alone.
