from __future__ import annotations

from types import UnionType
from typing import Any

from pydantic import TypeAdapter

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
