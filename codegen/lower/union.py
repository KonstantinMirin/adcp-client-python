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

WHAT A BRANCH IS.  A branch is a class this module DECLARES: from the branch's own
``properties``; or, where the branch COMPOSES, from ``compiler.lower_composition`` with
this base as its ``bases`` (``salesagent-j3k2l.40``); or, where the branch is a bare
``$ref``, **from TWO BASES** -- the target, which supplies the fields, and this union's
base, which supplies the dispatch (§4, ``salesagent-j3k2l.59``).  Everything else refuses
by name, pointer and keyword, because §7's done-when for this step is *one subclass per
branch* and each of these has no subclass to give:

* a ``required``-only overlay, which constrains requiredness and nothing else: that is a
  rule on the root's class (D2, D6), step 7's row;
* a scalar or array branch (step 6, D2), a nested ``oneOf``/``anyOf``/``not``/``if``, or an
  ``enum``.  A branch carrying a bare ``const`` is a SCALAR branch and is refused as one:
  the ``const`` pins the branch's whole value, so there is no property map to declare a
  subclass from.  D2's ``const`` row (``codegen.lower.const``) decides a branch's
  PROPERTIES, which is where the discriminating pin sits, and this module no longer
  carries a copy of it.

A BARE ``$ref`` BRANCH used to be the first entry on that list and is now §4's own
sentence, implemented.  The reason it stood was that the arm's member would be the
TARGET's class, which does not descend from this base -- true of a member, and the answer
§4 gives is that the branch is not the target: it is a class of its own, at the branch's
OWN ``#/<kw>/<i>`` pointer, carrying its own ``__adcp_schema__``, whose bases are this
base and the target.  So ``isinstance(payload, Base)`` holds, the target's fields arrive
by inheritance and nothing of the target is copied (P2), and the branch grades against its
own node -- which the resolved document states as the target's content, so the comparison
has a pointer for every inherited fact.  ``compiler.lower_composition`` is the reader,
handed the branch as the one-conjunct composition a ``$ref`` branch IS: the same binder,
the same inherited :class:`compiler.Shape` and the same ``bases`` argument the composing
branch above already uses, so there is no second reading of what a ``$ref`` conjunct
becomes.

DISPATCH IS DERIVED FROM THE BRANCHES, NEVER DECLARED (§4, and :func:`discriminator`).
A union whose branches each pin one shared property to a DISTINCT ``const`` carries
``Field(discriminator=<property>)``, whether or not the document declares
``discriminator``; a declared keyword the branches do not confirm is not a dispatch
source.  The emitter writes the derived property onto the base as
``_BRANCH_DISCRIMINATOR`` and ``_base.BranchDispatchMixin._branch_adapter`` is what reads
it.  A ``$ref`` branch pins through its target, so the pins are read off the inherited
shape and not off the branch node -- which is the same place its fields come from.

THAT IS §4's FIRST SOURCE OF THREE, and the third is :func:`overlapping`: where the
branches are PAIRWISE DISJOINT the payload selects its own branch, so the base needs no
key and the structural union is a dispatch rather than a fallback.  Disjointness is
derived from the branches themselves (:func:`separates`) and a pair the derivation cannot
separate counts as overlapping, because admitting a union on an unproven disjointness is
the defect the source exists to avoid.  A root matching none of the three refuses, and
what it refuses ON is OVERLAP: with an unseparated pair, a branch could only be reached
by trying each and keeping the first that validates, which makes the answer a property of
declaration order rather than of the payload.  §4's SECOND source -- a key the bundle's
manifest states -- is ``salesagent-j3k2l.60``'s row and is unwritten, which is why the
overlap refusal is a DEFERRAL.

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

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from adcp.types._base import applied_schema

from codegen import compiler, keywords
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal

#: The cells the ROOT of a union document CONSUMES -- this row's own coverage, not an
#: admission list.  ``discriminator`` is gone from it: §6 admits the keyword by name at
#: every position and the TABLE is where that decision lives now, which is also what
#: reaches the three other positions this set never did.  It is still READ here, as the
#: property §4's rule 2 takes a branch's name from.
#: The four conjuncts are CLAIMED here so that the explicit refusal below is what reports
#: them, after every other keyword has been checked.  Left out of this set, they refuse
#: through ``compiler.check_keywords``, which walks ``sorted(node)`` -- so a root carrying
#: both ``additionalProperties`` and ``oneOf`` branches blocked by a later step's keyword
#: was reported against ``additionalProperties``, this module's own grader-driven refusal,
#: rather than against the keyword that is the reason.  Measured: the by-keyword profile
#: over the 156 read 55 ``additionalProperties`` / 42 ``allOf`` that way, and 0 / 55 this
#: way.  Attribution is the point of a refusal report, and the same principle
#: ``harness.violated_keywords`` is built on.
ROOT_CLAIMS = frozenset({"type", "properties", "required", "additionalProperties", "allOf"})

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
#: ``const`` and ``allOf`` are both in the set for ``ROOT_CLAIMS``'s reason, and
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
#: identical misattribution :data:`ROOT_CLAIMS` measured at 55 of 156 and fixed the
#: same way, and a deferral promising a row for a branch shape this module refuses by
#: design.
BRANCH_CLAIMS = frozenset(
    {"type", "properties", "required", "additionalProperties", "const", "enum", "allOf"}
)


