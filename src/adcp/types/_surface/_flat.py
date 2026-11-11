"""Every word the domain aggregators publish, consolidated into one namespace.

Nothing here is a path a consumer writes and nothing here is declared: each name is
re-exported from the domain aggregator beside this module, which re-exported it from
the private module the document compiled to.  The object is the one the runtime
validates into -- ``isinstance`` against a name imported from here is true.

The one reader is ``adcp.types.__getattr__``, the lazy compatibility facade: an
application that wrote ``from adcp.types import <Name>`` is owed an answer for every
name this compiler emitted, and the per-domain aggregators cannot give it one
because the flat spelling names no domain.  The PUBLIC path for every name here is
still ``adcp.types.<domain>``.

Generated from the compiler's own record of what it exported, so a document added
upstream appears here with nothing edited.  A word more than one domain publishes is
DECLINED rather than resolved to a winner and is named in ``__adcp_ambiguous__``:
a flat namespace has one slot for the word, the domains have two classes, and
picking one would hand a consumer a class whose document they did not name.

**AND READING 10's ALIAS WORDS ARE HERE BESIDE THEM**: upstream's own published
spelling of a class of ours, which the private module already states as an
``X = <symbol>`` and which no domain aggregator carries -- the class has its one
domain path under its own word, and a second would be the path reading 6 forbids.
This is the ONE namespace a flat import resolves at, so it is the one place such a
spelling belongs.  A word the surface above already publishes, or that upstream's
generator derived from a property key two documents share, is DECLINED and named
in ``__adcp_alias_declined__``.
"""

from __future__ import annotations

from .._schemas.a2ui.bound_value import A2UiBoundValue as A2UiBoundValue
from .._schemas.a2ui.bound_value import A2UiBoundValue1 as A2UiBoundValue1
from .._schemas.a2ui.bound_value import A2UiBoundValue2 as A2UiBoundValue2
from .._schemas.a2ui.bound_value import A2UiBoundValue3 as A2UiBoundValue3
from .._schemas.a2ui.bound_value import A2UiBoundValue4 as A2UiBoundValue4
from .._schemas.a2ui.bound_value import A2UiBoundValue5 as A2UiBoundValue5
from .._schemas.a2ui.component import A2UiComponent as A2UiComponent
from .._schemas.a2ui.si_catalog import Component as Component
from .._schemas.a2ui.si_catalog import SiComponentCatalog as SiComponentCatalog
from .._schemas.a2ui.surface import A2UiSurface as A2UiSurface
from .._schemas.a2ui.user_action import A2UiUserAction as A2UiUserAction
from .._schemas.aao.agent_publishers import (
    AaoDirectoryAgentPublishersInverseLookupResponse as AaoDirectoryAgentPublishersInverseLookupResponse,
)
from .._schemas.account.get_account_financials_response import (
    GetAccountFinancialsResponse1 as GetAccountFinancialsResponse1,
)
from .._schemas.account.get_account_financials_response import (
    GetAccountFinancialsResponse2 as GetAccountFinancialsResponse2,
)
from .._schemas.account.sync_accounts_request import Accounts as Accounts
from .._schemas.account.sync_accounts_request import Accounts1 as Accounts1
from .._schemas.account.sync_accounts_response import SyncAccountsResponse1 as SyncAccountsResponse1
from .._schemas.account.sync_accounts_response import SyncAccountsResponse2 as SyncAccountsResponse2
from .._schemas.account.sync_governance_response import SyncGovernanceResponse1 as SyncGovernanceResponse1
from .._schemas.account.sync_governance_response import SyncGovernanceResponse2 as SyncGovernanceResponse2
from .._schemas.adagents import AdcpAgentsAuthorization as AdcpAgentsAuthorization
from .._schemas.adagents import AdcpAgentsAuthorization1 as AdcpAgentsAuthorization1
from .._schemas.adagents import RevokedPublisherDomain as RevokedPublisherDomain
from .._schemas.adagents import RevokedPublisherDomain1 as RevokedPublisherDomain1
from .._schemas.adagents import RevokedPublisherDomain2 as RevokedPublisherDomain2
from .._schemas.adagents import RevokedPublisherDomain3 as RevokedPublisherDomain3
from .._schemas.adagents import RevokedPublisherDomain4 as RevokedPublisherDomain4
from .._schemas.adagents import RevokedPublisherDomain5 as RevokedPublisherDomain5
from .._schemas.adagents import RevokedPublisherDomain6 as RevokedPublisherDomain6
from .._schemas.brand.acquire_rights_response import AcquireRightsResponse1 as AcquireRightsResponse1
from .._schemas.brand.acquire_rights_response import AcquireRightsResponse2 as AcquireRightsResponse2
from .._schemas.brand.acquire_rights_response import AcquireRightsResponse3 as AcquireRightsResponse3
from .._schemas.brand.acquire_rights_response import AcquireRightsResponse4 as AcquireRightsResponse4
from .._schemas.brand.creative_approval_response import CreativeApprovalResponse1 as CreativeApprovalResponse1
from .._schemas.brand.creative_approval_response import CreativeApprovalResponse2 as CreativeApprovalResponse2
from .._schemas.brand.creative_approval_response import CreativeApprovalResponse3 as CreativeApprovalResponse3
from .._schemas.brand.creative_approval_response import CreativeApprovalResponse4 as CreativeApprovalResponse4
from .._schemas.brand.get_brand_identity_response import Asset as Asset
from .._schemas.brand.get_brand_identity_response import FontRole2 as FontRole2
from .._schemas.brand.get_brand_identity_response import GetBrandIdentityResponse1 as GetBrandIdentityResponse1
from .._schemas.brand.get_brand_identity_response import GetBrandIdentityResponse2 as GetBrandIdentityResponse2
from .._schemas.brand.get_brand_identity_response import House as House
from .._schemas.brand.get_rights_response import Excluded as Excluded
from .._schemas.brand.get_rights_response import GetRightsResponse1 as GetRightsResponse1
from .._schemas.brand.get_rights_response import GetRightsResponse2 as GetRightsResponse2
from .._schemas.brand.get_rights_response import PreviewAsset as PreviewAsset
from .._schemas.brand.search_brands_response import Logo as Logo
from .._schemas.brand.update_rights_response import UpdateRightsResponse1 as UpdateRightsResponse1
from .._schemas.brand.update_rights_response import UpdateRightsResponse2 as UpdateRightsResponse2
from .._schemas.brand.verify_brand_claim_response import VerifyBrandClaimErrorResponse as VerifyBrandClaimErrorResponse
from .._schemas.brand.verify_brand_claim_response import (
    VerifyBrandClaimSignedSuccessPayload as VerifyBrandClaimSignedSuccessPayload,
)
from .._schemas.brand.verify_brand_claim_response import (
    VerifyBrandClaimSuccessResponse as VerifyBrandClaimSuccessResponse,
)
from .._schemas.brand.verify_brand_claims_response import ResultEntry1 as ResultEntry1
from .._schemas.brand.verify_brand_claims_response import ResultEntry2 as ResultEntry2
from .._schemas.brand.verify_brand_claims_response import (
    VerifyBrandClaimsErrorResponse as VerifyBrandClaimsErrorResponse,
)
from .._schemas.brand.verify_brand_claims_response import (
    VerifyBrandClaimsSignedSuccessPayload as VerifyBrandClaimsSignedSuccessPayload,
)
from .._schemas.collection.base_collection_source import BaseCollectionSource1 as BaseCollectionSource1
from .._schemas.collection.base_collection_source import BaseCollectionSource2 as BaseCollectionSource2
from .._schemas.collection.base_collection_source import BaseCollectionSource3 as BaseCollectionSource3
from .._schemas.collection.get_collection_list_request import Pagination as Pagination
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse1 as ComplyTestControllerResponse1,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse2 as ComplyTestControllerResponse2,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse4 as ComplyTestControllerResponse4,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse5 as ComplyTestControllerResponse5,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse6 as ComplyTestControllerResponse6,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse7 as ComplyTestControllerResponse7,
)
from .._schemas.compliance.comply_test_controller_response import (
    ComplyTestControllerResponse8 as ComplyTestControllerResponse8,
)
from .._schemas.compliance.comply_test_controller_response import IdentifierMatchProof as IdentifierMatchProof
from .._schemas.content_standards.artifact import AssetAccess1 as AssetAccess1
from .._schemas.content_standards.artifact import AssetAccess2 as AssetAccess2
from .._schemas.content_standards.artifact import AssetAccess3 as AssetAccess3
from .._schemas.content_standards.artifact import Assets1 as Assets1
from .._schemas.content_standards.artifact import Assets2 as Assets2
from .._schemas.content_standards.artifact import Assets3 as Assets3
from .._schemas.content_standards.artifact import Assets4 as Assets4
from .._schemas.content_standards.artifact import TranscriptFormat as TranscriptFormat
from .._schemas.content_standards.artifact import TranscriptSource as TranscriptSource
from .._schemas.content_standards.artifact import TranscriptSource1 as TranscriptSource1
from .._schemas.content_standards.calibrate_content_response import (
    CalibrateContentResponse1 as CalibrateContentResponse1,
)
from .._schemas.content_standards.calibrate_content_response import (
    CalibrateContentResponse2 as CalibrateContentResponse2,
)
from .._schemas.content_standards.create_content_standards_response import (
    CreateContentStandardsResponse1 as CreateContentStandardsResponse1,
)
from .._schemas.content_standards.create_content_standards_response import (
    CreateContentStandardsResponse2 as CreateContentStandardsResponse2,
)
from .._schemas.content_standards.get_content_standards_response import (
    GetContentStandardsResponse1 as GetContentStandardsResponse1,
)
from .._schemas.content_standards.get_content_standards_response import (
    GetContentStandardsResponse2 as GetContentStandardsResponse2,
)
from .._schemas.content_standards.get_media_buy_artifacts_response import BrandContext as BrandContext
from .._schemas.content_standards.get_media_buy_artifacts_response import (
    GetMediaBuyArtifactsResponse1 as GetMediaBuyArtifactsResponse1,
)
from .._schemas.content_standards.get_media_buy_artifacts_response import (
    GetMediaBuyArtifactsResponse2 as GetMediaBuyArtifactsResponse2,
)
from .._schemas.content_standards.list_content_standards_response import (
    ListContentStandardsResponse1 as ListContentStandardsResponse1,
)
from .._schemas.content_standards.list_content_standards_response import (
    ListContentStandardsResponse2 as ListContentStandardsResponse2,
)
from .._schemas.content_standards.update_content_standards_response import (
    UpdateContentStandardsResponse1 as UpdateContentStandardsResponse1,
)
from .._schemas.content_standards.update_content_standards_response import (
    UpdateContentStandardsResponse2 as UpdateContentStandardsResponse2,
)
from .._schemas.content_standards.validate_content_delivery_request import Record as Record
from .._schemas.content_standards.validate_content_delivery_response import (
    ValidateContentDeliveryResponse1 as ValidateContentDeliveryResponse1,
)
from .._schemas.content_standards.validate_content_delivery_response import (
    ValidateContentDeliveryResponse2 as ValidateContentDeliveryResponse2,
)
from .._schemas.core.acceptance_policy_profile_ids import AcceptancePolicyProfileIds as AcceptancePolicyProfileIds
from .._schemas.core.account import Setup as Setup
from .._schemas.core.account_identity_change import AccountIdentityChange1 as AccountIdentityChange1
from .._schemas.core.account_identity_change import AccountIdentityChange2 as AccountIdentityChange2
from .._schemas.core.account_identity_change_preview import (
    AccountIdentityChangePreview1 as AccountIdentityChangePreview1,
)
from .._schemas.core.account_identity_change_preview import (
    AccountIdentityChangePreview2 as AccountIdentityChangePreview2,
)
from .._schemas.core.account_identity_change_preview import (
    AccountIdentityChangePreview3 as AccountIdentityChangePreview3,
)
from .._schemas.core.account_identity_change_preview import Effect as Effect
from .._schemas.core.account_identity_change_preview import Effect1 as Effect1
from .._schemas.core.account_ref import AccountReference1 as AccountReference1
from .._schemas.core.account_ref import AccountReference2 as AccountReference2
from .._schemas.core.activation_key import ActivationKey1 as ActivationKey1
from .._schemas.core.activation_key import ActivationKey2 as ActivationKey2
from .._schemas.core.agent_reporting_destination import AgentReportingDestination1 as AgentReportingDestination1
from .._schemas.core.agent_reporting_destination import AgentReportingDestination2 as AgentReportingDestination2
from .._schemas.core.agent_reporting_destination import AgentReportingDestination3 as AgentReportingDestination3
from .._schemas.core.agent_webhook_challenge import DeliveryAuth as DeliveryAuth
from .._schemas.core.applicable_package_id import ApplicablePackageId as ApplicablePackageId
from .._schemas.core.asset_group_vocabulary import AdcpAssetGroupVocabularyRegistry as AdcpAssetGroupVocabularyRegistry
from .._schemas.core.assets.css_asset import CssAsset as CssAsset
from .._schemas.core.assets.daast_asset import DaastAsset as DaastAsset
from .._schemas.core.assets.daast_asset import DaastAsset3 as DaastAsset3
from .._schemas.core.assets.daast_asset import DaastAsset4 as DaastAsset4
from .._schemas.core.assets.daast_asset import Location13 as Location13
from .._schemas.core.assets.daast_tracker_asset import DaastTrackerAsset as DaastTrackerAsset
from .._schemas.core.assets.display_tag_asset import DisplayTagAsset4 as DisplayTagAsset4
from .._schemas.core.assets.display_tag_asset import DisplayTagAsset5 as DisplayTagAsset5
from .._schemas.core.assets.display_tag_asset import DisplayTagAsset6 as DisplayTagAsset6
from .._schemas.core.assets.html_asset import HtmlAsset as HtmlAsset
from .._schemas.core.assets.javascript_asset import JavascriptAsset as JavascriptAsset
from .._schemas.core.assets.url_asset import UrlAsset as UrlAsset
from .._schemas.core.assets.vast_asset import VastAsset as VastAsset
from .._schemas.core.assets.vast_asset import VastAsset3 as VastAsset3
from .._schemas.core.assets.vast_asset import VastAsset4 as VastAsset4
from .._schemas.core.assets.vast_tracker_asset import VastTrackerAsset as VastTrackerAsset
from .._schemas.core.async_response_data import AdcpAsyncResponseData as AdcpAsyncResponseData
from .._schemas.core.attestation_capabilities import AcceptedIssuer as AcceptedIssuer
from .._schemas.core.attestation_capabilities import Resolver as Resolver
from .._schemas.core.attestation_capabilities import SupportedDeliveryMethod as SupportedDeliveryMethod
from .._schemas.core.attestation_issuer import AttestationIssuer1 as AttestationIssuer1
from .._schemas.core.attestation_issuer import AttestationIssuer2 as AttestationIssuer2
from .._schemas.core.attestation_issuer import AttestationIssuer3 as AttestationIssuer3
from .._schemas.core.attestation_reference import Locator as Locator
from .._schemas.core.attestation_reference import Locator1 as Locator1
from .._schemas.core.attestation_subject import AttestationSubject1 as AttestationSubject1
from .._schemas.core.attestation_subject import AttestationSubject2 as AttestationSubject2
from .._schemas.core.attestation_subject import AttestationSubject3 as AttestationSubject3
from .._schemas.core.audience_activation_method import AudienceActivationMethod1 as AudienceActivationMethod1
from .._schemas.core.audience_activation_method import AudienceActivationMethod2 as AudienceActivationMethod2
from .._schemas.core.audience_activation_method import AudienceActivationMethod3 as AudienceActivationMethod3
from .._schemas.core.audience_activation_method import AudienceActivationMethod4 as AudienceActivationMethod4
from .._schemas.core.audience_activation_method import AudienceActivationMethod5 as AudienceActivationMethod5
from .._schemas.core.audience_activation_method import AudienceActivationMethod6 as AudienceActivationMethod6
from .._schemas.core.audience_activation_method import BuyerAgent as BuyerAgent
from .._schemas.core.audience_activation_method import ConsumerIdentity as ConsumerIdentity
from .._schemas.core.audience_activation_method import Direction as Direction
from .._schemas.core.audience_evidence import AttestationRef as AttestationRef
from .._schemas.core.audience_member import Uid as Uid
from .._schemas.core.audience_selector import AudienceSelector1 as AudienceSelector1
from .._schemas.core.audience_selector import AudienceSelector2 as AudienceSelector2
from .._schemas.core.audience_selector import AudienceSelector3 as AudienceSelector3
from .._schemas.core.audience_selector import AudienceSelector4 as AudienceSelector4
from .._schemas.core.audience_source import AudienceSource1 as AudienceSource1
from .._schemas.core.audience_source import AudienceSource2 as AudienceSource2
from .._schemas.core.bidding_policy import Strength1 as Strength1
from .._schemas.core.budget_allocation import BudgetAllocation1 as BudgetAllocation1
from .._schemas.core.budget_allocation import BudgetAllocation2 as BudgetAllocation2
from .._schemas.core.business_entity import Contact as Contact
from .._schemas.core.canonical_account_ref import CanonicalAccountReference1 as CanonicalAccountReference1
from .._schemas.core.canonical_account_ref import CanonicalAccountReference2 as CanonicalAccountReference2
from .._schemas.core.canonical_budget_allocation import CanonicalBudgetAllocation1 as CanonicalBudgetAllocation1
from .._schemas.core.canonical_budget_allocation import CanonicalBudgetAllocation2 as CanonicalBudgetAllocation2
from .._schemas.core.canonical_media_buy_action import Action3 as Action3
from .._schemas.core.canonical_media_buy_action import Action4 as Action4
from .._schemas.core.canonical_media_buy_action import CanonicalMediaBuyAction1 as CanonicalMediaBuyAction1
from .._schemas.core.canonical_media_buy_action import CanonicalMediaBuyAction2 as CanonicalMediaBuyAction2
from .._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoal1 as CanonicalOptimizationGoal1
from .._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoal2 as CanonicalOptimizationGoal2
from .._schemas.core.canonical_optimization_goal import CanonicalOptimizationGoal3 as CanonicalOptimizationGoal3
from .._schemas.core.canonical_optimization_goal import Target10 as Target10
from .._schemas.core.canonical_placement import CanonicalProductPlacement1 as CanonicalProductPlacement1
from .._schemas.core.canonical_placement import CanonicalProductPlacement2 as CanonicalProductPlacement2
from .._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitment1 as CanonicalReportingCommitment1,
)
from .._schemas.core.canonical_reporting_commitment import (
    CanonicalReportingCommitment2 as CanonicalReportingCommitment2,
)
from .._schemas.core.collection import RelatedCollection as RelatedCollection
from .._schemas.core.collection_selection import CollectionSelection1 as CollectionSelection1
from .._schemas.core.collection_selection import CollectionSelection2 as CollectionSelection2
from .._schemas.core.committed_metric import CommittedMetric1 as CommittedMetric1
from .._schemas.core.committed_metric import CommittedMetric2 as CommittedMetric2
from .._schemas.core.creative_brief import RequiredDisclosure as RequiredDisclosure
from .._schemas.core.creative_item import CreativeItem1 as CreativeItem1
from .._schemas.core.creative_item import CreativeItem2 as CreativeItem2
from .._schemas.core.creative_localization import TargetVariant as TargetVariant
from .._schemas.core.creative_localization_readback import LocaleFallback as LocaleFallback
from .._schemas.core.creative_localization_readback import Variants1 as Variants1
from .._schemas.core.creative_localization_readback import Variants2 as Variants2
from .._schemas.core.creative_revision_id import CreativeRevisionId as CreativeRevisionId
from .._schemas.core.daast_tracker_constraints import DaastTrackerConstraints as DaastTrackerConstraints
from .._schemas.core.data_provider_signal_selector import DataProviderSignalSelector1 as DataProviderSignalSelector1
from .._schemas.core.data_provider_signal_selector import DataProviderSignalSelector2 as DataProviderSignalSelector2
from .._schemas.core.data_provider_signal_selector import DataProviderSignalSelector3 as DataProviderSignalSelector3
from .._schemas.core.deadline_policy import MaterialStage as MaterialStage
from .._schemas.core.delivery_metric_aggregate import DeliveryMetricAggregate2 as DeliveryMetricAggregate2
from .._schemas.core.delivery_metrics import Panel as Panel
from .._schemas.core.delivery_metrics import Posting as Posting
from .._schemas.core.delivery_metrics import ReachWindow as ReachWindow
from .._schemas.core.delivery_metrics import TimeBasedView as TimeBasedView
from .._schemas.core.demographic_reporting_capability import ReportingMode as ReportingMode
from .._schemas.core.demographic_targeting_capability import ExecutionMode as ExecutionMode
from .._schemas.core.demographic_targeting_resolution import Execution as Execution
from .._schemas.core.demographic_targeting_resolution import Execution1 as Execution1
from .._schemas.core.demographic_targeting_resolution import Execution2 as Execution2
from .._schemas.core.deployment import Deployment1 as Deployment1
from .._schemas.core.deployment import Deployment2 as Deployment2
from .._schemas.core.destination import Destination1 as Destination1
from .._schemas.core.destination import Destination2 as Destination2
from .._schemas.core.destination_item import Location as Location
from .._schemas.core.error import Issue as Issue
from .._schemas.core.evaluator_spec import EvaluatorSpec1 as EvaluatorSpec1
from .._schemas.core.evaluator_spec import EvaluatorSpec2 as EvaluatorSpec2
from .._schemas.core.evaluator_spec import EvaluatorSpec3 as EvaluatorSpec3
from .._schemas.core.event_custom_data import Content as Content
from .._schemas.core.experimental_feature_id import ExperimentalFeatureId as ExperimentalFeatureId
from .._schemas.core.format import Assets as Assets
from .._schemas.core.format import Assets9 as Assets9
from .._schemas.core.format import Assets10 as Assets10
from .._schemas.core.format import Assets11 as Assets11
from .._schemas.core.format import Assets12 as Assets12
from .._schemas.core.format import Assets13 as Assets13
from .._schemas.core.format import Assets14 as Assets14
from .._schemas.core.format import Assets15 as Assets15
from .._schemas.core.format import Assets16 as Assets16
from .._schemas.core.format import Assets17 as Assets17
from .._schemas.core.format import Assets18 as Assets18
from .._schemas.core.format import Assets19 as Assets19
from .._schemas.core.format import Assets20 as Assets20
from .._schemas.core.format import Assets21 as Assets21
from .._schemas.core.format import Assets22 as Assets22
from .._schemas.core.format import Assets23 as Assets23
from .._schemas.core.format import Assets24 as Assets24
from .._schemas.core.format import Assets25 as Assets25
from .._schemas.core.format import Assets26 as Assets26
from .._schemas.core.format import Assets27 as Assets27
from .._schemas.core.format import Assets28 as Assets28
from .._schemas.core.format import Assets29 as Assets29
from .._schemas.core.format import Assets31 as Assets31
from .._schemas.core.format import Assets32 as Assets32
from .._schemas.core.format import Assets33 as Assets33
from .._schemas.core.format import Assets34 as Assets34
from .._schemas.core.format import Assets35 as Assets35
from .._schemas.core.format import Assets36 as Assets36
from .._schemas.core.format import Assets37 as Assets37
from .._schemas.core.format import Assets38 as Assets38
from .._schemas.core.format import Assets39 as Assets39
from .._schemas.core.format import Assets40 as Assets40
from .._schemas.core.format import Assets41 as Assets41
from .._schemas.core.format import Assets42 as Assets42
from .._schemas.core.format import Assets43 as Assets43
from .._schemas.core.format import Assets44 as Assets44
from .._schemas.core.format import Assets45 as Assets45
from .._schemas.core.format import Assets46 as Assets46
from .._schemas.core.format import Assets47 as Assets47
from .._schemas.core.format import Assets48 as Assets48
from .._schemas.core.format import Assets49 as Assets49
from .._schemas.core.format import Assets50 as Assets50
from .._schemas.core.format import Assets51 as Assets51
from .._schemas.core.format import Assets94 as Assets94
from .._schemas.core.format import DisclosureCapability as DisclosureCapability
from .._schemas.core.format import Renders as Renders
from .._schemas.core.format import Renders1 as Renders1
from .._schemas.core.format import UnknownFormatAsset as UnknownFormatAsset
from .._schemas.core.format import UnknownGroupAsset as UnknownGroupAsset
from .._schemas.core.format_option_ref import FormatOptionReference1 as FormatOptionReference1
from .._schemas.core.format_shape_vocabulary import (
    AdcpFormatShapeVocabularyRegistry as AdcpFormatShapeVocabularyRegistry,
)
from .._schemas.core.geo_region_support import Countries3 as Countries3
from .._schemas.core.https_url import HttpsUrl as HttpsUrl
from .._schemas.core.iana_timezone import IanaTimezoneIdentifier as IanaTimezoneIdentifier
from .._schemas.core.inventory_list_application import InventoryListApplication1 as InventoryListApplication1
from .._schemas.core.inventory_list_application import InventoryListApplication2 as InventoryListApplication2
from .._schemas.core.macro_bearing_url import MacroBearingUrl as MacroBearingUrl
from .._schemas.core.mcp_webhook_payload import McpWebhookPayload as McpWebhookPayload
from .._schemas.core.media_buy import Cancellation as Cancellation
from .._schemas.core.media_buy_available_action_id import MediaBuyAvailableActionId as MediaBuyAvailableActionId
from .._schemas.core.media_buy_change_term_id import MediaBuyChangeTermId as MediaBuyChangeTermId
from .._schemas.core.missing_metric import MissingMetric1 as MissingMetric1
from .._schemas.core.missing_metric import MissingMetric2 as MissingMetric2
from .._schemas.core.optimization_goal import OptimizationGoal8 as OptimizationGoal8
from .._schemas.core.optimization_goal import OptimizationGoal9 as OptimizationGoal9
from .._schemas.core.optimization_goal import OptimizationGoal10 as OptimizationGoal10
from .._schemas.core.optimization_goal import Target16 as Target16
from .._schemas.core.optimization_goal import Target17 as Target17
from .._schemas.core.performance_feedback_metric import PerformanceFeedbackMetric1 as PerformanceFeedbackMetric1
from .._schemas.core.performance_feedback_metric import PerformanceFeedbackMetric2 as PerformanceFeedbackMetric2
from .._schemas.core.placement_definition import FormatOptions as FormatOptions
from .._schemas.core.placement_identity import PlacementIdentity1 as PlacementIdentity1
from .._schemas.core.placement_identity import PlacementIdentity2 as PlacementIdentity2
from .._schemas.core.placement_selection import PlacementSelection1 as PlacementSelection1
from .._schemas.core.placement_selection import PlacementSelection2 as PlacementSelection2
from .._schemas.core.postal_area import PostalArea2 as PostalArea2
from .._schemas.core.postal_area import PostalArea112 as PostalArea112
from .._schemas.core.postal_area import PostalArea113 as PostalArea113
from .._schemas.core.postal_area import PostalArea114 as PostalArea114
from .._schemas.core.postal_area import PostalArea115 as PostalArea115
from .._schemas.core.postal_area import PostalArea116 as PostalArea116
from .._schemas.core.postal_area import PostalArea117 as PostalArea117
from .._schemas.core.postal_area import PostalArea118 as PostalArea118
from .._schemas.core.postal_area import PostalArea119 as PostalArea119
from .._schemas.core.postal_area import PostalArea120 as PostalArea120
from .._schemas.core.postal_area_support import (
    PostalAreaSupportAdditionalPropertyEnum as PostalAreaSupportAdditionalPropertyEnum,
)
from .._schemas.core.postal_country_system import PostalCountrySystem1 as PostalCountrySystem1
from .._schemas.core.postal_country_system import PostalCountrySystem2 as PostalCountrySystem2
from .._schemas.core.postal_country_system import PostalCountrySystem3 as PostalCountrySystem3
from .._schemas.core.principal_declarations_state import Exclusion as Exclusion
from .._schemas.core.principal_state import RetiredDestination as RetiredDestination
from .._schemas.core.product import Specification as Specification
from .._schemas.core.product import SupportedTarget5 as SupportedTarget5
from .._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuers1 as AcceptedAttestationIssuers1,
)
from .._schemas.core.product_audience_evidence_requirements import (
    AcceptedAttestationIssuers2 as AcceptedAttestationIssuers2,
)
from .._schemas.core.product_change_map import ProductChangeMap1 as ProductChangeMap1
from .._schemas.core.product_execution_requirement import ProductExecutionRequirement1 as ProductExecutionRequirement1
from .._schemas.core.product_execution_requirement import ProductExecutionRequirement2 as ProductExecutionRequirement2
from .._schemas.core.product_execution_requirement import ProductExecutionRequirement3 as ProductExecutionRequirement3
from .._schemas.core.product_filters import AudienceActivationMethods1 as AudienceActivationMethods1
from .._schemas.core.product_filters import AudienceActivationMethods2 as AudienceActivationMethods2
from .._schemas.core.product_filters import AudienceActivationMethods3 as AudienceActivationMethods3
from .._schemas.core.product_filters import AudienceActivationMethods4 as AudienceActivationMethods4
from .._schemas.core.product_filters import AudienceActivationMethods5 as AudienceActivationMethods5
from .._schemas.core.product_filters import Keyword as Keyword
from .._schemas.core.product_filters import TrustedMatch as TrustedMatch
from .._schemas.core.product_format_declaration import ProductFormatDeclaration1 as ProductFormatDeclaration1
from .._schemas.core.product_format_declaration import ProductFormatDeclaration2 as ProductFormatDeclaration2
from .._schemas.core.product_format_declaration import ProductFormatDeclaration3 as ProductFormatDeclaration3
from .._schemas.core.product_format_declaration import ProductFormatDeclaration4 as ProductFormatDeclaration4
from .._schemas.core.product_format_declaration import ProductFormatDeclaration5 as ProductFormatDeclaration5
from .._schemas.core.product_format_declaration import ProductFormatDeclaration6 as ProductFormatDeclaration6
from .._schemas.core.product_format_declaration import ProductFormatDeclaration7 as ProductFormatDeclaration7
from .._schemas.core.product_format_declaration import ProductFormatDeclaration8 as ProductFormatDeclaration8
from .._schemas.core.product_format_declaration import ProductFormatDeclaration9 as ProductFormatDeclaration9
from .._schemas.core.product_format_declaration import ProductFormatDeclaration10 as ProductFormatDeclaration10
from .._schemas.core.product_format_declaration import ProductFormatDeclaration11 as ProductFormatDeclaration11
from .._schemas.core.product_format_declaration import ProductFormatDeclaration12 as ProductFormatDeclaration12
from .._schemas.core.product_format_declaration import ProductFormatDeclaration13 as ProductFormatDeclaration13
from .._schemas.core.product_format_declaration import ProductFormatDeclaration14 as ProductFormatDeclaration14
from .._schemas.core.product_format_declaration import ProductFormatDeclaration15 as ProductFormatDeclaration15
from .._schemas.core.product_format_declaration import ProductFormatDeclaration16 as ProductFormatDeclaration16
from .._schemas.core.product_offer_filters import RequiredPerformanceStandard as RequiredPerformanceStandard
from .._schemas.core.product_signal_targeting_option import AllowedTargetingMode as AllowedTargetingMode
from .._schemas.core.property_id import PropertyId as PropertyId
from .._schemas.core.provenance import Watermark as Watermark
from .._schemas.core.publisher_property_selector import PublisherPropertySelector1 as PublisherPropertySelector1
from .._schemas.core.publisher_property_selector import PublisherPropertySelector2 as PublisherPropertySelector2
from .._schemas.core.publisher_property_selector import PublisherPropertySelector3 as PublisherPropertySelector3
from .._schemas.core.registry_event import Payload1 as Payload1
from .._schemas.core.registry_event import Payload2 as Payload2
from .._schemas.core.registry_event import Payload5 as Payload5
from .._schemas.core.registry_event import Payload6 as Payload6
from .._schemas.core.registry_event import Payload8 as Payload8
from .._schemas.core.registry_event import Payload9 as Payload9
from .._schemas.core.registry_event import Storyboard as Storyboard
from .._schemas.core.registry_event import Tracks as Tracks
from .._schemas.core.reporting_adjustment import AccountingPeriod as AccountingPeriod
from .._schemas.core.reporting_consumer_status import Period as Period
from .._schemas.core.reporting_control_total import ReportingControlTotal1 as ReportingControlTotal1
from .._schemas.core.reporting_control_total import ReportingControlTotal2 as ReportingControlTotal2
from .._schemas.core.reporting_coverage import Limitation as Limitation
from .._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestination1 as ReportingDatasetShareDestination1,
)
from .._schemas.core.reporting_dataset_share_destination import (
    ReportingDatasetShareDestination2 as ReportingDatasetShareDestination2,
)
from .._schemas.core.reporting_delivery_method import ReportingDeliveryMethod1 as ReportingDeliveryMethod1
from .._schemas.core.reporting_delivery_method import ReportingDeliveryMethod2 as ReportingDeliveryMethod2
from .._schemas.core.reporting_delivery_method import ReportingDeliveryMethod3 as ReportingDeliveryMethod3
from .._schemas.core.reporting_delivery_offering import DestinationMode as DestinationMode
from .._schemas.core.reporting_delivery_offering_id import ReportingDeliveryOfferingId as ReportingDeliveryOfferingId
from .._schemas.core.reporting_report_definition import FinalityPolicies as FinalityPolicies
from .._schemas.core.reporting_report_definition import FinalityPolicies1 as FinalityPolicies1
from .._schemas.core.reporting_report_definition import FinalityPolicies2 as FinalityPolicies2
from .._schemas.core.reporting_verification import PhysicalChecksums as PhysicalChecksums
from .._schemas.core.reporting_verification import PhysicalChecksums1 as PhysicalChecksums1
from .._schemas.core.reporting_write_destination import ReportingWriteDestination1 as ReportingWriteDestination1
from .._schemas.core.reporting_write_destination import ReportingWriteDestination2 as ReportingWriteDestination2
from .._schemas.core.requirements.catalog_field_binding import CatalogFieldBinding1 as CatalogFieldBinding1
from .._schemas.core.requirements.css_asset_requirements import CssAssetRequirements as CssAssetRequirements
from .._schemas.core.requirements.daast_asset_requirements import DaastAssetRequirements as DaastAssetRequirements
from .._schemas.core.requirements.html_asset_requirements import HtmlAssetRequirements as HtmlAssetRequirements
from .._schemas.core.requirements.image_asset_requirements import Bleed as Bleed
from .._schemas.core.requirements.image_asset_requirements import Bleed1 as Bleed1
from .._schemas.core.requirements.javascript_asset_requirements import (
    JavascriptAssetRequirements as JavascriptAssetRequirements,
)
from .._schemas.core.requirements.url_asset_requirements import UrlAssetRequirements as UrlAssetRequirements
from .._schemas.core.requirements.vast_asset_requirements import VastAssetRequirements as VastAssetRequirements
from .._schemas.core.response_payload_jws_envelope import ResponsePayloadJwsEnvelope as ResponsePayloadJwsEnvelope
from .._schemas.core.signal_coverage_forecast import Point as Point
from .._schemas.core.signal_definition import Channel as Channel
from .._schemas.core.signal_definition import DataSource as DataSource
from .._schemas.core.signal_definition import IdType as IdType
from .._schemas.core.signal_definition import MatchKey as MatchKey
from .._schemas.core.signal_definition import SeedSource as SeedSource
from .._schemas.core.signal_definition import Value as Value
from .._schemas.core.signal_definition import ValueMapping as ValueMapping
from .._schemas.core.signal_id import SignalId as SignalId
from .._schemas.core.signal_id import SignalId8 as SignalId8
from .._schemas.core.signal_id import SignalId9 as SignalId9
from .._schemas.core.signal_pricing import VendorPricing1 as VendorPricing1
from .._schemas.core.signal_pricing import VendorPricing2 as VendorPricing2
from .._schemas.core.signal_pricing import VendorPricing3 as VendorPricing3
from .._schemas.core.signal_pricing import VendorPricing4 as VendorPricing4
from .._schemas.core.signal_pricing import VendorPricing5 as VendorPricing5
from .._schemas.core.signal_ref import SignalRef1 as SignalRef1
from .._schemas.core.signal_ref import SignalRef2 as SignalRef2
from .._schemas.core.signal_ref import SignalRef3 as SignalRef3
from .._schemas.core.signal_targeting import SignalTargeting1 as SignalTargeting1
from .._schemas.core.signal_targeting import SignalTargeting2 as SignalTargeting2
from .._schemas.core.signal_targeting import SignalTargeting3 as SignalTargeting3
from .._schemas.core.signal_targeting_expression import SignalTargetingExpression1 as SignalTargetingExpression1
from .._schemas.core.signal_targeting_expression import SignalTargetingExpression2 as SignalTargetingExpression2
from .._schemas.core.signal_targeting_expression import SignalTargetingExpression3 as SignalTargetingExpression3
from .._schemas.core.sla_window import SlaWindow as SlaWindow
from .._schemas.core.targeting import Geometry as Geometry
from .._schemas.core.targeting import StoreCatchment as StoreCatchment
from .._schemas.core.targeting_modification import TargetingModification1 as TargetingModification1
from .._schemas.core.targeting_modification import TargetingModification2 as TargetingModification2
from .._schemas.core.targeting_overlay_requirements import BrowserRequirement1 as BrowserRequirement1
from .._schemas.core.targeting_overlay_requirements import DaypartRequirement1 as DaypartRequirement1
from .._schemas.core.targeting_overlay_requirements import KeywordRequirement1 as KeywordRequirement1
from .._schemas.core.targeting_overlay_requirements import MetroRequirement1 as MetroRequirement1
from .._schemas.core.targeting_overlay_support import BrowserSupport1 as BrowserSupport1
from .._schemas.core.targeting_overlay_support import CountrySupport1 as CountrySupport1
from .._schemas.core.targeting_overlay_support import DaypartSupport1 as DaypartSupport1
from .._schemas.core.targeting_overlay_support import KeywordSupport1 as KeywordSupport1
from .._schemas.core.targeting_overlay_support import MetroSupport1 as MetroSupport1
from .._schemas.core.tasks_get_response import HistoryItem as HistoryItem
from .._schemas.core.tasks_list_response import DomainBreakdown as DomainBreakdown
from .._schemas.core.tasks_list_response import Task as Task
from .._schemas.core.tracker_execution_selector import TrackerExecutionSelector1 as TrackerExecutionSelector1
from .._schemas.core.transformer_param import Option as Option
from .._schemas.core.truncation_sentinel import FieldTruncation as FieldTruncation
from .._schemas.core.vast_media_file_requirements import VastMediafileRequirements as VastMediafileRequirements
from .._schemas.core.vast_tracker_constraints import VastTrackerConstraints as VastTrackerConstraints
from .._schemas.core.vendor_metric_id import VendorMetricId as VendorMetricId
from .._schemas.core.verification_token_claims import (
    AgenticadvertisingOrgVerificationTokenClaims as AgenticadvertisingOrgVerificationTokenClaims,
)
from .._schemas.core.verification_token_claims import VerificationTokenMode as VerificationTokenMode
from .._schemas.core.version_envelope import AdcpVersionEnvelope as AdcpVersionEnvelope
from .._schemas.core.wholesale_feed_event import AppliesTo1 as AppliesTo1
from .._schemas.core.wholesale_feed_event import AppliesTo2 as AppliesTo2
from .._schemas.core.wholesale_feed_event import Payload as Payload
from .._schemas.core.wholesale_feed_event import Payload17 as Payload17
from .._schemas.core.wholesale_feed_event import Payload18 as Payload18
from .._schemas.core.wholesale_feed_event import Payload20 as Payload20
from .._schemas.core.wholesale_feed_event import Payload21 as Payload21
from .._schemas.core.wholesale_feed_event import Payload22 as Payload22
from .._schemas.core.wholesale_feed_event import Payload23 as Payload23
from .._schemas.core.wholesale_feed_event import Payload24 as Payload24
from .._schemas.creative.asset_types.index import AdcpAssetTypeRegistry as AdcpAssetTypeRegistry
from .._schemas.creative.get_creative_features_response import (
    GetCreativeFeaturesResponse1 as GetCreativeFeaturesResponse1,
)
from .._schemas.creative.get_creative_features_response import (
    GetCreativeFeaturesResponse2 as GetCreativeFeaturesResponse2,
)
from .._schemas.creative.get_creative_features_response import (
    GetCreativeFeaturesResponse3 as GetCreativeFeaturesResponse3,
)
from .._schemas.creative.list_creative_formats_response import CreativeAgent as CreativeAgent
from .._schemas.creative.list_creatives_response import AssignedPackage as AssignedPackage
from .._schemas.creative.list_creatives_response import Creatives as Creatives
from .._schemas.creative.list_creatives_response import Creatives1 as Creatives1
from .._schemas.creative.preview_creative_request import Request as Request
from .._schemas.creative.preview_creative_response import Preview3 as Preview3
from .._schemas.creative.preview_creative_response import PreviewCreativeResponse1 as PreviewCreativeResponse1
from .._schemas.creative.preview_creative_response import PreviewCreativeResponse2 as PreviewCreativeResponse2
from .._schemas.creative.preview_creative_response import PreviewCreativeResponse3 as PreviewCreativeResponse3
from .._schemas.creative.preview_creative_response import PreviewCreativeResponse4 as PreviewCreativeResponse4
from .._schemas.creative.preview_render import Dimensions as Dimensions
from .._schemas.creative.preview_render import PreviewRender1 as PreviewRender1
from .._schemas.creative.preview_render import PreviewRender2 as PreviewRender2
from .._schemas.creative.preview_render import PreviewRender3 as PreviewRender3
from .._schemas.creative.sync_creatives_request import Assignment as Assignment
from .._schemas.creative.sync_creatives_request import AssignmentOperations1 as AssignmentOperations1
from .._schemas.creative.sync_creatives_request import AssignmentOperations2 as AssignmentOperations2
from .._schemas.creative.sync_creatives_request import AssignmentOperations3 as AssignmentOperations3
from .._schemas.creative.sync_creatives_response import SyncCreativesResponse1 as SyncCreativesResponse1
from .._schemas.creative.sync_creatives_response import SyncCreativesResponse2 as SyncCreativesResponse2
from .._schemas.creative.sync_creatives_response import SyncCreativesResponse3 as SyncCreativesResponse3
from .._schemas.creative.validate_input_request import Targets1 as Targets1
from .._schemas.creative.validate_input_request import Targets2 as Targets2
from .._schemas.creative.validate_input_request import Targets3 as Targets3
from .._schemas.creative.validate_input_request import Targets4 as Targets4
from .._schemas.creative.video_brief import Segment as Segment
from .._schemas.enums.adcp_protocol import AdcpProtocol as AdcpProtocol
from .._schemas.enums.c2pa_watermark_action import C2PaWatermarkAction as C2PaWatermarkAction
from .._schemas.enums.content_id_type import ContentIdType as ContentIdType
from .._schemas.enums.ctv_ad_experience import CtvAdExperience as CtvAdExperience
from .._schemas.enums.daast_tracking_event import DaastTrackingEvent as DaastTrackingEvent
from .._schemas.enums.daast_version import DaastVersion as DaastVersion
from .._schemas.enums.dooh_motion_type import DoohMotionType as DoohMotionType
from .._schemas.enums.format_id_parameter import FormatIdParameter as FormatIdParameter
from .._schemas.enums.gop_type import GopType as GopType
from .._schemas.enums.http_method import HttpMethod as HttpMethod
from .._schemas.enums.javascript_module_type import JavascriptModuleType as JavascriptModuleType
from .._schemas.enums.match_id_type import MatchIdType as MatchIdType
from .._schemas.enums.response_type import TmpResponseType as TmpResponseType
from .._schemas.enums.si_session_status import SiSessionStatus as SiSessionStatus
from .._schemas.enums.signal_catalog_type import SignalCatalogType as SignalCatalogType
from .._schemas.enums.specialism import AdcpSpecialism as AdcpSpecialism
from .._schemas.enums.uid_type import UidType as UidType
from .._schemas.enums.url_asset_type import UrlAssetType as UrlAssetType
from .._schemas.enums.vast_media_delivery_method import VastMediaDeliveryMethod as VastMediaDeliveryMethod
from .._schemas.enums.vast_tracking_event import VastTrackingEvent as VastTrackingEvent
from .._schemas.enums.vast_version import VastVersion as VastVersion
from .._schemas.enums.wcag_level import WcagLevel as WcagLevel
from .._schemas.error_details.execution_requirement_unmet import UnmetRequirement as UnmetRequirement
from .._schemas.error_details.governance_agent_not_accepted import (
    GovernanceAgentNotAcceptedDetails1 as GovernanceAgentNotAcceptedDetails1,
)
from .._schemas.error_details.governance_agent_not_accepted import (
    GovernanceAgentNotAcceptedDetails2 as GovernanceAgentNotAcceptedDetails2,
)
from .._schemas.error_details.vast_version_mismatch import VastVersionMismatchDetails as VastVersionMismatchDetails
from .._schemas.error_details.vast_version_mismatch import VastVersionMismatchDetails3 as VastVersionMismatchDetails3
from .._schemas.error_details.vendor_error_codes import Codes as Codes
from .._schemas.error_details.vendor_error_codes import Vendors as Vendors
from .._schemas.extensions.extension_meta import AdcpExtensionFileSchema as AdcpExtensionFileSchema
from .._schemas.extensions.index import AdcpExtensionRegistry as AdcpExtensionRegistry
from .._schemas.formats.canonical._base import Slot as Slot
from .._schemas.formats.canonical.agent_placement import (
    CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement as CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement,
)
from .._schemas.formats.canonical.audio_daast import CanonicalFormatDaastAudio as CanonicalFormatDaastAudio
from .._schemas.formats.canonical.audio_hosted import AudioChannel as AudioChannel
from .._schemas.formats.canonical.audio_vast import CanonicalFormatVastAudio as CanonicalFormatVastAudio
from .._schemas.formats.canonical.coordinated_placements import Components as Components
from .._schemas.formats.canonical.coordinated_placements import Components1 as Components1
from .._schemas.formats.canonical.coordinated_placements import Components2 as Components2
from .._schemas.formats.canonical.coordinated_placements import Components3 as Components3
from .._schemas.formats.canonical.coordinated_placements import Components4 as Components4
from .._schemas.formats.canonical.coordinated_placements import Components5 as Components5
from .._schemas.formats.canonical.coordinated_placements import Components6 as Components6
from .._schemas.formats.canonical.coordinated_placements import Components7 as Components7
from .._schemas.formats.canonical.coordinated_placements import Components8 as Components8
from .._schemas.formats.canonical.coordinated_placements import Components9 as Components9
from .._schemas.formats.canonical.coordinated_placements import Components10 as Components10
from .._schemas.formats.canonical.coordinated_placements import Components11 as Components11
from .._schemas.formats.canonical.coordinated_placements import Components12 as Components12
from .._schemas.formats.canonical.coordinated_placements import Components13 as Components13
from .._schemas.formats.canonical.coordinated_placements import SharedSlot as SharedSlot
from .._schemas.formats.canonical.display_tag import SupportedDeliveryType as SupportedDeliveryType
from .._schemas.formats.canonical.display_tag import SupportedTagType as SupportedTagType
from .._schemas.formats.canonical.html5 import CanonicalFormatHtml5Banner as CanonicalFormatHtml5Banner
from .._schemas.formats.canonical.image_carousel import AllowedCardMediaAssetType as AllowedCardMediaAssetType
from .._schemas.formats.canonical.seller_rendered_stateful_display import Breakpoint as Breakpoint
from .._schemas.formats.canonical.seller_rendered_stateful_display import State as State
from .._schemas.formats.canonical.seller_rendered_stateful_display import TransitionMode9 as TransitionMode9
from .._schemas.formats.canonical.sponsored_placement import SupportedIdType as SupportedIdType
from .._schemas.formats.canonical.video_vast import CanonicalFormatVastVideo as CanonicalFormatVastVideo
from .._schemas.governance.accepted_governance_agents import AnyOf1 as AnyOf1
from .._schemas.governance.accepted_governance_agents import AnyOf2 as AnyOf2
from .._schemas.governance.attribute_definition import RegulatoryBasi as RegulatoryBasi
from .._schemas.governance.check_governance_response import Condition as Condition
from .._schemas.governance.check_governance_response import RuntimeAttestationEvaluation as RuntimeAttestationEvaluation
from .._schemas.governance.get_plan_audit_logs_response import ChannelAllocation as ChannelAllocation
from .._schemas.governance.get_plan_audit_logs_response import Entry as Entry
from .._schemas.governance.get_plan_audit_logs_response import Escalation as Escalation
from .._schemas.governance.get_plan_audit_logs_response import GovernedAction as GovernedAction
from .._schemas.governance.get_plan_audit_logs_response import RuntimeAttestation as RuntimeAttestation
from .._schemas.governance.policy_category_definition import Facet as Facet
from .._schemas.governance.policy_category_definition import RegulatoryFramework as RegulatoryFramework
from .._schemas.governance.sync_plans_request import Allocations as Allocations
from .._schemas.governance.sync_plans_request import Budget2 as Budget2
from .._schemas.governance.sync_plans_request import Delegation as Delegation
from .._schemas.governance.sync_plans_request import MixTargets as MixTargets
from .._schemas.governance.sync_plans_response import ResolvedPolicy as ResolvedPolicy
from .._schemas.governance.sync_plans_response import Status51 as Status51
from .._schemas.media_buy.acceptance_context import Subject as Subject
from .._schemas.media_buy.acceptance_policy_profile import PolicyRef as PolicyRef
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement1 as AcceptancePolicyRequirement1,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement2 as AcceptancePolicyRequirement2,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement3 as AcceptancePolicyRequirement3,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement4 as AcceptancePolicyRequirement4,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement5 as AcceptancePolicyRequirement5,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement6 as AcceptancePolicyRequirement6,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement7 as AcceptancePolicyRequirement7,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement8 as AcceptancePolicyRequirement8,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement9 as AcceptancePolicyRequirement9,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement10 as AcceptancePolicyRequirement10,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement11 as AcceptancePolicyRequirement11,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement12 as AcceptancePolicyRequirement12,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement13 as AcceptancePolicyRequirement13,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement14 as AcceptancePolicyRequirement14,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement15 as AcceptancePolicyRequirement15,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement16 as AcceptancePolicyRequirement16,
)
from .._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement17 as AcceptancePolicyRequirement17,
)
from .._schemas.media_buy.acceptance_policy_rule import AppliesToEnum as AppliesToEnum
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse1 as BuildCreativeResponse1
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse2 as BuildCreativeResponse2
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse3 as BuildCreativeResponse3
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse4 as BuildCreativeResponse4
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse5 as BuildCreativeResponse5
from .._schemas.media_buy.build_creative_response import BuildCreativeResponse6 as BuildCreativeResponse6
from .._schemas.media_buy.build_creative_response import PerLeaf as PerLeaf
from .._schemas.media_buy.build_creative_response import Preview2 as Preview2
from .._schemas.media_buy.build_creative_response import Preview4 as Preview4
from .._schemas.media_buy.build_creative_response import Variant as Variant
from .._schemas.media_buy.change_term import AllowedStatus as AllowedStatus
from .._schemas.media_buy.change_term_constraints import (
    MediaBuyChangeTermConstraints1 as MediaBuyChangeTermConstraints1,
)
from .._schemas.media_buy.change_term_constraints import (
    MediaBuyChangeTermConstraints2 as MediaBuyChangeTermConstraints2,
)
from .._schemas.media_buy.change_term_constraints import (
    MediaBuyChangeTermConstraints3 as MediaBuyChangeTermConstraints3,
)
from .._schemas.media_buy.change_term_constraints import (
    MediaBuyChangeTermConstraints4 as MediaBuyChangeTermConstraints4,
)
from .._schemas.media_buy.commercial_terms import ReportingCommitment as ReportingCommitment
from .._schemas.media_buy.control_media_buy_response import ControlMediaBuyResponse1 as ControlMediaBuyResponse1
from .._schemas.media_buy.control_media_buy_response import ControlMediaBuyResponse2 as ControlMediaBuyResponse2
from .._schemas.media_buy.control_media_buy_response import ControlMediaBuyResponse3 as ControlMediaBuyResponse3
from .._schemas.media_buy.create_media_buy_response import CreateMediaBuyResponse1 as CreateMediaBuyResponse1
from .._schemas.media_buy.create_media_buy_response import CreateMediaBuyResponse2 as CreateMediaBuyResponse2
from .._schemas.media_buy.create_media_buy_response import CreateMediaBuyResponse3 as CreateMediaBuyResponse3
from .._schemas.media_buy.decline_proposals_response import DeclineProposalsResponse1 as DeclineProposalsResponse1
from .._schemas.media_buy.get_media_buy_delivery_response import ByPackageItem as ByPackageItem
from .._schemas.media_buy.get_media_buy_delivery_response import ByPackageItem1 as ByPackageItem1
from .._schemas.media_buy.get_media_buy_delivery_response import Totals as Totals
from .._schemas.media_buy.get_media_buy_delivery_response import Window as Window
from .._schemas.media_buy.get_media_buys_response import CreativeApproval as CreativeApproval
from .._schemas.media_buy.get_products_request import Action9 as Action9
from .._schemas.media_buy.get_products_request import Fields as Fields
from .._schemas.media_buy.get_products_request import Refine1 as Refine1
from .._schemas.media_buy.get_products_request import Refine2 as Refine2
from .._schemas.media_buy.get_products_request import Refine3 as Refine3
from .._schemas.media_buy.get_products_response import ExcludedBy as ExcludedBy
from .._schemas.media_buy.get_products_response import RefinementApplied1 as RefinementApplied1
from .._schemas.media_buy.get_products_response import RefinementApplied2 as RefinementApplied2
from .._schemas.media_buy.get_products_response import RefinementApplied3 as RefinementApplied3
from .._schemas.media_buy.get_reporting_status_response import DeliveryConfigGeneration as DeliveryConfigGeneration
from .._schemas.media_buy.log_event_response import LogEventResponse1 as LogEventResponse1
from .._schemas.media_buy.log_event_response import LogEventResponse2 as LogEventResponse2
from .._schemas.media_buy.log_event_response import PartialFailure as PartialFailure
from .._schemas.media_buy.media_buy_commitment_response import (
    MediaBuyCommitmentResponse1 as MediaBuyCommitmentResponse1,
)
from .._schemas.media_buy.media_buy_commitment_response import (
    MediaBuyCommitmentResponse2 as MediaBuyCommitmentResponse2,
)
from .._schemas.media_buy.media_buy_commitment_response import (
    MediaBuyCommitmentResponse3 as MediaBuyCommitmentResponse3,
)
from .._schemas.media_buy.media_buy_commitment_response import PurchaseBinding as PurchaseBinding
from .._schemas.media_buy.media_buy_delivery_webhook_result import ReportingPeriod as ReportingPeriod
from .._schemas.media_buy.outcome_target import Goal as Goal
from .._schemas.media_buy.outcome_target import Goal1 as Goal1
from .._schemas.media_buy.package_request import CommittedMetrics2 as CommittedMetrics2
from .._schemas.media_buy.product_fields import ProductResponseField as ProductResponseField
from .._schemas.media_buy.provide_performance_feedback_response import (
    ProvidePerformanceFeedbackResponse1 as ProvidePerformanceFeedbackResponse1,
)
from .._schemas.media_buy.provide_performance_feedback_response import (
    ProvidePerformanceFeedbackResponse2 as ProvidePerformanceFeedbackResponse2,
)
from .._schemas.media_buy.request_proposals_response import Loss as Loss
from .._schemas.media_buy.sync_audiences_request import Audience as Audience
from .._schemas.media_buy.sync_audiences_response import MatchBreakdown as MatchBreakdown
from .._schemas.media_buy.sync_audiences_response import SyncAudiencesResponse1 as SyncAudiencesResponse1
from .._schemas.media_buy.sync_audiences_response import SyncAudiencesResponse2 as SyncAudiencesResponse2
from .._schemas.media_buy.sync_audiences_response import SyncAudiencesResponse3 as SyncAudiencesResponse3
from .._schemas.media_buy.sync_catalogs_response import ItemIssue as ItemIssue
from .._schemas.media_buy.sync_catalogs_response import SyncCatalogsResponse1 as SyncCatalogsResponse1
from .._schemas.media_buy.sync_catalogs_response import SyncCatalogsResponse2 as SyncCatalogsResponse2
from .._schemas.media_buy.sync_catalogs_response import SyncCatalogsResponse3 as SyncCatalogsResponse3
from .._schemas.media_buy.sync_event_sources_response import SyncEventSourcesResponse1 as SyncEventSourcesResponse1
from .._schemas.media_buy.sync_event_sources_response import SyncEventSourcesResponse2 as SyncEventSourcesResponse2
from .._schemas.media_buy.sync_reporting_receipts_response import Results20 as Results20
from .._schemas.media_buy.sync_reporting_receipts_response import Results21 as Results21
from .._schemas.media_buy.sync_reporting_receipts_response import Results22 as Results22
from .._schemas.media_buy.sync_reporting_receipts_response import Results23 as Results23
from .._schemas.media_buy.sync_reporting_status_response import Results26 as Results26
from .._schemas.media_buy.sync_reporting_status_response import Results27 as Results27
from .._schemas.media_buy.update_media_buy_response import UpdateMediaBuyResponse1 as UpdateMediaBuyResponse1
from .._schemas.media_buy.update_media_buy_response import UpdateMediaBuyResponse2 as UpdateMediaBuyResponse2
from .._schemas.media_buy.update_media_buy_response import UpdateMediaBuyResponse3 as UpdateMediaBuyResponse3
from .._schemas.pricing_options.cpa_option import CpaPricingOption as CpaPricingOption
from .._schemas.pricing_options.cpc_option import CpcPricingOption as CpcPricingOption
from .._schemas.pricing_options.cpcv_option import CpcvPricingOption as CpcvPricingOption
from .._schemas.pricing_options.cpm_option import CpmPricingOption as CpmPricingOption
from .._schemas.pricing_options.cpp_option import CppPricingOption as CppPricingOption
from .._schemas.pricing_options.cpv_option import CpvPricingOption as CpvPricingOption
from .._schemas.pricing_options.cpv_option import ViewThreshold1 as ViewThreshold1
from .._schemas.pricing_options.price_breakdown import Adjustment as Adjustment
from .._schemas.pricing_options.vcpm_option import VcpmPricingOption as VcpmPricingOption
from .._schemas.property.base_property_source import BasePropertySource1 as BasePropertySource1
from .._schemas.property.base_property_source import BasePropertySource2 as BasePropertySource2
from .._schemas.property.base_property_source import BasePropertySource3 as BasePropertySource3
from .._schemas.protocol.get_adcp_capabilities_request import GetAdcpCapabilitiesRequest as GetAdcpCapabilitiesRequest
from .._schemas.protocol.get_adcp_capabilities_response import Accreditation as Accreditation
from .._schemas.protocol.get_adcp_capabilities_response import ChangeFeed as ChangeFeed
from .._schemas.protocol.get_adcp_capabilities_response import Features as Features
from .._schemas.protocol.get_adcp_capabilities_response import (
    GetAdcpCapabilitiesResponse as GetAdcpCapabilitiesResponse,
)
from .._schemas.protocol.get_adcp_capabilities_response import Idempotency as Idempotency
from .._schemas.protocol.get_adcp_capabilities_response import IdentityUpdates as IdentityUpdates
from .._schemas.protocol.get_adcp_capabilities_response import LifecycleTool as LifecycleTool
from .._schemas.protocol.get_adcp_capabilities_response import Notifications as Notifications
from .._schemas.protocol.get_adcp_capabilities_response import Notifications2 as Notifications2
from .._schemas.protocol.get_adcp_capabilities_response import Operation as Operation
from .._schemas.protocol.get_adcp_capabilities_response import PropagationSurface as PropagationSurface
from .._schemas.protocol.get_adcp_capabilities_response import (
    ReportingDestinationOffering as ReportingDestinationOffering,
)
from .._schemas.protocol.get_adcp_capabilities_response import SupportedChange as SupportedChange
from .._schemas.protocol.get_adcp_capabilities_response import SupportedDimension as SupportedDimension
from .._schemas.protocol.get_adcp_capabilities_response import SupportedFormat as SupportedFormat
from .._schemas.protocol.get_adcp_capabilities_response import SupportedIdentifierType as SupportedIdentifierType
from .._schemas.protocol.get_adcp_capabilities_response import SupportedProtocol as SupportedProtocol
from .._schemas.protocol.get_adcp_capabilities_response import SupportedScope as SupportedScope
from .._schemas.protocol.get_adcp_capabilities_response import SupportedSection as SupportedSection
from .._schemas.protocol.get_adcp_capabilities_response import Tasks1 as Tasks1
from .._schemas.protocol.get_adcp_capabilities_response import Tasks2 as Tasks2
from .._schemas.protocol.get_adcp_capabilities_response import Tasks3 as Tasks3
from .._schemas.protocol.get_adcp_capabilities_response import Tasks4 as Tasks4
from .._schemas.protocol.get_adcp_capabilities_response import Tasks5 as Tasks5
from .._schemas.protocol.get_adcp_capabilities_response import Tasks6 as Tasks6
from .._schemas.protocol.get_adcp_capabilities_response import Tasks7 as Tasks7
from .._schemas.protocol.get_adcp_capabilities_response import Tasks8 as Tasks8
from .._schemas.protocol.get_adcp_capabilities_response import Tasks9 as Tasks9
from .._schemas.protocol.get_adcp_capabilities_response import Transport1 as Transport1
from .._schemas.protocol.get_adcp_capabilities_response import Type6 as Type6
from .._schemas.protocol.get_principal_response import PrincipalCurrentResult as PrincipalCurrentResult
from .._schemas.protocol.get_principal_response import PrincipalReadFailedResult as PrincipalReadFailedResult
from .._schemas.protocol.get_principal_response import PrincipalRecognizedResult as PrincipalRecognizedResult
from .._schemas.protocol.get_principal_response import PrincipalUnconfiguredResult as PrincipalUnconfiguredResult
from .._schemas.protocol.get_principal_response import Result2 as Result2
from .._schemas.protocol.get_principal_response import Result3 as Result3
from .._schemas.protocol.get_principal_response import Result5 as Result5
from .._schemas.protocol.sync_principal_response import Action33 as Action33
from .._schemas.protocol.sync_principal_response import PrincipalAppliedResult as PrincipalAppliedResult
from .._schemas.protocol.sync_principal_response import PrincipalSyncFailedResult as PrincipalSyncFailedResult
from .._schemas.protocol.sync_principal_response import PrincipalValidatedResult as PrincipalValidatedResult
from .._schemas.protocol.sync_principal_response import Result13 as Result13
from .._schemas.protocol.sync_principal_response import Result15 as Result15
from .._schemas.registries.v1_canonical_mapping import ParameterMapping as ParameterMapping
from .._schemas.registries.v1_canonical_mapping import V1Pattern as V1Pattern
from .._schemas.registries.v1_canonical_mapping import V1Pattern1 as V1Pattern1
from .._schemas.signals.activate_signal_response import ActivateSignalResponse1 as ActivateSignalResponse1
from .._schemas.signals.activate_signal_response import ActivateSignalResponse2 as ActivateSignalResponse2
from .._schemas.sponsored_intelligence.si_capabilities import SiCapabilities as SiCapabilities
from .._schemas.sponsored_intelligence.si_capabilities import StandardEnum as StandardEnum
from .._schemas.sponsored_intelligence.si_context_use import SiContextUse as SiContextUse
from .._schemas.sponsored_intelligence.si_get_offering_request import SiGetOfferingRequest as SiGetOfferingRequest
from .._schemas.sponsored_intelligence.si_get_offering_response import MatchingProduct as MatchingProduct
from .._schemas.sponsored_intelligence.si_get_offering_response import SiGetOfferingResponse as SiGetOfferingResponse
from .._schemas.sponsored_intelligence.si_identity import ConsentScopeEnum as ConsentScopeEnum
from .._schemas.sponsored_intelligence.si_identity import SiIdentity as SiIdentity
from .._schemas.sponsored_intelligence.si_initiate_session_request import (
    SiInitiateSessionRequest as SiInitiateSessionRequest,
)
from .._schemas.sponsored_intelligence.si_initiate_session_response import (
    SiInitiateSessionResponse as SiInitiateSessionResponse,
)
from .._schemas.sponsored_intelligence.si_send_message_request import SiSendMessageRequest as SiSendMessageRequest
from .._schemas.sponsored_intelligence.si_send_message_response import SiSendMessageResponse as SiSendMessageResponse
from .._schemas.sponsored_intelligence.si_sponsored_context import SiSponsoredContext as SiSponsoredContext
from .._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    SiSponsoredContextReceipt as SiSponsoredContextReceipt,
)
from .._schemas.sponsored_intelligence.si_sponsored_context_receipt import Status46 as Status46
from .._schemas.sponsored_intelligence.si_terminate_session_request import (
    SiTerminateSessionRequest as SiTerminateSessionRequest,
)
from .._schemas.sponsored_intelligence.si_terminate_session_response import (
    SiTerminateSessionResponse as SiTerminateSessionResponse,
)
from .._schemas.sponsored_intelligence.si_ui_element import SiUiElement as SiUiElement
from .._schemas.trusted_match.context_match_request import ArtifactRef as ArtifactRef
from .._schemas.trusted_match.context_match_response import SignalsByProvider as SignalsByProvider
from .._schemas.trusted_match.context_match_response import TargetingKv as TargetingKv
from .._schemas.trusted_match.error import TmpError as TmpError
from .._schemas.trusted_match.identity_match_request import Identity as Identity
from .._schemas.trusted_match.identity_match_request import SealedCredential as SealedCredential
from .._schemas.trusted_match.identity_match_response import IdentityMatchResponse as IdentityMatchResponse
from .._schemas.trusted_match.identity_match_response import TmpxProviders as TmpxProviders
from .._schemas.trusted_match.provider_registration import TmpProviderRegistration as TmpProviderRegistration
from .._schemas.trusted_match.provider_registration import TmpProviderRegistration1 as TmpProviderRegistration1
from .._schemas.trusted_match.provider_registration import TmpProviderRegistration2 as TmpProviderRegistration2
from .._schemas.trusted_match.publisher_targeting_kv_config import (
    PublisherTargetingKvMapping as PublisherTargetingKvMapping,
)
from .._schemas.trusted_match.publisher_tmpx_config import PublisherTmpxMacroMapping as PublisherTmpxMacroMapping
from .._schemas.trusted_match.tmpx_chunk import TmpxChunk as TmpxChunk
from .a2ui import A2UIBoundValue as A2UIBoundValue
from .a2ui import A2UIBoundValueLiteralBoolean as A2UIBoundValueLiteralBoolean
from .a2ui import A2UIBoundValueLiteralNumber as A2UIBoundValueLiteralNumber
from .a2ui import A2UIBoundValueLiteralString as A2UIBoundValueLiteralString
from .a2ui import A2UIBoundValueLiteralStringPath as A2UIBoundValueLiteralStringPath
from .a2ui import A2UIBoundValuePath as A2UIBoundValuePath
from .a2ui import A2UIComponent as A2UIComponent
from .a2ui import A2UISurface as A2UISurface
from .a2ui import A2UIUserAction as A2UIUserAction
from .a2ui import A2UIUserActionAction as A2UIUserActionAction
from .a2ui import ComponentValue as ComponentValue
from .a2ui import SIComponentCatalog as SIComponentCatalog
from .a2ui import SIComponentCatalogComponentsItem as SIComponentCatalogComponentsItem
from .aao import AAODirectoryAgentPublishersInverseLookupResponse as AAODirectoryAgentPublishersInverseLookupResponse
from .aao import (
    AAODirectoryAgentPublishersInverseLookupResponsePublisherEntry as AAODirectoryAgentPublishersInverseLookupResponsePublisherEntry,
)
from .aao import (
    AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryDiscoveryMethod as AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryDiscoveryMethod,
)
from .aao import (
    AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryStatus as AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryStatus,
)
from .account import GetAccountFinancialsError as GetAccountFinancialsError
from .account import GetAccountFinancialsRequest as GetAccountFinancialsRequest
from .account import GetAccountFinancialsResponse as GetAccountFinancialsResponse
from .account import GetAccountFinancialsSuccess as GetAccountFinancialsSuccess
from .account import GetAccountFinancialsSuccessBalance as GetAccountFinancialsSuccessBalance
from .account import GetAccountFinancialsSuccessBalanceLastTopUp as GetAccountFinancialsSuccessBalanceLastTopUp
from .account import GetAccountFinancialsSuccessCredit as GetAccountFinancialsSuccessCredit
from .account import GetAccountFinancialsSuccessInvoicesItem as GetAccountFinancialsSuccessInvoicesItem
from .account import GetAccountFinancialsSuccessInvoicesItemStatus as GetAccountFinancialsSuccessInvoicesItemStatus
from .account import GetAccountFinancialsSuccessPaymentStatus as GetAccountFinancialsSuccessPaymentStatus
from .account import GetAccountFinancialsSuccessSpend as GetAccountFinancialsSuccessSpend
from .account import ListAccountChangesRequest as ListAccountChangesRequest
from .account import ListAccountChangesRequestStartingPosition as ListAccountChangesRequestStartingPosition
from .account import ListAccountChangesResponse as ListAccountChangesResponse
from .account import ListAccountChangesResponseCompleted as ListAccountChangesResponseCompleted
from .account import ListAccountChangesResponseFailed as ListAccountChangesResponseFailed
from .account import ListAccountChangesResponseSourceCoverageItem as ListAccountChangesResponseSourceCoverageItem
from .account import (
    ListAccountChangesResponseSourceCoverageItemKind as ListAccountChangesResponseSourceCoverageItemKind,
)
from .account import (
    ListAccountChangesResponseSourceCoverageItemStatus as ListAccountChangesResponseSourceCoverageItemStatus,
)
from .account import ListAccountsRequest as ListAccountsRequest
from .account import ListAccountsResponse as ListAccountsResponse
from .account import ProvisioningMode as ProvisioningMode
from .account import ReportUsageRequest as ReportUsageRequest
from .account import ReportUsageRequestUsageItem as ReportUsageRequestUsageItem
from .account import ReportUsageResponse as ReportUsageResponse
from .account import SettingsUpdateMode as SettingsUpdateMode
from .account import SyncAccountsError as SyncAccountsError
from .account import SyncAccountsRequest as SyncAccountsRequest
from .account import SyncAccountsRequestAccountsItem as SyncAccountsRequestAccountsItem
from .account import (
    SyncAccountsRequestAccountsItemNotificationConfigsItem as SyncAccountsRequestAccountsItemNotificationConfigsItem,
)
from .account import SyncAccountsResponse as SyncAccountsResponse
from .account import SyncAccountsSuccess as SyncAccountsSuccess
from .account import SyncAccountsSuccessAccountsItem as SyncAccountsSuccessAccountsItem
from .account import SyncAccountsSuccessAccountsItemAction as SyncAccountsSuccessAccountsItemAction
from .account import SyncGovernanceError as SyncGovernanceError
from .account import SyncGovernanceRequest as SyncGovernanceRequest
from .account import SyncGovernanceRequestAccountsItem as SyncGovernanceRequestAccountsItem
from .account import (
    SyncGovernanceRequestAccountsItemGovernanceAgentsItem as SyncGovernanceRequestAccountsItemGovernanceAgentsItem,
)
from .account import (
    SyncGovernanceRequestAccountsItemGovernanceAgentsItemAuthentication as SyncGovernanceRequestAccountsItemGovernanceAgentsItemAuthentication,
)
from .account import SyncGovernanceResponse as SyncGovernanceResponse
from .account import SyncGovernanceSuccess as SyncGovernanceSuccess
from .account import SyncGovernanceSuccessAccountsItem as SyncGovernanceSuccessAccountsItem
from .account import SyncGovernanceSuccessAccountsItemStatus as SyncGovernanceSuccessAccountsItemStatus
from .adagents import AdCPAgentsAuthorization as AdCPAgentsAuthorization
from .adagents import AdCPAgentsAuthorizationAuthoritativeLocation as AdCPAgentsAuthorizationAuthoritativeLocation
from .adagents import AdCPAgentsAuthorizationCommunityFormatRegistry as AdCPAgentsAuthorizationCommunityFormatRegistry
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryCollections as AdCPAgentsAuthorizationCommunityFormatRegistryCollections,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryContact as AdCPAgentsAuthorizationCommunityFormatRegistryContact,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryFormats as AdCPAgentsAuthorizationCommunityFormatRegistryFormats,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryFormatsItem as AdCPAgentsAuthorizationCommunityFormatRegistryFormatsItem,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryPlacements as AdCPAgentsAuthorizationCommunityFormatRegistryPlacements,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryPlacementTagsValue as AdCPAgentsAuthorizationCommunityFormatRegistryPlacementTagsValue,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryProperties as AdCPAgentsAuthorizationCommunityFormatRegistryProperties,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryPropertyFeaturesItem as AdCPAgentsAuthorizationCommunityFormatRegistryPropertyFeaturesItem,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem as AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItemReason as AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItemReason,
)
from .adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistrySignals as AdCPAgentsAuthorizationCommunityFormatRegistrySignals,
)
from .adagents import DelegationType as DelegationType
from .adagents import FormatsItemAgentPlacement as FormatsItemAgentPlacement
from .adagents import FormatsItemAudioDaast as FormatsItemAudioDaast
from .adagents import FormatsItemAudioHosted as FormatsItemAudioHosted
from .adagents import FormatsItemAudioVast as FormatsItemAudioVast
from .adagents import FormatsItemCoordinatedPlacements as FormatsItemCoordinatedPlacements
from .adagents import FormatsItemCustom as FormatsItemCustom
from .adagents import FormatsItemDisplayTag as FormatsItemDisplayTag
from .adagents import FormatsItemHtml5 as FormatsItemHtml5
from .adagents import FormatsItemImage as FormatsItemImage
from .adagents import FormatsItemImageCarousel as FormatsItemImageCarousel
from .adagents import FormatsItemNativeInFeed as FormatsItemNativeInFeed
from .adagents import FormatsItemResponsiveCreative as FormatsItemResponsiveCreative
from .adagents import FormatsItemSellerRenderedStatefulDisplay as FormatsItemSellerRenderedStatefulDisplay
from .adagents import FormatsItemSponsoredPlacement as FormatsItemSponsoredPlacement
from .adagents import FormatsItemVideoHosted as FormatsItemVideoHosted
from .adagents import FormatsItemVideoVast as FormatsItemVideoVast
from .adagents import SignalTagsValue as SignalTagsValue
from .brand import AcquireRightsAcquired as AcquireRightsAcquired
from .brand import AcquireRightsAcquiredDisclosure as AcquireRightsAcquiredDisclosure
from .brand import AcquireRightsAcquiredRightsConstraint as AcquireRightsAcquiredRightsConstraint
from .brand import AcquireRightsError as AcquireRightsError
from .brand import AcquireRightsPendingApproval as AcquireRightsPendingApproval
from .brand import AcquireRightsRejected as AcquireRightsRejected
from .brand import AcquireRightsRequest as AcquireRightsRequest
from .brand import AcquireRightsRequestCampaign as AcquireRightsRequestCampaign
from .brand import AcquireRightsResponse as AcquireRightsResponse
from .brand import Agents as Agents
from .brand import AuthoritativeLocationRedirect as AuthoritativeLocationRedirect
from .brand import BrandAgent as BrandAgent
from .brand import BrandCanonicalDocument as BrandCanonicalDocument
from .brand import BrandDiscovery as BrandDiscovery
from .brand import BrandDiscoveryAsset as BrandDiscoveryAsset
from .brand import BrandDiscoveryAssetLibrary as BrandDiscoveryAssetLibrary
from .brand import BrandDiscoveryAssetLibraryColorGuide as BrandDiscoveryAssetLibraryColorGuide
from .brand import BrandDiscoveryAssetLibraryColorGuidePalettesItem as BrandDiscoveryAssetLibraryColorGuidePalettesItem
from .brand import BrandDiscoveryAssetLibraryType as BrandDiscoveryAssetLibraryType
from .brand import BrandDiscoveryAuthorizedOperator as BrandDiscoveryAuthorizedOperator
from .brand import BrandDiscoveryAuthorizedOperatorScopesItem as BrandDiscoveryAuthorizedOperatorScopesItem
from .brand import BrandDiscoveryBorderRadius as BrandDiscoveryBorderRadius
from .brand import BrandDiscoveryBrand as BrandDiscoveryBrand
from .brand import BrandDiscoveryBrandAgent as BrandDiscoveryBrandAgent
from .brand import BrandDiscoveryBrandAgentEntry as BrandDiscoveryBrandAgentEntry
from .brand import BrandDiscoveryBrandAvatar as BrandDiscoveryBrandAvatar
from .brand import BrandDiscoveryBrandCollectionsItem as BrandDiscoveryBrandCollectionsItem
from .brand import BrandDiscoveryBrandContact as BrandDiscoveryBrandContact
from .brand import BrandDiscoveryBrandDisclaimersItem as BrandDiscoveryBrandDisclaimersItem
from .brand import BrandDiscoveryBrandShapes as BrandDiscoveryBrandShapes
from .brand import BrandDiscoveryBrandShapesUsage as BrandDiscoveryBrandShapesUsage
from .brand import BrandDiscoveryBrandVoiceSynthesis as BrandDiscoveryBrandVoiceSynthesis
from .brand import BrandDiscoveryColorConstraint as BrandDiscoveryColorConstraint
from .brand import BrandDiscoveryColorConstraintAppliesToItem as BrandDiscoveryColorConstraintAppliesToItem
from .brand import BrandDiscoveryColorRef as BrandDiscoveryColorRef
from .brand import BrandDiscoveryColorRefKind as BrandDiscoveryColorRefKind
from .brand import BrandDiscoveryColorRefSurface as BrandDiscoveryColorRefSurface
from .brand import BrandDiscoveryColors as BrandDiscoveryColors
from .brand import BrandDiscoveryColorway as BrandDiscoveryColorway
from .brand import BrandDiscoveryCompositionRules as BrandDiscoveryCompositionRules
from .brand import BrandDiscoveryCompositionRulesBackgrounds as BrandDiscoveryCompositionRulesBackgrounds
from .brand import (
    BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem as BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem,
)
from .brand import BrandDiscoveryCompositionRulesOverlays as BrandDiscoveryCompositionRulesOverlays
from .brand import (
    BrandDiscoveryCompositionRulesOverlaysGradientStyle as BrandDiscoveryCompositionRulesOverlaysGradientStyle,
)
from .brand import BrandDiscoveryCompositionRulesTexture as BrandDiscoveryCompositionRulesTexture
from .brand import BrandDiscoveryCompositionRulesTextureIntensity as BrandDiscoveryCompositionRulesTextureIntensity
from .brand import BrandDiscoveryCompositionRulesTextureStyle as BrandDiscoveryCompositionRulesTextureStyle
from .brand import BrandDiscoveryContact as BrandDiscoveryContact
from .brand import BrandDiscoveryDataSubjectContestation as BrandDiscoveryDataSubjectContestation
from .brand import BrandDiscoveryElevation as BrandDiscoveryElevation
from .brand import BrandDiscoveryFontFile as BrandDiscoveryFontFile
from .brand import BrandDiscoveryFontFileStyle as BrandDiscoveryFontFileStyle
from .brand import BrandDiscoveryFontRole as BrandDiscoveryFontRole
from .brand import BrandDiscoveryFontRoleFamily as BrandDiscoveryFontRoleFamily
from .brand import BrandDiscoveryFonts as BrandDiscoveryFonts
from .brand import BrandDiscoveryGraphicElement as BrandDiscoveryGraphicElement
from .brand import BrandDiscoveryGraphicElementOrientation as BrandDiscoveryGraphicElementOrientation
from .brand import BrandDiscoveryGraphicElementType as BrandDiscoveryGraphicElementType
from .brand import BrandDiscoveryGraphicStyle as BrandDiscoveryGraphicStyle
from .brand import BrandDiscoveryGraphicStyleStrokeStyle as BrandDiscoveryGraphicStyleStrokeStyle
from .brand import BrandDiscoveryGraphicStyleStyleType as BrandDiscoveryGraphicStyleStyleType
from .brand import BrandDiscoveryGuidelineSeverity as BrandDiscoveryGuidelineSeverity
from .brand import BrandDiscoveryHouse as BrandDiscoveryHouse
from .brand import BrandDiscoveryHouseArchitecture as BrandDiscoveryHouseArchitecture
from .brand import BrandDiscoveryIconography as BrandDiscoveryIconography
from .brand import BrandDiscoveryIconographyCornerStyle as BrandDiscoveryIconographyCornerStyle
from .brand import BrandDiscoveryIconographyStyle as BrandDiscoveryIconographyStyle
from .brand import BrandDiscoveryIconographyUsage as BrandDiscoveryIconographyUsage
from .brand import BrandDiscoveryIdentityRelyingParty as BrandDiscoveryIdentityRelyingParty
from .brand import BrandDiscoveryIdentityRelyingPartyScope as BrandDiscoveryIdentityRelyingPartyScope
from .brand import BrandDiscoveryKellerType as BrandDiscoveryKellerType
from .brand import BrandDiscoveryLogo as BrandDiscoveryLogo
from .brand import BrandDiscoveryLogoBackground as BrandDiscoveryLogoBackground
from .brand import BrandDiscoveryLogoOrientation as BrandDiscoveryLogoOrientation
from .brand import BrandDiscoveryLogoPlacement as BrandDiscoveryLogoPlacement
from .brand import BrandDiscoveryLogoPlacementBackgroundContrast as BrandDiscoveryLogoPlacementBackgroundContrast
from .brand import BrandDiscoveryLogoPlacementPreferredPosition as BrandDiscoveryLogoPlacementPreferredPosition
from .brand import BrandDiscoveryLogoUsageRule as BrandDiscoveryLogoUsageRule
from .brand import BrandDiscoveryLogoUsageRuleMinimumSize as BrandDiscoveryLogoUsageRuleMinimumSize
from .brand import BrandDiscoveryLogoVariant as BrandDiscoveryLogoVariant
from .brand import BrandDiscoveryMarkLockup as BrandDiscoveryMarkLockup
from .brand import BrandDiscoveryMarkLockupLockupType as BrandDiscoveryMarkLockupLockupType
from .brand import BrandDiscoveryMarkLockupOrdering as BrandDiscoveryMarkLockupOrdering
from .brand import BrandDiscoveryMarkLockupSeparator as BrandDiscoveryMarkLockupSeparator
from .brand import BrandDiscoveryMarkLockupSeparatorType as BrandDiscoveryMarkLockupSeparatorType
from .brand import BrandDiscoveryMotionGuidelines as BrandDiscoveryMotionGuidelines
from .brand import BrandDiscoveryMotionGuidelinesAnimationSpeed as BrandDiscoveryMotionGuidelinesAnimationSpeed
from .brand import BrandDiscoveryMotionGuidelinesPacing as BrandDiscoveryMotionGuidelinesPacing
from .brand import BrandDiscoveryMotionGuidelinesTextEntrance as BrandDiscoveryMotionGuidelinesTextEntrance
from .brand import BrandDiscoveryMotionGuidelinesTransitionStyle as BrandDiscoveryMotionGuidelinesTransitionStyle
from .brand import BrandDiscoveryPhotographyStyle as BrandDiscoveryPhotographyStyle
from .brand import BrandDiscoveryPhotographyStyleColorTemperature as BrandDiscoveryPhotographyStyleColorTemperature
from .brand import BrandDiscoveryPhotographyStyleContrast as BrandDiscoveryPhotographyStyleContrast
from .brand import BrandDiscoveryPhotographyStyleDepthOfField as BrandDiscoveryPhotographyStyleDepthOfField
from .brand import BrandDiscoveryPhotographyStyleFraming as BrandDiscoveryPhotographyStyleFraming
from .brand import BrandDiscoveryPhotographyStyleRealism as BrandDiscoveryPhotographyStyleRealism
from .brand import BrandDiscoveryPhotographyStyleSubject as BrandDiscoveryPhotographyStyleSubject
from .brand import BrandDiscoveryPhotographyStyleSubjectPeople as BrandDiscoveryPhotographyStyleSubjectPeople
from .brand import (
    BrandDiscoveryPhotographyStyleSubjectProductFocus as BrandDiscoveryPhotographyStyleSubjectProductFocus,
)
from .brand import BrandDiscoveryPortfolioEntry as BrandDiscoveryPortfolioEntry
from .brand import BrandDiscoveryProductCatalog as BrandDiscoveryProductCatalog
from .brand import BrandDiscoveryProductCatalogAgenticCheckout as BrandDiscoveryProductCatalogAgenticCheckout
from .brand import BrandDiscoveryProperty as BrandDiscoveryProperty
from .brand import BrandDiscoveryPropertyRelationship as BrandDiscoveryPropertyRelationship
from .brand import BrandDiscoveryPropertyStore as BrandDiscoveryPropertyStore
from .brand import BrandDiscoveryRightsAgent as BrandDiscoveryRightsAgent
from .brand import BrandDiscoverySpacing as BrandDiscoverySpacing
from .brand import BrandDiscoverySpacingScale as BrandDiscoverySpacingScale
from .brand import BrandDiscoveryTrademark as BrandDiscoveryTrademark
from .brand import BrandDiscoveryTrademarkLicenseType as BrandDiscoveryTrademarkLicenseType
from .brand import BrandDiscoveryTrademarkStatus as BrandDiscoveryTrademarkStatus
from .brand import BrandDiscoveryTypeScaleEntry as BrandDiscoveryTypeScaleEntry
from .brand import BrandDiscoveryTypeScaleEntryTextTransform as BrandDiscoveryTypeScaleEntryTextTransform
from .brand import BrandDiscoveryVisualGuidelines as BrandDiscoveryVisualGuidelines
from .brand import BrandDiscoveryVisualGuidelinesTypeScale as BrandDiscoveryVisualGuidelinesTypeScale
from .brand import BrandId as BrandId
from .brand import ClaimEntry as ClaimEntry
from .brand import ColorRefName as ColorRefName
from .brand import ColorRefSurface as ColorRefSurface
from .brand import ColorRefValue as ColorRefValue
from .brand import ColorValue as ColorValue
from .brand import CreativeApprovalError as CreativeApprovalError
from .brand import CreativeApprovalRequest as CreativeApprovalRequest
from .brand import CreativeApprovalResponse as CreativeApprovalResponse
from .brand import CreativeApproved as CreativeApproved
from .brand import CreativePendingReview as CreativePendingReview
from .brand import CreativeRejected as CreativeRejected
from .brand import GetBrandIdentityError as GetBrandIdentityError
from .brand import GetBrandIdentityRequest as GetBrandIdentityRequest
from .brand import GetBrandIdentityRequestFieldsItem as GetBrandIdentityRequestFieldsItem
from .brand import GetBrandIdentityResponse as GetBrandIdentityResponse
from .brand import GetBrandIdentityResponseFontRole as GetBrandIdentityResponseFontRole
from .brand import GetBrandIdentityResponseFontRoleFamily as GetBrandIdentityResponseFontRoleFamily
from .brand import GetBrandIdentitySuccess as GetBrandIdentitySuccess
from .brand import GetBrandIdentitySuccessAssetsItem as GetBrandIdentitySuccessAssetsItem
from .brand import GetBrandIdentitySuccessColors as GetBrandIdentitySuccessColors
from .brand import GetBrandIdentitySuccessFonts as GetBrandIdentitySuccessFonts
from .brand import GetBrandIdentitySuccessHouse as GetBrandIdentitySuccessHouse
from .brand import GetBrandIdentitySuccessLogosItem as GetBrandIdentitySuccessLogosItem
from .brand import GetBrandIdentitySuccessRights as GetBrandIdentitySuccessRights
from .brand import GetBrandIdentitySuccessTone as GetBrandIdentitySuccessTone
from .brand import GetBrandIdentitySuccessVoiceSynthesis as GetBrandIdentitySuccessVoiceSynthesis
from .brand import GetRightsError as GetRightsError
from .brand import GetRightsRequest as GetRightsRequest
from .brand import GetRightsResponse as GetRightsResponse
from .brand import GetRightsSuccess as GetRightsSuccess
from .brand import GetRightsSuccessExcludedItem as GetRightsSuccessExcludedItem
from .brand import GetRightsSuccessRightsItem as GetRightsSuccessRightsItem
from .brand import GetRightsSuccessRightsItemExclusivityStatus as GetRightsSuccessRightsItemExclusivityStatus
from .brand import GetRightsSuccessRightsItemPreviewAssetsItem as GetRightsSuccessRightsItemPreviewAssetsItem
from .brand import HexColor as HexColor
from .brand import HousePortfolio as HousePortfolio
from .brand import HouseRedirect as HouseRedirect
from .brand import HouseRedirectRedirectReason as HouseRedirectRedirectReason
from .brand import LocalizedName as LocalizedName
from .brand import LocalizedScalar as LocalizedScalar
from .brand import LocalizedStringList as LocalizedStringList
from .brand import LocalizedStringListEntry as LocalizedStringListEntry
from .brand import LogoId as LogoId
from .brand import ResultEntry as ResultEntry
from .brand import RevocationNotification as RevocationNotification
from .brand import RightsPricingOption as RightsPricingOption
from .brand import RightsTerms as RightsTerms
from .brand import RightsTermsExclusivity as RightsTermsExclusivity
from .brand import SearchBrandsError as SearchBrandsError
from .brand import SearchBrandsRequest as SearchBrandsRequest
from .brand import SearchBrandsResponse as SearchBrandsResponse
from .brand import SearchBrandsResponseSearchBrandResult as SearchBrandsResponseSearchBrandResult
from .brand import SearchBrandsResponseSearchBrandResultLogosItem as SearchBrandsResponseSearchBrandResultLogosItem
from .brand import (
    SearchBrandsResponseSearchBrandResultRelationshipTrust as SearchBrandsResponseSearchBrandResultRelationshipTrust,
)
from .brand import SearchBrandsResponseSearchBrandResultRights as SearchBrandsResponseSearchBrandResultRights
from .brand import SearchBrandsSuccess as SearchBrandsSuccess
from .brand import Tone as Tone
from .brand import UpdateRightsError as UpdateRightsError
from .brand import UpdateRightsRequest as UpdateRightsRequest
from .brand import UpdateRightsResponse as UpdateRightsResponse
from .brand import UpdateRightsSuccess as UpdateRightsSuccess
from .brand import UpdateRightsSuccessRightsConstraint as UpdateRightsSuccessRightsConstraint
from .brand import VerificationStatus as VerificationStatus
from .brand import VerifyBrandClaimError as VerifyBrandClaimError
from .brand import VerifyBrandClaimRequest as VerifyBrandClaimRequest
from .brand import VerifyBrandClaimResponse as VerifyBrandClaimResponse
from .brand import VerifyBrandClaimResponseSignedResponse as VerifyBrandClaimResponseSignedResponse
from .brand import VerifyBrandClaimResponseSignedResponsePayload as VerifyBrandClaimResponseSignedResponsePayload
from .brand import VerifyBrandClaimResponseSignedSuccessPayload as VerifyBrandClaimResponseSignedSuccessPayload
from .brand import (
    VerifyBrandClaimResponseSignedSuccessPayloadClaimType as VerifyBrandClaimResponseSignedSuccessPayloadClaimType,
)
from .brand import VerifyBrandClaimsError as VerifyBrandClaimsError
from .brand import VerifyBrandClaimsRequestBulk as VerifyBrandClaimsRequestBulk
from .brand import VerifyBrandClaimsResponseBulk as VerifyBrandClaimsResponseBulk
from .brand import VerifyBrandClaimsResponseBulkSignedResponse as VerifyBrandClaimsResponseBulkSignedResponse
from .brand import (
    VerifyBrandClaimsResponseBulkSignedResponsePayload as VerifyBrandClaimsResponseBulkSignedResponsePayload,
)
from .brand import (
    VerifyBrandClaimsResponseBulkSignedSuccessPayload as VerifyBrandClaimsResponseBulkSignedSuccessPayload,
)
from .brand import VerifyBrandClaimsResultError as VerifyBrandClaimsResultError
from .brand import VerifyBrandClaimsResultSuccess as VerifyBrandClaimsResultSuccess
from .brand import VerifyBrandClaimsSuccess as VerifyBrandClaimsSuccess
from .brand import VerifyBrandClaimSuccess as VerifyBrandClaimSuccess
from .brand import VerifyParentClaim as VerifyParentClaim
from .brand import VerifyParentClaimClaim as VerifyParentClaimClaim
from .brand import VerifyPropertyClaim as VerifyPropertyClaim
from .brand import VerifyPropertyClaimClaim as VerifyPropertyClaimClaim
from .brand import VerifyPropertyClaimClaimProperty as VerifyPropertyClaimClaimProperty
from .brand import VerifyPropertyClaimClaimPropertyStore as VerifyPropertyClaimClaimPropertyStore
from .brand import VerifySubsidiaryClaim as VerifySubsidiaryClaim
from .brand import VerifySubsidiaryClaimClaim as VerifySubsidiaryClaimClaim
from .brand import VerifyTrademarkClaim as VerifyTrademarkClaim
from .brand import VerifyTrademarkClaimClaim as VerifyTrademarkClaimClaim
from .collection import BaseCollectionSource as BaseCollectionSource
from .collection import CollectionList as CollectionList
from .collection import CollectionListChangedWebhook as CollectionListChangedWebhook
from .collection import CollectionListChangedWebhookChangeSummary as CollectionListChangedWebhookChangeSummary
from .collection import CollectionListFilters as CollectionListFilters
from .collection import CreateCollectionListRequest as CreateCollectionListRequest
from .collection import CreateCollectionListResponse as CreateCollectionListResponse
from .collection import DeleteCollectionListRequest as DeleteCollectionListRequest
from .collection import DeleteCollectionListResponse as DeleteCollectionListResponse
from .collection import DistributionIDsSource as DistributionIDsSource
from .collection import DistributionIDsSourceIdentifiersItem as DistributionIDsSourceIdentifiersItem
from .collection import GetCollectionListRequest as GetCollectionListRequest
from .collection import GetCollectionListRequestPagination as GetCollectionListRequestPagination
from .collection import GetCollectionListResponse as GetCollectionListResponse
from .collection import GetCollectionListResponseCollectionsItem as GetCollectionListResponseCollectionsItem
from .collection import ListCollectionListsRequest as ListCollectionListsRequest
from .collection import ListCollectionListsResponse as ListCollectionListsResponse
from .collection import PublisherCollectionsSource as PublisherCollectionsSource
from .collection import PublisherGenresSource as PublisherGenresSource
from .collection import UpdateCollectionListRequest as UpdateCollectionListRequest
from .collection import UpdateCollectionListResponse as UpdateCollectionListResponse
from .compliance import ComplianceTaskCompletionData as ComplianceTaskCompletionData
from .compliance import ComplyTestControllerRequest as ComplyTestControllerRequest
from .compliance import ComplyTestControllerRequestAccount as ComplyTestControllerRequestAccount
from .compliance import ComplyTestControllerRequestParams as ComplyTestControllerRequestParams
from .compliance import ComplyTestControllerRequestParamsAdvanceTo as ComplyTestControllerRequestParamsAdvanceTo
from .compliance import ComplyTestControllerRequestParamsArm as ComplyTestControllerRequestParamsArm
from .compliance import ComplyTestControllerRequestParamsDoohMetrics as ComplyTestControllerRequestParamsDoohMetrics
from .compliance import ComplyTestControllerRequestParamsMetricsItem as ComplyTestControllerRequestParamsMetricsItem
from .compliance import ComplyTestControllerRequestParamsOperation as ComplyTestControllerRequestParamsOperation
from .compliance import ComplyTestControllerRequestParamsPurgeKind as ComplyTestControllerRequestParamsPurgeKind
from .compliance import ComplyTestControllerRequestParamsViewability as ComplyTestControllerRequestParamsViewability
from .compliance import ComplyTestControllerResponse as ComplyTestControllerResponse
from .compliance import ControllerError as ControllerError
from .compliance import ControllerErrorError as ControllerErrorError
from .compliance import CreateMediaBuyCompletion as CreateMediaBuyCompletion
from .compliance import DigestAttestation as DigestAttestation
from .compliance import ForcedDirectiveSuccess as ForcedDirectiveSuccess
from .compliance import ForcedDirectiveSuccessForced as ForcedDirectiveSuccessForced
from .compliance import GetCreativeFeaturesCompletion as GetCreativeFeaturesCompletion
from .compliance import GetCreativeFeaturesComplianceCompletion as GetCreativeFeaturesComplianceCompletion
from .compliance import GetProductsCompletion as GetProductsCompletion
from .compliance import GetSignalsCompletion as GetSignalsCompletion
from .compliance import ListScenariosSuccess as ListScenariosSuccess
from .compliance import (
    NotYetMeasurableVendorMetricsByPackageValueItem as NotYetMeasurableVendorMetricsByPackageValueItem,
)
from .compliance import ProvenanceAuditObservationsSuccess as ProvenanceAuditObservationsSuccess
from .compliance import RawAttestation as RawAttestation
from .compliance import SeedSuccess as SeedSuccess
from .compliance import SimulationSuccess as SimulationSuccess
from .compliance import StateTransitionSuccess as StateTransitionSuccess
from .compliance import UpstreamTrafficSuccess as UpstreamTrafficSuccess
from .compliance import UpstreamTrafficSuccessRecordedCallsItem as UpstreamTrafficSuccessRecordedCallsItem
from .compliance import (
    UpstreamTrafficSuccessRecordedCallsItemAttestationMode as UpstreamTrafficSuccessRecordedCallsItemAttestationMode,
)
from .compliance import (
    UpstreamTrafficSuccessRecordedCallsItemIdentifierMatchProofsItem as UpstreamTrafficSuccessRecordedCallsItemIdentifierMatchProofsItem,
)
from .compliance import UpstreamTrafficSuccessRecordedCallsItemMethod as UpstreamTrafficSuccessRecordedCallsItemMethod
from .compliance import UpstreamTrafficSuccessRecordedCallsItemPurpose as UpstreamTrafficSuccessRecordedCallsItemPurpose
from .content_standards import Artifact as Artifact
from .content_standards import ArtifactAssetAccessServiceAccountProvider as ArtifactAssetAccessServiceAccountProvider
from .content_standards import ArtifactAssetsItemAudioTranscriptSource as ArtifactAssetsItemAudioTranscriptSource
from .content_standards import ArtifactAssetsItemTextContentFormat as ArtifactAssetsItemTextContentFormat
from .content_standards import ArtifactAssetsItemTextRole as ArtifactAssetsItemTextRole
from .content_standards import ArtifactAssetsItemVideoTranscriptSource as ArtifactAssetsItemVideoTranscriptSource
from .content_standards import ArtifactIdentifiers as ArtifactIdentifiers
from .content_standards import ArtifactMetadata as ArtifactMetadata
from .content_standards import ArtifactWebhookPayload as ArtifactWebhookPayload
from .content_standards import ArtifactWebhookPayloadArtifactsItem as ArtifactWebhookPayloadArtifactsItem
from .content_standards import ArtifactWebhookPayloadPagination as ArtifactWebhookPayloadPagination
from .content_standards import AssetAccess as AssetAccess
from .content_standards import AssetAccessBearerToken as AssetAccessBearerToken
from .content_standards import AssetAccessServiceAccount as AssetAccessServiceAccount
from .content_standards import AssetAccessSignedUrl as AssetAccessSignedUrl
from .content_standards import AssetsItemAudio as AssetsItemAudio
from .content_standards import AssetsItemAudioTranscriptFormat as AssetsItemAudioTranscriptFormat
from .content_standards import AssetsItemImage as AssetsItemImage
from .content_standards import AssetsItemText as AssetsItemText
from .content_standards import AssetsItemVideo as AssetsItemVideo
from .content_standards import CalibrateContentRequest as CalibrateContentRequest
from .content_standards import CalibrateContentResponse as CalibrateContentResponse
from .content_standards import CalibrateContentResponseVerdict as CalibrateContentResponseVerdict
from .content_standards import (
    CalibrateContentResponseVerdictFeaturesItem as CalibrateContentResponseVerdictFeaturesItem,
)
from .content_standards import ContentStandards as ContentStandards
from .content_standards import ContentStandardsCalibrationExemplars as ContentStandardsCalibrationExemplars
from .content_standards import CreateContentStandardsRequest as CreateContentStandardsRequest
from .content_standards import (
    CreateContentStandardsRequestCalibrationExemplars as CreateContentStandardsRequestCalibrationExemplars,
)
from .content_standards import CreateContentStandardsRequestScope as CreateContentStandardsRequestScope
from .content_standards import CreateContentStandardsResponse as CreateContentStandardsResponse
from .content_standards import CreateContentStandardsResponseErrors as CreateContentStandardsResponseErrors
from .content_standards import CreateContentStandardsResponseStandardsId as CreateContentStandardsResponseStandardsId
from .content_standards import GetContentStandardsRequest as GetContentStandardsRequest
from .content_standards import GetContentStandardsResponse as GetContentStandardsResponse
from .content_standards import GetContentStandardsResponseErrors as GetContentStandardsResponseErrors
from .content_standards import GetMediaBuyArtifactsRequest as GetMediaBuyArtifactsRequest
from .content_standards import GetMediaBuyArtifactsRequestTimeRange as GetMediaBuyArtifactsRequestTimeRange
from .content_standards import GetMediaBuyArtifactsResponse as GetMediaBuyArtifactsResponse
from .content_standards import (
    GetMediaBuyArtifactsResponseArtifactsMediaBuyId as GetMediaBuyArtifactsResponseArtifactsMediaBuyId,
)
from .content_standards import (
    GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItem as GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItem,
)
from .content_standards import (
    GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext as GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext,
)
from .content_standards import (
    GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemLocalVerdict as GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemLocalVerdict,
)
from .content_standards import (
    GetMediaBuyArtifactsResponseArtifactsMediaBuyIdCollectionInfo as GetMediaBuyArtifactsResponseArtifactsMediaBuyIdCollectionInfo,
)
from .content_standards import GetMediaBuyArtifactsResponseErrors as GetMediaBuyArtifactsResponseErrors
from .content_standards import ListContentStandardsRequest as ListContentStandardsRequest
from .content_standards import ListContentStandardsResponse as ListContentStandardsResponse
from .content_standards import ListContentStandardsResponseErrors as ListContentStandardsResponseErrors
from .content_standards import ListContentStandardsResponseStandards as ListContentStandardsResponseStandards
from .content_standards import ObjErrorsContextExt as ObjErrorsContextExt
from .content_standards import ObjTypeValueLanguage as ObjTypeValueLanguage
from .content_standards import PassItemUrl as PassItemUrl
from .content_standards import UpdateContentStandardsError as UpdateContentStandardsError
from .content_standards import UpdateContentStandardsRequest as UpdateContentStandardsRequest
from .content_standards import UpdateContentStandardsRequestScope as UpdateContentStandardsRequestScope
from .content_standards import UpdateContentStandardsResponse as UpdateContentStandardsResponse
from .content_standards import UpdateContentStandardsSuccess as UpdateContentStandardsSuccess
from .content_standards import ValidateContentDeliveryRequest as ValidateContentDeliveryRequest
from .content_standards import ValidateContentDeliveryRequestRecordsItem as ValidateContentDeliveryRequestRecordsItem
from .content_standards import ValidateContentDeliveryResponse as ValidateContentDeliveryResponse
from .content_standards import ValidateContentDeliveryResponseErrors as ValidateContentDeliveryResponseErrors
from .content_standards import (
    ValidateContentDeliveryResponseResultsSummary as ValidateContentDeliveryResponseResultsSummary,
)
from .content_standards import (
    ValidateContentDeliveryResponseResultsSummaryResultsItem as ValidateContentDeliveryResponseResultsSummaryResultsItem,
)
from .content_standards import (
    ValidateContentDeliveryResponseResultsSummarySummary as ValidateContentDeliveryResponseResultsSummarySummary,
)
from .core import HTTPSURL as HTTPSURL
from .core import AcceptancePolicyProfileIDs as AcceptancePolicyProfileIDs
from .core import AcceptedAttestationIssuersItemAgent as AcceptedAttestationIssuersItemAgent
from .core import AcceptedAttestationIssuersItemBrand as AcceptedAttestationIssuersItemBrand
from .core import Account as Account
from .core import AccountAuthorization as AccountAuthorization
from .core import AccountChange as AccountChange
from .core import AccountChangeActor as AccountChangeActor
from .core import AccountChangeActorType as AccountChangeActorType
from .core import AccountChangeOrigin as AccountChangeOrigin
from .core import AccountChangeOriginKind as AccountChangeOriginKind
from .core import AccountChangeRecordedWebhook as AccountChangeRecordedWebhook
from .core import AccountChangeRecordedWebhookResource as AccountChangeRecordedWebhookResource
from .core import AccountChangeRepair as AccountChangeRepair
from .core import AccountChangeRepairTask as AccountChangeRepairTask
from .core import AccountChangeRepairUnavailableReason as AccountChangeRepairUnavailableReason
from .core import AccountChangeResource as AccountChangeResource
from .core import AccountCreditLimit as AccountCreditLimit
from .core import AccountGovernanceAgentsItem as AccountGovernanceAgentsItem
from .core import AccountIdentityChange as AccountIdentityChange
from .core import AccountIdentityChangeBlocked as AccountIdentityChangeBlocked
from .core import AccountIdentityChangePending as AccountIdentityChangePending
from .core import AccountIdentityChangePreview as AccountIdentityChangePreview
from .core import AccountIdentityChangePreviewImpact as AccountIdentityChangePreviewImpact
from .core import AccountIdentityChangePreviewImpactArea as AccountIdentityChangePreviewImpactArea
from .core import AccountIdentityChangePreviewImpactEffect as AccountIdentityChangePreviewImpactEffect
from .core import (
    AccountIdentityChangePreviewNonblockingImpactsItem as AccountIdentityChangePreviewNonblockingImpactsItem,
)
from .core import (
    AccountIdentityChangePreviewNonblockingImpactsItemEffect as AccountIdentityChangePreviewNonblockingImpactsItemEffect,
)
from .core import AccountIdentityChangeRejected as AccountIdentityChangeRejected
from .core import AccountIdentityChangeWouldApply as AccountIdentityChangeWouldApply
from .core import AccountIdentityChangeWouldRequireApproval as AccountIdentityChangeWouldRequireApproval
from .core import AccountReference as AccountReference
from .core import AccountReferenceAccountId as AccountReferenceAccountId
from .core import AccountReferenceBrandOperator as AccountReferenceBrandOperator
from .core import AccountReportingBucket as AccountReportingBucket
from .core import AccountReportingBucketCompression as AccountReportingBucketCompression
from .core import AccountSetup as AccountSetup
from .core import AccountStatusChangedWebhook as AccountStatusChangedWebhook
from .core import AccountStatusChangedWebhookReasonCode as AccountStatusChangedWebhookReasonCode
from .core import AccountStatusChangedWebhookSetup as AccountStatusChangedWebhookSetup
from .core import AccountTimezoneCapability as AccountTimezoneCapability
from .core import AccountTimezoneCapabilityAccountSelection as AccountTimezoneCapabilityAccountSelection
from .core import AccountTimezoneCapabilityMode as AccountTimezoneCapabilityMode
from .core import AccountWithAuthorization as AccountWithAuthorization
from .core import ActivationKey as ActivationKey
from .core import ActivationKeyKeyValue as ActivationKeyKeyValue
from .core import ActivationKeySegmentId as ActivationKeySegmentId
from .core import AdCPAssetGroupVocabularyRegistry as AdCPAssetGroupVocabularyRegistry
from .core import AdCPAsyncResponseData as AdCPAsyncResponseData
from .core import AdCPAsyncResponseDataBuildCreativeResponse as AdCPAsyncResponseDataBuildCreativeResponse
from .core import AdCPAsyncResponseDataCompactTaskInputRequired as AdCPAsyncResponseDataCompactTaskInputRequired
from .core import AdCPAsyncResponseDataCompactTaskSubmitted as AdCPAsyncResponseDataCompactTaskSubmitted
from .core import AdCPAsyncResponseDataCompactTaskWorking as AdCPAsyncResponseDataCompactTaskWorking
from .core import AdCPAsyncResponseDataCreateMediaBuyResponse as AdCPAsyncResponseDataCreateMediaBuyResponse
from .core import AdCPAsyncResponseDataDeclineProposalsResponse as AdCPAsyncResponseDataDeclineProposalsResponse
from .core import AdCPAsyncResponseDataGetCreativeFeaturesResponse as AdCPAsyncResponseDataGetCreativeFeaturesResponse
from .core import AdCPAsyncResponseDataGetProductsResponse as AdCPAsyncResponseDataGetProductsResponse
from .core import AdCPAsyncResponseDataGetSignalsResponse as AdCPAsyncResponseDataGetSignalsResponse
from .core import (
    AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult as AdCPAsyncResponseDataMediaBuyDeliveryWebhookResult,
)
from .core import AdCPAsyncResponseDataPreviewCreativeResponse as AdCPAsyncResponseDataPreviewCreativeResponse
from .core import AdCPAsyncResponseDataRefineProposalsResponse as AdCPAsyncResponseDataRefineProposalsResponse
from .core import AdCPAsyncResponseDataRejected as AdCPAsyncResponseDataRejected
from .core import AdCPAsyncResponseDataRequestProposalsResponse as AdCPAsyncResponseDataRequestProposalsResponse
from .core import AdCPAsyncResponseDataSyncCatalogsResponse as AdCPAsyncResponseDataSyncCatalogsResponse
from .core import AdCPAsyncResponseDataSyncCreativesResponse as AdCPAsyncResponseDataSyncCreativesResponse
from .core import AdCPAsyncResponseDataUpdateMediaBuyResponse as AdCPAsyncResponseDataUpdateMediaBuyResponse
from .core import AdCPAudienceSync as AdCPAudienceSync
from .core import AdCPFormatShapeVocabularyRegistry as AdCPFormatShapeVocabularyRegistry
from .core import AdcpMajorVersion as AdcpMajorVersion
from .core import AdcpVersion as AdcpVersion
from .core import AdCPVersionEnvelope as AdCPVersionEnvelope
from .core import AdInventoryConfiguration as AdInventoryConfiguration
from .core import AgentDeclarations as AgentDeclarations
from .core import AgentDeclarationsWebhookSigningAlgorithmsItem as AgentDeclarationsWebhookSigningAlgorithmsItem
from .core import AgentEncryptionKey as AgentEncryptionKey
from .core import AgenticAdvertisingOrgVerificationTokenClaims as AgenticAdvertisingOrgVerificationTokenClaims
from .core import AgenticAdvertisingOrgVerificationTokenClaimsRole as AgenticAdvertisingOrgVerificationTokenClaimsRole
from .core import (
    AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenMode as AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenMode,
)
from .core import AgentNotificationConfig as AgentNotificationConfig
from .core import AgentNotificationConfigState as AgentNotificationConfigState
from .core import AgentNotificationConfigStateAuthentication as AgentNotificationConfigStateAuthentication
from .core import AgentPlacementFormatDeclaration as AgentPlacementFormatDeclaration
from .core import AgentReportingDestination as AgentReportingDestination
from .core import AgentReportingDestinationState as AgentReportingDestinationState
from .core import AgentReportingDestinationStateSetup as AgentReportingDestinationStateSetup
from .core import AgentReportingDestinationStateSetupAction as AgentReportingDestinationStateSetupAction
from .core import AgentSigningKey as AgentSigningKey
from .core import AgentWebhookChallenge as AgentWebhookChallenge
from .core import AgentWebhookChallengeDeliveryAuth as AgentWebhookChallengeDeliveryAuth
from .core import AgentWebhookChallengeDeliveryAuthMode as AgentWebhookChallengeDeliveryAuthMode
from .core import AgentWebhookChallengeEventTypesItem as AgentWebhookChallengeEventTypesItem
from .core import AppItem as AppItem
from .core import AppItemPlatform as AppItemPlatform
from .core import ApplicablePackageID as ApplicablePackageID
from .core import AppliesTo as AppliesTo
from .core import AppliesToAccount as AppliesToAccount
from .core import AppliesToPublic as AppliesToPublic
from .core import AssetRequirements as AssetRequirements
from .core import AssetRequirementsAudio as AssetRequirementsAudio
from .core import AssetRequirementsCSS as AssetRequirementsCSS
from .core import AssetRequirementsDAAST as AssetRequirementsDAAST
from .core import AssetRequirementsHTML as AssetRequirementsHTML
from .core import AssetRequirementsImage as AssetRequirementsImage
from .core import AssetRequirementsJavaScript as AssetRequirementsJavaScript
from .core import AssetRequirementsMarkdown as AssetRequirementsMarkdown
from .core import AssetRequirementsText as AssetRequirementsText
from .core import AssetRequirementsURL as AssetRequirementsURL
from .core import AssetRequirementsVAST as AssetRequirementsVAST
from .core import AssetRequirementsVideo as AssetRequirementsVideo
from .core import AssetRequirementsWebhook as AssetRequirementsWebhook
from .core import AssetsItemIndividual as AssetsItemIndividual
from .core import AssetVariant as AssetVariant
from .core import AssetVariantAudio as AssetVariantAudio
from .core import AssetVariantBrief as AssetVariantBrief
from .core import AssetVariantCard as AssetVariantCard
from .core import AssetVariantCatalog as AssetVariantCatalog
from .core import AssetVariantCss as AssetVariantCss
from .core import AssetVariantDaast as AssetVariantDaast
from .core import AssetVariantDaastTracker as AssetVariantDaastTracker
from .core import AssetVariantDisplayTag as AssetVariantDisplayTag
from .core import AssetVariantHtml as AssetVariantHtml
from .core import AssetVariantImage as AssetVariantImage
from .core import AssetVariantJavascript as AssetVariantJavascript
from .core import AssetVariantMarkdown as AssetVariantMarkdown
from .core import AssetVariantPixelTracker as AssetVariantPixelTracker
from .core import AssetVariantPublishedPost as AssetVariantPublishedPost
from .core import AssetVariantText as AssetVariantText
from .core import AssetVariantUrl as AssetVariantUrl
from .core import AssetVariantVast as AssetVariantVast
from .core import AssetVariantVastTracker as AssetVariantVastTracker
from .core import AssetVariantVideo as AssetVariantVideo
from .core import AssetVariantWebhook as AssetVariantWebhook
from .core import AssetVariantZip as AssetVariantZip
from .core import AttestationAgentIssuer as AttestationAgentIssuer
from .core import AttestationAgentSubject as AttestationAgentSubject
from .core import AttestationBrandIssuer as AttestationBrandIssuer
from .core import AttestationBrandSubject as AttestationBrandSubject
from .core import AttestationCapabilities as AttestationCapabilities
from .core import AttestationCapabilitiesAcceptedIssuersItem as AttestationCapabilitiesAcceptedIssuersItem
from .core import (
    AttestationCapabilitiesAcceptedIssuersItemResolversItem as AttestationCapabilitiesAcceptedIssuersItemResolversItem,
)
from .core import (
    AttestationCapabilitiesAcceptedIssuersItemResolversItemAuthentication as AttestationCapabilitiesAcceptedIssuersItemResolversItemAuthentication,
)
from .core import AttestationCapabilitiesAcceptedVerifiersItem as AttestationCapabilitiesAcceptedVerifiersItem
from .core import (
    AttestationCapabilitiesSupportedDeliveryMethodsItem as AttestationCapabilitiesSupportedDeliveryMethodsItem,
)
from .core import AttestationCredentialUriLocator as AttestationCredentialUriLocator
from .core import AttestationEvaluation as AttestationEvaluation
from .core import AttestationEvaluationActionBinding as AttestationEvaluationActionBinding
from .core import AttestationEvaluationOutcome as AttestationEvaluationOutcome
from .core import AttestationIssuer as AttestationIssuer
from .core import AttestationIssuerCredentialIdLocator as AttestationIssuerCredentialIdLocator
from .core import AttestationOriginIssuer as AttestationOriginIssuer
from .core import AttestationReference as AttestationReference
from .core import AttestationReferenceEmbeddedCredential as AttestationReferenceEmbeddedCredential
from .core import AttestationReferenceValidityHint as AttestationReferenceValidityHint
from .core import AttestationReferenceVerifyAgent as AttestationReferenceVerifyAgent
from .core import AttestationResourceSubject as AttestationResourceSubject
from .core import AttestationSubject as AttestationSubject
from .core import AttributionWindow as AttributionWindow
from .core import AttributionWindowPostClick as AttributionWindowPostClick
from .core import AttributionWindowPostView as AttributionWindowPostView
from .core import AudienceActivationMethod as AudienceActivationMethod
from .core import AudienceActivationMethodFileTransfer as AudienceActivationMethodFileTransfer
from .core import AudienceActivationMethodsItemCleanRoom as AudienceActivationMethodsItemCleanRoom
from .core import AudienceActivationMethodsItemDatasetQuery as AudienceActivationMethodsItemDatasetQuery
from .core import AudienceActivationMethodsItemFileTransfer as AudienceActivationMethodsItemFileTransfer
from .core import AudienceActivationMethodsItemPlatformDistribution as AudienceActivationMethodsItemPlatformDistribution
from .core import AudienceActivationMethodsItemTmpIdentityMatch as AudienceActivationMethodsItemTmpIdentityMatch
from .core import AudienceCharacteristic as AudienceCharacteristic
from .core import AudienceCharacteristicRange as AudienceCharacteristicRange
from .core import AudienceCharacteristicTaxonomy as AudienceCharacteristicTaxonomy
from .core import AudienceEvidence as AudienceEvidence
from .core import AudienceEvidenceAttestationRefsItem as AudienceEvidenceAttestationRefsItem
from .core import AudienceEvidenceAttestationRefsItemSubject as AudienceEvidenceAttestationRefsItemSubject
from .core import AudienceEvidenceBaseline as AudienceEvidenceBaseline
from .core import AudienceEvidenceEvidenceType as AudienceEvidenceEvidenceType
from .core import AudienceEvidencePin as AudienceEvidencePin
from .core import AudienceEvidenceRelationship as AudienceEvidenceRelationship
from .core import AudienceEvidenceRequirements as AudienceEvidenceRequirements
from .core import AudienceEvidenceRequirementsMaximumAge as AudienceEvidenceRequirementsMaximumAge
from .core import AudienceEvidenceSelection as AudienceEvidenceSelection
from .core import (
    AudienceEvidenceSelectionAttestationEvaluationsItem as AudienceEvidenceSelectionAttestationEvaluationsItem,
)
from .core import (
    AudienceEvidenceSelectionAttestationEvaluationsItemEvaluation as AudienceEvidenceSelectionAttestationEvaluationsItemEvaluation,
)
from .core import (
    AudienceEvidenceSelectionAttestationEvaluationsItemEvaluationActionBinding as AudienceEvidenceSelectionAttestationEvaluationsItemEvaluationActionBinding,
)
from .core import AudienceEvidenceSelectionDecisionUse as AudienceEvidenceSelectionDecisionUse
from .core import AudienceEvidenceUnit as AudienceEvidenceUnit
from .core import AudienceExclude as AudienceExclude
from .core import AudienceForecastDimension as AudienceForecastDimension
from .core import AudienceInclude as AudienceInclude
from .core import AudienceMember as AudienceMember
from .core import AudienceMemberUidsItem as AudienceMemberUidsItem
from .core import AudienceSelector as AudienceSelector
from .core import AudienceSelectorDescription as AudienceSelectorDescription
from .core import AudienceSelectorSignalBinary as AudienceSelectorSignalBinary
from .core import AudienceSelectorSignalCategorical as AudienceSelectorSignalCategorical
from .core import AudienceSelectorSignalNumeric as AudienceSelectorSignalNumeric
from .core import AudioAsset as AudioAsset
from .core import AudioAssetRequirements as AudioAssetRequirements
from .core import AudioAssetRequirementsFormatsItem as AudioAssetRequirementsFormatsItem
from .core import AuthorizedAgentBaseFields as AuthorizedAgentBaseFields
from .core import AxeExcludeSegment as AxeExcludeSegment
from .core import AxeIncludeSegment as AxeIncludeSegment
from .core import BiddingPolicy as BiddingPolicy
from .core import BiddingPolicyCapability as BiddingPolicyCapability
from .core import BiddingPolicyCapabilityMaxBidWithCostPer as BiddingPolicyCapabilityMaxBidWithCostPer
from .core import BiddingPolicyCapabilityMaxBidWithRoas as BiddingPolicyCapabilityMaxBidWithRoas
from .core import BiddingPolicyCapabilityPolicyProfile as BiddingPolicyCapabilityPolicyProfile
from .core import BiddingPolicyCapabilityPolicyProfileModesItem as BiddingPolicyCapabilityPolicyProfileModesItem
from .core import BiddingPolicyCapabilityScopeCapability as BiddingPolicyCapabilityScopeCapability
from .core import BiddingPolicyCostPer as BiddingPolicyCostPer
from .core import BiddingPolicyRoas as BiddingPolicyRoas
from .core import BiddingPolicyRoasStrength as BiddingPolicyRoasStrength
from .core import BleedBottomLeftRightTop as BleedBottomLeftRightTop
from .core import BleedUniform as BleedUniform
from .core import BlockedImpacts as BlockedImpacts
from .core import BrandID as BrandID
from .core import BrandKey as BrandKey
from .core import BrandReference as BrandReference
from .core import BrandReferenceBrandKitOverride as BrandReferenceBrandKitOverride
from .core import BrandReferenceBrandKitOverrideColors as BrandReferenceBrandKitOverrideColors
from .core import BrandReferenceDataSubjectContestation as BrandReferenceDataSubjectContestation
from .core import BrandResponseAuthorizationResult as BrandResponseAuthorizationResult
from .core import BrandResponseAuthorizationResultReason as BrandResponseAuthorizationResultReason
from .core import BrandResponseAuthorizationResultTrust as BrandResponseAuthorizationResultTrust
from .core import BrandResponseAuthorizationResultTrusted as BrandResponseAuthorizationResultTrusted
from .core import BrandResponseAuthorizationResultUntrusted as BrandResponseAuthorizationResultUntrusted
from .core import BriefAsset as BriefAsset
from .core import Browser as Browser
from .core import BrowserExclude as BrowserExclude
from .core import BrowserRequirement as BrowserRequirement
from .core import BrowserRequirementFamilies as BrowserRequirementFamilies
from .core import BrowserSupport as BrowserSupport
from .core import BrowserSupportFamilies as BrowserSupportFamilies
from .core import BudgetAllocation as BudgetAllocation
from .core import BudgetAllocationFixed as BudgetAllocationFixed
from .core import BudgetAllocationSellerOptimized as BudgetAllocationSellerOptimized
from .core import BudgetRange as BudgetRange
from .core import BuildCreativeAsyncInputRequired as BuildCreativeAsyncInputRequired
from .core import BuildCreativeAsyncSubmitted as BuildCreativeAsyncSubmitted
from .core import BuildCreativeAsyncWorking as BuildCreativeAsyncWorking
from .core import BusinessEntity as BusinessEntity
from .core import BusinessEntityAddress as BusinessEntityAddress
from .core import BusinessEntityBank as BusinessEntityBank
from .core import BusinessEntityContactsItem as BusinessEntityContactsItem
from .core import BusinessEntityContactsItemRole as BusinessEntityContactsItemRole
from .core import CancellationPolicy as CancellationPolicy
from .core import CancellationPolicyCancellationFee as CancellationPolicyCancellationFee
from .core import CancellationPolicyCancellationFeeType as CancellationPolicyCancellationFeeType
from .core import CanonicalAccountReference as CanonicalAccountReference
from .core import CanonicalAccountReferenceAccountId as CanonicalAccountReferenceAccountId
from .core import CanonicalAccountReferenceBrandOperator as CanonicalAccountReferenceBrandOperator
from .core import CanonicalAudienceEvidence as CanonicalAudienceEvidence
from .core import CanonicalAudienceEvidenceSelection as CanonicalAudienceEvidenceSelection
from .core import CanonicalBudgetAllocation as CanonicalBudgetAllocation
from .core import CanonicalBudgetAllocationFixed as CanonicalBudgetAllocationFixed
from .core import CanonicalBudgetAllocationSellerOptimized as CanonicalBudgetAllocationSellerOptimized
from .core import CanonicalDeliveryForecast as CanonicalDeliveryForecast
from .core import CanonicalForecastPoint as CanonicalForecastPoint
from .core import CanonicalForecastPointMetrics as CanonicalForecastPointMetrics
from .core import CanonicalForecastPointViewability as CanonicalForecastPointViewability
from .core import CanonicalForecastVendorMetricValue as CanonicalForecastVendorMetricValue
from .core import CanonicalFormatKind as CanonicalFormatKind
from .core import CanonicalFormatManifest as CanonicalFormatManifest
from .core import CanonicalFormatOption as CanonicalFormatOption
from .core import CanonicalFormatOptionFormatKind as CanonicalFormatOptionFormatKind
from .core import CanonicalMeasurementTerms as CanonicalMeasurementTerms
from .core import CanonicalMeasurementTermsBillingMeasurement as CanonicalMeasurementTermsBillingMeasurement
from .core import CanonicalMeasurementTermsMakegoodPolicy as CanonicalMeasurementTermsMakegoodPolicy
from .core import CanonicalMediaBuyAction as CanonicalMediaBuyAction
from .core import CanonicalMediaBuyActionControlMediaBuy as CanonicalMediaBuyActionControlMediaBuy
from .core import CanonicalMediaBuyActionControlMediaBuyAction as CanonicalMediaBuyActionControlMediaBuyAction
from .core import CanonicalMediaBuyActionFields as CanonicalMediaBuyActionFields
from .core import CanonicalMediaBuyActionRefineProposals as CanonicalMediaBuyActionRefineProposals
from .core import CanonicalMediaBuyActionRefineProposalsAction as CanonicalMediaBuyActionRefineProposalsAction
from .core import CanonicalMediaBuyActionSyncCreatives as CanonicalMediaBuyActionSyncCreatives
from .core import CanonicalMediaBuyActionSyncCreativesAction as CanonicalMediaBuyActionSyncCreativesAction
from .core import CanonicalMediaBuyFeatures as CanonicalMediaBuyFeatures
from .core import CanonicalMetricQualifier as CanonicalMetricQualifier
from .core import CanonicalOptimizationGoal as CanonicalOptimizationGoal
from .core import CanonicalOptimizationGoalEvent as CanonicalOptimizationGoalEvent
from .core import CanonicalOptimizationGoalEventEventSourcesItem as CanonicalOptimizationGoalEventEventSourcesItem
from .core import CanonicalOptimizationGoalEventTarget as CanonicalOptimizationGoalEventTarget
from .core import CanonicalOptimizationGoalMetric as CanonicalOptimizationGoalMetric
from .core import CanonicalOptimizationGoalMetricMetric as CanonicalOptimizationGoalMetricMetric
from .core import CanonicalOptimizationGoalMetricTargetFrequency as CanonicalOptimizationGoalMetricTargetFrequency
from .core import CanonicalOptimizationGoalVendorMetric as CanonicalOptimizationGoalVendorMetric
from .core import CanonicalOptimizationGoalVendorMetricTarget as CanonicalOptimizationGoalVendorMetricTarget
from .core import CanonicalPerformanceStandard as CanonicalPerformanceStandard
from .core import CanonicalPricingOption as CanonicalPricingOption
from .core import CanonicalProduct as CanonicalProduct
from .core import CanonicalProductAction as CanonicalProductAction
from .core import CanonicalProductCatalogMatch as CanonicalProductCatalogMatch
from .core import CanonicalProductPlacement as CanonicalProductPlacement
from .core import (
    CanonicalProductPlacementCanonicalDoohPlacementAttributes as CanonicalProductPlacementCanonicalDoohPlacementAttributes,
)
from .core import (
    CanonicalProductPlacementCanonicalDoohScreenResolution as CanonicalProductPlacementCanonicalDoohScreenResolution,
)
from .core import CanonicalProductPlacementPublisherRef as CanonicalProductPlacementPublisherRef
from .core import CanonicalProductPlacementSellerInline as CanonicalProductPlacementSellerInline
from .core import CanonicalProjectionReference as CanonicalProjectionReference
from .core import CanonicalProjectionSlotOverride as CanonicalProjectionSlotOverride
from .core import CanonicalProposal as CanonicalProposal
from .core import CanonicalProposalForecast as CanonicalProposalForecast
from .core import CanonicalProposalProposalKind as CanonicalProposalProposalKind
from .core import CanonicalProposalTotalBudgetGuidance as CanonicalProposalTotalBudgetGuidance
from .core import CanonicalReportingCapabilities as CanonicalReportingCapabilities
from .core import CanonicalReportingCapabilitiesVendorMetricsItem as CanonicalReportingCapabilitiesVendorMetricsItem
from .core import CanonicalReportingCommitment as CanonicalReportingCommitment
from .core import CanonicalReportingCommitmentStandard as CanonicalReportingCommitmentStandard
from .core import CanonicalReportingCommitmentVendor as CanonicalReportingCommitmentVendor
from .core import CanvasConstraint as CanvasConstraint
from .core import CanvasConstraintConstraint as CanvasConstraintConstraint
from .core import CanvasConstraintRegion as CanvasConstraintRegion
from .core import CanvasConstraintRegionUnit as CanvasConstraintRegionUnit
from .core import CapabilitiesChangedWebhook as CapabilitiesChangedWebhook
from .core import CapabilitiesChangedWebhookReason as CapabilitiesChangedWebhookReason
from .core import CardAsset as CardAsset
from .core import Catalog as Catalog
from .core import CatalogAsset as CatalogAsset
from .core import CatalogExecutionRequirement as CatalogExecutionRequirement
from .core import CatalogFieldBinding as CatalogFieldBinding
from .core import CatalogFieldBindingAssetPool as CatalogFieldBindingAssetPool
from .core import CatalogFieldBindingAssetPoolBinding as CatalogFieldBindingAssetPoolBinding
from .core import CatalogFieldBindingCatalogGroup as CatalogFieldBindingCatalogGroup
from .core import CatalogFieldBindingScalar as CatalogFieldBindingScalar
from .core import CatalogFieldBindingScalarBinding as CatalogFieldBindingScalarBinding
from .core import CatalogFieldMapping as CatalogFieldMapping
from .core import CatalogFieldMappingTransform as CatalogFieldMappingTransform
from .core import CatalogItemAvailabilityError as CatalogItemAvailabilityError
from .core import CatalogItemAvailabilityReference as CatalogItemAvailabilityReference
from .core import CatalogItemAvailabilityState as CatalogItemAvailabilityState
from .core import CatalogItemAvailabilityStateAvailability as CatalogItemAvailabilityStateAvailability
from .core import CatalogItemAvailabilityStateStatus as CatalogItemAvailabilityStateStatus
from .core import CatalogItemAvailabilityUpdate as CatalogItemAvailabilityUpdate
from .core import CatalogItemAvailabilityUpdateReason as CatalogItemAvailabilityUpdateReason
from .core import CatalogItemAvailabilityUpdateResult as CatalogItemAvailabilityUpdateResult
from .core import CatalogItemAvailabilityUpdateResultAction as CatalogItemAvailabilityUpdateResultAction
from .core import CatalogItemAvailabilityUpdateResultStatus as CatalogItemAvailabilityUpdateResultStatus
from .core import CatalogItemDeliveryMetrics as CatalogItemDeliveryMetrics
from .core import CatalogItemReferenceNotFoundError as CatalogItemReferenceNotFoundError
from .core import CatalogRequirements as CatalogRequirements
from .core import CatalogSelection as CatalogSelection
from .core import Catchment as Catchment
from .core import CatchmentGeometry as CatchmentGeometry
from .core import CatchmentRadius as CatchmentRadius
from .core import CatchmentTransportModeTravelTime as CatchmentTransportModeTravelTime
from .core import Category as Category
from .core import ChangedFields as ChangedFields
from .core import CleanRoom as CleanRoom
from .core import Collection as Collection
from .core import CollectionDeliveryMetrics as CollectionDeliveryMetrics
from .core import CollectionDistribution as CollectionDistribution
from .core import CollectionDistributionIdentifiersItem as CollectionDistributionIdentifiersItem
from .core import CollectionListApplication as CollectionListApplication
from .core import CollectionListApplicationEffect as CollectionListApplicationEffect
from .core import CollectionListApplicationSummary as CollectionListApplicationSummary
from .core import CollectionListReference as CollectionListReference
from .core import CollectionPropertyDeliveryMetrics as CollectionPropertyDeliveryMetrics
from .core import CollectionReference as CollectionReference
from .core import CollectionRelatedCollectionsItem as CollectionRelatedCollectionsItem
from .core import CollectionSelection as CollectionSelection
from .core import CollectionSelector as CollectionSelector
from .core import Color as Color
from .core import CommittedMetric as CommittedMetric
from .core import CommittedMetricStandard as CommittedMetricStandard
from .core import CommittedMetricVendor as CommittedMetricVendor
from .core import CommittedMetricVendorQualifier as CommittedMetricVendorQualifier
from .core import CompactTaskInputRequired as CompactTaskInputRequired
from .core import CompactTaskSubmitted as CompactTaskSubmitted
from .core import CompactTaskWorking as CompactTaskWorking
from .core import ContentRating as ContentRating
from .core import ContextObject as ContextObject
from .core import ControlMediaBuyResponseCompleted as ControlMediaBuyResponseCompleted
from .core import ControlMediaBuyResponseFailed as ControlMediaBuyResponseFailed
from .core import ControlMediaBuyResponseSubmitted as ControlMediaBuyResponseSubmitted
from .core import CoordinatedPlacementsFormatDeclaration as CoordinatedPlacementsFormatDeclaration
from .core import Countries as Countries
from .core import CountryCode as CountryCode
from .core import CountrySupport as CountrySupport
from .core import CountrySupportMaxValuesPerPackage as CountrySupportMaxValuesPerPackage
from .core import CpmPricing as CpmPricing
from .core import CreateMediaBuyAsyncInputRequired as CreateMediaBuyAsyncInputRequired
from .core import CreateMediaBuyAsyncSubmitted as CreateMediaBuyAsyncSubmitted
from .core import CreateMediaBuyAsyncWorking as CreateMediaBuyAsyncWorking
from .core import CreativeAsset as CreativeAsset
from .core import CreativeAssets as CreativeAssets
from .core import CreativeAssignment as CreativeAssignment
from .core import CreativeAssignmentRotationMode as CreativeAssignmentRotationMode
from .core import CreativeBrief as CreativeBrief
from .core import CreativeBriefCompliance as CreativeBriefCompliance
from .core import CreativeBriefComplianceRequiredDisclosuresItem as CreativeBriefComplianceRequiredDisclosuresItem
from .core import CreativeBriefMessaging as CreativeBriefMessaging
from .core import CreativeBriefObjective as CreativeBriefObjective
from .core import CreativeConsumption as CreativeConsumption
from .core import CreativeDeliveryMetrics as CreativeDeliveryMetrics
from .core import CreativeFilters as CreativeFilters
from .core import CreativeItem as CreativeItem
from .core import CreativeItemMedia as CreativeItemMedia
from .core import CreativeItemText as CreativeItemText
from .core import CreativeLocalePolicy as CreativeLocalePolicy
from .core import CreativeLocalization as CreativeLocalization
from .core import CreativeLocalizationReadback as CreativeLocalizationReadback
from .core import CreativeLocalizationReadbackLocaleFallbacksItem as CreativeLocalizationReadbackLocaleFallbacksItem
from .core import CreativeLocalizationReadbackUnmatchedLocaleAction as CreativeLocalizationReadbackUnmatchedLocaleAction
from .core import CreativeLocalizationSource as CreativeLocalizationSource
from .core import CreativeLocalizationTargetVariantsItem as CreativeLocalizationTargetVariantsItem
from .core import CreativeManifest as CreativeManifest
from .core import CreativeOperationFormatDeclaration as CreativeOperationFormatDeclaration
from .core import CreativePolicy as CreativePolicy
from .core import CreativePolicyAcceptedVerifiersItem as CreativePolicyAcceptedVerifiersItem
from .core import CreativePolicyProvenanceRequirements as CreativePolicyProvenanceRequirements
from .core import CreativeRepresentation as CreativeRepresentation
from .core import CreativeRepresentationFormatId as CreativeRepresentationFormatId
from .core import CreativeRepresentationFormatKind as CreativeRepresentationFormatKind
from .core import CreativeRepresentationSet as CreativeRepresentationSet
from .core import CreativeRepresentationSource as CreativeRepresentationSource
from .core import CreativeRevisionID as CreativeRevisionID
from .core import CreativeVariable as CreativeVariable
from .core import CreativeVariableVariableType as CreativeVariableVariableType
from .core import CreativeVariant as CreativeVariant
from .core import CreativeVariantGenerationContext as CreativeVariantGenerationContext
from .core import CreativeVariantGenerationContextArtifact as CreativeVariantGenerationContextArtifact
from .core import CSSAsset as CSSAsset
from .core import CSSAssetRequirements as CSSAssetRequirements
from .core import CurrencyCode as CurrencyCode
from .core import CustomFormatDeclaration as CustomFormatDeclaration
from .core import CustomPricing as CustomPricing
from .core import CustomPricingMetadata as CustomPricingMetadata
from .core import DAASTAsset as DAASTAsset
from .core import DAASTAssetInline as DAASTAssetInline
from .core import DAASTAssetInlineMacroDeclarationsItem as DAASTAssetInlineMacroDeclarationsItem
from .core import DAASTAssetInlineMacroDeclarationsItemLocation as DAASTAssetInlineMacroDeclarationsItemLocation
from .core import DAASTAssetRequirements as DAASTAssetRequirements
from .core import DAASTAssetUrl as DAASTAssetUrl
from .core import DAASTAudioFormatDeclaration as DAASTAudioFormatDeclaration
from .core import DaastOffset as DaastOffset
from .core import DAASTTrackerAsset as DAASTTrackerAsset
from .core import DAASTTrackerConstraints as DAASTTrackerConstraints
from .core import DAASTTrackerConstraintsDaastEvent as DAASTTrackerConstraintsDaastEvent
from .core import DAASTTrackerConstraintsDaastTarget as DAASTTrackerConstraintsDaastTarget
from .core import DaastVersions as DaastVersions
from .core import DataProviderSignalSelector as DataProviderSignalSelector
from .core import DataProviderSignalSelectorAll as DataProviderSignalSelectorAll
from .core import DataProviderSignalSelectorById as DataProviderSignalSelectorById
from .core import DataProviderSignalSelectorByTag as DataProviderSignalSelectorByTag
from .core import Dataset as Dataset
from .core import DatasetQuery as DatasetQuery
from .core import DatasetQueryConsumerIdentitiesItem as DatasetQueryConsumerIdentitiesItem
from .core import DatasetShare as DatasetShare
from .core import DatasetShareRecipient as DatasetShareRecipient
from .core import DateRange as DateRange
from .core import DatetimeRange as DatetimeRange
from .core import DaypartRequirement as DaypartRequirement
from .core import DaypartRequirementTimezoneModes as DaypartRequirementTimezoneModes
from .core import DaypartSupport as DaypartSupport
from .core import DaypartSupportTimezoneModes as DaypartSupportTimezoneModes
from .core import DaypartTarget as DaypartTarget
from .core import DaypartTargets as DaypartTargets
from .core import DeadlinePolicy as DeadlinePolicy
from .core import DeadlinePolicyMaterialStagesItem as DeadlinePolicyMaterialStagesItem
from .core import DecimalReportingControlTotal as DecimalReportingControlTotal
from .core import DeliveryBreakdownControls as DeliveryBreakdownControls
from .core import DeliveryForecast as DeliveryForecast
from .core import DeliveryMetricAggregate as DeliveryMetricAggregate
from .core import DeliveryMetricAggregateStandard as DeliveryMetricAggregateStandard
from .core import DeliveryMetricAggregateVendor as DeliveryMetricAggregateVendor
from .core import DeliveryMetrics as DeliveryMetrics
from .core import DeliveryMetricsByActionSourceItem as DeliveryMetricsByActionSourceItem
from .core import DeliveryMetricsByEventTypeItem as DeliveryMetricsByEventTypeItem
from .core import DeliveryMetricsDoohMetrics as DeliveryMetricsDoohMetrics
from .core import DeliveryMetricsDoohMetricsVenueBreakdownItem as DeliveryMetricsDoohMetricsVenueBreakdownItem
from .core import DeliveryMetricsOohMetrics as DeliveryMetricsOohMetrics
from .core import DeliveryMetricsOohMetricsEstimationBasis as DeliveryMetricsOohMetricsEstimationBasis
from .core import DeliveryMetricsOohMetricsPanelsItem as DeliveryMetricsOohMetricsPanelsItem
from .core import (
    DeliveryMetricsOohMetricsPanelsItemIdentifiersItem as DeliveryMetricsOohMetricsPanelsItemIdentifiersItem,
)
from .core import (
    DeliveryMetricsOohMetricsPanelsItemIdentifiersItemIdType as DeliveryMetricsOohMetricsPanelsItemIdentifiersItemIdType,
)
from .core import DeliveryMetricsOohMetricsPostingsItem as DeliveryMetricsOohMetricsPostingsItem
from .core import DeliveryMetricsOohMetricsPostingsItemEventType as DeliveryMetricsOohMetricsPostingsItemEventType
from .core import DeliveryMetricsQuartileData as DeliveryMetricsQuartileData
from .core import DeliveryMetricsReachWindow as DeliveryMetricsReachWindow
from .core import DeliveryMetricsReachWindowKind as DeliveryMetricsReachWindowKind
from .core import DeliveryMetricsReachWindowPeriod as DeliveryMetricsReachWindowPeriod
from .core import DeliveryMetricsTimeBasedViewsItem as DeliveryMetricsTimeBasedViewsItem
from .core import DeliveryMetricsViewability as DeliveryMetricsViewability
from .core import (
    DeliveryMetricsViewabilityViewedSecondsHistogramItem as DeliveryMetricsViewabilityViewedSecondsHistogramItem,
)
from .core import (
    DeliveryMetricsViewabilityViewedSecondsPercentiles as DeliveryMetricsViewabilityViewedSecondsPercentiles,
)
from .core import DeliveryProvider as DeliveryProvider
from .core import DeliveryRecipient as DeliveryRecipient
from .core import DemographicAgeRange as DemographicAgeRange
from .core import DemographicPredicate as DemographicPredicate
from .core import DemographicReportingCapability as DemographicReportingCapability
from .core import DemographicReportingCapabilityAge as DemographicReportingCapabilityAge
from .core import DemographicReportingCapabilityAgeIntervalsItem as DemographicReportingCapabilityAgeIntervalsItem
from .core import (
    DemographicReportingCapabilityAgeReportingModesItem as DemographicReportingCapabilityAgeReportingModesItem,
)
from .core import DemographicTargetingCapability as DemographicTargetingCapability
from .core import DemographicTargetingCapabilityAge as DemographicTargetingCapabilityAge
from .core import (
    DemographicTargetingCapabilityAgeExecutionModesItem as DemographicTargetingCapabilityAgeExecutionModesItem,
)
from .core import DemographicTargetingCapabilityAgeIntervalsItem as DemographicTargetingCapabilityAgeIntervalsItem
from .core import DemographicTargetingCapabilityAgeUnknownHandling as DemographicTargetingCapabilityAgeUnknownHandling
from .core import DemographicTargetingIntent as DemographicTargetingIntent
from .core import DemographicTargetingIntentAge as DemographicTargetingIntentAge
from .core import DemographicTargetingResolution as DemographicTargetingResolution
from .core import Deployment as Deployment
from .core import DeploymentAgent as DeploymentAgent
from .core import DeploymentPlatform as DeploymentPlatform
from .core import Destination as Destination
from .core import DestinationAgent as DestinationAgent
from .core import DestinationItem as DestinationItem
from .core import DestinationItemDestinationType as DestinationItemDestinationType
from .core import DestinationItemLocation as DestinationItemLocation
from .core import DestinationPlatform as DestinationPlatform
from .core import DevicePlatformExclude as DevicePlatformExclude
from .core import DevicePlatformForecastDimension as DevicePlatformForecastDimension
from .core import DeviceTypeExclude as DeviceTypeExclude
from .core import DeviceTypeForecastDimension as DeviceTypeForecastDimension
from .core import DiagnosticIssue as DiagnosticIssue
from .core import DiagnosticIssueSeverity as DiagnosticIssueSeverity
from .core import DisplayTagAsset as DisplayTagAsset
from .core import DisplayTagFormatDeclaration as DisplayTagFormatDeclaration
from .core import DomainName as DomainName
from .core import DownstreamConnectionExecutionRequirement as DownstreamConnectionExecutionRequirement
from .core import (
    DownstreamConnectionExecutionRequirementConnection as DownstreamConnectionExecutionRequirementConnection,
)
from .core import DownstreamConnectionRequirement as DownstreamConnectionRequirement
from .core import DownstreamConnectionRequirementConnectionType as DownstreamConnectionRequirementConnectionType
from .core import DownstreamConnectionRequirementResourceRef as DownstreamConnectionRequirementResourceRef
from .core import DownstreamConnectionRequirementScope as DownstreamConnectionRequirementScope
from .core import DownstreamConnectionRequirementStatus as DownstreamConnectionRequirementStatus
from .core import Duration as Duration
from .core import EducationItem as EducationItem
from .core import EducationItemDegreeType as EducationItemDegreeType
from .core import EducationItemLevel as EducationItemLevel
from .core import EducationItemModality as EducationItemModality
from .core import Error as Error
from .core import ErrorBuyerReason as ErrorBuyerReason
from .core import ErrorIssuesItem as ErrorIssuesItem
from .core import ErrorIssuesItemDiscriminatorItem as ErrorIssuesItemDiscriminatorItem
from .core import ErrorRecovery as ErrorRecovery
from .core import ErrorSource as ErrorSource
from .core import EvaluatorSpec as EvaluatorSpec
from .core import EvaluatorSpecAgentUrl as EvaluatorSpecAgentUrl
from .core import EvaluatorSpecEvalBudget as EvaluatorSpecEvalBudget
from .core import EvaluatorSpecEvaluatorId as EvaluatorSpecEvaluatorId
from .core import EvaluatorSpecExemplars as EvaluatorSpecExemplars
from .core import EvaluatorSpecRankByItem as EvaluatorSpecRankByItem
from .core import EvaluatorSpecRankByItemDirection as EvaluatorSpecRankByItemDirection
from .core import Event as Event
from .core import EventCustomData as EventCustomData
from .core import EventCustomDataContentsItem as EventCustomDataContentsItem
from .core import EventSourceExecutionRequirement as EventSourceExecutionRequirement
from .core import EventSourceHealth as EventSourceHealth
from .core import EventSourceHealthDetail as EventSourceHealthDetail
from .core import EventSurface as EventSurface
from .core import EventSurfaceCategory as EventSurfaceCategory
from .core import ExecutionContinuousBounds as ExecutionContinuousBounds
from .core import ExecutionEnumeratedIntervals as ExecutionEnumeratedIntervals
from .core import ExecutionSignals as ExecutionSignals
from .core import ExperimentalFeatureID as ExperimentalFeatureID
from .core import ExtensionObject as ExtensionObject
from .core import FeatureRequirement as FeatureRequirement
from .core import FeatureRequirementIfNotCovered as FeatureRequirementIfNotCovered
from .core import FileTransferDestination as FileTransferDestination
from .core import FileTransferDirectionsItem as FileTransferDirectionsItem
from .core import FileTransferFormat as FileTransferFormat
from .core import FinalityPoliciesItemContractualCutoff as FinalityPoliciesItemContractualCutoff
from .core import FinalityPoliciesItemSourceFinal as FinalityPoliciesItemSourceFinal
from .core import FinalityPoliciesItemStabilized as FinalityPoliciesItemStabilized
from .core import FlatFeePricing as FlatFeePricing
from .core import FlatFeePricingPeriod as FlatFeePricingPeriod
from .core import FlightItem as FlightItem
from .core import FlightItemDestination as FlightItemDestination
from .core import FlightItemOrigin as FlightItemOrigin
from .core import ForecastPoint as ForecastPoint
from .core import ForecastPointDimensions as ForecastPointDimensions
from .core import ForecastPointMetrics as ForecastPointMetrics
from .core import ForecastPointMetricsCoverageRate as ForecastPointMetricsCoverageRate
from .core import ForecastPointViewability as ForecastPointViewability
from .core import ForecastPointViewabilityViewableRate as ForecastPointViewabilityViewableRate
from .core import ForecastRange as ForecastRange
from .core import ForecastRateRange as ForecastRateRange
from .core import ForecastVendorMetricValue as ForecastVendorMetricValue
from .core import Format as Format
from .core import FormatAccessibility as FormatAccessibility
from .core import FormatBaseGroupAsset as FormatBaseGroupAsset
from .core import FormatBaseIndividualAsset as FormatBaseIndividualAsset
from .core import FormatDisclosureCapabilitiesItem as FormatDisclosureCapabilitiesItem
from .core import FormatFormatCard as FormatFormatCard
from .core import FormatFormatCardDetailed as FormatFormatCardDetailed
from .core import FormatOptionReference as FormatOptionReference
from .core import FormatOptionsItemFormatOptionId as FormatOptionsItemFormatOptionId
from .core import FormatReferenceStructuredObject as FormatReferenceStructuredObject
from .core import FormatRendersItem as FormatRendersItem
from .core import FormatRendersItemDimensions as FormatRendersItemDimensions
from .core import FormatRendersItemDimensionsResponsive as FormatRendersItemDimensionsResponsive
from .core import FrequencyCap as FrequencyCap
from .core import FrequencyCapConstraints as FrequencyCapConstraints
from .core import FrequencyCapDurationUnit as FrequencyCapDurationUnit
from .core import FrequencyCapImpressionConstraints as FrequencyCapImpressionConstraints
from .core import FrequencyCapImpressionConstraintsAllowedValues as FrequencyCapImpressionConstraintsAllowedValues
from .core import FrequencyCapImpressionConstraintsMaximumMinimum as FrequencyCapImpressionConstraintsMaximumMinimum
from .core import FrequencyCapIntervalConstraints as FrequencyCapIntervalConstraints
from .core import FrequencyCapIntervalConstraintsAllowedIntervals as FrequencyCapIntervalConstraintsAllowedIntervals
from .core import (
    FrequencyCapIntervalConstraintsMaximumIntervalMinimumInterval as FrequencyCapIntervalConstraintsMaximumIntervalMinimumInterval,
)
from .core import FrequencyCapRequirements as FrequencyCapRequirements
from .core import FrequencyCapSuppress as FrequencyCapSuppress
from .core import FrequencyCapWindow as FrequencyCapWindow
from .core import GenerationCredential as GenerationCredential
from .core import GeoCountries as GeoCountries
from .core import GeoCountriesExclude as GeoCountriesExclude
from .core import GeoDeliveryMetrics as GeoDeliveryMetrics
from .core import GeoForecastDimension as GeoForecastDimension
from .core import GeographicBreakdownSupport as GeographicBreakdownSupport
from .core import GeographicPlaceArea as GeographicPlaceArea
from .core import GeographicPlaceCatalogCapability as GeographicPlaceCatalogCapability
from .core import GeographicPlaceCatalogEntry as GeographicPlaceCatalogEntry
from .core import GeographicPlaceCatalogEntryStatus as GeographicPlaceCatalogEntryStatus
from .core import GeographicPlaceIdentifierSystem as GeographicPlaceIdentifierSystem
from .core import GeographicPlaceRequirement as GeographicPlaceRequirement
from .core import GeographicPlaceRequirementCatalogRequirement as GeographicPlaceRequirementCatalogRequirement
from .core import GeographicPlaceResolver as GeographicPlaceResolver
from .core import GeographicPlaceResolverAuth as GeographicPlaceResolverAuth
from .core import GeographicPlaceSystemSupport as GeographicPlaceSystemSupport
from .core import GeographicPlaceType as GeographicPlaceType
from .core import GeographicRegionRequirement as GeographicRegionRequirement
from .core import GeographicRegionSupport as GeographicRegionSupport
from .core import GeoMetro as GeoMetro
from .core import GeoMetrosExclude as GeoMetrosExclude
from .core import GeoPlaces as GeoPlaces
from .core import GeoPlacesExclude as GeoPlacesExclude
from .core import GeoPostalAreas as GeoPostalAreas
from .core import GeoPostalAreasExclude as GeoPostalAreasExclude
from .core import GeoRegions as GeoRegions
from .core import GeoRegionsExclude as GeoRegionsExclude
from .core import GetCreativeFeaturesAsyncSubmitted as GetCreativeFeaturesAsyncSubmitted
from .core import GetGeographicPlaceResolutionRequest as GetGeographicPlaceResolutionRequest
from .core import GetGeographicPlaceResolutionResponse as GetGeographicPlaceResolutionResponse
from .core import GetProductsAsyncInputRequired as GetProductsAsyncInputRequired
from .core import GetProductsAsyncSubmitted as GetProductsAsyncSubmitted
from .core import GetProductsAsyncWorking as GetProductsAsyncWorking
from .core import GetSignalsAsyncSubmitted as GetSignalsAsyncSubmitted
from .core import GetSignalsAsyncWorking as GetSignalsAsyncWorking
from .core import GroupAudioAsset as GroupAudioAsset
from .core import GroupBriefAsset as GroupBriefAsset
from .core import GroupCardAsset as GroupCardAsset
from .core import GroupCatalogAsset as GroupCatalogAsset
from .core import GroupCssAsset as GroupCssAsset
from .core import GroupDaastAsset as GroupDaastAsset
from .core import GroupDaastTrackerAsset as GroupDaastTrackerAsset
from .core import GroupDisplayTagAsset as GroupDisplayTagAsset
from .core import GroupHtmlAsset as GroupHtmlAsset
from .core import GroupImageAsset as GroupImageAsset
from .core import GroupJavaScriptAsset as GroupJavaScriptAsset
from .core import GroupMarkdownAsset as GroupMarkdownAsset
from .core import GroupPixelTrackerAsset as GroupPixelTrackerAsset
from .core import GroupPublishedPostAsset as GroupPublishedPostAsset
from .core import GroupTextAsset as GroupTextAsset
from .core import GroupUrlAsset as GroupUrlAsset
from .core import GroupVastAsset as GroupVastAsset
from .core import GroupVastTrackerAsset as GroupVastTrackerAsset
from .core import GroupVideoAsset as GroupVideoAsset
from .core import GroupWebhookAsset as GroupWebhookAsset
from .core import GroupZipAsset as GroupZipAsset
from .core import Gtins as Gtins
from .core import HostedAudioFormatDeclaration as HostedAudioFormatDeclaration
from .core import HostedVideoFormatDeclaration as HostedVideoFormatDeclaration
from .core import HotelItem as HotelItem
from .core import HotelItemAddress as HotelItemAddress
from .core import HoursValue as HoursValue
from .core import HTML5FormatDeclaration as HTML5FormatDeclaration
from .core import HTMLAsset as HTMLAsset
from .core import HTMLAssetAccessibility as HTMLAssetAccessibility
from .core import HTMLAssetRequirements as HTMLAssetRequirements
from .core import HTMLAssetRequirementsSandbox as HTMLAssetRequirementsSandbox
from .core import IANATimezoneIdentifier as IANATimezoneIdentifier
from .core import IdempotencyKey as IdempotencyKey
from .core import Identifier as Identifier
from .core import Ids as Ids
from .core import ImageAsset as ImageAsset
from .core import ImageAssetRequirements as ImageAssetRequirements
from .core import ImageAssetRequirementsColorSpace as ImageAssetRequirementsColorSpace
from .core import ImageAssetRequirementsFormatsItem as ImageAssetRequirementsFormatsItem
from .core import ImageCarouselFormatDeclaration as ImageCarouselFormatDeclaration
from .core import ImageFormatDeclaration as ImageFormatDeclaration
from .core import Impairment as Impairment
from .core import ImpairmentResourceType as ImpairmentResourceType
from .core import ImpairmentTransition as ImpairmentTransition
from .core import Indicator as Indicator
from .core import IndicatorBearingResourceState as IndicatorBearingResourceState
from .core import IndicatorsChangedWebhook as IndicatorsChangedWebhook
from .core import IndicatorsChangedWebhookChangeKind as IndicatorsChangedWebhookChangeKind
from .core import IndicatorsChangedWebhookRelationshipKind as IndicatorsChangedWebhookRelationshipKind
from .core import IndicatorScope as IndicatorScope
from .core import IndividualAudioAsset as IndividualAudioAsset
from .core import IndividualBriefAsset as IndividualBriefAsset
from .core import IndividualCardAsset as IndividualCardAsset
from .core import IndividualCatalogAsset as IndividualCatalogAsset
from .core import IndividualCssAsset as IndividualCssAsset
from .core import IndividualDaastAsset as IndividualDaastAsset
from .core import IndividualDaastTrackerAsset as IndividualDaastTrackerAsset
from .core import IndividualDisplayTagAsset as IndividualDisplayTagAsset
from .core import IndividualHtmlAsset as IndividualHtmlAsset
from .core import IndividualImageAsset as IndividualImageAsset
from .core import IndividualJavaScriptAsset as IndividualJavaScriptAsset
from .core import IndividualMarkdownAsset as IndividualMarkdownAsset
from .core import IndividualPixelTrackerAsset as IndividualPixelTrackerAsset
from .core import IndividualPublishedPostAsset as IndividualPublishedPostAsset
from .core import IndividualTextAsset as IndividualTextAsset
from .core import IndividualUrlAsset as IndividualUrlAsset
from .core import IndividualVastAsset as IndividualVastAsset
from .core import IndividualVastTrackerAsset as IndividualVastTrackerAsset
from .core import IndividualVideoAsset as IndividualVideoAsset
from .core import IndividualWebhookAsset as IndividualWebhookAsset
from .core import IndividualZipAsset as IndividualZipAsset
from .core import IndustryIdentifier as IndustryIdentifier
from .core import InlineMarkup as InlineMarkup
from .core import InlineMarkupMacroDeclarationsItem as InlineMarkupMacroDeclarationsItem
from .core import InlineMarkupMacroDeclarationsItemLocation as InlineMarkupMacroDeclarationsItemLocation
from .core import InlineMarkupMarkupType as InlineMarkupMarkupType
from .core import InsertionOrder as InsertionOrder
from .core import InsertionOrderTerms as InsertionOrderTerms
from .core import InsertionOrderTermsPaymentTerms as InsertionOrderTermsPaymentTerms
from .core import InsertionOrderTermsTotalBudget as InsertionOrderTermsTotalBudget
from .core import Installment as Installment
from .core import InstallmentDeadlines as InstallmentDeadlines
from .core import InstallmentDeliveryMetrics as InstallmentDeliveryMetrics
from .core import InstallmentDerivativeOf as InstallmentDerivativeOf
from .core import InstallmentPropertyDeliveryMetrics as InstallmentPropertyDeliveryMetrics
from .core import InstallmentReference as InstallmentReference
from .core import IntegerReportingControlTotal as IntegerReportingControlTotal
from .core import InventoryListApplication as InventoryListApplication
from .core import JavaScriptAsset as JavaScriptAsset
from .core import JavaScriptAssetRequirements as JavaScriptAssetRequirements
from .core import JavaScriptAssetRequirementsModuleType as JavaScriptAssetRequirementsModuleType
from .core import JobItem as JobItem
from .core import JobItemEmploymentType as JobItemEmploymentType
from .core import JobItemExperienceLevel as JobItemExperienceLevel
from .core import JobItemSalary as JobItemSalary
from .core import JobItemSalaryPeriod as JobItemSalaryPeriod
from .core import KeywordDeliveryMetrics as KeywordDeliveryMetrics
from .core import KeywordRequirement as KeywordRequirement
from .core import KeywordRequirementSupportedMatchTypes as KeywordRequirementSupportedMatchTypes
from .core import KeywordSupport as KeywordSupport
from .core import KeywordSupportSupportedMatchTypes as KeywordSupportSupportedMatchTypes
from .core import KeywordTarget as KeywordTarget
from .core import LanguageTag as LanguageTag
from .core import LimitedSeries as LimitedSeries
from .core import LocalizedCreativeAsset as LocalizedCreativeAsset
from .core import LookbackWindow as LookbackWindow
from .core import MacroBearingURL as MacroBearingURL
from .core import MacroDeclaration as MacroDeclaration
from .core import MacroDeclarationLocation as MacroDeclarationLocation
from .core import MacroDeclarationLocationField as MacroDeclarationLocationField
from .core import MacroDeclarationUnavailableBehavior as MacroDeclarationUnavailableBehavior
from .core import MacroEncoding as MacroEncoding
from .core import MacroEncodingKind as MacroEncodingKind
from .core import MacroProcessingCapability as MacroProcessingCapability
from .core import MacroProcessingCapabilityMappingStatus as MacroProcessingCapabilityMappingStatus
from .core import MacroProcessingCapabilityOperation as MacroProcessingCapabilityOperation
from .core import MacroResolutionResult as MacroResolutionResult
from .core import MacroResolutionResultStatus as MacroResolutionResultStatus
from .core import MacroTranslationTarget as MacroTranslationTarget
from .core import MarkdownAsset as MarkdownAsset
from .core import MarkdownAssetRequirements as MarkdownAssetRequirements
from .core import MaterialDeadline as MaterialDeadline
from .core import MCPWebhookPayload as MCPWebhookPayload
from .core import MeasurementReadiness as MeasurementReadiness
from .core import MeasurementTerms as MeasurementTerms
from .core import MeasurementTermsBillingMeasurement as MeasurementTermsBillingMeasurement
from .core import MeasurementTermsMakegoodPolicy as MeasurementTermsMakegoodPolicy
from .core import MeasurementWindow as MeasurementWindow
from .core import MediaBuy as MediaBuy
from .core import MediaBuyAvailableAction as MediaBuyAvailableAction
from .core import MediaBuyAvailableActionID as MediaBuyAvailableActionID
from .core import MediaBuyAvailableActionTask as MediaBuyAvailableActionTask
from .core import MediaBuyBidding as MediaBuyBidding
from .core import MediaBuyCancellation as MediaBuyCancellation
from .core import MediaBuyChangeTermID as MediaBuyChangeTermID
from .core import MediaBuyCommitmentResponseCompleted as MediaBuyCommitmentResponseCompleted
from .core import MediaBuyCommitmentResponseFailed as MediaBuyCommitmentResponseFailed
from .core import MediaBuyCommitmentResponseSubmitted as MediaBuyCommitmentResponseSubmitted
from .core import MediaBuyFeatures as MediaBuyFeatures
from .core import MediaBuyFeaturesBiddingPolicy as MediaBuyFeaturesBiddingPolicy
from .core import MediaBuyFrequencyCap as MediaBuyFrequencyCap
from .core import MediaBuyFrequencyCapCapability as MediaBuyFrequencyCapCapability
from .core import MediaBuyFrequencyCapRequirement as MediaBuyFrequencyCapRequirement
from .core import MediaBuyFrequencyCapSupport as MediaBuyFrequencyCapSupport
from .core import MediaBuyTermsReference as MediaBuyTermsReference
from .core import MetroRequirement as MetroRequirement
from .core import MetroRequirementSystems as MetroRequirementSystems
from .core import MetroSupport as MetroSupport
from .core import MetroSupportSystems as MetroSupportSystems
from .core import MissingMetric as MissingMetric
from .core import MissingMetricVendor as MissingMetricVendor
from .core import NamedFormatManifest as NamedFormatManifest
from .core import NativeInFeedFormatDeclaration as NativeInFeedFormatDeclaration
from .core import NegativeKeyword as NegativeKeyword
from .core import NonblockingImpacts as NonblockingImpacts
from .core import NotificationConfig as NotificationConfig
from .core import NotificationConfigAuthentication as NotificationConfigAuthentication
from .core import NotificationConfigEventTypesItem as NotificationConfigEventTypesItem
from .core import NotificationConfigProductPayloadView as NotificationConfigProductPayloadView
from .core import ObjAllValues as ObjAllValues
from .core import ObjScopeMetricIdQualifier as ObjScopeMetricIdQualifier
from .core import ObjValues as ObjValues
from .core import Offering as Offering
from .core import OfferingAssetConstraint as OfferingAssetConstraint
from .core import OfferingAssetGroup as OfferingAssetGroup
from .core import OfferingGeoTargets as OfferingGeoTargets
from .core import OfferingGeoTargetsMetrosItem as OfferingGeoTargetsMetrosItem
from .core import OperatorIdentity as OperatorIdentity
from .core import OperatorUnit as OperatorUnit
from .core import OpportunityContext as OpportunityContext
from .core import OpportunityContextCloseReason as OpportunityContextCloseReason
from .core import OpportunityContextIntent as OpportunityContextIntent
from .core import OpportunityContextPhase as OpportunityContextPhase
from .core import OpportunityContextStatus as OpportunityContextStatus
from .core import OptimizationGoal as OptimizationGoal
from .core import OptimizationGoalEvent as OptimizationGoalEvent
from .core import OptimizationGoalEventAttributionWindow as OptimizationGoalEventAttributionWindow
from .core import OptimizationGoalEventEventSourcesItem as OptimizationGoalEventEventSourcesItem
from .core import OptimizationGoalEventTargetCostPer as OptimizationGoalEventTargetCostPer
from .core import OptimizationGoalMetric as OptimizationGoalMetric
from .core import OptimizationGoalMetricMetric as OptimizationGoalMetricMetric
from .core import OptimizationGoalMetricTargetCostPer as OptimizationGoalMetricTargetCostPer
from .core import OptimizationGoalMetricTargetFrequency as OptimizationGoalMetricTargetFrequency
from .core import OptimizationGoalMetricTargetFrequencyWindow as OptimizationGoalMetricTargetFrequencyWindow
from .core import OptimizationGoalMetricTargetThresholdRate as OptimizationGoalMetricTargetThresholdRate
from .core import OptimizationGoalMetricVendor as OptimizationGoalMetricVendor
from .core import OptimizationGoalVendorMetric as OptimizationGoalVendorMetric
from .core import OptimizationGoalVendorMetricTargetCostPer as OptimizationGoalVendorMetricTargetCostPer
from .core import OptimizationGoalVendorMetricTargetThresholdRate as OptimizationGoalVendorMetricTargetThresholdRate
from .core import OutcomeMeasurement as OutcomeMeasurement
from .core import OutcomeMeasurementWindow as OutcomeMeasurementWindow
from .core import OutcomeTargetCostPer as OutcomeTargetCostPer
from .core import Overlay as Overlay
from .core import OverlayBounds as OverlayBounds
from .core import OverlayBoundsUnit as OverlayBoundsUnit
from .core import OverlayVisual as OverlayVisual
from .core import Package as Package
from .core import PackageBidding as PackageBidding
from .core import PackageCancellation as PackageCancellation
from .core import PackageDeliveryMetricValue as PackageDeliveryMetricValue
from .core import PackageDeliveryMetricValueQualifier as PackageDeliveryMetricValueQualifier
from .core import PackageFormatSnapshot as PackageFormatSnapshot
from .core import PackageFormatSnapshotAgentPlacement as PackageFormatSnapshotAgentPlacement
from .core import PackageFormatSnapshotAudioDaast as PackageFormatSnapshotAudioDaast
from .core import PackageFormatSnapshotAudioHosted as PackageFormatSnapshotAudioHosted
from .core import PackageFormatSnapshotAudioVast as PackageFormatSnapshotAudioVast
from .core import PackageFormatSnapshotCoordinatedPlacements as PackageFormatSnapshotCoordinatedPlacements
from .core import PackageFormatSnapshotCustom as PackageFormatSnapshotCustom
from .core import PackageFormatSnapshotDisplayTag as PackageFormatSnapshotDisplayTag
from .core import PackageFormatSnapshotHtml5 as PackageFormatSnapshotHtml5
from .core import PackageFormatSnapshotImage as PackageFormatSnapshotImage
from .core import PackageFormatSnapshotImageCarousel as PackageFormatSnapshotImageCarousel
from .core import PackageFormatSnapshotNativeInFeed as PackageFormatSnapshotNativeInFeed
from .core import PackageFormatSnapshotPlacementRefsItem as PackageFormatSnapshotPlacementRefsItem
from .core import PackageFormatSnapshotResponsiveCreative as PackageFormatSnapshotResponsiveCreative
from .core import (
    PackageFormatSnapshotSellerRenderedStatefulDisplay as PackageFormatSnapshotSellerRenderedStatefulDisplay,
)
from .core import PackageFormatSnapshotSponsoredPlacement as PackageFormatSnapshotSponsoredPlacement
from .core import PackageFormatSnapshotVideoHosted as PackageFormatSnapshotVideoHosted
from .core import PackageFormatSnapshotVideoVast as PackageFormatSnapshotVideoVast
from .core import PackageSignalTargeting as PackageSignalTargeting
from .core import PackageSignalTargetingBinary as PackageSignalTargetingBinary
from .core import PackageSignalTargetingCategorical as PackageSignalTargetingCategorical
from .core import PackageSignalTargetingGroup as PackageSignalTargetingGroup
from .core import PackageSignalTargetingGroupOperator as PackageSignalTargetingGroupOperator
from .core import PackageSignalTargetingGroups as PackageSignalTargetingGroups
from .core import PackageSignalTargetingGroupsOperator as PackageSignalTargetingGroupsOperator
from .core import PackageSignalTargetingNumeric as PackageSignalTargetingNumeric
from .core import PackageTargetingResolution as PackageTargetingResolution
from .core import PaginationRequest as PaginationRequest
from .core import PaginationResponse as PaginationResponse
from .core import PairedRedirect as PairedRedirect
from .core import PairedRedirectMacroDeclarationsItem as PairedRedirectMacroDeclarationsItem
from .core import PairedRedirectMacroDeclarationsItemLocation as PairedRedirectMacroDeclarationsItemLocation
from .core import PairedRedirectMacroDeclarationsItemLocationField as PairedRedirectMacroDeclarationsItemLocationField
from .core import PercentOfMediaPricing as PercentOfMediaPricing
from .core import PerformanceFeedback as PerformanceFeedback
from .core import PerformanceFeedbackAssertion as PerformanceFeedbackAssertion
from .core import PerformanceFeedbackAssertionEvidence as PerformanceFeedbackAssertionEvidence
from .core import (
    PerformanceFeedbackAssertionEvidenceConfidenceInterval as PerformanceFeedbackAssertionEvidenceConfidenceInterval,
)
from .core import PerformanceFeedbackMetric as PerformanceFeedbackMetric
from .core import PerformanceFeedbackMetricStandard as PerformanceFeedbackMetricStandard
from .core import PerformanceFeedbackMetricVendor as PerformanceFeedbackMetricVendor
from .core import PerformanceFeedbackStatus as PerformanceFeedbackStatus
from .core import PerformanceStandard as PerformanceStandard
from .core import PerUnitPricing as PerUnitPricing
from .core import PixelTrackerAsset as PixelTrackerAsset
from .core import PixelTrackerAssetMethod as PixelTrackerAssetMethod
from .core import Placement as Placement
from .core import PlacementDefinition as PlacementDefinition
from .core import PlacementDefinitionIdentifiersItem as PlacementDefinitionIdentifiersItem
from .core import (
    PlacementDefinitionPublisherDoohPlacementAttributes as PlacementDefinitionPublisherDoohPlacementAttributes,
)
from .core import PlacementDefinitionPublisherDoohScreenResolution as PlacementDefinitionPublisherDoohScreenResolution
from .core import PlacementDeliveryMetrics as PlacementDeliveryMetrics
from .core import PlacementEvidence as PlacementEvidence
from .core import PlacementForecastDimension as PlacementForecastDimension
from .core import PlacementIdentity as PlacementIdentity
from .core import PlacementKind as PlacementKind
from .core import PlacementMode as PlacementMode
from .core import PlacementPresentationDocument as PlacementPresentationDocument
from .core import PlacementPresentationDocumentBoxDecoration as PlacementPresentationDocumentBoxDecoration
from .core import PlacementPresentationDocumentCanvas as PlacementPresentationDocumentCanvas
from .core import PlacementPresentationDocumentCreativeSlot as PlacementPresentationDocumentCreativeSlot
from .core import PlacementPresentationDocumentCreativeSlotFit as PlacementPresentationDocumentCreativeSlotFit
from .core import PlacementPresentationDocumentImageDecoration as PlacementPresentationDocumentImageDecoration
from .core import PlacementPresentationDocumentImageDecorationFit as PlacementPresentationDocumentImageDecorationFit
from .core import (
    PlacementPresentationDocumentImageDecorationImageRef as PlacementPresentationDocumentImageDecorationImageRef,
)
from .core import PlacementPresentationDocumentLayer as PlacementPresentationDocumentLayer
from .core import PlacementPresentationDocumentRectangle as PlacementPresentationDocumentRectangle
from .core import PlacementPresentationDocumentTextDecoration as PlacementPresentationDocumentTextDecoration
from .core import PlacementPresentationReference as PlacementPresentationReference
from .core import PlacementProductDoohPlacementAttributes as PlacementProductDoohPlacementAttributes
from .core import PlacementProductDoohScreenResolution as PlacementProductDoohScreenResolution
from .core import PlacementPropertyDeliveryMetrics as PlacementPropertyDeliveryMetrics
from .core import PlacementReference as PlacementReference
from .core import PlacementSelection as PlacementSelection
from .core import PlannedDelivery as PlannedDelivery
from .core import PlannedDeliveryBidding as PlannedDeliveryBidding
from .core import PlannedDeliveryGeo as PlannedDeliveryGeo
from .core import PlatformDistribution as PlatformDistribution
from .core import PlatformExtensionReference as PlatformExtensionReference
from .core import PlatformSegment as PlatformSegment
from .core import PositivePostalAreaSupport as PositivePostalAreaSupport
from .core import PostalArea as PostalArea
from .core import PostalAreaAUPostcode as PostalAreaAUPostcode
from .core import PostalAreaBranch9System as PostalAreaBranch9System
from .core import PostalAreaBRCep as PostalAreaBRCep
from .core import PostalAreaCA as PostalAreaCA
from .core import PostalAreaCountrySystemValues as PostalAreaCountrySystemValues
from .core import PostalAreaFRCodePostal as PostalAreaFRCodePostal
from .core import PostalAreaGB as PostalAreaGB
from .core import PostalAreaINPin as PostalAreaINPin
from .core import PostalAreaPlz as PostalAreaPlz
from .core import PostalAreaSupport as PostalAreaSupport
from .core import PostalAreaSupportValueItem as PostalAreaSupportValueItem
from .core import PostalAreaUS as PostalAreaUS
from .core import PostalAreaWithFusedSystem as PostalAreaWithFusedSystem
from .core import PostalAreaZAPostalCode as PostalAreaZAPostalCode
from .core import PostalCountrySystem as PostalCountrySystem
from .core import PostalCountrySystemAUPostcode as PostalCountrySystemAUPostcode
from .core import PostalCountrySystemBranch9System as PostalCountrySystemBranch9System
from .core import PostalCountrySystemBRCep as PostalCountrySystemBRCep
from .core import PostalCountrySystemCA as PostalCountrySystemCA
from .core import PostalCountrySystemCASystem as PostalCountrySystemCASystem
from .core import PostalCountrySystemFRCodePostal as PostalCountrySystemFRCodePostal
from .core import PostalCountrySystemGB as PostalCountrySystemGB
from .core import PostalCountrySystemGBSystem as PostalCountrySystemGBSystem
from .core import PostalCountrySystemINPin as PostalCountrySystemINPin
from .core import PostalCountrySystemPlz as PostalCountrySystemPlz
from .core import PostalCountrySystemPlzCountry as PostalCountrySystemPlzCountry
from .core import PostalCountrySystemUS as PostalCountrySystemUS
from .core import PostalCountrySystemUSSystem as PostalCountrySystemUSSystem
from .core import PostalCountrySystemZAPostalCode as PostalCountrySystemZAPostalCode
from .core import PreviewRendererMetadata as PreviewRendererMetadata
from .core import PreviewRendererMetadataRenderingOrigin as PreviewRendererMetadataRenderingOrigin
from .core import Price as Price
from .core import PricePeriod as PricePeriod
from .core import PricingOption as PricingOption
from .core import PricingOptionCpa as PricingOptionCpa
from .core import PricingOptionCpc as PricingOptionCpc
from .core import PricingOptionCpcv as PricingOptionCpcv
from .core import PricingOptionCpm as PricingOptionCpm
from .core import PricingOptionCpp as PricingOptionCpp
from .core import PricingOptionCpv as PricingOptionCpv
from .core import PricingOptionFlatRate as PricingOptionFlatRate
from .core import PricingOptionRevenueShare as PricingOptionRevenueShare
from .core import PricingOptionTime as PricingOptionTime
from .core import PricingOptionVcpm as PricingOptionVcpm
from .core import PrincipalChangedWebhook as PrincipalChangedWebhook
from .core import PrincipalChangedWebhookReason as PrincipalChangedWebhookReason
from .core import PrincipalDeclarationsState as PrincipalDeclarationsState
from .core import PrincipalDeclarationsStateExclusionsItem as PrincipalDeclarationsStateExclusionsItem
from .core import PrincipalDeclarationsStateExclusionsItemAxis as PrincipalDeclarationsStateExclusionsItemAxis
from .core import PrincipalState as PrincipalState
from .core import PrincipalStateRetiredDestinationsItem as PrincipalStateRetiredDestinationsItem
from .core import Product as Product
from .core import ProductAllocation as ProductAllocation
from .core import ProductAllowedAction as ProductAllowedAction
from .core import ProductAudienceActivation as ProductAudienceActivation
from .core import ProductAudienceEvidenceRequirements as ProductAudienceEvidenceRequirements
from .core import (
    ProductAudienceEvidenceRequirementsEvidencePresence as ProductAudienceEvidenceRequirementsEvidencePresence,
)
from .core import ProductAudienceEvidenceRequirementsMaximumAge as ProductAudienceEvidenceRequirementsMaximumAge
from .core import ProductAudienceEvidenceRequirementsMaximumAgeUnit as ProductAudienceEvidenceRequirementsMaximumAgeUnit
from .core import (
    ProductAudienceEvidenceRequirementsRequirementMode as ProductAudienceEvidenceRequirementsRequirementMode,
)
from .core import ProductCardReferenceAsset as ProductCardReferenceAsset
from .core import ProductCardReferenceAssetRole as ProductCardReferenceAssetRole
from .core import ProductCatalogMatch as ProductCatalogMatch
from .core import ProductChangeMap as ProductChangeMap
from .core import ProductChangeMapValue as ProductChangeMapValue
from .core import ProductConversionTracking as ProductConversionTracking
from .core import ProductConversionTrackingSupportedTargetsItem as ProductConversionTrackingSupportedTargetsItem
from .core import ProductDefaultCollections as ProductDefaultCollections
from .core import ProductDefaultPlacements as ProductDefaultPlacements
from .core import ProductDeliveryMeasurement as ProductDeliveryMeasurement
from .core import ProductExecutionRequirement as ProductExecutionRequirement
from .core import ProductFilters as ProductFilters
from .core import ProductFiltersGeoProximityItem as ProductFiltersGeoProximityItem
from .core import ProductFiltersGeoProximityItemGeometry as ProductFiltersGeoProximityItemGeometry
from .core import ProductFiltersGeoProximityItemLatLngRadius as ProductFiltersGeoProximityItemLatLngRadius
from .core import (
    ProductFiltersGeoProximityItemLatLngTransportModeTravelTime as ProductFiltersGeoProximityItemLatLngTransportModeTravelTime,
)
from .core import ProductFiltersKeywordsItem as ProductFiltersKeywordsItem
from .core import ProductFiltersMetrosItem as ProductFiltersMetrosItem
from .core import ProductFiltersRequiredGeoTargetingItem as ProductFiltersRequiredGeoTargetingItem
from .core import ProductFiltersRequiredVendorMetricsItem as ProductFiltersRequiredVendorMetricsItem
from .core import ProductFiltersSignalTargetingItem as ProductFiltersSignalTargetingItem
from .core import ProductFiltersSignalTargetingItemTargetingMode as ProductFiltersSignalTargetingItemTargetingMode
from .core import ProductFiltersTrustedMatch as ProductFiltersTrustedMatch
from .core import ProductFiltersTrustedMatchProvidersItem as ProductFiltersTrustedMatchProvidersItem
from .core import ProductFormatDeclaration as ProductFormatDeclaration
from .core import ProductFormatDeclarationSellerPreference as ProductFormatDeclarationSellerPreference
from .core import ProductIdentity as ProductIdentity
from .core import ProductLocalFormatOptionReference as ProductLocalFormatOptionReference
from .core import ProductMaterialSubmission as ProductMaterialSubmission
from .core import ProductMediaBuySupport as ProductMediaBuySupport
from .core import ProductMediaBuySupportRequirements as ProductMediaBuySupportRequirements
from .core import ProductMetricOptimization as ProductMetricOptimization
from .core import ProductMetricOptimizationSupportedTargetsItem as ProductMetricOptimizationSupportedTargetsItem
from .core import ProductOfferFilters as ProductOfferFilters
from .core import ProductOfferFiltersAvailabilityHorizon as ProductOfferFiltersAvailabilityHorizon
from .core import ProductOfferFiltersRequiredFeatures as ProductOfferFiltersRequiredFeatures
from .core import (
    ProductOfferFiltersRequiredPerformanceStandardsItem as ProductOfferFiltersRequiredPerformanceStandardsItem,
)
from .core import ProductOfferFiltersRequiredVendorMetricsItem as ProductOfferFiltersRequiredVendorMetricsItem
from .core import ProductProductCard as ProductProductCard
from .core import ProductProductCardDetailed as ProductProductCardDetailed
from .core import ProductProductCardDetailedSpecificationsItem as ProductProductCardDetailedSpecificationsItem
from .core import ProductSignalTargetingOption as ProductSignalTargetingOption
from .core import ProductSignalTargetingOptionActivationStatus as ProductSignalTargetingOptionActivationStatus
from .core import (
    ProductSignalTargetingOptionAllowedTargetingModesItem as ProductSignalTargetingOptionAllowedTargetingModesItem,
)
from .core import ProductTargetingResolution as ProductTargetingResolution
from .core import ProductTrustedMatch as ProductTrustedMatch
from .core import ProductTrustedMatchProvidersItem as ProductTrustedMatchProvidersItem
from .core import Property as Property
from .core import PropertyDeliveryMetrics as PropertyDeliveryMetrics
from .core import PropertyID as PropertyID
from .core import PropertyListApplication as PropertyListApplication
from .core import PropertyListApplicationEffect as PropertyListApplicationEffect
from .core import PropertyListApplicationSummary as PropertyListApplicationSummary
from .core import PropertyListReference as PropertyListReference
from .core import PropertyReference as PropertyReference
from .core import PropertyTag as PropertyTag
from .core import Proposal as Proposal
from .core import ProposalTotalBudgetGuidance as ProposalTotalBudgetGuidance
from .core import ProtocolEnvelope as ProtocolEnvelope
from .core import ProtocolResponse as ProtocolResponse
from .core import Provenance as Provenance
from .core import ProvenanceAiTool as ProvenanceAiTool
from .core import ProvenanceC2pa as ProvenanceC2pa
from .core import ProvenanceDeclaredBy as ProvenanceDeclaredBy
from .core import ProvenanceDeclaredByRole as ProvenanceDeclaredByRole
from .core import ProvenanceDisclosure as ProvenanceDisclosure
from .core import ProvenanceDisclosureJurisdictionsItem as ProvenanceDisclosureJurisdictionsItem
from .core import (
    ProvenanceDisclosureJurisdictionsItemRenderGuidance as ProvenanceDisclosureJurisdictionsItemRenderGuidance,
)
from .core import ProvenanceEmbeddedProvenanceItem as ProvenanceEmbeddedProvenanceItem
from .core import ProvenanceEmbeddedProvenanceItemVerifyAgent as ProvenanceEmbeddedProvenanceItemVerifyAgent
from .core import ProvenanceHumanOversight as ProvenanceHumanOversight
from .core import ProvenanceVerificationItem as ProvenanceVerificationItem
from .core import ProvenanceVerificationItemResult as ProvenanceVerificationItemResult
from .core import ProvenanceWatermarksItem as ProvenanceWatermarksItem
from .core import ProvenanceWatermarksItemVerifyAgent as ProvenanceWatermarksItemVerifyAgent
from .core import ProvisionBinding as ProvisionBinding
from .core import ProvisionRecipient as ProvisionRecipient
from .core import ProvisionRecipientProvider as ProvisionRecipientProvider
from .core import ProvisionRecipientRecipient as ProvisionRecipientRecipient
from .core import PublishedPostAsset as PublishedPostAsset
from .core import PublishedPostAssetIdentityRef as PublishedPostAssetIdentityRef
from .core import PublishedPostAssetReferenceAuthorization as PublishedPostAssetReferenceAuthorization
from .core import PublishedPostAssetReferenceAuthorizationStatus as PublishedPostAssetReferenceAuthorizationStatus
from .core import PublisherCatalogFormatOptionReference as PublisherCatalogFormatOptionReference
from .core import PublisherCatalogPlacementIdentity as PublisherCatalogPlacementIdentity
from .core import PublisherDesignatedPreviewProvider as PublisherDesignatedPreviewProvider
from .core import PublisherDesignatedPreviewProviderRoutesItem as PublisherDesignatedPreviewProviderRoutesItem
from .core import PublisherPropertySelector as PublisherPropertySelector
from .core import PublisherPropertySelectorAll as PublisherPropertySelectorAll
from .core import PublisherPropertySelectorById as PublisherPropertySelectorById
from .core import PublisherPropertySelectorByTag as PublisherPropertySelectorByTag
from .core import PushNotificationConfig as PushNotificationConfig
from .core import PushNotificationConfigAuthentication as PushNotificationConfigAuthentication
from .core import Query as Query
from .core import RealEstateItem as RealEstateItem
from .core import RealEstateItemArea as RealEstateItemArea
from .core import RealEstateItemAreaUnit as RealEstateItemAreaUnit
from .core import RealEstateItemListingType as RealEstateItemListingType
from .core import RealEstateItemPropertyType as RealEstateItemPropertyType
from .core import ReferenceAsset as ReferenceAsset
from .core import ReferenceAssetRole as ReferenceAssetRole
from .core import ReferenceRenderer as ReferenceRenderer
from .core import ReferenceRendererProvenance as ReferenceRendererProvenance
from .core import RefineProposalsAsyncSubmitted as RefineProposalsAsyncSubmitted
from .core import RegistryEvent as RegistryEvent
from .core import RegistryEventAgentComplianceChangedAgent as RegistryEventAgentComplianceChangedAgent
from .core import RegistryEventAgentDiscoveredAgent as RegistryEventAgentDiscoveredAgent
from .core import RegistryEventAgentDiscoveredAgentPayload as RegistryEventAgentDiscoveredAgentPayload
from .core import RegistryEventAgentProfilePayload as RegistryEventAgentProfilePayload
from .core import RegistryEventAgentProfilePayloadType as RegistryEventAgentProfilePayloadType
from .core import RegistryEventAgentProfileUpdatedAgent as RegistryEventAgentProfileUpdatedAgent
from .core import RegistryEventAgentProfileUpdatedAgentPayload as RegistryEventAgentProfileUpdatedAgentPayload
from .core import RegistryEventAgentRemovedAgent as RegistryEventAgentRemovedAgent
from .core import RegistryEventAgentRemovedAgentPayload as RegistryEventAgentRemovedAgentPayload
from .core import RegistryEventAgentVerificationEarnedAgent as RegistryEventAgentVerificationEarnedAgent
from .core import RegistryEventAgentVerificationEarnedAgentPayload as RegistryEventAgentVerificationEarnedAgentPayload
from .core import (
    RegistryEventAgentVerificationEarnedAgentPayloadGradingProfile as RegistryEventAgentVerificationEarnedAgentPayloadGradingProfile,
)
from .core import RegistryEventAgentVerificationLostAgent as RegistryEventAgentVerificationLostAgent
from .core import RegistryEventAgentVerificationLostAgentPayload as RegistryEventAgentVerificationLostAgentPayload
from .core import RegistryEventAuthorizationGrantedAuthorization as RegistryEventAuthorizationGrantedAuthorization
from .core import RegistryEventAuthorizationModifiedAuthorization as RegistryEventAuthorizationModifiedAuthorization
from .core import RegistryEventAuthorizationPayload as RegistryEventAuthorizationPayload
from .core import (
    RegistryEventAuthorizationPayloadAuthorizationType as RegistryEventAuthorizationPayloadAuthorizationType,
)
from .core import RegistryEventAuthorizationPayloadEvidence as RegistryEventAuthorizationPayloadEvidence
from .core import RegistryEventAuthorizationRevokedAuthorization as RegistryEventAuthorizationRevokedAuthorization
from .core import RegistryEventClassification as RegistryEventClassification
from .core import RegistryEventCollectionCreatedCollection as RegistryEventCollectionCreatedCollection
from .core import RegistryEventCollectionCreatedCollectionPayload as RegistryEventCollectionCreatedCollectionPayload
from .core import RegistryEventCollectionIdentifier as RegistryEventCollectionIdentifier
from .core import RegistryEventCollectionMergedCollection as RegistryEventCollectionMergedCollection
from .core import RegistryEventCollectionMergedCollectionPayload as RegistryEventCollectionMergedCollectionPayload
from .core import RegistryEventCollectionPayload as RegistryEventCollectionPayload
from .core import RegistryEventCollectionPayloadStatus as RegistryEventCollectionPayloadStatus
from .core import RegistryEventCollectionRemovedCollection as RegistryEventCollectionRemovedCollection
from .core import RegistryEventCollectionRemovedCollectionPayload as RegistryEventCollectionRemovedCollectionPayload
from .core import RegistryEventCollectionUpdatedCollection as RegistryEventCollectionUpdatedCollection
from .core import RegistryEventCollectionUpdatedCollectionPayload as RegistryEventCollectionUpdatedCollectionPayload
from .core import RegistryEventCompliancePayload as RegistryEventCompliancePayload
from .core import RegistryEventCompliancePayloadStoryboardsItem as RegistryEventCompliancePayloadStoryboardsItem
from .core import RegistryEventCompliancePayloadTracksValue as RegistryEventCompliancePayloadTracksValue
from .core import RegistryEventComplianceStatus as RegistryEventComplianceStatus
from .core import RegistryEventEntityType as RegistryEventEntityType
from .core import RegistryEventEventType as RegistryEventEventType
from .core import RegistryEventPropertyCreatedProperty as RegistryEventPropertyCreatedProperty
from .core import RegistryEventPropertyCreatedPropertyPayload as RegistryEventPropertyCreatedPropertyPayload
from .core import RegistryEventPropertyMergedProperty as RegistryEventPropertyMergedProperty
from .core import RegistryEventPropertyMergedPropertyPayload as RegistryEventPropertyMergedPropertyPayload
from .core import RegistryEventPropertyPayload as RegistryEventPropertyPayload
from .core import RegistryEventPropertyReactivatedProperty as RegistryEventPropertyReactivatedProperty
from .core import RegistryEventPropertyReactivatedPropertyPayload as RegistryEventPropertyReactivatedPropertyPayload
from .core import RegistryEventPropertySource as RegistryEventPropertySource
from .core import RegistryEventPropertyStaleProperty as RegistryEventPropertyStaleProperty
from .core import RegistryEventPropertyStalePropertyPayload as RegistryEventPropertyStalePropertyPayload
from .core import RegistryEventPropertyUpdatedProperty as RegistryEventPropertyUpdatedProperty
from .core import RegistryEventPropertyUpdatedPropertyPayload as RegistryEventPropertyUpdatedPropertyPayload
from .core import RegistryEventPublisherAdagentsChangedPublisher as RegistryEventPublisherAdagentsChangedPublisher
from .core import (
    RegistryEventPublisherAdagentsChangedPublisherPayload as RegistryEventPublisherAdagentsChangedPublisherPayload,
)
from .core import RegistryEventPublisherAdagentsDiscoveredPublisher as RegistryEventPublisherAdagentsDiscoveredPublisher
from .core import RegistryEventPublisherAdagentsPayload as RegistryEventPublisherAdagentsPayload
from .core import RegistryEventStoryboardStatus as RegistryEventStoryboardStatus
from .core import RegistryFeedResponse as RegistryFeedResponse
from .core import RegistryFeedResponseFreshness as RegistryFeedResponseFreshness
from .core import RemoveTargetingSetValues as RemoveTargetingSetValues
from .core import RemoveTargetingSetValuesPath as RemoveTargetingSetValuesPath
from .core import RemoveTargetingSetValuesSelector as RemoveTargetingSetValuesSelector
from .core import RendersItemDimensions as RendersItemDimensions
from .core import RendersItemParametersFromFormatId as RendersItemParametersFromFormatId
from .core import RepeatableGroupAsset as RepeatableGroupAsset
from .core import RepeatableGroupAssetSelectionMode as RepeatableGroupAssetSelectionMode
from .core import ReplaceTargetingValue as ReplaceTargetingValue
from .core import ReportingAdjustment as ReportingAdjustment
from .core import ReportingAdjustmentAccountingPeriod as ReportingAdjustmentAccountingPeriod
from .core import ReportingAdjustmentReasonCode as ReportingAdjustmentReasonCode
from .core import ReportingAdjustmentReceipt as ReportingAdjustmentReceipt
from .core import ReportingAdjustmentReceiptStatus as ReportingAdjustmentReceiptStatus
from .core import ReportingAdjustmentRejectionCode as ReportingAdjustmentRejectionCode
from .core import ReportingCanonicalContentDigest as ReportingCanonicalContentDigest
from .core import ReportingCanonicalizationContract as ReportingCanonicalizationContract
from .core import ReportingCanonicalizationContractGoldenVectors as ReportingCanonicalizationContractGoldenVectors
from .core import (
    ReportingCanonicalizationContractGoldenVectorsAdditionalItem as ReportingCanonicalizationContractGoldenVectorsAdditionalItem,
)
from .core import (
    ReportingCanonicalizationContractGoldenVectorsEmptyReport as ReportingCanonicalizationContractGoldenVectorsEmptyReport,
)
from .core import (
    ReportingCanonicalizationContractGoldenVectorsOrderingEncoding as ReportingCanonicalizationContractGoldenVectorsOrderingEncoding,
)
from .core import ReportingCapabilities as ReportingCapabilities
from .core import ReportingCapabilitiesDateRangeSupport as ReportingCapabilitiesDateRangeSupport
from .core import ReportingCapabilitiesVendorMetricsItem as ReportingCapabilitiesVendorMetricsItem
from .core import ReportingConsumerStatus as ReportingConsumerStatus
from .core import ReportingConsumerStatusConsumerStatus as ReportingConsumerStatusConsumerStatus
from .core import ReportingConsumerStatusFailureCode as ReportingConsumerStatusFailureCode
from .core import ReportingConsumerStatusMismatchCode as ReportingConsumerStatusMismatchCode
from .core import ReportingConsumerStatusPeriod as ReportingConsumerStatusPeriod
from .core import ReportingControlTotal as ReportingControlTotal
from .core import ReportingCoverage as ReportingCoverage
from .core import ReportingCoverageLimitationsItem as ReportingCoverageLimitationsItem
from .core import ReportingCoverageLimitationsItemReason as ReportingCoverageLimitationsItemReason
from .core import ReportingCoverageStatus as ReportingCoverageStatus
from .core import ReportingDatasetShareDestination as ReportingDatasetShareDestination
from .core import ReportingDatasetShareDestinationExisting as ReportingDatasetShareDestinationExisting
from .core import ReportingDeliveryCapabilities as ReportingDeliveryCapabilities
from .core import ReportingDeliveryCapabilitiesOperationsContact as ReportingDeliveryCapabilitiesOperationsContact
from .core import ReportingDeliveryConfiguration as ReportingDeliveryConfiguration
from .core import ReportingDeliveryConfigurationAuthoritativeParty as ReportingDeliveryConfigurationAuthoritativeParty
from .core import ReportingDeliveryConfigurationCoverageRequirement as ReportingDeliveryConfigurationCoverageRequirement
from .core import ReportingDeliveryConfigurationScope as ReportingDeliveryConfigurationScope
from .core import ReportingDeliveryConfigurationState as ReportingDeliveryConfigurationState
from .core import (
    ReportingDeliveryConfigurationStateReportingDeliveryConfigLifecycleState as ReportingDeliveryConfigurationStateReportingDeliveryConfigLifecycleState,
)
from .core import ReportingDeliveryConfigurationStateSetup as ReportingDeliveryConfigurationStateSetup
from .core import ReportingDeliveryConfigurationStateSetupAction as ReportingDeliveryConfigurationStateSetupAction
from .core import ReportingDeliveryMethod as ReportingDeliveryMethod
from .core import ReportingDeliveryMethodFileTransfer as ReportingDeliveryMethodFileTransfer
from .core import ReportingDeliveryMethodReportingOrchestration as ReportingDeliveryMethodReportingOrchestration
from .core import ReportingDeliveryOffering as ReportingDeliveryOffering
from .core import ReportingDeliveryOfferingID as ReportingDeliveryOfferingID
from .core import ReportingDeliveryOfferingMethod as ReportingDeliveryOfferingMethod
from .core import (
    ReportingDeliveryOfferingMethodDestinationModesItem as ReportingDeliveryOfferingMethodDestinationModesItem,
)
from .core import ReportingDeliveryOfferingMethodProducerIdentity as ReportingDeliveryOfferingMethodProducerIdentity
from .core import ReportingDeliveryOfferingReportingDeliveryPattern as ReportingDeliveryOfferingReportingDeliveryPattern
from .core import ReportingDeliveryOfferingReportingFeedPurpose as ReportingDeliveryOfferingReportingFeedPurpose
from .core import ReportingDeliveryOfferingReportingProfile as ReportingDeliveryOfferingReportingProfile
from .core import ReportingDeliveryReadyWebhook as ReportingDeliveryReadyWebhook
from .core import ReportingDeliveryReadyWebhookReadiness as ReportingDeliveryReadyWebhookReadiness
from .core import ReportingFileCompression as ReportingFileCompression
from .core import ReportingFileEntry as ReportingFileEntry
from .core import ReportingFileManifest as ReportingFileManifest
from .core import ReportingFileObjectReference as ReportingFileObjectReference
from .core import ReportingLedgerChangedWebhook as ReportingLedgerChangedWebhook
from .core import ReportingLedgerChangedWebhookChangeKind as ReportingLedgerChangedWebhookChangeKind
from .core import ReportingMaterialization as ReportingMaterialization
from .core import ReportingMaterializationStatus as ReportingMaterializationStatus
from .core import ReportingMediaBuyId as ReportingMediaBuyId
from .core import ReportingNativeVersionReference as ReportingNativeVersionReference
from .core import ReportingObligation as ReportingObligation
from .core import ReportingObligationProductionStatus as ReportingObligationProductionStatus
from .core import ReportingObligationReconciliationStatus as ReportingObligationReconciliationStatus
from .core import ReportingPackageId as ReportingPackageId
from .core import ReportingPrimaryKey as ReportingPrimaryKey
from .core import ReportingReaderCompatibilityItem as ReportingReaderCompatibilityItem
from .core import ReportingReceipt as ReportingReceipt
from .core import ReportingReceiptStatus as ReportingReceiptStatus
from .core import ReportingReconciliationMode as ReportingReconciliationMode
from .core import ReportingReliabilityStatistics as ReportingReliabilityStatistics
from .core import (
    ReportingReliabilityStatisticsAdjustmentMagnitudeItem as ReportingReliabilityStatisticsAdjustmentMagnitudeItem,
)
from .core import ReportingReliabilityStatisticsEvidence as ReportingReliabilityStatisticsEvidence
from .core import ReportingReliabilityStatisticsEvidenceBasis as ReportingReliabilityStatisticsEvidenceBasis
from .core import ReportingReliabilityStatisticsLatencyPercentiles as ReportingReliabilityStatisticsLatencyPercentiles
from .core import (
    ReportingReliabilityStatisticsReportingReliabilityMeasurementPeriod as ReportingReliabilityStatisticsReportingReliabilityMeasurementPeriod,
)
from .core import ReportingReportDefinition as ReportingReportDefinition
from .core import ReportingReportDefinitionCalendar as ReportingReportDefinitionCalendar
from .core import ReportingReportDefinitionMetricsItem as ReportingReportDefinitionMetricsItem
from .core import ReportingReportDefinitionMetricsItemAggregation as ReportingReportDefinitionMetricsItemAggregation
from .core import (
    ReportingReportDefinitionReportCalendarTimezoneBasis as ReportingReportDefinitionReportCalendarTimezoneBasis,
)
from .core import ReportingReportDefinitionRestatementPolicy as ReportingReportDefinitionRestatementPolicy
from .core import ReportingReportDefinitionSource as ReportingReportDefinitionSource
from .core import ReportingResource as ReportingResource
from .core import ReportingResourceImmutability as ReportingResourceImmutability
from .core import ReportingResourceKind as ReportingResourceKind
from .core import ReportingRevision as ReportingRevision
from .core import ReportingRevisionDataThroughPrecision as ReportingRevisionDataThroughPrecision
from .core import ReportingRevisionFinalityBasis as ReportingRevisionFinalityBasis
from .core import ReportingSchedule as ReportingSchedule
from .core import ReportingScheduleOffering as ReportingScheduleOffering
from .core import ReportingScheduleOfferingPeriodAnchorPolicy as ReportingScheduleOfferingPeriodAnchorPolicy
from .core import ReportingScheduleOfferingPeriodTimezonePolicy as ReportingScheduleOfferingPeriodTimezonePolicy
from .core import ReportingScheduleReportingScheduleAlignment as ReportingScheduleReportingScheduleAlignment
from .core import ReportingStatusChangedWebhook as ReportingStatusChangedWebhook
from .core import ReportingStatusIssue as ReportingStatusIssue
from .core import ReportingStatusIssueCode as ReportingStatusIssueCode
from .core import ReportingStatusIssueIssueState as ReportingStatusIssueIssueState
from .core import ReportingStatusIssueRecommendedAction as ReportingStatusIssueRecommendedAction
from .core import ReportingStatusIssueReportingStatusSeverity as ReportingStatusIssueReportingStatusSeverity
from .core import ReportingStatusIssueResponsibleParty as ReportingStatusIssueResponsibleParty
from .core import ReportingVerification as ReportingVerification
from .core import ReportingVerificationNativeCommitEvidence as ReportingVerificationNativeCommitEvidence
from .core import (
    ReportingVerificationNativeCommitEvidenceObservedThrough as ReportingVerificationNativeCommitEvidenceObservedThrough,
)
from .core import ReportingVerificationProfile as ReportingVerificationProfile
from .core import ReportingVerificationProfileSet as ReportingVerificationProfileSet
from .core import ReportingVerificationVerificationPath as ReportingVerificationVerificationPath
from .core import ReportingWebhook as ReportingWebhook
from .core import ReportingWebhookReportingFrequency as ReportingWebhookReportingFrequency
from .core import ReportingWriteDestination as ReportingWriteDestination
from .core import ReportingWriteDestinationExisting as ReportingWriteDestinationExisting
from .core import RepresentationDestination as RepresentationDestination
from .core import RepresentationRejection as RepresentationRejection
from .core import RepresentationRejectionCode as RepresentationRejectionCode
from .core import RepresentationSelection as RepresentationSelection
from .core import RequestProposalsAsyncSubmitted as RequestProposalsAsyncSubmitted
from .core import ResolvedAssets as ResolvedAssets
from .core import ResponsePayloadJWSEnvelope as ResponsePayloadJWSEnvelope
from .core import ResponsePayloadJWSEnvelopeResponsePayload as ResponsePayloadJWSEnvelopeResponsePayload
from .core import ResponsePayloadJWSEnvelopeResponsePayloadTask as ResponsePayloadJWSEnvelopeResponsePayloadTask
from .core import ResponsiveCreativeFormatDeclaration as ResponsiveCreativeFormatDeclaration
from .core import RightsAttestationEvaluation as RightsAttestationEvaluation
from .core import RightsAttestationEvaluationEvaluation as RightsAttestationEvaluationEvaluation
from .core import (
    RightsAttestationEvaluationEvaluationActionBinding as RightsAttestationEvaluationEvaluationActionBinding,
)
from .core import RightsAttestationEvaluationReference as RightsAttestationEvaluationReference
from .core import RightsConstraint as RightsConstraint
from .core import RightsConstraintApprovalStatus as RightsConstraintApprovalStatus
from .core import RightsConstraintAttestationRefsItem as RightsConstraintAttestationRefsItem
from .core import RightsConstraintAttestationRefsItemSubject as RightsConstraintAttestationRefsItemSubject
from .core import RightsConstraintDisclosure as RightsConstraintDisclosure
from .core import RightsConstraintGrantStatus as RightsConstraintGrantStatus
from .core import RightsConstraintRightsAgent as RightsConstraintRightsAgent
from .core import ScopedCreativeApproval as ScopedCreativeApproval
from .core import SelectedCollections as SelectedCollections
from .core import SelectedCollectionsCollectionsItem as SelectedCollectionsCollectionsItem
from .core import SelectedPlacements as SelectedPlacements
from .core import SellerAgentReference as SellerAgentReference
from .core import SellerInlinePlacementIdentity as SellerInlinePlacementIdentity
from .core import SellerRenderedStatefulDisplayFormatDeclaration as SellerRenderedStatefulDisplayFormatDeclaration
from .core import SHA256PhysicalChecksum as SHA256PhysicalChecksum
from .core import SHA512PhysicalChecksum as SHA512PhysicalChecksum
from .core import SignalCoverageForecast as SignalCoverageForecast
from .core import SignalCoverageForecastBucketCompleteness as SignalCoverageForecastBucketCompleteness
from .core import SignalCoverageForecastBucketSemantics as SignalCoverageForecastBucketSemantics
from .core import SignalCoverageForecastPointsItem as SignalCoverageForecastPointsItem
from .core import SignalCoverageForecastPointsItemMetrics as SignalCoverageForecastPointsItemMetrics
from .core import SignalCoverageForecastScope as SignalCoverageForecastScope
from .core import SignalCoverageForecastScopeKind as SignalCoverageForecastScopeKind
from .core import SignalDefinition as SignalDefinition
from .core import SignalDefinitionArt9Basis as SignalDefinitionArt9Basis
from .core import SignalDefinitionAudienceScope as SignalDefinitionAudienceScope
from .core import SignalDefinitionDataSourcesItem as SignalDefinitionDataSourcesItem
from .core import SignalDefinitionDataSubjectRights as SignalDefinitionDataSubjectRights
from .core import SignalDefinitionDataSubjectRightsChannelsItem as SignalDefinitionDataSubjectRightsChannelsItem
from .core import (
    SignalDefinitionDataSubjectRightsChannelsItemRightsItem as SignalDefinitionDataSubjectRightsChannelsItemRightsItem,
)
from .core import SignalDefinitionEnrichment as SignalDefinitionEnrichment
from .core import SignalDefinitionIdTypesItem as SignalDefinitionIdTypesItem
from .core import SignalDefinitionLookbackWindow as SignalDefinitionLookbackWindow
from .core import SignalDefinitionMethodology as SignalDefinitionMethodology
from .core import SignalDefinitionModeling as SignalDefinitionModeling
from .core import SignalDefinitionModelingAiActRiskClass as SignalDefinitionModelingAiActRiskClass
from .core import SignalDefinitionModelingMethod as SignalDefinitionModelingMethod
from .core import SignalDefinitionModelingSeedSource as SignalDefinitionModelingSeedSource
from .core import SignalDefinitionModelingSeedSourceType as SignalDefinitionModelingSeedSourceType
from .core import SignalDefinitionOnboarder as SignalDefinitionOnboarder
from .core import SignalDefinitionOnboarderMatchKeysItem as SignalDefinitionOnboarderMatchKeysItem
from .core import (
    SignalDefinitionOnboarderPreOnboardingPrecisionLevel as SignalDefinitionOnboarderPreOnboardingPrecisionLevel,
)
from .core import SignalDefinitionRange as SignalDefinitionRange
from .core import SignalDefinitionRefreshCadence as SignalDefinitionRefreshCadence
from .core import SignalDefinitionTaxonomy as SignalDefinitionTaxonomy
from .core import SignalDefinitionTaxonomyParentMatchBehavior as SignalDefinitionTaxonomyParentMatchBehavior
from .core import SignalDefinitionTaxonomyValueMappingsItem as SignalDefinitionTaxonomyValueMappingsItem
from .core import SignalDefinitionTaxonomyValuesItem as SignalDefinitionTaxonomyValuesItem
from .core import SignalFilters as SignalFilters
from .core import SignalForecastDimension as SignalForecastDimension
from .core import SignalForecastDimensionPresence as SignalForecastDimensionPresence
from .core import SignalID as SignalID
from .core import SignalIDAgent as SignalIDAgent
from .core import SignalIDCatalog as SignalIDCatalog
from .core import SignalListing as SignalListing
from .core import SignalListingRange as SignalListingRange
from .core import SignalModelingDisclosure as SignalModelingDisclosure
from .core import SignalModelingDisclosureJurisdictionsItem as SignalModelingDisclosureJurisdictionsItem
from .core import SignalModelingDisclosureJurisdictionsItemAudience as SignalModelingDisclosureJurisdictionsItemAudience
from .core import SignalPricingOption as SignalPricingOption
from .core import SignalRef as SignalRef
from .core import SignalRefDataProvider as SignalRefDataProvider
from .core import SignalRefProduct as SignalRefProduct
from .core import SignalRefSignalSource as SignalRefSignalSource
from .core import SignalSelectionGroupRule as SignalSelectionGroupRule
from .core import SignalSelectionGroupRuleSelectionMode as SignalSelectionGroupRuleSelectionMode
from .core import SignalSelectionGroupRuleTargetingMode as SignalSelectionGroupRuleTargetingMode
from .core import SignalTargeting as SignalTargeting
from .core import SignalTargetingBinary as SignalTargetingBinary
from .core import SignalTargetingCategorical as SignalTargetingCategorical
from .core import SignalTargetingExpression as SignalTargetingExpression
from .core import SignalTargetingExpressionBinary as SignalTargetingExpressionBinary
from .core import SignalTargetingExpressionCategorical as SignalTargetingExpressionCategorical
from .core import SignalTargetingExpressionNumeric as SignalTargetingExpressionNumeric
from .core import SignalTargetingItemBinary as SignalTargetingItemBinary
from .core import SignalTargetingItemCategorical as SignalTargetingItemCategorical
from .core import SignalTargetingItemNumeric as SignalTargetingItemNumeric
from .core import SignalTargetingNumeric as SignalTargetingNumeric
from .core import SignalTargetingRules as SignalTargetingRules
from .core import SignalTargetingRulesResolutionModel as SignalTargetingRulesResolutionModel
from .core import SLAWindow as SLAWindow
from .core import SourceLocalizationReadback as SourceLocalizationReadback
from .core import Special as Special
from .core import SponsoredPlacementFormatDeclaration as SponsoredPlacementFormatDeclaration
from .core import SpotReportingCapability as SpotReportingCapability
from .core import StandardScope as StandardScope
from .core import StartTiming as StartTiming
from .core import StoreCatchments as StoreCatchments
from .core import StoreItem as StoreItem
from .core import StringArray as StringArray
from .core import Supported as Supported
from .core import SyncCatalogsAsyncInputRequired as SyncCatalogsAsyncInputRequired
from .core import SyncCatalogsAsyncSubmitted as SyncCatalogsAsyncSubmitted
from .core import SyncCatalogsAsyncWorking as SyncCatalogsAsyncWorking
from .core import SyncCreativesAsyncInputRequired as SyncCreativesAsyncInputRequired
from .core import SyncCreativesAsyncSubmitted as SyncCreativesAsyncSubmitted
from .core import SyncCreativesAsyncWorking as SyncCreativesAsyncWorking
from .core import Tags as Tags
from .core import TagURL as TagURL
from .core import TagURLMacroDeclarationsItem as TagURLMacroDeclarationsItem
from .core import Talent as Talent
from .core import TargetingModification as TargetingModification
from .core import TargetingOverlay as TargetingOverlay
from .core import TargetingOverlayAgeRestriction as TargetingOverlayAgeRestriction
from .core import TargetingOverlayDevicePlatform as TargetingOverlayDevicePlatform
from .core import TargetingOverlayDeviceType as TargetingOverlayDeviceType
from .core import TargetingOverlayGeoProximity as TargetingOverlayGeoProximity
from .core import TargetingOverlayGeoProximityItem as TargetingOverlayGeoProximityItem
from .core import TargetingOverlayGeoProximityItemGeometry as TargetingOverlayGeoProximityItemGeometry
from .core import TargetingOverlayGeoProximityItemGeometryType as TargetingOverlayGeoProximityItemGeometryType
from .core import TargetingOverlayGeoProximityItemLatLngRadius as TargetingOverlayGeoProximityItemLatLngRadius
from .core import (
    TargetingOverlayGeoProximityItemLatLngTransportModeTravelTime as TargetingOverlayGeoProximityItemLatLngTransportModeTravelTime,
)
from .core import TargetingOverlayGeoProximityItemRadius as TargetingOverlayGeoProximityItemRadius
from .core import TargetingOverlayGeoProximityItemTravelTime as TargetingOverlayGeoProximityItemTravelTime
from .core import TargetingOverlayInput as TargetingOverlayInput
from .core import TargetingOverlayRequirements as TargetingOverlayRequirements
from .core import TargetingOverlayRequirementsDemographicsAge as TargetingOverlayRequirementsDemographicsAge
from .core import TargetingOverlayRequirementsGeoProximity as TargetingOverlayRequirementsGeoProximity
from .core import TargetingOverlayRequirementsRequired as TargetingOverlayRequirementsRequired
from .core import TargetingOverlayStoreCatchmentsItem as TargetingOverlayStoreCatchmentsItem
from .core import TargetingOverlaySupport as TargetingOverlaySupport
from .core import TargetingOverlaySupportDemographicsAge as TargetingOverlaySupportDemographicsAge
from .core import TargetingOverlaySupportFrequencyCapSupport as TargetingOverlaySupportFrequencyCapSupport
from .core import TargetingOverlaySupportGeoProximity as TargetingOverlaySupportGeoProximity
from .core import TargetingOverlaySupportPlaceCatalogSupport as TargetingOverlaySupportPlaceCatalogSupport
from .core import TargetingOverlaySupportPlacementSelection as TargetingOverlaySupportPlacementSelection
from .core import TargetingOverlaySupportPlaceSupport as TargetingOverlaySupportPlaceSupport
from .core import TargetingUnknownAgeEligibilityConstraint as TargetingUnknownAgeEligibilityConstraint
from .core import TargetingVerifiedAgeBasisConstraint as TargetingVerifiedAgeBasisConstraint
from .core import TargetLocalizationReadback as TargetLocalizationReadback
from .core import TargetMaximizeValue as TargetMaximizeValue
from .core import TargetPerAdSpend as TargetPerAdSpend
from .core import TasksGetRequest as TasksGetRequest
from .core import TasksGetResponse as TasksGetResponse
from .core import TasksGetResponseError as TasksGetResponseError
from .core import TasksGetResponseErrorDetails as TasksGetResponseErrorDetails
from .core import TasksGetResponseHistoryItem as TasksGetResponseHistoryItem
from .core import TasksGetResponseProgress as TasksGetResponseProgress
from .core import TasksListRequest as TasksListRequest
from .core import TasksListRequestFilters as TasksListRequestFilters
from .core import TasksListRequestSort as TasksListRequestSort
from .core import TasksListRequestSortField as TasksListRequestSortField
from .core import TasksListResponse as TasksListResponse
from .core import TasksListResponseQuerySummary as TasksListResponseQuerySummary
from .core import TasksListResponseQuerySummaryDomainBreakdown as TasksListResponseQuerySummaryDomainBreakdown
from .core import TasksListResponseQuerySummarySortApplied as TasksListResponseQuerySummarySortApplied
from .core import TasksListResponseTasksItem as TasksListResponseTasksItem
from .core import TasksListResponseTasksItemDomain as TasksListResponseTasksItemDomain
from .core import TextAsset as TextAsset
from .core import TextAssetRequirements as TextAssetRequirements
from .core import TimeForecastDimension as TimeForecastDimension
from .core import TMPIdentityMatch as TMPIdentityMatch
from .core import TMPIdentityMatchBuyerAgent as TMPIdentityMatchBuyerAgent
from .core import TrackerExecutionContract as TrackerExecutionContract
from .core import TrackerExecutionSelector as TrackerExecutionSelector
from .core import TrackerExecutionSelectorDaastTracker as TrackerExecutionSelectorDaastTracker
from .core import TrackerExecutionSelectorPixelTrackerImg as TrackerExecutionSelectorPixelTrackerImg
from .core import TrackerExecutionSelectorVastTracker as TrackerExecutionSelectorVastTracker
from .core import Transformer as Transformer
from .core import TransformerMultiplicity as TransformerMultiplicity
from .core import TransformerMultiplicityVariantDimensionsItem as TransformerMultiplicityVariantDimensionsItem
from .core import TransformerParam as TransformerParam
from .core import TransformerParamOptionsItem as TransformerParamOptionsItem
from .core import TransformerParamType as TransformerParamType
from .core import TransformerParamValueSource as TransformerParamValueSource
from .core import TransformerVoiceSynthesisRefItem as TransformerVoiceSynthesisRefItem
from .core import TransformerVoiceSynthesisRefItemBrandAgent as TransformerVoiceSynthesisRefItemBrandAgent
from .core import TruncationSentinel as TruncationSentinel
from .core import TruncationSentinelTruncation as TruncationSentinelTruncation
from .core import UpdateMediaBuyAsyncInputRequired as UpdateMediaBuyAsyncInputRequired
from .core import UpdateMediaBuyAsyncSubmitted as UpdateMediaBuyAsyncSubmitted
from .core import UpdateMediaBuyAsyncWorking as UpdateMediaBuyAsyncWorking
from .core import URLAsset as URLAsset
from .core import URLAssetMacroDeclarationsItem as URLAssetMacroDeclarationsItem
from .core import URLAssetMacroDeclarationsItemLocation as URLAssetMacroDeclarationsItemLocation
from .core import URLAssetRequirements as URLAssetRequirements
from .core import URLAssetRequirementsProtocolsItem as URLAssetRequirementsProtocolsItem
from .core import URLAssetRequirementsRole as URLAssetRequirementsRole
from .core import UserMatch as UserMatch
from .core import V1CreativeNamedFormatReference as V1CreativeNamedFormatReference
from .core import V2CreativeCanonicalFormatKind as V2CreativeCanonicalFormatKind
from .core import VASTAsset as VASTAsset
from .core import VASTAssetInline as VASTAssetInline
from .core import VASTAssetRequirements as VASTAssetRequirements
from .core import VASTAssetUrl as VASTAssetUrl
from .core import VASTAudioFormatDeclaration as VASTAudioFormatDeclaration
from .core import VASTMediaFileRequirements as VASTMediaFileRequirements
from .core import VastOffset as VastOffset
from .core import VASTTrackerAsset as VASTTrackerAsset
from .core import VASTTrackerAssetTarget as VASTTrackerAssetTarget
from .core import VASTTrackerConstraints as VASTTrackerConstraints
from .core import VASTTrackerConstraintsVastEvent as VASTTrackerConstraintsVastEvent
from .core import VASTTrackerConstraintsVastTarget as VASTTrackerConstraintsVastTarget
from .core import VastVersions as VastVersions
from .core import VASTVideoFormatDeclaration as VASTVideoFormatDeclaration
from .core import VehicleItem as VehicleItem
from .core import VehicleItemBodyStyle as VehicleItemBodyStyle
from .core import VehicleItemCondition as VehicleItemCondition
from .core import VehicleItemFuelType as VehicleItemFuelType
from .core import VehicleItemMileage as VehicleItemMileage
from .core import VehicleItemMileageUnit as VehicleItemMileageUnit
from .core import VehicleItemTransmission as VehicleItemTransmission
from .core import VendorMetricID as VendorMetricID
from .core import VendorMetricOptimization as VendorMetricOptimization
from .core import VendorMetricOptimizationSupportedMetric as VendorMetricOptimizationSupportedMetric
from .core import (
    VendorMetricOptimizationSupportedMetricSupportedTargetsItem as VendorMetricOptimizationSupportedMetricSupportedTargetsItem,
)
from .core import VendorMetricValue as VendorMetricValue
from .core import VendorPricing as VendorPricing
from .core import VendorPricingOption as VendorPricingOption
from .core import VendorPricingOptionCpm as VendorPricingOptionCpm
from .core import VendorPricingOptionCustom as VendorPricingOptionCustom
from .core import VendorPricingOptionFlatFee as VendorPricingOptionFlatFee
from .core import VendorPricingOptionPercentOfMedia as VendorPricingOptionPercentOfMedia
from .core import VendorPricingOptionPerUnit as VendorPricingOptionPerUnit
from .core import VideoAsset as VideoAsset
from .core import VideoAssetAudioBitDepth as VideoAssetAudioBitDepth
from .core import VideoAssetChromaSubsampling as VideoAssetChromaSubsampling
from .core import VideoAssetColorSpace as VideoAssetColorSpace
from .core import VideoAssetHdrFormat as VideoAssetHdrFormat
from .core import VideoAssetRequirements as VideoAssetRequirements
from .core import VideoAssetRequirementsAudioCodecsItem as VideoAssetRequirementsAudioCodecsItem
from .core import VideoAssetRequirementsContainersItem as VideoAssetRequirementsContainersItem
from .core import VideoAssetVideoBitDepth as VideoAssetVideoBitDepth
from .core import WarehouseMaterialization as WarehouseMaterialization
from .core import WarehouseMaterializationDestination as WarehouseMaterializationDestination
from .core import Warning as Warning
from .core import WarningAffectedResource as WarningAffectedResource
from .core import WarningAffectedResourceResourceType as WarningAffectedResourceResourceType
from .core import WebhookActivityRecord as WebhookActivityRecord
from .core import WebhookActivityRecordStatus as WebhookActivityRecordStatus
from .core import WebhookAsset as WebhookAsset
from .core import WebhookAssetRequirements as WebhookAssetRequirements
from .core import WebhookAssetSecurity as WebhookAssetSecurity
from .core import WebhookChallenge as WebhookChallenge
from .core import WebhookChallengeResponse as WebhookChallengeResponse
from .core import WholesaleFeedEvent as WholesaleFeedEvent
from .core import WholesaleFeedEventEntityType as WholesaleFeedEventEntityType
from .core import WholesaleFeedEventEventType as WholesaleFeedEventEventType
from .core import WholesaleFeedEventProductCreatedProduct as WholesaleFeedEventProductCreatedProduct
from .core import WholesaleFeedEventProductCreatedProductPayload as WholesaleFeedEventProductCreatedProductPayload
from .core import WholesaleFeedEventProductPricedProduct as WholesaleFeedEventProductPricedProduct
from .core import WholesaleFeedEventProductPricedProductPayload as WholesaleFeedEventProductPricedProductPayload
from .core import WholesaleFeedEventProductRemovedProduct as WholesaleFeedEventProductRemovedProduct
from .core import WholesaleFeedEventProductRemovedProductPayload as WholesaleFeedEventProductRemovedProductPayload
from .core import WholesaleFeedEventProductUpdatedProduct as WholesaleFeedEventProductUpdatedProduct
from .core import WholesaleFeedEventProductUpdatedProductPayload as WholesaleFeedEventProductUpdatedProductPayload
from .core import WholesaleFeedEventRemovalReason as WholesaleFeedEventRemovalReason
from .core import WholesaleFeedEventSignal as WholesaleFeedEventSignal
from .core import WholesaleFeedEventSignalCreatedSignal as WholesaleFeedEventSignalCreatedSignal
from .core import WholesaleFeedEventSignalCreatedSignalPayload as WholesaleFeedEventSignalCreatedSignalPayload
from .core import WholesaleFeedEventSignalPricedSignal as WholesaleFeedEventSignalPricedSignal
from .core import WholesaleFeedEventSignalPricedSignalPayload as WholesaleFeedEventSignalPricedSignalPayload
from .core import WholesaleFeedEventSignalRemovedSignal as WholesaleFeedEventSignalRemovedSignal
from .core import WholesaleFeedEventSignalRemovedSignalPayload as WholesaleFeedEventSignalRemovedSignalPayload
from .core import WholesaleFeedEventSignalUpdatedSignal as WholesaleFeedEventSignalUpdatedSignal
from .core import WholesaleFeedEventSignalUpdatedSignalPayload as WholesaleFeedEventSignalUpdatedSignalPayload
from .core import WholesaleFeedEventWholesaleFeedBulkChangeFeed as WholesaleFeedEventWholesaleFeedBulkChangeFeed
from .core import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeedPayload as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayload,
)
from .core import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadAffectedEntityType as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadAffectedEntityType,
)
from .core import (
    WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadRecommendation as WholesaleFeedEventWholesaleFeedBulkChangeFeedPayloadRecommendation,
)
from .core import WholesaleFeedWebhook as WholesaleFeedWebhook
from .core import XEntityTypes as XEntityTypes
from .core import ZipAsset as ZipAsset
from .creative import AdCPAssetTypeRegistry as AdCPAssetTypeRegistry
from .creative import AssignOrUpdate as AssignOrUpdate
from .creative import CanonicalFormatTarget as CanonicalFormatTarget
from .creative import CreativeAssignmentChangedWebhook as CreativeAssignmentChangedWebhook
from .creative import CreativeAssignmentChangedWebhookChangeKind as CreativeAssignmentChangedWebhookChangeKind
from .creative import CreativeAuditObservation as CreativeAuditObservation
from .creative import CreativeAuditObservationCode as CreativeAuditObservationCode
from .creative import CreativeAuditObservationDetails as CreativeAuditObservationDetails
from .creative import CreativeAuditObservationDetailsClaimedValue as CreativeAuditObservationDetailsClaimedValue
from .creative import (
    CreativeAuditObservationDetailsClaimedValueHumanOversight as CreativeAuditObservationDetailsClaimedValueHumanOversight,
)
from .creative import CreativeAuditObservationRecovery as CreativeAuditObservationRecovery
from .creative import CreativeAuditObservationSeverity as CreativeAuditObservationSeverity
from .creative import CreativeCapabilityTarget as CreativeCapabilityTarget
from .creative import CreativeFeatureResult as CreativeFeatureResult
from .creative import CreativePurgedWebhook as CreativePurgedWebhook
from .creative import CreativePurgedWebhookInitiator as CreativePurgedWebhookInitiator
from .creative import CreativesItemFormatId as CreativesItemFormatId
from .creative import CreativesItemFormatKind as CreativesItemFormatKind
from .creative import CreativeStatusChangedWebhook as CreativeStatusChangedWebhook
from .creative import CreativeStatusChangedWebhookTransition as CreativeStatusChangedWebhookTransition
from .creative import CreativeStatusChangedWebhookTransitionFrom as CreativeStatusChangedWebhookTransitionFrom
from .creative import GetCreativeDeliveryRequest as GetCreativeDeliveryRequest
from .creative import GetCreativeDeliveryResponse as GetCreativeDeliveryResponse
from .creative import GetCreativeDeliveryResponseCreativesItem as GetCreativeDeliveryResponseCreativesItem
from .creative import GetCreativeDeliveryResponsePagination as GetCreativeDeliveryResponsePagination
from .creative import GetCreativeDeliveryResponseReportingPeriod as GetCreativeDeliveryResponseReportingPeriod
from .creative import GetCreativeFeaturesError as GetCreativeFeaturesError
from .creative import GetCreativeFeaturesRequest as GetCreativeFeaturesRequest
from .creative import GetCreativeFeaturesResponse as GetCreativeFeaturesResponse
from .creative import GetCreativeFeaturesResponseSubmitted as GetCreativeFeaturesResponseSubmitted
from .creative import GetCreativeFeaturesResponseSuccess as GetCreativeFeaturesResponseSuccess
from .creative import GetCreativeFeaturesSubmitted as GetCreativeFeaturesSubmitted
from .creative import GetCreativeFeaturesSuccess as GetCreativeFeaturesSuccess
from .creative import ListCreativeFormatsRequestCreativeAgent as ListCreativeFormatsRequestCreativeAgent
from .creative import ListCreativeFormatsRequestCreativeAgentType as ListCreativeFormatsRequestCreativeAgentType
from .creative import ListCreativeFormatsResponseCreativeAgent as ListCreativeFormatsResponseCreativeAgent
from .creative import (
    ListCreativeFormatsResponseCreativeAgentCreativeAgentsItem as ListCreativeFormatsResponseCreativeAgentCreativeAgentsItem,
)
from .creative import ListCreativesRequest as ListCreativesRequest
from .creative import ListCreativesRequestAssignmentProjection as ListCreativesRequestAssignmentProjection
from .creative import ListCreativesRequestFieldsItem as ListCreativesRequestFieldsItem
from .creative import ListCreativesRequestSort as ListCreativesRequestSort
from .creative import ListCreativesResponse as ListCreativesResponse
from .creative import ListCreativesResponseCreativesItem as ListCreativesResponseCreativesItem
from .creative import ListCreativesResponseCreativesItemAssignments as ListCreativesResponseCreativesItemAssignments
from .creative import (
    ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItem as ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItem,
)
from .creative import (
    ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorsItem as ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorsItem,
)
from .creative import (
    ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorTypesEvaluatedItem as ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorTypesEvaluatedItem,
)
from .creative import (
    ListCreativesResponseCreativesItemLocalizationUnavailable as ListCreativesResponseCreativesItemLocalizationUnavailable,
)
from .creative import ListCreativesResponseCreativesItemPurge as ListCreativesResponseCreativesItemPurge
from .creative import ListCreativesResponseCreativesItemPurgeKind as ListCreativesResponseCreativesItemPurgeKind
from .creative import ListCreativesResponseCreativesItemSnapshot as ListCreativesResponseCreativesItemSnapshot
from .creative import ListCreativesResponseQuerySummary as ListCreativesResponseQuerySummary
from .creative import ListCreativesResponseQuerySummarySortApplied as ListCreativesResponseQuerySummarySortApplied
from .creative import ListCreativesResponseStatusSummary as ListCreativesResponseStatusSummary
from .creative import ListedCreativeCanonicalFormatKind as ListedCreativeCanonicalFormatKind
from .creative import ListedCreativeNamedFormatReference as ListedCreativeNamedFormatReference
from .creative import ListTransformersRequestCreativeAgent as ListTransformersRequestCreativeAgent
from .creative import (
    ListTransformersRequestCreativeAgentExpandPaginationItem as ListTransformersRequestCreativeAgentExpandPaginationItem,
)
from .creative import ListTransformersResponseCreativeAgent as ListTransformersResponseCreativeAgent
from .creative import PreviewBatchResultError as PreviewBatchResultError
from .creative import PreviewBatchResultSuccess as PreviewBatchResultSuccess
from .creative import PreviewCreativeBatchResponse as PreviewCreativeBatchResponse
from .creative import PreviewCreativeBatchResponseResultsItem as PreviewCreativeBatchResponseResultsItem
from .creative import PreviewCreativeBatchResponseResultsItemResponse as PreviewCreativeBatchResponseResultsItemResponse
from .creative import (
    PreviewCreativeBatchResponseResultsItemResponsePreviewsItem as PreviewCreativeBatchResponseResultsItemResponsePreviewsItem,
)
from .creative import (
    PreviewCreativeBatchResponseResultsItemResponsePreviewsItemInput as PreviewCreativeBatchResponseResultsItemResponsePreviewsItemInput,
)
from .creative import PreviewCreativeRequest as PreviewCreativeRequest
from .creative import PreviewCreativeRequestRequestsItem as PreviewCreativeRequestRequestsItem
from .creative import PreviewCreativeRequestRequestType as PreviewCreativeRequestRequestType
from .creative import PreviewCreativeResponse as PreviewCreativeResponse
from .creative import PreviewCreativeSingleResponse as PreviewCreativeSingleResponse
from .creative import PreviewCreativeSingleResponsePreviewsItem as PreviewCreativeSingleResponsePreviewsItem
from .creative import PreviewCreativeSingleResponsePreviewsItemInput as PreviewCreativeSingleResponsePreviewsItemInput
from .creative import PreviewCreativeSubmitted as PreviewCreativeSubmitted
from .creative import PreviewCreativeVariantResponse as PreviewCreativeVariantResponse
from .creative import PreviewCreativeVariantResponsePreviewsItem as PreviewCreativeVariantResponsePreviewsItem
from .creative import PreviewRender as PreviewRender
from .creative import PreviewRenderBoth as PreviewRenderBoth
from .creative import PreviewRenderBothEmbedding as PreviewRenderBothEmbedding
from .creative import PreviewRenderHtml as PreviewRenderHtml
from .creative import PreviewRenderHtmlEmbedding as PreviewRenderHtmlEmbedding
from .creative import PreviewRenderUrl as PreviewRenderUrl
from .creative import PreviewRenderUrlDimensions as PreviewRenderUrlDimensions
from .creative import ProductTarget as ProductTarget
from .creative import ReplaceAssignment as ReplaceAssignment
from .creative import SyncCreativesError as SyncCreativesError
from .creative import SyncCreativesInputRequired as SyncCreativesInputRequired
from .creative import SyncCreativesInputRequiredReason as SyncCreativesInputRequiredReason
from .creative import SyncCreativesRequest as SyncCreativesRequest
from .creative import SyncCreativesRequestAssignmentsItem as SyncCreativesRequestAssignmentsItem
from .creative import SyncCreativesRequestCreativesItem as SyncCreativesRequestCreativesItem
from .creative import SyncCreativesResponse as SyncCreativesResponse
from .creative import SyncCreativesResponseSubmitted as SyncCreativesResponseSubmitted
from .creative import SyncCreativesSubmitted as SyncCreativesSubmitted
from .creative import SyncCreativesSuccess as SyncCreativesSuccess
from .creative import SyncCreativesSuccessCreativesItem as SyncCreativesSuccessCreativesItem
from .creative import SyncCreativesWorking as SyncCreativesWorking
from .creative import ThirdPartyFormatTarget as ThirdPartyFormatTarget
from .creative import Unassign as Unassign
from .creative import ValidateInputRequest as ValidateInputRequest
from .creative import ValidateInputRequestTargetsItem as ValidateInputRequestTargetsItem
from .creative import ValidateInputResponse as ValidateInputResponse
from .creative import ValidateInputResult as ValidateInputResult
from .creative import ValidateInputResultResultKind as ValidateInputResultResultKind
from .creative import ValidateInputResultTarget as ValidateInputResultTarget
from .creative import ValidateInputResultTargetKind as ValidateInputResultTargetKind
from .creative import ValidateInputResultViolationsItem as ValidateInputResultViolationsItem
from .creative import ValidateInputResultWarningsItem as ValidateInputResultWarningsItem
from .creative import VideoBrief as VideoBrief
from .creative import VideoBriefSegmentsItem as VideoBriefSegmentsItem
from .enums import AccountCurrencyMode as AccountCurrencyMode
from .enums import AccountScope as AccountScope
from .enums import AccountStatus as AccountStatus
from .enums import ActionNotAllowedReason as ActionNotAllowedReason
from .enums import ActionSource as ActionSource
from .enums import AdCPProtocol as AdCPProtocol
from .enums import AdCPSpecialism as AdCPSpecialism
from .enums import AdvertiserIndustry as AdvertiserIndustry
from .enums import AgeDeterminationBasis as AgeDeterminationBasis
from .enums import AgeVerificationMethod as AgeVerificationMethod
from .enums import AssessmentStatus as AssessmentStatus
from .enums import AssetContentType as AssetContentType
from .enums import AttestationClaim as AttestationClaim
from .enums import AttributionMethodology as AttributionMethodology
from .enums import AttributionModel as AttributionModel
from .enums import AudienceEvidenceMethodology as AudienceEvidenceMethodology
from .enums import AudienceResolutionMethod as AudienceResolutionMethod
from .enums import AudienceStatus as AudienceStatus
from .enums import AudienceSubjectType as AudienceSubjectType
from .enums import AudioChannelLayout as AudioChannelLayout
from .enums import AudioDistributionType as AudioDistributionType
from .enums import AuthenticationScheme as AuthenticationScheme
from .enums import AvailabilityStatus as AvailabilityStatus
from .enums import AvailableMetric as AvailableMetric
from .enums import BillingParty as BillingParty
from .enums import BinaryVerdict as BinaryVerdict
from .enums import BrandAgentType as BrandAgentType
from .enums import BrowserFamily as BrowserFamily
from .enums import C2PAWatermarkAction as C2PAWatermarkAction
from .enums import CanceledBy as CanceledBy
from .enums import CanonicalMediaBuyActionMode as CanonicalMediaBuyActionMode
from .enums import CanonicalMediaBuyActionName as CanonicalMediaBuyActionName
from .enums import CatalogAction as CatalogAction
from .enums import CatalogItemStatus as CatalogItemStatus
from .enums import CatalogType as CatalogType
from .enums import CloudStorageProtocol as CloudStorageProtocol
from .enums import CoBrandingRequirement as CoBrandingRequirement
from .enums import CollectionCadence as CollectionCadence
from .enums import CollectionKind as CollectionKind
from .enums import CollectionRelationship as CollectionRelationship
from .enums import CollectionStatus as CollectionStatus
from .enums import CompletionSource as CompletionSource
from .enums import ConsentBasis as ConsentBasis
from .enums import ContentIDType as ContentIDType
from .enums import ContentRatingSystem as ContentRatingSystem
from .enums import CountryFusedPostalCodeSystem as CountryFusedPostalCodeSystem
from .enums import CreativeAction as CreativeAction
from .enums import CreativeActivationMethod as CreativeActivationMethod
from .enums import CreativeAgentCapability as CreativeAgentCapability
from .enums import CreativeApprovalStatus as CreativeApprovalStatus
from .enums import CreativeEventReasonCode as CreativeEventReasonCode
from .enums import CreativeIdentifierType as CreativeIdentifierType
from .enums import CreativeMotionLevel as CreativeMotionLevel
from .enums import CreativeQuality as CreativeQuality
from .enums import CreativeSelectionStrategy as CreativeSelectionStrategy
from .enums import CreativeSortField as CreativeSortField
from .enums import CreativeStatus as CreativeStatus
from .enums import CTVAdExperience as CTVAdExperience
from .enums import DAASTTrackingEvent as DAASTTrackingEvent
from .enums import DAASTVersion as DAASTVersion
from .enums import DayOfWeek as DayOfWeek
from .enums import DaypartTimezoneMode as DaypartTimezoneMode
from .enums import DelegationAuthority as DelegationAuthority
from .enums import DeliveryRecipientCloud as DeliveryRecipientCloud
from .enums import DeliveryStatus as DeliveryStatus
from .enums import DeliveryType as DeliveryType
from .enums import DemographicSystem as DemographicSystem
from .enums import DerivativeType as DerivativeType
from .enums import DevicePlatform as DevicePlatform
from .enums import DeviceType as DeviceType
from .enums import DigitalSourceType as DigitalSourceType
from .enums import DimensionUnit as DimensionUnit
from .enums import DisclosurePersistence as DisclosurePersistence
from .enums import DisclosurePosition as DisclosurePosition
from .enums import DistanceUnit as DistanceUnit
from .enums import DistributionIdentifierType as DistributionIdentifierType
from .enums import DOOHMotionType as DOOHMotionType
from .enums import EmbeddedProvenanceMethod as EmbeddedProvenanceMethod
from .enums import ErrorCode as ErrorCode
from .enums import ErrorScope as ErrorScope
from .enums import EscalationSeverity as EscalationSeverity
from .enums import EventType as EventType
from .enums import Exclusivity as Exclusivity
from .enums import FeatureCheckStatus as FeatureCheckStatus
from .enums import FeedbackSource as FeedbackSource
from .enums import FeedFormat as FeedFormat
from .enums import ForecastableMetric as ForecastableMetric
from .enums import ForecastMethod as ForecastMethod
from .enums import ForecastRangeUnit as ForecastRangeUnit
from .enums import FormatIDParameter as FormatIDParameter
from .enums import FrameRateType as FrameRateType
from .enums import FrequencyCapControlMode as FrequencyCapControlMode
from .enums import FrequencyCapMutableField as FrequencyCapMutableField
from .enums import FrequencyCapScope as FrequencyCapScope
from .enums import GenreTaxonomy as GenreTaxonomy
from .enums import GeographicTargetingLevel as GeographicTargetingLevel
from .enums import GOPType as GOPType
from .enums import GovernanceDecision as GovernanceDecision
from .enums import GovernanceDomain as GovernanceDomain
from .enums import GovernanceMode as GovernanceMode
from .enums import GovernancePhase as GovernancePhase
from .enums import HistoryEntryType as HistoryEntryType
from .enums import HTTPMethod as HTTPMethod
from .enums import ImpairmentOfflineState as ImpairmentOfflineState
from .enums import ImpairmentReasonCode as ImpairmentReasonCode
from .enums import IndicatorType as IndicatorType
from .enums import InstallmentStatus as InstallmentStatus
from .enums import JavaScriptModuleType as JavaScriptModuleType
from .enums import LandingPageRequirement as LandingPageRequirement
from .enums import LiftDimension as LiftDimension
from .enums import LogoSlot as LogoSlot
from .enums import MacroDialectFamily as MacroDialectFamily
from .enums import MacroMappingStatus as MacroMappingStatus
from .enums import MacroProcessingActor as MacroProcessingActor
from .enums import MacroProcessingOperation as MacroProcessingOperation
from .enums import MacroResolutionReason as MacroResolutionReason
from .enums import MacroValueContext as MacroValueContext
from .enums import MakegoodRemedy as MakegoodRemedy
from .enums import MarkdownFlavor as MarkdownFlavor
from .enums import MatchIDType as MatchIDType
from .enums import MatchType as MatchType
from .enums import MediaBuyActionMode as MediaBuyActionMode
from .enums import MediaBuyFrequencyCapControlMode as MediaBuyFrequencyCapControlMode
from .enums import MediaBuyHealth as MediaBuyHealth
from .enums import MediaBuyStatus as MediaBuyStatus
from .enums import MediaBuyValidAction as MediaBuyValidAction
from .enums import MediaChannel as MediaChannel
from .enums import MetricScope as MetricScope
from .enums import MetricType as MetricType
from .enums import MetroAreaSystem as MetroAreaSystem
from .enums import MoovAtomPosition as MoovAtomPosition
from .enums import NotificationType as NotificationType
from .enums import OfferingAvailabilityStatus as OfferingAvailabilityStatus
from .enums import OutcomeTargetCostStrength as OutcomeTargetCostStrength
from .enums import OutcomeType as OutcomeType
from .enums import Pacing as Pacing
from .enums import PaymentTerms as PaymentTerms
from .enums import PerformanceBaseline as PerformanceBaseline
from .enums import PerformanceStandardMetric as PerformanceStandardMetric
from .enums import PixelTrackingEvent as PixelTrackingEvent
from .enums import PolicyCategory as PolicyCategory
from .enums import PolicyEnforcementLevel as PolicyEnforcementLevel
from .enums import PostalCodeSystem as PostalCodeSystem
from .enums import PreviewOutputFormat as PreviewOutputFormat
from .enums import PriceAdjustmentKind as PriceAdjustmentKind
from .enums import PricingModel as PricingModel
from .enums import PricingStructure as PricingStructure
from .enums import PrincipalKind as PrincipalKind
from .enums import ProductionQuality as ProductionQuality
from .enums import PropertyIdentifierTypes as PropertyIdentifierTypes
from .enums import PropertyType as PropertyType
from .enums import ProposalDeclineReason as ProposalDeclineReason
from .enums import ProposalRefinementReason as ProposalRefinementReason
from .enums import ProposalStatus as ProposalStatus
from .enums import PublisherIdentifierTypes as PublisherIdentifierTypes
from .enums import PurchaseType as PurchaseType
from .enums import ReachAggregation as ReachAggregation
from .enums import ReachUnit as ReachUnit
from .enums import ReportingDestinationSetupState as ReportingDestinationSetupState
from .enums import ReportingFinality as ReportingFinality
from .enums import ReportingFrequency as ReportingFrequency
from .enums import ReportingHealth as ReportingHealth
from .enums import RepresentationSelectionStrategy as RepresentationSelectionStrategy
from .enums import RequestSigningErrorCode as RequestSigningErrorCode
from .enums import RestrictedAttribute as RestrictedAttribute
from .enums import RightsBillingPeriod as RightsBillingPeriod
from .enums import RightType as RightType
from .enums import RightUse as RightUse
from .enums import ScanType as ScanType
from .enums import SellerPolicyDeclineReason as SellerPolicyDeclineReason
from .enums import SignalAvailabilityType as SignalAvailabilityType
from .enums import SignalSource as SignalSource
from .enums import SignalValueType as SignalValueType
from .enums import SISessionStatus as SISessionStatus
from .enums import SnapshotUnavailableReason as SnapshotUnavailableReason
from .enums import SocialPlacementSurface as SocialPlacementSurface
from .enums import SortDirection as SortDirection
from .enums import SortMetric as SortMetric
from .enums import SpecialCategory as SpecialCategory
from .enums import SponsoredPlacementType as SponsoredPlacementType
from .enums import TalentRole as TalentRole
from .enums import TaskStatus as TaskStatus
from .enums import TaskType as TaskType
from .enums import TMPResponseType as TMPResponseType
from .enums import TrackerExecutionActor as TrackerExecutionActor
from .enums import TrackerFiringPath as TrackerFiringPath
from .enums import TransportMode as TransportMode
from .enums import TravelTimeUnit as TravelTimeUnit
from .enums import UIDType as UIDType
from .enums import UniversalMacro as UniversalMacro
from .enums import UpdateFrequency as UpdateFrequency
from .enums import URLAssetType as URLAssetType
from .enums import ValidationMode as ValidationMode
from .enums import VASTMediaDeliveryMethod as VASTMediaDeliveryMethod
from .enums import VASTTrackingEvent as VASTTrackingEvent
from .enums import VASTVersion as VASTVersion
from .enums import VendorRelationship as VendorRelationship
from .enums import VideoPlacementType as VideoPlacementType
from .enums import ViewabilityStandard as ViewabilityStandard
from .enums import ViewThresholdBasis as ViewThresholdBasis
from .enums import WarningCode as WarningCode
from .enums import WatermarkMediaType as WatermarkMediaType
from .enums import WCAGLevel as WCAGLevel
from .enums import WebhookResponseType as WebhookResponseType
from .enums import WebhookSecurityMethod as WebhookSecurityMethod
from .error_details import AccessibilityViolationDetails as AccessibilityViolationDetails
from .error_details import AccessibilityViolationDetailsViolationsItem as AccessibilityViolationDetailsViolationsItem
from .error_details import AccountMovedDetails as AccountMovedDetails
from .error_details import AccountSetupRequiredDetails as AccountSetupRequiredDetails
from .error_details import ActionNotAllowedDetails as ActionNotAllowedDetails
from .error_details import AgentPermissionDeniedDetails as AgentPermissionDeniedDetails
from .error_details import AgentPermissionDeniedDetailsReason as AgentPermissionDeniedDetailsReason
from .error_details import AssetOutsideAcceptedVersionIntersection as AssetOutsideAcceptedVersionIntersection
from .error_details import AudienceTooSmallDetails as AudienceTooSmallDetails
from .error_details import AuthorizationRequiredDetails as AuthorizationRequiredDetails
from .error_details import BillingNotPermittedForAgentDetails as BillingNotPermittedForAgentDetails
from .error_details import BillingNotSupportedDetails as BillingNotSupportedDetails
from .error_details import BillingNotSupportedDetailsScope as BillingNotSupportedDetailsScope
from .error_details import BudgetTooLowDetails as BudgetTooLowDetails
from .error_details import ConflictDetails as ConflictDetails
from .error_details import CreativeRejectedDetails as CreativeRejectedDetails
from .error_details import CreativeRepresentationUnresolvedDetails as CreativeRepresentationUnresolvedDetails
from .error_details import CreativeRevisionContentMismatchDetails as CreativeRevisionContentMismatchDetails
from .error_details import ExecutionRequirementUnmetDetails as ExecutionRequirementUnmetDetails
from .error_details import (
    ExecutionRequirementUnmetDetailsUnmetRequirementsItem as ExecutionRequirementUnmetDetailsUnmetRequirementsItem,
)
from .error_details import (
    ExecutionRequirementUnmetDetailsUnmetRequirementsItemReason as ExecutionRequirementUnmetDetailsUnmetRequirementsItemReason,
)
from .error_details import FailureKind as FailureKind
from .error_details import GovernanceAgentNotAcceptedDetails as GovernanceAgentNotAcceptedDetails
from .error_details import GovernanceAgentNotAcceptedDetailsDisclosed as GovernanceAgentNotAcceptedDetailsDisclosed
from .error_details import GovernanceAgentNotAcceptedDetailsOpaque as GovernanceAgentNotAcceptedDetailsOpaque
from .error_details import InspectedDocumentVersionMismatch as InspectedDocumentVersionMismatch
from .error_details import MacroResolutionFailedDetails as MacroResolutionFailedDetails
from .error_details import PolicyViolationDetails as PolicyViolationDetails
from .error_details import PolicyViolationDetailsOrigin as PolicyViolationDetailsOrigin
from .error_details import RateLimitedDetails as RateLimitedDetails
from .error_details import RateLimitedDetailsScope as RateLimitedDetailsScope
from .error_details import RequoteRequiredDetails as RequoteRequiredDetails
from .error_details import StaleResponseDetails as StaleResponseDetails
from .error_details import StaleResponseDetailsOriginalError as StaleResponseDetailsOriginalError
from .error_details import StaleResponseDetailsUpstream as StaleResponseDetailsUpstream
from .error_details import SupportedVersionsCompatibilityDetails as SupportedVersionsCompatibilityDetails
from .error_details import UnsupportedRefinementDimensionDetails as UnsupportedRefinementDimensionDetails
from .error_details import VASTVersionMismatchDetails as VASTVersionMismatchDetails
from .error_details import VASTVersionMismatchDetailsDocumentRole as VASTVersionMismatchDetailsDocumentRole
from .error_details import VASTVersionMismatchDetailsMismatchReason as VASTVersionMismatchDetailsMismatchReason
from .error_details import VendorErrorCodeRegistry as VendorErrorCodeRegistry
from .error_details import VendorErrorCodeRegistryVendorsValue as VendorErrorCodeRegistryVendorsValue
from .error_details import (
    VendorErrorCodeRegistryVendorsValueCodesValue as VendorErrorCodeRegistryVendorsValueCodesValue,
)
from .error_details import VersionUnsupportedDetails as VersionUnsupportedDetails
from .extensions import AdCPExtensionFileSchema as AdCPExtensionFileSchema
from .extensions import AdCPExtensionRegistry as AdCPExtensionRegistry
from .formats import AllowedCardAssetTypesItem as AllowedCardAssetTypesItem
from .formats import (
    CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement as CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement,
)
from .formats import (
    CanonicalFormatAgentPlacementAISurfaceSponsoredPlacementOutputModality as CanonicalFormatAgentPlacementAISurfaceSponsoredPlacementOutputModality,
)
from .formats import CanonicalFormatBase as CanonicalFormatBase
from .formats import CanonicalFormatBaseCompositionModel as CanonicalFormatBaseCompositionModel
from .formats import CanonicalFormatBaseReferenceMutability as CanonicalFormatBaseReferenceMutability
from .formats import CanonicalFormatBaseSlotsItem as CanonicalFormatBaseSlotsItem
from .formats import CanonicalFormatBaseSlotsItemAssetType as CanonicalFormatBaseSlotsItemAssetType
from .formats import CanonicalFormatCoordinatedPlacements as CanonicalFormatCoordinatedPlacements
from .formats import (
    CanonicalFormatCoordinatedPlacementsComponentsItem as CanonicalFormatCoordinatedPlacementsComponentsItem,
)
from .formats import (
    CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy as CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy,
)
from .formats import (
    CanonicalFormatCoordinatedPlacementsSharedSlotsItem as CanonicalFormatCoordinatedPlacementsSharedSlotsItem,
)
from .formats import (
    CanonicalFormatCoordinatedPlacementsSharedSlotsItemAssetType as CanonicalFormatCoordinatedPlacementsSharedSlotsItemAssetType,
)
from .formats import CanonicalFormatDAASTAudio as CanonicalFormatDAASTAudio
from .formats import CanonicalFormatDisplayTag as CanonicalFormatDisplayTag
from .formats import CanonicalFormatDisplayTagSizesItem as CanonicalFormatDisplayTagSizesItem
from .formats import (
    CanonicalFormatDisplayTagSupportedDeliveryTypesItem as CanonicalFormatDisplayTagSupportedDeliveryTypesItem,
)
from .formats import CanonicalFormatDisplayTagSupportedTagTypesItem as CanonicalFormatDisplayTagSupportedTagTypesItem
from .formats import CanonicalFormatHostedAudio as CanonicalFormatHostedAudio
from .formats import CanonicalFormatHostedAudioAssetSource as CanonicalFormatHostedAudioAssetSource
from .formats import CanonicalFormatHostedAudioAudioChannelsItem as CanonicalFormatHostedAudioAudioChannelsItem
from .formats import CanonicalFormatHostedAudioAudioCodecsItem as CanonicalFormatHostedAudioAudioCodecsItem
from .formats import CanonicalFormatHostedAudioBuyerAssetAcceptance as CanonicalFormatHostedAudioBuyerAssetAcceptance
from .formats import CanonicalFormatHostedVideo as CanonicalFormatHostedVideo
from .formats import CanonicalFormatHostedVideoAudioCodecsItem as CanonicalFormatHostedVideoAudioCodecsItem
from .formats import CanonicalFormatHostedVideoBuyerAssetAcceptance as CanonicalFormatHostedVideoBuyerAssetAcceptance
from .formats import CanonicalFormatHostedVideoCaptions as CanonicalFormatHostedVideoCaptions
from .formats import CanonicalFormatHostedVideoOrientation as CanonicalFormatHostedVideoOrientation
from .formats import CanonicalFormatHostedVideoVideoCodecsItem as CanonicalFormatHostedVideoVideoCodecsItem
from .formats import CanonicalFormatHTML5Banner as CanonicalFormatHTML5Banner
from .formats import CanonicalFormatHTML5BannerMraidVersion as CanonicalFormatHTML5BannerMraidVersion
from .formats import CanonicalFormatHTML5BannerSizesItem as CanonicalFormatHTML5BannerSizesItem
from .formats import CanonicalFormatImage as CanonicalFormatImage
from .formats import CanonicalFormatImageBuyerAssetAcceptance as CanonicalFormatImageBuyerAssetAcceptance
from .formats import CanonicalFormatImageCarousel as CanonicalFormatImageCarousel
from .formats import CanonicalFormatImageImageFormatsItem as CanonicalFormatImageImageFormatsItem
from .formats import CanonicalFormatImageMotionLevel as CanonicalFormatImageMotionLevel
from .formats import CanonicalFormatImageSizesItem as CanonicalFormatImageSizesItem
from .formats import CanonicalFormatNativeInFeed as CanonicalFormatNativeInFeed
from .formats import CanonicalFormatNativeInFeedAssetSource as CanonicalFormatNativeInFeedAssetSource
from .formats import CanonicalFormatNativeInFeedBuyerAssetAcceptance as CanonicalFormatNativeInFeedBuyerAssetAcceptance
from .formats import CanonicalFormatNativeInFeedFocusBehavior as CanonicalFormatNativeInFeedFocusBehavior
from .formats import CanonicalFormatNativeInFeedIconSize as CanonicalFormatNativeInFeedIconSize
from .formats import CanonicalFormatNativeInFeedImageFormatsItem as CanonicalFormatNativeInFeedImageFormatsItem
from .formats import CanonicalFormatNativeInFeedMainImageSizesItem as CanonicalFormatNativeInFeedMainImageSizesItem
from .formats import CanonicalFormatNativeInFeedMenuPlacement as CanonicalFormatNativeInFeedMenuPlacement
from .formats import CanonicalFormatResponsiveCreative as CanonicalFormatResponsiveCreative
from .formats import CanonicalFormatSellerRenderedStatefulDisplay as CanonicalFormatSellerRenderedStatefulDisplay
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayContainersItem as CanonicalFormatSellerRenderedStatefulDisplayContainersItem,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayReveal as CanonicalFormatSellerRenderedStatefulDisplayReveal,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayStatesItem as CanonicalFormatSellerRenderedStatefulDisplayStatesItem,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayStatesItemAnchoring as CanonicalFormatSellerRenderedStatefulDisplayStatesItemAnchoring,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItem as CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItem,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItemWidthMode as CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItemWidthMode,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayStatesItemMotion as CanonicalFormatSellerRenderedStatefulDisplayStatesItemMotion,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplaySupplyMode as CanonicalFormatSellerRenderedStatefulDisplaySupplyMode,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItem as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItem,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemDirection as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemDirection,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemInput as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemInput,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemMediaEvent as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemMediaEvent,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemScrollReference as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemScrollReference,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTransitionMode as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTransitionMode,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTrigger as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTrigger,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayUserControls as CanonicalFormatSellerRenderedStatefulDisplayUserControls,
)
from .formats import (
    CanonicalFormatSellerRenderedStatefulDisplayVideoPlayback as CanonicalFormatSellerRenderedStatefulDisplayVideoPlayback,
)
from .formats import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven as CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven,
)
from .formats import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenFanoutMode as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenFanoutMode,
)
from .formats import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenItemProductionModel as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenItemProductionModel,
)
from .formats import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenSupportedIdTypesItem as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenSupportedIdTypesItem,
)
from .formats import CanonicalFormatVASTAudio as CanonicalFormatVASTAudio
from .formats import CanonicalFormatVASTVideo as CanonicalFormatVASTVideo
from .formats import CanonicalFormatVASTVideoCreativeType as CanonicalFormatVASTVideoCreativeType
from .formats import CanonicalFormatVASTVideoVpaidVersion as CanonicalFormatVASTVideoVpaidVersion
from .formats import ComponentsItemFormatKindParams as ComponentsItemFormatKindParams
from .formats import ComponentsItemFormatKindParamsAgentPlacement as ComponentsItemFormatKindParamsAgentPlacement
from .formats import ComponentsItemFormatKindParamsAudioDaast as ComponentsItemFormatKindParamsAudioDaast
from .formats import ComponentsItemFormatKindParamsAudioHosted as ComponentsItemFormatKindParamsAudioHosted
from .formats import ComponentsItemFormatKindParamsDisplayTag as ComponentsItemFormatKindParamsDisplayTag
from .formats import ComponentsItemFormatKindParamsHtml5 as ComponentsItemFormatKindParamsHtml5
from .formats import ComponentsItemFormatKindParamsImage as ComponentsItemFormatKindParamsImage
from .formats import ComponentsItemFormatKindParamsImageCarousel as ComponentsItemFormatKindParamsImageCarousel
from .formats import ComponentsItemFormatKindParamsNativeInFeed as ComponentsItemFormatKindParamsNativeInFeed
from .formats import (
    ComponentsItemFormatKindParamsResponsiveCreative as ComponentsItemFormatKindParamsResponsiveCreative,
)
from .formats import (
    ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay as ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay,
)
from .formats import (
    ComponentsItemFormatKindParamsSponsoredPlacement as ComponentsItemFormatKindParamsSponsoredPlacement,
)
from .formats import ComponentsItemFormatKindParamsVideoHosted as ComponentsItemFormatKindParamsVideoHosted
from .formats import ComponentsItemFormatKindParamsVideoVast as ComponentsItemFormatKindParamsVideoVast
from .formats import ComponentsItemFormatOptionRef as ComponentsItemFormatOptionRef
from .formats import TransitionsItemInViewTimer as TransitionsItemInViewTimer
from .formats import TransitionsItemMediaEvent as TransitionsItemMediaEvent
from .formats import TransitionsItemScrollProgressScrollScrollLinked as TransitionsItemScrollProgressScrollScrollLinked
from .formats import TransitionsItemScrollThresholdScroll as TransitionsItemScrollThresholdScroll
from .formats import TransitionsItemTimer as TransitionsItemTimer
from .formats import TransitionsItemTimerTransitionMode as TransitionsItemTimerTransitionMode
from .formats import TransitionsItemUserAction as TransitionsItemUserAction
from .governance import AcceptedGovernanceAgents as AcceptedGovernanceAgents
from .governance import AnyOfItemAgentUrl as AnyOfItemAgentUrl
from .governance import AnyOfItemVerification as AnyOfItemVerification
from .governance import AttributeDefinition as AttributeDefinition
from .governance import AttributeDefinitionRegulatoryBasisItem as AttributeDefinitionRegulatoryBasisItem
from .governance import AudienceConstraints as AudienceConstraints
from .governance import BoundedObject as BoundedObject
from .governance import BoundedScalar as BoundedScalar
from .governance import BoundedValue as BoundedValue
from .governance import BoundedValueLevel2 as BoundedValueLevel2
from .governance import BoundedValueLevel3 as BoundedValueLevel3
from .governance import BudgetReallocationThreshold as BudgetReallocationThreshold
from .governance import BudgetReallocationUnlimited as BudgetReallocationUnlimited
from .governance import CheckGovernanceRequest as CheckGovernanceRequest
from .governance import CheckGovernanceRequestDeliveryMetrics as CheckGovernanceRequestDeliveryMetrics
from .governance import (
    CheckGovernanceRequestDeliveryMetricsAudienceDistribution as CheckGovernanceRequestDeliveryMetricsAudienceDistribution,
)
from .governance import (
    CheckGovernanceRequestDeliveryMetricsAudienceDistributionBaseline as CheckGovernanceRequestDeliveryMetricsAudienceDistributionBaseline,
)
from .governance import CheckGovernanceRequestDeliveryMetricsPacing as CheckGovernanceRequestDeliveryMetricsPacing
from .governance import CheckGovernanceRequestRuntimeAttestationsItem as CheckGovernanceRequestRuntimeAttestationsItem
from .governance import (
    CheckGovernanceRequestRuntimeAttestationsItemSubject as CheckGovernanceRequestRuntimeAttestationsItemSubject,
)
from .governance import CheckGovernanceResponse as CheckGovernanceResponse
from .governance import CheckGovernanceResponseCheckType as CheckGovernanceResponseCheckType
from .governance import CheckGovernanceResponseConditionsItem as CheckGovernanceResponseConditionsItem
from .governance import CheckGovernanceResponseDeliveryStatement as CheckGovernanceResponseDeliveryStatement
from .governance import (
    CheckGovernanceResponseDeliveryStatementCanonicalPayload as CheckGovernanceResponseDeliveryStatementCanonicalPayload,
)
from .governance import CheckGovernanceResponseFindingsItem as CheckGovernanceResponseFindingsItem
from .governance import (
    CheckGovernanceResponseRuntimeAttestationEvaluationsItem as CheckGovernanceResponseRuntimeAttestationEvaluationsItem,
)
from .governance import (
    CheckGovernanceResponseRuntimeAttestationEvaluationsItemActionBinding as CheckGovernanceResponseRuntimeAttestationEvaluationsItemActionBinding,
)
from .governance import GetPlanAuditLogsRequest as GetPlanAuditLogsRequest
from .governance import GetPlanAuditLogsResponse as GetPlanAuditLogsResponse
from .governance import GetPlanAuditLogsResponsePlansItem as GetPlanAuditLogsResponsePlansItem
from .governance import GetPlanAuditLogsResponsePlansItemBudget as GetPlanAuditLogsResponsePlansItemBudget
from .governance import (
    GetPlanAuditLogsResponsePlansItemBudgetAccountingMode as GetPlanAuditLogsResponsePlansItemBudgetAccountingMode,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemChannelAllocationValue as GetPlanAuditLogsResponsePlansItemChannelAllocationValue,
)
from .governance import GetPlanAuditLogsResponsePlansItemEntriesItem as GetPlanAuditLogsResponsePlansItemEntriesItem
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentState as GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentState,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentType as GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentType,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemAmount as GetPlanAuditLogsResponsePlansItemEntriesItemAmount,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemDelivery as GetPlanAuditLogsResponsePlansItemEntriesItemDelivery,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemDeliveryPeriodState as GetPlanAuditLogsResponsePlansItemEntriesItemDeliveryPeriodState,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemDeliverySource as GetPlanAuditLogsResponsePlansItemEntriesItemDeliverySource,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemEvidence as GetPlanAuditLogsResponsePlansItemEntriesItemEvidence,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemEvidenceEvidenceType as GetPlanAuditLogsResponsePlansItemEntriesItemEvidenceEvidenceType,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemRuntimeAttestationsItem as GetPlanAuditLogsResponsePlansItemEntriesItemRuntimeAttestationsItem,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemEntriesItemType as GetPlanAuditLogsResponsePlansItemEntriesItemType,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemGovernedActionsItem as GetPlanAuditLogsResponsePlansItemGovernedActionsItem,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemGovernedActionsItemDeliveryPeriodState as GetPlanAuditLogsResponsePlansItemGovernedActionsItemDeliveryPeriodState,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemGovernedActionsItemStatus as GetPlanAuditLogsResponsePlansItemGovernedActionsItemStatus,
)
from .governance import GetPlanAuditLogsResponsePlansItemStatus as GetPlanAuditLogsResponsePlansItemStatus
from .governance import GetPlanAuditLogsResponsePlansItemSummary as GetPlanAuditLogsResponsePlansItemSummary
from .governance import (
    GetPlanAuditLogsResponsePlansItemSummaryDriftMetrics as GetPlanAuditLogsResponsePlansItemSummaryDriftMetrics,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsEscalationRateTrend as GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsEscalationRateTrend,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsThresholds as GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsThresholds,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemSummaryEscalationsItem as GetPlanAuditLogsResponsePlansItemSummaryEscalationsItem,
)
from .governance import (
    GetPlanAuditLogsResponsePlansItemSummaryStatuses as GetPlanAuditLogsResponsePlansItemSummaryStatuses,
)
from .governance import (
    GovernedActionsItemDeliveryReconciliationStatus as GovernedActionsItemDeliveryReconciliationStatus,
)
from .governance import PolicyCategoryDefinition as PolicyCategoryDefinition
from .governance import PolicyCategoryDefinitionFacetsItem as PolicyCategoryDefinitionFacetsItem
from .governance import (
    PolicyCategoryDefinitionRegulatoryFrameworksItem as PolicyCategoryDefinitionRegulatoryFrameworksItem,
)
from .governance import PolicyEntry as PolicyEntry
from .governance import PolicyEntryExemplar as PolicyEntryExemplar
from .governance import PolicyEntryExemplars as PolicyEntryExemplars
from .governance import PolicyEntryIssuer as PolicyEntryIssuer
from .governance import PolicyEntrySource as PolicyEntrySource
from .governance import PolicyReference as PolicyReference
from .governance import ReportedOutcomeError as ReportedOutcomeError
from .governance import ReportedOutcomeErrorClassificationSource as ReportedOutcomeErrorClassificationSource
from .governance import ReportPlanAdjustmentRequest as ReportPlanAdjustmentRequest
from .governance import ReportPlanAdjustmentRequestAction as ReportPlanAdjustmentRequestAction
from .governance import ReportPlanAdjustmentRequestDecision as ReportPlanAdjustmentRequestDecision
from .governance import ReportPlanAdjustmentRequestEvidence as ReportPlanAdjustmentRequestEvidence
from .governance import ReportPlanAdjustmentResponse as ReportPlanAdjustmentResponse
from .governance import ReportPlanAdjustmentResponsePlanSummary as ReportPlanAdjustmentResponsePlanSummary
from .governance import ReportPlanOutcomeRequest as ReportPlanOutcomeRequest
from .governance import ReportPlanOutcomeRequestDelivery as ReportPlanOutcomeRequestDelivery
from .governance import ReportPlanOutcomeRequestSellerResponse as ReportPlanOutcomeRequestSellerResponse
from .governance import (
    ReportPlanOutcomeRequestSellerResponsePackagesItem as ReportPlanOutcomeRequestSellerResponsePackagesItem,
)
from .governance import ReportPlanOutcomeResponse as ReportPlanOutcomeResponse
from .governance import ReportPlanOutcomeResponseDeliveryPeriodState as ReportPlanOutcomeResponseDeliveryPeriodState
from .governance import ReportPlanOutcomeResponseFindingsItem as ReportPlanOutcomeResponseFindingsItem
from .governance import ReportPlanOutcomeResponseOutcomeState as ReportPlanOutcomeResponseOutcomeState
from .governance import ReportPlanOutcomeResponsePlanSummary as ReportPlanOutcomeResponsePlanSummary
from .governance import SyncPlansRequest as SyncPlansRequest
from .governance import SyncPlansRequestPlansItem as SyncPlansRequestPlansItem
from .governance import SyncPlansRequestPlansItemBudget as SyncPlansRequestPlansItemBudget
from .governance import (
    SyncPlansRequestPlansItemBudgetAllocationsValue as SyncPlansRequestPlansItemBudgetAllocationsValue,
)
from .governance import SyncPlansRequestPlansItemChannels as SyncPlansRequestPlansItemChannels
from .governance import (
    SyncPlansRequestPlansItemChannelsMixTargetsValue as SyncPlansRequestPlansItemChannelsMixTargetsValue,
)
from .governance import SyncPlansRequestPlansItemDelegationsItem as SyncPlansRequestPlansItemDelegationsItem
from .governance import (
    SyncPlansRequestPlansItemDelegationsItemBudgetLimit as SyncPlansRequestPlansItemDelegationsItemBudgetLimit,
)
from .governance import SyncPlansRequestPlansItemPortfolio as SyncPlansRequestPlansItemPortfolio
from .governance import (
    SyncPlansRequestPlansItemPortfolioTotalBudgetCap as SyncPlansRequestPlansItemPortfolioTotalBudgetCap,
)
from .governance import SyncPlansResponse as SyncPlansResponse
from .governance import SyncPlansResponsePlansItem as SyncPlansResponsePlansItem
from .governance import SyncPlansResponsePlansItemCategoriesItem as SyncPlansResponsePlansItemCategoriesItem
from .governance import SyncPlansResponsePlansItemCategoriesItemStatus as SyncPlansResponsePlansItemCategoriesItemStatus
from .governance import SyncPlansResponsePlansItemResolvedPoliciesItem as SyncPlansResponsePlansItemResolvedPoliciesItem
from .governance import (
    SyncPlansResponsePlansItemResolvedPoliciesItemSource as SyncPlansResponsePlansItemResolvedPoliciesItemSource,
)
from .governance import SyncPlansResponsePlansItemStatus as SyncPlansResponsePlansItemStatus
from .media_buy import AcceptanceContext as AcceptanceContext
from .media_buy import AcceptanceContextSubjectsItem as AcceptanceContextSubjectsItem
from .media_buy import AcceptancePolicyCatalog as AcceptancePolicyCatalog
from .media_buy import AcceptancePolicyProfile as AcceptancePolicyProfile
from .media_buy import AcceptancePolicyProfileCoverage as AcceptancePolicyProfileCoverage
from .media_buy import AcceptancePolicyProfilePolicyRefsItem as AcceptancePolicyProfilePolicyRefsItem
from .media_buy import AcceptancePolicyProfileScope as AcceptancePolicyProfileScope
from .media_buy import AcceptancePolicyRequirement as AcceptancePolicyRequirement
from .media_buy import AcceptancePolicyRequirementAccountSetup as AcceptancePolicyRequirementAccountSetup
from .media_buy import (
    AcceptancePolicyRequirementAdvertiserEligibility as AcceptancePolicyRequirementAdvertiserEligibility,
)
from .media_buy import (
    AcceptancePolicyRequirementAdvertiserVerification as AcceptancePolicyRequirementAdvertiserVerification,
)
from .media_buy import AcceptancePolicyRequirementCategoryDeclaration as AcceptancePolicyRequirementCategoryDeclaration
from .media_buy import AcceptancePolicyRequirementCertification as AcceptancePolicyRequirementCertification
from .media_buy import AcceptancePolicyRequirementCreativeRestriction as AcceptancePolicyRequirementCreativeRestriction
from .media_buy import AcceptancePolicyRequirementCustom as AcceptancePolicyRequirementCustom
from .media_buy import (
    AcceptancePolicyRequirementDestinationRestriction as AcceptancePolicyRequirementDestinationRestriction,
)
from .media_buy import AcceptancePolicyRequirementDisclosure as AcceptancePolicyRequirementDisclosure
from .media_buy import AcceptancePolicyRequirementFormatRestriction as AcceptancePolicyRequirementFormatRestriction
from .media_buy import AcceptancePolicyRequirementFundingRestriction as AcceptancePolicyRequirementFundingRestriction
from .media_buy import AcceptancePolicyRequirementLicense as AcceptancePolicyRequirementLicense
from .media_buy import AcceptancePolicyRequirementPriorAuthorization as AcceptancePolicyRequirementPriorAuthorization
from .media_buy import AcceptancePolicyRequirementSalesAssisted as AcceptancePolicyRequirementSalesAssisted
from .media_buy import (
    AcceptancePolicyRequirementTargetingRestriction as AcceptancePolicyRequirementTargetingRestriction,
)
from .media_buy import AcceptancePolicyRequirementTimeRestriction as AcceptancePolicyRequirementTimeRestriction
from .media_buy import (
    AcceptancePolicyRequirementTransparencyReporting as AcceptancePolicyRequirementTransparencyReporting,
)
from .media_buy import AcceptancePolicyRule as AcceptancePolicyRule
from .media_buy import AcceptancePolicyRuleAppliesToItem as AcceptancePolicyRuleAppliesToItem
from .media_buy import AcceptancePolicyRuleDisposition as AcceptancePolicyRuleDisposition
from .media_buy import AcceptProposalInputRequired as AcceptProposalInputRequired
from .media_buy import AcceptProposalRequest as AcceptProposalRequest
from .media_buy import AcceptProposalRequestIoAcceptance as AcceptProposalRequestIoAcceptance
from .media_buy import AcceptProposalRequestOpportunity as AcceptProposalRequestOpportunity
from .media_buy import AcceptProposalResponse as AcceptProposalResponse
from .media_buy import AcceptProposalSubmitted as AcceptProposalSubmitted
from .media_buy import AcceptProposalWorking as AcceptProposalWorking
from .media_buy import AgencyEstimateNumber as AgencyEstimateNumber
from .media_buy import AudienceEvidencePins as AudienceEvidencePins
from .media_buy import Budget as Budget
from .media_buy import BudgetChangeConstraints as BudgetChangeConstraints
from .media_buy import BuildCreativeError as BuildCreativeError
from .media_buy import BuildCreativeEstimate as BuildCreativeEstimate
from .media_buy import BuildCreativeEstimateEstimate as BuildCreativeEstimateEstimate
from .media_buy import BuildCreativeEstimateEstimateBasis as BuildCreativeEstimateEstimateBasis
from .media_buy import BuildCreativeEstimateEstimatePerLeafItem as BuildCreativeEstimateEstimatePerLeafItem
from .media_buy import BuildCreativeInputRequired as BuildCreativeInputRequired
from .media_buy import BuildCreativeInputRequiredReason as BuildCreativeInputRequiredReason
from .media_buy import BuildCreativeMultiSuccess as BuildCreativeMultiSuccess
from .media_buy import BuildCreativeMultiSuccessPreview as BuildCreativeMultiSuccessPreview
from .media_buy import BuildCreativeMultiSuccessPreviewPreviewsItem as BuildCreativeMultiSuccessPreviewPreviewsItem
from .media_buy import (
    BuildCreativeMultiSuccessPreviewPreviewsItemInput as BuildCreativeMultiSuccessPreviewPreviewsItemInput,
)
from .media_buy import BuildCreativeRequest as BuildCreativeRequest
from .media_buy import BuildCreativeRequestMaxSpend as BuildCreativeRequestMaxSpend
from .media_buy import BuildCreativeRequestMode as BuildCreativeRequestMode
from .media_buy import BuildCreativeRequestSignalConditionsItem as BuildCreativeRequestSignalConditionsItem
from .media_buy import BuildCreativeRequestVariantAxis as BuildCreativeRequestVariantAxis
from .media_buy import BuildCreativeRequestVariantAxisDimension as BuildCreativeRequestVariantAxisDimension
from .media_buy import BuildCreativeResponse as BuildCreativeResponse
from .media_buy import BuildCreativeResponseSubmitted as BuildCreativeResponseSubmitted
from .media_buy import BuildCreativeSubmitted as BuildCreativeSubmitted
from .media_buy import BuildCreativeSuccess as BuildCreativeSuccess
from .media_buy import BuildCreativeSuccessPreview as BuildCreativeSuccessPreview
from .media_buy import BuildCreativeSuccessPreviewPreviewsItem as BuildCreativeSuccessPreviewPreviewsItem
from .media_buy import BuildCreativeSuccessPreviewPreviewsItemInput as BuildCreativeSuccessPreviewPreviewsItemInput
from .media_buy import BuildCreativeVariantSuccess as BuildCreativeVariantSuccess
from .media_buy import BuildCreativeVariantSuccessBudgetStatus as BuildCreativeVariantSuccessBudgetStatus
from .media_buy import BuildCreativeVariantSuccessCreativesItem as BuildCreativeVariantSuccessCreativesItem
from .media_buy import (
    BuildCreativeVariantSuccessCreativesItemCatalogItemRef as BuildCreativeVariantSuccessCreativesItemCatalogItemRef,
)
from .media_buy import (
    BuildCreativeVariantSuccessCreativesItemVariantsItem as BuildCreativeVariantSuccessCreativesItemVariantsItem,
)
from .media_buy import (
    BuildCreativeVariantSuccessCreativesItemVariantsItemEval as BuildCreativeVariantSuccessCreativesItemVariantsItemEval,
)
from .media_buy import BuildCreativeVariantSuccessKeepModeApplied as BuildCreativeVariantSuccessKeepModeApplied
from .media_buy import BuildCreativeWorking as BuildCreativeWorking
from .media_buy import BuyProductsInputRequired as BuyProductsInputRequired
from .media_buy import BuyProductsRequest as BuyProductsRequest
from .media_buy import BuyProductsRequestBranch1Account as BuyProductsRequestBranch1Account
from .media_buy import BuyProductsRequestBranch1AccountAccountId as BuyProductsRequestBranch1AccountAccountId
from .media_buy import BuyProductsRequestBranch1AccountBrandOperator as BuyProductsRequestBranch1AccountBrandOperator
from .media_buy import BuyProductsRequestBrand as BuyProductsRequestBrand
from .media_buy import BuyProductsRequestOpportunity as BuyProductsRequestOpportunity
from .media_buy import BuyProductsResponse as BuyProductsResponse
from .media_buy import BuyProductsSubmitted as BuyProductsSubmitted
from .media_buy import BuyProductsWorking as BuyProductsWorking
from .media_buy import CatalogIds as CatalogIds
from .media_buy import CommercialTerms as CommercialTerms
from .media_buy import CommercialTermsCancellationTerms as CommercialTermsCancellationTerms
from .media_buy import CommercialTermsPurchasesItem as CommercialTermsPurchasesItem
from .media_buy import CommercialTermsReportingCommitmentsItem as CommercialTermsReportingCommitmentsItem
from .media_buy import CommitmentError as CommitmentError
from .media_buy import CommitmentSubmitted as CommitmentSubmitted
from .media_buy import CommittedMediaBuy as CommittedMediaBuy
from .media_buy import CommittedMediaBuyAcceptedProposal as CommittedMediaBuyAcceptedProposal
from .media_buy import CommittedMediaBuyPurchaseBindingsItem as CommittedMediaBuyPurchaseBindingsItem
from .media_buy import CommittedMediaBuyWarningsItem as CommittedMediaBuyWarningsItem
from .media_buy import CommittedMediaBuyWarningsItemCode as CommittedMediaBuyWarningsItemCode
from .media_buy import CommittedMetricsItemVendor as CommittedMetricsItemVendor
from .media_buy import CommittedProposalExecution as CommittedProposalExecution
from .media_buy import CompatibilityPurchaseCoordinatorInput as CompatibilityPurchaseCoordinatorInput
from .media_buy import ControlApplied as ControlApplied
from .media_buy import ControlAppliedWarningsItem as ControlAppliedWarningsItem
from .media_buy import ControlError as ControlError
from .media_buy import ControlMediaBuyInputRequired as ControlMediaBuyInputRequired
from .media_buy import ControlMediaBuyRequest as ControlMediaBuyRequest
from .media_buy import ControlMediaBuyResponse as ControlMediaBuyResponse
from .media_buy import ControlMediaBuySubmitted as ControlMediaBuySubmitted
from .media_buy import ControlMediaBuyWorking as ControlMediaBuyWorking
from .media_buy import ControlSubmitted as ControlSubmitted
from .media_buy import CreateMediaBuyError as CreateMediaBuyError
from .media_buy import CreateMediaBuyInputRequired as CreateMediaBuyInputRequired
from .media_buy import CreateMediaBuyInputRequiredReason as CreateMediaBuyInputRequiredReason
from .media_buy import CreateMediaBuyRequest as CreateMediaBuyRequest
from .media_buy import CreateMediaBuyRequestArtifactWebhook as CreateMediaBuyRequestArtifactWebhook
from .media_buy import (
    CreateMediaBuyRequestArtifactWebhookBatchFrequency as CreateMediaBuyRequestArtifactWebhookBatchFrequency,
)
from .media_buy import (
    CreateMediaBuyRequestArtifactWebhookDeliveryMode as CreateMediaBuyRequestArtifactWebhookDeliveryMode,
)
from .media_buy import CreateMediaBuyRequestBidding as CreateMediaBuyRequestBidding
from .media_buy import CreateMediaBuyRequestIoAcceptance as CreateMediaBuyRequestIoAcceptance
from .media_buy import CreateMediaBuyRequestOpportunity as CreateMediaBuyRequestOpportunity
from .media_buy import CreateMediaBuyResponse as CreateMediaBuyResponse
from .media_buy import CreateMediaBuyResponseSubmitted as CreateMediaBuyResponseSubmitted
from .media_buy import CreateMediaBuySubmitted as CreateMediaBuySubmitted
from .media_buy import CreateMediaBuySuccess as CreateMediaBuySuccess
from .media_buy import CreateMediaBuySuccessBidding as CreateMediaBuySuccessBidding
from .media_buy import CreateMediaBuyWorking as CreateMediaBuyWorking
from .media_buy import (
    CreativeApprovalsItemIndicatorTypesEvaluatedItem as CreativeApprovalsItemIndicatorTypesEvaluatedItem,
)
from .media_buy import DailyBudgetCap as DailyBudgetCap
from .media_buy import DeclineProposalsInputRequired as DeclineProposalsInputRequired
from .media_buy import DeclineProposalsRequest as DeclineProposalsRequest
from .media_buy import DeclineProposalsResponse as DeclineProposalsResponse
from .media_buy import DeclineProposalsResponseResults as DeclineProposalsResponseResults
from .media_buy import DeclineProposalsResponseResultsItem as DeclineProposalsResponseResultsItem
from .media_buy import DeclineProposalsResponseResultsItemOutcome as DeclineProposalsResponseResultsItemOutcome
from .media_buy import DeclineProposalsResponseResultsItemUnable as DeclineProposalsResponseResultsItemUnable
from .media_buy import DeclineProposalsResponseSubmitted as DeclineProposalsResponseSubmitted
from .media_buy import DeclineProposalsSubmitted as DeclineProposalsSubmitted
from .media_buy import DeclineProposalsWorking as DeclineProposalsWorking
from .media_buy import EffectiveTimingConstraints as EffectiveTimingConstraints
from .media_buy import EndTime as EndTime
from .media_buy import ExplicitPackagesWithFixedAllocation as ExplicitPackagesWithFixedAllocation
from .media_buy import (
    ExplicitPackagesWithFixedAllocationBudgetAllocation as ExplicitPackagesWithFixedAllocationBudgetAllocation,
)
from .media_buy import (
    ExplicitPackagesWithFixedAllocationPackagesItem as ExplicitPackagesWithFixedAllocationPackagesItem,
)
from .media_buy import ExplicitPackagesWithSellerOptimizedAllocation as ExplicitPackagesWithSellerOptimizedAllocation
from .media_buy import (
    ExplicitPackagesWithSellerOptimizedAllocationBudgetAllocation as ExplicitPackagesWithSellerOptimizedAllocationBudgetAllocation,
)
from .media_buy import FailedLookup as FailedLookup
from .media_buy import FailedReportingConsumerStatus as FailedReportingConsumerStatus
from .media_buy import FailedReportingReceipt as FailedReportingReceipt
from .media_buy import FlightChangeConstraints as FlightChangeConstraints
from .media_buy import FormatOptionRefs as FormatOptionRefs
from .media_buy import GetMediaBuyDeliveryRequest as GetMediaBuyDeliveryRequest
from .media_buy import GetMediaBuyDeliveryRequestReportingDimensions as GetMediaBuyDeliveryRequestReportingDimensions
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsAudience as GetMediaBuyDeliveryRequestReportingDimensionsAudience,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsDemographic as GetMediaBuyDeliveryRequestReportingDimensionsDemographic,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsDevicePlatform as GetMediaBuyDeliveryRequestReportingDimensionsDevicePlatform,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsDeviceType as GetMediaBuyDeliveryRequestReportingDimensionsDeviceType,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsGeo as GetMediaBuyDeliveryRequestReportingDimensionsGeo,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsPlacement as GetMediaBuyDeliveryRequestReportingDimensionsPlacement,
)
from .media_buy import (
    GetMediaBuyDeliveryRequestReportingDimensionsSpot as GetMediaBuyDeliveryRequestReportingDimensionsSpot,
)
from .media_buy import GetMediaBuyDeliveryResponse as GetMediaBuyDeliveryResponse
from .media_buy import GetMediaBuyDeliveryResponseAggregatedTotals as GetMediaBuyDeliveryResponseAggregatedTotals
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByAudienceItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByAudienceItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDemographicItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDemographicItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDevicePlatformItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDevicePlatformItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDeviceTypeItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDeviceTypeItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByFormatItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByFormatItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemBySpotItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemBySpotItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemDailyBreakdownItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemDailyBreakdownItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemDailyBreakdownItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemDailyBreakdownItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemTotals as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemTotals,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemByPackageItem as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemByPackageItem,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemTotals as GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemTotals,
)
from .media_buy import (
    GetMediaBuyDeliveryResponseReportingRevisionBinding as GetMediaBuyDeliveryResponseReportingRevisionBinding,
)
from .media_buy import GetMediaBuysRequest as GetMediaBuysRequest
from .media_buy import GetMediaBuysResponse as GetMediaBuysResponse
from .media_buy import GetMediaBuysResponseMediaBuysItem as GetMediaBuysResponseMediaBuysItem
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemAcceptedProposal as GetMediaBuysResponseMediaBuysItemAcceptedProposal,
)
from .media_buy import GetMediaBuysResponseMediaBuysItemBidding as GetMediaBuysResponseMediaBuysItemBidding
from .media_buy import GetMediaBuysResponseMediaBuysItemHistoryItem as GetMediaBuysResponseMediaBuysItemHistoryItem
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemIndicatorsItem as GetMediaBuysResponseMediaBuysItemIndicatorsItem,
)
from .media_buy import GetMediaBuysResponseMediaBuysItemPackagesItem as GetMediaBuysResponseMediaBuysItemPackagesItem
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemPackagesItemBidding as GetMediaBuysResponseMediaBuysItemPackagesItemBidding,
)
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemPackagesItemCreativeApprovalsItem as GetMediaBuysResponseMediaBuysItemPackagesItemCreativeApprovalsItem,
)
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemPackagesItemIndicatorsItem as GetMediaBuysResponseMediaBuysItemPackagesItemIndicatorsItem,
)
from .media_buy import (
    GetMediaBuysResponseMediaBuysItemPackagesItemSnapshot as GetMediaBuysResponseMediaBuysItemPackagesItemSnapshot,
)
from .media_buy import GetProductsInputRequired as GetProductsInputRequired
from .media_buy import GetProductsInputRequiredReason as GetProductsInputRequiredReason
from .media_buy import GetProductsRejected as GetProductsRejected
from .media_buy import GetProductsRequest as GetProductsRequest
from .media_buy import GetProductsRequestBuyingMode as GetProductsRequestBuyingMode
from .media_buy import GetProductsRequestFieldsItem as GetProductsRequestFieldsItem
from .media_buy import GetProductsRequestRefineItemProductAction as GetProductsRequestRefineItemProductAction
from .media_buy import GetProductsRequestRefineItemProposalAction as GetProductsRequestRefineItemProposalAction
from .media_buy import GetProductsRequestTimeBudget as GetProductsRequestTimeBudget
from .media_buy import GetProductsResponse as GetProductsResponse
from .media_buy import GetProductsResponseCacheScope as GetProductsResponseCacheScope
from .media_buy import GetProductsResponseFilterDiagnostics as GetProductsResponseFilterDiagnostics
from .media_buy import (
    GetProductsResponseFilterDiagnosticsExcludedByValue as GetProductsResponseFilterDiagnosticsExcludedByValue,
)
from .media_buy import GetProductsResponseFilterDiagnosticsSemantics as GetProductsResponseFilterDiagnosticsSemantics
from .media_buy import GetProductsResponseIncompleteItem as GetProductsResponseIncompleteItem
from .media_buy import GetProductsResponseIncompleteItemEstimatedWait as GetProductsResponseIncompleteItemEstimatedWait
from .media_buy import GetProductsResponseIncompleteItemScope as GetProductsResponseIncompleteItemScope
from .media_buy import GetProductsSubmitted as GetProductsSubmitted
from .media_buy import GetProductsWorking as GetProductsWorking
from .media_buy import GetReportingStatusRequest as GetReportingStatusRequest
from .media_buy import GetReportingStatusRequestReportingStatusView as GetReportingStatusRequestReportingStatusView
from .media_buy import GetReportingStatusResponse as GetReportingStatusResponse
from .media_buy import GetReportingStatusResponseObligationCounts as GetReportingStatusResponseObligationCounts
from .media_buy import GetReportingStatusResponseScope as GetReportingStatusResponseScope
from .media_buy import (
    GetReportingStatusResponseScopeDeliveryConfigGenerationsItem as GetReportingStatusResponseScopeDeliveryConfigGenerationsItem,
)
from .media_buy import GoalEvent as GoalEvent
from .media_buy import GoalMetric as GoalMetric
from .media_buy import ListCreativeFormatsRequest as ListCreativeFormatsRequest
from .media_buy import ListCreativeFormatsResponse as ListCreativeFormatsResponse
from .media_buy import ListCreativeFormatsResponseSource as ListCreativeFormatsResponseSource
from .media_buy import ListProductsRequest as ListProductsRequest
from .media_buy import ListProductsRequestPushNotificationConfig as ListProductsRequestPushNotificationConfig
from .media_buy import ListProductsResponse as ListProductsResponse
from .media_buy import ListProductsResponseIncompleteItem as ListProductsResponseIncompleteItem
from .media_buy import ListProductsResponseIncompleteItemScope as ListProductsResponseIncompleteItemScope
from .media_buy import ListProductsResponseListed as ListProductsResponseListed
from .media_buy import ListProductsResponseOutcome as ListProductsResponseOutcome
from .media_buy import ListProductsResponseUnchanged as ListProductsResponseUnchanged
from .media_buy import LogEventError as LogEventError
from .media_buy import LogEventRequest as LogEventRequest
from .media_buy import LogEventResponse as LogEventResponse
from .media_buy import LogEventSuccess as LogEventSuccess
from .media_buy import LogEventSuccessPartialFailuresItem as LogEventSuccessPartialFailuresItem
from .media_buy import MediaBuyChangeTerm as MediaBuyChangeTerm
from .media_buy import MediaBuyChangeTermAllowedStatusesItem as MediaBuyChangeTermAllowedStatusesItem
from .media_buy import MediaBuyChangeTermConstraints as MediaBuyChangeTermConstraints
from .media_buy import MediaBuyChangeTermConstraintsMoney as MediaBuyChangeTermConstraintsMoney
from .media_buy import MediaBuyCommitmentResponse as MediaBuyCommitmentResponse
from .media_buy import MediaBuyDeliveryWebhookResult as MediaBuyDeliveryWebhookResult
from .media_buy import (
    MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItem as MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItem,
)
from .media_buy import (
    MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemByPackageItem as MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemByPackageItem,
)
from .media_buy import (
    MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus as MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus,
)
from .media_buy import (
    MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemTotals as MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemTotals,
)
from .media_buy import MediaBuyDeliveryWebhookResultNotificationType as MediaBuyDeliveryWebhookResultNotificationType
from .media_buy import MediaBuyDeliveryWebhookResultReportingPeriod as MediaBuyDeliveryWebhookResultReportingPeriod
from .media_buy import MediaBuysItemIndicatorsItemType as MediaBuysItemIndicatorsItemType
from .media_buy import MinSpendTarget as MinSpendTarget
from .media_buy import ObjScopeAsk as ObjScopeAsk
from .media_buy import ObjScopeProductIdActionAsk as ObjScopeProductIdActionAsk
from .media_buy import ObjScopeProposalIdActionAsk as ObjScopeProposalIdActionAsk
from .media_buy import OperationalFailure as OperationalFailure
from .media_buy import OptimizationGoals as OptimizationGoals
from .media_buy import OutcomeTarget as OutcomeTarget
from .media_buy import PackageControl as PackageControl
from .media_buy import PackageCountConstraints as PackageCountConstraints
from .media_buy import PackageRequest as PackageRequest
from .media_buy import PackageRequestBidding as PackageRequestBidding
from .media_buy import PackagesItemIndicatorsItemType as PackagesItemIndicatorsItemType
from .media_buy import PackageUpdate as PackageUpdate
from .media_buy import PerformanceStandards as PerformanceStandards
from .media_buy import PeriodsView as PeriodsView
from .media_buy import PricingOptionId as PricingOptionId
from .media_buy import ProductDiscoveryCriteria as ProductDiscoveryCriteria
from .media_buy import ProductDiscoveryCriteriaOutcomeTarget as ProductDiscoveryCriteriaOutcomeTarget
from .media_buy import ProductDiscoveryTargetingResolution as ProductDiscoveryTargetingResolution
from .media_buy import ProductId as ProductId
from .media_buy import ProductPurchase as ProductPurchase
from .media_buy import ProductPurchaseInput as ProductPurchaseInput
from .media_buy import ProductRefinementRequests as ProductRefinementRequests
from .media_buy import ProductResponseFields as ProductResponseFields
from .media_buy import ProductResponseFieldsItem as ProductResponseFieldsItem
from .media_buy import ProposalBudgetConstraint as ProposalBudgetConstraint
from .media_buy import ProposalDecline as ProposalDecline
from .media_buy import ProposalRefinement as ProposalRefinement
from .media_buy import ProposalRefinementAction as ProposalRefinementAction
from .media_buy import ProposalRefinementAlternatives as ProposalRefinementAlternatives
from .media_buy import ProposalRefinementChangeKind as ProposalRefinementChangeKind
from .media_buy import ProposalRefinementConstraints as ProposalRefinementConstraints
from .media_buy import ProposalRefinementConstraintsCpm as ProposalRefinementConstraintsCpm
from .media_buy import ProposalRefinementConstraintsFlight as ProposalRefinementConstraintsFlight
from .media_buy import ProposalRefinementConstraintsImpressions as ProposalRefinementConstraintsImpressions
from .media_buy import ProposalRefinementFinalize as ProposalRefinementFinalize
from .media_buy import ProposalRefinementRevise as ProposalRefinementRevise
from .media_buy import ProposalRefinementReviseAlternatives as ProposalRefinementReviseAlternatives
from .media_buy import ProposalRefinementReviseAsk as ProposalRefinementReviseAsk
from .media_buy import ProposalRefinementReviseCancellation as ProposalRefinementReviseCancellation
from .media_buy import ProposalRefinementReviseConstraints as ProposalRefinementReviseConstraints
from .media_buy import ProposalRefinementReviseCriteria as ProposalRefinementReviseCriteria
from .media_buy import ProposalRefinementReviseProductChanges as ProposalRefinementReviseProductChanges
from .media_buy import (
    ProposalRefinementReviseRemoveMediaBuyFrequencyCap as ProposalRefinementReviseRemoveMediaBuyFrequencyCap,
)
from .media_buy import ProvidePerformanceFeedbackError as ProvidePerformanceFeedbackError
from .media_buy import ProvidePerformanceFeedbackRequest as ProvidePerformanceFeedbackRequest
from .media_buy import ProvidePerformanceFeedbackResponse as ProvidePerformanceFeedbackResponse
from .media_buy import ProvidePerformanceFeedbackSuccess as ProvidePerformanceFeedbackSuccess
from .media_buy import (
    ProvidePerformanceFeedbackSuccessApplicationStatus as ProvidePerformanceFeedbackSuccessApplicationStatus,
)
from .media_buy import PurchaseContinuationLegacyCreate as PurchaseContinuationLegacyCreate
from .media_buy import PurchaseContinuationListedPurchaseAccount as PurchaseContinuationListedPurchaseAccount
from .media_buy import RecordedReportingAdjustmentReceipt as RecordedReportingAdjustmentReceipt
from .media_buy import RecordedReportingConsumerStatus as RecordedReportingConsumerStatus
from .media_buy import RecordedReportingReceipt as RecordedReportingReceipt
from .media_buy import RefinementAppliedItemProduct as RefinementAppliedItemProduct
from .media_buy import RefinementAppliedItemProposal as RefinementAppliedItemProposal
from .media_buy import RefinementAppliedItemRequest as RefinementAppliedItemRequest
from .media_buy import RefinementAppliedItemRequestStatus as RefinementAppliedItemRequestStatus
from .media_buy import RefineProposalsInputRequired as RefineProposalsInputRequired
from .media_buy import RefineProposalsRequest as RefineProposalsRequest
from .media_buy import RefineProposalsResponse as RefineProposalsResponse
from .media_buy import RefineProposalsResponseCompleted as RefineProposalsResponseCompleted
from .media_buy import RefineProposalsResponseResultsItem as RefineProposalsResponseResultsItem
from .media_buy import (
    RefineProposalsResponseResultsItemFinalizedProposal as RefineProposalsResponseResultsItemFinalizedProposal,
)
from .media_buy import RefineProposalsResponseResultsItemOutcome as RefineProposalsResponseResultsItemOutcome
from .media_buy import RefineProposalsResponseResultsItemUnable as RefineProposalsResponseResultsItemUnable
from .media_buy import RefineProposalsResponseStatus as RefineProposalsResponseStatus
from .media_buy import RefineProposalsResponseSubmitted as RefineProposalsResponseSubmitted
from .media_buy import RefineProposalsSubmitted as RefineProposalsSubmitted
from .media_buy import RefineProposalsWorking as RefineProposalsWorking
from .media_buy import RegistryAcceptancePolicyProfileReference as RegistryAcceptancePolicyProfileReference
from .media_buy import RequestProposalsInputRequired as RequestProposalsInputRequired
from .media_buy import RequestProposalsRequest as RequestProposalsRequest
from .media_buy import RequestProposalsRequestAccount as RequestProposalsRequestAccount
from .media_buy import RequestProposalsRequestAccountAccount as RequestProposalsRequestAccountAccount
from .media_buy import RequestProposalsRequestAccountAccountAccountId as RequestProposalsRequestAccountAccountAccountId
from .media_buy import (
    RequestProposalsRequestAccountAccountBrandOperator as RequestProposalsRequestAccountAccountBrandOperator,
)
from .media_buy import RequestProposalsRequestBrand as RequestProposalsRequestBrand
from .media_buy import RequestProposalsRequestOpportunity as RequestProposalsRequestOpportunity
from .media_buy import RequestProposalsResponse as RequestProposalsResponse
from .media_buy import RequestProposalsResponseIncompleteItem as RequestProposalsResponseIncompleteItem
from .media_buy import RequestProposalsResponseOutcome as RequestProposalsResponseOutcome
from .media_buy import (
    RequestProposalsResponseProductsAvailableCompleted as RequestProposalsResponseProductsAvailableCompleted,
)
from .media_buy import RequestProposalsResponseProposalsItem as RequestProposalsResponseProposalsItem
from .media_buy import RequestProposalsResponseProposedCompleted as RequestProposalsResponseProposedCompleted
from .media_buy import (
    RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem as RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem,
)
from .media_buy import (
    RequestProposalsResponsePurchaseContinuationLegacyCreateSourceAdcpVersion as RequestProposalsResponsePurchaseContinuationLegacyCreateSourceAdcpVersion,
)
from .media_buy import RequestProposalsResponseRejectedCompleted as RequestProposalsResponseRejectedCompleted
from .media_buy import RequestProposalsResponseSubmitted as RequestProposalsResponseSubmitted
from .media_buy import RequestProposalsSubmitted as RequestProposalsSubmitted
from .media_buy import RequestProposalsWorking as RequestProposalsWorking
from .media_buy import ResultsItemDeclined as ResultsItemDeclined
from .media_buy import ResultsItemFinalized as ResultsItemFinalized
from .media_buy import ResultsItemPartial as ResultsItemPartial
from .media_buy import ResultsItemPartialProposalsItem as ResultsItemPartialProposalsItem
from .media_buy import ResultsItemRevised as ResultsItemRevised
from .media_buy import RevisionView as RevisionView
from .media_buy import RevisionViewPagination as RevisionViewPagination
from .media_buy import SignalConditionsItemBinary as SignalConditionsItemBinary
from .media_buy import SignalConditionsItemCategorical as SignalConditionsItemCategorical
from .media_buy import SignalConditionsItemNumeric as SignalConditionsItemNumeric
from .media_buy import StartTime as StartTime
from .media_buy import SuccessfulLookup as SuccessfulLookup
from .media_buy import SummaryView as SummaryView
from .media_buy import SyncAudiencesError as SyncAudiencesError
from .media_buy import SyncAudiencesRequest as SyncAudiencesRequest
from .media_buy import SyncAudiencesRequestAudiencesItem as SyncAudiencesRequestAudiencesItem
from .media_buy import SyncAudiencesRequestAudiencesItemAudienceType as SyncAudiencesRequestAudiencesItemAudienceType
from .media_buy import SyncAudiencesResponse as SyncAudiencesResponse
from .media_buy import SyncAudiencesSubmitted as SyncAudiencesSubmitted
from .media_buy import SyncAudiencesSuccess as SyncAudiencesSuccess
from .media_buy import SyncAudiencesSuccessAudiencesItem as SyncAudiencesSuccessAudiencesItem
from .media_buy import SyncAudiencesSuccessAudiencesItemAction as SyncAudiencesSuccessAudiencesItemAction
from .media_buy import (
    SyncAudiencesSuccessAudiencesItemMatchBreakdownItem as SyncAudiencesSuccessAudiencesItemMatchBreakdownItem,
)
from .media_buy import SyncAudiencesSuccessAudiencesItemSource as SyncAudiencesSuccessAudiencesItemSource
from .media_buy import (
    SyncAudiencesSuccessAudiencesItemSourceAccessStatus as SyncAudiencesSuccessAudiencesItemSourceAccessStatus,
)
from .media_buy import SyncAudiencesSuccessAudiencesItemSourceKind as SyncAudiencesSuccessAudiencesItemSourceKind
from .media_buy import SyncCatalogsError as SyncCatalogsError
from .media_buy import SyncCatalogsErrorErrorsItem as SyncCatalogsErrorErrorsItem
from .media_buy import SyncCatalogsInputRequired as SyncCatalogsInputRequired
from .media_buy import SyncCatalogsInputRequiredReason as SyncCatalogsInputRequiredReason
from .media_buy import SyncCatalogsRequest as SyncCatalogsRequest
from .media_buy import SyncCatalogsResponse as SyncCatalogsResponse
from .media_buy import SyncCatalogsResponseSubmitted as SyncCatalogsResponseSubmitted
from .media_buy import SyncCatalogsSubmitted as SyncCatalogsSubmitted
from .media_buy import SyncCatalogsSuccess as SyncCatalogsSuccess
from .media_buy import SyncCatalogsSuccessCatalogsItem as SyncCatalogsSuccessCatalogsItem
from .media_buy import SyncCatalogsSuccessCatalogsItemItemIssuesItem as SyncCatalogsSuccessCatalogsItemItemIssuesItem
from .media_buy import SyncCatalogsWorking as SyncCatalogsWorking
from .media_buy import SyncEventSourcesError as SyncEventSourcesError
from .media_buy import SyncEventSourcesRequest as SyncEventSourcesRequest
from .media_buy import SyncEventSourcesRequestEventSourcesItem as SyncEventSourcesRequestEventSourcesItem
from .media_buy import SyncEventSourcesResponse as SyncEventSourcesResponse
from .media_buy import SyncEventSourcesSuccess as SyncEventSourcesSuccess
from .media_buy import SyncEventSourcesSuccessEventSourcesItem as SyncEventSourcesSuccessEventSourcesItem
from .media_buy import SyncEventSourcesSuccessEventSourcesItemSetup as SyncEventSourcesSuccessEventSourcesItemSetup
from .media_buy import (
    SyncEventSourcesSuccessEventSourcesItemSetupSnippetType as SyncEventSourcesSuccessEventSourcesItemSetupSnippetType,
)
from .media_buy import SyncReportingReceiptsRequest as SyncReportingReceiptsRequest
from .media_buy import (
    SyncReportingReceiptsRequestAdjustmentReceiptsItem as SyncReportingReceiptsRequestAdjustmentReceiptsItem,
)
from .media_buy import SyncReportingReceiptsRequestReceiptsItem as SyncReportingReceiptsRequestReceiptsItem
from .media_buy import SyncReportingReceiptsResponse as SyncReportingReceiptsResponse
from .media_buy import SyncReportingStatusRequest as SyncReportingStatusRequest
from .media_buy import SyncReportingStatusRequestStatusesItem as SyncReportingStatusRequestStatusesItem
from .media_buy import SyncReportingStatusResponse as SyncReportingStatusResponse
from .media_buy import UnavailableLookup as UnavailableLookup
from .media_buy import UnavailableLookupAdcpError as UnavailableLookupAdcpError
from .media_buy import UnavailableLookupErrorsItem as UnavailableLookupErrorsItem
from .media_buy import UnchangedReportingAdjustmentReceipt as UnchangedReportingAdjustmentReceipt
from .media_buy import (
    UnchangedReportingAdjustmentReceiptAdjustmentReceipt as UnchangedReportingAdjustmentReceiptAdjustmentReceipt,
)
from .media_buy import UnchangedReportingConsumerStatus as UnchangedReportingConsumerStatus
from .media_buy import UnchangedReportingConsumerStatusConsumerStatus as UnchangedReportingConsumerStatusConsumerStatus
from .media_buy import UnchangedReportingReceipt as UnchangedReportingReceipt
from .media_buy import UnchangedReportingReceiptReceipt as UnchangedReportingReceiptReceipt
from .media_buy import UpdateMediaBuyError as UpdateMediaBuyError
from .media_buy import UpdateMediaBuyInputRequired as UpdateMediaBuyInputRequired
from .media_buy import UpdateMediaBuyInputRequiredReason as UpdateMediaBuyInputRequiredReason
from .media_buy import UpdateMediaBuyRequest as UpdateMediaBuyRequest
from .media_buy import UpdateMediaBuyResponse as UpdateMediaBuyResponse
from .media_buy import UpdateMediaBuyResponseSubmitted as UpdateMediaBuyResponseSubmitted
from .media_buy import UpdateMediaBuySubmitted as UpdateMediaBuySubmitted
from .media_buy import UpdateMediaBuySuccess as UpdateMediaBuySuccess
from .media_buy import UpdateMediaBuySuccessBidding as UpdateMediaBuySuccessBidding
from .media_buy import UpdateMediaBuyWorking as UpdateMediaBuyWorking
from .pricing_options import CPAPricingOption as CPAPricingOption
from .pricing_options import CPCPricingOption as CPCPricingOption
from .pricing_options import CPCVPricingOption as CPCVPricingOption
from .pricing_options import CPMPricingOption as CPMPricingOption
from .pricing_options import CPPPricingOption as CPPPricingOption
from .pricing_options import CPPPricingOptionParameters as CPPPricingOptionParameters
from .pricing_options import CPVPricingOption as CPVPricingOption
from .pricing_options import CPVPricingOptionParameters as CPVPricingOptionParameters
from .pricing_options import FlatRatePricingOption as FlatRatePricingOption
from .pricing_options import FlatRatePricingOptionParameters as FlatRatePricingOptionParameters
from .pricing_options import PriceBreakdown as PriceBreakdown
from .pricing_options import PriceBreakdownAdjustmentsItem as PriceBreakdownAdjustmentsItem
from .pricing_options import PriceGuidance as PriceGuidance
from .pricing_options import RevenueSharePricingOption as RevenueSharePricingOption
from .pricing_options import TimeBasedPricingOption as TimeBasedPricingOption
from .pricing_options import TimeBasedPricingOptionParameters as TimeBasedPricingOptionParameters
from .pricing_options import TimeBasedPricingOptionParametersTimeUnit as TimeBasedPricingOptionParametersTimeUnit
from .pricing_options import VCPMPricingOption as VCPMPricingOption
from .pricing_options import ViewThresholdDurationSeconds as ViewThresholdDurationSeconds
from .property import AuthorizationResult as AuthorizationResult
from .property import AuthorizationResultStatus as AuthorizationResultStatus
from .property import AuthorizationResultViolation as AuthorizationResultViolation
from .property import BasePropertySource as BasePropertySource
from .property import CreatePropertyListRequest as CreatePropertyListRequest
from .property import CreatePropertyListResponse as CreatePropertyListResponse
from .property import DeletePropertyListRequest as DeletePropertyListRequest
from .property import DeletePropertyListResponse as DeletePropertyListResponse
from .property import DeliveryRecord as DeliveryRecord
from .property import DirectIdentifiersSource as DirectIdentifiersSource
from .property import GetPropertyListRequest as GetPropertyListRequest
from .property import GetPropertyListResponse as GetPropertyListResponse
from .property import ListPropertyListsRequest as ListPropertyListsRequest
from .property import ListPropertyListsResponse as ListPropertyListsResponse
from .property import PropertyError as PropertyError
from .property import PropertyErrorCode as PropertyErrorCode
from .property import PropertyFeature as PropertyFeature
from .property import PropertyFeatureDefinition as PropertyFeatureDefinition
from .property import PropertyFeatureDefinitionCoverage as PropertyFeatureDefinitionCoverage
from .property import PropertyFeatureDefinitionType as PropertyFeatureDefinitionType
from .property import PropertyFeatureResult as PropertyFeatureResult
from .property import PropertyFeatureResultCoverageStatus as PropertyFeatureResultCoverageStatus
from .property import PropertyFeatureValue as PropertyFeatureValue
from .property import PropertyList as PropertyList
from .property import PropertyListChangedWebhook as PropertyListChangedWebhook
from .property import PropertyListChangedWebhookChangeSummary as PropertyListChangedWebhookChangeSummary
from .property import PropertyListFilters as PropertyListFilters
from .property import PublisherPropertyIDsSource as PublisherPropertyIDsSource
from .property import PublisherTagsSource as PublisherTagsSource
from .property import UpdatePropertyListRequest as UpdatePropertyListRequest
from .property import UpdatePropertyListResponse as UpdatePropertyListResponse
from .property import ValidatePropertyDeliveryRequest as ValidatePropertyDeliveryRequest
from .property import ValidatePropertyDeliveryResponse as ValidatePropertyDeliveryResponse
from .property import ValidatePropertyDeliveryResponseAggregate as ValidatePropertyDeliveryResponseAggregate
from .property import (
    ValidatePropertyDeliveryResponseAuthorizationSummary as ValidatePropertyDeliveryResponseAuthorizationSummary,
)
from .property import ValidatePropertyDeliveryResponseSummary as ValidatePropertyDeliveryResponseSummary
from .property import ValidationResult as ValidationResult
from .property import ValidationResultFeaturesItem as ValidationResultFeaturesItem
from .property import ValidationResultFeaturesItemRequirement as ValidationResultFeaturesItemRequirement
from .property import ValidationResultStatus as ValidationResultStatus
from .protocol import AccountChangeFeedSupported as AccountChangeFeedSupported
from .protocol import AccountChangeFeedUnsupported as AccountChangeFeedUnsupported
from .protocol import AccountIdentityUpdatesSupported as AccountIdentityUpdatesSupported
from .protocol import (
    AccountIdentityUpdatesSupportedSupportedChangesItem as AccountIdentityUpdatesSupportedSupportedChangesItem,
)
from .protocol import AccountIdentityUpdatesUnsupported as AccountIdentityUpdatesUnsupported
from .protocol import AccountNotificationsSupported as AccountNotificationsSupported
from .protocol import AccountNotificationsSupportedEventTypesItem as AccountNotificationsSupportedEventTypesItem
from .protocol import AccountNotificationsUnsupported as AccountNotificationsUnsupported
from .protocol import AppliedPrincipalConfiguration as AppliedPrincipalConfiguration
from .protocol import AppliedPrincipalConfigurationAction as AppliedPrincipalConfigurationAction
from .protocol import CapabilityChangeNotificationsSupported as CapabilityChangeNotificationsSupported
from .protocol import (
    CapabilityChangeNotificationsSupportedEventTypesItem as CapabilityChangeNotificationsSupportedEventTypesItem,
)
from .protocol import (
    CapabilityChangeNotificationsSupportedRegistrationTask as CapabilityChangeNotificationsSupportedRegistrationTask,
)
from .protocol import CapabilityChangeNotificationsUnsupported as CapabilityChangeNotificationsUnsupported
from .protocol import CreativeFeaturesItemRange as CreativeFeaturesItemRange
from .protocol import CreativeFeaturesItemType as CreativeFeaturesItemType
from .protocol import CurrentPrincipalConfiguration as CurrentPrincipalConfiguration
from .protocol import ExtensionsSupportedItem as ExtensionsSupportedItem
from .protocol import FailedPrincipalRead as FailedPrincipalRead
from .protocol import FailedPrincipalSync as FailedPrincipalSync
from .protocol import GetAdCPCapabilitiesRequest as GetAdCPCapabilitiesRequest
from .protocol import GetAdCPCapabilitiesRequestProtocolsItem as GetAdCPCapabilitiesRequestProtocolsItem
from .protocol import GetAdCPCapabilitiesResponse as GetAdCPCapabilitiesResponse
from .protocol import GetAdCPCapabilitiesResponseAccount as GetAdCPCapabilitiesResponseAccount
from .protocol import GetAdCPCapabilitiesResponseAdcp as GetAdCPCapabilitiesResponseAdcp
from .protocol import (
    GetAdCPCapabilitiesResponseAdcpCapabilityChanges as GetAdCPCapabilitiesResponseAdcpCapabilityChanges,
)
from .protocol import (
    GetAdCPCapabilitiesResponseAdcpGovernanceEnforcement as GetAdCPCapabilitiesResponseAdcpGovernanceEnforcement,
)
from .protocol import GetAdCPCapabilitiesResponseAdcpPrincipal as GetAdCPCapabilitiesResponseAdcpPrincipal
from .protocol import (
    GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItem as GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern as GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern,
)
from .protocol import (
    GetAdCPCapabilitiesResponseAdcpPrincipalSupportedSectionsItem as GetAdCPCapabilitiesResponseAdcpPrincipalSupportedSectionsItem,
)
from .protocol import GetAdCPCapabilitiesResponseBrand as GetAdCPCapabilitiesResponseBrand
from .protocol import (
    GetAdCPCapabilitiesResponseBudgetCappingTimezoneBasis as GetAdCPCapabilitiesResponseBudgetCappingTimezoneBasis,
)
from .protocol import (
    GetAdCPCapabilitiesResponseCapabilityReportingDeliveryMethod as GetAdCPCapabilitiesResponseCapabilityReportingDeliveryMethod,
)
from .protocol import GetAdCPCapabilitiesResponseComplianceTesting as GetAdCPCapabilitiesResponseComplianceTesting
from .protocol import GetAdCPCapabilitiesResponseCreative as GetAdCPCapabilitiesResponseCreative
from .protocol import GetAdCPCapabilitiesResponseCreativeLocalization as GetAdCPCapabilitiesResponseCreativeLocalization
from .protocol import GetAdCPCapabilitiesResponseCreativeMultiplicity as GetAdCPCapabilitiesResponseCreativeMultiplicity
from .protocol import (
    GetAdCPCapabilitiesResponseCreativeMultiplicityVariantDimensionsItem as GetAdCPCapabilitiesResponseCreativeMultiplicityVariantDimensionsItem,
)
from .protocol import GetAdCPCapabilitiesResponseCreativePreview as GetAdCPCapabilitiesResponseCreativePreview
from .protocol import (
    GetAdCPCapabilitiesResponseCreativePreviewRoutesItem as GetAdCPCapabilitiesResponseCreativePreviewRoutesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseCreativeRepresentationResolution as GetAdCPCapabilitiesResponseCreativeRepresentationResolution,
)
from .protocol import (
    GetAdCPCapabilitiesResponseCreativeSupportedFormatsItem as GetAdCPCapabilitiesResponseCreativeSupportedFormatsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseCreativeSupportedFormatsItemOperationsItem as GetAdCPCapabilitiesResponseCreativeSupportedFormatsItemOperationsItem,
)
from .protocol import GetAdCPCapabilitiesResponseGovernance as GetAdCPCapabilitiesResponseGovernance
from .protocol import (
    GetAdCPCapabilitiesResponseGovernanceCreativeFeaturesItem as GetAdCPCapabilitiesResponseGovernanceCreativeFeaturesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseGovernancePropertyFeaturesItem as GetAdCPCapabilitiesResponseGovernancePropertyFeaturesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseGovernanceRuntimeAttestations as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestations,
)
from .protocol import (
    GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivation as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivation,
)
from .protocol import (
    GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivationRequirement as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivationRequirement,
)
from .protocol import GetAdCPCapabilitiesResponseIdentity as GetAdCPCapabilitiesResponseIdentity
from .protocol import (
    GetAdCPCapabilitiesResponseIdentityCompromiseNotification as GetAdCPCapabilitiesResponseIdentityCompromiseNotification,
)
from .protocol import GetAdCPCapabilitiesResponseIdentityKeyOrigins as GetAdCPCapabilitiesResponseIdentityKeyOrigins
from .protocol import GetAdCPCapabilitiesResponseMeasurement as GetAdCPCapabilitiesResponseMeasurement
from .protocol import GetAdCPCapabilitiesResponseMeasurementGateway as GetAdCPCapabilitiesResponseMeasurementGateway
from .protocol import (
    GetAdCPCapabilitiesResponseMeasurementMetricsItem as GetAdCPCapabilitiesResponseMeasurementMetricsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMeasurementMetricsItemAccreditationsItem as GetAdCPCapabilitiesResponseMeasurementMetricsItemAccreditationsItem,
)
from .protocol import GetAdCPCapabilitiesResponseMediaBuy as GetAdCPCapabilitiesResponseMediaBuy
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery as GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyAudienceEvidence as GetAdCPCapabilitiesResponseMediaBuyAudienceEvidence,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyAudienceTargeting as GetAdCPCapabilitiesResponseMediaBuyAudienceTargeting,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyAudienceTargetingMatchingLatencyHours as GetAdCPCapabilitiesResponseMediaBuyAudienceTargetingMatchingLatencyHours,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyBudgetCapping as GetAdCPCapabilitiesResponseMediaBuyBudgetCapping,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedPeriodsItem as GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedPeriodsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedScopesItem as GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedScopesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyContentStandards as GetAdCPCapabilitiesResponseMediaBuyContentStandards,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyConversionTracking as GetAdCPCapabilitiesResponseMediaBuyConversionTracking,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyConversionTrackingAttributionWindowsItem as GetAdCPCapabilitiesResponseMediaBuyConversionTrackingAttributionWindowsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyCreativeApprovalMode as GetAdCPCapabilitiesResponseMediaBuyCreativeApprovalMode,
)
from .protocol import GetAdCPCapabilitiesResponseMediaBuyExecution as GetAdCPCapabilitiesResponseMediaBuyExecution
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecs as GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecs,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecsVastValidation as GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecsVastValidation,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargeting as GetAdCPCapabilitiesResponseMediaBuyExecutionTargeting,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingAgeRestriction as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingAgeRestriction,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingDemographics as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingDemographics,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoMetros as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoMetros,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoProximity as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoProximity,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingKeywordTargets as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingKeywordTargets,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingNegativeKeywords as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingNegativeKeywords,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyExecutionTrustedMatch as GetAdCPCapabilitiesResponseMediaBuyExecutionTrustedMatch,
)
from .protocol import GetAdCPCapabilitiesResponseMediaBuyFeatures as GetAdCPCapabilitiesResponseMediaBuyFeatures
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyFrequencyCapping as GetAdCPCapabilitiesResponseMediaBuyFrequencyCapping,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyLifecycleToolsItem as GetAdCPCapabilitiesResponseMediaBuyLifecycleToolsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyPerformanceFeedback as GetAdCPCapabilitiesResponseMediaBuyPerformanceFeedback,
)
from .protocol import GetAdCPCapabilitiesResponseMediaBuyPortfolio as GetAdCPCapabilitiesResponseMediaBuyPortfolio
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyPropagationSurfacesItem as GetAdCPCapabilitiesResponseMediaBuyPropagationSurfacesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyProposalRefinement as GetAdCPCapabilitiesResponseMediaBuyProposalRefinement,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyProposalRefinementSupportedDimensionsItem as GetAdCPCapabilitiesResponseMediaBuyProposalRefinementSupportedDimensionsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyRelationshipNotifications as GetAdCPCapabilitiesResponseMediaBuyRelationshipNotifications,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyRelationshipNotificationsEventTypesItem as GetAdCPCapabilitiesResponseMediaBuyRelationshipNotificationsEventTypesItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyRightsAttestations as GetAdCPCapabilitiesResponseMediaBuyRightsAttestations,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyRightsAttestationsRequirement as GetAdCPCapabilitiesResponseMediaBuyRightsAttestationsRequirement,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimization as GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimization,
)
from .protocol import (
    GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimizationSupportedTargetsItem as GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimizationSupportedTargetsItem,
)
from .protocol import GetAdCPCapabilitiesResponseOauth as GetAdCPCapabilitiesResponseOauth
from .protocol import GetAdCPCapabilitiesResponseRequestSigning as GetAdCPCapabilitiesResponseRequestSigning
from .protocol import (
    GetAdCPCapabilitiesResponseRequestSigningCoversContentDigest as GetAdCPCapabilitiesResponseRequestSigningCoversContentDigest,
)
from .protocol import GetAdCPCapabilitiesResponseSignals as GetAdCPCapabilitiesResponseSignals
from .protocol import (
    GetAdCPCapabilitiesResponseSignalsDiscoveryModesItem as GetAdCPCapabilitiesResponseSignalsDiscoveryModesItem,
)
from .protocol import GetAdCPCapabilitiesResponseSignalsFeatures as GetAdCPCapabilitiesResponseSignalsFeatures
from .protocol import (
    GetAdCPCapabilitiesResponseSponsoredIntelligence as GetAdCPCapabilitiesResponseSponsoredIntelligence,
)
from .protocol import (
    GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpoint as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpoint,
)
from .protocol import (
    GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointPreferred as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointPreferred,
)
from .protocol import (
    GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointTransportsItem as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointTransportsItem,
)
from .protocol import (
    GetAdCPCapabilitiesResponseSupportedProtocolsItem as GetAdCPCapabilitiesResponseSupportedProtocolsItem,
)
from .protocol import GetAdCPCapabilitiesResponseWebhookSigning as GetAdCPCapabilitiesResponseWebhookSigning
from .protocol import (
    GetAdCPCapabilitiesResponseWebhookSigningProfile as GetAdCPCapabilitiesResponseWebhookSigningProfile,
)
from .protocol import (
    GetAdCPCapabilitiesResponseWholesaleFeedVersioning as GetAdCPCapabilitiesResponseWholesaleFeedVersioning,
)
from .protocol import (
    GetAdCPCapabilitiesResponseWholesaleFeedWebhooks as GetAdCPCapabilitiesResponseWholesaleFeedWebhooks,
)
from .protocol import GetPrincipalRequest as GetPrincipalRequest
from .protocol import GetPrincipalResponse as GetPrincipalResponse
from .protocol import GetTaskStatusRequest as GetTaskStatusRequest
from .protocol import GetTaskStatusResponse as GetTaskStatusResponse
from .protocol import IdempotencySupported as IdempotencySupported
from .protocol import IdempotencyUnsupported as IdempotencyUnsupported
from .protocol import Language as Language
from .protocol import ListTasksRequest as ListTasksRequest
from .protocol import ListTasksResponse as ListTasksResponse
from .protocol import RecognizedPrincipalWithoutStandingConfiguration as RecognizedPrincipalWithoutStandingConfiguration
from .protocol import SupportedHashedIdentifiersItem as SupportedHashedIdentifiersItem
from .protocol import SyncAgentNotificationConfigsRequest as SyncAgentNotificationConfigsRequest
from .protocol import (
    SyncAgentNotificationConfigsRequestNotificationConfigsItem as SyncAgentNotificationConfigsRequestNotificationConfigsItem,
)
from .protocol import SyncAgentNotificationConfigsResponse as SyncAgentNotificationConfigsResponse
from .protocol import SyncAgentNotificationConfigsResponseAction as SyncAgentNotificationConfigsResponseAction
from .protocol import SyncPrincipalRequest as SyncPrincipalRequest
from .protocol import SyncPrincipalRequestConfiguration as SyncPrincipalRequestConfiguration
from .protocol import (
    SyncPrincipalRequestConfigurationNotificationConfigsItem as SyncPrincipalRequestConfigurationNotificationConfigsItem,
)
from .protocol import SyncPrincipalResponse as SyncPrincipalResponse
from .protocol import TasksItemAcceptProposal as TasksItemAcceptProposal
from .protocol import TasksItemAcquireRights as TasksItemAcquireRights
from .protocol import TasksItemActivateSignal as TasksItemActivateSignal
from .protocol import TasksItemBuildCreative as TasksItemBuildCreative
from .protocol import TasksItemBuyProducts as TasksItemBuyProducts
from .protocol import TasksItemControlMediaBuy as TasksItemControlMediaBuy
from .protocol import TasksItemCreateMediaBuy as TasksItemCreateMediaBuy
from .protocol import TasksItemCreateMediaBuyModesItem as TasksItemCreateMediaBuyModesItem
from .protocol import TasksItemUpdateMediaBuy as TasksItemUpdateMediaBuy
from .protocol import TasksItemUpdateRights as TasksItemUpdateRights
from .protocol import UnconfiguredPrincipal as UnconfiguredPrincipal
from .protocol import ValidatedPrincipalDryRun as ValidatedPrincipalDryRun
from .protocol import ValidatedPrincipalDryRunAction as ValidatedPrincipalDryRunAction
from .registries import V1PatternFormatIdGlob as V1PatternFormatIdGlob
from .registries import V1PatternStructural as V1PatternStructural
from .registries import V1V2CanonicalFormatMappingRegistry as V1V2CanonicalFormatMappingRegistry
from .registries import V1V2CanonicalFormatMappingRegistryMappingsItem as V1V2CanonicalFormatMappingRegistryMappingsItem
from .registries import (
    V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural as V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural,
)
from .registries import (
    V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions as V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions,
)
from .registries import (
    V1V2CanonicalFormatMappingRegistryMappingsItemV2 as V1V2CanonicalFormatMappingRegistryMappingsItemV2,
)
from .registries import (
    V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItem as V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItem,
)
from .registries import (
    V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItemTransform as V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItemTransform,
)
from .signals import ActivateSignalError as ActivateSignalError
from .signals import ActivateSignalRequest as ActivateSignalRequest
from .signals import ActivateSignalRequestAction as ActivateSignalRequestAction
from .signals import ActivateSignalResponse as ActivateSignalResponse
from .signals import ActivateSignalSuccess as ActivateSignalSuccess
from .signals import GetSignalsRequest as GetSignalsRequest
from .signals import GetSignalsRequestFieldsItem as GetSignalsRequestFieldsItem
from .signals import GetSignalsResponse as GetSignalsResponse
from .signals import GetSignalsResponseIncompleteItem as GetSignalsResponseIncompleteItem
from .signals import GetSignalsResponseIncompleteItemEstimatedWait as GetSignalsResponseIncompleteItemEstimatedWait
from .signals import GetSignalsResponseIncompleteItemScope as GetSignalsResponseIncompleteItemScope
from .signals import GetSignalsResponseSignalsItem as GetSignalsResponseSignalsItem
from .signals import GetSignalsSubmitted as GetSignalsSubmitted
from .signals import GetSignalsWorking as GetSignalsWorking
from .sponsored_intelligence import Avatar as Avatar
from .sponsored_intelligence import SICapabilities as SICapabilities
from .sponsored_intelligence import SICapabilitiesA2ui as SICapabilitiesA2ui
from .sponsored_intelligence import SICapabilitiesCommerce as SICapabilitiesCommerce
from .sponsored_intelligence import SICapabilitiesComponents as SICapabilitiesComponents
from .sponsored_intelligence import SICapabilitiesComponentsStandardItem as SICapabilitiesComponentsStandardItem
from .sponsored_intelligence import SICapabilitiesModalities as SICapabilitiesModalities
from .sponsored_intelligence import SIContextUse as SIContextUse
from .sponsored_intelligence import SIGetOfferingRequest as SIGetOfferingRequest
from .sponsored_intelligence import SIGetOfferingResponse as SIGetOfferingResponse
from .sponsored_intelligence import (
    SIGetOfferingResponseMatchingProductsItem as SIGetOfferingResponseMatchingProductsItem,
)
from .sponsored_intelligence import SIGetOfferingResponseOffering as SIGetOfferingResponseOffering
from .sponsored_intelligence import SIIdentity as SIIdentity
from .sponsored_intelligence import SIIdentityConsentScopeItem as SIIdentityConsentScopeItem
from .sponsored_intelligence import SIIdentityPrivacyPolicyAcknowledged as SIIdentityPrivacyPolicyAcknowledged
from .sponsored_intelligence import SIIdentityUser as SIIdentityUser
from .sponsored_intelligence import SIIdentityUserShippingAddress as SIIdentityUserShippingAddress
from .sponsored_intelligence import SIInitiateSessionRequest as SIInitiateSessionRequest
from .sponsored_intelligence import SIInitiateSessionResponse as SIInitiateSessionResponse
from .sponsored_intelligence import SIInitiateSessionResponseResponse as SIInitiateSessionResponseResponse
from .sponsored_intelligence import SISendMessageRequest as SISendMessageRequest
from .sponsored_intelligence import SISendMessageRequestActionResponse as SISendMessageRequestActionResponse
from .sponsored_intelligence import SISendMessageResponse as SISendMessageResponse
from .sponsored_intelligence import SISendMessageResponseHandoff as SISendMessageResponseHandoff
from .sponsored_intelligence import (
    SISendMessageResponseHandoffContextForCheckout as SISendMessageResponseHandoffContextForCheckout,
)
from .sponsored_intelligence import SISendMessageResponseHandoffIntent as SISendMessageResponseHandoffIntent
from .sponsored_intelligence import SISendMessageResponseHandoffIntentPrice as SISendMessageResponseHandoffIntentPrice
from .sponsored_intelligence import SISendMessageResponseHandoffType as SISendMessageResponseHandoffType
from .sponsored_intelligence import SISendMessageResponseResponse as SISendMessageResponseResponse
from .sponsored_intelligence import SISponsoredContext as SISponsoredContext
from .sponsored_intelligence import SISponsoredContextDeclaredBy as SISponsoredContextDeclaredBy
from .sponsored_intelligence import SISponsoredContextDeclaredByRole as SISponsoredContextDeclaredByRole
from .sponsored_intelligence import SISponsoredContextDisclosureObligation as SISponsoredContextDisclosureObligation
from .sponsored_intelligence import (
    SISponsoredContextDisclosureObligationJurisdictionsItem as SISponsoredContextDisclosureObligationJurisdictionsItem,
)
from .sponsored_intelligence import (
    SISponsoredContextDisclosureObligationProximity as SISponsoredContextDisclosureObligationProximity,
)
from .sponsored_intelligence import (
    SISponsoredContextDisclosureObligationTiming as SISponsoredContextDisclosureObligationTiming,
)
from .sponsored_intelligence import SISponsoredContextPayingPrincipal as SISponsoredContextPayingPrincipal
from .sponsored_intelligence import SISponsoredContextPayingPrincipalAccount as SISponsoredContextPayingPrincipalAccount
from .sponsored_intelligence import SISponsoredContextReceipt as SISponsoredContextReceipt
from .sponsored_intelligence import SISponsoredContextReceiptHostReceipt as SISponsoredContextReceiptHostReceipt
from .sponsored_intelligence import (
    SISponsoredContextReceiptHostReceiptDisclosureCommitment as SISponsoredContextReceiptHostReceiptDisclosureCommitment,
)
from .sponsored_intelligence import (
    SISponsoredContextReceiptHostReceiptDisclosureCommitmentStatus as SISponsoredContextReceiptHostReceiptDisclosureCommitmentStatus,
)
from .sponsored_intelligence import (
    SISponsoredContextReceiptHostReceiptStatus as SISponsoredContextReceiptHostReceiptStatus,
)
from .sponsored_intelligence import SITerminateSessionRequest as SITerminateSessionRequest
from .sponsored_intelligence import SITerminateSessionRequestReason as SITerminateSessionRequestReason
from .sponsored_intelligence import (
    SITerminateSessionRequestTerminationContext as SITerminateSessionRequestTerminationContext,
)
from .sponsored_intelligence import (
    SITerminateSessionRequestTerminationContextTransactionIntent as SITerminateSessionRequestTerminationContextTransactionIntent,
)
from .sponsored_intelligence import (
    SITerminateSessionRequestTerminationContextTransactionIntentAction as SITerminateSessionRequestTerminationContextTransactionIntentAction,
)
from .sponsored_intelligence import SITerminateSessionResponse as SITerminateSessionResponse
from .sponsored_intelligence import SITerminateSessionResponseAcpHandoff as SITerminateSessionResponseAcpHandoff
from .sponsored_intelligence import SITerminateSessionResponseFollowUp as SITerminateSessionResponseFollowUp
from .sponsored_intelligence import SITerminateSessionResponseFollowUpAction as SITerminateSessionResponseFollowUpAction
from .sponsored_intelligence import SIUIElement as SIUIElement
from .sponsored_intelligence import SIUIElementType as SIUIElementType
from .sponsored_intelligence import Video as Video
from .sponsored_intelligence import Voice as Voice
from .trusted_match import AvailablePackage as AvailablePackage
from .trusted_match import ContextMatchRequest as ContextMatchRequest
from .trusted_match import ContextMatchRequestArtifactRefsItem as ContextMatchRequestArtifactRefsItem
from .trusted_match import ContextMatchRequestArtifactRefsItemType as ContextMatchRequestArtifactRefsItemType
from .trusted_match import ContextMatchRequestContextSignals as ContextMatchRequestContextSignals
from .trusted_match import ContextMatchRequestContextSignalsSentiment as ContextMatchRequestContextSignalsSentiment
from .trusted_match import ContextMatchRequestGeo as ContextMatchRequestGeo
from .trusted_match import ContextMatchRequestGeoMetro as ContextMatchRequestGeoMetro
from .trusted_match import ContextMatchResponseProviderRouter as ContextMatchResponseProviderRouter
from .trusted_match import ContextMatchResponseProviderRouterSignals as ContextMatchResponseProviderRouterSignals
from .trusted_match import (
    ContextMatchResponseProviderRouterTargetingKvs as ContextMatchResponseProviderRouterTargetingKvs,
)
from .trusted_match import ContextMatchResponseRouterPublisher as ContextMatchResponseRouterPublisher
from .trusted_match import ContextMatchResponseRouterPublisherSignals as ContextMatchResponseRouterPublisherSignals
from .trusted_match import (
    ContextMatchResponseRouterPublisherSignalsByProviderValue as ContextMatchResponseRouterPublisherSignalsByProviderValue,
)
from .trusted_match import (
    ContextMatchResponseRouterPublisherTargetingKvs as ContextMatchResponseRouterPublisherTargetingKvs,
)
from .trusted_match import (
    ContextMatchResponseRouterPublisherTargetingKvsItem as ContextMatchResponseRouterPublisherTargetingKvsItem,
)
from .trusted_match import IdentityMatchRequest as IdentityMatchRequest
from .trusted_match import IdentityMatchRequestConsent as IdentityMatchRequestConsent
from .trusted_match import IdentityMatchRequestIdentitiesItem as IdentityMatchRequestIdentitiesItem
from .trusted_match import (
    IdentityMatchRequestIdentitiesItemAttestation as IdentityMatchRequestIdentitiesItemAttestation,
)
from .trusted_match import (
    IdentityMatchRequestIdentitiesItemAttestationVerificationLevel as IdentityMatchRequestIdentitiesItemAttestationVerificationLevel,
)
from .trusted_match import IdentityMatchRequestSealedCredentialsItem as IdentityMatchRequestSealedCredentialsItem
from .trusted_match import IdentityMatchResponseProviderRouter as IdentityMatchResponseProviderRouter
from .trusted_match import IdentityMatchResponseRouterPublisher as IdentityMatchResponseRouterPublisher
from .trusted_match import (
    IdentityMatchResponseRouterPublisherTmpxProvidersValue as IdentityMatchResponseRouterPublisherTmpxProvidersValue,
)
from .trusted_match import Offer as Offer
from .trusted_match import OfferPrice as OfferPrice
from .trusted_match import OfferPriceModel as OfferPriceModel
from .trusted_match import PublisherTargetingKVMapping as PublisherTargetingKVMapping
from .trusted_match import PublisherTMPXMacroMapping as PublisherTMPXMacroMapping
from .trusted_match import TargetingKvMappingValue as TargetingKvMappingValue
from .trusted_match import TMPError as TMPError
from .trusted_match import TMPErrorCode as TMPErrorCode
from .trusted_match import TMPProviderRegistration as TMPProviderRegistration
from .trusted_match import TMPProviderRegistrationContextMatch as TMPProviderRegistrationContextMatch
from .trusted_match import TMPProviderRegistrationIdentityMatch as TMPProviderRegistrationIdentityMatch
from .trusted_match import TMPProviderRegistrationStatus as TMPProviderRegistrationStatus
from .trusted_match import TMPXChunk as TMPXChunk
from .trusted_match import TmpxMacroMappingValue as TmpxMacroMappingValue

__all__ = [
    'HTTPSURL',
    'A2UIBoundValue',
    'A2UIBoundValueLiteralBoolean',
    'A2UIBoundValueLiteralNumber',
    'A2UIBoundValueLiteralString',
    'A2UIBoundValueLiteralStringPath',
    'A2UIBoundValuePath',
    'A2UIComponent',
    'A2UISurface',
    'A2UIUserAction',
    'A2UIUserActionAction',
    'A2UiBoundValue',
    'A2UiBoundValue1',
    'A2UiBoundValue2',
    'A2UiBoundValue3',
    'A2UiBoundValue4',
    'A2UiBoundValue5',
    'A2UiComponent',
    'A2UiSurface',
    'A2UiUserAction',
    'AAODirectoryAgentPublishersInverseLookupResponse',
    'AAODirectoryAgentPublishersInverseLookupResponsePublisherEntry',
    'AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryDiscoveryMethod',
    'AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryStatus',
    'AaoDirectoryAgentPublishersInverseLookupResponse',
    'AcceptProposalInputRequired',
    'AcceptProposalRequest',
    'AcceptProposalRequestIoAcceptance',
    'AcceptProposalRequestOpportunity',
    'AcceptProposalResponse',
    'AcceptProposalSubmitted',
    'AcceptProposalWorking',
    'AcceptanceContext',
    'AcceptanceContextSubjectsItem',
    'AcceptancePolicyCatalog',
    'AcceptancePolicyProfile',
    'AcceptancePolicyProfileCoverage',
    'AcceptancePolicyProfileIDs',
    'AcceptancePolicyProfileIds',
    'AcceptancePolicyProfilePolicyRefsItem',
    'AcceptancePolicyProfileScope',
    'AcceptancePolicyRequirement',
    'AcceptancePolicyRequirement1',
    'AcceptancePolicyRequirement2',
    'AcceptancePolicyRequirement3',
    'AcceptancePolicyRequirement4',
    'AcceptancePolicyRequirement5',
    'AcceptancePolicyRequirement6',
    'AcceptancePolicyRequirement7',
    'AcceptancePolicyRequirement8',
    'AcceptancePolicyRequirement9',
    'AcceptancePolicyRequirement10',
    'AcceptancePolicyRequirement11',
    'AcceptancePolicyRequirement12',
    'AcceptancePolicyRequirement13',
    'AcceptancePolicyRequirement14',
    'AcceptancePolicyRequirement15',
    'AcceptancePolicyRequirement16',
    'AcceptancePolicyRequirement17',
    'AcceptancePolicyRequirementAccountSetup',
    'AcceptancePolicyRequirementAdvertiserEligibility',
    'AcceptancePolicyRequirementAdvertiserVerification',
    'AcceptancePolicyRequirementCategoryDeclaration',
    'AcceptancePolicyRequirementCertification',
    'AcceptancePolicyRequirementCreativeRestriction',
    'AcceptancePolicyRequirementCustom',
    'AcceptancePolicyRequirementDestinationRestriction',
    'AcceptancePolicyRequirementDisclosure',
    'AcceptancePolicyRequirementFormatRestriction',
    'AcceptancePolicyRequirementFundingRestriction',
    'AcceptancePolicyRequirementLicense',
    'AcceptancePolicyRequirementPriorAuthorization',
    'AcceptancePolicyRequirementSalesAssisted',
    'AcceptancePolicyRequirementTargetingRestriction',
    'AcceptancePolicyRequirementTimeRestriction',
    'AcceptancePolicyRequirementTransparencyReporting',
    'AcceptancePolicyRule',
    'AcceptancePolicyRuleAppliesToItem',
    'AcceptancePolicyRuleDisposition',
    'AcceptedAttestationIssuers1',
    'AcceptedAttestationIssuers2',
    'AcceptedAttestationIssuersItemAgent',
    'AcceptedAttestationIssuersItemBrand',
    'AcceptedGovernanceAgents',
    'AcceptedIssuer',
    'AccessibilityViolationDetails',
    'AccessibilityViolationDetailsViolationsItem',
    'Account',
    'AccountAuthorization',
    'AccountChange',
    'AccountChangeActor',
    'AccountChangeActorType',
    'AccountChangeFeedSupported',
    'AccountChangeFeedUnsupported',
    'AccountChangeOrigin',
    'AccountChangeOriginKind',
    'AccountChangeRecordedWebhook',
    'AccountChangeRecordedWebhookResource',
    'AccountChangeRepair',
    'AccountChangeRepairTask',
    'AccountChangeRepairUnavailableReason',
    'AccountChangeResource',
    'AccountCreditLimit',
    'AccountCurrencyMode',
    'AccountGovernanceAgentsItem',
    'AccountIdentityChange',
    'AccountIdentityChange1',
    'AccountIdentityChange2',
    'AccountIdentityChangeBlocked',
    'AccountIdentityChangePending',
    'AccountIdentityChangePreview',
    'AccountIdentityChangePreview1',
    'AccountIdentityChangePreview2',
    'AccountIdentityChangePreview3',
    'AccountIdentityChangePreviewImpact',
    'AccountIdentityChangePreviewImpactArea',
    'AccountIdentityChangePreviewImpactEffect',
    'AccountIdentityChangePreviewNonblockingImpactsItem',
    'AccountIdentityChangePreviewNonblockingImpactsItemEffect',
    'AccountIdentityChangeRejected',
    'AccountIdentityChangeWouldApply',
    'AccountIdentityChangeWouldRequireApproval',
    'AccountIdentityUpdatesSupported',
    'AccountIdentityUpdatesSupportedSupportedChangesItem',
    'AccountIdentityUpdatesUnsupported',
    'AccountMovedDetails',
    'AccountNotificationsSupported',
    'AccountNotificationsSupportedEventTypesItem',
    'AccountNotificationsUnsupported',
    'AccountReference',
    'AccountReference1',
    'AccountReference2',
    'AccountReferenceAccountId',
    'AccountReferenceBrandOperator',
    'AccountReportingBucket',
    'AccountReportingBucketCompression',
    'AccountScope',
    'AccountSetup',
    'AccountSetupRequiredDetails',
    'AccountStatus',
    'AccountStatusChangedWebhook',
    'AccountStatusChangedWebhookReasonCode',
    'AccountStatusChangedWebhookSetup',
    'AccountTimezoneCapability',
    'AccountTimezoneCapabilityAccountSelection',
    'AccountTimezoneCapabilityMode',
    'AccountWithAuthorization',
    'AccountingPeriod',
    'Accounts',
    'Accounts1',
    'Accreditation',
    'AcquireRightsAcquired',
    'AcquireRightsAcquiredDisclosure',
    'AcquireRightsAcquiredRightsConstraint',
    'AcquireRightsError',
    'AcquireRightsPendingApproval',
    'AcquireRightsRejected',
    'AcquireRightsRequest',
    'AcquireRightsRequestCampaign',
    'AcquireRightsResponse',
    'AcquireRightsResponse1',
    'AcquireRightsResponse2',
    'AcquireRightsResponse3',
    'AcquireRightsResponse4',
    'Action3',
    'Action4',
    'Action9',
    'Action33',
    'ActionNotAllowedDetails',
    'ActionNotAllowedReason',
    'ActionSource',
    'ActivateSignalError',
    'ActivateSignalRequest',
    'ActivateSignalRequestAction',
    'ActivateSignalResponse',
    'ActivateSignalResponse1',
    'ActivateSignalResponse2',
    'ActivateSignalSuccess',
    'ActivationKey',
    'ActivationKey1',
    'ActivationKey2',
    'ActivationKeyKeyValue',
    'ActivationKeySegmentId',
    'AdCPAgentsAuthorization',
    'AdCPAgentsAuthorizationAuthoritativeLocation',
    'AdCPAgentsAuthorizationCommunityFormatRegistry',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds',
    'AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags',
    'AdCPAgentsAuthorizationCommunityFormatRegistryCollections',
    'AdCPAgentsAuthorizationCommunityFormatRegistryContact',
    'AdCPAgentsAuthorizationCommunityFormatRegistryFormats',
    'AdCPAgentsAuthorizationCommunityFormatRegistryFormatsItem',
    'AdCPAgentsAuthorizationCommunityFormatRegistryPlacementTagsValue',
    'AdCPAgentsAuthorizationCommunityFormatRegistryPlacements',
    'AdCPAgentsAuthorizationCommunityFormatRegistryProperties',
    'AdCPAgentsAuthorizationCommunityFormatRegistryPropertyFeaturesItem',
    'AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem',
    'AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItemReason',
    'AdCPAgentsAuthorizationCommunityFormatRegistrySignals',
    'AdCPAssetGroupVocabularyRegistry',
    'AdCPAssetTypeRegistry',
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
    'AdCPExtensionFileSchema',
    'AdCPExtensionRegistry',
    'AdCPFormatShapeVocabularyRegistry',
    'AdCPProtocol',
    'AdCPSpecialism',
    'AdCPVersionEnvelope',
    'AdInventoryConfiguration',
    'AdcpAgentsAuthorization',
    'AdcpAgentsAuthorization1',
    'AdcpAssetGroupVocabularyRegistry',
    'AdcpAssetTypeRegistry',
    'AdcpAsyncResponseData',
    'AdcpExtensionFileSchema',
    'AdcpExtensionRegistry',
    'AdcpFormatShapeVocabularyRegistry',
    'AdcpMajorVersion',
    'AdcpProtocol',
    'AdcpSpecialism',
    'AdcpVersion',
    'AdcpVersionEnvelope',
    'Adjustment',
    'AdvertiserIndustry',
    'AgeDeterminationBasis',
    'AgeVerificationMethod',
    'AgencyEstimateNumber',
    'AgentDeclarations',
    'AgentDeclarationsWebhookSigningAlgorithmsItem',
    'AgentEncryptionKey',
    'AgentNotificationConfig',
    'AgentNotificationConfigState',
    'AgentNotificationConfigStateAuthentication',
    'AgentPermissionDeniedDetails',
    'AgentPermissionDeniedDetailsReason',
    'AgentPlacementFormatDeclaration',
    'AgentReportingDestination',
    'AgentReportingDestination1',
    'AgentReportingDestination2',
    'AgentReportingDestination3',
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
    'AgenticadvertisingOrgVerificationTokenClaims',
    'Agents',
    'Allocations',
    'AllowedCardAssetTypesItem',
    'AllowedCardMediaAssetType',
    'AllowedStatus',
    'AllowedTargetingMode',
    'AnyOf1',
    'AnyOf2',
    'AnyOfItemAgentUrl',
    'AnyOfItemVerification',
    'AppItem',
    'AppItemPlatform',
    'ApplicablePackageID',
    'ApplicablePackageId',
    'AppliedPrincipalConfiguration',
    'AppliedPrincipalConfigurationAction',
    'AppliesTo',
    'AppliesTo1',
    'AppliesTo2',
    'AppliesToAccount',
    'AppliesToEnum',
    'AppliesToPublic',
    'Artifact',
    'ArtifactAssetAccessServiceAccountProvider',
    'ArtifactAssetsItemAudioTranscriptSource',
    'ArtifactAssetsItemTextContentFormat',
    'ArtifactAssetsItemTextRole',
    'ArtifactAssetsItemVideoTranscriptSource',
    'ArtifactIdentifiers',
    'ArtifactMetadata',
    'ArtifactRef',
    'ArtifactWebhookPayload',
    'ArtifactWebhookPayloadArtifactsItem',
    'ArtifactWebhookPayloadPagination',
    'AssessmentStatus',
    'Asset',
    'AssetAccess',
    'AssetAccess1',
    'AssetAccess2',
    'AssetAccess3',
    'AssetAccessBearerToken',
    'AssetAccessServiceAccount',
    'AssetAccessSignedUrl',
    'AssetContentType',
    'AssetOutsideAcceptedVersionIntersection',
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
    'Assets',
    'Assets1',
    'Assets2',
    'Assets3',
    'Assets4',
    'Assets9',
    'Assets10',
    'Assets11',
    'Assets12',
    'Assets13',
    'Assets14',
    'Assets15',
    'Assets16',
    'Assets17',
    'Assets18',
    'Assets19',
    'Assets20',
    'Assets21',
    'Assets22',
    'Assets23',
    'Assets24',
    'Assets25',
    'Assets26',
    'Assets27',
    'Assets28',
    'Assets29',
    'Assets31',
    'Assets32',
    'Assets33',
    'Assets34',
    'Assets35',
    'Assets36',
    'Assets37',
    'Assets38',
    'Assets39',
    'Assets40',
    'Assets41',
    'Assets42',
    'Assets43',
    'Assets44',
    'Assets45',
    'Assets46',
    'Assets47',
    'Assets48',
    'Assets49',
    'Assets50',
    'Assets51',
    'Assets94',
    'AssetsItemAudio',
    'AssetsItemAudioTranscriptFormat',
    'AssetsItemImage',
    'AssetsItemIndividual',
    'AssetsItemText',
    'AssetsItemVideo',
    'AssignOrUpdate',
    'AssignedPackage',
    'Assignment',
    'AssignmentOperations1',
    'AssignmentOperations2',
    'AssignmentOperations3',
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
    'AttestationClaim',
    'AttestationCredentialUriLocator',
    'AttestationEvaluation',
    'AttestationEvaluationActionBinding',
    'AttestationEvaluationOutcome',
    'AttestationIssuer',
    'AttestationIssuer1',
    'AttestationIssuer2',
    'AttestationIssuer3',
    'AttestationIssuerCredentialIdLocator',
    'AttestationOriginIssuer',
    'AttestationRef',
    'AttestationReference',
    'AttestationReferenceEmbeddedCredential',
    'AttestationReferenceValidityHint',
    'AttestationReferenceVerifyAgent',
    'AttestationResourceSubject',
    'AttestationSubject',
    'AttestationSubject1',
    'AttestationSubject2',
    'AttestationSubject3',
    'AttributeDefinition',
    'AttributeDefinitionRegulatoryBasisItem',
    'AttributionMethodology',
    'AttributionModel',
    'AttributionWindow',
    'AttributionWindowPostClick',
    'AttributionWindowPostView',
    'Audience',
    'AudienceActivationMethod',
    'AudienceActivationMethod1',
    'AudienceActivationMethod2',
    'AudienceActivationMethod3',
    'AudienceActivationMethod4',
    'AudienceActivationMethod5',
    'AudienceActivationMethod6',
    'AudienceActivationMethodFileTransfer',
    'AudienceActivationMethods1',
    'AudienceActivationMethods2',
    'AudienceActivationMethods3',
    'AudienceActivationMethods4',
    'AudienceActivationMethods5',
    'AudienceActivationMethodsItemCleanRoom',
    'AudienceActivationMethodsItemDatasetQuery',
    'AudienceActivationMethodsItemFileTransfer',
    'AudienceActivationMethodsItemPlatformDistribution',
    'AudienceActivationMethodsItemTmpIdentityMatch',
    'AudienceCharacteristic',
    'AudienceCharacteristicRange',
    'AudienceCharacteristicTaxonomy',
    'AudienceConstraints',
    'AudienceEvidence',
    'AudienceEvidenceAttestationRefsItem',
    'AudienceEvidenceAttestationRefsItemSubject',
    'AudienceEvidenceBaseline',
    'AudienceEvidenceEvidenceType',
    'AudienceEvidenceMethodology',
    'AudienceEvidencePin',
    'AudienceEvidencePins',
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
    'AudienceResolutionMethod',
    'AudienceSelector',
    'AudienceSelector1',
    'AudienceSelector2',
    'AudienceSelector3',
    'AudienceSelector4',
    'AudienceSelectorDescription',
    'AudienceSelectorSignalBinary',
    'AudienceSelectorSignalCategorical',
    'AudienceSelectorSignalNumeric',
    'AudienceSource1',
    'AudienceSource2',
    'AudienceStatus',
    'AudienceSubjectType',
    'AudienceTooSmallDetails',
    'AudioAsset',
    'AudioAssetRequirements',
    'AudioAssetRequirementsFormatsItem',
    'AudioChannel',
    'AudioChannelLayout',
    'AudioDistributionType',
    'AuthenticationScheme',
    'AuthoritativeLocationRedirect',
    'AuthorizationRequiredDetails',
    'AuthorizationResult',
    'AuthorizationResultStatus',
    'AuthorizationResultViolation',
    'AuthorizedAgentBaseFields',
    'AvailabilityStatus',
    'AvailableMetric',
    'AvailablePackage',
    'Avatar',
    'AxeExcludeSegment',
    'AxeIncludeSegment',
    'BaseCollectionSource',
    'BaseCollectionSource1',
    'BaseCollectionSource2',
    'BaseCollectionSource3',
    'BasePropertySource',
    'BasePropertySource1',
    'BasePropertySource2',
    'BasePropertySource3',
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
    'BillingNotPermittedForAgentDetails',
    'BillingNotSupportedDetails',
    'BillingNotSupportedDetailsScope',
    'BillingParty',
    'BinaryVerdict',
    'Bleed',
    'Bleed1',
    'BleedBottomLeftRightTop',
    'BleedUniform',
    'BlockedImpacts',
    'BoundedObject',
    'BoundedScalar',
    'BoundedValue',
    'BoundedValueLevel2',
    'BoundedValueLevel3',
    'BrandAgent',
    'BrandAgentType',
    'BrandCanonicalDocument',
    'BrandContext',
    'BrandDiscovery',
    'BrandDiscoveryAsset',
    'BrandDiscoveryAssetLibrary',
    'BrandDiscoveryAssetLibraryColorGuide',
    'BrandDiscoveryAssetLibraryColorGuidePalettesItem',
    'BrandDiscoveryAssetLibraryType',
    'BrandDiscoveryAuthorizedOperator',
    'BrandDiscoveryAuthorizedOperatorScopesItem',
    'BrandDiscoveryBorderRadius',
    'BrandDiscoveryBrand',
    'BrandDiscoveryBrandAgent',
    'BrandDiscoveryBrandAgentEntry',
    'BrandDiscoveryBrandAvatar',
    'BrandDiscoveryBrandCollectionsItem',
    'BrandDiscoveryBrandContact',
    'BrandDiscoveryBrandDisclaimersItem',
    'BrandDiscoveryBrandShapes',
    'BrandDiscoveryBrandShapesUsage',
    'BrandDiscoveryBrandVoiceSynthesis',
    'BrandDiscoveryColorConstraint',
    'BrandDiscoveryColorConstraintAppliesToItem',
    'BrandDiscoveryColorRef',
    'BrandDiscoveryColorRefKind',
    'BrandDiscoveryColorRefSurface',
    'BrandDiscoveryColors',
    'BrandDiscoveryColorway',
    'BrandDiscoveryCompositionRules',
    'BrandDiscoveryCompositionRulesBackgrounds',
    'BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem',
    'BrandDiscoveryCompositionRulesOverlays',
    'BrandDiscoveryCompositionRulesOverlaysGradientStyle',
    'BrandDiscoveryCompositionRulesTexture',
    'BrandDiscoveryCompositionRulesTextureIntensity',
    'BrandDiscoveryCompositionRulesTextureStyle',
    'BrandDiscoveryContact',
    'BrandDiscoveryDataSubjectContestation',
    'BrandDiscoveryElevation',
    'BrandDiscoveryFontFile',
    'BrandDiscoveryFontFileStyle',
    'BrandDiscoveryFontRole',
    'BrandDiscoveryFontRoleFamily',
    'BrandDiscoveryFonts',
    'BrandDiscoveryGraphicElement',
    'BrandDiscoveryGraphicElementOrientation',
    'BrandDiscoveryGraphicElementType',
    'BrandDiscoveryGraphicStyle',
    'BrandDiscoveryGraphicStyleStrokeStyle',
    'BrandDiscoveryGraphicStyleStyleType',
    'BrandDiscoveryGuidelineSeverity',
    'BrandDiscoveryHouse',
    'BrandDiscoveryHouseArchitecture',
    'BrandDiscoveryIconography',
    'BrandDiscoveryIconographyCornerStyle',
    'BrandDiscoveryIconographyStyle',
    'BrandDiscoveryIconographyUsage',
    'BrandDiscoveryIdentityRelyingParty',
    'BrandDiscoveryIdentityRelyingPartyScope',
    'BrandDiscoveryKellerType',
    'BrandDiscoveryLogo',
    'BrandDiscoveryLogoBackground',
    'BrandDiscoveryLogoOrientation',
    'BrandDiscoveryLogoPlacement',
    'BrandDiscoveryLogoPlacementBackgroundContrast',
    'BrandDiscoveryLogoPlacementPreferredPosition',
    'BrandDiscoveryLogoUsageRule',
    'BrandDiscoveryLogoUsageRuleMinimumSize',
    'BrandDiscoveryLogoVariant',
    'BrandDiscoveryMarkLockup',
    'BrandDiscoveryMarkLockupLockupType',
    'BrandDiscoveryMarkLockupOrdering',
    'BrandDiscoveryMarkLockupSeparator',
    'BrandDiscoveryMarkLockupSeparatorType',
    'BrandDiscoveryMotionGuidelines',
    'BrandDiscoveryMotionGuidelinesAnimationSpeed',
    'BrandDiscoveryMotionGuidelinesPacing',
    'BrandDiscoveryMotionGuidelinesTextEntrance',
    'BrandDiscoveryMotionGuidelinesTransitionStyle',
    'BrandDiscoveryPhotographyStyle',
    'BrandDiscoveryPhotographyStyleColorTemperature',
    'BrandDiscoveryPhotographyStyleContrast',
    'BrandDiscoveryPhotographyStyleDepthOfField',
    'BrandDiscoveryPhotographyStyleFraming',
    'BrandDiscoveryPhotographyStyleRealism',
    'BrandDiscoveryPhotographyStyleSubject',
    'BrandDiscoveryPhotographyStyleSubjectPeople',
    'BrandDiscoveryPhotographyStyleSubjectProductFocus',
    'BrandDiscoveryPortfolioEntry',
    'BrandDiscoveryProductCatalog',
    'BrandDiscoveryProductCatalogAgenticCheckout',
    'BrandDiscoveryProperty',
    'BrandDiscoveryPropertyRelationship',
    'BrandDiscoveryPropertyStore',
    'BrandDiscoveryRightsAgent',
    'BrandDiscoverySpacing',
    'BrandDiscoverySpacingScale',
    'BrandDiscoveryTrademark',
    'BrandDiscoveryTrademarkLicenseType',
    'BrandDiscoveryTrademarkStatus',
    'BrandDiscoveryTypeScaleEntry',
    'BrandDiscoveryTypeScaleEntryTextTransform',
    'BrandDiscoveryVisualGuidelines',
    'BrandDiscoveryVisualGuidelinesTypeScale',
    'BrandID',
    'BrandId',
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
    'Breakpoint',
    'BriefAsset',
    'Browser',
    'BrowserExclude',
    'BrowserFamily',
    'BrowserRequirement',
    'BrowserRequirement1',
    'BrowserRequirementFamilies',
    'BrowserSupport',
    'BrowserSupport1',
    'BrowserSupportFamilies',
    'Budget',
    'Budget2',
    'BudgetAllocation',
    'BudgetAllocation1',
    'BudgetAllocation2',
    'BudgetAllocationFixed',
    'BudgetAllocationSellerOptimized',
    'BudgetChangeConstraints',
    'BudgetRange',
    'BudgetReallocationThreshold',
    'BudgetReallocationUnlimited',
    'BudgetTooLowDetails',
    'BuildCreativeAsyncInputRequired',
    'BuildCreativeAsyncSubmitted',
    'BuildCreativeAsyncWorking',
    'BuildCreativeError',
    'BuildCreativeEstimate',
    'BuildCreativeEstimateEstimate',
    'BuildCreativeEstimateEstimateBasis',
    'BuildCreativeEstimateEstimatePerLeafItem',
    'BuildCreativeInputRequired',
    'BuildCreativeInputRequiredReason',
    'BuildCreativeMultiSuccess',
    'BuildCreativeMultiSuccessPreview',
    'BuildCreativeMultiSuccessPreviewPreviewsItem',
    'BuildCreativeMultiSuccessPreviewPreviewsItemInput',
    'BuildCreativeRequest',
    'BuildCreativeRequestMaxSpend',
    'BuildCreativeRequestMode',
    'BuildCreativeRequestSignalConditionsItem',
    'BuildCreativeRequestVariantAxis',
    'BuildCreativeRequestVariantAxisDimension',
    'BuildCreativeResponse',
    'BuildCreativeResponse1',
    'BuildCreativeResponse2',
    'BuildCreativeResponse3',
    'BuildCreativeResponse4',
    'BuildCreativeResponse5',
    'BuildCreativeResponse6',
    'BuildCreativeResponseSubmitted',
    'BuildCreativeSubmitted',
    'BuildCreativeSuccess',
    'BuildCreativeSuccessPreview',
    'BuildCreativeSuccessPreviewPreviewsItem',
    'BuildCreativeSuccessPreviewPreviewsItemInput',
    'BuildCreativeVariantSuccess',
    'BuildCreativeVariantSuccessBudgetStatus',
    'BuildCreativeVariantSuccessCreativesItem',
    'BuildCreativeVariantSuccessCreativesItemCatalogItemRef',
    'BuildCreativeVariantSuccessCreativesItemVariantsItem',
    'BuildCreativeVariantSuccessCreativesItemVariantsItemEval',
    'BuildCreativeVariantSuccessKeepModeApplied',
    'BuildCreativeWorking',
    'BusinessEntity',
    'BusinessEntityAddress',
    'BusinessEntityBank',
    'BusinessEntityContactsItem',
    'BusinessEntityContactsItemRole',
    'BuyProductsInputRequired',
    'BuyProductsRequest',
    'BuyProductsRequestBranch1Account',
    'BuyProductsRequestBranch1AccountAccountId',
    'BuyProductsRequestBranch1AccountBrandOperator',
    'BuyProductsRequestBrand',
    'BuyProductsRequestOpportunity',
    'BuyProductsResponse',
    'BuyProductsSubmitted',
    'BuyProductsWorking',
    'BuyerAgent',
    'ByPackageItem',
    'ByPackageItem1',
    'C2PAWatermarkAction',
    'C2PaWatermarkAction',
    'CPAPricingOption',
    'CPCPricingOption',
    'CPCVPricingOption',
    'CPMPricingOption',
    'CPPPricingOption',
    'CPPPricingOptionParameters',
    'CPVPricingOption',
    'CPVPricingOptionParameters',
    'CSSAsset',
    'CSSAssetRequirements',
    'CTVAdExperience',
    'CalibrateContentRequest',
    'CalibrateContentResponse',
    'CalibrateContentResponse1',
    'CalibrateContentResponse2',
    'CalibrateContentResponseVerdict',
    'CalibrateContentResponseVerdictFeaturesItem',
    'CanceledBy',
    'Cancellation',
    'CancellationPolicy',
    'CancellationPolicyCancellationFee',
    'CancellationPolicyCancellationFeeType',
    'CanonicalAccountReference',
    'CanonicalAccountReference1',
    'CanonicalAccountReference2',
    'CanonicalAccountReferenceAccountId',
    'CanonicalAccountReferenceBrandOperator',
    'CanonicalAudienceEvidence',
    'CanonicalAudienceEvidenceSelection',
    'CanonicalBudgetAllocation',
    'CanonicalBudgetAllocation1',
    'CanonicalBudgetAllocation2',
    'CanonicalBudgetAllocationFixed',
    'CanonicalBudgetAllocationSellerOptimized',
    'CanonicalDeliveryForecast',
    'CanonicalForecastPoint',
    'CanonicalForecastPointMetrics',
    'CanonicalForecastPointViewability',
    'CanonicalForecastVendorMetricValue',
    'CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement',
    'CanonicalFormatAgentPlacementAISurfaceSponsoredPlacementOutputModality',
    'CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement',
    'CanonicalFormatBase',
    'CanonicalFormatBaseCompositionModel',
    'CanonicalFormatBaseReferenceMutability',
    'CanonicalFormatBaseSlotsItem',
    'CanonicalFormatBaseSlotsItemAssetType',
    'CanonicalFormatCoordinatedPlacements',
    'CanonicalFormatCoordinatedPlacementsComponentsItem',
    'CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy',
    'CanonicalFormatCoordinatedPlacementsSharedSlotsItem',
    'CanonicalFormatCoordinatedPlacementsSharedSlotsItemAssetType',
    'CanonicalFormatDAASTAudio',
    'CanonicalFormatDaastAudio',
    'CanonicalFormatDisplayTag',
    'CanonicalFormatDisplayTagSizesItem',
    'CanonicalFormatDisplayTagSupportedDeliveryTypesItem',
    'CanonicalFormatDisplayTagSupportedTagTypesItem',
    'CanonicalFormatHTML5Banner',
    'CanonicalFormatHTML5BannerMraidVersion',
    'CanonicalFormatHTML5BannerSizesItem',
    'CanonicalFormatHostedAudio',
    'CanonicalFormatHostedAudioAssetSource',
    'CanonicalFormatHostedAudioAudioChannelsItem',
    'CanonicalFormatHostedAudioAudioCodecsItem',
    'CanonicalFormatHostedAudioBuyerAssetAcceptance',
    'CanonicalFormatHostedVideo',
    'CanonicalFormatHostedVideoAudioCodecsItem',
    'CanonicalFormatHostedVideoBuyerAssetAcceptance',
    'CanonicalFormatHostedVideoCaptions',
    'CanonicalFormatHostedVideoOrientation',
    'CanonicalFormatHostedVideoVideoCodecsItem',
    'CanonicalFormatHtml5Banner',
    'CanonicalFormatImage',
    'CanonicalFormatImageBuyerAssetAcceptance',
    'CanonicalFormatImageCarousel',
    'CanonicalFormatImageImageFormatsItem',
    'CanonicalFormatImageMotionLevel',
    'CanonicalFormatImageSizesItem',
    'CanonicalFormatKind',
    'CanonicalFormatManifest',
    'CanonicalFormatNativeInFeed',
    'CanonicalFormatNativeInFeedAssetSource',
    'CanonicalFormatNativeInFeedBuyerAssetAcceptance',
    'CanonicalFormatNativeInFeedFocusBehavior',
    'CanonicalFormatNativeInFeedIconSize',
    'CanonicalFormatNativeInFeedImageFormatsItem',
    'CanonicalFormatNativeInFeedMainImageSizesItem',
    'CanonicalFormatNativeInFeedMenuPlacement',
    'CanonicalFormatOption',
    'CanonicalFormatOptionFormatKind',
    'CanonicalFormatResponsiveCreative',
    'CanonicalFormatSellerRenderedStatefulDisplay',
    'CanonicalFormatSellerRenderedStatefulDisplayContainersItem',
    'CanonicalFormatSellerRenderedStatefulDisplayReveal',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItem',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemAnchoring',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItem',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItemWidthMode',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemMotion',
    'CanonicalFormatSellerRenderedStatefulDisplaySupplyMode',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItem',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemDirection',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemInput',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemMediaEvent',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemScrollReference',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTransitionMode',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTrigger',
    'CanonicalFormatSellerRenderedStatefulDisplayUserControls',
    'CanonicalFormatSellerRenderedStatefulDisplayVideoPlayback',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenFanoutMode',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenItemProductionModel',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenSupportedIdTypesItem',
    'CanonicalFormatTarget',
    'CanonicalFormatVASTAudio',
    'CanonicalFormatVASTVideo',
    'CanonicalFormatVASTVideoCreativeType',
    'CanonicalFormatVASTVideoVpaidVersion',
    'CanonicalFormatVastAudio',
    'CanonicalFormatVastVideo',
    'CanonicalMeasurementTerms',
    'CanonicalMeasurementTermsBillingMeasurement',
    'CanonicalMeasurementTermsMakegoodPolicy',
    'CanonicalMediaBuyAction',
    'CanonicalMediaBuyAction1',
    'CanonicalMediaBuyAction2',
    'CanonicalMediaBuyActionControlMediaBuy',
    'CanonicalMediaBuyActionControlMediaBuyAction',
    'CanonicalMediaBuyActionFields',
    'CanonicalMediaBuyActionMode',
    'CanonicalMediaBuyActionName',
    'CanonicalMediaBuyActionRefineProposals',
    'CanonicalMediaBuyActionRefineProposalsAction',
    'CanonicalMediaBuyActionSyncCreatives',
    'CanonicalMediaBuyActionSyncCreativesAction',
    'CanonicalMediaBuyFeatures',
    'CanonicalMetricQualifier',
    'CanonicalOptimizationGoal',
    'CanonicalOptimizationGoal1',
    'CanonicalOptimizationGoal2',
    'CanonicalOptimizationGoal3',
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
    'CanonicalProductPlacement1',
    'CanonicalProductPlacement2',
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
    'CanonicalReportingCommitment1',
    'CanonicalReportingCommitment2',
    'CanonicalReportingCommitmentStandard',
    'CanonicalReportingCommitmentVendor',
    'CanvasConstraint',
    'CanvasConstraintConstraint',
    'CanvasConstraintRegion',
    'CanvasConstraintRegionUnit',
    'CapabilitiesChangedWebhook',
    'CapabilitiesChangedWebhookReason',
    'CapabilityChangeNotificationsSupported',
    'CapabilityChangeNotificationsSupportedEventTypesItem',
    'CapabilityChangeNotificationsSupportedRegistrationTask',
    'CapabilityChangeNotificationsUnsupported',
    'CardAsset',
    'Catalog',
    'CatalogAction',
    'CatalogAsset',
    'CatalogExecutionRequirement',
    'CatalogFieldBinding',
    'CatalogFieldBinding1',
    'CatalogFieldBindingAssetPool',
    'CatalogFieldBindingAssetPoolBinding',
    'CatalogFieldBindingCatalogGroup',
    'CatalogFieldBindingScalar',
    'CatalogFieldBindingScalarBinding',
    'CatalogFieldMapping',
    'CatalogFieldMappingTransform',
    'CatalogIds',
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
    'CatalogItemStatus',
    'CatalogRequirements',
    'CatalogSelection',
    'CatalogType',
    'Catchment',
    'CatchmentGeometry',
    'CatchmentRadius',
    'CatchmentTransportModeTravelTime',
    'Category',
    'ChangeFeed',
    'ChangedFields',
    'Channel',
    'ChannelAllocation',
    'CheckGovernanceRequest',
    'CheckGovernanceRequestDeliveryMetrics',
    'CheckGovernanceRequestDeliveryMetricsAudienceDistribution',
    'CheckGovernanceRequestDeliveryMetricsAudienceDistributionBaseline',
    'CheckGovernanceRequestDeliveryMetricsPacing',
    'CheckGovernanceRequestRuntimeAttestationsItem',
    'CheckGovernanceRequestRuntimeAttestationsItemSubject',
    'CheckGovernanceResponse',
    'CheckGovernanceResponseCheckType',
    'CheckGovernanceResponseConditionsItem',
    'CheckGovernanceResponseDeliveryStatement',
    'CheckGovernanceResponseDeliveryStatementCanonicalPayload',
    'CheckGovernanceResponseFindingsItem',
    'CheckGovernanceResponseRuntimeAttestationEvaluationsItem',
    'CheckGovernanceResponseRuntimeAttestationEvaluationsItemActionBinding',
    'ClaimEntry',
    'CleanRoom',
    'CloudStorageProtocol',
    'CoBrandingRequirement',
    'Codes',
    'Collection',
    'CollectionCadence',
    'CollectionDeliveryMetrics',
    'CollectionDistribution',
    'CollectionDistributionIdentifiersItem',
    'CollectionKind',
    'CollectionList',
    'CollectionListApplication',
    'CollectionListApplicationEffect',
    'CollectionListApplicationSummary',
    'CollectionListChangedWebhook',
    'CollectionListChangedWebhookChangeSummary',
    'CollectionListFilters',
    'CollectionListReference',
    'CollectionPropertyDeliveryMetrics',
    'CollectionReference',
    'CollectionRelatedCollectionsItem',
    'CollectionRelationship',
    'CollectionSelection',
    'CollectionSelection1',
    'CollectionSelection2',
    'CollectionSelector',
    'CollectionStatus',
    'Color',
    'ColorRefName',
    'ColorRefSurface',
    'ColorRefValue',
    'ColorValue',
    'CommercialTerms',
    'CommercialTermsCancellationTerms',
    'CommercialTermsPurchasesItem',
    'CommercialTermsReportingCommitmentsItem',
    'CommitmentError',
    'CommitmentSubmitted',
    'CommittedMediaBuy',
    'CommittedMediaBuyAcceptedProposal',
    'CommittedMediaBuyPurchaseBindingsItem',
    'CommittedMediaBuyWarningsItem',
    'CommittedMediaBuyWarningsItemCode',
    'CommittedMetric',
    'CommittedMetric1',
    'CommittedMetric2',
    'CommittedMetricStandard',
    'CommittedMetricVendor',
    'CommittedMetricVendorQualifier',
    'CommittedMetrics2',
    'CommittedMetricsItemVendor',
    'CommittedProposalExecution',
    'CompactTaskInputRequired',
    'CompactTaskSubmitted',
    'CompactTaskWorking',
    'CompatibilityPurchaseCoordinatorInput',
    'CompletionSource',
    'ComplianceTaskCompletionData',
    'ComplyTestControllerRequest',
    'ComplyTestControllerRequestAccount',
    'ComplyTestControllerRequestParams',
    'ComplyTestControllerRequestParamsAdvanceTo',
    'ComplyTestControllerRequestParamsArm',
    'ComplyTestControllerRequestParamsDoohMetrics',
    'ComplyTestControllerRequestParamsMetricsItem',
    'ComplyTestControllerRequestParamsOperation',
    'ComplyTestControllerRequestParamsPurgeKind',
    'ComplyTestControllerRequestParamsViewability',
    'ComplyTestControllerResponse',
    'ComplyTestControllerResponse1',
    'ComplyTestControllerResponse2',
    'ComplyTestControllerResponse4',
    'ComplyTestControllerResponse5',
    'ComplyTestControllerResponse6',
    'ComplyTestControllerResponse7',
    'ComplyTestControllerResponse8',
    'Component',
    'ComponentValue',
    'Components',
    'Components1',
    'Components2',
    'Components3',
    'Components4',
    'Components5',
    'Components6',
    'Components7',
    'Components8',
    'Components9',
    'Components10',
    'Components11',
    'Components12',
    'Components13',
    'ComponentsItemFormatKindParams',
    'ComponentsItemFormatKindParamsAgentPlacement',
    'ComponentsItemFormatKindParamsAudioDaast',
    'ComponentsItemFormatKindParamsAudioHosted',
    'ComponentsItemFormatKindParamsDisplayTag',
    'ComponentsItemFormatKindParamsHtml5',
    'ComponentsItemFormatKindParamsImage',
    'ComponentsItemFormatKindParamsImageCarousel',
    'ComponentsItemFormatKindParamsNativeInFeed',
    'ComponentsItemFormatKindParamsResponsiveCreative',
    'ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay',
    'ComponentsItemFormatKindParamsSponsoredPlacement',
    'ComponentsItemFormatKindParamsVideoHosted',
    'ComponentsItemFormatKindParamsVideoVast',
    'ComponentsItemFormatOptionRef',
    'Condition',
    'ConflictDetails',
    'ConsentBasis',
    'ConsentScopeEnum',
    'ConsumerIdentity',
    'Contact',
    'Content',
    'ContentIDType',
    'ContentIdType',
    'ContentRating',
    'ContentRatingSystem',
    'ContentStandards',
    'ContentStandardsCalibrationExemplars',
    'ContextMatchRequest',
    'ContextMatchRequestArtifactRefsItem',
    'ContextMatchRequestArtifactRefsItemType',
    'ContextMatchRequestContextSignals',
    'ContextMatchRequestContextSignalsSentiment',
    'ContextMatchRequestGeo',
    'ContextMatchRequestGeoMetro',
    'ContextMatchResponseProviderRouter',
    'ContextMatchResponseProviderRouterSignals',
    'ContextMatchResponseProviderRouterTargetingKvs',
    'ContextMatchResponseRouterPublisher',
    'ContextMatchResponseRouterPublisherSignals',
    'ContextMatchResponseRouterPublisherSignalsByProviderValue',
    'ContextMatchResponseRouterPublisherTargetingKvs',
    'ContextMatchResponseRouterPublisherTargetingKvsItem',
    'ContextObject',
    'ControlApplied',
    'ControlAppliedWarningsItem',
    'ControlError',
    'ControlMediaBuyInputRequired',
    'ControlMediaBuyRequest',
    'ControlMediaBuyResponse',
    'ControlMediaBuyResponse1',
    'ControlMediaBuyResponse2',
    'ControlMediaBuyResponse3',
    'ControlMediaBuyResponseCompleted',
    'ControlMediaBuyResponseFailed',
    'ControlMediaBuyResponseSubmitted',
    'ControlMediaBuySubmitted',
    'ControlMediaBuyWorking',
    'ControlSubmitted',
    'ControllerError',
    'ControllerErrorError',
    'CoordinatedPlacementsFormatDeclaration',
    'Countries',
    'Countries3',
    'CountryCode',
    'CountryFusedPostalCodeSystem',
    'CountrySupport',
    'CountrySupport1',
    'CountrySupportMaxValuesPerPackage',
    'CpaPricingOption',
    'CpcPricingOption',
    'CpcvPricingOption',
    'CpmPricing',
    'CpmPricingOption',
    'CppPricingOption',
    'CpvPricingOption',
    'CreateCollectionListRequest',
    'CreateCollectionListResponse',
    'CreateContentStandardsRequest',
    'CreateContentStandardsRequestCalibrationExemplars',
    'CreateContentStandardsRequestScope',
    'CreateContentStandardsResponse',
    'CreateContentStandardsResponse1',
    'CreateContentStandardsResponse2',
    'CreateContentStandardsResponseErrors',
    'CreateContentStandardsResponseStandardsId',
    'CreateMediaBuyAsyncInputRequired',
    'CreateMediaBuyAsyncSubmitted',
    'CreateMediaBuyAsyncWorking',
    'CreateMediaBuyCompletion',
    'CreateMediaBuyError',
    'CreateMediaBuyInputRequired',
    'CreateMediaBuyInputRequiredReason',
    'CreateMediaBuyRequest',
    'CreateMediaBuyRequestArtifactWebhook',
    'CreateMediaBuyRequestArtifactWebhookBatchFrequency',
    'CreateMediaBuyRequestArtifactWebhookDeliveryMode',
    'CreateMediaBuyRequestBidding',
    'CreateMediaBuyRequestIoAcceptance',
    'CreateMediaBuyRequestOpportunity',
    'CreateMediaBuyResponse',
    'CreateMediaBuyResponse1',
    'CreateMediaBuyResponse2',
    'CreateMediaBuyResponse3',
    'CreateMediaBuyResponseSubmitted',
    'CreateMediaBuySubmitted',
    'CreateMediaBuySuccess',
    'CreateMediaBuySuccessBidding',
    'CreateMediaBuyWorking',
    'CreatePropertyListRequest',
    'CreatePropertyListResponse',
    'CreativeAction',
    'CreativeActivationMethod',
    'CreativeAgent',
    'CreativeAgentCapability',
    'CreativeApproval',
    'CreativeApprovalError',
    'CreativeApprovalRequest',
    'CreativeApprovalResponse',
    'CreativeApprovalResponse1',
    'CreativeApprovalResponse2',
    'CreativeApprovalResponse3',
    'CreativeApprovalResponse4',
    'CreativeApprovalStatus',
    'CreativeApprovalsItemIndicatorTypesEvaluatedItem',
    'CreativeApproved',
    'CreativeAsset',
    'CreativeAssets',
    'CreativeAssignment',
    'CreativeAssignmentChangedWebhook',
    'CreativeAssignmentChangedWebhookChangeKind',
    'CreativeAssignmentRotationMode',
    'CreativeAuditObservation',
    'CreativeAuditObservationCode',
    'CreativeAuditObservationDetails',
    'CreativeAuditObservationDetailsClaimedValue',
    'CreativeAuditObservationDetailsClaimedValueHumanOversight',
    'CreativeAuditObservationRecovery',
    'CreativeAuditObservationSeverity',
    'CreativeBrief',
    'CreativeBriefCompliance',
    'CreativeBriefComplianceRequiredDisclosuresItem',
    'CreativeBriefMessaging',
    'CreativeBriefObjective',
    'CreativeCapabilityTarget',
    'CreativeConsumption',
    'CreativeDeliveryMetrics',
    'CreativeEventReasonCode',
    'CreativeFeatureResult',
    'CreativeFeaturesItemRange',
    'CreativeFeaturesItemType',
    'CreativeFilters',
    'CreativeIdentifierType',
    'CreativeItem',
    'CreativeItem1',
    'CreativeItem2',
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
    'CreativeMotionLevel',
    'CreativeOperationFormatDeclaration',
    'CreativePendingReview',
    'CreativePolicy',
    'CreativePolicyAcceptedVerifiersItem',
    'CreativePolicyProvenanceRequirements',
    'CreativePurgedWebhook',
    'CreativePurgedWebhookInitiator',
    'CreativeQuality',
    'CreativeRejected',
    'CreativeRejectedDetails',
    'CreativeRepresentation',
    'CreativeRepresentationFormatId',
    'CreativeRepresentationFormatKind',
    'CreativeRepresentationSet',
    'CreativeRepresentationSource',
    'CreativeRepresentationUnresolvedDetails',
    'CreativeRevisionContentMismatchDetails',
    'CreativeRevisionID',
    'CreativeRevisionId',
    'CreativeSelectionStrategy',
    'CreativeSortField',
    'CreativeStatus',
    'CreativeStatusChangedWebhook',
    'CreativeStatusChangedWebhookTransition',
    'CreativeStatusChangedWebhookTransitionFrom',
    'CreativeVariable',
    'CreativeVariableVariableType',
    'CreativeVariant',
    'CreativeVariantGenerationContext',
    'CreativeVariantGenerationContextArtifact',
    'Creatives',
    'Creatives1',
    'CreativesItemFormatId',
    'CreativesItemFormatKind',
    'CssAsset',
    'CssAssetRequirements',
    'CtvAdExperience',
    'CurrencyCode',
    'CurrentPrincipalConfiguration',
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
    'DAASTTrackingEvent',
    'DAASTVersion',
    'DOOHMotionType',
    'DaastAsset',
    'DaastAsset3',
    'DaastAsset4',
    'DaastAssetRequirements',
    'DaastOffset',
    'DaastTrackerAsset',
    'DaastTrackerConstraints',
    'DaastTrackingEvent',
    'DaastVersion',
    'DaastVersions',
    'DailyBudgetCap',
    'DataProviderSignalSelector',
    'DataProviderSignalSelector1',
    'DataProviderSignalSelector2',
    'DataProviderSignalSelector3',
    'DataProviderSignalSelectorAll',
    'DataProviderSignalSelectorById',
    'DataProviderSignalSelectorByTag',
    'DataSource',
    'Dataset',
    'DatasetQuery',
    'DatasetQueryConsumerIdentitiesItem',
    'DatasetShare',
    'DatasetShareRecipient',
    'DateRange',
    'DatetimeRange',
    'DayOfWeek',
    'DaypartRequirement',
    'DaypartRequirement1',
    'DaypartRequirementTimezoneModes',
    'DaypartSupport',
    'DaypartSupport1',
    'DaypartSupportTimezoneModes',
    'DaypartTarget',
    'DaypartTargets',
    'DaypartTimezoneMode',
    'DeadlinePolicy',
    'DeadlinePolicyMaterialStagesItem',
    'DecimalReportingControlTotal',
    'DeclineProposalsInputRequired',
    'DeclineProposalsRequest',
    'DeclineProposalsResponse',
    'DeclineProposalsResponse1',
    'DeclineProposalsResponseResults',
    'DeclineProposalsResponseResultsItem',
    'DeclineProposalsResponseResultsItemOutcome',
    'DeclineProposalsResponseResultsItemUnable',
    'DeclineProposalsResponseSubmitted',
    'DeclineProposalsSubmitted',
    'DeclineProposalsWorking',
    'Delegation',
    'DelegationAuthority',
    'DelegationType',
    'DeleteCollectionListRequest',
    'DeleteCollectionListResponse',
    'DeletePropertyListRequest',
    'DeletePropertyListResponse',
    'DeliveryAuth',
    'DeliveryBreakdownControls',
    'DeliveryConfigGeneration',
    'DeliveryForecast',
    'DeliveryMetricAggregate',
    'DeliveryMetricAggregate2',
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
    'DeliveryRecipientCloud',
    'DeliveryRecord',
    'DeliveryStatus',
    'DeliveryType',
    'DemographicAgeRange',
    'DemographicPredicate',
    'DemographicReportingCapability',
    'DemographicReportingCapabilityAge',
    'DemographicReportingCapabilityAgeIntervalsItem',
    'DemographicReportingCapabilityAgeReportingModesItem',
    'DemographicSystem',
    'DemographicTargetingCapability',
    'DemographicTargetingCapabilityAge',
    'DemographicTargetingCapabilityAgeExecutionModesItem',
    'DemographicTargetingCapabilityAgeIntervalsItem',
    'DemographicTargetingCapabilityAgeUnknownHandling',
    'DemographicTargetingIntent',
    'DemographicTargetingIntentAge',
    'DemographicTargetingResolution',
    'Deployment',
    'Deployment1',
    'Deployment2',
    'DeploymentAgent',
    'DeploymentPlatform',
    'DerivativeType',
    'Destination',
    'Destination1',
    'Destination2',
    'DestinationAgent',
    'DestinationItem',
    'DestinationItemDestinationType',
    'DestinationItemLocation',
    'DestinationMode',
    'DestinationPlatform',
    'DevicePlatform',
    'DevicePlatformExclude',
    'DevicePlatformForecastDimension',
    'DeviceType',
    'DeviceTypeExclude',
    'DeviceTypeForecastDimension',
    'DiagnosticIssue',
    'DiagnosticIssueSeverity',
    'DigestAttestation',
    'DigitalSourceType',
    'DimensionUnit',
    'Dimensions',
    'DirectIdentifiersSource',
    'Direction',
    'DisclosureCapability',
    'DisclosurePersistence',
    'DisclosurePosition',
    'DisplayTagAsset',
    'DisplayTagAsset4',
    'DisplayTagAsset5',
    'DisplayTagAsset6',
    'DisplayTagFormatDeclaration',
    'DistanceUnit',
    'DistributionIDsSource',
    'DistributionIDsSourceIdentifiersItem',
    'DistributionIdentifierType',
    'DomainBreakdown',
    'DomainName',
    'DoohMotionType',
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
    'Effect',
    'Effect1',
    'EffectiveTimingConstraints',
    'EmbeddedProvenanceMethod',
    'EndTime',
    'Entry',
    'Error',
    'ErrorBuyerReason',
    'ErrorCode',
    'ErrorIssuesItem',
    'ErrorIssuesItemDiscriminatorItem',
    'ErrorRecovery',
    'ErrorScope',
    'ErrorSource',
    'Escalation',
    'EscalationSeverity',
    'EvaluatorSpec',
    'EvaluatorSpec1',
    'EvaluatorSpec2',
    'EvaluatorSpec3',
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
    'EventType',
    'Excluded',
    'ExcludedBy',
    'Exclusion',
    'Exclusivity',
    'Execution',
    'Execution1',
    'Execution2',
    'ExecutionContinuousBounds',
    'ExecutionEnumeratedIntervals',
    'ExecutionMode',
    'ExecutionRequirementUnmetDetails',
    'ExecutionRequirementUnmetDetailsUnmetRequirementsItem',
    'ExecutionRequirementUnmetDetailsUnmetRequirementsItemReason',
    'ExecutionSignals',
    'ExperimentalFeatureID',
    'ExperimentalFeatureId',
    'ExplicitPackagesWithFixedAllocation',
    'ExplicitPackagesWithFixedAllocationBudgetAllocation',
    'ExplicitPackagesWithFixedAllocationPackagesItem',
    'ExplicitPackagesWithSellerOptimizedAllocation',
    'ExplicitPackagesWithSellerOptimizedAllocationBudgetAllocation',
    'ExtensionObject',
    'ExtensionsSupportedItem',
    'Facet',
    'FailedLookup',
    'FailedPrincipalRead',
    'FailedPrincipalSync',
    'FailedReportingConsumerStatus',
    'FailedReportingReceipt',
    'FailureKind',
    'FeatureCheckStatus',
    'FeatureRequirement',
    'FeatureRequirementIfNotCovered',
    'Features',
    'FeedFormat',
    'FeedbackSource',
    'FieldTruncation',
    'Fields',
    'FileTransferDestination',
    'FileTransferDirectionsItem',
    'FileTransferFormat',
    'FinalityPolicies',
    'FinalityPolicies1',
    'FinalityPolicies2',
    'FinalityPoliciesItemContractualCutoff',
    'FinalityPoliciesItemSourceFinal',
    'FinalityPoliciesItemStabilized',
    'FlatFeePricing',
    'FlatFeePricingPeriod',
    'FlatRatePricingOption',
    'FlatRatePricingOptionParameters',
    'FlightChangeConstraints',
    'FlightItem',
    'FlightItemDestination',
    'FlightItemOrigin',
    'FontRole2',
    'ForcedDirectiveSuccess',
    'ForcedDirectiveSuccessForced',
    'ForecastMethod',
    'ForecastPoint',
    'ForecastPointDimensions',
    'ForecastPointMetrics',
    'ForecastPointMetricsCoverageRate',
    'ForecastPointViewability',
    'ForecastPointViewabilityViewableRate',
    'ForecastRange',
    'ForecastRangeUnit',
    'ForecastRateRange',
    'ForecastVendorMetricValue',
    'ForecastableMetric',
    'Format',
    'FormatAccessibility',
    'FormatBaseGroupAsset',
    'FormatBaseIndividualAsset',
    'FormatDisclosureCapabilitiesItem',
    'FormatFormatCard',
    'FormatFormatCardDetailed',
    'FormatIDParameter',
    'FormatIdParameter',
    'FormatOptionReference',
    'FormatOptionReference1',
    'FormatOptionRefs',
    'FormatOptions',
    'FormatOptionsItemFormatOptionId',
    'FormatReferenceStructuredObject',
    'FormatRendersItem',
    'FormatRendersItemDimensions',
    'FormatRendersItemDimensionsResponsive',
    'FormatsItemAgentPlacement',
    'FormatsItemAudioDaast',
    'FormatsItemAudioHosted',
    'FormatsItemAudioVast',
    'FormatsItemCoordinatedPlacements',
    'FormatsItemCustom',
    'FormatsItemDisplayTag',
    'FormatsItemHtml5',
    'FormatsItemImage',
    'FormatsItemImageCarousel',
    'FormatsItemNativeInFeed',
    'FormatsItemResponsiveCreative',
    'FormatsItemSellerRenderedStatefulDisplay',
    'FormatsItemSponsoredPlacement',
    'FormatsItemVideoHosted',
    'FormatsItemVideoVast',
    'FrameRateType',
    'FrequencyCap',
    'FrequencyCapConstraints',
    'FrequencyCapControlMode',
    'FrequencyCapDurationUnit',
    'FrequencyCapImpressionConstraints',
    'FrequencyCapImpressionConstraintsAllowedValues',
    'FrequencyCapImpressionConstraintsMaximumMinimum',
    'FrequencyCapIntervalConstraints',
    'FrequencyCapIntervalConstraintsAllowedIntervals',
    'FrequencyCapIntervalConstraintsMaximumIntervalMinimumInterval',
    'FrequencyCapMutableField',
    'FrequencyCapRequirements',
    'FrequencyCapScope',
    'FrequencyCapSuppress',
    'FrequencyCapWindow',
    'GOPType',
    'GenerationCredential',
    'GenreTaxonomy',
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
    'GeographicTargetingLevel',
    'Geometry',
    'GetAccountFinancialsError',
    'GetAccountFinancialsRequest',
    'GetAccountFinancialsResponse',
    'GetAccountFinancialsResponse1',
    'GetAccountFinancialsResponse2',
    'GetAccountFinancialsSuccess',
    'GetAccountFinancialsSuccessBalance',
    'GetAccountFinancialsSuccessBalanceLastTopUp',
    'GetAccountFinancialsSuccessCredit',
    'GetAccountFinancialsSuccessInvoicesItem',
    'GetAccountFinancialsSuccessInvoicesItemStatus',
    'GetAccountFinancialsSuccessPaymentStatus',
    'GetAccountFinancialsSuccessSpend',
    'GetAdCPCapabilitiesRequest',
    'GetAdCPCapabilitiesRequestProtocolsItem',
    'GetAdCPCapabilitiesResponse',
    'GetAdCPCapabilitiesResponseAccount',
    'GetAdCPCapabilitiesResponseAdcp',
    'GetAdCPCapabilitiesResponseAdcpCapabilityChanges',
    'GetAdCPCapabilitiesResponseAdcpGovernanceEnforcement',
    'GetAdCPCapabilitiesResponseAdcpPrincipal',
    'GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItem',
    'GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern',
    'GetAdCPCapabilitiesResponseAdcpPrincipalSupportedSectionsItem',
    'GetAdCPCapabilitiesResponseBrand',
    'GetAdCPCapabilitiesResponseBudgetCappingTimezoneBasis',
    'GetAdCPCapabilitiesResponseCapabilityReportingDeliveryMethod',
    'GetAdCPCapabilitiesResponseComplianceTesting',
    'GetAdCPCapabilitiesResponseCreative',
    'GetAdCPCapabilitiesResponseCreativeLocalization',
    'GetAdCPCapabilitiesResponseCreativeMultiplicity',
    'GetAdCPCapabilitiesResponseCreativeMultiplicityVariantDimensionsItem',
    'GetAdCPCapabilitiesResponseCreativePreview',
    'GetAdCPCapabilitiesResponseCreativePreviewRoutesItem',
    'GetAdCPCapabilitiesResponseCreativeRepresentationResolution',
    'GetAdCPCapabilitiesResponseCreativeSupportedFormatsItem',
    'GetAdCPCapabilitiesResponseCreativeSupportedFormatsItemOperationsItem',
    'GetAdCPCapabilitiesResponseGovernance',
    'GetAdCPCapabilitiesResponseGovernanceCreativeFeaturesItem',
    'GetAdCPCapabilitiesResponseGovernancePropertyFeaturesItem',
    'GetAdCPCapabilitiesResponseGovernanceRuntimeAttestations',
    'GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivation',
    'GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivationRequirement',
    'GetAdCPCapabilitiesResponseIdentity',
    'GetAdCPCapabilitiesResponseIdentityCompromiseNotification',
    'GetAdCPCapabilitiesResponseIdentityKeyOrigins',
    'GetAdCPCapabilitiesResponseMeasurement',
    'GetAdCPCapabilitiesResponseMeasurementGateway',
    'GetAdCPCapabilitiesResponseMeasurementMetricsItem',
    'GetAdCPCapabilitiesResponseMeasurementMetricsItemAccreditationsItem',
    'GetAdCPCapabilitiesResponseMediaBuy',
    'GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery',
    'GetAdCPCapabilitiesResponseMediaBuyAudienceEvidence',
    'GetAdCPCapabilitiesResponseMediaBuyAudienceTargeting',
    'GetAdCPCapabilitiesResponseMediaBuyAudienceTargetingMatchingLatencyHours',
    'GetAdCPCapabilitiesResponseMediaBuyBudgetCapping',
    'GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedPeriodsItem',
    'GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedScopesItem',
    'GetAdCPCapabilitiesResponseMediaBuyContentStandards',
    'GetAdCPCapabilitiesResponseMediaBuyConversionTracking',
    'GetAdCPCapabilitiesResponseMediaBuyConversionTrackingAttributionWindowsItem',
    'GetAdCPCapabilitiesResponseMediaBuyCreativeApprovalMode',
    'GetAdCPCapabilitiesResponseMediaBuyExecution',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecs',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecsVastValidation',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargeting',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingAgeRestriction',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingDemographics',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoMetros',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoProximity',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingKeywordTargets',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingNegativeKeywords',
    'GetAdCPCapabilitiesResponseMediaBuyExecutionTrustedMatch',
    'GetAdCPCapabilitiesResponseMediaBuyFeatures',
    'GetAdCPCapabilitiesResponseMediaBuyFrequencyCapping',
    'GetAdCPCapabilitiesResponseMediaBuyLifecycleToolsItem',
    'GetAdCPCapabilitiesResponseMediaBuyPerformanceFeedback',
    'GetAdCPCapabilitiesResponseMediaBuyPortfolio',
    'GetAdCPCapabilitiesResponseMediaBuyPropagationSurfacesItem',
    'GetAdCPCapabilitiesResponseMediaBuyProposalRefinement',
    'GetAdCPCapabilitiesResponseMediaBuyProposalRefinementSupportedDimensionsItem',
    'GetAdCPCapabilitiesResponseMediaBuyRelationshipNotifications',
    'GetAdCPCapabilitiesResponseMediaBuyRelationshipNotificationsEventTypesItem',
    'GetAdCPCapabilitiesResponseMediaBuyRightsAttestations',
    'GetAdCPCapabilitiesResponseMediaBuyRightsAttestationsRequirement',
    'GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimization',
    'GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimizationSupportedTargetsItem',
    'GetAdCPCapabilitiesResponseOauth',
    'GetAdCPCapabilitiesResponseRequestSigning',
    'GetAdCPCapabilitiesResponseRequestSigningCoversContentDigest',
    'GetAdCPCapabilitiesResponseSignals',
    'GetAdCPCapabilitiesResponseSignalsDiscoveryModesItem',
    'GetAdCPCapabilitiesResponseSignalsFeatures',
    'GetAdCPCapabilitiesResponseSponsoredIntelligence',
    'GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpoint',
    'GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointPreferred',
    'GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointTransportsItem',
    'GetAdCPCapabilitiesResponseSupportedProtocolsItem',
    'GetAdCPCapabilitiesResponseWebhookSigning',
    'GetAdCPCapabilitiesResponseWebhookSigningProfile',
    'GetAdCPCapabilitiesResponseWholesaleFeedVersioning',
    'GetAdCPCapabilitiesResponseWholesaleFeedWebhooks',
    'GetAdcpCapabilitiesRequest',
    'GetAdcpCapabilitiesResponse',
    'GetBrandIdentityError',
    'GetBrandIdentityRequest',
    'GetBrandIdentityRequestFieldsItem',
    'GetBrandIdentityResponse',
    'GetBrandIdentityResponse1',
    'GetBrandIdentityResponse2',
    'GetBrandIdentityResponseFontRole',
    'GetBrandIdentityResponseFontRoleFamily',
    'GetBrandIdentitySuccess',
    'GetBrandIdentitySuccessAssetsItem',
    'GetBrandIdentitySuccessColors',
    'GetBrandIdentitySuccessFonts',
    'GetBrandIdentitySuccessHouse',
    'GetBrandIdentitySuccessLogosItem',
    'GetBrandIdentitySuccessRights',
    'GetBrandIdentitySuccessTone',
    'GetBrandIdentitySuccessVoiceSynthesis',
    'GetCollectionListRequest',
    'GetCollectionListRequestPagination',
    'GetCollectionListResponse',
    'GetCollectionListResponseCollectionsItem',
    'GetContentStandardsRequest',
    'GetContentStandardsResponse',
    'GetContentStandardsResponse1',
    'GetContentStandardsResponse2',
    'GetContentStandardsResponseErrors',
    'GetCreativeDeliveryRequest',
    'GetCreativeDeliveryResponse',
    'GetCreativeDeliveryResponseCreativesItem',
    'GetCreativeDeliveryResponsePagination',
    'GetCreativeDeliveryResponseReportingPeriod',
    'GetCreativeFeaturesAsyncSubmitted',
    'GetCreativeFeaturesCompletion',
    'GetCreativeFeaturesComplianceCompletion',
    'GetCreativeFeaturesError',
    'GetCreativeFeaturesRequest',
    'GetCreativeFeaturesResponse',
    'GetCreativeFeaturesResponse1',
    'GetCreativeFeaturesResponse2',
    'GetCreativeFeaturesResponse3',
    'GetCreativeFeaturesResponseSubmitted',
    'GetCreativeFeaturesResponseSuccess',
    'GetCreativeFeaturesSubmitted',
    'GetCreativeFeaturesSuccess',
    'GetGeographicPlaceResolutionRequest',
    'GetGeographicPlaceResolutionResponse',
    'GetMediaBuyArtifactsRequest',
    'GetMediaBuyArtifactsRequestTimeRange',
    'GetMediaBuyArtifactsResponse',
    'GetMediaBuyArtifactsResponse1',
    'GetMediaBuyArtifactsResponse2',
    'GetMediaBuyArtifactsResponseArtifactsMediaBuyId',
    'GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItem',
    'GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext',
    'GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemLocalVerdict',
    'GetMediaBuyArtifactsResponseArtifactsMediaBuyIdCollectionInfo',
    'GetMediaBuyArtifactsResponseErrors',
    'GetMediaBuyDeliveryRequest',
    'GetMediaBuyDeliveryRequestReportingDimensions',
    'GetMediaBuyDeliveryRequestReportingDimensionsAudience',
    'GetMediaBuyDeliveryRequestReportingDimensionsDemographic',
    'GetMediaBuyDeliveryRequestReportingDimensionsDevicePlatform',
    'GetMediaBuyDeliveryRequestReportingDimensionsDeviceType',
    'GetMediaBuyDeliveryRequestReportingDimensionsGeo',
    'GetMediaBuyDeliveryRequestReportingDimensionsPlacement',
    'GetMediaBuyDeliveryRequestReportingDimensionsSpot',
    'GetMediaBuyDeliveryResponse',
    'GetMediaBuyDeliveryResponseAggregatedTotals',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByAudienceItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDemographicItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDevicePlatformItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByDeviceTypeItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemByFormatItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemBySpotItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemByPackageItemDailyBreakdownItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemDailyBreakdownItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemTotals',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemByPackageItem',
    'GetMediaBuyDeliveryResponseMediaBuyDeliveriesItemWindowsItemTotals',
    'GetMediaBuyDeliveryResponseReportingRevisionBinding',
    'GetMediaBuysRequest',
    'GetMediaBuysResponse',
    'GetMediaBuysResponseMediaBuysItem',
    'GetMediaBuysResponseMediaBuysItemAcceptedProposal',
    'GetMediaBuysResponseMediaBuysItemBidding',
    'GetMediaBuysResponseMediaBuysItemHistoryItem',
    'GetMediaBuysResponseMediaBuysItemIndicatorsItem',
    'GetMediaBuysResponseMediaBuysItemPackagesItem',
    'GetMediaBuysResponseMediaBuysItemPackagesItemBidding',
    'GetMediaBuysResponseMediaBuysItemPackagesItemCreativeApprovalsItem',
    'GetMediaBuysResponseMediaBuysItemPackagesItemIndicatorsItem',
    'GetMediaBuysResponseMediaBuysItemPackagesItemSnapshot',
    'GetPlanAuditLogsRequest',
    'GetPlanAuditLogsResponse',
    'GetPlanAuditLogsResponsePlansItem',
    'GetPlanAuditLogsResponsePlansItemBudget',
    'GetPlanAuditLogsResponsePlansItemBudgetAccountingMode',
    'GetPlanAuditLogsResponsePlansItemChannelAllocationValue',
    'GetPlanAuditLogsResponsePlansItemEntriesItem',
    'GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentState',
    'GetPlanAuditLogsResponsePlansItemEntriesItemAdjustmentType',
    'GetPlanAuditLogsResponsePlansItemEntriesItemAmount',
    'GetPlanAuditLogsResponsePlansItemEntriesItemDelivery',
    'GetPlanAuditLogsResponsePlansItemEntriesItemDeliveryPeriodState',
    'GetPlanAuditLogsResponsePlansItemEntriesItemDeliverySource',
    'GetPlanAuditLogsResponsePlansItemEntriesItemEvidence',
    'GetPlanAuditLogsResponsePlansItemEntriesItemEvidenceEvidenceType',
    'GetPlanAuditLogsResponsePlansItemEntriesItemRuntimeAttestationsItem',
    'GetPlanAuditLogsResponsePlansItemEntriesItemType',
    'GetPlanAuditLogsResponsePlansItemGovernedActionsItem',
    'GetPlanAuditLogsResponsePlansItemGovernedActionsItemDeliveryPeriodState',
    'GetPlanAuditLogsResponsePlansItemGovernedActionsItemStatus',
    'GetPlanAuditLogsResponsePlansItemStatus',
    'GetPlanAuditLogsResponsePlansItemSummary',
    'GetPlanAuditLogsResponsePlansItemSummaryDriftMetrics',
    'GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsEscalationRateTrend',
    'GetPlanAuditLogsResponsePlansItemSummaryDriftMetricsThresholds',
    'GetPlanAuditLogsResponsePlansItemSummaryEscalationsItem',
    'GetPlanAuditLogsResponsePlansItemSummaryStatuses',
    'GetPrincipalRequest',
    'GetPrincipalResponse',
    'GetProductsAsyncInputRequired',
    'GetProductsAsyncSubmitted',
    'GetProductsAsyncWorking',
    'GetProductsCompletion',
    'GetProductsInputRequired',
    'GetProductsInputRequiredReason',
    'GetProductsRejected',
    'GetProductsRequest',
    'GetProductsRequestBuyingMode',
    'GetProductsRequestFieldsItem',
    'GetProductsRequestRefineItemProductAction',
    'GetProductsRequestRefineItemProposalAction',
    'GetProductsRequestTimeBudget',
    'GetProductsResponse',
    'GetProductsResponseCacheScope',
    'GetProductsResponseFilterDiagnostics',
    'GetProductsResponseFilterDiagnosticsExcludedByValue',
    'GetProductsResponseFilterDiagnosticsSemantics',
    'GetProductsResponseIncompleteItem',
    'GetProductsResponseIncompleteItemEstimatedWait',
    'GetProductsResponseIncompleteItemScope',
    'GetProductsSubmitted',
    'GetProductsWorking',
    'GetPropertyListRequest',
    'GetPropertyListResponse',
    'GetReportingStatusRequest',
    'GetReportingStatusRequestReportingStatusView',
    'GetReportingStatusResponse',
    'GetReportingStatusResponseObligationCounts',
    'GetReportingStatusResponseScope',
    'GetReportingStatusResponseScopeDeliveryConfigGenerationsItem',
    'GetRightsError',
    'GetRightsRequest',
    'GetRightsResponse',
    'GetRightsResponse1',
    'GetRightsResponse2',
    'GetRightsSuccess',
    'GetRightsSuccessExcludedItem',
    'GetRightsSuccessRightsItem',
    'GetRightsSuccessRightsItemExclusivityStatus',
    'GetRightsSuccessRightsItemPreviewAssetsItem',
    'GetSignalsAsyncSubmitted',
    'GetSignalsAsyncWorking',
    'GetSignalsCompletion',
    'GetSignalsRequest',
    'GetSignalsRequestFieldsItem',
    'GetSignalsResponse',
    'GetSignalsResponseIncompleteItem',
    'GetSignalsResponseIncompleteItemEstimatedWait',
    'GetSignalsResponseIncompleteItemScope',
    'GetSignalsResponseSignalsItem',
    'GetSignalsSubmitted',
    'GetSignalsWorking',
    'GetTaskStatusRequest',
    'GetTaskStatusResponse',
    'Goal',
    'Goal1',
    'GoalEvent',
    'GoalMetric',
    'GopType',
    'GovernanceAgentNotAcceptedDetails',
    'GovernanceAgentNotAcceptedDetails1',
    'GovernanceAgentNotAcceptedDetails2',
    'GovernanceAgentNotAcceptedDetailsDisclosed',
    'GovernanceAgentNotAcceptedDetailsOpaque',
    'GovernanceDecision',
    'GovernanceDomain',
    'GovernanceMode',
    'GovernancePhase',
    'GovernedAction',
    'GovernedActionsItemDeliveryReconciliationStatus',
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
    'HTTPMethod',
    'HexColor',
    'HistoryEntryType',
    'HistoryItem',
    'HostedAudioFormatDeclaration',
    'HostedVideoFormatDeclaration',
    'HotelItem',
    'HotelItemAddress',
    'HoursValue',
    'House',
    'HousePortfolio',
    'HouseRedirect',
    'HouseRedirectRedirectReason',
    'HtmlAsset',
    'HtmlAssetRequirements',
    'HttpMethod',
    'HttpsUrl',
    'IANATimezoneIdentifier',
    'IanaTimezoneIdentifier',
    'IdType',
    'Idempotency',
    'IdempotencyKey',
    'IdempotencySupported',
    'IdempotencyUnsupported',
    'Identifier',
    'IdentifierMatchProof',
    'Identity',
    'IdentityMatchRequest',
    'IdentityMatchRequestConsent',
    'IdentityMatchRequestIdentitiesItem',
    'IdentityMatchRequestIdentitiesItemAttestation',
    'IdentityMatchRequestIdentitiesItemAttestationVerificationLevel',
    'IdentityMatchRequestSealedCredentialsItem',
    'IdentityMatchResponse',
    'IdentityMatchResponseProviderRouter',
    'IdentityMatchResponseRouterPublisher',
    'IdentityMatchResponseRouterPublisherTmpxProvidersValue',
    'IdentityUpdates',
    'Ids',
    'ImageAsset',
    'ImageAssetRequirements',
    'ImageAssetRequirementsColorSpace',
    'ImageAssetRequirementsFormatsItem',
    'ImageCarouselFormatDeclaration',
    'ImageFormatDeclaration',
    'Impairment',
    'ImpairmentOfflineState',
    'ImpairmentReasonCode',
    'ImpairmentResourceType',
    'ImpairmentTransition',
    'Indicator',
    'IndicatorBearingResourceState',
    'IndicatorScope',
    'IndicatorType',
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
    'InspectedDocumentVersionMismatch',
    'Installment',
    'InstallmentDeadlines',
    'InstallmentDeliveryMetrics',
    'InstallmentDerivativeOf',
    'InstallmentPropertyDeliveryMetrics',
    'InstallmentReference',
    'InstallmentStatus',
    'IntegerReportingControlTotal',
    'InventoryListApplication',
    'InventoryListApplication1',
    'InventoryListApplication2',
    'Issue',
    'ItemIssue',
    'JavaScriptAsset',
    'JavaScriptAssetRequirements',
    'JavaScriptAssetRequirementsModuleType',
    'JavaScriptModuleType',
    'JavascriptAsset',
    'JavascriptAssetRequirements',
    'JavascriptModuleType',
    'JobItem',
    'JobItemEmploymentType',
    'JobItemExperienceLevel',
    'JobItemSalary',
    'JobItemSalaryPeriod',
    'Keyword',
    'KeywordDeliveryMetrics',
    'KeywordRequirement',
    'KeywordRequirement1',
    'KeywordRequirementSupportedMatchTypes',
    'KeywordSupport',
    'KeywordSupport1',
    'KeywordSupportSupportedMatchTypes',
    'KeywordTarget',
    'LandingPageRequirement',
    'Language',
    'LanguageTag',
    'LifecycleTool',
    'LiftDimension',
    'Limitation',
    'LimitedSeries',
    'ListAccountChangesRequest',
    'ListAccountChangesRequestStartingPosition',
    'ListAccountChangesResponse',
    'ListAccountChangesResponseCompleted',
    'ListAccountChangesResponseFailed',
    'ListAccountChangesResponseSourceCoverageItem',
    'ListAccountChangesResponseSourceCoverageItemKind',
    'ListAccountChangesResponseSourceCoverageItemStatus',
    'ListAccountsRequest',
    'ListAccountsResponse',
    'ListCollectionListsRequest',
    'ListCollectionListsResponse',
    'ListContentStandardsRequest',
    'ListContentStandardsResponse',
    'ListContentStandardsResponse1',
    'ListContentStandardsResponse2',
    'ListContentStandardsResponseErrors',
    'ListContentStandardsResponseStandards',
    'ListCreativeFormatsRequest',
    'ListCreativeFormatsRequestCreativeAgent',
    'ListCreativeFormatsRequestCreativeAgentType',
    'ListCreativeFormatsResponse',
    'ListCreativeFormatsResponseCreativeAgent',
    'ListCreativeFormatsResponseCreativeAgentCreativeAgentsItem',
    'ListCreativeFormatsResponseSource',
    'ListCreativesRequest',
    'ListCreativesRequestAssignmentProjection',
    'ListCreativesRequestFieldsItem',
    'ListCreativesRequestSort',
    'ListCreativesResponse',
    'ListCreativesResponseCreativesItem',
    'ListCreativesResponseCreativesItemAssignments',
    'ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItem',
    'ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorTypesEvaluatedItem',
    'ListCreativesResponseCreativesItemAssignmentsAssignedPackagesItemIndicatorsItem',
    'ListCreativesResponseCreativesItemLocalizationUnavailable',
    'ListCreativesResponseCreativesItemPurge',
    'ListCreativesResponseCreativesItemPurgeKind',
    'ListCreativesResponseCreativesItemSnapshot',
    'ListCreativesResponseQuerySummary',
    'ListCreativesResponseQuerySummarySortApplied',
    'ListCreativesResponseStatusSummary',
    'ListProductsRequest',
    'ListProductsRequestPushNotificationConfig',
    'ListProductsResponse',
    'ListProductsResponseIncompleteItem',
    'ListProductsResponseIncompleteItemScope',
    'ListProductsResponseListed',
    'ListProductsResponseOutcome',
    'ListProductsResponseUnchanged',
    'ListPropertyListsRequest',
    'ListPropertyListsResponse',
    'ListScenariosSuccess',
    'ListTasksRequest',
    'ListTasksResponse',
    'ListTransformersRequestCreativeAgent',
    'ListTransformersRequestCreativeAgentExpandPaginationItem',
    'ListTransformersResponseCreativeAgent',
    'ListedCreativeCanonicalFormatKind',
    'ListedCreativeNamedFormatReference',
    'LocaleFallback',
    'LocalizedCreativeAsset',
    'LocalizedName',
    'LocalizedScalar',
    'LocalizedStringList',
    'LocalizedStringListEntry',
    'Location',
    'Location13',
    'Locator',
    'Locator1',
    'LogEventError',
    'LogEventRequest',
    'LogEventResponse',
    'LogEventResponse1',
    'LogEventResponse2',
    'LogEventSuccess',
    'LogEventSuccessPartialFailuresItem',
    'Logo',
    'LogoId',
    'LogoSlot',
    'LookbackWindow',
    'Loss',
    'MCPWebhookPayload',
    'MacroBearingURL',
    'MacroBearingUrl',
    'MacroDeclaration',
    'MacroDeclarationLocation',
    'MacroDeclarationLocationField',
    'MacroDeclarationUnavailableBehavior',
    'MacroDialectFamily',
    'MacroEncoding',
    'MacroEncodingKind',
    'MacroMappingStatus',
    'MacroProcessingActor',
    'MacroProcessingCapability',
    'MacroProcessingCapabilityMappingStatus',
    'MacroProcessingCapabilityOperation',
    'MacroProcessingOperation',
    'MacroResolutionFailedDetails',
    'MacroResolutionReason',
    'MacroResolutionResult',
    'MacroResolutionResultStatus',
    'MacroTranslationTarget',
    'MacroValueContext',
    'MakegoodRemedy',
    'MarkdownAsset',
    'MarkdownAssetRequirements',
    'MarkdownFlavor',
    'MatchBreakdown',
    'MatchIDType',
    'MatchIdType',
    'MatchKey',
    'MatchType',
    'MatchingProduct',
    'MaterialDeadline',
    'MaterialStage',
    'McpWebhookPayload',
    'MeasurementReadiness',
    'MeasurementTerms',
    'MeasurementTermsBillingMeasurement',
    'MeasurementTermsMakegoodPolicy',
    'MeasurementWindow',
    'MediaBuy',
    'MediaBuyActionMode',
    'MediaBuyAvailableAction',
    'MediaBuyAvailableActionID',
    'MediaBuyAvailableActionId',
    'MediaBuyAvailableActionTask',
    'MediaBuyBidding',
    'MediaBuyCancellation',
    'MediaBuyChangeTerm',
    'MediaBuyChangeTermAllowedStatusesItem',
    'MediaBuyChangeTermConstraints',
    'MediaBuyChangeTermConstraints1',
    'MediaBuyChangeTermConstraints2',
    'MediaBuyChangeTermConstraints3',
    'MediaBuyChangeTermConstraints4',
    'MediaBuyChangeTermConstraintsMoney',
    'MediaBuyChangeTermID',
    'MediaBuyChangeTermId',
    'MediaBuyCommitmentResponse',
    'MediaBuyCommitmentResponse1',
    'MediaBuyCommitmentResponse2',
    'MediaBuyCommitmentResponse3',
    'MediaBuyCommitmentResponseCompleted',
    'MediaBuyCommitmentResponseFailed',
    'MediaBuyCommitmentResponseSubmitted',
    'MediaBuyDeliveryWebhookResult',
    'MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItem',
    'MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemByPackageItem',
    'MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus',
    'MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemTotals',
    'MediaBuyDeliveryWebhookResultNotificationType',
    'MediaBuyDeliveryWebhookResultReportingPeriod',
    'MediaBuyFeatures',
    'MediaBuyFeaturesBiddingPolicy',
    'MediaBuyFrequencyCap',
    'MediaBuyFrequencyCapCapability',
    'MediaBuyFrequencyCapControlMode',
    'MediaBuyFrequencyCapRequirement',
    'MediaBuyFrequencyCapSupport',
    'MediaBuyHealth',
    'MediaBuyStatus',
    'MediaBuyTermsReference',
    'MediaBuyValidAction',
    'MediaBuysItemIndicatorsItemType',
    'MediaChannel',
    'MetricScope',
    'MetricType',
    'MetroAreaSystem',
    'MetroRequirement',
    'MetroRequirement1',
    'MetroRequirementSystems',
    'MetroSupport',
    'MetroSupport1',
    'MetroSupportSystems',
    'MinSpendTarget',
    'MissingMetric',
    'MissingMetric1',
    'MissingMetric2',
    'MissingMetricVendor',
    'MixTargets',
    'MoovAtomPosition',
    'NamedFormatManifest',
    'NativeInFeedFormatDeclaration',
    'NegativeKeyword',
    'NonblockingImpacts',
    'NotYetMeasurableVendorMetricsByPackageValueItem',
    'NotificationConfig',
    'NotificationConfigAuthentication',
    'NotificationConfigEventTypesItem',
    'NotificationConfigProductPayloadView',
    'NotificationType',
    'Notifications',
    'Notifications2',
    'ObjAllValues',
    'ObjErrorsContextExt',
    'ObjScopeAsk',
    'ObjScopeMetricIdQualifier',
    'ObjScopeProductIdActionAsk',
    'ObjScopeProposalIdActionAsk',
    'ObjTypeValueLanguage',
    'ObjValues',
    'Offer',
    'OfferPrice',
    'OfferPriceModel',
    'Offering',
    'OfferingAssetConstraint',
    'OfferingAssetGroup',
    'OfferingAvailabilityStatus',
    'OfferingGeoTargets',
    'OfferingGeoTargetsMetrosItem',
    'Operation',
    'OperationalFailure',
    'OperatorIdentity',
    'OperatorUnit',
    'OpportunityContext',
    'OpportunityContextCloseReason',
    'OpportunityContextIntent',
    'OpportunityContextPhase',
    'OpportunityContextStatus',
    'OptimizationGoal',
    'OptimizationGoal8',
    'OptimizationGoal9',
    'OptimizationGoal10',
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
    'OptimizationGoals',
    'Option',
    'OutcomeMeasurement',
    'OutcomeMeasurementWindow',
    'OutcomeTarget',
    'OutcomeTargetCostPer',
    'OutcomeTargetCostStrength',
    'OutcomeType',
    'Overlay',
    'OverlayBounds',
    'OverlayBoundsUnit',
    'OverlayVisual',
    'Pacing',
    'Package',
    'PackageBidding',
    'PackageCancellation',
    'PackageControl',
    'PackageCountConstraints',
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
    'PackageRequest',
    'PackageRequestBidding',
    'PackageSignalTargeting',
    'PackageSignalTargetingBinary',
    'PackageSignalTargetingCategorical',
    'PackageSignalTargetingGroup',
    'PackageSignalTargetingGroupOperator',
    'PackageSignalTargetingGroups',
    'PackageSignalTargetingGroupsOperator',
    'PackageSignalTargetingNumeric',
    'PackageTargetingResolution',
    'PackageUpdate',
    'PackagesItemIndicatorsItemType',
    'Pagination',
    'PaginationRequest',
    'PaginationResponse',
    'PairedRedirect',
    'PairedRedirectMacroDeclarationsItem',
    'PairedRedirectMacroDeclarationsItemLocation',
    'PairedRedirectMacroDeclarationsItemLocationField',
    'Panel',
    'ParameterMapping',
    'PartialFailure',
    'PassItemUrl',
    'Payload',
    'Payload1',
    'Payload2',
    'Payload5',
    'Payload6',
    'Payload8',
    'Payload9',
    'Payload17',
    'Payload18',
    'Payload20',
    'Payload21',
    'Payload22',
    'Payload23',
    'Payload24',
    'PaymentTerms',
    'PerLeaf',
    'PerUnitPricing',
    'PercentOfMediaPricing',
    'PerformanceBaseline',
    'PerformanceFeedback',
    'PerformanceFeedbackAssertion',
    'PerformanceFeedbackAssertionEvidence',
    'PerformanceFeedbackAssertionEvidenceConfidenceInterval',
    'PerformanceFeedbackMetric',
    'PerformanceFeedbackMetric1',
    'PerformanceFeedbackMetric2',
    'PerformanceFeedbackMetricStandard',
    'PerformanceFeedbackMetricVendor',
    'PerformanceFeedbackStatus',
    'PerformanceStandard',
    'PerformanceStandardMetric',
    'PerformanceStandards',
    'Period',
    'PeriodsView',
    'PhysicalChecksums',
    'PhysicalChecksums1',
    'PixelTrackerAsset',
    'PixelTrackerAssetMethod',
    'PixelTrackingEvent',
    'Placement',
    'PlacementDefinition',
    'PlacementDefinitionIdentifiersItem',
    'PlacementDefinitionPublisherDoohPlacementAttributes',
    'PlacementDefinitionPublisherDoohScreenResolution',
    'PlacementDeliveryMetrics',
    'PlacementEvidence',
    'PlacementForecastDimension',
    'PlacementIdentity',
    'PlacementIdentity1',
    'PlacementIdentity2',
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
    'PlacementSelection1',
    'PlacementSelection2',
    'PlannedDelivery',
    'PlannedDeliveryBidding',
    'PlannedDeliveryGeo',
    'PlatformDistribution',
    'PlatformExtensionReference',
    'PlatformSegment',
    'Point',
    'PolicyCategory',
    'PolicyCategoryDefinition',
    'PolicyCategoryDefinitionFacetsItem',
    'PolicyCategoryDefinitionRegulatoryFrameworksItem',
    'PolicyEnforcementLevel',
    'PolicyEntry',
    'PolicyEntryExemplar',
    'PolicyEntryExemplars',
    'PolicyEntryIssuer',
    'PolicyEntrySource',
    'PolicyRef',
    'PolicyReference',
    'PolicyViolationDetails',
    'PolicyViolationDetailsOrigin',
    'PositivePostalAreaSupport',
    'PostalArea',
    'PostalArea2',
    'PostalArea112',
    'PostalArea113',
    'PostalArea114',
    'PostalArea115',
    'PostalArea116',
    'PostalArea117',
    'PostalArea118',
    'PostalArea119',
    'PostalArea120',
    'PostalAreaAUPostcode',
    'PostalAreaBRCep',
    'PostalAreaBranch9System',
    'PostalAreaCA',
    'PostalAreaCountrySystemValues',
    'PostalAreaFRCodePostal',
    'PostalAreaGB',
    'PostalAreaINPin',
    'PostalAreaPlz',
    'PostalAreaSupport',
    'PostalAreaSupportAdditionalPropertyEnum',
    'PostalAreaSupportValueItem',
    'PostalAreaUS',
    'PostalAreaWithFusedSystem',
    'PostalAreaZAPostalCode',
    'PostalCodeSystem',
    'PostalCountrySystem',
    'PostalCountrySystem1',
    'PostalCountrySystem2',
    'PostalCountrySystem3',
    'PostalCountrySystemAUPostcode',
    'PostalCountrySystemBRCep',
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
    'Posting',
    'Preview2',
    'Preview3',
    'Preview4',
    'PreviewAsset',
    'PreviewBatchResultError',
    'PreviewBatchResultSuccess',
    'PreviewCreativeBatchResponse',
    'PreviewCreativeBatchResponseResultsItem',
    'PreviewCreativeBatchResponseResultsItemResponse',
    'PreviewCreativeBatchResponseResultsItemResponsePreviewsItem',
    'PreviewCreativeBatchResponseResultsItemResponsePreviewsItemInput',
    'PreviewCreativeRequest',
    'PreviewCreativeRequestRequestType',
    'PreviewCreativeRequestRequestsItem',
    'PreviewCreativeResponse',
    'PreviewCreativeResponse1',
    'PreviewCreativeResponse2',
    'PreviewCreativeResponse3',
    'PreviewCreativeResponse4',
    'PreviewCreativeSingleResponse',
    'PreviewCreativeSingleResponsePreviewsItem',
    'PreviewCreativeSingleResponsePreviewsItemInput',
    'PreviewCreativeSubmitted',
    'PreviewCreativeVariantResponse',
    'PreviewCreativeVariantResponsePreviewsItem',
    'PreviewOutputFormat',
    'PreviewRender',
    'PreviewRender1',
    'PreviewRender2',
    'PreviewRender3',
    'PreviewRenderBoth',
    'PreviewRenderBothEmbedding',
    'PreviewRenderHtml',
    'PreviewRenderHtmlEmbedding',
    'PreviewRenderUrl',
    'PreviewRenderUrlDimensions',
    'PreviewRendererMetadata',
    'PreviewRendererMetadataRenderingOrigin',
    'Price',
    'PriceAdjustmentKind',
    'PriceBreakdown',
    'PriceBreakdownAdjustmentsItem',
    'PriceGuidance',
    'PricePeriod',
    'PricingModel',
    'PricingOption',
    'PricingOptionCpa',
    'PricingOptionCpc',
    'PricingOptionCpcv',
    'PricingOptionCpm',
    'PricingOptionCpp',
    'PricingOptionCpv',
    'PricingOptionFlatRate',
    'PricingOptionId',
    'PricingOptionRevenueShare',
    'PricingOptionTime',
    'PricingOptionVcpm',
    'PricingStructure',
    'PrincipalAppliedResult',
    'PrincipalChangedWebhook',
    'PrincipalChangedWebhookReason',
    'PrincipalCurrentResult',
    'PrincipalDeclarationsState',
    'PrincipalDeclarationsStateExclusionsItem',
    'PrincipalDeclarationsStateExclusionsItemAxis',
    'PrincipalKind',
    'PrincipalReadFailedResult',
    'PrincipalRecognizedResult',
    'PrincipalState',
    'PrincipalStateRetiredDestinationsItem',
    'PrincipalSyncFailedResult',
    'PrincipalUnconfiguredResult',
    'PrincipalValidatedResult',
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
    'ProductChangeMap1',
    'ProductChangeMapValue',
    'ProductConversionTracking',
    'ProductConversionTrackingSupportedTargetsItem',
    'ProductDefaultCollections',
    'ProductDefaultPlacements',
    'ProductDeliveryMeasurement',
    'ProductDiscoveryCriteria',
    'ProductDiscoveryCriteriaOutcomeTarget',
    'ProductDiscoveryTargetingResolution',
    'ProductExecutionRequirement',
    'ProductExecutionRequirement1',
    'ProductExecutionRequirement2',
    'ProductExecutionRequirement3',
    'ProductFilters',
    'ProductFiltersGeoProximityItem',
    'ProductFiltersGeoProximityItemGeometry',
    'ProductFiltersGeoProximityItemLatLngRadius',
    'ProductFiltersGeoProximityItemLatLngTransportModeTravelTime',
    'ProductFiltersKeywordsItem',
    'ProductFiltersMetrosItem',
    'ProductFiltersRequiredGeoTargetingItem',
    'ProductFiltersRequiredVendorMetricsItem',
    'ProductFiltersSignalTargetingItem',
    'ProductFiltersSignalTargetingItemTargetingMode',
    'ProductFiltersTrustedMatch',
    'ProductFiltersTrustedMatchProvidersItem',
    'ProductFormatDeclaration',
    'ProductFormatDeclaration1',
    'ProductFormatDeclaration2',
    'ProductFormatDeclaration3',
    'ProductFormatDeclaration4',
    'ProductFormatDeclaration5',
    'ProductFormatDeclaration6',
    'ProductFormatDeclaration7',
    'ProductFormatDeclaration8',
    'ProductFormatDeclaration9',
    'ProductFormatDeclaration10',
    'ProductFormatDeclaration11',
    'ProductFormatDeclaration12',
    'ProductFormatDeclaration13',
    'ProductFormatDeclaration14',
    'ProductFormatDeclaration15',
    'ProductFormatDeclaration16',
    'ProductFormatDeclarationSellerPreference',
    'ProductId',
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
    'ProductPurchase',
    'ProductPurchaseInput',
    'ProductRefinementRequests',
    'ProductResponseField',
    'ProductResponseFields',
    'ProductResponseFieldsItem',
    'ProductSignalTargetingOption',
    'ProductSignalTargetingOptionActivationStatus',
    'ProductSignalTargetingOptionAllowedTargetingModesItem',
    'ProductTarget',
    'ProductTargetingResolution',
    'ProductTrustedMatch',
    'ProductTrustedMatchProvidersItem',
    'ProductionQuality',
    'PropagationSurface',
    'Property',
    'PropertyDeliveryMetrics',
    'PropertyError',
    'PropertyErrorCode',
    'PropertyFeature',
    'PropertyFeatureDefinition',
    'PropertyFeatureDefinitionCoverage',
    'PropertyFeatureDefinitionType',
    'PropertyFeatureResult',
    'PropertyFeatureResultCoverageStatus',
    'PropertyFeatureValue',
    'PropertyID',
    'PropertyId',
    'PropertyIdentifierTypes',
    'PropertyList',
    'PropertyListApplication',
    'PropertyListApplicationEffect',
    'PropertyListApplicationSummary',
    'PropertyListChangedWebhook',
    'PropertyListChangedWebhookChangeSummary',
    'PropertyListFilters',
    'PropertyListReference',
    'PropertyReference',
    'PropertyTag',
    'PropertyType',
    'Proposal',
    'ProposalBudgetConstraint',
    'ProposalDecline',
    'ProposalDeclineReason',
    'ProposalRefinement',
    'ProposalRefinementAction',
    'ProposalRefinementAlternatives',
    'ProposalRefinementChangeKind',
    'ProposalRefinementConstraints',
    'ProposalRefinementConstraintsCpm',
    'ProposalRefinementConstraintsFlight',
    'ProposalRefinementConstraintsImpressions',
    'ProposalRefinementFinalize',
    'ProposalRefinementReason',
    'ProposalRefinementRevise',
    'ProposalRefinementReviseAlternatives',
    'ProposalRefinementReviseAsk',
    'ProposalRefinementReviseCancellation',
    'ProposalRefinementReviseConstraints',
    'ProposalRefinementReviseCriteria',
    'ProposalRefinementReviseProductChanges',
    'ProposalRefinementReviseRemoveMediaBuyFrequencyCap',
    'ProposalStatus',
    'ProposalTotalBudgetGuidance',
    'ProtocolEnvelope',
    'ProtocolResponse',
    'Provenance',
    'ProvenanceAiTool',
    'ProvenanceAuditObservationsSuccess',
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
    'ProvidePerformanceFeedbackError',
    'ProvidePerformanceFeedbackRequest',
    'ProvidePerformanceFeedbackResponse',
    'ProvidePerformanceFeedbackResponse1',
    'ProvidePerformanceFeedbackResponse2',
    'ProvidePerformanceFeedbackSuccess',
    'ProvidePerformanceFeedbackSuccessApplicationStatus',
    'ProvisionBinding',
    'ProvisionRecipient',
    'ProvisionRecipientProvider',
    'ProvisionRecipientRecipient',
    'ProvisioningMode',
    'PublishedPostAsset',
    'PublishedPostAssetIdentityRef',
    'PublishedPostAssetReferenceAuthorization',
    'PublishedPostAssetReferenceAuthorizationStatus',
    'PublisherCatalogFormatOptionReference',
    'PublisherCatalogPlacementIdentity',
    'PublisherCollectionsSource',
    'PublisherDesignatedPreviewProvider',
    'PublisherDesignatedPreviewProviderRoutesItem',
    'PublisherGenresSource',
    'PublisherIdentifierTypes',
    'PublisherPropertyIDsSource',
    'PublisherPropertySelector',
    'PublisherPropertySelector1',
    'PublisherPropertySelector2',
    'PublisherPropertySelector3',
    'PublisherPropertySelectorAll',
    'PublisherPropertySelectorById',
    'PublisherPropertySelectorByTag',
    'PublisherTMPXMacroMapping',
    'PublisherTagsSource',
    'PublisherTargetingKVMapping',
    'PublisherTargetingKvMapping',
    'PublisherTmpxMacroMapping',
    'PurchaseBinding',
    'PurchaseContinuationLegacyCreate',
    'PurchaseContinuationListedPurchaseAccount',
    'PurchaseType',
    'PushNotificationConfig',
    'PushNotificationConfigAuthentication',
    'Query',
    'RateLimitedDetails',
    'RateLimitedDetailsScope',
    'RawAttestation',
    'ReachAggregation',
    'ReachUnit',
    'ReachWindow',
    'RealEstateItem',
    'RealEstateItemArea',
    'RealEstateItemAreaUnit',
    'RealEstateItemListingType',
    'RealEstateItemPropertyType',
    'RecognizedPrincipalWithoutStandingConfiguration',
    'Record',
    'RecordedReportingAdjustmentReceipt',
    'RecordedReportingConsumerStatus',
    'RecordedReportingReceipt',
    'ReferenceAsset',
    'ReferenceAssetRole',
    'ReferenceRenderer',
    'ReferenceRendererProvenance',
    'Refine1',
    'Refine2',
    'Refine3',
    'RefineProposalsAsyncSubmitted',
    'RefineProposalsInputRequired',
    'RefineProposalsRequest',
    'RefineProposalsResponse',
    'RefineProposalsResponseCompleted',
    'RefineProposalsResponseResultsItem',
    'RefineProposalsResponseResultsItemFinalizedProposal',
    'RefineProposalsResponseResultsItemOutcome',
    'RefineProposalsResponseResultsItemUnable',
    'RefineProposalsResponseStatus',
    'RefineProposalsResponseSubmitted',
    'RefineProposalsSubmitted',
    'RefineProposalsWorking',
    'RefinementApplied1',
    'RefinementApplied2',
    'RefinementApplied3',
    'RefinementAppliedItemProduct',
    'RefinementAppliedItemProposal',
    'RefinementAppliedItemRequest',
    'RefinementAppliedItemRequestStatus',
    'RegistryAcceptancePolicyProfileReference',
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
    'RegulatoryBasi',
    'RegulatoryFramework',
    'RelatedCollection',
    'RemoveTargetingSetValues',
    'RemoveTargetingSetValuesPath',
    'RemoveTargetingSetValuesSelector',
    'Renders',
    'Renders1',
    'RendersItemDimensions',
    'RendersItemParametersFromFormatId',
    'RepeatableGroupAsset',
    'RepeatableGroupAssetSelectionMode',
    'ReplaceAssignment',
    'ReplaceTargetingValue',
    'ReportPlanAdjustmentRequest',
    'ReportPlanAdjustmentRequestAction',
    'ReportPlanAdjustmentRequestDecision',
    'ReportPlanAdjustmentRequestEvidence',
    'ReportPlanAdjustmentResponse',
    'ReportPlanAdjustmentResponsePlanSummary',
    'ReportPlanOutcomeRequest',
    'ReportPlanOutcomeRequestDelivery',
    'ReportPlanOutcomeRequestSellerResponse',
    'ReportPlanOutcomeRequestSellerResponsePackagesItem',
    'ReportPlanOutcomeResponse',
    'ReportPlanOutcomeResponseDeliveryPeriodState',
    'ReportPlanOutcomeResponseFindingsItem',
    'ReportPlanOutcomeResponseOutcomeState',
    'ReportPlanOutcomeResponsePlanSummary',
    'ReportUsageRequest',
    'ReportUsageRequestUsageItem',
    'ReportUsageResponse',
    'ReportedOutcomeError',
    'ReportedOutcomeErrorClassificationSource',
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
    'ReportingCommitment',
    'ReportingConsumerStatus',
    'ReportingConsumerStatusConsumerStatus',
    'ReportingConsumerStatusFailureCode',
    'ReportingConsumerStatusMismatchCode',
    'ReportingConsumerStatusPeriod',
    'ReportingControlTotal',
    'ReportingControlTotal1',
    'ReportingControlTotal2',
    'ReportingCoverage',
    'ReportingCoverageLimitationsItem',
    'ReportingCoverageLimitationsItemReason',
    'ReportingCoverageStatus',
    'ReportingDatasetShareDestination',
    'ReportingDatasetShareDestination1',
    'ReportingDatasetShareDestination2',
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
    'ReportingDeliveryMethod1',
    'ReportingDeliveryMethod2',
    'ReportingDeliveryMethod3',
    'ReportingDeliveryMethodFileTransfer',
    'ReportingDeliveryMethodReportingOrchestration',
    'ReportingDeliveryOffering',
    'ReportingDeliveryOfferingID',
    'ReportingDeliveryOfferingId',
    'ReportingDeliveryOfferingMethod',
    'ReportingDeliveryOfferingMethodDestinationModesItem',
    'ReportingDeliveryOfferingMethodProducerIdentity',
    'ReportingDeliveryOfferingReportingDeliveryPattern',
    'ReportingDeliveryOfferingReportingFeedPurpose',
    'ReportingDeliveryOfferingReportingProfile',
    'ReportingDeliveryReadyWebhook',
    'ReportingDeliveryReadyWebhookReadiness',
    'ReportingDestinationOffering',
    'ReportingDestinationSetupState',
    'ReportingFileCompression',
    'ReportingFileEntry',
    'ReportingFileManifest',
    'ReportingFileObjectReference',
    'ReportingFinality',
    'ReportingFrequency',
    'ReportingHealth',
    'ReportingLedgerChangedWebhook',
    'ReportingLedgerChangedWebhookChangeKind',
    'ReportingMaterialization',
    'ReportingMaterializationStatus',
    'ReportingMediaBuyId',
    'ReportingMode',
    'ReportingNativeVersionReference',
    'ReportingObligation',
    'ReportingObligationProductionStatus',
    'ReportingObligationReconciliationStatus',
    'ReportingPackageId',
    'ReportingPeriod',
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
    'ReportingWriteDestination1',
    'ReportingWriteDestination2',
    'ReportingWriteDestinationExisting',
    'RepresentationDestination',
    'RepresentationRejection',
    'RepresentationRejectionCode',
    'RepresentationSelection',
    'RepresentationSelectionStrategy',
    'Request',
    'RequestProposalsAsyncSubmitted',
    'RequestProposalsInputRequired',
    'RequestProposalsRequest',
    'RequestProposalsRequestAccount',
    'RequestProposalsRequestAccountAccount',
    'RequestProposalsRequestAccountAccountAccountId',
    'RequestProposalsRequestAccountAccountBrandOperator',
    'RequestProposalsRequestBrand',
    'RequestProposalsRequestOpportunity',
    'RequestProposalsResponse',
    'RequestProposalsResponseIncompleteItem',
    'RequestProposalsResponseOutcome',
    'RequestProposalsResponseProductsAvailableCompleted',
    'RequestProposalsResponseProposalsItem',
    'RequestProposalsResponseProposedCompleted',
    'RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem',
    'RequestProposalsResponsePurchaseContinuationLegacyCreateSourceAdcpVersion',
    'RequestProposalsResponseRejectedCompleted',
    'RequestProposalsResponseSubmitted',
    'RequestProposalsSubmitted',
    'RequestProposalsWorking',
    'RequestSigningErrorCode',
    'RequiredDisclosure',
    'RequiredPerformanceStandard',
    'RequoteRequiredDetails',
    'ResolvedAssets',
    'ResolvedPolicy',
    'Resolver',
    'ResponsePayloadJWSEnvelope',
    'ResponsePayloadJWSEnvelopeResponsePayload',
    'ResponsePayloadJWSEnvelopeResponsePayloadTask',
    'ResponsePayloadJwsEnvelope',
    'ResponsiveCreativeFormatDeclaration',
    'RestrictedAttribute',
    'Result2',
    'Result3',
    'Result5',
    'Result13',
    'Result15',
    'ResultEntry',
    'ResultEntry1',
    'ResultEntry2',
    'Results20',
    'Results21',
    'Results22',
    'Results23',
    'Results26',
    'Results27',
    'ResultsItemDeclined',
    'ResultsItemFinalized',
    'ResultsItemPartial',
    'ResultsItemPartialProposalsItem',
    'ResultsItemRevised',
    'RetiredDestination',
    'RevenueSharePricingOption',
    'RevisionView',
    'RevisionViewPagination',
    'RevocationNotification',
    'RevokedPublisherDomain',
    'RevokedPublisherDomain1',
    'RevokedPublisherDomain2',
    'RevokedPublisherDomain3',
    'RevokedPublisherDomain4',
    'RevokedPublisherDomain5',
    'RevokedPublisherDomain6',
    'RightType',
    'RightUse',
    'RightsAttestationEvaluation',
    'RightsAttestationEvaluationEvaluation',
    'RightsAttestationEvaluationEvaluationActionBinding',
    'RightsAttestationEvaluationReference',
    'RightsBillingPeriod',
    'RightsConstraint',
    'RightsConstraintApprovalStatus',
    'RightsConstraintAttestationRefsItem',
    'RightsConstraintAttestationRefsItemSubject',
    'RightsConstraintDisclosure',
    'RightsConstraintGrantStatus',
    'RightsConstraintRightsAgent',
    'RightsPricingOption',
    'RightsTerms',
    'RightsTermsExclusivity',
    'RuntimeAttestation',
    'RuntimeAttestationEvaluation',
    'SHA256PhysicalChecksum',
    'SHA512PhysicalChecksum',
    'SICapabilities',
    'SICapabilitiesA2ui',
    'SICapabilitiesCommerce',
    'SICapabilitiesComponents',
    'SICapabilitiesComponentsStandardItem',
    'SICapabilitiesModalities',
    'SIComponentCatalog',
    'SIComponentCatalogComponentsItem',
    'SIContextUse',
    'SIGetOfferingRequest',
    'SIGetOfferingResponse',
    'SIGetOfferingResponseMatchingProductsItem',
    'SIGetOfferingResponseOffering',
    'SIIdentity',
    'SIIdentityConsentScopeItem',
    'SIIdentityPrivacyPolicyAcknowledged',
    'SIIdentityUser',
    'SIIdentityUserShippingAddress',
    'SIInitiateSessionRequest',
    'SIInitiateSessionResponse',
    'SIInitiateSessionResponseResponse',
    'SISendMessageRequest',
    'SISendMessageRequestActionResponse',
    'SISendMessageResponse',
    'SISendMessageResponseHandoff',
    'SISendMessageResponseHandoffContextForCheckout',
    'SISendMessageResponseHandoffIntent',
    'SISendMessageResponseHandoffIntentPrice',
    'SISendMessageResponseHandoffType',
    'SISendMessageResponseResponse',
    'SISessionStatus',
    'SISponsoredContext',
    'SISponsoredContextDeclaredBy',
    'SISponsoredContextDeclaredByRole',
    'SISponsoredContextDisclosureObligation',
    'SISponsoredContextDisclosureObligationJurisdictionsItem',
    'SISponsoredContextDisclosureObligationProximity',
    'SISponsoredContextDisclosureObligationTiming',
    'SISponsoredContextPayingPrincipal',
    'SISponsoredContextPayingPrincipalAccount',
    'SISponsoredContextReceipt',
    'SISponsoredContextReceiptHostReceipt',
    'SISponsoredContextReceiptHostReceiptDisclosureCommitment',
    'SISponsoredContextReceiptHostReceiptDisclosureCommitmentStatus',
    'SISponsoredContextReceiptHostReceiptStatus',
    'SITerminateSessionRequest',
    'SITerminateSessionRequestReason',
    'SITerminateSessionRequestTerminationContext',
    'SITerminateSessionRequestTerminationContextTransactionIntent',
    'SITerminateSessionRequestTerminationContextTransactionIntentAction',
    'SITerminateSessionResponse',
    'SITerminateSessionResponseAcpHandoff',
    'SITerminateSessionResponseFollowUp',
    'SITerminateSessionResponseFollowUpAction',
    'SIUIElement',
    'SIUIElementType',
    'SLAWindow',
    'ScanType',
    'ScopedCreativeApproval',
    'SealedCredential',
    'SearchBrandsError',
    'SearchBrandsRequest',
    'SearchBrandsResponse',
    'SearchBrandsResponseSearchBrandResult',
    'SearchBrandsResponseSearchBrandResultLogosItem',
    'SearchBrandsResponseSearchBrandResultRelationshipTrust',
    'SearchBrandsResponseSearchBrandResultRights',
    'SearchBrandsSuccess',
    'SeedSource',
    'SeedSuccess',
    'Segment',
    'SelectedCollections',
    'SelectedCollectionsCollectionsItem',
    'SelectedPlacements',
    'SellerAgentReference',
    'SellerInlinePlacementIdentity',
    'SellerPolicyDeclineReason',
    'SellerRenderedStatefulDisplayFormatDeclaration',
    'SettingsUpdateMode',
    'Setup',
    'SharedSlot',
    'SiCapabilities',
    'SiComponentCatalog',
    'SiContextUse',
    'SiGetOfferingRequest',
    'SiGetOfferingResponse',
    'SiIdentity',
    'SiInitiateSessionRequest',
    'SiInitiateSessionResponse',
    'SiSendMessageRequest',
    'SiSendMessageResponse',
    'SiSessionStatus',
    'SiSponsoredContext',
    'SiSponsoredContextReceipt',
    'SiTerminateSessionRequest',
    'SiTerminateSessionResponse',
    'SiUiElement',
    'SignalAvailabilityType',
    'SignalCatalogType',
    'SignalConditionsItemBinary',
    'SignalConditionsItemCategorical',
    'SignalConditionsItemNumeric',
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
    'SignalId',
    'SignalId8',
    'SignalId9',
    'SignalListing',
    'SignalListingRange',
    'SignalModelingDisclosure',
    'SignalModelingDisclosureJurisdictionsItem',
    'SignalModelingDisclosureJurisdictionsItemAudience',
    'SignalPricingOption',
    'SignalRef',
    'SignalRef1',
    'SignalRef2',
    'SignalRef3',
    'SignalRefDataProvider',
    'SignalRefProduct',
    'SignalRefSignalSource',
    'SignalSelectionGroupRule',
    'SignalSelectionGroupRuleSelectionMode',
    'SignalSelectionGroupRuleTargetingMode',
    'SignalSource',
    'SignalTagsValue',
    'SignalTargeting',
    'SignalTargeting1',
    'SignalTargeting2',
    'SignalTargeting3',
    'SignalTargetingBinary',
    'SignalTargetingCategorical',
    'SignalTargetingExpression',
    'SignalTargetingExpression1',
    'SignalTargetingExpression2',
    'SignalTargetingExpression3',
    'SignalTargetingExpressionBinary',
    'SignalTargetingExpressionCategorical',
    'SignalTargetingExpressionNumeric',
    'SignalTargetingItemBinary',
    'SignalTargetingItemCategorical',
    'SignalTargetingItemNumeric',
    'SignalTargetingNumeric',
    'SignalTargetingRules',
    'SignalTargetingRulesResolutionModel',
    'SignalValueType',
    'SignalsByProvider',
    'SimulationSuccess',
    'SlaWindow',
    'Slot',
    'SnapshotUnavailableReason',
    'SocialPlacementSurface',
    'SortDirection',
    'SortMetric',
    'SourceLocalizationReadback',
    'Special',
    'SpecialCategory',
    'Specification',
    'SponsoredPlacementFormatDeclaration',
    'SponsoredPlacementType',
    'SpotReportingCapability',
    'StaleResponseDetails',
    'StaleResponseDetailsOriginalError',
    'StaleResponseDetailsUpstream',
    'StandardEnum',
    'StandardScope',
    'StartTime',
    'StartTiming',
    'State',
    'StateTransitionSuccess',
    'Status46',
    'Status51',
    'StoreCatchment',
    'StoreCatchments',
    'StoreItem',
    'Storyboard',
    'Strength1',
    'StringArray',
    'Subject',
    'SuccessfulLookup',
    'SummaryView',
    'Supported',
    'SupportedChange',
    'SupportedDeliveryMethod',
    'SupportedDeliveryType',
    'SupportedDimension',
    'SupportedFormat',
    'SupportedHashedIdentifiersItem',
    'SupportedIdType',
    'SupportedIdentifierType',
    'SupportedProtocol',
    'SupportedScope',
    'SupportedSection',
    'SupportedTagType',
    'SupportedTarget5',
    'SupportedVersionsCompatibilityDetails',
    'SyncAccountsError',
    'SyncAccountsRequest',
    'SyncAccountsRequestAccountsItem',
    'SyncAccountsRequestAccountsItemNotificationConfigsItem',
    'SyncAccountsResponse',
    'SyncAccountsResponse1',
    'SyncAccountsResponse2',
    'SyncAccountsSuccess',
    'SyncAccountsSuccessAccountsItem',
    'SyncAccountsSuccessAccountsItemAction',
    'SyncAgentNotificationConfigsRequest',
    'SyncAgentNotificationConfigsRequestNotificationConfigsItem',
    'SyncAgentNotificationConfigsResponse',
    'SyncAgentNotificationConfigsResponseAction',
    'SyncAudiencesError',
    'SyncAudiencesRequest',
    'SyncAudiencesRequestAudiencesItem',
    'SyncAudiencesRequestAudiencesItemAudienceType',
    'SyncAudiencesResponse',
    'SyncAudiencesResponse1',
    'SyncAudiencesResponse2',
    'SyncAudiencesResponse3',
    'SyncAudiencesSubmitted',
    'SyncAudiencesSuccess',
    'SyncAudiencesSuccessAudiencesItem',
    'SyncAudiencesSuccessAudiencesItemAction',
    'SyncAudiencesSuccessAudiencesItemMatchBreakdownItem',
    'SyncAudiencesSuccessAudiencesItemSource',
    'SyncAudiencesSuccessAudiencesItemSourceAccessStatus',
    'SyncAudiencesSuccessAudiencesItemSourceKind',
    'SyncCatalogsAsyncInputRequired',
    'SyncCatalogsAsyncSubmitted',
    'SyncCatalogsAsyncWorking',
    'SyncCatalogsError',
    'SyncCatalogsErrorErrorsItem',
    'SyncCatalogsInputRequired',
    'SyncCatalogsInputRequiredReason',
    'SyncCatalogsRequest',
    'SyncCatalogsResponse',
    'SyncCatalogsResponse1',
    'SyncCatalogsResponse2',
    'SyncCatalogsResponse3',
    'SyncCatalogsResponseSubmitted',
    'SyncCatalogsSubmitted',
    'SyncCatalogsSuccess',
    'SyncCatalogsSuccessCatalogsItem',
    'SyncCatalogsSuccessCatalogsItemItemIssuesItem',
    'SyncCatalogsWorking',
    'SyncCreativesAsyncInputRequired',
    'SyncCreativesAsyncSubmitted',
    'SyncCreativesAsyncWorking',
    'SyncCreativesError',
    'SyncCreativesInputRequired',
    'SyncCreativesInputRequiredReason',
    'SyncCreativesRequest',
    'SyncCreativesRequestAssignmentsItem',
    'SyncCreativesRequestCreativesItem',
    'SyncCreativesResponse',
    'SyncCreativesResponse1',
    'SyncCreativesResponse2',
    'SyncCreativesResponse3',
    'SyncCreativesResponseSubmitted',
    'SyncCreativesSubmitted',
    'SyncCreativesSuccess',
    'SyncCreativesSuccessCreativesItem',
    'SyncCreativesWorking',
    'SyncEventSourcesError',
    'SyncEventSourcesRequest',
    'SyncEventSourcesRequestEventSourcesItem',
    'SyncEventSourcesResponse',
    'SyncEventSourcesResponse1',
    'SyncEventSourcesResponse2',
    'SyncEventSourcesSuccess',
    'SyncEventSourcesSuccessEventSourcesItem',
    'SyncEventSourcesSuccessEventSourcesItemSetup',
    'SyncEventSourcesSuccessEventSourcesItemSetupSnippetType',
    'SyncGovernanceError',
    'SyncGovernanceRequest',
    'SyncGovernanceRequestAccountsItem',
    'SyncGovernanceRequestAccountsItemGovernanceAgentsItem',
    'SyncGovernanceRequestAccountsItemGovernanceAgentsItemAuthentication',
    'SyncGovernanceResponse',
    'SyncGovernanceResponse1',
    'SyncGovernanceResponse2',
    'SyncGovernanceSuccess',
    'SyncGovernanceSuccessAccountsItem',
    'SyncGovernanceSuccessAccountsItemStatus',
    'SyncPlansRequest',
    'SyncPlansRequestPlansItem',
    'SyncPlansRequestPlansItemBudget',
    'SyncPlansRequestPlansItemBudgetAllocationsValue',
    'SyncPlansRequestPlansItemChannels',
    'SyncPlansRequestPlansItemChannelsMixTargetsValue',
    'SyncPlansRequestPlansItemDelegationsItem',
    'SyncPlansRequestPlansItemDelegationsItemBudgetLimit',
    'SyncPlansRequestPlansItemPortfolio',
    'SyncPlansRequestPlansItemPortfolioTotalBudgetCap',
    'SyncPlansResponse',
    'SyncPlansResponsePlansItem',
    'SyncPlansResponsePlansItemCategoriesItem',
    'SyncPlansResponsePlansItemCategoriesItemStatus',
    'SyncPlansResponsePlansItemResolvedPoliciesItem',
    'SyncPlansResponsePlansItemResolvedPoliciesItemSource',
    'SyncPlansResponsePlansItemStatus',
    'SyncPrincipalRequest',
    'SyncPrincipalRequestConfiguration',
    'SyncPrincipalRequestConfigurationNotificationConfigsItem',
    'SyncPrincipalResponse',
    'SyncReportingReceiptsRequest',
    'SyncReportingReceiptsRequestAdjustmentReceiptsItem',
    'SyncReportingReceiptsRequestReceiptsItem',
    'SyncReportingReceiptsResponse',
    'SyncReportingStatusRequest',
    'SyncReportingStatusRequestStatusesItem',
    'SyncReportingStatusResponse',
    'TMPError',
    'TMPErrorCode',
    'TMPIdentityMatch',
    'TMPIdentityMatchBuyerAgent',
    'TMPProviderRegistration',
    'TMPProviderRegistrationContextMatch',
    'TMPProviderRegistrationIdentityMatch',
    'TMPProviderRegistrationStatus',
    'TMPResponseType',
    'TMPXChunk',
    'TagURL',
    'TagURLMacroDeclarationsItem',
    'Tags',
    'Talent',
    'TalentRole',
    'Target10',
    'Target16',
    'Target17',
    'TargetLocalizationReadback',
    'TargetMaximizeValue',
    'TargetPerAdSpend',
    'TargetVariant',
    'TargetingKv',
    'TargetingKvMappingValue',
    'TargetingModification',
    'TargetingModification1',
    'TargetingModification2',
    'TargetingOverlay',
    'TargetingOverlayAgeRestriction',
    'TargetingOverlayDevicePlatform',
    'TargetingOverlayDeviceType',
    'TargetingOverlayGeoProximity',
    'TargetingOverlayGeoProximityItem',
    'TargetingOverlayGeoProximityItemGeometry',
    'TargetingOverlayGeoProximityItemGeometryType',
    'TargetingOverlayGeoProximityItemLatLngRadius',
    'TargetingOverlayGeoProximityItemLatLngTransportModeTravelTime',
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
    'Targets1',
    'Targets2',
    'Targets3',
    'Targets4',
    'Task',
    'TaskStatus',
    'TaskType',
    'Tasks1',
    'Tasks2',
    'Tasks3',
    'Tasks4',
    'Tasks5',
    'Tasks6',
    'Tasks7',
    'Tasks8',
    'Tasks9',
    'TasksGetRequest',
    'TasksGetResponse',
    'TasksGetResponseError',
    'TasksGetResponseErrorDetails',
    'TasksGetResponseHistoryItem',
    'TasksGetResponseProgress',
    'TasksItemAcceptProposal',
    'TasksItemAcquireRights',
    'TasksItemActivateSignal',
    'TasksItemBuildCreative',
    'TasksItemBuyProducts',
    'TasksItemControlMediaBuy',
    'TasksItemCreateMediaBuy',
    'TasksItemCreateMediaBuyModesItem',
    'TasksItemUpdateMediaBuy',
    'TasksItemUpdateRights',
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
    'ThirdPartyFormatTarget',
    'TimeBasedPricingOption',
    'TimeBasedPricingOptionParameters',
    'TimeBasedPricingOptionParametersTimeUnit',
    'TimeBasedView',
    'TimeForecastDimension',
    'TmpError',
    'TmpProviderRegistration',
    'TmpProviderRegistration1',
    'TmpProviderRegistration2',
    'TmpResponseType',
    'TmpxChunk',
    'TmpxMacroMappingValue',
    'TmpxProviders',
    'Tone',
    'Totals',
    'TrackerExecutionActor',
    'TrackerExecutionContract',
    'TrackerExecutionSelector',
    'TrackerExecutionSelector1',
    'TrackerExecutionSelectorDaastTracker',
    'TrackerExecutionSelectorPixelTrackerImg',
    'TrackerExecutionSelectorVastTracker',
    'TrackerFiringPath',
    'Tracks',
    'TranscriptFormat',
    'TranscriptSource',
    'TranscriptSource1',
    'Transformer',
    'TransformerMultiplicity',
    'TransformerMultiplicityVariantDimensionsItem',
    'TransformerParam',
    'TransformerParamOptionsItem',
    'TransformerParamType',
    'TransformerParamValueSource',
    'TransformerVoiceSynthesisRefItem',
    'TransformerVoiceSynthesisRefItemBrandAgent',
    'TransitionMode9',
    'TransitionsItemInViewTimer',
    'TransitionsItemMediaEvent',
    'TransitionsItemScrollProgressScrollScrollLinked',
    'TransitionsItemScrollThresholdScroll',
    'TransitionsItemTimer',
    'TransitionsItemTimerTransitionMode',
    'TransitionsItemUserAction',
    'Transport1',
    'TransportMode',
    'TravelTimeUnit',
    'TruncationSentinel',
    'TruncationSentinelTruncation',
    'TrustedMatch',
    'Type6',
    'UIDType',
    'URLAsset',
    'URLAssetMacroDeclarationsItem',
    'URLAssetMacroDeclarationsItemLocation',
    'URLAssetRequirements',
    'URLAssetRequirementsProtocolsItem',
    'URLAssetRequirementsRole',
    'URLAssetType',
    'Uid',
    'UidType',
    'Unassign',
    'UnavailableLookup',
    'UnavailableLookupAdcpError',
    'UnavailableLookupErrorsItem',
    'UnchangedReportingAdjustmentReceipt',
    'UnchangedReportingAdjustmentReceiptAdjustmentReceipt',
    'UnchangedReportingConsumerStatus',
    'UnchangedReportingConsumerStatusConsumerStatus',
    'UnchangedReportingReceipt',
    'UnchangedReportingReceiptReceipt',
    'UnconfiguredPrincipal',
    'UniversalMacro',
    'UnknownFormatAsset',
    'UnknownGroupAsset',
    'UnmetRequirement',
    'UnsupportedRefinementDimensionDetails',
    'UpdateCollectionListRequest',
    'UpdateCollectionListResponse',
    'UpdateContentStandardsError',
    'UpdateContentStandardsRequest',
    'UpdateContentStandardsRequestScope',
    'UpdateContentStandardsResponse',
    'UpdateContentStandardsResponse1',
    'UpdateContentStandardsResponse2',
    'UpdateContentStandardsSuccess',
    'UpdateFrequency',
    'UpdateMediaBuyAsyncInputRequired',
    'UpdateMediaBuyAsyncSubmitted',
    'UpdateMediaBuyAsyncWorking',
    'UpdateMediaBuyError',
    'UpdateMediaBuyInputRequired',
    'UpdateMediaBuyInputRequiredReason',
    'UpdateMediaBuyRequest',
    'UpdateMediaBuyResponse',
    'UpdateMediaBuyResponse1',
    'UpdateMediaBuyResponse2',
    'UpdateMediaBuyResponse3',
    'UpdateMediaBuyResponseSubmitted',
    'UpdateMediaBuySubmitted',
    'UpdateMediaBuySuccess',
    'UpdateMediaBuySuccessBidding',
    'UpdateMediaBuyWorking',
    'UpdatePropertyListRequest',
    'UpdatePropertyListResponse',
    'UpdateRightsError',
    'UpdateRightsRequest',
    'UpdateRightsResponse',
    'UpdateRightsResponse1',
    'UpdateRightsResponse2',
    'UpdateRightsSuccess',
    'UpdateRightsSuccessRightsConstraint',
    'UpstreamTrafficSuccess',
    'UpstreamTrafficSuccessRecordedCallsItem',
    'UpstreamTrafficSuccessRecordedCallsItemAttestationMode',
    'UpstreamTrafficSuccessRecordedCallsItemIdentifierMatchProofsItem',
    'UpstreamTrafficSuccessRecordedCallsItemMethod',
    'UpstreamTrafficSuccessRecordedCallsItemPurpose',
    'UrlAsset',
    'UrlAssetRequirements',
    'UrlAssetType',
    'UserMatch',
    'V1CreativeNamedFormatReference',
    'V1Pattern',
    'V1Pattern1',
    'V1PatternFormatIdGlob',
    'V1PatternStructural',
    'V1V2CanonicalFormatMappingRegistry',
    'V1V2CanonicalFormatMappingRegistryMappingsItem',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItem',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItemTransform',
    'V2CreativeCanonicalFormatKind',
    'VASTAsset',
    'VASTAssetInline',
    'VASTAssetRequirements',
    'VASTAssetUrl',
    'VASTAudioFormatDeclaration',
    'VASTMediaDeliveryMethod',
    'VASTMediaFileRequirements',
    'VASTTrackerAsset',
    'VASTTrackerAssetTarget',
    'VASTTrackerConstraints',
    'VASTTrackerConstraintsVastEvent',
    'VASTTrackerConstraintsVastTarget',
    'VASTTrackingEvent',
    'VASTVersion',
    'VASTVersionMismatchDetails',
    'VASTVersionMismatchDetailsDocumentRole',
    'VASTVersionMismatchDetailsMismatchReason',
    'VASTVideoFormatDeclaration',
    'VCPMPricingOption',
    'ValidateContentDeliveryRequest',
    'ValidateContentDeliveryRequestRecordsItem',
    'ValidateContentDeliveryResponse',
    'ValidateContentDeliveryResponse1',
    'ValidateContentDeliveryResponse2',
    'ValidateContentDeliveryResponseErrors',
    'ValidateContentDeliveryResponseResultsSummary',
    'ValidateContentDeliveryResponseResultsSummaryResultsItem',
    'ValidateContentDeliveryResponseResultsSummarySummary',
    'ValidateInputRequest',
    'ValidateInputRequestTargetsItem',
    'ValidateInputResponse',
    'ValidateInputResult',
    'ValidateInputResultResultKind',
    'ValidateInputResultTarget',
    'ValidateInputResultTargetKind',
    'ValidateInputResultViolationsItem',
    'ValidateInputResultWarningsItem',
    'ValidatePropertyDeliveryRequest',
    'ValidatePropertyDeliveryResponse',
    'ValidatePropertyDeliveryResponseAggregate',
    'ValidatePropertyDeliveryResponseAuthorizationSummary',
    'ValidatePropertyDeliveryResponseSummary',
    'ValidatedPrincipalDryRun',
    'ValidatedPrincipalDryRunAction',
    'ValidationMode',
    'ValidationResult',
    'ValidationResultFeaturesItem',
    'ValidationResultFeaturesItemRequirement',
    'ValidationResultStatus',
    'Value',
    'ValueMapping',
    'Variant',
    'Variants1',
    'Variants2',
    'VastAsset',
    'VastAsset3',
    'VastAsset4',
    'VastAssetRequirements',
    'VastMediaDeliveryMethod',
    'VastMediafileRequirements',
    'VastOffset',
    'VastTrackerAsset',
    'VastTrackerConstraints',
    'VastTrackingEvent',
    'VastVersion',
    'VastVersionMismatchDetails',
    'VastVersionMismatchDetails3',
    'VastVersions',
    'VcpmPricingOption',
    'VehicleItem',
    'VehicleItemBodyStyle',
    'VehicleItemCondition',
    'VehicleItemFuelType',
    'VehicleItemMileage',
    'VehicleItemMileageUnit',
    'VehicleItemTransmission',
    'VendorErrorCodeRegistry',
    'VendorErrorCodeRegistryVendorsValue',
    'VendorErrorCodeRegistryVendorsValueCodesValue',
    'VendorMetricID',
    'VendorMetricId',
    'VendorMetricOptimization',
    'VendorMetricOptimizationSupportedMetric',
    'VendorMetricOptimizationSupportedMetricSupportedTargetsItem',
    'VendorMetricValue',
    'VendorPricing',
    'VendorPricing1',
    'VendorPricing2',
    'VendorPricing3',
    'VendorPricing4',
    'VendorPricing5',
    'VendorPricingOption',
    'VendorPricingOptionCpm',
    'VendorPricingOptionCustom',
    'VendorPricingOptionFlatFee',
    'VendorPricingOptionPerUnit',
    'VendorPricingOptionPercentOfMedia',
    'VendorRelationship',
    'Vendors',
    'VerificationStatus',
    'VerificationTokenMode',
    'VerifyBrandClaimError',
    'VerifyBrandClaimErrorResponse',
    'VerifyBrandClaimRequest',
    'VerifyBrandClaimResponse',
    'VerifyBrandClaimResponseSignedResponse',
    'VerifyBrandClaimResponseSignedResponsePayload',
    'VerifyBrandClaimResponseSignedSuccessPayload',
    'VerifyBrandClaimResponseSignedSuccessPayloadClaimType',
    'VerifyBrandClaimSignedSuccessPayload',
    'VerifyBrandClaimSuccess',
    'VerifyBrandClaimSuccessResponse',
    'VerifyBrandClaimsError',
    'VerifyBrandClaimsErrorResponse',
    'VerifyBrandClaimsRequestBulk',
    'VerifyBrandClaimsResponseBulk',
    'VerifyBrandClaimsResponseBulkSignedResponse',
    'VerifyBrandClaimsResponseBulkSignedResponsePayload',
    'VerifyBrandClaimsResponseBulkSignedSuccessPayload',
    'VerifyBrandClaimsResultError',
    'VerifyBrandClaimsResultSuccess',
    'VerifyBrandClaimsSignedSuccessPayload',
    'VerifyBrandClaimsSuccess',
    'VerifyParentClaim',
    'VerifyParentClaimClaim',
    'VerifyPropertyClaim',
    'VerifyPropertyClaimClaim',
    'VerifyPropertyClaimClaimProperty',
    'VerifyPropertyClaimClaimPropertyStore',
    'VerifySubsidiaryClaim',
    'VerifySubsidiaryClaimClaim',
    'VerifyTrademarkClaim',
    'VerifyTrademarkClaimClaim',
    'VersionUnsupportedDetails',
    'Video',
    'VideoAsset',
    'VideoAssetAudioBitDepth',
    'VideoAssetChromaSubsampling',
    'VideoAssetColorSpace',
    'VideoAssetHdrFormat',
    'VideoAssetRequirements',
    'VideoAssetRequirementsAudioCodecsItem',
    'VideoAssetRequirementsContainersItem',
    'VideoAssetVideoBitDepth',
    'VideoBrief',
    'VideoBriefSegmentsItem',
    'VideoPlacementType',
    'ViewThreshold1',
    'ViewThresholdBasis',
    'ViewThresholdDurationSeconds',
    'ViewabilityStandard',
    'Voice',
    'WCAGLevel',
    'WarehouseMaterialization',
    'WarehouseMaterializationDestination',
    'Warning',
    'WarningAffectedResource',
    'WarningAffectedResourceResourceType',
    'WarningCode',
    'Watermark',
    'WatermarkMediaType',
    'WcagLevel',
    'WebhookActivityRecord',
    'WebhookActivityRecordStatus',
    'WebhookAsset',
    'WebhookAssetRequirements',
    'WebhookAssetSecurity',
    'WebhookChallenge',
    'WebhookChallengeResponse',
    'WebhookResponseType',
    'WebhookSecurityMethod',
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
    'Window',
    'XEntityTypes',
    'ZipAsset',
]


#: The words more than one domain publishes, and the domains that publish each.
#: Bound nowhere in this module -- the public ``adcp.types.<domain>`` path is the
#: only one that can say which of the two a caller meant.
__adcp_ambiguous__: dict[str, tuple[str, ...]] = {
    'AudienceSource': ('core', 'enums'),
}


#: Upstream's published words this module declines, and the
#: ``<module>.<symbol>`` subjects each one has.  A word that IS in ``__all__``
#: is declined because the generated surface already publishes it and resolves
#: it to the class the schemas name; a word that is NOT resolves nowhere here,
#: because upstream derived it from a property key more than one document uses
#: and the subjects below are distinct classes.  Each is reachable under its
#: own ``adcp.types.<domain>`` word, which is the name minted from the parent
#: class and the key together.
__adcp_alias_declined__: dict[str, tuple[str, ...]] = {
    'AcceptedVerifier': ('core.attestation_capabilities.AcceptedVerifiersItem', 'core.creative_policy.AcceptedVerifiersItem'),
    'Account': ('account.sync_governance_request.AccountsItem', 'account.sync_governance_response.AccountsItem', 'compliance.comply_test_controller_request.ComplyTestControllerRequestAccount', 'protocol.get_adcp_capabilities_response.GetAdCPCapabilitiesResponseAccount', 'sponsored_intelligence.si_sponsored_context.PayingPrincipalAccount'),
    'Action': ('core.canonical_media_buy_action.CanonicalMediaBuyActionControlMediaBuyAction', 'media_buy.get_products_request.RefineItemProductAction', 'protocol.sync_principal_response.AppliedPrincipalConfigurationAction'),
    'Artifact': ('core.creative_variant.GenerationContextArtifact',),
    'AttributionWindow': ('protocol.get_adcp_capabilities_response.AttributionWindowsItem',),
    'AudienceEvidence': ('protocol.get_adcp_capabilities_response.MediaBuyAudienceEvidence',),
    'AudioCodec': ('core.requirements.video_asset_requirements.AudioCodecsItem', 'formats.canonical.audio_hosted.AudioCodecsItem', 'formats.canonical.video_hosted.AudioCodecsItem'),
    'BrandId': ('core.brand_id.BrandID',),
    'Catalog': ('media_buy.sync_catalogs_response.CatalogsItem',),
    'Category': ('governance.sync_plans_response.CategoriesItem',),
    'ContentStandards': ('protocol.get_adcp_capabilities_response.MediaBuyContentStandards',),
    'Countries': ('core.geo_region_support.ObjAllValues',),
    'Creative': ('creative.get_creative_delivery_response.CreativesItem', 'creative.list_creatives_response.CreativesItem', 'creative.sync_creatives_response.CreativesItem', 'media_buy.build_creative_response.CreativesItem'),
    'Demographics': ('core.targeting_overlay_requirements.TargetingOverlayRequirementsDemographicsAge', 'core.targeting_overlay_support.TargetingOverlaySupportDemographicsAge'),
    'EventSource': ('core.canonical_optimization_goal.EventSourcesItem', 'core.optimization_goal.EventSourcesItem', 'media_buy.sync_event_sources_request.EventSourcesItem'),
    'EventType': ('core.notification_config.EventTypesItem', 'core.registry_event.RegistryEventEventType', 'core.wholesale_feed_event.WholesaleFeedEventType'),
    'Exclusivity': ('brand.rights_terms.RightsTermsExclusivity',),
    'Feature': ('content_standards.calibrate_content_response.FeaturesItem', 'property.validation_result.FeaturesItem'),
    'Field1': ('brand.get_brand_identity_request.BrandIdentityField', 'core.macro_declaration.LocationField', 'core.tasks_list_request.SortField', 'creative.list_creatives_request.FieldsItem', 'media_buy.get_products_request.FieldsItem', 'signals.get_signals_request.FieldsItem'),
    'Finding': ('governance.check_governance_response.FindingsItem', 'governance.report_plan_outcome_response.FindingsItem'),
    'Format': ('core.reporting_delivery_method.FileFormat', 'core.requirements.audio_asset_requirements.FormatsItem', 'core.requirements.image_asset_requirements.FormatsItem'),
    'GeoProximity': ('core.targeting_overlay_requirements.TargetingOverlayRequirementsGeoProximity', 'core.targeting_overlay_support.TargetingOverlaySupportGeoProximity'),
    'GovernanceAgent': ('account.sync_governance_request.GovernanceAgentsItem', 'core.account.ObjUrl'),
    'Identifier': ('collection.base_collection_source.IdentifiersItem', 'core.collection_distribution.IdentifiersItem', 'core.delivery_metrics.IdentifiersItem', 'core.placement_definition.IdentifiersItem'),
    'ImageFormat': ('formats.canonical.image.ImageFormatsItem', 'formats.canonical.native_in_feed.ImageFormatsItem'),
    'Interval': ('core.demographic_reporting_capability.IntervalsItem', 'core.demographic_targeting_capability.IntervalsItem'),
    'Jurisdiction': ('core.provenance.JurisdictionsItem', 'core.signal_modeling_disclosure.JurisdictionsItem', 'sponsored_intelligence.si_sponsored_context.JurisdictionsItem'),
    'MediaBuy': ('media_buy.get_media_buys_response.MediaBuysItem', 'protocol.get_adcp_capabilities_response.GetAdCPCapabilitiesResponseMediaBuy'),
    'MediaBuyDelivery': ('media_buy.get_media_buy_delivery_response.MediaBuyDeliveriesItem', 'media_buy.media_buy_delivery_webhook_result.MediaBuyDeliveriesItem'),
    'Metric': ('compliance.comply_test_controller_request.MetricsItem', 'core.optimization_goal.OptimizationMetric', 'core.reporting_report_definition.MetricsItem', 'protocol.get_adcp_capabilities_response.MetricsItem'),
    'Metro': ('core.offering.MetrosItem', 'core.product_filters.ObjSystemCode'),
    'Mode': ('core.bidding_policy_capability.ModesItem', 'protocol.get_adcp_capabilities_response.TasksItemCreateMediaBuyModesItem'),
    'NotificationType': ('media_buy.media_buy_delivery_webhook_result.MediaBuyDeliveryWebhookResultNotificationType',),
    'Offering': ('sponsored_intelligence.si_get_offering_response.SIGetOfferingResponseOffering',),
    'Pacing': ('governance.check_governance_request.DeliveryMetricsPacing',),
    'Package': ('governance.report_plan_outcome_request.PackagesItem', 'media_buy.get_media_buys_response.PackagesItem'),
    'PaymentTerms': ('core.insertion_order.TermsPaymentTerms',),
    'PerformanceFeedback': ('protocol.get_adcp_capabilities_response.MediaBuyPerformanceFeedback',),
    'PlacementSelection': ('core.targeting_overlay_support.TargetingOverlaySupportPlacementSelection',),
    'Plan': ('governance.get_plan_audit_logs_response.PlansItem', 'governance.sync_plans_response.PlansItem'),
    'Price': ('sponsored_intelligence.si_send_message_response.IntentPrice',),
    'PropertyFeature': ('adagents.PropertyFeaturesItem',),
    'PropertyType': ('core.real_estate_item.RealEstateItemPropertyType',),
    'ProposalRefinement': ('protocol.get_adcp_capabilities_response.MediaBuyProposalRefinement',),
    'Provenance': ('core.reference_renderer.ReferenceRendererProvenance',),
    'Provider': ('core.product.ProvidersItem', 'core.product_filters.ProvidersItem', 'core.reporting_dataset_share_destination.ObjDomain'),
    'Range': ('core.signal_listing.ObjMinMax', 'protocol.get_adcp_capabilities_response.PropertyFeaturesItemRange'),
    'ReportingFrequency': ('core.reporting_webhook.ReportingWebhookReportingFrequency',),
    'RequiredVendorMetric': ('core.product_filters.RequiredVendorMetricsItem', 'core.product_offer_filters.RequiredVendorMetricsItem'),
    'Result': ('content_standards.validate_content_delivery_response.ResultsItem', 'creative.preview_creative_response.ResultsItem', 'protocol.get_principal_response.UnconfiguredPrincipal', 'protocol.sync_principal_response.ValidatedPrincipalDryRun'),
    'Results': ('media_buy.sync_reporting_receipts_response.FailedReportingReceipt', 'media_buy.sync_reporting_status_response.RecordedReportingConsumerStatus'),
    'Right': ('brand.get_rights_response.RightsItem', 'core.signal_definition.RightsItem'),
    'Route': ('core.preview_provider.RoutesItem', 'protocol.get_adcp_capabilities_response.RoutesItem'),
    'Size': ('formats.canonical.display_tag.SizesItem', 'formats.canonical.html5.SizesItem', 'formats.canonical.image.SizesItem'),
    'Status': ('governance.sync_plans_response.PlansItemStatus', 'media_buy.get_products_response.RefinementAppliedItemRequestStatus', 'sponsored_intelligence.si_sponsored_context_receipt.HostReceiptStatus'),
    'SupportedTarget': ('core.product.MetricOptimizationSupportedTargetsItem', 'core.vendor_metric_optimization_supported_metric.SupportedTargetsItem', 'protocol.get_adcp_capabilities_response.SupportedTargetsItem'),
    'VariantDimension': ('core.transformer.VariantDimensionsItem', 'protocol.get_adcp_capabilities_response.VariantDimensionsItem'),
    'VendorMetric': ('core.canonical_reporting_capabilities.VendorMetricsItem', 'core.reporting_capabilities.VendorMetricsItem'),
    'VendorMetricOptimization': ('protocol.get_adcp_capabilities_response.MediaBuyVendorMetricOptimization',),
    'Violation': ('creative.validate_input_result.ViolationsItem', 'error_details.accessibility_violation.ViolationsItem'),
}
