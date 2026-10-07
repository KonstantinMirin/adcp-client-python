"""Public HTTP policy configuration for MCP and A2A deployments."""

from adcp.server import (
    ADCPHandler,
    ServeConfig,
    ToolContext,
    create_a2a_server,
    create_mcp_server,
    serve,
)


def configure(handler: ADCPHandler[ToolContext]) -> None:
    config = ServeConfig(
        transport="both",
        allowed_hosts=["seller.example"],
        allowed_origins=["https://buyer.example"],
        enable_dns_rebinding_protection=False,
        supported_versions=["3.2"],
    )
    create_a2a_server(
        handler,
        allowed_hosts=config.allowed_hosts,
        allowed_origins=config.allowed_origins,
        enable_dns_rebinding_protection=False,
        supported_versions=config.supported_versions,
    )
    create_mcp_server(
        handler,
        allowed_hosts=config.allowed_hosts,
        allowed_origins=config.allowed_origins,
        supported_versions=config.supported_versions,
    )
    serve(handler, config=config)
