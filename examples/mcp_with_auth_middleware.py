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

import hashlib
import hmac
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from adcp.server import (
    DISCOVERY_TOOLS,
    ADCPHandler,
    RequestMetadata,
    ToolContext,
    create_mcp_server,
)
from adcp.server.responses import capabilities_response, products_response

# ----------------------------------------------------------------------
# Per-request auth state — populated by middleware, read by context_factory.
# ContextVars are the recommended carrier: they compose cleanly with
# async tasks and don't leak across requests the way module globals do.
# IMPORTANT: always pair ``.set(x)`` with ``.reset(token)`` in a ``finally:``
# block so the value doesn't linger in the current context past the
# response — otherwise a subsequent task reusing the same context reads a
# stale principal (cross-request confidentiality leak).
# ----------------------------------------------------------------------

_principal: ContextVar[str | None] = ContextVar("adcp_principal", default=None)
_tenant: ContextVar[str | None] = ContextVar("adcp_tenant", default=None)


# Real agents look tokens up in Postgres / Vault / an identity provider /
# etc. This dict is a stand-in: it stores a per-token SHA-256 so the
# example's token-compare path uses ``hmac.compare_digest`` (constant-time)
# against a hash rather than comparing raw bearer tokens with ``==`` or
# ``in``. Never ship plain-text token equality against a user-supplied
# bearer token — it leaks information via timing, and dict lookups short-
# circuit on hash mismatch.
_TOKEN_HASHES: dict[str, tuple[str, str]] = {
    hashlib.sha256(raw.encode()).hexdigest(): (principal, tenant)
    for raw, (principal, tenant) in {
        "token-acme": ("principal-acme-ops", "tenant-acme"),
        "token-globex": ("principal-globex-ops", "tenant-globex"),
    }.items()
}


def _lookup_token(token: str) -> tuple[str, str] | None:
    """Constant-time bearer-token lookup.

    Iterate all known hashes with ``hmac.compare_digest`` so the wall-clock
    runtime doesn't depend on how much of the candidate matches any entry —
    the dict-lookup-then-equality pattern leaks that.
    """
    if not token:
        return None
    candidate = hashlib.sha256(token.encode()).hexdigest()
    for stored_hash, identity in _TOKEN_HASHES.items():
        if hmac.compare_digest(candidate, stored_hash):
            return identity
    return None


# ----------------------------------------------------------------------
# HTTP middleware — auth gate, honors DISCOVERY_TOOLS.
# ----------------------------------------------------------------------


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        tool = await _peek_tool_name(request)

        principal_token = None
        tenant_token = None
        try:
            # AdCP spec: ``get_adcp_capabilities`` is the discovery handshake —
            # clients MUST be able to call it without authenticating.
            if tool in DISCOVERY_TOOLS:
                principal_token = _principal.set(None)
                tenant_token = _tenant.set(None)
                return await call_next(request)

            # Everything else requires a bearer token.
            auth_header = request.headers.get("authorization", "")
            bearer = auth_header.removeprefix("Bearer ").strip()
            identity = _lookup_token(bearer)
            if identity is None:
                return JSONResponse({"error": "unauthenticated"}, status_code=401)

            principal_id, tenant_id = identity
            principal_token = _principal.set(principal_id)
            tenant_token = _tenant.set(tenant_id)
            return await call_next(request)
        finally:
            # Reset unconditionally. Without this, a later task running in
            # the same context reads the leftover principal — a
            # cross-request confidentiality leak.
            if principal_token is not None:
                _principal.reset(principal_token)
            if tenant_token is not None:
                _tenant.reset(tenant_token)


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


def build_context(meta: RequestMetadata) -> ToolContext:
    return ToolContext(
        request_id=meta.request_id,
        caller_identity=_principal.get(),
        tenant_id=_tenant.get(),
        metadata={"tool_name": meta.tool_name, "transport": meta.transport},
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
