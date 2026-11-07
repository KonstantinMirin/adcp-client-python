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

**A declaration carries no name of its own choosing, and that is the state rather than
the plan.**  ``name`` is a field here, and during the walk it holds the node's own
POINTER: ``codegen/lower/names.py`` is the pass over the finished module that rewrites
every slot into a symbol (§7, §14 step 7).  This docstring used to say the walk computed
a name and that the pass was coming; both stopped being true when step 7 landed.  The
READING: ``codegen/compiler.py``'s class declarer passes ``name=pointer``, and
``names.assign`` is the one function that turns those keys into §7's symbol table.

``TypeRef.validators`` is the same arrangement one level down: ``AtLeastOne``,
``NotValue`` and ``Distinct`` are declared in ``adcp.types._runtime`` beside the
class-level kinds, and this layer carries INSTANCES of them on the type they constrain.
§2 is why there are two slots and not one -- "on the nearest class if there is one ...
where no class sits above the value, the rule hangs off the value's own annotated type"
-- and ``codegen.lower.rules`` writes both halves, so one module decides which of the
two a document's statement reaches.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from adcp.types._base import KINDS, UNDERDETERMINED, WIDENED, Approximation, SchemaRef
from adcp.types._runtime import Rule, ValueRule

# §2's one exception, named here because :meth:`ClassDecl.__post_init__` raises it.
# ``codegen/refusal.py`` imports nothing of this package -- its own module docstring says
# so, "which is also what keeps the import graph acyclic once every lowering needs it" --
# so naming it from the IR closes no cycle.
from codegen.refusal import BuildFailure

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

#: **The one field a ``RootModel`` has**, which is pydantic's name and not ours.  Named
#: here for the reason the two module paths above are: two readers spell it and a second
#: spelling is how they come apart.  ``render.root_model`` writes the ``root:``
#: annotation, and ``lower/containers.py`` keys a root array's ``UniqueItems`` rule on it
#: -- because ``_runtime.supplied`` reads ``__pydantic_fields_set__``, and a root model
#: supplies exactly this name.  A rule keyed on anything else would be a rule that never
#: fires, which only a direct ``model_validate`` would show: a rule renders nothing in
#: a model's schema.
ROOT_FIELD = "root"

