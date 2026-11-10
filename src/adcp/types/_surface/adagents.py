"""The exports of the ``adagents`` domain, as the compiler aggregates them.

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

from .._schemas.adagents import AdCPAgentsAuthorization as AdCPAgentsAuthorization
from .._schemas.adagents import (
    AdCPAgentsAuthorizationAuthoritativeLocation as AdCPAgentsAuthorizationAuthoritativeLocation,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistry as AdCPAgentsAuthorizationCommunityFormatRegistry,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyTags,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalIds,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags as AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemSignalTags,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryCollections as AdCPAgentsAuthorizationCommunityFormatRegistryCollections,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryFormats as AdCPAgentsAuthorizationCommunityFormatRegistryFormats,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryPlacements as AdCPAgentsAuthorizationCommunityFormatRegistryPlacements,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryProperties as AdCPAgentsAuthorizationCommunityFormatRegistryProperties,
)
from .._schemas.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistrySignals as AdCPAgentsAuthorizationCommunityFormatRegistrySignals,
)
from .._schemas.adagents import Contact as AdCPAgentsAuthorizationCommunityFormatRegistryContact
from .._schemas.adagents import DelegationType as DelegationType
from .._schemas.adagents import FormatsItem as AdCPAgentsAuthorizationCommunityFormatRegistryFormatsItem
from .._schemas.adagents import FormatsItemAgentPlacement as FormatsItemAgentPlacement
from .._schemas.adagents import FormatsItemAudioDaast as FormatsItemAudioDaast
from .._schemas.adagents import FormatsItemAudioHosted as FormatsItemAudioHosted
from .._schemas.adagents import FormatsItemAudioVast as FormatsItemAudioVast
from .._schemas.adagents import FormatsItemCoordinatedPlacements as FormatsItemCoordinatedPlacements
from .._schemas.adagents import FormatsItemCustom as FormatsItemCustom
from .._schemas.adagents import FormatsItemDisplayTag as FormatsItemDisplayTag
from .._schemas.adagents import FormatsItemHtml5 as FormatsItemHtml5
from .._schemas.adagents import FormatsItemImage as FormatsItemImage
from .._schemas.adagents import FormatsItemImageCarousel as FormatsItemImageCarousel
from .._schemas.adagents import FormatsItemNativeInFeed as FormatsItemNativeInFeed
from .._schemas.adagents import FormatsItemResponsiveCreative as FormatsItemResponsiveCreative
from .._schemas.adagents import FormatsItemSellerRenderedStatefulDisplay as FormatsItemSellerRenderedStatefulDisplay
from .._schemas.adagents import FormatsItemSponsoredPlacement as FormatsItemSponsoredPlacement
from .._schemas.adagents import FormatsItemVideoHosted as FormatsItemVideoHosted
from .._schemas.adagents import FormatsItemVideoVast as FormatsItemVideoVast
from .._schemas.adagents import PlacementTagsValue as AdCPAgentsAuthorizationCommunityFormatRegistryPlacementTagsValue
from .._schemas.adagents import (
    PropertyFeaturesItem as AdCPAgentsAuthorizationCommunityFormatRegistryPropertyFeaturesItem,
)
from .._schemas.adagents import (
    Reason as AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItemReason,
)
from .._schemas.adagents import (
    RevokedPublisherDomainsItem as AdCPAgentsAuthorizationCommunityFormatRegistryRevokedPublisherDomainsItem,
)
from .._schemas.adagents import SignalTagsValue as SignalTagsValue

__all__ = [
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
    'DelegationType',
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
    'SignalTagsValue',
]
