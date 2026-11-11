# Porting an application off upstream `adcp`

**This package ships the types the AdCP schema bundle states, and nothing else.** It is not
a replacement for upstream's `adcp` wheel and does not intend to become one: the server,
decisioning, reporting, signing and canonical-format layers are hand-written, no document
states them, and nothing here can derive them. `README.md` measures that split and names
the instrument beside every figure; this document is the other half of the same answer —
**for each name an application imports, what to use instead, or the sentence saying there
is nothing and why.**

**READ THIS FIRST, BECAUSE IT DECIDES WHETHER THE REST APPLIES TO YOU.** You cannot install
this wheel *beside* upstream's. Both distributions own the `adcp` import root, so the
installer interleaves them at file granularity, the order decides who wins each file, and
`pip check` reports the result as healthy. Measured, both orders, in a throwaway virtual
environment:

| | upstream installed first, then this | this installed first, then upstream |
|---|---|---|
| `adcp.types.core.PaginationRequest` | ours, with its `__adcp_schema__` | `ImportError` |
| `import adcp.server` | `ImportError` | imports |
| `import adcp.decisioning` | `ImportError` | imports |
| `len(adcp.__all__)` | 0 | 748 |
| `uv pip check` | all compatible | all compatible |

Neither order is a working mixture and no tool says so. **So an application that needs the
machinery keeps upstream's wheel and does not install this one.** What this package is for
is code that needs the AdCP *types* — a client, a library, a service that speaks the
protocol and owns its own transport — and the entries below are written for the port that
follows from that choice.

---

## Validate with `strict_validate`, not `model_validate`

**Every class in this package carries `strict_validate`, and it is the call to make.** It
validates the payload against the schema node the class was compiled from, then hands the
same payload to `model_validate` — so you get exactly the instance `model_validate` would
have given you, after the document has had its say:

```python
Root.strict_validate(payload)      # schema first, then the model
Root.model_validate(payload)       # the model alone
```

It is not a different constructor and it is not a stricter mode of the class. It is the
same construction with the document's own verdict in front of it, and it calls
`model_validate` underneath.

**Why it exists: a Python type annotation cannot say everything a JSON Schema node says.**
The gaps are not exotic and you will meet them on ordinary fields:

| the document says | the annotation says | what differs |
|---|---|---|
| `type: integer` | `int` | pydantic coerces `"1"` and `True` to `1`; the document refuses both |
| an optional property | `X \| None = None` | `None` means *absent* to the document and *an explicit null* to the annotation — two different payloads |
| `oneOf` branches split by which key is present | one class, both fields optional | the exclusivity has nowhere to live in the signature |
| a `pattern`, a `maxLength`, a conditional | an `Annotated` constraint, or a rule | expressible, but only some of them, and only one at a time |

Some of these we close at the type — an optional non-nullable property now refuses an
explicit null. Others cannot be closed without making the class *wrong in the other
direction*: forcing `int` to strict would reject `1.0`, which the document **accepts**,
because JSON Schema treats a number with zero fractional part as an integer. **Trading a
permissive reading for a wrong one is not a fix.**

So the schema half is where those facts live, and `strict_validate` is how you consult it.

**The cost is a `jsonschema` validation per call** — negligible beside a network round trip,
and far cheaper than the alternatives: carrying the schema's rules a second time in
hand-written checks, or shipping types so contorted that the annotation stops telling a
reader what the field is. **The runtime penalty is small; the complexity and the degraded
developer experience of the alternative are not.**

Use `model_validate` where the payload has already been checked, or where you are
constructing an instance yourself rather than parsing one. Use `strict_validate` at every
boundary where a payload arrives from somewhere else.

---

## The set, the instrument, and what an entry owes

**The set every figure here is over: the 503 distinct names, from 82 distinct modules, that
upstream's own consumer-facing code imports.** That is upstream's `v9.2.0` checkout — its
80 `examples/**/*.py` files and the 477 Python fences of `README.md`, `llms.txt`,
`MIGRATION*.md`, `docs/**/*.md` and `skills/**` — with every `import adcp…` parsed by `ast`
and every imported name attributed to the module that *defines* it on the **installed
upstream `adcp` 9.6.1 wheel**. Not upstream's export surface, which is 27,094 public
`(module, name)` rows and mostly reachable only because a module declares no `__all__`; a
percentage over that set would mean nothing.

Two instruments, and every figure below says which one it comes from:

- **`survey/consumer_imports.py`** — the census the README's first table quotes: 503 names,
  82 modules, 120 (23.9%) defined by `adcp.types`, 23 (4.6%) resolving nowhere.
- **`survey/migration_notes.py`** — this document's own instrument. It partitions the same
  503 names into the buckets below and then **grades this file**, exiting non-zero on any
  name it owes an entry for and does not name. Its join is on **identity** — the field set
  read by wire alias, or the enumeration's value list — and never on a name, which is
  `docs/plan/final-state.md` reading 10's rule and the reason this partition does not move
  when a class of ours is renamed.

**How the 503 partition** (`survey/migration_notes.py`, upstream `adcp` 9.6.1 against
`src/adcp/types` of this tree):

| bucket | names | this guide |
|---|---|---|
| machinery this package does not ship | 360 | §1 |
| resolves nowhere on upstream's own wheel | 23 | §2 |
| on the type surface, but not a type | 13 | §3 |
| on the type surface, with no schema subject | 8 | §4 |
| on the type surface, meaning something else | 7 | §5 |
| on the type surface, with no identity for the instrument to join on | 7 | §6 |
| **owed an entry here** | **418** | |
| a class of ours holds the same identity — the alias layer's | 85 | §7 |

**418 + 85 = 503.** The second row is why **the denominator for "what do we owe" is 480 and
not 503**: reading 10 says a name that raises on upstream's own wheel is a finding about
them and not a name we owe, and 23 of the 503 do exactly that. 480 of 503 is the set a
reader can hold this package to; the other 23 are reported in §2 with their errors because
a reader whose code imports one of them needs to know it was already broken.

**An entry gives one of three answers, and the third is a correct entry.** A real
destination, named as an import path with the bundle document behind it; *no replacement*,
with why; or *undecided*, naming what would decide it. **Inventing a destination is the
defect** — reading 10: "minting a nodeless class to satisfy an import is the back door this
ordering exists to close."

**How the 418 entries answer, counted off the sections below:**

| answer | names | |
|---|---|---|
| a real import path of this package | 26 | §2 (10) · §3 (6) · §4 (2) · §5 (4) · §6 (4) |
| no replacement, with the reason | 386 | §1 (360) · §2 (13) · §3 (7) · §4 (5) · §5 (1) |
| undecided, with what would decide it | 6 | §4 (1) · §5 (2) · §6 (3) |

**386 of the 418 are "no replacement", and 360 of those are one sentence**: the machinery in
§1, which no document states. The honest reading of this table is that **porting an
application off upstream's wheel is a decision about the machinery and not a rename
exercise** — the type spellings are mostly handled (§7's 85 and these 26), and everything
else is the layer this package was never going to ship.

**Two words, used strictly.** *The bundle* is the schema repository
`adcontextprotocol/adcp`, the documents this package compiles. *Upstream's wheel* is the
Python package `adcp` on PyPI. They are different things.

---

## §1. Machinery: 360 names, and upstream's wheel still has every one

**These are the 360 names whose defining module on upstream's wheel is not under
`adcp.types`.** There is no replacement for any of them here and there will not be: none is
stated by a bundle document, so this package has nothing to derive one from. Every one of
them is still on upstream's `adcp` wheel at the module named beside it, unchanged — the
finding is about *this* package's scope and not about upstream's code.

**What to do instead, and it is a decision about your application rather than an import
rewrite.** If your code reaches any of these, the machinery is what your application is
built on; keep upstream's wheel (see the table at the top of this document — you cannot
have both). If you reach only a few of them — a `client`, an `exceptions` class, a
`webhooks` verifier — those are the places worth owning yourself, because each is a
hand-written layer over a transport you already control, and the types underneath them are
what this package gives you.

Grouped by the top-level child of `adcp` that defines them, then by defining module. **32
top-level children define these 360 names** — the 8 subpackages and 22 top-level modules
`README.md` lists, plus `adcp._version` and `adcp._null_clear`, which are private on
upstream's wheel and reached anyway by its own documentation.

<!-- GENERATED: survey/migration_notes.py writes the partition these names come from; the
     gate at the end of this document fails if one goes missing. -->

**`adcp.reporting`** — a subpackage; 74 names from 35 defining modules.

- `adcp.reporting._testing_failures` — `ReportingFailurePlan` · `ReportingTestBarrier`
- `adcp.reporting.currency` — `require_single_currency`
- `adcp.reporting.feed.store` — `ReportingFeedStore`
- `adcp.reporting.fixtures` — `redacted_capabilities` · `redacted_snapshot_request`
- `adcp.reporting.inline_source` — `InlineFetchResult` · `MetricEvidence` · `metric_delayed_through` · `metric_unsupported_everywhere`
- `adcp.reporting.ledger.consumer_status` — `ConsumerStatusIngest`
- `adcp.reporting.ledger.delivery_models` — `ReportingDestinationBinding` · `ReportingMaterializationAttempt` · `ReportingObligationDeliveryRecord`
- `adcp.reporting.ledger.models` — `ReportingConfiguration` · `ReportingConfigurationGenerationKey` · `ReportingDeliveryEscalation` · `ReportingObligationRecord` · `ReportingRevisionRecord`
- `adcp.reporting.ledger.notification_models` — `ReportingNotificationError`
- `adcp.reporting.ledger.producer` — `ProducerOfferings` · `ReportingProducer`
- `adcp.reporting.ledger.status` — `ReportingStatusHandler`
- `adcp.reporting.ledger.status_server` — `ReportingStatusCallerResolver` · `ReportingStatusNotificationHandler`
- `adcp.reporting.materializer.contracts` — `ReportingDestinationResolver` · `ReportingDestinationWriter` · `ReportingIOContext` · `ReportingWriterError` · `ReportingWriterFailure`
- `adcp.reporting.materializer.reference` — `ReferenceReportingDestinationWriter` · `ReferenceReportingResolver` · `reference_verifier`
- `adcp.reporting.materializer.service` — `ReportingMaterializerService`
- `adcp.reporting.materializer.verification` — `ReportingDestinationIO` · `ReportingRevisionRowReader` · `ReportingRevisionVerifier` · `ReportingRevisionVerifierRegistry` · `ReportingVerifiedDestination`
- `adcp.reporting.outbox.activity` — `ReportingActivityProjector`
- `adcp.reporting.outbox.identity` — `resolve_reporting_consumer`
- `adcp.reporting.outbox.routing` — `ReportingEnvelopeCipher` · `ReportingNotificationSubscription` · `ReportingSigningResolver` · `ReportingSubscriptionResolver`
- `adcp.reporting.outbox.status` — `ReportingStatusProjector` · `ReportingStatusSweeper`
- `adcp.reporting.outbox.status_service` — `ReportingStatusNotificationLifecycle` · `ReportingStatusService`
- `adcp.reporting.outbox.status_support` — `ReportingStatusSupport` · `validate_status_claims`
- `adcp.reporting.outbox.support` — `ReportingActivitySupport`
- `adcp.reporting.outbox.worker` — `ReportingNotificationWorker`
- `adcp.reporting.production.configuration` — `ReportingProductionConfigurationTask`
- `adcp.reporting.production.notifications` — `ReportingProductionSigning` · `production_notification_workers`
- `adcp.reporting.production.offerings` — `ReportingProductionOffering`
- `adcp.reporting.production.service` — `ReportingProductionDestination` · `ReportingProductionSupport`
- `adcp.reporting.receipts` — `ReceiptAccountResolver`
- `adcp.reporting.receipts.handler` — `ReportingReceiptHandler`
- `adcp.reporting.service` — `ReliableReportingService` · `ReportingAccountContext` · `ReportingAdapter` · `ReportingContextResolver`
- `adcp.reporting.service_lifecycle` — `ReliableReportingShutdownTimeoutError` · `ReliableReportingState`
- `adcp.reporting.service_production` — `ReportingProductionOptions` · `ReportingServiceOffering`
- `adcp.reporting.source` — `ReportingSourceCapabilitiesV1` · `ReportingSourceSliceRequestV1`
- `adcp.reporting.testing` — `DeterministicReportingClock` · `ScriptedReportingAdapter` · `run_reporting_adapter_conformance`

**`adcp.server`** — a subpackage; 69 names from 17 defining modules.

- `adcp.server` — `DISCOVERY_METHODS` · `DISCOVERY_TOOLS` · `MessageParser` · `SkillMiddleware` · `TokenValidator`
- `adcp.server.a2a_push_security` — `normalize_allowed_push_hosts` · `resolve_push_destination_settings` · `scope_from_server_context` · `validate_a2a_push_notification_url`
- `adcp.server.a2a_server` — `create_a2a_server`
- `adcp.server.auth` — `AUTHENTICATED_TENANT_METADATA_KEY` · `AuthRequest` · `BearerTokenAuth` · `BearerTokenAuthMiddleware` · `Principal` · `PrincipalResolverError` · `ROUTED_TENANT_METADATA_KEY` · `auth_context_factory` · `enforce_authenticated_tenant` · `validator_from_token_map`
- `adcp.server.base` — `ADCPHandler` · `AccountAwareToolContext` · `ToolContext`
- `adcp.server.governance_enforcement` — `GovernanceEnforcementDecision` · `make_governance_enforcement_middleware`
- `adcp.server.helpers` — `AccountError` · `adcp_error` · `cancel_media_buy_response` · `resolve_account` · `resolve_account_into_context` · `valid_actions_for_status`
- `adcp.server.idempotency.backends` — `MemoryBackend` · `PgBackend`
- `adcp.server.idempotency.store` — `IdempotencyStore`
- `adcp.server.idempotency.webhook_dedup` — `WebhookDedupStore`
- `adcp.server.mcp_sessions` — `get_mcp_session_stats`
- `adcp.server.mcp_tools` — `validate_discovery_set`
- `adcp.server.responses` — `activate_signal_response` · `build_creative_response` · `capabilities_response` · `delivery_response` · `legacy_creative_formats_response` · `list_creatives_response` · `log_event_response` · `media_buy_response` · `media_buys_response` · `preview_creative_response` · `products_response` · `signals_response` · `sync_accounts_response` · `sync_catalogs_response` · `sync_creatives_response` · `sync_governance_response` · `update_media_buy_response`
- `adcp.server.serve` — `RequestMetadata` · `ServeConfig` · `create_mcp_server`
- `adcp.server.signed_requests` — `RequestSignatureVerification`
- `adcp.server.tenant_router` — `InMemorySubdomainTenantRouter` · `SubdomainTenantMiddleware` · `SubdomainTenantRouter` · `Tenant` · `current_tenant` · `normalize_host_key`
- `adcp.server.test_controller` — `INSECURE_ALLOW_ALL` · `TestControllerError` · `TestControllerStore` · `_list_scenarios` · `register_test_controller`

**`adcp.decisioning`** — a subpackage; 68 names from 30 defining modules.

- `adcp.decisioning` — `BillingMode` · `BuyerAgentStatus` · `TaskTransition`
- `adcp.decisioning.account_projection` — `project_account_for_response` · `project_business_entity_for_response` · `strip_credentials_from_wire_result` · `to_wire_account` · `to_wire_sync_accounts_row`
- `adcp.decisioning.accounts` — `AccountStore` · `ExplicitAccounts` · `NaturalKeyAccounts` · `ResolveContext` · `SingletonAccounts`
- `adcp.decisioning.context` — `AuthInfo` · `RequestContext`
- `adcp.decisioning.errors` — `MediaBuyNotFoundError` · `ServiceUnavailableError`
- `adcp.decisioning.handler` — `PlatformHandler`
- `adcp.decisioning.media_buy_store` — `create_media_buy_store`
- `adcp.decisioning.mock_ad_server` — `InMemoryMockAdServer` · `MockAdServer`
- `adcp.decisioning.negotiation` — `execute_refinement_batch`
- `adcp.decisioning.pg.lazy` — `LazyTaskRegistry` · `LazyTaskWebhookOutbox`
- `adcp.decisioning.pg.media_buy_context_store` — `PgMediaBuyContextStore`
- `adcp.decisioning.pg.task_registry` — `PgTaskRegistry`
- `adcp.decisioning.pg.task_webhook_outbox` — `PgTaskWebhookOutbox`
- `adcp.decisioning.platform` — `DecisioningCapabilities` · `DecisioningPlatform`
- `adcp.decisioning.platform_router` — `PlatformRouter`
- `adcp.decisioning.proposal_manager` — `FinalizeProposalRequest` · `FinalizeProposalSuccess` · `MockProposalManager` · `ProposalCapabilities`
- `adcp.decisioning.proposal_store` — `create_dev_proposal_store`
- `adcp.decisioning.recipe` — `CapabilityOverlap` · `Recipe`
- `adcp.decisioning.refine` — `RefineResult` · `RefinementOutcome`
- `adcp.decisioning.registry` — `ApiKeyCredential` · `BuyerAgent` · `BuyerAgentDefaultTerms` · `BuyerAgentRegistry` · `OAuthCredential` · `bearer_only_registry` · `mixed_registry` · `signing_only_registry`
- `adcp.decisioning.registry_cache` — `AuditingBuyerAgentRegistry` · `CachingBuyerAgentRegistry` · `RateLimitedBuyerAgentRegistry`
- `adcp.decisioning.roster_store` — `create_roster_account_store`
- `adcp.decisioning.serve` — `create_adcp_server_from_platform` · `serve`
- `adcp.decisioning.specialisms.sales` — `SalesPlatform`
- `adcp.decisioning.state_machines` — `assert_media_buy_transition`
- `adcp.decisioning.task_registry` — `InMemoryTaskRegistry` · `ListableTaskRegistry` · `TaskHandoffContext` · `TaskRegistry`
- `adcp.decisioning.types` — `Account` · `AdcpError` · `SalesResult` · `SyncAccountsResultRow`
- `adcp.decisioning.update_media_buy` — `decompose_update_media_buy` · `disallowed_update_media_buy_mutations`
- `adcp.decisioning.upstream` — `StaticBearer` · `UpstreamHttpClient`
- `adcp.decisioning.validate_capabilities` — `validate_capabilities_response_shape_async`

**`adcp.canonical_formats`** — a subpackage; 26 names from 7 defining modules.

- `adcp.canonical_formats.format_options` — `FormatKindNotInClosedSetError` · `find_declaration_by_kind` · `find_declaration_by_v1_format_id` · `validate_format_kind_in_options`
- `adcp.canonical_formats.narrowing` — `check_narrows` · `narrowing_advisory`
- `adcp.canonical_formats.pixel_tracker` — `PixelTrackerBatchResult` · `PixelTrackerDowngrade` · `PixelTrackerUpgrade` · `downgrade_pixel_tracker` · `downgrade_pixel_trackers` · `upgrade_v1_tracker` · `upgrade_v1_trackers`
- `adcp.canonical_formats.projection` — `CanonicalFormatLegacyResolutionContext` · `LegacyFormatConversionContext` · `migrated_format_option_id` · `normalize_legacy_creative_request` · `project_canonical_response_to_legacy` · `projection_adapters_from_catalog_snapshots`
- `adcp.canonical_formats.registry` — `load_default_registry`
- `adcp.canonical_formats.v1_to_v2` — `V1CatalogProjection` · `V1ToV2Projection` · `project_v1_catalog_to_v2` · `project_v1_format_to_declaration`
- `adcp.canonical_formats.v2_to_v1` — `project_declaration_to_v1` · `project_product_to_v1`

**`adcp.signing`** — a subpackage; 23 names from 16 defining modules.

- `adcp.signing` — `DEFAULT_ALLOWED_PORTS`
- `adcp.signing.agent_resolver` — `async_resolve_agent` · `verify_from_agent_url`
- `adcp.signing.autosign` — `SigningConfig`
- `adcp.signing.brand_jwks` — `BrandJsonJwksResolver`
- `adcp.signing.client` — `install_signing_event_hook` · `signing_operation`
- `adcp.signing.crypto` — `load_private_key_pem`
- `adcp.signing.errors` — `SignatureVerificationError`
- `adcp.signing.jwks` — `CachingJwksResolver` · `StaticJwksResolver`
- `adcp.signing.keygen` — `generate_signing_keypair`
- `adcp.signing.middleware` — `unauthorized_response_headers` · `verify_starlette_request`
- `adcp.signing.pg.replay_store` — `PgReplayStore`
- `adcp.signing.replay` — `InMemoryReplayStore`
- `adcp.signing.signer` — `sign_request`
- `adcp.signing.signer_keys` — `JwksUriSignerKeys` · `StaticSignerKeys`
- `adcp.signing.verifier` — `VerifierCapability` · `VerifyOptions`
- `adcp.signing.webhook_verifier` — `WebhookVerifyOptions` · `verify_webhook_from_agent_url`

**`adcp.exceptions`** — a top-level module; 13 names from 1 defining module.

- `adcp.exceptions` — `ADCPAuthenticationError` · `ADCPConnectionError` · `ADCPError` · `ADCPProtocolError` · `ADCPResponseEncodingError` · `ADCPResponseTooLargeError` · `ADCPTimeoutError` · `ADCPToolNotFoundError` · `ADCPWebhookSignatureError` · `AdagentsNotFoundError` · `AdagentsValidationError` · `IdempotencyConflictError` · `IdempotencyExpiredError`

**`adcp.adagents`** — a top-level module; 11 names from 1 defining module.

- `adcp.adagents` — `domain_matches` · `fetch_adagents` · `fetch_agent_authorizations` · `find_authorized_agent_entries` · `get_all_properties` · `get_all_tags` · `get_properties_by_agent` · `resolve_properties_for_agent` · `validate_adagents_structure` · `verify_agent_authorization` · `verify_agent_for_property`

**`adcp.client`** — a top-level module; 10 names from 1 defining module.

- `adcp.client` — `ADCPClient` · `ADCPMultiAgentClient` · `DEFAULT_MAX_RESPONSE_BYTES` · `WIRE_RESPONSE_METADATA_KEY` · `creative_agent` · `test_agent` · `test_agent_a2a` · `test_agent_a2a_no_auth` · `test_agent_client` · `test_agent_no_auth`

**`adcp.webhooks`** — a top-level module; 9 names from 1 defining module.

- `adcp.webhooks` — `ReportingWebhookOperationIdMissingError` · `WebhookChallengeError` · `WebhookDestinationPolicy` · `WebhookDestinationValidationError` · `challenge_webhook_destination` · `create_mcp_webhook_payload` · `deliver` · `generate_webhook_idempotency_key` · `validate_webhook_destination_url`

**`adcp.compat`** — a subpackage; 6 names from 3 defining modules.

- `adcp.compat.negotiated_catalog_purchase` — `CoordinatorBuyProductsInput` · `MediaBuyLifecycleCoordinator`
- `adcp.compat.purchase_continuation` — `LegacyPurchaseCoordinator` · `PendingTaskResolution` · `ReconciliationResult`
- `adcp.compat.sqlite_continuation_store` — `SqliteCompatibilityContinuationStore`

**`adcp.media_buy_actions`** — a top-level module; 6 names from 1 defining module.

- `adcp.media_buy_actions` — `ActionAvailabilityStatus` · `ChangeTermSelection` · `assess_media_buy_action` · `assess_update_media_buy_actions` · `materialize_change_terms` · `project_available_actions`

**`adcp.testing`** — a subpackage; 6 names from 5 defining modules.

- `adcp.testing` — `TEST_AGENT_TOKEN`
- `adcp.testing.decisioning` — `build_test_client`
- `adcp.testing.harness` — `SellerA2AClient` · `SellerTestClient`
- `adcp.testing.models` — `build_all_models`
- `adcp.testing.test_helpers` — `create_test_agent`

**`adcp.oauth`** — a top-level module; 5 names from 1 defining module.

- `adcp.oauth` — `InMemoryPendingOAuthFlowStore` · `OAuthIssuerBinding` · `complete_oauth_authorization` · `discover_oauth_metadata` · `start_oauth_authorization`

**`adcp.webhook_sender`** — a top-level module; 4 names from 1 defining module.

- `adcp.webhook_sender` — `ScopePermanentlyUnknown` · `ScopeTransientlyUnavailable` · `WebhookSender` · `WebhookSenderResolution`

**`adcp.property_lists`** — a top-level module; 3 names from 1 defining module.

- `adcp.property_lists` — `MCPPropertyListFetcher` · `ProductPropertyPolicy` · `check_property_list_reference`

**`adcp.substitution`** — a top-level module; 3 names from 1 defining module.

- `adcp.substitution` — `NativeMacroMapping` · `ValueMacroMapping` · `translate_universal_macros`

**`adcp.validation`** — a subpackage; 3 names from 2 defining modules.

- `adcp.validation.client_hooks` — `SERVER_DEFAULT_VALIDATION` · `ValidationHookConfig`
- `adcp.validation.schema_validator` — `validate_request`

**`adcp.webhook_receiver`** — a top-level module; 3 names from 1 defining module.

- `adcp.webhook_receiver` — `LegacyHmacFallback` · `WebhookReceiver` · `WebhookReceiverConfig`

**`adcp.acceptance`** — a top-level module; 2 names from 1 defining module.

- `adcp.acceptance` — `AcceptancePolicyOutcome` · `AcceptancePolicyResolver`

**`adcp.audit_sink`** — a top-level module; 2 names from 1 defining module.

- `adcp.audit_sink` — `AuditEvent` · `AuditSink`

**`adcp.governance`** — a top-level module; 2 names from 1 defining module.

- `adcp.governance` — `GovernanceCommitment` · `InMemoryGovernanceReplayStore`

**`adcp.identifiers`** — a top-level module; 2 names from 1 defining module.

- `adcp.identifiers` — `normalize_identifier` · `validate_publisher_domain`

**`adcp._null_clear`** — a top-level module; 1 name from 1 defining module.

- `adcp._null_clear` — `nullable_request_paths`

**`adcp._version`** — a top-level module; 1 name from 1 defining module.

- `adcp._version` — `normalize_to_release_precision`

**`adcp.feed_mirror`** — a top-level module; 1 name from 1 defining module.

- `adcp.feed_mirror` — `FeedMirror`

**`adcp.negotiation`** — a top-level module; 1 name from 1 defining module.

- `adcp.negotiation` — `refine_proposals_verified`

**`adcp.notification_outbox_pg`** — a top-level module; 1 name from 1 defining module.

- `adcp.notification_outbox_pg` — `PgNotificationOutbox`

**`adcp.observability`** — a top-level module; 1 name from 1 defining module.

- `adcp.observability` — `is_tracing_available`

**`adcp.registry`** — a top-level module; 1 name from 1 defining module.

- `adcp.registry` — `RegistryClient`

**`adcp.task_options`** — a top-level module; 1 name from 1 defining module.

- `adcp.task_options` — `TaskOptions`

**`adcp.webhook_supervisor`** — a top-level module; 1 name from 1 defining module.

- `adcp.webhook_supervisor` — `InMemoryWebhookDeliverySupervisor`

**`adcp.webhook_transport_hooks`** — a top-level module; 1 name from 1 defining module.

- `adcp.webhook_transport_hooks` — `DockerLocalhostRewrite`

---

## §2. 23 names that resolve nowhere on upstream's own 9.6.1 wheel

**A name that raises on upstream's wheel is not a name this package owes** — reading 10 —
and it is reported here with the error because an application still carrying one of these
imports is already broken against the wheel it has installed.

**20 of the 23 raise at the name**: 17 an `AttributeError`, and 3 an `ImportError` carrying
upstream's own migration note. **The other 3 are spelled at a module upstream's wheel does
not have at all.**

**AND THAT 20 IS WHERE THIS DOCUMENT CORRECTS `README.md`, so read which set each figure is
over.** The README says "23 names resolve nowhere … and **21 of them raise**". 21 is the
count of **`(module, name)` pairs** that raise, which is what `survey/consumer_imports.py`
collects; **by NAME it is 20.** The extra pair is `adcp.GetAdcpCapabilitiesRequest`, which
raises at `adcp` and **resolves at `adcp.types`** — so it is a name upstream still has, it
is not one of the 23, and it is in §7's alias-layer set. Three figures, three sets: **21
pairs raise · 20 names raise · 23 names resolve nowhere.** None of them is wrong and none of
them is interchangeable.

| the name, as consumer code spells it | what upstream's 9.6.1 wheel does | what this package has |
|---|---|---|
| `adcp.BrandManifest` | `ImportError`: "was removed in adcp 4.0: use `BrandReference(domain=...)` on requests; read `ResolvedBrand.brand` from the response" | no class of that name; the replacement upstream names is a type, and §7's instrument places `BrandReference` in the alias layer |
| `adcp.Pricing` | `ImportError`: "was removed in adcp 4.0: use the discriminated pricing classes (e.g. `CpmFixedRatePricingOption`)" | the discriminated options are under `adcp.types.pricing_options`; `Pricing` itself has no document |
| `adcp.FormatCategory` | `ImportError`: "was removed in adcp 4.0: removed without replacement — format metadata carries category info" | **no replacement, and upstream says so too.** Its other spelling, `adcp.types.generated_poc.enums.format_category`, raises an `ImportError` pointing at `adcp.types.FormatId` — **which also does not exist on their wheel**, and is the row below |
| `adcp.types.FormatId` | `AttributeError` | **`adcp.types.core.FormatReferenceStructuredObject`**, from `core/format-id.json` — and read that document before using it, because it carries `"deprecated": true` and its own text says new products use `format_options`, `format_kind` and `format_option_ref`. The name differs because the document's title is "Format Reference (Structured Object)" |
| `adcp.types.ImageAsset` | `AttributeError` | **`adcp.types.core.ImageAsset`**, from `core/assets/image-asset.json` |
| `adcp.types.UrlAsset` | `AttributeError` | **`adcp.types.core.URLAsset`**, from `core/assets/url-asset.json`. The acronym is cased differently and that is the only difference |
| `adcp.SubAsset`, `adcp.TextSubAsset`, `adcp.MediaSubAsset` | `AttributeError` each | **no replacement.** The bundle has twenty asset documents under `core/assets/` and states no sub-asset subject in any of them — searched for `sub_assets`, `subAssets` and the title "Sub Asset", zero documents. Use the asset document your payload actually carries |
| `adcp.BuildCreativeRequest` | `AttributeError` | **`adcp.types.media_buy.BuildCreativeRequest`**, from `media-buy/build-creative-request.json` |
| `adcp.types.BuildCreativeSuccessResponse` | `AttributeError` | **`adcp.types.media_buy.BuildCreativeSuccess`**, from `media-buy/build-creative-response.json` — one of that document's seven exported declarations, beside `BuildCreativeResponse`, `BuildCreativeError` and the rest |
| `adcp.PreviewCreativeRequest` | `AttributeError` | **`adcp.types.creative.PreviewCreativeRequest`**, from `creative/preview-creative-request.json` |
| `adcp.types.ListCreativeFormatsRequest` | `AttributeError` | **`adcp.types.media_buy.ListCreativeFormatsRequest`**, from `media-buy/list-creative-formats-request.json` |
| `adcp.CreateMediaBuySuccess` | `AttributeError` | **`adcp.types.media_buy.CreateMediaBuySuccess`**, from `media-buy/create-media-buy-response.json` |
| `adcp.CreateMediaBuyError` | `AttributeError` | **`adcp.types.media_buy.CreateMediaBuyError`**, from `media-buy/create-media-buy-response.json` |
| `adcp.types.legacy.LegacyCreative` | `AttributeError` | **no replacement.** A legacy-compatibility class is a hand-written layer by definition and no document states one |
| `adcp.canonical_formats.V1Tracker` | `AttributeError` | **no replacement**; `canonical_formats` is machinery (§1) |
| `adcp.server.responses.creative_formats_response` | `AttributeError` | **no replacement**; `server` is machinery (§1) |
| `adcp.types._generated.Product1` | `AttributeError` | a private module's structurally-numbered name. The product subject is `core/product.json` → `adcp.types.core.Product`, and §5 is about what that rename does and does not carry |
| `adcp.types.domains.core.product.PublisherProperties4` | `AttributeError` | same: a structurally-numbered inner name of upstream's generated tree, absent from the wheel it is spelled against |
| `adcp.types.generated_poc.bundled.creative.build_creative_response.Assets9` | `ModuleNotFoundError`: no module `adcp.types.generated_poc.bundled.creative` | **no replacement**, and the module the import names does not exist upstream either |
| `adcp.discovery.PropertyCrawler`, `adcp.discovery.get_property_index` | `ModuleNotFoundError`: no module `adcp.discovery` | **no replacement.** `adcp.discovery` is a module upstream's own documentation imports from and its wheel does not ship |

**The `FormatCategory` row is the one worth reading twice**, because it is a chain: upstream's
migration note sends a reader to `adcp.types.FormatId`, and that name raises an
`AttributeError` on the same wheel. `FormatCategory` has no document and no replacement;
`FormatId` has one, `core/format-id.json`, and the document deprecates itself. So the chain's
honest end is "read the two documents", and neither half of it is reachable by following the
note.

**Ten of the 23 get a real import path** — `FormatId`, `ImageAsset`, `UrlAsset`,
`BuildCreativeRequest`, `BuildCreativeSuccessResponse`, `PreviewCreativeRequest`,
`ListCreativeFormatsRequest`, `CreateMediaBuySuccess`, `CreateMediaBuyError` and `Product1` —
which is a finding about the documents rather than a favour: each of those subjects is stated
by a bundle document, their wheel does not resolve the name, and this package compiled the
document anyway. **The other 13 have no replacement**, and the reason is given per row.

---

## §3. On the type surface, but not a type: 13 names

**These 13 resolve on upstream's wheel, under `adcp.types`, and are not classes.** Five are
functions, one is a metaclass value, and seven are `typing` aliases — which matters, because
`typing.Annotated[A | B, Field(discriminator=…)]` is not something an application can
subclass, `isinstance`-check, or give a schema reference to. Reading 3 makes a union of ours
a **root class that dispatches**, so where upstream has an alias we have a class, and that
is a real destination and not a near-miss.

**The seven aliases, with a destination:**

| upstream | what it is | this package |
|---|---|---|
| `adcp.types.AccountReference` | a `UnionType` (`A \| B`) | **`adcp.types.core.AccountReference`**, a dispatching root from `core/account-ref.json` |
| `adcp.types.ListProductsResponse` | an `Annotated` union | **`adcp.types.media_buy.ListProductsResponse`**, from `media-buy/list-products-response.json` |
| `adcp.types.signals.SignalTargeting` | an `Annotated` union, defined by `adcp.types._eager` | **`adcp.types.core.SignalTargeting`**, from `core/signal-targeting.json` |
| `adcp.types.VendorPricingOption` | an `Annotated` union over `VendorPricingOption7`…`11` | **`adcp.types.core.VendorPricingOption`**, from `core/vendor-pricing-option.json` |
| `adcp.types.VendorPricingOptionUnion` | **the same object** — `VendorPricingOption is VendorPricingOptionUnion` is `True` on their wheel | the same destination, `adcp.types.core.VendorPricingOption`. One object at two spellings is the multiplicity reading 6 forbids reproducing, so this package has one name |
| `adcp.WholesaleFeedEvent` | an `Annotated` union of nine branches | **`adcp.types.core.WholesaleFeedEvent`**, from `core/wholesale-feed-event.json` |
| `adcp.types.CanonicalFormatKindStr` | `Annotated[str, AfterValidator(require_canonical_format_kind)]` | **no replacement for the wrapper.** The documents make a `format_kind` a `str` and this package keeps it one; the enumeration of the kinds the pinned bundle declares is **`adcp.types.core.CanonicalFormatKind`**, and a model field is not annotated with it |

**The five functions and the one metaclass value — no replacement, and the reason is the
same for all six:** a function is behaviour, and a schema document states no behaviour, so
there is no node to derive one from.

| upstream | what it does | instead |
|---|---|---|
| `adcp.types.is_canonical_format_kind` | tests a value against a vocabulary (default: the sixteen kinds of the pin) | **no replacement.** Compare against `adcp.types.core.CanonicalFormatKind` yourself — and note upstream's own docstring says the set that matters is the seller's, not the library's |
| `adcp.types.require_canonical_format_kind` | the raising form of the above | **no replacement**, same answer |
| `adcp.types.validate_union` | dispatches a payload across a union by hand | **no replacement, and none is needed**: reading 3 makes every union of ours a root that dispatches, so `Root.strict_validate(payload)` is the operation |
| `adcp.types.guards.is_adcp_success` | a `TypeGuard` over upstream's response wrapper | **no replacement.** It guards `adcp.types.core.TaskResult`, which is itself nodeless — §4 |
| `adcp.types.legacy.coerce_legacy_assets` | rewrites pre-3.x asset payloads | **no replacement.** A migration of wire data is not a type |
| `adcp.types.SchemaVariant` | a metaclass-backed selector for which bundle version's classes to use | **no replacement.** This package compiles **one** bundle, named on every class by `__adcp_schema__`, and a wheel is the artifact (reading 8) — the version is the wheel's, not a runtime switch |

---

## §4. On the type surface, with no schema subject: 8 names

**Each of these eight is defined by one of upstream's own hand-written layers under
`adcp.types`** — a base layer, a "core type definitions" module, a version-pinned base, the
canonical-creative layer — **so no bundle document states the thing the name denotes, an
alias has nothing to point at, and reading 10 forbids minting a class to satisfy the
import.** Where an identity of ours comes *close*, the overlap is given with its number — as
**evidence a reader checks against the document, not as a destination**. Two rows name a
real import path anyway, for the *subject beside* the nodeless one (the 3.2 request where
upstream pinned 3.1), and one row — `Creative` — is undecided rather than absent, for the
reason its entry gives.

