"""Typed targeting composition across the rc.3 mutation boundaries (#1181)."""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

import pytest
from adcp.types.domains.core.targeting_input import TargetingOverlayInput as GeneratedInput
from adcp.types.domains.media_buy.package_control import PackageControl
from adcp.types.domains.media_buy.package_request import (
    PackageRequest as GeneratedPackageRequest,
)
from adcp.types.domains.media_buy.package_update import (
    PackageUpdate as GeneratedPackageUpdate,
)
from adcp.types.domains.media_buy.product_purchase_input import ProductPurchaseInput
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    TypeAdapter,
    ValidationError,
)

import adcp.types
from adcp._null_clear import preserve_explicit_nulls
from adcp.types import (
    BuyProductsRequest,
    ControlMediaBuyRequest,
    CreateMediaBuyRequest,
    LegacyCreateMediaBuyRequest,
    PackageRequest,
    PackageUpdate,
    UpdateMediaBuyRequest,
)
from adcp.types.base import is_no_explicit_null
from adcp.validation import validate_request

_NEW_PACKAGE = {"product_id": "product-1", "pricing_option_id": "price-1", "budget": 1000}
_EXISTING_PACKAGE = {"package_id": "package-1"}
_CONTAINERS = [
    pytest.param(GeneratedPackageRequest, _NEW_PACKAGE, id="generated-PackageRequest"),
    pytest.param(GeneratedPackageUpdate, _EXISTING_PACKAGE, id="generated-PackageUpdate"),
    pytest.param(PackageControl, _EXISTING_PACKAGE, id="PackageControl"),
    pytest.param(ProductPurchaseInput, _NEW_PACKAGE, id="ProductPurchaseInput"),
    # The public canonical-creative facades copy fields from these two
    # generated models. Patching only the generated originals misses adopters.
    pytest.param(PackageRequest, _NEW_PACKAGE, id="public-PackageRequest"),
    pytest.param(PackageUpdate, _EXISTING_PACKAGE, id="public-PackageUpdate"),
]
try:
    _forecast_module = import_module("adcp.types.domains.media_buy.package_forecast_input")
except ModuleNotFoundError as exc:
    if exc.name != "adcp.types.domains.media_buy.package_forecast_input":
        raise
else:
    _CONTAINERS.append(
        pytest.param(
            _forecast_module.PackageForecastInput,
            {"pricing_option_id": "price-1", "budget": 1000},
            id="PackageForecastInput",
        )
    )
_REQUEST_PATHS = [
    pytest.param("create_media_buy", "packages", id="create"),
    pytest.param("update_media_buy", "packages", id="update"),
    pytest.param("update_media_buy", "new_packages", id="update-new-packages"),
    pytest.param("control_media_buy", "packages", id="control"),
    pytest.param("buy_products", "purchases", id="direct-buy"),
]


# **ONLY THE INPUT TYPE, because only it is what the document puts on the field.**
# `media-buy/package-request.json` and `media-buy/package-update.json` both `$ref`
# `core/targeting-input.json` and nothing else, so `targeting_overlay` IS
# `TargetingOverlayInput | None`.
#
# `TargetingOverlay` is a DIFFERENT subject, not a spelling of the same one: it comes from
# `core/targeting.json`, and measured, all 37 of its properties carry a different subschema.
# The documents say why in their own words -- "Strict non-null targeting state used during
# product discovery, commercial snapshots, and media-buy readback" against "Request-only
# targeting mutation input. Each known dimension has three states: omission inherits the
# product default ...; null explicitly suppresses". Nullable mutation input and strict
# non-null state are not interchangeable.
#
# Upstream accepted both by WIDENING the field to
# `Annotated[Input | SkipJsonSchema[TargetingOverlay] | None, union_mode="left_to_right"]`
# in `adcp.types._forward_compat`. That is a widening of the document, it would need a
# declared `WIDENED` approximation here, and the module is deliberately not restored.
# Converting readback state into input goes through a dump, which
# `test_raw_dict_keeps_input_materialization` already grades.
@pytest.fixture(params=["TargetingOverlayInput"], ids=["input"])
def overlay_class(request: pytest.FixtureRequest) -> type[BaseModel]:
    # Resolve from the public surface inside the fixture so the original
    # missing export is a test failure rather than a collection failure.
    base = getattr(adcp.types, request.param)

    class InternalOverlay(base):
        model_config = ConfigDict(extra="forbid")
        internal_id: str = Field(exclude=True)
        internal_null: str | None = Field(default=None, exclude=True)
        _routing: dict[str, str] = PrivateAttr(default_factory=dict)

        def route(self) -> str:
            return self._routing[self.internal_id]

    return InternalOverlay


