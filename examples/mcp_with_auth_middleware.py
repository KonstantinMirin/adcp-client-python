"""Example: custom HTTP auth middleware + typed ToolContext via context_factory.

This is the recipe for multi-tenant sales agents that need to:

1. Validate bearer tokens (or any other credential) in front of
   :func:`adcp.server.create_mcp_server`-registered tools.
2. Allow the AdCP discovery handshake (``get_adcp_capabilities``) to go
   through unauthenticated — per :data:`adcp.server.DISCOVERY_TOOLS`.
3. Pass the authenticated principal + tenant to handlers as a typed
   :class:`adcp.server.ToolContext`.

Run::

    uv run python examples/mcp_with_auth_middleware.py
    # → server on http://localhost:3001/mcp/
    # curl -H 'Authorization: Bearer token-acme' ...

Production note: ``mcp.run()`` is used here for brevity. Real deployments
should mount the Starlette app behind uvicorn + a reverse proxy that
terminates TLS and handles rate limiting.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from adcp.server import (
    DISCOVERY_TOOLS,
    ADCPHandler,
    ToolContext,
    create_mcp_server,
)
from adcp.server.responses import capabilities_response, products_response

# ----------------------------------------------------------------------
# Per-request auth state — populated by middleware, read by context_factory.
# ContextVars are the recommended carrier: they compose cleanly with
# async tasks and don't leak across requests the way module globals do.
# ----------------------------------------------------------------------

_principal: ContextVar[str | None] = ContextVar("adcp_principal", default=None)
_tenant: ContextVar[str | None] = ContextVar("adcp_tenant", default=None)


# Toy token→principal database. Real agents look this up in Postgres /
# Vault / identity provider / etc.
_TOKENS: dict[str, tuple[str, str]] = {
    "token-acme": ("principal-acme-ops", "tenant-acme"),
    "token-globex": ("principal-globex-ops", "tenant-globex"),
}


# ----------------------------------------------------------------------
# HTTP middleware — auth gate, honors DISCOVERY_TOOLS.
# ----------------------------------------------------------------------


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        tool = await _peek_tool_name(request)

        # AdCP spec: ``get_adcp_capabilities`` is the discovery handshake —
        # clients MUST be able to call it without authenticating.
        if tool in DISCOVERY_TOOLS:
            _principal.set(None)
            _tenant.set(None)
            return await call_next(request)

        # Everything else requires a bearer token.
        auth_header = request.headers.get("authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()
        if token not in _TOKENS:
            return JSONResponse({"error": "unauthenticated"}, status_code=401)

        principal_id, tenant_id = _TOKENS[token]
        _principal.set(principal_id)
        _tenant.set(tenant_id)
        return await call_next(request)


async def _peek_tool_name(request: Request) -> str | None:
    """Inspect the JSON-RPC body without consuming it for downstream handlers."""
    body = await request.body()
    if not body:
        return None
    import json

    try:
        payload = json.loads(body)
    except ValueError:
        return None
    if payload.get("method") != "tools/call":
        return None
    params = payload.get("params") or {}
    name = params.get("name")
    return name if isinstance(name, str) else None


# ----------------------------------------------------------------------
# context_factory — runs per tool call, reads the ContextVars the
# middleware populated, returns a typed ToolContext.
# ----------------------------------------------------------------------


def build_context() -> ToolContext:
    return ToolContext(
        caller_identity=_principal.get(),
        tenant_id=_tenant.get(),
    )


# ----------------------------------------------------------------------
# Handler — reads caller_identity + tenant_id off the ToolContext.
# ----------------------------------------------------------------------


class MultiTenantSalesAgent(ADCPHandler):
    _agent_type = "demo multi-tenant sales agent"

    async def get_adcp_capabilities(
        self, params: Any, context: ToolContext | None = None
    ) -> dict[str, Any]:
        return capabilities_response(["media_buy"])

    async def get_products(self, params: Any, context: ToolContext | None = None) -> dict[str, Any]:
        # context.caller_identity is the authenticated principal;
        # context.tenant_id is populated for multi-tenant agents.
        tenant = context.tenant_id if context is not None else None
        catalog = _products_for_tenant(tenant)
        return products_response(catalog)


def _products_for_tenant(tenant_id: str | None) -> list[dict[str, Any]]:
    if tenant_id == "tenant-acme":
        return [{"product_id": "acme_display_1", "name": "Acme homepage display"}]
    if tenant_id == "tenant-globex":
        return [{"product_id": "globex_video_1", "name": "Globex CTV video"}]
    return []


# ----------------------------------------------------------------------
# Wiring — create_mcp_server with context_factory, then add middleware
# to the Starlette app.
# ----------------------------------------------------------------------


def main() -> None:
    mcp = create_mcp_server(
        MultiTenantSalesAgent(),
        name="multi-tenant-sales-agent",
        context_factory=build_context,
    )

    # Middleware must be added BEFORE the app runs. create_mcp_server
    # returns a FastMCP instance; its ASGI app is accessed via
    # streamable_http_app(), which is a standard Starlette app.
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    # mcp.run() hands control to FastMCP. In production, mount with
    # uvicorn and a reverse proxy for TLS + rate limiting.
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
