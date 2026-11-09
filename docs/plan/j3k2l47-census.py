#!/usr/bin/env python3
"""Count the suite's CENSUS EQUALITIES -- a quantity asserted as ``== <int>``.

The instrument the row was briefed with (``assert ... == <int>``, read as text) misses
two spellings, and both are in this tree in quantity:

* an int inside a TUPLE, LIST, SET or DICT comparator -- ``assert (a, b) == (76, 397)``;
* an int behind a MODULE-LEVEL CONSTANT -- ``assert len(reports) == PAIRS_PIN``, where
  ``PAIRS_PIN = 1090`` sits at the top of the file.  Thirteen of those in
  ``tests/test_emit.py`` alone, each one re-pointed by hand at every emitting row, and
  every one invisible to a scan for a literal beside an ``==``.

0 and 1 are NOT census equalities and are not counted: ``== 0`` is "this part is empty",
which is a shape the design asks for, and ``== 1`` is "exactly one", which is a
structural claim about a single node rather than a tally over a set.  Every other
integer is a count of however many there turned out to be on one tree.

    python docs/plan/j3k2l47-census.py [-v]
"""

from __future__ import annotations

import ast
import collections
import pathlib
import sys

CENSUS_FLOOR = 2  # 0 is "empty", 1 is "exactly one"; a census starts at 2


def _ints(node: ast.AST, consts: dict[str, ast.AST]) -> list[int]:
    """Every census integer a comparator exposes, through containers and constants."""
    if isinstance(node, ast.Constant):
        v = node.value
        return [v] if isinstance(v, int) and not isinstance(v, bool) and v >= CENSUS_FLOOR else []
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [n for e in node.elts for n in _ints(e, consts)]
    if isinstance(node, ast.Dict):
        return [n for e in node.values if e is not None for n in _ints(e, consts)]
    if isinstance(node, ast.Name) and node.id in consts:
        return _ints(consts[node.id], {})  # one hop: a constant naming a constant is rare
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        # ``A_PIN - B_PIN``, which is two pins and not an arithmetic over a derived
        # quantity.  Multiplication and floor division are NOT followed: ``["x"] *
        # (len(steps) // 2)`` is a shape derived from the data, and its ``2`` is a
        # property of the pointer grammar rather than a count of anything.
        return _ints(node.left, consts) + _ints(node.right, consts)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return _ints(consts.get(node.value.id, ast.Pass()), {})
    return []


def census(root: pathlib.Path = pathlib.Path("tests")) -> tuple[collections.Counter, list]:
    counts: collections.Counter[str] = collections.Counter()
    rows = []
    for f in sorted(root.glob("*.py")):
        src = f.read_text()
        tree = ast.parse(src)
        consts = {
            t.id: n.value
            for n in tree.body
            if isinstance(n, (ast.Assign, ast.AnnAssign))
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
            if isinstance(t, ast.Name) and n.value is not None
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
                continue
            for op, comp in zip(node.test.ops, node.test.comparators):
                if not isinstance(op, ast.Eq):
                    continue
                found = _ints(comp, consts)
                if found:
                    counts[f.name] += len(found)
                    rows.append((f.name, node.lineno, found, ast.unparse(node.test)[:100]))
    return counts, rows


if __name__ == "__main__":
    counts, rows = census()
    for k, v in counts.most_common():
        print(f"{v:4d}  {k}")
    print("TOTAL", sum(counts.values()))
    if "-v" in sys.argv:
        print()
        for name, line, ints, text in rows:
            print(f"{name}:{line}  {ints}  | {text}")
