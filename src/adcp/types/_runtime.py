"""What a document says about an instance AS A WHOLE, as data on the class, and the
one validator that reads it.

A constraint on a single value goes in that value's annotation, where pydantic already
enforces it on the constructor.  D6's six keyword families are the ones that constrain
the OBJECT rather than one of its values -- ``oneOf``/``anyOf`` over ``required``,
``if``/``then``/``else``, ``dependencies``, ``min``/``maxProperties``, ``uniqueItems``
and ``not`` -- so none of them has a field to live on and none can be a ``Field``
kwarg.  Each becomes a frozen dataclass in one class-level tuple (``_adcp_rules``), and
:class:`RuleBound` carries the single ``model_validator(mode="after")`` that evaluates
it.  Adding a rule kind adds a dataclass and renames nothing: the emitter writes a
different constructor into the same tuple and the validator loops over it unchanged.

``mode="after"`` and not ``mode="before"``: a before-validator receives the raw input,
and a repeated JSON key, or a key supplied under both its alias and its field name,
collapses there -- so a rule evaluated on it would decide about a payload the model
never built.  After construction ``__pydantic_fields_set__`` says exactly which keys
arrived.

WHAT THESE RULES ARE FOR, precisely, because D4 answers the other half.
``AdCPBaseModel.strict_validate`` validates the payload against the document's own JSON
Schema and so already refuses every one of these keywords -- it IS the accepted set,
and the conformance harness grades through it.  These rules are the ``model_validate``
path: the constructor D4 keeps public and documents as NOT consulting the schema.  So a
rule here cannot widen or narrow what the library ACCEPTS; it narrows what the
constructor BUILDS, and the only instrument that can observe one is a direct
``model_validate`` call.  ``tests/test_emit.py`` has those, and they are the only tests
that go red when this module is short-circuited -- measured, not asserted.

KNOWN CEILING, and it is the reason a rule is data rather than a schema fragment: a
rule is expressible here only as a statement about key PRESENCE, and about a key's
value being one of a listed set.  A conditional whose ``then`` narrows a VALUE --
``core/canvas-constraint.json``'s ``if unit == "percent" then x.maximum = 100`` -- is
not, and it gets no rule.  It is not refused either, and that is D4: the document still
states it, ``strict_validate`` still refuses the violation, and only the constructor is
wider.  Refusing the document instead would cost the whole ``if`` population for a
constraint the accepted set already enforces.  The ceiling is a committed test, not a
docstring: the constructor builds the violating payload and the schema half rejects the
same payload on ``maximum``.

``uniqueItems`` is :class:`UniqueItems`, and it is the one family of the six whose
keyword sits on a node BELOW the class that carries the rule -- the array held by a
field, which is where 467 of the bundle's 485 occurrences are.  D2 says the rule is
*on the nearest class*, so the class that holds the array is the one that states it,
and an array with no class above it (a mapping value, a document root, a combinator
branch) is refused by name rather than carried.  This module had no such kind while
there was no array lowering to reach one; there is now.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel, model_validator
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

#: One refusal: the JSON Schema keyword that bit, where it bit, the detail, and the
#: value that was there.
Error = tuple[str, tuple[Any, ...], str, Any]


def refuse(name: str, errors: Sequence[Error]) -> None:
    """Raise pydantic's ``ValidationError`` for ``errors``, or return if there are none.

    The ONE error shape in this package, shared with ``_base._refuse`` (the schema half
    of ``strict_validate``), so a caller reads the same thing whichever half refused:
    the JSON Schema keyword as the error ``type``, the instance pointer as its ``loc``.
    Two spellings of one refusal is one place for the halves to come apart, and a
    keyword like ``not`` or ``dependencies`` is refused by BOTH halves -- the schema
    half for a ``strict_validate`` caller and this one for a ``model_validate`` caller.

    The keyword reaches ``errors()[0]["type"]`` through ``PydanticCustomError``, which
    is the only way a name from another vocabulary gets there.  The template is fixed
    and the text is context, because a message from another vocabulary carries braces of
    its own and a message used AS the template would be read as placeholders.
    """
    if not errors:
        return
    raise ValidationError.from_exception_data(
        name,
        [
            InitErrorDetails(
                type=PydanticCustomError(keyword, "{detail}", {"detail": detail}),
                loc=loc,
                input=given,
            )
            for keyword, loc, detail, given in errors
        ],
    )


class Rule(Protocol):
    """What the validator needs of a rule, and all it needs.

    ``keys`` is the set of property names the instance supplied, as the DOCUMENT spells
    them, and ``values`` maps the same names to what arrived.  A rule reads those and
    yields its refusals; it never touches the model, so a rule is testable on two plain
    arguments and the validator is the only thing here that knows about pydantic.
    """

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]: ...


@dataclass(frozen=True)
class Dependencies:
    """draft-07 ``dependencies``, the list-of-names form: a key implies other keys.

    Only that form, because it is the only one this bundle uses -- every one of its 32
    sites.  The schema-valued form ``{"dependencies": {"k": {...}}}`` is a conditional,
    and if one appears it lowers through :class:`ConditionalRequired` or through nothing
    at all, never through this.
    """

    trigger: str
    requires: tuple[str, ...]

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        if self.trigger not in keys:
            return
        missing = [name for name in self.requires if name not in keys]
        if missing:
            yield (
                "dependencies",
                (self.trigger,),
                f"{self.trigger!r} requires {', '.join(repr(m) for m in missing)}",
                values.get(self.trigger),
            )


@dataclass(frozen=True)
class PropertyCount:
    """``minProperties`` / ``maxProperties``, counted over the keys that arrived.

    A class whose document declares no ``additionalProperties`` gets
    ``extra="ignore"`` (D8), so a key the document would COUNT and the model drops is
    not counted here -- and that is why ``codegen.lower.rules._count`` writes the
    MINIMUM only where the document states ``additionalProperties`` at all.  Under
    ``ignore`` a dropped key makes this count LOWER than the document's, which turns a
    minimum into a refusal of an instance the document ACCEPTS (measured on
    ``core/provenance.json``'s ``render_guidance``, which the document satisfies with
    one undeclared key) and leaves a maximum merely under-refusing, which is what D4
    says the constructor may do.  So a ``minimum`` here always counts declared fields
    or extras the class kept.
    """

    minimum: int | None = None
    maximum: int | None = None

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        if self.minimum is not None and len(keys) < self.minimum:
            yield ("minProperties", (), f"{len(keys)} properties, minimum {self.minimum}", None)
        if self.maximum is not None and len(keys) > self.maximum:
            yield ("maxProperties", (), f"{len(keys)} properties, maximum {self.maximum}", None)


@dataclass(frozen=True)
class ForbiddenGroups:
    """``not`` over ``required``: no listed group of keys may be present in full.

    One dataclass covers both shapes the bundle spells, because they are the same
    statement with a different group count: ``not: {"required": [a, b]}`` is one group
    ``(a, b)`` -- a and b are not both present -- and
    ``not: {"anyOf": [{"required": [a]}, {"required": [b]}]}`` is two groups ``(a,)``
    and ``(b,)`` -- neither is present.  ``allOf`` of required-only branches reduces the
    same way.  ``codegen.lower.rules`` does the reducing and declines to do it for a
    branch that constrains a value.
    """

    groups: tuple[tuple[str, ...], ...]

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        for group in self.groups:
            if group and all(name in keys for name in group):
                yield (
                    "not",
                    (group[0],),
                    f"{', '.join(repr(g) for g in group)} are present together, which the "
                    "document forbids",
                    values.get(group[0]),
                )


@dataclass(frozen=True)
class RequiredGroups:
    """``oneOf`` / ``anyOf`` over ``required``: which groups of keys may be present.

    ``anyOf`` is AT LEAST ONE group present in full; ``oneOf`` is EXACTLY ONE.  One
    dataclass with the combinator as a parameter rather than two kinds, because the two
    differ only in the count they admit and the refusal names the document's own
    keyword either way.  The negation of these is :class:`ForbiddenGroups` and that one
    is separate for the opposite reason: it is reached from a different keyword
    (``not``) and its groups are what the document FORBIDS, so collapsing them would
    make one field mean two things.

    ``oneOf`` counts the groups SATISFIED, which is the document's own reading: a group
    is satisfied when every name in it is present, and two groups can be satisfied by
    one instance.
    """

    groups: tuple[tuple[str, ...], ...]
    combinator: str = "anyOf"

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        satisfied = [g for g in self.groups if g and all(name in keys for name in g)]
        spelled = "; ".join(", ".join(repr(n) for n in g) for g in self.groups if g)
        if self.combinator == "oneOf":
            if len(satisfied) != 1:
                yield (
                    "oneOf",
                    (),
                    f"{len(satisfied)} of these groups are present, the document admits "
                    f"exactly one: {spelled}",
                    None,
                )
            return
        if not satisfied:
            yield (
                "anyOf",
                (),
                f"none of these groups is present, the document requires at least one: "
                f"{spelled}",
                None,
            )


def _same(a: Any, b: Any) -> bool:
    """Are these the same JSON value?  draft-07's equality, not Python's.

    ``==`` is draft-07's rule for every value this bundle puts in an array -- a
    string, a number, a null, an object, and a model or an enum member standing for
    one -- with ONE exception Python forces: ``True == 1`` and draft-07 says
    ``true`` and ``1`` are different values.  So the boolean-ness of both sides is
    tested first.  There is nothing else to reconcile: draft-07 and Python agree
    that ``1`` and ``1.0`` ARE the same number.
    """
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return bool(a == b)


@dataclass(frozen=True)
class UniqueItems:
    """``uniqueItems: true`` on the array one field holds: its members are distinct.

    The key is the DOCUMENT'S property name, like every other rule here, so it reads
    off ``supplied``'s mapping whether or not the field carries an alias.

    KNOWN CEILING: the comparison is PAIRWISE and so O(n^2), not a hash set. An item
    can be a pydantic model or a ``dict`` and neither is hashable -- the same
    measurement that rules out ``set[X]`` as the annotation, where pydantic refuses
    every instance with ``set_item_not_hashable``. The arrays in this bundle are
    small (a ``maxItems`` where one is stated is in the tens); the upgrade path is a
    hash set behind an ``isinstance`` test for the hashable cases, never a weaker
    comparison.

    A value that is not a list gets no verdict: the field may be a union with a
    non-array arm, and a rule that refused there would be stronger than the
    document, which applies ``uniqueItems`` only to an array.
    """

    key: str

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        if self.key not in keys:
            return
        items = values.get(self.key)
        if not isinstance(items, list):
            return
        for i, item in enumerate(items):
            if any(_same(item, earlier) for earlier in items[:i]):
                yield (
                    "uniqueItems",
                    (self.key, i),
                    f"item {i} repeats an earlier one, and the document requires the "
                    f"items of {self.key!r} to be distinct",
                    item,
                )
                return  # one refusal per field: the keyword bit, and where


@dataclass(frozen=True)
class Match:
    """One clause of an ``if``: a key is present, and its value is one of ``allowed``.

    ``allowed is None`` is a presence test alone (the ``if``'s ``required`` with no
    ``properties`` entry for that key).  A clause with ``present=False`` is the key
    being absent.
    """

    key: str
    present: bool = True
    allowed: tuple[Any, ...] | None = None

    def holds(self, keys: frozenset[str], values: Mapping[str, Any]) -> bool:
        if self.key not in keys:
            return not self.present
        if not self.present:
            return False
        return self.allowed is None or values.get(self.key) in self.allowed


@dataclass(frozen=True)
class ConditionalRequired:
    """``if`` / ``then`` reduced to presence: when every clause of ``when`` holds, each
    of ``require`` must be present and each of ``forbid`` absent.

    The ``else`` branch is a second rule with the same ``when`` negated, which is why
    this carries no ``else`` of its own: two rules, one dataclass.
    ``codegen.lower.rules`` writes both.
    """

    when: tuple[Match, ...]
    require: tuple[str, ...] = ()
    forbid: tuple[str, ...] = ()

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        if not all(clause.holds(keys, values) for clause in self.when):
            return
        condition = _condition(self.when)
        for name in self.require:
            if name not in keys:
                yield ("required", (name,), f"required when {condition}", None)
        for name in self.forbid:
            if name in keys:
                yield ("not", (name,), f"forbidden when {condition}", values.get(name))


@dataclass(frozen=True)
class NegatedConditional:
    """``if`` / ``else``: when ANY clause of ``when`` fails, the ``else`` branch applies.

    A separate kind rather than a flag on :class:`ConditionalRequired`, because the two
    differ in the QUANTIFIER and not in a parameter: a ``then`` applies when every
    clause holds, an ``else`` when at least one does not, and "not all" is not "all of
    the negations" for a ``when`` of more than one clause.
    """

    when: tuple[Match, ...]
    require: tuple[str, ...] = ()
    forbid: tuple[str, ...] = ()

    def errors(self, keys: frozenset[str], values: Mapping[str, Any]) -> Iterator[Error]:
        if all(clause.holds(keys, values) for clause in self.when):
            return
        condition = f"not ({_condition(self.when)})"
        for name in self.require:
            if name not in keys:
                yield ("required", (name,), f"required when {condition}", None)
        for name in self.forbid:
            if name in keys:
                yield ("not", (name,), f"forbidden when {condition}", values.get(name))


def _condition(when: tuple[Match, ...]) -> str:
    """The ``when`` clauses as text, for the detail of a refusal."""
    return ", ".join(
        f"{c.key}{'' if c.present else ' absent'}"
        + (
            ""
            if c.allowed is None
            else f"={c.allowed[0]!r}"
            if len(c.allowed) == 1
            else f" in {list(c.allowed)!r}"
        )
        for c in when
    )


def supplied(model: BaseModel) -> tuple[frozenset[str], Mapping[str, Any]]:
    """The keys the instance supplied, as the DOCUMENT spells them, and their values.

    ``__pydantic_fields_set__`` holds the field names that arrived, plus the names of
    any extras kept under ``extra="allow"``.  A field carrying an ``alias`` is spelled
    by its alias, because the alias is the document's property name and the only
    accepted spelling (``emit.field_name``); a name that is no field at all is an extra
    and is already the document's own.
    """
    fields = type(model).model_fields
    out: dict[str, Any] = {}
    for name in model.__pydantic_fields_set__:
        declared = fields.get(name)
        if declared is None:
            out[name] = (model.__pydantic_extra__ or {}).get(name)
            continue
        out[declared.alias or name] = getattr(model, name)
    return frozenset(out), out


class RuleBound(BaseModel):
    """The one validator, over the one tuple.

    A class with no rule carries the empty tuple it inherits and the validator returns
    on its first line, so this costs every other class one attribute lookup.
    """

    _adcp_rules: ClassVar[tuple[Rule, ...]] = ()

    @model_validator(mode="after")
    def _enforce_adcp_rules(self) -> RuleBound:
        if not self._adcp_rules:
            return self
        keys, values = supplied(self)
        refuse(
            type(self).__name__,
            [e for rule in self._adcp_rules for e in rule.errors(keys, values)],
        )
        return self
