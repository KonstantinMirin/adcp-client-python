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

import ast
import dataclasses
import datetime
import enum as stdlib_enum  # ``enum`` is this module's own renderer for an enum
import re
import typing
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pydantic
from datamodel_code_generator import PythonVersion
from datamodel_code_generator.imports import Import
from datamodel_code_generator.model import DataModelFieldBase
from datamodel_code_generator.model.enum import Enum as DmcgEnum
from datamodel_code_generator.model.enum import EnumMemberValue, IntEnum, StrEnum
from datamodel_code_generator.model.pydantic_v2 import BaseModel, DataModelField
from datamodel_code_generator.model.pydantic_v2.base_model import Constraints
from datamodel_code_generator.model.pydantic_v2.types import DataTypeManager
from datamodel_code_generator.python_literal import PythonCode, represent_python_value
from datamodel_code_generator.reference import Reference
from datamodel_code_generator.types import DataType
from pydantic import BaseModel as PydanticBaseModel

from adcp.types import _base as adcp_base
from adcp.types import _runtime as adcp_runtime
from adcp.types._base import APPROXIMATIONS, Approximation, SchemaRef
from adcp.types._runtime import Distinct, Match, Rule, UniqueItems
from codegen import bundle, ir
from codegen import constraints as constraint_names
from codegen.ir import MISSING

#: The runtime base §8 of the architecture document gives a root model, named here and
#: imported by no emitted module until a handler declares one (§14 step 9).  A NAME and
#: not an import of the class, for the reason every other emitted-module symbol is a name:
#: the renderer writes text, and a symbol it names is not a Pydantic idiom (§8).
ROOT_MODEL = "AdCPRootModel"

#: The artifact package every emitted module imports its own hand-written and generated
#: siblings from, as an import PREFIX, derived from ``ir``'s own declaration of the base
#: module's path.  :func:`_import_rank` is the one reader: an absolute import under this
#: prefix is the SDK's own and groups with ``_base``, ``_runtime`` and ``constraints``
#: rather than with the standard library.
ARTIFACT = ir.BASE_MODULE.rsplit(".", 1)[0] + "."

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
#: spelling back again, so the translation states neither more nor less than the keyword
#: it came from -- and enforces the bound (``{}`` refused, one key accepted, five
#: refused).
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
    if decided.members:
        # **§5's ``enum`` row at CONJ: a ``Literal`` over the ENUMERATION'S MEMBERS**, and
        # the subscript is composed here for ``container="alias"``'s reason -- the model
        # layer has no carrier for "this enumeration's members", and spelling one as a
        # path loses its qualifier to ``treat_dot_as_module`` (:attr:`ir.TypeRef.members`
        # carries the probe).
        #
        # ``data_types=[holder]`` is what carries the ENUMERATION's own import to the
        # module, exactly as the alias arm passes its arguments rather than only spelling
        # them; ``import_`` carries ``typing.Literal``, which is this arm's own.  Written
        # with only the text, the module names a symbol it does not import.
        holder = _data_type(dataclasses.replace(decided, members=()))
        return _TYPES.data_type(
            type="Literal[{}]".format(
                ", ".join(f"{holder.type_hint}.{member}" for member in decided.members)
            ),
            import_=_TYPES.get_data_type_from_full_path(
                "typing.Literal", is_custom_type=False
            ).import_,
            data_types=[holder],
        )
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

#: **The modules an emitted module imports a name FROM that the walk does not report.**
#: ``compiler.Module.imports`` holds what a lowering reported -- a cross-document symbol,
#: and the runtime carriers a lowering names for itself -- and these are the ones decided
#: HERE, at render: the model layer (``Field``, ``ConfigDict`` and every pydantic type a
#: ``DataType`` renders), the type vocabulary the generator reports against
#: (``Annotated``, ``ClassVar``, ``Literal``, ``StrEnum``), and the runtime's own
#: carriers.  Measured over the 1,054 portable documents: every one of the 909 emitted
#: modules imports ``SchemaRef``, 616 import ``Field`` and ``Annotated``, 442 import
#: ``StrEnum``, and none of those pairs is in ``Module.imports``.
#:
#: ``adcp.types.constraints`` is deliberately NOT here even though an emitted module
#: imports its aliases: it is a whole-RUN artifact, so reading its contents to decide a
#: name would be exactly the census §9 forbids -- a one-document emission and a
#: whole-bundle emission would spell the same class differently.  Every alias spelling a
#: class name could collide with is a pydantic name (``HttpUrl``, ``AnyUrl``) or begins
#: with a type word no property key spells (``StrMinLen1``, ``IntMin0Max1000``).
_SCOPE_MODULES = (pydantic, typing, stdlib_enum, datetime, adcp_base, adcp_runtime)

#: **Every name the RENDERER can bring into an emitted module's scope**, which is the
#: other half of that module's namespace and therefore of §4's collision rule
#: (``names.spell``): a class named ``Field`` shadows ``pydantic.Field``, and every
#: ``Annotated[X, Field(description=…)]`` in the module then calls the CLASS.  Measured
#: over the portable set with §4's nested rule in force: 4 positions derive ``Field`` for
#: a property named ``field`` and 1 derives ``Presence``, and every one of the 5 is in a
#: module that imports the name it would shadow.
#:
#: Read off the MODULES above with ``dir``, and never listed by name, for the reason
#: :data:`RESERVED` is read off ``dir(BaseModel)``: a list of names is a second copy of
#: another package's surface and drifts the first time that package adds one.  The cost
#: of the wider reading is measured and it is small -- 14 positions of 2,226 lengthen
#: against a ``typing`` name no module imports, 13 of them a property called ``type`` and
#: one called ``collection`` -- and it falls on the safe side: a prefix a module did not
#: need is a long name, where a name a module did need is an import silently retyped.
#:
#: HERE for :data:`RESERVED`'s reason, which §8 decides: this is the one module under
#: ``codegen/`` outside ``verify/`` that may read the model layer, ``lower/`` is banned
#: from it outright, and the run hands the SET to the naming pass as data.
CARRIERS = frozenset(
    name
    for module in _SCOPE_MODULES
    for name in dir(module)
    if not name.startswith("_")
)


#: The model layer's own name for "construct this annotation's value from JSON", which is
#: the ONE spelling :func:`_constructed_default` can write, and the reason is a
#: MEASUREMENT of what reaches this module rather than a preference between spellings.
#:
#: §5 requires a ``default`` to be emitted through its annotation's own type.  That needs
#: the annotation's KIND -- an enumeration takes ``Carrier(value)``, a class takes
#: ``Carrier.model_validate(value)``, and an ``Annotated`` alias takes NEITHER because it
#: is not callable -- and **a** :class:`codegen.ir.TypeRef` **does not carry it.**  Measured
#: over the 1,054 portable documents: ``LanguageTag`` (an alias, ``Annotated[StrMinLen2…,
#: Field(description=…)]``) and ``SortMetric`` (a ``StrEnum``) both arrive here as
#: ``TypeRef(path=<name>, local=True, container='', of=(), key=None, literals=(),
#: members=(), facts={}, format=None, validators=())`` -- byte-identical -- so no
#: condition over a ``TypeRef`` tells them apart.  Nor does ``Module.declarations``: of the
#: 120 defaulted fields whose carrier is a declaration this run emits, **58 name a symbol
#: IMPORTED from another module**, whose kind that module alone declares.  A rule reading
#: "call the local carrier" therefore emits ``LanguageTag('en')`` at 2 sites, which is a
#: ``TypeError`` at module import and takes the package down.
#:
#: ``TypeAdapter`` needs no kind.  It takes the annotation itself -- the text
#: :func:`_data_type` already decides for the field -- and validates the document's JSON
#: through it, so one spelling is correct at every carrier the bundle has: a ``StrEnum``
#: comes back a MEMBER, a class comes back an INSTANCE, a nested enumeration inside a
#: class's own field comes back a member too (pydantic validates to the leaf), and an
#: alias comes back the value it already was.  mypy reads
#: ``TypeAdapter(X).validate_python(...)`` as ``X``, which is the half a checker grades.
#:
#: HERE and not in ``lower/``, because the walk decided the type and the value and this is
#: the text for them -- §1's seam, and the same one ``container="alias"`` and
#: :func:`_bound_to_the_type` are composed on.
#:
#: As the ``(module, name)`` PAIR this module holds an import as, because both readers
#: need a different half of it: :func:`_constructed_default` resolves the dotted path
#: through the model layer to get the spelling, and :func:`klass` matches the bare name
#: against the rendered text to decide the import.  Two spellings of one symbol is how
#: those two come apart.
TYPE_ADAPTER = ("pydantic", "TypeAdapter")

#: ``pydantic.Field``, as the ``(module, name)`` pair, for the two lines this module writes
#: a ``Field(...)`` CALL into itself rather than handing keywords to the model layer.
#:
#: **Both exist because PEP 681 reads a field specifier off the ASSIGNED VALUE and nowhere
#: else**, which is the whole of ``adcp-client-python-82m.52`` and ``.53``: a consumer's
#: checker synthesises ``__init__`` from ``dataclass_transform`` on pydantic's metaclass
#: (``field_specifiers=(Field, PrivateAttr, NoInitField)``) and reads ``default``,
#: ``default_factory`` and ``init`` only from what the declaration is ASSIGNED.  Pydantic
#: reads them from an ``Annotated`` extra as happily, so the two spellings are identical at
#: runtime and only one of them is true to a consumer.
#:
#: The pair, and resolved through the model layer at the point of use, for
#: :data:`TYPE_ADAPTER`'s reason: the spelling is the model layer's and the import is this
#: module's, and two spellings of one symbol is how those come apart.
FIELD = ("pydantic", "Field")


def _field_symbol() -> str:
    """``pydantic.Field``'s spelling in the emitted module, off the model layer."""
    return _TYPES.get_data_type_from_full_path(".".join(FIELD), is_custom_type=False).type_hint