#: The two union keywords, in the order a root carrying one is read -- READ OFF the
#: declaration's descent column rather than named: a union keyword is one whose
#: subschemas occupy a BRANCH, which is what a union IS.
UNION = tuple(
    k
    for k, p in keywords.descends_at(Position.ROOT).items()
    if p is Position.BRANCH
)


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
def pins(props: Any) -> dict[str, Any]:
    """Every property of a property map that is pinned to a ``const``.

    ONE reading, and two things read it: §4 "Names"'s second branch-naming
    choice -- the ``const`` a branch pins on the discriminating property
    (:func:`_const_pin`) -- and §4's first dispatch source (:func:`discriminator`).  They
    are the same question asked of the same map -- "which key does this branch pin, and
    to what" -- and a second reading is how a class could come to be NAMED after a key
    the union does not dispatch on.

    A SCALAR pin only.  An object or an array ``const`` is refused by §5's ``const`` row
    at the property itself, and a value that is not hashable has no place in the
    distinctness test :func:`discriminator` runs, so it is not a pin here either.
    """
    if not isinstance(props, dict):
        return {}
    return {
        k: v["const"]
        for k, v in props.items()
        if isinstance(v, dict) and isinstance(v.get("const"), (str, bool, int))
    }


def _const_pin(props: Any, doc: dict) -> Any:
    """The ``const`` this branch pins on the discriminating property, or ``None``.

    The property is the root's ``discriminator.propertyName`` where it declares one, and
    otherwise the branch's single ``const``-pinned property.  Two pins and no
    ``discriminator`` is ambiguous and falls through to the next rule rather than taking
    the alphabetically first, which would make a class name a function of spelling.

    ``props`` is the branch's OWN property map, or -- for a bare ``$ref`` branch -- the
    map it inherits from its target (:class:`Branch`).  A ``$ref`` branch's fields come
    from the target by §4's own sentence, so its pin does too: read off the branch node
    instead, every such branch pins nothing and that naming choice would be dead at the
    exact position §4 names it for.
    """
    pinned = pins(props)
    named = (doc.get("discriminator") or {}).get("propertyName")
    if isinstance(named, str) and named in pinned:
        return pinned[named]
    return next(iter(pinned.values())) if len(pinned) == 1 else None


