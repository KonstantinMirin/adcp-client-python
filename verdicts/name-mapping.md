# The name mapping: 113 names upstream's own code imports and our surface does not hold

`survey/name_census.py` measured 1,105 class-shaped names upstream 9.6.1 declares and this
tree does not. 104 of them are imported by upstream's TESTS and 31 by their kept MACHINERY
— **113 distinct names, blocking 73 of their test files** (`survey/blocking_names.py`, run
against upstream at `4ed0bce87`). The other 992 are referenced by neither and cost nothing.

This file is the verdict for all 113: what each name IS upstream, which document and
pointer states its subject, which declaration of ours holds that subject, and what is owed
— an alias, a migration note, nothing, or a change to our EMISSION. Reading 10 is the rule
it is decided by: **a name with no schema subject gets a migration note and never a class.**
Nothing here mints a class to satisfy an import.

**Two strengths of evidence, and the table says which each row carries.**

* `measured` (44 rows) — the row was decided by a per-row reading: upstream's declaration
  read at its file and line, the subject recovered from the pinned bundle by keyword or by
  pointer, our declaration found BY POINTER and not by name, and the two ACCEPTED SETS
  probed against each other on payloads the document admits and refuses.
* `joined` (69 rows) — the row's document, pointer and target come from the committed
  node-keyed join (`survey/probes/probe_map.json`, built under the four rules
  `survey/node_keyed_aliases.py` states) plus an AST reading of upstream's own alias chain
  at `4ed0bce87`. The subject is located; the accepted sets have NOT been probed row by
  row. §5 says what settles them.

A row's ACTION is not a function of its strength: `MIGRATION_NOTE` on a `joined` row means
no node states the subject, which is a fact about the bundle and needs no probe.

**Where an alias may point, and where it may not.** 79 of the 113 are on upstream's
DELIBERATE flat surface — the hand-written `__all__` of `src/adcp/types/__init__.py` and
`src/adcp/__init__.py` at `4ed0bce87`, 1,197 names between them. The other 34 are reachable
only at a generated module path (`adcp.types.domains.core.targeting_modification.Path`,
`…bundled.protocol.get_adcp_capabilities_response.Encoding`), so no application import can
have been written against them and the row takes a note rather than a spelling. That
discriminator, and not the blocked-file count, is why `Path` and `Encoding` — 3 and 6 files
by the raw grep — are `MIGRATION_NOTE` with a corrected count of 0: every one of those
occurrences is `pathlib.Path`, `cryptography…Encoding` or the string `"Accept-Encoding"`.

## 1. The table

Sorted by blocked test files descending, because that is the order the work should happen
in. `blocks tests` is the corrected figure where a per-row reading found the raw grep count
to be a false positive; the raw figure is kept beside it. `blocks machinery` counts files
under upstream's `src/adcp/` outside their type tree.

