"""§5's ``allOf`` arms, graded as a function of one conjunct's KEY SET and nothing else.

``adcp-client-python-g4z``.  ``lower_composition`` was 1,438 lines and four concerns, and
the first of them -- *which arm does this conjunct reach* -- was stated four times inside
one ``while`` loop, once per arm, as inline set algebra.  Nothing could ask the question
on its own, so nothing graded it: the only evidence that the four conditions PARTITION a
conjunct's keys was that the emitted tree came out right.

``lower.composition.classify`` is that decision as one function over two sets, and this
file is what makes the separation real rather than cosmetic.  ``docs/plan/architecture.md``
§5's instruction is the standard these tests are written to: "a pure function over two
declarations lives in a module of its own, because purity is exactly the property that
makes it gradeable alone."  The classifier is not quite that -- it reads keyword NAMES and
not declarations -- but the property is the same one, and the test needs no bundle, no
:class:`codegen.compiler.Module` and no walk.

**What is asserted, in three clauses:**

1. every arm is REACHED by some key set, so no value of :class:`Conjunct` is dead;
2. the arms PARTITION, which is the claim the loop's four sequential ``if``\\ s make
   implicitly: over every subset of a keyword alphabet the bundle actually uses, each key
   set gets exactly one answer, and that answer is stable;
3. the two orderings that are load-bearing are the ones stated in the classifier's
   docstring, and each is asserted directly rather than described.
"""

from __future__ import annotations

import itertools

import pytest

from codegen.lower.composition import CONJ_COMPOSES, INLINE, Conjunct, classify

#: Every value a conjunct's key set can be classified as, so clause 1 can say the
#: enumeration has no dead member and a new arm reddens here until it is reached.
ARMS = frozenset(Conjunct)

#: The keyword alphabet clause 2 ranges over: the three families the classifier reads,
#: plus one keyword with no row at all.  Not the whole of draft-07, because the
#: classifier's answer is a function of these memberships and nothing else -- a keyword
#: outside every family behaves exactly as ``minLength`` does below, and the subsets of a
#: larger alphabet would be a bigger population of the same three facts.
ALPHABET = ("$ref", "type", "properties", "required", "additionalProperties", "allOf", "oneOf", "anyOf", "const", "enum", "minLength")


def test_the_four_inline_families_are_the_ones_the_classifier_reads() -> None:
    """The control for :data:`ALPHABET`: the sets it samples are the module's own.

    A fixture that drifts from the code it samples grades a population the code does not
    have.  ``INLINE`` and ``CONJ_COMPOSES`` are read by name, so a keyword joining either
    one reddens here and the alphabet is widened deliberately.
    """
    assert frozenset({"type", "properties", "required"}) == INLINE
    assert frozenset({"additionalProperties", "allOf"}) == CONJ_COMPOSES
    assert set(INLINE | CONJ_COMPOSES) <= set(ALPHABET)


@pytest.mark.parametrize(
    ("keys", "screen", "arm"),
    [
        # §5's ``$ref`` row at CONJ: the conjunct is a base.
        (frozenset({"$ref"}), frozenset(), Conjunct.BASE),
        # A reference AND something else -- the normalisation, not an arm.
        (frozenset({"$ref", "description"}), frozenset(), Conjunct.REFERENCE_WITH_SIBLINGS),
        (frozenset({"$ref", "minLength"}), frozenset(), Conjunct.REFERENCE_WITH_SIBLINGS),
        # An inline object: ``INLINE`` alone, and ``INLINE`` with the two CONJ composers.
        (frozenset({"type", "properties", "required"}), frozenset(), Conjunct.INLINE_OBJECT),
        (frozenset({"properties", "additionalProperties"}), frozenset(), Conjunct.INLINE_OBJECT),
        (frozenset({"allOf"}), frozenset(), Conjunct.INLINE_OBJECT),
        # The EMPTY key set is an inline object, because the empty set is a subset of
        # every set.  That is the arm an annotations-only conjunct reaches, and the arm's
        # own ``if keys:`` is what then makes it contribute nothing.
        (frozenset(), frozenset(), Conjunct.INLINE_OBJECT),
        # A rule source the TABLE gives the conjunct makes it an inline object: the
        # ``screen`` argument is why the answer is not a function of ``keys`` alone.
        (frozenset({"properties", "not"}), frozenset({"not"}), Conjunct.INLINE_OBJECT),
        (frozenset({"properties", "not"}), frozenset(), Conjunct.UNREADABLE),
        # A combinator of shapes.
        (frozenset({"oneOf"}), frozenset(), Conjunct.COMBINATOR),
        (frozenset({"anyOf"}), frozenset(), Conjunct.COMBINATOR),
        (frozenset({"oneOf", "minLength"}), frozenset(), Conjunct.COMBINATOR),
        # §5's ``enum`` row at CONJ.
        (frozenset({"const"}), frozenset(), Conjunct.VALUE_SET),
        (frozenset({"enum"}), frozenset(), Conjunct.VALUE_SET),
        (frozenset({"const", "enum"}), frozenset(), Conjunct.VALUE_SET),
        # Anything else refuses by name.
        (frozenset({"minLength"}), frozenset(), Conjunct.UNREADABLE),
        (frozenset({"enum", "minLength"}), frozenset(), Conjunct.UNREADABLE),
    ],
)
def test_each_key_set_reaches_the_arm_section_5_gives_it(
    keys: frozenset[str], screen: frozenset[str], arm: Conjunct
) -> None:
    """Clause 1, per arm, with the sentence of §5 that decides each in the table above."""
    assert classify(keys, screen) is arm


