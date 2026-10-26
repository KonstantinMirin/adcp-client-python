"""Naming and content dedup, as ONE pass over the finished module.

``docs/plan/architecture.md`` §7: **"Naming is a pass over the module, not a thread
through the walk."**  This module takes a :class:`codegen.compiler.Module` whose
declarations are keyed by POINTER and whose ``TypeRef``\\ s name local declarations by
pointer, and returns the module with a symbol table -- by §4 of
``docs/plan/rebuild-plan.md``'s rules: the root by ``pascal_case(title)``; a nested
declaration by its position (``<Parent><Property>`` at PROP, ``<Parent>Item`` at ELEM,
``<Parent>Value`` at MAPV, ``<Root><Key>`` at DEF); a branch by its own ``title``, else
the ``const`` it pins on the discriminating property, else its sorted ``required`` set.

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
    """The document ROOT: ``pascal_case(title)``, and the parent of every derived name."""

    title: str


@dataclass(frozen=True)
class Property:
    """A value of ``properties``: ``<Parent><Property>``."""

    parent: str
    key: str


@dataclass(frozen=True)
class Item:
    """An array's ``items``: ``<Parent>Item``."""

    parent: str


@dataclass(frozen=True)
class Value:
    """A mapping's value schema: ``<Parent>Value``."""

    parent: str


@dataclass(frozen=True)
class Entry:
    """A ``definitions``/``$defs`` entry: ``<Root><Key>``, the root being the parent."""

    key: str


@dataclass(frozen=True)
class Branch:
    """A branch of ``oneOf``/``anyOf``: §4's three rules, in order.

    :attr:`declaration` is the branch's own declaration, which is what all three rules
    read -- its ``title``, the ``const`` it pins on :attr:`discriminator`, its
    ``required`` set.  :attr:`properties` is the property map those readings range over:
    the branch's own, or -- for a bare ``$ref`` branch -- the TARGET's, because §4 says a
    ``$ref`` branch's fields are the target's and the walk is what resolved them.

    :attr:`refuses` is the difference between the two positions a branch is named at.  A
    ROOT union declares one class per branch, so a branch with no identity is a document
    this emitter cannot name and the document refuses; a NESTED union is a TYPE, and a
    branch that lowers to an annotation needs no name at all, so it falls back to the
    union's own derived name rather than refusing a union the walk can lower.
    """

    parent: str
    declaration: Any
    discriminator: str | None = None
    properties: Any = None
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
def pins(props: Any) -> dict[str, Any]:
    """Every property of a property map that is pinned to a ``const``.

    ONE reading, and two things read it: §4 "Names"'s second branch-naming choice -- the
    ``const`` a branch pins on the discriminating property (:func:`_const_pin`) -- and
    §4's first dispatch source (``lower.union.discriminator``, which re-binds this name).
    They are the same question asked of the same map -- "which key does this branch pin,
    and to what" -- and a second reading is how a class could come to be NAMED after a key
    the union does not dispatch on.

    A SCALAR pin only.  An object or an array ``const`` is refused by §5's ``const`` row
    at the property itself, and a value that is not hashable has no place in the
    distinctness test the dispatch derivation runs, so it is not a pin here either.
    """
    if not isinstance(props, dict):
        return {}
    return {
        k: v["const"]
        for k, v in props.items()
        if isinstance(v, dict) and isinstance(v.get("const"), (str, bool, int))
    }


def _const_pin(props: Any, named: str | None) -> Any:
    """The ``const`` a branch pins on the discriminating property, or ``None``.

    The property is the root's ``discriminator.propertyName`` where it declares one, and
    otherwise the branch's single ``const``-pinned property.  Two pins and no
    ``discriminator`` is ambiguous and falls through to the next rule rather than taking
    the alphabetically first, which would make a class name a function of spelling.

    ``props`` is the branch's OWN property map, or -- for a bare ``$ref`` branch -- the
    map it inherits from its target (``names.Branch.properties``).  A ``$ref`` branch's
    fields come from the target by §4's own sentence, so its pin does too: read off the
    branch node instead, every such branch pins nothing and that naming choice would be
    dead at the exact position §4 names it for.
    """
    pinned = pins(props)
    if named is not None and named in pinned:
        return pinned[named]
    return next(iter(pinned.values())) if len(pinned) == 1 else None


