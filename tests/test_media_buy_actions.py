from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from adcp.media_buy_actions import (
    ActionAvailabilityStatus,
    ActionDiagnosticCode,
    ActionIntent,
    ActionKnowledge,
    ActionTask,
    ChangeTermSelection,
    ConstraintOutcome,
    MediaBuyActionError,
    assess_media_buy_action,
    assess_update_media_buy_actions,
    dispatch_media_buy_action,
    evaluate_action_constraints,
    materialize_change_terms,
    project_available_actions,
    reassess_media_buy_action,
    route_media_buy_action,
)
from adcp.validation.schema_loader import get_named_validator

NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
GOLDEN_FIXTURE = Path(__file__).parent / "fixtures" / "media_buy_action_assessment.json"
ACTION_SCHEMA = (
    Path(__file__).parent.parent
    / "schemas"
    / "cache"
    / "3.2.0-rc.1"
    / "core"
    / "canonical-media-buy-action.json"
)


def _product(*actions: dict[str, Any]) -> dict[str, Any]:
    return {"allowed_actions": list(actions)}


def _term(
    action: str,
    *,
    term_id: str | None = None,
    mode: str = "self_serve",
    statuses: list[str] | None = None,
    constraints: dict[str, Any] | None = None,
    conditions: list[str] | None = None,
    sla: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "term_id": term_id or f"right_{action}",
        "action": action,
        "service_mode": mode,
    }
    if statuses is not None:
        value["allowed_statuses"] = statuses
    if constraints is not None:
        value["constraints"] = constraints
    if conditions is not None:
        value["conditions"] = conditions
    if sla is not None:
        value["processing_sla"] = sla
    return value


def _proposal(*terms: dict[str, Any], present: bool = True) -> dict[str, Any]:
    commercial_terms: dict[str, Any] = {}
    if present:
        commercial_terms["change_terms"] = list(terms)
    return {"commercial_terms": commercial_terms}


def _buy(
    status: str,
    *actions: dict[str, Any],
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"status": status, "available_actions": list(actions)}
    if proposal is not None:
        value["accepted_proposal"] = proposal
    return value


def _live(
    action: str,
    *,
    term_id: str | None = None,
    mode: str = "self_serve",
    task: str | None = None,
    terms_ref: str | None = None,
    sla: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "action": action,
        "mode": mode,
        "change_term_id": term_id or f"right_{action}",
    }
    if task is not None:
        value["task"] = task
    if terms_ref is not None:
        value["terms_ref"] = terms_ref
    if sla is not None:
        value["sla"] = sla
    return value


def _commercial_terms(*change_terms: dict[str, Any]) -> dict[str, Any]:
    # A purchase's requiredness is a CONJUNCTION. `media-buy/commercial-terms.json`
    # declares `purchases.items` as an `allOf` of `media-buy/product-purchase.json`
    # and a bare `required: ['product_id', 'pricing_option_id', 'pricing',
    # 'start_time', 'end_time']` conjunct -- so `start_time` and `end_time` are
    # required HERE while `product-purchase.json`'s own node leaves them optional
    # ("omission inherits the MediaBuy start"). Both are `format: date-time`, and
    # the purchase's `start_time` additionally carries `not: {const: "asap"}`, so
    # the envelope's "asap" is not a value a purchase may repeat.
    return {
        "brand": {"domain": "example.com"},
        "purchases": [
            {
                "product_id": "product-1",
                "pricing_option_id": "price-1",
                "pricing": {
                    "pricing_option_id": "price-1",
                    "pricing_model": "cpm",
                    "currency": "USD",
                },
                "start_time": "2026-06-01T00:00:00Z",
                "end_time": "2026-12-01T00:00:00Z",
            }
        ],
        "start_time": "asap",
        "end_time": "2026-12-01T00:00:00Z",
        "change_terms": list(change_terms),
    }


@pytest.mark.parametrize(
    ("action", "task"),
    [
        ("pause", ActionTask.control_media_buy),
        ("increase_budget", ActionTask.control_media_buy),
        ("remove_packages", ActionTask.control_media_buy),
        ("extend_flight", ActionTask.refine_proposals),
        ("add_packages", ActionTask.refine_proposals),
        ("replace_creative", ActionTask.sync_creatives),
        ("future_action", None),
    ],
)
def test_route_media_buy_action(action: str, task: ActionTask | None) -> None:
    assert route_media_buy_action(action) is task


