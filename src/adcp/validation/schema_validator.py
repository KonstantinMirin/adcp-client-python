"""Schema-driven validation for AdCP tool requests and responses.

The client uses this pre-send and post-receive; the opt-in server
middleware uses the same core to reject drift at the dispatcher.

Issues carry an RFC 6901 JSON Pointer to the offending field so callers
can index every failure programmatically instead of parsing free text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adcp.validation.schema_loader import Direction, ResponseVariant, get_validator


class SchemaValidationError(Exception):
    """Raised by strict-mode client hooks when a payload fails schema.

    Carries the full issue list via :attr:`issues` so callers can inspect
    every JSON Pointer, not just the first. Mirrors the shape of the AdCP
    L3 ``VALIDATION_ERROR`` error envelope.
    """

    def __init__(
        self,
        tool: str,
        side: str,
        issues: list[ValidationIssue],
        message: str | None = None,
    ) -> None:
        self.tool = tool
        self.side = side
        self.issues = issues
        self.code = "VALIDATION_ERROR"
        if message is None:
            first = issues[0] if issues else None
            if first is not None:
                message = (
                    f"{tool} {side} failed schema validation at "
                    f"{first.pointer}: {first.message}"
                )
            else:
                message = f"{tool} {side} failed schema validation"
        super().__init__(message)


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation failure.

    Attributes:
        pointer: RFC 6901 JSON Pointer to the offending field.
        message: Human-readable message from the schema engine.
        keyword: jsonschema keyword that rejected the payload
            (``required``, ``type``, ``enum``, etc.).
        schema_path: Path inside the schema that rejected the payload.
    """

    pointer: str
    message: str
    keyword: str
    schema_path: str


@dataclass(frozen=True)
class ValidationOutcome:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    variant: str = "skipped"


_OK_SKIPPED = ValidationOutcome(valid=True, issues=[], variant="skipped")


def _path_to_pointer(path: Any) -> str:
    """Convert a jsonschema ``deque(['packages', 0, 'targeting'])`` to
    ``/packages/0/targeting``. Empty path maps to ``/`` per RFC 6901
    convention used in the TS SDK (AJV's ``instancePath='' -> '/'``)."""
    if not path:
        return "/"

    def escape(seg: Any) -> str:
        s = str(seg)
        return s.replace("~", "~0").replace("/", "~1")

    return "/" + "/".join(escape(seg) for seg in path)


def _format_error(err: Any) -> ValidationIssue:
    """Turn a ``jsonschema.exceptions.ValidationError`` into a ``ValidationIssue``."""
    path = list(err.absolute_path)
    pointer = _path_to_pointer(path)

    keyword = err.validator or "validation"

    if keyword == "required":
        missing = err.message
        if "'" in missing:
            name = missing.split("'")[1] if missing.count("'") >= 2 else None
            if name:
                pointer = pointer.rstrip("/") + "/" + name if pointer != "/" else "/" + name

    schema_path = "#/" + "/".join(str(seg) for seg in err.absolute_schema_path)

    return ValidationIssue(
        pointer=pointer,
        message=err.message,
        keyword=str(keyword),
        schema_path=schema_path,
    )


def validate_request(tool_name: str, payload: Any) -> ValidationOutcome:
    """Validate an outgoing request against ``{tool}-request.json``."""
    validator = get_validator(tool_name, "request")
    if validator is None:
        return _OK_SKIPPED
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return ValidationOutcome(valid=True, issues=[], variant="request")
    return ValidationOutcome(
        valid=False,
        issues=[_format_error(e) for e in errors],
        variant="request",
    )


def _select_response_variant(payload: Any) -> ResponseVariant:
    """Pick the response variant by payload shape per AdCP 3.0 async contract.

    Per issue #688: choose by ``status`` field, not just tool name.
    ``submitted`` / ``working`` / ``input-required`` are the three
    async variants; everything else (``completed``, no status, terminal
    errors) routes to the sync schema.
    """
    if isinstance(payload, dict):
        status = payload.get("status")
        if status == "submitted":
            return "submitted"
        if status == "working":
            return "working"
        if status == "input-required":
            return "input-required"
    return "sync"


def validate_response(tool_name: str, payload: Any) -> ValidationOutcome:
    """Validate an incoming response, selecting the variant by payload shape."""
    variant: ResponseVariant = _select_response_variant(payload)
    validator = get_validator(tool_name, variant)
    used_variant: Direction = variant
    if validator is None and variant != "sync":
        validator = get_validator(tool_name, "sync")
        used_variant = "sync"
    if validator is None:
        return _OK_SKIPPED
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return ValidationOutcome(valid=True, issues=[], variant=used_variant)
    return ValidationOutcome(
        valid=False,
        issues=[_format_error(e) for e in errors],
        variant=used_variant,
    )


def format_issues(issues: list[ValidationIssue], limit: int = 3) -> str:
    """Render a compact one-line summary of failures — useful for logs."""
    head = "; ".join(f"{i.pointer} {i.message}" for i in issues[:limit])
    rest = len(issues) - limit
    return f"{head} (+{rest} more)" if rest > 0 else head
