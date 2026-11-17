"""``tools/list`` advertises ``outputSchema`` for every spec-mapped tool.

JS parity: the TS SDK ships ``outputSchema`` alongside ``inputSchema`` on
``tools/list`` so MCP clients can validate ``structuredContent`` without
a separate spec lookup. Python previously shipped only ``inputSchema``.

Two layers covered here:

* :data:`ADCP_TOOL_DEFINITIONS` (the in-memory inventory) carries an
  ``outputSchema`` for every Pydantic-mapped tool.
* The wire-level ``tools/list`` JSON-RPC response surfaces the same
  schema on the FastMCP transport. Locks in the integration so a
  regression on either side breaks loudly.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from asgi_lifespan import LifespanManager

from adcp.server import ADCPHandler, create_mcp_server
from adcp.server.mcp_tools import ADCP_TOOL_DEFINITIONS, _definition_pointer_body

# Sample of tools to lock in: one read-only catalog tool, one mutating
# tool with a discriminated union response, one discovery tool. If any
# of these regress to no outputSchema, the SDK has dropped JS parity.
_SAMPLE_TOOLS: tuple[str, ...] = (
    "get_products",
    "create_media_buy",
    "get_adcp_capabilities",
    "validate_input",
    "verify_brand_claim",
    "verify_brand_claims",
)


# ----------------------------------------------------------------------
# In-memory inventory
# ----------------------------------------------------------------------


def test_adcp_tool_definitions_has_output_schema_for_sample_tools() -> None:
    by_name = {t["name"]: t for t in ADCP_TOOL_DEFINITIONS}
    for tool_name in _SAMPLE_TOOLS:
        tool_def = by_name[tool_name]
        assert "outputSchema" in tool_def, (
            f"{tool_name} is missing outputSchema in ADCP_TOOL_DEFINITIONS — "
            "JS parity regression"
        )
        schema = tool_def["outputSchema"]
        assert isinstance(schema, dict)
        assert schema, f"{tool_name} outputSchema is empty"


def test_get_products_output_schema_is_object_shape() -> None:
    """``get_products`` returns a single response model — its outputSchema
    should be a flat ``type: object`` shape, not a discriminated union.
    Catches regressions where the response generator silently falls back."""
    by_name = {t["name"]: t for t in ADCP_TOOL_DEFINITIONS}
    schema = by_name["get_products"]["outputSchema"]

    assert schema.get("type") == "object"
    assert "properties" in schema
    # Spec: ``products`` is the load-bearing field.
    assert "products" in schema["properties"]


def test_create_media_buy_output_schema_includes_response_union() -> None:
    """``create_media_buy`` returns a 3-arm discriminated union (success /
    error / pending). The advertised outputSchema must surface that —
    JS parity ships ``anyOf`` for these."""
    by_name = {t["name"]: t for t in ADCP_TOOL_DEFINITIONS}
    schema = by_name["create_media_buy"]["outputSchema"]

    assert "anyOf" in schema, (
        "create_media_buy outputSchema lost its discriminated union — "
        "MCP clients can't tell success from error from pending without it"
    )
    assert isinstance(schema["anyOf"], list)
    assert len(schema["anyOf"]) >= 2


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Follow a local ``$ref`` into ``schema["$defs"]``.

    Advertised schemas are compact on both sides, so a union branch is a
    reference rather than an inline object. A document's pointer may continue
    into a definition, so resolve it the way the publisher does.
    """
    ref = node.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
        return node
    target = _definition_pointer_body(schema.get("$defs", {}), ref)
    assert isinstance(target, dict)
    return target


