"""Convert schema validation failures into thrown errors and the AdCP
``VALIDATION_ERROR`` envelope used by server middleware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adcp.validation.schema_validator import SchemaValidationError, ValidationIssue


@dataclass(frozen=True)
class ValidationErrorDetails:
    """Attached to a thrown :class:`SchemaValidationError` via ``details``."""

    tool: str
    side: str
    issues: list[ValidationIssue]


@dataclass(frozen=True)
class AdcpValidationErrorDetails:
    """Shape of ``adcp_error.details`` inside a server-side
    ``VALIDATION_ERROR`` envelope. Shipped so buyers can index every
    pointer programmatically instead of parsing the free-text message."""

    tool: str
    side: str
    issues: list[ValidationIssue]


def build_validation_error(
    tool: str, side: str, issues: list[ValidationIssue]
) -> SchemaValidationError:
    """Build a :class:`SchemaValidationError` carrying every failure.

    Strict-mode client hooks raise this so callers can inspect the full
    pointer list via ``.issues`` rather than only the first message.
    """
    err = SchemaValidationError(tool, side, issues)
    err.details = ValidationErrorDetails(tool=tool, side=side, issues=issues)  # type: ignore[attr-defined]
    return err


def build_adcp_validation_error_payload(
    tool: str, side: str, issues: list[ValidationIssue]
) -> dict[str, Any]:
    """Serialize issues into the kwargs expected by the AdCP ``Error`` model.

    Returns a dict with ``code`` / ``message`` / optional ``field`` /
    ``details`` keys — ready to splat into
    ``Error(**build_adcp_validation_error_payload(...))`` or into the
    server's ``adcp_error`` response envelope.
    """
    first = issues[0] if issues else None
    if first is not None:
        message = f"{tool} {side} failed schema validation at " f"{first.pointer}: {first.message}"
    else:
        message = f"{tool} {side} failed schema validation"

    payload: dict[str, Any] = {
        "code": "VALIDATION_ERROR",
        "message": message,
        "details": {
            "tool": tool,
            "side": side,
            "issues": [
                {
                    "pointer": i.pointer,
                    "message": i.message,
                    "keyword": i.keyword,
                    "schema_path": i.schema_path,
                }
                for i in issues
            ],
        },
    }
    if first is not None and first.pointer:
        payload["field"] = first.pointer
    return payload
