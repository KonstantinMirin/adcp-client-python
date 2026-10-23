"""The compiler half: a class declaration in, Python out -- and the machinery a
lowering is handed to build one.

``docs/plan/rebuild-plan.md`` §1 splits the pipeline at a DECISION rather than at
a translation.  Our walk reads the JSON Schema and decides what each node becomes -- a class, an
annotation, an enumeration or a rule -- what it is called, which fields it has
and what constrains them.  This module takes that declaration and nothing else,
and hands it to
``datamodel-code-generator``'s pydantic-v2 MODEL layer, which writes the Python.

**D13 puts the shared machinery here and not in ``codegen.emit``**, and the reason
is an import rule rather than a preference.  A lowering under ``codegen/lower/``
imports this module and ``codegen.refusal`` and nothing else of this package: it
never imports ``codegen.emit``, because ``emit`` holds the dispatch table that
names it, and an import back the other way closes a cycle that ``python -m
codegen.emit`` resolves into TWO module objects rather than into an ``ImportError``
-- the failure D12 already exists to prevent for ``Refusal``, one layer in.  A
``TYPE_CHECKING`` import hides that cycle from the type checker without removing
it, because the lowering needs the machinery at RUN time.  So the machinery moves,
which is what makes the one-directional import true rather than intended.

What moved, in D13's own terms: the field builder (:func:`fields`), the class
declarer (:func:`declare_object`, and :func:`declare_alias` beside it for a root
D2 makes an alias), and the carriers a lowering is handed (:class:`Module`,
:class:`Shape`, :class:`Target`, :class:`Decided`), with the keyword screen
(:func:`check_keywords`), the name rules (D3) and :func:`lower_object` -- which is
:func:`fields` plus :func:`declare_object` and has nothing else in it -- alongside.

**What did NOT move is the per-node dispatch.**  ``emit.decide_type`` answers "what
IS this node", and for an array, a mapping or a multi-type node the answer lives in
``codegen.lower.containers``.  Putting it here would make this module import a
lowering; leaving :func:`fields` to call it directly would make this module import
``emit``.  So it arrives the way reference resolution already arrives --
:class:`Module` carries it, ``emit`` supplies it, and the default refuses -- which
is the same mechanism as ``Module.bind`` and for the same reason.

**dmcg's parser never runs.**  The parser is the half that decides names and
structure from a schema, and that is our half -- it is where every judgement
about AdCP's bundle lives, and no library has that knowledge.  What dmcg has that
we would otherwise rewrite is the rendering: annotated constraints, defaults,
descriptions, aliases, ``ConfigDict``, the ``| None`` branch of an optional, and the
import set each of those needs.  A hand-rolled text emitter dropped three of
three schema defaults and all 142 property descriptions in the population it
covered, not because anyone decided to, but because carrying them is rendering
work and rendering work was being rewritten.

**Two gates, both silent, both measured.  Neither is a reason to avoid the
compiler; they are how it is driven.**

1. **Constraints are spelled in JSON Schema, not pydantic.**  ``Constraints``
   declares every field under its JSON-Schema alias with no
   ``populate_by_name``, so ``Constraints(ge=1, le=100)`` sets NOTHING -- empty
   ``model_fields_set``, empty dump, and a rendered class with no bound on the
   field.  ``Constraints(minimum=1, maximum=100)`` renders ``Field(ge=1,
   le=100)``.  :data:`CONSTRAINTS` is therefore the document's own vocabulary,
   passed through unchanged.
2. **``extras`` cannot carry a constraint.**  dmcg's ``_EXCLUDE_FIELD_KEYS``
   strips ``gt ge lt le multiple_of min_length max_length pattern`` out of
   ``extras`` on the way to ``Field(...)``.  A constraint goes through
   ``constraints=`` and nowhere else; ``extras`` carries the description.

A third gate, found here: **``class_body_lines`` is reserved.**  Passing it in
``extra_template_data`` raises ``Error: class_body_lines is reserved for
generator-owned built-in template data``, so the ``__adcp_schema__`` line reaches
the class body through ``_append_internal_template_data``, which is dmcg's own
channel for a project-produced line a built-in template renders as code.  The
alternative is a vendored copy of ``BaseModel.jinja2``, which is a template that
drifts from the pinned compiler on every upgrade for one line of output.  A dmcg
release that renames the method fails loudly: a class with no ``__adcp_schema__``
has no schema, so every grade of it fails rather than quietly passing.
"""

from __future__ import annotations

import keyword
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from datamodel_code_generator import PythonVersion
from datamodel_code_generator.model import DataModelFieldBase
from datamodel_code_generator.model.enum import Enum as DmcgEnum
from datamodel_code_generator.model.enum import EnumMemberValue, IntEnum, StrEnum
from datamodel_code_generator.model.pydantic_v2 import BaseModel, DataModelField
from datamodel_code_generator.model.pydantic_v2.base_model import Constraints
from datamodel_code_generator.model.pydantic_v2.types import DataTypeManager
from datamodel_code_generator.reference import Reference
from datamodel_code_generator.types import DataType
from jsonschema import Draft7Validator
from pydantic import BaseModel as PydanticBaseModel

from adcp.types._base import SchemaRef
from codegen import refusal
from codegen.refusal import Refusal

#: The import path of the hand-written base every emitted module imports from.
#: Here rather than in ``emit`` because :func:`declare_alias` writes the two
#: statements a root alias needs and a lowering calls it (D13's import rule).
BASE_MODULE = "adcp.types._base"

SCALAR = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}

#: The floor of ``requires-python``.  It decides the rendered spelling of an
#: optional (``T | None`` rather than ``Optional[T]``), so it is named once here
#: and never inferred from the interpreter running the emitter -- the output is a
#: function of (bundle, document set, this package) and of nothing else (P7).
#:
#: It MOVED with the floor rather than being left behind: D2's ``StrEnum`` is
#: 3.11, so ``pyproject`` raised ``requires-python`` and this would otherwise
#: have stated a floor the project no longer has.  Measured byte-neutral over the
#: whole emitted population -- 0 of 575 files differ between PY_310 and PY_311 --
#: so the two can be kept in agreement for free, which is the only reason to
#: touch it at all.
TARGET = PythonVersion.PY_311

#: The JSON Schema keywords this module passes to ``constraints=``, in the
#: document's own spelling, which is gate 1.  Everything else a document can say
#: about a value is either a type (and so part of the decided ``Type``), an
#: annotation (and so part of ``extras``), or a keyword our walk refuses.
CONSTRAINTS = (
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
)

#: Absent is not the same as ``None``: a property whose schema declares
#: ``default: null`` has a default and it is ``None``.
MISSING = object()

_TYPES = DataTypeManager(
    python_version=TARGET,
    use_union_operator=True,
    use_standard_collections=True,
)


