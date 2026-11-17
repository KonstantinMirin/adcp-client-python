# The 126 SDK failures, grouped by cause

Source artifacts, both from `b74aa3f58`, neither re-run as a whole:

    sdk-run.log                   full `make test` output
    test-results/sdk/report.json  the same run's json report
    126 failed, 16071 passed, 2821 skipped, 10 deselected, 1 xfailed, 4 errors

**34 rows, summing to 126.** The 4 ERRORs are a 35th row, counted separately because they are
not among the 126 (the summary counts them apart).

## How to read the table

* **Classification.** A row states where the fix belongs: **EMISSION** (the generated types
  under `src/adcp/types/_schemas/` are wrong), **SDK** (hand-written code under `src/adcp/`,
  `scripts/` or `examples/` is wrong), **STALE TEST** (the test pins something deliberately
  changed). Four rows have witnesses in two layers from ONE cause; those cells give both with
  counts rather than splitting the cause across two rows.
* **Decisions checked first.** `CLAUDE.md`'s opening rule and `docs/plan/rebuild-plan.md` §2's
  decision index were read before anything here was called a defect. Three rows (R1, R4, R7)
  are decisions already taken, and are classified accordingly — R7's failures are the
  `None`-is-absence rule and are STALE TEST, not defects; R1's are an ACCEPTED decision the
  emitter has not implemented yet, which is an emission defect against the decision and not
  against the document.

## What I re-ran, and why

`make test` was not re-run. Eleven targeted re-runs, each because the artifact records an
outcome but not the cause:

| re-run | why |
|---|---|
| `test_reporting_production_lifecycle::…frozen_wire_cycle[False-False-memory]`, with `__post_init__` instrumented to print the jsonschema errors it discards | R2 — the artifact carries only `ValueError: offering must satisfy the complete public contract` |
| `test_reporting_reconciliation::test_official_revision_requires_finality_evidence`, with `refused_at` spied | R3 — `_reconcile.py:481` swallows the cause by design |
| `test_media_buy_context_echo::test_buy_without_context_echoes_only_package_contexts`, with `_call` spied | R6 — needed to see whether the preceding `create_media_buy` had been refused |
| `test_client::test_get_products_still_projects_legacy_format_ids` | R22 — to confirm it still fails at HEAD |
| `test_reporting_notification_packaging::test_installed_base_import_needs_no_pg_extra[wheel]`, then a hand build of the same wheel | the 4 ERRORs — the test redacts the child's stderr to a sha256 |
| 6 small in-process probes (`BuildCreativeMultiSuccess`, `LegacyFormatId`, `AdcpAgentsAuthorization`, the `adcp.types` facade, `CreativeRepresentation`/`SignalRef`, `CreateMediaBuyRequest`) | R4, R33, R34, R13/R14, R9, R6 |

No code and no test was changed. The instrumentation above was applied in a throwaway
interpreter, not written to the tree.

**One environment fact, recorded because it bit this lane and will bit the next.** The shared
venv's editable path file reads

    $ cat /srv/ws/adcp-client-python/.venv/lib/python3.12/site-packages/__editable__.adcp-9.6.1.pth
    /srv/ws/wt-wrappers/src
    …

so a bare subprocess resolves `adcp` to `/srv/ws/wt-wrappers/src` (commit `3c1c572c4`), **not**
to the trunk, while pytest itself imported `/srv/ws/adcp-client-python/src` — every traceback
in `report.json` names that path. Five of the 126 run their body in a subprocess (R5's
`test_importing_the_surface_builds_no_patched_model`, R30, R33 ×2, R34). **Each of those five
was re-run against the trunk explicitly and reproduces there**, so no row below rests on the
sibling worktree. R2's two `production_scope` entries show `/srv/ws/wt-wrappers/…` in their
traceback for the same reason and reproduce in-process as the other five of that row do.

---

## The table

