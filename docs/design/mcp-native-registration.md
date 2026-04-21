# FastMCP native Pydantic registration — investigation

Status: decided — **stay with generation layer**
Issue: [#209](https://github.com/adcontextprotocol/adcp-client-python/issues/209)
Date: 2026-04-21

## Question

Can FastMCP's native `@mcp.tool` decorator (with a Pydantic-typed `params`) replace
`ADCP_TOOL_DEFINITIONS` + `_generate_pydantic_schemas()` and drive the drift surface
to zero?

## Answer

No. FastMCP's native path produces the wrong tool-argument shape for AdCP, and the
ergonomic wins don't survive the per-tool metadata we'd still need to hand-author.

## Findings

### 1. Native path wraps, does not unwrap, pydantic-typed params

```python
async def get_products(req: GetProductsRequest) -> dict: ...
mcp.add_tool(get_products, name="get_products")
```

Produces:

```json
{
  "properties": { "req": { "$ref": "#/$defs/GetProductsRequest" } },
  "required": ["req"],
  "$defs": { ... }
}
```

AdCP wire format expects the request model's fields **as tool arguments directly**
(e.g., `{"buying_mode": "brief", "brief": "..."}`), not nested under a `req` key.
FastMCP builds `arg_model` from the function signature
(`mcp/server/fastmcp/utilities/func_metadata.py:178`), treating each parameter as a
top-level field. There is no "unwrap a single pydantic param" option.

### 2. Unwrapped-kwargs native registration loses type fidelity

Hand-writing each request field as a separate function parameter
(`async def get_products(buying_mode, brief, refine, ...)`) produces a flat schema
but forces every param to be typed as `dict | None` or `Any` — you lose the
nested discriminated unions, enums, field descriptions, and validators that the
Pydantic Request model carries. Unmaintainable across 57 tools.

### 3. Hybrid "dynamic ArgModelBase" is just the generation layer, renamed

A dynamic
`create_model(f"{name}Args", __base__=ArgModelBase, **RequestModel.model_fields)`
produces a schema whose top-level `properties` and `required` fields match the
current generation-layer output exactly (verified: 16 properties, same names,
same required set). But this *is* the generation layer — it still needs the
name → Request-model mapping, still calls `model_json_schema()`, still needs
the $ref-inlining pass (current output has `additionalProperties: true` and no
`$defs`; the dynamic arg_model keeps `$defs` unless we inline).

### 4. What FastMCP native *does* give us for free

- `annotations: ToolAnnotations` kwarg on `add_tool()` — supports
  `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
  **We already use this via `Tool.from_function(...)` in `_register_tool`**
  (see `src/adcp/server/serve.py:805-910`).
- `description` kwarg on `add_tool()` — same story; already used.
- `structured_output=True` — already used.

So the "native features" the issue asks about are already on the hot path. What
gets rewritten in the override block is specifically the arg shape.

### 5. Startup cost is not a win

- Current (measured): `_generate_pydantic_schemas()` runs in ~100ms once at import,
  building 57 schemas.
- Native: `add_tool()` takes ~11ms per tool × 57 = ~640ms at server-startup time.

Native is slower in aggregate because FastMCP re-validates each tool and its
output model individually. Deferring until first request is possible, but it
shifts cost onto the first call rather than eliminating it.

### 6. Behavior that would need re-implementation under pure native

- `_inline_refs()` — MCP clients that don't chase `$ref`s (non-trivial slice of
  the ecosystem) need flat schemas. Native registration keeps `$defs`.
- `additionalProperties: true` — extension-safety default on the current output.
  Native is `additionalProperties: false`.
- `get_tools_for_handler()` MRO-walk + `_is_method_overridden()` filtering —
  advertises only tools the handler actually answers. Native has no equivalent;
  we'd wire the same filter upstream of `add_tool`.
- `create_tool_caller()` handler-instance binding + `inject_context()` echo +
  structured `INVALID_REQUEST` translation on Pydantic `ValidationError`.
  These live per-handler-instance and can't be expressed via a decorator on a
  free function.

## Recommendation

**Keep the generation layer.** The architectural premise — "FastMCP native
registration can express everything we need" — doesn't hold for the
flat-arg-surface AdCP requires. The override in `_register_tool`
(`src/adcp/server/serve.py:881-910`) is load-bearing, not accidental.

Do not delete `ADCP_TOOL_DEFINITIONS` or `_generate_pydantic_schemas()`.

### Small, separate wins worth considering

1. **Consolidate the two parallel tables.** `ADCP_TOOL_DEFINITIONS` (name +
   description + annotations + stub inputSchema) and `_tool_to_request`
   (name → Pydantic request model) are both keyed by tool name and must stay
   in sync. `test_mcp_schema_drift.py` exists because they can drift. A single
   declarative table
   ```python
   ADCP_TOOLS = [
       ToolSpec(name="get_products", request=GetProductsRequest,
                description="...", annotations=_RO),
       ...
   ]
   ```
   would remove the drift vector without changing the runtime model. Worth a
   follow-up issue; not a blocker.

2. **Drop the hand-crafted `inputSchema` stubs in `ADCP_TOOL_DEFINITIONS`.**
   Today each entry carries a minimal `inputSchema` that `_apply_pydantic_schemas()`
   immediately overwrites. The fallback path (Pydantic generation fails →
   keep hand-crafted) hasn't fired in practice; the drift test guarantees
   every tool has a Pydantic model. Schemas can be generated-only.

3. **Cache schemas to disk** (or a Python file committed to the repo) to remove
   the 100ms import cost and make schema output auditable in code review.
   Probably over-engineering at current scale.

None of these are native-FastMCP migrations. They're cleanups within the
existing architecture.

## Re-open trigger

Re-investigate if FastMCP ships one of:

- A "flatten single pydantic param" option on `@tool()` / `add_tool()`.
- Public API for registering a pre-built `Tool` object with a custom
  `parameters` schema, removing the `mcp._tool_manager._tools[name] = tool`
  workaround.

Either would change the calculus.
