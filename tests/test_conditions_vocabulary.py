"""One test per primitive in the compiled-condition vocabulary.

These are the exception the design names to "no unit tests for behaviour a
parity case can grade": the primitives are pure functions over one value, the
parity corpus grades their COMPOSITION on real documents, and the two
conventions they share -- presence as ``model_fields_set`` membership, and
vacuity off-type -- are exactly where a semantic slip between a compiled
predicate and JSON Schema would land first.

Each test states the keyword the primitive carries, the satisfied case, the
refused case, and the vacuous case. A primitive with no vacuity to state says
so.
"""

from __future__ import annotations

import datetime
import decimal
import inspect
import ipaddress
import types
import uuid
from typing import Any

import pytest
from pydantic import AnyUrl, BaseModel, ConfigDict

from adcp.types import _conditions as c


class _Nested(BaseModel):
    mode: str | None = None
    scale: int | None = None


class _Subject(BaseModel):
    """A model whose defaults are deliberately not ``None``.

    That is what separates "the caller supplied this" from "this is not None":
    ``pacing`` reads as set under an ``is None`` guard even when the document
    never carried it.
    """

    packages: list[str] | None = None
    proposal_id: str | None = None
    pacing: str = "even"
    nested: _Nested | None = None


class _Open(BaseModel):
    model_config = ConfigDict(extra="allow")

    declared: int | None = None


def test_supplied_is_membership_not_a_null_check() -> None:
    """``required``: the document carried the property.

    The three cases that separate membership from every other spelling: a
    default the caller never sent is NOT supplied even though it is not None,
    an explicit null IS supplied, and an absent nullable field is not.
    """
    subject = _Subject.model_validate({"packages": ["pkg_1"], "proposal_id": None})

    assert c.supplied(subject, "packages")
    assert c.supplied(subject, "proposal_id"), "an explicit null is a supplied value"
    assert not c.supplied(subject, "pacing"), "a default the caller never sent is not supplied"
    assert not c.supplied(subject, "nested")


def test_sent_is_membership_plus_the_non_null_half() -> None:
    """Presence on the document that is SENT, for a position forbidding null.

    ``supplied`` is membership and is the right reading where the schema marks
    the position nullable. Where it does not, the client's ``exclude_none``
    drops a null-valued key and ``preserve_explicit_nulls`` restores only
    nullable paths, so the document that arrives does not carry it --
    ``control-media-buy-request``'s ``canceled`` is ``Literal[True]`` and
    ``canceled=None`` is dropped on the way out. Reading it as present refused
    a request no seller receives.

    It stays membership-based: the default the caller never sent is absent
    because it is not in ``model_fields_set``, not because of its value.
    """
    subject = _Subject.model_validate({"packages": ["pkg_1"], "proposal_id": None})

    assert c.sent(subject, "packages")
    assert not c.sent(subject, "proposal_id"), "an explicit null is not sent at a closed position"
    assert c.supplied(subject, "proposal_id"), "and supplied still answers membership"
    assert not c.sent(subject, "pacing"), "a default the caller never sent is not sent"
    assert not c.sent("not an object", "packages")


def test_absent_refuses_a_key_the_shape_forbids_and_passes_everything_else() -> None:
    """``not: {required: [x]}`` on a branch class, at wire validation.

    A branch class types a field its arm forbids as ``None``, which is what
    makes the combination unspellable at construction. Under ``extra='allow'``
    that is not what refuses a raw document, so the forbidden names are refused
    here -- and presence is read the way ``sent`` reads it, because the negation
    of ``required`` is about the same document. At a position the schema forbids
    null, the client drops a null-valued key, so only a non-null value is
    carried; at a nullable position a null survives and its presence is what
    the ban forbids. A document carrying none of them, and anything that is not
    a mapping, pass through unchanged.
    """
    assert c.absent({"packages": ["pkg_1"]}, ["proposal_id"]) == {"packages": ["pkg_1"]}
    assert c.absent("not an object", ["proposal_id"]) == "not an object"
    assert c.absent({"proposal_id": None}, ["proposal_id"]) == {
        "proposal_id": None
    }, "a null at a position forbidding null never reaches the document sent"

    with pytest.raises(ValueError, match="proposal_id is not accepted"):
        c.absent({"packages": [], "proposal_id": "prop_1"}, ["proposal_id"])

    with pytest.raises(ValueError, match="daily_budget_cap is not accepted"):
        c.absent({"daily_budget_cap": None}, [], ["daily_budget_cap"])

    with pytest.raises(ValueError, match="budget_allocation, packages"):
        c.absent({"packages": [1], "budget_allocation": {}}, ["packages", "budget_allocation"])


