"""Byte-for-byte canonicalization check against AdCP request-signing vectors.

The committed positive-vector signatures are trustworthy only if our canonical
signature base agrees with `expected_signature_base` in every vector. This test
proves that — independent of crypto, HTTP, JWKS, or replay logic — before any
other stage is built on top.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adcp.signing.canonical import (
    build_signature_base,
    parse_signature_input_header,
)

VECTORS_DIR = Path(__file__).parent.parent / "vectors" / "request-signing"


def _vectors_with_expected_base() -> list[tuple[str, Path]]:
    all_vectors = sorted((VECTORS_DIR / "positive").glob("*.json")) + sorted(
        (VECTORS_DIR / "negative").glob("*.json")
    )
    result = [
        (p.name, p) for p in all_vectors if "expected_signature_base" in json.loads(p.read_text())
    ]
    assert result, f"no vectors with expected_signature_base under {VECTORS_DIR}"
    return result


@pytest.mark.parametrize(
    ("name", "path"),
    _vectors_with_expected_base(),
    ids=lambda v: v if isinstance(v, str) else v.name,
)
def test_signature_base_matches_expected(name: str, path: Path) -> None:
    vector = json.loads(path.read_text())
    request = vector["request"]
    sig_input_header = request["headers"]["Signature-Input"]
    labels = parse_signature_input_header(sig_input_header)
    assert "sig1" in labels, f"{name}: no sig1 label in Signature-Input"

    computed = build_signature_base(
        method=request["method"],
        url=request["url"],
        headers=request["headers"],
        parsed=labels["sig1"],
    )
    assert computed == vector["expected_signature_base"], (
        f"{name}: signature base mismatch\n"
        f"  expected: {vector['expected_signature_base']!r}\n"
        f"  computed: {computed!r}"
    )


def test_multi_label_signature_input_selects_sig1() -> None:
    """Per spec, verifiers process exactly sig1 and ignore additional labels."""
    vector = json.loads(
        (VECTORS_DIR / "positive" / "004-multiple-signature-labels.json").read_text()
    )
    labels = parse_signature_input_header(vector["request"]["headers"]["Signature-Input"])
    assert set(labels) == {"sig1", "sig2"}
    assert labels["sig1"].components == (
        "@method",
        "@target-uri",
        "@authority",
        "content-type",
    )
    assert labels["sig2"].components == ("@method", "@target-uri")
    assert labels["sig1"].params["nonce"] == "KXYnfEfJ0PBRZXQyVXfVQA"
    assert labels["sig2"].params["nonce"] == "DIFFERENT-NONCE-FOR-SIG2____"
