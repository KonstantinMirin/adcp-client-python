"""Backward-compat tests for the country-fused postal-area shape.

AdCP 3.1.0-rc.10 restructured postal-area targeting: the inline
``{system, values}`` shape was replaced by the ``PostalArea`` union of a
native per-country branch (``{country, system, values}``) and a legacy branch
(``{system, values}`` with country-fused tokens like ``us_zip``). The legacy
branch is still stated by the document, so old construction code keeps
working.

``core/postal-area.json#/anyOf/1`` is that branch and the surface names it
``adcp.types.core.PostalAreaWithFusedSystem``. The flat ``adcp.types``
namespace binds no ``GeoPostalArea``: that word was the previous generator's
and no document states it.

These tests exercise the wire contract of the public ``PostalArea`` /
``TargetingOverlay`` types by payload: which shapes construct, what they dump
to, and which country/system pairs are refused.
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter

from adcp.types.core import PostalArea, PostalAreaWithFusedSystem, TargetingOverlay

_POSTAL_AREA_ADAPTER = TypeAdapter(PostalArea)

# The 11 country-fused tokens the legacy branch accepts.
LEGACY_TOKENS = [
    "us_zip",
    "us_zip_plus_four",
    "gb_outward",
    "gb_full",
    "ca_fsa",
    "ca_full",
    "de_plz",
    "fr_code_postal",
    "au_postcode",
    "ch_plz",
    "at_plz",
]


def test_old_construction_shape_still_works():
    """Constructing the old ``{system, values}`` shape succeeds."""
    area = PostalAreaWithFusedSystem(system="us_zip", values=["10001", "10002"])

    dumped = area.model_dump(mode="json")
    assert dumped == {"system": "us_zip", "values": ["10001", "10002"]}


@pytest.mark.parametrize("token", LEGACY_TOKENS)
def test_every_legacy_token_constructs(token: str):
    """All 11 fused tokens still construct on the legacy branch."""
    area = PostalAreaWithFusedSystem(system=token, values=["X1"])
    assert area.model_dump(mode="json") == {"system": token, "values": ["X1"]}


def test_constructed_value_validates_against_postalarea_union_legacy_branch():
    """The constructed legacy value validates through the PostalArea union.

    Passing the constructed instance preserves the legacy branch — the union
    resolves to the legacy ``{system, values}`` shape rather than injecting a
    spurious ``country``.
    """
    area = PostalAreaWithFusedSystem(system="gb_outward", values=["SW1A"])

    validated = _POSTAL_AREA_ADAPTER.validate_python(area)
    assert isinstance(validated, PostalAreaWithFusedSystem)
    # Legacy branch round-trips faithfully with no injected country field.
    assert validated.model_dump(mode="json") == {
        "system": "gb_outward",
        "values": ["SW1A"],
    }


def test_raw_legacy_value_round_trips_through_postalarea_adapter():
    """Raw mappings must select the legacy branch before native defaults apply."""
    validated = _POSTAL_AREA_ADAPTER.validate_python({"system": "us_zip", "values": ["10001"]})

    wire = _POSTAL_AREA_ADAPTER.dump_python(validated, mode="json")
    assert wire == {"system": "us_zip", "values": ["10001"]}
    reparsed = _POSTAL_AREA_ADAPTER.validate_python(wire)
    assert _POSTAL_AREA_ADAPTER.dump_python(reparsed, mode="json") == wire


def test_legacy_value_accepted_where_geo_postal_areas_used():
    """Legacy postal areas are accepted in ``TargetingOverlay.geo_postal_areas``."""
    overlay = TargetingOverlay(
        geo_postal_areas=[
            PostalAreaWithFusedSystem(system="us_zip", values=["10001"]),
            PostalAreaWithFusedSystem(system="gb_outward", values=["SW1A"]),
        ]
    )

    dumped = overlay.model_dump(mode="json", exclude_none=True)["geo_postal_areas"]
    assert dumped == [
        {"system": "us_zip", "values": ["10001"]},
        {"system": "gb_outward", "values": ["SW1A"]},
    ]


def test_raw_legacy_value_round_trips_in_targeting_overlay():
    overlay = TargetingOverlay(
        geo_postal_areas=[{"system": "us_zip", "values": ["10001"]}],
        geo_postal_areas_exclude=[{"system": "gb_outward", "values": ["SW1A"]}],
    )

    wire = overlay.model_dump(mode="json", exclude_none=True)
    assert wire["geo_postal_areas"] == [{"system": "us_zip", "values": ["10001"]}]
    assert wire["geo_postal_areas_exclude"] == [{"system": "gb_outward", "values": ["SW1A"]}]
    assert TargetingOverlay.model_validate(wire).model_dump(mode="json", exclude_none=True) == wire


@pytest.mark.parametrize(
    ("country", "system"),
    [
        ("US", "zip"),
        ("US", "zip_plus_four"),
        ("GB", "outward"),
        ("DE", "plz"),
        ("NL", "postal_code"),
        ("NL", "custom"),
    ],
)
def test_native_postal_country_system_pairs_round_trip(country: str, system: str):
    area = _POSTAL_AREA_ADAPTER.validate_python(
        {"country": country, "system": system, "values": ["example"]}
    )

    assert area.model_dump(mode="json") == {
        "country": country,
        "system": system,
        "values": ["example"],
    }


@pytest.mark.parametrize(
    ("country", "system"),
    [("US", "plz"), ("DE", "zip"), ("NL", "plz")],
)
def test_native_postal_country_system_mismatches_fail_closed(country: str, system: str):
    with pytest.raises(ValueError, match="postal system .* is not valid for country"):
        _POSTAL_AREA_ADAPTER.validate_python(
            {"country": country, "system": system, "values": ["example"]}
        )


def test_targeting_overlay_rejects_mismatched_postal_pair():
    with pytest.raises(ValueError, match="postal system 'plz' is not valid for country 'US'"):
        TargetingOverlay(geo_postal_areas=[{"country": "US", "system": "plz", "values": ["10001"]}])


def test_schema_validation_rejects_mismatched_postal_pair():
    from adcp.validation import validate_request

    outcome = validate_request(
        "get_products",
        {
            "buying_mode": "brief",
            "brief": "Find inventory",
            "targeting_overlay": {
                "geo_postal_areas": [{"country": "US", "system": "plz", "values": ["10001"]}]
            },
        },
        version="3.2.0-beta.5",
    )

    assert outcome.valid is False
    assert any(issue.pointer == "/targeting_overlay/geo_postal_areas/0" for issue in outcome.issues)