def test_default_routes_track_released_canonical_action_schema() -> None:
    schema = json.loads(ACTION_SCHEMA.read_text())
    expected: dict[str, ActionTask] = {}
    for arm in schema["oneOf"]:
        properties = arm["properties"]
        task = ActionTask(properties["task"]["const"])
        for action in properties["action"]["enum"]:
            expected.setdefault(action, task)

    assert {action: route_media_buy_action(action) for action in expected} == expected


def test_assessment_joins_possible_promised_and_available() -> None:
    term = _term("pause", statuses=["active"])
    result = assess_media_buy_action(
        "pause",
        product=_product({"action": "pause", "modes": ["self_serve"]}),
        proposal=_proposal(term),
        media_buy=_buy(
            "active",
            _live("pause", task="control_media_buy"),
        ),
    )

    assert result.status is ActionAvailabilityStatus.available_now
    assert (result.possible, result.promised, result.available) == (
        ActionKnowledge.yes,
        ActionKnowledge.yes,
        ActionKnowledge.yes,
    )
    assert result.task is ActionTask.control_media_buy
    assert result.change_term_id == "right_pause"


def test_cross_sdk_action_assessment_golden_fixture() -> None:
    fixture = json.loads(GOLDEN_FIXTURE.read_text())

    assert fixture["schema_version"] == 1
    for case in fixture["cases"]:
        result = assess_media_buy_action(
            case["action"],
            product=case["product"],
            proposal=case["proposal"],
            media_buy=case["media_buy"],
        )
        normalized = result.model_dump(
            mode="json",
            include={
                "status",
                "possible",
                "promised",
                "available",
                "task",
                "mode",
                "change_term_id",
            },
        )
        assert normalized == case["expected"], case["name"]


def test_product_can_narrow_an_accepted_live_right() -> None:
    result = assess_media_buy_action(
        "pause",
        product=_product({"action": "resume", "modes": ["self_serve"]}),
        proposal=_proposal(_term("pause")),
        media_buy=_buy("active", _live("pause")),
    )

    assert result.status is ActionAvailabilityStatus.unsupported_by_product
    assert result.possible is ActionKnowledge.no


def test_absent_change_terms_is_legacy_unknown_even_with_flat_valid_action() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(present=False),
        media_buy={"status": "active", "valid_actions": ["pause"]},
    )

    assert result.status is ActionAvailabilityStatus.legacy_unknown
    assert result.promised is ActionKnowledge.unknown
    assert {item.code for item in result.diagnostics} >= {
        ActionDiagnosticCode.legacy_terms_unknown,
        ActionDiagnosticCode.legacy_coarse_action,
    }


def test_explicit_change_terms_omission_is_not_negotiated() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(_term("resume")),
        media_buy=_buy("active", _live("pause")),
    )

    assert result.status is ActionAvailabilityStatus.not_negotiated
    assert result.promised is ActionKnowledge.no


def test_wrong_status_is_distinct_from_current_unavailability() -> None:
    result = assess_media_buy_action(
        "increase_budget",
        proposal=_proposal(_term("increase_budget", statuses=["active"])),
        media_buy=_buy("paused"),
    )

    assert result.status is ActionAvailabilityStatus.wrong_status
    assert result.promised is ActionKnowledge.yes
    assert result.available is ActionKnowledge.no


def test_negotiated_but_omitted_live_action_is_currently_unavailable() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(_term("pause", statuses=["active"])),
        media_buy=_buy("active"),
    )

    assert result.status is ActionAvailabilityStatus.currently_unavailable


def test_mismatched_dual_aliases_fail_closed() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(_term("pause", term_id="right_pause")),
        media_buy=_buy(
            "active",
            _live("pause", term_id="right_pause", terms_ref="different"),
        ),
    )

    assert result.status is ActionAvailabilityStatus.currently_unavailable
    assert ActionDiagnosticCode.alias_mismatch in {item.code for item in result.diagnostics}


def test_protocol_allowed_refinement_route_is_accepted_for_overlapping_action() -> None:
    result = assess_media_buy_action(
        "increase_budget",
        proposal=_proposal(_term("increase_budget")),
        media_buy=_buy(
            "active",
            _live("increase_budget", task="refine_proposals"),
        ),
    )

    assert result.status is ActionAvailabilityStatus.available_now
    assert result.task is ActionTask.refine_proposals


