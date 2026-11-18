"""Strict manifest inputs and tolerant buyer response views (issue #1241)."""

from __future__ import annotations

import importlib
import json

import pytest
from adcp.types.domains.core.async_response_data import AdcpAsyncResponseData
from adcp.types.domains.core.creative_manifest import (
    CreativeManifest as InputManifest,
)
from adcp.types.domains.core.version_envelope import AdcpVersionEnvelope
from adcp.types.domains.media_buy.build_creative_response import (
    Creative as InputBuildCreative,
)
from adcp.types.domains.trusted_match.provider_context_match_response import (
    ContextMatchResponseProviderRouter,
)
from pydantic import TypeAdapter, ValidationError

from adcp import ADCPClient
from adcp.protocols.mcp import MCPAdapter
from adcp.types import (
    BuildCreativeMultiSuccess,
    BuildCreativeSuccess,
    BuildCreativeVariantSuccess,
    CanonicalFormatKind,
    ContextMatchResponse,
    CreativeManifest,
    LegacyBuildCreativeResponse,
    LegacyPreviewCreativeResponse,
    ListCreativesResponse,
    McpWebhookPayload,
    PreviewCreativeVariantResponse,
    TmpOffer,
)
from adcp.types.core import AgentConfig, Protocol, TaskResult, TaskStatus
from adcp.webhook_result import (
    WebhookResultUnresolvedError,
    ambiguous_pairs,
    branch_documents,
    resolution_table,
    resolve_result,
    result_model,
    unresolved_pairs,
)
from tests.conformance import _round_trip as rt

#: A kind the DOCUMENT ADMITS, and not an invented one.
#:
#: This was `"future_canonical_format"`, which `core/canonical-format-kind.json` refuses:
#: that document is a closed `enum` of 16 members and nothing beside it opens the
#: vocabulary.  The decision is stated -- rebuild-plan.md §6: *"`x-extensible` and
#: `x-pattern` describe an open vocabulary in a namespace the validator ignores, so the
#: document's accepted set is the closed `enum` beside them and a closed `StrEnum` is
#: faithful to it"* -- and this document does not even carry `x-extensible`.
#:
#: Accepting an unknown member would also FAIL the project's own grading: the verifier
#: draws "outside the enum" as a counterexample and requires the class to refuse it, so a
#: forward-compatible enum is graded as a defect, not a feature.  The layer that used to
#: supply that behaviour upstream (`adcp.types._forward_compat`) is deliberately not
#: restored here.
#:
#: What these tests actually grade -- that a manifest survives readback across the task,
#: webhook and transport boundaries without being rewritten -- is unaffected by WHICH
#: admitted kind rides along, so they keep that coverage with a kind the schema states.
OTHER_KIND = "sponsored_placement"
TASK_CASES = ("preview", "build-single", "build-multi", "build-variants")
CASES = (*TASK_CASES, "context-match", "provider-context-match")


def assert_publicly_addressed(cls):
    """§4: this class is reachable at its own domain path, which is a supported import.

    **THE DOMAIN PATH AND NOT THE FLAT NAMESPACE.**  The generated domain tree is the ONE
    public type surface -- no private tree behind it, no re-export tree in front -- so every
    emitted class has a public address.  The FLAT `adcp.types` namespace is a different
    claim and a weaker one: it cannot bind every name, because several schemas declare the
    same word, so `CreativesItem` is absent from `adcp.types.__all__` while being perfectly
    public at `adcp.types.domains.creative.list_creatives_response`.  Measured, that is
    exactly the case for this one.

    What stood here asserted the OPPOSITE -- that the class is not public at all -- which
    was true of the previous generator's numbered anonymous classes (`Assets162`,
    `Idempotency3`) and is not true of anything this tree emits.
    """
    module = importlib.import_module(
        cls.__module__.replace("adcp.types._schemas", "adcp.types.domains")
    )
    assert getattr(module, cls.__name__, None) is cls


