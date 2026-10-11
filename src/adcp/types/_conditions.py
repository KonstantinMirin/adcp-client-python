"""The vocabulary compiled root constraints are written in.

A schema root states more than its merged ``properties``: a root
``anyOf``/``oneOf`` over overlay branches, a root ``if``/``then``/``else``, root
``dependencies``, a root ``not``. ``scripts/schema_constraints.py`` reads that
content and the generator compiles it into a ``model_validator`` on the class,
as compositions of the primitives below. Nothing here is generated; every
function is a few lines, and each is graded one by one by
``tests/test_conditions_vocabulary.py``.

Two conventions run through all of them, and both are measured rather than
chosen.

**Presence is ``model_fields_set`` membership.** ``required`` asks whether the
document carries the property. An explicit null is a supplied value -- on an
AdCP 3.2 mutation input it is the command to clear a stored value -- and a
default the caller never sent is not. The alternatives were measured and both
are wrong: an ``is None`` guard is correct only when the field's default happens
to be ``None``, because a non-None default makes it false for an absent field
and the check over-refuses; and an unguarded attribute read raises on absence
and on an explicit null alike.

**Every predicate is vacuous off-type.** JSON Schema applies a keyword only to
instances of the type it grades: ``minLength`` says nothing about a number,
``properties`` grades present object members only, ``items`` says nothing about
a non-array. So a primitive handed a value of the wrong shape returns ``True``.
That is the schema's own reading, and it is what lets the generator compile a
nested predicate without first resolving the nested annotation.
"""

from __future__ import annotations

import datetime
import decimal
import ipaddress
import pathlib
import re
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from pydantic import AnyUrl, ValidationError

__all__ = [
    "branch_title",
    "name_the_combinator",
    "absent",
    "descend",
    "every",
    "json_type",
    "keys",
    "length",
    "matches",
    "matching_keys",
    "members",
    "only",
    "others",
    "sent",
    "some",
    "supplied",
    "unique",
    "within",
]

#: What a predicate over one value looks like.
Predicate = Callable[[Any], bool]

#: Python types a JSON STRING arrives as once pydantic has parsed it. A
#: compiled ``type`` check runs after validation, so ``isinstance(value, str)``
#: alone is false for every ``format``-bearing string field -- the model then
#: refuses a document its schema accepts, permanently and silently.
#:
#: Measured on the pin: seven fields over six modules were in exactly that
#: state -- ``reporting-revision``'s ``data_through``, ``search-brands-response``'s
#: ``relationship_verified_at`` and its logo ``url``, and four ``timestamp``
#: fields -- each annotated ``AwareDatetime`` or ``AnyUrl`` and each carrying a
#: root ``type: "string"`` rule it could never satisfy.
#:
#: Enumerated rather than defined by exclusion. "Not object, array, number,
#: boolean or null, therefore string" is true of JSON and wrong here, because
#: a JSON NUMBER also arrives as a non-``float``: pydantic parses one into
#: ``Decimal`` where the field says so, and exclusion would call that a string.
_STRING_BACKED = (
    str,
    datetime.datetime,
    datetime.date,
    datetime.time,
    datetime.timedelta,
    uuid.UUID,
    AnyUrl,
    pathlib.PurePath,
    ipaddress.IPv4Address,
    ipaddress.IPv6Address,
)

#: Python types a JSON NUMBER arrives as. ``Decimal`` is neither ``int`` nor
#: ``float``, and a field declared with a multiple-of or a money precision gets
#: one.
_NUMBER_BACKED = (int, float, decimal.Decimal)

#: JSON type names, and the Python instances that answer to them. ``integer``
#: excludes ``bool``, which is a subclass of ``int`` in Python and a separate
#: type in JSON.
_JSON_TYPES: dict[str, Callable[[Any], bool]] = {
    "object": lambda value: isinstance(value, Mapping) or _is_model(value),
    "array": lambda value: isinstance(value, (list, tuple)),
    "string": lambda value: isinstance(value, _STRING_BACKED),
    "integer": lambda value: isinstance(value, (int, decimal.Decimal))
    and not isinstance(value, bool)
    and int(value) == value,
    "number": lambda value: isinstance(value, _NUMBER_BACKED) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "null": lambda value: value is None,
}


