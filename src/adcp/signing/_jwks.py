"""JWKS fetching and caching for the AdCP request-signing profile.

Production deployments MUST validate JWKS URIs against SSRF per the AdCP
webhook-URL rules: reject reserved IP ranges (loopback, private, link-local,
multicast, reserved) and known cloud metadata endpoints. This module enforces
those rules at resolution time and provides a per-URL cache with a 30-second
refetch cooldown between fetches — the cooldown blocks attack-driven cache
invalidation (where an attacker forces a verifier to hammer the signer's
`jwks_uri` on every rejection).

DNS-rebinding-resistant transport (resolve-then-connect with IP pinning) is
tracked in #190 and not implemented here — the current design is vulnerable to
a TOCTOU where DNS resolves to an allowed IP during validation and a blocked
IP at connect time.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from collections.abc import Callable
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx

from adcp.signing._errors import (
    REQUEST_SIGNATURE_JWKS_UNAVAILABLE,
    REQUEST_SIGNATURE_JWKS_UNTRUSTED,
    SignatureVerificationError,
)

DEFAULT_JWKS_COOLDOWN_SECONDS = 30.0
DEFAULT_JWKS_TIMEOUT_SECONDS = 10.0

# Cloud metadata endpoints that MUST be blocked even if somehow marked non-private
BLOCKED_METADATA_IPS: frozenset[str] = frozenset(
    {
        "169.254.169.254",  # AWS, Azure, GCP, DigitalOcean, Alibaba
        "fd00:ec2::254",  # AWS IPv6
        "100.100.100.200",  # Alibaba
        "192.0.0.192",  # Oracle Cloud
    }
)

# Upper bound on the number of resolved addresses examined per validation call.
# A malicious DNS server can return thousands of records as a mild amplification
# vector against the validator's inner loop.
_MAX_RESOLVED_ADDRESSES = 32


class SSRFValidationError(Exception):
    """Raised when a URL resolves to an IP in a reserved or blocked range."""


class JwksFetcher(Protocol):
    """A callable that fetches and parses a JWKS document from a URL."""

    def __call__(self, uri: str, *, allow_private: bool = False) -> dict[str, Any]: ...


def validate_jwks_uri(uri: str, *, allow_private: bool = False) -> None:
    """Raise SSRFValidationError if `uri` resolves to a blocked IP or has a bad scheme."""
    parts = urlsplit(uri)
    if parts.scheme not in ("http", "https"):
        raise SSRFValidationError(f"unsupported scheme for JWKS URI: {parts.scheme!r}")
    host = parts.hostname
    if host is None or host == "":
        raise SSRFValidationError("JWKS URI has no host")

    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise SSRFValidationError(f"cannot resolve host {host!r}: {exc}") from exc

    for _family, _, _, _, sockaddr in infos[:_MAX_RESOLVED_ADDRESSES]:
        ip_raw = sockaddr[0]
        ip_str = str(ip_raw)
        # Strip IPv6 scope id if present
        if "%" in ip_str:
            ip_str = ip_str.split("%", 1)[0]
        ip: ipaddress.IPv4Address | ipaddress.IPv6Address = ipaddress.ip_address(ip_str)
        # Unwrap IPv4-mapped IPv6 (::ffff:a.b.c.d). On Python 3.10 the direct
        # flag checks (is_loopback, is_private, etc.) on the mapped form return
        # False — the fix landed in 3.11.4 via bpo-44269. The SDK targets 3.10+
        # per pyproject.toml so we unwrap explicitly.
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        if str(ip) in BLOCKED_METADATA_IPS:
            raise SSRFValidationError(f"cloud metadata IP {ip} blocked")
        if allow_private:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise SSRFValidationError(f"resolved IP {ip} is in a reserved range")


def default_jwks_fetcher(uri: str, *, allow_private: bool = False) -> dict[str, Any]:
    """Validate the URI against SSRF rules, then GET the JWKS document."""
    validate_jwks_uri(uri, allow_private=allow_private)
    # follow_redirects=False is explicit: httpx already defaults to no-follow,
    # but an attacker controlling the JWKS origin could 302 us to an IP that
    # `validate_jwks_uri` already cleared.
    with httpx.Client(timeout=DEFAULT_JWKS_TIMEOUT_SECONDS, follow_redirects=False) as client:
        response = client.get(uri, headers={"Accept": "application/json"})
        response.raise_for_status()
        body = response.json()
    if not isinstance(body, dict) or "keys" not in body:
        raise ValueError(f"JWKS document at {uri!r} has no 'keys' array")
    return body


class CachingJwksResolver:
    """JWKS resolver with per-URI cache and refetch cooldown.

    Behavior:
    - On a lookup miss, refresh if the cooldown has elapsed since the last
      refresh (success or failure). This prevents attacker-driven
      request-amplification on the signer's JWKS endpoint.
    - Cache keyed on `kid`. Unknown keyids return None (verifier converts to
      `request_signature_key_unknown`).
    - SSRF failures surface as `request_signature_jwks_untrusted`; network
      failures surface as `request_signature_jwks_unavailable`.
    """

    def __init__(
        self,
        jwks_uri: str,
        *,
        fetcher: JwksFetcher | None = None,
        cooldown_seconds: float = DEFAULT_JWKS_COOLDOWN_SECONDS,
        allow_private: bool = False,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._jwks_uri = jwks_uri
        self._fetcher = fetcher or default_jwks_fetcher
        self._cooldown = cooldown_seconds
        self._allow_private = allow_private
        self._clock = clock
        self._cache: dict[str, dict[str, Any]] = {}
        self._last_attempt: float | None = None
        self._primed = False

    def __call__(self, keyid: str) -> dict[str, Any] | None:
        if keyid in self._cache:
            return self._cache[keyid]
        now = self._clock()
        if not self._primed or (
            self._last_attempt is not None and now - self._last_attempt >= self._cooldown
        ):
            self._refresh(now)
        return self._cache.get(keyid)

    def _refresh(self, now: float) -> None:
        self._last_attempt = now
        try:
            jwks = self._fetcher(self._jwks_uri, allow_private=self._allow_private)
        except SSRFValidationError as exc:
            raise SignatureVerificationError(
                REQUEST_SIGNATURE_JWKS_UNTRUSTED,
                step=7,
                message=f"JWKS URI failed SSRF check: {exc}",
            ) from exc
        except (httpx.HTTPError, ValueError, OSError) as exc:
            raise SignatureVerificationError(
                REQUEST_SIGNATURE_JWKS_UNAVAILABLE,
                step=7,
                message=f"JWKS fetch failed: {exc}",
            ) from exc
        self._primed = True
        self._cache = {jwk["kid"]: jwk for jwk in jwks.get("keys", []) if "kid" in jwk}


class StaticJwksResolver:
    """Resolves keyids from a fixed in-memory JWKS — convenient for tests."""

    def __init__(self, jwks: dict[str, Any]) -> None:
        self._keys = {jwk["kid"]: jwk for jwk in jwks.get("keys", []) if "kid" in jwk}

    def __call__(self, keyid: str) -> dict[str, Any] | None:
        return self._keys.get(keyid)


__all__ = [
    "BLOCKED_METADATA_IPS",
    "CachingJwksResolver",
    "DEFAULT_JWKS_COOLDOWN_SECONDS",
    "DEFAULT_JWKS_TIMEOUT_SECONDS",
    "JwksFetcher",
    "SSRFValidationError",
    "StaticJwksResolver",
    "default_jwks_fetcher",
    "validate_jwks_uri",
]
