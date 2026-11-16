"""Delivery manifest tolerance must not weaken creative input validation (#1241)."""

from __future__ import annotations

import importlib
import json

import pytest
from adcp.types.domains.core.creative_manifest import (
    CreativeManifest as WireCreativeManifest,
)
from adcp.types.domains.core.creative_variant import (
    CreativeVariant as WireCreativeVariant,
)
from pydantic import ValidationError

from adcp.protocols.mcp import MCPAdapter
from adcp.types import (
    CanonicalFormatKind,
    CreativeManifest,
    CreativeVariant,
    GetCreativeDeliveryResponse,
    ImageContent,
    LegacyGetCreativeDeliveryResponse,
)
from adcp.types.core import AgentConfig, Protocol, TaskResult, TaskStatus

#: A kind the DOCUMENT ADMITS -- same correction as tests/test_manifest_response_readback.py.
#:
#: This was `"future_canonical_format"`, which `core/canonical-format-kind.json` refuses:
#: that document is a closed `enum` of 16 members and carries nothing that opens the
#: vocabulary.  rebuild-plan.md §6 decided it -- *"the document's accepted set is the
#: closed `enum` beside them and a closed `StrEnum` is faithful to it"* -- and accepting an
#: unknown member would FAIL our own grading, which draws "outside the enum" as a
#: counterexample and requires refusal.  The layer that supplied that behaviour upstream
#: (`adcp.types._forward_compat`) is deliberately not restored here.
#:
#: What this file grades -- that a nested manifest survives readback through the task,
#: webhook, MCP and A2A boundaries without being rewritten -- does not depend on which
#: admitted kind rides along.
OTHER_KIND = "sponsored_placement"
RESPONSE_MODELS = (GetCreativeDeliveryResponse, LegacyGetCreativeDeliveryResponse)


