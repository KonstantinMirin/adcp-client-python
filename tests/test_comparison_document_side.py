"""The two DOCUMENT-side readings, and the gates that keep them honest.

``harness._normalize`` used to be called on the model's node only, so two
spellings the DOCUMENT also uses went unread: a LOCAL ``$ref`` and a union of
types.  A faithful class then reported as NARROWER than its own document -- 43
``added`` facts over 4 pairs for the reference and 9 over 7 pairs for the folds
(``salesagent-j3k2l.32``, ``salesagent-j3k2l.33``).  It is now called on both
sides, with the root a ``$ref`` resolves against supplied per side.

**``added`` is the direction that matters and the reason both readings are
dangerous.**  The comparison is symmetric, and ``added`` is the half where the
model is narrower than its document -- a class that refuses an instance the
document accepts, which is the one direction that can make a faithful SDK reject
valid traffic.  It is 0 over the whole graded tree.  A reading that resolved the
document until it matched whatever the model happened to say would drive
``added`` to 0 for a BROKEN tree too, and then the only check on the generated
code is gone.

So, following ``tests/test_comparison_folds.py``: **every test here that matters
is one that must still REPORT.** For each reading there are three -- a model that
OMITS a fact the resolved document states (``missing``), one that CONTRADICTS it
(``differs``), and one that INVENTS a fact the resolved document does not state
(``added``) -- and each of them one level down inside a folded branch as well as
at the node.  The agreeing cases are the short half of the file.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Annotated, Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from codegen import bundle
from codegen.harness import ComparisonResult, Pair, check_pair, compare_schema
from codegen.refusal import Refusal

from tests.nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

# --------------------------------------------------------------------------- #
# the documents.  Each is a ROOT with a `definitions` section, and the graded
# NODE is `#/definitions/holder` -- which is the shape that has no reading
# without the root, because the node's own `$ref` points at a SIBLING of it.
# --------------------------------------------------------------------------- #


def document(holder_property: dict, target: dict) -> dict:
    """A root whose ``#/definitions/holder`` references ``#/definitions/target``."""
    return {
        "type": "object",
        "properties": {"h": {"$ref": "#/definitions/holder"}},
        "definitions": {
            "holder": {
                "type": "object",
                "required": ["v"],
                "properties": {"v": holder_property},
                "additionalProperties": False,
            },
            "target": target,
        },
    }


def node_of(root: dict) -> dict:
    """The graded node, as ``adcp.types._base.schema_at`` hands it over: the
    sub-dict itself, with no ``definitions`` section of its own."""
    return root["definitions"]["holder"]


def graded(root: dict, model: Any) -> ComparisonResult:
    """One pair, graded the way ``check_pair`` grades the real population."""
    return compare_schema(node_of(root), model, document=root)


def keys(rows: list[str]) -> list[str]:
    """The POINTERS a result names, without the sentence after each one."""
    return sorted(r.split(": ")[0] for r in rows)


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# reading one: a DOCUMENT-side local $ref (salesagent-j3k2l.32)
# --------------------------------------------------------------------------- #
#: The target the models below are graded against: an object stating four facts.
TARGET = {
    "type": "object",
    "required": ["a"],
    "properties": {"a": {"type": "string", "minLength": 3}},
    "additionalProperties": False,
}

#: The document node at ``/definitions/holder/properties/v``: a bare local
#: reference with the one sibling the bundle ever puts there (measured: of 405
#: local-``$ref`` sites, 58 carry ``description``, 4 carry ``deprecated``, and 0
#: carry a constraint keyword).
REFERENCE = {"$ref": "#/definitions/target", "description": "the referenced value"}


class Inner(Base):
    a: str = Field(min_length=3)


# Exactly ``TARGET``, which is what the emitter renders for it.  NO DOCSTRING on
# any class graded here: pydantic renders one as the node's ``description``, which
# is a fact in ``FACTS``, so a docstring on a fixture is an ``added`` fact of the
# fixture's own making -- it cost two failures before this comment existed.
class Faithful(Base):
    v: Inner = Field(description="the referenced value")


def test_a_faithful_class_behind_a_local_reference_adds_nothing() -> None:
    """The defect, stated as the assertion that it is fixed.

    Without the document-side reading the node states NO FACT AT ALL, so all four
    of ``TARGET``'s facts plus the nested property arrive as ``added`` -- the
    model reported narrower than its document, for a class that is exactly its
    document.  The ``no_root`` half is that defect, reproduced through the same
    function, so this test holds both readings at once and cannot pass by the
    reading doing nothing.
    """
    root = document(REFERENCE, TARGET)
    with_root = graded(root, Faithful)
    assert with_root.added == [], with_root.added
    assert with_root.missing == [], with_root.missing
    assert with_root.differs == [], with_root.differs
    assert with_root.outcome == "pass", with_root

    # The same pair with no root: the reference does not resolve, the node states
    # only its sibling annotation, and the facts the class correctly carries are
    # reported.  THIS IS THE FAIL-SAFE DIRECTION -- an unresolvable reference
    # reddens the pair rather than passing it blind.
    no_root = compare_schema(node_of(root), Faithful)
    assert no_root.added, "an unresolved reference must not pass as agreement"
    assert no_root.outcome == "model_adds_a_fact", no_root.outcome


def test_an_unresolvable_local_reference_still_reddens() -> None:
    """A reference naming nothing is not read as "the document states nothing and
    the model is free"."""
    root = document({"$ref": "#/definitions/no-such-target"}, TARGET)
    res = graded(root, Faithful)
    assert res.added, res
    assert res.outcome == "model_adds_a_fact", res.outcome


# ``minLength`` dropped from the referenced value's own property.
class OmitsAFactOfTheTarget(Base):
    class Inner(Base):
        a: str

    v: Inner = Field(description="the referenced value")


# ``minLength`` present and wrong.
class ContradictsAFactOfTheTarget(Base):
    class Inner(Base):
        a: str = Field(min_length=9)

    v: Inner = Field(description="the referenced value")


# A ``pattern`` nothing in the document states.
class InventsAFactTheTargetDoesNotState(Base):
    class Inner(Base):
        a: str = Field(min_length=3, pattern="^x")

    v: Inner = Field(description="the referenced value")


class DropsAPropertyOfTheTarget(Base):
    class Inner(Base):
        pass

    v: Inner = Field(description="the referenced value")


#: The three ways a model can be wrong about a fact the document states only
#: BEHIND a local reference, each with the bucket it must land in and the pointer
#: it must name.  A reading that resolved the document too far reports none of
#: them, which is why this list and not the agreeing case is the test.
MUST_REPORT = [
    (OmitsAFactOfTheTarget, "missing", "/properties/v/properties/a/minLength"),
    (ContradictsAFactOfTheTarget, "differs", "/properties/v/properties/a/minLength"),
    (InventsAFactTheTargetDoesNotState, "added", "/properties/v/properties/a/pattern"),
    (DropsAPropertyOfTheTarget, "missing", "/properties/v/properties/a"),
]


@pytest.mark.parametrize(
    ("model", "bucket", "pointer"), MUST_REPORT, ids=[m.__name__ for m, _, _ in MUST_REPORT]
)
def test_a_disagreement_behind_a_local_reference_is_still_reported(
    model: Any, bucket: str, pointer: str
) -> None:
    res = graded(document(REFERENCE, TARGET), model)
    assert pointer in keys(getattr(res, bucket)), (bucket, res)


def test_a_constraint_sibling_of_a_local_reference_is_the_stated_ceiling() -> None:
    """The one unsafe half of "the outer keys win", pinned so it cannot drift.

    Draft-07 IGNORES every sibling of a ``$ref``, so ``{"$ref": X, "minimum": 5}``
    means X alone and a model stating ``minimum: 5`` really is NARROWER than its
    document.  This reading lets the sibling win, so that narrowing is excused --
    stated here as the behaviour rather than discovered later.

    **What bounds it is the bundle and not an argument**: of the 405 local-``$ref``
    sites across all 1,054 portable documents the only keys ever beside one are
    ``description`` (58) and ``deprecated`` (4), so this cell has a population of
    zero.  If a document ever states a constraint there, the fix is to keep only
    the keys outside ``harness.FACTS`` -- and this test is what will fail and say
    so, because it asserts the CURRENT reading by name.
    """
    root = document({"$ref": "#/definitions/target", "minLength": 5}, {"type": "string"})

    class StatesTheIgnoredSibling(Base):
        v: Annotated[str, Field(min_length=5)]

    res = graded(root, StatesTheIgnoredSibling)
    assert res.added == [], "the ceiling: the ignored sibling is read as a document fact"
    assert res.outcome == "pass", res

    # And the reading is not a blanket licence even here: a bound the sibling does
    # NOT state is still reported.
    class StatesMoreThanTheSibling(Base):
        v: Annotated[str, Field(min_length=5, max_length=7)]

    other = graded(root, StatesMoreThanTheSibling)
    assert "/properties/v/maxLength" in keys(other.added), other.added


