"""§5's ``$ref`` row: a reference is a REFERENCE, and its siblings compile to nothing.

The target's own module declares its type once and this one names it (§1: one import path
per class), so nothing of the target's schema is read here and nothing of it can be copied.

**CONVERTED to node fields.**  Every fact this row reads is a field
:class:`codegen.schema.nodes.Reference` carries: the URI, its document half, its pointer
half, and the CONSTRAINING siblings the parser decided the co-occurrence over (§4 -- "the
co-occurrences the semantics document decides are decided here and nowhere else").  The
screen is the table's, at the node's own position, over the one set this row claims.
"""

from __future__ import annotations

from codegen import bundle, compiler, ir
from codegen.compiler import Decided, Module, check_keywords
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes


def lower(node: nodes.Reference, mod: Module) -> Decided | Refusal:
    """An IMPORT of the target's symbol, or the local entry's own declaration.

    **A CONSTRAINING sibling compiles to NOTHING and is REPORTED**, which is §5's ``$ref``
    row as the design owner settled it: draft-07 ignores every sibling of ``$ref``, so the
    keyword constrains no instance and the document's accepted set is the target's alone.
    The record keeps the key (§3 drops none), the cell says it compiles to nothing at this
    co-occurrence so §8 does not grade it, and the run names it because a key that reads as
    a constraint and is inert is worth reading once.  :attr:`nodes.Reference.inert` is the
    parser's reading of that co-occurrence; this row reports it and screens it as claimed.
    A key with NO ROW and a key whose cell is REFUSE still refuse, by name, through the
    screen.
    """
    compiler.report_inert(node.inert, node.pointer, mod)
    refused = check_keywords(
        node,
        {"$ref", *node.inert},
        "a sibling of $ref, which draft-07 ignores",
        mod=mod,
    )
    if refused is not None:
        return refused
    if node.position is Position.ROOT:
        return _root(node, mod)
    # **The DOCUMENT HALF decides which of the two resolutions this is**, and the reading
    # is ``bundle.split_ref``'s one reading of the ``#``, made by the parser.  An EMPTY
    # half is a pointer into the document being written: there is no module to import
    # from, and the symbol is one THIS module declares, so it is a lookup in
    # ``mod.declared`` rather than a binding, and ``compiler.local_reference`` parses and
    # declares the entry if the walk has not reached it yet.
    if not node.head:
        return compiler.local_reference(mod, node.into, node.pointer)
    target = mod.target(node.uri, node.pointer)
    if isinstance(target, Refusal):
        # The RUN's refusal for this site, unchanged (§6).  It is the run that mints the
        # CHAIN for a target that refused, because it is the one holding the target's own
        # refusal to carry ``through=``; this row has nothing to add to it.
        return target
    mod.importing(target.symbol, target.where)
    return Decided(ir.TypeRef(target.symbol, local=True))


def _root(node: nodes.Reference, mod: Module) -> Decided | Refusal:
    """§5(a)'s bare-``$ref`` root: a SUBCLASS of the target where the target is a class.

    "Refused because binding this module's symbol to another module's class would be a
    second way to reach one class, against §1.  **Where the target is a class the answer
    is a subclass of it**, which is one class per name and accepts exactly what the base
    accepts, so §1 is untouched."  The subclass declares no field of its own: the
    target supplies every one of them by inheritance, nothing of the target is copied
    (P2), and the pair grades against the document of record -- where §3 inlines the
    target unchanged, so there is a pointer for every inherited fact.

    ``declare_object`` is the funnel, handed the target's :class:`compiler.Shape` as what
    the class inherits and no props of its own, exactly as a composing node with one
    ``$ref`` conjunct and no properties reaches it -- which is what a bare ``$ref`` root
    IS, spelled without the ``allOf``.  So the ``extra``, the rule tuple, the
    ``__adcp_schema__`` and the recorded shape are the ones every other class gets, and
    there is no second reading of what a reference conjunct becomes.

    **Where the target is not a class the symbol is bound BY IDENTITY and that arm is
    unwired, which is reported rather than hidden.**  §5(a)'s other half -- "where the
    target is an alias, an enumeration or a root model there is nothing to subclass and
    the symbol is bound to the target by identity" -- has **population 0** over the
    portable set: 1 document states a bare-``$ref`` root
    (``core/signal-pricing-option.json``) and its target is a class.  ``Target.shape`` is
    the reading of "is a class", and it is ``None`` for a union ROOT as well as for an
    alias: ``emit.resolve`` declines to hand a union base's shape across a module
    boundary, which is the answer §5's ``$ref`` row at CONJ already gives ("a union root,
    whose instance is one of its branches ... is not a class a model can extend") and
    which §4 part 3 makes load-bearing here -- a subclass of a union base declared
    elsewhere keeps its OWN schema, so it would accept none of the branches.
    """
    target = mod.target(node.uri, node.pointer)
    if isinstance(target, Refusal):
        # The run's own refusal for this site, unchanged (§6), and the CHAIN is the
        # run's to mint: the target is where the obstruction is.
        return target
    if target.shape is None:
        return Refusal(
            "$ref",
            node.pointer,
            f"a root that is a bare reference to {node.uri!r} whose target is not a "
            "class declaring fields: section 5's bare-$ref root gives a subclass where "
            "the target is a class and an IDENTITY binding where it is an alias, an "
            "enumeration or a root model, and the identity half is unwritten -- "
            "population 0 over the portable set, where the one bare-$ref root's target "
            "is a class",
            kind=Kind.DEFERRED,
        )
    mod.importing(target.symbol, target.where)
    declared = compiler.declare_object(
        node,
        node.pointer,
        mod,
        (),
        # What the class INHERITS, which is the whole of the target's own shape: this
        # subclass declares nothing, so there is nothing to overlay.
        target.shape,
        bases=(ir.TypeRef(target.symbol, local=True),),
        # §6's description-authority rule, clause 3: this node's own ``description``
        # sibling where it states one -- §5's ``$ref`` row says the sibling's
        # description wins -- and the target's where it is silent.  ``declare_object``
        # reads the node's first and falls back to this.
        description=target.shape.description,
    )
    if isinstance(declared, Refusal):
        return declared
    return Decided(ir.TypeRef(declared, local=True))


#: Re-exported so ``emit`` keeps one spelling of the reading when it needs the two halves
#: of a URI without a node: the parser reads the ``#`` once (``nodes.Reference.head`` and
#: ``.into``) and this is the function it reads it with.
split_ref = bundle.split_ref
