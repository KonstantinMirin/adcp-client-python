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
from codegen.compiler import Decided, Module
from codegen.refusal import Refusal
from codegen.schema import nodes


def lower(node: nodes.Object, mod: Module) -> Decided | Refusal:
    """The class, declared at this node's POINTER, as a local type.

    The refusal the class declarer returns comes back out UNCHANGED (§6: "a handler that
    receives a ``Refusal`` from a child returns it, unchanged, immediately"), so the
    document is refused at the innermost node that carried the keyword and this row adds
    no sentence of its own to it.
    """
    declared = compiler.lower_object(node, mod)
    if isinstance(declared, Refusal):
        return declared
    return Decided(ir.TypeRef(declared, local=True))
