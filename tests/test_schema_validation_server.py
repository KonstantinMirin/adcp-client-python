"""Server-middleware integration tests for schema-driven validation (issue #249).

Exercises the opt-in request/response validator on ``create_tool_caller``
against real handlers, using the MCP-facing dispatcher shape.
"""

from __future__ import annotations

from typing import Any

import pytest

from adcp.exceptions import ADCPTaskError
from adcp.server.base import ADCPHandler, ToolContext
from adcp.server.mcp_tools import create_tool_caller
from adcp.validation import ValidationHookConfig


class _StubHandler(ADCPHandler[Any]):
    """Minimal handler that records whether it was invoked and returns the
    payload supplied in the constructor."""

    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response
        self.called = False

    async def get_products(self, params: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        self.called = True
        return dict(self._response)


VALID_GET_PRODUCTS = {
    "brief": "test campaign",
    "promoted_offering": "shoes",
    "buying_mode": "brief",
}


class TestRequestsStrict:
    @pytest.mark.asyncio
    async def test_rejects_malformed_with_validation_error_before_dispatch(
        self,
    ) -> None:
        handler = _StubHandler({"products": []})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(requests="strict"),
        )
        with pytest.raises(ADCPTaskError) as info:
            await caller({})
        assert handler.called is False
        first = info.value.errors[0]
        assert first.code == "VALIDATION_ERROR"
        assert first.field, "expected field pointer on error"
        assert first.details
        assert first.details["side"] == "request"

    @pytest.mark.asyncio
    async def test_accepts_valid_requests(self) -> None:
        handler = _StubHandler({"products": []})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(requests="strict"),
        )
        result = await caller(dict(VALID_GET_PRODUCTS))
        assert isinstance(result["products"], list)


class TestRequestsWarn:
    @pytest.mark.asyncio
    async def test_logs_warning_but_dispatches(self, caplog: pytest.LogCaptureFixture) -> None:
        handler = _StubHandler({"products": []})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(requests="warn"),
        )
        with caplog.at_level("WARNING", logger="adcp.server.mcp_tools"):
            await caller({})
        assert handler.called is True
        messages = [r.message for r in caplog.records]
        assert any(
            "Schema validation warning (request) for get_products" in m for m in messages
        ), f"no warning log: {messages}"


class TestNoValidationConfig:
    @pytest.mark.asyncio
    async def test_unconfigured_does_not_validate(self) -> None:
        handler = _StubHandler({"products": []})
        caller = create_tool_caller(handler, "get_products")
        await caller({})
        assert handler.called is True


class TestResponses:
    @pytest.mark.asyncio
    async def test_strict_drift_surfaces_validation_error(self) -> None:
        handler = _StubHandler({"products": "oops"})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(responses="strict"),
        )
        with pytest.raises(ADCPTaskError) as info:
            await caller(dict(VALID_GET_PRODUCTS))
        first = info.value.errors[0]
        assert first.code == "VALIDATION_ERROR"
        assert first.details["side"] == "response"

    @pytest.mark.asyncio
    async def test_warn_logs_but_returns_response_unchanged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        handler = _StubHandler({"products": "oops"})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(responses="warn"),
        )
        with caplog.at_level("WARNING", logger="adcp.server.mcp_tools"):
            result = await caller(dict(VALID_GET_PRODUCTS))
        assert result["products"] == "oops"
        messages = [r.message for r in caplog.records]
        assert any(
            "Schema validation warning (response) for get_products" in m for m in messages
        ), f"no warning log: {messages}"

    @pytest.mark.asyncio
    async def test_valid_response_passes_strict(self) -> None:
        handler = _StubHandler({"products": []})
        caller = create_tool_caller(
            handler,
            "get_products",
            validation=ValidationHookConfig(responses="strict"),
        )
        result = await caller(dict(VALID_GET_PRODUCTS))
        assert result["products"] == []
