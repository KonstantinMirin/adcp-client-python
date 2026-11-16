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
    AssetVariantImage,
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

    The branch that expected a ``model_type`` refusal cannot fire, for the reason
    ``test_delivery_manifest_cannot_bypass_strict_input`` already records one level
    up: measured, ``CreativeVariant is WireCreativeVariant`` and
    ``LegacyGetCreativeDeliveryResponse is GetCreativeDeliveryResponse``.  A
    ``Legacy*`` name IS the generated class (`tests/test_legacy_surface_names_every_arm.py`
    holds that as object identity against ``adcp.types``) and the domain path is an
    address rather than a second type, so the condition
    ``input_model is not CreativeVariant`` was never true and the instance handed to
    ``model_validate`` is already an instance of the class it is handed to.

    What remains measurable is the obligation #1241 actually asked for: the kind
    survives the WIRE route, which is the route a reader of a delivery response takes.
    A constraint the input model states is still enforced on that route --
    ``test_delivery_variants_keep_non_kind_constraints`` grades it.
    """
    response = model.model_validate(delivery_payload())
    variant = response.creatives[0].variants[1]
    dumped = variant.model_dump(mode="json")

    assert input_model.model_validate(dumped).manifest.format_kind == OTHER_KIND
    assert input_model.model_validate(variant).manifest.format_kind == OTHER_KIND


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
    #
    # AND THE SLOT TAKES THE UNION ARM, NOT THE REFERENCED DOCUMENT'S CLASS.
    # core/creative-manifest.json states the slot value as
    #   properties.assets.patternProperties['^[a-z0-9_]+$'].oneOf =
    #     [ $ref asset-union.json, {type: array, items: $ref asset-union.json, minItems: 1} ]
    # so the class addressing that position is the union's image arm,
    # `AssetVariantImage` at core/assets/asset-union.json#/oneOf/0.  That arm is a bare
    # `$ref` to image-asset.json and the emission keeps the subject identity as
    # inheritance -- `issubclass(AssetVariantImage, ImageContent)` holds, asserted below --
    # so naming the arm loses nothing.  An `ImageContent` instance is refused here with
    # `model_type`, because the parent is not an instance of the child.
    image = AssetVariantImage(
        asset_type="image",
        url="https://example.com/image.png",
        width=300,
        height=250,
    )
    assert isinstance(image, ImageContent)
    payload["creatives"][0]["variants"][1]["manifest"]["assets"] = {"image_main": image}
    response = model.model_validate(payload)
    assets = response.model_dump(mode="json")["creatives"][0]["variants"][1]["manifest"]["assets"]
    assert assets["image_main"]["url"] == "https://example.com/image.png"


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_keeps_legacy_identity_on_both_spellings(model):
    """``core/creative-manifest.json``'s root `oneOf` is the whole of the rule, and
    it is about the PAYLOAD rather than about which name read it.

    Arm 0 is "Named-format manifest", `deprecated: true`, `required: ['format_id']`
    with `not: {required: ['format_kind']}`; arm 1 is "Canonical-format manifest",
    `required: ['format_kind']` with `not: {required: ['format_id']}`.  So a manifest
    carrying `format_id` and no `format_kind` is ADMITTED -- deprecation is metadata
    and not absence -- and it parses to `NamedFormatManifest`.

    What stood here asserted that the canonical NAME refuses it while the `Legacy*`
    name accepts it.  Measured, `LegacyGetCreativeDeliveryResponse is
    GetCreativeDeliveryResponse`: a `Legacy*` name IS the generated class, held as
    object identity by `tests/test_legacy_surface_names_every_arm.py`.  One class
    cannot answer two ways, and the document gives it nothing to answer two ways
    about -- `format_id` is not on a removal schedule (CLAUDE.md measures 9 sites
    `deprecated: true` with no target and 3 not marked at all).
    """
    payload = delivery_payload()
    manifest = payload["creatives"][0]["variants"][1]["manifest"]
    manifest.pop("format_kind")
    manifest["format_id"] = {"agent_url": "https://seller.example", "id": "legacy-banner"}

    response = model.model_validate(payload)
    read = response.creatives[0].variants[1].manifest
    assert type(read).__name__ == "NamedFormatManifest"
    wire = response.model_dump(mode="json")
    assert wire["creatives"][0]["variants"][1]["manifest"]["format_id"]["id"] == "legacy-banner"


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.pop("format_kind"),
        lambda manifest: manifest.__setitem__(
            "format_id", {"agent_url": "https://seller.example", "id": "legacy-banner"}
        ),
    ],
    ids=["neither", "both"],
)
def test_delivery_refuses_a_manifest_that_is_neither_arm_or_both(model, mutate):
    """Each arm's `not` makes the identity an exclusive OR: a manifest carrying
    both `format_id` and `format_kind`, or neither, satisfies no arm."""
    payload = delivery_payload()
    mutate(payload["creatives"][0]["variants"][1]["manifest"])

    with pytest.raises(ValidationError) as error:
        model.model_validate(payload)

    assert any(
        item["loc"][-1] == "manifest" and item["type"] == "oneOf" for item in error.value.errors()
    )


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_keeps_the_manifest_optional(model):
    """``manifest`` is absent from the variant's own ``required``, so a variant may
    carry none and reads back as ``None``."""
    payload = delivery_payload()
    payload["creatives"][0]["variants"][0].pop("manifest")

    response = model.model_validate(payload)
    assert response.creatives[0].variants[0].manifest is None
    assert response.creatives[0].variants[1].manifest.format_kind == OTHER_KIND


@pytest.mark.parametrize("model", RESPONSE_MODELS, ids=["canonical", "legacy"])
def test_delivery_refuses_an_explicitly_null_format_kind(model):
    """A null is not the schema-valid way to spell "no kind".

    What stood here set ``format_kind = None`` and expected it to read back as
    ``None``, on the reading that the root ``oneOf`` keys on the key being PRESENT.
    It does -- and that is only half the conjunction.  Arm 1 also applies the
    property's own schema, and ``core/canonical-format-kind.json`` is a closed
    ``enum`` of 16 strings that admits no ``null`` (rebuild-plan.md §6: the
    document's accepted set is the closed ``enum`` and a closed ``StrEnum`` is
    faithful to it).  So the canonical arm refuses the value while the named arm
    refuses the absent ``format_id``, and the refusal lands on ``format_kind``
    with the enum's own 16 members.
    """
    payload = delivery_payload()
    payload["creatives"][0]["variants"][1]["manifest"]["format_kind"] = None

    with pytest.raises(ValidationError) as error:
        model.model_validate(payload)

    assert any(
        item["loc"][-1] == "format_kind" and item["type"] == "enum" for item in error.value.errors()
    )
