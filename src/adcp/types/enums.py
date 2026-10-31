"""The public types of the ``enums`` domain.

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

from ._schemas.enums.account_currency_mode import (
    AccountCurrencyMode as AccountCurrencyMode,
)
from ._schemas.enums.account_scope import (
    AccountScope as AccountScope,
)
from ._schemas.enums.account_status import (
    AccountStatus as AccountStatus,
)
from ._schemas.enums.action_not_allowed_reason import (
    ActionNotAllowedReason as ActionNotAllowedReason,
)
from ._schemas.enums.action_source import (
    ActionSource as ActionSource,
)
from ._schemas.enums.activation_method import (
    CreativeActivationMethod as CreativeActivationMethod,
)
from ._schemas.enums.adcp_protocol import (
    AdCPProtocol as AdCPProtocol,
)
from ._schemas.enums.adjustment_kind import (
    PriceAdjustmentKind as PriceAdjustmentKind,
)
from ._schemas.enums.advertiser_industry import (
    AdvertiserIndustry as AdvertiserIndustry,
)
from ._schemas.enums.age_determination_basis import (
    AgeDeterminationBasis as AgeDeterminationBasis,
)
from ._schemas.enums.age_verification_method import (
    AgeVerificationMethod as AgeVerificationMethod,
)
from ._schemas.enums.assessment_status import (
    AssessmentStatus as AssessmentStatus,
)
from ._schemas.enums.asset_content_type import (
    AssetContentType as AssetContentType,
)
from ._schemas.enums.attestation_claim import (
    AttestationClaim as AttestationClaim,
)
from ._schemas.enums.attribution_methodology import (
    AttributionMethodology as AttributionMethodology,
)
from ._schemas.enums.attribution_model import (
    AttributionModel as AttributionModel,
)
from ._schemas.enums.audience_evidence_methodology import (
    AudienceEvidenceMethodology as AudienceEvidenceMethodology,
)
from ._schemas.enums.audience_resolution_method import (
    AudienceResolutionMethod as AudienceResolutionMethod,
)
from ._schemas.enums.audience_source import (
    AudienceSource as AudienceSource,
)
from ._schemas.enums.audience_status import (
    AudienceStatus as AudienceStatus,
)
from ._schemas.enums.audience_subject_type import (
    AudienceSubjectType as AudienceSubjectType,
)
from ._schemas.enums.audio_channel_layout import (
    AudioChannelLayout as AudioChannelLayout,
)
from ._schemas.enums.audio_distribution_type import (
    AudioDistributionType as AudioDistributionType,
)
from ._schemas.enums.auth_scheme import (
    AuthenticationScheme as AuthenticationScheme,
)
from ._schemas.enums.availability_status import (
    AvailabilityStatus as AvailabilityStatus,
)
from ._schemas.enums.available_metric import (
    AvailableMetric as AvailableMetric,
)
from ._schemas.enums.billing_party import (
    BillingParty as BillingParty,
)
from ._schemas.enums.binary_verdict import (
    BinaryVerdict as BinaryVerdict,
)
from ._schemas.enums.brand_agent_type import (
    BrandAgentType as BrandAgentType,
)
from ._schemas.enums.browser_family import (
    BrowserFamily as BrowserFamily,
)
from ._schemas.enums.c2pa_watermark_action import (
    C2PAWatermarkAction as C2PAWatermarkAction,
)
from ._schemas.enums.canceled_by import (
    CanceledBy as CanceledBy,
)
from ._schemas.enums.canonical_media_buy_action import (
    CanonicalMediaBuyActionName as CanonicalMediaBuyActionName,
)
from ._schemas.enums.canonical_media_buy_action_mode import (
    CanonicalMediaBuyActionMode as CanonicalMediaBuyActionMode,
)
from ._schemas.enums.catalog_action import (
    CatalogAction as CatalogAction,
)
from ._schemas.enums.catalog_item_status import (
    CatalogItemStatus as CatalogItemStatus,
)
from ._schemas.enums.catalog_type import (
    CatalogType as CatalogType,
)
from ._schemas.enums.channels import (
    MediaChannel as MediaChannel,
)
from ._schemas.enums.cloud_storage_protocol import (
    CloudStorageProtocol as CloudStorageProtocol,
)
from ._schemas.enums.co_branding_requirement import (
    CoBrandingRequirement as CoBrandingRequirement,
)
from ._schemas.enums.collection_cadence import (
    CollectionCadence as CollectionCadence,
)
from ._schemas.enums.collection_kind import (
    CollectionKind as CollectionKind,
)
from ._schemas.enums.collection_relationship import (
    CollectionRelationship as CollectionRelationship,
)
from ._schemas.enums.collection_status import (
    CollectionStatus as CollectionStatus,
)
from ._schemas.enums.completion_source import (
    CompletionSource as CompletionSource,
)
from ._schemas.enums.consent_basis import (
    ConsentBasis as ConsentBasis,
)
from ._schemas.enums.content_id_type import (
    ContentIDType as ContentIDType,
)
from ._schemas.enums.content_rating_system import (
    ContentRatingSystem as ContentRatingSystem,
)
from ._schemas.enums.creative_action import (
    CreativeAction as CreativeAction,
)
from ._schemas.enums.creative_agent_capability import (
    CreativeAgentCapability as CreativeAgentCapability,
)
from ._schemas.enums.creative_approval_status import (
    CreativeApprovalStatus as CreativeApprovalStatus,
)
from ._schemas.enums.creative_event_reason_code import (
    CreativeEventReasonCode as CreativeEventReasonCode,
)
from ._schemas.enums.creative_identifier_type import (
    CreativeIdentifierType as CreativeIdentifierType,
)
from ._schemas.enums.creative_quality import (
    CreativeQuality as CreativeQuality,
)
from ._schemas.enums.creative_selection_strategy import (
    CreativeSelectionStrategy as CreativeSelectionStrategy,
)
from ._schemas.enums.creative_sort_field import (
    CreativeSortField as CreativeSortField,
)
from ._schemas.enums.creative_status import (
    CreativeStatus as CreativeStatus,
)
from ._schemas.enums.ctv_ad_experience import (
    CTVAdExperience as CTVAdExperience,
)
from ._schemas.enums.daast_tracking_event import (
    DAASTTrackingEvent as DAASTTrackingEvent,
)
from ._schemas.enums.daast_version import (
    DAASTVersion as DAASTVersion,
)
from ._schemas.enums.day_of_week import (
    DayOfWeek as DayOfWeek,
)
from ._schemas.enums.daypart_timezone_mode import (
    DaypartTimezoneMode as DaypartTimezoneMode,
)
from ._schemas.enums.delegation_authority import (
    DelegationAuthority as DelegationAuthority,
)
from ._schemas.enums.delivery_recipient_cloud import (
    DeliveryRecipientCloud as DeliveryRecipientCloud,
)
from ._schemas.enums.delivery_status import (
    DeliveryStatus as DeliveryStatus,
)
from ._schemas.enums.delivery_type import (
    DeliveryType as DeliveryType,
)
from ._schemas.enums.demographic_system import (
    DemographicSystem as DemographicSystem,
)
from ._schemas.enums.derivative_type import (
    DerivativeType as DerivativeType,
)
from ._schemas.enums.device_platform import (
    DevicePlatform as DevicePlatform,
)
from ._schemas.enums.device_type import (
    DeviceType as DeviceType,
)
from ._schemas.enums.digital_source_type import (
    DigitalSourceType as DigitalSourceType,
)
from ._schemas.enums.dimension_unit import (
    DimensionUnit as DimensionUnit,
)
from ._schemas.enums.disclosure_persistence import (
    DisclosurePersistence as DisclosurePersistence,
)
from ._schemas.enums.disclosure_position import (
    DisclosurePosition as DisclosurePosition,
)
from ._schemas.enums.distance_unit import (
    DistanceUnit as DistanceUnit,
)
from ._schemas.enums.distribution_identifier_type import (
    DistributionIdentifierType as DistributionIdentifierType,
)
from ._schemas.enums.dooh_motion_type import (
    DOOHMotionType as DOOHMotionType,
)
from ._schemas.enums.embedded_provenance_method import (
    EmbeddedProvenanceMethod as EmbeddedProvenanceMethod,
)
from ._schemas.enums.error_code import (
    ErrorCode as ErrorCode,
)
from ._schemas.enums.error_scope import (
    ErrorScope as ErrorScope,
)
from ._schemas.enums.escalation_severity import (
    EscalationSeverity as EscalationSeverity,
)
from ._schemas.enums.event_type import (
    EventType as EventType,
)
from ._schemas.enums.exclusivity import (
    Exclusivity as Exclusivity,
)
from ._schemas.enums.feature_check_status import (
    FeatureCheckStatus as FeatureCheckStatus,
)
from ._schemas.enums.feed_format import (
    FeedFormat as FeedFormat,
)
from ._schemas.enums.feedback_source import (
    FeedbackSource as FeedbackSource,
)
from ._schemas.enums.forecast_method import (
    ForecastMethod as ForecastMethod,
)
from ._schemas.enums.forecast_range_unit import (
    ForecastRangeUnit as ForecastRangeUnit,
)
from ._schemas.enums.forecastable_metric import (
    ForecastableMetric as ForecastableMetric,
)
from ._schemas.enums.format_id_parameter import (
    FormatIDParameter as FormatIDParameter,
)
from ._schemas.enums.frame_rate_type import (
    FrameRateType as FrameRateType,
)
from ._schemas.enums.frequency_cap_control_mode import (
    FrequencyCapControlMode as FrequencyCapControlMode,
)
from ._schemas.enums.frequency_cap_mutable_field import (
    FrequencyCapMutableField as FrequencyCapMutableField,
)
from ._schemas.enums.frequency_cap_scope import (
    FrequencyCapScope as FrequencyCapScope,
)
from ._schemas.enums.genre_taxonomy import (
    GenreTaxonomy as GenreTaxonomy,
)
from ._schemas.enums.geo_level import (
    GeographicTargetingLevel as GeographicTargetingLevel,
)
from ._schemas.enums.gop_type import (
    GOPType as GOPType,
)
from ._schemas.enums.governance_decision import (
    GovernanceDecision as GovernanceDecision,
)
from ._schemas.enums.governance_domain import (
    GovernanceDomain as GovernanceDomain,
)
from ._schemas.enums.governance_mode import (
    GovernanceMode as GovernanceMode,
)
from ._schemas.enums.governance_phase import (
    GovernancePhase as GovernancePhase,
)
from ._schemas.enums.history_entry_type import (
    HistoryEntryType as HistoryEntryType,
)
from ._schemas.enums.http_method import (
    HTTPMethod as HTTPMethod,
)
from ._schemas.enums.identifier_types import (
    PropertyIdentifierTypes as PropertyIdentifierTypes,
)
from ._schemas.enums.impairment_offline_state import (
    ImpairmentOfflineState as ImpairmentOfflineState,
)
from ._schemas.enums.impairment_reason_code import (
    ImpairmentReasonCode as ImpairmentReasonCode,
)
from ._schemas.enums.indicator_type import (
    IndicatorType as IndicatorType,
)
from ._schemas.enums.installment_status import (
    InstallmentStatus as InstallmentStatus,
)
from ._schemas.enums.javascript_module_type import (
    JavaScriptModuleType as JavaScriptModuleType,
)
from ._schemas.enums.landing_page_requirement import (
    LandingPageRequirement as LandingPageRequirement,
)
from ._schemas.enums.legacy_postal_system import (
    CountryFusedPostalCodeSystem as CountryFusedPostalCodeSystem,
)
from ._schemas.enums.lift_dimension import (
    LiftDimension as LiftDimension,
)
from ._schemas.enums.logo_slot import (
    LogoSlot as LogoSlot,
)
from ._schemas.enums.macro_dialect import (
    MacroDialectFamily as MacroDialectFamily,
)
from ._schemas.enums.macro_mapping_status import (
    MacroMappingStatus as MacroMappingStatus,
)
from ._schemas.enums.macro_processing_operation import (
    MacroProcessingOperation as MacroProcessingOperation,
)
from ._schemas.enums.macro_resolution_reason import (
    MacroResolutionReason as MacroResolutionReason,
)
from ._schemas.enums.macro_resolver import (
    MacroProcessingActor as MacroProcessingActor,
)
from ._schemas.enums.macro_value_context import (
    MacroValueContext as MacroValueContext,
)
from ._schemas.enums.makegood_remedy import (
    MakegoodRemedy as MakegoodRemedy,
)
from ._schemas.enums.markdown_flavor import (
    MarkdownFlavor as MarkdownFlavor,
)
from ._schemas.enums.match_id_type import (
    MatchIDType as MatchIDType,
)
from ._schemas.enums.match_type import (
    MatchType as MatchType,
)
from ._schemas.enums.media_buy_action_mode import (
    MediaBuyActionMode as MediaBuyActionMode,
)
from ._schemas.enums.media_buy_frequency_cap_control_mode import (
    MediaBuyFrequencyCapControlMode as MediaBuyFrequencyCapControlMode,
)
from ._schemas.enums.media_buy_health import (
    MediaBuyHealth as MediaBuyHealth,
)
from ._schemas.enums.media_buy_status import (
    MediaBuyStatus as MediaBuyStatus,
)
from ._schemas.enums.media_buy_valid_action import (
    MediaBuyValidAction as MediaBuyValidAction,
)
from ._schemas.enums.metric_scope import (
    MetricScope as MetricScope,
)
from ._schemas.enums.metric_type import (
    MetricType as MetricType,
)
from ._schemas.enums.metro_system import (
    MetroAreaSystem as MetroAreaSystem,
)
from ._schemas.enums.moov_atom_position import (
    MoovAtomPosition as MoovAtomPosition,
)
from ._schemas.enums.motion_level import (
    CreativeMotionLevel as CreativeMotionLevel,
)
from ._schemas.enums.notification_type import (
    NotificationType as NotificationType,
)
from ._schemas.enums.offering_availability_status import (
    OfferingAvailabilityStatus as OfferingAvailabilityStatus,
)
from ._schemas.enums.outcome_target_cost_strength import (
    OutcomeTargetCostStrength as OutcomeTargetCostStrength,
)
from ._schemas.enums.outcome_type import (
    OutcomeType as OutcomeType,
)
from ._schemas.enums.pacing import (
    Pacing as Pacing,
)
from ._schemas.enums.payment_terms import (
    PaymentTerms as PaymentTerms,
)
from ._schemas.enums.performance_baseline import (
    PerformanceBaseline as PerformanceBaseline,
)
from ._schemas.enums.performance_standard_metric import (
    PerformanceStandardMetric as PerformanceStandardMetric,
)
from ._schemas.enums.pixel_tracking_event import (
    PixelTrackingEvent as PixelTrackingEvent,
)
from ._schemas.enums.policy_category import (
    PolicyCategory as PolicyCategory,
)
from ._schemas.enums.policy_enforcement import (
    PolicyEnforcementLevel as PolicyEnforcementLevel,
)
from ._schemas.enums.postal_system import (
    PostalCodeSystem as PostalCodeSystem,
)
from ._schemas.enums.preview_output_format import (
    PreviewOutputFormat as PreviewOutputFormat,
)
from ._schemas.enums.pricing_model import (
    PricingModel as PricingModel,
)
from ._schemas.enums.pricing_structure import (
    PricingStructure as PricingStructure,
)
from ._schemas.enums.principal_kind import (
    PrincipalKind as PrincipalKind,
)
from ._schemas.enums.production_quality import (
    ProductionQuality as ProductionQuality,
)
from ._schemas.enums.property_type import (
    PropertyType as PropertyType,
)
from ._schemas.enums.proposal_decline_reason import (
    ProposalDeclineReason as ProposalDeclineReason,
)
from ._schemas.enums.proposal_refinement_reason import (
    ProposalRefinementReason as ProposalRefinementReason,
)
from ._schemas.enums.proposal_status import (
    ProposalStatus as ProposalStatus,
)
from ._schemas.enums.publisher_identifier_types import (
    PublisherIdentifierTypes as PublisherIdentifierTypes,
)
from ._schemas.enums.purchase_type import (
    PurchaseType as PurchaseType,
)
from ._schemas.enums.reach_aggregation import (
    ReachAggregation as ReachAggregation,
)
from ._schemas.enums.reach_unit import (
    ReachUnit as ReachUnit,
)
from ._schemas.enums.reporting_destination_setup_state import (
    ReportingDestinationSetupState as ReportingDestinationSetupState,
)
from ._schemas.enums.reporting_finality import (
    ReportingFinality as ReportingFinality,
)
from ._schemas.enums.reporting_frequency import (
    ReportingFrequency as ReportingFrequency,
)
from ._schemas.enums.reporting_health import (
    ReportingHealth as ReportingHealth,
)
from ._schemas.enums.representation_selection_strategy import (
    RepresentationSelectionStrategy as RepresentationSelectionStrategy,
)
from ._schemas.enums.request_signing_error_code import (
    RequestSigningErrorCode as RequestSigningErrorCode,
)
from ._schemas.enums.response_type import (
    TMPResponseType as TMPResponseType,
)
from ._schemas.enums.restricted_attribute import (
    RestrictedAttribute as RestrictedAttribute,
)
from ._schemas.enums.right_type import (
    RightType as RightType,
)
from ._schemas.enums.right_use import (
    RightUse as RightUse,
)
from ._schemas.enums.rights_billing_period import (
    RightsBillingPeriod as RightsBillingPeriod,
)
from ._schemas.enums.scan_type import (
    ScanType as ScanType,
)
from ._schemas.enums.seller_policy_decline_reason import (
    SellerPolicyDeclineReason as SellerPolicyDeclineReason,
)
from ._schemas.enums.si_session_status import (
    SISessionStatus as SISessionStatus,
)
from ._schemas.enums.signal_catalog_type import (
    SignalAvailabilityType as SignalAvailabilityType,
)
from ._schemas.enums.signal_source import (
    SignalSource as SignalSource,
)
from ._schemas.enums.signal_value_type import (
    SignalValueType as SignalValueType,
)
from ._schemas.enums.snapshot_unavailable_reason import (
    SnapshotUnavailableReason as SnapshotUnavailableReason,
)
from ._schemas.enums.social_placement_surface import (
    SocialPlacementSurface as SocialPlacementSurface,
)
from ._schemas.enums.sort_direction import (
    SortDirection as SortDirection,
)
from ._schemas.enums.sort_metric import (
    SortMetric as SortMetric,
)
from ._schemas.enums.special_category import (
    SpecialCategory as SpecialCategory,
)
from ._schemas.enums.specialism import (
    AdCPSpecialism as AdCPSpecialism,
)
from ._schemas.enums.sponsored_placement_type import (
    SponsoredPlacementType as SponsoredPlacementType,
)
from ._schemas.enums.talent_role import (
    TalentRole as TalentRole,
)
from ._schemas.enums.task_status import (
    TaskStatus as TaskStatus,
)
from ._schemas.enums.task_type import (
    TaskType as TaskType,
)
from ._schemas.enums.tracker_execution_actor import (
    TrackerExecutionActor as TrackerExecutionActor,
)
from ._schemas.enums.tracker_firing_path import (
    TrackerFiringPath as TrackerFiringPath,
)
from ._schemas.enums.transport_mode import (
    TransportMode as TransportMode,
)
from ._schemas.enums.travel_time_unit import (
    TravelTimeUnit as TravelTimeUnit,
)
from ._schemas.enums.uid_type import (
    UIDType as UIDType,
)
from ._schemas.enums.universal_macro import (
    UniversalMacro as UniversalMacro,
)
from ._schemas.enums.update_frequency import (
    UpdateFrequency as UpdateFrequency,
)
from ._schemas.enums.url_asset_type import (
    URLAssetType as URLAssetType,
)
from ._schemas.enums.validation_mode import (
    ValidationMode as ValidationMode,
)
from ._schemas.enums.vast_media_delivery_method import (
    VASTMediaDeliveryMethod as VASTMediaDeliveryMethod,
)
from ._schemas.enums.vast_tracking_event import (
    VASTTrackingEvent as VASTTrackingEvent,
)
from ._schemas.enums.vast_version import (
    VASTVersion as VASTVersion,
)
from ._schemas.enums.vendor_relationship import (
    VendorRelationship as VendorRelationship,
)
from ._schemas.enums.video_placement_type import (
    VideoPlacementType as VideoPlacementType,
)
from ._schemas.enums.view_threshold_basis import (
    ViewThresholdBasis as ViewThresholdBasis,
)
from ._schemas.enums.viewability_standard import (
    ViewabilityStandard as ViewabilityStandard,
)
from ._schemas.enums.warning_code import (
    WarningCode as WarningCode,
)
from ._schemas.enums.watermark_media_type import (
    WatermarkMediaType as WatermarkMediaType,
)
from ._schemas.enums.wcag_level import (
    WCAGLevel as WCAGLevel,
)
from ._schemas.enums.webhook_response_type import (
    WebhookResponseType as WebhookResponseType,
)
from ._schemas.enums.webhook_security_method import (
    WebhookSecurityMethod as WebhookSecurityMethod,
)

__all__ = [
    'AccountCurrencyMode',
    'AccountScope',
    'AccountStatus',
    'ActionNotAllowedReason',
    'ActionSource',
    'AdCPProtocol',
    'AdCPSpecialism',
    'AdvertiserIndustry',
    'AgeDeterminationBasis',
    'AgeVerificationMethod',
    'AssessmentStatus',
    'AssetContentType',
    'AttestationClaim',
    'AttributionMethodology',
    'AttributionModel',
    'AudienceEvidenceMethodology',
    'AudienceResolutionMethod',
    'AudienceSource',
    'AudienceStatus',
    'AudienceSubjectType',
    'AudioChannelLayout',
    'AudioDistributionType',
    'AuthenticationScheme',
    'AvailabilityStatus',
    'AvailableMetric',
    'BillingParty',
    'BinaryVerdict',
    'BrandAgentType',
    'BrowserFamily',
    'C2PAWatermarkAction',
    'CTVAdExperience',
    'CanceledBy',
    'CanonicalMediaBuyActionMode',
    'CanonicalMediaBuyActionName',
    'CatalogAction',
    'CatalogItemStatus',
    'CatalogType',
    'CloudStorageProtocol',
    'CoBrandingRequirement',
    'CollectionCadence',
    'CollectionKind',
    'CollectionRelationship',
    'CollectionStatus',
    'CompletionSource',
    'ConsentBasis',
    'ContentIDType',
    'ContentRatingSystem',
    'CountryFusedPostalCodeSystem',
    'CreativeAction',
    'CreativeActivationMethod',
    'CreativeAgentCapability',
    'CreativeApprovalStatus',
    'CreativeEventReasonCode',
    'CreativeIdentifierType',
    'CreativeMotionLevel',
    'CreativeQuality',
    'CreativeSelectionStrategy',
    'CreativeSortField',
    'CreativeStatus',
    'DAASTTrackingEvent',
    'DAASTVersion',
    'DOOHMotionType',
    'DayOfWeek',
    'DaypartTimezoneMode',
    'DelegationAuthority',
    'DeliveryRecipientCloud',
    'DeliveryStatus',
    'DeliveryType',
    'DemographicSystem',
    'DerivativeType',
    'DevicePlatform',
    'DeviceType',
    'DigitalSourceType',
    'DimensionUnit',
    'DisclosurePersistence',
    'DisclosurePosition',
    'DistanceUnit',
    'DistributionIdentifierType',
    'EmbeddedProvenanceMethod',
    'ErrorCode',
    'ErrorScope',
    'EscalationSeverity',
    'EventType',
    'Exclusivity',
    'FeatureCheckStatus',
    'FeedFormat',
    'FeedbackSource',
    'ForecastMethod',
    'ForecastRangeUnit',
    'ForecastableMetric',
    'FormatIDParameter',
    'FrameRateType',
    'FrequencyCapControlMode',
    'FrequencyCapMutableField',
    'FrequencyCapScope',
    'GOPType',
    'GenreTaxonomy',
    'GeographicTargetingLevel',
    'GovernanceDecision',
    'GovernanceDomain',
    'GovernanceMode',
    'GovernancePhase',
    'HTTPMethod',
    'HistoryEntryType',
    'ImpairmentOfflineState',
    'ImpairmentReasonCode',
    'IndicatorType',
    'InstallmentStatus',
    'JavaScriptModuleType',
    'LandingPageRequirement',
    'LiftDimension',
    'LogoSlot',
    'MacroDialectFamily',
    'MacroMappingStatus',
    'MacroProcessingActor',
    'MacroProcessingOperation',
    'MacroResolutionReason',
    'MacroValueContext',
    'MakegoodRemedy',
    'MarkdownFlavor',
    'MatchIDType',
    'MatchType',
    'MediaBuyActionMode',
    'MediaBuyFrequencyCapControlMode',
    'MediaBuyHealth',
    'MediaBuyStatus',
    'MediaBuyValidAction',
    'MediaChannel',
    'MetricScope',
    'MetricType',
    'MetroAreaSystem',
    'MoovAtomPosition',
    'NotificationType',
    'OfferingAvailabilityStatus',
    'OutcomeTargetCostStrength',
    'OutcomeType',
    'Pacing',
    'PaymentTerms',
    'PerformanceBaseline',
    'PerformanceStandardMetric',
    'PixelTrackingEvent',
    'PolicyCategory',
    'PolicyEnforcementLevel',
    'PostalCodeSystem',
    'PreviewOutputFormat',
    'PriceAdjustmentKind',
    'PricingModel',
    'PricingStructure',
    'PrincipalKind',
    'ProductionQuality',
    'PropertyIdentifierTypes',
    'PropertyType',
    'ProposalDeclineReason',
    'ProposalRefinementReason',
    'ProposalStatus',
    'PublisherIdentifierTypes',
    'PurchaseType',
    'ReachAggregation',
    'ReachUnit',
    'ReportingDestinationSetupState',
    'ReportingFinality',
    'ReportingFrequency',
    'ReportingHealth',
    'RepresentationSelectionStrategy',
    'RequestSigningErrorCode',
    'RestrictedAttribute',
    'RightType',
    'RightUse',
    'RightsBillingPeriod',
    'SISessionStatus',
    'ScanType',
    'SellerPolicyDeclineReason',
    'SignalAvailabilityType',
    'SignalSource',
    'SignalValueType',
    'SnapshotUnavailableReason',
    'SocialPlacementSurface',
    'SortDirection',
    'SortMetric',
    'SpecialCategory',
    'SponsoredPlacementType',
    'TMPResponseType',
    'TalentRole',
    'TaskStatus',
    'TaskType',
    'TrackerExecutionActor',
    'TrackerFiringPath',
    'TransportMode',
    'TravelTimeUnit',
    'UIDType',
    'URLAssetType',
    'UniversalMacro',
    'UpdateFrequency',
    'VASTMediaDeliveryMethod',
    'VASTTrackingEvent',
    'VASTVersion',
    'ValidationMode',
    'VendorRelationship',
    'VideoPlacementType',
    'ViewThresholdBasis',
    'ViewabilityStandard',
    'WCAGLevel',
    'WarningCode',
    'WatermarkMediaType',
    'WebhookResponseType',
    'WebhookSecurityMethod',
]
