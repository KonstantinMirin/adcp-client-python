"""Byte-for-byte canonicalization check against AdCP request-signing vectors.

The committed positive-vector signatures are trustworthy only if our canonical
signature base agrees with `expected_signature_base` in every vector. This test
proves that — independent of crypto, HTTP, JWKS, or replay logic — before any
other stage is built on top.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from _pytest.mark import ParameterSet

from adcp.signing.canonical import (
    build_signature_base,
    canonicalize_authority,
    canonicalize_target_uri,
    parse_signature_input_header,
)
from tests.conformance.signing.vectors import (
    VECTORS_DIR,
    load_canonicalization_cases,
    load_vector_set,
)

# Cases from canonicalization.json that the SDK does not yet satisfy, mapped to
# the issue tracking each gap. Marked strict so a fix XPASSes and forces the
# entry to be retired instead of lingering.
KNOWN_CANONICALIZATION_GAPS: dict[str, str] = {
    # No UTS-46 A-label conversion on the signing path. adcp.signing has a
    # canonicalize_host() helper, but canonical.py does not call it, so an IDN
    # authority signs and verifies under a non-ASCII host.
    "idn-to-punycode": "#977: IDN host is not converted to a Punycode A-label",
    "idn-mixed-case-to-punycode": "#977: IDN host is not converted to a Punycode A-label",
    # urlunsplit() cannot distinguish "no query" from "empty query", so the
    # trailing '?' is dropped and signer/verifier can disagree on the base.
    "trailing-empty-query-preserved": "#979: trailing '?' with an empty query is dropped",
    # Malformed authorities are canonicalized rather than rejected; the spec's
    # request_target_uri_malformed code is not implemented at all.
    "malformed-port-without-host": "#978: authority with a port but no host is accepted",
    "malformed-userinfo-without-host": "#978: authority with userinfo but no host is accepted",
    "malformed-empty-authority": "#978: empty authority is accepted",
    "malformed-bare-ipv6": "#978: unbracketed IPv6 literal is accepted",
    "malformed-ipv6-zone-identifier": "#978: RFC 6874 zone identifier is accepted",
}


def _vectors_with_expected_base() -> list[tuple[str, Path]]:
    all_vectors = load_vector_set("positive") + load_vector_set("negative")
    return [
        (name, path)
        for name, path in all_vectors
        if "expected_signature_base" in json.loads(path.read_text())
    ]


def _canonicalization_params() -> list[ParameterSet]:
    params = []
    for name, case in load_canonicalization_cases():
        marks = []
        if name in KNOWN_CANONICALIZATION_GAPS:
            marks.append(pytest.mark.xfail(strict=True, reason=KNOWN_CANONICALIZATION_GAPS[name]))
        params.append(pytest.param(name, case, marks=marks))
    return params


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


@pytest.mark.parametrize(("name", "case"), _canonicalization_params())
def test_canonicalization_case(name: str, case: dict[str, Any]) -> None:
    """Grade `canonicalization.json` -- pure URL canonicalization, no crypto.

    The per-vector `expected_signature_base` path only exercises the URL shapes
    that happen to appear in a signed vector. This fixture is the exhaustive
    set: IDN, IPv6, userinfo, empty-query and the six malformed-authority
    rejections, several of which no signed vector covers at all.
    """
    url = case["input_url"]

    if case.get("reject"):
        # The spec's expected_error_code here is request_target_uri_malformed,
        # which the SDK does not define. Assert the refusal, which is the
        # behavioral obligation; the code mapping follows once it exists.
        with pytest.raises(ValueError):
            canonicalize_target_uri(url)
        return

    assert (
        canonicalize_target_uri(url) == case["expected_target_uri"]
    ), f"{name}: @target-uri mismatch for {url!r} ({case['rule']})"
    assert (
        canonicalize_authority(url) == case["expected_authority"]
    ), f"{name}: @authority mismatch for {url!r} ({case['rule']})"


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
