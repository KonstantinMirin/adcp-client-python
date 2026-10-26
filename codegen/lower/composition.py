"""§5's ``allOf`` row: ``$ref`` conjuncts are BASES, inline conjuncts are fields and rules.

At EVERY position, in one arm: the conjunct list is the same list and the merge rule is the
same rule at every depth, and a document root reaches this very handler -- §5's "root and
non-root are one path".

**The intersection rule stays a function over DECLARATIONS, and that is the design's own
decision rather than an unconverted half.**  §6: "``restatement``, ``intersection`` and
``at_least_as_tight`` are pure functions over two nodes and stay so", and
``schema/nodes.py`` says why a conjunct is a :class:`codegen.schema.nodes.Conjunct` and not
a node: the rule MERGES two declarations of one property and hands the merged one back to
``parse``, because the result has to be parsed as one node and not composed out of two
decided ones.  So this row reads :attr:`nodes.Composition.conjuncts` -- declarations with
their pointers -- and the merge's result goes through the parser like any other node.
"""

from __future__ import annotations

from codegen import compiler, ir
from codegen.compiler import Decided, Module
from codegen.schema import nodes


def lower(node: nodes.Composition, name_hint: str, mod: Module) -> Decided:
    """The composed class, declared under this position's name, as a local type."""
    return Decided(ir.TypeRef(compiler.lower_composition(node, name_hint, mod), local=True))
