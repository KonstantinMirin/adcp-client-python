"""Public reporting promises are nullable, explicit and tier-consistent (#1180)."""

from __future__ import annotations

import json
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from adcp.types import GetAdcpCapabilitiesResponse, ReportingDeliveryCapabilities
from tests.test_reporting_ledger import _OFFERING

PROMISES = {
    "receipt_task": "sync_reporting_receipts",
    "readiness_notification": "reporting.delivery_ready",
    "status_notification": "reporting.status_changed",
    "ledger_notification": "reporting.ledger_changed",
}


def capability(**fields):
    return {
        "supported": True,
        # `core/reporting-delivery-capabilities.json` requires six properties and pins
        # these two with a `const`, so neither the key nor the value is a choice:
        #   configuration_task  const "sync_accounts"
        #   status_task         const "get_reporting_status"
        "configuration_task": "sync_accounts",
        "status_task": "get_reporting_status",
        "offerings": [_OFFERING],
        "automated_recovery_window_seconds": 0,
        "status_retention_days": 7,
        **fields,
    }


def response(raw):
    return {
        "status": "completed",
        "adcp": {
            "major_versions": [3],
            "idempotency": {"supported": True, "replay_ttl_seconds": 3600},
        },
        "supported_protocols": ["media_buy"],
        "media_buy": {"reporting_delivery": raw},
    }


@pytest.fixture
def graph():
    return ReportingDeliveryCapabilities, GetAdcpCapabilitiesResponse


@pytest.mark.parametrize(
    "flags",
    [
        {},
        {"managed_delivery": False},
        {"reconciled_billing": False},
        {"managed_delivery": False, "reconciled_billing": False},
    ],
)
def test_core_attributes_schema_and_json_round_trip_do_not_synthesize_promises(graph, flags):
    model, envelope = graph
    value = model.model_validate(capability(**flags))
    fields = set(value.model_fields_set)
    schema = model.model_json_schema()
    for name in PROMISES:
        field = model.model_fields[name]
        assert field.default is None
        assert type(None) in get_args(field.annotation)
        assert getattr(value, name) is None
        assert schema["properties"][name]["default"] is None
        assert {"type": "null"} in schema["properties"][name]["anyOf"]
    for raw in (
        value.model_dump(),
        value.model_dump(mode="json"),
        json.loads(value.model_dump_json()),
    ):
        assert not PROMISES.keys() & raw.keys()
        assert model.model_validate(raw).model_dump(mode="json") == value.model_dump(mode="json")
    restored = model.model_validate_json(value.model_dump_json())
    assert restored.model_dump(mode="json") == value.model_dump(mode="json")
    nested = envelope.model_validate(response(capability(**flags)))
    for raw in (nested.model_dump(mode="json"), json.loads(nested.model_dump_json())):
        assert not PROMISES.keys() & raw["media_buy"]["reporting_delivery"].keys()
        restored = envelope.model_validate_json(json.dumps(raw))
        assert restored.media_buy.reporting_delivery.receipt_task is None
        assert restored.media_buy.reporting_delivery.readiness_notification is None
    assert fields == value.model_fields_set


@pytest.mark.parametrize("flag", [None, False])
def test_readiness_notification_needs_managed_delivery_in_both_graphs(graph, flag):
    """`#/allOf/7`, read in two halves because the class carries one of them.

        {"if": {"required": ["readiness_notification"]},
         "then": {"properties": {"managed_delivery": {"const": true}},
                  "required": ["managed_delivery"]}}

    The `required` half lowers to a rule -- measured,
    ``ConditionalRequired(when=Match(key='readiness_notification', present=True),
    require=('managed_delivery',))`` -- so an ABSENT tier flag is refused at
    construction, standalone and nested.

    The `const: true` half does not: §5's `then` row puts a conditional's
    `properties` on the schema half and not on the model, and the class DECLARES
    the gap rather than hiding it --
    ``Approximation(pointer='#/allOf/7', keyword='if', kind='WIDENED',
    rung='KEYWORD')``.  So `managed_delivery: false` beside the doorbell is
    refused by the document and admitted by the class, and that is a decision
    already taken, not a defect.  It is graded through ``strict_validate``, which
    IS the document.

    What stood here expected both halves at construction, under the message of a
    hand-written validator the previous emission carried
    ("readiness_notification requires managed_delivery").
    """
    model, envelope = graph
    raw = capability(
        readiness_notification=PROMISES["readiness_notification"],
        **({"managed_delivery": flag} if flag is not None else {}),
    )

    if flag is None:
        for cls, body in ((model, raw), (envelope, response(raw))):
            with pytest.raises(ValidationError, match="required when readiness_notification"):
                cls.model_validate(body)
    else:
        assert model.model_validate(raw).managed_delivery is False
        with pytest.raises(ValidationError, match="True was expected"):
            model.strict_validate(raw)


