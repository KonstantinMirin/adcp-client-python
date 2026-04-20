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
  pattern, the `DISCOVERY_METHODS` + `DISCOVERY_TOOLS` composed bypass
  (note: `tools/list` is pre-auth by default — see
  [tools/list is unauthenticated by default](#toolslist-is-unauthenticated-by-default)),
  and `hmac.compare_digest`.
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

**`tools/list` reflects your overrides, not the full spec surface.**
By default the SDK advertises only the tools whose methods your
subclass overrode (plus spec-mandated discovery). The minimal
``MySeller`` above would surface two tools to MCP clients
(``get_adcp_capabilities`` + ``get_products``), not 57 — dropping
~20-30K tokens of unused tool schemas from every client's context.
Pass ``advertise_all=True`` to ``serve()`` / ``create_mcp_server()`` /
``create_a2a_server()`` to restore the full surface (spec-compliance
storyboards, agents that deliberately signal
``not_supported`` on specific tools).

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
from adcp.server import DISCOVERY_METHODS, DISCOVERY_TOOLS

async def dispatch(self, request, call_next):
    method, tool_name = _peek_jsonrpc(request)
    is_discovery = method in DISCOVERY_METHODS or (
        method == "tools/call" and tool_name in DISCOVERY_TOOLS
    )
    if not is_discovery:
        self._require_valid_token(request)
    return await call_next(request)
```

Your agent may have additional public discovery tools outside the AdCP
spec (e.g. a public `list_public_formats`); extend with `DISCOVERY_TOOLS
| {"your_tool"}` rather than redefining the set. See also
[tools/list is unauthenticated by default](#toolslist-is-unauthenticated-by-default)
for the MCP-layer handshake methods this same gate covers.

### `tools/list` is unauthenticated by default

MCP's streamable-HTTP transport accepts three JSON-RPC methods as
pre-auth handshake: `initialize` (session setup),
`notifications/initialized` (handshake-completion notification), and
`tools/list` (inventory advertisement). All three are exported as
`DISCOVERY_METHODS` for the composed gate above. This is consistent
with the MCP spec — discovery is a handshake concern — and with the
AdCP spec, where `get_adcp_capabilities` is pre-auth.

An unauthenticated client POSTing `{"method": "tools/list"}` receives
the full tool inventory: names, input schemas, descriptions, and
annotations. The SDK treats tool names and input schemas as
non-sensitive — they are public AdCP spec surface, and AdCP's discovery
flow presumes clients can see them before deciding whether to
authenticate. Freeform description strings are the one leakage vector.
If your deployment:

- **Adds tools outside the AdCP spec** with custom descriptions that
  embed deployment hints (internal names, rollout flags,
  customer-specific surfaces), either scrub the descriptions or gate
  `tools/list`.
- **Ships only spec-defined tools**, the descriptions come from
  `ADCP_TOOL_DEFINITIONS` — already public upstream — and no
  scrubbing is needed.

To gate `tools/list` behind auth, remove it from `DISCOVERY_METHODS`
in your middleware and run the same credential check you run for
`tools/call`. Clients that support auth-on-handshake work fine;
clients that expect pre-auth discovery will break and need an
out-of-band tool manifest.

The integration test at
[`tests/test_mcp_middleware_composition.py`](../tests/test_mcp_middleware_composition.py)
locks the default posture with a positive assertion that `tools/list`
returns 200 without credentials and a negative control that the gate
still lets it through when an invalid bearer is present.

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

### Durable task storage

A2A tracks each long-running operation as a `Task` — the default
`InMemoryTaskStore` keeps them in a process-local dict. That's fine for
demos but tasks vanish on restart and don't share across workers.
Production agents inject a durable `TaskStore`:

```python
from adcp.server import serve
from examples.a2a_db_tasks import SqliteTaskStore

serve(
    MyAgent(),
    transport="a2a",
    task_store=SqliteTaskStore("/var/lib/myagent/tasks.db"),
)
```

The `task_store=` kwarg accepts any `a2a.server.tasks.task_store.TaskStore`
subclass. `examples/a2a_db_tasks.py` is a runnable reference SQLite
implementation; swap in asyncpg / aiomysql / Redis for multi-node
deployments. For maximum correctness, implement the store against the
same engine/transaction as your handler's business writes so
"handler success → task save" happens atomically.

**Four things a durable `TaskStore` MUST do — the
`InMemoryTaskStore` got away with ignoring these because crash =
reset; your persistent store can't:**

1. **Filter every read, write, and delete by the authenticated
   principal.** The `TaskStore` ABC hands you a `ServerCallContext` on
   every call; a2a-sdk's `DefaultRequestHandler` always passes it. If
   your `get(task_id, context)` ignores `context.user`, any principal
   that learns another tenant's task id retrieves that tenant's task —
   history, artifacts, PII, all of it. The reference `SqliteTaskStore`
   derives a `scope` column from `context.user.user_name`; override
   `_scope_from_context` if you carry richer identity.
2. **Protect the database file.** Tasks include buyer-supplied
   `Message.parts` content and artifact metadata. On a shared host the
   default umask leaves the database world-readable. Set `0o600` on
   creation (reference does this), mount on an encrypted volume, and
   treat backups as the same trust boundary as the live DB.
3. **Handle concurrent writes explicitly.** Two workers saving the
   same task interleave. `INSERT OR REPLACE` is last-writer-wins and
   will silently revert state (`completed` → `working`). Add a version
   column, a `WHERE updated_at < ?` guard, or wrap updates in a
   transaction with explicit conflict handling.
4. **Garbage-collect terminal tasks.** Without a TTL / sweeper, your
   database grows unbounded and every completed task is retained
   forever — an ever-expanding exfiltration target. Add a periodic
   sweep deleting tasks in `completed` / `canceled` / `failed` states
   older than your retention policy.

### Durable push-notification config storage

Clients subscribe to task progress by calling
`tasks/pushNotificationConfig/set`. a2a-sdk's default behavior is
**push-notif disabled** — the endpoint surfaces
`UnsupportedOperationError` until you wire a store. Sellers that accept
push-notif subscriptions pass one:

```python
from adcp.server import serve
from examples.a2a_db_tasks import (
    SqliteTaskStore,
    SqlitePushNotificationConfigStore,
)

serve(
    MyAgent(),
    transport="a2a",
    task_store=SqliteTaskStore("/var/lib/myagent/tasks.db"),
    push_config_store=SqlitePushNotificationConfigStore(
        "/var/lib/myagent/push_configs.db"
    ),
)
```

**Three things a durable push-notification config store MUST do —
beyond the four from the TaskStore section above:**

1. **Validate the client-supplied `url` against an allowlist before
   persisting.** a2a-sdk's push-notif sender POSTs full task JSON to
   whatever URL is stored, with no built-in validation. An attacker
   registering `url=http://169.254.169.254/…` (cloud metadata) or
   `http://localhost:5432/` (internal services) gets SSRF +
   exfiltration in one call — the task JSON that lands on the
   attacker's server includes `history` and `artifacts`. The
   reference impl does NOT validate URLs; the seller's store (or
   a pre-persist hook) must. Reject non-https, reject RFC 1918 /
   IPv6 link-local, and require the host match an egress allowlist
   before `set_info` writes anything.
2. **Treat `PushNotificationConfig.authentication.credentials` and
   `PushNotificationConfig.token` as secrets at rest.** Clients pass
   bearer tokens / shared secrets so the agent's callbacks can
   authenticate. The reference impl serialises them to plaintext JSON
   under `chmod 0o600` — safe on a single-user host but that
   guarantee doesn't survive backups, Docker bind mounts with wrong
   umask, DB-to-Postgres migrations, or shared-volume mounts.
   Production stores should envelope-encrypt those fields, or persist
   opaque references and keep the secrets in a dedicated backend
   (Vault, AWS KMS, GCP Secret Manager).
3. **Scope by principal, not just by tenant.** a2a-sdk's ABC doesn't
   pass a `ServerCallContext` to push-config methods, so scoping has
   to happen out-of-band. The reference `SqlitePushNotificationConfigStore`
   reads a `ContextVar` your auth middleware populates and writes a
   `scope` column on every row. Cross-scope isolation works; **within
   a scope, multiple principals can still overwrite each other's
   configs** (same `(scope, task_id)`, client omits `config_id`, PK
   collision). For multi-principal-per-tenant deployments, widen the
   scope to include the principal (e.g. `f"{tenant}:{principal}"`) or
   require clients to supply an explicit `config_id`.

**Scoping caveat.** The reference impl's ContextVar approach has a
known gap: a2a-sdk's push-notif sender runs in a background
`asyncio.Task` that inherits the ContextVar snapshot from
task-creation time. If the seller's auth middleware has already reset
the ContextVar before the sender reads it, `get_info` returns empty
and notifications silently drop. Sellers running non-blocking
push-notifs must propagate scope into the sender path explicitly —
either capture the scope at `set_info` time and stash it alongside
the config, or override a2a-sdk's `BasePushNotificationSender` to
re-set the ContextVar before calling `get_info`. Not yet addressed in
the SDK.

**Operator-facing failure modes.** When `scope_provider` returns
`None`, the reference store falls through to an `__anonymous__`
bucket and emits a one-time `UserWarning`. Silent fall-through would
share one push-notif bucket across every unauthenticated caller. The
warning is the signal your auth middleware isn't populating the
ContextVar — treat it as a P0.

### Per-skill middleware (audit, activity feeds, rate limiting, tracing)

Every A2A skill dispatch can be wrapped in a chain of middleware
callables. Pass them as `middleware=[...]` to `create_a2a_server` /
`serve` / `ADCPAgentExecutor` — first entry wraps outermost, matching
Starlette/ASGI ordering:

```python
from adcp.server import SkillMiddleware, ToolContext, serve

async def audit_middleware(
    skill_name: str,
    params: dict,
    context: ToolContext,
    call_next,
) -> Any:
    started = time.monotonic()
    try:
        result = await call_next()
    except Exception as exc:
        audit_log.failure(skill_name, context.caller_identity, exc)
        raise
    audit_log.success(
        skill_name,
        context.caller_identity,
        elapsed_ms=(time.monotonic() - started) * 1000,
    )
    return result

serve(MyAgent(), transport="a2a", middleware=[audit_middleware])
```

**Semantics worth knowing:**

- **Composition — put audit outermost.** `middleware=[Audit(),
  RateLimit(), Metrics()]` runs `Audit → RateLimit → Metrics →
  handler` on the way in and unwinds in the opposite order. **If you
  put rate-limiting before audit, rejected requests disappear from
  your audit log** — often the most interesting events for security
  review. Audit always outermost.
- **Short-circuit — cache keys MUST include principal + tenant.** A
  middleware that returns without calling `call_next()` stops the
  chain; its return value becomes the dispatch result. Rate limiters
  / feature flags use this. **Caching middleware that short-circuits
  must key on `(skill_name, params, context.caller_identity,
  context.tenant_id)`** — a cache keyed only on `skill_name + params`
  serves principal A's data to principal B on a matching-params call.
- **Exception observation — never swallow an `ADCPError`.** Catch
  around `await call_next()` to log failures. Re-raise to let the
  executor's normal error path take over (`ADCPError` → failed task
  with `adcp_error` DataPart; other exceptions → opaque failed task).
  Swallowing an `ADCPError` (especially `IdempotencyConflictError` or
  `ADCPTaskError`) and returning a fake-success dict silently converts
  a rejected mutation into a "completed" task — double-billing,
  double-allocation, duplicated side effects. Don't.
