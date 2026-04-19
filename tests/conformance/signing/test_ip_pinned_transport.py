"""Tests for :mod:`adcp.signing.ip_pinned_transport`.

Three kinds of coverage:

1. **Contract tests** — fail fast if httpcore's private-backend API
   shifts shape between versions. These protect against silent upstream
   breakage of the ``_backends`` subpackage we reach into.
2. **Rebinding simulation** — monkey-patch :func:`socket.getaddrinfo`
   so the first resolution returns a safe IP and a hypothetical
   second resolution would return a dangerous one. The pinned
   transport MUST connect to the first IP, and the second resolution
   MUST never happen.
3. **SSRF integration** — the fetchers defer resolution to
   :func:`resolve_and_validate_host`; reserved-range and
   cloud-metadata IPs still reject at construction.
"""

from __future__ import annotations

import inspect
import socket
from unittest.mock import patch

import httpcore
import pytest
from httpcore._backends.anyio import AnyIOBackend  # type: ignore[attr-defined]
from httpcore._backends.sync import SyncBackend  # type: ignore[attr-defined]

from adcp.signing import (
    AsyncIpPinnedTransport,
    IpPinnedTransport,
    SSRFValidationError,
    abuild_ip_pinned_transport,
    build_ip_pinned_transport,
    resolve_and_validate_host,
)

# -- contract tests ---------------------------------------------------


def test_httpcore_sync_backend_connect_tcp_signature_unchanged() -> None:
    """If httpcore changes ``SyncBackend.connect_tcp``, the pinned
    transport silently breaks. This test fails fast on upgrade so we
    notice during CI, not during a real rebinding attempt.
    """
    sig = inspect.signature(SyncBackend.connect_tcp)
    # Required positional: host, port. Then the rest are kwargs with
    # defaults. If any of these vanish, override becomes wrong.
    params = list(sig.parameters)
    assert params[0] == "self"
    assert params[1] == "host"
    assert params[2] == "port"
    assert "timeout" in params
    assert "local_address" in params
    assert "socket_options" in params


def test_httpcore_async_backend_connect_tcp_signature_unchanged() -> None:
    sig = inspect.signature(AnyIOBackend.connect_tcp)
    params = list(sig.parameters)
    assert params[0] == "self"
    assert params[1] == "host"
    assert params[2] == "port"
    assert "timeout" in params
    assert "local_address" in params
    assert "socket_options" in params


def test_httpcore_connection_pool_accepts_network_backend() -> None:
    """``ConnectionPool(network_backend=...)`` is the public extension
    point we rely on."""
    sig = inspect.signature(httpcore.ConnectionPool.__init__)
    assert "network_backend" in sig.parameters
    sig_async = inspect.signature(httpcore.AsyncConnectionPool.__init__)
    assert "network_backend" in sig_async.parameters


# -- resolve_and_validate_host ---------------------------------------


def test_resolve_returns_tuple_of_host_ip_port() -> None:
    host, ip, port = resolve_and_validate_host("https://example.com/jwks")
    assert host == "example.com"
    assert port == 443
    # Accepted IP is a string form, not a wrapped ipaddress object.
    assert isinstance(ip, str)
    # example.com resolves publicly; we just check the ip isn't private.
    import ipaddress

    parsed = ipaddress.ip_address(ip)
    assert not parsed.is_private
    assert not parsed.is_loopback


def test_resolve_defaults_http_port_80() -> None:
    # Even though we normally refuse non-https elsewhere, the helper
    # itself is scheme-agnostic for the port default.
    host, _ip, port = resolve_and_validate_host("http://example.com/jwks")
    assert host == "example.com"
    assert port == 80


def test_resolve_rejects_non_http_scheme() -> None:
    with pytest.raises(SSRFValidationError, match="scheme"):
        resolve_and_validate_host("ftp://example.com/jwks")


def test_resolve_rejects_private_result_without_allow_private() -> None:
    # Simulate getaddrinfo returning a private IP — a rebinding
    # attacker's payload.
    def fake_getaddrinfo(_host, _port, *_args, **_kwargs):
        return [(socket.AF_INET, 0, 0, "", ("10.0.0.1", 0))]

    with patch("adcp.signing.jwks.socket.getaddrinfo", side_effect=fake_getaddrinfo):
        with pytest.raises(SSRFValidationError, match="reserved range"):
            resolve_and_validate_host("https://example.com/")


def test_resolve_rejects_cloud_metadata_ip_even_with_allow_private() -> None:
    """Cloud metadata IPs are blocked unconditionally — not even
    ``allow_private=True`` unlocks them."""

    def fake_getaddrinfo(_host, _port, *_args, **_kwargs):
        return [(socket.AF_INET, 0, 0, "", ("169.254.169.254", 0))]

    with patch("adcp.signing.jwks.socket.getaddrinfo", side_effect=fake_getaddrinfo):
        with pytest.raises(SSRFValidationError, match="metadata"):
            resolve_and_validate_host("https://example.com/", allow_private=True)


# -- rebinding simulation --------------------------------------------