def _response_case(case, kind=OTHER_KIND):
    manifest = {
        # ``None`` means the property is absent: the schema admits no null.  It does NOT
        # mean the manifest addresses no format: `core/creative-manifest.json` is a XOR
        # over the two addressing forms -- `format_id` present and `format_kind` absent,
        # or `format_kind` present and `format_id` absent -- so a manifest carrying
        # NEITHER satisfies no branch and is refused with "0 of these clauses hold".
        #
        # So the `None` case addresses the format the v1 way, which is the branch the
        # other two cases do not reach: `format_id` is a structured `{agent_url, id}` and
        # not a string (`core/format-id.json`), and it selects `NamedFormatManifest` where
        # a `format_kind` selects `CanonicalFormatManifest`.
        **(
            {"format_kind": kind}
            if kind is not None
            else {
                "format_id": {
                    "agent_url": "https://creative.example.com",
                    "id": "legacy_display_300x250",
                }
            }
        ),
        "assets": {},
        "vendor_annotation": {"notes": ["preserved"]},
    }
    if case == "preview":
        return PreviewCreativeVariantResponse, {
            "response_type": "variant",
            "variant_id": "variant-1",
            "previews": [
                {
                    "preview_id": "preview-1",
                    "renders": [
                        {
                            "render_id": "render-1",
                            "output_format": "html",
                            "preview_html": "<p>Preview</p>",
                            "role": "primary",
                        }
                    ],
                }
            ],
            "manifest": manifest,
        }
    if case == "build-single":
        return BuildCreativeSuccess, {"creative_manifest": manifest}
    if case == "build-multi":
        return BuildCreativeMultiSuccess, {"creative_manifests": [manifest]}
    if case in ("context-match", "provider-context-match"):
        model = (
            ContextMatchResponse if case == "context-match" else ContextMatchResponseProviderRouter
        )
        return model, {
            # `type` is a required `Literal["context_match_response"]` on both routes --
            # the document pins it with a `const`, so it is not inferable and not
            # defaultable.
            "type": "context_match_response",
            "request_id": "request-1",
            "offers": [{"package_id": "package-1", "creative_manifest": manifest}],
        }
    return BuildCreativeVariantSuccess, {
        "creatives": [
            {
                "build_creative_id": "creative-1",
                "variants": [
                    {
                        "build_variant_id": "variant-1",
                        "creative_manifest": manifest,
                        "rank": 1,
                    }
                ],
            }
        ],
    }


def response_case(case, kind=OTHER_KIND):
    """``(model, payload)`` with the envelope's own ``status`` on every payload.

    Every one of these six documents composes ``core/protocol-envelope.json`` through
    `allOf`, which is where `status` is required -- measured, all six models declare it
    and all six declare it REQUIRED.  Requiredness is a conjunction of the node's own
    `required` and every ancestor's that applies to the same instance, and the previous
    generator dropped the `allOf`-composed half, which is why these fixtures were written
    without it.

    Added in ONE place rather than at the five return sites, so a case added later cannot
    omit it.
    """
    model, payload = _response_case(case, kind)
    return model, {"status": "completed", **payload}


def _through(parsed):
    """The wire object a vacuous-branch instance still carries.

    ``extra='allow'`` on every branch class keeps the members the branch does
    not declare, so dumping one hands back what came in.  ``exclude_none``
    because the schema admits no ``null`` for an absent property, and the
    vacuous branch declares a handful of optional fields of its own
    (``percentage``, ``current_step``, …) that were never in the payload.
    """
    return parsed.model_dump(mode="json", exclude_none=True)


def read_manifest(response, case):
    if case == "preview":
        return response.manifest
    if case == "build-single":
        return response.creative_manifest
    if case == "build-multi":
        return response.creative_manifests[0]
    if case in ("context-match", "provider-context-match"):
        return response.offers[0].creative_manifest
    return response.creatives[0].variants[0].creative_manifest


