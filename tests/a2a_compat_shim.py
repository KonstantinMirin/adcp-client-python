"""Shared test compat layer for a2a-sdk 1.0 proto types.

The test suite was written against the 0.3 Pydantic types
(``DataPart(data=...)``, ``TextPart(text=...)``, ``Part(root=...)``,
string ``state="completed"`` enums). The 1.0 SDK replaces these with
protobuf messages carrying a ``content`` oneof on ``Part`` and
``TASK_STATE_*`` int enums. Rather than scrub every test call site
this module exposes Pydantic-era names as factory shims that build the
1.0 proto shapes under the hood; tests ``from tests.a2a_compat_shim
import ...`` and keep their prior constructor forms.
"""

from __future__ import annotations

from typing import Any

from a2a import types as pb
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Value

__all__ = [
    "DataPart",
    "TextPart",
    "Part",
    "Message",
    "Task",
    "Artifact",
    "TaskStatus",
    "Role",
    "SendMessageSuccessResponse",
    "SendMessageRequest",
    "state_to_pb",
    "part_data_dict",
    "part_text",
    "StreamResponse",
    "StreamResponseFromTask",
    "patch_send_and_aggregate",
]


# --- Role enum backwards-compat aliases (attribute-level monkey-patch) ---
# ``Role.user`` / ``Role.agent`` didn't exist on the proto enum; tests
# referenced them verbatim. Adding them once here means every call site
# (``role=Role.user``) keeps compiling without per-file edits.
pb.Role.user = pb.Role.ROLE_USER  # type: ignore[attr-defined]
pb.Role.agent = pb.Role.ROLE_AGENT  # type: ignore[attr-defined]


# --- TaskState backwards-compat aliases ---
# Tests reference ``TaskState.working`` / ``TaskState.completed`` / etc.
# Proto enums don't have these symbol-shaped attributes; shim them in.
pb.TaskState.completed = pb.TaskState.TASK_STATE_COMPLETED  # type: ignore[attr-defined]
pb.TaskState.failed = pb.TaskState.TASK_STATE_FAILED  # type: ignore[attr-defined]
pb.TaskState.working = pb.TaskState.TASK_STATE_WORKING  # type: ignore[attr-defined]
pb.TaskState.submitted = pb.TaskState.TASK_STATE_SUBMITTED  # type: ignore[attr-defined]
pb.TaskState.input_required = pb.TaskState.TASK_STATE_INPUT_REQUIRED  # type: ignore[attr-defined]
pb.TaskState.auth_required = pb.TaskState.TASK_STATE_AUTH_REQUIRED  # type: ignore[attr-defined]
pb.TaskState.canceled = pb.TaskState.TASK_STATE_CANCELED  # type: ignore[attr-defined]
pb.TaskState.rejected = pb.TaskState.TASK_STATE_REJECTED  # type: ignore[attr-defined]
pb.TaskState.unknown = pb.TaskState.TASK_STATE_UNSPECIFIED  # type: ignore[attr-defined]


Role = pb.Role
Task = pb.Task
Artifact = pb.Artifact
TaskStatus = pb.TaskStatus


# --- Part factories that match the 0.3 constructor shapes ---


def DataPart(data: dict[str, Any]) -> pb.Part:  # noqa: N802 (0.3 fixture shim)
    value = Value()
    ParseDict(data, value)
    return pb.Part(data=value)


def TextPart(text: str) -> pb.Part:  # noqa: N802 (0.3 fixture shim)
    return pb.Part(text=text)


def Part(root: pb.Part) -> pb.Part:  # noqa: N802 (0.3 fixture shim)
    """0.3 wrapped every Part in ``Part(root=<DataPart|TextPart>)``; the
    1.0 proto ``Part`` *is* the thing itself. Identity shim."""
    return root


def Message(  # noqa: N802 (0.3 fixture shim)
    *,
    message_id: str,
    role: pb.Role.ValueType,
    parts: list[pb.Part],
    context_id: str | None = None,
    task_id: str | None = None,
) -> pb.Message:
    kwargs: dict[str, Any] = {"message_id": message_id, "role": role, "parts": parts}
    if context_id is not None:
        kwargs["context_id"] = context_id
    if task_id is not None:
        kwargs["task_id"] = task_id
    return pb.Message(**kwargs)


