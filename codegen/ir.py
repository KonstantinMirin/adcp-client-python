"""The intermediate representation: what the walk DECIDED, as values.

``docs/plan/architecture.md`` §7 declares this layer and its one property: the IR is
**complete**, so nothing before ``codegen/render.py`` holds a string of Python.  A
declaration here carries a decision -- a type, a field, a class, an enumeration, an
alias, a root binding, a union install -- and ``render.py`` is the only module that
turns one into text.

*Why complete and not the economy this replaced.*  §7's own words: the decision layer
used to produce class-body lines, rule tuples and module trailers AS TEXT, and a
``Module`` accumulated text blocks beside its decision memo.  That is two layers
sharing a mutable object, and the cost was one module holding the renderer, the keyword
sets, the name rules, the field builder and the composition reader at once.  With the
IR complete the renderer is the only reader of the model layer it renders through, so a
change of rendering -- a ``datamodel-code-generator`` upgrade, a different spelling of
an optional -- touches one module.

**Rules are the runtime's own dataclasses** (§7, and §2 of the semantics document,
"rules are after-validators, written once").  :attr:`ClassDecl.rules` holds INSTANCES of
``adcp.types._runtime``'s frozen dataclasses -- ``RequiredGroups``,
``ConditionalRequired``, ``Dependencies``, ``PropertyCount``, ``UniqueItems``,
``ForbiddenGroups``, ``NegatedConditional`` -- built by ``codegen.lower.rules`` from the
rule sources on the node.  So a rule is declared ONCE, in the runtime, and the walk
composes values rather than formatting strings.  Naming ``adcp.types._runtime`` from
this layer is not a Pydantic idiom: §8 says naming a symbol is not one, while
constructing a ``Field``, a ``ConfigDict``, an ``Annotated`` or a ``DataType`` is, and
only ``render.py`` does that.

**A declaration carries no name of its own choosing.**  ``name`` is still a field here
because the walk computes one today; §7 and §14 step 7 move naming into
``codegen/lower/names.py`` as a pass over the finished module, keyed by POINTER.  This
layer is what that pass will rewrite, not where it lives.

Two slots §7 names are declared by the rows that write them and not here:
``TypeRef.validators`` (``AtLeastOne``, ``NotValue``, ``Distinct`` -- type-bound rules
for a value no class holds), whose runtime classes §14 step 8 declares; and a
union base's ``branches`` as ``TypeRef``s, which §14 step 7's symbol table supplies.
:class:`UnionInstall` carries the branch SYMBOLS the walk has today.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from adcp.types._base import KINDS, UNDERDETERMINED, WIDENED, Approximation, SchemaRef
from adcp.types._runtime import Rule

#: **Section 7's ``Approximation``, bound here and declared in the artifact's own
#: package.**  The section's table puts it in this layer -- "document, pointer, keyword,
#: kind (WIDENED / UNDERDETERMINED), rung, the fact the annotation does not carry in the
#: document's own spelling, and the attribution" -- and its text puts the VALUE in the
#: emitted module: "``render.py`` writes ``__adcp_approximations__`` onto the class ... and
#: ``verify/`` reads it as a consumer reads any other class attribute."
#:
#: Both are satisfied by declaring it where ``SchemaRef`` is declared and binding the name
#: here, which is exactly what this module already does for ``SchemaRef`` and ``Rule``:
#: the declaration is ONE, the artifact carries it, and the verifier -- which section 9
#: forbids ``codegen.ir`` -- reads it through ``adcp.types``, which section 9 permits.
#: ``adcp.types._base.Approximation``'s own docstring carries the reasoning.  The two
#: kind words travel with it, for the reason the class does: the emitted module spells
#: one of them and both halves read it.
_SECTION_7_APPROXIMATION = (Approximation, WIDENED, UNDERDETERMINED, KINDS)

#: Absent is not the same as ``None``: a property whose schema declares
#: ``default: null`` has a default and it is ``None``.
MISSING = object()

#: The import path of the hand-written base every emitted module imports from, and the
#: one the rule kinds come from.  Named in the layer that names the runtime's SYMBOLS --
#: ``SchemaRef`` and ``Rule`` above -- so the dotted path and the symbol have one
#: declaration between them: the renderer's import ranking, the module-level binding a
#: root alias writes and the rule imports a class reports all read these two.
BASE_MODULE = "adcp.types._base"
RUNTIME_MODULE = "adcp.types._runtime"

#: **The keywords a :attr:`TypeRef.facts` carries: a constraint of the VALUE, in the
#: document's own spelling.**  Everything else a document can say about a value is a type
#: (and so part of the decided :class:`TypeRef`), an annotation (and so a field's
#: ``description``), a rule (``ClassDecl.rules``), or a keyword the walk refuses.
#:
#: Declared HERE because this is the layer that declares what ``facts`` may hold, and
#: because two readers ask: the walk, cutting a scalar node's constraints out of the node
#: (``emit._scalar``), and ``codegen.render``, filtering them into the model layer's
#: ``constraints=``.  One declaration, so the two cannot disagree about what a constraint
#: IS; pydantic's own spelling of the two that differ is ``render.KEY_COUNT`` and stays
#: behind the §8 boundary.
#:
#: ``docs/plan/architecture.md`` §11 says this should be derived -- "the annotation set,
#: the rule-keyword set, the constraint spelling in three modules | rows of the table" --
#: and §3 declares no column that answers it: a cell's ``effect`` is ``TYPE`` for
#: ``type``, ``enum``, ``const`` and ``format`` as well, and ``uniqueItems`` is ``RULE``.
#: §14 step 5's ``schema/parse.py`` is the mechanism that reaches it: a parsed node
#: carries its own facts, classified from the table at its position, and this set is what
#: that classification replaces.
FACTS = (
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


@dataclass(frozen=True)
class TypeRef:
    """A Python type as a VALUE: what our walk decided a node's type is.

    ``path`` is a dotted path the renderer resolves to a type and an import
    (``"int"``, ``"datetime.date"``, ``"pydantic.AnyUrl"``, ``"typing.Any"``), or
    a bare symbol when ``local`` -- a class declared in the same module, or a
    symbol the module writer imports from a sibling module because the document
    referenced another document (P2).  The renderer adds no import for a local
    symbol, which is right in both cases: a sibling class needs none, and a
    cross-document import is the module writer's, derived from the two document
    paths.

    A local symbol is a REFERENCE to another model and not a custom type, and
    that distinction decides a config: ``is_custom_type`` makes the code generator add
    ``arbitrary_types_allowed=True`` to the class's ``ConfigDict``, which is a
    relaxation of pydantic nobody decided and which D7 does not derive.  Every
    local symbol here is something this pipeline emitted -- a sibling class or an
    ``Annotated`` alias -- so pydantic resolves all of them and the relaxation is
    both unasked for and untrue.

    A CONTAINER is the same vocabulary one level up: ``container`` names the shape
    and ``of`` carries the types inside it.  It is a decision and not a rendering
    because deciding ``list[X]`` is the walk's judgement and writing ``list[X]`` is
    the renderer's -- a lowering that assembled the annotation TEXT itself would be
    the second half of the seam doing the first half's job.

    ``of`` is deliberately one field for three shapes, because the renderer reads
    all three out of the model layer's single ``data_types``: the element of a list,
    the VALUE of a mapping, and the arms of a union.  A mapping's key is the one type
    that is not in it, because the model layer carries it in its own ``dict_key`` slot
    -- which is what makes D5's typed key expressible at all.

    **A container carries no bound of its OWN CONTENTS here.**  A bound on a list is
    a bound on the list (:attr:`facts`, rendered ``Field(min_length=...)``), and a
    bound on what is INSIDE a container has no slot in the model layer's ``DataType``
    -- which is the gap D5 closes by naming the inner type rather than the gap it
    looks like.  ``compiler.carried`` is where a position with no field asks for that
    name, and what still reaches it unnamed refuses instead of being dropped.

    ``container="alias"`` is the one shape the model layer cannot render itself and the
    one the naming answer needs: a GENERIC alias applied to its arguments, ``path``
    naming the alias and ``of`` carrying them.  ``NonEmptyList[MediaBuyStatus]`` is what
    a bounded array on a union BRANCH lowers to, and the model layer's ``DataType`` has
    no slot for it -- probed on the pinned version: a ``reference`` beside
    ``data_types`` renders the ARGUMENT alone (``str``), and a ``reference`` alone
    renders the alias alone (``NonEmptyList``), so either spelling silently loses half
    the type.  The subscript is therefore composed in ``render.py``, which keeps §1's
    seam: the walk decides the alias and the arguments, and the renderer writes the
    text.
    """

    path: str = ""
    local: bool = False
    #: ``"list"``, ``"dict"``, ``"union"`` or ``"alias"`` when this type is a container.
    container: str = ""
    #: A list's element, a mapping's value, or a union's arms.
    of: tuple[TypeRef, ...] = ()
    #: A mapping's key, and only a mapping has one (D5 types it from the document).
    key: TypeRef | None = None
    #: D2's ``const`` row: the one value the node PINS, as a 1-tuple, and ``()`` for
    #: every other node.  The walk decides the value and the renderer writes the
    #: ``Literal``, which is §1's seam -- and here it is load-bearing rather than
    #: tidy.  Written as ``TypeRef("Literal[%r]" % value, local=True)`` instead, the
    #: annotation reached the model layer as a ``Reference`` PATH, and
    #: ``treat_dot_as_module`` read the dot in a value like ``account.status_changed``
    #: as a module qualifier and kept the last segment:
    #: ``Literal['account.status_changed']`` rendered as ``status_changed']``, a module
    #: that does not parse.  The model layer's own ``literals`` carrier renders the
    #: value, escapes it (``"quo'te"`` comes back ``Literal["quo'te"]``) and reports the
    #: ``typing.Literal`` import itself.
    #:
    #: A tuple and not a bare value because ``const: null`` is a pinnable value, so
    #: a ``None`` default could not be told from an absent one.  One member is all
    #: a ``const`` has; the plural is the model layer's spelling of the slot.
    literals: tuple[Any, ...] = ()
    #: **The constraint keywords this type carries, in the DOCUMENT'S OWN SPELLING**
    #: (§7).  §2 of the semantics document: *constraints bind to the type, not the
    #: field* -- so a bound travels with the type into ``list[...]``, into a mapping
    #: value and into a union branch, and the one module that knows pydantic's
    #: vocabulary translates the spelling (``render.CONSTRAINTS``, ``render.KEY_COUNT``).
    #: Nothing before ``render.py`` holds pydantic's word for a keyword.
    facts: Mapping[str, Any] = field(default_factory=dict)
    #: The document's ``format``, where the walk did NOT turn it into a type.
    #: D5 lets a format select one (``emit.FORMAT_TYPES``), and a selected type
    #: states the format in its own rendered schema -- so this field is the other
    #: case, and it rides as ``json_schema_extra`` so the fact reaches the
    #: model's schema where the comparison grades it.  The two are exclusive by
    #: construction (``compiler.Decided``): a format is in the type or in here, and
    #: never in both and never nowhere.  Dropping it would lose a fact the
    #: document states.
    format: str | None = None


@dataclass(frozen=True)
class Field:
    """One decided field.

    ``name`` is the Python attribute and ``wire`` the document's property key.
    They differ only when pydantic cannot carry a field under the key's own
    spelling, and then ``wire`` becomes an ``alias`` -- the only accepted
    spelling, because nothing in the renderer sets ``populate_by_name``.

    The field's BOUND and its ``format`` are on its :attr:`type` (§2, and
    :attr:`TypeRef.facts`), not here: the same bound reached through a list, a mapping
    value or a union branch has nowhere else to live, and the usual repair -- putting
    it on the field holding the container -- constrains the wrong thing.
    """

    name: str
    wire: str
    type: TypeRef
    required: bool
    default: Any = MISSING
    description: str | None = None
    #: D6's ``uniqueItems`` on the array this field holds.  The RULE is what enforces
    #: it on the constructor (``adcp.types._runtime.UniqueItems``); this flag is the
    #: other half, and it rides the ``json_schema_extra`` channel beside
    #: :attr:`TypeRef.format` and for the same reason -- pydantic removed
    #: ``unique_items`` in v2, so no annotation states the fact, and the schema
    #: comparison reads ``uniqueItems`` off a model's rendered schema
    #: (``harness.FACTS``).  Rendering it where the document states it is what keeps
    #: the comparison symmetric: the fact is TRUE of the model, because the schema half
    #: and the rule both enforce it, so no admission row is needed in either direction.
    distinct: bool = False
    #: §6's ``deprecated`` row, which §14 step 8 and the ``deprecated`` row of the epic
    #: write the emitter half of.  Declared here because §7 declares it; nothing writes
    #: it yet and the renderer reads nothing from it, so flipping the cell to rendered
    #: is one handler change against a slot that exists.
    deprecated: bool = False


@dataclass(frozen=True)
class ClassDecl:
    """One decided class.  ``ref`` is the schema it will carry and grade against."""

    name: str
    ref: SchemaRef
    fields: tuple[Field, ...]
    description: str | None = None
    #: D8: ``forbid``, ``allow``, or ``None`` to leave the base's default.
    extra: str | None = None
    #: D7: the symbols this class's document COMPOSES, in the conjunct order the
    #: document lists them.  Empty leaves ``custom_base_class``, which is
    #: ``AdCPBaseModel`` and is every class with nothing to compose; a non-empty
    #: tuple replaces it, and ``AdCPBaseModel`` arrives through the bases because
    #: every base is itself an emitted class.  The symbols are names the module
    #: writer has already imported -- the renderer adds no import for a base, for
    #: the same reason ``TypeRef.local`` adds none: a cross-document import is
    #: derived from the two document paths (D1) and is the module writer's.
    #: §4's union row derives them from the SHAPE rather than from a composition --
    #: a base is ``(BranchDispatchMixin, AdCPBaseModel)`` and a branch is its base --
    #: so naming any of them replaces ``custom_base_class`` and a caller that wants
    #: ``AdCPBaseModel`` in the list says so.
    #:
    #: **``TypeRef``s and not bare strings** (§7's table: "bases (``TypeRef``s)"), which
    #: is what lets a base be a LOCAL declaration of this module -- carried by pointer
    #: until ``lower/names.py`` binds it -- beside one another module declares, carried
    #: as the symbol the module writer imported.  One slot, two kinds of name, and the
    #: symbol table is what tells them apart.
    bases: tuple[TypeRef, ...] = ()
    #: D8's typed row: the type of a property the class does not DECLARE, which
    #: pydantic validates through ``__pydantic_extra__``.  It is a mapping, because
    #: ``additionalProperties`` types the values under keys the document does not
    #: name -- D5 types the key too, so it is the same ``dict[K, V]`` a mapping node
    #: lowers to and is decided by the same row.
    extras: TypeRef | None = None
    #: **D6's rules, as INSTANCES of the runtime's own frozen dataclasses** (§7).  The
    #: renderer writes a constructor expression per rule into the one class-level
    #: ``_adcp_rules`` tuple that ``adcp.types._runtime.RuleBound`` reads.  This
    #: replaced a class-body LINE the walk formatted, which is the text §7 says the IR
    #: does not hold; the rule kinds are declared once, in the runtime, and the walk
    #: composes values.
    rules: tuple[Rule, ...] = ()
    #: §4's three facts the emitter writes onto a UNION BASE, because none of them is
    #: recoverable at run time.  ``root_required`` is the fields the root requires as
    #: opposed to the ones that select a branch; ``discriminator`` is the property
    #: every branch pins a ``const`` on (§4's first dispatch source), empty where
    #: dispatch is the third source; ``combinator`` is ``"oneOf"`` or ``"anyOf"``,
    #: because a refusal has to name a JSON Schema keyword and a payload satisfying no
    #: branch fails each branch at field validation.  ``None`` on every class that is
    #: not a union base, which is what tells the renderer to write none of the three.
    root_required: tuple[str, ...] | None = None
    discriminator: str | None = None
    combinator: str | None = None
    #: §7's fourth union-base slot: **the base's BRANCHES as ``TypeRef``s**.  Declared
    #: in the IR and unwritten until §14 step 7; written by ``lower/union.py`` now, from
    #: the same expression that builds :class:`UnionInstall`'s, so the two slots cannot
    #: come to disagree about which classes are this base's branches.  ``None`` on every
    #: class that is not a union base, which is what tells a reader the slot is not
    #: merely empty.
    branches: tuple[TypeRef, ...] | None = None


@dataclass(frozen=True)
class Member:
    """One decided enumeration member: the name the walk chose, and its value."""

    name: str
    value: Any
    #: The document's ``enumDescriptions`` entry for this value, where it has one.
    #: It reaches the rendered class as the member's own docstring, which is the
    #: renderer's own slot for it -- 137 of the bundle's enum nodes carry the
    #: block and a previous attempt dropped every one of them, for the same
    #: reason a hand-rolled renderer dropped 142 property descriptions: nothing
    #: compares an annotation that changes no accepted set.
    description: str | None = None


@dataclass(frozen=True)
class EnumDecl:
    """One decided enumeration.  ``kind`` names the base, in JSON Schema's words.

    No ``ref``, and that is the one place an enumeration differs from
    :class:`ClassDecl`: the model layer's ``Enum.jinja2`` has no ``class_body_lines``
    slot, so an ``__adcp_schema__`` line cannot reach an enum's class body through the
    renderer at all -- and D9 forbids writing it in afterwards.  A ROOT enum therefore
    binds the reference and ``strict_validate`` at module level (:class:`RootBinding`),
    which is what D2's root-scalar row already does for the same reason (a node with no
    ``AdCPBaseModel`` to hang a classmethod on).  An INLINE enum is a type its parent's
    field names, like any annotation.
    """

    name: str
    kind: str
    members: tuple[Member, ...]
    description: str | None = None


@dataclass(frozen=True)
class AliasDecl:
    """``<name> = <annotation>``: a node that is a TYPE and has a symbol.

    D2's root-scalar row, and the node another document NAMES.  A scalar root has no
    class to hang itself on, so it is a module-level ``Annotated`` alias; a fragment
    reference resolves to an import of a symbol the target module declares, never to a
    copy, so an array, a scalar or a mapping another document names takes one too.

    The bound and the ``format`` are on :attr:`type` (§2 and :attr:`TypeRef.facts`), so
    a ``minLength`` on an alias and a ``minLength`` on a property cannot come to be
    spelled two different ways.  The description rides in ``Field`` rather than in a
    docstring, because an alias has no docstring slot: five of the scalar roots had
    their root ``description`` dropped for exactly that reason.
    """

    name: str
    type: TypeRef
    description: str | None = None


@dataclass(frozen=True)
class RootBinding:
    """The module-level half of a root that is not an ``AdCPBaseModel`` (§7).

    D2 gives two root kinds no class to hang ``strict_validate`` on: a scalar root is
    an ``Annotated`` alias, and an enumeration cannot carry a class-body line at all.
    Both bind the SAME two statements at module scope -- the ``SchemaRef``, and
    ``strict_alias`` over the symbol -- so a class, an alias and an enumeration cannot
    come to answer differently about what their own document accepts.

    :attr:`declaration` is the alias or the enumeration the two statements wrap.  It is
    CARRIED here rather than declared beside this one because the three statements are
    one block in the module's own layout, and the blank-line rule between them is the
    renderer's: a reader of ``render.py`` sees the whole binding in one place.
    """

    ref: SchemaRef
    symbol: str
    declaration: AliasDecl | EnumDecl


@dataclass(frozen=True)
class RootModelDecl:
    """**Section 7's third root shape**: a root that is neither a class nor an alias.

    "``RootModelDecl`` | pointer, ``SchemaRef``, the root ``TypeRef``, description, rules,
    and for a mixed root union the dispatch facts -- a root that is an array, a mixed
    union, or a document stating no schema keyword."

    Three rows of the semantics document reach it and all three are section 14 step 9's,
    not this row's: section 5's ``items`` row at ROOT ("array -> ``RootModel[list[X]]``"),
    section 4's new mixed-root-union row ("A ``Union`` at ROOT mixing the two lowers to a
    ``RootModelDecl`` over the union of the branches' types, with the class branches
    declared beside it and the dispatch facts on the root model"), and section 7's
    registry row ("a root stating only these keys is a permissive root model").

    **Declared here with no producer, which is what makes each of those a one-handler
    change against a slot that exists** -- the same arrangement ``Field.deprecated`` and
    ``ClassDecl.branches`` were declared under, and the reason section 14 orders the
    structure before the rows.  ``codegen/render.py`` renders it, and
    ``tests/test_approximation.py`` grades that rendering against a hand-built declaration,
    so the path from a declaration to text is exercised before a handler writes one.

    *Why a declaration of its own and not a ``ClassDecl`` with a flag.*  A root model's
    body is a ``root:`` annotation and a class's is a field list, so the two differ in
    what the renderer writes rather than in a property of one shape; and section 7's table
    gives them separate rows.  ``rules`` is on both because section 8 of the architecture
    document requires it -- "each must carry ``__adcp_schema__``, ``strict_validate`` and
    a rule tuple exactly as a class does, or a root model and a class disagree about what
    their document accepts".

    The runtime base a renderer writes it through is ``AdCPRootModel``, which section 8 of
    the architecture document declares and step 9 adds; until then the renderer names it
    and no emitted module imports it, so nothing of the committed tree moves.
    """

    name: str
    ref: SchemaRef
    #: The type the root model wraps: ``list[X]`` for a root array, the union of the
    #: branches' types for a mixed root union, ``Any`` for a document stating no schema
    #: keyword.
    type: TypeRef
    description: str | None = None
    rules: tuple[Rule, ...] = ()
    #: Section 4's three dispatch facts, on a MIXED root union and ``None`` everywhere
    #: else -- the same three slots and the same meaning :class:`ClassDecl` carries them
    #: with, because a mixed root union's class branches dispatch exactly as a class
    #: base's do.
    root_required: tuple[str, ...] | None = None
    discriminator: str | None = None
    combinator: str | None = None
    branches: tuple[TypeRef, ...] | None = None


@dataclass(frozen=True)
class UnionInstall:
    """§4's rebuild: the union base takes its branches, and pydantic is told.

    Branches SUBCLASS the base, so they do not exist while the base is built: the
    mixin's ``__get_pydantic_core_schema__`` returns the base's own schema then, and the
    declaring module assigns ``_branch_models`` and calls ``model_rebuild(force=True)``
    afterwards.  §7 makes it a declaration rather than a module trailer the walk
    formats, which is the last of the four texts §11 lists as produced in the walk.

    It declares no NAME -- both statements are about symbols the module already declares
    -- so it is appended to the module's declarations and never passed through
    ``Module.declare``.
    """

    base: TypeRef
    branches: tuple[TypeRef, ...]


#: Every declaration a module can hold, which is what ``render.py`` dispatches on.
Declaration = ClassDecl | EnumDecl | AliasDecl | RootBinding | RootModelDecl | UnionInstall


@dataclass(frozen=True)
class Module:
    """One document's finished module: §7's last row, and the renderer's whole input.

    "``Module`` | document, root symbol, declarations in declaration order, imports, the
    symbol table pointer -> name, the adoption table pointer -> declaring pointer."

    **It is the OUTPUT of ``codegen/lower/names.py`` and not the walk's accumulator**,
    which is the split §7 draws and §14 step 7 is what lands.  The walk's own value --
    ``compiler.Module`` -- carries the run's targets, the parser's source, the shapes a
    composing row reads, the aliases and the reports, every one of which §11 keeps out
    of this layer ("representation | the declarations and ``TypeRef`` | text, pydantic,
    nodes").  What crosses the seam into ``render.py`` is this, and every symbol in it
    is bound: a ``TypeRef`` marked ``local`` names a class and never a pointer, so the
    renderer writes text and resolves nothing.

    *Why this retires ``render.Written``.*  That Protocol existed because §11's arrows
    run ``ir <- render <- emit`` and ``Module`` was in the decision layer, which the
    renderer may not know; with ``Module`` here the renderer takes the type by name.
    """

    document: str
    #: The symbol the document's ROOT binds, which is §4's ``pascal_case(title)``.
    root: str
    declarations: tuple[Declaration, ...]
    imports: frozenset[tuple[str, str]]
    #: **§7's symbol table**: JSON Pointer -> the symbol declared for the node at it.
    #: This is how a ``$ref`` carrying a pointer finds the symbol to import, and it is
    #: what ``emit.exported`` reads a module's public surface off.
    symbols: Mapping[str, str] = field(default_factory=dict)
    #: **§7's adoption table**: JSON Pointer -> the pointer whose class the node at it
    #: ADOPTED under §4's content dedup, because an earlier node of identical content
    #: declared it.  With :attr:`symbols` this is the whole of what the dedup did, and it
    #: is what a check can grade it over in both directions -- an adoption whose two
    #: nodes are NOT identical is the failure that matters more than a missed collapse.
    adopted: Mapping[str, str] = field(default_factory=dict)
    #: **§7's ``approximations`` slot**: every fact this document's annotations do not
    #: carry, in DOCUMENT ORDER.  §6: "An approximation ... is **local** -- it belongs to
    #: the node that could not render a keyword and says nothing about the node above it
    #: -- so a parent composes it like any other part of a child's lowering and keeps
    #: building ... What reaches ``lower_document`` is therefore not one approximation but
    #: all of them, in document order, because ``+`` concatenates and the children were
    #: lowered in the order the document states them."
    #:
    #: A TUPLE and not a set, for the reason ``declarations`` is one: the order is the
    #: document's and the report prints one line per entry, so two reports of one document
    #: are comparable.  ``render.py`` distributes them onto the declarations whose nodes
    #: contain them (``render.declared_at``), which is the pairing §9 grades over.
    #:
    #: **Empty over the whole bundle at §14 step 8**, which is that step's exit condition:
    #: the instrument exists and no cell widens, so every module's declaration is empty
    #: and the emitted tree does not move.
    approximations: tuple[Approximation, ...] = ()


def symbols(decided: TypeRef) -> set[str]:
    """Every symbol a decided type names in the module that decided it.

    Read off the :class:`TypeRef` TREE rather than off any rendered text: a local arm
    is marked ``local`` where it is decided, so this enumerates the symbols instead of
    matching identifiers in an annotation and guessing which are types.  Two readers ask
    -- ``compiler._reused``, for the symbols a re-used inherited field needs importable,
    and ``emit.exported``, for the names a module's ``__all__`` carries -- and a second
    copy of the walk is how the two come to disagree about what a type names.
    """
    found = {decided.path} if decided.local and decided.path else set()
    for inner in (*decided.of, *([decided.key] if decided.key is not None else [])):
        found |= symbols(inner)
    return found


def deduped(arms: Sequence[TypeRef]) -> tuple[TypeRef, ...]:
    """``arms`` in document order with the repeats dropped.

    By EQUALITY and not through a hash, because :attr:`TypeRef.facts` is a mapping: two
    types that say the same thing are one arm, and ``A | A`` would be a second spelling
    of one type.  Both callers -- ``containers.multi_type`` and ``union.nested`` -- are
    a type LIST reduced to a union, which is where the repeat comes from.
    """
    out: list[TypeRef] = []
    for arm in arms:
        if arm not in out:
            out.append(arm)
    return tuple(out)
