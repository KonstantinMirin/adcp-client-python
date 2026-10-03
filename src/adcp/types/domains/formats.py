"""Types the AdCP ``formats`` schemas declare.

Importing from the domain says which variant you mean, where the flat
``adcp.types`` namespace can only bind one class per name:

    from adcp.types.domains.formats import <Type>

A type this domain declares in more than one schema carries the defining
file in its name (``CreativeFromListCreativesResponse``); everything else
keeps the name codegen gave it.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.formats.canonical._base import (
    AssetType,
    CanonicalFormatBase,
    CompositionModel,
    PixelRatio as PixelRatioFromBase,
    ReferenceMutability,
    RequiredPixelRatio,
    Slot,
)
from adcp.types.generated_poc.formats.canonical.agent_placement import (
    CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement,
    OutputModality,
)
from adcp.types.generated_poc.formats.canonical.audio_daast import (
    CanonicalFormatDaastAudio,
    DurationMsRangeItem as DurationMsRangeItemFromAudioDaast,
)
from adcp.types.generated_poc.formats.canonical.audio_hosted import (
    AssetSource as AssetSourceFromAudioHosted,
    AudioChannel,
    AudioCodec as AudioCodecFromAudioHosted,
    AudioSampleRate,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromAudioHosted,
    CanonicalFormatHostedAudio,
    DurationMsRange as DurationMsRangeFromAudioHosted,
)
from adcp.types.generated_poc.formats.canonical.audio_vast import (
    CanonicalFormatVastAudio,
    DurationMsRangeItem as DurationMsRangeItemFromAudioVast,
)
from adcp.types.generated_poc.formats.canonical.coordinated_placements import (
    CanonicalFormatCoordinatedPlacements,
)
from adcp.types.generated_poc.formats.canonical.display_tag import (
    CanonicalFormatDisplayTag,
    Size as SizeFromDisplayTag,
    SupportedDeliveryType,
    SupportedTagType,
)
from adcp.types.generated_poc.formats.canonical.html5 import (
    CanonicalFormatHtml5Banner,
    ClicktagMacro,
    MraidVersion,
    Size as SizeFromHtml5,
)
from adcp.types.generated_poc.formats.canonical.image import (
    AssetSource as AssetSourceFromImage,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromImage,
    CanonicalFormatImage,
    ImageFormat as ImageFormatFromImage,
    MotionLevel,
    PixelRatio as PixelRatioFromImage,
    Size as SizeFromImage,
)
from adcp.types.generated_poc.formats.canonical.image_carousel import (
    AllowedCardMediaAssetType,
    CanonicalFormatImageCarousel,
)
from adcp.types.generated_poc.formats.canonical.native_in_feed import (
    AssetSource as AssetSourceFromNativeInFeed,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromNativeInFeed,
    CanonicalFormatNativeInFeed,
    FocusBehavior,
    IconSize,
    ImageFormat as ImageFormatFromNativeInFeed,
    MainImageSize,
    MenuPlacement,
)
from adcp.types.generated_poc.formats.canonical.responsive_creative import (
    CanonicalFormatResponsiveCreative,
)
from adcp.types.generated_poc.formats.canonical.seller_rendered_stateful_display import (
    Anchoring,
    Breakpoint,
    CanonicalFormatSellerRenderedStatefulDisplay,
    Clickthrough,
    Container as ContainerFromSellerRenderedStatefulDisplay,
    Direction,
    DurationMsRange as DurationMsRangeFromSellerRenderedStatefulDisplay,
    HeightRangeItem,
    Input,
    MediaEvent,
    Motion,
    Reveal,
    ScrollReference,
    SlotBinding,
    State,
    SupplyMode,
    TransitionMode,
    TransitionMode9,
    Transitions,
    Transitions10,
    Transitions11,
    Transitions7,
    Transitions8,
    Transitions9,
    Trigger,
    UserControls,
    VideoPlayback,
    WidthMode,
    WidthRangeItem,
)
from adcp.types.generated_poc.formats.canonical.sponsored_placement import (
    CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven,
    FanoutMode,
    ItemProductionModel,
    SupportedIdType,
)
from adcp.types.generated_poc.formats.canonical.video_hosted import (
    AssetSource as AssetSourceFromVideoHosted,
    AudioCodec as AudioCodecFromVideoHosted,
    BuyerAssetAcceptance as BuyerAssetAcceptanceFromVideoHosted,
    CanonicalFormatHostedVideo,
    Captions,
    CompanionBannerHeight,
    CompanionBannerWidth,
    Container as ContainerFromVideoHosted,
    DurationMsRange as DurationMsRangeFromVideoHosted,
    Orientation as OrientationFromVideoHosted,
    VideoCodec,
)
from adcp.types.generated_poc.formats.canonical.video_vast import (
    CanonicalFormatVastVideo,
    CreativeType,
    DurationMsRangeItem as DurationMsRangeItemFromVideoVast,
    Orientation as OrientationFromVideoVast,
    VpaidVersion,
)

# Explicit exports
__all__ = [
    "AllowedCardMediaAssetType",
    "Anchoring",
    "AssetSourceFromAudioHosted",
    "AssetSourceFromImage",
    "AssetSourceFromNativeInFeed",
    "AssetSourceFromVideoHosted",
    "AssetType",
    "AudioChannel",
    "AudioCodecFromAudioHosted",
    "AudioCodecFromVideoHosted",
    "AudioSampleRate",
    "Breakpoint",
    "BuyerAssetAcceptanceFromAudioHosted",
    "BuyerAssetAcceptanceFromImage",
    "BuyerAssetAcceptanceFromNativeInFeed",
    "BuyerAssetAcceptanceFromVideoHosted",
    "CanonicalFormatAgentPlacementAiSurfaceSponsoredPlacement",
    "CanonicalFormatBase",
    "CanonicalFormatCoordinatedPlacements",
    "CanonicalFormatDaastAudio",
    "CanonicalFormatDisplayTag",
    "CanonicalFormatHostedAudio",
    "CanonicalFormatHostedVideo",
    "CanonicalFormatHtml5Banner",
    "CanonicalFormatImage",
    "CanonicalFormatImageCarousel",
    "CanonicalFormatNativeInFeed",
    "CanonicalFormatResponsiveCreative",
    "CanonicalFormatSellerRenderedStatefulDisplay",
    "CanonicalFormatSponsoredPlacementRetailMediaCatalogDriven",
    "CanonicalFormatVastAudio",
    "CanonicalFormatVastVideo",
    "Captions",
    "ClicktagMacro",
    "Clickthrough",
    "CompanionBannerHeight",
    "CompanionBannerWidth",
    "CompositionModel",
    "ContainerFromSellerRenderedStatefulDisplay",
    "ContainerFromVideoHosted",
    "CreativeType",
    "Direction",
    "DurationMsRangeFromAudioHosted",
    "DurationMsRangeFromSellerRenderedStatefulDisplay",
    "DurationMsRangeFromVideoHosted",
    "DurationMsRangeItemFromAudioDaast",
    "DurationMsRangeItemFromAudioVast",
    "DurationMsRangeItemFromVideoVast",
    "FanoutMode",
    "FocusBehavior",
    "HeightRangeItem",
    "IconSize",
    "ImageFormatFromImage",
    "ImageFormatFromNativeInFeed",
    "Input",
    "ItemProductionModel",
    "MainImageSize",
    "MediaEvent",
    "MenuPlacement",
    "Motion",
    "MotionLevel",
    "MraidVersion",
    "OrientationFromVideoHosted",
    "OrientationFromVideoVast",
    "OutputModality",
    "PixelRatioFromBase",
    "PixelRatioFromImage",
    "ReferenceMutability",
    "RequiredPixelRatio",
    "Reveal",
    "ScrollReference",
    "SizeFromDisplayTag",
    "SizeFromHtml5",
    "SizeFromImage",
    "Slot",
    "SlotBinding",
    "State",
    "SupplyMode",
    "SupportedDeliveryType",
    "SupportedIdType",
    "SupportedTagType",
    "TransitionMode",
    "TransitionMode9",
    "Transitions",
    "Transitions10",
    "Transitions11",
    "Transitions7",
    "Transitions8",
    "Transitions9",
    "Trigger",
    "UserControls",
    "VideoCodec",
    "VideoPlayback",
    "VpaidVersion",
    "WidthMode",
    "WidthRangeItem",
]
