"""§5's ``$ref`` row at CONJ, read at the three SIBLINGS of a conjunct list.

``adcp-client-python-g4z``.  The row's answer for a sibling of an ``allOf`` is "the target
is this node's own TYPE, and the other conjuncts and the ``allOf``'s siblings constrain
it" -- and that answer needs a type to constrain.  Where every conjunct is a CLASS base
there is none, and the three keywords that reach that case were three consecutive ``if``
blocks inside ``lower_composition``, each with its own measured population and each
reachable only by compiling a document that happened to have the shape.

Two of the three have a population of **0** over the 1,054 portable documents, which is
exactly why they want a test of their own: the row that wrote them wrote them so the FIRST
such document is loud rather than emitted with the keyword dropped, and a screen with no
population and no test is a screen nothing holds.  ``lower.composition
.a_sibling_with_no_type_to_constrain`` is the one function and this file is the population
it does not have in the bundle.

What is asserted per arm is the REFUSAL's own information -- the keyword it names and the
pointer it names it at -- because that is what a lane reads and what the three arms differ
in.  The function is pure over its six arguments, so none of this needs a bundle, a module
or a walk.
"""

from __future__ import annotations

from codegen.keywords import Position
from codegen.lower.composition import a_sibling_with_no_type_to_constrain
from codegen.refusal import Refusal


def screen(**kw):
    """The function with the arguments that mean "nothing to screen", overridden per test."""
    return a_sibling_with_no_type_to_constrain(
        contains=kw.pop("contains", None),
        conjunct_values=kw.pop("conjunct_values", ()),
        facts=kw.pop("facts", {}),
        conjoined=kw.pop("conjoined", ()),
        pointer=kw.pop("pointer", "/properties/x"),
        position=kw.pop("position", Position.PROP),
        **kw,
    )


def test_a_node_with_no_sibling_at_all_passes_the_screen() -> None:
    """The control: the screen answers ``None`` where there is nothing to say.

    A screen that refused something here would refuse every composing node in the bundle,
    which is the direction a guard over an empty population fails in.
    """
    assert screen() is None


def test_a_contains_beside_conjuncts_that_are_all_bases_refuses_on_contains() -> None:
    """The arm with a population: ``contains`` quantifies over the MEMBERS of a list.

    This node's type is a composed class, so the predicate has nothing to range over --
    and dropping it would lose the document's own existential, which is a widening with no
    declaration to be made as.  Reported at the composing node's pointer and at CONJ,
    because the sibling is the node's and the row is the conjunct list's.
    """
    out = screen(contains={"const": 1})
    assert isinstance(out, Refusal)
    assert out.keyword == "contains"


def test_a_contains_beside_a_class_conjunct_is_not_this_screens_business() -> None:
    """The same sibling with a non-empty ``conjoined``: §5's row has a type to constrain.

    ``conjoined`` is the list of ``$ref`` conjuncts whose target IS a class, so a non-empty
    one means the node declares a class of its own and the sibling reaches the row's
    written half.  Asserted because the screen's whole condition is ``not conjoined``, and
    a screen that ignored it would refuse the composing nodes the compiler emits today.
    """
    assert screen(contains={"const": 1}, conjoined=("a base",)) is None


def test_a_conjunct_that_is_a_value_set_refuses_at_its_own_pointer_and_keyword() -> None:
    """The second arm, population 0: an instance of a class is not a member of a vocabulary.

    The pointer is the CONJUNCT's and not the composing node's -- the keyword is on the
    conjunct, so §6's rule that a document is refused at the innermost node carrying the
    keyword puts the report there.  And the keyword is read off the conjunct's own
    declaration rather than spelled, so a conjunct stating ``const`` reports ``const``.
    """
    out = screen(conjunct_values=[("/allOf/2", {"enum": ["a", "b"]})])
    assert isinstance(out, Refusal)
    assert out.keyword == "enum"
    assert out.pointer == "/allOf/2"

    pinned = screen(conjunct_values=[("/allOf/3", {"const": "a"})])
    assert isinstance(pinned, Refusal)
    assert pinned.keyword == "const"
    assert pinned.pointer == "/allOf/3"


def test_a_bound_beside_conjuncts_that_are_all_bases_refuses_on_the_first_bound() -> None:
    """The third arm, population 0: a bound on a string or a list says nothing about a class.

    The keyword named is ``min(facts)``, so a node stating several reports the first in
    sorted order and the sentence lists them all -- which is what keeps the report a
    function of the document rather than of a dict's iteration order.
    """
    out = screen(facts={"minLength": 1, "maxLength": 9})
    assert isinstance(out, Refusal)
    assert out.keyword == "maxLength"
    assert "['maxLength', 'minLength']" in out.detail


def test_the_three_arms_are_asked_in_the_order_the_row_reads_them() -> None:
    """A node with all three siblings reports the ``contains``, which is the arm with a population.

    The order is the one ``lower_composition`` had and is kept rather than chosen: a
    document carrying two of these is carrying two unwritten cases, and reporting the one
    that has ever been measured is the more useful sentence.  Asserted so that reordering
    the arms is a visible change and not a silent one.
    """
    out = screen(
        contains={"const": 1},
        conjunct_values=[("/allOf/2", {"enum": ["a"]})],
        facts={"minItems": 1},
    )
    assert isinstance(out, Refusal) and out.keyword == "contains"
