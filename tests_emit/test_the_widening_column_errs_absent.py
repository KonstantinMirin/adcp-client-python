"""An obligation the instrument cannot discharge is REPORTED, never passed.

``./verify``'s widening column is §8's accepts obligation, one declaration at a time, and
its whole value is that **absent is not a pass**: a declaration the check could not put a
value to reads ``unproved`` or ``absent`` and the pair goes red. A fix that makes an
unprovable obligation look discharged is worse than the red rows it removes, because the
red rows are visible and a laundered pass is not -- which is the defect class
``adcp-client-python-ahbe`` was filed for, read on the other instrument.

This file pins the DIRECTION the column errs in, so that a later repair of
``adcp-client-python-09ti``'s rows has to earn its passes. It asserts nothing about HOW
MANY rows are red: the count is a measurement and moves with the bundle, the emitter and
the constructor. What may not move is which way the instrument fails when it cannot answer.

**WHAT IS MEASURED HERE, 2026-11-20 at 3fc9d3060.** The widening column reads
``178/7/2384`` and the seven ``fail:unproved_widening`` rows are not the split
``adcp-client-python-09ti`` was filed with. That row's cause (A) -- four pairs at a pointer
``harness._steps`` could not walk -- is CLOSED: ``account/sync-accounts-response.json#/oneOf/0``,
``media-buy/create-media-buy-response.json#/oneOf/0``,
``media-buy/request-proposals-response.json#/anyOf/1`` and
``media-buy/sync-catalogs-response.json#/oneOf/1`` all read ``widening=pass``, which
:func:`test_the_four_pointers_a_leading_hop_reaches_are_still_reached` holds. Five of the
seven that remain share ONE cause, and it is the CONSTRUCTOR and not the walk: the least
instance fills a required member with a value a keyword beside it refuses -- ``['not']`` at
``core/agent-notification-config.json``'s ``event_types`` (the constructor offers
``["scheduled"]``, the first member of ``enums/notification-type.json``, which is the first
of the six values the sibling ``{"not": {"enum": [...]}}`` forbids, leaving 20 admitted
members unoffered) and ``['contains']`` at
``protocol/get-adcp-capabilities-response.json``'s ``lifecycle_tools``. The repair is in
``codegen/verify/witness.py``'s construction, which this lane does not own; the two
remaining rows are a ``required`` declaration whose note reports a ``url_parsing``
narrowing and are a different subject again.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen import harness

#: The committed verdict table's own report, which is what a reader quotes.
_ARTIFACT = Path(__file__).resolve().parents[1] / "src/adcp/types/verify.json"

#: The four pointers ``harness._steps``' leading-``allOf``-on-``stated`` reading exists
#: for, named in that function's own docstring and measured there as "4 of [459] walk to a
#: different node with this reading and every other one walks to the same node".
#:
#: They are ``adcp-client-python-09ti``'s cause (A), and they pass now. Held here because a
#: reading that silently stopped reaching them would put the obligation back to "the
#: document states no such keyword" -- a REPORT, so the column would stay honest and the
#: proof would quietly vanish. That is the regression this names.
A9_POINTERS: tuple[tuple[str, str], ...] = (
    ("account/sync-accounts-response.json", "#/oneOf/0"),
    ("media-buy/create-media-buy-response.json", "#/oneOf/0"),
    ("media-buy/request-proposals-response.json", "#/anyOf/1"),
    ("media-buy/sync-catalogs-response.json", "#/oneOf/1"),
)


def _report() -> dict:
    return json.loads(_ARTIFACT.read_text())


def _rows() -> list[dict]:
    return _report().get("not_pass_rows") or []


def test_the_widening_column_never_passes_what_it_could_not_put_a_value_to() -> None:
    """Every widening row that is not a pass says so in its own cell.

    The assertion is on the VOCABULARY of the column, not on its counts: a cell is
    ``pass``, or it names a failure or an absence. A cell that read ``pass`` while its note
    says a value could not be drawn or placed would be the laundered pass this file exists
    to forbid, and it is the one shape no count would show.
    """
    for row in _rows():
        cell = str(row.get("widening") or "")
        note = str(row.get("note") or "")
        if "pass" not in cell:
            continue
        for phrase in (
            "could not be drawn",
            "makes a payload the document refuses",
            "the document states no such keyword",
            "describes no instance location",
            "no value class is derivable",
        ):
            assert phrase not in note, (
                f"{row.get('document')}{row.get('pointer')} reads widening={cell!r} and its "
                f"note says {phrase!r}. An obligation the check could not put a value to "
                "is reported, never passed: absent is not a pass, and a pass here is a "
                "declaration nothing demonstrates."
            )


def test_an_unconstructible_node_is_reported_with_its_reason() -> None:
    """``_Draws._draw`` answers a node it cannot build for with ``[None, why]``.

    This is the erring direction at the one function that decides it. The screen after the
    construction is what makes the draw a CHECK rather than a claim -- a value the node
    refuses is not an answer -- and the reason names the keywords that refused it, which is
    how the five rows sharing a constructor cause are readable at all.

    Perturbed by hand rather than asserted from a count: a node whose ``enum`` is exactly
    what the sibling ``not`` forbids is unsatisfiable, and the answer must be a reason and
    not a value.
    """
    draws = harness._Draws(
        least=__import__("codegen.verify.witness", fromlist=["x"]).least_instance
    )
    unsatisfiable = {"allOf": [{"enum": ["scheduled"]}, {"not": {"enum": ["scheduled"]}}]}
    held = draws._draw(unsatisfiable, {})

    assert held[0] is None, (
        f"a node no value can satisfy returned {held[0]!r}; an unconstructible node is "
        "reported under its own reason, never answered with a value the node refuses"
    )
    assert len(held) > 1 and str(held[1]).strip(), (
        "the refusal carries no reason, so a reader of the red row cannot tell whether the "
        "document, the constructor or the screen said no"
    )


@pytest.mark.parametrize("document,pointer", A9_POINTERS, ids=lambda v: v.rsplit("/", 1)[-1])
def test_the_four_pointers_a_leading_hop_reaches_are_still_reached(
    document: str, pointer: str
) -> None:
    """``adcp-client-python-09ti``'s cause (A), held at the four pointers it names.

    Each is a BRANCH pointer whose ``/allOf/0`` is the branch's own conjunct, where the
    accessor splices the enclosing node's same-instance statements in FRONT of the
    branch's conjuncts -- so the index the document spells and the index into the applied
    node name different nodes. ``harness._steps`` takes a LEADING ``allOf`` hop on the
    document's own conjunct list for exactly this, and these four are the whole population
    it changes the answer for.

    Held on the committed verdict table rather than by re-walking, because what has to stay
    true is the GRADE: the obligation reaches the fact and discharges it.
    """
    table = {f"{row.get('document')}{row.get('pointer')}" for row in _rows()}
    assert f"{document}{pointer}" not in table, (
        f"{document}{pointer} is a not-pass row again. It is one of the four pointers the "
        "leading-allOf reading in harness._steps exists to reach; if the obligation can no "
        "longer walk there it reports rather than fails silently, so check the walk before "
        "the declaration (adcp-client-python-09ti cause A, closed between 62ceda40d and "
        "00092b521)."
    )