@dataclass(frozen=True)
class Type:
    """What our walk decided a node's Python type is.

    ``path`` is a dotted path the compiler resolves to a type and an import
    (``"int"``, ``"datetime.date"``, ``"pydantic.AnyUrl"``, ``"typing.Any"``), or
    a bare symbol when ``local`` -- a class declared in the same module, or a
    symbol the module writer imports from a sibling module because the document
    referenced another document (P2).  The compiler adds no import for a local
    symbol, which is right in both cases: a sibling class needs none, and a
    cross-document import is the module writer's, derived from the two document
    paths.

    A local symbol is a REFERENCE to another model and not a custom type, and
    that distinction decides a config: ``is_custom_type`` makes dmcg add
    ``arbitrary_types_allowed=True`` to the class's ``ConfigDict``, which is a
    relaxation of pydantic nobody decided and which D7 does not derive.  Every
    local symbol here is something this pipeline emitted -- a sibling class or an
    ``Annotated`` alias -- so pydantic resolves all of them and the relaxation is
    both unasked for and untrue.

    A CONTAINER is the same vocabulary one level up: ``container`` names the shape
    and ``of`` carries the types inside it.  It is here rather than in the
    container lowering because deciding ``list[X]`` is the walk's judgement and
    writing ``list[X]`` is the compiler's rendering -- a lowering that assembled
    the annotation text itself would be the second half of the seam doing the
    first half's job, and the text is exactly what §1 says the compiler is for.

    ``of`` is deliberately one field for three shapes, because the compiler reads
    all three out of dmcg's single ``data_types``: the element of a list, the
    VALUE of a mapping, and the arms of a union.  A mapping's key is the one type
    that is not in it, because dmcg carries it in its own ``dict_key`` slot --
    which is what makes D5's typed key expressible at all.

    **A container carries no constraints of its own here.**  A bound on a list is
    a bound on the FIELD holding it (``Property.constraints``, rendered
    ``Field(min_length=...)``), and a bound on what is INSIDE a container has no
    slot in dmcg's ``DataType`` -- which is the gap D5 closes by naming the
    inner type rather than the gap it looks like.  The container lowering refuses
    an inner constraint it cannot name instead of dropping it.
    """

    path: str = ""
    local: bool = False
    #: ``"list"``, ``"dict"`` or ``"union"`` when this type is a container.
    container: str = ""
    #: A list's element, a mapping's value, or a union's arms.
    of: tuple[Type, ...] = ()
    #: A mapping's key, and only a mapping has one (D5 types it from the document).
    key: Type | None = None
    #: D2's ``const`` row: the one value the node PINS, as a 1-tuple, and ``()`` for
    #: every other node.  The walk decides the value and the compiler writes the
    #: ``Literal``, which is §1's seam -- and here it is load-bearing rather than
    #: tidy.  Written as ``Type("Literal[%r]" % value, local=True)`` instead, the
    #: annotation reached dmcg as a ``Reference`` PATH, and ``treat_dot_as_module``
    #: read the dot in a value like ``account.status_changed`` as a module qualifier
    #: and kept the last segment: ``Literal['account.status_changed']`` rendered as
    #: ``status_changed']``, a module that does not parse.  dmcg's own ``literals``
    #: carrier renders the value, escapes it (``"quo'te"`` comes back
    #: ``Literal["quo'te"]``) and reports the ``typing.Literal`` import itself.
    #:
    #: A tuple and not a bare value because ``const: null`` is a pinnable value, so
    #: a ``None`` default could not be told from an absent one.  One member is all
    #: a ``const`` has; the plural is dmcg's spelling of the slot.
    literals: tuple[Any, ...] = ()

    def data_type(self) -> Any:
        if self.literals:
            return _TYPES.data_type(literals=list(self.literals))
        if self.container == "list":
            return _TYPES.data_type(is_list=True, data_types=[t.data_type() for t in self.of])
        if self.container == "dict":
            return _TYPES.data_type(
                is_dict=True,
                data_types=[t.data_type() for t in self.of],
                dict_key=self.key.data_type() if self.key is not None else None,
            )
        if self.container == "union":
            return _TYPES.data_type(data_types=[t.data_type() for t in self.of])
        if self.path == "None":
            return _TYPES.data_type(type="None")
        if self.local:
            return _TYPES.data_type(
                reference=Reference(path=f"#/{self.path}", original_name=self.path, name=self.path)
            )
        return _TYPES.get_data_type_from_full_path(self.path, is_custom_type=False)


@dataclass(frozen=True)
class Property:
    """One decided field.

    ``name`` is the Python attribute and ``wire`` the document's property key.
    They differ only when pydantic cannot carry a field under the key's own
    spelling, and then ``wire`` becomes an ``alias`` -- the only accepted
    spelling, because nothing here sets ``populate_by_name``.
    """

    name: str
    wire: str
    type: Type
    required: bool
    default: Any = MISSING
    description: str | None = None
    #: JSON Schema spelling, per gate 1.
    constraints: Mapping[str, Any] = field(default_factory=dict)
    #: The document's ``format``, where the walk did NOT turn it into a type.
    #: D5 lets a format select one (``emit.FORMAT_TYPES``), and a selected type
    #: states the format in its own rendered schema -- so this field is the other
    #: case, and it rides as ``json_schema_extra`` so the fact reaches the
    #: model's schema where the comparison grades it.  The two are exclusive by
    #: construction (``emit.Decided``): a format is in the type or in here, and
    #: never in both and never nowhere.  Dropping it would lose a fact the
    #: document states.
    format: str | None = None
    #: D6's ``uniqueItems`` on the array this field holds.  The RULE is what enforces
    #: it on the constructor (``adcp.types._runtime.UniqueItems``); this flag is the
    #: other half, and it rides the same ``json_schema_extra`` channel as
    #: :attr:`format` and for the same reason -- pydantic removed ``unique_items`` in
    #: v2, so no annotation states the fact, and the schema comparison reads
    #: ``uniqueItems`` off a model's rendered schema (``harness.FACTS``).  Rendering
    #: it where the document states it is what keeps the comparison symmetric: the
    #: fact is TRUE of the model, because the schema half and the rule both enforce
    #: it, so no admission row is needed in either direction.
    distinct: bool = False


@dataclass(frozen=True)
class Class:
    """One decided class.  ``ref`` is the schema it will carry and grade against."""

    name: str
    ref: SchemaRef
    properties: tuple[Property, ...]
    description: str | None = None
    #: D8: ``forbid``, ``allow``, or ``None`` to leave the base's default.
    extra: str | None = None
    #: D7: the symbols this class's document COMPOSES, in the conjunct order the
    #: document lists them.  Empty leaves ``custom_base_class``, which is
    #: ``AdCPBaseModel`` and is every class with nothing to compose; a non-empty
    #: tuple replaces it, and ``AdCPBaseModel`` arrives through the bases because
    #: every base is itself an emitted class.  The symbols are names the module
    #: writer has already imported -- the compiler adds no import for a base, for
    #: the same reason ``Type.local`` adds none: a cross-document import is
    #: derived from the two document paths (D1) and is the module writer's.
    #: §4's union row derives them from the SHAPE rather than from a composition --
    #: a base is ``(BranchDispatchMixin, AdCPBaseModel)`` and a branch is its base --
    #: so naming any of them replaces ``custom_base_class`` and a caller that wants
    #: ``AdCPBaseModel`` in the list says so.
    bases: tuple[str, ...] = ()
    #: Lines appended to the class body verbatim, after ``__adcp_schema__``.  The channel
    #: for a fact the emitter has to write onto a class because it is not recoverable at
    #: run time (``_branch_models``, ``_ROOT_REQUIRED``, ``_branch_combinator``), and the
    #: one thing in this module that is text rather than a decision -- which is why it is a
    #: parameter here rather than a second renderer somewhere else.
    body_lines: tuple[str, ...] = ()
    #: D8's typed row: the type of a property the class does not DECLARE, which
    #: pydantic validates through ``__pydantic_extra__``.  It is a mapping, because
    #: ``additionalProperties`` types the values under keys the document does not
    #: name -- D5 types the key too, so it is the same ``dict[K, V]`` a mapping node
    #: lowers to and is decided by the same row.
    extra_type: Type | None = None


@dataclass
class Rendered:
    text: str
    #: ``(module, name)`` pairs the rendered text needs, which the module writer
    #: merges with its own and sorts.
    imports: set[tuple[str, str]] = field(default_factory=set)


def _field(prop: Property) -> DataModelField:
    extras: dict[str, Any] = {}
    if prop.description:
        extras["description"] = prop.description
    # One ``json_schema_extra`` dict, two facts that can both be true of one field:
    # a ``format`` no type was selected for, and D6's ``uniqueItems``.  Assigning
    # rather than merging dropped whichever came second.
    extra_schema = {
        **({"format": prop.format} if prop.format else {}),
        **({"uniqueItems": True} if prop.distinct else {}),
    }
    if extra_schema:
        extras["json_schema_extra"] = extra_schema
    constraints = {k: v for k, v in prop.constraints.items() if k in CONSTRAINTS}
    kwargs: dict[str, Any] = {}
    if prop.default is not MISSING:
        # ``has_default`` is what the template reads; the value alone is not
        # enough, because ``None`` is a legitimate default.
        kwargs["default"] = prop.default
        kwargs["has_default"] = True
    if prop.wire != prop.name:
        kwargs["alias"] = prop.wire
        kwargs["original_name"] = prop.wire
    return DataModelField(
        name=prop.name,
        data_type=prop.type.data_type(),
        required=prop.required,
        constraints=Constraints(**constraints) if constraints else None,
        extras=extras,
        use_annotated=True,
        target_python_version=TARGET,
        **kwargs,
    )


def render_alias(
    symbol: str,
    type_: Type,
    constraints: Mapping[str, Any],
    *,
    description: str | None = None,
    format: str | None = None,  # noqa: A002 -- the JSON Schema keyword's own name
) -> Rendered:
    """``<symbol> = <annotation>`` for D2's root-scalar row.

    A scalar root has no class to hang itself on, so it is a module-level
    ``Annotated`` alias.  The ANNOTATION is still the compiler's -- the same
    ``DataModelField`` a class property gets, read off the field rather than out
    of a class body -- so a ``minLength`` on an alias and a ``minLength`` on a
    property cannot come to be spelled two different ways, and gate 1 applies to
    both.  The statement around it is the module writer's, because no template
    has a slot for a line beside an alias.

    ``required=True``: an alias is the document's own type, with no presence
    question to answer.  The ``| None`` branch belongs to an optional PROPERTY, and
    a property referencing this alias gets it from its own field.

    The description rides in ``Field`` and not in a docstring, because an alias
    has no docstring slot: five of this step's documents are scalar roots whose
    root ``description`` was dropped for exactly that reason, and a
    ``Field(description=...)`` puts it in the alias's own JSON schema where the
    schema comparison finds it.
    """
    fld = _field(
        Property(
            name=symbol,
            wire=symbol,
            type=type_,
            required=True,
            constraints=constraints,
            description=description,
            format=format,
        )
    )
    out = Rendered(text=f"{symbol} = {fld.annotated or fld.type_hint}")
    for imp in fld.imports:
        if imp.from_ and imp.import_:
            out.imports.add((imp.from_, imp.import_))
    out.imports.add(("adcp.types._base", "SchemaRef"))
    return out