| upstream | what it is | instead |
|---|---|---|
| `adcp.types.base.AdCPBaseModel` | their Pydantic base, carrying serialization behaviour | **no replacement you import.** Every model here already serializes by the document; there is a base in this tree and reading 6 keeps it private, so it is not part of the surface |
| `adcp.types.base.AdcpRequest` | a marker base for request models | **no replacement.** No document states a "request" supertype; the request documents are each compiled to their own class |
| `adcp.types.base.AdcpResponse` | a marker base for response models | **no replacement**, same reason. `adcp.types.envelopes` carries what the response *documents* state, which is not the same thing as a marker |
| `adcp.types.core.AgentConfig` | an agent's URI, auth and timeout settings — client configuration | **no replacement.** Configuration is the client's, and the client is machinery (§1). Nearest identity of ours: 0.08 agreement, which is noise |
| `adcp.types.core.TaskResult` | their task-execution result wrapper: `success`, `error`, `needs_input`, `data`, `metadata`, `replayed` | **no replacement.** This is a transport's result object. The schema states per-task *response* documents, and those are what this package compiles. Nearest identity of ours: 0.25, against an unrelated compliance class |
| `adcp.types.canonical_creative.Creative` (spelled `adcp.Creative`) | a hand-written creative class with 28 fields | **undecidable as an import today, and the honest answer is a pointer rather than a path.** The nearest identity of ours agrees **0.96** and is `adcp.types._schemas.creative.list_creatives_response.CreativesItem`, from `creative/list-creatives-response.json` — a class this package *has* and reading 6 does not export, because it is an inner declaration rather than a document root. Whether it gets an export is `adcp-client-python-2m5.2`'s decision, which is the thing that would turn this row into a path |
| `adcp.types.versioned_bases.v31.ListCreativesRequestBase` | the request as AdCP 3.1 stated it, pinned | **no replacement for the pin.** The 3.2 request is **`adcp.types.creative.ListCreativesRequest`** from `creative/list-creatives-request.json`, and the identities agree **0.89** — the difference is the version, which is the wheel's and not a class's |
| `adcp.types.versioned_bases.v31.PackageRequestBase` | the 3.1 package request, pinned | same: **`adcp.types.media_buy.PackageRequest`** from `media-buy/package-request.json`, identities agreeing **0.84**. No replacement for the pinned base itself |

---

## §5. Where upstream's name means something else: 7 names

**An alias here would be worse than an import error.** Reading 10: it "hands a caller
something that silently is not what it asked for". So each of these takes a note giving
**both sets**, and the destination — where there is one — is named with what it does and
does not carry.

### `TaskStatus` — the case the rule is written from

`adcp.types.core.TaskStatus` is a transport's **five** states. The bundle's
`enums/task-status.json` states **nine**. They are not the same enumeration and neither
contains the other.

| | values |
|---|---|
| upstream's `adcp.types.core.TaskStatus` | `completed` · `failed` · `needs_input` · `submitted` · `working` |
| the document, `enums/task-status.json` → **`adcp.types.enums.TaskStatus`** | `submitted` · `working` · `input-required` · `completed` · `canceled` · `failed` · `rejected` · `auth-required` · `unknown` |

Agreement: **0.40**. `needs_input` is upstream's spelling of the document's
`input-required`; `canceled`, `rejected`, `auth-required` and `unknown` have no counterpart
in their five. **So `from adcp.types.core import TaskStatus` has no drop-in here, and an
application that compares `status == TaskStatus.needs_input` must be ported by reading the
document, not by renaming an import.** Upstream's own generated enumeration for the same
document — `adcp.types.GeneratedTaskStatus`, nine values — *does* match ours exactly, and is
in §7 rather than here.

### The `canonical_creative` layer — five names that share a word with a document

Upstream's `adcp.types.canonical_creative` is a hand-written layer, and in UPSTREAM's package
`adcp.Product`, `adcp.Package`, `adcp.CreativeManifest`, `adcp.Format` and
`adcp.types.ProductFormatDeclaration` all resolve into it. **All five have a class of ours
carrying the same word, and only three of the five are a rename** — the field sets below are
what tells them apart, which is the whole reason the word is not allowed to decide.

**THAT LAYER IS NOT IN THIS PACKAGE** (`adcp-client-python-2f52`). It was restored here for a
while, at upstream's own path and bytes; it is deleted, because 32 of its 36 classes subclass
an emitted class of ours and then SUPPRESS a field the class's own document states —
`Product.format_ids` was a class attribute holding `None`, hiding the inherited field, and
`core/product.json` states `format_ids` with `deprecated: true` and `x-removed-in: 4.0.0`.
`deprecated` is metadata, not absence. So in THIS package the flat words resolve to the
documents' own classes, which is what the table below tells you to port to:

| flat word | resolves here to |
|---|---|
| `adcp.Product` | `core/product.json`'s root — `format_ids` present |
| `adcp.Package` | `core/package.json`'s root — `format_ids`, `format_ids_pending`, `format_ids_to_provide` present |
| `adcp.Placement` | `core/placement.json`'s root — `format_ids` present |
| `adcp.ProductFilters`, `adcp.CreativeFilters` | their own documents' roots — `format_ids` present |
| `adcp.CreativeManifest`, `adcp.CreativeAsset` | their own documents' roots — `format_id` present |
| `adcp.Format` | `core/format.json`'s root, which the bundle marks `deprecated: true` as a whole. **Read the `adcp.Format` row below before porting**: it is the v1 named-format definition and not a canonical declaration, and which subject the flat word SHOULD denote is `adcp-client-python`'s Format-union question and is not settled by this removal |
| `adcp.types.ProductFormatDeclaration` | `core/product-format-declaration.json`'s root |
| `adcp.MediaBuyPackage`, `adcp.DeliveryCreative`, `adcp.CreateMediaBuySuccessResponse`, `adcp.UpdateMediaBuySuccessResponse`, `adcp.CreateMediaBuyErrorResponse`, `adcp.is_canonical_format_kind`, `adcp.require_canonical_format_kind`, `adcp.CanonicalFormatKindStr` | **no longer resolve.** Each raises with the reason, recorded by name in `adcp.types._adapter.__adcp_refused__` — reading 10's "a name with no schema subject gets a migration note and never a class" |
| `adcp.Creative` | `protocol/get-adcp-capabilities-response.json`'s inner `Creative`, bound because it is the only declaration of that word in this tree. **Identity `differs` and the row at the top of this section is the one to read**: the nearest identity of upstream's listed creative is `creative/list-creatives-response.json`'s `CreativesItem` at 0.96, which this package has and does not export |

Three functions and a base class went with the file and are not re-expressed anywhere:
`strip_legacy_creative_identity` (a dict walk that deleted `format_id`/`format_ids` keys),
`sanitize_canonical_schema` (the same deletion over a JSON Schema), and
`CanonicalBoundaryModel` (the base that did both on `model_dump`, `model_dump_json` and
`model_json_schema`). A payload this package serializes now carries the fields its document
states.

| upstream | this package | agreement | the difference, field by field |
|---|---|---|---|
| `adcp.Product` | **`adcp.types.core.Product`** (`core/product.json`) | 0.98 | ours is a **superset**: all 59 of their field names, plus `format_ids`. Port it as a rename and read `format_ids` |
| `adcp.Package` | **`adcp.types.core.Package`** (`core/package.json`) | 0.92 | ours is a superset: their 34, plus `format_ids`, `format_ids_pending`, `format_ids_to_provide` |
| `adcp.CreativeManifest` | **`adcp.types.core.CreativeManifest`** (`core/creative-manifest.json`) | 0.91 | ours is a superset: their 10, plus `format_id` |
| `adcp.types.ProductFormatDeclaration` | **not a rename.** Ours of that name is `core/product-format-declaration.json` and shares 10 of their 12 fields; `format_kind` and `params` are theirs alone, and five fields (`locale_policy`, `sample_render_url`, `technical_requirements_complete`, `tracker_execution_contract`, `v1_format_ref`) are the document's alone | 0.71 at best | Port by reading `core/product-format-declaration.json`. The nearest identities of ours tie at 0.75 between `core/canonical-format-option.json` and `core/creative-operation-format-declaration.json`, and a tie is not a verdict |
| `adcp.Format` | **`adcp.types.core.Format` is a different subject and must not be used as the destination.** Their `Format` carries the same 12 fields as their `ProductFormatDeclaration` — a canonical *declaration*. Ours of that name is `core/format.json`: `format_id`, `assets`, `renders`, `pricing_options`, 20 fields, and **zero** shared with theirs | 0.00 against our `Format` | Read `core/product-format-declaration.json` and `core/canonical-format-option.json` — the two documents whose identities tie at 0.75 — and pick by the fields your code uses. **This is the row where a mechanical rename silently changes the subject** |

### `ReportingWebhook` — one field upstream carries and the document does not

`adcp.types.domains.core.reporting_webhook.ReportingWebhook` has six fields.
`core/reporting-webhook.json` states five, and this package's
**`adcp.types.core.ReportingWebhook`** has exactly those five. The sixth is upstream's
`operation_id`, which the document does not mention — searched, and the document's
`properties` are `authentication`, `reporting_frequency`, `requested_metrics`, `token`, `url`.
**Destination: `adcp.types.core.ReportingWebhook`. There is no `operation_id` and no node
behind one**, so if your code sets it, it is sending a field the protocol does not define.
Agreement 0.83.

---

## §6. The instrument's undecided seven: four the bundle settles, three it does not

**`survey/migration_notes.py` reports all seven of these as `UNDECIDED`, and this section
settles four of them.** That is not the instrument being wrong: its join is an identity
comparison, and for these seven it had nothing to compare — upstream's object is a union
root, whose field set is `{"root"}` and says nothing about its subject. Reading 10 names what
decides a case like that, and it is not a stronger comparison: **"name the schema node, or
say there isn't one"**, and "every many-to-one target is decided by reading the bundle
first — whether it REFERENCES one node from the others or RESTATES it". So the four below are
decided by reading the bundle, and the three after them are left undecided with the thing
that would decide each.

**Four, decided by the document and not by the word.** Each pair's defining module on
upstream's wheel is named for a bundle document, this package compiles that same document,
and the destination is the declaration that document states — a subject match, which is the
key reading 10 allows, rather than a shared word, which is not.

| upstream | the document both sides name | this package |
|---|---|---|
| `adcp.types.AcceptancePolicyProfileIds` | `core/acceptance-policy-profile-ids.json` | **`adcp.types.core.AcceptancePolicyProfileIDs`** — the only declaration that document states. The acronym is cased differently and that is the whole difference |
| `adcp.ContextObject` | `core/context.json` | **`adcp.types.core.ContextObject`** — one declaration, same name |
| `adcp.PropertyTag` | `core/property-tag.json` | **`adcp.types.core.PropertyTag`** — one declaration, same name |
| `adcp.decisioning.capabilities.Features` | `protocol/get-adcp-capabilities-response.json` **references** `core/media-buy-features.json` — at `/properties/media_buy/properties/features/allOf/0`, read off the document, and the other four `allOf` branches are `if`/`then` conditions that declare no property | **`adcp.types.core.MediaBuyFeatures`**, from `core/media-buy-features.json`. A reference and not a restatement, so this is one subject and the destination is a rename. **With one finding attached**: upstream's class has 11 fields and the document states 10 — the extra is `canonical_creatives`, which appears in neither `core/media-buy-features.json` nor the bundled capabilities document, so no node in the pinned bundle states it. Identity agreement 0.91, and that missing 0.09 is exactly this field |

**Three this guide does not decide**, and the reason is the same for all three: a class of
ours holds the subject, the question is whether a caller needs to spell it, and reading 10
says that answer is "an EXPORT or a NAME — never a split class", which makes it
`adcp-client-python-2m5.2`'s to give and not this document's.

| upstream | the document | what a reader can do today | what would decide it |
|---|---|---|---|
| `adcp.types.GeoCountry` | `core/targeting.json`, whose only exported declaration here is `adcp.types.core.TargetingOverlay` | read the geo fields off `TargetingOverlay` | whether this package's fold of `core/targeting.json` keeps every fact the document states — in which case their `GeoCountry` is redundant — or loses one, which is a reading 1 defect in the walk and outranks this question entirely |
| `adcp.types.error_details.SupportedVersion` | `error-details/version-unsupported.json`, compiled to exactly one exported class, `adcp.types.error_details.VersionUnsupportedDetails` | read the supported versions off that class | whether the folded class is awkward enough for a caller that the inner declaration needs an export |
| `adcp.types.SyncCreativeResult` | `creative/sync-creatives-response.json`, whose exports are `SyncCreativesResponse`, `SyncCreativesSuccess`, `SyncCreativesError` and `SyncCreativesResponseSubmitted` | read the per-creative results off `SyncCreativesSuccess` | the same export decision. The nearest identity of ours agrees **0.88** and is `adcp.types._schemas.creative.sync_creatives_response.CreativesItem`, a class this package has and reading 6 does not export because it is an inner declaration |

**Those three and `Creative` in §4 are one question asked four times**: a class of ours holds
the subject at a private module, because reading 6 exports document roots and union branches
and not inner declarations. They become paths the moment the export decision is taken, and
they are written as pointers until then rather than as paths a reader would type today.

---

## §7. What this guide deliberately does not cover

**85 of the 503 names already have a class of ours holding the same identity**, and they are
not listed here on purpose: an alias for each is `adcp-client-python-82m.7`'s work, and a
migration entry beside it would be a second answer to one question. The rule that layer is
held to is reading 10's — an alias is keyed on a schema subject, never on a name — and the
consequence for a reader of this guide is that **an import spelling absent from §1 to §6 is
one the alias layer is meant to keep working**, not one nobody looked at. To see which 85,
run the instrument: they are the `ALIAS LAYER` bucket of `migration-partition.json`.

**And `GetAdcpCapabilitiesRequest` is in this set, which is the other half of §2's
correction to the README.** It raises at `adcp` and resolves at `adcp.types`, so it is a
raising *pair* and not a raising *name* — the 21st of the README's 21, and the reason §2
counts 20. It is a name upstream still has, a class of ours holds its identity, and the
alias layer is what keeps it working.

---

## §8. Member spellings — the ATTRIBUTE a caller types, not the class

**Every section above is about a NAME an application imports. This one is about an
attribute OF one, and it is the granularity the instrument's identity join cannot reach:**
the join is over a class's field set or an enumeration's value list, and our value lists are
upstream's exactly, so an enumeration whose every member a caller spells differently joins
as a clean match. Measured in the drop-in lane: **3,282 of upstream 9.6.1's own behavioural
tests failed on ONE member** — more than any class name in this guide — and the member was
`Recovery.transient`.

**Our generated members are `UPPER_SNAKE` because that is PYTHON's** — `HTTPStatus.CONTINUE`,
`Signals.SIGHUP`, `AddressFamily.AF_UNSPEC` — **and upstream's are the value pushed through
`datamodel-code-generator`'s identifier sanitiser.** `core/error.json` states the value list
`transient|correctable|terminal` and says nothing about the attribute a caller types, so neither
spelling is the document's. **This package now emits both**, as a class-body line beside the
canonical member:

```python
class Recovery(StrEnum):
    TRANSIENT = 'transient'
    transient = MemberAlias('TRANSIENT')
    ...
```

`Recovery.transient is Recovery.TRANSIENT` — the same object, not a second member.
`len(Recovery.__members__)` is 3, the value set is the document's three strings, and
`Recovery('transient')` works as it always did.

**AND THE SPELLING IS THE SANITISER'S OUTPUT, NOT THE VALUE VERBATIM — which is the one line
of this section that USED TO SEND A CALLER TO REWRITE A LINE THAT WORKS.** Where the value is
already an identifier the two coincide and the distinction is invisible. Where it is not,
upstream does not refuse it: it replaces every character outside `[0-9A-Za-z_]` with `_`,
suffixes a python keyword with `_`, and prefixes `field_` to anything that cannot begin an
identifier. So

```python
AdCPProtocol.media_buy      # upstream — and HERE, from enums/adcp-protocol.json's 'media-buy'
Background.dark_bg          # upstream — and HERE, from brand.json's 'dark-bg'
VastVersion.field_1_0       # upstream — and HERE, from '1.0'
BinaryVerdict.pass_         # upstream — and HERE, from 'pass', which a class body refuses bare
```

all resolve on this package, each `is` its `UPPER_SNAKE` member. The four clauses are read off
upstream's installed 9.6.1 wheel and reproduce **6,159 of 6,159** of its generated member
attributes, so an attribute named here is one a caller of their package actually writes.

So **for nearly every member this section owes nothing and a port needs no edit**: most member
spellings carry the value verbatim, a further set carry the sanitiser's spelling, and the rest
already ARE it (the derived spelling is itself the `UPPER_SNAKE` name — `Method.GET` and
`AuthenticationScheme.HMAC_SHA256` are the attribute on both packages, so nothing is owed and
nothing changed).

**What IS owed is the spellings the sanitiser cannot rescue, plus 2 at one node.** Each is a
real edit for a caller who typed upstream's spelling, and each has one of three reasons:

| reason | what to write instead |
|---|---|
| `no python identifier derives from the value` | the `UPPER_SNAKE` member, or the constructor |
| `a name the enumeration already resolves` | the `UPPER_SNAKE` member, or the constructor |
| `two values sanitise onto one attribute` | the string — there is no class |
| `already the canonical member name` | **nothing — unchanged** |

**`no python identifier derives from the value` — the INTEGER members, and nothing else.** A
non-string value has no attribute spelling at all on either package: upstream's generator
names such a member from the value too, and an integer cannot begin an identifier. Reading 10
names a leading digit, the empty string and pure punctuation in this class as well; the
derivation read off upstream's wheel says they are *not* in it, because `field_` rescues all
three (`'1.0'` → `field_1_0`, `'3d_render'` → `field_3d_render`), and this document records
that disagreement rather than repeating the clause.

**`a name the enumeration already resolves` — the one place this package deliberately does
NOT follow upstream's derivation.** The derived spelling is a name the enumeration already has
before any member is declared: `name`, `value`, `count`, `index`, `format`, `title`, `split`,
`center`, `capitalize`. The first two are `enum.Enum`'s own `name` and `value` descriptors, and
upstream's wheel does bind over them — `name = 'name'` appears in eight of its generated
classes — which makes `Kind.NAME.name` return the member instead of `'NAME'`: the enum protocol
broken on a class whose document says nothing about python attributes. The rest are `str`
methods a member inherits. This package refuses the spelling instead, so

```python
Kind.name                   # upstream
Kind.NAME                   # here — or Kind('name')
```

**`two values sanitise onto one attribute` — 2 spellings, at one node, and there is no
class to spell them on.** `formats/canonical/html5.json#/properties/clicktag_macro` states
`["clickTag", "clickTAG"]`, which our `UPPER_SNAKE` naming maps onto one attribute —
`CLICKTAG` for both. The row renders a `Literal['clickTag', 'clickTAG']` and no enumeration,
so this is the one place a port loses the member object as well as the spelling: the field
holds and accepts the plain strings, and both values are carried exactly as the document
writes them.

```python
ClickTagMacro.clickTag      # upstream
"clickTag"                  # here — the field is Literal['clickTag', 'clickTAG']
```

**Both tables are DERIVED and gated.** The reasons are
`codegen.lower.enum.member_aliases` over the tree a fresh run emits, and
`tests/test_the_member_spelling_is_emitted.py` partitions every member spelling across the
four reasons and the two emitted halves — verbatim and sanitised — requires this section to
name three of them in the compiler's own words, and reddens if a fifth reason is added to the
compiler and not to this document. The live counts are in
`adcp-client-python-tuuc`, not here: a figure in a porting guide goes stale on the next bundle
and a stale figure gets believed.

---

## §9. Provisional words — an alias that RECORDS upstream's spelling of an untitled node

**Every name in this section is PROVISIONAL and an application should expect to stop using
it.** It is a word upstream's wheel publishes for a node the AdCP bundle gives *no title*,
and the only reason it is bound here at all is that upstream already shipped the commitment.

`docs/plan/final-state.md` reading 10 states both halves:

> **NO ALIAS POINTS AT A NAME THIS COMPILER MINTED FROM STRUCTURE.** … such a name is
> *pending* an upstream title. Publishing an alias onto it makes a placeholder permanent and
> public …
>
> **UNLESS THE ALIAS IS UPSTREAM'S OWN PUBLISHED WORD, DECLARED DEPRECATED AND PENDING.**
> Where upstream's wheel already ships that spelling, the commitment exists and is theirs;
> an alias **records** it rather than minting it … So the alias is admissible **and the
> migration entry must say the word is PROVISIONAL** — naming the untitled node by pointer
> and the upstream ask that would title it.

**AND THE EXPORT CAME FIRST, which is reading 6's clause of 2026-11-07.** Until that clause
landed the class behind each of these words was declared privately and reachable at no public
path at all, so the alias had nothing to bind: "an EXPORT or a NAME, never a split. The alias
layer cannot reach a private name." Reading 6 now exports **an untitled inner node under its
parent's name and its key, always** — read transitively, the node's whole chain through the
document — so each word below has a surface name of ours to record itself onto. **That word
of ours is itself pending the same upstream title**; it is derived from the document's own
path and is stable under the bundle's growth, which is the property a placeholder needs, but
it is not a name the protocol chose.

| upstream's word | the untitled node | our surface name | the ask that would retire both |
|---|---|---|---|
| `PixelTrackerMethod` | `core/assets/pixel-tracker-asset.json#/properties/method` | `adcp.types.core.PixelTrackerAssetMethod` | give the enumeration at that pointer a `title` — upstream's own generator derives `PixelTrackerMethod` from the parent and the key exactly as this package does, so neither side is choosing the word and only the bundle can settle it |

```python
from adcp.types import PixelTrackerMethod          # upstream's word — PROVISIONAL
from adcp.types.core import PixelTrackerAssetMethod  # ours — also pending the title

PixelTrackerMethod is PixelTrackerAssetMethod       # True: one object, two names
```

**THE PAIR IS THE UNIT AND NEITHER HALF IS ADMISSIBLE ALONE.** The alias is declared in
`src/adcp/types/compat.py`'s `__adcp_provisional__`, which maps each word to the pointer
above, and `tests/test_the_alias_layer_is_names.py::test_every_provisional_alias_is_paired_with_its_migration_entry`
requires every entry of that mapping to appear here with its pointer and the word
`PROVISIONAL`. An alias added without an entry is a red run, not an undocumented name.

**WHAT IS NOT HERE YET, measured.** Reading 6's clause puts **1,343 inner words** on the
domain surface, and the set of upstream spellings that are now recordable against one of
them is larger than this table: **58 names** of the drop-in census (`survey/dropin_blocking.py`
on `dropin/9.6-b`) and at least **26** of upstream's flat `adcp.types.__all__` have a class
of ours at the right node and a word of ours that differs from upstream's. Deciding each of
those is the alias layer's own re-derivation — `survey/alias_surface.py`, whose committed
table was built when those rows were invisible to its join — and it is tracked rather than
guessed at here.

---

<!-- GENERATED by survey/mechanical_aliases.py -- do not edit between the fences -->

## §10. The mechanical 1:1 structural aliases

**Every row below is a PAIR, and the pair is the unit** — `docs/plan/final-state.md` reading
10: "an alias whose entry is missing is a reading 10 FAILURE and not partial credit, because
an undisclosed substitution is the exact defect this reading refused, arriving with our name
on it instead of theirs."

**WHAT MAKES THESE ROWS MECHANICAL IS THAT NOTHING WAS DECIDED.**
`survey/structural_signature.py` compares the two sides by the class's own **resolved JSON
schema** — the wire names, the optionality, the defaults, the discriminators and the
constraint keywords, canonicalised by the normalisations that file states with its reason for
each. A row is here only when the two schemas are **EQUAL**. Reading 10's "the split is
proved PER ELEMENT, never by a ratio" is the rule for identities that *differ*; here no
element differs, so there is no element to argue and no judgment was exercised. A reader who
distrusts a row distrusts a normalisation, and every one of them is named in
`survey/mechanical-9.6.1.tsv`'s own header.

**452 pairs**, from the 738 1:1 declarations the instrument
found against upstream 9.6.1 — the remainder of that bucket already resolved flat
(230 names) or is withheld for a reason stated below.

**27 rows are plain and 425 are PROVISIONAL**, and the difference
is whose word *ours* is. Upstream's word, on the left, is always theirs — that is what makes
the narrowed clause apply at all. Where the bundle **titles** our word the row is plain; where
it titles nothing at that node our word is derived from the parent and the key, so the alias
*records* upstream's commitment rather than minting one and **the row says PROVISIONAL**. The
upstream ask is the same sentence in every provisional row and is stated once here rather than
425 times: **give the node at that pointer a `title`.** Upstream's generator
derives its word from the parent and the key exactly as this package does, so neither side is
choosing it and only the bundle can settle it.

