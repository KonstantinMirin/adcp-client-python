"""``_constrains_nothing``'s two remaining arms, and the gates that keep them honest.

``_constrains_nothing`` folds a DOCUMENT fact that admits exactly what its absence
admits, so a model omitting it is not reported as dropping it.

**TWO ARMS SINCE ROW .3, and the deleted one is why the negative cases below stayed.**
``docs/plan/architecture.md`` §9 deletes every fold that undid a rewriting of the
delegated resolver once ``bundle.record`` is this package's own inliner.  The
``enum: [false, true]`` arm was one: the resolver wrote a finite ``type`` out as its
members while inlining, and the arm restored what the document had said.  The record
copies the document's ``type``, so the arm has nothing to undo -- and its own
docstring already said the shape it would still fire on, a document stating the PAIR
in its own text, must be COMPARED rather than folded.  So every case that used to fold
on ``enum`` is now a case that does not, and they are kept below as exactly that.

**Every test here that matters is a NEGATIVE one.** A fold is correct when it
matches its own shape and nothing else, and a fold that matches one real
constraint is invisible and permanent -- nobody re-reads a green ``missing``.  So
the folding cases are two lines and the refusing cases are the file.
"""

from __future__ import annotations

import pytest

from codegen.harness import _constrains_nothing

# --------------------------------------------------------------------------- #
# what folds
# --------------------------------------------------------------------------- #

FOLDS = [
    ("required", {"type": "object", "required": []}, "an empty required demands no key"),
]


@pytest.mark.parametrize(("keyword", "doc", "why"), FOLDS, ids=[f"{k}-{w}" for k, _, w in FOLDS])
def test_a_fact_that_admits_what_its_absence_admits_is_folded(
    keyword: str, doc: dict, why: str
) -> None:
    assert _constrains_nothing(keyword, doc) is True, why


# --------------------------------------------------------------------------- #
# what must NOT fold -- the whole correctness of the function
# --------------------------------------------------------------------------- #

REFUSES = [
    # enum: no shape of it folds any more.  The two that did were the resolver's
    # finite-type rewrite, and a document stating either in its own text states a fact
    # to compare -- which is what the first two cases now assert.
    (
        "enum",
        {"type": "boolean", "enum": [False, True]},
        "the document's own boolean pair is a FACT and is compared, not folded",
    ),
    (
        "enum",
        {"type": "boolean", "enum": [True, False]},
        "the same set the other way round, and compared for the same reason",
    ),
    ("enum", {"type": "boolean", "enum": [False]}, "one member PINS the value to false"),
    ("enum", {"type": "boolean", "enum": [True]}, "one member PINS the value to true"),
    (
        "enum",
        {"enum": [False, True]},
        "no declared type: a bare node admits more than two booleans",
    ),
    (
        "enum",
        {"type": ["boolean", "null"], "enum": [False, True]},
        "the document admits null and the enum forbids it, so the enum constrains",
    ),
    (
        "enum",
        {"type": "boolean", "enum": [False, True, None]},
        "a third member is not the boolean domain",
    ),
    (
        "enum",
        {"type": "string", "enum": [False, True]},
        "the declared type is not boolean, whatever the members are",
    ),
    (
        "enum",
        {"type": "integer", "enum": [0, 1]},
        "0 and 1 are not booleans: a truthiness test would fold this and must not",
    ),
    # required: emptiness is the gate, not listness.
    ("required", {"type": "object", "required": ["x"]}, "it demands a key"),
    ("required", {"type": "object", "required": ["x", "y"]}, "it demands two"),
    # a keyword this fold knows nothing about is never folded.
    ("minLength", {"type": "string", "minLength": 0}, "minLength is not this fold's keyword"),
    ("maxItems", {"type": "array", "maxItems": 0}, "nor is maxItems, even at 0"),
    ("type", {"type": "boolean"}, "nor is type itself"),
]


@pytest.mark.parametrize(
    ("keyword", "doc", "why"), REFUSES, ids=[f"{k}-{w[:28]}" for k, _, w in REFUSES]
)
def test_a_fact_that_constrains_is_never_folded(keyword: str, doc: dict, why: str) -> None:
    assert _constrains_nothing(keyword, doc) is False, why


# --------------------------------------------------------------------------- #
# the third shape: a default the enclosing node makes unreachable
# --------------------------------------------------------------------------- #
#: Section 5's ``default`` row drops a default on a REQUIRED property, and this is the
#: grading half of that decision.  Its gate is the one thing that can be wrong, and the
#: gate is not the keyword: a default on an OPTIONAL property is the case where a
#: default does something, so folding on the keyword alone would excuse every dropped
#: default in the bundle.  Both directions are here, over one node, so the pair differs
#: in the judged dimension and nothing else.
DEFAULTED = {"type": "boolean", "default": True}


def test_a_default_on_a_required_property_admits_what_its_absence_admits() -> None:
    """A required key is in every admitted instance, so its default never applies."""
    assert _constrains_nothing("default", DEFAULTED, required=True) is True


def test_a_default_on_an_optional_property_constrains_and_is_never_folded() -> None:
    """The same node, the other requiredness: here the key may be omitted and the
    default is the value the document then means, so a model dropping it is reported."""
    assert _constrains_nothing("default", DEFAULTED, required=False) is False
    assert _constrains_nothing("default", DEFAULTED) is False, "the default is the safe one"


