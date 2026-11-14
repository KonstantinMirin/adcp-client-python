"""**Every value the document REFUSES, offered TO THE CLASS, which must refuse it.**

``docs/plan/final-state.md`` reading 1 is the sentence this file is about:

    Every class accepts every value its document admits, **refuses every value its
    document refuses**, and what it dumps validates against that document again.

``harness.check_accepts`` is the first half.  ``adcp-client-python-6oe`` is what the
absence of the second half cost: ``core/positive-postal-area-support.json`` refuses ``{}``
-- ``minProperties: 1`` in an ``allOf`` conjunct -- and
``PositivePostalAreaSupport.model_validate({})`` built one with ``__adcp_approximations__``
empty, a P0 in the shipped artifact that nothing reported for as long as it existed.

**AND ONE FORM OF THIS CHECK IS A MEASURED DEAD END.  IT IS NOT THE FORM BUILT HERE, AND
THE DIFFERENCE IS THE WHOLE DESIGN.**  ``codegen/harness.py``'s module docstring records
the refutation, under *"WHAT THIS MODULE USED TO DO AND NO LONGER DOES"*:

    The refuses check mutated ONE KEYWORD at a time, drew an instance the mutated schema
    accepts, and passed it to the caller's ``accept`` -- **which validates against THE
    DOCUMENT before constructing.**  So a step site asserted that ``jsonschema`` rejects a
    payload violating the schema it was handed, and **the generated class took no part in
    the outcome**: on ``core/pagination-request.json`` a model with ``Any`` on every field
    accepted, refused 75 of 75 instances and recorded no wrong acceptance, exactly as a
    faithful one did.  27,791 of those sites over the graded population were the suite's
    entire wall clock, spent on a property of a third-party validator.

So that instrument was deleted correctly and ``check_liveness`` is what survives it -- ONE
payload through ``strict_validate``, proving the schema half is CONNECTED, and its own
docstring forbids reading the answer as a measurement of the class.  **The ``refuses N/0``
figure the pair reports is liveness and has never been a refuses-check on the class.**

**THREE THINGS KEEP THIS FILE OUT OF THAT TRAP, and each is gated below rather than
asserted here:**

1. **The value is offered to the CLASS and to nothing else.**  ``check_refuses`` takes a
   ``construct`` callable and the production caller passes ``model_validate``, never
   ``pair.accept``.  No document-side gate runs between the witness and the class, so the
   class is the only thing that can produce the verdict.
2. **THE REFUTATION IS THE GATE.**
   :func:`test_a_model_with_any_on_every_field_fails_this_check` is the discarded
   instrument's own counterexample, run against this one: a model with ``Any`` on every
   field must FAIL.  If it ever passes, this has been rebuilt as the thing that measured
   ``jsonschema``, and the gate says so by name.
3. **Nothing is drawn and nothing is mutated.**  The witness is derived from the
   UNMODIFIED document by taking each keyword's boundary on the far side, and every
   candidate is screened by ``conforms(document, candidate) is False`` before it is
   offered -- so the document refuses it as the document is written, not as a mutation
   left it.  The cost is one ``conforms`` per keyword: ``hypothesis_jsonschema.from_schema``
   is never called, and that function is 151.24 s of a 151.51 s accepts pair
   (``tests/corpus.py``'s own table).

**WHY A PER-PAIR FORM IS KEPT BESIDE THE CELL FORM, on the measurement.**  The owner left
the choice open and the numbers answer it both ways, so both are kept and each says what
the other cannot:

* the CELL form (``tests/cells.py``'s ``grade``, which reads both of §2's directions) is
  COMPLETE over §5's 289 live cells and costs seconds, because a cell's cost is a function
  of the keyword and not of any document -- it reaches the 86 documents no draw finishes.
  What it cannot say is whether the WALK applied that cell at a real document's node,
  which is premise 3 of §8's induction.
* this file is the artifact, and it is affordable for the reason above: 15 pairs, no draw,
  one accepted instance each derived from the document's own ``const``/``enum``
  declarations.  It found nothing the cell form did not -- it CONFIRMS ``6oe`` at the
  document the P0 was measured on, which is the one thing a cell cannot do.

**WHAT IS NOT HERE.**  The sweep over the whole graded population, and the obstruction is
the INSTANCE rather than the check: over that population the accepted instance is
``check_accepts``' draw, held under a key whose computation needs the pair, so wiring it
means building 1,628 pairs -- ``tests/test_emit.py::graded_reports``, measured at "2h21m of
CPU at 20.3 GB" without completing (``adcp-client-python-82m.37``).  The per-pair check
costs one ``conforms`` per keyword inside that reader when it runs; until then the cell
form carries the completeness and the 15 pairs below carry the artifact.
"""

from __future__ import annotations

import importlib
import json
from functools import cache
from pathlib import Path
from typing import Annotated, Any

import fresh
import pytest
from compiled import compiled
from nodeset import claimed
from pydantic import BaseModel, StringConstraints, TypeAdapter

from adcp.types._base import OmittedNotNull
from codegen import bundle, harness
from codegen.harness import check_refuses, own_facts, refused_witnesses

REPO = Path(__file__).resolve().parents[1]
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE

#: The two keywords ``adcp-client-python-6oe`` is about: a property COUNT, which §5 lowers
#: to a ``PropertyCount`` rule over the keys the class RETAINED, and which the
#: document-side VALUE fold does not carry from a conjunct to the composed root.
COUNTS = ("minProperties", "maxProperties")

#: A bounded string, as the emitter writes it.  Built here rather than imported from the
#: tree so the INSTRUMENT's own gates do not depend on which documents happen to emit.
Bounded3 = Annotated[str, StringConstraints(max_length=3)]


# --------------------------------------------------------------------------- #
# the refutation: the discarded instrument's own counterexample, run against this one
# --------------------------------------------------------------------------- #
class AnyOnEveryField(BaseModel):
    """The model the deleted refuses-check could not tell from a faithful one.

    ``codegen/harness.py``'s refutation: "on ``core/pagination-request.json`` a model with
    ``Any`` on every field accepted, refused 75 of 75 instances and recorded no wrong
    acceptance, exactly as a faithful one did."  It is a BaseModel with ``extra="allow"``
    and no constraint anywhere, so it builds every object there is.
    """

    model_config = {"extra": "allow"}

    limit: Any = None
    cursor: Any = None


