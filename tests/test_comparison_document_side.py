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

from typing import Annotated, Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from codegen.harness import ComparisonResult, Pair, check_pair, compare_schema

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
#: THE SAME TWO UNIONS AS A REFERENCING DOCUMENT CARRIES THEM.  The resolver
#: writes a finite type out as its members while inlining, so a document that
#: references one of the shapes above states its boolean branch as
#: ``{"enum": [false, true]}`` and its null branch as ``{"const": null}``.
#: Measured: the fold fired on the 2 documents that STATE
#: ``creative/creative-feature-result.json#/properties/value`` and on none of the
#: 3 that reference it, and those 3 reported the model's type list as ``added``.
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
def test_the_fold_reads_a_branch_the_resolver_rewrote(node: dict, model: Any) -> None:
    """A referencing document spells the same union differently, and the fold has
    to read both -- or it fires on the documents that STATE a shape and not on the
    ones that reference it, which is the reading half-done.

    The restoration is the third canonicalization (``_uncanonicalized``) applied
    to the BRANCH, not a new rule: ``enum: [false, true]`` IS ``type: boolean``
    and ``const: null`` IS ``type: null``, same accepted set either way.
    """
    res = graded(holder(node), model)
    assert (res.added, res.missing, res.differs) == ([], [], []), res
    assert res.outcome == "pass", res


def test_a_rewritten_branch_does_not_make_the_fold_a_licence() -> None:
    """The restoration folds the two shapes the resolver writes and NOTHING else.

    A one-member ``enum`` and a three-member one are not finite TYPES, so a union
    carrying either is left alone and a model stating a type list over it is
    reported -- which is what keeps this from excusing a model that invented a
    type.
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

    with_root = check_pair(Pair("holder", node, Faithful, accept, document=root), max_steps=0)
    assert with_root.comparison is not None
    assert with_root.comparison.added == [], with_root.comparison.added
    assert with_root.comparison.outcome == "pass", with_root.comparison

    without = check_pair(Pair("holder", node, Faithful, accept), max_steps=0)
    assert without.comparison is not None
    assert without.comparison.added, "the default must not resolve a sibling definition"


def test_a_const_at_a_named_node_is_a_rendering_question_and_is_not_silenced() -> None:
    """The symptom ``salesagent-j3k2l.33`` names as SEPARATE, pinned as separate.

    The document states ``const: X`` at a property and the compiler declares a
    one-member ENUM class for it (``compiler.name_the_node``), so the comparison
    reports one ``missing`` const and one ``added`` enum.  That is reachable only
    through the documents these two readings unlock, and it is a question about
    what the emitter RENDERS -- so neither reading here may make it go quiet.

    This is the test that fails if a later widening of the document-side reading
    buys that pair's green by excusing a model-only ``enum``.
    """
    root = document({"const": "x"}, {"type": "string"})

    class OneMemberEnum(Base):
        v: Literal["x"]

    class Enumerated(Base):
        v: Annotated[str, Field(json_schema_extra={"enum": ["x"]})]

    # A `Literal` renders `const` AND `type`, so it agrees -- the rendering that
    # does not agree is the one that names the node as an enumeration.
    assert graded(root, OneMemberEnum).outcome == "pass", graded(root, OneMemberEnum)

    res = graded(root, Enumerated)
    assert "/properties/v/const" in keys(res.missing), res.missing
    assert "/properties/v/enum" in keys(res.added), res.added
