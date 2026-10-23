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
``properties``.  Everything else refuses by name, pointer and keyword, because §7's
done-when for this step is *one subclass per branch* and each of these has no subclass to
give:

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
  carries a copy of it;
* an ``allOf`` conjunct list.  That one is lowerable and is refused for a reason of its
  own, stated at the refusal in :func:`_plan`: the conjuncts sit at the branch's own
  node, so the grader has a pointer for them, and what is missing is only that the
  conjunct reader is the product row's and D13 keeps it out of reach.  It is checked
  AFTER the branch's ``type``, because a branch whose type is not an object cannot be a
  class whatever else it states -- see :func:`_plan`.

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
from codegen.refusal import Refusal

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
#: so unlike the root case it is genuinely lowerable; :func:`_plan` refuses it on the
#: one thing it lacks, which is the conjunct reader D13 keeps in the product row.
BRANCH_HANDLED = frozenset(
    {"type", "properties", "required", "additionalProperties", "const", "allOf"}
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
    title = branch.get("title")
    if isinstance(title, str) and title:
        return compiler.class_name(title)
    pin = _const_pin(branch, doc)
    if pin is not None and not isinstance(pin, (dict, list)):
        return root + compiler.class_name(str(pin))
    required = branch.get("required")
    if isinstance(required, list) and required:
        return root + "".join(compiler.class_name(str(k)) for k in sorted(required))
    raise Refusal(
        "title",
        pointer,
        "no title, no discriminator const and no required set: this branch has no "
        "identity to derive a name from, and D3 refuses rather than naming it after "
        "its siblings",
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
    compiler.check_keywords(doc, pointer, ROOT_HANDLED | {kw})  # the walk's own check
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
            )
    if doc.get("type") not in (None, "object"):
        raise Refusal("type", pointer, f"a union root of type {doc['type']!r} is step 6")
    branches = doc[kw]
    if len(branches) < 2:  # noqa: PLR2004 -- a union of one is not a union
        raise Refusal(
            kw, pointer, f"{len(branches)} branch: a union of one is the branch itself, not a union"
        )

    planned = [
        _plan(branches[i], f"{pointer}/{kw}/{i}", symbol, doc) for i in range(len(branches))
    ]
    names = [p.name for p in planned]
    if len(set(names)) != len(names):
        raise Refusal(
            "title",
            pointer,
            f"two branches derive the same class name: {sorted(n for n in names if names.count(n) > 1)}",
        )

    mod.imports.add((compiler.BASE_MODULE, "AdCPBaseModel"))
    mod.imports.add((compiler.BASE_MODULE, "BranchDispatchMixin"))
    mod.imports.add(("typing", "ClassVar"))
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
            ),
        )
    )
    mod.add(symbol, pointer, rendered)

    for plan in planned:
        compiler.lower_object(plan.node, plan.name, plan.pointer, mod, bases=(symbol,))

    # The module trailer.  Two statements beside the classes, which is the module writer's
    # own text (§3: no compiler template has a slot for a line beside a class), and they
    # declare no name -- so they are appended rather than declared.
    mod.blocks.append(
        f"{symbol}._branch_models = ({', '.join(names)},)\n{symbol}.model_rebuild(force=True)"
    )
    return symbol


def _plan(branch: Any, pointer: str, root: str, doc: dict) -> Branch:
    """What one branch becomes, or the refusal that says why it becomes nothing."""
    if not isinstance(branch, dict):
        raise Refusal("oneOf", pointer, f"a branch is {type(branch).__name__}, not a schema")
    live = {k for k in branch if k not in compiler.ANNOTATIONS and not k.startswith("x-")}
    if live == {"$ref"}:
        raise Refusal(
            "$ref",
            pointer,
            "a bare $ref branch has no node to declare a subclass from: the member would "
            "be the target's own class, which does not descend from this base, so the "
            "arm would not answer isinstance",
        )
    compiler.check_keywords(branch, pointer, BRANCH_HANDLED)  # the walk's own check
    # The TYPE first, and the property map after it.  A branch's type decides whether
    # it can be a class AT ALL; whether it declares properties is a question only an
    # object branch has.  The other order reported a scalar branch against
    # ``properties`` -- "constrains only requiredness", of a node that constrains a
    # value -- which is the same misattribution ``ROOT_HANDLED`` is ordered to avoid.
    if branch.get("type") not in (None, "object"):
        raise Refusal("type", pointer, f"a branch of type {branch['type']!r} is step 6")
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
        # What it needs is the conjuncts BOUND: a branch class's bases are already the
        # union base (§4, and ``isinstance(payload, Base)`` depends on it), so a
        # composing branch wants that base AND whatever its conjuncts name.  The reader
        # that binds a conjunct list is the product row's, and a lowering imports
        # ``codegen.compiler`` and ``codegen.refusal`` and nothing else of this package
        # (D13), so this row cannot reach it -- a branch composes once that reader is
        # shared machinery in ``compiler``, which is where D13 puts machinery two rows
        # need.  ``mod.decide`` is not the way round it: it would declare a composition
        # class that does not descend from this base, so the branch would not answer
        # ``isinstance``, which is the same reason a bare ``$ref`` branch refuses above.
        #
        # **The reachable population of that move is 0 TODAY, measured by making this
        # refusal fail.**  Probed by removing it and lowering each branch with its
        # conjuncts DROPPED -- which is what the move would supply -- over all 9
        # documents in this position: 0 emit.  They refuse on ``uniqueItems`` (3), a
        # ``$ref`` chain (2), a branch ``type`` (2), an ``allOf`` whose base is an alias
        # (1) and a class-name collision (1).  So hoisting the reader into ``compiler``
        # would be a derivation matching nothing (D14), and the step whose own keyword
        # unblocks one of these 9 is the step that should do it.  2 of the 9 compose
        # nothing but bare ``$ref`` conjuncts and are the two to re-measure then.
        raise Refusal(
            "allOf",
            pointer,
            "a branch that composes needs the bases its conjuncts name as well as the "
            "union base this row gives it, and the conjunct reader that binds them is "
            "the product row's: a lowering imports codegen.compiler and codegen.refusal "
            "and nothing else of this package (D13), so a branch composes once that "
            "reader is shared machinery in codegen.compiler",
        )
    if "properties" not in branch:
        raise Refusal(
            "required" if "required" in branch else "type",
            pointer,
            "a branch declaring no property constrains only requiredness: that is a rule "
            "on the root's class (D2, D6), not a branch class (step 7's row)",
        )
    return Branch(name=branch_name(branch, root, pointer, doc), pointer=pointer, node=branch)