def test_a_model_with_any_on_every_field_fails_this_check() -> None:
    """**THE GATE THAT SAYS THIS IS NOT THE DISCARDED INSTRUMENT.**

    The deleted check routed its payload through ``accept``, which validates against the
    document first, so the document's own refusal was the whole outcome and a model with
    ``Any`` on every field scored exactly as a faithful one did.  This check offers the
    payload to ``model_validate``, so the class is the only thing that can answer -- and
    the proof of that is that the same model now FAILS, by value and by keyword.

    A document with a bound on every field it declares, and a class that carries none of
    them: every witness the reduction derives is a value the document refuses and the
    model builds.
    """
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            "cursor": {"type": "string", "maxLength": 8},
        },
        "required": ["limit"],
        "minProperties": 2,
    }
    result = check_refuses(schema, AnyOnEveryField.model_validate, {"limit": 1, "cursor": "a"})
    assert result.outcome == "widened_undeclared", result
    # The class took part: every witness it admitted is named, with the keyword the
    # document refused it on.
    assert result.undeclared, result
    assert {row[1] for row in result.undeclared} >= {"required", "minProperties"}, result


def test_the_same_document_passes_for_a_class_that_carries_the_facts() -> None:
    """The other side of the refutation, and it has to be here or the gate above is vacuous.

    A check that failed EVERY class would also fail a model with ``Any`` on every field,
    so the pair of tests is what says the verdict is a function of the class.  This model
    declares the same facts the document states, so every witness is refused.
    """

    class Faithful(BaseModel):
        model_config = {"extra": "forbid"}

        limit: Annotated[int, None] | int
        #: **``OmittedNotNull`` is part of "carries the facts" at an OPTIONAL property**,
        #: and it is not this fixture being bent to the instrument: the document states
        #: ``cursor: {"type": "string", "maxLength": 3}`` and nothing about ``null``, so a
        #: ``Bounded3 | None`` that TOOK a ``null`` here would be wider than this document
        #: in exactly the direction reading 1 forbids -- which is the defect
        #: ``adcp-client-python-4yhb`` measured at 13,790 fields and which the
        #: ``properties`` witness is here to find.  The emitter writes this marker at every
        #: such property now (``codegen.render._OptionalMember``), so this is the shape a
        #: faithful class HAS.
        cursor: Annotated[Bounded3 | None, OmittedNotNull] = None

    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer"},
            "cursor": {"type": "string", "maxLength": 3},
        },
        "required": ["limit"],
        "additionalProperties": False,
    }
    result = check_refuses(schema, Faithful.model_validate, {"limit": 1, "cursor": "abc"})
    assert result.rows, "the witnesses do not discriminate"
    assert result.outcome == "pass", result


# --------------------------------------------------------------------------- #
# the instrument, in the directions §2 reads a disagreement in
# --------------------------------------------------------------------------- #
def test_a_class_wider_than_its_document_fails_and_names_the_value() -> None:
    """The half ``check_accepts`` structurally cannot reach.

    A bare ``str`` against a document that bounds its length: the document refuses
    ``"abcd"`` and the class builds it, and the row carries the value AND the keywords the
    DOCUMENT refused it on -- asked of the document rather than assumed from the
    perturbation, which is ``violated_keywords``' own reason.
    """
    schema = {"type": "string", "maxLength": 3}
    result = check_refuses(schema, TypeAdapter(str).validate_python, "abc")
    assert result.outcome == "widened_undeclared", result
    row = next(r for r in result.undeclared if r[1] == "maxLength")
    # EXACTLY one character past the bound: §8's witness is "both sides of each bound and
    # the bound itself", so a reader of the failure sees which boundary was crossed.
    assert len(json.loads(row[0])) > len("abc")
    assert len(json.loads(row[0])) < len("abcd") + 1
    assert "maxLength" in row[2]
    # The same document and a class that carries the bound: every witness is refused.
    assert check_refuses(schema, TypeAdapter(Bounded3).validate_python, "abc").outcome == "pass"


def test_the_explicit_null_witness_is_derived_and_it_discriminates() -> None:
    """**The witness ``adcp-client-python-4yhb`` cost the whole model half of the tree.**

    Reading 1 at an optional property: a JSON Schema property outside ``required`` whose
    type does not admit ``null`` permits exactly one way of not supplying it -- leaving it
    out -- and the generator renders every such property ``T | None = None``, which
    pydantic reads as a type that ALSO admits an explicit ``null``.

    **No derivation of this module ever offered one.**  ``_far_side``'s ``type`` arm
    replaces the WHOLE instance with an alien value and never a property's value;
    :func:`refusing_payload`'s three perturbations are a dropped required key, an alien
    whole instance and an alien key.  So the two columns reading :func:`check_refuses` were
    green over 13,790 fields in 1,819 classes at which the class admitted a value its
    document refuses, undeclared -- and a column that cannot fail is not a column.
    Measured with the witness wired, over the same 2,584 pairs: ``undeclared`` goes from
    759 pass / 1,749 fail to 2,225 pass / 10 fail.

    **BOTH DIRECTIONS, because a check that failed every class would fail this one too.**
    The faithful class refuses the null and passes; the one that takes it is
    ``widened_undeclared`` with the value named.

    **AND THE SCREEN IS WHAT MAKES IT EXACT**: the third document below declares the same
    property ``type: ["integer", "null"]``, so the candidate is one the DOCUMENT ADMITS, no
    witness is yielded at all, and a class that takes the null is not charged for it.
    That is the clause that keeps the repair from manufacturing a narrowing at the 171
    fields of the tree whose document does admit a ``null``.
    """
    schema = {
        "type": "object",
        "properties": {"limit": {"type": "integer"}, "cursor": {"type": "string"}},
        "required": ["cursor"],
    }
    instance = {"cursor": "a"}
    #: The witness is DERIVED and it is the instance with the key set to an explicit null
    #: -- added where the instance does not carry the key, which is the commonest shape of
    #: an optional property and the one no reduction of a drawn instance can reach.
    witnesses = refused_witnesses(schema, instance)
    nulls = [(c, k, how) for c, k, how in witnesses if k == "properties"]
    assert {json.dumps(c, sort_keys=True) for c, _, _ in nulls} == {
        '{"cursor": "a", "limit": null}',
        '{"cursor": null}',
    }, nulls
    assert all("explicit null" in how for _, _, how in nulls), nulls

    class TakesTheNull(BaseModel):
        cursor: str
        limit: int | None = None

    taken = check_refuses(schema, TakesTheNull.model_validate, instance)
    assert taken.outcome == "widened_undeclared", taken
    assert any(json.loads(row[0]) == {"cursor": "a", "limit": None} for row in taken.undeclared), (
        taken.undeclared
    )

    class RefusesTheNull(BaseModel):
        cursor: str
        limit: Annotated[int | None, OmittedNotNull] = None

    #: The faithful class, which is what the emitter writes now
    #: (``codegen.render._OptionalMember``): the same annotation, the same default, and an
    #: explicit ``null`` refused with the type's own error.
    assert RefusesTheNull.model_validate({"cursor": "a"}).limit is None
    assert check_refuses(schema, RefusesTheNull.model_validate, instance).outcome == "pass"

    #: And the SCREEN: a document that admits the null yields no witness for it, so the
    #: class that takes one is never asked and never charged.
    nullable = {
        "type": "object",
        "properties": {"limit": {"type": ["integer", "null"]}, "cursor": {"type": "string"}},
        "required": ["cursor"],
    }
    assert not [
        c
        for c, k, _ in refused_witnesses(nullable, instance)
        if k == "properties" and isinstance(c, dict) and c.get("limit", 0) is None
    ]
    assert check_refuses(nullable, TakesTheNull.model_validate, instance).outcome == "pass"


