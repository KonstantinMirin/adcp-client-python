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

from ._schemas.brand import (
    Agents as Agents,
    AuthoritativeLocationRedirect as AuthoritativeLocationRedirect,
    BrandAgent as BrandAgent,
    BrandCanonicalDocument as BrandCanonicalDocument,
    BrandDiscovery as BrandDiscovery,
    BrandDiscoveryFontRole as BrandDiscoveryFontRole,
    BrandDiscoveryFontRoleFamily as BrandDiscoveryFontRoleFamily,
    BrandId as BrandId,
    ColorRefName as ColorRefName,
    ColorRefSurface as ColorRefSurface,
    ColorRefValue as ColorRefValue,
    ColorValue as ColorValue,
    Domain as Domain,
    HexColor as HexColor,
    HousePortfolio as HousePortfolio,
    HouseRedirect as HouseRedirect,
    HouseRedirectRedirectReason as HouseRedirectRedirectReason,
    LocalizedName as LocalizedName,
    LocalizedScalar as LocalizedScalar,
    LocalizedStringList as LocalizedStringList,
    LocalizedStringListEntry as LocalizedStringListEntry,
    LogoId as LogoId,
    Tone as Tone,
)
from ._schemas.brand.acquire_rights_request import (
    AcquireRightsRequest as AcquireRightsRequest,
)
from ._schemas.brand.acquire_rights_response import (
    AcquireRightsAcquired as AcquireRightsAcquired,
    AcquireRightsError as AcquireRightsError,
    AcquireRightsPendingApproval as AcquireRightsPendingApproval,
    AcquireRightsRejected as AcquireRightsRejected,
    AcquireRightsResponse as AcquireRightsResponse,
)
from ._schemas.brand.creative_approval_request import (
    CreativeApprovalRequest as CreativeApprovalRequest,
)
from ._schemas.brand.creative_approval_response import (
    CreativeApprovalError as CreativeApprovalError,
    CreativeApprovalResponse as CreativeApprovalResponse,
    CreativeApproved as CreativeApproved,
    CreativePendingReview as CreativePendingReview,
    CreativeRejected as CreativeRejected,
)
from ._schemas.brand.get_brand_identity_request import (
    GetBrandIdentityRequest as GetBrandIdentityRequest,
)
from ._schemas.brand.get_brand_identity_response import (
    GetBrandIdentityError as GetBrandIdentityError,
    GetBrandIdentityResponse as GetBrandIdentityResponse,
    GetBrandIdentityResponseFontRole as GetBrandIdentityResponseFontRole,
    GetBrandIdentityResponseFontRoleFamily as GetBrandIdentityResponseFontRoleFamily,
    GetBrandIdentitySuccess as GetBrandIdentitySuccess,
)
from ._schemas.brand.get_rights_request import (
    GetRightsRequest as GetRightsRequest,
)
from ._schemas.brand.get_rights_response import (
    GetRightsError as GetRightsError,
    GetRightsResponse as GetRightsResponse,
    GetRightsSuccess as GetRightsSuccess,
)
from ._schemas.brand.revocation_notification import (
    RevocationNotification as RevocationNotification,
)
from ._schemas.brand.rights_pricing_option import (
    RightsPricingOption as RightsPricingOption,
)
from ._schemas.brand.rights_terms import (
    RightsTerms as RightsTerms,
)
from ._schemas.brand.search_brands_request import (
    SearchBrandsRequest as SearchBrandsRequest,
)
from ._schemas.brand.search_brands_response import (
    SearchBrandsError as SearchBrandsError,
    SearchBrandsResponse as SearchBrandsResponse,
    SearchBrandsSuccess as SearchBrandsSuccess,
)
from ._schemas.brand.update_rights_request import (
    UpdateRightsRequest as UpdateRightsRequest,
)
from ._schemas.brand.update_rights_response import (
    UpdateRightsError as UpdateRightsError,
    UpdateRightsResponse as UpdateRightsResponse,
    UpdateRightsSuccess as UpdateRightsSuccess,
)
from ._schemas.brand.verification_status import (
    VerificationStatus as VerificationStatus,
)
from ._schemas.brand.verify_brand_claim_request import (
    VerifyBrandClaimRequest as VerifyBrandClaimRequest,
    VerifyParentClaim as VerifyParentClaim,
    VerifyPropertyClaim as VerifyPropertyClaim,
    VerifySubsidiaryClaim as VerifySubsidiaryClaim,
    VerifyTrademarkClaim as VerifyTrademarkClaim,
)
from ._schemas.brand.verify_brand_claim_response import (
    VerifyBrandClaimError as VerifyBrandClaimError,
    VerifyBrandClaimResponse as VerifyBrandClaimResponse,
    VerifyBrandClaimSuccess as VerifyBrandClaimSuccess,
)
from ._schemas.brand.verify_brand_claims_request import (
    ClaimEntry as ClaimEntry,
    VerifyBrandClaimsRequestBulk as VerifyBrandClaimsRequestBulk,
)
from ._schemas.brand.verify_brand_claims_response import (
    ResultEntry as ResultEntry,
    VerifyBrandClaimsError as VerifyBrandClaimsError,
    VerifyBrandClaimsResponseBulk as VerifyBrandClaimsResponseBulk,
    VerifyBrandClaimsResultError as VerifyBrandClaimsResultError,
    VerifyBrandClaimsResultSuccess as VerifyBrandClaimsResultSuccess,
    VerifyBrandClaimsSuccess as VerifyBrandClaimsSuccess,
)

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
