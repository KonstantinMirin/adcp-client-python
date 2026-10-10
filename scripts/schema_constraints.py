"""One reader for a schema root's constraint content.

``datamodel-code-generator`` renders a schema root's ``properties`` and drops the
rest of what the root states: a root ``anyOf``/``oneOf`` over overlay arms, a root
``if``/``then``/``else``, root ``dependencies``, a root ``not``. Each dropped
keyword is a document the generated model accepts and the canonical schema
refuses.

This module is the only code that reads that content. It produces one
:class:`RootConstraints` record per schema root, and every consumer -- the
validator pass, the response-arm emitter, the union-arm naming rule -- takes the
record and nothing else from the node, so a second divergent reading of the same
node has nothing to call.

Parsing is key-consuming
------------------------

For every node it visits the parser accounts for every key as exactly one of:

* **Compiled** -- consumed by a grammar production, producing a :data:`Cond`.
* **Non-asserting** -- a member of :data:`NON_ASSERTING_KEYS`, a named frozen
  set of keys that carry no validation semantics by JSON Schema's own
  definition (annotations, identifiers, the ``$defs`` container, an ``ajv``
  message override).
* **Declared behavioral** -- exactly ``x-adcp-validation``, declared outside the
  structural models' promise by ``docs/validation-contract.md`` and carried by
  canonical wire validation plus targeted hand-written validators. The parser
  records the classification on the record; it is a contract citation, not a
  per-schema tolerance entry.
* **Proven restatement** -- a declarative keyword (``type``, ``$ref``,
  ``format``, ``additionalProperties``) or a whole property re-declaration that
  resolves equal to what the generated class already declares for that
  position. Equality is checked, never assumed; a narrowing compiles as a value
  predicate instead.

Anything else raises :class:`UnexpressibleKeywordError`, which aborts generation
naming the file, the JSON pointer and the keyword. There is no list of
known-dropped keywords anywhere in this module: a keyword is compiled,
classified by a named rule, or fatal. That is what makes "the model is weaker
than its schema, silently" unconstructible rather than detected.

What "what the generated class already declares" means here
-----------------------------------------------------------

``datamodel-code-generator`` renders a root's merged ``properties`` and nothing
else, so the declaration for a position inside root constraint content is the
schema node at the same position under the root's own ``properties`` -- which is
what the parser descends in parallel with the constraint node. Field *names* are
a separate question, because ``model_fields_set`` holds field names and a schema
states wire names; :class:`DeclaredShape` carries that map, taken from the
generated class's ``model_fields``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Union

#: Resolves the document half of a ``$ref`` to a parsed schema, or ``None``.
ResolveDocument = Callable[[str], Any]

__all__ = [
    "AllOf",
    "AnyOf",
    "Arm",
    "bundle_document_resolver",
    "COMPILED_KEYWORDS",
    "Cond",
    "DECLARED_BEHAVIORAL_KEY",
    "DeclaredShape",
    "DependentRequired",
    "EveryItem",
    "IfThen",
    "KeysSatisfy",
    "MatchingKeysSatisfy",
    "NON_ASSERTING_KEYS",
    "NoOtherProps",
    "Not",
    "OtherPropsSatisfy",
    "OneOf",
    "PropCount",
    "PropSatisfies",
    "read_root_constraints",
    "Restated",
    "root_carries_constraints",
    "RootConstraints",
    "SomeItem",
    "Supplied",
    "Undeclarable",
    "UnexpressibleKeywordError",
    "UnplaceableConstraintError",
    "ValueBounds",
    "ValueConst",
    "ValueEnum",
    "ValueItems",
    "ValueLen",
    "ValuePattern",
    "ValueType",
    "ValueUnique",
]


class UnexpressibleKeywordError(Exception):
    """A keyword inside root constraint content that the grammar cannot compile.

    Raising this aborts generation. ``generate_types.py`` generates into a
    staging tree and installs only on success, so the checkout stays clean and
    the previous generated tree stays in place.
    """

    def __init__(self, schema_file: str, pointer: str, keyword: str) -> None:
        self.schema_file = schema_file
        self.pointer = pointer
        self.keyword = keyword
        super().__init__(
            f"{schema_file}#{pointer or '/'}: root constraint content carries "
            f"{keyword!r}, which the constraint grammar cannot compile. Either add a "
            f"grammar production for it in scripts/schema_constraints.py (one Cond "
            f"node, one compiler case, one constructed-node test), or classify it by "
            f"name if it carries no validation semantics. There is no skip lane."
        )


class UnplaceableConstraintError(Exception):
    """A root constraint names a field no class for that schema declares.

    That is a generator field-drop surfacing loudly, not something to work
    around: the constraint cannot be placed because the field it grades does not
    exist on the model.
    """

    def __init__(self, schema_file: str, pointer: str, name: str) -> None:
        self.schema_file = schema_file
        self.pointer = pointer
        self.name = name
        super().__init__(
            f"{schema_file}#{pointer or '/'}: root constraint content names property "
            f"{name!r}, which the generated class for this schema does not declare. "
            f"A constraint that cannot be placed is a dropped field, not a keyword to "
            f"classify."
        )


#: Keys that carry no validation semantics at the position they appear, each
#: named for the reason it is inert. This is the whole set: a key outside it is
#: compiled or fatal.
NON_ASSERTING_KEYS = frozenset(
    {
        # Annotations: JSON Schema defines these as having no validation effect.
        "title",
        "description",
        "deprecated",
        "examples",
        "$comment",
        "default",
        "readOnly",
        "writeOnly",
        # Identifiers and the subschema container. ``$defs``/``definitions``
        # hold subschemas reachable only through a ``$ref``; at their own
        # position they assert nothing.
        "$schema",
        "$id",
        "$defs",
        "definitions",
        # OpenAPI's serialization hint for a union. It selects which arm a
        # document is read as; it adds no constraint of its own.
        "discriminator",
        # ``ajv``'s message override for a sibling keyword's failure. The
        # sibling keyword is what asserts.
        "errorMessage",
        # JSON Schema makes ``format`` an annotation by default -- an assertion
        # only under the format-assertion vocabulary -- and the SDK's models
        # carry format semantics in a field's own annotation where pydantic has
        # them at all. The formats pydantic lacks (``uri-template``) are a
        # pre-existing type-level looseness carried by canonical wire
        # validation, outside this defect class and named in the design's
        # coverage table rather than silently absorbed here.
        "format",
        # Per-enum-value documentation, and a maintainer's note. Neither is a
        # JSON Schema keyword; both are text alongside the sibling that
        # asserts.
        "enumDescriptions",
        "notes",
        # AdCP annotations.
        "x-entity",
        "x-status",
        "x-deprecated-in",
        "x-removed-in",
        # Marks a field whose object value is carried through unmodelled.
        # A rendering instruction, not a constraint on the document.
        "x-adcp-open-payload",
    }
)

#: The one key whose rules are declared outside the structural models' promise.
DECLARED_BEHAVIORAL_KEY = "x-adcp-validation"

#: Every keyword the grammar has a production for. Each member is graded twice
#: by ``tests/test_schema_constraints.py``: a constructed node carrying it must
#: compile, and the fixture map must cover exactly this set, so a production
#: added without a test and a claim made without a production both fail.
COMPILED_KEYWORDS = frozenset(
    {
        "$ref",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "contains",
        "dependencies",
        "dependentRequired",
        "dependentSchemas",
        "else",
        "enum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "if",
        "items",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "properties",
        "propertyNames",
        "required",
        "then",
        "type",
        "uniqueItems",
    }
)

#: Keys whose presence makes a node a constraint rather than a declaration. The
#: generator renders a node's declarative keys and drops these.
LOGIC_KEYS = frozenset(
    {
        "anyOf",
        "oneOf",
        "allOf",
        "not",
        "if",
        "then",
        "else",
        "dependencies",
        "dependentRequired",
        "dependentSchemas",
    }
)

#: The key :func:`_declaration_of` adds to carry every ``$ref`` a node declares,
#: its own and its ``allOf`` members'. A class inherits from every member, so a
#: restatement of any member's reference is already declared. Not a JSON Schema
#: keyword, so it collides with nothing a schema can write.
_DECLARED_REFS = "$refs"


# --------------------------------------------------------------------------- #
# The grammar
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Supplied:
    """``required``: the caller supplied the field.

    Presence is ``model_fields_set`` membership. An explicit null is a supplied
    value -- on a mutation input it is the command to clear -- and a default the
    caller never sent is not.
    """

    name: str


@dataclass(frozen=True)
class Not:
    operand: Cond


@dataclass(frozen=True)
class AllOf:
    operands: tuple[Cond, ...]


@dataclass(frozen=True)
class AnyOf:
    operands: tuple[Cond, ...]


@dataclass(frozen=True)
class OneOf:
    operands: tuple[Cond, ...]


@dataclass(frozen=True)
class IfThen:
    """``if``/``then``/``else`` as an implication over the condition."""

    condition: Cond
    consequent: Cond | None
    alternative: Cond | None


@dataclass(frozen=True)
class PropSatisfies:
    """Descend into a supplied value.

    Vacuously true when the property was not supplied or is an explicit null:
    JSON Schema's ``properties`` grades present object members only.
    """

    name: str
    operand: Cond


@dataclass(frozen=True)
class ValueConst:
    value: Any


@dataclass(frozen=True)
class ValueEnum:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ValueType:
    types: tuple[str, ...]


@dataclass(frozen=True)
class ValuePattern:
    pattern: str


@dataclass(frozen=True)
class ValueLen:
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class ValueBounds:
    ge: float | None = None
    le: float | None = None
    gt: float | None = None
    lt: float | None = None


@dataclass(frozen=True)
class ValueItems:
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class ValueUnique:
    pass


@dataclass(frozen=True)
class EveryItem:
    """``items``: every element satisfies the operand."""

    operand: Cond


@dataclass(frozen=True)
class SomeItem:
    """``contains``: at least one element satisfies the operand."""

    operand: Cond


@dataclass(frozen=True)
class KeysSatisfy:
    """``propertyNames``: every key satisfies the operand."""

    operand: Cond


@dataclass(frozen=True)
class MatchingKeysSatisfy:
    """``patternProperties``: every value under a matching key satisfies it."""

    pattern: str
    operand: Cond


@dataclass(frozen=True)
class PropCount:
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class DependentRequired:
    """``dependencies``/``dependentRequired``: presence implies presence."""

    name: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class NoOtherProps:
    """``additionalProperties: false``: only the named members may be supplied.

    The sibling ``properties`` names what may be present, and a generated class
    normally declares more fields than one arm's ``properties`` names, so this
    is a bound on what the caller supplied rather than on what the class can
    hold.
    """

    names: tuple[str, ...]


@dataclass(frozen=True)
class OtherPropsSatisfy:
    """``additionalProperties`` as a subschema: unnamed members satisfy it.

    With no names, every member does -- which is how the bundle spells a map
    type, ``{"additionalProperties": {"enum": [...]}}``.
    """

    names: tuple[str, ...]
    operand: Cond


@dataclass(frozen=True)
class Undeclarable:
    """``required`` naming a property the schema itself never declares.

    An AdCP request root that forbids ``creatives`` names a key the document
    may not carry at all. A generated model has no field for it and cannot be
    given one, so the predicate is false for every instance -- which is what
    makes the arm forbidding it satisfiable and the arm requiring it dead.
    """

    name: str


@dataclass(frozen=True)
class Restated:
    """A keyword proven identical to what the generated class declares.

    True of every instance of that class, which makes substituting it sound in
    a negated position as much as a positive one. Carries the keyword so a
    reader of the record can see what was accounted for rather than inferring
    it from an absence.
    """

    keyword: str


Cond = Union[
    "Supplied",
    "NoOtherProps",
    "OtherPropsSatisfy",
    "Undeclarable",
    "Not",
    "AllOf",
    "AnyOf",
    "OneOf",
    "IfThen",
    "PropSatisfies",
    "ValueConst",
    "ValueEnum",
    "ValueType",
    "ValuePattern",
    "ValueLen",
    "ValueBounds",
    "ValueItems",
    "ValueUnique",
    "EveryItem",
    "SomeItem",
    "KeysSatisfy",
    "MatchingKeysSatisfy",
    "PropCount",
    "DependentRequired",
    "Restated",
]


# --------------------------------------------------------------------------- #
# The record
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DeclaredShape:
    """The wire-to-field map the generated class declares for one object.

    ``model_fields_set`` holds field names and a schema states wire names; a
    field aliased ``schema`` appears as ``schema_``. Every schema-named property
    in a compiled predicate passes through this map before it reaches the
    record, so no emitter has to re-derive it.

    ``nested`` carries the same map for a field whose value is itself an object
    the parser descends into. A field with no entry is :data:`OPAQUE`: the
    parser could not resolve the nested class, so it carries wire names through
    unchanged. ``OPAQUE`` also answers "declares every name", which is what
    keeps an unresolved nesting from manufacturing a field-drop refusal.
    """

    fields: Mapping[str, str] = field(default_factory=dict)
    nested: Mapping[str, DeclaredShape] = field(default_factory=dict)
    opaque: bool = False

    def attribute(self, wire_name: str) -> str | None:
        """The attribute for a wire name, or ``None`` when undeclared."""
        if self.opaque:
            return wire_name
        return self.fields.get(wire_name)

    def descend(self, wire_name: str) -> DeclaredShape:
        return self.nested.get(wire_name, OPAQUE)

    @classmethod
    def from_schema(cls, schema: Any) -> DeclaredShape:
        """The map a schema's own declarations imply, with identity names.

        Every property any part of a root declares, because the generator emits
        one class per declaring arm and a root-level constraint may name a field
        a sibling arm declares. Used where no generated class is available --
        the bundle-closure test, and a nested object the parser cannot resolve
        to a class. It answers the keyword-accounting question faithfully, which
        is what the closure rule grades, and makes no claim about aliases, which
        only ``model_fields`` can answer.
        """
        properties = _declared_properties(schema)
        if not properties:
            return OPAQUE
        return cls(
            fields={name: name for name in properties},
            nested={name: cls.from_schema(sub) for name, sub in properties.items()},
        )


#: A shape the parser could not resolve: identity names, declares everything.
OPAQUE = DeclaredShape(opaque=True)


@dataclass(frozen=True)
class Arm:
    """One arm of a schema root's ``anyOf``/``oneOf``."""

    pointer: str
    """``"anyOf/0"`` -- provenance, never identity."""

    title: str | None
    """Identity source 1."""

    discriminator: tuple[str, str] | None
    """Identity source 2: ``(property, const)``."""

    required: tuple[str, ...]
    """Identity source 3, and a constraint. Attribute names, not wire names."""

    declares_fields: bool
    """``properties`` introducing new fields: a class-creating arm."""

    condition: Cond
    """The WHOLE arm as one constraint tree."""

    declares_behavioral_rules: bool = False
    """The arm carries ``x-adcp-validation``, so its cardinality is not derivable."""