def test_a_widening_passes_exactly_where_the_run_declares_one() -> None:
    """§2's rule read as a check, in both directions.

    A declaration that excused every keyword would be the allowlist §2's declared set
    exists not to be, so the keyword is compared: a declaration naming ``maxLength``
    passes the pair and one naming ``minLength`` does not.
    """
    schema = {"type": "string", "maxLength": 3}
    accept = TypeAdapter(str).validate_python
    assert check_refuses(schema, accept, "abc", declared=("maxLength",)).outcome == "pass"
    assert (
        check_refuses(schema, accept, "abc", declared=("minLength",)).outcome
        == "widened_undeclared"
    )


def test_a_document_that_refuses_nothing_this_reduction_builds_is_not_graded() -> None:
    """``no_witness`` is its own answer and not a pass smuggled through.

    The empty schema admits every instance there is, so there is nothing for a class to
    refuse.  Reporting ``pass`` would make a pair that offered NOTHING read identically to
    one that offered everything and was right, which is the shape §8 deleted an instrument
    for.
    """
    result = check_refuses({}, TypeAdapter(object).validate_python, {"a": 1})
    assert result.outcome == "no_witness"
    assert result.rows == ()


def test_a_conjuncts_keyword_is_a_witness_source_and_the_value_fold_does_not_carry_it() -> None:
    """``harness.own_facts`` and not ``_composed``, and ``6oe`` is why.

    ``FOLDED_FACTS`` is ``keywords.rendered_at(ROOT)`` and carries no property count, so
    the document-side VALUE fold does not bring ``minProperties`` from a conjunct to the
    composed root -- asserted, because the witness that found the P0 is derived from that
    keyword and from no other.  :func:`own_facts` asks the other question: which keywords
    are there to take a boundary FROM.
    """
    assert "minProperties" not in harness.FOLDED_FACTS
    composed = {
        "type": "object",
        "allOf": [{"minProperties": 1}, {"properties": {"a": {"const": True}}}],
    }
    assert own_facts(composed)["minProperties"] == 1
    witnesses = refused_witnesses(composed, {"a": True})
    assert any(keyword == "minProperties" for _, keyword, _ in witnesses), witnesses
    assert any(candidate == {} for candidate, _, _ in witnesses), witnesses


# --------------------------------------------------------------------------- #
# the CONDITIONAL arm, and its own refutation
# --------------------------------------------------------------------------- #
#: ``adcp-client-python-wvod``'s shape, written out: an ``allOf`` of a document that states
#: its OWN conditional plus a conjunct stating a second one.  Both apply to the whole
#: instance -- draft-07 applies every ``allOf`` member to it -- so an instance must satisfy
#: both, and the one the fold used to discard is the second.
WVOD_SHAPE: dict[str, Any] = {
    "type": "object",
    "allOf": [
        {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string"},
                "event_types": {"type": "array", "items": {"type": "string"}},
                "authentication": {
                    "type": "object",
                    "properties": {"schemes": {"type": "array"}, "credentials": {}},
                    "required": ["schemes"],
                },
            },
            "required": ["subscriber_id", "event_types"],
            "if": {"required": ["event_types"]},
            "then": {"properties": {"subscriber_id": {"minLength": 1}}},
        },
        {
            "if": {"required": ["authentication"]},
            "then": {"properties": {"authentication": {"required": ["credentials"]}}},
        },
    ],
}

#: An instance ``WVOD_SHAPE`` admits, and the one witness it must yield: the same instance
#: with ``credentials`` dropped, which is the payload ``adcp-client-python-wvod`` exhibits.
WVOD_ADMITTED: dict[str, Any] = {
    "subscriber_id": "s",
    "event_types": ["capabilities.changed"],
    "authentication": {"schemes": ["Bearer"], "credentials": {"token": "t"}},
}
WVOD_REFUSED: dict[str, Any] = {
    "subscriber_id": "s",
    "event_types": ["capabilities.changed"],
    "authentication": {"schemes": ["Bearer"]},
}


