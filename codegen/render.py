"""The renderer: a declaration in, Python out -- and the ONE module that knows pydantic.

``docs/plan/architecture.md`` §8: this is the only module under ``codegen/`` outside
``verify/`` that imports ``pydantic`` or ``datamodel_code_generator``.  It takes
``codegen.ir``'s declarations and returns text; it takes a module and returns the
module's text; it takes the run's union of constraint shapes and returns
``adcp/types/constraints.py``.  ``tests/test_import_rule.py`` is the boundary's test, and
it is one-way: a ``TypeRef`` naming ``pydantic.AwareDatetime`` is a Python symbol the
semantics document's ``format`` row names, and naming a symbol is not a Pydantic idiom;
constructing a ``Field``, a ``ConfigDict``, an ``Annotated`` or a ``DataType`` is, and
only this module does it.

``docs/plan/rebuild-plan.md`` §1 splits the pipeline at a DECISION rather than at a
translation.  Our walk reads the JSON Schema and decides what each node becomes -- a
class, an annotation, an enumeration or a rule -- what it is called, which fields it has
and what constrains them.  This module takes those declarations and nothing else, and
hands them to ``datamodel-code-generator``'s pydantic-v2 MODEL layer, which writes the
Python.

**The code generator's parser never runs.**  The parser is the half that decides names
and structure from a schema, and that is our half -- it is where every judgement about
AdCP's bundle lives, and no library has that knowledge.  What the generator has that we
would otherwise rewrite is the rendering: annotated constraints, defaults, descriptions,
aliases, ``ConfigDict``, the ``| None`` branch of an optional, and the import set each of
those needs.  A hand-rolled text emitter dropped three of three schema defaults and all
142 property descriptions in the population it covered, not because anyone decided to,
but because carrying them is rendering work and rendering work was being rewritten.

**Two gates, both silent, both measured.  Neither is a reason to avoid the generator;
they are how it is driven.**

1. **Constraints are spelled in JSON Schema, not pydantic.**  ``Constraints`` declares
   every field under its JSON-Schema alias with no ``populate_by_name``, so
   ``Constraints(ge=1, le=100)`` sets NOTHING -- empty ``model_fields_set``, empty dump,
   and a rendered class with no bound on the field.  ``Constraints(minimum=1,
   maximum=100)`` renders ``Field(ge=1, le=100)``.  ``codegen.ir.FACTS`` is therefore
   the document's own vocabulary, passed through unchanged -- one declaration, read by
   the walk and by this module -- and ``TypeRef.facts`` carries the keywords in the
   document's spelling all the way here (§7).  :data:`KEY_COUNT` is the one pair pydantic
   spells differently.
2. **``extras`` cannot carry a constraint.**  The generator's ``_EXCLUDE_FIELD_KEYS``
   strips ``gt ge lt le multiple_of min_length max_length pattern`` out of ``extras`` on
   the way to ``Field(...)``.  A constraint goes through ``constraints=`` and nowhere
   else; ``extras`` carries the description.

A third gate, found here: **``class_body_lines`` is reserved.**  Passing it in
``extra_template_data`` raises ``Error: class_body_lines is reserved for
generator-owned built-in template data``, so a project-produced line reaches the class
body through ``_append_internal_template_data``, which is the generator's own channel for
a line a built-in template renders as code.  The alternative is a vendored copy of
``BaseModel.jinja2``, which is a template that drifts from the pinned generator on every
upgrade for one line of output.  A release that renames the method fails loudly: a class
with no ``__adcp_schema__`` has no schema, so every grade of it fails rather than quietly
passing.

**Where a rule's constructor expression comes from, and the one place this module
deviates from §7's letter.**  §7 says the renderer writes each rule's ``repr``, "which
for a frozen dataclass is a constructor expression".  §14 step 4 marks this row *Bytes*:
the emitted tree does not change.  The two cannot both hold, because the text the walk
formatted before this row is POSITIONAL (``UniqueItems('tags')``,
``RequiredGroups((('rate',), ('amount',)), 'oneOf')``) and ``dataclasses``' ``repr`` is
keyword-form (``UniqueItems(key='tags')``).  Measured over this tree: of its 444 rule
lines, ``repr`` changes the text of 432, across 169 modules -- and the *Bytes* check, the
only instrument that tells a relocation from a decision, would be blind over that
population for exactly the row that moves the rules.  So the constructor expression is composed here
(:func:`_rule`), from the rule's OWN dataclass fields in their OWN order, which keeps
§7's reason intact: a rule is declared once, in ``adcp.types._runtime``, and adding a
field to a kind renames nothing here.  The deviation is the SPELLING of the call and is
reported on the row rather than absorbed.
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
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

from adcp.types._base import APPROXIMATIONS, Approximation, SchemaRef
from adcp.types._runtime import Distinct, Match, Rule, UniqueItems
from codegen import constraints as constraint_names
from codegen import ir
from codegen.ir import MISSING

#: The runtime base §8 of the architecture document gives a root model, named here and
#: imported by no emitted module until a handler declares one (§14 step 9).  A NAME and
#: not an import of the class, for the reason every other emitted-module symbol is a name:
#: the renderer writes text, and a symbol it names is not a Pydantic idiom (§8).
ROOT_MODEL = "AdCPRootModel"

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

#: **The one keyword pair whose pydantic spelling the document does not share**, so it
#: is translated here rather than passed through.  A mapping's key COUNT is
#: ``min``/``maxProperties`` in the document and ``min_length``/``max_length`` in
#: pydantic, and the generator's ``Constraints`` has no field for the document's spelling
#: at all: ``Constraints(minProperties=1)`` constructs and sets NOTHING, which is the
#: silent drop gate 1 exists to prevent.
#:
#: Measured on pydantic 2.13.5, which is why it is a translation and not a refusal:
#: ``Annotated[dict[str, int], Field(min_length=1, max_length=4)]`` renders
#: ``{"type": "object", "minProperties": 1, "maxProperties": 4}`` -- the document's own
#: spelling back again, so the symmetric comparison gains and drops nothing -- and
#: enforces the bound (``{}`` refused, one key accepted, five refused).
#:
#: It is HERE for the reason gate 1 is: a row states the document's keyword, and
#: translating one into pydantic's vocabulary is this module's half of the seam.  The
#: array row relies on the same seam without needing an entry, because the generator's
#: ``Constraints`` happens to alias ``minItems`` itself.  A node carries at most one of
#: the two pairs -- a string's ``minLength`` and an object's ``minProperties`` are
#: keywords of different types, and ``containers.ARM`` is what keeps a multi-type node's
#: arms apart -- so the translation cannot collide with a spelling already present.
KEY_COUNT = {"minProperties": "minLength", "maxProperties": "maxLength"}

_TYPES = DataTypeManager(
    python_version=TARGET,
    use_union_operator=True,
    use_standard_collections=True,
)


@dataclass
class Rendered:
    text: str
    #: ``(module, name)`` pairs the rendered text needs, which the module writer
    #: merges with its own and sorts.
    imports: set[tuple[str, str]] = field(default_factory=set)


# --------------------------------------------------------------------------- #
# a decided type as the model layer's own carrier
# --------------------------------------------------------------------------- #
def _data_type(decided: ir.TypeRef) -> Any:
    """One :class:`codegen.ir.TypeRef` as the model layer's ``DataType``."""
    if decided.validators:
        return _bound_to_the_type(decided)
    if decided.literals:
        return _TYPES.data_type(literals=list(decided.literals))
    if decided.container == "list":
        return _TYPES.data_type(is_list=True, data_types=[_data_type(t) for t in decided.of])
    if decided.container == "dict":
        return _TYPES.data_type(
            is_dict=True,
            data_types=[_data_type(t) for t in decided.of],
            dict_key=_data_type(decided.key) if decided.key is not None else None,
        )
    if decided.container == "union":
        return _TYPES.data_type(data_types=[_data_type(t) for t in decided.of])
    if decided.container == "alias":
        outer = _TYPES.get_data_type_from_full_path(decided.path, is_custom_type=False)
        inner = [_data_type(t) for t in decided.of]
        args = ", ".join(t.type_hint for t in inner)
        # **The ARGUMENTS are passed as well as spelled, so their own imports reach the
        # module.**  A generic alias's subscript is written as TEXT here, because the
        # model layer has no carrier for "this alias applied to these types"; written as
        # text alone, every argument's ``import_`` is dropped -- the model's import set
        # is collected off ``data_types`` -- and the module names a symbol it does not
        # import.  Latent until §14 step 9: an argument that is itself an alias needs a
        # second name from ``adcp.types.constraints``, which only happens where a
        # container alias's element is a constrained type, and
        # ``brand/get-brand-identity-response.json``'s ``tagline`` --
        # ``NonEmptyList[DictMinProperties1MaxProperties1[str, StrMinLen1]]`` -- is the
        # first node in the emitted population to be one.  ``type`` is still what the
        # hint is read off, so the text is unchanged wherever the arguments needed no
        # import, which is every node the tree carried before (byte-compared).
        return _TYPES.data_type(
            type=f"{outer.type_hint}[{args}]", import_=outer.import_, data_types=inner
        )
    if decided.path == "None":
        return _TYPES.data_type(type="None")
    if decided.local:
        return _TYPES.data_type(
            reference=Reference(
                path=f"#/{decided.path}", original_name=decided.path, name=decided.path
            )
        )
    return _TYPES.get_data_type_from_full_path(decided.path, is_custom_type=False)


