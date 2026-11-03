"""§2's intersection asked of ONE PROPERTY KEY, graded with two declarations and nothing else.

``adcp-client-python-g4z``.  The merge of an own property declaration against an inherited
one was the deepest nesting in ``lower_composition``'s 1,438 lines -- five arms, each with
its own measured prose, reached only by compiling a document that happened to have the
shape.  ``docs/plan/architecture.md`` §5's test of a boundary is "what a reader opens", and
its reason for separating a pure rule is the one this file is the evidence for: "purity is
exactly the property that makes it gradeable alone".

So ``codegen/lower/inherited.py`` is the module and this is the grading.  Every test below
builds the two declarations as literals and asserts which arm the pair takes.  No bundle,
no emitted tree, no :class:`codegen.compiler.Module` -- the stub below is the whole of the
context the rule touches, which is itself the claim that the rule is pure over the two
declarations.

**The five arms, and the sentence of ``docs/plan/rebuild-plan.md`` that decides each:**

=================================  ====================================================
the pair                           what the subclass states
=================================  ====================================================
no base declares the key           the composing node's own declaration, untouched
the restatement NARROWS            §2's intersection of the two
it is newly REQUIRED               §2's requiredness overlay -- the base's type, no
                                   default
same instance, different READER    the intersection, for §6's description authority
it adds nothing                    nothing: the field is inherited and no line written
neither matches nor narrows        a REFUSAL naming the keyword the two disagree at,
                                   which §5(b) decides and this compiler does not write
=================================  ====================================================
"""

from __future__ import annotations

from codegen import ir
from codegen.lower import inherited as inherited_row
from codegen.refusal import Refusal


class _NoReferences:
    """The whole of the context :func:`inherited_row.merge` touches, for a pair with no ``$ref``.

    ``resolve_node`` is the one member the rule reads, and every declaration in this file
    is written inline -- so it answers ``None`` for every URI, which is
    :func:`codegen.intersect._dereferenced`'s "leave the declaration as written".  A stub
    and not a :class:`codegen.compiler.Module`, because needing one would mean the rule is
    not pure over its two declarations and this file's whole claim would be false.
    """

    @staticmethod
    def resolve_node(uri: str) -> dict | None:
        return None


MOD = _NoReferences()


def merge(local, inherited, **kw):
    """:func:`inherited_row.merge` with the arguments every test here passes the same way."""
    return inherited_row.merge(
        local,
        inherited,
        at={key: f"/properties/{key}" for key in local},
        pointer="",
        required=kw.pop("required", frozenset()),
        inherited_required=kw.pop("inherited_required", frozenset()),
        inherited_fields=kw.pop("inherited_fields", {}),
        inherited_from=kw.pop("inherited_from", {}),
        mod=kw.pop("mod", MOD),
        **kw,
    )


def test_a_key_no_base_declares_is_the_composing_nodes_own_declaration() -> None:
    """The first arm, and the cheap one: there is nothing to merge.

    The declaration is passed through by IDENTITY and not copied, which is what the field
    builder is then handed -- so a reader can see that this arm neither drops nor adds a
    keyword.
    """
    stating = {"type": "string", "minLength": 2}
    out = merge({"a": stating}, {})
    assert out.own == {"a": stating}
    assert out.own["a"] is stating
    assert out.reuse == {} and out.distinct == set()


def test_a_narrowing_restatement_is_stated_as_the_intersection_of_the_two() -> None:
    """The second arm: §2's "the field carries the INTERSECTION".

    The child's value wins at a keyword both state (D7, "a bound is the tighter one") and
    the base's survives at a keyword only the base states -- which is the half a
    restatement lowered ALONE would drop, and the shadow the whole rule exists to make
    unspellable.
    """
    child = {"type": "integer", "maximum": 5}
    base = {"type": "integer", "maximum": 9, "minimum": 1}
    out = merge({"n": child}, {"n": base})
    # Written as the two INPUTS composed rather than as the answer re-typed, which states
    # §2's rule instead of restating its result: the base's keywords, overridden by the
    # child's wherever both state one.
    assert out.own == {"n": base | child}
    assert out.reuse == {}


def test_a_restatement_that_neither_matches_nor_narrows_refuses_at_the_shared_keyword() -> None:
    """The fifth arm: §5(b)'s row, which this compiler reports rather than widens.

    What is asserted is the REFUSAL's own information, because that is what the arm exists
    to produce and the sentence is what a lane reads: the keyword is the first the two
    declarations SHARE and disagree at, and the pointer is the PROPERTY's and not the
    composing node's.
    """
    out = merge(
        {"n": {"type": "integer", "maximum": 20}},
        {"n": {"type": "integer", "maximum": 9}},
    )
    assert isinstance(out, Refusal)
    assert out.keyword == "maximum"
    assert out.pointer == "/properties/n"
    assert "neither matches nor narrows" in out.detail


def test_a_keyword_only_the_base_states_is_never_the_obstruction() -> None:
    """The second arm again, at the shape that made silence stop being a loosening.

    Under ``allOf`` the base's declaration applies wherever the restatement is quiet, so a
    restatement naming FEWER keywords states no less about the instance.  Asserted here
    rather than described because the opposite reading refuses a document §2 decides: the
    pair below would be "unordered" under it.
    """
    out = merge(
        {"n": {"type": "integer", "maximum": 5}},
        {"n": {"type": "integer", "maximum": 9, "exclusiveMinimum": 0}},
    )
    assert not isinstance(out, Refusal)
    assert out.own["n"]["exclusiveMinimum"] == 0