| upstream's word | our surface name | the node the document states it at | status |
|---|---|---|---|
| `A2UiBoundValue1` | `adcp.types.a2ui.A2UIBoundValueLiteralString` | `a2ui/bound-value.json#/oneOf/0` | PROVISIONAL |
| `A2UiBoundValue2` | `adcp.types.a2ui.A2UIBoundValueLiteralNumber` | `a2ui/bound-value.json#/oneOf/1` | PROVISIONAL |
| `A2UiBoundValue3` | `adcp.types.a2ui.A2UIBoundValueLiteralBoolean` | `a2ui/bound-value.json#/oneOf/2` | PROVISIONAL |
| `A2UiBoundValue4` | `adcp.types.a2ui.A2UIBoundValuePath` | `a2ui/bound-value.json#/oneOf/3` | PROVISIONAL |
| `A2UiBoundValue5` | `adcp.types.a2ui.A2UIBoundValueLiteralStringPath` | `a2ui/bound-value.json#/oneOf/4` | PROVISIONAL |
| `AccountSelection` | `adcp.types.core.AccountTimezoneCapabilityAccountSelection` | `—` | PROVISIONAL |
| `Action3` | `adcp.types.core.CanonicalMediaBuyActionRefineProposalsAction` | `—` | PROVISIONAL |
| `Action33` | `adcp.types.protocol.ValidatedPrincipalDryRunAction` | `—` | PROVISIONAL |
| `Action4` | `adcp.types.core.CanonicalMediaBuyActionSyncCreativesAction` | `—` | PROVISIONAL |
| `ActionResponse` | `adcp.types.sponsored_intelligence.SISendMessageRequestActionResponse` | `sponsored-intelligence/si-send-message-request.json#/properties/action_response` | PROVISIONAL |
| `ActivationStatus` | `adcp.types.core.ProductSignalTargetingOptionActivationStatus` | `—` | PROVISIONAL |
| `Actor` | `adcp.types.core.AccountChangeActor` | `core/account-change.json#/properties/actor` | PROVISIONAL |
| `AdcpAgentsAuthorization1` | `adcp.types.adagents.AdCPAgentsAuthorizationAuthoritativeLocation` | `adagents.json#/oneOf/0` | PROVISIONAL |
| `Adjustment` | `adcp.types.pricing_options.PriceBreakdownAdjustmentsItem` | `pricing-options/price-breakdown.json#/properties/adjustments/items` | PROVISIONAL |
| `AdjustmentMagnitudeItem` | `adcp.types.core.ReportingReliabilityStatisticsAdjustmentMagnitudeItem` | `core/reporting-reliability-statistics.json#/properties/adjustment_magnitude/items` | PROVISIONAL |
| `AdvanceTo` | `adcp.types.compliance.ComplyTestControllerRequestParamsAdvanceTo` | `—` | PROVISIONAL |
| `AffectedEntityType` | `adcp.types.core.WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadAffectedEntityType` | `—` | PROVISIONAL |
| `Aggregation` | `adcp.types.core.ReportingReportDefinitionMetricsItemAggregation` | `—` | PROVISIONAL |
| `AiActRiskClass` | `adcp.types.core.SignalDefinitionModelingAiActRiskClass` | `—` | PROVISIONAL |
| `Allocations` | `adcp.types.governance.SyncPlansRequestPlansItemBudgetAllocationsValue` | `governance/sync-plans-request.json#/properties/plans/items/properties/budget/properties/allocations/additionalProperties` | PROVISIONAL |
| `AllowedStatus` | `adcp.types.media_buy.MediaBuyChangeTermAllowedStatusesItem` | `—` | PROVISIONAL |
| `Alternatives` | `adcp.types.media_buy.ProposalRefinementAlternatives` | `media-buy/proposal-refinement.json#/properties/alternatives` | PROVISIONAL |
| `AnimationSpeed` | `adcp.types.brand.BrandDiscoveryMotionGuidelinesAnimationSpeed` | `—` | PROVISIONAL |
| `ApprovalStatus` | `adcp.types.core.RightsConstraintApprovalStatus` | `—` | PROVISIONAL |
| `Architecture` | `adcp.types.brand.BrandDiscoveryHouseArchitecture` | `—` | PROVISIONAL |
| `Art9Basis` | `adcp.types.core.SignalDefinitionArt9Basis` | `—` | PROVISIONAL |
| `ArtifactRef` | `adcp.types.trusted_match.ContextMatchRequestArtifactRefsItem` | `trusted-match/context-match-request.json#/properties/artifact_refs/items` | PROVISIONAL |
| `AssetSource` | `adcp.types.formats.CanonicalFormatHostedAudioAssetSource` | `—` | PROVISIONAL |
| `AssetSource5` | `adcp.types.formats.CanonicalFormatNativeInFeedAssetSource` | `—` | PROVISIONAL |
| `Assignment` | `adcp.types.creative.SyncCreativesRequestAssignmentsItem` | `creative/sync-creatives-request.json#/properties/assignments/items` | PROVISIONAL |
| `AssignmentProjection` | `adcp.types.creative.ListCreativesRequestAssignmentProjection` | `—` | PROVISIONAL |
| `AttestationMode` | `adcp.types.compliance.UpstreamTrafficSuccessRecordedCallsItemAttestationMode` | `—` | PROVISIONAL |
| `Audience` | `adcp.types.core.SignalModelingDisclosureJurisdictionsItemAudience` | `—` | PROVISIONAL |
| `AudienceScope` | `adcp.types.core.SignalDefinitionAudienceScope` | `—` | PROVISIONAL |
| `AudienceSource` | `adcp.types.enums.AudienceSource` | `—` | TITLED |
| `AudienceType` | `adcp.types.media_buy.SyncAudiencesRequestAudiencesItemAudienceType` | `—` | PROVISIONAL |
| `AudioCodec` | `adcp.types.core.VideoAssetRequirementsAudioCodecsItem` | `—` | PROVISIONAL |
| `AudioCodec2` | `adcp.types.formats.CanonicalFormatHostedAudioAudioCodecsItem` | `—` | PROVISIONAL |
| `Auth` | `adcp.types.core.GeographicPlaceResolverAuth` | `—` | PROVISIONAL |
| `AuthoritativeParty` | `adcp.types.core.ReportingDeliveryConfigurationAuthoritativeParty` | `—` | PROVISIONAL |
| `AuthorizationSummary` | `adcp.types.property.ValidatePropertyDeliveryResponseAuthorizationSummary` | `property/validate-property-delivery-response.json#/properties/authorization_summary` | PROVISIONAL |
| `AvailabilityHorizon` | `adcp.types.core.ProductOfferFiltersAvailabilityHorizon` | `core/product-offer-filters.json#/properties/availability_horizon` | PROVISIONAL |
| `AvailableReportingFrequency` | `adcp.types.enums.ReportingFrequency` | `—` | TITLED |
| `Axis` | `adcp.types.core.PrincipalDeclarationsStateExclusionsItemAxis` | `—` | PROVISIONAL |
| `BackgroundContrast` | `adcp.types.brand.BrandDiscoveryLogoPlacementBackgroundContrast` | `—` | PROVISIONAL |
| `Backgrounds` | `adcp.types.brand.BrandDiscoveryCompositionRulesBackgrounds` | `brand.json#/definitions/composition_rules/properties/backgrounds` | PROVISIONAL |
| `Bank` | `adcp.types.core.BusinessEntityBank` | `core/business-entity.json#/properties/bank` | PROVISIONAL |
| `Baseline` | `adcp.types.governance.CheckGovernanceRequestDeliveryMetricsAudienceDistributionBaseline` | `—` | PROVISIONAL |
| `Basis` | `adcp.types.core.ReportingReliabilityStatisticsEvidenceBasis` | `—` | PROVISIONAL |
| `BatchFrequency` | `adcp.types.media_buy.CreateMediaBuyRequestArtifactWebhookBatchFrequency` | `—` | PROVISIONAL |
| `BitDepth` | `adcp.types.core.VideoAssetAudioBitDepth` | `—` | PROVISIONAL |
| `Bleed` | `adcp.types.core.BleedUniform` | `core/requirements/image-asset-requirements.json#/properties/bleed/oneOf/0` | PROVISIONAL |
| `Bleed1` | `adcp.types.core.BleedBottomLeftRightTop` | `core/requirements/image-asset-requirements.json#/properties/bleed/oneOf/1` | PROVISIONAL |
| `BodyStyle` | `adcp.types.core.VehicleItemBodyStyle` | `—` | PROVISIONAL |
| `BorderRadius` | `adcp.types.brand.BrandDiscoveryBorderRadius` | `brand.json#/definitions/border_radius` | PROVISIONAL |
| `Bounds` | `adcp.types.core.OverlayBounds` | `core/overlay.json#/properties/bounds` | PROVISIONAL |
| `BrandAgent` | `adcp.types.brand.BrandDiscoveryBrandAgent` | `brand.json#/definitions/brand_agent` | PROVISIONAL |
| `BrandAgentEntry` | `adcp.types.brand.BrandDiscoveryBrandAgentEntry` | `brand.json#/definitions/brand_agent_entry` | PROVISIONAL |
| `BrandDiscovery1` | `adcp.types.brand.AuthoritativeLocationRedirect` | `brand.json#/oneOf/0` | TITLED |
| `BrandDiscovery2` | `adcp.types.brand.HouseRedirect` | `brand.json#/oneOf/1` | TITLED |
| `BrandDiscovery3` | `adcp.types.brand.BrandAgent` | `brand.json#/oneOf/2` | TITLED |
| `BrandShapes` | `adcp.types.brand.BrandDiscoveryBrandShapes` | `brand.json#/definitions/brand_shapes` | PROVISIONAL |
| `BucketSemantics` | `adcp.types.core.SignalCoverageForecastBucketSemantics` | `—` | PROVISIONAL |
| `BudgetCappingTimezoneBasis` | `adcp.types.protocol.GetAdCPCapabilitiesResponseBudgetCappingTimezoneBasis` | `—` | TITLED |
| `BuyerReason` | `adcp.types.core.ErrorBuyerReason` | `core/error.json#/properties/buyer_reason` | PROVISIONAL |
| `ByActionSourceItem` | `adcp.types.core.DeliveryMetricsByActionSourceItem` | `core/delivery-metrics.json#/properties/by_action_source/items` | PROVISIONAL |
| `ByEventTypeItem` | `adcp.types.core.DeliveryMetricsByEventTypeItem` | `core/delivery-metrics.json#/properties/by_event_type/items` | PROVISIONAL |
| `CAEnum` | `adcp.types.core.PostalCountrySystemCASystem` | `—` | PROVISIONAL |
| `Calendar` | `adcp.types.core.ReportingReportDefinitionCalendar` | `core/reporting-report-definition.json#/properties/calendar` | PROVISIONAL |
| `CancellationFee` | `adcp.types.core.CancellationPolicyCancellationFee` | `core/cancellation-policy.json#/properties/cancellation_fee` | PROVISIONAL |
| `CancellationTerms` | `adcp.types.media_buy.CommercialTermsCancellationTerms` | `media-buy/commercial-terms.json#/properties/cancellation_terms` | PROVISIONAL |
| `CanonicalAssetSource` | `adcp.types.formats.CanonicalFormatHostedAudioAssetSource` | `—` | PROVISIONAL |
| `CanonicalCompositionModel` | `adcp.types.formats.CanonicalFormatBaseCompositionModel` | `—` | PROVISIONAL |
| `Capability` | `adcp.types.enums.CreativeAgentCapability` | `—` | TITLED |
| `CapabilityReportingDeliveryMethod` | `adcp.types.protocol.GetAdCPCapabilitiesResponseCapabilityReportingDeliveryMethod` | `—` | TITLED |
| `ChannelAllocation` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemChannelAllocationValue` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/channel_allocation/additionalProperties` | PROVISIONAL |
| `Channels` | `adcp.types.governance.SyncPlansRequestPlansItemChannels` | `governance/sync-plans-request.json#/properties/plans/items/properties/channels` | PROVISIONAL |
| `Claim2` | `adcp.types.brand.VerifyPropertyClaimClaim` | `brand/verify-brand-claim-request.json#/oneOf/2/properties/claim` | PROVISIONAL |
| `Claim3` | `adcp.types.brand.VerifyTrademarkClaimClaim` | `brand/verify-brand-claim-request.json#/oneOf/3/properties/claim` | PROVISIONAL |
| `ClaimedValue` | `adcp.types.creative.CreativeAuditObservationDetailsClaimedValue` | `creative/audit-observation.json#/properties/details/properties/claimed_value` | PROVISIONAL |
| `Classification` | `adcp.types.core.RegistryEventClassification` | `—` | PROVISIONAL |
| `ClassificationSource` | `adcp.types.governance.ReportedOutcomeErrorClassificationSource` | `—` | PROVISIONAL |
| `CloseReason` | `adcp.types.core.OpportunityContextCloseReason` | `—` | PROVISIONAL |
| `Codes` | `adcp.types.error_details.VendorErrorCodeRegistryVendorsValueCodesValue` | `error-details/vendor-error-codes.json#/properties/vendors/additionalProperties/properties/codes/additionalProperties` | PROVISIONAL |
| `CollectionIdentifier` | `adcp.types.core.RegistryEventCollectionIdentifier` | `core/registry-event.json#/$defs/collectionIdentifier` | PROVISIONAL |
| `ColorGuide` | `adcp.types.brand.BrandDiscoveryAssetLibraryColorGuide` | `brand.json#/definitions/asset_library/properties/color_guide` | PROVISIONAL |
| `ColorTemperature` | `adcp.types.brand.BrandDiscoveryPhotographyStyleColorTemperature` | `—` | PROVISIONAL |
| `Colors` | `adcp.types.brand.BrandDiscoveryColors` | `brand.json#/definitions/colors` | PROVISIONAL |
| `Colorway` | `adcp.types.brand.BrandDiscoveryColorway` | `brand.json#/definitions/colorway` | PROVISIONAL |
| `Component` | `adcp.types.a2ui.SIComponentCatalogComponentsItem` | `—` | PROVISIONAL |
| `CompositionModel` | `adcp.types.formats.CanonicalFormatBaseCompositionModel` | `—` | PROVISIONAL |
| `CompositionRules` | `adcp.types.brand.BrandDiscoveryCompositionRules` | `brand.json#/definitions/composition_rules` | PROVISIONAL |
| `Compression` | `adcp.types.core.AccountReportingBucketCompression` | `—` | PROVISIONAL |
| `ConfidenceInterval` | `adcp.types.core.PerformanceFeedbackAssertionEvidenceConfidenceInterval` | `core/performance-feedback-assertion.json#/properties/evidence/properties/confidence_interval` | PROVISIONAL |
| `ConnectionType` | `adcp.types.core.DownstreamConnectionRequirementConnectionType` | `—` | PROVISIONAL |
| `Consent` | `adcp.types.trusted_match.IdentityMatchRequestConsent` | `trusted-match/identity-match-request.json#/properties/consent` | PROVISIONAL |
| `ConsentScopeEnum` | `adcp.types.sponsored_intelligence.SIIdentityConsentScopeItem` | `—` | PROVISIONAL |
| `Constraint` | `adcp.types.core.CanvasConstraintConstraint` | `—` | PROVISIONAL |
| `ConsumerIdentity` | `adcp.types.core.DatasetQueryConsumerIdentitiesItem` | `core/audience-activation-method.json#/oneOf/3/properties/consumer_identities/items` | PROVISIONAL |
| `ConsumerStatus` | `adcp.types.core.ReportingConsumerStatusConsumerStatus` | `—` | PROVISIONAL |
| `Contact1` | `adcp.types.brand.BrandDiscoveryBrandContact` | `brand.json#/definitions/brand/properties/contact` | PROVISIONAL |
| `Content` | `adcp.types.core.EventCustomDataContentsItem` | `core/event-custom-data.json#/properties/contents/items` | PROVISIONAL |
| `ContentFormat` | `adcp.types.content_standards.ArtifactAssetsItemTextContentFormat` | `—` | PROVISIONAL |
| `ContextForCheckout` | `adcp.types.sponsored_intelligence.SISendMessageResponseHandoffContextForCheckout` | `sponsored-intelligence/si-send-message-response.json#/properties/handoff/properties/context_for_checkout` | PROVISIONAL |
| `ConversionTracking` | `adcp.types.core.ProductConversionTracking` | `core/product.json#/properties/conversion_tracking` | PROVISIONAL |
| `CoreGovernanceAgent` | `adcp.types.core.AccountGovernanceAgentsItem` | `core/account.json#/properties/governance_agents/items` | PROVISIONAL |
| `CornerStyle` | `adcp.types.brand.BrandDiscoveryIconographyCornerStyle` | `—` | PROVISIONAL |
| `CostPer` | `adcp.types.core.BiddingPolicyCostPer` | `core/bidding-policy.json#/properties/cost_per` | PROVISIONAL |
| `Coverage` | `adcp.types.property.PropertyFeatureDefinitionCoverage` | `property/property-feature-definition.json#/properties/coverage` | PROVISIONAL |
| `CoverageRequirement` | `adcp.types.core.ReportingDeliveryConfigurationCoverageRequirement` | `—` | PROVISIONAL |
| `CoverageStatus` | `adcp.types.property.PropertyFeatureResultCoverageStatus` | `—` | PROVISIONAL |
| `CoversContentDigest` | `adcp.types.protocol.GetAdCPCapabilitiesResponseRequestSigningCoversContentDigest` | `—` | PROVISIONAL |
| `Cpm` | `adcp.types.media_buy.ProposalRefinementConstraintsCpm` | `media-buy/proposal-refinement.json#/properties/constraints/properties/cpm` | PROVISIONAL |
| `CreativeApprovalMode` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyCreativeApprovalMode` | `—` | PROVISIONAL |
| `CreativeSlot` | `adcp.types.core.PlacementPresentationDocumentCreativeSlot` | `core/placement-presentation.json#/properties/creative_slot` | PROVISIONAL |
| `DaastEvent` | `adcp.types.core.DAASTTrackerConstraintsDaastEvent` | `—` | PROVISIONAL |
| `DataSource` | `adcp.types.core.SignalDefinitionDataSourcesItem` | `—` | PROVISIONAL |
| `DataThroughPrecision` | `adcp.types.core.ReportingRevisionDataThroughPrecision` | `—` | PROVISIONAL |
| `Decision` | `adcp.types.governance.ReportPlanAdjustmentRequestDecision` | `—` | PROVISIONAL |
| `DeclaredBy` | `adcp.types.sponsored_intelligence.SISponsoredContextDeclaredBy` | `sponsored-intelligence/si-sponsored-context.json#/properties/declared_by` | PROVISIONAL |
| `DegreeType` | `adcp.types.core.EducationItemDegreeType` | `—` | PROVISIONAL |
| `DeliveryConfigGeneration` | `adcp.types.media_buy.GetReportingStatusResponseScopeDeliveryConfigGenerationsItem` | `media-buy/get-reporting-status-response.json#/properties/scope/properties/delivery_config_generations/items` | PROVISIONAL |
| `DeliveryMode` | `adcp.types.media_buy.CreateMediaBuyRequestArtifactWebhookDeliveryMode` | `—` | PROVISIONAL |
| `DepthOfField` | `adcp.types.brand.BrandDiscoveryPhotographyStyleDepthOfField` | `—` | PROVISIONAL |
| `DerivativeOf` | `adcp.types.core.InstallmentDerivativeOf` | `core/installment.json#/properties/derivative_of` | PROVISIONAL |
| `DestinationMode` | `adcp.types.core.ReportingDeliveryOfferingMethodDestinationModesItem` | `—` | PROVISIONAL |
| `DestinationType` | `adcp.types.core.DestinationItemDestinationType` | `—` | PROVISIONAL |
| `Detail` | `adcp.types.core.EventSourceHealthDetail` | `core/event-source-health.json#/properties/detail` | PROVISIONAL |
| `Disclaimer` | `adcp.types.brand.BrandDiscoveryBrandDisclaimersItem` | `brand.json#/definitions/brand/properties/disclaimers/items` | PROVISIONAL |
| `DisclosureCommitment` | `adcp.types.sponsored_intelligence.SISponsoredContextReceiptHostReceiptDisclosureCommitment` | `sponsored-intelligence/si-sponsored-context-receipt.json#/properties/host_receipt/properties/disclosure_commitment` | PROVISIONAL |
| `DisclosureObligation` | `adcp.types.sponsored_intelligence.SISponsoredContextDisclosureObligation` | `sponsored-intelligence/si-sponsored-context.json#/properties/disclosure_obligation` | PROVISIONAL |
| `DiscriminatorItem` | `adcp.types.core.ErrorIssuesItemDiscriminatorItem` | `core/error.json#/properties/issues/items/properties/discriminator/items` | PROVISIONAL |
| `Disposition` | `adcp.types.media_buy.AcceptancePolicyRuleDisposition` | `—` | PROVISIONAL |
| `DocumentRole` | `adcp.types.error_details.VASTVersionMismatchDetailsDocumentRole` | `—` | PROVISIONAL |
| `DriftMetrics` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemSummaryDriftMetrics` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/summary/properties/drift_metrics` | PROVISIONAL |
| `Effect1` | `adcp.types.core.AccountIdentityChangePreviewNonblockingImpactsItemEffect` | `—` | PROVISIONAL |
| `Elevation` | `adcp.types.brand.BrandDiscoveryElevation` | `brand.json#/definitions/elevation` | PROVISIONAL |
| `EmbeddedProvenanceItem` | `adcp.types.core.ProvenanceEmbeddedProvenanceItem` | `core/provenance.json#/properties/embedded_provenance/items` | PROVISIONAL |
| `EmploymentType` | `adcp.types.core.JobItemEmploymentType` | `—` | PROVISIONAL |
| `Escalation` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemSummaryEscalationsItem` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/summary/properties/escalations/items` | PROVISIONAL |
| `EscalationRateTrend` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsEscalationRateTrend` | `—` | PROVISIONAL |
| `EstimationBasis` | `adcp.types.core.DeliveryMetricsOohMetricsEstimationBasis` | `—` | PROVISIONAL |
| `EvalBudget` | `adcp.types.core.EvaluatorSpecEvalBudget` | `core/evaluator-spec.json#/properties/eval_budget` | PROVISIONAL |
| `ExcludedBy` | `adcp.types.media_buy.GetProductsResponseFilterDiagnosticsExcludedByValue` | `media-buy/get-products-response.json#/properties/filter_diagnostics/properties/excluded_by/additionalProperties` | PROVISIONAL |
| `Exclusion` | `adcp.types.core.PrincipalDeclarationsStateExclusionsItem` | `core/principal-declarations-state.json#/properties/exclusions/items` | PROVISIONAL |
| `ExecutionMode` | `adcp.types.core.DemographicTargetingCapabilityAgeExecutionModesItem` | `—` | PROVISIONAL |
| `Exemplar` | `adcp.types.governance.PolicyEntryExemplar` | `governance/policy-entry.json#/$defs/exemplar` | PROVISIONAL |
| `Exemplars` | `adcp.types.governance.PolicyEntryExemplars` | `governance/policy-entry.json#/properties/exemplars` | PROVISIONAL |
| `ExpandPaginationItem` | `adcp.types.creative.ListTransformersRequestCreativeAgentExpandPaginationItem` | `creative/list-transformers-request.json#/properties/expand_pagination/items` | PROVISIONAL |
| `ExperienceLevel` | `adcp.types.core.JobItemExperienceLevel` | `—` | PROVISIONAL |
| `Facet` | `adcp.types.governance.PolicyCategoryDefinitionFacetsItem` | `governance/policy-category-definition.json#/properties/facets/items` | PROVISIONAL |
| `FailureCode` | `adcp.types.core.ReportingConsumerStatusFailureCode` | `—` | PROVISIONAL |
| `Feature` | `adcp.types.property.ValidationResultFeaturesItem` | `property/validation-result.json#/properties/features/items` | PROVISIONAL |
| `FieldModel` | `adcp.types.core.MacroDeclarationLocationField` | `—` | PROVISIONAL |
| `FieldTruncation` | `adcp.types.core.TruncationSentinelTruncation` | `core/truncation-sentinel.json#/properties/_truncation` | PROVISIONAL |
| `Fields` | `adcp.types.media_buy.FieldsItem` | `—` | PROVISIONAL |
| `FilterDiagnostics` | `adcp.types.media_buy.GetProductsResponseFilterDiagnostics` | `media-buy/get-products-response.json#/properties/filter_diagnostics` | PROVISIONAL |
| `FinalityBasis` | `adcp.types.core.ReportingRevisionFinalityBasis` | `—` | PROVISIONAL |
| `Flight` | `adcp.types.media_buy.ProposalRefinementConstraintsFlight` | `media-buy/proposal-refinement.json#/properties/constraints/properties/flight` | PROVISIONAL |
| `FollowUp` | `adcp.types.sponsored_intelligence.SITerminateSessionResponseFollowUp` | `sponsored-intelligence/si-terminate-session-response.json#/properties/follow_up` | PROVISIONAL |
| `FontFile` | `adcp.types.brand.BrandDiscoveryFontFile` | `brand.json#/definitions/font_file` | PROVISIONAL |
| `Forced` | `adcp.types.compliance.ForcedDirectiveSuccessForced` | `compliance/comply-test-controller-response.json#/oneOf/3/properties/forced` | PROVISIONAL |
| `FormatKind` | `adcp.types.core.CanonicalFormatOptionFormatKind` | `—` | PROVISIONAL |
| `Framing` | `adcp.types.brand.BrandDiscoveryPhotographyStyleFraming` | `brand.json#/definitions/photography_style/properties/framing` | PROVISIONAL |
| `Freshness` | `adcp.types.core.RegistryFeedResponseFreshness` | `core/registry-feed-response.json#/properties/freshness` | PROVISIONAL |
| `From` | `adcp.types.creative.CreativeStatusChangedWebhookTransitionFrom` | `—` | PROVISIONAL |
| `FuelType` | `adcp.types.core.VehicleItemFuelType` | `—` | PROVISIONAL |
| `GBEnum` | `adcp.types.core.PostalCountrySystemGBSystem` | `—` | PROVISIONAL |
| `GeneratedTaskStatus` | `adcp.types.enums.TaskStatus` | `—` | TITLED |
| `GetBrandIdentityField` | `adcp.types.brand.GetBrandIdentityRequestFieldsItem` | `—` | PROVISIONAL |
| `GovernanceAuthentication` | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItemAuthentication` | `account/sync-governance-request.json#/properties/accounts/items/properties/governance_agents/items/properties/authentication` | PROVISIONAL |
| `GovernedAction` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemGovernedActionsItem` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/governed_actions/items` | PROVISIONAL |
| `GradientStyle` | `adcp.types.brand.BrandDiscoveryCompositionRulesOverlaysGradientStyle` | `—` | PROVISIONAL |
| `GrantStatus` | `adcp.types.core.RightsConstraintGrantStatus` | `—` | PROVISIONAL |
| `GraphicElement` | `adcp.types.brand.BrandDiscoveryGraphicElement` | `brand.json#/definitions/graphic_element` | PROVISIONAL |
| `GraphicStyle` | `adcp.types.brand.BrandDiscoveryGraphicStyle` | `brand.json#/definitions/graphic_style` | PROVISIONAL |
| `GuidelineSeverity` | `adcp.types.brand.BrandDiscoveryGuidelineSeverity` | `—` | PROVISIONAL |
| `Handoff` | `adcp.types.sponsored_intelligence.SISendMessageResponseHandoff` | `sponsored-intelligence/si-send-message-response.json#/properties/handoff` | PROVISIONAL |
| `HostReceipt` | `adcp.types.sponsored_intelligence.SISponsoredContextReceiptHostReceipt` | `sponsored-intelligence/si-sponsored-context-receipt.json#/properties/host_receipt` | PROVISIONAL |
| `Iconography` | `adcp.types.brand.BrandDiscoveryIconography` | `brand.json#/definitions/iconography` | PROVISIONAL |
| `IdentifierMatchProof` | `adcp.types.compliance.UpstreamTrafficSuccessRecordedCallsItemIdentifierMatchProofsItem` | `compliance/comply-test-controller-response.json#/oneOf/6/properties/recorded_calls/items/properties/identifier_match_proofs/items` | PROVISIONAL |
| `IdentityUpdates1` | `adcp.types.protocol.AccountIdentityUpdatesUnsupported` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/identity_updates/oneOf/1` | TITLED |
| `ImageFormat1` | `adcp.types.formats.CanonicalFormatNativeInFeedImageFormatsItem` | `—` | PROVISIONAL |
| `ImageRef` | `adcp.types.core.PlacementPresentationDocumentImageDecorationImageRef` | `core/placement-presentation.json#/definitions/image_decoration/properties/image_ref` | PROVISIONAL |
| `Immutability` | `adcp.types.core.ReportingResourceImmutability` | `—` | PROVISIONAL |
| `Impact` | `adcp.types.core.AccountIdentityChangePreviewImpact` | `core/account-identity-change-preview.json#/definitions/impact` | PROVISIONAL |
| `Impressions` | `adcp.types.media_buy.ProposalRefinementConstraintsImpressions` | `media-buy/proposal-refinement.json#/properties/constraints/properties/impressions` | PROVISIONAL |
| `IncompleteItem` | `adcp.types.signals.GetSignalsResponseIncompleteItem` | `signals/get-signals-response.json#/properties/incomplete/items` | PROVISIONAL |
| `IncompleteItem3` | `adcp.types.media_buy.ListProductsResponseIncompleteItem` | `media-buy/list-products-response.json#/properties/incomplete/items` | PROVISIONAL |
| `Issue` | `adcp.types.core.ErrorIssuesItem` | `core/error.json#/properties/issues/items` | PROVISIONAL |
| `IssueState` | `adcp.types.core.ReportingStatusIssueIssueState` | `—` | PROVISIONAL |
| `Issuer` | `adcp.types.governance.PolicyEntryIssuer` | `governance/policy-entry.json#/properties/issuer` | PROVISIONAL |
| `Jurisdiction` | `adcp.types.sponsored_intelligence.SISponsoredContextDisclosureObligationJurisdictionsItem` | `sponsored-intelligence/si-sponsored-context.json#/properties/disclosure_obligation/properties/jurisdictions/items` | PROVISIONAL |
| `KeepMode` | `adcp.types.media_buy.BuildCreativeVariantSuccessKeepModeApplied` | `—` | PROVISIONAL |
| `KeywordTargetsAddItem` | `adcp.types.core.KeywordTarget` | `core/keyword-target.json#` | TITLED |
| `LandingPage` | `adcp.types.enums.LandingPageRequirement` | `—` | TITLED |
| `LatencyPercentiles` | `adcp.types.core.ReportingReliabilityStatisticsLatencyPercentiles` | `core/reporting-reliability-statistics.json#/definitions/LatencyPercentiles` | PROVISIONAL |
| `Layer` | `adcp.types.core.PlacementPresentationDocumentLayer` | `—` | PROVISIONAL |
| `LegacyPostalCodeSystem` | `adcp.types.enums.CountryFusedPostalCodeSystem` | `—` | TITLED |
| `LegacyProposalTotalBudgetGuidance` | `adcp.types.core.ProposalTotalBudgetGuidance` | `core/proposal.json#/properties/total_budget_guidance` | PROVISIONAL |
| `Level` | `adcp.types.core.EducationItemLevel` | `—` | PROVISIONAL |
| `LicenseType` | `adcp.types.brand.BrandDiscoveryTrademarkLicenseType` | `—` | PROVISIONAL |
| `ListCreativesField` | `adcp.types.brand.GetBrandIdentityRequestFieldsItem` | `—` | PROVISIONAL |
| `ListingType` | `adcp.types.core.RealEstateItemListingType` | `—` | PROVISIONAL |
| `LocalizationUnavailable` | `adcp.types.creative.ListCreativesResponseCreativesItemLocalizationUnavailable` | `creative/list-creatives-response.json#/properties/creatives/items/properties/localization_unavailable` | PROVISIONAL |
| `LockupType` | `adcp.types.brand.BrandDiscoveryMarkLockupLockupType` | `—` | PROVISIONAL |
| `LogoPlacement` | `adcp.types.brand.BrandDiscoveryLogoPlacement` | `brand.json#/definitions/logo_placement` | PROVISIONAL |
| `ME` | `adcp.types.core.PostalCountrySystemUSSystem` | `—` | PROVISIONAL |
| `MappingStatus` | `adcp.types.core.MacroProcessingCapabilityMappingStatus` | `—` | PROVISIONAL |
| `MatchKey` | `adcp.types.core.SignalDefinitionOnboarderMatchKeysItem` | `—` | PROVISIONAL |
| `MaterialStage` | `adcp.types.core.DeadlinePolicyMaterialStagesItem` | `core/deadline-policy.json#/properties/material_stages/items` | PROVISIONAL |
| `MaxSpend` | `adcp.types.media_buy.BuildCreativeRequestMaxSpend` | `media-buy/build-creative-request.json#/properties/max_spend` | PROVISIONAL |
| `MediaBuyDeliveryStatus` | `adcp.types.media_buy.MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus` | `—` | PROVISIONAL |
| `Methodology` | `adcp.types.core.SignalDefinitionMethodology` | `—` | PROVISIONAL |
| `Metric` | `adcp.types.compliance.ComplyTestControllerRequestParamsMetricsItem` | `compliance/comply-test-controller-request.json#/properties/params/properties/metrics/items` | PROVISIONAL |
| `Metro` | `adcp.types.trusted_match.ContextMatchRequestGeoMetro` | `trusted-match/context-match-request.json#/properties/geo/properties/metro` | PROVISIONAL |
| `Mileage` | `adcp.types.core.VehicleItemMileage` | `core/vehicle-item.json#/properties/mileage` | PROVISIONAL |
| `MinimumSize` | `adcp.types.brand.BrandDiscoveryLogoUsageRuleMinimumSize` | `brand.json#/definitions/logo_usage_rule/properties/minimum_size` | PROVISIONAL |
| `MismatchCode` | `adcp.types.core.ReportingConsumerStatusMismatchCode` | `—` | PROVISIONAL |
| `MismatchReason` | `adcp.types.error_details.VASTVersionMismatchDetailsMismatchReason` | `—` | PROVISIONAL |
| `MixTargets` | `adcp.types.governance.SyncPlansRequestPlansItemChannelsMixTargetsValue` | `governance/sync-plans-request.json#/properties/plans/items/properties/channels/properties/mix_targets/additionalProperties` | PROVISIONAL |
| `Modality` | `adcp.types.core.EducationItemModality` | `—` | PROVISIONAL |
| `Model` | `adcp.types.trusted_match.OfferPriceModel` | `—` | PROVISIONAL |
| `ModuleType` | `adcp.types.core.JavaScriptAssetRequirementsModuleType` | `—` | PROVISIONAL |
| `MotionGuidelines` | `adcp.types.brand.BrandDiscoveryMotionGuidelines` | `brand.json#/definitions/motion_guidelines` | PROVISIONAL |
| `NativeCommitEvidence` | `adcp.types.core.ReportingVerificationNativeCommitEvidence` | `core/reporting-verification.json#/properties/native_commit_evidence` | PROVISIONAL |
| `NotificationAuthentication` | `adcp.types.core.NotificationConfigAuthentication` | `core/notification-config.json#/properties/authentication` | PROVISIONAL |
| `ObligationCounts` | `adcp.types.media_buy.GetReportingStatusResponseObligationCounts` | `media-buy/get-reporting-status-response.json#/properties/obligation_counts` | PROVISIONAL |
| `ObservedThrough` | `adcp.types.core.ReportingVerificationNativeCommitEvidenceObservedThrough` | `—` | PROVISIONAL |
| `Onboarder` | `adcp.types.core.SignalDefinitionOnboarder` | `core/signal-definition.json#/properties/onboarder` | PROVISIONAL |
| `Operator` | `adcp.types.core.PackageSignalTargetingGroupOperator` | `—` | PROVISIONAL |
| `Option` | `adcp.types.core.TransformerParamOptionsItem` | `core/transformer-param.json#/properties/options/items` | PROVISIONAL |
| `Ordering` | `adcp.types.brand.BrandDiscoveryMarkLockupOrdering` | `—` | PROVISIONAL |
| `Orientation1` | `adcp.types.brand.BrandDiscoveryGraphicElementOrientation` | `—` | PROVISIONAL |
| `Origin` | `adcp.types.error_details.PolicyViolationDetailsOrigin` | `—` | PROVISIONAL |
| `OriginalError` | `adcp.types.error_details.StaleResponseDetailsOriginalError` | `error-details/stale-response.json#/properties/original_error` | PROVISIONAL |
| `Outcome` | `adcp.types.core.AttestationEvaluationOutcome` | `—` | PROVISIONAL |
| `OutcomeState` | `adcp.types.governance.ReportPlanOutcomeResponseOutcomeState` | `—` | PROVISIONAL |
| `OutputFormat` | `adcp.types.enums.PreviewOutputFormat` | `—` | TITLED |
| `OverlayUnit` | `adcp.types.core.OverlayBoundsUnit` | `—` | PROVISIONAL |
| `Overlays` | `adcp.types.brand.BrandDiscoveryCompositionRulesOverlays` | `brand.json#/definitions/composition_rules/properties/overlays` | PROVISIONAL |
| `Package` | `adcp.types.governance.ReportPlanOutcomeRequestSellerResponsePackagesItem` | `governance/report-plan-outcome-request.json#/properties/seller_response/properties/packages/items` | PROVISIONAL |
| `Pagination` | `adcp.types.creative.GetCreativeDeliveryResponsePagination` | `creative/get-creative-delivery-response.json#/properties/pagination` | PROVISIONAL |
| `Palette` | `adcp.types.brand.BrandDiscoveryAssetLibraryColorGuidePalettesItem` | `brand.json#/definitions/asset_library/properties/color_guide/properties/palettes/items` | PROVISIONAL |
| `Panel` | `adcp.types.core.DeliveryMetricsOohMetricsPanelsItem` | `core/delivery-metrics.json#/properties/ooh_metrics/properties/panels/items` | PROVISIONAL |
| `Parameters` | `adcp.types.pricing_options.CPPPricingOptionParameters` | `pricing-options/cpp-option.json#/properties/parameters` | PROVISIONAL |
| `ParentMatchBehavior` | `adcp.types.core.SignalDefinitionTaxonomyParentMatchBehavior` | `—` | PROVISIONAL |
| `Path` | `adcp.types.core.RemoveTargetingSetValuesPath` | `—` | PROVISIONAL |
| `Payload1` | `adcp.types.core.RegistryEventPropertyStalePropertyPayload` | `core/registry-event.json#/oneOf/3/properties/payload` | PROVISIONAL |
| `People` | `adcp.types.brand.BrandDiscoveryPhotographyStyleSubjectPeople` | `brand.json#/definitions/photography_style/properties/subject/properties/people` | PROVISIONAL |
| `PeriodAnchorPolicy` | `adcp.types.core.ReportingScheduleOfferingPeriodAnchorPolicy` | `—` | PROVISIONAL |
| `PeriodTimezonePolicy` | `adcp.types.core.ReportingScheduleOfferingPeriodTimezonePolicy` | `—` | PROVISIONAL |
| `Phase` | `adcp.types.core.OpportunityContextPhase` | `—` | PROVISIONAL |
| `PhotographyStyle` | `adcp.types.brand.BrandDiscoveryPhotographyStyle` | `brand.json#/definitions/photography_style` | PROVISIONAL |
| `Platform` | `adcp.types.core.AppItemPlatform` | `—` | PROVISIONAL |
| `PolicyRef` | `adcp.types.media_buy.AcceptancePolicyProfilePolicyRefsItem` | `media-buy/acceptance-policy-profile.json#/properties/policy_refs/items` | PROVISIONAL |
| `PortfolioEntry` | `adcp.types.brand.BrandDiscoveryPortfolioEntry` | `brand.json#/definitions/portfolio_entry` | PROVISIONAL |
| `PostalArea111` | `adcp.types.core.PostalAreaCountrySystemValues` | `core/postal-area.json#/anyOf/0` | PROVISIONAL |
| `PostalArea2` | `adcp.types.core.PostalAreaWithFusedSystem` | `core/postal-area.json#/anyOf/1` | TITLED |
| `PreOnboardingPrecisionLevel` | `adcp.types.core.SignalDefinitionOnboarderPreOnboardingPrecisionLevel` | `—` | PROVISIONAL |
| `PreferredPosition` | `adcp.types.brand.BrandDiscoveryLogoPlacementPreferredPosition` | `—` | PROVISIONAL |
| `Presence` | `adcp.types.core.SignalForecastDimensionPresence` | `—` | PROVISIONAL |
| `ProducerIdentity` | `adcp.types.core.ReportingDeliveryOfferingMethodProducerIdentity` | `core/reporting-delivery-offering.json#/properties/method/properties/producer_identity` | PROVISIONAL |
| `ProductChangeMap1` | `adcp.types.core.ProductChangeMapValue` | `—` | PROVISIONAL |
| `ProductFocus` | `adcp.types.brand.BrandDiscoveryPhotographyStyleSubjectProductFocus` | `—` | PROVISIONAL |
| `ProductFormatSellerPreference` | `adcp.types.core.ProductFormatDeclarationSellerPreference` | `—` | PROVISIONAL |
| `ProductResponseField` | `adcp.types.media_buy.ProductResponseFieldsItem` | `—` | PROVISIONAL |
| `ProductionStatus` | `adcp.types.core.ReportingObligationProductionStatus` | `—` | PROVISIONAL |
| `PropagationSurface` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyPropagationSurfacesItem` | `—` | PROVISIONAL |
| `PropertyFeature` | `adcp.types.property.PropertyFeature` | `property/property-feature.json#` | TITLED |
| `PropertyIdentifier` | `adcp.types.core.PlacementDefinitionIdentifiersItem` | `core/placement-definition.json#/properties/identifiers/items` | PROVISIONAL |
| `PropertySource` | `adcp.types.core.RegistryEventPropertySource` | `—` | PROVISIONAL |
| `ProvenanceRequirements` | `adcp.types.core.CreativePolicyProvenanceRequirements` | `core/creative-policy.json#/properties/provenance_requirements` | PROVISIONAL |
| `Provider` | `adcp.types.content_standards.ArtifactAssetAccessServiceAccountProvider` | `—` | PROVISIONAL |
| `Proximity` | `adcp.types.sponsored_intelligence.SISponsoredContextDisclosureObligationProximity` | `—` | PROVISIONAL |
| `PublisherEntry` | `adcp.types.aao.AAODirectoryAgentPublishersInverseLookupResponsePublisherEntry` | `aao/agent-publishers.json#/definitions/PublisherEntry` | PROVISIONAL |
| `Purpose` | `adcp.types.compliance.UpstreamTrafficSuccessRecordedCallsItemPurpose` | `—` | PROVISIONAL |
| `QuartileData` | `adcp.types.core.DeliveryMetricsQuartileData` | `core/delivery-metrics.json#/properties/quartile_data` | PROVISIONAL |
| `QuerySummary` | `adcp.types.creative.ListCreativesResponseQuerySummary` | `creative/list-creatives-response.json#/properties/query_summary` | PROVISIONAL |
| `Range` | `adcp.types.protocol.CreativeFeaturesItemRange` | `protocol/get-adcp-capabilities-response.json#/properties/governance/properties/property_features/items/properties/range` | PROVISIONAL |
| `Readiness` | `adcp.types.core.ReportingDeliveryReadyWebhookReadiness` | `—` | PROVISIONAL |
| `RealEstateUnit` | `adcp.types.core.RealEstateItemAreaUnit` | `—` | PROVISIONAL |
| `Realism` | `adcp.types.brand.BrandDiscoveryPhotographyStyleRealism` | `—` | PROVISIONAL |
| `RecommendedAction` | `adcp.types.core.ReportingStatusIssueRecommendedAction` | `—` | PROVISIONAL |
| `ReconciliationStatus` | `adcp.types.core.ReportingObligationReconciliationStatus` | `—` | PROVISIONAL |
| `Rectangle` | `adcp.types.core.PlacementPresentationDocumentRectangle` | `core/placement-presentation.json#/definitions/rectangle` | PROVISIONAL |
| `RedirectReason` | `adcp.types.brand.HouseRedirectRedirectReason` | `—` | PROVISIONAL |
| `ReferenceMutability` | `adcp.types.formats.CanonicalFormatBaseReferenceMutability` | `—` | PROVISIONAL |
| `RegistrationTask` | `adcp.types.protocol.CapabilityChangeNotificationsSupportedRegistrationTask` | `—` | PROVISIONAL |
| `RegulatoryBasi` | `adcp.types.governance.AttributeDefinitionRegulatoryBasisItem` | `governance/attribute-definition.json#/properties/regulatory_basis/items` | PROVISIONAL |
| `RegulatoryFramework` | `adcp.types.governance.PolicyCategoryDefinitionRegulatoryFrameworksItem` | `governance/policy-category-definition.json#/properties/regulatory_frameworks/items` | PROVISIONAL |
| `RelatedCollection` | `adcp.types.core.CollectionRelatedCollectionsItem` | `core/collection.json#/properties/related_collections/items` | PROVISIONAL |
| `Relationship` | `adcp.types.brand.BrandDiscoveryPropertyRelationship` | `—` | PROVISIONAL |
| `RelationshipKind` | `adcp.types.core.IndicatorsChangedWebhookRelationshipKind` | `—` | PROVISIONAL |
| `RelationshipTrust` | `adcp.types.brand.SearchBrandsResponseSearchBrandResultRelationshipTrust` | `—` | PROVISIONAL |
| `RemovalReason` | `adcp.types.core.WholesaleFeedEventRemovalReason` | `—` | PROVISIONAL |
| `Renders` | `adcp.types.core.RendersItemDimensions` | `core/format.json#/properties/renders/items/oneOf/0` | PROVISIONAL |
| `Renders1` | `adcp.types.core.RendersItemParametersFromFormatId` | `core/format.json#/properties/renders/items/oneOf/1` | PROVISIONAL |
| `ReportCalendarTimezoneBasis` | `adcp.types.core.ReportingReportDefinitionReportCalendarTimezoneBasis` | `—` | TITLED |
| `ReportingAuthoritativeParty` | `adcp.types.core.ReportingDeliveryConfigurationAuthoritativeParty` | `—` | PROVISIONAL |
| `ReportingConsumerFailureCode` | `adcp.types.core.ReportingConsumerStatusFailureCode` | `—` | PROVISIONAL |
| `ReportingConsumerMismatchCode` | `adcp.types.core.ReportingConsumerStatusMismatchCode` | `—` | PROVISIONAL |
| `ReportingConsumerStatusValue` | `adcp.types.core.ReportingConsumerStatusConsumerStatus` | `—` | PROVISIONAL |
| `ReportingDeliveryConfigLifecycleState` | `adcp.types.core.ReportingDeliveryConfigurationStateReportingDeliveryConfigLifecycleState` | `—` | PROVISIONAL |
| `ReportingFeedPurpose` | `adcp.types.core.ReportingDeliveryOfferingReportingFeedPurpose` | `—` | TITLED |
| `ReportingIssueRecommendedAction` | `adcp.types.core.ReportingStatusIssueRecommendedAction` | `—` | PROVISIONAL |
| `ReportingIssueState` | `adcp.types.core.ReportingStatusIssueIssueState` | `—` | PROVISIONAL |
| `ReportingMode` | `adcp.types.core.DemographicReportingCapabilityAgeReportingModesItem` | `—` | PROVISIONAL |
| `ReportingObligationCounts` | `adcp.types.media_buy.GetReportingStatusResponseObligationCounts` | `media-buy/get-reporting-status-response.json#/properties/obligation_counts` | PROVISIONAL |
| `ReportingOrchestration` | `adcp.types.core.ReportingDeliveryMethodReportingOrchestration` | `—` | TITLED |
| `ReportingPeriod` | `adcp.types.creative.GetCreativeDeliveryResponseReportingPeriod` | `creative/get-creative-delivery-response.json#/properties/reporting_period` | PROVISIONAL |
| `ReportingScheduleAlignment` | `adcp.types.core.ReportingScheduleReportingScheduleAlignment` | `—` | TITLED |
| `ReportingStatusView` | `adcp.types.media_buy.GetReportingStatusRequestReportingStatusView` | `—` | TITLED |
| `RequestType` | `adcp.types.creative.PreviewCreativeRequestRequestType` | `—` | PROVISIONAL |
| `RequiredGeoTargetingItem` | `adcp.types.core.ProductFiltersRequiredGeoTargetingItem` | `core/product-filters.json#/properties/required_geo_targeting/items` | PROVISIONAL |
| `Requirement` | `adcp.types.property.ValidationResultFeaturesItemRequirement` | `property/validation-result.json#/properties/features/items/properties/requirement` | PROVISIONAL |
| `ResolutionModel` | `adcp.types.core.SignalTargetingRulesResolutionModel` | `—` | PROVISIONAL |
| `ResolvedPolicy` | `adcp.types.governance.SyncPlansResponsePlansItemResolvedPoliciesItem` | `governance/sync-plans-response.json#/properties/plans/items/properties/resolved_policies/items` | PROVISIONAL |
| `ResponsibleParty` | `adcp.types.core.ReportingStatusIssueResponsibleParty` | `—` | PROVISIONAL |
| `Responsive` | `adcp.types.core.FormatRendersItemDimensionsResponsive` | `core/format.json#/properties/renders/items/properties/dimensions/properties/responsive` | TITLED |
| `Result` | `adcp.types.core.ProvenanceVerificationItemResult` | `—` | PROVISIONAL |
| `ResultEntry1` | `adcp.types.brand.VerifyBrandClaimsResultSuccess` | `brand/verify-brand-claims-response.json#/definitions/result_entry/oneOf/0` | TITLED |
| `ResultEntry2` | `adcp.types.brand.VerifyBrandClaimsResultError` | `brand/verify-brand-claims-response.json#/definitions/result_entry/oneOf/1` | TITLED |
| `ResultKind` | `adcp.types.creative.ValidateInputResultResultKind` | `—` | PROVISIONAL |
| `RevokedPublisherDomain` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain1` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain2` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain3` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain4` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain5` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `RevokedPublisherDomain6` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem` | `adagents.json#/oneOf/1/properties/revoked_publisher_domains/items` | PROVISIONAL |
| `Right` | `adcp.types.core.SignalDefinitionDataSubjectRightsChannelsItemRightsItem` | `—` | PROVISIONAL |
| `RightsAgent` | `adcp.types.brand.BrandDiscoveryRightsAgent` | `brand.json#/definitions/rights_agent` | PROVISIONAL |
| `RightsAttestations` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyRightsAttestations` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/rights_attestations` | PROVISIONAL |
| `Roas` | `adcp.types.core.BiddingPolicyRoas` | `core/bidding-policy.json#/properties/roas` | PROVISIONAL |
| `Role2` | `adcp.types.core.ReferenceAssetRole` | `—` | PROVISIONAL |
| `RotationMode` | `adcp.types.core.CreativeAssignmentRotationMode` | `—` | PROVISIONAL |
| `Salary` | `adcp.types.core.JobItemSalary` | `core/job-item.json#/properties/salary` | PROVISIONAL |
| `Sandbox` | `adcp.types.core.HTMLAssetRequirementsSandbox` | `—` | PROVISIONAL |
| `Scale` | `adcp.types.brand.BrandDiscoverySpacingScale` | `brand.json#/definitions/spacing/properties/scale` | PROVISIONAL |
| `Scheme` | `adcp.types.enums.AuthenticationScheme` | `—` | TITLED |
| `Scope1` | `adcp.types.brand.BrandDiscoveryAuthorizedOperatorScopesItem` | `—` | PROVISIONAL |
| `ScopeFromBillingNotSupported` | `adcp.types.error_details.BillingNotSupportedDetailsScope` | `—` | PROVISIONAL |
| `ScopeFromDownstreamConnectionRequirement` | `adcp.types.core.DownstreamConnectionRequirementScope` | `—` | PROVISIONAL |
| `ScopeFromRateLimited` | `adcp.types.error_details.RateLimitedDetailsScope` | `—` | PROVISIONAL |
| `SealedCredential` | `adcp.types.trusted_match.IdentityMatchRequestSealedCredentialsItem` | `trusted-match/identity-match-request.json#/properties/sealed_credentials/items` | PROVISIONAL |
| `Security` | `adcp.types.core.WebhookAssetSecurity` | `core/assets/webhook-asset.json#/properties/security` | PROVISIONAL |
| `SeedSource` | `adcp.types.core.SignalDefinitionModelingSeedSource` | `core/signal-definition.json#/properties/modeling/properties/seed_source` | PROVISIONAL |
| `Segment` | `adcp.types.creative.VideoBriefSegmentsItem` | `creative/video-brief.json#/properties/segments/items` | PROVISIONAL |
| `Selector` | `adcp.types.core.RemoveTargetingSetValuesSelector` | `core/targeting-modification.json#/oneOf/1/properties/selector` | PROVISIONAL |
| `SellerPreference` | `adcp.types.core.ProductFormatDeclarationSellerPreference` | `—` | PROVISIONAL |
| `Semantics` | `adcp.types.media_buy.GetProductsResponseFilterDiagnosticsSemantics` | `—` | PROVISIONAL |
| `Sentiment` | `adcp.types.trusted_match.ContextMatchRequestContextSignalsSentiment` | `—` | PROVISIONAL |
| `ServingPolicy` | `adcp.types.formats.CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy` | `—` | PROVISIONAL |
| `Severity` | `adcp.types.core.DiagnosticIssueSeverity` | `—` | PROVISIONAL |
| `ShippingAddress` | `adcp.types.sponsored_intelligence.SIIdentityUserShippingAddress` | `sponsored-intelligence/si-identity.json#/properties/user/properties/shipping_address` | PROVISIONAL |
| `SiSponsoredContextDeclaredBy` | `adcp.types.sponsored_intelligence.SISponsoredContextDeclaredBy` | `sponsored-intelligence/si-sponsored-context.json#/properties/declared_by` | PROVISIONAL |
| `SignalCondition4` | `adcp.types.media_buy.BuildCreativeRequestSignalConditionsItem` | `media-buy/build-creative-request.json#/properties/signal_conditions/items` | PROVISIONAL |
| `SignalType` | `adcp.types.enums.SignalAvailabilityType` | `—` | TITLED |
| `Snapshot` | `adcp.types.creative.ListCreativesResponseCreativesItemSnapshot` | `creative/list-creatives-response.json#/properties/creatives/items/properties/snapshot` | PROVISIONAL |
| `SortApplied` | `adcp.types.creative.ListCreativesResponseQuerySummarySortApplied` | `creative/list-creatives-response.json#/properties/query_summary/properties/sort_applied` | PROVISIONAL |
| `Source` | `adcp.types.core.ErrorSource` | `—` | PROVISIONAL |
| `SourceAdcpVersion` | `adcp.types.media_buy.RequestProposalsResponsePurchaseContinuationLegacyCreateSourceAdcpVersion` | `—` | PROVISIONAL |
| `Spacing` | `adcp.types.brand.BrandDiscoverySpacing` | `brand.json#/definitions/spacing` | PROVISIONAL |
| `Specification` | `adcp.types.core.ProductProductCardDetailedSpecificationsItem` | `core/product.json#/properties/product_card_detailed/properties/specifications/items` | PROVISIONAL |
| `Spot` | `adcp.types.media_buy.GetMediaBuyDeliveryRequestReportingDimensionsSpot` | `media-buy/get-media-buy-delivery-request.json#/properties/reporting_dimensions/properties/spot` | PROVISIONAL |
| `StandardEnum` | `adcp.types.sponsored_intelligence.SICapabilitiesComponentsStandardItem` | `—` | PROVISIONAL |
| `StartingPosition` | `adcp.types.account.ListAccountChangesRequestStartingPosition` | `—` | PROVISIONAL |
| `Status46` | `adcp.types.sponsored_intelligence.SISponsoredContextReceiptHostReceiptDisclosureCommitmentStatus` | `—` | PROVISIONAL |
| `Status51` | `adcp.types.governance.SyncPlansResponsePlansItemCategoriesItemStatus` | `—` | PROVISIONAL |
| `StatusFromDownstreamConnectionRequirement` | `adcp.types.core.DownstreamConnectionRequirementStatus` | `—` | PROVISIONAL |
| `StatusFromMacroResolutionResult` | `adcp.types.core.MacroResolutionResultStatus` | `—` | PROVISIONAL |
| `StatusSummary` | `adcp.types.creative.ListCreativesResponseStatusSummary` | `creative/list-creatives-response.json#/properties/status_summary` | PROVISIONAL |
| `Statuses` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemSummaryStatuses` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/summary/properties/statuses` | PROVISIONAL |
| `Storyboard` | `adcp.types.core.RegistryEventCompliancePayloadStoryboardsItem` | `core/registry-event.json#/$defs/compliancePayload/properties/storyboards/items` | PROVISIONAL |
| `StoryboardStatus` | `adcp.types.core.RegistryEventStoryboardStatus` | `—` | PROVISIONAL |
| `StringArray` | `adcp.types.core.StringArray` | `—` | PROVISIONAL |
| `StrokeStyle` | `adcp.types.brand.BrandDiscoveryGraphicStyleStrokeStyle` | `—` | PROVISIONAL |
| `Structural` | `adcp.types.registries.V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/1/properties/structural` | PROVISIONAL |
| `Style` | `adcp.types.brand.BrandDiscoveryFontFileStyle` | `—` | PROVISIONAL |
| `Style1` | `adcp.types.brand.BrandDiscoveryIconographyStyle` | `—` | PROVISIONAL |
| `Style2` | `adcp.types.brand.BrandDiscoveryCompositionRulesTextureStyle` | `—` | PROVISIONAL |
| `StyleType` | `adcp.types.brand.BrandDiscoveryGraphicStyleStyleType` | `—` | PROVISIONAL |
| `Subject` | `adcp.types.brand.BrandDiscoveryPhotographyStyleSubject` | `brand.json#/definitions/photography_style/properties/subject` | PROVISIONAL |
| `SupportedChange` | `adcp.types.protocol.AccountIdentityUpdatesSupportedSupportedChangesItem` | `—` | PROVISIONAL |
| `SupportedDeliveryMethod` | `adcp.types.core.AttestationCapabilitiesSupportedDeliveryMethodsItem` | `—` | PROVISIONAL |
| `SupportedDimension` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyProposalRefinementSupportedDimensionsItem` | `—` | PROVISIONAL |
| `SupportedIdentifierType` | `adcp.types.protocol.SupportedHashedIdentifiersItem` | `—` | PROVISIONAL |
| `SupportedPresenceMode` | `adcp.types.core.ProductAudienceEvidenceRequirementsEvidencePresence` | `—` | PROVISIONAL |
| `SupportedRequirementMode` | `adcp.types.core.ProductAudienceEvidenceRequirementsRequirementMode` | `—` | PROVISIONAL |
| `SupportedScope` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedScopesItem` | `—` | PROVISIONAL |
| `SupportedSection` | `adcp.types.protocol.GetAdCPCapabilitiesResponseAdcpPrincipalSupportedSectionsItem` | `—` | PROVISIONAL |
| `SyncGovernanceGovernanceAgent` | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItem` | `account/sync-governance-request.json#/properties/accounts/items/properties/governance_agents/items` | PROVISIONAL |
| `Target` | `adcp.types.creative.ValidateInputResultTarget` | `creative/validate-input-result.json#/properties/target` | PROVISIONAL |
| `TaskStatus` | `adcp.types.enums.TaskStatus` | `—` | TITLED |
| `TerminationContext` | `adcp.types.sponsored_intelligence.SITerminateSessionRequestTerminationContext` | `sponsored-intelligence/si-terminate-session-request.json#/properties/termination_context` | PROVISIONAL |
| `Terms` | `adcp.types.core.InsertionOrderTerms` | `core/insertion-order.json#/properties/terms` | PROVISIONAL |
| `TextEntrance` | `adcp.types.brand.BrandDiscoveryMotionGuidelinesTextEntrance` | `—` | PROVISIONAL |
| `TextTransform` | `adcp.types.brand.BrandDiscoveryTypeScaleEntryTextTransform` | `—` | PROVISIONAL |
| `Texture` | `adcp.types.brand.BrandDiscoveryCompositionRulesTexture` | `brand.json#/definitions/composition_rules/properties/texture` | PROVISIONAL |
| `Thresholds` | `adcp.types.governance.GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsThresholds` | `governance/get-plan-audit-logs-response.json#/properties/plans/items/properties/summary/properties/drift_metrics/properties/thresholds` | PROVISIONAL |
| `TimeBasedView` | `adcp.types.core.DeliveryMetricsTimeBasedViewsItem` | `core/delivery-metrics.json#/properties/time_based_views/items` | PROVISIONAL |
| `TimeRange` | `adcp.types.content_standards.GetMediaBuyArtifactsRequestTimeRange` | `content-standards/get-media-buy-artifacts-request.json#/properties/time_range` | PROVISIONAL |
| `TimeUnit` | `adcp.types.pricing_options.TimeBasedPricingOptionParametersTimeUnit` | `—` | PROVISIONAL |
| `Timing` | `adcp.types.sponsored_intelligence.SISponsoredContextDisclosureObligationTiming` | `—` | PROVISIONAL |
| `TmpxProviders` | `adcp.types.trusted_match.IdentityMatchResponseRouterPublisherTmpxProvidersValue` | `trusted-match/identity-match-response.json#/properties/tmpx_providers/additionalProperties` | PROVISIONAL |
| `TotalBudget` | `adcp.types.core.InsertionOrderTermsTotalBudget` | `core/insertion-order.json#/properties/terms/properties/total_budget` | PROVISIONAL |
| `TotalBudgetGuidance` | `adcp.types.core.ProposalTotalBudgetGuidance` | `core/proposal.json#/properties/total_budget_guidance` | PROVISIONAL |
| `Tracks` | `adcp.types.core.RegistryEventCompliancePayloadTracksValue` | `—` | PROVISIONAL |
| `Trademark` | `adcp.types.brand.BrandDiscoveryTrademark` | `brand.json#/definitions/trademark` | PROVISIONAL |
| `TransactionIntent` | `adcp.types.sponsored_intelligence.SITerminateSessionRequestTerminationContextTransactionIntent` | `sponsored-intelligence/si-terminate-session-request.json#/properties/termination_context/properties/transaction_intent` | PROVISIONAL |
| `TranscriptFormat` | `adcp.types.content_standards.AssetsItemAudioTranscriptFormat` | `—` | PROVISIONAL |
| `TranscriptSource` | `adcp.types.content_standards.ArtifactAssetsItemVideoTranscriptSource` | `—` | PROVISIONAL |
| `TranscriptSource1` | `adcp.types.content_standards.ArtifactAssetsItemAudioTranscriptSource` | `—` | PROVISIONAL |
| `TransitionStyle` | `adcp.types.brand.BrandDiscoveryMotionGuidelinesTransitionStyle` | `—` | PROVISIONAL |
| `Transmission` | `adcp.types.core.VehicleItemTransmission` | `—` | PROVISIONAL |
| `Trust` | `adcp.types.core.BrandResponseAuthorizationResultTrust` | `—` | PROVISIONAL |
| `Type1` | `adcp.types.brand.BrandDiscoveryGraphicElementType` | `—` | PROVISIONAL |
| `Type2` | `adcp.types.brand.BrandDiscoveryAssetLibraryType` | `—` | PROVISIONAL |
| `TypeScale` | `adcp.types.brand.BrandDiscoveryVisualGuidelinesTypeScale` | `brand.json#/definitions/visual_guidelines/properties/type_scale` | PROVISIONAL |
| `TypeScaleEntry` | `adcp.types.brand.BrandDiscoveryTypeScaleEntry` | `brand.json#/definitions/type_scale_entry` | PROVISIONAL |
| `TypesAllowedEnum` | `adcp.types.brand.BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem` | `—` | PROVISIONAL |
| `UnavailableBehavior` | `adcp.types.core.MacroDeclarationUnavailableBehavior` | `—` | PROVISIONAL |
| `UnavailableReason` | `adcp.types.core.AccountChangeRepairUnavailableReason` | `—` | PROVISIONAL |
| `UnknownHandling` | `adcp.types.core.DemographicTargetingCapabilityAgeUnknownHandling` | `—` | PROVISIONAL |
| `Usage` | `adcp.types.brand.BrandDiscoveryBrandShapesUsage` | `brand.json#/definitions/brand_shapes/properties/usage` | PROVISIONAL |
| `Usage1` | `adcp.types.brand.BrandDiscoveryIconographyUsage` | `brand.json#/definitions/iconography/properties/usage` | PROVISIONAL |
| `User` | `adcp.types.sponsored_intelligence.SIIdentityUser` | `sponsored-intelligence/si-identity.json#/properties/user` | PROVISIONAL |
| `V1CanonicalDimensions` | `adcp.types.registries.V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/1/properties/structural/properties/dimensions` | PROVISIONAL |
| `V1CanonicalGlobPattern` | `adcp.types.registries.V1PatternFormatIdGlob` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/0` | PROVISIONAL |
| `V1CanonicalStructural` | `adcp.types.registries.V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/1/properties/structural` | PROVISIONAL |
| `V1CanonicalStructuralPattern` | `adcp.types.registries.V1PatternStructural` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/1` | PROVISIONAL |
| `V1Pattern` | `adcp.types.registries.V1PatternFormatIdGlob` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/0` | PROVISIONAL |
| `V1Pattern1` | `adcp.types.registries.V1PatternStructural` | `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf/1` | PROVISIONAL |
| `ValidityHint` | `adcp.types.core.AttestationReferenceValidityHint` | `core/attestation-reference.json#/properties/validity_hint` | PROVISIONAL |
| `Value` | `adcp.types.core.SignalDefinitionTaxonomyValuesItem` | `core/signal-definition.json#/properties/taxonomy/properties/values/items` | PROVISIONAL |
| `ValueMapping` | `adcp.types.core.SignalDefinitionTaxonomyValueMappingsItem` | `core/signal-definition.json#/properties/taxonomy/properties/value_mappings/items` | PROVISIONAL |
| `ValueSource` | `adcp.types.core.TransformerParamValueSource` | `—` | PROVISIONAL |
| `VariableType` | `adcp.types.core.CreativeVariableVariableType` | `—` | PROVISIONAL |
| `VariantAxis` | `adcp.types.media_buy.BuildCreativeRequestVariantAxis` | `media-buy/build-creative-request.json#/properties/variant_axis` | PROVISIONAL |
| `VastEvent` | `adcp.types.core.VASTTrackerConstraintsVastEvent` | `—` | PROVISIONAL |
| `VastValidation` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecsVastValidation` | `—` | PROVISIONAL |
| `VehicleUnit` | `adcp.types.core.VehicleItemMileageUnit` | `—` | PROVISIONAL |
| `VenueBreakdownItem` | `adcp.types.core.DeliveryMetricsDoohMetricsVenueBreakdownItem` | `core/delivery-metrics.json#/properties/dooh_metrics/properties/venue_breakdown/items` | PROVISIONAL |
| `VerificationLevel` | `adcp.types.trusted_match.IdentityMatchRequestIdentitiesItemAttestationVerificationLevel` | `—` | PROVISIONAL |
| `VerificationPath` | `adcp.types.core.ReportingVerificationVerificationPath` | `—` | PROVISIONAL |
| `ViewThreshold1` | `adcp.types.pricing_options.ViewThresholdDurationSeconds` | `pricing-options/cpv-option.json#/properties/parameters/properties/view_threshold/oneOf/1` | PROVISIONAL |
| `ViewedSecondsHistogramItem` | `adcp.types.core.DeliveryMetricsViewabilityViewedSecondsHistogramItem` | `core/delivery-metrics.json#/properties/viewability/properties/viewed_seconds_histogram/items` | PROVISIONAL |
| `ViewedSecondsPercentiles` | `adcp.types.core.DeliveryMetricsViewabilityViewedSecondsPercentiles` | `core/delivery-metrics.json#/properties/viewability/properties/viewed_seconds_percentiles` | PROVISIONAL |
| `VoiceSynthesis` | `adcp.types.brand.BrandDiscoveryBrandVoiceSynthesis` | `brand.json#/definitions/brand/properties/voice_synthesis` | PROVISIONAL |
| `Watermark` | `adcp.types.core.ProvenanceWatermarksItem` | `core/provenance.json#/properties/watermarks/items` | PROVISIONAL |
| `WholesaleFeedVersioning` | `adcp.types.protocol.GetAdCPCapabilitiesResponseWholesaleFeedVersioning` | `protocol/get-adcp-capabilities-response.json#/properties/wholesale_feed_versioning` | PROVISIONAL |

