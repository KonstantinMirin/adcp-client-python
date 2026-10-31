"""The public types of the ``media_buy`` domain.

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

from ._schemas.media_buy.accept_proposal_async_response_input_required import (
    AcceptProposalInputRequired as AcceptProposalInputRequired,
)
from ._schemas.media_buy.accept_proposal_async_response_submitted import (
    AcceptProposalSubmitted as AcceptProposalSubmitted,
)
from ._schemas.media_buy.accept_proposal_async_response_working import (
    AcceptProposalWorking as AcceptProposalWorking,
)
from ._schemas.media_buy.accept_proposal_request import (
    AcceptProposalRequest as AcceptProposalRequest,
)
from ._schemas.media_buy.accept_proposal_response import (
    AcceptProposalResponse as AcceptProposalResponse,
)
from ._schemas.media_buy.acceptance_context import (
    AcceptanceContext as AcceptanceContext,
)
from ._schemas.media_buy.acceptance_policy_catalog import (
    AcceptancePolicyCatalog as AcceptancePolicyCatalog,
)
from ._schemas.media_buy.acceptance_policy_profile import (
    AcceptancePolicyProfile as AcceptancePolicyProfile,
)
from ._schemas.media_buy.acceptance_policy_profile_ref import (
    RegistryAcceptancePolicyProfileReference as RegistryAcceptancePolicyProfileReference,
)
from ._schemas.media_buy.acceptance_policy_requirement import (
    AcceptancePolicyRequirement as AcceptancePolicyRequirement,
    AcceptancePolicyRequirementAccountSetup as AcceptancePolicyRequirementAccountSetup,
    AcceptancePolicyRequirementAdvertiserEligibility as AcceptancePolicyRequirementAdvertiserEligibility,
    AcceptancePolicyRequirementAdvertiserVerification as AcceptancePolicyRequirementAdvertiserVerification,
    AcceptancePolicyRequirementCategoryDeclaration as AcceptancePolicyRequirementCategoryDeclaration,
    AcceptancePolicyRequirementCertification as AcceptancePolicyRequirementCertification,
    AcceptancePolicyRequirementCreativeRestriction as AcceptancePolicyRequirementCreativeRestriction,
    AcceptancePolicyRequirementCustom as AcceptancePolicyRequirementCustom,
    AcceptancePolicyRequirementDestinationRestriction as AcceptancePolicyRequirementDestinationRestriction,
    AcceptancePolicyRequirementDisclosure as AcceptancePolicyRequirementDisclosure,
    AcceptancePolicyRequirementFormatRestriction as AcceptancePolicyRequirementFormatRestriction,
    AcceptancePolicyRequirementFundingRestriction as AcceptancePolicyRequirementFundingRestriction,
    AcceptancePolicyRequirementLicense as AcceptancePolicyRequirementLicense,
    AcceptancePolicyRequirementPriorAuthorization as AcceptancePolicyRequirementPriorAuthorization,
    AcceptancePolicyRequirementSalesAssisted as AcceptancePolicyRequirementSalesAssisted,
    AcceptancePolicyRequirementTargetingRestriction as AcceptancePolicyRequirementTargetingRestriction,
    AcceptancePolicyRequirementTimeRestriction as AcceptancePolicyRequirementTimeRestriction,
    AcceptancePolicyRequirementTransparencyReporting as AcceptancePolicyRequirementTransparencyReporting,
)
from ._schemas.media_buy.acceptance_policy_rule import (
    AcceptancePolicyRule as AcceptancePolicyRule,
)
from ._schemas.media_buy.build_creative_async_response_input_required import (
    BuildCreativeInputRequired as BuildCreativeInputRequired,
)
from ._schemas.media_buy.build_creative_async_response_submitted import (
    BuildCreativeSubmitted as BuildCreativeSubmitted,
)
from ._schemas.media_buy.build_creative_async_response_working import (
    BuildCreativeWorking as BuildCreativeWorking,
)
from ._schemas.media_buy.build_creative_request import (
    BuildCreativeRequest as BuildCreativeRequest,
    SignalConditionsItemBinary as SignalConditionsItemBinary,
    SignalConditionsItemCategorical as SignalConditionsItemCategorical,
    SignalConditionsItemNumeric as SignalConditionsItemNumeric,
)
from ._schemas.media_buy.build_creative_response import (
    BuildCreativeError as BuildCreativeError,
    BuildCreativeEstimate as BuildCreativeEstimate,
    BuildCreativeMultiSuccess as BuildCreativeMultiSuccess,
    BuildCreativeResponse as BuildCreativeResponse,
    BuildCreativeResponseSubmitted as BuildCreativeResponseSubmitted,
    BuildCreativeSuccess as BuildCreativeSuccess,
    BuildCreativeVariantSuccess as BuildCreativeVariantSuccess,
)
from ._schemas.media_buy.buy_products_async_response_input_required import (
    BuyProductsInputRequired as BuyProductsInputRequired,
)
from ._schemas.media_buy.buy_products_async_response_submitted import (
    BuyProductsSubmitted as BuyProductsSubmitted,
)
from ._schemas.media_buy.buy_products_async_response_working import (
    BuyProductsWorking as BuyProductsWorking,
)
from ._schemas.media_buy.buy_products_request import (
    BuyProductsRequest as BuyProductsRequest,
    BuyProductsRequestBranch1 as BuyProductsRequestBranch1,
    BuyProductsRequestBranch1AccountAccountId as BuyProductsRequestBranch1AccountAccountId,
    BuyProductsRequestBranch1AccountBrandOperator as BuyProductsRequestBranch1AccountBrandOperator,
    BuyProductsRequestBrand as BuyProductsRequestBrand,
)
from ._schemas.media_buy.buy_products_response import (
    BuyProductsResponse as BuyProductsResponse,
)
from ._schemas.media_buy.change_term import (
    MediaBuyChangeTerm as MediaBuyChangeTerm,
)
from ._schemas.media_buy.change_term_constraints import (
    BudgetChangeConstraints as BudgetChangeConstraints,
    EffectiveTimingConstraints as EffectiveTimingConstraints,
    FlightChangeConstraints as FlightChangeConstraints,
    MediaBuyChangeTermConstraints as MediaBuyChangeTermConstraints,
    PackageCountConstraints as PackageCountConstraints,
)
from ._schemas.media_buy.commercial_terms import (
    CommercialTerms as CommercialTerms,
    Fee as Fee,
)
from ._schemas.media_buy.control_media_buy_async_response_input_required import (
    ControlMediaBuyInputRequired as ControlMediaBuyInputRequired,
)
from ._schemas.media_buy.control_media_buy_async_response_submitted import (
    ControlMediaBuySubmitted as ControlMediaBuySubmitted,
)
from ._schemas.media_buy.control_media_buy_async_response_working import (
    ControlMediaBuyWorking as ControlMediaBuyWorking,
)
from ._schemas.media_buy.control_media_buy_request import (
    ControlMediaBuyRequest as ControlMediaBuyRequest,
)
from ._schemas.media_buy.control_media_buy_response import (
    ControlApplied as ControlApplied,
    ControlError as ControlError,
    ControlMediaBuyResponse as ControlMediaBuyResponse,
    ControlSubmitted as ControlSubmitted,
)
from ._schemas.media_buy.create_media_buy_async_response_input_required import (
    CreateMediaBuyInputRequired as CreateMediaBuyInputRequired,
)
from ._schemas.media_buy.create_media_buy_async_response_submitted import (
    CreateMediaBuySubmitted as CreateMediaBuySubmitted,
)
from ._schemas.media_buy.create_media_buy_async_response_working import (
    CreateMediaBuyWorking as CreateMediaBuyWorking,
)
from ._schemas.media_buy.create_media_buy_request import (
    CommittedProposalExecution as CommittedProposalExecution,
    CreateMediaBuyRequest as CreateMediaBuyRequest,
    ExplicitPackagesWithFixedAllocation as ExplicitPackagesWithFixedAllocation,
    ExplicitPackagesWithSellerOptimizedAllocation as ExplicitPackagesWithSellerOptimizedAllocation,
)
from ._schemas.media_buy.create_media_buy_response import (
    CreateMediaBuyError as CreateMediaBuyError,
    CreateMediaBuyResponse as CreateMediaBuyResponse,
    CreateMediaBuyResponseSubmitted as CreateMediaBuyResponseSubmitted,
    CreateMediaBuySuccess as CreateMediaBuySuccess,
)
from ._schemas.media_buy.decline_proposals_async_response_input_required import (
    DeclineProposalsInputRequired as DeclineProposalsInputRequired,
)
from ._schemas.media_buy.decline_proposals_async_response_submitted import (
    DeclineProposalsSubmitted as DeclineProposalsSubmitted,
)
from ._schemas.media_buy.decline_proposals_async_response_working import (
    DeclineProposalsWorking as DeclineProposalsWorking,
)
from ._schemas.media_buy.decline_proposals_request import (
    DeclineProposalsRequest as DeclineProposalsRequest,
)
from ._schemas.media_buy.decline_proposals_response import (
    DeclineProposalsResponse as DeclineProposalsResponse,
    DeclineProposalsResponseResults as DeclineProposalsResponseResults,
    DeclineProposalsResponseResultsItemUnable as DeclineProposalsResponseResultsItemUnable,
    DeclineProposalsResponseSubmitted as DeclineProposalsResponseSubmitted,
    ResultsItemDeclined as ResultsItemDeclined,
)
from ._schemas.media_buy.get_media_buy_delivery_request import (
    GetMediaBuyDeliveryRequest as GetMediaBuyDeliveryRequest,
)
from ._schemas.media_buy.get_media_buy_delivery_response import (
    GetMediaBuyDeliveryResponse as GetMediaBuyDeliveryResponse,
)
from ._schemas.media_buy.get_media_buys_request import (
    GetMediaBuysRequest as GetMediaBuysRequest,
)
from ._schemas.media_buy.get_media_buys_response import (
    CreativeApprovalsItemIndicatorTypesEvaluatedItem as CreativeApprovalsItemIndicatorTypesEvaluatedItem,
    GetMediaBuysResponse as GetMediaBuysResponse,
    MediaBuysItemIndicatorsItemType as MediaBuysItemIndicatorsItemType,
    PackagesItemIndicatorsItemType as PackagesItemIndicatorsItemType,
)
from ._schemas.media_buy.get_products_async_response_input_required import (
    GetProductsInputRequired as GetProductsInputRequired,
)
from ._schemas.media_buy.get_products_async_response_submitted import (
    GetProductsSubmitted as GetProductsSubmitted,
)
from ._schemas.media_buy.get_products_async_response_working import (
    GetProductsWorking as GetProductsWorking,
)
from ._schemas.media_buy.get_products_rejected import (
    GetProductsRejected as GetProductsRejected,
)
from ._schemas.media_buy.get_products_request import (
    FieldsItem as FieldsItem,
    GetProductsRequest as GetProductsRequest,
    RefineItemProduct as RefineItemProduct,
    RefineItemProposal as RefineItemProposal,
    RefineItemRequest as RefineItemRequest,
)
from ._schemas.media_buy.get_products_response import (
    GetProductsResponse as GetProductsResponse,
    RefinementAppliedItemProduct as RefinementAppliedItemProduct,
    RefinementAppliedItemProductStatus as RefinementAppliedItemProductStatus,
    RefinementAppliedItemProposal as RefinementAppliedItemProposal,
    RefinementAppliedItemProposalStatus as RefinementAppliedItemProposalStatus,
    RefinementAppliedItemRequest as RefinementAppliedItemRequest,
)
from ._schemas.media_buy.get_products_targeting_resolution import (
    ProductDiscoveryTargetingResolution as ProductDiscoveryTargetingResolution,
)
from ._schemas.media_buy.get_reporting_status_request import (
    GetReportingStatusRequest as GetReportingStatusRequest,
)
from ._schemas.media_buy.get_reporting_status_response import (
    FailedLookup as FailedLookup,
    GetReportingStatusResponse as GetReportingStatusResponse,
    OperationalFailure as OperationalFailure,
    OperationalFailureView as OperationalFailureView,
    PeriodsView as PeriodsView,
    RevisionView as RevisionView,
    RevisionViewPagination as RevisionViewPagination,
    SuccessfulLookup as SuccessfulLookup,
    SummaryView as SummaryView,
    UnavailableLookup as UnavailableLookup,
)
from ._schemas.media_buy.legacy_purchase_continuation_input import (
    CompatibilityPurchaseCoordinatorInput as CompatibilityPurchaseCoordinatorInput,
)
from ._schemas.media_buy.list_creative_formats_request import (
    ListCreativeFormatsRequest as ListCreativeFormatsRequest,
)
from ._schemas.media_buy.list_creative_formats_response import (
    ListCreativeFormatsResponse as ListCreativeFormatsResponse,
)
from ._schemas.media_buy.list_products_request import (
    ListProductsRequest as ListProductsRequest,
)
from ._schemas.media_buy.list_products_response import (
    ListProductsResponse as ListProductsResponse,
    ListProductsResponseListed as ListProductsResponseListed,
    ListProductsResponseUnchanged as ListProductsResponseUnchanged,
)
from ._schemas.media_buy.log_event_request import (
    LogEventRequest as LogEventRequest,
)
from ._schemas.media_buy.log_event_response import (
    LogEventError as LogEventError,
    LogEventResponse as LogEventResponse,
    LogEventSuccess as LogEventSuccess,
)
from ._schemas.media_buy.media_buy_commitment_response import (
    CommitmentError as CommitmentError,
    CommitmentSubmitted as CommitmentSubmitted,
    CommittedMediaBuy as CommittedMediaBuy,
    MediaBuyCommitmentResponse as MediaBuyCommitmentResponse,
)
from ._schemas.media_buy.media_buy_delivery_webhook_result import (
    MediaBuyDeliveryWebhookResult as MediaBuyDeliveryWebhookResult,
)
from ._schemas.media_buy.outcome_target import (
    GoalEvent as GoalEvent,
    GoalMetric as GoalMetric,
    OutcomeTarget as OutcomeTarget,
)
from ._schemas.media_buy.package_control import (
    PackageControl as PackageControl,
)
from ._schemas.media_buy.package_request import (
    CommittedMetricsItemStandard as CommittedMetricsItemStandard,
    CommittedMetricsItemVendor as CommittedMetricsItemVendor,
    PackageRequest as PackageRequest,
)
from ._schemas.media_buy.package_update import (
    PackageUpdate as PackageUpdate,
)
from ._schemas.media_buy.product_discovery_criteria import (
    ProductDiscoveryCriteria as ProductDiscoveryCriteria,
)
from ._schemas.media_buy.product_fields import (
    ProductResponseFields as ProductResponseFields,
)
from ._schemas.media_buy.product_purchase import (
    AgencyEstimateNumber as AgencyEstimateNumber,
    AudienceEvidencePins as AudienceEvidencePins,
    Budget as Budget,
    CatalogIds as CatalogIds,
    DailyBudgetCap as DailyBudgetCap,
    EndTime as EndTime,
    FormatOptionRefs as FormatOptionRefs,
    MinSpendTarget as MinSpendTarget,
    OptimizationGoals as OptimizationGoals,
    PerformanceStandards as PerformanceStandards,
    PricingOptionId as PricingOptionId,
    ProductId as ProductId,
    ProductPurchase as ProductPurchase,
    StartTime as StartTime,
)
from ._schemas.media_buy.product_purchase_input import (
    ProductPurchaseInput as ProductPurchaseInput,
)
from ._schemas.media_buy.product_refinement import (
    ProductRefinementRequests as ProductRefinementRequests,
    ProductRefinementRequestsItemProduct as ProductRefinementRequestsItemProduct,
    ProductRefinementRequestsItemProposal as ProductRefinementRequestsItemProposal,
    ProductRefinementRequestsItemRequest as ProductRefinementRequestsItemRequest,
)
from ._schemas.media_buy.proposal_budget_constraint import (
    ProposalBudgetConstraint as ProposalBudgetConstraint,
)
from ._schemas.media_buy.proposal_decline import (
    ProposalDecline as ProposalDecline,
)
from ._schemas.media_buy.proposal_refinement import (
    ProposalRefinement as ProposalRefinement,
    ProposalRefinementFinalize as ProposalRefinementFinalize,
    ProposalRefinementRevise as ProposalRefinementRevise,
    ProposalRefinementReviseAlternatives as ProposalRefinementReviseAlternatives,
    ProposalRefinementReviseAsk as ProposalRefinementReviseAsk,
    ProposalRefinementReviseCancellation as ProposalRefinementReviseCancellation,
    ProposalRefinementReviseConstraints as ProposalRefinementReviseConstraints,
    ProposalRefinementReviseCriteria as ProposalRefinementReviseCriteria,
    ProposalRefinementReviseProductChanges as ProposalRefinementReviseProductChanges,
    ProposalRefinementReviseRemoveMediaBuyFrequencyCap as ProposalRefinementReviseRemoveMediaBuyFrequencyCap,
)
from ._schemas.media_buy.provide_performance_feedback_request import (
    ProvidePerformanceFeedbackRequest as ProvidePerformanceFeedbackRequest,
)
from ._schemas.media_buy.provide_performance_feedback_response import (
    ProvidePerformanceFeedbackError as ProvidePerformanceFeedbackError,
    ProvidePerformanceFeedbackResponse as ProvidePerformanceFeedbackResponse,
    ProvidePerformanceFeedbackSuccess as ProvidePerformanceFeedbackSuccess,
)
from ._schemas.media_buy.refine_proposals_async_response_input_required import (
    RefineProposalsInputRequired as RefineProposalsInputRequired,
)
from ._schemas.media_buy.refine_proposals_async_response_submitted import (
    RefineProposalsSubmitted as RefineProposalsSubmitted,
)
from ._schemas.media_buy.refine_proposals_async_response_working import (
    RefineProposalsWorking as RefineProposalsWorking,
)
from ._schemas.media_buy.refine_proposals_request import (
    RefineProposalsRequest as RefineProposalsRequest,
)
from ._schemas.media_buy.refine_proposals_response import (
    RefineProposalsResponse as RefineProposalsResponse,
    RefineProposalsResponseCompleted as RefineProposalsResponseCompleted,
    RefineProposalsResponseResultsItemUnable as RefineProposalsResponseResultsItemUnable,
    RefineProposalsResponseSubmitted as RefineProposalsResponseSubmitted,
    ResultsItemFinalized as ResultsItemFinalized,
    ResultsItemPartial as ResultsItemPartial,
    ResultsItemPartialProposalsItem as ResultsItemPartialProposalsItem,
    ResultsItemRevised as ResultsItemRevised,
)
from ._schemas.media_buy.request_proposals_async_response_input_required import (
    RequestProposalsInputRequired as RequestProposalsInputRequired,
)
from ._schemas.media_buy.request_proposals_async_response_submitted import (
    RequestProposalsSubmitted as RequestProposalsSubmitted,
)
from ._schemas.media_buy.request_proposals_async_response_working import (
    RequestProposalsWorking as RequestProposalsWorking,
)
from ._schemas.media_buy.request_proposals_request import (
    RequestProposalsRequest as RequestProposalsRequest,
    RequestProposalsRequestAccount as RequestProposalsRequestAccount,
    RequestProposalsRequestAccountAccountAccountId as RequestProposalsRequestAccountAccountAccountId,
    RequestProposalsRequestAccountAccountBrandOperator as RequestProposalsRequestAccountAccountBrandOperator,
    RequestProposalsRequestBrand as RequestProposalsRequestBrand,
)
from ._schemas.media_buy.request_proposals_response import (
    PurchaseContinuationLegacyCreate as PurchaseContinuationLegacyCreate,
    PurchaseContinuationListedPurchaseAccount as PurchaseContinuationListedPurchaseAccount,
    RequestProposalsResponse as RequestProposalsResponse,
    RequestProposalsResponseProductsAvailableCompleted as RequestProposalsResponseProductsAvailableCompleted,
    RequestProposalsResponseProposedCompleted as RequestProposalsResponseProposedCompleted,
    RequestProposalsResponseRejectedCompleted as RequestProposalsResponseRejectedCompleted,
    RequestProposalsResponseSubmitted as RequestProposalsResponseSubmitted,
)
from ._schemas.media_buy.sync_audiences_request import (
    SyncAudiencesRequest as SyncAudiencesRequest,
)
from ._schemas.media_buy.sync_audiences_response import (
    SyncAudiencesError as SyncAudiencesError,
    SyncAudiencesResponse as SyncAudiencesResponse,
    SyncAudiencesSubmitted as SyncAudiencesSubmitted,
    SyncAudiencesSuccess as SyncAudiencesSuccess,
)
from ._schemas.media_buy.sync_catalogs_async_response_input_required import (
    SyncCatalogsInputRequired as SyncCatalogsInputRequired,
)
from ._schemas.media_buy.sync_catalogs_async_response_submitted import (
    SyncCatalogsSubmitted as SyncCatalogsSubmitted,
)
from ._schemas.media_buy.sync_catalogs_async_response_working import (
    SyncCatalogsWorking as SyncCatalogsWorking,
)
from ._schemas.media_buy.sync_catalogs_request import (
    SyncCatalogsRequest as SyncCatalogsRequest,
)
from ._schemas.media_buy.sync_catalogs_response import (
    SyncCatalogsError as SyncCatalogsError,
    SyncCatalogsResponse as SyncCatalogsResponse,
    SyncCatalogsResponseSubmitted as SyncCatalogsResponseSubmitted,
    SyncCatalogsSuccess as SyncCatalogsSuccess,
)
from ._schemas.media_buy.sync_event_sources_request import (
    SyncEventSourcesRequest as SyncEventSourcesRequest,
)
from ._schemas.media_buy.sync_event_sources_response import (
    SyncEventSourcesError as SyncEventSourcesError,
    SyncEventSourcesResponse as SyncEventSourcesResponse,
    SyncEventSourcesSuccess as SyncEventSourcesSuccess,
)
from ._schemas.media_buy.sync_reporting_receipts_request import (
    SyncReportingReceiptsRequest as SyncReportingReceiptsRequest,
)
from ._schemas.media_buy.sync_reporting_receipts_response import (
    FailedReportingReceipt as FailedReportingReceipt,
    RecordedReportingAdjustmentReceipt as RecordedReportingAdjustmentReceipt,
    RecordedReportingReceipt as RecordedReportingReceipt,
    SyncReportingReceiptsResponse as SyncReportingReceiptsResponse,
    UnchangedReportingAdjustmentReceipt as UnchangedReportingAdjustmentReceipt,
    UnchangedReportingAdjustmentReceiptAdjustmentReceipt as UnchangedReportingAdjustmentReceiptAdjustmentReceipt,
    UnchangedReportingReceipt as UnchangedReportingReceipt,
    UnchangedReportingReceiptReceipt as UnchangedReportingReceiptReceipt,
)
from ._schemas.media_buy.sync_reporting_status_request import (
    SyncReportingStatusRequest as SyncReportingStatusRequest,
)
from ._schemas.media_buy.sync_reporting_status_response import (
    FailedReportingConsumerStatus as FailedReportingConsumerStatus,
    RecordedReportingConsumerStatus as RecordedReportingConsumerStatus,
    SyncReportingStatusResponse as SyncReportingStatusResponse,
    UnchangedReportingConsumerStatus as UnchangedReportingConsumerStatus,
    UnchangedReportingConsumerStatusConsumerStatus as UnchangedReportingConsumerStatusConsumerStatus,
)
from ._schemas.media_buy.update_media_buy_async_response_input_required import (
    UpdateMediaBuyInputRequired as UpdateMediaBuyInputRequired,
)
from ._schemas.media_buy.update_media_buy_async_response_submitted import (
    UpdateMediaBuySubmitted as UpdateMediaBuySubmitted,
)
from ._schemas.media_buy.update_media_buy_async_response_working import (
    UpdateMediaBuyWorking as UpdateMediaBuyWorking,
)
from ._schemas.media_buy.update_media_buy_request import (
    UpdateMediaBuyRequest as UpdateMediaBuyRequest,
)
from ._schemas.media_buy.update_media_buy_response import (
    UpdateMediaBuyError as UpdateMediaBuyError,
    UpdateMediaBuyResponse as UpdateMediaBuyResponse,
    UpdateMediaBuyResponseSubmitted as UpdateMediaBuyResponseSubmitted,
    UpdateMediaBuySuccess as UpdateMediaBuySuccess,
)

__all__ = [
    'AcceptProposalInputRequired',
    'AcceptProposalRequest',
    'AcceptProposalResponse',
    'AcceptProposalSubmitted',
    'AcceptProposalWorking',
    'AcceptanceContext',
    'AcceptancePolicyCatalog',
    'AcceptancePolicyProfile',
    'AcceptancePolicyRequirement',
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
    'AgencyEstimateNumber',
    'AudienceEvidencePins',
    'Budget',
    'BudgetChangeConstraints',
    'BuildCreativeError',
    'BuildCreativeEstimate',
    'BuildCreativeInputRequired',
    'BuildCreativeMultiSuccess',
    'BuildCreativeRequest',
    'BuildCreativeResponse',
    'BuildCreativeResponseSubmitted',
    'BuildCreativeSubmitted',
    'BuildCreativeSuccess',
    'BuildCreativeVariantSuccess',
    'BuildCreativeWorking',
    'BuyProductsInputRequired',
    'BuyProductsRequest',
    'BuyProductsRequestBranch1',
    'BuyProductsRequestBranch1AccountAccountId',
    'BuyProductsRequestBranch1AccountBrandOperator',
    'BuyProductsRequestBrand',
    'BuyProductsResponse',
    'BuyProductsSubmitted',
    'BuyProductsWorking',
    'CatalogIds',
    'CommercialTerms',
    'CommitmentError',
    'CommitmentSubmitted',
    'CommittedMediaBuy',
    'CommittedMetricsItemStandard',
    'CommittedMetricsItemVendor',
    'CommittedProposalExecution',
    'CompatibilityPurchaseCoordinatorInput',
    'ControlApplied',
    'ControlError',
    'ControlMediaBuyInputRequired',
    'ControlMediaBuyRequest',
    'ControlMediaBuyResponse',
    'ControlMediaBuySubmitted',
    'ControlMediaBuyWorking',
    'ControlSubmitted',
    'CreateMediaBuyError',
    'CreateMediaBuyInputRequired',
    'CreateMediaBuyRequest',
    'CreateMediaBuyResponse',
    'CreateMediaBuyResponseSubmitted',
    'CreateMediaBuySubmitted',
    'CreateMediaBuySuccess',
    'CreateMediaBuyWorking',
    'CreativeApprovalsItemIndicatorTypesEvaluatedItem',
    'DailyBudgetCap',
    'DeclineProposalsInputRequired',
    'DeclineProposalsRequest',
    'DeclineProposalsResponse',
    'DeclineProposalsResponseResults',
    'DeclineProposalsResponseResultsItemUnable',
    'DeclineProposalsResponseSubmitted',
    'DeclineProposalsSubmitted',
    'DeclineProposalsWorking',
    'EffectiveTimingConstraints',
    'EndTime',
    'ExplicitPackagesWithFixedAllocation',
    'ExplicitPackagesWithSellerOptimizedAllocation',
    'FailedLookup',
    'FailedReportingConsumerStatus',
    'FailedReportingReceipt',
    'Fee',
    'FieldsItem',
    'FlightChangeConstraints',
    'FormatOptionRefs',
    'GetMediaBuyDeliveryRequest',
    'GetMediaBuyDeliveryResponse',
    'GetMediaBuysRequest',
    'GetMediaBuysResponse',
    'GetProductsInputRequired',
    'GetProductsRejected',
    'GetProductsRequest',
    'GetProductsResponse',
    'GetProductsSubmitted',
    'GetProductsWorking',
    'GetReportingStatusRequest',
    'GetReportingStatusResponse',
    'GoalEvent',
    'GoalMetric',
    'ListCreativeFormatsRequest',
    'ListCreativeFormatsResponse',
    'ListProductsRequest',
    'ListProductsResponse',
    'ListProductsResponseListed',
    'ListProductsResponseUnchanged',
    'LogEventError',
    'LogEventRequest',
    'LogEventResponse',
    'LogEventSuccess',
    'MediaBuyChangeTerm',
    'MediaBuyChangeTermConstraints',
    'MediaBuyCommitmentResponse',
    'MediaBuyDeliveryWebhookResult',
    'MediaBuysItemIndicatorsItemType',
    'MinSpendTarget',
    'OperationalFailure',
    'OperationalFailureView',
    'OptimizationGoals',
    'OutcomeTarget',
    'PackageControl',
    'PackageCountConstraints',
    'PackageRequest',
    'PackageUpdate',
    'PackagesItemIndicatorsItemType',
    'PerformanceStandards',
    'PeriodsView',
    'PricingOptionId',
    'ProductDiscoveryCriteria',
    'ProductDiscoveryTargetingResolution',
    'ProductId',
    'ProductPurchase',
    'ProductPurchaseInput',
    'ProductRefinementRequests',
    'ProductRefinementRequestsItemProduct',
    'ProductRefinementRequestsItemProposal',
    'ProductRefinementRequestsItemRequest',
    'ProductResponseFields',
    'ProposalBudgetConstraint',
    'ProposalDecline',
    'ProposalRefinement',
    'ProposalRefinementFinalize',
    'ProposalRefinementRevise',
    'ProposalRefinementReviseAlternatives',
    'ProposalRefinementReviseAsk',
    'ProposalRefinementReviseCancellation',
    'ProposalRefinementReviseConstraints',
    'ProposalRefinementReviseCriteria',
    'ProposalRefinementReviseProductChanges',
    'ProposalRefinementReviseRemoveMediaBuyFrequencyCap',
    'ProvidePerformanceFeedbackError',
    'ProvidePerformanceFeedbackRequest',
    'ProvidePerformanceFeedbackResponse',
    'ProvidePerformanceFeedbackSuccess',
    'PurchaseContinuationLegacyCreate',
    'PurchaseContinuationListedPurchaseAccount',
    'RecordedReportingAdjustmentReceipt',
    'RecordedReportingConsumerStatus',
    'RecordedReportingReceipt',
    'RefineItemProduct',
    'RefineItemProposal',
    'RefineItemRequest',
    'RefineProposalsInputRequired',
    'RefineProposalsRequest',
    'RefineProposalsResponse',
    'RefineProposalsResponseCompleted',
    'RefineProposalsResponseResultsItemUnable',
    'RefineProposalsResponseSubmitted',
    'RefineProposalsSubmitted',
    'RefineProposalsWorking',
    'RefinementAppliedItemProduct',
    'RefinementAppliedItemProductStatus',
    'RefinementAppliedItemProposal',
    'RefinementAppliedItemProposalStatus',
    'RefinementAppliedItemRequest',
    'RegistryAcceptancePolicyProfileReference',
    'RequestProposalsInputRequired',
    'RequestProposalsRequest',
    'RequestProposalsRequestAccount',
    'RequestProposalsRequestAccountAccountAccountId',
    'RequestProposalsRequestAccountAccountBrandOperator',
    'RequestProposalsRequestBrand',
    'RequestProposalsResponse',
    'RequestProposalsResponseProductsAvailableCompleted',
    'RequestProposalsResponseProposedCompleted',
    'RequestProposalsResponseRejectedCompleted',
    'RequestProposalsResponseSubmitted',
    'RequestProposalsSubmitted',
    'RequestProposalsWorking',
    'ResultsItemDeclined',
    'ResultsItemFinalized',
    'ResultsItemPartial',
    'ResultsItemPartialProposalsItem',
    'ResultsItemRevised',
    'RevisionView',
    'RevisionViewPagination',
    'SignalConditionsItemBinary',
    'SignalConditionsItemCategorical',
    'SignalConditionsItemNumeric',
    'StartTime',
    'SuccessfulLookup',
    'SummaryView',
    'SyncAudiencesError',
    'SyncAudiencesRequest',
    'SyncAudiencesResponse',
    'SyncAudiencesSubmitted',
    'SyncAudiencesSuccess',
    'SyncCatalogsError',
    'SyncCatalogsInputRequired',
    'SyncCatalogsRequest',
    'SyncCatalogsResponse',
    'SyncCatalogsResponseSubmitted',
    'SyncCatalogsSubmitted',
    'SyncCatalogsSuccess',
    'SyncCatalogsWorking',
    'SyncEventSourcesError',
    'SyncEventSourcesRequest',
    'SyncEventSourcesResponse',
    'SyncEventSourcesSuccess',
    'SyncReportingReceiptsRequest',
    'SyncReportingReceiptsResponse',
    'SyncReportingStatusRequest',
    'SyncReportingStatusResponse',
    'UnavailableLookup',
    'UnchangedReportingAdjustmentReceipt',
    'UnchangedReportingAdjustmentReceiptAdjustmentReceipt',
    'UnchangedReportingConsumerStatus',
    'UnchangedReportingConsumerStatusConsumerStatus',
    'UnchangedReportingReceipt',
    'UnchangedReportingReceiptReceipt',
    'UpdateMediaBuyError',
    'UpdateMediaBuyInputRequired',
    'UpdateMediaBuyRequest',
    'UpdateMediaBuyResponse',
    'UpdateMediaBuyResponseSubmitted',
    'UpdateMediaBuySubmitted',
    'UpdateMediaBuySuccess',
    'UpdateMediaBuyWorking',
]
