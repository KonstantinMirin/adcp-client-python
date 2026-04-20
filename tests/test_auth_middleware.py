"""Tests for BearerTokenAuthMiddleware + auth_context_factory.

The middleware is load-bearing: a subtle bug here is a cross-tenant
confidentiality leak in production. Tests focus on the exact
invariants that matter for correctness — token compare, discovery
bypass, ContextVar reset, principal/tenant population.

Composition with ``create_mcp_server(context_factory=auth_context_factory)``
lives in ``test_mcp_middleware_composition.py`` — these tests
exercise the middleware class in isolation.
"""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
import pytest
from asgi_lifespan import LifespanManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from adcp.server import (
    BearerTokenAuthMiddleware,
    Principal,
    auth_context_factory,
    constant_time_token_match,
)
from adcp.server.auth import (
    current_principal,
    current_principal_metadata,
    current_tenant,
)

# ---------------------------------------------------------------------------
# Principal + validator plumbing
# ---------------------------------------------------------------------------


def test_principal_is_immutable() -> None:
    """Principal is frozen so a middleware can't mutate it after the
    validator returns — any re-scope must build a fresh Principal."""
    p = Principal(caller_identity="alice", tenant_id="t1")
    with pytest.raises(AttributeError):
        p.caller_identity = "bob"  # type: ignore[misc]


def test_constant_time_token_match_returns_value() -> None:
    stored = {hashlib.sha256(b"good").hexdigest(): "payload"}
    assert constant_time_token_match("good", stored) == "payload"


def test_constant_time_token_match_returns_none_on_miss() -> None:
    stored = {hashlib.sha256(b"good").hexdigest(): "payload"}
    assert constant_time_token_match("wrong", stored) is None


def test_constant_time_token_match_empty_token() -> None:
    stored = {hashlib.sha256(b"good").hexdigest(): "payload"}
    assert constant_time_token_match("", stored) is None


# ---------------------------------------------------------------------------
# Middleware-in-isolation tests via a minimal Starlette harness
# ---------------------------------------------------------------------------


async def _echo_handler(request: Request) -> JSONResponse:
    """Starlette handler that echoes back the per-request ContextVars.

    The middleware populates these for each successfully-authenticated
    request; failures short-circuit before the handler runs.
    """
    return JSONResponse(
        {
            "principal": current_principal.get(),
            "tenant": current_tenant.get(),
            "metadata": current_principal_metadata.get(),
        }
    )


def _build_app(validator: Any, routes: list[Route] | None = None) -> Starlette:
    app = Starlette(routes=routes or [Route("/", _echo_handler, methods=["POST"])])
    app.add_middleware(BearerTokenAuthMiddleware, validate_token=validator)
    return app


@pytest.mark.asyncio
async def test_rejects_missing_bearer() -> None:
    def validator(token: str) -> Principal | None:
        return Principal(caller_identity="alice")

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/", json={"method": "tools/call"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rejects_invalid_bearer() -> None:
    def validator(token: str) -> Principal | None:
        return None  # always reject

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Bearer bad-token"},
            )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_populates_contextvars_on_valid_token() -> None:
    expected = Principal(
        caller_identity="alice",
        tenant_id="t1",
        metadata={"role": "admin"},
    )

    def validator(token: str) -> Principal | None:
        return expected if token == "good" else None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Bearer good"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["principal"] == "alice"
    assert body["tenant"] == "t1"
    assert body["metadata"] == {"role": "admin"}


@pytest.mark.asyncio
async def test_async_validator_is_awaited() -> None:
    """Validators can be `async def` — the middleware awaits them."""

    async def validator(token: str) -> Principal | None:
        return Principal(caller_identity="async-alice") if token == "good" else None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Bearer good"},
            )
    assert resp.status_code == 200
    assert resp.json()["principal"] == "async-alice"


@pytest.mark.asyncio
async def test_discovery_methods_bypass_auth() -> None:
    """``initialize`` / ``notifications/initialized`` / ``tools/list``
    MUST go through without credentials — the MCP handshake has no
    token yet."""
    validator_calls: list[str] = []

    def validator(token: str) -> Principal | None:
        validator_calls.append(token)
        return None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            for method in ("initialize", "notifications/initialized", "tools/list"):
                resp = await client.post("/", json={"method": method})
                assert resp.status_code == 200, f"{method} should bypass auth"

    # Validator MUST NOT have been called for any discovery method — bypass
    # is composition-by-identity, not "call validator and ignore result".
    assert validator_calls == []