#: **The fact a value rule STATES in the model's rendered schema**, keyed by the kind,
#: and the reason it is DERIVED from the rule rather than carried beside it: a rule and
#: the ``json_schema_extra`` that makes it gradable are ONE claim, so a tree in which the
#: two disagree should not be spellable.  ``render.root_model`` already derives the same
#: fact from a root array's rule tuple, for the same reason and in the same words.
#:
#: ``Distinct`` is the only entry because it is the only one of the three whose keyword a
#: faithful model states as a FACT: ``uniqueItems`` is ``rendered=True`` in
#: ``codegen.keywords`` (pydantic v2 has no annotation for it, so it rides the
#: ``json_schema_extra`` channel), while ``contains`` and ``not`` are ``rendered=False``
#: -- the model enforces each as a rule and renders nothing for it, which is §8's own
#: answer for a keyword a rule carries.  So this map is the table's ``rendered`` column
#: read at the three kinds, not a second decision about them.
VALUE_RULE_FACTS: dict[str, Mapping[str, Any]] = {Distinct.__name__: {"uniqueItems": True}}


def _bound_to_the_type(decided: ir.TypeRef) -> Any:
    """§2's rule on a VALUE: the node's own type wrapped in the rules bound to it.

    "Where no class sits above the value -- a root array, a mapping value, a
    ``definitions`` entry, a union branch -- the rule hangs off the value's own
    annotated type as an after-validator (``AtLeastOne``, ``NotValue``, ``Distinct``)."
    ``Annotated[list[X], Field(json_schema_extra=…), AfterValidator(Distinct())]`` is the
    whole of that, and it is composed HERE for the reason the generic-alias arm above is:
    the model layer's ``DataType`` has no carrier for "this type with this metadata", so
    the subscript is TEXT in the one module §8 lets hold pydantic's spellings, and the
    walk composes the rule as a VALUE.

    **The parts are PASSED as well as spelled**, which is the alias arm's measured rule:
    a model's import set is collected off ``data_types``, so a part named only in the
    text reaches the module as a ``NameError``.  ``Annotated``, ``AfterValidator``,
    ``Field`` and each rule kind are therefore resolved through the model layer and their
    own ``type_hint`` is what the text uses -- so there is no second spelling of any of
    them here.

    The inner type is the same :class:`codegen.ir.TypeRef` with the rules taken off, so
    every other arm of :func:`_data_type` decides it exactly as it would with no rule
    bound: a rule on a value changes what the annotation ENFORCES and not what it IS.
    """
    inner = _data_type(dataclasses.replace(decided, validators=()))
    annotated = _TYPES.get_data_type_from_full_path("typing.Annotated", is_custom_type=False)
    after = _TYPES.get_data_type_from_full_path("pydantic.AfterValidator", is_custom_type=False)
    carried = [inner, annotated, after]
    parts = [inner.type_hint]
    stated = {
        keyword: value
        for rule in decided.validators
        for keyword, value in VALUE_RULE_FACTS.get(type(rule).__name__, {}).items()
    }
    if stated:
        marker = _TYPES.get_data_type_from_full_path("pydantic.Field", is_custom_type=False)
        carried.append(marker)
        parts.append(f"{marker.type_hint}(json_schema_extra={stated!r})")
    for rule in decided.validators:
        carried += [
            _TYPES.get_data_type_from_full_path(f"{ir.RUNTIME_MODULE}.{name}", is_custom_type=False)
            for name in sorted(_named_by(rule))
        ]
        parts.append(f"{after.type_hint}({_rule(rule)})")
    return _TYPES.data_type(
        type=f"{annotated.type_hint}[{', '.join(parts)}]", data_types=carried
    )


