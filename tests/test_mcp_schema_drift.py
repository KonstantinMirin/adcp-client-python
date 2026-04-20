"""Drift tests for MCP tool inputSchema generation.

The MCP tool registry exposes ``inputSchema`` for every ADCP tool via
``tools/list``. These schemas are auto-generated from the corresponding
Pydantic request models in ``adcp.types`` at import time
(:func:`adcp.server.mcp_tools._generate_pydantic_schemas`).

This module protects the generation path from regressions:

1. Every tool must resolve to a Pydantic-generated schema. If a new tool
   is added to ``ADCP_TOOL_DEFINITIONS`` without a mapping in
   ``_tool_to_request``, the tool would silently ship a hand-crafted
   stub schema again — the drift this whole mechanism exists to prevent.
2. Each tool's ``inputSchema`` must match the ``model_json_schema()``
   output of its request model (modulo the ``title`` strip and the
   conditional ``$defs`` drop). If Pydantic changes its schema output,
   or a model gains/drops a field, this test fails on the affected tool.
3. The schema must advertise the model's required fields so agents
   constructing payloads via ``tools/list`` see accurate constraints.
"""

from __future__ import annotations

import json

from adcp.server.mcp_tools import (
    _PYDANTIC_SCHEMAS,
    ADCP_TOOL_DEFINITIONS,
    _generate_pydantic_schemas,
)


def test_every_tool_has_pydantic_generated_schema() -> None:
    """Every ADCP tool must map to a Pydantic request model."""
    tool_names = {t["name"] for t in ADCP_TOOL_DEFINITIONS}
    missing = tool_names - set(_PYDANTIC_SCHEMAS.keys())
    assert not missing, (
        "Tools missing from Pydantic schema generator — they would ship "
        "stub inputSchemas that drift from the real request model:\n"
        + "\n".join(f"  - {name}" for name in sorted(missing))
        + "\n\nAdd each tool to ``_tool_to_request`` in "
        "``adcp/server/mcp_tools.py``, mapped to its ``<ToolName>Request`` model."
    )


def test_input_schemas_match_pydantic_generation() -> None:
    """tools/list schemas must byte-match fresh generation — no silent drift."""
    fresh = _generate_pydantic_schemas()
    mismatches: list[str] = []
    for tool in ADCP_TOOL_DEFINITIONS:
        name = tool["name"]
        if name not in fresh:
            continue
        expected = fresh[name]
        actual = tool["inputSchema"]
        if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
            mismatches.append(name)

    assert not mismatches, (
        "ADCP_TOOL_DEFINITIONS has stale inputSchemas — "
        "`_apply_pydantic_schemas()` must run at import time:\n"
        + "\n".join(f"  - {name}" for name in mismatches)
    )


def test_required_fields_advertised() -> None:
    """Required fields on each model must appear in the tool's inputSchema.

    Agents building payloads from ``tools/list`` rely on the ``required``
    array to know which fields cannot be omitted. If a model marks a
    field as required but the advertised schema doesn't, the agent will
    happily send a malformed request.
    """
    from pydantic import TypeAdapter

    from adcp.types import (
        AcquireRightsRequest,
        BuildCreativeRequest,
        CheckGovernanceRequest,
        ContextMatchRequest,
        CreateMediaBuyRequest,
        GetProductsRequest,
        IdentityMatchRequest,
        ReportPlanOutcomeRequest,
        SyncGovernanceRequest,
        UpdateRightsRequest,
    )

    # Spot-check a representative slice: a mix of simple GETs, mutating
    # writes, and schemas that include nested $refs. If the required
    # fields drift for any of these, the rest probably drifted too.
    checks = {
        "get_products": GetProductsRequest,
        "build_creative": BuildCreativeRequest,
        "create_media_buy": CreateMediaBuyRequest,
        "check_governance": CheckGovernanceRequest,
        "report_plan_outcome": ReportPlanOutcomeRequest,
        "acquire_rights": AcquireRightsRequest,
        "update_rights": UpdateRightsRequest,
        "sync_governance": SyncGovernanceRequest,
        "context_match": ContextMatchRequest,
        "identity_match": IdentityMatchRequest,
    }

    tool_schemas = {t["name"]: t["inputSchema"] for t in ADCP_TOOL_DEFINITIONS}
    errors: list[str] = []

    for tool_name, model in checks.items():
        expected_required = set(TypeAdapter(model).json_schema().get("required", []))
        advertised_required = set(tool_schemas[tool_name].get("required", []))
        missing = expected_required - advertised_required
        if missing:
            errors.append(
                f"{tool_name}: model requires {sorted(missing)} " f"but inputSchema does not"
            )

    assert not errors, "Required-field drift:\n" + "\n".join(errors)


def test_spot_check_real_fields_reach_clients() -> None:
    """The three tools that previously had the worst drift must now
    advertise the real required fields from their request models.
    """
    tool_schemas = {t["name"]: t["inputSchema"] for t in ADCP_TOOL_DEFINITIONS}

    get_products = tool_schemas["get_products"]
    assert "brief" in get_products["properties"]
    assert "buying_mode" in get_products["properties"]
    assert "buying_mode" in get_products.get("required", [])

    build_creative = tool_schemas["build_creative"]
    assert "target_format_id" in build_creative["properties"]
    assert "creative_manifest" in build_creative["properties"]
    assert "idempotency_key" in build_creative.get("required", [])

    create_media_buy = tool_schemas["create_media_buy"]
    for field in ("account", "brand", "start_time", "end_time", "packages"):
        assert field in create_media_buy["properties"], f"create_media_buy missing field {field!r}"
    for req in ("account", "brand", "start_time", "end_time", "idempotency_key"):
        assert req in create_media_buy.get(
            "required", []
        ), f"create_media_buy should require {req!r}"