@dataclass(frozen=True)
class RootConstraints:
    """Everything a schema root states beyond its merged ``properties``."""

    combinator: Literal["anyOf", "oneOf"] | None
    arms: tuple[Arm, ...]
    conjuncts: tuple[Cond, ...]
    """Root ``if``/``then``/``else``, ``dependencies``, ``dependentRequired``,
    root ``not``, and the constraint arms of a root ``allOf``."""

    declares_behavioral_rules: bool = False

    def __bool__(self) -> bool:
        return bool(self.arms or self.conjuncts)


# --------------------------------------------------------------------------- #
# The parser
# --------------------------------------------------------------------------- #


def root_carries_constraints(schema: Any) -> bool:
    """Whether a schema root states anything beyond its merged ``properties``."""
    if not isinstance(schema, dict):
        return False
    if any(key in schema for key in ("if", "dependencies", "dependentRequired", "not")):
        return True
    return any(isinstance(schema.get(key), list) and schema[key] for key in ("anyOf", "oneOf"))


#: Positions whose subschema describes the same object as its parent, so a
#: property named there is a property of the parent.
_SAME_OBJECT_LISTS = ("allOf", "anyOf", "oneOf")
_SAME_OBJECT_NODES = ("if", "then", "else", "not")


def _declaration_of(node: Any) -> dict[str, Any]:
    """The part of a node the generator renders: its declarative keys.

    A node's logic keys are exactly what the generator drops, so they are never
    part of the declaration a restatement is proven against -- with one
    exception the generator does render: a root ``allOf`` is inheritance, and
    its members' declarations are merged into the class. So the declaration a
    restatement is proven against includes them.
    """
    if not isinstance(node, dict):
        return {}
    declaration = {key: value for key, value in node.items() if key not in LOGIC_KEYS}
    refs = [declaration["$ref"]] if isinstance(declaration.get("$ref"), str) else []
    members = node.get("allOf")
    if isinstance(members, list):
        properties = dict(declaration.get("properties") or {})
        for member in members:
            inherited = _declaration_of(member)
            properties.update(inherited.get("properties") or {})
            refs.extend(inherited.get(_DECLARED_REFS, ()))
            for key, value in inherited.items():
                if key not in ("properties", _DECLARED_REFS):
                    declaration.setdefault(key, value)
        if properties:
            declaration["properties"] = properties
    if refs:
        declaration[_DECLARED_REFS] = tuple(refs)
    return declaration