def test_receipt_task_alone_is_admitted_because_no_node_states_the_inverse() -> None:
    """The document states the implication in ONE direction, and this is the other.

    `#/allOf/4` is ``if reconciled_billing const true -> then required
    ['receipt_task']``, and `receipt_task`'s own description says "Required when
    reconciled_billing is true".  Measured over bundle 3.2, NO node anywhere keys
    an `if` on `receipt_task`, so "receipt_task requires reconciled_billing" is
    stated nowhere -- and both halves agree: the class admits it and
    ``strict_validate``, the document itself, admits it too.

    The stated direction is graded by
    :func:`test_reconciled_billing_requires_a_receipt_task`.
    """
    model = ReportingDeliveryCapabilities
    raw = capability(receipt_task=PROMISES["receipt_task"])
    assert model.model_validate(raw).receipt_task == PROMISES["receipt_task"]
    model.strict_validate(raw)


@pytest.mark.parametrize("managed", [None, False])
def test_reconciled_billing_requires_a_receipt_task(graph, managed):
    """`#/allOf/4`'s `required` half: the tier flag owes the task, in both graphs.

    ``ConditionalRequired(when=Match(key='reconciled_billing', allowed=(True,)),
    require=('receipt_task',))``, measured on ``_adcp_rules``, and it fires
    whether the OTHER tier flag is absent or explicitly false, because the
    document keys this conditional on `reconciled_billing` alone.

    What stood here expected "reconciled_billing requires managed_delivery".  No
    node of bundle 3.2 states that implication in that direction -- `#/allOf/3`
    keys on `managed_delivery` and requires retention and revocation windows, and
    `#/allOf/5` reaches `managed_delivery` from an offering's `method`.  It was
    the previous emission's hand-written validator, and the refusal it was
    reading is this one.
    """
    model, envelope = graph
    raw = capability(reconciled_billing=True, managed_delivery=managed)
    for cls, body in ((model, raw), (envelope, response(raw))):
        with pytest.raises(ValidationError, match="required when reconciled_billing=True"):
            cls.model_validate(body)


@pytest.mark.parametrize("field", PROMISES)
def test_each_explicit_supported_literal_survives_without_implying_other_promises(graph, field):
    model, envelope = graph
    flags = {"managed_delivery": True} if field == "readiness_notification" else {}
    if field == "receipt_task":
        flags = {"managed_delivery": True, "reconciled_billing": True}
    raw = capability(**flags, **{field: PROMISES[field]})
    for cls, body in ((model, raw), (envelope, response(raw))):
        value = cls.model_validate(body)
        for output in (value.model_dump(mode="json"), json.loads(value.model_dump_json())):
            block = output if cls is model else output["media_buy"]["reporting_delivery"]
            assert {key: block[key] for key in PROMISES if key in block} == {field: PROMISES[field]}
        with pytest.raises(ValidationError):
            cls.model_validate(
                {**raw, field: "unsupported"}
                if cls is model
                else response({**raw, field: "unsupported"})
            )


def test_subclasses_inside_a_non_sdk_parent_omit_absent_promises():
    class Reporting(ReportingDeliveryCapabilities):
        pass

    class OrdinaryParent(BaseModel):
        reporting: Reporting

    value = OrdinaryParent.model_validate({"reporting": capability()})
    assert all(getattr(value.reporting, name) is None for name in PROMISES)
    for raw in (value.model_dump(), json.loads(value.model_dump_json())):
        assert not PROMISES.keys() & raw["reporting"].keys()
    value = OrdinaryParent.model_validate(
        {"reporting": capability(status_notification=PROMISES["status_notification"])}
    )
    assert value.model_dump()["reporting"]["status_notification"] == PROMISES["status_notification"]
