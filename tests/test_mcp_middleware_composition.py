"""Integration test: custom HTTP middleware composes with SDK-registered tools.

Downstream agents (salesagent, creative agents) need to wire their own
auth middleware around tools registered by ``create_mcp_server()``. This
test proves the composition path works end-to-end:

1. ``mcp.streamable_http_app()`` returns a Starlette app that accepts
   ``.add_middleware()``.
2. The middleware fires before tool dispatch and can reject requests
   (401 Unauthorized) or let them through.
3. When the middleware lets the request through, a ``context_factory``
   passed to ``create_mcp_server()`` builds a :class:`ToolContext` the
   handler receives — populated from the middleware's side-channel
   (``contextvars.ContextVar``).
4. Tools in :data:`adcp.server.DISCOVERY_TOOLS` are callable without
   auth (the spec-mandated handshake path).

If any of this regresses, salesagent and every other downstream has to
keep their wrapper layer (``mcp_context_wrapper.py``, custom
``@mcp.tool()`` scaffolding) forever. Failing here is the signal to fix
the integration, not the test.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

import httpx
import pytest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from adcp.server import DISCOVERY_TOOLS, ADCPHandler, ToolContext, create_mcp_server

_current_principal: ContextVar[str | None] = ContextVar("test_current_principal", default=None)
_current_tenant: ContextVar[str | None] = ContextVar("test_current_tenant", default=None)


class _RecordingHandler(ADCPHandler):
    """Handler that records the ToolContext each call received."""

    def __init__(self) -> None:
        self.calls: list[ToolContext | None] = []

    async def get_adcp_capabilities(
        self, params: Any, context: ToolContext | None = None
    ) -> dict[str, Any]:
        self.calls.append(context)
        return {"adcp": {"major_versions": [3]}}

    async def get_products(self, params: Any, context: ToolContext | None = None) -> dict[str, Any]:
        self.calls.append(context)
        return {"products": []}


class _AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Authorization headers.

    Rejects any tool call except :data:`DISCOVERY_TOOLS` without a valid
    token. On a valid token, stashes principal + tenant in ContextVars
    so the handler-side ``context_factory`` can read them.
    """

    VALID_TOKENS: dict[str, tuple[str, str]] = {
        "token-acme": ("principal-acme-1", "tenant-acme"),
        "token-beta": ("principal-beta-9", "tenant-beta"),
    }

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        tool_name = await _peek_tool_name(request)

        if tool_name not in DISCOVERY_TOOLS:
            auth = request.headers.get("authorization", "")
            token = auth.removeprefix("Bearer ").strip()
            if token not in self.VALID_TOKENS:
                return JSONResponse({"error": "unauthenticated"}, status_code=401)
            principal, tenant = self.VALID_TOKENS[token]
            _principal_token = _current_principal.set(principal)
            _tenant_token = _current_tenant.set(tenant)
        else:
            _principal_token = _current_principal.set(None)
            _tenant_token = _current_tenant.set(None)

        try:
            return await call_next(request)
        finally:
            _current_principal.reset(_principal_token)
            _current_tenant.reset(_tenant_token)


async def _peek_tool_name(request: Request) -> str | None:
    """Extract the MCP tool name from the incoming JSON-RPC body without
    consuming the request body for downstream handlers."""
    # Starlette caches ``request._body`` on first read, so subsequent
    # reads inside the app still see the bytes.
    body = await request.body()
    if not body:
        return None
    try:
        import json

        payload = json.loads(body)
    except ValueError:
        return None
    if payload.get("method") != "tools/call":
        return None
    params = payload.get("params") or {}
    name = params.get("name")
    return name if isinstance(name, str) else None


def _build_context() -> ToolContext:
    return ToolContext(
        caller_identity=_current_principal.get(),
        tenant_id=_current_tenant.get(),
    )


@pytest.fixture
async def handler_and_client() -> Any:
    handler = _RecordingHandler()
    mcp = create_mcp_server(
        handler,
        name="test-agent",
        context_factory=_build_context,
    )
    # Force stateless JSON responses. Production deployments mount the
    # MCP app behind a reverse proxy; this test covers that shape.
    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    # Allow in-process test host — MCP's DNS-rebinding protection
    # rejects unknown Host headers by default when enabled.
    mcp.settings.transport_security.allowed_hosts = ["localhost", "127.0.0.1"]
    app = mcp.streamable_http_app()
    app.add_middleware(_AuthMiddleware)

    # FastMCP's streamable HTTP session manager initializes a TaskGroup
    # via the Starlette app lifespan. httpx.ASGITransport does not run
    # lifespan by default; this manages it manually so the session
    # manager has a live TaskGroup during requests.
    async with _StarletteLifespan(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://localhost",
            follow_redirects=True,
        ) as client:
            yield handler, client