@pytest.mark.parametrize("kind", ["image", OTHER_KIND, None])
@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("json_input", [False, True], ids=["python", "json"])
def test_manifest_response_round_trip(case, kind, json_input):
    model, payload = response_case(case, kind)
    response = (
        model.model_validate_json(json.dumps(payload))
        if json_input
        else model.model_validate(payload)
    )
    manifest = read_manifest(response, case)
    if kind == "image":
        assert manifest.format_kind == CanonicalFormatKind.image
    else:
        assert manifest.format_kind == kind
    assert manifest.model_dump()["vendor_annotation"] == {"notes": ["preserved"]}
    assert model.model_validate_json(response.model_dump_json()).model_dump(mode="json") == (
        response.model_dump(mode="json")
    )
    assert_publicly_addressed(type(manifest))


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("mcp_content", [False, True], ids=["dict", "mcp-text"])
def test_adapter_keeps_manifest_response(case, mcp_content):
    model, payload = response_case(case)
    union = (
        LegacyPreviewCreativeResponse
        if case == "preview"
        else LegacyBuildCreativeResponse
        if case.startswith("build-")
        else model
    )
    data = [{"type": "text", "text": json.dumps(payload)}] if mcp_content else payload
    adapter = MCPAdapter(
        AgentConfig(
            id="creative-agent",
            agent_uri="https://seller.example/mcp",
            protocol=Protocol.MCP,
        )
    )
    result = adapter._parse_response(TaskResult(status=TaskStatus.COMPLETED, data=data), union)
    assert result.success, result.error
    assert result.status is TaskStatus.COMPLETED
    assert read_manifest(result.data, case).format_kind == OTHER_KIND
    reparsed = TypeAdapter(union).validate_json(result.data.model_dump_json())
    assert read_manifest(reparsed, case).format_kind == OTHER_KIND


def completed_task(case):
    _, result = response_case(case)
    return {
        "idempotency_key": "whk_manifest_readback_1",
        "operation_id": "operation-1",
        "task_id": "task-1",
        "task_type": "preview_creative" if case == "preview" else "build_creative",
        "status": "completed",
        "timestamp": "2026-09-01T00:00:00Z",
        "result": result,
    }