**WHAT IS WITHHELD, AND WHY — counted, not omitted.**

* **40 words reach two different declarations of
  ours** depending on which module of upstream's the import came from. Reading 10: "a name
  resolves to a *different* class of ours depending on which upstream module the import came
  from, so one flat alias cannot serve both." One flat namespace cannot hold two meanings for
  one word, so these take a migration note and no alias — and the alternative on offer is an
  arbitrary pick, which is the silent substitution this reading exists to refuse.
* **0 declarations of ours reach no
  `adcp.types.<domain>` export.** §4's own remedy applies and it is not this layer's: "an
  EXPORT or a NAME, never a split. The alias layer cannot reach a private name."

Both lists are re-derivable with `survey/mechanical_aliases.py --report`, which prints them
by name.

<!-- END GENERATED -->
---

<!-- GENERATED by survey/node_keyed_aliases.py -- do not edit between the fences -->

## §11. The node-keyed aliases, on upstream's declared flat surface

**Every row below is a PAIR, and the pair is the unit** — `docs/plan/final-state.md` reading
10: "an alias whose entry is missing is a reading 10 FAILURE and not partial credit."

**WHAT DECIDED THE TARGET IS THE DOCUMENT NODE, WITH IDENTITY AS A GATE.** Upstream's
defining module names the document; our declarations compiled from *that document* are the
candidates; the class's identity — the field set read by wire alias, or the enum's value
list — is a **gate on that candidate set and never the proposal**, because the error-envelope
field set is shared by forty classes of ours and identity alone over the whole tree "matches"
everything. A name no rule resolved is left out and reported, never minted
(`survey/probes/build_map.py`, `survey/dropin_blocking.py`).

**AND THE COUNT IS OVER THE DELIBERATE SURFACE, WHICH IS THE LARGER FIGURE CORRECTED.** The
map carries **2626 rows over 2318 distinct names**, keyed at
`adcp.types.domains.<document>` — upstream's *generated layout*, which reading 10 calls a
spelling and not a name, and which no `__all__` of theirs declares. Upstream's own
hand-written flat `__all__` holds **939** names, and
**436** of the map's names are on it. The other
**1882** are reachable only through their generated layout: reading
10 is explicit that "a name reachable only because a module forgot to declare what it exports
is not a name an application was invited to import, and treating it as one makes upstream's
omission our obligation." Those spellings are served in the tree by a RULE and not a table,
and they get no flat word here.

**69 pairs written**, 25 plain and 44 PROVISIONAL. The
difference is whose word *ours* is: where the bundle **titles** our word the row is plain;
where it titles nothing at that node our word is derived from the parent and the key, so the
alias *records* upstream's commitment and the row says PROVISIONAL. The upstream ask is the
same sentence for every provisional row and is stated once: **give the node at that pointer a
`title`.**

| upstream's word | our surface name | the node the document states it at | status |
|---|---|---|---|
| `AcceptancePolicyDiscovery` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/acceptance_policy_discovery` | PROVISIONAL |
| `AcceptancePolicyProfileId` | `adcp.types.core.ReportingMediaBuyId` | `—` | PROVISIONAL |
| `AcceptedLoss` | `adcp.types.media_buy.RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem` | `—` | PROVISIONAL |
| `AcquireRightsResponse1` | `adcp.types.brand.AcquireRightsAcquired` | `brand/acquire-rights-response.json#/oneOf/0` | TITLED |
| `Action` | `adcp.types.a2ui.A2UIUserActionAction` | `a2ui/user-action.json#/properties/action` | PROVISIONAL |
| `ActivateSignalResponse1` | `adcp.types.signals.ActivateSignalSuccess` | `signals/activate-signal-response.json#/oneOf/0` | TITLED |
| `AggregatedTotals` | `adcp.types.media_buy.GetMediaBuyDeliveryResponseAggregatedTotals` | `media-buy/get-media-buy-delivery-response.json#/properties/aggregated_totals` | PROVISIONAL |
| `AiTool` | `adcp.types.core.ProvenanceAiTool` | `core/provenance.json#/properties/ai_tool` | PROVISIONAL |
| `AssignedPackage` | `adcp.types.creative.ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItem` | `creative/list-creatives-response.json#/properties/creatives/items/properties/assignments/properties/assigned_packages/items` | PROVISIONAL |
| `Assignments` | `adcp.types.creative.ListCreativesResponseCreativesItemAssignments` | `creative/list-creatives-response.json#/properties/creatives/items/properties/assignments` | PROVISIONAL |
| `CalibrateContentResponse1` | `adcp.types.content_standards.CalibrateContentResponseVerdict` | `content-standards/calibrate-content-response.json#/oneOf/0` | PROVISIONAL |
| `CatalogFieldBinding1` | `adcp.types.core.CatalogFieldBindingCatalogGroup` | `core/requirements/catalog-field-binding.json#/oneOf/2` | PROVISIONAL |
| `ComplyTestControllerResponse1` | `adcp.types.compliance.ListScenariosSuccess` | `compliance/comply-test-controller-response.json#/oneOf/0` | TITLED |
| `CreateContentStandardsResponse1` | `adcp.types.content_standards.CreateContentStandardsResponseStandardsId` | `content-standards/create-content-standards-response.json#/oneOf/0` | PROVISIONAL |
| `CreativeAgent` | `adcp.types.creative.ListCreativeFormatsResponseCreativeAgentCreativeAgentsItem` | `creative/list-creative-formats-response.json#/properties/creative_agents/items` | PROVISIONAL |
| `CreativeApproval` | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItemPackagesItemCreativeApprovalsItem` | `media-buy/get-media-buys-response.json#/properties/media_buys/items/properties/packages/items/properties/creative_approvals/items` | PROVISIONAL |
| `CreditLimit` | `adcp.types.core.AccountCreditLimit` | `core/account.json#/properties/credit_limit` | PROVISIONAL |
| `DailyBreakdownItem` | `adcp.types.media_buy.GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemDailyBreakdownItem` | `media-buy/get-media-buy-delivery-response.json#/properties/media_buy_deliveries/items/properties/by_package/items/allOf/1/properties/daily_breakdown/items` | PROVISIONAL |
| `DeliveryMeasurement` | `adcp.types.core.ProductDeliveryMeasurement` | `core/product.json#/properties/delivery_measurement` | PROVISIONAL |
| `DoohMetrics` | `adcp.types.core.DeliveryMetricsDoohMetrics` | `core/delivery-metrics.json#/properties/dooh_metrics` | PROVISIONAL |
| `Fonts` | `adcp.types.brand.BrandDiscoveryFonts` | `brand.json#/definitions/fonts` | PROVISIONAL |
| `FormatCard` | `adcp.types.core.FormatFormatCard` | `core/format.json#/properties/format_card` | PROVISIONAL |
| `FormatCardDetailed` | `adcp.types.core.FormatFormatCard` | `core/format.json#/properties/format_card` | PROVISIONAL |
| `GetAccountFinancialsResponse1` | `adcp.types.account.GetAccountFinancialsSuccess` | `account/get-account-financials-response.json#/oneOf/0` | TITLED |
| `GetBrandIdentityResponse1` | `adcp.types.brand.GetBrandIdentitySuccess` | `brand/get-brand-identity-response.json#/oneOf/0` | TITLED |
| `GetContentStandardsResponse1` | `adcp.types.content_standards.GetContentStandardsResponseBranch0` | `content-standards/get-content-standards-response.json#/oneOf/0` | PROVISIONAL |
| `GetCreativeFeaturesResponse1` | `adcp.types.creative.GetCreativeFeaturesResponse` | `creative/get-creative-features-response.json#` | TITLED |
| `GetMediaBuyArtifactsResponse1` | `adcp.types.content_standards.GetMediaBuyArtifactsResponseArtifactsMediaBuyId` | `content-standards/get-media-buy-artifacts-response.json#/oneOf/0` | PROVISIONAL |
| `GetRightsResponse1` | `adcp.types.brand.GetRightsSuccess` | `brand/get-rights-response.json#/oneOf/0` | TITLED |
| `Input` | `adcp.types.creative.PreviewCreativeSingleResponsePreviewsItemInput` | `creative/preview-creative-response.json#/oneOf/0/properties/previews/items/properties/input` | PROVISIONAL |
| `ListContentStandardsResponse1` | `adcp.types.content_standards.ListContentStandardsResponseStandards` | `content-standards/list-content-standards-response.json#/oneOf/0` | PROVISIONAL |
| `LogEventResponse1` | `adcp.types.media_buy.LogEventSuccess` | `media-buy/log-event-response.json#/oneOf/0` | TITLED |
| `MeasurementPeriod` | `adcp.types.content_standards.GetMediaBuyArtifactsRequestTimeRange` | `content-standards/get-media-buy-artifacts-request.json#/properties/time_range` | PROVISIONAL |
| `Method` | `adcp.types.core.ReportingDeliveryOfferingMethod` | `core/reporting-delivery-offering.json#/properties/method` | PROVISIONAL |
| `PrincipalAppliedResult` | `adcp.types.protocol.AppliedPrincipalConfiguration` | `protocol/sync-principal-response.json#/properties/result/oneOf/0` | TITLED |
| `PrincipalCurrentResult` | `adcp.types.protocol.CurrentPrincipalConfiguration` | `protocol/get-principal-response.json#/properties/result/oneOf/0` | TITLED |
| `PrincipalReadFailedResult` | `adcp.types.protocol.FailedPrincipalRead` | `protocol/get-principal-response.json#/properties/result/oneOf/3` | TITLED |
| `PrincipalRecognizedResult` | `adcp.types.protocol.RecognizedPrincipalWithoutStandingConfiguration` | `protocol/get-principal-response.json#/properties/result/oneOf/1` | TITLED |
| `PrincipalSyncFailedResult` | `adcp.types.protocol.FailedPrincipalSync` | `protocol/sync-principal-response.json#/properties/result/oneOf/2` | TITLED |
| `PrincipalUnconfiguredResult` | `adcp.types.protocol.UnconfiguredPrincipal` | `protocol/get-principal-response.json#/properties/result/oneOf/2` | TITLED |
| `PrincipalValidatedResult` | `adcp.types.protocol.ValidatedPrincipalDryRun` | `protocol/sync-principal-response.json#/properties/result/oneOf/1` | TITLED |
| `ProductCard` | `adcp.types.core.ProductProductCard` | `core/product.json#/properties/product_card` | PROVISIONAL |
| `ProductCardDetailed` | `adcp.types.core.ProductProductCardDetailed` | `core/product.json#/properties/product_card_detailed` | PROVISIONAL |
| `ProductCatalog` | `adcp.types.brand.BrandDiscoveryProductCatalog` | `brand.json#/definitions/product_catalog` | PROVISIONAL |
| `PropertyList` | `adcp.types.property.PropertyList` | `property/property-list.json#` | TITLED |
| `ProvidePerformanceFeedbackResponse1` | `adcp.types.media_buy.ProvidePerformanceFeedbackSuccess` | `media-buy/provide-performance-feedback-response.json#/oneOf/0` | TITLED |
| `RefinementApplied1` | `adcp.types.media_buy.RefinementAppliedItemRequest` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/0` | PROVISIONAL |
| `RefinementApplied2` | `adcp.types.media_buy.RefinementAppliedItemProduct` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/1` | PROVISIONAL |
| `RefinementApplied3` | `adcp.types.media_buy.RefinementAppliedItemProposal` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/2` | PROVISIONAL |
| `ReportingBucket` | `adcp.types.core.AccountReportingBucket` | `core/account.json#/properties/reporting_bucket` | PROVISIONAL |
| `Request` | `adcp.types.creative.PreviewCreativeRequestRequestsItem` | `creative/preview-creative-request.json#/properties/requests/items` | PROVISIONAL |
| `SyncAccountsResponse1` | `adcp.types.account.SyncAccountsSuccess` | `account/sync-accounts-response.json#/oneOf/0` | TITLED |
| `SyncAudiencesResponse1` | `adcp.types.media_buy.SyncAudiencesSuccess` | `media-buy/sync-audiences-response.json#/oneOf/0` | TITLED |
| `SyncCatalogsResponse1` | `adcp.types.media_buy.SyncCatalogsSuccess` | `media-buy/sync-catalogs-response.json#/oneOf/0` | TITLED |
| `SyncCreativesResponse1` | `adcp.types.creative.SyncCreativesSuccess` | `creative/sync-creatives-response.json#/oneOf/0` | TITLED |
| `SyncCreativesResponse3` | `adcp.types.creative.SyncCreativesError` | `creative/sync-creatives-response.json#/oneOf/1` | TITLED |
| `SyncEventSourcesResponse1` | `adcp.types.media_buy.SyncEventSourcesSuccess` | `media-buy/sync-event-sources-response.json#/oneOf/0` | TITLED |
| `Tags` | `adcp.types.adagents.SignalTagsValue` | `adagents.json#/oneOf/1/properties/tags/additionalProperties` | PROVISIONAL |
| `UnknownFormatAsset` | `adcp.types.core.FormatBaseIndividualAsset` | `core/format.json#/$defs/baseIndividualAsset` | PROVISIONAL |
| `UnknownGroupAsset` | `adcp.types.core.FormatBaseGroupAsset` | `core/format.json#/$defs/baseGroupAsset` | PROVISIONAL |
| `UpdateContentStandardsResponse1` | `adcp.types.content_standards.UpdateContentStandardsSuccess` | `content-standards/update-content-standards-response.json#/oneOf/0` | TITLED |
| `ValidateContentDeliveryResponse1` | `adcp.types.content_standards.ValidateContentDeliveryResponseResultsSummary` | `content-standards/validate-content-delivery-response.json#/oneOf/0` | PROVISIONAL |
| `VerifyBrandClaimPayload` | `adcp.types.brand.VerifyBrandClaimResponseSignedResponsePayload` | `brand/verify-brand-claim-response.json#/definitions/signed_response/allOf/1/properties/payload` | PROVISIONAL |
| `VerifyBrandClaimSignedResponse` | `adcp.types.brand.VerifyBrandClaimResponseSignedResponse` | `brand/verify-brand-claim-response.json#/definitions/signed_response` | PROVISIONAL |
| `VerifyBrandClaimSignedSuccessPayload` | `adcp.types.brand.VerifyBrandClaimResponseSignedSuccessPayload` | `brand/verify-brand-claim-response.json#/definitions/signed_success_payload` | PROVISIONAL |
| `VerifyBrandClaimsErrorResponse` | `adcp.types.brand.VerifyBrandClaimsError` | `brand/verify-brand-claims-response.json#/oneOf/1` | TITLED |
| `VerifyBrandClaimsPayload` | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload` | `brand/verify-brand-claims-response.json#/definitions/signed_response/allOf/1/properties/payload` | PROVISIONAL |
| `VerifyBrandClaimsSignedResponse` | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponse` | `brand/verify-brand-claims-response.json#/definitions/signed_response` | PROVISIONAL |
| `VerifyBrandClaimsSignedSuccessPayload` | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedSuccessPayload` | `brand/verify-brand-claims-response.json#/definitions/signed_success_payload` | PROVISIONAL |

**WHAT IS WITHHELD, AND WHY — counted, not omitted.**

* **43 words on their declared surface reach two
  different declarations of ours** depending on which module of theirs the import came from.
  Reading 10: "a name resolves to a *different* class of ours depending on which upstream
  module the import came from, so one flat alias cannot serve both." These take a migration
  note and no alias (`adcp-client-python-r482`).
* **23 words are THEIRS, declared by a
  hand-written module of theirs and not by their generated tree** — read off their own
  `_eager.py`, which is what their `adcp/types/__init__.py` resolves every flat `__getattr__`
  through. Reading 10: "where upstream's name means a different set of values, an alias is a
  DEFECT and not a bridge ... that name takes a migration note naming both sets." Their
  `canonical_creative.Format` requires `[format_kind, params]`; `core/format.json` requires
  `[format_id, name]`; **no shared required element, so disjoint on its face.** Measured cost
  of writing them anyway: `from adcp.types import Format` handed back our generated class and
  148 of their behavioural tests failed on a silent substitution.
* **293 already resolve flat** and owe nothing.
* **8 targets reach no `adcp.types.<domain>` export.**
  §4's own remedy applies and it is not this layer's: "an EXPORT or a NAME, never a split.
  The alias layer cannot reach a private name."
* **0 targets do not resolve at all**, which is a
  defect of the map and is reported rather than skipped.

Re-derivable with `survey/node_keyed_aliases.py --report`, which prints each by name.

<!-- END GENERATED -->
---

<!-- GENERATED by survey/alias_destinations.py -- do not edit between the markers -->

## §12. The spellings that RESOLVE: the alias is upstream's word, the emitted path is the document's

**NOTHING IN THIS SECTION IS GOING AWAY, and an application that changes none of its imports
goes on working.** The six sections above are about names that FAIL. This one is about the
**1,077 that WORK**: an upstream spelling the alias layer binds, resolving onto a
class this compiler emitted from a bundle document. Until now they were documented only by
their absence from those six, and the owner's ruling is that their absence said the wrong
thing about them.

### Construct from the payload and let the model choose the branch

**A CALLER SHOULD NEVER NAME A BRANCH CLASS, and this is the AdCP data model rather than a
feature of this package.** At 8 nodes the bundle states an XOR — a
`required` clause per branch with a `not` forbidding the other's key — so a creative is
addressed one way or the other and never both.
`creative/list-creatives-response.json#/properties/creatives/items` is the case to read: two
branches titled *"Listed creative (named-format reference)"* and *"Listed creative (canonical
format kind)"*, selected by whether `format_id` or `format_kind` is present. So hand the
payload to the base and let it dispatch:

```python
from adcp.types.creative import ListCreativesResponseCreativesItem

ListCreativesResponseCreativesItem.model_validate({**base, "format_id": ref})
# -> ListedCreativeNamedFormatReference
ListCreativesResponseCreativesItem.model_validate({**base, "format_kind": "image"})
# -> ListedCreativeCanonicalFormatKind
ListCreativesResponseCreativesItem.model_validate(
    {**base, "format_id": ref, "format_kind": "image"}
)
# -> refused: "0 of these clauses hold, the document admits exactly one"
ListCreativesResponseCreativesItem.model_validate(base)
# -> refused, the same sentence
```

The XOR is enforced structurally and the caller does not choose. **This holds for anyone
implementing AdCP 3.2–3.3 in any language** — our classes reproduce the document's clause,
they do not invent it — so the guidance is not "use our helper", it is *a creative is
addressed one way or the other, pass what you have, and the model decides*.

**AND WHERE AN UPSTREAM SPELLING REACHES ONE OF THOSE BASES, THAT IS THE FUTURE-PROOF FORM
AND NOT MERELY THE EMITTED PATH.** Upstream's word at such a node names a class that carried
both addressing forms as optional fields, and the edit worth making there is not a rename: it
is to stop selecting a class at all and hand the payload over. **4 rows below
reach one of the 8 bases** and carry **PAYLOAD** in their last
column — `Catchment`, `FrequencyCapImpressionConstraints`, `FrequencyCapIntervalConstraints`, `LegacyCreativeAsset` — and
no row reaches a branch class directly.
For every other row the emitted-path rule below is the whole of it. The
8 nodes are `adcp-client-python-j0fr`'s census, taken from it rather
than re-derived here.

### The rule, stated once rather than per row

**BOTH SPELLINGS ARE TRUE AND ONE OF THEM IS A FUNCTION OF THE DOCUMENT.** An alias is a
NAME and never a second type — every statement in `compat.py`, `_adapter.py` and
`_restored.py` is a re-export, so the object reached through upstream's word IS the object
the walk emitted, `isinstance` holds across every spelling of one subject, and
`adcp.types.<word> is adcp.types.<domain>.<Name>` for every row below. What separates the two
columns is whose word each one is:

- **the left column is upstream's word**, recorded from their 9.6.1 wheel. It keeps
  resolving. It is pinned to a release of theirs and to nothing else.
- **the right column is the document's**, derived from the node the declaration was compiled
  from. A bundle bump moves it with the document — and it can retire an upstream word
  entirely, which is the one thing the left column cannot survive.

So the emitted path is what a new line should be written against, and an existing line that
works needs no edit. **This is a precedence between two live spellings and not a
deprecation**: no row below is scheduled for removal, and nothing in this section is a
breaking change. The six sections above keep the breaking changes, which are theirs.

### How the 1,077 rows were derived

Read off the compiler's own record and the alias layers' own tables, never off this file's
text — `survey/alias_destinations.py`, committed, and `--write` rewrites this section whole:

| the table | names | what it is |
|---|---|---|
| `compat.__all__` | 988 | the alias table — every relocated upstream spelling |
| `compat.__adcp_flat_only__` | 79 | a word our own domain module carries |
| `_adapter.__all__` | 127 | upstream's own module-scope flat imports |
| `_restored.__all__` | 223 | what upstream's restored files declare |
| **the union** | **1,391** | a word may stand in two tables |

The union is 1,391 and not 1,338, which is the three-table sum
`adcp-client-python-b2pm` measured before `__adcp_flat_only__` was counted. Of those
1,391 words, **1,077 reach a class this compiler emitted**, and each
row states four things: the word an application writes today, the emitted class, that
class's own path, and the node the document states it at. The class is the last segment of
the path, so one column carries both.

A row's target is found by OBJECT and never by name: `adcp.types._surface` is the compiler's
own per-domain export record, 23 domains, and a path is admissible only
where the object at it IS the object upstream's word resolves to. 1,077 of the
1,077 rows have exactly one such path, and 1,077 of them are in the domain
their own document derives — so no row picks between two paths and none of them is served by
a module outside the domain surface. Which layer answers is `adcp.types.__getattr__`'s
precedence order and not a membership test: upstream's own statement first
(`_restored.STATED`), then the alias table, then `__adcp_flat_only__`, then `_adapter`, then
`_restored` —
**compat** 918, **_adapter** 91, **flat_only** 68.

**AND THE TOP-LEVEL DEMAND IS READ AND NOT EXCLUDED, which is a blind spot the adapter
census has.** That census ranges over what upstream's kept machinery imports and cannot see
`adcp/__init__.py`'s `_LAZY` map, so it under-measures the `from adcp import <Name>`
surface. Read here: of its
751 names,
**375 are already in one of the four tables** (305 of them
are rows below), **32 resolve at `adcp.types` with no alias
at all** because our own walk emitted the same word, and **344 raise
there** — §1's machinery, which no document states and this section owes nothing.

