"""Framework helpers for running the AdCP request-signing verifier.

These are thin wrappers around `verify_request_signature`. The spec requires
rejection with `401` and `WWW-Authenticate: Signature error="<code>"` (no
realm) — `unauthorized_response_headers` gives you that header exactly.
"""

from __future__ import annotations

from typing import Any

from adcp.signing.errors import SignatureVerificationError
from adcp.signing.verifier import (
    VerifiedSigner,
    VerifyOptions,
    verify_request_signature,
)


def unauthorized_response_headers(exc: SignatureVerificationError) -> dict[str, str]:
    """Headers for the 401 response. Realm is intentionally omitted per spec."""
    return {"WWW-Authenticate": f'Signature error="{exc.code}"'}


def verify_flask_request(request: Any, *, options: VerifyOptions) -> VerifiedSigner:
    """Verify a Flask `request` object against the AdCP profile."""
    return verify_request_signature(
        method=request.method,
        url=request.url,
        headers=dict(request.headers),
        body=request.get_data(),
        options=options,
    )


async def verify_starlette_request(request: Any, *, options: VerifyOptions) -> VerifiedSigner:
    """Verify a Starlette / FastAPI ``Request`` object against the AdCP profile.

    Consumes ``await request.body()`` once — Starlette caches the result
    internally, so downstream handlers calling ``request.body()`` or
    ``request.json()`` again will get the same bytes. If your handler
    needs the parsed body AFTER this verifier succeeds, call
    ``await request.body()`` yourself downstream; there's no hidden
    side channel on the returned :class:`VerifiedSigner`.

    Returns
    -------
    VerifiedSigner
        On success — carries the verified ``key_id`` and metadata.

    Raises
    ------
    SignatureVerificationError
        On any failure of the AdCP verifier checklist. The ``.code``
        attribute holds the spec's error code string (e.g.
        ``request_signature_replayed``) and ``.step`` points at the
        failed checklist step. Frameworks typically map this to a 401
        with :func:`unauthorized_response_headers`.
    """
    body = await request.body()
    return verify_request_signature(
        method=request.method,
        url=str(request.url),
        headers=dict(request.headers),
        body=body,
        options=options,
    )


__all__ = [
    "unauthorized_response_headers",
    "verify_flask_request",
    "verify_starlette_request",
]
