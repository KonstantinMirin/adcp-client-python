"""The public types of the ``brand`` domain.

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

from ._schemas.brand import Agents as Agents
from ._schemas.brand import AuthoritativeLocationRedirect as AuthoritativeLocationRedirect
from ._schemas.brand import BrandAgent as BrandAgent
from ._schemas.brand import BrandCanonicalDocument as BrandCanonicalDocument
from ._schemas.brand import BrandDiscovery as BrandDiscovery
from ._schemas.brand import BrandDiscoveryFontRole as BrandDiscoveryFontRole
from ._schemas.brand import BrandDiscoveryFontRoleFamily as BrandDiscoveryFontRoleFamily
from ._schemas.brand import BrandId as BrandId
from ._schemas.brand import ColorRefName as ColorRefName
from ._schemas.brand import ColorRefSurface as ColorRefSurface
from ._schemas.brand import ColorRefValue as ColorRefValue
from ._schemas.brand import ColorValue as ColorValue
from ._schemas.brand import Domain as Domain
from ._schemas.brand import HexColor as HexColor
from ._schemas.brand import HousePortfolio as HousePortfolio
from ._schemas.brand import HouseRedirect as HouseRedirect
from ._schemas.brand import HouseRedirectRedirectReason as HouseRedirectRedirectReason
from ._schemas.brand import LocalizedName as LocalizedName
from ._schemas.brand import LocalizedScalar as LocalizedScalar
from ._schemas.brand import LocalizedStringList as LocalizedStringList
from ._schemas.brand import LocalizedStringListEntry as LocalizedStringListEntry
from ._schemas.brand import LogoId as LogoId
from ._schemas.brand import Tone as Tone
from ._schemas.brand.acquire_rights_request import AcquireRightsRequest as AcquireRightsRequest
from ._schemas.brand.acquire_rights_response import AcquireRightsAcquired as AcquireRightsAcquired
from ._schemas.brand.acquire_rights_response import AcquireRightsError as AcquireRightsError
from ._schemas.brand.acquire_rights_response import AcquireRightsPendingApproval as AcquireRightsPendingApproval
from ._schemas.brand.acquire_rights_response import AcquireRightsRejected as AcquireRightsRejected
from ._schemas.brand.acquire_rights_response import AcquireRightsResponse as AcquireRightsResponse
from ._schemas.brand.creative_approval_request import CreativeApprovalRequest as CreativeApprovalRequest
from ._schemas.brand.creative_approval_response import CreativeApprovalError as CreativeApprovalError
from ._schemas.brand.creative_approval_response import CreativeApprovalResponse as CreativeApprovalResponse
from ._schemas.brand.creative_approval_response import CreativeApproved as CreativeApproved
from ._schemas.brand.creative_approval_response import CreativePendingReview as CreativePendingReview
from ._schemas.brand.creative_approval_response import CreativeRejected as CreativeRejected
from ._schemas.brand.get_brand_identity_request import GetBrandIdentityRequest as GetBrandIdentityRequest
from ._schemas.brand.get_brand_identity_response import GetBrandIdentityError as GetBrandIdentityError
from ._schemas.brand.get_brand_identity_response import GetBrandIdentityResponse as GetBrandIdentityResponse
from ._schemas.brand.get_brand_identity_response import (
    GetBrandIdentityResponseFontRole as GetBrandIdentityResponseFontRole,
)
from ._schemas.brand.get_brand_identity_response import (
    GetBrandIdentityResponseFontRoleFamily as GetBrandIdentityResponseFontRoleFamily,
)
from ._schemas.brand.get_brand_identity_response import GetBrandIdentitySuccess as GetBrandIdentitySuccess
from ._schemas.brand.get_rights_request import GetRightsRequest as GetRightsRequest
from ._schemas.brand.get_rights_response import GetRightsError as GetRightsError
from ._schemas.brand.get_rights_response import GetRightsResponse as GetRightsResponse
from ._schemas.brand.get_rights_response import GetRightsSuccess as GetRightsSuccess
from ._schemas.brand.revocation_notification import RevocationNotification as RevocationNotification
from ._schemas.brand.rights_pricing_option import RightsPricingOption as RightsPricingOption
from ._schemas.brand.rights_terms import RightsTerms as RightsTerms
from ._schemas.brand.search_brands_request import SearchBrandsRequest as SearchBrandsRequest
from ._schemas.brand.search_brands_response import SearchBrandsError as SearchBrandsError
from ._schemas.brand.search_brands_response import SearchBrandsResponse as SearchBrandsResponse
from ._schemas.brand.search_brands_response import SearchBrandsSuccess as SearchBrandsSuccess
from ._schemas.brand.update_rights_request import UpdateRightsRequest as UpdateRightsRequest
from ._schemas.brand.update_rights_response import UpdateRightsError as UpdateRightsError
from ._schemas.brand.update_rights_response import UpdateRightsResponse as UpdateRightsResponse
from ._schemas.brand.update_rights_response import UpdateRightsSuccess as UpdateRightsSuccess
from ._schemas.brand.verification_status import VerificationStatus as VerificationStatus
from ._schemas.brand.verify_brand_claim_request import VerifyBrandClaimRequest as VerifyBrandClaimRequest
from ._schemas.brand.verify_brand_claim_request import VerifyParentClaim as VerifyParentClaim
from ._schemas.brand.verify_brand_claim_request import VerifyPropertyClaim as VerifyPropertyClaim
from ._schemas.brand.verify_brand_claim_request import VerifySubsidiaryClaim as VerifySubsidiaryClaim
from ._schemas.brand.verify_brand_claim_request import VerifyTrademarkClaim as VerifyTrademarkClaim
from ._schemas.brand.verify_brand_claim_response import VerifyBrandClaimError as VerifyBrandClaimError
from ._schemas.brand.verify_brand_claim_response import VerifyBrandClaimResponse as VerifyBrandClaimResponse
from ._schemas.brand.verify_brand_claim_response import VerifyBrandClaimSuccess as VerifyBrandClaimSuccess
from ._schemas.brand.verify_brand_claims_request import ClaimEntry as ClaimEntry
from ._schemas.brand.verify_brand_claims_request import VerifyBrandClaimsRequestBulk as VerifyBrandClaimsRequestBulk
from ._schemas.brand.verify_brand_claims_response import ResultEntry as ResultEntry
from ._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsError as VerifyBrandClaimsError
from ._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsResponseBulk as VerifyBrandClaimsResponseBulk
from ._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsResultError as VerifyBrandClaimsResultError
from ._schemas.brand.verify_brand_claims_response import (
    VerifyBrandClaimsResultSuccess as VerifyBrandClaimsResultSuccess,
)
from ._schemas.brand.verify_brand_claims_response import VerifyBrandClaimsSuccess as VerifyBrandClaimsSuccess

__all__ = [
    'AcquireRightsAcquired',
    'AcquireRightsError',
    'AcquireRightsPendingApproval',
    'AcquireRightsRejected',
    'AcquireRightsRequest',
    'AcquireRightsResponse',
    'Agents',
    'AuthoritativeLocationRedirect',
    'BrandAgent',
    'BrandCanonicalDocument',
    'BrandDiscovery',
    'BrandDiscoveryFontRole',
    'BrandDiscoveryFontRoleFamily',
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
    'Domain',
    'GetBrandIdentityError',
    'GetBrandIdentityRequest',
    'GetBrandIdentityResponse',
    'GetBrandIdentityResponseFontRole',
    'GetBrandIdentityResponseFontRoleFamily',
    'GetBrandIdentitySuccess',
    'GetRightsError',
    'GetRightsRequest',
    'GetRightsResponse',
    'GetRightsSuccess',
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
    'SearchBrandsError',
    'SearchBrandsRequest',
    'SearchBrandsResponse',
    'SearchBrandsSuccess',
    'Tone',
    'UpdateRightsError',
    'UpdateRightsRequest',
    'UpdateRightsResponse',
    'UpdateRightsSuccess',
    'VerificationStatus',
    'VerifyBrandClaimError',
    'VerifyBrandClaimRequest',
    'VerifyBrandClaimResponse',
    'VerifyBrandClaimSuccess',
    'VerifyBrandClaimsError',
    'VerifyBrandClaimsRequestBulk',
    'VerifyBrandClaimsResponseBulk',
    'VerifyBrandClaimsResultError',
    'VerifyBrandClaimsResultSuccess',
    'VerifyBrandClaimsSuccess',
    'VerifyParentClaim',
    'VerifyPropertyClaim',
    'VerifySubsidiaryClaim',
    'VerifyTrademarkClaim',
]