- **Exception messages end up in server logs.** Middleware-raised
  exceptions flow through `logger.exception` in the executor before
  client-facing sanitisation. Don't format `params` or
  `context.caller_identity` into exception text — operators read those
  logs.
- **Retry is supported.** Call `call_next()` more than once (e.g.
  retry-on-transient-error middleware). Each call gets a fresh
  inner chain — composition is re-entrant by design.
- **Transform on return, not on input.** `params` passed in is the
  same dict every middleware sees. Mutating it doesn't change what
  the next layer receives. Transforms happen on the *return* side by
  modifying the value of `await call_next()`.
- **Context access**: the middleware sees the `ToolContext` produced
  by the `context_factory` (or the a2a-sdk fallback). Tenant id,
  caller identity, anything your factory populates. `ContextVar`s set
  before `call_next()` propagate to the handler — no `asyncio.create_task`
  needed.

**Security — middleware is a data processor for the full skill
payload.** `params` carries decoded buyer briefs, budgets, brand
refs, proposal text, PII in message parts. `context` carries
`caller_identity` + `tenant_id`. Installing a third-party middleware
(SaaS audit, observability vendor, bespoke tracing) hands that vendor
the complete skill surface. Treat it as a data processor under your
GDPR/CCPA controller-processor agreements.

