"""Payload conformance for the ``property_ids`` adagents authorization branch.

An ``adagents.json`` authorization entry chooses how it delegates: by property
id, property tag, inline properties, publisher properties, signal id or signal
tag. This grades the ``property_ids`` branch against its wire fragment.

``AuthorizedAgents`` was the previous generator's word for it. The branch's
declaring position is ``adagents.json#/oneOf/1/properties/authorized_agents/
items/oneOf/0``, and the surface names it from that position --
``adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds``.
"""

from __future__ import annotations

from adcp.types.adagents import (
    AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds,
)


def test_property_ids_branch_validates_its_wire_fragment() -> None:
    agent = (
        AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds.model_validate(
            {
                "url": "https://agent.example.com",
                "authorized_for": "Premium display inventory",
                "authorization_type": "property_ids",
                "property_ids": ["homepage"],
            }
        )
    )
    assert agent.authorization_type == "property_ids"
    # A property id is a scalar root, so it is its own `str` and carries no
    # `.root` wrapper (`rebuild-plan.md` §4: a scalar at a root is an alias).
    assert agent.property_ids == ["homepage"]
