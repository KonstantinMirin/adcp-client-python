"""A nested AdCP model leaves unset optional fields off the wire from any parent (#1587).

``AdCPBaseModel.model_dump`` defaults ``exclude_none=True``, but a plain pydantic
parent's serializer never calls that override, so a nested AdCP model wrote
``"ext": null`` -- and since #1555 the same model refuses that ``null`` on the way
back in. The fix moves the omission to the field: every ``NoExplicitNull``-marked
field carries ``exclude_if`` (pydantic-core level, no Python wrap serializer), so
a ``None`` is left off wherever the model sits, and ``model_validate_json`` of
``model_dump_json`` round-trips from a direct field, a list, a dict, several
plain levels down, and a ``RootModel`` over an AdCP union.

The published JSON Schema is unchanged in both modes, and a property whose
schema admits ``null`` is still emitted as ``null`` when the dump asks for it.
"""

from __future__ import annotations

import copy
import json
import warnings
from typing import Any

import pytest
from adcp.types.domains.core.product import Provider
from adcp.types.domains.core.vendor_pricing_option import (
    VendorPricingOption,
    VendorPricingOptionCpm,
)
from adcp.types.domains.creative.sync_creatives_request import (
    SyncCreativesRequest as GeneratedSyncCreativesRequest,
)
from adcp.types.domains.media_buy.create_media_buy_request import CreateMediaBuyRequest
from pydantic import BaseModel, RootModel, ValidationError
from pydantic.fields import FieldInfo

import adcp.types as public_types
from adcp._null_clear import nullable_request_paths, preserve_explicit_nulls

# `VendorPricingOptionCpm` and `VendorPricingOptionUnion` are both refused on the
# flat surface -- the first DOCUMENT-NO-WORD-NO-IDENTITY, the second as an
# Annotated expression with no document behind it. The subjects are both
# emitted from `core/vendor-pricing-option.json`: `VendorPricingOption` is the
# union base and `VendorPricingOptionCpm` is the `model: cpm` branch.
from adcp.types import (
    Product,
    ReportingWebhook,
    SyncCreativesRequest,
    TrustedMatch,
    UpdateMediaBuyRequest,
)
from adcp.types._base import OmittedNotNull, omits_null
from adcp.types.base import _REFUSE_JSON_NULL, AdCPBaseModel, NoExplicitNull, is_no_explicit_null
from tests.conformance import _schema_parity as parity

# --- the reported case -----------------------------------------------------------


class _Parent(BaseModel):
    """The issue's parent: an ordinary pydantic model holding AdCP models."""

    pricing: VendorPricingOptionCpm
    trusted_match: TrustedMatch


def _parent() -> _Parent:
    return _Parent(
        pricing=VendorPricingOptionCpm(
            pricing_option_id="cpm", model="cpm", cpm=1.0, currency="USD"
        ),
        trusted_match=TrustedMatch(context_match=True),
    )


def test_issue_repro_round_trips_from_a_plain_parent() -> None:
    parent = _parent()
    body = parent.model_dump_json()
    document = json.loads(body)
    assert "ext" not in document["pricing"]
    assert "providers" not in document["trusted_match"]
    assert _Parent.model_validate_json(body) == parent


def test_nested_dump_matches_the_direct_dump() -> None:
    """The model serializes the same way wherever it sits.

    The parent passes no ``exclude_none``, so the precise statement is that the
    nested document equals the direct dump under ``exclude_none=False``; with no
    nullable field set to ``None`` here, that is also the default direct dump.
    """
    parent = _parent()
    document = parent.model_dump(mode="json")
    assert document["pricing"] == parent.pricing.model_dump(mode="json")
    assert document["trusted_match"] == parent.trusted_match.model_dump(mode="json")
    assert document["trusted_match"] == parent.trusted_match.model_dump(
        mode="json", exclude_none=False
    )
    assert json.loads(parent.model_dump_json())["pricing"] == json.loads(
        parent.pricing.model_dump_json()
    )


