"""TMP (Temporal Matching Protocol) handler for ADCP server implementations."""

from __future__ import annotations

from adcp.server.base import ADCPHandler


class TmpHandler(ADCPHandler):
    """Handler for Temporal Matching Protocol operations.

    Subclass this to implement context matching and identity matching.
    Only TMP tools will be exposed via MCP.

    Example:
        class MyTmpAgent(TmpHandler):
            async def context_match(self, params, context=None):
                # Evaluate context signals against buyer packages
                pass

            async def identity_match(self, params, context=None):
                # Evaluate user identity for package eligibility
                pass
    """

    _agent_type = "TMP agents"