def test_the_conjunct_fold_does_not_decide_which_conditional_survives() -> None:
    """``adcp-client-python-x63t`` cause 3, as a gate on the two readings that replaced it.

    The fold was ``out.setdefault(keyword, value)`` in document order, so where two
    conjuncts each state an ``if`` only the FIRST survived -- and the one
    ``adcp-client-python-wvod`` is about is the second.  Measured on that row at
    ``protocol/sync-agent-notification-configs-request.json
    #/properties/notification_configs/items``, where conjunct 0 (the ``$ref``'d document's
    own) and conjunct 1 both state one and the fold kept conjunct 0's.

    Two obligations, because the fold went wrong in two ways:

    * ``own_facts`` folds NO conjunct's conditional, so it cannot report one conjunct's as
      the node's;
    * ``conditionals`` returns every triple UNMERGED and in document order, so neither is
      lost and neither conjunct's ``if`` is paired with the other's ``then`` -- a
      conditional no document states.

    The document itself is asserted to refuse ``WVOD_REFUSED``, so the shape under test is
    the one the row measured rather than one this file arranged to pass.
    """
    assert harness.conforms(WVOD_SHAPE, WVOD_ADMITTED) is True
    assert harness.conforms(WVOD_SHAPE, WVOD_REFUSED) is False
    # The node states no conditional of its own, so a fold is the only way one could
    # arrive -- and none does.
    facts = own_facts(WVOD_SHAPE)
    assert not harness.CONDITIONAL & set(facts), sorted(harness.CONDITIONAL & set(facts))
    # Both triples, unmerged, in document order, each with the ``then`` its own conjunct
    # states beside the ``if`` that conjunct states.
    triples = harness.conditionals(WVOD_SHAPE)
    assert [one["if"] for one in triples] == [
        {"required": ["event_types"]},
        {"required": ["authentication"]},
    ], triples
    assert triples[1]["then"] == {
        "properties": {"authentication": {"required": ["credentials"]}}
    }, triples


def test_a_conditional_stated_by_a_conjunct_is_a_witness_source() -> None:
    """The arm ``adcp-client-python-x63t`` measured absent, and the payload it must build.

    That row's measurement, over ``adcp-client-python-wvod``'s three nodes and from an
    instance each document admits::

        refused_witnesses aimed at: ['additionalProperties', 'required', 'type']
        ANY witness aimed at 'if'/'then'/'else': False
        the payload the document refuses is among the witnesses: False

    So even wired onto the graded path the instrument could not have found those three.
    Both halves are asserted here, and the second is the one that matters: the witness is
    the exhibited payload itself, DERIVED from an admitted instance rather than written
    down, so a derivation that merely aims at ``if`` and builds something else reddens.

    The keyword is ``if`` and not the arm's own ``required``, because that is the name §2's
    declaration carries: ``core/agent-notification-config.json``'s own root conditional is
    declared ``Approximation(..., keyword='if', ...)``, and a comparison against the
    declared set made on a different name would excuse nothing a module can declare.
    """
    witnesses = refused_witnesses(WVOD_SHAPE, WVOD_ADMITTED)
    assert any(keyword == "if" for _, keyword, _ in witnesses), witnesses
    assert WVOD_REFUSED in [candidate for candidate, _, _ in witnesses], witnesses
    # And it came from the conjunct's arm, named in the reason a reader of a failure gets.
    how = next(how for candidate, _, how in witnesses if candidate == WVOD_REFUSED)
    assert "credentials" in how and "authentication" in how, how


def test_the_conditional_arm_fails_a_model_that_drops_the_conditional() -> None:
    """**THE ARM'S OWN REFUTATION, which ``adcp-client-python-x63t`` requires.**

    "A conditional arm must be added with its own refutation -- wvod's own payload is the
    counterexample, so the arm is proved red by construction before it is trusted."  A
    class that carries the document's conditional refuses ``WVOD_REFUSED``; one that drops
    it -- which is exactly what the three measured classes do -- admits it, and with
    nothing declared that is ``widened_undeclared``.

    Both directions, because a check that failed every class would fail a dropped
    conditional too and say nothing about the arm.  And the DECLARED direction as well: §2
    permits the looseness as a declared widening, so a declaration naming ``if`` passes the
    same class and the arm is a comparison rather than an allowlist.
    """

    class DropsTheConditional(BaseModel):
        """The shape the three measured classes have: the properties, and no conditional."""

        model_config = {"extra": "allow"}

        subscriber_id: str
        event_types: list[str]
        #: The conditional is what this class DROPS; the explicit ``null`` at an optional
        #: property is a second, unrelated widening, and leaving it here would make the
        #: declared direction below assert that a module declaring ``if`` passes a class
        #: that is also wider at ``properties``.  One fixture, one dropped fact.
        authentication: Annotated[dict[str, Any] | None, OmittedNotNull] = None

    result = check_refuses(WVOD_SHAPE, DropsTheConditional.model_validate, WVOD_ADMITTED)
    assert result.outcome == "widened_undeclared", result
    assert any(row[1] == "if" for row in result.undeclared), result.undeclared
    assert any(json.loads(row[0]) == WVOD_REFUSED for row in result.undeclared), result.undeclared

    #: The same class and the same document, with the widening DECLARED under the keyword
    #: §2 names.  A pass here is what makes the check a comparison; a failure would mean a
    #: module cannot declare this widening at all.
    declared = check_refuses(
        WVOD_SHAPE, DropsTheConditional.model_validate, WVOD_ADMITTED, declared=("if",)
    )
    assert declared.outcome == "pass", declared

    #: And a class that CARRIES the conditional refuses the witness, so the verdict is a
    #: function of the class.  A validator over the document itself is that class: §5
    #: lowers a conditional the annotation cannot carry to a rule on the nearest class, and
    #: what the rule has to do is refuse this value.
    def carries(value: Any) -> Any:
        if harness.conforms(WVOD_SHAPE, value) is not True:
            raise ValueError("the conditional refuses this value")
        return value

    assert check_refuses(WVOD_SHAPE, carries, WVOD_ADMITTED).outcome == "model_error"


