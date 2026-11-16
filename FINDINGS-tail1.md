# Findings — fixtures that could not be made green, and why

Three causes, none of them in a test fixture. Each is reported with what was measured, the
clause of the document it is measured against, and the `src/` site. Per TASK.md the tests are
left RED rather than forced green.

Scope note: nothing under `src/` was touched. Line numbers are against
`src/` as of commit `344ffe985`.

---

## 1. `PrincipalService`'s success-path responses omit the envelope-required `status`

**Tests left failing (9, all of `tests/test_server_principal.py` except four):**

```
test_recognized_and_unconfigured_read_variants
test_sync_persists_state_negotiation_and_exact_replay
test_version_fence_rejects_stale_replacement
test_dry_run_does_not_call_proof_hook_or_persist
test_destination_transition_emits_invalidation_without_version_churn
test_suspension_preserves_generation_and_revocation_retires_it
test_seller_declaration_change_emits_without_version_churn
test_unsupported_declarations_persist_empty_intersection_and_exclusions
test_shared_store_cas_rejects_one_of_two_concurrent_fenced_writes
```

**What the document says.** `core/protocol-envelope.json` states `required: ["status"]`, and both
`protocol/get-principal-response.json` and `protocol/sync-principal-response.json` compose it
through their top-level `allOf`. The envelope's own description is unusually explicit about the
consequence:

> The `status` field is REQUIRED on every task response envelope, including synchronous metadata
> responses (e.g., `get_adcp_capabilities`) where the value is `completed`. Agents shipping
> responses without a top-level `status` are non-conformant regardless of whether the task body
> schema would otherwise validate.

**What was measured.** Every response the service builds goes through
`model_validate` on a literal dict. Of the seven sites, the two REJECTION paths supply `status`
and the five success paths do not:

| site | builds | `status` |
| --- | --- | --- |
| `src/adcp/server/principal.py:162` (`_failed`) | failed sync | `"rejected"` |
| `src/adcp/server/principal.py:378` | failed read (kind changed) | `"rejected"` |
| `src/adcp/server/principal.py:374` | `unconfigured` read | **absent** |
| `src/adcp/server/principal.py:394` | `recognized` read | **absent** |
| `src/adcp/server/principal.py:803` (`_current_response`) | `current` read | **absent** |
| `src/adcp/server/principal.py:471` | `validated` dry run | **absent** |
| `src/adcp/server/principal.py:487` | `applied` sync | **absent** |

so the five raise `ValidationError: status Field required` under the new emission. The split is
itself the evidence that this is an oversight and not a position: the same module supplies the
field where it happens to have written it and omits it everywhere else.

**Why no fixture can fix it.** These tests call `PrincipalService` and never construct a response;
the omitted field is supplied inside `src/`. There is no argument to `sync_principal` or
`get_principal` that reaches it.

**The fix, when src is in scope.** Add `"status"` to the five success-path dicts: `"completed"` on
all five. Both response documents additionally state a top-level if/then narrowing it where
`result.kind == "failed"` to `enum: ["failed", "rejected"]`, which the two existing rejection
sites already satisfy; the success branches are unconstrained beyond the envelope's own
`enums/task-status.json`.

---

## 2. `ProposalCapabilities` validates a `media_buy` FRAGMENT against a document that conditionally requires a sibling

**Tests left failing (4, in `tests/test_decisioning_negotiation.py`):**

```
test_platform_router_routes_compact_refinement_to_proposal_manager
test_platform_router_rejects_declared_refinement_without_callback
test_capability_discovery_projects_manager_refinement
test_authenticated_capability_discovery_projects_tenant_manager_refinement
```

**What the document says.** `protocol/get-adcp-capabilities-response.json` states, at
`properties.media_buy.allOf[0]`:

```json
{ "if":   { "required": ["proposal_refinement"] },
  "then": { "properties": { "lifecycle_tools": { "contains": { "const": "refine_proposals" } } },
            "required": ["lifecycle_tools"] } }
```

A `media_buy` that declares `proposal_refinement` must also declare `lifecycle_tools`, and that
array must contain `"refine_proposals"`. The new emission enforces this as a model-level rule
(`lifecycle_tools: required when proposal_refinement`), which is the document being read
correctly — requiredness is the conjunction, and this conditional is part of it.

**What was measured.** `src/adcp/decisioning/proposal_manager.py:248` validates the refinement
capability by wrapping it in a bare `media_buy` and handing that to the full response model:

```python
validated = MediaBuy.model_validate({"proposal_refinement": raw_refinement}).proposal_refinement
```

That dict has no `lifecycle_tools` and never could: the lines just above reject any key outside
`{"supported_dimensions", "max_alternatives"}`. So EVERY `proposal_refinement`, valid or not, now
raises:

```
$ ProposalCapabilities(sales_specialism="sales-guaranteed",
                       proposal_refinement={"supported_dimensions": ["total_budget"]})
ValidationError: 1 validation error for GetAdCPCapabilitiesResponseMediaBuy
lifecycle_tools
  required when proposal_refinement [type=required, input_value=None, input_type=NoneType]
```