# --------------------------------------------------------------------------- #
# reading two: the fold reads the document's own branch (salesagent-j3k2l.33)
# --------------------------------------------------------------------------- #
#: The two shapes ``_normalize`` folds, in the spelling the DOCUMENT uses for
#: each: the bundle states the bare-type union as ``oneOf`` (measured at
#: ``creative/creative-feature-result.json#/properties/value`` and
#: ``property/property-feature-value.json#/properties/value``) and the null arm
#: as ``anyOf`` (``formats/canonical/{audio,video}_hosted.json``
#: ``#/properties/duration_ms_range/items``).
BARE_TYPES = {"oneOf": [{"type": "boolean"}, {"type": "number"}, {"type": "string"}]}
NULL_ARM = {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]}
#: THE TWO UNIONS AS THE DELEGATED RESOLVER USED TO WRITE THEM.  It wrote a finite
#: type out as its members while inlining, so a document REFERENCING one of the
#: shapes above arrived with its boolean branch as ``{"enum": [false, true]}`` and its
#: null branch as ``{"const": null}`` -- and ``_normalize`` restored each branch before
#: folding.  ``bundle.record`` copies the branch the document writes, so all five of
#: the ``creative/creative-feature-result.json#/properties/value`` documents now carry
#: the one shape and the restoration is DELETED (``docs/plan/architecture.md`` §9).
#: These two stay as the NEGATIVE case: a document stating either in its own text is
#: left alone and compared, which is what the deleted fold must not come back to do.
BARE_TYPES_INLINED = {"oneOf": [{"enum": [False, True]}, {"type": "number"}, {"type": "string"}]}
NULL_ARM_INLINED = {"anyOf": [{"type": "integer", "minimum": 0}, {"const": None}]}


def holder(node: dict) -> dict:
    """A root whose graded node states ``node`` at ``/properties/v`` -- no
    reference, so this exercises the fold on its own."""
    return document(node, {"type": "string"})


class FaithfulBareTypes(Base):
    v: bool | float | str


class FaithfulNullArm(Base):
    v: Annotated[int, Field(ge=0)] | None


def test_a_faithful_class_over_a_folded_document_union_adds_nothing() -> None:
    """Both fold arms, read off the document instead of the model only.

    Before this, the document's node stated nothing in ``FACTS`` -- ``oneOf`` and
    ``anyOf`` are not facts -- while the model's node folded to a ``type`` list,
    so the list arrived as ``added``: 5 facts over 5 pairs for the bare-type arm
    and 4 over 2 for the null arm.
    """
    bare = graded(holder(BARE_TYPES), FaithfulBareTypes)
    assert (bare.added, bare.missing, bare.differs) == ([], [], []), bare
    assert bare.outcome == "pass", bare

    nul = graded(holder(NULL_ARM), FaithfulNullArm)
    assert (nul.added, nul.missing, nul.differs) == ([], [], []), nul
    assert nul.outcome == "pass", nul


@pytest.mark.parametrize(
    ("node", "model"),
    [(BARE_TYPES_INLINED, FaithfulBareTypes), (NULL_ARM_INLINED, FaithfulNullArm)],
    ids=["bare-types", "null-arm"],
)
def test_a_branch_the_resolver_used_to_rewrite_is_now_compared_as_written(
    node: dict, model: Any
) -> None:
    """The restoration is DELETED, so these two shapes no longer fold into a type list.

    The fold existed because the delegated resolver gave one union two shapes depending
    on whether the document stated it or referenced one that did.  ``bundle.record``
    copies the branch, so the two shapes stop being one union said two ways -- and a
    document that states ``{"enum": [false, true]}`` as a branch in its OWN text states
    an ``enum``, which §9's own rule says is a fact to compare rather than a type to
    restore.  So the node stays a combinator, states no fact in the compared set, and
    the model's type list is REPORTED: visible, which is the safe direction.
    """
    res = graded(holder(node), model)
    assert res.added, f"a branch the document itself writes must not fold: {res}"


def test_a_rewritten_branch_does_not_make_the_fold_a_licence() -> None:
    """A union whose branch states anything but a bare ``type`` is left alone.

    The surviving arm folds only where EVERY branch is a bare ``{"type": X}`` -- §9's
    "a type list rendered as a union" -- so a union carrying a value set in any branch
    is left alone and a model stating a type list over it is reported, which is what
    keeps the arm from excusing a model that invented a type.
    """
    for branch in ({"enum": [False]}, {"enum": ["a", "b"]}, {"const": "x"}):
        node = {"oneOf": [branch, {"type": "number"}]}

        class StatesATypeList(Base):
            v: bool | float

        res = graded(holder(node), StatesATypeList)
        assert res.added, f"{branch} is not a finite type and must not fold"


class FewerTypes(Base):
    v: bool | str


class MoreTypes(Base):
    v: bool | float | str | None


# ``int`` where the document's own branch declares ``null`` beside it.  The hole
# the fold has to NOT open: if the document side folded the null away the way D4's
# absence fold does, this model and ``FaithfulNullArm`` would compare identically
# and a dropped declaration would be invisible.
class DropsTheBranchDeclaredNull(Base):
    v: Annotated[int, Field(ge=0)]


class DropsTheBranchesBound(Base):
    v: int | None


class ContradictsTheBranchesBound(Base):
    v: Annotated[int, Field(ge=4)] | None


class InventsABoundInsideTheBranch(Base):
    v: Annotated[int, Field(ge=0, le=9)] | None


#: Every way a model can disagree with a fact the document states ONE LEVEL DOWN,
#: inside the branch the fold restored.  The bound (``minimum``) is the
#: interesting one: it is not a ``type`` word, so it reaches the comparison only
#: through the fold, and a fold that restored the type and dropped the bound
#: would pass all three of the ``type`` rows above.
FOLD_MUST_REPORT = [
    (BARE_TYPES, FewerTypes, "differs", "/properties/v/type"),
    (BARE_TYPES, MoreTypes, "differs", "/properties/v/type"),
    (NULL_ARM, DropsTheBranchDeclaredNull, "differs", "/properties/v/type"),
    (NULL_ARM, DropsTheBranchesBound, "missing", "/properties/v/minimum"),
    (NULL_ARM, ContradictsTheBranchesBound, "differs", "/properties/v/minimum"),
    (NULL_ARM, InventsABoundInsideTheBranch, "added", "/properties/v/maximum"),
]


@pytest.mark.parametrize(
    ("node", "model", "bucket", "pointer"),
    FOLD_MUST_REPORT,
    ids=[f"{m.__name__}-{b}" for _, m, b, _ in FOLD_MUST_REPORT],
)
def test_a_disagreement_inside_a_folded_branch_is_still_reported(
    node: dict, model: Any, bucket: str, pointer: str
) -> None:
    res = graded(holder(node), model)
    assert pointer in keys(getattr(res, bucket)), (bucket, res)


def test_a_null_the_model_admits_at_a_REQUIRED_key_is_not_read_as_absence() -> None:
    """The blind spot the document-side fold would otherwise have OPENED, and the
    only cell in this file that is a widening rather than a narrowing.

    Reading the document's union closes the ``added`` half: the document now
    states its ``type`` list.  It also makes the pair comparable in the other
    direction for the first time, and there the pre-existing unwrap was wrong --
    D4 renders ``None`` for an OPTIONAL property, and a REQUIRED one has no
    default, so a null branch there is a type the model admits and the document
    does not.  Measured before the ``null_is_absence`` axis existed: this model
    and ``FaithfulBareTypes`` both reported ``pass``, with identical empty
    ``added``, ``missing`` and ``differs``.

    Both halves are asserted, because the fix has to keep the unwrap D4 needs AND
    report the widening -- and only the two together tell a correct fold from a
    silencer.
    """
    required = document(BARE_TYPES, {"type": "string"})
    optional = {
        **required,
        "definitions": {
            **required["definitions"],
            "holder": {k: v for k, v in node_of(required).items() if k != "required"},
        },
    }

    # The widening is reported where the key cannot be omitted ...
    wide = graded(required, MoreTypes)
    assert "/properties/v/type" in keys(wide.differs), wide
    assert wide.outcome == "model_drops_a_fact", wide.outcome

    # ... and the SAME annotation is correct where it can, which is the half the
    # unwrap exists for.
    class OptionalNone(Base):
        v: bool | float | str | None = None

    narrow = graded(optional, OptionalNone)
    assert (narrow.added, narrow.missing, narrow.differs) == ([], [], []), narrow


