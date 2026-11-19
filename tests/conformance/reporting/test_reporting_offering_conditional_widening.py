"""A conditional requirement about a CHILD's keys, and the declaration that stands in
for the rule nothing can carry.

``core/reporting-delivery-offering.json#/allOf/1`` says: when ``reconciliation_mode`` is
``consumer_receipt``, ``method`` is required AND ``reporting_profile`` must carry the five
``canonicalization_*`` keys.  The class carries the first half as a
:class:`adcp.types._runtime.ConditionalRequired` and DROPS the second, because the second
is a requiredness about a child's keys and no rule kind in ``adcp.types._runtime`` reaches
one -- every one of them resolves a flat property NAME against the class's own supplied
key set (:func:`adcp.types._runtime.supplied`).

So ``ReportingDeliveryOffering`` is WIDER than its document there, and ``CLAUDE.md``'s
standing rule makes the missing DECLARATION the defect rather than the drop: the class
carries an :class:`adcp.types._base.Approximation` at that pointer, which is what this
file pins.  Three halves, each measured here, because a declaration nobody grades is a
comment:

* the DOCUMENT refuses the incomplete profile, at
  ``allOf/1/then/properties/reporting_profile/required``;
* the CLASS builds it anyway -- that is the widening, and a consumer who relies on the
  constructor alone ships a payload the standard refuses;
* the class DECLARES it, at ``#/allOf/1``, kind ``WIDENED``.

And the fourth, which is why the declaration is the honest treatment rather than a
shortcut: the one spelling :class:`~adcp.types._runtime.ConditionalRequired` would admit
for a nested path -- a dotted property name -- refuses a payload the document ACCEPTS,
because the dotted name is never a key the instance supplied.  A rule narrower than its
document is forbidden outright, so there is nothing to lower until the carrier exists.
That carrier is the named follow-up in ``FINDINGS-pointer.md`` §5
(``adcp-client-python-8cz3``); when it lands, the second and third assertions here invert
and the approximation goes away.

``tests/conformance/reporting/_production_support.py`` is the consumer of exactly this
fact: its fixture profile supplies both keys explicitly, and
``ReportingProductionOffering.__post_init__`` -- which screens the dump against the
document -- is what refuses when it does not.
"""

from __future__ import annotations

import pytest

from adcp.types import ReportingDeliveryOffering
from adcp.types._runtime import ConditionalRequired, Match, supplied
from adcp.validation.schema_loader import get_named_validator

#: The pointer the document states the conditional at, and the pointer the declaration
#: carries.  ONE constant: §8 sentence 2 gives an approximation one identity per
#: ``(document, pointer)``, so a declaration read at another pointer is another fact.
DOCUMENT = "core/reporting-delivery-offering.json"
POINTER = "#/allOf/1"

#: The two keys ``allOf/1/then`` requires on ``reporting_profile`` and the class does not.
#: Both are ``const`` on ``reporting_profile``'s own node, which is why the pinned default
#: looked like it would carry them and does not: that decision
#: (``verdicts/a-pinned-default-is-the-documents-own.md``) fires where a node states
#: ``required`` AND ``const`` at the SAME node, and ``reporting_profile``'s own
#: ``required`` lists neither -- the requiredness lives one ``allOf`` up, under a
#: condition.
CONDITIONALLY_REQUIRED = {
    "canonicalization_contract_version": "1.0",
    "canonicalization_media_type": "application/vnd.adcp.reporting-canonicalization+json",
}

_PROFILE = {
    "id": "reference-report-v1",
    "version": "1",
    "schema_uri": "https://seller.example.com/reporting/schema.json",
    "schema_sha256": "a" * 64,
    "schema_dialect": "https://json-schema.org/draft/2020-12/schema",
    "schema_ref_policy": "local_fragment_only",
    "grain": "row",
    "primary_keys": ["row_id"],
    "canonicalization_id": "jcs-v1",
    "canonicalization_uri": "https://seller.example.com/reporting/canonicalization.json",
    "canonicalization_sha256": "b" * 64,
}

#: An offering in the conditional's own region: ``reconciliation_mode`` is
#: ``consumer_receipt``, so ``allOf/1/then`` is in force.
_OFFERING = {
    "offering_id": "reconciled-fixture",
    "feed_purpose": "billing",
    "report_definition_id": "reference-report-v1",
    "report_definition_uri": "https://seller.example.com/reporting/definition.json",
    "report_definition_sha256": "c" * 64,
    "schedule": {"period_duration": "PT1H", "alignment": "utc", "delivery_sla": "PT1H"},
    "supported_finality": ["official"],
    "reconciliation_mode": "consumer_receipt",
    "method": {
        "pattern": "file_transfer",
        "transport": "sftp",
        "format": "csv",
        "orchestration": "producer_managed",
        "destination_modes": ["existing"],
        "provider": {"domain": "seller.example.com"},
    },
}


def _offering(profile: dict) -> dict:
    return {**_OFFERING, "reporting_profile": profile}