def _constructed_default(decided: ir.Field) -> PythonCode | None:
    """§5's constructed ``default`` as a ``default_factory`` expression, or ``None``.

    **The rule fires where the field's value must be an instance of something this run
    EMITS**, which is the one position a raw JSON literal can disagree with the
    annotation: a declaration's name resolves to a class, an enumeration or an alias, and
    only the first two make the literal wrong -- but see :data:`TYPE_ADAPTER` for why this
    cannot ask which.  A carrier the model layer already owns (``bool``, ``str``,
    ``adcp.types.constraints.IntMin1``, ``pydantic.NonNegativeInt``) is skipped: the
    document's JSON IS a value of it, so there is nothing to construct and firing would
    be churn.

    ``None`` is skipped as a VALUE and not as an absence: ``default: null`` is a default
    (:data:`codegen.ir.MISSING` is what absence is), and ``None`` inhabits the ``| None``
    every optional field's annotation carries, so it needs no construction.

    The three positions it reaches are the three the section's table names -- the type
    itself, a ``list`` of it, and a ``dict`` of it -- and the annotation handed to the
    adapter is the field's own WITHOUT the ``| None``: the document states a non-null
    default, so what it has to validate against is the type the document declares there.
    A ``union`` of two real arms is NOT one of them and is skipped, because there is no
    single type to validate through and the arm the value belongs to is the document's
    judgement rather than this module's.
    """
    if decided.default is MISSING or decided.default is None:
        return None
    carried = decided.type
    if carried.container in {"list", "dict"}:
        carried = carried.of[0] if carried.of else carried
    # A BARE reference to an emitted declaration, and nothing else: a container, a
    # ``Literal``, a member subscript or a type carrying value rules is already a
    # composed annotation, and ``local`` on one of those says nothing about the value's
    # own type.  ``ir.symbols`` reads ``local`` the same way -- "a local arm is marked
    # ``local`` where it is decided" -- which is why this needs no second notion of what
    # a reference is.
    if not (
        carried.local
        and carried.path
        and not carried.container
        and not carried.literals
        and not carried.members
        and not carried.validators
    ):
        return None
    adapter = _TYPES.get_data_type_from_full_path(".".join(TYPE_ADAPTER), is_custom_type=False)
    return PythonCode(
        f"lambda: {adapter.type_hint}({_data_type(decided.type).type_hint})"
        f".validate_python({represent_python_value(decided.default)})"
    )


#: ``adcp.types._base.OmittedNotNull``, as the ``(module, name)`` pair this module holds
#: an import as -- :data:`FIELD`'s and :data:`MEMBER_ALIAS`'s own form, and for their
#: reason: the NAME is written into the annotation and the IMPORT into the module header,
#: and two spellings of one symbol is how those come apart.
#:
#: The name is read off the runtime declaration rather than typed, so renaming the marker
#: there renames nothing here.
OMITTED_NOT_NULL = (ir.BASE_MODULE, adcp_base.OMITTED_NOT_NULL)


class _OptionalMember(DataModelField):
    """A field whose ``Annotated`` carries one more item than the model layer puts there.

    **The marker belongs OUTSIDE the ``| None``, which is why it cannot ride the type.**
    :data:`adcp.types._base.OmittedNotNull` strikes the null arm an OPTIONAL rendering
    added, and that arm is the model layer's: the ``| None`` is derived from
    ``required=False`` here and nowhere else (see :func:`_field`'s own note on the
    arrangement that took it away).  §2's value rules compose inside the type
    (:func:`_bound_to_the_type`) and so are inside the union; this has to be the last item
    of the field's own ``Annotated``, where ``handler(source)`` hands it the nullable
    schema to strike.

    So the one property that composes that list is extended, rather than a template being
    vendored: the pinned generator renders ``Annotated[<hint>, <Field(...)>]`` and has no
    slot for a third item.  Everything else -- the hint, the ``Field(...)`` call, the
    assignment, the imports the hint needs -- is the layer's, unchanged.
    """

    #: Whether this field takes the marker: ``codegen.ir.admits_null`` read at
    #: :func:`_field`, which is the one place the decision is made.
    omits_null: bool = False

    def _marked(self, field_call: str) -> str:
        """``Annotated[<hint>, <Field(...)>, OmittedNotNull]``, with the middle optional.

        ``Field(...)`` is absent for a field that states no description, no alias and no
        constraint, and the marker then stands alone beside the hint -- which is what makes
        the ``Annotated`` appear on a field the layer would have rendered bare.
        """
        parts = [part for part in (field_call, OMITTED_NOT_NULL[1]) if part]
        return f"Annotated[{self.type_hint}, {', '.join(parts)}]"

    #: **Whether this field renders the marker at all**, which is the one predicate both
    #: writers below ask: a ``ClassVar`` has no presence question (the layer renders no
    #: ``| None`` for one either), and a field the layer renders un-annotated still takes
    #: the marker, which is why this does not read ``use_annotated`` alone.
    @property
    def _marks(self) -> bool:
        return self.omits_null and not self.is_class_var and self.use_annotated

    @property
    def annotated(self) -> str | None:
        """The layer's ``Annotated`` with the marker appended.

        **Not the only writer, which is why :meth:`_marked` is shared.**  The pinned
        generator has a second, faster path to the same text --
        ``_rendered_field_values_from_plan``, which the built-in templates reach through
        ``_RenderedDataModelField`` and which composes the subscript from its own render
        plan rather than reading this property.  Measured: with this override alone the
        rendered class body carried no marker at all.  Both are overridden, and both
        compose through one function, so the two paths cannot render two annotations.
        """
        if not self._marks:
            return super().annotated
        return self._marked(str(self))

    def _rendered_field_values_from_plan(self, plan: Any) -> tuple[str | None, str | None]:
        """The built-in template's path to the same two strings: the assignment and the
        ``Annotated``.  See :attr:`annotated` for why both exist."""
        assignment, annotated = super()._rendered_field_values_from_plan(plan)
        if not self._marks:
            return assignment, annotated
        return assignment, self._marked(plan.rendered or "")

    @property
    def imports(self) -> tuple[Any, ...]:
        """The layer's imports, plus the marker's own and ``Annotated``.

        **REPORTED BY THE FIELD AND NOT BY THE RENDERER, which is the latency this closes.**
        The import began life in :func:`klass`, gated on ``any(member.omits_null)`` -- and
        that is complete only while no OTHER caller of :func:`_field` can mark: both of
        them pass ``required=True`` today and say so in their docstrings, so nothing
        marked and nothing was missing.  Measured by perturbing the decision to mark a
        REQUIRED field: the alias and the root model emitted ``OmittedNotNull`` into an
        annotation their modules do not import, and every such module raised ``NameError:
        name 'OmittedNotNull' is not defined`` at import -- a crash rather than a verdict,
        which is what the structural guard calls a defect the comment hides.  A field that
        writes a symbol reports the symbol, so the gate is the one thing that decides it.

        ``Annotated`` is here for the same reason one level down: the layer reports it off
        ``_has_field_statement()`` -- whether there is a ``Field(...)`` to wrap -- so a
        field carrying the marker and nothing else names a symbol the module would not
        import.
        """
        reported = super().imports
        if not self._marks:
            return reported
        annotated = _TYPES.get_data_type_from_full_path("typing.Annotated", is_custom_type=False)
        wanted = (Import(from_=OMITTED_NOT_NULL[0], import_=OMITTED_NOT_NULL[1]),
                  *annotated.all_imports)
        return (*reported, *(imp for imp in wanted if imp not in reported))


