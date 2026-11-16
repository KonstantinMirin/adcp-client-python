"""Payload conformance for the ``property_ids`` adagents authorization variant.

An ``adagents.json`` authorization entry chooses how it delegates: by property
id, property tag, inline properties, publisher properties, signal id or signal
tag. This grades the ``property_ids`` arm against its wire fragment.
"""

from __future__ import annotations


def test_property_ids_variant_validates_its_wire_fragment() -> None:
    """The bare public symbol accepts the ``property_ids`` adagents fragment."""
    import adcp.types

    agent = adcp.types.AuthorizedAgents.model_validate(
        {
            "url": "https://agent.example.com",
            "authorized_for": "Premium display inventory",
            "authorization_type": "property_ids",
            "property_ids": ["homepage"],
        }
    )
    assert agent.authorization_type == "property_ids"
    assert [p.root for p in agent.property_ids] == ["homepage"]