| # | Cause, in the code's own terms | n | Where it lives | Evidence | Class |
|---|---|---|---|---|---|
| **R1** | **The accepted "a required property the document PINS to one value may default to it" decision is not implemented.** A `const`-pinned required field is emitted with no Python-side default, so a caller who omits the one value the document admits is refused. | **9** | `codegen/render.py` + the Python-side half owed beside `OmittedNotNull` in `src/adcp/types/_base.py`; witnesses at `src/adcp/types/_schemas/core/assets/image_asset.py:27` and `src/adcp/types/_schemas/core/reporting_delivery_capabilities.py:59-60` | emitted: `asset_type: Annotated[Literal['image'], Field(...)]` — required, no default; `configuration_task: Literal['sync_accounts']`; `status_task: Literal['get_reporting_status']`. Failure: `1 validation error for ImageAsset / asset_type / Field required [type=missing, input_value={'url': 'https://via.plac...th': 300, 'height': 250}]`. The decision index names this exact class: *"`ImageAsset(url=…, width=…, height=…)` supplies `asset_type="image"` itself, because `const` states it"*, and `verdicts/a-pinned-default-is-the-documents-own.md` lists `ImageAsset.asset_type` (7), `ReportingDeliveryCapabilities.status_task` (3) and `.configuration_task` (3) among its 82. | EMISSION |
| **R2** | **`core/reporting-delivery-offering.json`'s `allOf[1].then` conditionally requires `reporting_profile.canonicalization_contract_version` and `.canonicalization_media_type`; the emitted class lowers neither**, so the model admits a profile the document refuses and the SDK's own schema screen rejects it. | **7** | emission of `core/reporting-delivery-offering.json`; detected at `src/adcp/reporting/production/offerings.py:70` | artifact: `ValueError: offering must satisfy the complete public contract`. Instrumented re-run: `ERR: ['reporting_profile'] \| ['allOf', 1, 'then', 'properties', 'reporting_profile', 'required'] \| 'canonicalization_contract_version' is a required property` (and `…_media_type`); `RAWPROF: ['canonicalization_id', 'canonicalization_sha256', 'canonicalization_uri', 'grain', 'id', 'primary_keys', 'schema_dialect', 'schema_ref_policy', 'schema_sha256', 'schema_uri', 'version']`. Both missing properties are `const`, so **R1's fix closes this row too** — that is the cheapest proposal. | EMISSION (undeclared widening) |
| **R3** | **`if`/`then`/`not` conditional requirements are now lowered to `ConditionalRequired` rules and enforced at construction**, where the previous tree dropped them. Payloads the document always refused are refused for the first time, and the refusal text changed. | **12** | `src/adcp/types/_base.py` rules; e.g. `src/adcp/types/_schemas/core/reporting_delivery_capabilities.py:41-42` | `2 validation errors for ProvidersItem / countries / required when identity_match=True`; `GetSignalsRequest / signal_spec / forbidden when discovery_mode='wholesale'`; `ReportingDeliveryOffering / method.format / required when pattern='file_transfer'`. That the rules are RIGHT is pinned by `test_validation_parity`: its fixture `get_signals.wholesale_forbids_selector` asserts `pydantic_valid: True` for `{'discovery_mode': 'wholesale', 'signal_spec': 'sports fans'}` — the fixture's own id says the document forbids it. | **STALE TEST ×6** (fixtures/messages: `test_decisioning_async_discovery`, `test_decisioning_capabilities_submodule::test_preview_capability_models_construct_with_bundled_creative`, `test_nested…::test_provider_level_nesting_round_trips`, `test_reporting_reconciliation::test_official_revision_requires_finality_evidence`, `test_trusted_match_validation`, `test_validation_parity`) + **SDK ×6** (`src/adcp/decisioning/proposal_manager.py:248` builds a capabilities object declaring `proposal_refinement` without `lifecycle_tools`, ×4; `src/adcp/reporting/service.py:349` first-boot offerings, ×2) |
| **R4** | **The protocol-envelope conjunction is enforced: `status` (and `success`) is required on every response class.** Producers and expectations that omit it are refused. | **10** | `core/protocol-envelope.json` one `allOf` up, as `CLAUDE.md` states; witnesses in test fixtures and `examples/seller_agent.py` | `1 validation error for ListAccountsResponse / status / Field required`; `2 validation errors for ComplyTestControllerResponse / status … / success …`; `jsonschema.exceptions.ValidationError: 'status' is a required property`. `test_build_readback_preserves_empty_and_error_branch_rules` fails only on error ORDER — re-run: `missing ('status',)` precedes `too_short ('creative_manifests',)`, and the test reads `errors()[0]`. The requiredness is the document's: `CLAUDE.md` — *"`status` looks optional on a task response and is required by `core/protocol-envelope.json` one `allOf` up"*. | STALE TEST (the producers are `examples/seller_agent.py` and in-test handlers; none is `src/adcp/`) |
| **R5** | **The import-time patch layer is deleted, and with it `ReportingWebhook.operation_id` and `_ergonomic`'s order-preserving unique-items coercion.** `adcp.types._forward_compat` and `adcp.types._ergonomic` no longer exist. | **6** | `verdicts/the-dead-patch-layer.md`; consumer at `src/adcp/webhooks.py:378` | trunk probe: `ModuleNotFoundError: No module named 'adcp.types._forward_compat'`. `KeyError: 'operation_id'` from `ReportingWebhook.model_fields`; `AttributeError: 'ReportingWebhook' object has no attribute 'operation_id'` at `src/adcp/webhooks.py:378: if not webhook.operation_id:`. `_ergonomic` de-duplicated where the document's `uniqueItems` now refuses: `item 1 repeats an earlier one, and the document requires the items of 'disclosure_positions' to be distinct`. The verdict: *"the layer has been absent from every run we have graded"*. `canonical_creative` was the third patcher, so `SyncCreativesRequest.model_fields["creatives"] is GeneratedSyncCreativesRequest.model_fields["creatives"]` now holds. | **STALE TEST ×4** (`test_lazy_rebuild::test_ergonomic_patches_apply_on_first_use`, `::test_importing_the_surface_builds_no_patched_model`, `test_nested…::test_forward_compat_reporting_operation_id_is_left_off_when_unset`, `::test_canonical_redeclaration_inherits_the_exclusion`) + **SDK ×2** (`webhooks.py` reads a field the layer used to add) |
| **R6** | **The same deletion removed the legacy media-buy lifecycle-status widening.** `status: 'active'` / `'paused'` is refused by the typed response classes; `media_buy_status_helpers` is restored as DATA but applied nowhere on the model path. | **10** | `src/adcp/types/media_buy_status_helpers.py` (data only); only consumer is `src/adcp/server/mcp_tools.py:118`, the server tool path | `1 validation error for CreateMediaBuySuccess / status / Input should be 'submitted', 'working', 'input-required', 'completed', 'canceled', 'failed', 'rejected', 'auth-required' or 'unknown' [type=enum, input_value='active']`. The helper's own docstring states the contract that is now unmet: *"The sync create/update media-buy response arms accept legacy constructor and handler payloads where `status` carried lifecycle state."* `src/adcp/types/_restored.py:13-16` records that `_ergonomic` and `_forward_compat` "stay deleted". Instrumented re-run of `test_buy_without_context_echoes_only_package_contexts` shows the KeyError is downstream: `CREATE: {"adcp_error": …"(field: 'status')"…}` then `READ: …"packages":[{"package_id":"mb_1_pkg_0",…}]` with no `context` — the create was refused, so no package context was ever recorded. | SDK (the SDK's own seller/dispatch path emits the legacy value and nothing normalizes it) |
| **R7** | **The dump omits an optional property whose value is `None`, whatever its type admits.** The emitter now writes `OmittedNotNull` (`exclude_if=_is_absent`) on every optional field; the old nullable-keeps-null split is gone. | **7** | `src/adcp/types/_base.py:486,616`; the old spelling at `src/adcp/types/base.py:674` | `KeyError: 'budget_cap_timezone'` on `request.model_dump(exclude_none=False)`; `assert <function _is_absent …> is <function _is_none …>`; `AssertionError: ('A2UIComponent', 'parentId')` where the test asserts `field.exclude_if is None` for an unmarked field. **This is decision 2 of the index**: *"a required property keeps its `null` on the wire … an optional one is omitted whatever its type admits"*. `base.py:720-746` already names the two spellings as one marker. | STALE TEST — **but see proposal:** `_to_store_dict`'s "an explicit clear is a command" path (`test_rc3_media_buy_runtime`) now has no way to express a clear, and `src/adcp/_null_clear.py::preserve_explicit_nulls` (schema + `model_fields_set`, not `exclude_if`) is the mechanism that already solves it on the wire path |
| **R8** | **A `$ref`ed scalar and a property-less opaque object mint no class**, so `.root` and model attribute access are gone. | **3** | `src/adcp/types/_schemas/core/principal_state.py:27`; `src/adcp/types/_schemas/core/context.py:12` | emitted: `destination_refs: Annotated[list[StrMinLen1MaxLen255], …]`; `ContextObject = Annotated[dict[str, Any], Field(...)]`. Failures: `AttributeError: 'str' object has no attribute 'root'` ×2 and `AttributeError: 'dict' object has no attribute 'correlation_id'`. `rebuild-plan.md` §4: *"a scalar at a root → a module-level annotated alias, not a class"*. | STALE TEST |
| **R9** | **A union at a reference position is a BASE CLASS with branch subclasses, not an `Annotated[A \| B \| C]` alias.** | **2** | `rebuild-plan.md` §5 `oneOf, anyOf`: *"Shapes at ROOT → the base plus one class per branch"* | probe: `SignalRef <class 'adcp.types._schemas.core.signal_ref.SignalRef'> <class 'adcp.types._base._Dispatching'>`, `get_args ()`. Failures: `ValueError: not enough values to unpack (expected 2, got 0)` from `arms, metadata = get_args(SignalRef)` and `KeyError: 'format_kind'` from `CreativeRepresentation.model_fields` (fields are now `['representation_id', 'source']` — the branch carries `format_kind`). | STALE TEST |
| **R10** | **A `model_construct`ed union BASE instance is refused at a field annotated with that base**, because the base's core schema is the union over its branch subclasses and the unvalidated base is a member of none. | **1** | `BranchDispatchMixin.__get_pydantic_core_schema__`, `src/adcp/types/_base.py` | `creative_manifest / Input should be a valid dictionary or instance of NamedFormatManifest [type=model_type, input_value=CreativeManifest(format_i…), input_type=CreativeManifest]`. The field IS annotated with the parent (`preview_creative_request.py:49`: `creative_manifest: Annotated[CreativeManifest \| None, …]`), so the annotation is right; the test builds its value with `CreativeManifest.model_construct(format_id=format_id, assets={})` (`tests/test_simple_api.py:225`), bypassing dispatch. | STALE TEST |
| **R11** | **`core/async-response-data.json`'s untagged `anyOf` is lowered to an undiscriminated union, and its `#/anyOf/2` branch `GetProductsAsyncWorking` requires nothing and allows extras — so it matches every object and shadows every later branch.** | **11** | `src/adcp/types/_schemas/core/async_response_data.py:87` | `assert False + where False = isinstance(GetProductsAsyncWorking(percentage=None, …, status='completed', response_type='variant', variant_id='variant-1', previews=[…]), <class '…PreviewCreativeVariantResponse'>)`. Every one of the 11 shows the same swallow, including the three webhook-sanitising cases: `data=GetProductsAsyncWorking(…, format_id={'agent_url': 'https://legacy.example', 'id': 'display'}, unexpected=True)`. The class declares `model_config = ConfigDict(extra='allow')` and inherits only optional fields from `GetProductsWorking`. | EMISSION |
| **R12** | **A root `oneOf`/`anyOf` response emits a BASE class whose `model_json_schema()` is one plain object, so the advertised MCP `outputSchema` no longer publishes the branches.** | **4** | §4's base-plus-branches lowering, rendered through `src/adcp/server/mcp_tools.py` | `KeyError: 'anyOf'` from `schema["anyOf"][0]` ×2; `AssertionError: create_media_buy outputSchema lost its discriminated union — MCP clients can't tell success from error from pending without it`; the schema now reads `{'additionalProperties': True, 'description': …, 'required': ['status'], …}`. The repo already records the same observation in prose: `tests/test_discovery_payload_size.py` — *"the emitted base declares no fields and `model_json_schema()` renders `{"type": "object", "properties": {}}` — no `oneOf` … Recorded in FINDINGS-rest.md; three tools advertise that schema."* | EMISSION |
| **R13** | **Six words name two different subjects, and the flat `adcp.types` facade binds the OpenAPI-derived `registry` one while `adcp.types.core` publishes the other.** | **6** | `src/adcp/types/registry.py:1204,1251,1290,1304,1756,1778` vs `adcp.core` re-exported through `adcp.types.core` | probe: `flat is core: False \| flat is registry: True`; `core module: adcp.core \| registry module: adcp.types.registry`. The six failing words are exactly the six `registry.py` also defines (`Policy`, `PolicySummary`, `PolicyHistory`, `PolicyRevision`, `ResolvedBrand`, `ResolvedProperty`); `PolicyExemplar`, which `registry.py` does not define, passes. `rebuild-plan.md` §1 forbids the inverse ("one import path per class") and says nothing yet about one word over two subjects — **this one may be a decision nobody has taken, and is a question for the owner before it is a fix.** | SDK |
| **R14** | **The rebuilt facade does not reproduce the `__all__`/`__dir__` advertisement contract**: a bound name need not be in `__all__`, the six partial modules are not named in `adcp.types.__all__`, and they define no `__dir__`. | **3** | `src/adcp/types/__init__.py` and the partial modules | probe: `VerifyBrandClaimsPayload hasattr True in __all__ False`; `modules in __all__: []`; `mb has __dir__? False`, `extra dir: ['__all__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__']` — the "9 more items" the diff reports. | SDK |
| **R15** | **Three words the old surface bound are bound nowhere now.** | **3** | `src/adcp/types/legacy.py`, `src/adcp/types/v32.py`, the alias layer | `ImportError: cannot import name 'LegacyFormat' from 'adcp.types.legacy'`; `ImportError: cannot import name 'ListCreativesRequest' from 'adcp.types.v32'`; `AssertionError: source-scoped migration target 'adcp.types.CoreGovernanceAgent' is not public` (probe: `CoreGovernanceAgent hasattr False`). `LegacyFormat` is not optional — `CLAUDE.md` makes it the only name for the v1 definition and requires that the rename BREAK rather than redirect, which it does; the binding is still owed. | SDK |
| **R16** | **The recorded surface censuses were derived against the pre-rebuild tree and not re-derived.** They cite `adcp.types.domains.*` and `adcp.types.canonical_creative`, which no longer import. | **4** | `src/adcp/types/_adapter.py` (generated by `survey/adapter_surface.py`); `tests/fixtures/public_api_snapshot.json` | `cites adcp.types.canonical_creative.Format / and adcp.types.canonical_creative does not import: ModuleNotFoundError`; `DOCUMENT-NO-WORD-NO-IDENTITY: upstream declares it at adcp.types.domains.account.sync_accounts_response.CreditLimit`; `Extra items in the left set: 'adcp.types.domains.brand_discovery' / 'adcp.types.domains.manifest' / 'adcp.types.domains.manifest_schema'`. The tests say the fix themselves: *"`_adapter.py` is generated by survey/adapter_surface.py, so neither group is fixed by editing it"* and *"Re-derive the census against the tree as it is."* | **SDK ×3** (`_adapter.py`) + **STALE TEST ×1** (the snapshot fixture, regenerated with `python scripts/regenerate_public_api_snapshot.py`) |
| **R17** | **A capability sub-object's class name is now §4's collision-resolved long name**, because the short candidate is taken by another document. | **2** | §4's branch/class naming, resolved by first fit | `assert 'GetAdCPCapab...sponseAccount' == 'Account'`; `assert 'MediaBuyContentStandards' == 'ContentStandards'`. The test's own comment pins the old generator spelling (*"codegen `Features2`"*), which §4 replaced. | STALE TEST |
| **R18** | **`create-media-buy-request.json`'s root `anyOf` is lowered to BRANCH CLASSES, not to a `RequiredGroups` rule**, so both the refusal message and the per-branch accepted set changed. | **2** | emission of `media-buy/create-media-buy-request.json` | expected `'at least one of these field groups'`, actual `packages / #/anyOf/0 (ExplicitPackagesWithFixedAllocation): Field required … proposal_id / #/anyOf/2 (CommittedProposalExecution): Field required …`. The second failure is a fixture that satisfies no group: `proposal_id / #/anyOf/0 (ExplicitPackagesWithFixedAllocation): 'proposal_id' are present together, which the document forbids`. | STALE TEST |
| **R19** | **`RequiredGroups`' refusal wording changed.** The mechanism fires; the words differ. | **1** | `RequiredGroups` in `src/adcp/types/_base.py` | expected `'at least one of these field groups'`, actual `none of these groups is present, the document requires at least one: 'creatives'; 'assignments'; 'assignment_operations'`. | STALE TEST |
| **R20** | **The postal country/system cross-field refusal now comes from the emitted `anyOf` branch union, not from a hand-written validator**, so the message changed. The refusal itself still happens. | **4** | emission of the postal-area union | expected `"postal system .* is not valid for country"`, actual `country / #/anyOf/0/allOf/0 (PostalAreaGB): Input should be 'GB' … system / #/anyOf/1 (PostalAreaWithFusedSystem): Input should be 'us_zip', … / and 6 more of this union's 10 branches refused`. | STALE TEST |
| **R21** | **`v1_format_ref` survives the canonical response projection**, and `media-buy/list-products-response.json` forbids it on a compact format option. | **2** | `src/adcp/canonical_formats/` projection; the value is set by `examples/seller_agent.py:271,302` | `AssertionError: assert 'v1_format_ref' not in {'format_option_id': 'example_billboard_970x250', 'display_name': 'Example.com Homepage — Billboard', …}`; and against the 3.2.1 validator, `<ValidationError: "Additional properties are not allowed ('v1_format_ref' was unexpected)">`. The field is legitimately STATED on the canonical declaration (`CLAUDE.md`: it is how v2→v1 is possible at all) — what is missing is the projection stripping it where the projection's own document forbids it. | SDK |
| **R22** | **`_canonicalize_get_products_result` decides "this response is canonical" by whether `GetProductsResponse` parses. Now that the canonical model states the deprecated `format_ids`, a legacy-only response parses canonically and the v1→v2 projection never runs.** | **1** | `src/adcp/client.py:2315-2326` | `TypeError: 'NoneType' object is not subscriptable` at `result.data.products[0].format_options[0]`. The early return is `if canonical_result.success and canonical_result.data is not None: … return canonical_result` — reached before `project_legacy_product`. The field's presence is the decision: `CLAUDE.md` — *"`deprecated` is metadata, not absence"*, with `core/product.json` among the seven documents that state it. The fork needs a positive test for canonical evidence, not a parse. | SDK |
| **R23** | **Two undeclared divergences between the bundled schema and the model.** | **2** | emission of `trusted_match/context-match-request.json` `#/properties/property_rid` and of `control-media-buy-request.json` `#/packages/items/budget` | `5 document(s) graded differently by the bundled schema and ContextMatchRequest … keyword='format', message="value does not match required format ('uuid')", direction='the model accepts a document the bundled schema refuses'` — a WIDENING with no `Approximation`; and `control_media_buy/packages/0/budget = None: the bundled schema accepts a document the model refuses (anyOf)` — a NARROWING with no declaration. Per `CLAUDE.md`, **the defect here is the missing DECLARATION, not the decision** — unless the `format: uuid` is meant to ride as `json_schema_extra`, which §5's `format` row says it should. | EMISSION (undeclared approximations) |
| **R24** | **Three declared divergences no longer occur, and the declaration set is shrink-only.** | **1** | `tests/conformance/_schema_parity.py` `DECLARED` | `declared divergences that no longer occur: ['canonical_model_refuses_legacy_creative_identity', 'format_kind_is_an_open_vocabulary_by_decision', 'model_requires_a_field_the_schema_does_not']. Delete each from tests/conformance/_schema_parity.py DECLARED.` | STALE TEST (delete the three rows) |
| **R25** | **A union branch's validator appears in the error `loc` as an unnamed `function-wrap[<lambda>()]` frame**, so `narrow_union_errors` cannot localize to the matched variant. | **1** | the branch wrapper installed by `src/adcp/types/_base.py` | `errors should localize to the matched 'image' asset variant; got: [('assets', 'hero', 'function-wrap[<lambda>()]', 'image', 'width'), ('assets', 'hero', 'function-wrap[<lambda>()]', 'image', 'height'), ('assets', 'hero', 'list[function-wrap[<lambda>()]]')]` — the third entry carries no variant at all. | EMISSION |
| **R26** | **`params` on a canonical format declaration is now a model, and `preview_cache` treats it as a dict.** | **1** | `src/adcp/utils/preview_cache.py:540` | `width = int(getattr(fmt, "params", {}).get("width", 300))` → `AttributeError: 'CanonicalFormatImage' object has no attribute 'get'`. `format_kind` + `params` with a 16-branch `oneOf` is the v2 canonical declaration `CLAUDE.md` describes; a class at `params` is the correct emission. | SDK |
| **R27** | **`SyncReportingReceiptsRequest.receipts` requires the narrower `ReceiptsItem`; `_reconcile.py` hands it the base `ReportingReceipt`.** | **2** | `src/adcp/reporting/_reconcile.py:1982` | `receipts.0 / Input should be a valid dictionary or instance of ReceiptsItem [type=model_type, input_value=ReportingReceipt(…), input_type=ReportingReceipt]`. `ReceiptsItem(ReportingReceipt)` is a real narrowing the document states — `extra='forbid'` plus `ForbiddenGroups((('received_at',),))` at `#/properties/receipts/items` — so the subclass is right and the caller is wrong. Proposal: build `ReceiptsItem`, or pass dicts. | SDK |
| **R28** | **Creative-dialect resolution runs inside `_prepare_creative_params` and fails closed on a creative-free `update_media_buy` before the version preflight can report `UNSUPPORTED_FEATURE`.** | **2** | `src/adcp/canonical_formats/dialect.py:137`, reached from `src/adcp/client.py:2294` | `CreativeDialectError: AdCP 3.1 does not establish a creative dialect: advertise media_buy.features.canonical_creatives or provide unambiguous request-local schema evidence`. The evidence reading is deliberate — `_schema_evidence`'s docstring: *"a payload stating neither is ABSENT evidence and fails closed"*, after the `__adcp_canonical_creative_model__` class marker was deleted. What is wrong is the SCOPE: an `update_media_buy` carrying only `account`/`media_buy_id`/`idempotency_key`/`frequency_cap=None` states nothing creative and should never have been asked. The test expects `adcp_error["code"] == "UNSUPPORTED_FEATURE"` with `pointer == "/frequency_cap"`. | SDK |
| **R29** | **`scripts/ci/run_native_tests.py` names a test file that no longer exists.** | **1** | `scripts/ci/run_native_tests.py:29` | probe over `COMPATIBILITY_TESTS`: 17 `OK`, one `MISSING tests/test_type_guards.py`. The test asserts `all(Path(path.split("::", 1)[0]).is_file() for path in native.COMPATIBILITY_TESTS)`. Proposal: drop the entry, or restore the file. | SDK (repo script) |
| **R30** | **The lazy facade no longer routes a first type access through `adcp.types._generated`.** | **1** | `src/adcp/types/__init__.py` | trunk probe (`PYTHONPATH=src`): `from adcp import Product` leaves `'adcp.types._generated' in sys.modules` False. The `_eager.py` layer `CLAUDE.md` describes is gone; `_generated.py` still exists but is not the path a symbol takes. The test asserts `out == "True"`. | STALE TEST |
| **R31** | **Two independently-versioned third-party httpcore distributions annotate `socket_options` differently**, and the test asserts their signatures are equal. | **1** | `tests/conformance/signing/test_ip_pinned_transport.py:99`; the packages are `httpcore` and `httpcore2` | `assert <Signature (…, socket_options: 'Iterable[SOCKET_OPTION]' …)> == <Signature (…, socket_options: 'typing.Iterable[SOCKET_OPTION]' …)>` — `collections.abc.Iterable` against `typing.Iterable`, same type, different spelling. Nothing in this row touches the rebuild. | STALE TEST (compare resolved annotations, not their source spelling) |
| **R32** | **A nested array-item class carries no version envelope**, and the document gives it none. | **1** | `src/adcp/types/_schemas/media_buy/build_creative_response.py:243` | `class CreativesItem(AdCPBaseModel):` at `#/oneOf/2/properties/creatives/items`, whose fields are `build_creative_id, catalog_item_ref, signal_condition, variants, errors` — no `adcp_version`. The test asserts `isinstance(node, AdcpVersionEnvelope)` for a creative and a variant. | STALE TEST |
| **R33** | **A `format: uri` field holds a URL OBJECT, so `== '<the string>'` is False.** | **2** | `src/adcp/types/_wire.py` `WireAnyUrl`, per the index's two-URL-types decision | trunk probe: `WireAnyUrl('https://creative.example')`, `eq str: False`, `str(): https://creative.example`, MRO `(WireAnyUrl, pydantic.networks.AnyUrl, _BaseUrl, object)`. The failing line is the program's line 78: `assert LegacyFormatId(agent_url='https://creative.example', id='display').agent_url == 'https://creative.example'`. The index: *"every other `format: uri` node is `AnyUrl` with a host required"*. **Side observation, not this row's failure:** the same decision says both URL types *"give an empty path a `/`"*, and this value has no trailing `/` — worth a separate check. | STALE TEST (compare `str(...)`) |
| **R34** | **A deferred generated RootModel dumped BY INFERENCE through a plain pydantic parent serialises as `{}` instead of its root value.** | **1** | the `_DeferredValSer` placeholder in `src/adcp/types/_base.py` | trunk probe: `Parent(item=AdcpAgentsAuthorization.model_construct(root=None)).model_dump(mode='json')` → `{'item': {}}`; the test asserts `{"item": None}`. `CLAUDE.md` describes exactly this path: the placeholders *"build on instance attribute access, which is how pydantic-core reaches a serializer when it dumps by inference (`Any` field, `serialize_as_any`)"* — for a root model it does not. | SDK (generated runtime base) |
| | **TOTAL** | **126** | | | |

