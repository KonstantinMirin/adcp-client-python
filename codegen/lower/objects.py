"""§5's object row: ``type: object`` (stated or applied) with ``properties`` -> a class.

The handler is one line, because what a class IS is the field builder's and the class
declarer's -- ``compiler.fields`` and ``compiler.declare_object``, the one funnel every
class with fields passes through, shared with the composing row and with a union BRANCH so
that all three write the same rule tuple and the same ``extra`` policy.  §14 step 5's
remaining move is those two functions out of ``compiler.py``; the SIGNATURE is what this
step changes, and it is a node.
"""

from __future__ import annotations

from codegen import compiler, ir
from codegen.compiler import Module
from codegen.refusal import Refusal
from codegen.schema import nodes


def lower(node: nodes.Object, mod: Module) -> ir.Decided | Refusal:
    """The class, declared at this node's POINTER, as a local type.

    The refusal the class declarer returns comes back out UNCHANGED (§6: "a handler that
    receives a ``Refusal`` from a child returns it, unchanged, immediately"), so the
    document is refused at the innermost node that carried the keyword and this row adds
    no sentence of its own to it.
    """
    # **§3a's CATALOGUE, layer L2, asked at the node's own position** -- "the catalogue is
    # an INPUT to the walk, never a pass over its output: a node's type is a REFERENCE to a
    # catalogue entry, or a fresh type where the node is genuinely unique".
    # :attr:`compiler.Module.objects` is the first of those, so a position that RESTATES an
    # object type the bundle NAMES imports the symbol the naming position declares instead
    # of minting a second class over the same field set.
    #
    # **Asked FIRST, which is the one ordering this row has and is reading 4's own.** The
    # class declarer records a shape, a hop and a declaration at this pointer; a position
    # that is not going to declare must not do any of that, or the module carries a
    # declaration nothing references and §4 names it.
    #
    # The three positions this table never holds are ``catalogue.ShapeEntry.restating``'s
    # and each is a standing rule rather than a precaution: a document ROOT declares
    # because §1 says every portable document contributes a symbol; a position in the
    # home's own document is §4's content dedup's and not this layer's; and the home
    # declares. A home whose document REFUSED is absent from the table for the reason
    # ``emit.objects`` gives -- there is no symbol to import, and refusing this document
    # would charge it for a defect in another.
    entry = mod.objects.get(node.pointer)
    if entry is not None:
        # The same two records a ``$ref`` writes, through the same one writer: §1 gives a
        # class one import path, so the symbol is taken from the module that DECLARES it
        # and never re-exported from a third.
        mod.importing(entry.symbol, compiler.Importable(entry.module, entry.document))
        return ir.Decided(ir.TypeRef(entry.symbol))
    declared = compiler.lower_object(node, mod)
    if isinstance(declared, Refusal):
        return declared
    return ir.Decided(ir.TypeRef(declared, local=True))
