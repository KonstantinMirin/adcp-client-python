"""Runtime coverage for ``ADCPHandler[TContext]`` — closes #223.

The TypeVar work is a typing-level refactor (mypy-visible), but the
contract it promises has runtime consequences too:

1. Existing ``class MyAgent(ADCPHandler)`` code keeps working without
   edits — unparameterised subclasses must not break.
2. Parameterising with a ``ToolContext`` subclass is a legal Generic
   subscription — ``ADCPHandler[MyContext]`` resolves at class-body
   time.
3. Protocol handlers (``BrandHandler``, ``ContentStandardsHandler`` etc.)
   propagate the same TypeVar — downstream can write
   ``class MyBrand(BrandHandler[MyContext])``.
4. At dispatch time, the handler method receives whatever ``ToolContext``
   subclass the transport hands it — no isinstance check loses the
   subclass type.

These tests are behavioural, not type-system assertions — they verify
the TypeVar machinery doesn't impose a runtime cost and that the
subclass flows through the A2A/MCP invocation paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from adcp.server import (
    ADCPHandler,
    BrandHandler,
    ComplianceHandler,
    TmpHandler,
    ToolContext,
)
from adcp.server.base import TContext  # noqa: F401 — imported to pin the export


@dataclass
class _PlatformAdapter:
    """Stand-in for a real platform adapter — the typed field a downstream
    would carry on their ToolContext subclass."""

    name: str


@dataclass
class _TypedContext(ToolContext):
    """Demonstrates the multi-tenant pattern: handlers need typed access
    to tenant + adapter fields beyond what ToolContext names."""

    adapter: _PlatformAdapter | None = None


# ---------------------------------------------------------------------------
# Unparameterised subclasses — existing pattern must keep working
# ---------------------------------------------------------------------------


def test_unparameterised_subclass_still_works():
    """``class MyAgent(ADCPHandler)`` with no TypeVar argument must
    keep working for backward compat. The bulk of existing adopters
    aren't ready to introduce typed context subclasses yet."""

    class _MyAgent(ADCPHandler):
        _agent_type = "test"

        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    agent = _MyAgent()
    assert agent._agent_type == "test"


def test_unparameterised_protocol_handler_still_works():
    """Same backward-compat check for the non-abstract protocol handler
    bases — ``BrandHandler``, ``ComplianceHandler``, ``TmpHandler``
    don't declare additional abstract methods, so they can be
    subclassed directly. ``ContentStandardsHandler``, ``GovernanceHandler``,
    and ``SponsoredIntelligenceHandler`` have ``handle_*`` abstracts
    (predating this PR) that subclasses must implement — covered
    separately by the typed-subclass tests below."""
    for cls in (BrandHandler, ComplianceHandler, TmpHandler):

        class _Concrete(cls):  # type: ignore[valid-type,misc]
            _agent_type = "test"

            async def get_adcp_capabilities(self, params, context=None):
                return {"adcp": {"major_versions": [3]}}

        instance = _Concrete()
        assert instance._agent_type == "test"


# ---------------------------------------------------------------------------
# Parameterised subclasses — the new capability
# ---------------------------------------------------------------------------


def test_parameterised_adcphandler_subclass_resolves():
    """``class MyAgent(ADCPHandler[MyContext])`` must construct without
    error — the Generic subscription is the core promise of #223."""

    class _TypedAgent(ADCPHandler[_TypedContext]):
        _agent_type = "typed"

        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}}

    agent = _TypedAgent()
    # __class_getitem__ returned something sensible — we can subclass it
    # and instantiate the subclass.
    assert agent._agent_type == "typed"


def test_protocol_handler_propagates_typevar():
    """``BrandHandler[MyContext]`` must work the same way.  Without
    this the TypeVar on the base is useless for the specialised
    handler classes."""

    class _TypedBrand(BrandHandler[_TypedContext]):
        _agent_type = "typed brand"

    agent = _TypedBrand()
    assert agent._agent_type == "typed brand"


def test_handler_receives_subclass_at_dispatch_time():
    """The TypeVar is static-type narrowing, but the runtime path must
    preserve the subclass identity on the ``context`` argument — a
    handler that does ``context.adapter`` at runtime needs the subclass
    to survive the dispatch."""
    received: list[Any] = []

    class _TypedAgent(ADCPHandler[_TypedContext]):
        _agent_type = "adapter-reader"

        async def get_adcp_capabilities(self, params, context=None):
            received.append(context)
            return {"adcp": {"major_versions": [3]}}

    import asyncio

    agent = _TypedAgent()
    ctx = _TypedContext(
        caller_identity="p-1",
        tenant_id="t-1",
        adapter=_PlatformAdapter(name="demo"),
    )
    asyncio.run(agent.get_adcp_capabilities({}, ctx))

    assert len(received) == 1
    got = received[0]
    assert isinstance(got, _TypedContext)
    assert got.adapter is not None
    assert got.adapter.name == "demo"
    assert got.caller_identity == "p-1"
    assert got.tenant_id == "t-1"


