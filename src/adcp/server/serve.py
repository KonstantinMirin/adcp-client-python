"""One-liner server for ADCP handlers (MCP or A2A).

Stand up an ADCP-compliant server with a single function call:

    from adcp.server import ADCPHandler, serve
    from adcp.server.responses import capabilities_response

    class MyAgent(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return capabilities_response(["media_buy"])

    # MCP (default)
    serve(MyAgent())

    # A2A
    serve(MyAgent(), transport="a2a")
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from adcp.server.base import ADCPHandler
from adcp.server.mcp_tools import create_tool_caller, get_tools_for_handler

if TYPE_CHECKING:
    from adcp.server.test_controller import TestControllerStore


def serve(
    handler: ADCPHandler | Any,
    *,
    name: str = "adcp-agent",
    port: int | None = None,
    mount: str = "/mcp",
    transport: str = "streamable-http",
    instructions: str | None = None,
    test_controller: TestControllerStore | None = None,
) -> None:
    """Start an MCP or A2A server from an ADCP handler or server builder.

    Accepts either an ``ADCPHandler`` instance or an ``ADCPServerBuilder``
    (from ``adcp_server()``). Builders are auto-converted via ``build_handler()``.

    This is the simplest way to run an ADCP agent. Set ``transport="a2a"``
    to serve over the A2A protocol instead of MCP.

    Args:
        handler: An ADCPHandler subclass instance with your tool implementations.
        name: Server name shown to clients / in the A2A agent card.
        port: Port to listen on. Defaults to PORT env var, then 3001.
        mount: URL path to mount MCP endpoint on (MCP only).
        transport: ``"streamable-http"`` (default, MCP) or ``"a2a"``.
        instructions: Optional system instructions for the agent (MCP only).
        test_controller: Optional TestControllerStore instance for storyboard testing.

    Security:
        This function does NOT configure authentication. In production,
        use a reverse proxy or middleware that validates credentials
        before forwarding to the endpoint. Without authentication,
        MCP exposes tools/list and A2A exposes /.well-known/agent.json,
        both of which reveal the agent's full capability surface.

    Example (MCP):
        from adcp.server import ADCPHandler, serve
        from adcp.server.responses import capabilities_response

        class MyAgent(ADCPHandler):
            async def get_adcp_capabilities(self, params, context=None):
                return capabilities_response(["media_buy"])

        serve(MyAgent(), name="my-agent")

    Example (A2A):
        serve(MyAgent(), name="my-agent", transport="a2a")

    With test controller:
        from adcp.server.test_controller import TestControllerStore

        class MyStore(TestControllerStore):
            async def force_account_status(self, account_id, status):
                ...

        serve(MyAgent(), name="my-agent", test_controller=MyStore())
    """
    # Accept ADCPServerBuilder from adcp_server() decorator pattern
    from adcp.server.builder import ADCPServerBuilder

    if isinstance(handler, ADCPServerBuilder):
        if not name or name == "adcp-agent":
            name = handler.name
        handler = handler.build_handler()

    if transport == "a2a":
        _serve_a2a(handler, name=name, port=port, test_controller=test_controller)
    elif transport in ("streamable-http", "sse", "stdio"):
        _serve_mcp(
            handler,
            name=name,
            port=port,
            transport=transport,
            instructions=instructions,
            test_controller=test_controller,
        )
    else:
        valid = ", ".join(sorted(("a2a", "streamable-http", "sse", "stdio")))
        raise ValueError(f"Unknown transport {transport!r}. Valid: {valid}")


def _serve_mcp(
    handler: ADCPHandler,
    *,
    name: str,
    port: int | None,
    transport: str,
    instructions: str | None,
    test_controller: TestControllerStore | None,
) -> None:
    """Start an MCP server."""
    mcp = create_mcp_server(handler, name=name, port=port, instructions=instructions)

    if test_controller is not None:
        from adcp.server.test_controller import register_test_controller

        register_test_controller(mcp, test_controller)

    mcp.run(transport=transport)


def _serve_a2a(
    handler: ADCPHandler,
    *,
    name: str,
    port: int | None,
    test_controller: TestControllerStore | None,
) -> None:
    """Start an A2A server using uvicorn."""
    import uvicorn

    from adcp.server.a2a_server import create_a2a_server

    resolved_port = port or int(os.environ.get("PORT", "3001"))

    app = create_a2a_server(
        handler, name=name, port=resolved_port, test_controller=test_controller
    )
    uvicorn.run(app, host="0.0.0.0", port=resolved_port)


def create_mcp_server(
    handler: ADCPHandler,
    *,
    name: str = "adcp-agent",
    port: int | None = None,
    instructions: str | None = None,
) -> Any:
    """Create a FastMCP server from an ADCP handler without starting it.

    Use this when you need to customize the server before running it,
    or when you need to add extra non-ADCP tools.

    Args:
        handler: An ADCPHandler subclass instance.
        name: Server name.
        port: Port to listen on.
        instructions: Optional system instructions.

    Returns:
        A configured FastMCP server instance. Call mcp.run() to start.

    Example:
        mcp = create_mcp_server(MyAgent(), name="my-agent")
        mcp.run(transport="streamable-http")
    """
    from mcp.server.fastmcp import FastMCP

    resolved_port = port or int(os.environ.get("PORT", "3001"))
    mcp = FastMCP(name, instructions=instructions, port=resolved_port)
    _register_handler_tools(mcp, handler)
    return mcp


def _register_handler_tools(mcp: Any, handler: ADCPHandler) -> None:
    """Register all ADCP tools from a handler onto a FastMCP server."""
    tool_defs = get_tools_for_handler(handler)
    for tool_def in tool_defs:
        tool_name = tool_def["name"]
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {"type": "object", "properties": {}})
        caller = create_tool_caller(handler, tool_name)
        _register_tool(mcp, tool_name, description, input_schema, caller)


def _register_tool(
    mcp: Any,
    name: str,
    description: str,
    input_schema: dict[str, Any],
    caller: Callable[[dict[str, Any]], Any],
) -> None:
    """Register a single ADCP tool on a FastMCP server.

    Creates a Tool with a permissive arg model that accepts any fields,
    then overrides the advertised schema with the Pydantic-generated one.
    This ensures MCP clients see the correct schema while the handler
    receives all parameters as a plain dict.
    """
    from mcp.server.fastmcp.tools import Tool
    from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
    from pydantic import ConfigDict

    from adcp.exceptions import ADCPError
    from adcp.server.translate import translate_error

    async def fn(**kwargs: Any) -> dict[str, Any]:
        try:
            result = await caller(kwargs)
        except ADCPError as exc:
            # Translate AdCP-typed exceptions (IdempotencyConflictError,
            # ADCPTaskError with a spec code, etc.) into a ToolError so FastMCP
            # surfaces ``is_error=true`` with the spec error code in the
            # message text. Clients per AdCP §transport-errors will extract
            # the code via either structuredContent.adcp_error (if populated)
            # or the text-fallback path.
            raise translate_error(exc, protocol="mcp") from exc
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json", exclude_none=True)  # type: ignore[no-any-return]
        if isinstance(result, dict):
            return result
        return {"result": result}

    # Create tool from function (gives us proper fn_metadata scaffolding)
    tool = Tool.from_function(fn, name=name, description=description, structured_output=True)

    # Override the advertised schema with the Pydantic-generated one
    tool.parameters = input_schema

    # Override fn_metadata with a permissive model that passes through
    # all fields as individual kwargs (instead of wrapping in a "kwargs" field).
    # Keep the output_schema/output_model so structuredContent is populated.
    class _AdcpArgs(ArgModelBase):
        model_config = ConfigDict(extra="allow")

        def model_dump_one_level(self) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for field_name in self.__class__.model_fields:
                result[field_name] = getattr(self, field_name)
            if self.model_extra:
                result.update(self.model_extra)
            return result

    tool.fn_metadata = FuncMetadata(
        arg_model=_AdcpArgs,
        output_schema=tool.fn_metadata.output_schema,
        output_model=tool.fn_metadata.output_model,
        wrap_output=False,
    )

    # FastMCP does not expose a public API for registering pre-built Tool
    # objects with custom schemas. This accesses internals; requires mcp>=1.23.
    mcp._tool_manager._tools[name] = tool