def test_supplied_reads_a_mapping_by_its_keys() -> None:
    """An open payload reaches a predicate as a mapping, not a model."""
    assert c.supplied({"a": None}, "a")
    assert not c.supplied({"a": None}, "b")
    assert not c.supplied("not an object", "a")


def test_descend_is_vacuous_for_a_member_the_document_did_not_carry() -> None:
    """``properties`` grades present object members only -- including a null one.

    An arm constraining ``nested.mode`` says nothing about a request that sent
    no ``nested`` at all. It does say something about one that sent ``null``:
    JSON Schema applies the subschema to whatever value is there, and a
    subschema expecting an object is false for ``null``. Reading the null as
    vacuous instead let ``creative-manifest.json``'s audio-VAST conjunct fire
    on a manifest whose ``format_kind`` was null, refusing a document under a
    rule the schema does not apply to it.
    """
    predicate = lambda value: getattr(value, "mode", None) == "fixed"  # noqa: E731

    assert c.descend(_Subject.model_validate({"nested": {"mode": "fixed"}}), "nested", predicate)
    assert not c.descend(
        _Subject.model_validate({"nested": {"mode": "seller_optimized"}}), "nested", predicate
    )
    assert c.descend(_Subject(), "nested", predicate), "absent is unconstrained"
    assert not c.descend(
        _Subject.model_validate({"nested": None}), "nested", predicate
    ), "an explicit null is a value the subschema grades, and this one fails it"
    # And a predicate JSON Schema reads as vacuous off-type stays vacuous on a
    # null, which is what keeps the composition faithful rather than strict.
    assert c.descend(
        _Subject.model_validate({"nested": None}), "nested", lambda value: c.matches(value, "^x")
    )


def test_every_grades_each_element_and_nothing_else() -> None:
    """``items``."""
    assert c.every([2, 4], lambda value: value % 2 == 0)
    assert not c.every([2, 3], lambda value: value % 2 == 0)
    assert c.every([], lambda value: False), "an empty array satisfies items"
    assert c.every("not an array", lambda value: False)


def test_some_grades_whether_one_element_matches() -> None:
    """``contains``."""
    assert c.some([1, 2], lambda value: value == 2)
    assert not c.some([1, 3], lambda value: value == 2)
    assert not c.some([], lambda value: True), "an empty array contains nothing"
    assert c.some(None, lambda value: False)


def test_keys_grades_the_member_names() -> None:
    """``propertyNames``."""
    assert c.keys({"ab": 1, "ac": 2}, lambda name: name.startswith("a"))
    assert not c.keys({"ab": 1, "zz": 2}, lambda name: name.startswith("a"))
    assert c.keys(7, lambda name: False)


def test_matching_keys_grades_only_the_matching_members() -> None:
    """``patternProperties``."""
    assert c.matching_keys({"x_a": 1, "other": "text"}, "^x_", lambda value: value == 1)
    assert not c.matching_keys({"x_a": 2, "other": "text"}, "^x_", lambda value: value == 1)
    assert c.matching_keys({"other": "text"}, "^x_", lambda value: False)


def test_only_bounds_what_the_caller_supplied() -> None:
    """``additionalProperties: false``.

    The bound is on what the document carried, not on what the class declares:
    a class normally has more fields than one arm's ``properties`` names, and a
    field the caller left out is not an additional property.
    """
    assert c.only(_Subject.model_validate({"packages": []}), ["packages", "proposal_id"])
    assert not c.only(_Subject.model_validate({"packages": [], "proposal_id": "p"}), ["packages"])
    assert not c.only(
        _Open.model_validate({"declared": 1, "undeclared": 2}), ["declared"]
    ), "a key the model carried through is supplied"
    assert c.only("not an object", [])


def test_others_grades_the_unnamed_members() -> None:
    """``additionalProperties: <schema>``, which is how a map type is spelled."""
    assert c.others({"a": "pass", "b": "fail"}, [], lambda value: value in {"pass", "fail"})
    assert not c.others({"a": "pass", "b": "x"}, [], lambda value: value in {"pass", "fail"})
    assert c.others({"a": "x"}, ["a"], lambda value: False), "a named member is exempt"


