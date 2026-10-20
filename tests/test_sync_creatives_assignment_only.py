"""AdCP 3.2 can traffic existing creatives without uploading assets (#1545)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from adcp.server.base import ADCPHandler, ToolContext
from adcp.server.mcp_tools import create_tool_caller
from adcp.types import CreativeAsset, SyncCreativesRequest
from adcp.validation import ValidationHookConfig, validate_request

_BASE = {
    "adcp_version": "3.2",
    "idempotency_key": "assignment-only-sync-0001",
    "account": {"account_id": "acct_1"},
}
_ASSIGNMENTS = {"assignments": [{"creative_id": "cr_1", "package_id": "pkg_1"}]}
_MUTATIONS = [
    pytest.param(_ASSIGNMENTS, id="assignments"),
    *[
        pytest.param(
            {
                "assignment_operations": [
                    {
                        "operation": operation,
                        "creative_id": "cr_1",
                        "package_id": "pkg_1",
                        **({"replaces_creative_id": "cr_old"} if operation == "replace" else {}),
                    }
                ]
            },
            id=operation,
        )
        for operation in ("assign", "unassign", "replace")
    ],
]


@pytest.mark.parametrize("mutation", _MUTATIONS)
@pytest.mark.parametrize("json_input", [False, True], ids=["python", "json"])
def test_public_model_accepts_assignment_only_sync(
    mutation: dict[str, Any], json_input: bool
) -> None:
    payload = {**_BASE, **mutation}
    request = (
        SyncCreativesRequest.model_validate_json(json.dumps(payload))
        if json_input
        else SyncCreativesRequest.model_validate(payload)
    )

    assert request.creatives is None
    wire = request.model_dump(mode="json", exclude_unset=True)
    assert wire == payload
    assert validate_request("sync_creatives", wire, version="3.2").valid


def test_empty_creatives_are_rejected_even_with_assignments() -> None:
    with pytest.raises(ValidationError) as caught:
        SyncCreativesRequest.model_validate({**_BASE, **_ASSIGNMENTS, "creatives": []})
    assert caught.value.errors()[0]["loc"] == ("creatives",)
    assert caught.value.errors()[0]["type"] == "too_short"


def test_sync_still_requires_assets_or_assignments() -> None:
    with pytest.raises(ValidationError) as caught:
        SyncCreativesRequest.model_validate(_BASE)
    assert caught.value.errors()[0]["type"] == "anyOf"


def test_asset_sync_still_parses_canonical_creatives() -> None:
    request = SyncCreativesRequest.model_validate(
        {
            **_BASE,
            "creatives": [
                {"creative_id": "cr_1", "name": "Banner", "format_kind": "image", "assets": {}}
            ],
        }
    )
    assert request.creatives is not None
    assert isinstance(request.creatives[0], CreativeAsset)
    assert request.creatives[0].format_kind == "image"


def test_public_schema_allows_omitting_creatives() -> None:
    assert "creatives" not in SyncCreativesRequest.model_json_schema()["required"]


class _AssignmentHandler(ADCPHandler[Any]):
    adcp_capabilities = {"media_buy": {"features": {"canonical_creatives": True}}}

    def __init__(self) -> None:
        self.received: SyncCreativesRequest | None = None

    async def sync_creatives(
        self, params: SyncCreativesRequest, context: ToolContext | None = None
    ) -> dict[str, Any]:
        self.received = params
        return {"creatives": []}


@pytest.mark.parametrize("mutation", _MUTATIONS)
async def test_assignment_only_sync_reaches_typed_handler(mutation: dict[str, Any]) -> None:
    handler = _AssignmentHandler()
    caller = create_tool_caller(
        handler, "sync_creatives", validation=ValidationHookConfig(requests="strict")
    )

    result = await caller({**_BASE, **mutation})

    assert result["creatives"] == []
    assert isinstance(handler.received, SyncCreativesRequest)
    assert handler.received.creatives is None
    assert handler.received.model_dump(mode="json", exclude_unset=True) == {**_BASE, **mutation}


@pytest.mark.parametrize("version", ["3.0", "3.1"])
def test_older_version_schemas_still_require_creatives(version: str) -> None:
    payload = {**_BASE, **_ASSIGNMENTS}
    payload.pop("adcp_version")
    outcome = validate_request("sync_creatives", payload, version=version)

    assert not outcome.valid
    assert any(
        issue.pointer == "/creatives" and issue.keyword == "required" for issue in outcome.issues
    )