def _declared_properties(node: Any) -> dict[str, Any]:
    """Every property name any part of one object's schema declares.

    A root constraint may name a field a sibling arm declares -- an arm that
    forbids ``errors`` is the arm whose sibling declares it -- so the set of
    names a root's constraint content may reference is the union over every
    subschema describing the same object.
    """
    if not isinstance(node, dict):
        return {}
    collected: dict[str, Any] = {}
    properties = node.get("properties")
    if isinstance(properties, dict):
        collected.update(properties)
    for key in _SAME_OBJECT_LISTS:
        members = node.get(key)
        if isinstance(members, list):
            for member in members:
                collected.update(_declared_properties(member))
    for key in _SAME_OBJECT_NODES:
        if key in node:
            collected.update(_declared_properties(node[key]))
    for key in ("dependencies", "dependentSchemas"):
        members = node.get(key)
        if isinstance(members, dict):
            for member in members.values():
                collected.update(_declared_properties(member))
    return collected


class _Parser:
    """Compiles one schema root. One instance per root, so errors carry the file."""

    def __init__(
        self,
        schema_file: str,
        declared: DeclaredShape,
        resolve_document: ResolveDocument | None,
    ) -> None:
        self._file = schema_file
        self._root_shape = declared
        self._resolve_document = resolve_document
        self._schema_names: frozenset[str] = frozenset()
        self._document: Any = {}
        self._resolving: frozenset[str] = frozenset()
        self.behavioral = False

    # -- entry point -------------------------------------------------------- #

    def read(self, schema: dict[str, Any]) -> RootConstraints:
        combinator: Literal["anyOf", "oneOf"] | None = None
        arms: tuple[Arm, ...] = ()
        root_declaration = _declaration_of(schema)
        self._schema_names = frozenset(_declared_properties(schema))
        self._document = schema

        candidates: tuple[Literal["anyOf", "oneOf"], ...] = ("anyOf", "oneOf")
        for candidate in candidates:
            node = schema.get(candidate)
            if isinstance(node, list) and node:
                combinator = candidate
                arms = tuple(
                    self._read_arm(arm, f"{candidate}/{index}", root_declaration)
                    for index, arm in enumerate(node)
                )
                break

        conjuncts: list[Cond] = []
        if "if" in schema:
            conjuncts.append(self._if_then(schema, "", root_declaration, self._root_shape))
        for keyword in ("dependencies", "dependentRequired"):
            if keyword in schema:
                conjuncts.extend(self._dependencies(schema[keyword], keyword, "", self._root_shape))
        if "not" in schema:
            conjuncts.append(
                Not(self._node(schema["not"], "not", root_declaration, self._root_shape))
            )
        if combinator is None and isinstance(schema.get("allOf"), list):
            for index, member in enumerate(schema["allOf"]):
                compiled = self._node(member, f"allOf/{index}", root_declaration, self._root_shape)
                if not isinstance(compiled, Restated):
                    conjuncts.append(compiled)

        return RootConstraints(
            combinator=combinator,
            arms=arms,
            conjuncts=tuple(conjuncts),
            declares_behavioral_rules=self.behavioral,
        )

    # -- arms --------------------------------------------------------------- #

    def _read_arm(self, arm: Any, pointer: str, root_declaration: dict[str, Any]) -> Arm:
        if not isinstance(arm, dict):
            raise UnexpressibleKeywordError(self._file, pointer, type(arm).__name__)

        root_properties = root_declaration.get("properties")
        root_names = set(root_properties) if isinstance(root_properties, dict) else set()
        arm_declaration = _declaration_of(arm)
        arm_properties = arm_declaration.get("properties")
        arm_names = set(arm_properties) if isinstance(arm_properties, dict) else set()
        declares_fields = bool(arm_names - root_names)
        # An arm the generator renders as its own type declares its own shape;
        # an overlay arm narrows the shape the root declares. The generator
        # renders an arm that introduces fields as a class, and a bare ``$ref``
        # or scalar arm as that referenced or scalar type -- so in all three the
        # arm's own declarative keys are the declaration a restatement is proven
        # against. An arm whose properties only narrow the root's is the one
        # whose keywords are constraint content.
        renders_own_shape = (
            declares_fields
            or "$ref" in arm_declaration
            or arm_declaration.get("type", root_declaration.get("type"))
            != root_declaration.get("type")
        )
        declaration = arm_declaration if renders_own_shape else root_declaration

        before = self.behavioral
        self.behavioral = False
        condition = self._node(arm, pointer, declaration, self._root_shape)
        arm_behavioral = self.behavioral
        self.behavioral = before or arm_behavioral

        # Identity reads the names the arm requires OF THE CLASS; a name the
        # document may not carry identifies nothing.
        required = tuple(
            attribute
            for attribute in (
                self._attribute(name, self._root_shape, pointer)
                for name in arm.get("required", ())
                if isinstance(name, str)
            )
            if attribute is not None
        )
        return Arm(
            pointer=pointer,
            title=arm.get("title") if isinstance(arm.get("title"), str) else None,
            discriminator=self._discriminator(arm),
            required=required,
            declares_fields=declares_fields,
            condition=condition,
            declares_behavioral_rules=arm_behavioral,
        )

    @staticmethod
    def _discriminator(arm: dict[str, Any]) -> tuple[str, str] | None:
        """The ``(property, const)`` pair an arm pins exactly one property to."""
        properties = arm.get("properties")
        if not isinstance(properties, dict):
            return None
        pinned = [
            (name, sub["const"])
            for name, sub in properties.items()
            if isinstance(sub, dict) and isinstance(sub.get("const"), str)
        ]
        if len(pinned) != 1:
            return None
        return pinned[0]

    # -- the key-consuming walk --------------------------------------------- #

    def _node(
        self,
        node: Any,
        pointer: str,
        declaration: Any,
        shape: DeclaredShape,
    ) -> Cond:
        """Compile one schema node, accounting for every key it carries."""
        if node is True or node == {}:
            return Restated("true")
        if node is False:
            # ``false`` admits nothing. Spelled as a logic node so a caller
            # never has to special-case a bare boolean.
            return Not(Restated("true"))
        if not isinstance(node, dict):
            raise UnexpressibleKeywordError(self._file, pointer, type(node).__name__)

        declaration = declaration if isinstance(declaration, dict) else {}
        operands: list[Cond] = []

        for keyword in sorted(node):
            value = node[keyword]
            if keyword in NON_ASSERTING_KEYS:
                continue
            if keyword == DECLARED_BEHAVIORAL_KEY:
                self.behavioral = True
                continue
            compiled = self._keyword(keyword, value, node, pointer, declaration, shape)
            if compiled is None:
                raise UnexpressibleKeywordError(self._file, pointer, keyword)
            if isinstance(compiled, Restated):
                continue
            operands.append(compiled)

        if not operands:
            return Restated("declaration")
        if len(operands) == 1:
            return operands[0]
        return AllOf(tuple(operands))

    def _keyword(  # noqa: C901, PLR0911, PLR0912
        self,
        keyword: str,
        value: Any,
        node: dict[str, Any],
        pointer: str,
        declaration: dict[str, Any],
        shape: DeclaredShape,
    ) -> Cond | None:
        """One grammar production, or ``None`` when the grammar has none."""
        here = f"{pointer}/{keyword}" if pointer else keyword

        # The restatement rule, in one place and for every keyword: a keyword
        # whose value is exactly what the generated class declares at this
        # position is already enforced by the class, so it is true of every
        # instance. A keyword that NARROWS the declaration is not equal to it
        # and falls through to a production below -- equality is checked, never
        # assumed.
        if keyword in declaration and _equal(value, declaration[keyword]):
            return Restated(keyword)

        if keyword == "required":
            return _conjoin(
                self._supplied(name, shape, pointer) for name in value if isinstance(name, str)
            )

        if keyword == "properties":
            parts: list[Cond] = []
            declared_properties = declaration.get("properties")
            declared_properties = (
                declared_properties if isinstance(declared_properties, dict) else {}
            )
            for name in sorted(value):
                sub = value[name]
                declared_sub = declared_properties.get(name)
                if declared_sub is not None and _equal(sub, declared_sub):
                    continue
                attribute = self._attribute(name, shape, pointer)
                if attribute is None:
                    # ``properties`` grades present members only, and a key the
                    # document may not carry is never present.
                    continue
                inner = self._node(sub, f"{here}/{name}", declared_sub, shape.descend(name))
                if isinstance(inner, Restated):
                    continue
                parts.append(PropSatisfies(attribute, inner))
            return _conjoin(parts)

        if keyword == "patternProperties":
            parts = []
            for pattern in sorted(value):
                inner = self._node(value[pattern], f"{here}/{pattern}", None, OPAQUE)
                if isinstance(inner, Restated):
                    continue
                parts.append(MatchingKeysSatisfy(pattern, inner))
            return _conjoin(parts)

        if keyword == "additionalProperties":
            if value is True:
                return Restated(keyword)
            if value is False:
                # Only the sibling ``properties`` members may be supplied. A
                # generated class normally declares more fields than one arm
                # names, so this bounds what the caller supplied.
                if "patternProperties" in node:
                    # The admissible key set is then not enumerable.
                    return None
                return NoOtherProps(self._sibling_names(node, shape, pointer))
            if "patternProperties" in node:
                return None
            inner = self._node(value, here, None, OPAQUE)
            if isinstance(inner, Restated):
                return Restated(keyword)
            return OtherPropsSatisfy(self._sibling_names(node, shape, pointer), inner)

        if keyword == "not":
            # ``not``, ``if``, ``then`` and ``else`` grade the SAME object as
            # their parent, so a restatement inside one is proven against the
            # parent's declaration. A predicate the declaration already
            # enforces is true of every instance, which is exactly as sound
            # under a negation (where it makes the arm unsatisfiable) as it is
            # on the positive path.
            return Not(self._node(value, here, declaration, shape))
        if keyword == "allOf":
            return _conjoin(
                self._node(member, f"{here}/{index}", declaration, shape)
                for index, member in enumerate(value)
            )
        if keyword == "anyOf":
            return AnyOf(
                tuple(
                    self._node(member, f"{here}/{index}", declaration, shape)
                    for index, member in enumerate(value)
                )
            )
        if keyword == "oneOf":
            return OneOf(
                tuple(
                    self._node(member, f"{here}/{index}", declaration, shape)
                    for index, member in enumerate(value)
                )
            )
        if keyword == "if":
            return self._if_then(node, pointer, declaration, shape)
        if keyword in ("then", "else"):
            # Consumed by the sibling ``if``; without one, JSON Schema's own
            # reading is that the keyword asserts nothing.
            return Restated(keyword)

        if keyword in ("dependencies", "dependentRequired"):
            return _conjoin(self._dependencies(value, keyword, pointer, shape))
        if keyword == "dependentSchemas":
            return _conjoin(self._dependencies(value, keyword, pointer, shape))

        if keyword == "const":
            return ValueConst(value)
        if keyword == "enum":
            return ValueEnum(tuple(value))
        if keyword == "type":
            return ValueType((value,) if isinstance(value, str) else tuple(value))
        if keyword == "pattern":
            return ValuePattern(value)
        if keyword == "$ref":
            if value in declaration.get(_DECLARED_REFS, ()):
                return Restated(keyword)
            # A reference the declaration does not name is a narrowing: the
            # position has to satisfy the referenced schema as well. Resolve it
            # and compile what it says. An unresolvable reference refuses --
            # assuming an unproven equality is the one thing this module will
            # not do.
            return self._reference(value, here, declaration, shape)

        if keyword == "minLength":
            return ValueLen(minimum=value)
        if keyword == "maxLength":
            return ValueLen(maximum=value)
        if keyword == "minimum":
            return ValueBounds(ge=value)
        if keyword == "maximum":
            return ValueBounds(le=value)
        if keyword == "exclusiveMinimum":
            return ValueBounds(gt=value)
        if keyword == "exclusiveMaximum":
            return ValueBounds(lt=value)
        if keyword == "minItems":
            return ValueItems(minimum=value)
        if keyword == "maxItems":
            return ValueItems(maximum=value)
        if keyword == "uniqueItems":
            return ValueUnique() if value else Restated(keyword)
        if keyword == "minProperties":
            return PropCount(minimum=value)
        if keyword == "maxProperties":
            return PropCount(maximum=value)

        if keyword == "items":
            declared_items = declaration.get("items")
            if declared_items is not None and _equal(value, declared_items):
                return Restated(keyword)
            return EveryItem(self._node(value, here, declared_items, OPAQUE))
        if keyword == "contains":
            return SomeItem(self._node(value, here, None, OPAQUE))
        if keyword == "propertyNames":
            return KeysSatisfy(self._node(value, here, None, OPAQUE))

        return None

    def _sibling_names(
        self, node: dict[str, Any], shape: DeclaredShape, pointer: str
    ) -> tuple[str, ...]:
        """The members a node's own ``properties`` names, as field names."""
        declared = node.get("properties")
        if not isinstance(declared, dict):
            return ()
        resolved = (self._attribute(name, shape, pointer) for name in sorted(declared))
        return tuple(name for name in resolved if name is not None)

    # -- references --------------------------------------------------------- #

    def _reference(
        self, ref: str, pointer: str, declaration: dict[str, Any], shape: DeclaredShape
    ) -> Cond | None:
        """Compile the schema a ``$ref`` names, or ``None`` when unresolvable.

        The referenced schema lands at the position the reference occupies, so
        it is graded against the same declaration -- the target is constraint
        content, not a declaration of its own.
        """
        if ref in self._resolving:
            # A recursive reference states nothing new at this depth.
            return Restated("$ref")
        target = self._resolve_reference(ref)
        if target is None:
            return None
        self._resolving = self._resolving | {ref}
        try:
            return self._node(target, pointer, declaration, shape)
        finally:
            self._resolving = self._resolving - {ref}

    def _resolve_reference(self, ref: str) -> Any | None:
        document, fragment = (ref.split("#", 1) + [""])[:2] if "#" in ref else (ref, "")
        if document:
            resolved = self._resolve_document(document) if self._resolve_document else None
            if resolved is None:
                return None
        else:
            resolved = self._document
        return _follow_pointer(resolved, fragment)

    # -- productions needing two keys --------------------------------------- #

    def _if_then(
        self, node: dict[str, Any], pointer: str, declaration: Any, shape: DeclaredShape
    ) -> Cond:
        base = f"{pointer}/" if pointer else ""
        condition = self._node(node["if"], f"{base}if", declaration, shape)
        consequent = (
            self._node(node["then"], f"{base}then", declaration, shape) if "then" in node else None
        )
        alternative = (
            self._node(node["else"], f"{base}else", declaration, shape) if "else" in node else None
        )
        return IfThen(condition, consequent, alternative)

    def _dependencies(
        self, value: Any, keyword: str, pointer: str, shape: DeclaredShape
    ) -> list[Cond]:
        here = f"{pointer}/{keyword}" if pointer else keyword
        parts: list[Cond] = []
        for name in sorted(value):
            dependents = value[name]
            trigger = self._attribute(name, shape, pointer)
            if trigger is None:
                # A key the document may not carry never triggers.
                continue
            if isinstance(dependents, list):
                required = [
                    self._supplied(dependent, shape, pointer)
                    for dependent in dependents
                    if isinstance(dependent, str)
                ]
                if all(isinstance(part, Supplied) for part in required):
                    parts.append(
                        DependentRequired(
                            trigger,
                            tuple(part.name for part in required),  # type: ignore[union-attr]
                        )
                    )
                else:
                    parts.append(IfThen(Supplied(trigger), _conjoin(required), None))
                continue
            # The schema form of ``dependencies``: presence implies a subschema.
            parts.append(
                IfThen(
                    Supplied(trigger),
                    self._node(dependents, f"{here}/{name}", None, shape),
                    None,
                )
            )
        return parts

    # -- names -------------------------------------------------------------- #

    def _attribute(self, wire_name: str, shape: DeclaredShape, pointer: str) -> str | None:
        """The field name for a wire name, or ``None`` when the key cannot exist.

        Two different absences. A name the SCHEMA declares somewhere but the
        generated class does not is a dropped field, and refuses. A name the
        schema never declares anywhere is a key the document may not carry at
        all -- an AdCP request root that forbids ``creatives`` -- and that is a
        statically decidable predicate, not a gap.
        """
        attribute = shape.attribute(wire_name)
        if attribute is not None:
            return attribute
        if wire_name in self._schema_names:
            raise UnplaceableConstraintError(self._file, pointer, wire_name)
        return None

    def _supplied(self, wire_name: str, shape: DeclaredShape, pointer: str) -> Cond:
        attribute = self._attribute(wire_name, shape, pointer)
        if attribute is None:
            return Undeclarable(wire_name)
        return Supplied(attribute)


