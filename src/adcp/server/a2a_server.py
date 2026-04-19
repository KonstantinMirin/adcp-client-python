"""A2A server support for ADCP handlers.

Bridges ADCPHandler to the a2a-sdk server framework so the same handler
can be served over both MCP and A2A transports.

    from adcp.server import ADCPHandler, serve
    serve(MyHandler(), name="my-agent", transport="a2a")
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from uuid import uuid4

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import (
    DefaultRequestHandler,
)
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Artifact,
    DataPart,
    Part,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

from adcp.exceptions import ADCPError, ADCPTaskError
from adcp.server.base import ADCPHandler, ToolContext
from adcp.server.helpers import STANDARD_ERROR_CODES
from adcp.server.mcp_tools import create_tool_caller, get_tools_for_handler
from adcp.server.test_controller import TestControllerStore, _handle_test_controller

logger = logging.getLogger(__name__)


class ADCPAgentExecutor(AgentExecutor):
    """Bridges ADCPHandler methods to the a2a-sdk AgentExecutor interface.

    Incoming A2A messages are parsed to extract the ADCP skill name and
    parameters, dispatched to the matching handler method, and the result
    is published back as A2A Task events.

    Expects the explicit skill invocation format used by A2AAdapter:
        DataPart(data={"skill": "get_products", "parameters": {...}})
    """

    def __init__(
        self,
        handler: ADCPHandler,
        test_controller: TestControllerStore | None = None,
    ) -> None:
        self._handler = handler
        self._tool_callers: dict[str, Any] = {}

        # Build tool callers for all tools this handler supports
        tool_defs = get_tools_for_handler(handler)
        for tool_def in tool_defs:
            name = tool_def["name"]
            self._tool_callers[name] = create_tool_caller(handler, name)

        if test_controller is not None:
            self._register_test_controller(test_controller)

    @property
    def supported_skills(self) -> list[str]:
        """List of skill names this executor can handle."""
        return list(self._tool_callers.keys())

    def _register_test_controller(self, store: TestControllerStore) -> None:
        """Register comply_test_controller as a callable skill."""

        async def _call_test_controller(
            params: dict[str, Any], context: ToolContext | None = None
        ) -> Any:
            return await _handle_test_controller(store, params)

        self._tool_callers["comply_test_controller"] = _call_test_controller

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Execute an ADCP skill from an incoming A2A message."""
        skill_name, params = self._parse_request(context)

        if skill_name is None:
            await self._send_error(
                event_queue, context, "No skill specified in message"
            )
            return

        if skill_name not in self._tool_callers:
            await self._send_error(
                event_queue, context, f"Unknown skill: {skill_name}"
            )
            return

        tool_context = _tool_context_from_request(context)
        try:
            result = await self._tool_callers[skill_name](params, tool_context)
            await self._send_result(event_queue, context, skill_name, result)
        except ADCPError as exc:
            # Application-layer AdCP error (IdempotencyConflictError etc.).
            # Emit a failed task with the adcp_error in a DataPart per
            # transport-errors.mdx §A2A Binding, plus a human-readable text
            # part. The JSON-RPC channel is reserved for transport-level
            # errors (auth rejected, rate-limited pre-dispatch).
            logger.info(
                "AdCP application error for skill %s: %s", skill_name, exc
            )
            await self._send_adcp_error(event_queue, context, exc)
        except Exception:
            logger.exception("Error executing skill %s", skill_name)
            await self._send_error(
                event_queue, context, f"Skill execution failed: {skill_name}"
            )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """ADCP operations are synchronous; cancellation sets state to canceled."""
        event = _make_task(
            context,
            state=TaskState.canceled,
            message="Task canceled",
        )
        await event_queue.enqueue_event(event)

    # ------------------------------------------------------------------
    # Message parsing
    # ------------------------------------------------------------------

    def _parse_request(
        self, context: RequestContext
    ) -> tuple[str | None, dict[str, Any]]:
        """Extract skill name and parameters from the A2A message.

        Supports two formats:
        1. Explicit skill invocation via DataPart:
           DataPart(data={"skill": "get_products", "parameters": {...}})
        2. Natural language fallback via TextPart (best-effort parse)
        """
        msg = context.message
        if msg is None or not msg.parts:
            return None, {}

        # Try DataPart first (explicit skill invocation)
        for part in msg.parts:
            inner = part.root if hasattr(part, "root") else part
            if isinstance(inner, DataPart) and isinstance(inner.data, dict):
                skill = inner.data.get("skill")
                params = inner.data.get("parameters", {})
                if skill:
                    return str(skill), params if isinstance(params, dict) else {}

        # Fallback: try to parse TextPart as JSON
        for part in msg.parts:
            inner = part.root if hasattr(part, "root") else part
            if isinstance(inner, TextPart):
                parsed = self._parse_text_request(inner.text)
                if parsed[0] is not None:
                    return parsed

        return None, {}

    def _parse_text_request(
        self, text: str
    ) -> tuple[str | None, dict[str, Any]]:
        """Best-effort parse of a text request for skill + params."""
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "skill" in data:
                return str(data["skill"]), data.get("parameters", {})
        except (json.JSONDecodeError, TypeError):
            pass
        return None, {}

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    async def _send_result(
        self,
        event_queue: EventQueue,
        context: RequestContext,
        skill_name: str,
        result: Any,
    ) -> None:
        """Publish a completed task with the skill result."""
        # Normalize result to a JSON-safe dict
        if hasattr(result, "model_dump"):
            data = result.model_dump(mode="json", exclude_none=True)
        elif not isinstance(result, dict):
            data = {"result": result}
        else:
            data = result

        task = _make_task(
            context,
            state=TaskState.completed,
            data=data,
            message=f"Completed {skill_name}",
        )
        await event_queue.enqueue_event(task)

    async def _send_error(
        self,
        event_queue: EventQueue,
        context: RequestContext,
        error_msg: str,
    ) -> None:
        """Publish a failed task."""
        task = _make_task(
            context,
            state=TaskState.failed,
            message=error_msg,
        )
        await event_queue.enqueue_event(task)

    async def _send_adcp_error(
        self,
        event_queue: EventQueue,
        context: RequestContext,
        exc: ADCPError,
    ) -> None:
        """Publish a failed task carrying an AdCP ``adcp_error`` payload.

        Follows transport-errors.mdx §A2A Binding: failed task with artifact
        containing a ``DataPart`` keyed under ``adcp_error`` plus a terse
        ``TextPart`` for human/LLM consumption.
        """
        # Derive the spec error code. ADCPTaskError carries a list of codes
        # (e.g. IdempotencyConflictError → IDEMPOTENCY_CONFLICT); fall back
        # to a generic INTERNAL_ERROR when the exception doesn't supply one.
        code = "INTERNAL_ERROR"
        if isinstance(exc, ADCPTaskError) and exc.error_codes:
            code = str(exc.error_codes[0])

        adcp_error: dict[str, Any] = {
            "code": code,
            "message": exc.message,
        }
        recovery = STANDARD_ERROR_CODES.get(code, {}).get("recovery")
        if recovery:
            adcp_error["recovery"] = recovery
        suggestion = getattr(exc, "suggestion", None)
        if suggestion:
            adcp_error["suggestion"] = suggestion

        task = _make_task(
            context,
            state=TaskState.failed,
            data={"adcp_error": adcp_error},
            message=exc.message,
        )
        await event_queue.enqueue_event(task)


