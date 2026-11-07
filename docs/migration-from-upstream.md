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
