"""**THE ONE DISPATCH**: an exhaustive ``match`` over the node kinds, and nothing else.

``docs/plan/architecture.md`` §5: "This is the one place a node's kind is routed, it
contains no decision beyond the route, and ``assert_never`` makes the type checker refuse
a kind the match does not cover."

The kind is decided in ``codegen/schema/parse.py`` (§4), so there is nothing to read here:
the node IS the classification, and a ``match`` over a closed sum is the form §5 chose
against the two alternatives it names -- a ``(position, kind)`` product table, which is
mostly copies of one row and hides the one real position dependency behind them, and a
polymorphic hierarchy with a ``lower`` method, which spreads one function over the files
that read JSON and drags the IR and the keyword table into them.

**Root and non-root are one path** (§5).  There is no second table of root selectors: a
document is ``parse(raw, position=ROOT)`` followed by ``decide``, and the only thing ROOT
adds is the module wrapper, which ``emit.lower_document`` holds.  Where ROOT changes an
answer -- a root array is ``RootModel[list[X]]``, a root union is a base plus one class
per branch, a root scalar is a module-level alias -- it changes the HANDLER'S ANSWER at
``node.position`` and never which handler answers.

``name_hint`` rides beside the node because §4 of the semantics document makes a name an
INPUT to a lowering; §14 step 7 moves naming to ``lower/names.py`` as a pass over the
finished module, and this parameter is what goes then.
"""

from __future__ import annotations

from typing import assert_never

from codegen.compiler import Decided, Module
from codegen.lower import composition, const, containers, enum, objects, references, scalars, union
from codegen.refusal import Refusal
from codegen.schema import nodes


def decide(
    node: nodes.Node, name_hint: str, mod: Module, *, of_a_root_union: bool = False
) -> Decided | Refusal:
    """What one parsed node IS, routed by its kind -- or the refusal that says it is not.

    ``Decided | Refusal`` is §2's "total functions from node to decision", and it is
    where §14 step 6's claim that the TYPE CHECKER IS THE TEST bites hardest: this is
    the signature every handler has and every caller reads, so a caller that takes
    ``.type`` off the result without handling the other branch does not type-check.  The
    union has two branches and the checker makes a reader of it answer both.

    ``of_a_root_union`` is §6's one fact that travels DOWN: the enclosing UNION knows its
    own position and tells its branches, because "a branch of a ROOT union" is a statement
    about the union.  Only ``Enumeration`` reads it -- §4 of the semantics document gives
    an untitled branch of a root union a ``Literal`` of its members -- and routing a fact
    a parent handed down is not a decision this function makes.
    """
    match node:
        case nodes.Reference():
            return references.lower(node, name_hint, mod)
        case nodes.Enumeration():
            return enum.lower(node, name_hint, mod, of_a_root_union=of_a_root_union)
        case nodes.Constant():
            return const.lower(node, name_hint, mod)
        case nodes.Composition():
            return composition.lower(node, name_hint, mod)
        case nodes.Union():
            return union.lower(node, name_hint, mod)
        case nodes.Object():
            return objects.lower(node, name_hint, mod)
        case nodes.Mapping_():
            return containers.mapping(node, name_hint, mod)
        case nodes.Array():
            return containers.array(node, name_hint, mod)
        case nodes.Scalar():
            return scalars.lower(node, name_hint, mod)
        case nodes.MultiType():
            return containers.multi_type(node, name_hint, mod)
        case nodes.Null():
            return scalars.null(node, name_hint, mod)
        case nodes.Typeless():
            return scalars.typeless(node, name_hint, mod)
        case _:
            assert_never(node)
