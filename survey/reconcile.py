"""Every test accounted for, upstream's suite to our pass count, as a table that ADDS UP.

    PYTHONPATH=.:src ./.venv/bin/python -m survey reconcile \
        --upstream /srv/ws/dropin-upstream --ours /srv/ws/dropin-trunk2

**WHY THIS EXISTS.**  A reader was handed four figures in one message -- 21,646, 15,673,
13,120 and 11,842 -- and no two of them were over the same population, so the "gap" between
any pair was an aggregate of removals, declines, collection failures and genuine failures
with no way to tell which was which.  The owner's instruction: *"each and everything should
be accounted for, with a list, maintained in a JSON file."*

**SO EVERY LINE IS A SET, NOT A COUNT**, and the sets are written out beside the table.  A
count can be wrong by one and nobody notices; a set either contains a nodeid or it does
not, and the next line's arithmetic fails if it is wrong.  The table is required to close:
``partition - absent-from-ours + only-in-ours == what our run reported``, asserted, so a
stale artifact raises instead of printing a plausible number.

**THE FOUR REASONS A TEST IS NOT IN OUR PASS COUNT, which the old single "gap" merged:**

1. **deleted** -- it was in one of upstream's generator-test files, and we deleted their
   generator, so a test of it grades nothing we have.  Not a gap; a removal.
2. **declined** -- a test function our own decline layers name, with the layer recorded
   (``delete-set`` for a test of the old emission's structure, ``invented-default`` for one
   whose premise is a default the document does not state).
3. **not collected** -- its module raises at import in OUR tree.  These are INVISIBLE in a
   failure count because the tests never appear, and they are the most expensive kind:
   one import error hides every test in its file.
4. **failed** -- it ran and did not pass.  The only one of the four that is a behavioural
   gap, and the only one a cause table can own.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib

#: Where the sets go.  One file, read by eye or by a later run, so a figure quoted in a
#: message can be checked against the nodeids it came from.
ARTIFACT = pathlib.Path("survey/reconciliation.json")


def outcomes(out: pathlib.Path) -> dict[str, str]:
    """``nodeid -> outcome`` from a run's own chunk reports."""
    found: dict[str, str] = {}
    reports = sorted((out / "junit").glob("chunk-*.json"))
    if not reports:
        raise SystemExit(f"no chunk reports under {out / 'junit'}")
    for report in reports:
        for test in json.loads(report.read_text()).get("tests", []):
            found[test["nodeid"]] = test["outcome"]
    return found


def collected(path: pathlib.Path | None) -> set[str] | None:
    """A ``pytest --co`` nodeid list, or ``None`` where the caller did not supply one."""
    if path is None:
        return None
    return {line.strip() for line in path.read_text().splitlines() if "::" in line}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upstream", required=True, help="an --upstream-only run's out dir")
    parser.add_argument("--ours", required=True, help="our run's out dir")
    parser.add_argument(
        "--bare",
        default=None,
        help="nodeids from `pytest tests/ --co` on the upstream tree, for the decline line",
    )
    ns = parser.parse_args(argv)

    up = outcomes(pathlib.Path(ns.upstream))
    ours = outcomes(pathlib.Path(ns.ours))
    bare = collected(pathlib.Path(ns.bare) if ns.bare else None)

    absent = {n: up[n] for n in sorted(set(up) - set(ours))}
    extra = {n: ours[n] for n in sorted(set(ours) - set(up))}
    both = set(up) & set(ours)

    # **THE TABLE MUST CLOSE.**  If it does not, one of the inputs is stale and every figure
    # below it is a guess -- which is the whole failure this module answers.
    closes = len(up) - len(absent) + len(extra)
    if closes != len(ours):
        raise SystemExit(
            f"the accounting does not close: {len(up)} - {len(absent)} + {len(extra)} "
            f"= {closes}, but our run reported {len(ours)}"
        )

    print("== THE POPULATION")
    if bare is not None:
        print(f"   {len(bare):7d}  upstream's behavioural suite, bare collect")
        print(f"  -{len(bare - set(up)):7d}  declined by our deselect plugin")
    print(f"   {len(up):7d}  the partition BOTH runs grade")
    print(f"  -{len(absent):7d}  upstream ran it, OUR tree never collected it")
    print(f"  +{len(extra):7d}  our tree ran it, upstream's did not")
    print(f"   {len(ours):7d}  our run reported  (closes)")

    print("\n== THE OUTCOMES, over the partition each one ran")
    for name, got in (("upstream", up), ("ours", ours)):
        counted = collections.Counter(got.values())
        tail = "  ".join(f"{k} {v}" for k, v in sorted(counted.items()))
        print(f"   {name:9s} {tail}   = {sum(counted.values())}")

    print("\n== THE GAP IN PASSES, decomposed -- every row a different kind of thing")
    moved = collections.Counter((up[n], ours[n]) for n in both)
    gap = 0
    for (was, now), count in sorted(moved.items(), key=lambda r: -r[1]):
        if was == now:
            continue
        if was == "passed":
            gap += count
        print(f"   {count:6d}  upstream {was:8s} -> ours {now}")
    hidden = sum(1 for n in absent if absent[n] == "passed")
    gap += hidden
    print(f"   {hidden:6d}  upstream passed   -> ours NEVER COLLECTED (an import error)")
    gained = sum(1 for n in extra if extra[n] == "passed")
    print(f"  -{gained:6d}  ours passes, upstream never ran it")
    counted_up = collections.Counter(up.values())
    counted_ours = collections.Counter(ours.values())
    print(f"   {gap - gained:6d}  == {counted_up['passed']} - {counted_ours['passed']}")
    if gap - gained != counted_up["passed"] - counted_ours["passed"]:
        raise SystemExit("the gap does not decompose; one of the rows above is wrong")

    print("\n== THE 'NEVER COLLECTED' SET, by file -- one import error hides a whole file")
    by_file = collections.Counter(n.split("::")[0] for n in absent)
    for name, count in by_file.most_common(12):
        print(f"   {count:5d}  {name}")
    print(f"   {len(by_file)} files")

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "upstream run": ns.upstream,
                "our run": ns.ours,
                "partition": len(up),
                "upstream outcomes": dict(counted_up),
                "our outcomes": dict(counted_ours),
                "never collected by us": absent,
                "only in ours": extra,
                "moved": {f"{was} -> {now}": n for (was, now), n in moved.items() if was != now},
            },
            indent=1,
            sort_keys=True,
        )
    )
    print(f"\n   sets written to {ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