#: **The keywords a :attr:`TypeRef.facts` carries: a constraint of the VALUE, in the
#: document's own spelling.**  Everything else a document can say about a value is a type
#: (and so part of the decided :class:`TypeRef`), an annotation (and so a field's
#: ``description``), a rule (``ClassDecl.rules``), or a keyword the walk refuses.
#:
#: Declared HERE because this is the layer that declares what ``facts`` may hold.  It had
#: two readers -- the walk, cutting a scalar node's constraints out of the raw node, and
#: ``codegen.render``, filtering them into the model layer's ``constraints=``.  **The
#: walk's half is gone**: ``codegen/schema/parse.py`` classifies a node's own facts from
#: the table at its position (``nodes.Base``'s ``facts``, DERIVED), so ``render.py``'s
#: filter is the one reader left of this tuple.  pydantic's own spelling of the two that
#: differ is ``render.KEY_COUNT`` and stays behind the §8 boundary.
#:
#: ``docs/plan/architecture.md`` §11 says this should be derived -- "the annotation set,
#: the rule-keyword set, the constraint spelling in three modules | rows of the table" --
#: and §3 declares no column that answers it: a cell's ``effect`` is ``TYPE`` for
#: ``type``, ``enum``, ``const`` and ``format`` as well, and ``uniqueItems`` is ``RULE``.
#: §14 step 5's ``schema/parse.py`` is the mechanism that reached it, and it has: a parsed
#: node carries its own facts, classified from the table at its position, which is what
#: this tuple was replaced BY on the walk's side.  What survives here is the renderer's
#: filter, and §11's row is still pointed at that.
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
    #: **§5's ``enum`` row at CONJ: the MEMBER NAMES of the enumeration :attr:`path`
    #: names, where a conjunct's own vocabulary narrows the target's to a subset.**  The
    #: rendering the row decides is ``Literal[CreativeApprovalStatus.PENDING_REVIEW, …]``
    #: -- a ``Literal`` over the target's members and not over their raw values, because
    #: both dump identically and the member form keeps the imported symbol a caller can
    #: name.
    #:
    #: A SLOT OF ITS OWN, and :attr:`literals` could not carry it for the very reason
    #: that field's own comment records: the model layer's ``literals`` renders a VALUE,
    #: and spelling a member as a path instead hits ``treat_dot_as_module``, which reads
    #: the dot as a module qualifier.  Probed on the pinned version --
    #: ``TypeRef("typing.Literal", container="alias", of=(TypeRef("X.A"), TypeRef("X.B")))``
    #: renders ``Literal[A, B]``, both members' qualifier gone -- so the subscript is
    #: composed in ``render.py`` exactly as ``container="alias"``'s is, and for the same
    #: stated reason: the walk decides the enumeration and the members, the renderer
    #: writes the text.
    #:
    #: Python IDENTIFIERS and not the document's values: they are the names
    #: ``lower.enum.member_name`` minted on the DECLARING side, so a member here is a
    #: name that module already binds.
    members: tuple[str, ...] = ()
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
    #: case, and it rides as ``json_schema_extra`` so the fact reaches the class at
    #: the node the document states it at.  The two are exclusive by
    #: construction (:class:`Decided`): a format is in the type or in here, and
    #: never in both and never nowhere.  Dropping it would lose a fact the
    #: document states.
    format: str | None = None
    #: **§7's ``validators`` slot: the rules bound to THIS TYPE, as INSTANCES of the
    #: runtime's own frozen value-rule kinds** (``AtLeastOne``, ``NotValue``,
    #: ``Distinct``).  §2's "Where a rule hangs": on the nearest class if there is one,
    #: and "where no class sits above the value -- a root array, a mapping value, a
    #: ``definitions`` entry, a union branch -- the rule hangs off the value's own
    #: annotated type as an after-validator".
    #:
    #: The same carrier as :attr:`facts` and for the same reason: a rule on a type
    #: travels with it into ``list[...]``, into a mapping value and into a union branch,
    #: which is exactly the set of places that have no field and no class.  Declared as
    #: VALUES, like :attr:`ClassDecl.rules`, so the kinds are declared once in
    #: ``adcp.types._runtime`` and ``codegen.render`` writes the call.
    #:
    #: A tuple and not a set: the order is the document's, so the rendered annotation is
    #: a function of the document's content (P7).
    validators: tuple[ValueRule, ...] = ()


@dataclass(frozen=True)
class Decided:
    """What the walk decided one schema node IS.

    ``format`` is set only when ``type`` does NOT already carry the format -- the
    compiler then states it as an annotation rather than as a type.  Keeping the
    two separate here is what makes the drop impossible to make by accident: a
    format is either in the type or in this field, and never nowhere.

    **Declared HERE and not in ``codegen/compiler.py``, which is §14 step 10's own move**
    (``adcp-client-python-3be.6``, after ``3be.5`` measured what blocked it).  Three
    reasons, and the third is the one that forced it:

    * it is what §11's table already says.  The decision layer's output is
      "``Node`` -> ``Lowering``", and §7 declares this module as the layer that holds
      "what the walk DECIDED, as values".  A node's decision is the IR's own vocabulary:
      every field of this class is a :class:`TypeRef` or a fact about one.
    * every handler returns one and the walk's own carrier does not.  ``Module`` is the
      walk's mutable accumulator and this is a frozen value; one module holding both put
      the seam's TYPE behind an import of the walk's state.
    * ``lower/names.py`` could not construct one.  Its arrow to ``compiler`` is
      ``TYPE_CHECKING``-only while ``compiler`` imports it at module level (D13), so a
      runtime ``compiler.Decided`` there turns a reported cycle into a real one -- which
      is exactly why ``3be.5`` left ``lower_node``'s wrapper in ``compiler.py`` and said
      so.  This module imports nothing of ``codegen`` at all, so naming it from
      ``names.py`` adds no edge: it is the one place in the package every layer may
      already reach.
    """

    type: TypeRef
    constraints: dict[str, Any] = field(default_factory=dict)
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
    #: ``unique_items`` in v2, so no annotation states the fact.  Rendering it where
    #: the document states it is what keeps the two halves agreeing: the rule refuses a
    #: duplicate on the constructor and the channel carries the keyword at the pointer
    #: the document states it at, so nothing of the fact is owed a declaration.
    distinct: bool = False
    #: §6's ``deprecated`` row, which §14 step 8 and the ``deprecated`` row of the epic
    #: write the emitter half of.  Declared here because §7 declares it; nothing writes
    #: it yet and the renderer reads nothing from it, so flipping the cell to rendered
    #: is one handler change against a slot that exists.
    deprecated: bool = False