@pytest.mark.parametrize("case", TASK_CASES)
def test_async_response_union_and_webhook_round_trip(case):
    """The BARE union cannot name the branch; the ENVELOPE around it can.

    **THIS TEST WAS TWO CLAIMS AND ONLY ONE OF THEM IS ACHIEVABLE**, which is
    why it read as one failure.  What stood here asserted
    ``isinstance(TypeAdapter(AdcpAsyncResponseData).validate_json(payload),
    PreviewCreativeVariantResponse)`` -- and no conforming consumer can do
    that.

    ``core/async-response-data.json`` is a 42-branch untagged ``anyOf`` with no
    ``discriminator`` keyword, and -- re-derived the way
    ``adcontextprotocol/adcp#8964`` derives it, by VALIDATING the empty object
    against each branch rather than by a structural proxy -- **the empty object
    satisfies 15 of the 42 branches**.  So a ``preview_creative`` result
    validates against ``media-buy/get-products-async-response-working.json``, a
    plain jsonschema validator agrees, and the branch the union hands back is
    whichever vacuous one comes first.  **The emission is faithful; the document
    cannot discriminate.**

    So the bare-union half asserts what the document DOES guarantee, and the
    document states the rest itself:

        Because this shared webhook union is not tagged with the originating
        task type, callers MUST also validate a terminal result against that
        task or event's specific schema.

    Repointing this half is therefore not conceding a limitation -- it is
    asserting the document's own sentence.  Three things hold and are checked:
    the union ACCEPTS the payload, the branch it returns is UNINFORMATIVE (it
    admits the empty object too), and the payload SURVIVES the round trip
    whole, which is what lets the second validation recover the branch
    afterwards.

    The envelope half is a real requirement: ``core/mcp-webhook-payload.json``
    requires ``task_type`` and ``status`` beside ``result``, the pair names the
    schema, and :func:`adcp.webhooks.resolve_result` performs the MUST.  The
    branch INSIDE that schema stays pydantic's to pick -- a ``build_creative``
    result comes back as ``BuildCreativeSuccess`` or
    ``BuildCreativeMultiSuccess`` with no help from the caller.
    """
    model, payload = response_case(case)
    adapter = TypeAdapter(AdcpAsyncResponseData)
    result = adapter.validate_json(json.dumps(payload))
    # The union accepts, and the acceptance says nothing: this branch admits
    # ``{}`` as readily as it admits a preview response.
    assert isinstance(result, AdcpAsyncResponseData)
    assert not isinstance(result, model)
    assert isinstance(type(result).model_validate({}), type(result))
    # A ``TypeAdapter`` dump has no ``exclude_none`` default of its own, and
    # the schema admits no ``null`` for an omitted property.
    reparsed = adapter.validate_json(adapter.dump_json(result, exclude_none=True))
    assert type(reparsed) is type(result)
    # Nothing was dropped on the way through: ``extra='allow'`` keeps every
    # member the vacuous branch does not declare, which is why the second
    # validation has a whole payload to work with.
    assert read_manifest(model.model_validate(_through(result)), case).format_kind == OTHER_KIND

    webhook = McpWebhookPayload.model_validate_json(json.dumps(completed_task(case)))
    resolved = resolve_result(webhook)
    assert isinstance(resolved, model)
    assert read_manifest(resolved, case).format_kind == OTHER_KIND
    reparsed_webhook = McpWebhookPayload.model_validate_json(webhook.model_dump_json())
    assert isinstance(resolve_result(reparsed_webhook), model)
    assert read_manifest(resolve_result(reparsed_webhook), case).format_kind == OTHER_KIND
    # The raw mapping a receiver holds resolves to the same branch as the
    # validated envelope: the pair is read off the wire either way.
    assert isinstance(resolve_result(completed_task(case)), model)


def test_the_empty_object_satisfies_fifteen_of_the_forty_two_branches():
    """The vacuity, re-derived by VALIDATION rather than by a structural proxy.

    ``adcontextprotocol/adcp#8964`` asks the real question -- does ``{}``
    validate against this branch -- and answers **15 of 42**.  A structural
    proxy (no top-level ``required``, ``additionalProperties`` not ``false``, no
    ``allOf``) answers 17, and the two it over-counts are
    ``MediaBuyCommitmentResponse`` and ``ControlMediaBuyResponse``: both are
    ``oneOf`` parents carrying ``discriminator: {propertyName: status}`` with no
    top-level ``required`` of their own, and ``{}`` satisfies no branch of either
    because every branch requires ``status``.

    Asserted here so the resolver's reason for existing is a measurement in the
    suite and not a sentence in a docstring.  The 15 are exactly the ``working``
    and ``input-required`` branches, which is the shape of the defect: a
    progress payload's schema requires nothing, so it accepts a completed
    response.
    """
    union = json.loads((rt.schema_root() / "core/async-response-data.json").read_text())
    # A branch is a bare ``$ref`` plus a title and a description, so validating
    # the branch IS validating the document it names -- through the bundle's own
    # validator, which resolves every nested reference the way a conforming
    # consumer's would.
    vacuous = [
        branch["title"]
        for branch in union["anyOf"]
        if rt.is_valid(branch["$ref"].split("/schemas/", 1)[1].split("/", 1)[1], {})
    ]
    assert len(union["anyOf"]) == 42
    assert len(vacuous) == 15, vacuous
    assert all(name.endswith(("Working", "InputRequired")) for name in vacuous), vacuous


