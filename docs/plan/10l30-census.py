#!/usr/bin/env python3
"""Census the AUTHORED unions of the bundle and which pairs NOTHING separates.

Probe for ``adcp-client-python-10l.30``.  It reads the documents AS AUTHORED
(``bundle.read``, no reference resolution), finds every ``oneOf``/``anyOf`` whose
branches are all SHAPES, and asks BOTH separator readings of every pair:

* the WALK's -- ``codegen.lower.union.separates``, over ``Branch`` plans built by the
  production parse at BRANCH;
* the VERIFIER's -- ``codegen.harness.separates``, over the branch nodes.

Two readings and two answers, which is the point: §9 keeps them separate spellings so a
defect in one is not green on both sides.

    PYTHONPATH=.:src .venv/bin/python docs/plan/10l30-census.py [--walk|--verifier]
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path
from typing import Any

from codegen import bundle, compiler, harness, keywords
from codegen.keywords import Position
from codegen.lower import union as lower_union
from codegen.schema import parse as schema_parse

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


def _plan(raw: dict, pointer: str, document: str) -> lower_union.Branch:
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


def unions(document: str, doc: dict) -> list[tuple[str, str, list[dict], list[Any]]]:
    """Every authored union of SHAPES in one document, with the applied type per branch."""
    out = []
    for pointer, node in harness._rule_free_nodes(doc):
        for kw in ("oneOf", "anyOf"):
            branches = node.get(kw)
            if not isinstance(branches, list) or len(branches) < 2:
                continue
            if not all(isinstance(b, dict) for b in branches):
                continue
            if all(set(b) <= {"required"} for b in branches):
                continue
            applied = [b.get("type") or node.get("type") for b in branches]
            if not all(
                t == "object" or (t is None and b.get("properties")) for t, b in zip(applied, branches)
            ):
                continue
            base = "" if pointer == "/" else pointer
            out.append((f"{base}/{kw}", kw, branches, applied))
    return out


def main() -> int:
    sides = sys.argv[1:] or ["--walk", "--verifier"]
    for side in sides:
        walk = side == "--walk"
        total = refy = 0
        bad: dict[str, list[str]] = {}
        refbad: dict[str, list[str]] = {}
        pairs = refpairs = 0
        for document in sorted(bundle.portable(BUNDLE)):
            doc = bundle.read(BUNDLE, document)
            for at, kw, branches, applied in unions(document, doc):
                total += 1
                has_ref = any("$ref" in b for b in branches)
                refy += has_ref
                if walk:
                    planned = [
                        _plan(b, f"{at}/{i}", document) for i, b in enumerate(branches)
                    ]
                    unsep = [
                        f"{i},{j}"
                        for i in range(len(planned))
                        for j in range(i + 1, len(planned))
                        if lower_union.separates(planned[i], planned[j], applied[i], applied[j])
                        is None
                    ]
                else:
                    unsep = [
                        f"{i},{j}"
                        for i in range(len(branches))
                        for j in range(i + 1, len(branches))
                        if harness.separates(branches[i], branches[j], applied[i], applied[j])
                        is None
                    ]
                if not unsep:
                    continue
                if has_ref:
                    refbad[f"{document}#{at}"] = unsep
                    refpairs += len(unsep)
                else:
                    bad[f"{document}#{at}"] = unsep
                    pairs += len(unsep)
        reader = "walk (lower.union.separates)" if walk else "verifier (harness.separates)"
        print(f"=== {reader}")
        print(f"authored unions of shapes: {total}  ($ref branch: {refy}, non-$ref: {total - refy})")
        print(
            f"non-$ref inseparable: {len(bad)} unions, "
            f"{len({a.split('#')[0] for a in bad})} documents, {pairs} pairs"
        )
        for a, u in sorted(bad.items()):
            print(f"  {a}  {u}")
        print(
            f"$ref-branch inseparable: {len(refbad)} unions, "
            f"{len({a.split('#')[0] for a in refbad})} documents, {refpairs} pairs"
        )
        for a, u in sorted(refbad.items()):
            print(f"  {a}  {len(u)} pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
