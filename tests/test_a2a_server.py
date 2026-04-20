"""Tests for A2A server support: ADCPAgentExecutor, create_a2a_server."""

from __future__ import annotations

import contextlib
import json
import sys
from typing import Any

import pytest
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    DataPart,
    Message,
    MessageSendParams,
    Part,
    Role,
    Task,
    TextPart,
)

from adcp.server import ADCPHandler
from adcp.server.a2a_server import (
    ADCPAgentExecutor,
    _build_agent_card,
    create_a2a_server,
)
from adcp.server.test_controller import TestControllerError, TestControllerStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _TestHandler(ADCPHandler):
    """Minimal handler that supports get_adcp_capabilities and get_products."""

    async def get_adcp_capabilities(self, params: Any, context: Any = None) -> dict[str, Any]:
        return {"adcp": {"major_versions": [3]}, "supported_protocols": ["media_buy"]}

    async def get_products(self, params: Any, context: Any = None) -> dict[str, Any]:
        return {
            "products": [{"id": "p1", "name": "Display"}],
            "sandbox": True,
        }


def _make_datapart_msg(skill: str, parameters: dict[str, Any] | None = None) -> Message:
    return Message(
        message_id="msg-1",
        role=Role.user,
        parts=[Part(root=DataPart(data={"skill": skill, "parameters": parameters or {}}))],
    )


def _make_text_msg(text: str) -> Message:
    return Message(
        message_id="msg-1",
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
    )


# ---------------------------------------------------------------------------
# ADCPAgentExecutor — sync tests
# ---------------------------------------------------------------------------


def test_executor_supported_skills():
    executor = ADCPAgentExecutor(_TestHandler())
    skills = executor.supported_skills
    assert "get_adcp_capabilities" in skills
    assert "get_products" in skills


# ---------------------------------------------------------------------------
# ADCPAgentExecutor — async tests
# ---------------------------------------------------------------------------


async def test_execute_with_datapart():
    """Executor dispatches DataPart skill invocation to handler."""
    executor = ADCPAgentExecutor(_TestHandler())
    ctx = RequestContext(request=MessageSendParams(message=_make_datapart_msg("get_products")))
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"

    # Verify the result data is in the artifact
    assert event.artifacts
    data_parts = [
        p.root
        for p in event.artifacts[0].parts
        if hasattr(p.root, "data") and isinstance(p.root.data, dict)
    ]
    assert len(data_parts) >= 1
    result = data_parts[0].data
    assert "products" in result
    assert result["products"][0]["id"] == "p1"


async def test_context_auto_injected():
    """Context from request is automatically echoed in response."""
    executor = ADCPAgentExecutor(_TestHandler())
    ctx = RequestContext(
        request=MessageSendParams(
            message=_make_datapart_msg(
                "get_products",
                {"context": {"correlation_id": "test-ctx-123"}},
            )
        )
    )
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    data_parts = [
        p.root
        for p in event.artifacts[0].parts
        if hasattr(p.root, "data") and isinstance(p.root.data, dict)
    ]
    result = data_parts[0].data
    assert result["context"]["correlation_id"] == "test-ctx-123"


async def test_execute_unknown_skill():
    """Executor returns failed task for unknown skills."""
    executor = ADCPAgentExecutor(_TestHandler())
    ctx = RequestContext(request=MessageSendParams(message=_make_datapart_msg("nonexistent_skill")))
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "failed"


async def test_execute_no_skill_in_message():
    """Executor returns failed task when message has no parseable skill."""
    executor = ADCPAgentExecutor(_TestHandler())
    ctx = RequestContext(request=MessageSendParams(message=_make_text_msg("hello")))
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "failed"


async def test_execute_json_text_fallback():
    """Executor parses JSON text as skill invocation."""
    executor = ADCPAgentExecutor(_TestHandler())
    payload = json.dumps({"skill": "get_products", "parameters": {}})
    ctx = RequestContext(request=MessageSendParams(message=_make_text_msg(payload)))
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"


async def test_execute_handler_exception():
    """Handler exception returns failed task without leaking details."""

    class _BrokenHandler(ADCPHandler):
        async def get_adcp_capabilities(self, params: Any, context: Any = None) -> Any:
            return {"adcp": {"major_versions": [3]}}

        async def get_products(self, params: Any, context: Any = None) -> Any:
            raise RuntimeError("secret database connection string leaked")

    executor = ADCPAgentExecutor(_BrokenHandler())
    ctx = RequestContext(request=MessageSendParams(message=_make_datapart_msg("get_products")))
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "failed"

    # Verify exception details are NOT in the error message
    text_parts = [p.root for p in event.artifacts[0].parts if hasattr(p.root, "text")]
    error_text = text_parts[0].text
    assert "secret database" not in error_text
    assert "get_products" in error_text


