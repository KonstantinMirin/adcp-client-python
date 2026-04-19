"""AdCP RFC 9421 request-signing profile.

Implements the transport-layer signed-request profile from the AdCP specification.
See: https://adcontextprotocol.org/docs/building/implementation/security#signed-requests-transport-layer
"""

from __future__ import annotations

from adcp.signing.autosign import (
    SigningConfig,
    SigningDecision,
    operation_needs_signing,
)
from adcp.signing.canonical import (
    SignatureInputLabel,
    build_signature_base,
    canonicalize_authority,
    canonicalize_target_uri,
    parse_signature_input_header,
)
from adcp.signing.constants import (
    DEFAULT_EXPIRES_IN_SECONDS,
    DEFAULT_SKEW_SECONDS,
    DEFAULT_TAG,
    MAX_WINDOW_SECONDS,
    NONCE_BYTES,
    SIG_LABEL_DEFAULT,
)
from adcp.signing.crypto import (
    ALG_ED25519,
    ALG_ES256,
    ALLOWED_ALGS,
    alg_for_jwk,
    b64url_decode,
    b64url_encode,
    extract_signature_bytes,
    format_signature_header,
    private_key_from_jwk,
    public_key_from_jwk,
    sign_signature_base,
    verify_signature,
)
from adcp.signing.digest import compute_content_digest_sha256, content_digest_matches
from adcp.signing.errors import (
    REQUEST_SIGNATURE_ALG_NOT_ALLOWED,
    REQUEST_SIGNATURE_COMPONENTS_INCOMPLETE,
    REQUEST_SIGNATURE_COMPONENTS_UNEXPECTED,
    REQUEST_SIGNATURE_DIGEST_MISMATCH,
    REQUEST_SIGNATURE_HEADER_MALFORMED,
    REQUEST_SIGNATURE_INVALID,
    REQUEST_SIGNATURE_JWKS_UNAVAILABLE,
    REQUEST_SIGNATURE_JWKS_UNTRUSTED,
    REQUEST_SIGNATURE_KEY_PURPOSE_INVALID,
    REQUEST_SIGNATURE_KEY_REVOKED,
    REQUEST_SIGNATURE_KEY_UNKNOWN,
    REQUEST_SIGNATURE_PARAMS_INCOMPLETE,
    REQUEST_SIGNATURE_RATE_ABUSE,
    REQUEST_SIGNATURE_REPLAYED,
    REQUEST_SIGNATURE_REQUIRED,
    REQUEST_SIGNATURE_REVOCATION_STALE,
    REQUEST_SIGNATURE_TAG_INVALID,
    REQUEST_SIGNATURE_WINDOW_INVALID,
    SignatureVerificationError,
)
from adcp.signing.jwks import (
    CachingJwksResolver,
    SSRFValidationError,
    StaticJwksResolver,
    default_jwks_fetcher,
    validate_jwks_uri,
)
from adcp.signing.middleware import (
    unauthorized_response_headers,
    verify_flask_request,
    verify_starlette_request,
)
from adcp.signing.replay import InMemoryReplayStore, ReplayStore
from adcp.signing.revocation import RevocationChecker, RevocationList
from adcp.signing.signer import (
    SignedHeaders,
    sign_request,
)
from adcp.signing.verifier import (
    JwksResolver,
    VerifiedSigner,
    VerifierCapability,
    VerifyOptions,
    verify_request_signature,
)

__all__ = [
    "ALG_ED25519",
    "ALG_ES256",
    "ALLOWED_ALGS",
    "CachingJwksResolver",
    "DEFAULT_EXPIRES_IN_SECONDS",
    "DEFAULT_SKEW_SECONDS",
    "DEFAULT_TAG",
    "InMemoryReplayStore",
    "JwksResolver",
    "MAX_WINDOW_SECONDS",
    "NONCE_BYTES",
    "REQUEST_SIGNATURE_ALG_NOT_ALLOWED",
    "REQUEST_SIGNATURE_COMPONENTS_INCOMPLETE",
    "REQUEST_SIGNATURE_COMPONENTS_UNEXPECTED",
    "REQUEST_SIGNATURE_DIGEST_MISMATCH",
    "REQUEST_SIGNATURE_HEADER_MALFORMED",
    "REQUEST_SIGNATURE_INVALID",
    "REQUEST_SIGNATURE_JWKS_UNAVAILABLE",
    "REQUEST_SIGNATURE_JWKS_UNTRUSTED",
    "REQUEST_SIGNATURE_KEY_PURPOSE_INVALID",
    "REQUEST_SIGNATURE_KEY_REVOKED",
    "REQUEST_SIGNATURE_KEY_UNKNOWN",
    "REQUEST_SIGNATURE_PARAMS_INCOMPLETE",
    "REQUEST_SIGNATURE_RATE_ABUSE",
    "REQUEST_SIGNATURE_REPLAYED",
    "REQUEST_SIGNATURE_REQUIRED",
    "REQUEST_SIGNATURE_REVOCATION_STALE",
    "REQUEST_SIGNATURE_TAG_INVALID",
    "REQUEST_SIGNATURE_WINDOW_INVALID",
    "ReplayStore",
    "RevocationChecker",
    "RevocationList",
    "SIG_LABEL_DEFAULT",
    "SSRFValidationError",
    "SignatureInputLabel",
    "SignatureVerificationError",
    "SignedHeaders",
    "SigningConfig",
    "SigningDecision",
    "StaticJwksResolver",
    "VerifiedSigner",
    "VerifierCapability",
    "VerifyOptions",
    "alg_for_jwk",
    "b64url_decode",
    "b64url_encode",
    "build_signature_base",
    "canonicalize_authority",
    "canonicalize_target_uri",
    "compute_content_digest_sha256",
    "content_digest_matches",
    "default_jwks_fetcher",
    "extract_signature_bytes",
    "format_signature_header",
    "operation_needs_signing",
    "parse_signature_input_header",
    "private_key_from_jwk",
    "public_key_from_jwk",
    "sign_request",
    "sign_signature_base",
    "unauthorized_response_headers",
    "validate_jwks_uri",
    "verify_flask_request",
    "verify_request_signature",
    "verify_signature",
    "verify_starlette_request",
]
