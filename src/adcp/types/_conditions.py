"""The vocabulary compiled root constraints are written in.

A schema root states more than its merged ``properties``: a root
``anyOf``/``oneOf`` over overlay arms, a root ``if``/``then``/``else``, root
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

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

__all__ = [
    "absent",
    "descend",
    "every",
    "json_type",
    "keys",
    "length",
    "matches",
    "matching_keys",
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

#: JSON type names, and the Python instances that answer to them. ``integer``
#: excludes ``bool``, which is a subclass of ``int`` in Python and a separate
#: type in JSON.
_JSON_TYPES: dict[str, Callable[[Any], bool]] = {
    "object": lambda value: isinstance(value, Mapping) or _is_model(value),
    "array": lambda value: isinstance(value, (list, tuple)),
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
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
    if isinstance(value, Mapping):
        return list(value)
    if _is_model(value):
        return list(value.model_fields_set) + list(getattr(value, "model_extra", None) or ())
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

    A generated class normally declares more fields than one arm's
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
    """``minLength``/``maxLength``, ``minItems``/``maxItems``, ``min``/``maxProperties``.

    All six are bounds on a size, differing only in the type they grade -- and
    each is vacuous off its own type, which a single ``len`` test over anything
    sized reproduces exactly.
    """
    try:
        size = len(value)
    except TypeError:
        return True
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


def absent(data: Any, names: Sequence[str]) -> Any:
    """``not: {required: [...]}``: the document may not carry these keys at all.

    A branch class does not DECLARE a field its arm forbids, which is what
    makes the combination unspellable at construction. It is not what refuses
    a raw document: the generated models are ``extra='allow'`` where their
    schemas say ``additionalProperties: true``, so pydantic would file the key
    under extras and accept. So the shape's forbidden names are refused here,
    before validation, on the document as sent.

    Presence is the key being there -- with any value, an explicit null
    included -- which is exactly what ``required`` asks and therefore exactly
    what its negation forbids. Returned unchanged when the document carries
    none of them, and when it is not a mapping at all (a model being
    revalidated has already been through this).
    """
    if not isinstance(data, Mapping):
        return data
    carried = sorted(name for name in names if name in data)
    if carried:
        offending = ", ".join(carried)
        raise ValueError(f"{offending} is not accepted by this request shape")
    return data