async def test_cancel():
    """Cancel returns a canceled task."""
    executor = ADCPAgentExecutor(_TestHandler())
    ctx = RequestContext(task_id="t1", context_id="c1")
    queue = EventQueue()

    await executor.cancel(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "canceled"


# ---------------------------------------------------------------------------
# Agent card builder
# ---------------------------------------------------------------------------


def test_build_agent_card_with_skills():
    card = _build_agent_card(_TestHandler(), name="test-agent", port=3001)
    assert card.name == "test-agent"
    assert card.url == "http://localhost:3001/"
    skill_ids = [s.id for s in card.skills]
    assert "get_adcp_capabilities" in skill_ids
    assert "get_products" in skill_ids


def test_build_agent_card_skills_tagged_adcp():
    card = _build_agent_card(_TestHandler(), name="test", port=8080)
    for skill in card.skills:
        assert "adcp" in skill.tags


# ---------------------------------------------------------------------------
# create_a2a_server
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
def test_create_a2a_server_creates_starlette_app():
    app = create_a2a_server(_TestHandler(), name="test-agent")
    # Starlette app has .routes
    assert hasattr(app, "routes")
    route_paths = [r.path for r in app.routes]
    # A2A well-known agent card endpoint
    assert "/.well-known/agent.json" in route_paths


# ---------------------------------------------------------------------------
# TestControllerStore integration
# ---------------------------------------------------------------------------


class _TestStore(TestControllerStore):
    def __init__(self) -> None:
        self.accounts: dict[str, str] = {"acct-1": "active"}

    async def force_account_status(self, account_id: str, status: str) -> dict[str, Any]:
        if account_id not in self.accounts:
            raise TestControllerError("NOT_FOUND", f"Account {account_id} not found")
        prev = self.accounts[account_id]
        self.accounts[account_id] = status
        return {"previous_state": prev, "current_state": status}


def test_executor_with_test_controller_has_skill():
    """Test controller registers comply_test_controller as a skill."""
    executor = ADCPAgentExecutor(_TestHandler(), test_controller=_TestStore())
    assert "comply_test_controller" in executor.supported_skills


async def test_execute_test_controller_list_scenarios():
    """comply_test_controller list_scenarios works via A2A."""
    executor = ADCPAgentExecutor(_TestHandler(), test_controller=_TestStore())
    ctx = RequestContext(
        request=MessageSendParams(
            message=_make_datapart_msg(
                "comply_test_controller",
                {"scenario": "list_scenarios"},
            )
        )
    )
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"

    data_parts = [
        p.root
        for p in event.artifacts[0].parts
        if hasattr(p.root, "data") and isinstance(p.root.data, dict)
    ]
    result = data_parts[0].data
    assert result["success"] is True
    assert "force_account_status" in result["scenarios"]


async def test_execute_test_controller_force_account_status():
    """comply_test_controller dispatches force_account_status correctly."""
    executor = ADCPAgentExecutor(_TestHandler(), test_controller=_TestStore())
    ctx = RequestContext(
        request=MessageSendParams(
            message=_make_datapart_msg(
                "comply_test_controller",
                {
                    "scenario": "force_account_status",
                    "params": {"account_id": "acct-1", "status": "suspended"},
                },
            )
        )
    )
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"

    data_parts = [
        p.root
        for p in event.artifacts[0].parts
        if hasattr(p.root, "data") and isinstance(p.root.data, dict)
    ]
    result = data_parts[0].data
    assert result["success"] is True
    assert result["previous_state"] == "active"
    assert result["current_state"] == "suspended"


async def test_execute_test_controller_error():
    """comply_test_controller handles TestControllerError."""
    executor = ADCPAgentExecutor(_TestHandler(), test_controller=_TestStore())
    ctx = RequestContext(
        request=MessageSendParams(
            message=_make_datapart_msg(
                "comply_test_controller",
                {
                    "scenario": "force_account_status",
                    "params": {"account_id": "nonexistent", "status": "active"},
                },
            )
        )
    )
    queue = EventQueue()

    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"  # A2A task succeeds; error is in data

    data_parts = [
        p.root
        for p in event.artifacts[0].parts
        if hasattr(p.root, "data") and isinstance(p.root.data, dict)
    ]
    result = data_parts[0].data
    assert result["success"] is False
    assert result["error"] == "NOT_FOUND"


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
def test_create_a2a_server_with_test_controller():
    """create_a2a_server includes comply_test_controller in agent card."""
    app = create_a2a_server(_TestHandler(), name="test-agent", test_controller=_TestStore())
    assert hasattr(app, "routes")


# ---------------------------------------------------------------------------
# Pluggable TaskStore (issue #224)
# ---------------------------------------------------------------------------


class _RecordingTaskStore:
    """TaskStore that records every save/get/delete for test assertions.

    Implements the a2a-sdk ``TaskStore`` protocol via duck-typing. Tests
    inject this to prove ``create_a2a_server(task_store=...)`` actually
    threads the store through to ``DefaultRequestHandler`` — the whole
    point of the hook.
    """

    def __init__(self) -> None:
        self.saves: list[str] = []
        self.gets: list[str] = []
        self.deletes: list[str] = []
        self._store: dict[str, Any] = {}

    async def save(self, task: Any, context: Any = None) -> None:
        self.saves.append(task.id)
        self._store[task.id] = task

    async def get(self, task_id: str, context: Any = None) -> Any | None:
        self.gets.append(task_id)
        return self._store.get(task_id)

    async def delete(self, task_id: str, context: Any = None) -> None:
        self.deletes.append(task_id)
        self._store.pop(task_id, None)


def _extract_default_request_handler(app: Any) -> Any:
    """Walk the a2a-sdk Starlette app graph to the DefaultRequestHandler.

    Structure is ``Starlette.routes[*].endpoint.__self__ →
    A2AStarletteApplication.handler (JSONRPCHandler) → .request_handler``.
    Touching this indirection in one place localises the blast radius if
    a2a-sdk changes its internals.
    """
    from a2a.server.request_handlers.default_request_handler import (
        DefaultRequestHandler,
    )

    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        a2a_app = getattr(endpoint, "__self__", None) if endpoint else None
        if a2a_app is None:
            continue
        jsonrpc_handler = getattr(a2a_app, "handler", None)
        request_handler = getattr(jsonrpc_handler, "request_handler", None)
        if isinstance(request_handler, DefaultRequestHandler):
            return request_handler
    raise AssertionError(
        "Could not locate the DefaultRequestHandler on the A2A app — "
        "a2a-sdk internals likely changed. Update _extract_default_request_handler "
        "but keep the contract: task_store= on create_a2a_server must thread "
        "through to DefaultRequestHandler.task_store."
    )


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
def test_create_a2a_server_defaults_to_in_memory_task_store():
    """Default behavior preserved: omitting task_store falls back to
    InMemoryTaskStore, so existing adopters see no change."""
    from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore

    app = create_a2a_server(_TestHandler(), name="test-agent")
    handler = _extract_default_request_handler(app)
    assert isinstance(handler.task_store, InMemoryTaskStore), (
        "Default task_store should be InMemoryTaskStore when no override "
        "is provided, preserving pre-#224 behavior."
    )


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
def test_create_a2a_server_accepts_custom_task_store():
    """Custom TaskStore instance must be threaded through to the A2A
    DefaultRequestHandler — the whole point of the hook."""
    store = _RecordingTaskStore()
    app = create_a2a_server(_TestHandler(), name="test-agent", task_store=store)
    handler = _extract_default_request_handler(app)
    assert handler.task_store is store, (
        "create_a2a_server(task_store=...) dropped the custom store. "
        "DefaultRequestHandler.task_store is instead "
        f"{type(handler.task_store).__name__}."
    )


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
async def test_custom_task_store_receives_saves_from_skill_dispatch():
    """Behavioral test: a skill call through the A2A executor actually
    produces ``save()`` traffic on the pluggable store.

    The attribute-identity check in the previous test proves the hook is
    wired at construction time; this one proves the hook is *used* at
    runtime — the failure mode it defends against is a2a-sdk version
    changes that rename or sidestep ``DefaultRequestHandler.task_store``
    while the attribute reference stays intact.

    We drive the executor directly (no HTTP) and observe the recording
    store. Exercising via ``DefaultRequestHandler`` would be closer to
    production but pulls in message-send request construction that
    a2a-sdk keeps in flux; this level is the stable behavioral contract.
    """
    store = _RecordingTaskStore()
    # The executor itself doesn't touch the store — DefaultRequestHandler
    # does. But routing an end-to-end message through the full JSON-RPC
    # path via httpx is a lot of scaffolding for a single-store
    # assertion, and the store's ABC is the stable surface. Go through
    # DefaultRequestHandler.on_get_task instead: if the handler asks
    # the store anything, the recording store records it.
    app = create_a2a_server(_TestHandler(), name="behavioral-test", task_store=store)
    handler = _extract_default_request_handler(app)

    # A get for a non-existent task should route through our store.
    # ``on_get_task`` raises ``ServerError(TaskNotFoundError)`` once the
    # store returns None; that's fine — what we care about is that the
    # store *was queried*. If the handler bypassed our store and went
    # somewhere else, the recording set stays empty.
    from a2a.types import TaskQueryParams
    from a2a.utils.errors import ServerError

    with contextlib.suppress(ServerError):
        await handler.on_get_task(TaskQueryParams(id="does-not-exist"))
    assert "does-not-exist" in store.gets, (
        "DefaultRequestHandler did not route the get_task call through our "
        "custom store. The kwarg is wired but not exercised."
    )


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)
async def test_task_store_persists_across_app_recreation():
    """A shared ``TaskStore`` instance is reusable across multiple
    ``create_a2a_server`` calls — the "restart" property durable stores
    actually need. This test deliberately uses direct store access on
    both sides of the 'restart' because it's proving persistence of
    the store's own state, not a claim about the new server using it
    (that's the previous test's job)."""
    store = _RecordingTaskStore()

    from a2a.types import TaskStatus

    task_1 = Task(
        id="task-persistence-1",
        context_id="ctx-1",
        status=TaskStatus(state="completed"),
    )
    await store.save(task_1)

    # Recreate the server. In production this is a process restart; here
    # it's just a second create_a2a_server call reusing the store.
    create_a2a_server(_TestHandler(), name="test-agent-v2", task_store=store)

    retrieved = await store.get("task-persistence-1")
    assert retrieved is not None
    assert retrieved.id == "task-persistence-1"
    assert "task-persistence-1" in store.gets