---

## The 4 ERRORs — counted separately

All four are `tests/conformance/reporting/test_reporting_notification_packaging.py`, erroring in
the module-scoped `installed_distribution` / `built_distribution` fixtures:

    test_installed_base_import_needs_no_pg_extra[wheel]
    test_installed_base_import_needs_no_pg_extra[sdist]
    test_installed_pg_extra_migrates_commits_and_restarts[wheel]
    test_installed_pg_extra_migrates_commits_and_restarts[sdist]

**Cause: `built_distribution` copies the source tree through a filter that excludes any path
component named `_schemas`, and the rebuild moved the emitted tree from `src/adcp/types/domains/`
to `src/adcp/types/_schemas/`.** The wheel it builds therefore contains none of the 1,094
generated modules, and importing it fails.

The filter, at `tests/conformance/reporting/test_reporting_notification_packaging.py`:

```python
sources.extend(
    p
    for p in (ROOT / "src").rglob("*")
    if p.is_file()
    and not any(
        part in {"__pycache__", "_schemas"} or part.endswith(".egg-info") for part in p.parts
    )
)
```

It was written for `src/adcp/_schemas`, the gitignored bundled schema cache that `MANIFEST.in`
also prunes (*"A clean VCS source tree has no ignored `src/adcp/_schemas` directory"*).
`src/adcp/types/_schemas` is tracked — `git ls-files src/adcp/types/_schemas` returns 2,153
files — and `pyproject.toml` ships it deliberately (`"types/_schemas/**/*.json"`, whose comment
records the move *"from `types/domains/` to `types/_schemas/`"*).

