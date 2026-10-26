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