@dataclass(frozen=True)
class ClassDecl:
    """One decided class.  ``ref`` is the schema it will carry and grade against.

    **``ref`` is ``None`` for a class that names no document**, and that is the whole of
    ``codegen/lower/envelope.py``'s row: a base synthesised for a family of nodes that
    do NOT share an accepted set carries ``context``, ``errors`` and ``ext`` for a
    consumer to program against and claims nothing about any document.  §9 of the
    architecture document pairs a class with "the node its ``__adcp_schema__`` names", so
    a class with no reference is not in the pairing at all -- it is not graded, nothing
    draws for it, and ``strict_validate`` does not resolve on it.  The concrete classes
    of the family keep their own ``ref`` and remain the things §8 grades, which is what
    makes the base safe: the authority stays with the document.

    ``AdCPBaseModel``, ``BranchDispatchMixin`` and ``RuleBound`` are the precedent --
    three bases the tree already carries, none of which names a document -- and the one
    thing this slot adds is that the compiler can now DERIVE such a base rather than only
    inherit a hand-written one.
    """

    name: str
    ref: SchemaRef | None
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

    def __post_init__(self) -> None:
        """**A base list naming one class twice RAISES** (``architecture.md``, 2026-10-29).

        §2's division decides which of the two this is: "a refusal is the document's and a
        broken invariant is ours".  Nothing a document can state produces a duplicate base
        -- a composition names conjuncts, a union base names ``BranchDispatchMixin`` and
        ``AdCPBaseModel``, a branch names its base, and in every case the list is a
        function of what the WALK derived from them -- so the reader of such a report would
        go to ``codegen/`` and not to the schema.  An exception at the pointer is loud and
        honest where a refusal would be quiet and wrong: ``class X(Indicator, Indicator)``
        is ``TypeError: duplicate base class`` at IMPORT, three test files away from the
        walk that built it, and it charges a document that did nothing wrong.

        **Here and not in ``lower.composition.dispatching_bases``**, which ``adcp-client-python-10l.105``
        measured: that function is called from two sites (``compiler``'s distribution arm
        and ``lower/union.py``) and is not the chokepoint every base list passes through.
        This is -- every class declaration constructs one, on every route.

        **And it fires on BOTH spellings of the list, which is why it is in
        ``__post_init__`` rather than at the call sites.**  A base travels as a POINTER
        until ``lower/names.py`` binds it (:attr:`bases`' own note), so two DISTINCT
        pointers naming one class are a duplicate only after binding -- and
        ``names._bound`` rebuilds the declaration with ``dataclasses.replace``, which runs
        this.  ``adcp-client-python-10l.98``'s own defect was exactly that shape: two
        pointers, one symbol, caught at neither call site.

        Keyed on ``TypeRef.path``, because that is the symbol ``render.klass`` writes into
        ``base_classes`` -- the name Python will see -- and not on the ``TypeRef``, two of
        which can differ in a slot the base list does not render.
        """
        seen: list[str] = []
        for base in self.bases:
            if base.path in seen:
                raise BuildFailure(
                    f"{self.name}: the base list names {base.path!r} twice "
                    f"({[b.path for b in self.bases]}); section 2 makes a duplicate base "
                    "a broken invariant of the compiler and not an outcome of "
                    f"{self.ref.document if self.ref is not None else 'any document'}"
                )
            seen.append(base.path)


