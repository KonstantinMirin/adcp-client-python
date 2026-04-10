"""ADCP Server Framework.

The simplest way to build an AdCP agent:

    from adcp.server import ADCPHandler, serve
    from adcp.server.responses import capabilities_response, products_response

    class MySeller(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return capabilities_response(["media_buy"])

        async def get_products(self, params, context=None):
            return products_response(MY_PRODUCTS)

    serve(MySeller(), name="my-seller")
"""

from __future__ import annotations

from adcp.capabilities import validate_capabilities
from adcp.server.base import (
    ADCPHandler,
    NotImplementedResponse,
    ToolContext,
    not_supported,
)
from adcp.server.brand import BrandHandler
from adcp.server.compliance import ComplianceHandler
from adcp.server.content_standards import ContentStandardsHandler
from adcp.server.governance import GovernanceHandler
from adcp.server.mcp_tools import MCPToolSet, create_mcp_tools, get_tools_for_handler
from adcp.server.proposal import ProposalBuilder, ProposalNotSupported
from adcp.server.responses import (
    activate_signal_response,
    build_creative_response,
    capabilities_response,
    creative_formats_response,
    delivery_response,
    error_response,
    list_creatives_response,
    log_event_response,
    media_buy_error_response,
    media_buy_response,
    media_buys_response,
    preview_creative_response,
    products_response,
    signals_response,
    sync_accounts_response,
    sync_catalogs_response,
    sync_creatives_response,
    sync_governance_response,
    update_media_buy_response,
)
from adcp.server.serve import create_mcp_server, serve
from adcp.server.sponsored_intelligence import SponsoredIntelligenceHandler
from adcp.server.test_controller import (
    TestControllerError,
    TestControllerStore,
    register_test_controller,
)
from adcp.server.tmp import TmpHandler

__all__ = [
    # Base classes
    "ADCPHandler",
    "BrandHandler",
    "ComplianceHandler",
    "TmpHandler",
    "ToolContext",
    "NotImplementedResponse",
    "not_supported",
    # Capability validation
    "validate_capabilities",
    # Protocol handlers
    "ContentStandardsHandler",
    "GovernanceHandler",
    "SponsoredIntelligenceHandler",
    # Proposal helpers
    "ProposalBuilder",
    "ProposalNotSupported",
    # MCP integration
    "MCPToolSet",
    "create_mcp_tools",
    "create_mcp_server",
    "get_tools_for_handler",
    "serve",
    # Test controller
    "TestControllerStore",
    "TestControllerError",
    "register_test_controller",
    # Response builders
    "activate_signal_response",
    "build_creative_response",
    "capabilities_response",
    "creative_formats_response",
    "delivery_response",
    "error_response",
    "list_creatives_response",
    "log_event_response",
    "media_buy_error_response",
    "media_buy_response",
    "media_buys_response",
    "preview_creative_response",
    "products_response",
    "signals_response",
    "sync_accounts_response",
    "sync_catalogs_response",
    "sync_creatives_response",
    "sync_governance_response",
    "update_media_buy_response",
]