#: **What the MODEL LAYER carries, derived and never listed by hand**: every attribute
#: a pydantic ``BaseModel`` already has, so a property key spelling one of them is
#: carried under an alias instead of shadowing it (``names.field_name``).
#:
#: It is HERE because §8 draws the boundary here: ``codegen/render.py`` is the only
#: module under ``codegen/`` outside ``verify/`` that may import ``pydantic``, and the
#: reading used to sit in ``compiler.field_name`` as the one model-layer import left
#: outside it -- a shrink-only exception in ``tests/test_import_rule.py``'s set.  §4's
#: name rules moved to ``codegen/lower/names.py`` in §14 step 7, and ``lower/`` is a
#: package §8 bans ``pydantic`` from OUTRIGHT, so the reading could not move with them:
#: it moves the other way, into the one module that already knows the model layer, and
#: the run hands the SET to the naming pass as data.  The exception shrinks to nothing.
#:
#: An emitted class inherits ``AdCPBaseModel`` rather than ``BaseModel``, and the two
#: differ by the runtime's own additions (``strict_validate``, ``__adcp_schema__``,
#: ``_adcp_rules``).  ``BaseModel`` is what is read, because that is the surface the
#: field builder has always been checked against and because the runtime's additions are
#: this project's own names rather than the model layer's: a key colliding with one of
#: them is a fact about ``src/adcp/types/_base.py`` and belongs to the row that owns it.
#: Measured over every property key of the 1,054 portable documents: 0 keys spell an
#: ``AdCPBaseModel`` attribute that is not a ``BaseModel`` attribute, so the two readings
#: name the same fields today and the narrower one is the one with a reason.
RESERVED = frozenset(dir(PydanticBaseModel))


def _field(decided: ir.Field) -> DataModelField:
    extras: dict[str, Any] = {}
    if decided.description:
        extras["description"] = decided.description
    # One ``json_schema_extra`` dict, two facts that can both be true of one field:
    # a ``format`` no type was selected for, and D6's ``uniqueItems``.  Assigning
    # rather than merging dropped whichever came second.
    extra_schema = {
        **({"format": decided.type.format} if decided.type.format else {}),
        **({"uniqueItems": True} if decided.distinct else {}),
    }
    if extra_schema:
        extras["json_schema_extra"] = extra_schema
    constraints = {
        KEY_COUNT.get(k, k): v
        for k, v in decided.type.facts.items()
        if k in ir.FACTS or k in KEY_COUNT
    }
    kwargs: dict[str, Any] = {}
    if decided.default is not MISSING:
        # ``has_default`` is what the template reads; the value alone is not
        # enough, because ``None`` is a legitimate default.
        kwargs["default"] = decided.default
        kwargs["has_default"] = True
    if decided.wire != decided.name:
        kwargs["alias"] = decided.wire
        kwargs["original_name"] = decided.wire
    return DataModelField(
        name=decided.name,
        data_type=_data_type(decided.type),
        required=decided.required,
        constraints=Constraints(**constraints) if constraints else None,
        extras=extras,
        use_annotated=True,
        target_python_version=TARGET,
        **kwargs,
    )


def _reported(imports: Collection[Any], into: set[tuple[str, str]]) -> None:
    """The model layer's own import records, as the ``(module, name)`` pairs we hold."""
    for imp in imports:
        if imp.from_ and imp.import_:
            into.add((imp.from_, imp.import_))


# --------------------------------------------------------------------------- #
# D6's rules: one constructor expression per runtime dataclass
# --------------------------------------------------------------------------- #
def _argument(name: str, value: Any, default: Any) -> str:
    """One argument of a rule's constructor, positional or by keyword.

    **A parameter whose default is NOTHING -- ``None`` or an empty tuple -- is spelled
    by keyword, and every other one positionally.**  That is the whole rule and it is a
    readability one: a bare ``None`` or ``()`` in a call says nothing about which
    parameter it is, where ``'oneOf'`` or a group tuple does.  So
    ``PropertyCount(minimum=None, maximum=4)`` and
    ``RequiredGroups((('rate',), ('amount',)), 'oneOf')``.

    The NAMES and their ORDER are the dataclass's own (:func:`_rule`), so adding a field
    to a rule kind in ``adcp.types._runtime`` renames nothing here.
    """
    if default is None or default == ():
        return f"{name}={value!r}"
    return repr(value)


def _clause(clause: Match) -> str:
    """One ``if`` clause as a constructor expression, every part POSITIONAL.

    :class:`adcp.types._runtime.Match` is a clause and not a rule -- it has no
    ``errors`` -- and its three parts read as a triple: a key, whether it is present, and
    the values it admits.  So :func:`_argument`'s rule does not apply to it and all three
    are written in order, which is what the class-body line has always carried.
    """
    return (
        f"{type(clause).__name__}({clause.key!r}, {clause.present!r}, {clause.allowed!r})"
    )


def _rule(rule: Rule) -> str:
    """One rule as a constructor expression, from its own dataclass fields.

    The kinds are ``adcp.types._runtime``'s frozen dataclasses, so the field names, their
    order and their defaults are declared there and read here -- §7's "one declaration of
    what a rule is".  A tuple of :func:`_clause`\\ s is written without the spaces a
    tuple's ``repr`` puts in, because it is one condition rather than a sequence of
    values.
    """
    args: list[str] = []
    for spec in dataclasses.fields(rule):
        value = getattr(rule, spec.name)
        if isinstance(value, tuple) and value and all(isinstance(v, Match) for v in value):
            args.append("(" + "".join(f"{_clause(clause)}," for clause in value) + ")")
            continue
        args.append(_argument(spec.name, value, spec.default))
    return f"{type(rule).__name__}({', '.join(args)})"


def _named_by(rule: Any) -> set[str]:
    """Every runtime symbol one rule's constructor expression names, itself included.

    Read off the VALUES and not off the rendered text: a clause nested in a tuple is a
    dataclass, so this recurses into it rather than sniffing the expression for
    ``Match(`` -- which a property key could spell.
    """
    out = {type(rule).__name__}
    for spec in dataclasses.fields(rule):
        value = getattr(rule, spec.name)
        if isinstance(value, tuple):
            out |= {n for item in value if dataclasses.is_dataclass(item) for n in _named_by(item)}
    return out


