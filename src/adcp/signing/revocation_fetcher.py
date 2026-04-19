"""Live revocation-list fetcher + caching checker.

The AdCP governance profile publishes a signed revocation list at
``{issuer-origin}/.well-known/governance-revocations.json``. Verifiers
poll the list, verify its JWS, and reject tokens signed under a revoked
``kid`` (or with a revoked ``jti``). This module ships:

* :class:`RevocationListFetcher` — Protocol callers can implement for
  alternate transports (Redis-backed mirror, local fixture, etc).
* :func:`default_revocation_list_fetcher` — SSRF-validated HTTPS fetch
  with ``If-None-Match`` support.
* :class:`CachingRevocationChecker` — implements the existing
  :class:`adcp.signing.revocation.RevocationChecker` Protocol. Handles
  first fetch, refetch near ``next_update``, 304s, and the spec's
  fail-closed rule past ``next_update + grace``.

The verifier plugs it into :class:`VerifyOptions.revocation_checker`.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

from adcp.signing.jwks import (
    DEFAULT_JWKS_TIMEOUT_SECONDS,
    JwksResolver,
    validate_jwks_uri,
)
from adcp.signing.jws import (
    JwsError,
    verify_jws_document,
)
from adcp.signing.revocation import RevocationList

logger = logging.getLogger(__name__)

REVOCATION_LIST_TYP = "adcp-gov-revocation+jws"

# Spec-declared polling bounds for execution-phase traffic.
MIN_POLLING_INTERVAL_SECONDS = 60  # spec floor
MAX_POLLING_INTERVAL_SECONDS = 15 * 60  # spec ceiling for execution phase

# Recommended grace multiplier: if a seller hasn't successfully refreshed
# within `next_update + grace * last_interval`, all subsequent is_revoked
# calls fail closed. Spec recommends 2×.
DEFAULT_GRACE_MULTIPLIER = 2.0

# Shape-validate `Last-Modified` before persisting it for the next
# `If-Modified-Since` request. The value comes from a (potentially
# untrusted) origin; echoing it verbatim into an outbound request header
# is header-injection-adjacent. We only accept an RFC 7231 HTTP-date
# shape, length-capped.
_HTTP_DATE_MAX_LEN = 64
# RFC 7231 §7.1.1.1 defines three formats; IMF-fixdate is the normative
# one. We accept all three shapes loosely via regex on the visible
# characters — no attempt to parse as a real date, since the server
# hands it back to us opaquely.
_HTTP_DATE_PATTERN = re.compile(r"^[A-Za-z0-9 ,:+\-]+$")


class RevocationListFetchError(Exception):
    """The fetcher cannot retrieve the list (network / HTTP / SSRF).

    Mapped to ``request_signature_revocation_stale`` at the verifier
    edge when it occurs past the grace window; within the grace window
    the cached list is served and the error is logged at debug level.
    """


class RevocationListParseError(Exception):
    """The fetched document is malformed, fails schema validation, or
    violates the spec's polling-cadence floor.

    Mapped to ``request_signature_revocation_stale`` at the verifier
    edge. Parse errors within the grace window fall back to the cached
    list; past the grace window they surface as
    :class:`RevocationListFreshnessError`.

    :class:`RevocationListSignatureError` is a subclass of this class —
    callers that catch this exception catch signature failures too.
    """


class RevocationListSignatureError(RevocationListParseError):
    """The JWS signature does not verify against the configured JWKS.

    Subclass of :class:`RevocationListParseError` so callers that catch
    parse errors catch this too. Mapped to
    ``request_signature_revocation_stale`` at the verifier edge.

    Not re-exported from :mod:`adcp.signing` — import from
    :mod:`adcp.signing.revocation_fetcher` if you specifically want to
    distinguish signature failures from other parse failures.
    """


class RevocationListFreshnessError(Exception):
    """The cached list is past ``next_update + grace`` and refetch failed.

    Mapped to ``request_signature_revocation_stale`` at the verifier
    edge. The spec requires fail-closed behavior here — serving a stale
    list lets an attacker DoS the revocation endpoint to extend a
    compromised key's fraud window indefinitely.
    """


@dataclass(frozen=True)
class FetchResult:
    """Output of a successful revocation-list fetch.

    ``body`` is the raw JWS document — compact string or general-JSON
    dict. ``etag`` / ``last_modified`` capture server-side freshness
    hints for the next conditional request. ``not_modified=True``
    indicates a 304 response; in that case ``body`` is unused and the
    caller continues serving the cached list.
    """

    body: str | dict[str, Any]
    etag: str | None
    last_modified: str | None = None
    not_modified: bool = False


class RevocationListFetcher(Protocol):
    """Fetch a revocation-list JWS document.

    Implementations return a ``FetchResult`` on success. On 304
    (conditional request), ``not_modified=True`` and the caller
    continues serving the cached list. Transport-level concerns
    (private-network support, TLS settings, etc.) are the fetcher's
    construction-time config — not arguments the checker threads through
    on every call.
    """

    def __call__(
        self,
        uri: str,
        *,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult: ...


def default_revocation_list_fetcher(
    uri: str,
    *,
    if_none_match: str | None = None,
    if_modified_since: str | None = None,
    allow_private: bool = False,
    timeout: float = DEFAULT_JWKS_TIMEOUT_SECONDS,
) -> FetchResult:
    """HTTPS GET the revocation list, honoring SSRF rules and conditional requests.

    Reuses ``validate_jwks_uri`` — the SSRF controls are identical (same
    reserved-range rejection, same cloud-metadata block). ``httpx``
    re-resolves the hostname on connect, which is the TOCTOU window
    tracked separately in #190. Sends ``If-None-Match`` when an ETag is
    supplied and ``If-Modified-Since`` when a ``Last-Modified`` is
    supplied; the spec accepts either (sellers SHOULD use both when
    available).
    """
    validate_jwks_uri(uri, allow_private=allow_private)
    headers = {"Accept": "application/jose+json, application/json, application/jose"}
    if if_none_match is not None:
        headers["If-None-Match"] = if_none_match
    if if_modified_since is not None:
        headers["If-Modified-Since"] = if_modified_since

    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.get(uri, headers=headers)
    except httpx.HTTPError as exc:
        raise RevocationListFetchError(f"revocation list GET {uri!r} failed: {exc}") from exc

    if response.status_code == 304:
        return FetchResult(
            body="",
            etag=if_none_match,
            last_modified=if_modified_since,
            not_modified=True,
        )
    if response.status_code != 200:
        raise RevocationListFetchError(
            f"revocation list {uri!r} returned HTTP {response.status_code}"
        )

    etag = response.headers.get("ETag")
    last_modified = _sanitize_last_modified(response.headers.get("Last-Modified"))
    raw_body = response.text.strip()

    # General JSON serialization starts with `{`; compact form is three
    # base64url segments separated by dots. Dispatch by first-byte shape
    # rather than trusting Content-Type, which is unreliable in practice.
    if not raw_body:
        raise RevocationListFetchError(f"revocation list {uri!r} returned empty body")

    body: str | dict[str, Any]
    if raw_body.startswith("{"):
        try:
            body = json.loads(raw_body)
        except ValueError as exc:
            raise RevocationListFetchError(
                f"revocation list {uri!r} body is neither compact JWS nor valid JSON: {exc}"
            ) from exc
    else:
        body = raw_body

    return FetchResult(
        body=body,
        etag=etag,
        last_modified=last_modified,
        not_modified=False,
    )


def _sanitize_last_modified(raw: str | None) -> str | None:
    """Validate a ``Last-Modified`` header value before persisting it.

    Returns the value if it matches RFC 7231 HTTP-date shape (letters,
    digits, space, comma, colon, plus, hyphen) and fits in
    :data:`_HTTP_DATE_MAX_LEN` bytes. Returns ``None`` otherwise — the
    caller then skips conditional-request fallback and relies on ETag
    alone. An attacker-controlled origin cannot inject CRLF or arbitrary
    bytes into our next outbound request header this way.
    """
    if raw is None:
        return None
    if len(raw) > _HTTP_DATE_MAX_LEN:
        return None
    if not _HTTP_DATE_PATTERN.match(raw):
        return None
    return raw


def _parse_iso8601(ts: str) -> datetime:
    """Accept ``2026-04-18T14:00:00Z`` (the spec format) and other ISO-8601 shapes."""
    raw = ts
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_issuer(issuer: str) -> str:
    """Normalize an origin string for byte-equal comparison.

    RFC 6454 origin: ``scheme://host[:port]`` — scheme is case-insensitive,
    host is case-insensitive (and IDNA-canonicalized), trailing slash is
    not part of the origin. Rejects userinfo (``user:pass@host``) because
    there's no legitimate reason for a governance issuer to include it
    and accepting it opens impersonation via ``attacker@gov.example.com``.

    Rejects any host that can't be encoded as ASCII via IDNA — blocks
    homoglyph attacks like ``https://goᴠ.example.com`` (U+1D20) that
    lowercase-fold to something visually but not byte-wise equal to the
    configured origin.
    """
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(issuer)
    if parts.scheme not in ("http", "https"):
        raise ValueError(f"issuer must be http or https, got {parts.scheme!r}")
    if parts.username or parts.password:
        raise ValueError("issuer must not contain userinfo (user:pass@host)")
    if not parts.hostname:
        raise ValueError(f"issuer has no host: {issuer!r}")

    # IDNA-encode the host to collapse unicode homoglyphs to ASCII
    # punycode. ``host.encode("idna")`` raises on characters outside the
    # IDNA allowlist — which is the failure mode we want.
    try:
        host_ascii = parts.hostname.encode("idna").decode("ascii").lower()
    except (UnicodeError, UnicodeEncodeError) as exc:
        raise ValueError(f"issuer host {parts.hostname!r} is not IDNA-valid: {exc}") from exc

    netloc = f"{host_ascii}:{parts.port}" if parts.port else host_ascii
    scheme = parts.scheme.lower()
    return urlunsplit((scheme, netloc, "", "", ""))


def _build_list_from_payload(payload: dict[str, Any], expected_issuer: str) -> RevocationList:
    """Validate the JWS payload schema and assemble a ``RevocationList``.

    Raises :class:`RevocationListParseError` on any schema violation,
    including out-of-bounds declared cadence (spec §Revocation says the
    floor is 60 s for execution-phase lists).
    """
    # Version: accept any positive integer. Unknown versions produce a
    # warning-style log via the base class but do not reject, because
    # hard-rejecting a future additive schema change would force every
    # verifier running an older SDK into fail-closed across ALL traffic
    # the moment an issuer rolls forward.
    version = payload.get("version")
    if not isinstance(version, int) or version < 1:
        raise RevocationListParseError(
            f"revocation list version {version!r} must be a positive integer"
        )

    issuer = payload.get("issuer")
    if not isinstance(issuer, str):
        raise RevocationListParseError("revocation list missing string field 'issuer'")
    try:
        normalized_issuer = _normalize_issuer(issuer)
    except ValueError as exc:
        raise RevocationListParseError(
            f"revocation list issuer {issuer!r} is not a valid origin: {exc}"
        ) from exc
    if normalized_issuer != expected_issuer:
        raise RevocationListParseError(
            f"revocation list issuer {issuer!r} does not match expected {expected_issuer!r} "
            f"(normalized comparison)"
        )

    for key in ("updated", "next_update"):
        if not isinstance(payload.get(key), str):
            raise RevocationListParseError(f"revocation list missing string field {key!r}")

    # Enforce the spec's polling-cadence floor on the DECLARED cadence.
    # An issuer that declared next_update - updated < 60s is violating
    # the spec; we reject rather than silently honoring it, since the
    # checker's cooldown would otherwise force a silent downgrade to
    # the 60s floor anyway.
    updated_dt = _parse_iso8601(payload["updated"])
    next_update_dt = _parse_iso8601(payload["next_update"])
    declared_interval = (next_update_dt - updated_dt).total_seconds()
    if declared_interval < MIN_POLLING_INTERVAL_SECONDS:
        raise RevocationListParseError(
            f"revocation list declared cadence ({declared_interval:.0f}s) is below "
            f"spec floor ({MIN_POLLING_INTERVAL_SECONDS}s)"
        )

    return RevocationList.from_dict(payload)


class CachingRevocationChecker:
    """Live revocation checker with caching, refetch, grace, and fail-closed.

    Implements the ``RevocationChecker`` Protocol — callable as
    ``checker(keyid) -> bool``. Fetches and verifies the list on first
    call, refetches when ``now >= next_update``, and raises
    :class:`RevocationListFreshnessError` (which the verifier maps to
    ``request_signature_revocation_stale``) once the cached list is past
    ``next_update + grace * last_interval``.

    The checker does not fetch at construction time — the first call is
    the trigger. This keeps ``__init__`` side-effect-free and defers
    network I/O to the first verification. Call :meth:`prime` at startup
    to fail-fast on misconfiguration.

    Thread safety
    -------------
    This class is NOT thread-safe. Concurrent ``__call__`` s that each
    trigger a refresh can race the ``self._current_list`` assignment —
    the later writer wins, which for our replay-rejection check means
    only the most recent fetch's list ends up cached (still consistent,
    but two HTTP round-trips happen instead of one). Wrap instances in
    an external lock if you run the verifier from a thread pool. An
    ``asyncio``-driven verifier (single-threaded event loop) is fine
    unmodified.

    Parameters
    ----------
    revocation_uri:
        Full URL, e.g. ``https://gov.example.com/.well-known/governance-revocations.json``.
    issuer:
        Expected ``iss`` origin (``https://gov.example.com``). Set this
        explicitly; do not infer from ``revocation_uri`` because the
        .well-known location could theoretically be on a sibling host.
    jwks_resolver:
        Resolves the ``kid`` on the revocation-list JWS header to a JWK.
        Same Protocol as the request-signing JWKS resolver. Typically a
        :class:`adcp.signing.CachingJwksResolver` pointed at the
        governance agent's JWKS.
    fetcher:
        Override for the HTTP fetcher (primarily for tests and alternate
        transports). Defaults to :func:`default_revocation_list_fetcher`.
        Transport-level config (private-network allowance, TLS settings,
        alternate timeout) lives on the fetcher — pass a pre-configured
        one via ``functools.partial`` if you need to customize.
    grace_multiplier:
        Grace window beyond ``next_update``, measured in multiples of
        the list's declared polling interval
        (``next_update - updated``). Defaults to 2× per spec recommendation.
    clock:
        Monotonic-time source; overridable for tests. Returns seconds.
    wall_clock:
        Wall-clock source returning a ``datetime`` in UTC. Used to
        evaluate ``next_update`` and ``updated`` against the current
        moment. Separate from ``clock`` because polling is measured as
        a duration but freshness is measured against absolute times.
    """

    def __init__(
        self,
        *,
        revocation_uri: str,
        issuer: str,
        jwks_resolver: JwksResolver,
        fetcher: RevocationListFetcher | None = None,
        grace_multiplier: float = DEFAULT_GRACE_MULTIPLIER,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        # Reject the common footgun of passing time.time (wall-clock
        # seconds) as the `clock` kwarg — `_ensure_fresh` assumes
        # monotonicity for cooldown math. Requiring `time.monotonic`
        # (or a dedicated monotonic test fake) keeps cooldowns correct
        # across wall-clock jumps.
        if clock is time.time:
            raise ValueError(
                "clock must be a monotonic time source (use time.monotonic, "
                "not time.time); wall-clock jumps would break cooldown math"
            )
        # Cast via Any so mypy doesn't complain about the differing
        # declared return types (float vs datetime) — we're asking
        # whether the caller bound the SAME callable to both slots.
        if clock is wall_clock:  # type: ignore[comparison-overlap]
            raise ValueError(
                "clock and wall_clock must be different sources — clock is "
                "monotonic seconds (cooldown timing), wall_clock is a UTC "
                "datetime source (freshness evaluation)"
            )

        self._revocation_uri = revocation_uri
        self._issuer = _normalize_issuer(issuer)
        self._jwks_resolver = jwks_resolver
        self._fetcher = fetcher or default_revocation_list_fetcher
        self._grace_multiplier = grace_multiplier
        self._clock = clock
        self._wall_clock = wall_clock

        self._current_list: RevocationList | None = None
        self._current_etag: str | None = None
        self._current_last_modified: str | None = None
        self._last_successful_refresh: float | None = None
        self._last_polling_interval_seconds: float | None = None
        # Cooldown state: when a refresh attempt fails, we don't retry
        # until at least MIN_POLLING_INTERVAL_SECONDS of monotonic time
        # have elapsed. Stops a high-traffic verifier from hammering a
        # dead revocation endpoint.
        self._last_refresh_attempt: float | None = None

    @classmethod
    def from_issuer_origin(
        cls,
        origin: str,
        *,
        jwks_resolver: JwksResolver,
        fetcher: RevocationListFetcher | None = None,
        grace_multiplier: float = DEFAULT_GRACE_MULTIPLIER,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> CachingRevocationChecker:
        """Build a checker from the issuer origin alone.

        The AdCP spec pins the revocation list at
        ``{origin}/.well-known/governance-revocations.json``. This
        classmethod fills that path in so callers supply one origin
        instead of three coordinated strings.

        >>> checker = CachingRevocationChecker.from_issuer_origin(
        ...     "https://gov.example.com",
        ...     jwks_resolver=my_jwks,
        ... )
        """
        normalized = _normalize_issuer(origin)
        revocation_uri = f"{normalized}/.well-known/governance-revocations.json"
        return cls(
            revocation_uri=revocation_uri,
            issuer=normalized,
            jwks_resolver=jwks_resolver,
            fetcher=fetcher,
            grace_multiplier=grace_multiplier,
            clock=clock,
            wall_clock=wall_clock,
        )

    def prime(self) -> None:
        """Fetch and verify the revocation list synchronously.

        Call this at application startup to fail-fast on configuration
        problems (wrong issuer, JWKS unreachable, operator down) rather
        than surfacing them at the first user verification. If priming
        fails, the exception propagates unchanged — let the startup
        handler decide whether to abort the process or retry with
        backoff.

        This is optional: the checker works perfectly without priming,
        lazily fetching on the first :meth:`__call__`.
        """
        self._ensure_fresh()

    def is_jti_revoked(self, jti: str) -> bool:
        """Return True iff ``jti`` is in the cached list's ``revoked_jtis``.

        Governance-token verifiers (AdCP security.mdx §Seller
        verification checklist step 14) check both ``kid`` and ``jti``.
        The plain :meth:`__call__` covers ``kid`` because that's the
        request-signing path; governance callers use this method for
        per-token revocation.

        Triggers a refresh if the cached list is past ``next_update``
        (same lifecycle as :meth:`__call__`).
        """
        self._ensure_fresh()
        if self._current_list is None:
            raise RevocationListFreshnessError("revocation list not available")
        return jti in self._current_list.revoked_jtis

    def __call__(self, keyid: str) -> bool:
        """Return True iff ``keyid`` is in the cached list's ``revoked_kids``.

        This is the RFC 9421 request-signing path (verifier checklist
        step 9). For governance-token verification (seller-verification
        checklist step 14) check both the signing ``kid`` here AND the
        token's ``jti`` via :meth:`is_jti_revoked`.
        """
        self._ensure_fresh()
        if self._current_list is None:
            # Unreachable in practice — _ensure_fresh raises on unsuccessful
            # first load. Guarded for mypy.
            raise RevocationListFreshnessError("revocation list not available")
        return self._current_list.is_revoked(keyid)

    def _ensure_fresh(self) -> None:
        now_wall = self._wall_clock()
        now_mono = self._clock()

        if self._current_list is None:
            self._refresh(conditional=False, now_wall=now_wall, now_mono=now_mono)
            return

        next_update = _parse_iso8601(self._current_list.next_update)
        if now_wall < next_update:
            # Cached list is still within its declared freshness window.
            return

        # Past next_update: try a refresh, but only if we haven't recently
        # attempted one. Without this cooldown a high-QPS verifier would
        # hammer a dead endpoint on every verification.
        since_last_attempt = (
            now_mono - self._last_refresh_attempt
            if self._last_refresh_attempt is not None
            else float("inf")
        )
        if since_last_attempt >= MIN_POLLING_INTERVAL_SECONDS:
            try:
                self._refresh(conditional=True, now_wall=now_wall, now_mono=now_mono)
                return
            except (RevocationListFetchError, RevocationListParseError) as exc:
                # Fall through to the grace-window check below.
                last_exc: Exception = exc
        else:
            last_exc = RevocationListFetchError(
                f"refresh cooldown not elapsed ({since_last_attempt:.0f}s < "
                f"{MIN_POLLING_INTERVAL_SECONDS}s)"
            )

        grace_seconds = self._grace_seconds()
        if now_wall.timestamp() >= next_update.timestamp() + grace_seconds:
            raise RevocationListFreshnessError(
                f"revocation list {self._revocation_uri!r} past next_update "
                f"({self._current_list.next_update}) + grace ({grace_seconds:.0f}s); "
                f"last refresh error: {last_exc}"
            ) from last_exc
        # Still within grace — serve the cached list.

    def _refresh(self, *, conditional: bool, now_wall: datetime, now_mono: float) -> None:
        self._last_refresh_attempt = now_mono
        if_none_match = self._current_etag if conditional else None
        if_modified_since = self._current_last_modified if conditional else None
        result = self._fetcher(
            self._revocation_uri,
            if_none_match=if_none_match,
            if_modified_since=if_modified_since,
        )
        if result.not_modified:
            # 304: server confirms the cached list is still current. Advance
            # the cached list's `next_update` by the declared polling
            # interval so subsequent calls don't re-enter the past-
            # next_update branch on every request — without this, the 60s
            # cooldown gate would fire once per verification request once
            # we cross the original next_update.
            self._last_successful_refresh = now_mono
            if self._current_list is not None and self._last_polling_interval_seconds:
                prior = _parse_iso8601(self._current_list.next_update)
                new_next_update = prior + timedelta(
                    seconds=self._last_polling_interval_seconds
                )
                self._current_list = RevocationList(
                    issuer=self._current_list.issuer,
                    updated=self._current_list.updated,
                    next_update=new_next_update.isoformat().replace("+00:00", "Z"),
                    revoked_kids=self._current_list.revoked_kids,
                    revoked_jtis=self._current_list.revoked_jtis,
                )
            return

        try:
            payload = verify_jws_document(
                result.body,
                jwks_resolver=self._jwks_resolver,
                expected_typ=REVOCATION_LIST_TYP,
            )
        except JwsError as exc:
            raise RevocationListSignatureError(
                f"revocation list JWS verification failed: {exc}"
            ) from exc

        revocation_list = _build_list_from_payload(payload, expected_issuer=self._issuer)

        updated = _parse_iso8601(revocation_list.updated)
        next_update = _parse_iso8601(revocation_list.next_update)

        # Verify `updated` is not in the future beyond clock skew. An issuer
        # whose clock is far ahead would otherwise force an immediate stale
        # rejection.
        if updated > now_wall.replace(microsecond=0):
            delta = (updated - now_wall).total_seconds()
            if delta > 60:  # 60s clock skew tolerance, mirrors JWS exp/iat rules
                raise RevocationListParseError(
                    f"revocation list updated={revocation_list.updated!r} is "
                    f"{delta:.0f}s in the future"
                )
        if next_update <= updated:
            raise RevocationListParseError(
                f"revocation list next_update {revocation_list.next_update!r} is not "
                f"after updated {revocation_list.updated!r}"
            )

        # Reject a freshly-fetched list whose `updated` is older than the
        # one we already have cached. Defense-in-depth against:
        # - CDN replaying a stale list after a kid has been revoked,
        # - operator-key compromise where an attacker serves an older list
        #   with revocations removed.
        # The spec doesn't permit un-revocation, so `updated` MUST be
        # monotonically non-decreasing across refreshes.
        if self._current_list is not None:
            current_updated = _parse_iso8601(self._current_list.updated)
            if updated < current_updated:
                raise RevocationListParseError(
                    f"revocation list updated={revocation_list.updated!r} is older "
                    f"than cached list updated={self._current_list.updated!r} — "
                    f"refusing to roll back"
                )

        self._current_list = revocation_list
        self._current_etag = result.etag
        # Sanitize again at write-side: custom fetcher impls may not have
        # validated the value before constructing FetchResult.
        self._current_last_modified = _sanitize_last_modified(result.last_modified)
        self._last_successful_refresh = now_mono
        # Declared cadence is already validated >= 60s and bounded above
        # at parse time; clamp to the spec ceiling as defense against an
        # issuer declaring an out-of-bounds ceiling value.
        self._last_polling_interval_seconds = min(
            MAX_POLLING_INTERVAL_SECONDS,
            (next_update - updated).total_seconds(),
        )

    def _grace_seconds(self) -> float:
        interval = self._last_polling_interval_seconds or MAX_POLLING_INTERVAL_SECONDS
        return interval * self._grace_multiplier


__all__ = [
    "CachingRevocationChecker",
    "DEFAULT_GRACE_MULTIPLIER",
    "FetchResult",
    "REVOCATION_LIST_TYP",
    "RevocationListFetchError",
    "RevocationListFetcher",
    "RevocationListFreshnessError",
    "RevocationListParseError",
    "default_revocation_list_fetcher",
]

# ``RevocationListSignatureError`` is intentionally not in __all__ and
# not re-exported from ``adcp.signing``. It remains a subclass of
# ``RevocationListParseError`` so callers who want to catch it can
# import it from this module directly; catching the parent covers the
# common case.
