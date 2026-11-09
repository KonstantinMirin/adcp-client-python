"""The exports of the ``trusted_match`` domain, as the compiler aggregates them.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  The object is the same one the runtime validates into -- ``isinstance``
against a union branch imported from here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.

**NOT the path a consumer writes.**  This file is the compiler's outright and is
compared byte for byte, so that the domain's PUBLIC module can compose it in one
line and serve a hand-written name set beside it where the domain's word is also a
word upstream kept machinery under.  The public module is the one import path for
every name here.
"""

from __future__ import annotations

from .._schemas.trusted_match.available_package import AvailablePackage as AvailablePackage
from .._schemas.trusted_match.context_match_request import ArtifactRefsItem as ContextMatchRequestArtifactRefsItem
from .._schemas.trusted_match.context_match_request import (
    ArtifactRefsItemType as ContextMatchRequestArtifactRefsItemType,
)
from .._schemas.trusted_match.context_match_request import ContextMatchRequest as ContextMatchRequest
from .._schemas.trusted_match.context_match_request import ContextSignals as ContextMatchRequestContextSignals
from .._schemas.trusted_match.context_match_request import Geo as ContextMatchRequestGeo
from .._schemas.trusted_match.context_match_request import Metro as ContextMatchRequestGeoMetro
from .._schemas.trusted_match.context_match_request import Sentiment as ContextMatchRequestContextSignalsSentiment
from .._schemas.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisher as ContextMatchResponseRouterPublisher,
)
from .._schemas.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisherTargetingKvs as ContextMatchResponseRouterPublisherTargetingKvs,
)
from .._schemas.trusted_match.context_match_response import (
    ObjKeyValue as ContextMatchResponseRouterPublisherTargetingKvsItem,
)
from .._schemas.trusted_match.context_match_response import Signals as ContextMatchResponseRouterPublisherSignals
from .._schemas.trusted_match.context_match_response import (
    SignalsByProviderValue as ContextMatchResponseRouterPublisherSignalsByProviderValue,
)
from .._schemas.trusted_match.error import Code as TMPErrorCode
from .._schemas.trusted_match.error import TMPError as TMPError
from .._schemas.trusted_match.identity_match_request import Attestation as IdentityMatchRequestIdentitiesItemAttestation
from .._schemas.trusted_match.identity_match_request import Consent as IdentityMatchRequestConsent
from .._schemas.trusted_match.identity_match_request import IdentitiesItem as IdentityMatchRequestIdentitiesItem
from .._schemas.trusted_match.identity_match_request import IdentityMatchRequest as IdentityMatchRequest
from .._schemas.trusted_match.identity_match_request import (
    SealedCredentialsItem as IdentityMatchRequestSealedCredentialsItem,
)
from .._schemas.trusted_match.identity_match_request import (
    VerificationLevel as IdentityMatchRequestIdentitiesItemAttestationVerificationLevel,
)
from .._schemas.trusted_match.identity_match_response import (
    IdentityMatchResponseRouterPublisher as IdentityMatchResponseRouterPublisher,
)
from .._schemas.trusted_match.identity_match_response import (
    TmpxProvidersValue as IdentityMatchResponseRouterPublisherTmpxProvidersValue,
)
from .._schemas.trusted_match.offer import Offer as Offer
from .._schemas.trusted_match.offer_price import Model as OfferPriceModel
from .._schemas.trusted_match.offer_price import OfferPrice as OfferPrice
from .._schemas.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouter as ContextMatchResponseProviderRouter,
)
from .._schemas.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouterTargetingKvs as ContextMatchResponseProviderRouterTargetingKvs,
)
from .._schemas.trusted_match.provider_context_match_response import (
    Signals as ContextMatchResponseProviderRouterSignals,
)
from .._schemas.trusted_match.provider_identity_match_response import (
    IdentityMatchResponseProviderRouter as IdentityMatchResponseProviderRouter,
)
from .._schemas.trusted_match.provider_registration import Status as TMPProviderRegistrationStatus
from .._schemas.trusted_match.provider_registration import TMPProviderRegistration as TMPProviderRegistration
from .._schemas.trusted_match.provider_registration import (
    TMPProviderRegistrationContextMatch as TMPProviderRegistrationContextMatch,
)
from .._schemas.trusted_match.provider_registration import (
    TMPProviderRegistrationIdentityMatch as TMPProviderRegistrationIdentityMatch,
)
from .._schemas.trusted_match.publisher_targeting_kv_config import (
    PublisherTargetingKVMapping as PublisherTargetingKVMapping,
)
from .._schemas.trusted_match.publisher_targeting_kv_config import TargetingKvMappingValue as TargetingKvMappingValue
from .._schemas.trusted_match.publisher_tmpx_config import PublisherTMPXMacroMapping as PublisherTMPXMacroMapping
from .._schemas.trusted_match.publisher_tmpx_config import TmpxMacroMappingValue as TmpxMacroMappingValue
from .._schemas.trusted_match.tmpx_chunk import TMPXChunk as TMPXChunk

__all__ = [
    'AvailablePackage',
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
    'IdentityMatchRequest',
    'IdentityMatchRequestConsent',
    'IdentityMatchRequestIdentitiesItem',
    'IdentityMatchRequestIdentitiesItemAttestation',
    'IdentityMatchRequestIdentitiesItemAttestationVerificationLevel',
    'IdentityMatchRequestSealedCredentialsItem',
    'IdentityMatchResponseProviderRouter',
    'IdentityMatchResponseRouterPublisher',
    'IdentityMatchResponseRouterPublisherTmpxProvidersValue',
    'Offer',
    'OfferPrice',
    'OfferPriceModel',
    'PublisherTMPXMacroMapping',
    'PublisherTargetingKVMapping',
    'TMPError',
    'TMPErrorCode',
    'TMPProviderRegistration',
    'TMPProviderRegistrationContextMatch',
    'TMPProviderRegistrationIdentityMatch',
    'TMPProviderRegistrationStatus',
    'TMPXChunk',
    'TargetingKvMappingValue',
    'TmpxMacroMappingValue',
]