def _overlay(overlay_class: type[BaseModel], dimensions: dict[str, Any]) -> Any:
    overlay = overlay_class.model_validate(
        {**dimensions, "internal_id": "route-1181", "internal_null": None}
    )
    overlay._routing["route-1181"] = "seller-1"
    return overlay


@pytest.mark.parametrize("container,required", _CONTAINERS)
def test_public_overlay_subclass_preserves_identity_and_internal_behavior(
    overlay_class: type[BaseModel], container: type[BaseModel], required: dict[str, Any]
) -> None:
    overlay = _overlay(overlay_class, {"geo_regions": ["US-NY"]})
    result = container.model_validate({**required, "targeting_overlay": overlay})

    assert result.targeting_overlay is overlay
    assert result.targeting_overlay.route() == "seller-1"
    # Both branches read a collection field as the collection. Neither is converted
    # into the other; they agree on the type the field already has.
    #
    # The element IS the string, read directly. `region.root` was the previous
    # emission's shape, where a constrained scalar root became a `RootModel` wrapper;
    # this tree emits it as the scalar itself with the constraint carried in the
    # annotation (`Annotated[str, pattern=...]`), so the pattern is still enforced --
    # 'us-ny', 'USA-NYC', '' and ' US-NY' are all refused -- and there is no `.root` to
    # unwrap.
    assert list(overlay.geo_regions) == ["US-NY"]
    assert result.model_dump(mode="json", exclude_none=True)["targeting_overlay"] == {
        "geo_regions": ["US-NY"]
    }


@pytest.mark.parametrize("container,required", _CONTAINERS)
@pytest.mark.parametrize("dimensions", [{}, {"geo_regions": ["US-NY"]}, {"geo_countries": None}])
def test_raw_dict_keeps_input_materialization(
    container: type[BaseModel], required: dict[str, Any], dimensions: dict[str, Any]
) -> None:
    result = container.model_validate({**required, "targeting_overlay": dimensions})
    assert type(result.targeting_overlay) is GeneratedInput
    # Materialization is what this grades, and every supplied key is set.
    assert result.targeting_overlay.model_fields_set == set(dimensions)
    # The dump is the decision's, not this test's: §2 omits an optional
    # property's ``None`` whatever ``exclude_none`` says, because only a
    # REQUIRED key cannot be absent. ``geo_countries`` is optional, so the
    # supplied ``None`` is recorded as set above and left off the wire here --
    # the same reading ``test_bridge_serialization_keeps_objects_on_the_wire``
    # takes through ``is_no_explicit_null``.
    expected = {key: value for key, value in dimensions.items() if value is not None}
    assert (
        result.targeting_overlay.model_dump(mode="json", exclude_unset=True, exclude_none=False)
        == expected
    )


def _request(task: str, collection: str, overlay: Any, *, legacy_create: bool = False) -> BaseModel:
    params: dict[str, Any] = {
        "idempotency_key": "targeting-compat-1181",
        "account": {"account_id": "account-1"},
    }
    if task in {"create_media_buy", "buy_products"}:
        params.update(
            brand={"brand_id": "brand_1", "domain": "brand.example"},
            start_time="2026-10-01T00:00:00Z",
            end_time="2026-10-31T00:00:00Z",
        )
        item = _NEW_PACKAGE
    else:
        params["media_buy_id"] = "buy-1"
        item = _NEW_PACKAGE if collection == "new_packages" else _EXISTING_PACKAGE
    if task == "control_media_buy":
        params["revision"] = 1
    elif task == "buy_products":
        params["feed_version"] = "feed-1"
    params[collection] = [{**item, "targeting_overlay": overlay}]
    models = {
        "create_media_buy": LegacyCreateMediaBuyRequest if legacy_create else CreateMediaBuyRequest,
        "update_media_buy": UpdateMediaBuyRequest,
        "control_media_buy": ControlMediaBuyRequest,
        "buy_products": BuyProductsRequest,
    }
    return models[task].model_validate(params)