def test_the_two_shapes_are_the_only_ones_and_the_population_is_not_empty() -> None:
    """The fold admits exactly two shapes, asserted by exhausting the compared set.

    A fold whose population nobody enumerated can grow silently when a keyword joins
    the compared set.  This reads the real set -- ``harness.compared_facts``, which is
    the table's rendered column -- rather than a copy of it, so a new keyword that this
    fold would swallow fails here.  The second shape is asked with ``required=True``,
    which is the only way to reach it, so a rule that folded on requiredness alone
    reddens in the last assertion.

    The deleted finite-type arm is asserted here too, over the whole compared set and
    not only over ``enum``: a document stating the boolean pair folds NOTHING now, in
    either keyword, so the fold cannot come back under another name.
    """
    from codegen.harness import compared_facts
    from codegen.keywords import Position

    facts = compared_facts(Position.PROP)
    assert facts, "empty keyword set: the assertion below would pass vacuously"
    folding = {
        kw for kw in facts if _constrains_nothing(kw, {"type": "boolean", "enum": [False, True]})
    }
    assert folding == set(), folding
    folding = {kw for kw in facts if _constrains_nothing(kw, {"type": "object", "required": []})}
    assert folding == {"required"}, folding
    folding = {kw for kw in facts if _constrains_nothing(kw, DEFAULTED, required=True)}
    assert folding == {"default"}, folding


# --------------------------------------------------------------------------- #
# the ADDED side's one fold: a model-only ``properties`` entry that is the empty schema
# --------------------------------------------------------------------------- #
#: §8's empty-schema clause, and the direction is why these cases are written in full.
#: ``_constrains_nothing`` above folds a DOCUMENT fact, so a mistake there reports a
#: model as faithful when it dropped something -- bad.  This one folds a MODEL fact, and
#: ``added`` is the half that can make a faithful SDK refuse valid traffic, so a mistake
#: here hides a model NARROWER than its document, which §2 never permits.  The negative
#: cases are therefore the file's own rule applied twice over.
VACUOUS = [
    ({}, "the empty schema, which IS true and constrains nothing"),
    (True, "``true``, which is the same subschema spelled the other way"),
    (
        {"title": "Id"},
        "what pydantic renders for a bare Any field: a title, which the TABLE's effect "
        "column makes an annotation, so §8's annotation clause already says a "
        "difference about it cannot change what a payload is accepted as",
    ),
    (
        {"title": "Id", "description": "text"},
        "two annotations and still no graded fact: the fold's predicate is "
        "grades_a_difference and not a count of keys",
    ),
]

NOT_VACUOUS = [
    (False, "``false`` admits NOTHING, which is the tightest a subschema can be"),
    ({"type": "string"}, "a type word is a fact, and the model stating one the document "
     "does not is the narrowing ``added`` exists to report"),
    ({"title": "Id", "type": "string"}, "one graded key beside an annotation is still a "
     "fact: a fold that counted annotations instead of grading keys would swallow it"),
    ({"enum": ["a"]}, "a value set the document does not state"),
    ({"const": "a"}, "a pin the document does not state"),
    ({"required": ["x"]}, "a nested presence demand"),
    ({"minLength": 1}, "a bound"),
    ({"format": "uri"}, "a format, which D5 lets select a type"),
    ({"properties": {"x": {}}}, "a nested object declaration: vacuous INSIDE is not "
     "vacuous here, because ``properties`` is structure the comparison descends"),
    ("not a schema", "not a mapping and not a boolean, so nothing says it is vacuous"),
]


@pytest.mark.parametrize(("entry", "why"), VACUOUS, ids=[str(e) for e, _ in VACUOUS])
def test_a_model_only_properties_entry_stating_no_graded_fact_is_folded(entry, why: str) -> None:
    from codegen.harness import _states_no_graded_fact

    assert _states_no_graded_fact(entry) is True, why


@pytest.mark.parametrize(("entry", "why"), NOT_VACUOUS, ids=[str(e) for e, _ in NOT_VACUOUS])
def test_a_model_only_properties_entry_stating_any_graded_fact_is_not_folded(
    entry, why: str
) -> None:
    from codegen.harness import _states_no_graded_fact

    assert _states_no_graded_fact(entry) is False, why


def test_no_graded_keyword_is_vacuous_on_its_own_over_the_whole_compared_set() -> None:
    """The fold's population, exhausted the way the one above is.

    A fold whose population nobody enumerated grows silently when a keyword joins the
    compared set, so this reads the real sets -- ``harness.compared_facts``, the table's
    rendered column, split by ``grades_a_difference`` -- rather than a copy of them, and
    asserts the fold's answer for each half.  A keyword that changed sides reddens here
    by name.

    **The two sets are NOT the same set, and §8 says so**: ``grades_a_difference`` "is
    asked at the three REPORTS and NOT of the compared set", because ``compared`` is the
    pair's evidence and an annotation IS looked for.  ``description`` is the measured
    case -- rendered at PROP, so compared, and an annotation, so a difference about it is
    not graded -- and an entry stating only a description therefore folds, correctly: the
    model declaring a property the document does not, and saying nothing about it but
    words, accepts exactly the payloads the document accepts.  Asserting the fold over
    the compared set alone would have called that a defect; asserting it over the graded
    half alone would never have met it.
    """
    from codegen.harness import _states_no_graded_fact, compared_facts, grades_a_difference
    from codegen.keywords import Position

    facts = compared_facts(Position.PROP)
    assert facts, "empty keyword set: the assertions below would pass vacuously"
    graded = {kw for kw in facts if grades_a_difference(kw, Position.PROP)}
    annotations = set(facts) - graded
    assert graded and annotations, (sorted(graded), sorted(annotations))
    assert {kw for kw in graded if _states_no_graded_fact({kw: "anything"})} == set()
    assert {kw for kw in annotations if not _states_no_graded_fact({kw: "anything"})} == set()