| the word written today | the emitted class, at its own path | the document and pointer | layer |
|---|---|---|---|
| `A2UiBoundValue` | `adcp.types.a2ui.A2UIBoundValue` | `a2ui/bound-value.json#` | compat |
| `A2UiComponent` | `adcp.types.a2ui.A2UIComponent` | `a2ui/component.json#` | compat |
| `A2UiSurface` | `adcp.types.a2ui.A2UISurface` | `a2ui/surface.json#` | compat |
| `A2UiUserAction` | `adcp.types.a2ui.A2UIUserAction` | `a2ui/user-action.json#` | compat |
| `AaoDirectoryAgentPublishersInverseLookupResponse` | `adcp.types.aao.AAODirectoryAgentPublishersInverseLookupResponse` | `aao/agent-publishers.json#` | compat |
| `AcceptProposalInputRequired` | `adcp.types.media_buy.AcceptProposalInputRequired` | `media-buy/accept-proposal-async-response-input-required.json#` | compat |
| `AcceptProposalRequest` | `adcp.types.media_buy.AcceptProposalRequest` | `media-buy/accept-proposal-request.json#` | flat_only |
| `AcceptProposalSubmitted` | `adcp.types.media_buy.AcceptProposalSubmitted` | `media-buy/accept-proposal-async-response-submitted.json#` | compat |
| `AcceptProposalWorking` | `adcp.types.media_buy.AcceptProposalWorking` | `media-buy/accept-proposal-async-response-working.json#` | compat |
| `AcceptanceContext` | `adcp.types.media_buy.AcceptanceContext` | `media-buy/acceptance-context.json#` | flat_only |
| `AcceptancePolicyCatalog` | `adcp.types.media_buy.AcceptancePolicyCatalog` | `media-buy/acceptance-policy-catalog.json#` | flat_only |
| `AcceptancePolicyDiscovery` | `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/acceptance_policy_discovery` | _adapter |
| `AcceptancePolicyProfile` | `adcp.types.media_buy.AcceptancePolicyProfile` | `media-buy/acceptance-policy-profile.json#` | flat_only |
| `AcceptancePolicyProfileIds` | `adcp.types.core.AcceptancePolicyProfileIDs` | `core/acceptance-policy-profile-ids.json#` | compat |
| `AcceptancePolicyRequirement` | `adcp.types.media_buy.AcceptancePolicyRequirement` | `media-buy/acceptance-policy-requirement.json#` | flat_only |
| `AcceptancePolicyRule` | `adcp.types.media_buy.AcceptancePolicyRule` | `media-buy/acceptance-policy-rule.json#` | flat_only |
| `AcceptedGovernanceAgents` | `adcp.types.governance.AcceptedGovernanceAgents` | `governance/accepted-governance-agents.json#` | compat |
| `AccessibilityViolationDetails` | `adcp.types.error_details.AccessibilityViolationDetails` | `error-details/accessibility-violation.json#` | flat_only |
| `Account` | `adcp.types.core.Account` | `core/account.json#` | compat |
| `AccountAuthorization` | `adcp.types.core.AccountAuthorization` | `core/account-authorization.json#` | compat |
| `AccountChange` | `adcp.types.core.AccountChange` | `core/account-change.json#` | compat |
| `AccountChangeRecordedWebhook` | `adcp.types.core.AccountChangeRecordedWebhook` | `core/account-change-recorded-webhook.json#` | compat |
| `AccountCurrencyMode` | `adcp.types.enums.AccountCurrencyMode` | `enums/account-currency-mode.json#` | compat |
| `AccountIdentityChange` | `adcp.types.core.AccountIdentityChange` | `core/account-identity-change.json#` | compat |
| `AccountIdentityChangePreview` | `adcp.types.core.AccountIdentityChangePreview` | `core/account-identity-change-preview.json#` | compat |
| `AccountMovedDetails` | `adcp.types.error_details.AccountMovedDetails` | `error-details/account-moved.json#` | flat_only |
| `AccountReference` | `adcp.types.core.AccountReference` | `core/account-ref.json#` | compat |
| `AccountReferenceById` | `adcp.types.core.AccountReferenceAccountId` | `core/account-ref.json#/oneOf/0` | _adapter |
| `AccountReferenceByNaturalKey` | `adcp.types.core.AccountReferenceBrandOperator` | `core/account-ref.json#/oneOf/1` | _adapter |
| `AccountScope` | `adcp.types.enums.AccountScope` | `enums/account-scope.json#` | compat |
| `AccountSetupRequiredDetails` | `adcp.types.error_details.AccountSetupRequiredDetails` | `error-details/account-setup-required.json#` | flat_only |
| `AccountStatus` | `adcp.types.enums.AccountStatus` | `enums/account-status.json#` | compat |
| `AccountStatusChangedWebhook` | `adcp.types.core.AccountStatusChangedWebhook` | `core/account-status-changed-webhook.json#` | compat |
| `AccountTimezoneCapability` | `adcp.types.core.AccountTimezoneCapability` | `core/account-timezone-capability.json#` | compat |
| `AccountWithAuthorization` | `adcp.types.core.AccountWithAuthorization` | `core/account-with-authorization.json#` | compat |
| `AcquireRightsRequest` | `adcp.types.brand.AcquireRightsRequest` | `brand/acquire-rights-request.json#` | compat |
| `AcquireRightsResponse` | `adcp.types.brand.AcquireRightsResponse` | `brand/acquire-rights-response.json#` | compat |
| `ActionNotAllowedDetails` | `adcp.types.error_details.ActionNotAllowedDetails` | `error-details/action-not-allowed.json#` | flat_only |
| `ActionNotAllowedReason` | `adcp.types.enums.ActionNotAllowedReason` | `enums/action-not-allowed-reason.json#` | compat |
| `ActionSource` | `adcp.types.enums.ActionSource` | `enums/action-source.json#` | compat |
| `ActivateSignalRequest` | `adcp.types.signals.ActivateSignalRequest` | `signals/activate-signal-request.json#` | flat_only |
| `ActivateSignalResponse` | `adcp.types.signals.ActivateSignalResponse` | `signals/activate-signal-response.json#` | flat_only |
| `ActivateSignalSuccessResponse` | `adcp.types.signals.ActivateSignalSuccess` | `signals/activate-signal-response.json#/oneOf/0` | _adapter |
| `ActivationKey` | `adcp.types.core.ActivationKey` | `core/activation-key.json#` | compat |
| `AdInventoryConfiguration` | `adcp.types.core.AdInventoryConfiguration` | `core/ad-inventory-config.json#` | compat |
| `AdcpAgentsAuthorization` | `adcp.types.adagents.AdCPAgentsAuthorization` | `adagents.json#` | compat |
| `AdcpAssetGroupVocabularyRegistry` | `adcp.types.core.AdCPAssetGroupVocabularyRegistry` | `core/asset-group-vocabulary.json#` | compat |
| `AdcpAsyncResponseData` | `adcp.types.core.AdCPAsyncResponseData` | `core/async-response-data.json#` | compat |
| `AdcpExtensionFileSchema` | `adcp.types.extensions.AdCPExtensionFileSchema` | `extensions/extension-meta.json#` | compat |
| `AdcpFormatShapeVocabularyRegistry` | `adcp.types.core.AdCPFormatShapeVocabularyRegistry` | `core/format-shape-vocabulary.json#` | compat |
| `AdcpProtocol` | `adcp.types.enums.AdCPProtocol` | `enums/adcp-protocol.json#` | compat |
| `AdcpSpecialism` | `adcp.types.enums.AdCPSpecialism` | `enums/specialism.json#` | compat |
| `AdcpVersionEnvelope` | `adcp.types.core.AdCPVersionEnvelope` | `core/version-envelope.json#` | compat |
| `AdvertiserIndustry` | `adcp.types.enums.AdvertiserIndustry` | `enums/advertiser-industry.json#` | compat |
| `AgeDeterminationBasis` | `adcp.types.enums.AgeDeterminationBasis` | `enums/age-determination-basis.json#` | compat |
| `AgeVerificationMethod` | `adcp.types.enums.AgeVerificationMethod` | `enums/age-verification-method.json#` | compat |
| `AgentDeclarations` | `adcp.types.core.AgentDeclarations` | `core/principal-declarations.json#` | compat |
| `AgentEncryptionKey` | `adcp.types.core.AgentEncryptionKey` | `core/agent-encryption-key.json#` | compat |
| `AgentNotificationConfig` | `adcp.types.core.AgentNotificationConfig` | `core/agent-notification-config.json#` | compat |
| `AgentNotificationConfigState` | `adcp.types.core.AgentNotificationConfigState` | `core/agent-notification-config-state.json#` | compat |
| `AgentPermissionDeniedDetails` | `adcp.types.error_details.AgentPermissionDeniedDetails` | `error-details/agent-permission-denied.json#` | flat_only |
| `AgentReportingDestination` | `adcp.types.core.AgentReportingDestination` | `core/agent-reporting-destination.json#` | compat |
| `AgentReportingDestinationState` | `adcp.types.core.AgentReportingDestinationState` | `core/agent-reporting-destination-state.json#` | compat |
| `AgentSigningKey` | `adcp.types.core.AgentSigningKey` | `core/agent-signing-key.json#` | compat |
| `AgentWebhookChallenge` | `adcp.types.core.AgentWebhookChallenge` | `core/agent-webhook-challenge.json#` | compat |
| `AgenticadvertisingOrgVerificationTokenClaims` | `adcp.types.core.AgenticAdvertisingOrgVerificationTokenClaims` | `core/verification-token-claims.json#` | compat |
| `AppItem` | `adcp.types.core.AppItem` | `core/app-item.json#` | compat |
| `Artifact` | `adcp.types.content_standards.Artifact` | `content-standards/artifact.json#` | compat |
| `ArtifactWebhookPayload` | `adcp.types.content_standards.ArtifactWebhookPayload` | `content-standards/artifact-webhook-payload.json#` | compat |
| `AssessmentStatus` | `adcp.types.enums.AssessmentStatus` | `enums/assessment-status.json#` | compat |
| `AssetContentType` | `adcp.types.enums.AssetContentType` | `enums/asset-content-type.json#` | compat |
| `AssetRequirements` | `adcp.types.core.AssetRequirements` | `core/requirements/asset-requirements.json#` | compat |
| `AssetVariant` | `adcp.types.core.AssetVariant` | `core/assets/asset-union.json#` | compat |
| `AttestationCapabilities` | `adcp.types.core.AttestationCapabilities` | `core/attestation-capabilities.json#` | compat |
| `AttestationClaim` | `adcp.types.enums.AttestationClaim` | `enums/attestation-claim.json#` | compat |
| `AttestationEvaluation` | `adcp.types.core.AttestationEvaluation` | `core/attestation-evaluation.json#` | compat |
| `AttestationIssuer` | `adcp.types.core.AttestationIssuer` | `core/attestation-issuer.json#` | compat |
| `AttestationReference` | `adcp.types.core.AttestationReference` | `core/attestation-reference.json#` | compat |
| `AttestationSubject` | `adcp.types.core.AttestationSubject` | `core/attestation-subject.json#` | compat |
| `AttributeDefinition` | `adcp.types.governance.AttributeDefinition` | `governance/attribute-definition.json#` | compat |
| `AttributionMethodology` | `adcp.types.enums.AttributionMethodology` | `enums/attribution-methodology.json#` | compat |
| `AttributionModel` | `adcp.types.enums.AttributionModel` | `enums/attribution-model.json#` | compat |
| `AudienceActivationMethod` | `adcp.types.core.AudienceActivationMethod` | `core/audience-activation-method.json#` | compat |
| `AudienceCharacteristic` | `adcp.types.core.AudienceCharacteristic` | `core/audience-characteristic.json#` | compat |
| `AudienceConstraints` | `adcp.types.governance.AudienceConstraints` | `governance/audience-constraints.json#` | compat |
| `AudienceEvidence` | `adcp.types.core.AudienceEvidence` | `core/audience-evidence.json#` | compat |
| `AudienceEvidenceMethodology` | `adcp.types.enums.AudienceEvidenceMethodology` | `enums/audience-evidence-methodology.json#` | compat |
| `AudienceEvidencePin` | `adcp.types.core.AudienceEvidencePin` | `core/audience-evidence-pin.json#` | compat |
| `AudienceEvidenceRequirements` | `adcp.types.core.AudienceEvidenceRequirements` | `core/audience-evidence-requirements.json#` | compat |
| `AudienceEvidenceSelection` | `adcp.types.core.AudienceEvidenceSelection` | `core/audience-evidence-selection.json#` | compat |
| `AudienceForecastDimension` | `adcp.types.core.AudienceForecastDimension` | `core/forecast-dimension-audience.json#` | compat |
| `AudienceMember` | `adcp.types.core.AudienceMember` | `core/audience-member.json#` | compat |
| `AudienceResolutionMethod` | `adcp.types.enums.AudienceResolutionMethod` | `enums/audience-resolution-method.json#` | compat |
| `AudienceSelector` | `adcp.types.core.AudienceSelector` | `core/audience-selector.json#` | compat |
| `AudienceSource` | `adcp.types.enums.AudienceSource` | `enums/audience-source.json#` | _adapter |
| `AudienceStatus` | `adcp.types.enums.AudienceStatus` | `enums/audience-status.json#` | compat |
| `AudienceSubjectType` | `adcp.types.enums.AudienceSubjectType` | `enums/audience-subject-type.json#` | compat |
| `AudienceTooSmallDetails` | `adcp.types.error_details.AudienceTooSmallDetails` | `error-details/audience-too-small.json#` | flat_only |
| `AudioAsset` | `adcp.types.core.AudioAsset` | `core/assets/audio-asset.json#` | compat |
| `AudioAssetRequirements` | `adcp.types.core.AudioAssetRequirements` | `core/requirements/audio-asset-requirements.json#` | compat |
| `AudioChannelLayout` | `adcp.types.enums.AudioChannelLayout` | `enums/audio-channel-layout.json#` | compat |
| `AudioContent` | `adcp.types.core.AudioAsset` | `core/assets/audio-asset.json#` | _adapter |
| `AudioDistributionType` | `adcp.types.enums.AudioDistributionType` | `enums/audio-distribution-type.json#` | compat |
| `Authentication` | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItemAuthentication` | `account/sync-governance-request.json#/properties/accounts/items/properties/governance_agents/items/properties/authentication` | _adapter |
| `AuthenticationScheme` | `adcp.types.enums.AuthenticationScheme` | `enums/auth-scheme.json#` | compat |
| `AuthorizationRequiredDetails` | `adcp.types.error_details.AuthorizationRequiredDetails` | `error-details/authorization-required.json#` | flat_only |
| `AuthorizationResult` | `adcp.types.property.AuthorizationResult` | `property/authorization-result.json#` | compat |
| `AuthorizedAgentBaseFields` | `adcp.types.core.AuthorizedAgentBaseFields` | `core/authorized-agent-base.json#` | compat |
| `AvailabilityStatus` | `adcp.types.enums.AvailabilityStatus` | `enums/availability-status.json#` | compat |
| `AvailableMetric` | `adcp.types.enums.AvailableMetric` | `enums/available-metric.json#` | compat |
| `AvailablePackage` | `adcp.types.trusted_match.AvailablePackage` | `trusted-match/available-package.json#` | compat |
| `Avatar` | `adcp.types.sponsored_intelligence.Avatar` | `sponsored-intelligence/si-capabilities.json#/properties/modalities/properties/avatar/oneOf/1` | compat |
| `BaseCollectionSource` | `adcp.types.collection.BaseCollectionSource` | `collection/base-collection-source.json#` | compat |
| `BasePropertySource` | `adcp.types.property.BasePropertySource` | `property/base-property-source.json#` | compat |
| `BiddingPolicy` | `adcp.types.core.BiddingPolicy` | `core/bidding-policy.json#` | compat |
| `BiddingPolicyCapability` | `adcp.types.core.BiddingPolicyCapability` | `core/bidding-policy-capability.json#` | compat |
| `BillingNotPermittedForAgentDetails` | `adcp.types.error_details.BillingNotPermittedForAgentDetails` | `error-details/billing-not-permitted-for-agent.json#` | flat_only |
| `BillingNotSupportedDetails` | `adcp.types.error_details.BillingNotSupportedDetails` | `error-details/billing-not-supported.json#` | flat_only |
| `BillingParty` | `adcp.types.enums.BillingParty` | `enums/billing-party.json#` | compat |
| `BinaryVerdict` | `adcp.types.enums.BinaryVerdict` | `enums/binary-verdict.json#` | compat |
| `BrandAgentType` | `adcp.types.enums.BrandAgentType` | `enums/brand-agent-type.json#` | compat |
| `BrandDiscovery` | `adcp.types.brand.BrandDiscovery` | `brand.json#` | compat |
| `BrandKey` | `adcp.types.core.BrandKey` | `core/brand-key.json#` | compat |
| `BrandRef` | `adcp.types.core.BrandReference` | `core/brand-ref.json#` | compat |
| `BrandReference` | `adcp.types.core.BrandReference` | `core/brand-ref.json#` | compat |
| `BrandResponseAuthorizationResult` | `adcp.types.core.BrandResponseAuthorizationResult` | `core/brand-response-authorization-result.json#` | compat |
| `BriefAsset` | `adcp.types.core.BriefAsset` | `core/assets/brief-asset.json#` | compat |
| `BrowserFamily` | `adcp.types.enums.BrowserFamily` | `enums/browser-family.json#` | compat |
| `BudgetAllocation` | `adcp.types.core.BudgetAllocation` | `core/budget-allocation.json#` | compat |
| `BudgetChangeConstraints` | `adcp.types.media_buy.BudgetChangeConstraints` | `media-buy/change-term-constraints.json#/oneOf/0` | flat_only |
| `BudgetRange` | `adcp.types.core.BudgetRange` | `core/budget-range.json#` | compat |
| `BudgetTooLowDetails` | `adcp.types.error_details.BudgetTooLowDetails` | `error-details/budget-too-low.json#` | flat_only |
| `BuildCreativeInputRequired` | `adcp.types.media_buy.BuildCreativeInputRequired` | `media-buy/build-creative-async-response-input-required.json#` | compat |
| `BuildCreativeRequest` | `adcp.types.media_buy.BuildCreativeRequest` | `media-buy/build-creative-request.json#` | compat |
| `BuildCreativeResponse` | `adcp.types.media_buy.BuildCreativeResponse` | `media-buy/build-creative-response.json#` | compat |
| `BuildCreativeSubmitted` | `adcp.types.media_buy.BuildCreativeSubmitted` | `media-buy/build-creative-async-response-submitted.json#` | compat |
| `BuildCreativeWorking` | `adcp.types.media_buy.BuildCreativeWorking` | `media-buy/build-creative-async-response-working.json#` | compat |
| `BusinessEntity` | `adcp.types.core.BusinessEntity` | `core/business-entity.json#` | compat |
| `BuyProductsInputRequired` | `adcp.types.media_buy.BuyProductsInputRequired` | `media-buy/buy-products-async-response-input-required.json#` | compat |
| `BuyProductsRequest` | `adcp.types.media_buy.BuyProductsRequest` | `media-buy/buy-products-request.json#` | flat_only |
| `BuyProductsSubmitted` | `adcp.types.media_buy.BuyProductsSubmitted` | `media-buy/buy-products-async-response-submitted.json#` | compat |
| `BuyProductsWorking` | `adcp.types.media_buy.BuyProductsWorking` | `media-buy/buy-products-async-response-working.json#` | compat |
| `C2PaWatermarkAction` | `adcp.types.enums.C2PAWatermarkAction` | `enums/c2pa-watermark-action.json#` | compat |
| `C2paWatermarkAction` | `adcp.types.enums.C2PAWatermarkAction` | `enums/c2pa-watermark-action.json#` | compat |
| `CalibrateContentRequest` | `adcp.types.content_standards.CalibrateContentRequest` | `content-standards/calibrate-content-request.json#` | compat |
| `CalibrateContentResponse` | `adcp.types.content_standards.CalibrateContentResponse` | `content-standards/calibrate-content-response.json#` | compat |
| `CanceledBy` | `adcp.types.enums.CanceledBy` | `enums/canceled-by.json#` | compat |
| `CancellationPolicy` | `adcp.types.core.CancellationPolicy` | `core/cancellation-policy.json#` | compat |
| `CanonicalAccountReference` | `adcp.types.core.CanonicalAccountReference` | `core/canonical-account-ref.json#` | compat |
| `CanonicalAudienceEvidence` | `adcp.types.core.CanonicalAudienceEvidence` | `core/canonical-audience-evidence.json#` | compat |
| `CanonicalAudienceEvidenceSelection` | `adcp.types.core.CanonicalAudienceEvidenceSelection` | `core/canonical-audience-evidence-selection.json#` | compat |
| `CanonicalBudgetAllocation` | `adcp.types.core.CanonicalBudgetAllocation` | `core/canonical-budget-allocation.json#` | compat |
| `CanonicalDeliveryForecast` | `adcp.types.core.CanonicalDeliveryForecast` | `core/canonical-delivery-forecast.json#` | compat |
| `CanonicalForecastPoint` | `adcp.types.core.CanonicalForecastPoint` | `core/canonical-forecast-point.json#` | compat |
| `CanonicalForecastVendorMetricValue` | `adcp.types.core.CanonicalForecastVendorMetricValue` | `core/canonical-forecast-vendor-metric-value.json#` | compat |
| `CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement` | `adcp.types.formats.CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement` | `formats/canonical/agent_placement.json#` | compat |
| `CanonicalFormatBase` | `adcp.types.formats.CanonicalFormatBase` | `formats/canonical/_base.json#` | compat |
| `CanonicalFormatCoordinatedPlacements` | `adcp.types.formats.CanonicalFormatCoordinatedPlacements` | `formats/canonical/coordinated_placements.json#` | compat |
| `CanonicalFormatDaastAudio` | `adcp.types.formats.CanonicalFormatDAASTAudio` | `formats/canonical/audio_daast.json#` | compat |
| `CanonicalFormatDisplayTag` | `adcp.types.formats.CanonicalFormatDisplayTag` | `formats/canonical/display_tag.json#` | compat |
| `CanonicalFormatHostedAudio` | `adcp.types.formats.CanonicalFormatHostedAudio` | `formats/canonical/audio_hosted.json#` | compat |
| `CanonicalFormatHostedVideo` | `adcp.types.formats.CanonicalFormatHostedVideo` | `formats/canonical/video_hosted.json#` | compat |
| `CanonicalFormatHtml5Banner` | `adcp.types.formats.CanonicalFormatHTML5Banner` | `formats/canonical/html5.json#` | compat |
| `CanonicalFormatImage` | `adcp.types.formats.CanonicalFormatImage` | `formats/canonical/image.json#` | compat |
| `CanonicalFormatImageCarousel` | `adcp.types.formats.CanonicalFormatImageCarousel` | `formats/canonical/image_carousel.json#` | compat |
| `CanonicalFormatKind` | `adcp.types.core.CanonicalFormatKind` | `core/canonical-format-kind.json#` | compat |
| `CanonicalFormatNativeInFeed` | `adcp.types.formats.CanonicalFormatNativeInFeed` | `formats/canonical/native_in_feed.json#` | compat |
| `CanonicalFormatOption` | `adcp.types.core.CanonicalFormatOption` | `core/canonical-format-option.json#` | compat |
| `CanonicalFormatResponsiveCreative` | `adcp.types.formats.CanonicalFormatResponsiveCreative` | `formats/canonical/responsive_creative.json#` | compat |
| `CanonicalFormatSellerRenderedStatefulDisplay` | `adcp.types.formats.CanonicalFormatSellerRenderedStatefulDisplay` | `formats/canonical/seller_rendered_stateful_display.json#` | compat |
| `CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven` | `adcp.types.formats.CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven` | `formats/canonical/sponsored_placement.json#` | compat |
| `CanonicalFormatVastAudio` | `adcp.types.formats.CanonicalFormatVASTAudio` | `formats/canonical/audio_vast.json#` | compat |
| `CanonicalFormatVastVideo` | `adcp.types.formats.CanonicalFormatVASTVideo` | `formats/canonical/video_vast.json#` | compat |
| `CanonicalMeasurementTerms` | `adcp.types.core.CanonicalMeasurementTerms` | `core/canonical-measurement-terms.json#` | compat |
| `CanonicalMediaBuyAction` | `adcp.types.core.CanonicalMediaBuyAction` | `core/canonical-media-buy-action.json#` | compat |
| `CanonicalMediaBuyActionFields` | `adcp.types.core.CanonicalMediaBuyActionFields` | `core/canonical-media-buy-action-fields.json#` | compat |
| `CanonicalMediaBuyActionMode` | `adcp.types.enums.CanonicalMediaBuyActionMode` | `enums/canonical-media-buy-action-mode.json#` | compat |
| `CanonicalMediaBuyActionName` | `adcp.types.enums.CanonicalMediaBuyActionName` | `enums/canonical-media-buy-action.json#` | compat |
| `CanonicalMediaBuyFeatures` | `adcp.types.core.CanonicalMediaBuyFeatures` | `core/canonical-media-buy-features.json#` | compat |
| `CanonicalMetricQualifier` | `adcp.types.core.CanonicalMetricQualifier` | `core/canonical-metric-qualifier.json#` | compat |
| `CanonicalOptimizationGoal` | `adcp.types.core.CanonicalOptimizationGoal` | `core/canonical-optimization-goal.json#` | compat |
| `CanonicalPerformanceStandard` | `adcp.types.core.CanonicalPerformanceStandard` | `core/canonical-performance-standard.json#` | compat |
| `CanonicalPricingOption` | `adcp.types.core.CanonicalPricingOption` | `core/canonical-pricing-option.json#` | compat |
| `CanonicalProduct` | `adcp.types.core.CanonicalProduct` | `core/canonical-product.json#` | compat |
| `CanonicalProductAction` | `adcp.types.core.CanonicalProductAction` | `core/canonical-product-action.json#` | compat |
| `CanonicalProductPlacement` | `adcp.types.core.CanonicalProductPlacement` | `core/canonical-placement.json#` | compat |
| `CanonicalProjectionReference` | `adcp.types.core.CanonicalProjectionReference` | `core/canonical-projection-ref.json#` | compat |
| `CanonicalProjectionSlotOverride` | `adcp.types.core.CanonicalProjectionSlotOverride` | `core/canonical-projection-slot-override.json#` | compat |
| `CanonicalProposal` | `adcp.types.core.CanonicalProposal` | `core/canonical-proposal.json#` | compat |
| `CanonicalProposalTotalBudgetGuidance` | `adcp.types.core.CanonicalProposalTotalBudgetGuidance` | `core/canonical-proposal.json#/properties/total_budget_guidance` | compat |
| `CanonicalReportingCapabilities` | `adcp.types.core.CanonicalReportingCapabilities` | `core/canonical-reporting-capabilities.json#` | compat |
| `CanonicalReportingCommitment` | `adcp.types.core.CanonicalReportingCommitment` | `core/canonical-reporting-commitment.json#` | compat |
| `CanvasConstraint` | `adcp.types.core.CanvasConstraint` | `core/canvas-constraint.json#` | compat |
| `CapabilitiesChangedWebhook` | `adcp.types.core.CapabilitiesChangedWebhook` | `core/capabilities-changed-webhook.json#` | compat |
| `CardAsset` | `adcp.types.core.CardAsset` | `core/assets/card-asset.json#` | compat |
| `Catalog` | `adcp.types.core.Catalog` | `core/catalog.json#` | compat |
| `CatalogAction` | `adcp.types.enums.CatalogAction` | `enums/catalog-action.json#` | compat |
| `CatalogAsset` | `adcp.types.core.CatalogAsset` | `core/assets/catalog-asset.json#` | compat |
| `CatalogFieldBinding` | `adcp.types.core.CatalogFieldBinding` | `core/requirements/catalog-field-binding.json#` | compat |
| `CatalogFieldMapping` | `adcp.types.core.CatalogFieldMapping` | `core/catalog-field-mapping.json#` | compat |
| `CatalogItemAvailabilityError` | `adcp.types.core.CatalogItemAvailabilityError` | `core/catalog-item-availability-error.json#` | compat |
| `CatalogItemAvailabilityReference` | `adcp.types.core.CatalogItemAvailabilityReference` | `core/catalog-item-availability-ref.json#` | compat |
| `CatalogItemAvailabilityState` | `adcp.types.core.CatalogItemAvailabilityState` | `core/catalog-item-availability-state.json#` | compat |
| `CatalogItemAvailabilityUpdate` | `adcp.types.core.CatalogItemAvailabilityUpdate` | `core/catalog-item-availability-update.json#` | compat |
| `CatalogItemAvailabilityUpdateResult` | `adcp.types.core.CatalogItemAvailabilityUpdateResult` | `core/catalog-item-availability-update-result.json#` | compat |
| `CatalogItemDeliveryMetrics` | `adcp.types.core.CatalogItemDeliveryMetrics` | `core/catalog-item-delivery-metrics.json#` | compat |
| `CatalogItemReferenceNotFoundError` | `adcp.types.core.CatalogItemReferenceNotFoundError` | `core/catalog-item-reference-not-found-error.json#` | compat |
| `CatalogItemStatus` | `adcp.types.enums.CatalogItemStatus` | `enums/catalog-item-status.json#` | compat |
| `CatalogRequirements` | `adcp.types.core.CatalogRequirements` | `core/requirements/catalog-requirements.json#` | compat |
| `CatalogSelection` | `adcp.types.core.CatalogSelection` | `core/catalog-selection.json#` | compat |
| `CatalogType` | `adcp.types.enums.CatalogType` | `enums/catalog-type.json#` | compat |
| `Catchment` | `adcp.types.core.Catchment` | `core/catchment.json#` | compat · **PAYLOAD** |
| `CheckGovernanceRequest` | `adcp.types.governance.CheckGovernanceRequest` | `governance/check-governance-request.json#` | compat |
| `CheckGovernanceResponse` | `adcp.types.governance.CheckGovernanceResponse` | `governance/check-governance-response.json#` | compat |
| `CloudStorageProtocol` | `adcp.types.enums.CloudStorageProtocol` | `enums/cloud-storage-protocol.json#` | compat |
| `CoBrandingRequirement` | `adcp.types.enums.CoBrandingRequirement` | `enums/co-branding-requirement.json#` | compat |
| `Collection` | `adcp.types.core.Collection` | `core/collection.json#` | compat |
| `CollectionCadence` | `adcp.types.enums.CollectionCadence` | `enums/collection-cadence.json#` | compat |
| `CollectionDeliveryMetrics` | `adcp.types.core.CollectionDeliveryMetrics` | `core/collection-delivery-metrics.json#` | compat |
| `CollectionDistribution` | `adcp.types.core.CollectionDistribution` | `core/collection-distribution.json#` | compat |
| `CollectionKind` | `adcp.types.enums.CollectionKind` | `enums/collection-kind.json#` | compat |
| `CollectionList` | `adcp.types.collection.CollectionList` | `collection/collection-list.json#` | compat |
| `CollectionListChangedWebhook` | `adcp.types.collection.CollectionListChangedWebhook` | `collection/collection-list-changed-webhook.json#` | compat |
| `CollectionListFilters` | `adcp.types.collection.CollectionListFilters` | `collection/collection-list-filters.json#` | compat |
| `CollectionListReference` | `adcp.types.core.CollectionListReference` | `core/collection-list-ref.json#` | compat |
| `CollectionPropertyDeliveryMetrics` | `adcp.types.core.CollectionPropertyDeliveryMetrics` | `core/collection-property-delivery-metrics.json#` | compat |
| `CollectionReference` | `adcp.types.core.CollectionReference` | `core/collection-ref.json#` | compat |
| `CollectionRelationship` | `adcp.types.enums.CollectionRelationship` | `enums/collection-relationship.json#` | compat |
| `CollectionSelection` | `adcp.types.core.CollectionSelection` | `core/collection-selection.json#` | compat |
| `CollectionSelector` | `adcp.types.core.CollectionSelector` | `core/collection-selector.json#` | compat |
| `CollectionStatus` | `adcp.types.enums.CollectionStatus` | `enums/collection-status.json#` | compat |
| `CommercialTerms` | `adcp.types.media_buy.CommercialTerms` | `media-buy/commercial-terms.json#` | flat_only |
| `CommittedMetric` | `adcp.types.core.CommittedMetric` | `core/committed-metric.json#` | compat |
| `CompactTaskInputRequired` | `adcp.types.core.CompactTaskInputRequired` | `core/compact-task-input-required.json#` | compat |
| `CompactTaskSubmitted` | `adcp.types.core.CompactTaskSubmitted` | `core/compact-task-submitted.json#` | compat |
| `CompactTaskWorking` | `adcp.types.core.CompactTaskWorking` | `core/compact-task-working.json#` | compat |
| `CompatibilityPurchaseCoordinatorInput` | `adcp.types.media_buy.CompatibilityPurchaseCoordinatorInput` | `media-buy/legacy-purchase-continuation-input.json#` | flat_only |
| `CompletionSource` | `adcp.types.enums.CompletionSource` | `enums/completion-source.json#` | compat |
| `ComplianceTaskCompletionData` | `adcp.types.compliance.ComplianceTaskCompletionData` | `compliance/task-completion-data.json#` | compat |
| `ComplyTestControllerRequest` | `adcp.types.compliance.ComplyTestControllerRequest` | `compliance/comply-test-controller-request.json#` | compat |
| `ComplyTestControllerResponse` | `adcp.types.compliance.ComplyTestControllerResponse` | `compliance/comply-test-controller-response.json#` | compat |
| `ConflictDetails` | `adcp.types.error_details.ConflictDetails` | `error-details/conflict.json#` | flat_only |
| `ConsentBasis` | `adcp.types.enums.ConsentBasis` | `enums/consent-basis.json#` | compat |
| `ContentIdType` | `adcp.types.enums.ContentIDType` | `enums/content-id-type.json#` | compat |
| `ContentRating` | `adcp.types.core.ContentRating` | `core/content-rating.json#` | compat |
| `ContentRatingSystem` | `adcp.types.enums.ContentRatingSystem` | `enums/content-rating-system.json#` | compat |
| `ContextMatchRequest` | `adcp.types.trusted_match.ContextMatchRequest` | `trusted-match/context-match-request.json#` | compat |
| `ContextMatchResponse` | `adcp.types.trusted_match.ContextMatchResponseRouterPublisher` | `trusted-match/context-match-response.json#` | compat |
| `ContextMatchResponseProviderRouter` | `adcp.types.trusted_match.ContextMatchResponseProviderRouter` | `trusted-match/provider-context-match-response.json#` | compat |
| `ContextMatchResponseRouterPublisher` | `adcp.types.trusted_match.ContextMatchResponseRouterPublisher` | `trusted-match/context-match-response.json#` | compat |
| `ControlMediaBuyInputRequired` | `adcp.types.media_buy.ControlMediaBuyInputRequired` | `media-buy/control-media-buy-async-response-input-required.json#` | compat |
| `ControlMediaBuyRequest` | `adcp.types.media_buy.ControlMediaBuyRequest` | `media-buy/control-media-buy-request.json#` | flat_only |
| `ControlMediaBuyResponse` | `adcp.types.media_buy.ControlMediaBuyResponse` | `media-buy/control-media-buy-response.json#` | flat_only |
| `ControlMediaBuySubmitted` | `adcp.types.media_buy.ControlMediaBuySubmitted` | `media-buy/control-media-buy-async-response-submitted.json#` | compat |
| `ControlMediaBuyWorking` | `adcp.types.media_buy.ControlMediaBuyWorking` | `media-buy/control-media-buy-async-response-working.json#` | compat |
| `CountryFusedPostalCodeSystem` | `adcp.types.enums.CountryFusedPostalCodeSystem` | `enums/legacy-postal-system.json#` | compat |
| `CpaPricingOption` | `adcp.types.pricing_options.CPAPricingOption` | `pricing-options/cpa-option.json#` | compat |
| `CpcPricingOption` | `adcp.types.pricing_options.CPCPricingOption` | `pricing-options/cpc-option.json#` | compat |
| `CpcvPricingOption` | `adcp.types.pricing_options.CPCVPricingOption` | `pricing-options/cpcv-option.json#` | compat |
| `CpmAuctionPricingOption` | `adcp.types.pricing_options.CPMPricingOption` | `pricing-options/cpm-option.json#` | _adapter |
| `CpmFixedRatePricingOption` | `adcp.types.pricing_options.CPMPricingOption` | `pricing-options/cpm-option.json#` | _adapter |
| `CpmPricingOption` | `adcp.types.pricing_options.CPMPricingOption` | `pricing-options/cpm-option.json#` | compat |
| `CppPricingOption` | `adcp.types.pricing_options.CPPPricingOption` | `pricing-options/cpp-option.json#` | compat |
| `CpvPricingOption` | `adcp.types.pricing_options.CPVPricingOption` | `pricing-options/cpv-option.json#` | compat |
| `CreateCollectionListRequest` | `adcp.types.collection.CreateCollectionListRequest` | `collection/create-collection-list-request.json#` | compat |
| `CreateCollectionListResponse` | `adcp.types.collection.CreateCollectionListResponse` | `collection/create-collection-list-response.json#` | compat |
| `CreateContentStandardsRequest` | `adcp.types.content_standards.CreateContentStandardsRequest` | `content-standards/create-content-standards-request.json#` | compat |
| `CreateContentStandardsResponse` | `adcp.types.content_standards.CreateContentStandardsResponse` | `content-standards/create-content-standards-response.json#` | compat |
| `CreateMediaBuyInputRequired` | `adcp.types.media_buy.CreateMediaBuyInputRequired` | `media-buy/create-media-buy-async-response-input-required.json#` | compat |
| `CreateMediaBuyRequest` | `adcp.types.media_buy.CreateMediaBuyRequest` | `media-buy/create-media-buy-request.json#` | flat_only |
| `CreateMediaBuySubmitted` | `adcp.types.media_buy.CreateMediaBuySubmitted` | `media-buy/create-media-buy-async-response-submitted.json#` | compat |
| `CreateMediaBuyWorking` | `adcp.types.media_buy.CreateMediaBuyWorking` | `media-buy/create-media-buy-async-response-working.json#` | compat |
| `CreatePropertyListRequest` | `adcp.types.property.CreatePropertyListRequest` | `property/create-property-list-request.json#` | compat |
| `CreatePropertyListResponse` | `adcp.types.property.CreatePropertyListResponse` | `property/create-property-list-response.json#` | compat |
| `CreativeAction` | `adcp.types.enums.CreativeAction` | `enums/creative-action.json#` | compat |
| `CreativeActivationMethod` | `adcp.types.enums.CreativeActivationMethod` | `enums/activation-method.json#` | compat |
| `CreativeAgentCapability` | `adcp.types.enums.CreativeAgentCapability` | `enums/creative-agent-capability.json#` | compat |
| `CreativeApprovalRequest` | `adcp.types.brand.CreativeApprovalRequest` | `brand/creative-approval-request.json#` | compat |
| `CreativeApprovalResponse` | `adcp.types.brand.CreativeApprovalResponse` | `brand/creative-approval-response.json#` | compat |
| `CreativeApprovalStatus` | `adcp.types.enums.CreativeApprovalStatus` | `enums/creative-approval-status.json#` | compat |
| `CreativeAssignment` | `adcp.types.core.CreativeAssignment` | `core/creative-assignment.json#` | compat |
| `CreativeAssignmentChangedWebhook` | `adcp.types.creative.CreativeAssignmentChangedWebhook` | `creative/creative-assignment-changed-webhook.json#` | compat |
| `CreativeAuditObservation` | `adcp.types.creative.CreativeAuditObservation` | `creative/audit-observation.json#` | compat |
| `CreativeBrief` | `adcp.types.core.CreativeBrief` | `core/creative-brief.json#` | compat |
| `CreativeConsumption` | `adcp.types.core.CreativeConsumption` | `core/creative-consumption.json#` | compat |
| `CreativeDeliveryMetrics` | `adcp.types.core.CreativeDeliveryMetrics` | `core/creative-delivery-metrics.json#` | compat |
| `CreativeEventReasonCode` | `adcp.types.enums.CreativeEventReasonCode` | `enums/creative-event-reason-code.json#` | compat |
| `CreativeFeatureResult` | `adcp.types.creative.CreativeFeatureResult` | `creative/creative-feature-result.json#` | compat |
| `CreativeIdentifierType` | `adcp.types.enums.CreativeIdentifierType` | `enums/creative-identifier-type.json#` | compat |
| `CreativeItem` | `adcp.types.core.CreativeItem` | `core/creative-item.json#` | compat |
| `CreativeLocalePolicy` | `adcp.types.core.CreativeLocalePolicy` | `core/creative-locale-policy.json#` | compat |
| `CreativeLocalization` | `adcp.types.core.CreativeLocalization` | `core/creative-localization.json#` | compat |
| `CreativeLocalizationReadback` | `adcp.types.core.CreativeLocalizationReadback` | `core/creative-localization-readback.json#` | compat |
| `CreativeMotionLevel` | `adcp.types.enums.CreativeMotionLevel` | `enums/motion-level.json#` | compat |
| `CreativeOperationFormatDeclaration` | `adcp.types.core.CreativeOperationFormatDeclaration` | `core/creative-operation-format-declaration.json#` | compat |
| `CreativePolicy` | `adcp.types.core.CreativePolicy` | `core/creative-policy.json#` | compat |
| `CreativePurgedWebhook` | `adcp.types.creative.CreativePurgedWebhook` | `creative/creative-purged-webhook.json#` | compat |
| `CreativeQuality` | `adcp.types.enums.CreativeQuality` | `enums/creative-quality.json#` | compat |
| `CreativeRejectedDetails` | `adcp.types.error_details.CreativeRejectedDetails` | `error-details/creative-rejected.json#` | flat_only |
| `CreativeRepresentation` | `adcp.types.core.CreativeRepresentation` | `core/creative-representation.json#` | compat |
| `CreativeRepresentationSet` | `adcp.types.core.CreativeRepresentationSet` | `core/creative-representation-set.json#` | compat |
| `CreativeRepresentationUnresolvedDetails` | `adcp.types.error_details.CreativeRepresentationUnresolvedDetails` | `error-details/creative-representation-unresolved.json#` | flat_only |
| `CreativeRevisionContentMismatchDetails` | `adcp.types.error_details.CreativeRevisionContentMismatchDetails` | `error-details/creative-revision-content-mismatch.json#` | flat_only |
| `CreativeSelectionStrategy` | `adcp.types.enums.CreativeSelectionStrategy` | `enums/creative-selection-strategy.json#` | compat |
| `CreativeSortField` | `adcp.types.enums.CreativeSortField` | `enums/creative-sort-field.json#` | compat |
| `CreativeStatus` | `adcp.types.enums.CreativeStatus` | `enums/creative-status.json#` | compat |
| `CreativeStatusChangedWebhook` | `adcp.types.creative.CreativeStatusChangedWebhook` | `creative/creative-status-changed-webhook.json#` | compat |
| `CreativeVariable` | `adcp.types.core.CreativeVariable` | `core/creative-variable.json#` | compat |
| `CssAsset` | `adcp.types.core.CSSAsset` | `core/assets/css-asset.json#` | compat |
| `CssAssetRequirements` | `adcp.types.core.CSSAssetRequirements` | `core/requirements/css-asset-requirements.json#` | compat |
| `CssContent` | `adcp.types.core.CSSAsset` | `core/assets/css-asset.json#` | _adapter |
| `CtvAdExperience` | `adcp.types.enums.CTVAdExperience` | `enums/ctv-ad-experience.json#` | compat |
| `DaastAsset` | `adcp.types.core.DAASTAsset` | `core/assets/daast-asset.json#` | compat |
| `DaastAssetRequirements` | `adcp.types.core.DAASTAssetRequirements` | `core/requirements/daast-asset-requirements.json#` | compat |
| `DaastTrackerAsset` | `adcp.types.core.DAASTTrackerAsset` | `core/assets/daast-tracker-asset.json#` | compat |
| `DaastTrackerConstraints` | `adcp.types.core.DAASTTrackerConstraints` | `core/daast-tracker-constraints.json#` | compat |
| `DaastTrackingEvent` | `adcp.types.enums.DAASTTrackingEvent` | `enums/daast-tracking-event.json#` | compat |
| `DaastVersion` | `adcp.types.enums.DAASTVersion` | `enums/daast-version.json#` | compat |
| `DataProviderSignalSelector` | `adcp.types.core.DataProviderSignalSelector` | `core/data-provider-signal-selector.json#` | compat |
| `DateRange` | `adcp.types.core.DateRange` | `core/date-range.json#` | compat |
| `DatetimeRange` | `adcp.types.core.DatetimeRange` | `core/datetime-range.json#` | compat |
| `DayOfWeek` | `adcp.types.enums.DayOfWeek` | `enums/day-of-week.json#` | compat |
| `DaypartTarget` | `adcp.types.core.DaypartTarget` | `core/daypart-target.json#` | compat |
| `DaypartTimezoneMode` | `adcp.types.enums.DaypartTimezoneMode` | `enums/daypart-timezone-mode.json#` | compat |
| `DeadlinePolicy` | `adcp.types.core.DeadlinePolicy` | `core/deadline-policy.json#` | compat |
| `DeclineProposalsInputRequired` | `adcp.types.media_buy.DeclineProposalsInputRequired` | `media-buy/decline-proposals-async-response-input-required.json#` | compat |
| `DeclineProposalsRequest` | `adcp.types.media_buy.DeclineProposalsRequest` | `media-buy/decline-proposals-request.json#` | flat_only |
| `DeclineProposalsResponse` | `adcp.types.media_buy.DeclineProposalsResponse` | `media-buy/decline-proposals-response.json#` | flat_only |
| `DeclineProposalsSubmitted` | `adcp.types.media_buy.DeclineProposalsSubmitted` | `media-buy/decline-proposals-async-response-submitted.json#` | compat |
| `DeclineProposalsWorking` | `adcp.types.media_buy.DeclineProposalsWorking` | `media-buy/decline-proposals-async-response-working.json#` | compat |
| `DelegationAuthority` | `adcp.types.enums.DelegationAuthority` | `enums/delegation-authority.json#` | compat |
| `DeleteCollectionListRequest` | `adcp.types.collection.DeleteCollectionListRequest` | `collection/delete-collection-list-request.json#` | compat |
| `DeleteCollectionListResponse` | `adcp.types.collection.DeleteCollectionListResponse` | `collection/delete-collection-list-response.json#` | compat |
| `DeletePropertyListRequest` | `adcp.types.property.DeletePropertyListRequest` | `property/delete-property-list-request.json#` | compat |
| `DeletePropertyListResponse` | `adcp.types.property.DeletePropertyListResponse` | `property/delete-property-list-response.json#` | compat |
| `DeliveryBreakdownControls` | `adcp.types.core.DeliveryBreakdownControls` | `core/delivery-breakdown-controls.json#` | compat |
| `DeliveryForecast` | `adcp.types.core.DeliveryForecast` | `core/delivery-forecast.json#` | compat |
| `DeliveryMeasurement` | `adcp.types.core.ProductDeliveryMeasurement` | `core/product.json#/properties/delivery_measurement` | _adapter |
| `DeliveryMetricAggregate` | `adcp.types.core.DeliveryMetricAggregate` | `core/delivery-metric-aggregate.json#` | compat |
| `DeliveryMetrics` | `adcp.types.core.DeliveryMetrics` | `core/delivery-metrics.json#` | compat |
| `DeliveryProvider` | `adcp.types.core.DeliveryProvider` | `core/delivery-provider.json#` | compat |
| `DeliveryRecipient` | `adcp.types.core.DeliveryRecipient` | `core/delivery-recipient.json#` | compat |
| `DeliveryRecipientCloud` | `adcp.types.enums.DeliveryRecipientCloud` | `enums/delivery-recipient-cloud.json#` | compat |
| `DeliveryRecord` | `adcp.types.property.DeliveryRecord` | `property/delivery-record.json#` | compat |
| `DeliveryStatus` | `adcp.types.enums.DeliveryStatus` | `enums/delivery-status.json#` | compat |
| `DeliveryType` | `adcp.types.enums.DeliveryType` | `enums/delivery-type.json#` | compat |
| `DemographicAgeRange` | `adcp.types.core.DemographicAgeRange` | `core/demographic-age-range.json#` | compat |
| `DemographicPredicate` | `adcp.types.core.DemographicPredicate` | `core/demographic-predicate.json#` | compat |
| `DemographicReportingCapability` | `adcp.types.core.DemographicReportingCapability` | `core/demographic-reporting-capability.json#` | compat |
| `DemographicSystem` | `adcp.types.enums.DemographicSystem` | `enums/demographic-system.json#` | compat |
| `DemographicTargetingCapability` | `adcp.types.core.DemographicTargetingCapability` | `core/demographic-targeting-capability.json#` | compat |
| `DemographicTargetingIntent` | `adcp.types.core.DemographicTargetingIntent` | `core/demographic-targeting-intent.json#` | compat |
| `DemographicTargetingResolution` | `adcp.types.core.DemographicTargetingResolution` | `core/demographic-targeting-resolution.json#` | compat |
| `Deployment` | `adcp.types.core.Deployment` | `core/deployment.json#` | compat |
| `DerivativeType` | `adcp.types.enums.DerivativeType` | `enums/derivative-type.json#` | compat |
| `Destination` | `adcp.types.core.Destination` | `core/destination.json#` | compat |
| `DestinationItem` | `adcp.types.core.DestinationItem` | `core/destination-item.json#` | compat |
| `DevicePlatform` | `adcp.types.enums.DevicePlatform` | `enums/device-platform.json#` | compat |
| `DevicePlatformForecastDimension` | `adcp.types.core.DevicePlatformForecastDimension` | `core/forecast-dimension-device-platform.json#` | compat |
| `DeviceType` | `adcp.types.enums.DeviceType` | `enums/device-type.json#` | compat |
| `DeviceTypeForecastDimension` | `adcp.types.core.DeviceTypeForecastDimension` | `core/forecast-dimension-device-type.json#` | compat |
| `DiagnosticIssue` | `adcp.types.core.DiagnosticIssue` | `core/diagnostic-issue.json#` | compat |
| `DigitalSourceType` | `adcp.types.enums.DigitalSourceType` | `enums/digital-source-type.json#` | compat |
| `DimensionUnit` | `adcp.types.enums.DimensionUnit` | `enums/dimension-unit.json#` | compat |
| `DisclosurePersistence` | `adcp.types.enums.DisclosurePersistence` | `enums/disclosure-persistence.json#` | compat |
| `DisclosurePosition` | `adcp.types.enums.DisclosurePosition` | `enums/disclosure-position.json#` | compat |
| `DisplayTagAsset` | `adcp.types.core.DisplayTagAsset` | `core/assets/display-tag-asset.json#` | compat |
| `DistanceUnit` | `adcp.types.enums.DistanceUnit` | `enums/distance-unit.json#` | compat |
| `DistributionIdentifierType` | `adcp.types.enums.DistributionIdentifierType` | `enums/distribution-identifier-type.json#` | compat |
| `DoohMotionType` | `adcp.types.enums.DOOHMotionType` | `enums/dooh-motion-type.json#` | compat |
| `DownstreamConnectionRequirement` | `adcp.types.core.DownstreamConnectionRequirement` | `core/downstream-connection-requirement.json#` | compat |
| `Duration` | `adcp.types.core.Duration` | `core/duration.json#` | compat |
| `EducationItem` | `adcp.types.core.EducationItem` | `core/education-item.json#` | compat |
| `EffectiveTimingChangeConstraints` | `adcp.types.media_buy.EffectiveTimingConstraints` | `media-buy/change-term-constraints.json#/oneOf/3` | _adapter |
| `EmbeddedProvenanceMethod` | `adcp.types.enums.EmbeddedProvenanceMethod` | `enums/embedded-provenance-method.json#` | compat |
| `Error` | `adcp.types.core.Error` | `core/error.json#` | compat |
| `ErrorCode` | `adcp.types.enums.ErrorCode` | `enums/error-code.json#` | compat |
| `ErrorScope` | `adcp.types.enums.ErrorScope` | `enums/error-scope.json#` | compat |
| `EscalationSeverity` | `adcp.types.enums.EscalationSeverity` | `enums/escalation-severity.json#` | compat |
| `EvaluatorSpec` | `adcp.types.core.EvaluatorSpec` | `core/evaluator-spec.json#` | compat |
| `Event` | `adcp.types.core.Event` | `core/event.json#` | compat |
| `EventCustomData` | `adcp.types.core.EventCustomData` | `core/event-custom-data.json#` | compat |
| `EventSourceHealth` | `adcp.types.core.EventSourceHealth` | `core/event-source-health.json#` | compat |
| `EventSurface` | `adcp.types.core.EventSurface` | `core/event-surface.json#` | compat |
| `EventType` | `adcp.types.enums.EventType` | `enums/event-type.json#` | compat |
| `ExecutionRequirementUnmetDetails` | `adcp.types.error_details.ExecutionRequirementUnmetDetails` | `error-details/execution-requirement-unmet.json#` | flat_only |
| `FeatureCheckStatus` | `adcp.types.enums.FeatureCheckStatus` | `enums/feature-check-status.json#` | compat |
| `FeatureRequirement` | `adcp.types.core.FeatureRequirement` | `core/feature-requirement.json#` | compat |
| `FeedFormat` | `adcp.types.enums.FeedFormat` | `enums/feed-format.json#` | compat |
| `FeedbackSource` | `adcp.types.enums.FeedbackSource` | `enums/feedback-source.json#` | compat |
| `FlatRatePricingOption` | `adcp.types.pricing_options.FlatRatePricingOption` | `pricing-options/flat-rate-option.json#` | compat |
| `FlightChangeConstraints` | `adcp.types.media_buy.FlightChangeConstraints` | `media-buy/change-term-constraints.json#/oneOf/1` | flat_only |
| `FlightItem` | `adcp.types.core.FlightItem` | `core/flight-item.json#` | compat |
| `ForecastMethod` | `adcp.types.enums.ForecastMethod` | `enums/forecast-method.json#` | compat |
| `ForecastPoint` | `adcp.types.core.ForecastPoint` | `core/forecast-point.json#` | compat |
| `ForecastPointDimensions` | `adcp.types.core.ForecastPointDimensions` | `core/forecast-point-dimensions.json#` | compat |
| `ForecastRange` | `adcp.types.core.ForecastRange` | `core/forecast-range.json#` | compat |
| `ForecastRangeUnit` | `adcp.types.enums.ForecastRangeUnit` | `enums/forecast-range-unit.json#` | compat |
| `ForecastRateRange` | `adcp.types.core.ForecastRateRange` | `core/forecast-rate-range.json#` | compat |
| `ForecastVendorMetricValue` | `adcp.types.core.ForecastVendorMetricValue` | `core/forecast-vendor-metric-value.json#` | compat |
| `ForecastableMetric` | `adcp.types.enums.ForecastableMetric` | `enums/forecastable-metric.json#` | compat |
| `FormatCard` | `adcp.types.core.FormatFormatCard` | `core/format.json#/properties/format_card` | _adapter |
| `FormatId` | `adcp.types.core.FormatReferenceStructuredObject` | `core/format-id.json#` | compat |
| `FormatIdParameter` | `adcp.types.enums.FormatIDParameter` | `enums/format-id-parameter.json#` | compat |
| `FormatOptionReference` | `adcp.types.core.FormatOptionReference` | `core/format-option-ref.json#` | compat |
| `FormatReferenceStructuredObject` | `adcp.types.core.FormatReferenceStructuredObject` | `core/format-id.json#` | compat |
| `FrameRateType` | `adcp.types.enums.FrameRateType` | `enums/frame-rate-type.json#` | compat |
| `FrequencyCap` | `adcp.types.core.FrequencyCap` | `core/frequency-cap.json#` | compat |
| `FrequencyCapConstraints` | `adcp.types.core.FrequencyCapConstraints` | `core/frequency-cap-constraints.json#` | compat |
| `FrequencyCapControlMode` | `adcp.types.enums.FrequencyCapControlMode` | `enums/frequency-cap-control-mode.json#` | compat |
| `FrequencyCapDurationUnit` | `adcp.types.core.FrequencyCapDurationUnit` | `core/frequency-cap-duration-unit.json#` | compat |
| `FrequencyCapImpressionConstraints` | `adcp.types.core.FrequencyCapImpressionConstraints` | `core/frequency-cap-impression-constraints.json#` | compat · **PAYLOAD** |
| `FrequencyCapIntervalConstraints` | `adcp.types.core.FrequencyCapIntervalConstraints` | `core/frequency-cap-interval-constraints.json#` | compat · **PAYLOAD** |
| `FrequencyCapMutableField` | `adcp.types.enums.FrequencyCapMutableField` | `enums/frequency-cap-mutable-field.json#` | compat |
| `FrequencyCapRequirements` | `adcp.types.core.FrequencyCapRequirements` | `core/frequency-cap-requirements.json#` | compat |
| `FrequencyCapScope` | `adcp.types.enums.FrequencyCapScope` | `enums/frequency-cap-scope.json#` | compat |
| `GeneratedTaskStatus` | `adcp.types.enums.TaskStatus` | `enums/task-status.json#` | _adapter |
| `GenerationCredential` | `adcp.types.core.GenerationCredential` | `core/generation-credential.json#` | compat |
| `GenreTaxonomy` | `adcp.types.enums.GenreTaxonomy` | `enums/genre-taxonomy.json#` | compat |
| `GeoDeliveryMetrics` | `adcp.types.core.GeoDeliveryMetrics` | `core/geo-delivery-metrics.json#` | compat |
| `GeoForecastDimension` | `adcp.types.core.GeoForecastDimension` | `core/forecast-dimension-geo.json#` | compat |
| `GeoMetro` | `adcp.types.core.GeoMetro` | `core/geo-metro.json#` | compat |
| `GeographicBreakdownSupport` | `adcp.types.core.GeographicBreakdownSupport` | `core/geo-breakdown-support.json#` | compat |
| `GeographicPlaceArea` | `adcp.types.core.GeographicPlaceArea` | `core/geo-place-area.json#` | compat |
| `GeographicPlaceCatalogCapability` | `adcp.types.core.GeographicPlaceCatalogCapability` | `core/geo-place-catalog-capability.json#` | compat |
| `GeographicPlaceCatalogEntry` | `adcp.types.core.GeographicPlaceCatalogEntry` | `core/geo-place-catalog-entry.json#` | compat |
| `GeographicPlaceRequirement` | `adcp.types.core.GeographicPlaceRequirement` | `core/geo-place-requirement.json#` | compat |
| `GeographicPlaceResolver` | `adcp.types.core.GeographicPlaceResolver` | `core/geo-place-resolver.json#` | compat |
| `GeographicPlaceSystemSupport` | `adcp.types.core.GeographicPlaceSystemSupport` | `core/geo-place-support.json#` | compat |
| `GeographicRegionRequirement` | `adcp.types.core.GeographicRegionRequirement` | `core/geo-region-requirement.json#` | compat |
| `GeographicRegionSupport` | `adcp.types.core.GeographicRegionSupport` | `core/geo-region-support.json#` | compat |
| `GeographicTargetingLevel` | `adcp.types.enums.GeographicTargetingLevel` | `enums/geo-level.json#` | compat |
| `GetAccountFinancialsRequest` | `adcp.types.account.GetAccountFinancialsRequest` | `account/get-account-financials-request.json#` | compat |
| `GetAccountFinancialsResponse` | `adcp.types.account.GetAccountFinancialsResponse` | `account/get-account-financials-response.json#` | compat |
| `GetAdcpCapabilitiesRequest` | `adcp.types.protocol.GetAdCPCapabilitiesRequest` | `protocol/get-adcp-capabilities-request.json#` | compat |
| `GetAdcpCapabilitiesResponse` | `adcp.types.protocol.GetAdCPCapabilitiesResponse` | `protocol/get-adcp-capabilities-response.json#` | compat |
| `GetBrandIdentityRequest` | `adcp.types.brand.GetBrandIdentityRequest` | `brand/get-brand-identity-request.json#` | compat |
| `GetBrandIdentityResponse` | `adcp.types.brand.GetBrandIdentityResponse` | `brand/get-brand-identity-response.json#` | compat |
| `GetBrandIdentitySuccessResponse` | `adcp.types.brand.GetBrandIdentitySuccess` | `brand/get-brand-identity-response.json#/oneOf/0` | _adapter |
| `GetCollectionListRequest` | `adcp.types.collection.GetCollectionListRequest` | `collection/get-collection-list-request.json#` | compat |
| `GetCollectionListResponse` | `adcp.types.collection.GetCollectionListResponse` | `collection/get-collection-list-response.json#` | compat |
| `GetContentStandardsRequest` | `adcp.types.content_standards.GetContentStandardsRequest` | `content-standards/get-content-standards-request.json#` | compat |
| `GetContentStandardsResponse` | `adcp.types.content_standards.GetContentStandardsResponse` | `content-standards/get-content-standards-response.json#` | compat |
| `GetCreativeDeliveryRequest` | `adcp.types.creative.GetCreativeDeliveryRequest` | `creative/get-creative-delivery-request.json#` | compat |
| `GetCreativeFeaturesComplianceCompletion` | `adcp.types.compliance.GetCreativeFeaturesComplianceCompletion` | `compliance/get-creative-features-completion.json#` | compat |
| `GetCreativeFeaturesRequest` | `adcp.types.creative.GetCreativeFeaturesRequest` | `creative/get-creative-features-request.json#` | flat_only |
| `GetCreativeFeaturesResponse` | `adcp.types.creative.GetCreativeFeaturesResponse` | `creative/get-creative-features-response.json#` | flat_only |
| `GetCreativeFeaturesSubmitted` | `adcp.types.creative.GetCreativeFeaturesSubmitted` | `creative/get-creative-features-async-response-submitted.json#` | compat |
| `GetCreativeFeaturesSuccess` | `adcp.types.creative.GetCreativeFeaturesSuccess` | `creative/get-creative-features-terminal-success.json#` | compat |
| `GetGeographicPlaceResolutionRequest` | `adcp.types.core.GetGeographicPlaceResolutionRequest` | `core/get-geo-place-resolution-request.json#` | compat |
| `GetGeographicPlaceResolutionResponse` | `adcp.types.core.GetGeographicPlaceResolutionResponse` | `core/get-geo-place-resolution-response.json#` | compat |
| `GetMediaBuyArtifactsRequest` | `adcp.types.content_standards.GetMediaBuyArtifactsRequest` | `content-standards/get-media-buy-artifacts-request.json#` | compat |
| `GetMediaBuyArtifactsResponse` | `adcp.types.content_standards.GetMediaBuyArtifactsResponse` | `content-standards/get-media-buy-artifacts-response.json#` | compat |
| `GetMediaBuyDeliveryRequest` | `adcp.types.media_buy.GetMediaBuyDeliveryRequest` | `media-buy/get-media-buy-delivery-request.json#` | flat_only |
| `GetMediaBuysRequest` | `adcp.types.media_buy.GetMediaBuysRequest` | `media-buy/get-media-buys-request.json#` | flat_only |
| `GetPlanAuditLogsRequest` | `adcp.types.governance.GetPlanAuditLogsRequest` | `governance/get-plan-audit-logs-request.json#` | compat |
| `GetPlanAuditLogsResponse` | `adcp.types.governance.GetPlanAuditLogsResponse` | `governance/get-plan-audit-logs-response.json#` | compat |
| `GetPrincipalRequest` | `adcp.types.protocol.GetPrincipalRequest` | `protocol/get-principal-request.json#` | flat_only |
| `GetPrincipalResponse` | `adcp.types.protocol.GetPrincipalResponse` | `protocol/get-principal-response.json#` | flat_only |
| `GetProductsInputRequired` | `adcp.types.media_buy.GetProductsInputRequired` | `media-buy/get-products-async-response-input-required.json#` | compat |
| `GetProductsRejected` | `adcp.types.media_buy.GetProductsRejected` | `media-buy/get-products-rejected.json#` | compat |
| `GetProductsSubmitted` | `adcp.types.media_buy.GetProductsSubmitted` | `media-buy/get-products-async-response-submitted.json#` | compat |
| `GetProductsWorking` | `adcp.types.media_buy.GetProductsWorking` | `media-buy/get-products-async-response-working.json#` | compat |
| `GetPropertyListRequest` | `adcp.types.property.GetPropertyListRequest` | `property/get-property-list-request.json#` | compat |
| `GetPropertyListResponse` | `adcp.types.property.GetPropertyListResponse` | `property/get-property-list-response.json#` | compat |
| `GetReportingStatusRequest` | `adcp.types.media_buy.GetReportingStatusRequest` | `media-buy/get-reporting-status-request.json#` | compat |
| `GetReportingStatusResponse` | `adcp.types.media_buy.GetReportingStatusResponse` | `media-buy/get-reporting-status-response.json#` | compat |
| `GetRightsRequest` | `adcp.types.brand.GetRightsRequest` | `brand/get-rights-request.json#` | compat |
| `GetRightsResponse` | `adcp.types.brand.GetRightsResponse` | `brand/get-rights-response.json#` | compat |
| `GetRightsSuccessResponse` | `adcp.types.brand.GetRightsSuccess` | `brand/get-rights-response.json#/oneOf/0` | _adapter |
| `GetSignalsDiscoveryRequest` | `adcp.types.signals.GetSignalsRequest` | `signals/get-signals-request.json#` | _adapter |
| `GetSignalsLookupRequest` | `adcp.types.signals.GetSignalsRequest` | `signals/get-signals-request.json#` | _adapter |
| `GetSignalsRequest` | `adcp.types.signals.GetSignalsRequest` | `signals/get-signals-request.json#` | flat_only |
| `GetSignalsResponse` | `adcp.types.signals.GetSignalsResponse` | `signals/get-signals-response.json#` | flat_only |
| `GetSignalsSubmitted` | `adcp.types.signals.GetSignalsSubmitted` | `signals/get-signals-async-response-submitted.json#` | compat |
| `GetSignalsWorking` | `adcp.types.signals.GetSignalsWorking` | `signals/get-signals-async-response-working.json#` | compat |
| `GetTaskStatusRequest` | `adcp.types.protocol.GetTaskStatusRequest` | `protocol/get-task-status-request.json#` | flat_only |
| `GetTaskStatusResponse` | `adcp.types.protocol.GetTaskStatusResponse` | `protocol/get-task-status-response.json#` | flat_only |
| `GopType` | `adcp.types.enums.GOPType` | `enums/gop-type.json#` | compat |
| `GovernanceAgent` | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItem` | `account/sync-governance-request.json#/properties/accounts/items/properties/governance_agents/items` | _adapter |
| `GovernanceAgentNotAcceptedDetails` | `adcp.types.error_details.GovernanceAgentNotAcceptedDetails` | `error-details/governance-agent-not-accepted.json#` | flat_only |
| `GovernanceDecision` | `adcp.types.enums.GovernanceDecision` | `enums/governance-decision.json#` | compat |
| `GovernanceDomain` | `adcp.types.enums.GovernanceDomain` | `enums/governance-domain.json#` | compat |
| `GovernanceMode` | `adcp.types.enums.GovernanceMode` | `enums/governance-mode.json#` | compat |
| `GovernancePhase` | `adcp.types.enums.GovernancePhase` | `enums/governance-phase.json#` | compat |
| `HistoryEntryType` | `adcp.types.enums.HistoryEntryType` | `enums/history-entry-type.json#` | compat |
| `HotelItem` | `adcp.types.core.HotelItem` | `core/hotel-item.json#` | compat |
| `HtmlAsset` | `adcp.types.core.HTMLAsset` | `core/assets/html-asset.json#` | compat |
| `HtmlAssetRequirements` | `adcp.types.core.HTMLAssetRequirements` | `core/requirements/html-asset-requirements.json#` | compat |
| `HtmlContent` | `adcp.types.core.HTMLAsset` | `core/assets/html-asset.json#` | _adapter |
| `HttpMethod` | `adcp.types.enums.HTTPMethod` | `enums/http-method.json#` | compat |
| `IdempotencySupported` | `adcp.types.protocol.IdempotencySupported` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/idempotency/oneOf/0` | compat |
| `IdempotencyUnsupported` | `adcp.types.protocol.IdempotencyUnsupported` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/idempotency/oneOf/1` | compat |
| `Identifier` | `adcp.types.core.Identifier` | `core/identifier.json#` | compat |
| `IdentityMatchRequest` | `adcp.types.trusted_match.IdentityMatchRequest` | `trusted-match/identity-match-request.json#` | compat |
| `IdentityMatchResponse` | `adcp.types.trusted_match.IdentityMatchResponseRouterPublisher` | `trusted-match/identity-match-response.json#` | compat |
| `IdentityMatchResponseProviderRouter` | `adcp.types.trusted_match.IdentityMatchResponseProviderRouter` | `trusted-match/provider-identity-match-response.json#` | compat |
| `IdentityMatchResponseRouterPublisher` | `adcp.types.trusted_match.IdentityMatchResponseRouterPublisher` | `trusted-match/identity-match-response.json#` | compat |
| `ImageAsset` | `adcp.types.core.ImageAsset` | `core/assets/image-asset.json#` | compat |
| `ImageAssetRequirements` | `adcp.types.core.ImageAssetRequirements` | `core/requirements/image-asset-requirements.json#` | compat |
| `ImageContent` | `adcp.types.core.ImageAsset` | `core/assets/image-asset.json#` | _adapter |
| `Impairment` | `adcp.types.core.Impairment` | `core/impairment.json#` | compat |
| `ImpairmentOfflineState` | `adcp.types.enums.ImpairmentOfflineState` | `enums/impairment-offline-state.json#` | compat |
| `ImpairmentReasonCode` | `adcp.types.enums.ImpairmentReasonCode` | `enums/impairment-reason-code.json#` | compat |
| `Indicator` | `adcp.types.core.Indicator` | `core/indicator.json#` | compat |
| `IndicatorBearingResourceState` | `adcp.types.core.IndicatorBearingResourceState` | `core/indicator-bearing.json#` | compat |
| `IndicatorScope` | `adcp.types.core.IndicatorScope` | `core/indicator-scope.json#` | compat |
| `IndicatorType` | `adcp.types.enums.IndicatorType` | `enums/indicator-type.json#` | compat |
| `IndicatorsChangedWebhook` | `adcp.types.core.IndicatorsChangedWebhook` | `core/indicators-changed-webhook.json#` | compat |
| `IndustryIdentifier` | `adcp.types.core.IndustryIdentifier` | `core/industry-identifier.json#` | compat |
| `InsertionOrder` | `adcp.types.core.InsertionOrder` | `core/insertion-order.json#` | compat |
| `Installment` | `adcp.types.core.Installment` | `core/installment.json#` | compat |
| `InstallmentDeadlines` | `adcp.types.core.InstallmentDeadlines` | `core/installment-deadlines.json#` | compat |
| `InstallmentDeliveryMetrics` | `adcp.types.core.InstallmentDeliveryMetrics` | `core/installment-delivery-metrics.json#` | compat |
| `InstallmentPropertyDeliveryMetrics` | `adcp.types.core.InstallmentPropertyDeliveryMetrics` | `core/installment-property-delivery-metrics.json#` | compat |
| `InstallmentReference` | `adcp.types.core.InstallmentReference` | `core/installment-ref.json#` | compat |
| `InstallmentStatus` | `adcp.types.enums.InstallmentStatus` | `enums/installment-status.json#` | compat |
| `InventoryListApplication` | `adcp.types.core.InventoryListApplication` | `core/inventory-list-application.json#` | compat |
| `JavascriptAsset` | `adcp.types.core.JavaScriptAsset` | `core/assets/javascript-asset.json#` | compat |
| `JavascriptAssetRequirements` | `adcp.types.core.JavaScriptAssetRequirements` | `core/requirements/javascript-asset-requirements.json#` | compat |
| `JavascriptContent` | `adcp.types.core.JavaScriptAsset` | `core/assets/javascript-asset.json#` | _adapter |
| `JavascriptModuleType` | `adcp.types.enums.JavaScriptModuleType` | `enums/javascript-module-type.json#` | compat |
| `JobItem` | `adcp.types.core.JobItem` | `core/job-item.json#` | compat |
| `KeywordDeliveryMetrics` | `adcp.types.core.KeywordDeliveryMetrics` | `core/keyword-delivery-metrics.json#` | compat |
| `KeywordTarget` | `adcp.types.core.KeywordTarget` | `core/keyword-target.json#` | compat |
| `LandingPageRequirement` | `adcp.types.enums.LandingPageRequirement` | `enums/landing-page-requirement.json#` | compat |
| `Language` | `adcp.types.protocol.Language` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/execution/properties/targeting/properties/language/oneOf/1` | compat |
| `LegacyBuildCreativeErrorResponse` | `adcp.types.media_buy.BuildCreativeMultiSuccess` | `media-buy/build-creative-response.json#/oneOf/1` | _adapter |
| `LegacyBuildCreativeRequest` | `adcp.types.media_buy.BuildCreativeRequest` | `media-buy/build-creative-request.json#` | _adapter |
| `LegacyBuildCreativeResponse` | `adcp.types.media_buy.BuildCreativeResponse` | `media-buy/build-creative-response.json#` | _adapter |
| `LegacyBuildCreativeResponse1` | `adcp.types.media_buy.BuildCreativeSuccess` | `media-buy/build-creative-response.json#/oneOf/0` | _adapter |
| `LegacyBuildCreativeResponse2` | `adcp.types.media_buy.BuildCreativeMultiSuccess` | `media-buy/build-creative-response.json#/oneOf/1` | _adapter |
| `LegacyBuildCreativeResponse3` | `adcp.types.media_buy.BuildCreativeVariantSuccess` | `media-buy/build-creative-response.json#/oneOf/2` | _adapter |
| `LegacyBuildCreativeResponse4` | `adcp.types.media_buy.BuildCreativeEstimate` | `media-buy/build-creative-response.json#/oneOf/3` | _adapter |
| `LegacyBuildCreativeResponse5` | `adcp.types.media_buy.BuildCreativeError` | `media-buy/build-creative-response.json#/oneOf/4` | _adapter |
| `LegacyBuildCreativeResponse6` | `adcp.types.media_buy.BuildCreativeResponseSubmitted` | `media-buy/build-creative-response.json#/oneOf/5` | _adapter |
| `LegacyBuildCreativeSubmittedResponse` | `adcp.types.media_buy.BuildCreativeResponseSubmitted` | `media-buy/build-creative-response.json#/oneOf/5` | _adapter |
| `LegacyBuildCreativeSuccessResponse` | `adcp.types.media_buy.BuildCreativeSuccess` | `media-buy/build-creative-response.json#/oneOf/0` | _adapter |
| `LegacyCreateMediaBuyRequest` | `adcp.types.media_buy.CreateMediaBuyRequest` | `media-buy/create-media-buy-request.json#` | _adapter |
| `LegacyCreativeAsset` | `adcp.types.core.CreativeAsset` | `core/creative-asset.json#` | _adapter · **PAYLOAD** |
| `LegacyCreativeFilters` | `adcp.types.core.CreativeFilters` | `core/creative-filters.json#` | _adapter |
| `LegacyFormat` | `adcp.types.core.Format` | `core/format.json#` | _adapter |
| `LegacyFormatId` | `adcp.types.core.FormatReferenceStructuredObject` | `core/format-id.json#` | _adapter |
| `LegacyFormatReferenceStructuredObject` | `adcp.types.core.FormatReferenceStructuredObject` | `core/format-id.json#` | _adapter |
| `LegacyGetCreativeDeliveryResponse` | `adcp.types.creative.GetCreativeDeliveryResponse` | `creative/get-creative-delivery-response.json#` | _adapter |
| `LegacyGetMediaBuyDeliveryResponse` | `adcp.types.media_buy.GetMediaBuyDeliveryResponse` | `media-buy/get-media-buy-delivery-response.json#` | _adapter |
| `LegacyGetMediaBuysResponse` | `adcp.types.media_buy.GetMediaBuysResponse` | `media-buy/get-media-buys-response.json#` | _adapter |
| `LegacyGetProductsRequest` | `adcp.types.media_buy.GetProductsRequest` | `media-buy/get-products-request.json#` | _adapter |
| `LegacyGetProductsResponse` | `adcp.types.media_buy.GetProductsResponse` | `media-buy/get-products-response.json#` | _adapter |
| `LegacyListCreativeFormatsRequest` | `adcp.types.media_buy.ListCreativeFormatsRequest` | `media-buy/list-creative-formats-request.json#` | _adapter |
| `LegacyListCreativeFormatsResponse` | `adcp.types.media_buy.ListCreativeFormatsResponse` | `media-buy/list-creative-formats-response.json#` | _adapter |
| `LegacyListCreativesRequest` | `adcp.types.creative.ListCreativesRequest` | `creative/list-creatives-request.json#` | _adapter |
| `LegacyListCreativesResponse` | `adcp.types.creative.ListCreativesResponse` | `creative/list-creatives-response.json#` | _adapter |
| `LegacyPackage` | `adcp.types.core.Package` | `core/package.json#` | _adapter |
| `LegacyPackageRequest` | `adcp.types.media_buy.PackageRequest` | `media-buy/package-request.json#` | _adapter |
| `LegacyPackageUpdate` | `adcp.types.media_buy.PackageUpdate` | `media-buy/package-update.json#` | _adapter |
| `LegacyPlacement` | `adcp.types.core.Placement` | `core/placement.json#` | _adapter |
| `LegacyPreviewCreativeBatchResponse` | `adcp.types.creative.PreviewCreativeBatchResponse` | `creative/preview-creative-response.json#/oneOf/1` | _adapter |
| `LegacyPreviewCreativeRequest` | `adcp.types.creative.PreviewCreativeRequest` | `creative/preview-creative-request.json#` | _adapter |
| `LegacyPreviewCreativeResponse` | `adcp.types.creative.PreviewCreativeResponse` | `creative/preview-creative-response.json#` | _adapter |
| `LegacyPreviewCreativeResponse1` | `adcp.types.creative.PreviewCreativeSingleResponse` | `creative/preview-creative-response.json#/oneOf/0` | _adapter |
| `LegacyPreviewCreativeResponse2` | `adcp.types.creative.PreviewCreativeBatchResponse` | `creative/preview-creative-response.json#/oneOf/1` | _adapter |
| `LegacyPreviewCreativeResponse3` | `adcp.types.creative.PreviewCreativeVariantResponse` | `creative/preview-creative-response.json#/oneOf/2` | _adapter |
| `LegacyPreviewCreativeSingleResponse` | `adcp.types.creative.PreviewCreativeSingleResponse` | `creative/preview-creative-response.json#/oneOf/0` | _adapter |
| `LegacyPreviewCreativeVariantResponse` | `adcp.types.creative.PreviewCreativeVariantResponse` | `creative/preview-creative-response.json#/oneOf/2` | _adapter |
| `LegacyProduct` | `adcp.types.core.Product` | `core/product.json#` | _adapter |
| `LegacyProductFilters` | `adcp.types.core.ProductFilters` | `core/product-filters.json#` | _adapter |
| `LegacySyncCreativesRequest` | `adcp.types.creative.SyncCreativesRequest` | `creative/sync-creatives-request.json#` | _adapter |
| `LegacyUpdateMediaBuyRequest` | `adcp.types.media_buy.UpdateMediaBuyRequest` | `media-buy/update-media-buy-request.json#` | _adapter |
| `LiftDimension` | `adcp.types.enums.LiftDimension` | `enums/lift-dimension.json#` | compat |
| `LimitedSeries` | `adcp.types.core.LimitedSeries` | `core/limited-series.json#` | compat |
| `ListAccountChangesRequest` | `adcp.types.account.ListAccountChangesRequest` | `account/list-account-changes-request.json#` | compat |
| `ListAccountChangesResponse` | `adcp.types.account.ListAccountChangesResponse` | `account/list-account-changes-response.json#` | compat |
| `ListAccountsRequest` | `adcp.types.account.ListAccountsRequest` | `account/list-accounts-request.json#` | compat |
| `ListAccountsResponse` | `adcp.types.account.ListAccountsResponse` | `account/list-accounts-response.json#` | compat |
| `ListCollectionListsRequest` | `adcp.types.collection.ListCollectionListsRequest` | `collection/list-collection-lists-request.json#` | compat |
| `ListCollectionListsResponse` | `adcp.types.collection.ListCollectionListsResponse` | `collection/list-collection-lists-response.json#` | compat |
| `ListContentStandardsRequest` | `adcp.types.content_standards.ListContentStandardsRequest` | `content-standards/list-content-standards-request.json#` | compat |
| `ListContentStandardsResponse` | `adcp.types.content_standards.ListContentStandardsResponse` | `content-standards/list-content-standards-response.json#` | compat |
| `ListCreativeFormatsRequest` | `adcp.types.media_buy.ListCreativeFormatsRequest` | `media-buy/list-creative-formats-request.json#` | compat |
| `ListCreativeFormatsRequestCreativeAgent` | `adcp.types.creative.ListCreativeFormatsRequestCreativeAgent` | `creative/list-creative-formats-request.json#` | compat |
| `ListCreativeFormatsResponse` | `adcp.types.media_buy.ListCreativeFormatsResponse` | `media-buy/list-creative-formats-response.json#` | compat |
| `ListCreativeFormatsResponseCreativeAgent` | `adcp.types.creative.ListCreativeFormatsResponseCreativeAgent` | `creative/list-creative-formats-response.json#` | compat |
| `ListProductsRequest` | `adcp.types.media_buy.ListProductsRequest` | `media-buy/list-products-request.json#` | flat_only |
| `ListProductsResponse` | `adcp.types.media_buy.ListProductsResponse` | `media-buy/list-products-response.json#` | flat_only |
| `ListPropertyListsRequest` | `adcp.types.property.ListPropertyListsRequest` | `property/list-property-lists-request.json#` | compat |
| `ListPropertyListsResponse` | `adcp.types.property.ListPropertyListsResponse` | `property/list-property-lists-response.json#` | compat |
| `ListTasksRequest` | `adcp.types.protocol.ListTasksRequest` | `protocol/list-tasks-request.json#` | flat_only |
| `ListTasksResponse` | `adcp.types.protocol.ListTasksResponse` | `protocol/list-tasks-response.json#` | flat_only |
| `ListTransformersRequest` | `adcp.types.creative.ListTransformersRequestCreativeAgent` | `creative/list-transformers-request.json#` | compat |
| `ListTransformersRequestCreativeAgent` | `adcp.types.creative.ListTransformersRequestCreativeAgent` | `creative/list-transformers-request.json#` | compat |
| `ListTransformersResponse` | `adcp.types.creative.ListTransformersResponseCreativeAgent` | `creative/list-transformers-response.json#` | compat |
| `ListTransformersResponseCreativeAgent` | `adcp.types.creative.ListTransformersResponseCreativeAgent` | `creative/list-transformers-response.json#` | compat |
| `LogEventRequest` | `adcp.types.media_buy.LogEventRequest` | `media-buy/log-event-request.json#` | compat |
| `LogEventResponse` | `adcp.types.media_buy.LogEventResponse` | `media-buy/log-event-response.json#` | compat |
| `LogoSlot` | `adcp.types.enums.LogoSlot` | `enums/logo-slot.json#` | compat |
| `MacroDeclaration` | `adcp.types.core.MacroDeclaration` | `core/macro-declaration.json#` | compat |
| `MacroDialect` | `adcp.types.enums.MacroDialectFamily` | `enums/macro-dialect.json#` | compat |
| `MacroDialectFamily` | `adcp.types.enums.MacroDialectFamily` | `enums/macro-dialect.json#` | compat |
| `MacroEncoding` | `adcp.types.core.MacroEncoding` | `core/macro-encoding.json#` | compat |
| `MacroMappingStatus` | `adcp.types.enums.MacroMappingStatus` | `enums/macro-mapping-status.json#` | compat |
| `MacroProcessingActor` | `adcp.types.enums.MacroProcessingActor` | `enums/macro-resolver.json#` | compat |
| `MacroProcessingCapability` | `adcp.types.core.MacroProcessingCapability` | `core/macro-resolution-capability.json#` | compat |
| `MacroProcessingOperation` | `adcp.types.enums.MacroProcessingOperation` | `enums/macro-processing-operation.json#` | compat |
| `MacroResolutionCapability` | `adcp.types.core.MacroProcessingCapability` | `core/macro-resolution-capability.json#` | compat |
| `MacroResolutionFailedDetails` | `adcp.types.error_details.MacroResolutionFailedDetails` | `error-details/macro-resolution-failed.json#` | flat_only |
| `MacroResolutionReason` | `adcp.types.enums.MacroResolutionReason` | `enums/macro-resolution-reason.json#` | compat |
| `MacroResolutionResult` | `adcp.types.core.MacroResolutionResult` | `core/macro-resolution-result.json#` | compat |
| `MacroResolver` | `adcp.types.enums.MacroProcessingActor` | `enums/macro-resolver.json#` | compat |
| `MacroTranslationTarget` | `adcp.types.core.MacroTranslationTarget` | `core/macro-translation-target.json#` | compat |
| `MacroValueContext` | `adcp.types.enums.MacroValueContext` | `enums/macro-value-context.json#` | compat |
| `MakegoodRemedy` | `adcp.types.enums.MakegoodRemedy` | `enums/makegood-remedy.json#` | compat |
| `MarkdownAsset` | `adcp.types.core.MarkdownAsset` | `core/assets/markdown-asset.json#` | compat |
| `MarkdownAssetRequirements` | `adcp.types.core.MarkdownAssetRequirements` | `core/requirements/markdown-asset-requirements.json#` | compat |
| `MarkdownFlavor` | `adcp.types.enums.MarkdownFlavor` | `enums/markdown-flavor.json#` | compat |
| `MatchIdType` | `adcp.types.enums.MatchIDType` | `enums/match-id-type.json#` | compat |
| `MatchType` | `adcp.types.enums.MatchType` | `enums/match-type.json#` | compat |
| `MaterialDeadline` | `adcp.types.core.MaterialDeadline` | `core/material-deadline.json#` | compat |
| `McpWebhookPayload` | `adcp.types.core.MCPWebhookPayload` | `core/mcp-webhook-payload.json#` | compat |
| `MeasurementReadiness` | `adcp.types.core.MeasurementReadiness` | `core/measurement-readiness.json#` | compat |
| `MeasurementTerms` | `adcp.types.core.MeasurementTerms` | `core/measurement-terms.json#` | compat |
| `MeasurementWindow` | `adcp.types.core.MeasurementWindow` | `core/measurement-window.json#` | compat |
| `MediaBuy` | `adcp.types.core.MediaBuy` | `core/media-buy.json#` | compat |
| `MediaBuyActionMode` | `adcp.types.enums.MediaBuyActionMode` | `enums/media-buy-action-mode.json#` | compat |
| `MediaBuyAvailableAction` | `adcp.types.core.MediaBuyAvailableAction` | `core/media-buy-available-action.json#` | compat |
| `MediaBuyChangeTerm` | `adcp.types.media_buy.MediaBuyChangeTerm` | `media-buy/change-term.json#` | flat_only |
| `MediaBuyChangeTermConstraints` | `adcp.types.media_buy.MediaBuyChangeTermConstraints` | `media-buy/change-term-constraints.json#` | flat_only |
| `MediaBuyCommitmentResponse` | `adcp.types.media_buy.MediaBuyCommitmentResponse` | `media-buy/media-buy-commitment-response.json#` | compat |
| `MediaBuyDeliveryWebhookResult` | `adcp.types.media_buy.MediaBuyDeliveryWebhookResult` | `media-buy/media-buy-delivery-webhook-result.json#` | compat |
| `MediaBuyFeatures` | `adcp.types.core.MediaBuyFeatures` | `core/media-buy-features.json#` | compat |
| `MediaBuyFrequencyCap` | `adcp.types.core.MediaBuyFrequencyCap` | `core/media-buy-frequency-cap.json#` | compat |
| `MediaBuyFrequencyCapCapability` | `adcp.types.core.MediaBuyFrequencyCapCapability` | `core/media-buy-frequency-cap-capability.json#` | compat |
| `MediaBuyFrequencyCapControlMode` | `adcp.types.enums.MediaBuyFrequencyCapControlMode` | `enums/media-buy-frequency-cap-control-mode.json#` | compat |
| `MediaBuyFrequencyCapRequirement` | `adcp.types.core.MediaBuyFrequencyCapRequirement` | `core/media-buy-frequency-cap-requirement.json#` | compat |
| `MediaBuyFrequencyCapSupport` | `adcp.types.core.MediaBuyFrequencyCapSupport` | `core/media-buy-frequency-cap-support.json#` | compat |
| `MediaBuyHealth` | `adcp.types.enums.MediaBuyHealth` | `enums/media-buy-health.json#` | compat |
| `MediaBuyStatus` | `adcp.types.enums.MediaBuyStatus` | `enums/media-buy-status.json#` | compat |
| `MediaBuyValidAction` | `adcp.types.enums.MediaBuyValidAction` | `enums/media-buy-valid-action.json#` | compat |
| `MediaChannel` | `adcp.types.enums.MediaChannel` | `enums/channels.json#` | compat |
| `MetricScope` | `adcp.types.enums.MetricScope` | `enums/metric-scope.json#` | compat |
| `MetricType` | `adcp.types.enums.MetricType` | `enums/metric-type.json#` | compat |
| `MetroAreaSystem` | `adcp.types.enums.MetroAreaSystem` | `enums/metro-system.json#` | compat |
| `MissingMetric` | `adcp.types.core.MissingMetric` | `core/missing-metric.json#` | compat |
| `MoovAtomPosition` | `adcp.types.enums.MoovAtomPosition` | `enums/moov-atom-position.json#` | compat |
| `NegativeKeyword` | `adcp.types.core.NegativeKeyword` | `core/negative-keyword.json#` | compat |
| `NotificationAuthentication` | `adcp.types.core.NotificationConfigAuthentication` | `core/notification-config.json#/properties/authentication` | _adapter |
| `NotificationConfig` | `adcp.types.core.NotificationConfig` | `core/notification-config.json#` | compat |
| `NotificationType` | `adcp.types.enums.NotificationType` | `enums/notification-type.json#` | compat |
| `Offer` | `adcp.types.trusted_match.Offer` | `trusted-match/offer.json#` | compat |
| `OfferPrice` | `adcp.types.trusted_match.OfferPrice` | `trusted-match/offer-price.json#` | compat |
| `Offering` | `adcp.types.core.Offering` | `core/offering.json#` | compat |
| `OfferingAssetConstraint` | `adcp.types.core.OfferingAssetConstraint` | `core/requirements/offering-asset-constraint.json#` | compat |
| `OfferingAssetGroup` | `adcp.types.core.OfferingAssetGroup` | `core/offering-asset-group.json#` | compat |
| `OfferingAvailabilityStatus` | `adcp.types.enums.OfferingAvailabilityStatus` | `enums/offering-availability-status.json#` | compat |
| `OperatorIdentity` | `adcp.types.core.OperatorIdentity` | `core/operator-identity.json#` | compat |
| `OperatorUnit` | `adcp.types.core.OperatorUnit` | `core/operator-unit.json#` | compat |
| `OpportunityContext` | `adcp.types.core.OpportunityContext` | `core/opportunity-context.json#` | compat |
| `OptimizationGoal` | `adcp.types.core.OptimizationGoal` | `core/optimization-goal.json#` | compat |
| `OutcomeMeasurement` | `adcp.types.core.OutcomeMeasurement` | `core/outcome-measurement.json#` | compat |
| `OutcomeTarget` | `adcp.types.media_buy.OutcomeTarget` | `media-buy/outcome-target.json#` | compat |
| `OutcomeTargetCostPer` | `adcp.types.core.OutcomeTargetCostPer` | `core/outcome-target-cost-per.json#` | compat |
| `OutcomeTargetCostStrength` | `adcp.types.enums.OutcomeTargetCostStrength` | `enums/outcome-target-cost-strength.json#` | compat |
| `OutcomeType` | `adcp.types.enums.OutcomeType` | `enums/outcome-type.json#` | compat |
| `Overlay` | `adcp.types.core.Overlay` | `core/overlay.json#` | compat |
| `Pacing` | `adcp.types.enums.Pacing` | `enums/pacing.json#` | compat |
| `PackageControl` | `adcp.types.media_buy.PackageControl` | `media-buy/package-control.json#` | compat |
| `PackageCountChangeConstraints` | `adcp.types.media_buy.PackageCountConstraints` | `media-buy/change-term-constraints.json#/oneOf/2` | _adapter |
| `PackageDeliveryMetricValue` | `adcp.types.core.PackageDeliveryMetricValue` | `core/package-delivery-metric-value.json#` | compat |
| `PackageFormatSnapshot` | `adcp.types.core.PackageFormatSnapshot` | `core/package-format-snapshot.json#` | compat |
| `PackageSignalTargeting` | `adcp.types.core.PackageSignalTargeting` | `core/package-signal-targeting.json#` | compat |
| `PackageSignalTargetingGroup` | `adcp.types.core.PackageSignalTargetingGroup` | `core/package-signal-targeting-group.json#` | compat |
| `PackageSignalTargetingGroups` | `adcp.types.core.PackageSignalTargetingGroups` | `core/package-signal-targeting-groups.json#` | compat |
| `PackageTargetingResolution` | `adcp.types.core.PackageTargetingResolution` | `core/package-targeting-resolution.json#` | compat |
| `PaginationRequest` | `adcp.types.core.PaginationRequest` | `core/pagination-request.json#` | compat |
| `PaginationResponse` | `adcp.types.core.PaginationResponse` | `core/pagination-response.json#` | compat |
| `PaymentTerms` | `adcp.types.enums.PaymentTerms` | `enums/payment-terms.json#` | compat |
| `PerformanceBaseline` | `adcp.types.enums.PerformanceBaseline` | `enums/performance-baseline.json#` | compat |
| `PerformanceFeedback` | `adcp.types.core.PerformanceFeedback` | `core/performance-feedback.json#` | compat |
| `PerformanceFeedbackAssertion` | `adcp.types.core.PerformanceFeedbackAssertion` | `core/performance-feedback-assertion.json#` | compat |
| `PerformanceFeedbackMetric` | `adcp.types.core.PerformanceFeedbackMetric` | `core/performance-feedback-metric.json#` | compat |
| `PerformanceStandard` | `adcp.types.core.PerformanceStandard` | `core/performance-standard.json#` | compat |
| `PerformanceStandardMetric` | `adcp.types.enums.PerformanceStandardMetric` | `enums/performance-standard-metric.json#` | compat |
| `PixelTrackerAsset` | `adcp.types.core.PixelTrackerAsset` | `core/assets/pixel-tracker-asset.json#` | compat |
| `PixelTrackerEvent` | `adcp.types.enums.PixelTrackingEvent` | `enums/pixel-tracking-event.json#` | _adapter |
| `PixelTrackingEvent` | `adcp.types.enums.PixelTrackingEvent` | `enums/pixel-tracking-event.json#` | compat |
| `PlacementDefinition` | `adcp.types.core.PlacementDefinition` | `core/placement-definition.json#` | compat |
| `PlacementDeliveryMetrics` | `adcp.types.core.PlacementDeliveryMetrics` | `core/placement-delivery-metrics.json#` | compat |
| `PlacementEvidence` | `adcp.types.core.PlacementEvidence` | `core/placement-evidence.json#` | compat |
| `PlacementForecastDimension` | `adcp.types.core.PlacementForecastDimension` | `core/forecast-dimension-placement.json#` | compat |
| `PlacementIdentity` | `adcp.types.core.PlacementIdentity` | `core/placement-identity.json#` | compat |
| `PlacementPresentationDocument` | `adcp.types.core.PlacementPresentationDocument` | `core/placement-presentation.json#` | compat |
| `PlacementPresentationReference` | `adcp.types.core.PlacementPresentationReference` | `core/presentation-ref.json#` | compat |
| `PlacementPropertyDeliveryMetrics` | `adcp.types.core.PlacementPropertyDeliveryMetrics` | `core/placement-property-delivery-metrics.json#` | compat |
| `PlacementReference` | `adcp.types.core.PlacementReference` | `core/placement-ref.json#` | compat |
| `PlacementSelection` | `adcp.types.core.PlacementSelection` | `core/placement-selection.json#` | compat |
| `PlannedDelivery` | `adcp.types.core.PlannedDelivery` | `core/planned-delivery.json#` | compat |
| `PlatformDeployment` | `adcp.types.core.DeploymentPlatform` | `core/deployment.json#/oneOf/0` | _adapter |
| `PlatformExtensionRef` | `adcp.types.core.PlatformExtensionReference` | `core/platform-extension-ref.json#` | compat |
| `PlatformExtensionReference` | `adcp.types.core.PlatformExtensionReference` | `core/platform-extension-ref.json#` | compat |
| `PolicyCategory` | `adcp.types.enums.PolicyCategory` | `enums/policy-category.json#` | compat |
| `PolicyCategoryDefinition` | `adcp.types.governance.PolicyCategoryDefinition` | `governance/policy-category-definition.json#` | compat |
| `PolicyEnforcement` | `adcp.types.enums.PolicyEnforcementLevel` | `enums/policy-enforcement.json#` | compat |
| `PolicyEnforcementLevel` | `adcp.types.enums.PolicyEnforcementLevel` | `enums/policy-enforcement.json#` | compat |
| `PolicyEntry` | `adcp.types.governance.PolicyEntry` | `governance/policy-entry.json#` | compat |
| `PolicyReference` | `adcp.types.governance.PolicyReference` | `governance/policy-ref.json#` | compat |
| `PolicyViolationDetails` | `adcp.types.error_details.PolicyViolationDetails` | `error-details/policy-violation.json#` | flat_only |
| `PositivePostalAreaSupport` | `adcp.types.core.PositivePostalAreaSupport` | `core/positive-postal-area-support.json#` | compat |
| `PostalArea` | `adcp.types.core.PostalArea` | `core/postal-area.json#` | compat |
| `PostalAreaSupport` | `adcp.types.core.PostalAreaSupport` | `core/postal-area-support.json#` | compat |
| `PostalCodeSystem` | `adcp.types.enums.PostalCodeSystem` | `enums/postal-system.json#` | compat |
| `PostalCountrySystem` | `adcp.types.core.PostalCountrySystem` | `core/postal-country-system.json#` | compat |
| `PreviewCreativeRequest` | `adcp.types.creative.PreviewCreativeRequest` | `creative/preview-creative-request.json#` | compat |
| `PreviewCreativeResponse` | `adcp.types.creative.PreviewCreativeResponse` | `creative/preview-creative-response.json#` | compat |
| `PreviewOutputFormat` | `adcp.types.enums.PreviewOutputFormat` | `enums/preview-output-format.json#` | compat |
| `PreviewRender` | `adcp.types.creative.PreviewRender` | `creative/preview-render.json#` | flat_only |
| `PreviewRendererMetadata` | `adcp.types.core.PreviewRendererMetadata` | `core/preview-renderer-metadata.json#` | compat |
| `Price` | `adcp.types.core.Price` | `core/price.json#` | compat |
| `PriceAdjustmentKind` | `adcp.types.enums.PriceAdjustmentKind` | `enums/adjustment-kind.json#` | compat |
| `PriceBreakdown` | `adcp.types.pricing_options.PriceBreakdown` | `pricing-options/price-breakdown.json#` | compat |
| `PriceGuidance` | `adcp.types.pricing_options.PriceGuidance` | `pricing-options/price-guidance.json#` | compat |
| `PricingModel` | `adcp.types.enums.PricingModel` | `enums/pricing-model.json#` | compat |
| `PricingOption` | `adcp.types.core.PricingOption` | `core/pricing-option.json#` | compat |
| `PricingStructure` | `adcp.types.enums.PricingStructure` | `enums/pricing-structure.json#` | compat |
| `PrincipalChangedWebhook` | `adcp.types.core.PrincipalChangedWebhook` | `core/principal-changed-webhook.json#` | compat |
| `PrincipalConfiguration` | `adcp.types.protocol.SyncPrincipalRequestConfiguration` | `protocol/sync-principal-request.json#/properties/configuration` | _adapter |
| `PrincipalDeclarationsState` | `adcp.types.core.PrincipalDeclarationsState` | `core/principal-declarations-state.json#` | compat |
| `PrincipalKind` | `adcp.types.enums.PrincipalKind` | `enums/principal-kind.json#` | compat |
| `PrincipalState` | `adcp.types.core.PrincipalState` | `core/principal-state.json#` | compat |
| `ProductAllocation` | `adcp.types.core.ProductAllocation` | `core/product-allocation.json#` | compat |
| `ProductAllowedAction` | `adcp.types.core.ProductAllowedAction` | `core/product-allowed-action.json#` | compat |
| `ProductAudienceEvidenceRequirements` | `adcp.types.core.ProductAudienceEvidenceRequirements` | `core/product-audience-evidence-requirements.json#` | compat |
| `ProductCardReferenceAsset` | `adcp.types.core.ProductCardReferenceAsset` | `core/product-card-reference-asset.json#` | compat |
| `ProductDiscoveryCriteria` | `adcp.types.media_buy.ProductDiscoveryCriteria` | `media-buy/product-discovery-criteria.json#` | compat |
| `ProductDiscoveryTargetingResolution` | `adcp.types.media_buy.ProductDiscoveryTargetingResolution` | `media-buy/get-products-targeting-resolution.json#` | compat |
| `ProductExecutionRequirement` | `adcp.types.core.ProductExecutionRequirement` | `core/product-execution-requirement.json#` | compat |
| `ProductIdentity` | `adcp.types.core.ProductIdentity` | `core/product-identity.json#` | compat |
| `ProductMediaBuySupport` | `adcp.types.core.ProductMediaBuySupport` | `core/media-buy-support.json#` | compat |
| `ProductMediaBuySupportRequirements` | `adcp.types.core.ProductMediaBuySupportRequirements` | `core/media-buy-support-requirements.json#` | compat |
| `ProductOfferFilters` | `adcp.types.core.ProductOfferFilters` | `core/product-offer-filters.json#` | compat |
| `ProductPurchase` | `adcp.types.media_buy.ProductPurchase` | `media-buy/product-purchase.json#` | compat |
| `ProductPurchaseInput` | `adcp.types.media_buy.ProductPurchaseInput` | `media-buy/product-purchase-input.json#` | compat |
| `ProductRefinementRequests` | `adcp.types.media_buy.ProductRefinementRequests` | `media-buy/product-refinement.json#` | compat |
| `ProductResponseFields` | `adcp.types.media_buy.ProductResponseFields` | `media-buy/product-fields.json#` | compat |
| `ProductSignalTargetingOption` | `adcp.types.core.ProductSignalTargetingOption` | `core/product-signal-targeting-option.json#` | compat |
| `ProductTargetingResolution` | `adcp.types.core.ProductTargetingResolution` | `core/product-targeting-resolution.json#` | compat |
| `ProductionQuality` | `adcp.types.enums.ProductionQuality` | `enums/production-quality.json#` | compat |
| `Property` | `adcp.types.core.Property` | `core/property.json#` | compat |
| `PropertyDeliveryMetrics` | `adcp.types.core.PropertyDeliveryMetrics` | `core/property-delivery-metrics.json#` | compat |
| `PropertyError` | `adcp.types.property.PropertyError` | `property/property-error.json#` | compat |
| `PropertyFeatureDefinition` | `adcp.types.property.PropertyFeatureDefinition` | `property/property-feature-definition.json#` | compat |
| `PropertyFeatureResult` | `adcp.types.property.PropertyFeatureResult` | `property/property-feature-result.json#` | compat |
| `PropertyFeatureValue` | `adcp.types.property.PropertyFeatureValue` | `property/property-feature-value.json#` | compat |
| `PropertyIdActivationKey` | `adcp.types.core.ActivationKeySegmentId` | `core/activation-key.json#/oneOf/0` | _adapter |
| `PropertyIdentifierTypes` | `adcp.types.enums.PropertyIdentifierTypes` | `enums/identifier-types.json#` | compat |
| `PropertyListChangedWebhook` | `adcp.types.property.PropertyListChangedWebhook` | `property/property-list-changed-webhook.json#` | compat |
| `PropertyListFilters` | `adcp.types.property.PropertyListFilters` | `property/property-list-filters.json#` | compat |
| `PropertyListReference` | `adcp.types.core.PropertyListReference` | `core/property-list-ref.json#` | compat |
| `PropertyReference` | `adcp.types.core.PropertyReference` | `core/property-ref.json#` | compat |
| `PropertyTagActivationKey` | `adcp.types.core.ActivationKeyKeyValue` | `core/activation-key.json#/oneOf/1` | _adapter |
| `PropertyType` | `adcp.types.enums.PropertyType` | `enums/property-type.json#` | compat |
| `Proposal` | `adcp.types.core.Proposal` | `core/proposal.json#` | compat |
| `ProposalBudgetConstraint` | `adcp.types.media_buy.ProposalBudgetConstraint` | `media-buy/proposal-budget-constraint.json#` | compat |
| `ProposalDecline` | `adcp.types.media_buy.ProposalDecline` | `media-buy/proposal-decline.json#` | compat |
| `ProposalDeclineReason` | `adcp.types.enums.ProposalDeclineReason` | `enums/proposal-decline-reason.json#` | compat |
| `ProposalRefinementReason` | `adcp.types.enums.ProposalRefinementReason` | `enums/proposal-refinement-reason.json#` | compat |
| `ProposalStatus` | `adcp.types.enums.ProposalStatus` | `enums/proposal-status.json#` | compat |
| `ProtocolEnvelope` | `adcp.types.core.ProtocolEnvelope` | `core/protocol-envelope.json#` | compat |
| `ProtocolResponse` | `adcp.types.core.ProtocolResponse` | `core/response.json#` | compat |
| `Provenance` | `adcp.types.core.Provenance` | `core/provenance.json#` | compat |
| `ProvenanceDeclaredBy` | `adcp.types.core.ProvenanceDeclaredBy` | `core/provenance.json#/properties/declared_by` | compat |
| `ProvidePerformanceFeedbackRequest` | `adcp.types.media_buy.ProvidePerformanceFeedbackRequest` | `media-buy/provide-performance-feedback-request.json#` | compat |
| `ProvidePerformanceFeedbackResponse` | `adcp.types.media_buy.ProvidePerformanceFeedbackResponse` | `media-buy/provide-performance-feedback-response.json#` | compat |
| `ProviderIdentityMatchResponse` | `adcp.types.trusted_match.IdentityMatchResponseProviderRouter` | `trusted-match/provider-identity-match-response.json#` | compat |
| `PublishedPostAsset` | `adcp.types.core.PublishedPostAsset` | `core/assets/published-post-asset.json#` | compat |
| `PublisherDesignatedPreviewProvider` | `adcp.types.core.PublisherDesignatedPreviewProvider` | `core/preview-provider.json#` | compat |
| `PublisherIdentifierTypes` | `adcp.types.enums.PublisherIdentifierTypes` | `enums/publisher-identifier-types.json#` | compat |
| `PublisherPropertySelector` | `adcp.types.core.PublisherPropertySelector` | `core/publisher-property-selector.json#` | compat |
| `PublisherTargetingKvMapping` | `adcp.types.trusted_match.PublisherTargetingKVMapping` | `trusted-match/publisher-targeting-kv-config.json#` | compat |
| `PublisherTmpxMacroMapping` | `adcp.types.trusted_match.PublisherTMPXMacroMapping` | `trusted-match/publisher-tmpx-config.json#` | compat |
| `PurchaseType` | `adcp.types.enums.PurchaseType` | `enums/purchase-type.json#` | compat |
| `PushNotificationConfig` | `adcp.types.core.PushNotificationConfig` | `core/push-notification-config.json#` | compat |
| `RateLimitedDetails` | `adcp.types.error_details.RateLimitedDetails` | `error-details/rate-limited.json#` | flat_only |
| `ReachAggregation` | `adcp.types.enums.ReachAggregation` | `enums/reach-aggregation.json#` | compat |
| `ReachUnit` | `adcp.types.enums.ReachUnit` | `enums/reach-unit.json#` | compat |
| `RealEstateItem` | `adcp.types.core.RealEstateItem` | `core/real-estate-item.json#` | compat |
| `ReferenceAsset` | `adcp.types.core.ReferenceAsset` | `core/reference-asset.json#` | compat |
| `ReferenceRenderer` | `adcp.types.core.ReferenceRenderer` | `core/reference-renderer.json#` | compat |
| `ReferenceRendererProvenance` | `adcp.types.core.ReferenceRendererProvenance` | `core/reference-renderer.json#/properties/provenance` | compat |
| `RefineProposalsInputRequired` | `adcp.types.media_buy.RefineProposalsInputRequired` | `media-buy/refine-proposals-async-response-input-required.json#` | compat |
| `RefineProposalsRequest` | `adcp.types.media_buy.RefineProposalsRequest` | `media-buy/refine-proposals-request.json#` | flat_only |
| `RefineProposalsResponse` | `adcp.types.media_buy.RefineProposalsResponse` | `media-buy/refine-proposals-response.json#` | flat_only |
| `RefineProposalsSubmitted` | `adcp.types.media_buy.RefineProposalsSubmitted` | `media-buy/refine-proposals-async-response-submitted.json#` | compat |
| `RefineProposalsWorking` | `adcp.types.media_buy.RefineProposalsWorking` | `media-buy/refine-proposals-async-response-working.json#` | compat |
| `RegistryAcceptancePolicyProfileReference` | `adcp.types.media_buy.RegistryAcceptancePolicyProfileReference` | `media-buy/acceptance-policy-profile-ref.json#` | flat_only |
| `RegistryEvent` | `adcp.types.core.RegistryEvent` | `core/registry-event.json#` | compat |
| `RegistryFeedResponse` | `adcp.types.core.RegistryFeedResponse` | `core/registry-feed-response.json#` | compat |
| `ReportPlanAdjustmentRequest` | `adcp.types.governance.ReportPlanAdjustmentRequest` | `governance/report-plan-adjustment-request.json#` | compat |
| `ReportPlanAdjustmentResponse` | `adcp.types.governance.ReportPlanAdjustmentResponse` | `governance/report-plan-adjustment-response.json#` | compat |
| `ReportPlanOutcomeRequest` | `adcp.types.governance.ReportPlanOutcomeRequest` | `governance/report-plan-outcome-request.json#` | compat |
| `ReportPlanOutcomeResponse` | `adcp.types.governance.ReportPlanOutcomeResponse` | `governance/report-plan-outcome-response.json#` | compat |
| `ReportUsageRequest` | `adcp.types.account.ReportUsageRequest` | `account/report-usage-request.json#` | compat |
| `ReportUsageResponse` | `adcp.types.account.ReportUsageResponse` | `account/report-usage-response.json#` | compat |
| `ReportedOutcomeError` | `adcp.types.governance.ReportedOutcomeError` | `governance/reported-outcome-error.json#` | compat |
| `ReportingAdjustment` | `adcp.types.core.ReportingAdjustment` | `core/reporting-adjustment.json#` | compat |
| `ReportingAdjustmentReceipt` | `adcp.types.core.ReportingAdjustmentReceipt` | `core/reporting-adjustment-receipt.json#` | compat |
| `ReportingBucket` | `adcp.types.core.AccountReportingBucket` | `core/account.json#/properties/reporting_bucket` | _adapter |
| `ReportingCanonicalContentDigest` | `adcp.types.core.ReportingCanonicalContentDigest` | `core/reporting-canonical-content-digest.json#` | compat |
| `ReportingCanonicalizationContract` | `adcp.types.core.ReportingCanonicalizationContract` | `core/reporting-canonicalization-contract.json#` | compat |
| `ReportingCapabilities` | `adcp.types.core.ReportingCapabilities` | `core/reporting-capabilities.json#` | compat |
| `ReportingConsumerStatus` | `adcp.types.core.ReportingConsumerStatus` | `core/reporting-consumer-status.json#` | compat |
| `ReportingControlTotal` | `adcp.types.core.ReportingControlTotal` | `core/reporting-control-total.json#` | compat |
| `ReportingCoverage` | `adcp.types.core.ReportingCoverage` | `core/reporting-coverage.json#` | compat |
| `ReportingDatasetShareDestination` | `adcp.types.core.ReportingDatasetShareDestination` | `core/reporting-dataset-share-destination.json#` | compat |
| `ReportingDeliveryCapabilities` | `adcp.types.core.ReportingDeliveryCapabilities` | `core/reporting-delivery-capabilities.json#` | compat |
| `ReportingDeliveryConfiguration` | `adcp.types.core.ReportingDeliveryConfiguration` | `core/reporting-delivery-config.json#` | compat |
| `ReportingDeliveryConfigurationState` | `adcp.types.core.ReportingDeliveryConfigurationState` | `core/reporting-delivery-config-state.json#` | compat |
| `ReportingDeliveryMethod` | `adcp.types.core.ReportingDeliveryMethod` | `core/reporting-delivery-method.json#` | compat |
| `ReportingDeliveryOffering` | `adcp.types.core.ReportingDeliveryOffering` | `core/reporting-delivery-offering.json#` | compat |
| `ReportingDeliveryReadyWebhook` | `adcp.types.core.ReportingDeliveryReadyWebhook` | `core/reporting-delivery-ready-webhook.json#` | compat |
| `ReportingDestinationSetupState` | `adcp.types.enums.ReportingDestinationSetupState` | `enums/reporting-destination-setup-state.json#` | compat |
| `ReportingFileCompression` | `adcp.types.core.ReportingFileCompression` | `core/reporting-file-compression.json#` | compat |
| `ReportingFileEntry` | `adcp.types.core.ReportingFileEntry` | `core/reporting-file-entry.json#` | compat |
| `ReportingFileManifest` | `adcp.types.core.ReportingFileManifest` | `core/reporting-file-manifest.json#` | compat |
| `ReportingFinality` | `adcp.types.enums.ReportingFinality` | `enums/reporting-finality.json#` | compat |
| `ReportingFrequency` | `adcp.types.enums.ReportingFrequency` | `enums/reporting-frequency.json#` | compat |
| `ReportingHealth` | `adcp.types.enums.ReportingHealth` | `enums/reporting-health.json#` | compat |
| `ReportingLedgerChangedWebhook` | `adcp.types.core.ReportingLedgerChangedWebhook` | `core/reporting-ledger-changed-webhook.json#` | compat |
| `ReportingMaterialization` | `adcp.types.core.ReportingMaterialization` | `core/reporting-materialization.json#` | compat |
| `ReportingObligation` | `adcp.types.core.ReportingObligation` | `core/reporting-obligation.json#` | compat |
| `ReportingObligationCounts` | `adcp.types.media_buy.GetReportingStatusResponseObligationCounts` | `media-buy/get-reporting-status-response.json#/properties/obligation_counts` | _adapter |
| `ReportingOperationsContact` | `adcp.types.core.ReportingDeliveryCapabilitiesOperationsContact` | `core/reporting-delivery-capabilities.json#/properties/operations_contact` | _adapter |
| `ReportingReceipt` | `adcp.types.core.ReportingReceipt` | `core/reporting-receipt.json#` | compat |
| `ReportingReconciliationMode` | `adcp.types.core.ReportingReconciliationMode` | `core/reporting-reconciliation-mode.json#` | compat |
| `ReportingReliabilityStatistics` | `adcp.types.core.ReportingReliabilityStatistics` | `core/reporting-reliability-statistics.json#` | compat |
| `ReportingReportDefinition` | `adcp.types.core.ReportingReportDefinition` | `core/reporting-report-definition.json#` | compat |
| `ReportingResource` | `adcp.types.core.ReportingResource` | `core/reporting-resource.json#` | compat |
| `ReportingRevision` | `adcp.types.core.ReportingRevision` | `core/reporting-revision.json#` | compat |
| `ReportingSchedule` | `adcp.types.core.ReportingSchedule` | `core/reporting-schedule.json#` | compat |
| `ReportingScheduleOffering` | `adcp.types.core.ReportingScheduleOffering` | `core/reporting-schedule-offering.json#` | compat |
| `ReportingStatusChangedWebhook` | `adcp.types.core.ReportingStatusChangedWebhook` | `core/reporting-status-changed-webhook.json#` | compat |
| `ReportingStatusIssue` | `adcp.types.core.ReportingStatusIssue` | `core/reporting-status-issue.json#` | compat |
| `ReportingVerification` | `adcp.types.core.ReportingVerification` | `core/reporting-verification.json#` | compat |
| `ReportingVerificationProfile` | `adcp.types.core.ReportingVerificationProfile` | `core/reporting-verification-profile.json#` | compat |
| `ReportingVerificationProfileSet` | `adcp.types.core.ReportingVerificationProfileSet` | `core/reporting-verification-profile-set.json#` | compat |
| `ReportingWebhook` | `adcp.types.core.ReportingWebhook` | `core/reporting-webhook.json#` | compat |
| `ReportingWriteDestination` | `adcp.types.core.ReportingWriteDestination` | `core/reporting-write-destination.json#` | compat |
| `RepresentationDestination` | `adcp.types.core.RepresentationDestination` | `core/representation-destination.json#` | compat |
| `RepresentationRejection` | `adcp.types.core.RepresentationRejection` | `core/representation-rejection.json#` | compat |
| `RepresentationSelection` | `adcp.types.core.RepresentationSelection` | `core/representation-selection.json#` | compat |
| `RepresentationSelectionStrategy` | `adcp.types.enums.RepresentationSelectionStrategy` | `enums/representation-selection-strategy.json#` | compat |
| `RequestProposalsInputRequired` | `adcp.types.media_buy.RequestProposalsInputRequired` | `media-buy/request-proposals-async-response-input-required.json#` | compat |
| `RequestProposalsRequest` | `adcp.types.media_buy.RequestProposalsRequest` | `media-buy/request-proposals-request.json#` | flat_only |
| `RequestProposalsResponse` | `adcp.types.media_buy.RequestProposalsResponse` | `media-buy/request-proposals-response.json#` | flat_only |
| `RequestProposalsSubmitted` | `adcp.types.media_buy.RequestProposalsSubmitted` | `media-buy/request-proposals-async-response-submitted.json#` | compat |
| `RequestProposalsWorking` | `adcp.types.media_buy.RequestProposalsWorking` | `media-buy/request-proposals-async-response-working.json#` | compat |
| `RequestSigningErrorCode` | `adcp.types.enums.RequestSigningErrorCode` | `enums/request-signing-error-code.json#` | compat |
| `RequoteRequiredDetails` | `adcp.types.error_details.RequoteRequiredDetails` | `error-details/requote-required.json#` | flat_only |
| `Response` | `adcp.types.core.ProtocolResponse` | `core/response.json#` | compat |
| `ResponsePayloadJwsEnvelope` | `adcp.types.core.ResponsePayloadJWSEnvelope` | `core/response-payload-jws-envelope.json#` | compat |
| `RestrictedAttribute` | `adcp.types.enums.RestrictedAttribute` | `enums/restricted-attribute.json#` | compat |
| `RevenueSharePricingOption` | `adcp.types.pricing_options.RevenueSharePricingOption` | `pricing-options/revenue-share-option.json#` | compat |
| `RevocationNotification` | `adcp.types.brand.RevocationNotification` | `brand/revocation-notification.json#` | compat |
| `RightType` | `adcp.types.enums.RightType` | `enums/right-type.json#` | compat |
| `RightUse` | `adcp.types.enums.RightUse` | `enums/right-use.json#` | compat |
| `RightsAttestationEvaluation` | `adcp.types.core.RightsAttestationEvaluation` | `core/rights-attestation-evaluation.json#` | compat |
| `RightsBillingPeriod` | `adcp.types.enums.RightsBillingPeriod` | `enums/rights-billing-period.json#` | compat |
| `RightsConstraint` | `adcp.types.core.RightsConstraint` | `core/rights-constraint.json#` | compat |
| `RightsPricingOption` | `adcp.types.brand.RightsPricingOption` | `brand/rights-pricing-option.json#` | compat |
| `RightsTerms` | `adcp.types.brand.RightsTerms` | `brand/rights-terms.json#` | compat |
| `ScanType` | `adcp.types.enums.ScanType` | `enums/scan-type.json#` | compat |
| `ScopedCreativeApproval` | `adcp.types.core.ScopedCreativeApproval` | `core/creative-approval-scope.json#` | compat |
| `SearchBrandsRequest` | `adcp.types.brand.SearchBrandsRequest` | `brand/search-brands-request.json#` | compat |
| `SearchBrandsResponse` | `adcp.types.brand.SearchBrandsResponse` | `brand/search-brands-response.json#` | compat |
| `SellerAgentReference` | `adcp.types.core.SellerAgentReference` | `core/seller-agent-ref.json#` | compat |
| `SellerPolicyDeclineReason` | `adcp.types.enums.SellerPolicyDeclineReason` | `enums/seller-policy-decline-reason.json#` | compat |
| `SiCapabilities` | `adcp.types.sponsored_intelligence.SICapabilities` | `sponsored-intelligence/si-capabilities.json#` | compat |
| `SiComponentCatalog` | `adcp.types.a2ui.SIComponentCatalog` | `a2ui/si-catalog.json#` | compat |
| `SiContextUse` | `adcp.types.sponsored_intelligence.SIContextUse` | `sponsored-intelligence/si-context-use.json#` | compat |
| `SiGetOfferingRequest` | `adcp.types.sponsored_intelligence.SIGetOfferingRequest` | `sponsored-intelligence/si-get-offering-request.json#` | compat |
| `SiGetOfferingResponse` | `adcp.types.sponsored_intelligence.SIGetOfferingResponse` | `sponsored-intelligence/si-get-offering-response.json#` | compat |
| `SiIdentity` | `adcp.types.sponsored_intelligence.SIIdentity` | `sponsored-intelligence/si-identity.json#` | compat |
| `SiInitiateSessionRequest` | `adcp.types.sponsored_intelligence.SIInitiateSessionRequest` | `sponsored-intelligence/si-initiate-session-request.json#` | compat |
| `SiInitiateSessionResponse` | `adcp.types.sponsored_intelligence.SIInitiateSessionResponse` | `sponsored-intelligence/si-initiate-session-response.json#` | compat |
| `SiSendMessageRequest` | `adcp.types.sponsored_intelligence.SISendMessageRequest` | `sponsored-intelligence/si-send-message-request.json#` | compat |
| `SiSendMessageResponse` | `adcp.types.sponsored_intelligence.SISendMessageResponse` | `sponsored-intelligence/si-send-message-response.json#` | compat |
| `SiSessionStatus` | `adcp.types.enums.SISessionStatus` | `enums/si-session-status.json#` | compat |
| `SiSponsoredContext` | `adcp.types.sponsored_intelligence.SISponsoredContext` | `sponsored-intelligence/si-sponsored-context.json#` | compat |
| `SiSponsoredContextDeclaredBy` | `adcp.types.sponsored_intelligence.SISponsoredContextDeclaredBy` | `sponsored-intelligence/si-sponsored-context.json#/properties/declared_by` | compat |
| `SiSponsoredContextReceipt` | `adcp.types.sponsored_intelligence.SISponsoredContextReceipt` | `sponsored-intelligence/si-sponsored-context-receipt.json#` | compat |
| `SiTerminateSessionRequest` | `adcp.types.sponsored_intelligence.SITerminateSessionRequest` | `sponsored-intelligence/si-terminate-session-request.json#` | compat |
| `SiTerminateSessionResponse` | `adcp.types.sponsored_intelligence.SITerminateSessionResponse` | `sponsored-intelligence/si-terminate-session-response.json#` | compat |
| `SiUiElement` | `adcp.types.sponsored_intelligence.SIUIElement` | `sponsored-intelligence/si-ui-element.json#` | compat |
| `Signal` | `adcp.types.core.WholesaleFeedEventSignal` | `core/wholesale-feed-event.json#/$defs/signal` | _adapter |
| `SignalAvailabilityType` | `adcp.types.enums.SignalAvailabilityType` | `enums/signal-catalog-type.json#` | compat |
| `SignalCatalogType` | `adcp.types.enums.SignalAvailabilityType` | `enums/signal-catalog-type.json#` | compat |
| `SignalCoverageForecast` | `adcp.types.core.SignalCoverageForecast` | `core/signal-coverage-forecast.json#` | compat |
| `SignalDefinition` | `adcp.types.core.SignalDefinition` | `core/signal-definition.json#` | compat |
| `SignalDefinitionEnrichment` | `adcp.types.core.SignalDefinitionEnrichment` | `core/signal-definition-enrichment.json#` | compat |
| `SignalFilters` | `adcp.types.core.SignalFilters` | `core/signal-filters.json#` | compat |
| `SignalForecastDimension` | `adcp.types.core.SignalForecastDimension` | `core/forecast-dimension-signal.json#` | compat |
| `SignalId` | `adcp.types.core.SignalID` | `core/signal-id.json#` | compat |
| `SignalListing` | `adcp.types.core.SignalListing` | `core/signal-listing.json#` | compat |
| `SignalModelingDisclosure` | `adcp.types.core.SignalModelingDisclosure` | `core/signal-modeling-disclosure.json#` | compat |
| `SignalRef` | `adcp.types.core.SignalRef` | `core/signal-ref.json#` | compat |
| `SignalSelectionGroupRule` | `adcp.types.core.SignalSelectionGroupRule` | `core/signal-selection-group-rule.json#` | compat |
| `SignalSource` | `adcp.types.enums.SignalSource` | `enums/signal-source.json#` | compat |
| `SignalTargeting` | `adcp.types.core.SignalTargeting` | `core/signal-targeting.json#` | compat |
| `SignalTargetingExpression` | `adcp.types.core.SignalTargetingExpression` | `core/signal-targeting-expression.json#` | compat |
| `SignalTargetingRules` | `adcp.types.core.SignalTargetingRules` | `core/signal-targeting-rules.json#` | compat |
| `SignalValueType` | `adcp.types.enums.SignalValueType` | `enums/signal-value-type.json#` | compat |
| `SlaWindow` | `adcp.types.core.SLAWindow` | `core/sla-window.json#` | compat |
| `Snapshot` | `adcp.types.creative.ListCreativesResponseCreativesItemSnapshot` | `creative/list-creatives-response.json#/properties/creatives/items/properties/snapshot` | _adapter |
| `SnapshotUnavailableReason` | `adcp.types.enums.SnapshotUnavailableReason` | `enums/snapshot-unavailable-reason.json#` | compat |
| `SocialPlacementSurface` | `adcp.types.enums.SocialPlacementSurface` | `enums/social-placement-surface.json#` | compat |
| `SortDirection` | `adcp.types.enums.SortDirection` | `enums/sort-direction.json#` | compat |
| `SortMetric` | `adcp.types.enums.SortMetric` | `enums/sort-metric.json#` | compat |
| `Special` | `adcp.types.core.Special` | `core/special.json#` | compat |
| `SpecialCategory` | `adcp.types.enums.SpecialCategory` | `enums/special-category.json#` | compat |
| `Specialism` | `adcp.types.enums.AdCPSpecialism` | `enums/specialism.json#` | compat |
| `SponsoredPlacementType` | `adcp.types.enums.SponsoredPlacementType` | `enums/sponsored-placement-type.json#` | compat |
| `SpotReportingCapability` | `adcp.types.core.SpotReportingCapability` | `core/spot-reporting-capability.json#` | compat |
| `StaleResponse` | `adcp.types.error_details.StaleResponseDetails` | `error-details/stale-response.json#` | compat |
| `StaleResponseDetails` | `adcp.types.error_details.StaleResponseDetails` | `error-details/stale-response.json#` | flat_only |
| `StoreItem` | `adcp.types.core.StoreItem` | `core/store-item.json#` | compat |
| `SyncAccountsRequest` | `adcp.types.account.SyncAccountsRequest` | `account/sync-accounts-request.json#` | compat |
| `SyncAccountsResponse` | `adcp.types.account.SyncAccountsResponse` | `account/sync-accounts-response.json#` | compat |
| `SyncAgentNotificationConfigsRequest` | `adcp.types.protocol.SyncAgentNotificationConfigsRequest` | `protocol/sync-agent-notification-configs-request.json#` | compat |
| `SyncAgentNotificationConfigsResponse` | `adcp.types.protocol.SyncAgentNotificationConfigsResponse` | `protocol/sync-agent-notification-configs-response.json#` | compat |
| `SyncAudiencesRequest` | `adcp.types.media_buy.SyncAudiencesRequest` | `media-buy/sync-audiences-request.json#` | compat |
| `SyncAudiencesResponse` | `adcp.types.media_buy.SyncAudiencesResponse` | `media-buy/sync-audiences-response.json#` | compat |
| `SyncAudiencesSuccessResponse` | `adcp.types.media_buy.SyncAudiencesSuccess` | `media-buy/sync-audiences-response.json#/oneOf/0` | _adapter |
| `SyncCatalogsInputRequired` | `adcp.types.media_buy.SyncCatalogsInputRequired` | `media-buy/sync-catalogs-async-response-input-required.json#` | compat |
| `SyncCatalogsRequest` | `adcp.types.media_buy.SyncCatalogsRequest` | `media-buy/sync-catalogs-request.json#` | compat |
| `SyncCatalogsResponse` | `adcp.types.media_buy.SyncCatalogsResponse` | `media-buy/sync-catalogs-response.json#` | compat |
| `SyncCatalogsSubmitted` | `adcp.types.media_buy.SyncCatalogsSubmitted` | `media-buy/sync-catalogs-async-response-submitted.json#` | compat |
| `SyncCatalogsSuccessResponse` | `adcp.types.media_buy.SyncCatalogsSuccess` | `media-buy/sync-catalogs-response.json#/oneOf/0` | _adapter |
| `SyncCatalogsWorking` | `adcp.types.media_buy.SyncCatalogsWorking` | `media-buy/sync-catalogs-async-response-working.json#` | compat |
| `SyncCreativesInputRequired` | `adcp.types.creative.SyncCreativesInputRequired` | `creative/sync-creatives-async-response-input-required.json#` | compat |
| `SyncCreativesResponse` | `adcp.types.creative.SyncCreativesResponse` | `creative/sync-creatives-response.json#` | flat_only |
| `SyncCreativesResponse1` | `adcp.types.creative.SyncCreativesSuccess` | `creative/sync-creatives-response.json#/oneOf/0` | _adapter |
| `SyncCreativesSubmitted` | `adcp.types.creative.SyncCreativesSubmitted` | `creative/sync-creatives-async-response-submitted.json#` | compat |
| `SyncCreativesSuccessResponse` | `adcp.types.creative.SyncCreativesSuccess` | `creative/sync-creatives-response.json#/oneOf/0` | _adapter |
| `SyncCreativesWorking` | `adcp.types.creative.SyncCreativesWorking` | `creative/sync-creatives-async-response-working.json#` | compat |
| `SyncEventSourcesRequest` | `adcp.types.media_buy.SyncEventSourcesRequest` | `media-buy/sync-event-sources-request.json#` | compat |
| `SyncEventSourcesResponse` | `adcp.types.media_buy.SyncEventSourcesResponse` | `media-buy/sync-event-sources-response.json#` | compat |
| `SyncGovernanceRequest` | `adcp.types.account.SyncGovernanceRequest` | `account/sync-governance-request.json#` | compat |
| `SyncGovernanceResponse` | `adcp.types.account.SyncGovernanceResponse` | `account/sync-governance-response.json#` | compat |
| `SyncPlansRequest` | `adcp.types.governance.SyncPlansRequest` | `governance/sync-plans-request.json#` | compat |
| `SyncPlansResponse` | `adcp.types.governance.SyncPlansResponse` | `governance/sync-plans-response.json#` | compat |
| `SyncPrincipalRequest` | `adcp.types.protocol.SyncPrincipalRequest` | `protocol/sync-principal-request.json#` | flat_only |
| `SyncPrincipalResponse` | `adcp.types.protocol.SyncPrincipalResponse` | `protocol/sync-principal-response.json#` | flat_only |
| `SyncReportingReceiptsRequest` | `adcp.types.media_buy.SyncReportingReceiptsRequest` | `media-buy/sync-reporting-receipts-request.json#` | compat |
| `SyncReportingReceiptsResponse` | `adcp.types.media_buy.SyncReportingReceiptsResponse` | `media-buy/sync-reporting-receipts-response.json#` | compat |
| `SyncReportingStatusRequest` | `adcp.types.media_buy.SyncReportingStatusRequest` | `media-buy/sync-reporting-status-request.json#` | compat |
| `SyncReportingStatusResponse` | `adcp.types.media_buy.SyncReportingStatusResponse` | `media-buy/sync-reporting-status-response.json#` | compat |
| `Talent` | `adcp.types.core.Talent` | `core/talent.json#` | compat |
| `TalentRole` | `adcp.types.enums.TalentRole` | `enums/talent-role.json#` | compat |
| `TargetingModification` | `adcp.types.core.TargetingModification` | `core/targeting-modification.json#` | compat |
| `TargetingOverlay` | `adcp.types.core.TargetingOverlay` | `core/targeting.json#` | compat |
| `TargetingOverlayInput` | `adcp.types.core.TargetingOverlayInput` | `core/targeting-input.json#` | compat |
| `TargetingOverlayRequirements` | `adcp.types.core.TargetingOverlayRequirements` | `core/targeting-overlay-requirements.json#` | compat |
| `TargetingOverlaySupport` | `adcp.types.core.TargetingOverlaySupport` | `core/targeting-overlay-support.json#` | compat |
| `TargetingUnknownAgeEligibilityConstraint` | `adcp.types.core.TargetingUnknownAgeEligibilityConstraint` | `core/targeting-unknown-age-eligibility-constraint.json#` | compat |
| `TargetingVerifiedAgeBasisConstraint` | `adcp.types.core.TargetingVerifiedAgeBasisConstraint` | `core/targeting-verified-age-basis-constraint.json#` | compat |
| `TaskType` | `adcp.types.enums.TaskType` | `enums/task-type.json#` | compat |
| `TasksGetRequest` | `adcp.types.core.TasksGetRequest` | `core/tasks-get-request.json#` | compat |
| `TasksGetResponse` | `adcp.types.core.TasksGetResponse` | `core/tasks-get-response.json#` | compat |
| `TasksListRequest` | `adcp.types.core.TasksListRequest` | `core/tasks-list-request.json#` | compat |
| `TasksListResponse` | `adcp.types.core.TasksListResponse` | `core/tasks-list-response.json#` | compat |
| `TextAsset` | `adcp.types.core.TextAsset` | `core/assets/text-asset.json#` | compat |
| `TextAssetRequirements` | `adcp.types.core.TextAssetRequirements` | `core/requirements/text-asset-requirements.json#` | compat |
| `TextContent` | `adcp.types.core.TextAsset` | `core/assets/text-asset.json#` | _adapter |
| `TimeBasedPricingOption` | `adcp.types.pricing_options.TimeBasedPricingOption` | `pricing-options/time-option.json#` | compat |
| `TimeForecastDimension` | `adcp.types.core.TimeForecastDimension` | `core/forecast-dimension-time.json#` | compat |
| `TmpError` | `adcp.types.trusted_match.TMPError` | `trusted-match/error.json#` | compat |
| `TmpOffer` | `adcp.types.trusted_match.Offer` | `trusted-match/offer.json#` | _adapter |
| `TmpProviderRegistration` | `adcp.types.trusted_match.TMPProviderRegistration` | `trusted-match/provider-registration.json#` | compat |
| `TmpResponseType` | `adcp.types.enums.TMPResponseType` | `enums/response-type.json#` | compat |
| `TmpxChunk` | `adcp.types.trusted_match.TMPXChunk` | `trusted-match/tmpx-chunk.json#` | compat |
| `TrackerExecutionActor` | `adcp.types.enums.TrackerExecutionActor` | `enums/tracker-execution-actor.json#` | compat |
| `TrackerExecutionContract` | `adcp.types.core.TrackerExecutionContract` | `core/tracker-execution-contract.json#` | compat |
| `TrackerExecutionSelector` | `adcp.types.core.TrackerExecutionSelector` | `core/tracker-execution-selector.json#` | compat |
| `TrackerFiringPath` | `adcp.types.enums.TrackerFiringPath` | `enums/tracker-firing-path.json#` | compat |
| `Transformer` | `adcp.types.core.Transformer` | `core/transformer.json#` | compat |
| `TransformerParam` | `adcp.types.core.TransformerParam` | `core/transformer-param.json#` | compat |
| `TransportMode` | `adcp.types.enums.TransportMode` | `enums/transport-mode.json#` | compat |
| `TravelTimeUnit` | `adcp.types.enums.TravelTimeUnit` | `enums/travel-time-unit.json#` | compat |
| `TruncationSentinel` | `adcp.types.core.TruncationSentinel` | `core/truncation-sentinel.json#` | compat |
| `TrustedMatch` | `adcp.types.core.ProductTrustedMatch` | `core/product.json#/properties/trusted_match` | _adapter |
| `UIDType` | `adcp.types.enums.UIDType` | `enums/uid-type.json#` | compat |
| `UidType` | `adcp.types.enums.UIDType` | `enums/uid-type.json#` | compat |
| `UniversalMacro` | `adcp.types.enums.UniversalMacro` | `enums/universal-macro.json#` | compat |
| `UnsupportedRefinementDimensionDetails` | `adcp.types.error_details.UnsupportedRefinementDimensionDetails` | `error-details/unsupported-refinement-dimension.json#` | flat_only |
| `UpdateCollectionListRequest` | `adcp.types.collection.UpdateCollectionListRequest` | `collection/update-collection-list-request.json#` | compat |
| `UpdateCollectionListResponse` | `adcp.types.collection.UpdateCollectionListResponse` | `collection/update-collection-list-response.json#` | compat |
| `UpdateContentStandardsRequest` | `adcp.types.content_standards.UpdateContentStandardsRequest` | `content-standards/update-content-standards-request.json#` | compat |
| `UpdateContentStandardsResponse` | `adcp.types.content_standards.UpdateContentStandardsResponse` | `content-standards/update-content-standards-response.json#` | compat |
| `UpdateFrequency` | `adcp.types.enums.UpdateFrequency` | `enums/update-frequency.json#` | compat |
| `UpdateMediaBuyInputRequired` | `adcp.types.media_buy.UpdateMediaBuyInputRequired` | `media-buy/update-media-buy-async-response-input-required.json#` | compat |
| `UpdateMediaBuyRequest` | `adcp.types.media_buy.UpdateMediaBuyRequest` | `media-buy/update-media-buy-request.json#` | flat_only |
| `UpdateMediaBuySubmitted` | `adcp.types.media_buy.UpdateMediaBuySubmitted` | `media-buy/update-media-buy-async-response-submitted.json#` | compat |
| `UpdateMediaBuyWorking` | `adcp.types.media_buy.UpdateMediaBuyWorking` | `media-buy/update-media-buy-async-response-working.json#` | compat |
| `UpdatePropertyListRequest` | `adcp.types.property.UpdatePropertyListRequest` | `property/update-property-list-request.json#` | compat |
| `UpdatePropertyListResponse` | `adcp.types.property.UpdatePropertyListResponse` | `property/update-property-list-response.json#` | compat |
| `UpdateRightsRequest` | `adcp.types.brand.UpdateRightsRequest` | `brand/update-rights-request.json#` | compat |
| `UpdateRightsResponse` | `adcp.types.brand.UpdateRightsResponse` | `brand/update-rights-response.json#` | compat |
| `UrlAsset` | `adcp.types.core.URLAsset` | `core/assets/url-asset.json#` | compat |
| `UrlAssetRequirements` | `adcp.types.core.URLAssetRequirements` | `core/requirements/url-asset-requirements.json#` | compat |
| `UrlAssetType` | `adcp.types.enums.URLAssetType` | `enums/url-asset-type.json#` | compat |
| `UrlContent` | `adcp.types.core.URLAsset` | `core/assets/url-asset.json#` | _adapter |
| `UserMatch` | `adcp.types.core.UserMatch` | `core/user-match.json#` | compat |
| `V1CanonicalMapping` | `adcp.types.registries.V1V2CanonicalFormatMappingRegistry` | `registries/v1-canonical-mapping.json#` | compat |
| `V1V2CanonicalFormatMappingRegistry` | `adcp.types.registries.V1V2CanonicalFormatMappingRegistry` | `registries/v1-canonical-mapping.json#` | compat |
| `ValidateContentDeliveryRequest` | `adcp.types.content_standards.ValidateContentDeliveryRequest` | `content-standards/validate-content-delivery-request.json#` | compat |
| `ValidateContentDeliveryResponse` | `adcp.types.content_standards.ValidateContentDeliveryResponse` | `content-standards/validate-content-delivery-response.json#` | compat |
| `ValidateInputRequest` | `adcp.types.creative.ValidateInputRequest` | `creative/validate-input-request.json#` | compat |
| `ValidateInputResponse` | `adcp.types.creative.ValidateInputResponse` | `creative/validate-input-response.json#` | compat |
| `ValidateInputResult` | `adcp.types.creative.ValidateInputResult` | `creative/validate-input-result.json#` | compat |
| `ValidatePropertyDeliveryRequest` | `adcp.types.property.ValidatePropertyDeliveryRequest` | `property/validate-property-delivery-request.json#` | compat |
| `ValidatePropertyDeliveryResponse` | `adcp.types.property.ValidatePropertyDeliveryResponse` | `property/validate-property-delivery-response.json#` | compat |
| `ValidationMode` | `adcp.types.enums.ValidationMode` | `enums/validation-mode.json#` | compat |
| `VastAsset` | `adcp.types.core.VASTAsset` | `core/assets/vast-asset.json#` | compat |
| `VastAssetRequirements` | `adcp.types.core.VASTAssetRequirements` | `core/requirements/vast-asset-requirements.json#` | compat |
| `VastMediaDeliveryMethod` | `adcp.types.enums.VASTMediaDeliveryMethod` | `enums/vast-media-delivery-method.json#` | compat |
| `VastMediafileRequirements` | `adcp.types.core.VASTMediaFileRequirements` | `core/vast-media-file-requirements.json#` | compat |
| `VastTrackerAsset` | `adcp.types.core.VASTTrackerAsset` | `core/assets/vast-tracker-asset.json#` | compat |
| `VastTrackerConstraints` | `adcp.types.core.VASTTrackerConstraints` | `core/vast-tracker-constraints.json#` | compat |
| `VastTrackingEvent` | `adcp.types.enums.VASTTrackingEvent` | `enums/vast-tracking-event.json#` | compat |
| `VastVersion` | `adcp.types.enums.VASTVersion` | `enums/vast-version.json#` | compat |
| `VastVersionMismatchDetails` | `adcp.types.error_details.VASTVersionMismatchDetails` | `error-details/vast-version-mismatch.json#` | compat |
| `VcpmAuctionPricingOption` | `adcp.types.pricing_options.VCPMPricingOption` | `pricing-options/vcpm-option.json#` | _adapter |
| `VcpmFixedRatePricingOption` | `adcp.types.pricing_options.VCPMPricingOption` | `pricing-options/vcpm-option.json#` | _adapter |
| `VcpmPricingOption` | `adcp.types.pricing_options.VCPMPricingOption` | `pricing-options/vcpm-option.json#` | compat |
| `VehicleItem` | `adcp.types.core.VehicleItem` | `core/vehicle-item.json#` | compat |
| `VendorErrorCodeRegistry` | `adcp.types.error_details.VendorErrorCodeRegistry` | `error-details/vendor-error-codes.json#` | flat_only |
| `VendorMetricOptimizationSupportedMetric` | `adcp.types.core.VendorMetricOptimizationSupportedMetric` | `core/vendor-metric-optimization-supported-metric.json#` | compat |
| `VendorMetricValue` | `adcp.types.core.VendorMetricValue` | `core/vendor-metric-value.json#` | compat |
| `VendorPricing` | `adcp.types.core.VendorPricing` | `core/signal-pricing.json#` | compat |
| `VendorPricingOption` | `adcp.types.core.VendorPricingOption` | `core/vendor-pricing-option.json#` | compat |
| `VendorRelationship` | `adcp.types.enums.VendorRelationship` | `enums/vendor-relationship.json#` | compat |
| `VerificationStatus` | `adcp.types.brand.VerificationStatus` | `brand/verification-status.json#` | compat |
| `VerifyBrandClaimPayload` | `adcp.types.brand.VerifyBrandClaimResponseSignedResponsePayload` | `brand/verify-brand-claim-response.json#/definitions/signed_response/allOf/1/properties/payload` | _adapter |
| `VerifyBrandClaimRequest` | `adcp.types.brand.VerifyBrandClaimRequest` | `brand/verify-brand-claim-request.json#` | compat |
| `VerifyBrandClaimResponse` | `adcp.types.brand.VerifyBrandClaimResponse` | `brand/verify-brand-claim-response.json#` | compat |
| `VerifyBrandClaimSignedResponse` | `adcp.types.brand.VerifyBrandClaimResponseSignedResponse` | `brand/verify-brand-claim-response.json#/definitions/signed_response` | _adapter |
| `VerifyBrandClaimSignedSuccessPayload` | `adcp.types.brand.VerifyBrandClaimResponseSignedSuccessPayload` | `brand/verify-brand-claim-response.json#/definitions/signed_success_payload` | _adapter |
| `VerifyBrandClaimsRequest` | `adcp.types.brand.VerifyBrandClaimsRequestBulk` | `brand/verify-brand-claims-request.json#` | compat |
| `VerifyBrandClaimsRequestBulk` | `adcp.types.brand.VerifyBrandClaimsRequestBulk` | `brand/verify-brand-claims-request.json#` | compat |
| `VerifyBrandClaimsResponse` | `adcp.types.brand.VerifyBrandClaimsResponseBulk` | `brand/verify-brand-claims-response.json#` | compat |
| `VerifyBrandClaimsResponseBulk` | `adcp.types.brand.VerifyBrandClaimsResponseBulk` | `brand/verify-brand-claims-response.json#` | compat |
| `VersionUnsupportedDetails` | `adcp.types.error_details.VersionUnsupportedDetails` | `error-details/version-unsupported.json#` | flat_only |
| `Video` | `adcp.types.sponsored_intelligence.Video` | `sponsored-intelligence/si-capabilities.json#/properties/modalities/properties/video/oneOf/1` | compat |
| `VideoAsset` | `adcp.types.core.VideoAsset` | `core/assets/video-asset.json#` | compat |
| `VideoAssetRequirements` | `adcp.types.core.VideoAssetRequirements` | `core/requirements/video-asset-requirements.json#` | compat |
| `VideoBrief` | `adcp.types.creative.VideoBrief` | `creative/video-brief.json#` | compat |
| `VideoContent` | `adcp.types.core.VideoAsset` | `core/assets/video-asset.json#` | _adapter |
| `VideoPlacementType` | `adcp.types.enums.VideoPlacementType` | `enums/video-placement-type.json#` | compat |
| `ViewThresholdBasis` | `adcp.types.enums.ViewThresholdBasis` | `enums/view-threshold-basis.json#` | compat |
| `ViewabilityStandard` | `adcp.types.enums.ViewabilityStandard` | `enums/viewability-standard.json#` | compat |
| `Voice` | `adcp.types.sponsored_intelligence.Voice` | `sponsored-intelligence/si-capabilities.json#/properties/modalities/properties/voice/oneOf/1` | compat |
| `Warning` | `adcp.types.core.Warning` | `core/warning.json#` | compat |
| `WarningAffectedResource` | `adcp.types.core.WarningAffectedResource` | `core/warning-resource.json#` | compat |
| `WarningCode` | `adcp.types.enums.WarningCode` | `enums/warning-code.json#` | compat |
| `WatermarkMediaType` | `adcp.types.enums.WatermarkMediaType` | `enums/watermark-media-type.json#` | compat |
| `WcagLevel` | `adcp.types.enums.WCAGLevel` | `enums/wcag-level.json#` | compat |
| `WebhookActivityRecord` | `adcp.types.core.WebhookActivityRecord` | `core/webhook-activity-record.json#` | compat |
| `WebhookAsset` | `adcp.types.core.WebhookAsset` | `core/assets/webhook-asset.json#` | compat |
| `WebhookAssetRequirements` | `adcp.types.core.WebhookAssetRequirements` | `core/requirements/webhook-asset-requirements.json#` | compat |
| `WebhookChallenge` | `adcp.types.core.WebhookChallenge` | `core/webhook-challenge.json#` | compat |
| `WebhookChallengeResponse` | `adcp.types.core.WebhookChallengeResponse` | `core/webhook-challenge-response.json#` | compat |
| `WebhookContent` | `adcp.types.core.WebhookAsset` | `core/assets/webhook-asset.json#` | _adapter |
| `WebhookResponseType` | `adcp.types.enums.WebhookResponseType` | `enums/webhook-response-type.json#` | compat |
| `WebhookSecurityMethod` | `adcp.types.enums.WebhookSecurityMethod` | `enums/webhook-security-method.json#` | compat |
| `WholesaleFeedEvent` | `adcp.types.core.WholesaleFeedEvent` | `core/wholesale-feed-event.json#` | compat |
| `WholesaleFeedWebhook` | `adcp.types.core.WholesaleFeedWebhook` | `core/wholesale-feed-webhook.json#` | compat |
| `XEntityTypes` | `adcp.types.core.XEntityTypes` | `core/x-entity-types.json#` | compat |
| `ZipAsset` | `adcp.types.core.ZipAsset` | `core/assets/zip-asset.json#` | compat |

