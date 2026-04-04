"""Compliance test controller handler for ADCP server implementations."""

from __future__ import annotations

from adcp.server.base import ADCPHandler


class ComplianceHandler(ADCPHandler):
    """Handler for compliance test operations.

    Subclass this to implement compliance sandbox testing.
    Only compliance tools will be exposed via MCP.

    Example:
        class MyComplianceAgent(ComplianceHandler):
            async def comply_test_controller(self, params, context=None):
                # Implement test controller
                pass
    """

    _agent_type = "Compliance agents"