def _field(decided: ir.Field) -> DataModelField:
    extras: dict[str, Any] = {}
    if decided.description:
        extras["description"] = decided.description
    constructed = _constructed_default(decided)
    # One ``json_schema_extra`` dict, three facts that can all be true of one field:
    # a ``format`` no type was selected for, D6's ``uniqueItems``, and the document's own
    # ``default`` where that default is CONSTRUCTED.  Assigning rather than merging
    # dropped whichever came second.
    #
    # **The ``default`` is here because ``default_factory`` does not render one.**
    # Measured on pydantic 2.13.5 and §5's own reason for the pairing: a field carrying
    # ``default_factory`` renders ``model_json_schema()`` with NO ``default`` at all,
    # where a plain default renders it -- so constructing the value through the
    # annotation would silently drop a keyword §8 grades the document by.  It rides THIS
    # channel and not a second one for the reason ``format`` and ``uniqueItems`` do: a
    # fact pydantic has no annotation for reaches the rendered schema here or nowhere.
    # The key is LAST so that every field that constructs nothing renders byte-identically.
    extra_schema = {
        **({"format": decided.type.format} if decided.type.format else {}),
        **({"uniqueItems": True} if decided.distinct else {}),
        **({"default": decided.default} if constructed is not None else {}),
    }
    if extra_schema:
        extras["json_schema_extra"] = extra_schema
    constraints = {
        KEY_COUNT.get(k, k): v
        for k, v in decided.type.facts.items()
        if k in ir.FACTS or k in KEY_COUNT
    }
    kwargs: dict[str, Any] = {}
    if constructed is not None:
        # **THE FACTORY IS THE FIELD'S ASSIGNED VALUE, and that is the whole of
        # ``adcp-client-python-82m.52``.**  It rode the model layer's ``default_factory``
        # EXTRA before, which put it inside ``Annotated[...]`` and made the template write
        # no ``= …`` line at all (``has_default_factory_in_field``).  Pydantic finds a
        # ``default_factory`` wherever it sits, so the field was optional at runtime --
        # and **PEP 681 does not look there.**  A consumer's checker reads
        # ``default``/``default_factory`` off the ASSIGNED VALUE alone, so 90 of the 1,459
        # public model exports told a consumer that a field the DOCUMENT gives a default
        # was required, and only a checker outside this package could see it (our own
        # ``[tool.mypy]`` excludes the emitted tree by name, and the source tree reads the
        # same with or without a marker).  Measured on pydantic 2.13.5 against mypy:
        # ``a: Annotated[int, Field(default_factory=…)]`` reports ``Missing named
        # argument``; ``a: Annotated[int, Field(description=…)] = Field(default_factory=…)``
        # is clean; both construct the same value and render the same
        # ``model_json_schema()``.  Pydantic MERGES the two ``FieldInfo``s -- the
        # annotation's keywords and the assignment's -- so ``description`` and
        # ``json_schema_extra`` keep arriving through the ``Annotated`` extra above.
        #
        # ``PythonCode`` is the model layer's own carrier for a default that is an
        # EXPRESSION rather than a literal (``represent_python_value`` renders it
        # unquoted), which is the same channel :func:`_bound_to_the_type` uses.
        #
        # **THE ASSIGNMENT IS NOW THE ONLY PLACE THE FACTORY LIVES, and the template
        # writes it only for a field that is not ``required``** -- so this arm depends on
        # §5's other rule, which is that a ``default`` on a property its object REQUIRES is
        # DROPPED (``codegen.lower.objects``, recorded in ``Emitted.drops`` and graded by
        # ``tests/test_inner_facts.py``'s two default clauses).  A required field therefore
        # reaches here with ``default is MISSING`` and constructs nothing, which is why no
        # ``use_default_with_required`` is asked for: the 98 constructed defaults in the
        # tree all carry ``| None``, i.e. all 98 are optional, and a required one would be
        # a drop the run reports rather than a line this writes.
        kwargs["default"] = PythonCode(f"{_field_symbol()}(default_factory={constructed.code})")
        kwargs["has_default"] = True
    elif decided.default is not MISSING:
        # ``has_default`` is what the template reads; the value alone is not
        # enough, because ``None`` is a legitimate default.
        kwargs["default"] = decided.default
        kwargs["has_default"] = True
    if decided.wire != decided.name:
        kwargs["alias"] = decided.wire
        kwargs["original_name"] = decided.wire
    # **The ``| None`` an optional field carries is the MODEL LAYER'S again**, and it is
    # not stated here, because the arrangement that took it away is gone.  Measured on the
    # pinned generator: ``DataModelFieldBase._type_hint_from_data_type`` returns the bare
    # hint as soon as ``has_default_factory`` is true -- which is
    # ``"default_factory" in extras`` and nothing else -- so while the factory rode the
    # ``Annotated`` extra, ``slots`` rendered ``list[SlotsItem]`` where every other
    # optional field rendered ``list[SlotsItem] | None``, the class REFUSED the ``None``
    # the document admits, and the schema read ``{"type": "array"}`` where it had read an
    # ``anyOf`` with ``null``.  The factory is now the ASSIGNED value (above), ``extras``
    # carries none, and the layer derives the union from ``required=False`` exactly as it
    # does for the 6,900 fields whose default is a literal.  One derivation, so a
    # constructed default and a literal one cannot come to render two shapes of optional.
    annotation = _data_type(decided.type)
    return _OptionalMember(
        name=decided.name,
        data_type=annotation,
        required=decided.required,
        constraints=Constraints(**constraints) if constraints else None,
        extras=extras,
        use_annotated=True,
        target_python_version=TARGET,
        # **Reading 1 at an OPTIONAL property: absence is spelled by OMISSION, and an
        # explicit ``null`` is refused where the document refuses one.**  The ``| None``
        # the layer derives from ``required=False`` below carries ABSENCE; pydantic reads
        # it as a type that also admits an explicit ``null``, so without this the model
        # half admitted a value the document refuses at 13,790 of the tree's 13,961
        # graded optional fields, in 1,819 classes, declared nowhere
        # (``adcp-client-python-4yhb``).
        #
        # **The BOUNDARY is the document's and it is asked of the decided TYPE**
        # (``ir.admits_null``): a property whose document DOES admit ``null`` --
        # ``type: [..., "null"]``, 171 fields of this tree -- keeps the plain ``| None``
        # and every ``null`` it ever took.  The reading is wrong only in the direction
        # that loses a refusal, which is that function's own argument.
        omits_null=not decided.required and not ir.admits_null(decided.type),
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


#: The parts of a clause that read as a TRIPLE and are therefore written in order.
#:
#: :class:`adcp.types._runtime.Match` is a clause and not a rule -- it has no ``errors``
#: -- and these three are a key, whether it is present, and the values it admits.  So
#: :func:`_argument`'s rule does not apply to them and all three are written positionally,
#: which is what the class-body line has always carried.
_CLAUSE_TRIPLE = ("key", "present", "allowed")


def _clause(clause: Match) -> str:
    """One ``if`` clause as a constructor expression: the triple, then what it adds.

    **Every field past the triple is written BY NAME and only where it differs from its
    own default**, which is what keeps §8 sentence 3b's complement from respelling every
    clause in the tree.  ``Match`` gained a ``forbidden`` value set so that a negated
    presence-and-value condition lowers as ONE clause, and that set is ``None`` at all but
    the clauses that take the complement -- so a positional read would have rewritten
    thousands of unchanged lines to say ``None`` and made the diff that carries the
    decision unreadable.

    Read off ``dataclasses.fields`` and not a second list, so a field added to the clause
    reports itself here exactly as :func:`_rule` already does for a rule's own.
    """
    args = [f"{getattr(clause, name)!r}" for name in _CLAUSE_TRIPLE]
    args += [
        f"{spec.name}={getattr(clause, spec.name)!r}"
        for spec in dataclasses.fields(clause)
        if spec.name not in _CLAUSE_TRIPLE and getattr(clause, spec.name) != spec.default
    ]
    return f"{type(clause).__name__}({', '.join(args)})"


def _rule(rule: Any) -> str:
    """One rule as a constructor expression, from its own dataclass fields.

    The kinds are ``adcp.types._runtime``'s frozen dataclasses, so the field names, their
    order and their defaults are declared there and read here -- §7's "one declaration of
    what a rule is".  A tuple of :func:`_clause`\\ s is written without the spaces a
    tuple's ``repr`` puts in, because it is one condition rather than a sequence of
    values.

    **``Any``, and the reason is §2's two places rather than laziness.**  This is called
    with a :class:`~adcp.types._runtime.Rule` (:attr:`ir.ClassDecl.rules`) AND with a
    :class:`~adcp.types._runtime.ValueRule` (:attr:`ir.TypeRef.validators`), and those
    two are SIBLINGS -- ``_runtime`` says so in as many words, "``Rule``'s sibling and
    NOT a narrower version of it" -- so neither annotates both.  What this function
    actually requires is orthogonal to both: that the kind be a frozen dataclass, which
    is ``_typeshed.DataclassInstance`` and intersects with neither protocol in a type
    system without intersections.  Annotating one of the two siblings states something
    false about the other and was reported as such the moment the shipped package
    entered the checker's scope (``Argument 1 to "_rule" has incompatible type
    "ValueRule"``); ``Any`` states the truth, which is that the read is STRUCTURAL.
    :func:`_named_by` below takes the same argument the same way.
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
    dropped for exactly that reason, and a ``Field(description=...)`` is the one slot an
    alias has for the sentence its document states.
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


def _member(member: ir.Member, values: str | None = None, at: int = 0) -> DataModelFieldBase:
    """One member as the model layer's field.

    ``EnumMemberValue`` is the generator's own carrier for a string member, and it is
    what renders the value as a Python literal with the escaping this module owns
    (quotes, backslashes, newlines, the null byte).  A bare ``str`` would reach the
    template as that text and would be read as a rendered default.

    ``use_inline_field_description`` is what puts the description in the class
    body: a single-line one becomes ``\"\"\"text\"\"\"`` under the member, and a
    multi-line one an indented triple-quoted block.

    **``values`` is §3a's module-level value list this member's VALUE is read out of**
    (:attr:`ir.EnumDecl.values`), and ``at`` is the member's own position in it.  The
    carrier is then ``PythonCode``, which is the generator's own carrier for a rendered
    EXPRESSION -- the same mechanism ``EnumMemberValue`` is for a literal, selected here
    rather than by concatenating text, so the escaping and the indexing go through one
    template and not two.

    The NAME is unchanged either way, which is the whole point: a class-body statement
    binding a name is what a consumer's type checker reads, and only the value moves.
    """
    return DataModelFieldBase(
        name=member.name,
        data_type=DataType(),
        default=(
            PythonCode(f"{values}[{at}]")
            if values is not None
            else EnumMemberValue(member.value)
            if isinstance(member.value, str)
            else member.value
        ),
        required=True,
        extras={"description": member.description} if member.description else {},
        use_inline_field_description=True,
    )


#: ``adcp.types._base.MemberAlias``, as the ``(module, name)`` pair this module holds an
#: import as -- :data:`TYPE_ADAPTER`'s and :data:`FIELD`'s own form, and for their reason:
#: the NAME is written into the class body and the IMPORT is written into the module
#: header, and two spellings of one symbol is how those come apart.
MEMBER_ALIAS = (ir.BASE_MODULE, "MemberAlias")


def _alias(member: ir.Member) -> DataModelFieldBase:
    """One member's SECOND spelling as the model layer's field.

    ``docs/plan/final-state.md`` reading 10: "the emitted enum carries the value-verbatim
    spelling as an alias member", "EMITTED in the class body, never installed at runtime,
    because reading 8 says the wheel is the artifact".  So it is a FIELD of the same list
    the canonical member is in, rendered through the same ``{{ field.name }} = {{
    field.default }}`` line by the same template -- not a string appended to the rendering,
    which D9 forbids, and not a slot the template has not got (``Enum.jinja2`` has no
    ``class_body_lines``, which is why an ``__adcp_schema__`` cannot reach an enum's body
    at all; see :class:`ir.EnumDecl`).

    **The VALUE is ``MemberAlias(<canonical>)`` and not the member's own value**, which is
    the whole of why ``__members__`` does not move: a plain ``transient = 'transient'``
    beside ``TRANSIENT = 'transient'`` is python's own enum aliasing and puts the second
    name IN ``__members__`` -- 6 entries where the document states 3, and
    ``tests/test_enum.py``'s ``_members`` then reads a lower-case member off a class whose
    every member is asserted upper-case.  ``enum._EnumDict`` passes a DESCRIPTOR over
    without making it a member, so this binds a NAME and nothing else.

    ``PythonCode`` is the carrier because the default is an EXPRESSION, which is the same
    selection :func:`_member` makes for ``<values>[<i>]``: the alternative is to write the
    call as text and have two escapings in one class body.  The argument is the canonical
    member NAME -- an identifier this module derived, never a document's value -- so
    ``repr`` of it is a python literal by construction.

    No description, and that is not a loss: a ``enumDescriptions`` entry describes a VALUE
    and the value's own member carries it, so a second docstring under the second spelling
    would be the one fact this compiler restated.
    """
    return DataModelFieldBase(
        name=member.alias,
        data_type=DataType(),
        default=PythonCode(f"{MEMBER_ALIAS[1]}({member.name!r})"),
        required=True,
    )


#: The Python type word for each kind's MEMBER VALUE, for the annotation a value list
#: carries.  ``lower.enum.BASES`` is the same mapping read from the other side.
_VALUE_TYPES = {"string": "str", "integer": "int"}


def values(decl: ir.ValuesDecl) -> Rendered:
    """§3a's module-level VALUE LIST: ``<name>: tuple[<base>, ...] = (…)``.

    "The **VALUE LIST** is a module-level constant in the catalogue layer, written once
    per distinct member set; the **NAMED TYPE** is constructed from it at each position
    that needs one, keeping the name §4 derives and keeping the types distinct."

    The VALUES alone, which is :class:`ir.ValuesDecl`'s own reason: the member NAME is a
    class-body statement at each type over the list, so the list is the value list the
    reading is worded on and carries nothing a type decides.

    ``repr`` is the escaping, and it is the language's own rather than this module's: the
    repr of a ``str`` or an ``int`` is by definition a Python literal for that value, so
    a member containing a quote, a backslash or a newline round-trips without this
    function knowing which characters those are.  The class body reaches the same
    guarantee through the model layer's ``EnumMemberValue`` (:func:`_member`); there is no
    second escaping rule here, only a second expression of one.
    """
    held = "\n".join(f"    {value!r}," for value in decl.values)
    return Rendered(
        text=f"{decl.name}: tuple[{_VALUE_TYPES[decl.kind]}, ...] = (\n{held}\n)"
    )


def enum(decl: ir.EnumDecl) -> Rendered:
    """The Python for one decided enumeration, and the imports it needs.

    The members' NAMES are rendered verbatim (``{{ field.name }}``): this module names
    nothing here, which is why ``codegen.lower.enum`` owns the naming and why the
    injectivity check binds to its function.

    **ONE FORM, and :attr:`ir.EnumDecl.values` moves the member's VALUE and not its
    name.**  §3a's "the NAMED TYPE is constructed from it at each position" is satisfied
    by a class statement whose members are read out of the one list, and the functional
    ``StrEnum('<Name>', …)`` call -- which §3a's correction of 2026-11-02 named as one way
    to do it -- is not usable here: a consumer's type checker cannot see a functionally
    built enum's members (``error: "type[CatalogAction]" has no attribute "CREATED"
    [attr-defined]``, measured against a wheel), which is a regression in reading 7.  So
    the two docstring slots the correction was willing to give up are kept as well, and
    nothing about this function differs between a value list of its own and a shared one.

    **A MEMBER WITH A SECOND SPELLING RENDERS TWO CLASS-BODY LINES, THE ALIAS BESIDE THE
    CANONICAL ONE** (:func:`_alias`, reading 10).  Beside and not in a trailing block,
    because the two lines are two names for ONE member and a reader of the module meets
    them together; the import is reported exactly where one was written, so a module whose
    every member spelling is refused imports nothing it does not use.
    """
    fields: list[DataModelFieldBase] = []
    for at, member in enumerate(decl.members):
        fields.append(_member(member, decl.values, at))
        if member.alias is not None:
            fields.append(_alias(member))
    model = _ENUM_BASES[decl.kind](
        reference=Reference(path=f"#/{decl.name}", original_name=decl.name, name=decl.name),
        fields=fields,
        description=decl.description or None,
    )
    out = Rendered(text=model.render().rstrip("\n"))
    _reported(model.imports, out.imports)
    if any(member.alias is not None for member in decl.members):
        out.imports.add(MEMBER_ALIAS)
    return out


def klass(decl: ir.ClassDecl, declared: Sequence[Approximation] = ()) -> Rendered:
    """The Python for one decided class, and the imports it needs.

    ``declared`` is §7's approximation declaration for this class's own node, already
    narrowed by :func:`declared_at`.  Empty at §14 step 8 and for every faithful class
    after it, which is why it defaults: a caller with nothing to declare says nothing.

    **A ``ref`` of ``None`` writes no ``__adcp_schema__`` line and no ``SchemaRef``
    import**, which is the renderer's whole knowledge of a class that names no document
    (``codegen/lower/envelope.py``).  Gate 3's note above already says what the absence
    means and relies on it: "a class with no ``__adcp_schema__`` has no schema, so every
    grade of it fails rather than quietly passing" -- and §9 of the architecture document
    pairs a class with the node its reference names, so a class with none is not a pair.
    Written as the absence of a line rather than as a ``None`` reference, because a
    ``SchemaRef`` naming no document would be a reference the schema half would then try
    to read.
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
    body = [] if decl.ref is None else [f"__adcp_schema__: ClassVar[SchemaRef] = {decl.ref!r}"]
    extra_field = None
    if decl.extras is not None:
        # ``__pydantic_extra__`` is a dunder and not a field: declared as one it
        # would be a model field named ``__pydantic_extra__``, which pydantic reads
        # as the extras store rather than as a property, so it goes through the same
        # channel the schema reference does.  The ANNOTATION is still this module's
        # -- read off a ``DataModelField`` like every other type hint here -- so a
        # mapping's rendering and an extras store's cannot come to be two spellings of
        # one decision.  Only the ``name: hint`` line is ours.
        #
        # **AND IT CARRIES THE ``init=False`` SPECIFIER THE BASE CARRIES, which is
        # ``adcp-client-python-82m.53``.**  The sentence above is right about pydantic and
        # was silent about PEP 681.  ``BaseModel`` declares this same name as
        # ``NoInitField(init=False)``, a member of pydantic's own
        # ``dataclass_transform(field_specifiers=…)`` tuple, so a checker leaves it out of
        # the synthesised ``__init__`` -- and **a subclass re-declaring it with no assigned
        # value PUTS IT BACK**, as a required keyword-only parameter naming a dunder
        # pydantic's ``__init__`` must never be handed.  Measured: the 5 public exports
        # that declare a typed store had NO correct consumer call at all -- naming the
        # dunder is wrong and omitting it was reported.  ``Field(init=False)`` is the
        # PUBLIC spelling of the same specifier (``pydantic.Field`` is the first member of
        # that tuple), so the emitted text imports nothing private.
        #
        # The assignment is removed again at class creation by
        # ``AdCPBaseModel.__pydantic_init_subclass__``, which is pydantic's own trick for
        # the same three dunders -- its metaclass pops them out of ``BaseModel``'s
        # namespace -- and is what keeps the runtime IDENTICAL rather than nearly so: left
        # in place, the class attribute shadows ``BaseModel``'s slot descriptor and the
        # extras store lands in the instance ``__dict__`` beside the field values instead
        # of in its slot.  Every public read (``model_dump``, ``model_dump_json``,
        # ``repr``, ``==``, ``model_fields_set``, the JSON schema, the refusal of a
        # wrong-typed extra) is the same either way; ``instance.__dict__`` is not -- see
        # that method for the measurement and for why it is taken off rather than left.
        extra_field = _field(
            ir.Field(
                name="__pydantic_extra__",
                wire="__pydantic_extra__",
                type=decl.extras,
                required=True,
            )
        )
        body.append(f"__pydantic_extra__: {extra_field.type_hint} = {_field_symbol()}(init=False)")
    rule_lines, rule_imports = _rule_lines(decl.rules)
    approximation_lines = _approximation_lines(declared)
    class_body = (*body, *_union_base_lines(decl), *rule_lines, *approximation_lines)
    for line in class_body:
        model._append_internal_template_data("class_body_lines", line)  # the generator's own channel; see the module docstring
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
        #
        # **The split is over every character a Python NAME cannot contain, and that was
        # a bug fixed at ``adcp-client-python-10l.21``.**  It listed four separators by
        # hand -- ``[``, ``]``, ``,`` and ``|`` -- which is exactly the set a mapping of
        # bare types needs and nothing more, so a CALL inside the annotation hid every
        # name in it: §2's value rules render as
        # ``Annotated[X, Field(json_schema_extra={…}), AfterValidator(Distinct())]``, and
        # ``AfterValidator(Distinct())`` tokenised as one word, so none of ``Field``,
        # ``AfterValidator`` or ``Distinct`` was in ``used`` and all three imports were
        # filtered out of a line that names them.  Measured on
        # ``core/postal-area-support.json``, whose typed extras store holds a
        # ``uniqueItems`` array: the module raised ``PydanticUserError: not fully
        # defined; you should define AfterValidator`` at import, and 11 pairs reported
        # ``harness_error``.  A character class keeps the filter's safe direction -- it
        # can only ADMIT more names, and an unused import is never a ``NameError`` --
        # while being a property of Python's identifier grammar rather than of today's
        # annotation shape, so the next carrier added to an annotation cannot re-open it.
        used = set(re.split(r"[^\w.]+", extra_field.type_hint))
        for imp in extra_field.imports:
            if imp.from_ and imp.import_ and imp.import_ in used:
                out.imports.add((imp.from_, imp.import_))
        # ``Field`` is named by the ``init=False`` SPECIFIER this module writes beside the
        # hint, which is not part of the hint -- so the filter above cannot report it and
        # the model layer does not either (the store is not one of the model's fields).
        # Stated unconditionally rather than off the text for the reason the filter is
        # filtered: a class whose only ``Field(`` is this one would otherwise raise
        # ``NameError`` at import, and the one class in that state today
        # (``core/canonical-media-buy-features.json``) happens to carry a described field
        # as well, which is exactly the shape of latency the ``ConfigDict`` rule below
        # records being bitten by.
        out.imports.add(FIELD)
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
    # ``TypeAdapter`` follows the TEXT, which is the rule one line up and for its reason.
    # The name is named by a CONSTRUCTED default's factory expression and by nothing else,
    # and that expression is a field's rather than a class's -- so it cannot be decided
    # from ``decl``, and the model layer does not report it: ``_constructed_default``
    # resolves the symbol through the model layer to get its spelling, but the import
    # rides a field's ``extras`` and a ``DataModelField`` collects imports off its
    # ``data_type`` alone.  A class with no constructed default therefore adds nothing,
    # which is what keeps every module the tree already carried byte-identical.
    if f"{TYPE_ADAPTER[1]}(" in out.text:
        out.imports.add(TYPE_ADAPTER)
    # ``ClassVar`` and ``SchemaRef`` are named by the class-body lines and by nothing
    # else, so a class with no body line needs neither.  Read off the LINES this call
    # produced rather than off ``decl``, which is the ``ConfigDict`` filter's own rule
    # one line up: the import follows the text.  Every class the tree carried before
    # ``ClassDecl.ref`` could be ``None`` writes at least the ``__adcp_schema__`` line,
    # so this is byte-neutral over that population and the one class it is about is the
    # envelope base, whose body is its fields alone.
    if any("ClassVar" in line for line in class_body):
        out.imports.add(("typing", "ClassVar"))
    if decl.ref is not None:
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

    **There was no producer in the walk at §14 step 8**, which was that step's own exit
    condition; the three rows that lower to one were step 9's and step 9 has landed, so
    a handler writes them today.  ``tests/test_approximation.py`` also renders a
    hand-built declaration, which is what keeps the IR-to-text path graded independently
    of which handler produced the declaration.
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
        # ``model_json_schema()`` then stated no ``uniqueItems`` at all -- the fact §8
        # needs RENDERED, absent from a root model whose rule tuple enforces it.
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
    decl: ir.Declaration,
    approximations: Sequence[Approximation] = (),
    sections: Collection[str] = (),
) -> Rendered:
    """One declaration's text and imports: the ONE dispatch over ``codegen.ir``.

    ``approximations`` is the MODULE's whole tuple and the three writers that carry one
    narrow it themselves, through :func:`declared_at` at their own ``ref``.  Narrowed here
    rather than by the caller, because which node a declaration's ``ref`` names is a fact
    about the declaration and this is the one dispatch that holds every kind of it.

    ``sections`` rides with it because :func:`declared_at` needs both to answer: the
    containment is a fact about two pointers and the SECTION BOUNDARY is a fact about the
    document, and that function carries why.

    An ``EnumDecl``, an ``AliasDecl`` and a ``UnionInstall`` carry none and are handed
    none: a nested enumeration has no ``class_body_lines`` slot at all (``EnumDecl``'s own
    docstring), a nested alias binds no ``__adcp_schema__`` and is no pair, and a union
    install declares no name.  Each is contained in a node that DOES carry one, by
    :func:`declared_at`'s containment rule, so nothing is lost.
    """
    if isinstance(decl, ir.ClassDecl):
        # A class with no ``ref`` names no document, so there is no node for a
        # declaration to be AT: :func:`declared_at` compares a document and a pointer and
        # has neither to compare.  Nothing is lost, because every approximation is about
        # a fact some document states and such a class states no document's facts.
        return klass(
            decl, () if decl.ref is None else declared_at(approximations, decl.ref, sections)
        )
    if isinstance(decl, ir.EnumDecl):
        return enum(decl)
    if isinstance(decl, ir.ValuesDecl):
        return values(decl)
    if isinstance(decl, ir.AliasDecl):
        return alias(decl)
    if isinstance(decl, ir.RootBinding):
        return root_binding(decl, declared_at(approximations, decl.ref, sections))
    if isinstance(decl, ir.RootModelDecl):
        return root_model(decl, declared_at(approximations, decl.ref, sections))
    if isinstance(decl, ir.UnionInstall):
        return union_install(decl)
    raise TypeError(f"no rendering for {type(decl).__name__}")