def test_transport_pins_first_resolution_against_rebinding() -> None:
    """Attacker scenario: TTL=0 DNS returns a safe IP first (passes
    validation), then returns a metadata IP on the second resolution.
    The transport MUST ignore the second resolution and connect to
    the first IP.
    """
    call_count = {"n": 0}

    def fake_getaddrinfo(_host, _port, *_args, **_kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Safe public IP — passes validation.
            return [(socket.AF_INET, 0, 0, "", ("8.8.8.8", 0))]
        # Any subsequent lookup would return cloud metadata.
        return [(socket.AF_INET, 0, 0, "", ("169.254.169.254", 0))]

    with patch("adcp.signing.jwks.socket.getaddrinfo", side_effect=fake_getaddrinfo):
        transport = build_ip_pinned_transport("https://attacker.example/")

    # One resolution happened during build; nothing else is allowed.
    assert call_count["n"] == 1

    # Inspect the backend the transport installed: the pinned IP must
    # be the first resolution, and the hostname match must be
    # case-insensitive for safety.
    pool = transport._pool
    backend = pool._network_backend  # type: ignore[attr-defined]
    assert backend._resolved_ip == "8.8.8.8"
    assert backend._hostname == "attacker.example"


def test_async_transport_pins_first_resolution_against_rebinding() -> None:
    call_count = {"n": 0}

    def fake_getaddrinfo(_host, _port, *_args, **_kwargs):
        call_count["n"] += 1
        return [(socket.AF_INET, 0, 0, "", ("1.1.1.1", 0))]

    with patch("adcp.signing.jwks.socket.getaddrinfo", side_effect=fake_getaddrinfo):
        transport = abuild_ip_pinned_transport("https://attacker.example/")

    assert call_count["n"] == 1
    pool = transport._pool
    backend = pool._network_backend  # type: ignore[attr-defined]
    assert backend._resolved_ip == "1.1.1.1"
    assert backend._hostname == "attacker.example"


def test_backend_connect_tcp_swaps_hostname_for_pinned_ip() -> None:
    """Directly test the backend's override — ``connect_tcp`` with the
    pinned hostname calls the parent with the resolved IP instead.
    """
    from adcp.signing.ip_pinned_transport import _IpPinnedSyncBackend

    backend = _IpPinnedSyncBackend(hostname="attacker.example", resolved_ip="198.51.100.30")

    captured = {}

    def _fake_parent_connect(self, *, host, port, timeout, local_address, socket_options):
        captured["host"] = host
        captured["port"] = port
        return object()  # stand-in for a NetworkStream

    with patch.object(SyncBackend, "connect_tcp", _fake_parent_connect):
        backend.connect_tcp(host="attacker.example", port=443)

    assert captured["host"] == "198.51.100.30"
    assert captured["port"] == 443


def test_backend_connect_tcp_leaves_other_hosts_unchanged() -> None:
    """If some code path reuses the transport for a DIFFERENT host
    (misuse), the backend MUST NOT silently route it to the pinned IP.
    """
    from adcp.signing.ip_pinned_transport import _IpPinnedSyncBackend

    backend = _IpPinnedSyncBackend(hostname="attacker.example", resolved_ip="198.51.100.40")
    captured = {}

    def _fake_parent_connect(self, *, host, port, timeout, local_address, socket_options):
        captured["host"] = host
        return object()

    with patch.object(SyncBackend, "connect_tcp", _fake_parent_connect):
        backend.connect_tcp(host="other.example", port=443)

    assert captured["host"] == "other.example"


def test_backend_hostname_match_is_case_insensitive() -> None:
    from adcp.signing.ip_pinned_transport import _IpPinnedSyncBackend

    backend = _IpPinnedSyncBackend(hostname="Attacker.Example", resolved_ip="198.51.100.50")
    captured = {}

    def _fake_parent_connect(self, *, host, port, timeout, local_address, socket_options):
        captured["host"] = host
        return object()

    with patch.object(SyncBackend, "connect_tcp", _fake_parent_connect):
        backend.connect_tcp(host="ATTACKER.example", port=443)

    assert captured["host"] == "198.51.100.50"


# -- real-network smoke (optional, skipped if no internet) ------------


def _internet_ok() -> bool:
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2).close()
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _internet_ok(), reason="no outbound internet")
def test_real_tls_handshake_still_validates_hostname() -> None:
    """End-to-end sanity: with the pinned transport, TLS cert
    validation still runs against the hostname (not the IP). A
    successful GET against a public HTTPS endpoint proves the TLS
    SNI + cert validation paths are intact.
    """
    import httpx

    transport = build_ip_pinned_transport("https://example.com/")
    # Generous timeout — this test is inherently network-dependent and
    # real TLS handshakes occasionally slow-run on constrained CI
    # machines. The intent is "handshake didn't reject", not speed.
    with httpx.Client(transport=transport, timeout=60.0) as client:
        response = client.get("https://example.com/")
    assert response.status_code == 200


@pytest.mark.skipif(not _internet_ok(), reason="no outbound internet")
def test_transport_type_is_httpx_httptransport() -> None:
    """The returned transport IS an httpx.HTTPTransport instance so
    callers can use it with httpx.Client without type-gymnastics."""
    import httpx

    transport = build_ip_pinned_transport("https://example.com/")
    assert isinstance(transport, httpx.HTTPTransport)
    assert isinstance(transport, IpPinnedTransport)

    atransport = abuild_ip_pinned_transport("https://example.com/")
    assert isinstance(atransport, httpx.AsyncHTTPTransport)
    assert isinstance(atransport, AsyncIpPinnedTransport)