#: The unions the fold must LEAVE ALONE, each with the reason.  A fold that took
#: any of these would throw a fact away, and a thrown-away fact is a green cell
#: nobody re-reads.
NEVER_FOLDED = [
    (
        {"anyOf": [{"type": "string", "minLength": 2}, {"type": "integer"}]},
        "two live branches and one carries more than a type word",
    ),
    (
        {"oneOf": [{"type": "integer"}, {"type": "number"}]},
        "a oneOf naming both integer and number REFUSES 5, which the type list admits",
    ),
    (
        {"anyOf": [{"type": "string", "description": "d"}, {"type": "integer"}]},
        "a branch description would be thrown away by the type-list fold",
    ),
    (
        {"anyOf": [{"properties": {"k": {"type": "string"}}}, {"type": "null"}]},
        "the live branch states no type word, so the fold cannot carry the null forward",
    ),
]


@pytest.mark.parametrize(
    ("node", "why"), NEVER_FOLDED, ids=[w[:40].replace(" ", "-") for _, w in NEVER_FOLDED]
)
def test_a_union_outside_the_two_arms_is_left_alone(node: dict, why: str) -> None:
    """Left alone means the node states no fact in ``FACTS``, so a model stating
    one is reported -- the SAFE direction, and the one that is visible."""
    from codegen.harness import _normalize  # noqa: PLC0415

    assert _normalize(node, {}, declared_null=True) == node, why

    class StatesAType(Base):
        v: str | None = None

    res = graded(holder(node), StatesAType)
    assert res.added, f"{why}: an unfolded node must not pass as agreement"


def test_the_two_fold_arms_are_the_only_ones_and_the_population_is_not_empty() -> None:
    """The fold admits exactly the two arms, asserted by exhausting the
    combinator list rather than by a copy of it.

    Same discipline as ``test_comparison_folds.py``'s closing test: a reading
    whose population nobody enumerated can grow silently when a keyword is added.
    """
    from codegen.harness import _UNION_KEYWORDS, _normalize  # noqa: PLC0415

    assert _UNION_KEYWORDS, "empty keyword list: the assertions below would be vacuous"
    folded = {
        kw
        for kw in _UNION_KEYWORDS
        if _normalize({kw: [{"type": "boolean"}, {"type": "string"}]}, {}) != {
            kw: [{"type": "boolean"}, {"type": "string"}]
        }
    }
    assert folded == set(_UNION_KEYWORDS), folded
    # allOf is a conjunction and `_composed` owns it; the fold must never touch it.
    conj = {"allOf": [{"type": "boolean"}, {"type": "string"}]}
    assert _normalize(conj, {}, declared_null=True) == conj


# --------------------------------------------------------------------------- #
# both readings at once, through `check_pair` -- the entry point the population
# is graded by, so the plumbing that carries the root is graded too.
# --------------------------------------------------------------------------- #
def test_the_root_reaches_the_comparison_through_check_pair() -> None:
    """``Pair.document`` is not decoration: the pointer that needs it is three
    hops below the node, and ``check_pair`` is what the real population runs.

    Asserted in both positions -- with the document and without -- because a
    field that is never read looks exactly like one that is.
    """
    root = document(REFERENCE, TARGET)
    node = node_of(root)

    def accept(x: Any) -> Any:
        return Faithful.model_validate(x)

    with_root = check_pair(Pair("holder", node, Faithful, accept, document=root))
    assert with_root.comparison is not None
    assert with_root.comparison.added == [], with_root.comparison.added
    assert with_root.comparison.outcome == "pass", with_root.comparison

    without = check_pair(Pair("holder", node, Faithful, accept))
    assert without.comparison is not None
    assert without.comparison.added, "the default must not resolve a sibling definition"


def test_a_wider_or_different_value_set_is_reported_in_the_documents_own_word() -> None:
    """§6 forbids a report about the TEXT ("A test that fails while the emitted
    behaviour is unchanged is grading a spelling"), and D14 the same of every check
    here ("A check asserts what a class accepts, refuses, or states about itself --
    never the text that expresses it").  What must still report is a different
    ACCEPTED SET, and that is what this pins.

    **The respelling that used to make the two words interchangeable is deleted
    (architecture §9).**  It existed because ``canonicalish`` rewrote a one-member
    ``enum`` into a ``const`` while inlining a remote ``$ref``, so a document that
    wrote ``const: x`` and one that wrote ``enum: [x]`` reached the comparison as the
    same bytes and no gate could ask which it was.  ``bundle.record`` copies the node,
    so the question is answerable again and each side is graded in the word its own
    document wrote -- which is what the section below asserts.  Here the subject is
    the accepted SET, and every one of these reports whichever word carries it.
    """
    root = document({"const": "x"}, {"type": "string"})

    class Literally(Base):
        v: Literal["x"]

    class TwoMembers(Base):
        v: Annotated[str, Field(json_schema_extra={"enum": ["x", "y"]})]

    class TheWrongMember(Base):
        v: Literal["y"]

    # A `Literal` renders `const`, which is what this document states.
    assert graded(root, Literally).outcome == "pass", graded(root, Literally)

    # Two members is a WIDER set, and one member that is not the document's is a
    # different one.  Neither is a spelling and both are reported.
    two = graded(root, TwoMembers)
    assert "/properties/v/const" in keys(two.missing), two
    assert "/properties/v/enum" in keys(two.added), two
    wrong = graded(root, TheWrongMember)
    assert "/properties/v/const" in keys(wrong.differs), wrong

    # And the other direction: a document stating TWO members against a model pinning
    # one is a model NARROWER than its document, which is the `added`/`differs` half.
    wider = document({"type": "string", "enum": ["x", "y"]}, {"type": "string"})
    assert graded(wider, Literally).outcome != "pass", graded(wider, Literally)


# --------------------------------------------------------------------------- #
# reading three: a CONJUNCT, read as the DOCUMENT writes it (row .3)
#
# `_composed` folds an `allOf` conjunct's facts into the node.  The conjunct used to
# arrive through the delegated resolver, whose finite-type rewrite had dropped the
# `type` off any boolean an inlined base declared -- so the fold was handed
# `{"enum": [false, true]}` and gap-filling left the merged node with an enum and no
# type, a shape no document states: 9 facts over 5 `formats/canonical` documents, each
# restating an inherited boolean with nothing but a `default` and a `description`.
#
# `bundle.record` copies the base's `{"type": "boolean"}`, so the conjunct arrives in
# the document's own spelling and both the restoration and the one-member respelling
# are DELETED (architecture §9).  Same discipline as above: the tests that matter are
# the ones that must still REPORT.
# --------------------------------------------------------------------------- #
def composing(own: dict, conjunct: dict, *, required: bool = True) -> dict:
    """A holder restating ``v`` itself beside an ``allOf`` conjunct declaring it.

    The ``formats/canonical`` shape exactly: the document's own property node
    carries annotations and no ``type``, and the inlined base's conjunct carries
    the resolver's rewrite of the ``type`` and nothing else.

    ``required`` is the holder's own, and has to follow the MODEL the probe
    grades: a field with a default is not required in pydantic, so a holder that
    demands the key would report a ``/required`` of the fixture's own making.
    """
    root = document(own, {"type": "string"})
    holder = root["definitions"]["holder"]
    holder["allOf"] = [{"properties": {"v": conjunct}}]
    if not required:
        del holder["required"]
    return root


#: A base's boolean AS THE BUNDLE WRITES IT, which is what ``bundle.record`` now
#: copies into the conjunct.  The delegated resolver wrote it ``{"enum": [false,
#: true]}`` with every annotation at the node dropped, and that is the shape
#: :data:`RESOLVER_SPELLING` keeps as the negative case below.
DOCUMENTS_BOOLEAN = {"type": "boolean", "description": "d"}
RESOLVER_SPELLING = {"enum": [False, True]}


def test_a_conjuncts_own_type_is_folded_in_and_the_pair_grades_the_accepted_set() -> None:
    """The 9 facts, as a pair: a faithful class over the real shape reports nothing.

    The conjunct carries the base's ``{"type": "boolean"}`` because the record copies
    it, so the fold receives a typed node and the pair grades the accepted set as a
    ``type`` -- with no restoration between the document and the comparison.
    """
    own = {"default": True, "description": "d"}
    root = composing(own, DOCUMENTS_BOOLEAN, required=False)

    class Faithful(Base):
        v: bool = Field(default=True, description="d")

    res = graded(root, Faithful)
    assert (res.added, res.missing, res.differs) == ([], [], []), res
    assert res.outcome == "pass", res
    # Nothing is folded by ``_constrains_nothing`` here either: its gate is never
    # asked, because there is no enum at the merged node to ask about.  Asserted so a
    # later change that routes this through the fold instead is visible rather than
    # silently equivalent.
    assert res.constrains_nothing == [], res.constrains_nothing