def test_a_conditional_no_value_was_offered_for_is_not_a_pass() -> None:
    """**The reach, which is not the population, measured rather than described.**

    A conditional's boundary lies inside the region its ``if`` selects and the reduction
    has ONE accepted instance, so where that instance is outside the region and the node
    states no ``else`` there is no arm in force and the class is never asked.  Measured on
    ``adcp-client-python-wvod``'s own third site --
    ``account/sync-accounts-request.json#/properties/accounts/items/properties/notification_configs/items``
    -- whose draw is ``{event_types, subscriber_id, url}``: it satisfies neither of that
    node's two ``if``s, so the row that proved the other two reports nothing there.

    A ``pass`` would say the class refuses what its document refuses, about the one fact
    the row is about and a value for which was never built.  So the result carries the
    unreached conditionals with the reason each, and the verdict reads ``absent`` with the
    count against the node's own total.
    """
    #: The admitted instance carries no ``authentication``, so the second conjunct's ``if``
    #: is not satisfied and that conjunct states no ``else``.
    outside = {"subscriber_id": "s", "event_types": ["capabilities.changed"]}
    assert harness.conforms(WVOD_SHAPE, outside) is True
    unreached = harness.unreached_conditionals(WVOD_SHAPE, outside)
    assert len(unreached) == 1, unreached
    assert "authentication" in unreached[0] and "else" in unreached[0], unreached

    #: A class that refuses every witness this instance DOES yield -- the two required
    #: keys, the ``minLength`` conjunct 0's own ``then`` states, and each alien JSON type.
    #: So the result is a ``pass`` on everything offered, which is precisely the case the
    #: verdict must not report as green: the one conditional nobody built a value for is
    #: the fact ``adcp-client-python-wvod`` is about.
    class CarriesWhatWasOffered(BaseModel):
        model_config = {"extra": "allow"}

        subscriber_id: Annotated[str, StringConstraints(min_length=1)]
        event_types: list[str]
        #: DECLARED, where this fixture used to leave the key to ``extra="allow"``.  An
        #: undeclared key under that policy admits EVERY value, so the ``properties``
        #: witness -- an explicit ``null`` at ``authentication``, which the document
        #: refuses on ``type`` -- was admitted, and the pass this test is about would have
        #: been a ``widened_undeclared`` about a different fact.  The node declares the
        #: property, so a faithful class declares it; what this class still does not carry
        #: is the second conjunct's ``if``, which is the fact the test is about.
        authentication: Annotated[dict[str, Any] | None, OmittedNotNull] = None

    result = check_refuses(WVOD_SHAPE, CarriesWhatWasOffered.model_validate, outside)
    assert result.outcome == "pass", result
    assert result.unreached == unreached, result
    #: The DENOMINATOR, as an equality between two derivations and never a pinned integer:
    #: the result's count is the node's own triples, so a document that grows a conditional
    #: moves both sides and neither has to be told.
    sites = len(harness.conditionals(WVOD_SHAPE))
    assert result.conditional_sites == sites, result
    #: The cell, which is where a reader meets this: ``absent`` with the count, never
    #: ``pass`` -- and the state is read off the table's own function so a rename cannot
    #: leave this asserting a token nothing writes.
    verdict = harness._undeclared_verdict(result)
    assert verdict.state == harness.ABSENT, verdict
    assert verdict.cause == f"{len(unreached)}_of_{sites}_conditionals_unreached", verdict
    #: And the instance that IS inside the region reaches it, so the ``absent`` above is a
    #: statement about the draw and not about the node.
    assert harness.unreached_conditionals(WVOD_SHAPE, WVOD_ADMITTED) == (), WVOD_ADMITTED


# --------------------------------------------------------------------------- #
# the artifact: the pairs whose composed root states a property count
# --------------------------------------------------------------------------- #
@cache
def counting_roots() -> dict[str, dict]:
    """Every portable document whose COMPOSED ROOT states a property count, with its node.

    Derived over the bundle through ``harness.own_facts`` -- the same fold the witness
    builder reads -- so the set is the bundle's answer and a document that grows a count
    joins it without being told.  The node is the document OF RECORD, which is the schema
    a class's own ``strict_validate`` answers from (D4).
    """
    known = set(bundle.portable(BUNDLE))
    out: dict[str, dict] = {}
    for document in sorted(known):
        node = bundle.record(BUNDLE, document, known)
        if not isinstance(node, dict):
            continue
        if any(keyword in own_facts(node) for keyword in COUNTS):
            out[document] = node
    return out


def an_instance_the_document_admits(node: dict) -> dict | None:
    """One instance for the reduction to perturb, built from the node's own declarations.

    **Not a draw**, which is this check's whole cost argument: an object root whose
    properties pin a ``const`` or an ``enum`` is satisfied by the object carrying one
    pinned value per key, and a count's witness is derived by REMOVING keys from it.  A
    node this cannot satisfy is skipped by name rather than graded against a guess -- and
    the instance is offered to the DOCUMENT before anything else reads it, so a wrong one
    skips the pair instead of producing a verdict.
    """
    built: dict[str, Any] = {}
    for key, pinned in _pins(node, node).items():
        built[key] = pinned
    return built or None


def _pins(view: Any, root: dict, depth: int = 0) -> dict[str, Any]:
    """Each property key some VIEW of this node pins to a value, with that value.

    **One view per ``allOf`` member and the key is NOT won by the first of them**, which is
    a measured skip of this gate rather than a refinement:
    ``core/positive-postal-area-support.json`` declares ``us_zip`` twice -- the inlined
    base types it ``boolean`` and the conjunct pins it ``const: true`` -- so a reader that
    took one view's declaration for the key found no pin at all, no instance was derivable,
    and the pair ``adcp-client-python-6oe`` was measured on SKIPPED while fourteen others
    reported green.  Later views fill a key no earlier view PINNED, which is what makes the
    pin the thing being searched for rather than the declaration.

    A bare local pointer is read as the node it names, because §4 leaves a local ``$ref``
    exactly as the document writes it AND ``bundle.record``'s own sharing writes one: both
    of that document's declarations arrive as ``{"$ref": "#/definitions/Shared<N>"}``.  The
    hop goes through ``bundle.node_at`` and nowhere else -- "two readings of RFC 6901's two
    escapes is how an inliner and a grader come to disagree about which node a reference
    names".  A pointer naming nothing contributes no pin, which is the fail-safe direction:
    the pair skips by name rather than being graded against a guess.
    """
    if not isinstance(view, dict) or depth > 8:
        return {}
    out: dict[str, Any] = {}
    for key, declaration in (view.get("properties") or {}).items():
        resolved = _locally(declaration, root)
        if "const" in resolved:
            out[key] = resolved["const"]
        elif isinstance(resolved.get("enum"), list) and resolved["enum"]:
            out[key] = resolved["enum"][0]
    for conjunct in view.get("allOf") or ():
        for key, value in _pins(_locally(conjunct, root), root, depth + 1).items():
            out.setdefault(key, value)
    return out


