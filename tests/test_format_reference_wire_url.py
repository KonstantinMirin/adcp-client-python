"""A format reference keeps the ``agent_url`` bytes the wire delivered (#1384).

``migrated_format_option_id`` hashes ``str(ref.agent_url)`` exactly as received,
which is the cross-SDK algorithm the TypeScript parity fixture pins. A reference
that had passed through a generated model used to carry an ``AnyUrl``, which
normalizes ``https://creative.adcontextprotocol.org`` to a trailing-slash form,
so the same wire format hashed to two different option IDs depending on where
the reference came from.
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from adcp.canonical_formats.projection import migrated_format_option_id
from adcp.types._wire import WireAnyUrl
from adcp.types.base import WireUrl
from adcp.types.domains.core.format_id import FormatReferenceStructuredObject
from adcp.types.legacy import LegacyFormatId

_WIRE = {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_300x250_image"}


def test_model_derived_reference_hashes_to_the_wire_mapping_id() -> None:
    from_wire = migrated_format_option_id(dict(_WIRE))
    from_model = migrated_format_option_id(LegacyFormatId.model_validate(dict(_WIRE)))
    from_generated = migrated_format_option_id(
        FormatReferenceStructuredObject.model_validate(dict(_WIRE)).model_dump(mode="json")
    )
    assert from_wire == from_model == from_generated


def test_agent_url_round_trips_without_normalization() -> None:
    ref = LegacyFormatId.model_validate(dict(_WIRE))
    # The attribute is a WireAnyUrl -- the wire-preserving URL type, which has
    # the AnyUrl attribute API and serializes the text it was parsed from. That
    # is what fixes #1384; a bare ``str`` was one way of keeping the bytes and
    # this one keeps the parsed URL beside them. ``str()`` is what
    # ``migrated_format_option_id`` hashes, as this module's docstring says, so
    # ``str()`` is what the round trip is graded on.
    assert isinstance(ref.agent_url, WireAnyUrl)
    assert str(ref.agent_url) == "https://creative.adcontextprotocol.org"
    assert ref.model_dump(mode="json")["agent_url"] == "https://creative.adcontextprotocol.org"


@pytest.mark.parametrize("value", ["not a url", "", "creative.adcontextprotocol.org", 42])
def test_agent_url_is_still_url_validated(value: object) -> None:
    with pytest.raises(ValidationError):
        LegacyFormatId.model_validate({**_WIRE, "agent_url": value})


def test_wire_url_keeps_the_schema_format() -> None:
    assert TypeAdapter(WireUrl).json_schema() == {"type": "string", "format": "uri"}
    schema = FormatReferenceStructuredObject.model_json_schema()
    assert schema["properties"]["agent_url"]["format"] == "uri"
