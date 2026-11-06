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

from ._schemas.core.acceptance_policy_profile_ids import AcceptancePolicyProfileIDs as AcceptancePolicyProfileIDs
from ._schemas.core.account import Account as Account
from ._schemas.core.account_authorization import AccountAuthorization as AccountAuthorization
from ._schemas.core.account_authorization import StandardScope as StandardScope
from ._schemas.core.account_change import AccountChange as AccountChange
from ._schemas.core.account_change_recorded_webhook import AccountChangeRecordedWebhook as AccountChangeRecordedWebhook
from ._schemas.core.account_identity_change import AccountIdentityChange as AccountIdentityChange
from ._schemas.core.account_identity_change import AccountIdentityChangePending as AccountIdentityChangePending
from ._schemas.core.account_identity_change import AccountIdentityChangeRejected as AccountIdentityChangeRejected
from ._schemas.core.account_identity_change_preview import AccountIdentityChangeBlocked as AccountIdentityChangeBlocked
from ._schemas.core.account_identity_change_preview import AccountIdentityChangePreview as AccountIdentityChangePreview
from ._schemas.core.account_identity_change_preview import (
    AccountIdentityChangeWouldApply as AccountIdentityChangeWouldApply,
)
from ._schemas.core.account_identity_change_preview import (
    AccountIdentityChangeWouldRequireApproval as AccountIdentityChangeWouldRequireApproval,
)
from ._schemas.core.account_identity_change_preview import BlockedImpacts as BlockedImpacts
from ._schemas.core.account_identity_change_preview import NonblockingImpacts as NonblockingImpacts
from ._schemas.core.account_ref import AccountReference as AccountReference
from ._schemas.core.account_ref import AccountReferenceAccountId as AccountReferenceAccountId
from ._schemas.core.account_ref import AccountReferenceBrandOperator as AccountReferenceBrandOperator
from ._schemas.core.account_status_changed_webhook import AccountStatusChangedWebhook as AccountStatusChangedWebhook
from ._schemas.core.account_timezone_capability import AccountTimezoneCapability as AccountTimezoneCapability
from ._schemas.core.account_with_authorization import AccountWithAuthorization as AccountWithAuthorization
from ._schemas.core.activation_key import ActivationKey as ActivationKey
from ._schemas.core.activation_key import ActivationKeyKeyValue as ActivationKeyKeyValue
from ._schemas.core.activation_key import ActivationKeySegmentId as ActivationKeySegmentId
from ._schemas.core.ad_inventory_config import AdInventoryConfiguration as AdInventoryConfiguration
from ._schemas.core.agent_encryption_key import AgentEncryptionKey as AgentEncryptionKey
from ._schemas.core.agent_notification_config import AgentNotificationConfig as AgentNotificationConfig
from ._schemas.core.agent_notification_config_state import AgentNotificationConfigState as AgentNotificationConfigState
from ._schemas.core.agent_reporting_destination import AgentReportingDestination as AgentReportingDestination
from ._schemas.core.agent_reporting_destination import DatasetShareRecipient as DatasetShareRecipient
from ._schemas.core.agent_reporting_destination import FileTransferDestination as FileTransferDestination
from ._schemas.core.agent_reporting_destination import (
    WarehouseMaterializationDestination as WarehouseMaterializationDestination,
)
from ._schemas.core.agent_reporting_destination_state import (
    AgentReportingDestinationState as AgentReportingDestinationState,
)
from ._schemas.core.agent_signing_key import AgentSigningKey as AgentSigningKey
from ._schemas.core.agent_webhook_challenge import AgentWebhookChallenge as AgentWebhookChallenge
from ._schemas.core.app_item import AppItem as AppItem
from ._schemas.core.applicable_package_id import ApplicablePackageID as ApplicablePackageID
from ._schemas.core.asset_group_vocabulary import AdCPAssetGroupVocabularyRegistry as AdCPAssetGroupVocabularyRegistry
from ._schemas.core.assets.asset_union import AssetVariant as AssetVariant
from ._schemas.core.assets.asset_union import AssetVariantAudio as AssetVariantAudio
from ._schemas.core.assets.asset_union import AssetVariantBrief as AssetVariantBrief
from ._schemas.core.assets.asset_union import AssetVariantCard as AssetVariantCard
from ._schemas.core.assets.asset_union import AssetVariantCatalog as AssetVariantCatalog
from ._schemas.core.assets.asset_union import AssetVariantCss as AssetVariantCss
from ._schemas.core.assets.asset_union import AssetVariantDaast as AssetVariantDaast
from ._schemas.core.assets.asset_union import AssetVariantDaastTracker as AssetVariantDaastTracker
from ._schemas.core.assets.asset_union import AssetVariantDisplayTag as AssetVariantDisplayTag
from ._schemas.core.assets.asset_union import AssetVariantHtml as AssetVariantHtml
from ._schemas.core.assets.asset_union import AssetVariantImage as AssetVariantImage
from ._schemas.core.assets.asset_union import AssetVariantJavascript as AssetVariantJavascript
from ._schemas.core.assets.asset_union import AssetVariantMarkdown as AssetVariantMarkdown
from ._schemas.core.assets.asset_union import AssetVariantPixelTracker as AssetVariantPixelTracker
from ._schemas.core.assets.asset_union import AssetVariantPublishedPost as AssetVariantPublishedPost
from ._schemas.core.assets.asset_union import AssetVariantText as AssetVariantText
from ._schemas.core.assets.asset_union import AssetVariantUrl as AssetVariantUrl
from ._schemas.core.assets.asset_union import AssetVariantVast as AssetVariantVast
from ._schemas.core.assets.asset_union import AssetVariantVastTracker as AssetVariantVastTracker
from ._schemas.core.assets.asset_union import AssetVariantVideo as AssetVariantVideo
from ._schemas.core.assets.asset_union import AssetVariantWebhook as AssetVariantWebhook
from ._schemas.core.assets.asset_union import AssetVariantZip as AssetVariantZip
from ._schemas.core.assets.audio_asset import AudioAsset as AudioAsset
from ._schemas.core.assets.brief_asset import BriefAsset as BriefAsset
from ._schemas.core.assets.card_asset import CardAsset as CardAsset
from ._schemas.core.assets.catalog_asset import CatalogAsset as CatalogAsset
from ._schemas.core.assets.css_asset import CSSAsset as CSSAsset
from ._schemas.core.assets.daast_asset import DAASTAsset as DAASTAsset
from ._schemas.core.assets.daast_asset import DAASTAssetInline as DAASTAssetInline
from ._schemas.core.assets.daast_asset import DAASTAssetUrl as DAASTAssetUrl
from ._schemas.core.assets.daast_tracker_asset import DAASTTrackerAsset as DAASTTrackerAsset
from ._schemas.core.assets.display_tag_asset import DisplayTagAsset as DisplayTagAsset
from ._schemas.core.assets.display_tag_asset import InlineMarkup as InlineMarkup
from ._schemas.core.assets.display_tag_asset import PairedRedirect as PairedRedirect
from ._schemas.core.assets.display_tag_asset import TagURL as TagURL
from ._schemas.core.assets.display_tag_asset import TagURLMacroDeclarationsItem as TagURLMacroDeclarationsItem
from ._schemas.core.assets.html_asset import HTMLAsset as HTMLAsset
from ._schemas.core.assets.image_asset import ImageAsset as ImageAsset
from ._schemas.core.assets.javascript_asset import JavaScriptAsset as JavaScriptAsset
from ._schemas.core.assets.markdown_asset import MarkdownAsset as MarkdownAsset
from ._schemas.core.assets.pixel_tracker_asset import PixelTrackerAsset as PixelTrackerAsset
from ._schemas.core.assets.published_post_asset import PublishedPostAsset as PublishedPostAsset
from ._schemas.core.assets.text_asset import TextAsset as TextAsset
from ._schemas.core.assets.url_asset import URLAsset as URLAsset
from ._schemas.core.assets.vast_asset import VASTAsset as VASTAsset
from ._schemas.core.assets.vast_asset import VASTAssetInline as VASTAssetInline
from ._schemas.core.assets.vast_asset import VASTAssetUrl as VASTAssetUrl
from ._schemas.core.assets.vast_tracker_asset import VASTTrackerAsset as VASTTrackerAsset
from ._schemas.core.assets.video_asset import VideoAsset as VideoAsset
from ._schemas.core.assets.webhook_asset import WebhookAsset as WebhookAsset
from ._schemas.core.assets.zip_asset import ZipAsset as ZipAsset
from ._schemas.core.async_response_data import AdCPAsyncResponseData as AdCPAsyncResponseData
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataBuildCreativeResponse as AdCPAsyncResponseDataBuildCreativeResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataCompactTaskInputRequired as AdCPAsyncResponseDataCompactTaskInputRequired,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataCompactTaskSubmitted as AdCPAsyncResponseDataCompactTaskSubmitted,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataCompactTaskWorking as AdCPAsyncResponseDataCompactTaskWorking,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataCreateMediaBuyResponse as AdCPAsyncResponseDataCreateMediaBuyResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataDeclineProposalsResponse as AdCPAsyncResponseDataDeclineProposalsResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataGetCreativeFeaturesResponse as AdCPAsyncResponseDataGetCreativeFeaturesResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataGetProductsResponse as AdCPAsyncResponseDataGetProductsResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataGetSignalsResponse as AdCPAsyncResponseDataGetSignalsResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult as AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataPreviewCreativeResponse as AdCPAsyncResponseDataPreviewCreativeResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataRefineProposalsResponse as AdCPAsyncResponseDataRefineProposalsResponse,
)
from ._schemas.core.async_response_data import AdCPAsyncResponseDataRejected as AdCPAsyncResponseDataRejected
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataRequestProposalsResponse as AdCPAsyncResponseDataRequestProposalsResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataSyncCatalogsResponse as AdCPAsyncResponseDataSyncCatalogsResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataSyncCreativesResponse as AdCPAsyncResponseDataSyncCreativesResponse,
)
from ._schemas.core.async_response_data import (
    AdCPAsyncResponseDataUpdateMediaBuyResponse as AdCPAsyncResponseDataUpdateMediaBuyResponse,
)
from ._schemas.core.async_response_data import BuildCreativeAsyncInputRequired as BuildCreativeAsyncInputRequired
from ._schemas.core.async_response_data import BuildCreativeAsyncSubmitted as BuildCreativeAsyncSubmitted
from ._schemas.core.async_response_data import BuildCreativeAsyncWorking as BuildCreativeAsyncWorking
from ._schemas.core.async_response_data import ControlMediaBuyResponseCompleted as ControlMediaBuyResponseCompleted
from ._schemas.core.async_response_data import ControlMediaBuyResponseFailed as ControlMediaBuyResponseFailed
from ._schemas.core.async_response_data import ControlMediaBuyResponseSubmitted as ControlMediaBuyResponseSubmitted
from ._schemas.core.async_response_data import CreateMediaBuyAsyncInputRequired as CreateMediaBuyAsyncInputRequired
from ._schemas.core.async_response_data import CreateMediaBuyAsyncSubmitted as CreateMediaBuyAsyncSubmitted
from ._schemas.core.async_response_data import CreateMediaBuyAsyncWorking as CreateMediaBuyAsyncWorking
from ._schemas.core.async_response_data import GetCreativeFeaturesAsyncSubmitted as GetCreativeFeaturesAsyncSubmitted
from ._schemas.core.async_response_data import GetProductsAsyncInputRequired as GetProductsAsyncInputRequired
from ._schemas.core.async_response_data import GetProductsAsyncSubmitted as GetProductsAsyncSubmitted
from ._schemas.core.async_response_data import GetProductsAsyncWorking as GetProductsAsyncWorking
from ._schemas.core.async_response_data import GetSignalsAsyncSubmitted as GetSignalsAsyncSubmitted
from ._schemas.core.async_response_data import GetSignalsAsyncWorking as GetSignalsAsyncWorking
from ._schemas.core.async_response_data import (
    MediaBuyCommitmentResponseCompleted as MediaBuyCommitmentResponseCompleted,
)
from ._schemas.core.async_response_data import MediaBuyCommitmentResponseFailed as MediaBuyCommitmentResponseFailed
from ._schemas.core.async_response_data import (
    MediaBuyCommitmentResponseSubmitted as MediaBuyCommitmentResponseSubmitted,
)
from ._schemas.core.async_response_data import RefineProposalsAsyncSubmitted as RefineProposalsAsyncSubmitted
from ._schemas.core.async_response_data import RequestProposalsAsyncSubmitted as RequestProposalsAsyncSubmitted
from ._schemas.core.async_response_data import SyncCatalogsAsyncInputRequired as SyncCatalogsAsyncInputRequired
from ._schemas.core.async_response_data import SyncCatalogsAsyncSubmitted as SyncCatalogsAsyncSubmitted
from ._schemas.core.async_response_data import SyncCatalogsAsyncWorking as SyncCatalogsAsyncWorking
from ._schemas.core.async_response_data import SyncCreativesAsyncInputRequired as SyncCreativesAsyncInputRequired
from ._schemas.core.async_response_data import SyncCreativesAsyncSubmitted as SyncCreativesAsyncSubmitted
from ._schemas.core.async_response_data import SyncCreativesAsyncWorking as SyncCreativesAsyncWorking
from ._schemas.core.async_response_data import UpdateMediaBuyAsyncInputRequired as UpdateMediaBuyAsyncInputRequired
from ._schemas.core.async_response_data import UpdateMediaBuyAsyncSubmitted as UpdateMediaBuyAsyncSubmitted
from ._schemas.core.async_response_data import UpdateMediaBuyAsyncWorking as UpdateMediaBuyAsyncWorking
from ._schemas.core.attestation_capabilities import AttestationCapabilities as AttestationCapabilities
from ._schemas.core.attestation_evaluation import AttestationEvaluation as AttestationEvaluation
from ._schemas.core.attestation_issuer import AttestationAgentIssuer as AttestationAgentIssuer
from ._schemas.core.attestation_issuer import AttestationBrandIssuer as AttestationBrandIssuer
from ._schemas.core.attestation_issuer import AttestationIssuer as AttestationIssuer
from ._schemas.core.attestation_issuer import AttestationOriginIssuer as AttestationOriginIssuer
from ._schemas.core.attestation_reference import AttestationCredentialUriLocator as AttestationCredentialUriLocator
from ._schemas.core.attestation_reference import (
    AttestationIssuerCredentialIdLocator as AttestationIssuerCredentialIdLocator,
)
from ._schemas.core.attestation_reference import AttestationReference as AttestationReference
from ._schemas.core.attestation_subject import AttestationAgentSubject as AttestationAgentSubject
from ._schemas.core.attestation_subject import AttestationBrandSubject as AttestationBrandSubject
from ._schemas.core.attestation_subject import AttestationResourceSubject as AttestationResourceSubject
from ._schemas.core.attestation_subject import AttestationSubject as AttestationSubject
from ._schemas.core.attribution_window import AttributionWindow as AttributionWindow
from ._schemas.core.audience_activation_method import AdCPAudienceSync as AdCPAudienceSync
from ._schemas.core.audience_activation_method import AudienceActivationMethod as AudienceActivationMethod
from ._schemas.core.audience_activation_method import (
    AudienceActivationMethodFileTransfer as AudienceActivationMethodFileTransfer,
)
from ._schemas.core.audience_activation_method import CleanRoom as CleanRoom
from ._schemas.core.audience_activation_method import DatasetQuery as DatasetQuery
from ._schemas.core.audience_activation_method import PlatformDistribution as PlatformDistribution
from ._schemas.core.audience_activation_method import TMPIdentityMatch as TMPIdentityMatch
from ._schemas.core.audience_characteristic import AudienceCharacteristic as AudienceCharacteristic
from ._schemas.core.audience_evidence import AudienceEvidence as AudienceEvidence
from ._schemas.core.audience_evidence_pin import AudienceEvidencePin as AudienceEvidencePin
from ._schemas.core.audience_evidence_requirements import AudienceEvidenceRequirements as AudienceEvidenceRequirements
from ._schemas.core.audience_evidence_selection import AudienceEvidenceSelection as AudienceEvidenceSelection
from ._schemas.core.audience_member import AudienceMember as AudienceMember
from ._schemas.core.audience_selector import AudienceSelector as AudienceSelector
from ._schemas.core.audience_selector import AudienceSelectorDescription as AudienceSelectorDescription
from ._schemas.core.audience_selector import AudienceSelectorSignalBinary as AudienceSelectorSignalBinary
from ._schemas.core.audience_selector import AudienceSelectorSignalCategorical as AudienceSelectorSignalCategorical
from ._schemas.core.audience_selector import AudienceSelectorSignalNumeric as AudienceSelectorSignalNumeric
from ._schemas.core.audience_source import AudienceSource as AudienceSource
from ._schemas.core.audience_source import Dataset as Dataset
from ._schemas.core.audience_source import PlatformSegment as PlatformSegment
from ._schemas.core.authorized_agent_base import AuthorizedAgentBaseFields as AuthorizedAgentBaseFields
from ._schemas.core.bidding_policy import BiddingPolicy as BiddingPolicy
from ._schemas.core.bidding_policy_capability import BiddingPolicyCapability as BiddingPolicyCapability
from ._schemas.core.brand_id import BrandID as BrandID
from ._schemas.core.brand_key import BrandKey as BrandKey
from ._schemas.core.brand_ref import BrandReference as BrandReference
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResult as BrandResponseAuthorizationResult,
)
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResultTrusted as BrandResponseAuthorizationResultTrusted,
)
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResultUntrusted as BrandResponseAuthorizationResultUntrusted,
)
from ._schemas.core.budget_allocation import BudgetAllocation as BudgetAllocation
from ._schemas.core.budget_allocation import BudgetAllocationFixed as BudgetAllocationFixed
from ._schemas.core.budget_allocation import BudgetAllocationSellerOptimized as BudgetAllocationSellerOptimized
from ._schemas.core.budget_range import BudgetRange as BudgetRange
from ._schemas.core.business_entity import BusinessEntity as BusinessEntity
from ._schemas.core.cancellation_policy import CancellationPolicy as CancellationPolicy
from ._schemas.core.canonical_account_ref import CanonicalAccountReference as CanonicalAccountReference
from ._schemas.core.canonical_account_ref import (
    CanonicalAccountReferenceAccountId as CanonicalAccountReferenceAccountId,
)
from ._schemas.core.canonical_account_ref import (
    CanonicalAccountReferenceBrandOperator as CanonicalAccountReferenceBrandOperator,
)
from ._schemas.core.canonical_audience_evidence import CanonicalAudienceEvidence as CanonicalAudienceEvidence
from ._schemas.core.canonical_audience_evidence_selection import (
    CanonicalAudienceEvidenceSelection as CanonicalAudienceEvidenceSelection,
)
from ._schemas.core.canonical_budget_allocation import CanonicalBudgetAllocation as CanonicalBudgetAllocation
from ._schemas.core.canonical_budget_allocation import CanonicalBudgetAllocationFixed as CanonicalBudgetAllocationFixed
from ._schemas.core.canonical_budget_allocation import (
    CanonicalBudgetAllocationSellerOptimized as CanonicalBudgetAllocationSellerOptimized,
)
from ._schemas.core.canonical_delivery_forecast import CanonicalDeliveryForecast as CanonicalDeliveryForecast
from ._schemas.core.canonical_forecast_point import CanonicalForecastPoint as CanonicalForecastPoint
from ._schemas.core.canonical_forecast_vendor_metric_value import (
    CanonicalForecastVendorMetricValue as CanonicalForecastVendorMetricValue,
)
from ._schemas.core.canonical_format_kind import CanonicalFormatKind as CanonicalFormatKind
from ._schemas.core.canonical_format_option import CanonicalFormatOption as CanonicalFormatOption
from ._schemas.core.canonical_measurement_terms import CanonicalMeasurementTerms as CanonicalMeasurementTerms
from ._schemas.core.canonical_media_buy_action import CanonicalMediaBuyAction as CanonicalMediaBuyAction
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionControlMediaBuy as CanonicalMediaBuyActionControlMediaBuy,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionRefineProposals as CanonicalMediaBuyActionRefineProposals,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionSyncCreatives as CanonicalMediaBuyActionSyncCreatives,
)
from ._schemas.core.canonical_media_buy_action_fields import (
    CanonicalMediaBuyActionFields as CanonicalMediaBuyActionFields,
)
from ._schemas.core.canonical_media_buy_features import CanonicalMediaBuyFeatures as CanonicalMediaBuyFeatures
from ._schemas.core.canonical_metric_qualifier import CanonicalMetricQualifier as CanonicalMetricQualifier
from ._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoal as CanonicalOptimizationGoal
from ._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoalEvent as CanonicalOptimizationGoalEvent
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalMetric as CanonicalOptimizationGoalMetric,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalVendorMetric as CanonicalOptimizationGoalVendorMetric,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalVendorMetricTarget as CanonicalOptimizationGoalVendorMetricTarget,
)
from ._schemas.core.canonical_performance_standard import CanonicalPerformanceStandard as CanonicalPerformanceStandard
from ._schemas.core.canonical_placement import CanonicalProductPlacement as CanonicalProductPlacement
from ._schemas.core.canonical_placement import (
    CanonicalProductPlacementPublisherRef as CanonicalProductPlacementPublisherRef,
)
from ._schemas.core.canonical_placement import (
    CanonicalProductPlacementSellerInline as CanonicalProductPlacementSellerInline,
)
from ._schemas.core.canonical_pricing_option import CanonicalPricingOption as CanonicalPricingOption
from ._schemas.core.canonical_product import CanonicalProduct as CanonicalProduct
from ._schemas.core.canonical_product_action import CanonicalProductAction as CanonicalProductAction
from ._schemas.core.canonical_projection_ref import CanonicalProjectionReference as CanonicalProjectionReference
from ._schemas.core.canonical_projection_slot_override import (
    CanonicalProjectionSlotOverride as CanonicalProjectionSlotOverride,
)
from ._schemas.core.canonical_proposal import CanonicalProposal as CanonicalProposal
from ._schemas.core.canonical_reporting_capabilities import (
    CanonicalReportingCapabilities as CanonicalReportingCapabilities,
)
from ._schemas.core.canonical_reporting_commitment import CanonicalReportingCommitment as CanonicalReportingCommitment
from ._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitmentStandard as CanonicalReportingCommitmentStandard,
)
from ._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitmentVendor as CanonicalReportingCommitmentVendor,
)
from ._schemas.core.canvas_constraint import CanvasConstraint as CanvasConstraint
from ._schemas.core.capabilities_changed_webhook import CapabilitiesChangedWebhook as CapabilitiesChangedWebhook
from ._schemas.core.catalog import Catalog as Catalog
from ._schemas.core.catalog import Category as Category
from ._schemas.core.catalog import Gtins as Gtins
from ._schemas.core.catalog import Ids as Ids
from ._schemas.core.catalog import Query as Query
from ._schemas.core.catalog import Tags as Tags
from ._schemas.core.catalog_field_mapping import CatalogFieldMapping as CatalogFieldMapping
from ._schemas.core.catalog_item_availability_error import CatalogItemAvailabilityError as CatalogItemAvailabilityError
from ._schemas.core.catalog_item_availability_ref import (
    CatalogItemAvailabilityReference as CatalogItemAvailabilityReference,
)
from ._schemas.core.catalog_item_availability_state import CatalogItemAvailabilityState as CatalogItemAvailabilityState
from ._schemas.core.catalog_item_availability_update import (
    CatalogItemAvailabilityUpdate as CatalogItemAvailabilityUpdate,
)
from ._schemas.core.catalog_item_availability_update_result import (
    CatalogItemAvailabilityUpdateResult as CatalogItemAvailabilityUpdateResult,
)
from ._schemas.core.catalog_item_delivery_metrics import CatalogItemDeliveryMetrics as CatalogItemDeliveryMetrics
from ._schemas.core.catalog_item_reference_not_found_error import (
    CatalogItemReferenceNotFoundError as CatalogItemReferenceNotFoundError,
)
from ._schemas.core.catalog_selection import CatalogSelection as CatalogSelection
from ._schemas.core.catchment import Catchment as Catchment
from ._schemas.core.collection import Collection as Collection
from ._schemas.core.collection_delivery_metrics import CollectionDeliveryMetrics as CollectionDeliveryMetrics
from ._schemas.core.collection_distribution import CollectionDistribution as CollectionDistribution
from ._schemas.core.collection_list_ref import CollectionListReference as CollectionListReference
from ._schemas.core.collection_property_delivery_metrics import (
    CollectionPropertyDeliveryMetrics as CollectionPropertyDeliveryMetrics,
)
from ._schemas.core.collection_ref import CollectionReference as CollectionReference
from ._schemas.core.collection_selection import CollectionSelection as CollectionSelection
from ._schemas.core.collection_selection import ProductDefaultCollections as ProductDefaultCollections
from ._schemas.core.collection_selection import SelectedCollections as SelectedCollections
from ._schemas.core.collection_selector import CollectionSelector as CollectionSelector
from ._schemas.core.committed_metric import CommittedMetric as CommittedMetric
from ._schemas.core.committed_metric import CommittedMetricStandard as CommittedMetricStandard
from ._schemas.core.committed_metric import CommittedMetricVendor as CommittedMetricVendor
from ._schemas.core.compact_task_input_required import CompactTaskInputRequired as CompactTaskInputRequired
from ._schemas.core.compact_task_submitted import CompactTaskSubmitted as CompactTaskSubmitted
from ._schemas.core.compact_task_working import CompactTaskWorking as CompactTaskWorking
from ._schemas.core.content_rating import ContentRating as ContentRating
from ._schemas.core.context import ContextObject as ContextObject
from ._schemas.core.country_code import CountryCode as CountryCode
from ._schemas.core.creative_approval_scope import ScopedCreativeApproval as ScopedCreativeApproval
from ._schemas.core.creative_asset import CreativeAsset as CreativeAsset
from ._schemas.core.creative_assets import CreativeAssets as CreativeAssets
from ._schemas.core.creative_assignment import CreativeAssignment as CreativeAssignment
from ._schemas.core.creative_brief import CreativeBrief as CreativeBrief
from ._schemas.core.creative_consumption import CreativeConsumption as CreativeConsumption
from ._schemas.core.creative_delivery_metrics import CreativeDeliveryMetrics as CreativeDeliveryMetrics
from ._schemas.core.creative_filters import CreativeFilters as CreativeFilters
from ._schemas.core.creative_item import CreativeItem as CreativeItem
from ._schemas.core.creative_item import CreativeItemMedia as CreativeItemMedia
from ._schemas.core.creative_item import CreativeItemText as CreativeItemText
from ._schemas.core.creative_locale_policy import CreativeLocalePolicy as CreativeLocalePolicy
from ._schemas.core.creative_localization import CreativeLocalization as CreativeLocalization
from ._schemas.core.creative_localization_readback import CreativeLocalizationReadback as CreativeLocalizationReadback
from ._schemas.core.creative_localization_readback import ResolvedAssets as ResolvedAssets
from ._schemas.core.creative_localization_readback import SourceLocalizationReadback as SourceLocalizationReadback
from ._schemas.core.creative_localization_readback import TargetLocalizationReadback as TargetLocalizationReadback
from ._schemas.core.creative_manifest import CreativeManifest as CreativeManifest
from ._schemas.core.creative_operation_format_declaration import (
    CreativeOperationFormatDeclaration as CreativeOperationFormatDeclaration,
)
from ._schemas.core.creative_policy import CreativePolicy as CreativePolicy
from ._schemas.core.creative_representation import CreativeRepresentation as CreativeRepresentation
from ._schemas.core.creative_representation_set import CreativeRepresentationSet as CreativeRepresentationSet
from ._schemas.core.creative_revision_id import CreativeRevisionID as CreativeRevisionID
from ._schemas.core.creative_variable import CreativeVariable as CreativeVariable
from ._schemas.core.creative_variant import CreativeVariant as CreativeVariant
from ._schemas.core.currency_code import CurrencyCode as CurrencyCode
from ._schemas.core.daast_tracker_constraints import DaastOffset as DaastOffset
from ._schemas.core.daast_tracker_constraints import DAASTTrackerConstraints as DAASTTrackerConstraints
from ._schemas.core.daast_tracker_constraints import (
    DAASTTrackerConstraintsDaastTarget as DAASTTrackerConstraintsDaastTarget,
)
from ._schemas.core.daast_tracker_constraints import DaastVersions as DaastVersions
from ._schemas.core.data_provider_signal_selector import DataProviderSignalSelector as DataProviderSignalSelector
from ._schemas.core.data_provider_signal_selector import DataProviderSignalSelectorAll as DataProviderSignalSelectorAll
from ._schemas.core.data_provider_signal_selector import (
    DataProviderSignalSelectorById as DataProviderSignalSelectorById,
)
from ._schemas.core.data_provider_signal_selector import (
    DataProviderSignalSelectorByTag as DataProviderSignalSelectorByTag,
)
from ._schemas.core.date_range import DateRange as DateRange
from ._schemas.core.datetime_range import DatetimeRange as DatetimeRange
from ._schemas.core.daypart_target import DaypartTarget as DaypartTarget
from ._schemas.core.deadline_policy import DeadlinePolicy as DeadlinePolicy
from ._schemas.core.delivery_breakdown_controls import DeliveryBreakdownControls as DeliveryBreakdownControls
from ._schemas.core.delivery_forecast import DeliveryForecast as DeliveryForecast
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregate as DeliveryMetricAggregate
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregateStandard as DeliveryMetricAggregateStandard
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregateVendor as DeliveryMetricAggregateVendor
from ._schemas.core.delivery_metrics import DeliveryMetrics as DeliveryMetrics
from ._schemas.core.delivery_provider import DeliveryProvider as DeliveryProvider
from ._schemas.core.delivery_recipient import DeliveryRecipient as DeliveryRecipient
from ._schemas.core.demographic_age_range import DemographicAgeRange as DemographicAgeRange
from ._schemas.core.demographic_predicate import DemographicPredicate as DemographicPredicate
from ._schemas.core.demographic_reporting_capability import (
    DemographicReportingCapability as DemographicReportingCapability,
)
from ._schemas.core.demographic_targeting_capability import (
    DemographicTargetingCapability as DemographicTargetingCapability,
)
from ._schemas.core.demographic_targeting_intent import DemographicTargetingIntent as DemographicTargetingIntent
from ._schemas.core.demographic_targeting_resolution import (
    DemographicTargetingResolution as DemographicTargetingResolution,
)
from ._schemas.core.demographic_targeting_resolution import ExecutionContinuousBounds as ExecutionContinuousBounds
from ._schemas.core.demographic_targeting_resolution import ExecutionEnumeratedIntervals as ExecutionEnumeratedIntervals
from ._schemas.core.demographic_targeting_resolution import ExecutionSignals as ExecutionSignals
from ._schemas.core.deployment import Deployment as Deployment
from ._schemas.core.deployment import DeploymentAgent as DeploymentAgent
from ._schemas.core.deployment import DeploymentPlatform as DeploymentPlatform
from ._schemas.core.destination import Destination as Destination
from ._schemas.core.destination import DestinationAgent as DestinationAgent
from ._schemas.core.destination import DestinationPlatform as DestinationPlatform
from ._schemas.core.destination_item import DestinationItem as DestinationItem
from ._schemas.core.diagnostic_issue import DiagnosticIssue as DiagnosticIssue
from ._schemas.core.domain_name import DomainName as DomainName
from ._schemas.core.downstream_connection_requirement import (
    DownstreamConnectionRequirement as DownstreamConnectionRequirement,
)
from ._schemas.core.duration import Duration as Duration
from ._schemas.core.education_item import EducationItem as EducationItem
from ._schemas.core.error import Error as Error
from ._schemas.core.evaluator_spec import EvaluatorSpec as EvaluatorSpec
from ._schemas.core.evaluator_spec import EvaluatorSpecAgentUrl as EvaluatorSpecAgentUrl
from ._schemas.core.evaluator_spec import EvaluatorSpecEvaluatorId as EvaluatorSpecEvaluatorId
from ._schemas.core.evaluator_spec import EvaluatorSpecExemplars as EvaluatorSpecExemplars
from ._schemas.core.event import Event as Event
from ._schemas.core.event_custom_data import EventCustomData as EventCustomData
from ._schemas.core.event_source_health import EventSourceHealth as EventSourceHealth
from ._schemas.core.event_surface import EventSurface as EventSurface
from ._schemas.core.experimental_feature_id import ExperimentalFeatureID as ExperimentalFeatureID
from ._schemas.core.ext import ExtensionObject as ExtensionObject
from ._schemas.core.feature_requirement import FeatureRequirement as FeatureRequirement
from ._schemas.core.flight_item import FlightItem as FlightItem
from ._schemas.core.forecast_dimension_audience import AudienceForecastDimension as AudienceForecastDimension
from ._schemas.core.forecast_dimension_device_platform import (
    DevicePlatformForecastDimension as DevicePlatformForecastDimension,
)
from ._schemas.core.forecast_dimension_device_type import DeviceTypeForecastDimension as DeviceTypeForecastDimension
from ._schemas.core.forecast_dimension_geo import GeoForecastDimension as GeoForecastDimension
from ._schemas.core.forecast_dimension_placement import PlacementForecastDimension as PlacementForecastDimension
from ._schemas.core.forecast_dimension_signal import SignalForecastDimension as SignalForecastDimension
from ._schemas.core.forecast_dimension_time import TimeForecastDimension as TimeForecastDimension
from ._schemas.core.forecast_point import ForecastPoint as ForecastPoint
from ._schemas.core.forecast_point_dimensions import ForecastPointDimensions as ForecastPointDimensions
from ._schemas.core.forecast_range import ForecastRange as ForecastRange
from ._schemas.core.forecast_rate_range import ForecastRateRange as ForecastRateRange
from ._schemas.core.forecast_vendor_metric_value import ForecastVendorMetricValue as ForecastVendorMetricValue
from ._schemas.core.format import AssetsItemIndividual as AssetsItemIndividual
from ._schemas.core.format import Format as Format
from ._schemas.core.format import GroupAudioAsset as GroupAudioAsset
from ._schemas.core.format import GroupBriefAsset as GroupBriefAsset
from ._schemas.core.format import GroupCardAsset as GroupCardAsset
from ._schemas.core.format import GroupCatalogAsset as GroupCatalogAsset
from ._schemas.core.format import GroupCssAsset as GroupCssAsset
from ._schemas.core.format import GroupDaastAsset as GroupDaastAsset
from ._schemas.core.format import GroupDaastTrackerAsset as GroupDaastTrackerAsset
from ._schemas.core.format import GroupDisplayTagAsset as GroupDisplayTagAsset
from ._schemas.core.format import GroupHtmlAsset as GroupHtmlAsset
from ._schemas.core.format import GroupImageAsset as GroupImageAsset
from ._schemas.core.format import GroupJavaScriptAsset as GroupJavaScriptAsset
from ._schemas.core.format import GroupMarkdownAsset as GroupMarkdownAsset
from ._schemas.core.format import GroupPixelTrackerAsset as GroupPixelTrackerAsset
from ._schemas.core.format import GroupPublishedPostAsset as GroupPublishedPostAsset
from ._schemas.core.format import GroupTextAsset as GroupTextAsset
from ._schemas.core.format import GroupUrlAsset as GroupUrlAsset
from ._schemas.core.format import GroupVastAsset as GroupVastAsset
from ._schemas.core.format import GroupVastTrackerAsset as GroupVastTrackerAsset
from ._schemas.core.format import GroupVideoAsset as GroupVideoAsset
from ._schemas.core.format import GroupWebhookAsset as GroupWebhookAsset
from ._schemas.core.format import GroupZipAsset as GroupZipAsset
from ._schemas.core.format import IndividualAudioAsset as IndividualAudioAsset
from ._schemas.core.format import IndividualBriefAsset as IndividualBriefAsset
from ._schemas.core.format import IndividualCardAsset as IndividualCardAsset
from ._schemas.core.format import IndividualCatalogAsset as IndividualCatalogAsset
from ._schemas.core.format import IndividualCssAsset as IndividualCssAsset
from ._schemas.core.format import IndividualDaastAsset as IndividualDaastAsset
from ._schemas.core.format import IndividualDaastTrackerAsset as IndividualDaastTrackerAsset
from ._schemas.core.format import IndividualDisplayTagAsset as IndividualDisplayTagAsset
from ._schemas.core.format import IndividualHtmlAsset as IndividualHtmlAsset
from ._schemas.core.format import IndividualImageAsset as IndividualImageAsset
from ._schemas.core.format import IndividualJavaScriptAsset as IndividualJavaScriptAsset
from ._schemas.core.format import IndividualMarkdownAsset as IndividualMarkdownAsset
from ._schemas.core.format import IndividualPixelTrackerAsset as IndividualPixelTrackerAsset
from ._schemas.core.format import IndividualPublishedPostAsset as IndividualPublishedPostAsset
from ._schemas.core.format import IndividualTextAsset as IndividualTextAsset
from ._schemas.core.format import IndividualUrlAsset as IndividualUrlAsset
from ._schemas.core.format import IndividualVastAsset as IndividualVastAsset
from ._schemas.core.format import IndividualVastTrackerAsset as IndividualVastTrackerAsset
from ._schemas.core.format import IndividualVideoAsset as IndividualVideoAsset
from ._schemas.core.format import IndividualWebhookAsset as IndividualWebhookAsset
from ._schemas.core.format import IndividualZipAsset as IndividualZipAsset
from ._schemas.core.format import RendersItemDimensions as RendersItemDimensions
from ._schemas.core.format import RendersItemParametersFromFormatId as RendersItemParametersFromFormatId
from ._schemas.core.format import RepeatableGroupAsset as RepeatableGroupAsset
from ._schemas.core.format_id import FormatReferenceStructuredObject as FormatReferenceStructuredObject
from ._schemas.core.format_option_ref import FormatOptionReference as FormatOptionReference
from ._schemas.core.format_option_ref import ProductLocalFormatOptionReference as ProductLocalFormatOptionReference
from ._schemas.core.format_option_ref import (
    PublisherCatalogFormatOptionReference as PublisherCatalogFormatOptionReference,
)
from ._schemas.core.format_shape_vocabulary import (
    AdCPFormatShapeVocabularyRegistry as AdCPFormatShapeVocabularyRegistry,
)
from ._schemas.core.frequency_cap import FrequencyCap as FrequencyCap
from ._schemas.core.frequency_cap_constraints import FrequencyCapConstraints as FrequencyCapConstraints
from ._schemas.core.frequency_cap_duration_unit import FrequencyCapDurationUnit as FrequencyCapDurationUnit
from ._schemas.core.frequency_cap_impression_constraints import (
    FrequencyCapImpressionConstraints as FrequencyCapImpressionConstraints,
)
from ._schemas.core.frequency_cap_interval_constraints import (
    FrequencyCapIntervalConstraints as FrequencyCapIntervalConstraints,
)
from ._schemas.core.frequency_cap_requirements import FrequencyCapRequirements as FrequencyCapRequirements
from ._schemas.core.generation_credential import GenerationCredential as GenerationCredential
from ._schemas.core.geo_breakdown_support import GeographicBreakdownSupport as GeographicBreakdownSupport
from ._schemas.core.geo_delivery_metrics import GeoDeliveryMetrics as GeoDeliveryMetrics
from ._schemas.core.geo_metro import GeoMetro as GeoMetro
from ._schemas.core.geo_place_area import GeographicPlaceArea as GeographicPlaceArea
from ._schemas.core.geo_place_catalog_capability import (
    GeographicPlaceCatalogCapability as GeographicPlaceCatalogCapability,
)
from ._schemas.core.geo_place_catalog_entry import GeographicPlaceCatalogEntry as GeographicPlaceCatalogEntry
from ._schemas.core.geo_place_requirement import GeographicPlaceRequirement as GeographicPlaceRequirement
from ._schemas.core.geo_place_resolver import GeographicPlaceResolver as GeographicPlaceResolver
from ._schemas.core.geo_place_support import GeographicPlaceSystemSupport as GeographicPlaceSystemSupport
from ._schemas.core.geo_place_system import GeographicPlaceIdentifierSystem as GeographicPlaceIdentifierSystem
from ._schemas.core.geo_place_type import GeographicPlaceType as GeographicPlaceType
from ._schemas.core.geo_region_requirement import GeographicRegionRequirement as GeographicRegionRequirement
from ._schemas.core.geo_region_support import GeographicRegionSupport as GeographicRegionSupport
from ._schemas.core.geo_region_support import ObjAllValues as ObjAllValues
from ._schemas.core.geo_region_support import ObjValues as ObjValues
from ._schemas.core.get_geo_place_resolution_request import (
    GetGeographicPlaceResolutionRequest as GetGeographicPlaceResolutionRequest,
)
from ._schemas.core.get_geo_place_resolution_response import (
    GetGeographicPlaceResolutionResponse as GetGeographicPlaceResolutionResponse,
)
from ._schemas.core.hotel_item import HotelItem as HotelItem
from ._schemas.core.https_url import HTTPSURL as HTTPSURL
from ._schemas.core.iana_timezone import IANATimezoneIdentifier as IANATimezoneIdentifier
from ._schemas.core.idempotency_key import IdempotencyKey as IdempotencyKey
from ._schemas.core.identifier import Identifier as Identifier
from ._schemas.core.impairment import Impairment as Impairment
from ._schemas.core.indicator import Indicator as Indicator
from ._schemas.core.indicator_bearing import IndicatorBearingResourceState as IndicatorBearingResourceState
from ._schemas.core.indicator_scope import IndicatorScope as IndicatorScope
from ._schemas.core.indicators_changed_webhook import IndicatorsChangedWebhook as IndicatorsChangedWebhook
from ._schemas.core.industry_identifier import IndustryIdentifier as IndustryIdentifier
from ._schemas.core.insertion_order import InsertionOrder as InsertionOrder
from ._schemas.core.installment import Installment as Installment
from ._schemas.core.installment_deadlines import InstallmentDeadlines as InstallmentDeadlines
from ._schemas.core.installment_delivery_metrics import InstallmentDeliveryMetrics as InstallmentDeliveryMetrics
from ._schemas.core.installment_property_delivery_metrics import (
    InstallmentPropertyDeliveryMetrics as InstallmentPropertyDeliveryMetrics,
)
from ._schemas.core.installment_ref import InstallmentReference as InstallmentReference
from ._schemas.core.inventory_list_application import CollectionListApplication as CollectionListApplication
from ._schemas.core.inventory_list_application import InventoryListApplication as InventoryListApplication
from ._schemas.core.inventory_list_application import PropertyListApplication as PropertyListApplication
from ._schemas.core.job_item import JobItem as JobItem
from ._schemas.core.keyword_delivery_metrics import KeywordDeliveryMetrics as KeywordDeliveryMetrics
from ._schemas.core.keyword_target import KeywordTarget as KeywordTarget
from ._schemas.core.limited_series import LimitedSeries as LimitedSeries
from ._schemas.core.locale_tag import LanguageTag as LanguageTag
from ._schemas.core.localized_creative_asset import LocalizedCreativeAsset as LocalizedCreativeAsset
from ._schemas.core.macro_bearing_url import MacroBearingURL as MacroBearingURL
from ._schemas.core.macro_declaration import MacroDeclaration as MacroDeclaration
from ._schemas.core.macro_encoding import MacroEncoding as MacroEncoding
from ._schemas.core.macro_resolution_capability import MacroProcessingCapability as MacroProcessingCapability
from ._schemas.core.macro_resolution_result import MacroResolutionResult as MacroResolutionResult
from ._schemas.core.macro_translation_target import MacroTranslationTarget as MacroTranslationTarget
from ._schemas.core.material_deadline import MaterialDeadline as MaterialDeadline
from ._schemas.core.mcp_webhook_payload import MCPWebhookPayload as MCPWebhookPayload
from ._schemas.core.measurement_readiness import MeasurementReadiness as MeasurementReadiness
from ._schemas.core.measurement_terms import MeasurementTerms as MeasurementTerms
from ._schemas.core.measurement_window import MeasurementWindow as MeasurementWindow
from ._schemas.core.media_buy import MediaBuy as MediaBuy
from ._schemas.core.media_buy_available_action import MediaBuyAvailableAction as MediaBuyAvailableAction
from ._schemas.core.media_buy_available_action_id import MediaBuyAvailableActionID as MediaBuyAvailableActionID
from ._schemas.core.media_buy_change_term_id import MediaBuyChangeTermID as MediaBuyChangeTermID
from ._schemas.core.media_buy_features import MediaBuyFeatures as MediaBuyFeatures
from ._schemas.core.media_buy_frequency_cap import MediaBuyFrequencyCap as MediaBuyFrequencyCap
from ._schemas.core.media_buy_frequency_cap_capability import (
    MediaBuyFrequencyCapCapability as MediaBuyFrequencyCapCapability,
)
from ._schemas.core.media_buy_frequency_cap_requirement import (
    MediaBuyFrequencyCapRequirement as MediaBuyFrequencyCapRequirement,
)
from ._schemas.core.media_buy_frequency_cap_support import MediaBuyFrequencyCapSupport as MediaBuyFrequencyCapSupport
from ._schemas.core.media_buy_legacy_terms_ref import MediaBuyTermsReference as MediaBuyTermsReference
from ._schemas.core.media_buy_support import ProductMediaBuySupport as ProductMediaBuySupport
from ._schemas.core.media_buy_support_requirements import (
    ProductMediaBuySupportRequirements as ProductMediaBuySupportRequirements,
)
from ._schemas.core.missing_metric import MissingMetric as MissingMetric
from ._schemas.core.missing_metric import MissingMetricVendor as MissingMetricVendor
from ._schemas.core.missing_metric import ObjScopeMetricIdQualifier as ObjScopeMetricIdQualifier
from ._schemas.core.negative_keyword import NegativeKeyword as NegativeKeyword
from ._schemas.core.notification_config import NotificationConfig as NotificationConfig
from ._schemas.core.offering import Offering as Offering
from ._schemas.core.offering_asset_group import OfferingAssetGroup as OfferingAssetGroup
from ._schemas.core.operator_identity import OperatorIdentity as OperatorIdentity
from ._schemas.core.operator_unit import OperatorUnit as OperatorUnit
from ._schemas.core.opportunity_context import OpportunityContext as OpportunityContext
from ._schemas.core.optimization_goal import OptimizationGoal as OptimizationGoal
from ._schemas.core.optimization_goal import OptimizationGoalEvent as OptimizationGoalEvent
from ._schemas.core.optimization_goal import OptimizationGoalEventTargetCostPer as OptimizationGoalEventTargetCostPer
from ._schemas.core.optimization_goal import OptimizationGoalMetric as OptimizationGoalMetric
from ._schemas.core.optimization_goal import OptimizationGoalMetricTargetCostPer as OptimizationGoalMetricTargetCostPer
from ._schemas.core.optimization_goal import (
    OptimizationGoalMetricTargetThresholdRate as OptimizationGoalMetricTargetThresholdRate,
)
from ._schemas.core.optimization_goal import OptimizationGoalVendorMetric as OptimizationGoalVendorMetric
from ._schemas.core.optimization_goal import (
    OptimizationGoalVendorMetricTargetCostPer as OptimizationGoalVendorMetricTargetCostPer,
)
from ._schemas.core.optimization_goal import (
    OptimizationGoalVendorMetricTargetThresholdRate as OptimizationGoalVendorMetricTargetThresholdRate,
)
from ._schemas.core.optimization_goal import TargetMaximizeValue as TargetMaximizeValue
from ._schemas.core.optimization_goal import TargetPerAdSpend as TargetPerAdSpend
from ._schemas.core.outcome_measurement import OutcomeMeasurement as OutcomeMeasurement
from ._schemas.core.outcome_target_cost_per import OutcomeTargetCostPer as OutcomeTargetCostPer
from ._schemas.core.overlay import Overlay as Overlay
from ._schemas.core.package import Package as Package
from ._schemas.core.package_delivery_metric_value import PackageDeliveryMetricValue as PackageDeliveryMetricValue
from ._schemas.core.package_format_snapshot import PackageFormatSnapshot as PackageFormatSnapshot
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotAgentPlacement as PackageFormatSnapshotAgentPlacement,
)
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotAudioDaast as PackageFormatSnapshotAudioDaast
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotAudioHosted as PackageFormatSnapshotAudioHosted
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotAudioVast as PackageFormatSnapshotAudioVast
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotCoordinatedPlacements as PackageFormatSnapshotCoordinatedPlacements,
)
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotCustom as PackageFormatSnapshotCustom
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotDisplayTag as PackageFormatSnapshotDisplayTag
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotHtml5 as PackageFormatSnapshotHtml5
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotImage as PackageFormatSnapshotImage
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotImageCarousel as PackageFormatSnapshotImageCarousel,
)
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotNativeInFeed as PackageFormatSnapshotNativeInFeed,
)
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotResponsiveCreative as PackageFormatSnapshotResponsiveCreative,
)
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotSellerRenderedStatefulDisplay as PackageFormatSnapshotSellerRenderedStatefulDisplay,
)
from ._schemas.core.package_format_snapshot import (
    PackageFormatSnapshotSponsoredPlacement as PackageFormatSnapshotSponsoredPlacement,
)
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotVideoHosted as PackageFormatSnapshotVideoHosted
from ._schemas.core.package_format_snapshot import PackageFormatSnapshotVideoVast as PackageFormatSnapshotVideoVast
from ._schemas.core.package_signal_targeting import PackageSignalTargeting as PackageSignalTargeting
from ._schemas.core.package_signal_targeting import PackageSignalTargetingBinary as PackageSignalTargetingBinary
from ._schemas.core.package_signal_targeting import (
    PackageSignalTargetingCategorical as PackageSignalTargetingCategorical,
)
from ._schemas.core.package_signal_targeting import PackageSignalTargetingNumeric as PackageSignalTargetingNumeric
from ._schemas.core.package_signal_targeting_group import PackageSignalTargetingGroup as PackageSignalTargetingGroup
from ._schemas.core.package_signal_targeting_groups import PackageSignalTargetingGroups as PackageSignalTargetingGroups
from ._schemas.core.package_targeting_resolution import PackageTargetingResolution as PackageTargetingResolution
from ._schemas.core.pagination_request import PaginationRequest as PaginationRequest
from ._schemas.core.pagination_response import PaginationResponse as PaginationResponse
from ._schemas.core.performance_feedback import PerformanceFeedback as PerformanceFeedback
from ._schemas.core.performance_feedback_assertion import PerformanceFeedbackAssertion as PerformanceFeedbackAssertion
from ._schemas.core.performance_feedback_metric import PerformanceFeedbackMetric as PerformanceFeedbackMetric
from ._schemas.core.performance_feedback_metric import (
    PerformanceFeedbackMetricStandard as PerformanceFeedbackMetricStandard,
)
from ._schemas.core.performance_feedback_metric import (
    PerformanceFeedbackMetricVendor as PerformanceFeedbackMetricVendor,
)
from ._schemas.core.performance_standard import PerformanceStandard as PerformanceStandard
from ._schemas.core.placement import Placement as Placement
from ._schemas.core.placement_definition import FormatOptionsItemFormatOptionId as FormatOptionsItemFormatOptionId
from ._schemas.core.placement_definition import PlacementDefinition as PlacementDefinition
from ._schemas.core.placement_delivery_metrics import PlacementDeliveryMetrics as PlacementDeliveryMetrics
from ._schemas.core.placement_evidence import PlacementEvidence as PlacementEvidence
from ._schemas.core.placement_identity import PlacementIdentity as PlacementIdentity
from ._schemas.core.placement_identity import PublisherCatalogPlacementIdentity as PublisherCatalogPlacementIdentity
from ._schemas.core.placement_identity import SellerInlinePlacementIdentity as SellerInlinePlacementIdentity
from ._schemas.core.placement_presentation import Color as Color
from ._schemas.core.placement_presentation import PlacementPresentationDocument as PlacementPresentationDocument
from ._schemas.core.placement_property_delivery_metrics import (
    PlacementPropertyDeliveryMetrics as PlacementPropertyDeliveryMetrics,
)
from ._schemas.core.placement_ref import PlacementReference as PlacementReference
from ._schemas.core.placement_selection import PlacementSelection as PlacementSelection
from ._schemas.core.placement_selection import ProductDefaultPlacements as ProductDefaultPlacements
from ._schemas.core.placement_selection import PublisherPlacementReference as PublisherPlacementReference
from ._schemas.core.placement_selection import SelectedPlacements as SelectedPlacements
from ._schemas.core.planned_delivery import PlannedDelivery as PlannedDelivery
from ._schemas.core.platform_extension_ref import PlatformExtensionReference as PlatformExtensionReference
from ._schemas.core.positive_postal_area_support import PositivePostalAreaSupport as PositivePostalAreaSupport
from ._schemas.core.postal_area import PostalArea as PostalArea
from ._schemas.core.postal_area import PostalAreaAUPostcode as PostalAreaAUPostcode
from ._schemas.core.postal_area import PostalAreaBranch9 as PostalAreaBranch9
from ._schemas.core.postal_area import PostalAreaBRCep as PostalAreaBRCep
from ._schemas.core.postal_area import PostalAreaCA as PostalAreaCA
from ._schemas.core.postal_area import PostalAreaCountrySystemValues as PostalAreaCountrySystemValues
from ._schemas.core.postal_area import PostalAreaFRCodePostal as PostalAreaFRCodePostal
from ._schemas.core.postal_area import PostalAreaGB as PostalAreaGB
from ._schemas.core.postal_area import PostalAreaINPin as PostalAreaINPin
from ._schemas.core.postal_area import PostalAreaPlz as PostalAreaPlz
from ._schemas.core.postal_area import PostalAreaUS as PostalAreaUS
from ._schemas.core.postal_area import PostalAreaWithFusedSystem as PostalAreaWithFusedSystem
from ._schemas.core.postal_area import PostalAreaZAPostalCode as PostalAreaZAPostalCode
from ._schemas.core.postal_area_support import PostalAreaSupport as PostalAreaSupport
from ._schemas.core.postal_country_system import PostalCountrySystem as PostalCountrySystem
from ._schemas.core.postal_country_system import PostalCountrySystemAUPostcode as PostalCountrySystemAUPostcode
from ._schemas.core.postal_country_system import PostalCountrySystemBranch9 as PostalCountrySystemBranch9
from ._schemas.core.postal_country_system import PostalCountrySystemBRCep as PostalCountrySystemBRCep
from ._schemas.core.postal_country_system import PostalCountrySystemCA as PostalCountrySystemCA
from ._schemas.core.postal_country_system import PostalCountrySystemFRCodePostal as PostalCountrySystemFRCodePostal
from ._schemas.core.postal_country_system import PostalCountrySystemGB as PostalCountrySystemGB
from ._schemas.core.postal_country_system import PostalCountrySystemINPin as PostalCountrySystemINPin
from ._schemas.core.postal_country_system import PostalCountrySystemPlz as PostalCountrySystemPlz
from ._schemas.core.postal_country_system import PostalCountrySystemUS as PostalCountrySystemUS
from ._schemas.core.postal_country_system import PostalCountrySystemZAPostalCode as PostalCountrySystemZAPostalCode
from ._schemas.core.presentation_ref import PlacementPresentationReference as PlacementPresentationReference
from ._schemas.core.preview_provider import PublisherDesignatedPreviewProvider as PublisherDesignatedPreviewProvider
from ._schemas.core.preview_renderer_metadata import PreviewRendererMetadata as PreviewRendererMetadata
from ._schemas.core.price import Price as Price
from ._schemas.core.pricing_option import PricingOption as PricingOption
from ._schemas.core.pricing_option import PricingOptionCpa as PricingOptionCpa
from ._schemas.core.pricing_option import PricingOptionCpc as PricingOptionCpc
from ._schemas.core.pricing_option import PricingOptionCpcv as PricingOptionCpcv
from ._schemas.core.pricing_option import PricingOptionCpm as PricingOptionCpm
from ._schemas.core.pricing_option import PricingOptionCpp as PricingOptionCpp
from ._schemas.core.pricing_option import PricingOptionCpv as PricingOptionCpv
from ._schemas.core.pricing_option import PricingOptionFlatRate as PricingOptionFlatRate
from ._schemas.core.pricing_option import PricingOptionRevenueShare as PricingOptionRevenueShare
from ._schemas.core.pricing_option import PricingOptionTime as PricingOptionTime
from ._schemas.core.pricing_option import PricingOptionVcpm as PricingOptionVcpm
from ._schemas.core.principal_changed_webhook import PrincipalChangedWebhook as PrincipalChangedWebhook
from ._schemas.core.principal_declarations import AgentDeclarations as AgentDeclarations
from ._schemas.core.principal_declarations_state import PrincipalDeclarationsState as PrincipalDeclarationsState
from ._schemas.core.principal_state import PrincipalState as PrincipalState
from ._schemas.core.product import Product as Product
from ._schemas.core.product_allocation import ProductAllocation as ProductAllocation
from ._schemas.core.product_allowed_action import ProductAllowedAction as ProductAllowedAction
from ._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuersItemAgent as AcceptedAttestationIssuersItemAgent,
)
from ._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuersItemBrand as AcceptedAttestationIssuersItemBrand,
)
from ._schemas.core.product_audience_evidence_requirements import (
    ProductAudienceEvidenceRequirements as ProductAudienceEvidenceRequirements,
)
from ._schemas.core.product_card_reference_asset import ProductCardReferenceAsset as ProductCardReferenceAsset
from ._schemas.core.product_change_map import ProductChangeMap as ProductChangeMap
from ._schemas.core.product_execution_requirement import CatalogExecutionRequirement as CatalogExecutionRequirement
from ._schemas.core.product_execution_requirement import (
    DownstreamConnectionExecutionRequirement as DownstreamConnectionExecutionRequirement,
)
from ._schemas.core.product_execution_requirement import (
    EventSourceExecutionRequirement as EventSourceExecutionRequirement,
)
from ._schemas.core.product_execution_requirement import ProductExecutionRequirement as ProductExecutionRequirement
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemCleanRoom as AudienceActivationMethodsItemCleanRoom,
)
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemDatasetQuery as AudienceActivationMethodsItemDatasetQuery,
)
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemFileTransfer as AudienceActivationMethodsItemFileTransfer,
)
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemPlatformDistribution as AudienceActivationMethodsItemPlatformDistribution,
)
from ._schemas.core.product_filters import (
    AudienceActivationMethodsItemTmpIdentityMatch as AudienceActivationMethodsItemTmpIdentityMatch,
)
from ._schemas.core.product_filters import ProductFilters as ProductFilters
from ._schemas.core.product_filters import SignalTargetingItemBinary as SignalTargetingItemBinary
from ._schemas.core.product_filters import SignalTargetingItemCategorical as SignalTargetingItemCategorical
from ._schemas.core.product_filters import SignalTargetingItemNumeric as SignalTargetingItemNumeric
from ._schemas.core.product_format_declaration import AgentPlacementFormatDeclaration as AgentPlacementFormatDeclaration
from ._schemas.core.product_format_declaration import (
    CoordinatedPlacementsFormatDeclaration as CoordinatedPlacementsFormatDeclaration,
)
from ._schemas.core.product_format_declaration import CustomFormatDeclaration as CustomFormatDeclaration
from ._schemas.core.product_format_declaration import DAASTAudioFormatDeclaration as DAASTAudioFormatDeclaration
from ._schemas.core.product_format_declaration import DisplayTagFormatDeclaration as DisplayTagFormatDeclaration
from ._schemas.core.product_format_declaration import HostedAudioFormatDeclaration as HostedAudioFormatDeclaration
from ._schemas.core.product_format_declaration import HostedVideoFormatDeclaration as HostedVideoFormatDeclaration
from ._schemas.core.product_format_declaration import HTML5FormatDeclaration as HTML5FormatDeclaration
from ._schemas.core.product_format_declaration import ImageCarouselFormatDeclaration as ImageCarouselFormatDeclaration
from ._schemas.core.product_format_declaration import ImageFormatDeclaration as ImageFormatDeclaration
from ._schemas.core.product_format_declaration import NativeInFeedFormatDeclaration as NativeInFeedFormatDeclaration
from ._schemas.core.product_format_declaration import ProductFormatDeclaration as ProductFormatDeclaration
from ._schemas.core.product_format_declaration import (
    ResponsiveCreativeFormatDeclaration as ResponsiveCreativeFormatDeclaration,
)
from ._schemas.core.product_format_declaration import (
    SellerRenderedStatefulDisplayFormatDeclaration as SellerRenderedStatefulDisplayFormatDeclaration,
)
from ._schemas.core.product_format_declaration import (
    SponsoredPlacementFormatDeclaration as SponsoredPlacementFormatDeclaration,
)
from ._schemas.core.product_format_declaration import VASTAudioFormatDeclaration as VASTAudioFormatDeclaration
from ._schemas.core.product_format_declaration import VASTVideoFormatDeclaration as VASTVideoFormatDeclaration
from ._schemas.core.product_identity import ProductIdentity as ProductIdentity
from ._schemas.core.product_offer_filters import ProductOfferFilters as ProductOfferFilters
from ._schemas.core.product_signal_targeting_option import ProductSignalTargetingOption as ProductSignalTargetingOption
from ._schemas.core.product_targeting_resolution import ProductTargetingResolution as ProductTargetingResolution
from ._schemas.core.property import Property as Property
from ._schemas.core.property_delivery_metrics import PropertyDeliveryMetrics as PropertyDeliveryMetrics
from ._schemas.core.property_id import PropertyID as PropertyID
from ._schemas.core.property_list_ref import PropertyListReference as PropertyListReference
from ._schemas.core.property_ref import PropertyReference as PropertyReference
from ._schemas.core.property_tag import PropertyTag as PropertyTag
from ._schemas.core.proposal import Proposal as Proposal
from ._schemas.core.protocol_envelope import ProtocolEnvelope as ProtocolEnvelope
from ._schemas.core.provenance import Provenance as Provenance
from ._schemas.core.publisher_property_selector import PublisherPropertySelector as PublisherPropertySelector
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorAll as PublisherPropertySelectorAll
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorById as PublisherPropertySelectorById
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorByTag as PublisherPropertySelectorByTag
from ._schemas.core.push_notification_config import PushNotificationConfig as PushNotificationConfig
from ._schemas.core.real_estate_item import RealEstateItem as RealEstateItem
from ._schemas.core.reference_asset import ReferenceAsset as ReferenceAsset
from ._schemas.core.reference_renderer import ReferenceRenderer as ReferenceRenderer
from ._schemas.core.registry_event import ChangedFields as ChangedFields
from ._schemas.core.registry_event import Countries as Countries
from ._schemas.core.registry_event import RegistryEvent as RegistryEvent
from ._schemas.core.registry_event import (
    RegistryEventAgentComplianceChangedAgent as RegistryEventAgentComplianceChangedAgent,
)
from ._schemas.core.registry_event import RegistryEventAgentDiscoveredAgent as RegistryEventAgentDiscoveredAgent
from ._schemas.core.registry_event import RegistryEventAgentProfileUpdatedAgent as RegistryEventAgentProfileUpdatedAgent
from ._schemas.core.registry_event import RegistryEventAgentRemovedAgent as RegistryEventAgentRemovedAgent
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationEarnedAgent as RegistryEventAgentVerificationEarnedAgent,
)
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationLostAgent as RegistryEventAgentVerificationLostAgent,
)
from ._schemas.core.registry_event import (
    RegistryEventAuthorizationGrantedAuthorization as RegistryEventAuthorizationGrantedAuthorization,
)
from ._schemas.core.registry_event import (
    RegistryEventAuthorizationModifiedAuthorization as RegistryEventAuthorizationModifiedAuthorization,
)
from ._schemas.core.registry_event import (
    RegistryEventAuthorizationRevokedAuthorization as RegistryEventAuthorizationRevokedAuthorization,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionCreatedCollection as RegistryEventCollectionCreatedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionMergedCollection as RegistryEventCollectionMergedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionRemovedCollection as RegistryEventCollectionRemovedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionUpdatedCollection as RegistryEventCollectionUpdatedCollection,
)
from ._schemas.core.registry_event import RegistryEventPropertyCreatedProperty as RegistryEventPropertyCreatedProperty
from ._schemas.core.registry_event import RegistryEventPropertyMergedProperty as RegistryEventPropertyMergedProperty
from ._schemas.core.registry_event import (
    RegistryEventPropertyReactivatedProperty as RegistryEventPropertyReactivatedProperty,
)
from ._schemas.core.registry_event import RegistryEventPropertyStaleProperty as RegistryEventPropertyStaleProperty
from ._schemas.core.registry_event import RegistryEventPropertyUpdatedProperty as RegistryEventPropertyUpdatedProperty
from ._schemas.core.registry_event import (
    RegistryEventPublisherAdagentsChangedPublisher as RegistryEventPublisherAdagentsChangedPublisher,
)
from ._schemas.core.registry_event import (
    RegistryEventPublisherAdagentsDiscoveredPublisher as RegistryEventPublisherAdagentsDiscoveredPublisher,
)
from ._schemas.core.registry_event import StringArray as StringArray
from ._schemas.core.registry_feed_response import RegistryFeedResponse as RegistryFeedResponse
from ._schemas.core.reporting_adjustment import ReportingAdjustment as ReportingAdjustment
from ._schemas.core.reporting_adjustment_receipt import ReportingAdjustmentReceipt as ReportingAdjustmentReceipt
from ._schemas.core.reporting_adjustment_receipt import (
    ReportingAdjustmentRejectionCode as ReportingAdjustmentRejectionCode,
)
from ._schemas.core.reporting_canonical_content_digest import (
    ReportingCanonicalContentDigest as ReportingCanonicalContentDigest,
)
from ._schemas.core.reporting_canonicalization_contract import (
    ReportingCanonicalizationContract as ReportingCanonicalizationContract,
)
from ._schemas.core.reporting_canonicalization_contract import ReportingPrimaryKey as ReportingPrimaryKey
from ._schemas.core.reporting_capabilities import ReportingCapabilities as ReportingCapabilities
from ._schemas.core.reporting_consumer_status import ReportingConsumerStatus as ReportingConsumerStatus
from ._schemas.core.reporting_control_total import DecimalReportingControlTotal as DecimalReportingControlTotal
from ._schemas.core.reporting_control_total import IntegerReportingControlTotal as IntegerReportingControlTotal
from ._schemas.core.reporting_control_total import ReportingControlTotal as ReportingControlTotal
from ._schemas.core.reporting_coverage import ReportingCoverage as ReportingCoverage
from ._schemas.core.reporting_coverage import ReportingMediaBuyId as ReportingMediaBuyId
from ._schemas.core.reporting_coverage import ReportingPackageId as ReportingPackageId
from ._schemas.core.reporting_dataset_share_destination import ProvisionRecipient as ProvisionRecipient
from ._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestination as ReportingDatasetShareDestination,
)
from ._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestinationExisting as ReportingDatasetShareDestinationExisting,
)
from ._schemas.core.reporting_delivery_capabilities import (
    ReportingDeliveryCapabilities as ReportingDeliveryCapabilities,
)
from ._schemas.core.reporting_delivery_config import ReportingDeliveryConfiguration as ReportingDeliveryConfiguration
from ._schemas.core.reporting_delivery_config_state import (
    ReportingDeliveryConfigurationState as ReportingDeliveryConfigurationState,
)
from ._schemas.core.reporting_delivery_method import DatasetShare as DatasetShare
from ._schemas.core.reporting_delivery_method import ReportingDeliveryMethod as ReportingDeliveryMethod
from ._schemas.core.reporting_delivery_method import (
    ReportingDeliveryMethodFileTransfer as ReportingDeliveryMethodFileTransfer,
)
from ._schemas.core.reporting_delivery_method import WarehouseMaterialization as WarehouseMaterialization
from ._schemas.core.reporting_delivery_offering import ReportingDeliveryOffering as ReportingDeliveryOffering
from ._schemas.core.reporting_delivery_offering_id import ReportingDeliveryOfferingID as ReportingDeliveryOfferingID
from ._schemas.core.reporting_delivery_ready_webhook import (
    ReportingDeliveryReadyWebhook as ReportingDeliveryReadyWebhook,
)
from ._schemas.core.reporting_file_compression import ReportingFileCompression as ReportingFileCompression
from ._schemas.core.reporting_file_entry import ReportingFileEntry as ReportingFileEntry
from ._schemas.core.reporting_file_manifest import ReportingFileManifest as ReportingFileManifest
from ._schemas.core.reporting_file_object_ref import ReportingFileObjectReference as ReportingFileObjectReference
from ._schemas.core.reporting_ledger_changed_webhook import (
    ReportingLedgerChangedWebhook as ReportingLedgerChangedWebhook,
)
from ._schemas.core.reporting_materialization import ReportingMaterialization as ReportingMaterialization
from ._schemas.core.reporting_native_version_ref import (
    ReportingNativeVersionReference as ReportingNativeVersionReference,
)
from ._schemas.core.reporting_obligation import ReportingObligation as ReportingObligation
from ._schemas.core.reporting_receipt import ReportingReceipt as ReportingReceipt
from ._schemas.core.reporting_reconciliation_mode import ReportingReconciliationMode as ReportingReconciliationMode
from ._schemas.core.reporting_reliability_statistics import (
    ReportingReliabilityStatistics as ReportingReliabilityStatistics,
)
from ._schemas.core.reporting_report_definition import (
    FinalityPoliciesItemContractualCutoff as FinalityPoliciesItemContractualCutoff,
)
from ._schemas.core.reporting_report_definition import (
    FinalityPoliciesItemSourceFinal as FinalityPoliciesItemSourceFinal,
)
from ._schemas.core.reporting_report_definition import FinalityPoliciesItemStabilized as FinalityPoliciesItemStabilized
from ._schemas.core.reporting_report_definition import ReportingReportDefinition as ReportingReportDefinition
from ._schemas.core.reporting_resource import ReportingReaderCompatibilityItem as ReportingReaderCompatibilityItem
from ._schemas.core.reporting_resource import ReportingResource as ReportingResource
from ._schemas.core.reporting_revision import ReportingRevision as ReportingRevision
from ._schemas.core.reporting_schedule import ReportingSchedule as ReportingSchedule
from ._schemas.core.reporting_schedule_offering import ReportingScheduleOffering as ReportingScheduleOffering
from ._schemas.core.reporting_status_changed_webhook import (
    ReportingStatusChangedWebhook as ReportingStatusChangedWebhook,
)
from ._schemas.core.reporting_status_issue import ReportingStatusIssue as ReportingStatusIssue
from ._schemas.core.reporting_verification import ReportingVerification as ReportingVerification
from ._schemas.core.reporting_verification import SHA256PhysicalChecksum as SHA256PhysicalChecksum
from ._schemas.core.reporting_verification import SHA512PhysicalChecksum as SHA512PhysicalChecksum
from ._schemas.core.reporting_verification_profile import ReportingVerificationProfile as ReportingVerificationProfile
from ._schemas.core.reporting_verification_profile_set import (
    ReportingVerificationProfileSet as ReportingVerificationProfileSet,
)
from ._schemas.core.reporting_webhook import ReportingWebhook as ReportingWebhook
from ._schemas.core.reporting_write_destination import ProvisionBinding as ProvisionBinding
from ._schemas.core.reporting_write_destination import ReportingWriteDestination as ReportingWriteDestination
from ._schemas.core.reporting_write_destination import (
    ReportingWriteDestinationExisting as ReportingWriteDestinationExisting,
)
from ._schemas.core.representation_destination import RepresentationDestination as RepresentationDestination
from ._schemas.core.representation_rejection import RepresentationRejection as RepresentationRejection
from ._schemas.core.representation_selection import RepresentationSelection as RepresentationSelection
from ._schemas.core.requirements.asset_requirements import AssetRequirements as AssetRequirements
from ._schemas.core.requirements.asset_requirements import AssetRequirementsAudio as AssetRequirementsAudio
from ._schemas.core.requirements.asset_requirements import AssetRequirementsCSS as AssetRequirementsCSS
from ._schemas.core.requirements.asset_requirements import AssetRequirementsDAAST as AssetRequirementsDAAST
from ._schemas.core.requirements.asset_requirements import AssetRequirementsHTML as AssetRequirementsHTML
from ._schemas.core.requirements.asset_requirements import AssetRequirementsImage as AssetRequirementsImage
from ._schemas.core.requirements.asset_requirements import AssetRequirementsJavaScript as AssetRequirementsJavaScript
from ._schemas.core.requirements.asset_requirements import AssetRequirementsMarkdown as AssetRequirementsMarkdown
from ._schemas.core.requirements.asset_requirements import AssetRequirementsText as AssetRequirementsText
from ._schemas.core.requirements.asset_requirements import AssetRequirementsURL as AssetRequirementsURL
from ._schemas.core.requirements.asset_requirements import AssetRequirementsVAST as AssetRequirementsVAST
from ._schemas.core.requirements.asset_requirements import AssetRequirementsVideo as AssetRequirementsVideo
from ._schemas.core.requirements.asset_requirements import AssetRequirementsWebhook as AssetRequirementsWebhook
from ._schemas.core.requirements.audio_asset_requirements import AudioAssetRequirements as AudioAssetRequirements
from ._schemas.core.requirements.catalog_field_binding import CatalogFieldBinding as CatalogFieldBinding
from ._schemas.core.requirements.catalog_field_binding import (
    CatalogFieldBindingAssetPool as CatalogFieldBindingAssetPool,
)
from ._schemas.core.requirements.catalog_field_binding import (
    CatalogFieldBindingCatalogGroup as CatalogFieldBindingCatalogGroup,
)
from ._schemas.core.requirements.catalog_field_binding import CatalogFieldBindingScalar as CatalogFieldBindingScalar
from ._schemas.core.requirements.catalog_requirements import CatalogRequirements as CatalogRequirements
from ._schemas.core.requirements.css_asset_requirements import CSSAssetRequirements as CSSAssetRequirements
from ._schemas.core.requirements.daast_asset_requirements import DAASTAssetRequirements as DAASTAssetRequirements
from ._schemas.core.requirements.html_asset_requirements import HTMLAssetRequirements as HTMLAssetRequirements
from ._schemas.core.requirements.image_asset_requirements import BleedBottomLeftRightTop as BleedBottomLeftRightTop
from ._schemas.core.requirements.image_asset_requirements import BleedUniform as BleedUniform
from ._schemas.core.requirements.image_asset_requirements import ImageAssetRequirements as ImageAssetRequirements
from ._schemas.core.requirements.javascript_asset_requirements import (
    JavaScriptAssetRequirements as JavaScriptAssetRequirements,
)
from ._schemas.core.requirements.markdown_asset_requirements import (
    MarkdownAssetRequirements as MarkdownAssetRequirements,
)
from ._schemas.core.requirements.offering_asset_constraint import OfferingAssetConstraint as OfferingAssetConstraint
from ._schemas.core.requirements.text_asset_requirements import TextAssetRequirements as TextAssetRequirements
from ._schemas.core.requirements.url_asset_requirements import URLAssetRequirements as URLAssetRequirements
from ._schemas.core.requirements.vast_asset_requirements import VASTAssetRequirements as VASTAssetRequirements
from ._schemas.core.requirements.video_asset_requirements import VideoAssetRequirements as VideoAssetRequirements
from ._schemas.core.requirements.webhook_asset_requirements import WebhookAssetRequirements as WebhookAssetRequirements
from ._schemas.core.response import ProtocolResponse as ProtocolResponse
from ._schemas.core.response_payload_jws_envelope import ResponsePayloadJWSEnvelope as ResponsePayloadJWSEnvelope
from ._schemas.core.rights_attestation_evaluation import RightsAttestationEvaluation as RightsAttestationEvaluation
from ._schemas.core.rights_constraint import RightsConstraint as RightsConstraint
from ._schemas.core.seller_agent_ref import SellerAgentReference as SellerAgentReference
from ._schemas.core.signal_coverage_forecast import SignalCoverageForecast as SignalCoverageForecast
from ._schemas.core.signal_definition import SignalDefinition as SignalDefinition
from ._schemas.core.signal_definition_enrichment import LookbackWindow as LookbackWindow
from ._schemas.core.signal_definition_enrichment import SignalDefinitionEnrichment as SignalDefinitionEnrichment
from ._schemas.core.signal_filters import SignalFilters as SignalFilters
from ._schemas.core.signal_id import SignalID as SignalID
from ._schemas.core.signal_id import SignalIDAgent as SignalIDAgent
from ._schemas.core.signal_id import SignalIDCatalog as SignalIDCatalog
from ._schemas.core.signal_listing import SignalListing as SignalListing
from ._schemas.core.signal_modeling_disclosure import SignalModelingDisclosure as SignalModelingDisclosure
from ._schemas.core.signal_pricing import CpmPricing as CpmPricing
from ._schemas.core.signal_pricing import CustomPricing as CustomPricing
from ._schemas.core.signal_pricing import FlatFeePricing as FlatFeePricing
from ._schemas.core.signal_pricing import PercentOfMediaPricing as PercentOfMediaPricing
from ._schemas.core.signal_pricing import PerUnitPricing as PerUnitPricing
from ._schemas.core.signal_pricing import VendorPricing as VendorPricing
from ._schemas.core.signal_pricing_option import SignalPricingOption as SignalPricingOption
from ._schemas.core.signal_ref import SignalRef as SignalRef
from ._schemas.core.signal_ref import SignalRefDataProvider as SignalRefDataProvider
from ._schemas.core.signal_ref import SignalRefProduct as SignalRefProduct
from ._schemas.core.signal_ref import SignalRefSignalSource as SignalRefSignalSource
from ._schemas.core.signal_selection_group_rule import SignalSelectionGroupRule as SignalSelectionGroupRule
from ._schemas.core.signal_targeting import SignalTargeting as SignalTargeting
from ._schemas.core.signal_targeting import SignalTargetingBinary as SignalTargetingBinary
from ._schemas.core.signal_targeting import SignalTargetingCategorical as SignalTargetingCategorical
from ._schemas.core.signal_targeting import SignalTargetingNumeric as SignalTargetingNumeric
from ._schemas.core.signal_targeting_expression import SignalTargetingExpression as SignalTargetingExpression
from ._schemas.core.signal_targeting_expression import (
    SignalTargetingExpressionBinary as SignalTargetingExpressionBinary,
)
from ._schemas.core.signal_targeting_expression import (
    SignalTargetingExpressionCategorical as SignalTargetingExpressionCategorical,
)
from ._schemas.core.signal_targeting_expression import (
    SignalTargetingExpressionNumeric as SignalTargetingExpressionNumeric,
)
from ._schemas.core.signal_targeting_rules import SignalTargetingRules as SignalTargetingRules
from ._schemas.core.sla_window import SLAWindow as SLAWindow
from ._schemas.core.special import Special as Special
from ._schemas.core.spot_reporting_capability import SpotReportingCapability as SpotReportingCapability
from ._schemas.core.start_timing import StartTiming as StartTiming
from ._schemas.core.store_item import HoursValue as HoursValue
from ._schemas.core.store_item import StoreItem as StoreItem
from ._schemas.core.talent import Talent as Talent
from ._schemas.core.targeting import AudienceExclude as AudienceExclude
from ._schemas.core.targeting import AudienceInclude as AudienceInclude
from ._schemas.core.targeting import AxeExcludeSegment as AxeExcludeSegment
from ._schemas.core.targeting import AxeIncludeSegment as AxeIncludeSegment
from ._schemas.core.targeting import Browser as Browser
from ._schemas.core.targeting import BrowserExclude as BrowserExclude
from ._schemas.core.targeting import DaypartTargets as DaypartTargets
from ._schemas.core.targeting import DevicePlatformExclude as DevicePlatformExclude
from ._schemas.core.targeting import DeviceTypeExclude as DeviceTypeExclude
from ._schemas.core.targeting import GeoCountries as GeoCountries
from ._schemas.core.targeting import GeoCountriesExclude as GeoCountriesExclude
from ._schemas.core.targeting import GeoMetrosExclude as GeoMetrosExclude
from ._schemas.core.targeting import GeoPlaces as GeoPlaces
from ._schemas.core.targeting import GeoPlacesExclude as GeoPlacesExclude
from ._schemas.core.targeting import GeoPostalAreas as GeoPostalAreas
from ._schemas.core.targeting import GeoPostalAreasExclude as GeoPostalAreasExclude
from ._schemas.core.targeting import GeoRegions as GeoRegions
from ._schemas.core.targeting import GeoRegionsExclude as GeoRegionsExclude
from ._schemas.core.targeting import StoreCatchments as StoreCatchments
from ._schemas.core.targeting import TargetingOverlay as TargetingOverlay
from ._schemas.core.targeting import TargetingOverlayDevicePlatform as TargetingOverlayDevicePlatform
from ._schemas.core.targeting import TargetingOverlayDeviceType as TargetingOverlayDeviceType
from ._schemas.core.targeting import TargetingOverlayGeoProximity as TargetingOverlayGeoProximity
from ._schemas.core.targeting_input import TargetingOverlayInput as TargetingOverlayInput
from ._schemas.core.targeting_modification import RemoveTargetingSetValues as RemoveTargetingSetValues
from ._schemas.core.targeting_modification import ReplaceTargetingValue as ReplaceTargetingValue
from ._schemas.core.targeting_modification import TargetingModification as TargetingModification
from ._schemas.core.targeting_overlay_requirements import BrowserRequirement as BrowserRequirement
from ._schemas.core.targeting_overlay_requirements import BrowserRequirementFamilies as BrowserRequirementFamilies
from ._schemas.core.targeting_overlay_requirements import DaypartRequirement as DaypartRequirement
from ._schemas.core.targeting_overlay_requirements import (
    DaypartRequirementTimezoneModes as DaypartRequirementTimezoneModes,
)
from ._schemas.core.targeting_overlay_requirements import KeywordRequirement as KeywordRequirement
from ._schemas.core.targeting_overlay_requirements import (
    KeywordRequirementSupportedMatchTypes as KeywordRequirementSupportedMatchTypes,
)
from ._schemas.core.targeting_overlay_requirements import MetroRequirement as MetroRequirement
from ._schemas.core.targeting_overlay_requirements import MetroRequirementSystems as MetroRequirementSystems
from ._schemas.core.targeting_overlay_requirements import TargetingOverlayRequirements as TargetingOverlayRequirements
from ._schemas.core.targeting_overlay_requirements import (
    TargetingOverlayRequirementsDemographicsAge as TargetingOverlayRequirementsDemographicsAge,
)
from ._schemas.core.targeting_overlay_requirements import (
    TargetingOverlayRequirementsGeoProximity as TargetingOverlayRequirementsGeoProximity,
)
from ._schemas.core.targeting_overlay_requirements import (
    TargetingOverlayRequirementsRequired as TargetingOverlayRequirementsRequired,
)
from ._schemas.core.targeting_overlay_support import BrowserSupport as BrowserSupport
from ._schemas.core.targeting_overlay_support import BrowserSupportFamilies as BrowserSupportFamilies
from ._schemas.core.targeting_overlay_support import CountrySupport as CountrySupport
from ._schemas.core.targeting_overlay_support import (
    CountrySupportMaxValuesPerPackage as CountrySupportMaxValuesPerPackage,
)
from ._schemas.core.targeting_overlay_support import DaypartSupport as DaypartSupport
from ._schemas.core.targeting_overlay_support import DaypartSupportTimezoneModes as DaypartSupportTimezoneModes
from ._schemas.core.targeting_overlay_support import KeywordSupport as KeywordSupport
from ._schemas.core.targeting_overlay_support import (
    KeywordSupportSupportedMatchTypes as KeywordSupportSupportedMatchTypes,
)
from ._schemas.core.targeting_overlay_support import MetroSupport as MetroSupport
from ._schemas.core.targeting_overlay_support import MetroSupportSystems as MetroSupportSystems
from ._schemas.core.targeting_overlay_support import Supported as Supported
from ._schemas.core.targeting_overlay_support import TargetingOverlaySupport as TargetingOverlaySupport
from ._schemas.core.targeting_overlay_support import (
    TargetingOverlaySupportDemographicsAge as TargetingOverlaySupportDemographicsAge,
)
from ._schemas.core.targeting_overlay_support import (
    TargetingOverlaySupportGeoProximity as TargetingOverlaySupportGeoProximity,
)
from ._schemas.core.targeting_overlay_support import (
    TargetingOverlaySupportPlacementSelection as TargetingOverlaySupportPlacementSelection,
)
from ._schemas.core.targeting_unknown_age_eligibility_constraint import (
    TargetingUnknownAgeEligibilityConstraint as TargetingUnknownAgeEligibilityConstraint,
)
from ._schemas.core.targeting_verified_age_basis_constraint import (
    TargetingVerifiedAgeBasisConstraint as TargetingVerifiedAgeBasisConstraint,
)
from ._schemas.core.tasks_get_request import TasksGetRequest as TasksGetRequest
from ._schemas.core.tasks_get_response import TasksGetResponse as TasksGetResponse
from ._schemas.core.tasks_list_request import TasksListRequest as TasksListRequest
from ._schemas.core.tasks_list_response import TasksListResponse as TasksListResponse
from ._schemas.core.tracker_execution_contract import TrackerExecutionContract as TrackerExecutionContract
from ._schemas.core.tracker_execution_selector import TrackerExecutionSelector as TrackerExecutionSelector
from ._schemas.core.tracker_execution_selector import (
    TrackerExecutionSelectorDaastTracker as TrackerExecutionSelectorDaastTracker,
)
from ._schemas.core.tracker_execution_selector import (
    TrackerExecutionSelectorPixelTrackerImg as TrackerExecutionSelectorPixelTrackerImg,
)
from ._schemas.core.tracker_execution_selector import (
    TrackerExecutionSelectorVastTracker as TrackerExecutionSelectorVastTracker,
)
from ._schemas.core.transformer import Transformer as Transformer
from ._schemas.core.transformer_param import TransformerParam as TransformerParam
from ._schemas.core.truncation_sentinel import TruncationSentinel as TruncationSentinel
from ._schemas.core.user_match import UserMatch as UserMatch
from ._schemas.core.vast_media_file_requirements import VASTMediaFileRequirements as VASTMediaFileRequirements
from ._schemas.core.vast_tracker_constraints import VastOffset as VastOffset
from ._schemas.core.vast_tracker_constraints import VASTTrackerConstraints as VASTTrackerConstraints
from ._schemas.core.vast_tracker_constraints import VastVersions as VastVersions
from ._schemas.core.vehicle_item import VehicleItem as VehicleItem
from ._schemas.core.vendor_metric_id import VendorMetricID as VendorMetricID
from ._schemas.core.vendor_metric_optimization import VendorMetricOptimization as VendorMetricOptimization
from ._schemas.core.vendor_metric_optimization_supported_metric import (
    VendorMetricOptimizationSupportedMetric as VendorMetricOptimizationSupportedMetric,
)
from ._schemas.core.vendor_metric_value import VendorMetricValue as VendorMetricValue
from ._schemas.core.vendor_pricing_option import VendorPricingOption as VendorPricingOption
from ._schemas.core.vendor_pricing_option import VendorPricingOptionCpm as VendorPricingOptionCpm
from ._schemas.core.vendor_pricing_option import VendorPricingOptionCustom as VendorPricingOptionCustom
from ._schemas.core.vendor_pricing_option import VendorPricingOptionFlatFee as VendorPricingOptionFlatFee
from ._schemas.core.vendor_pricing_option import VendorPricingOptionPercentOfMedia as VendorPricingOptionPercentOfMedia
from ._schemas.core.vendor_pricing_option import VendorPricingOptionPerUnit as VendorPricingOptionPerUnit
from ._schemas.core.verification_token_claims import (
    AgenticAdvertisingOrgVerificationTokenClaims as AgenticAdvertisingOrgVerificationTokenClaims,
)
from ._schemas.core.verification_token_claims import VerificationTokenGradingProfile as VerificationTokenGradingProfile
from ._schemas.core.version_envelope import AdcpMajorVersion as AdcpMajorVersion
from ._schemas.core.version_envelope import AdcpVersion as AdcpVersion
from ._schemas.core.version_envelope import AdCPVersionEnvelope as AdCPVersionEnvelope
from ._schemas.core.warning import Warning as Warning
from ._schemas.core.warning_resource import WarningAffectedResource as WarningAffectedResource
from ._schemas.core.webhook_activity_record import WebhookActivityRecord as WebhookActivityRecord
from ._schemas.core.webhook_challenge import WebhookChallenge as WebhookChallenge
from ._schemas.core.webhook_challenge_response import WebhookChallengeResponse as WebhookChallengeResponse
from ._schemas.core.wholesale_feed_event import AppliesTo as AppliesTo
from ._schemas.core.wholesale_feed_event import AppliesToAccount as AppliesToAccount
from ._schemas.core.wholesale_feed_event import AppliesToPublic as AppliesToPublic
from ._schemas.core.wholesale_feed_event import WholesaleFeedEvent as WholesaleFeedEvent
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductCreatedProduct as WholesaleFeedEventProductCreatedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductPricedProduct as WholesaleFeedEventProductPricedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductRemovedProduct as WholesaleFeedEventProductRemovedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductUpdatedProduct as WholesaleFeedEventProductUpdatedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalCreatedSignal as WholesaleFeedEventSignalCreatedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalPricedSignal as WholesaleFeedEventSignalPricedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalRemovedSignal as WholesaleFeedEventSignalRemovedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalUpdatedSignal as WholesaleFeedEventSignalUpdatedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeed as WholesaleFeedEventWholesaleFeedBulkChangeFeed,
)
from ._schemas.core.wholesale_feed_webhook import WholesaleFeedWebhook as WholesaleFeedWebhook
from ._schemas.core.x_entity_types import XEntityTypes as XEntityTypes

