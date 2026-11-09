"""The exports of the ``formats`` domain, as the compiler aggregates them.

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

from .._schemas.formats.canonical._base import AssetType as CanonicalFormatBaseSlotsItemAssetType
from .._schemas.formats.canonical._base import CanonicalFormatBase as CanonicalFormatBase
from .._schemas.formats.canonical._base import CompositionModel as CanonicalFormatBaseCompositionModel
from .._schemas.formats.canonical._base import ReferenceMutability as CanonicalFormatBaseReferenceMutability
from .._schemas.formats.canonical._base import SlotsItem as CanonicalFormatBaseSlotsItem
from .._schemas.formats.canonical.agent_placement import (
    CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement as CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement,
)
from .._schemas.formats.canonical.agent_placement import (
    OutputModality as CanonicalFormatAgentPlacementAISurfaceSponsoredPlacementOutputModality,
)
from .._schemas.formats.canonical.audio_daast import CanonicalFormatDAASTAudio as CanonicalFormatDAASTAudio
from .._schemas.formats.canonical.audio_hosted import AssetSource as CanonicalFormatHostedAudioAssetSource
from .._schemas.formats.canonical.audio_hosted import AudioChannels as CanonicalFormatHostedAudioAudioChannelsItem
from .._schemas.formats.canonical.audio_hosted import AudioCodecsItem as CanonicalFormatHostedAudioAudioCodecsItem
from .._schemas.formats.canonical.audio_hosted import (
    BuyerAssetAcceptance as CanonicalFormatHostedAudioBuyerAssetAcceptance,
)
from .._schemas.formats.canonical.audio_hosted import CanonicalFormatHostedAudio as CanonicalFormatHostedAudio
from .._schemas.formats.canonical.audio_vast import CanonicalFormatVASTAudio as CanonicalFormatVASTAudio
from .._schemas.formats.canonical.coordinated_placements import (
    AssetType as CanonicalFormatCoordinatedPlacementsSharedSlotsItemAssetType,
)
from .._schemas.formats.canonical.coordinated_placements import (
    CanonicalFormatCoordinatedPlacements as CanonicalFormatCoordinatedPlacements,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItem as CanonicalFormatCoordinatedPlacementsComponentsItem,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParams as ComponentsItemFormatKindParams,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsAgentPlacement as ComponentsItemFormatKindParamsAgentPlacement,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsAudioDaast as ComponentsItemFormatKindParamsAudioDaast,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsAudioHosted as ComponentsItemFormatKindParamsAudioHosted,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsDisplayTag as ComponentsItemFormatKindParamsDisplayTag,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsHtml5 as ComponentsItemFormatKindParamsHtml5,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsImage as ComponentsItemFormatKindParamsImage,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsImageCarousel as ComponentsItemFormatKindParamsImageCarousel,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsNativeInFeed as ComponentsItemFormatKindParamsNativeInFeed,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsResponsiveCreative as ComponentsItemFormatKindParamsResponsiveCreative,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay as ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsSponsoredPlacement as ComponentsItemFormatKindParamsSponsoredPlacement,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsVideoHosted as ComponentsItemFormatKindParamsVideoHosted,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatKindParamsVideoVast as ComponentsItemFormatKindParamsVideoVast,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ComponentsItemFormatOptionRef as ComponentsItemFormatOptionRef,
)
from .._schemas.formats.canonical.coordinated_placements import (
    ServingPolicy as CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy,
)
from .._schemas.formats.canonical.coordinated_placements import (
    SharedSlotsItem as CanonicalFormatCoordinatedPlacementsSharedSlotsItem,
)
from .._schemas.formats.canonical.display_tag import CanonicalFormatDisplayTag as CanonicalFormatDisplayTag
from .._schemas.formats.canonical.display_tag import SizesItem as CanonicalFormatDisplayTagSizesItem
from .._schemas.formats.canonical.display_tag import (
    SupportedDeliveryTypesItem as CanonicalFormatDisplayTagSupportedDeliveryTypesItem,
)
from .._schemas.formats.canonical.display_tag import (
    SupportedTagTypesItem as CanonicalFormatDisplayTagSupportedTagTypesItem,
)
from .._schemas.formats.canonical.html5 import CanonicalFormatHTML5Banner as CanonicalFormatHTML5Banner
from .._schemas.formats.canonical.html5 import MraidVersion as CanonicalFormatHTML5BannerMraidVersion
from .._schemas.formats.canonical.html5 import SizesItem as CanonicalFormatHTML5BannerSizesItem
from .._schemas.formats.canonical.image import BuyerAssetAcceptance as CanonicalFormatImageBuyerAssetAcceptance
from .._schemas.formats.canonical.image import CanonicalFormatImage as CanonicalFormatImage
from .._schemas.formats.canonical.image import ImageFormatsItem as CanonicalFormatImageImageFormatsItem
from .._schemas.formats.canonical.image import MotionLevel as CanonicalFormatImageMotionLevel
from .._schemas.formats.canonical.image import SizesItem as CanonicalFormatImageSizesItem
from .._schemas.formats.canonical.image_carousel import AllowedCardAssetTypesItem as AllowedCardAssetTypesItem
from .._schemas.formats.canonical.image_carousel import CanonicalFormatImageCarousel as CanonicalFormatImageCarousel
from .._schemas.formats.canonical.native_in_feed import AssetSource as CanonicalFormatNativeInFeedAssetSource
from .._schemas.formats.canonical.native_in_feed import (
    BuyerAssetAcceptance as CanonicalFormatNativeInFeedBuyerAssetAcceptance,
)
from .._schemas.formats.canonical.native_in_feed import CanonicalFormatNativeInFeed as CanonicalFormatNativeInFeed
from .._schemas.formats.canonical.native_in_feed import FocusBehavior as CanonicalFormatNativeInFeedFocusBehavior
from .._schemas.formats.canonical.native_in_feed import IconSize as CanonicalFormatNativeInFeedIconSize
from .._schemas.formats.canonical.native_in_feed import ImageFormatsItem as CanonicalFormatNativeInFeedImageFormatsItem
from .._schemas.formats.canonical.native_in_feed import (
    MainImageSizesItem as CanonicalFormatNativeInFeedMainImageSizesItem,
)
from .._schemas.formats.canonical.native_in_feed import MenuPlacement as CanonicalFormatNativeInFeedMenuPlacement
from .._schemas.formats.canonical.responsive_creative import (
    CanonicalFormatResponsiveCreative as CanonicalFormatResponsiveCreative,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Anchoring as CanonicalFormatSellerRenderedStatefulDisplayStatesItemAnchoring,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    BreakpointsItem as CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItem,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    CanonicalFormatSellerRenderedStatefulDisplay as CanonicalFormatSellerRenderedStatefulDisplay,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    ContainersItem as CanonicalFormatSellerRenderedStatefulDisplayContainersItem,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Direction as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemDirection,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Input as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemInput,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    MediaEvent as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemMediaEvent,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Motion as CanonicalFormatSellerRenderedStatefulDisplayStatesItemMotion,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Reveal as CanonicalFormatSellerRenderedStatefulDisplayReveal,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    ScrollReference as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemScrollReference,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    StatesItem as CanonicalFormatSellerRenderedStatefulDisplayStatesItem,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    SupplyMode as CanonicalFormatSellerRenderedStatefulDisplaySupplyMode,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItem as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItem,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemInViewTimer as TransitionsItemInViewTimer,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemMediaEvent as TransitionsItemMediaEvent,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemScrollProgressScrollScrollLinked as TransitionsItemScrollProgressScrollScrollLinked,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemScrollThresholdScroll as TransitionsItemScrollThresholdScroll,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import TransitionsItemTimer as TransitionsItemTimer
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemTimerTransitionMode as TransitionsItemTimerTransitionMode,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemTransitionMode as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTransitionMode,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    TransitionsItemUserAction as TransitionsItemUserAction,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    Trigger as CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTrigger,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    UserControls as CanonicalFormatSellerRenderedStatefulDisplayUserControls,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    VideoPlayback as CanonicalFormatSellerRenderedStatefulDisplayVideoPlayback,
)
from .._schemas.formats.canonical.seller_rendered_stateful_display import (
    WidthMode as CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItemWidthMode,
)
from .._schemas.formats.canonical.sponsored_placement import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven as CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven,
)
from .._schemas.formats.canonical.sponsored_placement import (
    FanoutMode as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenFanoutMode,
)
from .._schemas.formats.canonical.sponsored_placement import (
    ItemProductionModel as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenItemProductionModel,
)
from .._schemas.formats.canonical.sponsored_placement import (
    SupportedIdTypesItem as CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenSupportedIdTypesItem,
)
from .._schemas.formats.canonical.video_hosted import AudioCodecsItem as CanonicalFormatHostedVideoAudioCodecsItem
from .._schemas.formats.canonical.video_hosted import (
    BuyerAssetAcceptance as CanonicalFormatHostedVideoBuyerAssetAcceptance,
)
from .._schemas.formats.canonical.video_hosted import CanonicalFormatHostedVideo as CanonicalFormatHostedVideo
from .._schemas.formats.canonical.video_hosted import Captions as CanonicalFormatHostedVideoCaptions
from .._schemas.formats.canonical.video_hosted import Orientation as CanonicalFormatHostedVideoOrientation
from .._schemas.formats.canonical.video_hosted import VideoCodec as CanonicalFormatHostedVideoVideoCodecsItem
from .._schemas.formats.canonical.video_vast import CanonicalFormatVASTVideo as CanonicalFormatVASTVideo
from .._schemas.formats.canonical.video_vast import CreativeType as CanonicalFormatVASTVideoCreativeType
from .._schemas.formats.canonical.video_vast import VpaidVersion as CanonicalFormatVASTVideoVpaidVersion

__all__ = [
    'AllowedCardAssetTypesItem',
    'CanonicalFormatAgentPlacementAISurfaceSponsoredPlacement',
    'CanonicalFormatAgentPlacementAISurfaceSponsoredPlacementOutputModality',
    'CanonicalFormatBase',
    'CanonicalFormatBaseCompositionModel',
    'CanonicalFormatBaseReferenceMutability',
    'CanonicalFormatBaseSlotsItem',
    'CanonicalFormatBaseSlotsItemAssetType',
    'CanonicalFormatCoordinatedPlacements',
    'CanonicalFormatCoordinatedPlacementsComponentsItem',
    'CanonicalFormatCoordinatedPlacementsComponentsItemServingPolicy',
    'CanonicalFormatCoordinatedPlacementsSharedSlotsItem',
    'CanonicalFormatCoordinatedPlacementsSharedSlotsItemAssetType',
    'CanonicalFormatDAASTAudio',
    'CanonicalFormatDisplayTag',
    'CanonicalFormatDisplayTagSizesItem',
    'CanonicalFormatDisplayTagSupportedDeliveryTypesItem',
    'CanonicalFormatDisplayTagSupportedTagTypesItem',
    'CanonicalFormatHTML5Banner',
    'CanonicalFormatHTML5BannerMraidVersion',
    'CanonicalFormatHTML5BannerSizesItem',
    'CanonicalFormatHostedAudio',
    'CanonicalFormatHostedAudioAssetSource',
    'CanonicalFormatHostedAudioAudioChannelsItem',
    'CanonicalFormatHostedAudioAudioCodecsItem',
    'CanonicalFormatHostedAudioBuyerAssetAcceptance',
    'CanonicalFormatHostedVideo',
    'CanonicalFormatHostedVideoAudioCodecsItem',
    'CanonicalFormatHostedVideoBuyerAssetAcceptance',
    'CanonicalFormatHostedVideoCaptions',
    'CanonicalFormatHostedVideoOrientation',
    'CanonicalFormatHostedVideoVideoCodecsItem',
    'CanonicalFormatImage',
    'CanonicalFormatImageBuyerAssetAcceptance',
    'CanonicalFormatImageCarousel',
    'CanonicalFormatImageImageFormatsItem',
    'CanonicalFormatImageMotionLevel',
    'CanonicalFormatImageSizesItem',
    'CanonicalFormatNativeInFeed',
    'CanonicalFormatNativeInFeedAssetSource',
    'CanonicalFormatNativeInFeedBuyerAssetAcceptance',
    'CanonicalFormatNativeInFeedFocusBehavior',
    'CanonicalFormatNativeInFeedIconSize',
    'CanonicalFormatNativeInFeedImageFormatsItem',
    'CanonicalFormatNativeInFeedMainImageSizesItem',
    'CanonicalFormatNativeInFeedMenuPlacement',
    'CanonicalFormatResponsiveCreative',
    'CanonicalFormatSellerRenderedStatefulDisplay',
    'CanonicalFormatSellerRenderedStatefulDisplayContainersItem',
    'CanonicalFormatSellerRenderedStatefulDisplayReveal',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItem',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemAnchoring',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItem',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemBreakpointsItemWidthMode',
    'CanonicalFormatSellerRenderedStatefulDisplayStatesItemMotion',
    'CanonicalFormatSellerRenderedStatefulDisplaySupplyMode',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItem',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemDirection',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemInput',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemMediaEvent',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemScrollReference',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTransitionMode',
    'CanonicalFormatSellerRenderedStatefulDisplayTransitionsItemTrigger',
    'CanonicalFormatSellerRenderedStatefulDisplayUserControls',
    'CanonicalFormatSellerRenderedStatefulDisplayVideoPlayback',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenFanoutMode',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenItemProductionModel',
    'CanonicalFormatSponsoredPlacementRetailMediaCatalogDrivenSupportedIdTypesItem',
    'CanonicalFormatVASTAudio',
    'CanonicalFormatVASTVideo',
    'CanonicalFormatVASTVideoCreativeType',
    'CanonicalFormatVASTVideoVpaidVersion',
    'ComponentsItemFormatKindParams',
    'ComponentsItemFormatKindParamsAgentPlacement',
    'ComponentsItemFormatKindParamsAudioDaast',
    'ComponentsItemFormatKindParamsAudioHosted',
    'ComponentsItemFormatKindParamsDisplayTag',
    'ComponentsItemFormatKindParamsHtml5',
    'ComponentsItemFormatKindParamsImage',
    'ComponentsItemFormatKindParamsImageCarousel',
    'ComponentsItemFormatKindParamsNativeInFeed',
    'ComponentsItemFormatKindParamsResponsiveCreative',
    'ComponentsItemFormatKindParamsSellerRenderedStatefulDisplay',
    'ComponentsItemFormatKindParamsSponsoredPlacement',
    'ComponentsItemFormatKindParamsVideoHosted',
    'ComponentsItemFormatKindParamsVideoVast',
    'ComponentsItemFormatOptionRef',
    'TransitionsItemInViewTimer',
    'TransitionsItemMediaEvent',
    'TransitionsItemScrollProgressScrollScrollLinked',
    'TransitionsItemScrollThresholdScroll',
    'TransitionsItemTimer',
    'TransitionsItemTimerTransitionMode',
    'TransitionsItemUserAction',
]
