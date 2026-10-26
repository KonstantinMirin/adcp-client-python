"""Emit Python types for bundle documents named on the command line.

    python -m codegen --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over the steps' whole population, which is
derived from the bundle and never listed by hand.  The predicates it is the union of
live in ``tests/populations.py`` and ``tests/test_emit.py``'s ``population()`` is the
union -- ``docs/plan/architecture.md`` §5 puts them there ("the document-set predicates
a step's result was stated over are the tests' business and live under ``tests/``"), so
this package names no population and the one the tree is graded against is the one the
suite counts.

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

**This module exists so that no module of the compiler is ever bound as
``__main__``.**  ``runpy`` binds the file it executes under the name
``__main__``, so ``python -m codegen.emit`` left ``codegen.emit`` importable
under its own name as a SECOND module object: one dispatch table, one decider
and one ``Refusal`` class per binding, and a class compared by identity across
that boundary is two classes.  The compiler's answer used to be a prohibition --
no module of the walk could name ``codegen.emit`` at all, so the per-node
decision and the constraint namer were carried on :class:`codegen.compiler.Module`
as callables, and the only way back to them was through a dataclass field.

The entry point is the structural fix: ``python -m codegen`` executes THIS file
as ``__main__``, this file holds no state the compiler reads, and every module of
the compiler is reached by import alone.  ``codegen.emit`` is therefore imported
once, by name, on every path -- so the decision can be reached by NAME, the
context carries data rather than functions, and the import rule shrinks to the
two boundaries that are about design (``tests/test_import_rule.py``).

The bundle directory is an argument (D9) and there is no default, so no version
literal can enter this package.  The output path is a function of the document
path (D1): ``core/pagination-request.json`` ->
``src/adcp/types/_schemas/core/pagination_request.py``.
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

from codegen import refusal
from codegen.emit import TREE, emit, write


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="codegen", description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True, help="the schema bundle directory")
    ap.add_argument("--tree", type=Path, default=TREE, help="where the modules are written")
    ap.add_argument(
        "--package",
        type=Path,
        default=None,
        help="where D5's alias module is written; a WHOLE-RUN artifact, so a run over "
        "part of the population must leave it out (see `write`)",
    )
    ap.add_argument("document", nargs="+", help="bundle-relative document paths")
    ns = ap.parse_args(argv)

    out = emit(ns.bundle, ns.document)
    write(out, ns.tree, ns.package)
    if ns.package is None:
        print(
            f"not written: {', '.join(sorted(out.beside))} "
            f"(D5's alias module is a whole-run artifact; pass --package to write it)"
        )
    # Section 5's ``default`` row says "dropped and REPORTED", and this line is the
    # report.  Printed BEFORE the refusals, because a drop is a fact about a document
    # this run EMITTED: a reader scanning the refusals for a document's name would not
    # find it, and the drop would then be invisible to everyone but the suite.
    for document in sorted(out.drops):
        for pointer, value in sorted(out.drops[document].items()):
            print(
                f"dropped {document} at {pointer} on default: the document says "
                f"{value!r} and the property is REQUIRED, so the default can never be "
                "applied and no rendering carries it"
            )
    for document in sorted(out.refusals):
        r = out.refusals[document]
        print(
            f"refused {document} ({r['resolved']}) at {r['pointer']} "
            f"on {r['keyword']}: {r['detail']}"
        )
    # A NAME THE CLASS CARRIES NOTHING FOR is not a refusal and is printed as its own
    # line: the document emitted, and what the reader needs to know is that one name at
    # one pointer reached no class.
    for document in sorted(out.carries_nothing):
        for line in out.carries_nothing[document]:
            print(f"carries nothing for {document} at {line}")
    # **The report names the KINDS and not "refused" alone.**  "refused" admits "not
    # built yet", which is how `emitted + refused == 1054` stayed green over 385
    # documents waiting on rows nobody had written, so the one figure the exit
    # condition counts -- emitted plus VERDICTS -- is printed beside the partition
    # rather than left to a reader to assemble.
    counted = collections.Counter(r["resolved"] for r in out.refusals.values())
    verdicts = sum(counted[k] for k in refusal.FINAL_KINDS)
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
        f"({', '.join(f'{k} {n}' for k, n in sorted(counted.items()))}); "
        f"accounted {len(out.emitted) + verdicts}; "
        f"{len(set(ns.document))} named, the rest reached through a $ref"
    )
    return 1 if out.refusals else 0


if __name__ == "__main__":
    sys.exit(main())