@pytest.mark.asyncio
async def test_discovery_tools_bypass_auth() -> None:
    """``tools/call`` on a DISCOVERY_TOOLS entry (``get_adcp_capabilities``)
    bypasses auth per AdCP spec — the capability handshake."""

    def validator(token: str) -> Principal | None:
        return None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={
                    "method": "tools/call",
                    "params": {"name": "get_adcp_capabilities"},
                },
            )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_contextvars_reset_after_request() -> None:
    """The critical security invariant: after the response, the
    ContextVars MUST be back to None — otherwise a later task sharing
    the context reads a stale principal."""

    def validator(token: str) -> Principal | None:
        return Principal(caller_identity="alice", tenant_id="t1")

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Bearer good"},
            )
    assert resp.status_code == 200

    # The test's own context reads None — the middleware reset-in-finally
    # fired before the test resumed. If this regresses, `.get()` would
    # return "alice" from a leaked ContextVar.
    assert current_principal.get() is None
    assert current_tenant.get() is None
    assert current_principal_metadata.get() is None


@pytest.mark.asyncio
async def test_batch_jsonrpc_fails_closed() -> None:
    """JSON-RPC 2.0 allows batch arrays, but the discovery bypass must
    NOT apply to batches — a client could smuggle a mutation past the
    gate inside a batch. Batch → auth required → 401 without a bearer."""

    def validator(token: str) -> Principal | None:
        return None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json=[{"method": "tools/list"}, {"method": "tools/call"}],
            )
    # Without a bearer header, the batch cannot satisfy the auth gate.
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "header",
    [
        "Bearer good",  # canonical
        "bearer good",  # RFC 7235: scheme is case-insensitive
        "BEARER good",
        "Bearer  good",  # folded double-space
        "Bearer\tgood",  # tab-separator accepted
        "Bearer good\n",  # trailing whitespace tolerated
    ],
)
async def test_accepts_rfc7235_scheme_variants(header: str) -> None:
    """RFC 7235 says the ``Bearer`` scheme is case-insensitive and
    whitespace-folded. Clients that send lowercase or tab-separated
    headers must not get a 401 — that's an interop bug that looks like
    an auth bug."""

    def validator(token: str) -> Principal | None:
        return Principal(caller_identity="alice") if token == "good" else None

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": header},
            )
    assert resp.status_code == 200, f"header {header!r} was rejected"


@pytest.mark.asyncio
async def test_non_bearer_scheme_is_rejected() -> None:
    """Basic / Digest / other schemes MUST return 401 — the middleware
    is bearer-only by design."""

    def validator(token: str) -> Principal | None:
        return Principal(caller_identity="alice")

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Placeholder non-bearer header — specific value is irrelevant,
            # we only check the scheme gate rejects anything that isn't
            # "Bearer". Kept as obvious placeholder text so secret scanners
            # don't flag a real-looking base64 payload.
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Basic <placeholder>"},
            )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_validator_exception_returns_401_not_500() -> None:
    """A buggy validator (DB outage, bug) must fail closed with 401 —
    a 500 leaks stack traces to the caller and signals the presence of
    an auth path on the deployment. The docstring contract is "do not
    raise"; we enforce fail-closed regardless."""

    def validator(token: str) -> Principal | None:
        raise RuntimeError("db down — leak-prone details here")

    app = _build_app(validator)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                json={"method": "tools/call", "params": {"name": "get_products"}},
                headers={"Authorization": "Bearer token"},
            )
    assert resp.status_code == 401
    # Body must NOT carry the exception text — exceptions go to logs, not clients.
    assert "db down" not in resp.text


@pytest.mark.asyncio
async def test_principal_metadata_cannot_shadow_sdk_keys() -> None:
    """A validator returning ``Principal(metadata={"tool_name": "x"})``
    must NOT shadow the SDK-populated ``tool_name`` in
    ``ToolContext.metadata``. SDK keys always win — otherwise an
    attacker-controlled validator could inject arbitrary audit fields."""
    from adcp.server import RequestMetadata

    principal_token = current_principal.set("alice")
    metadata_token = current_principal_metadata.set(
        {"tool_name": "attacker-injected", "transport": "attacker"}
    )
    try:
        meta = RequestMetadata(tool_name="get_products", transport="mcp")
        ctx = auth_context_factory(meta)
    finally:
        current_principal.reset(principal_token)
        current_principal_metadata.reset(metadata_token)

    # SDK keys win over principal-supplied keys.
    assert ctx.metadata["tool_name"] == "get_products"
    assert ctx.metadata["transport"] == "mcp"


