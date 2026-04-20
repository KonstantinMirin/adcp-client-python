"""Example: multi-tenant MCP server with bearer-token auth.

Wires :class:`~adcp.server.BearerTokenAuthMiddleware` +
:func:`~adcp.server.auth_context_factory` onto a multi-tenant sales
agent. The SDK owns the security-critical plumbing (constant-time
token compare, discovery bypass, ``ContextVar`` reset-in-finally);
the seller supplies only ``validate_token`` and the handler logic.

Run::

    uv run python examples/mcp_with_auth_middleware.py
    # → server on http://localhost:3001/mcp/
    # curl -H 'Authorization: Bearer token-acme' ...

Production note: ``mcp.run()`` is used here for brevity. Real
deployments should mount the Starlette app behind uvicorn + a reverse
proxy that terminates TLS and handles rate limiting.
"""

from __future__ import annotations

import hashlib
from typing import Any

from adcp.server import (
    ADCPHandler,
    BearerTokenAuthMiddleware,
    Principal,
    ToolContext,
    auth_context_factory,
    constant_time_token_match,
    create_mcp_server,
)
from adcp.server.responses import capabilities_response, products_response

# Real agents look tokens up in Postgres / Vault / an identity provider.
# Keyed by SHA-256 so the comparison uses ``hmac.compare_digest`` rather
# than raw string equality — never compare raw bearer tokens with ``==``.
_TOKEN_HASHES: dict[str, Principal] = {
    hashlib.sha256(raw.encode()).hexdigest(): principal
    for raw, principal in {
        "token-acme": Principal(
            caller_identity="principal-acme-ops",
            tenant_id="tenant-acme",
        ),
        "token-globex": Principal(
            caller_identity="principal-globex-ops",
            tenant_id="tenant-globex",
        ),
    }.items()
}


def validate_token(token: str) -> Principal | None:
    """Seller-supplied token validator.

    ``constant_time_token_match`` iterates every stored hash with
    :func:`hmac.compare_digest`, avoiding the prefix-match timing leak
    that a plain ``dict`` lookup would have.
    """
    return constant_time_token_match(token, _TOKEN_HASHES)


class MultiTenantSalesAgent(ADCPHandler):
    _agent_type = "demo multi-tenant sales agent"

    async def get_adcp_capabilities(
        self, params: Any, context: ToolContext | None = None
    ) -> dict[str, Any]:
        return capabilities_response(["media_buy"])

    async def get_products(self, params: Any, context: ToolContext | None = None) -> dict[str, Any]:
        tenant = context.tenant_id if context is not None else None
        return products_response(_products_for_tenant(tenant))


def _products_for_tenant(tenant_id: str | None) -> list[dict[str, Any]]:
    if tenant_id == "tenant-acme":
        return [{"product_id": "acme_display_1", "name": "Acme homepage display"}]
    if tenant_id == "tenant-globex":
        return [{"product_id": "globex_video_1", "name": "Globex CTV video"}]
    return []


def main() -> None:
    mcp = create_mcp_server(
        MultiTenantSalesAgent(),
        name="multi-tenant-sales-agent",
        context_factory=auth_context_factory,
    )
    app = mcp.streamable_http_app()
    app.add_middleware(BearerTokenAuthMiddleware, validate_token=validate_token)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
