"""Time ONE pair through check_pair.  The iteration unit for salesagent-j3k2l.25.

Deterministic: picks the graded pair whose step-site count is nearest TARGET, so
before and after measure the same work.  Prints seconds and the site count.
Run with --profile to get the top of a cProfile instead of a timing; never quote
a profiled duration as a before/after number.
"""

from __future__ import annotations

import sys
import time

sys.path.insert(0, "tests")

TARGET = 40


def pick(T, harness):
    best = None
    for g in T.graded():
        p = T.pair_of(g)
        try:
            n = len(harness.steps(p.schema))
        except Exception:
            continue
        if best is None or abs(n - TARGET) < abs(best[0] - TARGET):
            best = (n, g)
    return best


def main() -> None:
    import test_emit as T

    from codegen import harness

    n, g = pick(T, harness)
    p = T.pair_of(g)
    print(f"pair  {p.name}")
    print(f"sites {n}")

    if "--profile" in sys.argv:
        import cProfile
        import io
        import pstats

        pr = cProfile.Profile()
        pr.enable()
        T.check_pair(p, max_steps=None)
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(18)
        for line in s.getvalue().splitlines():
            if "ncalls" in line or "site-packages" in line or "codegen/" in line:
                print(line[:150])
        return

    t = time.perf_counter()
    T.check_pair(p, max_steps=None)
    print(f"SECONDS {time.perf_counter() - t:.2f}")


if __name__ == "__main__":
    main()
