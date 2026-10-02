"""Unambiguous names for generated types that share a bare type name.

AdCP schemas name an inline object after the property that holds it, so
several generated modules legitimately define a class called ``QuerySummary``
or ``Creative``. ``adcp.types`` binds one of them per name. Import from here
to name the variant you want:

    from adcp.types.disambiguated import QuerySummaryFromCreativeListCreativesResponse

The name is ``<Type>From<DottedModulePath>`` in CamelCase, derived from the
module that defines the class. Every variant of every shared name is here,
including the one ``adcp.types`` binds.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-02 22:58:03 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.a2ui.si_catalog import (
    Action as ActionFromA2UiSiCatalog,
    ProductCard as ProductCardFromA2UiSiCatalog,
    Type as TypeFromA2UiSiCatalog,
    Variant as VariantFromA2UiSiCatalog,
)
from adcp.types.generated_poc.a2ui.user_action import Action as ActionFromA2UiUserAction
from adcp.types.generated_poc.aao.agent_publishers import Status as StatusFromAaoAgentPublishers
from adcp.types.generated_poc.account.list_account_changes_request import (
    ResourceType as ResourceTypeFromAccountListAccountChangesRequest,
)
from adcp.types.generated_poc.account.list_account_changes_response import (
    Kind as KindFromAccountListAccountChangesResponse,
    ResourceType as ResourceTypeFromAccountListAccountChangesResponse,
    Status as StatusFromAccountListAccountChangesResponse,
)
from adcp.types.generated_poc.account.list_accounts_request import (
    Status as StatusFromAccountListAccountsRequest,
)
from adcp.types.generated_poc.account.sync_accounts_response import (
    Account as AccountFromAccountSyncAccountsResponse,
    CreditLimit as CreditLimitFromAccountSyncAccountsResponse,
    Setup as SetupFromAccountSyncAccountsResponse,
)
from adcp.types.generated_poc.account.sync_governance_request import (
    Account as AccountFromAccountSyncGovernanceRequest,
    Authentication as AuthenticationFromAccountSyncGovernanceRequest,
    GovernanceAgent as GovernanceAgentFromAccountSyncGovernanceRequest,
)
from adcp.types.generated_poc.account.sync_governance_response import (
    Account as AccountFromAccountSyncGovernanceResponse,
    GovernanceAgent as GovernanceAgentFromAccountSyncGovernanceResponse,
    Status as StatusFromAccountSyncGovernanceResponse,
)
from adcp.types.generated_poc.adagents import (
    AuthorizedAgents as AuthorizedAgentsFromAdagents,
    AuthorizedAgents1 as AuthorizedAgents1FromAdagents,
    AuthorizedAgents2 as AuthorizedAgents2FromAdagents,
    AuthorizedAgents3 as AuthorizedAgents3FromAdagents,
    AuthorizedAgents4 as AuthorizedAgents4FromAdagents,
    AuthorizedAgents5 as AuthorizedAgents5FromAdagents,
    Contact as ContactFromAdagents,
    Country as CountryFromAdagents,
    DelegationType as DelegationTypeFromAdagents,
    PropertyFeature as PropertyFeatureFromAdagents,
    Reason as ReasonFromAdagents,
    SignalId as SignalIdFromAdagents,
    SignalTag as SignalTagFromAdagents,
    Tags as TagsFromAdagents,
)
from adcp.types.generated_poc.brand.acquire_rights_request import (
    Country as CountryFromBrandAcquireRightsRequest,
)
from adcp.types.generated_poc.brand.acquire_rights_response import (
    Disclosure as DisclosureFromBrandAcquireRightsResponse,
)
from adcp.types.generated_poc.brand.get_brand_identity_request import (
    Field1 as Field1FromBrandGetBrandIdentityRequest,
)
from adcp.types.generated_poc.brand.get_brand_identity_response import (
    Colors as ColorsFromBrandGetBrandIdentityResponse,
    House as HouseFromBrandGetBrandIdentityResponse,
    Logo as LogoFromBrandGetBrandIdentityResponse,
    Rights as RightsFromBrandGetBrandIdentityResponse,
)
from adcp.types.generated_poc.brand.get_rights_request import (
    Country as CountryFromBrandGetRightsRequest,
)
from adcp.types.generated_poc.brand.get_rights_response import (
    Right as RightFromBrandGetRightsResponse,
)
from adcp.types.generated_poc.brand.rights_terms import (
    Country as CountryFromBrandRightsTerms,
    Exclusivity as ExclusivityFromBrandRightsTerms,
)
from adcp.types.generated_poc.brand.search_brands_request import (
    Country as CountryFromBrandSearchBrandsRequest,
)
from adcp.types.generated_poc.brand.search_brands_response import (
    Country as CountryFromBrandSearchBrandsResponse,
    ExcludedCountry as ExcludedCountryFromBrandSearchBrandsResponse,
    House as HouseFromBrandSearchBrandsResponse,
    Logo as LogoFromBrandSearchBrandsResponse,
    Orientation as OrientationFromBrandSearchBrandsResponse,
    Rights as RightsFromBrandSearchBrandsResponse,
    Variant as VariantFromBrandSearchBrandsResponse,
)
from adcp.types.generated_poc.brand.verify_brand_claim_request import (
    ClaimType as ClaimTypeFromBrandVerifyBrandClaimRequest,
)
from adcp.types.generated_poc.brand.verify_brand_claim_response import (
    ClaimType as ClaimTypeFromBrandVerifyBrandClaimResponse,
)
from adcp.types.generated_poc.brand.verify_brand_claims_request import (
    Country as CountryFromBrandVerifyBrandClaimsRequest,
    Property as PropertyFromBrandVerifyBrandClaimsRequest,
)
from adcp.types.generated_poc.brand.verify_brand_claims_response import (
    ClaimType as ClaimTypeFromBrandVerifyBrandClaimsResponse,
)
from adcp.types.generated_poc.collection.base_collection_source import (
    Identifier as IdentifierFromCollectionBaseCollectionSource,
)
from adcp.types.generated_poc.collection.collection_list_changed_webhook import (
    ChangeSummary as ChangeSummaryFromCollectionCollectionListChangedWebhook,
)
from adcp.types.generated_poc.collection.get_collection_list_request import (
    Pagination as PaginationFromCollectionGetCollectionListRequest,
)
from adcp.types.generated_poc.collection.get_collection_list_response import (
    Collection as CollectionFromCollectionGetCollectionListResponse,
)
from adcp.types.generated_poc.compliance.comply_test_controller_request import (
    Account as AccountFromComplianceComplyTestControllerRequest,
    Kind as KindFromComplianceComplyTestControllerRequest,
    Metric as MetricFromComplianceComplyTestControllerRequest,
    Operation as OperationFromComplianceComplyTestControllerRequest,
    PurgeKind as PurgeKindFromComplianceComplyTestControllerRequest,
    ReachWindow as ReachWindowFromComplianceComplyTestControllerRequest,
    Suggestion as SuggestionFromComplianceComplyTestControllerRequest,
)
from adcp.types.generated_poc.compliance.comply_test_controller_response import (
    Error as ErrorFromComplianceComplyTestControllerResponse,
    Method as MethodFromComplianceComplyTestControllerResponse,
    Suggestion as SuggestionFromComplianceComplyTestControllerResponse,
)
from adcp.types.generated_poc.content_standards.artifact import (
    Artifact as ArtifactFromContentStandardsArtifact,
    Assets as AssetsFromContentStandardsArtifact,
    Metadata as MetadataFromContentStandardsArtifact,
    Provider as ProviderFromContentStandardsArtifact,
    Role as RoleFromContentStandardsArtifact,
)
from adcp.types.generated_poc.content_standards.artifact_webhook_payload import (
    Artifact as ArtifactFromContentStandardsArtifactWebhookPayload,
    Pagination as PaginationFromContentStandardsArtifactWebhookPayload,
)
from adcp.types.generated_poc.content_standards.calibrate_content_response import (
    Feature as FeatureFromContentStandardsCalibrateContentResponse,
)
from adcp.types.generated_poc.content_standards.content_standards import (
    CalibrationExemplars as CalibrationExemplarsFromContentStandardsContentStandards,
    ContentStandards as ContentStandardsFromContentStandardsContentStandards,
)
from adcp.types.generated_poc.content_standards.create_content_standards_request import (
    CalibrationExemplars as CalibrationExemplarsFromContentStandardsCreateContentStandardsRequest,
    Fail as FailFromContentStandardsCreateContentStandardsRequest,
    Pass as PassFromContentStandardsCreateContentStandardsRequest,
    Scope as ScopeFromContentStandardsCreateContentStandardsRequest,
)
from adcp.types.generated_poc.content_standards.get_media_buy_artifacts_request import (
    Pagination as PaginationFromContentStandardsGetMediaBuyArtifactsRequest,
)
from adcp.types.generated_poc.content_standards.get_media_buy_artifacts_response import (
    Artifact as ArtifactFromContentStandardsGetMediaBuyArtifactsResponse,
    BrandContext as BrandContextFromContentStandardsGetMediaBuyArtifactsResponse,
)
from adcp.types.generated_poc.content_standards.update_content_standards_request import (
    CalibrationExemplars as CalibrationExemplarsFromContentStandardsUpdateContentStandardsRequest,
    Fail as FailFromContentStandardsUpdateContentStandardsRequest,
    Pass as PassFromContentStandardsUpdateContentStandardsRequest,
    Scope as ScopeFromContentStandardsUpdateContentStandardsRequest,
)
from adcp.types.generated_poc.content_standards.validate_content_delivery_request import (
    BrandContext as BrandContextFromContentStandardsValidateContentDeliveryRequest,
)
from adcp.types.generated_poc.content_standards.validate_content_delivery_response import (
    Feature as FeatureFromContentStandardsValidateContentDeliveryResponse,
    Result as ResultFromContentStandardsValidateContentDeliveryResponse,
    Summary as SummaryFromContentStandardsValidateContentDeliveryResponse,
)
from adcp.types.generated_poc.core.account import (
    Account as AccountFromCoreAccount,
    CreditLimit as CreditLimitFromCoreAccount,
    Format as FormatFromCoreAccount,
    GovernanceAgent as GovernanceAgentFromCoreAccount,
    Setup as SetupFromCoreAccount,
)
from adcp.types.generated_poc.core.account_change import (
    ChangedPath as ChangedPathFromCoreAccountChange,
    Kind as KindFromCoreAccountChange,
    Origin as OriginFromCoreAccountChange,
    Resource as ResourceFromCoreAccountChange,
    Task as TaskFromCoreAccountChange,
    Type as TypeFromCoreAccountChange,
)
from adcp.types.generated_poc.core.account_change_recorded_webhook import (
    Resource as ResourceFromCoreAccountChangeRecordedWebhook,
)
from adcp.types.generated_poc.core.account_identity_change_preview import (
    Area as AreaFromCoreAccountIdentityChangePreview,
    Effect as EffectFromCoreAccountIdentityChangePreview,
)
from adcp.types.generated_poc.core.account_status_changed_webhook import (
    ReasonCode as ReasonCodeFromCoreAccountStatusChangedWebhook,
    Setup as SetupFromCoreAccountStatusChangedWebhook,
)
from adcp.types.generated_poc.core.account_timezone_capability import (
    Mode as ModeFromCoreAccountTimezoneCapability,
)
from adcp.types.generated_poc.core.agent_notification_config import (
    Authentication as AuthenticationFromCoreAgentNotificationConfig,
)
from adcp.types.generated_poc.core.agent_notification_config_state import (
    Authentication as AuthenticationFromCoreAgentNotificationConfigState,
)
from adcp.types.generated_poc.core.agent_reporting_destination_state import (
    Action as ActionFromCoreAgentReportingDestinationState,
    Setup as SetupFromCoreAgentReportingDestinationState,
)
from adcp.types.generated_poc.core.agent_webhook_challenge import (
    DeliveryAuth as DeliveryAuthFromCoreAgentWebhookChallenge,
    Mode as ModeFromCoreAgentWebhookChallenge,
)
from adcp.types.generated_poc.core.assets.daast_asset import (
    Field1 as Field1FromCoreAssetsDaastAsset,
    Location as LocationFromCoreAssetsDaastAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsDaastAsset,
    UnavailableBehavior as UnavailableBehaviorFromCoreAssetsDaastAsset,
)
from adcp.types.generated_poc.core.assets.daast_tracker_asset import (
    Field1 as Field1FromCoreAssetsDaastTrackerAsset,
    Location as LocationFromCoreAssetsDaastTrackerAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsDaastTrackerAsset,
    Target as TargetFromCoreAssetsDaastTrackerAsset,
)
from adcp.types.generated_poc.core.assets.display_tag_asset import (
    Field1 as Field1FromCoreAssetsDisplayTagAsset,
    Location as LocationFromCoreAssetsDisplayTagAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsDisplayTagAsset,
    UnavailableBehavior as UnavailableBehaviorFromCoreAssetsDisplayTagAsset,
)
from adcp.types.generated_poc.core.assets.html_asset import (
    Accessibility as AccessibilityFromCoreAssetsHtmlAsset,
)
from adcp.types.generated_poc.core.assets.javascript_asset import (
    Accessibility as AccessibilityFromCoreAssetsJavascriptAsset,
)
from adcp.types.generated_poc.core.assets.pixel_tracker_asset import (
    Field1 as Field1FromCoreAssetsPixelTrackerAsset,
    Location as LocationFromCoreAssetsPixelTrackerAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsPixelTrackerAsset,
    Method as MethodFromCoreAssetsPixelTrackerAsset,
)
from adcp.types.generated_poc.core.assets.published_post_asset import (
    Status as StatusFromCoreAssetsPublishedPostAsset,
)
from adcp.types.generated_poc.core.assets.url_asset import (
    Field1 as Field1FromCoreAssetsUrlAsset,
    Location as LocationFromCoreAssetsUrlAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsUrlAsset,
)
from adcp.types.generated_poc.core.assets.vast_asset import (
    Field1 as Field1FromCoreAssetsVastAsset,
    Location as LocationFromCoreAssetsVastAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsVastAsset,
    UnavailableBehavior as UnavailableBehaviorFromCoreAssetsVastAsset,
)
from adcp.types.generated_poc.core.assets.vast_tracker_asset import (
    Field1 as Field1FromCoreAssetsVastTrackerAsset,
    Location as LocationFromCoreAssetsVastTrackerAsset,
    MacroDeclaration as MacroDeclarationFromCoreAssetsVastTrackerAsset,
    Target as TargetFromCoreAssetsVastTrackerAsset,
)
from adcp.types.generated_poc.core.assets.video_asset import (
    ColorSpace as ColorSpaceFromCoreAssetsVideoAsset,
)
from adcp.types.generated_poc.core.assets.zip_asset import (
    Accessibility as AccessibilityFromCoreAssetsZipAsset,
)
from adcp.types.generated_poc.core.attestation_capabilities import (
    AcceptedVerifier as AcceptedVerifierFromCoreAttestationCapabilities,
    Authentication as AuthenticationFromCoreAttestationCapabilities,
)
from adcp.types.generated_poc.core.attestation_evaluation import (
    ActionBinding as ActionBindingFromCoreAttestationEvaluation,
    AttestationEvaluation as AttestationEvaluationFromCoreAttestationEvaluation,
    Outcome as OutcomeFromCoreAttestationEvaluation,
    ReasonCode as ReasonCodeFromCoreAttestationEvaluation,
)
from adcp.types.generated_poc.core.attestation_reference import (
    VerifyAgent as VerifyAgentFromCoreAttestationReference,
)
from adcp.types.generated_poc.core.attribution_window import (
    AttributionWindow as AttributionWindowFromCoreAttributionWindow,
)
from adcp.types.generated_poc.core.audience_activation_method import (
    BuyerAgent as BuyerAgentFromCoreAudienceActivationMethod,
    Direction as DirectionFromCoreAudienceActivationMethod,
)
from adcp.types.generated_poc.core.audience_characteristic import (
    Dimension as DimensionFromCoreAudienceCharacteristic,
    Range as RangeFromCoreAudienceCharacteristic,
    Taxonomy as TaxonomyFromCoreAudienceCharacteristic,
    Value as ValueFromCoreAudienceCharacteristic,
)
from adcp.types.generated_poc.core.audience_evidence import (
    AttestationRef as AttestationRefFromCoreAudienceEvidence,
    AudienceEvidence as AudienceEvidenceFromCoreAudienceEvidence,
    Baseline as BaselineFromCoreAudienceEvidence,
    EvidenceType as EvidenceTypeFromCoreAudienceEvidence,
    Relationship as RelationshipFromCoreAudienceEvidence,
    Subject as SubjectFromCoreAudienceEvidence,
    Unit as UnitFromCoreAudienceEvidence,
)
from adcp.types.generated_poc.core.audience_evidence_requirements import (
    AcceptedEvidenceType as AcceptedEvidenceTypeFromCoreAudienceEvidenceRequirements,
    EvidencePresence as EvidencePresenceFromCoreAudienceEvidenceRequirements,
    MaximumAge as MaximumAgeFromCoreAudienceEvidenceRequirements,
    RequirementMode as RequirementModeFromCoreAudienceEvidenceRequirements,
    Unit as UnitFromCoreAudienceEvidenceRequirements,
)
from adcp.types.generated_poc.core.audience_evidence_selection import (
    ActionBinding as ActionBindingFromCoreAudienceEvidenceSelection,
    AttestationEvaluation as AttestationEvaluationFromCoreAudienceEvidenceSelection,
    DecisionUse as DecisionUseFromCoreAudienceEvidenceSelection,
    Evaluation as EvaluationFromCoreAudienceEvidenceSelection,
)
from adcp.types.generated_poc.core.audience_member import Uid as UidFromCoreAudienceMember
from adcp.types.generated_poc.core.audience_source import (
    AudienceSource as AudienceSourceFromCoreAudienceSource,
)
from adcp.types.generated_poc.core.bidding_policy_capability import (
    Mode as ModeFromCoreBiddingPolicyCapability,
)
from adcp.types.generated_poc.core.brand_key import Country as CountryFromCoreBrandKey
from adcp.types.generated_poc.core.brand_ref import (
    Colors as ColorsFromCoreBrandRef,
    Country as CountryFromCoreBrandRef,
)
from adcp.types.generated_poc.core.brand_response_authorization_result import (
    Reason as ReasonFromCoreBrandResponseAuthorizationResult,
)
from adcp.types.generated_poc.core.budget_allocation import (
    EventSource as EventSourceFromCoreBudgetAllocation,
    Metric as MetricFromCoreBudgetAllocation,
    OptimizationGoal as OptimizationGoalFromCoreBudgetAllocation,
    Target as TargetFromCoreBudgetAllocation,
    TargetFrequency as TargetFrequencyFromCoreBudgetAllocation,
)
from adcp.types.generated_poc.core.budget_range import BudgetRange as BudgetRangeFromCoreBudgetRange
from adcp.types.generated_poc.core.business_entity import (
    Address as AddressFromCoreBusinessEntity,
    Contact as ContactFromCoreBusinessEntity,
    Role as RoleFromCoreBusinessEntity,
)
from adcp.types.generated_poc.core.cancellation_policy import Type as TypeFromCoreCancellationPolicy
from adcp.types.generated_poc.core.canonical_audience_evidence import (
    Baseline as BaselineFromCoreCanonicalAudienceEvidence,
    EvidenceType as EvidenceTypeFromCoreCanonicalAudienceEvidence,
    Relationship as RelationshipFromCoreCanonicalAudienceEvidence,
    Unit as UnitFromCoreCanonicalAudienceEvidence,
)
from adcp.types.generated_poc.core.canonical_audience_evidence_selection import (
    DecisionUse as DecisionUseFromCoreCanonicalAudienceEvidenceSelection,
)
from adcp.types.generated_poc.core.canonical_forecast_point import (
    Metrics as MetricsFromCoreCanonicalForecastPoint,
    Viewability as ViewabilityFromCoreCanonicalForecastPoint,
)
from adcp.types.generated_poc.core.canonical_format_option import (
    SellerPreference as SellerPreferenceFromCoreCanonicalFormatOption,
)
from adcp.types.generated_poc.core.canonical_measurement_terms import (
    BillingMeasurement as BillingMeasurementFromCoreCanonicalMeasurementTerms,
    MakegoodPolicy as MakegoodPolicyFromCoreCanonicalMeasurementTerms,
)
from adcp.types.generated_poc.core.canonical_media_buy_action import (
    Action as ActionFromCoreCanonicalMediaBuyAction,
)
from adcp.types.generated_poc.core.canonical_media_buy_action_fields import (
    Task as TaskFromCoreCanonicalMediaBuyActionFields,
)
from adcp.types.generated_poc.core.canonical_optimization_goal import (
    EventSource as EventSourceFromCoreCanonicalOptimizationGoal,
    Metric as MetricFromCoreCanonicalOptimizationGoal,
    Target as TargetFromCoreCanonicalOptimizationGoal,
    TargetFrequency as TargetFrequencyFromCoreCanonicalOptimizationGoal,
)
from adcp.types.generated_poc.core.canonical_placement import (
    Identifier as IdentifierFromCoreCanonicalPlacement,
    Kind as KindFromCoreCanonicalPlacement,
    Mode as ModeFromCoreCanonicalPlacement,
)
from adcp.types.generated_poc.core.canonical_pricing_option import (
    PricingModel as PricingModelFromCoreCanonicalPricingOption,
)
from adcp.types.generated_poc.core.canonical_product import (
    CatalogMatch as CatalogMatchFromCoreCanonicalProduct,
    MatchedGtin as MatchedGtinFromCoreCanonicalProduct,
    PublisherDomain as PublisherDomainFromCoreCanonicalProduct,
    PublisherProperty as PublisherPropertyFromCoreCanonicalProduct,
)
from adcp.types.generated_poc.core.canonical_projection_ref import (
    AssetSource as AssetSourceFromCoreCanonicalProjectionRef,
)
from adcp.types.generated_poc.core.canonical_proposal import (
    ProposalKind as ProposalKindFromCoreCanonicalProposal,
    TotalBudgetGuidance as TotalBudgetGuidanceFromCoreCanonicalProposal,
)
from adcp.types.generated_poc.core.canonical_reporting_capabilities import (
    DateRangeSupport as DateRangeSupportFromCoreCanonicalReportingCapabilities,
    VendorMetric as VendorMetricFromCoreCanonicalReportingCapabilities,
)
from adcp.types.generated_poc.core.canvas_constraint import (
    Region as RegionFromCoreCanvasConstraint,
    Unit as UnitFromCoreCanvasConstraint,
)
from adcp.types.generated_poc.core.capabilities_changed_webhook import (
    ChangedPath as ChangedPathFromCoreCapabilitiesChangedWebhook,
    Reason as ReasonFromCoreCapabilitiesChangedWebhook,
)
from adcp.types.generated_poc.core.catalog import (
    Catalog as CatalogFromCoreCatalog,
    Category as CategoryFromCoreCatalog,
    Tags as TagsFromCoreCatalog,
    Type as TypeFromCoreCatalog,
)
from adcp.types.generated_poc.core.catalog_field_mapping import (
    Transform as TransformFromCoreCatalogFieldMapping,
)
from adcp.types.generated_poc.core.catalog_item_availability_state import (
    Availability as AvailabilityFromCoreCatalogItemAvailabilityState,
    Status as StatusFromCoreCatalogItemAvailabilityState,
)
from adcp.types.generated_poc.core.catalog_item_availability_update import (
    Action as ActionFromCoreCatalogItemAvailabilityUpdate,
    Reason as ReasonFromCoreCatalogItemAvailabilityUpdate,
)
from adcp.types.generated_poc.core.catalog_item_availability_update_result import (
    Action as ActionFromCoreCatalogItemAvailabilityUpdateResult,
    Availability as AvailabilityFromCoreCatalogItemAvailabilityUpdateResult,
    Status as StatusFromCoreCatalogItemAvailabilityUpdateResult,
)
from adcp.types.generated_poc.core.catchment import (
    Geometry as GeometryFromCoreCatchment,
    Radius as RadiusFromCoreCatchment,
    TravelTime as TravelTimeFromCoreCatchment,
    Type as TypeFromCoreCatchment,
)
from adcp.types.generated_poc.core.collection import Collection as CollectionFromCoreCollection
from adcp.types.generated_poc.core.collection_distribution import (
    Identifier as IdentifierFromCoreCollectionDistribution,
)
from adcp.types.generated_poc.core.committed_metric import (
    Qualifier as QualifierFromCoreCommittedMetric,
)
from adcp.types.generated_poc.core.creative_asset import (
    Assets as AssetsFromCoreCreativeAsset,
    Input as InputFromCoreCreativeAsset,
)
from adcp.types.generated_poc.core.creative_brief import (
    Jurisdiction as JurisdictionFromCoreCreativeBrief,
)
from adcp.types.generated_poc.core.creative_localization import (
    Assets as AssetsFromCoreCreativeLocalization,
    LocaleFallback as LocaleFallbackFromCoreCreativeLocalization,
    Source as SourceFromCoreCreativeLocalization,
    UnmatchedLocaleAction as UnmatchedLocaleActionFromCoreCreativeLocalization,
)
from adcp.types.generated_poc.core.creative_localization_readback import (
    LocaleFallback as LocaleFallbackFromCoreCreativeLocalizationReadback,
    UnmatchedLocaleAction as UnmatchedLocaleActionFromCoreCreativeLocalizationReadback,
)
from adcp.types.generated_poc.core.creative_manifest import Assets as AssetsFromCoreCreativeManifest
from adcp.types.generated_poc.core.creative_operation_format_declaration import (
    SellerPreference as SellerPreferenceFromCoreCreativeOperationFormatDeclaration,
)
from adcp.types.generated_poc.core.creative_policy import (
    AcceptedVerifier as AcceptedVerifierFromCoreCreativePolicy,
)
from adcp.types.generated_poc.core.creative_representation import (
    Source as SourceFromCoreCreativeRepresentation,
)
from adcp.types.generated_poc.core.creative_variant import (
    Artifact as ArtifactFromCoreCreativeVariant,
)
from adcp.types.generated_poc.core.data_provider_signal_selector import (
    SignalId as SignalIdFromCoreDataProviderSignalSelector,
    SignalTag as SignalTagFromCoreDataProviderSignalSelector,
)
from adcp.types.generated_poc.core.delivery_metric_aggregate import (
    Qualifier as QualifierFromCoreDeliveryMetricAggregate,
)
from adcp.types.generated_poc.core.delivery_metrics import (
    DeliveryMetrics as DeliveryMetricsFromCoreDeliveryMetrics,
    EventType as EventTypeFromCoreDeliveryMetrics,
    IdType as IdTypeFromCoreDeliveryMetrics,
    Identifier as IdentifierFromCoreDeliveryMetrics,
    Kind as KindFromCoreDeliveryMetrics,
    ReachWindow as ReachWindowFromCoreDeliveryMetrics,
    Viewability as ViewabilityFromCoreDeliveryMetrics,
)
from adcp.types.generated_poc.core.demographic_reporting_capability import (
    Age as AgeFromCoreDemographicReportingCapability,
    Interval as IntervalFromCoreDemographicReportingCapability,
)
from adcp.types.generated_poc.core.demographic_targeting_capability import (
    Age as AgeFromCoreDemographicTargetingCapability,
    Interval as IntervalFromCoreDemographicTargetingCapability,
)
from adcp.types.generated_poc.core.demographic_targeting_intent import (
    Age as AgeFromCoreDemographicTargetingIntent,
)
from adcp.types.generated_poc.core.demographic_targeting_resolution import (
    Execution as ExecutionFromCoreDemographicTargetingResolution,
)
from adcp.types.generated_poc.core.destination import Destination as DestinationFromCoreDestination
from adcp.types.generated_poc.core.destination_item import (
    Location as LocationFromCoreDestinationItem,
)
from adcp.types.generated_poc.core.downstream_connection_requirement import (
    RequiredForItem as RequiredForItemFromCoreDownstreamConnectionRequirement,
    Scope as ScopeFromCoreDownstreamConnectionRequirement,
    Status as StatusFromCoreDownstreamConnectionRequirement,
)
from adcp.types.generated_poc.core.duration import Unit as UnitFromCoreDuration
from adcp.types.generated_poc.core.error import (
    Error as ErrorFromCoreError,
    Recovery as RecoveryFromCoreError,
    Source as SourceFromCoreError,
)
from adcp.types.generated_poc.core.evaluator_spec import (
    Direction as DirectionFromCoreEvaluatorSpec,
    Exemplars as ExemplarsFromCoreEvaluatorSpec,
)
from adcp.types.generated_poc.core.event_surface import Category as CategoryFromCoreEventSurface
from adcp.types.generated_poc.core.flight_item import (
    Destination as DestinationFromCoreFlightItem,
    Origin as OriginFromCoreFlightItem,
)
from adcp.types.generated_poc.core.forecast_point import (
    CoverageRate as CoverageRateFromCoreForecastPoint,
    Metrics as MetricsFromCoreForecastPoint,
    Viewability as ViewabilityFromCoreForecastPoint,
)
from adcp.types.generated_poc.core.format import (
    Accessibility as AccessibilityFromCoreFormat,
    Assets as AssetsFromCoreFormat,
    Dimensions as DimensionsFromCoreFormat,
    Format as FormatFromCoreFormat,
    SelectionMode as SelectionModeFromCoreFormat,
    SellerPreference as SellerPreferenceFromCoreFormat,
)
from adcp.types.generated_poc.core.geo_place_area import Value as ValueFromCoreGeoPlaceArea
from adcp.types.generated_poc.core.geo_place_catalog_capability import (
    SupportedVersion as SupportedVersionFromCoreGeoPlaceCatalogCapability,
)
from adcp.types.generated_poc.core.geo_place_catalog_entry import (
    Status as StatusFromCoreGeoPlaceCatalogEntry,
)
from adcp.types.generated_poc.core.geo_place_requirement import (
    SystemVersion as SystemVersionFromCoreGeoPlaceRequirement,
)
from adcp.types.generated_poc.core.geo_region_requirement import (
    Countries as CountriesFromCoreGeoRegionRequirement,
    Value as ValueFromCoreGeoRegionRequirement,
)
from adcp.types.generated_poc.core.geo_region_support import (
    Countries as CountriesFromCoreGeoRegionSupport,
    Value as ValueFromCoreGeoRegionSupport,
)
from adcp.types.generated_poc.core.hotel_item import (
    Address as AddressFromCoreHotelItem,
    Location as LocationFromCoreHotelItem,
)
from adcp.types.generated_poc.core.identifier import Identifier as IdentifierFromCoreIdentifier
from adcp.types.generated_poc.core.impairment import (
    ResourceType as ResourceTypeFromCoreImpairment,
    Transition as TransitionFromCoreImpairment,
)
from adcp.types.generated_poc.core.indicator import Indicator as IndicatorFromCoreIndicator
from adcp.types.generated_poc.core.indicators_changed_webhook import (
    ChangeKind as ChangeKindFromCoreIndicatorsChangedWebhook,
)
from adcp.types.generated_poc.core.insertion_order import (
    PaymentTerms as PaymentTermsFromCoreInsertionOrder,
    TotalBudget as TotalBudgetFromCoreInsertionOrder,
)
from adcp.types.generated_poc.core.inventory_list_application import (
    Effect as EffectFromCoreInventoryListApplication,
    Summary as SummaryFromCoreInventoryListApplication,
)
from adcp.types.generated_poc.core.job_item import Period as PeriodFromCoreJobItem
from adcp.types.generated_poc.core.keyword_target import (
    KeywordTarget as KeywordTargetFromCoreKeywordTarget,
)
from adcp.types.generated_poc.core.macro_declaration import (
    MacroDeclaration as MacroDeclarationFromCoreMacroDeclaration,
)
from adcp.types.generated_poc.core.macro_encoding import Kind as KindFromCoreMacroEncoding
from adcp.types.generated_poc.core.macro_resolution_capability import (
    Operation as OperationFromCoreMacroResolutionCapability,
)
from adcp.types.generated_poc.core.macro_resolution_result import (
    Status as StatusFromCoreMacroResolutionResult,
    UnavailableBehavior as UnavailableBehaviorFromCoreMacroResolutionResult,
)
from adcp.types.generated_poc.core.measurement_terms import (
    BillingMeasurement as BillingMeasurementFromCoreMeasurementTerms,
    MakegoodPolicy as MakegoodPolicyFromCoreMeasurementTerms,
)
from adcp.types.generated_poc.core.media_buy import (
    Cancellation as CancellationFromCoreMediaBuy,
    MediaBuy as MediaBuyFromCoreMediaBuy,
)
from adcp.types.generated_poc.core.media_buy_available_action import (
    Task as TaskFromCoreMediaBuyAvailableAction,
)
from adcp.types.generated_poc.core.missing_metric import Qualifier as QualifierFromCoreMissingMetric
from adcp.types.generated_poc.core.notification_config import (
    Authentication as AuthenticationFromCoreNotificationConfig,
    EventType as EventTypeFromCoreNotificationConfig,
    ProductPayloadView as ProductPayloadViewFromCoreNotificationConfig,
)
from adcp.types.generated_poc.core.offering import (
    Country as CountryFromCoreOffering,
    Metro as MetroFromCoreOffering,
    Offering as OfferingFromCoreOffering,
    Region as RegionFromCoreOffering,
)
from adcp.types.generated_poc.core.opportunity_context import (
    Intent as IntentFromCoreOpportunityContext,
    Status as StatusFromCoreOpportunityContext,
)
from adcp.types.generated_poc.core.optimization_goal import (
    EventSource as EventSourceFromCoreOptimizationGoal,
    Metric as MetricFromCoreOptimizationGoal,
    OptimizationGoal as OptimizationGoalFromCoreOptimizationGoal,
    Target as TargetFromCoreOptimizationGoal,
    TargetFrequency as TargetFrequencyFromCoreOptimizationGoal,
)
from adcp.types.generated_poc.core.overlay import Unit as UnitFromCoreOverlay
from adcp.types.generated_poc.core.package import (
    Cancellation as CancellationFromCorePackage,
    Package as PackageFromCorePackage,
)
from adcp.types.generated_poc.core.package_delivery_metric_value import (
    Qualifier as QualifierFromCorePackageDeliveryMetricValue,
)
from adcp.types.generated_poc.core.package_format_snapshot import (
    SellerPreference as SellerPreferenceFromCorePackageFormatSnapshot,
)
from adcp.types.generated_poc.core.performance_feedback import (
    Metric as MetricFromCorePerformanceFeedback,
    PerformanceFeedback as PerformanceFeedbackFromCorePerformanceFeedback,
    Qualifier as QualifierFromCorePerformanceFeedback,
    Status as StatusFromCorePerformanceFeedback,
)
from adcp.types.generated_poc.core.performance_feedback_assertion import (
    Evidence as EvidenceFromCorePerformanceFeedbackAssertion,
)
from adcp.types.generated_poc.core.performance_feedback_metric import (
    Qualifier as QualifierFromCorePerformanceFeedbackMetric,
)
from adcp.types.generated_poc.core.placement import (
    Identifier as IdentifierFromCorePlacement,
    Kind as KindFromCorePlacement,
    Mode as ModeFromCorePlacement,
    Placement as PlacementFromCorePlacement,
)
from adcp.types.generated_poc.core.placement_definition import (
    Identifier as IdentifierFromCorePlacementDefinition,
)
from adcp.types.generated_poc.core.placement_selection import (
    PlacementSelection as PlacementSelectionFromCorePlacementSelection,
)
from adcp.types.generated_poc.core.planned_delivery import Geo as GeoFromCorePlannedDelivery
from adcp.types.generated_poc.core.postal_area import (
    Country as CountryFromCorePostalArea,
    System as SystemFromCorePostalArea,
)
from adcp.types.generated_poc.core.postal_country_system import (
    Country as CountryFromCorePostalCountrySystem,
    System as SystemFromCorePostalCountrySystem,
)
from adcp.types.generated_poc.core.preview_provider import Route as RouteFromCorePreviewProvider
from adcp.types.generated_poc.core.preview_renderer_metadata import (
    RenderingOrigin as RenderingOriginFromCorePreviewRendererMetadata,
)
from adcp.types.generated_poc.core.price import (
    Period as PeriodFromCorePrice,
    Price as PriceFromCorePrice,
)
from adcp.types.generated_poc.core.principal_changed_webhook import (
    Reason as ReasonFromCorePrincipalChangedWebhook,
)
from adcp.types.generated_poc.core.product import (
    CatalogMatch as CatalogMatchFromCoreProduct,
    ConversionTracking as ConversionTrackingFromCoreProduct,
    Country as CountryFromCoreProduct,
    MatchedGtin as MatchedGtinFromCoreProduct,
    ProductCard as ProductCardFromCoreProduct,
    Provider as ProviderFromCoreProduct,
    PublisherDomain as PublisherDomainFromCoreProduct,
    PublisherProperty as PublisherPropertyFromCoreProduct,
    SupportedTarget as SupportedTargetFromCoreProduct,
    TrustedMatch as TrustedMatchFromCoreProduct,
)
from adcp.types.generated_poc.core.product_audience_evidence_requirements import (
    AcceptedEvidenceType as AcceptedEvidenceTypeFromCoreProductAudienceEvidenceRequirements,
    EvidencePresence as EvidencePresenceFromCoreProductAudienceEvidenceRequirements,
    MaximumAge as MaximumAgeFromCoreProductAudienceEvidenceRequirements,
    RequirementMode as RequirementModeFromCoreProductAudienceEvidenceRequirements,
    Unit as UnitFromCoreProductAudienceEvidenceRequirements,
)
from adcp.types.generated_poc.core.product_card_reference_asset import (
    Role as RoleFromCoreProductCardReferenceAsset,
)
from adcp.types.generated_poc.core.product_execution_requirement import (
    RequiredForItem as RequiredForItemFromCoreProductExecutionRequirement,
    Status as StatusFromCoreProductExecutionRequirement,
)
from adcp.types.generated_poc.core.product_filters import (
    BudgetRange as BudgetRangeFromCoreProductFilters,
    BuyerAgent as BuyerAgentFromCoreProductFilters,
    Country as CountryFromCoreProductFilters,
    Direction as DirectionFromCoreProductFilters,
    GeoProximityItem as GeoProximityItemFromCoreProductFilters,
    Geometry as GeometryFromCoreProductFilters,
    Keyword as KeywordFromCoreProductFilters,
    Metro as MetroFromCoreProductFilters,
    PricingCurrency as PricingCurrencyFromCoreProductFilters,
    Provider as ProviderFromCoreProductFilters,
    Radius as RadiusFromCoreProductFilters,
    Region as RegionFromCoreProductFilters,
    RequiredVendorMetric as RequiredVendorMetricFromCoreProductFilters,
    TargetingMode as TargetingModeFromCoreProductFilters,
    TravelTime as TravelTimeFromCoreProductFilters,
    TrustedMatch as TrustedMatchFromCoreProductFilters,
    Type as TypeFromCoreProductFilters,
)
from adcp.types.generated_poc.core.product_format_declaration import (
    SellerPreference as SellerPreferenceFromCoreProductFormatDeclaration,
)
from adcp.types.generated_poc.core.product_offer_filters import (
    Country as CountryFromCoreProductOfferFilters,
    Metro as MetroFromCoreProductOfferFilters,
    PricingCurrency as PricingCurrencyFromCoreProductOfferFilters,
    Provider as ProviderFromCoreProductOfferFilters,
    Region as RegionFromCoreProductOfferFilters,
    RequiredVendorMetric as RequiredVendorMetricFromCoreProductOfferFilters,
    TrustedMatch as TrustedMatchFromCoreProductOfferFilters,
)
from adcp.types.generated_poc.core.property import (
    Identifier as IdentifierFromCoreProperty,
    Property as PropertyFromCoreProperty,
)
from adcp.types.generated_poc.core.proposal import (
    Proposal as ProposalFromCoreProposal,
    TotalBudgetGuidance as TotalBudgetGuidanceFromCoreProposal,
)
from adcp.types.generated_poc.core.provenance import (
    DeclaredBy as DeclaredByFromCoreProvenance,
    Disclosure as DisclosureFromCoreProvenance,
    HumanOversight as HumanOversightFromCoreProvenance,
    Jurisdiction as JurisdictionFromCoreProvenance,
    Provenance as ProvenanceFromCoreProvenance,
    Result as ResultFromCoreProvenance,
    Role as RoleFromCoreProvenance,
    VerifyAgent as VerifyAgentFromCoreProvenance,
)
from adcp.types.generated_poc.core.publisher_property_selector import (
    PublisherDomain as PublisherDomainFromCorePublisherPropertySelector,
)
from adcp.types.generated_poc.core.push_notification_config import (
    Authentication as AuthenticationFromCorePushNotificationConfig,
)
from adcp.types.generated_poc.core.real_estate_item import (
    Address as AddressFromCoreRealEstateItem,
    Area as AreaFromCoreRealEstateItem,
    Location as LocationFromCoreRealEstateItem,
    PropertyType as PropertyTypeFromCoreRealEstateItem,
    Unit as UnitFromCoreRealEstateItem,
)
from adcp.types.generated_poc.core.reference_asset import Role as RoleFromCoreReferenceAsset
from adcp.types.generated_poc.core.reference_renderer import (
    Provenance as ProvenanceFromCoreReferenceRenderer,
)
from adcp.types.generated_poc.core.registry_event import (
    Countries as CountriesFromCoreRegistryEvent,
    Country as CountryFromCoreRegistryEvent,
    DelegationType as DelegationTypeFromCoreRegistryEvent,
    Domain as DomainFromCoreRegistryEvent,
    EntityType as EntityTypeFromCoreRegistryEvent,
    EventType as EventTypeFromCoreRegistryEvent,
    Evidence as EvidenceFromCoreRegistryEvent,
    Payload as PayloadFromCoreRegistryEvent,
    Status as StatusFromCoreRegistryEvent,
    Type as TypeFromCoreRegistryEvent,
)
from adcp.types.generated_poc.core.reporting_adjustment import (
    ReasonCode as ReasonCodeFromCoreReportingAdjustment,
)
from adcp.types.generated_poc.core.reporting_adjustment_receipt import (
    Status as StatusFromCoreReportingAdjustmentReceipt,
)
from adcp.types.generated_poc.core.reporting_capabilities import (
    DateRangeSupport as DateRangeSupportFromCoreReportingCapabilities,
    VendorMetric as VendorMetricFromCoreReportingCapabilities,
)
from adcp.types.generated_poc.core.reporting_consumer_status import (
    Period as PeriodFromCoreReportingConsumerStatus,
)
from adcp.types.generated_poc.core.reporting_coverage import (
    Reason as ReasonFromCoreReportingCoverage,
    Status as StatusFromCoreReportingCoverage,
)
from adcp.types.generated_poc.core.reporting_dataset_share_destination import (
    Provider as ProviderFromCoreReportingDatasetShareDestination,
)
from adcp.types.generated_poc.core.reporting_delivery_config import (
    Scope as ScopeFromCoreReportingDeliveryConfig,
)
from adcp.types.generated_poc.core.reporting_delivery_config_state import (
    Action as ActionFromCoreReportingDeliveryConfigState,
    Setup as SetupFromCoreReportingDeliveryConfigState,
)
from adcp.types.generated_poc.core.reporting_delivery_method import (
    Format as FormatFromCoreReportingDeliveryMethod,
)
from adcp.types.generated_poc.core.reporting_delivery_offering import (
    Format as FormatFromCoreReportingDeliveryOffering,
    Method as MethodFromCoreReportingDeliveryOffering,
    Provider as ProviderFromCoreReportingDeliveryOffering,
)
from adcp.types.generated_poc.core.reporting_file_manifest import (
    Format as FormatFromCoreReportingFileManifest,
    Period as PeriodFromCoreReportingFileManifest,
)
from adcp.types.generated_poc.core.reporting_ledger_changed_webhook import (
    ChangeKind as ChangeKindFromCoreReportingLedgerChangedWebhook,
)
from adcp.types.generated_poc.core.reporting_materialization import (
    Method as MethodFromCoreReportingMaterialization,
    Status as StatusFromCoreReportingMaterialization,
)
from adcp.types.generated_poc.core.reporting_obligation import (
    Period as PeriodFromCoreReportingObligation,
)
from adcp.types.generated_poc.core.reporting_receipt import Status as StatusFromCoreReportingReceipt
from adcp.types.generated_poc.core.reporting_reliability_statistics import (
    Evidence as EvidenceFromCoreReportingReliabilityStatistics,
)
from adcp.types.generated_poc.core.reporting_report_definition import (
    Dimension as DimensionFromCoreReportingReportDefinition,
    Metric as MetricFromCoreReportingReportDefinition,
    Provider as ProviderFromCoreReportingReportDefinition,
    Source as SourceFromCoreReportingReportDefinition,
)
from adcp.types.generated_poc.core.reporting_resource import Kind as KindFromCoreReportingResource
from adcp.types.generated_poc.core.reporting_revision import (
    Period as PeriodFromCoreReportingRevision,
)
from adcp.types.generated_poc.core.reporting_status_issue import (
    Code as CodeFromCoreReportingStatusIssue,
)
from adcp.types.generated_poc.core.reporting_webhook import (
    Authentication as AuthenticationFromCoreReportingWebhook,
    ReportingFrequency as ReportingFrequencyFromCoreReportingWebhook,
)
from adcp.types.generated_poc.core.reporting_write_destination import (
    Provider as ProviderFromCoreReportingWriteDestination,
)
from adcp.types.generated_poc.core.representation_rejection import (
    Code as CodeFromCoreRepresentationRejection,
)
from adcp.types.generated_poc.core.requirements.audio_asset_requirements import (
    Channel as ChannelFromCoreRequirementsAudioAssetRequirements,
    Format as FormatFromCoreRequirementsAudioAssetRequirements,
)
from adcp.types.generated_poc.core.requirements.image_asset_requirements import (
    ColorSpace as ColorSpaceFromCoreRequirementsImageAssetRequirements,
    Format as FormatFromCoreRequirementsImageAssetRequirements,
    PixelRatio as PixelRatioFromCoreRequirementsImageAssetRequirements,
)
from adcp.types.generated_poc.core.requirements.url_asset_requirements import (
    Protocol as ProtocolFromCoreRequirementsUrlAssetRequirements,
    Role as RoleFromCoreRequirementsUrlAssetRequirements,
)
from adcp.types.generated_poc.core.requirements.video_asset_requirements import (
    AudioCodec as AudioCodecFromCoreRequirementsVideoAssetRequirements,
    AudioSampleRate as AudioSampleRateFromCoreRequirementsVideoAssetRequirements,
    Codec as CodecFromCoreRequirementsVideoAssetRequirements,
    Container as ContainerFromCoreRequirementsVideoAssetRequirements,
)
from adcp.types.generated_poc.core.requirements.webhook_asset_requirements import (
    Method as MethodFromCoreRequirementsWebhookAssetRequirements,
)
from adcp.types.generated_poc.core.response_payload_jws_envelope import (
    Task as TaskFromCoreResponsePayloadJwsEnvelope,
)
from adcp.types.generated_poc.core.rights_attestation_evaluation import (
    ActionBinding as ActionBindingFromCoreRightsAttestationEvaluation,
    Evaluation as EvaluationFromCoreRightsAttestationEvaluation,
    Issuer as IssuerFromCoreRightsAttestationEvaluation,
    Subject as SubjectFromCoreRightsAttestationEvaluation,
)
from adcp.types.generated_poc.core.rights_constraint import (
    AttestationRef as AttestationRefFromCoreRightsConstraint,
    Country as CountryFromCoreRightsConstraint,
    Disclosure as DisclosureFromCoreRightsConstraint,
    ExcludedCountry as ExcludedCountryFromCoreRightsConstraint,
    Issuer as IssuerFromCoreRightsConstraint,
    Subject as SubjectFromCoreRightsConstraint,
)
from adcp.types.generated_poc.core.signal_coverage_forecast import (
    Country as CountryFromCoreSignalCoverageForecast,
    CoverageRate as CoverageRateFromCoreSignalCoverageForecast,
    Kind as KindFromCoreSignalCoverageForecast,
    Metrics as MetricsFromCoreSignalCoverageForecast,
    Scope as ScopeFromCoreSignalCoverageForecast,
)
from adcp.types.generated_poc.core.signal_definition import (
    AiActRiskClass as AiActRiskClassFromCoreSignalDefinition,
    Art9Basis as Art9BasisFromCoreSignalDefinition,
    Channel as ChannelFromCoreSignalDefinition,
    Country as CountryFromCoreSignalDefinition,
    DataSource as DataSourceFromCoreSignalDefinition,
    DataSubjectRights as DataSubjectRightsFromCoreSignalDefinition,
    IdType as IdTypeFromCoreSignalDefinition,
    MatchKey as MatchKeyFromCoreSignalDefinition,
    Method as MethodFromCoreSignalDefinition,
    Methodology as MethodologyFromCoreSignalDefinition,
    Modeling as ModelingFromCoreSignalDefinition,
    Onboarder as OnboarderFromCoreSignalDefinition,
    ParentMatchBehavior as ParentMatchBehaviorFromCoreSignalDefinition,
    PreOnboardingPrecisionLevel as PreOnboardingPrecisionLevelFromCoreSignalDefinition,
    Range as RangeFromCoreSignalDefinition,
    RefreshCadence as RefreshCadenceFromCoreSignalDefinition,
    Right as RightFromCoreSignalDefinition,
    SeedSource as SeedSourceFromCoreSignalDefinition,
    Tag as TagFromCoreSignalDefinition,
    Taxonomy as TaxonomyFromCoreSignalDefinition,
    TrainingDataJurisdiction as TrainingDataJurisdictionFromCoreSignalDefinition,
    Type as TypeFromCoreSignalDefinition,
    Value as ValueFromCoreSignalDefinition,
    ValueMapping as ValueMappingFromCoreSignalDefinition,
)
from adcp.types.generated_poc.core.signal_definition_enrichment import (
    AiActRiskClass as AiActRiskClassFromCoreSignalDefinitionEnrichment,
    Art9Basis as Art9BasisFromCoreSignalDefinitionEnrichment,
    Channel as ChannelFromCoreSignalDefinitionEnrichment,
    Country as CountryFromCoreSignalDefinitionEnrichment,
    DataSource as DataSourceFromCoreSignalDefinitionEnrichment,
    DataSubjectRights as DataSubjectRightsFromCoreSignalDefinitionEnrichment,
    MatchKey as MatchKeyFromCoreSignalDefinitionEnrichment,
    Method as MethodFromCoreSignalDefinitionEnrichment,
    Methodology as MethodologyFromCoreSignalDefinitionEnrichment,
    Modeling as ModelingFromCoreSignalDefinitionEnrichment,
    Onboarder as OnboarderFromCoreSignalDefinitionEnrichment,
    ParentMatchBehavior as ParentMatchBehaviorFromCoreSignalDefinitionEnrichment,
    PreOnboardingPrecisionLevel as PreOnboardingPrecisionLevelFromCoreSignalDefinitionEnrichment,
    RefreshCadence as RefreshCadenceFromCoreSignalDefinitionEnrichment,
    Right as RightFromCoreSignalDefinitionEnrichment,
    SeedSource as SeedSourceFromCoreSignalDefinitionEnrichment,
    Taxonomy as TaxonomyFromCoreSignalDefinitionEnrichment,
    TrainingDataJurisdiction as TrainingDataJurisdictionFromCoreSignalDefinitionEnrichment,
    Type as TypeFromCoreSignalDefinitionEnrichment,
    Value as ValueFromCoreSignalDefinitionEnrichment,
    ValueMapping as ValueMappingFromCoreSignalDefinitionEnrichment,
)
from adcp.types.generated_poc.core.signal_id import SignalId as SignalIdFromCoreSignalId
from adcp.types.generated_poc.core.signal_listing import Range as RangeFromCoreSignalListing
from adcp.types.generated_poc.core.signal_modeling_disclosure import (
    Audience as AudienceFromCoreSignalModelingDisclosure,
    Jurisdiction as JurisdictionFromCoreSignalModelingDisclosure,
)
from adcp.types.generated_poc.core.signal_pricing import (
    Metadata as MetadataFromCoreSignalPricing,
    Period as PeriodFromCoreSignalPricing,
)
from adcp.types.generated_poc.core.signal_selection_group_rule import (
    SelectionMode as SelectionModeFromCoreSignalSelectionGroupRule,
    TargetingMode as TargetingModeFromCoreSignalSelectionGroupRule,
)
from adcp.types.generated_poc.core.signal_targeting_rules import (
    SelectionMode as SelectionModeFromCoreSignalTargetingRules,
)
from adcp.types.generated_poc.core.store_item import (
    Address as AddressFromCoreStoreItem,
    Location as LocationFromCoreStoreItem,
)
from adcp.types.generated_poc.core.targeting import (
    AgeRestriction as AgeRestrictionFromCoreTargeting,
    Demographics as DemographicsFromCoreTargeting,
    DevicePlatform as DevicePlatformFromCoreTargeting,
    DeviceType as DeviceTypeFromCoreTargeting,
    GeoProximity as GeoProximityFromCoreTargeting,
    GeoProximityItem as GeoProximityItemFromCoreTargeting,
    Geometry as GeometryFromCoreTargeting,
    KeywordTarget as KeywordTargetFromCoreTargeting,
    PlacementSelection as PlacementSelectionFromCoreTargeting,
    Radius as RadiusFromCoreTargeting,
    TravelTime as TravelTimeFromCoreTargeting,
    Type as TypeFromCoreTargeting,
)
from adcp.types.generated_poc.core.targeting_input import (
    KeywordTarget as KeywordTargetFromCoreTargetingInput,
)
from adcp.types.generated_poc.core.targeting_overlay_requirements import (
    Demographics as DemographicsFromCoreTargetingOverlayRequirements,
    GeoProximity as GeoProximityFromCoreTargetingOverlayRequirements,
)
from adcp.types.generated_poc.core.targeting_overlay_support import (
    Demographics as DemographicsFromCoreTargetingOverlaySupport,
    GeoProximity as GeoProximityFromCoreTargetingOverlaySupport,
    PlacementSelection as PlacementSelectionFromCoreTargetingOverlaySupport,
    SystemVersion as SystemVersionFromCoreTargetingOverlaySupport,
)
from adcp.types.generated_poc.core.tasks_get_response import (
    Details as DetailsFromCoreTasksGetResponse,
    Error as ErrorFromCoreTasksGetResponse,
    HistoryItem as HistoryItemFromCoreTasksGetResponse,
    Progress as ProgressFromCoreTasksGetResponse,
    Type as TypeFromCoreTasksGetResponse,
)
from adcp.types.generated_poc.core.tasks_list_request import (
    Field1 as Field1FromCoreTasksListRequest,
    Filters as FiltersFromCoreTasksListRequest,
    Sort as SortFromCoreTasksListRequest,
)
from adcp.types.generated_poc.core.tasks_list_response import (
    Direction as DirectionFromCoreTasksListResponse,
    Domain as DomainFromCoreTasksListResponse,
    DomainBreakdown as DomainBreakdownFromCoreTasksListResponse,
    QuerySummary as QuerySummaryFromCoreTasksListResponse,
    SortApplied as SortAppliedFromCoreTasksListResponse,
    Task as TaskFromCoreTasksListResponse,
)
from adcp.types.generated_poc.core.transformer import (
    Multiplicity as MultiplicityFromCoreTransformer,
    OutputCapabilityId as OutputCapabilityIdFromCoreTransformer,
    SellerPreference as SellerPreferenceFromCoreTransformer,
    VariantDimension as VariantDimensionFromCoreTransformer,
)
from adcp.types.generated_poc.core.transformer_param import Type as TypeFromCoreTransformerParam
from adcp.types.generated_poc.core.user_match import Uid as UidFromCoreUserMatch
from adcp.types.generated_poc.core.vast_media_file_requirements import (
    Codec as CodecFromCoreVastMediaFileRequirements,
    Container as ContainerFromCoreVastMediaFileRequirements,
)
from adcp.types.generated_poc.core.vehicle_item import (
    Condition as ConditionFromCoreVehicleItem,
    Location as LocationFromCoreVehicleItem,
    Unit as UnitFromCoreVehicleItem,
)
from adcp.types.generated_poc.core.vendor_metric_optimization import (
    VendorMetricOptimization as VendorMetricOptimizationFromCoreVendorMetricOptimization,
)
from adcp.types.generated_poc.core.vendor_metric_optimization_supported_metric import (
    SupportedTarget as SupportedTargetFromCoreVendorMetricOptimizationSupportedMetric,
)
from adcp.types.generated_poc.core.vendor_metric_value import (
    Qualifier as QualifierFromCoreVendorMetricValue,
)
from adcp.types.generated_poc.core.vendor_pricing_option import (
    Metadata as MetadataFromCoreVendorPricingOption,
    Period as PeriodFromCoreVendorPricingOption,
)
from adcp.types.generated_poc.core.verification_token_claims import (
    Role as RoleFromCoreVerificationTokenClaims,
)
from adcp.types.generated_poc.core.warning import Warning as WarningFromCoreWarning
from adcp.types.generated_poc.core.warning_resource import (
    ResourceType as ResourceTypeFromCoreWarningResource,
)
from adcp.types.generated_poc.core.webhook_activity_record import (
    Status as StatusFromCoreWebhookActivityRecord,
)
from adcp.types.generated_poc.core.webhook_challenge import (
    DeliveryAuth as DeliveryAuthFromCoreWebhookChallenge,
    Mode as ModeFromCoreWebhookChallenge,
)
from adcp.types.generated_poc.core.wholesale_feed_event import (
    EntityType as EntityTypeFromCoreWholesaleFeedEvent,
    EventType as EventTypeFromCoreWholesaleFeedEvent,
    Payload as PayloadFromCoreWholesaleFeedEvent,
    Signal as SignalFromCoreWholesaleFeedEvent,
)
from adcp.types.generated_poc.core.wholesale_feed_webhook import (
    CacheScope as CacheScopeFromCoreWholesaleFeedWebhook,
    NotificationType as NotificationTypeFromCoreWholesaleFeedWebhook,
    ProductPayloadView as ProductPayloadViewFromCoreWholesaleFeedWebhook,
)
from adcp.types.generated_poc.creative.audit_observation import (
    Details as DetailsFromCreativeAuditObservation,
    HumanOversight as HumanOversightFromCreativeAuditObservation,
)
from adcp.types.generated_poc.creative.creative_assignment_changed_webhook import (
    ChangeKind as ChangeKindFromCreativeCreativeAssignmentChangedWebhook,
)
from adcp.types.generated_poc.creative.creative_purged_webhook import (
    Initiator as InitiatorFromCreativeCreativePurgedWebhook,
    PurgeKind as PurgeKindFromCreativeCreativePurgedWebhook,
)
from adcp.types.generated_poc.creative.creative_status_changed_webhook import (
    Initiator as InitiatorFromCreativeCreativeStatusChangedWebhook,
    Transition as TransitionFromCreativeCreativeStatusChangedWebhook,
)
from adcp.types.generated_poc.creative.get_creative_delivery_response import (
    Creative as CreativeFromCreativeGetCreativeDeliveryResponse,
    Pagination as PaginationFromCreativeGetCreativeDeliveryResponse,
    ReportingPeriod as ReportingPeriodFromCreativeGetCreativeDeliveryResponse,
)
from adcp.types.generated_poc.creative.list_creative_formats_request import (
    Type as TypeFromCreativeListCreativeFormatsRequest,
)
from adcp.types.generated_poc.creative.list_creative_formats_response import (
    CreativeAgent as CreativeAgentFromCreativeListCreativeFormatsResponse,
)
from adcp.types.generated_poc.creative.list_creatives_request import (
    Field1 as Field1FromCreativeListCreativesRequest,
    Sort as SortFromCreativeListCreativesRequest,
)
from adcp.types.generated_poc.creative.list_creatives_response import (
    Assets as AssetsFromCreativeListCreativesResponse,
    Creative as CreativeFromCreativeListCreativesResponse,
    Indicator as IndicatorFromCreativeListCreativesResponse,
    IndicatorTypesEvaluatedEnum as IndicatorTypesEvaluatedEnumFromCreativeListCreativesResponse,
    QuerySummary as QuerySummaryFromCreativeListCreativesResponse,
    Snapshot as SnapshotFromCreativeListCreativesResponse,
    SortApplied as SortAppliedFromCreativeListCreativesResponse,
)
from adcp.types.generated_poc.creative.list_transformers_request import (
    OutputCapabilityId as OutputCapabilityIdFromCreativeListTransformersRequest,
)
from adcp.types.generated_poc.creative.preview_creative_request import (
    Input as InputFromCreativePreviewCreativeRequest,
)
from adcp.types.generated_poc.creative.preview_creative_response import (
    Input as InputFromCreativePreviewCreativeResponse,
    Input2 as Input2FromCreativePreviewCreativeResponse,
    Preview as PreviewFromCreativePreviewCreativeResponse,
    Preview2 as Preview2FromCreativePreviewCreativeResponse,
    Preview3 as Preview3FromCreativePreviewCreativeResponse,
    Response as ResponseFromCreativePreviewCreativeResponse,
    Result as ResultFromCreativePreviewCreativeResponse,
)
from adcp.types.generated_poc.creative.preview_render import (
    Dimensions as DimensionsFromCreativePreviewRender,
)
from adcp.types.generated_poc.creative.sync_creatives_async_response_input_required import (
    Reason as ReasonFromCreativeSyncCreativesAsyncResponseInputRequired,
)
from adcp.types.generated_poc.creative.sync_creatives_request import (
    Creative as CreativeFromCreativeSyncCreativesRequest,
)
from adcp.types.generated_poc.creative.sync_creatives_response import (
    Creative as CreativeFromCreativeSyncCreativesResponse,
)
from adcp.types.generated_poc.creative.validate_input_result import (
    Kind as KindFromCreativeValidateInputResult,
    Target as TargetFromCreativeValidateInputResult,
    Violation as ViolationFromCreativeValidateInputResult,
    Warning as WarningFromCreativeValidateInputResult,
)
from adcp.types.generated_poc.enums.audience_source import (
    AudienceSource as AudienceSourceFromEnumsAudienceSource,
)
from adcp.types.generated_poc.enums.device_platform import (
    DevicePlatform as DevicePlatformFromEnumsDevicePlatform,
)
from adcp.types.generated_poc.enums.device_type import DeviceType as DeviceTypeFromEnumsDeviceType
from adcp.types.generated_poc.enums.event_type import EventType as EventTypeFromEnumsEventType
from adcp.types.generated_poc.enums.exclusivity import (
    Exclusivity as ExclusivityFromEnumsExclusivity,
)
from adcp.types.generated_poc.enums.notification_type import (
    NotificationType as NotificationTypeFromEnumsNotificationType,
)
from adcp.types.generated_poc.enums.pacing import Pacing as PacingFromEnumsPacing
from adcp.types.generated_poc.enums.payment_terms import (
    PaymentTerms as PaymentTermsFromEnumsPaymentTerms,
)
from adcp.types.generated_poc.enums.pricing_model import (
    PricingModel as PricingModelFromEnumsPricingModel,
)
from adcp.types.generated_poc.enums.property_type import (
    PropertyType as PropertyTypeFromEnumsPropertyType,
)
from adcp.types.generated_poc.enums.proposal_status import (
    ProposalStatus as ProposalStatusFromEnumsProposalStatus,
)
from adcp.types.generated_poc.enums.reporting_frequency import (
    ReportingFrequency as ReportingFrequencyFromEnumsReportingFrequency,
)
from adcp.types.generated_poc.error_details.accessibility_violation import (
    Violation as ViolationFromErrorDetailsAccessibilityViolation,
)
from adcp.types.generated_poc.error_details.billing_not_supported import (
    Scope as ScopeFromErrorDetailsBillingNotSupported,
)
from adcp.types.generated_poc.error_details.execution_requirement_unmet import (
    Reason as ReasonFromErrorDetailsExecutionRequirementUnmet,
)
from adcp.types.generated_poc.error_details.policy_violation import (
    Origin as OriginFromErrorDetailsPolicyViolation,
)
from adcp.types.generated_poc.error_details.rate_limited import (
    Scope as ScopeFromErrorDetailsRateLimited,
)
from adcp.types.generated_poc.error_details.unsupported_refinement_dimension import (
    SupportedDimension as SupportedDimensionFromErrorDetailsUnsupportedRefinementDimension,
)
from adcp.types.generated_poc.error_details.vendor_error_codes import (
    Recovery as RecoveryFromErrorDetailsVendorErrorCodes,
)
from adcp.types.generated_poc.error_details.version_unsupported import (
    SupportedVersion as SupportedVersionFromErrorDetailsVersionUnsupported,
)
from adcp.types.generated_poc.formats.canonical._base import (
    PixelRatio as PixelRatioFromFormatsCanonicalBase,
)
from adcp.types.generated_poc.formats.canonical.audio_daast import (
    DurationMsRangeItem as DurationMsRangeItemFromFormatsCanonicalAudioDaast,
)
from adcp.types.generated_poc.formats.canonical.audio_hosted import (
    AssetSource as AssetSourceFromFormatsCanonicalAudioHosted,
    AudioCodec as AudioCodecFromFormatsCanonicalAudioHosted,
    AudioSampleRate as AudioSampleRateFromFormatsCanonicalAudioHosted,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromFormatsCanonicalAudioHosted,
    DurationMsRange as DurationMsRangeFromFormatsCanonicalAudioHosted,
)
from adcp.types.generated_poc.formats.canonical.audio_vast import (
    DurationMsRangeItem as DurationMsRangeItemFromFormatsCanonicalAudioVast,
)
from adcp.types.generated_poc.formats.canonical.display_tag import (
    Size as SizeFromFormatsCanonicalDisplayTag,
)
from adcp.types.generated_poc.formats.canonical.html5 import (
    MraidVersion as MraidVersionFromFormatsCanonicalHtml5,
    Size as SizeFromFormatsCanonicalHtml5,
)
from adcp.types.generated_poc.formats.canonical.image import (
    AssetSource as AssetSourceFromFormatsCanonicalImage,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromFormatsCanonicalImage,
    ImageFormat as ImageFormatFromFormatsCanonicalImage,
    PixelRatio as PixelRatioFromFormatsCanonicalImage,
    Size as SizeFromFormatsCanonicalImage,
)
from adcp.types.generated_poc.formats.canonical.native_in_feed import (
    AssetSource as AssetSourceFromFormatsCanonicalNativeInFeed,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromFormatsCanonicalNativeInFeed,
    ImageFormat as ImageFormatFromFormatsCanonicalNativeInFeed,
)
from adcp.types.generated_poc.formats.canonical.seller_rendered_stateful_display import (
    Container as ContainerFromFormatsCanonicalSellerRenderedStatefulDisplay,
    Direction as DirectionFromFormatsCanonicalSellerRenderedStatefulDisplay,
    DurationMsRange as DurationMsRangeFromFormatsCanonicalSellerRenderedStatefulDisplay,
    Input as InputFromFormatsCanonicalSellerRenderedStatefulDisplay,
)
from adcp.types.generated_poc.formats.canonical.video_hosted import (
    AssetSource as AssetSourceFromFormatsCanonicalVideoHosted,
    AudioCodec as AudioCodecFromFormatsCanonicalVideoHosted,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromFormatsCanonicalVideoHosted,
    Container as ContainerFromFormatsCanonicalVideoHosted,
    DurationMsRange as DurationMsRangeFromFormatsCanonicalVideoHosted,
    Orientation as OrientationFromFormatsCanonicalVideoHosted,
)
from adcp.types.generated_poc.formats.canonical.video_vast import (
    DurationMsRangeItem as DurationMsRangeItemFromFormatsCanonicalVideoVast,
    Orientation as OrientationFromFormatsCanonicalVideoVast,
)
from adcp.types.generated_poc.governance.check_governance_request import (
    Baseline as BaselineFromGovernanceCheckGovernanceRequest,
    DeliveryMetrics as DeliveryMetricsFromGovernanceCheckGovernanceRequest,
    Pacing as PacingFromGovernanceCheckGovernanceRequest,
    ReportingPeriod as ReportingPeriodFromGovernanceCheckGovernanceRequest,
    RuntimeAttestation as RuntimeAttestationFromGovernanceCheckGovernanceRequest,
    Subject as SubjectFromGovernanceCheckGovernanceRequest,
)
from adcp.types.generated_poc.governance.check_governance_response import (
    ActionBinding as ActionBindingFromGovernanceCheckGovernanceResponse,
    CanonicalPayload as CanonicalPayloadFromGovernanceCheckGovernanceResponse,
    CheckType as CheckTypeFromGovernanceCheckGovernanceResponse,
    Condition as ConditionFromGovernanceCheckGovernanceResponse,
    DeliveryStatement as DeliveryStatementFromGovernanceCheckGovernanceResponse,
    Finding as FindingFromGovernanceCheckGovernanceResponse,
    ReportingPeriod as ReportingPeriodFromGovernanceCheckGovernanceResponse,
)
from adcp.types.generated_poc.governance.get_plan_audit_logs_response import (
    AccountingMode as AccountingModeFromGovernanceGetPlanAuditLogsResponse,
    AdjustmentState as AdjustmentStateFromGovernanceGetPlanAuditLogsResponse,
    AdjustmentType as AdjustmentTypeFromGovernanceGetPlanAuditLogsResponse,
    Amount as AmountFromGovernanceGetPlanAuditLogsResponse,
    Budget as BudgetFromGovernanceGetPlanAuditLogsResponse,
    CanonicalPayload as CanonicalPayloadFromGovernanceGetPlanAuditLogsResponse,
    CheckType as CheckTypeFromGovernanceGetPlanAuditLogsResponse,
    Delivery as DeliveryFromGovernanceGetPlanAuditLogsResponse,
    DeliveryPeriodState as DeliveryPeriodStateFromGovernanceGetPlanAuditLogsResponse,
    DeliveryReconciliationStatus as DeliveryReconciliationStatusFromGovernanceGetPlanAuditLogsResponse,
    DeliveryStatement as DeliveryStatementFromGovernanceGetPlanAuditLogsResponse,
    Evidence as EvidenceFromGovernanceGetPlanAuditLogsResponse,
    EvidenceType as EvidenceTypeFromGovernanceGetPlanAuditLogsResponse,
    Finding as FindingFromGovernanceGetPlanAuditLogsResponse,
    Plan as PlanFromGovernanceGetPlanAuditLogsResponse,
    ReportingPeriod as ReportingPeriodFromGovernanceGetPlanAuditLogsResponse,
    RuntimeAttestation as RuntimeAttestationFromGovernanceGetPlanAuditLogsResponse,
    Source as SourceFromGovernanceGetPlanAuditLogsResponse,
    Status as StatusFromGovernanceGetPlanAuditLogsResponse,
    Summary as SummaryFromGovernanceGetPlanAuditLogsResponse,
    Type as TypeFromGovernanceGetPlanAuditLogsResponse,
)
from adcp.types.generated_poc.governance.policy_entry import (
    Exemplars as ExemplarsFromGovernancePolicyEntry,
    Issuer as IssuerFromGovernancePolicyEntry,
    Source as SourceFromGovernancePolicyEntry,
)
from adcp.types.generated_poc.governance.report_plan_adjustment_request import (
    Action as ActionFromGovernanceReportPlanAdjustmentRequest,
    AdjustmentType as AdjustmentTypeFromGovernanceReportPlanAdjustmentRequest,
    Amount as AmountFromGovernanceReportPlanAdjustmentRequest,
    Evidence as EvidenceFromGovernanceReportPlanAdjustmentRequest,
    EvidenceType as EvidenceTypeFromGovernanceReportPlanAdjustmentRequest,
)
from adcp.types.generated_poc.governance.report_plan_adjustment_response import (
    AccountingMode as AccountingModeFromGovernanceReportPlanAdjustmentResponse,
    AdjustmentState as AdjustmentStateFromGovernanceReportPlanAdjustmentResponse,
    AdjustmentType as AdjustmentTypeFromGovernanceReportPlanAdjustmentResponse,
    Amount as AmountFromGovernanceReportPlanAdjustmentResponse,
    PlanSummary as PlanSummaryFromGovernanceReportPlanAdjustmentResponse,
)
from adcp.types.generated_poc.governance.report_plan_outcome_request import (
    Delivery as DeliveryFromGovernanceReportPlanOutcomeRequest,
    Package as PackageFromGovernanceReportPlanOutcomeRequest,
    ReportingPeriod as ReportingPeriodFromGovernanceReportPlanOutcomeRequest,
    Source as SourceFromGovernanceReportPlanOutcomeRequest,
)
from adcp.types.generated_poc.governance.report_plan_outcome_response import (
    DeliveryPeriodState as DeliveryPeriodStateFromGovernanceReportPlanOutcomeResponse,
    DeliveryReconciliationStatus as DeliveryReconciliationStatusFromGovernanceReportPlanOutcomeResponse,
    Finding as FindingFromGovernanceReportPlanOutcomeResponse,
    PlanSummary as PlanSummaryFromGovernanceReportPlanOutcomeResponse,
)
from adcp.types.generated_poc.governance.reported_outcome_error import (
    Recovery as RecoveryFromGovernanceReportedOutcomeError,
)
from adcp.types.generated_poc.governance.sync_plans_request import (
    AccountingMode as AccountingModeFromGovernanceSyncPlansRequest,
    Budget as BudgetFromGovernanceSyncPlansRequest,
    Flight as FlightFromGovernanceSyncPlansRequest,
    Plan as PlanFromGovernanceSyncPlansRequest,
    Portfolio as PortfolioFromGovernanceSyncPlansRequest,
)
from adcp.types.generated_poc.governance.sync_plans_response import (
    Category as CategoryFromGovernanceSyncPlansResponse,
    Plan as PlanFromGovernanceSyncPlansResponse,
    Source as SourceFromGovernanceSyncPlansResponse,
    Status as StatusFromGovernanceSyncPlansResponse,
)
from adcp.types.generated_poc.manifest import Model as ModelFromManifest
from adcp.types.generated_poc.manifest_schema import (
    Mode as ModeFromManifestSchema,
    Protocol as ProtocolFromManifestSchema,
)
from adcp.types.generated_poc.media_buy.accept_proposal_request import (
    IoAcceptance as IoAcceptanceFromMediaBuyAcceptProposalRequest,
    Opportunity as OpportunityFromMediaBuyAcceptProposalRequest,
    Status as StatusFromMediaBuyAcceptProposalRequest,
    TotalBudget as TotalBudgetFromMediaBuyAcceptProposalRequest,
)
from adcp.types.generated_poc.media_buy.accept_proposal_response import (
    AcceptedProposal as AcceptedProposalFromMediaBuyAcceptProposalResponse,
    Code as CodeFromMediaBuyAcceptProposalResponse,
    ProposalStatus as ProposalStatusFromMediaBuyAcceptProposalResponse,
    PurchaseBinding as PurchaseBindingFromMediaBuyAcceptProposalResponse,
    Warning as WarningFromMediaBuyAcceptProposalResponse,
)
from adcp.types.generated_poc.media_buy.acceptance_context import (
    AdvertiserRole as AdvertiserRoleFromMediaBuyAcceptanceContext,
    Subject as SubjectFromMediaBuyAcceptanceContext,
    SubjectFacet as SubjectFacetFromMediaBuyAcceptanceContext,
)
from adcp.types.generated_poc.media_buy.acceptance_policy_profile import (
    AppliesToEnum as AppliesToEnumFromMediaBuyAcceptancePolicyProfile,
    Coverage as CoverageFromMediaBuyAcceptancePolicyProfile,
    Jurisdiction as JurisdictionFromMediaBuyAcceptancePolicyProfile,
    JurisdictionGroup as JurisdictionGroupFromMediaBuyAcceptancePolicyProfile,
    Scope as ScopeFromMediaBuyAcceptancePolicyProfile,
)
from adcp.types.generated_poc.media_buy.acceptance_policy_rule import (
    AdvertiserRole as AdvertiserRoleFromMediaBuyAcceptancePolicyRule,
    AppliesToEnum as AppliesToEnumFromMediaBuyAcceptancePolicyRule,
    Jurisdiction as JurisdictionFromMediaBuyAcceptancePolicyRule,
    JurisdictionGroup as JurisdictionGroupFromMediaBuyAcceptancePolicyRule,
    PolicyId as PolicyIdFromMediaBuyAcceptancePolicyRule,
    SubjectFacet as SubjectFacetFromMediaBuyAcceptancePolicyRule,
)
from adcp.types.generated_poc.media_buy.build_creative_async_response_input_required import (
    Reason as ReasonFromMediaBuyBuildCreativeAsyncResponseInputRequired,
)
from adcp.types.generated_poc.media_buy.build_creative_request import (
    Dimension as DimensionFromMediaBuyBuildCreativeRequest,
    Mode as ModeFromMediaBuyBuildCreativeRequest,
)
from adcp.types.generated_poc.media_buy.build_creative_response import (
    Creative as CreativeFromMediaBuyBuildCreativeResponse,
    Input as InputFromMediaBuyBuildCreativeResponse,
    Input2 as Input2FromMediaBuyBuildCreativeResponse,
    Preview as PreviewFromMediaBuyBuildCreativeResponse,
    Preview2 as Preview2FromMediaBuyBuildCreativeResponse,
    Preview3 as Preview3FromMediaBuyBuildCreativeResponse,
    Variant as VariantFromMediaBuyBuildCreativeResponse,
)
from adcp.types.generated_poc.media_buy.buy_products_request import (
    Opportunity as OpportunityFromMediaBuyBuyProductsRequest,
    Status as StatusFromMediaBuyBuyProductsRequest,
    TotalBudget as TotalBudgetFromMediaBuyBuyProductsRequest,
)
from adcp.types.generated_poc.media_buy.buy_products_response import (
    AcceptedProposal as AcceptedProposalFromMediaBuyBuyProductsResponse,
    Code as CodeFromMediaBuyBuyProductsResponse,
    ProposalStatus as ProposalStatusFromMediaBuyBuyProductsResponse,
    PurchaseBinding as PurchaseBindingFromMediaBuyBuyProductsResponse,
    Warning as WarningFromMediaBuyBuyProductsResponse,
)
from adcp.types.generated_poc.media_buy.change_term import (
    Condition as ConditionFromMediaBuyChangeTerm,
)
from adcp.types.generated_poc.media_buy.commercial_terms import (
    TotalBudget as TotalBudgetFromMediaBuyCommercialTerms,
)
from adcp.types.generated_poc.media_buy.control_media_buy_request import (
    TotalBudget as TotalBudgetFromMediaBuyControlMediaBuyRequest,
)
from adcp.types.generated_poc.media_buy.control_media_buy_response import (
    Code as CodeFromMediaBuyControlMediaBuyResponse,
    Warning as WarningFromMediaBuyControlMediaBuyResponse,
)
from adcp.types.generated_poc.media_buy.create_media_buy_async_response_input_required import (
    Reason as ReasonFromMediaBuyCreateMediaBuyAsyncResponseInputRequired,
)
from adcp.types.generated_poc.media_buy.create_media_buy_request import (
    Authentication as AuthenticationFromMediaBuyCreateMediaBuyRequest,
    IoAcceptance as IoAcceptanceFromMediaBuyCreateMediaBuyRequest,
    Opportunity as OpportunityFromMediaBuyCreateMediaBuyRequest,
    Status as StatusFromMediaBuyCreateMediaBuyRequest,
    TotalBudget as TotalBudgetFromMediaBuyCreateMediaBuyRequest,
)
from adcp.types.generated_poc.media_buy.decline_proposals_response import (
    Outcome as OutcomeFromMediaBuyDeclineProposalsResponse,
    Results as ResultsFromMediaBuyDeclineProposalsResponse,
)
from adcp.types.generated_poc.media_buy.get_media_buy_delivery_request import (
    AttributionWindow as AttributionWindowFromMediaBuyGetMediaBuyDeliveryRequest,
    Audience as AudienceFromMediaBuyGetMediaBuyDeliveryRequest,
    Creative as CreativeFromMediaBuyGetMediaBuyDeliveryRequest,
    DevicePlatform as DevicePlatformFromMediaBuyGetMediaBuyDeliveryRequest,
    DeviceType as DeviceTypeFromMediaBuyGetMediaBuyDeliveryRequest,
    Format as FormatFromMediaBuyGetMediaBuyDeliveryRequest,
    Geo as GeoFromMediaBuyGetMediaBuyDeliveryRequest,
    Keyword as KeywordFromMediaBuyGetMediaBuyDeliveryRequest,
    Placement as PlacementFromMediaBuyGetMediaBuyDeliveryRequest,
    StatusFilter as StatusFilterFromMediaBuyGetMediaBuyDeliveryRequest,
)
from adcp.types.generated_poc.media_buy.get_media_buy_delivery_response import (
    ByPackageItem as ByPackageItemFromMediaBuyGetMediaBuyDeliveryResponse,
    MediaBuyDelivery as MediaBuyDeliveryFromMediaBuyGetMediaBuyDeliveryResponse,
    NotificationType as NotificationTypeFromMediaBuyGetMediaBuyDeliveryResponse,
    ReportingPeriod as ReportingPeriodFromMediaBuyGetMediaBuyDeliveryResponse,
    Status as StatusFromMediaBuyGetMediaBuyDeliveryResponse,
    Totals as TotalsFromMediaBuyGetMediaBuyDeliveryResponse,
)
from adcp.types.generated_poc.media_buy.get_media_buys_request import (
    StatusFilter as StatusFilterFromMediaBuyGetMediaBuysRequest,
)
from adcp.types.generated_poc.media_buy.get_media_buys_response import (
    AcceptedProposal as AcceptedProposalFromMediaBuyGetMediaBuysResponse,
    Cancellation as CancellationFromMediaBuyGetMediaBuysResponse,
    HistoryItem as HistoryItemFromMediaBuyGetMediaBuysResponse,
    Indicator as IndicatorFromMediaBuyGetMediaBuysResponse,
    IndicatorTypesEvaluatedEnum as IndicatorTypesEvaluatedEnumFromMediaBuyGetMediaBuysResponse,
    MediaBuy as MediaBuyFromMediaBuyGetMediaBuysResponse,
    Package as PackageFromMediaBuyGetMediaBuysResponse,
    ProposalStatus as ProposalStatusFromMediaBuyGetMediaBuysResponse,
    Snapshot as SnapshotFromMediaBuyGetMediaBuysResponse,
)
from adcp.types.generated_poc.media_buy.get_products_async_response_input_required import (
    Reason as ReasonFromMediaBuyGetProductsAsyncResponseInputRequired,
)
from adcp.types.generated_poc.media_buy.get_products_rejected import (
    Suggestion as SuggestionFromMediaBuyGetProductsRejected,
)
from adcp.types.generated_poc.media_buy.get_products_request import (
    Action as ActionFromMediaBuyGetProductsRequest,
    BuyingMode as BuyingModeFromMediaBuyGetProductsRequest,
    Field1 as Field1FromMediaBuyGetProductsRequest,
)
from adcp.types.generated_poc.media_buy.get_products_response import (
    CacheScope as CacheScopeFromMediaBuyGetProductsResponse,
    IncompleteItem as IncompleteItemFromMediaBuyGetProductsResponse,
    Scope as ScopeFromMediaBuyGetProductsResponse,
    Status as StatusFromMediaBuyGetProductsResponse,
    Suggestion as SuggestionFromMediaBuyGetProductsResponse,
)
from adcp.types.generated_poc.media_buy.get_reporting_status_request import (
    Period as PeriodFromMediaBuyGetReportingStatusRequest,
)
from adcp.types.generated_poc.media_buy.get_reporting_status_response import (
    Scope as ScopeFromMediaBuyGetReportingStatusResponse,
    Status as StatusFromMediaBuyGetReportingStatusResponse,
)
from adcp.types.generated_poc.media_buy.list_creative_formats_response import (
    CreativeAgent as CreativeAgentFromMediaBuyListCreativeFormatsResponse,
    Source as SourceFromMediaBuyListCreativeFormatsResponse,
)
from adcp.types.generated_poc.media_buy.list_products_response import (
    CacheScope as CacheScopeFromMediaBuyListProductsResponse,
    IncompleteItem as IncompleteItemFromMediaBuyListProductsResponse,
    Outcome as OutcomeFromMediaBuyListProductsResponse,
    Scope as ScopeFromMediaBuyListProductsResponse,
)
from adcp.types.generated_poc.media_buy.media_buy_commitment_response import (
    AcceptedProposal as AcceptedProposalFromMediaBuyMediaBuyCommitmentResponse,
    Code as CodeFromMediaBuyMediaBuyCommitmentResponse,
    ProposalStatus as ProposalStatusFromMediaBuyMediaBuyCommitmentResponse,
    PurchaseBinding as PurchaseBindingFromMediaBuyMediaBuyCommitmentResponse,
    Warning as WarningFromMediaBuyMediaBuyCommitmentResponse,
)
from adcp.types.generated_poc.media_buy.media_buy_delivery_webhook_result import (
    ByPackageItem as ByPackageItemFromMediaBuyMediaBuyDeliveryWebhookResult,
    MediaBuyDelivery as MediaBuyDeliveryFromMediaBuyMediaBuyDeliveryWebhookResult,
    NotificationType as NotificationTypeFromMediaBuyMediaBuyDeliveryWebhookResult,
    ReportingPeriod as ReportingPeriodFromMediaBuyMediaBuyDeliveryWebhookResult,
    Status as StatusFromMediaBuyMediaBuyDeliveryWebhookResult,
    Totals as TotalsFromMediaBuyMediaBuyDeliveryWebhookResult,
)
from adcp.types.generated_poc.media_buy.package_control import (
    CatalogId as CatalogIdFromMediaBuyPackageControl,
)
from adcp.types.generated_poc.media_buy.package_request import (
    Qualifier as QualifierFromMediaBuyPackageRequest,
)
from adcp.types.generated_poc.media_buy.product_discovery_criteria import (
    PolicyId as PolicyIdFromMediaBuyProductDiscoveryCriteria,
    ProductId as ProductIdFromMediaBuyProductDiscoveryCriteria,
)
from adcp.types.generated_poc.media_buy.product_purchase import (
    Budget as BudgetFromMediaBuyProductPurchase,
    CatalogId as CatalogIdFromMediaBuyProductPurchase,
    Pacing as PacingFromMediaBuyProductPurchase,
    ProductId as ProductIdFromMediaBuyProductPurchase,
)
from adcp.types.generated_poc.media_buy.product_refinement import (
    Action as ActionFromMediaBuyProductRefinement,
)
from adcp.types.generated_poc.media_buy.proposal_refinement import (
    Action as ActionFromMediaBuyProposalRefinement,
    ChangeKind as ChangeKindFromMediaBuyProposalRefinement,
    Flight as FlightFromMediaBuyProposalRefinement,
    ProposalRefinement as ProposalRefinementFromMediaBuyProposalRefinement,
)
from adcp.types.generated_poc.media_buy.refine_proposals_response import (
    Outcome as OutcomeFromMediaBuyRefineProposalsResponse,
    Proposal as ProposalFromMediaBuyRefineProposalsResponse,
    ProposalKind as ProposalKindFromMediaBuyRefineProposalsResponse,
    ProposalStatus as ProposalStatusFromMediaBuyRefineProposalsResponse,
    Results as ResultsFromMediaBuyRefineProposalsResponse,
    Status as StatusFromMediaBuyRefineProposalsResponse,
    Suggestion as SuggestionFromMediaBuyRefineProposalsResponse,
    TotalBudgetGuidance as TotalBudgetGuidanceFromMediaBuyRefineProposalsResponse,
)
from adcp.types.generated_poc.media_buy.request_proposals_request import (
    Opportunity as OpportunityFromMediaBuyRequestProposalsRequest,
    Status as StatusFromMediaBuyRequestProposalsRequest,
)
from adcp.types.generated_poc.media_buy.request_proposals_response import (
    IncompleteItem as IncompleteItemFromMediaBuyRequestProposalsResponse,
    Outcome as OutcomeFromMediaBuyRequestProposalsResponse,
    ProductId as ProductIdFromMediaBuyRequestProposalsResponse,
    Proposal as ProposalFromMediaBuyRequestProposalsResponse,
    ProposalStatus as ProposalStatusFromMediaBuyRequestProposalsResponse,
    Scope as ScopeFromMediaBuyRequestProposalsResponse,
    Status as StatusFromMediaBuyRequestProposalsResponse,
    Suggestion as SuggestionFromMediaBuyRequestProposalsResponse,
)
from adcp.types.generated_poc.media_buy.sync_audiences_request import (
    Audience as AudienceFromMediaBuySyncAudiencesRequest,
    Tag as TagFromMediaBuySyncAudiencesRequest,
)
from adcp.types.generated_poc.media_buy.sync_audiences_response import (
    Audience as AudienceFromMediaBuySyncAudiencesResponse,
    Source as SourceFromMediaBuySyncAudiencesResponse,
)
from adcp.types.generated_poc.media_buy.sync_catalogs_async_response_input_required import (
    Reason as ReasonFromMediaBuySyncCatalogsAsyncResponseInputRequired,
)
from adcp.types.generated_poc.media_buy.sync_catalogs_response import (
    Catalog as CatalogFromMediaBuySyncCatalogsResponse,
)
from adcp.types.generated_poc.media_buy.sync_event_sources_request import (
    EventSource as EventSourceFromMediaBuySyncEventSourcesRequest,
)
from adcp.types.generated_poc.media_buy.sync_event_sources_response import (
    EventSource as EventSourceFromMediaBuySyncEventSourcesResponse,
    Setup as SetupFromMediaBuySyncEventSourcesResponse,
)
from adcp.types.generated_poc.media_buy.sync_reporting_receipts_response import (
    Results as ResultsFromMediaBuySyncReportingReceiptsResponse,
)
from adcp.types.generated_poc.media_buy.sync_reporting_status_response import (
    Results as ResultsFromMediaBuySyncReportingStatusResponse,
)
from adcp.types.generated_poc.media_buy.update_media_buy_async_response_input_required import (
    Reason as ReasonFromMediaBuyUpdateMediaBuyAsyncResponseInputRequired,
)
from adcp.types.generated_poc.media_buy.update_media_buy_request import (
    TotalBudget as TotalBudgetFromMediaBuyUpdateMediaBuyRequest,
)
from adcp.types.generated_poc.pricing_options.cpp_option import (
    Parameters as ParametersFromPricingOptionsCppOption,
)
from adcp.types.generated_poc.pricing_options.cpv_option import (
    Parameters as ParametersFromPricingOptionsCpvOption,
)
from adcp.types.generated_poc.pricing_options.flat_rate_option import (
    Parameters as ParametersFromPricingOptionsFlatRateOption,
)
from adcp.types.generated_poc.pricing_options.time_option import (
    Parameters as ParametersFromPricingOptionsTimeOption,
)
from adcp.types.generated_poc.property.authorization_result import (
    Status as StatusFromPropertyAuthorizationResult,
    Violation as ViolationFromPropertyAuthorizationResult,
)
from adcp.types.generated_poc.property.get_property_list_request import (
    Pagination as PaginationFromPropertyGetPropertyListRequest,
)
from adcp.types.generated_poc.property.property_error import Code as CodeFromPropertyPropertyError
from adcp.types.generated_poc.property.property_feature import (
    PropertyFeature as PropertyFeatureFromPropertyPropertyFeature,
)
from adcp.types.generated_poc.property.property_feature_definition import (
    Coverage as CoverageFromPropertyPropertyFeatureDefinition,
    Range as RangeFromPropertyPropertyFeatureDefinition,
    Type as TypeFromPropertyPropertyFeatureDefinition,
)
from adcp.types.generated_poc.property.property_list_changed_webhook import (
    ChangeSummary as ChangeSummaryFromPropertyPropertyListChangedWebhook,
)
from adcp.types.generated_poc.property.validate_property_delivery_response import (
    Summary as SummaryFromPropertyValidatePropertyDeliveryResponse,
)
from adcp.types.generated_poc.property.validation_result import (
    Feature as FeatureFromPropertyValidationResult,
    Requirement as RequirementFromPropertyValidationResult,
    Status as StatusFromPropertyValidationResult,
)
from adcp.types.generated_poc.protocol.get_adcp_capabilities_request import (
    Protocol as ProtocolFromProtocolGetAdcpCapabilitiesRequest,
)
from adcp.types.generated_poc.protocol.get_adcp_capabilities_response import (
    Account as AccountFromProtocolGetAdcpCapabilitiesResponse,
    AgeRestriction as AgeRestrictionFromProtocolGetAdcpCapabilitiesResponse,
    AttributionWindow as AttributionWindowFromProtocolGetAdcpCapabilitiesResponse,
    AudienceEvidence as AudienceEvidenceFromProtocolGetAdcpCapabilitiesResponse,
    BuyingMode as BuyingModeFromProtocolGetAdcpCapabilitiesResponse,
    ContentStandards as ContentStandardsFromProtocolGetAdcpCapabilitiesResponse,
    ConversionTracking as ConversionTrackingFromProtocolGetAdcpCapabilitiesResponse,
    Creative as CreativeFromProtocolGetAdcpCapabilitiesResponse,
    Demographics as DemographicsFromProtocolGetAdcpCapabilitiesResponse,
    DiscoveryMode as DiscoveryModeFromProtocolGetAdcpCapabilitiesResponse,
    EventType as EventTypeFromProtocolGetAdcpCapabilitiesResponse,
    Execution as ExecutionFromProtocolGetAdcpCapabilitiesResponse,
    Format as FormatFromProtocolGetAdcpCapabilitiesResponse,
    GeoProximity as GeoProximityFromProtocolGetAdcpCapabilitiesResponse,
    Identity as IdentityFromProtocolGetAdcpCapabilitiesResponse,
    MediaBuy as MediaBuyFromProtocolGetAdcpCapabilitiesResponse,
    Metric as MetricFromProtocolGetAdcpCapabilitiesResponse,
    Mode as ModeFromProtocolGetAdcpCapabilitiesResponse,
    MraidVersion as MraidVersionFromProtocolGetAdcpCapabilitiesResponse,
    Multiplicity as MultiplicityFromProtocolGetAdcpCapabilitiesResponse,
    Operation as OperationFromProtocolGetAdcpCapabilitiesResponse,
    PerformanceFeedback as PerformanceFeedbackFromProtocolGetAdcpCapabilitiesResponse,
    Portfolio as PortfolioFromProtocolGetAdcpCapabilitiesResponse,
    Preview as PreviewFromProtocolGetAdcpCapabilitiesResponse,
    PropertyFeature as PropertyFeatureFromProtocolGetAdcpCapabilitiesResponse,
    ProposalRefinement as ProposalRefinementFromProtocolGetAdcpCapabilitiesResponse,
    PublisherDomain as PublisherDomainFromProtocolGetAdcpCapabilitiesResponse,
    Range as RangeFromProtocolGetAdcpCapabilitiesResponse,
    RenderingOrigin as RenderingOriginFromProtocolGetAdcpCapabilitiesResponse,
    RequiredForItem as RequiredForItemFromProtocolGetAdcpCapabilitiesResponse,
    Requirement as RequirementFromProtocolGetAdcpCapabilitiesResponse,
    ResourceType as ResourceTypeFromProtocolGetAdcpCapabilitiesResponse,
    Route as RouteFromProtocolGetAdcpCapabilitiesResponse,
    Signals as SignalsFromProtocolGetAdcpCapabilitiesResponse,
    SupportedDimension as SupportedDimensionFromProtocolGetAdcpCapabilitiesResponse,
    SupportedTarget as SupportedTargetFromProtocolGetAdcpCapabilitiesResponse,
    SupportedVersion as SupportedVersionFromProtocolGetAdcpCapabilitiesResponse,
    Transport as TransportFromProtocolGetAdcpCapabilitiesResponse,
    TrustedMatch as TrustedMatchFromProtocolGetAdcpCapabilitiesResponse,
    Type as TypeFromProtocolGetAdcpCapabilitiesResponse,
    VariantDimension as VariantDimensionFromProtocolGetAdcpCapabilitiesResponse,
    VendorMetricOptimization as VendorMetricOptimizationFromProtocolGetAdcpCapabilitiesResponse,
)
from adcp.types.generated_poc.protocol.get_principal_response import (
    Result as ResultFromProtocolGetPrincipalResponse,
)
from adcp.types.generated_poc.protocol.get_task_status_response import (
    Details as DetailsFromProtocolGetTaskStatusResponse,
    Error as ErrorFromProtocolGetTaskStatusResponse,
    HistoryItem as HistoryItemFromProtocolGetTaskStatusResponse,
    Progress as ProgressFromProtocolGetTaskStatusResponse,
    Type as TypeFromProtocolGetTaskStatusResponse,
)
from adcp.types.generated_poc.protocol.list_tasks_request import (
    Field1 as Field1FromProtocolListTasksRequest,
    Filters as FiltersFromProtocolListTasksRequest,
    Sort as SortFromProtocolListTasksRequest,
)
from adcp.types.generated_poc.protocol.list_tasks_response import (
    Direction as DirectionFromProtocolListTasksResponse,
    Domain as DomainFromProtocolListTasksResponse,
    DomainBreakdown as DomainBreakdownFromProtocolListTasksResponse,
    QuerySummary as QuerySummaryFromProtocolListTasksResponse,
    SortApplied as SortAppliedFromProtocolListTasksResponse,
    Task as TaskFromProtocolListTasksResponse,
)
from adcp.types.generated_poc.protocol.sync_agent_notification_configs_response import (
    Action as ActionFromProtocolSyncAgentNotificationConfigsResponse,
)
from adcp.types.generated_poc.protocol.sync_principal_response import (
    Action as ActionFromProtocolSyncPrincipalResponse,
    Result as ResultFromProtocolSyncPrincipalResponse,
)
from adcp.types.generated_poc.registries.v1_canonical_mapping import (
    Dimensions as DimensionsFromRegistriesV1CanonicalMapping,
    Transform as TransformFromRegistriesV1CanonicalMapping,
)
from adcp.types.generated_poc.signals.activate_signal_request import (
    Action as ActionFromSignalsActivateSignalRequest,
)
from adcp.types.generated_poc.signals.get_signals_request import (
    Country as CountryFromSignalsGetSignalsRequest,
    DiscoveryMode as DiscoveryModeFromSignalsGetSignalsRequest,
    Field1 as Field1FromSignalsGetSignalsRequest,
)
from adcp.types.generated_poc.signals.get_signals_response import (
    AiActRiskClass as AiActRiskClassFromSignalsGetSignalsResponse,
    Art9Basis as Art9BasisFromSignalsGetSignalsResponse,
    CacheScope as CacheScopeFromSignalsGetSignalsResponse,
    Channel as ChannelFromSignalsGetSignalsResponse,
    Country as CountryFromSignalsGetSignalsResponse,
    DataSource as DataSourceFromSignalsGetSignalsResponse,
    DataSubjectRights as DataSubjectRightsFromSignalsGetSignalsResponse,
    IncompleteItem as IncompleteItemFromSignalsGetSignalsResponse,
    MatchKey as MatchKeyFromSignalsGetSignalsResponse,
    Method as MethodFromSignalsGetSignalsResponse,
    Methodology as MethodologyFromSignalsGetSignalsResponse,
    Modeling as ModelingFromSignalsGetSignalsResponse,
    Onboarder as OnboarderFromSignalsGetSignalsResponse,
    ParentMatchBehavior as ParentMatchBehaviorFromSignalsGetSignalsResponse,
    PreOnboardingPrecisionLevel as PreOnboardingPrecisionLevelFromSignalsGetSignalsResponse,
    Range as RangeFromSignalsGetSignalsResponse,
    RefreshCadence as RefreshCadenceFromSignalsGetSignalsResponse,
    Right as RightFromSignalsGetSignalsResponse,
    Scope as ScopeFromSignalsGetSignalsResponse,
    SeedSource as SeedSourceFromSignalsGetSignalsResponse,
    Signal as SignalFromSignalsGetSignalsResponse,
    Taxonomy as TaxonomyFromSignalsGetSignalsResponse,
    TrainingDataJurisdiction as TrainingDataJurisdictionFromSignalsGetSignalsResponse,
    Type as TypeFromSignalsGetSignalsResponse,
    Value as ValueFromSignalsGetSignalsResponse,
    ValueMapping as ValueMappingFromSignalsGetSignalsResponse,
)
from adcp.types.generated_poc.sponsored_intelligence.si_get_offering_response import (
    Offering as OfferingFromSponsoredIntelligenceSiGetOfferingResponse,
)
from adcp.types.generated_poc.sponsored_intelligence.si_initiate_session_response import (
    Response as ResponseFromSponsoredIntelligenceSiInitiateSessionResponse,
)
from adcp.types.generated_poc.sponsored_intelligence.si_send_message_response import (
    Intent as IntentFromSponsoredIntelligenceSiSendMessageResponse,
    Price as PriceFromSponsoredIntelligenceSiSendMessageResponse,
    Response as ResponseFromSponsoredIntelligenceSiSendMessageResponse,
    Type as TypeFromSponsoredIntelligenceSiSendMessageResponse,
)
from adcp.types.generated_poc.sponsored_intelligence.si_sponsored_context import (
    Account as AccountFromSponsoredIntelligenceSiSponsoredContext,
    DeclaredBy as DeclaredByFromSponsoredIntelligenceSiSponsoredContext,
    Jurisdiction as JurisdictionFromSponsoredIntelligenceSiSponsoredContext,
    Role as RoleFromSponsoredIntelligenceSiSponsoredContext,
)
from adcp.types.generated_poc.sponsored_intelligence.si_sponsored_context_receipt import (
    Status as StatusFromSponsoredIntelligenceSiSponsoredContextReceipt,
)
from adcp.types.generated_poc.sponsored_intelligence.si_terminate_session_request import (
    Action as ActionFromSponsoredIntelligenceSiTerminateSessionRequest,
    Reason as ReasonFromSponsoredIntelligenceSiTerminateSessionRequest,
)
from adcp.types.generated_poc.sponsored_intelligence.si_terminate_session_response import (
    Action as ActionFromSponsoredIntelligenceSiTerminateSessionResponse,
)
from adcp.types.generated_poc.sponsored_intelligence.si_ui_element import (
    Type as TypeFromSponsoredIntelligenceSiUiElement,
)
from adcp.types.generated_poc.trusted_match.context_match_request import (
    Geo as GeoFromTrustedMatchContextMatchRequest,
    Keyword as KeywordFromTrustedMatchContextMatchRequest,
    Metro as MetroFromTrustedMatchContextMatchRequest,
    Type as TypeFromTrustedMatchContextMatchRequest,
)
from adcp.types.generated_poc.trusted_match.context_match_response import (
    Signals as SignalsFromTrustedMatchContextMatchResponse,
    TargetingKv as TargetingKvFromTrustedMatchContextMatchResponse,
    TargetingKvs as TargetingKvsFromTrustedMatchContextMatchResponse,
)
from adcp.types.generated_poc.trusted_match.error import Code as CodeFromTrustedMatchError
from adcp.types.generated_poc.trusted_match.identity_match_request import (
    Identity as IdentityFromTrustedMatchIdentityMatchRequest,
)
from adcp.types.generated_poc.trusted_match.identity_match_response import (
    TmpxMacro as TmpxMacroFromTrustedMatchIdentityMatchResponse,
)
from adcp.types.generated_poc.trusted_match.offer_price import (
    Model as ModelFromTrustedMatchOfferPrice,
)
from adcp.types.generated_poc.trusted_match.provider_context_match_response import (
    Signals as SignalsFromTrustedMatchProviderContextMatchResponse,
    TargetingKv as TargetingKvFromTrustedMatchProviderContextMatchResponse,
    TargetingKvs as TargetingKvsFromTrustedMatchProviderContextMatchResponse,
)
from adcp.types.generated_poc.trusted_match.provider_registration import (
    Country as CountryFromTrustedMatchProviderRegistration,
    Status as StatusFromTrustedMatchProviderRegistration,
    TmpxMacro as TmpxMacroFromTrustedMatchProviderRegistration,
)

# Explicit exports
__all__ = [
    "AcceptedEvidenceTypeFromCoreAudienceEvidenceRequirements",
    "AcceptedEvidenceTypeFromCoreProductAudienceEvidenceRequirements",
    "AcceptedProposalFromMediaBuyAcceptProposalResponse",
    "AcceptedProposalFromMediaBuyBuyProductsResponse",
    "AcceptedProposalFromMediaBuyGetMediaBuysResponse",
    "AcceptedProposalFromMediaBuyMediaBuyCommitmentResponse",
    "AcceptedVerifierFromCoreAttestationCapabilities",
    "AcceptedVerifierFromCoreCreativePolicy",
    "AccessibilityFromCoreAssetsHtmlAsset",
    "AccessibilityFromCoreAssetsJavascriptAsset",
    "AccessibilityFromCoreAssetsZipAsset",
    "AccessibilityFromCoreFormat",
    "AccountFromAccountSyncAccountsResponse",
    "AccountFromAccountSyncGovernanceRequest",
    "AccountFromAccountSyncGovernanceResponse",
    "AccountFromComplianceComplyTestControllerRequest",
    "AccountFromCoreAccount",
    "AccountFromProtocolGetAdcpCapabilitiesResponse",
    "AccountFromSponsoredIntelligenceSiSponsoredContext",
    "AccountingModeFromGovernanceGetPlanAuditLogsResponse",
    "AccountingModeFromGovernanceReportPlanAdjustmentResponse",
    "AccountingModeFromGovernanceSyncPlansRequest",
    "ActionBindingFromCoreAttestationEvaluation",
    "ActionBindingFromCoreAudienceEvidenceSelection",
    "ActionBindingFromCoreRightsAttestationEvaluation",
    "ActionBindingFromGovernanceCheckGovernanceResponse",
    "ActionFromA2UiSiCatalog",
    "ActionFromA2UiUserAction",
    "ActionFromCoreAgentReportingDestinationState",
    "ActionFromCoreCanonicalMediaBuyAction",
    "ActionFromCoreCatalogItemAvailabilityUpdate",
    "ActionFromCoreCatalogItemAvailabilityUpdateResult",
    "ActionFromCoreReportingDeliveryConfigState",
    "ActionFromGovernanceReportPlanAdjustmentRequest",
    "ActionFromMediaBuyGetProductsRequest",
    "ActionFromMediaBuyProductRefinement",
    "ActionFromMediaBuyProposalRefinement",
    "ActionFromProtocolSyncAgentNotificationConfigsResponse",
    "ActionFromProtocolSyncPrincipalResponse",
    "ActionFromSignalsActivateSignalRequest",
    "ActionFromSponsoredIntelligenceSiTerminateSessionRequest",
    "ActionFromSponsoredIntelligenceSiTerminateSessionResponse",
    "AddressFromCoreBusinessEntity",
    "AddressFromCoreHotelItem",
    "AddressFromCoreRealEstateItem",
    "AddressFromCoreStoreItem",
    "AdjustmentStateFromGovernanceGetPlanAuditLogsResponse",
    "AdjustmentStateFromGovernanceReportPlanAdjustmentResponse",
    "AdjustmentTypeFromGovernanceGetPlanAuditLogsResponse",
    "AdjustmentTypeFromGovernanceReportPlanAdjustmentRequest",
    "AdjustmentTypeFromGovernanceReportPlanAdjustmentResponse",
    "AdvertiserRoleFromMediaBuyAcceptanceContext",
    "AdvertiserRoleFromMediaBuyAcceptancePolicyRule",
    "AgeFromCoreDemographicReportingCapability",
    "AgeFromCoreDemographicTargetingCapability",
    "AgeFromCoreDemographicTargetingIntent",
    "AgeRestrictionFromCoreTargeting",
    "AgeRestrictionFromProtocolGetAdcpCapabilitiesResponse",
    "AiActRiskClassFromCoreSignalDefinition",
    "AiActRiskClassFromCoreSignalDefinitionEnrichment",
    "AiActRiskClassFromSignalsGetSignalsResponse",
    "AmountFromGovernanceGetPlanAuditLogsResponse",
    "AmountFromGovernanceReportPlanAdjustmentRequest",
    "AmountFromGovernanceReportPlanAdjustmentResponse",
    "AppliesToEnumFromMediaBuyAcceptancePolicyProfile",
    "AppliesToEnumFromMediaBuyAcceptancePolicyRule",
    "AreaFromCoreAccountIdentityChangePreview",
    "AreaFromCoreRealEstateItem",
    "Art9BasisFromCoreSignalDefinition",
    "Art9BasisFromCoreSignalDefinitionEnrichment",
    "Art9BasisFromSignalsGetSignalsResponse",
    "ArtifactFromContentStandardsArtifact",
    "ArtifactFromContentStandardsArtifactWebhookPayload",
    "ArtifactFromContentStandardsGetMediaBuyArtifactsResponse",
    "ArtifactFromCoreCreativeVariant",
    "AssetSourceFromCoreCanonicalProjectionRef",
    "AssetSourceFromFormatsCanonicalAudioHosted",
    "AssetSourceFromFormatsCanonicalImage",
    "AssetSourceFromFormatsCanonicalNativeInFeed",
    "AssetSourceFromFormatsCanonicalVideoHosted",
    "AssetsFromContentStandardsArtifact",
    "AssetsFromCoreCreativeAsset",
    "AssetsFromCoreCreativeLocalization",
    "AssetsFromCoreCreativeManifest",
    "AssetsFromCoreFormat",
    "AssetsFromCreativeListCreativesResponse",
    "AttestationEvaluationFromCoreAttestationEvaluation",
    "AttestationEvaluationFromCoreAudienceEvidenceSelection",
    "AttestationRefFromCoreAudienceEvidence",
    "AttestationRefFromCoreRightsConstraint",
    "AttributionWindowFromCoreAttributionWindow",
    "AttributionWindowFromMediaBuyGetMediaBuyDeliveryRequest",
    "AttributionWindowFromProtocolGetAdcpCapabilitiesResponse",
    "AudienceEvidenceFromCoreAudienceEvidence",
    "AudienceEvidenceFromProtocolGetAdcpCapabilitiesResponse",
    "AudienceFromCoreSignalModelingDisclosure",
    "AudienceFromMediaBuyGetMediaBuyDeliveryRequest",
    "AudienceFromMediaBuySyncAudiencesRequest",
    "AudienceFromMediaBuySyncAudiencesResponse",
    "AudienceSourceFromCoreAudienceSource",
    "AudienceSourceFromEnumsAudienceSource",
    "AudioCodecFromCoreRequirementsVideoAssetRequirements",
    "AudioCodecFromFormatsCanonicalAudioHosted",
    "AudioCodecFromFormatsCanonicalVideoHosted",
    "AudioSampleRateFromCoreRequirementsVideoAssetRequirements",
    "AudioSampleRateFromFormatsCanonicalAudioHosted",
    "AuthenticationFromAccountSyncGovernanceRequest",
    "AuthenticationFromCoreAgentNotificationConfig",
    "AuthenticationFromCoreAgentNotificationConfigState",
    "AuthenticationFromCoreAttestationCapabilities",
    "AuthenticationFromCoreNotificationConfig",
    "AuthenticationFromCorePushNotificationConfig",
    "AuthenticationFromCoreReportingWebhook",
    "AuthenticationFromMediaBuyCreateMediaBuyRequest",
    "AuthorizedAgents1FromAdagents",
    "AuthorizedAgents2FromAdagents",
    "AuthorizedAgents3FromAdagents",
    "AuthorizedAgents4FromAdagents",
    "AuthorizedAgents5FromAdagents",
    "AuthorizedAgentsFromAdagents",
    "AvailabilityFromCoreCatalogItemAvailabilityState",
    "AvailabilityFromCoreCatalogItemAvailabilityUpdateResult",
    "BaselineFromCoreAudienceEvidence",
    "BaselineFromCoreCanonicalAudienceEvidence",
    "BaselineFromGovernanceCheckGovernanceRequest",
    "BillingMeasurementFromCoreCanonicalMeasurementTerms",
    "BillingMeasurementFromCoreMeasurementTerms",
    "BrandContextFromContentStandardsGetMediaBuyArtifactsResponse",
    "BrandContextFromContentStandardsValidateContentDeliveryRequest",
    "BudgetFromGovernanceGetPlanAuditLogsResponse",
    "BudgetFromGovernanceSyncPlansRequest",
    "BudgetFromMediaBuyProductPurchase",
    "BudgetRangeFromCoreBudgetRange",
    "BudgetRangeFromCoreProductFilters",
    "BuyerAgentFromCoreAudienceActivationMethod",
    "BuyerAgentFromCoreProductFilters",
    "BuyerAssetAcceptanceFromFormatsCanonicalAudioHosted",
    "BuyerAssetAcceptanceFromFormatsCanonicalImage",
    "BuyerAssetAcceptanceFromFormatsCanonicalNativeInFeed",
    "BuyerAssetAcceptanceFromFormatsCanonicalVideoHosted",
    "BuyingModeFromMediaBuyGetProductsRequest",
    "BuyingModeFromProtocolGetAdcpCapabilitiesResponse",
    "ByPackageItemFromMediaBuyGetMediaBuyDeliveryResponse",
    "ByPackageItemFromMediaBuyMediaBuyDeliveryWebhookResult",
    "CacheScopeFromCoreWholesaleFeedWebhook",
    "CacheScopeFromMediaBuyGetProductsResponse",
    "CacheScopeFromMediaBuyListProductsResponse",
    "CacheScopeFromSignalsGetSignalsResponse",
    "CalibrationExemplarsFromContentStandardsContentStandards",
    "CalibrationExemplarsFromContentStandardsCreateContentStandardsRequest",
    "CalibrationExemplarsFromContentStandardsUpdateContentStandardsRequest",
    "CancellationFromCoreMediaBuy",
    "CancellationFromCorePackage",
    "CancellationFromMediaBuyGetMediaBuysResponse",
    "CanonicalPayloadFromGovernanceCheckGovernanceResponse",
    "CanonicalPayloadFromGovernanceGetPlanAuditLogsResponse",
    "CatalogFromCoreCatalog",
    "CatalogFromMediaBuySyncCatalogsResponse",
    "CatalogIdFromMediaBuyPackageControl",
    "CatalogIdFromMediaBuyProductPurchase",
    "CatalogMatchFromCoreCanonicalProduct",
    "CatalogMatchFromCoreProduct",
    "CategoryFromCoreCatalog",
    "CategoryFromCoreEventSurface",
    "CategoryFromGovernanceSyncPlansResponse",
    "ChangeKindFromCoreIndicatorsChangedWebhook",
    "ChangeKindFromCoreReportingLedgerChangedWebhook",
    "ChangeKindFromCreativeCreativeAssignmentChangedWebhook",
    "ChangeKindFromMediaBuyProposalRefinement",
    "ChangeSummaryFromCollectionCollectionListChangedWebhook",
    "ChangeSummaryFromPropertyPropertyListChangedWebhook",
    "ChangedPathFromCoreAccountChange",
    "ChangedPathFromCoreCapabilitiesChangedWebhook",
    "ChannelFromCoreRequirementsAudioAssetRequirements",
    "ChannelFromCoreSignalDefinition",
    "ChannelFromCoreSignalDefinitionEnrichment",
    "ChannelFromSignalsGetSignalsResponse",
    "CheckTypeFromGovernanceCheckGovernanceResponse",
    "CheckTypeFromGovernanceGetPlanAuditLogsResponse",
    "ClaimTypeFromBrandVerifyBrandClaimRequest",
    "ClaimTypeFromBrandVerifyBrandClaimResponse",
    "ClaimTypeFromBrandVerifyBrandClaimsResponse",
    "CodeFromCoreReportingStatusIssue",
    "CodeFromCoreRepresentationRejection",
    "CodeFromMediaBuyAcceptProposalResponse",
    "CodeFromMediaBuyBuyProductsResponse",
    "CodeFromMediaBuyControlMediaBuyResponse",
    "CodeFromMediaBuyMediaBuyCommitmentResponse",
    "CodeFromPropertyPropertyError",
    "CodeFromTrustedMatchError",
    "CodecFromCoreRequirementsVideoAssetRequirements",
    "CodecFromCoreVastMediaFileRequirements",
    "CollectionFromCollectionGetCollectionListResponse",
    "CollectionFromCoreCollection",
    "ColorSpaceFromCoreAssetsVideoAsset",
    "ColorSpaceFromCoreRequirementsImageAssetRequirements",
    "ColorsFromBrandGetBrandIdentityResponse",
    "ColorsFromCoreBrandRef",
    "ConditionFromCoreVehicleItem",
    "ConditionFromGovernanceCheckGovernanceResponse",
    "ConditionFromMediaBuyChangeTerm",
    "ContactFromAdagents",
    "ContactFromCoreBusinessEntity",
    "ContainerFromCoreRequirementsVideoAssetRequirements",
    "ContainerFromCoreVastMediaFileRequirements",
    "ContainerFromFormatsCanonicalSellerRenderedStatefulDisplay",
    "ContainerFromFormatsCanonicalVideoHosted",
    "ContentStandardsFromContentStandardsContentStandards",
    "ContentStandardsFromProtocolGetAdcpCapabilitiesResponse",
    "ConversionTrackingFromCoreProduct",
    "ConversionTrackingFromProtocolGetAdcpCapabilitiesResponse",
    "CountriesFromCoreGeoRegionRequirement",
    "CountriesFromCoreGeoRegionSupport",
    "CountriesFromCoreRegistryEvent",
    "CountryFromAdagents",
    "CountryFromBrandAcquireRightsRequest",
    "CountryFromBrandGetRightsRequest",
    "CountryFromBrandRightsTerms",
    "CountryFromBrandSearchBrandsRequest",
    "CountryFromBrandSearchBrandsResponse",
    "CountryFromBrandVerifyBrandClaimsRequest",
    "CountryFromCoreBrandKey",
    "CountryFromCoreBrandRef",
    "CountryFromCoreOffering",
    "CountryFromCorePostalArea",
    "CountryFromCorePostalCountrySystem",
    "CountryFromCoreProduct",
    "CountryFromCoreProductFilters",
    "CountryFromCoreProductOfferFilters",
    "CountryFromCoreRegistryEvent",
    "CountryFromCoreRightsConstraint",
    "CountryFromCoreSignalCoverageForecast",
    "CountryFromCoreSignalDefinition",
    "CountryFromCoreSignalDefinitionEnrichment",
    "CountryFromSignalsGetSignalsRequest",
    "CountryFromSignalsGetSignalsResponse",
    "CountryFromTrustedMatchProviderRegistration",
    "CoverageFromMediaBuyAcceptancePolicyProfile",
    "CoverageFromPropertyPropertyFeatureDefinition",
    "CoverageRateFromCoreForecastPoint",
    "CoverageRateFromCoreSignalCoverageForecast",
    "CreativeAgentFromCreativeListCreativeFormatsResponse",
    "CreativeAgentFromMediaBuyListCreativeFormatsResponse",
    "CreativeFromCreativeGetCreativeDeliveryResponse",
    "CreativeFromCreativeListCreativesResponse",
    "CreativeFromCreativeSyncCreativesRequest",
    "CreativeFromCreativeSyncCreativesResponse",
    "CreativeFromMediaBuyBuildCreativeResponse",
    "CreativeFromMediaBuyGetMediaBuyDeliveryRequest",
    "CreativeFromProtocolGetAdcpCapabilitiesResponse",
    "CreditLimitFromAccountSyncAccountsResponse",
    "CreditLimitFromCoreAccount",
    "DataSourceFromCoreSignalDefinition",
    "DataSourceFromCoreSignalDefinitionEnrichment",
    "DataSourceFromSignalsGetSignalsResponse",
    "DataSubjectRightsFromCoreSignalDefinition",
    "DataSubjectRightsFromCoreSignalDefinitionEnrichment",
    "DataSubjectRightsFromSignalsGetSignalsResponse",
    "DateRangeSupportFromCoreCanonicalReportingCapabilities",
    "DateRangeSupportFromCoreReportingCapabilities",
    "DecisionUseFromCoreAudienceEvidenceSelection",
    "DecisionUseFromCoreCanonicalAudienceEvidenceSelection",
    "DeclaredByFromCoreProvenance",
    "DeclaredByFromSponsoredIntelligenceSiSponsoredContext",
    "DelegationTypeFromAdagents",
    "DelegationTypeFromCoreRegistryEvent",
    "DeliveryAuthFromCoreAgentWebhookChallenge",
    "DeliveryAuthFromCoreWebhookChallenge",
    "DeliveryFromGovernanceGetPlanAuditLogsResponse",
    "DeliveryFromGovernanceReportPlanOutcomeRequest",
    "DeliveryMetricsFromCoreDeliveryMetrics",
    "DeliveryMetricsFromGovernanceCheckGovernanceRequest",
    "DeliveryPeriodStateFromGovernanceGetPlanAuditLogsResponse",
    "DeliveryPeriodStateFromGovernanceReportPlanOutcomeResponse",
    "DeliveryReconciliationStatusFromGovernanceGetPlanAuditLogsResponse",
    "DeliveryReconciliationStatusFromGovernanceReportPlanOutcomeResponse",
    "DeliveryStatementFromGovernanceCheckGovernanceResponse",
    "DeliveryStatementFromGovernanceGetPlanAuditLogsResponse",
    "DemographicsFromCoreTargeting",
    "DemographicsFromCoreTargetingOverlayRequirements",
    "DemographicsFromCoreTargetingOverlaySupport",
    "DemographicsFromProtocolGetAdcpCapabilitiesResponse",
    "DestinationFromCoreDestination",
    "DestinationFromCoreFlightItem",
    "DetailsFromCoreTasksGetResponse",
    "DetailsFromCreativeAuditObservation",
    "DetailsFromProtocolGetTaskStatusResponse",
    "DevicePlatformFromCoreTargeting",
    "DevicePlatformFromEnumsDevicePlatform",
    "DevicePlatformFromMediaBuyGetMediaBuyDeliveryRequest",
    "DeviceTypeFromCoreTargeting",
    "DeviceTypeFromEnumsDeviceType",
    "DeviceTypeFromMediaBuyGetMediaBuyDeliveryRequest",
    "DimensionFromCoreAudienceCharacteristic",
    "DimensionFromCoreReportingReportDefinition",
    "DimensionFromMediaBuyBuildCreativeRequest",
    "DimensionsFromCoreFormat",
    "DimensionsFromCreativePreviewRender",
    "DimensionsFromRegistriesV1CanonicalMapping",
    "DirectionFromCoreAudienceActivationMethod",
    "DirectionFromCoreEvaluatorSpec",
    "DirectionFromCoreProductFilters",
    "DirectionFromCoreTasksListResponse",
    "DirectionFromFormatsCanonicalSellerRenderedStatefulDisplay",
    "DirectionFromProtocolListTasksResponse",
    "DisclosureFromBrandAcquireRightsResponse",
    "DisclosureFromCoreProvenance",
    "DisclosureFromCoreRightsConstraint",
    "DiscoveryModeFromProtocolGetAdcpCapabilitiesResponse",
    "DiscoveryModeFromSignalsGetSignalsRequest",
    "DomainBreakdownFromCoreTasksListResponse",
    "DomainBreakdownFromProtocolListTasksResponse",
    "DomainFromCoreRegistryEvent",
    "DomainFromCoreTasksListResponse",
    "DomainFromProtocolListTasksResponse",
    "DurationMsRangeFromFormatsCanonicalAudioHosted",
    "DurationMsRangeFromFormatsCanonicalSellerRenderedStatefulDisplay",
    "DurationMsRangeFromFormatsCanonicalVideoHosted",
    "DurationMsRangeItemFromFormatsCanonicalAudioDaast",
    "DurationMsRangeItemFromFormatsCanonicalAudioVast",
    "DurationMsRangeItemFromFormatsCanonicalVideoVast",
    "EffectFromCoreAccountIdentityChangePreview",
    "EffectFromCoreInventoryListApplication",
    "EntityTypeFromCoreRegistryEvent",
    "EntityTypeFromCoreWholesaleFeedEvent",
    "ErrorFromComplianceComplyTestControllerResponse",
    "ErrorFromCoreError",
    "ErrorFromCoreTasksGetResponse",
    "ErrorFromProtocolGetTaskStatusResponse",
    "EvaluationFromCoreAudienceEvidenceSelection",
    "EvaluationFromCoreRightsAttestationEvaluation",
    "EventSourceFromCoreBudgetAllocation",
    "EventSourceFromCoreCanonicalOptimizationGoal",
    "EventSourceFromCoreOptimizationGoal",
    "EventSourceFromMediaBuySyncEventSourcesRequest",
    "EventSourceFromMediaBuySyncEventSourcesResponse",
    "EventTypeFromCoreDeliveryMetrics",
    "EventTypeFromCoreNotificationConfig",
    "EventTypeFromCoreRegistryEvent",
    "EventTypeFromCoreWholesaleFeedEvent",
    "EventTypeFromEnumsEventType",
    "EventTypeFromProtocolGetAdcpCapabilitiesResponse",
    "EvidenceFromCorePerformanceFeedbackAssertion",
    "EvidenceFromCoreRegistryEvent",
    "EvidenceFromCoreReportingReliabilityStatistics",
    "EvidenceFromGovernanceGetPlanAuditLogsResponse",
    "EvidenceFromGovernanceReportPlanAdjustmentRequest",
    "EvidencePresenceFromCoreAudienceEvidenceRequirements",
    "EvidencePresenceFromCoreProductAudienceEvidenceRequirements",
    "EvidenceTypeFromCoreAudienceEvidence",
    "EvidenceTypeFromCoreCanonicalAudienceEvidence",
    "EvidenceTypeFromGovernanceGetPlanAuditLogsResponse",
    "EvidenceTypeFromGovernanceReportPlanAdjustmentRequest",
    "ExcludedCountryFromBrandSearchBrandsResponse",
    "ExcludedCountryFromCoreRightsConstraint",
    "ExclusivityFromBrandRightsTerms",
    "ExclusivityFromEnumsExclusivity",
    "ExecutionFromCoreDemographicTargetingResolution",
    "ExecutionFromProtocolGetAdcpCapabilitiesResponse",
    "ExemplarsFromCoreEvaluatorSpec",
    "ExemplarsFromGovernancePolicyEntry",
    "FailFromContentStandardsCreateContentStandardsRequest",
    "FailFromContentStandardsUpdateContentStandardsRequest",
    "FeatureFromContentStandardsCalibrateContentResponse",
    "FeatureFromContentStandardsValidateContentDeliveryResponse",
    "FeatureFromPropertyValidationResult",
    "Field1FromBrandGetBrandIdentityRequest",
    "Field1FromCoreAssetsDaastAsset",
    "Field1FromCoreAssetsDaastTrackerAsset",
    "Field1FromCoreAssetsDisplayTagAsset",
    "Field1FromCoreAssetsPixelTrackerAsset",
    "Field1FromCoreAssetsUrlAsset",
    "Field1FromCoreAssetsVastAsset",
    "Field1FromCoreAssetsVastTrackerAsset",
    "Field1FromCoreTasksListRequest",
    "Field1FromCreativeListCreativesRequest",
    "Field1FromMediaBuyGetProductsRequest",
    "Field1FromProtocolListTasksRequest",
    "Field1FromSignalsGetSignalsRequest",
    "FiltersFromCoreTasksListRequest",
    "FiltersFromProtocolListTasksRequest",
    "FindingFromGovernanceCheckGovernanceResponse",
    "FindingFromGovernanceGetPlanAuditLogsResponse",
    "FindingFromGovernanceReportPlanOutcomeResponse",
    "FlightFromGovernanceSyncPlansRequest",
    "FlightFromMediaBuyProposalRefinement",
    "FormatFromCoreAccount",
    "FormatFromCoreFormat",
    "FormatFromCoreReportingDeliveryMethod",
    "FormatFromCoreReportingDeliveryOffering",
    "FormatFromCoreReportingFileManifest",
    "FormatFromCoreRequirementsAudioAssetRequirements",
    "FormatFromCoreRequirementsImageAssetRequirements",
    "FormatFromMediaBuyGetMediaBuyDeliveryRequest",
    "FormatFromProtocolGetAdcpCapabilitiesResponse",
    "GeoFromCorePlannedDelivery",
    "GeoFromMediaBuyGetMediaBuyDeliveryRequest",
    "GeoFromTrustedMatchContextMatchRequest",
    "GeoProximityFromCoreTargeting",
    "GeoProximityFromCoreTargetingOverlayRequirements",
    "GeoProximityFromCoreTargetingOverlaySupport",
    "GeoProximityFromProtocolGetAdcpCapabilitiesResponse",
    "GeoProximityItemFromCoreProductFilters",
    "GeoProximityItemFromCoreTargeting",
    "GeometryFromCoreCatchment",
    "GeometryFromCoreProductFilters",
    "GeometryFromCoreTargeting",
    "GovernanceAgentFromAccountSyncGovernanceRequest",
    "GovernanceAgentFromAccountSyncGovernanceResponse",
    "GovernanceAgentFromCoreAccount",
    "HistoryItemFromCoreTasksGetResponse",
    "HistoryItemFromMediaBuyGetMediaBuysResponse",
    "HistoryItemFromProtocolGetTaskStatusResponse",
    "HouseFromBrandGetBrandIdentityResponse",
    "HouseFromBrandSearchBrandsResponse",
    "HumanOversightFromCoreProvenance",
    "HumanOversightFromCreativeAuditObservation",
    "IdTypeFromCoreDeliveryMetrics",
    "IdTypeFromCoreSignalDefinition",
    "IdentifierFromCollectionBaseCollectionSource",
    "IdentifierFromCoreCanonicalPlacement",
    "IdentifierFromCoreCollectionDistribution",
    "IdentifierFromCoreDeliveryMetrics",
    "IdentifierFromCoreIdentifier",
    "IdentifierFromCorePlacement",
    "IdentifierFromCorePlacementDefinition",
    "IdentifierFromCoreProperty",
    "IdentityFromProtocolGetAdcpCapabilitiesResponse",
    "IdentityFromTrustedMatchIdentityMatchRequest",
    "ImageFormatFromFormatsCanonicalImage",
    "ImageFormatFromFormatsCanonicalNativeInFeed",
    "IncompleteItemFromMediaBuyGetProductsResponse",
    "IncompleteItemFromMediaBuyListProductsResponse",
    "IncompleteItemFromMediaBuyRequestProposalsResponse",
    "IncompleteItemFromSignalsGetSignalsResponse",
    "IndicatorFromCoreIndicator",
    "IndicatorFromCreativeListCreativesResponse",
    "IndicatorFromMediaBuyGetMediaBuysResponse",
    "IndicatorTypesEvaluatedEnumFromCreativeListCreativesResponse",
    "IndicatorTypesEvaluatedEnumFromMediaBuyGetMediaBuysResponse",
    "InitiatorFromCreativeCreativePurgedWebhook",
    "InitiatorFromCreativeCreativeStatusChangedWebhook",
    "Input2FromCreativePreviewCreativeResponse",
    "Input2FromMediaBuyBuildCreativeResponse",
    "InputFromCoreCreativeAsset",
    "InputFromCreativePreviewCreativeRequest",
    "InputFromCreativePreviewCreativeResponse",
    "InputFromFormatsCanonicalSellerRenderedStatefulDisplay",
    "InputFromMediaBuyBuildCreativeResponse",
    "IntentFromCoreOpportunityContext",
    "IntentFromSponsoredIntelligenceSiSendMessageResponse",
    "IntervalFromCoreDemographicReportingCapability",
    "IntervalFromCoreDemographicTargetingCapability",
    "IoAcceptanceFromMediaBuyAcceptProposalRequest",
    "IoAcceptanceFromMediaBuyCreateMediaBuyRequest",
    "IssuerFromCoreRightsAttestationEvaluation",
    "IssuerFromCoreRightsConstraint",
    "IssuerFromGovernancePolicyEntry",
    "JurisdictionFromCoreCreativeBrief",
    "JurisdictionFromCoreProvenance",
    "JurisdictionFromCoreSignalModelingDisclosure",
    "JurisdictionFromMediaBuyAcceptancePolicyProfile",
    "JurisdictionFromMediaBuyAcceptancePolicyRule",
    "JurisdictionFromSponsoredIntelligenceSiSponsoredContext",
    "JurisdictionGroupFromMediaBuyAcceptancePolicyProfile",
    "JurisdictionGroupFromMediaBuyAcceptancePolicyRule",
    "KeywordFromCoreProductFilters",
    "KeywordFromMediaBuyGetMediaBuyDeliveryRequest",
    "KeywordFromTrustedMatchContextMatchRequest",
    "KeywordTargetFromCoreKeywordTarget",
    "KeywordTargetFromCoreTargeting",
    "KeywordTargetFromCoreTargetingInput",
    "KindFromAccountListAccountChangesResponse",
    "KindFromComplianceComplyTestControllerRequest",
    "KindFromCoreAccountChange",
    "KindFromCoreCanonicalPlacement",
    "KindFromCoreDeliveryMetrics",
    "KindFromCoreMacroEncoding",
    "KindFromCorePlacement",
    "KindFromCoreReportingResource",
    "KindFromCoreSignalCoverageForecast",
    "KindFromCreativeValidateInputResult",
    "LocaleFallbackFromCoreCreativeLocalization",
    "LocaleFallbackFromCoreCreativeLocalizationReadback",
    "LocationFromCoreAssetsDaastAsset",
    "LocationFromCoreAssetsDaastTrackerAsset",
    "LocationFromCoreAssetsDisplayTagAsset",
    "LocationFromCoreAssetsPixelTrackerAsset",
    "LocationFromCoreAssetsUrlAsset",
    "LocationFromCoreAssetsVastAsset",
    "LocationFromCoreAssetsVastTrackerAsset",
    "LocationFromCoreDestinationItem",
    "LocationFromCoreHotelItem",
    "LocationFromCoreRealEstateItem",
    "LocationFromCoreStoreItem",
    "LocationFromCoreVehicleItem",
    "LogoFromBrandGetBrandIdentityResponse",
    "LogoFromBrandSearchBrandsResponse",
    "MacroDeclarationFromCoreAssetsDaastAsset",
    "MacroDeclarationFromCoreAssetsDaastTrackerAsset",
    "MacroDeclarationFromCoreAssetsDisplayTagAsset",
    "MacroDeclarationFromCoreAssetsPixelTrackerAsset",
    "MacroDeclarationFromCoreAssetsUrlAsset",
    "MacroDeclarationFromCoreAssetsVastAsset",
    "MacroDeclarationFromCoreAssetsVastTrackerAsset",
    "MacroDeclarationFromCoreMacroDeclaration",
    "MakegoodPolicyFromCoreCanonicalMeasurementTerms",
    "MakegoodPolicyFromCoreMeasurementTerms",
    "MatchKeyFromCoreSignalDefinition",
    "MatchKeyFromCoreSignalDefinitionEnrichment",
    "MatchKeyFromSignalsGetSignalsResponse",
    "MatchedGtinFromCoreCanonicalProduct",
    "MatchedGtinFromCoreProduct",
    "MaximumAgeFromCoreAudienceEvidenceRequirements",
    "MaximumAgeFromCoreProductAudienceEvidenceRequirements",
    "MediaBuyDeliveryFromMediaBuyGetMediaBuyDeliveryResponse",
    "MediaBuyDeliveryFromMediaBuyMediaBuyDeliveryWebhookResult",
    "MediaBuyFromCoreMediaBuy",
    "MediaBuyFromMediaBuyGetMediaBuysResponse",
    "MediaBuyFromProtocolGetAdcpCapabilitiesResponse",
    "MetadataFromContentStandardsArtifact",
    "MetadataFromCoreSignalPricing",
    "MetadataFromCoreVendorPricingOption",
    "MethodFromComplianceComplyTestControllerResponse",
    "MethodFromCoreAssetsPixelTrackerAsset",
    "MethodFromCoreReportingDeliveryOffering",
    "MethodFromCoreReportingMaterialization",
    "MethodFromCoreRequirementsWebhookAssetRequirements",
    "MethodFromCoreSignalDefinition",
    "MethodFromCoreSignalDefinitionEnrichment",
    "MethodFromSignalsGetSignalsResponse",
    "MethodologyFromCoreSignalDefinition",
    "MethodologyFromCoreSignalDefinitionEnrichment",
    "MethodologyFromSignalsGetSignalsResponse",
    "MetricFromComplianceComplyTestControllerRequest",
    "MetricFromCoreBudgetAllocation",
    "MetricFromCoreCanonicalOptimizationGoal",
    "MetricFromCoreOptimizationGoal",
    "MetricFromCorePerformanceFeedback",
    "MetricFromCoreReportingReportDefinition",
    "MetricFromProtocolGetAdcpCapabilitiesResponse",
    "MetricsFromCoreCanonicalForecastPoint",
    "MetricsFromCoreForecastPoint",
    "MetricsFromCoreSignalCoverageForecast",
    "MetroFromCoreOffering",
    "MetroFromCoreProductFilters",
    "MetroFromCoreProductOfferFilters",
    "MetroFromTrustedMatchContextMatchRequest",
    "ModeFromCoreAccountTimezoneCapability",
    "ModeFromCoreAgentWebhookChallenge",
    "ModeFromCoreBiddingPolicyCapability",
    "ModeFromCoreCanonicalPlacement",
    "ModeFromCorePlacement",
    "ModeFromCoreWebhookChallenge",
    "ModeFromManifestSchema",
    "ModeFromMediaBuyBuildCreativeRequest",
    "ModeFromProtocolGetAdcpCapabilitiesResponse",
    "ModelFromManifest",
    "ModelFromTrustedMatchOfferPrice",
    "ModelingFromCoreSignalDefinition",
    "ModelingFromCoreSignalDefinitionEnrichment",
    "ModelingFromSignalsGetSignalsResponse",
    "MraidVersionFromFormatsCanonicalHtml5",
    "MraidVersionFromProtocolGetAdcpCapabilitiesResponse",
    "MultiplicityFromCoreTransformer",
    "MultiplicityFromProtocolGetAdcpCapabilitiesResponse",
    "NotificationTypeFromCoreWholesaleFeedWebhook",
    "NotificationTypeFromEnumsNotificationType",
    "NotificationTypeFromMediaBuyGetMediaBuyDeliveryResponse",
    "NotificationTypeFromMediaBuyMediaBuyDeliveryWebhookResult",
    "OfferingFromCoreOffering",
    "OfferingFromSponsoredIntelligenceSiGetOfferingResponse",
    "OnboarderFromCoreSignalDefinition",
    "OnboarderFromCoreSignalDefinitionEnrichment",
    "OnboarderFromSignalsGetSignalsResponse",
    "OperationFromComplianceComplyTestControllerRequest",
    "OperationFromCoreMacroResolutionCapability",
    "OperationFromProtocolGetAdcpCapabilitiesResponse",
    "OpportunityFromMediaBuyAcceptProposalRequest",
    "OpportunityFromMediaBuyBuyProductsRequest",
    "OpportunityFromMediaBuyCreateMediaBuyRequest",
    "OpportunityFromMediaBuyRequestProposalsRequest",
    "OptimizationGoalFromCoreBudgetAllocation",
    "OptimizationGoalFromCoreOptimizationGoal",
    "OrientationFromBrandSearchBrandsResponse",
    "OrientationFromFormatsCanonicalVideoHosted",
    "OrientationFromFormatsCanonicalVideoVast",
    "OriginFromCoreAccountChange",
    "OriginFromCoreFlightItem",
    "OriginFromErrorDetailsPolicyViolation",
    "OutcomeFromCoreAttestationEvaluation",
    "OutcomeFromMediaBuyDeclineProposalsResponse",
    "OutcomeFromMediaBuyListProductsResponse",
    "OutcomeFromMediaBuyRefineProposalsResponse",
    "OutcomeFromMediaBuyRequestProposalsResponse",
    "OutputCapabilityIdFromCoreTransformer",
    "OutputCapabilityIdFromCreativeListTransformersRequest",
    "PacingFromEnumsPacing",
    "PacingFromGovernanceCheckGovernanceRequest",
    "PacingFromMediaBuyProductPurchase",
    "PackageFromCorePackage",
    "PackageFromGovernanceReportPlanOutcomeRequest",
    "PackageFromMediaBuyGetMediaBuysResponse",
    "PaginationFromCollectionGetCollectionListRequest",
    "PaginationFromContentStandardsArtifactWebhookPayload",
    "PaginationFromContentStandardsGetMediaBuyArtifactsRequest",
    "PaginationFromCreativeGetCreativeDeliveryResponse",
    "PaginationFromPropertyGetPropertyListRequest",
    "ParametersFromPricingOptionsCppOption",
    "ParametersFromPricingOptionsCpvOption",
    "ParametersFromPricingOptionsFlatRateOption",
    "ParametersFromPricingOptionsTimeOption",
    "ParentMatchBehaviorFromCoreSignalDefinition",
    "ParentMatchBehaviorFromCoreSignalDefinitionEnrichment",
    "ParentMatchBehaviorFromSignalsGetSignalsResponse",
    "PassFromContentStandardsCreateContentStandardsRequest",
    "PassFromContentStandardsUpdateContentStandardsRequest",
    "PayloadFromCoreRegistryEvent",
    "PayloadFromCoreWholesaleFeedEvent",
    "PaymentTermsFromCoreInsertionOrder",
    "PaymentTermsFromEnumsPaymentTerms",
    "PerformanceFeedbackFromCorePerformanceFeedback",
    "PerformanceFeedbackFromProtocolGetAdcpCapabilitiesResponse",
    "PeriodFromCoreJobItem",
    "PeriodFromCorePrice",
    "PeriodFromCoreReportingConsumerStatus",
    "PeriodFromCoreReportingFileManifest",
    "PeriodFromCoreReportingObligation",
    "PeriodFromCoreReportingRevision",
    "PeriodFromCoreSignalPricing",
    "PeriodFromCoreVendorPricingOption",
    "PeriodFromMediaBuyGetReportingStatusRequest",
    "PixelRatioFromCoreRequirementsImageAssetRequirements",
    "PixelRatioFromFormatsCanonicalBase",
    "PixelRatioFromFormatsCanonicalImage",
    "PlacementFromCorePlacement",
    "PlacementFromMediaBuyGetMediaBuyDeliveryRequest",
    "PlacementSelectionFromCorePlacementSelection",
    "PlacementSelectionFromCoreTargeting",
    "PlacementSelectionFromCoreTargetingOverlaySupport",
    "PlanFromGovernanceGetPlanAuditLogsResponse",
    "PlanFromGovernanceSyncPlansRequest",
    "PlanFromGovernanceSyncPlansResponse",
    "PlanSummaryFromGovernanceReportPlanAdjustmentResponse",
    "PlanSummaryFromGovernanceReportPlanOutcomeResponse",
    "PolicyIdFromMediaBuyAcceptancePolicyRule",
    "PolicyIdFromMediaBuyProductDiscoveryCriteria",
    "PortfolioFromGovernanceSyncPlansRequest",
    "PortfolioFromProtocolGetAdcpCapabilitiesResponse",
    "PreOnboardingPrecisionLevelFromCoreSignalDefinition",
    "PreOnboardingPrecisionLevelFromCoreSignalDefinitionEnrichment",
    "PreOnboardingPrecisionLevelFromSignalsGetSignalsResponse",
    "Preview2FromCreativePreviewCreativeResponse",
    "Preview2FromMediaBuyBuildCreativeResponse",
    "Preview3FromCreativePreviewCreativeResponse",
    "Preview3FromMediaBuyBuildCreativeResponse",
    "PreviewFromCreativePreviewCreativeResponse",
    "PreviewFromMediaBuyBuildCreativeResponse",
    "PreviewFromProtocolGetAdcpCapabilitiesResponse",
    "PriceFromCorePrice",
    "PriceFromSponsoredIntelligenceSiSendMessageResponse",
    "PricingCurrencyFromCoreProductFilters",
    "PricingCurrencyFromCoreProductOfferFilters",
    "PricingModelFromCoreCanonicalPricingOption",
    "PricingModelFromEnumsPricingModel",
    "ProductCardFromA2UiSiCatalog",
    "ProductCardFromCoreProduct",
    "ProductIdFromMediaBuyProductDiscoveryCriteria",
    "ProductIdFromMediaBuyProductPurchase",
    "ProductIdFromMediaBuyRequestProposalsResponse",
    "ProductPayloadViewFromCoreNotificationConfig",
    "ProductPayloadViewFromCoreWholesaleFeedWebhook",
    "ProgressFromCoreTasksGetResponse",
    "ProgressFromProtocolGetTaskStatusResponse",
    "PropertyFeatureFromAdagents",
    "PropertyFeatureFromPropertyPropertyFeature",
    "PropertyFeatureFromProtocolGetAdcpCapabilitiesResponse",
    "PropertyFromBrandVerifyBrandClaimsRequest",
    "PropertyFromCoreProperty",
    "PropertyTypeFromCoreRealEstateItem",
    "PropertyTypeFromEnumsPropertyType",
    "ProposalFromCoreProposal",
    "ProposalFromMediaBuyRefineProposalsResponse",
    "ProposalFromMediaBuyRequestProposalsResponse",
    "ProposalKindFromCoreCanonicalProposal",
    "ProposalKindFromMediaBuyRefineProposalsResponse",
    "ProposalRefinementFromMediaBuyProposalRefinement",
    "ProposalRefinementFromProtocolGetAdcpCapabilitiesResponse",
    "ProposalStatusFromEnumsProposalStatus",
    "ProposalStatusFromMediaBuyAcceptProposalResponse",
    "ProposalStatusFromMediaBuyBuyProductsResponse",
    "ProposalStatusFromMediaBuyGetMediaBuysResponse",
    "ProposalStatusFromMediaBuyMediaBuyCommitmentResponse",
    "ProposalStatusFromMediaBuyRefineProposalsResponse",
    "ProposalStatusFromMediaBuyRequestProposalsResponse",
    "ProtocolFromCoreRequirementsUrlAssetRequirements",
    "ProtocolFromManifestSchema",
    "ProtocolFromProtocolGetAdcpCapabilitiesRequest",
    "ProvenanceFromCoreProvenance",
    "ProvenanceFromCoreReferenceRenderer",
    "ProviderFromContentStandardsArtifact",
    "ProviderFromCoreProduct",
    "ProviderFromCoreProductFilters",
    "ProviderFromCoreProductOfferFilters",
    "ProviderFromCoreReportingDatasetShareDestination",
    "ProviderFromCoreReportingDeliveryOffering",
    "ProviderFromCoreReportingReportDefinition",
    "ProviderFromCoreReportingWriteDestination",
    "PublisherDomainFromCoreCanonicalProduct",
    "PublisherDomainFromCoreProduct",
    "PublisherDomainFromCorePublisherPropertySelector",
    "PublisherDomainFromProtocolGetAdcpCapabilitiesResponse",
    "PublisherPropertyFromCoreCanonicalProduct",
    "PublisherPropertyFromCoreProduct",
    "PurchaseBindingFromMediaBuyAcceptProposalResponse",
    "PurchaseBindingFromMediaBuyBuyProductsResponse",
    "PurchaseBindingFromMediaBuyMediaBuyCommitmentResponse",
    "PurgeKindFromComplianceComplyTestControllerRequest",
    "PurgeKindFromCreativeCreativePurgedWebhook",
    "QualifierFromCoreCommittedMetric",
    "QualifierFromCoreDeliveryMetricAggregate",
    "QualifierFromCoreMissingMetric",
    "QualifierFromCorePackageDeliveryMetricValue",
    "QualifierFromCorePerformanceFeedback",
    "QualifierFromCorePerformanceFeedbackMetric",
    "QualifierFromCoreVendorMetricValue",
    "QualifierFromMediaBuyPackageRequest",
    "QuerySummaryFromCoreTasksListResponse",
    "QuerySummaryFromCreativeListCreativesResponse",
    "QuerySummaryFromProtocolListTasksResponse",
    "RadiusFromCoreCatchment",
    "RadiusFromCoreProductFilters",
    "RadiusFromCoreTargeting",
    "RangeFromCoreAudienceCharacteristic",
    "RangeFromCoreSignalDefinition",
    "RangeFromCoreSignalListing",
    "RangeFromPropertyPropertyFeatureDefinition",
    "RangeFromProtocolGetAdcpCapabilitiesResponse",
    "RangeFromSignalsGetSignalsResponse",
    "ReachWindowFromComplianceComplyTestControllerRequest",
    "ReachWindowFromCoreDeliveryMetrics",
    "ReasonCodeFromCoreAccountStatusChangedWebhook",
    "ReasonCodeFromCoreAttestationEvaluation",
    "ReasonCodeFromCoreReportingAdjustment",
    "ReasonFromAdagents",
    "ReasonFromCoreBrandResponseAuthorizationResult",
    "ReasonFromCoreCapabilitiesChangedWebhook",
    "ReasonFromCoreCatalogItemAvailabilityUpdate",
    "ReasonFromCorePrincipalChangedWebhook",
    "ReasonFromCoreReportingCoverage",
    "ReasonFromCreativeSyncCreativesAsyncResponseInputRequired",
    "ReasonFromErrorDetailsExecutionRequirementUnmet",
    "ReasonFromMediaBuyBuildCreativeAsyncResponseInputRequired",
    "ReasonFromMediaBuyCreateMediaBuyAsyncResponseInputRequired",
    "ReasonFromMediaBuyGetProductsAsyncResponseInputRequired",
    "ReasonFromMediaBuySyncCatalogsAsyncResponseInputRequired",
    "ReasonFromMediaBuyUpdateMediaBuyAsyncResponseInputRequired",
    "ReasonFromSponsoredIntelligenceSiTerminateSessionRequest",
    "RecoveryFromCoreError",
    "RecoveryFromErrorDetailsVendorErrorCodes",
    "RecoveryFromGovernanceReportedOutcomeError",
    "RefreshCadenceFromCoreSignalDefinition",
    "RefreshCadenceFromCoreSignalDefinitionEnrichment",
    "RefreshCadenceFromSignalsGetSignalsResponse",
    "RegionFromCoreCanvasConstraint",
    "RegionFromCoreOffering",
    "RegionFromCoreProductFilters",
    "RegionFromCoreProductOfferFilters",
    "RelationshipFromCoreAudienceEvidence",
    "RelationshipFromCoreCanonicalAudienceEvidence",
    "RenderingOriginFromCorePreviewRendererMetadata",
    "RenderingOriginFromProtocolGetAdcpCapabilitiesResponse",
    "ReportingFrequencyFromCoreReportingWebhook",
    "ReportingFrequencyFromEnumsReportingFrequency",
    "ReportingPeriodFromCreativeGetCreativeDeliveryResponse",
    "ReportingPeriodFromGovernanceCheckGovernanceRequest",
    "ReportingPeriodFromGovernanceCheckGovernanceResponse",
    "ReportingPeriodFromGovernanceGetPlanAuditLogsResponse",
    "ReportingPeriodFromGovernanceReportPlanOutcomeRequest",
    "ReportingPeriodFromMediaBuyGetMediaBuyDeliveryResponse",
    "ReportingPeriodFromMediaBuyMediaBuyDeliveryWebhookResult",
    "RequiredForItemFromCoreDownstreamConnectionRequirement",
    "RequiredForItemFromCoreProductExecutionRequirement",
    "RequiredForItemFromProtocolGetAdcpCapabilitiesResponse",
    "RequiredVendorMetricFromCoreProductFilters",
    "RequiredVendorMetricFromCoreProductOfferFilters",
    "RequirementFromPropertyValidationResult",
    "RequirementFromProtocolGetAdcpCapabilitiesResponse",
    "RequirementModeFromCoreAudienceEvidenceRequirements",
    "RequirementModeFromCoreProductAudienceEvidenceRequirements",
    "ResourceFromCoreAccountChange",
    "ResourceFromCoreAccountChangeRecordedWebhook",
    "ResourceTypeFromAccountListAccountChangesRequest",
    "ResourceTypeFromAccountListAccountChangesResponse",
    "ResourceTypeFromCoreImpairment",
    "ResourceTypeFromCoreWarningResource",
    "ResourceTypeFromProtocolGetAdcpCapabilitiesResponse",
    "ResponseFromCreativePreviewCreativeResponse",
    "ResponseFromSponsoredIntelligenceSiInitiateSessionResponse",
    "ResponseFromSponsoredIntelligenceSiSendMessageResponse",
    "ResultFromContentStandardsValidateContentDeliveryResponse",
    "ResultFromCoreProvenance",
    "ResultFromCreativePreviewCreativeResponse",
    "ResultFromProtocolGetPrincipalResponse",
    "ResultFromProtocolSyncPrincipalResponse",
    "ResultsFromMediaBuyDeclineProposalsResponse",
    "ResultsFromMediaBuyRefineProposalsResponse",
    "ResultsFromMediaBuySyncReportingReceiptsResponse",
    "ResultsFromMediaBuySyncReportingStatusResponse",
    "RightFromBrandGetRightsResponse",
    "RightFromCoreSignalDefinition",
    "RightFromCoreSignalDefinitionEnrichment",
    "RightFromSignalsGetSignalsResponse",
    "RightsFromBrandGetBrandIdentityResponse",
    "RightsFromBrandSearchBrandsResponse",
    "RoleFromContentStandardsArtifact",
    "RoleFromCoreBusinessEntity",
    "RoleFromCoreProductCardReferenceAsset",
    "RoleFromCoreProvenance",
    "RoleFromCoreReferenceAsset",
    "RoleFromCoreRequirementsUrlAssetRequirements",
    "RoleFromCoreVerificationTokenClaims",
    "RoleFromSponsoredIntelligenceSiSponsoredContext",
    "RouteFromCorePreviewProvider",
    "RouteFromProtocolGetAdcpCapabilitiesResponse",
    "RuntimeAttestationFromGovernanceCheckGovernanceRequest",
    "RuntimeAttestationFromGovernanceGetPlanAuditLogsResponse",
    "ScopeFromContentStandardsCreateContentStandardsRequest",
    "ScopeFromContentStandardsUpdateContentStandardsRequest",
    "ScopeFromCoreDownstreamConnectionRequirement",
    "ScopeFromCoreReportingDeliveryConfig",
    "ScopeFromCoreSignalCoverageForecast",
    "ScopeFromErrorDetailsBillingNotSupported",
    "ScopeFromErrorDetailsRateLimited",
    "ScopeFromMediaBuyAcceptancePolicyProfile",
    "ScopeFromMediaBuyGetProductsResponse",
    "ScopeFromMediaBuyGetReportingStatusResponse",
    "ScopeFromMediaBuyListProductsResponse",
    "ScopeFromMediaBuyRequestProposalsResponse",
    "ScopeFromSignalsGetSignalsResponse",
    "SeedSourceFromCoreSignalDefinition",
    "SeedSourceFromCoreSignalDefinitionEnrichment",
    "SeedSourceFromSignalsGetSignalsResponse",
    "SelectionModeFromCoreFormat",
    "SelectionModeFromCoreSignalSelectionGroupRule",
    "SelectionModeFromCoreSignalTargetingRules",
    "SellerPreferenceFromCoreCanonicalFormatOption",
    "SellerPreferenceFromCoreCreativeOperationFormatDeclaration",
    "SellerPreferenceFromCoreFormat",
    "SellerPreferenceFromCorePackageFormatSnapshot",
    "SellerPreferenceFromCoreProductFormatDeclaration",
    "SellerPreferenceFromCoreTransformer",
    "SetupFromAccountSyncAccountsResponse",
    "SetupFromCoreAccount",
    "SetupFromCoreAccountStatusChangedWebhook",
    "SetupFromCoreAgentReportingDestinationState",
    "SetupFromCoreReportingDeliveryConfigState",
    "SetupFromMediaBuySyncEventSourcesResponse",
    "SignalFromCoreWholesaleFeedEvent",
    "SignalFromSignalsGetSignalsResponse",
    "SignalIdFromAdagents",
    "SignalIdFromCoreDataProviderSignalSelector",
    "SignalIdFromCoreSignalId",
    "SignalTagFromAdagents",
    "SignalTagFromCoreDataProviderSignalSelector",
    "SignalsFromProtocolGetAdcpCapabilitiesResponse",
    "SignalsFromTrustedMatchContextMatchResponse",
    "SignalsFromTrustedMatchProviderContextMatchResponse",
    "SizeFromFormatsCanonicalDisplayTag",
    "SizeFromFormatsCanonicalHtml5",
    "SizeFromFormatsCanonicalImage",
    "SnapshotFromCreativeListCreativesResponse",
    "SnapshotFromMediaBuyGetMediaBuysResponse",
    "SortAppliedFromCoreTasksListResponse",
    "SortAppliedFromCreativeListCreativesResponse",
    "SortAppliedFromProtocolListTasksResponse",
    "SortFromCoreTasksListRequest",
    "SortFromCreativeListCreativesRequest",
    "SortFromProtocolListTasksRequest",
    "SourceFromCoreCreativeLocalization",
    "SourceFromCoreCreativeRepresentation",
    "SourceFromCoreError",
    "SourceFromCoreReportingReportDefinition",
    "SourceFromGovernanceGetPlanAuditLogsResponse",
    "SourceFromGovernancePolicyEntry",
    "SourceFromGovernanceReportPlanOutcomeRequest",
    "SourceFromGovernanceSyncPlansResponse",
    "SourceFromMediaBuyListCreativeFormatsResponse",
    "SourceFromMediaBuySyncAudiencesResponse",
    "StatusFilterFromMediaBuyGetMediaBuyDeliveryRequest",
    "StatusFilterFromMediaBuyGetMediaBuysRequest",
    "StatusFromAaoAgentPublishers",
    "StatusFromAccountListAccountChangesResponse",
    "StatusFromAccountListAccountsRequest",
    "StatusFromAccountSyncGovernanceResponse",
    "StatusFromCoreAssetsPublishedPostAsset",
    "StatusFromCoreCatalogItemAvailabilityState",
    "StatusFromCoreCatalogItemAvailabilityUpdateResult",
    "StatusFromCoreDownstreamConnectionRequirement",
    "StatusFromCoreGeoPlaceCatalogEntry",
    "StatusFromCoreMacroResolutionResult",
    "StatusFromCoreOpportunityContext",
    "StatusFromCorePerformanceFeedback",
    "StatusFromCoreProductExecutionRequirement",
    "StatusFromCoreRegistryEvent",
    "StatusFromCoreReportingAdjustmentReceipt",
    "StatusFromCoreReportingCoverage",
    "StatusFromCoreReportingMaterialization",
    "StatusFromCoreReportingReceipt",
    "StatusFromCoreWebhookActivityRecord",
    "StatusFromGovernanceGetPlanAuditLogsResponse",
    "StatusFromGovernanceSyncPlansResponse",
    "StatusFromMediaBuyAcceptProposalRequest",
    "StatusFromMediaBuyBuyProductsRequest",
    "StatusFromMediaBuyCreateMediaBuyRequest",
    "StatusFromMediaBuyGetMediaBuyDeliveryResponse",
    "StatusFromMediaBuyGetProductsResponse",
    "StatusFromMediaBuyGetReportingStatusResponse",
    "StatusFromMediaBuyMediaBuyDeliveryWebhookResult",
    "StatusFromMediaBuyRefineProposalsResponse",
    "StatusFromMediaBuyRequestProposalsRequest",
    "StatusFromMediaBuyRequestProposalsResponse",
    "StatusFromPropertyAuthorizationResult",
    "StatusFromPropertyValidationResult",
    "StatusFromSponsoredIntelligenceSiSponsoredContextReceipt",
    "StatusFromTrustedMatchProviderRegistration",
    "SubjectFacetFromMediaBuyAcceptanceContext",
    "SubjectFacetFromMediaBuyAcceptancePolicyRule",
    "SubjectFromCoreAudienceEvidence",
    "SubjectFromCoreRightsAttestationEvaluation",
    "SubjectFromCoreRightsConstraint",
    "SubjectFromGovernanceCheckGovernanceRequest",
    "SubjectFromMediaBuyAcceptanceContext",
    "SuggestionFromComplianceComplyTestControllerRequest",
    "SuggestionFromComplianceComplyTestControllerResponse",
    "SuggestionFromMediaBuyGetProductsRejected",
    "SuggestionFromMediaBuyGetProductsResponse",
    "SuggestionFromMediaBuyRefineProposalsResponse",
    "SuggestionFromMediaBuyRequestProposalsResponse",
    "SummaryFromContentStandardsValidateContentDeliveryResponse",
    "SummaryFromCoreInventoryListApplication",
    "SummaryFromGovernanceGetPlanAuditLogsResponse",
    "SummaryFromPropertyValidatePropertyDeliveryResponse",
    "SupportedDimensionFromErrorDetailsUnsupportedRefinementDimension",
    "SupportedDimensionFromProtocolGetAdcpCapabilitiesResponse",
    "SupportedTargetFromCoreProduct",
    "SupportedTargetFromCoreVendorMetricOptimizationSupportedMetric",
    "SupportedTargetFromProtocolGetAdcpCapabilitiesResponse",
    "SupportedVersionFromCoreGeoPlaceCatalogCapability",
    "SupportedVersionFromErrorDetailsVersionUnsupported",
    "SupportedVersionFromProtocolGetAdcpCapabilitiesResponse",
    "SystemFromCorePostalArea",
    "SystemFromCorePostalCountrySystem",
    "SystemVersionFromCoreGeoPlaceRequirement",
    "SystemVersionFromCoreTargetingOverlaySupport",
    "TagFromCoreSignalDefinition",
    "TagFromMediaBuySyncAudiencesRequest",
    "TagsFromAdagents",
    "TagsFromCoreCatalog",
    "TargetFrequencyFromCoreBudgetAllocation",
    "TargetFrequencyFromCoreCanonicalOptimizationGoal",
    "TargetFrequencyFromCoreOptimizationGoal",
    "TargetFromCoreAssetsDaastTrackerAsset",
    "TargetFromCoreAssetsVastTrackerAsset",
    "TargetFromCoreBudgetAllocation",
    "TargetFromCoreCanonicalOptimizationGoal",
    "TargetFromCoreOptimizationGoal",
    "TargetFromCreativeValidateInputResult",
    "TargetingKvFromTrustedMatchContextMatchResponse",
    "TargetingKvFromTrustedMatchProviderContextMatchResponse",
    "TargetingKvsFromTrustedMatchContextMatchResponse",
    "TargetingKvsFromTrustedMatchProviderContextMatchResponse",
    "TargetingModeFromCoreProductFilters",
    "TargetingModeFromCoreSignalSelectionGroupRule",
    "TaskFromCoreAccountChange",
    "TaskFromCoreCanonicalMediaBuyActionFields",
    "TaskFromCoreMediaBuyAvailableAction",
    "TaskFromCoreResponsePayloadJwsEnvelope",
    "TaskFromCoreTasksListResponse",
    "TaskFromProtocolListTasksResponse",
    "TaxonomyFromCoreAudienceCharacteristic",
    "TaxonomyFromCoreSignalDefinition",
    "TaxonomyFromCoreSignalDefinitionEnrichment",
    "TaxonomyFromSignalsGetSignalsResponse",
    "TmpxMacroFromTrustedMatchIdentityMatchResponse",
    "TmpxMacroFromTrustedMatchProviderRegistration",
    "TotalBudgetFromCoreInsertionOrder",
    "TotalBudgetFromMediaBuyAcceptProposalRequest",
    "TotalBudgetFromMediaBuyBuyProductsRequest",
    "TotalBudgetFromMediaBuyCommercialTerms",
    "TotalBudgetFromMediaBuyControlMediaBuyRequest",
    "TotalBudgetFromMediaBuyCreateMediaBuyRequest",
    "TotalBudgetFromMediaBuyUpdateMediaBuyRequest",
    "TotalBudgetGuidanceFromCoreCanonicalProposal",
    "TotalBudgetGuidanceFromCoreProposal",
    "TotalBudgetGuidanceFromMediaBuyRefineProposalsResponse",
    "TotalsFromMediaBuyGetMediaBuyDeliveryResponse",
    "TotalsFromMediaBuyMediaBuyDeliveryWebhookResult",
    "TrainingDataJurisdictionFromCoreSignalDefinition",
    "TrainingDataJurisdictionFromCoreSignalDefinitionEnrichment",
    "TrainingDataJurisdictionFromSignalsGetSignalsResponse",
    "TransformFromCoreCatalogFieldMapping",
    "TransformFromRegistriesV1CanonicalMapping",
    "TransitionFromCoreImpairment",
    "TransitionFromCreativeCreativeStatusChangedWebhook",
    "TransportFromProtocolGetAdcpCapabilitiesResponse",
    "TravelTimeFromCoreCatchment",
    "TravelTimeFromCoreProductFilters",
    "TravelTimeFromCoreTargeting",
    "TrustedMatchFromCoreProduct",
    "TrustedMatchFromCoreProductFilters",
    "TrustedMatchFromCoreProductOfferFilters",
    "TrustedMatchFromProtocolGetAdcpCapabilitiesResponse",
    "TypeFromA2UiSiCatalog",
    "TypeFromCoreAccountChange",
    "TypeFromCoreCancellationPolicy",
    "TypeFromCoreCatalog",
    "TypeFromCoreCatchment",
    "TypeFromCoreProductFilters",
    "TypeFromCoreRegistryEvent",
    "TypeFromCoreSignalDefinition",
    "TypeFromCoreSignalDefinitionEnrichment",
    "TypeFromCoreTargeting",
    "TypeFromCoreTasksGetResponse",
    "TypeFromCoreTransformerParam",
    "TypeFromCreativeListCreativeFormatsRequest",
    "TypeFromGovernanceGetPlanAuditLogsResponse",
    "TypeFromPropertyPropertyFeatureDefinition",
    "TypeFromProtocolGetAdcpCapabilitiesResponse",
    "TypeFromProtocolGetTaskStatusResponse",
    "TypeFromSignalsGetSignalsResponse",
    "TypeFromSponsoredIntelligenceSiSendMessageResponse",
    "TypeFromSponsoredIntelligenceSiUiElement",
    "TypeFromTrustedMatchContextMatchRequest",
    "UidFromCoreAudienceMember",
    "UidFromCoreUserMatch",
    "UnavailableBehaviorFromCoreAssetsDaastAsset",
    "UnavailableBehaviorFromCoreAssetsDisplayTagAsset",
    "UnavailableBehaviorFromCoreAssetsVastAsset",
    "UnavailableBehaviorFromCoreMacroResolutionResult",
    "UnitFromCoreAudienceEvidence",
    "UnitFromCoreAudienceEvidenceRequirements",
    "UnitFromCoreCanonicalAudienceEvidence",
    "UnitFromCoreCanvasConstraint",
    "UnitFromCoreDuration",
    "UnitFromCoreOverlay",
    "UnitFromCoreProductAudienceEvidenceRequirements",
    "UnitFromCoreRealEstateItem",
    "UnitFromCoreVehicleItem",
    "UnmatchedLocaleActionFromCoreCreativeLocalization",
    "UnmatchedLocaleActionFromCoreCreativeLocalizationReadback",
    "ValueFromCoreAudienceCharacteristic",
    "ValueFromCoreGeoPlaceArea",
    "ValueFromCoreGeoRegionRequirement",
    "ValueFromCoreGeoRegionSupport",
    "ValueFromCoreSignalDefinition",
    "ValueFromCoreSignalDefinitionEnrichment",
    "ValueFromSignalsGetSignalsResponse",
    "ValueMappingFromCoreSignalDefinition",
    "ValueMappingFromCoreSignalDefinitionEnrichment",
    "ValueMappingFromSignalsGetSignalsResponse",
    "VariantDimensionFromCoreTransformer",
    "VariantDimensionFromProtocolGetAdcpCapabilitiesResponse",
    "VariantFromA2UiSiCatalog",
    "VariantFromBrandSearchBrandsResponse",
    "VariantFromMediaBuyBuildCreativeResponse",
    "VendorMetricFromCoreCanonicalReportingCapabilities",
    "VendorMetricFromCoreReportingCapabilities",
    "VendorMetricOptimizationFromCoreVendorMetricOptimization",
    "VendorMetricOptimizationFromProtocolGetAdcpCapabilitiesResponse",
    "VerifyAgentFromCoreAttestationReference",
    "VerifyAgentFromCoreProvenance",
    "ViewabilityFromCoreCanonicalForecastPoint",
    "ViewabilityFromCoreDeliveryMetrics",
    "ViewabilityFromCoreForecastPoint",
    "ViolationFromCreativeValidateInputResult",
    "ViolationFromErrorDetailsAccessibilityViolation",
    "ViolationFromPropertyAuthorizationResult",
    "WarningFromCoreWarning",
    "WarningFromCreativeValidateInputResult",
    "WarningFromMediaBuyAcceptProposalResponse",
    "WarningFromMediaBuyBuyProductsResponse",
    "WarningFromMediaBuyControlMediaBuyResponse",
    "WarningFromMediaBuyMediaBuyCommitmentResponse",
]