`lifecycle_tools` is not a property of `proposal_refinement` — it is a sibling the ADOPTER's
capability projection supplies, and the fragment under validation is by construction not the
node the conditional is about.

**Why no fixture can fix it.** The four tests only pass `proposal_refinement` to
`ProposalCapabilities`; the fragment is assembled inside `src/`. (The one direct
`MediaBuy.model_validate` in this file WAS a fixture problem and is fixed in commit `51be784bc`:
a seller declaring refinement support declares the tool it obliges itself to serve.)

**A second-order effect worth noting.** `test_proposal_manager_rejects_invalid_refinement_capability`
currently PASSES, and passes vacuously: it asserts `pytest.raises(ValueError)` over five invalid
refinement capabilities, and right now every capability raises, including the valid ones. It will
stop being a vacuous pass only once this is fixed.

**The fix, when src is in scope.** Validate the refinement against the node the document states it
at, not through a fragment of its parent — e.g. hand the sub-model
(`MediaBuy.model_fields["proposal_refinement"]`'s annotation) the mapping directly, or supply
`lifecycle_tools: ["refine_proposals"]` in the throwaway wrapper, which is what the document says
a real declaration would carry anyway.

---

## 3. The v1→v2 product projection is gated on a canonical parse FAILURE that no longer happens

**Test left failing (1, in `tests/test_client.py`):**

```
test_get_products_still_projects_legacy_format_ids
```

("Canonical-first parsing must retain the legacy compatibility fallback.")

**What the document says.** `core/product.json` states the two addressing forms as a field-level
`anyOf` over `required: ["format_ids"]` and `required: ["format_options"]`, with its own text:
*"Products MUST carry `format_ids`, `format_options`, or both during the 3.x migration window."*
`format_ids` is `deprecated: true` there, and per `CLAUDE.md` deprecated is metadata, not absence —
so the canonical `Product` class STATES `format_ids`, and a product carrying only `format_ids` is
a schema-valid `get-products-response`. The new emission admits it, correctly.

**What was measured.** `src/adcp/client.py:2304` (`_canonicalize_get_products_result`) uses "the
canonical parse failed" as its proxy for "this response is legacy-shaped":

```python
canonical_result = self.adapter._parse_response(raw_result, GetProductsResponse)
...
if canonical_result.success and canonical_result.data is not None:
    ...                      # returns here; no projection
    return canonical_result
legacy_result = ...          # project_legacy_product() lives beyond this point
```

With a `format_ids`-only product the canonical parse now SUCCEEDS, so the function returns at the
early branch and `project_legacy_product` is never called:

```
format_options: None
format_ids:     [FormatReferenceStructuredObject(agent_url=.../seller.example, id='display_300x250_image', ...)]
metadata:       {'projection': {'diagnostics': []}}
```

The projection machinery itself is FINE — called directly on the same product it still produces
the declaration the test asserts:

```
format_options: [ImageFormatDeclaration(format_kind='image',
                 params=CanonicalFormatImage(width=300, height=250, ...),
                 v1_format_ref=[... id='display_300x250_image'], ...)]
diagnostics: []
```

So the defect is the GATE, not the conversion: parse success no longer implies canonical format
declarations are present, because the document admits a product that has only the v1 form.

**Why no fixture can fix it.** The only way to make the assertion pass from the test side is to
delete what it asserts — that a `format_ids`-only product still reaches the canonical surface with
a projected `format_options`. Asserting `format_options is None` instead would record the fallback
as dead rather than test it. (The envelope `status` this fixture also lacked IS fixed, in commit
`6cf0657e9`; the projection failure is what remains.)

**The fix, when src is in scope.** Gate the projection on what it is actually about — a product
that carries no `format_options` — rather than on the response failing to parse. Note the
direction rule in `CLAUDE.md`: `registries/v1-canonical-mapping.json` is authoritative for v1 → v2
only, which is the direction this path needs, so nothing here has to invent a mapping.

---

## Not a finding: three decisions these fixtures predated

Recorded so they are not re-filed as defects. All three were fixed in the fixture, which is where
the error was.

1. **`core/protocol-envelope.json` `required: ["status"]`, composed by `allOf`** — hand-built
   response fixtures in `tests/test_principal.py` and mocked wire payloads in
   `tests/test_client.py`. Requiredness is the conjunction of the node and its ancestors.
2. **`media-buy/commercial-terms.json` `properties.purchases.items.allOf[1]`** requires
   `start_time` and `end_time` per purchase, though `media-buy/product-purchase.json` alone
   requires neither. The composing node is half of the conjunction.
3. **A document's `not`/`uniqueItems` refuses at the TYPE what a service used to refuse in its own
   prose** — `sync-principal-request.json`'s `not: {enum: ["scheduled", ...]}` on
   `notification_configs[].event_types[]`, and `refine-proposals-request.json`'s
   `uniqueItems: true` on `refinements`. Where the document closes the path, the test asserts the
   refusal and the field it names, not the service message for a request it can no longer be
   handed.
