"""IP-pinned httpx transports that close the DNS-rebinding TOCTOU.

The default signing fetchers (JWKS + revocation-list, sync + async)
resolve the target hostname via :func:`resolve_and_validate_host`,
then hand the URL back to httpx — which resolves the hostname a
second time at connect. A malicious origin with ``TTL=0`` can return
a safe IP on the first lookup (passing SSRF validation) and a
private IP or cloud-metadata address on the second.

This module closes that gap. :func:`build_ip_pinned_transport`
resolves once, picks the first IP that passes the SSRF validator,
and returns an :class:`httpx.HTTPTransport` wired to a custom
:mod:`httpcore` network backend that translates the pinned
hostname → IP at connect time. TLS certificate validation still
runs against the original hostname (httpcore passes it separately
as ``server_hostname`` during the TLS handshake), so cert CN/SAN
matching is unaffected.

The transport is single-host-scoped. Reusing it for a DIFFERENT
hostname would bypass the pin and either connect to the wrong IP
or fail SSRF re-resolution. Build one transport per hostname you
need to reach; the existing fetchers do this per-call.

Naming conventions
------------------

* Classes use the ``Async`` CapWords prefix
  (:class:`AsyncIpPinnedTransport`).
* Free functions use the ``async_``/``a`` prefix
  (:func:`abuild_ip_pinned_transport`) — matches the rest of this
  sub-package.

Dependency on httpcore internals
--------------------------------

We reach into httpcore at two points:

1. ``httpcore.ConnectionPool(network_backend=...)`` — public API.
2. ``httpcore._backends.sync.SyncBackend`` /
   ``httpcore._backends.anyio.AnyIOBackend`` — underscore-prefixed
   path, nominally private. The backend classes are the documented
   default-backend implementations, and the ``network_backend`` kwarg
   is the sanctioned extension point, but the stability of the
   backend class names themselves isn't guaranteed.

Mitigations:

* ``pyproject.toml`` pins ``httpcore>=1.0,<2.0``.
* :class:`adcp.signing.ip_pinned_transport` exports the backend
  signatures from a contract test that fails on import if upstream
  changes them — see
  ``tests/conformance/signing/test_ip_pinned_transport.py``.
"""

from __future__ import annotations

import ssl
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import httpcore
import httpx

# Private but documented-as-the-default-backend implementations. The
# underscore prefix is a stability hazard; the contract test in
# tests/conformance/signing/test_ip_pinned_transport.py fails if the
# signatures we rely on change, so a silent upstream break becomes a
# CI failure instead of a latent security regression.
from httpcore._backends.anyio import AnyIOBackend as _AnyIOBackend
from httpcore._backends.sync import SyncBackend as _SyncBackend

from adcp.signing.jwks import (
    DEFAULT_JWKS_TIMEOUT_SECONDS,
    resolve_and_validate_host,
)

if TYPE_CHECKING:
    from httpcore._backends.base import SOCKET_OPTION


__all__ = [
    "AsyncIpPinnedTransport",
    "IpPinnedTransport",
    "abuild_ip_pinned_transport",
    "build_ip_pinned_transport",
]


def _build_ssl_context() -> ssl.SSLContext:
    """Standard cert-validating TLS context. ``check_hostname`` stays True
    so the hostname-in-cert-SAN match runs against the URL's original
    host (the hostname httpcore passes as ``server_hostname`` during
    the handshake), not the pinned IP.
    """
    return ssl.create_default_context()