**WHAT IS NOT A ROW, counted and attributed rather than omitted.**
1,391 words stand in the four tables and 1,077 are rows. **The other
314 resolve too** — none of them is a failure this derivation
discovered — but each reaches something other than a class compiled from a document, so the
triple a row states has no third element, and each already has a section of its own above:

* **203** — upstream's own hand-written declaration, served from the file restored at upstream's own path. §1's subject: no document states it, so there is no emitted class and no node.
* **72** — an `Annotated` constrained scalar or a union over branches — a type expression and not a class, so it has no `adcp.types.<domain>.<Name>` of its own. §3's subject.
* **32** — upstream's `canonical_creative` and `projections` layers, which SUBCLASS a class of ours. §5's subject — the word reaches their subclass and not our emitted class, which is exactly the substitution a row here must not claim.
* **7** — a `frozenset`, a tuple or a helper upstream's restored files declare — `MEDIA_BUY_LEGACY_STATUS_VALUES` is the measured case. §1's subject.

The subclass set is the one this derivation had to be built around, and it is the reason the
record is read from `vars(cls)` and never with `getattr`: such a class INHERITS
`__adcp_schema__` from the class of ours it extends, so `getattr` finds a record, the word
looks like it reaches an emitted class, and it does not — it reaches a different object.
Measured: 32 rows whose
identity claim would have been false.

