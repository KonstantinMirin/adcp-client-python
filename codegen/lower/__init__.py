"""One module per D2 row, and the table ``codegen.emit`` dispatches through.

``codegen.emit`` owns everything that is not a shape: the CLI, the module text,
the import ordering, the refusal report.  A row owns one shape.

A row is a ``(selector, lowering)`` pair, and the SELECTOR is the row's own
population test in ``codegen.bundle`` -- the same predicate its step's metric is
stated over.  So a row cannot come to claim a document its step does not count,
and there is no second definition of a population to drift from.

The rows are UNORDERED, and that is deliberate: ``emit.lower_document`` FAILS on
a document two rows select rather than letting the table's order decide which one
wins.  An ordered chain makes precedence a property of where a lane happened to
insert its row -- invisible in review, and the same "last wins" this project
refuses of an ``allOf`` member list.  Disjointness is a fact about the SELECTORS
and belongs there: ``composes_at_the_root`` is already "``allOf`` and NO union",
because a union root is step 5's row whatever else it carries.  A collision is a
selector defect and gets fixed in ``codegen.bundle``.

A lane adds ONE line to :data:`ROWS` and its selector to ``codegen.bundle``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from codegen.emit import Module


class Row(NamedTuple):
    """One D2 row: the population it selects, and the lowering that emits it.

    ``lower`` has ``emit.lower_object``'s signature -- ``(node, name, pointer,
    mod)`` returning the declared name -- because a root shape and a nested one
    are the same job at different pointers.
    """

    selects: Callable[[dict], bool]
    lower: Callable[[dict, str, str, Module], str]


#: Every shape with a lowering, one line each, order-independent.
ROWS: tuple[Row, ...] = ()