| # | upstream name | category | our dotted path | document | pointer | action | blocks tests | blocks machinery | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `CreateMediaBuySuccessResponse` | SPELLING | `adcp.types.media_buy.CreateMediaBuySuccess` | `media-buy/create-media-buy-response.json` | `#/oneOf/0` | **ALIAS** | 17 | 1 | joined |
| 2 | `CanonicalBoundaryModel` | MACHINERY | — | — | — | **NONE** | 8 | 0 | measured |
| 3 | `UpdateMediaBuySuccessResponse` | SPELLING | `adcp.types.media_buy.UpdateMediaBuySuccess` | `media-buy/update-media-buy-response.json` | `#/oneOf/0` | **ALIAS** | 5 | 2 | joined |
| 4 | `DeliveryCreative` | SPELLING | `adcp.types.creative.GetCreativeDeliveryResponseCreativesItem` | `creative/get-creative-delivery-response.json` | `#/properties/creatives/items` | **ALIAS** | 4 | 0 | measured |
| 5 | `MajorVersion` | ARTIFACT | `adcp.types.constraints.IntMin1` | `protocol/get-adcp-capabilities-response.json` | `#/properties/adcp/properties/major_versions/items` | **ALIAS** | 4 | 0 | joined |
| 6 | `PRIMARY_CANONICAL_MODELS` | MACHINERY | — | — | — | **NONE** | 4 | 0 | measured |
| 7 | `InlineVastAsset` | ARTIFACT | `adcp.types.core.VASTAssetInline` | `core/assets/vast-asset.json` | `#/oneOf/1` | **ALIAS** | 3 | 1 | joined |
| 8 | `UrlDaastAsset` | ARTIFACT | `adcp.types.core.DAASTAssetUrl` | `core/assets/daast-asset.json` | `#/oneOf/0` | **ALIAS** | 3 | 1 | joined |
| 9 | `UrlVastAsset` | ARTIFACT | `adcp.types.core.VASTAssetUrl` | `core/assets/vast-asset.json` | `#/oneOf/0` | **ALIAS** | 3 | 1 | joined |
| 10 | `CreateMediaBuySubmittedResponse` | SPELLING | `adcp.types.media_buy.CreateMediaBuyResponseSubmitted` | `media-buy/create-media-buy-response.json` | `#/oneOf/2` | **ALIAS** | 3 | 0 | joined |
| 11 | `DOMAINS` | MACHINERY | — | — | — | **NONE** | 3 | 0 | joined |
| 12 | `VendorPricingOptionUnion` | NO_SUBJECT | — | `core/vendor-pricing-option.json` | no node states the union | **UNDECIDED** | 3 | 0 | joined |
| 13 | `AssetInstance` | NO_SUBJECT | union over our 11 asset classes | `core/assets/asset-union.json` | `#/oneOf (members, not the union)` | **ALIAS** | 2 | 1 | joined |
| 14 | `AssetInstanceType` | NO_SUBJECT | — | `creative/asset-types/index.json` | `#/asset_types` | **MIGRATION_NOTE** | 2 | 1 | measured |
| 15 | `InlineDaastAsset` | SPELLING | `adcp.types.core.DAASTAssetInline` | `core/assets/daast-asset.json` | `#/oneOf/1` | **ALIAS** | 2 | 1 | measured |
| 16 | `AuthorizedAgents` | ARTIFACT | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/0` | **ALIAS** | 2 | 0 | joined |
| 17 | `CANONICAL_ROOT` | MACHINERY | `adcp.migrate.v3_to_v4.CANONICAL_TYPES_ROOT` | — | — | **ALIAS** | 2 | 0 | measured |
| 18 | `CanonicalFormatKindStr` | NO_SUBJECT | — | — | — | **MIGRATION_NOTE** | 2 | 0 | joined |
| 19 | `DEPRECATED_ROOT` | MACHINERY | `adcp.migrate.v3_to_v4.DEPRECATED_TYPES_ROOT` | — | — | **ALIAS** | 2 | 0 | joined |
| 20 | `FormatAssetUnion` | NO_SUBJECT | — | `core/format.json` | union over numbered Assets* | **MIGRATION_NOTE** | 2 | 0 | joined |
| 21 | `GroupFormatAssetUnion` | NO_SUBJECT | — | `core/format.json` | union over numbered Assets31+ | **MIGRATION_NOTE** | 2 | 0 | joined |
| 22 | `RefineProposalsResponse1` | ARTIFACT | `adcp.types.media_buy.RefineProposalsResponseCompleted` | `media-buy/refine-proposals-response.json` | `#/anyOf/0` | **ALIAS** | 2 | 0 | joined |
| 23 | `RepeatableAssetGroup` | NO_SUBJECT | — | `core/format.json` | factory-built, no node located | **UNDECIDED** | 2 | 0 | joined |
| 24 | `SupportedMajor` | ARTIFACT | `adcp.types.constraints.IntMin1` | `error-details/version-unsupported.json` | `#/properties/supported_majors/items` | **ALIAS** | 2 | 0 | measured |
| 25 | `SupportedVersion` | ARTIFACT | `adcp.types.constraints.AdCPVersionEnvelopeAdcpVersion` | `error-details/version-unsupported.json` | `#/properties/supported_versions/items` | **ALIAS** | 2 | 0 | measured |
| 26 | `SyncAccountsAccount` | SPELLING | `adcp.types.account.SyncAccountsSuccessAccountsItem` | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items` | **ALIAS** | 2 | 0 | joined |
| 27 | `UpdateMediaBuySubmittedResponse` | SPELLING | `adcp.types.media_buy.UpdateMediaBuyResponseSubmitted` | `media-buy/update-media-buy-response.json` | `#/oneOf/2` | **ALIAS** | 2 | 0 | measured |
| 28 | `VastAsset1` | ARTIFACT | `adcp.types.core.VASTAssetUrl` | `core/assets/vast-asset.json` | `#/oneOf/0` | **ALIAS** | 2 | 0 | joined |
| 29 | `AuthorizedAgentsByInlineProperties` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/2` | **ALIAS** | 1 | 1 | measured |
| 30 | `AuthorizedAgentsByPropertyId` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/0` | **ALIAS** | 1 | 1 | joined |
| 31 | `AuthorizedAgentsByPropertyTag` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/1` | **ALIAS** | 1 | 1 | joined |
| 32 | `AuthorizedAgentsByPublisherProperties` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/3` | **ALIAS** | 1 | 1 | joined |
| 33 | `AuthorizedAgentsBySignalId` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/4` | **ALIAS** | 1 | 1 | joined |
| 34 | `AuthorizedAgentsBySignalTag` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/5` | **ALIAS** | 1 | 1 | joined |
| 35 | `CatalogGroupBinding` | SPELLING | `adcp.types.core.CatalogFieldBindingCatalogGroup` | `core/requirements/catalog-field-binding.json` | `#/oneOf/2` | **ALIAS** | 1 | 1 | measured |
| 36 | `IdentityMatchTmpxMacro` | NO_SUBJECT | — | `trusted-match/identity-match-response.json` | `#/not/anyOf/2 (the document FORBIDS the key)` | **MIGRATION_NOTE** | 1 | 1 | measured |
| 37 | `LegacyProductFormatDeclaration` | NO_SUBJECT | — | `core/format.json` | deprecated whole; no node states the union | **MIGRATION_NOTE** | 1 | 1 | joined |
| 38 | `ProviderRegistrationTmpxMacro` | NO_SUBJECT | — | `trusted-match/provider-registration.json` | no node carries the key | **MIGRATION_NOTE** | 1 | 1 | measured |
| 39 | `Row` | ARTIFACT | — | `a2ui/si-catalog.json` | `#/definitions/Row` | **EMIT_CHANGE** | 1 | 1 | joined |
| 40 | `SyncCatalogResult` | NO_SUBJECT | — | — | hand-written union; members not resolved | **UNDECIDED** | 1 | 1 | joined |
| 41 | `VerifyBrandClaimsSignedResponse` | SPELLING | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponse` | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response` | **ALIAS** | 1 | 1 | measured |
| 42 | `AuthorizedAgents1` | ARTIFACT | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/1` | **ALIAS** | 1 | 0 | joined |
| 43 | `AuthorizedAgents2` | ARTIFACT | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/2` | **ALIAS** | 1 | 0 | joined |
| 44 | `AuthorizedAgents3` | ARTIFACT | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/3` | **ALIAS** | 1 | 0 | joined |
| 45 | `BadgeRole` | ARTIFACT | `adcp.types.enums.AdCPProtocol` | `enums/adcp-protocol.json` | `# (reached from core/registry-event.json#/$defs/badgeRole, a pure $ref)` | **ALIAS** | 1 | 0 | joined |
| 46 | `CanonicalParameters` | ARTIFACT | — | `core/format.json` | `#/properties/canonical_parameters (deprecated)` | **UNDECIDED** | 1 | 0 | joined |
| 47 | `ComplyListScenariosResponse` | SPELLING | `adcp.types.compliance.ListScenariosSuccess` | `compliance/comply-test-controller-response.json` | `#/oneOf/0` | **ALIAS** | 1 | 0 | measured |
| 48 | `CoreAccount` | SPELLING | `adcp.types.core.Account` | `core/account.json` | `#` | **ALIAS** | 1 | 0 | joined |
| 49 | `CoreCreditLimit` | SPELLING | `adcp.types.core.AccountCreditLimit` | `core/account.json` | `#/properties/credit_limit` | **ALIAS** | 1 | 0 | measured |
| 50 | `CoreGovernanceAgent` | SPELLING | `adcp.types.core.AccountGovernanceAgentsItem` | `core/account.json` | `#/properties/governance_agents/items` | **ALIAS** | 1 | 0 | measured |
| 51 | `CoreMediaBuy` | SPELLING | `adcp.types.core.MediaBuy` | `core/media-buy.json` | `#` | **ALIAS** | 1 | 0 | measured |
| 52 | `CoreSetup` | SPELLING | `adcp.types.core.AccountSetup` | `core/account.json` | `#/properties/setup` | **ALIAS** | 1 | 0 | measured |
| 53 | `CpmVendorPricingOption` | ARTIFACT | `adcp.types.core.CpmPricing` | `core/signal-pricing.json` | `#/oneOf/0` | **ALIAS** | 1 | 0 | measured |
| 54 | `DaastAsset1` | ARTIFACT | `adcp.types.core.DAASTAssetUrl` | `core/assets/daast-asset.json` | `#/oneOf/0` | **ALIAS** | 1 | 0 | joined |
| 55 | `DaastAsset2` | ARTIFACT | `adcp.types.core.DAASTAssetInline` | `core/assets/daast-asset.json` | `#/oneOf/1` | **ALIAS** | 1 | 0 | joined |
| 56 | `FIELDS` | MACHINERY | — | — | — | **NONE** | 1 | 0 | joined |
| 57 | `File` | ARTIFACT | `adcp.types.brand.BrandDiscoveryFontFile` | `brand.json` | `#/definitions/font_file` | **ALIAS** | 1 | 0 | joined |
| 58 | `GeographicPlaceIdentifierSystem1` | ARTIFACT | `adcp.types.core.GeographicPlaceIdentifierSystem` | `core/geo-place-system.json` | `#/anyOf/0` | **MIGRATION_NOTE** | 1 | 0 | joined |
| 59 | `GetMediaBuysMediaBuy` | SPELLING | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItem` | `media-buy/get-media-buys-response.json` | `#/properties/media_buys/items` | **ALIAS** | 1 | 0 | measured |
| 60 | `GetProductsInputRequiredResponse` | SPELLING | `adcp.types.media_buy.GetProductsInputRequired` | `media-buy/get-products-async-response-input-required.json` | `#` | **ALIAS** | 1 | 0 | measured |
| 61 | `GetProductsResponseUnion` | NO_SUBJECT | — | `manifest.json` | `#/tools/get_products (a tool entry, not a node)` | **MIGRATION_NOTE** | 1 | 0 | measured |
| 62 | `GetProductsSubmittedResponse` | SPELLING | `adcp.types.media_buy.GetProductsSubmitted` | `media-buy/get-products-async-response-submitted.json` | `#` | **ALIAS** | 1 | 0 | joined |
| 63 | `GetProductsWorkingResponse` | SPELLING | `adcp.types.media_buy.GetProductsWorking` | `media-buy/get-products-async-response-working.json` | `#` | **ALIAS** | 1 | 0 | measured |
| 64 | `GetSignalsResponseUnion` | MACHINERY | union over GetSignalsResponse | GetSignalsSubmitted | GetSignalsWorking | `signals/get-signals-response.json (+2 async documents)` | `# of each; no node states the union` | **ALIAS** | 1 | 0 | measured |
| 65 | `GetSignalsSignal` | SPELLING | `adcp.types.signals.GetSignalsResponseSignalsItem` | `signals/get-signals-response.json` | `#/properties/signals/items` | **ALIAS** | 1 | 0 | measured |
| 66 | `GetSignalsSubmittedResponse` | SPELLING | `adcp.types.signals.GetSignalsSubmitted` | `signals/get-signals-async-response-submitted.json` | `#` | **ALIAS** | 1 | 0 | joined |
| 67 | `GetSignalsWorkingResponse` | SPELLING | `adcp.types.signals.GetSignalsWorking` | `signals/get-signals-async-response-working.json` | `#` | **ALIAS** | 1 | 0 | joined |
| 68 | `ImageFormatAsset` | NO_SUBJECT | — | `core/format.json` | factory-built, no node located | **UNDECIDED** | 1 | 0 | joined |
| 69 | `ImageFormatGroupAsset` | NO_SUBJECT | — | `core/format.json` | factory-built, no node located | **UNDECIDED** | 1 | 0 | joined |
| 70 | `Invoice` | ARTIFACT | `adcp.types.account.GetAccountFinancialsSuccessInvoicesItem` | `account/get-account-financials-response.json` | `#/oneOf/0/properties/invoices/items` | **ALIAS** | 1 | 0 | joined |
| 71 | `LegacyProposalTotalBudgetGuidance` | SPELLING | `adcp.types.core.ProposalTotalBudgetGuidance` | `core/proposal.json` | `#/properties/total_budget_guidance` | **ALIAS** | 1 | 0 | measured |
| 72 | `ListCreativesCanonicalCreative` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | joined |
| 73 | `ListCreativesCreative` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | measured |
| 74 | `ListCreativesCreativeItem` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | measured |
| 75 | `ListCreativesLegacyCreative` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | joined |
| 76 | `ListCreativesSort` | SPELLING | `adcp.types.creative.ListCreativesRequestSort` | `creative/list-creatives-request.json` | `#/properties/sort` | **ALIAS** | 1 | 0 | measured |
| 77 | `OverlayUnit` | SPELLING | `adcp.types.core.OverlayBoundsUnit` | `core/overlay.json` | `#/properties/bounds/properties/unit` | **ALIAS** | 1 | 0 | measured |
| 78 | `Pass` | ARTIFACT | `adcp.types.content_standards.PassItemUrl` | `content-standards/create-content-standards-request.json` | `#/properties/calibration_exemplars/properties/pass/items/oneOf/0` | **ALIAS** | 1 | 0 | joined |
| 79 | `PublisherDomain` | ARTIFACT | — | `core/canonical-product.json or protocol/get-adcp-capabilities-response.json -- two instruments disagree` | publisher_domains items; see §5 | **UNDECIDED** | 1 | 0 | joined |
| 80 | `PublisherPreviewRoute` | SPELLING | `adcp.types.core.PublisherDesignatedPreviewProviderRoutesItem` | `core/preview-provider.json` | `#/properties/routes/items` | **ALIAS** | 1 | 0 | joined |
| 81 | `PurchaseContinuation1` | ARTIFACT | `adcp.types.media_buy.PurchaseContinuationLegacyCreate` | `media-buy/request-proposals-response.json` | `#/properties/purchase_continuation/oneOf/1` | **ALIAS** | 1 | 0 | joined |
| 82 | `PushNotificationAuthentication` | SPELLING | `adcp.types.core.PushNotificationConfigAuthentication` | `core/push-notification-config.json` | `#/properties/authentication` | **ALIAS** | 1 | 0 | joined |
| 83 | `REMOVED_IN_MAJOR` | MACHINERY | — | — | — | **NONE** | 1 | 0 | measured |
| 84 | `RealEstateUnit` | ARTIFACT | `adcp.types.core.RealEstateItemAreaUnit` | `core/real-estate-item.json` | `#/properties/area/properties/unit` | **ALIAS** | 1 | 0 | measured |
| 85 | `RefineProposalsResponse2` | ARTIFACT | `adcp.types.media_buy.RefineProposalsResponseSubmitted` | `media-buy/refine-proposals-response.json` | `#/anyOf/1` | **ALIAS** | 1 | 0 | joined |
| 86 | `RefineProposalsTotalBudgetGuidance` | ARTIFACT | `adcp.types.core.CanonicalProposalTotalBudgetGuidance` | `core/canonical-proposal.json` | `#/properties/total_budget_guidance` | **ALIAS** | 1 | 0 | measured |
| 87 | `ReportingDelivery` | ARTIFACT | `adcp.types.core.ReportingDeliveryCapabilities` | `core/reporting-delivery-capabilities.json` | `#` | **MIGRATION_NOTE** | 1 | 0 | measured |
| 88 | `RequestProposalsResponse4` | ARTIFACT | `adcp.types.media_buy.RequestProposalsResponseSubmitted` | `media-buy/request-proposals-response.json` | `#/anyOf/3` | **ALIAS** | 1 | 0 | joined |
| 89 | `ScopeFromBillingNotSupported` | SPELLING | `adcp.types.error_details.BillingNotSupportedDetailsScope` | `error-details/billing-not-supported.json` | `#/properties/scope` | **ALIAS** | 1 | 0 | joined |
| 90 | `ScopeFromRateLimited` | SPELLING | `adcp.types.error_details.RateLimitedDetailsScope` | `error-details/rate-limited.json` | `#/properties/scope` | **ALIAS** | 1 | 0 | joined |
| 91 | `SyncAccountsCreditLimit` | SPELLING | `adcp.types.core.AccountCreditLimit` | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items/properties/credit_limit` | **ALIAS** | 1 | 0 | joined |
| 92 | `SyncAccountsSetup` | SPELLING | `adcp.types.core.AccountSetup` | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items/properties/setup` | **ALIAS** | 1 | 0 | joined |
| 93 | `SyncCreativesCreative` | SPELLING | `adcp.types.creative.SyncCreativesSuccessCreativesItem` | `creative/sync-creatives-response.json` | `#/oneOf/0/properties/creatives/items` | **ALIAS** | 1 | 0 | joined |
| 94 | `SyncEventSourcesSetup` | SPELLING | `adcp.types.media_buy.SyncEventSourcesSuccessEventSourcesItemSetup` | `media-buy/sync-event-sources-response.json` | `#/oneOf/0/properties/event_sources/items/properties/setup` | **ALIAS** | 1 | 0 | joined |
| 95 | `SyncGovernanceAccount` | SPELLING | `adcp.types.account.SyncGovernanceRequestAccountsItem` | `account/sync-governance-request.json` | `#/properties/accounts/items` | **ALIAS** | 1 | 0 | measured |
| 96 | `SyncGovernanceGovernanceAgent` | SPELLING | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItem` | `account/sync-governance-request.json` | `#/properties/accounts/items/properties/governance_agents/items` | **ALIAS** | 1 | 0 | joined |
| 97 | `TasksListSort` | SPELLING | `adcp.types.core.TasksListRequestSort` | `core/tasks-list-request.json` | `#/properties/sort` | **ALIAS** | 1 | 0 | measured |
| 98 | `UpdateMediaBuyErrorResponse` | SPELLING | `adcp.types.media_buy.UpdateMediaBuyError` | `media-buy/update-media-buy-response.json` | `#/oneOf/1` | **ALIAS** | 1 | 0 | joined |
| 99 | `VastAsset2` | ARTIFACT | `adcp.types.core.VASTAssetInline` | `core/assets/vast-asset.json` | `#/oneOf/1` | **ALIAS** | 1 | 0 | measured |
| 100 | `VehicleUnit` | SPELLING | `adcp.types.core.VehicleItemMileageUnit` | `core/vehicle-item.json` | `#/properties/mileage/properties/unit` | **ALIAS** | 1 | 0 | measured |
| 101 | `ViewThreshold` | ARTIFACT | `adcp.types.constraints.FloatMin0Max1` | `pricing-options/cpv-option.json` | `#/properties/parameters/properties/view_threshold/oneOf/0` | **ALIAS** | 1 | 0 | joined |
| 102 | `WholesaleFeedSignal` | SPELLING | `adcp.types.core.WholesaleFeedEventSignal` | `core/wholesale-feed-event.json` | `#/$defs/signal` | **ALIAS** | 1 | 0 | joined |
| 103 | `Pattern` | ARTIFACT | `adcp.types.protocol.GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern` | `protocol/get-adcp-capabilities-response.json` | `#/properties/adcp/properties/principal/properties/reporting_destination_offerings/items/properties/pattern` | **ALIAS** | 0 | 3 | joined |
| 104 | `SyncAudiencesAudience` | SPELLING | `adcp.types.media_buy.SyncAudiencesRequestAudiencesItem` | `media-buy/sync-audiences-request.json` | `#/properties/audiences/items` | **ALIAS** | 0 | 2 | joined |
| 105 | `SyncCreativeResult` | NO_SUBJECT | — | — | hand-written union; members not resolved | **UNDECIDED** | 0 | 2 | joined |
| 106 | `AcceptedLoss` | ARTIFACT | `adcp.types.media_buy.RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem` | `media-buy/request-proposals-response.json` | `#/properties/purchase_continuation/oneOf/1/properties/losses/items` | **ALIAS** | 0 | 1 | joined |
| 107 | `Encoding` | ARTIFACT | `adcp.types.core.MacroEncoding` | `core/macro-encoding.json` | `#` | **MIGRATION_NOTE** | 0 (raw 6) | 1 | measured |
| 108 | `MediaBuyPackage` | SPELLING | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItemPackagesItem` | `media-buy/get-media-buys-response.json` | `#/properties/media_buys/items/properties/packages/items` | **ALIAS** | 0 | 1 | measured |
| 109 | `PrincipalReadResult` | NO_SUBJECT | union over our 4 principal-result classes | `protocol/sync-principal-response.json` | `# of each arm; no node states the union` | **ALIAS** | 0 | 1 | joined |
| 110 | `PrincipalSyncResult` | NO_SUBJECT | union over our 3 principal-result classes | `protocol/sync-principal-response.json` | `# of each arm; no node states the union` | **ALIAS** | 0 | 1 | joined |
| 111 | `Refine` | ARTIFACT | — | `media-buy/get-products-request.json` | `#/properties/refine/items` | **EMIT_CHANGE** | 0 | 1 | measured |
| 112 | `VerifyBrandClaimsPayload` | SPELLING | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload` | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response/allOf/1/properties/payload` | **ALIAS** | 0 | 1 | measured |
| 113 | `Path` | ARTIFACT | `adcp.types.core.RemoveTargetingSetValuesPath` | `core/targeting-modification.json` | `#/oneOf/1/properties/path` | **MIGRATION_NOTE** | 0 (raw 3) | 0 | measured |