def _rule_lines(rules: Sequence[Rule]) -> tuple[list[str], set[tuple[str, str]]]:
    """The class-body entry binding ``_adcp_rules``, and the imports it names.

    The FIRST line carries no indentation and the continuation lines carry their own:
    this goes through the ``class_body_lines`` channel, whose template indents the first
    line of an entry and passes the rest through verbatim (measured, and the reason the
    shape is asymmetric rather than tidy).

    The imports are read off the rules themselves (:func:`_named_by`) plus ``Rule`` and
    ``ClassVar`` for the annotation, so a rule kind added to ``adcp.types._runtime`` and
    written by a lowering reports its own import with no second list to update.
    """
    if not rules:
        return [], set()
    body = "".join(f"        {_rule(r)},\n" for r in rules)
    imports = {(ir.RUNTIME_MODULE, "Rule"), ("typing", "ClassVar")}
    imports |= {(ir.RUNTIME_MODULE, name) for r in rules for name in _named_by(r)}
    return [f"_adcp_rules: ClassVar[tuple[Rule, ...]] = (\n{body}    )"], imports


# --------------------------------------------------------------------------- #
# one declaration at a time
# --------------------------------------------------------------------------- #
def alias(decl: ir.AliasDecl) -> Rendered:
    """``<name> = <annotation>`` for D2's root-scalar row and for a named node.

    The ANNOTATION is the renderer's -- the same ``DataModelField`` a class property
    gets, read off the field rather than out of a class body -- so a ``minLength`` on an
    alias and a ``minLength`` on a property cannot come to be spelled two different
    ways, and gate 1 applies to both.  The statement around it is the module writer's,
    because no template has a slot for a line beside an alias.

    ``required=True``: an alias is the document's own type, with no presence question to
    answer.  The ``| None`` branch belongs to an optional PROPERTY, and a property
    referencing this alias gets it from its own field.

    The description rides in ``Field`` and not in a docstring, because an alias has no
    docstring slot: five of the bundle's scalar roots had their root ``description``
    dropped for exactly that reason, and a ``Field(description=...)`` puts it in the
    alias's own JSON schema where the schema comparison finds it.
    """
    fld = _field(
        ir.Field(
            name=decl.name,
            wire=decl.name,
            type=decl.type,
            required=True,
            description=decl.description,
        )
    )
    out = Rendered(text=f"{decl.name} = {fld.annotated or fld.type_hint}")
    _reported(fld.imports, out.imports)
    # A ROOT alias's module needs the name for its ``__adcp_schema__`` line
    # (:func:`root_binding`), and the import set is a union, so reporting it from the
    # alias costs a module that has one anyway nothing.  ``constraints.py`` is the one
    # output with no document and so no reference, which is why :func:`constraints_module`
    # drops it by name.
    out.imports.add((ir.BASE_MODULE, "SchemaRef"))
    return out


#: D2's two enumeration bases, keyed by the member type the WALK decided, in the
#: document's own vocabulary (``codegen.lower.enum.BASES`` produces the key).
#:
#: The class is chosen rather than derived from a ``type_`` argument: the generator's
#: ``Enum.__init__`` reads ``type_`` only to ADD a ``str``/``int`` base class beside the
#: enumeration one, so passing it renders ``class X(str, StrEnum)`` -- which is the
#: pre-3.11 spelling ``StrEnum`` exists to replace, and whose members ``str()`` as
#: ``"X.BROAD"`` rather than as ``"broad"``.
#:
#: ``boolean`` and ``number`` are absent because this module has no base for them;
#: ``codegen.lower.enum`` refuses such a node by name, with ``bool`` carrying its own
#: reason.
_ENUM_BASES: dict[str, type[DmcgEnum]] = {"string": StrEnum, "integer": IntEnum}


