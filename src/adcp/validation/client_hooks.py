"""Client-side hooks that run the schema validator around every AdCP tool
call. Pre-send validation blocks malformed requests; post-receive
validation catches field-name drift from agents (issue #249)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from adcp.validation.schema_errors import build_validation_error
from adcp.validation.schema_validator import (
    ValidationOutcome,
    format_issues,
    validate_request,
    validate_response,
)

logger = logging.getLogger(__name__)

ValidationMode = Literal["strict", "warn", "off"]


@dataclass(frozen=True)
class ValidationHookConfig:
    """Per-side client validation modes.

    Defaults match the TS port (adcontextprotocol/adcp-client#694):

    * ``requests``: ``"warn"`` — strict would break callers that
      intentionally send partial payloads (error-path tests, exploratory
      probes). Storyboards and compliance runners that want hard-stop
      enforcement pass ``requests="strict"`` explicitly.
    * ``responses``: ``"strict"`` in dev/test, ``"warn"`` when any of
      ``ADCP_ENV`` / ``PYTHON_ENV`` / ``ENV`` / ``ENVIRONMENT`` is set
      to ``production`` (or ``prod``). Strict-by-default makes the SDK
      a compliance harness: drift from an agent fails the task on the
      first call, not the Nth storyboard run.
    """

    requests: ValidationMode | None = None
    responses: ValidationMode | None = None


class DebugLogEntry(dict):  # type: ignore[type-arg]
    """Thin ``dict`` subclass for debug log append-only entries."""


def _default_response_mode() -> ValidationMode:
    """Response default: ``strict`` everywhere except when a common env
    var explicitly declares a production environment. Read at call time
    (not import time) so tests that ``patch.dict`` the environment work
    without a module-level reset hook.
    """
    for name in ("ADCP_ENV", "PYTHON_ENV", "ENV", "ENVIRONMENT"):
        val = os.environ.get(name)
        if val and val.lower() in {"prod", "production"}:
            return "warn"
    return "strict"


def resolve_validation_modes(
    config: ValidationHookConfig | None = None,
) -> tuple[ValidationMode, ValidationMode]:
    """Return the effective ``(requests, responses)`` modes."""
    req: ValidationMode = (config.requests if config is not None else None) or "warn"
    resp: ValidationMode = (
        config.responses if config is not None else None
    ) or _default_response_mode()
    return req, resp


def _log_warning(
    debug_logs: list[DebugLogEntry] | None,
    tool_name: str,
    side: str,
    outcome: ValidationOutcome,
) -> None:
    summary = format_issues(outcome.issues)
    logger.warning("Schema validation warning (%s) for %s: %s", side, tool_name, summary)
    if debug_logs is None:
        return
    debug_logs.append(
        DebugLogEntry(
            type="warning",
            message=f"Schema validation warning for {tool_name}: {summary}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            schema_variant=outcome.variant,
            issues=[
                {
                    "pointer": i.pointer,
                    "message": i.message,
                    "keyword": i.keyword,
                    "schema_path": i.schema_path,
                }
                for i in outcome.issues
            ],
        )
    )


def validate_outgoing_request(
    tool_name: str,
    params: Any,
    mode: ValidationMode,
    debug_logs: list[DebugLogEntry] | None = None,
) -> ValidationOutcome | None:
    """Run request validation per the configured mode.

    * ``off`` — no-op (returns ``None``; validator is not consulted).
    * ``warn`` — log + continue; returns the outcome.
    * ``strict`` — raise :class:`SchemaValidationError` on failure.
    """
    if mode == "off":
        return None
    outcome = validate_request(tool_name, params)
    if outcome.valid:
        return outcome
    if mode == "warn":
        _log_warning(debug_logs, tool_name, "request", outcome)
        return outcome
    raise build_validation_error(tool_name, "request", outcome.issues)


def validate_incoming_response(
    tool_name: str,
    data: Any,
    mode: ValidationMode,
    debug_logs: list[DebugLogEntry] | None = None,
) -> ValidationOutcome:
    """Run response validation per the configured mode.

    * ``off`` — no-op (returns a valid skipped outcome).
    * ``warn`` — log + return the invalid outcome so the caller can
      surface details without failing the task.
    * ``strict`` — return the invalid outcome so the caller fails the task.

    Never raises — matches the existing Python response contract where a
    validation failure turns a task into ``status=FAILED`` rather than
    raising out of the adapter.
    """
    if mode == "off":
        return ValidationOutcome(valid=True, issues=[], variant="skipped")
    outcome = validate_response(tool_name, data)
    if not outcome.valid and mode == "warn":
        _log_warning(debug_logs, tool_name, "response", outcome)
    return outcome