def branch_identity(hop: Branch, parent: str) -> str | None:
    """§4 "Names"'s three branch rules, or ``None`` where none of them applies.

    A title names itself.  A ``const`` or a required set is prefixed with the PARENT's
    name, so a branch named by either shares its base's spelling.  The required-set key
    is deliberate: it is stable when the spec adds an OPTIONAL field and renames exactly
    when requiredness changes, which is a semantic change a caller should meet as an
    ``ImportError`` rather than as a silent repoint.

    **A name is never derived from the neighbourhood.**  The rule a previous generator
    reached for -- name the sole classed branch after its PARENT -- makes a class name a
    function of what its siblings happen to be, so adding a branch renames an unrelated
    class.  §4 has no such rule and the caller refuses or falls back instead.
    """
    branch = hop.declaration
    if not isinstance(branch, Mapping):
        return None
    title = branch.get("title")
    if isinstance(title, str) and title:
        return class_name(title)
    props = branch.get("properties") if hop.properties is None else hop.properties
    pin = _const_pin(props, hop.discriminator)
    if pin is not None:
        return parent + class_name(str(pin))
    required = branch.get("required")
    if isinstance(required, list) and required:
        return parent + "".join(class_name(str(k)) for k in sorted(required))
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
    :func:`derive` folds the adopting position's own hops to.

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
def derive(
    pointer: str, hops: Mapping[str, Hop], seen: frozenset[str] = frozenset()
) -> str | Refusal:
    """The name §4 derives for the node at ``pointer``, folding its hops to the root.

    A name is a function of the node's PATH through the document and of nothing else --
    not of its content, not of which other nodes exist, not of the order the walk
    happened to reach it in.  That is what makes it recomputable after the walk, and it
    is also §9's rule: no census over the run enters here.

    ``seen`` is the pointers already on this fold, so a hop table that named a pointer
    through itself answers once rather than recurring.  The parser gives a child a
    pointer strictly below its parent's, so the population is 0; it is written because
    a fold with no base case is a crash and §9 says a crash is not an outcome.
    """
    hop = hops.get(pointer)
    if hop is None or pointer in seen:
        return ""
    if isinstance(hop, Unnamed):
        return ""
    if isinstance(hop, Root):
        return class_name(hop.title)
    if isinstance(hop, Entry):
        root = derive("", hops, seen | {pointer})
        return root if isinstance(root, Refusal) else root + class_name(hop.key)
    parent = derive(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    if isinstance(hop, Property):
        return parent + class_name(hop.key)
    if isinstance(hop, Item):
        return parent + "Item"
    if isinstance(hop, Value):
        return parent + "Value"
    derived = branch_identity(hop, parent)
    if derived is not None:
        return derived
    if hop.refuses:
        return Refusal("title", pointer, NO_IDENTITY, kind=Kind.VERDICT)
    return parent


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
    if isinstance(declaration, ir.ClassDecl | ir.EnumDecl | ir.AliasDecl):
        return declaration.name
    if isinstance(declaration, ir.RootBinding):
        return declaration.symbol
    return None


def assign(mod: Module) -> ir.Module | Refusal:
    """The pass: every declaration of one module given the name §4 derives for it.

    ``mod`` is the walk's own module value, ``compiler.Module``, and the import of it is
    under ``TYPE_CHECKING``: the arrow at RUN time runs one way (``compiler`` imports this
    module for §4's rules and nothing here imports it back), so the annotation is the only
    thing that needs the name and the type checker gets it.  What this reads is four
    fields -- the declarations in declaration order, the hops, the adoptions and the
    imports -- and nothing else of the walk.

    THE WHOLE OF THE DEDUP IS HERE, and it is §4's own sentence: declarations whose
    NODES are equal are one class, declared under the first pointer in document order,
    and every later pointer binds its own derived name to it by identity.  The walk
    records the equality -- it must, because a second occurrence's CHILDREN are not
    lowered at all and a declaration it never made has no name to derive -- and this
    pass is what turns the record into names: it decides nothing from the order the
    walk iterated in, because the adopting pointer takes the name ITS OWN position
    derives and the declaring pointer takes its own.

    :data:`SCOPE` is the scope, and the signature holds it: the only inputs are this
    module and §4's rules, so there is no census over the run to decide a name by.
    """
    symbols: dict[str, str] = {}
    taken: dict[str, str] = {}
    #: The declarations §4's dedup leaves unwritten: an adopting position that derives NO
    #: name of its own, and one whose derived name IS the declaring class's.  The first
    #: has nothing to bind and the second would be ``X = X``; both take the class symbol
    #: DIRECTLY, which is what mapping the adopting pointer onto the declaring symbol
    #: does for every type that names it.
    degenerate: set[int] = set()
    for i, declaration in enumerate(mod.declarations):
        pointer = _at(declaration)
        if pointer is None:
            continue
        derived = derive(pointer, mod.hops)
        if isinstance(derived, Refusal):
            return derived
        declares = mod.adopted.get(pointer)
        if declares is not None and derived in ("", symbols.get(declares)):
            symbols[pointer] = symbols[declares]
            degenerate.add(i)
            continue
        if derived in taken:
            # The symmetric failure to ``Module.declare``'s pointer check, and the same
            # kind of thing: §1 gives a class ONE import path, so two nodes of one
            # module deriving one name is a document this emitter cannot name -- and
            # which of the two a referrer would import would be decided by the order
            # the walk reached them in.  Measured 0 times over the 1,054 portable
            # documents, so this refuses rather than ordering them.
            return Refusal(
                "title",
                pointer,
                f"two nodes in this document derive the class name {derived!r}",
                kind=Kind.VERDICT,
            )
        symbols[pointer] = derived
        taken[derived] = pointer
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
    )
