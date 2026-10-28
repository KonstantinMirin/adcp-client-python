#!/usr/bin/env python3
"""The three numbers of ``adcp-client-python-10l.30``, measured over one run.

    PYTHONPATH=.:src .venv/bin/python docs/plan/10l30-measure.py [--names]

``emitted``/``refused``, the refusal KINDS read off ``Refusal.kind`` (never off a
sentence), and the approximation census.  Writes nothing.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

from adcp.types._base import UNDERDETERMINED, WIDENED
from codegen import emit, refusal
from codegen.refusal import Kind

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


def main() -> int:
    from codegen import bundle

    population = sorted(bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, population)
    kinds = collections.Counter()
    for document, row in out.refusals.items():
        kinds[row["kind"]] += 1
    deferred = [d for d, r in out.refusals.items() if r["kind"] == Kind.DEFERRED.value]
    verdicts = [d for d, r in out.refusals.items() if r["kind"] == Kind.VERDICT.value]
    chained = [d for d, r in out.refusals.items() if r["kind"] == Kind.CHAINED.value]
    primary = len(verdicts) + len(deferred)
    res = collections.Counter(r["resolved"] for r in out.refusals.values())
    print(f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
          f"(deferred {res[Kind.DEFERRED.value]}, verdict {res[Kind.VERDICT.value]})")
    print(f"kind: verdict {len(verdicts)}, deferred {len(deferred)}, chained {len(chained)}"
          f"  ->  primary {primary}, chained {len(chained)}")
    approximations = [one for d in out.approximations for one in out.approximations[d]]
    widened = [one for one in approximations if one.kind == WIDENED]
    undetermined = [one for one in approximations if one.kind == UNDERDETERMINED]
    upstream = [one for one in approximations if "#" in one.attribution]
    print(f"approximated {len(approximations)} facts in {len(out.approximations)} documents "
          f"(WIDENED {len(widened)}, UNDERDETERMINED {len(undetermined)}; "
          f"ours {len(approximations) - len(upstream)}, upstream {len(upstream)})")
    for one in undetermined:
        print(f"    UNDERDETERMINED {one.document}{one.pointer} {one.attribution}")
    print(f"accounted {len(out.emitted) + len(verdicts)}")
    if "--names" in sys.argv:
        Path("/tmp/run.json").write_text(json.dumps({
            "emitted": sorted(out.emitted),
            "refusals": {d: {k: str(v) for k, v in r.items()} for d, r in out.refusals.items()},
            "approximations": {
                d: [[one.pointer, one.keyword, one.kind, one.rung] for one in rows]
                for d, rows in out.approximations.items()
            },
        }, indent=1, default=str))
        print("wrote /tmp/run.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