MCP transport has its own middleware story (see "Pattern 2 —
in-process HTTP middleware" above); `SkillMiddleware` is A2A-only.

### Known gaps

All three Phase-2 A2A hooks (#224 TaskStore, #225 PushNotificationConfigStore,
#226 SkillMiddleware) have landed. A2A adoption now reaches parity with
MCP for production agents.

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

## Testing hooks — storyboard + header-driven composition

Two orthogonal test-runtime shapes exist in the wild. Compose them via
the same `context_factory` you already wire for auth:

**Storyboard-driven** (SDK-native). Sellers register a
`TestControllerStore` and clients invoke the `comply_test_controller`
skill with a scenario name (`force_media_buy_status`, `simulate_delivery`,
etc.). This is the AdCP spec's compliance-test shape and what the
conformance suite exercises.

**Header-driven** (downstream pattern, e.g. salesagent's
`AdCPTestContext.from_headers(request.headers)`). Clients pass HTTP
headers like `X-AdCP-Test-Mode: slow` and the server adjusts mock
behavior. Useful for scenario-wide state that doesn't fit the
storyboard frame — "every update in this request returns pending",
"this request simulates a delayed ad server".

Before SDK 3.x you had to pick one. As of #227 both compose through
the existing `context_factory`:

```python
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

from adcp.server import RequestMetadata, ToolContext, create_mcp_server
from adcp.server.test_controller import (
    TestControllerStore,
    register_test_controller,
)

# 1. ContextVar the HTTP middleware populates from request headers.
_test_context: ContextVar[AdCPTestContext | None] = ContextVar(
    "test_context", default=None
)


# 2. Starlette middleware reads headers into the ContextVar per request.
class TestHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        _test_context.set(AdCPTestContext.from_headers(request.headers))
        return await call_next(request)


# 3. context_factory snapshots the ContextVar onto ToolContext.
def build_context(meta: RequestMetadata) -> ToolContext:
    return ToolContext(
        metadata={"test_context": _test_context.get()},
    )


# 4. Store methods that want header-driven state accept `context`.
class MyStore(TestControllerStore):
    async def force_media_buy_status(
        self,
        media_buy_id: str,
        status: str,
        rejection_reason: str | None = None,
        *,
        context: ToolContext | None = None,
    ) -> dict[str, Any]:
        test_ctx = (context.metadata.get("test_context") if context else None)
        if test_ctx and test_ctx.slow_ad_server:
            status = "pending"  # header-driven behavior override
        self.media_buys[media_buy_id] = status
        return {"previous_state": "active", "current_state": status}


# 5. Wire the same factory into both create_mcp_server AND
#    register_test_controller. Regular handler methods and
#    comply_test_controller both see the same context.
mcp = create_mcp_server(MySeller(), name="my-agent", context_factory=build_context)
register_test_controller(mcp, MyStore(), context_factory=build_context)

app = mcp.streamable_http_app()
app.add_middleware(TestHeaderMiddleware)
```

**Backward compatibility**: stores whose methods don't declare
`context` keep working. The dispatcher inspects the signature and
only passes `context` to methods that opt in. `serve(..., test_controller=...)`
automatically threads `context_factory` through, so no extra wiring is
needed if you use the `serve()` helper.

**When to pick which**: the storyboard skill is for spec-level
compliance tests (scenarios named by the AdCP test suite). Headers are
for your own mock-ad-server behaviors that sit outside the spec.
Sellers typically need both.

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
