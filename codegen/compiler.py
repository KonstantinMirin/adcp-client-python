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
from pydantic import BaseModel as PydanticBaseModel

from adcp.types._base import SchemaRef
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

    def data_type(self) -> Any:
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
    if prop.format:
        extras["json_schema_extra"] = {"format": prop.format}
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
#: Keywords that annotate a node without constraining an instance.  ``default``
#: and ``description`` are carried by the compiler (they are rendering, and
#: rendering is what the compiler is for); the rest have nowhere to go and are
#: never a reason to refuse.
ANNOTATIONS = frozenset(
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
    #: ``(uri, pointer) -> Target``; see ``emit.emit``.
    bind: Callable[[str, str], Target] = _no_binder
    #: ``(node, pointer, name_hint, mod) -> Decided``; see ``emit.decide_type``.
    decide: Callable[[dict, str, str, "Module"], Decided] = _no_decider
    #: The formats this document's own draft asserts; see ``emit.asserted_formats``.
    #: Empty by default, so a node lowered outside ``lower_document`` selects no
    #: format-derived type rather than one nothing checks.
    asserted: frozenset[str] = frozenset()
    imports: set[tuple[str, str]] = field(default_factory=set)  # (module, name)
    blocks: list[str] = field(default_factory=list)
    names: set[str] = field(default_factory=set)
    #: class name -> its :class:`Shape`, for a class declared in THIS module.
    shapes: dict[str, Shape] = field(default_factory=dict)

    def declare(self, name: str, pointer: str, block: str) -> None:
        if name in self.names:
            raise Refusal(
                "title",
                pointer,
                f"two nodes in this document derive the class name {name!r}",
            )
        self.names.add(name)
        self.blocks.append(block)

    def add(self, name: str, pointer: str, rendered: Rendered) -> None:
        """Declare one rendered block and take its imports.

        The two always happen together -- a block whose imports were not merged
        renders a module that does not import -- so they are one call, and a
        caller cannot do the first and forget the second.
        """
        self.imports |= rendered.imports
        self.declare(name, pointer, rendered.text)


def check_keywords(
    node: dict,
    pointer: str,
    handled: set[str],
    why: str = "this step lowers no such keyword (a later D2 row does)",
) -> None:
    for key in sorted(node):
        if key in handled or key in ANNOTATIONS or key.startswith("x-"):
            continue
        raise Refusal(key, pointer, why)


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
    decided: Mapping[str, Decided] | None = None,
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

    ``decided`` is a per-property type the CALLER has already decided, by property
    key.  It exists so a lowering that owns a keyword for ONE position can apply it
    there without claiming the keyword everywhere: the union row turns a branch's
    ``const`` into a ``Literal``, and putting that into ``decide_type`` instead
    would emit a ``const`` row for steps 1 and 2's own populations too and collide
    with whichever step claims D2's ``const`` row in full.
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
        decided_type = (decided or {}).get(key) or mod.decide(sub, at, name + class_name(key), mod)
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
) -> str:
    """Assemble one class out of decided properties, and record what it declares.

    The other half shared with a composing row: D8's ``extra``, the description,
    the ``__adcp_schema__`` the compiler writes, and the :class:`Shape` a later
    subclass reads.  ``bases`` is empty for a node that composes nothing, and
    then the base is ``AdCPBaseModel``; a composing row passes the symbols its
    ``$ref`` conjuncts bound (D7 -- a base is DERIVED from what the document
    composes, never classified by hand), and ``AdCPBaseModel`` arrives through
    them.
    """
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
    mod.add(name, pointer, rendered)
    return name


def lower_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    *,
    bases: tuple[str, ...] = (),
    decided: Mapping[str, Decided] | None = None,
    body_lines: tuple[str, ...] = (),
) -> str:
    """Append the class for an object node, children first, and return its name.

    The three keyword arguments are what a COMPOSITION needs and a leaf object does
    not, and each defaults to the leaf's answer, so steps 1 and 2's call sites are
    unchanged and so is every module they emit.  :func:`fields` documents
    ``decided``; ``bases`` and ``body_lines`` are :class:`Class`'s own.
    """
    check_keywords(
        node, pointer, {"type", "properties", "required", "additionalProperties", "propertyNames"}
    )
    if node.get("type") != "object":
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
        raise Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.get('type', '<absent>')!r}, so the document admits a non-object that "
            "no class can",
        )
    props = node["properties"]
    if not isinstance(props, dict) or not props:
        raise Refusal("properties", pointer, "an object node with no property declared")
    required = node.get("required", [])
    if not isinstance(required, list) or not all(isinstance(r, str) for r in required):
        raise Refusal("required", pointer, f"required is {required!r}, not a list of names")
    built = fields(props, required, pointer, name, mod, decided=decided)
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
    description = doc.get("description")
    return bind_without_a_model(
        mod,
        symbol,
        render_alias(
            symbol,
            decided.type,
            decided.constraints,
            description=description if isinstance(description, str) and description else None,
            format=decided.format,
        ),
    )