@dataclass(frozen=True)
class Member:
    """One decided enumeration member: the name the walk chose, and its value."""

    name: str
    value: Any
    #: The document's ``enumDescriptions`` entry for this value, where it has one.
    #: It reaches the rendered class as the member's own docstring, which is the
    #: renderer's own slot for it -- 137 of the bundle's enum nodes carry the
    #: block and a previous attempt dropped every one of them, for the same
    #: reason a hand-rolled renderer dropped 142 property descriptions: nothing the
    #: harness draws or validates reads an annotation that changes no accepted set, so
    #: only a reader of the emitted module notices the loss.
    description: str | None = None
    #: **The member's SECOND spelling: the value verbatim, as a class-body line beside
    #: the canonical one** (``adcp.types._base.MemberAlias``), or ``None`` where the
    #: spelling cannot be an attribute of this class.
    #:
    #: ``docs/plan/final-state.md`` reading 10 at ATTRIBUTE granularity.  Our members are
    #: ``UPPER_SNAKE`` and ``datamodel-code-generator``'s are the value verbatim;
    #: ``core/error.json`` states the value list ``transient|correctable|terminal`` and
    #: nothing about the attribute a caller types, so neither spelling is the document's
    #: and carrying both widens nothing -- ``Recovery.transient is Recovery.TRANSIENT``,
    #: ``__members__`` unmoved, no value set touched, no fact attributed.
    #:
    #: ``None`` is one of :data:`codegen.lower.enum.ALIAS_REFUSALS`' three cases and is
    #: never a silence: ``codegen.lower.enum.member_aliases`` is the one derivation and it
    #: returns the refusal beside the alias, so a spelling upstream has and we do not is
    #: COUNTED.  Defaulting to ``None`` is also what keeps a hand-built ``Member`` free of
    #: one: the spelling is decided over a whole member SET (the collision cases are
    #: about the other members' names) and cannot be read off one member alone.
    alias: str | None = None


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
    #: The module-level VALUE LIST this enumeration's members are read OUT OF, as the
    #: expression that names it, or ``None`` where each member's value is written beside
    #: it.
    #:
    #: ``docs/plan/architecture.md`` §3a: "the **VALUE LIST** is a module-level constant in
    #: the catalogue layer, written once per distinct member set; the **NAMED TYPE** is
    #: constructed from it at each position that needs one, keeping the name §4 derives and
    #: keeping the types distinct."
    #:
    #: **IT IS STILL A CLASS STATEMENT, and §3a's correction of 2026-11-02 is why**: "ONE
    #: TYPE IS A CLASS STATEMENT ... a functionally-built enum has no slot for the class
    #: docstring pydantic renders as ``description``".  The functional
    #: ``StrEnum('<Name>', …)`` call is ONE way to construct a type from a value list and
    #: is not the rule, and it costs a third thing the correction did not price: **a
    #: consumer's type checker cannot read its members.**  Measured against a wheel --
    #: ``CatalogAction.CREATED`` is ``error: "type[CatalogAction]" has no attribute
    #: "CREATED"  [attr-defined]`` -- which is a regression in reading 7, *the package
    #: declares its types to a consumer's type checker*, a reading that HOLDS.
    #:
    #: So the member's NAME is a class-body statement, which every checker reads, and only
    #: its VALUE is the expression ``<values>[<i>]`` -- the index being the member's own
    #: position in the value list, which is the document's order.  The rendering keeps the
    #: model layer's two docstring slots, the JSON Schema pydantic renders is byte-identical
    #: to the literal form's, and nothing is restated: the value is written once, in the
    #: constant.
    values: str | None = None