def test_the_conjuncts_type_is_graded_and_not_merely_dropped() -> None:
    """A model whose type disagrees with the conjunct's is still reported, which is
    what makes the gap-fill lossless rather than a hole one fact wide."""
    root = composing({"description": "d"}, DOCUMENTS_BOOLEAN)

    class WrongType(Base):
        v: str = Field(description="d")

    res = graded(root, WrongType)
    assert "/properties/v/type" in keys(res.differs), res


def test_the_resolvers_own_spelling_of_a_boolean_is_now_compared_as_an_enum() -> None:
    """The DELETED restoration, from the side that proves it is gone.

    A conjunct stating ``{"enum": [false, true]}`` used to be restored to
    ``{"type": "boolean"}`` before its facts were folded in.  No document of the bundle
    writes that shape -- 0 raw nodes, measured -- so the only thing the restoration
    could still fire on is a document that states it itself, where §9 says the enum is
    a fact to compare.  So it is compared: the faithful-boolean model states the
    ``type`` and not the ``enum``, and the ``enum`` is reported ``missing``.
    """
    root = composing({"description": "d"}, RESOLVER_SPELLING)

    class StatesTheType(Base):
        v: bool = Field(description="d")

    res = graded(root, StatesTheType)
    assert "/properties/v/enum" in keys(res.missing), res


def test_a_conjunct_stating_a_fact_the_model_lacks_is_still_missing() -> None:
    """A conjunct is the document, so a conjunct's own constraint the model drops
    is reported.  The reading restores a rewritten TYPE; it excuses nothing."""
    root = composing(
        {"description": "d"}, {"type": "string", "minLength": 3, "pattern": "^a"}
    )

    class Lax(Base):
        v: str = Field(description="d")

    res = graded(root, Lax)
    assert "/properties/v/minLength" in keys(res.missing), res
    assert "/properties/v/pattern" in keys(res.missing), res


class StatesABoolean(Base):
    v: bool = Field(description="d")


class StatesAString(Base):
    v: str = Field(description="d")


@pytest.mark.parametrize(
    ("conjunct", "model", "keyword", "why"),
    [
        ({"enum": [False]}, StatesABoolean, "enum", "one member PINS the value to false"),
        ({"enum": [True]}, StatesABoolean, "enum", "and the other one pins it to true"),
        (
            {"enum": [False, True, None]},
            StatesABoolean,
            "enum",
            "a third member is not the boolean domain",
        ),
        ({"enum": ["a", "b"]}, StatesAString, "enum", "a string enumeration is no rewrite"),
    ],
    ids=["false-only", "true-only", "three-members", "strings"],
)
def test_a_conjunct_enum_outside_the_boolean_DOMAIN_still_compares(
    conjunct: dict, model: Any, keyword: str, why: str
) -> None:
    """**The test that says a conjunct's value set is never excused.**

    A conjunct is the document, so its vocabulary is the document's and a model that
    drops it is reported.  No shape of ``enum`` folds anywhere now --
    ``_constrains_nothing``'s boolean-pair arm and ``_one_member_enum``'s respelling
    both went with the delegated resolver (§9) -- so every case here reports under the
    keyword the DOCUMENT wrote, which is why ``keyword`` is ``enum`` throughout.

    ``keyword`` stays a parameter rather than becoming a looser assertion so that a
    case which stopped being reported at all still fails here.
    """
    res = graded(composing({"description": "d"}, conjunct), model)
    assert f"/properties/v/{keyword}" in keys(res.missing), f"{why}: {res}"
    assert res.constrains_nothing == [], f"{why}: {res.constrains_nothing}"


# --------------------------------------------------------------------------- #
# reading four, DELETED: the ONE-MEMBER respelling (architecture §9)
#
# `const: v` and `enum: [v]` admit exactly the same instance, and `_one_member_enum`
# wrote the second as the first on BOTH sides.  It existed because `canonicalish`
# rewrote a one-member `enum` into a `const` WHILE INLINING a remote `$ref` and
# dropped the node's `type` and `description` doing it -- so `creative/audit-
# observation.json`'s own resolved `code` node read `{"type": "string", "enum":
# ["OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"], "description": ...}` while the copy
# inlined into `creative/get-creative-features-terminal-success.json` read
# `{"const": "OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"}`, and a faithful class read as
# both dropping a `const` and adding an `enum`: 3 facts in each direction.
#
# `bundle.record` copies the node, so the referrer's copy spells what the target
# spells, and §4's rows pick the same word on the model's side -- a `const` node
# renders a `Literal` and so a `const`, an `enum` node renders a `StrEnum` and so an
# `enum`.  The two sides reach the node with the same keyword, there is nothing to
# respell, and the fold is gone.
#
# What is left to assert is that EACH SPELLING IS GRADED AS THE DOCUMENT WRITES IT,
# and that every disagreement about the accepted set still reports.
# --------------------------------------------------------------------------- #
# No docstring: a model's docstring IS its root `description`, and the document
# the probe grades against states none.
class EnumeratesX(Base):  # `enum: ['x']` -- a one-member enumeration's spelling
    v: Annotated[str, Field(json_schema_extra={"enum": ["x"]})]


def test_each_spelling_of_a_one_member_set_is_graded_as_the_document_writes_it() -> None:
    """A ``const`` document against a ``const`` model, an ``enum`` one against an
    ``enum`` model, and both pass -- with no respelling in between.

    This is the pairing the record produces: §4's enumeration row lowers an ``enum``
    node and §4's ``const`` row lowers a ``const`` one, so the word the model renders
    is the word its own document wrote, at the referrer as much as at the target.
    """
    res = graded(holder({"type": "string", "enum": ["x"]}), EnumeratesX)
    assert (res.added, res.missing, res.differs) == ([], [], []), res

    class Literally(Base):
        v: Literal["x"]

    res = graded(holder({"const": "x"}), Literally)
    assert (res.added, res.missing, res.differs) == ([], [], []), res
    assert res.outcome == "pass", res


def test_a_cross_spelling_pair_is_REPORTED_and_no_longer_folded() -> None:
    """The deleted fold, from the side that proves it is gone.

    A document writing ``enum: ["x"]`` against a model rendering ``const: "x"`` is the
    pair the respelling made green.  It is now reported in both halves -- the
    document's ``enum`` missing, the model's ``const`` added -- and that is the right
    report, because nothing in the record produces the mismatch: the respelling's only
    source was the delegated resolver, and a mismatch that survives it is the EMITTER
    choosing a word its document did not.
    """

    class Literally(Base):
        v: Literal["x"]

    res = graded(holder({"type": "string", "enum": ["x"]}), Literally)
    assert "/properties/v/enum" in keys(res.missing), res
    assert "/properties/v/const" in keys(res.added), res


def test_a_conjuncts_one_member_set_is_compared_in_its_own_spelling() -> None:
    """§6's "including one level down, inside a branch it folded", after the deletion.

    ``_composed`` folds an ``allOf`` conjunct's facts into the node, and the conjunct
    now carries the word the base wrote.  A base declaring ``enum: ["x"]`` against a
    model that enumerates one member agrees; against a ``Literal`` it reports.
    """
    root = composing({"description": "d"}, {"enum": ["x"]})

    class EnumeratesXWithDescription(Base):
        v: Annotated[str, Field(description="d", json_schema_extra={"enum": ["x"]})]

    res = graded(root, EnumeratesXWithDescription)
    assert (res.added, res.missing, res.differs) == ([], [], []), res

    class Faithful(Base):
        v: Annotated[Literal["x"], Field(description="d")]

    assert "/properties/v/enum" in keys(graded(root, Faithful).missing)


def test_a_model_pinning_a_DIFFERENT_member_is_still_reported() -> None:
    """The deletion excuses no accepted set: the document pins ``x``, the model ``y``.

    Written once as a one-member enumeration, where the two sides share the keyword and
    the fact ``differs``, and once as a ``Literal``, where they do not and the document's
    ``enum`` is ``missing`` -- both reported, which is the half that matters.
    """

    class EnumeratesY(Base):
        v: Annotated[str, Field(json_schema_extra={"enum": ["y"]})]

    class PinsY(Base):
        v: Literal["y"]

    res = graded(holder({"type": "string", "enum": ["x"]}), EnumeratesY)
    assert "/properties/v/enum" in keys(res.differs), res
    res = graded(holder({"type": "string", "enum": ["x"]}), PinsY)
    assert "/properties/v/enum" in keys(res.missing), res
    res = graded(holder({"const": "x"}), PinsY)
    assert "/properties/v/const" in keys(res.differs), res


