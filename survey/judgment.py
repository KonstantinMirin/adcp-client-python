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
from tests.judgment import BUNDLE, COLLAPSE, SPLIT, UNDECIDABLE, ask_for, judged, table


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
    by_ask: dict[str, list] = {}
    for row in rows:
        by_ask.setdefault(ask_for(row), []).append(row)
    print("\nTHE ASK EACH ENTRY IS FILED UNDER, derived per entry:")
    for ask, mine in sorted(by_ask.items(), key=lambda kv: -len(kv[1])):
        print(
            f"  {len(mine):4d} entries over {sum(len(r.positions) for r in mine):5d} "
            "positions -- " + ", ".join(
                f"{k} {v}" for k, v in sorted(Counter(r.outcome for r in mine).items())
            )
        )
        print(f"        {ask}")
    carried = [r for r in rows if ask_for(r).startswith("adcontextprotocol")]
    bare = [r for r in rows if "BARE" in ask_for(r)]
    none = [r for r in rows if ask_for(r).startswith("none owed")]
    print(
        f"\nFILED {len(carried)} / BARE {len(bare)} / NO ASK OWED {len(none)}  "
        f"(= {len(carried) + len(bare) + len(none)} of {len(rows)})"
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
