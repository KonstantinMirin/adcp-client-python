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
from codegen.schema import nodes


def lower(node: nodes.Object, name_hint: str, mod: Module) -> Decided:
    """The class, declared under the name this position derives, as a local type."""
    return Decided(ir.TypeRef(compiler.lower_object(node, name_hint, mod), local=True))
