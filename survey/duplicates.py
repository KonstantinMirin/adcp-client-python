"""Print THE DUPLICATE CENSUS over the emitted tree, and the decision for each group.

::

    PYTHONPATH=.:src ./.venv/bin/python survey/duplicates.py

The derivation is ``tests/test_one_node_is_one_declaration.py`` and the table is
``tests/duplicates.py``, and NEITHER is restated here: the gate in that file grades the
table against the same reading, so a figure printed here and a figure a check ranges over
cannot come apart.  That is ``test_patch_8525.py``'s rule -- *"the census lives beside the
patch rather than in a script that has been deleted"* -- read for a reading a test needs
too.

**THE FIGURES THIS PRINTS ARE OVER CLASS OBJECTS AND NEVER OVER NAMES OR FIELD SETS.**  A
field-set key is the instrument behind every wrong figure this epic reported (790, 718,
650, 547, 242); a name key is what ``model_json_schema()``'s ``title`` makes of the
five-part key if the title is left in.  Both corrections are in the derivation and this
script only reads it.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

import duplicates  # the sys.path line above is what makes these three resolve
import fresh  # noqa: F401  -- binds the generated half of adcp.types to a fresh run
import test_one_node_is_one_declaration as gate


def main() -> int:
    tree = gate.the_tree()
    declarations = [cls for members in tree.values() for cls in members]
    groups = gate.grouped(declarations)
    repeated = {key: members for key, members in groups.items() if len(members) > 1}
    live = gate.cross_document_groups(declarations)
    decided = duplicates.by_position()

    print(f"class objects                      {len(declarations)}")
    print(f"distinct types                     {len(groups)}")
    print(
        f"types declared more than once      {len(repeated)}  over "
        f"{sum(len(members) for members in repeated.values())} declarations"
    )
    print(f"SAME-document groups               {len(gate.restated_within_one_document(declarations))}")
    print(f"cross-document groups              {len(live)}")
    print(f"rows of the decision table         {len(decided)}   <- the DEBT figure")
    print()
    counted = Counter(row.outcome for row in duplicates.DECIDED)
    for outcome, count in sorted(counted.items()):
        print(f"   {outcome:16} {count} rows")
    print()

    for at in sorted(live, key=sorted):
        row = decided.get(at)
        members = live[at]
        print(f"=== {len(members)} declarations -- {row.outcome if row else 'NO ROW -- UNDECIDED'}")
        for member in sorted(members, key=lambda cls: f"{cls.__module__}.{cls.__name__}"):
            document, pointer = duplicates.at_of(member) or ("?", "?")
            print(f"      {member.__name__:42} {document}{pointer}")
        if row is None:
            print("      ** no row in tests/duplicates.py answers this group **")
            continue
        print(f"      defect: {row.defect}")
        print(f"      ask   : {row.ask}")
        if row.payload is not duplicates.NO_PAYLOAD:
            print(f"      proved by: {row.payload}")
        if row.names_the_subject is not None:
            print(f"      named at : {row.names_the_subject}")
    stale = set(decided) - set(live)
    if stale:
        print("\nROWS WHOSE GROUP THE TREE NO LONGER FORMS -- DELETE THEM:")
        for at in sorted(stale, key=sorted):
            print(f"   {sorted(at)}  {decided[at].ask}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
