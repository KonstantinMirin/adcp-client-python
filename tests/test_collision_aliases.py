"""Payload conformance for the ``list_creatives`` response row union.

AdCP 3.1.8 splits a listing row into a v1 named-format reference branch and a
v2 canonical ``format_kind`` branch. The choice is stated with no discriminator
keyword, so the branch is decided by ``format_id`` XOR ``format_kind``
presence: exactly one must be there. This grades that exactness by payload.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def _minimal_list_creative(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "creative_id": "cr_123",
        "name": "Medium Rectangle",
        "format_id": {
            "agent_url": "https://creative.example.com",
            "id": "display_300x250",
        },
        "status": "approved",
        "created_date": "2026-01-10T14:00:00Z",
        "updated_date": "2026-01-10T14:00:00Z",
    }
    payload.update(overrides)
    return payload


def _minimal_list_creatives_response(creative: dict[str, object]) -> dict[str, object]:
    return {
        "status": "completed",
        "query_summary": {"total_matching": 1, "returned": 1},
        "pagination": {"has_more": False, "total_count": 1},
        "creatives": [creative],
    }


def test_list_creatives_response_enforces_format_reference_xor() -> None:
    """Generated response rows must keep the schema oneOf exactness."""
    from adcp.types.domains.creative.list_creatives_response import ListCreativesResponse

    legacy = _minimal_list_creative()
    canonical = _minimal_list_creative(format_id=None, format_kind="image")
    canonical.pop("format_id")

    assert ListCreativesResponse.model_validate(_minimal_list_creatives_response(legacy))
    assert ListCreativesResponse.model_validate(_minimal_list_creatives_response(canonical))

    both = _minimal_list_creative(format_kind="image")
    neither = _minimal_list_creative(format_id=None)
    neither.pop("format_id")

    with pytest.raises(ValidationError):
        ListCreativesResponse.model_validate(_minimal_list_creatives_response(both))
    with pytest.raises(ValidationError):
        ListCreativesResponse.model_validate(_minimal_list_creatives_response(neither))