**Re-derivable, and every row is executable.**
`survey/alias_destinations.py --report` prints every figure above and each withheld set by
name. `tests_emit/test_the_resolving_spellings.py` parses the table out of this file and, for
every row, imports the word from `adcp.types`, imports the path, and requires the two to be
**the same object by identity** — then re-derives the whole set and requires it to equal what
is written here, so a bundle bump that moves an emitted name reddens rather than quietly
leaving this table behind.

**And 2 further nodes dispatch on a key set the same way
and are not in `j0fr`'s 8** —
`core/creative-representation.json#`, `creative/sync-creatives-request.json#/properties/creatives/items`. They are reported here
rather than folded into the count above, because the set named there is that row's
measurement and re-deriving it would be a second derivation of one number.

<!-- END GENERATED -->
---

## Re-deriving this document, and the gate that keeps it true

Two interpreters, because the two trees cannot be imported into one — the table at the top
of this document is why.

```bash
uv venv $TMPDIR/up && uv pip install --python $TMPDIR/up/bin/python adcp==9.6.1
PYTHONPATH=.:src ./.venv/bin/python survey/migration_notes.py --dump-ours $TMPDIR/ours-identities.json
$TMPDIR/up/bin/python survey/migration_notes.py --corpus /srv/ws/wt-v92 --ours $TMPDIR/ours-identities.json --guide docs/migration-from-upstream.md
```

