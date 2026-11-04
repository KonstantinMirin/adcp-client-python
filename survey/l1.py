"""The four layers of §3a's catalogue, one census each, keyed on that layer's own identity.

INSTRUMENT, not a gate: it reports the readings and asserts nothing.  Reading 4 ranges over
all four layers, and its own ``Decided by`` says each census is keyed on that layer's own
identity -- the value list, the constraint set, the field set, the element type.  **Every
figure here comes from ``codegen/catalogue.py``** and none is re-derived, which is the rule
about a derived reading having one owner: an instrument that recomputed a layer's identity
would be a second answer to drift from the compiler's.

    PYTHONPATH=.:src ./.venv/bin/python survey/l1.py [schemas/cache/3.2]
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codegen import catalogue, constraints, emit


def l0(bundle_dir: Path) -> None:
    print("=== L0  key: the VALUE LIST ===")
    found = catalogue.collect(bundle_dir)
    keys = collections.Counter(catalogue.value_list(p) for p in found.positions)
    print(f"  stating positions                 {len(found.positions)}")
    print(f"  distinct value lists              {len(keys)}")
    print(f"  stated at more than one position  {len([k for k, n in keys.items() if n > 1])}")
    print(f"  one document only (§4's dedup)    {len(found.restated)}")
    print(f"  NAMED entries                     {len(found.entries)}")
    print(f"  untitled -- the upstream ask      {len(found.untitled)}"
          f"  positions {sum(len(g) for g in found.untitled)}")
    print(f"  conflicting titles                {len(found.conflicting)}")


def l1(bundle_dir: Path) -> None:
    print("=== L1  key: the CONSTRAINT SET ===")
    found = catalogue.collect_scalars(
        bundle_dir,
        frozenset(keyword for keyword, _ in constraints.SPELLING),
        constraints.symbol,
    )
    keys = collections.Counter(p.key for p in found.positions)
    pending = found.pending_a_name
    print(f"  stating positions                 {len(found.positions)}")
    print(f"  distinct constraints              {len(found.entries)}")
    print(f"  stated at more than one position  {len([k for k, n in keys.items() if n > 1])}")
    print(f"  stated in more than one document  "
          f"{len([e for e in found.entries.values() if len(e.documents) > 1])}")
    print(f"  §4 step 1  the bundle names it    {len(found.named_by_the_bundle)}")
    print(f"  §4 step 2  the constraint in words{len(found.named_by_the_constraint)}")
    print(f"  §4 step 3  the declaring position {len(pending)}   <- pending a name")
    print(f"    positions they cover            {sum(len(e.positions) for e in pending)}")
    print(f"    documents they touch           "
          f" {len(set().union(*[e.documents for e in pending])) if pending else 0}")
    for entry in sorted(pending, key=lambda e: -len(e.positions))[:10]:
        print(f"      {entry.name:62} {len(entry.positions):4} pos {len(entry.documents):3} docs")


def structural(bundle_dir: Path, layer: str, key: str) -> None:
    print(f"=== {layer}  key: {key} ===")
    # ``emit.standing_order`` is §3a's home rule's own input and the RUN's own reading of
    # it, handed in rather than recomputed here -- which is this file's own rule about a
    # derived reading having one owner.
    found = catalogue.collect_shapes(
        catalogue.Admitted(bundle_dir), layer, emit.standing_order(bundle_dir)
    )
    keys = collections.Counter(p.key for p in found.positions)
    print(f"  stating positions                 {len(found.positions)}")
    print(f"  distinct structures               {len(keys)}")
    print(f"  stated at more than one position  {len([k for k, n in keys.items() if n > 1])}")
    print(f"  one document only (§4's dedup)    {len(found.restated)}")
    print(f"  COLLECTED entries                 {len(found.entries)}"
          f"  restating positions {sum(len(e.restating) for e in found.entries.values())}")
    steps = collections.Counter(e.step for e in found.entries.values())
    print(f"    §4 step 1  the bundle's title   {steps[1]}"
          f"  restating {sum(len(e.restating) for e in found.entries.values() if e.step == 1)}")
    print(f"    §4 step 2  the structure in words {steps[2]}"
          f"  restating {sum(len(e.restating) for e in found.entries.values() if e.step == 2)}")
    print(f"    §4 step 3  the declaring position {steps[3]}"
          f"  restating {sum(len(e.restating) for e in found.entries.values() if e.step == 3)}")
    print(f"  withheld, enumerated              {len(found.withheld)}")
    print(f"  undeclared, enumerated            {len(found.undeclared)}")
    print(f"  NOT COLLECTED, no title anywhere  {len(found.untitled)}"
          f"  positions {sum(len(g) for g in found.untitled)}")
    print(f"  conflicting titles                {len(found.conflicting)}")
    print(f"  every position a document ROOT    {len(found.duplicated)}"
          f"  positions {sum(len(g) for g in found.duplicated)}")
    print(f"  no position declares a class      {len(found.declaring_nothing)}"
          f"  positions {sum(len(g) for g in found.declaring_nothing)}")


def main() -> None:
    bundle_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "schemas/cache/3.2")
    l0(bundle_dir)
    l1(bundle_dir)
    structural(bundle_dir, "L2", "the FIELD SET (catalogue.Admitted)")
    structural(bundle_dir, "L3", "the ELEMENT TYPE (catalogue.Admitted)")


if __name__ == "__main__":
    main()
