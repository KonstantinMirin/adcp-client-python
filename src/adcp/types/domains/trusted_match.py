"""Types the AdCP ``trusted_match`` schemas declare.

Importing from the domain says which variant you mean, where the flat
``adcp.types`` namespace can only bind one class per name:

    from adcp.types.domains.trusted_match import <Type>

A type this domain declares in more than one schema carries the defining
file in its name (``CreativeFromListCreativesResponse``); everything else
keeps the name codegen gave it.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.trusted_match.available_package import AvailablePackage
from adcp.types.generated_poc.trusted_match.context_match_request import (
    ArtifactRef,
    ContextMatchRequest,
    ContextSignals,
    Geo,
    Keyword,
    Metro,
    Sentiment,
    Type,
)
from adcp.types.generated_poc.trusted_match.context_match_response import (
    ContextMatchResponseRouterPublisher,
    Signals as SignalsFromContextMatchResponse,
    SignalsByProvider,
    TargetingKv as TargetingKvFromContextMatchResponse,
    TargetingKvs as TargetingKvsFromContextMatchResponse,
)
from adcp.types.generated_poc.trusted_match.error import Code, TmpError
from adcp.types.generated_poc.trusted_match.identity_match_request import (
    Attestation,
    Consent,
    Identity,
    IdentityMatchRequest,
    SealedCredential,
    VerificationLevel,
)
from adcp.types.generated_poc.trusted_match.identity_match_response import (
    IdentityMatchResponse,
    IdentityMatchResponseRouterPublisher,
    TmpxMacro as TmpxMacroFromIdentityMatchResponse,
    TmpxProviders,
)
from adcp.types.generated_poc.trusted_match.offer import Offer
from adcp.types.generated_poc.trusted_match.offer_price import Model, OfferPrice
from adcp.types.generated_poc.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouter,
    Signals as SignalsFromProviderContextMatchResponse,
    TargetingKv as TargetingKvFromProviderContextMatchResponse,
    TargetingKvs as TargetingKvsFromProviderContextMatchResponse,
)
from adcp.types.generated_poc.trusted_match.provider_identity_match_response import (
    IdentityMatchResponseProviderRouter,
)
from adcp.types.generated_poc.trusted_match.provider_registration import (
    Country,
    Status,
    TmpProviderRegistration,
    TmpProviderRegistration1,
    TmpProviderRegistration2,
    TmpxMacro as TmpxMacroFromProviderRegistration,
    TmpxSlot,
)
from adcp.types.generated_poc.trusted_match.publisher_targeting_kv_config import (
    PublisherTargetingKvMapping,
)
from adcp.types.generated_poc.trusted_match.publisher_tmpx_config import PublisherTmpxMacroMapping
from adcp.types.generated_poc.trusted_match.tmpx_chunk import TmpxChunk

# Explicit exports
__all__ = [
    "ArtifactRef",
    "Attestation",
    "AvailablePackage",
    "Code",
    "Consent",
    "ContextMatchRequest",
    "ContextMatchResponseProviderRouter",
    "ContextMatchResponseRouterPublisher",
    "ContextSignals",
    "Country",
    "Geo",
    "Identity",
    "IdentityMatchRequest",
    "IdentityMatchResponse",
    "IdentityMatchResponseProviderRouter",
    "IdentityMatchResponseRouterPublisher",
    "Keyword",
    "Metro",
    "Model",
    "Offer",
    "OfferPrice",
    "PublisherTargetingKvMapping",
    "PublisherTmpxMacroMapping",
    "SealedCredential",
    "Sentiment",
    "SignalsByProvider",
    "SignalsFromContextMatchResponse",
    "SignalsFromProviderContextMatchResponse",
    "Status",
    "TargetingKvFromContextMatchResponse",
    "TargetingKvFromProviderContextMatchResponse",
    "TargetingKvsFromContextMatchResponse",
    "TargetingKvsFromProviderContextMatchResponse",
    "TmpError",
    "TmpProviderRegistration",
    "TmpProviderRegistration1",
    "TmpProviderRegistration2",
    "TmpxChunk",
    "TmpxMacroFromIdentityMatchResponse",
    "TmpxMacroFromProviderRegistration",
    "TmpxProviders",
    "TmpxSlot",
    "Type",
    "VerificationLevel",
]
