"""Tests for error translation and request normalization helpers."""

from __future__ import annotations

import pytest
from a2a.types import InternalError, InvalidParamsError
from a2a.utils.errors import ServerError
from mcp.server.fastmcp.exceptions import ToolError

from adcp.exceptions import (
    ADCPAuthenticationError,
    ADCPConnectionError,
    ADCPError,
    ADCPTaskError,
    ADCPTimeoutError,
)
from adcp.server.translate import normalize_request, translate_error
from adcp.types import Error
from adcp.types.core import Protocol

# ============================================================================
# translate_error → MCP
# ============================================================================


class TestTranslateErrorToMCP:
    """Test translate_error with protocol='mcp'."""

    def test_returns_tool_error(self):
        """MCP translation returns a ToolError instance."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="mcp")
        assert isinstance(result, ToolError)

    def test_includes_code_and_message(self):
        """ToolError text contains the error code and message."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="mcp")
        assert "INTERNAL_ERROR" in str(result)
        assert "something went wrong" in str(result)

    def test_error_model_uses_its_code(self):
        """Error Pydantic model produces ToolError with its own code."""
        err = Error(code="VALIDATION_ERROR", message="Missing field 'packages'")
        result = translate_error(err, protocol="mcp")
        assert "VALIDATION_ERROR" in str(result)
        assert "packages" in str(result)

    def test_preserves_suggestion(self):
        """Suggestion from ADCPError appears in ToolError text."""
        exc = ADCPError("bad request", suggestion="Set the budget field")
        result = translate_error(exc, protocol="mcp")
        assert "Set the budget field" in str(result)

    def test_auth_error_maps_to_auth_required(self):
        """ADCPAuthenticationError maps to AUTH_REQUIRED code."""
        exc = ADCPAuthenticationError("Invalid token", agent_id="test-agent")
        result = translate_error(exc, protocol="mcp")
        assert "AUTH_REQUIRED" in str(result)

    def test_timeout_error_maps_to_service_unavailable(self):
        """ADCPTimeoutError maps to SERVICE_UNAVAILABLE code."""
        exc = ADCPTimeoutError("Request timed out", timeout=30.0)
        result = translate_error(exc, protocol="mcp")
        assert "SERVICE_UNAVAILABLE" in str(result)

    def test_connection_error_maps_to_service_unavailable(self):
        """ADCPConnectionError maps to SERVICE_UNAVAILABLE code."""
        exc = ADCPConnectionError("Cannot reach upstream")
        result = translate_error(exc, protocol="mcp")
        assert "SERVICE_UNAVAILABLE" in str(result)

    def test_task_error_uses_original_code(self):
        """ADCPTaskError preserves the original error code from the response."""
        err = Error(code="BUDGET_TOO_LOW", message="Budget below minimum")
        exc = ADCPTaskError("create_media_buy", [err])
        result = translate_error(exc, protocol="mcp")
        assert "BUDGET_TOO_LOW" in str(result)


# ============================================================================
# translate_error → A2A
# ============================================================================


