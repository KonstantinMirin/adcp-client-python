"""End-to-end HTTP integration tests for A2A contextId / taskId handling.

Spins up a real A2A Starlette app on localhost via uvicorn and drives
it with the SDK's ``ADCPClient``. These tests prove the wire-level
behavior — they are the counterpart to the mocked adapter tests in
``tests/test_protocols.py`` and the only thing that would catch
regressions in how the client actually serializes ``context_id`` /
``task_id`` onto the JSON-RPC ``message/send`` request.

Also guards the server-side session-scoping claim: a handler keyed on
``context_id`` would start seeing fresh buckets on every call if the
client stopped echoing the id — these tests would fire first.

Note on what the observer can see: the a2a-sdk's ``RequestContext``
auto-populates ``context_id`` / ``task_id`` server-side — it mints
one when the client sent nothing, so a server-side observer cannot
tell "client sent None" from "client sent X" by reading
``RequestContext.context_id`` alone. What it *can* prove is the
higher-value contract — that two turns on one ``ADCPClient`` land on
the *same* server-observed id, and that ``reset_context()`` produces
a *different* one. That's the buyer-visible semantic; the None-on-
first-wire detail is covered by the unit tests in
``tests/test_protocols.py``.
"""

from __future__ import annotations

import asyncio
import socket
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import pytest
import uvicorn
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

from adcp import ADCPClient
from adcp.server import ADCPHandler
from adcp.server.a2a_server import create_a2a_server
from adcp.types import AgentConfig, Protocol

# Starlette/uvicorn A2A integration requires Python 3.11+.
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="a2a-sdk starlette integration requires Python 3.11+",
)


class _EchoHandler(ADCPHandler):
    """Minimal handler for the happy-path tests — the assertions are at
    the protocol layer, not the handler. Returns empty payloads."""

    async def get_adcp_capabilities(self, params: Any, context: Any = None) -> dict[str, Any]:
        return {"adcp": {"major_versions": [3]}, "supported_protocols": ["media_buy"]}

    async def get_products(self, params: Any, context: Any = None) -> dict[str, Any]:
        return {"products": [{"id": "p1", "name": "Display"}]}

    async def create_media_buy(self, params: Any, context: Any = None) -> dict[str, Any]:
        return {"media_buy_id": "mb-1"}


