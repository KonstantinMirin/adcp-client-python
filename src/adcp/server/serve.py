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


def _bind_reusable_socket(host: str, port: int) -> Any:
    """Create a listening socket with SO_REUSEADDR set.

    Without ``SO_REUSEADDR``, rapid restarts (common during tests and
    storyboard runs) hit ``TIME_WAIT`` on the prior socket and the new
    process hangs on bind for up to 2×MSL (roughly a minute on macOS).
    Setting ``SO_REUSEADDR`` on the listening socket is the standard,
    portable fix on Linux and macOS; it is safe because listeners are
    unique by (addr, port) and the kernel still rejects a second live
    listener on the same tuple.

    On Windows ``SO_REUSEADDR`` has different semantics (it allows
    hijacking a live listener). FastMCP's streamable-http and uvicorn
    support Windows, so we guard with ``SO_EXCLUSIVEADDRUSE`` there —
    but since the ADCP server primarily targets Linux/macOS and the
    Windows path is rarely exercised, the guard is best-effort.
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name == "nt":
            # Windows: prevent hijacking; don't set SO_REUSEADDR.
            exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if exclusive is not None:
                sock.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(128)
        sock.set_inheritable(True)
    except Exception:
        sock.close()
        raise
    return sock


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
    mcp = create_mcp_server(
        handler,
        name=name,
        port=port,
        instructions=instructions,
        include_test_controller=test_controller is not None,
    )

    if test_controller is not None:
        from adcp.server.test_controller import register_test_controller

        register_test_controller(mcp, test_controller)

    if transport in ("streamable-http", "sse"):
        _run_mcp_http(mcp, transport=transport)
    else:
        # stdio — no listening socket, nothing to configure.
        mcp.run(transport=transport)


def _run_mcp_http(mcp: Any, *, transport: str) -> None:
    """Run FastMCP's HTTP transports with a pre-bound SO_REUSEADDR socket.

    FastMCP builds its own ``uvicorn.Server(config).serve()`` inside
    ``run_*_async`` and does not expose hooks to pass a pre-bound socket,
    so we reproduce the minimal setup here and hand uvicorn the socket
    directly via ``Server.serve([sock])``. This keeps the public surface
    (``serve()``) unchanged while fixing the readiness-flake on reruns.
    """
    import anyio
    import uvicorn

    host = getattr(mcp.settings, "host", "0.0.0.0")
    port = int(mcp.settings.port)
    log_level = getattr(mcp.settings, "log_level", "INFO").lower()

    if transport == "streamable-http":
        app = mcp.streamable_http_app()
    else:
        app = mcp.sse_app()

    sock = _bind_reusable_socket(host, port)
    try:
        config = uvicorn.Config(app, log_level=log_level)
        server = uvicorn.Server(config)

        async def _serve() -> None:
            await server.serve(sockets=[sock])

        anyio.run(_serve)
    finally:
        sock.close()


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

    app = create_a2a_server(handler, name=name, port=resolved_port, test_controller=test_controller)
    sock = _bind_reusable_socket("0.0.0.0", resolved_port)
    try:
        config = uvicorn.Config(app)
        server = uvicorn.Server(config)
        import anyio

        async def _serve() -> None:
            await server.serve(sockets=[sock])

        anyio.run(_serve)
    finally:
        sock.close()


def create_mcp_server(
    handler: ADCPHandler,
    *,
    name: str = "adcp-agent",
    port: int | None = None,
    instructions: str | None = None,
    include_test_controller: bool = False,
) -> Any:
    """Create a FastMCP server from an ADCP handler without starting it.

    Use this when you need to customize the server before running it,
    or when you need to add extra non-ADCP tools.

    Args:
        handler: An ADCPHandler subclass instance.
        name: Server name.
        port: Port to listen on.
        instructions: Optional system instructions.
        include_test_controller: When False (default), skip registering
            ``comply_test_controller`` as a handler tool. Sellers who want
            compliance-testing support should pass ``test_controller=`` to
            :func:`serve`, which registers a store-backed implementation
            via :func:`register_test_controller` and sets this flag
            implicitly. Registering the handler stub unconditionally would
            advertise a tool the seller didn't opt into.

    Returns:
        A configured FastMCP server instance. Call mcp.run() to start.

    Example:
        mcp = create_mcp_server(MyAgent(), name="my-agent")
        mcp.run(transport="streamable-http")
    """
    from mcp.server.fastmcp import FastMCP

    resolved_port = port or int(os.environ.get("PORT", "3001"))
    mcp = FastMCP(name, instructions=instructions, port=resolved_port)
    _register_handler_tools(mcp, handler, include_test_controller=include_test_controller)
    return mcp


def _register_handler_tools(
    mcp: Any, handler: ADCPHandler, *, include_test_controller: bool = False
) -> None:
    """Register all ADCP tools from a handler onto a FastMCP server."""
    tool_defs = get_tools_for_handler(handler)
    for tool_def in tool_defs:
        tool_name = tool_def["name"]
        # Gate comply_test_controller on explicit opt-in. The handler base
        # class has a not-supported stub; registering it as an MCP tool
        # would advertise compliance-testing the seller didn't declare.
        if tool_name == "comply_test_controller" and not include_test_controller:
            continue
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {"type": "object", "properties": {}})
        caller = create_tool_caller(handler, tool_name)
        _register_tool(mcp, tool_name, description, input_schema, caller)


def _register_tool(
    mcp: Any,
    name: str,
    description: str,
    input_schema: dict[str, Any],
    caller: Callable[..., Any],
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
        # Note on caller identity: FastMCP does not expose an authenticated
        # principal to tool handlers at the SDK level — ``Context.client_id``
        # is a session hint, not an authenticated user identifier. Sellers
        # who need per-principal server middleware (e.g. the idempotency
        # store's per-principal scoping) should wire their own FastMCP auth
        # middleware and either pre-populate ``params`` with a principal
        # hint their handler reads, or override ``create_tool_caller`` to
        # build a ToolContext from their auth layer. The A2A transport
        # derives caller_identity from ServerCallContext.user automatically.
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