def _refusals(payload: dict) -> list[tuple[str, tuple]]:
    """What the DOCUMENT says about ``payload``, as (message, schema path) pairs."""
    validator = get_named_validator(DOCUMENT)
    assert validator is not None, f"no bundled validator for {DOCUMENT}"
    return [(e.message, tuple(e.absolute_schema_path)) for e in validator.iter_errors(payload)]


def test_the_document_requires_the_nested_keys_and_the_class_does_not() -> None:
    """The widening itself: the document refuses the profile, the constructor builds it."""
    incomplete = _offering(_PROFILE)

    #: The DOCUMENT refuses, and the path says the requiredness is the CHILD's -- which is
    #: the whole reason no rule kind carries it.
    where = _refusals(incomplete)
    assert sorted(message for message, _ in where) == [
        f"{name!r} is a required property" for name in sorted(CONDITIONALLY_REQUIRED)
    ], where
    assert {path for _, path in where} == {
        ("allOf", 1, "then", "properties", "reporting_profile", "required")
    }, where

    #: And the class builds it: the constructor is WIDER than the document here.  D4 keeps
    #: ``model_validate`` off the schema path, so this is the route an adopter takes.
    built = ReportingDeliveryOffering.model_validate(incomplete)
    assert built.reporting_profile.canonicalization_contract_version is None
    assert built.reporting_profile.canonicalization_media_type is None

    #: Supplying both keys is what the document asks for, and nothing else changes.
    assert _refusals(_offering({**_PROFILE, **CONDITIONALLY_REQUIRED})) == []


def test_the_dropped_nested_requiredness_is_declared_at_its_own_pointer() -> None:
    """The deliverable: the drop is declared, out loud, on the artifact a consumer gets.

    Read off the class and not off a compiler report, for the account row's reason in
    ``tests_emit/test_union_dispatch.py``: an approximation the BUILD does not apply is a
    lie, and the class is what ships.
    """
    declared = [
        one
        for one in ReportingDeliveryOffering.__adcp_approximations__
        if one.document == DOCUMENT and one.pointer == POINTER
    ]
    assert declared, (
        f"ReportingDeliveryOffering drops {sorted(CONDITIONALLY_REQUIRED)} at "
        f"{POINTER}/then/properties/reporting_profile/required and declares nothing: "
        f"{ReportingDeliveryOffering.__adcp_approximations__}"
    )
    assert [one.kind for one in declared] == ["WIDENED"], declared

    #: **THE KEYWORD IS ``if``, WHATEVER BRANCH THE DROPPED FACT SITS IN**
    #: (``codegen.lower.rules._conditional``, ``adcp-client-python-wvod``, ``-szfx``): a
    #: conditional is a triple whose members mean nothing apart, so one declaration per
    #: ``(document, pointer)`` records that the CONDITIONAL is approximated -- not one per
    #: arm.  ``harness.refused_witnesses`` attributes every witness it derives from an arm
    #: to the same keyword, which is what makes the two halves agree.
    assert [one.keyword for one in declared] == ["if"], declared


def test_no_rule_kind_carries_a_nested_requiredness() -> None:
    """Why it is declared and not lowered, measured rather than asserted.

    Every rule kind resolves a flat property NAME against the class's own supplied key
    set, so the only spelling available for a child's key is a name no instance can
    supply -- and a rule on it refuses the payload the document ACCEPTS.  That is a model
    narrower than its document, which is forbidden outright, so the declaration is the
    only honest treatment until the carrier in ``FINDINGS-pointer.md`` §5 exists.
    """
    conformant = ReportingDeliveryOffering.model_validate(
        _offering({**_PROFILE, **CONDITIONALLY_REQUIRED})
    )
    keys, values = supplied(conformant)

    #: The keys a rule sees at this class are the class's OWN, and a child's key is not
    #: among them under any spelling.
    assert "reporting_profile" in keys
    for name in CONDITIONALLY_REQUIRED:
        assert name not in keys
        assert f"reporting_profile.{name}" not in keys

    #: So the dotted spelling fires on a payload the document accepts.  Asserted on the
    #: CONFORMANT payload on purpose: a rule that refuses here is not a weaker carrier,
    #: it is a wrong one.
    dotted = ConditionalRequired(
        (Match("reconciliation_mode", True, ("consumer_receipt",)),),
        require=tuple(f"reporting_profile.{name}" for name in sorted(CONDITIONALLY_REQUIRED)),
    )
    assert _refusals(conformant.model_dump(mode="json", exclude_none=True)) == []
    assert [error[1] for error in dotted.errors(keys, values)] == [
        (f"reporting_profile.{name}",) for name in sorted(CONDITIONALLY_REQUIRED)
    ]


@pytest.mark.parametrize("name", sorted(CONDITIONALLY_REQUIRED))
def test_the_class_states_the_properties_it_does_not_require(name: str) -> None:
    """``deprecated``'s sibling reading: the fields are STATED, just not required.

    The drop is the REQUIREDNESS and nothing else -- both properties are declared on
    ``reporting_profile``, pinned to the document's own ``const``, and optional.  A class
    that suppressed them would be NARROWER than its document, which is the opposite
    defect.
    """
    field = type(ReportingDeliveryOffering.model_validate(_offering(_PROFILE)).reporting_profile)
    assert name in field.model_fields
    assert not field.model_fields[name].is_required()