def test_provider_level_nesting_round_trips() -> None:
    """One level down: a provider that omits ``countries`` / ``uid_types``."""
    parent = _Parent(
        pricing=_parent().pricing,
        trusted_match=TrustedMatch(
            context_match=True,
            # `core/product.json`'s
            # `#/properties/trusted_match/properties/providers/items` states
            # `if: {identity_match: {const: true}} -> then: required: [agent_url,
            # countries, uid_types]`. A provider that OMITS the two is therefore a
            # provider that does not claim identity match, which is the subject here.
            providers=[Provider(agent_url="https://tmp.example.com/", context_match=True)],
        ),
    )
    body = parent.model_dump_json()
    provider = json.loads(body)["trusted_match"]["providers"][0]
    assert "countries" not in provider
    assert "uid_types" not in provider
    assert _Parent.model_validate_json(body) == parent


class _VendorPricing(RootModel[VendorPricingOption]):
    """A ``RootModel`` over an AdCP union."""


_PRICING_DOCUMENT = {"pricing_option_id": "cpm", "model": "cpm", "cpm": 1.0, "currency": "USD"}


def test_root_model_over_an_adcp_union_round_trips() -> None:
    wrapped = _VendorPricing.model_validate(_PRICING_DOCUMENT)
    assert isinstance(wrapped.root, AdCPBaseModel)
    body = wrapped.model_dump_json()
    assert "ext" not in json.loads(body)
    assert _VendorPricing.model_validate_json(body) == wrapped


class _Containers(BaseModel):
    items: list[VendorPricingOptionCpm]
    by_key: dict[str, TrustedMatch]


def test_list_and_dict_containers_round_trip() -> None:
    parent = _Containers(
        items=[_parent().pricing, _parent().pricing],
        by_key={"a": TrustedMatch(context_match=True), "b": TrustedMatch(context_match=False)},
    )
    body = parent.model_dump_json()
    document = json.loads(body)
    assert all("ext" not in item for item in document["items"])
    assert all("providers" not in item for item in document["by_key"].values())
    assert _Containers.model_validate_json(body) == parent


class _Inner(BaseModel):
    parent: _Parent


class _Middle(BaseModel):
    inners: list[_Inner]


class _Outer(BaseModel):
    middle: _Middle
    pricing_by_key: dict[str, _VendorPricing]


def test_several_plain_levels_down_round_trip() -> None:
    outer = _Outer(
        middle=_Middle(inners=[_Inner(parent=_parent())]),
        pricing_by_key={"cpm": _VendorPricing.model_validate(_PRICING_DOCUMENT)},
    )
    body = outer.model_dump_json()
    assert "null" not in body
    assert _Outer.model_validate_json(body) == outer
    assert _Outer.model_validate(outer.model_dump(mode="json")) == outer


# --- legitimate nulls are kept ------------------------------------------------------

_NULLABLE_UPDATE: dict[str, Any] = {
    "account": {"account_id": "acct_1"},
    "media_buy_id": "mb_1",
    "idempotency_key": "nullable-clear-0001",
    # Both admit ``null`` in the bundled schema (a clear), neither is marked.
    "budget_cap_timezone": None,
    "daily_budget_cap": None,
}


class _Holder(BaseModel):
    request: UpdateMediaBuyRequest


def test_a_nullable_optional_is_omitted_from_a_plain_parent_too() -> None:
    """An OPTIONAL property's ``None`` is omitted whatever its type admits.

    Decision 2 of ``rebuild-plan.md`` §2's index: *"a required property keeps
    its ``null`` on the wire, because a required key cannot be absent; an
    optional one is omitted whatever its type admits. Serialisation keys on
    ``required``, validation still keys on nullability."* So the exclusion is on
    every optional field -- ``OmittedNotNull`` where the document refuses
    ``null``, ``OmittedWhenNone`` where it admits one -- and the split this test
    was written for (nullable keeps its ``null``) is the superseded half.

    Validation is unaffected and is asserted below: this request still ACCEPTS
    the explicit ``null`` its document admits, and still refuses one where the
    document does not.
    """
    holder = _Holder(request=UpdateMediaBuyRequest.model_validate(_NULLABLE_UPDATE))
    for body in (holder.model_dump_json(), holder.model_dump_json(exclude_none=False)):
        document = json.loads(body)["request"]
        assert "budget_cap_timezone" not in document
        assert "daily_budget_cap" not in document
        assert "name" not in document
        assert "push_notification_config" not in document
        # The round trip still holds: the omitted keys read back as ``None``,
        # which is this SDK's spelling of "not supplied".
        assert _Holder.model_validate_json(body) == holder

    # The nullable property keeps ADMITTING a ``null`` -- the exclusion is the
    # serialisation half only.
    admitted = UpdateMediaBuyRequest.model_validate_json(
        json.dumps({**_NULLABLE_UPDATE, "budget_cap_timezone": None})
    )
    assert admitted.budget_cap_timezone is None
    assert "budget_cap_timezone" in admitted.model_fields_set
    with pytest.raises(ValidationError):
        # ``name`` carries ``OmittedNotNull``: its document admits no ``null``.
        UpdateMediaBuyRequest.model_validate_json(json.dumps({**_NULLABLE_UPDATE, "name": None}))


