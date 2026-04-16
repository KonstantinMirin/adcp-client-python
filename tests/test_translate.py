"""Tests for error translation and request normalization helpers."""

from __future__ import annotations

import pytest

from adcp.exceptions import (
    ADCPAuthenticationError,
    ADCPConnectionError,
    ADCPError,
    ADCPTimeoutError,
)
from adcp.server.translate import normalize_request, translate_error
from adcp.types import Error
from adcp.types.core import Protocol


class TestTranslateErrorToMCP:
    """Test translate_error with protocol='mcp'."""

    def test_translates_adcp_error_to_mcp(self):
        """ADCPError produces MCP error response with isError=True."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="mcp")

        assert result["isError"] is True
        assert any("something went wrong" in c["text"] for c in result["content"])

    def test_translates_error_model_to_mcp(self):
        """Error Pydantic model produces MCP error with code and message."""
        err = Error(code="VALIDATION_ERROR", message="Missing required field 'packages'")
        result = translate_error(err, protocol="mcp")

        assert result["isError"] is True
        assert result["structuredContent"]["error"]["code"] == "VALIDATION_ERROR"
        assert "packages" in result["structuredContent"]["error"]["message"]
        assert len(result["content"]) >= 1

    def test_translates_error_model_with_details(self):
        """Error with optional fields preserves them in structured content."""
        err = Error(
            code="RATE_LIMIT",
            message="Too many requests",
            retry_after=30.0,
            suggestion="Wait before retrying",
        )
        result = translate_error(err, protocol="mcp")

        sc = result["structuredContent"]["error"]
        assert sc["retry_after"] == 30.0
        assert sc["suggestion"] == "Wait before retrying"

    def test_translates_auth_error_to_mcp(self):
        """ADCPAuthenticationError includes error type context."""
        exc = ADCPAuthenticationError("Invalid token", agent_id="test-agent")
        result = translate_error(exc, protocol="mcp")

        assert result["isError"] is True
        assert any("Invalid token" in c["text"] for c in result["content"])

    def test_translates_timeout_error_to_mcp(self):
        """ADCPTimeoutError translates to MCP error."""
        exc = ADCPTimeoutError("Request timed out", timeout=30.0)
        result = translate_error(exc, protocol="mcp")

        assert result["isError"] is True

    def test_preserves_suggestion_from_exception(self):
        """Suggestion field on ADCPError is preserved in MCP output."""
        exc = ADCPError("bad request", suggestion="Try setting the budget field")
        result = translate_error(exc, protocol="mcp")

        sc = result["structuredContent"]["error"]
        assert sc["suggestion"] == "Try setting the budget field"


class TestTranslateErrorToA2A:
    """Test translate_error with protocol='a2a'."""

    def test_translates_adcp_error_to_a2a(self):
        """ADCPError produces A2A failed task response."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="a2a")

        assert result["state"] == "failed"
        assert result["error"]["message"] == "something went wrong"

    def test_translates_error_model_to_a2a(self):
        """Error Pydantic model produces A2A response with code."""
        err = Error(code="VALIDATION_ERROR", message="Missing field")
        result = translate_error(err, protocol="a2a")

        assert result["state"] == "failed"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Missing field"

    def test_translates_error_model_with_details_to_a2a(self):
        """Error with details preserved in A2A response."""
        err = Error(
            code="BUDGET_EXCEEDED",
            message="Budget exceeded",
            details={"max_budget": 10000, "requested": 15000},
        )
        result = translate_error(err, protocol="a2a")

        assert result["error"]["details"] == {"max_budget": 10000, "requested": 15000}

    def test_translates_connection_error_to_a2a(self):
        """ADCPConnectionError translates to A2A with SERVICE_UNAVAILABLE code."""
        exc = ADCPConnectionError("Cannot reach upstream")
        result = translate_error(exc, protocol="a2a")

        assert result["state"] == "failed"
        assert result["error"]["code"] == "SERVICE_UNAVAILABLE"

    def test_translates_auth_error_to_a2a(self):
        """ADCPAuthenticationError gets AUTH_ERROR code in A2A."""
        exc = ADCPAuthenticationError("Forbidden")
        result = translate_error(exc, protocol="a2a")

        assert result["error"]["code"] == "AUTH_ERROR"

    def test_translates_timeout_error_to_a2a(self):
        """ADCPTimeoutError gets TIMEOUT code in A2A."""
        exc = ADCPTimeoutError("Timed out", timeout=30.0)
        result = translate_error(exc, protocol="a2a")

        assert result["error"]["code"] == "TIMEOUT"

    def test_preserves_suggestion_from_exception(self):
        """Suggestion field on ADCPError is preserved in A2A output."""
        exc = ADCPError("bad request", suggestion="Check the budget field")
        result = translate_error(exc, protocol="a2a")

        assert result["error"]["suggestion"] == "Check the budget field"


