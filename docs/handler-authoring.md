# Authoring an ADCP server handler

This guide is for teams building AdCP-compliant agents — sales agents,
creative agents, governance agents, signals agents — on top of
`adcp.server`. It captures the patterns that keep handlers spec-compliant
and production-grade, plus the hooks the SDK provides so you don't have
to rebuild middleware that already exists.

## 15-minute decision tree

- **Just want an agent running?** → Start with "The one-file starting
  point" below, then `serve()`.
- **Need auth in front of tools?** → If your proxy already validates
  credentials, use "Pattern 1 — reverse-proxy auth". Otherwise copy
  `examples/mcp_with_auth_middleware.py` — it covers the ContextVars
  pattern, the `DISCOVERY_TOOLS` bypass, and `hmac.compare_digest`.
- **Multi-tenant?** → Subclass `ToolContext`, populate `tenant_id` in
  your `context_factory`, and read the
  [Multi-tenant typing](#multi-tenant-typing) section. The idempotency
  middleware uses `(tenant_id, caller_identity)` for scope isolation —
  populating `tenant_id` is required for cross-tenant safety.
- **Full context?** → Keep reading.

## The one-file starting point

```python
from adcp.server import ADCPHandler, ToolContext, serve
from adcp.server.responses import capabilities_response, products_response

class MyAgent(ADCPHandler):
    async def get_adcp_capabilities(self, params, context=None):
        return capabilities_response(["media_buy"])

    async def get_products(self, params, context=None):
        return products_response(MY_PRODUCTS)

serve(MyAgent(), name="my-agent")
```

That's a complete AdCP agent. All 57+ other tools return `not_supported`
automatically via the `ADCPHandler` default methods; override only what
your agent actually implements.

## The `_impl` pattern (production-grade)

Production agents usually don't put business logic directly on handler
methods. Instead:

- Business logic lives in `src/core/_impl/` or similar — transport-free,
  takes typed domain objects, returns typed responses.
- `ADCPHandler` methods are thin delegations that pull identity /
  adapter config out of `ToolContext` and call the `_impl` function.

This keeps the tested surface independent of whether the caller came in
via MCP, A2A, HTTP, a background job, or a test. The SDK's server
framework is designed for this shape:

```python
from adcp.server import ADCPHandler, ToolContext
from myagent.impl.products import get_products_impl
from myagent.identity import ResolvedIdentity

class MyAgent(ADCPHandler):
    async def get_products(self, params, context: ToolContext | None = None):
        identity = _resolve_identity(context)
        return await get_products_impl(params, identity=identity)

def _resolve_identity(ctx: ToolContext | None) -> ResolvedIdentity:
    if ctx is None or ctx.caller_identity is None:
        raise AuthenticationRequired()
    return ResolvedIdentity(
        principal_id=ctx.caller_identity,
        tenant_id=ctx.tenant_id,
        # … adapter config, feature flags, etc. from your DB
    )
```

## Authentication

The SDK does not enforce authentication. There are two supported
integration patterns:

### Pattern 1 — reverse-proxy auth

The proxy (nginx, Caddy, Envoy) validates credentials and forwards only
authenticated requests. The SDK trusts the proxy's decision. Simplest,
and the right choice when your identity provider and tool endpoints run
behind the same gateway.

### Pattern 2 — in-process HTTP middleware

Call `mcp.streamable_http_app()` to get the Starlette ASGI app, then
`app.add_middleware(YourAuthMiddleware)`. The middleware validates
credentials, stashes the resolved principal + tenant somewhere the
`context_factory` can read (ContextVars are recommended), and calls
`context_factory=` on `create_mcp_server()` to inject a typed
`ToolContext` per call.

Full worked example: `examples/mcp_with_auth_middleware.py`. Integration
test proving the composition: `tests/test_mcp_middleware_composition.py`.

### Discovery tools bypass auth

Per AdCP spec, `get_adcp_capabilities` is the handshake — clients MUST
be able to call it before authenticating. The SDK exports the list as a
frozenset:

```python
from adcp.server import DISCOVERY_TOOLS

async def dispatch(self, request, call_next):
    tool_name = _peek_tool_name(request)
    if tool_name not in DISCOVERY_TOOLS:
        self._require_valid_token(request)
    return await call_next(request)
```

Your agent may have additional public discovery tools outside the AdCP
spec (e.g. a public `list_public_formats`); extend with `DISCOVERY_TOOLS
| {"your_tool"}` rather than redefining the set.

## Idempotency

The SDK ships an `IdempotencyStore` middleware that honors the
`Idempotency-Key` header per AdCP §idempotency. Requests with the same
`(caller_identity, idempotency_key)` return the cached response instead
of re-executing the handler.

The store keys on `ToolContext.caller_identity` — if your transport
doesn't populate it, per-principal scoping falls through and dedup is
skipped (with a UserWarning). A2A populates it automatically from
`ServerCallContext.user`; MCP requires you to wire `context_factory`.

Don't rebuild idempotency in your handler. Import the middleware.

## Error handling

Raise `AdCPError` (or a subclass: `ADCPTaskError`, `IdempotencyConflictError`)
from handler code. The SDK translates to the wire-level error shape the
AdCP spec mandates — MCP gets a `ToolError` with the spec error code in
the message, A2A gets a `JSON-RPC error` with the code populated.

Use the error classification helpers:

```python
from adcp.server import adcp_error

raise adcp_error("BUDGET_TOO_LOW")  # auto-classifies as correctable
raise adcp_error("DOWNSTREAM_TIMEOUT")  # auto-classifies as transient
```

The recovery hint (transient / correctable / terminal) gets populated
from 20+ standard codes — don't reinvent the table.

## Response builders

Manual `model_dump()` on response Pydantic objects is error-prone —
you'll drift from the spec's required fields. Use the response builders:

```python
from adcp.server.responses import media_buy_response, products_response

return media_buy_response(
    media_buy_id="mb_123",
    status="active",  # auto-populates valid_actions from the state machine
)
```

One per AdCP operation. Read the `adcp.server.responses` docstrings.

## Multi-tenant typing

Production multi-tenant agents usually carry `tenant + principal +
adapter + testing hooks` in their own identity type. `ToolContext`
exposes the fields those handlers need:

- `ToolContext.tenant_id: str | None` — first-class field; populate from
  your `context_factory`. **Required** for multi-tenant deployments
  whose principal IDs are only unique within a tenant (Okta group-scoped,
  SCIM per-tenant, seller-internal employee IDs) — the idempotency
  store keys its cache on `(tenant_id, caller_identity)`, so leaving
  `tenant_id` unset collapses distinct tenants into the same scope and
  enables cross-tenant response replay.
- `ToolContext.metadata: dict[str, Any]` — escape hatch for adapter
  instance handles, testing hooks, per-tenant config blobs.
- Subclassing `ToolContext` is supported — return the subclass from your
  `context_factory` and your handler methods `isinstance(context,
  MyContext)` (or `cast(MyContext, context)` if you've established the
  invariant via the factory) to reach the extra fields.

When in doubt, subclass: `metadata: dict[str, Any]` loses type safety.

## A2A transport

`serve(MyAgent(), transport="a2a")` wires the same handler through the
A2A protocol with auto-generated agent card (`/.well-known/agent.json`)
derived from the `ADCPHandler` methods your class overrides.

Caveats:

- The SDK uses `a2a-sdk`'s `DefaultRequestHandler` + `InMemoryTaskStore`.
  Tasks do not persist across restarts.
- Push-notification config is in-memory only.
- Per-skill middleware hooks for audit logging / activity feeds don't
  exist yet (tracked in the SDK adoption roadmap).

If your agent needs DB-backed tasks, persistent push-notif config, or
per-skill audit hooks, keep a custom A2A server for now. The MCP side is
production-ready; the A2A side is reference-quality.

## Testing

The integration test pattern in `tests/test_mcp_middleware_composition.py`
is the shape you can copy for your own middleware tests. Key pieces:

- `create_mcp_server(..., context_factory=build_context)` wires the
  context factory.
- `mcp.settings.stateless_http = True` + `mcp.settings.json_response = True`
  disables the session manager so tests don't need a TaskGroup.
- `mcp.settings.transport_security.allowed_hosts = ["localhost"]` allows
  in-process `httpx.ASGITransport` requests through the DNS-rebinding
  guard.
- Run the app's lifespan manually if you're exercising HTTP endpoints.

## What not to build

- Don't write per-tool `@mcp.tool()` wrappers. `create_mcp_server()`
  registers all ADCP tools from a handler automatically.
- Don't hand-maintain an agent card. A2A auto-derives it from the
  handler methods you override.
- Don't reinvent `IdempotencyStore`, response builders, or error
  classification. Use the shipped helpers.
- Don't import from `adcp.types.generated_poc.*`. Everything public
  lives at `adcp.types` or `adcp` — and the internal paths renumber
  between releases (see `MIGRATION_v3_to_v4.md`).

## Where to look next

- `examples/minimal_sales_agent.py` — handler-only starting point.
- `examples/mcp_with_auth_middleware.py` — full auth + typed context.
- `src/adcp/server/responses.py` — response builder reference.
- `src/adcp/server/helpers.py` — error codes, state machine, account
  resolution.
- `tests/test_mcp_middleware_composition.py` — the integration test
  that protects this contract.