# ------------------------------------------------------------------
# Request context helpers
# ------------------------------------------------------------------


def _tool_context_from_request(request: RequestContext) -> ToolContext:
    """Derive a :class:`ToolContext` from an A2A :class:`RequestContext`.

    Extracts the authenticated principal from ``request.call_context.user``
    when present. Unauthenticated / anonymous requests get a bare
    ``ToolContext`` — server middleware that requires a principal (e.g. the
    idempotency store's per-principal scoping) falls through to its
    no-principal default rather than collapsing everyone into a shared
    namespace.

    Security invariant: ``ServerCallContext`` is populated by the seller's
    server-side auth middleware from verified transport material (bearer
    token, mTLS cert, OAuth identity). A malicious client cannot flip
    ``is_authenticated`` or set ``user_name`` from the message payload.
    The ``is_authenticated and user_name`` gate below relies on this
    invariant — do not relax it.

    PII note: the ``user_name`` string becomes ``caller_identity``, which
    the idempotency middleware logs prefix-truncated at DEBUG. If your auth
    layer sets ``user_name`` to an email address, treat idempotency debug
    logs as containing PII. Prefer opaque principal IDs.
    """
    ctx = ToolContext(request_id=request.task_id)
    call_context = getattr(request, "call_context", None)
    user = getattr(call_context, "user", None)
    if user is not None:
        is_auth = getattr(user, "is_authenticated", False)
        user_name = getattr(user, "user_name", "") or ""
        if is_auth and user_name:
            ctx.caller_identity = user_name
    return ctx


