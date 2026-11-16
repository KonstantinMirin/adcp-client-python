# Findings — the 87-failure long tail, and the eleven left reporting

Eighty-seven failures across thirty-two files. Sixty-two were the test being wrong about this
emission and were re-pointed or deleted. **Twenty-five are left red**, and this file is why: each
names a file, what was measured, and where the repair is. Every one of them is outside this lane's
write scope (`src/`, `tests/fixtures/`, `examples/`) or is an instrument the owner asked to be left
alone.

Two counts worth stating up front, because they are the shape of the tail:

* **Six of the eleven grounds below are one decision biting production code.** §2's dump row —
  *"The dump omits `None` UNLESS the document requires the property … Serialisation keys on
  `required`, validation still keys on nullability"* — made the no-explicit-null marker's
  SERIALISATION half universal. Code written when that half meant "this property refuses null"
  now reads it as true of every optional property.
* **Nothing in the tail was the emitted type being wrong about its document.** Where a class
  refused something, the document refused it too, measured through `_refuse_at` or the document's
  own text. That is the sixth consecutive cluster with that outcome.

---

## 1. `is_no_explicit_null` ANSWERS TRUE FOR EVERY OPTIONAL FIELD

**`src/adcp/types/base.py:711`.** Reported by `tests/test_no_explicit_null.py` (repaired here by
asking the other half) and the proximate cause of findings 2, 3 and 4 below.

The marker has two halves, and the predicate reads one of them:

| half | where it lives | when the emitter writes it |
| --- | --- | --- |
| serialisation | `exclude_if=_is_absent` on the `FieldInfo` | **every optional property** |
| validation | `_AbsenceIsOmission` in `field.metadata` | only where the document admits no `null` |

`is_no_explicit_null` returns `field.exclude_if in (NoExplicitNull.exclude_if,
OmittedNotNull.exclude_if)` — the serialisation half alone. Measured on `UpdateMediaBuyRequest`:
**24 optional fields, 24 carrying the `exclude_if`, 20 carrying the validation half, and the 4
without it are exactly the 4 whose published node has a null branch** (`daily_budget_cap`,
`frequency_cap`, `budget_cap_timezone`, and one more). So the predicate says "this property refuses
an explicit null" about `budget_cap_timezone`, which accepts one on the JSON route and publishes
`anyOf: [..., {"type": "null"}]`.

Its own docstring is where the claim is made — *"the two are the same marker in substance — a JSON
`null` refused, a Python `None` read as absence, a `None` left off the dump, and no null branch
published"* — and the decision's own sentence is what makes it false: serialisation keys on
`required`, validation on nullability. `adcp.types._base.omits_null` reads the same half and has the
same reach.

**The repair** is a predicate over `field.metadata` — `isinstance(entry, (_RefuseJsonNull,
_AbsenceIsOmission))` — which is what `tests/test_no_explicit_null.py::_refuses_json_null` now does
locally. Callers to re-check: `tests/test_targeting_overlay_compat.py:326` branches on it and takes
the "marked" branch for a genuinely nullable `geo_countries`; it passes, but for the serialisation
reason rather than the nullability one it names.

## 2. `model_dump_as_received` DROPS AN ADMITTED NULL, WHICH IS THE DIGEST CONTRACT

**`src/adcp/types/base.py:884`.** `tests/test_wire_types.py::test_model_dump_as_received_keeps_an_admitted_null_and_the_wire_alias`,
**left red**.

```
TargetingOverlayInput.model_validate_json('{"signal_targeting_groups": null}')
  .model_dump_as_received()  ->  {}          # the document said null
```

`signal_targeting_groups` admits `null`: its published node is
`anyOf: [{"$ref": ...}, {"type": "null"}]` and the JSON route accepts one — the validation half is
absent, measured. The method sets `exclude_none=False` and the docstring explains why that is enough:
*"a property the schema refuses `null` on is left off by its own `NoExplicitNull` exclusion either
way"*. That reasoning assumed finding 1's split; the `exclude_if` is now on the nullable property
too, so nothing can carry the null.