def branch_identity(branch: dict, root: str, doc: dict, props: Any = None) -> str | None:
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

    ``props`` and ``required`` default to the branch's OWN, and are passed for a bare
    ``$ref`` branch as the INHERITED ones: rules 2 and 3 both read a fact about the
    branch's fields, and §4 says a ``$ref`` branch's fields are the target's.  Rule 1 is
    unaffected -- a title is the branch node's own annotation and never the target's,
    because the target's title names the target's class.
    """
    title = branch.get("title")
    if isinstance(title, str) and title:
        return compiler.class_name(title)
    pin = _const_pin(branch.get("properties") if props is None else props, doc)
    if pin is not None:
        return root + compiler.class_name(str(pin))
    required = branch.get("required")
    if isinstance(required, list) and required:
        return root + "".join(compiler.class_name(str(k)) for k in sorted(required))
    return None


def branch_name(branch: dict, root: str, pointer: str, doc: dict, props: Any = None) -> str:
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
    named = branch_identity(branch, root, doc, props)
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
class Inherited:
    """The class a bare ``$ref`` branch's fields come from, and the fields themselves.

    Two things come out of resolving such a branch and both are needed before any class
    is declared: the SYMBOL, which is the branch's second base, and the property map,
    which is where §4 "Names"'s ``const`` choice and §4's dispatch derivation read the
    ``const`` pin.  Carried together because they are one resolution -- asked twice, the
    second ask is a second reading of what a ``$ref`` names.
    """

    symbol: str
    shape: compiler.Shape


@dataclass(frozen=True)
class Branch:
    """One branch's decided class: its name, its node, and what it inherits.

    It carried a third field -- a per-property type this module had already decided,
    for the ``const`` on the discriminating property -- and that is gone with
    ``_literal``: D2's ``const`` row is ``codegen.lower.const`` now and the walk
    reaches it for every node, so a branch's properties are decided the way every
    other object's are.

    ``inherits`` is ``None`` for a branch that declares its own fields and the resolved
    target for a bare ``$ref`` branch (§4's two bases).  :attr:`properties` is the one
    place the difference is read, so nothing downstream asks which kind of branch this
    is in order to find its property map.

    ``name`` is EMPTY out of :func:`_plan` and written by :func:`_named` once every
    branch is planned, which is a sequencing fact and not a two-phase object for its own
    sake: §4 "Names"'s ``const`` choice reads the pin and §4's dispatch derivation reads
    the same pins across every branch, so a root with no derivable dispatch has to be
    reported on the dispatch -- not on whichever branch happens to be the first with no
    title.  Measured on ``core/requirements/asset-requirements.json``, whose 12 bare
    ``$ref`` branches have no title and no pin: named first, it refuses on ``title`` at
    ``/anyOf/0`` with "this branch has no identity", which names the symptom.
    """

    name: str
    pointer: str
    node: dict
    inherits: Inherited | None = None

    @property
    def properties(self) -> Any:
        """The property map this branch's fields come out of: its own, or the target's."""
        return self.node.get("properties") if self.inherits is None else self.inherits.shape.properties


def discriminator(planned: Sequence[Branch], doc: dict) -> str:
    """§4's FIRST dispatch source: the property whose ``const`` selects the branch.

    DERIVED FROM THE BRANCHES, never from the keyword.  A union whose branches each pin
    one shared property to a DISTINCT ``const`` dispatches on that property whether or
    not the document declares ``discriminator``, and a declared keyword the branches do
    not confirm is not a dispatch source -- ``core/format.json``'s asset union is the
    case that proves the first half (12 branches pinning ``asset_type``, no keyword
    declared) and the second is what keeps a stale keyword from naming a property only
    some branches pin.

    Two clauses, and the second is the one that makes the key SELECT rather than
    merely exist:

    * SHARED -- every branch pins it.  A property only some branches pin cannot route a
      payload that carries one of the others.
    * DISTINCT -- the branches' values for it are pairwise different.  Two branches
      pinning one property to one value are not told apart by it, and pydantic refuses
      such a union at class-build time rather than at validation.

    ``discriminator.propertyName`` is READ where the branches confirm it, and it is read
    first: a document declaring one has said which of several confirmed candidates it
    means, and ignoring it would make the choice a function of spelling (``sorted``).
    Where the branches confirm exactly one candidate it is the answer with or without
    the keyword.  Where they confirm several and the document names none, the choice IS
    a function of spelling and this refuses rather than taking the alphabetically first.

    **Empty IS returned, and it means "this root has no KEY to dispatch on".**  It does
    not mean the root has no dispatch: §4's third source is the branches being pairwise
    disjoint, which needs no key, and :func:`overlapping` is what asks that question of
    the same branches.  So an empty answer here is a question handed on rather than a
    refusal, and the refusal that does fire belongs to the third source.  Measured over
    the 1,054 portable documents: 7 roots reach that hand-off, 5 of them are disjoint and
    emit, and 2 overlap.
    """
    maps = [pins(p.properties) for p in planned]
    shared = set.intersection(*(set(m) for m in maps))
    candidates = sorted(k for k in shared if len({m[k] for m in maps}) == len(maps))
    named = (doc.get("discriminator") or {}).get("propertyName")
    if isinstance(named, str) and named in candidates:
        return named
    if len(candidates) == 1:
        return candidates[0]
    return ""


def applied_type(doc: dict, pointer: str, kw: str, i: int) -> Any:
    """The ``type`` the document applies to branch ``i``, which is not always its own.

    ``_base.applied_schema`` is the one reading of that, and it is the reading the
    SCHEMA half of every graded pair already uses: a root ``type`` asserts about the
    same instance every branch sees, so a branch stating none of its own has the
    root's.  Asked here through that same function, so the walk and the grader cannot
    come to disagree about what a branch says -- which for ``core/macro-bearing-url.json``
    is the difference between three typeless branches and three string branches.
    """
    return applied_schema(doc, f"{pointer}/{kw}/{i}").get("type")


def states_a_scalar_instance(doc: dict, pointer: str, kw: str) -> bool:
    """Does the document say its instance is a SCALAR?  That is what makes a union root
    an alias rather than a base plus subclasses.

    Every branch of a draft-07 combinator is applied to the SAME instance, so a branch
    declaring a non-object type is the document stating what that instance is -- for the
    whole document, and not for one branch.  A root that says so is a root SCALAR, and
    D2's row for one is "a root scalar or mapping -> a module-level alias"
    (:func:`_alias`), never a base plus subclasses: there is no class for a string to be
    an instance of.

    **Asked of a DECLARED type, and not of the absence of a property map.**  That
    distinction is the one a first cut of this got wrong, and the measurement is what
    caught it: a bare ``$ref`` branch declares no property map either, so "no branch can
    be a class" also claimed ``core/assets/asset-union.json`` and
    ``core/pricing-option.json`` -- two roots whose branches reference OBJECT documents,
    which the class path refuses for a reason of its own (:func:`_plan`) and which this
    row has no business re-deciding.  Measured over the portable population: the loose
    reading moved both documents' refusal, and this one moves neither.
    """
    return any(
        applied_type(doc, pointer, kw, i) not in (None, "object") for i in range(len(doc[kw]))
    )


def declares_a_class(doc_branch: Any, doc: dict, pointer: str, kw: str, i: int) -> bool:
    """Can this branch be a CLASS?

    Two clauses, and each is a clause of :func:`_plan`'s own reading rather than a
    second one: a branch whose applied ``type`` is not an object cannot be a class
    whatever else it states, and a branch declaring neither a property map nor a
    conjunct list has no shape for a class to have.

    It is asked BESIDE :func:`states_a_scalar_instance` rather than instead of it,
    because a root MIXING a declared scalar branch with a property-map branch is
    neither shape -- no alias holds a class, and no base is a string -- and it must not
    silently take either.  Such a root keeps the class path, where the scalar branch's
    own ``type`` check refuses it by name and pointer.  Measured over the 1,054 portable
    documents: of the 126 ``bundle.union_root`` claims, **0 mix the two**, so this guard
    moves no document today and is what makes the first one that appears loud.
    """
    if not isinstance(doc_branch, dict):
        return False
    if applied_type(doc, pointer, kw, i) not in (None, "object"):
        return False
    return "properties" in doc_branch or "allOf" in doc_branch


def _alias(doc: dict, symbol: str, pointer: str, kw: str, mod: compiler.Module) -> str:
    """D2's module-level alias for a union root whose branches are all annotations.

    The root's name binds an ``Annotated`` alias over the branches' own union, and the
    module carries the same two halves ``emit._scalar_root`` gives a plain scalar root
    -- the ``SchemaRef`` and the bound ``strict_validate`` -- because §4 says a root
    scalar has no class to carry the second and so binds a module-level function over
    the first.  ``compiler.declare_alias`` is that shape and this adds nothing to it.

    **The TYPE is :func:`nested`'s, unchanged.**  ``A | B`` over the branches is what a
    union below a root already lowers to, and the branches of a root union are the same
    list read the same way; a second reading here is how the two positions come to
    disagree about one document.  What this passes is the branch list AS THE DOCUMENT
    APPLIES IT, so the root's ``type`` reaches a branch that states none -- which is
    the reading ``_base.applied_schema`` already serves the SCHEMA half, so the two
    halves of every graded pair conjoin the same fact.  Read any other way the alias is
    graded against a schema the document does not mean.

    The node handed to :func:`nested` is the branch list alone, with the root's own
    keywords left off.  A root's ``type`` is not a sibling of the union in the sense
    ``nested``'s screen refuses -- that screen is about a fact with nowhere to go, and
    this one has gone into every branch.

    **A null branch lands here and the bundle has none.**  ``{"type": "null"}`` decides
    to ``compiler.Type("None")`` through ``emit._decide``'s own arm, so such a root
    aliases to ``str | None``.  At a root that ``| None`` can only be a fact about the
    TYPE -- there is no key for an absence to be the absence of -- which is the half of
    D4 this row is named for; the other half is the ``| None`` the compiler adds to an
    OPTIONAL PROPERTY, which is a fact about presence and not a claim that the document
    admits an explicit null.  Measured over the 1,054 portable documents: 0 union roots
    carry a ``null`` branch and 57 sites state ``null`` in a ``type`` LIST, every one of
    them below a root.

    **KNOWN CEILING, and it is D3's naming gap arriving at a new position.**  The name
    hint handed to :func:`nested` is the ROOT's own symbol, and at a root that symbol is
    TAKEN -- ``declare_alias`` below declares it.  A branch that lowers to an annotation
    needs no name and never reaches for the hint, but a branch that DECLARES something
    does: an untitled ``enum`` branch has no D3 identity (:func:`branch_identity` --
    title, else the discriminator ``const``, else the required set), takes the hint, and
    then ``compiler.Module.declare`` refuses the document by name, reporting "two nodes
    in this document derive the class name ..." at ``/``.  That refusal is a VERDICT and
    it is the right ANSWER -- D3 gives such a branch no name, and naming it from its
    neighbourhood is what D3 refuses -- but it reports the collision rather than the
    gap.  Measured: 2 documents, ``core/geo-place-system.json`` and
    ``core/geo-place-type.json``, each an untitled string ``enum`` branch beside a
    ``format: uri`` branch.  Clearing them needs a D3 rule for naming an untitled enum
    branch, which is a decision for the plan and not for this row; a predictive check
    here would be a second reading of what the walk declares, which is what makes the
    two disagree.
    """
    applied = {kw: [applied_schema(doc, f"{pointer}/{kw}/{i}") for i in range(len(doc[kw]))]}
    return compiler.declare_alias(
        mod, symbol, doc, nested(applied, pointer, symbol, mod, Position.ROOT)
    )


def _named(plan: Branch, root: str, doc: dict) -> Branch:
    """§4 "Names"'s branch name, written onto a planned branch, or the refusal
    that says why not.

    The naming PASS, separate from :func:`_plan` for the reason :class:`Branch` states:
    the ``const`` choice reads the pin that §4's dispatch derivation also reads, so
    the dispatch is decided first and a root with none is reported on the dispatch.
    """
    return replace(
        plan,
        name=branch_name(plan.node, root, plan.pointer, doc, plan.properties),
    )


def _why_no_pin(planned: Sequence[Branch]) -> str:
    """What the branches pin, for the refusal that says no dispatch is derivable.

    The refusal has to be actionable without re-running the emitter, and "no shared
    distinct const" is not: the reader needs to know whether the branches pin NOTHING,
    pin different properties, or pin one property to a repeated value.  So the pins
    themselves are reported, which is the measurement the derivation made.
    """
    maps = [pins(p.properties) for p in planned]
    shared = sorted(set.intersection(*(set(m) for m in maps)))
    if not shared:
        return f"the properties each branch pins are {[sorted(m) for m in maps]}"
    return (
        f"every branch pins {shared}, and the values are "
        f"{ {k: [m[k] for m in maps] for k in shared} }"
    )


# --------------------------------------------------------------------------- #
# §4's THIRD dispatch source: branches no instance satisfies twice
# --------------------------------------------------------------------------- #
def requires(plan: Branch) -> frozenset[str]:
    """The names this branch requires.

    Its own ``required``, or -- for a bare ``$ref`` branch -- the target's, which is
    where that branch's fields come from (§4's two bases).  One reading, beside
    :attr:`Branch.properties`, which answers the same question about the other half of a
    branch's shape.
    """
    if plan.inherits is not None:
        return frozenset(plan.inherits.shape.required)
    named = plan.node.get("required")
    return frozenset(named) if isinstance(named, list) else frozenset()


def admits_only_what_it_declares(plan: Branch) -> bool:
    """Does this branch FORBID every name outside its own property map?

    ``additionalProperties: false`` says so, and a ``patternProperties`` beside it takes
    it back for whatever the pattern matches -- so a node carrying one admits names this
    cannot enumerate and the answer is no.

    **A bare ``$ref`` branch answers NO, and that is §4's own instruction rather than a
    gap this hides.**  Closure is a fact about the NODE, the branch's node is the
    reference, and ``compiler.Shape`` carries a target's properties and its ``required``
    and not its ``additionalProperties`` -- so the derivation cannot read the target's
    closure from here, and §4 says "a pair the derivation cannot separate is treated as
    overlapping, because admitting a union on an unproven disjointness is the defect this
    source exists to avoid".  Reading it would need ``compiler.Shape`` to carry the fact,
    which is a change to the shared record and not this row's.
    """
    return plan.node.get("additionalProperties") is False and "patternProperties" not in plan.node


def separates(a: Branch, b: Branch, a_type: Any, b_type: Any) -> str | None:
    """What tells these two branches apart, or ``None`` where nothing does.

    §4's third dispatch source names three separators and all three are here, each
    read off the branches themselves:

    * **one property pinned to different ``const`` values** -- an instance carrying one
      value fails the branch pinning the other, so no instance satisfies both;
    * **a ``required`` name one branch declares and another forbids** -- an instance
      carrying the name fails the forbidding branch and one without it fails the
      requiring branch;
    * **scalar branches of different ``type``**.

    ``a_type`` and ``b_type`` are the ``type`` the DOCUMENT applies to each branch
    (:func:`applied_type`), because a branch stating none of its own has the root's.

    **MEASURED, one separator at a time, by turning each off and re-emitting.**  Over the
    7 roots that reach the derivation (30 pairs, 24 of them separated):

    * the pinned ``const`` decides 6 pairs, all of ``core/audience-selector.json``, whose
      four branches pin ``value_type`` three ways and ``type`` the fourth.  Off: emitted
      732 -> 730, that root and ``governance/audience-constraints.json`` behind it;
    * the required/forbidden name decides 18 pairs across 5 roots.  Off: emitted
      **732 -> 689**, which is the whole weight of the source;
    * the scalar type decides 0, and off, nothing moves.

    **The third separator's set is empty at this position, and it is written anyway.**
    Two checks upstream make it so: :func:`lower_union` refuses a root whose own ``type``
    is neither absent nor ``"object"``, and :func:`_plan` refuses a branch whose own
    ``type`` is neither -- so every branch the derivation is handed has an applied type of
    ``None`` or ``"object"`` and no pair of them differs as scalars.  A union whose
    branches ARE scalars is a root scalar and reaches :func:`_alias` instead, which
    declares no branch classes and so needs no dispatch at all.  It is written because §4
    names three separators and a derivation missing one is narrower than the section it
    implements, and it is GRADED directly on a constructed pair -- the same ground
    :func:`declares_a_class` keeps its 0-of-126 guard on.
    """
    first, second = pins(a.properties), pins(b.properties)
    for key in sorted(set(first) & set(second)):
        if first[key] != second[key]:
            return f"{key!r} is pinned to {first[key]!r} on one branch and {second[key]!r} on the other"
    for one, other in ((a, b), (b, a)):
        if not admits_only_what_it_declares(other):
            continue
        declared = set(other.properties or {})
        forbidden = sorted(requires(one) - declared)
        if forbidden:
            return (
                f"one branch requires {forbidden} and the other declares no such "
                "property and admits no name outside its own map"
            )
    scalars = a_type not in (None, "object") and b_type not in (None, "object")
    if scalars and a_type != b_type:
        return f"the branches are scalars of type {a_type!r} and {b_type!r}"
    return None


def overlapping(planned: Sequence[Branch], doc: dict, pointer: str, kw: str) -> list[str]:
    """Every PAIR of branches §4's third source cannot separate, named.

    Pairwise and not globally, because that is what the section says: "Where the
    branches are pairwise disjoint, the payload selects its own branch and the order
    they are tried in cannot change which one it reaches."  One unseparated pair is
    enough to make the answer a property of declaration order, which is what the refusal
    below is about.

    The pairs are returned rather than a boolean, so the refusal can NAME them: a reader
    of "these branches overlap" cannot tell which two without re-running the emitter, and
    a root with twelve branches has sixty-six pairs.
    """
    applied = [applied_type(doc, pointer, kw, i) for i in range(len(planned))]
    return [
        f"{planned[i].pointer} and {planned[j].pointer}"
        for i in range(len(planned))
        for j in range(i + 1, len(planned))
        if separates(planned[i], planned[j], applied[i], applied[j]) is None
    ]


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
    stated = compiler.rules_at(doc, position=Position.ROOT)
    compiler.check_keywords(
        doc, pointer, Position.ROOT, ROOT_CLAIMS | {kw} | stated.screen, mod=mod
    )
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
    branches = doc[kw]
    if len(branches) < 2:  # noqa: PLR2004 -- a union of one is not a union
        raise Refusal(
            kw, pointer, f"{len(branches)} branch: a union of one is the branch itself, not a union"
        , kind=Kind.VERDICT)
    # D2's two union shapes, and the DOCUMENT decides which.  A root whose instance is
    # a scalar is a root scalar (:func:`states_a_scalar_instance`), and a root scalar is
    # an alias; a root whose branches are shapes is the base-plus-subclasses below.  The
    # second clause is the guard against a root that is neither -- see
    # :func:`declares_a_class`.
    if states_a_scalar_instance(doc, pointer, kw) and not any(
        declares_a_class(branch, doc, pointer, kw, i) for i, branch in enumerate(branches)
    ):
        return _alias(doc, symbol, pointer, kw, mod)
    if doc.get("type") not in (None, "object"):
        raise Refusal(
            "type",
            pointer,
            f"a union root of type {doc['type']!r} states that every instance reaching a "
            f"branch is a {doc['type']}, and a branch that declares a property map is a "
            "CLASS, which no instance of that type can be: the document contradicts "
            "itself at this pointer and the branch's own type check reports the other "
            "half",
            kind=Kind.VERDICT,
        )

    # PLAN every branch, then DERIVE the dispatch, then NAME them -- in that order,
    # because each step's input is the one before it.  A bare ``$ref`` branch's pin
    # lives on its target, so the targets have to be resolved before either the
    # dispatch or the ``const`` naming choice can read one; and the dispatch has to be
    # decided before the names, so that a root with no derivable dispatch is reported
    # on the dispatch
    # rather than on the first branch that happens to have no title.
    planned = [
        _plan(branches[i], f"{pointer}/{kw}/{i}", symbol, doc, mod) for i in range(len(branches))
    ]
    on = discriminator(planned, doc)
    overlaps = overlapping(planned, doc, pointer, kw) if not on else []
    if overlaps:
        # **§4's three dispatch sources, and the refusal for a union matching none of
        # them.**  The first is a ``const`` every branch pins on one shared property
        # (:func:`discriminator`), the second a key the bundle's manifest states, and the
        # third branches no instance satisfies twice (:func:`overlapping`).  What the
        # refusal is ON is OVERLAP: with an unseparated pair, a branch can only be reached
        # by trying each and keeping the first that validates, and the answer is then a
        # property of declaration order rather than of the payload.
        #
        # **The DERIVATION is what keeps this small, and the number is the point.**  This
        # site read ``not on and any(p.inherits is not None ...)`` -- a narrow reading of
        # §4's refusal sentence, scoped to a root whose branches own no fields, because
        # the literal reading cost 43 documents at the time it was written and the
        # section then named only two sources.  §4's third source replaces that scoping
        # with a derivation, and the measurement over the 1,054 portable documents is
        # that **7 roots reach the derivation, 5 separate and 2 overlap**:
        #
        # * ``a2ui/bound-value`` (10 pairs), ``core/account-ref`` (1),
        #   ``core/canonical-account-ref`` (1) and ``core/postal-area`` (1) separate on a
        #   required name the other branch forbids; ``core/audience-selector`` (6)
        #   separates on a pinned ``const``.  All five get past the dispatch, and the
        #   four that were emitting keep emitting -- **the emitted set is unchanged**.
        # * ``adagents`` (1 pair, both branches open so neither forbids anything) and
        #   ``brand`` (5 of 10 pairs; ``/oneOf/1`` and ``/oneOf/3`` both require AND
        #   declare ``house``, so one instance satisfies both) refuse here.
        #
        # **Both of those two were already refusing, deeper, and this moves the report
        # to the root.**  ``adagents`` read an ``anyOf`` conjunct at
        # ``/oneOf/1/allOf/0`` and stays a deferral; ``brand`` read a scalar base at
        # ``/definitions/default_language/allOf/0``, which is a VERDICT, so its
        # resolution changes from verdict to deferral and the tree's verdict count falls
        # by one.  The deeper obstruction is untouched and reports again once the overlap
        # is resolved.  The root's dispatch is decided before its branches are declared,
        # for the reason the naming pass is: a root-level fact is reported against the
        # root.
        #
        # **The kind is a DEFERRAL and not a verdict**, because the second source is
        # unwritten: a union whose discriminant is in the ENVELOPE is
        # ``salesagent-j3k2l.60``'s row, which emits such a root as a mapping keyed by
        # that field rather than as the base plus branches here, and a lowering cannot
        # read the manifest to ask whether this document is one (§3's one dispatch seam).
        # A verdict would count a clearable document as finally refused.
        #
        # What the derivation does regardless of this refusal: the discriminator is
        # WRITTEN wherever it derives, so 34 of the 38 bases in the tree dispatch on a key
        # instead of on a structural union, and the other 4 carry
        # ``_BRANCH_DISCRIMINATOR = ""`` and reach their branches through §4's third
        # source.
        raise Refusal(
            kw,
            pointer,
            "no branch dispatch is derivable and the branches OVERLAP: §4's three "
            "sources are a const every branch pins on one shared property to a distinct "
            "value, a key the bundle's manifest states, and branches no instance "
            "satisfies twice.  The branches confirm no such property "
            f"({_why_no_pin(planned)}), and these pairs are separated by no pinned const, "
            f"no required name the other forbids and no scalar type: {overlaps}.  So a "
            "branch could only be reached by trying each and keeping the first that "
            "validates, which makes the answer a property of declaration order rather "
            "than of the payload.  The manifest source is the row for a union whose "
            "discriminant is in the envelope (salesagent-j3k2l.60), which emits such a "
            "root as a MAPPING keyed by that field rather than as the base plus branches "
            "here, and a lowering cannot read the manifest to ask whether this document "
            "is one",
            kind=Kind.DEFERRED,
        )
    planned = [_named(p, symbol, doc) for p in planned]
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
                # §4's derived dispatch, which is the one fact on this base that is a
                # judgement about the branches rather than a transcription of the root.
                f'_BRANCH_DISCRIMINATOR: ClassVar[str] = "{on}"',
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
        # Three branch shapes and three readers, and every one of them takes the union
        # base as ``bases`` -- the one argument that makes the branch answer
        # ``isinstance(payload, Base)``.  The shape is read off the NODE and not off a
        # field of :class:`Branch`, except for the one shape whose reader needs the
        # resolved target: ``_plan`` has already admitted the keyword set, so the node
        # is what decides which reader reads it.
        if plan.inherits is not None:
            # **§4's two bases.**  No fields of its own: the target supplies them, so
            # the class body is the ``__adcp_schema__`` of the BRANCH's own pointer and
            # nothing else, and the :class:`compiler.Shape` recorded for it is the
            # target's -- which is what a later reuser of this branch reads, the same
            # transitive record ``lower_composition`` writes for a ``$ref`` conjunct.
            # ``declare_object`` rather than ``lower_object``: there is no property map
            # here to read and an object node with none refuses there, correctly.
            compiler.declare_object(
                plan.node,
                plan.name,
                plan.pointer,
                mod,
                (),
                compiler.Shape(
                    plan.inherits.shape.properties,
                    plan.inherits.shape.required,
                    decided=plan.inherits.shape.decided,
                ),
                Position.BRANCH,
                bases=(symbol, plan.inherits.symbol),
            )
            continue
        lower = compiler.lower_composition if "allOf" in plan.node else compiler.lower_object
        lower(plan.node, plan.name, plan.pointer, mod, Position.BRANCH, bases=(symbol,))

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
#:
#: **The mechanism is a CONSTRAINING sibling's, and it is read as one** (§5's ``$ref``
#: row draws the same line in the same table: "an annotation sibling -> the sibling's
#: description wins; a constraining sibling -> refused").  A sibling §6 admits states
#: nothing about an instance, so there is no fact for the union's type to carry and no
#: fact for the comparison to miss.  The TABLE is the set of those: a sibling whose
#: cell carries nothing is admitted, and a sibling whose cell lowers is a constraining
#: one and reaches this refusal.
_NESTED_SIBLING = (
    "a sibling of a nested oneOf/anyOf is a CONJUNCTION with every branch (draft-07), "
    "and a nested union lowers to one type -- A | B -- which has no slot for a fact of "
    "its own: compiler.Type carries a container and its members and nothing else.  "
    "Conjoining it into each branch instead states it at a pointer the document does "
    "not, and dropping it is a model wider than its document, which "
    "harness.compare_schema reports as a missing fact at this very pointer"
)

#: ``discriminator`` beside a NESTED union is admitted by the TABLE, and the decision
#: is §6's own row -- "Nothing on the class.  It names a branch where that branch pins
#: more than one ``const``, and separately it CONFIRMS a dispatch key the branches
#: already state -- it does not establish one" -- whose answer carries no position
#: split, where the ``title`` and ``description`` rows beside it both give one.  So it
#: is the answer at this position too, and this module no longer names it.
#:
#: Three facts hold here and each was checked rather than assumed:
#:
#: * The keyword CONSTRAINS NOTHING, so :data:`_NESTED_SIBLING`'s mechanism does not
#:   reach it.  The same cell admits it at a root, and the two positions differ in
#:   nothing the reason mentions.
#: * The comparison does not look for it: ``keywords.rendered_at`` is the compared set
#:   and the cell's ``rendered`` is ``False``, so a model whose node is a bare ``anyOf``
#:   reports nothing ``missing`` at that pointer -- which is the second half of the
#:   sentence above and the half that does not hold for a constraining sibling.
#: * It is already READ at this position: :func:`nested` names each branch through
#:   :func:`branch_identity`, which reads ``discriminator.propertyName`` off the union's
#:   own node (:func:`_const_pin`).



def nested(
    node: dict, pointer: str, name_hint: str, mod: compiler.Module, position: Position
) -> compiler.Decided:
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

    **Two refusals stood here and are gone, because each one's stated reason was a
    claim about a harness that has since changed** (``salesagent-j3k2l.28``, §6 "every
    fold applies to both sides").  One refused a branch that was a LOCAL ``$ref`` and
    one refused a union whose shape ``harness._normalize`` folds, and both said the
    fold ran on the MODEL's side alone -- so a faithful class would read as narrower
    than its own document, which is the ``added`` direction.  ``_normalize`` now serves
    both sides from one body of code with a per-side ``$ref`` root, reads ``oneOf`` as
    well as ``anyOf``, and reads each branch through the finite-type rewrite one level
    down, so neither claim holds.  Measured by lifting each refusal and grading the
    population: the local-``$ref`` guard cost **8 documents** and its 43 ``added``
    facts have no site left -- 0 new reports of any kind -- and the fold guard cost
    **9**, whose folds grade green in both arms.  Together they took emitted from
    **691 to 702 of 1054 portable** with ``added`` 0.
    """
    kw = keyword(node)
    assert kw is not None, "nested is dispatched on the keyword being present"
    # The sibling screen, with its own ``why``: a CONSTRAINING sibling of this node is a
    # conjunction with every branch, and the generic answer for a draft-07 keyword
    # promises a later row for something no row can carry here.  Same shape as the
    # ``$ref`` arm's "a sibling of $ref, which draft-07 ignores" -- and the same line
    # that arm draws between an annotation sibling and a constraining one, which is what
    # the TABLE's cells carry.
    compiler.check_keywords(node, pointer, position, {kw}, _NESTED_SIBLING, mod=mod)
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
        decided = compiler.decide(branch, at, hint, mod, Position.BRANCH)
        # **The branch's own bound rides on the branch's own TYPE, never on the field
        # holding the union** (section 5's ``minItems``/``maxItems`` row, and section
        # 2's reasoning for every constraint).  The field holds the other branches too,
        # so a bound written there would refuse values the document accepts --
        # ``Annotated[str | int, Field(min_length=4)]`` applying a string's bound to the
        # integer branch, which is ``containers.multi_type``'s named defect at the
        # other spelling of the same shape.  ``compiler.carried`` is where the three
        # positions with no field of their own ask for a named type, and it refuses a
        # shape the alias module cannot spell rather than dropping it.
        arms.append(compiler.carried(decided, at, "this branch", mod))
    unique = tuple(dict.fromkeys(arms))  # document order, deduped
    if len(unique) == 1:
        # Two branches that lower to one type are one type, and saying ``X | X`` would
        # be a second spelling of it.  ``multi_type`` dedupes for the same reason.
        return compiler.Decided(unique[0])
    return compiler.Decided(compiler.Type(container="union", of=unique))


