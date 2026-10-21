"""Point the harness at the tree THIS run emitted, and at nothing else.

The pair comes from the emitter's own binding table: the emitter knows which
document it lowered into which symbol, so it writes that down and the grader
reads it.  Nothing here scans a directory for modules, parses a header for a
filename, or maps a name to a document by convention.

That is the one guard this module exists for.  A harness pointed at a tree the
run did not emit grades a different generator's output and reports it as this
one's -- which is how 1,602 documents came to be graded green in a previous
attempt while nothing was being generated.  So ``pairs`` refuses a binding whose
module did not come out of the named tree, and refuses one whose generated
header does not name the document being graded.

It also refuses a binding carrying no ``strict_validate``.  ``harness.accepting``
falls back to ``TypeAdapter`` for a model with no entry point of its own, which
is right for an Enum and wrong for anything this emitter produces: it would
grade the constructor and report it as the accepted set.  The harness knows no
package and cannot tell the two apart; this module does, so the refusal lives
here -- see ``_graded``, which also knows that D2's root-scalar row keeps its
entry point on the MODULE, because an alias has no method to carry one.

Of the first two, only the tree check is separately graded (``test_emit`` points
the adapter at a tree it did not emit and requires the refusal).  The header one is reachable
only by hand-editing ``_bindings.json`` in place, because an import resolves by
package name and so always lands in the real tree, which the first check catches
first.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from codegen import bundle
from codegen.harness import Pair


def bindings(tree: Path) -> dict[str, dict[str, Any]]:
    table = json.loads((tree / "_bindings.json").read_text())
    if not table:
        raise AssertionError(f"{tree}/_bindings.json is empty: nothing was emitted to grade")
    return table


def pairs(bundle_dir: Path, tree: Path) -> list[Pair]:
    """One graded unit per binding, in sorted order."""
    out = []
    for document, row in sorted(bindings(tree).items()):
        module = importlib.import_module(row["module"])
        where = Path(getattr(module, "__file__", "") or "").resolve()
        if not where.is_relative_to(tree.resolve()):
            raise AssertionError(
                f"{row['module']} resolves to {where}, outside the emitted tree {tree}: "
                "the grade would be of another tree's output"
            )
        header = where.read_text().split("\n", 1)[0]
        if document not in header:
            raise AssertionError(f"{where} does not name {document}: {header!r}")
        # Resolved from the BUNDLE, not read off the row: the row is the
        # emitter's output and this module exists to be independent of it.  The
        # two must agree, and that they do is the strongest statement available
        # here -- the schema ``strict_validate`` decides acceptance with at
        # runtime IS the bundle's document, resolved.  An emitter that wrote the
        # wrong schema into the row would otherwise be graded against its own
        # mistake and be green.
        schema = bundle.resolved(bundle_dir, document)
        if row["schema"] != schema:
            raise AssertionError(
                f"{document}: the binding row's schema is not this document resolved; "
                "strict_validate would decide acceptance against something the bundle "
                "does not say"
            )
        out.append(Pair(document, schema, _graded(module, row)))
    return out


def _graded(module: Any, row: dict[str, Any]) -> Any:
    """What the harness is handed for one binding: the thing carrying the strict
    entry point.

    ``harness.accepting`` reads ``strict_validate`` off whatever it is given and
    uses it for nothing else, so this answers only one question -- where does
    this binding's entry point live.

    For a class it lives on the class.  For D2's root-scalar row it cannot: an
    alias is not a class, it has no method and no ``__qualname__``, so the
    emitted MODULE binds ``strict_validate`` (``_base.strict_alias``) and the
    module is what goes to the harness.  Both are the same two halves against the
    same binding table; only construction differs.

    A binding with neither is refused here rather than handed over, because the
    harness would then fall back to ``TypeAdapter`` -- the model's CONSTRUCTOR --
    and report it as the accepted set.  That refusal is D4's and the reason is in
    ``harness.accepting``; this adds the second place an entry point can be, not
    a way to go without one.
    """
    model = getattr(module, row["symbol"])
    for carrier in (model, module):
        if callable(getattr(carrier, "strict_validate", None)):
            return carrier
    raise AssertionError(
        f"{row['module']}.{row['symbol']} carries no strict_validate, and neither does its "
        "module: the harness would grade it through TypeAdapter, which is its constructor "
        "and not its accepted set (codegen.harness.accepting)"
    )