**What it costs.** `core/canonical-proposal.json` binds `terms_digest` to the JCS form of
`commercial_terms` **as declared**, and this method exists (#1613, #1614) so a buyer recomputing it
gets the seller's bytes back. A `commercial_terms` carrying one explicit null now hashes to a
different digest than the document it came from. `tests/conformance/test_wire_round_trip.py` holds
every digest-covered schema to byte-for-byte RFC 8785 and has no allowlist.

**The repair** is for `model_dump_as_received` to re-add the nulls the document set, the way
`adcp._null_clear.preserve_explicit_nulls` does for a request — `model_fields_set` is where the
knowledge is, and it is intact (finding 4 measures that).

## 3. A STORE PATCH CANNOT CARRY A CLEAR, AND A SNAPSHOT CANNOT CARRY A DEFAULT

**`src/adcp/decisioning/handler.py:1189`, `_to_store_dict`.** Two tests in
`tests/test_rc3_media_buy_runtime.py`, **left red**:
`test_the_store_patch_shape_drops_unset_and_keeps_explicit_nulls` and
`test_a_platform_response_still_keeps_unset_fields`.

```
_to_store_dict(_update(frequency_cap=None, ...), patch=True)   ->  no 'frequency_cap' key
_to_store_dict(_update(paused=True))                           ->  no 'frequency_cap' key
```

The function's own docstring states both contracts and the reason each is written the way it is:

* `patch=True` — *"``exclude_none=False`` is not redundant … ``exclude_unset=True`` alone would
  still drop every explicit null and turn a clear back into 'leave unchanged'."* The merge contract
  below it reads `None` as "clear this field", so a dropped null is a **lost command**: the adopter
  store is told nothing where the buyer said "remove the cap".
* `patch=False` — *"a platform that relied on a model default must still see that default land in
  the store."* An unset optional defaults to `None` and is now omitted, so the snapshot is sparse
  where it promised to be whole.

Both follow from finding 1. Forcing the tests green would assert that a clear is silently dropped,
which is the failure mode the module's own docstring opens with: *"Both fail silently in the
schema-only version: the request succeeds, the mutation does not happen, and nothing says so."*

**The repair** is the same one finding 2 needs, applied at this boundary.

## 4. WHAT IS *NOT* BROKEN, AND IT NARROWS FINDINGS 2 AND 3

Measured end to end through a real MCP client and a typed server
(`tests/test_control_request_intent.py`, repaired and now green): **a clear survives the wire.**
`preserve_explicit_nulls` puts the `null` back on the request, the server parses it, and the server's
model carries the key in `model_fields_set` — at the request root and inside each package — with the
attribute `None`.

So the knowledge is not lost anywhere in transport. It is lost only at `model_dump`, which is the
one place findings 2 and 3 both call. That is what makes the repair local.

## 5. A UNION-ROOTED RESPONSE ADVERTISES NO UNION, AND THREE ADVERTISE NOTHING AT ALL

**The emitted base's `model_json_schema()`, surfaced through `src/adcp/server/mcp_tools.py`.**
`tests/test_tools_list_output_schema.py` — three tests **left red**, and the reason
`tests/test_discovery_payload_size.py::test_compact_output_schemas_still_reject_unknown_fields` and
`tests/test_mcp_schema_drift.py` had to be re-pointed.

§4 emits a `oneOf` of object types as a base plus one class per branch. The base's JSON schema is
built from the base's own fields, so the union is not in it:

```
create_media_buy outputSchema:  {"type":"object", "required":["status"],
                                 "properties":[the envelope's 12], "additionalProperties":true}
                                 # no anyOf, and no branch property at all
```

A buyer validating `structuredContent` against that cannot tell success from error from pending —
which is the test's own sentence — and `additionalProperties: true` means every branch field passes
unchecked.

**Worse where the document states no root properties.** `media-buy/control-media-buy-response.json`
is a bare `oneOf` over three branches with no root `properties`, so the base declares no fields and
the whole advertised schema is:

```json
{"description": "Result of applying operational controls …", "properties": {}, "type": "object"}
```

Measured: **3 of 78 advertised tools** publish that — `control_media_buy`, `buy_products`,
`accept_proposal`. 151, 160 and 174 bytes of "any object". `control_media_buy` was the
discriminating case for "compaction must not open a closed object", because its success branch was
both closed and pruned; there is now nothing closed in it to grade, and that test moved to
`list_products`.

**This is not a declared approximation.** `CreateMediaBuyResponse.__adcp_approximations__` holds one
entry, an `if` widening at `#/oneOf/0/allOf/0`, and says nothing about the union.

**The repair** is a `__get_pydantic_json_schema__` on the branch-dispatch base that renders
`_branch_models` — the list is already there and already in document order.

## 6. THE PRIMARY WEBHOOK BOUNDARY DOES NOT SANITIZE A NON-TERMINAL RESULT

**`src/adcp/client.py:6455` onward.** Three parameters of
`tests/test_legacy_only_creative_surfaces.py::test_primary_webhook_sanitizes_every_status_and_activity`
(`failed`, `working`, `input-required`), **left red**; the `completed` parameter passes.

The test hands the primary (non-legacy) boundary a result carrying `format_id` and asserts no legacy
identity survives — *"the primary boundary must sanitize even when task-specific parsing cannot
produce a canonical model"*. Measured, the sanitizing branches in `_handle_mcp_webhook` are all
under `if status == GeneratedTaskStatus.completed`, so for a non-terminal status the result is
handed through untouched and lands in `GetProductsAsyncWorking.__pydantic_extra__`:

```
status='working'  ->  data.__pydantic_extra__ == {'format_id': {...}, 'unexpected': True}
```

**The class is right.** `core/async-response-data.json#/anyOf/2` states `additionalProperties: true`,
so the branch admits undeclared keys and round-trips them — §2's `extra` row exactly. What changed is
that the test used to pass because the model **dropped** the key, not because anything sanitized it:
reading 8's trap, in the direction where a test passes for a reason it does not name.

**The repair** is a sanitizer on the non-terminal path, or an explicit decision that the primary
boundary only sanitizes a parsed result — in which case the test should say so.

## 7. `proposal_manager` VALIDATES A ONE-KEY `MediaBuy` THE DOCUMENT REFUSES

**`src/adcp/decisioning/proposal_manager.py:248`.** All four failures in
`tests/test_decisioning_negotiation.py`, **left red**.

```python
MediaBuy.model_validate({"proposal_refinement": raw_refinement})
# -> lifecycle_tools: required when proposal_refinement
```

`protocol/get-adcp-capabilities-response.json#/properties/media_buy/allOf/0` states it:

```json
{"if": {"required": ["proposal_refinement"]},
 "then": {"properties": {"lifecycle_tools": {"contains": {"const": "refine_proposals"}}},
          "required": ["lifecycle_tools"]}}
```

The conditional is the document's and §5 compiles it. What the code wants is to validate the
refinement SUB-OBJECT, and it does so by wrapping it in a bare `MediaBuy` — a parent the document
then judges as a whole. No fixture can fix this: the one-key dict is built inside the production
method from whatever the platform declared.

**The repair** is to validate against the sub-object's own type —
`MediaBuy.model_fields["proposal_refinement"].annotation` — which is the node the keyword
`supported_dimensions` / `max_alternatives` belongs to.

## 8. CANONICAL-FIRST PARSING NO LONGER REACHES THE LEGACY PROJECTION

**`src/adcp/client.py:2304`, `_canonicalize_get_products_result`.**
`tests/test_client.py::test_get_products_still_projects_legacy_format_ids`, **left red**. The test's
own docstring is the contract: *"Canonical-first parsing must retain the legacy compatibility
fallback."*

The method parses canonically first and returns early if that succeeds; the legacy projection runs
only on the fall-through. The discriminator was that a `format_ids`-only product failed canonical
parsing. It does not any more, and the reason is a decision this project took deliberately:
**`deprecated` is metadata, not absence** — `core/product.json` states `format_ids` as
deprecated-but-present, so the canonical `Product` carries it and the product parses.

Measured on a product carrying only `format_ids`:

```
result.success          True
products[0].format_ids  [FormatReferenceStructuredObject(agent_url=…, id='display_300x250_image')]
products[0].format_options  None        # project_legacy_product never ran
```

Nothing is wrong with the response — `core/product.json`'s own text says a product MUST carry
`format_ids`, `format_options`, **or both** during the 3.x migration window. What is wrong is that
the buyer asked a canonicalizing client and got no canonical declaration.

**The repair** is to make the test a FIELD test rather than a parse-failure test: project where
`format_options` is absent and `format_ids` is present, which is the condition
`src/adcp/canonical_formats/v1_to_v2.py` is written for.

## 9. TWO HAND-WRITTEN DECLARATIONS SHARE EIGHT PUBLIC WORDS

**`src/adcp/core.py` against the restored `src/adcp/types/registry.py`.** All six failures in
`tests/test_registry.py`, **left red**. This was measured in full by the previous lane and the
measurement still holds — see `FINDINGS-tail3.md` §"tests/test_registry.py", which carries the
field-set table and the two candidate repairs. Confirmed unchanged here:

```
adcp.types.core.ResolvedBrand  ->  adcp.core.ResolvedBrand          (hand-written)
adcp.ResolvedBrand             ->  adcp.core.ResolvedBrand
adcp.types.ResolvedBrand       ->  adcp.types.registry.ResolvedBrand   (a DIFFERENT class)
```

`adcp.registry.RegistryClient` imports from `adcp.types.core`, so the class the client builds is the
one the test imported, and `adcp.types.<Word>` hands an adopter the other one. That is the outcome
this task's own rule names as the worst available: *a public word that changes meaning while staying
importable*. The flat facade's stated rule is to DECLINE such a word (`_flat`'s
`__adcp_ambiguous__`); these eight are hand-written and never reach it.

