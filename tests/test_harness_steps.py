"""The step: one constraint FACT, stepped at every position that states it.

``codegen/harness.py`` is the whole subject.  The emitted tree is not involved,
and these documents are written here rather than drawn from the bundle on
purpose: the behaviour under test is a property of the instrument, and a fixture
drawn from the population would make the test's reach a function of whatever the
population happens to hold this week.

The defect these grade: a document whose root and whose ``allOf`` conjunct both
state one keyword got one step site per POSITION, and stepping one of them left
the other stating the original bound.  The conjunction admitted no instance,
``hypothesis_jsonschema`` raised, and the site reported ``harness_error`` -- so it
cost a step and graded nothing.  D7 makes that restatement the normal case: where
a composition tightens an inherited field's requiredness the subclass redeclares
the field with the base's keywords, and a composed class's ``required`` is the
union of its own and every base's.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from codegen.harness import (
    Pair,
    check_pair,
    check_refuses,
    conforms,
    instance_location,
    steps,
)

DRAFT = "http://json-schema.org/draft-07/schema#"


def restating(keyword_at_root: bool = True) -> dict:
    """A root ``allOf`` whose conjunct restates every keyword the root states.

    Three keywords of three different shapes -- a presence list, a string length
    and a collection length -- because the three failed in three different
    exception shapes and a fixture with one of them would grade one third of the
    defect.
    """
    view = {
        "type": "object",
        "properties": {
            "label": {"type": "string", "minLength": 3},
            "tags": {"type": "array", "minItems": 2, "items": {"type": "string"}},
        },
        "required": ["label"],
    }
    doc: dict[str, Any] = {"$schema": DRAFT, "allOf": [dict(view)]}
    if keyword_at_root:
        doc.update(view)
    else:
        doc["type"] = "object"
    return doc


def stating_once() -> dict:
    """The same facts, stated at one position each.  The control document."""
    return {"$schema": DRAFT, **restating(keyword_at_root=True)["allOf"][0]}


class Faithful(BaseModel):
    """What the document says, said again in Python."""

    model_config = ConfigDict(extra="ignore")
    label: str = Field(min_length=3)
    tags: list[str] | None = Field(default=None, min_length=2)


class Wide(BaseModel):
    """A model that ACCEPTS what the document refuses on the restated keywords."""

    model_config = ConfigDict(extra="ignore")
    label: str | None = None  # drops both `minLength: 3` and `required`
    tags: list[str] | None = None  # drops `minItems: 2`


def by_fact(document: dict) -> dict[tuple[str, str, str], tuple[str, ...]]:
    """Each step's positions, keyed by the fact it steps.

    The instance location is part of the key: two steps can state the same
    keyword with the same rewrite at DIFFERENT locations, and a key without the
    location would silently drop one of them -- which is what a first draft of
    this helper did, and it made a test read a single ``if`` site as the whole
    answer.
    """
    return {
        (instance_location(s.pointer), s.keyword, s.describe): s.positions
        for s in steps(document)
    }


# --------------------------------------------------------------------------- #
# the defect
# --------------------------------------------------------------------------- #
def test_a_restated_keyword_is_one_step_over_both_positions() -> None:
    """The fix: one step per fact, holding every position that states it.

    Before, this document produced six sites -- three at the root and three in
    the conjunct -- and every one of them manufactured an unsatisfiable stepped
    document.  The positions are asserted, not just the count: a count would also
    be satisfied by a walk that stopped descending into ``allOf`` and so stopped
    seeing the conjunct's facts at all, which is a blindness and not a fix.
    """
    facts = by_fact(restating())
    assert facts == {
        ("/", "required", "required drops 'label'"): ("/", "/allOf/0"),
        ("/properties/label", "minLength", "minLength 3 -> at most 2"): (
            "/properties/label",
            "/allOf/0/properties/label",
        ),
        ("/properties/tags", "minItems", "minItems 2 -> maxItems 0"): (
            "/properties/tags",
            "/allOf/0/properties/tags",
        ),
    }


def test_the_restated_document_is_stepped_rather_than_erroring() -> None:
    """Every site is stepped, every site grades, and nothing reports an error.

    ``accept`` is the faithful model's plain ``model_validate``, so the
    ANNOTATIONS decide -- a refusal here is the model's and not a schema half's.
    """
    document = restating()
    for step in steps(document):
        stepped = step.materialize(document)
        assert conforms(stepped, {}) is not None, step.describe
        res = check_refuses(document, Faithful.model_validate, step, examples=20)
        assert res.harness == "", f"{step.describe}: {res.harness}"
        assert res.outcome == "pass", (step.describe, res)
        assert res.refused > 0  # the denominator is not zero
        assert res.accepted_invalid == 0
        assert step.keyword in res.violated, (step.describe, res.violated)


def test_a_model_that_accepts_a_restated_keywords_violation_is_caught() -> None:
    """The answer the fix must not silence.

    A restated keyword that is now STEPPED is also now GRADED, so a model wider
    than the document on it has to come back red.  Both arms run on the same
    document and the same steps, so a red here is a property of the model rather
    than of the fixture.
    """
    document = restating()
    all_steps = steps(document)
    assert len(all_steps) == 3  # noqa: PLR2004 -- the three facts above

    wide = [check_refuses(document, Wide.model_validate, s, examples=20) for s in all_steps]
    assert [r.outcome for r in wide] == ["model_accepted_invalid"] * 3
    for r in wide:
        assert r.accepted_invalid > 0
        assert r.counterexample  # the instance it should have refused

    faithful = [check_refuses(document, Faithful.model_validate, s, examples=20) for s in all_steps]
    assert [r.outcome for r in faithful] == ["pass"] * 3


def test_the_wide_model_is_red_at_the_pair_level_too() -> None:
    """And the pair's one verdict says so, since that is what a caller reads."""
    document = restating()
    wide = check_pair(
        Pair(name="wide", schema=document, model=Wide, accept=Wide.model_validate),
        max_steps=None,
    )
    assert wide.outcome == "refuses:model_accepted_invalid"

    faithful = check_pair(
        Pair(name="faithful", schema=document, model=Faithful, accept=Faithful.model_validate),
        max_steps=None,
    )
    assert [r.outcome for r in faithful.refuses] == ["pass"] * 3
    assert faithful.graded_instances > 0