def test_the_derivation_reaches_every_branch_of_the_union():
    """42 of 42 branches, derived from the bundle and not typed out.

    The whole point of deriving: a hand-written table of 42 branches is a table
    that goes stale on a bundle bump, and nobody can tell a stale row from a
    correct one by reading it.  Two readings of the bundle produce this, and
    both are the bundle's own statements -- ``manifest.task_result_resolution``
    (the procedure ``core/tasks-get-response.json`` says consumers MUST use)
    and the ONE ``if``/``then`` clause ``core/mcp-webhook-payload.json`` carries
    itself.

    The second is what reaches the 42nd branch: ``task_result_resolution``
    never names ``media-buy/get-products-rejected.json`` at all, because a
    terminal status resolves to the task's ``response_schema`` and that is
    ``get-products-response.json``.  The envelope's clause -- ``task_type:
    get_products`` plus ``result.status: rejected`` -> the rejected document --
    is both the 42nd branch and the fix shape #8964 asks for, already applied
    once by upstream's own hand for one of the 42 positions.
    """
    table = resolution_table()
    reached = {branch for one in table.values() for branch in one.branches}
    assert len(branch_documents()) == 42
    assert reached == set(branch_documents()), set(branch_documents()) - reached
    assert len({one.model for one in table.values() if one.model}) == 42
    # The envelope supplies exactly one pair, and it is the one the manifest
    # cannot reach.
    by_envelope = [one for one in table.values() if one.source == "envelope"]
    assert [(one.task_type, one.status, one.document) for one in by_envelope] == [
        ("get_products", "rejected", "media-buy/get-products-rejected.json")
    ]


def test_the_derivation_s_coverage_and_its_holes_are_measured():
    """What the derivation covers, and what happens to a pair it does not.

    ``task_type x status`` is 38 x 9 = 342 pairs and the union has 42 branches,
    so most pairs cannot resolve and the useful question is which.  Three
    populations, each a measurement rather than a target:

    * **153 pairs are NAMED** by the derivation at all.
    * **87 of those resolve** to exactly one branch of the union, across 16 of
      the 38 task types.
    * **66 name a schema the union does not contain** -- 22 task types whose
      webhook ``result`` has no branch to be, which is the other half of #8964:
      the manifest knows exactly what a ``sync_accounts`` webhook carries and
      the union has no branch for it, so the vacuous branches accept it and
      nothing notices.
    * **0 name more than one branch.**  Accumulated rather than overwritten so
      that this is read and not assumed, and :func:`resolve_result` raises for
      an ambiguous pair rather than choosing between two documents the bundle
      gives no precedence between.

    An unnamed pair -- ``canceled``, ``auth-required``, ``unknown``, and every
    status a task's manifest entry omits -- is absent from the table and raises.
    """
    table = resolution_table()
    assert len(table) == 153
    assert sum(1 for one in table.values() if one.model) == 87
    assert len({one.task_type for one in table.values() if one.model}) == 16
    assert len(unresolved_pairs()) == 66
    assert len({one.task_type for one in unresolved_pairs()}) == 22
    assert ambiguous_pairs() == ()


@pytest.mark.parametrize(
    ("task_type", "status", "expected"),
    [
        # The envelope's own if/then, and the generic terminal rule beside it.
        ("get_products", "rejected", "GetProductsRejected"),
        ("get_products", "completed", "GetProductsResponse"),
        ("get_products", "working", "GetProductsWorking"),
        # `terminal_schema_overrides`, for the one task_type with no `tools`
        # entry at all: a delivery-report event rather than a called tool.
        ("media_buy_delivery", "completed", "MediaBuyDeliveryWebhookResult"),
        # A wrapper followed through `allOf` to the branch the union holds:
        # `buy-products-response.json` is a title over
        # `media-buy-commitment-response.json`, and the compact lifecycle's
        # async schemas are titles over `core/compact-task-*.json`.
        ("buy_products", "completed", "MediaBuyCommitmentResponse"),
        ("buy_products", "submitted", "CompactTaskSubmitted"),
        ("accept_proposal", "working", "CompactTaskWorking"),
    ],
)
def test_a_pair_names_the_branch_the_bundle_says_it_does(task_type, status, expected):
    """Spot checks on the derivation, one per reading that produces an answer.

    Not a second table -- seven rows against a 153-entry derivation, each
    chosen because a different clause of it is what answers.
    """
    found = result_model(task_type, status)
    assert found is not None, (task_type, status)
    assert found.__name__ == expected


