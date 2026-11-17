"""The beta.14 object bridge must not widen the advertised mutation contract."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import TypeAdapter

from adcp.server.mcp_tools import (
    ADCP_TOOL_DEFINITIONS,
    _ensure_pydantic_schemas_applied,
    _inline_refs,
)
from adcp.types import TargetingOverlayInput

# ``packages`` is optional but not nullable on every request, so the
# advertised node is the array itself rather than an ``anyOf`` with a null branch
# (#1547; the canonical create/update redeclarations inherit the generated
# never-null marker since #1620).
_PACKAGE_PATH = ("properties", "packages", "items", "properties", "targeting_overlay")
_TARGETING_PATHS = {
    "create_media_buy": {_PACKAGE_PATH},
    "update_media_buy": {
        _PACKAGE_PATH,
        ("properties", "new_packages", "items", "properties", "targeting_overlay"),
    },
    "control_media_buy": {_PACKAGE_PATH},
    "buy_products": {("properties", "purchases", "items", "properties", "targeting_overlay")},
}


def _targeting_nodes(node: Any, path: tuple[str | int, ...] = ()):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "targeting_overlay":
                yield (*path, key), value
            yield from _targeting_nodes(value, (*path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _targeting_nodes(value, (*path, index))


@pytest.mark.parametrize("tool", _TARGETING_PATHS)
def test_advertised_targeting_mutations_keep_input_only_schema(tool: str) -> None:
    # Exercise the actual lazy tools/list registry, not just an isolated
    # TypeAdapter. The session fixture also invokes this with every tool.
    _ensure_pydantic_schemas_applied(_TARGETING_PATHS)
    advertised = next(t["inputSchema"] for t in ADCP_TOOL_DEFINITIONS if t["name"] == tool)
    # Compact discovery may retain local references. Resolve them before
    # comparing the semantic input surface and its historical use-site paths.
    nodes = dict(_targeting_nodes(_inline_refs(advertised)))
    assert nodes.keys() == _TARGETING_PATHS[tool], tool

    # Independent mutation-only reference. The overlay property is optional,
    # not nullable: the bundled schema declares the input shape with no null
    # branch, and the advertised node now states the same (#1547), so the
    # reference is the input shape itself.
    #
    # The create/update graphs were previously passed through
    # `adcp.types.canonical_creative.sanitize_canonical_schema`, which stripped
    # the nested creative identities the old emission carried into them.
    # `__adcp_refused__["canonical_creative"]` declares that module
    # UNRESOLVABLE-UPSTREAM; the overlay's own graph states no such identity
    # here, so the reference is compared unsanitised for every tool and the
    # assertions below are what prove that.
    expected = _inline_refs(TypeAdapter(TargetingOverlayInput).json_schema())
    assert expected["title"] == "TargetingOverlayInput"
    assert expected["type"] == "object"

    for path, node in nodes.items():
        assert set(node) == {
            "additionalProperties",
            "default",
            "description",
            "properties",
            "title",
            "type",
        }, (tool, path)
        # Inlining the reference merges the input object into the field node;
        # the field keeps its own title and description. Pin the keys rather
        # than permitting an arbitrary amount of metadata around the object.
        assert node["title"] == "Targeting Overlay", (tool, path)
        assert node["type"] == "object", (tool, path)
        assert node["properties"] == expected["properties"], (tool, path)
        assert node["additionalProperties"] == expected["additionalProperties"], (tool, path)
        assert node["default"] is None
        assert isinstance(node["description"], str)
        actual_bytes = json.dumps(node, sort_keys=True).encode()
        mutation_bytes = json.dumps(expected, sort_keys=True).encode()
        # Retain a budget for the generated description as well as pinning
        # the exact metadata keys/title above.
        assert len(actual_bytes) <= len(mutation_bytes) + 2048, (tool, path)
        assert b'"title": "TargetingOverlay"' not in actual_bytes, (tool, path)


def _advertised_description(field: dict[str, Any]) -> str | None:
    """The description a buyer reads off one advertised field node.

    An optional, nullable field advertises as ``{"anyOf": [<the shape>, {"type":
    "null"}], "default": null}``, and the shape's own ``description`` sits on the
    branch rather than on the node holding the ``anyOf``. Both positions are the
    one field's documentation as a reader meets it, so both are looked at here.
    """
    if "description" in field:
        return str(field["description"])
    for branch in field.get("anyOf", ()):
        if isinstance(branch, dict) and "description" in branch:
            return str(branch["description"])
    return None


def test_advertised_targeting_fields_carry_the_description_the_schema_declares() -> None:
    """A buyer reading tools/list sees each targeting field documented.

    ``core/targeting-input.json`` points at ``core/targeting.json``'s properties,
    and every one of those properties declares a ``description``. A generated
    wrapper per pointed-to position moved the description onto the wrapper's own
    definition and left the field node bare, so the advertised input schema
    documented 5 of the 37 targeting fields, and ten stayed bare after the fix.

    All 37 are documented now, and the list of exceptions is gone rather than
    shortened. The ten were the fields whose schema is a whole-file ``$ref``:
    pydantic put the description on the referenced definition and inlining the
    reference replaced the node that carried it. This emission states each
    optional field as an ``anyOf`` over the shape and ``null``, so the shape's
    description travels on its own branch and ``_inline_refs`` has nothing left
    to overwrite.
    """
    _ensure_pydantic_schemas_applied(_TARGETING_PATHS)
    advertised = next(
        t["inputSchema"] for t in ADCP_TOOL_DEFINITIONS if t["name"] == "create_media_buy"
    )
    overlay = next(iter(dict(_targeting_nodes(_inline_refs(advertised))).values()))
    fields = overlay["properties"]

    assert set(fields) == set(
        TargetingOverlayInput.model_json_schema()["properties"]
    ), "advertised fields drifted from the model"
    assert len(fields) == 37
    assert [name for name, field in fields.items() if not _advertised_description(field)] == []