def test_an_explicit_clear_reaches_the_wire_through_preserve_explicit_nulls() -> None:
    """The three-state convention survives the omission, by the stated mechanism.

    ``core/targeting-input.json``'s convention is omitted = leave unchanged,
    ``null`` = clear, a value = replace. With the omission on the field, no
    ``exclude_none`` setting can put that ``null`` back -- and
    ``adcp._null_clear.preserve_explicit_nulls`` is the mechanism that does,
    from the two facts that decide it: ``model_fields_set`` (did the caller
    supply the key) and the bundled REQUEST SCHEMA (does ``null`` mean anything
    at that path). That module's own docstring states the contract; this test is
    what grades it for the clear the model dump no longer carries.

    Asserted on the client's own serialisation path, which is where the clear
    has to survive: ``model_dump(exclude_none=True)`` then
    ``preserve_explicit_nulls``.
    """
    request = UpdateMediaBuyRequest.model_validate(_NULLABLE_UPDATE)
    assert {"budget_cap_timezone", "daily_budget_cap"} <= request.model_fields_set
    assert ("budget_cap_timezone",) in nullable_request_paths("update_media_buy")

    params = request.model_dump(mode="json", exclude_none=True)
    assert "budget_cap_timezone" not in params
    wire = preserve_explicit_nulls(request, params, task_name="update_media_buy")
    assert wire["budget_cap_timezone"] is None
    assert wire["daily_budget_cap"] is None
    # A property the caller never mentioned stays absent: the clear is a
    # command, and only a supplied key issues it.
    assert "name" not in wire

    reread = UpdateMediaBuyRequest.model_validate_json(json.dumps(wire))
    assert reread.budget_cap_timezone is None
    assert "budget_cap_timezone" in reread.model_fields_set


def test_exclude_none_false_keeps_an_unmarked_none_inside_an_open_dict() -> None:
    """Only marked *fields* are affected; a ``None`` value in an opaque object is data.

    ``ext`` (like ``context``) keeps its nulls on every dump path (#1575/#1600).
    """
    pricing = VendorPricingOptionCpm(
        pricing_option_id="cpm", model="cpm", cpm=1.0, currency="USD", ext={"note": None}
    )
    assert pricing.model_dump(exclude_none=False)["ext"] == {"note": None}
    assert pricing.model_dump()["ext"] == {"note": None}


# --- the marker carries both halves --------------------------------------------------


def test_marker_carries_the_exclusion_and_the_refusal() -> None:
    """The EMITTED marker is ``adcp.types._base.OmittedNotNull``, both halves.

    Two spellings of one marker, and ``is_no_explicit_null`` is the predicate
    that knows it: this module's ``NoExplicitNull`` is upstream's, carried by
    the hand-written code kept as machinery, and the generator writes
    ``OmittedNotNull``. What differs is the ``exclude_if`` FUNCTION OBJECT each
    holds, and identity is what the predicate compares -- so asking an emitted
    field for upstream's object answers ``False`` about a field that carries the
    marker, which is the measurement that docstring records.
    """
    field = TrustedMatch.model_fields["providers"]
    assert is_no_explicit_null(field)
    assert omits_null(field)
    assert field.exclude_if is OmittedNotNull.exclude_if
    assert field.exclude_if(None) is True
    assert field.exclude_if([]) is False
    assert isinstance(OmittedNotNull, FieldInfo)
    # The validation half, in ``metadata``: a JSON ``null`` at this key is
    # refused with the type's own error, and no null arm is published.
    validation_half = OmittedNotNull.metadata[0]
    assert validation_half in field.metadata
    assert [repr(item) for item in field.metadata if item == validation_half] == ["OmittedNotNull"]
    # The marker is merged into the field, never itself in ``metadata``; the
    # halves are distinct objects.
    assert OmittedNotNull not in field.metadata
    assert validation_half != OmittedNotNull
    # Upstream's spelling is a DIFFERENT object, which is why the predicate is a
    # membership test over both and not an identity test against one.
    assert _REFUSE_JSON_NULL is not validation_half
    assert NoExplicitNull.exclude_if is not OmittedNotNull.exclude_if
    # A generated ``Field(description=...)`` beside the marker survives the merge.
    assert field.description


