"""Signer for the AdCP request-signing profile.

Produces the `Signature-Input`, `Signature`, and (optionally) `Content-Digest`
headers for a request, per the verifier checklist the other side will run.
The signer is a single pure function; there is no ambient state.
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass

from adcp.signing.canonical import (
    SignatureInputLabel,
    _lookup,
    build_signature_base,
)
from adcp.signing.constants import (
    DEFAULT_EXPIRES_IN_SECONDS,
    DEFAULT_TAG,
    MAX_WINDOW_SECONDS,
    NONCE_BYTES,
    SIG_LABEL_DEFAULT,
)
from adcp.signing.crypto import (
    ALG_ED25519,
    ALG_ES256,
    ALLOWED_ALGS,
    PrivateKey,
    b64url_encode,
    format_signature_header,
    sign_signature_base,
)
from adcp.signing.digest import compute_content_digest_sha256


@dataclass(frozen=True)
class SignedHeaders:
    """The headers a signer must add to the outgoing request."""

    signature_input: str
    signature: str
    content_digest: str | None = None

    def as_dict(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Signature-Input": self.signature_input,
            "Signature": self.signature,
        }
        if self.content_digest is not None:
            headers["Content-Digest"] = self.content_digest
        return headers


def sign_request(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    private_key: PrivateKey,
    key_id: str,
    alg: str,
    cover_content_digest: bool = False,
    created: int | None = None,
    expires_in_seconds: int = DEFAULT_EXPIRES_IN_SECONDS,
    nonce: str | None = None,
    tag: str = DEFAULT_TAG,
    label: str = SIG_LABEL_DEFAULT,
) -> SignedHeaders:
    """Sign a request and return the headers to add to it.

    The caller is responsible for attaching `SignedHeaders.as_dict()` to the
    outgoing HTTP request before sending.
    """
    if alg not in ALLOWED_ALGS:
        raise ValueError(f"alg must be one of {sorted(ALLOWED_ALGS)}, got {alg!r}")
    if expires_in_seconds <= 0 or expires_in_seconds > MAX_WINDOW_SECONDS:
        raise ValueError(
            f"expires_in_seconds must be in (0, {MAX_WINDOW_SECONDS}], got {expires_in_seconds}"
        )

    if created is None:
        created = int(time.time())
    expires = created + expires_in_seconds
    if nonce is None:
        nonce = b64url_encode(secrets.token_bytes(NONCE_BYTES))

    components = ["@method", "@target-uri", "@authority"]
    outgoing_headers: dict[str, str] = dict(headers)
    content_digest_value: str | None = None
    if _lookup(headers, "content-type") is not None:
        components.append("content-type")
    if cover_content_digest:
        content_digest_value = compute_content_digest_sha256(body)
        outgoing_headers["Content-Digest"] = content_digest_value
        components.append("content-digest")

    comp_serialized = "(" + " ".join(f'"{c}"' for c in components) + ")"
    params_serialized = (
        f';created={created};expires={expires};nonce="{nonce}"'
        f';keyid="{key_id}";alg="{alg}";tag="{tag}"'
    )
    raw_value = comp_serialized + params_serialized

    parsed = SignatureInputLabel(
        label=label,
        components=tuple(components),
        params={
            "created": created,
            "expires": expires,
            "nonce": nonce,
            "keyid": key_id,
            "alg": alg,
            "tag": tag,
        },
        raw_value=raw_value,
    )
    base = build_signature_base(
        method=method, url=url, headers=outgoing_headers, parsed=parsed
    ).encode("utf-8")
    sig_bytes = sign_signature_base(alg=alg, private_key=private_key, signature_base=base)

    return SignedHeaders(
        signature_input=f"{label}={raw_value}",
        signature=format_signature_header(sig_bytes, label=label),
        content_digest=content_digest_value,
    )


__all__ = [
    "ALG_ED25519",
    "ALG_ES256",
    "DEFAULT_EXPIRES_IN_SECONDS",
    "DEFAULT_TAG",
    "SignedHeaders",
    "sign_request",
]
