"""Runtime contracts retained by post-generation compatibility fixes."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ValidationError

# `adcp.types.response_dispatch` was the previous generator's compatibility seam
# over `model_validate` -- two private helpers that dropped post-2.0 pydantic
# keywords left at their defaults. It was removed with the rest of that layer
# (`639134c75`, "the seam their behavioural code reaches types through"), and no
# document states it, so the test that graded its two helpers is gone with it.


def test_product_signal_targeting_option_keeps_discriminated_signal_ref() -> None:
    """``SignalRef`` is a BASE CLASS with one subclass per branch, not an alias.

    ``rebuild-plan.md`` §4 *"A union root: the base, the branches, and how a
    payload reaches its branch"*: a ``oneOf`` root emits *"a base carrying
    ``BranchDispatchMixin`` plus one class per branch, and the base's name is
    what every referrer imports"*. So the referring field is annotated with the
    BASE -- there is no ``Annotated[A | B | C]`` to unpack with ``get_args``,
    and the discriminator is a class fact (``_BRANCH_DISCRIMINATOR``) the mixin
    reads to build the union rather than ``FieldInfo`` metadata.

    What the test graded is unchanged and is asserted below: the reference
    position carries the discriminated union, a payload reaches the branch its
    ``scope`` names, and a scope no branch pins is refused.
    """
    from adcp.types.domains.core.signal_ref import SignalRef

    from adcp import ProductSignalTargetingOption

    assert ProductSignalTargetingOption.model_fields["signal_ref"].annotation is SignalRef
    assert SignalRef._BRANCH_DISCRIMINATOR == "scope"
    assert SignalRef._branch_combinator() == "oneOf"
    assert all(issubclass(branch, SignalRef) for branch in SignalRef._branch_models)
    assert ProductSignalTargetingOption.model_json_schema()["properties"]["signal_ref"][
        "description"
    ].startswith("Canonical signal reference.")

    option = ProductSignalTargetingOption.model_validate(
        {"signal_ref": {"scope": "product", "signal_id": "signal_1"}}
    )
    # The branch, reached through the base: ``isinstance`` holds against both.
    assert isinstance(option.signal_ref, SignalRef)
    assert type(option.signal_ref) in SignalRef._branch_models
    assert option.signal_ref.scope == "product"

    with pytest.raises(ValidationError) as unknown_scope:
        ProductSignalTargetingOption.model_validate(
            {"signal_ref": {"scope": "unknown", "signal_id": "signal_1"}}
        )
    # The keyword the refusal names is the document's own (§4: a payload
    # satisfying no branch fails at the discriminating property).
    assert [error["type"] for error in unknown_scope.value.errors()] == ["oneOf"]
    assert unknown_scope.value.errors()[0]["loc"] == ("signal_ref", "scope")

    with pytest.raises(ValidationError):
        ProductSignalTargetingOption.model_validate({"signal_ref": "signal_1"})


def test_creative_representation_keeps_canonical_format_contract() -> None:
    """The canonical contract moved to the BRANCH, and the vocabulary CLOSED.

    Two decisions, both the document's:

    * ``core/creative-representation.json`` is an ``allOf`` over
      ``core/creative-manifest.json`` -- itself a union over the two addressing
      forms (``CLAUDE.md`` → Formats) -- and a conjunct requiring ``format_kind``.
      ``rebuild-plan.md`` §4 *"where the target is itself a union root, the
      branch DISTRIBUTES"*, so the base declares only what every branch shares
      (``representation_id``, ``source``) and ``format_kind`` sits on the
      ``format_kind`` branch. Reading it off the base is reading a field the
      document states one level down.
    * ``format_kind`` is the CLOSED 16-member enum of
      ``core/canonical-format-kind.json``. ``rebuild-plan.md`` §6:
      ``x-extensible`` *"describes an open vocabulary in a namespace the
      validator ignores, so the document's accepted set is the closed ``enum``
      beside them and a closed ``StrEnum`` is faithful to it"* -- and this
      document carries no ``x-extensible`` at all. What used to widen it
      (``adcp.types._forward_compat``) is deleted by
      ``verdicts/the-dead-patch-layer.md``, so the parity declaration
      ``format_kind_is_an_open_vocabulary_by_decision`` no longer occurs and is
      deleted from ``tests/conformance/_schema_parity.py`` with the other two.
    """
    from adcp.types.domains.core.creative_representation import CreativeRepresentation

    from adcp import LegacyBuildCreativeRequest
    from adcp.types import CanonicalFormatKind
    from adcp.types._runtime import ForbiddenGroups

    canonical_branch = {
        branch.__name__: branch for branch in CreativeRepresentation._branch_models
    }["CreativeRepresentationFormatKind"]
    assert canonical_branch.model_fields["format_kind"].annotation is CanonicalFormatKind
    assert "format_kind" in CreativeRepresentation._ROOT_REQUIRED
    assert "image" in {kind.value for kind in CanonicalFormatKind}
    schema = canonical_branch.model_json_schema()
    assert schema["properties"]["format_kind"]["description"].startswith("Canonical 3.2 path.")
    # ``#/allOf/1``'s ``not`` is lowered to a RULE on the union base rather than
    # published as a schema keyword -- §5's combinators row, "rules are
    # after-validators, written once".
    assert (
        ForbiddenGroups((("format_id",), ("format_option_ref",), ("representation_selection",)))
        in CreativeRepresentation._adcp_rules
    )

    representation = {
        "representation_id": "representation_1",
        "source": {"system": "test", "source_representation": "source_1"},
        "format_kind": "image",
        "assets": {},
    }
    parsed_representation = CreativeRepresentation.model_validate(representation)
    assert type(parsed_representation) is canonical_branch
    assert parsed_representation.format_kind is CanonicalFormatKind.image

    # A kind outside the closed enum is REFUSED, at the base and at a nested
    # position. Choosing which kinds a caller tolerates is still the caller's,
    # through ``adcp.types.is_canonical_format_kind``.
    with pytest.raises(ValidationError) as unknown_kind:
        CreativeRepresentation.model_validate({**representation, "format_kind": "unknown"})
    assert unknown_kind.value.errors()[0]["type"] == "enum"

    # A seller-bound field the canonical path forbids, with a value the
    # document admits: the rule refuses the pairing rather than the value.
    with pytest.raises(ValidationError, match="which the document forbids"):
        CreativeRepresentation.model_validate(
            {
                **representation,
                "format_option_ref": {
                    "scope": "product",
                    "product_id": "product_1",
                    "format_option_id": "format_option_1",
                },
            }
        )

    representation_set = {
        "creative_id": "creative_1",
        "revision_id": "revision_1",
        "revision_content_digest": "sha256:" + "0" * 64,
        "name": "Test creative",
        "representations": [{**representation, "format_kind": "unknown"}],
    }
    with pytest.raises(ValidationError) as nested_unknown:
        LegacyBuildCreativeRequest.model_validate(
            {
                "idempotency_key": "idem-123456789012",
                "creative_representation_set": representation_set,
            }
        )
    assert ("creative_representation_set", "representations", 0, "format_kind") in {
        error["loc"] for error in nested_unknown.value.errors()
    }


def test_transformer_requires_a_canonical_or_legacy_output_declaration() -> None:
    from adcp.types.domains.core.transformer import Transformer

    from adcp.types import ListTransformersResponse

    base_transformer = {"transformer_id": "transformer_1", "name": "Test transformer"}
    with pytest.raises(ValidationError):
        ListTransformersResponse.model_validate({"transformers": [base_transformer]})

    assert (
        Transformer.model_validate(
            {**base_transformer, "output_capability_ids": ["capability_1"]}
        ).output_capability_ids
        is not None
    )
    assert (
        Transformer.model_validate(
            {
                **base_transformer,
                "output_format_ids": [{"agent_url": "https://creative.example", "id": "format_1"}],
            }
        ).model_dump()["output_format_ids"]
        is not None
    )


def test_public_response_bases_remain_constructible_and_arms_remain_specific() -> None:
    from adcp.types.domains.account.sync_governance_response import SyncGovernanceResponse1
    from adcp.types.domains.compliance.comply_test_controller_response import (
        ComplyTestControllerResponse1,
    )
    from adcp.types.domains.content_standards.create_content_standards_response import (
        CreateContentStandardsResponse1,
    )
    from adcp.types.domains.content_standards.list_content_standards_response import (
        ListContentStandardsResponse1,
    )
    from adcp.types.domains.content_standards.update_content_standards_response import (
        UpdateContentStandardsResponse1,
    )

    from adcp.types import (
        ComplyTestControllerResponse,
        CreateContentStandardsResponse,
        ListContentStandardsResponse,
        SyncGovernanceResponse,
        UpdateContentStandardsResponse,
    )
    from adcp.types.aliases import (
        CreateContentStandardsSuccessResponse,
        ListContentStandardsSuccessResponse,
        UpdateContentStandardsSuccessResponse,
    )

    # `compliance/comply-test-controller-response.json#/oneOf/0` is titled
    # "List Scenarios Success", so that is the branch's name; upstream's
    # `ComplyListScenariosResponse` is a word no node of the document states and
    # `aliases.py` declines to invent it.
    from adcp.types.compliance import ListScenariosSuccess as ComplyListScenariosResponse
    from adcp.utils.response_parser import parse_json_or_text

    # ``status`` is on every payload because the ENVELOPE requires it:
    # ``core/protocol-envelope.json`` is composed one ``allOf`` up by each of
    # these documents, and requiredness is the conjunction of the node's own
    # ``required`` and every ancestor's that applies to the same instance
    # (``CLAUDE.md`` → "REQUIREDNESS IS A CONJUNCTION"). A response without it
    # is a document any conforming peer refuses, not merely this suite.
    envelope = {"status": "completed"}
    responses = (
        (
            ComplyTestControllerResponse,
            ComplyListScenariosResponse,
            ComplyTestControllerResponse1,
            {**envelope, "success": True, "scenarios": []},
            {**envelope, "success": True},
            {**envelope, "success": "invalid"},
            {"scenarios": []},
        ),
        (
            CreateContentStandardsResponse,
            CreateContentStandardsSuccessResponse,
            CreateContentStandardsResponse1,
            {**envelope, "standards_id": "standards_1"},
            dict(envelope),
            dict(envelope),
            {"standards_id": "standards_1"},
        ),
        (
            ListContentStandardsResponse,
            ListContentStandardsSuccessResponse,
            ListContentStandardsResponse1,
            {**envelope, "standards": []},
            dict(envelope),
            dict(envelope),
            {"standards": []},
        ),
        (
            SyncGovernanceResponse,
            SyncGovernanceResponse1,
            SyncGovernanceResponse1,
            {**envelope, "accounts": []},
            dict(envelope),
            dict(envelope),
            {"accounts": []},
        ),
        (
            UpdateContentStandardsResponse,
            UpdateContentStandardsSuccessResponse,
            UpdateContentStandardsResponse1,
            {**envelope, "success": True, "standards_id": "standards_1"},
            {**envelope, "success": False, "standards_id": "standards_1"},
            {**envelope, "success": False, "standards_id": "standards_1"},
            {"standards_id": "standards_1"},
        ),
    )

    for (
        response_base,
        response_alias,
        response_arm,
        valid,
        invalid_arm,
        invalid_base,
        preserved_fields,
    ) in responses:
        assert issubclass(response_base, BaseModel)
        # A base takes the PAYLOAD and answers with the branch it satisfies --
        # §4's "how a payload reaches its branch". An argument-free base is no
        # longer a value: the envelope requires ``status`` and the dispatch
        # requires a branch, so there is nothing for it to be.
        with pytest.raises(ValidationError) as empty:
            response_base()
        assert empty.value.errors()
        assert response_alias is response_arm
        assert issubclass(response_arm, response_base)
        assert isinstance(response_alias.model_validate(valid), response_base)

        direct = response_base.model_validate(valid)
        direct_json = response_base.model_validate_json(json.dumps(valid))
        parsed = parse_json_or_text(valid, response_base)
        for result in (direct, direct_json, parsed):
            assert type(result) is response_arm
            assert all(getattr(result, name) == value for name, value in preserved_fields.items())

        # An instance of a branch is not revalidated into a copy.
        assert response_base.model_validate(direct) is direct

        with pytest.raises(ValidationError):
            response_alias.model_validate(invalid_arm)
        with pytest.raises(ValidationError):
            response_base.model_validate(invalid_base)
        with pytest.raises(ValueError):
            parse_json_or_text(invalid_base, response_base)


_MEDIA_BUY_UNCONDITIONAL_FIELDS = {
    "idempotency_key": "idem-key-0123456789",
    "account": {"account_id": "acct_1"},
    "brand": {"brand_id": "brand_1", "domain": "example.com"},
    "start_time": "2026-11-01T00:00:00Z",
    "end_time": "2026-11-30T00:00:00Z",
}


def test_create_media_buy_request_requires_one_root_anyof_group() -> None:
    """``create-media-buy-request.json`` declares three ways to be a media buy.

    Root ``required`` names the five fields every branch shares; the root
    ``anyOf`` names the three groups, one of which a request has to carry. A
    document with the five and none of the three is a media buy with no
    packages, no budget and no proposal.

    **The three groups are lowered to BRANCH CLASSES, not to a ``RequiredGroups``
    rule**, because each group states more than a presence set -- a ``const`` on
    ``budget_allocation.mode``, per-item conjuncts on ``packages``, a ``not`` over
    its siblings. ``rebuild-plan.md`` §4 *"a ``oneOf``/``anyOf`` root emits a base
    plus one class per branch"* applies, so the refusal is each branch's own
    missing requirement, with the branch NAMED, rather than one sentence about
    groups. The branch names are §4's candidates by first fit -- each document's
    own ``title`` -- so they say what the branch is.
    """
    from adcp.types.domains.media_buy.create_media_buy_request import CreateMediaBuyRequest

    with pytest.raises(ValidationError) as no_group:
        CreateMediaBuyRequest.model_validate(dict(_MEDIA_BUY_UNCONDITIONAL_FIELDS))

    reasons = str(no_group.value)
    assert "#/anyOf/0 (ExplicitPackagesWithFixedAllocation)" in reasons
    assert "#/anyOf/1 (ExplicitPackagesWithSellerOptimizedAllocation)" in reasons
    assert "#/anyOf/2 (CommittedProposalExecution)" in reasons
    assert {error["loc"][0] for error in no_group.value.errors()} == {
        "packages",
        "total_budget",
        "budget_allocation",
        "proposal_id",
    }

    committed = CreateMediaBuyRequest.model_validate(
        {
            **_MEDIA_BUY_UNCONDITIONAL_FIELDS,
            "proposal_id": "prop_1",
            "total_budget": {"amount": 1000.0, "currency": "USD"},
        }
    )
    assert type(committed).__name__ == "CommittedProposalExecution"
    assert isinstance(committed, CreateMediaBuyRequest)
    assert committed.proposal_id == "prop_1"
    assert committed.packages is None


def test_sync_creatives_request_takes_assignment_operations_without_creatives() -> None:
    """``creatives`` is one arm of a root ``anyOf``, not an unconditional field.

    AdCP 3.2 moved ``creatives`` out of root ``required`` into a group alongside
    ``assignments`` and ``assignment_operations``, so a request that traffics
    existing creative IDs carries no ``creatives`` at all.

    The ``RequiredGroups`` mechanism is unchanged; its WORDING is not. The
    refusal now names the groups it looked for, in the document's own order --
    ``rebuild-plan.md`` §2 *"A refusal is the document's"*.
    """
    from adcp.types.domains.creative.sync_creatives_request import SyncCreativesRequest

    base = {"idempotency_key": "idem-key-0123456789", "account": {"account_id": "acct_1"}}

    with pytest.raises(
        ValidationError,
        match=(
            "none of these groups is present, the document requires at least one: "
            "'creatives'; 'assignments'; 'assignment_operations'"
        ),
    ):
        SyncCreativesRequest.model_validate(dict(base))

    assignments_only = SyncCreativesRequest.model_validate(
        {
            **base,
            "assignment_operations": [
                {"operation": "assign", "creative_id": "creative_1", "package_id": "package_1"}
            ],
        }
    )
    assert assignments_only.creatives is None
    assert assignments_only.assignment_operations is not None