def test_a_model_that_pins_NOTHING_is_still_reported() -> None:
    """The other must-report half: a model that drops the pin entirely.

    ``str`` admits every string and the document admits one, so the model is WIDER
    than its document -- which is the ``missing`` no fold may swallow, in either of
    the document's two spellings.
    """

    class AnyString(Base):
        v: str

    res = graded(holder({"type": "string", "enum": ["x"]}), AnyString)
    assert "/properties/v/enum" in keys(res.missing), res
    res = graded(holder({"type": "string", "const": "x"}), AnyString)
    assert "/properties/v/const" in keys(res.missing), res


# --------------------------------------------------------------------------- #
# reading five: a MAPPING's `additionalProperties: true` is the silence it is
# (adcp-client-python-10l.3)
#
# Section 4's mapping row renders a property-less object as `dict[K, V]`, and pydantic
# 2.13.5 has no spelling of `dict[str, Any]` that omits `additionalProperties: true`.
# draft-07's `additionalProperties` constrains the keys a schema does not declare, and
# `true` admits every one of them -- which is what silence admits -- so the two spellings
# are ONE acceptance fact and a faithful mapping states a keyword its document does not.
# 23 pairs of the committed tree, measured, every one of whose documents writes
# `{"type": "object"}` in the RAW bundle.
#
# `harness._silent_about_extras` reads it as silence on BOTH sides, which is §9's "the
# readings this pipeline's own output forces ... each applied to both sides".  What it
# REPLACED was a model-only admission -- `_narrows_nothing`'s
# `keyword == "additionalProperties" and value is True`, justified by a ONE-site
# measurement of the delegated resolver's redundant-key drop and silently absorbing
# these 23.  So the tests that matter here are the ones that say the SCOPE holds: a node
# with `properties`, a `false`, and a typed value are each untouched, and each still
# reports.
# --------------------------------------------------------------------------- #
class OpenMapping(Base):  # `dict[str, Any]` -- section 4's mapping row with no value type
    v: dict[str, Any]


class ClosedInner(Base):  # pydantic renders `{"additionalProperties": false, "properties": {}}`
    pass


class ClosedMapping(Base):
    v: ClosedInner


class TypedMapping(Base):
    v: dict[str, str]


def test_a_mappings_additional_properties_true_is_read_as_silence_on_both_sides() -> None:
    """The live shape, in both directions, and the function on its own beside it.

    A document writing ``{"type": "object"}`` against a model rendering
    ``dict[str, Any]``, and the same document writing ``additionalProperties: true``
    against a model that is silent -- one accepted set either way, so neither direction
    reports.  Probed on the function too, because a pair that happens to pass says
    nothing about which reading produced the pass.
    """
    from codegen.harness import _silent_about_extras  # noqa: PLC0415

    assert _silent_about_extras({"type": "object", "additionalProperties": True}) == {
        "type": "object"
    }
    assert _silent_about_extras({"type": "object"}) == {"type": "object"}

    for node in ({"type": "object"}, {"type": "object", "additionalProperties": True}):
        res = graded(holder(node), OpenMapping)
        assert (res.added, res.missing, res.differs) == ([], [], []), (node, res)
        assert res.outcome == "pass", (node, res)


@pytest.mark.parametrize(
    ("node", "why"),
    [
        (
            {"type": "object", "properties": {"k": {"type": "string"}}, "additionalProperties": True},
            "a node declaring properties is a CLASS, where D8 makes the distinction "
            "load-bearing: silence is extra=ignore and true is extra=allow",
        ),
        (
            {"type": "object", "additionalProperties": False},
            "false FORBIDS what silence permits, so the two are different accepted sets",
        ),
        (
            {"type": "object", "additionalProperties": {"type": "string"}},
            "a typed value restricts the VALUE schema, which silence does not",
        ),
    ],
    ids=["declares-properties", "closed", "typed"],
)
def test_the_mapping_reading_fires_on_NEITHER_side_outside_its_shape(node: dict, why: str) -> None:
    """The control, and the whole of this reading's correctness.

    The arm it replaced was blanket -- any model-only ``additionalProperties: true``,
    whatever the node -- so the scope is what keeps one blanket predicate from becoming
    another.  Asserted on the node itself rather than through a pair, because a pair that
    happens to report says nothing about which gate held.
    """
    from codegen.harness import _silent_about_extras  # noqa: PLC0415

    assert _silent_about_extras(node) == node, why


def test_a_model_that_CLOSES_a_mapping_its_document_leaves_open_is_still_reported() -> None:
    """The narrowing direction, which is the one that matters.

    ``additionalProperties: false`` on the model at a mapping the document leaves open
    refuses keys the document admits -- a model NARROWER than its schema, and the reading
    above must not touch it.  Both spellings of the document's openness are asked, so a
    reading that normalised ``false`` into silence by accident reddens here.
    """

    for node in ({"type": "object"}, {"type": "object", "additionalProperties": True}):
        res = graded(holder(node), ClosedMapping)
        # By NAME and not by ``outcome``: a model that happened to differ on some other
        # keyword would satisfy "not pass" and say nothing about this reading.
        assert "/properties/v/additionalProperties" in keys(res.added), (node, res)


def test_a_document_that_CLOSES_a_mapping_the_model_leaves_open_is_still_reported() -> None:
    """The other direction: the document forbids an extra key and the model admits one,
    which is the model being WIDER and is reported as ``missing``."""

    res = graded(holder({"type": "object", "additionalProperties": False}), OpenMapping)
    assert "/properties/v/additionalProperties" in keys(res.missing), res


def test_a_model_that_TYPES_a_mapping_whose_document_says_true_is_still_reported() -> None:
    """A typed value is a restriction the document does not state, so it is reported.

    This is the case the reading could most easily swallow -- the document's ``true`` is
    normalised to silence, so the model's value schema has nothing to be compared
    against and reads as ``added``.  Asserted rather than left to the gate's wording.
    """

    res = graded(holder({"type": "object", "additionalProperties": True}), TypedMapping)
    assert "/properties/v/additionalProperties" in keys(res.added), res


# --------------------------------------------------------------------------- #
# reading six: a `description` two views state goes with the view that states the
# composed VALUE SET (adcp-client-python-10l.18)
#
# `_composed` folds a conjunct by GAP-FILL for every fact `_tighter` cannot order, and
# `description` is one of those: the node's own won and the conjunct's was dropped.  At
# a ROOT that is the right answer and the measurement that justified it was taken there
# -- the node IS the document's own declaration and a conjunct is a composed base's, so
# §6's "a composed base's loses to the document's own" and "the node's own wins" are the
# same sentence.
#
# They are opposite sentences at an OVERLAY.  A conjunct's `properties` and `items` are
# stashed as an `allOf` on the merged node and folded again on descent, so at the
# descended pointer the NODE is the base's declaration and the STASH is the document's
# own narrowing conjunct.  Measured on `core/media-buy-frequency-cap-requirement.json`
# at `/properties/supported_control_modes/items`, whose base declares the element as
# `enums/frequency-cap-control-mode.json` (three members) and whose own overlay narrows
# it to `enums/media-buy-frequency-cap-control-mode.json` (one): the merged node took
# the conjunct's `enum` by `_tighter` and kept the BASE's description, so a class typed
# by the narrowing declaration read as dropping a fact.  2 pairs, 2 `differs`.
#
# `_described_by_the_conjunct` is the reading, and its SCOPE is the whole of its
# correctness: it fires where the conjunct's value set is STRICTLY inside the node's and
# the conjunct states a description, and nowhere else.  Re-measured over the graded
# tree: 2 sites inside the scope, 3 where the node is the narrower view, 277 where
# neither narrows, 0 where the narrowing is a bound.  So each gate is perturbed
# separately below, and the must-REPORT half is asserted through a pair.
# --------------------------------------------------------------------------- #
#: The two views of one element, as the bundle writes them: a base's vocabulary and the
#: document's own narrowing of it, each with a description of its own.
WIDE_ELEMENT = {"type": "string", "enum": ["a", "b", "c"], "description": "the package shape"}
NARROW_ELEMENT = {"type": "string", "enum": ["a", "b"], "description": "the aggregate shape"}