#: D2's two enumeration bases, keyed by the member type the WALK decided, in the
#: document's own vocabulary (``codegen.lower.enum.BASES`` produces the key).
#:
#: The class is chosen rather than derived from a ``type_`` argument: dmcg's
#: ``Enum.__init__`` reads ``type_`` only to ADD a ``str``/``int`` base class
#: beside the enumeration one, so passing it renders ``class X(str, StrEnum)`` --
#: which is the pre-3.11 spelling ``StrEnum`` exists to replace, and whose members
#: ``str()`` as ``"X.BROAD"`` rather than as ``"broad"``.
#:
#: ``boolean`` and ``number`` are absent because the compiler has no base for
#: them; ``codegen.lower.enum`` refuses such a node by name, with ``bool``
#: carrying its own reason.
_ENUM_BASES: dict[str, type[DmcgEnum]] = {"string": StrEnum, "integer": IntEnum}


@dataclass(frozen=True)
class Member:
    """One decided enumeration member: the name the walk chose, and its value."""

    name: str
    value: Any
    #: The document's ``enumDescriptions`` entry for this value, where it has one.
    #: It reaches the rendered class as the member's own docstring, which is the
    #: compiler's own slot for it -- 137 of the bundle's enum nodes carry the
    #: block and a previous attempt dropped every one of them, for the same
    #: reason the hand-rolled renderer dropped 142 property descriptions: nothing
    #: compares an annotation that changes no accepted set.
    description: str | None = None


@dataclass(frozen=True)
class Enumeration:
    """One decided enumeration.  ``kind`` names the base, in JSON Schema's words.

    No ``ref``, and that is the one place an enumeration differs from
    :class:`Class`: ``Enum.jinja2`` has no ``class_body_lines`` slot, so an
    ``__adcp_schema__`` line cannot reach an enum's class body through the
    compiler at all -- and D9 forbids writing it in afterwards.  A ROOT enum
    therefore binds the reference and ``strict_validate`` at module level, which
    is what D2's root-scalar row already does for the same reason (a node with no
    ``AdCPBaseModel`` to hang a classmethod on).  An INLINE enum is a type its
    parent's field names, like any annotation.
    """

    name: str
    kind: str
    members: tuple[Member, ...]
    description: str | None = None


def _member(member: Member) -> DataModelFieldBase:
    """One member as the compiler's field.

    ``EnumMemberValue`` is dmcg's own carrier for a string member, and it is what
    renders the value as a Python literal with the escaping the compiler owns
    (quotes, backslashes, newlines, the null byte).  A bare ``str`` would reach
    the template as that text and would be read as a rendered default.

    ``use_inline_field_description`` is what puts the description in the class
    body: a single-line one becomes ``\"\"\"text\"\"\"`` under the member, and a
    multi-line one an indented triple-quoted block.
    """
    return DataModelFieldBase(
        name=member.name,
        data_type=DataType(),
        default=EnumMemberValue(member.value) if isinstance(member.value, str) else member.value,
        required=True,
        extras={"description": member.description} if member.description else {},
        use_inline_field_description=True,
    )


def render_enum(decided: Enumeration) -> Rendered:
    """The Python for one decided enumeration, and the imports it needs.

    The members' NAMES are rendered verbatim (``{{ field.name }}``): the compiler
    names nothing here, which is why ``codegen.lower.enum`` owns the naming and
    why the injectivity check binds to its function.
    """
    model = _ENUM_BASES[decided.kind](
        reference=Reference(
            path=f"#/{decided.name}", original_name=decided.name, name=decided.name
        ),
        fields=[_member(m) for m in decided.members],
        description=decided.description or None,
    )
    out = Rendered(text=model.render().rstrip("\n"))
    for imp in model.imports:
        if imp.from_ and imp.import_:
            out.imports.add((imp.from_, imp.import_))
    return out


def render(decided: Class) -> Rendered:
    """The Python for one decided class, and the imports it needs."""
    config = {"extra": decided.extra} if decided.extra else None
    extra_template_data: defaultdict[str, Any] = defaultdict(dict)
    if config:
        extra_template_data[decided.name] = {"config": config}
    model = BaseModel(
        reference=Reference(
            path=f"#/{decided.name}", original_name=decided.name, name=decided.name
        ),
        fields=[_field(p) for p in decided.properties],
        base_classes=[Reference(path=f"#/{b}", original_name=b, name=b) for b in decided.bases],
        custom_base_class="adcp.types._base.AdCPBaseModel",
        description=decided.description or None,
        extra_template_data=extra_template_data,
    )
    # Gate 3: the one line a built-in template renders from project-produced
    # code.  ``repr`` of a ``SchemaRef`` is a valid Python expression naming the
    # type, so there is no spelling of the ref in this module to drift from the
    # one in ``_base``.
    #
    # ``_append_internal_template_data`` APPENDS to a list, measured on 0.86.0, so a
    # caller's own lines follow the ref rather than replacing it.
    body = [f"__adcp_schema__: ClassVar[SchemaRef] = {decided.ref!r}"]
    extra_field = None
    if decided.extra_type is not None:
        # ``__pydantic_extra__`` is a dunder and not a field: declared as one it
        # would be a model field named ``__pydantic_extra__``, which pydantic reads
        # as the extras store rather than as a property, so it goes through the same
        # channel the schema reference does.  The ANNOTATION is still the compiler's
        # -- read off a ``DataModelField`` like every other type hint in this module
        # -- so a mapping's rendering and an extras store's cannot come to be two
        # spellings of one decision.  Only the ``name: hint`` line is ours.
        extra_field = _field(
            Property(
                name="__pydantic_extra__",
                wire="__pydantic_extra__",
                type=decided.extra_type,
                required=True,
            )
        )
        body.append(f"__pydantic_extra__: {extra_field.type_hint}")
    for line in (*body, *decided.body_lines):
        model._append_internal_template_data("class_body_lines", line)  # noqa: SLF001 -- dmcg's own channel; see the module docstring
    out = Rendered(text=model.render().rstrip("\n"))
    for imp in model.imports:
        if imp.from_ and imp.import_:
            out.imports.add((imp.from_, imp.import_))
    if extra_field is not None:
        for imp in extra_field.imports:
            if imp.from_ and imp.import_:
                out.imports.add((imp.from_, imp.import_))
    # ``ConfigDict`` is kept exactly when the rendered text uses the name, read
    # off the text rather than off what we asked for.  dmcg reports the import
    # for a model whose rendering MIGHT need one, and it also renders a config
    # WE did not ask for: a class with a look-around ``pattern`` gets
    # ``regex_engine="python-re"`` -- the same decision ``AdCPBaseModel`` makes,
    # reached independently.  Deciding by our own ``config`` argument instead
    # deleted the import that line needs, and the only class it affected
    # (``core/sla-window.json``) happened to declare ``additionalProperties`` as
    # well, so the module imported anyway and the defect was latent.  A
    # perturbation that stopped deriving ``extra`` turned it into a NameError.
    if "ConfigDict(" in out.text:
        out.imports.add(("pydantic", "ConfigDict"))
    else:
        out.imports.discard(("pydantic", "ConfigDict"))
    out.imports.add(("typing", "ClassVar"))
    out.imports.add(("adcp.types._base", "SchemaRef"))
    return out


# --------------------------------------------------------------------------- #
# the machinery a lowering is handed (D13)
# --------------------------------------------------------------------------- #
#: DRAFT-07's own annotation keywords: names the draft DEFINES and that annotate a
#: node without constraining an instance.  ``default`` and ``description`` are
#: carried by the compiler (they are rendering, and rendering is what the compiler
#: is for); the rest have nowhere to go and are never a reason to refuse.
_DRAFT_ANNOTATIONS = frozenset(
    {
        "$schema",
        "$id",
        "$comment",
        "title",
        "description",
        "examples",
        "example",
        "default",
        "deprecated",
        "readOnly",
        "writeOnly",
    }
)

