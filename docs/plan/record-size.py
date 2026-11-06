"""Reading 5's decider, measured over every portable document.

    PYTHONPATH=.:src ./.venv/bin/python docs/plan/record-size.py [--tsv OUT]

**READING 5'S DECIDER AS A TABLE**, where
``tests/test_a_record_is_no_larger_than_its_source.py`` is the same inequality as a GATE.
The gate answers yes or no; this answers "how big, and which ones", which is the question
``adcp-client-python-lzzj.5`` was filed on and had no instrument for.  Both read the same
three declarations in ``codegen.bundle`` -- :func:`~codegen.bundle.compact`,
:func:`~codegen.bundle.resolves` and :func:`~codegen.bundle.storage_bookkeeping` -- so the
table and the gate cannot disagree about what a record's size is.

* ``source`` -- the document's own text, compacted, so the comparison is not a statement
  about the ``indent=2`` the emitter writes with.
* ``record`` -- ``bundle.recorded``'s answer, compacted, LESS the bookkeeping its own
  storage requires: reading 5's first sentence asks for an entry per stored subtree and a
  reference at every occurrence, and those bytes are not duplication.
* ``resolved`` -- one copy per distinct subtree the references name, derived from the RAW
  bundle and never from the record.

A record over ``source + resolved`` is holding some subtree more than once, and the ratio
is how many times over.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from codegen import bundle, patch
from codegen.refusal import Refusal


def measured(bundle_dir: Path, document: str, known: frozenset[str]) -> dict:
    """One row: the three terms of the inequality and what they are made of."""
    raw = bundle.read(bundle_dir, document)
    answer = bundle.recorded(bundle_dir, document, known)
    if isinstance(answer, Refusal):
        return {"document": document, "refused": answer.detail}
    rec, origins = answer
    charged = bundle.resolves(bundle_dir, document, known)
    section = rec.get("definitions")
    entries = (
        sum(1 for key in section if key.startswith("Shared"))
        if isinstance(section, dict)
        else 0
    )
    source, record = bundle.compact(raw), bundle.compact(rec)
    spent = bundle.storage_bookkeeping(rec)
    record -= spent
    bound = source + charged
    return {
        "document": document,
        "source": source,
        "record": record,
        "resolved": charged,
        "bound": bound,
        "ratio": record / bound,
        "refs": len(bundle.references(raw)),
        "entries": entries,
        "spent": spent,
        "nodes": len(origins),
    }


def main(argv: list[str]) -> int:
    bundle_dir = patch.for_build(Path("schemas/cache/3.2"))
    every = sorted(bundle.portable(bundle_dir))
    known = frozenset(every)
    out = Path(argv[argv.index("--tsv") + 1]) if "--tsv" in argv else None
    rows = []
    for index, document in enumerate(every, start=1):
        rows.append(measured(bundle_dir, document, known))
        if index % 100 == 0:
            print(f"  {index}/{len(every)}", file=sys.stderr, flush=True)
    graded = [row for row in rows if "record" in row]
    over = sorted(
        (row for row in graded if row["record"] > row["bound"]),
        key=lambda row: -row["ratio"],
    )
    print(f"documents {len(rows)}, graded {len(graded)}, refused {len(rows) - len(graded)}")
    print(f"source total   {sum(r['source'] for r in graded):>14,}")
    print(f"record total   {sum(r['record'] for r in graded):>14,}")
    print(f"resolved total {sum(r['resolved'] for r in graded):>14,}")
    print(f"largest record {max(r['record'] for r in graded):>14,}")
    print(f"VIOLATE record > source + resolved: {len(over)} of {len(graded)}")
    for row in over[:25]:
        print(
            f"  {row['ratio']:7.2f}x  record {row['record']:>12,}  "
            f"bound {row['bound']:>12,}  refs {row['refs']:>5}  "
            f"entries {row['entries']:>4}  {row['document']}"
        )
    if out is not None:
        keys = ["document", "source", "record", "resolved", "bound", "ratio", "refs",
                "entries", "spent", "nodes"]
        with out.open("w") as handle:
            handle.write("\t".join(keys) + "\n")
            for row in sorted(graded, key=lambda r: -r["ratio"]):
                handle.write("\t".join(str(row[key]) for key in keys) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