def test_unknown_live_route_fails_closed() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(_term("pause")),
        media_buy=_buy("active", _live("pause", task="delete_everything")),
    )

    assert result.status is ActionAvailabilityStatus.currently_unavailable
    assert result.task is None
    assert ActionDiagnosticCode.route_mismatch in {item.code for item in result.diagnostics}


def test_seller_managed_action_on_wrong_task_fails_closed() -> None:
    result = assess_media_buy_action(
        "extend_flight",
        proposal=_proposal(_term("extend_flight", mode="seller_managed")),
        media_buy=_buy(
            "active",
            _live(
                "extend_flight",
                mode="seller_managed",
                task="control_media_buy",
            ),
        ),
    )

    assert result.status is ActionAvailabilityStatus.currently_unavailable
    assert ActionDiagnosticCode.route_mismatch in {item.code for item in result.diagnostics}


def test_legacy_terms_ref_is_not_promoted_without_accepted_terms() -> None:
    result = assess_media_buy_action(
        "pause",
        proposal=_proposal(present=False),
        media_buy={
            "status": "active",
            "available_actions": [
                {"action": "pause", "mode": "self_serve", "terms_ref": "right_pause"}
            ],
        },
    )

    assert result.status is ActionAvailabilityStatus.legacy_unknown
    assert result.change_term_id is None


def test_unknown_future_action_round_trips_without_becoming_available() -> None:
    result = assess_media_buy_action(
        "future_action_v4",
        proposal=_proposal(_term("future_action_v4")),
        media_buy=_buy("active", _live("future_action_v4")),
    )

    assert result.action == "future_action_v4"
    assert result.status is ActionAvailabilityStatus.currently_unavailable
    assert result.available is ActionKnowledge.unknown
    assert ActionDiagnosticCode.unknown_action in {item.code for item in result.diagnostics}


def test_untrusted_unknown_action_is_not_echoed_in_diagnostic_detail() -> None:
    action = "future\nsecret"
    result = project_available_actions(
        [{"term_id": "right", "action": action, "service_mode": "self_serve"}],
        "active",
    )

    assert result.actions == ()
    assert result.diagnostics[0].detail is None


def test_seller_projection_rejects_schema_invalid_term() -> None:
    result = project_available_actions(
        [{"term_id": "right", "action": "pause", "service_mode": "future_mode"}],
        "active",
    )

    assert result.actions == ()
    assert result.diagnostics[0].code is ActionDiagnosticCode.invalid_projection


def test_materialize_change_terms_requires_explicit_selection_and_copies_bounds() -> None:
    terms = materialize_change_terms(
        [
            {
                "action": "increase_budget",
                "modes": ["self_serve", "seller_managed"],
                "allowed_statuses": ["active", "paused"],
                "sla": {"response_max": "PT30M"},
                "constraints": {"kind": "budget", "max_delta_percent": 20},
                "terms_ref": "https://seller.example/terms/budget",
            },
            {"action": "pause", "modes": ["self_serve"]},
        ],
        [
            ChangeTermSelection(
                action="increase_budget",
                term_id="right_increase",
                service_mode="seller_managed",
                allowed_statuses=("active",),
                conditions=("account_in_good_standing",),
            )
        ],
    )

    assert len(terms) == 1
    assert terms[0].model_dump(mode="json", exclude_none=True) == {
        "term_id": "right_increase",
        "action": "increase_budget",
        "service_mode": "seller_managed",
        "allowed_statuses": ["active"],
        "processing_sla": {"response_max": "PT30M"},
        "conditions": ["account_in_good_standing"],
        "constraints": {"kind": "budget", "max_delta_percent": 20.0},
        "terms_ref": "https://seller.example/terms/budget",
    }


def test_materialize_requires_mode_when_product_has_multiple() -> None:
    with pytest.raises(MediaBuyActionError, match="service_mode_required"):
        materialize_change_terms(
            [{"action": "increase_budget", "modes": ["self_serve", "seller_managed"]}],
            [{"action": "increase_budget", "term_id": "right_increase"}],
        )