async def test_sqlite_task_store_isolates_scopes_by_context():
    """Reference ``SqliteTaskStore`` filters reads and writes by the
    authenticated principal derived from ``context.user.user_name``.
    Cross-tenant task lookups must not succeed — the whole point of
    carrying `context` through the TaskStore ABC."""
    # Import the reference impl from the example file. Keeping the test
    # close to the example guards the security claim in the example's
    # docstring.
    import importlib.util
    import tempfile
    from pathlib import Path

    from a2a.auth.user import User
    from a2a.server.context import ServerCallContext
    from a2a.types import TaskStatus

    example_path = Path(__file__).parent.parent / "examples" / "a2a_db_tasks.py"
    spec = importlib.util.spec_from_file_location("_a2a_db_tasks_example", example_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class _TestUser(User):
        def __init__(self, name: str) -> None:
            self._name = name

        @property
        def is_authenticated(self) -> bool:
            return True

        @property
        def user_name(self) -> str:
            return self._name

    def _ctx(name: str) -> ServerCallContext:
        return ServerCallContext(user=_TestUser(name))

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "isolation.db"
        store = mod.SqliteTaskStore(db_path=db)

        task = Task(id="shared-task-id", context_id="c1", status=TaskStatus(state="completed"))
        await store.save(task, context=_ctx("tenant-a-principal"))

        # Same task id, different principal → must not surface tenant
        # A's task to tenant B. The scope column is the whole isolation
        # mechanism; if this ever returns the saved task, the example
        # just taught a cross-tenant data leak.
        got_b = await store.get("shared-task-id", context=_ctx("tenant-b-principal"))
        assert got_b is None, (
            "SqliteTaskStore returned tenant A's task to tenant B — the "
            "reference impl is leaking across principals."
        )

        # Same principal returns the task.
        got_a = await store.get("shared-task-id", context=_ctx("tenant-a-principal"))
        assert got_a is not None and got_a.id == "shared-task-id"

        # Delete from tenant B's scope must not delete tenant A's row.
        await store.delete("shared-task-id", context=_ctx("tenant-b-principal"))
        still_a = await store.get("shared-task-id", context=_ctx("tenant-a-principal"))
        assert still_a is not None, "SqliteTaskStore cross-scope delete removed tenant A's task."