def overlaid(base: dict, overlay: dict) -> dict:
    """A holder declaring ``v`` in TWO conjuncts and in no ``properties`` of its own.

    The measured shape, and the reason the polarity flips: the holder's own
    ``properties`` is empty, so the first conjunct's declaration of ``v`` becomes the
    merged node and the second arrives as the stash ``_composed`` folds on descent.  A
    fixture that put the base in the holder's own ``properties`` would have the node be
    the document's own and would never reach this reading.
    """
    root = document({"type": "string"}, {"type": "string"})
    holder = root["definitions"]["holder"]
    holder["properties"] = {}
    # DEEP COPIES: ``WIDE_ELEMENT`` and ``NARROW_ELEMENT`` are module-level and are read
    # by the scope table as well, so a fixture holding either by reference would let one
    # test's grading decide another's -- under xdist, in an order nobody chose.
    holder["allOf"] = [
        {"properties": {"v": copy.deepcopy(base)}},
        {"properties": {"v": copy.deepcopy(overlay)}},
    ]
    return root


#: The live shape: an array whose ELEMENT the overlay narrows.  Written through ``items``
#: rather than at the property itself because that is where the bundle states it, and
#: because the ``items`` stash is a second mechanism between the document and the
#: reading -- a test at the property alone would pass with the descent broken.
NARROWED_ELEMENT = overlaid(
    {"type": "array", "items": WIDE_ELEMENT}, {"type": "array", "items": NARROW_ELEMENT}
)


class NarrowedWithItsOwnDescription(Base):
    v: list[Annotated[Literal["a", "b"], Field(description="the aggregate shape")]]


class NarrowedWithTheBasesDescription(Base):
    v: list[Annotated[Literal["a", "b"], Field(description="the package shape")]]


class NarrowedAndSilent(Base):
    v: list[Literal["a", "b"]]


def test_a_class_typed_by_the_narrowing_declaration_states_the_documents_description() -> None:
    """The live shape, as a pair: the faithful class reports nothing in any direction.

    "Faithful" is the compiler's own answer here -- ``_intersection`` decides the field
    from the narrowing declaration and carries that declaration's annotations, so the
    element type is the narrowing target's class and its docstring is that target's
    description.  This asserts the DOCUMENT side reaches the same reading, which is what
    §9 requires of the two spellings it keeps apart.
    """
    res = graded(NARROWED_ELEMENT, NarrowedWithItsOwnDescription)
    assert (res.added, res.missing, res.differs) == ([], [], []), res
    # The vocabulary is graded too, and by ``_tighter`` rather than by this reading: a
    # fold that moved the description and left the enum wide would pass the assertion
    # above only because the model happened to say nothing about it.
    assert res.compared, res


def test_a_class_stating_the_WIDER_descriptions_text_is_still_reported() -> None:
    """The must-report half, and the one the old gap-fill made green.

    A class carrying the BASE's description where the document's own conjunct states
    another is the exact pair the ceiling passed -- with the polarity reversed, since
    the gap-fill graded against the base's text.  It reports ``differs``, which is the
    proof the reading moved the authority rather than stopped comparing.
    """
    res = graded(NARROWED_ELEMENT, NarrowedWithTheBasesDescription)
    assert "/properties/v/items/description" in keys(res.differs), res


def test_a_class_stating_NO_description_is_still_missing_one() -> None:
    """The other must-report half: the reading decides WHICH description the document
    states, never whether it states one.  A class that drops it entirely is ``missing``.
    """
    res = graded(NARROWED_ELEMENT, NarrowedAndSilent)
    assert "/properties/v/items/description" in keys(res.missing), res


#: Every gate of :func:`_described_by_the_conjunct`, perturbed ONE AT A TIME against the
#: shape above, with the reason the reading must not fire.  Asserted on the function and
#: not through a pair: a pair that happens to report says nothing about which gate held,
#: and three of these perturbations leave a pair green for a different reason.
OUTSIDE_THE_SCOPE: list[tuple[dict, dict, str]] = [
    (
        WIDE_ELEMENT,
        {"type": "string", "enum": ["a", "b"]},
        "the conjunct states NO description, and silence inherits (§6 clause 3): "
        "core/canonical-media-buy-action.json narrows task to a const and says nothing "
        "to a reader, where deleting the base's text would make the document state none",
    ),
    (
        NARROW_ELEMENT,
        WIDE_ELEMENT,
        "the NODE is the narrower view, so the node already states the composed "
        "declaration and its own description is the answer -- 3 sites on the tree",
    ),
    (
        WIDE_ELEMENT,
        {"type": "string", "enum": ["c", "b", "a"], "description": "a reordering"},
        "the two state the SAME value set in a different order, so neither narrows and "
        "§6's default stands: the node's own wins",
    ),
    (
        WIDE_ELEMENT,
        {"type": "string", "enum": ["b", "c", "d"], "description": "an overlap"},
        "the sets OVERLAP and neither contains the other, so no view states the "
        "intersection and there is nothing to inherit an annotation from",
    ),
    (
        WIDE_ELEMENT,
        {"type": "string", "enum": ["x"], "description": "a disjoint pin"},
        "the sets are DISJOINT -- an empty intersection, which is the emitter's refusal "
        "to make, so the pair must report rather than be regraded",
    ),
    (
        {"type": "integer", "minimum": 0, "description": "the base's bound"},
        {"type": "integer", "minimum": 3, "description": "a tighter bound"},
        "the narrowing is a BOUND and not a vocabulary: 0 sites on the tree, and an arm "
        "for it would be a derivation matching nothing",
    ),
    (
        {"type": "string", "description": "the base's text"},
        {"minLength": 3, "description": "a tighter length"},
        "neither view states a value set at all, so the axis this reading is about is "
        "not in play",
    ),
    (
        {"type": "string", "enum": ["a", "a", "b"], "description": "a duplicated member"},
        {"type": "string", "enum": ["a", "b"], "description": "the same two members"},
        "the conjunct's set EQUALS the node's and only a duplicate makes it look "
        "smaller, so strictness is membership and never a length",
    ),
]


@pytest.mark.parametrize(
    ("node", "conjunct", "why"),
    OUTSIDE_THE_SCOPE,
    # UNDERSCORES and not the hyphens the ids above this section use: every gate here is
    # selected by name from ``perturb_composed_description.sh``, and ``pytest -k`` reads a
    # hyphen as part of its expression grammar rather than as part of a word -- so a
    # hyphenated id selects NO test and the perturbation script scores a dead guard as a
    # live one.  Measured: three cases printed "STAYED GREEN" with no test having run.
    ids=[
        "conjunct_silent",
        "node_is_narrower",
        "same_set_reordered",
        "overlapping",
        "disjoint",
        "bound_narrows",
        "no_vocabulary",
        "duplicate_member",
    ],
)
def test_the_description_reading_fires_on_NOTHING_outside_its_shape(
    node: dict, conjunct: dict, why: str
) -> None:
    """The control, and the whole of this reading's correctness.

    It replaced a gap-fill whose answer was right at 277 of 282 sites, so a gate that
    widened by one case would re-grade a description the document does state at its own
    pointer -- and the symptom is a FALSE GREEN, because the re-graded text is whatever
    the model happens to say.  Each row is the live shape with one gate perturbed and
    nothing else.
    """
    from codegen.harness import _described_by_the_conjunct  # noqa: PLC0415

    assert _described_by_the_conjunct(node, conjunct) == node, why


def test_the_reading_fires_INSIDE_its_shape_so_the_table_above_is_not_vacuous() -> None:
    """The positive case on the same function, so the eight rows above are a scope and
    not a predicate that answers ``node`` to everything.

    Asserted as "the node's description stood down and nothing else moved": the reading
    is written as a stand-down rather than a second write, so the gap-fill below it stays
    the one place a fact crosses from a conjunct to the merged node.
    """
    from codegen.harness import _described_by_the_conjunct  # noqa: PLC0415

    answer = _described_by_the_conjunct(WIDE_ELEMENT, NARROW_ELEMENT)
    assert answer == {k: v for k, v in WIDE_ELEMENT.items() if k != "description"}, answer


def test_a_conjuncts_const_INSIDE_the_nodes_enum_is_the_narrower_view() -> None:
    """A ``const`` is read as the one-member vocabulary it is, which is the rewrite
    ``compiler._as_enum`` makes on the model side.

    Without it the pin -- the tightest narrowing a conjunct can state -- would be the one
    shape the reading missed, and it is also the shape ``_one_vocabulary`` fires on, so
    the vocabulary is read BEFORE that collapse drops one of the two statements.
    """
    from codegen.harness import _described_by_the_conjunct  # noqa: PLC0415

    pin = {"type": "string", "const": "a", "description": "the aggregate shape"}
    answer = _described_by_the_conjunct(WIDE_ELEMENT, pin)
    assert "description" not in answer, answer
    # And the other direction is the node's: a node that pins inside the conjunct's
    # vocabulary is the narrower view and keeps its own text.
    assert _described_by_the_conjunct(pin, WIDE_ELEMENT) == pin


