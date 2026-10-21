"""Import each route's emitted module and grade every case against its own
schema with codegen.harness.check_pair, both directions."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cases import CASES  # noqa: E402

from codegen.harness import Pair, check_pair  # noqa: E402


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod  # a real package import does this; pydantic resolves deferred annotations through it
    spec.loader.exec_module(mod)
    return mod


def main(which: str) -> int:
    mod = load(Path(__file__).with_name(f"out_{which}.py"))
    bad = 0
    for symbol, schema in CASES.items():
        rep = check_pair(Pair(symbol, schema, getattr(mod, symbol)), accepts_examples=25,
                         refuses_examples=25, max_steps=None)
        acc = rep.accepts
        outcomes = [r.outcome for r in rep.refuses]
        acc_ok = acc.outcome == "pass"
        ref_ok = all(o in ("pass", "no_evidence") for o in outcomes)
        bad += (not acc_ok) + (not ref_ok)
        print(f"[{which}] {symbol}: direction1={acc.outcome} ({acc.examples} ex)  "
              f"direction2 sites={len(outcomes)} pass={outcomes.count('pass')} "
              f"no_evidence={outcomes.count('no_evidence')} wider={outcomes.count('model_accepted_invalid')} "
              f"harness={outcomes.count('harness_error')}")
        for r in rep.refuses:
            if r.outcome not in ("pass", "no_evidence"):
                print("    ", r.outcome, r.pointer, r.keyword, r.counterexample[:160], r.harness[:160])
        if not acc_ok:
            print("    NARROWER:", acc.detail[:200], acc.counterexample[:200])
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
