"""Look up every upstream reference this repository cites, and print the registry.

``codegen/attribution.py``'s ``VERIFIED`` is a record of what somebody SAW when they
looked at ``adcontextprotocol/adcp``'s tracker.  A record like that has one failure mode --
nobody can tell it from an assertion -- so this is the half that makes the looking
reproducible: it re-derives the citations from the tree, asks the tracker about each one,
and prints the registry literal to paste back.

    gh auth status                       # the network half needs a token
    PYTHONPATH=.:src python survey/upstream_issues.py

READ-ONLY.  It runs ``gh issue view <n> --repo adcontextprotocol/adcp --json ...`` and
nothing else: it opens nothing, closes nothing and comments on nothing.  A reference that
does not resolve is recorded ``ABSENT`` rather than skipped, which is the state
``tests/test_decision_set.py``'s ``absent()`` gate reads -- a look that found nothing is a
measurement and a missing entry is not.

**THE CITATION CENSUS IS THE TEST'S, not a second one.**  The population comes from
``tests/test_decision_set.py`` -- its ``_cited`` and its ``CARRIED`` exclusion -- so this
script and the gate cannot come apart about which references exist.  That is the whole
reason it imports from ``tests/`` rather than re-deriving: a second census is a second
answer, and the one this prints has to be the one the gate will read back.

**A PULL REQUEST ANSWERS AS AN ISSUE.**  ``gh issue view`` resolves a PR number too (they
share a numbering space), which is deliberate: ``adcontextprotocol/adcp#8753`` is a PR
opened for the ``#8735`` title ask, and a citation naming it is a citation of something
that exists.  ``state`` is then the PR's -- ``OPEN``, ``CLOSED`` or ``MERGED`` -- and
``MERGED`` is recorded as ``CLOSED``, because what the registry needs to know is whether
the ask is still live.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from test_decision_set import CITATION, _cited

REPO = "adcontextprotocol/adcp"


def look(number: str) -> tuple[str, str]:
    """``(state, title)`` for one reference, as the tracker answers today.

    ``("ABSENT", "")`` where it does not resolve.  ``gh`` prints its own message on stderr
    and exits non-zero for that case, which is why the return code is read rather than the
    text: a parser over an error message is a parser over something nobody promised.
    """
    done = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            number,
            "--repo",
            REPO,
            "--json",
            "number,state,title",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        return ("ABSENT", "")
    answer = json.loads(done.stdout)
    state = "CLOSED" if answer["state"] == "MERGED" else answer["state"]
    return (state, answer["title"])


def main() -> int:
    """Print the registry literal, and a line per reference on stderr as it goes."""
    today = dt.datetime.now(tz=dt.UTC).date().isoformat()
    cited = _cited()
    rows = []
    for reference, files in sorted(cited.items()):
        (number,) = CITATION.findall(reference)
        state, title = look(number)
        print(f"{reference:34} {state:7} {title[:70]}", file=sys.stderr)
        print(f"{'':34} cited by {', '.join(files)}", file=sys.stderr)
        rows.append((reference, state, title))
    print("VERIFIED: Mapping[str, Sighting] = {")
    for reference, state, title in rows:
        print(f"    {reference!r}: Sighting(")
        print(f"        reference={reference!r},")
        print(f"        state={state!r},")
        print(f"        title={title!r},")
        print(f"        seen={today!r},")
        print("    ),")
    print("}")
    absent = [one for one in rows if one[1] == "ABSENT"]
    if absent:
        print(
            f"\n{len(absent)} reference(s) DO NOT EXIST and are cited anyway: {[one[0] for one in absent]}",
            file=sys.stderr,
        )
    return 1 if absent else 0


if __name__ == "__main__":
    sys.exit(main())