Forcing the six green by importing from `adcp.types.registry` would bless the repoint and leave
`adcp.<Word>` disagreeing with it. **It is the owner's call which declaration is the SDK's.**

## 10. TWO COMPAT TABLES DISAGREE ABOUT THREE NUMBERED BUILD-CREATIVE SPELLINGS

**`src/adcp/types/legacy_names.py` against `src/adcp/types/_adapter.py` / `legacy.py` /
`_generated.py`.** No test is red for this — it was found while repairing
`tests/test_legacy_only_creative_surfaces.py` and `tests/test_response_str.py`, and both now name the
branch instead. Recording it so it is not re-found.

`media-buy/build-creative-response.json`'s own branch order is
`1 Success, 2 MultiSuccess, 3 VariantSuccess, 4 Estimate, 5 Error, 6 Submitted`, which is what
`BuildCreativeResponse._branch_models` carries. The two public spellings disagree:

| N | `adcp.types.BuildCreativeResponse<N>` | `adcp.types.LegacyBuildCreativeResponse<N>` | document |
| --- | --- | --- | --- |
| 1 | BuildCreativeSuccess | BuildCreativeSuccess | Success |
| **2** | **BuildCreativeError** | **BuildCreativeMultiSuccess** | MultiSuccess |
| **3** | **BuildCreativeMultiSuccess** | **BuildCreativeVariantSuccess** | VariantSuccess |
| 4 | BuildCreativeEstimate | BuildCreativeEstimate | Estimate |
| **5** | **BuildCreativeEstimate** | **BuildCreativeError** | Error |
| 6 | BuildCreativeResponseSubmitted | BuildCreativeResponseSubmitted | Submitted |

