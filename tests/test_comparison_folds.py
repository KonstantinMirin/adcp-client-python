"""The fifth resolver canonicalization, and the gates that keep it honest.

``_constrains_nothing`` folds a DOCUMENT fact that admits exactly what its absence
admits, so a model omitting it is not reported as dropping it.  Section 6 of the
plan carries four such folds and this is the fifth.

**Every test here that matters is a NEGATIVE one.** A fold is correct when it
matches its own shape and nothing else, and a fold that matches one real
constraint is invisible and permanent -- nobody re-reads a green ``missing``.  So
the folding cases are three lines and the refusing cases are the file.
"""

from __future__ import annotations

import pytest

from codegen.harness import _constrains_nothing

# --------------------------------------------------------------------------- #
# what folds
# --------------------------------------------------------------------------- #

FOLDS = [
    ("required", {"type": "object", "required": []}, "an empty required demands no key"),
    (
        "enum",
        {"type": "boolean", "enum": [False, True]},
        "both booleans is the whole boolean domain",
    ),
    (
        "enum",
        {"type": "boolean", "enum": [True, False]},
        "the same set, written the other way round",
    ),
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
    # enum: the SET is the gate, not the keyword and not the length.
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


def test_the_three_shapes_are_the_only_ones_and_the_population_is_not_empty() -> None:
    """The fold admits exactly three shapes, asserted by exhausting FACTS.

    A fold whose population nobody enumerated can grow silently when a keyword is
    added to ``FACTS``.  This reads the real keyword list rather than a copy of it,
    so a new keyword that this fold would swallow fails here.  The third shape is
    asked with ``required=True``, which is the only way to reach it, and the first
    two are asked at the default -- so a rule that folded on requiredness alone
    reddens in the third assertion.
    """
    from codegen.harness import FACTS

    assert FACTS, "empty keyword list: the assertion below would pass vacuously"
    folding = {kw for kw in FACTS if _constrains_nothing(kw, {"type": "boolean", "enum": [False, True]})}
    assert folding == {"enum"}, folding
    folding = {kw for kw in FACTS if _constrains_nothing(kw, {"type": "object", "required": []})}
    assert folding == {"required"}, folding
    folding = {kw for kw in FACTS if _constrains_nothing(kw, DEFAULTED, required=True)}
    assert folding == {"default"}, folding
