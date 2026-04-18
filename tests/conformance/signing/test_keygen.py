"""Generate a keypair, load it, sign with it, verify with the matching JWK."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization

from adcp.signing import (
    StaticJwksResolver,
    VerifierCapability,
    VerifyOptions,
    sign_request,
    verify_request_signature,
)
from adcp.signing.keygen import generate_ed25519, generate_es256, main


@pytest.mark.parametrize(
    ("generator", "alg"),
    [(generate_ed25519, "ed25519"), (generate_es256, "ecdsa-p256-sha256")],
)
def test_generated_keypair_signs_and_verifies(generator, alg: str) -> None:
    pem, jwk = generator(kid="test-kid")
    assert jwk["adcp_use"] == "request-signing"
    assert jwk["use"] == "sig"
    assert jwk["key_ops"] == ["verify"]

    private_key = serialization.load_pem_private_key(pem, password=None)

    body = b'{"x":1}'
    url = "https://seller.example.com/adcp/create_media_buy"
    signed = sign_request(
        method="POST",
        url=url,
        headers={"Content-Type": "application/json"},
        body=body,
        private_key=private_key,  # type: ignore[arg-type]
        key_id="test-kid",
        alg=alg,
    )
    headers = {"Content-Type": "application/json", **signed.as_dict()}

    options = VerifyOptions(
        now=float(int(time.time())),
        capability=VerifierCapability(
            covers_content_digest="either",
            required_for=frozenset({"create_media_buy"}),
        ),
        operation="create_media_buy",
        jwks_resolver=StaticJwksResolver({"keys": [jwk]}),
    )
    verify_request_signature(method="POST", url=url, headers=headers, body=body, options=options)


def test_cli_main_writes_pem_and_prints_jwks(tmp_path: Path, capsys) -> None:
    out = tmp_path / "key.pem"
    rc = main(["--alg", "ed25519", "--out", str(out), "--kid", "my-kid"])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0
    # mode 600
    assert oct(out.stat().st_mode)[-3:] == "600"

    captured = capsys.readouterr()
    jwks = json.loads(captured.out)
    assert jwks["keys"][0]["kid"] == "my-kid"
    assert jwks["keys"][0]["adcp_use"] == "request-signing"


def test_cli_main_refuses_overwrite_without_force(tmp_path: Path, capsys) -> None:
    out = tmp_path / "key.pem"
    out.write_bytes(b"existing")
    rc = main(["--alg", "ed25519", "--out", str(out)])
    assert rc == 2
    assert out.read_bytes() == b"existing"
