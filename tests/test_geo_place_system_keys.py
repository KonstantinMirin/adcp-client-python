"""Place-system map keys stay validated opaque strings, including through parents (#1450)."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, get_args

import pytest

# There is no `adcp.types.domains.bundled`. It was a SECOND generated tree, and
# the four `bundled-*` cases below were the same claims put to its copy of each
# class. One bundle compiles to one tree here -- section 4's one class per
# SUBJECT -- so those cases were the same object twice.
from adcp.types.domains.core.geo_place_requirement import GeographicPlaceRequirement
from adcp.types.domains.core.geo_place_system import GeographicPlaceIdentifierSystem
from adcp.types.domains.core.targeting_overlay_support import PlaceSupport, TargetingOverlaySupport
from adcp.types.domains.protocol.get_adcp_capabilities_response import Targeting
from pydantic import BaseModel, ValidationError

from adcp.types import GetAdcpCapabilitiesResponse, GetProductsRequest, GetProductsResponse, Product

_COUNTRIES = {"US": ["city"]}
_SUPPORT = {"countries": _COUNTRIES, "current_version": "v1", "system_versions": ["v1"]}
_CAPABILITY = {
    "countries": _COUNTRIES,
    "catalog": {
        "current_version": "v1",
        "supported_versions": ["v1"],
        # `core/geo-place-resolver.json` requires all three of `url`, `auth` and
        # `protocol`; the last is a `const` naming the resolver contract version.
        "resolver": {
            "url": "https://seller.example/resolve",
            "auth": "none",
            "protocol": "adcp_geo_place_resolver_v1",
        },
    },
}
_MODELS = [
    pytest.param(PlaceSupport, "systems", _SUPPORT, id="support"),
    pytest.param(
        GeographicPlaceRequirement, "systems", {"countries": _COUNTRIES}, id="requirement"
    ),
    pytest.param(Targeting, "geo_places", _CAPABILITY, id="capabilities"),
]
def _registered_systems() -> list[str]:
    """The tokens `core/geo-place-system.json` registers, read off the annotation.

    The document states the system as a `oneOf` of a token enum and an HTTPS
    URI. `GeographicPlaceIdentifierSystem1` was the enum half as its own class;
    this emission lowers the node to one `Annotated` union, so the tokens are
    the `Literal`'s own arguments and there is no member object to take a
    `.value` off -- the key is already the plain string the wire carries.
    """
    for part in get_args(get_args(GeographicPlaceIdentifierSystem)[0]):
        tokens = get_args(part)
        if tokens and all(isinstance(token, str) for token in tokens):
            return list(tokens)
    raise AssertionError("no registered-token Literal in GeographicPlaceIdentifierSystem")


_REGISTERED_SYSTEMS = _registered_systems()

_SYSTEMS = [
    "geonames",
    "google_ads",
    "microsoft_ads",
    "https://seller.example",
    "https://SELLER.example:443/places/%7eCity?version=v1#Catalog",
]


def test_cold_schema_imports_validate_without_flat_surface_initialization() -> None:
    cases = [
        (model.__module__, model.__name__, field, value)
        for model, field, value in (
            (PlaceSupport, "systems", _SUPPORT),
            (GeographicPlaceRequirement, "systems", {"countries": _COUNTRIES}),
            (Targeting, "geo_places", _CAPABILITY),
        )
    ]
    script = """
import importlib
import json
import sys
from pydantic import ValidationError
for module, name, field, value in json.loads(sys.argv[1]):
    model = getattr(importlib.import_module(module), name)
    for key in ('geonames', 'https://SELLER.example:443/places/%7eCity'):
        result = model.model_validate_json(json.dumps({field: {key: value}}))
        assert list(json.loads(result.model_dump_json())[field]) == [key]
    try:
        model.model_validate({field: {'http://seller.example/places': value}})
    except ValidationError:
        pass
    else:
        raise AssertionError('HTTP place-system key accepted')
print('cold schema imports passed')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, json.dumps(cases)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert "cold schema imports passed" in result.stdout


# The two key-rewrite tests that stood here graded
# `scripts.post_generate_fixes.preserve_geo_place_system_map_keys`, a
# post-generate text rewrite that retyped the map key to
# `adcp.types.base.GeoPlaceSystemKey` after the previous generator had written
# `dict[GeographicPlaceIdentifierSystem, ...]`. There is no such pass here: the
# compiler lowers `core/geo-place-system.json`'s own `anyOf` into the key type
# directly, so there is no generated spelling to rewrite and no second
# `bundled/` tree to rewrite it in. Their only subject was that layer.