# --------------------------------------------------------------------------- #
# §7: the approximation declaration, written into the emitted module
# --------------------------------------------------------------------------- #
#: The annotation the class-body line carries, so the declaration is a ``ClassVar`` like
#: ``__adcp_schema__`` beside it rather than a model field pydantic would try to validate.
APPROXIMATIONS_HINT = f"ClassVar[tuple[{Approximation.__name__}, ...]]"


def declared_at(
    approximations: Sequence[Approximation],
    ref: SchemaRef,
    sections: Collection[str] = (),
) -> tuple[Approximation, ...]:
    """Every approximation at or INSIDE the node ``ref`` names, in document order.

    **Containment and not the nearest declaration**, and the reason is the pairing §9
    grades over.  A pair is graded over its own node and the whole subtree under it -- a
    property's facts, an ``items``, a ``propertyNames`` -- and the obligation that proves
    a declaration walks the declaration's pointer from the pair's OWN node
    (``harness.check_widening``), so a fact at ``#/properties/x/maxLength`` is reached
    from the root class's node as well as from the nested class's own.  A declaration
    carried only by the nearest enclosing class would be put to a draw at one of those
    pairs and be unknown to the other, for a widening the design declared.  Carrying it
    on every declaration whose node contains it costs a repeated line in one module and
    makes both pairs read the same answer.

    Over-coverage in the other direction is harmless and measured: a root union's BASE is
    at ``#`` and so contains ``#/oneOf/0/...``, so the base's own tuple carries a
    branch's declaration as well as the branch pair's does.  Both pairs then put that
    declaration to the same draw -- a combinator hop is a same-instance step of the
    obligation's walk, so each reaches the same node -- and the repeated line buys a
    second proof of one fact rather than a claim about anything else.

    **EXCEPT ACROSS A SECTION BOUNDARY, WHERE CONTAINMENT IS NOT REACHABILITY AND THE
    OVER-COVERAGE IS A RED.**  A ``definitions`` / ``$defs`` entry is contained by the
    root's pointer and describes NO instance location the root's own class can reach: an
    entry is reached only by a ``$ref``, which is another class's node, and draft-07 gives
    a section no assertion behaviour at all.  §8 already reads this from the other side --
    ``harness.locations`` takes no frontier item inside an entry because "it has no
    instance location, which is §8's own reading of why such a declaration belongs to the
    entry's own pair" -- and the obligation's walk refuses the pointer outright, reporting
    ``unproved_widening`` with "the pointer describes no instance location, so no drawn
    value can be placed at it".  So the declaration was carried to a pair that cannot put
    it to a draw, and the SAME declaration is carried to the entry's own pair, which
    proves it: one fact, counted once as a pass and once as a failure.

    Measured over the graded population at the row that wrote this: 91 declarations are put
    to the obligation, 3 of them sit inside a section entry, and all 3 are the whole of what
    the obligation's walk cannot reach -- ``core/bidding-policy-capability.json#`` carrying
    ``#/definitions/policy_profile/allOf/{0,1}/if`` and
    ``core/targeting-overlay-support.json#`` carrying
    ``#/definitions/daypartSupport/anyOf/1/allOf/0/if``, every one of them also carried and
    proved at the entry's own pair.

    ``sections`` is :attr:`codegen.ir.Module.sections`, and the predicate is
    ``bundle.reaches`` -- the same one ``bundle.undecidable_references`` asks of a
    reference, over the same boundary, read here rather than restated: "validation and the
    lowering both start at a declared pointer and descend by assertion keywords, WHICH
    NEVER CROSS A SECTION BOUNDARY."  ``declared`` is this one pointer, because the
    question here is about THIS pair and not about the innermost one; an entry AT ``ref``
    is not between them, so a class declared at the entry keeps every declaration inside
    it.  **Empty ``sections`` is the containment this function always had**, which is the
    fail-safe direction: a module built outside a run carries a declaration wherever
    containment reaches it rather than dropping one on a census it does not have.

    The prefix test is on ONE spelling of a pointer -- ``SchemaRef``'s, which
    ``compiler.schema_ref`` is the sole producer of -- and the separator is part of the
    prefix, so ``#/properties/x`` does not contain ``#/properties/xy``.
    """
    prefix = ref.pointer if ref.pointer.endswith("/") else ref.pointer + "/"
    return tuple(
        a
        for a in approximations
        if a.document == ref.document
        and (a.pointer == ref.pointer or a.pointer.startswith(prefix))
        and bundle.reaches(
            a.pointer.lstrip("#"), entries=sections, declared={ref.pointer.lstrip("#")}
        )
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
    """stdlib, the third-party library, the artifact's own package, then a sibling
    module of this tree (always relative, so always ``.``-prefixed).

    **Rank 2 is derived from the artifact package's own prefix** and was three names
    (``ir.BASE_MODULE``, ``ir.RUNTIME_MODULE``, ``constraint_names.MODULE``).  Every
    absolute import an emitted module can make of its own package is under that prefix --
    a sibling module is RELATIVE and takes rank 3 -- so the prefix says what the list
    said and a fourth such module (``lower/envelope.py``'s base) needs no entry.
    Byte-neutral over the committed tree, which is what the list's three names were.
    """
    if module.startswith("."):
        return 3
    if module.startswith(ARTIFACT):
        return 2
    return 1 if module == "pydantic" else 0


#: The width an import statement is written to before it is WRAPPED, which is
#: ``[tool.ruff] line-length`` and is the one figure this module shares with the linter.
#:
#: It is restated here rather than read, because the output is ``f(bundle, document set,
#: this package)`` (P7) and a configuration file is none of those -- and it needs no
#: pin of its own, because the enforcement already exists in both directions: lower the
#: linter's width and it reports the statements this one leaves long, raise it and it
#: reports the ones this one wrapped.  Either way ``I001`` names the file.
LINE_LENGTH = 120

#: The indent of a wrapped import's names, which is ``isort``'s vertical-hanging-indent.
IMPORT_INDENT = "    "

#: A run of digits, which both sort keys below split a name on.
_DIGITS = re.compile(r"(\d+)")


def _natural(text: str) -> tuple[tuple[int, int, str], ...]:
    """``natord``'s ordering, which is the one both ruff rules sort names by: a run of
    DIGITS compares as a number and not as characters.

    ``StrMaxLen64`` before ``StrMaxLen100`` and ``Branch9`` before ``Branch10``, where a
    plain string sort gives both the other way round.  A digit chunk ranks before a text
    chunk, which is what ``natord`` does by character code as well: every character a
    Python identifier can carry outside a digit (``A``-``Z``, ``a``-``z``, ``_``) is
    above ``9``.
    """
    return tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in _DIGITS.split(text)
        if part
    )