Evidence, both halves:

* re-running `test_installed_base_import_needs_no_pg_extra[wheel]` reproduces the artifact's
  error verbatim — `notification distribution base-import-without-pg: exit 1 … stderr={"lines":33,…,"trace":[[33,["module_missing"]]],"classification":"recognized"}`;
* building the **same wheel from the unfiltered tree** (`python -m build --wheel`), installing it
  plus `adcp_reporting_storage` into a clean venv, and running the fixture's own `base_check`
  program prints `base-import-without-pg-ok`.

Classification: **STALE TEST** — the fixture's exclusion filter predates the move. Proposal:
narrow it to the one directory it meant, e.g. `p.relative_to(ROOT) != Path("src/adcp/_schemas")`
as a prefix test rather than a component-name test.

---

## Rows that are decisions, not defects — stated once more so they are not re-filed

* **R7** is the `None`-is-absence rule, index row 1 and 2. 1,021 pairs were once filed as defects
  for it. The failures are tests pinning the superseded nullable-keeps-null split.
* **R4** is the protocol-envelope conjunction, which `CLAUDE.md` calls the rule that "costs most
  often, and has cost twice". The producers that omit `status` are examples and fixtures.
* **R1** is an ACCEPTED decision (`verdicts/a-pinned-default-is-the-documents-own.md`) that the
  emitter has not implemented. It is filed as an emission defect against the decision, not
  against the document: the accepted set over DOCUMENTS does not move either way.