class _Observer:
    """Captures the (context_id, task_id) the server saw on each
    incoming A2A message.

    Installed via the ``message_parser`` hook — the parser is invoked
    on every ``message/send`` with the full RequestContext. See the
    module docstring for what this observation point can and cannot
    prove.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []

    def parser(self, context: RequestContext) -> tuple[str | None, dict[str, Any]]:
        self.calls.append({"context_id": context.context_id, "task_id": context.task_id})
        # Reimplement the default DataPart(skill=..., parameters=...)
        # parse inline so we don't reach into executor internals.
        msg = context.message
        if msg is None:
            return None, {}
        for part in msg.parts:
            inner = part.root if hasattr(part, "root") else part
            if isinstance(inner, DataPart) and isinstance(inner.data, dict):
                skill = inner.data.get("skill")
                params = inner.data.get("parameters") or {}
                if skill and isinstance(params, dict):
                    return str(skill), params
        return None, {}


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@asynccontextmanager
async def _running_server(handler: ADCPHandler, observer: _Observer) -> AsyncIterator[str]:
    """Start an in-process uvicorn serving the A2A app, yield its base URL."""
    port = _pick_free_port()
    app = create_a2a_server(
        handler,
        name="integration-test-agent",
        port=port,
        message_parser=observer.parser,
    )
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    try:
        for _ in range(200):  # ~10s ceiling
            if server.started:
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("uvicorn failed to start within timeout")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await task


@pytest.mark.asyncio
async def test_two_calls_share_server_assigned_context_id():
    """Core contract: two sequential calls on one ADCPClient land on
    the server under the same context_id. If the client stopped
    echoing it, turn 2 would get a different server-minted id — the
    assertion that calls[0] == calls[1] catches that regression."""
    observer = _Observer()
    async with _running_server(_EchoHandler(), observer) as base_url:
        config = AgentConfig(
            id="ctx-test-agent",
            agent_uri=base_url,
            protocol=Protocol.A2A,
            auth_token="test",
        )
        async with ADCPClient(config) as client:
            assert client.context_id is None
            r1 = await client.adapter.get_products({"brief": "x"})
            assert r1.success, r1.error
            # After turn 1 the client has captured the server's id.
            assert client.context_id is not None
            captured_after_turn_1 = client.context_id

            r2 = await client.adapter.create_media_buy({"budget": 1000})
            assert r2.success, r2.error

    assert len(observer.calls) == 2
    # The server saw the same context_id on both turns — this proves
    # session continuity end-to-end. The server is authoritative, so
    # this value is what any handler keyed on context_id would scope to.
    assert observer.calls[0]["context_id"] == observer.calls[1]["context_id"]
    # And that server-observed id matches what the client captured.
    assert observer.calls[1]["context_id"] == captured_after_turn_1


@pytest.mark.asyncio
async def test_reset_context_produces_new_server_side_session():
    """After ``reset_context()``, the next call must land on a
    different server-side context than the one before. If reset were a
    no-op the two server-observed ids would match and this would fire."""
    observer = _Observer()
    async with _running_server(_EchoHandler(), observer) as base_url:
        config = AgentConfig(
            id="ctx-test-agent",
            agent_uri=base_url,
            protocol=Protocol.A2A,
            auth_token="test",
        )
        async with ADCPClient(config) as client:
            await client.adapter.get_products({"brief": "x"})
            client.reset_context()
            assert client.context_id is None
            await client.adapter.get_products({"brief": "y"})

    # Two distinct server-side sessions.
    assert observer.calls[0]["context_id"] != observer.calls[1]["context_id"]


@pytest.mark.asyncio
async def test_seeded_context_id_reaches_server_on_first_call():
    """Constructor seeding (``ADCPClient(context_id=...)``) — the
    resume-across-restart use case. The server sees the seeded id on
    turn 1 with no round-trip, so a buyer rehydrating from persisted
    state lands on the same server-side session."""
    seed = f"buyer-seeded-{uuid4()}"
    observer = _Observer()
    async with _running_server(_EchoHandler(), observer) as base_url:
        config = AgentConfig(
            id="ctx-test-agent",
            agent_uri=base_url,
            protocol=Protocol.A2A,
            auth_token="test",
        )
        async with ADCPClient(config, context_id=seed) as client:
            assert client.context_id == seed
            r1 = await client.adapter.get_products({"brief": "x"})
            assert r1.success, r1.error

    assert observer.calls[0]["context_id"] == seed


# ---------------------------------------------------------------------------
# HITL / input-required resume — requires a custom AgentExecutor that emits
# a non-terminal task on the first call. ADCPAgentExecutor always emits
# terminal (completed/failed), so we drop down to the raw a2a-sdk here.
# ---------------------------------------------------------------------------


class _HitlExecutor(AgentExecutor):
    """Emits an ``input-required`` task on the first call, then a
    ``completed`` task on the second. Records what came in on the wire.
    """

    def __init__(self) -> None:
        self.observations: list[dict[str, str | None]] = []
        self._served = 0

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        self.observations.append(
            {
                "context_id": context.context_id,
                "task_id": context.task_id,
                "message_task_id": (context.message.task_id if context.message else None),
                "message_context_id": (context.message.context_id if context.message else None),
            }
        )
        self._served += 1
        if self._served == 1:
            state = TaskState.input_required
            text = "manager approval needed"
        else:
            state = TaskState.completed
            text = "approved"

        task = Task(
            id=context.task_id or str(uuid4()),
            context_id=context.context_id or str(uuid4()),
            status=TaskStatus(state=state),
            artifacts=[
                Artifact(
                    artifact_id=str(uuid4()),
                    parts=[
                        Part(root=TextPart(text=text)),
                        Part(root=DataPart(data={"approved": state == TaskState.completed})),
                    ],
                )
            ],
        )
        await event_queue.enqueue_event(task)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = Task(
            id=context.task_id or str(uuid4()),
            context_id=context.context_id or str(uuid4()),
            status=TaskStatus(state=TaskState.canceled),
        )
        await event_queue.enqueue_event(task)


def _make_hitl_app(executor: _HitlExecutor, port: int) -> Any:
    """Build a raw A2A Starlette app around the custom executor.

    The agent-card ``url`` must include the serving port — the client
    routes JSON-RPC POSTs to ``agent_card.url``, not to the base_url
    it passed to the resolver.
    """
    from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication

    card = AgentCard(
        name="hitl-test-agent",
        description="non-terminal-state test",
        url=f"http://127.0.0.1:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="create_media_buy",
                name="create_media_buy",
                description="create_media_buy",
                tags=["adcp"],
            )
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(agent_card=card, http_handler=handler).build()


@asynccontextmanager
async def _running_raw_server(
    executor: _HitlExecutor,
) -> AsyncIterator[str]:
    port = _pick_free_port()
    app = _make_hitl_app(executor, port)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    try:
        for _ in range(200):
            if server.started:
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("uvicorn failed to start within timeout")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await task


@pytest.mark.asyncio
async def test_task_id_echoed_on_resume_after_input_required():
    """HITL flow: server returns ``input-required`` on turn 1 → client
    auto-retains task_id → turn 2 carries both context_id and task_id
    so the server resumes the same task. Without task_id echo the
    server would orphan the pending HITL task."""
    executor = _HitlExecutor()
    async with _running_raw_server(executor) as base_url:
        config = AgentConfig(
            id="hitl-agent",
            agent_uri=base_url,
            protocol=Protocol.A2A,
            auth_token="test",
        )
        async with ADCPClient(config) as client:
            r1 = await client.adapter.create_media_buy({"budget": 1000})
            # After an input-required response the adapter stashed both ids.
            assert client.context_id is not None
            assert client.pending_task_id is not None
            retained_task_id = client.pending_task_id
            retained_context_id = client.context_id

            r2 = await client.adapter.create_media_buy({"approval": "yes"})
            # Terminal state on turn 2 cleared pending_task_id; context stays.
            assert client.pending_task_id is None
            assert client.context_id == retained_context_id

    assert len(executor.observations) == 2
    # Turn 1: both ids are server-generated (client sent nothing).
    # Turn 2: the client echoed the server's task_id back on the Message —
    # this is what resumes the pending HITL task server-side.
    assert executor.observations[1]["message_task_id"] == retained_task_id
    assert executor.observations[1]["message_context_id"] == retained_context_id
    # Sanity: r2 came back as completed.
    assert r2.success, r2.error
    _ = r1


@pytest.mark.asyncio
async def test_resume_across_simulated_restart_lands_on_same_session():
    """Persistence-across-restart story: client A establishes a
    session, persists its context_id, dies. Client B spins up, seeds
    with the persisted id, and its first call must carry that id so
    the server can reattach it to the original session."""
    observer = _Observer()
    async with _running_server(_EchoHandler(), observer) as base_url:
        config = AgentConfig(
            id="ctx-test-agent",
            agent_uri=base_url,
            protocol=Protocol.A2A,
            auth_token="test",
        )
        # Client A — establishes the session and "persists" the id.
        async with ADCPClient(config) as client_a:
            await client_a.adapter.get_products({"brief": "x"})
            persisted_context_id = client_a.context_id
            assert persisted_context_id is not None

        # Client B — different instance, seeds from persisted state.
        async with ADCPClient(config, context_id=persisted_context_id) as client_b:
            await client_b.adapter.create_media_buy({"budget": 1000})

    # Both server-observed calls share the same context_id.
    assert observer.calls[0]["context_id"] == observer.calls[1]["context_id"]
    assert observer.calls[1]["context_id"] == persisted_context_id