def test_legacy_create_parent_refreshes_its_cached_nested_validator(
    overlay_class: type[BaseModel],
) -> None:
    overlay = _overlay(overlay_class, {"geo_countries": None})
    request = _request("create_media_buy", "packages", overlay, legacy_create=True)
    assert request.packages[0].targeting_overlay is overlay
    wire = preserve_explicit_nulls(
        request,
        request.model_dump(mode="json", exclude_none=True),
        task_name="create_media_buy",
        version="3.2.0-rc.3",
    )
    assert wire["packages"][0]["targeting_overlay"] == {"geo_countries": None}
    outcome = validate_request("create_media_buy", wire, version="3.2.0-rc.3")
    assert outcome.valid, outcome.issues
    assert outcome.variant == "request"


@pytest.mark.parametrize("task,collection", _REQUEST_PATHS)
@pytest.mark.parametrize("clear", [False, True], ids=["inherit", "clear"])
def test_subclass_null_intent_survives_request_serialization(
    overlay_class: type[BaseModel], task: str, collection: str, clear: bool
) -> None:
    dimensions: dict[str, Any] = {"geo_regions": ["US-NY"]}
    if clear:
        dimensions["geo_countries"] = None
    overlay = _overlay(overlay_class, dimensions)
    request = _request(task, collection, overlay)
    assert getattr(request, collection)[0].targeting_overlay is overlay
    params = request.model_dump(mode="json", exclude_none=True)
    assert params[collection][0]["targeting_overlay"] == {"geo_regions": ["US-NY"]}

    wire = preserve_explicit_nulls(request, params, task_name=task, version="3.2.0-rc.3")

    assert wire[collection][0]["targeting_overlay"] == dimensions
    outcome = validate_request(task, wire, version="3.2.0-rc.3")
    assert outcome.valid, outcome.issues
    assert outcome.variant == "request"


# As the fixture above: the field's own type is the only one it takes.
@pytest.mark.parametrize("overlay_name", ["TargetingOverlayInput"])
@pytest.mark.parametrize("task,collection", _REQUEST_PATHS)
@pytest.mark.parametrize(
    "dimensions",
    [
        {"geo_regions": ["US-NY"]},
        {"geo_regions": ["US-NY"], "geo_countries": None},
        {},
        {"geo_regions": ["US-NY"], "geo_countries": ["US"]},
    ],
    ids=["omitted-country", "null-country", "empty-overlay", "populated-country"],
)
def test_exact_overlay_objects_preserve_wire_intent(
    overlay_name: str, task: str, collection: str, dimensions: dict[str, Any]
) -> None:
    overlay_type = getattr(adcp.types, overlay_name)
    overlay = overlay_type.model_validate(dimensions)
    assert type(overlay) is overlay_type
    # Exact objects have no declared excluded extension fields. A private
    # runtime hint must also remain off the wire; excluded subclass fields
    # are covered separately above.
    overlay._routing_hint = "seller-1"
    request = _request(task, collection, overlay)
    assert getattr(request, collection)[0].targeting_overlay is overlay
    assert overlay._routing_hint == "seller-1"

    wire = preserve_explicit_nulls(
        request,
        request.model_dump(mode="json", exclude_none=True),
        task_name=task,
        version="3.2.0-rc.3",
    )

    assert wire[collection][0]["targeting_overlay"] == dimensions
    outcome = validate_request(task, wire, version="3.2.0-rc.3")
    assert outcome.valid, outcome.issues
    assert outcome.variant == "request"


