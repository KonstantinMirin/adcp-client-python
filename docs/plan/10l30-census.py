#!/usr/bin/env python3
"""Census the AUTHORED unions of the bundle and which pairs NOTHING separates.

The measurement ``adcp-client-python-10l.30``'s acceptance criterion names, DERIVED on
both sides rather than pinned.  It reads the documents AS AUTHORED (``bundle.read``, no
reference resolution), takes every ``oneOf``/``anyOf`` whose branches are all SHAPES --
the gate both halves of §8's third equality already apply, because that is the set where
branch CLASSES exist and a declaration order has something to choose between -- and asks
BOTH separator readings of every pair:

* the WALK's -- ``codegen.lower.union.separates``, over ``Branch`` plans built by the
  production parse at BRANCH and ``union.forbidden_names``;
* the VERIFIER's -- ``codegen.harness.separates``, over the branch nodes.

Two readings and two answers, which is the point: §9 keeps them separate spellings so a
defect in one is not green on both sides.  The population is SPLIT on whether a branch
states a ``$ref`` anywhere inside it: §4's reading of such a branch may live in the
target, which neither side resolves, so the row is measured over the remainder and the
``$ref`` half is reported rather than fixed.

    PYTHONPATH=.:src .venv/bin/python docs/plan/10l30-census.py [--walk|--verifier]

``tests/test_union_disjointness.py`` carries the same two derivations as assertions --
the two readings agree pair by pair, and the inseparable remainder is named and
partitioned -- so this script is the reader's view of a figure the suite already grades.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from codegen import bundle, harness
from codegen.keywords import Position
from codegen.lower import union as lower_union
from codegen.schema import parse as schema_parse

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


def planned(raw: dict, pointer: str, document: str) -> lower_union.Branch:
    """One branch as the walk plans it: the declaration, the parse, and the rules."""
    parsed = schema_parse.parse(
        raw,
        pointer=pointer,
        position=Position.BRANCH,
        source=schema_parse.Source(document=document),
    )
    return lower_union.Branch(
        pointer=pointer,
        node=raw,
        parsed=parsed,
        forbids=lower_union.forbidden_names(parsed, raw),
    )


def states_a_reference(node: Any) -> bool:
    """Does this branch state a ``$ref`` anywhere inside it?"""
    if isinstance(node, dict):
        return "$ref" in node or any(states_a_reference(v) for v in node.values())
    if isinstance(node, list):
        return any(states_a_reference(v) for v in node)
    return False


def unions() -> list[tuple[str, list[dict], list[Any]]]:
    """Every authored union of 3.2 whose branches are all shapes, with the applied type.

    A presence-only combinator is excluded, because it lowers to a rule on the enclosing
    class (``schema.presence_only``, the parser's own reading) and declares no branch
    classes for an order to choose between.
    """
    out = []
    for document in sorted(bundle.portable(BUNDLE)):
        doc = bundle.read(BUNDLE, document)
        for pointer, node in harness._rule_free_nodes(doc):
            for keyword in ("oneOf", "anyOf"):
                branches = node.get(keyword)
                if not isinstance(branches, list) or len(branches) < 2:  # noqa: PLR2004
                    continue
                if not all(isinstance(b, dict) for b in branches):
                    continue
                if schema_parse.presence_only({keyword: branches}, Position.ROOT):
                    continue
                applied = [b.get("type") or node.get("type") for b in branches]
                if not all(
                    t == "object" or (t is None and b.get("properties"))
                    for t, b in zip(applied, branches, strict=True)
                ):
                    continue
                base = "" if pointer == "/" else pointer
                out.append((f"{document}#{base}/{keyword}", branches, applied))
    return out


def main() -> int:
    population = unions()
    with_a_reference = {
        at for at, branches, _ in population if any(states_a_reference(b) for b in branches)
    }
    print(
        f"authored unions of shapes: {len(population)}  "
        f"($ref inside a branch: {len(with_a_reference)}, "
        f"non-$ref: {len(population) - len(with_a_reference)})"
    )
    for side in sys.argv[1:] or ["--walk", "--verifier"]:
        walk = side == "--walk"
        halves: dict[bool, dict[str, list[str]]] = {True: {}, False: {}}
        for at, branches, applied in population:
            if walk:
                plans = [planned(b, f"{at}/{i}", at) for i, b in enumerate(branches)]
                unseparated = [
                    f"{i},{j}"
                    for i in range(len(plans))
                    for j in range(i + 1, len(plans))
                    if lower_union.separates(plans[i], plans[j], applied[i], applied[j]) is None
                ]
            else:
                unseparated = [
                    f"{i},{j}"
                    for i in range(len(branches))
                    for j in range(i + 1, len(branches))
                    if harness.separates(branches[i], branches[j], applied[i], applied[j]) is None
                ]
            if unseparated:
                halves[at in with_a_reference][at] = unseparated
        reader = "walk (lower.union.separates)" if walk else "verifier (harness.separates)"
        print(f"=== {reader}")
        for referencing, label in ((False, "non-$ref"), (True, "$ref inside a branch")):
            found = halves[referencing]
            print(
                f"  {label}: {len(found)} unions, "
                f"{len({a.split('#')[0] for a in found})} documents, "
                f"{sum(len(v) for v in found.values())} pairs"
            )
            for at, pairs in sorted(found.items()):
                shown = pairs if len(pairs) <= 6 else f"{len(pairs)} pairs"  # noqa: PLR2004
                print(f"    {at}  {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