def test_a_restatement_that_adds_nothing_leaves_the_field_inherited() -> None:
    """The fourth arm: no line, no shadow.

    The key is absent from all three maps, which is what makes the class inherit the
    base's field rather than redeclare it -- and a redeclaration of an inherited field is
    what this module's own rule calls a build failure.
    """
    base = {"type": "string", "minLength": 2}
    out = merge({"a": dict(base)}, {"a": base})
    assert out.own == {} and out.reuse == {} and out.distinct == set()


def test_a_restatement_differing_only_in_what_a_READER_sees_states_the_field() -> None:
    """The third arm: §6's description-authority rule.

    "A document's own declaration governs the annotation at its own pointer", so a
    restatement saying the same thing about the instance and a different thing to the
    reader is stated by the subclass -- with the INTERSECTION as its content, because the
    restatement alone would drop whatever the base states and this one is silent about.
    """
    child = {"type": "string", "description": "the document's own"}
    base = {"type": "string", "minLength": 2, "description": "the base's"}
    out = merge({"a": child}, {"a": base})
    # The base's ``minLength`` survives and the child's ``description`` wins, which is
    # the same composition as the narrowing arm above and is written the same way.
    assert out.own == {"a": base | child}


def test_a_restatement_that_only_annotates_reuses_the_bases_DECIDED_field() -> None:
    """The third arm's EMPTY half, which is the one that reaches ``_reused``.

    A restatement with no constraining content of its own says nothing about the instance,
    so the field is the base's DECIDED one wearing this document's annotation -- re-deciding
    it would declare the base's nested classes again, in this module, at a pointer this
    document does not have.  ``inherited_from`` empty is the case
    :func:`inherited_row._reused` answers without touching the module at all: the base's
    field is this document's own class's, so there is no import to place.
    """
    held = ir.Field(name="a", wire="a", type=ir.TypeRef("str"), required=True)
    out = merge(
        {"a": {"description": "the document's own"}},
        {"a": {"type": "string", "description": "the base's"}},
        inherited_fields={"a": held},
    )
    assert out.reuse == {"a": held}
    assert out.own["a"]["type"] == "string"
    assert out.own["a"]["description"] == "the document's own"


def test_a_requiredness_the_base_does_not_have_is_a_NARROWING() -> None:
    """The second arm through its other door: ``required`` moved and nothing else.

    Left inherited, the field keeps the base's optionality while the composing document's
    own ``required`` names it -- so the class accepts a payload the document refuses and
    renders a ``default: None`` the document does not state.  The restatement here is
    EQUAL to the base, so ``_restatement`` is false and the requiredness is the whole of
    what narrows.
    """
    held = ir.Field(name="a", wire="a", type=ir.TypeRef("str"), required=True)
    out = merge(
        {"a": {"type": "string"}},
        {"a": {"type": "string"}},
        required=frozenset({"a"}),
        inherited_required=frozenset(),
        inherited_fields={"a": held},
    )
    assert out.own["a"] == {"type": "string"}
    # The intersection is the base's content, so the field is the base's DECIDED one and
    # not a second decision of the base's node (§2's "the base's type and no default").
    assert out.reuse == {"a": held}


def test_the_requiredness_OVERLAY_reaches_a_key_no_view_declares() -> None:
    """§2's only permitted redeclaration, and the arm the per-key loop cannot reach.

    ``{"required": ["a"]}`` and nothing more: no view of this document declares ``a``, so
    the loop over ``local`` never sees the key and the overlay is what states the field.
    Asserted together with the loop's own half above, because the two are one decision
    about one key and splitting them is how the optional-field defect survived in one of
    them while the other was fixed.
    """
    held = ir.Field(name="a", wire="a", type=ir.TypeRef("str"), required=True)
    out = merge(
        {},
        {"a": {"type": "string"}},
        required=frozenset({"a"}),
        inherited_required=frozenset(),
        inherited_fields={"a": held},
    )
    assert out.reuse == {"a": held}
    assert out.own == {"a": {"type": "string"}}


def test_an_overlay_for_a_required_name_no_view_declares_writes_nothing() -> None:
    """The overlay's own screen: a name neither the node nor a base declares is skipped.

    The field builder refuses such a name BY NAME, which is the accurate answer and is
    already written -- so this arm must not write a field for it, and the assertion is
    that all three maps stay empty.
    """
    out = merge({}, {}, required=frozenset({"ghost"}), inherited_required=frozenset())
    assert out.own == {} and out.reuse == {} and out.distinct == set()


def test_a_uniqueItems_taken_from_the_BASE_is_recorded_as_a_rule_the_class_inherits() -> None:
    """The ``distinct`` map: the keyword the intersection merged back in.

    A bare ``{"contains": ...}`` restatement over an array base intersects to the base's
    ``type``, ``items`` AND ``uniqueItems`` -- and deciding that merged declaration FRESH
    sends the keyword to the array row, which carries no ``uniqueItems`` and refuses one by
    name.  Recording the key here is what lets the field builder strip the keyword and
    render the fact, exactly as it does for a reused key.
    """
    out = merge(
        {"xs": {"contains": {"const": 1}}},
        {"xs": {"type": "array", "items": {"type": "integer"}, "uniqueItems": True}},
    )
    assert out.distinct == {"xs"}
    assert out.own["xs"]["uniqueItems"] is True


def test_a_uniqueItems_the_RESTATEMENT_states_itself_is_not_the_bases_rule() -> None:
    """The control for the test above: ``distinct`` is about where the keyword CAME FROM.

    A restatement stating the keyword itself is stating its own fact, so the class that
    decides this field states the rule and there is nothing for the base's rule to cover.
    Without this half, ``distinct`` would be "every key whose intersection has the
    keyword", which is a different set and would strip a fact nothing else states.
    """
    out = merge(
        {"xs": {"type": "array", "uniqueItems": True, "minItems": 1}},
        {"xs": {"type": "array", "uniqueItems": True}},
    )
    assert out.distinct == set()