@pytest.mark.parametrize("task,collection", _REQUEST_PATHS)
def test_raw_dict_keeps_input_materialization_in_enclosing_request(
    task: str, collection: str
) -> None:
    request = _request(task, collection, {"geo_countries": None})
    assert type(getattr(request, collection)[0].targeting_overlay) is GeneratedInput


@pytest.mark.parametrize("container,required", _CONTAINERS)
@pytest.mark.parametrize(
    "strict,bid_price,valid",
    [(False, "1.5", True), (True, "1.5", False), (True, 1.5, True)],
)
def test_json_targeting_preserves_caller_strictness(
    container: type[BaseModel],
    required: dict[str, Any],
    strict: bool,
    bid_price: str | float,
    valid: bool,
) -> None:
    overlay = {
        "keyword_targets": [{"keyword": "boots", "match_type": "exact", "bid_price": bid_price}]
    }
    encoded = json.dumps({**required, "targeting_overlay": overlay})
    reference = TypeAdapter(GeneratedInput | None)
    if valid:
        expected = reference.validate_json(json.dumps(overlay), strict=strict)
        result = container.model_validate_json(encoded, strict=strict).targeting_overlay
        assert type(result) is GeneratedInput
        assert result.model_dump(mode="json") == expected.model_dump(mode="json")
    else:
        with pytest.raises(ValidationError) as expected_error:
            reference.validate_json(json.dumps(overlay), strict=strict)
        with pytest.raises(ValidationError) as actual_error:
            container.model_validate_json(encoded, strict=strict)
        assert actual_error.value.errors() == [
            {**error, "loc": ("targeting_overlay", *error["loc"])}
            for error in expected_error.value.errors()
        ]


@pytest.mark.parametrize("container,required", _CONTAINERS)
@pytest.mark.parametrize("round_trip", [False, True])
def test_bridge_serialization_keeps_objects_on_the_wire(
    overlay_class: type[BaseModel],
    container: type[BaseModel],
    required: dict[str, Any],
    round_trip: bool,
) -> None:
    overlay = _overlay(overlay_class, {"geo_regions": ["US-NY"], "geo_countries": None})
    result = container.model_validate({**required, "targeting_overlay": overlay})
    options = {
        "exclude_none": False,
        "serialize_as_any": False,
        "round_trip": round_trip,
        "warnings": "error",
    }
    expected = overlay.model_dump(mode="json", **options)
    assert isinstance(expected, dict)
    if is_no_explicit_null(overlay_class.model_fields["geo_countries"]):
        # The resolved-state shape: ``null`` is not a clear there, so a ``None``
        # is left off even under ``exclude_none=False`` (#1587). The mutation
        # input keeps it, and ``preserve_explicit_nulls`` is the client path.
        assert "geo_countries" not in expected
    else:
        assert expected["geo_countries"] is None
    assert result.model_dump(mode="json", **options)["targeting_overlay"] == expected
    encoded = result.model_dump_json(**options)
    assert json.loads(encoded)["targeting_overlay"] == expected
    assert "route-1181" not in encoded
    assert "seller-1" not in encoded


@pytest.mark.parametrize("container,required", _CONTAINERS)
def test_container_json_schema_keeps_only_mutation_input(
    container: type[BaseModel], required: dict[str, Any]
) -> None:
    # The bundled schema declares the overlay as the input shape with no null
    # branch (the field is optional, not nullable), and the published schema
    # states the same since ``NoExplicitNull`` (#1547).
    node = container.model_json_schema()["properties"]["targeting_overlay"]
    assert node["$ref"] == "#/$defs/TargetingOverlayInput"
    assert "anyOf" not in node


@pytest.mark.parametrize("container,required", _CONTAINERS)
def test_field_serialization_schema_keeps_only_mutation_input(
    container: type[BaseModel], required: dict[str, Any]
) -> None:
    # Canonical parents have their own opaque wrap serializer. Check the field
    # contract directly rather than expecting properties in that parent schema.
    annotation = container.model_fields["targeting_overlay"].rebuild_annotation()
    schema = TypeAdapter(annotation).json_schema(mode="serialization")
    assert "anyOf" not in schema
    assert schema["title"] == "TargetingOverlayInput"
    assert schema["type"] == "object"