def test_every_arm_is_reached_so_no_member_of_the_enumeration_is_dead() -> None:
    """Clause 1's own control: the parametrisation above covers the whole enumeration.

    A member nothing reaches is either an arm the row no longer has or a case the table
    forgot, and both are findings.  Asserted off :class:`Conjunct` rather than off a
    count, so a sixth arm reddens this by NAME.
    """
    reached = {
        classify(keys, screen)
        for keys, screen in (
            (frozenset({"$ref"}), frozenset()),
            (frozenset({"$ref", "description"}), frozenset()),
            (frozenset({"properties"}), frozenset()),
            (frozenset({"oneOf"}), frozenset()),
            (frozenset({"const"}), frozenset()),
            (frozenset({"minLength"}), frozenset()),
        )
    }
    assert reached == ARMS, sorted(ARMS - reached)


def test_the_arms_partition_every_key_set_over_the_alphabet() -> None:
    """Clause 2: one answer per key set, and the answer is a function of the two sets.

    This is the claim ``lower_composition``'s four sequential ``if``\\ s make and could not
    state: that a conjunct reaches exactly one arm.  A classifier returning a single value
    makes it true by construction, which is the point -- so what is left to assert is that
    the function is TOTAL (no key set falls through to an exception) and DETERMINISTIC
    (the same pair gets the same answer, so no arm reads anything but its arguments).

    2,048 key sets over an 11-keyword alphabet, each asked with an empty screen and again
    with the whole alphabet as the screen.  The second screen is the interesting one: it
    makes every key a rule source, so the inline arm claims everything the normalisation
    does not -- which is the assertion below.
    """
    everything = frozenset(ALPHABET)
    for size in range(len(ALPHABET) + 1):
        for combination in itertools.combinations(ALPHABET, size):
            keys = frozenset(combination)
            bare, screened = classify(keys, frozenset()), classify(keys, everything)
            assert isinstance(bare, Conjunct) and isinstance(screened, Conjunct)
            assert classify(keys, frozenset()) is bare, keys
            # With every keyword a rule source, nothing is unreadable and nothing is a
            # combinator or a value set: the inline arm is asked first and claims the
            # whole conjunct.  The two reference answers are the normalisation's and come
            # before the inline test, so they are the only other answers left.
            if "$ref" in keys:
                assert screened is (
                    Conjunct.BASE if keys == {"$ref"} else Conjunct.REFERENCE_WITH_SIBLINGS
                ), keys
            else:
                assert screened is Conjunct.INLINE_OBJECT, keys


def test_the_inline_arm_is_asked_before_the_combinator_arm() -> None:
    """Clause 3, first ordering: ``properties`` beside ``oneOf`` is an INLINE OBJECT.

    The classifier's docstring states this and it is load-bearing: a conjunct whose
    ``oneOf`` the table reads as a presence clause is an inline object whose combinator is
    one of this node's RULES, and asking the combinator arm first would refuse it.  Both
    directions are asserted, because the fact is about the ORDER and not about either
    condition alone.
    """
    assert classify(frozenset({"properties", "oneOf"}), frozenset({"oneOf"})) is Conjunct.INLINE_OBJECT
    assert classify(frozenset({"properties", "oneOf"}), frozenset()) is Conjunct.COMBINATOR


def test_the_reference_normalisation_is_asked_before_every_arm() -> None:
    """Clause 3, second ordering: a ``$ref`` beside anything is the normalisation's.

    ``{"$ref", "allOf"}`` is a subset of ``INLINE | CONJ_COMPOSES``, so the inline arm
    would claim it if it were asked first -- and the conjunct's ``$ref`` would then be
    dropped in silence, which is the one thing §5's ``$ref`` row at CONJ exists to
    prevent.  ``{"$ref", "oneOf"}`` is the same fact against the combinator arm.
    """
    assert classify(frozenset({"$ref", "allOf"}), frozenset()) is Conjunct.REFERENCE_WITH_SIBLINGS
    assert classify(frozenset({"$ref", "oneOf"}), frozenset()) is Conjunct.REFERENCE_WITH_SIBLINGS
    assert classify(frozenset({"$ref", "enum"}), frozenset()) is Conjunct.REFERENCE_WITH_SIBLINGS
