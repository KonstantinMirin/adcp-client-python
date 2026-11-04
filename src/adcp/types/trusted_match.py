"""The public types of the ``trusted_match`` domain.

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

from ._schemas.trusted_match.available_package import AvailablePackage as AvailablePackage
from ._schemas.trusted_match.context_match_request import ContextMatchRequest as ContextMatchRequest
from ._schemas.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisher as ContextMatchResponseRouterPublisher,
)
from ._schemas.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisherTargetingKvs as ContextMatchResponseRouterPublisherTargetingKvs,
)
from ._schemas.trusted_match.error import TMPError as TMPError
from ._schemas.trusted_match.identity_match_request import IdentityMatchRequest as IdentityMatchRequest
from ._schemas.trusted_match.identity_match_response import (
    IdentityMatchResponseRouterPublisher as IdentityMatchResponseRouterPublisher,
)
from ._schemas.trusted_match.offer import Offer as Offer
from ._schemas.trusted_match.offer_price import OfferPrice as OfferPrice
from ._schemas.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouter as ContextMatchResponseProviderRouter,
)
from ._schemas.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouterTargetingKvs as ContextMatchResponseProviderRouterTargetingKvs,
)
from ._schemas.trusted_match.provider_identity_match_response import (
    IdentityMatchResponseProviderRouter as IdentityMatchResponseProviderRouter,
)
from ._schemas.trusted_match.provider_registration import TMPProviderRegistration as TMPProviderRegistration
from ._schemas.trusted_match.provider_registration import (
    TMPProviderRegistrationContextMatch as TMPProviderRegistrationContextMatch,
)
from ._schemas.trusted_match.provider_registration import (
    TMPProviderRegistrationIdentityMatch as TMPProviderRegistrationIdentityMatch,
)
from ._schemas.trusted_match.publisher_targeting_kv_config import (
    PublisherTargetingKVMapping as PublisherTargetingKVMapping,
)
from ._schemas.trusted_match.publisher_targeting_kv_config import TargetingKvMappingValue as TargetingKvMappingValue
from ._schemas.trusted_match.publisher_tmpx_config import PublisherTMPXMacroMapping as PublisherTMPXMacroMapping
from ._schemas.trusted_match.publisher_tmpx_config import TmpxMacroMappingValue as TmpxMacroMappingValue
from ._schemas.trusted_match.tmpx_chunk import TMPXChunk as TMPXChunk

__all__ = [
    'AvailablePackage',
    'ContextMatchRequest',
    'ContextMatchResponseProviderRouter',
    'ContextMatchResponseProviderRouterTargetingKvs',
    'ContextMatchResponseRouterPublisher',
    'ContextMatchResponseRouterPublisherTargetingKvs',
    'IdentityMatchRequest',
    'IdentityMatchResponseProviderRouter',
    'IdentityMatchResponseRouterPublisher',
    'Offer',
    'OfferPrice',
    'PublisherTMPXMacroMapping',
    'PublisherTargetingKVMapping',
    'TMPError',
    'TMPProviderRegistration',
    'TMPProviderRegistrationContextMatch',
    'TMPProviderRegistrationIdentityMatch',
    'TMPXChunk',
    'TargetingKvMappingValue',
    'TmpxMacroMappingValue',
]