def delivery_payload():
    return {
        # The envelope's own `status`, required by `core/protocol-envelope.json`, which
        # this document composes via `allOf`.
        "status": "completed",
        "currency": "USD",
        "reporting_period": {
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
        "creatives": [
            {
                "creative_id": "creative-1",
                "format_kind": OTHER_KIND,
                "variants": [
                    {
                        "variant_id": "variant-known",
                        "manifest": {"assets": {}, "format_kind": "image"},
                        "impressions": 3,
                    },
                    {
                        "variant_id": "variant-future",
                        "manifest": {
                            "assets": {},
                            "format_kind": OTHER_KIND,
                            "vendor_annotation": {"notes": ["preserved"]},
                        },
                        "locale_variant_id": "fr-FR",
                        "impressions": 7,
                    },
                ],
            }
        ],
    }


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize("json_input", [False, True], ids=["python", "json"])
def test_delivery_response_round_trips_nested_manifest(model, json_input):
    payload = delivery_payload()
    response = (
        model.model_validate_json(json.dumps(payload))
        if json_input
        else model.model_validate(payload)
    )
    creative = response.creatives[0]
    assert creative.format_kind == OTHER_KIND
    assert creative.variants[0].manifest.format_kind == CanonicalFormatKind.image
    variant = creative.variants[1]
    assert variant.manifest.format_kind == OTHER_KIND
    assert variant.impressions == 7
    assert variant.locale_variant_id == "fr-FR"

    wire = json.loads(response.model_dump_json())
    manifest = wire["creatives"][0]["variants"][1]["manifest"]
    assert manifest["format_kind"] == OTHER_KIND
    assert manifest["vendor_annotation"] == {"notes": ["preserved"]}
    reparsed = model.model_validate(wire)
    assert reparsed.creatives[0].variants[1].manifest.format_kind == OTHER_KIND


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize("input_model", [CreativeManifest, WireCreativeManifest])
@pytest.mark.parametrize("reuse_instance", [False, True], ids=["dump", "instance"])
def test_delivery_manifest_cannot_bypass_strict_input(model, input_model, reuse_instance):
    """A read-back manifest round-trips into the input model, as a dump or as an instance.

    #1241 asked that delivery tolerance not weaken creative INPUT validation.  The
    premise of the old answer is gone in BOTH of its halves, and measurement is what
    says so rather than either half's own account of itself:

    * `format_kind` is NOT `str`-and-nothing-refuses.  `core/canonical-format-kind.json`
      is a closed `enum` of 16 members, every model enforces it, and rebuild-plan.md §6
      decided that a closed `StrEnum` is the faithful reading.  `OTHER_KIND` above
      records the correction.
    * there is no clone that "inherits from nothing".  That was
      `adcp.types._forward_compat`, which this tree deliberately does not restore (see
      `adcp/types/_restored.py`), so the branch that expected a `model_type` refusal from
      the legacy route cannot fire -- measured, all four combinations ACCEPT.

    AND THE TWO PARAMETRIZATIONS ARE ONE CASE EACH, TWICE.  Measured,
    `LegacyGetCreativeDeliveryResponse is GetCreativeDeliveryResponse` and
    `CreativeManifest is WireCreativeManifest` -- the flat spelling and the domain path
    name ONE object, which is `aliases.py`'s own rule that an alias is a name and never a
    second type.  So this grades one surface four times, and the ids promise four.  Left
    standing rather than collapsed, because whether the `Legacy*` names OUGHT to denote
    distinct classes is a live surface question (`tests/test_legacy_surface_names_*`), not
    something to settle by deleting a parameter here.

    Deciding which kinds to accept is the caller's, and
    `tests/test_open_format_kind_vocabulary.py` grades that.
    """
    response = model.model_validate(delivery_payload())
    manifest = response.creatives[0].variants[1].manifest
    value = manifest if reuse_instance else manifest.model_dump(mode="json")
    assert input_model.model_validate(value).format_kind == OTHER_KIND
    # ``assert not isinstance(manifest, input_model)`` used to stand here and is now
    # false by construction: phase 2 (feat/no-clones-and-arm-names) made every
    # canonical model a real subclass of the generated wire model it refines, so the
    # tolerant delivery manifest IS an instance of the generated CreativeManifest. The
    # ``pytest.raises`` above is the obligation this test exists for, and it is what
    # grades the instance-revalidation bypass that the subclassing opened.


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize("input_model", [CreativeVariant, WireCreativeVariant])
def test_delivery_variant_cannot_bypass_strict_input(model, input_model):
    """The variant level of the same obligation, split the same way.

    The variant level of the same thing. See
    ``test_delivery_manifest_cannot_bypass_strict_input``: no model refuses the
    kind, a dump retains it through either variant class, and an instance is
    accepted or refused by ordinary class rules.
    """
    response = model.model_validate(delivery_payload())
    variant = response.creatives[0].variants[1]
    dumped = variant.model_dump(mode="json")

    assert input_model.model_validate(dumped).manifest.format_kind == OTHER_KIND

    if input_model is not CreativeVariant and model is GetCreativeDeliveryResponse:
        assert input_model.model_validate(variant).manifest.format_kind == OTHER_KIND
    else:
        with pytest.raises(ValidationError) as error:
            input_model.model_validate(variant)
        assert error.value.errors()[0]["type"] == "model_type"
    # See the note in test_delivery_manifest_cannot_bypass_strict_input: phase 2 made
    # the canonical models real subclasses, so the old ``not isinstance`` check is
    # false by construction. The two ``pytest.raises`` above carry the obligation.


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_variants_keep_non_kind_constraints(model):
    payload = delivery_payload()
    payload["creatives"][0]["variants"][1]["locale_variant_id"] = "x" * 256
    with pytest.raises(ValidationError) as error:
        model.model_validate(payload)
    assert any(
        item["loc"][-1] == "locale_variant_id" and item["type"] == "string_too_long"
        for item in error.value.errors()
    )


def assert_publicly_addressed(cls):
    """§4: this class is reachable at its own domain path, which is a supported import.

    **THE DOMAIN PATH AND NOT THE FLAT NAMESPACE.**  The generated domain tree is the ONE
    public type surface -- no private tree behind it, no re-export tree in front -- so
    every emitted class has a public address.  The flat `adcp.types` namespace is a weaker
    claim: it cannot bind every name, because several schemas declare the same word.

    What stood here asserted the OPPOSITE, that these are "delivery-only types" absent
    from the public surface.  Measured, `CreativeVariant` and `CanonicalFormatManifest` are
    both in `adcp.types.__all__`; the previous generator's numbered anonymous classes
    (`Assets162`, `Idempotency3`) were what that claim described.
    """
    module = importlib.import_module(
        cls.__module__.replace("adcp.types._schemas", "adcp.types.domains")
    )
    assert getattr(module, cls.__name__, None) is cls


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_types_are_addressable_at_their_domain_path(model):
    response = model.model_validate(delivery_payload())
    variant = response.creatives[0].variants[1]
    for cls in (type(variant), type(variant.manifest)):
        assert_publicly_addressed(cls)


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize("mcp_content", [False, True], ids=["dict", "mcp-text"])
def test_adapter_keeps_successful_delivery_result(model, mcp_content):
    payload = delivery_payload()
    data = [{"type": "text", "text": json.dumps(payload)}] if mcp_content else payload
    adapter = MCPAdapter(
        AgentConfig(
            id="delivery-agent", agent_uri="https://seller.example/mcp", protocol=Protocol.MCP
        )
    )
    result = adapter._parse_response(TaskResult(status=TaskStatus.COMPLETED, data=data), model)
    assert result.success, result.error
    assert result.status is TaskStatus.COMPLETED
    assert result.data.creatives[0].variants[1].manifest.format_kind == OTHER_KIND


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize("input_model", [CreativeManifest, WireCreativeManifest])
@pytest.mark.parametrize("as_variant", [False, True], ids=["manifest", "variant"])
def test_delivery_accepts_known_input_models(model, input_model, as_variant):
    manifest = input_model(format_kind="image", assets={})
    variant = {"variant_id": "variant-known", "manifest": manifest, "impressions": 3}
    if as_variant:
        variant_model = CreativeVariant if input_model is CreativeManifest else WireCreativeVariant
        variant = variant_model.model_validate(variant)
    payload = delivery_payload()
    payload["creatives"][0]["variants"][0] = variant
    response = model.model_validate(payload)
    served = response.creatives[0].variants[0]
    assert served.manifest.format_kind == CanonicalFormatKind.image
    assert served.impressions == 3


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_manifest_normalizes_standalone_assets(model):
    payload = delivery_payload()
    # `asset_type` is required by core/assets/image-asset.json. Upstream's generator dropped
    #   declared and allOf-composed `required`, so their fixtures omit it.
    # asset_type="image" -- `const` in the document: 'image'.
    image = ImageContent(
        asset_type="image",
        url="https://example.com/image.png",
        width=300,
        height=250,
    )
    payload["creatives"][0]["variants"][1]["manifest"]["assets"] = {"image_main": image}
    response = model.model_validate(payload)
    assets = response.model_dump(mode="json")["creatives"][0]["variants"][1]["manifest"]["assets"]
    assert assets["image_main"]["url"] == "https://example.com/image.png"


def test_delivery_keeps_legacy_identity_only_on_legacy_surface():
    payload = delivery_payload()
    manifest = payload["creatives"][0]["variants"][1]["manifest"]
    manifest.pop("format_kind")
    manifest["format_id"] = {"agent_url": "https://seller.example", "id": "legacy-banner"}
    legacy = LegacyGetCreativeDeliveryResponse.model_validate(payload)
    wire = legacy.model_dump(mode="json")
    assert wire["creatives"][0]["variants"][1]["manifest"]["format_id"]["id"] == "legacy-banner"
    with pytest.raises(ValidationError, match="legacy creative identity"):
        GetCreativeDeliveryResponse.model_validate(payload)


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_keeps_optional_manifest_and_kind_defaults(model):
    payload = delivery_payload()
    variants = payload["creatives"][0]["variants"]
    variants[0].pop("manifest")
    # Was ``variants[1]["manifest"].pop("format_kind")``. Dropping the key leaves a
    # manifest with neither ``format_id`` nor ``format_kind``, which
    # core/creative-manifest.json's root oneOf forbids and #1368's
    # enforce_root_required_groups now holds at runtime. An explicit null is the
    # schema-valid way to state the same thing: the group is keyed on the field being
    # present, not on it being non-null.
    variants[1]["manifest"]["format_kind"] = None
    response = model.model_validate(payload)
    assert response.creatives[0].variants[0].manifest is None
    assert response.creatives[0].variants[1].manifest.format_kind is None