# --------------------------------------------------------------------------- #
# what must not move
# --------------------------------------------------------------------------- #
def test_a_document_stating_each_keyword_once_steps_exactly_as_before() -> None:
    """The invariant: a fact stated at one position is one step at that position.

    Most of the bundle is this case, so this is the assertion that says the
    grouping took nothing away.  The site count, the pointers and the per-site
    outcomes are all compared against the restating document's, which states the
    same three facts -- so the two documents differ in the judged dimension
    (whether a fact is restated) and in nothing else.
    """
    once = stating_once()
    facts = by_fact(once)
    assert facts == {
        ("/", "required", "required drops 'label'"): ("/",),
        ("/properties/label", "minLength", "minLength 3 -> at most 2"): ("/properties/label",),
        ("/properties/tags", "minItems", "minItems 2 -> maxItems 0"): ("/properties/tags",),
    }
    assert [len(p) for p in facts.values()] == [1, 1, 1]

    for step in steps(once):
        res = check_refuses(once, Faithful.model_validate, step, examples=20)
        assert res.outcome == "pass", (step.describe, res)
        assert res.positions == (step.pointer,)


def test_two_different_bounds_at_one_location_stay_two_steps() -> None:
    """An intersection is not a restatement, and is not grouped.

    ``minLength: 3`` at the root and ``minLength: 5`` in a conjunct state two
    facts about one location; the effective constraint is the tighter one.  Their
    rewrites differ, so the admission rule -- same keyword, same location, same
    rewrite -- keeps them apart, and a group that merged them would have to pick
    one rewrite to apply at a position the other describes.  Stepping either
    alone can be unsatisfiable, which is the residual this fix does not claim to
    fix; what is asserted here is that it is REPORTED, never passed.
    """
    document = {
        "$schema": DRAFT,
        "type": "object",
        "required": ["label"],
        "properties": {"label": {"type": "string", "minLength": 3}},
        "allOf": [{"properties": {"label": {"type": "string", "minLength": 5}}}],
    }
    length = [s for s in steps(document) if s.keyword == "minLength"]
    assert sorted(s.describe for s in length) == [
        "minLength 3 -> at most 2",
        "minLength 5 -> at most 4",
    ]
    assert all(len(s.positions) == 1 for s in length)

    outcomes = {
        s.describe: check_refuses(document, Faithful.model_validate, s, examples=10).outcome
        for s in length
    }
    assert "pass" not in {o for d, o in outcomes.items() if d == "minLength 3 -> at most 2"}


