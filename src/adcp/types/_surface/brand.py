"""The exports of the ``brand`` domain, as the compiler aggregates them.

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

from .._schemas.brand import AgenticCheckout as BrandDiscoveryProductCatalogAgenticCheckout
from .._schemas.brand import Agents as Agents
from .._schemas.brand import AnimationSpeed as BrandDiscoveryMotionGuidelinesAnimationSpeed
from .._schemas.brand import AppliesToItem as BrandDiscoveryColorConstraintAppliesToItem
from .._schemas.brand import Architecture as BrandDiscoveryHouseArchitecture
from .._schemas.brand import Asset as BrandDiscoveryAsset
from .._schemas.brand import AssetLibrary as BrandDiscoveryAssetLibrary
from .._schemas.brand import AssetLibraryType as BrandDiscoveryAssetLibraryType
from .._schemas.brand import AuthoritativeLocationRedirect as AuthoritativeLocationRedirect
from .._schemas.brand import AuthorizedOperator as BrandDiscoveryAuthorizedOperator
from .._schemas.brand import Avatar as BrandDiscoveryBrandAvatar
from .._schemas.brand import Background as BrandDiscoveryLogoBackground
from .._schemas.brand import BackgroundContrast as BrandDiscoveryLogoPlacementBackgroundContrast
from .._schemas.brand import Backgrounds as BrandDiscoveryCompositionRulesBackgrounds
from .._schemas.brand import BorderRadius as BrandDiscoveryBorderRadius
from .._schemas.brand import Brand as BrandDiscoveryBrand
from .._schemas.brand import BrandAgent as BrandAgent
from .._schemas.brand import BrandAgentEntry as BrandDiscoveryBrandAgentEntry
from .._schemas.brand import BrandCanonicalDocument as BrandCanonicalDocument
from .._schemas.brand import BrandContact as BrandDiscoveryBrandContact
from .._schemas.brand import BrandDiscovery as BrandDiscovery
from .._schemas.brand import BrandDiscoveryBrandAgent as BrandDiscoveryBrandAgent
from .._schemas.brand import BrandDiscoveryContact as BrandDiscoveryContact
from .._schemas.brand import BrandDiscoveryFontRole as BrandDiscoveryFontRole
from .._schemas.brand import BrandDiscoveryFontRoleFamily as BrandDiscoveryFontRoleFamily
from .._schemas.brand import BrandDiscoveryProperty as BrandDiscoveryProperty
from .._schemas.brand import BrandId as BrandId
from .._schemas.brand import BrandShapes as BrandDiscoveryBrandShapes
from .._schemas.brand import BrandShapesUsage as BrandDiscoveryBrandShapesUsage
from .._schemas.brand import CollectionsItem as BrandDiscoveryBrandCollectionsItem
from .._schemas.brand import ColorConstraint as BrandDiscoveryColorConstraint
from .._schemas.brand import ColorGuide as BrandDiscoveryAssetLibraryColorGuide
from .._schemas.brand import ColorRef as BrandDiscoveryColorRef
from .._schemas.brand import ColorRefName as ColorRefName
from .._schemas.brand import ColorRefSurface as ColorRefSurface
from .._schemas.brand import ColorRefValue as ColorRefValue
from .._schemas.brand import Colors as BrandDiscoveryColors
from .._schemas.brand import ColorTemperature as BrandDiscoveryPhotographyStyleColorTemperature
from .._schemas.brand import ColorValue as ColorValue
from .._schemas.brand import Colorway as BrandDiscoveryColorway
from .._schemas.brand import CompositionRules as BrandDiscoveryCompositionRules
from .._schemas.brand import Contrast as BrandDiscoveryPhotographyStyleContrast
from .._schemas.brand import CornerStyle as BrandDiscoveryIconographyCornerStyle
from .._schemas.brand import DataSubjectContestation as BrandDiscoveryDataSubjectContestation
from .._schemas.brand import DepthOfField as BrandDiscoveryPhotographyStyleDepthOfField
from .._schemas.brand import DisclaimersItem as BrandDiscoveryBrandDisclaimersItem
from .._schemas.brand import Elevation as BrandDiscoveryElevation
from .._schemas.brand import FontFileStyle as BrandDiscoveryFontFileStyle
from .._schemas.brand import Fonts as BrandDiscoveryFonts
from .._schemas.brand import Framing as BrandDiscoveryPhotographyStyleFraming
from .._schemas.brand import GradientStyle as BrandDiscoveryCompositionRulesOverlaysGradientStyle
from .._schemas.brand import GraphicElement as BrandDiscoveryGraphicElement
from .._schemas.brand import GraphicElementType as BrandDiscoveryGraphicElementType
from .._schemas.brand import GraphicStyle as BrandDiscoveryGraphicStyle
from .._schemas.brand import GuidelineSeverity as BrandDiscoveryGuidelineSeverity
from .._schemas.brand import HexColor as HexColor
from .._schemas.brand import House as BrandDiscoveryHouse
from .._schemas.brand import HousePortfolio as HousePortfolio
from .._schemas.brand import HouseRedirect as HouseRedirect
from .._schemas.brand import HouseRedirectRedirectReason as HouseRedirectRedirectReason
from .._schemas.brand import Iconography as BrandDiscoveryIconography
from .._schemas.brand import IconographyStyle as BrandDiscoveryIconographyStyle
from .._schemas.brand import IconographyUsage as BrandDiscoveryIconographyUsage
from .._schemas.brand import IdentityRelyingParty as BrandDiscoveryIdentityRelyingParty
from .._schemas.brand import Intensity as BrandDiscoveryCompositionRulesTextureIntensity
from .._schemas.brand import KellerType as BrandDiscoveryKellerType
from .._schemas.brand import Kind as BrandDiscoveryColorRefKind
from .._schemas.brand import LicenseType as BrandDiscoveryTrademarkLicenseType
from .._schemas.brand import LocalizedName as LocalizedName
from .._schemas.brand import LocalizedScalar as LocalizedScalar
from .._schemas.brand import LocalizedStringList as LocalizedStringList
from .._schemas.brand import LocalizedStringListEntry as LocalizedStringListEntry
from .._schemas.brand import LockupType as BrandDiscoveryMarkLockupLockupType
from .._schemas.brand import Logo as BrandDiscoveryLogo
from .._schemas.brand import LogoId as LogoId
from .._schemas.brand import LogoOrientation as BrandDiscoveryLogoOrientation
from .._schemas.brand import LogoPlacement as BrandDiscoveryLogoPlacement
from .._schemas.brand import LogoUsageRule as BrandDiscoveryLogoUsageRule
from .._schemas.brand import LogoVariant as BrandDiscoveryLogoVariant
from .._schemas.brand import MarkLockup as BrandDiscoveryMarkLockup
from .._schemas.brand import MinimumSize as BrandDiscoveryLogoUsageRuleMinimumSize
from .._schemas.brand import MotionGuidelines as BrandDiscoveryMotionGuidelines
from .._schemas.brand import MotionGuidelinesPacing as BrandDiscoveryMotionGuidelinesPacing
from .._schemas.brand import ObjUrlWeightWeightRangeStyle as BrandDiscoveryFontFile
from .._schemas.brand import Ordering as BrandDiscoveryMarkLockupOrdering
from .._schemas.brand import Orientation as BrandDiscoveryGraphicElementOrientation
from .._schemas.brand import Overlays as BrandDiscoveryCompositionRulesOverlays
from .._schemas.brand import PalettesItem as BrandDiscoveryAssetLibraryColorGuidePalettesItem
from .._schemas.brand import People as BrandDiscoveryPhotographyStyleSubjectPeople
from .._schemas.brand import PhotographyStyle as BrandDiscoveryPhotographyStyle
from .._schemas.brand import PortfolioEntry as BrandDiscoveryPortfolioEntry
from .._schemas.brand import PreferredPosition as BrandDiscoveryLogoPlacementPreferredPosition
from .._schemas.brand import ProductCatalog as BrandDiscoveryProductCatalog
from .._schemas.brand import ProductFocus as BrandDiscoveryPhotographyStyleSubjectProductFocus
from .._schemas.brand import Realism as BrandDiscoveryPhotographyStyleRealism
from .._schemas.brand import Relationship as BrandDiscoveryPropertyRelationship
from .._schemas.brand import RightsAgent as BrandDiscoveryRightsAgent
from .._schemas.brand import Scale as BrandDiscoverySpacingScale
from .._schemas.brand import Scope as BrandDiscoveryIdentityRelyingPartyScope
from .._schemas.brand import ScopesItem as BrandDiscoveryAuthorizedOperatorScopesItem
from .._schemas.brand import Separator as BrandDiscoveryMarkLockupSeparator
from .._schemas.brand import SeparatorType as BrandDiscoveryMarkLockupSeparatorType
from .._schemas.brand import Spacing as BrandDiscoverySpacing
from .._schemas.brand import Status as BrandDiscoveryTrademarkStatus
from .._schemas.brand import Store as BrandDiscoveryPropertyStore
from .._schemas.brand import StrokeStyle as BrandDiscoveryGraphicStyleStrokeStyle
from .._schemas.brand import StyleType as BrandDiscoveryGraphicStyleStyleType
from .._schemas.brand import Subject as BrandDiscoveryPhotographyStyleSubject
from .._schemas.brand import Surface as BrandDiscoveryColorRefSurface
from .._schemas.brand import TextEntrance as BrandDiscoveryMotionGuidelinesTextEntrance
from .._schemas.brand import TextTransform as BrandDiscoveryTypeScaleEntryTextTransform
from .._schemas.brand import Texture as BrandDiscoveryCompositionRulesTexture
from .._schemas.brand import TextureStyle as BrandDiscoveryCompositionRulesTextureStyle
from .._schemas.brand import Tone as Tone
from .._schemas.brand import Trademark as BrandDiscoveryTrademark
from .._schemas.brand import TransitionStyle as BrandDiscoveryMotionGuidelinesTransitionStyle
from .._schemas.brand import TypesAllowedItem as BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem
from .._schemas.brand import TypeScale as BrandDiscoveryVisualGuidelinesTypeScale
from .._schemas.brand import TypeScaleEntry as BrandDiscoveryTypeScaleEntry
from .._schemas.brand import VisualGuidelines as BrandDiscoveryVisualGuidelines
from .._schemas.brand import VoiceSynthesis as BrandDiscoveryBrandVoiceSynthesis
from .._schemas.brand.acquire_rights_request import AcquireRightsRequest as AcquireRightsRequest
from .._schemas.brand.acquire_rights_request import Campaign as AcquireRightsRequestCampaign
from .._schemas.brand.acquire_rights_response import AcquireRightsAcquired as AcquireRightsAcquired
from .._schemas.brand.acquire_rights_response import (
    AcquireRightsAcquiredRightsConstraint as AcquireRightsAcquiredRightsConstraint,
)
from .._schemas.brand.acquire_rights_response import AcquireRightsError as AcquireRightsError
from .._schemas.brand.acquire_rights_response import AcquireRightsPendingApproval as AcquireRightsPendingApproval
from .._schemas.brand.acquire_rights_response import AcquireRightsRejected as AcquireRightsRejected
from .._schemas.brand.acquire_rights_response import AcquireRightsResponse as AcquireRightsResponse
from .._schemas.brand.acquire_rights_response import Disclosure as AcquireRightsAcquiredDisclosure
from .._schemas.brand.creative_approval_request import CreativeApprovalRequest as CreativeApprovalRequest
from .._schemas.brand.creative_approval_response import CreativeApprovalError as CreativeApprovalError
from .._schemas.brand.creative_approval_response import CreativeApprovalResponse as CreativeApprovalResponse
from .._schemas.brand.creative_approval_response import CreativeApproved as CreativeApproved
from .._schemas.brand.creative_approval_response import CreativePendingReview as CreativePendingReview
from .._schemas.brand.creative_approval_response import CreativeRejected as CreativeRejected
from .._schemas.brand.get_brand_identity_request import BrandIdentityField as GetBrandIdentityRequestFieldsItem
from .._schemas.brand.get_brand_identity_request import GetBrandIdentityRequest as GetBrandIdentityRequest
from .._schemas.brand.get_brand_identity_response import AssetsItem as GetBrandIdentitySuccessAssetsItem
from .._schemas.brand.get_brand_identity_response import Colors as GetBrandIdentitySuccessColors
from .._schemas.brand.get_brand_identity_response import Fonts as GetBrandIdentitySuccessFonts
from .._schemas.brand.get_brand_identity_response import GetBrandIdentityError as GetBrandIdentityError
from .._schemas.brand.get_brand_identity_response import GetBrandIdentityResponse as GetBrandIdentityResponse
from .._schemas.brand.get_brand_identity_response import (
    GetBrandIdentityResponseFontRole as GetBrandIdentityResponseFontRole,
)
from .._schemas.brand.get_brand_identity_response import (
    GetBrandIdentityResponseFontRoleFamily as GetBrandIdentityResponseFontRoleFamily,
)
from .._schemas.brand.get_brand_identity_response import GetBrandIdentitySuccess as GetBrandIdentitySuccess
from .._schemas.brand.get_brand_identity_response import LogosItem as GetBrandIdentitySuccessLogosItem
from .._schemas.brand.get_brand_identity_response import ObjDomainName as GetBrandIdentitySuccessHouse
from .._schemas.brand.get_brand_identity_response import Rights as GetBrandIdentitySuccessRights
from .._schemas.brand.get_brand_identity_response import Tone as GetBrandIdentitySuccessTone
from .._schemas.brand.get_brand_identity_response import VoiceSynthesis as GetBrandIdentitySuccessVoiceSynthesis
from .._schemas.brand.get_rights_request import GetRightsRequest as GetRightsRequest
from .._schemas.brand.get_rights_response import ExcludedItem as GetRightsSuccessExcludedItem
from .._schemas.brand.get_rights_response import ExclusivityStatus as GetRightsSuccessRightsItemExclusivityStatus
from .._schemas.brand.get_rights_response import GetRightsError as GetRightsError
from .._schemas.brand.get_rights_response import GetRightsResponse as GetRightsResponse
from .._schemas.brand.get_rights_response import GetRightsSuccess as GetRightsSuccess
from .._schemas.brand.get_rights_response import PreviewAssetsItem as GetRightsSuccessRightsItemPreviewAssetsItem
from .._schemas.brand.get_rights_response import RightsItem as GetRightsSuccessRightsItem
from .._schemas.brand.revocation_notification import RevocationNotification as RevocationNotification
from .._schemas.brand.rights_pricing_option import RightsPricingOption as RightsPricingOption
from .._schemas.brand.rights_terms import RightsTerms as RightsTerms
from .._schemas.brand.rights_terms import RightsTermsExclusivity as RightsTermsExclusivity
from .._schemas.brand.search_brands_request import SearchBrandsRequest as SearchBrandsRequest
from .._schemas.brand.search_brands_response import LogosItem as SearchBrandsResponseSearchBrandResultLogosItem
from .._schemas.brand.search_brands_response import (
    RelationshipTrust as SearchBrandsResponseSearchBrandResultRelationshipTrust,
)
from .._schemas.brand.search_brands_response import Rights as SearchBrandsResponseSearchBrandResultRights
from .._schemas.brand.search_brands_response import SearchBrandResult as SearchBrandsResponseSearchBrandResult
from .._schemas.brand.search_brands_response import SearchBrandsError as SearchBrandsError
from .._schemas.brand.search_brands_response import SearchBrandsResponse as SearchBrandsResponse
from .._schemas.brand.search_brands_response import SearchBrandsSuccess as SearchBrandsSuccess
from .._schemas.brand.update_rights_request import UpdateRightsRequest as UpdateRightsRequest
from .._schemas.brand.update_rights_response import UpdateRightsError as UpdateRightsError
from .._schemas.brand.update_rights_response import UpdateRightsResponse as UpdateRightsResponse
from .._schemas.brand.update_rights_response import UpdateRightsSuccess as UpdateRightsSuccess
from .._schemas.brand.update_rights_response import (
    UpdateRightsSuccessRightsConstraint as UpdateRightsSuccessRightsConstraint,
)
from .._schemas.brand.verification_status import VerificationStatus as VerificationStatus
from .._schemas.brand.verify_brand_claim_request import ObjPropertyUseCase as VerifyPropertyClaimClaim
from .._schemas.brand.verify_brand_claim_request import ObjTypeIdentifierStoreRegion as VerifyPropertyClaimClaimProperty
from .._schemas.brand.verify_brand_claim_request import Store as VerifyPropertyClaimClaimPropertyStore
from .._schemas.brand.verify_brand_claim_request import VerifyBrandClaimRequest as VerifyBrandClaimRequest
from .._schemas.brand.verify_brand_claim_request import VerifyParentClaim as VerifyParentClaim
from .._schemas.brand.verify_brand_claim_request import VerifyParentClaimClaim as VerifyParentClaimClaim
from .._schemas.brand.verify_brand_claim_request import VerifyPropertyClaim as VerifyPropertyClaim
from .._schemas.brand.verify_brand_claim_request import VerifySubsidiaryClaim as VerifySubsidiaryClaim
from .._schemas.brand.verify_brand_claim_request import VerifySubsidiaryClaimClaim as VerifySubsidiaryClaimClaim
from .._schemas.brand.verify_brand_claim_request import VerifyTrademarkClaim as VerifyTrademarkClaim
from .._schemas.brand.verify_brand_claim_request import VerifyTrademarkClaimClaim as VerifyTrademarkClaimClaim
from .._schemas.brand.verify_brand_claim_response import (
    ClaimType as VerifyBrandClaimResponseSignedSuccessPayloadClaimType,
)
from .._schemas.brand.verify_brand_claim_response import Payload as VerifyBrandClaimResponseSignedResponsePayload
from .._schemas.brand.verify_brand_claim_response import SignedResponse as VerifyBrandClaimResponseSignedResponse
from .._schemas.brand.verify_brand_claim_response import (
    SignedSuccessPayload as VerifyBrandClaimResponseSignedSuccessPayload,
)
from .._schemas.brand.verify_brand_claim_response import VerifyBrandClaimError as VerifyBrandClaimError
from .._schemas.brand.verify_brand_claim_response import VerifyBrandClaimResponse as VerifyBrandClaimResponse
from .._schemas.brand.verify_brand_claim_response import VerifyBrandClaimSuccess as VerifyBrandClaimSuccess
from .._schemas.brand.verify_brand_claims_request import ClaimEntry as ClaimEntry
from .._schemas.brand.verify_brand_claims_request import VerifyBrandClaimsRequestBulk as VerifyBrandClaimsRequestBulk
from .._schemas.brand.verify_brand_claims_response import Payload as VerifyBrandClaimsResponseBulkSignedResponsePayload
from .._schemas.brand.verify_brand_claims_response import ResultEntry as ResultEntry
from .._schemas.brand.verify_brand_claims_response import SignedResponse as VerifyBrandClaimsResponseBulkSignedResponse
from .._schemas.brand.verify_brand_claims_response import (
    SignedSuccessPayload as VerifyBrandClaimsResponseBulkSignedSuccessPayload,
)
from .._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsError as VerifyBrandClaimsError
from .._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsResponseBulk as VerifyBrandClaimsResponseBulk
from .._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsResultError as VerifyBrandClaimsResultError
from .._schemas.brand.verify_brand_claims_response import (
    VerifyBrandClaimsResultSuccess as VerifyBrandClaimsResultSuccess,
)
from .._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsSuccess as VerifyBrandClaimsSuccess

__all__ = [
    'AcquireRightsAcquired',
    'AcquireRightsAcquiredDisclosure',
    'AcquireRightsAcquiredRightsConstraint',
    'AcquireRightsError',
    'AcquireRightsPendingApproval',
    'AcquireRightsRejected',
    'AcquireRightsRequest',
    'AcquireRightsRequestCampaign',
    'AcquireRightsResponse',
    'Agents',
    'AuthoritativeLocationRedirect',
    'BrandAgent',
    'BrandCanonicalDocument',
    'BrandDiscovery',
    'BrandDiscoveryAsset',
    'BrandDiscoveryAssetLibrary',
    'BrandDiscoveryAssetLibraryColorGuide',
    'BrandDiscoveryAssetLibraryColorGuidePalettesItem',
    'BrandDiscoveryAssetLibraryType',
    'BrandDiscoveryAuthorizedOperator',
    'BrandDiscoveryAuthorizedOperatorScopesItem',
    'BrandDiscoveryBorderRadius',
    'BrandDiscoveryBrand',
    'BrandDiscoveryBrandAgent',
    'BrandDiscoveryBrandAgentEntry',
    'BrandDiscoveryBrandAvatar',
    'BrandDiscoveryBrandCollectionsItem',
    'BrandDiscoveryBrandContact',
    'BrandDiscoveryBrandDisclaimersItem',
    'BrandDiscoveryBrandShapes',
    'BrandDiscoveryBrandShapesUsage',
    'BrandDiscoveryBrandVoiceSynthesis',
    'BrandDiscoveryColorConstraint',
    'BrandDiscoveryColorConstraintAppliesToItem',
    'BrandDiscoveryColorRef',
    'BrandDiscoveryColorRefKind',
    'BrandDiscoveryColorRefSurface',
    'BrandDiscoveryColors',
    'BrandDiscoveryColorway',
    'BrandDiscoveryCompositionRules',
    'BrandDiscoveryCompositionRulesBackgrounds',
    'BrandDiscoveryCompositionRulesBackgroundsTypesAllowedItem',
    'BrandDiscoveryCompositionRulesOverlays',
    'BrandDiscoveryCompositionRulesOverlaysGradientStyle',
    'BrandDiscoveryCompositionRulesTexture',
    'BrandDiscoveryCompositionRulesTextureIntensity',
    'BrandDiscoveryCompositionRulesTextureStyle',
    'BrandDiscoveryContact',
    'BrandDiscoveryDataSubjectContestation',
    'BrandDiscoveryElevation',
    'BrandDiscoveryFontFile',
    'BrandDiscoveryFontFileStyle',
    'BrandDiscoveryFontRole',
    'BrandDiscoveryFontRoleFamily',
    'BrandDiscoveryFonts',
    'BrandDiscoveryGraphicElement',
    'BrandDiscoveryGraphicElementOrientation',
    'BrandDiscoveryGraphicElementType',
    'BrandDiscoveryGraphicStyle',
    'BrandDiscoveryGraphicStyleStrokeStyle',
    'BrandDiscoveryGraphicStyleStyleType',
    'BrandDiscoveryGuidelineSeverity',
    'BrandDiscoveryHouse',
    'BrandDiscoveryHouseArchitecture',
    'BrandDiscoveryIconography',
    'BrandDiscoveryIconographyCornerStyle',
    'BrandDiscoveryIconographyStyle',
    'BrandDiscoveryIconographyUsage',
    'BrandDiscoveryIdentityRelyingParty',
    'BrandDiscoveryIdentityRelyingPartyScope',
    'BrandDiscoveryKellerType',
    'BrandDiscoveryLogo',
    'BrandDiscoveryLogoBackground',
    'BrandDiscoveryLogoOrientation',
    'BrandDiscoveryLogoPlacement',
    'BrandDiscoveryLogoPlacementBackgroundContrast',
    'BrandDiscoveryLogoPlacementPreferredPosition',
    'BrandDiscoveryLogoUsageRule',
    'BrandDiscoveryLogoUsageRuleMinimumSize',
    'BrandDiscoveryLogoVariant',
    'BrandDiscoveryMarkLockup',
    'BrandDiscoveryMarkLockupLockupType',
    'BrandDiscoveryMarkLockupOrdering',
    'BrandDiscoveryMarkLockupSeparator',
    'BrandDiscoveryMarkLockupSeparatorType',
    'BrandDiscoveryMotionGuidelines',
    'BrandDiscoveryMotionGuidelinesAnimationSpeed',
    'BrandDiscoveryMotionGuidelinesPacing',
    'BrandDiscoveryMotionGuidelinesTextEntrance',
    'BrandDiscoveryMotionGuidelinesTransitionStyle',
    'BrandDiscoveryPhotographyStyle',
    'BrandDiscoveryPhotographyStyleColorTemperature',
    'BrandDiscoveryPhotographyStyleContrast',
    'BrandDiscoveryPhotographyStyleDepthOfField',
    'BrandDiscoveryPhotographyStyleFraming',
    'BrandDiscoveryPhotographyStyleRealism',
    'BrandDiscoveryPhotographyStyleSubject',
    'BrandDiscoveryPhotographyStyleSubjectPeople',
    'BrandDiscoveryPhotographyStyleSubjectProductFocus',
    'BrandDiscoveryPortfolioEntry',
    'BrandDiscoveryProductCatalog',
    'BrandDiscoveryProductCatalogAgenticCheckout',
    'BrandDiscoveryProperty',
    'BrandDiscoveryPropertyRelationship',
    'BrandDiscoveryPropertyStore',
    'BrandDiscoveryRightsAgent',
    'BrandDiscoverySpacing',
    'BrandDiscoverySpacingScale',
    'BrandDiscoveryTrademark',
    'BrandDiscoveryTrademarkLicenseType',
    'BrandDiscoveryTrademarkStatus',
    'BrandDiscoveryTypeScaleEntry',
    'BrandDiscoveryTypeScaleEntryTextTransform',
    'BrandDiscoveryVisualGuidelines',
    'BrandDiscoveryVisualGuidelinesTypeScale',
    'BrandId',
    'ClaimEntry',
    'ColorRefName',
    'ColorRefSurface',
    'ColorRefValue',
    'ColorValue',
    'CreativeApprovalError',
    'CreativeApprovalRequest',
    'CreativeApprovalResponse',
    'CreativeApproved',
    'CreativePendingReview',
    'CreativeRejected',
    'GetBrandIdentityError',
    'GetBrandIdentityRequest',
    'GetBrandIdentityRequestFieldsItem',
    'GetBrandIdentityResponse',
    'GetBrandIdentityResponseFontRole',
    'GetBrandIdentityResponseFontRoleFamily',
    'GetBrandIdentitySuccess',
    'GetBrandIdentitySuccessAssetsItem',
    'GetBrandIdentitySuccessColors',
    'GetBrandIdentitySuccessFonts',
    'GetBrandIdentitySuccessHouse',
    'GetBrandIdentitySuccessLogosItem',
    'GetBrandIdentitySuccessRights',
    'GetBrandIdentitySuccessTone',
    'GetBrandIdentitySuccessVoiceSynthesis',
    'GetRightsError',
    'GetRightsRequest',
    'GetRightsResponse',
    'GetRightsSuccess',
    'GetRightsSuccessExcludedItem',
    'GetRightsSuccessRightsItem',
    'GetRightsSuccessRightsItemExclusivityStatus',
    'GetRightsSuccessRightsItemPreviewAssetsItem',
    'HexColor',
    'HousePortfolio',
    'HouseRedirect',
    'HouseRedirectRedirectReason',
    'LocalizedName',
    'LocalizedScalar',
    'LocalizedStringList',
    'LocalizedStringListEntry',
    'LogoId',
    'ResultEntry',
    'RevocationNotification',
    'RightsPricingOption',
    'RightsTerms',
    'RightsTermsExclusivity',
    'SearchBrandsError',
    'SearchBrandsRequest',
    'SearchBrandsResponse',
    'SearchBrandsResponseSearchBrandResult',
    'SearchBrandsResponseSearchBrandResultLogosItem',
    'SearchBrandsResponseSearchBrandResultRelationshipTrust',
    'SearchBrandsResponseSearchBrandResultRights',
    'SearchBrandsSuccess',
    'Tone',
    'UpdateRightsError',
    'UpdateRightsRequest',
    'UpdateRightsResponse',
    'UpdateRightsSuccess',
    'UpdateRightsSuccessRightsConstraint',
    'VerificationStatus',
    'VerifyBrandClaimError',
    'VerifyBrandClaimRequest',
    'VerifyBrandClaimResponse',
    'VerifyBrandClaimResponseSignedResponse',
    'VerifyBrandClaimResponseSignedResponsePayload',
    'VerifyBrandClaimResponseSignedSuccessPayload',
    'VerifyBrandClaimResponseSignedSuccessPayloadClaimType',
    'VerifyBrandClaimSuccess',
    'VerifyBrandClaimsError',
    'VerifyBrandClaimsRequestBulk',
    'VerifyBrandClaimsResponseBulk',
    'VerifyBrandClaimsResponseBulkSignedResponse',
    'VerifyBrandClaimsResponseBulkSignedResponsePayload',
    'VerifyBrandClaimsResponseBulkSignedSuccessPayload',
    'VerifyBrandClaimsResultError',
    'VerifyBrandClaimsResultSuccess',
    'VerifyBrandClaimsSuccess',
    'VerifyParentClaim',
    'VerifyParentClaimClaim',
    'VerifyPropertyClaim',
    'VerifyPropertyClaimClaim',
    'VerifyPropertyClaimClaimProperty',
    'VerifyPropertyClaimClaimPropertyStore',
    'VerifySubsidiaryClaim',
    'VerifySubsidiaryClaimClaim',
    'VerifyTrademarkClaim',
    'VerifyTrademarkClaimClaim',
]
