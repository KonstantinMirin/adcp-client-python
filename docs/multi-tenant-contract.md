# Multi-tenant contract

This is the security-critical surface of `adcp.server`. Sellers serving
more than one tenant (or more than one account within a tenant) must
satisfy every invariant below. Each invariant names the failure mode
you get if you violate it — use this as an audit checklist.

The SDK enforces some of these automatically (idempotency scope
composition); others are the seller's responsibility to populate
correctly. Both kinds are listed here.

## The three scopes

AdCP models three nested identifiers. Handlers, middleware, audit logs,
and cache keys all compose from these three.

| Scope | Source | Populated on |
|-------|--------|-------------|
| `caller_identity` | Authenticated principal (token, mTLS, signed request) | `ToolContext.caller_identity` |
| `tenant_id` | Seller's tenancy model — maps an authenticated principal to its tenant | `ToolContext.tenant_id` |
| `account_id` | Request parameter (`params.account`) resolved via `resolve_account` | `AccountAwareToolContext.account_id` |

`caller_identity` and `tenant_id` are **authentication-scoped** — they
come from the bearer token / client cert / discovery key, and do not
change for the lifetime of the request. `account_id` is
**request-scoped** — the same principal can operate on different
accounts on successive calls.

## Invariants

### I1. `caller_identity` MUST be stable and globally unique within the tenant

A *stable* identifier means the same string for the same principal
across all time. An *email address is not stable* — it can be recycled
after account deletion, renamed, or merged.

**Populate with**: the principal's surrogate id from your IdP (Okta
`sub` claim, SCIM `externalId`, internal employee id, signing key
fingerprint). Never an email, display name, or any other mutable
handle.

**Failure mode**: cross-principal replay of idempotent responses. The
server-side idempotency store keys cached responses by
`(scope_key, idempotency_key)` where `scope_key` composes
`tenant_id + caller_identity`. If principal A's identity is reused
after they're deleted and assigned to principal B, B will see A's
cached responses — a confidentiality leak.

**Where populated**: transport layer.
- A2A: `ADCPAgentExecutor` reads it from `ServerCallContext.user.user_name`.
- MCP: the seller's FastMCP auth middleware populates a `ContextVar`
  that `context_factory` reads (see `examples/mcp_with_auth_middleware.py`).

### I2. `tenant_id` MUST be populated when principal ids are tenant-scoped

If your principal ids are *only unique within a tenant* — typical for
Okta group-scoped ids, SCIM per-tenant ids, seller-internal employee
ids — you **must** populate `tenant_id` so the idempotency store can
compose `(tenant_id, caller_identity)` into a globally-unique scope
key.

**Failure mode**: cross-tenant replay. Principal "alice@corp" on tenant
T1 and principal "alice@corp" on tenant T2 would share cached
responses. Another confidentiality leak, this time across tenants.

**Single-tenant exception**: if every principal id is globally unique
across your entire deployment (e.g. every principal id is a UUID, or
the service only ever serves one tenant), you can leave `tenant_id`
unset and the scope collapses to `caller_identity` alone.

**Where populated**: seller's `context_factory`. Look up the tenant
for the authenticated principal and populate the field on the
`ToolContext` returned by the factory. Subclass `ToolContext` if your
tenant model needs more than a string id.

### I3. `account_id` is request-scoped, not authentication-scoped

An authenticated principal may operate on several accounts — for
example, an agency with multiple brand accounts, or a reseller managing
downstream advertisers. Every operation's `account` parameter carries
an `AccountReference` that the seller resolves to a concrete account
at the handler boundary.

**Populate with**: the resolved account's stable id from the seller's
own system. Same stability rule as `caller_identity` — no emails, no
display names.

**Failure mode**: authorization bypass. If you treat
`context.account_id` as if it were as stable as `caller_identity`, a
single handler invocation can end up scoping a downstream cache or
authorization check to the wrong account.

**Where populated**: the handler (or a middleware), per-call, via
`resolve_account_into_context(params, context, resolver)`. The helper
populates `AccountAwareToolContext.account_id` if the resolver
succeeds, and returns an `ACCOUNT_NOT_FOUND` / `ACCOUNT_SUSPENDED` /
etc. error dict if it doesn't.

### I4. Idempotency scope keys MUST include tenant + principal

Enforced by `IdempotencyStore` — listed here so you know what the SDK
guarantees.

