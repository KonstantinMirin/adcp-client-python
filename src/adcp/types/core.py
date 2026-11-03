"""The public types of the ``core`` domain.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  This is the one import path for each of them, and the object is the same one
the runtime validates into -- ``isinstance`` against a union branch imported from
here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.
"""

from __future__ import annotations

from ._schemas.core.acceptance_policy_profile_ids import (
    AcceptancePolicyProfileIDs as AcceptancePolicyProfileIDs,
)
from ._schemas.core.account import (
    Account as Account,
)
from ._schemas.core.account_authorization import (
    AccountAuthorization as AccountAuthorization,
    StandardScope as StandardScope,
)
from ._schemas.core.account_change import (
    AccountChange as AccountChange,
)
from ._schemas.core.account_change_recorded_webhook import (
    AccountChangeRecordedWebhook as AccountChangeRecordedWebhook,
)
from ._schemas.core.account_identity_change import (
    AccountIdentityChange as AccountIdentityChange,
    AccountIdentityChangePending as AccountIdentityChangePending,
    AccountIdentityChangeRejected as AccountIdentityChangeRejected,
)
from ._schemas.core.account_identity_change_preview import (
    AccountIdentityChangeBlocked as AccountIdentityChangeBlocked,
    AccountIdentityChangePreview as AccountIdentityChangePreview,
    AccountIdentityChangeWouldApply as AccountIdentityChangeWouldApply,
    AccountIdentityChangeWouldRequireApproval as AccountIdentityChangeWouldRequireApproval,
    BlockedImpacts as BlockedImpacts,
    NonblockingImpacts as NonblockingImpacts,
)
from ._schemas.core.account_ref import (
    AccountReference as AccountReference,
    AccountReferenceAccountId as AccountReferenceAccountId,
    AccountReferenceBrandOperator as AccountReferenceBrandOperator,
)
from ._schemas.core.account_status_changed_webhook import (
    AccountStatusChangedWebhook as AccountStatusChangedWebhook,
)
from ._schemas.core.account_timezone_capability import (
    AccountTimezoneCapability as AccountTimezoneCapability,
)
from ._schemas.core.account_with_authorization import (
    AccountWithAuthorization as AccountWithAuthorization,
)
from ._schemas.core.activation_key import (
    ActivationKey as ActivationKey,
    ActivationKeyKeyValue as ActivationKeyKeyValue,
    ActivationKeySegmentId as ActivationKeySegmentId,
)
from ._schemas.core.ad_inventory_config import (
    AdInventoryConfiguration as AdInventoryConfiguration,
)
from ._schemas.core.agent_encryption_key import (
    AgentEncryptionKey as AgentEncryptionKey,
)
from ._schemas.core.agent_notification_config import (
    AgentNotificationConfig as AgentNotificationConfig,
)
from ._schemas.core.agent_notification_config_state import (
    AgentNotificationConfigState as AgentNotificationConfigState,
)
from ._schemas.core.agent_reporting_destination import (
    AgentReportingDestination as AgentReportingDestination,
    DatasetShareRecipient as DatasetShareRecipient,
    FileTransferDestination as FileTransferDestination,
    WarehouseMaterializationDestination as WarehouseMaterializationDestination,
)
from ._schemas.core.agent_reporting_destination_state import (
    AgentReportingDestinationState as AgentReportingDestinationState,
)
from ._schemas.core.agent_signing_key import (
    AgentSigningKey as AgentSigningKey,
)
from ._schemas.core.agent_webhook_challenge import (
    AgentWebhookChallenge as AgentWebhookChallenge,
)
from ._schemas.core.app_item import (
    AppItem as AppItem,
)
from ._schemas.core.applicable_package_id import (
    ApplicablePackageID as ApplicablePackageID,
)
from ._schemas.core.asset_group_vocabulary import (
    AdCPAssetGroupVocabularyRegistry as AdCPAssetGroupVocabularyRegistry,
)
from ._schemas.core.assets.asset_union import (
    AssetVariant as AssetVariant,
    AssetVariantAudio as AssetVariantAudio,
    AssetVariantBrief as AssetVariantBrief,
    AssetVariantCard as AssetVariantCard,
    AssetVariantCatalog as AssetVariantCatalog,
    AssetVariantCss as AssetVariantCss,
    AssetVariantDaast as AssetVariantDaast,
    AssetVariantDaastTracker as AssetVariantDaastTracker,
    AssetVariantDisplayTag as AssetVariantDisplayTag,
    AssetVariantHtml as AssetVariantHtml,
    AssetVariantImage as AssetVariantImage,
    AssetVariantJavascript as AssetVariantJavascript,
    AssetVariantMarkdown as AssetVariantMarkdown,
    AssetVariantPixelTracker as AssetVariantPixelTracker,
    AssetVariantPublishedPost as AssetVariantPublishedPost,
    AssetVariantText as AssetVariantText,
    AssetVariantUrl as AssetVariantUrl,
    AssetVariantVast as AssetVariantVast,
    AssetVariantVastTracker as AssetVariantVastTracker,
    AssetVariantVideo as AssetVariantVideo,
    AssetVariantWebhook as AssetVariantWebhook,
    AssetVariantZip as AssetVariantZip,
)
from ._schemas.core.assets.audio_asset import (
    AudioAsset as AudioAsset,
)
from ._schemas.core.assets.brief_asset import (
    BriefAsset as BriefAsset,
)
from ._schemas.core.assets.card_asset import (
    CardAsset as CardAsset,
)
from ._schemas.core.assets.catalog_asset import (
    CatalogAsset as CatalogAsset,
)
from ._schemas.core.assets.css_asset import (
    CSSAsset as CSSAsset,
)
from ._schemas.core.assets.daast_asset import (
    DAASTAsset as DAASTAsset,
    DAASTAssetInline as DAASTAssetInline,
    DAASTAssetUrl as DAASTAssetUrl,
)
from ._schemas.core.assets.daast_tracker_asset import (
    DAASTTrackerAsset as DAASTTrackerAsset,
)
from ._schemas.core.assets.display_tag_asset import (
    DisplayTagAsset as DisplayTagAsset,
    InlineMarkup as InlineMarkup,
    PairedRedirect as PairedRedirect,
    TagURL as TagURL,
)
from ._schemas.core.assets.html_asset import (
    HTMLAsset as HTMLAsset,
)
from ._schemas.core.assets.image_asset import (
    ImageAsset as ImageAsset,
)
from ._schemas.core.assets.javascript_asset import (
    JavaScriptAsset as JavaScriptAsset,
)
from ._schemas.core.assets.markdown_asset import (
    MarkdownAsset as MarkdownAsset,
)
from ._schemas.core.assets.pixel_tracker_asset import (
    PixelTrackerAsset as PixelTrackerAsset,
)
from ._schemas.core.assets.published_post_asset import (
    PublishedPostAsset as PublishedPostAsset,
)
from ._schemas.core.assets.text_asset import (
    TextAsset as TextAsset,
)
from ._schemas.core.assets.url_asset import (
    URLAsset as URLAsset,
)
from ._schemas.core.assets.vast_asset import (
    VASTAsset as VASTAsset,
    VASTAssetInline as VASTAssetInline,
    VASTAssetUrl as VASTAssetUrl,
)
from ._schemas.core.assets.vast_tracker_asset import (
    VASTTrackerAsset as VASTTrackerAsset,
)
from ._schemas.core.assets.video_asset import (
    VideoAsset as VideoAsset,
)
from ._schemas.core.assets.webhook_asset import (
    WebhookAsset as WebhookAsset,
)
from ._schemas.core.assets.zip_asset import (
    ZipAsset as ZipAsset,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseData as AdCPAsyncResponseData,
    AdCPAsyncResponseDataBuildCreativeResponse as AdCPAsyncResponseDataBuildCreativeResponse,
    AdCPAsyncResponseDataCompactTaskInputRequired as AdCPAsyncResponseDataCompactTaskInputRequired,
    AdCPAsyncResponseDataCompactTaskSubmitted as AdCPAsyncResponseDataCompactTaskSubmitted,
    AdCPAsyncResponseDataCompactTaskWorking as AdCPAsyncResponseDataCompactTaskWorking,
    AdCPAsyncResponseDataControlMediaBuyResponse as AdCPAsyncResponseDataControlMediaBuyResponse,
    AdCPAsyncResponseDataCreateMediaBuyResponse as AdCPAsyncResponseDataCreateMediaBuyResponse,
    AdCPAsyncResponseDataDeclineProposalsResponse as AdCPAsyncResponseDataDeclineProposalsResponse,
    AdCPAsyncResponseDataGetCreativeFeaturesResponse as AdCPAsyncResponseDataGetCreativeFeaturesResponse,
    AdCPAsyncResponseDataGetProductsResponse as AdCPAsyncResponseDataGetProductsResponse,
    AdCPAsyncResponseDataGetSignalsResponse as AdCPAsyncResponseDataGetSignalsResponse,
    AdCPAsyncResponseDataMediaBuyCommitmentResponse as AdCPAsyncResponseDataMediaBuyCommitmentResponse,
    AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult as AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult,
    AdCPAsyncResponseDataPreviewCreativeResponse as AdCPAsyncResponseDataPreviewCreativeResponse,
    AdCPAsyncResponseDataRefineProposalsResponse as AdCPAsyncResponseDataRefineProposalsResponse,
    AdCPAsyncResponseDataRejected as AdCPAsyncResponseDataRejected,
    AdCPAsyncResponseDataRequestProposalsResponse as AdCPAsyncResponseDataRequestProposalsResponse,
    AdCPAsyncResponseDataSyncCatalogsResponse as AdCPAsyncResponseDataSyncCatalogsResponse,
    AdCPAsyncResponseDataSyncCreativesResponse as AdCPAsyncResponseDataSyncCreativesResponse,
    AdCPAsyncResponseDataUpdateMediaBuyResponse as AdCPAsyncResponseDataUpdateMediaBuyResponse,
    BuildCreativeAsyncInputRequired as BuildCreativeAsyncInputRequired,
    BuildCreativeAsyncSubmitted as BuildCreativeAsyncSubmitted,
    BuildCreativeAsyncWorking as BuildCreativeAsyncWorking,
    CreateMediaBuyAsyncInputRequired as CreateMediaBuyAsyncInputRequired,
    CreateMediaBuyAsyncSubmitted as CreateMediaBuyAsyncSubmitted,
    CreateMediaBuyAsyncWorking as CreateMediaBuyAsyncWorking,
    GetCreativeFeaturesAsyncSubmitted as GetCreativeFeaturesAsyncSubmitted,
    GetProductsAsyncInputRequired as GetProductsAsyncInputRequired,
    GetProductsAsyncSubmitted as GetProductsAsyncSubmitted,
    GetProductsAsyncWorking as GetProductsAsyncWorking,
    GetSignalsAsyncSubmitted as GetSignalsAsyncSubmitted,
    GetSignalsAsyncWorking as GetSignalsAsyncWorking,
    RefineProposalsAsyncSubmitted as RefineProposalsAsyncSubmitted,
    RequestProposalsAsyncSubmitted as RequestProposalsAsyncSubmitted,
    SyncCatalogsAsyncInputRequired as SyncCatalogsAsyncInputRequired,
    SyncCatalogsAsyncSubmitted as SyncCatalogsAsyncSubmitted,
    SyncCatalogsAsyncWorking as SyncCatalogsAsyncWorking,
    SyncCreativesAsyncInputRequired as SyncCreativesAsyncInputRequired,
    SyncCreativesAsyncSubmitted as SyncCreativesAsyncSubmitted,
    SyncCreativesAsyncWorking as SyncCreativesAsyncWorking,
    UpdateMediaBuyAsyncInputRequired as UpdateMediaBuyAsyncInputRequired,
    UpdateMediaBuyAsyncSubmitted as UpdateMediaBuyAsyncSubmitted,
    UpdateMediaBuyAsyncWorking as UpdateMediaBuyAsyncWorking,
)
from ._schemas.core.async_response_refs.creative.get_creative_features_async_response_submitted import (
    GetCreativeFeaturesSubmitted as GetCreativeFeaturesSubmitted,
)
from ._schemas.core.async_response_refs.creative.sync_creatives_async_response_input_required import (
    SyncCreativesInputRequired as SyncCreativesInputRequired,
)
from ._schemas.core.async_response_refs.creative.sync_creatives_async_response_submitted import (
    SyncCreativesSubmitted as SyncCreativesSubmitted,
)
from ._schemas.core.async_response_refs.creative.sync_creatives_async_response_working import (
    SyncCreativesWorking as SyncCreativesWorking,
)
from ._schemas.core.async_response_refs.media_buy.accept_proposal_async_response_input_required import (
    AcceptProposalInputRequired as AcceptProposalInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.accept_proposal_async_response_submitted import (
    AcceptProposalSubmitted as AcceptProposalSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.accept_proposal_async_response_working import (
    AcceptProposalWorking as AcceptProposalWorking,
)
from ._schemas.core.async_response_refs.media_buy.build_creative_async_response_input_required import (
    BuildCreativeInputRequired as BuildCreativeInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.build_creative_async_response_submitted import (
    BuildCreativeSubmitted as BuildCreativeSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.build_creative_async_response_working import (
    BuildCreativeWorking as BuildCreativeWorking,
)
from ._schemas.core.async_response_refs.media_buy.buy_products_async_response_input_required import (
    BuyProductsInputRequired as BuyProductsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.buy_products_async_response_submitted import (
    BuyProductsSubmitted as BuyProductsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.buy_products_async_response_working import (
    BuyProductsWorking as BuyProductsWorking,
)
from ._schemas.core.async_response_refs.media_buy.control_media_buy_async_response_input_required import (
    ControlMediaBuyInputRequired as ControlMediaBuyInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.control_media_buy_async_response_submitted import (
    ControlMediaBuySubmitted as ControlMediaBuySubmitted,
)
from ._schemas.core.async_response_refs.media_buy.control_media_buy_async_response_working import (
    ControlMediaBuyWorking as ControlMediaBuyWorking,
)
from ._schemas.core.async_response_refs.media_buy.create_media_buy_async_response_input_required import (
    CreateMediaBuyInputRequired as CreateMediaBuyInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.create_media_buy_async_response_submitted import (
    CreateMediaBuySubmitted as CreateMediaBuySubmitted,
)
from ._schemas.core.async_response_refs.media_buy.create_media_buy_async_response_working import (
    CreateMediaBuyWorking as CreateMediaBuyWorking,
)
from ._schemas.core.async_response_refs.media_buy.decline_proposals_async_response_input_required import (
    DeclineProposalsInputRequired as DeclineProposalsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.decline_proposals_async_response_submitted import (
    DeclineProposalsSubmitted as DeclineProposalsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.decline_proposals_async_response_working import (
    DeclineProposalsWorking as DeclineProposalsWorking,
)
from ._schemas.core.async_response_refs.media_buy.get_products_async_response_input_required import (
    GetProductsInputRequired as GetProductsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.get_products_async_response_submitted import (
    GetProductsSubmitted as GetProductsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.get_products_async_response_working import (
    GetProductsWorking as GetProductsWorking,
)
from ._schemas.core.async_response_refs.media_buy.refine_proposals_async_response_input_required import (
    RefineProposalsInputRequired as RefineProposalsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.refine_proposals_async_response_submitted import (
    RefineProposalsSubmitted as RefineProposalsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.refine_proposals_async_response_working import (
    RefineProposalsWorking as RefineProposalsWorking,
)
from ._schemas.core.async_response_refs.media_buy.request_proposals_async_response_input_required import (
    RequestProposalsInputRequired as RequestProposalsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.request_proposals_async_response_submitted import (
    RequestProposalsSubmitted as RequestProposalsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.request_proposals_async_response_working import (
    RequestProposalsWorking as RequestProposalsWorking,
)
from ._schemas.core.async_response_refs.media_buy.sync_catalogs_async_response_input_required import (
    SyncCatalogsInputRequired as SyncCatalogsInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.sync_catalogs_async_response_submitted import (
    SyncCatalogsSubmitted as SyncCatalogsSubmitted,
)
from ._schemas.core.async_response_refs.media_buy.sync_catalogs_async_response_working import (
    SyncCatalogsWorking as SyncCatalogsWorking,
)
from ._schemas.core.async_response_refs.media_buy.update_media_buy_async_response_input_required import (
    UpdateMediaBuyInputRequired as UpdateMediaBuyInputRequired,
)
from ._schemas.core.async_response_refs.media_buy.update_media_buy_async_response_submitted import (
    UpdateMediaBuySubmitted as UpdateMediaBuySubmitted,
)
from ._schemas.core.async_response_refs.media_buy.update_media_buy_async_response_working import (
    UpdateMediaBuyWorking as UpdateMediaBuyWorking,
)
from ._schemas.core.async_response_refs.signals.get_signals_async_response_submitted import (
    GetSignalsSubmitted as GetSignalsSubmitted,
)
from ._schemas.core.async_response_refs.signals.get_signals_async_response_working import (
    GetSignalsWorking as GetSignalsWorking,
)
from ._schemas.core.attestation_capabilities import (
    AttestationCapabilities as AttestationCapabilities,
)
from ._schemas.core.attestation_evaluation import (
    AttestationEvaluation as AttestationEvaluation,
)
from ._schemas.core.attestation_issuer import (
    AttestationAgentIssuer as AttestationAgentIssuer,
    AttestationBrandIssuer as AttestationBrandIssuer,
    AttestationIssuer as AttestationIssuer,
    AttestationOriginIssuer as AttestationOriginIssuer,
)
from ._schemas.core.attestation_reference import (
    AttestationCredentialUriLocator as AttestationCredentialUriLocator,
    AttestationIssuerCredentialIdLocator as AttestationIssuerCredentialIdLocator,
    AttestationReference as AttestationReference,
)
from ._schemas.core.attestation_subject import (
    AttestationAgentSubject as AttestationAgentSubject,
    AttestationBrandSubject as AttestationBrandSubject,
    AttestationResourceSubject as AttestationResourceSubject,
    AttestationSubject as AttestationSubject,
)
from ._schemas.core.attribution_window import (
    AttributionWindow as AttributionWindow,
)
from ._schemas.core.audience_activation_method import (
    AdCPAudienceSync as AdCPAudienceSync,
    AudienceActivationMethod as AudienceActivationMethod,
    AudienceActivationMethodFileTransfer as AudienceActivationMethodFileTransfer,
    CleanRoom as CleanRoom,
    DatasetQuery as DatasetQuery,
    PlatformDistribution as PlatformDistribution,
    TMPIdentityMatch as TMPIdentityMatch,
)
from ._schemas.core.audience_characteristic import (
    AudienceCharacteristic as AudienceCharacteristic,
)
from ._schemas.core.audience_evidence import (
    AudienceEvidence as AudienceEvidence,
)
from ._schemas.core.audience_evidence_pin import (
    AudienceEvidencePin as AudienceEvidencePin,
)
from ._schemas.core.audience_evidence_requirements import (
    AudienceEvidenceRequirements as AudienceEvidenceRequirements,
)
from ._schemas.core.audience_evidence_selection import (
    AudienceEvidenceSelection as AudienceEvidenceSelection,
)
from ._schemas.core.audience_member import (
    AudienceMember as AudienceMember,
)
from ._schemas.core.audience_selector import (
    AudienceSelector as AudienceSelector,
    AudienceSelectorDescription as AudienceSelectorDescription,
    AudienceSelectorSignalBinary as AudienceSelectorSignalBinary,
    AudienceSelectorSignalCategorical as AudienceSelectorSignalCategorical,
    AudienceSelectorSignalNumeric as AudienceSelectorSignalNumeric,
)
from ._schemas.core.audience_source import (
    AudienceSource as AudienceSource,
    Dataset as Dataset,
    PlatformSegment as PlatformSegment,
)
from ._schemas.core.authorized_agent_base import (
    AuthorizedAgentBaseFields as AuthorizedAgentBaseFields,
)
from ._schemas.core.bidding_policy import (
    BiddingPolicy as BiddingPolicy,
)
from ._schemas.core.bidding_policy_capability import (
    BiddingPolicyCapability as BiddingPolicyCapability,
)
from ._schemas.core.brand_id import (
    BrandID as BrandID,
)
from ._schemas.core.brand_key import (
    BrandKey as BrandKey,
)
from ._schemas.core.brand_ref import (
    BrandReference as BrandReference,
)
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResult as BrandResponseAuthorizationResult,
    BrandResponseAuthorizationResultTrusted as BrandResponseAuthorizationResultTrusted,
    BrandResponseAuthorizationResultUntrusted as BrandResponseAuthorizationResultUntrusted,
)
from ._schemas.core.budget_allocation import (
    BudgetAllocation as BudgetAllocation,
    BudgetAllocationFixed as BudgetAllocationFixed,
    BudgetAllocationSellerOptimized as BudgetAllocationSellerOptimized,
)
from ._schemas.core.budget_range import (
    BudgetRange as BudgetRange,
)
from ._schemas.core.business_entity import (
    BusinessEntity as BusinessEntity,
)
from ._schemas.core.cancellation_policy import (
    CancellationPolicy as CancellationPolicy,
)
from ._schemas.core.canonical_account_ref import (
    CanonicalAccountReference as CanonicalAccountReference,
    CanonicalAccountReferenceAccountId as CanonicalAccountReferenceAccountId,
    CanonicalAccountReferenceBrandOperator as CanonicalAccountReferenceBrandOperator,
)
from ._schemas.core.canonical_audience_evidence import (
    CanonicalAudienceEvidence as CanonicalAudienceEvidence,
)
from ._schemas.core.canonical_audience_evidence_selection import (
    CanonicalAudienceEvidenceSelection as CanonicalAudienceEvidenceSelection,
)
from ._schemas.core.canonical_budget_allocation import (
    CanonicalBudgetAllocation as CanonicalBudgetAllocation,
    CanonicalBudgetAllocationFixed as CanonicalBudgetAllocationFixed,
    CanonicalBudgetAllocationSellerOptimized as CanonicalBudgetAllocationSellerOptimized,
)
from ._schemas.core.canonical_delivery_forecast import (
    CanonicalDeliveryForecast as CanonicalDeliveryForecast,
)
from ._schemas.core.canonical_forecast_point import (
    CanonicalForecastPoint as CanonicalForecastPoint,
)
from ._schemas.core.canonical_forecast_vendor_metric_value import (
    CanonicalForecastVendorMetricValue as CanonicalForecastVendorMetricValue,
)
from ._schemas.core.canonical_format_kind import (
    CanonicalFormatKind as CanonicalFormatKind,
)
from ._schemas.core.canonical_format_option import (
    CanonicalFormatOption as CanonicalFormatOption,
)
from ._schemas.core.canonical_measurement_terms import (
    CanonicalMeasurementTerms as CanonicalMeasurementTerms,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyAction as CanonicalMediaBuyAction,
    CanonicalMediaBuyActionControlMediaBuy as CanonicalMediaBuyActionControlMediaBuy,
    CanonicalMediaBuyActionRefineProposals as CanonicalMediaBuyActionRefineProposals,
    CanonicalMediaBuyActionSyncCreatives as CanonicalMediaBuyActionSyncCreatives,
)
from ._schemas.core.canonical_media_buy_action_fields import (
    CanonicalMediaBuyActionFields as CanonicalMediaBuyActionFields,
)
from ._schemas.core.canonical_media_buy_features import (
    CanonicalMediaBuyFeatures as CanonicalMediaBuyFeatures,
)
from ._schemas.core.canonical_metric_qualifier import (
    CanonicalMetricQualifier as CanonicalMetricQualifier,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoal as CanonicalOptimizationGoal,
    CanonicalOptimizationGoalEvent as CanonicalOptimizationGoalEvent,
    CanonicalOptimizationGoalMetric as CanonicalOptimizationGoalMetric,
    CanonicalOptimizationGoalVendorMetric as CanonicalOptimizationGoalVendorMetric,
    CanonicalOptimizationGoalVendorMetricTarget as CanonicalOptimizationGoalVendorMetricTarget,
)
from ._schemas.core.canonical_performance_standard import (
    CanonicalPerformanceStandard as CanonicalPerformanceStandard,
)
from ._schemas.core.canonical_placement import (
    CanonicalProductPlacement as CanonicalProductPlacement,
    CanonicalProductPlacementPublisherRef as CanonicalProductPlacementPublisherRef,
    CanonicalProductPlacementSellerInline as CanonicalProductPlacementSellerInline,
)
from ._schemas.core.canonical_pricing_option import (
    CanonicalPricingOption as CanonicalPricingOption,
)
from ._schemas.core.canonical_product import (
    CanonicalProduct as CanonicalProduct,
)
from ._schemas.core.canonical_product_action import (
    CanonicalProductAction as CanonicalProductAction,
)
from ._schemas.core.canonical_projection_ref import (
    CanonicalProjectionReference as CanonicalProjectionReference,
)
from ._schemas.core.canonical_projection_slot_override import (
    CanonicalProjectionSlotOverride as CanonicalProjectionSlotOverride,
)
from ._schemas.core.canonical_proposal import (
    CanonicalProposal as CanonicalProposal,
)
from ._schemas.core.canonical_reporting_capabilities import (
    CanonicalReportingCapabilities as CanonicalReportingCapabilities,
)
from ._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitment as CanonicalReportingCommitment,
    CanonicalReportingCommitmentStandard as CanonicalReportingCommitmentStandard,
    CanonicalReportingCommitmentVendor as CanonicalReportingCommitmentVendor,
)
from ._schemas.core.canvas_constraint import (
    CanvasConstraint as CanvasConstraint,
)
from ._schemas.core.capabilities_changed_webhook import (
    CapabilitiesChangedWebhook as CapabilitiesChangedWebhook,
)
from ._schemas.core.catalog import (
    Catalog as Catalog,
    Category as Category,
    Gtins as Gtins,
    Ids as Ids,
    Query as Query,
    Tags as Tags,
)
from ._schemas.core.catalog_field_mapping import (
    CatalogFieldMapping as CatalogFieldMapping,
)
from ._schemas.core.catalog_item_availability_error import (
    CatalogItemAvailabilityError as CatalogItemAvailabilityError,
)
from ._schemas.core.catalog_item_availability_ref import (
    CatalogItemAvailabilityReference as CatalogItemAvailabilityReference,
)
from ._schemas.core.catalog_item_availability_state import (
    CatalogItemAvailabilityState as CatalogItemAvailabilityState,
)
from ._schemas.core.catalog_item_availability_update import (
    CatalogItemAvailabilityUpdate as CatalogItemAvailabilityUpdate,
)
from ._schemas.core.catalog_item_availability_update_result import (
    CatalogItemAvailabilityUpdateResult as CatalogItemAvailabilityUpdateResult,
)
from ._schemas.core.catalog_item_delivery_metrics import (
    CatalogItemDeliveryMetrics as CatalogItemDeliveryMetrics,
)
from ._schemas.core.catalog_item_reference_not_found_error import (
    CatalogItemReferenceNotFoundError as CatalogItemReferenceNotFoundError,
)
from ._schemas.core.catalog_selection import (
    CatalogSelection as CatalogSelection,
)
from ._schemas.core.catchment import (
    Catchment as Catchment,
)
from ._schemas.core.collection import (
    Collection as Collection,
)
from ._schemas.core.collection_delivery_metrics import (
    CollectionDeliveryMetrics as CollectionDeliveryMetrics,
)
from ._schemas.core.collection_distribution import (
    CollectionDistribution as CollectionDistribution,
)
from ._schemas.core.collection_list_ref import (
    CollectionListReference as CollectionListReference,
)
from ._schemas.core.collection_property_delivery_metrics import (
    CollectionPropertyDeliveryMetrics as CollectionPropertyDeliveryMetrics,
)
from ._schemas.core.collection_ref import (
    CollectionReference as CollectionReference,
)
from ._schemas.core.collection_selection import (
    CollectionSelection as CollectionSelection,
    ProductDefaultCollections as ProductDefaultCollections,
    SelectedCollections as SelectedCollections,
)
from ._schemas.core.collection_selector import (
    CollectionSelector as CollectionSelector,
)
from ._schemas.core.committed_metric import (
    CommittedMetric as CommittedMetric,
    CommittedMetricStandard as CommittedMetricStandard,
    CommittedMetricVendor as CommittedMetricVendor,
)
from ._schemas.core.compact_task_input_required import (
    CompactTaskInputRequired as CompactTaskInputRequired,
)
from ._schemas.core.compact_task_submitted import (
    CompactTaskSubmitted as CompactTaskSubmitted,
)
from ._schemas.core.compact_task_working import (
    CompactTaskWorking as CompactTaskWorking,
)
from ._schemas.core.content_rating import (
    ContentRating as ContentRating,
)
from ._schemas.core.context import (
    ContextObject as ContextObject,
)
from ._schemas.core.creative_approval_scope import (
    ScopedCreativeApproval as ScopedCreativeApproval,
)
from ._schemas.core.creative_asset import (
    CreativeAsset as CreativeAsset,
)
from ._schemas.core.creative_assets import (
    CreativeAssets as CreativeAssets,
)
from ._schemas.core.creative_assignment import (
    CreativeAssignment as CreativeAssignment,
)
from ._schemas.core.creative_brief import (
    CreativeBrief as CreativeBrief,
)
from ._schemas.core.creative_consumption import (
    CreativeConsumption as CreativeConsumption,
)
from ._schemas.core.creative_delivery_metrics import (
    CreativeDeliveryMetrics as CreativeDeliveryMetrics,
)
from ._schemas.core.creative_filters import (
    CreativeFilters as CreativeFilters,
)
from ._schemas.core.creative_item import (
    CreativeItem as CreativeItem,
    CreativeItemMedia as CreativeItemMedia,
    CreativeItemText as CreativeItemText,
)
from ._schemas.core.creative_locale_policy import (
    CreativeLocalePolicy as CreativeLocalePolicy,
)
from ._schemas.core.creative_localization import (
    CreativeLocalization as CreativeLocalization,
)
from ._schemas.core.creative_localization_readback import (
    CreativeLocalizationReadback as CreativeLocalizationReadback,
    ResolvedAssets as ResolvedAssets,
    SourceLocalizationReadback as SourceLocalizationReadback,
    TargetLocalizationReadback as TargetLocalizationReadback,
)
from ._schemas.core.creative_manifest import (
    CreativeManifest as CreativeManifest,
)
from ._schemas.core.creative_operation_format_declaration import (
    CreativeOperationFormatDeclaration as CreativeOperationFormatDeclaration,
)
from ._schemas.core.creative_policy import (
    CreativePolicy as CreativePolicy,
)
from ._schemas.core.creative_representation import (
    CreativeRepresentation as CreativeRepresentation,
)
from ._schemas.core.creative_representation_set import (
    CreativeRepresentationSet as CreativeRepresentationSet,
)
from ._schemas.core.creative_revision_id import (
    CreativeRevisionID as CreativeRevisionID,
)
from ._schemas.core.creative_variable import (
    CreativeVariable as CreativeVariable,
)
from ._schemas.core.creative_variant import (
    CreativeVariant as CreativeVariant,
)
from ._schemas.core.daast_tracker_constraints import (
    DAASTTrackerConstraints as DAASTTrackerConstraints,
    DAASTTrackerConstraintsDaastTarget as DAASTTrackerConstraintsDaastTarget,
    DaastOffset as DaastOffset,
    DaastVersions as DaastVersions,
)
from ._schemas.core.data_provider_signal_selector import (
    DataProviderSignalSelector as DataProviderSignalSelector,
    DataProviderSignalSelectorAll as DataProviderSignalSelectorAll,
    DataProviderSignalSelectorById as DataProviderSignalSelectorById,
    DataProviderSignalSelectorByTag as DataProviderSignalSelectorByTag,
)
from ._schemas.core.date_range import (
    DateRange as DateRange,
)
from ._schemas.core.datetime_range import (
    DatetimeRange as DatetimeRange,
)
from ._schemas.core.daypart_target import (
    DaypartTarget as DaypartTarget,
)
from ._schemas.core.deadline_policy import (
    DeadlinePolicy as DeadlinePolicy,
)
from ._schemas.core.delivery_breakdown_controls import (
    DeliveryBreakdownControls as DeliveryBreakdownControls,
)
from ._schemas.core.delivery_forecast import (
    DeliveryForecast as DeliveryForecast,
)
from ._schemas.core.delivery_metric_aggregate import (
    DeliveryMetricAggregate as DeliveryMetricAggregate,
    DeliveryMetricAggregateStandard as DeliveryMetricAggregateStandard,
    DeliveryMetricAggregateVendor as DeliveryMetricAggregateVendor,
)
from ._schemas.core.delivery_metrics import (
    DeliveryMetrics as DeliveryMetrics,
)
from ._schemas.core.delivery_provider import (
    DeliveryProvider as DeliveryProvider,
)
from ._schemas.core.delivery_recipient import (
    DeliveryRecipient as DeliveryRecipient,
)
from ._schemas.core.demographic_age_range import (
    DemographicAgeRange as DemographicAgeRange,
)
from ._schemas.core.demographic_predicate import (
    DemographicPredicate as DemographicPredicate,
)
from ._schemas.core.demographic_reporting_capability import (
    DemographicReportingCapability as DemographicReportingCapability,
)
from ._schemas.core.demographic_targeting_capability import (
    DemographicTargetingCapability as DemographicTargetingCapability,
)
from ._schemas.core.demographic_targeting_intent import (
    DemographicTargetingIntent as DemographicTargetingIntent,
)
from ._schemas.core.demographic_targeting_resolution import (
    DemographicTargetingResolution as DemographicTargetingResolution,
    ExecutionContinuousBounds as ExecutionContinuousBounds,
    ExecutionEnumeratedIntervals as ExecutionEnumeratedIntervals,
    ExecutionSignals as ExecutionSignals,
)
from ._schemas.core.deployment import (
    Deployment as Deployment,
    DeploymentAgent as DeploymentAgent,
    DeploymentPlatform as DeploymentPlatform,
)
from ._schemas.core.destination import (
    Destination as Destination,
    DestinationAgent as DestinationAgent,
    DestinationPlatform as DestinationPlatform,
)
from ._schemas.core.destination_item import (
    DestinationItem as DestinationItem,
)
from ._schemas.core.diagnostic_issue import (
    DiagnosticIssue as DiagnosticIssue,
)
from ._schemas.core.downstream_connection_requirement import (
    DownstreamConnectionRequirement as DownstreamConnectionRequirement,
)
from ._schemas.core.duration import (
    Duration as Duration,
)
from ._schemas.core.education_item import (
    EducationItem as EducationItem,
)
from ._schemas.core.error import (
    Error as Error,
)
from ._schemas.core.evaluator_spec import (
    EvaluatorSpec as EvaluatorSpec,
    EvaluatorSpecAgentUrl as EvaluatorSpecAgentUrl,
    EvaluatorSpecEvaluatorId as EvaluatorSpecEvaluatorId,
    EvaluatorSpecExemplars as EvaluatorSpecExemplars,
)
from ._schemas.core.event import (
    Event as Event,
)
from ._schemas.core.event_custom_data import (
    EventCustomData as EventCustomData,
)
from ._schemas.core.event_source_health import (
    EventSourceHealth as EventSourceHealth,
)
from ._schemas.core.event_surface import (
    EventSurface as EventSurface,
)
from ._schemas.core.experimental_feature_id import (
    ExperimentalFeatureID as ExperimentalFeatureID,
)
from ._schemas.core.ext import (
    ExtensionObject as ExtensionObject,
)
from ._schemas.core.feature_requirement import (
    FeatureRequirement as FeatureRequirement,
)
from ._schemas.core.flight_item import (
    FlightItem as FlightItem,
)
from ._schemas.core.forecast_dimension_audience import (
    AudienceForecastDimension as AudienceForecastDimension,
)
from ._schemas.core.forecast_dimension_device_platform import (
    DevicePlatformForecastDimension as DevicePlatformForecastDimension,
)
from ._schemas.core.forecast_dimension_device_type import (
    DeviceTypeForecastDimension as DeviceTypeForecastDimension,
)
from ._schemas.core.forecast_dimension_geo import (
    GeoForecastDimension as GeoForecastDimension,
)
from ._schemas.core.forecast_dimension_placement import (
    PlacementForecastDimension as PlacementForecastDimension,
)
from ._schemas.core.forecast_dimension_signal import (
    SignalForecastDimension as SignalForecastDimension,
)
from ._schemas.core.forecast_dimension_time import (
    TimeForecastDimension as TimeForecastDimension,
)
from ._schemas.core.forecast_point import (
    ForecastPoint as ForecastPoint,
)
from ._schemas.core.forecast_point_dimensions import (
    ForecastPointDimensions as ForecastPointDimensions,
)
from ._schemas.core.forecast_range import (
    ForecastRange as ForecastRange,
)
from ._schemas.core.forecast_rate_range import (
    ForecastRateRange as ForecastRateRange,
)
from ._schemas.core.forecast_vendor_metric_value import (
    ForecastVendorMetricValue as ForecastVendorMetricValue,
)
from ._schemas.core.format import (
    AssetsItemIndividual as AssetsItemIndividual,
    Format as Format,
    GroupAudioAsset as GroupAudioAsset,
    GroupBriefAsset as GroupBriefAsset,
    GroupCardAsset as GroupCardAsset,
    GroupCatalogAsset as GroupCatalogAsset,
    GroupCssAsset as GroupCssAsset,
    GroupDaastAsset as GroupDaastAsset,
    GroupDaastTrackerAsset as GroupDaastTrackerAsset,
    GroupDisplayTagAsset as GroupDisplayTagAsset,
    GroupHtmlAsset as GroupHtmlAsset,
    GroupImageAsset as GroupImageAsset,
    GroupJavaScriptAsset as GroupJavaScriptAsset,
    GroupMarkdownAsset as GroupMarkdownAsset,
    GroupPixelTrackerAsset as GroupPixelTrackerAsset,
    GroupPublishedPostAsset as GroupPublishedPostAsset,
    GroupTextAsset as GroupTextAsset,
    GroupUrlAsset as GroupUrlAsset,
    GroupVastAsset as GroupVastAsset,
    GroupVastTrackerAsset as GroupVastTrackerAsset,
    GroupVideoAsset as GroupVideoAsset,
    GroupWebhookAsset as GroupWebhookAsset,
    GroupZipAsset as GroupZipAsset,
    IndividualAudioAsset as IndividualAudioAsset,
    IndividualBriefAsset as IndividualBriefAsset,
    IndividualCardAsset as IndividualCardAsset,
    IndividualCatalogAsset as IndividualCatalogAsset,
    IndividualCssAsset as IndividualCssAsset,
    IndividualDaastAsset as IndividualDaastAsset,
    IndividualDaastTrackerAsset as IndividualDaastTrackerAsset,
    IndividualDisplayTagAsset as IndividualDisplayTagAsset,
    IndividualHtmlAsset as IndividualHtmlAsset,
    IndividualImageAsset as IndividualImageAsset,
    IndividualJavaScriptAsset as IndividualJavaScriptAsset,
    IndividualMarkdownAsset as IndividualMarkdownAsset,
    IndividualPixelTrackerAsset as IndividualPixelTrackerAsset,
    IndividualPublishedPostAsset as IndividualPublishedPostAsset,
    IndividualTextAsset as IndividualTextAsset,
    IndividualUrlAsset as IndividualUrlAsset,
    IndividualVastAsset as IndividualVastAsset,
    IndividualVastTrackerAsset as IndividualVastTrackerAsset,
    IndividualVideoAsset as IndividualVideoAsset,
    IndividualWebhookAsset as IndividualWebhookAsset,
    IndividualZipAsset as IndividualZipAsset,
    RendersItemDimensions as RendersItemDimensions,
    RendersItemParametersFromFormatId as RendersItemParametersFromFormatId,
    RepeatableGroupAsset as RepeatableGroupAsset,
)
from ._schemas.core.format_id import (
    FormatReferenceStructuredObject as FormatReferenceStructuredObject,
)
from ._schemas.core.format_option_ref import (
    FormatOptionReference as FormatOptionReference,
    ProductLocalFormatOptionReference as ProductLocalFormatOptionReference,
    PublisherCatalogFormatOptionReference as PublisherCatalogFormatOptionReference,
)
from ._schemas.core.format_shape_vocabulary import (
    AdCPFormatShapeVocabularyRegistry as AdCPFormatShapeVocabularyRegistry,
)
from ._schemas.core.frequency_cap import (
    FrequencyCap as FrequencyCap,
)
from ._schemas.core.frequency_cap_constraints import (
    FrequencyCapConstraints as FrequencyCapConstraints,
)
from ._schemas.core.frequency_cap_duration_unit import (
    FrequencyCapDurationUnit as FrequencyCapDurationUnit,
)
from ._schemas.core.frequency_cap_impression_constraints import (
    FrequencyCapImpressionConstraints as FrequencyCapImpressionConstraints,
)
from ._schemas.core.frequency_cap_interval_constraints import (
    FrequencyCapIntervalConstraints as FrequencyCapIntervalConstraints,
)
from ._schemas.core.frequency_cap_requirements import (
    FrequencyCapRequirements as FrequencyCapRequirements,
)
from ._schemas.core.generation_credential import (
    GenerationCredential as GenerationCredential,
)
from ._schemas.core.geo_breakdown_support import (
    GeographicBreakdownSupport as GeographicBreakdownSupport,
)
from ._schemas.core.geo_delivery_metrics import (
    GeoDeliveryMetrics as GeoDeliveryMetrics,
)
from ._schemas.core.geo_metro import (
    GeoMetro as GeoMetro,
)
from ._schemas.core.geo_place_area import (
    GeographicPlaceArea as GeographicPlaceArea,
)
from ._schemas.core.geo_place_catalog_capability import (
    GeographicPlaceCatalogCapability as GeographicPlaceCatalogCapability,
)
from ._schemas.core.geo_place_catalog_entry import (
    GeographicPlaceCatalogEntry as GeographicPlaceCatalogEntry,
)
from ._schemas.core.geo_place_requirement import (
    GeographicPlaceRequirement as GeographicPlaceRequirement,
)
from ._schemas.core.geo_place_resolver import (
    GeographicPlaceResolver as GeographicPlaceResolver,
)
from ._schemas.core.geo_place_support import (
    GeographicPlaceSystemSupport as GeographicPlaceSystemSupport,
)
from ._schemas.core.geo_place_system import (
    GeographicPlaceIdentifierSystem as GeographicPlaceIdentifierSystem,
)
from ._schemas.core.geo_place_type import (
    GeographicPlaceType as GeographicPlaceType,
)
from ._schemas.core.geo_region_requirement import (
    GeographicRegionRequirement as GeographicRegionRequirement,
    GeographicRegionRequirementCountriesValueAllValues as GeographicRegionRequirementCountriesValueAllValues,
    GeographicRegionRequirementCountriesValueValues as GeographicRegionRequirementCountriesValueValues,
)
from ._schemas.core.geo_region_support import (
    GeographicRegionSupport as GeographicRegionSupport,
    GeographicRegionSupportCountriesValueAllValues as GeographicRegionSupportCountriesValueAllValues,
    GeographicRegionSupportCountriesValueValues as GeographicRegionSupportCountriesValueValues,
)
from ._schemas.core.get_geo_place_resolution_request import (
    GetGeographicPlaceResolutionRequest as GetGeographicPlaceResolutionRequest,
)
from ._schemas.core.get_geo_place_resolution_response import (
    GetGeographicPlaceResolutionResponse as GetGeographicPlaceResolutionResponse,
)
from ._schemas.core.hotel_item import (
    HotelItem as HotelItem,
)
from ._schemas.core.iana_timezone import (
    IANATimezoneIdentifier as IANATimezoneIdentifier,
)
from ._schemas.core.identifier import (
    Identifier as Identifier,
)
from ._schemas.core.impairment import (
    Impairment as Impairment,
)
from ._schemas.core.indicator import (
    Indicator as Indicator,
)
from ._schemas.core.indicator_bearing import (
    IndicatorBearingResourceState as IndicatorBearingResourceState,
)
from ._schemas.core.indicator_scope import (
    IndicatorScope as IndicatorScope,
)
from ._schemas.core.indicators_changed_webhook import (
    IndicatorsChangedWebhook as IndicatorsChangedWebhook,
)
from ._schemas.core.industry_identifier import (
    IndustryIdentifier as IndustryIdentifier,
)
from ._schemas.core.insertion_order import (
    InsertionOrder as InsertionOrder,
)
from ._schemas.core.installment import (
    Installment as Installment,
)
from ._schemas.core.installment_deadlines import (
    InstallmentDeadlines as InstallmentDeadlines,
)
from ._schemas.core.installment_delivery_metrics import (
    InstallmentDeliveryMetrics as InstallmentDeliveryMetrics,
)
from ._schemas.core.installment_property_delivery_metrics import (
    InstallmentPropertyDeliveryMetrics as InstallmentPropertyDeliveryMetrics,
)
from ._schemas.core.installment_ref import (
    InstallmentReference as InstallmentReference,
)
from ._schemas.core.inventory_list_application import (
    CollectionListApplication as CollectionListApplication,
    InventoryListApplication as InventoryListApplication,
    PropertyListApplication as PropertyListApplication,
)
from ._schemas.core.job_item import (
    JobItem as JobItem,
)
from ._schemas.core.keyword_delivery_metrics import (
    KeywordDeliveryMetrics as KeywordDeliveryMetrics,
)
from ._schemas.core.keyword_target import (
    KeywordTarget as KeywordTarget,
)
from ._schemas.core.limited_series import (
    LimitedSeries as LimitedSeries,
)
from ._schemas.core.locale_tag import (
    LanguageTag as LanguageTag,
)
from ._schemas.core.localized_creative_asset import (
    LocalizedCreativeAsset as LocalizedCreativeAsset,
)
from ._schemas.core.macro_bearing_url import (
    MacroBearingURL as MacroBearingURL,
)
from ._schemas.core.macro_declaration import (
    MacroDeclaration as MacroDeclaration,
)
from ._schemas.core.macro_encoding import (
    MacroEncoding as MacroEncoding,
)
from ._schemas.core.macro_resolution_capability import (
    MacroProcessingCapability as MacroProcessingCapability,
)
from ._schemas.core.macro_resolution_result import (
    MacroResolutionResult as MacroResolutionResult,
)
from ._schemas.core.macro_translation_target import (
    MacroTranslationTarget as MacroTranslationTarget,
)
from ._schemas.core.material_deadline import (
    MaterialDeadline as MaterialDeadline,
)
from ._schemas.core.mcp_webhook_payload import (
    MCPWebhookPayload as MCPWebhookPayload,
)
from ._schemas.core.measurement_readiness import (
    MeasurementReadiness as MeasurementReadiness,
)
from ._schemas.core.measurement_terms import (
    MeasurementTerms as MeasurementTerms,
)
from ._schemas.core.measurement_window import (
    MeasurementWindow as MeasurementWindow,
)
from ._schemas.core.media_buy import (
    MediaBuy as MediaBuy,
)
from ._schemas.core.media_buy_available_action import (
    MediaBuyAvailableAction as MediaBuyAvailableAction,
)
from ._schemas.core.media_buy_available_action_id import (
    MediaBuyAvailableActionID as MediaBuyAvailableActionID,
)
from ._schemas.core.media_buy_change_term_id import (
    MediaBuyChangeTermID as MediaBuyChangeTermID,
)
from ._schemas.core.media_buy_features import (
    MediaBuyFeatures as MediaBuyFeatures,
)
from ._schemas.core.media_buy_frequency_cap import (
    MediaBuyFrequencyCap as MediaBuyFrequencyCap,
)
from ._schemas.core.media_buy_frequency_cap_capability import (
    MediaBuyFrequencyCapCapability as MediaBuyFrequencyCapCapability,
)
from ._schemas.core.media_buy_frequency_cap_requirement import (
    MediaBuyFrequencyCapRequirement as MediaBuyFrequencyCapRequirement,
)
from ._schemas.core.media_buy_frequency_cap_support import (
    MediaBuyFrequencyCapSupport as MediaBuyFrequencyCapSupport,
)
from ._schemas.core.media_buy_legacy_terms_ref import (
    MediaBuyTermsReference as MediaBuyTermsReference,
)
from ._schemas.core.media_buy_support import (
    ProductMediaBuySupport as ProductMediaBuySupport,
)
from ._schemas.core.media_buy_support_requirements import (
    ProductMediaBuySupportRequirements as ProductMediaBuySupportRequirements,
)
from ._schemas.core.missing_metric import (
    MissingMetric as MissingMetric,
    MissingMetricStandard as MissingMetricStandard,
    MissingMetricVendor as MissingMetricVendor,
)
from ._schemas.core.negative_keyword import (
    NegativeKeyword as NegativeKeyword,
)
from ._schemas.core.notification_config import (
    NotificationConfig as NotificationConfig,
)
from ._schemas.core.offering import (
    Offering as Offering,
)
from ._schemas.core.offering_asset_group import (
    OfferingAssetGroup as OfferingAssetGroup,
)
from ._schemas.core.operator_identity import (
    OperatorIdentity as OperatorIdentity,
)
from ._schemas.core.operator_unit import (
    OperatorUnit as OperatorUnit,
)
from ._schemas.core.opportunity_context import (
    OpportunityContext as OpportunityContext,
)
from ._schemas.core.optimization_goal import (
    OptimizationGoal as OptimizationGoal,
    OptimizationGoalEvent as OptimizationGoalEvent,
    OptimizationGoalEventTargetCostPer as OptimizationGoalEventTargetCostPer,
    OptimizationGoalMetric as OptimizationGoalMetric,
    OptimizationGoalMetricTargetCostPer as OptimizationGoalMetricTargetCostPer,
    OptimizationGoalMetricTargetThresholdRate as OptimizationGoalMetricTargetThresholdRate,
    OptimizationGoalVendorMetric as OptimizationGoalVendorMetric,
    OptimizationGoalVendorMetricTargetCostPer as OptimizationGoalVendorMetricTargetCostPer,
    OptimizationGoalVendorMetricTargetThresholdRate as OptimizationGoalVendorMetricTargetThresholdRate,
    TargetMaximizeValue as TargetMaximizeValue,
    TargetPerAdSpend as TargetPerAdSpend,
)
from ._schemas.core.outcome_measurement import (
    OutcomeMeasurement as OutcomeMeasurement,
)
from ._schemas.core.outcome_target_cost_per import (
    OutcomeTargetCostPer as OutcomeTargetCostPer,
)
from ._schemas.core.overlay import (
    Overlay as Overlay,
)
from ._schemas.core.package import (
    Package as Package,
)
from ._schemas.core.package_delivery_metric_value import (
    PackageDeliveryMetricValue as PackageDeliveryMetricValue,
)
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshot as PackageFormatSnapshot,
    PackageFormatSnapshotAgentPlacement as PackageFormatSnapshotAgentPlacement,
    PackageFormatSnapshotAudioDaast as PackageFormatSnapshotAudioDaast,
    PackageFormatSnapshotAudioHosted as PackageFormatSnapshotAudioHosted,
    PackageFormatSnapshotAudioVast as PackageFormatSnapshotAudioVast,
    PackageFormatSnapshotCoordinatedPlacements as PackageFormatSnapshotCoordinatedPlacements,
    PackageFormatSnapshotCustom as PackageFormatSnapshotCustom,
    PackageFormatSnapshotDisplayTag as PackageFormatSnapshotDisplayTag,
    PackageFormatSnapshotHtml5 as PackageFormatSnapshotHtml5,
    PackageFormatSnapshotImage as PackageFormatSnapshotImage,
    PackageFormatSnapshotImageCarousel as PackageFormatSnapshotImageCarousel,
    PackageFormatSnapshotNativeInFeed as PackageFormatSnapshotNativeInFeed,
    PackageFormatSnapshotResponsiveCreative as PackageFormatSnapshotResponsiveCreative,
    PackageFormatSnapshotSellerRenderedStatefulDisplay as PackageFormatSnapshotSellerRenderedStatefulDisplay,
    PackageFormatSnapshotSponsoredPlacement as PackageFormatSnapshotSponsoredPlacement,
    PackageFormatSnapshotVideoHosted as PackageFormatSnapshotVideoHosted,
    PackageFormatSnapshotVideoVast as PackageFormatSnapshotVideoVast,
)
from ._schemas.core.package_signal_targeting import (
    PackageSignalTargeting as PackageSignalTargeting,
    PackageSignalTargetingBinary as PackageSignalTargetingBinary,
    PackageSignalTargetingCategorical as PackageSignalTargetingCategorical,
    PackageSignalTargetingNumeric as PackageSignalTargetingNumeric,
)
from ._schemas.core.package_signal_targeting_group import (
    PackageSignalTargetingGroup as PackageSignalTargetingGroup,
)
from ._schemas.core.package_signal_targeting_groups import (
    PackageSignalTargetingGroups as PackageSignalTargetingGroups,
)
from ._schemas.core.package_targeting_resolution import (
    PackageTargetingResolution as PackageTargetingResolution,
)
from ._schemas.core.pagination_request import (
    PaginationRequest as PaginationRequest,
)
from ._schemas.core.pagination_response import (
    PaginationResponse as PaginationResponse,
)
from ._schemas.core.performance_feedback import (
    MetricStandard as MetricStandard,
    MetricVendor as MetricVendor,
    PerformanceFeedback as PerformanceFeedback,
)
from ._schemas.core.performance_feedback_assertion import (
    PerformanceFeedbackAssertion as PerformanceFeedbackAssertion,
)
from ._schemas.core.performance_feedback_metric import (
    PerformanceFeedbackMetric as PerformanceFeedbackMetric,
    PerformanceFeedbackMetricStandard as PerformanceFeedbackMetricStandard,
    PerformanceFeedbackMetricVendor as PerformanceFeedbackMetricVendor,
)
from ._schemas.core.performance_standard import (
    PerformanceStandard as PerformanceStandard,
)
from ._schemas.core.placement import (
    Placement as Placement,
)
from ._schemas.core.placement_definition import (
    FormatOptionsItemFormatOptionId as FormatOptionsItemFormatOptionId,
    PlacementDefinition as PlacementDefinition,
)
from ._schemas.core.placement_delivery_metrics import (
    PlacementDeliveryMetrics as PlacementDeliveryMetrics,
)
from ._schemas.core.placement_evidence import (
    PlacementEvidence as PlacementEvidence,
)
from ._schemas.core.placement_identity import (
    PlacementIdentity as PlacementIdentity,
    PublisherCatalogPlacementIdentity as PublisherCatalogPlacementIdentity,
    SellerInlinePlacementIdentity as SellerInlinePlacementIdentity,
)
from ._schemas.core.placement_presentation import (
    Color as Color,
    PlacementPresentationDocument as PlacementPresentationDocument,
)
from ._schemas.core.placement_property_delivery_metrics import (
    PlacementPropertyDeliveryMetrics as PlacementPropertyDeliveryMetrics,
)
from ._schemas.core.placement_ref import (
    PlacementReference as PlacementReference,
)
from ._schemas.core.placement_selection import (
    PlacementRefsItem as PlacementRefsItem,
    PlacementSelection as PlacementSelection,
    ProductDefaultPlacements as ProductDefaultPlacements,
    SelectedPlacements as SelectedPlacements,
)
from ._schemas.core.planned_delivery import (
    PlannedDelivery as PlannedDelivery,
)
from ._schemas.core.platform_extension_ref import (
    PlatformExtensionReference as PlatformExtensionReference,
)
from ._schemas.core.positive_postal_area_support import (
    PositivePostalAreaSupport as PositivePostalAreaSupport,
)
from ._schemas.core.postal_area import (
    PostalArea as PostalArea,
    PostalAreaAUPostcode as PostalAreaAUPostcode,
    PostalAreaBRCep as PostalAreaBRCep,
    PostalAreaBranch9 as PostalAreaBranch9,
    PostalAreaCA as PostalAreaCA,
    PostalAreaCountrySystemValues as PostalAreaCountrySystemValues,
    PostalAreaFRCodePostal as PostalAreaFRCodePostal,
    PostalAreaGB as PostalAreaGB,
    PostalAreaINPin as PostalAreaINPin,
    PostalAreaPlz as PostalAreaPlz,
    PostalAreaUS as PostalAreaUS,
    PostalAreaWithFusedSystem as PostalAreaWithFusedSystem,
    PostalAreaZAPostalCode as PostalAreaZAPostalCode,
)
from ._schemas.core.postal_area_support import (
    PostalAreaSupport as PostalAreaSupport,
)
from ._schemas.core.postal_country_system import (
    PostalCountrySystem as PostalCountrySystem,
    PostalCountrySystemAUPostcode as PostalCountrySystemAUPostcode,
    PostalCountrySystemBRCep as PostalCountrySystemBRCep,
    PostalCountrySystemBranch9 as PostalCountrySystemBranch9,
    PostalCountrySystemCA as PostalCountrySystemCA,
    PostalCountrySystemFRCodePostal as PostalCountrySystemFRCodePostal,
    PostalCountrySystemGB as PostalCountrySystemGB,
    PostalCountrySystemINPin as PostalCountrySystemINPin,
    PostalCountrySystemPlz as PostalCountrySystemPlz,
    PostalCountrySystemUS as PostalCountrySystemUS,
    PostalCountrySystemZAPostalCode as PostalCountrySystemZAPostalCode,
)
from ._schemas.core.presentation_ref import (
    PlacementPresentationReference as PlacementPresentationReference,
)
from ._schemas.core.preview_provider import (
    PublisherDesignatedPreviewProvider as PublisherDesignatedPreviewProvider,
)
from ._schemas.core.preview_renderer_metadata import (
    PreviewRendererMetadata as PreviewRendererMetadata,
)
from ._schemas.core.price import (
    Price as Price,
)
from ._schemas.core.pricing_option import (
    PricingOption as PricingOption,
    PricingOptionCpa as PricingOptionCpa,
    PricingOptionCpc as PricingOptionCpc,
    PricingOptionCpcv as PricingOptionCpcv,
    PricingOptionCpm as PricingOptionCpm,
    PricingOptionCpp as PricingOptionCpp,
    PricingOptionCpv as PricingOptionCpv,
    PricingOptionFlatRate as PricingOptionFlatRate,
    PricingOptionRevenueShare as PricingOptionRevenueShare,
    PricingOptionTime as PricingOptionTime,
    PricingOptionVcpm as PricingOptionVcpm,
)
from ._schemas.core.principal_changed_webhook import (
    PrincipalChangedWebhook as PrincipalChangedWebhook,
)
from ._schemas.core.principal_declarations import (
    AgentDeclarations as AgentDeclarations,
)
from ._schemas.core.principal_declarations_state import (
    PrincipalDeclarationsState as PrincipalDeclarationsState,
)
from ._schemas.core.principal_state import (
    PrincipalState as PrincipalState,
)
from ._schemas.core.product import (
    Product as Product,
)
from ._schemas.core.product_allocation import (
    ProductAllocation as ProductAllocation,
)
from ._schemas.core.product_allowed_action import (
    ProductAllowedAction as ProductAllowedAction,
)
from ._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuersItemAgent as AcceptedAttestationIssuersItemAgent,
    AcceptedAttestationIssuersItemBrand as AcceptedAttestationIssuersItemBrand,
    ProductAudienceEvidenceRequirements as ProductAudienceEvidenceRequirements,
)
from ._schemas.core.product_card_reference_asset import (
    ProductCardReferenceAsset as ProductCardReferenceAsset,
)
from ._schemas.core.product_change_map import (
    ProductChangeMap as ProductChangeMap,
)
from ._schemas.core.product_execution_requirement import (
    CatalogExecutionRequirement as CatalogExecutionRequirement,
    DownstreamConnectionExecutionRequirement as DownstreamConnectionExecutionRequirement,
    EventSourceExecutionRequirement as EventSourceExecutionRequirement,
    ProductExecutionRequirement as ProductExecutionRequirement,
)
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemCleanRoom as AudienceActivationMethodsItemCleanRoom,
    AudienceActivationMethodsItemDatasetQuery as AudienceActivationMethodsItemDatasetQuery,
    AudienceActivationMethodsItemFileTransfer as AudienceActivationMethodsItemFileTransfer,
    AudienceActivationMethodsItemPlatformDistribution as AudienceActivationMethodsItemPlatformDistribution,
    AudienceActivationMethodsItemTmpIdentityMatch as AudienceActivationMethodsItemTmpIdentityMatch,
    PricingCurrenciesItem as PricingCurrenciesItem,
    ProductFilters as ProductFilters,
    SignalTargetingItemBinary as SignalTargetingItemBinary,
    SignalTargetingItemCategorical as SignalTargetingItemCategorical,
    SignalTargetingItemNumeric as SignalTargetingItemNumeric,
)
from ._schemas.core.product_format_declaration import (
    AgentPlacementFormatDeclaration as AgentPlacementFormatDeclaration,
    CoordinatedPlacementsFormatDeclaration as CoordinatedPlacementsFormatDeclaration,
    CustomFormatDeclaration as CustomFormatDeclaration,
    DAASTAudioFormatDeclaration as DAASTAudioFormatDeclaration,
    DisplayTagFormatDeclaration as DisplayTagFormatDeclaration,
    HTML5FormatDeclaration as HTML5FormatDeclaration,
    HostedAudioFormatDeclaration as HostedAudioFormatDeclaration,
    HostedVideoFormatDeclaration as HostedVideoFormatDeclaration,
    ImageCarouselFormatDeclaration as ImageCarouselFormatDeclaration,
    ImageFormatDeclaration as ImageFormatDeclaration,
    NativeInFeedFormatDeclaration as NativeInFeedFormatDeclaration,
    ProductFormatDeclaration as ProductFormatDeclaration,
    ResponsiveCreativeFormatDeclaration as ResponsiveCreativeFormatDeclaration,
    SellerRenderedStatefulDisplayFormatDeclaration as SellerRenderedStatefulDisplayFormatDeclaration,
    SponsoredPlacementFormatDeclaration as SponsoredPlacementFormatDeclaration,
    VASTAudioFormatDeclaration as VASTAudioFormatDeclaration,
    VASTVideoFormatDeclaration as VASTVideoFormatDeclaration,
)
from ._schemas.core.product_identity import (
    ProductIdentity as ProductIdentity,
)
from ._schemas.core.product_offer_filters import (
    ProductOfferFilters as ProductOfferFilters,
)
from ._schemas.core.product_signal_targeting_option import (
    ProductSignalTargetingOption as ProductSignalTargetingOption,
)
from ._schemas.core.product_targeting_resolution import (
    ProductTargetingResolution as ProductTargetingResolution,
)
from ._schemas.core.property import (
    Property as Property,
)
from ._schemas.core.property_delivery_metrics import (
    PropertyDeliveryMetrics as PropertyDeliveryMetrics,
)
from ._schemas.core.property_id import (
    PropertyID as PropertyID,
)
from ._schemas.core.property_list_ref import (
    PropertyListReference as PropertyListReference,
)
from ._schemas.core.property_ref import (
    PropertyReference as PropertyReference,
)
from ._schemas.core.property_tag import (
    PropertyTag as PropertyTag,
)
from ._schemas.core.proposal import (
    Proposal as Proposal,
)
from ._schemas.core.protocol_envelope import (
    ProtocolEnvelope as ProtocolEnvelope,
)
from ._schemas.core.provenance import (
    Provenance as Provenance,
)
from ._schemas.core.publisher_property_selector import (
    PublisherPropertySelector as PublisherPropertySelector,
    PublisherPropertySelectorAll as PublisherPropertySelectorAll,
    PublisherPropertySelectorById as PublisherPropertySelectorById,
    PublisherPropertySelectorByTag as PublisherPropertySelectorByTag,
)
from ._schemas.core.push_notification_config import (
    PushNotificationConfig as PushNotificationConfig,
)
from ._schemas.core.real_estate_item import (
    RealEstateItem as RealEstateItem,
)
from ._schemas.core.reference_asset import (
    ReferenceAsset as ReferenceAsset,
)
from ._schemas.core.reference_renderer import (
    ReferenceRenderer as ReferenceRenderer,
)
from ._schemas.core.registry_event import (
    ChangedFields as ChangedFields,
    Countries as Countries,
    Domain as Domain,
    RegistryEvent as RegistryEvent,
    RegistryEventAgentComplianceChangedAgent as RegistryEventAgentComplianceChangedAgent,
    RegistryEventAgentDiscoveredAgent as RegistryEventAgentDiscoveredAgent,
    RegistryEventAgentProfileUpdatedAgent as RegistryEventAgentProfileUpdatedAgent,
    RegistryEventAgentRemovedAgent as RegistryEventAgentRemovedAgent,
    RegistryEventAgentVerificationEarnedAgent as RegistryEventAgentVerificationEarnedAgent,
    RegistryEventAgentVerificationLostAgent as RegistryEventAgentVerificationLostAgent,
    RegistryEventAuthorizationGrantedAuthorization as RegistryEventAuthorizationGrantedAuthorization,
    RegistryEventAuthorizationModifiedAuthorization as RegistryEventAuthorizationModifiedAuthorization,
    RegistryEventAuthorizationRevokedAuthorization as RegistryEventAuthorizationRevokedAuthorization,
    RegistryEventCollectionCreatedCollection as RegistryEventCollectionCreatedCollection,
    RegistryEventCollectionMergedCollection as RegistryEventCollectionMergedCollection,
    RegistryEventCollectionRemovedCollection as RegistryEventCollectionRemovedCollection,
    RegistryEventCollectionUpdatedCollection as RegistryEventCollectionUpdatedCollection,
    RegistryEventPropertyCreatedProperty as RegistryEventPropertyCreatedProperty,
    RegistryEventPropertyMergedProperty as RegistryEventPropertyMergedProperty,
    RegistryEventPropertyReactivatedProperty as RegistryEventPropertyReactivatedProperty,
    RegistryEventPropertyStaleProperty as RegistryEventPropertyStaleProperty,
    RegistryEventPropertyUpdatedProperty as RegistryEventPropertyUpdatedProperty,
    RegistryEventPublisherAdagentsChangedPublisher as RegistryEventPublisherAdagentsChangedPublisher,
    RegistryEventPublisherAdagentsDiscoveredPublisher as RegistryEventPublisherAdagentsDiscoveredPublisher,
    StringArray as StringArray,
)
from ._schemas.core.registry_feed_response import (
    RegistryFeedResponse as RegistryFeedResponse,
)
from ._schemas.core.reporting_adjustment import (
    ReportingAdjustment as ReportingAdjustment,
)
from ._schemas.core.reporting_adjustment_receipt import (
    ReportingAdjustmentReceipt as ReportingAdjustmentReceipt,
    ReportingAdjustmentRejectionCode as ReportingAdjustmentRejectionCode,
)
from ._schemas.core.reporting_canonical_content_digest import (
    ReportingCanonicalContentDigest as ReportingCanonicalContentDigest,
)
from ._schemas.core.reporting_canonicalization_contract import (
    ReportingCanonicalizationContract as ReportingCanonicalizationContract,
    ReportingPrimaryKey as ReportingPrimaryKey,
)
from ._schemas.core.reporting_capabilities import (
    ReportingCapabilities as ReportingCapabilities,
)
from ._schemas.core.reporting_consumer_status import (
    ReportingConsumerStatus as ReportingConsumerStatus,
)
from ._schemas.core.reporting_control_total import (
    DecimalReportingControlTotal as DecimalReportingControlTotal,
    IntegerReportingControlTotal as IntegerReportingControlTotal,
    ReportingControlTotal as ReportingControlTotal,
)
from ._schemas.core.reporting_coverage import (
    ReportingCoverage as ReportingCoverage,
    ReportingMediaBuyId as ReportingMediaBuyId,
    ReportingPackageId as ReportingPackageId,
)
from ._schemas.core.reporting_dataset_share_destination import (
    ProvisionRecipient as ProvisionRecipient,
    ReportingCloud as ReportingCloud,
    ReportingDatasetShareDestination as ReportingDatasetShareDestination,
    ReportingDatasetShareDestinationExisting as ReportingDatasetShareDestinationExisting,
)
from ._schemas.core.reporting_delivery_capabilities import (
    ReportingDeliveryCapabilities as ReportingDeliveryCapabilities,
)
from ._schemas.core.reporting_delivery_config import (
    ReportingDeliveryConfiguration as ReportingDeliveryConfiguration,
)
from ._schemas.core.reporting_delivery_config_state import (
    ReportingDeliveryConfigurationState as ReportingDeliveryConfigurationState,
)
from ._schemas.core.reporting_delivery_method import (
    DatasetShare as DatasetShare,
    ReportingDeliveryMethod as ReportingDeliveryMethod,
    ReportingDeliveryMethodFileTransfer as ReportingDeliveryMethodFileTransfer,
    WarehouseMaterialization as WarehouseMaterialization,
)
from ._schemas.core.reporting_delivery_offering import (
    ProducerIdentityProvider as ProducerIdentityProvider,
    ReportingDeliveryOffering as ReportingDeliveryOffering,
)
from ._schemas.core.reporting_delivery_offering_id import (
    ReportingDeliveryOfferingID as ReportingDeliveryOfferingID,
)
from ._schemas.core.reporting_delivery_ready_webhook import (
    ReportingDeliveryReadyWebhook as ReportingDeliveryReadyWebhook,
)
from ._schemas.core.reporting_file_compression import (
    ReportingFileCompression as ReportingFileCompression,
)
from ._schemas.core.reporting_file_entry import (
    ReportingFileEntry as ReportingFileEntry,
)
from ._schemas.core.reporting_file_manifest import (
    ReportingFileManifest as ReportingFileManifest,
)
from ._schemas.core.reporting_file_object_ref import (
    ReportingFileObjectReference as ReportingFileObjectReference,
)
from ._schemas.core.reporting_ledger_changed_webhook import (
    ReportingLedgerChangedWebhook as ReportingLedgerChangedWebhook,
)
from ._schemas.core.reporting_materialization import (
    ReportingMaterialization as ReportingMaterialization,
)
from ._schemas.core.reporting_native_version_ref import (
    ReportingNativeVersionReference as ReportingNativeVersionReference,
)
from ._schemas.core.reporting_obligation import (
    ReportingObligation as ReportingObligation,
)
from ._schemas.core.reporting_receipt import (
    ReportingReceipt as ReportingReceipt,
)
from ._schemas.core.reporting_reconciliation_mode import (
    ReportingReconciliationMode as ReportingReconciliationMode,
)
from ._schemas.core.reporting_reliability_statistics import (
    ReportingReliabilityStatistics as ReportingReliabilityStatistics,
)
from ._schemas.core.reporting_report_definition import (
    FinalityPoliciesItemContractualCutoff as FinalityPoliciesItemContractualCutoff,
    FinalityPoliciesItemSourceFinal as FinalityPoliciesItemSourceFinal,
    FinalityPoliciesItemStabilized as FinalityPoliciesItemStabilized,
    ReportingReportDefinition as ReportingReportDefinition,
)
from ._schemas.core.reporting_resource import (
    ReportingReaderCompatibilityItem as ReportingReaderCompatibilityItem,
    ReportingResource as ReportingResource,
)
from ._schemas.core.reporting_revision import (
    ReportingRevision as ReportingRevision,
)
from ._schemas.core.reporting_schedule import (
    ReportingSchedule as ReportingSchedule,
)
from ._schemas.core.reporting_schedule_offering import (
    ReportingScheduleOffering as ReportingScheduleOffering,
)
from ._schemas.core.reporting_status_changed_webhook import (
    ReportingStatusChangedWebhook as ReportingStatusChangedWebhook,
)
from ._schemas.core.reporting_status_issue import (
    ReportingStatusIssue as ReportingStatusIssue,
)
from ._schemas.core.reporting_verification import (
    ReportingVerification as ReportingVerification,
    SHA256PhysicalChecksum as SHA256PhysicalChecksum,
    SHA512PhysicalChecksum as SHA512PhysicalChecksum,
)
from ._schemas.core.reporting_verification_profile import (
    ReportingVerificationProfile as ReportingVerificationProfile,
)
from ._schemas.core.reporting_verification_profile_set import (
    ReportingVerificationProfileSet as ReportingVerificationProfileSet,
)
from ._schemas.core.reporting_webhook import (
    ReportingWebhook as ReportingWebhook,
)
from ._schemas.core.reporting_write_destination import (
    ProvisionBinding as ProvisionBinding,
    ReportingWriteDestination as ReportingWriteDestination,
    ReportingWriteDestinationExisting as ReportingWriteDestinationExisting,
)
from ._schemas.core.representation_destination import (
    RepresentationDestination as RepresentationDestination,
)
from ._schemas.core.representation_rejection import (
    RepresentationRejection as RepresentationRejection,
)
from ._schemas.core.representation_selection import (
    RepresentationSelection as RepresentationSelection,
)
from ._schemas.core.requirements.asset_requirements import (
    AssetRequirements as AssetRequirements,
    AssetRequirementsAudio as AssetRequirementsAudio,
    AssetRequirementsCSS as AssetRequirementsCSS,
    AssetRequirementsDAAST as AssetRequirementsDAAST,
    AssetRequirementsHTML as AssetRequirementsHTML,
    AssetRequirementsImage as AssetRequirementsImage,
    AssetRequirementsJavaScript as AssetRequirementsJavaScript,
    AssetRequirementsMarkdown as AssetRequirementsMarkdown,
    AssetRequirementsText as AssetRequirementsText,
    AssetRequirementsURL as AssetRequirementsURL,
    AssetRequirementsVAST as AssetRequirementsVAST,
    AssetRequirementsVideo as AssetRequirementsVideo,
    AssetRequirementsWebhook as AssetRequirementsWebhook,
)
from ._schemas.core.requirements.audio_asset_requirements import (
    AudioAssetRequirements as AudioAssetRequirements,
)
from ._schemas.core.requirements.catalog_field_binding import (
    CatalogFieldBinding as CatalogFieldBinding,
    CatalogFieldBindingAssetPool as CatalogFieldBindingAssetPool,
    CatalogFieldBindingCatalogGroup as CatalogFieldBindingCatalogGroup,
    CatalogFieldBindingScalar as CatalogFieldBindingScalar,
)
from ._schemas.core.requirements.catalog_requirements import (
    CatalogRequirements as CatalogRequirements,
)
from ._schemas.core.requirements.css_asset_requirements import (
    CSSAssetRequirements as CSSAssetRequirements,
)
from ._schemas.core.requirements.daast_asset_requirements import (
    DAASTAssetRequirements as DAASTAssetRequirements,
)
from ._schemas.core.requirements.html_asset_requirements import (
    HTMLAssetRequirements as HTMLAssetRequirements,
)
from ._schemas.core.requirements.image_asset_requirements import (
    BleedBottomLeftRightTop as BleedBottomLeftRightTop,
    BleedUniform as BleedUniform,
    ImageAssetRequirements as ImageAssetRequirements,
)
from ._schemas.core.requirements.javascript_asset_requirements import (
    JavaScriptAssetRequirements as JavaScriptAssetRequirements,
)
from ._schemas.core.requirements.markdown_asset_requirements import (
    MarkdownAssetRequirements as MarkdownAssetRequirements,
)
from ._schemas.core.requirements.offering_asset_constraint import (
    OfferingAssetConstraint as OfferingAssetConstraint,
)
from ._schemas.core.requirements.text_asset_requirements import (
    TextAssetRequirements as TextAssetRequirements,
)
from ._schemas.core.requirements.url_asset_requirements import (
    URLAssetRequirements as URLAssetRequirements,
)
from ._schemas.core.requirements.vast_asset_requirements import (
    VASTAssetRequirements as VASTAssetRequirements,
)
from ._schemas.core.requirements.video_asset_requirements import (
    VideoAssetRequirements as VideoAssetRequirements,
)
from ._schemas.core.requirements.webhook_asset_requirements import (
    WebhookAssetRequirements as WebhookAssetRequirements,
)
from ._schemas.core.response import (
    ProtocolResponse as ProtocolResponse,
)
from ._schemas.core.response_payload_jws_envelope import (
    ResponsePayloadJWSEnvelope as ResponsePayloadJWSEnvelope,
)
from ._schemas.core.rights_attestation_evaluation import (
    RightsAttestationEvaluation as RightsAttestationEvaluation,
)
from ._schemas.core.rights_constraint import (
    RightsConstraint as RightsConstraint,
)
from ._schemas.core.seller_agent_ref import (
    SellerAgentReference as SellerAgentReference,
)
from ._schemas.core.signal_coverage_forecast import (
    SignalCoverageForecast as SignalCoverageForecast,
)
from ._schemas.core.signal_definition import (
    SignalDefinition as SignalDefinition,
)
from ._schemas.core.signal_definition_enrichment import (
    LookbackWindow as LookbackWindow,
    SignalDefinitionEnrichment as SignalDefinitionEnrichment,
)
from ._schemas.core.signal_filters import (
    SignalFilters as SignalFilters,
)
from ._schemas.core.signal_id import (
    SignalID as SignalID,
    SignalIDAgent as SignalIDAgent,
    SignalIDCatalog as SignalIDCatalog,
)
from ._schemas.core.signal_listing import (
    SignalListing as SignalListing,
)
from ._schemas.core.signal_modeling_disclosure import (
    SignalModelingDisclosure as SignalModelingDisclosure,
)
from ._schemas.core.signal_pricing import (
    CpmPricing as CpmPricing,
    CustomPricing as CustomPricing,
    FlatFeePricing as FlatFeePricing,
    PerUnitPricing as PerUnitPricing,
    PercentOfMediaPricing as PercentOfMediaPricing,
    VendorPricing as VendorPricing,
)
from ._schemas.core.signal_pricing_option import (
    SignalPricingOption as SignalPricingOption,
)
from ._schemas.core.signal_ref import (
    SignalRef as SignalRef,
    SignalRefDataProvider as SignalRefDataProvider,
    SignalRefProduct as SignalRefProduct,
    SignalRefSignalSource as SignalRefSignalSource,
)
from ._schemas.core.signal_selection_group_rule import (
    SignalSelectionGroupRule as SignalSelectionGroupRule,
)
from ._schemas.core.signal_targeting import (
    SignalTargeting as SignalTargeting,
    SignalTargetingBinary as SignalTargetingBinary,
    SignalTargetingCategorical as SignalTargetingCategorical,
    SignalTargetingNumeric as SignalTargetingNumeric,
)
from ._schemas.core.signal_targeting_expression import (
    SignalTargetingExpression as SignalTargetingExpression,
    SignalTargetingExpressionBinary as SignalTargetingExpressionBinary,
    SignalTargetingExpressionCategorical as SignalTargetingExpressionCategorical,
    SignalTargetingExpressionNumeric as SignalTargetingExpressionNumeric,
)
from ._schemas.core.signal_targeting_rules import (
    SignalTargetingRules as SignalTargetingRules,
)
from ._schemas.core.sla_window import (
    SLAWindow as SLAWindow,
)
from ._schemas.core.special import (
    Special as Special,
)
from ._schemas.core.spot_reporting_capability import (
    SpotReportingCapability as SpotReportingCapability,
)
from ._schemas.core.start_timing import (
    StartTiming as StartTiming,
)
from ._schemas.core.store_item import (
    HoursValue as HoursValue,
    StoreItem as StoreItem,
)
from ._schemas.core.talent import (
    Talent as Talent,
)
from ._schemas.core.targeting import (
    AudienceExclude as AudienceExclude,
    AudienceInclude as AudienceInclude,
    AxeExcludeSegment as AxeExcludeSegment,
    AxeIncludeSegment as AxeIncludeSegment,
    Browser as Browser,
    BrowserExclude as BrowserExclude,
    DaypartTargets as DaypartTargets,
    DevicePlatformExclude as DevicePlatformExclude,
    DeviceTypeExclude as DeviceTypeExclude,
    GeoCountries as GeoCountries,
    GeoCountriesExclude as GeoCountriesExclude,
    GeoMetrosExclude as GeoMetrosExclude,
    GeoPlaces as GeoPlaces,
    GeoPlacesExclude as GeoPlacesExclude,
    GeoPostalAreas as GeoPostalAreas,
    GeoPostalAreasExclude as GeoPostalAreasExclude,
    GeoRegions as GeoRegions,
    GeoRegionsExclude as GeoRegionsExclude,
    StoreCatchments as StoreCatchments,
    TargetingOverlay as TargetingOverlay,
    TargetingOverlayDevicePlatform as TargetingOverlayDevicePlatform,
    TargetingOverlayDeviceType as TargetingOverlayDeviceType,
    TargetingOverlayGeoProximity as TargetingOverlayGeoProximity,
)
from ._schemas.core.targeting_input import (
    TargetingOverlayInput as TargetingOverlayInput,
)
from ._schemas.core.targeting_modification import (
    RemoveTargetingSetValues as RemoveTargetingSetValues,
    ReplaceTargetingValue as ReplaceTargetingValue,
    TargetingModification as TargetingModification,
)
from ._schemas.core.targeting_overlay_requirements import (
    BrowserRequirement as BrowserRequirement,
    BrowserRequirementFamilies as BrowserRequirementFamilies,
    DaypartRequirement as DaypartRequirement,
    DaypartRequirementTimezoneModes as DaypartRequirementTimezoneModes,
    KeywordRequirement as KeywordRequirement,
    KeywordRequirementSupportedMatchTypes as KeywordRequirementSupportedMatchTypes,
    MetroRequirement as MetroRequirement,
    MetroRequirementSystems as MetroRequirementSystems,
    TargetingOverlayRequirements as TargetingOverlayRequirements,
    TargetingOverlayRequirementsDemographicsAge as TargetingOverlayRequirementsDemographicsAge,
    TargetingOverlayRequirementsGeoProximity as TargetingOverlayRequirementsGeoProximity,
    TargetingOverlayRequirementsRequired as TargetingOverlayRequirementsRequired,
)
from ._schemas.core.targeting_overlay_support import (
    BrowserSupport as BrowserSupport,
    BrowserSupportFamilies as BrowserSupportFamilies,
    CountrySupport as CountrySupport,
    CountrySupportMaxValuesPerPackage as CountrySupportMaxValuesPerPackage,
    DaypartSupport as DaypartSupport,
    DaypartSupportTimezoneModes as DaypartSupportTimezoneModes,
    IanaTimezones as IanaTimezones,
    KeywordSupport as KeywordSupport,
    KeywordSupportSupportedMatchTypes as KeywordSupportSupportedMatchTypes,
    MetroSupport as MetroSupport,
    MetroSupportSystems as MetroSupportSystems,
    Supported as Supported,
    TargetingOverlaySupport as TargetingOverlaySupport,
    TargetingOverlaySupportDemographicsAge as TargetingOverlaySupportDemographicsAge,
    TargetingOverlaySupportGeoProximity as TargetingOverlaySupportGeoProximity,
    TargetingOverlaySupportPlacementSelection as TargetingOverlaySupportPlacementSelection,
)
from ._schemas.core.targeting_unknown_age_eligibility_constraint import (
    TargetingUnknownAgeEligibilityConstraint as TargetingUnknownAgeEligibilityConstraint,
)
from ._schemas.core.targeting_verified_age_basis_constraint import (
    TargetingVerifiedAgeBasisConstraint as TargetingVerifiedAgeBasisConstraint,
)
from ._schemas.core.tasks_get_request import (
    TasksGetRequest as TasksGetRequest,
)
from ._schemas.core.tasks_get_response import (
    TasksGetResponse as TasksGetResponse,
)
from ._schemas.core.tasks_list_request import (
    TasksListRequest as TasksListRequest,
)
from ._schemas.core.tasks_list_response import (
    TasksListResponse as TasksListResponse,
)
from ._schemas.core.tracker_execution_contract import (
    TrackerExecutionContract as TrackerExecutionContract,
)
from ._schemas.core.tracker_execution_selector import (
    TrackerExecutionSelector as TrackerExecutionSelector,
    TrackerExecutionSelectorDaastTracker as TrackerExecutionSelectorDaastTracker,
    TrackerExecutionSelectorPixelTrackerImg as TrackerExecutionSelectorPixelTrackerImg,
    TrackerExecutionSelectorVastTracker as TrackerExecutionSelectorVastTracker,
)
from ._schemas.core.transformer import (
    Transformer as Transformer,
)
from ._schemas.core.transformer_param import (
    TransformerParam as TransformerParam,
)
from ._schemas.core.truncation_sentinel import (
    TruncationSentinel as TruncationSentinel,
)
from ._schemas.core.user_match import (
    UserMatch as UserMatch,
)
from ._schemas.core.vast_media_file_requirements import (
    VASTMediaFileRequirements as VASTMediaFileRequirements,
)
from ._schemas.core.vast_tracker_constraints import (
    VASTTrackerConstraints as VASTTrackerConstraints,
    VastOffset as VastOffset,
    VastVersions as VastVersions,
)
from ._schemas.core.vehicle_item import (
    VehicleItem as VehicleItem,
)
from ._schemas.core.vendor_metric_id import (
    VendorMetricID as VendorMetricID,
)
from ._schemas.core.vendor_metric_optimization import (
    VendorMetricOptimization as VendorMetricOptimization,
)
from ._schemas.core.vendor_metric_optimization_supported_metric import (
    VendorMetricOptimizationSupportedMetric as VendorMetricOptimizationSupportedMetric,
)
from ._schemas.core.vendor_metric_value import (
    VendorMetricValue as VendorMetricValue,
)
from ._schemas.core.vendor_pricing_option import (
    VendorPricingOption as VendorPricingOption,
    VendorPricingOptionCpm as VendorPricingOptionCpm,
    VendorPricingOptionCustom as VendorPricingOptionCustom,
    VendorPricingOptionFlatFee as VendorPricingOptionFlatFee,
    VendorPricingOptionPerUnit as VendorPricingOptionPerUnit,
    VendorPricingOptionPercentOfMedia as VendorPricingOptionPercentOfMedia,
)
from ._schemas.core.verification_token_claims import (
    AgenticAdvertisingOrgVerificationTokenClaims as AgenticAdvertisingOrgVerificationTokenClaims,
    VerificationTokenGradingProfile as VerificationTokenGradingProfile,
)
from ._schemas.core.version_envelope import (
    AdCPVersionEnvelope as AdCPVersionEnvelope,
    AdcpMajorVersion as AdcpMajorVersion,
    AdcpVersion as AdcpVersion,
)
from ._schemas.core.warning import (
    Warning as Warning,
)
from ._schemas.core.warning_resource import (
    WarningAffectedResource as WarningAffectedResource,
)
from ._schemas.core.webhook_activity_record import (
    WebhookActivityRecord as WebhookActivityRecord,
)
from ._schemas.core.webhook_challenge import (
    WebhookChallenge as WebhookChallenge,
)
from ._schemas.core.webhook_challenge_response import (
    WebhookChallengeResponse as WebhookChallengeResponse,
)
from ._schemas.core.wholesale_feed_event import (
    AppliesTo as AppliesTo,
    AppliesToAccount as AppliesToAccount,
    AppliesToPublic as AppliesToPublic,
    WholesaleFeedEvent as WholesaleFeedEvent,
    WholesaleFeedEventProductCreatedProduct as WholesaleFeedEventProductCreatedProduct,
    WholesaleFeedEventProductPricedProduct as WholesaleFeedEventProductPricedProduct,
    WholesaleFeedEventProductRemovedProduct as WholesaleFeedEventProductRemovedProduct,
    WholesaleFeedEventProductUpdatedProduct as WholesaleFeedEventProductUpdatedProduct,
    WholesaleFeedEventSignalCreatedSignal as WholesaleFeedEventSignalCreatedSignal,
    WholesaleFeedEventSignalPricedSignal as WholesaleFeedEventSignalPricedSignal,
    WholesaleFeedEventSignalRemovedSignal as WholesaleFeedEventSignalRemovedSignal,
    WholesaleFeedEventSignalUpdatedSignal as WholesaleFeedEventSignalUpdatedSignal,
    WholesaleFeedEventWholesaleFeedBulkChangeFeed as WholesaleFeedEventWholesaleFeedBulkChangeFeed,
)
from ._schemas.core.wholesale_feed_webhook import (
    WholesaleFeedWebhook as WholesaleFeedWebhook,
)
from ._schemas.core.x_entity_types import (
    XEntityTypes as XEntityTypes,
)

__all__ = [
    'AcceptProposalInputRequired',
    'AcceptProposalSubmitted',
    'AcceptProposalWorking',
    'AcceptancePolicyProfileIDs',
    'AcceptedAttestationIssuersItemAgent',
    'AcceptedAttestationIssuersItemBrand',
    'Account',
    'AccountAuthorization',
    'AccountChange',
    'AccountChangeRecordedWebhook',
    'AccountIdentityChange',
    'AccountIdentityChangeBlocked',
    'AccountIdentityChangePending',
    'AccountIdentityChangePreview',
    'AccountIdentityChangeRejected',
    'AccountIdentityChangeWouldApply',
    'AccountIdentityChangeWouldRequireApproval',
    'AccountReference',
    'AccountReferenceAccountId',
    'AccountReferenceBrandOperator',
    'AccountStatusChangedWebhook',
    'AccountTimezoneCapability',
    'AccountWithAuthorization',
    'ActivationKey',
    'ActivationKeyKeyValue',
    'ActivationKeySegmentId',
    'AdCPAssetGroupVocabularyRegistry',
    'AdCPAsyncResponseData',
    'AdCPAsyncResponseDataBuildCreativeResponse',
    'AdCPAsyncResponseDataCompactTaskInputRequired',
    'AdCPAsyncResponseDataCompactTaskSubmitted',
    'AdCPAsyncResponseDataCompactTaskWorking',
    'AdCPAsyncResponseDataControlMediaBuyResponse',
    'AdCPAsyncResponseDataCreateMediaBuyResponse',
    'AdCPAsyncResponseDataDeclineProposalsResponse',
    'AdCPAsyncResponseDataGetCreativeFeaturesResponse',
    'AdCPAsyncResponseDataGetProductsResponse',
    'AdCPAsyncResponseDataGetSignalsResponse',
    'AdCPAsyncResponseDataMediaBuyCommitmentResponse',
    'AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult',
    'AdCPAsyncResponseDataPreviewCreativeResponse',
    'AdCPAsyncResponseDataRefineProposalsResponse',
    'AdCPAsyncResponseDataRejected',
    'AdCPAsyncResponseDataRequestProposalsResponse',
    'AdCPAsyncResponseDataSyncCatalogsResponse',
    'AdCPAsyncResponseDataSyncCreativesResponse',
    'AdCPAsyncResponseDataUpdateMediaBuyResponse',
    'AdCPAudienceSync',
    'AdCPFormatShapeVocabularyRegistry',
    'AdCPVersionEnvelope',
    'AdInventoryConfiguration',
    'AdcpMajorVersion',
    'AdcpVersion',
    'AgentDeclarations',
    'AgentEncryptionKey',
    'AgentNotificationConfig',
    'AgentNotificationConfigState',
    'AgentPlacementFormatDeclaration',
    'AgentReportingDestination',
    'AgentReportingDestinationState',
    'AgentSigningKey',
    'AgentWebhookChallenge',
    'AgenticAdvertisingOrgVerificationTokenClaims',
    'AppItem',
    'ApplicablePackageID',
    'AppliesTo',
    'AppliesToAccount',
    'AppliesToPublic',
    'AssetRequirements',
    'AssetRequirementsAudio',
    'AssetRequirementsCSS',
    'AssetRequirementsDAAST',
    'AssetRequirementsHTML',
    'AssetRequirementsImage',
    'AssetRequirementsJavaScript',
    'AssetRequirementsMarkdown',
    'AssetRequirementsText',
    'AssetRequirementsURL',
    'AssetRequirementsVAST',
    'AssetRequirementsVideo',
    'AssetRequirementsWebhook',
    'AssetVariant',
    'AssetVariantAudio',
    'AssetVariantBrief',
    'AssetVariantCard',
    'AssetVariantCatalog',
    'AssetVariantCss',
    'AssetVariantDaast',
    'AssetVariantDaastTracker',
    'AssetVariantDisplayTag',
    'AssetVariantHtml',
    'AssetVariantImage',
    'AssetVariantJavascript',
    'AssetVariantMarkdown',
    'AssetVariantPixelTracker',
    'AssetVariantPublishedPost',
    'AssetVariantText',
    'AssetVariantUrl',
    'AssetVariantVast',
    'AssetVariantVastTracker',
    'AssetVariantVideo',
    'AssetVariantWebhook',
    'AssetVariantZip',
    'AssetsItemIndividual',
    'AttestationAgentIssuer',
    'AttestationAgentSubject',
    'AttestationBrandIssuer',
    'AttestationBrandSubject',
    'AttestationCapabilities',
    'AttestationCredentialUriLocator',
    'AttestationEvaluation',
    'AttestationIssuer',
    'AttestationIssuerCredentialIdLocator',
    'AttestationOriginIssuer',
    'AttestationReference',
    'AttestationResourceSubject',
    'AttestationSubject',
    'AttributionWindow',
    'AudienceActivationMethod',
    'AudienceActivationMethodFileTransfer',
    'AudienceActivationMethodsItemCleanRoom',
    'AudienceActivationMethodsItemDatasetQuery',
    'AudienceActivationMethodsItemFileTransfer',
    'AudienceActivationMethodsItemPlatformDistribution',
    'AudienceActivationMethodsItemTmpIdentityMatch',
    'AudienceCharacteristic',
    'AudienceEvidence',
    'AudienceEvidencePin',
    'AudienceEvidenceRequirements',
    'AudienceEvidenceSelection',
    'AudienceExclude',
    'AudienceForecastDimension',
    'AudienceInclude',
    'AudienceMember',
    'AudienceSelector',
    'AudienceSelectorDescription',
    'AudienceSelectorSignalBinary',
    'AudienceSelectorSignalCategorical',
    'AudienceSelectorSignalNumeric',
    'AudienceSource',
    'AudioAsset',
    'AudioAssetRequirements',
    'AuthorizedAgentBaseFields',
    'AxeExcludeSegment',
    'AxeIncludeSegment',
    'BiddingPolicy',
    'BiddingPolicyCapability',
    'BleedBottomLeftRightTop',
    'BleedUniform',
    'BlockedImpacts',
    'BrandID',
    'BrandKey',
    'BrandReference',
    'BrandResponseAuthorizationResult',
    'BrandResponseAuthorizationResultTrusted',
    'BrandResponseAuthorizationResultUntrusted',
    'BriefAsset',
    'Browser',
    'BrowserExclude',
    'BrowserRequirement',
    'BrowserRequirementFamilies',
    'BrowserSupport',
    'BrowserSupportFamilies',
    'BudgetAllocation',
    'BudgetAllocationFixed',
    'BudgetAllocationSellerOptimized',
    'BudgetRange',
    'BuildCreativeAsyncInputRequired',
    'BuildCreativeAsyncSubmitted',
    'BuildCreativeAsyncWorking',
    'BuildCreativeInputRequired',
    'BuildCreativeSubmitted',
    'BuildCreativeWorking',
    'BusinessEntity',
    'BuyProductsInputRequired',
    'BuyProductsSubmitted',
    'BuyProductsWorking',
    'CSSAsset',
    'CSSAssetRequirements',
    'CancellationPolicy',
    'CanonicalAccountReference',
    'CanonicalAccountReferenceAccountId',
    'CanonicalAccountReferenceBrandOperator',
    'CanonicalAudienceEvidence',
    'CanonicalAudienceEvidenceSelection',
    'CanonicalBudgetAllocation',
    'CanonicalBudgetAllocationFixed',
    'CanonicalBudgetAllocationSellerOptimized',
    'CanonicalDeliveryForecast',
    'CanonicalForecastPoint',
    'CanonicalForecastVendorMetricValue',
    'CanonicalFormatKind',
    'CanonicalFormatOption',
    'CanonicalMeasurementTerms',
    'CanonicalMediaBuyAction',
    'CanonicalMediaBuyActionControlMediaBuy',
    'CanonicalMediaBuyActionFields',
    'CanonicalMediaBuyActionRefineProposals',
    'CanonicalMediaBuyActionSyncCreatives',
    'CanonicalMediaBuyFeatures',
    'CanonicalMetricQualifier',
    'CanonicalOptimizationGoal',
    'CanonicalOptimizationGoalEvent',
    'CanonicalOptimizationGoalMetric',
    'CanonicalOptimizationGoalVendorMetric',
    'CanonicalOptimizationGoalVendorMetricTarget',
    'CanonicalPerformanceStandard',
    'CanonicalPricingOption',
    'CanonicalProduct',
    'CanonicalProductAction',
    'CanonicalProductPlacement',
    'CanonicalProductPlacementPublisherRef',
    'CanonicalProductPlacementSellerInline',
    'CanonicalProjectionReference',
    'CanonicalProjectionSlotOverride',
    'CanonicalProposal',
    'CanonicalReportingCapabilities',
    'CanonicalReportingCommitment',
    'CanonicalReportingCommitmentStandard',
    'CanonicalReportingCommitmentVendor',
    'CanvasConstraint',
    'CapabilitiesChangedWebhook',
    'CardAsset',
    'Catalog',
    'CatalogAsset',
    'CatalogExecutionRequirement',
    'CatalogFieldBinding',
    'CatalogFieldBindingAssetPool',
    'CatalogFieldBindingCatalogGroup',
    'CatalogFieldBindingScalar',
    'CatalogFieldMapping',
    'CatalogItemAvailabilityError',
    'CatalogItemAvailabilityReference',
    'CatalogItemAvailabilityState',
    'CatalogItemAvailabilityUpdate',
    'CatalogItemAvailabilityUpdateResult',
    'CatalogItemDeliveryMetrics',
    'CatalogItemReferenceNotFoundError',
    'CatalogRequirements',
    'CatalogSelection',
    'Catchment',
    'Category',
    'ChangedFields',
    'CleanRoom',
    'Collection',
    'CollectionDeliveryMetrics',
    'CollectionDistribution',
    'CollectionListApplication',
    'CollectionListReference',
    'CollectionPropertyDeliveryMetrics',
    'CollectionReference',
    'CollectionSelection',
    'CollectionSelector',
    'Color',
    'CommittedMetric',
    'CommittedMetricStandard',
    'CommittedMetricVendor',
    'CompactTaskInputRequired',
    'CompactTaskSubmitted',
    'CompactTaskWorking',
    'ContentRating',
    'ContextObject',
    'ControlMediaBuyInputRequired',
    'ControlMediaBuySubmitted',
    'ControlMediaBuyWorking',
    'CoordinatedPlacementsFormatDeclaration',
    'Countries',
    'CountrySupport',
    'CountrySupportMaxValuesPerPackage',
    'CpmPricing',
    'CreateMediaBuyAsyncInputRequired',
    'CreateMediaBuyAsyncSubmitted',
    'CreateMediaBuyAsyncWorking',
    'CreateMediaBuyInputRequired',
    'CreateMediaBuySubmitted',
    'CreateMediaBuyWorking',
    'CreativeAsset',
    'CreativeAssets',
    'CreativeAssignment',
    'CreativeBrief',
    'CreativeConsumption',
    'CreativeDeliveryMetrics',
    'CreativeFilters',
    'CreativeItem',
    'CreativeItemMedia',
    'CreativeItemText',
    'CreativeLocalePolicy',
    'CreativeLocalization',
    'CreativeLocalizationReadback',
    'CreativeManifest',
    'CreativeOperationFormatDeclaration',
    'CreativePolicy',
    'CreativeRepresentation',
    'CreativeRepresentationSet',
    'CreativeRevisionID',
    'CreativeVariable',
    'CreativeVariant',
    'CustomFormatDeclaration',
    'CustomPricing',
    'DAASTAsset',
    'DAASTAssetInline',
    'DAASTAssetRequirements',
    'DAASTAssetUrl',
    'DAASTAudioFormatDeclaration',
    'DAASTTrackerAsset',
    'DAASTTrackerConstraints',
    'DAASTTrackerConstraintsDaastTarget',
    'DaastOffset',
    'DaastVersions',
    'DataProviderSignalSelector',
    'DataProviderSignalSelectorAll',
    'DataProviderSignalSelectorById',
    'DataProviderSignalSelectorByTag',
    'Dataset',
    'DatasetQuery',
    'DatasetShare',
    'DatasetShareRecipient',
    'DateRange',
    'DatetimeRange',
    'DaypartRequirement',
    'DaypartRequirementTimezoneModes',
    'DaypartSupport',
    'DaypartSupportTimezoneModes',
    'DaypartTarget',
    'DaypartTargets',
    'DeadlinePolicy',
    'DecimalReportingControlTotal',
    'DeclineProposalsInputRequired',
    'DeclineProposalsSubmitted',
    'DeclineProposalsWorking',
    'DeliveryBreakdownControls',
    'DeliveryForecast',
    'DeliveryMetricAggregate',
    'DeliveryMetricAggregateStandard',
    'DeliveryMetricAggregateVendor',
    'DeliveryMetrics',
    'DeliveryProvider',
    'DeliveryRecipient',
    'DemographicAgeRange',
    'DemographicPredicate',
    'DemographicReportingCapability',
    'DemographicTargetingCapability',
    'DemographicTargetingIntent',
    'DemographicTargetingResolution',
    'Deployment',
    'DeploymentAgent',
    'DeploymentPlatform',
    'Destination',
    'DestinationAgent',
    'DestinationItem',
    'DestinationPlatform',
    'DevicePlatformExclude',
    'DevicePlatformForecastDimension',
    'DeviceTypeExclude',
    'DeviceTypeForecastDimension',
    'DiagnosticIssue',
    'DisplayTagAsset',
    'DisplayTagFormatDeclaration',
    'Domain',
    'DownstreamConnectionExecutionRequirement',
    'DownstreamConnectionRequirement',
    'Duration',
    'EducationItem',
    'Error',
    'EvaluatorSpec',
    'EvaluatorSpecAgentUrl',
    'EvaluatorSpecEvaluatorId',
    'EvaluatorSpecExemplars',
    'Event',
    'EventCustomData',
    'EventSourceExecutionRequirement',
    'EventSourceHealth',
    'EventSurface',
    'ExecutionContinuousBounds',
    'ExecutionEnumeratedIntervals',
    'ExecutionSignals',
    'ExperimentalFeatureID',
    'ExtensionObject',
    'FeatureRequirement',
    'FileTransferDestination',
    'FinalityPoliciesItemContractualCutoff',
    'FinalityPoliciesItemSourceFinal',
    'FinalityPoliciesItemStabilized',
    'FlatFeePricing',
    'FlightItem',
    'ForecastPoint',
    'ForecastPointDimensions',
    'ForecastRange',
    'ForecastRateRange',
    'ForecastVendorMetricValue',
    'Format',
    'FormatOptionReference',
    'FormatOptionsItemFormatOptionId',
    'FormatReferenceStructuredObject',
    'FrequencyCap',
    'FrequencyCapConstraints',
    'FrequencyCapDurationUnit',
    'FrequencyCapImpressionConstraints',
    'FrequencyCapIntervalConstraints',
    'FrequencyCapRequirements',
    'GenerationCredential',
    'GeoCountries',
    'GeoCountriesExclude',
    'GeoDeliveryMetrics',
    'GeoForecastDimension',
    'GeoMetro',
    'GeoMetrosExclude',
    'GeoPlaces',
    'GeoPlacesExclude',
    'GeoPostalAreas',
    'GeoPostalAreasExclude',
    'GeoRegions',
    'GeoRegionsExclude',
    'GeographicBreakdownSupport',
    'GeographicPlaceArea',
    'GeographicPlaceCatalogCapability',
    'GeographicPlaceCatalogEntry',
    'GeographicPlaceIdentifierSystem',
    'GeographicPlaceRequirement',
    'GeographicPlaceResolver',
    'GeographicPlaceSystemSupport',
    'GeographicPlaceType',
    'GeographicRegionRequirement',
    'GeographicRegionRequirementCountriesValueAllValues',
    'GeographicRegionRequirementCountriesValueValues',
    'GeographicRegionSupport',
    'GeographicRegionSupportCountriesValueAllValues',
    'GeographicRegionSupportCountriesValueValues',
    'GetCreativeFeaturesAsyncSubmitted',
    'GetCreativeFeaturesSubmitted',
    'GetGeographicPlaceResolutionRequest',
    'GetGeographicPlaceResolutionResponse',
    'GetProductsAsyncInputRequired',
    'GetProductsAsyncSubmitted',
    'GetProductsAsyncWorking',
    'GetProductsInputRequired',
    'GetProductsSubmitted',
    'GetProductsWorking',
    'GetSignalsAsyncSubmitted',
    'GetSignalsAsyncWorking',
    'GetSignalsSubmitted',
    'GetSignalsWorking',
    'GroupAudioAsset',
    'GroupBriefAsset',
    'GroupCardAsset',
    'GroupCatalogAsset',
    'GroupCssAsset',
    'GroupDaastAsset',
    'GroupDaastTrackerAsset',
    'GroupDisplayTagAsset',
    'GroupHtmlAsset',
    'GroupImageAsset',
    'GroupJavaScriptAsset',
    'GroupMarkdownAsset',
    'GroupPixelTrackerAsset',
    'GroupPublishedPostAsset',
    'GroupTextAsset',
    'GroupUrlAsset',
    'GroupVastAsset',
    'GroupVastTrackerAsset',
    'GroupVideoAsset',
    'GroupWebhookAsset',
    'GroupZipAsset',
    'Gtins',
    'HTML5FormatDeclaration',
    'HTMLAsset',
    'HTMLAssetRequirements',
    'HostedAudioFormatDeclaration',
    'HostedVideoFormatDeclaration',
    'HotelItem',
    'HoursValue',
    'IANATimezoneIdentifier',
    'IanaTimezones',
    'Identifier',
    'Ids',
    'ImageAsset',
    'ImageAssetRequirements',
    'ImageCarouselFormatDeclaration',
    'ImageFormatDeclaration',
    'Impairment',
    'Indicator',
    'IndicatorBearingResourceState',
    'IndicatorScope',
    'IndicatorsChangedWebhook',
    'IndividualAudioAsset',
    'IndividualBriefAsset',
    'IndividualCardAsset',
    'IndividualCatalogAsset',
    'IndividualCssAsset',
    'IndividualDaastAsset',
    'IndividualDaastTrackerAsset',
    'IndividualDisplayTagAsset',
    'IndividualHtmlAsset',
    'IndividualImageAsset',
    'IndividualJavaScriptAsset',
    'IndividualMarkdownAsset',
    'IndividualPixelTrackerAsset',
    'IndividualPublishedPostAsset',
    'IndividualTextAsset',
    'IndividualUrlAsset',
    'IndividualVastAsset',
    'IndividualVastTrackerAsset',
    'IndividualVideoAsset',
    'IndividualWebhookAsset',
    'IndividualZipAsset',
    'IndustryIdentifier',
    'InlineMarkup',
    'InsertionOrder',
    'Installment',
    'InstallmentDeadlines',
    'InstallmentDeliveryMetrics',
    'InstallmentPropertyDeliveryMetrics',
    'InstallmentReference',
    'IntegerReportingControlTotal',
    'InventoryListApplication',
    'JavaScriptAsset',
    'JavaScriptAssetRequirements',
    'JobItem',
    'KeywordDeliveryMetrics',
    'KeywordRequirement',
    'KeywordRequirementSupportedMatchTypes',
    'KeywordSupport',
    'KeywordSupportSupportedMatchTypes',
    'KeywordTarget',
    'LanguageTag',
    'LimitedSeries',
    'LocalizedCreativeAsset',
    'LookbackWindow',
    'MCPWebhookPayload',
    'MacroBearingURL',
    'MacroDeclaration',
    'MacroEncoding',
    'MacroProcessingCapability',
    'MacroResolutionResult',
    'MacroTranslationTarget',
    'MarkdownAsset',
    'MarkdownAssetRequirements',
    'MaterialDeadline',
    'MeasurementReadiness',
    'MeasurementTerms',
    'MeasurementWindow',
    'MediaBuy',
    'MediaBuyAvailableAction',
    'MediaBuyAvailableActionID',
    'MediaBuyChangeTermID',
    'MediaBuyFeatures',
    'MediaBuyFrequencyCap',
    'MediaBuyFrequencyCapCapability',
    'MediaBuyFrequencyCapRequirement',
    'MediaBuyFrequencyCapSupport',
    'MediaBuyTermsReference',
    'MetricStandard',
    'MetricVendor',
    'MetroRequirement',
    'MetroRequirementSystems',
    'MetroSupport',
    'MetroSupportSystems',
    'MissingMetric',
    'MissingMetricStandard',
    'MissingMetricVendor',
    'NativeInFeedFormatDeclaration',
    'NegativeKeyword',
    'NonblockingImpacts',
    'NotificationConfig',
    'Offering',
    'OfferingAssetConstraint',
    'OfferingAssetGroup',
    'OperatorIdentity',
    'OperatorUnit',
    'OpportunityContext',
    'OptimizationGoal',
    'OptimizationGoalEvent',
    'OptimizationGoalEventTargetCostPer',
    'OptimizationGoalMetric',
    'OptimizationGoalMetricTargetCostPer',
    'OptimizationGoalMetricTargetThresholdRate',
    'OptimizationGoalVendorMetric',
    'OptimizationGoalVendorMetricTargetCostPer',
    'OptimizationGoalVendorMetricTargetThresholdRate',
    'OutcomeMeasurement',
    'OutcomeTargetCostPer',
    'Overlay',
    'Package',
    'PackageDeliveryMetricValue',
    'PackageFormatSnapshot',
    'PackageFormatSnapshotAgentPlacement',
    'PackageFormatSnapshotAudioDaast',
    'PackageFormatSnapshotAudioHosted',
    'PackageFormatSnapshotAudioVast',
    'PackageFormatSnapshotCoordinatedPlacements',
    'PackageFormatSnapshotCustom',
    'PackageFormatSnapshotDisplayTag',
    'PackageFormatSnapshotHtml5',
    'PackageFormatSnapshotImage',
    'PackageFormatSnapshotImageCarousel',
    'PackageFormatSnapshotNativeInFeed',
    'PackageFormatSnapshotResponsiveCreative',
    'PackageFormatSnapshotSellerRenderedStatefulDisplay',
    'PackageFormatSnapshotSponsoredPlacement',
    'PackageFormatSnapshotVideoHosted',
    'PackageFormatSnapshotVideoVast',
    'PackageSignalTargeting',
    'PackageSignalTargetingBinary',
    'PackageSignalTargetingCategorical',
    'PackageSignalTargetingGroup',
    'PackageSignalTargetingGroups',
    'PackageSignalTargetingNumeric',
    'PackageTargetingResolution',
    'PaginationRequest',
    'PaginationResponse',
    'PairedRedirect',
    'PerUnitPricing',
    'PercentOfMediaPricing',
    'PerformanceFeedback',
    'PerformanceFeedbackAssertion',
    'PerformanceFeedbackMetric',
    'PerformanceFeedbackMetricStandard',
    'PerformanceFeedbackMetricVendor',
    'PerformanceStandard',
    'PixelTrackerAsset',
    'Placement',
    'PlacementDefinition',
    'PlacementDeliveryMetrics',
    'PlacementEvidence',
    'PlacementForecastDimension',
    'PlacementIdentity',
    'PlacementPresentationDocument',
    'PlacementPresentationReference',
    'PlacementPropertyDeliveryMetrics',
    'PlacementReference',
    'PlacementRefsItem',
    'PlacementSelection',
    'PlannedDelivery',
    'PlatformDistribution',
    'PlatformExtensionReference',
    'PlatformSegment',
    'PositivePostalAreaSupport',
    'PostalArea',
    'PostalAreaAUPostcode',
    'PostalAreaBRCep',
    'PostalAreaBranch9',
    'PostalAreaCA',
    'PostalAreaCountrySystemValues',
    'PostalAreaFRCodePostal',
    'PostalAreaGB',
    'PostalAreaINPin',
    'PostalAreaPlz',
    'PostalAreaSupport',
    'PostalAreaUS',
    'PostalAreaWithFusedSystem',
    'PostalAreaZAPostalCode',
    'PostalCountrySystem',
    'PostalCountrySystemAUPostcode',
    'PostalCountrySystemBRCep',
    'PostalCountrySystemBranch9',
    'PostalCountrySystemCA',
    'PostalCountrySystemFRCodePostal',
    'PostalCountrySystemGB',
    'PostalCountrySystemINPin',
    'PostalCountrySystemPlz',
    'PostalCountrySystemUS',
    'PostalCountrySystemZAPostalCode',
    'PreviewRendererMetadata',
    'Price',
    'PricingCurrenciesItem',
    'PricingOption',
    'PricingOptionCpa',
    'PricingOptionCpc',
    'PricingOptionCpcv',
    'PricingOptionCpm',
    'PricingOptionCpp',
    'PricingOptionCpv',
    'PricingOptionFlatRate',
    'PricingOptionRevenueShare',
    'PricingOptionTime',
    'PricingOptionVcpm',
    'PrincipalChangedWebhook',
    'PrincipalDeclarationsState',
    'PrincipalState',
    'ProducerIdentityProvider',
    'Product',
    'ProductAllocation',
    'ProductAllowedAction',
    'ProductAudienceEvidenceRequirements',
    'ProductCardReferenceAsset',
    'ProductChangeMap',
    'ProductDefaultCollections',
    'ProductDefaultPlacements',
    'ProductExecutionRequirement',
    'ProductFilters',
    'ProductFormatDeclaration',
    'ProductIdentity',
    'ProductLocalFormatOptionReference',
    'ProductMediaBuySupport',
    'ProductMediaBuySupportRequirements',
    'ProductOfferFilters',
    'ProductSignalTargetingOption',
    'ProductTargetingResolution',
    'Property',
    'PropertyDeliveryMetrics',
    'PropertyID',
    'PropertyListApplication',
    'PropertyListReference',
    'PropertyReference',
    'PropertyTag',
    'Proposal',
    'ProtocolEnvelope',
    'ProtocolResponse',
    'Provenance',
    'ProvisionBinding',
    'ProvisionRecipient',
    'PublishedPostAsset',
    'PublisherCatalogFormatOptionReference',
    'PublisherCatalogPlacementIdentity',
    'PublisherDesignatedPreviewProvider',
    'PublisherPropertySelector',
    'PublisherPropertySelectorAll',
    'PublisherPropertySelectorById',
    'PublisherPropertySelectorByTag',
    'PushNotificationConfig',
    'Query',
    'RealEstateItem',
    'ReferenceAsset',
    'ReferenceRenderer',
    'RefineProposalsAsyncSubmitted',
    'RefineProposalsInputRequired',
    'RefineProposalsSubmitted',
    'RefineProposalsWorking',
    'RegistryEvent',
    'RegistryEventAgentComplianceChangedAgent',
    'RegistryEventAgentDiscoveredAgent',
    'RegistryEventAgentProfileUpdatedAgent',
    'RegistryEventAgentRemovedAgent',
    'RegistryEventAgentVerificationEarnedAgent',
    'RegistryEventAgentVerificationLostAgent',
    'RegistryEventAuthorizationGrantedAuthorization',
    'RegistryEventAuthorizationModifiedAuthorization',
    'RegistryEventAuthorizationRevokedAuthorization',
    'RegistryEventCollectionCreatedCollection',
    'RegistryEventCollectionMergedCollection',
    'RegistryEventCollectionRemovedCollection',
    'RegistryEventCollectionUpdatedCollection',
    'RegistryEventPropertyCreatedProperty',
    'RegistryEventPropertyMergedProperty',
    'RegistryEventPropertyReactivatedProperty',
    'RegistryEventPropertyStaleProperty',
    'RegistryEventPropertyUpdatedProperty',
    'RegistryEventPublisherAdagentsChangedPublisher',
    'RegistryEventPublisherAdagentsDiscoveredPublisher',
    'RegistryFeedResponse',
    'RemoveTargetingSetValues',
    'RendersItemDimensions',
    'RendersItemParametersFromFormatId',
    'RepeatableGroupAsset',
    'ReplaceTargetingValue',
    'ReportingAdjustment',
    'ReportingAdjustmentReceipt',
    'ReportingAdjustmentRejectionCode',
    'ReportingCanonicalContentDigest',
    'ReportingCanonicalizationContract',
    'ReportingCapabilities',
    'ReportingCloud',
    'ReportingConsumerStatus',
    'ReportingControlTotal',
    'ReportingCoverage',
    'ReportingDatasetShareDestination',
    'ReportingDatasetShareDestinationExisting',
    'ReportingDeliveryCapabilities',
    'ReportingDeliveryConfiguration',
    'ReportingDeliveryConfigurationState',
    'ReportingDeliveryMethod',
    'ReportingDeliveryMethodFileTransfer',
    'ReportingDeliveryOffering',
    'ReportingDeliveryOfferingID',
    'ReportingDeliveryReadyWebhook',
    'ReportingFileCompression',
    'ReportingFileEntry',
    'ReportingFileManifest',
    'ReportingFileObjectReference',
    'ReportingLedgerChangedWebhook',
    'ReportingMaterialization',
    'ReportingMediaBuyId',
    'ReportingNativeVersionReference',
    'ReportingObligation',
    'ReportingPackageId',
    'ReportingPrimaryKey',
    'ReportingReaderCompatibilityItem',
    'ReportingReceipt',
    'ReportingReconciliationMode',
    'ReportingReliabilityStatistics',
    'ReportingReportDefinition',
    'ReportingResource',
    'ReportingRevision',
    'ReportingSchedule',
    'ReportingScheduleOffering',
    'ReportingStatusChangedWebhook',
    'ReportingStatusIssue',
    'ReportingVerification',
    'ReportingVerificationProfile',
    'ReportingVerificationProfileSet',
    'ReportingWebhook',
    'ReportingWriteDestination',
    'ReportingWriteDestinationExisting',
    'RepresentationDestination',
    'RepresentationRejection',
    'RepresentationSelection',
    'RequestProposalsAsyncSubmitted',
    'RequestProposalsInputRequired',
    'RequestProposalsSubmitted',
    'RequestProposalsWorking',
    'ResolvedAssets',
    'ResponsePayloadJWSEnvelope',
    'ResponsiveCreativeFormatDeclaration',
    'RightsAttestationEvaluation',
    'RightsConstraint',
    'SHA256PhysicalChecksum',
    'SHA512PhysicalChecksum',
    'SLAWindow',
    'ScopedCreativeApproval',
    'SelectedCollections',
    'SelectedPlacements',
    'SellerAgentReference',
    'SellerInlinePlacementIdentity',
    'SellerRenderedStatefulDisplayFormatDeclaration',
    'SignalCoverageForecast',
    'SignalDefinition',
    'SignalDefinitionEnrichment',
    'SignalFilters',
    'SignalForecastDimension',
    'SignalID',
    'SignalIDAgent',
    'SignalIDCatalog',
    'SignalListing',
    'SignalModelingDisclosure',
    'SignalPricingOption',
    'SignalRef',
    'SignalRefDataProvider',
    'SignalRefProduct',
    'SignalRefSignalSource',
    'SignalSelectionGroupRule',
    'SignalTargeting',
    'SignalTargetingBinary',
    'SignalTargetingCategorical',
    'SignalTargetingExpression',
    'SignalTargetingExpressionBinary',
    'SignalTargetingExpressionCategorical',
    'SignalTargetingExpressionNumeric',
    'SignalTargetingItemBinary',
    'SignalTargetingItemCategorical',
    'SignalTargetingItemNumeric',
    'SignalTargetingNumeric',
    'SignalTargetingRules',
    'SourceLocalizationReadback',
    'Special',
    'SponsoredPlacementFormatDeclaration',
    'SpotReportingCapability',
    'StandardScope',
    'StartTiming',
    'StoreCatchments',
    'StoreItem',
    'StringArray',
    'Supported',
    'SyncCatalogsAsyncInputRequired',
    'SyncCatalogsAsyncSubmitted',
    'SyncCatalogsAsyncWorking',
    'SyncCatalogsInputRequired',
    'SyncCatalogsSubmitted',
    'SyncCatalogsWorking',
    'SyncCreativesAsyncInputRequired',
    'SyncCreativesAsyncSubmitted',
    'SyncCreativesAsyncWorking',
    'SyncCreativesInputRequired',
    'SyncCreativesSubmitted',
    'SyncCreativesWorking',
    'TMPIdentityMatch',
    'TagURL',
    'Tags',
    'Talent',
    'TargetLocalizationReadback',
    'TargetMaximizeValue',
    'TargetPerAdSpend',
    'TargetingModification',
    'TargetingOverlay',
    'TargetingOverlayDevicePlatform',
    'TargetingOverlayDeviceType',
    'TargetingOverlayGeoProximity',
    'TargetingOverlayInput',
    'TargetingOverlayRequirements',
    'TargetingOverlayRequirementsDemographicsAge',
    'TargetingOverlayRequirementsGeoProximity',
    'TargetingOverlayRequirementsRequired',
    'TargetingOverlaySupport',
    'TargetingOverlaySupportDemographicsAge',
    'TargetingOverlaySupportGeoProximity',
    'TargetingOverlaySupportPlacementSelection',
    'TargetingUnknownAgeEligibilityConstraint',
    'TargetingVerifiedAgeBasisConstraint',
    'TasksGetRequest',
    'TasksGetResponse',
    'TasksListRequest',
    'TasksListResponse',
    'TextAsset',
    'TextAssetRequirements',
    'TimeForecastDimension',
    'TrackerExecutionContract',
    'TrackerExecutionSelector',
    'TrackerExecutionSelectorDaastTracker',
    'TrackerExecutionSelectorPixelTrackerImg',
    'TrackerExecutionSelectorVastTracker',
    'Transformer',
    'TransformerParam',
    'TruncationSentinel',
    'URLAsset',
    'URLAssetRequirements',
    'UpdateMediaBuyAsyncInputRequired',
    'UpdateMediaBuyAsyncSubmitted',
    'UpdateMediaBuyAsyncWorking',
    'UpdateMediaBuyInputRequired',
    'UpdateMediaBuySubmitted',
    'UpdateMediaBuyWorking',
    'UserMatch',
    'VASTAsset',
    'VASTAssetInline',
    'VASTAssetRequirements',
    'VASTAssetUrl',
    'VASTAudioFormatDeclaration',
    'VASTMediaFileRequirements',
    'VASTTrackerAsset',
    'VASTTrackerConstraints',
    'VASTVideoFormatDeclaration',
    'VastOffset',
    'VastVersions',
    'VehicleItem',
    'VendorMetricID',
    'VendorMetricOptimization',
    'VendorMetricOptimizationSupportedMetric',
    'VendorMetricValue',
    'VendorPricing',
    'VendorPricingOption',
    'VendorPricingOptionCpm',
    'VendorPricingOptionCustom',
    'VendorPricingOptionFlatFee',
    'VendorPricingOptionPerUnit',
    'VendorPricingOptionPercentOfMedia',
    'VerificationTokenGradingProfile',
    'VideoAsset',
    'VideoAssetRequirements',
    'WarehouseMaterialization',
    'WarehouseMaterializationDestination',
    'Warning',
    'WarningAffectedResource',
    'WebhookActivityRecord',
    'WebhookAsset',
    'WebhookAssetRequirements',
    'WebhookChallenge',
    'WebhookChallengeResponse',
    'WholesaleFeedEvent',
    'WholesaleFeedEventProductCreatedProduct',
    'WholesaleFeedEventProductPricedProduct',
    'WholesaleFeedEventProductRemovedProduct',
    'WholesaleFeedEventProductUpdatedProduct',
    'WholesaleFeedEventSignalCreatedSignal',
    'WholesaleFeedEventSignalPricedSignal',
    'WholesaleFeedEventSignalRemovedSignal',
    'WholesaleFeedEventSignalUpdatedSignal',
    'WholesaleFeedEventWholesaleFeedBulkChangeFeed',
    'WholesaleFeedWebhook',
    'XEntityTypes',
    'ZipAsset',
]