* **R13** may be a decision nobody has taken — one word, two subjects, no rule in `rebuild-plan.md`
  §1 or §4 that settles which the flat surface should bind. Ask the owner before fixing it.

## Where the 126 are concentrated

| cause | n |
|---|---|
| R3 conditional requirements now enforced | 12 |
| R11 async-response union swallowed by its permissive branch | 11 |
| R4 envelope conjunction (`status` required) | 10 |
| R6 legacy media-buy status no longer widened | 10 |
| R1 pinned `const` default not supplied | 9 |
| R2 offering `allOf[1].then` not lowered | 7 |
| R7 `None` is absence on the dump | 7 |
| R13 registry/core word collision | 6 |
| R5 dead patch layer | 6 |
| the other 25 rows | 48 |

By classification: **EMISSION 34**, **SDK 43**, **STALE TEST 49** (34 + 43 + 49 = 126).

| class | rows | n |
|---|---|---|
| EMISSION | R1 9, R2 7, R11 11, R12 4, R23 2, R25 1 | 34 |
| SDK | R3 6, R5 2, R6 10, R13 6, R14 3, R15 3, R16 3, R21 2, R22 1, R26 1, R27 2, R28 2, R29 1, R34 1 | 43 |
| STALE TEST | R3 6, R4 10, R5 4, R7 7, R8 3, R9 2, R10 1, R16 1, R17 2, R18 2, R19 1, R20 4, R24 1, R30 1, R31 1, R32 1, R33 2 | 49 |