The cache key is `(scope_key, idempotency_key)` where `scope_key`
derives from both `tenant_id` and `caller_identity` on the request
context. You cannot bypass this by supplying your own scope key; the
store composes it internally from the `ToolContext` fields.

**Seller's responsibility**: populate `caller_identity` (I1) and
`tenant_id` (I2) correctly. The SDK does the composition.

### I5. Caches and audit logs MUST key on the same three scopes

Any seller-side cache (product catalog, resolved accounts, rate limit
counters) or audit log that stores per-principal or per-account state
MUST key on `(tenant_id, caller_identity, account_id)` — or a prefix of
that tuple appropriate for the data.

**Failure mode**: same class as I1/I2 — confidentiality or
authorization leaks. The SDK idempotency store is just the most
prominent example of the rule; your own storage has to follow it too.

**Rule of thumb**: if you cache something derived from the request
context or params, the cache key must incorporate whichever of the
three scopes varied to produce the cached value.

### I6. `context_factory` MUST NOT hold mutable per-request state

`context_factory` is called once per request; the returned
`ToolContext` is passed through every handler invocation in that
request. If your factory mutates a shared instance instead of
returning a fresh one, concurrent requests will read each other's
scopes.

**Where this bites**: sellers who cache their `context_factory` result
module-globally and mutate it.

**Rule**: the factory returns a **new** `ToolContext` (or subclass)
every call.

### I7. Never stash the context in a module-level variable

Handlers receive `context` as a parameter. Adopting a ContextVar
pattern for ergonomics (resetting the var in a `finally` block) is
fine; storing `context` in a module-level dict indexed by anything
other than the request's transient id is not.

**Failure mode**: cross-request leak. Request A's context is still in
the module when request B starts — whatever B reads is A's data.

The same advice applies to application-level locks, caches, and
tracing state: scope them by tenant + principal + account as in I5.

## Wiring it up

### Single-tenant agent (simplest)

Populate `caller_identity` from your auth middleware. Leave `tenant_id`
unset (scope collapses safely).

```python
serve(MyAgent(), name="my-agent", context_factory=my_auth_context_factory)
```

### Multi-tenant agent (typical)

Subclass `ToolContext` with your tenant model, populate it in the
factory, parameterise the handler so types flow through.

```python
from dataclasses import dataclass
from adcp.server import ADCPHandler, ToolContext

@dataclass
class TenantContext(ToolContext):
    tenant: Tenant | None = None  # your tenant model
    # caller_identity + tenant_id fields inherited from ToolContext

class MyAgent(ADCPHandler[TenantContext]):
    async def get_products(self, params, context=None):
        ...
```

The `context_factory` returns `TenantContext(caller_identity=..., tenant_id=..., tenant=...)`.

### Account-scoped operations

Add `account_id` resolution per-call. Use `AccountAwareToolContext`
(or a subclass of it) and resolve at handler entry.

```python
from adcp.server import (
    ADCPHandler,
    AccountAwareToolContext,
    resolve_account_into_context,
)

class MyAgent(ADCPHandler[AccountAwareToolContext]):
    async def get_products(self, params, context=None):
        err = await resolve_account_into_context(params, context, my_resolver)
        if err:
            return err
        # context.account_id is populated — safe to scope cache/audit by it
        return products_response(self.catalog.for_account(context.account_id))
```

## Audit checklist

Before shipping a multi-tenant agent, verify each of these:

- [ ] `caller_identity` is populated from a stable surrogate id, not an email.
- [ ] `tenant_id` is populated (unless single-tenant or globally unique ids).
- [ ] `context_factory` returns a fresh `ToolContext` on every call.
- [ ] No module-level dict indexes `ToolContext` instances by mutable keys.
- [ ] Every seller-side cache or audit log keys on
      `(tenant_id, caller_identity, account_id)` as appropriate for the data.
- [ ] Account-scoped handlers call `resolve_account_into_context` before
      touching account-scoped storage.
- [ ] Tests cover the cross-tenant and cross-principal leak paths
      (two concurrent requests with different scopes return different results).

## Related reading

- `examples/mcp_with_auth_middleware.py` — concrete ContextVar pattern
  for MCP, including the discovery-method bypass.
- `docs/handler-authoring.md` — broader handler patterns, including
  the single-file starting point.
- `src/adcp/server/idempotency/store.py` — how scope keys are composed
  inside the SDK.