def test_a_pair_that_names_no_branch_raises_instead_of_guessing():
    """The refusals, which are the whole difference from the bare union.

    A bare union answers every one of these with a vacuous branch and no error.
    This answers with the measurement: which pair, and -- where the bundle does
    name a schema -- which schema the caller should validate against instead.
    """
    # `canceled` is named by nothing: `core/tasks-get-response.json` says in as
    # many words that "canceled tasks may omit" the result.
    with pytest.raises(WebhookResultUnresolvedError, match="is named by task_type"):
        resolve_result({"task_type": "create_media_buy", "status": "canceled", "result": {}})
    # The pair DOES name a schema and the union has no branch for it, so the
    # error carries the schema rather than refusing bare.
    with pytest.raises(WebhookResultUnresolvedError, match="NOT a branch") as raised:
        resolve_result({"task_type": "sync_accounts", "status": "completed", "result": {}})
    assert raised.value.document == "account/sync-accounts-response.json"
    # No `result` is not an error: the member is optional on the envelope.
    assert resolve_result({"task_type": "get_products", "status": "canceled"}) is None
    # No pair to resolve on at all.
    with pytest.raises(WebhookResultUnresolvedError, match="requires"):
        resolve_result({"result": {}})


def test_a_result_disagreeing_with_its_own_envelope_is_refused():
    """A pydantic ``ValidationError`` propagates, and that is the point.

    ``core/mcp-webhook-payload.json`` calls ``result`` the "Task-specific
    payload matching the status", so a payload that does not match the schema
    its own envelope names is a conformance finding and not something to
    recover from.  Through the bare union this is unobservable -- the vacuous
    branch accepts it.
    """
    envelope = completed_task("preview")
    envelope["task_type"] = "sync_creatives"
    with pytest.raises(ValidationError):
        resolve_result(envelope)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", TASK_CASES)