#: THE BUNDLE'S OWN annotation names: names draft-07 does not define at all, which
#: this bundle uses to annotate a node, ENUMERATED and never derived from a prefix.
#:
#: An unknown keyword that COULD CONSTRAIN an instance must keep refusing, because
#: that refusal is what keeps the generator from emitting a class quietly wider than
#: its author meant.  So membership here is by name and by measurement.
#:
#: **The census, over all 1,054 portable documents** (every key at a schema position
#: that draft-07 does not define, is not ``x-*``, and is not already admitted; all
#: 1,054 declare draft-07, so one draft decides the vocabulary): 24 names over 251
#: sites.  Two are admitted here:
#:
#: * ``notes`` -- 2 sites, 2 documents, both at a root, a list of English sentences
#:   in each.  It annotates the document for a reader.
#: * ``enumMetadata`` -- 4 sites, 4 documents, all at a root.  ``lower.enum.HANDLED``
#:   already admitted it on the reason written there -- it states nothing about an
#:   instance, the ``enum`` having already closed the value set -- for the three
#:   whose root IS an enum.  The fourth (``core/media-buy-available-action-id.json``)
#:   is a UNION root, which that set does not reach.  Admitting it HERE is the same
#:   decision in one place rather than two, so it is removed from that set.
#:
#: And twenty-two are not, each for a stated reason:
#:
#: * ``enumDescriptions`` (137 sites, 135 documents) is CARRIED, not ignored: the
#:   enum row reads it into the member docstrings.  Admitting it here would delete a
#:   fact the SDK emits.
#: * ``discriminator`` (81 sites, 73 documents, 7 refusals) COULD CONSTRAIN AN
#:   INSTANCE -- in OpenAPI it selects which branch a payload resolves to, a job §4
#:   gives to ``DataType.discriminator``.  It keeps refusing.
#: * ``errorMessage`` (2 sites, 1 document) constrains nothing, and its document
#:   refuses on ``if`` first, so admitting it would change no outcome.  Nothing is
#:   admitted on no evidence.
#: * The other 19 -- ``version``, ``lastUpdated``, ``last_updated``, ``mappings``,
#:   ``vocabulary``, ``governance``, ``extensions``, ``_generated``,
#:   ``_generatedAt``, ``adcp_version``, ``architecture``, ``asset_types``,
#:   ``baseUrl``, ``prerelease``, ``protocol_layers``, ``published_version``,
#:   ``stability``, ``usage_notes``, ``versioning`` -- ARE NOT ANNOTATIONS.  They are
#:   a document's own INSTANCE DATA at a schema root: five registry, vocabulary and
#:   index documents carry their payload beside their schema.  Measured: 4 of those 5
#:   refuse on ``type`` ("no D2 row selects this root") and not on a payload key at
#:   all, so admitting the 19 changes nothing for them and buys the fifth
#:   (``registries/v1-canonical-mapping.json``) by calling a registry's 300-line
#:   ``mappings`` payload an annotation.  That is the blanket allowance in another
#:   shape, and the set would then grow by a data field name per registry.  The fifth
#:   stays refused, which is a designed outcome.
BUNDLE_ANNOTATIONS = frozenset({"notes", "enumMetadata"})

#: The ONE set every reader asks, so the two halves above cannot drift apart from a
#: second literal.  Read by :func:`check_keywords` and by the three places that ask
#: what a node DECLARES (``lower.union._plan``, ``lower.product._own``,
#: ``lower.rules._own``) -- the same question, since a key that annotates without
#: constraining is not a declaration either.
ANNOTATIONS = _DRAFT_ANNOTATIONS | BUNDLE_ANNOTATIONS

#: Every name draft-07 DEFINES, read off the draft's own meta-schema rather than
#: typed here, and used for one thing: to tell a keyword no row lowers YET from a
#: name no row can EVER lower (:func:`check_keywords`).
DRAFT07 = frozenset(Draft7Validator.META_SCHEMA["properties"])

#: **D6's six keyword families, as the set a keyword screen admits.**
#:
#: Here rather than in ``codegen.lower.rules`` for the reason ``ANNOTATIONS`` is here,
#: and it is the same reason verbatim: ``compiler`` sits BELOW both ``codegen.lower``
#: and ``codegen.bundle``, so every reader can import it, while a lowering may not
#: import a sibling lowering (D13).  Three lowerings need it -- the object row screens
#: an object node with it, the ``allOf`` row screens a root, the union row screens a
#: root and each branch -- and two of the three cannot reach ``rules`` at all.  Two
#: copies of the set would be one place for a screen to admit a keyword the lowering
#: writes nothing for, which is a model wider than its document.
#:
#: ``codegen.lower.rules`` re-exports this as its own ``KEYWORDS`` rather than
#: restating it, which is the direction D13 fixes.
RULE_KEYWORDS = frozenset(
    {
        "oneOf",
        "anyOf",
        "if",
        "then",
        "else",
        "dependencies",
        "minProperties",
        "maxProperties",
        "uniqueItems",
        "not",
    }
)

#: The two keywords holding a BAG OF NAMED SUBSCHEMAS, admitted at every node and
#: separate from :data:`ANNOTATIONS` because the reason is different.
#:
#: Neither keyword asserts anything about an instance in any draft this bundle
#: declares: a section is a place to PUT a subschema, and what it holds reaches an
#: instance only through a ``$ref``.  So admitting one drops nothing -- the node a
#: reference names is declared when the reference asks for it
#: (:func:`local_reference`), and a node nothing references cannot change what the
#: document accepts, which is the whole of what a refusal protects (P3).
#:
#: One place rather than a member of each row's own handled set, because the screen
#: runs at 13 call sites across five modules and the answer is the same at every one:
#: the section is not a root kind and not a row's business.  Measured on the 3.2
#: bundle: 45 documents declare a section at their root and 1 declares one deeper
#: (``brand/get-brand-identity-response.json#/oneOf/0/properties/fonts``), so a
#: root-only admission would leave that one refusing on a keyword this now handles.
#:
#: ``codegen.bundle`` imports this set rather than restating it, which is the
#: direction D13 fixes: ``bundle`` imports this module and never the other way.
DEFINITION_SECTIONS = frozenset({"definitions", "$defs"})


# --------------------------------------------------------------------------- #
# names (D3)
# --------------------------------------------------------------------------- #
def class_name(title: str) -> str:
    """``pascal_case`` that keeps an acronym: only the first letter of a word is
    touched, so ``TMPX Chunk`` stays ``TMPXChunk`` and does not become
    ``TmpxChunk``."""
    words: list[str] = []
    cur = ""
    for ch in title:
        if ch.isalnum():
            cur += ch
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return "".join(w[:1].upper() + w[1:] for w in words)