## 2. The counts, and the arithmetic that sums to 113

**The population.** `survey/name_census.py` and `survey/blocking_names.py`, both static by
AST over the SOURCE of the two trees, so no import is attempted and neither a recursion nor
an absent module can hide a declaration:

| | names |
| --- | --- |
| upstream declares, we do not | 1,105 |
| …imported by upstream's TESTS | 104 |
| …imported by their kept MACHINERY | 31 |
| …imported by BOTH (counted once) | −22 |
| **distinct blocking names, this table** | **113** |
| …referenced by NEITHER (not in this table) | 992 |

`104 + 31 − 22 = 113`, and `113 + 992 = 1,105`. The 104 take 73 of upstream's test files.
All 1,105 were re-checked at RUNTIME by `getattr` against our PEP 562 facade: zero of them
resolve, so the AST reading is not an overcount.

**By category** (what the name IS, which is prior to what is owed):

| category | rows | what it means |
| --- | --- | --- |
| SPELLING | 52 | both trees hold the node; the two words differ (their collision prefix, our document-derived word) |
| ARTIFACT | 36 | their word is minted from a property key, a `$defs` key or their generator's traversal ordinal, and the document states no such word |
| NO_SUBJECT | 17 | a hand-written union, `Literal`, factory or 3.1-era leftover; no node of the pinned bundle states it |
| MACHINERY | 8 | not a type: a module constant, an inventory tuple, or a base class whose body is behaviour |
| **total** | **113** | |

