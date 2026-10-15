"""Regressions for the final AdCP 3.3 agent-identity decisions (adcp-client-python#1500).

Each test names the decision it pins: the signature path follows DR-0023 and
WBA §5.5/§6.10, revocation and bindings are the authorization layer, trust
outages never restore access, and the hardening found in the Go and
TypeScript reviews.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx
import pytest
from asgi_lifespan import LifespanManager
from cryptography.hazmat.primitives.asymmetric import ed25519
from http_sfv.dictionary import Dictionary
from http_sfv.item import InnerList, Item
from starlette.requests import Request
from starlette.responses import JSONResponse

from adcp.decisioning.registry import BuyerAgent
from adcp.decisioning.trust_grants import (
    _MEDIA_BUY_DEFAULT_OPERATIONS,
    TrustGrantClaim,
    TrustGrantGate,
)
from adcp.decisioning.types import Account, AdcpError
from adcp.server import ADCPHandler, RequestSignatureVerification, ToolContext
from adcp.server.signed_requests import (
    SignedRequestVerificationMiddleware,
    _received_target_uri,
    apply_verified_signer,
    check_wba_authorization,
)
from adcp.server.translate import build_mcp_error_result
from adcp.signing import (
    InMemoryReplayStore,
    OriginBindings,
    StaticSignerKeys,
    TrustGrantEvaluator,
    TrustRecordEvaluator,
    TrustRecordMatchError,
    TrustRecordUnavailableError,
    TrustResponse,
    VerifiedSigner,
    public_directory_key,
    sign_request,
    sign_wba_request,
    trust_record_url,
    verify_request_signature,
)
from adcp.signing.crypto import b64url_encode
from adcp.signing.digest import compute_content_digest_sha256
from adcp.signing.middleware import VERIFIED_SIGNER_SCOPE_KEY
from adcp.signing.revocation_fetcher import FetchResult, RevocationListFetchError
from adcp.signing.signer_keys import ResolvedSignerKey
from adcp.signing.trust import TrustRecordError
from adcp.signing.wba import (
    DIRECTORY_MEDIA_TYPE,
    DIRECTORY_PATH,
    DIRECTORY_SKEW_ALLOWANCE_SECONDS,
    GENERIC_AUTHENTICATION_ERROR,
    DirectoryResponse,
    DiscoveredSignerKeys,
    OriginRevocationChecker,
    WbaDiscoveryError,
    WbaVerificationError,
    _base,
    _sign,
    sign_key_directory,
    verify_directory_response,
    verify_wba_request,
)

ORIGIN = "https://buyer.platform.com"
TARGET = "https://seller.example.com/mcp"


async def _not_revoked(origin: str, keyid: str) -> bool:
    return False


def _tool(name: str, arguments: dict[str, Any] | None = None) -> bytes:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
    ).encode()


def _signed(private: Any, body: bytes, *, origin: str = ORIGIN, url: str = TARGET, **kwargs: Any):
    headers = {"Content-Type": "application/json"}
    headers.update(
        sign_wba_request(
            method="POST",
            url=url,
            headers=headers,
            body=body,
            private_key=private,
            agent_origin=origin,
            **kwargs,
        )
    )
    return headers


def _member(value: str, label: str = "sig1") -> Any:
    parsed = Dictionary()
    parsed.parse(value.encode("ascii"))
    return parsed[label]


def _recording_app(config: RequestSignatureVerification, *, transport: str = "mcp"):
    seen: list[Any] = []

    async def dispatch(scope, receive, send):
        context = apply_verified_signer(None, Request(scope))
        try:
            check_wba_authorization(context)
        except AdcpError as exc:
            await JSONResponse(build_mcp_error_result(exc).model_dump(mode="json", by_alias=True))(
                scope, receive, send
            )
            return
        seen.append(scope.get(VERIFIED_SIGNER_SCOPE_KEY))
        await JSONResponse({"ok": True})(scope, receive, send)

    app = SignedRequestVerificationMiddleware(
        dispatch, config, transport=transport, defer_authorization_errors=True
    )
    return app, seen


# ---------------------------------------------------------------------------
# A1-A3: the signature path follows DR-0023 and WBA §6.10
# ---------------------------------------------------------------------------


async def test_discovery_failure_never_evicts_a_cached_directory_within_max_stale():
    private = ed25519.Ed25519PrivateKey.generate()
    kid = public_directory_key(private)["kid"]
    now, offline, calls = [1000.0], [False], []

    async def fetch(url, *, allow_private=False):
        calls.append(url)
        if offline[0]:
            raise OSError("directory host is down")
        return sign_key_directory(
            agent_origin=ORIGIN, private_keys=[private], created=1000, expires_in_seconds=100_000
        )

    keys = DiscoveredSignerKeys(fetcher=fetch, clock=lambda: now[0], max_stale_seconds=3600)
    assert await keys(kid, signer_origin=ORIGIN) is not None
    offline[0], now[0] = True, 1301  # past the five-minute refresh
    assert await keys(kid, signer_origin=ORIGIN) is not None
    # A key rotated in during the outage cannot be seen: a discovery failure.
    with pytest.raises(WbaDiscoveryError):
        await keys("n" * 43, signer_origin=ORIGIN)
    now[0] = 4599.0
    assert await keys(kid, signer_origin=ORIGIN) is not None
    now[0] = 4600.0  # max_stale after the last successful fetch
    with pytest.raises(WbaDiscoveryError) as failure:
        await keys(kid, signer_origin=ORIGIN)
    assert failure.value.status == 403 and failure.value.headers["Accept-Signature"]
    assert calls.count(ORIGIN + DIRECTORY_PATH) == 3  # 60 s cooldown between attempts


async def test_cached_directory_never_verifies_past_its_signatures():
    private = ed25519.Ed25519PrivateKey.generate()
    kid = public_directory_key(private)["kid"]
    now, offline = [1000.0], [False]

    async def fetch(url, *, allow_private=False):
        if offline[0]:
            return DirectoryResponse(b"", {}, status=503)
        return sign_key_directory(
            agent_origin=ORIGIN, private_keys=[private], created=900, expires_in_seconds=600
        )

    keys = DiscoveredSignerKeys(fetcher=fetch, clock=lambda: now[0])
    assert await keys(kid, signer_origin=ORIGIN) is not None
    offline[0], now[0] = True, 1499
    assert await keys(kid, signer_origin=ORIGIN) is not None
    now[0] = 1500
    with pytest.raises(WbaDiscoveryError):
        await keys(kid, signer_origin=ORIGIN)


async def test_local_discovery_capacity_is_load_shedding_not_a_challenge():
    private = ed25519.Ed25519PrivateKey.generate()
    kid = public_directory_key(private)["kid"]
    entered, release = asyncio.Event(), asyncio.Event()

    async def fetch(url, *, allow_private=False):
        entered.set()
        await asyncio.wait_for(release.wait(), timeout=5)
        return sign_key_directory(agent_origin=ORIGIN, private_keys=[private], created=1000)

    keys = DiscoveredSignerKeys(fetcher=fetch, max_origins=1, clock=lambda: 1000)
    pending = asyncio.create_task(keys(kid, signer_origin=ORIGIN))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        with pytest.raises(WbaVerificationError) as refused:
            await keys(kid, signer_origin="https://buyer.other.com")
        assert refused.value.status == 429
        assert not refused.value.discovery_failure
        assert "Accept-Signature" not in refused.value.headers
    finally:
        release.set()
        assert await asyncio.wait_for(pending, timeout=5) is not None


@pytest.mark.parametrize("policy", ["reject", "anonymous"])
@pytest.mark.parametrize("operation", ["get_products", "create_media_buy"])
async def test_unresolvable_directory_is_unverified_under_local_policy(policy, operation):
    private = ed25519.Ed25519PrivateKey.generate()

    async def fetch(url, *, allow_private=False):
        return DirectoryResponse(b"", {}, status=404)

    config = RequestSignatureVerification(
        signer_keys=DiscoveredSignerKeys(fetcher=fetch),
        enable_web_bot_auth=True,
        wba_revocation_checker=_not_revoked,
        required_for=frozenset({"create_media_buy"}),
        wba_discovery_failure=policy,
    )
    app, seen = _recording_app(config)
    body = _tool(operation)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app)) as client:
        response = await client.post(TARGET, content=body, headers=_signed(private, body))
    if policy == "anonymous" and operation == "get_products":
        # Served exactly as an anonymous request: no verified signer.
        assert response.status_code == 200
        assert seen == [None]
    else:
        # Default policy, or an operation that requires a signature.
        assert response.status_code == 403
        assert response.json() == GENERIC_AUTHENTICATION_ERROR
        assert "Accept-Signature" in response.headers
        assert not seen


async def test_wba_request_to_a_seller_without_wba_is_refused_without_a_challenge():
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    with pytest.warns(DeprecationWarning):
        config = RequestSignatureVerification(
            signer_keys=StaticSignerKeys({ORIGIN: {"keys": [jwk]}})
        )
    app, seen = _recording_app(config)
    body = _tool("get_products")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app)) as client:
        response = await client.post(TARGET, content=body, headers=_signed(private, body))
    assert response.status_code == 403
    assert "Accept-Signature" not in response.headers
    assert response.json() == GENERIC_AUTHENTICATION_ERROR
    assert not seen


def test_wba_config_requires_an_origin_scoped_key_resolver():
    async def keyid_only(keyid: str) -> ResolvedSignerKey | None:
        return None

    with pytest.raises(TypeError, match="signer_origin"):
        RequestSignatureVerification(signer_keys=keyid_only, enable_web_bot_auth=True)


# ---------------------------------------------------------------------------
# A4/A5: revocation is the authorization layer
# ---------------------------------------------------------------------------


def _signed_revocations(private, origin, *, start, revoked=()):
    from datetime import timedelta

    kid = public_directory_key(private)["kid"]
    payload = {
        "version": 1,
        "issuer": origin,
        "updated": start.isoformat(),
        "next_update": (start + timedelta(seconds=300)).isoformat(),
        "revoked_kids": list(revoked),
        "revoked_jtis": [],
    }
    protected = b64url_encode(
        json.dumps({"alg": "EdDSA", "kid": kid, "typ": "adcp-gov-revocation+jws"}).encode()
    )
    encoded = b64url_encode(json.dumps(payload).encode())
    signature = b64url_encode(private.sign(f"{protected}.{encoded}".encode()))
    return FetchResult(f"{protected}.{encoded}.{signature}", etag=None)


async def test_origin_without_a_revocation_list_is_identity_established_and_unbindable():
    from datetime import datetime, timedelta, timezone

    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    start = datetime.now(timezone.utc)
    now, published = [0.0], [False]

    async def resolve(keyid, *, signer_origin=None):
        return ResolvedSignerKey(signer_origin, jwk)

    async def fetch(uri, **kwargs):
        if not published[0]:
            raise RevocationListFetchError("not published", status_code=404)
        return _signed_revocations(private, ORIGIN, start=start)

    checker = OriginRevocationChecker(
        resolve,
        fetcher=fetch,
        clock=lambda: now[0],
        wall_clock=lambda: start + timedelta(seconds=now[0]),
    )
    assert await checker.status(ORIGIN, jwk["kid"]) == "no_list"

    async def listed(url, *, allow_private=False):
        return TrustResponse(
            json.dumps({"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]}).encode()
        )

    records = TrustRecordEvaluator(fetcher=listed)
    signer = VerifiedSigner(
        jwk["kid"], "ed25519", "sig1", time.time(), agent_url=ORIGIN, profile="web-bot-auth"
    )
    for state in (None, "no_list", "stale", "unavailable"):
        with pytest.raises(TrustRecordError, match="revocation list"):
            await records.bind(
                VerifiedSigner(**{**signer.__dict__, "revocation": state}),
                principal_id="p",
                bindings=OriginBindings(),
            )
    # Once a list was verified, a later 404 is a failure to read it, never a reset.
    published[0], now[0] = True, 61
    assert await checker.status(ORIGIN, jwk["kid"]) == "current"


@pytest.mark.parametrize("revocation", ["no_list", "current", "stale", "unavailable"])
@pytest.mark.parametrize("operation", ["get_media_buys", "create_media_buy"])
async def test_binding_gate_reads_the_revocation_state(revocation, operation):
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)

    class Checker:
        async def status(self, origin, keyid):
            return revocation

    async def listed(url, *, allow_private=False):
        return TrustResponse(
            json.dumps({"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]}).encode()
        )

    bindings = OriginBindings()
    bindings.bind(ORIGIN, "principal-1")
    config = RequestSignatureVerification(
        signer_keys=StaticSignerKeys({ORIGIN: {"keys": [jwk]}}),
        enable_web_bot_auth=True,
        wba_revocation_checker=Checker(),
        origin_bindings=bindings,
        trust_records=TrustRecordEvaluator(fetcher=listed),
        unbound_for=frozenset({"get_media_buys", "create_media_buy"}),
    )
    app, seen = _recording_app(config)
    body = _tool(operation)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app)) as client:
        response = await client.post(TARGET, content=body, headers=_signed(private, body))
    assert response.status_code == 200, response.text
    assert "Accept-Signature" not in response.headers
    outage = revocation == "unavailable" or (
        revocation == "stale" and operation == "create_media_buy"
    )
    if outage:
        error = response.json()["structuredContent"]["adcp_error"]
        assert error["code"] == "SERVICE_UNAVAILABLE"
        assert not seen
        return
    (signer,) = seen
    assert signer.revocation == revocation
    # No revocation list: identity-established, never acting for the principal.
    assert signer.principal_id == (None if revocation == "no_list" else "principal-1")


async def test_revoked_relay_key_is_refused_like_the_originator():
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)

    class Checker:
        async def status(self, origin, keyid):
            return "revoked"

    from adcp.signing.wba import WbaRevokedKeyError, check_wba_revocation

    signer = VerifiedSigner(
        jwk["kid"], "ed25519", "relay", time.time(), agent_url=ORIGIN, profile="web-bot-auth"
    )
    with pytest.raises(WbaRevokedKeyError) as revoked:
        await check_wba_revocation(Checker(), (signer,))
    assert revoked.value.status == 403
    assert not revoked.value.headers


# ---------------------------------------------------------------------------
# A6: trust-record outages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bound,at,allowed", [(30, 1089, True), (30, 1090, False), (0, 1061, False)]
)
async def test_outage_continuation_is_seller_policy(bound, at, allowed):
    now, offline = [1000.0], [False]

    async def fetch(url, *, allow_private=False):
        if offline[0]:
            raise OSError("offline")
        return TrustResponse(
            json.dumps({"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]}).encode()
        )

    records = TrustRecordEvaluator(
        fetcher=fetch, clock=lambda: now[0], outage_continuation_seconds=bound
    )
    assert (await records.check_listing(ORIGIN, role="adcp:buying")).status == "listed"
    offline[0], now[0] = True, at
    listing = await records.check_listing(ORIGIN, role="adcp:buying")
    assert listing.status == "unavailable"
    assert listing.within_grace is allowed
    with pytest.raises(ValueError):
        TrustRecordEvaluator(outage_continuation_seconds=-1)


async def test_operators_retire_agents_with_an_empty_agents_list():
    now, retired = [1000.0], [False]

    async def fetch(url, *, allow_private=False):
        agents = [] if retired[0] else [{"url": ORIGIN, "roles": ["adcp:buying"]}]
        return TrustResponse(json.dumps({"agents": agents}).encode())

    records = TrustRecordEvaluator(fetcher=fetch, clock=lambda: now[0])
    assert (await records.check_listing(ORIGIN, role="adcp:buying")).status == "listed"
    retired[0], now[0] = True, 1061
    listing = await records.check_listing(ORIGIN, role="adcp:buying")
    assert listing.status == "unlisted"
    assert isinstance(listing.error, TrustRecordMatchError)


async def test_operator_that_never_published_is_unlisted_not_an_outage():
    async def fetch(url, *, allow_private=False):
        return TrustResponse(b"", 404)

    listing = await TrustRecordEvaluator(fetcher=fetch).check_listing(ORIGIN, role="adcp:buying")
    assert listing.status == "unlisted"


async def test_grantor_outage_without_a_prior_read_is_service_unavailable():
    async def fetch(url, *, allow_private=False):
        if url == trust_record_url(ORIGIN):
            return TrustResponse(
                json.dumps({"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]}).encode()
            )
        raise OSError("brand record unreachable")

    result = await TrustGrantEvaluator(TrustRecordEvaluator(fetcher=fetch)).check(
        agent_origin=ORIGIN,
        brand_domain="brand.com",
        account_operator="platform.com",
        allow_stale_on_outage=True,
    )
    assert not result.authorized and result.error_code == "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# A9: grants (L2 §Grants in trust.json)
# ---------------------------------------------------------------------------


def _grant_records(documents: dict[str, Any], fetched: list[str] | None = None):
    async def fetch(url, *, allow_private=False):
        if fetched is not None:
            fetched.append(url)
        document = documents.get(url)
        if isinstance(document, Exception):
            raise document
        if document is None:
            return TrustResponse(b"", 404)
        return TrustResponse(json.dumps(document).encode())

    return TrustRecordEvaluator(fetcher=fetch, clock=lambda: 1000)


async def test_only_the_house_record_authorizes():
    fetched: list[str] = []
    documents = {
        trust_record_url(ORIGIN): {"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]},
        # The brand's own record must never be consulted once it names a house.
        trust_record_url("brand.com"): {
            "grants": [{"grantee": "platform.com", "scopes": ["adcp:media_buying"]}]
        },
        trust_record_url("house.com"): {
            "grants": [{"grantee": "platform.com", "scopes": ["adcp:media_buying"]}]
        },
    }

    async def house(brand_domain: str) -> str | None:
        return "house.com" if brand_domain == "brand.com" else None

    records = _grant_records(documents, fetched)
    result = await TrustGrantEvaluator(records, resolve_house=house).check(
        agent_origin=ORIGIN, brand_domain="brand.com", account_operator="platform.com"
    )
    assert result.authorized
    assert trust_record_url("brand.com") not in fetched
    documents[trust_record_url("house.com")] = {"grants": []}
    denied = await TrustGrantEvaluator(_grant_records(documents), resolve_house=house).check(
        agent_origin=ORIGIN, brand_domain="brand.com", account_operator="platform.com"
    )
    assert not denied.authorized and denied.reason == "grant_absent"

    async def broken(brand_domain: str) -> str | None:
        raise OSError("brand.json unreachable")

    outage = await TrustGrantEvaluator(_grant_records(documents), resolve_house=broken).check(
        agent_origin=ORIGIN, brand_domain="brand.com", account_operator="platform.com"
    )
    assert not outage.authorized and outage.error_code == "SERVICE_UNAVAILABLE"


@pytest.mark.parametrize(
    "first,second,authorized",
    [
        ({}, {}, True),
        # The window is the latest valid_from to the earliest valid_until.
        ({"valid_from": "1970-01-01T00:16:00Z"}, {"valid_until": "1970-01-01T00:16:50Z"}, True),
        ({"valid_from": "1970-01-01T00:16:50Z"}, {}, False),
        ({}, {"valid_until": "1970-01-01T00:16:40Z"}, False),
        # A narrowed first link ends the chain unless it lists the signer.
        ({"agents": [{"url": "https://buyer.agency.com"}]}, {}, False),
        ({"agents": [{"url": ORIGIN}]}, {}, True),
        ({}, {"agents": [{"url": "https://other.platform.com"}]}, False),
    ],
)
async def test_two_link_chain_narrowing_and_window_intersection(first, second, authorized):
    documents = {
        trust_record_url(ORIGIN): {"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]},
        trust_record_url("brand.com"): {
            "grants": [{"grantee": "agency.com", "scopes": ["adcp:media_buying"], **first}]
        },
        trust_record_url("agency.com"): {
            "grants": [{"grantee": "platform.com", "scopes": ["adcp:media_buying"], **second}]
        },
    }
    result = await TrustGrantEvaluator(_grant_records(documents)).check(
        agent_origin=ORIGIN, brand_domain="brand.com", account_operator="agency.com"
    )
    assert result.authorized is authorized
    if authorized and "valid_until" in second:
        assert result.expires_at == 1010


async def test_grant_domains_compare_as_registrable_domains():
    documents = {
        trust_record_url(ORIGIN): {"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]},
        trust_record_url("brand.com"): {
            "grants": [{"grantee": "platform.com", "scopes": ["adcp:media_buying"]}]
        },
    }
    result = await TrustGrantEvaluator(_grant_records(documents)).check(
        agent_origin=ORIGIN,
        brand_domain="https://WWW.Brand.com/",
        account_operator="ads.platform.com",
    )
    assert result.authorized


# ---------------------------------------------------------------------------
# B: interop details not covered by the vendored fixtures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nonce_bytes", [32, 63, 65])
async def test_verifier_accepts_exactly_64_byte_nonces(nonce_bytes):
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    body = _tool("get_products")
    headers = _signed(private, body, created=1000, nonce=b64url_encode(b"\x07" * nonce_bytes))
    with pytest.raises(WbaVerificationError, match="64 bytes"):
        await verify_wba_request(
            method="POST",
            url=TARGET,
            headers=headers,
            body=body,
            signer_keys=StaticSignerKeys({ORIGIN: {"keys": [jwk]}}),
            replay_store=InMemoryReplayStore(),
            now=1001,
        )


def test_received_target_uri_keeps_percent_encoding_and_query():
    scope = {
        "scheme": "https",
        "path": "/a~b/mcp/",
        "raw_path": b"/a%7Eb/mcp/",
        "query_string": b"x=%41",
        "headers": [(b"host", b"seller.example.com")],
    }
    assert _received_target_uri(scope) == "https://seller.example.com/a%7Eb/mcp/?x=%41"


async def test_middleware_verifies_a_percent_encoded_target_as_received():
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    config = RequestSignatureVerification(
        signer_keys=StaticSignerKeys({ORIGIN: {"keys": [jwk]}}),
        enable_web_bot_auth=True,
        wba_revocation_checker=_not_revoked,
    )
    app, seen = _recording_app(config)
    url = "https://seller.example.com/a%7Eb/mcp/"
    body = _tool("get_principal")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app)) as client:
        response = await client.post(url, content=body, headers=_signed(private, body, url=url))
    assert response.status_code == 200, response.text
    assert seen[0].agent_url == ORIGIN


def _unsigned_directory(*jwks: dict[str, Any], media_type: str = "application/json"):
    body = json.dumps({"keys": list(jwks)}).encode()
    return DirectoryResponse(body, {"Content-Type": media_type})


def test_plain_jwks_directory_is_accepted_by_thumbprint_unless_signatures_are_required():
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    without_kid = {k: v for k, v in jwk.items() if k != "kid"}
    other_use = {"kty": "oct", "k": "c2VjcmV0"}  # not a key the profile can use
    keys = verify_directory_response(
        ORIGIN, _unsigned_directory(without_kid, {**jwk, "use": "enc"}), now=1000
    )
    assert list(keys) == [jwk["kid"]]
    for media_type in ("application/jwk-set+json", DIRECTORY_MEDIA_TYPE):
        assert verify_directory_response(
            ORIGIN, _unsigned_directory(without_kid, media_type=media_type), now=1000
        )
    with pytest.raises(WbaVerificationError, match="private key material"):
        verify_directory_response(ORIGIN, _unsigned_directory(without_kid, other_use), now=1000)
    with pytest.raises(WbaVerificationError, match="not signed"):
        verify_directory_response(
            ORIGIN, _unsigned_directory(without_kid), now=1000, require_signed=True
        )


def _partly_signed_directory(signed_key, unsigned_key, *, components=None, created=1000):
    jwks = [public_directory_key(signed_key), public_directory_key(unsigned_key)]
    body = json.dumps({"keys": jwks}).encode()
    headers = {
        "Content-Type": DIRECTORY_MEDIA_TYPE,
        "Content-Digest": compute_content_digest_sha256(body),
    }
    authority = Item("@authority")
    authority.params["req"] = True
    member = InnerList(components or [authority, Item("content-digest")])
    member.params.update(
        {
            "created": created,
            "expires": created + 3600,
            "keyid": jwks[0]["kid"],
            "alg": "ed25519",
            "tag": "http-message-signatures-directory",
        }
    )
    base = _base("GET", ORIGIN + DIRECTORY_PATH, headers, member, directory_response=True)
    headers["Signature-Input"] = str(Dictionary({"key1": member}))
    headers["Signature"] = str(Dictionary({"key1": Item(_sign("ed25519", signed_key, base))}))
    return DirectoryResponse(body, headers), jwks


def test_signed_directory_indexes_only_keys_with_a_verified_signature():
    signed, unsigned = (ed25519.Ed25519PrivateKey.generate() for _ in range(2))
    response, jwks = _partly_signed_directory(signed, unsigned)
    keys = verify_directory_response(ORIGIN, response, now=1001)
    assert list(keys) == [jwks[0]["kid"]]


def test_directory_signatures_require_the_exact_component_identifiers():
    signed, unsigned = (ed25519.Ed25519PrivateKey.generate() for _ in range(2))
    keyed_digest = Item("content-digest")
    keyed_digest.params["key"] = "sha-256"
    bare_authority = Item("@authority")
    for components in ([Item("@authority"), Item("content-digest")], [bare_authority]):
        with pytest.raises(WbaVerificationError):
            verify_directory_response(
                ORIGIN,
                _partly_signed_directory(signed, unsigned, components=components)[0],
                now=1001,
            )
    authority = Item("@authority")
    authority.params["req"] = True
    with pytest.raises(WbaVerificationError):
        verify_directory_response(
            ORIGIN,
            _partly_signed_directory(signed, unsigned, components=[authority, keyed_digest])[0],
            now=1001,
        )


def test_directory_digest_covers_the_exact_bytes_including_a_bom():
    from dataclasses import replace

    response = sign_key_directory(
        agent_origin=ORIGIN, private_keys=[ed25519.Ed25519PrivateKey.generate()], created=1000
    )
    with pytest.raises(WbaVerificationError, match="digest"):
        verify_directory_response(
            ORIGIN, replace(response, body=b"\xef\xbb\xbf" + response.body), now=1001
        )


def test_directory_created_is_backdated_and_tolerates_a_verifier_behind():
    before = int(time.time())
    response = sign_key_directory(
        agent_origin=ORIGIN, private_keys=[ed25519.Ed25519PrivateKey.generate()]
    )
    member = _member(response.headers["Signature-Input"], "key1")
    assert member.params["created"] <= before - DIRECTORY_SKEW_ALLOWANCE_SECONDS + 1
    assert member.params["expires"] >= before + 86400
    assert verify_directory_response(ORIGIN, response, now=time.time() - 30)


async def test_a_synchronously_throwing_fetcher_cannot_poison_discovery():
    private = ed25519.Ed25519PrivateKey.generate()
    kid = public_directory_key(private)["kid"]
    now, broken = [1000.0], [True]

    def fetch(url, *, allow_private=False):
        if broken[0]:
            raise RuntimeError("synchronous failure")

        async def served():
            return sign_key_directory(agent_origin=ORIGIN, private_keys=[private], created=1000)

        return served()

    keys = DiscoveredSignerKeys(fetcher=fetch, clock=lambda: now[0])
    with pytest.raises(WbaDiscoveryError):
        await keys(kid, signer_origin=ORIGIN)
    assert not keys._pending
    broken[0], now[0] = False, 1061
    assert await keys(kid, signer_origin=ORIGIN) is not None


async def test_wba_replay_at_exactly_expires_plus_skew_is_rejected():
    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    body = _tool("get_products")
    headers = _signed(private, body, created=1000, expires_in_seconds=300)
    clock = [1000.0]
    store = InMemoryReplayStore(clock=lambda: clock[0])
    options = {
        "method": "POST",
        "url": TARGET,
        "headers": headers,
        "body": body,
        "signer_keys": StaticSignerKeys({ORIGIN: {"keys": [jwk]}}),
        "replay_store": store,
    }
    await verify_wba_request(**options, now=1000)
    clock[0] = 1360.0
    with pytest.raises(WbaVerificationError, match="replayed"):
        await verify_wba_request(**options, now=1360)


def test_rfc9421_replay_at_exactly_expires_plus_skew_is_rejected():
    from adcp.signing import (
        SignatureVerificationError,
        VerifierCapability,
        VerifyOptions,
        generate_signing_keypair,
        load_private_key_pem,
    )

    pem, jwk = generate_signing_keypair(kid="replay-key")
    body = b"{}"
    signed = sign_request(
        method="POST",
        url=TARGET,
        headers={"Content-Type": "application/json"},
        body=body,
        private_key=load_private_key_pem(pem),
        key_id="replay-key",
        alg="ed25519",
        created=1000,
        expires_in_seconds=300,
        signing_profile_version="3.2",
    )
    clock = [1000.0]
    store = InMemoryReplayStore(clock=lambda: clock[0])

    def verify(now: float) -> None:
        verify_request_signature(
            method="POST",
            url=TARGET,
            headers={"Content-Type": "application/json", **signed.as_dict()},
            body=body,
            options=VerifyOptions(
                now=now,
                capability=VerifierCapability(),
                operation="get_products",
                jwks_resolver=lambda keyid: jwk,
                replay_store=store,
                signing_profile_version="3.2",
            ),
        )

    verify(1000)
    clock[0] = 1360.0
    with pytest.raises(SignatureVerificationError, match="replay"):
        verify(1360)


async def test_signer_never_strips_another_partys_signature_fields():
    import httpx as _httpx

    from adcp.signing import SigningConfig
    from adcp.signing.client import install_signing_event_hook, signing_operation
    from adcp.types.experimental_identity import RequestSigning

    private = ed25519.Ed25519PrivateKey.generate()
    existing = {"Signature-Input": 'sig0=("@method");created=1', "Signature": "sig0=:AAAA:"}
    with pytest.raises(ValueError, match="relay signer"):
        sign_wba_request(
            method="POST",
            url=TARGET,
            headers={"Content-Type": "application/json", **existing},
            body=b"{}",
            private_key=private,
            agent_origin=ORIGIN,
        )
    config = SigningConfig(
        private_key=private,
        key_id=public_directory_key(private)["kid"],
        agent_origin=ORIGIN,
    )
    sent: list[_httpx.Request] = []
    client = _httpx.AsyncClient(
        transport=_httpx.MockTransport(lambda request: sent.append(request) or _httpx.Response(200))
    )
    install_signing_event_hook(
        client,
        signing=config,
        seller_capability=RequestSigning(
            supported=True, required_for=["get_products"], profiles=["web-bot-auth"]
        ),
    )
    with signing_operation("get_products"), pytest.raises(ValueError, match="relay signer"):
        await client.post(TARGET, content=b"{}", headers={**existing, "Content-Type": "x/y"})
    assert not sent
    await client.aclose()


# ---------------------------------------------------------------------------
# C: trust host budgets and history quotas
# ---------------------------------------------------------------------------


async def test_authoritative_location_hops_never_spend_the_victims_own_budget():
    entered, release = asyncio.Event(), asyncio.Event()
    hop_calls = []

    async def fetch(url, *, allow_private=False):
        host = url.split("/")[2]
        if host.startswith("attacker-"):
            index = host.split(".")[0]
            return TrustResponse(
                json.dumps({"authoritative_location": f"https://victim.com/{index}.json"}).encode()
            )
        if url != "https://victim.com/.well-known/trust.json":
            hop_calls.append(url)
            if len(hop_calls) == 2:
                entered.set()
            await asyncio.wait_for(release.wait(), timeout=5)
            return TrustResponse(b'{"agents":[]}')
        return TrustResponse(
            json.dumps(
                {"agents": [{"url": "https://buyer.victim.com", "roles": ["adcp:buying"]}]}
            ).encode()
        )

    records = TrustRecordEvaluator(
        fetcher=fetch, max_fetches_per_host=1, max_foreign_fetches_per_host=2
    )
    attackers = [
        asyncio.create_task(records.evaluate(f"https://attacker-{index}.com")) for index in range(2)
    ]
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        # The foreign budget for victim.com is full; another hop is refused...
        with pytest.raises(TrustRecordUnavailableError, match="capacity"):
            await records.evaluate("https://attacker-2.com")
        # ...but the victim's own fetch of its own host still proceeds.
        victim = await asyncio.wait_for(records.evaluate("https://buyer.victim.com"), 5)
        assert victim.operator_domain == "victim.com"
    finally:
        release.set()
        await asyncio.wait_for(asyncio.gather(*attackers, return_exceptions=True), timeout=5)
    assert not records._foreign_inflight and not records._hosts_inflight


async def test_revocation_quota_groups_private_suffix_tenants():
    from datetime import datetime, timezone

    private = ed25519.Ed25519PrivateKey.generate()
    jwk = public_directory_key(private)
    start = datetime.now(timezone.utc)

    async def resolve(keyid, *, signer_origin=None):
        return ResolvedSignerKey(signer_origin, jwk)

    async def fetch(uri, **kwargs):
        return _signed_revocations(private, uri.partition("/.well-known")[0], start=start)

    checker = OriginRevocationChecker(
        resolve, fetcher=fetch, max_origins=8, max_origins_per_operator=2
    )
    for tenant in ("a", "b"):
        assert await checker.status(f"https://{tenant}.vercel.app", jwk["kid"]) == "current"
    # A third free tenant of the same hosting provider shares the quota.
    assert await checker.status("https://c.vercel.app", jwk["kid"]) == "stale"
    assert await checker.status("https://buyer.other.com", jwk["kid"]) == "current"


# ---------------------------------------------------------------------------
# C: grant gate
# ---------------------------------------------------------------------------

BUYER = BuyerAgent(agent_url=ORIGIN, display_name="Buyer", status="active")


def _gate(extract: Any) -> TrustGrantGate:
    documents = {
        trust_record_url(ORIGIN): {"agents": [{"url": ORIGIN, "roles": ["adcp:buying"]}]},
        trust_record_url("brand.com"): {
            "grants": [{"grantee": "platform.com", "scopes": ["adcp:media_buying"]}]
        },
    }
    return TrustGrantGate(TrustGrantEvaluator(_grant_records(documents)), extract)


def test_list_products_uses_the_media_buying_scope():
    assert "list_products" in _MEDIA_BUY_DEFAULT_OPERATIONS


@pytest.mark.parametrize("failure", ["raises", "empty_brand", "empty_operator", "not_a_claim"])
async def test_account_without_a_resolvable_claim_fails_closed(failure):
    def extract(account: Account[Any], agent: BuyerAgent) -> Any:
        if failure == "raises":
            return account.metadata["brand_domain"]  # KeyError: missing seller state
        if failure == "not_a_claim":
            return {"brand_domain": "brand.com"}
        return TrustGrantClaim(
            "" if failure == "empty_brand" else "brand.com",
            "" if failure == "empty_operator" else "platform.com",
        )

    with pytest.raises(AdcpError) as denied:
        await _gate(extract).require_account(Account(id="a"), BUYER, operation="get_products")
    assert denied.value.code == "PERMISSION_DENIED"
    await _gate(
        lambda account, agent: TrustGrantClaim("brand.com", "platform.com")
    ).require_account(Account(id="a"), BUYER, operation="list_products")


async def test_sync_accounts_checks_the_existing_account_behind_an_account_id():
    from concurrent.futures import ThreadPoolExecutor

    from adcp.decisioning import (
        AuthInfo,
        DecisioningCapabilities,
        DecisioningPlatform,
        HttpSigCredential,
        InMemoryTaskRegistry,
        SingletonAccounts,
        signing_only_registry,
    )
    from adcp.decisioning.handler import PlatformHandler
    from adcp.types import SyncAccountsRequest

    upserted: list[Any] = []
    resolved: list[Any] = []

    class Accounts(SingletonAccounts):
        def resolve(self, ref: Any = None, auth_info: Any = None) -> Any:
            resolved.append(ref)
            if ref and ref.get("account_id") == "victim":
                return Account(
                    id="victim",
                    metadata={"claim": TrustGrantClaim("victim-brand.com", "victim.com")},
                )
            return None

        def upsert_request(self, request: Any, ctx: Any = None) -> Any:
            upserted.append(request)
            return {"accounts": []}

    class Platform(DecisioningPlatform):
        capabilities = DecisioningCapabilities()
        accounts = Accounts(account_id="victim")

    async def lookup(origin: str) -> BuyerAgent:
        return BUYER

    context = ToolContext(
        metadata={
            "adcp.auth_info": AuthInfo(
                kind="http_sig",
                credential=HttpSigCredential(
                    kind="http_sig", keyid="kid", agent_url=ORIGIN, verified_at=1000
                ),
                extra={
                    "signing_profile": "web-bot-auth",
                    "principal_id": "p",
                    "wba_revocation": "current",
                },
            )
        }
    )
    gate = _gate(lambda account, agent: account.metadata["claim"])
    with ThreadPoolExecutor(max_workers=1) as executor:
        handler = PlatformHandler(
            Platform(),
            executor=executor,
            registry=InMemoryTaskRegistry(),
            buyer_agent_registry=signing_only_registry(lookup),
            trust_grant_gate=gate,
        )
        # A natural key the signer is granted cannot carry an update to an
        # existing account it is not granted.
        request = SyncAccountsRequest.model_validate(
            {
                "accounts": [
                    {
                        "brand": {"domain": "brand.com"},
                        "operator": "platform.com",
                        "billing": "operator",
                    }
                ],
                "idempotency_key": "k" * 16,
            }
        )
        rows = [
            {
                "account_id": "victim",
                "brand": {"domain": "brand.com"},
                "operator": "platform.com",
            }
        ]
        object.__setattr__(request, "accounts", rows)
        with pytest.raises(AdcpError) as denied:
            await handler.sync_accounts(request, context)
        assert denied.value.code == "PERMISSION_DENIED"
        assert not upserted
        # An account_id that does not resolve is denied before any upsert.
        object.__setattr__(request, "accounts", [{"account_id": "missing"}])
        with pytest.raises(AdcpError):
            await handler.sync_accounts(request, context)
        assert not upserted


# ---------------------------------------------------------------------------
# C: stateful MCP sessions read the verified signer per request
# ---------------------------------------------------------------------------


async def test_stateful_mcp_session_reads_each_requests_own_wba_signer():
    from adcp.server.serve import _build_mcp_and_a2a_app

    origins = ("https://buyer-one.platform.com", "https://buyer-two.platform.com")
    privates = {origin: ed25519.Ed25519PrivateKey.generate() for origin in origins}
    bindings = OriginBindings()
    for index, origin in enumerate(origins):
        bindings.bind(origin, f"principal-{index}")

    async def listed(url, *, allow_private=False):
        return TrustResponse(
            json.dumps(
                {"agents": [{"url": origin, "roles": ["adcp:buying"]} for origin in origins]}
            ).encode()
        )

    seen: list[tuple[str | None, str | None]] = []

    class Handler(ADCPHandler[Any]):
        async def get_media_buys(self, params: Any, context: Any = None) -> dict[str, Any]:
            auth = context.metadata["adcp.auth_info"]
            seen.append((context.caller_identity, auth.extra["principal_id"]))
            return {"media_buys": []}

    app = _build_mcp_and_a2a_app(
        Handler(),
        name="stateful-wba",
        port=0,
        host="127.0.0.1",
        instructions=None,
        test_controller=None,
        validation=None,
        advertise_all=True,
        stateless_http=False,
        allowed_hosts=["localhost"],
        request_signature_verification=RequestSignatureVerification(
            signer_keys=StaticSignerKeys(
                {origin: {"keys": [public_directory_key(key)]} for origin, key in privates.items()}
            ),
            enable_web_bot_auth=True,
            wba_revocation_checker=_not_revoked,
            origin_bindings=bindings,
            trust_records=TrustRecordEvaluator(fetcher=listed),
        ),
    )
    mcp_headers = {"accept": "application/json, text/event-stream"}

    def signed(origin: str, payload: dict[str, Any], extra: dict[str, str]):
        body = json.dumps(payload).encode()
        headers = {**mcp_headers, **extra, "content-type": "application/json"}
        headers.update(
            sign_wba_request(
                method="POST",
                url="http://localhost/mcp",
                headers=headers,
                body=body,
                private_key=privates[origin],
                agent_origin=origin,
            )
        )
        return body, headers

    initialize = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "t", "version": "1"},
        },
    }
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as client:
            body, headers = signed(origins[0], initialize, {})
            init = await client.post("/mcp", content=body, headers=headers)
            assert init.status_code == 200, init.text
            session = {"mcp-session-id": init.headers["mcp-session-id"]}
            for index, origin in enumerate((origins[1], origins[0], origins[1])):
                call = {
                    "jsonrpc": "2.0",
                    "id": index + 1,
                    "method": "tools/call",
                    "params": {"name": "get_media_buys", "arguments": {}},
                }
                body, headers = signed(origin, call, session)
                response = await client.post("/mcp", content=body, headers=headers)
                assert response.status_code == 200, response.text
    assert seen == [
        (origins[1], "principal-1"),
        (origins[0], "principal-0"),
        (origins[1], "principal-1"),
    ]