---

## Appendix — every test id, by row

### R1 — pinned `const` required property gets no default (9)
- `tests/conformance/reporting/test_reporting_status_capabilities.py::test_adopter_subclasses_and_nested_wire_models_keep_the_explicit_field_allowlist`
- `tests/conformance/reporting/test_reporting_status_capabilities.py::test_raw_generated_capability_dumps_omit_unset_task_notification_and_false_flags[core]`
- `tests/conformance/reporting/test_reporting_status_capabilities.py::test_raw_generated_capability_dumps_omit_unset_task_notification_and_false_flags[managed]`
- `tests/conformance/reporting/test_reporting_status_capabilities.py::test_raw_generated_capability_dumps_omit_unset_task_notification_and_false_flags[reconciled]`
- `tests/test_preview_html.py::test_create_sample_asset`
- `tests/test_preview_html.py::test_create_sample_manifest_for_format`
- `tests/test_preview_html.py::test_create_sample_manifest_for_format_with_new_assets_field`
- `tests/test_preview_html.py::test_create_sample_manifest_uses_assets_field`
- `tests/test_preview_html.py::test_list_creative_formats_with_preview_urls`

### R2 — `reporting-delivery-offering` `allOf[1].then` not lowered (7)
- `tests/conformance/reporting/test_reporting_production_lifecycle.py::test_production_official_receipts_adjustment_and_frozen_wire_cycle[False-False-memory]`
- `tests/conformance/reporting/test_reporting_production_lifecycle.py::test_production_official_receipts_adjustment_and_frozen_wire_cycle[False-True-memory]`
- `tests/conformance/reporting/test_reporting_production_lifecycle.py::test_production_official_receipts_adjustment_and_frozen_wire_cycle[True-False-memory]`
- `tests/conformance/reporting/test_reporting_production_lifecycle.py::test_production_official_receipts_adjustment_and_frozen_wire_cycle[True-True-memory]`
- `tests/conformance/reporting/test_reporting_production_scope.py::test_typed_exact_revision_pages_after_actual_publication[0-memory]`
- `tests/conformance/reporting/test_reporting_production_scope.py::test_typed_exact_revision_pages_after_actual_publication[503-memory]`
- `tests/conformance/reporting/test_reporting_projection_rc6.py::test_admitted_producer_verified_artifact_and_receipt_keep_the_future_summary[True-3.2-memory]`

### R3 — conditional requirements now enforced (12)
STALE TEST:
- `tests/test_decisioning_async_discovery.py::test_get_signals_wholesale_handoff_rejected_leaves_no_registry_row`
- `tests/test_decisioning_capabilities_submodule.py::test_preview_capability_models_construct_with_bundled_creative`
- `tests/test_nested_no_explicit_null_round_trip.py::test_provider_level_nesting_round_trips`
- `tests/test_reporting_reconciliation.py::test_official_revision_requires_finality_evidence`
- `tests/test_trusted_match_validation.py::test_provider_registration_requires_identity_dimensions_when_identity_match_enabled`
- `tests/test_validation_parity.py::test_validation_parity_fixtures_match_both_runtime_paths`

SDK:
- `tests/test_decisioning_negotiation.py::test_authenticated_capability_discovery_projects_tenant_manager_refinement`
- `tests/test_decisioning_negotiation.py::test_capability_discovery_projects_manager_refinement`
- `tests/test_decisioning_negotiation.py::test_platform_router_rejects_declared_refinement_without_callback`
- `tests/test_decisioning_negotiation.py::test_platform_router_routes_compact_refinement_to_proposal_manager`
- `tests/test_reliable_reporting_service.py::test_first_boot_offerings_require_their_installed_tier[managed]`
- `tests/test_reliable_reporting_service.py::test_first_boot_offerings_require_their_installed_tier[reconciled]`