**By action** (what is owed):

| action | rows | |
| --- | --- | --- |
| ALIAS | 86 | one subject, two spellings — a NAME and never a second type, so `isinstance` holds across both |
| MIGRATION_NOTE | 12 | no subject, or a subject with no published spelling to serve |
| UNDECIDED | 8 | §5 |
| NONE | 5 | machinery we deliberately do not ship; the name has nothing to point at |
| EMIT_CHANGE | 2 | §4 — the document states a node and our tree declares no type at it |
| SAME_BUT_NOT | 0 | §4 |
| **total** | **113** | |

`52 + 36 + 17 + 8 = 113` and `86 + 12 + 8 + 5 + 2 + 0 = 113`. By strength:
`44 measured + 69 joined = 113`; of the 86 aliases, 33 are measured and 53 joined.

## 3. The generator change: this table must be `survey/adapter_surface.py`'s OUTPUT

The owner's instruction is that the alias layer be MEASURED AND ENUMERATED rather than
vibed into existence. `survey/adapter_surface.py` is the instrument that exists for it, and
it writes `survey/adapter-surface-9.6.1.tsv` (486 rows) and `src/adcp/types/_adapter.py`.

**What that table says about these 113 today, measured against it.** 58 of them have NO
row at all; 50 have a row that is only a REFUSAL; 5 are BOUND. Of the 50 refusals,
`DOCUMENT-NO-WORD-NO-IDENTITY` accounts for 33 — names whose document and pointer §1 now
carries — and `NO-DOCUMENT-NO-SUBJECT` for 14, including `Refine`, whose document states
the node (§4a), with 3 `UPSTREAM-PRIVATE-MODULE-NOT-A-TYPE`, one `NOT-A-TYPE` and one
`UPSTREAM-AMBIGUOUS` behind them.