def _is_constant(name: str) -> bool:
    """``isort``'s CONSTANT: longer than one character and cased all upper.

    The length clause is the rule's own and is load-bearing here -- ``T`` is a one-letter
    class and not a constant -- and the cased clause is what keeps ``___`` out.
    """
    return len(name) > 1 and name.upper() == name and name.lower() != name


def _member_key(name: str) -> tuple[int, tuple[tuple[int, int, str], ...]]:
    """``isort``'s member order within one ``from`` statement: ``order-by-type`` puts
    CONSTANTs first, then CLASSes, then everything else, and ``case-sensitive = false``
    compares the rest case-blind.

    So ``APPROXIMATIONS, Approximation, SchemaRef`` and ``AdcpMajorVersion, AdcpVersion,
    AdCPVersionEnvelope`` -- the second of which a plain sort gives in the other order,
    because ``C`` sorts before ``c``.
    """
    return (0 if _is_constant(name) else 1 if name[:1].isupper() else 2, _natural(name.lower()))


def _export_key(name: str) -> tuple[int, tuple[tuple[int, int, str], ...]]:
    """``RUF022``'s ``__all__`` order, which is NOT :func:`_member_key`: two groups
    rather than three and case-SENSITIVE within them.

    Measured against the rule rather than assumed from the family: given one list of
    twenty-one names the two rules disagree about four positions, because ``RUF022``
    compares ``_VALUES_X`` after ``MISSING`` where ``isort`` compares it before
    ``A2UI_X``.  One key for both would leave one of the two rules reporting.
    """
    return (0 if _is_constant(name) else 1, _natural(name))


def _import_statement(module: str, names: Sequence[str]) -> list[str]:
    """One ``from`` statement, on one line or wrapped at :data:`LINE_LENGTH`.

    The wrapped form is ``isort``'s vertical hanging indent WITH the trailing comma, and
    the comma is not decoration: ``split-on-trailing-comma`` reads it as the instruction
    to keep the statement split, so the form without it is one the sorter would rejoin.
    A statement whose single name does not fit either is still wrapped, which is what the
    sorter does -- there is nothing shorter to write.
    """
    one = f"from {module} import {', '.join(names)}"
    if len(one) <= LINE_LENGTH:
        return [one]
    return [f"from {module} import (", *(f"{IMPORT_INDENT}{name}," for name in names), ")"]


