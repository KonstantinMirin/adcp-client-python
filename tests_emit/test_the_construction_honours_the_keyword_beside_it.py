"""The least instance fills a required member with a value its SIBLING keywords admit.

**THE DEFECT WAS FIVE OF THE SEVEN ``fail:unproved_widening`` ROWS, and it was the
CONSTRUCTOR rather than the walk** (``adcp-client-python-09ti``, measured by the memo lane
at trunk ``3fc9d3060``). :func:`codegen.verify.witness.least_instance` read a member's own
keyword and stopped, so it offered a value a keyword BESIDE it refuses -- and the screen
after the build then reported the obligation unproved, blaming the declaration for a value
the instrument could not build.

Two shapes, and each is a value CHOICE inside the existing construction rather than new
keyword support:

1. **an ``enum`` conjoined with a ``not`` over values.**
   ``core/agent-notification-config.json`` requires ``event_types``, whose ``items`` is
   ``allOf: [{$ref enums/notification-type.json}, {not: {enum: ["scheduled", "final",
   "delayed", "adjusted", "window_update", "impairment"]}}]``. The enum has 26 members, the
   ``not`` forbids 6, and **the first member of the enum is the first value the ``not``
   forbids** -- so ``["scheduled"]`` went out while 20 admitted members went unoffered, and
   the screen reported ``broke ['not']``. Three of the seven rows were that one site reached
   from three pairs.
2. **a ``contains`` the construction is filling an array for.**
   ``protocol/get-adcp-capabilities-response.json``'s ``media_buy`` conjunct states ``{if:
   {required: [proposal_refinement]}, then: {properties: {lifecycle_tools: {contains:
   {const: "refine_proposals"}}}, required: [lifecycle_tools]}}``. With the declaration
   demanding ``proposal_refinement`` the ``if`` fires and the ``then`` is folded in, and the
   builder still filled ``lifecycle_tools`` from the item enum's first member --
   ``["list_products"]``, which the folded ``contains`` refuses. Two rows.

**WHAT IS ASSERTED HERE IS THE VALUE, NOT THE ROW COUNT.** A count moves with the bundle,
the emitter and the constructor; what must not move is that a required member is filled
with something the whole conjunction admits. Each case below builds through the real
:func:`least_instance` and screens the answer against the node with ``jsonschema`` -- the
same screen ``harness._Draws._draw`` applies -- so the test fails if the construction ever
goes back to offering a refused value.

**AND THE DIRECTION IS PINNED BESIDE IT, because the cheap way to clear a red row is to
stop reporting** (``tests_emit/test_the_widening_column_errs_absent.py``, the guard this
file's work sits under). Where the conjunction admits NOTHING, the construction must
decline with a reason and never answer with a value one of its statements refuses: the two
synthetic nodes below are contradictions, and what they must produce is a refusal.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import jsonschema
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def records() -> Any:
    """The documents of record, read the way the grade reads them."""
    from codegen import bundle, patch

    bundle_dir = patch.for_build(ROOT / "schemas" / "cache" / "3.2")
    known = set(bundle.portable(bundle_dir))
    return lambda document: bundle.record(bundle_dir, document, known)


def _admits(node: Any, value: Any) -> bool:
    """Does ``node`` admit ``value``?  The screen the draw applies, asked here."""
    return jsonschema.Draft7Validator(node).is_valid(value)


def test_a_member_a_conjoined_not_forbids_is_not_offered(records: Any) -> None:
    """``event_types/items``: a member of the enum that the sibling ``not`` admits.

    The site is the measured one and the assertion is the DOCUMENT's: the value is offered
    to the node's own validator, so this holds for whichever member the construction picks
    as long as every statement admits it.
    """
    from codegen.verify.witness import least_instance

    record = records("core/agent-notification-config.json")
    node = record["properties"]["event_types"]["items"]
    built = least_instance([node])
    assert built.held, f"no member was offered at all: {built.reason}"
    assert _admits(node, built.value), (
        f"the construction offered {built.value!r}, which this node refuses -- "
        f"the enum and the not beside it are one statement about one value"
    )


def test_the_whole_notification_config_builds_an_instance_its_document_admits(
    records: Any,
) -> None:
    """The member choice reaches the pair: the document's own least instance is valid.

    The three ``fail:unproved_widening`` rows of this shape were at
    ``protocol/sync-agent-notification-configs-request.json#`` and
    ``protocol/sync-principal-request.json`` (twice), each reaching this one site through
    ``notification_configs/items``. Asserting the document here rather than those three
    pairs keeps the test about the CONSTRUCTION, which is where the repair is.
    """
    from codegen.verify.witness import least_instance

    record = records("core/agent-notification-config.json")
    built = least_instance([record])
    assert built.held, f"the document's least instance was not built: {built.reason}"
    assert _admits(
        record, built.value
    ), f"the document refuses its own least instance: {json.dumps(built.value)[:300]}"


def test_an_array_a_contains_demands_of_holds_the_element_it_demands(records: Any) -> None:
    """``media_buy`` + the presence demand: ``lifecycle_tools`` holds ``refine_proposals``.

    The presence demand is what ``check_widening`` conjoins to reach the declaration at
    ``#/properties/media_buy/properties/proposal_refinement``, and it is what fires the
    ``if``; without it the conditional states nothing and there is no ``contains`` in force.
    """
    from codegen.verify.witness import least_instance

    record = records("protocol/get-adcp-capabilities-response.json")
    node = record["properties"]["media_buy"]
    demand = {"required": ["proposal_refinement"]}
    built = least_instance([node, demand])
    assert built.held, f"no instance was offered at all: {built.reason}"
    assert _admits({"allOf": [node, demand]}, built.value), (
        f"the construction offered {json.dumps(built.value)[:300]}, which the node refuses "
        f"-- the then's contains is a statement about the array the required member is"
    )


@pytest.mark.parametrize(
    "node,why",
    [
        (
            {"allOf": [{"enum": ["scheduled"]}, {"not": {"enum": ["scheduled"]}}]},
            "an enum whose only member a not forbids",
        ),
        (
            {
                "type": "array",
                "minItems": 1,
                "maxItems": 0,
                "contains": {"const": "x"},
            },
            "a contains whose element overruns maxItems",
        ),
    ],
)
def test_a_conjunction_that_admits_nothing_is_declined_and_not_answered(
    node: Any, why: str
) -> None:
    """A node admitting no value gets a REASON, never a value one statement refuses.

    This is the direction ``test_the_widening_column_errs_absent.py`` pins, asked of the
    two keywords this file repaired: honouring a sibling keyword must not become a licence
    to invent a value where honouring it is impossible. An obligation the construction
    cannot witness stays ABSENT, and absent is not a pass.
    """
    from codegen.verify.witness import least_instance

    built = least_instance([node])
    assert (
        not built.held
    ), f"{why}: the construction answered {built.value!r} for a node that admits nothing"
    assert built.reason, f"{why}: declined with no reason, so no reader can act on it"
