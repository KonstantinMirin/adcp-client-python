"""Row 34's measurement: the three numbers, the kind split, and the sibling sites.

Run as ``PYTHONPATH=.:src python survey/measure34.py``.  Nothing in the compiler reads
this; it is the row's own instrument.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

from codegen import bundle, emit, keywords, refusal
from adcp.types._base import KINDS

BUNDLE = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"


def main() -> None:
    documents = sorted(bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, documents)
    counted = collections.Counter(r["resolved"] for r in out.refusals.values())
    by_kind = collections.Counter(r["kind"] for r in out.refusals.values())
    verdicts = sum(counted[k] for k in refusal.FINAL_KINDS)
    declared = [a for one in out.approximations.values() for a in one]
    kinds = collections.Counter(a.kind for a in declared)
    ours = [a for a in declared if a.attribution.startswith(keywords.DOCUMENT)]
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
        f"({', '.join(f'{k} {n}' for k, n in sorted(counted.items()))}); "
        f"accounted {len(out.emitted) + verdicts}"
    )
    primary = sum(n for k, n in by_kind.items() if k != "chained")
    print(
        f"kind: {', '.join(f'{k} {n}' for k, n in sorted(by_kind.items()))}"
        f"  ->  primary {primary}, chained {by_kind['chained']}"
    )
    print(
        f"approximated {len(declared)} facts in {len(out.approximations)} documents "
        f"({', '.join(f'{k} {kinds[k]}' for k in KINDS)}; "
        f"ours {len(ours)}, upstream {len(declared) - len(ours)})"
    )
    Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/m34.json").write_text(
        json.dumps(
            {
                "emitted": sorted(out.emitted),
                "refusals": {
                    d: {
                        "keyword": r["keyword"],
                        "pointer": r["pointer"],
                        "kind": r["kind"],
                        "resolved": r["resolved"],
                        "detail": r["detail"],
                    }
                    for d, r in out.refusals.items()
                },
            },
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