def _module_statements(
    module: str, names: Collection[str], reexported: Mapping[str, str]
) -> list[str]:
    """One module's statements: the plain names in ONE statement, then each re-export in
    its own.

    ``combine-as-imports`` is false -- the default, and this project does not set it --
    so ``X as X`` cannot share a statement with anything: ``from m import A, B as B``
    is rewritten to two statements by the sorter, and the plain one comes first.  That is
    the whole reason this is not one join.

    ``reexported`` is symbol -> the WORD the statement binds it to, which is the symbol
    itself for every re-export but reading 6's inner clause (``ir.Module.published``).  A
    MAPPING and not a set because the two halves of ``X as Y`` are two names and a set
    could only carry one of them; the identity case is simply the entry where they agree,
    so there is no second spelling of ``X as X`` to keep in step.
    """
    plain = sorted(set(names) - set(reexported), key=_member_key)
    out = _import_statement(module, plain) if plain else []
    #: Sorted by the SYMBOL, which is the member a sorter reads: ``isort`` orders the
    #: statements of one module by the imported name and not by the ``as`` clause.
    for name in sorted(reexported, key=_member_key):
        out += _import_statement(module, [f"{name} as {reexported[name]}"])
    return out


def _import_block(
    imports: Collection[tuple[str, str]],
    reexports: Collection[tuple[str, str] | tuple[str, str, str]] = (),
) -> list[str]:
    """The import statements, grouped by :func:`_import_rank` and sorted within a rank.

    Sorted the way the SORTER sorts -- :func:`_natural` over the module name, case-blind,
    and :func:`_member_key` over the names within a statement -- rather than by
    ``sorted()``, which agrees with it on most of this tree and not on all of it.

    A re-export is ``(module, symbol)`` or ``(module, symbol, word)``, and the pair is the
    word-equals-symbol case written short: every caller but the domain surface re-exports
    under the name it imported, and reading 6's inner clause is the one that does not.
    """
    groups: list[list[str]] = [[], [], [], []]
    by_module: dict[str, set[str]] = {}
    held: dict[str, dict[str, str]] = {}
    for module, name in imports:
        by_module.setdefault(module, set()).add(name)
    for reexport in reexports:
        module, name, word = (*reexport, reexport[1])[:3]
        by_module.setdefault(module, set()).add(name)
        held.setdefault(module, {})[name] = word
    for module in sorted(by_module, key=lambda m: _natural(m.lower())):
        groups[_import_rank(module)] += _module_statements(
            module, by_module[module], held.get(module, {})
        )
    out: list[str] = []
    for group in groups:
        if group:
            out += [*group, ""]
    return out


def _code_names(body: str) -> set[str]:
    """Every name the body's CODE names, which is what decides whether an import the
    walk reported is one the text uses.

    **Read off the parse and not off the characters.**  A word search over the text
    keeps four imports this tree does not use, because a schema ``description`` carried
    verbatim mentions the class by name in prose (``Each item is a
    ProductFormatDeclaration ...``, three documents) and a declared ``Approximation``'s
    ``fact`` is the document's own subtree, which carries every ``title`` in it
    (``core/async-response-data.json``, two).  Both are STRING literals and neither is a
    use, so ``F401`` still reported all four after a word filter had passed them.

    **Two kinds of string ARE a use and both are read**, which is what keeps the filter
    on the admitting side of the two errors -- an unused import is a finding where a
    missing one is a ``NameError``:

    * an entry of ``__all__``, which is a RE-EXPORT.  That is ``F401``'s own reading of
      a name in ``__all__``, so taking it here is agreeing with the rule rather than
      guessing at it.
    * an identifier inside an ANNOTATION, which is a forward reference.  Today's tree
      holds none (``UP037`` reads 0 over it, because every module has ``from __future__
      import annotations`` and nothing quotes a hint) -- it is read because an annotation
      is the one position where a string is a NAME, and a filter that dropped one would
      produce a module that does not import.

    An identifier-valued string anywhere ELSE is DATA and is not read, which is the
    distinction the two ``Approximation`` facts above turn on: theirs carries ``{'title':
    'ControlMediaBuyResponse', ...}`` -- the class name, in a dict, as a value.
    """
    tree = ast.parse(body)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    for node in ast.walk(tree):
        annotation = getattr(node, "annotation", None)
        if annotation is not None:
            names |= _identifier_strings(annotation)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            names |= _identifier_strings(node.value)
    return names


def _identifier_strings(node: ast.AST) -> set[str]:
    """Every string under ``node`` that is a Python identifier on its own."""
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and child.value.isidentifier()
    }


def _import_section(
    imports: Collection[tuple[str, str]],
    body: str,
    reexports: Collection[tuple[str, str] | tuple[str, str, str]] = (),
) -> list[str]:
    """``from __future__ import annotations``, the import block, and the blank lines
    ``isort`` puts between that block and what follows.

    **An import the body does not NAME is dropped here**, which is the one place that
    reading can be taken: the walk reports the import for a type it decided and the
    renderer may write a narrower spelling of it, and a reported name that merely
    appears as a SUBSTRING of a class the module does declare was being kept by the
    emitter's own union -- ``PostalCountrySystem`` kept by ``PostalCountrySystemUS``,
    nineteen times over the tree.  :func:`_code_names` is the test and the one place the
    reading is taken; this is the ``ConfigDict`` filter one line up generalised, in the
    direction that filter already has.

    ``reexports`` are exempt and are written ``X as X``: they are named by a CONSUMER and
    not by this module, so a usage test would delete exactly the names the package
    promises -- ``constraints.HttpUrl``, which 133 emitted modules import, and every
    name on a domain surface.  ``X as X`` is also what makes the promise readable to a
    type checker (PEP 484), which is why ``PLC0414`` is declined in the configuration.
    """
    used = _code_names(body)
    named = [(module, name) for module, name in imports if name in used]
    # ``X as X`` and ``X as Y`` are both exempt from the usage filter above, and for the
    # same reason: the name is promised to a CONSUMER and is not named by this module.
    block = _import_block(named, reexports)
    after = ["", ""] if body.lstrip("\n").startswith(("class ", "def ", "@")) else [""]
    return ["from __future__ import annotations", *(["", *block[:-1]] if block else []), *after]


def blocks(
    declarations: Sequence[ir.Declaration],
    approximations: Sequence[Approximation] = (),
    sections: Collection[str] = (),
) -> list[Rendered]:
    """Every declaration rendered, in declaration order."""
    return [declaration(decl, approximations, sections) for decl in declarations]


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
    the type is named directly.  The export SET is the walk's (``emit.exported``),
    because which names another module may ask for is a decision about the bundle and
    not about text -- and its ORDER is this module's, because an order is layout (D8).
    :func:`_export_key` is the one a sorter would write, which is what keeps every
    module of the tree from reporting ``RUF022``.
    """
    rendered = blocks(mod.declarations, mod.approximations, mod.sections)
    imports = set(mod.imports)
    for one in rendered:
        imports |= one.imports
    classes = "\n\n\n".join(one.text for one in rendered)
    names = ", ".join(f'"{n}"' for n in sorted(exports, key=_export_key))
    #: **The two blank lines are BETWEEN the last class and ``__all__``, so a module with
    #: no class has nothing for them to be between.**  §3a's repeated-DOCUMENT layer is
    #: what produces one (``emit.lower_document``): a non-home member of a repeated
    #: document declares nothing and RE-EXPORTS the home's class, so its whole body is the
    #: import block and the ``__all__`` -- and the layout rule is the same one it always
    #: was, which is why this is an empty ``rendered`` and not a second layout.
    body = "\n".join([*([classes, "", ""] if rendered else []), f"__all__ = [{names}]", ""])
    return "\n".join(
        [
            f"# Generated by codegen.emit from {mod.document}. Do not edit.",
            *_import_section(imports, body),
            body,
        ]
    )


# --------------------------------------------------------------------------- #
# the envelope base module, which belongs to no document either
# --------------------------------------------------------------------------- #
#: The same first line every emitted module carries, less the document name: the two
#: outputs written BESIDE the tree -- the constraints module and the envelope bases --
#: are the ones that belong to no document, so there is no path for the header to name.
#:
#: §3a's CATALOGUE module takes it too, and that is the point of the line rather than a
#: reuse of it: "**A pseudo-document path is refused**: it names a file the bundle does
#: not contain, and every reader that resolves a record from a key would then be lying
#: about where the schema came from."  A header naming a document would be the same lie
#: one line further in.
BESIDE_HEADER = "# Generated by codegen.emit. Do not edit."

VOCABULARIES_DOCSTRING = '''"""Value lists the bundle states under more than one name, written once.

GENERATED by ``codegen.emit``; see ``docs/plan/architecture.md`` §3a, which decides both
that these lists are written once and that the types over them stay distinct.  Edit
nothing -- the tree is ``f(bundle, emitter, pinned compiler)`` and a hand edit here is a
fact no input states.

**This module belongs to NO document**, which is why it carries no header path, no
``__adcp_schema__`` and no ``strict_validate``: §3a's catalogue is a reading of the
bundle, and a value list the bundle states at six positions in four documents has no one
document to be reached through.  It sits in the narrowest namespace that contains every
position referencing it -- a domain's where every reference is within one domain, the
shared one otherwise.

**Nothing here is a type.**  Each name is a list of VALUES, and the enumerations that
read their members out of it are declared in the modules of the documents that state
them -- as class statements, each keeping the name §4 derives for it: "a conflicting
title is not a question about which name wins ... where the bundle states two concepts,
both names are right and merging types one subject with the other's name."
"""'''


def vocabularies_module(declarations: Sequence[ir.ValuesDecl]) -> str:
    """The text of one namespace's ``_vocabularies.py``: §3a's value lists, written once.

    A module of CONSTANTS, so there is no ``__all__``: every name here is private by its
    own leading underscore and is reached by the modules that build a type from it, never
    by a consumer.  §1's export set is about types a consumer writes, and a value list is
    not one.

    The header is :data:`BESIDE_HEADER` for the reason that constant now carries: this
    module has no document, and naming one would be the pseudo-document path §3a refuses.
    """
    rendered = [values(decl) for decl in declarations]
    imports: set[tuple[str, str]] = set()
    for one in rendered:
        imports |= one.imports
    body = "\n".join(["\n\n\n".join(one.text for one in rendered), ""])
    return "\n".join(
        [
            BESIDE_HEADER,
            VOCABULARIES_DOCSTRING,
            "",
            *_import_section(imports, body),
            body,
        ]
    )

ENVELOPES_DOCSTRING = '''"""Consumer-facing bases for a repeated envelope the bundle spells more than one way.

GENERATED by ``codegen.emit``; see ``codegen/lower/envelope.py``, which derives both the
family and this shape from the bundle.  Edit neither -- the tree is
``f(bundle, emitter, pinned compiler)`` and a hand edit here is a fact no input states.

A type here belongs to NO document, which is why it lives beside ``adcp.types.constraints``
rather than in a document's own module: every other emitted type is reachable through the
module of the document it came from, and this one has no document to be reached through.
It carries no ``__adcp_schema__``, nothing grades it, and ``strict_validate`` does not
resolve on it.