def an_instance_this_check_can_offer(document: str, node: dict) -> Any:
    """One instance ``document`` admits for the reduction to perturb, or ``None``.

    **TWO DERIVATIONS, and the second is §8's FIXTURE DERIVATION** -- "a referenced
    document is graded by its own pair", read here at the document's own pair rather than
    at a referring position.  ``harness.Fixtures`` holds it, and what it answers with for a
    root pointer is the instance the ACCEPTS CORPUS already holds for that pair: drawn from
    the document by ``check_accepts``, keyed on the document's raw bytes and its raw
    reference closure's, and re-offered to the document on every read.

    **It is here because eight documents of this set reported "no instance derivable" and
    a check scoped away from eight of its own documents reports green.**
    ``docs/plan/final-state.md`` names that as one of the three forms of the same evasion
    -- "a scope that omits the code the check is about" -- and :func:`_pins` reaches only a
    root whose properties pin a ``const`` or an ``enum``, which these eight do not:
    ``core/bidding-policy-capability.json``, ``core/deadline-policy.json``,
    ``core/installment-deadlines.json``, ``core/principal-state.json``,
    ``core/product-change-map.json``, ``core/targeting-overlay-support.json``,
    ``governance/audience-constraints.json`` and
    ``media-buy/product-discovery-criteria.json``.

    The pinned derivation is asked FIRST and is not replaced, for the reason
    :func:`_pins`' own docstring gives: it costs no draw at all, and
    ``core/positive-postal-area-support.json`` -- the document ``adcp-client-python-6oe``
    was measured on -- is satisfied by it.

    **THE DOCUMENT DECIDES, in both arms.**  Each candidate is offered to ``conforms``
    before it is returned, so a derivation that misreads a node contributes nothing rather
    than a verdict against a guess.
    """
    pinned = an_instance_the_document_admits(node)
    if pinned is not None and harness.conforms(node, pinned) is True:
        return pinned
    import test_emit  # the tree reader, one reading for the whole suite  # noqa: PLC0415

    drawn = test_emit.fixtures().one(document, "#")
    if drawn is not harness.NONE and harness.conforms(node, drawn) is True:
        return drawn
    return None


def _locally(declaration: Any, root: dict) -> dict:
    """``declaration`` with a bare local pointer resolved against ``root``."""
    if not isinstance(declaration, dict):
        return {}
    ref = declaration.get("$ref")
    if set(declaration) != {"$ref"} or not isinstance(ref, str) or not ref.startswith("#"):
        return declaration
    try:
        target = bundle.node_at(root, ref[1:])
    except (KeyError, IndexError, TypeError, ValueError):
        return declaration
    return target if isinstance(target, dict) else declaration


@pytest.mark.parametrize("document", sorted(counting_roots()))
def test_every_counting_root_refuses_the_count_its_document_refuses(document: str) -> None:
    """**The gate ``adcp-client-python-6oe`` earns**, over the derived set and not one pair.

    The class is read off the tree a FRESH run emits (``tests/fresh.py``'s rule: "grading
    reads the tree a fresh run emits; the committed tree is an ARTIFACT, verified by one
    byte-compare"), and its declarations are read off it the way a consumer reads any class
    attribute -- ``harness.declarations_of``, which §9 requires of the verifier.

    **Red at ``5021772c`` on ``core/positive-postal-area-support.json``**: the document
    refuses ``{}``, the class built one, and nothing was declared.
    """
    assert fresh.schemas() is not None, fresh.FAILURE
    node = counting_roots()[document]
    #: **NO SKIP ON THE INSTANCE, which is the change ``final-state.md`` requires.**  Eight
    #: documents of this set had none derivable from their own ``const``/``enum``
    #: declarations and reported green while being unrun;
    #: :func:`an_instance_this_check_can_offer` adds §8's fixture derivation beside the
    #: pinned one and the set is graded whole.  An assertion and not a skip, so a document
    #: that stops having one REDDENS with its name.
    instance = an_instance_this_check_can_offer(document, node)
    assert instance is not None, (
        f"no instance {document} admits is derivable, so this document's pair would be "
        "scoped out of a check that reports green over the others"
    )
    symbol = _root_of(document)
    if symbol is None:
        #: An assertion for the same reason the instance above is one: §2 makes every
        #: portable document emit, ``./check`` reports ``refused 0``, and a skip here would
        #: scope this check away from a document whose class exists.  Measured: 0 of this
        #: set take it.
        raise AssertionError(f"{document} emits no root class, so its pair is ungraded")
    result = check_refuses(
        node,
        TypeAdapter(symbol).validate_python,
        instance,
        declared=tuple(one.keyword for one in harness.declarations_of(symbol)),
    )
    assert result.outcome in ("pass", "no_witness"), (document, result)


