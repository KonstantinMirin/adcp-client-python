"""The compiler half: a class declaration in, Python out.

``docs/plan/rebuild-plan.md`` §1 splits the pipeline at a DECISION rather than at
a translation.  Our walk reads the JSON Schema and decides what each node becomes -- a class, an
annotation, an enumeration or a rule -- what it is called, which fields it has
and what constrains them.  This module takes that declaration and nothing else,
and hands it to
``datamodel-code-generator``'s pydantic-v2 MODEL layer, which writes the Python.

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

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from datamodel_code_generator import PythonVersion
from datamodel_code_generator.model.pydantic_v2 import BaseModel, DataModelField
from datamodel_code_generator.model.pydantic_v2.base_model import Constraints
from datamodel_code_generator.model.pydantic_v2.types import DataTypeManager
from datamodel_code_generator.reference import Reference

from adcp.types._base import SchemaRef

#: The floor of ``requires-python``.  It decides the rendered spelling of an
#: optional (``T | None`` rather than ``Optional[T]``), so it is named once here
#: and never inferred from the interpreter running the emitter -- the output is a
#: function of (bundle, document set, this package) and of nothing else (P7).
TARGET = PythonVersion.PY_310

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
    """

    path: str
    local: bool = False

    def data_type(self) -> Any:
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
    #: Set only when :class:`Type` does not already carry the format -- a
    #: ``format`` whose Python type the walk declined to use because a
    #: constraint sits beside it.  It then rides as ``json_schema_extra``, which
    #: states the fact without changing what is accepted: draft-07 ``format`` is
    #: an annotation and ``jsonschema`` asserts nothing for it.  Dropping it
    #: instead loses a fact the document states, which the schema comparison
    #: grades (measured: ``core/platform-extension-ref.json``'s ``uri`` carries
    #: ``format: uri`` beside a ``pattern``).
    format: str | None = None


@dataclass(frozen=True)
class Class:
    """One decided class.  ``ref`` is the schema it will carry and grade against."""

    name: str
    ref: SchemaRef
    properties: tuple[Property, ...]
    description: str | None = None
    #: D7: ``forbid``, ``allow``, or ``None`` to leave the base's default.
    extra: str | None = None


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
        base_classes=[],
        custom_base_class="adcp.types._base.AdCPBaseModel",
        description=decided.description or None,
        extra_template_data=extra_template_data,
    )
    # Gate 3: the one line a built-in template renders from project-produced
    # code.  ``repr`` of a ``SchemaRef`` is a valid Python expression naming the
    # type, so there is no spelling of the ref in this module to drift from the
    # one in ``_base``.
    model._append_internal_template_data(  # noqa: SLF001 -- dmcg's own channel; see the module docstring
        "class_body_lines",
        f"__adcp_schema__: ClassVar[SchemaRef] = {decided.ref!r}",
    )
    out = Rendered(text=model.render().rstrip("\n"))
    for imp in model.imports:
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