**It is a type to program against and not an authority on acceptance.**  The documents of
the family do not agree about what they accept, so no single schema reference could be
right for all of them; the concrete class for a document keeps its own reference, its own
``strict_validate`` and its own constraints, and that class is what decides whether a
payload is valid. A base here is what those classes have in common and nothing more.
"""'''


def envelopes_module(
    declarations: Sequence[ir.ClassDecl],
    imports: Collection[tuple[str, ...]],
    prose: str = "",
) -> str:
    """The text of ``adcp/types/envelopes.py``, for the bases a bundle's families earn.

    A module of CLASSES with an ``__all__``, so the layout is :func:`module`'s and the
    class text is :func:`klass`'s -- one rendering of a class, whether its ``ref`` names a
    document or is ``None``.  What is this function's is the module around them, and the
    one thing it does not share with :func:`module` is the header: that one names the
    document a module was emitted from and these belong to none.

    ``imports`` are the annotations' own, decided by ``lower/envelope.py`` from the
    documents the family reaches, and they are ABSOLUTE: this module sits beside
    ``_schemas`` rather than inside it, so a relative import would not resolve.

    **A TRIPLE IS A RE-EXPORT AND IS PROMISED, NOT ONLY IMPORTED**, which is the one
    reading this function takes of its own argument.  ``lower/message.UPSTREAM`` re-exports
    upstream's two task-message markers rather than declaring subclasses of them, so the
    name here IS upstream's object; a triple is the form :func:`_import_block` already
    writes, routing it through ``reexports`` is what exempts it from
    :func:`_import_section`'s usage filter -- a re-export is named by a CONSUMER and not
    by this module's body -- and its WORD joins ``__all__`` beside the declared names, so
    the module promises every name it offers whether it declared it or not.

    **No declaration is a legitimate answer and writes an empty module**: a bundle that
    does not repeat an envelope states no family, and the artifact says so with an empty
    ``__all__`` rather than by not existing.

    ``prose`` is the lowering's own text about names this module does not declare, placed
    into the module docstring because a re-export has no docstring of its own to carry it
    -- the seam §7 states, where the lowering owns the sentence and the renderer owns
    where it goes.
    """
    rendered = [klass(decl) for decl in declarations]
    named = {one for one in imports if len(one) == 2}
    aliased = [one for one in imports if len(one) == 3]
    for one in rendered:
        named |= one.imports
    promised = [decl.name for decl in declarations] + [one[2] for one in aliased]
    exports = ", ".join(f'"{name}"' for name in sorted(promised, key=_export_key))
    body = "\n".join(
        [
            *(["\n\n\n".join(one.text for one in rendered), "", ""] if rendered else [""]),
            f"__all__ = [{exports}]",
            "",
        ]
    )
    return "\n".join(
        [
            BESIDE_HEADER,
            _with_prose(ENVELOPES_DOCSTRING, prose),
            "",
            *_import_section(named, body, aliased),
            body,
        ]
    )


#: The three characters that open and close a docstring, named once so :func:`_with_prose`
#: states the quote it reopens rather than spelling it twice in an f-string.
QUOTES = '"""'


def _with_prose(docstring: str, prose: str) -> str:
    """``docstring`` with ``prose`` as its last paragraph, or unchanged when there is none.

    :data:`ENVELOPES_DOCSTRING` is already the quoted TEXT of a docstring, so the paragraph
    goes before its closing quotes rather than after them -- which is why this is a
    function and not an f-string at the call site: getting that boundary wrong produces a
    module whose docstring swallows its own imports, and the mistake is invisible in a
    diff of the template.
    """
    if not prose:
        return docstring
    return "\n".join([docstring.removesuffix(QUOTES).rstrip("\n"), "", prose, QUOTES])


# --------------------------------------------------------------------------- #
# the constraints module, which belongs to no document (§8)
# --------------------------------------------------------------------------- #
#: ``AdCPUrl`` is ours: ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``,
#: named for provenance rather than after a standard, because pydantic exports 22
#: URL types and none is https-only -- a name like ``HttpsUrl`` would read as an
#: upstream export a reader cannot find.  The NAME is ``constraints.URL`` and the
#: STATEMENT is here, because a statement is text (§7).
URL_LINE = (
    f'{constraint_names.URL} = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]'
)

#: What :data:`URL_LINE` names.
URL_IMPORTS = {
    ("typing", "Annotated"),
    ("pydantic", "AnyUrl"),
    ("pydantic", "UrlConstraints"),
}

#: ``HttpUrl``: pydantic's own, RE-EXPORTED by the constraints module rather than
#: imported from ``pydantic`` at each site.  The import IS the declaration -- no
#: assignment, so nothing in this package restates what pydantic defines -- and it is
#: there and not left to ``pydantic`` because the SDK's ``uri`` decision is a SPLIT: a
#: consumer reading a module that declared only ``AdCPUrl`` would read the https-only arm
#: as the whole rule.  One place names both arms.
#:
#: **Declared as a re-export and not as an import, which is what it always was.**  No
#: line of the module NAMES it -- 133 emitted modules do -- so ``F401`` reported it
#: unused, and ``--fix`` would have deleted the name those modules import.  ``X as X``
#: is PEP 484's explicit re-export: ``F401`` reads it as the declaration the docstring
#: above already calls it, and a consumer's type checker reads it as part of this
#: module's interface, which is what ``py.typed`` promises.
URL_REEXPORTS = {("pydantic", constraint_names.HTTP_URL)}

CONSTRAINTS_DOCSTRING = '''"""Constrained types, each named for the constraint it carries.

GENERATED by ``codegen.emit``; see ``codegen/constraints.py``.  Edit neither --
the tree is ``f(bundle, emitter, pinned compiler)`` and a hand edit here is a
fact no input states (P10).

Every other type this SDK emits comes FROM A DOCUMENT and is reachable through
that document's own module, at its path under ``adcp.types._schemas`` -- which is
PRIVATE, and is the only path there is today (see ``adcp.types``).  A type derived
from a CONSTRAINT belongs to no document, so there is no such module for it and it
lives here instead, public, because a consumer annotating application code needs
it.  Its name is derived from the constraint and from nothing else -- never from a
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
place -- annotates every other ``uri`` field whose document asserts NOTHING ELSE.
``AdCPUrl`` everywhere was tried and
withdrawn: ``format: uri`` is RFC 3986, so a document stating only
``{"type": "string", "format": "uri"}`` admits ``http://``, ``urn:`` and
``file:///`` as well, and refusing those made the SDK stricter than the spec it
implements -- at 228 of 300 positions.  ``HttpUrl`` still refuses ``urn:`` and
``file:``, which is a named ceiling rather than an oversight.

**A ``uri`` NODE THAT ASSERTS ANYTHING THE URL TYPE DOES NOT STATE KEEPS THE
ASSERTION AND GIVES UP THE TYPE**, and a ``pattern`` is such an assertion.  No URL
type can carry a ``pattern`` at all -- pydantic refuses to build one -- so the node
becomes a constrained ``str`` here with the format riding as
``json_schema_extra={"format": "uri"}``, and BOTH of the document's facts are in the
annotation.  ``^https://`` is the one exception and it is not an exception to the
rule: that pattern IS ``AdCPUrl``'s ``allowed_schemes``, so the type states it.

What stood here read "either way the document's own ``pattern`` stays with the schema
half ... ``strict_validate`` applies the document before the constructor ever runs, so
the accepted set at the entry point is the document's", and the last clause is true of
the ENTRY POINT and false of the CLASS.  A consumer who constructs got a field wider
than its document at 408 positions in 115 documents, with no
``__adcp_approximations__`` entry to say so -- measured on
``core/reference-renderer.json``'s ``provenance.source_repository``, whose document
pins ``^https://github\\.com/`` and calls the field an allowlist, and whose class
round-tripped four non-GitHub URLs (``adcp-client-python-bgyd``).
"""'''


def domain_module(domain: str, held: Mapping[str, Sequence[tuple[str, str]]]) -> str:
    """The text of ``adcp/types/<domain>.py``: §1's public surface for one domain.

    ``held`` is the private module each exported name is declared in, grouped, with each
    entry the ``(symbol, word)`` pair the statement binds -- the DECISION, which is
    ``emit.domain_modules``' (§1's export set plus reading 6's inner words, read off the
    compiler's own record of both).  What is here is the TEXT, because §7 gives a module's
    header, import block and ``__all__`` to this module and because
    ``tests/test_import_rule.py`` holds it: nothing before the renderer holds a string of
    Python.

    **``X as X`` and a literal ``__all__``, which are two statements of one fact and both
    are wanted.**  The re-export form is what makes the name an export to a type checker
    rather than an incidental binding, and the literal list is what §1 asks for in so many
    words -- a module that leaves its surface implicit makes a reader derive it.  Written
    from one ``held``, so the two cannot disagree.

    **AND ``X as Y`` FOR READING 6's INNER CLAUSE**, where the two names differ by
    construction (``lower/names.THE_INNER_EXPORT``): the symbol is what §4 decided the
    private module declares and the word is what the clause decides the DOMAIN publishes.
    There the ``__all__`` entry is the half that makes it an export -- PEP 484 reads a name
    in ``__all__`` as public whatever the import spelling -- which is the second reason the
    literal list is written and not derived.

    **RELATIVE, for ``emit.relative_module``'s reason**: ``_schemas`` is private (P8) and a
    relative import is the one spelling that cannot name it.  TWO levels, because the
    aggregator sits in ``adcp/types/_surface/`` -- a package the compiler owns outright,
    whose reason is ``emit.SURFACE``'s -- and ``_schemas`` is its parent's sibling.  The
    arithmetic is one dot more than the public module needed and is asserted against the
    emitted import block rather than restated, for the reason
    ``test_a_document_whose_path_is_also_a_directorys_is_that_packages_root`` already gives:
    a leading dot too few resolves to a module that EXISTS, just the wrong one.

    **One statement per name, which is the sorter's form and not a choice of layout.**
    ``combine-as-imports`` is false by default and this project does not set it, so a
    ``X as X`` cannot share a statement with a sibling: the grouped form this function
    used to write is one the sorter rewrites, and ``I001`` named all 19 surface modules
    for it.  Setting the option instead would have been the measuring instrument moved to
    fit the output.
    """
    lines = [
        f'"""The exports of the ``{domain}`` domain, as the compiler aggregates them.',
        "",
        "Every name here is the class, root model, enumeration or alias the schema document",
        "of that name compiles to, re-exported from the private module at the document's own",
        "path.  The object is the same one the runtime validates into -- ``isinstance``",
        "against a union branch imported from here is true.",
        "",
        "Generated from the compiler's own record of what it exported: every document ROOT,",
        "every union BRANCH and every type ALIAS the documents of this domain declare.  A",
        "document added upstream appears here with nothing edited.",
        "",
        "**NOT the path a consumer writes.**  This file is the compiler's outright and is",
        "compared byte for byte, so that the domain's PUBLIC module can compose it in one",
        "line and serve a hand-written name set beside it where the domain's word is also a",
        "word upstream kept machinery under.  The public module is the one import path for",
        "every name here.",
        '"""',
        "",
    ]
    names = [word for module in held for _, word in held[module]]
    body = "\n".join(
        ["__all__ = [", *(f"    {word!r}," for word in sorted(names, key=_export_key)), "]", ""]
    )
    reexports = [
        (f".._schemas.{module}", symbol, word)
        for module in held
        for symbol, word in held[module]
    ]
    return "\n".join([*lines, *_import_section((), body, reexports), body])


