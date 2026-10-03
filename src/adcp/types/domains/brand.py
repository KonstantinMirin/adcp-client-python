"""Types the AdCP ``brand`` schemas declare.

Importing from the domain says which variant you mean, where the flat
``adcp.types`` namespace can only bind one class per name:

    from adcp.types.domains.brand import <Type>

A type this domain declares in more than one schema carries the defining
file in its name (``CreativeFromListCreativesResponse``); everything else
keeps the name codegen gave it.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.brand.acquire_rights_request import (
    AcquireRightsRequest,
    Campaign,
    Country as CountryFromAcquireRightsRequest,
)
from adcp.types.generated_poc.brand.acquire_rights_response import (
    AcquireRightsResponse,
    AcquireRightsResponse1,
    AcquireRightsResponse2,
    AcquireRightsResponse3,
    AcquireRightsResponse4,
    Disclosure,
)
from adcp.types.generated_poc.brand.creative_approval_request import CreativeApprovalRequest
from adcp.types.generated_poc.brand.creative_approval_response import (
    CreativeApprovalResponse,
    CreativeApprovalResponse1,
    CreativeApprovalResponse2,
    CreativeApprovalResponse3,
    CreativeApprovalResponse4,
)
from adcp.types.generated_poc.brand.get_brand_identity_request import (
    Field1,
    GetBrandIdentityRequest,
)
from adcp.types.generated_poc.brand.get_brand_identity_response import (
    Asset,
    Colors,
    File,
    FontRole2,
    Fonts,
    GetBrandIdentityResponse,
    GetBrandIdentityResponse1,
    GetBrandIdentityResponse2,
    House as HouseFromGetBrandIdentityResponse,
    Logo as LogoFromGetBrandIdentityResponse,
    Rights as RightsFromGetBrandIdentityResponse,
    Tone,
    VoiceSynthesis,
)
from adcp.types.generated_poc.brand.get_rights_request import (
    Country as CountryFromGetRightsRequest,
    GetRightsRequest,
)
from adcp.types.generated_poc.brand.get_rights_response import (
    Excluded,
    ExclusivityStatus,
    GetRightsResponse,
    GetRightsResponse1,
    GetRightsResponse2,
    PreviewAsset,
    Right,
)
from adcp.types.generated_poc.brand.revocation_notification import RevocationNotification
from adcp.types.generated_poc.brand.rights_pricing_option import RightsPricingOption
from adcp.types.generated_poc.brand.rights_terms import (
    Country as CountryFromRightsTerms,
    Exclusivity,
    RightsTerms,
)
from adcp.types.generated_poc.brand.search_brands_request import (
    Country as CountryFromSearchBrandsRequest,
    SearchBrandsRequest,
)
from adcp.types.generated_poc.brand.search_brands_response import (
    Background,
    Country as CountryFromSearchBrandsResponse,
    ExcludedCountry,
    House as HouseFromSearchBrandsResponse,
    KellerType,
    Logo as LogoFromSearchBrandsResponse,
    Orientation,
    RelationshipTrust,
    Rights as RightsFromSearchBrandsResponse,
    SearchBrandResult,
    SearchBrandsResponse,
    Variant,
)
from adcp.types.generated_poc.brand.update_rights_request import UpdateRightsRequest
from adcp.types.generated_poc.brand.update_rights_response import (
    UpdateRightsResponse,
    UpdateRightsResponse1,
    UpdateRightsResponse2,
)
from adcp.types.generated_poc.brand.verification_status import VerificationStatus
from adcp.types.generated_poc.brand.verify_brand_claim_request import (
    ClaimType as ClaimTypeFromVerifyBrandClaimRequest,
    VerifyBrandClaimRequest,
)
from adcp.types.generated_poc.brand.verify_brand_claim_response import (
    ClaimType as ClaimTypeFromVerifyBrandClaimResponse,
    VerifyBrandClaimErrorResponse,
    VerifyBrandClaimPayload,
    VerifyBrandClaimResponse,
    VerifyBrandClaimSignedResponse,
    VerifyBrandClaimSignedSuccessPayload,
    VerifyBrandClaimSuccessResponse,
)
from adcp.types.generated_poc.brand.verify_brand_claims_request import (
    Claim,
    Claim1,
    Claim2,
    Claim3,
    ClaimEntry,
    ClaimEntry1,
    ClaimEntry2,
    ClaimEntry3,
    ClaimEntry4,
    Country as CountryFromVerifyBrandClaimsRequest,
    Property,
    Store,
    VerifyBrandClaimsRequest,
    VerifyBrandClaimsRequestBulk,
)
from adcp.types.generated_poc.brand.verify_brand_claims_response import (
    ClaimType as ClaimTypeFromVerifyBrandClaimsResponse,
    ResultEntry,
    ResultEntry1,
    ResultEntry2,
    VerifyBrandClaimsErrorResponse,
    VerifyBrandClaimsPayload,
    VerifyBrandClaimsResponse,
    VerifyBrandClaimsResponseBulk,
    VerifyBrandClaimsSignedResponse,
    VerifyBrandClaimsSignedSuccessPayload,
)

# Explicit exports
__all__ = [
    "AcquireRightsRequest",
    "AcquireRightsResponse",
    "AcquireRightsResponse1",
    "AcquireRightsResponse2",
    "AcquireRightsResponse3",
    "AcquireRightsResponse4",
    "Asset",
    "Background",
    "Campaign",
    "Claim",
    "Claim1",
    "Claim2",
    "Claim3",
    "ClaimEntry",
    "ClaimEntry1",
    "ClaimEntry2",
    "ClaimEntry3",
    "ClaimEntry4",
    "ClaimTypeFromVerifyBrandClaimRequest",
    "ClaimTypeFromVerifyBrandClaimResponse",
    "ClaimTypeFromVerifyBrandClaimsResponse",
    "Colors",
    "CountryFromAcquireRightsRequest",
    "CountryFromGetRightsRequest",
    "CountryFromRightsTerms",
    "CountryFromSearchBrandsRequest",
    "CountryFromSearchBrandsResponse",
    "CountryFromVerifyBrandClaimsRequest",
    "CreativeApprovalRequest",
    "CreativeApprovalResponse",
    "CreativeApprovalResponse1",
    "CreativeApprovalResponse2",
    "CreativeApprovalResponse3",
    "CreativeApprovalResponse4",
    "Disclosure",
    "Excluded",
    "ExcludedCountry",
    "Exclusivity",
    "ExclusivityStatus",
    "Field1",
    "File",
    "FontRole2",
    "Fonts",
    "GetBrandIdentityRequest",
    "GetBrandIdentityResponse",
    "GetBrandIdentityResponse1",
    "GetBrandIdentityResponse2",
    "GetRightsRequest",
    "GetRightsResponse",
    "GetRightsResponse1",
    "GetRightsResponse2",
    "HouseFromGetBrandIdentityResponse",
    "HouseFromSearchBrandsResponse",
    "KellerType",
    "LogoFromGetBrandIdentityResponse",
    "LogoFromSearchBrandsResponse",
    "Orientation",
    "PreviewAsset",
    "Property",
    "RelationshipTrust",
    "ResultEntry",
    "ResultEntry1",
    "ResultEntry2",
    "RevocationNotification",
    "Right",
    "RightsFromGetBrandIdentityResponse",
    "RightsFromSearchBrandsResponse",
    "RightsPricingOption",
    "RightsTerms",
    "SearchBrandResult",
    "SearchBrandsRequest",
    "SearchBrandsResponse",
    "Store",
    "Tone",
    "UpdateRightsRequest",
    "UpdateRightsResponse",
    "UpdateRightsResponse1",
    "UpdateRightsResponse2",
    "Variant",
    "VerificationStatus",
    "VerifyBrandClaimErrorResponse",
    "VerifyBrandClaimPayload",
    "VerifyBrandClaimRequest",
    "VerifyBrandClaimResponse",
    "VerifyBrandClaimSignedResponse",
    "VerifyBrandClaimSignedSuccessPayload",
    "VerifyBrandClaimSuccessResponse",
    "VerifyBrandClaimsErrorResponse",
    "VerifyBrandClaimsPayload",
    "VerifyBrandClaimsRequest",
    "VerifyBrandClaimsRequestBulk",
    "VerifyBrandClaimsResponse",
    "VerifyBrandClaimsResponseBulk",
    "VerifyBrandClaimsSignedResponse",
    "VerifyBrandClaimsSignedSuccessPayload",
    "VoiceSynthesis",
]
