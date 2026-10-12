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

**Presence is what the DOCUMENT carries.** ``required`` asks whether the document
carries the property, so ``model_fields_set`` answers it for everything the
caller typed -- and an explicit null is one of those, because on an AdCP 3.2
mutation input it is the command to clear a stored value. It is not the whole
answer, because a default the class EMITS is on the document too, and the
document is all a seller can see: the two dumps are byte-identical, so a
constraint whose verdict differs between them is grading something the wire
cannot express (salesagent-k37fs). So an unset field is asked of the serializer,
which is the only authority on what the class emits -- see :func:`_emitted`.

The alternatives were measured and both are wrong: an ``is None`` guard is
correct only when the field's default happens to be ``None``, because a non-None
default makes it false for an absent field and the check over-refuses; and an
unguarded attribute read raises on absence and on an explicit null alike.

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
import typing
import uuid
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from pydantic import AnyUrl, ValidationError
from pydantic_core import PydanticCustomError, PydanticUndefined
from pydantic_core.core_schema import ErrorType

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
    "integer": lambda value: (
        isinstance(value, (int, decimal.Decimal))
        and not isinstance(value, bool)
        and int(value) == value
    ),
    "number": lambda value: isinstance(value, _NUMBER_BACKED) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "null": lambda value: value is None,
}


def _is_model(value: Any) -> bool:
    return hasattr(value, "model_fields_set")


def _emitted(value: Any, name: str) -> bool:
    """Whether ``value``'s own serialization carries ``name`` the caller did not set.

    The serializer is ASKED rather than the default inspected, because the two
    disagree and only the serializer is right. ``GetMediaBuyDeliveryRequest``
    defaults ``include_window_breakdown`` to ``False`` and its wrap serializer
    drops that field when it is unset beside a ``reporting_revision_id``: the
    default exists, the wire does not carry it, and a constraint reading it as
    present would accept a document the schema refuses. Inspecting the default
    gets that case backwards; one ``model_dump`` gets it right, and gets a
    ``default_factory`` and ``exclude_none`` right with it.

    ``include`` narrows the dump to the one field, so this costs that field's
    serialization and not the model's. Narrowing could only change an answer
    where a serializer decides about THIS field by reading another one out of the
    dict it was handed, so it was checked against all three wrap serializers in
    the tree that drop a field, and the narrowed dump agrees with the full one on
    each: two decide from ``self`` -- ``AdCPBaseModel`` reads ``event_types``, and
    flipping it flips this answer in both directions -- and ``Scope``'s reads only
    the key it is deciding about.

    The default check ahead of it is a cost guard, not the question: a field with
    nothing to emit is dropped by ``exclude_none`` anyway, and that is the common
    case on every optional field. Identity rather than ``in``, because a default
    is an arbitrary object and ``==`` against it is the caller's code.
    """
    fields = getattr(type(value), "model_fields", None)
    info = fields.get(name) if fields else None
    if info is None:
        return False
    if info.default_factory is None and (info.default is None or info.default is PydanticUndefined):
        return False
    return name in value.model_dump(mode="json", exclude_none=True, include={name})


