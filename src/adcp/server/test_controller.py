"""Built-in comply_test_controller for ADCP servers.

Provides TestControllerStore and register_test_controller() so that
storyboard tests can manipulate server state (force status transitions,
simulate delivery, etc.) without agents needing to implement the
comply_test_controller tool by hand.

Usage:
    from adcp.server import serve, ADCPHandler
    from adcp.server.test_controller import TestControllerStore, register_test_controller

    class MyStore(TestControllerStore):
        async def force_account_status(self, account_id, status):
            old = self.accounts[account_id]["status"]
            self.accounts[account_id]["status"] = status
            return {"previous_state": old, "current_state": status}

    store = MyStore()
    serve(MySeller(), name="my-agent", test_controller=store)
"""

from __future__ import annotations

import json
from typing import Any

# Scenario names — must match the AdCP comply_test_controller schema
SCENARIOS = [
    "force_creative_status",
    "force_account_status",
    "force_media_buy_status",
    "force_session_status",
    "simulate_delivery",
    "simulate_budget_spend",
]


class TestControllerError(Exception):
    """Typed error for test controller store methods.

    Raise this from your TestControllerStore methods to return structured
    error responses. The dispatcher catches it and converts to the AdCP
    comply_test_controller error format.

    Example:
        async def force_media_buy_status(self, media_buy_id, status, rejection_reason=None):
            prev = self.media_buys.get(media_buy_id)
            if prev is None:
                raise TestControllerError("NOT_FOUND", f"Media buy {media_buy_id} not found")
            if prev in ("completed", "rejected", "canceled"):
                raise TestControllerError(
                    "INVALID_TRANSITION",
                    f"Cannot transition from {prev}",
                    current_state=prev,
                )
            self.media_buys[media_buy_id] = status
            return {"previous_state": prev, "current_state": status}
    """

    def __init__(self, code: str, message: str, current_state: str | None = None):
        super().__init__(message)
        self.code = code
        self.current_state = current_state


