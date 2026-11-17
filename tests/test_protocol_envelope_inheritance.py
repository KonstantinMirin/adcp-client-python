"""Every response branch carries the root ``allOf`` protocol envelope (#1136).

Each AdCP response schema composes ``core/protocol-envelope.json`` at its root
via ``allOf``, so ``status``, ``task_id``, ``message``, ``context_id``,
``replayed``, ``timestamp``, ``push_notification_config``,
``governance_context``, ``context``, ``payload`` and ``adcp_error`` are part of
every response's contract — on the success branch, the error branch and the
submitted branch alike. The code generator used to attach
:class:`ProtocolEnvelope` only to the ``status: submitted`` branch, leaving
those fields untyped on the rest: a
seller that set one wrote a pydantic extra and a buyer that read one got an
``AttributeError``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from adcp._version import _read_packaged_version
from adcp.types import ProtocolEnvelope
from adcp.types import aliases as aliases_module
from adcp.validation.version import resolve_bundle_key

_ENVELOPE_FIELDS = frozenset(ProtocolEnvelope.model_fields)


def _schema_dir() -> Path:
    return Path("schemas") / "cache" / resolve_bundle_key(_read_packaged_version())


def _public_response_classes() -> list[tuple[str, type[BaseModel]]]:
    """Public ``*SuccessResponse`` / ``*ErrorResponse`` aliases that are classes.

    Non-discriminated ``oneOf`` responses also expose bare union aliases, which
    are ``types.UnionType`` rather than classes; those are out of scope here.
    """
    found: list[tuple[str, type[BaseModel]]] = []
    for name in sorted(dir(aliases_module)):
        if name.startswith("_") or not name.endswith(("SuccessResponse", "ErrorResponse")):
            continue
        obj = getattr(aliases_module, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            found.append((name, obj))
    return found


def test_public_response_aliases_inherit_protocol_envelope() -> None:
    """The alias surface adopters import must carry the envelope."""
    classes = _public_response_classes()
    assert len(classes) > 20, "expected the full public response-alias surface"

    missing = [name for name, obj in classes if not issubclass(obj, ProtocolEnvelope)]
    assert missing == [], "response aliases missing the ProtocolEnvelope base: " + ", ".join(
        missing
    )


def test_public_response_aliases_declare_every_envelope_field() -> None:
    """Envelope fields are declared fields, never ``extra`` bags."""
    for name, obj in _public_response_classes():
        assert _ENVELOPE_FIELDS <= set(obj.model_fields), name


@pytest.mark.parametrize(
    "relative",
    [
        "account/get_account_financials_response.py",
        "account/sync_accounts_response.py",
        "brand/acquire_rights_response.py",
        "brand/get_brand_identity_response.py",
        "brand/get_rights_response.py",
        "brand/update_rights_response.py",
        "content_standards/calibrate_content_response.py",
        "content_standards/get_content_standards_response.py",
        "content_standards/get_media_buy_artifacts_response.py",
        "content_standards/validate_content_delivery_response.py",
        "creative/get_creative_features_response.py",
        "creative/preview_creative_response.py",
        "creative/sync_creatives_response.py",
        "media_buy/build_creative_response.py",
        "media_buy/create_media_buy_response.py",
        "media_buy/log_event_response.py",
        "media_buy/provide_performance_feedback_response.py",
        "media_buy/sync_audiences_response.py",
        "media_buy/sync_catalogs_response.py",
        "media_buy/sync_event_sources_response.py",
        "media_buy/update_media_buy_response.py",
        "signals/activate_signal_response.py",
    ],
)
def test_generated_branches_match_their_root_schema_composition(relative: str) -> None:
    """Every emitted branch mirrors whether its ROOT schema composes the envelope.

    The branches are read off the union BASE's own ``_branch_models``, not off a
    ``<Base><n>`` name pattern. Section 4 emits no positional name, so the old
    regex matched nothing and the count assertion below compared 0 against the
    schema's ``oneOf`` length -- which is the one way this test could fail
    without saying anything about an envelope.
    """
    import importlib

    module_name = "adcp.types.domains." + relative.removesuffix(".py").replace("/", ".")
    module = importlib.import_module(module_name)

    schema_path = _schema_dir() / Path(relative).with_suffix(".json").as_posix().replace("_", "-")
    schema = json.loads(schema_path.read_text())
    root_refs = [part.get("$ref", "") for part in schema.get("allOf", []) if isinstance(part, dict)]
    root_composes_envelope = any(ref.endswith("core/protocol-envelope.json") for ref in root_refs)
    assert root_composes_envelope, f"{relative}: fixture assumes a root protocol envelope"

    base = getattr(module, module.__all__[0])
    branches = list(base.__dict__.get("_branch_models") or ())
    assert branches, f"{relative}: {base.__name__} declares no branches"
    assert len(branches) == len(schema["oneOf"]), (
        f"{relative}: branch count drifted from the schema"
    )
    for branch in branches:
        assert issubclass(branch, ProtocolEnvelope), f"{relative}: {branch.__name__}"


def test_error_branch_can_carry_envelope_state() -> None:
    """The error branch of a ``oneOf`` is an envelope too, not a bare payload."""
    from adcp.types.aliases import CreateMediaBuyErrorResponse

    error = CreateMediaBuyErrorResponse.model_validate(
        {
            "errors": [{"code": "INVALID_BUDGET", "message": "too low"}],
            "status": "rejected",
            "task_id": "task_1",
            "replayed": True,
        }
    )
    assert error.status == "rejected"
    assert error.task_id == "task_1"
    assert error.replayed is True
    assert error.model_extra == {}


def test_replayed_and_status_round_trip_as_declared_fields() -> None:
    """Idempotency rule 4: a replayed response sets ``replayed`` on the envelope."""
    from adcp.types.aliases import SyncCreativesSuccessResponse

    # `status` is required and NOT defaulted here. The success branch of
    # `creative/sync-creatives-response.json` states no `status` of its own, so
    # the field is the envelope's -- the full `TaskStatus` enum one `allOf` up --
    # and the decision index is explicit that a multi-member `enum` gets no
    # default. Only a `const` may default to the value it pins.
    response = SyncCreativesSuccessResponse.model_validate(
        {"creatives": [], "status": "completed"}
    )
    assert response.replayed is False
    assert response.model_extra == {}

    response.replayed = True
    dumped = response.model_dump(mode="json")
    assert dumped["replayed"] is True
    # ``status`` is required on every task response envelope and now serializes
    # from a declared field rather than being dropped.
    assert dumped["status"] == "completed"

    reparsed = SyncCreativesSuccessResponse.model_validate(dumped)
    assert reparsed.replayed is True
    assert reparsed.model_extra == {}


def test_envelope_state_used_to_land_in_extra() -> None:
    """Pin the exact regression: envelope keys are not ``extra`` any more."""
    from adcp.types.aliases import LogEventSuccessResponse

    response = LogEventSuccessResponse.model_validate(
        {
            "events_received": 0,
            "events_processed": 0,
            "status": "completed",
            "replayed": True,
            "context_id": "ctx_1",
        }
    )
    assert response.model_extra == {}
    assert response.context_id == "ctx_1"