def test_a_step_under_an_if_or_a_not_is_not_grouped_with_the_fact_above_it() -> None:
    """``if`` and ``not`` are absent from the applicator table deliberately.

    A step beneath an ``if`` makes the condition FAIL, which releases ``then``
    rather than pushing the instance out of the document, and a step beneath a
    ``not`` is satisfied by the negation.  Neither restates the fact above it, so
    grouping either would rewrite a position whose meaning is inverted or
    conditional and claim the document refuses what it accepts.
    """
    assert instance_location("/allOf/0/properties/x") == "/properties/x"
    assert instance_location("/anyOf/2/oneOf/1/properties/x") == "/properties/x"
    assert instance_location("/then/properties/x") == "/properties/x"
    assert instance_location("/else/properties/x") == "/properties/x"
    assert instance_location("/if/properties/x") == "/if/properties/x"
    assert instance_location("/not/properties/x") == "/not/properties/x"
    # and the index is KEPT under an `if`, so two conjuncts' conditions are two
    # facts -- measured on `core/creative-approval-scope.json`, which states one
    # `required` inside `/allOf/0/if` and another inside `/allOf/1/if`
    assert instance_location("/allOf/0/if/properties/x") == "/allOf/0/if/properties/x"
    assert instance_location("/allOf/1/if/properties/x") == "/allOf/1/if/properties/x"
    assert instance_location("/properties/allOf") == "/properties/allOf"  # a property so NAMED
    assert instance_location("/$defs/Thing/properties/x") == "/$defs/Thing/properties/x"

    document = {
        "$schema": DRAFT,
        "type": "object",
        "required": ["label"],
        "properties": {"label": {"type": "string", "minLength": 3}},
        "if": {"properties": {"label": {"type": "string", "minLength": 3}}},
        "then": {"properties": {"label": {"type": "string", "minLength": 3}}},
    }
    facts = by_fact(document)
    at_label = facts[("/properties/label", "minLength", "minLength 3 -> at most 2")]
    assert at_label == ("/properties/label", "/then/properties/label")
    assert facts[("/if/properties/label", "minLength", "minLength 3 -> at most 2")] == (
        "/if/properties/label",
    )


def test_two_conjuncts_conditions_are_two_facts_and_not_one() -> None:
    """The over-grouping the first draft of this had, on the document that found it.

    ``core/creative-approval-scope.json`` states ``required`` inside two
    conjuncts' ``if`` conditions.  Dropping the ``allOf`` index while keeping the
    ``if`` hop collapsed them to one location and so to one step over two
    positions, which claims the two conditions are one fact about the instance.
    They are two, and a step rewriting both says the document demands something
    it does not.
    """
    document = {
        "$schema": DRAFT,
        "type": "object",
        "properties": {"kind": {"type": "string"}, "label": {"type": "string"}},
        "allOf": [
            {"if": {"required": ["kind"]}, "then": {"required": ["label"]}},
            {"if": {"required": ["label"]}, "then": {"required": ["kind"]}},
        ],
    }
    conditions = sorted(
        s.positions[0] for s in steps(document) if "/if" in s.positions[0]
    )
    assert conditions == ["/allOf/0/if", "/allOf/1/if"]
    assert all(len(s.positions) == 1 for s in steps(document) if "/if" in s.positions[0])


def test_a_union_branch_restating_a_root_fact_is_stepped_too() -> None:
    """Step 5's shape: a root fact restated in every branch of a union.

    Stepping the root alone left both branches demanding the original bound, so
    the stepped document admitted nothing -- the same defect through ``anyOf``
    rather than ``allOf``.  Grouping across a branch hop stays correct because the
    ORIGINAL document decides whether an instance violates anything, so a group
    that pushes out only some branches reports a fired control and never a pass.
    """
    branch = {
        "type": "object",
        "properties": {"label": {"type": "string", "minLength": 3}},
        "required": ["label"],
    }
    document = {
        "$schema": DRAFT,
        "type": "object",
        "properties": {"label": {"type": "string", "minLength": 3}},
        "required": ["label"],
        "anyOf": [dict(branch), {**branch, "properties": {**branch["properties"], "k": {}}}],
    }
    positions = by_fact(document)[("/properties/label", "minLength", "minLength 3 -> at most 2")]
    assert positions == (
        "/properties/label",
        "/anyOf/0/properties/label",
        "/anyOf/1/properties/label",
    )
    (step,) = [s for s in steps(document) if s.keyword == "minLength"]
    res = check_refuses(document, Faithful.model_validate, step, examples=20)
    assert res.harness == ""
    assert res.outcome == "pass"
    assert res.refused > 0