def _inherited(branch: dict, pointer: str, root: str, mod: compiler.Module) -> Inherited:
    """Resolve a bare ``$ref`` branch's target: the class it subclasses and its fields.

    §4: a ``$ref`` branch is a class with TWO BASES, and the target is the one that
    supplies the fields.  So the target has to be a CLASS, and the two things this needs
    off it -- the symbol and the :class:`compiler.Shape` -- are the two things a ``$ref``
    conjunct's base already takes from ``mod.bind`` in ``compiler.lower_composition``.

    **:func:`compiler.decide` is what reads the reference**, and it is read ONCE here,
    because
    ``emit.decide_type``'s ``$ref`` arm is the one place in this generator that decides
    which of the two resolutions a reference is: an absolute one binds a module and
    imports its symbol, a LOCAL ``#/...`` one names a node of the document being written
    and ``compiler.local_reference`` declares it.  Reading the ``#`` here instead would
    be a second reading of ``bundle.split_ref``'s delimiter -- which that function's own
    docstring names as how a binder and a resolver come to disagree about which document
    a reference names -- and a lowering may not import ``bundle`` at all (§3's one
    dispatch seam).

    The SHAPE is then whichever side declared the class: ``mod.shapes`` for a local
    target, which ``compiler.declare_object`` wrote while ``local_reference`` was
    declaring it, and ``mod.bind`` for one in another document, which is the same call
    and the same memo the walk already made.  A target that is not a class has no shape
    on either side and refuses here, for the reason a ``$ref`` conjunct refuses as a
    base: §4 "What becomes what" makes a scalar root an ``Annotated`` alias,
    and subclassing one is a ``TypeError`` at import.
    """
    decided = compiler.decide(branch, pointer, root, mod, Position.BRANCH)
    symbol = decided.type.path
    shape = mod.shapes.get(symbol)
    if shape is None and not decided.type.local:
        # Not a symbol at all -- a scalar, a container or a literal -- so there is no
        # class and :meth:`compiler.Module.bind` would be asked about a reference whose
        # target this very call already resolved.
        raise Refusal(
            "$ref",
            pointer,
            f"this branch references {branch['$ref']}, which the walk lowers to the "
            f"annotation {symbol or decided.type.container or 'Any'!r} rather than to "
            "a class: a "
            "branch is a class with two bases and an annotation cannot be one of them",
            kind=Kind.VERDICT,
        )
    if shape is None:
        shape = mod.bind(branch["$ref"], pointer).shape
    if shape is None:
        raise Refusal(
            "$ref",
            pointer,
            f"{symbol} is not a class, so it cannot be a base (a scalar root is an "
            "Annotated alias, and subclassing one is a TypeError at import)",
            kind=Kind.VERDICT,
        )
    return Inherited(symbol=symbol, shape=shape)


