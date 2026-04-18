"""Unit tests for the JWKS resolver and SSRF validation."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from adcp.signing import (
    CachingJwksResolver,
    SignatureVerificationError,
    SSRFValidationError,
    StaticJwksResolver,
    validate_jwks_uri,
)

# ---- SSRF validation ----


@pytest.mark.parametrize(
    "host_or_url",
    [
        "http://127.0.0.1/jwks.json",
        "https://10.0.0.1/jwks.json",
        "https://192.168.1.1/jwks.json",
        "https://172.16.0.1/jwks.json",
        "https://169.254.169.254/jwks.json",  # AWS/GCP metadata
        "http://localhost/jwks.json",
        "http://[::1]/jwks.json",
    ],
)
def test_ssrf_rejects_reserved_and_metadata(host_or_url: str) -> None:
    with pytest.raises(SSRFValidationError):
        validate_jwks_uri(host_or_url)


def test_ssrf_rejects_non_http_scheme() -> None:
    with pytest.raises(SSRFValidationError):
        validate_jwks_uri("file:///etc/passwd")


def test_ssrf_allows_public_hostnames() -> None:
    # Mock getaddrinfo to return a public IP so we don't hit the real DNS
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
    ):
        validate_jwks_uri("https://example.com/jwks.json")


def test_ssrf_allow_private_override() -> None:
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("127.0.0.1", 0))],
    ):
        validate_jwks_uri("http://localhost:8080/jwks.json", allow_private=True)


def test_ssrf_metadata_ip_blocked_even_with_allow_private() -> None:
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("169.254.169.254", 0))],
    ):
        with pytest.raises(SSRFValidationError):
            validate_jwks_uri("http://metadata.internal/jwks.json", allow_private=True)


def test_ssrf_rejects_ipv4_mapped_ipv6_metadata() -> None:
    # `::ffff:169.254.169.254` — IPv4-mapped IPv6. On Python 3.10 the direct
    # flag checks on this form are False; we must unwrap to the embedded IPv4
    # before checking, or the block list is silently bypassed.
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=[(10, 1, 6, "", ("::ffff:169.254.169.254", 0, 0, 0))],
    ):
        with pytest.raises(SSRFValidationError):
            validate_jwks_uri("https://[::ffff:169.254.169.254]/jwks")


def test_ssrf_blocks_oracle_metadata() -> None:
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("192.0.0.192", 0))],
    ):
        with pytest.raises(SSRFValidationError):
            validate_jwks_uri("http://oracle-metadata.example/jwks.json")


def test_ssrf_caps_resolved_address_scan() -> None:
    # Build 100 records where the first 32 are public and the 33rd is internal.
    # With the cap at 32, the scan stops before reaching the loopback address.
    infos = [(2, 1, 6, "", ("93.184.216.34", 0))] * 32 + [(2, 1, 6, "", ("127.0.0.1", 0))] * 68
    with patch(
        "adcp.signing._jwks.socket.getaddrinfo",
        return_value=infos,
    ):
        # Must pass: the validator stops scanning before the internal IP.
        validate_jwks_uri("https://example.com/jwks.json")


# ---- CachingJwksResolver ----


def _make_jwks(*kids: str) -> dict[str, Any]:
    return {"keys": [{"kid": k, "kty": "OKP", "crv": "Ed25519", "x": "stub"} for k in kids]}


def test_caching_resolver_hits_cache_on_known_kid() -> None:
    calls = 0

    def fetcher(uri: str, *, allow_private: bool = False) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return _make_jwks("k1", "k2")

    resolver = CachingJwksResolver("https://example.com/jwks.json", fetcher=fetcher)
    assert resolver("k1") is not None
    assert resolver("k1") is not None
    assert calls == 1


def test_caching_resolver_returns_none_for_unknown_kid() -> None:
    fetcher = lambda uri, **kw: _make_jwks("k1")  # noqa: E731
    resolver = CachingJwksResolver("https://example.com/jwks.json", fetcher=fetcher)
    assert resolver("unknown") is None


def test_caching_resolver_refetches_after_cooldown() -> None:
    calls = 0

    def fetcher(uri: str, *, allow_private: bool = False) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        # On first call, only k1 exists; on later calls, k2 appears
        return _make_jwks("k1", "k2") if calls > 1 else _make_jwks("k1")

    clock = {"t": 0.0}
    resolver = CachingJwksResolver(
        "https://example.com/jwks.json",
        fetcher=fetcher,
        cooldown_seconds=30.0,
        clock=lambda: clock["t"],
    )
    assert resolver("k1") is not None
    assert resolver("k2") is None  # no refresh because cooldown not elapsed
    assert calls == 1

    clock["t"] = 31.0  # cooldown elapsed
    assert resolver("k2") is not None
    assert calls == 2


def test_caching_resolver_wraps_ssrf_as_untrusted() -> None:
    def fetcher(uri: str, *, allow_private: bool = False) -> dict[str, Any]:
        raise SSRFValidationError("blocked")

    resolver = CachingJwksResolver("https://example.com/jwks.json", fetcher=fetcher)
    with pytest.raises(SignatureVerificationError) as exc:
        resolver("k1")
    assert exc.value.code == "request_signature_jwks_untrusted"


def test_caching_resolver_wraps_network_failure_as_unavailable() -> None:
    import httpx

    def fetcher(uri: str, *, allow_private: bool = False) -> dict[str, Any]:
        raise httpx.ConnectError("dns failed")

    resolver = CachingJwksResolver("https://example.com/jwks.json", fetcher=fetcher)
    with pytest.raises(SignatureVerificationError) as exc:
        resolver("k1")
    assert exc.value.code == "request_signature_jwks_unavailable"


# ---- StaticJwksResolver ----


def test_static_resolver() -> None:
    resolver = StaticJwksResolver(_make_jwks("k1", "k2"))
    assert resolver("k1") is not None
    assert resolver("unknown") is None