class TestControllerStore:
    """Base class for test controller state management.

    Subclass this and override the methods for scenarios your agent supports.
    Methods you don't override will be reported as unsupported scenarios
    and excluded from list_scenarios.

    Raise TestControllerError for structured error responses.
    """

    async def force_creative_status(
        self, creative_id: str, status: str, rejection_reason: str | None = None
    ) -> dict[str, Any]:
        """Force a creative to a given status.

        Returns:
            {"previous_state": str, "current_state": str}
        """
        raise NotImplementedError

    async def force_account_status(self, account_id: str, status: str) -> dict[str, Any]:
        """Force an account to a given status.

        Returns:
            {"previous_state": str, "current_state": str}
        """
        raise NotImplementedError

    async def force_media_buy_status(
        self, media_buy_id: str, status: str, rejection_reason: str | None = None
    ) -> dict[str, Any]:
        """Force a media buy to a given status.

        Returns:
            {"previous_state": str, "current_state": str}
        """
        raise NotImplementedError

    async def force_session_status(
        self, session_id: str, status: str, termination_reason: str | None = None
    ) -> dict[str, Any]:
        """Force a session to a given status.

        Returns:
            {"previous_state": str, "current_state": str}
        """
        raise NotImplementedError

    async def simulate_delivery(
        self,
        media_buy_id: str,
        impressions: int | None = None,
        clicks: int | None = None,
        conversions: int | None = None,
        reported_spend: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Simulate delivery metrics for a media buy.

        Returns:
            {"simulated": {...}, "cumulative": {...} | None}
        """
        raise NotImplementedError

    async def simulate_budget_spend(
        self,
        spend_percentage: float,
        account_id: str | None = None,
        media_buy_id: str | None = None,
    ) -> dict[str, Any]:
        """Simulate budget spend to a percentage.

        Returns:
            {"simulated": {...}}
        """
        raise NotImplementedError


def _list_scenarios(store: TestControllerStore) -> list[str]:
    """Detect which scenarios a store actually implements.

    Checks whether each scenario method is overridden in the store's
    own class (not just inherited from TestControllerStore).
    """
    implemented = []
    store_cls = type(store)
    for scenario in SCENARIOS:
        # Check if this class or any non-TestControllerStore ancestor defines it
        for cls in store_cls.__mro__:
            if cls is TestControllerStore:
                break
            if scenario in cls.__dict__:
                implemented.append(scenario)
                break
    return implemented


def _controller_error(
    error: str, detail: str, current_state: str | None = None
) -> dict[str, Any]:
    """Format a test controller error response."""
    resp: dict[str, Any] = {
        "success": False,
        "error": error,
        "error_detail": detail,
    }
    if current_state is not None:
        resp["current_state"] = current_state
    return resp


async def _handle_test_controller(
    store: TestControllerStore, params: dict[str, Any]
) -> dict[str, Any]:
    """Dispatch a comply_test_controller request to the store."""
    scenario = params.get("scenario")
    implemented = _list_scenarios(store)

    if scenario == "list_scenarios":
        return {
            "success": True,
            "scenarios": implemented,
        }

    if scenario not in SCENARIOS:
        return _controller_error(
            "UNKNOWN_SCENARIO",
            f"Unknown scenario: {scenario}",
        )

    if scenario not in implemented:
        return _controller_error(
            "UNKNOWN_SCENARIO",
            f"Scenario {scenario} is not implemented by this agent",
        )

    method = getattr(store, scenario)
    scenario_params = params.get("params", {})

    try:
        if scenario == "force_creative_status":
            result = await method(
                creative_id=scenario_params["creative_id"],
                status=scenario_params["status"],
                rejection_reason=scenario_params.get("rejection_reason"),
            )
        elif scenario == "force_account_status":
            result = await method(
                account_id=scenario_params["account_id"],
                status=scenario_params["status"],
            )
        elif scenario == "force_media_buy_status":
            result = await method(
                media_buy_id=scenario_params["media_buy_id"],
                status=scenario_params["status"],
                rejection_reason=scenario_params.get("rejection_reason"),
            )
        elif scenario == "force_session_status":
            result = await method(
                session_id=scenario_params["session_id"],
                status=scenario_params["status"],
                termination_reason=scenario_params.get("termination_reason"),
            )
        elif scenario == "simulate_delivery":
            result = await method(
                media_buy_id=scenario_params["media_buy_id"],
                impressions=scenario_params.get("impressions"),
                clicks=scenario_params.get("clicks"),
                conversions=scenario_params.get("conversions"),
                reported_spend=scenario_params.get("reported_spend"),
            )
        elif scenario == "simulate_budget_spend":
            result = await method(
                spend_percentage=scenario_params["spend_percentage"],
                account_id=scenario_params.get("account_id"),
                media_buy_id=scenario_params.get("media_buy_id"),
            )
        else:
            return _controller_error("UNKNOWN_SCENARIO", f"Unknown scenario: {scenario}")
    except TestControllerError as e:
        return _controller_error(e.code, str(e), current_state=e.current_state)
    except KeyError as e:
        return _controller_error("INVALID_PARAMS", f"Missing required parameter: {e}")
    except NotImplementedError:
        return _controller_error(
            "UNKNOWN_SCENARIO",
            f"Scenario {scenario} is not implemented by this agent",
        )
    except Exception as e:
        return _controller_error("INTERNAL_ERROR", str(e))

    # Wrap in success=True if the store didn't include it
    if isinstance(result, dict) and "success" not in result:
        result["success"] = True

    return dict(result)


def register_test_controller(mcp: Any, store: TestControllerStore) -> None:
    """Register the comply_test_controller tool on an MCP server.

    This is the Python equivalent of the JS SDK's registerTestController().
    It adds the comply_test_controller MCP tool backed by your TestControllerStore.

    Args:
        mcp: A FastMCP server instance.
        store: Your TestControllerStore implementation.

    Example:
        from adcp.server.test_controller import TestControllerStore, register_test_controller

        class MyStore(TestControllerStore):
            async def force_account_status(self, account_id, status):
                old = self.accounts[account_id]["status"]
                self.accounts[account_id]["status"] = status
                return {"previous_state": old, "current_state": status}

        mcp = create_mcp_server(MySeller(), name="my-agent")
        register_test_controller(mcp, MyStore())
        mcp.run(transport="streamable-http")
    """

    from mcp.server.fastmcp.tools import Tool
    from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
    from pydantic import ConfigDict

    async def comply_test_controller(**kwargs: Any) -> str:
        result = await _handle_test_controller(store, kwargs)
        return json.dumps(result)

    tool = Tool.from_function(
        comply_test_controller,
        name="comply_test_controller",
        description="Compliance test controller. Sandbox only, not for production use.",
    )

    # Override schema with the proper comply_test_controller inputSchema
    tool.parameters = {
        "type": "object",
        "properties": {
            "scenario": {
                "type": "string",
                "enum": [
                    "list_scenarios",
                    "force_creative_status",
                    "force_account_status",
                    "force_media_buy_status",
                    "force_session_status",
                    "simulate_delivery",
                    "simulate_budget_spend",
                ],
            },
            "params": {"type": "object"},
            "context": {"type": "object"},
        },
        "required": ["scenario"],
    }

    # Override fn_metadata with a permissive model
    class _ControllerArgs(ArgModelBase):
        model_config = ConfigDict(extra="allow")

        def model_dump_one_level(self) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for field_name in self.__class__.model_fields:
                result[field_name] = getattr(self, field_name)
            if self.model_extra:
                result.update(self.model_extra)
            return result

    tool.fn_metadata = FuncMetadata(
        arg_model=_ControllerArgs,
        output_schema=tool.fn_metadata.output_schema,
        output_model=tool.fn_metadata.output_model,
        wrap_output=tool.fn_metadata.wrap_output,
    )

    mcp._tool_manager._tools["comply_test_controller"] = tool