class TestTranslateErrorToA2A:
    """Test translate_error with protocol='a2a'."""

    def test_returns_server_error(self):
        """A2A translation returns a ServerError instance."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="a2a")
        assert isinstance(result, ServerError)

    def test_internal_error_wraps_internal(self):
        """Generic ADCPError wraps InternalError (terminal/transient)."""
        exc = ADCPError("something went wrong")
        result = translate_error(exc, protocol="a2a")
        assert isinstance(result.error, InternalError)
        assert result.error.message == "something went wrong"

    def test_correctable_error_wraps_invalid_params(self):
        """Error with correctable code wraps InvalidParamsError."""
        err = Error(code="VALIDATION_ERROR", message="Missing field")
        result = translate_error(err, protocol="a2a")
        assert isinstance(result.error, InvalidParamsError)

    def test_data_includes_recovery(self):
        """A2A error data includes recovery classification."""
        exc = ADCPConnectionError("Cannot reach upstream")
        result = translate_error(exc, protocol="a2a")
        assert result.error.data["recovery"] == "transient"

    def test_data_includes_error_code(self):
        """A2A error data includes the ADCP error code."""
        err = Error(code="BUDGET_TOO_LOW", message="Budget below minimum")
        result = translate_error(err, protocol="a2a")
        assert result.error.data["error_code"] == "BUDGET_TOO_LOW"

    def test_data_includes_suggestion(self):
        """A2A error data includes suggestion when present."""
        exc = ADCPError("bad request", suggestion="Check the budget field")
        result = translate_error(exc, protocol="a2a")
        assert result.error.data["suggestion"] == "Check the budget field"

    def test_data_includes_details(self):
        """A2A error data includes details from Error model."""
        err = Error(
            code="BUDGET_EXCEEDED",
            message="Budget exceeded",
            details={"max_budget": 10000, "requested": 15000},
        )
        result = translate_error(err, protocol="a2a")
        assert result.error.data["details"] == {"max_budget": 10000, "requested": 15000}

    def test_task_error_preserves_original_errors(self):
        """ADCPTaskError passes through the original error list."""
        err1 = Error(code="BUDGET_TOO_LOW", message="Budget below minimum")
        err2 = Error(code="AUDIENCE_TOO_SMALL", message="Audience too small")
        exc = ADCPTaskError("create_media_buy", [err1, err2])
        result = translate_error(exc, protocol="a2a")
        errors = result.error.data["errors"]
        assert len(errors) == 2
        assert errors[0]["code"] == "BUDGET_TOO_LOW"
        assert errors[1]["code"] == "AUDIENCE_TOO_SMALL"

    def test_auth_error_is_terminal(self):
        """ADCPAuthenticationError gets terminal recovery."""
        exc = ADCPAuthenticationError("Forbidden")
        result = translate_error(exc, protocol="a2a")
        assert result.error.data["recovery"] == "terminal"

    def test_timeout_error_is_transient(self):
        """ADCPTimeoutError gets transient recovery."""
        exc = ADCPTimeoutError("Timed out", timeout=30.0)
        result = translate_error(exc, protocol="a2a")
        assert result.error.data["recovery"] == "transient"


# ============================================================================
# translate_error validation
# ============================================================================


class TestTranslateErrorValidation:
    """Test translate_error input validation."""

    def test_rejects_unknown_protocol(self):
        """Unknown protocol raises ValueError."""
        with pytest.raises(ValueError, match="protocol"):
            translate_error(ADCPError("err"), protocol="grpc")  # type: ignore[arg-type]

    def test_accepts_protocol_enum(self):
        """Protocol enum values work."""
        err = Error(code="TEST", message="test")
        result_mcp = translate_error(err, protocol=Protocol.MCP)
        assert isinstance(result_mcp, ToolError)

        result_a2a = translate_error(err, protocol=Protocol.A2A)
        assert isinstance(result_a2a, ServerError)

    def test_accepts_uppercase_protocol_string(self):
        """Protocol strings are case-insensitive."""
        err = Error(code="TEST", message="test")
        result = translate_error(err, protocol="MCP")  # type: ignore[arg-type]
        assert isinstance(result, ToolError)


# ============================================================================
# normalize_request — structural transforms
# ============================================================================


class TestNormalizeAccountId:
    """Test account_id → account structural reshape."""

    def test_reshapes_account_id_to_nested_object(self):
        """account_id string becomes account: {account_id: "..."}."""
        params = {"account_id": "acct-123", "name": "Test"}
        result = normalize_request(params)

        assert result["account"] == {"account_id": "acct-123"}
        assert "account_id" not in result

    def test_does_not_overwrite_existing_account(self):
        """If account already present, account_id is dropped."""
        params = {"account_id": "old", "account": {"account_id": "current"}}
        result = normalize_request(params)

        assert result["account"] == {"account_id": "current"}
        assert "account_id" not in result

    def test_no_account_id_is_noop(self):
        """Params without account_id pass through unchanged."""
        params = {"account": {"account_id": "123"}}
        result = normalize_request(params)
        assert result == params


class TestNormalizeBrandManifest:
    """Test brand_manifest URL → brand object."""

    def test_parses_url_to_domain(self):
        """brand_manifest URL is parsed to brand: {domain: hostname}."""
        params = {"brand_manifest": "https://example.com/brand.json"}
        result = normalize_request(params)

        assert result["brand"] == {"domain": "example.com"}
        assert "brand_manifest" not in result

    def test_does_not_overwrite_existing_brand(self):
        """If brand already present, brand_manifest is dropped."""
        params = {"brand_manifest": "https://old.com", "brand": {"domain": "new.com"}}
        result = normalize_request(params)

        assert result["brand"] == {"domain": "new.com"}
        assert "brand_manifest" not in result

    def test_non_string_manifest_renamed(self):
        """Non-string brand_manifest is passed through as brand."""
        params = {"brand_manifest": {"url": "https://example.com"}}
        result = normalize_request(params)

        assert result["brand"] == {"url": "https://example.com"}


class TestNormalizePackages:
    """Test package-level scalar-to-array transforms."""

    def test_optimization_goal_to_array(self):
        """optimization_goal string wraps to optimization_goals array."""
        params = {"packages": [{"optimization_goal": "cpa", "name": "pkg1"}]}
        result = normalize_request(params)

        assert result["packages"][0]["optimization_goals"] == ["cpa"]
        assert "optimization_goal" not in result["packages"][0]

    def test_catalog_to_array(self):
        """catalog string wraps to catalogs array."""
        params = {"packages": [{"catalog": "retail"}]}
        result = normalize_request(params)

        assert result["packages"][0]["catalogs"] == ["retail"]
        assert "catalog" not in result["packages"][0]

    def test_does_not_overwrite_existing_array(self):
        """If optimization_goals already present, scalar is dropped."""
        params = {"packages": [{"optimization_goal": "cpa", "optimization_goals": ["roas"]}]}
        result = normalize_request(params)

        assert result["packages"][0]["optimization_goals"] == ["roas"]
        assert "optimization_goal" not in result["packages"][0]

    def test_does_not_mutate_original_packages(self):
        """Package dicts in the original params are not mutated."""
        pkg = {"optimization_goal": "cpa"}
        params = {"packages": [pkg]}
        normalize_request(params)

        assert "optimization_goal" in pkg  # original unchanged


# ============================================================================
# normalize_request — renames
# ============================================================================


class TestNormalizeRenames:
    """Test field renames (global and tool-scoped)."""

    def test_promoted_offerings_to_catalogs(self):
        """promoted_offerings renames to catalogs."""
        params = {"promoted_offerings": ["offer-1"]}
        result = normalize_request(params)

        assert result["catalogs"] == ["offer-1"]
        assert "promoted_offerings" not in result

    def test_campaign_ref_scoped_to_create_media_buy(self):
        """campaign_ref → buyer_campaign_ref only on create_media_buy."""
        params = {"campaign_ref": "camp-456"}

        result_scoped = normalize_request(params, task_name="create_media_buy")
        assert result_scoped["buyer_campaign_ref"] == "camp-456"
        assert "campaign_ref" not in result_scoped

    def test_campaign_ref_not_renamed_for_other_tasks(self):
        """campaign_ref passes through for non-create_media_buy tasks."""
        params = {"campaign_ref": "camp-456"}

        result_other = normalize_request(params, task_name="update_media_buy")
        assert result_other["campaign_ref"] == "camp-456"
        assert "buyer_campaign_ref" not in result_other

    def test_campaign_ref_not_renamed_without_task_name(self):
        """campaign_ref passes through when no task_name provided."""
        params = {"campaign_ref": "camp-456"}
        result = normalize_request(params)

        assert result["campaign_ref"] == "camp-456"


# ============================================================================
# normalize_request — general behavior
# ============================================================================


class TestNormalizeGeneral:
    """Test general normalize_request behavior."""

    def test_returns_new_dict(self):
        """normalize_request returns a copy, does not mutate input."""
        params = {"account_id": "acct-123"}
        result = normalize_request(params)

        assert result is not params
        assert "account_id" in params  # original unchanged

    def test_empty_params(self):
        """Empty params return empty dict."""
        result = normalize_request({})
        assert result == {}

    def test_unknown_fields_pass_through(self):
        """Fields not in any rename map pass through unchanged."""
        params = {"custom_field": "value", "account_id": "acct-123"}
        result = normalize_request(params)

        assert result["custom_field"] == "value"
        assert result["account"] == {"account_id": "acct-123"}

    def test_all_transforms_combined(self):
        """Multiple transforms apply in a single call."""
        params = {
            "account_id": "acct-1",
            "brand_manifest": "https://brand.co/manifest.json",
            "promoted_offerings": ["offer-1"],
            "campaign_ref": "camp-1",
            "packages": [{"optimization_goal": "cpa", "catalog": "retail"}],
        }
        result = normalize_request(params, task_name="create_media_buy")

        assert result["account"] == {"account_id": "acct-1"}
        assert result["brand"] == {"domain": "brand.co"}
        assert result["catalogs"] == ["offer-1"]
        assert result["buyer_campaign_ref"] == "camp-1"
        assert result["packages"][0]["optimization_goals"] == ["cpa"]
        assert result["packages"][0]["catalogs"] == ["retail"]
        # Old names removed
        assert "account_id" not in result
        assert "brand_manifest" not in result
        assert "promoted_offerings" not in result
        assert "campaign_ref" not in result