@dataclass(frozen=True)
class ValuesDecl:
    """``<name>: tuple[<base>, ...] = (…)``: ONE value list, written once.

    §3a: "the **VALUE LIST** is a module-level constant in the catalogue layer, written
    once per distinct member set; the **NAMED TYPE** is constructed from it at each
    position that needs one, keeping the name §4 derives and keeping the types distinct."

    **The VALUES and nothing else.**  It carried ``(member name, value)`` pairs while the
    types over it were built by the functional ``StrEnum('<Name>', …)`` call, which names
    members from what it is handed; a class statement names them itself
    (:attr:`EnumDecl.values`), so the member name belongs to the type and the list is the
    value list the reading is worded on.

    It declares a NAME and is not a type, which is why it is a declaration of its own
    rather than a slot on :class:`EnumDecl`: the constant is written once and the
    enumerations that read members out of it are written per position, and a slot would
    make the first position's declaration carry the others' shared text.
    """

    name: str
    #: ``"string"`` or ``"integer"``, in JSON Schema's words -- :attr:`EnumDecl.kind`'s
    #: own spelling, because the two always agree and the annotation is written from it.
    kind: str
    values: tuple[object, ...]


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

    Three rows of the semantics document reach it: section 5's ``items`` row at ROOT
    ("array -> ``RootModel[list[X]]``"), section 4's mixed-root-union row ("A ``Union`` at
    ROOT mixing the two lowers to a ``RootModelDecl`` over the union of the branches'
    types, with the class branches declared beside it and the dispatch facts on the root
    model"), and section 7's registry row ("a root stating only these keys is a permissive
    root model").

    **It HAS a producer and the tree carries its output.**  This docstring was written
    when it did not -- "declared here with no producer", on the precedent
    ``Field.deprecated`` and ``ClassDecl.branches`` set, which is why section 14 orders
    the structure before the rows -- and section 14 step 9 has since landed.  The READING
    rather than a count: ``codegen/compiler.py`` is the one mint site, and a module of
    the emitted tree declares a root model exactly where it names
    :data:`codegen.render.ROOT_MODEL` in a base list, so
    ``grep -rl AdCPRootModel`` over a fresh tree is the census and it is not empty.
    ``codegen/render.py`` renders the declaration and ``tests/test_approximation.py``
    grades that rendering against a hand-built one, so the path from a declaration to
    text is exercised independently of which handler writes it.

    *Why a declaration of its own and not a ``ClassDecl`` with a flag.*  A root model's
    body is a ``root:`` annotation and a class's is a field list, so the two differ in
    what the renderer writes rather than in a property of one shape; and section 7's table
    gives them separate rows.  ``rules`` is on both because section 8 of the architecture
    document requires it -- "each must carry ``__adcp_schema__``, ``strict_validate`` and
    a rule tuple exactly as a class does, or a root model and a class disagree about what
    their document accepts".

    The runtime base a renderer writes it through is ``AdCPRootModel``, which section 8 of
    the architecture document declares and ``src/adcp/types/_base.py`` carries.  The
    emitted modules import it: the sentence here used to say none did, which stopped being
    true when step 9 landed the handlers.
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
Declaration = (
    ClassDecl | EnumDecl | ValuesDecl | AliasDecl | RootBinding | RootModelDecl | UnionInstall
)


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
    #: **It was EMPTY over the whole bundle at §14 step 8**, which was that step's exit
    #: condition -- the instrument existed, no cell widened, and the emitted tree did not
    #: move.  Step 10 widened the cells and it is populated now.  The READING, so a figure
    #: here cannot go stale: ``./check``'s third line prints how many facts in how many
    #: documents the run declares, and ``tests/test_the_declared_backlog.py`` holds the
    #: equality between what the run mints and what the tree declares.
    approximations: tuple[Approximation, ...] = ()
    #: **The pointers of this document that name an ENTRY of a ``definitions`` / ``$defs``
    #: section**, which is the one fact ``render.declared_at``'s distribution needs beyond
    #: a pointer: a declaration inside such an entry is CONTAINED by the root's pointer and
    #: describes no instance location the root's own class can reach, so §8 gives it to the
    #: entry's own pair (``harness.locations``) and the obligation's walk refuses it at the
    #: root (``harness.check_widening``: "the pointer describes no instance location").
    #:
    #: Carried as a set of POINTERS rather than as the document, because the renderer may
    #: not know a node (§11) and because a segment reading ``definitions`` is a section only
    #: at a KEYWORD position -- a reading of the document, made once, by
    #: ``bundle.section_entries``.  ``compiler.Module.sections`` is where it is filled and
    #: carries the whole of why.
    #:
    #: Empty by default, exactly as :attr:`approximations` is: a module built outside a run
    #: has no census, and the fail-safe is the containment every declaration already had.
    sections: frozenset[str] = frozenset()
    #: **§1's EXPORT SET for this module**: the symbol the domain surface re-exports ->
    #: which of §1's three kinds it is (``root``, ``branch`` or ``alias``).
    #:
    #: Recorded by ``lower/names.py``'s pass, which is the one place a position's hop and
    #: its declaration are both in hand (``names.the_surface_exports``), and carried here
    #: so that the domain surface, §1's domain-scope collision rule and the check that
    #: grades them all read ONE answer.  A second derivation over the emitted text is what
    #: this replaces and it was measured wrong: reading a branch as "a class one of whose
    #: bases this module declares" misses a nested ``A | B`` union's arms, which subclass
    #: nothing local -- ``core/targeting_overlay_support.py``'s ``PlacementSelection`` and
    #: ``core/placement_definition.py``'s ``FormatOptionReference`` are two, and both are
    #: §1 collisions a check reading the text could not see.
    #:
    #: Keyed by SYMBOL and not by pointer, because what §1 forbids two of is a NAME and
    #: the surface re-exports names; the pointer is in :attr:`symbols` for a reader who
    #: wants the node.
    #:
    #: **Every member of it is a DECLARATION** (§1, 2026-11-03): where one of §1's three
    #: kinds falls on a position that only NAMES a class another position declares, the
    #: export is relocated onto the declaring position, because "a position that references
    #: a class does not name it".  :attr:`binds` is the record that reading is made on.
    exports: Mapping[str, str] = field(default_factory=dict)
    #: **§1's BINDINGS**: every symbol this module binds to a declaration made somewhere
    #: else -> the symbol it names.  ``X = Y`` and nothing more: §4's identity binding at
    #: the second position of one node, and the cross-document ``$ref`` at a named node.
    #:
    #: §1 (2026-11-03): "**A gate on this counts DECLARATIONS, not ``id()`` and not
    #: names** ... an ``X = <bare Name>`` is a binding, not a declaration."  A gate asking
    #: that the number of export paths equal the number of distinct declarations behind
    #: them cannot read that off the runtime -- the type system interns an ``Annotated``
    #: alias and an interned literal, so ``id()`` makes two independent declarations look
    #: like one -- and it cannot read it off the emitted TEXT either, for the reason
    #: :attr:`exports` already records. So the walk says which of its statements declare.
    #:
    #: **Every binding and not only the exported ones**, which is what keeps the gate
    #: honest after the repair: once no export path is a binding, a record holding only
    #: the exported ones would be empty and the check would pass by having nothing to
    #: range over.
    #:
    #: Keyed by SYMBOL for :attr:`exports`' reason, and the value is a symbol too, so a
    #: failure can name what the binding reaches.
    binds: Mapping[str, str] = field(default_factory=dict)


def symbols(decided: TypeRef) -> set[str]:
    """Every symbol a decided type names in the module that decided it.

    Read off the :class:`TypeRef` TREE rather than off any rendered text: a local arm
    is marked ``local`` where it is decided, so this enumerates the symbols instead of
    matching identifiers in an annotation and guessing which are types.  Two readers ask
    -- ``lower.composition._reused``, for the symbols a re-used inherited field needs importable,
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
