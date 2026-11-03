"""§8 sentence 3b: a negated presence-and-value condition is ONE complemented match.

``docs/plan/rebuild-plan.md`` §8, "A NEGATED PRESENCE-AND-VALUE CONDITION IS ONE
COMPLEMENTED MATCH, AND ``Match`` GAINS THE COMPLEMENT" (decided 2026-11-03), which
**replaces** a sentence that said such conditions DECLARE:

    The condition the bundle writes most often is ``not: {required: [k], properties: {k:
    {const: v}}}`` -- the inner schema being *"k is present AND equals v"*.  By De Morgan
    its negation is *"k is absent OR k differs from v"*, and that was read as a
    disjunction no clause list can state, since a rule's ``when`` is a conjunction.
    **That reading is wrong, and the error is in where the disjunction sits.**  It is not
    a disjunction of independent facts about different keys; it is **one predicate about
    one key** -- *k is not v, whether by absence or by value* -- and a single clause says
    it the moment the clause can say *not*.

**WHAT THE DEFECT WAS, in a payload, because §8 asks every claim here to have one.**  At
``450449c5`` the condition read as nothing, so nothing was lowered and -- the reduction
taking its early return before the arm was recorded -- nothing was declared either.  The
class then BUILT a payload the document refuses, which is §8 sentence 1's second
direction: *"A dropped CONDITIONAL's witness is the opposite: a value the document
refuses and the class admits."*  Measured at ``formats/canonical/_base.json``'s
``SlotsItem``, which is the one site the bundle states this shape at:

    {"asset_type": "image", "asset_group_id": "banner", "logo_slots": ["logo_card_light"]}

    at 450449c5   schema half REFUSES   constructor ACCEPTS   -- the class is wider
    under 3b      schema half REFUSES   constructor REFUSES

:func:`test_the_class_refuses_what_its_document_refuses_at_the_site_the_bundle_states`
is that payload, and it is the test of record for this decision.

**THE OTHER DIRECTION IS WHAT KEEPS THE COMPLEMENT FROM BEING A NARROWING**, and it is
the half a rule stronger than its document would fail: absence satisfies the condition,
and so does a present-and-DIFFERING value, so the consequent must fire for both and for
neither of the values the condition pins.  §2 permits a model looser than its document
and forbids a tighter one, so the three states are asserted one by one rather than only
at the payload that found the defect.

**AND THE LIMIT IS ASSERTED TOO.**  A negation that genuinely spans two keys is a
disjunction ACROSS keys, which a conjunction of clauses cannot state; §8 keeps it
declaring, and
:func:`test_a_negation_that_spans_two_keys_is_not_read_as_a_conjunction_of_complements`
is why a later row cannot widen the arm into one.  Without it the complement would read
``not (a present and b present)`` as *a absent AND b absent* -- a rule refusing what the
document admits, which is the one outcome §2 forbids outright.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adcp.types._runtime import Match
from codegen import bundle
from codegen.keywords import Position
from codegen.lower import rules
from tests.nodeset import claimed

BUNDLE = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"

#: The payload the defect was measured with, and the key the condition is about.
#:
#: ``asset_type`` is in it because the node REQUIRES it: a payload short of a required
#: field is refused by the field half and says nothing about a rule, which is how the
#: first reading of this witness came to report an agreement that was about ``asset_type``.
A_PINNED_VALUE = "logo"
A_FORBIDDEN_KEY = "logo_slots"
A_COMPLETE_PAYLOAD: dict[str, Any] = {"asset_type": "image", A_FORBIDDEN_KEY: ["logo_card_light"]}


def _negated_conditions() -> dict[tuple[str, str], Any]:
    """Every ``(document, pointer)`` of the bundle whose ``if`` is exactly a ``not``.

    Read off the SOURCE bundle through ``bundle.nodes_at`` -- the one walk, with the
    position the descent column assigns rather than one recovered from the pointer -- so
    the set is a function of the bundle and not of this file.  A ``not`` under an ``if``
    is at RULE twice over, and the reduction is asked at RULE for that reason.
    """
    found = {}
    for document in bundle.portable(BUNDLE):
        for pointer, node, _ in bundle.nodes_at(bundle.read(BUNDLE, document)):
            condition = node.get("if")
            if isinstance(condition, dict) and set(rules._keys(condition)) == {"not"}:
                found[document, pointer] = condition
    return found


def test_every_negated_condition_the_bundle_states_lowers_as_one_complemented_clause() -> None:
    """The reduction reads each one, and reads it as ONE clause with a complement.

    Three things per site, and the first is what makes the other two a claim about the
    bundle rather than about a literal: the reduction returns a clause list at all, that
    list is ONE clause, and that clause's presence is IMMATERIAL with a FORBIDDEN value
    set.  A positive clause here would be the two-state reading back, and a clause per
    key would be the disjunction-across-keys §8 forbids.
    """
    stated = _negated_conditions()
    sites = claimed("negated conditions the bundle states", stated)

    unread = {}
    for document, pointer in sites:
        read = rules._clauses(stated[document, pointer])
        if read is None or len(read) != 1:
            unread[f"{document}#{pointer}"] = read
            continue
        _, present, allowed, forbidden = read[0]
        if present is not None or allowed is not None or not forbidden:
            unread[f"{document}#{pointer}"] = read
    assert unread == {}, {
        "negated conditions that did not lower as one complemented clause": unread
    }


def test_the_complement_admits_absence_and_a_differing_value_and_refuses_the_pinned_one() -> None:
    """De Morgan, one state at a time, on the clause the reduction mints.

    ``not (k present AND k == v)`` is ``k absent OR k != v``, so all three states are
    asserted: the two that must SATISFY the clause and the one that must not.  A clause
    satisfied by only one of the first two is the two-state flag's own failure and is
    what sentence 3b names.
    """
    clause = Match("k", None, None, (A_PINNED_VALUE,))

    assert clause.holds(frozenset(), {}) is True, "absence must satisfy the complement"
    assert clause.holds(frozenset({"k"}), {"k": "other"}) is True, (
        "a present-and-DIFFERING value must satisfy the complement"
    )
    assert clause.holds(frozenset({"k"}), {"k": A_PINNED_VALUE}) is False, (
        "present-and-equal is the one state the negation excludes"
    )


def test_the_two_state_readings_are_unchanged_by_the_third_state() -> None:
    """``present=True`` and ``present=False`` answer exactly what they answered before.

    ``present`` is now ``bool | None`` and ``not None`` is ``True``, so a truthy read of
    it would have made an immaterial clause behave as ``present=False`` at the absent
    instance.  These four are the states that must NOT have moved, asserted here because
    every rule the tree already carries is one of them.
    """
    required = Match("k", True, (A_PINNED_VALUE,))
    assert required.holds(frozenset({"k"}), {"k": A_PINNED_VALUE}) is True
    assert required.holds(frozenset({"k"}), {"k": "other"}) is False
    assert required.holds(frozenset(), {}) is False

    absent = Match("k", False)
    assert absent.holds(frozenset(), {}) is True
    assert absent.holds(frozenset({"k"}), {"k": 1}) is False


def test_a_negation_that_spans_two_keys_is_not_read_as_a_conjunction_of_complements() -> None:
    """§8: such a condition still DECLARES, and the reduction must say so.

    ``not (a present and b present)`` is *a absent OR b absent*.  A per-key complement
    would state *a absent AND b absent*, which refuses an instance carrying exactly one
    of them -- an instance the document admits.  So the reduction returns ``None`` and
    the node declares, which is the arm this test exists to keep.
    """
    across_keys = {"not": {"required": ["a", "b"]}}
    assert rules._clauses(across_keys) is None, (
        "a negation spanning two keys was read as a clause list, which states a "
        "conjunction the document does not"
    )

    one_key = {"not": {"required": ["a"], "properties": {"a": {"const": A_PINNED_VALUE}}}}
    read = rules._clauses(one_key)
    assert read is not None and len(read) == 1, (
        f"the one-key shape is the shape 3b lowers, and it did not: {read!r}"
    )


def test_a_negated_presence_only_condition_is_the_two_state_absence() -> None:
    """``not: {required: [k]}`` is ``k absent``, which the flag already said.

    The complement is not needed for this one and must not be invented for it: a value
    set forbidden where the document names no value would be a fact the document does not
    state.
    """
    read = rules._clauses({"not": {"required": ["k"]}})
    assert read == [("k", False, None, None)], read


def test_the_class_refuses_what_its_document_refuses_at_the_site_the_bundle_states() -> None:
    """The payload of record, through both halves of the pair.

    The document half is the class's own ``strict_validate`` -- D4's decision-maker,
    reading the document the class names -- and the constructor half is
    ``model_validate``.  The claim is agreement in BOTH directions at the one site the
    bundle states this shape: the pinned value admits the key, and every other state of
    the key forbids it.

    Read off the fresh tree like every other check in this suite, through the import the
    conftest binds, so the subject is what a run emits rather than the committed tree.
    """
    from adcp.types._schemas.formats.canonical._base import SlotsItem

    pinned = {**A_COMPLETE_PAYLOAD, "asset_group_id": A_PINNED_VALUE}
    differing = {**A_COMPLETE_PAYLOAD, "asset_group_id": "banner"}

    disagreed = {}
    for label, payload in (("pinned", pinned), ("differing", differing)):
        try:
            SlotsItem.strict_validate(payload)
            document_admits = True
        except Exception:  # the VERDICT is the reading, not the exception
            document_admits = False
        try:
            SlotsItem.model_validate(payload)
            class_admits = True
        except Exception:  # as above
            class_admits = False
        if document_admits != class_admits:
            disagreed[label] = {"document": document_admits, "class": class_admits}

    assert disagreed == {}, {
        "the class and its document disagree at the negated condition": disagreed
    }
    # And the two states are not both the same answer, which is what makes the agreement
    # above a reading of the condition rather than of a payload nothing distinguishes.
    assert SlotsItem.model_validate(pinned) is not None
    try:
        SlotsItem.model_validate(differing)
    except Exception as refused:
        assert A_FORBIDDEN_KEY in str(refused), str(refused)
    else:
        raise AssertionError(
            "a present-and-differing value satisfies the condition, so the consequent "
            f"must forbid {A_FORBIDDEN_KEY!r} -- the class admitted it"
        )


def test_no_widening_is_declared_where_the_complement_lowers() -> None:
    """§8: *"those sites lower with no declaration at all"*.

    ``DO NOT declare a condition the complement can lower`` -- a declaration there would
    describe a difference no payload can reach, which §8 deletes rather than counts.  The
    reading is over the stating document's own module, which is where §8 sentence 2 puts
    a fact's declaration.
    """
    import fresh
    from compiled import compiled

    stating = {document for document, _ in _negated_conditions()}
    claimed("documents stating a negated condition", stating, inside=bundle.portable(BUNDLE))

    out = compiled(BUNDLE, fresh.population())
    declared = {
        f"{a.document}{a.pointer} on {a.keyword}"
        for document in stating
        for a in out.approximations.get(document, ())
        if a.keyword in {"if", "then", "else", "not"}
    }
    assert declared == set(), {
        "conditions declared at a site the complement lowers": sorted(declared)
    }


def test_the_position_the_reduction_is_asked_at_is_the_one_the_table_assigns() -> None:
    """A ``not`` under an ``if`` is at RULE, and the reduction reads its keys there.

    ``rules._keys`` is ``intersect.declaring`` at :data:`Position.RULE`, so an annotation
    beside the ``not`` does not stop the arm from being taken -- a key that annotates
    without constraining is not part of what a rule TESTS.  The bundle states exactly
    that: the site of record carries a ``$comment`` on the enclosing node.
    """
    annotated = {
        "$comment": "an annotation is not part of what a rule tests",
        "not": {"required": ["k"], "properties": {"k": {"const": A_PINNED_VALUE}}},
    }
    assert set(rules._keys(annotated)) == {"not"}, sorted(rules._keys(annotated))
    assert bundle.DESCENDS["not"] is Position.RULE
    read = rules._clauses(annotated)
    assert read is not None and len(read) == 1, read
