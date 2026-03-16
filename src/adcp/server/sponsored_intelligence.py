"""Sponsored Intelligence protocol handler.

Provides a base class for implementing Sponsored Intelligence agents.
Non-SI operations return 'not supported' via the base class.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import ValidationError

from adcp.server.base import ADCPHandler, NotImplementedResponse, ToolContext
from adcp.types import (
    Error,
    SiGetOfferingRequest,
    SiGetOfferingResponse,
    SiInitiateSessionRequest,
    SiInitiateSessionResponse,
    SiSendMessageRequest,
    SiSendMessageResponse,
    SiTerminateSessionRequest,
    SiTerminateSessionResponse,
)


class SponsoredIntelligenceHandler(ADCPHandler):
    """Handler for Sponsored Intelligence protocol.

    Subclass this to implement a Sponsored Intelligence agent. All SI
    operations must be implemented via the handle_* methods.
    The public methods (si_get_offering, etc.) handle validation and
    error handling automatically.

    Non-SI operations (get_products, create_media_buy, content standards, etc.)
    return 'not supported' via the base class.

    Example:
        class MySIHandler(SponsoredIntelligenceHandler):
            async def handle_si_get_offering(
                self,
                request: SiGetOfferingRequest,
                context: ToolContext | None = None
            ) -> SiGetOfferingResponse:
                # Your implementation
                return SiGetOfferingResponse(...)
    """

    _agent_type: str = "Sponsored Intelligence agents"

    # ========================================================================
    # Sponsored Intelligence Operations - Override base class with validation
    # ========================================================================

    async def si_get_offering(
        self,
        params: dict[str, Any],
        context: ToolContext | None = None,
    ) -> SiGetOfferingResponse | NotImplementedResponse:
        """Get sponsored intelligence offering.

        Validates params and delegates to handle_si_get_offering.
        """
        try:
            request = SiGetOfferingRequest.model_validate(params)
        except ValidationError as e:
            return NotImplementedResponse(
                supported=False,
                reason=f"Invalid request: {e}",
                error=Error(code="VALIDATION_ERROR", message=str(e)),
            )
        return await self.handle_si_get_offering(request, context)

    async def si_initiate_session(
        self,
        params: dict[str, Any],
        context: ToolContext | None = None,
    ) -> SiInitiateSessionResponse | NotImplementedResponse:
        """Initiate sponsored intelligence session.

        Validates params and delegates to handle_si_initiate_session.
        """
        try:
            request = SiInitiateSessionRequest.model_validate(params)
        except ValidationError as e:
            return NotImplementedResponse(
                supported=False,
                reason=f"Invalid request: {e}",
                error=Error(code="VALIDATION_ERROR", message=str(e)),
            )
        return await self.handle_si_initiate_session(request, context)

    async def si_send_message(
        self,
        params: dict[str, Any],
        context: ToolContext | None = None,
    ) -> SiSendMessageResponse | NotImplementedResponse:
        """Send message in sponsored intelligence session.

        Validates params and delegates to handle_si_send_message.
        """
        try:
            request = SiSendMessageRequest.model_validate(params)
        except ValidationError as e:
            return NotImplementedResponse(
                supported=False,
                reason=f"Invalid request: {e}",
                error=Error(code="VALIDATION_ERROR", message=str(e)),
            )
        return await self.handle_si_send_message(request, context)

    async def si_terminate_session(
        self,
        params: dict[str, Any],
        context: ToolContext | None = None,
    ) -> SiTerminateSessionResponse | NotImplementedResponse:
        """Terminate sponsored intelligence session.

        Validates params and delegates to handle_si_terminate_session.
        """
        try:
            request = SiTerminateSessionRequest.model_validate(params)
        except ValidationError as e:
            return NotImplementedResponse(
                supported=False,
                reason=f"Invalid request: {e}",
                error=Error(code="VALIDATION_ERROR", message=str(e)),
            )
        return await self.handle_si_terminate_session(request, context)

    # ========================================================================
    # Abstract handlers - Implement these in subclasses
    # ========================================================================

    @abstractmethod
    async def handle_si_get_offering(
        self,
        request: SiGetOfferingRequest,
        context: ToolContext | None = None,
    ) -> SiGetOfferingResponse:
        """Handle get offering request."""
        ...

    @abstractmethod
    async def handle_si_initiate_session(
        self,
        request: SiInitiateSessionRequest,
        context: ToolContext | None = None,
    ) -> SiInitiateSessionResponse:
        """Handle initiate session request."""
        ...

    @abstractmethod
    async def handle_si_send_message(
        self,
        request: SiSendMessageRequest,
        context: ToolContext | None = None,
    ) -> SiSendMessageResponse:
        """Handle send message request."""
        ...

    @abstractmethod
    async def handle_si_terminate_session(
        self,
        request: SiTerminateSessionRequest,
        context: ToolContext | None = None,
    ) -> SiTerminateSessionResponse:
        """Handle terminate session request."""
        ...
