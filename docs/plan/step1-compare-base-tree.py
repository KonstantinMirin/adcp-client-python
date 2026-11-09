"""Run the schema comparison against the tree the TEXT EMITTER wrote.

The red end of step 1's measurement, in one command.  The green end is in the
suite (``pytest tests/test_emit.py -k passes_all_three_checks``), but the suite
can only reach the committed tree, and the claim that the comparison catches
what a hand-rolled renderer drops is a claim about a tree that is no longer
there.  So this points the same ``compare_schema`` at it:

    git worktree add --detach /tmp/base-tree 11a9b2828
    PYTHONPATH=. uv run --no-sync python docs/plan/step1-compare-base-tree.py /tmp/base-tree
    git worktree remove /tmp/base-tree

11a9b2828 is the last commit whose ``_schemas/`` the text emitter produced.

Two things make it possible to grade a tree that predates ``__adcp_schema__``.
The pairing comes from that tree's own ``_bindings.json`` -- the emitter's record
of which document it lowered into which symbol, which is the only pairing that
tree has -- and ``sys.path`` puts the base worktree's ``src`` first, so ``adcp``
resolves there while ``codegen.harness`` is this tree's.  That works only because
the harness imports no ``adcp``: it knows no package, which is the property that
lets it grade output it did not emit.

The numbers it prints, at 11a9b2828: 43 pairs, 42 of which the comparison
refuses and 1 it passes; 475 facts compared, 108 the model does not state and 4
it states differently.
"""

from __future__ import annotations

import collections
import importlib
import json
import sys
from pathlib import Path


def main(base: Path, here: Path) -> int:
    sys.path.insert(0, str(here))
    sys.path.insert(0, str(base / "src"))
    from codegen.harness import compare_schema

    table = json.loads((base / "src/adcp/types/_schemas/_bindings.json").read_text())
    verdicts: collections.Counter[str] = collections.Counter()
    keywords: collections.Counter[str] = collections.Counter()
    compared = missing = differs = 0
    passing: list[str] = []

    for document, row in sorted(table.items()):
        module = importlib.import_module(row["module"])
        res = compare_schema(row["schema"], getattr(module, row["symbol"]))
        verdicts[res.outcome] += 1
        compared += res.compared
        missing += len(res.missing)
        differs += len(res.differs)
        for fact in res.missing + res.differs:
            keywords[fact.split(": ")[0].rsplit("/", 1)[-1]] += 1
        if res.outcome == "pass":
            passing.append(document)
        else:
            print(f"{document}  missing={len(res.missing)} differs={len(res.differs)}")
            for fact in res.missing + res.differs:
                print(f"    {fact[:160]}")

    print()
    print(f"pairs {sum(verdicts.values())}: {dict(verdicts)}")
    print(f"facts compared {compared}  the model states nothing {missing}  states otherwise {differs}")
    print(f"by keyword {dict(keywords.most_common())}")
    print(f"passing {passing}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004 -- the script's own name plus the worktree
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(__file__).resolve().parents[2]))