# ------------------------------------------------------------------
# Task factory
# ------------------------------------------------------------------


def _make_task(
    context: RequestContext,
    *,
    state: TaskState,
    data: dict[str, Any] | None = None,
    message: str | None = None,
) -> Task:
    """Build an a2a Task event from context and result data."""
    parts: list[Part] = []
    if data is not None:
        parts.append(Part(root=DataPart(data=data)))
    if message:
        parts.append(Part(root=TextPart(text=message)))

    artifacts = []
    if parts:
        artifacts.append(
            Artifact(
                artifact_id=str(uuid4()),
                parts=parts,
            )
        )

    return Task(
        id=context.task_id or str(uuid4()),
        context_id=context.context_id or str(uuid4()),
        status=TaskStatus(state=state),
        artifacts=artifacts if artifacts else None,
    )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def _build_agent_card(
    handler: ADCPHandler,
    *,
    name: str,
    port: int,
    description: str | None = None,
    version: str = "1.0.0",
    extra_skills: list[AgentSkill] | None = None,
) -> AgentCard:
    """Build an A2A AgentCard from an ADCPHandler's tool definitions."""
    tool_defs = get_tools_for_handler(handler)

    skills = [
        AgentSkill(
            id=td["name"],
            name=td["name"],
            description=td.get("description", td["name"]),
            tags=["adcp"],
        )
        for td in tool_defs
    ]

    if extra_skills:
        skills.extend(extra_skills)

    return AgentCard(
        name=name,
        description=description or f"ADCP agent: {name}",
        url=f"http://localhost:{port}/",
        version=version,
        skills=skills,
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
    )


def create_a2a_server(
    handler: ADCPHandler,
    *,
    name: str = "adcp-agent",
    port: int | None = None,
    description: str | None = None,
    version: str = "1.0.0",
    test_controller: TestControllerStore | None = None,
) -> Any:
    """Create an A2A Starlette application from an ADCP handler.

    Args:
        handler: An ADCPHandler subclass instance.
        name: Agent name shown in the A2A agent card.
        port: Port number (used in the agent card URL).
        description: Agent description for the agent card.
        version: Agent version string.
        test_controller: Optional TestControllerStore for storyboard testing.

    Returns:
        A Starlette app ready to be run with uvicorn.
    """
    from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication

    resolved_port = port or int(os.environ.get("PORT", "3001"))

    executor = ADCPAgentExecutor(handler, test_controller=test_controller)

    agent_card = _build_agent_card(
        handler,
        name=name,
        port=resolved_port,
        description=description,
        version=version,
        extra_skills=_test_controller_skills() if test_controller else None,
    )

    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    return a2a_app.build()


def _test_controller_skills() -> list[AgentSkill]:
    """Build A2A skill definition for comply_test_controller."""
    return [
        AgentSkill(
            id="comply_test_controller",
            name="comply_test_controller",
            description="Compliance test controller. Sandbox only, not for production use.",
            tags=["adcp", "testing"],
        )
    ]