@pytest.mark.asyncio
async def test_body_peek_does_not_starve_downstream_handler() -> None:
    """The middleware peeks the JSON-RPC body to identify the method.
    Downstream handlers must still read the same bytes — otherwise
    MCP's streamable-HTTP transport (nested ASGI app that reads from
    ``receive`` directly) hangs or sees empty payloads.

    This test runs the full request path: middleware peeks, downstream
    reads ``request.body()``, asserts identical bytes."""
    from starlette.requests import Request as _Request
    from starlette.responses import JSONResponse as _JSONResponse

    async def _echo_body(request: _Request) -> _JSONResponse:
        body = await request.body()
        return _JSONResponse({"body_len": len(body), "body_text": body.decode()})

    def validator(token: str) -> Principal | None:
        return Principal(caller_identity="alice")

    app = Starlette(routes=[Route("/", _echo_body, methods=["POST"])])
    app.add_middleware(BearerTokenAuthMiddleware, validate_token=validator)

    payload = {
        "method": "tools/call",
        "params": {"name": "get_products", "arguments": {"brief": "x"}},
    }
    import json as _json

    expected = _json.dumps(payload)

    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/",
                content=expected,
                headers={
                    "Authorization": "Bearer good",
                    "Content-Type": "application/json",
                },
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["body_len"] == len(expected)
    assert body["body_text"] == expected


@pytest.mark.asyncio
async def test_subclass_can_tighten_discovery_bypass() -> None:
    """Operators tightening ``tools/list`` behind auth override
    ``is_discovery_request``. Confirm the hook fires."""

    class StricterMiddleware(BearerTokenAuthMiddleware):
        def is_discovery_request(self, method: str | None, tool: str | None) -> bool:
            # Only MCP initialize is bypassed; tools/list requires auth.
            return method == "initialize"

    def validator(token: str) -> Principal | None:
        return None

    app = Starlette(routes=[Route("/", _echo_handler, methods=["POST"])])
    app.add_middleware(StricterMiddleware, validate_token=validator)

    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp_init = await client.post("/", json={"method": "initialize"})
            resp_list = await client.post("/", json={"method": "tools/list"})
    assert resp_init.status_code == 200
    assert resp_list.status_code == 401


# ---------------------------------------------------------------------------
# Composition: auth_context_factory reads the middleware's ContextVars
# ---------------------------------------------------------------------------


def test_auth_context_factory_reads_contextvars() -> None:
    """The factory builds a ToolContext from current_principal /
    current_tenant / current_principal_metadata. No middleware runs
    here — set the vars directly and call the factory."""
    from adcp.server import RequestMetadata

    principal_token = current_principal.set("alice")
    tenant_token = current_tenant.set("t1")
    metadata_token = current_principal_metadata.set({"role": "admin"})
    try:
        meta = RequestMetadata(tool_name="get_products", transport="mcp")
        ctx = auth_context_factory(meta)
    finally:
        current_principal.reset(principal_token)
        current_tenant.reset(tenant_token)
        current_principal_metadata.reset(metadata_token)

    assert ctx.caller_identity == "alice"
    assert ctx.tenant_id == "t1"
    assert ctx.metadata["role"] == "admin"
    assert ctx.metadata["tool_name"] == "get_products"
    assert ctx.metadata["transport"] == "mcp"


def test_auth_context_factory_with_no_principal() -> None:
    """Discovery requests populate the ContextVars to None; the factory
    returns a ToolContext with caller_identity=None (handshake is
    pre-auth by design)."""
    from adcp.server import RequestMetadata

    meta = RequestMetadata(tool_name="get_adcp_capabilities", transport="mcp")
    ctx = auth_context_factory(meta)

    assert ctx.caller_identity is None
    assert ctx.tenant_id is None


# Full-stack composition (middleware + create_mcp_server + handler) is
# covered by ``test_mcp_middleware_composition.py`` — that harness
# already boots the FastMCP initialize/tools-call flow end-to-end. The
# tests in this file stay focused on the middleware class itself so
# failures localise to the auth logic, not the transport plumbing.