def _plan(branch: Any, pointer: str, root: str, doc: dict, mod: compiler.Module) -> Branch:
    """What one branch becomes, or the refusal that says why it becomes nothing."""
    if not isinstance(branch, dict):
        raise Refusal(
            "oneOf",
            pointer,
            f"a branch is {type(branch).__name__}, not a schema",
            kind=Kind.VERDICT,
        )
    live = set(compiler.declaring(branch, Position.BRANCH))
    if live == {"$ref"}:
        # **§4's two bases.**  The branch is a class at its OWN pointer whose bases are
        # the union's base and the ``$ref`` target: the target supplies the fields and
        # the base supplies the dispatch, so ``isinstance(payload, Base)`` holds for the
        # arm and nothing of the target is copied (P2).  Named here with NO name yet,
        # because §4 "Names"'s ``const`` choice reads the pin off the
        # INHERITED property map and the dispatch derivation reads the same map --
        # :func:`lower_union` resolves every
        # branch before it names any, so a root with no derivable dispatch is reported
        # on the dispatch rather than on the first branch that has no title.
        return Branch(
            name="",
            pointer=pointer,
            node=branch,
            inherits=_inherited(branch, pointer, root, mod),
        )
    # The branch's own D6 rules: the keywords are admitted here and the TUPLE is
    # written by ``compiler.declare_object``, which ``lower_object`` below reaches.
    compiler.check_keywords(  # the walk's own check
        branch,
        pointer,
        Position.BRANCH,
        BRANCH_CLAIMS | compiler.rules_at(branch, position=Position.BRANCH).screen,
        mod=mod,
    )
    # The TYPE first, and the property map after it.  A branch's type decides whether
    # it can be a class AT ALL; whether it declares properties is a question only an
    # object branch has.  The other order reported a scalar branch against
    # ``properties`` -- "constrains only requiredness", of a node that constrains a
    # value -- which is the same misattribution ``ROOT_CLAIMS`` is ordered to avoid.
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
        # union base to the conjuncts' own.  ``compiler.decide`` is not the way to it and
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
        return Branch(name="", pointer=pointer, node=branch)
    if "properties" not in branch:
        raise Refusal(
            "required" if "required" in branch else "type",
            pointer,
            "a branch declaring no property constrains only requiredness: that is a rule "
            "on the root's class (D2, D6), not a branch class (step 7's row)",
            kind=Kind.DEFERRED,
        )
    return Branch(name="", pointer=pointer, node=branch)