class TestTranslateErrorValidation:
    """Test translate_error input validation."""

    def test_rejects_unknown_protocol(self):
        """Unknown protocol raises ValueError."""
        with pytest.raises(ValueError, match="protocol"):
            translate_error(ADCPError("err"), protocol="grpc")  # type: ignore[arg-type]

    def test_accepts_protocol_enum(self):
        """Protocol enum values work too."""
        err = Error(code="TEST", message="test")
        result_mcp = translate_error(err, protocol=Protocol.MCP)
        assert result_mcp["isError"] is True

        result_a2a = translate_error(err, protocol=Protocol.A2A)
        assert result_a2a["state"] == "failed"

    def test_accepts_uppercase_protocol_string(self):
        """Protocol strings are case-insensitive."""
        err = Error(code="TEST", message="test")
        result = translate_error(err, protocol="MCP")  # type: ignore[arg-type]
        assert result["isError"] is True


class TestNormalizeRequest:
    """Test normalize_request for cross-version field renames."""

    def test_renames_account_id_to_account(self):
        """account_id gets renamed to account."""
        params = {"account_id": "acct-123", "name": "Test"}
        result = normalize_request(params)

        assert result["account"] == "acct-123"
        assert "account_id" not in result

    def test_renames_campaign_ref_to_buyer_campaign_ref(self):
        """campaign_ref gets renamed to buyer_campaign_ref."""
        params = {"campaign_ref": "camp-456"}
        result = normalize_request(params)

        assert result["buyer_campaign_ref"] == "camp-456"
        assert "campaign_ref" not in result

    def test_does_not_overwrite_current_field_name(self):
        """If the current field name is already present, don't overwrite."""
        params = {"account_id": "old", "account": "current"}
        result = normalize_request(params)

        assert result["account"] == "current"
        assert "account_id" not in result

    def test_no_renames_when_params_are_current(self):
        """Params using current field names pass through unchanged."""
        params = {"account": "acct-123", "buyer_campaign_ref": "camp-456"}
        result = normalize_request(params)

        assert result == params

    def test_returns_new_dict(self):
        """normalize_request returns a copy, does not mutate input."""
        params = {"account_id": "acct-123"}
        result = normalize_request(params)

        assert result is not params
        assert "account_id" in params  # original unchanged

    def test_works_with_task_name(self):
        """Optional task_name parameter is accepted."""
        params = {"account_id": "acct-123"}
        result = normalize_request(params, task_name="update_media_buy")

        assert result["account"] == "acct-123"

    def test_empty_params(self):
        """Empty params return empty dict."""
        result = normalize_request({})
        assert result == {}

    def test_unknown_fields_pass_through(self):
        """Fields not in the rename map pass through unchanged."""
        params = {"custom_field": "value", "account_id": "acct-123"}
        result = normalize_request(params)

        assert result["custom_field"] == "value"
        assert result["account"] == "acct-123"
