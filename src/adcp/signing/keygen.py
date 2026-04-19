"""Key generation helpers for AdCP request signing.

Writes a PEM private key and prints the matching JWK (public half) with
`adcp_use: "request-signing"` — paste that JWK into your agent's JWKS at the
URL advertised in brand.json.

Usage:
    adcp-keygen --alg ed25519 --out private-key.pem
    adcp-keygen --alg es256 --out private-key.pem
    adcp-keygen --alg ed25519 --encrypt --out private-key.pem
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from adcp.signing.crypto import ALG_ED25519, ALG_ES256, b64url_encode


def _encryption_algorithm(
    passphrase: bytes | None,
) -> serialization.KeySerializationEncryption:
    if passphrase is None:
        return serialization.NoEncryption()
    return serialization.BestAvailableEncryption(passphrase)


def generate_ed25519(kid: str, passphrase: bytes | None = None) -> tuple[bytes, dict[str, Any]]:
    private = ed25519.Ed25519PrivateKey.generate()
    pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=_encryption_algorithm(passphrase),
    )
    public = private.public_key()
    x = public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    jwk = {
        "kty": "OKP",
        "crv": "Ed25519",
        "alg": "EdDSA",
        "use": "sig",
        "key_ops": ["verify"],
        "adcp_use": "request-signing",
        "kid": kid,
        "x": b64url_encode(x),
    }
    return pem, jwk


def generate_es256(kid: str, passphrase: bytes | None = None) -> tuple[bytes, dict[str, Any]]:
    private = ec.generate_private_key(ec.SECP256R1())
    pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=_encryption_algorithm(passphrase),
    )
    numbers = private.public_key().public_numbers()
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "alg": "ES256",
        "use": "sig",
        "key_ops": ["verify"],
        "adcp_use": "request-signing",
        "kid": kid,
        "x": b64url_encode(numbers.x.to_bytes(32, "big")),
        "y": b64url_encode(numbers.y.to_bytes(32, "big")),
    }
    return pem, jwk


def _prompt_passphrase_bytes() -> bytes:
    first = getpass.getpass("Passphrase: ")
    if not first:
        print("error: passphrase cannot be empty", file=sys.stderr)
        raise SystemExit(2)
    second = getpass.getpass("Confirm passphrase: ")
    if first != second:
        print("error: passphrases do not match", file=sys.stderr)
        raise SystemExit(2)
    # NFC-normalize so a passphrase typed on macOS (which may emit NFD for some
    # composed characters) round-trips against the same passphrase typed on
    # Linux/Windows. CPython can't truly zero the plaintext string, but encoding
    # to bytes here lets the caller drop the string reference promptly.
    return unicodedata.normalize("NFC", first).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="adcp-keygen",
        description="Generate a signing keypair for the AdCP request-signing profile.",
    )
    parser.add_argument(
        "--alg",
        choices=["ed25519", "es256"],
        default="ed25519",
        help="Signature algorithm (default: ed25519)",
    )
    parser.add_argument(
        "--kid",
        default=None,
        help="Key ID to embed in the JWK (default: generated from alg + timestamp)",
    )
    parser.add_argument(
        "--out",
        default="adcp-signing-key.pem",
        help="Path to write the PEM private key (default: adcp-signing-key.pem)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output path if it exists",
    )
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help=(
            "Prompt for a passphrase and encrypt the PEM with BestAvailableEncryption. "
            "Suitable for dev laptops and CI test keys; for automated deployments the "
            "default unencrypted PKCS8 (protected by mode 0600) is usually what you want."
        ),
    )
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    if out_path.exists() and not args.force:
        print(
            f"refusing to overwrite {out_path} — pass --force to replace",
            file=sys.stderr,
        )
        return 2

    passphrase = _prompt_passphrase_bytes() if args.encrypt else None

    kid = args.kid or f"adcp-{args.alg}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    if args.alg == "ed25519":
        pem, jwk = generate_ed25519(kid, passphrase=passphrase)
        alg_rfc = ALG_ED25519
    else:
        pem, jwk = generate_es256(kid, passphrase=passphrase)
        alg_rfc = ALG_ES256

    # `--force` clobbers in two steps (non-atomic on overwrite), but the
    # happy-path create is atomic via O_EXCL | mode=0o600 so there is no window
    # where the file exists with permissive perms.
    if args.force and out_path.exists():
        out_path.unlink()
    fd = os.open(str(out_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, pem)
    finally:
        os.close(fd)

    encryption_note = ", encrypted" if passphrase is not None else ""
    print(
        f"wrote PEM private key to {out_path} (mode 600{encryption_note})",
        file=sys.stderr,
    )
    print(
        f"rfc 9421 alg: {alg_rfc}   (use this for `alg` in Signature-Input)",
        file=sys.stderr,
    )
    print("publish this JWK (public half) at your agent's jwks_uri:", file=sys.stderr)
    print(json.dumps({"keys": [jwk]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