def test_forward_compat_reporting_operation_id_is_left_off_when_unset() -> None:
    """The hand-written ``_ReportingOperationId`` annotation uses the same marker."""
    field = ReportingWebhook.model_fields["operation_id"]
    assert is_no_explicit_null(field)
    assert _REFUSE_JSON_NULL in field.metadata

    class Holder(BaseModel):
        webhook: ReportingWebhook

    holder = Holder(
        webhook=ReportingWebhook.model_validate(
            {
                "url": "https://buyer.example.com/hook",
                "authentication": {"schemes": ["Bearer"], "credentials": "x" * 40},
                "reporting_frequency": "daily",
            }
        )
    )
    body = holder.model_dump_json()
    assert "operation_id" not in json.loads(body)["webhook"]
    assert Holder.model_validate_json(body) == holder


# --- the published JSON Schema is unchanged ------------------------------------------


def _without_exclusion(model: type[BaseModel]) -> type[BaseModel]:
    """The same model as it was before #1587: every field's ``exclude_if`` cleared.

    A subclass under the original name and docstring, so titles and
    descriptions match; only the serialization exclusion differs.
    """
    namespace: dict[str, Any] = {
        "__module__": model.__module__,
        "__qualname__": model.__qualname__,
        "__doc__": model.__doc__,
        "__annotations__": {},
    }
    for name, field in model.model_fields.items():
        # A deep copy: ``copy.copy`` would share ``_attributes_set`` with the
        # real field, and popping from it would strip the exclusion from every
        # later redeclaration of that field.
        twin = copy.deepcopy(field)
        twin.exclude_if = None
        twin._attributes_set.pop("exclude_if", None)
        namespace["__annotations__"][name] = field.annotation
        namespace[name] = twin
    return type(model.__name__, (model,), namespace)


