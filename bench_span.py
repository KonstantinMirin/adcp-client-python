"""Time a COMMITTED SELECTION of pairs through ``check_pair``, one by one.

The iteration instrument for ``salesagent-j3k2l.25``, and the selection is data
rather than a search so that two runs of this file measure the same work. The
twelve names below SPAN the cost distribution, which is skewed about 20x and
skewed by DOCUMENT rather than by step-site count -- measured on the graded
population at ``7ffad8134``: 1,055 pairs, 27,791 step sites, mean 26.3 sites,
median 6, max 1,980, and one pair with 1 site inside a 124 KB document
(``enums/error-code.json``). A dozen convenient pairs would measure one corner
of that and generalise wrongly, so each entry below names which corner it is.

Per-pair seconds, never a total: a total can improve while a monster regresses,
and the monsters are what the suite's long pole is made of. Peak RSS is printed
beside the seconds, because a performance figure without a memory figure is what
produced a kernel kill here.

    uv run --no-sync python bench_span.py             # time the selection
    uv run --no-sync python bench_span.py --profile   # locate the next change
"""

from __future__ import annotations

import json
import resource
import sys
import time

sys.path.insert(0, "tests")

#: ``(pair name, why it is in the selection)``.  Site counts are as measured at
#: ``7ffad8134`` and are the reason each row was picked, not an assertion.
SELECTION: tuple[tuple[str, str], ...] = (
    ("enums/webhook-response-type.json#", "1 site, 225 B -- the floor of both axes"),
    ("enums/error-code.json#", "1 site, 124 KB -- few sites inside a large document"),
    ("collection/base-collection-source.json#/oneOf/0/properties/identifiers/items", "6 sites -- the median"),
    ("core/inventory-list-application.json#", "16 sites -- a oneOf with a discriminator"),
    ("core/async-response-refs/signals/get-signals-async-response-submitted.json#", "26 sites -- the mean"),
    ("core/canonical-product-action.json#", "60 sites"),
    ("core/attestation-subject.json#", "72 sites, 25 KB -- the 90th percentile"),
    ("core/signal-definition.json#", "121 sites"),
    ("creative/list-creatives-request.json#", "200 sites, 67 KB"),
    ("media-buy/provide-performance-feedback-request.json#", "228 sites -- the 99th percentile"),
    ("collection/get-collection-list-response.json#", "313 sites, 150 KB"),
    ("governance/audience-constraints.json#", "464 sites, 88 KB"),
    ("protocol/get-task-status-response.json#", "1,980 sites, 1.3 MB -- the monster"),
)


def _peak_mb() -> float:
    """Peak RSS of this process in MB (macOS reports ``ru_maxrss`` in bytes)."""
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / (1024 * 1024) if sys.platform == "darwin" else raw / 1024


def main() -> None:
    import test_emit as T

    by_name = {T.pair_of(g).name: g for g in T.graded()}
    missing = [n for n, _ in SELECTION if n not in by_name]
    if missing:
        raise SystemExit(f"selection names {len(missing)} pair(s) the tree does not grade: {missing}")

    if "--profile" in sys.argv:
        import cProfile
        import io
        import pstats

        name = sys.argv[sys.argv.index("--profile") + 1] if len(sys.argv) > sys.argv.index("--profile") + 1 else SELECTION[-1][0]
        pair = T.pair_of(by_name[name])
        pr = cProfile.Profile()
        pr.enable()
        T.check_pair(pair, max_steps=None)
        pr.disable()
        buf = io.StringIO()
        pstats.Stats(pr, stream=buf).sort_stats("tottime").print_stats(25)
        print(f"profile of {name} -- a profiled duration is NOT a before/after number")
        for line in buf.getvalue().splitlines():
            if "ncalls" in line or "site-packages" in line or "codegen/" in line:
                print(line[:150])
        return

    rows = []
    for name, why in SELECTION:
        pair = T.pair_of(by_name[name])
        start = time.perf_counter()
        rep = T.check_pair(pair, max_steps=None)
        seconds = time.perf_counter() - start
        rows.append({"pair": name, "why": why, "seconds": round(seconds, 3), "outcome": rep.outcome})
        print(f"{seconds:9.3f}s  peak {_peak_mb():7.1f} MB  {rep.outcome:28s} {name}", flush=True)
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