def _is_model(value: Any) -> bool:
    return hasattr(value, "model_fields_set")


def supplied(value: Any, name: str) -> bool:
    """Whether the document carried ``name`` on ``value``.

    A pydantic model answers from ``model_fields_set``, which holds the fields
    the caller actually set; a mapping -- an open payload the models carry
    through unmodelled -- answers from its keys.
    """
    if _is_model(value):
        return name in value.model_fields_set
    if isinstance(value, Mapping):
        return name in value
    return False


def sent(value: Any, name: str) -> bool:
    """Whether ``name`` would be PRESENT on the document that is sent.

    ``supplied`` answers membership, which is the whole question at a position
    the schema marks nullable: there an explicit null is the caller's value and
    the client keeps the key. Where the schema does NOT permit null, the client
    drops the key -- ``model_dump(exclude_none=True)`` removes it and
    ``preserve_explicit_nulls`` restores only nullable paths -- so a null-valued
    field is absent from what is sent, and a constraint reading it as present
    refuses a request no seller receives.

    Still membership, not an ``is None`` test: a default the caller never sent
    is absent because it is not in ``model_fields_set``, whatever its value.
    """
    return supplied(value, name) and _member(value, name) is not None


def _member(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def descend(value: Any, name: str, predicate: Predicate) -> bool:
    """Apply ``predicate`` to a supplied member of ``value``.

    Vacuous when the member was NOT SUPPLIED, because ``properties`` grades
    present object members and says nothing about a missing one. An explicit
    null is supplied, and the subschema applies to it like any other value:
    ``{"properties": {"format_kind": {"const": "audio_vast"}}}`` is false for
    ``{"format_kind": null}``, not vacuous. Each primitive already reads a
    ``None`` the way JSON Schema does -- ``const`` and ``enum`` compare and
    fail, ``type`` answers ``null``, and a bound on a string or an array is
    vacuous off its own type -- so passing the null through is what makes the
    composition match the schema.

    Reading a null as vacuous here was measured wrong on
    ``creative-manifest.json``: its audio-VAST conjunct tests
    ``format_kind == 'audio_vast'``, a manifest carrying
    ``format_kind: null`` satisfied that test vacuously, and the model refused
    the document under a rule its schema does not apply to it.
    """
    if not supplied(value, name):
        return True
    return predicate(_member(value, name))


def every(value: Any, predicate: Predicate) -> bool:
    """``items``: every element satisfies ``predicate``."""
    if not isinstance(value, (list, tuple)):
        return True
    return all(predicate(element) for element in value)


def some(value: Any, predicate: Predicate) -> bool:
    """``contains``: at least one element satisfies ``predicate``."""
    if not isinstance(value, (list, tuple)):
        return True
    return any(predicate(element) for element in value)


def _named_members(value: Any) -> Iterable[str]:
    """The names the document carried, each once.

    pydantic puts an extra a model KEPT into ``model_fields_set`` as well as
    ``model_extra``, so concatenating the two names every extra twice. Four of
    the five callers quantify over these names and cannot see a duplicate;
    :func:`members` lengths them, and for it a duplicate is a wrong count -- an
    open model carrying two members read as three, so ``maxProperties: 2``
    refused a document the schema accepts. Both sources are still read, so a
    name present in only one of them still counts.
    """
    if isinstance(value, Mapping):
        return list(value)
    if _is_model(value):
        extras = getattr(value, "model_extra", None) or ()
        return list(dict.fromkeys([*value.model_fields_set, *extras]))
    return ()


def keys(value: Any, predicate: Predicate) -> bool:
    """``propertyNames``: every member name satisfies ``predicate``."""
    if not (isinstance(value, Mapping) or _is_model(value)):
        return True
    return all(predicate(name) for name in _named_members(value))


def matching_keys(value: Any, pattern: str, predicate: Predicate) -> bool:
    """``patternProperties``: every member whose name matches satisfies it."""
    if not (isinstance(value, Mapping) or _is_model(value)):
        return True
    expression = re.compile(pattern)
    return all(
        predicate(_member(value, name)) for name in _named_members(value) if expression.search(name)
    )


def only(value: Any, names: Sequence[str]) -> bool:
    """``additionalProperties: false``: only ``names`` were supplied.

    A generated class normally declares more fields than one branch's
    ``properties`` names, so this bounds what the caller supplied rather than
    what the class can hold. An extra key the model carried through (an open
    payload) counts as supplied.
    """
    if not (isinstance(value, Mapping) or _is_model(value)):
        return True
    return set(_named_members(value)) <= set(names)


def others(value: Any, names: Sequence[str], predicate: Predicate) -> bool:
    """``additionalProperties: <schema>``: unnamed members satisfy it."""
    if not (isinstance(value, Mapping) or _is_model(value)):
        return True
    permitted = set(names)
    return all(
        predicate(_member(value, name)) for name in _named_members(value) if name not in permitted
    )


def json_type(value: Any, *names: str) -> bool:
    """``type``: the value is an instance of one of the named JSON types."""
    return any(_JSON_TYPES[name](value) for name in names if name in _JSON_TYPES)


def matches(value: Any, pattern: str) -> bool:
    """``pattern``: an unanchored match, which is what JSON Schema specifies."""
    if not isinstance(value, str):
        return True
    return re.search(pattern, value) is not None


def length(value: Any, minimum: int | None = None, maximum: int | None = None) -> bool:
    """``minLength``/``maxLength`` and ``minItems``/``maxItems``.

    Four bounds on a size, differing only in the type they grade -- and each is
    vacuous off its own type, which a single ``len`` test over anything sized
    reproduces exactly.

    NOT ``min``/``maxProperties``, which this docstring used to claim. A pydantic
    object model has no ``__len__``, so those two returned ``True`` for every
    object: the production existed, the renderer pointed here, and nothing was
    graded. They are :func:`members` now, and the split is necessary rather than
    tidy -- adding a model branch HERE would measure a ``RootModel``'s own single
    field against an array's ``minItems``.
    """
    try:
        size = len(value)
    except TypeError:
        return True
    if minimum is not None and size < minimum:
        return False
    return not (maximum is not None and size > maximum)


def members(value: Any, minimum: int | None = None, maximum: int | None = None) -> bool:
    """``minProperties``/``maxProperties``: how many members the document carried.

    The same question :func:`supplied` asks, counted instead of tested: a
    model answers from ``model_fields_set`` plus its extras, a mapping from its
    keys. A default the caller never sent is not a property of the document, for
    the same reason it is not ``supplied``.

    Vacuous off its own type, like every primitive here. A ``RootModel`` does not
    reach this from a root conjunct -- ``flat_root_shape`` returns ``None`` for a
    map or array root, so no root validator is emitted for one, and its count
    renders as a field constraint on the key or element type instead.
    """
    if not (isinstance(value, Mapping) or _is_model(value)):
        return True
    size = len(list(_named_members(value)))
    if minimum is not None and size < minimum:
        return False
    return not (maximum is not None and size > maximum)


def within(
    value: Any,
    ge: float | None = None,
    le: float | None = None,
    gt: float | None = None,
    lt: float | None = None,
) -> bool:
    """``minimum``/``maximum``/``exclusiveMinimum``/``exclusiveMaximum``."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True
    if ge is not None and value < ge:
        return False
    if le is not None and value > le:
        return False
    if gt is not None and value <= gt:
        return False
    return not (lt is not None and value >= lt)


def unique(value: Any) -> bool:
    """``uniqueItems``: no element equals another.

    Quadratic on purpose. A JSON array's elements need not be hashable -- an
    array of objects is the common case here -- so a set cannot do it, and the
    arrays this grades are bounded by their own ``maxItems``.
    """
    if not isinstance(value, (list, tuple)):
        return True
    seen: list[Any] = []
    for element in value:
        if element in seen:
            return False
        seen.append(element)
    return True


def absent(data: Any, names: Sequence[str], nullable_names: Sequence[str] = ()) -> Any:
    """``not: {required: [...]}``: these keys may not reach the document sent.

    A branch class types a field its branch forbids as ``None``, which is what
    makes the combination unspellable at construction. It is not what refuses
    a raw document: the generated models are ``extra='allow'`` where their
    schemas say ``additionalProperties: true``, so pydantic would file an
    undeclared key under extras and accept. So the shape's forbidden names are
    refused here, before validation.

    Presence is read the same way ``sent`` reads it, because the negation of
    ``required`` is about the same document. A name in ``names`` sits at a
    position the schema forbids ``null``, so the client drops a null-valued key
    and only a non-null value is carried. A name in ``nullable_names`` sits at
    a position where a null survives, so its mere presence is what the ban
    forbids.

    Returned unchanged when the document carries none of them, and when it is
    not a mapping at all (a model being revalidated has already been through
    this).
    """
    if not isinstance(data, Mapping):
        return data
    carried = sorted(
        [name for name in names if data.get(name) is not None]
        + [name for name in nullable_names if name in data]
    )
    if carried:
        offending = ", ".join(carried)
        raise ValueError(f"{offending} is not accepted by this request shape")
    return data


def branch_title(branch: type) -> str:
    """The schema title of the branch a branch class was compiled from.

    The emitter opens each branch's docstring with the branch's ``title``, which is
    where schema-derived text rides -- no identifier is invented for it, and the
    title is the only phrase a reader can match against the schema. A branch
    with no docstring falls back to its class name, which is itself derived from
    that title.
    """
    first_line = (branch.__doc__ or "").strip().splitlines()
    return first_line[0].rstrip(".") if first_line else branch.__name__


def name_the_combinator(keyword: str, branches: Sequence[type] = ()) -> Callable[[Any, Any], Any]:
    """Build the wrapping validator a split root's union carries.

    The refusal reads the same whether the root was SPLIT into branch classes or
    left flat with a compiled ``_require_schema_required_group`` validator:
    "requires at least one of these field groups: <title> | <title>". A root
    moving from one mechanism to the other must not change what a reader sees,
    and when the split landed this message did -- which is what
    ``test_create_media_buy_request_requires_one_root_anyof_group`` caught.

    ``core/error.json`` requires every ``issues[]`` entry to carry a ``keyword``
    drawn from the JSON Schema vocabulary, and tells a consumer not to invent
    one. A document that satisfies no branch fails each branch at FIELD
    validation, so pydantic reports ``missing`` and nothing names the root's
    combinator. ``missing`` is not in that vocabulary, so a consumer assembling
    a conformant envelope has nothing valid to put in the field.

    A model validator on the shared base cannot supply it: field validation
    fails first and an after-validator never runs. A wrapper around the UNION
    runs, because it sits where the union's own validation happens.

    The absent field names travel with the keyword, in the message and in the
    error context, so the refusal says more than a bare combinator keyword
    says. The success path is untouched: a document that satisfies a branch
    returns that branch's instance.
    """
    from pydantic_core import PydanticCustomError

    def _wrap(value: Any, handler: Any) -> Any:
        try:
            return handler(value)
        except ValidationError as exc:
            # Group by branch: in a union's errors the first ``loc`` element
            # names the branch that produced them.
            per_branch: dict[str, list[dict[str, Any]]] = {}
            for error in exc.errors():
                if not error["loc"]:
                    return handler(value)
                per_branch.setdefault(str(error["loc"][0]), []).append(dict(error))
            # Relabel ONLY when the document satisfies no branch's requiredness.
            # If one branch got past its required fields and failed on content,
            # that failure is what the caller needs, and replacing it with the
            # combinator keyword would discard the only informative error --
            # pydantic re-wraps a raise from inside a validator, so the original
            # is not recoverable from ``__cause__`` either.
            if not all(
                any(error["type"] == "missing" for error in errors)
                for errors in per_branch.values()
            ):
                raise
            absent = sorted(
                {
                    str(error["loc"][-1])
                    for errors in per_branch.values()
                    for error in errors
                    if error["type"] == "missing" and error["loc"]
                }
            )
            if not absent:
                raise
            groups = " | ".join(branch_title(branch) for branch in branches)
            raise PydanticCustomError(
                keyword,
                "requires at least one of these field groups: {groups}",
                # The absent field names travel beside the titles in the error
                # context, so a consumer can report which keys were missing
                # without parsing the sentence.
                {"groups": groups or ", ".join(absent), "fields": ", ".join(absent)},
            ) from exc

    return _wrap