async def test_public_completed_task_parser_keeps_manifest_readback(case):
    model, _ = response_case(case)
    payload = completed_task(case)
    client = ADCPClient(
        AgentConfig(
            id="creative-agent", agent_uri="https://seller.example/mcp", protocol=Protocol.MCP
        ),
        allow_unauthenticated_webhooks=True,
    )
    with pytest.deprecated_call(match="handle_webhook_legacy"):
        result = await client.handle_webhook_legacy(
            payload,
            task_type=payload["task_type"],
            operation_id=payload["operation_id"],
        )
    assert result.success, result.error
    assert result.status is TaskStatus.COMPLETED
    # A successful untyped fallback would silently hide strict-union rejection.
    assert isinstance(result.data, AdcpAsyncResponseData)
    # **AND THE BRANCH IS NOT THE TASK'S, for the reason the test above
    # measures.** ``TaskResult[AdcpAsyncResponseData]`` is the BARE union, so
    # the parser's own answer is whichever of the 15 branches that admit the
    # empty object comes first -- the document's own sentence is that a caller
    # MUST validate again against the task's specific schema, and this parser
    # is not handed the ``task_type`` to do it with.  What it does guarantee is
    # that nothing is lost, which is what the second validation needs.
    assert read_manifest(model.model_validate(_through(result.data)), case).format_kind == (
        OTHER_KIND
    )
    # ``TaskResult`` is a plain pydantic model: its dump carries every ``None``
    # as ``null`` unless told otherwise, and a JSON ``null`` is not an AdCP
    # document (#1547). Dump the way the CLI does, with ``exclude_none``.
    reparsed = TaskResult[AdcpAsyncResponseData].model_validate_json(
        result.model_dump_json(exclude_none=True)
    )
    assert type(reparsed.data) is type(result.data)
    assert read_manifest(model.model_validate(_through(reparsed.data)), case).format_kind == (
        OTHER_KIND
    )
    # The ENVELOPE the webhook arrived as is what names the branch, and it is
    # the payload this parser was handed.
    assert isinstance(resolve_result(payload), model)


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("reuse_instance", [False, True], ids=["dump", "instance"])
def test_manifest_readback_is_the_input_model_s_own_branch(case, reuse_instance):
    """What a read-back manifest does when handed back to the input model.

    The vocabulary half of this test is gone with the open-vocabulary decision:
    ``format_kind`` is ``str`` on every model and none of them refuses a value,
    because a pinned SDK cannot tell a kind a seller invented from a kind
    defined after its pin (see :mod:`adcp.types.canonical_creative`). Choosing
    which kinds to accept is the caller's, through
    ``adcp.types.is_canonical_format_kind``.

    **AND THE STRUCTURAL HALF REVERSES.**  What stood here asserted
    ``not isinstance(manifest, input_model)`` and a ``model_type`` refusal of the
    instance -- true of the FLAT emission, where a readback node was an unrelated
    class.  `CLAUDE.md` records the decision this one makes: ``core/creative-
    manifest.json#`` emits ``CreativeManifest`` as the base with
    ``NamedFormatManifest`` / ``CanonicalFormatManifest`` as its branches, and
    *"``isinstance`` holds against the parent"*.  Measured, the readback node's
    mro is ``CanonicalFormatManifest -> CreativeManifest -> …``, so refusing it
    would be refusing the document's own branch.

    So both halves of the handoff are graded here: the instance is accepted,
    unchanged and still its branch, and the dump validates back into the same
    branch with the kind it was given.

    The two spellings of the input model are ONE object -- ``adcp.types``'s flat
    name and the domain path are the same class, asserted below -- so the model
    is no longer parametrized over them.
    """
    assert CreativeManifest is InputManifest

    model, payload = response_case(case)
    manifest = read_manifest(model.model_validate(payload), case)
    assert isinstance(manifest, CreativeManifest)

    value = manifest if reuse_instance else manifest.model_dump(mode="json")
    readback = CreativeManifest.model_validate(value)

    assert type(readback) is type(manifest)
    assert readback.format_kind == OTHER_KIND
    if reuse_instance:
        # An instance of a branch is not revalidated into a copy.
        assert readback is manifest


@pytest.mark.parametrize("case", ["build-variants", "context-match", "provider-context-match"])
def test_nested_readback_accepts_known_source_models(case):
    model, payload = response_case(case, "image")
    collection = "creatives" if case == "build-variants" else "offers"
    source = InputBuildCreative if case == "build-variants" else TmpOffer
    payload[collection][0] = source.model_validate(payload[collection][0])
    response = model.model_validate(payload)
    assert read_manifest(response, case).format_kind == CanonicalFormatKind.image
    node = getattr(response, collection)[0]
    assert_publicly_addressed(type(node))