@cache
def _root_of(document: str) -> Any:
    """The ROOT symbol of a document's FRESH module, **resolved by its PROVENANCE POINTER**.

    ``Emitted.declared`` is "the run's own record of WHERE each symbol came from" --
    pointer -> symbol -- so the root is the symbol the run declared at the document's root
    pointer, and the name it happens to carry decides nothing.

    **WHAT STOOD HERE WAS ``__all__[0]`` AND IT GRADED A DIFFERENT DOCUMENT'S NODE.**  The
    export list is SORTED, so the first export is whichever declaration of the module sorts
    first alphabetically -- which is the root only by luck.  Measured at ``781f873d1``, this
    reading handed the gate below:

    * ``core/targeting-overlay-support.json`` -> ``BrowserSupport``
      (``Supported | BrowserSupportFamilies``), not ``TargetingOverlaySupport``;
    * ``core/targeting-overlay-requirements.json`` -> ``BrowserRequirement``, not
      ``TargetingOverlayRequirements``.

    Both are ``Supported | ...`` unions whose first branch is ``Literal[True]``, so both
    ADMITTED the witness ``true`` that the root's ``type: object`` refuses, and the gate
    reported ``widened_undeclared`` on keyword ``type`` under ``not`` -- a widening of a
    node the check was never asked about, attributed to the document.  The verdict was
    right about the symbol it was handed and about nothing else, which is why the reason and
    not only the verdict has to be read.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    #: ``Emitted.emitted`` maps a document to the MODULE NAME the run wrote it to, which
    #: is the dotted name a consumer imports -- so nothing here spells a path.
    name = out.emitted.get(document)
    if name is None:
        return None
    #: The ROOT POINTER's own declaration.  ``Module.declared`` spells a document's root as
    #: the empty pointer, and a document whose root declares nothing is absent from the map
    #: rather than carrying a name that is not its root's.
    root = out.declared.get(document, {}).get("")
    if root is None:
        return None
    return getattr(importlib.import_module(name), root, None)


def test_every_graded_root_is_the_class_the_run_declared_at_the_documents_root() -> None:
    """**The symbol under test answers for the document under test, by its own pointer.**

    ``docs/plan/architecture.md``'s identity rule read as a grading rule, and the gate the
    three reds at ``781f873d1`` earn: a class resolved by NAME can be a faithful class of
    the WRONG NODE, and the verdict it produces is then right about something nobody asked.

    **ASSERTED BY VALUE AND NOT BY PROVENANCE**, because a provenance reading is satisfied
    by the defect: the three symbols the by-name reading handed over were a ``Supported |
    ...`` union and an ``Annotated[dict[...]]`` alias, neither of which carries an
    ``__adcp_schema__`` at all, so a gate asking the symbol for its pointer EXCLUDED exactly
    the cells that were wrong and passed.  A/B'd, both readings, 2026-11-05.  What a wrongly
    resolved class cannot do is ACCEPT the instance this document admits -- that is reading
    1's own first half, it is a value, and it reddens on all three.

    Two statements, both derived and neither a pin:

    * the class the gate grades accepts the instance the gate offers it, over the whole
      counting population and with the document's own verdict asserted first, so a witness
      the document itself refuses cannot make this pass;
    * the reading by NAME resolves a NON-EMPTY subset of the population to a different
      declaration, which is what stops the first statement being a property of this
      bundle's alphabet.  Measured at ``781f873d1``: 3 of the 15 counting roots, and all
      three reported ``widened_undeclared`` under it.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    population = claimed("counting roots the gate grades", set(counting_roots()))
    refused: dict[str, str] = {}
    for document in sorted(population):
        node = counting_roots()[document]
        instance = an_instance_this_check_can_offer(document, node)
        assert instance is not None, document
        # The DOCUMENT's own verdict first: a witness it refuses would make the class's
        # refusal correct, and this gate would then be reading reading 1 backwards.
        assert harness.conforms(node, instance) is True, (document, instance)
        try:
            TypeAdapter(_root_of(document)).validate_python(instance)
        except Exception as error:  # noqa: BLE001 -- any refusal is a refusal
            refused[document] = f"{type(error).__name__}: {str(error)[:200]}"
    assert refused == {}, refused
    # The NON-VACUITY, off the same ``declared`` record the resolution reads: the documents
    # whose alphabetically first declaration is not the root's.  Named, so a reader of a
    # green run sees which they are, and asserted non-empty, so the statement above is
    # about the pointer and not about this bundle's naming luck.
    by_name = claimed(
        "counting roots a reading by NAME resolves elsewhere",
        {
            document
            for document in population
            if (declared := out.declared.get(document, {}))
            and min(declared.values()) != declared.get("")
        },
        inside=population,
    )
    assert by_name


def test_the_counting_population_is_named_and_derived() -> None:
    """The denominator the gate above ranges over, NAMED rather than counted.

    ``nodeset.claimed`` so a document leaving the set reddens with the document named,
    where an integer would say only that a number moved.  15 of the bundle's 1,015 distinct
    documents state a property count at a composed root -- ``bundle.portable`` returns
    1,054 PATHS over 1,015 documents, 39 of them byte-identical duplicates under
    ``core/async-response-refs/``, and this set holds none of the duplicates.
    """
    population = claimed("portable roots stating a property count", set(counting_roots()))
    assert "core/positive-postal-area-support.json" in population
    assert not any(d.startswith("core/async-response-refs/") for d in population)


def test_the_document_the_p0_was_measured_on_is_GRADED_and_never_skipped() -> None:
    """**The one document ``6oe`` names reaches a verdict, and that is its own gate.**

    ``docs/plan/final-state.md``: "a scope that omits the code the check is about" is one
    of the three forms of the same evasion, and a parametrised gate that SKIPS the pair it
    exists for is exactly that -- it reports green over fourteen other documents while the
    P0's own pair is unrun.  It skipped once, measured: ``harness.own_facts`` gap-filled
    ``properties`` instead of merging by key, so the inlined base won the key map and no
    instance was derivable from the document's own declarations.
    """
    document = "core/positive-postal-area-support.json"
    node = counting_roots()[document]
    instance = an_instance_the_document_admits(node)
    assert instance, "no instance derivable -- the gate for 6oe would skip"
    assert harness.conforms(node, instance) is True, instance
    witnesses = refused_witnesses(node, instance)
    # ``{}`` is THE witness: the document's conjunct states ``minProperties: 1`` and the
    # empty object is the far side of it, which is the value a fresh run's class built
    # at ``5021772c`` with nothing declared.
    assert any(candidate == {} for candidate, _, _ in witnesses), witnesses
    assert fresh.schemas() is not None, fresh.FAILURE
    symbol = _root_of(document)
    assert symbol is not None
    result = check_refuses(
        node,
        TypeAdapter(symbol).validate_python,
        instance,
        declared=tuple(one.keyword for one in harness.declarations_of(symbol)),
    )
    assert result.outcome == "pass", result


# --------------------------------------------------------------------------- #
# the marker is the declaration, and it is PRECISE
# --------------------------------------------------------------------------- #
#: The document the three clauses below are read on: one optional property whose ``type``
#: refuses ``null``, one required property, and nothing else.  Stated once because the
#: claim is about which FIELD the class binds ``note`` to, so the three must be asked
#: about one document or they are three measurements.
_A_DOCUMENT_REFUSING_NULL = {
    "type": "object",
    "properties": {"id": {"type": "integer"}, "note": {"type": "string"}},
    "required": ["id"],
    "additionalProperties": False,
}
_AN_ACCEPTED_INSTANCE = {"id": 1, "note": "a"}