**And the five BOUND rows still do not resolve on our surface**, which is a second defect
and not a reprieve: `ScopeFromBillingNotSupported` and `ScopeFromRateLimited`
(`document+word` → `adcp.types.error_details.{BillingNotSupportedDetailsScope,
RateLimitedDetailsScope}`), `SupportedVersion` (`document+pointer-constraint`, with the
note "the document states that constraint at `/properties/supported_versions/items` and
nowhere else in it"), `RefineProposalsResponse1` (`document+ordinal`, note "arm 1 of 2,
consts agree" → `RefineProposalsResponseCompleted`, which is the reading §1 carries) and
`PublisherDomain` — whose binding is to a DIFFERENT subject from the one the blocking
import names, which is why §1 leaves it `UNDECIDED` and §5 states the disagreement. A
bound row that never reached the surface means `write_modules()` and the table disagree,
and nothing grades the difference.

Four specific defects, each in a named function.

### 3a. `census()` measures the wrong demand: it counts IMPORTS, at MODULE SCOPE, from `adcp.types*`

`census(src, suite)` walks `corpus()` — which, correctly, is upstream's own code by
PROVENANCE including their whole suite — and records a pair only from
`module_scope_imports(tree)`, i.e. an `ast.ImportFrom` outside any function or class body,
and only when `mod == "adcp.types" or mod.startswith("adcp.types.")`. Three classes of
demand cannot enter it:

1. **An ATTRIBUTE is not an import.** `survey/blocking_names.py::refs()` counts
   `ast.Attribute` as well, and that is how the most expensive name in this table was
   found: `CanonicalBoundaryModel` is reached by `import … as boundary` and then
   SUBCLASSED (`class Custom(boundary.CanonicalBoundaryModel)`) in 8 of upstream's files,
   and `ReportingDelivery` only ever through `importlib.import_module(…)` plus `getattr`.
   `census()` sees none of them.
2. **A function-scope import is dropped by design.** `module_scope_imports()`' own rule is
   that only a module-scope import takes the whole file at collection — true for the
   collection-error count and false for the question this table asks, which is "which names
   does upstream's own code ask of our surface". The scope belongs in a COLUMN, not in the
   filter.
3. **The module filter loses `from adcp import X`.** `MediaBuyPackage` is in
   `adcp.__all__` and is imported from the top-level package, not from `adcp.types`; the
   filter requires `adcp.types*`, so its row never existed.

**The demand census must be the union of three readings, keyed by NAME:** upstream's own
importers (tests + kept machinery, imports AND attributes, any scope) and upstream's
DELIBERATE PUBLISHED SURFACE — the hand-written `__all__` of `src/adcp/types/__init__.py`
and `src/adcp/__init__.py` read by AST from the pinned rev, 1,197 names. The last is the
set reading 10 ranges over, and it is the set the gate in
`tests_emit/test_every_upstream_name_resolves_or_is_noted.py` derives.

### 3b. The join is keyed off their DECLARING MODULE, and 40 of these names are declared in a module that names no document

`Join.resolve` → `_by_dump` keys every one of its thirteen keys on
`their_document(module)`, the arithmetic that turns `adcp.types.domains.core.product` into
`core/product.json`. The script's own rule follows: **"a module no document states is
refused whole."** That is right for `adcp.types.registry` and wrong for the layer this
table is mostly made of — `adcp.types.aliases`, `canonical_creative`, `legacy`,
`_generated`, `_eager`, `_generated_poc_alias`. Every `X as Y` collision alias upstream
wrote lives there, and the whole family (`CoreCreditLimit`, `GetMediaBuysMediaBuy`,
`SyncGovernanceAccount`, `ListCreativesSort`, `OverlayUnit`, `VehicleUnit`,
`CpmVendorPricingOption`, the six `AuthorizedAgentsBy…`, …) is refused at the module, with
reasons the bundle then contradicts: `_adapter.py`'s `DOCUMENT-NO-WORD-NO-IDENTITY` for
`AuthorizedAgentsByInlineProperties` was reached through their numbered
`AuthorizedAgents3`, and `adagents.json#/oneOf/1/properties/authorized_agents/items/oneOf/2`
states `authorization_type: {const: inline_properties}` — both words of the spelling are
the document's own.

**The key must be the DENOTED DECLARATION, not the spelling's home module.** Add an
alias-chain resolver over upstream's SOURCE, by AST at the pinned rev: follow
`from M import X as Y`, `Y = X` and `Y: TypeAlias = X` through their hand-written layer
until it reaches a `ClassDef` in `adcp.types.domains.*`, then ask `their_document()` of
THAT module and run the existing thirteen keys unchanged. `Join.denoted()` already decides
"which declaration of theirs a pair denotes" — but only as a tie-break inside the dump's
candidate set, and only for pairs the dump already proposed. What is missing is the hop
that produces the candidate at all. Measured: that resolver places 69 of the 69 unmeasured
rows of this table on a document, and 100 of the 113 on a (document, pointer) pair.

### 3c. `pointer_pool()` follows one `$ref` hop, and these subjects are two hops away

`Join.pointer_pool(doc)` is "every declaration of ours the document states, inline at a
pointer of its own or through a `$ref` THAT DOCUMENT states" — one hop. It reaches
`core/assets/asset-union.json` → `core/assets/vast-asset.json` (which is why
`InlineVastAsset`/`VastAsset2` join at all) and cannot reach
`protocol/get-adcp-capabilities-response.json` → `…/properties/encoding` →
`core/macro-encoding.json`, or the same document's `reporting_delivery` →
`core/reporting-delivery-capabilities.json`. Both of those are pure `$ref` nodes, so the
bundle REFERENCES one subject and upstream's generator minted a class per call site; our
tree states the referenced document once. **The pool must be the `$ref` CLOSURE from the
document, with the hop count recorded on the row**, so a two-hop bind is a reviewable fact
rather than an absence. The same closure settles `BadgeRole`
(`core/registry-event.json#/$defs/badgeRole` is a bare `$ref` to `enums/adcp-protocol.json`)
and the projection case, where `PROJECTIONS` already drops `bundled/` and `mcp/` from the
path but nothing follows the reference underneath it.

### 3d. What the script must then EMIT

`write_modules()` already writes the alias statements and the refusal table. The table in
§1 is six columns it does not yet carry: `category`, `document`, `pointer`, `action`,
`blocks_tests`, `blocks_machinery`. Add them to the `--table` TSV, have it write
`verdicts/name-mapping.md` from the same rows, and the pair of halves
`node_keyed_aliases.py` already insists on — the alias statement and its migration entry —
becomes one output of one run. A name whose row is `UNDECIDED` must appear in the TSV as
`UNDECIDED` with its blocker, never be dropped: a row dropped for lack of a key is exactly
how 113 names came to be absent from a 488-row table with no record that they were missing.

## 4. Every `EMIT_CHANGE`, and every `SAME_BUT_NOT`

These are the defects in OUR emission and they are the most valuable output of the
exercise. There are **two `EMIT_CHANGE` rows and no `SAME_BUT_NOT` row at all**.

### 4a. `Refine` — `media-buy/get-products-request.json`, `#/properties/refine/items`

The keyword is the node's own `discriminator: {propertyName: 'scope'}`, over a 3-arm
`oneOf` whose arms require `['scope','ask']`, `['scope','product_id']` and
`['scope','proposal_id']`. **The subject exists and our tree declares no type at that
pointer.** We declare the three ARMS — `#/properties/refine/items/oneOf/0`, `…/1`, `…/2` —
under structure-minted words (`ObjScopeAsk`, `ObjScopeProductIdActionAsk`,
`ObjScopeProposalIdActionAsk`) and write the union inline in the field annotation; the
module's `__all__` is `['GetProductsRequest']`. `src/adcp/types/_adapter.py` refuses the
name as `NO-DOCUMENT-NO-SUBJECT`, which the document contradicts. The accepted sets AGREE
over five probes (tagged and untagged payloads on each arm), so this is not a validation
defect: it is a declaration-and-export gap at a stated pointer, and no alias can be written
until a type exists there — aliasing onto one of the three `ObjScope*` words would breach
reading 10's bar on aliasing a structure-minted placeholder.

### 4b. `Row` — `a2ui/si-catalog.json`, `#/definitions/Row`

The keyword is the definition key `Row` and its own description, `"Horizontal layout
container"`; the node is `type: object` with `children` (array of string), `gap`, `align`
(enum of 4) and `justify` (enum of 5). **Our tree declares nothing at it.** The document's
`definitions` hold ELEVEN such nodes — `Text`, `Button`, `Link`, `Image`, `Card`,
`ProductCard`, `List`, `Row`, `Column`, `IntegrationAction`, `AppHandoff` — and we emit a
class for none of them; `adcp.types._schemas.a2ui.si_catalog` holds only the root
`SIComponentCatalog` and the `components` enum, whose members are the eleven NAMES as
strings. Upstream emits all eleven as classes, and `Row` is the one their suite imports.

Sized over the whole non-projection bundle, so the rule is not read off one document: 169
nodes are stated under `definitions`/`$defs`, 111 of them record-shaped (carrying
`properties` or a combinator); 33 of those 111 have no class of ours, and **exactly 11 of
the 33 — the si-catalog eleven — are referenced by nothing anywhere in the bundle.** The
other 22 are each referenced, and our class for them sits at the REFERRING pointer
(`brand/verify-brand-claims-request.json#/definitions/claim_entry` is our `ClaimsItem` at
the `claims` items node), which is a stamping question and not an absence. So the defect is
precise and its boundary is measured: **an unreferenced `definitions` node is a stated node
and our walk does not reach it.** Fixing it is 11 classes in one document.

### 4c. No `SAME_BUT_NOT`, and what that means

**Not one row found our class admitting a payload its document refuses, or refusing one its
document admits.** Every accepted-set comparison in the 44 measured rows came back either
IDENTICAL or differing on one of exactly three accounted causes:

* **their required-`const` default.** Upstream's generator turns a required property that
  pins a `const` into a defaulted `Literal`, so their arm accepts a payload omitting
  `status`, `asset_type`, `kind` or `delivery_type` and ours requires it, as the document
  does. Already measured tree-wide at `docs/plan/sdk-type-generation.md:206` — 1,083
  properties over 613 sites. Ours is the document's reading; `codegen/structure.py:72`'s
  `STRUCTURAL_IDENTITY` already excludes a pinned field from identity for this reason.
* **the two-half design.** `src/adcp/types/_base.py:40-49`: the document's accepted set is
  reached through `strict_validate`, not through the pydantic half, so
  `{'min': '1'}` coercing where upstream's `StrictFloat` refuses is our stated architecture
  and not a widening of the document.
* **ours strictly NARROWER and faithful.** `CoreGovernanceAgent` keeps the document's
  `^https://` pattern their field dropped; `RefineProposalsTotalBudgetGuidance` enforces the
  `anyOf` over `recommended`/`min`/`max` that their class does not.

So the 113 are a NAMING debt plus the two emission gaps above — and the absence of a
`SAME_BUT_NOT` row is itself the finding, because the alternative hypothesis going in was
that a missing name might be hiding a disagreement about what the wire admits. On the 44
rows read payload by payload, it is not.

## 5. What is still undecided

Four things, with what settles each. Nothing else in this file is pending.

1. **69 of 113 rows carry `joined` strength, not `measured`.** Their document, pointer and
   target are located; their ACCEPTED SETS have not been probed row by row. What settles
   each: the per-row probe the 44 used — construct the document's own admitted and refused
   payloads against both classes, in the two interpreters, and record the result in the
   row. The cheapest order is the table's own order, because a wrong target on
   `CreateMediaBuySuccessResponse` costs 17 files and a wrong one on `AcceptedLoss` costs
   none.
2. **Seven of the eight `UNDECIDED` rows are upstream hand-written unions or factory
   calls**: `VendorPricingOptionUnion`, `SyncCatalogResult`, `SyncCreativeResult`,
   `RepeatableAssetGroup`, `ImageFormatAsset`, `ImageFormatGroupAsset`,
   `CanonicalParameters`. Each is an expression over their NUMBERED variants or a call to a
   private factory (`_format_asset_class('image')`), so the subject is whatever their
   generator put at that ordinal on the day it ran. What settles them: resolve every member
   of the expression through the alias chain of §3b and apply the rule the decided unions
   already follow — a union alias is owed when EVERY member resolves in ours
   (`AssetInstance` 11/11, `PrincipalReadResult` 4/4, `PrincipalSyncResult` 3/3 → alias;
   `GetProductsResponseUnion` 1/4 → note), and the arms of a `Literal` the bundle does not
   state get a note (`AssetInstanceType`).
3. **The eighth, `PublisherDomain`, is a word two rows disagree about, which is the one
   case that gets no alias.** Upstream declares it three times — `core/canonical_product.py`,
   `core/product.py` and their bundled capabilities clone — and `publisher_domains` is not
   a key of `core/canonical-product.json` at all, so the name reaches that document only
   through an inlined `$ref`. The two instruments answer differently:
   `survey/probes/probe_map.json` lowers it to `adcp.types.constraints.StrDomainName` by
   the constraint-set key, and `survey/adapter-surface-9.6.1.tsv` BINDS it to
   `adcp.types.core.DomainName` with the note "the document states it at
   `/properties/media_buy/properties/portfolio/properties/publisher_domains/items`" — of
   `protocol/get-adcp-capabilities-response.json`, a different document from the one the
   blocking import names. `survey/node_keyed_aliases.py`'s own rule applies: "a name that
   resolves to a DIFFERENT class of ours depending on which upstream module the import came
   from gets no alias, it gets a migration note." What settles it: the `$ref` closure of §3c
   run from each of the three declaring modules; if they do not converge on one subject the
   row is a note naming both. The shared-symbol caveat stands on the four decided
   constraint rows as well (`SupportedVersion`, `SupportedMajor`, `MajorVersion`,
   `ViewThreshold`): the alias re-attaches a property-key name to a content-addressed symbol
   every same-constrained position in the bundle shares, so the row is only as specific as
   the POSITION it names.
4. **Whether a RESTATED node is owed its own class.**
   `account/sync-accounts-response.json` restates `credit_limit` and `setup` INLINE (they
   are not `$ref`s to `core/account.json`), and our `AccountsItem` types them with
   `core/account.json`'s classes — so `CoreCreditLimit` and `SyncAccountsCreditLimit` alias
   onto ONE object of ours where upstream has two, and their own assertion
   (`tests/test_collision_aliases.py:258`, `CoreCreditLimit is not SyncAccountsCreditLimit`)
   cannot hold whatever those two aliases point at. What settles it: a ruling on
   cross-document identification of structurally identical restated nodes — `codegen`'s
   duplicate policy against the two documents' accepted sets. Until it lands, both rows are
   `ALIAS` onto the one class and the collapse is stated here rather than discovered by a
   consumer.

**And the gate's population is wider than this table, deliberately.**
`tests_emit/test_every_upstream_name_resolves_or_is_noted.py` ranges over upstream's
deliberate published surface, derived: 1,197 names, of which **211 do not resolve here and
146 of those appear nowhere in `docs/migration-from-upstream.md`** — 63 of the 146 are
blocking names of this table and 83 are names nothing of upstream's own code imports. The
gate is RED at 146 today and that number is the work list; it is not a figure this table
can close on its own, because a name no instrument has a demand for still owes a consumer a
row.