def test_nested_build_readback_preserves_envelopes_and_constraints():
    """The envelope is carried where the document STATES it, and nowhere else.

    ``media-buy/build-creative-response.json#/oneOf/2`` composes
    ``core/version-envelope.json``, so the response branch carries
    ``adcp_version`` -- and its ``creatives`` items and their ``variants``
    items state no envelope at all. Reading 1 is what decides this: a class
    accepts exactly what its own document accepts, so a nested item class that
    inherited ``adcp_version`` would admit a property no node of the document
    states, at every position of the array. The constraints the items DO state
    are asserted below and are unchanged.
    """
    model, payload = response_case("build-variants")
    response = model.model_validate(payload)
    creative = response.creatives[0]
    variant = creative.variants[0]
    assert isinstance(response, AdcpVersionEnvelope)
    for node in (creative, variant):
        assert not isinstance(node, AdcpVersionEnvelope)
        assert "adcp_version" not in type(node).model_fields
        assert_publicly_addressed(type(node))

    payload["creatives"][0]["variants"][0]["rank"] = 0
    with pytest.raises(ValidationError) as invalid_rank:
        model.model_validate(payload)
    assert invalid_rank.value.errors()[0]["type"] == "greater_than_equal"
    payload["creatives"][0]["variants"] = []
    with pytest.raises(ValidationError) as empty_variants:
        model.model_validate(payload)
    assert empty_variants.value.errors()[0]["type"] == "too_short"
    payload["creatives"] = []
    with pytest.raises(ValidationError) as empty_creatives:
        model.model_validate(payload)
    assert empty_creatives.value.errors()[0]["type"] == "too_short"


def test_build_readback_preserves_empty_and_error_branch_rules():
    """Both payloads carry the envelope's own ``status``, for ``response_case``'s
    reason: it is required one ``allOf`` up and these documents compose it. A
    payload omitting it is refused on ``status`` FIRST -- ``missing ('status',)``
    precedes ``too_short ('creative_manifests',)`` -- so the array rule this
    test exists for would be read out of ``errors()[0]`` of a different refusal.
    """
    with pytest.raises(ValidationError) as empty_manifests:
        BuildCreativeMultiSuccess.model_validate({"status": "completed", "creative_manifests": []})
    assert empty_manifests.value.errors()[0]["type"] == "too_short"

    response = BuildCreativeVariantSuccess.model_validate(
        {
            "status": "completed",
            "creatives": [
                {
                    "build_creative_id": "creative-1",
                    "errors": [
                        {"code": "BUILD_FAILED", "message": "Unable to build this creative"}
                    ],
                }
            ],
        }
    )
    assert response.creatives[0].variants is None
    assert response.creatives[0].errors[0].code == "BUILD_FAILED"


def test_a_directly_listed_creative_retains_its_kind():
    """A listed creative retains the ``format_kind`` the seller sent.

    This test used to assert the opposite — that a listed creative's
    ``format_kind`` stays inside the closed enum — because the enum was the
    type. ``format_kind`` is now ``str`` on every model and none of them
    refuses a value (see :mod:`adcp.types.canonical_creative`), so retaining is
    the required behaviour and refusing would be the defect: a buyer on an
    older SDK would fail the whole page because one row named a kind promoted
    after their release.

    There is no strict counterpart to pair this with. Deciding which kinds to
    accept is the caller's, through ``adcp.types.is_canonical_format_kind``,
    graded by ``tests/test_open_format_kind_vocabulary.py``.
    """
    payload = {
        # The response envelope's own `status`, required one level up by
        # `core/protocol-envelope.json` (`#/allOf/1`) and distinct from each
        # creative's `status` below; 9-member enum there, "completed" chosen.
        "status": "completed",
        "query_summary": {"total_matching": 1, "returned": 1},
        "pagination": {"has_more": False},
        "creatives": [
            {
                "creative_id": "creative-1",
                "name": "Image",
                "format_kind": "image",
                "status": "approved",
                "created_date": "2026-09-01T00:00:00Z",
                "updated_date": "2026-09-01T00:00:00Z",
            }
        ],
    }
    assert ListCreativesResponse.model_validate(payload).creatives[0].format_kind == (
        CanonicalFormatKind.image
    )
    payload["creatives"][0]["format_kind"] = OTHER_KIND
    listed = ListCreativesResponse.model_validate(payload).creatives[0]
    assert listed.format_kind == OTHER_KIND
    # Retained on the wire too, so a buyer can route it and hand it back.
    assert listed.model_dump(mode="json")["format_kind"] == OTHER_KIND
