"""Reporting defaults on the wire: what the document requires, and what it defaults."""

import json

import pytest
from pydantic import BaseModel

from adcp.decisioning.capabilities import MediaBuy
from adcp.types import NotificationConfig
from adcp.types.base import AdCPBaseModel
from tests.test_reporting_ledger import _OFFERING

# `core/reporting-delivery-capabilities.json`'s own `required`.
_REQUIRED = {
    "supported": True,
    "configuration_task": "sync_accounts",
    "status_task": "get_reporting_status",
    "offerings": [_OFFERING],
    "automated_recovery_window_seconds": 0,
    "status_retention_days": 30,
}
# Optional, and the document gives each a `default`.
_DOCUMENT_DEFAULTED = ("managed_delivery", "reconciled_billing", "supports_webhook_activity")


@pytest.mark.parametrize("explicit", [False, True])
def test_reporting_capability_wire_carries_required_and_defaulted_keys(explicit):
    """One model, and the dump keys follow the document rather than supply.

    Two things changed from what stood here, both of them decisions:

    * **There is no bundled/canonical PAIR to parametrize over.** §4's one class
      per SUBJECT means `MediaBuy` is the class; `MediaBuy.__bases__[0]` is
      `AdCPBaseModel`, which states no `reporting_delivery` at all.
    * **A default is a VALUE, so the dump keeps it.** The omission rule is
      "the dump omits `None` unless the document requires the property"
      (decision index). `managed_delivery`, `reconciled_billing` and
      `supports_webhook_activity` each carry `default: false` in the document,
      so they are `False` and not `None`, and they ride the wire whether or not
      the caller supplied them. `model_fields_set` is what still distinguishes
      supplied from defaulted, and it is asserted here.
    """
    supplied = dict(_REQUIRED)
    if explicit:
        supplied.update(
            reliable_reporting_version="1.0",
            managed_delivery=False,
            # Required by the document once `reliable_reporting_version` is 1.0.
            revision_content_task="get_media_buy_delivery",
        )
    model = MediaBuy.model_validate({"reporting_delivery": supplied})
    before = set(model.reporting_delivery.model_fields_set)
    assert before == set(supplied)

    for wire in (model.model_dump(mode="json"), json.loads(model.model_dump_json())):
        value = wire["reporting_delivery"]
        assert set(_REQUIRED) <= set(value)
        assert all(key in value for key in _DOCUMENT_DEFAULTED)
        assert value["configuration_task"] == "sync_accounts"
        assert value["status_task"] == "get_reporting_status"
        assert ("reliable_reporting_version" in value) is explicit
        assert ("revision_content_task" in value) is explicit
        if explicit:
            assert value["reliable_reporting_version"] == "1.0"
            assert value["managed_delivery"] is False

    assert model.reporting_delivery.model_fields_set == before
    assert model.reporting_delivery.status_task == "get_reporting_status"


@pytest.mark.parametrize("product_event,explicit", [(False, False), (False, True), (True, False)])
def test_nested_notification_defaults_follow_event_and_field_provenance(product_event, explicit):
    class Envelope(BaseModel):
        config: NotificationConfig

    supplied = {
        "subscriber_id": "test",
        "url": "https://buyer.example/events",
        "event_types": ["product.updated" if product_event else "reporting.status_changed"],
    }
    if explicit:
        supplied["product_payload_view"] = "legacy"
    model = Envelope.model_validate({"config": supplied})
    before = set(model.config.model_fields_set)
    for wire in (model.model_dump(mode="json"), json.loads(model.model_dump_json())):
        assert ("product_payload_view" in wire["config"]) is (product_event or explicit)
    assert model.config.model_fields_set == before


def test_unrelated_model_keeps_its_defaults():
    class Unrelated(AdCPBaseModel):
        managed_delivery: bool = False
        supports_webhook_activity: bool = False
        product_payload_view: str = "legacy"

    model = Unrelated()
    expected = {
        "managed_delivery": False,
        "supports_webhook_activity": False,
        "product_payload_view": "legacy",
    }
    assert model.model_dump() == expected
    assert json.loads(model.model_dump_json()) == expected


def test_notification_config_serialization_schema_retains_fields():
    schema = NotificationConfig.model_json_schema(mode="serialization")
    assert schema["type"] == "object"
    assert {"subscriber_id", "url", "event_types"} <= schema["properties"].keys()