def test_materialize_cannot_expand_status_scope_or_constraint_kind() -> None:
    with pytest.raises(MediaBuyActionError, match="status_scope_expanded"):
        materialize_change_terms(
            [
                {
                    "action": "pause",
                    "modes": ["self_serve"],
                    "allowed_statuses": ["active"],
                }
            ],
            [
                {
                    "action": "pause",
                    "term_id": "right_pause",
                    "allowed_statuses": ["active", "paused"],
                }
            ],
        )


@pytest.mark.parametrize(
    ("constraint_type", "kind", "bounds"),
    [
        (
            "BudgetChangeConstraints",
            "budget",
            ("max_delta_amount", "max_delta_percent", "min_result_amount", "max_result_amount"),
        ),
        (
            "FlightChangeConstraints",
            "flight",
            ("max_change", "earliest_result", "latest_result", "minimum_notice"),
        ),
        (
            "PackageCountChangeConstraints",
            "package_count",
            ("max_additions", "max_removals", "max_result_count"),
        ),
        (
            "EffectiveTimingChangeConstraints",
            "effective_timing",
            ("minimum_notice", "earliest_effective_at", "latest_effective_at"),
        ),
    ],
)
def test_generated_constraint_models_require_a_portable_bound(
    constraint_type: str, kind: str, bounds: tuple[str, ...]
) -> None:
    """Each arm of ``media-buy/change-term-constraints.json`` states TWO facts.

    ``required: ['kind']`` and an ``anyOf`` over one-key ``required`` groups — the
    portable bounds. An empty payload breaks both, and the document's own first
    answer is the missing ``kind``: the ``anyOf`` rule is an after-validator and
    cannot run on a payload the field layer already refused. So the two are asked
    separately, each by its own error TYPE and location rather than by a message.
    """
    from adcp import types

    model = getattr(types, constraint_type)

    with pytest.raises(ValidationError) as missing_kind:
        model.model_validate({})
    assert [(e["type"], e["loc"]) for e in missing_kind.value.errors()] == [("missing", ("kind",))]

    with pytest.raises(ValidationError) as missing_bound:
        model.model_validate({"kind": kind})
    errors = missing_bound.value.errors()
    assert [(e["type"], e["loc"]) for e in errors] == [("anyOf", ())]
    for bound in bounds:
        assert bound in errors[0]["msg"]


def test_generated_canonical_action_requires_action_field() -> None:
    from adcp.types import CanonicalMediaBuyAction

    with pytest.raises(ValidationError):
        TypeAdapter(CanonicalMediaBuyAction).validate_python(
            {"task": "control_media_buy", "mode": "self_serve"}
        )


def test_generated_change_term_admits_an_incompatible_constraint_kind() -> None:
    """``constraint_action_compatibility`` is `x-adcp-validation`, so the model admits it.

    ``media-buy/change-term.json`` states the kind/action table under
    ``x-adcp-validation.verifier_constraints`` — an extension keyword, not a JSON
    Schema one. §6 of ``docs/plan/rebuild-plan.md`` takes the decision by name:
    *"`x-adcp-validation` constrains in intent and not in the document, so a model
    enforcing it would be narrower than its document"* (upstream
    ``adcontextprotocol/adcp#8472``). A generated class refusing `kind: budget` on
    `action: pause` would be that narrowing.

    The enforcement is the SDK layer's, where the verifier lives, and the
    document's own ``on_violation: reject_proposal`` is what it answers to.
    """
    from adcp.types import MediaBuyChangeTerm

    term = MediaBuyChangeTerm.model_validate(
        {
            "term_id": "right_pause",
            "action": "pause",
            "service_mode": "self_serve",
            "constraints": {"kind": "budget", "max_delta_percent": 10},
        }
    )
    assert term.constraints.kind == "budget"

    # The verifier's answer to the same pair, at the layer that holds it.
    assert (
        evaluate_action_constraints(
            "pause", {"kind": "budget", "max_delta_percent": 10}, ActionIntent()
        )[0].outcome
        is ConstraintOutcome.unknown
    )

    with pytest.raises(MediaBuyActionError, match="constraint_action_mismatch"):
        materialize_change_terms(
            [
                {
                    "action": "pause",
                    "modes": ["self_serve"],
                    "constraints": {"kind": "budget", "max_delta_percent": 5},
                }
            ],
            [{"action": "pause", "term_id": "right_pause"}],
        )