class _StarletteLifespan:
    """Async context manager that runs a Starlette app's lifespan."""

    def __init__(self, app: Any) -> None:
        self._app = app
        self._scope = {"type": "lifespan"}
        self._startup_complete: Any = None
        self._shutdown_event: Any = None
        self._task: Any = None

    async def __aenter__(self) -> None:
        import asyncio

        self._startup_complete = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        startup_done = asyncio.Event()
        shutdown_done = asyncio.Event()

        send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def receive() -> dict[str, Any]:
            if not self._startup_complete.is_set():
                self._startup_complete.set()
                return {"type": "lifespan.startup"}
            await self._shutdown_event.wait()
            return {"type": "lifespan.shutdown"}

        async def send(message: dict[str, Any]) -> None:
            await send_queue.put(message)
            if message["type"] == "lifespan.startup.complete":
                startup_done.set()
            elif message["type"] == "lifespan.shutdown.complete":
                shutdown_done.set()

        self._task = asyncio.create_task(self._app(self._scope, receive, send))
        self._startup_done = startup_done
        self._shutdown_done = shutdown_done
        await startup_done.wait()

    async def __aexit__(self, *exc: Any) -> None:
        self._shutdown_event.set()
        await self._shutdown_done.wait()
        await self._task


@pytest.mark.asyncio
async def test_discovery_tool_is_callable_without_auth(handler_and_client: Any) -> None:
    handler, client = handler_and_client

    await _initialize_session(client)
    response = await _call_tool(client, "get_adcp_capabilities", {})

    assert response.status_code == 200, response.text
    payload = _parse_event_stream(response.text)
    assert "result" in payload, payload
    assert handler.calls, "handler was not invoked"
    call_context = handler.calls[-1]
    # Discovery calls have no authenticated principal — that's the whole point.
    assert call_context is not None
    assert call_context.caller_identity is None
    assert call_context.tenant_id is None


@pytest.mark.asyncio
async def test_authenticated_tool_call_populates_caller_identity(
    handler_and_client: Any,
) -> None:
    handler, client = handler_and_client

    await _initialize_session(client, headers={"Authorization": "Bearer token-acme"})
    response = await _call_tool(
        client,
        "get_products",
        {"brief": "coffee"},
        headers={"Authorization": "Bearer token-acme"},
    )

    assert response.status_code == 200, response.text
    call_context = handler.calls[-1]
    assert call_context is not None
    assert call_context.caller_identity == "principal-acme-1"
    assert call_context.tenant_id == "tenant-acme"


@pytest.mark.asyncio
async def test_missing_token_blocks_non_discovery_tool(handler_and_client: Any) -> None:
    handler, client = handler_and_client

    response = await _call_tool(client, "get_products", {"brief": "coffee"})

    assert response.status_code == 401
    assert not handler.calls, (
        "handler was invoked despite missing auth — middleware did NOT "
        "compose with the tool dispatch"
    )


def test_discovery_tools_frozenset_contract() -> None:
    # Protects against accidental widening/narrowing of the spec-mandated
    # auth-optional set. Callers extend via ``DISCOVERY_TOOLS | {...}``.
    assert DISCOVERY_TOOLS == frozenset({"get_adcp_capabilities"})


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


async def _initialize_session(
    client: httpx.AsyncClient, *, headers: dict[str, str] | None = None
) -> httpx.Response:
    """Send an MCP ``initialize`` JSON-RPC call — FastMCP requires this
    before ``tools/call`` even in stateless mode."""
    request_headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
    }
    if headers:
        request_headers.update(headers)
    body = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    return await client.post("/mcp/", json=body, headers=request_headers)


async def _call_tool(
    client: httpx.AsyncClient,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """POST a JSON-RPC ``tools/call`` to the MCP endpoint."""
    request_headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
    }
    if headers:
        request_headers.update(headers)
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    return await client.post("/mcp/", json=body, headers=request_headers)


def _parse_event_stream(body: str) -> dict[str, Any]:
    """Parse SSE event-stream body from FastMCP into a dict."""
    import json

    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            return json.loads(line.removeprefix("data: "))
    return json.loads(body) if body.strip() else {}
