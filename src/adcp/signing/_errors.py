"""Error taxonomy for the AdCP request-signing profile.

Codes match the transport error taxonomy defined in `security.mdx`. The code
string is the normative surface — middleware adapters emit a `401` response
with `WWW-Authenticate: Signature error="<code>"` (no realm).
"""

from __future__ import annotations


class SignatureVerificationError(Exception):
    """Raised when a request signature fails any step of the verifier checklist."""

    def __init__(
        self,
        code: str,
        *,
        step: int | str | None = None,
        message: str | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.step = step


REQUEST_SIGNATURE_REQUIRED = "request_signature_required"
REQUEST_SIGNATURE_HEADER_MALFORMED = "request_signature_header_malformed"
REQUEST_SIGNATURE_PARAMS_INCOMPLETE = "request_signature_params_incomplete"
REQUEST_SIGNATURE_TAG_INVALID = "request_signature_tag_invalid"
REQUEST_SIGNATURE_ALG_NOT_ALLOWED = "request_signature_alg_not_allowed"
REQUEST_SIGNATURE_WINDOW_INVALID = "request_signature_window_invalid"
REQUEST_SIGNATURE_COMPONENTS_INCOMPLETE = "request_signature_components_incomplete"
REQUEST_SIGNATURE_COMPONENTS_UNEXPECTED = "request_signature_components_unexpected"
REQUEST_SIGNATURE_KEY_UNKNOWN = "request_signature_key_unknown"
REQUEST_SIGNATURE_KEY_PURPOSE_INVALID = "request_signature_key_purpose_invalid"
REQUEST_SIGNATURE_INVALID = "request_signature_invalid"
REQUEST_SIGNATURE_DIGEST_MISMATCH = "request_signature_digest_mismatch"
REQUEST_SIGNATURE_REPLAYED = "request_signature_replayed"
REQUEST_SIGNATURE_KEY_REVOKED = "request_signature_key_revoked"
REQUEST_SIGNATURE_REVOCATION_STALE = "request_signature_revocation_stale"
REQUEST_SIGNATURE_JWKS_UNAVAILABLE = "request_signature_jwks_unavailable"
REQUEST_SIGNATURE_JWKS_UNTRUSTED = "request_signature_jwks_untrusted"
REQUEST_SIGNATURE_RATE_ABUSE = "request_signature_rate_abuse"