### R4 — envelope conjunction, `status` required (10)
- `tests/test_account_v3_wire.py::test_handler_list_accounts_returns_ads_and_publisher_identity_grants`
- `tests/test_account_v3_wire.py::test_list_accounts_projects_multiple_tiktok_authorization_grants`
- `tests/test_account_v3_wire.py::test_sync_creatives_authorization_required_can_name_publisher_identity`
- `tests/test_codegen_contract_compatibility.py::test_public_response_bases_remain_constructible_and_arms_remain_specific`
- `tests/test_discovery_payload_size.py::test_advertised_output_schemas_still_describe_real_responses[create_media_buy-params5]`
- `tests/test_discovery_payload_size.py::test_advertised_output_schemas_still_describe_real_responses[list_creatives-params4]`
- `tests/test_manifest_response_readback.py::test_build_readback_preserves_empty_and_error_branch_rules`
- `tests/test_negotiated_catalog_purchase.py::test_completed_payload_does_not_invent_newer_response_defaults`
- `tests/test_observability.py::test_client_task_creates_one_bounded_span`
- `tests/test_observability.py::test_nested_execute_task_does_not_duplicate_spans`

### R5 — the dead patch layer (6)
STALE TEST:
- `tests/test_lazy_rebuild.py::test_ergonomic_patches_apply_on_first_use`
- `tests/test_lazy_rebuild.py::test_importing_the_surface_builds_no_patched_model`
- `tests/test_nested_no_explicit_null_round_trip.py::test_canonical_redeclaration_inherits_the_exclusion`
- `tests/test_nested_no_explicit_null_round_trip.py::test_forward_compat_reporting_operation_id_is_left_off_when_unset`

SDK:
- `tests/test_reporting_webhook_operation_id.py::test_scheduled_sends_skip_and_flag_registrations_without_operation_id`
- `tests/test_reporting_webhook_operation_id.py::test_typed_registration_without_operation_id_is_refused`

### R6 — legacy media-buy lifecycle status no longer widened (10)
- `tests/test_decisioning_handler.py::test_update_media_buy_arg_projects_media_buy_id_and_patch`
- `tests/test_media_buy_context_echo.py::test_buy_without_context_echoes_only_package_contexts[memory]`
- `tests/test_media_buy_context_echo.py::test_get_media_buys_echoes_create_context[memory-a2a]`
- `tests/test_media_buy_context_echo.py::test_get_media_buys_echoes_create_context[memory-mcp]`
- `tests/test_media_buy_store_integration.py::test_create_media_buy_noop_path_when_seller_lacks_specialism`
- `tests/test_media_buy_store_integration.py::test_create_media_buy_persists_overlay_through_handler`
- `tests/test_media_buy_store_integration.py::test_persist_then_backfill_round_trip`
- `tests/test_media_buy_store_integration.py::test_update_media_buy_merges_overlay_through_handler`
- `tests/test_server_dx.py::TestMediaBuyResponse::test_typed_success_normalizes_legacy_status`
- `tests/test_server_dx.py::TestUpdateMediaBuyResponse::test_typed_success_normalizes_legacy_status`

### R7 — `None` is absence on the dump (7)
- `tests/test_nested_no_explicit_null_round_trip.py::test_every_marked_field_in_the_generated_tree_carries_the_exclusion`
- `tests/test_nested_no_explicit_null_round_trip.py::test_exclude_none_false_on_a_direct_dump_keeps_only_schema_admitted_nulls`
- `tests/test_nested_no_explicit_null_round_trip.py::test_marker_carries_the_exclusion_and_the_refusal`
- `tests/test_nested_no_explicit_null_round_trip.py::test_nullable_fields_still_emit_null_from_a_plain_parent`
- `tests/test_rc3_media_buy_runtime.py::test_a_platform_response_still_keeps_unset_fields`
- `tests/test_rc3_media_buy_runtime.py::test_the_store_patch_shape_drops_unset_and_keeps_explicit_nulls`
- `tests/test_wire_types.py::test_model_dump_as_received_keeps_an_admitted_null_and_the_wire_alias`

### R8 — a `$ref`ed scalar / opaque object mints no class (3)
- `tests/test_server_principal.py::test_seller_declaration_change_emits_without_version_churn`
- `tests/test_server_principal.py::test_suspension_preserves_generation_and_revocation_retires_it`
- `tests/test_server_principal.py::test_sync_persists_state_negotiation_and_exact_replay`

### R9 — a union is a base class, not an `Annotated` alias (2)
- `tests/test_codegen_contract_compatibility.py::test_creative_representation_keeps_canonical_format_contract`
- `tests/test_codegen_contract_compatibility.py::test_product_signal_targeting_option_keeps_discriminated_signal_ref`

### R10 — a `model_construct`ed union base is refused at its own field (1)
- `tests/test_simple_api.py::test_preview_creative_simple_api`

### R11 — the async-response union is swallowed by `GetProductsAsyncWorking` (11)
- `tests/test_legacy_only_creative_surfaces.py::test_primary_webhook_sanitizes_every_status_and_activity[failed]`
- `tests/test_legacy_only_creative_surfaces.py::test_primary_webhook_sanitizes_every_status_and_activity[input-required]`
- `tests/test_legacy_only_creative_surfaces.py::test_primary_webhook_sanitizes_every_status_and_activity[working]`
- `tests/test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip[build-multi]`
- `tests/test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip[build-single]`
- `tests/test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip[build-variants]`
- `tests/test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip[preview]`
- `tests/test_manifest_response_readback.py::test_public_completed_task_parser_keeps_manifest_readback[build-multi]`
- `tests/test_manifest_response_readback.py::test_public_completed_task_parser_keeps_manifest_readback[build-single]`
- `tests/test_manifest_response_readback.py::test_public_completed_task_parser_keeps_manifest_readback[build-variants]`
- `tests/test_manifest_response_readback.py::test_public_completed_task_parser_keeps_manifest_readback[preview]`

### R12 — the advertised `outputSchema` lost its branches (4)
- `tests/test_server_dx.py::TestPydanticSchemas::test_media_buy_output_schema_allows_30_and_31_sync_shapes`
- `tests/test_tools_list_output_schema.py::test_create_media_buy_output_schema_includes_response_union`
- `tests/test_tools_list_output_schema.py::test_media_buy_output_schema_accepts_negotiated_30_statuses`
- `tests/test_tools_list_output_schema.py::test_new_brand_creative_tools_have_output_schema`