# --------------------------------------------------------------------------- #
# a site the check cannot step is reported, never passed
# --------------------------------------------------------------------------- #
def test_an_unsteppable_site_is_reported_rather_than_passed() -> None:
    """§6's rule one level down.

    A keyword stepped against a DIFFERENT keyword in a conjunct is not a
    restatement -- here a ``maxLength`` stepped one character up against a
    conjunct's ``const`` -- and no grouping fixes it, because the two positions
    state different facts.  What the rule requires is that such a site is
    REPORTED: ``harness_error`` is not in ``PairReport``'s admitted set, so the
    pair's verdict is a refusal and the site contributes nothing to the
    denominator.  A reader is owed the fact; what is forbidden is a green mark.
    """
    document = {
        "$schema": DRAFT,
        "type": "object",
        "required": ["label"],
        "properties": {"label": {"type": "string", "maxLength": 4}},
        "allOf": [{"properties": {"label": {"const": "abcd"}}}],
    }
    (step,) = [s for s in steps(document) if s.keyword == "maxLength"]
    res = check_refuses(document, Faithful.model_validate, step, examples=10)
    assert res.outcome != "pass"
    assert res.outcome == "harness_error"
    assert res.harness
    assert res.refused + res.accepted_invalid == 0  # nothing reached the model
    # **And it is NOT `no_instrument`**, which is the gate between the two things an
    # empty witness means: a NAMED keyword contradicts the step here, so the harness
    # has a reason it could act on and §6's rule stands.  An empty `collides` is the
    # other case -- nothing forbids the witness and the strategy still produced none
    # -- and that is the generator's, recorded by `PairReport.no_instrument`.
    assert res.collides == ("/allOf/0/properties/label:const",), res.collides
    assert not res.undrawable, res.undrawable

    rep = check_pair(
        Pair(name="unsteppable", schema=document, model=Faithful, accept=Faithful.model_validate),
        max_steps=None,
    )
    assert rep.outcome.startswith("refuses:harness_error")


def test_a_group_that_admits_nothing_is_retried_one_position_at_a_time() -> None:
    """The obligation is the KEYWORD at a location, not the size of the group.

    Two ``oneOf`` branches telling themselves apart by a discriminating ``const``
    both state ``required: ['kind', 'label']``, so each member is one step over
    two positions.  Dropping ``kind`` at BOTH positions forbids it in both
    branches, an instance without it then matches neither, and the root ``oneOf``
    has nothing to pick -- the group admits nothing.  Dropping it at ONE leaves
    the other branch requiring it, so exactly one branch can match and the step
    grades.  Measured first on
    ``core/inventory-list-application.json#``, the only pair of the emitted 448
    that reaches this: the group was `harness_error` with a zero denominator and
    refused an otherwise-green pair over a witness the harness had chosen badly.

    Both members run on the one document, so the two arms differ in the judged
    dimension -- whether the whole group admits anything -- and in nothing else.
    ``stepped_at`` is the evidence: empty where the group itself bit, and the one
    position where it did not.  A denominator alone would not separate them.
    """
    branch = {
        "type": "object",
        "properties": {"kind": {"const": "a"}, "label": {"type": "string"}},
        "required": ["kind", "label"],
        "additionalProperties": False,
    }
    document = {
        "$schema": DRAFT,
        "type": "object",
        "oneOf": [
            dict(branch),
            {**branch, "properties": {"kind": {"const": "b"}, "label": {"type": "string"}}},
        ],
    }
    by_member = {
        s.describe.split("'")[1]: s for s in steps(document) if s.keyword == "required"
    }
    assert sorted(by_member) == ["kind", "label"]
    assert all(len(s.positions) == 2 for s in by_member.values())  # noqa: PLR2004

    results = {
        member: check_refuses(document, lambda _i: None, step, examples=20)
        for member, step in by_member.items()
    }

    # `label` is pushed out of both branches at once and the discriminator still
    # tells them apart, so the group itself bites and nothing is narrowed.
    whole = results["label"]
    assert whole.harness == "", whole.harness
    assert whole.refused + whole.accepted_invalid > 0
    assert whole.stepped_at == ""
    assert whole.positions == ("/oneOf/0", "/oneOf/1")

    # `kind` IS the discriminator, so the group admits nothing and one position
    # alone is what grades it.  The fact is still stated at both.
    retried = results["kind"]
    assert retried.harness == "", retried.harness
    assert retried.refused + retried.accepted_invalid > 0
    assert retried.stepped_at in ("/oneOf/0", "/oneOf/1")
    assert retried.positions == ("/oneOf/0", "/oneOf/1")
    assert "required" in retried.violated  # the ORIGINAL refuses on the stepped keyword

    rep = check_pair(
        Pair(
            name="retried",
            schema=document,
            model=Faithful,
            accept=lambda _i: None,
        ),
        max_steps=None,
    )
    assert [r.outcome for r in rep.refuses if r.outcome == "harness_error"] == []


