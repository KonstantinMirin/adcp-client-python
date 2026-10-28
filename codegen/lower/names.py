"""Naming and content dedup, as ONE pass over the finished module.

``docs/plan/architecture.md`` §7: **"Naming is a pass over the module, not a thread
through the walk."**  This module takes a :class:`codegen.compiler.Module` whose
declarations are keyed by POINTER and whose ``TypeRef``\\ s name local declarations by
pointer, and returns the module with a symbol table -- by §4 of
``docs/plan/rebuild-plan.md``'s rules: the root by ``pascal_case(title)``; a nested
declaration by its OWN position (``<Property>`` at PROP, ``<Property>Item`` at ELEM,
``<Property>Value`` at MAPV, ``<Root><Key>`` at DEF); a branch by its own ``title``, else
the ``const`` it pins on the discriminating property, else its sorted ``required`` set.

**A nested name is its own position and not the path to it, and §4's collision rule is
what pays for that** (:data:`COLLISION`, :func:`spell`).  "The module path already
carries the document, so a nested name does not repeat it" -- so two positions of one
module can derive one name, and where N do, ALL N lengthen by their own nearest ancestor
segment until every name in the module is unique.  Before the rule was written this pass
folded every hop to the root and concatenated, which cannot collide and therefore needed
no rule: 808 of 2,118 emitted classes were longer than 30 characters, 141 longer than 50,
and one was ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.
With the rule it is 235 of 2,144 over 30, the median falls from 26 characters to 17, and
2,116 of 2,226 named positions keep the one segment §4 derives.
:func:`segments` is the same readings kept as a CHAIN so that :func:`spell` can spend as
few of them as the module requires, and the chain's whole spelling is the name the fold
gave -- which is why the refusal two indistinguishable positions earn is the same
refusal, over the same documents, as before.

**The walk computes no name, and §7 reads §4's own rule strictly.**  §4 says a name is
an input to a lowering and is never computed inside one; §7 adds "read strictly, it is
not an input either: it is assigned after".  So a handler declares at a pointer and
records the HOP its child's name is derived through (:data:`Hop` below), and nothing
before this pass holds a symbol of this module's own.  Every symbol slot in the IR --
``ClassDecl.name``, ``EnumDecl.name``, ``AliasDecl.name``, ``RootBinding.symbol``,
``ClassDecl.bases``, ``ClassDecl.branches``, ``UnionInstall``, and every ``TypeRef``
marked ``local`` -- holds a POINTER until :func:`assign` runs, and a NAME after.  A
pointer is ``""`` or begins with ``/`` and a name is an identifier, so the two cannot be
mistaken for one another, and the one slot that mixes them is ``bases``: a base is
either a pointer into this module or a symbol another module declares, and :func:`assign`
resolves the pointers and leaves the symbols.

**The SCOPE of the dedup is ONE MODULE, which is one document (D1).**  §9 of the
semantics document decides it: "do not decide one document's output by a census over
the run -- a name, a shape or an import that depends on which other documents the run
includes makes a one-document emission and a whole-bundle emission disagree about the
same document."  Two documents that inline identical content therefore keep a class
each; collapsing them would need a rule for which module owns the survivor, D1 gives a
node exactly one home, and 0 of the bundle's 1,271 identical-content groups have a ROOT
carrying that content for a ``$ref`` to reach.  :data:`SCOPE` is the sentence, and the
only inputs this pass has are the module and the reserved attribute set, so the scope is
held by the signature as well as by the sentence.

**The dedup KEY is NODE EQUALITY.**  ``codegen/schema/nodes.py`` excludes ``pointer``
and ``position`` from a node's equality, so two nodes are equal exactly when they state
the same thing about an instance -- which is §4's content dedup read off the type system
rather than off a JSON serialisation with a position bit appended (``emit.content_key``,
deleted).  Measured over the memo's own population: 7,250 nodes in 677 documents, 283
groups by the deleted key and 283 by this equality, and 0 documents whose partition
differs.  **Do not reintroduce a serialisation-based key.**

**What the dedup does with a group**: §4's own sentence.  "The class is declared under
the name of the position the walk reaches first, and every later position of the same
content binds its own derived name to that class by identity, ``X = Y``."  So one class
per group, declared at the first pointer in document order, and every later pointer
binds the name ITS OWN position derives -- never a sibling position's name, which would
read as one branch carrying another's type and would make a public symbol a function of
which key the walk reached first.

Two refusals are this pass's, and both are VERDICTS of the document: two pointers
deriving one name, and a branch with no identity.  ``docs/plan/architecture.md`` §13
item 7 records the one case that reaches the second -- an untitled ``enum`` branch of a
root union whose only other branch is a constrained string -- and §4 gives no fourth
naming rule, so it stays refused.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from codegen import ir
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes

if TYPE_CHECKING:  # pragma: no cover -- the annotation only; see :func:`assign`
    from codegen.compiler import Module

#: **The stated scope of the content dedup** (§14 step 7's own words for this row, and
#: §9's rule behind it).  Read by ``tests/test_emit.py``, so the sentence the code states
#: and the sentence a check grades are one string.
SCOPE = (
    "one module, which is one document (D1): a name, a shape or an import that depended "
    "on which other documents the run includes would make a one-document emission and a "
    "whole-bundle emission disagree about the same document (section 9)"
)


# --------------------------------------------------------------------------- #
# §4's name rules
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


def _suffixed(chain: tuple[str, ...], suffix: str) -> tuple[str, ...]:
    """``chain`` with ``suffix`` spelled onto its LAST segment rather than appended as a
    segment of its own.

    §4 names three positions off their container -- ``<Property>Item`` for an element,
    ``<Property>Value`` for a mapping value, ``<Base><Const>`` for a pinned branch -- and
    each of the three is ONE segment, because ``Item``, ``Value`` and ``True`` name no
    position on their own: a collision between two elements has to lengthen past the
    container to say anything at all.

    An empty chain is the position under a mapping's KEY, which derives no name
    (:class:`Unnamed`), and the suffix is then the whole chain -- which is what the fold
    produced there before this pass had segments.
    """
    return (chain[:-1] + (chain[-1] + suffix,)) if chain else (suffix,)


def spelling(chain: tuple[str, ...], depth: int) -> str:
    """One position's name carrying its last ``depth`` segments.

    ``depth`` 1 is the name §4 derives, each further step is the next nearest ancestor
    prepended (§4's collision rule, :func:`spell`), and ``len(chain)`` is the whole path
    -- which is the name this emitter gave every position before the rule was written.
    """
    return "".join(chain[max(len(chain) - depth, 0) :])


def entry_key(pointer: str) -> str:
    """The ``definitions``/``$defs`` KEY a local reference's pointer names.

    RFC 6901's two escapes, inverted.  The one reading of a pointer's last segment in
    this compiler, and it is a KEY and not a POSITION: §6 forbids recovering a position
    from a pointer string, and a DEF entry's position is the parser's (``Position.DEF``)
    -- what is read here is the name the document gave the entry, which the pointer
    carries because the pointer IS that key.
    """
    return pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")


# --------------------------------------------------------------------------- #
# the HOPS: what the walk records instead of a name
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Root:
    """The document ROOT: ``pascal_case(title)``, and the OUTERMOST segment of every
    name derived below it (:func:`segments`)."""

    title: str


@dataclass(frozen=True)
class Property:
    """A value of ``properties``: ``<Property>``, a segment of its own."""

    parent: str
    key: str


@dataclass(frozen=True)
class Item:
    """An array's ``items``: ``<Property>Item``, spelled onto the segment the array is
    spelled with, because ``Item`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Value:
    """A mapping's value schema: ``<Property>Value``, spelled onto the segment the
    mapping is spelled with, because ``Value`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Entry:
    """A ``definitions``/``$defs`` entry: ``<Root><Key>``, the root being the parent."""

    key: str


@dataclass(frozen=True)
class Branch:
    """A branch of ``oneOf``/``anyOf``: the three FACTS §4's three rules read, as values.

    §4 "Names"'s branch rules are "its own ``title``, else the ``const`` it pins on the
    discriminating property, else its sorted ``required`` set", and each of the three is a
    fact of the branch's own DECLARATION.  The declaration is ``lower/union.py``'s to read
    -- §6 keeps that reading at the declaration level and
    ``tests/test_import_rule.py``'s ``MAY_READ_A_DECLARATION`` names the module -- so what
    crosses into this pass is the three facts and not the mapping.  Extracting a fact is
    not deriving a name: which fact wins, how it is spelled, and what a parent prefix is
    are all below, and a module that reads no mapping cannot come to read one.

    :attr:`pin` is the ``const`` the branch pins on the discriminating property, read over
    the property map §4 gives the rule: the branch's own, or -- for a bare ``$ref`` branch
    -- the TARGET's, because §4 says a ``$ref`` branch's fields are the target's and the
    walk is what resolved them.

    :attr:`refuses` is the difference between the two positions a branch is named at.  A
    ROOT union declares one class per branch, so a branch with no identity is a document
    this emitter cannot name and the document refuses; a NESTED union is a TYPE, and a
    branch that lowers to an annotation needs no name at all, so it falls back to the
    union's own derived name rather than refusing a union the walk can lower.
    """

    parent: str
    #: The branch's own ``title``, where it states one that is a non-empty string.
    title: str | None = None
    #: The ``const`` it pins on the discriminating property, where exactly one is derived.
    pin: Any = None
    #: Its ``required`` set, as the document lists it.
    required: tuple[str, ...] = ()
    refuses: bool = False


@dataclass(frozen=True)
class Unnamed:
    """A position with NO name to derive: a mapping's KEY type.

    Not an omission and not a failure: ``propertyNames`` states a constraint on a key
    and §4's nested rule derives a name from a PROPERTY, an element or a value, so there
    is no rule to apply here.  The empty name is what the walk passed at those two call
    sites before this pass existed, and a declaration that needed one would collide with
    the other unnamed position and refuse by name.
    """


#: What the walk records for a child it lowers, instead of the child's name.  Keyed by
#: the child's POINTER on :attr:`codegen.compiler.Module.hops`.
#:
#: **A child at its PARENT's pointer needs no hop**, and two shapes are in that
#: position: a ``type``-list member and an extras store, both of which the parser builds
#: at the node's own pointer because each is the same instance re-read (§4).  They
#: inherit the entry the grandparent recorded, so there is one name per pointer and the
#: recursion below cannot meet itself.
Hop = Root | Property | Item | Value | Entry | Branch | Unnamed


# --------------------------------------------------------------------------- #
# §4's branch rules
# --------------------------------------------------------------------------- #
def branch_identity(hop: Branch, parent: tuple[str, ...]) -> tuple[str, ...] | None:
    """§4 "Names"'s three branch rules, in order, as the branch's own SEGMENTS, or
    ``None`` where none of them applies.

    A title names ITSELF, so it is a chain of one and the branch's ancestors are no part
    of it.  A ``const`` or a required set is spelled ON the parent's own last segment, so
    a branch named by either shares its base's spelling.  The required-set key is
    deliberate: it is stable when the spec adds an OPTIONAL field and renames exactly
    when requiredness changes, which is a semantic change a caller should meet as an
    ``ImportError`` rather than as a silent repoint.

    **Which fact wins decides the SPELLING and the PLACEMENT together, which is why both
    are here.**  A caller handed the spelling alone would have to read ``hop.title``
    again to find out whether the ancestors belong in the chain, and that reading would
    be a second copy of the first rule.

    **A name is never derived from the neighbourhood.**  The rule a previous generator
    reached for -- name the sole classed branch after its PARENT -- makes a class name a
    function of what its siblings happen to be, so adding a branch renames an unrelated
    class.  §4 has no such rule and the caller refuses or falls back instead.
    """
    if hop.title:
        return (class_name(hop.title),)
    if hop.pin is not None:
        return _suffixed(parent, class_name(str(hop.pin)))
    if hop.required:
        return _suffixed(parent, "".join(class_name(str(k)) for k in sorted(hop.required)))
    return None


NO_IDENTITY = (
    "no title, no discriminator const and no required set: this branch has no "
    "identity to derive a name from, and D3 refuses rather than naming it after "
    "its siblings"
)


# --------------------------------------------------------------------------- #
# the field spelling, which is pydantic's own surface read once
# --------------------------------------------------------------------------- #
def field_name(key: str, reserved: frozenset[str] = frozenset()) -> str:
    """The Python field name for a property key, which is the key itself unless the
    model layer cannot carry a field under that name.

    A key is carried as-is or it is carried under an ALIAS, never dropped.  The bundle
    has keys a Python attribute cannot spell (``$schema``) and keys pydantic reads as
    something other than a field: a leading underscore makes a private attribute and no
    field at all, so ``core/truncation-sentinel.json``'s required ``_truncation`` was
    silently absent from the model -- the model refused the document's own instance AND
    accepted an instance omitting the required key, in the same class.

    The alias is the ONLY accepted spelling (no ``populate_by_name``), so the model's
    accepted set stays the document's: the wire name is accepted and the Python name is
    not a second way in.

    **``reserved`` is what the MODEL LAYER carries, and it is an ARGUMENT because §8
    draws the boundary where it does.**  This function read
    ``hasattr(pydantic.BaseModel, name)``, and that import was the one model-layer read
    left outside ``codegen/render.py`` -- named as a shrink-only exception in
    ``tests/test_import_rule.py``'s set.  §8 bans ``pydantic`` under ``lower/``
    outright, so moving the reading here would have GROWN that set; the set shrinks
    instead, because the reserved names are DERIVED in ``render.py`` (``render.RESERVED``)
    and handed to :func:`assign` by the run.  The fact is still read off the model layer
    and never listed by hand, and no module under ``lower/`` names pydantic.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in key).lstrip("_")
    if not name or name[0].isdigit():
        name = f"f_{name}"
    import keyword as _keyword

    while _keyword.iskeyword(name) or name.startswith("model_") or name in reserved:
        name += "_"
    return name


# --------------------------------------------------------------------------- #
# §4's content dedup: the equality, and the binding at a later position
# --------------------------------------------------------------------------- #
def same_node(mod: Module, node: nodes.Base) -> str | None:
    """The POINTER an EQUAL node already declared in this module, or ``None``.

    **§4's content dedup, keyed on NODE EQUALITY.**  §14 step 5 deleted
    ``emit.content_key`` -- ``json.dumps([the node's own mapping, node.applied])`` -- and
    ``schema/nodes.py`` says what replaces it: ``pointer`` and ``position`` are excluded
    from the kinds' equality, so two nodes are equal exactly when they state the same
    thing about an instance.  Everything else a node STATES is compared, including
    ``annotations`` (a node differing only in a ``$comment`` states a different thing to
    a reader) and ``applied`` (a node whose enclosing type word decides differently --
    which is the bit the old key appended by hand, and 1,390 of the bundle's nodes
    declare ``properties`` with no ``type``, 556 of them with that word applied and 834
    without, so both sides are populated).

    ``compiler.Module.collapsed`` is where the equality's CUT at a ``$ref`` and the
    reason the memo is a SEQUENCE are both written down: a node carries mappings and is
    not hashable, and a hash would be a second spelling of what identical means.

    **Measured over the memo's own population**, which is the nodes ``emit.decide_type``
    is called on: 7,250 nodes in 677 documents over the whole portable set, 283 groups of
    more than one node by the deleted key and 283 by this equality, and 0 documents whose
    partition differs.  So the replacement is a relocation and not a decision.

    **Asked in the WALK and not in the pass, and the reason is the pruning.**  A second
    occurrence's CHILDREN are never lowered -- they would declare a second class each,
    and their drops and their reports would be recorded twice -- so the equality has to
    be consulted before the node is decided.  What the PASS owns is everything §4
    actually decides about a group: which pointer declares, what each pointer is called,
    and that a later pointer binds the class by identity (:func:`adopt`, :func:`assign`).
    :data:`SCOPE` is the scope of all of it.
    """
    return next((at for other, at in mod.collapsed if other == node), None)


def adopt(mod: Module, pointer: str, declared: str) -> ir.TypeRef | Refusal:
    """§4's content dedup at the SECOND and later positions of one node: the class the
    first position declared, under the name THIS position's own rule derives.

    **One class, as many names as the node has positions.**  §4's dedup is a statement
    about CLASSES -- one node yields one class -- and §4's nested rule derives a name per
    POSITION, so a node at three positions has one class and three derived names.  An
    alias is a NAME BOUND TO THAT CLASS and not a second class, which is why the two
    rules do not collide and why nothing here is hand-assigned: the name is whatever
    :func:`segments` folds the adopting position's own hops to and :func:`spell`
    spells.

    What this refuses to do is type a field by a SIBLING POSITION's name.  Binding
    ``PreviewRenderHtml.dimensions`` to ``PreviewRenderUrlDimensions`` would read as the
    html branch carrying the url branch's type, and it would make the public symbol a
    function of which key the walk happened to reach first.  The upstream v9 SDK is the
    worked case of the opposite failure -- 1,092 of its 4,360 classes are numbered
    variants of content it declares over and over, ``WholesaleFeedEvent1`` through
    ``WholesaleFeedEvent9`` among them -- and the answer to that is one class aliased,
    not one class renamed.

    **The DECLARATION is an ``ir.AliasDecl``, the same statement §4's root-scalar row
    emits**, so there is one alias spelling in the emitter and not a second one here.  It
    carries no constraints, no description and no format on purpose: the node is EQUAL to
    the one the class already lowered, so every fact about it is already stated on the
    class, and a ``Field(description=...)`` wrapper here would both restate it and make
    the alias an ``Annotated`` object rather than the class itself -- which is the one
    thing a consumer must be able to rely on.  ``X = TheClass`` is the class by IDENTITY:
    ``X is TheClass``, ``isinstance`` works, and a type checker follows it.

    **Two positions take the class symbol directly rather than an alias, and
    :func:`assign` is what decides that** -- it has to be, because neither test can be
    made before the names are derived.  A position whose hops derive NO name (a mapping's
    key type) has no name to bind, and a position whose derived name IS the declared
    one would be ``X = X``.  The walk declares the alias at the adopting pointer either
    way and the pass drops the degenerate ones, mapping the adopting pointer straight
    onto the declaring class's symbol.

    **The adopting pointer IS declared**, under its own name, so a cross-document
    ``$ref`` naming the second position resolves to it -- ``emit.exported`` lists the
    symbol at every bundle-named pointer, so the import side and the export side still
    read one fact.  Before the alias this arm refused DEFERRED instead; 0 of the
    collapsed pointers are among the bundle's 216 named nodes, so the change closes a
    ceiling nothing reaches rather than moving a refusal.
    """
    collision = mod.declare(
        pointer, ir.AliasDecl(pointer, ir.TypeRef(declared, local=True))
    )
    if collision is not None:
        return collision
    return ir.TypeRef(pointer, local=True)


# --------------------------------------------------------------------------- #
# the pass
# --------------------------------------------------------------------------- #
def segments(
    pointer: str, hops: Mapping[str, Hop], seen: frozenset[str] = frozenset()
) -> tuple[str, ...] | Refusal:
    """§4's name rules for the node at ``pointer``, as the SEGMENTS of its path with the
    root first -- so the LAST segment is the name §4 derives for it and each earlier one
    is an ancestor a collision can lengthen by (:func:`spell`).

    A name is a function of the node's PATH through the document and of nothing else --
    not of its content, not of which other nodes exist, not of the order the walk
    happened to reach it in.  That is what makes it recomputable after the walk, and it
    is also §9's rule: no census over the run enters here.

    **A chain and not a name, and that is the whole of §4's "the module path already
    carries the document".**  This fold used to CONCATENATE every hop to the root, which
    needs no collision rule because it cannot collide -- and that is why 808 of 2,118
    emitted classes were longer than 30 characters and one was
    ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.  The
    segments are the same readings, kept apart, so :func:`spell` can spend exactly as
    many of them as the module's own names require.

    Three positions are a segment rather than a name of their own, and :func:`_suffixed`
    is where: an element, a mapping value and a pinned branch are each spelled onto the
    segment their container is spelled with.  A ``definitions`` entry is one segment too,
    because §4 names it ``<Root><Key>`` -- the root is part of the name the section
    states, exactly as the property is part of ``<Property>Item``.  A branch TITLE names
    itself, so it starts a chain and its ancestors are no part of it.

    ``seen`` is the pointers already on this fold, so a hop table that named a pointer
    through itself answers once rather than recurring.  The parser gives a child a
    pointer strictly below its parent's, so the population is 0; it is written because
    a fold with no base case is a crash and §9 says a crash is not an outcome.
    """
    hop = hops.get(pointer)
    if hop is None or pointer in seen:
        return ()
    if isinstance(hop, Unnamed):
        return ()
    if isinstance(hop, Root):
        return (class_name(hop.title),)
    if isinstance(hop, Entry):
        root = segments("", hops, seen | {pointer})
        if isinstance(root, Refusal):
            return root
        return ("".join(root) + class_name(hop.key),)
    parent = segments(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    if isinstance(hop, Property):
        return (*parent, class_name(hop.key))
    if isinstance(hop, Item):
        return _suffixed(parent, "Item")
    if isinstance(hop, Value):
        return _suffixed(parent, "Value")
    derived = branch_identity(hop, parent)
    if derived is not None:
        return derived
    if hop.refuses:
        return Refusal("title", pointer, NO_IDENTITY, kind=Kind.VERDICT)
    return parent


#: §4's collision rule, in the section's own words.  QUOTED by the checks that grade it
#: (``tests/test_names_collision.py``), so the sentence the code states and the sentence
#: a check reports against are one string.
COLLISION = (
    "every position derives its short name; where N positions of one module derive the "
    "same name, ALL N lengthen -- each prepends its own nearest ancestor segment -- and "
    "the step repeats until every name in the module is unique; a position whose short "
    "name collides with nothing keeps it (section 4)"
)


def spell(
    chains: Mapping[str, tuple[str, ...]], occupied: frozenset[str] = frozenset()
) -> dict[str, str] | Refusal:
    """§4's collision rule over the names of ONE module: pointer -> the name it is
    declared under, or the refusal of a module two of whose positions cannot be told
    apart.

    :data:`COLLISION` is the rule.  Every position starts at the name §4 derives (its
    last segment); the positions sharing a name ALL lengthen by their own nearest
    ancestor segment; the step repeats until no name is shared.

    **ALL N lengthen, and that is the whole of why this is order-independent.**
    Lengthening only the later collider would make a public symbol a function of which
    position the walk reached first, which §9 forbids and which :func:`adopt` already
    refuses for the same reason.  Lengthening all of them makes each name a function of
    the SET of colliding positions, and that set is a function of the one document --
    which is why this takes a mapping and not a module, and why nothing here can consult
    the run.

    ``occupied`` is the names the module's own IMPORTS hold: what the walk reported
    (``Module.imports``) and what the renderer brings in (``render.CARRIERS``, via
    :func:`assign`).  A module's namespace is its declarations AND what it imports -- a
    class shadowing an imported symbol retypes every field annotated with it, and
    ``class Field(StrEnum)`` beside ``from pydantic import Field`` makes
    ``Annotated[X, Field(description=…)]`` call the class -- so an imported name is a
    name taken, and a position deriving it lengthens.  Measured over the portable set
    with §4's nested rule in force: 25 positions of 2,226 derive an occupied name -- 3
    a symbol their own document's ``$ref`` imports, 5 one the renderer brings
    (``Field`` four times and ``Presence`` once), and 17 a name in the vocabulary the
    renderer could bring and this module does not.

    It is not a census over the run.  A module imports a symbol because ITS OWN ``$ref``
    names the target, so the set is a function of the one document and its closure, which
    a one-document emission writes as well; §9's rule is about the documents BEYOND that
    closure.  An import cannot lengthen, so only the positions move.

    **An occupied name a position cannot lengthen past is kept and does not refuse**, and
    the reason is that it is exactly the name this emitter has always given that position.
    A ROOT and a titled branch are chains of ONE -- §4 names them after the document and
    after the branch's own title -- so neither has an ancestor to prepend, and refusing
    them would refuse 99 documents of this bundle on a name no document says anything
    about -- measured by making it refuse: ``core/error.json``'s root is ``Error`` and
    the runtime exports an ``Error``, and 98 more follow it or chain behind one.
    Lengthening is an improvement where it is available and the status quo where it is
    not.

    The REFUSAL is the one this pass always had, and it needs two positions: both spelled
    with their whole paths, neither with an ancestor left to prepend, and spelled alike.
    That is exactly the population the fold refused before the rule was written -- the
    full path was the name then -- so the rule moves no document into the refused set.
    """
    depth = dict.fromkeys(chains, 1)
    while True:
        spelled = {p: spelling(chains[p], depth[p]) for p in chains}
        groups: dict[str, list[str]] = {}
        for pointer, name in spelled.items():
            groups.setdefault(name, []).append(pointer)
        colliding = {
            name: ps for name, ps in groups.items() if len(ps) > 1 or name in occupied
        }
        lengthened = False
        for group in colliding.values():
            for pointer in group:
                if depth[pointer] < len(chains[pointer]):
                    depth[pointer] += 1
                    lengthened = True
        if lengthened:
            continue
        # Nothing colliding can lengthen.  Two positions sharing a name is the refusal;
        # a position alone on a name an import holds keeps it (above).  The pointer named
        # is the one that COLLIDED -- the later of the two in declaration order, which is
        # the pointer ``Module.declare``'s symmetric check names as well.
        shared = {name: ps for name, ps in colliding.items() if len(ps) > 1}
        if not shared:
            return spelled
        at = next(p for p in chains if p in {q for ps in shared.values() for q in ps[1:]})
        return Refusal(
            "title",
            at,
            f"two nodes in this document derive the class name {spelled[at]!r}",
            kind=Kind.VERDICT,
        )


def resolved(decided: ir.TypeRef, symbols: Mapping[str, str]) -> ir.TypeRef:
    """One decided type with every LOCAL pointer replaced by the symbol it names.

    Recursive over the type TREE and not over a rendered string: a container carries its
    members in ``of`` with a mapping's key beside them, so ``list[X] | None`` reaches
    ``X`` through two levels and neither can be read off ``path``.

    A local path that is NOT in the table is a symbol another module declares -- a
    cross-document import, which §5's ``$ref`` row makes an import of the TARGET's own
    symbol -- and it is left exactly as the walk decided it.  That is the one slot where
    a pointer and a name share a field, and the table is what tells them apart.
    """
    out = decided
    if decided.local and decided.path in symbols:
        out = replace(out, path=symbols[decided.path])
    if decided.of:
        out = replace(out, of=tuple(resolved(inner, symbols) for inner in decided.of))
    if decided.key is not None:
        out = replace(out, key=resolved(decided.key, symbols))
    return out


def _bound(declaration: ir.Declaration, symbols: Mapping[str, str]) -> ir.Declaration:
    """One declaration with every symbol slot bound: its own name, its bases, its
    branches, and every type it holds."""
    if isinstance(declaration, ir.ClassDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            fields=tuple(
                replace(f, type=resolved(f.type, symbols)) for f in declaration.fields
            ),
            extras=(
                None
                if declaration.extras is None
                else resolved(declaration.extras, symbols)
            ),
            bases=tuple(resolved(b, symbols) for b in declaration.bases),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    if isinstance(declaration, ir.EnumDecl):
        return replace(declaration, name=symbols[declaration.name])
    if isinstance(declaration, ir.AliasDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
        )
    if isinstance(declaration, ir.RootBinding):
        held = declaration.declaration
        return replace(
            declaration,
            symbol=symbols[declaration.symbol],
            # The two kinds a root binding can wrap, narrowed by construction rather than
            # by an ``isinstance`` standing in for a branch: ``RootBinding.declaration``
            # is ``AliasDecl | EnumDecl`` and each has its own rewrite above.
            declaration=(
                replace(
                    held,
                    name=symbols[held.name],
                    type=resolved(held.type, symbols),
                )
                if isinstance(held, ir.AliasDecl)
                else replace(held, name=symbols[held.name])
            ),
        )
    if isinstance(declaration, ir.RootModelDecl):
        # §7's third root shape, whose name and whose wrapped type are bound exactly as a
        # class's are.  An ARM of its own and not the fallthrough, because the fallthrough
        # is what the type checker reads as "everything left", and adding a declaration to
        # ``ir.Declaration`` without one here is how a new kind silently takes another
        # kind's rewrite -- which is what mypy reported the moment ``RootModelDecl`` joined
        # the union.
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    return replace(
        declaration,
        base=resolved(declaration.base, symbols),
        branches=tuple(resolved(b, symbols) for b in declaration.branches),
    )


def _at(declaration: ir.Declaration) -> str | None:
    """The POINTER a declaration was declared at, which is what its name slot holds
    until this pass runs.  ``None`` for the one declaration that binds no name --
    :class:`codegen.ir.UnionInstall`, whose two statements are about symbols the module
    already declares."""
    if isinstance(
        declaration, ir.ClassDecl | ir.EnumDecl | ir.AliasDecl | ir.RootModelDecl
    ):
        return declaration.name
    if isinstance(declaration, ir.RootBinding):
        return declaration.symbol
    return None


def assign(mod: Module, carriers: frozenset[str] = frozenset()) -> ir.Module | Refusal:
    """The pass: every declaration of one module given the name §4 derives for it.

    ``mod`` is the walk's own module value, ``compiler.Module``, and the import of it is
    under ``TYPE_CHECKING``: the arrow at RUN time runs one way (``compiler`` imports this
    module for §4's rules and nothing here imports it back), so the annotation is the only
    thing that needs the name and the type checker gets it.  What this reads is four
    fields -- the declarations in declaration order, the hops, the adoptions and the
    imports -- and nothing else of the walk.

    ``carriers`` is the other half of the module's NAMESPACE: the names the renderer
    brings in, which the walk does not report (``render.CARRIERS``, handed in by the run
    for :func:`field_name`'s reason -- §8 bans ``pydantic`` under ``lower/`` and the one
    module allowed to read the model layer derives the set).  It is empty by default,
    which spells every position by §4 alone; the run passes it, so a class cannot take
    the name of an import the module's own fields are annotated with.

    THE WHOLE OF THE DEDUP IS HERE, and it is §4's own sentence: declarations whose
    NODES are equal are one class, declared under the first pointer in document order,
    and every later pointer binds its own derived name to it by identity.  The walk
    records the equality -- it must, because a second occurrence's CHILDREN are not
    lowered at all and a declaration it never made has no name to derive -- and this
    pass is what turns the record into names: it decides nothing from the order the
    walk iterated in, because the adopting pointer takes the name ITS OWN position
    derives and the declaring pointer takes its own.

    **The names are decided over the WHOLE module and not one declaration at a time**,
    because §4's collision rule is about a SET: the positions sharing a derived name all
    lengthen, so no position's name can be settled before every position's chain is
    known.  So this fold collects the chains (:func:`segments`) and :func:`spell` decides
    the names from them -- and the refusal two indistinguishable positions earn is
    :func:`spell`'s, where the whole set is in hand, rather than a first-come check that
    would name whichever the walk reached second.

    :data:`SCOPE` is the scope, and the signature holds it: the only inputs are this
    module and §4's rules, so there is no census over the run to decide a name by.
    """
    #: The declarations §4's dedup leaves unwritten: an adopting position that derives NO
    #: name of its own, and one whose derived name IS the declaring class's.  The first
    #: has nothing to bind and the second would be ``X = X``; both take the class symbol
    #: DIRECTLY, which is what mapping the adopting pointer onto the declaring symbol
    #: does for every type that names it.
    degenerate: set[int] = set()
    chains: dict[str, tuple[str, ...]] = {}
    #: An adopting pointer that binds no name of its own -> the pointer whose class it
    #: takes.  Resolved after :func:`spell`, because the symbol it takes is not decided
    #: until the declaring position's own name is.
    takes: dict[str, str] = {}
    for i, declaration in enumerate(mod.declarations):
        pointer = _at(declaration)
        if pointer is None:
            continue
        chain = segments(pointer, mod.hops)
        if isinstance(chain, Refusal):
            return chain
        declares = mod.adopted.get(pointer)
        #: Compared over the WHOLE chain, which is this position's own longest spelling:
        #: two positions whose paths spell alike derive one name at every length, so the
        #: degenerate arm is the same arm it was when the fold returned that spelling.
        if declares is not None and "".join(chain) in (
            "",
            "".join(chains.get(declares, ())),
        ):
            takes[pointer] = declares
            degenerate.add(i)
            continue
        chains[pointer] = chain
    spelled = spell(chains, carriers | {symbol for _, symbol in mod.imports})
    if isinstance(spelled, Refusal):
        return spelled
    symbols: dict[str, str] = dict(spelled)
    for pointer, declares in takes.items():
        symbols[pointer] = symbols[declares]
    return ir.Module(
        document=mod.document,
        root=symbols.get("", ""),
        declarations=tuple(
            _bound(d, symbols)
            for i, d in enumerate(mod.declarations)
            if i not in degenerate
        ),
        imports=frozenset(mod.imports),
        symbols=symbols,
        adopted=dict(mod.adopted),
        # §7's ``approximations`` slot, carried through unchanged: this pass assigns
        # SYMBOLS, and a declaration names a POINTER, which naming does not move.  It is a
        # tuple here because the IR is immutable and the walk's accumulator is a list.
        approximations=tuple(mod.approximations),
    )
