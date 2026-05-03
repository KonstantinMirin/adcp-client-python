"""Smoke + structural tests for the :mod:`adcp.decisioning.capabilities` submodule.

The submodule sits between the disambiguated forms in
:mod:`adcp.types.capabilities` (where ``Account`` / ``MediaBuy`` /
``Creative`` are aliased to ``Capabilities*`` to avoid colliding with
the unrelated wire types in :mod:`adcp.types`) and the adopter-facing
import path. Adopter code reads against the AdCP wire spec, so the
submodule re-aliases the disambiguated forms back to the wire-spec names.

These tests guard the alias mapping — if the disambiguation drifts (for
example, codegen renames a sub-model and the alias goes stale), the
import fails here before adopters hit it.
"""

from __future__ import annotations

import pytest


def test_wire_spec_names_resolve_in_submodule() -> None:
    """Adopter-facing names match the AdCP wire spec field types 1:1."""
    from adcp.decisioning.capabilities import (
        Account,
        Adcp,
        Creative,
        IdempotencySupported,
        IdempotencyUnsupported,
        MediaBuy,
        Targeting,
    )

    # Spot-check a few — full surface is covered by ``__all__``.
    assert Account.__name__ == "Account"
    assert MediaBuy.__name__ == "MediaBuy"
    assert Creative.__name__ == "Creative"
    assert Adcp.__name__ == "Adcp"
    assert Targeting.__name__ == "Targeting"
    assert IdempotencySupported.__name__ == "Idempotency"  # the supported variant
    assert IdempotencyUnsupported.__name__ == "Idempotency3"  # the unsupported variant


def test_capability_sub_models_construct() -> None:
    """Typical declarations produce well-formed Pydantic instances.

    Validates that the pieces an adopter would compose into a
    ``DecisioningCapabilities`` declaration work as Pydantic models —
    construction, field access, ``model_dump``.
    """
    from adcp.decisioning.capabilities import (
        Account,
        Execution,
        GeoMetros,
        IdempotencySupported,
        Specialism,
        Targeting,
    )

    idempotency = IdempotencySupported(supported=True, replay_ttl_seconds=86400)
    assert idempotency.replay_ttl_seconds == 86400

    geo_metros = GeoMetros(nielsen_dma=True, eurostat_nuts2=False)
    assert geo_metros.nielsen_dma is True

    targeting = Targeting(geo_countries=True, geo_metros=geo_metros)
    assert targeting.geo_countries is True
    assert targeting.geo_metros is not None
    assert targeting.geo_metros.nielsen_dma is True

    execution = Execution(targeting=targeting)
    dump = execution.model_dump(mode="json", exclude_none=True)
    assert dump == {
        "targeting": {
            "geo_countries": True,
            "geo_metros": {"nielsen_dma": True, "eurostat_nuts2": False},
        },
    }

    account = Account(supported_billing=["operator"])
    billing = [b.value if hasattr(b, "value") else b for b in account.supported_billing]
    assert billing == ["operator"]

    # Specialism is the wire enum; .value matches the AdCP slug form.
    assert Specialism.sales_non_guaranteed.value == "sales-non-guaranteed"


def test_wire_account_and_capabilities_account_are_distinct() -> None:
    """Guard against a future regression where the colliding names get conflated.

    The wire ``Account`` (from :mod:`adcp.types`) and the capabilities
    ``Account`` (from :mod:`adcp.decisioning.capabilities`) are different
    Pydantic classes describing different parts of AdCP. The alias
    plumbing in :mod:`adcp.types.capabilities` is the only thing keeping
    them apart in the public API; if it drifts, this fails.
    """
    from adcp.decisioning.capabilities import Account as CapabilitiesAccount
    from adcp.types import Account as WireAccount

    assert CapabilitiesAccount is not WireAccount
    assert CapabilitiesAccount.__module__.endswith("get_adcp_capabilities_response")


def test_idempotency_union_halves_round_trip_distinctly() -> None:
    """``IdempotencySupported`` and ``IdempotencyUnsupported`` are the two
    arms of the AdCP idempotency oneOf — adopters pick one at declaration
    time and the wire shape differs accordingly. The supported arm
    requires ``replay_ttl_seconds``; the unsupported arm forbids it.
    """
    from adcp.decisioning.capabilities import IdempotencySupported, IdempotencyUnsupported

    supported = IdempotencySupported(supported=True, replay_ttl_seconds=3600)
    assert supported.model_dump(mode="json")["supported"] is True
    assert supported.model_dump(mode="json")["replay_ttl_seconds"] == 3600

    unsupported = IdempotencyUnsupported(supported=False)
    dump = unsupported.model_dump(mode="json", exclude_none=True)
    assert dump == {"supported": False}
    # The schema's "not required: replay_ttl_seconds" invariant — the
    # unsupported arm should not even surface the field.
    assert "replay_ttl_seconds" not in dump

    # Wire validation: supported arm rejects missing replay_ttl_seconds.
    with pytest.raises(
        Exception
    ):  # noqa: PT011 — Pydantic ValidationError, broad to avoid coupling
        IdempotencySupported(supported=True)  # type: ignore[call-arg]


def test_submodule_all_matches_imports() -> None:
    """``__all__`` is the public contract — guard against drift from
    actual exports."""
    import adcp.decisioning.capabilities as caps

    for name in caps.__all__:
        assert hasattr(caps, name), f"__all__ lists {name!r} but it is not importable"