# --------------------------------------------------------------------------- #
# the mechanics the group needs
# --------------------------------------------------------------------------- #
def test_a_required_step_drops_the_key_at_every_position() -> None:
    """A ``required`` step over two positions removes the key from both lists.

    An earlier draft of this claimed the FORCE/REWRITE ORDER was load-bearing
    here -- force one position, rewrite it, force the second and the second
    forcing puts the key back.  Perturbing the order reddened nothing, and the
    claim is wrong: forcing adds a name to the ``required`` of each PROPERTY HOP
    on the way DOWN to a position, and every position in one group addresses the
    node itself, so no position in the group descends through the key the step
    drops.  What this grades is the rewrite reaching both lists.
    """
    document = restating()
    (step,) = [s for s in steps(document) if s.keyword == "required"]
    stepped = step.materialize(document)
    assert "label" not in stepped.get("required", [])
    assert "label" not in stepped["allOf"][0].get("required", [])
    assert stepped["not"] == {"required": ["label"]}
    assert stepped["allOf"][0]["not"] == {"required": ["label"]}
    assert conforms(stepped, {"tags": ["a", "b"]}) is True


def test_forcing_every_position_leaves_no_example_ungraded() -> None:
    """Why ``materialize`` forces EVERY position and not only the reported one.

    Neither union branch requires ``label`` and the root states nothing about its
    length, so forcing the first position alone makes the key mandatory in that
    branch only: the generator satisfies the OTHER branch, omits the key, and
    those examples grade nothing.  Measured 8 of 25 in that state.

    The verdict is ``pass`` either way -- one graded example is enough for it --
    so this asserts the CONTROL COUNT, which is the thing that moves.  It is a
    property and not a blessed number: every instance of the stepped document
    carries ``label`` at two characters or fewer, and the original refuses that in
    both branches, so no example can fail to violate.
    """
    branch = {"properties": {"label": {"type": "string", "minLength": 3}}}
    document = {
        "$schema": DRAFT,
        "type": "object",
        "properties": {"label": {"type": "string"}, "k": {"type": "string"}},
        "anyOf": [dict(branch), {**branch, "required": ["k"]}],
    }
    (step,) = [s for s in steps(document) if s.keyword == "minLength"]
    assert step.positions == ("/anyOf/0/properties/label", "/anyOf/1/properties/label")

    res = check_refuses(document, Faithful.model_validate, step, examples=25)
    assert res.outcome == "pass"
    assert res.control_fired == 0
    assert res.refused == res.examples


def test_materialize_leaves_the_original_document_untouched() -> None:
    """The original is what decides a violation, so a step may not write on it."""
    document = restating()
    before = repr(document)
    for step in steps(document):
        step.materialize(document)
        step.materialize(document, force=False)
    assert repr(document) == before


@pytest.mark.parametrize("force", [True, False])
def test_an_unforced_step_still_rewrites_every_position(force: bool) -> None:
    """``force=False`` exists for a measurement, and it steps the same positions."""
    document = restating()
    (step,) = [s for s in steps(document) if s.keyword == "minLength"]
    stepped = step.materialize(document, force=force)
    for node in (stepped["properties"]["label"], stepped["allOf"][0]["properties"]["label"]):
        assert node["maxLength"] == 2  # noqa: PLR2004 -- minLength 3 -> at most 2
        assert "minLength" not in node or node["minLength"] == 0


def test_a_fact_stated_twice_at_one_position_is_one_step() -> None:
    """The degenerate case: a conjunct that is a copy of the root, with no facts
    of its own anywhere else.  The group is the two positions and the stepped
    document is satisfiable, which is the whole of the fix stated once."""
    document = {
        "$schema": DRAFT,
        "type": "array",
        "minItems": 2,
        "items": {"type": "string"},
        "allOf": [{"minItems": 2}],
    }
    (step,) = steps(document)
    assert step.positions == ("/", "/allOf/0")
    stepped = step.materialize(document)
    assert stepped["maxItems"] == 0
    assert stepped["allOf"][0]["maxItems"] == 0
    assert conforms(stepped, []) is True
    assert conforms(document, []) is False


def test_the_wide_models_arms_differ_in_the_judged_dimension() -> None:
    """The two models above are compared on the restated keywords and nothing
    else, so a red from ``Wide`` cannot come from some other difference."""
    assert set(Faithful.model_fields) == set(Wide.model_fields)
    with pytest.raises(ValidationError):
        Faithful.model_validate({"label": "ab"})
    assert Wide.model_validate({"label": "ab"}).label == "ab"
    assert Wide.model_validate({}).label is None
