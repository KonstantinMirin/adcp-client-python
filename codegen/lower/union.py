"""D2's union row: a root ``oneOf``/``anyOf`` becomes a base plus one class per branch.

    class AccountRef(BranchDispatchMixin, AdCPBaseModel):
        __adcp_schema__: ClassVar[SchemaRef] = SchemaRef('core/account-ref.json', '#')
        _branch_models: ClassVar[tuple[type[AdCPBaseModel], ...]] = ()
        _ROOT_REQUIRED: ClassVar[tuple[str, ...]] = ()

        @classmethod
        def _branch_combinator(cls) -> str:
            return 'oneOf'

    class AccountRefAccountId(AccountRef): ...
    class AccountRefBrandOperator(AccountRef): ...

    AccountRef._branch_models = (AccountRefAccountId, AccountRefBrandOperator)
    AccountRef.model_rebuild(force=True)

**The root's name binds the BASE**, never a union alias, and that is the thing the
previous generator got wrong at scale: censused over the bundle's 156 union roots, 100
bound the root name to the alias, so a caller had nothing to ``isinstance`` against.
Here every referrer imports one symbol, the base carries ``strict_validate`` off
``AdCPBaseModel`` like any other class, and a received value comes back as the arm it
satisfies.  The mechanism is four parts and all four are in
``adcp.types._base.BranchDispatchMixin``, with the measurement for each beside it; this
module decides WHICH nodes get that shape and what the three emitted facts are.

``model_rebuild(force=True)`` is not optional and not a tidy-up: the branches subclass the
base, so they do not exist while the base is being built.  The mixin's hook returns the
base's own schema then, and the rebuild after the branch definitions is what installs the
union.

WHAT A BRANCH IS.  A branch is a class this module DECLARES, from the branch's own
``properties`` -- or, where the branch COMPOSES, from ``compiler.lower_composition`` with
this base as its ``bases``, which is the one case that was on the list below and left it
(``salesagent-j3k2l.40``).  Everything else refuses by name, pointer and keyword, because
§7's done-when for this step is *one subclass per branch* and each of these has no
subclass to give:

* a bare ``$ref`` branch.  Its member would be the TARGET's class, which does not descend
  from this base, so ``isinstance(payload, Base)`` would be false for that arm; declaring
  a subclass of both would be a second name for the target's node (P2) and would inherit
  the target's ``__adcp_schema__``, which points at another document.  Measured cost: 5 of
  the 44 documents that pass this module's keyword screen, all five entirely bare-ref;
* a ``required``-only overlay, which constrains requiredness and nothing else: that is a
  rule on the root's class (D2, D6), step 7's row;
* a scalar or array branch (step 6, D2), a nested ``oneOf``/``anyOf``/``not``/``if``, or an
  ``enum``.  A branch carrying a bare ``const`` is a SCALAR branch and is refused as one:
  the ``const`` pins the branch's whole value, so there is no property map to declare a
  subclass from.  D2's ``const`` row (``codegen.lower.const``) decides a branch's
  PROPERTIES, which is where the discriminating pin sits, and this module no longer
  carries a copy of it.

An ``allOf`` conjunct list used to be the fourth entry here and is not one: it was never
unlowerable, only unreachable.  The conjuncts sit at the branch's own node, so the grader
has a pointer for every one of them, and what was missing was that the conjunct reader
lived in the product row where D13 keeps a lowering from importing it.  The reader is
``compiler.lower_composition`` now, so a composing branch is a class like any other --
the union base FIRST, because ``isinstance(payload, Base)`` depends on it, and the
conjuncts' own bases after.  The branch's ``type`` is still read BEFORE its conjunct
list, because a branch whose type is not an object cannot be a class whatever else it
states -- see :func:`_plan`.

WHAT THE ROOT MAY NOT CARRY, and this is the one refusal that is about the GRADER rather
than about a missing lowering.  A root ``allOf``, ``properties``, ``required`` or
``additionalProperties`` applies to the whole document in draft-07, so it is a
CONJUNCTION with every branch -- and for ``allOf`` that is D7's own wording.  A branch
class inheriting those fields is the faithful reading of the document, and it is also
unreportable: the branch's own ``__adcp_schema__`` names ``#/<kw>/<i>``, that node states
none of the root's facts, and the schema comparison correctly reports the inherited ones
as facts the model adds.  There is no JSON pointer to the conjunction, so there is nothing
for the branch to name instead.  Emitting it is the row for a step that can name a
conjunction; here it refuses.  Measured cost: 4 of the 44 for the three object facts, and
41 documents for ``allOf`` -- 37 of whose conjuncts reference ``core/version-envelope.json``
and 33 ``core/protocol-envelope.json``, which is D7's envelope pair on the task-response
documents D7 names.  **D7 reads the other way about those 41, so the conflict is recorded
at ``ROOT_CONJUNCTS`` with the probe that decided it rather than resolved by preference.**

The consequence is that ``_ROOT_REQUIRED`` is ``()`` for every document this step emits --
a root with required fields declares the properties they name, and that refuses above.  It
is written anyway, because the mixin's refusal reads it and §4 states it, and it is graded
by a unit assertion rather than by the population.  Said here rather than discovered
later: the population grades 0 non-empty ``_ROOT_REQUIRED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codegen import compiler
from codegen.refusal import Kind, Refusal

#: What the ROOT of a union document may carry.  ``discriminator`` is an annotation in
#: draft-07 -- ``jsonschema`` has no validator for it, so ignoring it cannot make the model
#: wider than its document -- and it is READ here, as the property D3's rule 2 takes a
#: branch's name from.
#: The four conjuncts are HANDLED here so that the explicit refusal below is what reports
#: them, after every other keyword has been checked.  Left out of this set, they refuse
#: through ``compiler.check_keywords``, which walks ``sorted(node)`` -- so a root carrying
#: both ``additionalProperties`` and ``oneOf`` branches blocked by a later step's keyword
#: was reported against ``additionalProperties``, this module's own grader-driven refusal,
#: rather than against the keyword that is the reason.  Measured: the by-keyword profile
#: over the 156 read 55 ``additionalProperties`` / 42 ``allOf`` that way, and 0 / 55 this
#: way.  Attribution is the point of a refusal report, and the same principle
#: ``harness.violated_keywords`` is built on.
ROOT_HANDLED = frozenset(
    {"type", "discriminator", "properties", "required", "additionalProperties", "allOf"}
)

#: The root facts whose refusal is explained in the module docstring.  Checked after
#: ``compiler.check_keywords``, so a root blocked by a later step's keyword is reported
#: against it.
#:
#: **``allOf`` IS ONE OF THEM, and it was the entry that read as step 4's.**  A root
#: ``allOf`` is a conjunction with every branch for precisely the reason the other three
#: are -- D7 states it in those words -- so a branch class inheriting the conjuncts'
#: classes states facts its own ``#/<kw>/<i>`` node does not, and there is no pointer to
#: the conjunction for it to name.  It sat outside this tuple and refused through the
#: keyword screen with "a later D2 row does", which pointed at step 4's product row;
#: measured, that row claims 0 of these documents -- ``bundle.composes_at_the_root``
#: excludes a root carrying a union -- so the deferral named a row that was never going
#: to see them.
#:
#: FIRST in the tuple, so the keyword each of those documents is reported on does not
#: move: ``allOf`` is the structural fact (the document composes) where the other three
#: are the root's own inline facts, and it is the keyword D7 names.  Measured over the 41:
#: 30 declare ``properties: {}``, 2 declare no ``properties``, 9 declare a non-empty one.
#:
#: **Measured rather than assumed: binding the conjuncts as bases emits none of them.**
#: Probed by patching this row to do exactly that over all 41 -- 0 emit, and the blockers
#: are elsewhere: 35 refuse on the root ``properties`` below, 4 on a branch ``not``, 1 on a
#: branch ``type`` and 1 on ``dependencies``.  So the reachable population of a
#: conjunct-binding branch here is 0 today, which is the same ground D5 refuses an ``enum``
#: under ``propertyNames`` on and the product row omits a ``required``-only conjunct on.
#:
#: **And this entry is what keeps that honest once a branch stops refusing.**  Probed the
#: other way, by removing ``allOf`` from this tuple while the keyword screen above still
#: admits it: nothing emits today either, so the entry changes no accepted set now -- what
#: it changes is the REASON 37 documents are refused, from a deferral naming a row that
#: claims none of them to the fact above.  The widening it forecloses becomes reachable at
#: the first branch repair: ``_base.applied_schema`` conjoins an enclosing ``type``, which
#: by itself unblocks a branch in 17 of these 41, and without this entry such a document
#: would emit a base that drops its composed bases -- caught by the comparison as a
#: ``missing``, so a red gate rather than a named refusal.
ROOT_CONJUNCTS = ("allOf", "properties", "required", "additionalProperties")

#: What a BRANCH may carry and still be a class this module declares.
#:
#: D6's rule families are NOT listed here and are added per branch by
#: ``compiler.rules_at``, which is what keeps the distinction this module's docstring
#: draws: a branch's ``anyOf`` of ``required`` groups is a RULE on that branch's own
#: class, and a branch's ``oneOf`` of SHAPES is a nested union this row still refuses.
#: One predicate decides both (``rules.presence_only``, reached through the compiler
#: because a lowering cannot import a sibling lowering), so there is no second reading
#: for the two to disagree through.
#:
#: ``const`` and ``allOf`` are both in the set for ``ROOT_HANDLED``'s reason, and
#: neither because this module lowers one: left out, the keyword screen reports them
#: first with the generic "a later D2 row does", and an explicit refusal below says
#: what each actually is.  Attribution is the point of a refusal report.
#:
#: ``const`` at the BRANCH node pins the branch's whole VALUE, so the branch is a
#: scalar and the refusal that says so is :func:`_plan`'s ``type`` check.  The generic
#: deferral pointed at a row that already exists (D2's ``const`` row is
#: ``codegen.lower.const``, reached for every PROPERTY of a branch), which sent the
#: reader looking for the wrong thing.  Measured: 1 document,
#: ``core/start-timing.json``, whose two branches are a ``const`` and a
#: ``format: date-time``, both scalars.
#:
#: ``allOf`` at the BRANCH node is a conjunct list the branch's own pointer addresses,
#: so unlike the root case it is genuinely lowerable -- and it IS lowered:
#: :func:`lower_union` hands such a branch to ``compiler.lower_composition`` with the
#: union base as ``bases``.  The keyword is in this set so the screen admits it; the
#: dispatch at the bottom of :func:`lower_union` is what reads it.
#:
#: ``enum`` is here for ``const``'s reason exactly, and the module docstring already
#: lists an ``enum`` branch among those that have no subclass to give: it pins the
#: branch's VALUE SET, so there is no property map to declare a class from, which makes
#: it a scalar branch and :func:`_plan`'s ``type`` check the refusal that says so.
#: Measured over all 126 union roots of this bundle: **2 branches carry an ``enum`` and
#: both state ``type: "string"``** -- ``core/geo-place-system.json#/anyOf/0`` and
#: ``core/geo-place-type.json#/anyOf/0``.  Left out of this set, both were reported on
#: ``enum`` with ``DEFERRED_TO_A_LATER_ROW``, because ``compiler.check_keywords`` walks
#: ``sorted(node)`` and reaches ``enum`` before the ``type`` check below -- the
#: identical misattribution :data:`ROOT_HANDLED` measured at 55 of 156 and fixed the
#: same way, and a deferral promising a row for a branch shape this module refuses by
#: design.
BRANCH_HANDLED = frozenset(
    {"type", "properties", "required", "additionalProperties", "const", "enum", "allOf"}
)


#: The two union keywords, in the order a root carrying one is read.
UNION = ("oneOf", "anyOf")


def keyword(doc: dict) -> str | None:
    """The union keyword at this document's ROOT, or ``None``.

    ONE reading, and it lives HERE because the DISPATCH SELECTOR
    (``bundle.union_root``) is built on it: the selector is this step's population
    test, so a row cannot claim a document its lowering reads differently.  The lane
    had this function in ``codegen.bundle`` and the lowering importing it from there,
    which D13's import rule forbids -- a lowering imports ``compiler`` and
    ``refusal`` and nothing else of this package -- so the dependency is inverted and
    ``bundle`` reads this, the way ``states_an_object_rule`` reads
    ``rules.presence_only``.

    A root carrying BOTH keywords would be ambiguous; the bundle has 0 of them and
    the keyword check below refuses one anyway, because the first would be handled
    and the second left unmentioned.

    **This answers "which keyword", not "is this document step 5's".**  A combinator
    of ``required`` GROUPS carries one of these keywords and is a RULE on one class
    (D6, step 7) rather than a union: a branch declaring no property has no shape to
    subclass, which :func:`_plan` refuses by name.  Which ROW owns such a document is
    a fact about the selectors and is decided in ``bundle.union_root``, where both
    steps' readings can be consulted -- a lowering imports ``compiler`` and
    ``refusal`` and nothing else of this package (D13), so it cannot read step 7's.
    """
    return next((kw for kw in UNION if isinstance(doc.get(kw), list)), None)


# --------------------------------------------------------------------------- #
# D3: which rule names a branch
# --------------------------------------------------------------------------- #
def _const_pin(branch: dict, doc: dict) -> Any:
    """The ``const`` this branch pins on the discriminating property, or ``None``.

    The property is the root's ``discriminator.propertyName`` where it declares one, and
    otherwise the branch's single ``const``-pinned property.  Two pins and no
    ``discriminator`` is ambiguous and falls through to the next rule rather than taking
    the alphabetically first, which would make a class name a function of spelling.
    """
    props = branch.get("properties")
    if not isinstance(props, dict):
        return None
    pinned = {k: v["const"] for k, v in props.items() if isinstance(v, dict) and "const" in v}
    named = (doc.get("discriminator") or {}).get("propertyName")
    if isinstance(named, str) and named in pinned:
        return pinned[named]
    return next(iter(pinned.values())) if len(pinned) == 1 else None


def branch_identity(branch: dict, root: str, doc: dict) -> str | None:
    """D3's three branch rules, or ``None`` where none of them applies.

    Split out of :func:`branch_name` because the two callers need the SAME three rules
    and differ only in what "no identity" means.  A ROOT union declares one class per
    branch, so a branch with no identity is a document this emitter cannot name and
    :func:`branch_name` refuses it.  A NESTED union is a TYPE (:func:`nested`), and a
    branch that lowers to an annotation -- a scalar, a ``$ref``, an array -- needs no
    name at all, so refusing one there would refuse a union the walk can lower.

    It is one function and not two copies of the three rules for the ordinary reason:
    the rules ARE D3, and a second reading of them is how the two positions come to
    name one branch differently.
    """
    title = branch.get("title")
    if isinstance(title, str) and title:
        return compiler.class_name(title)
    pin = _const_pin(branch, doc)
    if pin is not None and not isinstance(pin, (dict, list)):
        return root + compiler.class_name(str(pin))
    required = branch.get("required")
    if isinstance(required, list) and required:
        return root + "".join(compiler.class_name(str(k)) for k in sorted(required))
    return None


def branch_name(branch: dict, root: str, pointer: str, doc: dict) -> str:
    """D3's branch rules, in order: title, the discriminator ``const``, the required set,
    then refuse the document by name and pointer.

    A title names itself.  A ``const`` or a required set is prefixed with the ROOT's name,
    so a branch named by either shares its base's spelling.  The required-set key is
    deliberate: it is stable when the spec adds an OPTIONAL field and renames exactly when
    requiredness changes, which is a semantic change a caller should meet as an
    ``ImportError`` rather than as a silent repoint.

    **A name is never derived from the neighbourhood.**  The rule a previous generator
    reached for -- name the sole classed branch after its PARENT -- makes a class name a
    function of what its siblings happen to be, so adding a branch renames an unrelated
    class.  D3 has no such rule and this refuses instead.
    """
    named = branch_identity(branch, root, doc)
    if named is not None:
        return named
    raise Refusal(
        "title",
        pointer,
        "no title, no discriminator const and no required set: this branch has no "
        "identity to derive a name from, and D3 refuses rather than naming it after "
        "its siblings",
        kind=Kind.VERDICT,
    )


# --------------------------------------------------------------------------- #
# the lowering
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Branch:
    """One branch's decided class: its name and its node.

    It carried a third field -- a per-property type this module had already decided,
    for the ``const`` on the discriminating property -- and that is gone with
    ``_literal``: D2's ``const`` row is ``codegen.lower.const`` now and the walk
    reaches it for every node, so a branch's properties are decided the way every
    other object's are.
    """

    name: str
    pointer: str
    node: dict


def lower_union(doc: dict, symbol: str, pointer: str, mod: compiler.Module) -> str:
    """Emit the base, the branches and the module trailer; return the base's symbol.

    ``pointer`` is D13's signature and is the ROOT's -- ``""`` -- for every call the
    table makes: a union is only ever a document root here, and a nested one is a
    later row.  It is read rather than ignored, so a nested call would name its own
    node.
    """
    kw = keyword(doc)
    assert kw is not None, "lower_union is dispatched on the keyword being present"
    # **A root D6 rule is the BASE's**, and the base is the one class every branch
    # descends from -- so draft-07's reading, that a root keyword applies to the whole
    # instance and therefore to every branch, is what class inheritance already says.
    # It is admissible where a root ``properties`` is NOT (``ROOT_CONJUNCTS`` below)
    # because the reason that one refuses is the GRADER: a branch class carrying an
    # inherited field states a fact its own ``#/<kw>/<i>`` node does not, and the
    # schema comparison correctly reports it as added.  A rule renders NOTHING in a
    # model's JSON schema, so there is no fact for the comparison to gain, and the
    # instrument that observes a rule is a direct ``model_validate``.
    #
    # ``rules_at`` subtracts the two combinators from a root whose branches are
    # shapes, so the union keyword arrives through ``{kw}`` alone and a root carrying
    # BOTH ``oneOf`` and ``anyOf`` still refuses on the second -- which is what the
    # docstring of :func:`keyword` says it does, and the bundle has 0 of them.
    stated = compiler.rules_at(doc)
    compiler.check_keywords(doc, pointer, ROOT_HANDLED | {kw} | stated.screen)
    for name in ROOT_CONJUNCTS:
        if name in doc:
            raise Refusal(
                name,
                pointer,
                f"a root {name!r} is a conjunction with every branch (draft-07), and a "
                f"branch class that carries it -- as a field of its own, or as a base "
                f"inherited through the root's class -- states a fact its own "
                f"#{'/' + kw}/<i> node does not: there is no pointer to the conjunction "
                "for it to name",
                kind=Kind.VERDICT,
            )
    if doc.get("type") not in (None, "object"):
        raise Refusal(
            "type",
            pointer,
            f"a union root of type {doc['type']!r} is step 6",
            kind=Kind.DEFERRED,
        )
    branches = doc[kw]
    if len(branches) < 2:  # noqa: PLR2004 -- a union of one is not a union
        raise Refusal(
            kw, pointer, f"{len(branches)} branch: a union of one is the branch itself, not a union"
        , kind=Kind.VERDICT)

    planned = [
        _plan(branches[i], f"{pointer}/{kw}/{i}", symbol, doc) for i in range(len(branches))
    ]
    names = [p.name for p in planned]
    if len(set(names)) != len(names):
        raise Refusal(
            "title",
            pointer,
            f"two branches derive the same class name: {sorted(n for n in names if names.count(n) > 1)}",
            kind=Kind.VERDICT,
        )

    mod.imports.add((compiler.BASE_MODULE, "AdCPBaseModel"))
    mod.imports.add((compiler.BASE_MODULE, "BranchDispatchMixin"))
    mod.imports.add(("typing", "ClassVar"))
    mod.imports |= stated.body.imports
    description = doc.get("description")
    rendered = compiler.render(
        compiler.Class(
            name=symbol,
            ref=compiler.schema_ref(mod.document, pointer),
            properties=(),
            description=description if isinstance(description, str) and description else None,
            bases=("BranchDispatchMixin", "AdCPBaseModel"),
            body_lines=(
                "_branch_models: ClassVar[tuple[type[AdCPBaseModel], ...]] = ()",
                # Always empty in this step's population, and written anyway: the mixin's
                # refusal reads it, and a root with required fields refuses above.
                "_ROOT_REQUIRED: ClassVar[tuple[str, ...]] = ()",
                # No blank line between the attributes and the method: dmcg indents every
                # body line, so an empty one renders as trailing whitespace.
                "@classmethod",
                "def _branch_combinator(cls) -> str:",
                f'    return "{kw}"',
                # The root's own rule, which every branch inherits.  Last, because the
                # compiler indents each body entry and a multi-line entry after the
                # method reads as part of neither.
                *(line for line in (stated.body.text,) if line),
            ),
        )
    )
    mod.add(symbol, pointer, rendered)

    for plan in planned:
        # A branch that composes is lowered by the conjunct reader and a branch that
        # does not by the object row, and both take the union base as ``bases`` -- the
        # one argument that makes the branch answer ``isinstance(payload, Base)``.  The
        # dispatch is on the keyword the branch carries and not on a field of
        # :class:`Branch`: ``_plan`` has already admitted the keyword set, so the node
        # is the only thing that decides which reader reads it.
        lower = compiler.lower_composition if "allOf" in plan.node else compiler.lower_object
        lower(plan.node, plan.name, plan.pointer, mod, bases=(symbol,))

    # The module trailer.  Two statements beside the classes, which is the module writer's
    # own text (§3: no compiler template has a slot for a line beside a class), and they
    # declare no name -- so they are appended rather than declared.
    mod.blocks.append(
        f"{symbol}._branch_models = ({', '.join(names)},)\n{symbol}.model_rebuild(force=True)"
    )
    return symbol


# --------------------------------------------------------------------------- #
# the same keyword BELOW a root, which is a TYPE and not a base plus subclasses
# --------------------------------------------------------------------------- #
#: Why a nested union's SIBLING refuses, and why it is a verdict rather than a
#: deferral.  The sentence is :data:`ROOT_CONJUNCTS`' reasoning at a nested pointer, and
#: the mechanism it names is different: a root's branches are CLASSES and the fact is
#: unreportable because a branch's ``#/<kw>/<i>`` node does not state it, while a nested
#: union is one TYPE and there is no slot on a ``compiler.Type`` for a sibling fact at
#: all.  Both ends of that were measured on the pinned harness: the document states the
#: sibling at this pointer and ``harness.compare_schema`` looks for it here, so a model
#: whose node is a bare ``anyOf`` reports it ``missing`` -- a model wider than its
#: document, by the keyword's own position.
_NESTED_SIBLING = (
    "a sibling of a nested oneOf/anyOf is a CONJUNCTION with every branch (draft-07), "
    "and a nested union lowers to one type -- A | B -- which has no slot for a fact of "
    "its own: compiler.Type carries a container and its members and nothing else.  "
    "Conjoining it into each branch instead states it at a pointer the document does "
    "not, and dropping it is a model wider than its document, which "
    "harness.compare_schema reports as a missing fact at this very pointer.  The "
    "position needs a row that can NAME the conjunction, which is the same thing a "
    "root union's ROOT_CONJUNCTS refuses for"
)


def nested(node: dict, pointer: str, name_hint: str, mod: compiler.Module) -> compiler.Decided:
    """``A | B`` for a ``oneOf``/``anyOf`` at a pointer that is NOT a document root.

    **It is not the root row's shape and must not be.**  A root union emits a base
    carrying ``BranchDispatchMixin`` and one subclass per branch because a DOCUMENT must
    export one importable symbol that answers ``isinstance`` for every arm (§4).  A
    nested position exports nothing: it is a property's type, an element type or a
    mapping value, so what it needs is a TYPE -- which is exactly what
    ``lower.containers.multi_type`` already builds for a ``type`` LIST, through the same
    ``compiler.Type(container="union", ...)``.

    It is reached from ``emit.decide_type`` and NOT through ``emit.ROWS``, for the
    reason the nested ``allOf`` arm beside it is: ``ROWS`` dispatches on ROOT KIND and
    is a partition by it, so a keyword at a position no root selector sees has no row to
    be and no selector to select it.  Measured on the 3.2 bundle, of the NODE'S POSITION
    and not of the document: of the 32 deferred nested combinators **0 sit at a root**,
    so no root selector sees one and a row would have claimed none.  (Asked of the
    document instead, 2 of the 32 have a root ``bundle.union_root`` already claims and 14
    have one ``composes_at_the_root`` claims -- a row claiming the document says nothing
    about the position inside it, which is the whole of why ``ROWS`` partitions by root
    kind.)  The other 4 of the 48 deferrals that DO sit at a root are all on
    ``uniqueItems`` at a root ARRAY, a kind ``bundle.is_container_root`` already claims.
    So ``ROWS`` stays six.

    **Each branch is decided by the same walk as any other node**, at its own
    ``<pointer>/<kw>/<i>``, which is what gives a branch that becomes a CLASS its own
    ``__adcp_schema__`` and therefore its own graded pair -- the root row's
    docstring states that mechanism and it is the one that grades these branches too.
    A branch's name is D3's (:func:`branch_identity`), and a branch with no identity
    needs none: it lowers to an annotation, and if it turns out to need a name anyway
    two branches collide and ``compiler.Module.declare`` refuses by name.

    **What this does NOT make as narrow as its document, named here rather than
    discovered later.**  ``A | B`` admits a value satisfying BOTH arms and a ``oneOf``
    refuses one, so the ``model_validate`` CONSTRUCTOR is wider than a ``oneOf`` at
    exactly that instance.  That is D4's standing trade and not a new one: the accepted
    set of every emitted class is ``strict_validate``, which validates against the
    document's own schema and so enforces the exclusivity, and ``lower/rules.py``
    records the identical ceiling for a conditional it cannot express as a rule.  A
    rule cannot close it either -- ``RuleBound`` reads ``__pydantic_fields_set__`` and
    exclusivity is a statement about values, not about which keys are present.
    """
    kw = keyword(node)
    assert kw is not None, "nested is dispatched on the keyword being present"
    # The sibling screen, with its own ``why``: every other keyword at this node is a
    # conjunction with every branch, and the generic answer for a draft-07 keyword
    # promises a later row for something no row can carry here.  Same shape as the
    # ``$ref`` arm's "a sibling of $ref, which draft-07 ignores".
    compiler.check_keywords(node, pointer, {kw}, _NESTED_SIBLING)
    branches = node[kw]
    if len(branches) < 2:  # noqa: PLR2004 -- a union of one is not a union
        raise Refusal(
            kw, pointer, f"{len(branches)} branch: a union of one is the branch itself, not a union"
        , kind=Kind.VERDICT)
    arms: list[compiler.Type] = []
    for i, branch in enumerate(branches):
        at = f"{pointer}/{kw}/{i}"
        if not isinstance(branch, dict):
            raise Refusal(
                kw,
                at,
                f"a branch is {type(branch).__name__}, not a schema",
                kind=Kind.VERDICT,
            )
        hint = branch_identity(branch, name_hint, node) or name_hint
        _refuse_a_local_reference_branch(branch, at)
        decided = mod.decide(branch, at, hint, mod)
        if decided.constraints or decided.format is not None:
            # The arm's own bound has nowhere to go: ``compiler.Type`` carries none, so
            # the keyword would reach the FIELD holding the union and bound every arm --
            # ``Annotated[str | int, Field(min_length=4)]`` applying a string's bound to
            # the integer arm, which is ``containers.multi_type``'s named defect at the
            # other spelling of the same shape.  D5's alias module is what puts a bound
            # on an arm's own type, and what reaches here still carrying one is a shape
            # it has no spelling for.
            stated = {
                **decided.constraints,
                **({"format": decided.format} if decided.format else {}),
            }
            raise Refusal(
                sorted(stated)[0],
                at,
                f"this branch states {stated} and compiler.Type carries no constraint, "
                "so the keyword would reach the field holding the union and bound every "
                "arm; D5's alias module names an arm's own bounded type and has no "
                "spelling for this shape",
                kind=Kind.DEFERRED,
            )
        arms.append(decided.type)
    _refuse_a_shape_the_comparison_cannot_read(node, kw, pointer)
    unique = tuple(dict.fromkeys(arms))  # document order, deduped
    if len(unique) == 1:
        # Two branches that lower to one type are one type, and saying ``X | X`` would
        # be a second spelling of it.  ``multi_type`` dedupes for the same reason.
        return compiler.Decided(unique[0])
    return compiler.Decided(compiler.Type(container="union", of=unique))


def _refuse_a_local_reference_branch(branch: dict, pointer: str) -> None:
    """A branch that is a LOCAL reference puts this document's own ``definitions``
    section in front of a comparison that has no reading for one.

    ``compiler.local_reference`` declares a class for the node the reference names --
    a node of THIS document -- and declares it if the walk has not reached it yet, which
    for a ``definitions`` entry nothing else reaches is this row's own doing.  The
    class then has its own ``__adcp_schema__`` and so its own graded pair.

    **What has no reading is the DOCUMENT side.**  ``harness._normalize`` resolves a
    ``$ref`` into ``$defs`` on the MODEL's side, and nothing resolves one on the
    document's: ``bundle.resolved`` inlines a REMOTE reference and leaves a local one
    in place, so the comparison reads a property whose document node is
    ``{"$ref": "#/definitions/x"}`` as stating no fact at all, and every fact the
    model's class correctly carries arrives as ``added`` -- the model reported NARROWER
    than its document, which is the half that could admit an instance the document
    rejects.

    Measured, and the first population the reading would ever have had: **0 graded
    pairs of the committed tree hold a document-side local ``$ref``**, while the two
    documents whose pairs hold one carry **24 sites over 4 pairs and produce 43
    ``added`` facts** -- 31 at ``core/placement-presentation.json``'s three
    ``#/definitions/*_decoration`` pairs, which THIS ROW'S branch lowering declares,
    and 12 at ``core/bidding-policy-capability.json#/definitions/scope_capability``,
    whose pair the root's own property declares in a document this row is the last
    blocker for.

    **What the guard COSTS is 4 emissions and not 2**, measured by removing it and
    re-emitting: ``core/bidding-policy-capability.json``,
    ``core/placement-presentation.json`` -- the two that produce the 43 -- plus
    ``core/canonical-media-buy-features.json`` and ``core/media-buy-features.json``,
    which reference them. It refuses 8 documents in all; the other 4 refuse on
    something else as well. 686 emitted with it, 690 without.

    **The limit of this predicate, stated rather than discovered.**  It asks about the
    NODE -- is this branch a local reference -- while what is ungradeable is the
    document's ``definitions`` section. The two coincide over all 6 documents of the
    bundle that carry a local-reference branch at a nested combinator, and the
    coincidence is NOT a derivation: a document carrying one with no ungradeable
    ``definitions`` position would be refused here for nothing.  The fix is the
    document-side reading in ``codegen/harness.py``, which is one instrument for both
    directions; widening the predicate here would admit the 43.
    """
    ref = branch.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#"):
        return
    raise Refusal(
        "$ref",
        pointer,
        f"a branch referencing {ref!r} names a node of THIS document, and "
        "compiler.local_reference declares a class for it whose own pair is then graded "
        "against a document side the resolver did not inline: bundle.resolved inlines a "
        "remote reference and leaves a local one, harness._normalize resolves a $ref on "
        "the MODEL's side only, and so every fact the class correctly carries is "
        "reported as added -- the model narrower than its document.  Measured: 0 graded "
        "pairs of the committed tree hold a document-side local $ref, and the two "
        "documents this admits produce 43 added facts over 4 pairs.  The document-side "
        "reading is the harness's row"
    , kind=Kind.DEFERRED)


def _bare_type(branch: dict) -> str | None:
    """The one ``type`` word this branch states and nothing else, or ``None``.

    The DOCUMENT-side spelling of the shape ``harness._normalize``'s third
    normalization fires on, read through ``compiler.ANNOTATIONS`` so a branch that
    carries only a ``description`` beside its type is still a bare type -- which is
    what the model renders, because an annotation changes no accepted set.
    """
    live = {k for k in branch if k not in compiler.ANNOTATIONS and not k.startswith("x-")}
    word = branch.get("type")
    return word if live == {"type"} and isinstance(word, str) else None


def _refuse_a_shape_the_comparison_cannot_read(node: dict, kw: str, pointer: str) -> None:
    """A union the comparison FOLDS is emitted ungraded, so this refuses it by name.

    **It is the grader and not the rendering, and the predicate is ``_normalize``'s own
    two fold arms read off the document.**  ``A | B`` is exactly what the document
    admits and pydantic renders it as an ``anyOf``.  ``harness._normalize`` then folds
    that ``anyOf`` away in two cases, each for a reason that is right about the model:

    * **one null branch and one live branch** -- D4 renders an optional property
      ``T | None``, so the fold unwraps the null arm and keeps the live branch's own
      keys (resolving a ``$ref`` into ``$defs`` on the way);
    * **at most one null branch and every live branch a bare ``{"type": X}``** -- a
      union of bare types is draft-07's multi-type node in pydantic's only spelling of
      one, so the fold restores the ``type`` LIST.

    Both are correct for a node whose DOCUMENT states those facts at the node. A nested
    combinator's node states them INSIDE a branch and nothing at the node itself -- a
    sibling refuses above -- so every folded fact arrives in ``compare_schema``'s second
    pass as a fact the model states and the document does not.  ``_narrows_nothing``
    admits a model-only ``type`` only where ``_entails_type`` derives it, and that
    derivation requires every branch to declare the SAME type, which is exactly the case
    neither fold arm is about.

    So the comparison reports a faithful model as NARROWER than its document. Measured
    over the committed tree, in two passes:

    * the bare-type arm: **5 ``added`` facts over 5 pairs**, all of them
      ``.../value/type: the model says ['boolean', 'number', 'string'], the document
      nothing`` -- the two documents that state the shape
      (``creative/creative-feature-result.json#/properties/value``,
      ``property/property-feature-value.json#/properties/value``) and the three that
      reference them;
    * the null arm: **4 ``added`` facts over 2 pairs**, at
      ``formats/canonical/{audio,video}_hosted.json#/properties/duration_ms_range/items``,
      whose ``anyOf`` is ``[{"type": "integer", "minimum": 0}, {"type": "null"}]`` and
      whose model folds to ``{"type": ["integer", "null"], "minimum": 0}``.

    ``added`` is the half that could admit an instance the document rejects, so it is 0
    over the whole committed tree and must stay 0; emitting a node no check can read is
    the widening this pipeline exists to remove.

    **The upgrade path is the harness's row and not this one's**, exactly as
    ``containers.multi_type``'s constrained-arm refusal says of its own shape: each fold
    is right that the two spellings are one fact, and what is missing is for the fold to
    be told that the facts it restored are the DOCUMENT's own, stated one level down
    inside the branch it folded.  ``codegen/harness.py`` is one instrument for both
    directions, so the reading belongs there and not in a wider rule here.

    **What this does NOT refuse, which is the whole reachable population:** a union with
    two live branches at least one of which states more than a type word -- a ``$ref``, an
    object, a constrained scalar, an array.  Neither arm folds it, the model's node stays
    an ``anyOf``, ``anyOf`` is not in ``harness.FACTS``, and each branch that became a
    class is graded at its own pair through its own ``__adcp_schema__``.  **8 of the 32
    documents in this family emit, and every one of the 8 is in that position**; the
    row's whole gain is 12 documents, the 10 of the 48 that emit plus 2 of the 30
    chained-pending refusals that cleared into emissions.
    """
    branches = [b for b in node[kw] if isinstance(b, dict)]
    nulls = [b for b in branches if _bare_type(b) == "null"]
    live = [b for b in branches if _bare_type(b) != "null"]
    unwraps = len(nulls) == 1 and len(live) == 1
    restores = len(nulls) <= 1 and len(live) > 1 and all(_bare_type(b) is not None for b in live)
    if not (unwraps or restores):
        return
    which = (
        "one null branch and one live one, which D4's own T | None renders"
        if unwraps
        else "every live branch a bare type, which is a type LIST in pydantic's only "
        "spelling of one"
    )
    raise Refusal(
        kw,
        pointer,
        f"this union is {which}, and harness._normalize folds exactly that shape off "
        "the model's side -- while this node states no such fact of its own, because a "
        "nested combinator states them inside a branch.  So the folded facts arrive as "
        "facts the model adds and the document does not, and _entails_type derives a "
        "model-only type only where every branch declares the SAME one: a faithful model "
        "is reported NARROWER than its document and the node would be emitted ungraded.  "
        "Teaching the fold that the facts it restored are the document's own, one level "
        "down in the branch it folded, is the harness's row",
        kind=Kind.DEFERRED,
    )


def _plan(branch: Any, pointer: str, root: str, doc: dict) -> Branch:
    """What one branch becomes, or the refusal that says why it becomes nothing."""
    if not isinstance(branch, dict):
        raise Refusal(
            "oneOf",
            pointer,
            f"a branch is {type(branch).__name__}, not a schema",
            kind=Kind.VERDICT,
        )
    live = {k for k in branch if k not in compiler.ANNOTATIONS and not k.startswith("x-")}
    if live == {"$ref"}:
        raise Refusal(
            "$ref",
            pointer,
            "a bare $ref branch has no node to declare a subclass from: the member would "
            "be the target's own class, which does not descend from this base, so the "
            "arm would not answer isinstance",
            kind=Kind.VERDICT,
        )
    # The branch's own D6 rules: the keywords are admitted here and the TUPLE is
    # written by ``compiler.declare_object``, which ``lower_object`` below reaches.
    compiler.check_keywords(  # the walk's own check
        branch, pointer, BRANCH_HANDLED | compiler.rules_at(branch).screen
    )
    # The TYPE first, and the property map after it.  A branch's type decides whether
    # it can be a class AT ALL; whether it declares properties is a question only an
    # object branch has.  The other order reported a scalar branch against
    # ``properties`` -- "constrains only requiredness", of a node that constrains a
    # value -- which is the same misattribution ``ROOT_HANDLED`` is ordered to avoid.
    if branch.get("type") not in (None, "object"):
        raise Refusal(
            "type",
            pointer,
            f"a branch of type {branch['type']!r} is step 6",
            kind=Kind.DEFERRED,
        )
    # **The composition AFTER the type, for that same reason**, and the order is
    # measured rather than preferred: a branch stating a non-object type cannot be a
    # class whatever else it states, so the type is the reason and the conjunct list is
    # not.  Measured over the portable population: 0 branches of a root union carry
    # both a non-object ``type`` and an ``allOf``, so the order moves no document today
    # -- it is written this way so that the first one to carry both is reported on the
    # keyword that is the reason.
    if "allOf" in branch:
        # **A branch that COMPOSES, which is a different position from a root ``allOf``
        # and is genuinely lowerable.**  The conjunct sits AT the branch's own node, so
        # ``harness._composed`` folds its facts into the node the branch class names and
        # the comparison has a pointer for every one of them -- none of the root case's
        # unreportability applies here.
        #
        # What it needs is the conjuncts BOUND, and it has them: a branch class's bases
        # are already the union base (§4, and ``isinstance(payload, Base)`` depends on
        # it), so a composing branch wants that base AND whatever its conjuncts name --
        # which is ``compiler.lower_composition``'s ``bases`` argument, prepending the
        # union base to the conjuncts' own.  ``mod.decide`` is not the way to it and
        # never was: it would declare a composition class that does not descend from
        # this base, so the branch would not answer ``isinstance``, which is the same
        # reason a bare ``$ref`` branch refuses above.
        #
        # The reader used to live in ``lower/product.py``, which a lowering may not
        # import (D13), and this row refused on that alone -- with a comment claiming
        # "the reachable population of that move is 0 TODAY" over 9 documents.  **That
        # measurement was taken before the branch rows landed and was stale when it was
        # read.** Re-run at ``c9bfb5133``, the same probe over the population it had
        # grown to: of 10 documents here, 4 EMIT, 5 become verdicts (2 an alias base, 1
        # a class-name collision, 2 through a chain) and 1 defers to step 7's row, and
        # 12 more documents chained onto this refusal release with them.  So the move
        # was a derivation matching 9 of 10, and ``docs/plan/j3k2l40-prediction.md``
        # carries both runs.
        #
        # ``properties`` is NOT required of a composing branch, which is why the check
        # below sits after this one: a branch whose fields all come from its conjuncts
        # declares none of its own, and ``lower_composition`` reads the conjunct list
        # for them.
        return Branch(name=branch_name(branch, root, pointer, doc), pointer=pointer, node=branch)
    if "properties" not in branch:
        raise Refusal(
            "required" if "required" in branch else "type",
            pointer,
            "a branch declaring no property constrains only requiredness: that is a rule "
            "on the root's class (D2, D6), not a branch class (step 7's row)",
            kind=Kind.DEFERRED,
        )
    return Branch(name=branch_name(branch, root, pointer, doc), pointer=pointer, node=branch)