def test_generated_commercial_terms_admit_duplicate_rights_and_a_foreign_currency() -> None:
    """Both of these are `x-adcp-validation` and prose, and neither is a keyword.

    ``media-buy/commercial-terms.json`` says *"Entries are uniquely keyed by
    action"* in ``change_terms``'s ``description``, and states
    ``constraint_currency`` — *"Every monetary constraint currency equals the
    commercial terms purchase currency"* — under ``x-adcp-validation``. §6's
    decision on ``x-adcp-validation`` covers the second and a ``description``
    constrains nothing at all, so the generated class admits both payloads. The
    refusals live where the verifier does: ``materialize_change_terms`` for the
    duplicate action, ``evaluate_action_constraints`` for the currency.
    """
    from adcp.types import CommercialTerms

    duplicated = CommercialTerms.model_validate(
        _commercial_terms(
            _term("pause", term_id="right-a"),
            _term("pause", term_id="right-b"),
        )
    )
    assert [term.term_id for term in duplicated.change_terms] == ["right-a", "right-b"]
    assert {term.action for term in duplicated.change_terms} == {"pause"}

    with pytest.raises(MediaBuyActionError, match="duplicate_action"):
        materialize_change_terms(
            [{"action": "pause", "modes": ["self_serve"]}],
            [
                {"action": "pause", "term_id": "right-a"},
                {"action": "pause", "term_id": "right-b"},
            ],
        )

    foreign = CommercialTerms.model_validate(
        _commercial_terms(
            _term(
                "increase_budget",
                constraints={
                    "kind": "budget",
                    "max_delta_amount": {"amount": 100, "currency": "EUR"},
                },
            )
        )
    )
    assert foreign.purchases[0].pricing.currency == "USD"
    assert foreign.change_terms[0].constraints.max_delta_amount.currency == "EUR"

    violated = evaluate_action_constraints(
        "increase_budget",
        {"kind": "budget", "max_delta_amount": {"amount": 100, "currency": "EUR"}},
        ActionIntent(current_amount=1000, result_amount=1050, currency="USD"),
    )
    assert [check.outcome for check in violated] == [ConstraintOutcome.violated]
    # Same bound in the purchases' own currency: satisfied, so the verdict above is
    # the currency's and not the amount's.
    assert [
        check.outcome
        for check in evaluate_action_constraints(
            "increase_budget",
            {"kind": "budget", "max_delta_amount": {"amount": 100, "currency": "USD"}},
            ActionIntent(current_amount=1000, result_amount=1050, currency="USD"),
        )
    ] == [ConstraintOutcome.satisfied]

    with pytest.raises(MediaBuyActionError, match="constraint_action_mismatch"):
        materialize_change_terms(
            [
                {
                    "action": "pause",
                    "modes": ["self_serve"],
                    "constraints": {"kind": "budget", "max_delta_percent": 5},
                }
            ],
            [{"action": "pause", "term_id": "right_pause"}],
        )


def _scenario_terms() -> list[dict[str, Any]]:
    return [
        _term("pause", term_id="right_pause_active", statuses=["active"]),
        _term("resume", term_id="right_resume_paused", statuses=["paused"]),
        _term(
            "increase_budget",
            term_id="right_increase_active",
            mode="seller_managed",
            statuses=["active"],
            constraints={"kind": "budget", "max_delta_percent": 20},
            conditions=["account_in_good_standing"],
            sla={"response_max": "PT30M", "completion_max": "PT24H"},
        ),
        _term(
            "decrease_budget",
            term_id="right_decrease_paused",
            statuses=["paused"],
            constraints={"kind": "budget", "max_delta_percent": 50},
        ),
        _term("extend_flight", term_id="right_extend_active", statuses=["active"]),
    ]


def test_seller_projection_matches_released_active_storyboard() -> None:
    result = project_available_actions(_scenario_terms(), "active")

    assert result.to_wire() == [
        {
            "action": "pause",
            "mode": "self_serve",
            "task": "control_media_buy",
            "change_term_id": "right_pause_active",
        },
        {
            "action": "extend_flight",
            "mode": "self_serve",
            "task": "refine_proposals",
            "change_term_id": "right_extend_active",
        },
    ]
    assert ActionDiagnosticCode.condition_unresolved in {item.code for item in result.diagnostics}