def supplied(value: Any, name: str) -> bool:
    """Whether the document carried ``name`` on ``value``.

    A pydantic model answers from ``model_fields_set`` -- the fields the caller
    actually set -- and then from its serializer, because a default the class
    emits is carried by the document just as a supplied value is. A mapping -- an
    open payload the models carry through unmodelled -- answers from its keys.
    """
    if _is_model(value):
        return name in value.model_fields_set or _emitted(value, name)
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

    Still presence, not an ``is None`` test: :func:`supplied` decides whether the
    document carries the name, and this adds only the non-null half.
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

    A default the class emits is a third source, for the reason :func:`supplied`
    gives: ``core/deadline-policy.json`` states ``minProperties: 1`` and
    ``DeadlinePolicy`` defaults ``business_days_only`` to ``False``, so the empty
    construction dumps one member and ``_c.members`` counted none.

    The declared fields are read through ``getattr``, the same way :func:`_emitted`
    reads them, because :func:`_is_model` is duck-typed: a subject can carry
    ``model_fields_set`` and declare no fields, and then :func:`supplied` answers
    for it while an unguarded ``type(value).model_fields`` raises. Every primitive
    has to answer for every subject the predicate admits.
    """
    if isinstance(value, Mapping):
        return list(value)
    if _is_model(value):
        extras = getattr(value, "model_extra", None) or ()
        declared = getattr(type(value), "model_fields", None) or {}
        unset = (name for name in declared if name not in value.model_fields_set)
        emitted = [name for name in unset if _emitted(value, name)]
        return list(dict.fromkeys([*value.model_fields_set, *extras, *emitted]))
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
    model answers from ``model_fields_set`` plus its extras plus the defaults it
    emits, a mapping from its keys.

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
        # The keyword is the schema construct this compiles, named at the raise
        # site because only the raise site knows it. A bare ``ValueError``
        # reaches pydantic as ``value_error``, which has no JSON Schema
        # equivalent, so the projection falls back to ``validation`` -- and
        # ``core/error.json`` requires every ``issues[]`` entry's keyword to be
        # "drawn from the JSON Schema vocabulary", which ``error-handling.mdx``
        # states as a MUST. The forbidden names ride in the context rather than
        # in a sentence, the way ``name_the_combinator`` carries the absent
        # ones, so a consumer reads them without parsing text and the wire
        # message stays the one ``safe_message_for`` authors.
        raise PydanticCustomError(
            "not",
            "{fields} is not accepted by this request shape",
            {"fields": ", ".join(carried)},
        )
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


#: The error types ``ValidationError.from_exception_data`` resolves by name.
#: ``ErrorType`` is the public enumeration of them; a type outside it is a
#: ``PydanticCustomError`` someone minted, and has to be re-minted rather than
#: named.
_KNOWN_ERROR_TYPES = frozenset(typing.get_args(ErrorType))


def _is_known(error: Any) -> bool:
    """Whether ``from_exception_data`` can rebuild this error FROM ITS NAME.

    The name is not enough on its own. A custom error may REUSE a known name
    with its own context: ``EmailStr`` reports ``value_error`` carrying
    ``{'reason': ...}``, while pydantic's own ``value_error`` carries
    ``{'error': <exception>}`` and refuses to be built without it. Naming such
    an error raises ``TypeError: ValueError: 'error' required in context``,
    which is how this was found -- three parity tests, after the rest of the
    suite was green.

    So the record itself is asked: ``errors()`` attaches ``url``, the
    documentation link for a known type, and omits it for a custom one.
    Measured on all four combinations -- ``int_parsing`` (known, url),
    ``EmailStr``'s ``value_error`` (custom, no url), a compiled ``anyOf``
    (custom, no url), and a bare ``ValueError`` (known, url). The name is kept
    as a second condition, so an error with neither falls to the re-mint, which
    always builds.
    """
    return error["type"] in _KNOWN_ERROR_TYPES and "url" in error


def _is_branch_requiredness(error: Any) -> bool:
    """Whether a union error says a BRANCH's own required field is absent.

    Inside a union every ``loc`` opens with the label of the choice that
    produced it, so a branch's own root properties sit at length two and
    anything longer is a position inside the document. A ``missing`` deeper
    than that is content, not requiredness: an object nested three levels down
    lacking a field ITS schema requires says this branch was reached and the
    document is wrong inside it.
    """
    return error["type"] == "missing" and len(error["loc"]) == 2


def _refuses_the_shape(error: Any) -> bool:
    """Whether this error says the branch was never REACHED, asked on its own.

    Two ways a branch declines the document rather than finding a fault inside
    it, and both report at the branch's own root:

    * a required field of its own is absent -- ``missing`` at a ``loc`` of
      length one;
    * it FORBIDS a key the document carries -- ``_c.absent`` raises, which
      arrives as a whole-document error at ``loc`` ``()``.

    Measured on the create request, which has one of each: the
    seller-optimized branch reports ``missing`` for ``total_budget`` and the
    committed-proposal branch reports a ``value_error`` at ``()`` because it
    forbids ``packages``. Counting only the first left TWO candidates and the
    selection declined to choose, which is the shape of a rule that reads a
    wholesale refusal as a content failure.
    """
    return (error["type"] == "missing" and len(error["loc"]) == 1) or not error["loc"]


def _errors_of_the_reached_branch(
    value: Any, branches: Sequence[type], merged: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """The subset of ``merged`` belonging to the branch the document reached.

    Used only when the union's labels are degenerate, so the merged list holds
    every branch's errors under one key and there is nothing to group by. The
    branches are asked DIRECTLY to decide which of them got past its own
    requiredness; their own errors then identify which merged entries are that
    branch's, matched on the error's type and its path below the label.

    Selection only: what is reported is still the union's own errors, in the
    caller's input mode. A branch asked directly reports a document path, so its
    ``loc`` is the merged ``loc`` minus the label -- which is the match key.

    Returns ``None`` when it cannot decide, and the caller then keeps the
    ungrouped bucket: no branch was reached, two were, or a branch's direct
    verdict disagrees with the union's. A wrong narrowing is worse than none.
    """
    reached: list[Counter[tuple[Any, ...]]] = []
    for branch in branches:
        try:
            branch.__pydantic_validator__.validate_python(value)  # type: ignore[attr-defined]
        except ValidationError as branch_exc:
            own = branch_exc.errors()
            if any(_refuses_the_shape(error) for error in own):
                continue
            reached.append(Counter(tuple(error["loc"]) for error in own))
        else:
            return None  # accepts on its own while the union refused: do not guess
    if len(reached) != 1:
        return None
    # A MULTISET, not a set. Sibling branches report the SAME nested error when
    # they share the field it is under -- two branches of the create request
    # both validate ``packages``, so the merged list holds two identical
    # ``string_type`` entries for one bad ``geo_countries`` element. Matching on
    # membership kept both and the caller received the one real fault twice.
    # Taking at most as many copies as the branch itself reported drops the
    # sibling's duplicate and keeps a genuine repeat -- a document with a
    # repeated JSON key does produce two errors at one path, and that is the
    # branch's own count.
    remaining = reached[0]
    selected: list[dict[str, Any]] = []
    for error in merged:
        key = tuple(error["loc"])[1:]
        if remaining[key] > 0:
            remaining[key] -= 1
            selected.append(error)
    return selected or None


def _in_the_document(error: Any) -> Any:
    """One union error restated with a ``loc`` that is a path in the document.

    Drops the choice label positionally, which is where it always is, rather
    than recognising it by spelling. Everything else -- the type, the context a
    message is rendered from, the input -- is pydantic's own, so the restated
    error is identical to the one the branch would have reported had it been
    asked alone, in the mode the caller used.
    """
    detail: dict[str, Any] = {
        "type": error["type"],
        "loc": tuple(error["loc"][1:]),
        "input": error["input"],
    }
    context = error.get("ctx")
    if _is_known(error):
        if context is not None:
            detail["ctx"] = context
    else:
        # A custom refusal -- a compiled root constraint, or a library's own.
        # Its context is already substituted into the message it rendered, so
        # the message IS the template; a brace left in it stays literal, which
        # is measured rather than assumed.
        detail["type"] = (
            PydanticCustomError(error["type"], error["msg"], context)
            if context is not None
            else PydanticCustomError(error["type"], error["msg"])
        )
    return detail


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

    A REFUSAL IS THE BRANCH'S OWN, NOT THE UNION'S. A pydantic union prefixes
    every error's ``loc`` with the label of the choice that produced it: a plain
    model's class name, and for a branch carrying a compiled validator
    pydantic's own schema spelling,
    ``function-after[_require_schema_required_group(), <Branch>]``. ``loc`` is
    read as a path through the buyer's document -- ``core/error.json`` specifies
    ``issues[].pointer`` as an RFC 6901 pointer into the request payload -- and
    a choice label is a fact about this package's classes, not a key the buyer
    sent. Measured: a union of two plain models reports
    ``('PlainA', 'packages', 0, 'geo', 0)`` for a document error at
    ``/packages/0/geo/0``, and the same union over the same models carrying a
    model-level validator reports
    ``('function-after[_require_schema_required_group(), WrappedA]', ...)``. So
    the union is the element's source and the validator only changes its
    spelling.

    So a refusal is restated as the refusal of ONE branch -- the one the
    document meant -- with the label dropped. Nothing downstream has to
    recognise a label, and the two spellings stop being a distinction anything
    depends on.
    """

    def _wrap(value: Any, handler: Any) -> Any:
        try:
            return handler(value)
        except ValidationError as exc:
            # Group by branch: in a union's errors the first ``loc`` element
            # names the branch that produced them.
            per_branch: dict[str, list[dict[str, Any]]] = {}
            for error in exc.errors():
                if not error["loc"]:
                    raise
                per_branch.setdefault(str(error["loc"][0]), []).append(dict(error))
            if len(per_branch) == 1 and len(branches) > 1:
                # DEGENERATE LABELS: the grouping above carries no information.
                # It assumes pydantic gives each union choice a DISTINCT label,
                # which is not a property anyone guarantees. A branch that gains
                # a WRAP validator is spelled
                # ``function-after[..., function-wrap[<validator>()]]`` -- a name
                # with no class in it -- so every branch collapses to one label
                # and one bucket. Measured: making the canonical layer's legacy
                # refusal ``mode="wrap"`` did exactly that, all three branches of
                # the create request arrived under one key, the bucket contained
                # another branch's ``missing``, and the combinator refusal
                # displaced the document error in 23 tests.
                #
                # WHICH SPELLINGS COLLAPSE, measured on the same two branches, so
                # the next validator added to a branch can be checked against
                # this rather than against the one case that bit us:
                #
                #     plain branches         ['First', 'Second']          distinct
                #     after-validator only   ['function-after[f(), First]',
                #                             'function-after[f(), Second]']
                #                                                         distinct
                #     WRAP only              ['function-wrap[f()]']       DEGENERATE
                #     after over wrap        ['function-after[f(),
                #                              function-wrap[f()]]']      DEGENERATE
                #
                # So the hazard is ANY wrap in a branch's schema, not one
                # particular validator.
                #
                # So when the labels are degenerate, the branches are asked
                # directly -- for SELECTION ONLY. The reported errors still come
                # from the union, which is what keeps them in the caller's input
                # mode; a branch's own errors are used to recognise WHICH of the
                # merged errors are its.
                selected = _errors_of_the_reached_branch(
                    value, branches, next(iter(per_branch.values()))
                )
                if selected is not None:
                    per_branch = {"": selected}
            # Report ONE branch's errors when the document satisfies that
            # branch's requiredness. A branch that failed on fields IT requires
            # was never reached; one that got past its own requiredness and
            # failed on CONTENT is the branch the document meant, and that
            # failure is what the caller needs -- replacing it with the
            # combinator keyword would discard the only informative error, and
            # merging it with the other branches' complaints would publish
            # contradictory pointers, because branches differ by which fields
            # they FORBID.
            reached = [
                errors
                for errors in per_branch.values()
                if not any(_is_branch_requiredness(error) for error in errors)
            ]
            if reached:
                # CEILING: the branches are pairwise disjoint, so at most one
                # can get past its own requiredness. If two ever did, the first
                # in the root's own branch order is reported.
                raise ValidationError.from_exception_data(
                    exc.title, [_in_the_document(error) for error in reached[0]]
                ) from exc
            absent = sorted(
                {
                    str(error["loc"][1])
                    for errors in per_branch.values()
                    for error in errors
                    if _is_branch_requiredness(error)
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