@pytest.mark.parametrize(
    "model",
    [
        VendorPricingOptionCpm,
        TrustedMatch,
        Provider,
        Product,
        SyncCreativesRequest,
        GeneratedSyncCreativesRequest,
        UpdateMediaBuyRequest,
        CreateMediaBuyRequest,  # nested packages
        ReportingWebhook,
    ],
    ids=lambda model: model.__name__,
)
def test_published_schema_is_unchanged_by_the_exclusion(model: type[BaseModel]) -> None:
    before = _without_exclusion(model)
    assert any(is_no_explicit_null(f) for f in model.model_fields.values())
    assert all(f.exclude_if is None for f in before.model_fields.values())
    # The real fields are untouched by building the twin.
    for field in model.model_fields.values():
        if is_no_explicit_null(field):
            assert "exclude_if" in field._attributes_set
    for mode in ("validation", "serialization"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert model.model_json_schema(mode=mode) == before.model_json_schema(mode=mode)


# --- sweeps over the generated tree ------------------------------------------------------


def _adcp_models() -> list[tuple[str, type[AdCPBaseModel]]]:
    models = []
    for name in sorted(dir(public_types)):
        if name.startswith("_"):
            continue
        obj = getattr(public_types, name, None)
        if isinstance(obj, type) and issubclass(obj, AdCPBaseModel) and obj.model_fields:
            models.append((name, obj))
    return models


def test_the_exclusion_is_on_every_optional_field_and_on_no_required_one() -> None:
    """Serialisation keys on ``required``; validation keys on nullability.

    Decision 2 of ``rebuild-plan.md`` §2's index, stated as a tree-wide
    invariant. Three facts, and the second is what this test used to assert the
    negation of:

    * a field carrying the VALIDATION half (``OmittedNotNull``, in
      ``metadata``) is optional, and carries the exclusion -- the two halves
      never come apart;
    * a field with NO validation half still carries the exclusion when it is
      optional (``OmittedWhenNone``: its document admits a ``null`` on input and
      does not require the property, so the dump omits it anyway). The old
      invariant read ``exclude_if is None`` here and so pinned the superseded
      nullable-keeps-null split;
    * a REQUIRED field carries no exclusion, because a required key cannot be
      absent and its ``null`` is the one that stays on the wire.

    One clause beside those three, and it is not an exception to them: a field
    dropped from EVERY dump (``exclude=True`` -- a write-only strip such as
    ``BusinessEntityResponse.bank``, which the spec forbids echoing) has no
    ``None`` for a conditional exclusion to omit.
    """
    marked = 0
    excluded = 0
    stripped = 0
    validation_half = OmittedNotNull.metadata[0]
    for name, model in _adcp_models():
        for field_name, field in model.model_fields.items():
            refuses = validation_half in field.metadata
            if refuses:
                marked += 1
                assert is_no_explicit_null(field), (name, field_name)
                assert not field.is_required(), (name, field_name)
            if field.exclude:
                assert field.exclude_if is None, (name, field_name)
                stripped += 1
            elif field.is_required():
                assert field.exclude_if is None, (name, field_name)
            else:
                assert field.exclude_if is OmittedNotNull.exclude_if, (name, field_name)
                excluded += 1
    assert marked > 5000
    assert excluded > marked
    assert stripped


def test_default_instances_of_every_model_dump_no_null_for_marked_fields() -> None:
    """Each public model, with only its defaults, dumped by a plain parent.

    ``model_construct`` fills every optional field with its default, so the
    dump is the worst case: every marked field holds ``None``. A plain parent
    passes no ``exclude_none``, so the only thing keeping ``null`` off the wire
    is the field's own exclusion. A ``null`` that does appear must belong to
    an unmarked (schema-nullable) field.
    """
    checked = 0
    for name, model in _adcp_models():
        instance = model.model_construct()
        parent = RootModel[model].model_construct(root=instance)  # type: ignore[valid-type]
        try:
            document = parent.model_dump(mode="json")
        except Exception:  # noqa: BLE001 -- a serializer that needs a validated instance
            continue
        if not isinstance(document, dict):
            continue
        checked += 1
        for field_name, field in model.model_fields.items():
            if is_no_explicit_null(field):
                for key in {field_name, field.alias or field_name}:
                    assert document.get(key, "absent") is not None, (name, field_name)
    assert checked > 600


def _models_for(tool: str) -> list[type[AdCPBaseModel]]:
    """The canonical request model first, then the ``Legacy*`` spelling when there is one.

    A synthesized document can carry legacy creative identity, which the
    canonical model refuses by design; the legacy model reads the same shape.
    """
    camel = "".join(part.capitalize() for part in tool.split("_"))
    models = []
    for name in (f"{camel}Request", camel, f"Legacy{camel}Request"):
        model = getattr(public_types, name, None)
        if isinstance(model, type) and issubclass(model, AdCPBaseModel):
            models.append(model)
    return models


@pytest.mark.parametrize(
    "tool",
    [
        "create_media_buy",
        "update_media_buy",
        "sync_creatives",
        "get_products",
        "activate_signal",
        "list_creatives",
        "get_media_buy_delivery",
        "provide_performance_feedback",
        "build_creative",
        "buy_products",
        "sync_audiences",
        "get_adcp_capabilities",
    ],
)
def test_synthesized_requests_round_trip_from_a_plain_parent(tool: str) -> None:
    """A schema-valid request, grown to reach its optional properties, through a parent."""
    models = _models_for(tool)
    if not models:
        pytest.skip(f"{tool} exposes no request model under adcp.types")
    try:
        document = parity.synthesize(tool)
    except parity.UnsynthesizableError as exc:
        pytest.skip(str(exc))
    request: AdCPBaseModel | None = None
    for model in models:
        try:
            request = model.model_validate(document)
        except ValidationError:
            continue
        break
    assert request is not None, f"no model under adcp.types reads the synthesized {tool}"

    class Holder(BaseModel):
        request: type(request)  # type: ignore[valid-type]

    holder = Holder(request=request)
    # ``by_alias``: the wire spelling, so a field such as ``pass_`` reads back
    # under its alias. The parent still passes no ``exclude_none``.
    body = holder.model_dump_json(by_alias=True)
    assert Holder.model_validate_json(body) == holder
    # The nested document is the direct dump under the parent's ``exclude_none``
    # (``False``): a schema-admitted ``null`` the synthesizer set is kept, a
    # marked field's ``None`` is not.
    assert json.loads(body)["request"] == json.loads(
        request.model_dump_json(by_alias=True, exclude_none=False)
    )