@pytest.mark.parametrize(
    ("value", "names", "expected"),
    [
        ("text", ("string",), True),
        (1, ("string",), False),
        (True, ("integer",), False),
        (True, ("boolean",), True),
        (1, ("number",), True),
        (1.5, ("integer",), False),
        ([], ("array",), True),
        ({}, ("object",), True),
        (_Subject(), ("object",), True),
        (None, ("null",), True),
        ("text", ("integer", "string"), True),
        # A compiled ``type`` check runs AFTER validation, so the value it sees
        # is what pydantic parsed, not what the document carried. Every one of
        # these arrived as a JSON string.
        (datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC), ("string",), True),
        (datetime.date(2026, 1, 1), ("string",), True),
        (datetime.timedelta(seconds=5), ("string",), True),
        (uuid.UUID(int=1), ("string",), True),
        (AnyUrl("https://seller.example"), ("string",), True),
        (ipaddress.IPv4Address("10.0.0.1"), ("string",), True),
        # And a JSON number can arrive as a Decimal, which is neither int nor
        # float -- so defining "string" by excluding the other five JSON types
        # would call this one a string.
        (decimal.Decimal("2.5"), ("number",), True),
        (decimal.Decimal("2.5"), ("string",), False),
        (decimal.Decimal("2.5"), ("integer",), False),
        (decimal.Decimal("2"), ("integer",), True),
    ],
)
def test_json_type_answers_the_json_type_names(
    value: Any, names: tuple[str, ...], expected: bool
) -> None:
    """``type``, including the Python-versus-JSON mismatches.

    ``bool`` is a subclass of ``int`` in Python and a separate type in JSON, and
    a pydantic model is a JSON object without being a mapping.

    The third mismatch is the one that shipped broken: a ``format``-bearing
    string field is a ``datetime`` or an ``AnyUrl`` by the time the check runs,
    so an ``isinstance(value, str)`` test is false for every document and the
    model refuses what its schema accepts. Seven fields over six modules were in
    that state on the pin -- ``reporting-revision``'s ``data_through`` among
    them, which made ``tests/test_reporting_consumer_loop.py`` fail at
    COLLECTION.
    """
    assert c.json_type(value, *names) is expected


def test_matches_is_an_unanchored_search() -> None:
    """``pattern``: JSON Schema specifies a partial match, not a full one."""
    assert c.matches("prefix-mid-suffix", "mid")
    assert not c.matches("prefix", "mid")
    assert c.matches(7, "mid"), "pattern says nothing about a non-string"


@pytest.mark.parametrize(
    ("value", "bounds", "expected"),
    [
        ("abc", {"minimum": 3}, True),
        ("ab", {"minimum": 3}, False),
        ([1, 2, 3], {"maximum": 2}, False),
        ([1, 2], {"maximum": 2}, True),
        ({"a": 1}, {"minimum": 1, "maximum": 1}, True),
        ({}, {"minimum": 1}, False),
        (7, {"minimum": 1}, True),
    ],
)
def test_length_bounds_anything_sized_and_nothing_else(
    value: Any, bounds: dict[str, int], expected: bool
) -> None:
    """``minLength``/``maxLength``, ``minItems``/``maxItems``, ``min``/``maxProperties``."""
    assert c.length(value, **bounds) is expected


@pytest.mark.parametrize(
    ("value", "bounds", "expected"),
    [
        (0, {"ge": 0}, True),
        (-1, {"ge": 0}, False),
        (0, {"gt": 0}, False),
        (100, {"le": 100}, True),
        (101, {"le": 100}, False),
        (1, {"lt": 1}, False),
        (True, {"ge": 5}, True),
        ("5", {"ge": 5}, True),
    ],
)
def test_within_bounds_only_numbers(value: Any, bounds: dict[str, float], expected: bool) -> None:
    """``minimum``/``maximum``/``exclusiveMinimum``/``exclusiveMaximum``.

    ``True`` is excluded on purpose: it is an ``int`` subclass in Python and a
    boolean in JSON, so a numeric bound says nothing about it.
    """
    assert c.within(value, **bounds) is expected


def test_unique_compares_unhashable_elements() -> None:
    """``uniqueItems``, over the array of objects that is the common case."""
    assert c.unique([{"a": 1}, {"a": 2}])
    assert not c.unique([{"a": 1}, {"a": 1}])
    assert c.unique([])
    assert c.unique("not an array")


