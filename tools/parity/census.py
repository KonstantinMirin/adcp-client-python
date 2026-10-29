"""What a CONSUMER can and cannot use in an emitted tree, and what a change renames.

Two instruments over the emitted tree, both derived from the tree itself so that neither
is a reading of a file listing:

::

    tools/parity/census.py --tree <dir>                      the usability census
    tools/parity/census.py --tree <after> --against <before>  the rename census

**The usability census.**  Each row is a shape a caller meets when they import our types,
counted over every class of the tree.  The rows are not style preferences; each one names
a thing a consumer cannot do:

``positional``
    a class whose name is its branch INDEX.  ``isinstance(req, AssetRequirementsBranch7)``
    requires counting the document's branches to learn that it means JavaScript.
``unexported``
    a class the module declares and its ``__all__`` does not name.  A union's BRANCHES are
    the case: ``core/requirements/asset_requirements.py`` exports ``AssetRequirements``
    alone, so the twelve arms a caller matches on are reachable only by a private path.
``undiscriminated``
    a union base whose ``_BRANCH_DISCRIMINATOR`` is empty.  There is no field a caller can
    read to learn which arm they hold; the only route is ``isinstance`` against the arms,
    which the previous two rows make hard to name and hard to import.
``any_typed``
    a field annotated ``Any`` (or ``dict[str, Any]`` at the top level of the annotation),
    which is the annotation that tells a type checker nothing.
``deep_name``
    a class whose name carries three or more ancestor segments, i.e. one §4's collision
    rule had to lengthen past the second hop -- the names no caller guesses.
``long_name``
    over 40 characters.

**The rename census.**  Symbol sets per module, before against after.  A name that
MOVES is a consumer's ``ImportError``, so the set is reported in full and never as a
count: the question a reviewer asks is "which classes could be reached before and cannot
after", and only the list answers it.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import re
import sys
from pathlib import Path

POSITIONAL = re.compile(r"Branch\d+$")


def classes(tree: Path) -> dict[str, dict]:
    """Every class statement of the tree, keyed ``module:name``, read by ``ast``.

    PARSED and not imported: the census runs over a tree that is not on ``sys.path`` and
    may not be installed, and a class's name, its bases, its ``__all__`` membership and
    its annotations are all syntax.  Importing would also run the module, which a
    comparison of two trees of the same package cannot do in one interpreter.
    """
    out: dict[str, dict] = {}
    for path in sorted(tree.rglob("*.py")):
        module = str(path.relative_to(tree).with_suffix("")).replace("/", ".")
        parsed = ast.parse(path.read_text(encoding="utf-8"))
        exported: set[str] = set()
        for node in parsed.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
            ):
                exported = {
                    e.value for e in getattr(node.value, "elts", ())
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }
        for node in parsed.body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields, flags = {}, {}
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    name = statement.target.id
                    text = ast.unparse(statement.annotation)
                    if name.startswith("_"):
                        flags[name] = ast.unparse(statement.value) if statement.value else ""
                    else:
                        fields[name] = text
            out[f"{module}:{node.name}"] = {
                "module": module,
                "name": node.name,
                "bases": [ast.unparse(b) for b in node.bases],
                "exported": node.name in exported,
                "fields": fields,
                "flags": flags,
                "doc": bool(ast.get_docstring(node)),
            }
    return out


def census(tree: Path) -> dict:
    found = classes(tree)
    rows: dict[str, list[str]] = collections.defaultdict(list)
    for key, cls in found.items():
        name = cls["name"]
        if POSITIONAL.search(name):
            rows["positional"].append(key)
        if not cls["exported"]:
            rows["unexported"].append(key)
        if cls["flags"].get("_BRANCH_DISCRIMINATOR") in ("''", '""'):
            rows["undiscriminated"].append(key)
        for field, annotation in cls["fields"].items():
            head = annotation.split("[")[0]
            if annotation == "Any" or head in ("Any",) or re.search(r"\bdict\[str, Any\]", annotation):
                rows["any_typed"].append(f"{key}.{field}")
        if len(name) > 40:
            rows["long_name"].append(key)
        if len(re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*", name)) >= 7:
            rows["deep_name"].append(key)
    return {"total": len(found), "rows": {k: sorted(v) for k, v in rows.items()}}


def renames(before: Path, after: Path) -> dict:
    was, now = classes(before), classes(after)
    modules = sorted({c["module"] for c in was.values()} | {c["module"] for c in now.values()})
    gone, new = collections.defaultdict(list), collections.defaultdict(list)
    for module in modules:
        old_names = {c["name"] for c in was.values() if c["module"] == module}
        new_names = {c["name"] for c in now.values() if c["module"] == module}
        for name in sorted(old_names - new_names):
            gone[module].append(name)
        for name in sorted(new_names - old_names):
            new[module].append(name)
    return {"removed": dict(gone), "added": dict(new),
            "before_total": len(was), "after_total": len(now)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--against", type=Path, default=None,
                    help="a BEFORE tree; prints the rename census instead")
    ap.add_argument("--show", type=int, default=12, help="examples per row")
    args = ap.parse_args(argv)

    if args.against is not None:
        out = renames(args.against, args.tree)
        print(f"classes: {out['before_total']} before, {out['after_total']} after")
        print("\n--- REMOVED (a consumer could reach these before and cannot after) ---")
        for module, names in sorted(out["removed"].items()):
            print(f"  {module}\n      {names}")
        print("\n--- ADDED ---")
        for module, names in sorted(out["added"].items()):
            print(f"  {module}\n      {names}")
        print(json.dumps({"removed": out["removed"], "added": out["added"]}, indent=1),
              file=sys.stderr)
        return 0

    out = census(args.tree)
    print(f"{out['total']} classes in {args.tree}\n")
    for row, hits in sorted(out["rows"].items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(hits):6d}  {row}")
        for hit in hits[: args.show]:
            print(f"            {hit}")
        if len(hits) > args.show:
            print(f"            ... {len(hits) - args.show} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
