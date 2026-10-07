"""Typed served-version selection on handler and platform composition APIs."""

from collections.abc import Sequence

from adcp.decisioning import DecisioningPlatform, create_adcp_server_from_platform
from adcp.decisioning import serve as serve_platform
from adcp.server import (
    ADCPHandler,
    ServeConfig,
    ToolContext,
    create_a2a_server,
    create_mcp_server,
    serve,
)
from adcp.server.a2a_server import ADCPAgentExecutor
from adcp.server.mcp_tools import MCPToolSet, create_mcp_tools, create_tool_caller
from adcp.testing import build_asgi_app, build_test_client


def compose(handler: ADCPHandler[ToolContext], platform: DecisioningPlatform) -> None:
    selected: Sequence[str] = ("3.2", "3.2-rc.7")
    config = ServeConfig(supported_versions=selected)
    create_mcp_server(handler, supported_versions=selected)
    create_a2a_server(handler, supported_versions=selected)
    create_tool_caller(handler, "get_products", supported_versions=selected)
    create_mcp_tools(handler, supported_versions=selected)
    MCPToolSet(handler, supported_versions=selected)
    ADCPAgentExecutor(handler, supported_versions=selected)
    serve(handler, config=config)
    _, executor, _ = create_adcp_server_from_platform(platform, supported_versions=selected)
    executor.shutdown(wait=True)
    serve_platform(platform, supported_versions=selected)
    build_asgi_app(platform, supported_versions=selected)


async def connect(platform: DecisioningPlatform) -> None:
    async with build_test_client(platform, supported_versions=("3.2",)) as client:
        await client.get("/.well-known/agent-card.json")