def test_media_buy_output_schema_accepts_negotiated_30_statuses() -> None:
    """The advertised schema must match the negotiated 3.0 wire shape too.

    Repointed for FINDINGS-schema.md R12: the advertisement comes from the
    document of record now rather than from ``model_json_schema()``, so
    ``status`` is read where ``core/protocol-envelope.json`` states it — once,
    reached through the root ``allOf``, governing every branch — instead of on
    the success branch, where only Pydantic's per-branch rendering put it.
    The accepted value set is unchanged, and it is checked here by validating
    a real negotiated-3.0 payload rather than by re-describing the shape.
    """
    jsonschema = pytest.importorskip("jsonschema")
    by_name = {t["name"]: t for t in ADCP_TOOL_DEFINITIONS}
    expected_statuses = {
        "active",
        "canceled",
        "completed",
        "paused",
        "pending_creatives",
        "pending_start",
        "rejected",
    }

    for tool_name in ("create_media_buy", "update_media_buy"):
        schema = by_name[tool_name]["outputSchema"]
        envelope = next(
            resolved
            for entry in schema["allOf"]
            if isinstance(resolved := _resolve(schema, entry), dict)
            and "status" in resolved.get("properties", {})
        )
        # The document requires ``status``; the widening adds the 3.0
        # lifecycle values beside the task-envelope ones, it does not
        # make the field optional.
        assert "status" in envelope["required"]
        advertised = set()
        for variant in envelope["properties"]["status"]["anyOf"]:
            advertised.update(_resolve(schema, variant).get("enum", ()))
        assert expected_statuses <= advertised

        # What the advertisement is for: a negotiated 3.0 buyer's success
        # payload has to validate against it.
        jsonschema.validate(
            {
                "adcp_version": "3.0",
                "status": "pending_creatives",
                "media_buy_id": "mb-1",
                "packages": [],
                "confirmed_at": "2026-01-01T00:00:00Z",
                "revision": 1,
            },
            schema,
        )


def test_new_brand_creative_tools_have_output_schema() -> None:
    """New beta 3 tools must advertise response schemas on tools/list too."""
    by_name = {t["name"]: t for t in ADCP_TOOL_DEFINITIONS}

    assert "properties" in by_name["validate_input"]["outputSchema"]
    assert "anyOf" in by_name["verify_brand_claim"]["outputSchema"]
    assert "properties" in by_name["verify_brand_claims"]["outputSchema"]


# ----------------------------------------------------------------------
# Wire-level: tools/list response
# ----------------------------------------------------------------------


class _StubHandler(ADCPHandler):
    """Minimal handler — we only need ``tools/list``, not actual tool calls."""


@pytest.fixture
async def mcp_client() -> Any:
    handler = _StubHandler()
    mcp = create_mcp_server(handler, name="test-output-schema", advertise_all=True)
    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    mcp.settings.transport_security.allowed_hosts = ["localhost", "127.0.0.1"]
    app = mcp.streamable_http_app()

    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://localhost",
            follow_redirects=True,
        ) as client:
            yield client


async def _initialize_session(client: httpx.AsyncClient) -> None:
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
    headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
    }
    resp = await client.post("/mcp/", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    # Stateful streamable-http binds subsequent requests to the
    # ``Mcp-Session-Id`` returned by ``initialize``. Persist it on the
    # client's default headers so ``tools/list`` and ``tools/call`` from
    # tests target the same session.
    session_id = resp.headers.get("mcp-session-id")
    if session_id is not None:
        client.headers["mcp-session-id"] = session_id


async def _list_tools(client: httpx.AsyncClient) -> dict[str, Any]:
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
    }
    resp = await client.post("/mcp/", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return _parse_event_stream(resp.text)


def _parse_event_stream(body: str) -> dict[str, Any]:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            return json.loads(line.removeprefix("data: "))
    return json.loads(body) if body.strip() else {}


@pytest.mark.asyncio
async def test_tools_list_response_includes_output_schema(mcp_client: Any) -> None:
    await _initialize_session(mcp_client)
    payload = await _list_tools(mcp_client)

    assert "result" in payload, payload
    tools = {t["name"]: t for t in payload["result"]["tools"]}

    for tool_name in _SAMPLE_TOOLS:
        assert tool_name in tools, f"{tool_name} not advertised"
        tool = tools[tool_name]
        assert "outputSchema" in tool, (
            f"tools/list did not advertise outputSchema for {tool_name} — "
            "JS parity regression on the wire"
        )
        assert tool["outputSchema"], f"{tool_name} outputSchema is empty on the wire"


@pytest.mark.asyncio
async def test_tools_list_input_and_output_schemas_are_distinct(mcp_client: Any) -> None:
    """Sanity: the request and response schemas describe different
    shapes. Catches a regression where outputSchema is mistakenly set
    to the inputSchema."""
    await _initialize_session(mcp_client)
    payload = await _list_tools(mcp_client)

    tools = {t["name"]: t for t in payload["result"]["tools"]}
    tool = tools["get_products"]

    assert tool["inputSchema"] != tool["outputSchema"]