def _equal(left: Any, right: Any) -> bool:
    """Structural equality ignoring keys that assert nothing."""
    if isinstance(left, dict) and isinstance(right, dict):
        kept_left = {k: v for k, v in left.items() if k not in NON_ASSERTING_KEYS}
        kept_right = {k: v for k, v in right.items() if k not in NON_ASSERTING_KEYS}
        if set(kept_left) != set(kept_right):
            return False
        return all(_equal(kept_left[k], kept_right[k]) for k in kept_left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right) and type(left) is type(right)


def _conjoin(operands: Iterable[Cond]) -> Cond:
    kept: list[Cond] = [operand for operand in operands if not isinstance(operand, Restated)]
    if not kept:
        return Restated("conjunction")
    if len(kept) == 1:
        return kept[0]
    return AllOf(tuple(kept))


def _follow_pointer(document: Any, fragment: str) -> Any | None:
    """Resolve a JSON pointer fragment, honouring ``~0``/``~1`` escapes."""
    node = document
    for raw in fragment.lstrip("#").split("/"):
        if not raw:
            continue
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            try:
                node = node[int(token)]
            except (ValueError, IndexError):
                return None
            continue
        if not isinstance(node, dict) or token not in node:
            return None
        node = node[token]
    return node


def bundle_document_resolver(schema_dir: Path) -> ResolveDocument:
    """Resolve a ``$ref``'s document half against a schema bundle directory.

    The bundle spells the same reference two ways -- an absolute
    ``https://adcontextprotocol.org/schemas/<version>/<path>`` URL in the plain
    schemas and a ``#/$defs/external:<escaped path>`` pointer in the bundled
    ``mcp/`` variants -- so matching the longest path suffix that names a file
    under ``schema_dir`` covers both without a version table to keep in step.
    """
    cache: dict[str, Any | None] = {}

    def resolve(document: str) -> Any | None:
        if document not in cache:
            cache[document] = _load_bundle_document(schema_dir, document)
        return cache[document]

    return resolve


def _load_bundle_document(schema_dir: Path, document: str) -> Any | None:
    parts = [part for part in document.split("/") if part and not part.endswith(":")]
    for start in range(len(parts)):
        candidate = schema_dir.joinpath(*parts[start:])
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
    return None


def read_root_constraints(
    schema: dict[str, Any],
    declared: DeclaredShape,
    *,
    schema_file: str = "<schema>",
    resolve_document: ResolveDocument | None = None,
) -> RootConstraints:
    """Read everything a schema root states beyond its merged ``properties``.

    ``declared`` is the wire-to-field map of the class the generator emits for
    this root; compiled predicates name attributes, not wire names.

    ``resolve_document`` resolves the document half of a ``$ref`` the schema's
    own ``$defs`` do not hold. Without one, such a reference refuses -- the
    parser does no I/O of its own.

    Raises :class:`UnexpressibleKeywordError` for a keyword the grammar cannot
    compile, and :class:`UnplaceableConstraintError` for a constraint naming a
    property no class declares. Both abort generation.
    """
    return _Parser(schema_file, declared, resolve_document).read(schema)