def test_seller_projection_matches_released_paused_storyboard() -> None:
    result = project_available_actions(_scenario_terms(), "paused")

    assert result.to_wire() == [
        {
            "action": "resume",
            "mode": "self_serve",
            "task": "control_media_buy",
            "change_term_id": "right_resume_paused",
        },
        {
            "action": "decrease_budget",
            "mode": "self_serve",
            "task": "control_media_buy",
            "change_term_id": "right_decrease_paused",
        },
    ]


def test_projection_gates_authorization_delegation_policy_and_product() -> None:
    terms = [_term("pause"), _term("resume", statuses=["paused"])]

    assert (
        project_available_actions(
            terms,
            "active",
            authorized_actions=[],
        ).actions
        == ()
    )
    assert (
        project_available_actions(
            terms,
            "active",
            delegated_actions=["resume"],
        ).actions
        == ()
    )
    assert (
        project_available_actions(
            terms,
            "active",
            policy_actions=["resume"],
        ).actions
        == ()
    )
    assert (
        project_available_actions(
            terms,
            "active",
            product_actions=[{"action": "resume", "modes": ["self_serve"]}],
        ).actions
        == ()
    )


@pytest.mark.parametrize("status", ["completed", "rejected", "canceled", "future_status"])
def test_terminal_or_unknown_status_projects_no_actions(status: str) -> None:
    assert project_available_actions([_term("cancel")], status).actions == ()


def test_resolved_condition_allows_seller_managed_standard_async_action() -> None:
    result = project_available_actions(
        _scenario_terms(),
        "active",
        resolved_conditions={"account_in_good_standing": True},
    )
    increase = next(action for action in result.actions if action.action == "increase_budget")
    assert increase.mode == "seller_managed"
    assert increase.task is ActionTask.control_media_buy


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        (
            "3.1.19",
            {
                "action": "increase_budget",
                "mode": "requires_approval",
                "sla": {"response_max": "PT30M"},
                "terms_ref": "right_increase",
            },
        ),
        (
            "3.2.0-beta.6",
            {
                "action": "increase_budget",
                "mode": "requires_approval",
                "task": "control_media_buy",
                "sla": {"response_max": "PT30M"},
                "terms_ref": "right_increase",
            },
        ),
        (
            "3.2.0-rc.1",
            {
                "action": "increase_budget",
                "mode": "seller_managed",
                "task": "control_media_buy",
                "sla": {"response_max": "PT30M"},
                "change_term_id": "right_increase",
            },
        ),
    ],
)
def test_projection_version_matrix(version: str, expected: dict[str, Any]) -> None:
    result = project_available_actions(
        [
            _term(
                "increase_budget",
                term_id="right_increase",
                mode="seller_managed",
                sla={"response_max": "PT30M"},
            )
        ],
        "active",
        protocol_version=version,
    )
    wire = result.to_wire()[0]
    assert wire == expected

    schema_version = "3.1" if version == "3.1.19" else version
    validator = get_named_validator("core/media-buy-available-action.json", version=schema_version)
    assert validator is not None
    assert list(validator.iter_errors(wire)) == []


@pytest.mark.parametrize(
    ("constraint", "intent", "outcomes"),
    [
        (
            {
                "kind": "budget",
                "max_delta_amount": {"amount": 200, "currency": "USD"},
                "max_delta_percent": 20,
                "min_result_amount": {"amount": 500, "currency": "USD"},
                "max_result_amount": {"amount": 1200, "currency": "USD"},
            },
            ActionIntent(current_amount=1000, result_amount=1100, currency="USD"),
            [ConstraintOutcome.satisfied] * 4,
        ),
        (
            {"kind": "flight", "max_change": {"interval": 7, "unit": "days"}},
            ActionIntent(
                current_time="2026-09-01T00:00:00Z",
                result_time="2026-09-05T00:00:00Z",
            ),
            [ConstraintOutcome.satisfied],
        ),
        (
            {"kind": "package_count", "max_additions": 2, "max_result_count": 5},
            ActionIntent(additions=3, current_package_count=3, result_package_count=6),
            [ConstraintOutcome.violated, ConstraintOutcome.violated],
        ),
        (
            {
                "kind": "effective_timing",
                "minimum_notice": {"interval": 2, "unit": "days"},
            },
            ActionIntent(effective_at="2026-08-29T12:00:00Z"),
            [ConstraintOutcome.violated],
        ),
    ],
)
def test_portable_constraint_evaluation(
    constraint: dict[str, Any],
    intent: ActionIntent,
    outcomes: list[ConstraintOutcome],
) -> None:
    action = {
        "budget": "increase_budget",
        "flight": "extend_flight",
        "package_count": "add_packages",
        "effective_timing": "pause",
    }[constraint["kind"]]

    result = evaluate_action_constraints(action, constraint, intent, now=NOW)
    assert [check.outcome for check in result] == outcomes


