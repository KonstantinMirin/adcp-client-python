"""Print THE JUDGMENT PASS over §3a's pending sets, and write the verdict table.

::

    PYTHONPATH=.:src ./.venv/bin/python survey/judgment.py            the counts
    PYTHONPATH=.:src ./.venv/bin/python survey/judgment.py table.json  and the table

The derivation is ``tests/judgment.py`` and is NOT restated here: the gate
(``tests/test_judgment_table.py``) grades the checked-in table against that one reading, so
a figure printed here and a figure a check ranges over cannot come apart.  That is
``test_patch_8525.py``'s own rule -- "the census lives beside the patch rather than in a
script that has been deleted" -- read for a reading that a test also needs.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from codegen import catalogue, emit
from tests.judgment import BUNDLE, COLLAPSE, SPLIT, UNDECIDABLE, judged, table


def main(argv: list[str]) -> int:
    rows = judged(catalogue.Admitted(BUNDLE), emit.standing_order(BUNDLE))
    for layer in ("L2", "L3"):
        mine = [row for row in rows if row.layer == layer]
        print(
            f"{layer}  {len(mine)} pending entries over "
            f"{sum(len(row.positions) for row in mine)} positions"
        )
        for outcome in (COLLAPSE, SPLIT, UNDECIDABLE):
            chosen = [row for row in mine if row.outcome == outcome]
            print(
                f"   {outcome:12} {len(chosen):4d} entries over "
                f"{sum(len(row.positions) for row in chosen):5d} positions"
            )
    counted = Counter(row.outcome for row in rows)
    print(
        f"TOTAL {len(rows)} entries over {sum(len(row.positions) for row in rows)} "
        "positions: " + ", ".join(f"{k} {v}" for k, v in sorted(counted.items()))
    )
    asked = [row for row in rows if not row.beneath_a_rule and row.layer == "L2"]
    posted = [row for row in rows if not row.beneath_a_rule and row.layer == "L3"]
    bare = [row for row in rows if row.beneath_a_rule]
    for what, rows_ in (("#8735 ASKS", asked), ("#8735 POSTS, does not ask", posted),
                        ("BARE behind q5g", bare)):
        print(
            f"{what}: {len(rows_)} entries over {sum(len(r.positions) for r in rows_)} "
            "positions -- " + ", ".join(
                f"{k} {v}" for k, v in sorted(Counter(r.outcome for r in rows_).items())
            )
        )
    print(
        "NAMED MEMBERS: "
        f"{sum(1 for r in rows if r.named)} entries have a position the bundle's own $refs "
        f"reach, of which {sum(1 for r in rows if r.named and r.outcome == COLLAPSE)} have "
        "the rest of the bundle agreeing with that name"
    )
    if argv:
        Path(argv[0]).write_text(json.dumps(table(rows), indent=2) + "\n")
        print(f"wrote {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