`BuildCreativeVariantSuccess` has no unprefixed numbered spelling at all and `BuildCreativeEstimate`
has two (4 and 5). The `Legacy` side follows the document; the unprefixed side comes from the
`BuildCreativeResponse<N> = …` block the emitter writes into
`src/adcp/types/_schemas/media_buy/build_creative_response.py`, which `legacy_names.py` re-exports
under the comment *"upstream published this spelling"*.

So one of two things is owed: either the emitted block is mis-numbered against its own
`_branch_models` and should be regenerated in document order, or it is faithful to upstream's wheel
and the two spellings genuinely name different things — in which case `Legacy<Word>N` must stop
being a synonym of `<Word>N`. Either way, **two importable words differing by a prefix must not
resolve to two different branches silently.** `adcp.types.domains.core.publisher_property_selector`
is the shape the rest of the tree uses: name the branch.

## 11. TWO SDK RESPONSE HELPERS BUILD A PAYLOAD WITHOUT `status`

**`src/adcp/server/responses.py:691` (`list_creatives_response`) and
`src/adcp/server/helpers.py:159` (`adcp_error`).** Two parameters of
`tests/test_discovery_payload_size.py::test_advertised_output_schemas_still_describe_real_responses`,
**left red**.

The test validates the reference seller's REAL handler output against the schema the SDK advertises
for the same tool. Both failures are one message:

```
list_creatives    -> 'status' is a required property
create_media_buy  -> 'status' is a required property
```

`status` is required by `core/protocol-envelope.json` one `allOf` up, the advertised schema carries
`required: ['status']` for every tool, and the five passing parameters all supply it. The two that
do not are the ones built by an SDK helper: `list_creatives_response` returns
`{creatives, pagination, query_summary, sandbox}` and `adcp_error` returns `{errors: [...]}`.
`examples/seller_agent.py` compensates by hand where it remembers to —
`control_media_buy` does `return {"status": "failed", **error}` — and `create_media_buy`'s error path
does not.

**The repair** is in the helpers, which is where every adopter meets it; `examples/` is where the
test reads it. Both are outside this lane.

## 12. TWO PARITY DIVERGENCES HAVE CLOSED AND THE FIXTURE STILL DECLARES THEM

**`tests/fixtures/validation-parity-cases.json` and
`tests/fixtures/validation-model-divergences.json`.**
`tests/test_validation_parity.py::test_validation_parity_fixtures_match_both_runtime_paths`,
**left red** — the fixtures are outside this lane's write scope.

The allowlist records three cases where Pydantic accepts what the canonical schema refuses, each with
the reason *"datamodel-code-generator does not emit the top-level wholesale-mode conditional"*. That
names the PREVIOUS generator. Measured over all 8 cases, two of the three have closed:

| case | declared | measured |
| --- | --- | --- |
| `get_signals.wholesale_forbids_selector` | pydantic True | **False** — *"forbidden when discovery_mode='wholesale'"* |
| `get_signals.pricing_requires_feed_version` | pydantic True | **False** |
| `get_signals.brief_requires_selector` | pydantic True | True — still diverges |

**The repair shrinks an allowlist**, which is the only direction it may move: set `pydantic_valid`
to `false` on those two cases, and delete their two entries from
`validation-model-divergences.json`. The third stays with its reason restated for this emitter.
`test_every_model_schema_divergence_is_explicitly_allowlisted` holds the two files equal, so both
edits land together.

## 13. `GENERATED_POC_SOURCE_SYMBOL_MAP` NAMES EIGHT WORDS THIS EMISSION DOES NOT BIND

**`src/adcp/migrate/v3_to_v4.py:407`.**
`tests/test_migrate_v3_to_v4.py::test_generated_poc_symbol_map_covers_publicly_exported_names`,
**left red**. It is the drift instrument and the drift is real.

The map's job is `("<private module>", "<v3 symbol>") -> "adcp.types.<public alias>"`, and the test
checks both ends resolve to one class. Measured, 23 entries, 8 broken:

| entry | what is missing |
| --- | --- |
| `core.account.GovernanceAgent` → `CoreGovernanceAgent` | the public alias |
| `core.vendor_pricing_option.VendorPricingOption{,1..5}` → `{VendorPricingOptionUnion, Cpm…, PercentOfMedia…, FlatFee…, PerUnit…, Custom…}` | the alias **and** the numbered source symbols |
| `creative.list_creatives_request.Sort` → `ListCreativesSort` | the public alias |
| `signals.get_signals_response.{Signal,Range}` → `{GetSignalsSignal, SignalCoverageRange}` | the source symbols |
| `core.property.Identifier` → `PropertyIdentifier` | the source symbol |
| `core.product_filters.Country` → `ProductFilterCountry` | both |

None of these is "a name that should be bound and is not". §4 names a branch from its own
declaration (`VendorPricingOptionCpm`) and a nested node from its declaring position
(`ListCreativesRequestSort`, `IdentifiersItem`, `SignalsItem`); the map holds the previous emission's
spellings on both sides. `_replacement_is_identical` sees it and degrades each to the plain module
rename, so **the codemod is correct and only the hints are poorer**.

