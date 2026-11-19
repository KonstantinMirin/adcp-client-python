"""Public surface and validation checks for AdCP 3.1 rc4 schema additions."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

_RC4_EXPORTS = (
    "MediaBuyDeliveryWebhookResult",
    "PricingCurrency",
    "ResponsePayloadJwsEnvelope",
    "SignalDefinitionEnrichment",
    "VerifyBrandClaimPayload",
    "VerifyBrandClaimSignedResponse",
    "VerifyBrandClaimSignedSuccessPayload",
    "VerifyBrandClaimsErrorResponse",
    "VerifyBrandClaimsPayload",
    "VerifyBrandClaimsResponse",
    "VerifyBrandClaimsSignedResponse",
    "VerifyBrandClaimsSignedSuccessPayload",
)


def test_rc4_symbols_are_publicly_exported() -> None:
    import adcp
    import adcp.types

    for name in _RC4_EXPORTS:
        assert hasattr(adcp, name), f"{name} not exported from adcp"
        assert name in adcp.__all__, f"{name} not declared in adcp.__all__"
        assert hasattr(adcp.types, name), f"{name} not exported from adcp.types"
        assert name in adcp.types.__all__, f"{name} not declared in adcp.types.__all__"


def test_verify_brand_claim_success_requires_signed_response() -> None:
    from adcp.types import VerifyBrandClaimResponse

    with pytest.raises(ValidationError, match="signed_response"):
        TypeAdapter(VerifyBrandClaimResponse).validate_python(
            {
                # Required one level up by `core/protocol-envelope.json` (`#/allOf/1`),
                # a 9-member enum; "completed" chosen.  Without it the envelope's own
                # refusal preempts the `signed_response` refusal under test.
                "status": "completed",
                "claim_type": "property",
                "verification_status": "owned",
            }
        )


def test_verify_brand_claim_signed_response_requires_payload() -> None:
    from adcp.types import VerifyBrandClaimSignedResponse

    with pytest.raises(ValidationError, match="payload"):
        VerifyBrandClaimSignedResponse.model_validate(
            {
                "protected": "abc",
                "signature": "def",
            }
        )


def test_verify_brand_claims_success_requires_signed_response_payload() -> None:
    from adcp.types import VerifyBrandClaimsResponseBulk, VerifyBrandClaimsSignedResponse

    result = {"claim_type": "property", "status": "owned"}
    with pytest.raises(ValidationError, match="signed_response"):
        # The envelope `status` (required at `#/allOf/1`, 9-member enum, "completed"
        # chosen) is the response's own, distinct from each result's `status`.
        VerifyBrandClaimsResponseBulk.model_validate(
            {"status": "completed", "results": [result]}
        )

    with pytest.raises(ValidationError, match="payload"):
        VerifyBrandClaimsSignedResponse.model_validate(
            {
                "protected": "abc",
                "signature": "def",
            }
        )