def _member(member: ir.Member) -> DataModelFieldBase:
    """One member as the model layer's field.

    ``EnumMemberValue`` is the generator's own carrier for a string member, and it is
    what renders the value as a Python literal with the escaping this module owns
    (quotes, backslashes, newlines, the null byte).  A bare ``str`` would reach the
    template as that text and would be read as a rendered default.

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


def enum(decl: ir.EnumDecl) -> Rendered:
    """The Python for one decided enumeration, and the imports it needs.

    The members' NAMES are rendered verbatim (``{{ field.name }}``): this module names
    nothing here, which is why ``codegen.lower.enum`` owns the naming and why the
    injectivity check binds to its function.
    """
    model = _ENUM_BASES[decl.kind](
        reference=Reference(path=f"#/{decl.name}", original_name=decl.name, name=decl.name),
        fields=[_member(m) for m in decl.members],
        description=decl.description or None,
    )
    out = Rendered(text=model.render().rstrip("\n"))
    _reported(model.imports, out.imports)
    return out


def klass(decl: ir.ClassDecl, declared: Sequence[Approximation] = ()) -> Rendered:
    """The Python for one decided class, and the imports it needs.

    ``declared`` is §7's approximation declaration for this class's own node, already
    narrowed by :func:`declared_at`.  Empty at §14 step 8 and for every faithful class
    after it, which is why it defaults: a caller with nothing to declare says nothing.
    """
    config = {"extra": decl.extra} if decl.extra else None
    extra_template_data: defaultdict[str, Any] = defaultdict(dict)
    if config:
        extra_template_data[decl.name] = {"config": config}
    model = BaseModel(
        reference=Reference(path=f"#/{decl.name}", original_name=decl.name, name=decl.name),
        fields=[_field(f) for f in decl.fields],
        # A base is a ``TypeRef`` (§7) and its ``path`` is the SYMBOL the module writes
        # -- a class this module declares, or one it imported from a sibling.  The
        # renderer adds no import for either, for the reason ``TypeRef.local`` adds
        # none: a cross-document import is derived from the two document paths (D1) and
        # is the module writer's.
        base_classes=[
            Reference(path=f"#/{b.path}", original_name=b.path, name=b.path)
            for b in decl.bases
        ],
        custom_base_class="adcp.types._base.AdCPBaseModel",
        description=decl.description or None,
        extra_template_data=extra_template_data,
    )
    # Gate 3: the one line a built-in template renders from project-produced
    # code.  ``repr`` of a ``SchemaRef`` is a valid Python expression naming the
    # type, so there is no spelling of the ref in this module to drift from the
    # one in ``_base``.
    #
    # ``_append_internal_template_data`` APPENDS to a list, measured on 0.86.0, so a
    # caller's own lines follow the ref rather than replacing it.
    body = [f"__adcp_schema__: ClassVar[SchemaRef] = {decl.ref!r}"]
    extra_field = None
    if decl.extras is not None:
        # ``__pydantic_extra__`` is a dunder and not a field: declared as one it
        # would be a model field named ``__pydantic_extra__``, which pydantic reads
        # as the extras store rather than as a property, so it goes through the same
        # channel the schema reference does.  The ANNOTATION is still this module's
        # -- read off a ``DataModelField`` like every other type hint here -- so a
        # mapping's rendering and an extras store's cannot come to be two spellings of
        # one decision.  Only the ``name: hint`` line is ours.
        extra_field = _field(
            ir.Field(
                name="__pydantic_extra__",
                wire="__pydantic_extra__",
                type=decl.extras,
                required=True,
            )
        )
        body.append(f"__pydantic_extra__: {extra_field.type_hint}")
    rule_lines, rule_imports = _rule_lines(decl.rules)
    approximation_lines = _approximation_lines(declared)
    for line in (*body, *_union_base_lines(decl), *rule_lines, *approximation_lines):
        model._append_internal_template_data("class_body_lines", line)  # noqa: SLF001 -- the generator's own channel; see the module docstring
    out = Rendered(text=model.render().rstrip("\n"), imports=set(rule_imports))
    if approximation_lines:
        out.imports.add((ir.BASE_MODULE, Approximation.__name__))
    _reported(model.imports, out.imports)
    if extra_field is not None:
        # The same rule as ``ConfigDict`` below, and for the same reason: the generator
        # reports the import for a type its ``DataType`` COULD render, while rendering
        # the modern spelling -- ``dict[str, bool]`` with a reported ``typing.Dict``.  So
        # the extras store's imports are filtered by the names its rendered ANNOTATION
        # uses, read off the HINT rather than off ``out.text``, which contains
        # ``ConfigDict(`` and would match ``Dict`` as a substring.  Measured: this is
        # the tree's ONLY typed ``__pydantic_extra__``
        # (``core/canonical-media-buy-features.json``, first reachable at
        # ``salesagent-j3k2l.28``), and ``typing.Dict`` was the one name the generator
        # reported for it that the line does not use.  The direction is safe either way:
        # a class name that merely CONTAINS a reported name keeps an import the line
        # does not need, which is an unused import and never a ``NameError``.
        used = {
            word
            for word in extra_field.type_hint.replace("[", " ")
            .replace("]", " ")
            .replace(",", " ")
            .replace("|", " ")
            .split()
        }
        for imp in extra_field.imports:
            if imp.from_ and imp.import_ and imp.import_ in used:
                out.imports.add((imp.from_, imp.import_))
    # ``ConfigDict`` is kept exactly when the rendered text uses the name, read
    # off the text rather than off what we asked for.  The generator reports the import
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
    out.imports.add((ir.BASE_MODULE, "SchemaRef"))
    return out


def _union_base_lines(decl: ir.ClassDecl) -> list[str]:
    """§4's three facts the emitter writes onto a union BASE, plus the slot it declares.

    ``_branch_models`` is declared EMPTY and :class:`codegen.ir.UnionInstall` fills it
    after the branches exist, because §4's third mechanic is that the class which gets
    the union is the one that DECLARES the attribute: a class that inherits it keeps its
    own schema, which is the whole of subclass support.  ``_ROOT_REQUIRED`` is always
    empty in today's population and is written anyway, because the mixin's refusal reads
    it and a root with required fields refuses above.  ``_BRANCH_DISCRIMINATOR`` is the
    derived dispatch, the one fact here that is a judgement about the branches rather
    than a transcription of the root.  ``_branch_combinator`` is a classmethod and not an
    attribute because a refusal has to name a JSON Schema keyword.

    No blank line between the attributes and the method: the generator indents every body
    line, so an empty one renders as trailing whitespace.  The method goes last of the
    four, and a rule tuple after it, because each body entry is indented as a unit and a
    multi-line entry after the method reads as part of neither.
    """
    if decl.root_required is None:
        return []
    return [
        "_branch_models: ClassVar[tuple[type[AdCPBaseModel], ...]] = ()",
        f"_ROOT_REQUIRED: ClassVar[tuple[str, ...]] = {decl.root_required!r}",
        f'_BRANCH_DISCRIMINATOR: ClassVar[str] = "{decl.discriminator or ""}"',
        "@classmethod",
        "def _branch_combinator(cls) -> str:",
        f'    return "{decl.combinator or ""}"',
    ]


def root_binding(decl: ir.RootBinding, declared: Sequence[Approximation] = ()) -> Rendered:
    """The module-level half of a root that is not an ``AdCPBaseModel``.

    ``declared`` is §7's "beside the module for an alias": an alias has no class body and
    an enumeration has no ``class_body_lines`` slot at all, so the declaration binds at
    module scope exactly where ``__adcp_schema__`` binds -- which is the same split §4 of
    the semantics document already makes for ``strict_validate``, and so the same
    reasoning.

    D2 gives two root kinds no class to hang ``strict_validate`` on: a scalar root is an
    ``Annotated`` alias, and an enumeration cannot carry a class-body line at all because
    ``Enum.jinja2`` has no ``class_body_lines`` slot and D9 forbids writing one in
    afterwards.  Both therefore bind the SAME two statements at module scope -- the
    reference, and ``strict_alias`` over it -- so a class, an alias and an enumeration
    cannot come to answer differently about what their own document accepts.
    ``strict_alias`` reaches the document through ``schema_at`` and refuses through
    ``_refuse``, which is exactly what ``AdCPBaseModel.strict_validate`` does.

    One function and not two, because the rows differ only in the declaration BETWEEN
    the statements.  ``tests/test_emit.py`` reads the pairing off the module for both.
    """
    inner = declaration(decl.declaration)
    imports = inner.imports | {(ir.BASE_MODULE, "SchemaRef"), (ir.BASE_MODULE, "strict_alias")}
    lines = _approximation_lines(declared, annotated=False)
    beside = ""
    if lines:
        imports.add((ir.BASE_MODULE, Approximation.__name__))
        beside = f"\n{lines[0]}\n"
    return Rendered(
        text=f"__adcp_schema__ = {decl.ref!r}\n{beside}\n"
        f"{inner.text}\n\n\n"
        f'strict_validate = strict_alias(__adcp_schema__, "{decl.symbol}", {decl.symbol})',
        imports=imports,
    )


def union_install(decl: ir.UnionInstall) -> Rendered:
    """§4's rebuild: the base takes its branches, and pydantic is told.

    Two statements beside the classes, which is the module writer's own text (§1: no
    template has a slot for a line beside a class), and they declare no name -- so they
    are appended to the module's declarations rather than declared.
    """
    base = decl.base.path
    return Rendered(
        text=f"{base}._branch_models = ({', '.join(b.path for b in decl.branches)},)\n"
        f"{base}.model_rebuild(force=True)"
    )


def root_model(decl: ir.RootModelDecl, declared: Sequence[Approximation] = ()) -> Rendered:
    """§7's ``RootModelDecl``: a root that is neither a class nor an alias.

    A ``RootModel`` subclass, written by this module rather than through the model layer's
    ``BaseModel`` template, because the body is one ``root:`` annotation and not a field
    list and no template of the pinned generator has that shape.  The ANNOTATION is still
    a ``DataModelField``'s ``type_hint`` (:func:`_field`), so a root model's type and a
    property's cannot come to be two spellings of one decision.

    It carries the same three things a class carries -- ``__adcp_schema__``, the rule
    tuple, and the dispatch facts for a mixed root union -- which is §8's own requirement:
    "each must carry ``__adcp_schema__``, ``strict_validate`` and a rule tuple exactly as a
    class does, or a root model and a class disagree about what their document accepts."
    ``strict_validate`` arrives by inheritance from ``AdCPRootModel``, which §8 declares.

    **No producer in the walk at §14 step 8**, which is the step's own exit condition: the
    three rows that lower to one are step 9's.  ``tests/test_approximation.py`` renders a
    hand-built declaration, so the path from the IR to text is graded before a handler
    writes one.
    """
    annotation = _field(
        ir.Field(
            name=ir.ROOT_FIELD,
            wire=ir.ROOT_FIELD,
            type=decl.type,
            required=True,
            # **D6's ``uniqueItems``, DERIVED from the rule tuple rather than carried
            # beside it.**  :attr:`ir.Field.distinct` is the ``json_schema_extra`` half of
            # one claim whose other half is the ``UniqueItems`` rule, and at a root the two
            # halves are both this declaration's: the rule is keyed on
            # :data:`ir.ROOT_FIELD`, so the rule tuple already says the fact, and a second
            # slot on :class:`ir.RootModelDecl` holding it would be the second copy
            # ``ir.Field.distinct``'s own reasoning warns about.  §8 of the semantics
            # document needs the fact RENDERED -- pydantic v2 removed ``unique_items``, so
            # ``json_schema_extra`` is the one channel that reaches
            # ``model_json_schema()`` -- and this is where it is written.
            distinct=any(
                isinstance(rule, UniqueItems) and rule.key == ir.ROOT_FIELD
                for rule in decl.rules
            ),
        )
    )
    body = [
        # ``annotated or type_hint``, which is :func:`alias`'s own expression and for its
        # reason: the ``Field`` is where every fact that is not the type word itself rides
        # -- the ``minItems``/``maxItems`` of a root array, and D6's ``uniqueItems``
        # through ``json_schema_extra`` -- and ``type_hint`` alone is the type with the
        # ``Field`` dropped.  Measured on ``core/acceptance-policy-profile-ids.json``:
        # ``type_hint`` alone rendered ``root: list[StrMinLen1]`` and
        # ``model_json_schema()`` then stated no ``uniqueItems``, so §8's comparison read
        # the document's own keyword as *missing* at a root model whose rule tuple
        # enforces it.
        f"{ir.ROOT_FIELD}: {annotation.annotated or annotation.type_hint}",
        f"__adcp_schema__: ClassVar[SchemaRef] = {decl.ref!r}",
    ]
    rule_lines, rule_imports = _rule_lines(decl.rules)
    approximation_lines = _approximation_lines(declared)
    lines = "\n".join(
        f"    {line}" for line in (*body, *rule_lines, *approximation_lines)
    )
    docstring = f'    """{decl.description}"""\n' if decl.description else ""
    imports = {
        ("typing", "ClassVar"),
        (ir.BASE_MODULE, "SchemaRef"),
        (ir.BASE_MODULE, ROOT_MODEL),
        *rule_imports,
    }
    if approximation_lines:
        imports.add((ir.BASE_MODULE, Approximation.__name__))
    for imp in annotation.imports:
        if imp.from_ and imp.import_:
            imports.add((imp.from_, imp.import_))
    return Rendered(
        text=f"class {decl.name}({ROOT_MODEL}):\n{docstring}{lines}", imports=imports
    )


def declaration(
    decl: ir.Declaration, approximations: Sequence[Approximation] = ()
) -> Rendered:
    """One declaration's text and imports: the ONE dispatch over ``codegen.ir``.

    ``approximations`` is the MODULE's whole tuple and the three writers that carry one
    narrow it themselves, through :func:`declared_at` at their own ``ref``.  Narrowed here
    rather than by the caller, because which node a declaration's ``ref`` names is a fact
    about the declaration and this is the one dispatch that holds every kind of it.

    An ``EnumDecl``, an ``AliasDecl`` and a ``UnionInstall`` carry none and are handed
    none: a nested enumeration has no ``class_body_lines`` slot at all (``EnumDecl``'s own
    docstring), a nested alias binds no ``__adcp_schema__`` and is no pair, and a union
    install declares no name.  Each is contained in a node that DOES carry one, by
    :func:`declared_at`'s containment rule, so nothing is lost.
    """
    if isinstance(decl, ir.ClassDecl):
        return klass(decl, declared_at(approximations, decl.ref))
    if isinstance(decl, ir.EnumDecl):
        return enum(decl)
    if isinstance(decl, ir.AliasDecl):
        return alias(decl)
    if isinstance(decl, ir.RootBinding):
        return root_binding(decl, declared_at(approximations, decl.ref))
    if isinstance(decl, ir.RootModelDecl):
        return root_model(decl, declared_at(approximations, decl.ref))
    if isinstance(decl, ir.UnionInstall):
        return union_install(decl)
    raise TypeError(f"no rendering for {type(decl).__name__}")


# --------------------------------------------------------------------------- #
# §7: the approximation declaration, written into the emitted module
# --------------------------------------------------------------------------- #
#: The annotation the class-body line carries, so the declaration is a ``ClassVar`` like
#: ``__adcp_schema__`` beside it rather than a model field pydantic would try to validate.
APPROXIMATIONS_HINT = f"ClassVar[tuple[{Approximation.__name__}, ...]]"


def declared_at(approximations: Sequence[Approximation], ref: SchemaRef) -> tuple[Approximation, ...]:
    """Every approximation at or INSIDE the node ``ref`` names, in document order.

    **Containment and not the nearest declaration**, and the reason is the pairing §9
    grades over.  A pair's comparison descends from its own node into the whole subtree --
    a property's facts, an ``items``, a ``propertyNames`` -- so a root class's comparison
    reports a fact at ``#/properties/x/maxLength`` as well as the nested class's own
    comparison does.  A declaration carried only by the nearest enclosing class would
    therefore leave the enclosing pair reporting that fact as *missing*, which is §8's
    defect, for a widening the design declared.  Carrying it on every declaration whose
    node contains it costs a repeated line in one module and makes both pairs read the
    same answer.

    Over-coverage in the other direction is harmless and measured: a root union's BASE is
    at ``#`` and so contains ``#/oneOf/0/...``, which the base's own comparison never
    visits because ``compare`` does not descend a combinator.  A declaration the
    comparison does not reach is neither *approximated* nor *over-declared* at that pair;
    the run-level equality (§8) ranges over the union of the pairs, where the branch pair
    reports it.

    The prefix test is on ONE spelling of a pointer -- ``SchemaRef``'s, which
    ``compiler.schema_ref`` is the sole producer of -- and the separator is part of the
    prefix, so ``#/properties/x`` does not contain ``#/properties/xy``.
    """
    prefix = ref.pointer if ref.pointer.endswith("/") else ref.pointer + "/"
    return tuple(
        a
        for a in approximations
        if a.document == ref.document and (a.pointer == ref.pointer or a.pointer.startswith(prefix))
    )


def _approximation_lines(
    declared: Sequence[Approximation], *, annotated: bool = True
) -> list[str]:
    """The one declaration line, or no line at all where nothing was approximated.

    ``annotated`` is the one difference between the two writers: inside a class body the
    declaration is a ``ClassVar``, like ``__adcp_schema__`` and ``_adcp_rules`` beside it,
    so pydantic reads it as a class attribute and not as a model field; at MODULE scope
    there is no model for an annotation to be about, which is the same shape
    ``__adcp_schema__`` already takes in a root binding (a ``ClassVar`` in a class, a bare
    assignment beside a module).

    The FIRST line carries no indentation and the continuation lines carry their own, for
    :func:`_rule_lines`'s measured reason: the ``class_body_lines`` channel's template
    indents the first line of an entry and passes the rest through verbatim.  At module
    scope the first line is already at its own level, so one shape serves both.

    **No line where the tuple is empty, which is §14 step 8's byte-exact check.**  The
    step says the tree "changes by one line per module (``__adcp_approximations__ = ()``)",
    and that is an allowance rather than an obligation: an ABSENT attribute and an empty
    tuple are the same answer to the one question a consumer asks (``vars(cls).get(...,
    ())``), so writing the empty case buys a reader nothing and costs the step its
    strongest evidence -- an emitted tree that is byte-identical to the one before the
    instrument existed.  The row that widens the first cell is where the line appears, in
    the modules whose documents it widens and nowhere else.

    ``repr`` of a tuple of ``NamedTuple``s is a valid Python expression naming the type,
    which is how ``__adcp_schema__`` is written already; there is therefore no spelling of
    an approximation in this module to drift from the one in ``adcp.types._base``.  One
    entry per line, because a declaration is read by a human looking for a pointer.
    """
    if not declared:
        return []
    entries = "".join(f"        {a!r},\n" for a in declared)
    hint = f": {APPROXIMATIONS_HINT}" if annotated else ""
    return [f"{APPROXIMATIONS}{hint} = (\n{entries}    )"]


# --------------------------------------------------------------------------- #
# the module text (D8: the emitter owns its layout)
# --------------------------------------------------------------------------- #
def _import_rank(module: str) -> int:
    """stdlib, the third-party library, this package's own hand-written modules,
    then a sibling module of this tree (always relative, so always
    ``.``-prefixed)."""
    if module.startswith("."):
        return 3
    if module in (ir.BASE_MODULE, ir.RUNTIME_MODULE, constraint_names.MODULE):
        return 2
    return 1 if module == "pydantic" else 0


def _import_block(imports: Collection[tuple[str, str]]) -> list[str]:
    """The import statements, grouped by :func:`_import_rank` and sorted within a rank."""
    groups: list[list[str]] = [[], [], [], []]
    by_module: dict[str, set[str]] = {}
    for module, name in imports:
        by_module.setdefault(module, set()).add(name)
    for module in sorted(by_module):
        names = ", ".join(sorted(by_module[module]))
        groups[_import_rank(module)].append(f"from {module} import {names}")
    out: list[str] = []
    for group in groups:
        if group:
            out += [*group, ""]
    return out


def blocks(
    declarations: Sequence[ir.Declaration], approximations: Sequence[Approximation] = ()
) -> list[Rendered]:
    """Every declaration rendered, in declaration order."""
    return [declaration(decl, approximations) for decl in declarations]


def module(mod: ir.Module, exports: Sequence[str]) -> str:
    """One document's module: the header, the imports, the declarations, ``__all__``.

    ``mod`` is :class:`codegen.ir.Module`, the value ``codegen/lower/names.py`` returns:
    this reads its ``document``, its ``declarations`` and the imports the WALK decided --
    a cross-document symbol, a base class, a runtime name -- and unions them with the
    imports each rendered declaration reports.  Every symbol in it is already bound, so
    the renderer resolves nothing.

    It took a ``Written`` Protocol over three attributes while ``Module`` lived in the
    decision layer, which §11's arrows (``ir <- render <- emit``) forbid this module to
    know; §7 puts ``Module`` in ``codegen.ir`` and §14 step 7 is what got it there, so
    the type is named directly.  The export list is the walk's
    (``emit.exported``), because which names another module may ask for is a decision
    about the bundle and not about text.
    """
    rendered = blocks(mod.declarations, mod.approximations)
    imports = set(mod.imports)
    for one in rendered:
        imports |= one.imports
    out = [
        f"# Generated by codegen.emit from {mod.document}. Do not edit.",
        "from __future__ import annotations",
        "",
        *_import_block(imports),
    ]
    classes = "\n\n\n".join(one.text for one in rendered)
    names = ", ".join(f'"{n}"' for n in exports)
    return "\n".join([*out, "", classes, "", "", f"__all__ = [{names}]", ""])


# --------------------------------------------------------------------------- #
# the constraints module, which belongs to no document (§8)
# --------------------------------------------------------------------------- #
#: The same first line every emitted module carries, less the document name: the
#: constraints module is the one output that belongs to no document.
CONSTRAINTS_HEADER = "# Generated by codegen.emit. Do not edit."

#: ``AdCPUrl`` is ours: ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``,
#: named for provenance rather than after a standard, because pydantic exports 22
#: URL types and none is https-only -- a name like ``HttpsUrl`` would read as an
#: upstream export a reader cannot find.  The NAME is ``constraints.URL`` and the
#: STATEMENT is here, because a statement is text (§7).
URL_LINE = (
    f'{constraint_names.URL} = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]'
)

#: What :data:`URL_LINE` names, plus ``HttpUrl``: pydantic's own, RE-EXPORTED by the
#: constraints module rather than imported from ``pydantic`` at each site.  The import IS
#: the declaration -- no assignment, so nothing in this package restates what pydantic
#: defines -- and it is there and not left to ``pydantic`` because the SDK's ``uri``
#: decision is a SPLIT: a consumer reading a module that declared only ``AdCPUrl`` would
#: read the https-only arm as the whole rule.  One place names both arms.
URL_IMPORTS = {
    ("typing", "Annotated"),
    ("pydantic", "AnyUrl"),
    ("pydantic", "UrlConstraints"),
    ("pydantic", constraint_names.HTTP_URL),
}

CONSTRAINTS_DOCSTRING = '''"""Constrained types, each named for the constraint it carries.

