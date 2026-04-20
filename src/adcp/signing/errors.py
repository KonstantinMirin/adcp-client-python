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

# Webhook-signing error taxonomy — adcp#2423 / webhooks.mdx + security.mdx.
# Distinct strings from the request-signing family so receivers can route the
# 401 response through webhook-specific observability.
WEBHOOK_SIGNATURE_REQUIRED = "webhook_signature_required"
WEBHOOK_SIGNATURE_HEADER_MALFORMED = "webhook_signature_header_malformed"
WEBHOOK_SIGNATURE_PARAMS_INCOMPLETE = "webhook_signature_params_incomplete"
WEBHOOK_SIGNATURE_TAG_INVALID = "webhook_signature_tag_invalid"
WEBHOOK_SIGNATURE_ALG_NOT_ALLOWED = "webhook_signature_alg_not_allowed"
WEBHOOK_SIGNATURE_WINDOW_INVALID = "webhook_signature_window_invalid"
WEBHOOK_SIGNATURE_COMPONENTS_INCOMPLETE = "webhook_signature_components_incomplete"
WEBHOOK_SIGNATURE_COMPONENTS_UNEXPECTED = "webhook_signature_components_unexpected"
WEBHOOK_SIGNATURE_KEY_UNKNOWN = "webhook_signature_key_unknown"
WEBHOOK_SIGNATURE_KEY_PURPOSE_INVALID = "webhook_signature_key_purpose_invalid"
WEBHOOK_SIGNATURE_INVALID = "webhook_signature_invalid"
WEBHOOK_SIGNATURE_DIGEST_MISMATCH = "webhook_signature_digest_mismatch"
WEBHOOK_SIGNATURE_REPLAYED = "webhook_signature_replayed"
WEBHOOK_SIGNATURE_KEY_REVOKED = "webhook_signature_key_revoked"
WEBHOOK_SIGNATURE_REVOCATION_STALE = "webhook_signature_revocation_stale"
WEBHOOK_SIGNATURE_JWKS_UNAVAILABLE = "webhook_signature_jwks_unavailable"
WEBHOOK_SIGNATURE_JWKS_UNTRUSTED = "webhook_signature_jwks_untrusted"
WEBHOOK_SIGNATURE_RATE_ABUSE = "webhook_signature_rate_abuse"

# Code-family translation used by the webhook verifier wrapper. The verifier
# pipeline raises request_signature_* codes; the wrapper retags them into
# webhook_signature_* before exposing to callers. Keeps the 300-line verifier
# unchanged and guarantees webhook routes never leak request-family codes.
REQUEST_TO_WEBHOOK_CODE = {
    REQUEST_SIGNATURE_REQUIRED: WEBHOOK_SIGNATURE_REQUIRED,
    REQUEST_SIGNATURE_HEADER_MALFORMED: WEBHOOK_SIGNATURE_HEADER_MALFORMED,
    REQUEST_SIGNATURE_PARAMS_INCOMPLETE: WEBHOOK_SIGNATURE_PARAMS_INCOMPLETE,
    REQUEST_SIGNATURE_TAG_INVALID: WEBHOOK_SIGNATURE_TAG_INVALID,
    REQUEST_SIGNATURE_ALG_NOT_ALLOWED: WEBHOOK_SIGNATURE_ALG_NOT_ALLOWED,
    REQUEST_SIGNATURE_WINDOW_INVALID: WEBHOOK_SIGNATURE_WINDOW_INVALID,
    REQUEST_SIGNATURE_COMPONENTS_INCOMPLETE: WEBHOOK_SIGNATURE_COMPONENTS_INCOMPLETE,
    REQUEST_SIGNATURE_COMPONENTS_UNEXPECTED: WEBHOOK_SIGNATURE_COMPONENTS_UNEXPECTED,
    REQUEST_SIGNATURE_KEY_UNKNOWN: WEBHOOK_SIGNATURE_KEY_UNKNOWN,
    REQUEST_SIGNATURE_KEY_PURPOSE_INVALID: WEBHOOK_SIGNATURE_KEY_PURPOSE_INVALID,
    REQUEST_SIGNATURE_INVALID: WEBHOOK_SIGNATURE_INVALID,
    REQUEST_SIGNATURE_DIGEST_MISMATCH: WEBHOOK_SIGNATURE_DIGEST_MISMATCH,
    REQUEST_SIGNATURE_REPLAYED: WEBHOOK_SIGNATURE_REPLAYED,
    REQUEST_SIGNATURE_KEY_REVOKED: WEBHOOK_SIGNATURE_KEY_REVOKED,
    REQUEST_SIGNATURE_REVOCATION_STALE: WEBHOOK_SIGNATURE_REVOCATION_STALE,
    REQUEST_SIGNATURE_JWKS_UNAVAILABLE: WEBHOOK_SIGNATURE_JWKS_UNAVAILABLE,
    REQUEST_SIGNATURE_JWKS_UNTRUSTED: WEBHOOK_SIGNATURE_JWKS_UNTRUSTED,
    REQUEST_SIGNATURE_RATE_ABUSE: WEBHOOK_SIGNATURE_RATE_ABUSE,
}