`--guide` makes the run a **gate**: every name in the six owed buckets must appear inside a
backticked span of this file, or the run exits 1 and names the ones missing. That is what
keeps this document from falling quietly behind an upstream release — a new name in
upstream's examples that nothing here answers is a red run, not a careful reread.

**`--corpus` IS REQUIRED AND HAS NO DEFAULT, AND AN EMPTY CORPUS IS AN ERROR RATHER THAN A
PASS.** This is the defect the gate itself had, and it is recorded because it is the exact
failure `final-state.md` forbids: *a check that passes when nothing happens decides
nothing.* Pointed at `/srv/ws/adcp-upstream` — a sparse, blobless clone whose
`sparse-checkout` is `static/schemas` plus `scripts`, with no `examples/` and no docs tree —
an earlier form of this script reported **"names every one of the 0 names it owes an entry
for"** and exited 0, **and went on reporting it with an owed name deleted from this
document.** The gate could not fail for any content of the guide, in the one environment a
reader was most likely to run it in.

So the three sets the run ranges over go through `tests/nodeset.claimed`, the idiom this
repository already has for refusing an empty one, and each names the corpus path it looked
in and the globs it looked for:

- the **example and skill sources** (`examples/**/*.py`, `skills/**/*.py`),
- the **documentation fences** (`README.md`, `llms.txt`, `MIGRATION*.md`, `docs/**/*.md`,
  `skills/**/*.md`) — claimed *separately*, because a checkout can carry one half and not
  the other and a claim on the total would be satisfied by the README alone,
- and the **owed set** itself, which is the one that bit.

A refusal reads `REFUSED: example and skill sources under <path> (examples/**/*.py,
skills/**/*.py): empty set of nodes -- every assertion over it holds vacuously`, and exits
1. **Six red directions are demonstrated rather than argued**: an owed name removed from
this document — tried three times, one name from the machinery set, one from §4 and one from
§6, each reported by name with exit 1; the sparse clone; a tree with docs and no examples; a
tree with examples and no docs; an empty directory; and `--corpus` omitted, which `argparse`
refuses with exit 2.

The run writes its partition to `--out`, which **defaults under `TMPDIR` and never the
working directory** — an earlier form wrote `migration-partition.json` into the worktree
root whenever it was invoked from there. That file carries, per name: where consumer code
spells it, its defining module on upstream's wheel, its bucket, its upstream identity, the
bundle document behind it where there is one, and the nearest identities of ours with the
agreement number — plus the corpus path and its file and fence counts, so a figure can be
checked against the corpus it came from. Every figure in this document is a field of that
file.