def test_a_default_two_views_state_differently_is_NOT_moved() -> None:
    """The reading is scoped to ``description`` and ``default`` is left where it was.

    ``compiler.RENDERED`` carries both and the authority question is the same one, but
    the 7 sites where two views default a property differently are all outside this
    reading's shape -- none of them narrows a vocabulary -- so an arm for ``default``
    would be a derivation matching nothing.  Asserted so that adding one is a decision
    rather than a side effect.
    """
    from codegen.harness import _described_by_the_conjunct  # noqa: PLC0415

    node = {"type": "string", "enum": ["a", "b", "c"], "default": "c", "description": "d"}
    conjunct = {"type": "string", "enum": ["a", "b"], "default": "a", "description": "e"}
    answer = _described_by_the_conjunct(node, conjunct)
    assert answer["default"] == "c", answer
    assert "description" not in answer, answer


# --------------------------------------------------------------------------- #
# reading three: a union BRANCH that is a bare local `$ref`
# (adcp-client-python-10l.19)
# --------------------------------------------------------------------------- #
# Reading one takes the local reference at the NODE.  It was not taken at the
# BRANCHES inside a combinator, and `_entails_type`'s union derivation asks every
# branch for its own `type` word -- so a branch that is a bare local `$ref` answered
# nothing, a root union whose every branch is typed `object` derived no type, and §4's
# union base, which is a pydantic model and renders `type: object`, reported as `added`
# against a document that states the word at every branch.  That is
# `core/requirements/catalog-field-binding.json#`, whose first two branches are
# `{"$ref": "#/definitions/ScalarBinding"}` and `{"$ref": "#/definitions/AssetPoolBinding"}`.
#
# `_branch_target` is the hop, it is ONE HOP, and it is gated on the branch being BARE.
# Every test below is a perturbation that must still REPORT, for the reason the module
# docstring gives: `added` is the direction that can make a faithful SDK refuse valid
# traffic, and a reading that resolved the document until it matched the model would
# drive it to 0 for a broken tree too.
#: The two branch targets of the agreeing case: objects, each stating the same `type`.
SCALAR = {
    "type": "object",
    "required": ["kind"],
    "properties": {"kind": {"type": "string", "const": "scalar"}},
}
POOL = {
    "type": "object",
    "required": ["kind"],
    "properties": {"kind": {"type": "string", "const": "pool"}},
}


def union_root(branches: list[dict], **targets: dict) -> dict:
    """A ROOT union with a ``definitions`` section its branches point into.

    The shape `core/requirements/catalog-field-binding.json` has, and the shape that
    has no reading without the root: the branch's pointer names a SIBLING of the node
    it is a branch of.
    """
    return {
        "description": "a binding",
        "definitions": dict(targets),
        "oneOf": branches,
    }


#: §4's union base, which is a pydantic model and so renders ``type: object``.  **No
#: ``extra`` setting and no docstring**: ``extra="forbid"`` renders
#: ``additionalProperties: false``, which is a compared fact the document does not
#: state, and a docstring renders a ``description`` -- either would be an ``added``
#: fact of the fixture's own making rather than of the reading's.
class UnionBase(BaseModel):
    """a binding"""


def root_graded(root: dict, model: Any = UnionBase) -> ComparisonResult:
    """The root union, graded as a ROOT pair: the node IS the document."""
    return compare_schema(root, model, document=root)


