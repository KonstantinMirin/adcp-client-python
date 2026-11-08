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
from ._schemas.core.account import Compression as AccountReportingBucketCompression
from ._schemas.core.account import CreditLimit as AccountCreditLimit
from ._schemas.core.account import ObjUrl as AccountGovernanceAgentsItem
from ._schemas.core.account import ObjUrlMessageExpiresAt as AccountSetup
from ._schemas.core.account import ReportingBucket as AccountReportingBucket
from ._schemas.core.account_authorization import AccountAuthorization as AccountAuthorization
from ._schemas.core.account_authorization import StandardScope as StandardScope
from ._schemas.core.account_change import AccountChange as AccountChange
from ._schemas.core.account_change import Actor as AccountChangeActor
from ._schemas.core.account_change import ActorType as AccountChangeActorType
from ._schemas.core.account_change import Kind as AccountChangeOriginKind
from ._schemas.core.account_change import Origin as AccountChangeOrigin
from ._schemas.core.account_change import Repair as AccountChangeRepair
from ._schemas.core.account_change import Resource as AccountChangeResource
from ._schemas.core.account_change import Task as AccountChangeRepairTask
from ._schemas.core.account_change import UnavailableReason as AccountChangeRepairUnavailableReason
from ._schemas.core.account_change_recorded_webhook import AccountChangeRecordedWebhook as AccountChangeRecordedWebhook
from ._schemas.core.account_change_recorded_webhook import Resource as AccountChangeRecordedWebhookResource
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
from ._schemas.core.account_identity_change_preview import Area as AccountIdentityChangePreviewImpactArea
from ._schemas.core.account_identity_change_preview import BlockedImpacts as BlockedImpacts
from ._schemas.core.account_identity_change_preview import Impact as AccountIdentityChangePreviewImpact
from ._schemas.core.account_identity_change_preview import ImpactEffect as AccountIdentityChangePreviewImpactEffect
from ._schemas.core.account_identity_change_preview import NonblockingImpacts as NonblockingImpacts
from ._schemas.core.account_identity_change_preview import (
    NonblockingImpactsItem as AccountIdentityChangePreviewNonblockingImpactsItem,
)
from ._schemas.core.account_identity_change_preview import (
    NonblockingImpactsItemEffect as AccountIdentityChangePreviewNonblockingImpactsItemEffect,
)
from ._schemas.core.account_ref import AccountReference as AccountReference
from ._schemas.core.account_ref import AccountReferenceAccountId as AccountReferenceAccountId
from ._schemas.core.account_ref import AccountReferenceBrandOperator as AccountReferenceBrandOperator
from ._schemas.core.account_status_changed_webhook import AccountStatusChangedWebhook as AccountStatusChangedWebhook
from ._schemas.core.account_status_changed_webhook import ReasonCode as AccountStatusChangedWebhookReasonCode
from ._schemas.core.account_status_changed_webhook import Setup as AccountStatusChangedWebhookSetup
from ._schemas.core.account_timezone_capability import AccountSelection as AccountTimezoneCapabilityAccountSelection
from ._schemas.core.account_timezone_capability import AccountTimezoneCapability as AccountTimezoneCapability
from ._schemas.core.account_timezone_capability import Mode as AccountTimezoneCapabilityMode
from ._schemas.core.account_with_authorization import AccountWithAuthorization as AccountWithAuthorization
from ._schemas.core.activation_key import ActivationKey as ActivationKey
from ._schemas.core.activation_key import ActivationKeyKeyValue as ActivationKeyKeyValue
from ._schemas.core.activation_key import ActivationKeySegmentId as ActivationKeySegmentId
from ._schemas.core.ad_inventory_config import AdInventoryConfiguration as AdInventoryConfiguration
from ._schemas.core.agent_encryption_key import AgentEncryptionKey as AgentEncryptionKey
from ._schemas.core.agent_notification_config import AgentNotificationConfig as AgentNotificationConfig
from ._schemas.core.agent_notification_config_state import AgentNotificationConfigState as AgentNotificationConfigState
from ._schemas.core.agent_notification_config_state import Authentication as AgentNotificationConfigStateAuthentication
from ._schemas.core.agent_reporting_destination import AgentReportingDestination as AgentReportingDestination
from ._schemas.core.agent_reporting_destination import DatasetShareRecipient as DatasetShareRecipient
from ._schemas.core.agent_reporting_destination import FileTransferDestination as FileTransferDestination
from ._schemas.core.agent_reporting_destination import (
    WarehouseMaterializationDestination as WarehouseMaterializationDestination,
)
from ._schemas.core.agent_reporting_destination_state import Action as AgentReportingDestinationStateSetupAction
from ._schemas.core.agent_reporting_destination_state import (
    AgentReportingDestinationState as AgentReportingDestinationState,
)
from ._schemas.core.agent_reporting_destination_state import Setup as AgentReportingDestinationStateSetup
from ._schemas.core.agent_signing_key import AgentSigningKey as AgentSigningKey
from ._schemas.core.agent_webhook_challenge import AgentWebhookChallenge as AgentWebhookChallenge
from ._schemas.core.agent_webhook_challenge import EventTypesItem as AgentWebhookChallengeEventTypesItem
from ._schemas.core.agent_webhook_challenge import Mode as AgentWebhookChallengeDeliveryAuthMode
from ._schemas.core.agent_webhook_challenge import ObjModeCredentialFingerprint as AgentWebhookChallengeDeliveryAuth
from ._schemas.core.app_item import AppItem as AppItem
from ._schemas.core.app_item import Platform as AppItemPlatform
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
from ._schemas.core.assets.daast_asset import Location as DAASTAssetInlineMacroDeclarationsItemLocation
from ._schemas.core.assets.daast_asset import ObjLocation as DAASTAssetInlineMacroDeclarationsItem
from ._schemas.core.assets.daast_tracker_asset import DAASTTrackerAsset as DAASTTrackerAsset
from ._schemas.core.assets.display_tag_asset import DisplayTagAsset as DisplayTagAsset
from ._schemas.core.assets.display_tag_asset import InlineMarkup as InlineMarkup
from ._schemas.core.assets.display_tag_asset import (
    InlineMarkupMacroDeclarationsItem as InlineMarkupMacroDeclarationsItem,
)
from ._schemas.core.assets.display_tag_asset import (
    InlineMarkupMacroDeclarationsItemLocation as InlineMarkupMacroDeclarationsItemLocation,
)
from ._schemas.core.assets.display_tag_asset import LocationField as PairedRedirectMacroDeclarationsItemLocationField
from ._schemas.core.assets.display_tag_asset import MarkupType as InlineMarkupMarkupType
from ._schemas.core.assets.display_tag_asset import PairedRedirect as PairedRedirect
from ._schemas.core.assets.display_tag_asset import (
    PairedRedirectMacroDeclarationsItem as PairedRedirectMacroDeclarationsItem,
)
from ._schemas.core.assets.display_tag_asset import (
    PairedRedirectMacroDeclarationsItemLocation as PairedRedirectMacroDeclarationsItemLocation,
)
from ._schemas.core.assets.display_tag_asset import TagURL as TagURL
from ._schemas.core.assets.display_tag_asset import TagURLMacroDeclarationsItem as TagURLMacroDeclarationsItem
from ._schemas.core.assets.html_asset import Accessibility as HTMLAssetAccessibility
from ._schemas.core.assets.html_asset import HTMLAsset as HTMLAsset
from ._schemas.core.assets.image_asset import ImageAsset as ImageAsset
from ._schemas.core.assets.javascript_asset import JavaScriptAsset as JavaScriptAsset
from ._schemas.core.assets.markdown_asset import MarkdownAsset as MarkdownAsset
from ._schemas.core.assets.pixel_tracker_asset import Method as PixelTrackerAssetMethod
from ._schemas.core.assets.pixel_tracker_asset import PixelTrackerAsset as PixelTrackerAsset
from ._schemas.core.assets.published_post_asset import IdentityRef as PublishedPostAssetIdentityRef
from ._schemas.core.assets.published_post_asset import PublishedPostAsset as PublishedPostAsset
from ._schemas.core.assets.published_post_asset import (
    ReferenceAuthorization as PublishedPostAssetReferenceAuthorization,
)
from ._schemas.core.assets.published_post_asset import Status as PublishedPostAssetReferenceAuthorizationStatus
from ._schemas.core.assets.text_asset import TextAsset as TextAsset
from ._schemas.core.assets.url_asset import Location as URLAssetMacroDeclarationsItemLocation
from ._schemas.core.assets.url_asset import MacroDeclarationsItem as URLAssetMacroDeclarationsItem
from ._schemas.core.assets.url_asset import URLAsset as URLAsset
from ._schemas.core.assets.vast_asset import VASTAsset as VASTAsset
from ._schemas.core.assets.vast_asset import VASTAssetInline as VASTAssetInline
from ._schemas.core.assets.vast_asset import VASTAssetUrl as VASTAssetUrl
from ._schemas.core.assets.vast_tracker_asset import Target as VASTTrackerAssetTarget
from ._schemas.core.assets.vast_tracker_asset import VASTTrackerAsset as VASTTrackerAsset
from ._schemas.core.assets.video_asset import AudioBitDepth as VideoAssetAudioBitDepth
from ._schemas.core.assets.video_asset import ChromaSubsampling as VideoAssetChromaSubsampling
from ._schemas.core.assets.video_asset import ColorSpace as VideoAssetColorSpace
from ._schemas.core.assets.video_asset import HdrFormat as VideoAssetHdrFormat
from ._schemas.core.assets.video_asset import VideoAsset as VideoAsset
from ._schemas.core.assets.video_asset import VideoBitDepth as VideoAssetVideoBitDepth
from ._schemas.core.assets.webhook_asset import Security as WebhookAssetSecurity
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
from ._schemas.core.attestation_capabilities import AcceptedIssuersItem as AttestationCapabilitiesAcceptedIssuersItem
from ._schemas.core.attestation_capabilities import (
    AcceptedVerifiersItem as AttestationCapabilitiesAcceptedVerifiersItem,
)
from ._schemas.core.attestation_capabilities import AttestationCapabilities as AttestationCapabilities
from ._schemas.core.attestation_capabilities import (
    Authentication as AttestationCapabilitiesAcceptedIssuersItemResolversItemAuthentication,
)
from ._schemas.core.attestation_capabilities import (
    ResolversItem as AttestationCapabilitiesAcceptedIssuersItemResolversItem,
)
from ._schemas.core.attestation_capabilities import (
    SupportedDeliveryMethodsItem as AttestationCapabilitiesSupportedDeliveryMethodsItem,
)
from ._schemas.core.attestation_evaluation import ActionBinding as AttestationEvaluationActionBinding
from ._schemas.core.attestation_evaluation import AttestationEvaluation as AttestationEvaluation
from ._schemas.core.attestation_evaluation import Outcome as AttestationEvaluationOutcome
from ._schemas.core.attestation_issuer import AttestationAgentIssuer as AttestationAgentIssuer
from ._schemas.core.attestation_issuer import AttestationBrandIssuer as AttestationBrandIssuer
from ._schemas.core.attestation_issuer import AttestationIssuer as AttestationIssuer
from ._schemas.core.attestation_issuer import AttestationOriginIssuer as AttestationOriginIssuer
from ._schemas.core.attestation_reference import AttestationCredentialUriLocator as AttestationCredentialUriLocator
from ._schemas.core.attestation_reference import (
    AttestationIssuerCredentialIdLocator as AttestationIssuerCredentialIdLocator,
)
from ._schemas.core.attestation_reference import AttestationReference as AttestationReference
from ._schemas.core.attestation_reference import EmbeddedCredential as AttestationReferenceEmbeddedCredential
from ._schemas.core.attestation_reference import ValidityHint as AttestationReferenceValidityHint
from ._schemas.core.attestation_reference import VerifyAgent as AttestationReferenceVerifyAgent
from ._schemas.core.attestation_subject import AttestationAgentSubject as AttestationAgentSubject
from ._schemas.core.attestation_subject import AttestationBrandSubject as AttestationBrandSubject
from ._schemas.core.attestation_subject import AttestationResourceSubject as AttestationResourceSubject
from ._schemas.core.attestation_subject import AttestationSubject as AttestationSubject
from ._schemas.core.attribution_window import AttributionWindow as AttributionWindow
from ._schemas.core.attribution_window import PostClick as AttributionWindowPostClick
from ._schemas.core.attribution_window import PostView as AttributionWindowPostView
from ._schemas.core.audience_activation_method import AdCPAudienceSync as AdCPAudienceSync
from ._schemas.core.audience_activation_method import AudienceActivationMethod as AudienceActivationMethod
from ._schemas.core.audience_activation_method import (
    AudienceActivationMethodFileTransfer as AudienceActivationMethodFileTransfer,
)
from ._schemas.core.audience_activation_method import CleanRoom as CleanRoom
from ._schemas.core.audience_activation_method import ConsumerIdentitiesItem as DatasetQueryConsumerIdentitiesItem
from ._schemas.core.audience_activation_method import DatasetQuery as DatasetQuery
from ._schemas.core.audience_activation_method import DirectionsItem as FileTransferDirectionsItem
from ._schemas.core.audience_activation_method import ObjAgentUrl as TMPIdentityMatchBuyerAgent
from ._schemas.core.audience_activation_method import PlatformDistribution as PlatformDistribution
from ._schemas.core.audience_activation_method import TMPIdentityMatch as TMPIdentityMatch
from ._schemas.core.audience_characteristic import AudienceCharacteristic as AudienceCharacteristic
from ._schemas.core.audience_characteristic import Range as AudienceCharacteristicRange
from ._schemas.core.audience_characteristic import Taxonomy as AudienceCharacteristicTaxonomy
from ._schemas.core.audience_evidence import AttestationRefsItem as AudienceEvidenceAttestationRefsItem
from ._schemas.core.audience_evidence import AudienceEvidence as AudienceEvidence
from ._schemas.core.audience_evidence import Baseline as AudienceEvidenceBaseline
from ._schemas.core.audience_evidence import EvidenceType as AudienceEvidenceEvidenceType
from ._schemas.core.audience_evidence import Relationship as AudienceEvidenceRelationship
from ._schemas.core.audience_evidence import Subject as AudienceEvidenceAttestationRefsItemSubject
from ._schemas.core.audience_evidence import Unit as AudienceEvidenceUnit
from ._schemas.core.audience_evidence_pin import AudienceEvidencePin as AudienceEvidencePin
from ._schemas.core.audience_evidence_requirements import AudienceEvidenceRequirements as AudienceEvidenceRequirements
from ._schemas.core.audience_evidence_requirements import MaximumAge as AudienceEvidenceRequirementsMaximumAge
from ._schemas.core.audience_evidence_selection import (
    ActionBinding as AudienceEvidenceSelectionAttestationEvaluationsItemEvaluationActionBinding,
)
from ._schemas.core.audience_evidence_selection import (
    AttestationEvaluationsItem as AudienceEvidenceSelectionAttestationEvaluationsItem,
)
from ._schemas.core.audience_evidence_selection import AudienceEvidenceSelection as AudienceEvidenceSelection
from ._schemas.core.audience_evidence_selection import DecisionUse as AudienceEvidenceSelectionDecisionUse
from ._schemas.core.audience_evidence_selection import (
    Evaluation as AudienceEvidenceSelectionAttestationEvaluationsItemEvaluation,
)
from ._schemas.core.audience_member import AudienceMember as AudienceMember
from ._schemas.core.audience_member import UidsItem as AudienceMemberUidsItem
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
from ._schemas.core.bidding_policy import CostPer as BiddingPolicyCostPer
from ._schemas.core.bidding_policy import Roas as BiddingPolicyRoas
from ._schemas.core.bidding_policy import RoasStrength as BiddingPolicyRoasStrength
from ._schemas.core.bidding_policy_capability import BiddingPolicyCapability as BiddingPolicyCapability
from ._schemas.core.bidding_policy_capability import MaxBidWithCostPer as BiddingPolicyCapabilityMaxBidWithCostPer
from ._schemas.core.bidding_policy_capability import MaxBidWithRoas as BiddingPolicyCapabilityMaxBidWithRoas
from ._schemas.core.bidding_policy_capability import ModesItem as BiddingPolicyCapabilityPolicyProfileModesItem
from ._schemas.core.bidding_policy_capability import PolicyProfile as BiddingPolicyCapabilityPolicyProfile
from ._schemas.core.bidding_policy_capability import ScopeCapability as BiddingPolicyCapabilityScopeCapability
from ._schemas.core.brand_id import BrandID as BrandID
from ._schemas.core.brand_key import BrandKey as BrandKey
from ._schemas.core.brand_ref import BrandKitOverride as BrandReferenceBrandKitOverride
from ._schemas.core.brand_ref import BrandReference as BrandReference
from ._schemas.core.brand_ref import Colors as BrandReferenceBrandKitOverrideColors
from ._schemas.core.brand_ref import DataSubjectContestation as BrandReferenceDataSubjectContestation
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResult as BrandResponseAuthorizationResult,
)
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResultTrusted as BrandResponseAuthorizationResultTrusted,
)
from ._schemas.core.brand_response_authorization_result import (
    BrandResponseAuthorizationResultUntrusted as BrandResponseAuthorizationResultUntrusted,
)
from ._schemas.core.brand_response_authorization_result import Reason as BrandResponseAuthorizationResultReason
from ._schemas.core.brand_response_authorization_result import Trust as BrandResponseAuthorizationResultTrust
from ._schemas.core.budget_allocation import BudgetAllocation as BudgetAllocation
from ._schemas.core.budget_allocation import BudgetAllocationFixed as BudgetAllocationFixed
from ._schemas.core.budget_allocation import BudgetAllocationSellerOptimized as BudgetAllocationSellerOptimized
from ._schemas.core.budget_range import BudgetRange as BudgetRange
from ._schemas.core.business_entity import Address as BusinessEntityAddress
from ._schemas.core.business_entity import Bank as BusinessEntityBank
from ._schemas.core.business_entity import BusinessEntity as BusinessEntity
from ._schemas.core.business_entity import ContactsItem as BusinessEntityContactsItem
from ._schemas.core.business_entity import Role as BusinessEntityContactsItemRole
from ._schemas.core.cancellation_policy import CancellationFee as CancellationPolicyCancellationFee
from ._schemas.core.cancellation_policy import CancellationFeeType as CancellationPolicyCancellationFeeType
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
from ._schemas.core.canonical_forecast_point import Metrics as CanonicalForecastPointMetrics
from ._schemas.core.canonical_forecast_point import Viewability as CanonicalForecastPointViewability
from ._schemas.core.canonical_forecast_vendor_metric_value import (
    CanonicalForecastVendorMetricValue as CanonicalForecastVendorMetricValue,
)
from ._schemas.core.canonical_format_kind import CanonicalFormatKind as CanonicalFormatKind
from ._schemas.core.canonical_format_option import CanonicalFormatOption as CanonicalFormatOption
from ._schemas.core.canonical_format_option import FormatKind as CanonicalFormatOptionFormatKind
from ._schemas.core.canonical_measurement_terms import BillingMeasurement as CanonicalMeasurementTermsBillingMeasurement
from ._schemas.core.canonical_measurement_terms import CanonicalMeasurementTerms as CanonicalMeasurementTerms
from ._schemas.core.canonical_measurement_terms import MakegoodPolicy as CanonicalMeasurementTermsMakegoodPolicy
from ._schemas.core.canonical_media_buy_action import CanonicalMediaBuyAction as CanonicalMediaBuyAction
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionControlMediaBuy as CanonicalMediaBuyActionControlMediaBuy,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionControlMediaBuyAction as CanonicalMediaBuyActionControlMediaBuyAction,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionRefineProposals as CanonicalMediaBuyActionRefineProposals,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionRefineProposalsAction as CanonicalMediaBuyActionRefineProposalsAction,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionSyncCreatives as CanonicalMediaBuyActionSyncCreatives,
)
from ._schemas.core.canonical_media_buy_action import (
    CanonicalMediaBuyActionSyncCreativesAction as CanonicalMediaBuyActionSyncCreativesAction,
)
from ._schemas.core.canonical_media_buy_action_fields import (
    CanonicalMediaBuyActionFields as CanonicalMediaBuyActionFields,
)
from ._schemas.core.canonical_media_buy_features import CanonicalMediaBuyFeatures as CanonicalMediaBuyFeatures
from ._schemas.core.canonical_metric_qualifier import CanonicalMetricQualifier as CanonicalMetricQualifier
from ._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoal as CanonicalOptimizationGoal
from ._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoalEvent as CanonicalOptimizationGoalEvent
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalEventTarget as CanonicalOptimizationGoalEventTarget,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalMetric as CanonicalOptimizationGoalMetric,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalVendorMetric as CanonicalOptimizationGoalVendorMetric,
)
from ._schemas.core.canonical_optimization_goal import (
    CanonicalOptimizationGoalVendorMetricTarget as CanonicalOptimizationGoalVendorMetricTarget,
)
from ._schemas.core.canonical_optimization_goal import (
    EventSourcesItem as CanonicalOptimizationGoalEventEventSourcesItem,
)
from ._schemas.core.canonical_optimization_goal import Metric as CanonicalOptimizationGoalMetricMetric
from ._schemas.core.canonical_optimization_goal import TargetFrequency as CanonicalOptimizationGoalMetricTargetFrequency
from ._schemas.core.canonical_performance_standard import CanonicalPerformanceStandard as CanonicalPerformanceStandard
from ._schemas.core.canonical_placement import (
    CanonicalDoohPlacementAttributes as CanonicalProductPlacementCanonicalDoohPlacementAttributes,
)
from ._schemas.core.canonical_placement import (
    CanonicalDoohScreenResolution as CanonicalProductPlacementCanonicalDoohScreenResolution,
)
from ._schemas.core.canonical_placement import CanonicalProductPlacement as CanonicalProductPlacement
from ._schemas.core.canonical_placement import (
    CanonicalProductPlacementPublisherRef as CanonicalProductPlacementPublisherRef,
)
from ._schemas.core.canonical_placement import (
    CanonicalProductPlacementSellerInline as CanonicalProductPlacementSellerInline,
)
from ._schemas.core.canonical_pricing_option import CanonicalPricingOption as CanonicalPricingOption
from ._schemas.core.canonical_product import CanonicalProduct as CanonicalProduct
from ._schemas.core.canonical_product import CatalogMatch as CanonicalProductCatalogMatch
from ._schemas.core.canonical_product_action import CanonicalProductAction as CanonicalProductAction
from ._schemas.core.canonical_projection_ref import CanonicalProjectionReference as CanonicalProjectionReference
from ._schemas.core.canonical_projection_slot_override import (
    CanonicalProjectionSlotOverride as CanonicalProjectionSlotOverride,
)
from ._schemas.core.canonical_proposal import CanonicalProposal as CanonicalProposal
from ._schemas.core.canonical_proposal import Forecast as CanonicalProposalForecast
from ._schemas.core.canonical_proposal import ProposalKind as CanonicalProposalProposalKind
from ._schemas.core.canonical_proposal import TotalBudgetGuidance as CanonicalProposalTotalBudgetGuidance
from ._schemas.core.canonical_reporting_capabilities import (
    CanonicalReportingCapabilities as CanonicalReportingCapabilities,
)
from ._schemas.core.canonical_reporting_capabilities import (
    VendorMetricsItem as CanonicalReportingCapabilitiesVendorMetricsItem,
)
from ._schemas.core.canonical_reporting_commitment import CanonicalReportingCommitment as CanonicalReportingCommitment
from ._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitmentStandard as CanonicalReportingCommitmentStandard,
)
from ._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitmentVendor as CanonicalReportingCommitmentVendor,
)
from ._schemas.core.canvas_constraint import CanvasConstraint as CanvasConstraint
from ._schemas.core.canvas_constraint import Constraint as CanvasConstraintConstraint
from ._schemas.core.canvas_constraint import Region as CanvasConstraintRegion
from ._schemas.core.canvas_constraint import Unit as CanvasConstraintRegionUnit
from ._schemas.core.capabilities_changed_webhook import CapabilitiesChangedWebhook as CapabilitiesChangedWebhook
from ._schemas.core.capabilities_changed_webhook import Reason as CapabilitiesChangedWebhookReason
from ._schemas.core.catalog import Catalog as Catalog
from ._schemas.core.catalog import Category as Category
from ._schemas.core.catalog import Gtins as Gtins
from ._schemas.core.catalog import Ids as Ids
from ._schemas.core.catalog import Query as Query
from ._schemas.core.catalog import Tags as Tags
from ._schemas.core.catalog_field_mapping import CatalogFieldMapping as CatalogFieldMapping
from ._schemas.core.catalog_field_mapping import Transform as CatalogFieldMappingTransform
from ._schemas.core.catalog_item_availability_error import CatalogItemAvailabilityError as CatalogItemAvailabilityError
from ._schemas.core.catalog_item_availability_ref import (
    CatalogItemAvailabilityReference as CatalogItemAvailabilityReference,
)
from ._schemas.core.catalog_item_availability_state import Availability as CatalogItemAvailabilityStateAvailability
from ._schemas.core.catalog_item_availability_state import CatalogItemAvailabilityState as CatalogItemAvailabilityState
from ._schemas.core.catalog_item_availability_state import Status as CatalogItemAvailabilityStateStatus
from ._schemas.core.catalog_item_availability_update import (
    CatalogItemAvailabilityUpdate as CatalogItemAvailabilityUpdate,
)
from ._schemas.core.catalog_item_availability_update import Reason as CatalogItemAvailabilityUpdateReason
from ._schemas.core.catalog_item_availability_update_result import Action as CatalogItemAvailabilityUpdateResultAction
from ._schemas.core.catalog_item_availability_update_result import (
    CatalogItemAvailabilityUpdateResult as CatalogItemAvailabilityUpdateResult,
)
from ._schemas.core.catalog_item_availability_update_result import Status as CatalogItemAvailabilityUpdateResultStatus
from ._schemas.core.catalog_item_delivery_metrics import CatalogItemDeliveryMetrics as CatalogItemDeliveryMetrics
from ._schemas.core.catalog_item_reference_not_found_error import (
    CatalogItemReferenceNotFoundError as CatalogItemReferenceNotFoundError,
)
from ._schemas.core.catalog_selection import CatalogSelection as CatalogSelection
from ._schemas.core.catchment import Catchment as Catchment
from ._schemas.core.collection import Collection as Collection
from ._schemas.core.collection import RelatedCollectionsItem as CollectionRelatedCollectionsItem
from ._schemas.core.collection_delivery_metrics import CollectionDeliveryMetrics as CollectionDeliveryMetrics
from ._schemas.core.collection_distribution import CollectionDistribution as CollectionDistribution
from ._schemas.core.collection_distribution import IdentifiersItem as CollectionDistributionIdentifiersItem
from ._schemas.core.collection_list_ref import CollectionListReference as CollectionListReference
from ._schemas.core.collection_property_delivery_metrics import (
    CollectionPropertyDeliveryMetrics as CollectionPropertyDeliveryMetrics,
)
from ._schemas.core.collection_ref import CollectionReference as CollectionReference
from ._schemas.core.collection_selection import CollectionSelection as CollectionSelection
from ._schemas.core.collection_selection import CollectionsItem as SelectedCollectionsCollectionsItem
from ._schemas.core.collection_selection import ProductDefaultCollections as ProductDefaultCollections
from ._schemas.core.collection_selection import SelectedCollections as SelectedCollections
from ._schemas.core.collection_selector import CollectionSelector as CollectionSelector
from ._schemas.core.committed_metric import CommittedMetric as CommittedMetric
from ._schemas.core.committed_metric import CommittedMetricStandard as CommittedMetricStandard
from ._schemas.core.committed_metric import CommittedMetricVendor as CommittedMetricVendor
from ._schemas.core.committed_metric import Qualifier as CommittedMetricVendorQualifier
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
from ._schemas.core.creative_assignment import RotationMode as CreativeAssignmentRotationMode
from ._schemas.core.creative_brief import Compliance as CreativeBriefCompliance
from ._schemas.core.creative_brief import CreativeBrief as CreativeBrief
from ._schemas.core.creative_brief import Messaging as CreativeBriefMessaging
from ._schemas.core.creative_brief import Objective as CreativeBriefObjective
from ._schemas.core.creative_brief import RequiredDisclosuresItem as CreativeBriefComplianceRequiredDisclosuresItem
from ._schemas.core.creative_consumption import CreativeConsumption as CreativeConsumption
from ._schemas.core.creative_delivery_metrics import CreativeDeliveryMetrics as CreativeDeliveryMetrics
from ._schemas.core.creative_filters import CreativeFilters as CreativeFilters
from ._schemas.core.creative_item import CreativeItem as CreativeItem
from ._schemas.core.creative_item import CreativeItemMedia as CreativeItemMedia
from ._schemas.core.creative_item import CreativeItemText as CreativeItemText
from ._schemas.core.creative_locale_policy import CreativeLocalePolicy as CreativeLocalePolicy
from ._schemas.core.creative_localization import CreativeLocalization as CreativeLocalization
from ._schemas.core.creative_localization import Source as CreativeLocalizationSource
from ._schemas.core.creative_localization import TargetVariantsItem as CreativeLocalizationTargetVariantsItem
from ._schemas.core.creative_localization_readback import CreativeLocalizationReadback as CreativeLocalizationReadback
from ._schemas.core.creative_localization_readback import (
    LocaleFallbacksItem as CreativeLocalizationReadbackLocaleFallbacksItem,
)
from ._schemas.core.creative_localization_readback import ResolvedAssets as ResolvedAssets
from ._schemas.core.creative_localization_readback import SourceLocalizationReadback as SourceLocalizationReadback
from ._schemas.core.creative_localization_readback import TargetLocalizationReadback as TargetLocalizationReadback
from ._schemas.core.creative_localization_readback import (
    UnmatchedLocaleAction as CreativeLocalizationReadbackUnmatchedLocaleAction,
)
from ._schemas.core.creative_manifest import CreativeManifest as CreativeManifest
from ._schemas.core.creative_operation_format_declaration import (
    CreativeOperationFormatDeclaration as CreativeOperationFormatDeclaration,
)
from ._schemas.core.creative_policy import AcceptedVerifiersItem as CreativePolicyAcceptedVerifiersItem
from ._schemas.core.creative_policy import CreativePolicy as CreativePolicy
from ._schemas.core.creative_policy import ProvenanceRequirements as CreativePolicyProvenanceRequirements
from ._schemas.core.creative_representation import CreativeRepresentation as CreativeRepresentation
from ._schemas.core.creative_representation import Source as CreativeRepresentationSource
from ._schemas.core.creative_representation_set import CreativeRepresentationSet as CreativeRepresentationSet
from ._schemas.core.creative_revision_id import CreativeRevisionID as CreativeRevisionID
from ._schemas.core.creative_variable import CreativeVariable as CreativeVariable
from ._schemas.core.creative_variable import VariableType as CreativeVariableVariableType
from ._schemas.core.creative_variant import CreativeVariant as CreativeVariant
from ._schemas.core.creative_variant import GenerationContext as CreativeVariantGenerationContext
from ._schemas.core.creative_variant import GenerationContextArtifact as CreativeVariantGenerationContextArtifact
from ._schemas.core.currency_code import CurrencyCode as CurrencyCode
from ._schemas.core.daast_tracker_constraints import DaastEvent as DAASTTrackerConstraintsDaastEvent
from ._schemas.core.daast_tracker_constraints import DaastOffset as DaastOffset
from ._schemas.core.daast_tracker_constraints import DaastTarget as DAASTTrackerConstraintsDaastTarget
from ._schemas.core.daast_tracker_constraints import DAASTTrackerConstraints as DAASTTrackerConstraints
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
from ._schemas.core.deadline_policy import MaterialStagesItem as DeadlinePolicyMaterialStagesItem
from ._schemas.core.delivery_breakdown_controls import DeliveryBreakdownControls as DeliveryBreakdownControls
from ._schemas.core.delivery_forecast import DeliveryForecast as DeliveryForecast
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregate as DeliveryMetricAggregate
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregateStandard as DeliveryMetricAggregateStandard
from ._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregateVendor as DeliveryMetricAggregateVendor
from ._schemas.core.delivery_metrics import ByActionSourceItem as DeliveryMetricsByActionSourceItem
from ._schemas.core.delivery_metrics import ByEventTypeItem as DeliveryMetricsByEventTypeItem
from ._schemas.core.delivery_metrics import DeliveryMetrics as DeliveryMetrics
from ._schemas.core.delivery_metrics import DoohMetrics as DeliveryMetricsDoohMetrics
from ._schemas.core.delivery_metrics import EstimationBasis as DeliveryMetricsOohMetricsEstimationBasis
from ._schemas.core.delivery_metrics import IdentifiersItem as DeliveryMetricsOohMetricsPanelsItemIdentifiersItem
from ._schemas.core.delivery_metrics import IdType as DeliveryMetricsOohMetricsPanelsItemIdentifiersItemIdType
from ._schemas.core.delivery_metrics import Kind as DeliveryMetricsReachWindowKind
from ._schemas.core.delivery_metrics import ObjKindPeriod as DeliveryMetricsReachWindow
from ._schemas.core.delivery_metrics import OohMetrics as DeliveryMetricsOohMetrics
from ._schemas.core.delivery_metrics import PanelsItem as DeliveryMetricsOohMetricsPanelsItem
from ._schemas.core.delivery_metrics import Period as DeliveryMetricsReachWindowPeriod
from ._schemas.core.delivery_metrics import PostingsItem as DeliveryMetricsOohMetricsPostingsItem
from ._schemas.core.delivery_metrics import PostingsItemEventType as DeliveryMetricsOohMetricsPostingsItemEventType
from ._schemas.core.delivery_metrics import QuartileData as DeliveryMetricsQuartileData
from ._schemas.core.delivery_metrics import TimeBasedViewsItem as DeliveryMetricsTimeBasedViewsItem
from ._schemas.core.delivery_metrics import VenueBreakdownItem as DeliveryMetricsDoohMetricsVenueBreakdownItem
from ._schemas.core.delivery_metrics import Viewability as DeliveryMetricsViewability
from ._schemas.core.delivery_metrics import (
    ViewedSecondsHistogramItem as DeliveryMetricsViewabilityViewedSecondsHistogramItem,
)
from ._schemas.core.delivery_metrics import (
    ViewedSecondsPercentiles as DeliveryMetricsViewabilityViewedSecondsPercentiles,
)
from ._schemas.core.delivery_provider import DeliveryProvider as DeliveryProvider
from ._schemas.core.delivery_recipient import DeliveryRecipient as DeliveryRecipient
from ._schemas.core.demographic_age_range import DemographicAgeRange as DemographicAgeRange
from ._schemas.core.demographic_predicate import DemographicPredicate as DemographicPredicate
from ._schemas.core.demographic_reporting_capability import Age as DemographicReportingCapabilityAge
from ._schemas.core.demographic_reporting_capability import (
    DemographicReportingCapability as DemographicReportingCapability,
)
from ._schemas.core.demographic_reporting_capability import (
    IntervalsItem as DemographicReportingCapabilityAgeIntervalsItem,
)
from ._schemas.core.demographic_reporting_capability import (
    ReportingModesItem as DemographicReportingCapabilityAgeReportingModesItem,
)
from ._schemas.core.demographic_targeting_capability import Age as DemographicTargetingCapabilityAge
from ._schemas.core.demographic_targeting_capability import (
    DemographicTargetingCapability as DemographicTargetingCapability,
)
from ._schemas.core.demographic_targeting_capability import (
    ExecutionModesItem as DemographicTargetingCapabilityAgeExecutionModesItem,
)
from ._schemas.core.demographic_targeting_capability import (
    IntervalsItem as DemographicTargetingCapabilityAgeIntervalsItem,
)
from ._schemas.core.demographic_targeting_capability import (
    UnknownHandling as DemographicTargetingCapabilityAgeUnknownHandling,
)
from ._schemas.core.demographic_targeting_intent import Age as DemographicTargetingIntentAge
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
from ._schemas.core.destination_item import DestinationType as DestinationItemDestinationType
from ._schemas.core.destination_item import ObjLatLng as DestinationItemLocation
from ._schemas.core.diagnostic_issue import DiagnosticIssue as DiagnosticIssue
from ._schemas.core.diagnostic_issue import Severity as DiagnosticIssueSeverity
from ._schemas.core.domain_name import DomainName as DomainName
from ._schemas.core.downstream_connection_requirement import (
    ConnectionType as DownstreamConnectionRequirementConnectionType,
)
from ._schemas.core.downstream_connection_requirement import (
    DownstreamConnectionRequirement as DownstreamConnectionRequirement,
)
from ._schemas.core.downstream_connection_requirement import ResourceRef as DownstreamConnectionRequirementResourceRef
from ._schemas.core.downstream_connection_requirement import Scope as DownstreamConnectionRequirementScope
from ._schemas.core.downstream_connection_requirement import Status as DownstreamConnectionRequirementStatus
from ._schemas.core.duration import Duration as Duration
from ._schemas.core.education_item import DegreeType as EducationItemDegreeType
from ._schemas.core.education_item import EducationItem as EducationItem
from ._schemas.core.education_item import Level as EducationItemLevel
from ._schemas.core.education_item import Modality as EducationItemModality
from ._schemas.core.error import BuyerReason as ErrorBuyerReason
from ._schemas.core.error import DiscriminatorItem as ErrorIssuesItemDiscriminatorItem
from ._schemas.core.error import Error as Error
from ._schemas.core.error import IssuesItem as ErrorIssuesItem
from ._schemas.core.error import Recovery as ErrorRecovery
from ._schemas.core.error import Source as ErrorSource
from ._schemas.core.evaluator_spec import Direction as EvaluatorSpecRankByItemDirection
from ._schemas.core.evaluator_spec import EvalBudget as EvaluatorSpecEvalBudget
from ._schemas.core.evaluator_spec import EvaluatorSpec as EvaluatorSpec
from ._schemas.core.evaluator_spec import EvaluatorSpecAgentUrl as EvaluatorSpecAgentUrl
from ._schemas.core.evaluator_spec import EvaluatorSpecEvaluatorId as EvaluatorSpecEvaluatorId
from ._schemas.core.evaluator_spec import EvaluatorSpecExemplars as EvaluatorSpecExemplars
from ._schemas.core.evaluator_spec import RankByItem as EvaluatorSpecRankByItem
from ._schemas.core.event import Event as Event
from ._schemas.core.event_custom_data import ContentsItem as EventCustomDataContentsItem
from ._schemas.core.event_custom_data import EventCustomData as EventCustomData
from ._schemas.core.event_source_health import Detail as EventSourceHealthDetail
from ._schemas.core.event_source_health import EventSourceHealth as EventSourceHealth
from ._schemas.core.event_surface import Category as EventSurfaceCategory
from ._schemas.core.event_surface import EventSurface as EventSurface
from ._schemas.core.experimental_feature_id import ExperimentalFeatureID as ExperimentalFeatureID
from ._schemas.core.ext import ExtensionObject as ExtensionObject
from ._schemas.core.feature_requirement import FeatureRequirement as FeatureRequirement
from ._schemas.core.feature_requirement import IfNotCovered as FeatureRequirementIfNotCovered
from ._schemas.core.flight_item import FlightItem as FlightItem
from ._schemas.core.flight_item import FlightItemDestination as FlightItemDestination
from ._schemas.core.flight_item import Origin as FlightItemOrigin
from ._schemas.core.forecast_dimension_audience import AudienceForecastDimension as AudienceForecastDimension
from ._schemas.core.forecast_dimension_device_platform import (
    DevicePlatformForecastDimension as DevicePlatformForecastDimension,
)
from ._schemas.core.forecast_dimension_device_type import DeviceTypeForecastDimension as DeviceTypeForecastDimension
from ._schemas.core.forecast_dimension_geo import GeoForecastDimension as GeoForecastDimension
from ._schemas.core.forecast_dimension_placement import PlacementForecastDimension as PlacementForecastDimension
from ._schemas.core.forecast_dimension_signal import SignalForecastDimension as SignalForecastDimension
from ._schemas.core.forecast_dimension_signal import SignalForecastDimensionPresence as SignalForecastDimensionPresence
from ._schemas.core.forecast_dimension_time import TimeForecastDimension as TimeForecastDimension
from ._schemas.core.forecast_point import CoverageRate as ForecastPointMetricsCoverageRate
from ._schemas.core.forecast_point import ForecastPoint as ForecastPoint
from ._schemas.core.forecast_point import Metrics as ForecastPointMetrics
from ._schemas.core.forecast_point import Viewability as ForecastPointViewability
from ._schemas.core.forecast_point import ViewableRate as ForecastPointViewabilityViewableRate
from ._schemas.core.forecast_point_dimensions import ForecastPointDimensions as ForecastPointDimensions
from ._schemas.core.forecast_range import ForecastRange as ForecastRange
from ._schemas.core.forecast_rate_range import ForecastRateRange as ForecastRateRange
from ._schemas.core.forecast_vendor_metric_value import ForecastVendorMetricValue as ForecastVendorMetricValue
from ._schemas.core.format import Accessibility as FormatAccessibility
from ._schemas.core.format import AssetsItemIndividual as AssetsItemIndividual
from ._schemas.core.format import BaseGroupAsset as FormatBaseGroupAsset
from ._schemas.core.format import BaseIndividualAsset as FormatBaseIndividualAsset
from ._schemas.core.format import Dimensions as FormatRendersItemDimensions
from ._schemas.core.format import DisclosureCapabilitiesItem as FormatDisclosureCapabilitiesItem
from ._schemas.core.format import Format as Format
from ._schemas.core.format import FormatCard as FormatFormatCard
from ._schemas.core.format import FormatCardDetailed as FormatFormatCardDetailed
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
from ._schemas.core.format import RendersItem as FormatRendersItem
from ._schemas.core.format import RendersItemDimensions as RendersItemDimensions
from ._schemas.core.format import RendersItemParametersFromFormatId as RendersItemParametersFromFormatId
from ._schemas.core.format import RepeatableGroupAsset as RepeatableGroupAsset
from ._schemas.core.format import Responsive as FormatRendersItemDimensionsResponsive
from ._schemas.core.format import SelectionMode as RepeatableGroupAssetSelectionMode
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
from ._schemas.core.frequency_cap import Suppress as FrequencyCapSuppress
from ._schemas.core.frequency_cap import Window as FrequencyCapWindow
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
from ._schemas.core.geo_place_catalog_entry import Status as GeographicPlaceCatalogEntryStatus
from ._schemas.core.geo_place_requirement import CatalogRequirement as GeographicPlaceRequirementCatalogRequirement
from ._schemas.core.geo_place_requirement import GeographicPlaceRequirement as GeographicPlaceRequirement
from ._schemas.core.geo_place_resolver import Auth as GeographicPlaceResolverAuth
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
from ._schemas.core.hotel_item import Address as HotelItemAddress
from ._schemas.core.hotel_item import HotelItem as HotelItem
from ._schemas.core.https_url import HTTPSURL as HTTPSURL
from ._schemas.core.iana_timezone import IANATimezoneIdentifier as IANATimezoneIdentifier
from ._schemas.core.idempotency_key import IdempotencyKey as IdempotencyKey
from ._schemas.core.identifier import Identifier as Identifier
from ._schemas.core.impairment import Impairment as Impairment
from ._schemas.core.impairment import ResourceType as ImpairmentResourceType
from ._schemas.core.impairment import Transition as ImpairmentTransition
from ._schemas.core.indicator import Indicator as Indicator
from ._schemas.core.indicator_bearing import IndicatorBearingResourceState as IndicatorBearingResourceState
from ._schemas.core.indicator_scope import IndicatorScope as IndicatorScope
from ._schemas.core.indicators_changed_webhook import ChangeKind as IndicatorsChangedWebhookChangeKind
from ._schemas.core.indicators_changed_webhook import IndicatorsChangedWebhook as IndicatorsChangedWebhook
from ._schemas.core.indicators_changed_webhook import RelationshipKind as IndicatorsChangedWebhookRelationshipKind
from ._schemas.core.industry_identifier import IndustryIdentifier as IndustryIdentifier
from ._schemas.core.insertion_order import InsertionOrder as InsertionOrder
from ._schemas.core.insertion_order import Terms as InsertionOrderTerms
from ._schemas.core.insertion_order import TermsPaymentTerms as InsertionOrderTermsPaymentTerms
from ._schemas.core.insertion_order import TotalBudget as InsertionOrderTermsTotalBudget
from ._schemas.core.installment import DerivativeOf as InstallmentDerivativeOf
from ._schemas.core.installment import Installment as Installment
from ._schemas.core.installment_deadlines import InstallmentDeadlines as InstallmentDeadlines
from ._schemas.core.installment_delivery_metrics import InstallmentDeliveryMetrics as InstallmentDeliveryMetrics
from ._schemas.core.installment_property_delivery_metrics import (
    InstallmentPropertyDeliveryMetrics as InstallmentPropertyDeliveryMetrics,
)
from ._schemas.core.installment_ref import InstallmentReference as InstallmentReference
from ._schemas.core.inventory_list_application import CollectionListApplication as CollectionListApplication
from ._schemas.core.inventory_list_application import CollectionListApplicationEffect as CollectionListApplicationEffect
from ._schemas.core.inventory_list_application import (
    CollectionListApplicationSummary as CollectionListApplicationSummary,
)
from ._schemas.core.inventory_list_application import InventoryListApplication as InventoryListApplication
from ._schemas.core.inventory_list_application import PropertyListApplication as PropertyListApplication
from ._schemas.core.inventory_list_application import PropertyListApplicationEffect as PropertyListApplicationEffect
from ._schemas.core.inventory_list_application import PropertyListApplicationSummary as PropertyListApplicationSummary
from ._schemas.core.job_item import EmploymentType as JobItemEmploymentType
from ._schemas.core.job_item import ExperienceLevel as JobItemExperienceLevel
from ._schemas.core.job_item import JobItem as JobItem
from ._schemas.core.job_item import Period as JobItemSalaryPeriod
from ._schemas.core.job_item import Salary as JobItemSalary
from ._schemas.core.keyword_delivery_metrics import KeywordDeliveryMetrics as KeywordDeliveryMetrics
from ._schemas.core.keyword_target import KeywordTarget as KeywordTarget
from ._schemas.core.limited_series import LimitedSeries as LimitedSeries
from ._schemas.core.locale_tag import LanguageTag as LanguageTag
from ._schemas.core.localized_creative_asset import LocalizedCreativeAsset as LocalizedCreativeAsset
from ._schemas.core.macro_bearing_url import MacroBearingURL as MacroBearingURL
from ._schemas.core.macro_declaration import Location as MacroDeclarationLocation
from ._schemas.core.macro_declaration import LocationField as MacroDeclarationLocationField
from ._schemas.core.macro_declaration import MacroDeclaration as MacroDeclaration
from ._schemas.core.macro_declaration import UnavailableBehavior as MacroDeclarationUnavailableBehavior
from ._schemas.core.macro_encoding import Kind as MacroEncodingKind
from ._schemas.core.macro_encoding import MacroEncoding as MacroEncoding
from ._schemas.core.macro_resolution_capability import MacroProcessingCapability as MacroProcessingCapability
from ._schemas.core.macro_resolution_capability import MappingStatus as MacroProcessingCapabilityMappingStatus
from ._schemas.core.macro_resolution_capability import Operation as MacroProcessingCapabilityOperation
from ._schemas.core.macro_resolution_result import MacroResolutionResult as MacroResolutionResult
from ._schemas.core.macro_resolution_result import Status as MacroResolutionResultStatus
from ._schemas.core.macro_translation_target import MacroTranslationTarget as MacroTranslationTarget
from ._schemas.core.material_deadline import MaterialDeadline as MaterialDeadline
from ._schemas.core.mcp_webhook_payload import MCPWebhookPayload as MCPWebhookPayload
from ._schemas.core.measurement_readiness import MeasurementReadiness as MeasurementReadiness
from ._schemas.core.measurement_terms import BillingMeasurement as MeasurementTermsBillingMeasurement
from ._schemas.core.measurement_terms import MakegoodPolicy as MeasurementTermsMakegoodPolicy
from ._schemas.core.measurement_terms import MeasurementTerms as MeasurementTerms
from ._schemas.core.measurement_window import MeasurementWindow as MeasurementWindow
from ._schemas.core.media_buy import Bidding as MediaBuyBidding
from ._schemas.core.media_buy import MediaBuy as MediaBuy
from ._schemas.core.media_buy import ObjCanceledAtCanceledByReason as MediaBuyCancellation
from ._schemas.core.media_buy_available_action import MediaBuyAvailableAction as MediaBuyAvailableAction
from ._schemas.core.media_buy_available_action import Task as MediaBuyAvailableActionTask
from ._schemas.core.media_buy_available_action_id import MediaBuyAvailableActionID as MediaBuyAvailableActionID
from ._schemas.core.media_buy_change_term_id import MediaBuyChangeTermID as MediaBuyChangeTermID
from ._schemas.core.media_buy_features import MediaBuyFeatures as MediaBuyFeatures
from ._schemas.core.media_buy_features import MediaBuyFeaturesBiddingPolicy as MediaBuyFeaturesBiddingPolicy
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
from ._schemas.core.notification_config import Authentication as NotificationConfigAuthentication
from ._schemas.core.notification_config import EventTypesItem as NotificationConfigEventTypesItem
from ._schemas.core.notification_config import NotificationConfig as NotificationConfig
from ._schemas.core.notification_config import ProductPayloadView as NotificationConfigProductPayloadView
from ._schemas.core.offering import GeoTargets as OfferingGeoTargets
from ._schemas.core.offering import MetrosItem as OfferingGeoTargetsMetrosItem
from ._schemas.core.offering import Offering as Offering
from ._schemas.core.offering_asset_group import OfferingAssetGroup as OfferingAssetGroup
from ._schemas.core.operator_identity import OperatorIdentity as OperatorIdentity
from ._schemas.core.operator_unit import OperatorUnit as OperatorUnit
from ._schemas.core.opportunity_context import CloseReason as OpportunityContextCloseReason
from ._schemas.core.opportunity_context import Intent as OpportunityContextIntent
from ._schemas.core.opportunity_context import OpportunityContext as OpportunityContext
from ._schemas.core.opportunity_context import Phase as OpportunityContextPhase
from ._schemas.core.opportunity_context import Status as OpportunityContextStatus
from ._schemas.core.optimization_goal import EventSourcesItem as OptimizationGoalEventEventSourcesItem
from ._schemas.core.optimization_goal import OptimizationGoal as OptimizationGoal
from ._schemas.core.optimization_goal import OptimizationGoalEvent as OptimizationGoalEvent
from ._schemas.core.optimization_goal import (
    OptimizationGoalEventAttributionWindow as OptimizationGoalEventAttributionWindow,
)
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
from ._schemas.core.optimization_goal import OptimizationMetric as OptimizationGoalMetricMetric
from ._schemas.core.optimization_goal import TargetFrequency as OptimizationGoalMetricTargetFrequency
from ._schemas.core.optimization_goal import TargetMaximizeValue as TargetMaximizeValue
from ._schemas.core.optimization_goal import TargetPerAdSpend as TargetPerAdSpend
from ._schemas.core.optimization_goal import Vendor as OptimizationGoalMetricVendor
from ._schemas.core.optimization_goal import Window as OptimizationGoalMetricTargetFrequencyWindow
from ._schemas.core.outcome_measurement import OutcomeMeasurement as OutcomeMeasurement
from ._schemas.core.outcome_measurement import Window as OutcomeMeasurementWindow
from ._schemas.core.outcome_target_cost_per import OutcomeTargetCostPer as OutcomeTargetCostPer
from ._schemas.core.overlay import Bounds as OverlayBounds
from ._schemas.core.overlay import Overlay as Overlay
from ._schemas.core.overlay import Unit as OverlayBoundsUnit
from ._schemas.core.overlay import Visual as OverlayVisual
from ._schemas.core.package import Bidding as PackageBidding
from ._schemas.core.package import Cancellation as PackageCancellation
from ._schemas.core.package import Package as Package
from ._schemas.core.package_delivery_metric_value import PackageDeliveryMetricValue as PackageDeliveryMetricValue
from ._schemas.core.package_delivery_metric_value import Qualifier as PackageDeliveryMetricValueQualifier
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
from ._schemas.core.package_format_snapshot import PlacementRefsItem as PackageFormatSnapshotPlacementRefsItem
from ._schemas.core.package_signal_targeting import PackageSignalTargeting as PackageSignalTargeting
from ._schemas.core.package_signal_targeting import PackageSignalTargetingBinary as PackageSignalTargetingBinary
from ._schemas.core.package_signal_targeting import (
    PackageSignalTargetingCategorical as PackageSignalTargetingCategorical,
)
from ._schemas.core.package_signal_targeting import PackageSignalTargetingNumeric as PackageSignalTargetingNumeric
from ._schemas.core.package_signal_targeting_group import Operator as PackageSignalTargetingGroupOperator
from ._schemas.core.package_signal_targeting_group import PackageSignalTargetingGroup as PackageSignalTargetingGroup
from ._schemas.core.package_signal_targeting_groups import Operator as PackageSignalTargetingGroupsOperator
from ._schemas.core.package_signal_targeting_groups import PackageSignalTargetingGroups as PackageSignalTargetingGroups
from ._schemas.core.package_targeting_resolution import PackageTargetingResolution as PackageTargetingResolution
from ._schemas.core.pagination_request import PaginationRequest as PaginationRequest
from ._schemas.core.pagination_response import PaginationResponse as PaginationResponse
from ._schemas.core.performance_feedback import PerformanceFeedback as PerformanceFeedback
from ._schemas.core.performance_feedback import Status as PerformanceFeedbackStatus
from ._schemas.core.performance_feedback_assertion import (
    ConfidenceInterval as PerformanceFeedbackAssertionEvidenceConfidenceInterval,
)
from ._schemas.core.performance_feedback_assertion import Evidence as PerformanceFeedbackAssertionEvidence
from ._schemas.core.performance_feedback_assertion import PerformanceFeedbackAssertion as PerformanceFeedbackAssertion
from ._schemas.core.performance_feedback_metric import PerformanceFeedbackMetric as PerformanceFeedbackMetric
from ._schemas.core.performance_feedback_metric import (
    PerformanceFeedbackMetricStandard as PerformanceFeedbackMetricStandard,
)
from ._schemas.core.performance_feedback_metric import (
    PerformanceFeedbackMetricVendor as PerformanceFeedbackMetricVendor,
)
from ._schemas.core.performance_standard import PerformanceStandard as PerformanceStandard
from ._schemas.core.placement import Kind as PlacementKind
from ._schemas.core.placement import Mode as PlacementMode
from ._schemas.core.placement import Placement as Placement
from ._schemas.core.placement import ProductDoohPlacementAttributes as PlacementProductDoohPlacementAttributes
from ._schemas.core.placement import ProductDoohScreenResolution as PlacementProductDoohScreenResolution
from ._schemas.core.placement_definition import FormatOptionsItemFormatOptionId as FormatOptionsItemFormatOptionId
from ._schemas.core.placement_definition import IdentifiersItem as PlacementDefinitionIdentifiersItem
from ._schemas.core.placement_definition import PlacementDefinition as PlacementDefinition
from ._schemas.core.placement_definition import (
    PublisherDoohPlacementAttributes as PlacementDefinitionPublisherDoohPlacementAttributes,
)
from ._schemas.core.placement_definition import (
    PublisherDoohScreenResolution as PlacementDefinitionPublisherDoohScreenResolution,
)
from ._schemas.core.placement_delivery_metrics import PlacementDeliveryMetrics as PlacementDeliveryMetrics
from ._schemas.core.placement_evidence import PlacementEvidence as PlacementEvidence
from ._schemas.core.placement_identity import PlacementIdentity as PlacementIdentity
from ._schemas.core.placement_identity import PublisherCatalogPlacementIdentity as PublisherCatalogPlacementIdentity
from ._schemas.core.placement_identity import SellerInlinePlacementIdentity as SellerInlinePlacementIdentity
from ._schemas.core.placement_presentation import BoxDecoration as PlacementPresentationDocumentBoxDecoration
from ._schemas.core.placement_presentation import Canvas as PlacementPresentationDocumentCanvas
from ._schemas.core.placement_presentation import Color as Color
from ._schemas.core.placement_presentation import CreativeSlot as PlacementPresentationDocumentCreativeSlot
from ._schemas.core.placement_presentation import CreativeSlotFit as PlacementPresentationDocumentCreativeSlotFit
from ._schemas.core.placement_presentation import ImageDecoration as PlacementPresentationDocumentImageDecoration
from ._schemas.core.placement_presentation import ImageDecorationFit as PlacementPresentationDocumentImageDecorationFit
from ._schemas.core.placement_presentation import ImageRef as PlacementPresentationDocumentImageDecorationImageRef
from ._schemas.core.placement_presentation import Layer as PlacementPresentationDocumentLayer
from ._schemas.core.placement_presentation import PlacementPresentationDocument as PlacementPresentationDocument
from ._schemas.core.placement_presentation import Rectangle as PlacementPresentationDocumentRectangle
from ._schemas.core.placement_presentation import TextDecoration as PlacementPresentationDocumentTextDecoration
from ._schemas.core.placement_property_delivery_metrics import (
    PlacementPropertyDeliveryMetrics as PlacementPropertyDeliveryMetrics,
)
from ._schemas.core.placement_ref import PlacementReference as PlacementReference
from ._schemas.core.placement_selection import PlacementSelection as PlacementSelection
from ._schemas.core.placement_selection import ProductDefaultPlacements as ProductDefaultPlacements
from ._schemas.core.placement_selection import SelectedPlacements as SelectedPlacements
from ._schemas.core.planned_delivery import Bidding as PlannedDeliveryBidding
from ._schemas.core.planned_delivery import Geo as PlannedDeliveryGeo
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
from ._schemas.core.postal_area import System as PostalAreaBranch9System
from ._schemas.core.postal_area_support import PostalAreaSupport as PostalAreaSupport
from ._schemas.core.postal_area_support import PostalAreaSupportValueItem as PostalAreaSupportValueItem
from ._schemas.core.postal_country_system import CaPostalCodeSystem as PostalCountrySystemCASystem
from ._schemas.core.postal_country_system import Country as PostalCountrySystemPlzCountry
from ._schemas.core.postal_country_system import GBPostalCodeSystem as PostalCountrySystemGBSystem
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
from ._schemas.core.postal_country_system import System as PostalCountrySystemBranch9System
from ._schemas.core.postal_country_system import USPostalCodeSystem as PostalCountrySystemUSSystem
from ._schemas.core.presentation_ref import PlacementPresentationReference as PlacementPresentationReference
from ._schemas.core.preview_provider import PublisherDesignatedPreviewProvider as PublisherDesignatedPreviewProvider
from ._schemas.core.preview_provider import RoutesItem as PublisherDesignatedPreviewProviderRoutesItem
from ._schemas.core.preview_renderer_metadata import PreviewRendererMetadata as PreviewRendererMetadata
from ._schemas.core.preview_renderer_metadata import RenderingOrigin as PreviewRendererMetadataRenderingOrigin
from ._schemas.core.price import Period as PricePeriod
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
from ._schemas.core.principal_changed_webhook import Reason as PrincipalChangedWebhookReason
from ._schemas.core.principal_declarations import AgentDeclarations as AgentDeclarations
from ._schemas.core.principal_declarations import (
    WebhookSigningAlgorithm as AgentDeclarationsWebhookSigningAlgorithmsItem,
)
from ._schemas.core.principal_declarations_state import Axis as PrincipalDeclarationsStateExclusionsItemAxis
from ._schemas.core.principal_declarations_state import ExclusionsItem as PrincipalDeclarationsStateExclusionsItem
from ._schemas.core.principal_declarations_state import PrincipalDeclarationsState as PrincipalDeclarationsState
from ._schemas.core.principal_state import PrincipalState as PrincipalState
from ._schemas.core.principal_state import RetiredDestinationsItem as PrincipalStateRetiredDestinationsItem
from ._schemas.core.product import AudienceActivation as ProductAudienceActivation
from ._schemas.core.product import CatalogMatch as ProductCatalogMatch
from ._schemas.core.product import ConversionTracking as ProductConversionTracking
from ._schemas.core.product import (
    ConversionTrackingSupportedTargetsItem as ProductConversionTrackingSupportedTargetsItem,
)
from ._schemas.core.product import DeliveryMeasurement as ProductDeliveryMeasurement
from ._schemas.core.product import MaterialSubmission as ProductMaterialSubmission
from ._schemas.core.product import MetricOptimization as ProductMetricOptimization
from ._schemas.core.product import (
    MetricOptimizationSupportedTargetsItem as ProductMetricOptimizationSupportedTargetsItem,
)
from ._schemas.core.product import Product as Product
from ._schemas.core.product import ProductCard as ProductProductCard
from ._schemas.core.product import ProductCardDetailed as ProductProductCardDetailed
from ._schemas.core.product import ProvidersItem as ProductTrustedMatchProvidersItem
from ._schemas.core.product import SpecificationsItem as ProductProductCardDetailedSpecificationsItem
from ._schemas.core.product import TrustedMatch as ProductTrustedMatch
from ._schemas.core.product_allocation import ProductAllocation as ProductAllocation
from ._schemas.core.product_allowed_action import ProductAllowedAction as ProductAllowedAction
from ._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuersItemAgent as AcceptedAttestationIssuersItemAgent,
)
from ._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuersItemBrand as AcceptedAttestationIssuersItemBrand,
)
from ._schemas.core.product_audience_evidence_requirements import (
    EvidencePresence as ProductAudienceEvidenceRequirementsEvidencePresence,
)
from ._schemas.core.product_audience_evidence_requirements import (
    MaximumAge as ProductAudienceEvidenceRequirementsMaximumAge,
)
from ._schemas.core.product_audience_evidence_requirements import (
    ProductAudienceEvidenceRequirements as ProductAudienceEvidenceRequirements,
)
from ._schemas.core.product_audience_evidence_requirements import (
    RequirementMode as ProductAudienceEvidenceRequirementsRequirementMode,
)
from ._schemas.core.product_audience_evidence_requirements import (
    Unit as ProductAudienceEvidenceRequirementsMaximumAgeUnit,
)
from ._schemas.core.product_card_reference_asset import ProductCardReferenceAsset as ProductCardReferenceAsset
from ._schemas.core.product_card_reference_asset import Role as ProductCardReferenceAssetRole
from ._schemas.core.product_change_map import ProductChangeMap as ProductChangeMap
from ._schemas.core.product_change_map import ProductChangeMapValue as ProductChangeMapValue
from ._schemas.core.product_execution_requirement import CatalogExecutionRequirement as CatalogExecutionRequirement
from ._schemas.core.product_execution_requirement import (
    Connection as DownstreamConnectionExecutionRequirementConnection,
)
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
from ._schemas.core.product_filters import GeoProximityItem as ProductFiltersGeoProximityItem
from ._schemas.core.product_filters import KeywordsItem as ProductFiltersKeywordsItem
from ._schemas.core.product_filters import ObjProvidersResponseTypes as ProductFiltersTrustedMatch
from ._schemas.core.product_filters import ObjSystemCode as ProductFiltersMetrosItem
from ._schemas.core.product_filters import ProductFilters as ProductFilters
from ._schemas.core.product_filters import ProvidersItem as ProductFiltersTrustedMatchProvidersItem
from ._schemas.core.product_filters import RequiredGeoTargetingItem as ProductFiltersRequiredGeoTargetingItem
from ._schemas.core.product_filters import RequiredVendorMetricsItem as ProductFiltersRequiredVendorMetricsItem
from ._schemas.core.product_filters import SignalTargetingItem as ProductFiltersSignalTargetingItem
from ._schemas.core.product_filters import SignalTargetingItemBinary as SignalTargetingItemBinary
from ._schemas.core.product_filters import SignalTargetingItemCategorical as SignalTargetingItemCategorical
from ._schemas.core.product_filters import SignalTargetingItemNumeric as SignalTargetingItemNumeric
from ._schemas.core.product_filters import TargetingMode as ProductFiltersSignalTargetingItemTargetingMode
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
from ._schemas.core.product_format_declaration import SellerPreference as ProductFormatDeclarationSellerPreference
from ._schemas.core.product_format_declaration import (
    SellerRenderedStatefulDisplayFormatDeclaration as SellerRenderedStatefulDisplayFormatDeclaration,
)
from ._schemas.core.product_format_declaration import (
    SponsoredPlacementFormatDeclaration as SponsoredPlacementFormatDeclaration,
)
from ._schemas.core.product_format_declaration import VASTAudioFormatDeclaration as VASTAudioFormatDeclaration
from ._schemas.core.product_format_declaration import VASTVideoFormatDeclaration as VASTVideoFormatDeclaration
from ._schemas.core.product_identity import ProductIdentity as ProductIdentity
from ._schemas.core.product_offer_filters import AvailabilityHorizon as ProductOfferFiltersAvailabilityHorizon
from ._schemas.core.product_offer_filters import ProductOfferFilters as ProductOfferFilters
from ._schemas.core.product_offer_filters import RequiredFeatures as ProductOfferFiltersRequiredFeatures
from ._schemas.core.product_offer_filters import (
    RequiredPerformanceStandardsItem as ProductOfferFiltersRequiredPerformanceStandardsItem,
)
from ._schemas.core.product_offer_filters import (
    RequiredVendorMetricsItem as ProductOfferFiltersRequiredVendorMetricsItem,
)
from ._schemas.core.product_signal_targeting_option import (
    ActivationStatus as ProductSignalTargetingOptionActivationStatus,
)
from ._schemas.core.product_signal_targeting_option import (
    AllowedTargetingModesItem as ProductSignalTargetingOptionAllowedTargetingModesItem,
)
from ._schemas.core.product_signal_targeting_option import ProductSignalTargetingOption as ProductSignalTargetingOption
from ._schemas.core.product_targeting_resolution import ProductTargetingResolution as ProductTargetingResolution
from ._schemas.core.property import Property as Property
from ._schemas.core.property_delivery_metrics import PropertyDeliveryMetrics as PropertyDeliveryMetrics
from ._schemas.core.property_id import PropertyID as PropertyID
from ._schemas.core.property_list_ref import PropertyListReference as PropertyListReference
from ._schemas.core.property_ref import PropertyReference as PropertyReference
from ._schemas.core.property_tag import PropertyTag as PropertyTag
from ._schemas.core.proposal import Proposal as Proposal
from ._schemas.core.proposal import TotalBudgetGuidance as ProposalTotalBudgetGuidance
from ._schemas.core.protocol_envelope import ProtocolEnvelope as ProtocolEnvelope
from ._schemas.core.provenance import AiTool as ProvenanceAiTool
from ._schemas.core.provenance import C2pa as ProvenanceC2pa
from ._schemas.core.provenance import DeclaredBy as ProvenanceDeclaredBy
from ._schemas.core.provenance import Disclosure as ProvenanceDisclosure
from ._schemas.core.provenance import EmbeddedProvenanceItem as ProvenanceEmbeddedProvenanceItem
from ._schemas.core.provenance import HumanOversight as ProvenanceHumanOversight
from ._schemas.core.provenance import JurisdictionsItem as ProvenanceDisclosureJurisdictionsItem
from ._schemas.core.provenance import ObjAgentUrlFeatureId as ProvenanceEmbeddedProvenanceItemVerifyAgent
from ._schemas.core.provenance import Provenance as Provenance
from ._schemas.core.provenance import RenderGuidance as ProvenanceDisclosureJurisdictionsItemRenderGuidance
from ._schemas.core.provenance import Result as ProvenanceVerificationItemResult
from ._schemas.core.provenance import Role as ProvenanceDeclaredByRole
from ._schemas.core.provenance import VerificationItem as ProvenanceVerificationItem
from ._schemas.core.provenance import VerifyAgent as ProvenanceWatermarksItemVerifyAgent
from ._schemas.core.provenance import WatermarksItem as ProvenanceWatermarksItem
from ._schemas.core.publisher_property_selector import PublisherPropertySelector as PublisherPropertySelector
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorAll as PublisherPropertySelectorAll
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorById as PublisherPropertySelectorById
from ._schemas.core.publisher_property_selector import PublisherPropertySelectorByTag as PublisherPropertySelectorByTag
from ._schemas.core.push_notification_config import Authentication as PushNotificationConfigAuthentication
from ._schemas.core.push_notification_config import PushNotificationConfig as PushNotificationConfig
from ._schemas.core.real_estate_item import Area as RealEstateItemArea
from ._schemas.core.real_estate_item import ListingType as RealEstateItemListingType
from ._schemas.core.real_estate_item import RealEstateItem as RealEstateItem
from ._schemas.core.real_estate_item import RealEstateItemPropertyType as RealEstateItemPropertyType
from ._schemas.core.real_estate_item import Unit as RealEstateItemAreaUnit
from ._schemas.core.reference_asset import ReferenceAsset as ReferenceAsset
from ._schemas.core.reference_asset import Role as ReferenceAssetRole
from ._schemas.core.reference_renderer import ReferenceRenderer as ReferenceRenderer
from ._schemas.core.reference_renderer import ReferenceRendererProvenance as ReferenceRendererProvenance
from ._schemas.core.registry_event import AgentProfilePayload as RegistryEventAgentProfilePayload
from ._schemas.core.registry_event import AgentProfilePayloadType as RegistryEventAgentProfilePayloadType
from ._schemas.core.registry_event import AuthorizationPayload as RegistryEventAuthorizationPayload
from ._schemas.core.registry_event import AuthorizationType as RegistryEventAuthorizationPayloadAuthorizationType
from ._schemas.core.registry_event import ChangedFields as ChangedFields
from ._schemas.core.registry_event import Classification as RegistryEventClassification
from ._schemas.core.registry_event import CollectionIdentifier as RegistryEventCollectionIdentifier
from ._schemas.core.registry_event import CollectionPayload as RegistryEventCollectionPayload
from ._schemas.core.registry_event import CompliancePayload as RegistryEventCompliancePayload
from ._schemas.core.registry_event import ComplianceStatus as RegistryEventComplianceStatus
from ._schemas.core.registry_event import Countries as Countries
from ._schemas.core.registry_event import EntityType as RegistryEventEntityType
from ._schemas.core.registry_event import Evidence as RegistryEventAuthorizationPayloadEvidence
from ._schemas.core.registry_event import (
    GradingProfile as RegistryEventAgentVerificationEarnedAgentPayloadGradingProfile,
)
from ._schemas.core.registry_event import PropertyPayload as RegistryEventPropertyPayload
from ._schemas.core.registry_event import PropertySource as RegistryEventPropertySource
from ._schemas.core.registry_event import PublisherAdagentsPayload as RegistryEventPublisherAdagentsPayload
from ._schemas.core.registry_event import RegistryEvent as RegistryEvent
from ._schemas.core.registry_event import (
    RegistryEventAgentComplianceChangedAgent as RegistryEventAgentComplianceChangedAgent,
)
from ._schemas.core.registry_event import RegistryEventAgentDiscoveredAgent as RegistryEventAgentDiscoveredAgent
from ._schemas.core.registry_event import (
    RegistryEventAgentDiscoveredAgentPayload as RegistryEventAgentDiscoveredAgentPayload,
)
from ._schemas.core.registry_event import RegistryEventAgentProfileUpdatedAgent as RegistryEventAgentProfileUpdatedAgent
from ._schemas.core.registry_event import (
    RegistryEventAgentProfileUpdatedAgentPayload as RegistryEventAgentProfileUpdatedAgentPayload,
)
from ._schemas.core.registry_event import RegistryEventAgentRemovedAgent as RegistryEventAgentRemovedAgent
from ._schemas.core.registry_event import RegistryEventAgentRemovedAgentPayload as RegistryEventAgentRemovedAgentPayload
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationEarnedAgent as RegistryEventAgentVerificationEarnedAgent,
)
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationEarnedAgentPayload as RegistryEventAgentVerificationEarnedAgentPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationLostAgent as RegistryEventAgentVerificationLostAgent,
)
from ._schemas.core.registry_event import (
    RegistryEventAgentVerificationLostAgentPayload as RegistryEventAgentVerificationLostAgentPayload,
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
    RegistryEventCollectionCreatedCollectionPayload as RegistryEventCollectionCreatedCollectionPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionMergedCollection as RegistryEventCollectionMergedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionMergedCollectionPayload as RegistryEventCollectionMergedCollectionPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionRemovedCollection as RegistryEventCollectionRemovedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionRemovedCollectionPayload as RegistryEventCollectionRemovedCollectionPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionUpdatedCollection as RegistryEventCollectionUpdatedCollection,
)
from ._schemas.core.registry_event import (
    RegistryEventCollectionUpdatedCollectionPayload as RegistryEventCollectionUpdatedCollectionPayload,
)
from ._schemas.core.registry_event import RegistryEventEventType as RegistryEventEventType
from ._schemas.core.registry_event import RegistryEventPropertyCreatedProperty as RegistryEventPropertyCreatedProperty
from ._schemas.core.registry_event import (
    RegistryEventPropertyCreatedPropertyPayload as RegistryEventPropertyCreatedPropertyPayload,
)
from ._schemas.core.registry_event import RegistryEventPropertyMergedProperty as RegistryEventPropertyMergedProperty
from ._schemas.core.registry_event import (
    RegistryEventPropertyMergedPropertyPayload as RegistryEventPropertyMergedPropertyPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventPropertyReactivatedProperty as RegistryEventPropertyReactivatedProperty,
)
from ._schemas.core.registry_event import (
    RegistryEventPropertyReactivatedPropertyPayload as RegistryEventPropertyReactivatedPropertyPayload,
)
from ._schemas.core.registry_event import RegistryEventPropertyStaleProperty as RegistryEventPropertyStaleProperty
from ._schemas.core.registry_event import (
    RegistryEventPropertyStalePropertyPayload as RegistryEventPropertyStalePropertyPayload,
)
from ._schemas.core.registry_event import RegistryEventPropertyUpdatedProperty as RegistryEventPropertyUpdatedProperty
from ._schemas.core.registry_event import (
    RegistryEventPropertyUpdatedPropertyPayload as RegistryEventPropertyUpdatedPropertyPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventPublisherAdagentsChangedPublisher as RegistryEventPublisherAdagentsChangedPublisher,
)
from ._schemas.core.registry_event import (
    RegistryEventPublisherAdagentsChangedPublisherPayload as RegistryEventPublisherAdagentsChangedPublisherPayload,
)
from ._schemas.core.registry_event import (
    RegistryEventPublisherAdagentsDiscoveredPublisher as RegistryEventPublisherAdagentsDiscoveredPublisher,
)
from ._schemas.core.registry_event import Status as RegistryEventCollectionPayloadStatus
from ._schemas.core.registry_event import StoryboardsItem as RegistryEventCompliancePayloadStoryboardsItem
from ._schemas.core.registry_event import StoryboardStatus as RegistryEventStoryboardStatus
from ._schemas.core.registry_event import StringArray as StringArray
from ._schemas.core.registry_event import TracksValue as RegistryEventCompliancePayloadTracksValue
from ._schemas.core.registry_feed_response import Freshness as RegistryFeedResponseFreshness
from ._schemas.core.registry_feed_response import RegistryFeedResponse as RegistryFeedResponse
from ._schemas.core.reporting_adjustment import ObjStartEnd as ReportingAdjustmentAccountingPeriod
from ._schemas.core.reporting_adjustment import ReasonCode as ReportingAdjustmentReasonCode
from ._schemas.core.reporting_adjustment import ReportingAdjustment as ReportingAdjustment
from ._schemas.core.reporting_adjustment_receipt import ReportingAdjustmentReceipt as ReportingAdjustmentReceipt
from ._schemas.core.reporting_adjustment_receipt import (
    ReportingAdjustmentRejectionCode as ReportingAdjustmentRejectionCode,
)
from ._schemas.core.reporting_adjustment_receipt import Status as ReportingAdjustmentReceiptStatus
from ._schemas.core.reporting_canonical_content_digest import (
    ReportingCanonicalContentDigest as ReportingCanonicalContentDigest,
)
from ._schemas.core.reporting_canonicalization_contract import (
    AdditionalItem as ReportingCanonicalizationContractGoldenVectorsAdditionalItem,
)
from ._schemas.core.reporting_canonicalization_contract import (
    EmptyReport as ReportingCanonicalizationContractGoldenVectorsEmptyReport,
)
from ._schemas.core.reporting_canonicalization_contract import (
    GoldenVectors as ReportingCanonicalizationContractGoldenVectors,
)
from ._schemas.core.reporting_canonicalization_contract import (
    OrderingEncoding as ReportingCanonicalizationContractGoldenVectorsOrderingEncoding,
)
from ._schemas.core.reporting_canonicalization_contract import (
    ReportingCanonicalizationContract as ReportingCanonicalizationContract,
)
from ._schemas.core.reporting_canonicalization_contract import ReportingPrimaryKey as ReportingPrimaryKey
from ._schemas.core.reporting_capabilities import DateRangeSupport as ReportingCapabilitiesDateRangeSupport
from ._schemas.core.reporting_capabilities import ReportingCapabilities as ReportingCapabilities
from ._schemas.core.reporting_capabilities import VendorMetricsItem as ReportingCapabilitiesVendorMetricsItem
from ._schemas.core.reporting_consumer_status import ConsumerStatus as ReportingConsumerStatusConsumerStatus
from ._schemas.core.reporting_consumer_status import FailureCode as ReportingConsumerStatusFailureCode
from ._schemas.core.reporting_consumer_status import MismatchCode as ReportingConsumerStatusMismatchCode
from ._schemas.core.reporting_consumer_status import ObjStartEndSourceTimezone as ReportingConsumerStatusPeriod
from ._schemas.core.reporting_consumer_status import ReportingConsumerStatus as ReportingConsumerStatus
from ._schemas.core.reporting_control_total import DecimalReportingControlTotal as DecimalReportingControlTotal
from ._schemas.core.reporting_control_total import IntegerReportingControlTotal as IntegerReportingControlTotal
from ._schemas.core.reporting_control_total import ReportingControlTotal as ReportingControlTotal
from ._schemas.core.reporting_coverage import LimitationsItem as ReportingCoverageLimitationsItem
from ._schemas.core.reporting_coverage import Reason as ReportingCoverageLimitationsItemReason
from ._schemas.core.reporting_coverage import ReportingCoverage as ReportingCoverage
from ._schemas.core.reporting_coverage import ReportingMediaBuyId as ReportingMediaBuyId
from ._schemas.core.reporting_coverage import ReportingPackageId as ReportingPackageId
from ._schemas.core.reporting_coverage import Status as ReportingCoverageStatus
from ._schemas.core.reporting_dataset_share_destination import ObjDomain as ProvisionRecipientProvider
from ._schemas.core.reporting_dataset_share_destination import ProvisionRecipient as ProvisionRecipient
from ._schemas.core.reporting_dataset_share_destination import Recipient as ProvisionRecipientRecipient
from ._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestination as ReportingDatasetShareDestination,
)
from ._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestinationExisting as ReportingDatasetShareDestinationExisting,
)
from ._schemas.core.reporting_delivery_capabilities import (
    OperationsContact as ReportingDeliveryCapabilitiesOperationsContact,
)
from ._schemas.core.reporting_delivery_capabilities import (
    ReportingDeliveryCapabilities as ReportingDeliveryCapabilities,
)
from ._schemas.core.reporting_delivery_config import (
    AuthoritativeParty as ReportingDeliveryConfigurationAuthoritativeParty,
)
from ._schemas.core.reporting_delivery_config import (
    CoverageRequirement as ReportingDeliveryConfigurationCoverageRequirement,
)
from ._schemas.core.reporting_delivery_config import ReportingDeliveryConfiguration as ReportingDeliveryConfiguration
from ._schemas.core.reporting_delivery_config import Scope as ReportingDeliveryConfigurationScope
from ._schemas.core.reporting_delivery_config_state import Action as ReportingDeliveryConfigurationStateSetupAction
from ._schemas.core.reporting_delivery_config_state import (
    ReportingDeliveryConfigLifecycleState as ReportingDeliveryConfigurationStateReportingDeliveryConfigLifecycleState,
)
from ._schemas.core.reporting_delivery_config_state import (
    ReportingDeliveryConfigurationState as ReportingDeliveryConfigurationState,
)
from ._schemas.core.reporting_delivery_config_state import Setup as ReportingDeliveryConfigurationStateSetup
from ._schemas.core.reporting_delivery_method import DatasetShare as DatasetShare
from ._schemas.core.reporting_delivery_method import FileFormat as FileTransferFormat
from ._schemas.core.reporting_delivery_method import ReportingDeliveryMethod as ReportingDeliveryMethod
from ._schemas.core.reporting_delivery_method import (
    ReportingDeliveryMethodFileTransfer as ReportingDeliveryMethodFileTransfer,
)
from ._schemas.core.reporting_delivery_method import (
    ReportingOrchestration as ReportingDeliveryMethodReportingOrchestration,
)
from ._schemas.core.reporting_delivery_method import WarehouseMaterialization as WarehouseMaterialization
from ._schemas.core.reporting_delivery_offering import (
    DestinationModesItem as ReportingDeliveryOfferingMethodDestinationModesItem,
)
from ._schemas.core.reporting_delivery_offering import Method as ReportingDeliveryOfferingMethod
from ._schemas.core.reporting_delivery_offering import (
    ProducerIdentity as ReportingDeliveryOfferingMethodProducerIdentity,
)
from ._schemas.core.reporting_delivery_offering import ReportingDeliveryOffering as ReportingDeliveryOffering
from ._schemas.core.reporting_delivery_offering import (
    ReportingDeliveryPattern as ReportingDeliveryOfferingReportingDeliveryPattern,
)
from ._schemas.core.reporting_delivery_offering import (
    ReportingFeedPurpose as ReportingDeliveryOfferingReportingFeedPurpose,
)
from ._schemas.core.reporting_delivery_offering import ReportingProfile as ReportingDeliveryOfferingReportingProfile
from ._schemas.core.reporting_delivery_offering_id import ReportingDeliveryOfferingID as ReportingDeliveryOfferingID
from ._schemas.core.reporting_delivery_ready_webhook import Readiness as ReportingDeliveryReadyWebhookReadiness
from ._schemas.core.reporting_delivery_ready_webhook import (
    ReportingDeliveryReadyWebhook as ReportingDeliveryReadyWebhook,
)
from ._schemas.core.reporting_file_compression import ReportingFileCompression as ReportingFileCompression
from ._schemas.core.reporting_file_entry import ReportingFileEntry as ReportingFileEntry
from ._schemas.core.reporting_file_manifest import ReportingFileManifest as ReportingFileManifest
from ._schemas.core.reporting_file_object_ref import ReportingFileObjectReference as ReportingFileObjectReference
from ._schemas.core.reporting_ledger_changed_webhook import ChangeKind as ReportingLedgerChangedWebhookChangeKind
from ._schemas.core.reporting_ledger_changed_webhook import (
    ReportingLedgerChangedWebhook as ReportingLedgerChangedWebhook,
)
from ._schemas.core.reporting_materialization import ReportingMaterialization as ReportingMaterialization
from ._schemas.core.reporting_materialization import Status as ReportingMaterializationStatus
from ._schemas.core.reporting_native_version_ref import (
    ReportingNativeVersionReference as ReportingNativeVersionReference,
)
from ._schemas.core.reporting_obligation import ProductionStatus as ReportingObligationProductionStatus
from ._schemas.core.reporting_obligation import ReconciliationStatus as ReportingObligationReconciliationStatus
from ._schemas.core.reporting_obligation import ReportingObligation as ReportingObligation
from ._schemas.core.reporting_receipt import ReportingReceipt as ReportingReceipt
from ._schemas.core.reporting_receipt import Status as ReportingReceiptStatus
from ._schemas.core.reporting_reconciliation_mode import ReportingReconciliationMode as ReportingReconciliationMode
from ._schemas.core.reporting_reliability_statistics import (
    AdjustmentMagnitudeItem as ReportingReliabilityStatisticsAdjustmentMagnitudeItem,
)
from ._schemas.core.reporting_reliability_statistics import Basis as ReportingReliabilityStatisticsEvidenceBasis
from ._schemas.core.reporting_reliability_statistics import Evidence as ReportingReliabilityStatisticsEvidence
from ._schemas.core.reporting_reliability_statistics import (
    LatencyPercentiles as ReportingReliabilityStatisticsLatencyPercentiles,
)
from ._schemas.core.reporting_reliability_statistics import (
    ReportingReliabilityMeasurementPeriod as ReportingReliabilityStatisticsReportingReliabilityMeasurementPeriod,
)
from ._schemas.core.reporting_reliability_statistics import (
    ReportingReliabilityStatistics as ReportingReliabilityStatistics,
)
from ._schemas.core.reporting_report_definition import Aggregation as ReportingReportDefinitionMetricsItemAggregation
from ._schemas.core.reporting_report_definition import Calendar as ReportingReportDefinitionCalendar
from ._schemas.core.reporting_report_definition import (
    FinalityPoliciesItemContractualCutoff as FinalityPoliciesItemContractualCutoff,
)
from ._schemas.core.reporting_report_definition import (
    FinalityPoliciesItemSourceFinal as FinalityPoliciesItemSourceFinal,
)
from ._schemas.core.reporting_report_definition import FinalityPoliciesItemStabilized as FinalityPoliciesItemStabilized
from ._schemas.core.reporting_report_definition import MetricsItem as ReportingReportDefinitionMetricsItem
from ._schemas.core.reporting_report_definition import (
    ReportCalendarTimezoneBasis as ReportingReportDefinitionReportCalendarTimezoneBasis,
)
from ._schemas.core.reporting_report_definition import ReportingReportDefinition as ReportingReportDefinition
from ._schemas.core.reporting_report_definition import RestatementPolicy as ReportingReportDefinitionRestatementPolicy
from ._schemas.core.reporting_report_definition import Source as ReportingReportDefinitionSource
from ._schemas.core.reporting_resource import Immutability as ReportingResourceImmutability
from ._schemas.core.reporting_resource import Kind as ReportingResourceKind
from ._schemas.core.reporting_resource import ReportingReaderCompatibilityItem as ReportingReaderCompatibilityItem
from ._schemas.core.reporting_resource import ReportingResource as ReportingResource
from ._schemas.core.reporting_revision import DataThroughPrecision as ReportingRevisionDataThroughPrecision
from ._schemas.core.reporting_revision import FinalityBasis as ReportingRevisionFinalityBasis
from ._schemas.core.reporting_revision import ReportingRevision as ReportingRevision
from ._schemas.core.reporting_schedule import ReportingSchedule as ReportingSchedule
from ._schemas.core.reporting_schedule import ReportingScheduleAlignment as ReportingScheduleReportingScheduleAlignment
from ._schemas.core.reporting_schedule_offering import PeriodAnchorPolicy as ReportingScheduleOfferingPeriodAnchorPolicy
from ._schemas.core.reporting_schedule_offering import (
    PeriodTimezonePolicy as ReportingScheduleOfferingPeriodTimezonePolicy,
)
from ._schemas.core.reporting_schedule_offering import ReportingScheduleOffering as ReportingScheduleOffering
from ._schemas.core.reporting_status_changed_webhook import (
    ReportingStatusChangedWebhook as ReportingStatusChangedWebhook,
)
from ._schemas.core.reporting_status_issue import Code as ReportingStatusIssueCode
from ._schemas.core.reporting_status_issue import IssueState as ReportingStatusIssueIssueState
from ._schemas.core.reporting_status_issue import RecommendedAction as ReportingStatusIssueRecommendedAction
from ._schemas.core.reporting_status_issue import ReportingStatusIssue as ReportingStatusIssue
from ._schemas.core.reporting_status_issue import ReportingStatusSeverity as ReportingStatusIssueReportingStatusSeverity
from ._schemas.core.reporting_status_issue import ResponsibleParty as ReportingStatusIssueResponsibleParty
from ._schemas.core.reporting_verification import NativeCommitEvidence as ReportingVerificationNativeCommitEvidence
from ._schemas.core.reporting_verification import (
    ObservedThrough as ReportingVerificationNativeCommitEvidenceObservedThrough,
)
from ._schemas.core.reporting_verification import ReportingVerification as ReportingVerification
from ._schemas.core.reporting_verification import SHA256PhysicalChecksum as SHA256PhysicalChecksum
from ._schemas.core.reporting_verification import SHA512PhysicalChecksum as SHA512PhysicalChecksum
from ._schemas.core.reporting_verification import VerificationPath as ReportingVerificationVerificationPath
from ._schemas.core.reporting_verification_profile import ReportingVerificationProfile as ReportingVerificationProfile
from ._schemas.core.reporting_verification_profile_set import (
    ReportingVerificationProfileSet as ReportingVerificationProfileSet,
)
from ._schemas.core.reporting_webhook import ReportingWebhook as ReportingWebhook
from ._schemas.core.reporting_webhook import ReportingWebhookReportingFrequency as ReportingWebhookReportingFrequency
from ._schemas.core.reporting_write_destination import ProvisionBinding as ProvisionBinding
from ._schemas.core.reporting_write_destination import ReportingWriteDestination as ReportingWriteDestination
from ._schemas.core.reporting_write_destination import (
    ReportingWriteDestinationExisting as ReportingWriteDestinationExisting,
)
from ._schemas.core.representation_destination import RepresentationDestination as RepresentationDestination
from ._schemas.core.representation_rejection import Code as RepresentationRejectionCode
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
from ._schemas.core.requirements.audio_asset_requirements import FormatsItem as AudioAssetRequirementsFormatsItem
from ._schemas.core.requirements.catalog_field_binding import AssetPoolBinding as CatalogFieldBindingAssetPoolBinding
from ._schemas.core.requirements.catalog_field_binding import CatalogFieldBinding as CatalogFieldBinding
from ._schemas.core.requirements.catalog_field_binding import (
    CatalogFieldBindingAssetPool as CatalogFieldBindingAssetPool,
)
from ._schemas.core.requirements.catalog_field_binding import (
    CatalogFieldBindingCatalogGroup as CatalogFieldBindingCatalogGroup,
)
from ._schemas.core.requirements.catalog_field_binding import CatalogFieldBindingScalar as CatalogFieldBindingScalar
from ._schemas.core.requirements.catalog_field_binding import ScalarBinding as CatalogFieldBindingScalarBinding
from ._schemas.core.requirements.catalog_requirements import CatalogRequirements as CatalogRequirements
from ._schemas.core.requirements.css_asset_requirements import CSSAssetRequirements as CSSAssetRequirements
from ._schemas.core.requirements.daast_asset_requirements import DAASTAssetRequirements as DAASTAssetRequirements
from ._schemas.core.requirements.html_asset_requirements import HTMLAssetRequirements as HTMLAssetRequirements
from ._schemas.core.requirements.html_asset_requirements import Sandbox as HTMLAssetRequirementsSandbox
from ._schemas.core.requirements.image_asset_requirements import BleedBottomLeftRightTop as BleedBottomLeftRightTop
from ._schemas.core.requirements.image_asset_requirements import BleedUniform as BleedUniform
from ._schemas.core.requirements.image_asset_requirements import ColorSpace as ImageAssetRequirementsColorSpace
from ._schemas.core.requirements.image_asset_requirements import FormatsItem as ImageAssetRequirementsFormatsItem
from ._schemas.core.requirements.image_asset_requirements import ImageAssetRequirements as ImageAssetRequirements
from ._schemas.core.requirements.javascript_asset_requirements import (
    JavaScriptAssetRequirements as JavaScriptAssetRequirements,
)
from ._schemas.core.requirements.javascript_asset_requirements import (
    ModuleType as JavaScriptAssetRequirementsModuleType,
)
from ._schemas.core.requirements.markdown_asset_requirements import (
    MarkdownAssetRequirements as MarkdownAssetRequirements,
)
from ._schemas.core.requirements.offering_asset_constraint import OfferingAssetConstraint as OfferingAssetConstraint
from ._schemas.core.requirements.text_asset_requirements import TextAssetRequirements as TextAssetRequirements
from ._schemas.core.requirements.url_asset_requirements import ProtocolsItem as URLAssetRequirementsProtocolsItem
from ._schemas.core.requirements.url_asset_requirements import Role as URLAssetRequirementsRole
from ._schemas.core.requirements.url_asset_requirements import URLAssetRequirements as URLAssetRequirements
from ._schemas.core.requirements.vast_asset_requirements import VASTAssetRequirements as VASTAssetRequirements
from ._schemas.core.requirements.video_asset_requirements import (
    AudioCodecsItem as VideoAssetRequirementsAudioCodecsItem,
)
from ._schemas.core.requirements.video_asset_requirements import ContainersItem as VideoAssetRequirementsContainersItem
from ._schemas.core.requirements.video_asset_requirements import VideoAssetRequirements as VideoAssetRequirements
from ._schemas.core.requirements.webhook_asset_requirements import WebhookAssetRequirements as WebhookAssetRequirements
from ._schemas.core.response import ProtocolResponse as ProtocolResponse
from ._schemas.core.response_payload_jws_envelope import ResponsePayload as ResponsePayloadJWSEnvelopeResponsePayload
from ._schemas.core.response_payload_jws_envelope import ResponsePayloadJWSEnvelope as ResponsePayloadJWSEnvelope
from ._schemas.core.response_payload_jws_envelope import Task as ResponsePayloadJWSEnvelopeResponsePayloadTask
from ._schemas.core.rights_attestation_evaluation import (
    ActionBinding as RightsAttestationEvaluationEvaluationActionBinding,
)
from ._schemas.core.rights_attestation_evaluation import Evaluation as RightsAttestationEvaluationEvaluation
from ._schemas.core.rights_attestation_evaluation import Reference as RightsAttestationEvaluationReference
from ._schemas.core.rights_attestation_evaluation import RightsAttestationEvaluation as RightsAttestationEvaluation
from ._schemas.core.rights_constraint import ApprovalStatus as RightsConstraintApprovalStatus
from ._schemas.core.rights_constraint import AttestationRefsItem as RightsConstraintAttestationRefsItem
from ._schemas.core.rights_constraint import Disclosure as RightsConstraintDisclosure
from ._schemas.core.rights_constraint import GrantStatus as RightsConstraintGrantStatus
from ._schemas.core.rights_constraint import ObjTypeResourceType as RightsConstraintAttestationRefsItemSubject
from ._schemas.core.rights_constraint import RightsAgent as RightsConstraintRightsAgent
from ._schemas.core.rights_constraint import RightsConstraint as RightsConstraint
from ._schemas.core.seller_agent_ref import SellerAgentReference as SellerAgentReference
from ._schemas.core.signal_coverage_forecast import BucketCompleteness as SignalCoverageForecastBucketCompleteness
from ._schemas.core.signal_coverage_forecast import BucketSemantics as SignalCoverageForecastBucketSemantics
from ._schemas.core.signal_coverage_forecast import Kind as SignalCoverageForecastScopeKind
from ._schemas.core.signal_coverage_forecast import Metrics as SignalCoverageForecastPointsItemMetrics
from ._schemas.core.signal_coverage_forecast import PointsItem as SignalCoverageForecastPointsItem
from ._schemas.core.signal_coverage_forecast import Scope as SignalCoverageForecastScope
from ._schemas.core.signal_coverage_forecast import SignalCoverageForecast as SignalCoverageForecast
from ._schemas.core.signal_definition import AiActRiskClass as SignalDefinitionModelingAiActRiskClass
from ._schemas.core.signal_definition import Art9Basis as SignalDefinitionArt9Basis
from ._schemas.core.signal_definition import AudienceScope as SignalDefinitionAudienceScope
from ._schemas.core.signal_definition import ChannelsItem as SignalDefinitionDataSubjectRightsChannelsItem
from ._schemas.core.signal_definition import DataSourcesItem as SignalDefinitionDataSourcesItem
from ._schemas.core.signal_definition import DataSubjectRights as SignalDefinitionDataSubjectRights
from ._schemas.core.signal_definition import IdTypesItem as SignalDefinitionIdTypesItem
from ._schemas.core.signal_definition import LookbackWindow as SignalDefinitionLookbackWindow
from ._schemas.core.signal_definition import MatchKeysItem as SignalDefinitionOnboarderMatchKeysItem
from ._schemas.core.signal_definition import Method as SignalDefinitionModelingMethod
from ._schemas.core.signal_definition import Methodology as SignalDefinitionMethodology
from ._schemas.core.signal_definition import Modeling as SignalDefinitionModeling
from ._schemas.core.signal_definition import ObjIdPathModifiers as SignalDefinitionTaxonomyValuesItem
from ._schemas.core.signal_definition import ObjTypeProviderSigned as SignalDefinitionModelingSeedSource
from ._schemas.core.signal_definition import Onboarder as SignalDefinitionOnboarder
from ._schemas.core.signal_definition import ParentMatchBehavior as SignalDefinitionTaxonomyParentMatchBehavior
from ._schemas.core.signal_definition import (
    PreOnboardingPrecisionLevel as SignalDefinitionOnboarderPreOnboardingPrecisionLevel,
)
from ._schemas.core.signal_definition import Range as SignalDefinitionRange
from ._schemas.core.signal_definition import RefreshCadence as SignalDefinitionRefreshCadence
from ._schemas.core.signal_definition import RightsItem as SignalDefinitionDataSubjectRightsChannelsItemRightsItem
from ._schemas.core.signal_definition import SeedSourceType as SignalDefinitionModelingSeedSourceType
from ._schemas.core.signal_definition import SignalDefinition as SignalDefinition
from ._schemas.core.signal_definition import Taxonomy as SignalDefinitionTaxonomy
from ._schemas.core.signal_definition import ValueMappingsItem as SignalDefinitionTaxonomyValueMappingsItem
from ._schemas.core.signal_definition_enrichment import LookbackWindow as LookbackWindow
from ._schemas.core.signal_definition_enrichment import SignalDefinitionEnrichment as SignalDefinitionEnrichment
from ._schemas.core.signal_filters import SignalFilters as SignalFilters
from ._schemas.core.signal_id import SignalID as SignalID
from ._schemas.core.signal_id import SignalIDAgent as SignalIDAgent
from ._schemas.core.signal_id import SignalIDCatalog as SignalIDCatalog
from ._schemas.core.signal_listing import ObjMinMax as SignalListingRange
from ._schemas.core.signal_listing import SignalListing as SignalListing
from ._schemas.core.signal_modeling_disclosure import Audience as SignalModelingDisclosureJurisdictionsItemAudience
from ._schemas.core.signal_modeling_disclosure import JurisdictionsItem as SignalModelingDisclosureJurisdictionsItem
from ._schemas.core.signal_modeling_disclosure import SignalModelingDisclosure as SignalModelingDisclosure
from ._schemas.core.signal_pricing import CpmPricing as CpmPricing
from ._schemas.core.signal_pricing import CustomPricing as CustomPricing
from ._schemas.core.signal_pricing import FlatFeePricing as FlatFeePricing
from ._schemas.core.signal_pricing import Metadata as CustomPricingMetadata
from ._schemas.core.signal_pricing import PercentOfMediaPricing as PercentOfMediaPricing
from ._schemas.core.signal_pricing import Period as FlatFeePricingPeriod
from ._schemas.core.signal_pricing import PerUnitPricing as PerUnitPricing
from ._schemas.core.signal_pricing import VendorPricing as VendorPricing
from ._schemas.core.signal_pricing_option import SignalPricingOption as SignalPricingOption
from ._schemas.core.signal_ref import SignalRef as SignalRef
from ._schemas.core.signal_ref import SignalRefDataProvider as SignalRefDataProvider
from ._schemas.core.signal_ref import SignalRefProduct as SignalRefProduct
from ._schemas.core.signal_ref import SignalRefSignalSource as SignalRefSignalSource
from ._schemas.core.signal_selection_group_rule import SelectionMode as SignalSelectionGroupRuleSelectionMode
from ._schemas.core.signal_selection_group_rule import SignalSelectionGroupRule as SignalSelectionGroupRule
from ._schemas.core.signal_selection_group_rule import TargetingMode as SignalSelectionGroupRuleTargetingMode
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
from ._schemas.core.signal_targeting_rules import ResolutionModel as SignalTargetingRulesResolutionModel
from ._schemas.core.signal_targeting_rules import SignalTargetingRules as SignalTargetingRules
from ._schemas.core.sla_window import SLAWindow as SLAWindow
from ._schemas.core.special import Special as Special
from ._schemas.core.spot_reporting_capability import SpotReportingCapability as SpotReportingCapability
from ._schemas.core.start_timing import StartTiming as StartTiming
from ._schemas.core.store_item import HoursValue as HoursValue
from ._schemas.core.store_item import StoreItem as StoreItem
from ._schemas.core.talent import Talent as Talent
from ._schemas.core.targeting import AgeRestriction as TargetingOverlayAgeRestriction
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
from ._schemas.core.targeting import GeometryType as TargetingOverlayGeoProximityItemGeometryType
from ._schemas.core.targeting import GeoPlaces as GeoPlaces
from ._schemas.core.targeting import GeoPlacesExclude as GeoPlacesExclude
from ._schemas.core.targeting import GeoPostalAreas as GeoPostalAreas
from ._schemas.core.targeting import GeoPostalAreasExclude as GeoPostalAreasExclude
from ._schemas.core.targeting import GeoProximityItem as TargetingOverlayGeoProximityItem
from ._schemas.core.targeting import GeoRegions as GeoRegions
from ._schemas.core.targeting import GeoRegionsExclude as GeoRegionsExclude
from ._schemas.core.targeting import ObjTypeCoordinates as TargetingOverlayGeoProximityItemGeometry
from ._schemas.core.targeting import Radius as TargetingOverlayGeoProximityItemRadius
from ._schemas.core.targeting import StoreCatchments as StoreCatchments
from ._schemas.core.targeting import StoreCatchmentsItem as TargetingOverlayStoreCatchmentsItem
from ._schemas.core.targeting import TargetingOverlay as TargetingOverlay
from ._schemas.core.targeting import TargetingOverlayDevicePlatform as TargetingOverlayDevicePlatform
from ._schemas.core.targeting import TargetingOverlayDeviceType as TargetingOverlayDeviceType
from ._schemas.core.targeting import TargetingOverlayGeoProximity as TargetingOverlayGeoProximity
from ._schemas.core.targeting import TravelTime as TargetingOverlayGeoProximityItemTravelTime
from ._schemas.core.targeting_input import TargetingOverlayInput as TargetingOverlayInput
from ._schemas.core.targeting_modification import RemoveTargetingSetValues as RemoveTargetingSetValues
from ._schemas.core.targeting_modification import RemoveTargetingSetValuesPath as RemoveTargetingSetValuesPath
from ._schemas.core.targeting_modification import ReplaceTargetingValue as ReplaceTargetingValue
from ._schemas.core.targeting_modification import Selector as RemoveTargetingSetValuesSelector
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
from ._schemas.core.targeting_overlay_support import FrequencyCapSupport as TargetingOverlaySupportFrequencyCapSupport
from ._schemas.core.targeting_overlay_support import KeywordSupport as KeywordSupport
from ._schemas.core.targeting_overlay_support import (
    KeywordSupportSupportedMatchTypes as KeywordSupportSupportedMatchTypes,
)
from ._schemas.core.targeting_overlay_support import MetroSupport as MetroSupport
from ._schemas.core.targeting_overlay_support import MetroSupportSystems as MetroSupportSystems
from ._schemas.core.targeting_overlay_support import PlaceCatalogSupport as TargetingOverlaySupportPlaceCatalogSupport
from ._schemas.core.targeting_overlay_support import PlaceSupport as TargetingOverlaySupportPlaceSupport
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
from ._schemas.core.tasks_get_response import Details as TasksGetResponseErrorDetails
from ._schemas.core.tasks_get_response import ObjCodeMessageDetails as TasksGetResponseError
from ._schemas.core.tasks_get_response import ObjTimestampTypeData as TasksGetResponseHistoryItem
from ._schemas.core.tasks_get_response import Progress as TasksGetResponseProgress
from ._schemas.core.tasks_get_response import TasksGetResponse as TasksGetResponse
from ._schemas.core.tasks_list_request import Filters as TasksListRequestFilters
from ._schemas.core.tasks_list_request import Sort as TasksListRequestSort
from ._schemas.core.tasks_list_request import SortField as TasksListRequestSortField
from ._schemas.core.tasks_list_request import TasksListRequest as TasksListRequest
from ._schemas.core.tasks_list_response import Domain as TasksListResponseTasksItemDomain
from ._schemas.core.tasks_list_response import (
    ObjMediaBuySignalsCreative as TasksListResponseQuerySummaryDomainBreakdown,
)
from ._schemas.core.tasks_list_response import QuerySummary as TasksListResponseQuerySummary
from ._schemas.core.tasks_list_response import SortApplied as TasksListResponseQuerySummarySortApplied
from ._schemas.core.tasks_list_response import TasksItem as TasksListResponseTasksItem
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
from ._schemas.core.transformer import BrandAgent as TransformerVoiceSynthesisRefItemBrandAgent
from ._schemas.core.transformer import Multiplicity as TransformerMultiplicity
from ._schemas.core.transformer import Transformer as Transformer
from ._schemas.core.transformer import VariantDimensionsItem as TransformerMultiplicityVariantDimensionsItem
from ._schemas.core.transformer import VoiceSynthesisRefItem as TransformerVoiceSynthesisRefItem
from ._schemas.core.transformer_param import OptionsItem as TransformerParamOptionsItem
from ._schemas.core.transformer_param import TransformerParam as TransformerParam
from ._schemas.core.transformer_param import TransformerParamType as TransformerParamType
from ._schemas.core.transformer_param import ValueSource as TransformerParamValueSource
from ._schemas.core.truncation_sentinel import Truncation as TruncationSentinelTruncation
from ._schemas.core.truncation_sentinel import TruncationSentinel as TruncationSentinel
from ._schemas.core.user_match import UserMatch as UserMatch
from ._schemas.core.vast_media_file_requirements import VASTMediaFileRequirements as VASTMediaFileRequirements
from ._schemas.core.vast_tracker_constraints import VastEvent as VASTTrackerConstraintsVastEvent
from ._schemas.core.vast_tracker_constraints import VastOffset as VastOffset
from ._schemas.core.vast_tracker_constraints import VastTarget as VASTTrackerConstraintsVastTarget
from ._schemas.core.vast_tracker_constraints import VASTTrackerConstraints as VASTTrackerConstraints
from ._schemas.core.vast_tracker_constraints import VastVersions as VastVersions
from ._schemas.core.vehicle_item import BodyStyle as VehicleItemBodyStyle
from ._schemas.core.vehicle_item import Condition as VehicleItemCondition
from ._schemas.core.vehicle_item import FuelType as VehicleItemFuelType
from ._schemas.core.vehicle_item import Mileage as VehicleItemMileage
from ._schemas.core.vehicle_item import Transmission as VehicleItemTransmission
from ._schemas.core.vehicle_item import Unit as VehicleItemMileageUnit
from ._schemas.core.vehicle_item import VehicleItem as VehicleItem
from ._schemas.core.vendor_metric_id import VendorMetricID as VendorMetricID
from ._schemas.core.vendor_metric_optimization import VendorMetricOptimization as VendorMetricOptimization
from ._schemas.core.vendor_metric_optimization_supported_metric import (
    SupportedTargetsItem as VendorMetricOptimizationSupportedMetricSupportedTargetsItem,
)
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
from ._schemas.core.verification_token_claims import Role as AgenticAdvertisingOrgVerificationTokenClaimsRole
from ._schemas.core.verification_token_claims import (
    VerificationMode as AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenMode,
)
from ._schemas.core.version_envelope import AdcpMajorVersion as AdcpMajorVersion
from ._schemas.core.version_envelope import AdcpVersion as AdcpVersion
from ._schemas.core.version_envelope import AdCPVersionEnvelope as AdCPVersionEnvelope
from ._schemas.core.warning import Warning as Warning
from ._schemas.core.warning_resource import ResourceType as WarningAffectedResourceResourceType
from ._schemas.core.warning_resource import WarningAffectedResource as WarningAffectedResource
from ._schemas.core.webhook_activity_record import Status as WebhookActivityRecordStatus
from ._schemas.core.webhook_activity_record import WebhookActivityRecord as WebhookActivityRecord
from ._schemas.core.webhook_challenge import WebhookChallenge as WebhookChallenge
from ._schemas.core.webhook_challenge_response import WebhookChallengeResponse as WebhookChallengeResponse
from ._schemas.core.wholesale_feed_event import (
    AffectedEntityType as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadAffectedEntityType,
)
from ._schemas.core.wholesale_feed_event import AppliesTo as AppliesTo
from ._schemas.core.wholesale_feed_event import AppliesToAccount as AppliesToAccount
from ._schemas.core.wholesale_feed_event import AppliesToPublic as AppliesToPublic
from ._schemas.core.wholesale_feed_event import EntityType as WholesaleFeedEventEntityType
from ._schemas.core.wholesale_feed_event import (
    Recommendation as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadRecommendation,
)
from ._schemas.core.wholesale_feed_event import RemovalReason as WholesaleFeedEventRemovalReason
from ._schemas.core.wholesale_feed_event import Signal as WholesaleFeedEventSignal
from ._schemas.core.wholesale_feed_event import WholesaleFeedEvent as WholesaleFeedEvent
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductCreatedProduct as WholesaleFeedEventProductCreatedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductCreatedProductPayload as WholesaleFeedEventProductCreatedProductPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductPricedProduct as WholesaleFeedEventProductPricedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductPricedProductPayload as WholesaleFeedEventProductPricedProductPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductRemovedProduct as WholesaleFeedEventProductRemovedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductRemovedProductPayload as WholesaleFeedEventProductRemovedProductPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductUpdatedProduct as WholesaleFeedEventProductUpdatedProduct,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventProductUpdatedProductPayload as WholesaleFeedEventProductUpdatedProductPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalCreatedSignal as WholesaleFeedEventSignalCreatedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalCreatedSignalPayload as WholesaleFeedEventSignalCreatedSignalPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalPricedSignal as WholesaleFeedEventSignalPricedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalPricedSignalPayload as WholesaleFeedEventSignalPricedSignalPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalRemovedSignal as WholesaleFeedEventSignalRemovedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalRemovedSignalPayload as WholesaleFeedEventSignalRemovedSignalPayload,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalUpdatedSignal as WholesaleFeedEventSignalUpdatedSignal,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventSignalUpdatedSignalPayload as WholesaleFeedEventSignalUpdatedSignalPayload,
)
from ._schemas.core.wholesale_feed_event import WholesaleFeedEventType as WholesaleFeedEventEventType
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeed as WholesaleFeedEventWholesaleFeedBulkChangeFeed,
)
from ._schemas.core.wholesale_feed_event import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeedPayload as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayload,
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
    'AccountChangeActor',
    'AccountChangeActorType',
    'AccountChangeOrigin',
    'AccountChangeOriginKind',
    'AccountChangeRecordedWebhook',
    'AccountChangeRecordedWebhookResource',
    'AccountChangeRepair',
    'AccountChangeRepairTask',
    'AccountChangeRepairUnavailableReason',
    'AccountChangeResource',
    'AccountCreditLimit',
    'AccountGovernanceAgentsItem',
    'AccountIdentityChange',
    'AccountIdentityChangeBlocked',
    'AccountIdentityChangePending',
    'AccountIdentityChangePreview',
    'AccountIdentityChangePreviewImpact',
    'AccountIdentityChangePreviewImpactArea',
    'AccountIdentityChangePreviewImpactEffect',
    'AccountIdentityChangePreviewNonblockingImpactsItem',
    'AccountIdentityChangePreviewNonblockingImpactsItemEffect',
    'AccountIdentityChangeRejected',
    'AccountIdentityChangeWouldApply',
    'AccountIdentityChangeWouldRequireApproval',
    'AccountReference',
    'AccountReferenceAccountId',
    'AccountReferenceBrandOperator',
    'AccountReportingBucket',
    'AccountReportingBucketCompression',
    'AccountSetup',
    'AccountStatusChangedWebhook',
    'AccountStatusChangedWebhookReasonCode',
    'AccountStatusChangedWebhookSetup',
    'AccountTimezoneCapability',
    'AccountTimezoneCapabilityAccountSelection',
    'AccountTimezoneCapabilityMode',
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
    'AgentDeclarationsWebhookSigningAlgorithmsItem',
    'AgentEncryptionKey',
    'AgentNotificationConfig',
    'AgentNotificationConfigState',
    'AgentNotificationConfigStateAuthentication',
    'AgentPlacementFormatDeclaration',
    'AgentReportingDestination',
    'AgentReportingDestinationState',
    'AgentReportingDestinationStateSetup',
    'AgentReportingDestinationStateSetupAction',
    'AgentSigningKey',
    'AgentWebhookChallenge',
    'AgentWebhookChallengeDeliveryAuth',
    'AgentWebhookChallengeDeliveryAuthMode',
    'AgentWebhookChallengeEventTypesItem',
    'AgenticAdvertisingOrgVerificationTokenClaims',
    'AgenticAdvertisingOrgVerificationTokenClaimsRole',
    'AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenMode',
    'AppItem',
    'AppItemPlatform',
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
    'AttestationCapabilitiesAcceptedIssuersItem',
    'AttestationCapabilitiesAcceptedIssuersItemResolversItem',
    'AttestationCapabilitiesAcceptedIssuersItemResolversItemAuthentication',
    'AttestationCapabilitiesAcceptedVerifiersItem',
    'AttestationCapabilitiesSupportedDeliveryMethodsItem',
    'AttestationCredentialUriLocator',
    'AttestationEvaluation',
    'AttestationEvaluationActionBinding',
    'AttestationEvaluationOutcome',
    'AttestationIssuer',
    'AttestationIssuerCredentialIdLocator',
    'AttestationOriginIssuer',
    'AttestationReference',
    'AttestationReferenceEmbeddedCredential',
    'AttestationReferenceValidityHint',
    'AttestationReferenceVerifyAgent',
    'AttestationResourceSubject',
    'AttestationSubject',
    'AttributionWindow',
    'AttributionWindowPostClick',
    'AttributionWindowPostView',
    'AudienceActivationMethod',
    'AudienceActivationMethodFileTransfer',
    'AudienceActivationMethodsItemCleanRoom',
    'AudienceActivationMethodsItemDatasetQuery',
    'AudienceActivationMethodsItemFileTransfer',
    'AudienceActivationMethodsItemPlatformDistribution',
    'AudienceActivationMethodsItemTmpIdentityMatch',
    'AudienceCharacteristic',
    'AudienceCharacteristicRange',
    'AudienceCharacteristicTaxonomy',
    'AudienceEvidence',
    'AudienceEvidenceAttestationRefsItem',
    'AudienceEvidenceAttestationRefsItemSubject',
    'AudienceEvidenceBaseline',
    'AudienceEvidenceEvidenceType',
    'AudienceEvidencePin',
    'AudienceEvidenceRelationship',
    'AudienceEvidenceRequirements',
    'AudienceEvidenceRequirementsMaximumAge',
    'AudienceEvidenceSelection',
    'AudienceEvidenceSelectionAttestationEvaluationsItem',
    'AudienceEvidenceSelectionAttestationEvaluationsItemEvaluation',
    'AudienceEvidenceSelectionAttestationEvaluationsItemEvaluationActionBinding',
    'AudienceEvidenceSelectionDecisionUse',
    'AudienceEvidenceUnit',
    'AudienceExclude',
    'AudienceForecastDimension',
    'AudienceInclude',
    'AudienceMember',
    'AudienceMemberUidsItem',
    'AudienceSelector',
    'AudienceSelectorDescription',
    'AudienceSelectorSignalBinary',
    'AudienceSelectorSignalCategorical',
    'AudienceSelectorSignalNumeric',
    'AudienceSource',
    'AudioAsset',
    'AudioAssetRequirements',
    'AudioAssetRequirementsFormatsItem',
    'AuthorizedAgentBaseFields',
    'AxeExcludeSegment',
    'AxeIncludeSegment',
    'BiddingPolicy',
    'BiddingPolicyCapability',
    'BiddingPolicyCapabilityMaxBidWithCostPer',
    'BiddingPolicyCapabilityMaxBidWithRoas',
    'BiddingPolicyCapabilityPolicyProfile',
    'BiddingPolicyCapabilityPolicyProfileModesItem',
    'BiddingPolicyCapabilityScopeCapability',
    'BiddingPolicyCostPer',
    'BiddingPolicyRoas',
    'BiddingPolicyRoasStrength',
    'BleedBottomLeftRightTop',
    'BleedUniform',
    'BlockedImpacts',
    'BrandID',
    'BrandKey',
    'BrandReference',
    'BrandReferenceBrandKitOverride',
    'BrandReferenceBrandKitOverrideColors',
    'BrandReferenceDataSubjectContestation',
    'BrandResponseAuthorizationResult',
    'BrandResponseAuthorizationResultReason',
    'BrandResponseAuthorizationResultTrust',
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
    'BusinessEntityAddress',
    'BusinessEntityBank',
    'BusinessEntityContactsItem',
    'BusinessEntityContactsItemRole',
    'CSSAsset',
    'CSSAssetRequirements',
    'CancellationPolicy',
    'CancellationPolicyCancellationFee',
    'CancellationPolicyCancellationFeeType',
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
    'CanonicalForecastPointMetrics',
    'CanonicalForecastPointViewability',
    'CanonicalForecastVendorMetricValue',
    'CanonicalFormatKind',
    'CanonicalFormatOption',
    'CanonicalFormatOptionFormatKind',
    'CanonicalMeasurementTerms',
    'CanonicalMeasurementTermsBillingMeasurement',
    'CanonicalMeasurementTermsMakegoodPolicy',
    'CanonicalMediaBuyAction',
    'CanonicalMediaBuyActionControlMediaBuy',
    'CanonicalMediaBuyActionControlMediaBuyAction',
    'CanonicalMediaBuyActionFields',
    'CanonicalMediaBuyActionRefineProposals',
    'CanonicalMediaBuyActionRefineProposalsAction',
    'CanonicalMediaBuyActionSyncCreatives',
    'CanonicalMediaBuyActionSyncCreativesAction',
    'CanonicalMediaBuyFeatures',
    'CanonicalMetricQualifier',
    'CanonicalOptimizationGoal',
    'CanonicalOptimizationGoalEvent',
    'CanonicalOptimizationGoalEventEventSourcesItem',
    'CanonicalOptimizationGoalEventTarget',
    'CanonicalOptimizationGoalMetric',
    'CanonicalOptimizationGoalMetricMetric',
    'CanonicalOptimizationGoalMetricTargetFrequency',
    'CanonicalOptimizationGoalVendorMetric',
    'CanonicalOptimizationGoalVendorMetricTarget',
    'CanonicalPerformanceStandard',
    'CanonicalPricingOption',
    'CanonicalProduct',
    'CanonicalProductAction',
    'CanonicalProductCatalogMatch',
    'CanonicalProductPlacement',
    'CanonicalProductPlacementCanonicalDoohPlacementAttributes',
    'CanonicalProductPlacementCanonicalDoohScreenResolution',
    'CanonicalProductPlacementPublisherRef',
    'CanonicalProductPlacementSellerInline',
    'CanonicalProjectionReference',
    'CanonicalProjectionSlotOverride',
    'CanonicalProposal',
    'CanonicalProposalForecast',
    'CanonicalProposalProposalKind',
    'CanonicalProposalTotalBudgetGuidance',
    'CanonicalReportingCapabilities',
    'CanonicalReportingCapabilitiesVendorMetricsItem',
    'CanonicalReportingCommitment',
    'CanonicalReportingCommitmentStandard',
    'CanonicalReportingCommitmentVendor',
    'CanvasConstraint',
    'CanvasConstraintConstraint',
    'CanvasConstraintRegion',
    'CanvasConstraintRegionUnit',
    'CapabilitiesChangedWebhook',
    'CapabilitiesChangedWebhookReason',
    'CardAsset',
    'Catalog',
    'CatalogAsset',
    'CatalogExecutionRequirement',
    'CatalogFieldBinding',
    'CatalogFieldBindingAssetPool',
    'CatalogFieldBindingAssetPoolBinding',
    'CatalogFieldBindingCatalogGroup',
    'CatalogFieldBindingScalar',
    'CatalogFieldBindingScalarBinding',
    'CatalogFieldMapping',
    'CatalogFieldMappingTransform',
    'CatalogItemAvailabilityError',
    'CatalogItemAvailabilityReference',
    'CatalogItemAvailabilityState',
    'CatalogItemAvailabilityStateAvailability',
    'CatalogItemAvailabilityStateStatus',
    'CatalogItemAvailabilityUpdate',
    'CatalogItemAvailabilityUpdateReason',
    'CatalogItemAvailabilityUpdateResult',
    'CatalogItemAvailabilityUpdateResultAction',
    'CatalogItemAvailabilityUpdateResultStatus',
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
    'CollectionDistributionIdentifiersItem',
    'CollectionListApplication',
    'CollectionListApplicationEffect',
    'CollectionListApplicationSummary',
    'CollectionListReference',
    'CollectionPropertyDeliveryMetrics',
    'CollectionReference',
    'CollectionRelatedCollectionsItem',
    'CollectionSelection',
    'CollectionSelector',
    'Color',
    'CommittedMetric',
    'CommittedMetricStandard',
    'CommittedMetricVendor',
    'CommittedMetricVendorQualifier',
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
    'CreativeAssignmentRotationMode',
    'CreativeBrief',
    'CreativeBriefCompliance',
    'CreativeBriefComplianceRequiredDisclosuresItem',
    'CreativeBriefMessaging',
    'CreativeBriefObjective',
    'CreativeConsumption',
    'CreativeDeliveryMetrics',
    'CreativeFilters',
    'CreativeItem',
    'CreativeItemMedia',
    'CreativeItemText',
    'CreativeLocalePolicy',
    'CreativeLocalization',
    'CreativeLocalizationReadback',
    'CreativeLocalizationReadbackLocaleFallbacksItem',
    'CreativeLocalizationReadbackUnmatchedLocaleAction',
    'CreativeLocalizationSource',
    'CreativeLocalizationTargetVariantsItem',
    'CreativeManifest',
    'CreativeOperationFormatDeclaration',
    'CreativePolicy',
    'CreativePolicyAcceptedVerifiersItem',
    'CreativePolicyProvenanceRequirements',
    'CreativeRepresentation',
    'CreativeRepresentationSet',
    'CreativeRepresentationSource',
    'CreativeRevisionID',
    'CreativeVariable',
    'CreativeVariableVariableType',
    'CreativeVariant',
    'CreativeVariantGenerationContext',
    'CreativeVariantGenerationContextArtifact',
    'CurrencyCode',
    'CustomFormatDeclaration',
    'CustomPricing',
    'CustomPricingMetadata',
    'DAASTAsset',
    'DAASTAssetInline',
    'DAASTAssetInlineMacroDeclarationsItem',
    'DAASTAssetInlineMacroDeclarationsItemLocation',
    'DAASTAssetRequirements',
    'DAASTAssetUrl',
    'DAASTAudioFormatDeclaration',
    'DAASTTrackerAsset',
    'DAASTTrackerConstraints',
    'DAASTTrackerConstraintsDaastEvent',
    'DAASTTrackerConstraintsDaastTarget',
    'DaastOffset',
    'DaastVersions',
    'DataProviderSignalSelector',
    'DataProviderSignalSelectorAll',
    'DataProviderSignalSelectorById',
    'DataProviderSignalSelectorByTag',
    'Dataset',
    'DatasetQuery',
    'DatasetQueryConsumerIdentitiesItem',
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
    'DeadlinePolicyMaterialStagesItem',
    'DecimalReportingControlTotal',
    'DeliveryBreakdownControls',
    'DeliveryForecast',
    'DeliveryMetricAggregate',
    'DeliveryMetricAggregateStandard',
    'DeliveryMetricAggregateVendor',
    'DeliveryMetrics',
    'DeliveryMetricsByActionSourceItem',
    'DeliveryMetricsByEventTypeItem',
    'DeliveryMetricsDoohMetrics',
    'DeliveryMetricsDoohMetricsVenueBreakdownItem',
    'DeliveryMetricsOohMetrics',
    'DeliveryMetricsOohMetricsEstimationBasis',
    'DeliveryMetricsOohMetricsPanelsItem',
    'DeliveryMetricsOohMetricsPanelsItemIdentifiersItem',
    'DeliveryMetricsOohMetricsPanelsItemIdentifiersItemIdType',
    'DeliveryMetricsOohMetricsPostingsItem',
    'DeliveryMetricsOohMetricsPostingsItemEventType',
    'DeliveryMetricsQuartileData',
    'DeliveryMetricsReachWindow',
    'DeliveryMetricsReachWindowKind',
    'DeliveryMetricsReachWindowPeriod',
    'DeliveryMetricsTimeBasedViewsItem',
    'DeliveryMetricsViewability',
    'DeliveryMetricsViewabilityViewedSecondsHistogramItem',
    'DeliveryMetricsViewabilityViewedSecondsPercentiles',
    'DeliveryProvider',
    'DeliveryRecipient',
    'DemographicAgeRange',
    'DemographicPredicate',
    'DemographicReportingCapability',
    'DemographicReportingCapabilityAge',
    'DemographicReportingCapabilityAgeIntervalsItem',
    'DemographicReportingCapabilityAgeReportingModesItem',
    'DemographicTargetingCapability',
    'DemographicTargetingCapabilityAge',
    'DemographicTargetingCapabilityAgeExecutionModesItem',
    'DemographicTargetingCapabilityAgeIntervalsItem',
    'DemographicTargetingCapabilityAgeUnknownHandling',
    'DemographicTargetingIntent',
    'DemographicTargetingIntentAge',
    'DemographicTargetingResolution',
    'Deployment',
    'DeploymentAgent',
    'DeploymentPlatform',
    'Destination',
    'DestinationAgent',
    'DestinationItem',
    'DestinationItemDestinationType',
    'DestinationItemLocation',
    'DestinationPlatform',
    'DevicePlatformExclude',
    'DevicePlatformForecastDimension',
    'DeviceTypeExclude',
    'DeviceTypeForecastDimension',
    'DiagnosticIssue',
    'DiagnosticIssueSeverity',
    'DisplayTagAsset',
    'DisplayTagFormatDeclaration',
    'DomainName',
    'DownstreamConnectionExecutionRequirement',
    'DownstreamConnectionExecutionRequirementConnection',
    'DownstreamConnectionRequirement',
    'DownstreamConnectionRequirementConnectionType',
    'DownstreamConnectionRequirementResourceRef',
    'DownstreamConnectionRequirementScope',
    'DownstreamConnectionRequirementStatus',
    'Duration',
    'EducationItem',
    'EducationItemDegreeType',
    'EducationItemLevel',
    'EducationItemModality',
    'Error',
    'ErrorBuyerReason',
    'ErrorIssuesItem',
    'ErrorIssuesItemDiscriminatorItem',
    'ErrorRecovery',
    'ErrorSource',
    'EvaluatorSpec',
    'EvaluatorSpecAgentUrl',
    'EvaluatorSpecEvalBudget',
    'EvaluatorSpecEvaluatorId',
    'EvaluatorSpecExemplars',
    'EvaluatorSpecRankByItem',
    'EvaluatorSpecRankByItemDirection',
    'Event',
    'EventCustomData',
    'EventCustomDataContentsItem',
    'EventSourceExecutionRequirement',
    'EventSourceHealth',
    'EventSourceHealthDetail',
    'EventSurface',
    'EventSurfaceCategory',
    'ExecutionContinuousBounds',
    'ExecutionEnumeratedIntervals',
    'ExecutionSignals',
    'ExperimentalFeatureID',
    'ExtensionObject',
    'FeatureRequirement',
    'FeatureRequirementIfNotCovered',
    'FileTransferDestination',
    'FileTransferDirectionsItem',
    'FileTransferFormat',
    'FinalityPoliciesItemContractualCutoff',
    'FinalityPoliciesItemSourceFinal',
    'FinalityPoliciesItemStabilized',
    'FlatFeePricing',
    'FlatFeePricingPeriod',
    'FlightItem',
    'FlightItemDestination',
    'FlightItemOrigin',
    'ForecastPoint',
    'ForecastPointDimensions',
    'ForecastPointMetrics',
    'ForecastPointMetricsCoverageRate',
    'ForecastPointViewability',
    'ForecastPointViewabilityViewableRate',
    'ForecastRange',
    'ForecastRateRange',
    'ForecastVendorMetricValue',
    'Format',
    'FormatAccessibility',
    'FormatBaseGroupAsset',
    'FormatBaseIndividualAsset',
    'FormatDisclosureCapabilitiesItem',
    'FormatFormatCard',
    'FormatFormatCardDetailed',
    'FormatOptionReference',
    'FormatOptionsItemFormatOptionId',
    'FormatReferenceStructuredObject',
    'FormatRendersItem',
    'FormatRendersItemDimensions',
    'FormatRendersItemDimensionsResponsive',
    'FrequencyCap',
    'FrequencyCapConstraints',
    'FrequencyCapDurationUnit',
    'FrequencyCapImpressionConstraints',
    'FrequencyCapIntervalConstraints',
    'FrequencyCapRequirements',
    'FrequencyCapSuppress',
    'FrequencyCapWindow',
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
    'GeographicPlaceCatalogEntryStatus',
    'GeographicPlaceIdentifierSystem',
    'GeographicPlaceRequirement',
    'GeographicPlaceRequirementCatalogRequirement',
    'GeographicPlaceResolver',
    'GeographicPlaceResolverAuth',
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
    'HTMLAssetAccessibility',
    'HTMLAssetRequirements',
    'HTMLAssetRequirementsSandbox',
    'HostedAudioFormatDeclaration',
    'HostedVideoFormatDeclaration',
    'HotelItem',
    'HotelItemAddress',
    'HoursValue',
    'IANATimezoneIdentifier',
    'IdempotencyKey',
    'Identifier',
    'Ids',
    'ImageAsset',
    'ImageAssetRequirements',
    'ImageAssetRequirementsColorSpace',
    'ImageAssetRequirementsFormatsItem',
    'ImageCarouselFormatDeclaration',
    'ImageFormatDeclaration',
    'Impairment',
    'ImpairmentResourceType',
    'ImpairmentTransition',
    'Indicator',
    'IndicatorBearingResourceState',
    'IndicatorScope',
    'IndicatorsChangedWebhook',
    'IndicatorsChangedWebhookChangeKind',
    'IndicatorsChangedWebhookRelationshipKind',
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
    'InlineMarkupMacroDeclarationsItem',
    'InlineMarkupMacroDeclarationsItemLocation',
    'InlineMarkupMarkupType',
    'InsertionOrder',
    'InsertionOrderTerms',
    'InsertionOrderTermsPaymentTerms',
    'InsertionOrderTermsTotalBudget',
    'Installment',
    'InstallmentDeadlines',
    'InstallmentDeliveryMetrics',
    'InstallmentDerivativeOf',
    'InstallmentPropertyDeliveryMetrics',
    'InstallmentReference',
    'IntegerReportingControlTotal',
    'InventoryListApplication',
    'JavaScriptAsset',
    'JavaScriptAssetRequirements',
    'JavaScriptAssetRequirementsModuleType',
    'JobItem',
    'JobItemEmploymentType',
    'JobItemExperienceLevel',
    'JobItemSalary',
    'JobItemSalaryPeriod',
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
    'MacroDeclarationLocation',
    'MacroDeclarationLocationField',
    'MacroDeclarationUnavailableBehavior',
    'MacroEncoding',
    'MacroEncodingKind',
    'MacroProcessingCapability',
    'MacroProcessingCapabilityMappingStatus',
    'MacroProcessingCapabilityOperation',
    'MacroResolutionResult',
    'MacroResolutionResultStatus',
    'MacroTranslationTarget',
    'MarkdownAsset',
    'MarkdownAssetRequirements',
    'MaterialDeadline',
    'MeasurementReadiness',
    'MeasurementTerms',
    'MeasurementTermsBillingMeasurement',
    'MeasurementTermsMakegoodPolicy',
    'MeasurementWindow',
    'MediaBuy',
    'MediaBuyAvailableAction',
    'MediaBuyAvailableActionID',
    'MediaBuyAvailableActionTask',
    'MediaBuyBidding',
    'MediaBuyCancellation',
    'MediaBuyChangeTermID',
    'MediaBuyCommitmentResponseCompleted',
    'MediaBuyCommitmentResponseFailed',
    'MediaBuyCommitmentResponseSubmitted',
    'MediaBuyFeatures',
    'MediaBuyFeaturesBiddingPolicy',
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
    'NotificationConfigAuthentication',
    'NotificationConfigEventTypesItem',
    'NotificationConfigProductPayloadView',
    'ObjAllValues',
    'ObjScopeMetricIdQualifier',
    'ObjValues',
    'Offering',
    'OfferingAssetConstraint',
    'OfferingAssetGroup',
    'OfferingGeoTargets',
    'OfferingGeoTargetsMetrosItem',
    'OperatorIdentity',
    'OperatorUnit',
    'OpportunityContext',
    'OpportunityContextCloseReason',
    'OpportunityContextIntent',
    'OpportunityContextPhase',
    'OpportunityContextStatus',
    'OptimizationGoal',
    'OptimizationGoalEvent',
    'OptimizationGoalEventAttributionWindow',
    'OptimizationGoalEventEventSourcesItem',
    'OptimizationGoalEventTargetCostPer',
    'OptimizationGoalMetric',
    'OptimizationGoalMetricMetric',
    'OptimizationGoalMetricTargetCostPer',
    'OptimizationGoalMetricTargetFrequency',
    'OptimizationGoalMetricTargetFrequencyWindow',
    'OptimizationGoalMetricTargetThresholdRate',
    'OptimizationGoalMetricVendor',
    'OptimizationGoalVendorMetric',
    'OptimizationGoalVendorMetricTargetCostPer',
    'OptimizationGoalVendorMetricTargetThresholdRate',
    'OutcomeMeasurement',
    'OutcomeMeasurementWindow',
    'OutcomeTargetCostPer',
    'Overlay',
    'OverlayBounds',
    'OverlayBoundsUnit',
    'OverlayVisual',
    'Package',
    'PackageBidding',
    'PackageCancellation',
    'PackageDeliveryMetricValue',
    'PackageDeliveryMetricValueQualifier',
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
    'PackageFormatSnapshotPlacementRefsItem',
    'PackageFormatSnapshotResponsiveCreative',
    'PackageFormatSnapshotSellerRenderedStatefulDisplay',
    'PackageFormatSnapshotSponsoredPlacement',
    'PackageFormatSnapshotVideoHosted',
    'PackageFormatSnapshotVideoVast',
    'PackageSignalTargeting',
    'PackageSignalTargetingBinary',
    'PackageSignalTargetingCategorical',
    'PackageSignalTargetingGroup',
    'PackageSignalTargetingGroupOperator',
    'PackageSignalTargetingGroups',
    'PackageSignalTargetingGroupsOperator',
    'PackageSignalTargetingNumeric',
    'PackageTargetingResolution',
    'PaginationRequest',
    'PaginationResponse',
    'PairedRedirect',
    'PairedRedirectMacroDeclarationsItem',
    'PairedRedirectMacroDeclarationsItemLocation',
    'PairedRedirectMacroDeclarationsItemLocationField',
    'PerUnitPricing',
    'PercentOfMediaPricing',
    'PerformanceFeedback',
    'PerformanceFeedbackAssertion',
    'PerformanceFeedbackAssertionEvidence',
    'PerformanceFeedbackAssertionEvidenceConfidenceInterval',
    'PerformanceFeedbackMetric',
    'PerformanceFeedbackMetricStandard',
    'PerformanceFeedbackMetricVendor',
    'PerformanceFeedbackStatus',
    'PerformanceStandard',
    'PixelTrackerAsset',
    'PixelTrackerAssetMethod',
    'Placement',
    'PlacementDefinition',
    'PlacementDefinitionIdentifiersItem',
    'PlacementDefinitionPublisherDoohPlacementAttributes',
    'PlacementDefinitionPublisherDoohScreenResolution',
    'PlacementDeliveryMetrics',
    'PlacementEvidence',
    'PlacementForecastDimension',
    'PlacementIdentity',
    'PlacementKind',
    'PlacementMode',
    'PlacementPresentationDocument',
    'PlacementPresentationDocumentBoxDecoration',
    'PlacementPresentationDocumentCanvas',
    'PlacementPresentationDocumentCreativeSlot',
    'PlacementPresentationDocumentCreativeSlotFit',
    'PlacementPresentationDocumentImageDecoration',
    'PlacementPresentationDocumentImageDecorationFit',
    'PlacementPresentationDocumentImageDecorationImageRef',
    'PlacementPresentationDocumentLayer',
    'PlacementPresentationDocumentRectangle',
    'PlacementPresentationDocumentTextDecoration',
    'PlacementPresentationReference',
    'PlacementProductDoohPlacementAttributes',
    'PlacementProductDoohScreenResolution',
    'PlacementPropertyDeliveryMetrics',
    'PlacementReference',
    'PlacementSelection',
    'PlannedDelivery',
    'PlannedDeliveryBidding',
    'PlannedDeliveryGeo',
    'PlatformDistribution',
    'PlatformExtensionReference',
    'PlatformSegment',
    'PositivePostalAreaSupport',
    'PostalArea',
    'PostalAreaAUPostcode',
    'PostalAreaBRCep',
    'PostalAreaBranch9',
    'PostalAreaBranch9System',
    'PostalAreaCA',
    'PostalAreaCountrySystemValues',
    'PostalAreaFRCodePostal',
    'PostalAreaGB',
    'PostalAreaINPin',
    'PostalAreaPlz',
    'PostalAreaSupport',
    'PostalAreaSupportValueItem',
    'PostalAreaUS',
    'PostalAreaWithFusedSystem',
    'PostalAreaZAPostalCode',
    'PostalCountrySystem',
    'PostalCountrySystemAUPostcode',
    'PostalCountrySystemBRCep',
    'PostalCountrySystemBranch9',
    'PostalCountrySystemBranch9System',
    'PostalCountrySystemCA',
    'PostalCountrySystemCASystem',
    'PostalCountrySystemFRCodePostal',
    'PostalCountrySystemGB',
    'PostalCountrySystemGBSystem',
    'PostalCountrySystemINPin',
    'PostalCountrySystemPlz',
    'PostalCountrySystemPlzCountry',
    'PostalCountrySystemUS',
    'PostalCountrySystemUSSystem',
    'PostalCountrySystemZAPostalCode',
    'PreviewRendererMetadata',
    'PreviewRendererMetadataRenderingOrigin',
    'Price',
    'PricePeriod',
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
    'PrincipalChangedWebhookReason',
    'PrincipalDeclarationsState',
    'PrincipalDeclarationsStateExclusionsItem',
    'PrincipalDeclarationsStateExclusionsItemAxis',
    'PrincipalState',
    'PrincipalStateRetiredDestinationsItem',
    'Product',
    'ProductAllocation',
    'ProductAllowedAction',
    'ProductAudienceActivation',
    'ProductAudienceEvidenceRequirements',
    'ProductAudienceEvidenceRequirementsEvidencePresence',
    'ProductAudienceEvidenceRequirementsMaximumAge',
    'ProductAudienceEvidenceRequirementsMaximumAgeUnit',
    'ProductAudienceEvidenceRequirementsRequirementMode',
    'ProductCardReferenceAsset',
    'ProductCardReferenceAssetRole',
    'ProductCatalogMatch',
    'ProductChangeMap',
    'ProductChangeMapValue',
    'ProductConversionTracking',
    'ProductConversionTrackingSupportedTargetsItem',
    'ProductDefaultCollections',
    'ProductDefaultPlacements',
    'ProductDeliveryMeasurement',
    'ProductExecutionRequirement',
    'ProductFilters',
    'ProductFiltersGeoProximityItem',
    'ProductFiltersKeywordsItem',
    'ProductFiltersMetrosItem',
    'ProductFiltersRequiredGeoTargetingItem',
    'ProductFiltersRequiredVendorMetricsItem',
    'ProductFiltersSignalTargetingItem',
    'ProductFiltersSignalTargetingItemTargetingMode',
    'ProductFiltersTrustedMatch',
    'ProductFiltersTrustedMatchProvidersItem',
    'ProductFormatDeclaration',
    'ProductFormatDeclarationSellerPreference',
    'ProductIdentity',
    'ProductLocalFormatOptionReference',
    'ProductMaterialSubmission',
    'ProductMediaBuySupport',
    'ProductMediaBuySupportRequirements',
    'ProductMetricOptimization',
    'ProductMetricOptimizationSupportedTargetsItem',
    'ProductOfferFilters',
    'ProductOfferFiltersAvailabilityHorizon',
    'ProductOfferFiltersRequiredFeatures',
    'ProductOfferFiltersRequiredPerformanceStandardsItem',
    'ProductOfferFiltersRequiredVendorMetricsItem',
    'ProductProductCard',
    'ProductProductCardDetailed',
    'ProductProductCardDetailedSpecificationsItem',
    'ProductSignalTargetingOption',
    'ProductSignalTargetingOptionActivationStatus',
    'ProductSignalTargetingOptionAllowedTargetingModesItem',
    'ProductTargetingResolution',
    'ProductTrustedMatch',
    'ProductTrustedMatchProvidersItem',
    'Property',
    'PropertyDeliveryMetrics',
    'PropertyID',
    'PropertyListApplication',
    'PropertyListApplicationEffect',
    'PropertyListApplicationSummary',
    'PropertyListReference',
    'PropertyReference',
    'PropertyTag',
    'Proposal',
    'ProposalTotalBudgetGuidance',
    'ProtocolEnvelope',
    'ProtocolResponse',
    'Provenance',
    'ProvenanceAiTool',
    'ProvenanceC2pa',
    'ProvenanceDeclaredBy',
    'ProvenanceDeclaredByRole',
    'ProvenanceDisclosure',
    'ProvenanceDisclosureJurisdictionsItem',
    'ProvenanceDisclosureJurisdictionsItemRenderGuidance',
    'ProvenanceEmbeddedProvenanceItem',
    'ProvenanceEmbeddedProvenanceItemVerifyAgent',
    'ProvenanceHumanOversight',
    'ProvenanceVerificationItem',
    'ProvenanceVerificationItemResult',
    'ProvenanceWatermarksItem',
    'ProvenanceWatermarksItemVerifyAgent',
    'ProvisionBinding',
    'ProvisionRecipient',
    'ProvisionRecipientProvider',
    'ProvisionRecipientRecipient',
    'PublishedPostAsset',
    'PublishedPostAssetIdentityRef',
    'PublishedPostAssetReferenceAuthorization',
    'PublishedPostAssetReferenceAuthorizationStatus',
    'PublisherCatalogFormatOptionReference',
    'PublisherCatalogPlacementIdentity',
    'PublisherDesignatedPreviewProvider',
    'PublisherDesignatedPreviewProviderRoutesItem',
    'PublisherPropertySelector',
    'PublisherPropertySelectorAll',
    'PublisherPropertySelectorById',
    'PublisherPropertySelectorByTag',
    'PushNotificationConfig',
    'PushNotificationConfigAuthentication',
    'Query',
    'RealEstateItem',
    'RealEstateItemArea',
    'RealEstateItemAreaUnit',
    'RealEstateItemListingType',
    'RealEstateItemPropertyType',
    'ReferenceAsset',
    'ReferenceAssetRole',
    'ReferenceRenderer',
    'ReferenceRendererProvenance',
    'RefineProposalsAsyncSubmitted',
    'RegistryEvent',
    'RegistryEventAgentComplianceChangedAgent',
    'RegistryEventAgentDiscoveredAgent',
    'RegistryEventAgentDiscoveredAgentPayload',
    'RegistryEventAgentProfilePayload',
    'RegistryEventAgentProfilePayloadType',
    'RegistryEventAgentProfileUpdatedAgent',
    'RegistryEventAgentProfileUpdatedAgentPayload',
    'RegistryEventAgentRemovedAgent',
    'RegistryEventAgentRemovedAgentPayload',
    'RegistryEventAgentVerificationEarnedAgent',
    'RegistryEventAgentVerificationEarnedAgentPayload',
    'RegistryEventAgentVerificationEarnedAgentPayloadGradingProfile',
    'RegistryEventAgentVerificationLostAgent',
    'RegistryEventAgentVerificationLostAgentPayload',
    'RegistryEventAuthorizationGrantedAuthorization',
    'RegistryEventAuthorizationModifiedAuthorization',
    'RegistryEventAuthorizationPayload',
    'RegistryEventAuthorizationPayloadAuthorizationType',
    'RegistryEventAuthorizationPayloadEvidence',
    'RegistryEventAuthorizationRevokedAuthorization',
    'RegistryEventClassification',
    'RegistryEventCollectionCreatedCollection',
    'RegistryEventCollectionCreatedCollectionPayload',
    'RegistryEventCollectionIdentifier',
    'RegistryEventCollectionMergedCollection',
    'RegistryEventCollectionMergedCollectionPayload',
    'RegistryEventCollectionPayload',
    'RegistryEventCollectionPayloadStatus',
    'RegistryEventCollectionRemovedCollection',
    'RegistryEventCollectionRemovedCollectionPayload',
    'RegistryEventCollectionUpdatedCollection',
    'RegistryEventCollectionUpdatedCollectionPayload',
    'RegistryEventCompliancePayload',
    'RegistryEventCompliancePayloadStoryboardsItem',
    'RegistryEventCompliancePayloadTracksValue',
    'RegistryEventComplianceStatus',
    'RegistryEventEntityType',
    'RegistryEventEventType',
    'RegistryEventPropertyCreatedProperty',
    'RegistryEventPropertyCreatedPropertyPayload',
    'RegistryEventPropertyMergedProperty',
    'RegistryEventPropertyMergedPropertyPayload',
    'RegistryEventPropertyPayload',
    'RegistryEventPropertyReactivatedProperty',
    'RegistryEventPropertyReactivatedPropertyPayload',
    'RegistryEventPropertySource',
    'RegistryEventPropertyStaleProperty',
    'RegistryEventPropertyStalePropertyPayload',
    'RegistryEventPropertyUpdatedProperty',
    'RegistryEventPropertyUpdatedPropertyPayload',
    'RegistryEventPublisherAdagentsChangedPublisher',
    'RegistryEventPublisherAdagentsChangedPublisherPayload',
    'RegistryEventPublisherAdagentsDiscoveredPublisher',
    'RegistryEventPublisherAdagentsPayload',
    'RegistryEventStoryboardStatus',
    'RegistryFeedResponse',
    'RegistryFeedResponseFreshness',
    'RemoveTargetingSetValues',
    'RemoveTargetingSetValuesPath',
    'RemoveTargetingSetValuesSelector',
    'RendersItemDimensions',
    'RendersItemParametersFromFormatId',
    'RepeatableGroupAsset',
    'RepeatableGroupAssetSelectionMode',
    'ReplaceTargetingValue',
    'ReportingAdjustment',
    'ReportingAdjustmentAccountingPeriod',
    'ReportingAdjustmentReasonCode',
    'ReportingAdjustmentReceipt',
    'ReportingAdjustmentReceiptStatus',
    'ReportingAdjustmentRejectionCode',
    'ReportingCanonicalContentDigest',
    'ReportingCanonicalizationContract',
    'ReportingCanonicalizationContractGoldenVectors',
    'ReportingCanonicalizationContractGoldenVectorsAdditionalItem',
    'ReportingCanonicalizationContractGoldenVectorsEmptyReport',
    'ReportingCanonicalizationContractGoldenVectorsOrderingEncoding',
    'ReportingCapabilities',
    'ReportingCapabilitiesDateRangeSupport',
    'ReportingCapabilitiesVendorMetricsItem',
    'ReportingConsumerStatus',
    'ReportingConsumerStatusConsumerStatus',
    'ReportingConsumerStatusFailureCode',
    'ReportingConsumerStatusMismatchCode',
    'ReportingConsumerStatusPeriod',
    'ReportingControlTotal',
    'ReportingCoverage',
    'ReportingCoverageLimitationsItem',
    'ReportingCoverageLimitationsItemReason',
    'ReportingCoverageStatus',
    'ReportingDatasetShareDestination',
    'ReportingDatasetShareDestinationExisting',
    'ReportingDeliveryCapabilities',
    'ReportingDeliveryCapabilitiesOperationsContact',
    'ReportingDeliveryConfiguration',
    'ReportingDeliveryConfigurationAuthoritativeParty',
    'ReportingDeliveryConfigurationCoverageRequirement',
    'ReportingDeliveryConfigurationScope',
    'ReportingDeliveryConfigurationState',
    'ReportingDeliveryConfigurationStateReportingDeliveryConfigLifecycleState',
    'ReportingDeliveryConfigurationStateSetup',
    'ReportingDeliveryConfigurationStateSetupAction',
    'ReportingDeliveryMethod',
    'ReportingDeliveryMethodFileTransfer',
    'ReportingDeliveryMethodReportingOrchestration',
    'ReportingDeliveryOffering',
    'ReportingDeliveryOfferingID',
    'ReportingDeliveryOfferingMethod',
    'ReportingDeliveryOfferingMethodDestinationModesItem',
    'ReportingDeliveryOfferingMethodProducerIdentity',
    'ReportingDeliveryOfferingReportingDeliveryPattern',
    'ReportingDeliveryOfferingReportingFeedPurpose',
    'ReportingDeliveryOfferingReportingProfile',
    'ReportingDeliveryReadyWebhook',
    'ReportingDeliveryReadyWebhookReadiness',
    'ReportingFileCompression',
    'ReportingFileEntry',
    'ReportingFileManifest',
    'ReportingFileObjectReference',
    'ReportingLedgerChangedWebhook',
    'ReportingLedgerChangedWebhookChangeKind',
    'ReportingMaterialization',
    'ReportingMaterializationStatus',
    'ReportingMediaBuyId',
    'ReportingNativeVersionReference',
    'ReportingObligation',
    'ReportingObligationProductionStatus',
    'ReportingObligationReconciliationStatus',
    'ReportingPackageId',
    'ReportingPrimaryKey',
    'ReportingReaderCompatibilityItem',
    'ReportingReceipt',
    'ReportingReceiptStatus',
    'ReportingReconciliationMode',
    'ReportingReliabilityStatistics',
    'ReportingReliabilityStatisticsAdjustmentMagnitudeItem',
    'ReportingReliabilityStatisticsEvidence',
    'ReportingReliabilityStatisticsEvidenceBasis',
    'ReportingReliabilityStatisticsLatencyPercentiles',
    'ReportingReliabilityStatisticsReportingReliabilityMeasurementPeriod',
    'ReportingReportDefinition',
    'ReportingReportDefinitionCalendar',
    'ReportingReportDefinitionMetricsItem',
    'ReportingReportDefinitionMetricsItemAggregation',
    'ReportingReportDefinitionReportCalendarTimezoneBasis',
    'ReportingReportDefinitionRestatementPolicy',
    'ReportingReportDefinitionSource',
    'ReportingResource',
    'ReportingResourceImmutability',
    'ReportingResourceKind',
    'ReportingRevision',
    'ReportingRevisionDataThroughPrecision',
    'ReportingRevisionFinalityBasis',
    'ReportingSchedule',
    'ReportingScheduleOffering',
    'ReportingScheduleOfferingPeriodAnchorPolicy',
    'ReportingScheduleOfferingPeriodTimezonePolicy',
    'ReportingScheduleReportingScheduleAlignment',
    'ReportingStatusChangedWebhook',
    'ReportingStatusIssue',
    'ReportingStatusIssueCode',
    'ReportingStatusIssueIssueState',
    'ReportingStatusIssueRecommendedAction',
    'ReportingStatusIssueReportingStatusSeverity',
    'ReportingStatusIssueResponsibleParty',
    'ReportingVerification',
    'ReportingVerificationNativeCommitEvidence',
    'ReportingVerificationNativeCommitEvidenceObservedThrough',
    'ReportingVerificationProfile',
    'ReportingVerificationProfileSet',
    'ReportingVerificationVerificationPath',
    'ReportingWebhook',
    'ReportingWebhookReportingFrequency',
    'ReportingWriteDestination',
    'ReportingWriteDestinationExisting',
    'RepresentationDestination',
    'RepresentationRejection',
    'RepresentationRejectionCode',
    'RepresentationSelection',
    'RequestProposalsAsyncSubmitted',
    'ResolvedAssets',
    'ResponsePayloadJWSEnvelope',
    'ResponsePayloadJWSEnvelopeResponsePayload',
    'ResponsePayloadJWSEnvelopeResponsePayloadTask',
    'ResponsiveCreativeFormatDeclaration',
    'RightsAttestationEvaluation',
    'RightsAttestationEvaluationEvaluation',
    'RightsAttestationEvaluationEvaluationActionBinding',
    'RightsAttestationEvaluationReference',
    'RightsConstraint',
    'RightsConstraintApprovalStatus',
    'RightsConstraintAttestationRefsItem',
    'RightsConstraintAttestationRefsItemSubject',
    'RightsConstraintDisclosure',
    'RightsConstraintGrantStatus',
    'RightsConstraintRightsAgent',
    'SHA256PhysicalChecksum',
    'SHA512PhysicalChecksum',
    'SLAWindow',
    'ScopedCreativeApproval',
    'SelectedCollections',
    'SelectedCollectionsCollectionsItem',
    'SelectedPlacements',
    'SellerAgentReference',
    'SellerInlinePlacementIdentity',
    'SellerRenderedStatefulDisplayFormatDeclaration',
    'SignalCoverageForecast',
    'SignalCoverageForecastBucketCompleteness',
    'SignalCoverageForecastBucketSemantics',
    'SignalCoverageForecastPointsItem',
    'SignalCoverageForecastPointsItemMetrics',
    'SignalCoverageForecastScope',
    'SignalCoverageForecastScopeKind',
    'SignalDefinition',
    'SignalDefinitionArt9Basis',
    'SignalDefinitionAudienceScope',
    'SignalDefinitionDataSourcesItem',
    'SignalDefinitionDataSubjectRights',
    'SignalDefinitionDataSubjectRightsChannelsItem',
    'SignalDefinitionDataSubjectRightsChannelsItemRightsItem',
    'SignalDefinitionEnrichment',
    'SignalDefinitionIdTypesItem',
    'SignalDefinitionLookbackWindow',
    'SignalDefinitionMethodology',
    'SignalDefinitionModeling',
    'SignalDefinitionModelingAiActRiskClass',
    'SignalDefinitionModelingMethod',
    'SignalDefinitionModelingSeedSource',
    'SignalDefinitionModelingSeedSourceType',
    'SignalDefinitionOnboarder',
    'SignalDefinitionOnboarderMatchKeysItem',
    'SignalDefinitionOnboarderPreOnboardingPrecisionLevel',
    'SignalDefinitionRange',
    'SignalDefinitionRefreshCadence',
    'SignalDefinitionTaxonomy',
    'SignalDefinitionTaxonomyParentMatchBehavior',
    'SignalDefinitionTaxonomyValueMappingsItem',
    'SignalDefinitionTaxonomyValuesItem',
    'SignalFilters',
    'SignalForecastDimension',
    'SignalForecastDimensionPresence',
    'SignalID',
    'SignalIDAgent',
    'SignalIDCatalog',
    'SignalListing',
    'SignalListingRange',
    'SignalModelingDisclosure',
    'SignalModelingDisclosureJurisdictionsItem',
    'SignalModelingDisclosureJurisdictionsItemAudience',
    'SignalPricingOption',
    'SignalRef',
    'SignalRefDataProvider',
    'SignalRefProduct',
    'SignalRefSignalSource',
    'SignalSelectionGroupRule',
    'SignalSelectionGroupRuleSelectionMode',
    'SignalSelectionGroupRuleTargetingMode',
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
    'SignalTargetingRulesResolutionModel',
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
    'TMPIdentityMatchBuyerAgent',
    'TagURL',
    'TagURLMacroDeclarationsItem',
    'Tags',
    'Talent',
    'TargetLocalizationReadback',
    'TargetMaximizeValue',
    'TargetPerAdSpend',
    'TargetingModification',
    'TargetingOverlay',
    'TargetingOverlayAgeRestriction',
    'TargetingOverlayDevicePlatform',
    'TargetingOverlayDeviceType',
    'TargetingOverlayGeoProximity',
    'TargetingOverlayGeoProximityItem',
    'TargetingOverlayGeoProximityItemGeometry',
    'TargetingOverlayGeoProximityItemGeometryType',
    'TargetingOverlayGeoProximityItemRadius',
    'TargetingOverlayGeoProximityItemTravelTime',
    'TargetingOverlayInput',
    'TargetingOverlayRequirements',
    'TargetingOverlayRequirementsDemographicsAge',
    'TargetingOverlayRequirementsGeoProximity',
    'TargetingOverlayRequirementsRequired',
    'TargetingOverlayStoreCatchmentsItem',
    'TargetingOverlaySupport',
    'TargetingOverlaySupportDemographicsAge',
    'TargetingOverlaySupportFrequencyCapSupport',
    'TargetingOverlaySupportGeoProximity',
    'TargetingOverlaySupportPlaceCatalogSupport',
    'TargetingOverlaySupportPlaceSupport',
    'TargetingOverlaySupportPlacementSelection',
    'TargetingUnknownAgeEligibilityConstraint',
    'TargetingVerifiedAgeBasisConstraint',
    'TasksGetRequest',
    'TasksGetResponse',
    'TasksGetResponseError',
    'TasksGetResponseErrorDetails',
    'TasksGetResponseHistoryItem',
    'TasksGetResponseProgress',
    'TasksListRequest',
    'TasksListRequestFilters',
    'TasksListRequestSort',
    'TasksListRequestSortField',
    'TasksListResponse',
    'TasksListResponseQuerySummary',
    'TasksListResponseQuerySummaryDomainBreakdown',
    'TasksListResponseQuerySummarySortApplied',
    'TasksListResponseTasksItem',
    'TasksListResponseTasksItemDomain',
    'TextAsset',
    'TextAssetRequirements',
    'TimeForecastDimension',
    'TrackerExecutionContract',
    'TrackerExecutionSelector',
    'TrackerExecutionSelectorDaastTracker',
    'TrackerExecutionSelectorPixelTrackerImg',
    'TrackerExecutionSelectorVastTracker',
    'Transformer',
    'TransformerMultiplicity',
    'TransformerMultiplicityVariantDimensionsItem',
    'TransformerParam',
    'TransformerParamOptionsItem',
    'TransformerParamType',
    'TransformerParamValueSource',
    'TransformerVoiceSynthesisRefItem',
    'TransformerVoiceSynthesisRefItemBrandAgent',
    'TruncationSentinel',
    'TruncationSentinelTruncation',
    'URLAsset',
    'URLAssetMacroDeclarationsItem',
    'URLAssetMacroDeclarationsItemLocation',
    'URLAssetRequirements',
    'URLAssetRequirementsProtocolsItem',
    'URLAssetRequirementsRole',
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
    'VASTTrackerAssetTarget',
    'VASTTrackerConstraints',
    'VASTTrackerConstraintsVastEvent',
    'VASTTrackerConstraintsVastTarget',
    'VASTVideoFormatDeclaration',
    'VastOffset',
    'VastVersions',
    'VehicleItem',
    'VehicleItemBodyStyle',
    'VehicleItemCondition',
    'VehicleItemFuelType',
    'VehicleItemMileage',
    'VehicleItemMileageUnit',
    'VehicleItemTransmission',
    'VendorMetricID',
    'VendorMetricOptimization',
    'VendorMetricOptimizationSupportedMetric',
    'VendorMetricOptimizationSupportedMetricSupportedTargetsItem',
    'VendorMetricValue',
    'VendorPricing',
    'VendorPricingOption',
    'VendorPricingOptionCpm',
    'VendorPricingOptionCustom',
    'VendorPricingOptionFlatFee',
    'VendorPricingOptionPerUnit',
    'VendorPricingOptionPercentOfMedia',
    'VideoAsset',
    'VideoAssetAudioBitDepth',
    'VideoAssetChromaSubsampling',
    'VideoAssetColorSpace',
    'VideoAssetHdrFormat',
    'VideoAssetRequirements',
    'VideoAssetRequirementsAudioCodecsItem',
    'VideoAssetRequirementsContainersItem',
    'VideoAssetVideoBitDepth',
    'WarehouseMaterialization',
    'WarehouseMaterializationDestination',
    'Warning',
    'WarningAffectedResource',
    'WarningAffectedResourceResourceType',
    'WebhookActivityRecord',
    'WebhookActivityRecordStatus',
    'WebhookAsset',
    'WebhookAssetRequirements',
    'WebhookAssetSecurity',
    'WebhookChallenge',
    'WebhookChallengeResponse',
    'WholesaleFeedEvent',
    'WholesaleFeedEventEntityType',
    'WholesaleFeedEventEventType',
    'WholesaleFeedEventProductCreatedProduct',
    'WholesaleFeedEventProductCreatedProductPayload',
    'WholesaleFeedEventProductPricedProduct',
    'WholesaleFeedEventProductPricedProductPayload',
    'WholesaleFeedEventProductRemovedProduct',
    'WholesaleFeedEventProductRemovedProductPayload',
    'WholesaleFeedEventProductUpdatedProduct',
    'WholesaleFeedEventProductUpdatedProductPayload',
    'WholesaleFeedEventRemovalReason',
    'WholesaleFeedEventSignal',
    'WholesaleFeedEventSignalCreatedSignal',
    'WholesaleFeedEventSignalCreatedSignalPayload',
    'WholesaleFeedEventSignalPricedSignal',
    'WholesaleFeedEventSignalPricedSignalPayload',
    'WholesaleFeedEventSignalRemovedSignal',
    'WholesaleFeedEventSignalRemovedSignalPayload',
    'WholesaleFeedEventSignalUpdatedSignal',
    'WholesaleFeedEventSignalUpdatedSignalPayload',
    'WholesaleFeedEventWholesaleFeedBulkChangeFeed',
    'WholesaleFeedEventWholesaleFeedBulkChangeFeedPayload',
    'WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadAffectedEntityType',
    'WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadRecommendation',
    'WholesaleFeedWebhook',
    'XEntityTypes',
    'ZipAsset',
]
