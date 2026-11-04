"""The public types of the ``error_details`` domain.

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

from ._schemas.error_details.accessibility_violation import (
    AccessibilityViolationDetails as AccessibilityViolationDetails,
)
from ._schemas.error_details.accessibility_violation import FailureKind as FailureKind
from ._schemas.error_details.account_moved import AccountMovedDetails as AccountMovedDetails
from ._schemas.error_details.account_setup_required import AccountSetupRequiredDetails as AccountSetupRequiredDetails
from ._schemas.error_details.action_not_allowed import ActionNotAllowedDetails as ActionNotAllowedDetails
from ._schemas.error_details.agent_permission_denied import AgentPermissionDeniedDetails as AgentPermissionDeniedDetails
from ._schemas.error_details.audience_too_small import AudienceTooSmallDetails as AudienceTooSmallDetails
from ._schemas.error_details.authorization_required import AuthorizationRequiredDetails as AuthorizationRequiredDetails
from ._schemas.error_details.billing_not_permitted_for_agent import (
    BillingNotPermittedForAgentDetails as BillingNotPermittedForAgentDetails,
)
from ._schemas.error_details.billing_not_supported import BillingNotSupportedDetails as BillingNotSupportedDetails
from ._schemas.error_details.budget_too_low import BudgetTooLowDetails as BudgetTooLowDetails
from ._schemas.error_details.conflict import ConflictDetails as ConflictDetails
from ._schemas.error_details.creative_rejected import CreativeRejectedDetails as CreativeRejectedDetails
from ._schemas.error_details.creative_representation_unresolved import (
    CreativeRepresentationUnresolvedDetails as CreativeRepresentationUnresolvedDetails,
)
from ._schemas.error_details.creative_revision_content_mismatch import (
    CreativeRevisionContentMismatchDetails as CreativeRevisionContentMismatchDetails,
)
from ._schemas.error_details.execution_requirement_unmet import (
    ExecutionRequirementUnmetDetails as ExecutionRequirementUnmetDetails,
)
from ._schemas.error_details.governance_agent_not_accepted import (
    GovernanceAgentNotAcceptedDetails as GovernanceAgentNotAcceptedDetails,
)
from ._schemas.error_details.governance_agent_not_accepted import (
    GovernanceAgentNotAcceptedDetailsDisclosed as GovernanceAgentNotAcceptedDetailsDisclosed,
)
from ._schemas.error_details.governance_agent_not_accepted import (
    GovernanceAgentNotAcceptedDetailsOpaque as GovernanceAgentNotAcceptedDetailsOpaque,
)
from ._schemas.error_details.macro_resolution_failed import MacroResolutionFailedDetails as MacroResolutionFailedDetails
from ._schemas.error_details.policy_violation import PolicyViolationDetails as PolicyViolationDetails
from ._schemas.error_details.rate_limited import RateLimitedDetails as RateLimitedDetails
from ._schemas.error_details.requote_required import RequoteRequiredDetails as RequoteRequiredDetails
from ._schemas.error_details.stale_response import StaleResponseDetails as StaleResponseDetails
from ._schemas.error_details.unsupported_refinement_dimension import (
    UnsupportedRefinementDimensionDetails as UnsupportedRefinementDimensionDetails,
)
from ._schemas.error_details.vast_version_mismatch import (
    AssetOutsideAcceptedVersionIntersection as AssetOutsideAcceptedVersionIntersection,
)
from ._schemas.error_details.vast_version_mismatch import (
    InspectedDocumentVersionMismatch as InspectedDocumentVersionMismatch,
)
from ._schemas.error_details.vast_version_mismatch import (
    SupportedVersionsCompatibilityDetails as SupportedVersionsCompatibilityDetails,
)
from ._schemas.error_details.vast_version_mismatch import VASTVersionMismatchDetails as VASTVersionMismatchDetails
from ._schemas.error_details.vendor_error_codes import VendorErrorCodeRegistry as VendorErrorCodeRegistry
from ._schemas.error_details.version_unsupported import VersionUnsupportedDetails as VersionUnsupportedDetails

__all__ = [
    'AccessibilityViolationDetails',
    'AccountMovedDetails',
    'AccountSetupRequiredDetails',
    'ActionNotAllowedDetails',
    'AgentPermissionDeniedDetails',
    'AssetOutsideAcceptedVersionIntersection',
    'AudienceTooSmallDetails',
    'AuthorizationRequiredDetails',
    'BillingNotPermittedForAgentDetails',
    'BillingNotSupportedDetails',
    'BudgetTooLowDetails',
    'ConflictDetails',
    'CreativeRejectedDetails',
    'CreativeRepresentationUnresolvedDetails',
    'CreativeRevisionContentMismatchDetails',
    'ExecutionRequirementUnmetDetails',
    'FailureKind',
    'GovernanceAgentNotAcceptedDetails',
    'GovernanceAgentNotAcceptedDetailsDisclosed',
    'GovernanceAgentNotAcceptedDetailsOpaque',
    'InspectedDocumentVersionMismatch',
    'MacroResolutionFailedDetails',
    'PolicyViolationDetails',
    'RateLimitedDetails',
    'RequoteRequiredDetails',
    'StaleResponseDetails',
    'SupportedVersionsCompatibilityDetails',
    'UnsupportedRefinementDimensionDetails',
    'VASTVersionMismatchDetails',
    'VendorErrorCodeRegistry',
    'VersionUnsupportedDetails',
]