def flat_surface(
    held: Mapping[str, str],
    ambiguous: Mapping[str, Sequence[str]] = {},
    aliases: Mapping[str, str] = {},
    declined: Mapping[str, Sequence[str]] = {},
) -> str:
    """The text of ``adcp/types/_surface/_flat.py``: the CROSS-DOMAIN consolidation.

    ``held`` is the word every domain aggregator publishes, keyed on the word and valued
    at the ONE domain that publishes it; ``ambiguous`` is the words more than one domain
    publishes, valued at every domain that does.  Both are
    ``emit.domain_modules``' decision, derived from the same ``Emitted.surface`` record
    the per-domain aggregators are, so this module is that union and never a second list.

    **IT IS ONE LEVEL UP FROM :func:`domain_module` AND NOTHING ELSE.**  A domain
    aggregator re-exports one domain's names out of the private per-document tree; this
    re-exports every domain aggregator's names out of the aggregators.  ``from .<domain>
    import <word> as <word>`` -- a SIBLING relative import, one dot, because ``_flat`` sits
    in ``_surface/`` beside the module it reads -- so the object bound here is the one the
    aggregator bound, which is the one the private module built.  Three spellings of a
    class and still one object: ``adcp.types.core.Account is
    adcp.types._surface.core.Account is adcp.types._surface._flat.Account``.

    **WHY A FLAT CONSOLIDATION EXISTS AT ALL, and it is not §1's second path.**  §1 gives
    a class ONE path a consumer writes and that path is the domain's.  This module is not
    one: it is private, under the package the compiler owns outright (``emit.SURFACE``),
    and the only thing that reads it is ``adcp.types.__getattr__`` -- the lazy
    compatibility facade reading 10 states, whose subject is "the import an application has
    already written".  An application that wrote ``from adcp.types import Account`` is owed
    an answer, and before this module the flat facade could answer only from the alias
    table, the adapter and the restored modules; a name our own walk emitted and no table
    mentioned raised ``AttributeError``.  Measured on the bundle this landed against:
    the aggregators carried 3,220 words and the flat facade served 1,183 of them.

    **A WORD TWO DOMAINS PUBLISH IS DECLINED AND NAMED, never resolved to a winner.**
    ``adcp.types.<domain>.<Name>`` is unique per domain and the surface gate holds that
    (``tests_emit/test_the_domain_surface.py``), but nothing makes a word unique ACROSS
    domains -- ``core/audience-source.json`` and ``enums/audience-source.json`` are two
    documents and two classes, and a flat namespace has one slot for the word.  Binding
    either would hand a consumer a class whose document they did not name and which
    ``isinstance`` would be false against; binding "whichever import ran last" is that same
    defect decided by file order.  So an ambiguous word gets NO binding here and is written
    into ``__adcp_ambiguous__``, which is the module saying what it declined and where the
    two paths are -- a reader who asks for it at the flat facade gets the facade's own
    ``AttributeError`` naming ``adcp.types.<domain>`` as the surface, which is the one
    answer that is true.

    **The literal ``__all__``, for :func:`domain_module`'s reason** -- §1 asks for the
    surface stated and the ``X as X`` form is what a type checker reads as an export -- and
    the measured one: under mypy ``--strict`` a star import re-exported through a module
    reveals the real class even with ``--no-implicit-reexport``, where a module-level
    ``__getattr__`` reveals ``Any``.  Written from one ``held``, so the list and the imports
    cannot disagree.

    **AND READING 10's ALIAS ARM IS THE SECOND HALF OF THE SAME MODULE** (2026-11-10).
    ``aliases`` is upstream's own published word -> the PRIVATE module whose ``X = <symbol>``
    statement binds it, and ``declined`` is the words that arm could not bind -> the
    ``<module>.<symbol>`` subjects each has.  Both are ``emit._alias_words``' decision,
    off the run's own record of the three joins that recovered those words.

    **THE IMPORT IS TWO LEVELS AND NAMES ``_schemas``, which is the one difference from the
    half above and is not a privacy leak**: the word is not on any domain aggregator -- it
    must not be, because the class it binds already has its one domain path and a second
    would be the path reading 6 forbids -- so there is no sibling to re-export it from and
    the private module that states it is the only source.  This file is itself private and
    is read by nothing but ``adcp.types.__getattr__``, so the spelling publishes nothing:
    the PUBLIC path for the class stays ``adcp.types.<domain>.<its own word>``, and what
    this module adds is the flat SPELLING an application already wrote.

    ``X as X`` here too, and for the plainer reason: upstream's word IS the symbol the
    private module binds, so the two halves are one name and the re-export convention
    applies unchanged.
    """
    lines = [
        '"""Every word the domain aggregators publish, consolidated into one namespace.',
        "",
        "Nothing here is a path a consumer writes and nothing here is declared: each name is",
        "re-exported from the domain aggregator beside this module, which re-exported it from",
        "the private module the document compiled to.  The object is the one the runtime",
        "validates into -- ``isinstance`` against a name imported from here is true.",
        "",
        "The one reader is ``adcp.types.__getattr__``, the lazy compatibility facade: an",
        "application that wrote ``from adcp.types import <Name>`` is owed an answer for every",
        "name this compiler emitted, and the per-domain aggregators cannot give it one",
        "because the flat spelling names no domain.  The PUBLIC path for every name here is",
        "still ``adcp.types.<domain>``.",
        "",
        "Generated from the compiler's own record of what it exported, so a document added",
        "upstream appears here with nothing edited.  A word more than one domain publishes is",
        "DECLINED rather than resolved to a winner and is named in ``__adcp_ambiguous__``:",
        "a flat namespace has one slot for the word, the domains have two classes, and",
        "picking one would hand a consumer a class whose document they did not name.",
        "",
        "**AND READING 10's ALIAS WORDS ARE HERE BESIDE THEM**: upstream's own published",
        "spelling of a class of ours, which the private module already states as an",
        "``X = <symbol>`` and which no domain aggregator carries -- the class has its one",
        "domain path under its own word, and a second would be the path reading 6 forbids.",
        "This is the ONE namespace a flat import resolves at, so it is the one place such a",
        "spelling belongs.  A word the surface above already publishes, or that upstream's",
        "generator derived from a property key two documents share, is DECLINED and named",
        "in ``__adcp_alias_declined__``.",
        '"""',
        "",
    ]
    declined_block = "\n".join(
        [
            "#: The words more than one domain publishes, and the domains that publish each.",
            "#: Bound nowhere in this module -- the public ``adcp.types.<domain>`` path is the",
            "#: only one that can say which of the two a caller meant.",
            "__adcp_ambiguous__: dict[str, tuple[str, ...]] = {",
            *(
                f"    {word!r}: {tuple(sorted(ambiguous[word]))!r},"
                for word in sorted(ambiguous, key=_export_key)
            ),
            "}",
            "",
            "",
            "#: Upstream's published words this module declines, and the",
            "#: ``<module>.<symbol>`` subjects each one has.  A word that IS in ``__all__``",
            "#: is declined because the generated surface already publishes it and resolves",
            "#: it to the class the schemas name; a word that is NOT resolves nowhere here,",
            "#: because upstream derived it from a property key more than one document uses",
            "#: and the subjects below are distinct classes.  Each is reachable under its",
            "#: own ``adcp.types.<domain>`` word, which is the name minted from the parent",
            "#: class and the key together.",
            "__adcp_alias_declined__: dict[str, tuple[str, ...]] = {",
            *(
                f"    {word!r}: {tuple(declined[word])!r},"
                for word in sorted(declined, key=_export_key)
            ),
            "}",
            "",
        ]
    )
    body = "\n".join(
        [
            "__all__ = [",
            *(
                f"    {word!r},"
                for word in sorted({*held, *aliases}, key=_export_key)
            ),
            "]",
            "",
            "",
            declined_block,
        ]
    )
    reexports = [
        *((f".{held[word]}", word, word) for word in sorted(held, key=_export_key)),
        *(
            # ``.._schemas.<module>``, the same arithmetic :func:`domain_module` writes and
            # for the same reason -- this file sits in ``_surface/`` and ``_schemas`` is its
            # parent's sibling.  A leading dot too few, or the prefix left off, resolves to
            # ``adcp.types.<domain>.<module>``: a module that does NOT exist, and whose
            # ``ModuleNotFoundError`` the facade's own missing-module shim swallows, so the
            # whole arm degrades to silence rather than to an error.  Measured, once.
            (f".._schemas.{aliases[word]}", word, word)
            for word in sorted(aliases, key=_export_key)
        ),
    ]
    return "\n".join([*lines, *_import_section((), body, reexports), body])


def surface_package() -> str:
    """The text of ``adcp/types/_surface/__init__.py``: a docstring and NO name.

    The package exists so that each domain's aggregator can live in a file the compiler
    owns outright (``emit.SURFACE``), and its own ``__init__`` is the one module of it that
    aggregates nothing: a name bound here would be a third spelling of a class §1 gives one
    path, and it would be bound while the package's body runs -- which is before anything
    can decide which tree the children come from.
    """
    return "\n".join(
        [
            '"""The compiler\'s own aggregators, one module per domain.',
            "",
            "Nothing here is a path a consumer writes.  Each module re-exports one domain's",
            "names from the private per-document tree, and the public module of that domain",
            "composes this one with a single star re-export -- which is what lets a public",
            "path serve an emitted name set beside a hand-written one without either file",
            "holding the other's text.",
            "",
            "This package declares no name of its own.",
            '"""',
            "",
        ]
    )


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

    The LAYOUT is :func:`_import_section`'s, which is every other module's: stdlib, then
    the library, one blank line between the groups.  It used to be spelled here, on the
    argument that two of :func:`_import_rank`'s four ranks cannot occur in this module --
    true, and it is the RANK FUNCTION that says so rather than a second copy of the
    grouping.  The copy had drifted by one blank line, which is one ``I001``.
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
    body = "\n".join([*lines, ""])
    return "\n".join(
        [
            BESIDE_HEADER,
            CONSTRAINTS_DOCSTRING,
            "",
            *_import_section(imports, body, URL_REEXPORTS),
            body,
        ]
    )