def test_the_marker_declares_an_explicit_null_at_its_own_field() -> None:
    """**A ``None`` AT A MARKED FIELD IS DECLARED -- by the marker, at the site, once.**

    ``docs/plan/rebuild-plan.md`` §2 *"``None`` is absence and ``null`` is a value"* takes
    the decision and its last paragraph says the widening is declared; the marker is where
    it is stated, at every one of the fields it applies to.  So the class below is wider
    than its document at ``note`` on the Python route -- deliberately, and with
    ``Approximation`` declaring nothing -- and this column must read it as a ``pass``.

    The witness is not constructed here: ``refused_witnesses``' explicit-null derivation
    builds it from the document's own ``properties``, so this clause grades the production
    derivation rather than a payload written to match the exemption.
    """

    class Marked(BaseModel):
        model_config = {"extra": "forbid"}

        id: int
        note: Annotated[str | None, OmittedNotNull] = None

    offered = refused_witnesses(_A_DOCUMENT_REFUSING_NULL, _AN_ACCEPTED_INSTANCE)
    claimed(
        "derivations the document's own keywords offer",
        tuple(how for _candidate, _keyword, how in offered),
    )
    assert any(
        isinstance(candidate, dict) and candidate.get("note", False) is None
        for candidate, _keyword, _how in offered
    ), offered

    result = check_refuses(_A_DOCUMENT_REFUSING_NULL, Marked.model_validate, _AN_ACCEPTED_INSTANCE)
    assert result.rows, "the witnesses do not discriminate"
    assert result.outcome == "pass", result
    assert not result.undeclared, result
    # and the exemption is the MARKER's and not the declaration machinery's: nothing was
    # declared at this pointer, which is the whole reason the row used to fail.
    assert result.declared == (), result
    #: **THE OTHER PRECISION DIRECTION IS ALREADY ASSERTED IN THIS FILE and is not
    #: restated here**, which is §8's rule about a fact being declared once applied to the
    #: gate: :func:`test_the_explicit_null_witness_is_derived_and_it_discriminates` offers
    #: the same derived null to a ``TakesTheNull`` carrying NO marker and requires
    #: ``widened_undeclared`` with that row named, and to a ``RefusesTheNull`` carrying one
    #: and requires ``pass``.  Both of those clauses were RED before this exemption
    #: existed, so the direction has a gate older than the change it grades.


def test_any_other_value_at_a_MARKED_field_is_still_undeclared() -> None:
    """**THE SECOND PRECISION DIRECTION: the marker declares a ``None`` and nothing else.**

    ``OmittedNotNull`` states one fact -- that this property's absence is spelled ``None``
    -- so it cannot stand for a different widening at the same field.  A declaration that
    covered every value at its own field would be an allowlist by position, which is what
    ``check_refuses``' comparison against ``declared`` is written to avoid in this
    direction too.

    **Asked of the predicate directly, and that is the right level rather than a shortcut.**
    ``refused_witnesses``' per-property derivation builds exactly one candidate per key and
    the value in it is always ``None``, so no document can make the production path offer
    "some other value at this field" -- the condition is reachable only here.  Three
    candidates at one marked field of one class, so the claim that they are separable is
    read off one fixture.
    """

    class Marked(BaseModel):
        model_config = {"extra": "forbid"}

        id: int
        note: Annotated[str | None, OmittedNotNull] = None

    built = Marked.model_validate(_AN_ACCEPTED_INSTANCE)
    assert harness.the_marker_declares(_AN_ACCEPTED_INSTANCE, {"id": 1, "note": None}, built), (
        "the marked field's own null is not declared"
    )
    for other in ("abcd", 7, [], {}, False):
        assert not harness.the_marker_declares(
            _AN_ACCEPTED_INSTANCE, {"id": 1, "note": other}, built
        ), other
    # and a null at a SECOND key beside it is two differences, not the derivation's witness
    assert not harness.the_marker_declares(_AN_ACCEPTED_INSTANCE, {"id": None, "note": None}, built)


def test_a_second_undeclared_widening_survives_beside_a_declared_null() -> None:
    """The exemption is per ROW and does not carry the pair.

    A class carrying the marker at ``note`` and dropping the document's ``minProperties``:
    the null row is declared and the ``minProperties`` row is not, so the pair still fails
    and names the one that is genuinely undeclared.  ``minProperties`` rather than a bound
    on the property, because ``refused_witnesses`` derives from the node's OWN keywords and
    a ``maxLength`` one level down is not one of them -- a document written to make that
    witness exist would be testing the derivation and not this.
    """
    document = {
        "type": "object",
        "properties": {"id": {"type": "integer"}, "note": {"type": "string"}},
        "required": ["id"],
        "minProperties": 2,
        "additionalProperties": False,
    }

    class Marked(BaseModel):
        model_config = {"extra": "forbid"}

        id: int
        note: Annotated[str | None, OmittedNotNull] = None

    result = check_refuses(document, Marked.model_validate, _AN_ACCEPTED_INSTANCE)
    assert result.outcome == "widened_undeclared", result
    assert {row[1] for row in result.undeclared} == {"minProperties"}, result.undeclared
    # the null row at the marked field is the one the marker declares, so it is not here
    assert not any(json.loads(row[0]).get("note", False) is None for row in result.undeclared), (
        result.undeclared
    )


def test_the_marker_declares_nothing_for_a_key_the_class_binds_to_no_field() -> None:
    """An ``extra`` carries no field, so it carries no marker, so it is not declared.

    A document with ``additionalProperties: true`` states a key the class does not declare;
    a ``None`` there is the payload's own value arriving at a position no field of ours
    describes, and ``the_marker_declares``' field lookup finds nothing to read. Asserted
    because the lookup's ``None`` answer is the conservative one and a reader should know
    it is deliberate rather than an oversight.
    """
    assert not harness.the_marker_declares({"a": 1}, {"a": 1, "b": None}, object())