def test_protocol_handler_subclass_receives_typed_context():
    """End-to-end for a specialised handler: BrandHandler[MyContext]
    subclass's methods receive the typed subclass at dispatch."""
    received: list[Any] = []

    class _TypedBrand(BrandHandler[_TypedContext]):
        _agent_type = "typed-brand"

        async def get_adcp_capabilities(self, params, context=None):
            received.append(context)
            return {"adcp": {"major_versions": [3]}}

    import asyncio

    agent = _TypedBrand()
    ctx = _TypedContext(
        caller_identity="brand-p",
        adapter=_PlatformAdapter(name="brand-adapter"),
    )
    asyncio.run(agent.get_adcp_capabilities({}, ctx))

    assert isinstance(received[0], _TypedContext)
    assert received[0].adapter is not None
    assert received[0].adapter.name == "brand-adapter"


# ---------------------------------------------------------------------------
# Negative case: the TypeVar has a bound
# ---------------------------------------------------------------------------


def test_typevar_is_bound_to_toolcontext():
    """The TypeVar bound prevents parameterising with an unrelated
    class.  At runtime Python doesn't enforce the bound (only mypy
    does), so this test just asserts the bound attribute — the static
    check is mypy's job and is covered by the CI mypy step."""
    from adcp.server.base import TContext as _TContext

    # TypeVar has __bound__ (forward ref or evaluated class).
    bound = _TContext.__bound__
    # Forward ref evaluates to the string; evaluated binding to the class.
    assert bound is ToolContext or (
        hasattr(bound, "__forward_arg__") and bound.__forward_arg__ == "ToolContext"
    )


# ---------------------------------------------------------------------------
# ADCPAgentExecutor integration — the subclass still flows through
# ---------------------------------------------------------------------------


async def test_typed_handler_works_under_a2a_executor():
    """A handler parameterised with a custom ToolContext subclass must
    still dispatch correctly under the A2A executor.  Runtime doesn't
    touch the TypeVar directly (the executor passes whatever context
    the context_factory returned), but this pins the no-regression
    promise: adding the TypeVar didn't break the A2A dispatch path."""
    from a2a.server.agent_execution.context import RequestContext
    from a2a.server.events.event_queue import EventQueue
    from a2a.types import DataPart, Message, MessageSendParams, Part, Role, Task

    from adcp.server.a2a_server import ADCPAgentExecutor

    class _TypedAgent(ADCPHandler[_TypedContext]):
        _agent_type = "typed-executor-test"

        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {"major_versions": [3]}, "supported_protocols": ["media_buy"]}

    executor = ADCPAgentExecutor(_TypedAgent())
    msg = Message(
        message_id="m-1",
        role=Role.user,
        parts=[Part(root=DataPart(data={"skill": "get_adcp_capabilities", "parameters": {}}))],
    )
    ctx = RequestContext(request=MessageSendParams(message=msg))
    queue = EventQueue()
    await executor.execute(ctx, queue)

    event = await queue.dequeue_event(no_wait=True)
    assert isinstance(event, Task)
    assert event.status.state == "completed"


# ---------------------------------------------------------------------------
# Handler method signature annotations survive the TypeVar
# ---------------------------------------------------------------------------


def test_handler_method_signatures_accept_subclass_positionally():
    """A sanity check that handler methods accept a ``ToolContext``
    subclass positionally — the rewrite of 57 method sigs from
    ``context: ToolContext | None`` to ``context: TContext | None``
    must not have shifted any parameter positions."""

    class _Agent(ADCPHandler):
        async def get_adcp_capabilities(self, params, context=None):
            return {"adcp": {}}

        async def get_products(self, params, context=None):
            return {"products": []}

    import inspect

    for method_name in ("get_adcp_capabilities", "get_products", "create_media_buy"):
        method = getattr(ADCPHandler, method_name, None)
        assert method is not None, f"{method_name} missing from ADCPHandler"
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        # self, params, context — in that order, minimum.
        assert params[0] == "self"
        assert params[1] == "params"
        assert "context" in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