class _IpPinnedSyncBackend(_SyncBackend):
    """httpcore sync backend that connects by IP for one pinned hostname.

    Delegates to the parent's ``connect_tcp`` after swapping the
    host argument from the hostname to the pre-resolved IP. All
    other methods (``connect_unix_socket``) pass through unchanged.
    """

    def __init__(self, *, hostname: str, resolved_ip: str) -> None:
        super().__init__()
        self._hostname = hostname.lower()
        self._resolved_ip = resolved_ip

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[SOCKET_OPTION] | None = None,
    ) -> Any:
        if host.lower() == self._hostname:
            host = self._resolved_ip
        return super().connect_tcp(
            host=host,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class _IpPinnedAsyncBackend(_AnyIOBackend):
    """Async counterpart to :class:`_IpPinnedSyncBackend`."""

    def __init__(self, *, hostname: str, resolved_ip: str) -> None:
        super().__init__()
        self._hostname = hostname.lower()
        self._resolved_ip = resolved_ip

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[SOCKET_OPTION] | None = None,
    ) -> Any:
        if host.lower() == self._hostname:
            host = self._resolved_ip
        return await super().connect_tcp(
            host=host,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class IpPinnedTransport(httpx.HTTPTransport):
    """``httpx.HTTPTransport`` that connects by pre-resolved IP.

    Preserves normal httpx ergonomics — pass this to
    ``httpx.Client(transport=...)`` and everything else works
    unchanged. The TLS handshake uses the original hostname for
    SNI + cert validation; only the TCP destination is rewritten.

    Construct via :func:`build_ip_pinned_transport` unless you've
    already resolved the hostname yourself.
    """

    def __init__(
        self,
        *,
        hostname: str,
        resolved_ip: str,
        verify: bool = True,
        retries: int = 0,
    ) -> None:
        if verify:
            ssl_context = _build_ssl_context()
        else:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        backend = _IpPinnedSyncBackend(hostname=hostname, resolved_ip=resolved_ip)
        # Build the ConnectionPool ourselves (rather than super().__init__
        # and then reassign ._pool) so the TLS + backend config is set
        # up atomically and we don't briefly own a vanilla pool.
        self._pool = httpcore.ConnectionPool(
            ssl_context=ssl_context,
            network_backend=backend,
            http1=True,
            http2=False,
            retries=retries,
        )


class AsyncIpPinnedTransport(httpx.AsyncHTTPTransport):
    """Async counterpart to :class:`IpPinnedTransport`."""

    def __init__(
        self,
        *,
        hostname: str,
        resolved_ip: str,
        verify: bool = True,
        retries: int = 0,
    ) -> None:
        if verify:
            ssl_context = _build_ssl_context()
        else:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        backend = _IpPinnedAsyncBackend(hostname=hostname, resolved_ip=resolved_ip)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl_context,
            network_backend=backend,
            http1=True,
            http2=False,
            retries=retries,
        )


def build_ip_pinned_transport(
    uri: str,
    *,
    allow_private: bool = False,
    verify: bool = True,
) -> IpPinnedTransport:
    """Resolve ``uri`` once and return a transport pinned to the validated IP.

    Raises :class:`SSRFValidationError` if the URI's scheme isn't
    ``http``/``https``, the host doesn't resolve, or every resolved
    IP is in a blocked range.

    Typical use inside a fetcher::

        transport = build_ip_pinned_transport(uri)
        with httpx.Client(transport=transport, timeout=10.0) as client:
            response = client.get(uri)
    """
    hostname, resolved_ip, _port = resolve_and_validate_host(uri, allow_private=allow_private)
    return IpPinnedTransport(hostname=hostname, resolved_ip=resolved_ip, verify=verify)


def abuild_ip_pinned_transport(
    uri: str,
    *,
    allow_private: bool = False,
    verify: bool = True,
) -> AsyncIpPinnedTransport:
    """Async counterpart to :func:`build_ip_pinned_transport`.

    The resolution itself is synchronous (``socket.getaddrinfo``);
    this function is not actually awaitable, but the prefix matches
    the rest of the sub-package's naming and the returned transport
    is async.
    """
    hostname, resolved_ip, _port = resolve_and_validate_host(uri, allow_private=allow_private)
    return AsyncIpPinnedTransport(hostname=hostname, resolved_ip=resolved_ip, verify=verify)


# Quiet the unused-import warning — DEFAULT_JWKS_TIMEOUT_SECONDS is
# imported for re-export convenience and callers who want to pair the
# transport with a matching timeout.
_ = DEFAULT_JWKS_TIMEOUT_SECONDS