_STATE_STRING_MAP: dict[str, pb.TaskState.ValueType] = {
    "completed": pb.TaskState.TASK_STATE_COMPLETED,
    "failed": pb.TaskState.TASK_STATE_FAILED,
    "working": pb.TaskState.TASK_STATE_WORKING,
    "submitted": pb.TaskState.TASK_STATE_SUBMITTED,
    "input-required": pb.TaskState.TASK_STATE_INPUT_REQUIRED,
    "input_required": pb.TaskState.TASK_STATE_INPUT_REQUIRED,
    "auth-required": pb.TaskState.TASK_STATE_AUTH_REQUIRED,
    "auth_required": pb.TaskState.TASK_STATE_AUTH_REQUIRED,
    "canceled": pb.TaskState.TASK_STATE_CANCELED,
    "rejected": pb.TaskState.TASK_STATE_REJECTED,
    "unknown": pb.TaskState.TASK_STATE_UNSPECIFIED,
}


def state_to_pb(state: Any) -> pb.TaskState.ValueType:
    """Translate a 0.3 spec string (``"completed"``) to the 1.0 enum."""
    if isinstance(state, str):
        return _STATE_STRING_MAP[state]
    return state  # assume already a proto enum int


_original_taskstatus_init = pb.TaskStatus.__init__


def _taskstatus_init(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[no-untyped-def]
    """Allow ``TaskStatus(state="completed", timestamp="...")`` on a 1.0 proto.

    Protobuf's default ``__init__`` rejects string-typed enum values and
    requires a ``google.protobuf.Timestamp`` for the ``timestamp`` field;
    this shim translates the 0.3 spec shapes before delegating to the
    real initializer, so existing test call sites keep compiling.
    """
    state = kwargs.get("state")
    if isinstance(state, str):
        kwargs["state"] = _STATE_STRING_MAP[state]
    ts = kwargs.get("timestamp")
    if isinstance(ts, str) and ts:
        from google.protobuf.timestamp_pb2 import Timestamp

        proto_ts = Timestamp()
        try:
            proto_ts.FromJsonString(ts)
        except ValueError:
            # Fall back to dropping the timestamp — the test likely
            # passed a freeform string (e.g. "now") and we don't want
            # to fail construction over a side-kwarg.
            kwargs.pop("timestamp")
        else:
            kwargs["timestamp"] = proto_ts
    _original_taskstatus_init(self, *args, **kwargs)


pb.TaskStatus.__init__ = _taskstatus_init  # type: ignore[method-assign]


def part_data_dict(part: pb.Part) -> dict[str, Any] | None:
    """Return the dict payload of a Part if it carries a ``data`` oneof, else None."""
    if part.WhichOneof("content") != "data":
        return None
    value = MessageToDict(part.data)
    return value if isinstance(value, dict) else None


def part_text(part: pb.Part) -> str | None:
    if part.WhichOneof("content") != "text":
        return None
    return part.text


# --- send_message StreamResponse shim ---
#
# The 1.0 :class:`~a2a.client.Client.send_message` returns
# ``AsyncIterator[StreamResponse]``. The test suite was written against
# the 0.3 ``send_message`` that returned a ``SendMessageSuccessResponse``
# directly. The helpers below let tests keep the old mock surface —
# ``mock_client.send_message = AsyncMock(return_value=SendMessageSuccessResponse(result=task))``
# — while patching the adapter to unwrap it internally.


class SendMessageSuccessResponse:
    """Mimic the 0.3 ``SendMessageSuccessResponse`` for mock return values."""

    def __init__(self, result: pb.Task) -> None:
        self.result = result


def SendMessageRequest(message: pb.Message) -> pb.SendMessageRequest:  # noqa: N802
    # Mimics the 0.3 class constructor signature for existing test call sites.
    return pb.SendMessageRequest(message=message)


StreamResponse = pb.StreamResponse


def StreamResponseFromTask(task: pb.Task) -> pb.StreamResponse:  # noqa: N802
    # PascalCase factory mirrors 0.3 ``SendMessageSuccessResponse`` pattern.
    event = pb.StreamResponse()
    event.task.CopyFrom(task)
    return event


async def _fake_send_and_aggregate(self, client, request):  # type: ignore[no-untyped-def]
    """Drop-in replacement for :meth:`A2AAdapter._send_and_aggregate`.

    Reads ``client.send_message(request)`` as the 0.3 tests expect —
    returning a ``SendMessageSuccessResponse`` or plain ``pb.Task`` —
    and repackages it as the ``pb.StreamResponse`` the real adapter
    pulls off the wire.
    """
    response = await client.send_message(request)
    if hasattr(response, "result"):
        task = response.result
    else:
        task = response
    return StreamResponseFromTask(task)


def patch_send_and_aggregate(monkeypatch) -> None:
    """Monkey-patch :meth:`A2AAdapter._send_and_aggregate` with the shim."""
    from adcp.protocols import a2a as _a2a_mod

    monkeypatch.setattr(_a2a_mod.A2AAdapter, "_send_and_aggregate", _fake_send_and_aggregate)
