"""The public types of the ``sponsored_intelligence`` domain.

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

from ._schemas.sponsored_intelligence.si_capabilities import A2ui as SICapabilitiesA2ui
from ._schemas.sponsored_intelligence.si_capabilities import Avatar as Avatar
from ._schemas.sponsored_intelligence.si_capabilities import Commerce as SICapabilitiesCommerce
from ._schemas.sponsored_intelligence.si_capabilities import Components as SICapabilitiesComponents
from ._schemas.sponsored_intelligence.si_capabilities import Modalities as SICapabilitiesModalities
from ._schemas.sponsored_intelligence.si_capabilities import SICapabilities as SICapabilities
from ._schemas.sponsored_intelligence.si_capabilities import StandardItem as SICapabilitiesComponentsStandardItem
from ._schemas.sponsored_intelligence.si_capabilities import Video as Video
from ._schemas.sponsored_intelligence.si_capabilities import Voice as Voice
from ._schemas.sponsored_intelligence.si_context_use import SIContextUse as SIContextUse
from ._schemas.sponsored_intelligence.si_get_offering_request import SIGetOfferingRequest as SIGetOfferingRequest
from ._schemas.sponsored_intelligence.si_get_offering_response import (
    MatchingProductsItem as SIGetOfferingResponseMatchingProductsItem,
)
from ._schemas.sponsored_intelligence.si_get_offering_response import SIGetOfferingResponse as SIGetOfferingResponse
from ._schemas.sponsored_intelligence.si_get_offering_response import (
    SIGetOfferingResponseOffering as SIGetOfferingResponseOffering,
)
from ._schemas.sponsored_intelligence.si_identity import ConsentScopeItem as SIIdentityConsentScopeItem
from ._schemas.sponsored_intelligence.si_identity import (
    PrivacyPolicyAcknowledged as SIIdentityPrivacyPolicyAcknowledged,
)
from ._schemas.sponsored_intelligence.si_identity import ShippingAddress as SIIdentityUserShippingAddress
from ._schemas.sponsored_intelligence.si_identity import SIIdentity as SIIdentity
from ._schemas.sponsored_intelligence.si_identity import User as SIIdentityUser
from ._schemas.sponsored_intelligence.si_initiate_session_request import (
    SIInitiateSessionRequest as SIInitiateSessionRequest,
)
from ._schemas.sponsored_intelligence.si_initiate_session_response import Response as SIInitiateSessionResponseResponse
from ._schemas.sponsored_intelligence.si_initiate_session_response import (
    SIInitiateSessionResponse as SIInitiateSessionResponse,
)
from ._schemas.sponsored_intelligence.si_send_message_request import (
    ActionResponse as SISendMessageRequestActionResponse,
)
from ._schemas.sponsored_intelligence.si_send_message_request import SISendMessageRequest as SISendMessageRequest
from ._schemas.sponsored_intelligence.si_send_message_response import (
    ContextForCheckout as SISendMessageResponseHandoffContextForCheckout,
)
from ._schemas.sponsored_intelligence.si_send_message_response import Handoff as SISendMessageResponseHandoff
from ._schemas.sponsored_intelligence.si_send_message_response import HandoffType as SISendMessageResponseHandoffType
from ._schemas.sponsored_intelligence.si_send_message_response import Intent as SISendMessageResponseHandoffIntent
from ._schemas.sponsored_intelligence.si_send_message_response import (
    IntentPrice as SISendMessageResponseHandoffIntentPrice,
)
from ._schemas.sponsored_intelligence.si_send_message_response import Response as SISendMessageResponseResponse
from ._schemas.sponsored_intelligence.si_send_message_response import SISendMessageResponse as SISendMessageResponse
from ._schemas.sponsored_intelligence.si_sponsored_context import DeclaredBy as SISponsoredContextDeclaredBy
from ._schemas.sponsored_intelligence.si_sponsored_context import (
    DisclosureObligation as SISponsoredContextDisclosureObligation,
)
from ._schemas.sponsored_intelligence.si_sponsored_context import (
    JurisdictionsItem as SISponsoredContextDisclosureObligationJurisdictionsItem,
)
from ._schemas.sponsored_intelligence.si_sponsored_context import PayingPrincipal as SISponsoredContextPayingPrincipal
from ._schemas.sponsored_intelligence.si_sponsored_context import (
    PayingPrincipalAccount as SISponsoredContextPayingPrincipalAccount,
)
from ._schemas.sponsored_intelligence.si_sponsored_context import (
    Proximity as SISponsoredContextDisclosureObligationProximity,
)
from ._schemas.sponsored_intelligence.si_sponsored_context import Role as SISponsoredContextDeclaredByRole
from ._schemas.sponsored_intelligence.si_sponsored_context import SISponsoredContext as SISponsoredContext
from ._schemas.sponsored_intelligence.si_sponsored_context import Timing as SISponsoredContextDisclosureObligationTiming
from ._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    DisclosureCommitment as SISponsoredContextReceiptHostReceiptDisclosureCommitment,
)
from ._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    DisclosureCommitmentStatus as SISponsoredContextReceiptHostReceiptDisclosureCommitmentStatus,
)
from ._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    HostReceipt as SISponsoredContextReceiptHostReceipt,
)
from ._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    HostReceiptStatus as SISponsoredContextReceiptHostReceiptStatus,
)
from ._schemas.sponsored_intelligence.si_sponsored_context_receipt import (
    SISponsoredContextReceipt as SISponsoredContextReceipt,
)
from ._schemas.sponsored_intelligence.si_terminate_session_request import (
    Action as SITerminateSessionRequestTerminationContextTransactionIntentAction,
)
from ._schemas.sponsored_intelligence.si_terminate_session_request import Reason as SITerminateSessionRequestReason
from ._schemas.sponsored_intelligence.si_terminate_session_request import (
    SITerminateSessionRequest as SITerminateSessionRequest,
)
from ._schemas.sponsored_intelligence.si_terminate_session_request import (
    TerminationContext as SITerminateSessionRequestTerminationContext,
)
from ._schemas.sponsored_intelligence.si_terminate_session_request import (
    TransactionIntent as SITerminateSessionRequestTerminationContextTransactionIntent,
)
from ._schemas.sponsored_intelligence.si_terminate_session_response import (
    AcpHandoff as SITerminateSessionResponseAcpHandoff,
)
from ._schemas.sponsored_intelligence.si_terminate_session_response import (
    Action as SITerminateSessionResponseFollowUpAction,
)
from ._schemas.sponsored_intelligence.si_terminate_session_response import (
    FollowUp as SITerminateSessionResponseFollowUp,
)
from ._schemas.sponsored_intelligence.si_terminate_session_response import (
    SITerminateSessionResponse as SITerminateSessionResponse,
)
from ._schemas.sponsored_intelligence.si_ui_element import SIUIElement as SIUIElement
from ._schemas.sponsored_intelligence.si_ui_element import SIUIElementType as SIUIElementType

__all__ = [
    'Avatar',
    'SICapabilities',
    'SICapabilitiesA2ui',
    'SICapabilitiesCommerce',
    'SICapabilitiesComponents',
    'SICapabilitiesComponentsStandardItem',
    'SICapabilitiesModalities',
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
    'Video',
    'Voice',
]
