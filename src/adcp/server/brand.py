"""Brand rights handler for ADCP server implementations."""

from __future__ import annotations

from adcp.server.base import ADCPHandler


class BrandHandler(ADCPHandler):
    """Handler for brand rights operations.

    Subclass this to implement brand identity and rights management.
    Only brand rights tools will be exposed via MCP.

    Example:
        class MyBrandAgent(BrandHandler):
            async def get_brand_identity(self, params, context=None):
                # Implement brand identity lookup
                pass
    """

    _agent_type = "Brand agents"
