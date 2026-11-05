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

Upstream's `adcp.types.canonical_creative` is a hand-written layer, and `adcp.Product`,
`adcp.Package`, `adcp.CreativeManifest`, `adcp.Format` and `adcp.types.ProductFormatDeclaration`
all resolve into it. **All five have a class of ours carrying the same word, and only three
of the five are a rename** — the field sets below are what tells them apart, which is the
whole reason the word is not allowed to decide.

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
