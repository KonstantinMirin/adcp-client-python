#!/usr/bin/env python3
"""Fire-probe a converted check: perturb what it grades and confirm it REDDENS.

A conversion you cannot make fail on purpose is not graded, and the suite passing
afterwards proves nothing about it.  Each probe is (file, old text, new text, nodeid):
the replacement is applied, the nodeid is run, the file is restored from the copy this
script took -- never from git, because a checkout eats anything else in the tree.

    CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python docs/plan/j3k2l47-probe.py probes.json

Each probe in the JSON list is ``{"file":..., "old":..., "new":..., "nodeid":...}``.
``old`` must occur exactly once.  Exit status is the number of probes that did NOT
redden, so 0 means every conversion is graded.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


def main(spec: pathlib.Path) -> int:
    probes = json.loads(spec.read_text())
    unreddened = []
    for i, probe in enumerate(probes, 1):
        path = pathlib.Path(probe["file"])
        original = path.read_text()
        count = original.count(probe["old"])
        if count != 1:
            print(f"[{i}] SPEC ERROR: 'old' occurs {count} times in {path}")
            unreddened.append(probe["nodeid"])
            continue
        path.write_text(original.replace(probe["old"], probe["new"], 1))
        try:
            done = subprocess.run(
                [sys.executable, "-m", "pytest", probe["nodeid"], "-q", "-p", "no:randomly", "-x"],
                capture_output=True,
                text=True,
            )
        finally:
            path.write_text(original)
        reddened = done.returncode != 0
        tail = [ln for ln in done.stdout.splitlines() if ln.strip()][-1:] or [""]
        print(f"[{i}] {'REDDENS' if reddened else 'STAYED GREEN'}  {probe['nodeid']}")
        print(f"      perturbation: {probe.get('what', probe['old'][:70])}")
        print(f"      {tail[0][:160]}")
        if not reddened:
            unreddened.append(probe["nodeid"])
    print(f"\n{len(probes) - len(unreddened)}/{len(probes)} probes reddened")
    for n in unreddened:
        print(f"  NOT GRADED: {n}")
    return len(unreddened)


if __name__ == "__main__":
    raise SystemExit(main(pathlib.Path(sys.argv[1])))