def field_name(key: str) -> str:
    """The Python field name for a property key, which is the key itself unless
    pydantic cannot carry a field under that name.

    A key is carried as-is or it is carried under an ALIAS, never dropped.  The
    bundle has keys a Python attribute cannot spell (``$schema``) and keys
    pydantic reads as something other than a field: a leading underscore makes a
    private attribute and no field at all, so
    ``core/truncation-sentinel.json``'s required ``_truncation`` was silently
    absent from the model -- the model refused the document's own instance AND
    accepted an instance omitting the required key, in the same class.

    The alias is the ONLY accepted spelling (no ``populate_by_name``), so the
    model's accepted set stays the document's: the wire name is accepted and the
    Python name is not a second way in.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in key).lstrip("_")
    if not name or name[0].isdigit():
        name = f"f_{name}"
    while (
        keyword.iskeyword(name) or name.startswith("model_") or hasattr(PydanticBaseModel, name)
    ):
        name += "_"
    return name


def schema_ref(document: str, pointer: str) -> SchemaRef:
    """The schema reference a class at ``pointer`` of ``document`` carries."""
    return SchemaRef(document, f"#{pointer}")


# --------------------------------------------------------------------------- #
# the carriers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Shape:
    """One class's own field set: each property key's schema node, and which keys
    are required.

    Written by :func:`declare_object` for every class the emitter declares, and
    carried to a lowering by :class:`Target`, so it is produced in ONE place and
    a second copy cannot disagree about what a class declares.

    Read by TWO of D2's rows, not one: the ``allOf`` row, and the union row for a
    branch whose root composes as well -- a subclass has to know what it inherits
    in order not to restate it.

    TRANSITIVE by construction: a class that itself composes records its inherited
    keys here too, so a subclass reads one map rather than walking a chain of base
    documents.
    """

    properties: Mapping[str, dict]
    required: frozenset[str]


@dataclass(frozen=True)
class Target:
    """What a resolved ``$ref`` gives the lowering that asked for it.

    ``module`` and ``symbol`` are what an ANNOTATION needs.  ``shape`` is what an
    ``allOf`` conjunct needs, and it is ``None`` when the target is not a class --
    D2's root-scalar row is an ``Annotated`` alias, and subclassing one is a
    ``TypeError`` at import, so a lowering refuses it as a base rather than
    writing a module that cannot be imported.
    """

    module: str
    symbol: str
    shape: Shape | None = None


@dataclass(frozen=True)
class Decided:
    """What the walk decided one schema node IS.

    ``format`` is set only when ``type`` does NOT already carry the format -- the
    compiler then states it as an annotation rather than as a type.  Keeping the
    two separate here is what makes the drop impossible to make by accident: a
    format is either in the type or in this field, and never nowhere.
    """

    type: Type
    constraints: dict[str, Any] = field(default_factory=dict)
    format: str | None = None


def _no_binder(uri: str, pointer: str) -> Target:
    """The default binder: a document lowered on its own resolves no reference.

    ``emit`` supplies the real one, which owns the walk.  Lowering a document
    without it refuses its references by name rather than inventing an import, so
    there is no path on which a reference is silently dropped.
    """
    raise Refusal("$ref", pointer, f"no reference binder: {uri} cannot be resolved to a module")


def _no_decider(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """The default node decider, and it refuses for ``_no_binder``'s reason.

    ``emit.decide_type`` is the real one.  It stays in ``emit`` because an array, a
    mapping and a multi-type node are answered by ``codegen.lower.containers``, so
    a decider living HERE would make this module import a lowering -- and a
    :func:`fields` that called into ``emit`` directly would make this module import
    the entry point, which is the cycle D13 removes.  Carried on the :class:`Module`
    instead, exactly as ``bind`` is carried, so a lowering decides a nested node
    without naming ``emit``.
    """
    raise Refusal("type", pointer, f"no node decider: {node.get('type')!r} cannot be decided")


@dataclass
class Module:
    document: str
    #: The symbol the document's ROOT binds, which is D3's parent for a name derived
    #: inside the module: :func:`local_reference` qualifies an entry's own key with it,
    #: the way :func:`fields` qualifies a property's.  ``emit.lower_document`` sets it
    #: from the title before the row runs.  Empty by default, so a document lowered
    #: outside it derives a bare, unqualified name rather than one naming a root that
    #: is not there -- the same shape as ``asserted`` and ``named`` being empty.
    root: str = ""
    #: ``(uri, pointer) -> Target``; see ``emit.emit``.
    bind: Callable[[str, str], Target] = _no_binder
    #: ``(node, pointer, name_hint, mod) -> Decided``; see ``emit.decide_type``.
    decide: Callable[[dict, str, str, "Module"], Decided] = _no_decider
    #: The formats this document's own draft asserts; see ``emit.asserted_formats``.
    #: Empty by default, so a node lowered outside ``lower_document`` selects no
    #: format-derived type rather than one nothing checks.
    asserted: frozenset[str] = frozenset()
    #: The pointers of THIS document's nodes that a ``$ref`` NAMES -- from elsewhere in
    #: the bundle, or from this very document; see ``bundle.named_nodes``.  Empty by
    #: default, so a document lowered outside ``lower_document`` names no node for a
    #: referrer that is not there -- the same reason ``asserted`` is empty by default.
    named: frozenset[str] = frozenset()
    #: The SUBSCHEMA at each of those pointers, for the ones a LOCAL reference reaches:
    #: ``pointer -> node``.  A local reference resolves against the REFERRING document,
    #: so the node it names is in this file and :func:`local_reference` needs it without a
    #: binder and without a second reading of the document.  Keyed by the pointer
    #: ``bundle.nodes`` yields, which is the same walk ``bundle.named_nodes`` read the
    #: reference off, so there is no second pointer navigator and no second escaping
    #: rule for a ``~0``/``~1`` in a key.  Empty by default: a document lowered outside
    #: ``lower_document`` resolves no local reference rather than inventing a symbol.
    local: Mapping[str, dict] = field(default_factory=dict)

    #: The pointers of this document's nodes an ENCLOSING node already constrains to
    #: ``type: "object"``; see ``bundle.constrained_to_object``.  A fact about the
    #: DOCUMENT, computed once per document rather than re-derived per node, which is
    #: the same arrangement as ``named`` and for the same reason: a lowering reads a
    #: set and no two readings of the enclosing structure can disagree.
    #:
    #: Empty by default, which refuses rather than admits -- a node lowered outside
    #: ``lower_document`` states its own ``type`` or is refused, which is exactly what
    #: :func:`lower_object` did before this set existed.
    object_constrained: frozenset[str] = frozenset()
    imports: set[tuple[str, str]] = field(default_factory=set)  # (module, name)
    blocks: list[str] = field(default_factory=list)
    names: set[str] = field(default_factory=set)
    #: class name -> its :class:`Shape`, for a class declared in THIS module.
    shapes: dict[str, Shape] = field(default_factory=dict)
    #: JSON Pointer -> the symbol declared for the node at it.  Written by
    #: :meth:`declare`, which EVERY declaration passes through, so a fragment
    #: reference reads one map rather than a second record something could forget to
    #: write.  This is how a ``$ref`` carrying a pointer finds the symbol to import.
    #: It is also :func:`local_reference`'s MEMO, which is why that function needs no
    #: record of its own: a node declared because the walk reached it and a node
    #: declared because a local reference asked for it are one entry here.
    declared: dict[str, str] = field(default_factory=dict)
    #: The pointers :func:`local_reference` is in the middle of declaring, innermost last.
    #: A pointer meeting itself here is a local reference CYCLE, which refuses by name
    #: rather than recurring -- the same shape, and the same reason, as ``emit.emit``'s
    #: ``inflight`` list for a cross-document cycle.
    resolving: list[str] = field(default_factory=list)

    #: D5's rung 3: ``alias symbol -> (the document's type word, its constraints)``
    #: for every constrained scalar this module resolved to a name in
    #: ``adcp.types.constraints``.  Recorded on the module the walk met it in, and
    #: the RUN unions them -- the alias module is one module for the whole run, and
    #: a per-document record is the only place the walk can write one without the
    #: decider taking run-level state.  The IMPORT needs nothing from here: a
    #: dotted path on :class:`Type` produces it through the field, like
    #: ``pydantic.AwareDatetime``.
    aliases: dict[str, tuple[str, dict[str, Any]]] = field(default_factory=dict)

    def declare(self, name: str, pointer: str, block: str) -> None:
        if name in self.names:
            raise Refusal(
                "title",
                pointer,
                f"two nodes in this document derive the class name {name!r}",
            )
        if pointer in self.declared:
            # The symmetric failure to the one above, and the same kind of thing: a
            # pointer names ONE node of a document, so two symbols at one pointer
            # means a fragment reference to it would import whichever the walk
            # happened to declare last.  Measured 0 times over the whole population
            # -- the root's pointer is written once, by the row, and every nested
            # declaration sits at its own node -- so this refuses rather than
            # ordering them.
            raise Refusal(
                "$ref",
                pointer,
                f"two nodes are declared at this pointer: {self.declared[pointer]!r} "
                f"and {name!r}, so a reference to it would import whichever came last",
            )
        self.names.add(name)
        self.declared[pointer] = name
        self.blocks.append(block)

    def add(self, name: str, pointer: str, rendered: Rendered) -> None:
        """Declare one rendered block and take its imports.

        The two always happen together -- a block whose imports were not merged
        renders a module that does not import -- so they are one call, and a
        caller cannot do the first and forget the second.
        """
        self.imports |= rendered.imports
        self.declare(name, pointer, rendered.text)


@dataclass(frozen=True)
class Rules:
    """What one node's D6 rules come to, as the four things a lowering needs.

    ONE carrier and one call (:func:`rules_at`), because the four answers are read
    off one reading of the node and a lowering that took three of them would be a
    lowering that could take one and forget the other -- which is exactly what
    happened: the object row read them all, the ``allOf`` row read none, and the
    documents in this bead's population refused at a keyword whose mechanism was
    complete three modules away.

    * ``screen`` is what a keyword check may ADMIT at this node.  It is not
      :data:`RULE_KEYWORDS` flat, and the difference is load-bearing: a
      ``oneOf``/``anyOf`` is a rule only where every branch is ``required``-only
      (``rules.presence_only``, the published step-5/step-7 test).  A combinator of
      SHAPES is a nested union, ``rules.lower`` writes nothing for it, and admitting
      it would emit a class that drops the combinator silently -- a model wider than
      its document.  Measured on the 3.2 bundle: 72 object nodes carry a
      non-presence-only combinator, and 0 of them sit in a document that emits
      today, so the object row's former unconditional admission was latent rather
      than live -- and this step makes more documents emit, which is what would have
      reached it.
    * ``properties`` are the properties the node declares ONLY inside a conditional.
      They still arrive on the wire, so the class needs a field to carry one, and a
      rule naming a key the class has no field for is worse than no rule: under D8's
      ``ignore`` the key is dropped, the rule reads it as absent, and the constructor
      refuses a payload the document admits.
    * ``body`` is the class-body line binding ``_adcp_rules``, with its imports.
      Empty text where the node states no rule this lowering can express, which D4
      makes correct rather than a refusal (``codegen.lower.rules``' module docstring
      is the one place that judgement is stated).
    * ``distinct`` are the property keys whose array this node states is DISTINCT.
      D6 has claimed their ``uniqueItems``, so :func:`fields` strips the keyword off
      the declaration before the array row sees it and renders the fact onto the
      field instead (``Property.distinct``).  It travels on this carrier for the
      reason the other three do: a caller that reads the rule tuple and forgets the
      strip emits a class whose ``uniqueItems`` reaches a row that refuses it by
      name, which loses the document the rule was written for.
    """

    screen: frozenset[str]
    properties: Mapping[str, dict]
    body: Rendered
    distinct: tuple[str, ...]


def rules_at(node: dict, *also: dict) -> Rules:
    """D6's reading of a node, for a lowering that cannot import the rules module.

    Imported on use, because ``codegen.lower.rules`` imports this module for
    :data:`ANNOTATIONS` and :data:`RULE_KEYWORDS` -- the one place the two halves
    meet, and the lowering's direction is the one D13 fixes, so this side is the lazy
    one.  The same lazy import ``lower_object`` already used, now in one place.

    **``also`` is the other nodes whose rules belong to THIS class**, which is what a
    draft-07 ``allOf`` conjunct is: it applies to the same instance, so it is not a
    separate object and its rule is this node's rule, exactly as a conjunct's
    ``properties`` are this node's fields (``codegen.lower.product``).  They are one
    ``Rules`` and not one per node because a class body can bind ``_adcp_rules``
    ONCE -- two lines would make the second silently replace the first -- so the
    sources are concatenated and the tuple is rendered once.

    ``screen`` is ``node``'s alone and deliberately not merged: a keyword screen is
    asked about one node, and each conjunct is screened by its own call at its own
    pointer, which is what keeps a refusal pointing at the node that caused it.
    """
    from codegen.lower import rules

    lowered = [rules.lower(n) for n in (node, *also)]
    screen = RULE_KEYWORDS if rules.presence_only(node) else RULE_KEYWORDS - {"oneOf", "anyOf"}
    properties: dict[str, dict] = {}
    for one in lowered:
        properties.update({k: v for k, v in one.properties.items() if k not in properties})
    sources = [source for one in lowered for source in one.rules]
    distinct: list[str] = []
    for one in lowered:
        distinct += [key for key in one.distinct if key not in distinct]
    return Rules(
        screen=frozenset(screen),
        properties=properties,
        body=Rendered(
            text=rules.block(sources),
            imports=set().union(*(one.imports for one in lowered)),
        ),
        distinct=tuple(distinct),
    )


def _why(key: str) -> str:
    """Why this key stopped the walk, and the two answers are not the same claim.

    A key draft-07 DEFINES is a keyword some D2 row owns, so "a later row does" is
    a schedule and the bead for it exists.  A key draft-07 does not define has no
    row to be scheduled -- it is not a schema keyword, so there is no lowering to
    write -- and answering "a later D2 row does" about one PROMISES AN UNSCHEDULED
    ROW.  Measured on the base tree (``5d92cf2c0``, 406 emitted and 648 refused of
    1,054): 11 of the 648 refusals answered that about a
    non-keyword (``discriminator`` 7, ``notes`` 2, ``enumMetadata`` 1,
    ``last_updated`` 1), and the four this bead names were three distinct names at
    a root with no row anywhere that could ever claim them.

    So the admission decision and the refusal REASON are the one bug read twice:
    :data:`BUNDLE_ANNOTATIONS` names the non-keywords that annotate, and this names
    what a refusal says about the rest.
    """
    if key in DRAFT07:
        return refusal.DEFERRED_TO_A_LATER_ROW
    return (
        "draft-07 defines no such keyword, so no D2 row lowers it and none is "
        "scheduled; a non-keyword that ANNOTATES a node is named in "
        "compiler.BUNDLE_ANNOTATIONS and this is not one of those names"
    )


def check_keywords(
    node: dict,
    pointer: str,
    handled: set[str],
    why: str | None = None,
) -> None:
    for key in sorted(node):
        if key in handled or key in ANNOTATIONS or key in DEFINITION_SECTIONS:
            continue
        if key.startswith("x-"):
            continue
        raise Refusal(key, pointer, why or _why(key))


# --------------------------------------------------------------------------- #
# the field builder and the class declarer
# --------------------------------------------------------------------------- #
def fields(
    props: Mapping[str, Any],
    required: Collection[str],
    pointer: str,
    name: str,
    mod: Module,
    *,
    inherited: Collection[str] = (),
    declared_at: Mapping[str, str] | None = None,
    distinct: Collection[str] = (),
) -> list[Property]:
    """The decided properties for one property map, children declared first.

    Shared with a composing row, which builds ONE property map out of a root's
    own ``properties`` and an inline ``allOf`` conjunct's.  How a property is
    decided is the same question wherever it was declared, and a second copy of
    this loop is how two declarations of one field come to disagree about the
    answer.

    ``inherited`` names the keys a BASE CLASS already declares.  They are not
    decided here -- the field is inherited, and a subclass that restated it would
    shadow the base's type with whatever its own restatement happens to say --
    but they do satisfy ``required``, because an inherited field is present on
    the class.  The row decides what goes in it (the narrowing rule); this
    function only honours it.  ``declared_at`` gives the pointer a key was
    declared at where that is not ``<pointer>/properties/<key>``, which it is not
    for a key that came from a conjunct.

    There was a third keyword argument, ``decided``: a per-property type the CALLER
    had already decided, so that the union row could turn a branch's ``const`` into a
    ``Literal`` without claiming the keyword everywhere.  **It is gone, and so is the
    scoping it existed for.**  D2's ``const`` row is ``codegen.lower.const`` and
    ``decide_type`` reaches it for every node, so a branch's discriminating pin is
    decided exactly the way every other property is -- which leaves one lowering for
    the keyword instead of two that have to agree.

    ``distinct`` is the same "one position, not everywhere" shape that ``decided``
    had, and it survives because its keyword has no such row: it names the keys whose
    array D6's rule lowering has CLAIMED the ``uniqueItems`` of
    (``lower.rules._distinct``).  The keyword is stripped off the declaration here so
    the array row never sees it -- which is what leaves that row's screen refusing an
    array no class holds rather than widening it -- and :attr:`Property.distinct`
    carries the fact onto the field, where ``_field`` renders it.  A key named here
    whose declaration is not an array with ``uniqueItems: true`` is a caller defect,
    so nothing is silently stripped: the strip is read off the declaration and the
    flag off this set, and the two agreeing is asserted by the rules lowering's own
    gate.
    """
    undeclared = [r for r in required if r not in props and r not in inherited]
    if undeclared:
        raise Refusal(
            "required",
            pointer,
            f"required names no property declares: {undeclared} (step 7's rule, not a field)",
        )

    built: list[Property] = []
    spelled: dict[str, str] = {}
    where = declared_at or {}
    for key, sub in props.items():
        at = where.get(key, f"{pointer}/properties/{key}")
        if not isinstance(sub, dict):
            raise Refusal("properties", at, "property is not a schema")
        fname = field_name(key)
        if fname in spelled:
            raise Refusal(
                "properties", at, f"{key!r} and {spelled[fname]!r} both spell the field {fname!r}"
            )
        spelled[fname] = key
        is_distinct = key in distinct
        if is_distinct:
            # D6 owns the keyword at this position, so the walk below must not see it:
            # the array row carries no ``uniqueItems`` and refuses one by name, which
            # is what keeps an array NO class holds refused rather than widened.
            sub = {k: v for k, v in sub.items() if k != "uniqueItems"}
        decided_type = mod.decide(sub, at, name + class_name(key), mod)
        is_required = key in required
        default = MISSING
        if "default" in sub:
            if is_required:
                # No rendering carries it: a pydantic field with a default is not
                # required, so transcribing one here would widen the model's
                # accepted set to admit an instance omitting a key the document
                # demands -- and the schema half of `strict_validate` would hide
                # that in both acceptance directions.  5 of the bundle's 339
                # property defaults sit on a required property; the step whose
                # population reaches one decides between `json_schema_extra` and
                # refusing.
                raise Refusal(
                    "default",
                    at,
                    "a default on a REQUIRED property has no rendering that does not also "
                    "make the property optional",
                )
            default = sub["default"]
        doc = sub.get("description")
        built.append(
            Property(
                name=fname,
                wire=key,
                type=decided_type.type,
                required=is_required,
                default=default,
                description=doc if isinstance(doc, str) and doc else None,
                constraints=decided_type.constraints,
                format=decided_type.format,
                distinct=is_distinct,
            )
        )
    return built


def declare_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    props: Sequence[Property],
    shape: Shape,
    *,
    bases: tuple[str, ...] = (),
    body_lines: tuple[str, ...] = (),
    imports: set[tuple[str, str]] | None = None,
    rule_nodes: Sequence[dict] = (),
) -> str:
    """Assemble one class out of decided properties, and record what it declares.

    The other half shared with a composing row: D8's ``extra``, the description,
    the ``__adcp_schema__`` the compiler writes, and the :class:`Shape` a later
    subclass reads.  ``bases`` is empty for a node that composes nothing, and
    then the base is ``AdCPBaseModel``; a composing row passes the symbols its
    ``$ref`` conjuncts bound (D7 -- a base is DERIVED from what the document
    composes, never classified by hand), and ``AdCPBaseModel`` arrives through
    them.

    **D6's rule tuple is written HERE**, for the node being declared, and that is what
    makes "a rule attaches to the nearest class" true of every row rather than of the
    one that remembered.  This is the one funnel a class WITH FIELDS passes through --
    the object row, the ``allOf`` row and a union BRANCH all arrive here -- so the
    ``allOf`` row gets its root's ``not``/``dependencies``/``minProperties`` by passing
    through rather than by repeating the object row's call.  A rule renders nothing in a
    model's JSON schema, so the symmetric comparison neither gains nor loses a fact by
    this; the only instrument that observes one is a direct ``model_validate``, which
    is what ``src/adcp/types/_runtime.py`` records.

    ``rule_nodes`` are the OTHER nodes whose rules are this class's -- an ``allOf``
    conjunct, which draft-07 applies to the same instance.  Empty for every row but
    the composing one.
    """
    stated = rules_at(node, *rule_nodes)
    body_lines = (*body_lines, *(line for line in (stated.body.text,) if line))
    imports = (imports or set()) | stated.body.imports
    # D8's typed row: a property the class does not DECLARE is validated against
    # the document's own value schema, through pydantic's ``__pydantic_extra__``.
    # The TYPE is the same ``dict[K, V]`` a mapping node lowers to, decided by the
    # same row -- the node is handed to ``mod.decide`` as the mapping it is, with
    # whatever the node says about its KEYS carried across (D5 types the key too),
    # so an extras store and a mapping cannot come to read ``additionalProperties``
    # two different ways.  ``mod.decide`` rather than an import of the container
    # row: D13's import rule runs the other way, and the default decider refuses,
    # so a node lowered outside ``lower_document`` is not silently widened.
    ap = node.get("additionalProperties")
    extra_type = None
    if isinstance(ap, dict) and ap:
        extra_type = mod.decide(
            {
                "type": "object",
                "additionalProperties": ap,
                **{k: node[k] for k in ("propertyNames",) if k in node},
            },
            pointer,
            name,
            mod,
        ).type
    description = node.get("description")
    rendered = render(
        Class(
            name=name,
            ref=schema_ref(mod.document, pointer),
            properties=tuple(props),
            description=description if isinstance(description, str) and description else None,
            # D8; absent leaves the base's default in place.  A TYPED
            # ``additionalProperties`` is ``allow`` with the type beside it: the
            # properties are part of the document, so they are retained, and
            # ``__pydantic_extra__`` is what validates them.
            extra="allow" if extra_type is not None else {False: "forbid", True: "allow"}.get(ap),
            extra_type=extra_type,
            bases=bases,
            body_lines=body_lines,
        )
    )
    mod.shapes[name] = shape
    if imports:
        mod.imports |= imports
    mod.add(name, pointer, rendered)
    return name


def lower_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    *,
    bases: tuple[str, ...] = (),
    body_lines: tuple[str, ...] = (),
) -> str:
    """Append the class for an object node, children first, and return its name.

    The two keyword arguments are what a COMPOSITION needs and a leaf object does
    not, and each defaults to the leaf's answer, so steps 1 and 2's call sites are
    unchanged and so is every module they emit.  Both are :class:`Class`'s own.  A
    third, ``decided``, is gone with the union row's private ``const`` lowering --
    :func:`fields` says why.
    """
    # D6's six families are handled HERE and not refused: a rule attaches to the
    # nearest class, so a node with fields is the only node that can carry one.  The
    # reading is :func:`rules_at`'s, which is also where the TUPLE is written
    # (:func:`declare_object`) -- so this row and the ``allOf`` row and a union branch
    # all admit the same keywords and all write the same rule.
    stated = rules_at(node)
    check_keywords(
        node,
        pointer,
        {
            "type",
            "properties",
            "required",
            "additionalProperties",
            "propertyNames",
            *stated.screen,
        },
    )
    declared = node.get("type")
    if declared != "object" and not (declared is None and pointer in mod.object_constrained):
        # A node carrying ``properties`` and no ``type`` ADMITS A NON-OBJECT: JSON
        # Schema applies ``properties`` only to objects and asserts nothing about
        # anything else, so ``{"properties": {"a": {"type": "string"}}, "required":
        # ["a"]}`` admits ``"hello"`` and ``42`` -- measured with ``jsonschema`` on
        # exactly that node.  No class can, so the model is NARROWER than its
        # document, which is the defect P3 removes.
        #
        # This condition read ``in (None, "object")`` and 0 of the 43 documents
        # emitted before step 5 exercise the ``None`` arm -- every one of them
        # declares ``type: object`` -- so the tolerance was latent rather than
        # relied on.  Step 5's union BRANCHES are the first population to reach it,
        # and they reach it in the worst way: the accepts check reports
        # ``model_type`` on a valid instance, which is the model refusing a payload
        # the document admits.
        #
        # **``mod.object_constrained`` is what keeps it from reading the node in
        # ISOLATION, which was the other half of the defect.**  draft-07 applies a
        # root's assertions and its combinator branch's to the SAME instance, so
        # ``{"type": "object", "oneOf": [{"properties": ...}]}`` admits only objects
        # and the branch at ``/oneOf/0`` restates nothing: there is no non-object for
        # the class to be narrower than.  This refusal fired for 11 documents whose
        # own root declares ``type: object`` three lines above the branch, and for 33
        # whose node is a PROPERTY's own schema -- where nothing constrains the value
        # and the refusal is right.  ``bundle.constrained_to_object`` is the one
        # reading of which is which.
        #
        # A node declaring a type that is NOT ``object`` is still refused whatever
        # encloses it: a conjunction of ``object`` and ``string`` admits nothing, and
        # a class for it would accept what the document refuses.
        raise Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.get('type', '<absent>')!r} and nothing enclosing it constrains the "
            "instance to an object, so the document admits a non-object that no class can",
        )
    props = node["properties"]
    if not isinstance(props, dict) or not props:
        raise Refusal("properties", pointer, "an object node with no property declared")
    # A property the node declares only under a conditional still arrives on the
    # wire, so the class needs a field to carry it.  Collected by the rules lowering,
    # which is what reads the conditional, and merged in BEFORE the walk over
    # ``props`` so such a property is typed from its own declaration rather than left
    # off the model -- a required name the model does not declare is a class narrower
    # than its document on both acceptance paths.
    props = {**props, **{k: v for k, v in stated.properties.items() if k not in props}}
    required = node.get("required", [])
    if not isinstance(required, list) or not all(isinstance(r, str) for r in required):
        raise Refusal("required", pointer, f"required is {required!r}, not a list of names")
    built = fields(props, required, pointer, name, mod, distinct=stated.distinct)
    return declare_object(
        node,
        name,
        pointer,
        mod,
        built,
        Shape(props, frozenset(required)),
        bases=bases,
        body_lines=body_lines,
    )


def bind_without_a_model(mod: Module, symbol: str, rendered: Rendered) -> str:
    """The module-level half of a root that is not an ``AdCPBaseModel``.

    D2 gives two root kinds no class to hang ``strict_validate`` on: a scalar root
    is an ``Annotated`` alias, and an enumeration cannot carry a class-body line at
    all because ``Enum.jinja2`` has no ``class_body_lines`` slot and D9 forbids
    writing one in afterwards.  Both therefore bind the SAME two halves at module
    scope -- the reference, and ``strict_alias`` over it -- so a class, an alias and
    an enumeration cannot come to answer differently about what their own document
    accepts.  ``strict_alias`` reaches the document through ``schema_at`` and
    refuses through ``_refuse``, which is exactly what
    ``AdCPBaseModel.strict_validate`` does.

    One function and not two, because the rows differ only in the rendered text
    BETWEEN the statements.  ``tests/test_emit.py`` reads the pairing off the module
    for both.
    """
    ref = schema_ref(mod.document, "")
    mod.imports.add((BASE_MODULE, "SchemaRef"))
    mod.imports.add((BASE_MODULE, "strict_alias"))
    mod.add(
        symbol,
        "",
        Rendered(
            text=f"__adcp_schema__ = {ref!r}\n\n"
            f"{rendered.text}\n\n\n"
            f'strict_validate = strict_alias(__adcp_schema__, "{symbol}", {symbol})',
            imports=rendered.imports,
        ),
    )
    return symbol


def _alias_for(symbol: str, node: dict, decided: Decided) -> Rendered:
    """:func:`render_alias` over one node's own decision.

    Shared by the TWO rows that declare an alias -- a root (:func:`declare_alias`) and
    a node another document names (:func:`name_the_node`) -- because "the annotation
    for this node, under this name" is the same question in both and a second copy of
    it is how the two come to carry a node's ``format`` or its ``description``
    differently.  They differ only in what wraps the statement, which is each row's
    own and stays there.
    """
    description = node.get("description")
    return render_alias(
        symbol,
        decided.type,
        decided.constraints,
        description=description if isinstance(description, str) and description else None,
        format=decided.format,
    )


def name_the_node(mod: Module, symbol: str, pointer: str, node: dict, decided: Decided) -> Decided:
    """Give a node a SYMBOL in its own module, because a ``$ref`` elsewhere names it.

    A fragment reference resolves to an import of a symbol the target module
    declares, never to a copy (section 2's rule).  A node D2 makes a CLASS already
    has one -- the walk declared it and ``decided.type.local`` says so -- and this is
    the other case: an array, a scalar or a mapping is an annotation with no name, so
    the target module has nothing to export and the reference has nothing to import.

    **The node's type BECOMES the symbol**, which is why this returns a ``Decided``
    rather than only declaring: the alias carries the constraints and the referring
    property then references it, so the node's facts have ONE spelling in the module.
    Declaring the alias and leaving the parent's field to restate the same
    ``minLength`` inline would be the copy P2 removes, two spellings deep in one file.

    Not :func:`declare_alias`, which is a ROOT's whole module -- the reference, the
    alias and the bound ``strict_validate``, all at module scope, where there is room
    for exactly one of each.  A named node is INSIDE a document that already has a
    root, so it takes the alias statement alone.  It therefore carries no
    ``__adcp_schema__`` of its own, and that is the existing arrangement rather than
    a gap: every nested node that is not a class is ungraded on its own today, and
    this one is graded twice over anyway -- inside its own document's pair, which
    names the whole document, and inside its referrer's, whose resolved schema inlines
    this very node at the pointer the reference carries.

    The name is the walk's own ``name_hint``, which is D3's nested rule (parent +
    ``pascal_case(property)``) already computed at the call site.  D3 says a name is an
    input to a lowering and is never computed inside one, so none is computed here.
    """
    mod.add(symbol, pointer, _alias_for(symbol, node, decided))
    return Decided(Type(symbol, local=True))


def local_reference(mod: Module, pointer: str, at: str) -> Decided:
    """What a LOCAL ``$ref`` decides to: the node of THIS document that it names.

    :func:`name_the_node`'s sibling, and the division is which document the reference
    resolves against.  An ABSOLUTE fragment reference names a node of ANOTHER document,
    so the referring module imports a symbol that module declared and
    ``emit.emit``'s binder does the work.  A local one (``#/definitions/x`` -- an empty
    document half, which ``bundle.split_ref`` is what hands back) names a node of the
    document being written, so there is no module to import from and no binder to ask:
    the symbol is one THIS module declares, and if it has not declared it yet, this is
    what makes it.

    **Declared when a reference asks, not ahead of time**, and three things follow that
    an eager pass over the section would have to solve one at a time:

    * a FORWARD reference costs nothing.  20 of the bundle's local references name an
      entry the document lists after the one referring to it, in 4 documents; declaring
      on demand puts every symbol in the module before its user by construction, where
      an eager pass in document order would need a topological sort over the section.
    * an entry nothing references is NOT declared, which is the decision rather than an
      omission.  ``definitions`` and ``$defs`` assert nothing about an instance, so an
      entry no reference reaches cannot change what the document accepts or refuses --
      declaring it would emit a class no field names, nothing imports and ``__all__``
      does not export, whose only reachable effect is that a keyword inside a DEAD
      section could refuse the whole document.  Measured: 11 of the 157 entries in the
      40 documents this step unblocks, all 11 in ``a2ui/si-catalog.json``, whose 24
      ``$ref``\\ s all sit inside the dead section.
    * a CYCLE refuses by name instead of recurring, through ``mod.resolving``.  0
      documents are in that position today, which is why this is the rule rather than a
      forward-declaration scheme: two entries naming each other is a recursive type,
      and nothing here has a spelling for one.

    **The NODE ITSELF decides what it becomes, and the decision is returned rather than
    looked back up.**  ``mod.decide`` is the one per-node walk, so an object entry is a
    class, an enumeration is an enumeration, and a scalar or an array is an annotation
    that :func:`name_the_node` gives this very symbol to -- the pointer is in
    ``mod.named``, which is what put it in ``mod.local`` in the first place.  Each one
    therefore carries ITS OWN pointer: a class through :func:`declare_object`'s
    ``schema_ref(mod.document, pointer)``, and nothing is written against the referring
    document's.

    Returning the decision is what makes the ONE case with no declaration correct
    instead of a ``KeyError``: an entry that is ITSELF a ``$ref`` decides to the symbol
    the module IMPORTED for its target, which nothing declared here.  That is the right
    answer within one module -- the import is already in the module and there is no
    export to re-export -- and it is the opposite of the cross-module case, where
    section 2's rule demands the symbol be one the TARGET declares and ``emit.emit``'s
    binder refuses a pointer at such a node.  It is also why ``mod.declared`` is a
    sufficient memo rather than a required one: such an entry is simply re-decided, to
    the same imported symbol, and ``mod.imports`` is a set.  Measured, so the arm is
    known live rather than defensive: 4 of the bundle's 405 local reference sites name
    such an entry, in 2 documents (``brand.json#/definitions/logo_slot`` and
    ``core/registry-event.json#/$defs/badgeRole``, each named twice).

    The NAME is D3's nested rule with the document as the parent: the root's symbol plus
    ``class_name`` of the entry's own key, which is the pointer's last segment
    unescaped.  **No identifier check here, and that is a proof rather than an
    omission**: ``class_name`` returns alphanumerics only, ``emit.lower_document``
    refuses a title that derives no identifier before any row runs, so ``mod.root``
    always begins with a letter and the concatenation is always an identifier.  What
    CAN go wrong is two keys deriving one name (``a_b`` and ``a.b``), and
    :meth:`Module.declare` already fails the build naming both -- including the key
    whose characters are all non-alphanumeric, which derives the root's own name.
    Measured spellable for all 163 of the bundle's entry keys.
    """
    if pointer in mod.declared:
        return Decided(Type(mod.declared[pointer], local=True))
    if pointer in mod.resolving:
        raise Refusal(
            "$ref",
            at,
            f"a local reference cycle: #{' -> #'.join([*mod.resolving, pointer])}",
        )
    node = mod.local.get(pointer)
    if node is None:
        raise Refusal("$ref", at, f"#{pointer} names no node of this document")
    key = pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
    symbol = mod.root + class_name(key)
    mod.resolving.append(pointer)
    try:
        return mod.decide(node, pointer, symbol, mod)
    finally:
        mod.resolving.pop()


def declare_alias(mod: Module, symbol: str, doc: dict, decided: Decided) -> str:
    """Declare the module for a root D2 makes an ALIAS rather than a class.

    A scalar root takes this shape, and so does every other root with no field to
    hang itself on: a class would be a second name for the same node (P2) and
    would put an object on the wire where the document carries a string or a map.
    One function for all of them because the module shape is identical -- the
    reference, the alias, and the bound ``strict_validate`` -- and two copies of it
    would be two places for the ``strict_validate`` line to drift.

    The ANNOTATION is still the compiler's: the same field rendering a class
    property gets, read off the field instead of out of a class body, so a
    constraint on an alias and a constraint on a property cannot come to be spelled
    two ways.  What is ours is the two module-level STATEMENTS, and §1 says why: no
    compiler template has a slot for a line beside an alias.

    KNOWN CEILING: an alias has no ``ConfigDict``, so it cannot carry the per-class
    ``regex_engine`` a look-around pattern needs, and ``strict_alias`` builds its
    ``TypeAdapter`` at import.  A root carrying look-around would therefore fail to
    IMPORT once the base stops forcing ``python-re``.  Measured over steps 1 and 2's
    population: 5 scalar roots, 2 carrying a ``pattern`` (both ``^[a-z0-9_]+$``,
    which the default engine compiles) and 0 carrying look-around, so no document
    there reaches it.  The failure is an ImportError at the gate rather than a
    silent widening, so the upgrade path is for the step whose population reaches
    one: either refuse such a document by name, or wrap the alias in a
    ``RootModel`` that has a config slot.
    """
    return bind_without_a_model(mod, symbol, _alias_for(symbol, doc, decided))
