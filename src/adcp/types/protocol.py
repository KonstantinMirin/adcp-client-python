"""The public types of the ``protocol`` domain.

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

from ._schemas.protocol.get_adcp_capabilities_request import GetAdCPCapabilitiesRequest as GetAdCPCapabilitiesRequest
from ._schemas.protocol.get_adcp_capabilities_request import ProtocolsItem as GetAdCPCapabilitiesRequestProtocolsItem
from ._schemas.protocol.get_adcp_capabilities_response import (
    AcceptancePolicyDiscovery as GetAdCPCapabilitiesResponseMediaBuyAcceptancePolicyDiscovery,
)
from ._schemas.protocol.get_adcp_capabilities_response import AccountChangeFeedSupported as AccountChangeFeedSupported
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountChangeFeedUnsupported as AccountChangeFeedUnsupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountIdentityUpdatesSupported as AccountIdentityUpdatesSupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountIdentityUpdatesUnsupported as AccountIdentityUpdatesUnsupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountNotifications as GetAdCPCapabilitiesResponseAccountNotifications,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountNotificationsSupported as AccountNotificationsSupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountNotificationsSupportedEventTypesItem as AccountNotificationsSupportedEventTypesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccountNotificationsUnsupported as AccountNotificationsUnsupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AccreditationsItem as GetAdCPCapabilitiesResponseMeasurementMetricsItemAccreditationsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import Adcp as GetAdCPCapabilitiesResponseAdcp
from ._schemas.protocol.get_adcp_capabilities_response import (
    AgeRestriction as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingAgeRestriction,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AttributionWindowsItem as GetAdCPCapabilitiesResponseMediaBuyConversionTrackingAttributionWindowsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    AudienceTargeting as GetAdCPCapabilitiesResponseMediaBuyAudienceTargeting,
)
from ._schemas.protocol.get_adcp_capabilities_response import Brand as GetAdCPCapabilitiesResponseBrand
from ._schemas.protocol.get_adcp_capabilities_response import (
    BudgetCapping as GetAdCPCapabilitiesResponseMediaBuyBudgetCapping,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    BudgetCappingTimezoneBasis as GetAdCPCapabilitiesResponseBudgetCappingTimezoneBasis,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityChangeNotificationsSupported as CapabilityChangeNotificationsSupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityChangeNotificationsSupportedEventTypesItem as CapabilityChangeNotificationsSupportedEventTypesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityChangeNotificationsUnsupported as CapabilityChangeNotificationsUnsupported,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityChanges as GetAdCPCapabilitiesResponseAdcpCapabilityChanges,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityChangesNotifications as GetAdCPCapabilitiesResponseAdcpCapabilityChangesNotifications,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CapabilityReportingDeliveryMethod as GetAdCPCapabilitiesResponseCapabilityReportingDeliveryMethod,
)
from ._schemas.protocol.get_adcp_capabilities_response import ChangeFeed as GetAdCPCapabilitiesResponseAccountChangeFeed
from ._schemas.protocol.get_adcp_capabilities_response import (
    ComplianceTesting as GetAdCPCapabilitiesResponseComplianceTesting,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CompromiseNotification as GetAdCPCapabilitiesResponseIdentityCompromiseNotification,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    ConversionTracking as GetAdCPCapabilitiesResponseMediaBuyConversionTracking,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CoversContentDigest as GetAdCPCapabilitiesResponseRequestSigningCoversContentDigest,
)
from ._schemas.protocol.get_adcp_capabilities_response import Creative as GetAdCPCapabilitiesResponseCreative
from ._schemas.protocol.get_adcp_capabilities_response import (
    CreativeApprovalMode as GetAdCPCapabilitiesResponseMediaBuyCreativeApprovalMode,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    CreativeFeaturesItem as GetAdCPCapabilitiesResponseGovernanceCreativeFeaturesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import CreativeFeaturesItemRange as CreativeFeaturesItemRange
from ._schemas.protocol.get_adcp_capabilities_response import CreativeFeaturesItemType as CreativeFeaturesItemType
from ._schemas.protocol.get_adcp_capabilities_response import (
    CreativeSpecs as GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecs,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    Demographics as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingDemographics,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    DiscoveryMode as GetAdCPCapabilitiesResponseSignalsDiscoveryModesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    Endpoint as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpoint,
)
from ._schemas.protocol.get_adcp_capabilities_response import Execution as GetAdCPCapabilitiesResponseMediaBuyExecution
from ._schemas.protocol.get_adcp_capabilities_response import ExtensionsSupportedItem as ExtensionsSupportedItem
from ._schemas.protocol.get_adcp_capabilities_response import (
    FrequencyCapping as GetAdCPCapabilitiesResponseMediaBuyFrequencyCapping,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    GeoMetros as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoMetros,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    GeoProximity as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingGeoProximity,
)
from ._schemas.protocol.get_adcp_capabilities_response import GetAdCPCapabilitiesResponse as GetAdCPCapabilitiesResponse
from ._schemas.protocol.get_adcp_capabilities_response import (
    GetAdCPCapabilitiesResponseAccount as GetAdCPCapabilitiesResponseAccount,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    GetAdCPCapabilitiesResponseMediaBuy as GetAdCPCapabilitiesResponseMediaBuy,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    GetAdCPCapabilitiesResponseMediaBuyFeatures as GetAdCPCapabilitiesResponseMediaBuyFeatures,
)
from ._schemas.protocol.get_adcp_capabilities_response import Governance as GetAdCPCapabilitiesResponseGovernance
from ._schemas.protocol.get_adcp_capabilities_response import (
    GovernanceEnforcement as GetAdCPCapabilitiesResponseAdcpGovernanceEnforcement,
)
from ._schemas.protocol.get_adcp_capabilities_response import Idempotency as GetAdCPCapabilitiesResponseAdcpIdempotency
from ._schemas.protocol.get_adcp_capabilities_response import IdempotencySupported as IdempotencySupported
from ._schemas.protocol.get_adcp_capabilities_response import IdempotencyUnsupported as IdempotencyUnsupported
from ._schemas.protocol.get_adcp_capabilities_response import Identity as GetAdCPCapabilitiesResponseIdentity
from ._schemas.protocol.get_adcp_capabilities_response import (
    IdentityUpdates as GetAdCPCapabilitiesResponseAccountIdentityUpdates,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    KeyOrigins as GetAdCPCapabilitiesResponseIdentityKeyOrigins,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    KeywordTargets as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingKeywordTargets,
)
from ._schemas.protocol.get_adcp_capabilities_response import Language as Language
from ._schemas.protocol.get_adcp_capabilities_response import (
    LifecycleToolsItem as GetAdCPCapabilitiesResponseMediaBuyLifecycleToolsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    Localization as GetAdCPCapabilitiesResponseCreativeLocalization,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MatchingLatencyHours as GetAdCPCapabilitiesResponseMediaBuyAudienceTargetingMatchingLatencyHours,
)
from ._schemas.protocol.get_adcp_capabilities_response import Measurement as GetAdCPCapabilitiesResponseMeasurement
from ._schemas.protocol.get_adcp_capabilities_response import (
    MeasurementGateway as GetAdCPCapabilitiesResponseMeasurementGateway,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MediaBuyAudienceEvidence as GetAdCPCapabilitiesResponseMediaBuyAudienceEvidence,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MediaBuyContentStandards as GetAdCPCapabilitiesResponseMediaBuyContentStandards,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MediaBuyPerformanceFeedback as GetAdCPCapabilitiesResponseMediaBuyPerformanceFeedback,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MediaBuyProposalRefinement as GetAdCPCapabilitiesResponseMediaBuyProposalRefinement,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MediaBuyVendorMetricOptimization as GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimization,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    MetricsItem as GetAdCPCapabilitiesResponseMeasurementMetricsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    Multiplicity as GetAdCPCapabilitiesResponseCreativeMultiplicity,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    NegativeKeywords as GetAdCPCapabilitiesResponseMediaBuyExecutionTargetingNegativeKeywords,
)
from ._schemas.protocol.get_adcp_capabilities_response import Oauth as GetAdCPCapabilitiesResponseOauth
from ._schemas.protocol.get_adcp_capabilities_response import (
    OperationsItem as GetAdCPCapabilitiesResponseCreativeSupportedFormatsItemOperationsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import Portfolio as GetAdCPCapabilitiesResponseMediaBuyPortfolio
from ._schemas.protocol.get_adcp_capabilities_response import Preview as GetAdCPCapabilitiesResponseCreativePreview
from ._schemas.protocol.get_adcp_capabilities_response import Principal as GetAdCPCapabilitiesResponseAdcpPrincipal
from ._schemas.protocol.get_adcp_capabilities_response import (
    Profile as GetAdCPCapabilitiesResponseWebhookSigningProfile,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    PropagationSurfacesItem as GetAdCPCapabilitiesResponseMediaBuyPropagationSurfacesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    PropertyFeaturesItem as GetAdCPCapabilitiesResponseGovernancePropertyFeaturesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    ProtocolTransportType as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointPreferred,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RegistrationTask as CapabilityChangeNotificationsSupportedRegistrationTask,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RelationshipNotifications as GetAdCPCapabilitiesResponseMediaBuyRelationshipNotifications,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RelationshipNotificationsEventTypesItem as GetAdCPCapabilitiesResponseMediaBuyRelationshipNotificationsEventTypesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    ReportingDestinationOfferingsItem as GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    ReportingDestinationOfferingsItemPattern as GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RepresentationResolution as GetAdCPCapabilitiesResponseCreativeRepresentationResolution,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RequestSigning as GetAdCPCapabilitiesResponseRequestSigning,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RightsAttestations as GetAdCPCapabilitiesResponseMediaBuyRightsAttestations,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RightsAttestationsRequirement as GetAdCPCapabilitiesResponseMediaBuyRightsAttestationsRequirement,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RoutesItem as GetAdCPCapabilitiesResponseCreativePreviewRoutesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    RuntimeAttestations as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestations,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SignalActivation as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivation,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SignalActivationRequirement as GetAdCPCapabilitiesResponseGovernanceRuntimeAttestationsSignalActivationRequirement,
)
from ._schemas.protocol.get_adcp_capabilities_response import Signals as GetAdCPCapabilitiesResponseSignals
from ._schemas.protocol.get_adcp_capabilities_response import (
    SignalsFeatures as GetAdCPCapabilitiesResponseSignalsFeatures,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SponsoredIntelligence as GetAdCPCapabilitiesResponseSponsoredIntelligence,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedChangesItem as AccountIdentityUpdatesSupportedSupportedChangesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedDimensionsItem as GetAdCPCapabilitiesResponseMediaBuyProposalRefinementSupportedDimensionsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedFormatsItem as GetAdCPCapabilitiesResponseCreativeSupportedFormatsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedHashedIdentifiersItem as SupportedHashedIdentifiersItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedPeriodsItem as GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedPeriodsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedProtocolsItem as GetAdCPCapabilitiesResponseSupportedProtocolsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedScopesItem as GetAdCPCapabilitiesResponseMediaBuyBudgetCappingSupportedScopesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedSectionsItem as GetAdCPCapabilitiesResponseAdcpPrincipalSupportedSectionsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    SupportedTargetsItem as GetAdCPCapabilitiesResponseMediaBuyVendorMetricOptimizationSupportedTargetsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    Targeting as GetAdCPCapabilitiesResponseMediaBuyExecutionTargeting,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    TasksItem as GetAdCPCapabilitiesResponseAdcpGovernanceEnforcementTasksItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemAcceptProposal as TasksItemAcceptProposal
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemAcquireRights as TasksItemAcquireRights
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemActivateSignal as TasksItemActivateSignal
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemBuildCreative as TasksItemBuildCreative
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemBuyProducts as TasksItemBuyProducts
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemControlMediaBuy as TasksItemControlMediaBuy
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemCreateMediaBuy as TasksItemCreateMediaBuy
from ._schemas.protocol.get_adcp_capabilities_response import (
    TasksItemCreateMediaBuyModesItem as TasksItemCreateMediaBuyModesItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemUpdateMediaBuy as TasksItemUpdateMediaBuy
from ._schemas.protocol.get_adcp_capabilities_response import TasksItemUpdateRights as TasksItemUpdateRights
from ._schemas.protocol.get_adcp_capabilities_response import (
    TransportsItem as GetAdCPCapabilitiesResponseSponsoredIntelligenceEndpointTransportsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    TrustedMatch as GetAdCPCapabilitiesResponseMediaBuyExecutionTrustedMatch,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    VariantDimensionsItem as GetAdCPCapabilitiesResponseCreativeMultiplicityVariantDimensionsItem,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    VastValidation as GetAdCPCapabilitiesResponseMediaBuyExecutionCreativeSpecsVastValidation,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    WebhookSigning as GetAdCPCapabilitiesResponseWebhookSigning,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    WholesaleFeedVersioning as GetAdCPCapabilitiesResponseWholesaleFeedVersioning,
)
from ._schemas.protocol.get_adcp_capabilities_response import (
    WholesaleFeedWebhooks as GetAdCPCapabilitiesResponseWholesaleFeedWebhooks,
)
from ._schemas.protocol.get_principal_request import GetPrincipalRequest as GetPrincipalRequest
from ._schemas.protocol.get_principal_response import CurrentPrincipalConfiguration as CurrentPrincipalConfiguration
from ._schemas.protocol.get_principal_response import FailedPrincipalRead as FailedPrincipalRead
from ._schemas.protocol.get_principal_response import GetPrincipalResponse as GetPrincipalResponse
from ._schemas.protocol.get_principal_response import (
    RecognizedPrincipalWithoutStandingConfiguration as RecognizedPrincipalWithoutStandingConfiguration,
)
from ._schemas.protocol.get_principal_response import Result as GetPrincipalResponseResult
from ._schemas.protocol.get_principal_response import UnconfiguredPrincipal as UnconfiguredPrincipal
from ._schemas.protocol.get_task_status_request import GetTaskStatusRequest as GetTaskStatusRequest
from ._schemas.protocol.get_task_status_response import GetTaskStatusResponse as GetTaskStatusResponse
from ._schemas.protocol.list_tasks_request import ListTasksRequest as ListTasksRequest
from ._schemas.protocol.list_tasks_response import ListTasksResponse as ListTasksResponse
from ._schemas.protocol.sync_agent_notification_configs_request import (
    NotificationConfigsItem as SyncAgentNotificationConfigsRequestNotificationConfigsItem,
)
from ._schemas.protocol.sync_agent_notification_configs_request import (
    SyncAgentNotificationConfigsRequest as SyncAgentNotificationConfigsRequest,
)
from ._schemas.protocol.sync_agent_notification_configs_response import (
    Action as SyncAgentNotificationConfigsResponseAction,
)
from ._schemas.protocol.sync_agent_notification_configs_response import (
    SyncAgentNotificationConfigsResponse as SyncAgentNotificationConfigsResponse,
)
from ._schemas.protocol.sync_principal_request import Configuration as SyncPrincipalRequestConfiguration
from ._schemas.protocol.sync_principal_request import (
    NotificationConfigsItem as SyncPrincipalRequestConfigurationNotificationConfigsItem,
)
from ._schemas.protocol.sync_principal_request import SyncPrincipalRequest as SyncPrincipalRequest
from ._schemas.protocol.sync_principal_response import AppliedPrincipalConfiguration as AppliedPrincipalConfiguration
from ._schemas.protocol.sync_principal_response import (
    AppliedPrincipalConfigurationAction as AppliedPrincipalConfigurationAction,
)
from ._schemas.protocol.sync_principal_response import FailedPrincipalSync as FailedPrincipalSync
from ._schemas.protocol.sync_principal_response import Result as SyncPrincipalResponseResult
from ._schemas.protocol.sync_principal_response import SyncPrincipalResponse as SyncPrincipalResponse
from ._schemas.protocol.sync_principal_response import ValidatedPrincipalDryRun as ValidatedPrincipalDryRun
from ._schemas.protocol.sync_principal_response import ValidatedPrincipalDryRunAction as ValidatedPrincipalDryRunAction

__all__ = [
    'AccountChangeFeedSupported',
    'AccountChangeFeedUnsupported',
    'AccountIdentityUpdatesSupported',
    'AccountIdentityUpdatesSupportedSupportedChangesItem',
    'AccountIdentityUpdatesUnsupported',
    'AccountNotificationsSupported',
    'AccountNotificationsSupportedEventTypesItem',
    'AccountNotificationsUnsupported',
    'AppliedPrincipalConfiguration',
    'AppliedPrincipalConfigurationAction',
    'CapabilityChangeNotificationsSupported',
    'CapabilityChangeNotificationsSupportedEventTypesItem',
    'CapabilityChangeNotificationsSupportedRegistrationTask',
    'CapabilityChangeNotificationsUnsupported',
    'CreativeFeaturesItemRange',
    'CreativeFeaturesItemType',
    'CurrentPrincipalConfiguration',
    'ExtensionsSupportedItem',
    'FailedPrincipalRead',
    'FailedPrincipalSync',
    'GetAdCPCapabilitiesRequest',
    'GetAdCPCapabilitiesRequestProtocolsItem',
    'GetAdCPCapabilitiesResponse',
    'GetAdCPCapabilitiesResponseAccount',
    'GetAdCPCapabilitiesResponseAccountChangeFeed',
    'GetAdCPCapabilitiesResponseAccountIdentityUpdates',
    'GetAdCPCapabilitiesResponseAccountNotifications',
    'GetAdCPCapabilitiesResponseAdcp',
    'GetAdCPCapabilitiesResponseAdcpCapabilityChanges',
    'GetAdCPCapabilitiesResponseAdcpCapabilityChangesNotifications',
    'GetAdCPCapabilitiesResponseAdcpGovernanceEnforcement',
    'GetAdCPCapabilitiesResponseAdcpGovernanceEnforcementTasksItem',
    'GetAdCPCapabilitiesResponseAdcpIdempotency',
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
    'GetPrincipalRequest',
    'GetPrincipalResponse',
    'GetPrincipalResponseResult',
    'GetTaskStatusRequest',
    'GetTaskStatusResponse',
    'IdempotencySupported',
    'IdempotencyUnsupported',
    'Language',
    'ListTasksRequest',
    'ListTasksResponse',
    'RecognizedPrincipalWithoutStandingConfiguration',
    'SupportedHashedIdentifiersItem',
    'SyncAgentNotificationConfigsRequest',
    'SyncAgentNotificationConfigsRequestNotificationConfigsItem',
    'SyncAgentNotificationConfigsResponse',
    'SyncAgentNotificationConfigsResponseAction',
    'SyncPrincipalRequest',
    'SyncPrincipalRequestConfiguration',
    'SyncPrincipalRequestConfigurationNotificationConfigsItem',
    'SyncPrincipalResponse',
    'SyncPrincipalResponseResult',
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
    'UnconfiguredPrincipal',
    'ValidatedPrincipalDryRun',
    'ValidatedPrincipalDryRunAction',
]