__all__ = [
    'HTTPSURL',
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
    'AdCPAsyncResponseDataCreateMediaBuyResponse',
    'AdCPAsyncResponseDataDeclineProposalsResponse',
    'AdCPAsyncResponseDataGetCreativeFeaturesResponse',
    'AdCPAsyncResponseDataGetProductsResponse',
    'AdCPAsyncResponseDataGetSignalsResponse',
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
    'BusinessEntity',
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
    'ControlMediaBuyResponseCompleted',
    'ControlMediaBuyResponseFailed',
    'ControlMediaBuyResponseSubmitted',
    'CoordinatedPlacementsFormatDeclaration',
    'Countries',
    'CountryCode',
    'CountrySupport',
    'CountrySupportMaxValuesPerPackage',
    'CpmPricing',
    'CreateMediaBuyAsyncInputRequired',
    'CreateMediaBuyAsyncSubmitted',
    'CreateMediaBuyAsyncWorking',
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
    'CurrencyCode',
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
    'DomainName',
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
    'GeographicRegionSupport',
    'GetCreativeFeaturesAsyncSubmitted',
    'GetGeographicPlaceResolutionRequest',
    'GetGeographicPlaceResolutionResponse',
    'GetProductsAsyncInputRequired',
    'GetProductsAsyncSubmitted',
    'GetProductsAsyncWorking',
    'GetSignalsAsyncSubmitted',
    'GetSignalsAsyncWorking',
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
    'IdempotencyKey',
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
    'MediaBuyCommitmentResponseCompleted',
    'MediaBuyCommitmentResponseFailed',
    'MediaBuyCommitmentResponseSubmitted',
    'MediaBuyFeatures',
    'MediaBuyFrequencyCap',
    'MediaBuyFrequencyCapCapability',
    'MediaBuyFrequencyCapRequirement',
    'MediaBuyFrequencyCapSupport',
    'MediaBuyTermsReference',
    'MetroRequirement',
    'MetroRequirementSystems',
    'MetroSupport',
    'MetroSupportSystems',
    'MissingMetric',
    'MissingMetricVendor',
    'NativeInFeedFormatDeclaration',
    'NegativeKeyword',
    'NonblockingImpacts',
    'NotificationConfig',
    'ObjAllValues',
    'ObjScopeMetricIdQualifier',
    'ObjValues',
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
    'PublisherPlacementReference',
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
    'SyncCreativesAsyncInputRequired',
    'SyncCreativesAsyncSubmitted',
    'SyncCreativesAsyncWorking',
    'TMPIdentityMatch',
    'TagURL',
    'TagURLMacroDeclarationsItem',
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
