"""The override-based advertised-tools gate — closes #220.

Before #220, ``get_tools_for_handler`` returned every tool in the
handler-type's allowed set. A minimal seller agent that only overrode
``get_products`` still advertised all 57 tools in ``tools/list`` — 55
of them answering ``not_supported`` to every call. With Pydantic-
generated schemas averaging several hundred tokens each, that's a
significant context tax on every agent client that connects.

#220 adds an override filter: by default only tools whose method has
been overridden by the subclass are advertised. Spec-mandated discovery
tools (``get_adcp_capabilities``, anything in
:data:`~adcp.server.DISCOVERY_TOOLS`) are always advertised. Sellers
who want the old behavior — e.g. for spec-compliance storyboards that
exercise every tool — pass ``advertise_all=True``.

These tests lock the contract.
"""

from __future__ import annotations

from typing import Any

import pytest

from adcp.server import (
    ADCPHandler,
    GovernanceHandler,
    create_mcp_server,
)
from adcp.server.a2a_server import ADCPAgentExecutor
from adcp.server.mcp_tools import (
    ADCP_TOOL_DEFINITIONS,
    DISCOVERY_TOOLS,
    get_tools_for_handler,
)

# ---------------------------------------------------------------------------
# Override detection — the filter's core logic
# ---------------------------------------------------------------------------


def test_bare_adcphandler_subclass_advertises_only_discovery_tools():
    """A subclass that implements ``get_adcp_capabilities`` and nothing
    else should advertise just that + any auth-optional discovery
    tools. 1 tool advertised vs the 57 the pre-#220 default would have
    exposed."""

    class _Empty(ADCPHandler):
        _agent_type = "empty"

        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    tools = {t["name"] for t in get_tools_for_handler(_Empty())}
    assert tools == {"get_adcp_capabilities"} | DISCOVERY_TOOLS


def test_single_override_advertises_only_that_tool_plus_discovery():
    """One override = one advertised tool beyond discovery. This is the
    common minimal-agent case — and the reduction this PR is for."""

    class _Minimal(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

        async def get_products(self, params, context=None):
            return {"products": []}

    tools = {t["name"] for t in get_tools_for_handler(_Minimal())}
    assert tools == {"get_adcp_capabilities", "get_products"} | DISCOVERY_TOOLS


def test_multiple_overrides_advertise_every_override():
    """Handler that overrides N tools advertises exactly those N plus
    discovery."""

    class _Multi(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

        async def get_products(self, params, context=None):
            return {}

        async def create_media_buy(self, params, context=None):
            return {}

        async def sync_creatives(self, params, context=None):
            return {}

    expected = {
        "get_adcp_capabilities",
        "get_products",
        "create_media_buy",
        "sync_creatives",
    } | DISCOVERY_TOOLS
    tools = {t["name"] for t in get_tools_for_handler(_Multi())}
    assert tools == expected


def test_protocol_handler_subclass_advertises_only_implemented_protocol_tools():
    """A ``GovernanceHandler`` subclass that implements 2 out of the 15
    governance tools advertises only those 2 (plus discovery) — not all
    15. The handler-type filter and override filter intersect."""

    class _PartialGovernance(GovernanceHandler):
        _agent_type = "partial governance"

        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

        async def handle_get_property_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_list_property_lists(self, request: Any, context: Any = None) -> Any:
            return {}

        # Other abstract handle_* methods implemented as stubs so the
        # class is instantiable. They're not user-facing overrides of
        # the tool methods (``get_property_list`` etc.), so the gate
        # should NOT advertise them.
        async def handle_create_property_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_update_property_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_delete_property_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_create_collection_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_update_collection_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_delete_collection_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_get_collection_list(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_list_collection_lists(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_check_governance(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_report_plan_outcome(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_sync_plans(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_get_plan_audit_logs(self, request: Any, context: Any = None) -> Any:
            return {}

        async def handle_get_creative_features(self, request: Any, context: Any = None) -> Any:
            return {}

        async def get_property_list(self, params, context=None):
            return {}

        async def list_property_lists(self, params, context=None):
            return {}

    tools = {t["name"] for t in get_tools_for_handler(_PartialGovernance())}
    assert (
        tools
        == {
            "get_adcp_capabilities",
            "get_property_list",
            "list_property_lists",
        }
        | DISCOVERY_TOOLS
    )


# ---------------------------------------------------------------------------
# advertise_all escape hatch
# ---------------------------------------------------------------------------


def test_advertise_all_restores_pre_220_behavior():
    """``advertise_all=True`` returns the full handler-type tool set —
    including not_supported defaults. Needed for spec-compliance
    storyboard tests that exercise every tool."""

    class _Empty(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    default = {t["name"] for t in get_tools_for_handler(_Empty())}
    all_tools = {t["name"] for t in get_tools_for_handler(_Empty(), advertise_all=True)}

    # Default should be small; advertise_all should return everything
    # ADCPHandler's allowed set covers.
    assert default == {"get_adcp_capabilities"} | DISCOVERY_TOOLS
    assert len(all_tools) == len(ADCP_TOOL_DEFINITIONS)
    assert default.issubset(all_tools)


# ---------------------------------------------------------------------------
# create_mcp_server / create_a2a_server threading
# ---------------------------------------------------------------------------


def test_create_mcp_server_defaults_to_override_filter():
    """``create_mcp_server`` should register only overridden tools on
    the FastMCP instance."""

    class _Minimal(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

        async def get_products(self, params, context=None):
            return {"products": []}

    mcp = create_mcp_server(_Minimal(), name="test-agent")
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    assert tool_names == {"get_adcp_capabilities", "get_products"} | DISCOVERY_TOOLS


def test_create_mcp_server_advertise_all_restores_full_surface():
    """The escape hatch reaches through create_mcp_server."""

    class _Minimal(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    mcp = create_mcp_server(_Minimal(), name="test-agent", advertise_all=True)
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    # Full ADCP surface minus comply_test_controller (which is
    # gated behind include_test_controller=True).
    assert len(tool_names) >= 50


def test_adcp_agent_executor_defaults_to_override_filter():
    """The A2A executor's ``supported_skills`` mirrors the filtered list."""

    class _Minimal(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

        async def get_products(self, params, context=None):
            return {"products": []}

    executor = ADCPAgentExecutor(_Minimal())
    assert (
        set(executor.supported_skills)
        == {
            "get_adcp_capabilities",
            "get_products",
        }
        | DISCOVERY_TOOLS
    )


def test_adcp_agent_executor_advertise_all_restores_full_surface():
    """The escape hatch reaches through the A2A executor."""

    class _Minimal(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    executor = ADCPAgentExecutor(_Minimal(), advertise_all=True)
    # Same as create_mcp_server check — full surface, minus comply_test_controller.
    assert len(executor.supported_skills) >= 50


# ---------------------------------------------------------------------------
# Agent card reflects the filter
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    True,
    reason=(
        "Python 3.10 — a2a-sdk's agent-card builder imports the Starlette "
        "integration which needs 3.11+. The card-shape is covered by the "
        "test_a2a_server.py agent-card tests under the correct skipif."
    ),
)
def test_agent_card_uses_override_filter_by_default():  # pragma: no cover
    pass
