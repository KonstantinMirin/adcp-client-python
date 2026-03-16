"""Spec coverage tests for SDK surface area.

These tests ensure the schema index and the SDK's public task surfaces stay aligned.
"""

from __future__ import annotations

import json
from pathlib import Path


def _schema_task_names() -> set[str]:
    index_path = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "index.json"
    index_data = json.loads(index_path.read_text())

    task_names: set[str] = set()
    for schema_group in index_data.get("schemas", {}).values():
        tasks = schema_group.get("tasks") if isinstance(schema_group, dict) else None
        if isinstance(tasks, dict):
            task_names.update(name.replace("-", "_") for name in tasks)

    return task_names


def test_client_methods_cover_schema_index():
    """ADCPClient exposes every schema task as a method."""
    from adcp.client import ADCPClient

    missing = sorted(name for name in _schema_task_names() if not hasattr(ADCPClient, name))
    assert missing == []


def test_handler_methods_cover_schema_index():
    """ADCPHandler provides a default stub for every schema task."""
    from adcp.server import ADCPHandler

    missing = sorted(name for name in _schema_task_names() if not hasattr(ADCPHandler, name))
    assert missing == []


def test_protocol_adapters_cover_schema_index():
    """Concrete protocol adapters implement every schema task wrapper."""
    from adcp.protocols.a2a import A2AAdapter
    from adcp.protocols.mcp import MCPAdapter

    task_names = _schema_task_names()
    mcp_missing = sorted(name for name in task_names if not hasattr(MCPAdapter, name))
    a2a_missing = sorted(name for name in task_names if not hasattr(A2AAdapter, name))

    assert mcp_missing == []
    assert a2a_missing == []


def test_cli_dispatch_covers_schema_index():
    """CLI dispatch table covers every schema task."""
    from adcp.__main__ import _get_dispatch_table

    dispatch_table = _get_dispatch_table()
    missing = sorted(name for name in _schema_task_names() if name not in dispatch_table)
    assert missing == []


def test_mcp_tool_definitions_cover_schema_index():
    """MCP tool definitions cover every schema task."""
    from adcp.server.mcp_tools import ADCP_TOOL_DEFINITIONS

    tool_names = {tool["name"] for tool in ADCP_TOOL_DEFINITIONS}
    missing = sorted(name for name in _schema_task_names() if name not in tool_names)
    assert missing == []