GENERATED by ``codegen.emit``; see ``codegen/constraints.py``.  Edit neither --
the tree is ``f(bundle, emitter, pinned compiler)`` and a hand edit here is a
fact no input states (P10).

Every other type this SDK emits is reachable at ``adcp.types.<domain>.<Name>``,
where the domain is the schema document's own path.  A type derived from a
CONSTRAINT belongs to no document, so it has no domain and lives here instead.
Its name is derived from the constraint and from nothing else -- never from a
property key and never from a domain word, because two fields sharing a bound
are not thereby the same idea.  A ``pattern`` has no readable name that is not a
concept, so it contributes eight hex digits of its own SHA-256.  Two distinct
constraints deriving one name is a build failure rather than a shared alias.

A bound on a CONTAINER is named here too, and such an alias is GENERIC: the bound is
the alias and the contents are its parameter, so ``NonEmptyList[MediaBuyStatus]`` is a
list of statuses with at least one member and ``NonEmptyList`` names the bound once for
every content type.  ``NonEmptyList[T]`` is declared whatever a run met, because the
design names it and a consumer annotating a non-empty list of their own imports it from
here.

Two names here are DECISIONS rather than derivations, and together they are this
SDK's whole answer for ``format: uri``: a field's type FOLLOWS THE DOCUMENT'S OWN
PATTERN.