### R13 — registry/core word collision (6)
- `tests/test_registry.py::TestPolicyExports::test_policy_exported_from_types`
- `tests/test_registry.py::TestPolicyExports::test_policy_history_exported_from_types`
- `tests/test_registry.py::TestPolicyExports::test_policy_revision_exported_from_types`
- `tests/test_registry.py::TestPolicyExports::test_policy_summary_exported_from_types`
- `tests/test_registry.py::TestPublicApiExports::test_resolved_brand_exported_from_types`
- `tests/test_registry.py::TestPublicApiExports::test_resolved_property_exported_from_types`

### R14 — the `__all__` / `__dir__` advertisement contract (3)
- `tests/test_adcp_31_rc4_surface.py::test_rc4_symbols_are_publicly_exported`
- `tests/test_lazy_types.py::test_partial_module_names_all_resolve_via_adcp_types`
- `tests/test_lazy_types.py::test_partial_modules_are_in_types_all`

### R15 — three words bound nowhere (3)
- `tests/test_migrate_v3_to_v4.py::test_generated_poc_symbol_map_covers_publicly_exported_names`
- `tests/test_rc6_adoption.py::test_historical_v32_models_keep_their_beta6_identity_offline`
- `tests/test_validate_platform_warnings.py::test_v3_reference_seller_passes_with_no_warnings`

### R16 — stale surface censuses (4)
STALE TEST:
- `tests/test_public_api.py::test_public_api_surface_matches_snapshot`

SDK (`src/adcp/types/_adapter.py`):
- `tests/test_public_words_resolve.py::test_every_declared_refusal_cites_a_location_that_exists`
- `tests/test_public_words_resolve.py::test_our_own_source_does_not_import_a_word_the_package_refuses`
- `tests/test_public_words_resolve.py::test_the_refusal_table_and_the_public_surface_agree`

### R17 — collision-resolved capability class names (2)
- `tests/test_decisioning_capabilities_submodule.py::test_signals_features_and_content_standards_re_exported`
- `tests/test_decisioning_capabilities_submodule.py::test_wire_spec_names_resolve_in_submodule`

### R18 — `create-media-buy-request`'s root `anyOf` lowered to branch classes (2)
- `tests/test_codegen_contract_compatibility.py::test_create_media_buy_request_requires_one_root_anyof_group`
- `tests/test_proposal_lifecycle_e2e.py::test_create_media_buy_rejects_disallowed_pricing_model`

### R19 — `RequiredGroups` message wording (1)
- `tests/test_codegen_contract_compatibility.py::test_sync_creatives_request_takes_assignment_operations_without_creatives`

### R20 — postal cross-field refusal now comes from the branch union (4)
- `tests/test_postal_area_compat.py::test_native_postal_country_system_mismatches_fail_closed[DE-zip]`
- `tests/test_postal_area_compat.py::test_native_postal_country_system_mismatches_fail_closed[NL-plz]`
- `tests/test_postal_area_compat.py::test_native_postal_country_system_mismatches_fail_closed[US-plz]`
- `tests/test_postal_area_compat.py::test_targeting_overlay_rejects_mismatched_postal_pair`

### R21 — `v1_format_ref` survives the projection (2)
- `tests/test_seller_agent_storyboard.py::test_compact_catalog_ignores_outcome_target_and_paginates_fields`
- `tests/test_seller_agent_storyboard.py::test_get_products_uses_canonical_models_and_preserves_legacy_delivery`

### R22 — the canonical/legacy fork no longer discriminates (1)
- `tests/test_client.py::test_get_products_still_projects_legacy_format_ids`

### R23 — undeclared approximations (2)
- `tests/conformance/test_schema_model_parity.py::test_schema_and_model_agree[context_match]`
- `tests/conformance/test_schema_model_parity.py::test_schema_and_model_agree[control_media_buy]`

### R24 — three declared divergences no longer occur (1)
- `tests/conformance/test_schema_model_parity.py::test_every_declared_divergence_still_occurs`

### R25 — `function-wrap[<lambda>()]` in the error `loc` (1)
- `tests/test_error_narrowing.py::test_e2e_creative_manifest_missing_width_height_surfaces_actionable_errors`

### R26 — `params` is a model, not a dict (1)
- `tests/test_preview_html.py::test_get_products_with_preview_urls`

### R27 — the base `ReportingReceipt` at a `ReceiptsItem` position (2)
- `tests/test_reporting_reconciliation.py::test_reconciles_billing_and_records_matching_receipt`
- `tests/test_reporting_reconciliation.py::test_recorded_rejected_checkpoint_is_reinspected`

### R28 — dialect resolution fails closed before the version preflight (2)
- `tests/test_version_client_boundaries.py::test_version_preflight_failure_is_a_failed_result_without_dispatch[null_clear-a2a]`
- `tests/test_version_client_boundaries.py::test_version_preflight_failure_is_a_failed_result_without_dispatch[null_clear-mcp]`

### R29 — a CI manifest names a deleted test file (1)
- `tests/test_native_ci.py::test_compatibility_suite_checks_runtime_on_every_interpreter_without_adopter_rebuilds`

### R30 — `_generated` is no longer on the first-access path (1)
- `tests/test_lazy_types.py::test_schema_symbol_triggers_build`

### R31 — two httpcore distributions spell one annotation differently (1)
- `tests/conformance/signing/test_ip_pinned_transport.py::test_httpcore2_backends_match_the_httpcore_signatures`

### R32 — a nested array-item class carries no version envelope (1)
- `tests/test_manifest_response_readback.py::test_nested_build_readback_preserves_envelopes_and_constraints`

### R33 — a URL field holds an object, not a `str` (2)
- `tests/test_freezegun_models.py::test_freezegun_in_fresh_process[prewarm]`
- `tests/test_freezegun_models.py::test_freezegun_in_fresh_process[reverse]`

### R34 — a deferred root model dumps as `{}` by inference (1)
- `tests/test_lazy_rebuild.py::test_a_deferred_instance_dumps_through_a_plain_pydantic_parent`

### The 4 ERRORs — `_schemas` excluded from the built distribution (not part of the 126)
- `tests/conformance/reporting/test_reporting_notification_packaging.py::test_installed_base_import_needs_no_pg_extra[wheel]`
- `tests/conformance/reporting/test_reporting_notification_packaging.py::test_installed_base_import_needs_no_pg_extra[sdist]`
- `tests/conformance/reporting/test_reporting_notification_packaging.py::test_installed_pg_extra_migrates_commits_and_restarts[wheel]`
- `tests/conformance/reporting/test_reporting_notification_packaging.py::test_installed_pg_extra_migrates_commits_and_restarts[sdist]`