def test_every_primitive_the_vocabulary_exports_is_graded_here() -> None:
    """A primitive the generator can emit but nothing grades would be a hole.

    Both halves are derived: the export list against what the module defines,
    and the export list against which primitives the tests above actually call.
    """
    defined = {
        name
        for name, value in vars(c).items()
        if not name.startswith("_")
        and isinstance(value, types.FunctionType)
        and value.__module__ == c.__name__
    }
    assert defined == set(c.__all__)
    graded = {
        name
        for test in globals()
        if test.startswith("test_")
        for name in c.__all__
        if f"c.{name}(" in inspect.getsource(globals()[test])
    }
    assert graded == set(c.__all__), sorted(set(c.__all__) - graded)


def test_name_the_combinator_names_the_keyword_and_keeps_the_fields() -> None:
    """The wrapper a split root's union carries.

    A document that satisfies no branch fails each branch at FIELD validation,
    so pydantic reports ``missing`` and nothing names the root's combinator.
    ``core/error.json`` requires a keyword drawn from the JSON Schema
    vocabulary, so the wrapper supplies one -- and carries the absent field
    names with it, in the message and in the error context, so the refusal says
    more than the keyword alone.
    """
    from typing import Annotated, TypeAlias

    from pydantic import BaseModel, TypeAdapter, ValidationError, WrapValidator

    class Shape(BaseModel):
        a: str | None = None
        b: str | None = None

    class First(Shape):
        a: str
        b: None = None

    class Second(Shape):
        b: str
        a: None = None

    Wrapped: TypeAlias = Annotated[First | Second, WrapValidator(c.name_the_combinator("anyOf"))]
    adapter: TypeAdapter[First | Second] = TypeAdapter(Wrapped)

    with pytest.raises(ValidationError) as refusal:
        adapter.validate_python({})
    errors = refusal.value.errors()
    assert [error["type"] for error in errors] == ["anyOf"]
    assert errors[0]["ctx"] == {"fields": "a, b"}
    assert "one of these is required: a, b" in errors[0]["msg"]

    # The success path is untouched: a document that satisfies a branch comes
    # back as that branch rather than as the base.
    assert type(adapter.validate_python({"a": "x"})) is First

    # A refusal that is not about an absent field passes through unchanged, so
    # the wrapper never relabels a failure it did not diagnose.
    with pytest.raises(ValidationError) as other:
        adapter.validate_python({"a": 1, "b": 2})
    assert "anyOf" not in {error["type"] for error in other.value.errors()}


def test_name_the_combinator_keeps_a_branchs_content_failure() -> None:
    """A branch that passed its required fields owns the refusal.

    The wrapper names the combinator only when the document satisfies NO
    branch's requiredness. If one branch got past its required fields and then
    failed on content -- a bound, a pattern, a nested rule -- that failure is
    the informative one, and replacing it with ``anyOf`` would discard the only
    error telling the caller what is wrong. Pydantic re-wraps a raise from
    inside a validator, so the original is not recoverable afterwards either.
    """
    from typing import Annotated, TypeAlias

    from pydantic import BaseModel, Field, TypeAdapter, ValidationError, WrapValidator

    class Shape(BaseModel):
        a: str | None = None
        b: str | None = None

    class First(Shape):
        a: Annotated[str, Field(min_length=5)]

    class Second(Shape):
        b: str

    Wrapped: TypeAlias = Annotated[First | Second, WrapValidator(c.name_the_combinator("anyOf"))]
    adapter: TypeAdapter[First | Second] = TypeAdapter(Wrapped)

    # ``a`` is supplied, so First passes requiredness and fails on the bound;
    # Second reports ``b`` missing. The bound is what the caller needs.
    with pytest.raises(ValidationError) as refusal:
        adapter.validate_python({"a": "xy"})
    types = {error["type"] for error in refusal.value.errors()}
    assert "string_too_short" in types, refusal.value.errors()
    assert "anyOf" not in types, "a branch's content failure was replaced by the keyword"

    # And a document satisfying no branch's requiredness still names the keyword.
    with pytest.raises(ValidationError) as none_matched:
        adapter.validate_python({})
    assert [error["type"] for error in none_matched.value.errors()] == ["anyOf"]
