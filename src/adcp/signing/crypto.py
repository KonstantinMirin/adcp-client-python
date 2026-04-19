"""Crypto primitives for the AdCP request-signing profile.

Supported algorithms per RFC 9421 profile:
- `ed25519` (EdDSA over Curve25519)
- `ecdsa-p256-sha256` (ES256)

ES256 signatures use IEEE P1363 (r||s, 64 bytes) per RFC 9421 §3.3.2. The
`cryptography` library emits/accepts DER by default, so sign() and verify()
convert at the boundary.

Encrypted PEM support (passphrase-protected private keys) is tracked in #191.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from adcp.signing.canonical import split_structured_field

PublicKey = ed25519.Ed25519PublicKey | ec.EllipticCurvePublicKey
PrivateKey = ed25519.Ed25519PrivateKey | ec.EllipticCurvePrivateKey

ALG_ED25519 = "ed25519"
ALG_ES256 = "ecdsa-p256-sha256"
ALLOWED_ALGS: frozenset[str] = frozenset({ALG_ED25519, ALG_ES256})

# Ed25519 raw public-key and ECDSA-P-256 coordinate lengths (both 32 bytes).
# Defensive byte-length check before the library's on-curve validation.
_RAW_KEY_BYTES = 32


def b64url_decode(s: str) -> bytes:
    """Decode base64url, tolerating missing padding."""
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    """Encode bytes as base64url without padding."""
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def public_key_from_jwk(jwk: dict[str, Any]) -> PublicKey:
    """Reconstruct a public key from its JWK."""
    kty = jwk.get("kty")
    crv = jwk.get("crv")
    if kty == "OKP" and crv == "Ed25519":
        x_raw = b64url_decode(jwk["x"])
        if len(x_raw) != _RAW_KEY_BYTES:
            raise ValueError(f"Ed25519 JWK x has length {len(x_raw)}, expected {_RAW_KEY_BYTES}")
        return ed25519.Ed25519PublicKey.from_public_bytes(x_raw)
    if kty == "EC" and crv == "P-256":
        x_raw = b64url_decode(jwk["x"])
        y_raw = b64url_decode(jwk["y"])
        if len(x_raw) != _RAW_KEY_BYTES or len(y_raw) != _RAW_KEY_BYTES:
            raise ValueError(
                f"P-256 JWK x/y must be {_RAW_KEY_BYTES} bytes each, "
                f"got x={len(x_raw)} y={len(y_raw)}"
            )
        x = int.from_bytes(x_raw, "big")
        y = int.from_bytes(y_raw, "big")
        return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
    raise ValueError(f"unsupported JWK kty/crv: {kty}/{crv}")


def private_key_from_jwk(jwk: dict[str, Any], *, d_field: str = "d") -> PrivateKey:
    """Reconstruct a private key from its JWK.

    `d_field` lets callers read from a non-standard scalar field — the AdCP test
    vectors store the private half under `_private_d_for_test_only` to signal
    that the keys are not production-grade.
    """
    kty = jwk.get("kty")
    crv = jwk.get("crv")
    if kty == "OKP" and crv == "Ed25519":
        d_raw = b64url_decode(jwk[d_field])
        if len(d_raw) != _RAW_KEY_BYTES:
            raise ValueError(f"Ed25519 JWK d has length {len(d_raw)}, expected {_RAW_KEY_BYTES}")
        return ed25519.Ed25519PrivateKey.from_private_bytes(d_raw)
    if kty == "EC" and crv == "P-256":
        d_raw = b64url_decode(jwk[d_field])
        x_raw = b64url_decode(jwk["x"])
        y_raw = b64url_decode(jwk["y"])
        if (
            len(d_raw) != _RAW_KEY_BYTES
            or len(x_raw) != _RAW_KEY_BYTES
            or len(y_raw) != _RAW_KEY_BYTES
        ):
            raise ValueError(
                f"P-256 JWK d/x/y must be {_RAW_KEY_BYTES} bytes each, "
                f"got d={len(d_raw)} x={len(x_raw)} y={len(y_raw)}"
            )
        d = int.from_bytes(d_raw, "big")
        x = int.from_bytes(x_raw, "big")
        y = int.from_bytes(y_raw, "big")
        pub = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1())
        return ec.EllipticCurvePrivateNumbers(d, pub).private_key()
    raise ValueError(f"unsupported JWK kty/crv: {kty}/{crv}")


def alg_for_jwk(jwk: dict[str, Any]) -> str:
    """Map a JWK to its RFC 9421 alg name for the AdCP profile."""
    kty = jwk.get("kty")
    crv = jwk.get("crv")
    if kty == "OKP" and crv == "Ed25519":
        return ALG_ED25519
    if kty == "EC" and crv == "P-256":
        return ALG_ES256
    raise ValueError(f"unsupported JWK kty/crv: {kty}/{crv}")


def verify_signature(
    *,
    alg: str,
    public_key: PublicKey,
    signature_base: bytes,
    signature: bytes,
) -> bool:
    """Return True iff `signature` is valid over `signature_base` for `alg`."""
    if alg not in ALLOWED_ALGS:
        raise ValueError(f"unsupported alg: {alg}")
    try:
        if alg == ALG_ED25519:
            if not isinstance(public_key, ed25519.Ed25519PublicKey):
                return False
            public_key.verify(signature, signature_base)
            return True
        if alg == ALG_ES256:
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                return False
            if len(signature) != 64:
                return False
            r = int.from_bytes(signature[:32], "big")
            s = int.from_bytes(signature[32:], "big")
            der = encode_dss_signature(r, s)
            public_key.verify(der, signature_base, ec.ECDSA(hashes.SHA256()))
            return True
    except InvalidSignature:
        return False
    return False


def sign_signature_base(
    *,
    alg: str,
    private_key: PrivateKey,
    signature_base: bytes,
) -> bytes:
    """Produce a signature over the base. ES256 returns r||s (64 bytes)."""
    if alg == ALG_ED25519:
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise ValueError("alg/private_key mismatch: expected Ed25519 key")
        return private_key.sign(signature_base)
    if alg == ALG_ES256:
        if not isinstance(private_key, ec.EllipticCurvePrivateKey):
            raise ValueError("alg/private_key mismatch: expected EC P-256 key")
        der = private_key.sign(signature_base, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")
    raise ValueError(f"unsupported alg: {alg}")


def extract_signature_bytes(signature_header: str, label: str = "sig1") -> bytes:
    """Parse a Signature header value and return the raw signature bytes for `label`.

    The value is an sf-dictionary: `sig1=:<base64>:[, sig2=:<base64>:]`.
    RFC 8941 specifies standard base64; the AdCP vectors use base64url. Both
    are accepted here (standard tried first; url as fallback).
    """
    for entry in split_structured_field(signature_header, ","):
        entry = entry.strip()
        if not entry:
            continue
        eq = entry.find("=")
        if eq < 0:
            continue
        name = entry[:eq].strip()
        value = entry[eq + 1 :].strip()
        if name != label:
            continue
        if not (value.startswith(":") and value.endswith(":")):
            raise ValueError(f"Signature value for {label!r} is not an sf-binary: {value!r}")
        inner = value[1:-1]
        try:
            return base64.b64decode(inner, validate=True)
        except (ValueError, binascii.Error):
            return b64url_decode(inner)
    raise KeyError(f"label not found in Signature header: {label}")


def format_signature_header(signature: bytes, label: str = "sig1") -> str:
    """Produce a Signature header value for a single-label signature."""
    return f"{label}=:{b64url_encode(signature)}:"