**The repair** is to drop the eight entries or re-point them, which the test's own failure message
asks for. The fifteen live entries are exercised by the parametrized test here.

## 14. `brand` NO LONGER SPLITS, AND A WHOLE-STEM RENAME MIS-LANDS ONE NAME

**`src/adcp/migrate/v3_to_v4.py:163`, `_split_halves`.** No test is red for this — the four
split-stem tests were re-pointed or deleted — and it is worth one paragraph because the codemod will
write a broken import.

`_split_halves` asks the installed SDK for `adcp.types.domains.<stem>_discovery`. This emission ships
**no `_discovery` module at all**: `adcp.types._generated_poc_alias` and
`scripts/generate_types.py`'s `ROOT_DISCOVERY_SCHEMAS`, the two things that minted the suffix, are
both the previous generator's. So no stem splits and every stem renames whole.

That is right for `brand.json`'s own classes — `brand.json` compiles to the `__init__` of the
`adcp.types.domains.brand` PACKAGE, so `Brand`, `Asset`, `LocalizedName` and `Fonts` all resolve
there. It is wrong for a name the old aggregator carried from a SIBLING document:
`from adcp.types.generated_poc.brand import AcquireRightsRequest` is rewritten to
`from adcp.types.domains.brand import AcquireRightsRequest`, and that module does not bind it — it
is at `adcp.types.domains.brand.acquire_rights_request`, and publicly at `adcp.types.brand` and
`adcp.types`.

So the stem DID split in this emission, just not into two siblings: it split into a package root and
its submodules. The probe looking for a `_discovery` suffix cannot see that.

## 15. `tests/test_public_api.py` — LEFT REPORTING BY INSTRUCTION

One failure, unchanged from `FINDINGS-tail3.md`: `scripts/export_resolution.py:49` reads
`adcp.types.domains.DOMAINS`, and `adcp.types.domains` is a `sys.meta_path` mirror with no module
list by design. The task names this a known snapshot drift the owner has not decided to re-take, so
the snapshot was not regenerated and the test was not touched.

---

## What was repaired, by ground

| ground | files (failures) | total |
| --- | --- | --- |
| **a name, module or field type the PREVIOUS generator bound and this emission does not** | migrate_v3_to_v4 (13), legacy_only_creative_surfaces (3), canonical_formats_public_api (2), wire_types (1), import_memory (1), notification_outbox_artifacts (1), response_str (1), format_reference_wire_url (1), no_explicit_null (1) | 24 |
| **a fixture short a key, or a group, the document requires** | response_size_limit (4), rc3_media_buy_runtime (2), decisioning_idempotency_conflict (2), feed_version (2), update_rights_roundtrip (1), looks_like_v3 (1), decisioning_wire_dispatch (1), control_request_intent (1), idempotency_handoff (1) | 15 |
| **a test asserting against a DECISION already taken** | targeting_overlay_compat (6), discovery_payload_size (3), no_explicit_null (2), acceptance (1) | 12 |
| **the old FLAT class graph, where §4 emits a base plus one child per branch** | targeting_overlay_errors (4), discovery_payload_size (1), update_rights_roundtrip (1), decisioning_specialisms (1), mcp_schema_drift (1) | 8 |
| **a refusal or a rule re-pointed at the document's own keyword** | publisher_selector_xor_autoenforce (2), purchase_continuation (1) | 3 |

Sixty-two repaired, twenty-five left reporting, eighty-seven accounted for. Two tests were
DELETED and five parametrize entries with them, all in `test_migrate_v3_to_v4.py`, all naming a
`_discovery` module this emission does not ship or an alias it does not bind; the collected total
falls from 17,910 to 17,903 by exactly those seven.

Measured against `test-results/before.json` and `test-results/after.json`: **398 → 337 failed,
5 → 4 errors, 14,681 → 14,736 passed. Zero newly-failing node ids anywhere in the suite, and the
316 failures outside this lane's thirty-two files are unchanged.**
