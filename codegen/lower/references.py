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


def lower(node: nodes.Reference, name_hint: str, mod: Module) -> Decided | Refusal:
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
        # **A root that is a bare ``$ref`` has no row in §4's table.**  §5 makes a
        # reference an IMPORT of the target's symbol, and a module whose ROOT symbol is
        # another module's class is a second import path for that class -- which §1
        # refuses by name.  A VERDICT, because the obstruction is the POINTER SPACE: the
        # document names a node that already has a home, and no row is waiting for it.
        return Refusal(
            "$ref",
            node.pointer,
            f"a root that is a bare reference to {node.uri!r} would bind this "
            "module's own symbol to a class another module declares, which is a "
            "second import path for one class (section 1); section 5's $ref row "
            "makes a reference an import and section 4's table gives a root no such "
            "shape",
            kind=Kind.VERDICT,
        )
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
    mod.imports.add((target.module, target.symbol))
    return Decided(ir.TypeRef(target.symbol, local=True))


#: Re-exported so ``emit`` keeps one spelling of the reading when it needs the two halves
#: of a URI without a node: the parser reads the ``#`` once (``nodes.Reference.head`` and
#: ``.into``) and this is the function it reads it with.
split_ref = bundle.split_ref
