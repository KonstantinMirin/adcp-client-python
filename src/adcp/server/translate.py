"""Error translation and request normalization for multi-transport servers.

Servers supporting both MCP and A2A need to translate AdCP errors to each
protocol's error format. These helpers eliminate that duplication.

Examples::

    from adcp.server import translate_error, normalize_request

    try:
        result = await handler.create_media_buy(params)
    except ADCPError as e:
        return translate_error(e, protocol="a2a")
        # Returns: {"state": "failed", "error": {"code": "...", "message": "..."}}

    return translate_error(e, protocol="mcp")
    # Returns: {"content": [{"type": "text", "text": "CODE: msg"}],
    #           "structuredContent": {"error": {"code": "...", ...}},
    #           "isError": True}

    # Normalize deprecated field names before processing
    params = normalize_request(params)
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from adcp.exceptions import (
    ADCPAuthenticationError,
    ADCPConnectionError,
    ADCPError,
    ADCPTimeoutError,
)
from adcp.types import Error
from adcp.types.core import Protocol

# Map deprecated field names to current names.
# Applied globally across all task types.
_FIELD_RENAMES: dict[str, str] = {
    "account_id": "account",
    "campaign_ref": "buyer_campaign_ref",
}


class MCPErrorResult(TypedDict):
    """MCP tool error response shape."""

    content: list[dict[str, str]]
    structuredContent: dict[str, Any]
    isError: bool


class A2AErrorResult(TypedDict):
    """A2A failed task response shape."""

    state: str
    error: dict[str, Any]


def _error_code_for_exception(exc: ADCPError) -> str:
    """Derive a structured error code from an exception type."""
    if isinstance(exc, ADCPAuthenticationError):
        return "AUTH_ERROR"
    if isinstance(exc, ADCPTimeoutError):
        return "TIMEOUT"
    if isinstance(exc, ADCPConnectionError):
        return "SERVICE_UNAVAILABLE"
    return "INTERNAL_ERROR"


def _error_to_dict(err: Error) -> dict[str, Any]:
    """Convert an Error model to a dict, excluding None fields."""
    return err.model_dump(exclude_none=True)


def translate_error(
    exc: ADCPError | Error,
    protocol: Literal["mcp", "a2a"] | Protocol,
) -> MCPErrorResult | A2AErrorResult:
    """Translate an AdCP error to a protocol-specific error response.

    Accepts either an ``ADCPError`` exception (from a catch block) or an
    ``Error`` Pydantic model (from a constructed response).

    Args:
        exc: An ADCPError exception or an Error Pydantic model.
        protocol: Target protocol - ``"mcp"`` or ``"a2a"`` (or Protocol enum).

    Returns:
        Protocol-specific dict:

        - MCP: ``MCPErrorResult`` with ``content``, ``structuredContent``,
          and ``isError=True``.
        - A2A: ``A2AErrorResult`` with ``state="failed"`` and ``error`` dict.

    Raises:
        ValueError: If protocol is not ``"mcp"`` or ``"a2a"``.

    Warning:
        The ``details`` field and any extra fields on the Error model are
        passed through verbatim. Do not include internal state (stack traces,
        SQL queries, internal URLs) in Error objects passed to this function,
        as the output is sent to external clients.
    """
    proto = protocol.value if isinstance(protocol, Protocol) else str(protocol)
    proto = proto.lower()
    if proto not in ("mcp", "a2a"):
        raise ValueError(f"protocol must be 'mcp' or 'a2a', got {protocol!r}")

    # Normalize to an Error model
    if isinstance(exc, Error):
        error_model = exc
    else:
        error_model = Error(
            code=_error_code_for_exception(exc),
            message=exc.message,
            suggestion=exc.suggestion,
        )

    if proto == "mcp":
        return _to_mcp(error_model)
    return _to_a2a(error_model)


def _to_mcp(error: Error) -> MCPErrorResult:
    """Format error as MCP tool result with isError=True."""
    text = f"{error.code}: {error.message}"
    return MCPErrorResult(
        content=[{"type": "text", "text": text}],
        structuredContent={"error": _error_to_dict(error)},
        isError=True,
    )


def _to_a2a(error: Error) -> A2AErrorResult:
    """Format error as A2A failed task status."""
    return A2AErrorResult(
        state="failed",
        error=_error_to_dict(error),
    )


def normalize_request(
    params: dict[str, Any],
    task_name: str | None = None,
) -> dict[str, Any]:
    """Normalize deprecated field names in request params.

    Applies known field renames so servers can accept both old and new
    field names without duplicating rename logic in every handler.

    If both the deprecated and current field name are present, the current
    name takes precedence and the deprecated name is removed.

    Args:
        params: Request parameters dict.
        task_name: Optional ADCP task/tool name (e.g. ``"create_media_buy"``).
            Reserved for task-specific renames in the future.

    Returns:
        New dict with deprecated field names replaced by current names.
        Original dict is not mutated.
    """
    result = dict(params)
    for old_name, new_name in _FIELD_RENAMES.items():
        if old_name in result:
            # Only rename if the current name isn't already set
            if new_name not in result:
                result[new_name] = result.pop(old_name)
            else:
                del result[old_name]
    return result