def test_a_union_branch_that_is_a_bare_local_ref_states_its_targets_type() -> None:
    """The defect, stated as the assertion that it is fixed.

    Every branch of a draft-07 combinator is applied to the SAME instance and an
    instance must satisfy one of them, so a root stating no ``type`` of its own whose
    every branch states ``object`` admits only objects.  Two of the three branches of
    the live document say ``object`` through a reference, and a derivation that reads
    the pointer rather than the node it names answers ``False``.
    """
    root = union_root(
        [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/pool"}],
        scalar=SCALAR,
        pool=POOL,
    )
    res = root_graded(root)
    assert res.added == [], res.added
    assert res.missing == [], res.missing
    assert res.differs == [], res.differs
    assert res.compared, "the root states a description; a 0-fact pair grades nothing"

    # The derivation is the thing, so it is also asked directly -- and asked for the
    # types the document does NOT force, which the one assertion above cannot see.
    from codegen.harness import _entails_type, _normalize  # noqa: PLC0415

    node = _normalize(root, root, declared_null=True)
    assert _entails_type(node, "object") is True
    for other in ("string", "array", "integer", "number", "boolean", "null"):
        assert _entails_type(node, other) is False, other


#: Every way a union branch can fail to state a type the document really forces, each
#: of which must leave the model's ``type: object`` REPORTED.  A reading that answered
#: ``True`` for any of these would excuse a narrowing nobody decided.
MUST_STILL_REPORT = [
    (
        union_root(
            [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/other"}],
            scalar=SCALAR,
            other={"type": "string"},
        ),
        "the branches disagree once resolved, so the union forces no one type",
    ),
    (
        union_root(
            [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/untyped"}],
            scalar=SCALAR,
            untyped={"required": ["kind"]},
        ),
        "a resolved branch stating no type word forces nothing",
    ),
    (
        union_root(
            [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/no-such-target"}],
            scalar=SCALAR,
        ),
        "an unresolvable branch pointer leaves the branch as written -- FAIL-SAFE",
    ),
    (
        union_root(
            [
                {"$ref": "#/definitions/scalar"},
                {"$ref": "#/definitions/pool", "description": "a sibling"},
            ],
            scalar=SCALAR,
            pool=POOL,
        ),
        "the gate is that the branch is BARE: a sibling means no hop, 0 sites in the bundle",
    ),
    (
        union_root(
            [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/hop"}],
            scalar=SCALAR,
            hop={"$ref": "#/definitions/pool"},
            pool=POOL,
        ),
        "ONE HOP: a chain is not followed, and it reddens rather than passing blind",
    ),
    (
        union_root(
            [
                {"$ref": "#/definitions/scalar"},
                {"$ref": "https://adcontextprotocol.org/schemas/3.2.4/core/pool.json"},
            ],
            scalar=SCALAR,
        ),
        "a REMOTE reference is not a local one; bundle.record inlines those, 0 in a record",
    ),
    (
        union_root([{"$ref": "#/definitions/scalar"}], scalar={"type": "object"}),
        "a target that is itself bare is still read, and a one-branch union is still graded",
    ),
]


@pytest.mark.parametrize(
    ("root", "why"),
    MUST_STILL_REPORT[:-1],
    ids=[w[:44].replace(" ", "-") for _, w in MUST_STILL_REPORT[:-1]],
)
def test_a_branch_the_hop_does_not_reach_still_reports_the_models_type(
    root: dict, why: str
) -> None:
    res = root_graded(root)
    assert "/type" in keys(res.added), f"{why}: {res}"
    assert res.outcome == "model_adds_a_fact", (why, res.outcome)


def test_the_hop_does_not_excuse_any_other_model_only_fact() -> None:
    """The hop answers a ``type`` and nothing else.

    Scoped by what it changes, not by what it is gated on: the derivation it feeds is
    ``_entails_type``, which decides exactly one keyword.  A model closing the root, or
    requiring a key the document does not, is still reported at the same node the hop
    made green for ``type``.
    """
    root = union_root(
        [{"$ref": "#/definitions/scalar"}, {"$ref": "#/definitions/pool"}],
        scalar=SCALAR,
        pool=POOL,
    )

    class ClosesTheRoot(BaseModel):
        """a binding"""

        model_config = ConfigDict(extra="forbid")

    res = root_graded(root, ClosesTheRoot)
    assert "/additionalProperties" in keys(res.added), res.added
    assert "/type" not in keys(res.added), res.added

    class RequiresAKeyTheRootDoesNot(BaseModel):
        """a binding"""

        k: str

    other = root_graded(root, RequiresAKeyTheRootDoesNot)
    assert "/required" in keys(other.added), other.added
    assert "/properties/k" in keys(other.added), other.added


def test_the_hop_is_taken_against_whichever_root_it_is_handed() -> None:
    """ONE function, BOTH sides -- §9's "each is applied to both sides".

    ``_normalize`` is called once per side with that side's own root: the document for
    the document, ``model_json_schema()`` for the model.  pydantic names a nested class
    ``{"$ref": "#/$defs/X"}`` and ``bundle.record`` leaves a local ``#/definitions/X``
    as written, so the branch is the same spelling against two different sections --
    and the hop is the root's pointer walk, so it reads either.
    """
    from codegen.harness import _normalize  # noqa: PLC0415

    document_side = {"oneOf": [{"$ref": "#/definitions/t"}], "definitions": {"t": SCALAR}}
    model_side = {"anyOf": [{"$ref": "#/$defs/T"}], "$defs": {"T": SCALAR}}
    assert _normalize(document_side, document_side)["oneOf"] == [SCALAR]
    assert _normalize(model_side, model_side)["anyOf"] == [SCALAR]


def test_a_branch_reference_to_a_bare_type_folds_to_the_type_list_it_spells() -> None:
    """The ONE shape the hop can hand to a fold arm, and it has **0 sites**.

    A resolved branch that is exactly ``{"type": X}`` reaches the type-list arm, which
    the branch as written could not. That is the right answer -- a value has exactly one
    JSON type, so ``oneOf: [string, integer]`` and ``type: ["string", "integer"]`` admit
    the same instances -- but it is an answer this reading newly makes reachable, so it
    is asserted rather than discovered. Measured over the records of all 1,054 portable
    documents: of the 33 union branches that are a local ``$ref``, the targets' key sets
    are ``{const, type}`` (21), ``{additionalProperties, properties, required, type}``
    (5), ``{additionalProperties, description, properties, required, type}`` (4) and
    ``{oneOf}`` (3) -- **none is ``{type}``**, so the cell is empty on this tree.

    And it excuses nothing: a model listing FEWER types than the folded list still
    reports, which is the half that keeps the arm honest.
    """
    from codegen.harness import _normalize  # noqa: PLC0415

    root = {
        "oneOf": [{"$ref": "#/definitions/s"}, {"type": "integer"}],
        "definitions": {"s": {"type": "string"}},
    }
    assert _normalize(root, root, declared_null=True)["type"] == ["string", "integer"]

    class StatesOneOfTheTwo(BaseModel):
        v: str

    res = compare_schema(root, StatesOneOfTheTwo, document=root)
    assert "/type" in keys(res.differs), res

    # The draft-07 overlap is still refused, through a reference as well as inline:
    # ``integer`` and ``number`` both admit ``5``, so this ``oneOf`` refuses every
    # integer and the type list would admit it.
    overlap = {
        "oneOf": [{"$ref": "#/definitions/n"}, {"type": "integer"}],
        "definitions": {"n": {"type": "number"}},
    }
    assert "type" not in _normalize(overlap, overlap, declared_null=True)


def test_the_bundles_union_branch_references_are_counted_by_shape() -> None:
    """Every site the hop can fire at, enumerated off the records BY SHAPE, with the
    one site where it changes an answer named and the empty shapes named too.

    The standard ``adcp-client-python-10l.18`` set: a reading whose population nobody
    split can quietly cover something it was never shown. So this walks the document of
    record of every portable document, finds every union branch that is a ``$ref``, and
    says what the hop does at each.

    **The record and not the raw bundle**, because the record is what the comparison
    reads -- and the difference is the point: ``bundle.record`` inlines a REMOTE
    reference, and resolves the inlined document's own local pointers while doing it, so
    a record carries **0** remote union branches where the raw bundle carries 201 over 47
    documents, and a referrer's inlined copy of a union root carries none of the
    target's local ones. The 33 local sites are therefore the whole population, and they
    sit in the 6 documents that WRITE them.
    """
    from codegen.harness import _branch_target, _entails_type  # noqa: PLC0415

    kinds = ("string", "object", "integer", "number", "boolean", "array", "null")
    local: dict[tuple[str, str], str | None] = {}
    remote: set[tuple[str, str]] = set()
    siblinged: set[tuple[str, str]] = set()
    chained: set[tuple[str, str]] = set()
    bare_typed: set[tuple[str, str]] = set()
    changed: set[tuple[str, str, str]] = set()

    def visit(node: Any, pointer: str, document: str, root: Any) -> None:
        if isinstance(node, dict):
            for kw in ("oneOf", "anyOf"):
                branches = node.get(kw)
                if not (isinstance(branches, list) and branches):
                    continue
                refs = [
                    (i, b)
                    for i, b in enumerate(branches)
                    if isinstance(b, dict) and isinstance(b.get("$ref"), str)
                ]
                for i, b in refs:
                    at = (document, f"{pointer}/{kw}/{i}")
                    if not b["$ref"].startswith("#"):
                        remote.add(at)
                        continue
                    if set(b) != {"$ref"}:
                        siblinged.add(at)
                    target = _branch_target(b, root)
                    local[at] = target.get("type") if target is not b else None
                    if target is not b and set(target) == {"$ref"}:
                        chained.add(at)
                    if target is not b and set(target) == {"type"}:
                        bare_typed.add(at)
                if not refs:
                    continue
                hopped = {**node, kw: [_branch_target(b, root) for b in branches]}
                for kind in kinds:
                    if _entails_type(hopped, kind) != _entails_type(node, kind):
                        changed.add((document, pointer, kind))
            for key, value in node.items():
                visit(value, f"{pointer}/{key}", document, root)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                visit(value, f"{pointer}/{i}", document, root)

    documents = claimed("bundle.portable", bundle.portable(BUNDLE))
    for document in sorted(documents):
        record = bundle.record(BUNDLE, document)
        if isinstance(record, Refusal):
            continue
        visit(record, "", document, record)

    sites = claimed("union branches that are a local $ref, in a record", set(local))
    # **BY SHAPE, and the shape is the target's own ``type`` word** -- which is what the
    # derivation asks each branch for, so it is the axis that decides what the hop does.
    partitions(
        sites,
        typed_boolean={a for a in sites if local[a] == "boolean"},
        typed_object={a for a in sites if local[a] == "object"},
        states_no_type={a for a in sites if local[a] is None},
    )
    # 21 sites in the two refused ``targeting-overlay-*`` documents, whose other branch
    # is an object: resolved, the branches disagree and the derivation still answers
    # ``False``.  3 sites in ``governance/reported-outcome-error.json``, whose target's
    # own content is a ``oneOf`` and so states no ``type`` word: one hop leaves the
    # derivation at ``False``, which is the fail-safe answer.  9 sites typed ``object``,
    # of which exactly one is at a ROOT.
    assert {d for d, _ in sites} == {
        "core/bidding-policy-capability.json",
        "core/placement-presentation.json",
        "core/requirements/catalog-field-binding.json",
        "core/targeting-overlay-requirements.json",
        "core/targeting-overlay-support.json",
        "governance/reported-outcome-error.json",
    }, sorted({d for d, _ in sites})
    # **EVERY NODE WHERE THE HOP CHANGES THE DERIVATION'S ANSWER**, derived by asking it
    # both ways at every union node that carries a local-``$ref`` branch rather than
    # read off the one pair that reddened.  FOUR nodes, all of them answering ``object``
    # where they answered nothing, and the list is named so a fifth reddens here with
    # its pointer.
    assert changed == {
        ("core/bidding-policy-capability.json", "/definitions/policy_profile/properties/supported_combinations/items", "object"),
        ("core/placement-presentation.json", "/properties/decorations/items", "object"),
        ("core/requirements/catalog-field-binding.json", "", "object"),
        ("core/requirements/catalog-field-binding.json", "/oneOf/2/properties/per_item_bindings/items", "object"),
    }, sorted(changed)
    # **AND ONE OF THE FOUR IS EVER ASKED, which is §4's doing and not this reading's.**
    # The derivation answers a MODEL-ONLY ``type``, so it is reached only where the
    # model states one: §5 compiles a union at ROOT to a base plus a class per branch,
    # and the base is a pydantic model that renders ``type: object``, while a NESTED
    # union compiles to one type ``A | B``, whose alias renders an ``anyOf`` and no
    # ``type`` at all.  The three nested nodes above therefore have no model-side
    # ``type`` for the derivation to excuse, and the one root does.  Measured through
    # ``compare_schema`` over the graded population: the union arm decides at 221 pairs
    # with the hop and 220 without, and the one pair is this root.
    partitions(
        changed,
        at_a_root={c for c in changed if c[1] == ""},
        at_a_nested_union={c for c in changed if c[1] != ""},
    )
    assert {c for c in changed if c[1] == ""} == {
        ("core/requirements/catalog-field-binding.json", "", "object")
    }, sorted(changed)
    # **THE SHAPES EXCLUDED, BY NAME AND AT ZERO SITES.**  Each is a cell the gate keeps
    # the hop out of, and each is empty on this tree -- so none of them is what makes
    # the one site above green, and a document arriving in one of them reddens here
    # rather than being covered silently.
    assert remote == set(), sorted(remote)  # record inlines every remote reference
    assert siblinged == set(), sorted(siblinged)  # 0 of 33 carry a key beside the $ref
    assert chained == set(), sorted(chained)  # 0 targets are themselves a bare $ref
    assert bare_typed == set(), sorted(bare_typed)  # 0 targets are exactly {"type": X}
