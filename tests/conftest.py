from __future__ import annotations

from types import UnionType
from typing import Any

import pytest
from pydantic import TypeAdapter

# Import the a2a-sdk 1.0 compat shim early so monkey-patches like
# ``Role.user = ROLE_USER`` and ``TaskStatus.__init__`` string coercion
# land before any test module constructs those proto types.
from tests import a2a_compat_shim as _a2a_compat_shim  # noqa: F401


@pytest.fixture(autouse=True)
def _a2a_compat_send_and_aggregate(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Patch :meth:`A2AAdapter._send_and_aggregate` for unit tests only.

    The 1.0 ``Client.send_message`` is an async generator but the
    unit-test suite mocks it with ``AsyncMock(return_value=...)`` (the
    0.3 shape). The shim shortcuts the iterator drain so unit tests
    keep their original mock return values. Integration tests talk to
    a real a2a-sdk server and must NOT be shimmed — they rely on the
    genuine async-generator contract.
    """
    if "integration" in request.node.nodeid:
        return
    _a2a_compat_shim.patch_send_and_aggregate(monkeypatch)


_adapter_cache: dict[type | UnionType, TypeAdapter[Any]] = {}


def validate_union(tp: type | UnionType, data: dict[str, Any]) -> Any:
    """Validate data against a type (handles both classes and union type aliases).

    Caches TypeAdapter instances to avoid repeated schema compilation.
    """
    try:
        adapter = _adapter_cache[tp]
    except KeyError:
        _adapter_cache[tp] = adapter = TypeAdapter(tp)
    return adapter.validate_python(data)