@pytest.mark.parametrize("model,field,value", _MODELS)
@pytest.mark.parametrize("system", _SYSTEMS)
@pytest.mark.parametrize("from_json", [False, True], ids=["python", "json"])
def test_system_keys_round_trip(
    model: type[BaseModel], field: str, value: dict[str, Any], system: str, from_json: bool
) -> None:
    data = {field: {system: value}}
    result = (
        model.model_validate_json(json.dumps(data)) if from_json else model.model_validate(data)
    )
    # The document states the system as an `anyOf` of a token enum and an
    # `^https://` URI, so a registered token validates to a plain `str` and a
    # URI validates to the URL type the `format: uri` branch selects. On the
    # PYTHON side a URI key is therefore a `WireAnyUrl`, whose `str()` is the
    # text as received -- which is what "compared as exact opaque strings" asks
    # for. The wire side is `str` either way, and that is where the round trip
    # is graded.
    keys = list(getattr(result, field))
    assert [str(key) for key in keys] == [system]
    assert [str(key) for key in result.model_dump(mode="python")[field]] == [system]
    assert list(result.model_dump(mode="json")[field]) == [system]
    assert list(json.loads(result.model_dump_json())[field]) == [system]
    assert model.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("model,field,value", _MODELS)
@pytest.mark.parametrize("system", _REGISTERED_SYSTEMS)
def test_registered_enum_keys_become_plain_strings(
    model: type[BaseModel],
    field: str,
    value: dict[str, Any],
    system: str,
) -> None:
    result = model.model_validate({field: {system: value}})
    key = next(iter(getattr(result, field)))
    assert type(key) is str
    assert key == system


@pytest.mark.parametrize("model,field,value", _MODELS)
@pytest.mark.parametrize(
    "system",
    [
        "http://seller.example/places",
        "ftp://seller.example",
        "unknown",
        "",
        "https://",
        "HTTPS://seller.example/places",
        "Https://seller.example/places",
        " https://seller.example/places",
        "https:\\seller.example/places",
    ],
)
@pytest.mark.parametrize("from_json", [False, True], ids=["python", "json"])
def test_invalid_system_keys_raise_validation_errors(
    model: type[BaseModel], field: str, value: dict[str, Any], system: str, from_json: bool
) -> None:
    data = {field: {system: value}}
    with pytest.raises(ValidationError):
        if from_json:
            model.model_validate_json(json.dumps(data))
        else:
            model.model_validate(data)


@pytest.mark.parametrize("model,field,value", _MODELS)
def test_nonempty_map_constraint_is_preserved(
    model: type[BaseModel], field: str, value: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({field: {}})
    schema = model.model_json_schema()["properties"][field]
    assert schema.get("minProperties") == 1 or any(
        branch.get("minProperties") == 1 for branch in schema.get("anyOf", [])
    )


@pytest.mark.parametrize("system", ["geonames", "https://SELLER.example:443/places/%7eCity"])
@pytest.mark.parametrize("field", ["geo_places", "geo_places_exclude"])
@pytest.mark.parametrize("from_json", [False, True], ids=["python", "json"])
def test_overlay_product_and_discovery_parents(system: str, field: str, from_json: bool) -> None:
    overlay = {field: {"systems": {system: _SUPPORT}}}
    product = {
        "product_id": "places",
        "name": "Places",
        "description": "Place targeting",
        "publisher_properties": [{"selection_type": "all", "publisher_domain": "pub.example"}],
        "delivery_type": "non_guaranteed",
        "pricing_options": [
            {"pricing_model": "cpm", "pricing_option_id": "cpm", "currency": "USD"}
        ],
        "format_options": [
            {"format_option_id": "display", "format_kind": "display_tag", "params": {}}
        ],
        "reporting_capabilities": {
            "available_reporting_frequencies": ["daily"],
            "expected_delay_minutes": 0,
            "timezone": "UTC",
            "supports_webhooks": False,
            "available_metrics": ["impressions"],
            "date_range_support": "date_range",
        },
        "overlay_support": overlay,
    }
    cases = [
        (TargetingOverlaySupport, overlay, [field, "systems"]),
        (Product, product, ["overlay_support", field, "systems"]),
        (
            GetProductsResponse,
            {"products": [product]},
            ["products", 0, "overlay_support", field, "systems"],
        ),
        (
            GetProductsRequest,
            {
                "buying_mode": "brief",
                "required_overlay_support": {
                    field: {"systems": {system: {"countries": _COUNTRIES}}}
                },
            },
            ["required_overlay_support", field, "systems"],
        ),
    ]
    for model, data, path in cases:
        result = (
            model.model_validate_json(json.dumps(data)) if from_json else model.model_validate(data)
        )
        wire = json.loads(result.model_dump_json())
        for key in path:
            wire = wire[key]
        assert list(wire) == [system]


@pytest.mark.parametrize("model", [GetAdcpCapabilitiesResponse])
@pytest.mark.parametrize("system", ["geonames", "https://SELLER.example:443/places/%7eCity"])
@pytest.mark.parametrize("from_json", [False, True], ids=["python", "json"])
def test_full_capabilities_response(model: type[BaseModel], system: str, from_json: bool) -> None:
    data = {
        "status": "completed",
        "adcp": {"major_versions": [3], "idempotency": {"supported": False}},
        "supported_protocols": ["media_buy"],
        "media_buy": {"execution": {"targeting": {"geo_places": {system: _CAPABILITY}}}},
    }
    result = (
        model.model_validate_json(json.dumps(data)) if from_json else model.model_validate(data)
    )
    assert list(
        json.loads(result.model_dump_json())["media_buy"]["execution"]["targeting"]["geo_places"]
    ) == [system]