def test_opaque_or_insufficient_constraints_remain_unknown() -> None:
    result = evaluate_action_constraints(
        "pause",
        {"kind": "budget", "max_delta_percent": 10},
        ActionIntent(),
    )
    assert result[0].outcome is ConstraintOutcome.unknown


def test_update_patch_preflights_binding_budget_constraint() -> None:
    proposal = _proposal(
        _term(
            "decrease_budget",
            constraints={"kind": "budget", "max_delta_percent": 50},
        )
    )
    current = {
        "status": "paused",
        "currency": "USD",
        "total_budget": 1000,
        "packages": [],
        "available_actions": [_live("decrease_budget", task="control_media_buy")],
    }
    result = assess_update_media_buy_actions(
        {"total_budget": {"amount": 100, "currency": "USD"}},
        current,
        proposal=proposal,
        now=NOW,
    )

    assert result[0].status is ActionAvailabilityStatus.currently_unavailable
    assert result[0].constraints[0].outcome is ConstraintOutcome.violated


def test_action_not_allowed_echo_reassesses_stale_projection() -> None:
    proposal = _proposal(_term("pause"), _term("resume"))
    stale = _buy("active", _live("pause", task="control_media_buy"))

    refreshed = reassess_media_buy_action(
        "pause",
        currently_available_actions=[_live("resume", task="control_media_buy")],
        media_buy=stale,
        proposal=proposal,
    )

    assert refreshed.status is ActionAvailabilityStatus.currently_unavailable
    assert refreshed.available is ActionKnowledge.no


def test_mixed_patch_keeps_available_and_blocked_actions_distinct() -> None:
    proposal = _proposal(
        _term("pause", statuses=["active"]),
        _term("decrease_budget", statuses=["active"]),
    )
    current = {
        "status": "active",
        "total_budget": {"amount": 1000, "currency": "USD"},
        "packages": [],
        "available_actions": [_live("pause", task="control_media_buy")],
    }

    results = assess_update_media_buy_actions(
        {
            "paused": True,
            "total_budget": {"amount": 900, "currency": "USD"},
        },
        current,
        proposal=proposal,
    )

    assert [(result.action, result.status) for result in results] == [
        ("pause", ActionAvailabilityStatus.available_now),
        ("decrease_budget", ActionAvailabilityStatus.currently_unavailable),
    ]


class _Request(BaseModel):
    value: str


class _Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, BaseModel, Any]] = []

    async def execute_task(
        self,
        task_name: str,
        request: BaseModel,
        *,
        options: Any | None = None,
    ) -> str:
        self.calls.append((task_name, request, options))
        return "ok"


@pytest.mark.asyncio
async def test_dispatch_uses_assessed_route_and_standard_async_lifecycle() -> None:
    assessment = assess_media_buy_action(
        "increase_budget",
        proposal=_proposal(_term("increase_budget", mode="seller_managed")),
        media_buy=_buy(
            "active",
            _live(
                "increase_budget",
                mode="seller_managed",
                task="control_media_buy",
            ),
        ),
    )
    client = _Client()
    request = _Request(value="x")

    assert assessment.async_processing is True
    assert await dispatch_media_buy_action(client, assessment, request) == "ok"
    assert client.calls == [("control_media_buy", request, None)]


@pytest.mark.asyncio
async def test_dispatch_refuses_unavailable_action() -> None:
    assessment = assess_media_buy_action(
        "pause",
        proposal=_proposal(_term("pause")),
        media_buy=_buy("active"),
    )
    with pytest.raises(MediaBuyActionError, match="action_not_available"):
        await dispatch_media_buy_action(_Client(), assessment, _Request(value="x"))