``AdCPUrl`` annotates a field whose document restricts the scheme to https
(``pattern: ^https://``, 47 of the bundle's 300 ``uri`` positions).  There the type
and the document agree.

``HttpUrl`` -- pydantic's own, re-exported here so that both arms are named in one
place -- annotates every other ``uri`` field.  ``AdCPUrl`` everywhere was tried and
withdrawn: ``format: uri`` is RFC 3986, so a document stating only
``{"type": "string", "format": "uri"}`` admits ``http://``, ``urn:`` and
``file:///`` as well, and refusing those made the SDK stricter than the spec it
implements -- at 228 of 300 positions.  ``HttpUrl`` still refuses ``urn:`` and
``file:``, which is a named ceiling rather than an oversight.

Either way the document's own ``pattern`` stays with the schema half: the bundle
states eight distinct ones across 73 of its 300 ``uri`` uses, and no URL type can
carry a ``pattern`` at all -- pydantic refuses to build one.  ``strict_validate``
applies the document before the constructor ever runs, so the accepted set at the
entry point is the document's.
"""'''


def constraints_module(shapes: Mapping[str, constraint_names.Shape]) -> str:
    """The text of ``adcp/types/constraints.py``, for the shapes a run met (§8).

    :data:`URL_LINE` is declared whatever the run met, because it is a DECISION rather
    than a derivation -- D5 names it, ``emit.FORMAT_TYPES`` points every ``format: uri``
    field at it, and a consumer who wants to parse a URL of their own imports it from
    here.  ``constraints.NAMED_CONTAINERS`` is declared for the same reason: §5 names
    ``NonEmptyList[T]`` and a consumer annotating a non-empty list of their own imports
    it from here.  The derived aliases are exactly the shapes the run resolved, sorted,
    so the module is a function of the run and holds no alias nothing names.

    A generic alias needs its type VARIABLES declared, and exactly the ones the lines use
    are: ``T`` is always one, because ``NonEmptyList`` is always declared, and ``K``/``V``
    arrive with the first bounded mapping.  Derived rather than always written, so the
    module holds no name nothing in it reads.

    The ANNOTATIONS are :func:`alias`'s, the same statement a root alias and a named node
    get, so a ``minLength`` on an alias here and a ``minLength`` on a property there
    cannot come to be spelled two different ways.  What is this function's is the module
    around them.  :func:`alias` also reports the ``SchemaRef`` import a ROOT alias module
    needs; these aliases carry no schema reference -- an alias has no document -- so that
    one import is dropped here by name.

    The LAYOUT is the emitted modules' own (:func:`module`): stdlib, then the library,
    one blank line between the groups.  Spelled here rather than shared, because
    :func:`module` writes a module of CLASSES with an ``__all__`` and a document header,
    and two of :func:`_import_rank`'s four ranks cannot occur here at all -- an alias
    imports nothing but the annotation machinery.
    """
    declared, variables = constraint_names.declarations(shapes)
    imports: set[tuple[str, str]] = set(URL_IMPORTS)
    lines: list[str] = [URL_LINE]
    for name in sorted(declared):
        rendered = alias(declared[name])
        lines.append(rendered.text)
        imports |= {i for i in rendered.imports if i != (ir.BASE_MODULE, "SchemaRef")}
    if variables:
        imports.add(("typing", "TypeVar"))
        lines = [f'{p} = TypeVar("{p}")' for p in variables] + ["", *lines]
    by_module: dict[str, set[str]] = {}
    for module_, item in imports:
        by_module.setdefault(module_, set()).add(item)
    groups = [
        [
            f"from {m} import {', '.join(sorted(by_module[m]))}"
            for m in sorted(by_module)
            if keep(m)
        ]
        for keep in (lambda m: m != "pydantic", lambda m: m == "pydantic")
    ]
    head: list[str] = []
    for group in groups:
        if group:
            head += ["", *group]
    return "\n".join(
        [
            CONSTRAINTS_HEADER,
            CONSTRAINTS_DOCSTRING,
            "",
            "from __future__ import annotations",
            *head,
            "",
            "",
            *lines,
            "",
        ]
    )
