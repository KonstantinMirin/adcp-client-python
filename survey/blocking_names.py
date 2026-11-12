"""Upstream's published surface against ours: which of them anything actually imports.

STATIC, BY AST, AND IT NEEDS NO WORKING TREE. The substituted tree cannot be
imported while 177 of upstream's files error at collection, and a tree that cannot
collect cannot tell you what it is missing -- so the census reads the SOURCE of both
trees and joins on the NAME. No import, so a recursion or an absent module cannot
hide a declaration from it.

Measured on upstream 9.6.1 at 4ed0bce87 against ours:

    upstream declares, we do not              1,105
      ...imported by upstream's TESTS           104   -> blocks 73 of their files
      ...imported by their kept MACHINERY        31
      ...referenced by NEITHER                  992   -> their dead numbered variants

VERIFIED AGAINST RUNTIME: all 1,105 are absent from ``adcp.types`` by ``getattr``
too, so the lazy facade rescues none of them and the AST reading is not an
overcount -- which it could have been, since a PEP 562 ``__getattr__`` resolves
names no AST shows.

AND IT REPLACES A FILE COUNT WITH A NAME COUNT. "177 files error at collection" was
not random, but it was the wrong unit: it decomposes into 73 files importing a name
we do not publish and 102 files behind one import recursion. The work list is the
NAMES, and there are 113 of them.
"""

import ast
import collections
import json
import pathlib

missing = set(json.loads(pathlib.Path("/tmp/missing.json").read_text()))
UPROOT = pathlib.Path("/srv/ws/wt-upbase")


def refs(root: pathlib.Path, subdir: str):
    """name -> set of files that IMPORT it from adcp.types*, by AST."""
    hit = collections.defaultdict(set)
    base = root / subdir
    for p in sorted(base.rglob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and "adcp" in n.module:
                for a in n.names:
                    if a.name in missing:
                        hit[a.name].add(str(p.relative_to(root)))
            elif isinstance(n, ast.Attribute):
                if isinstance(n.value, ast.Name) and n.attr in missing:
                    hit[n.attr].add(str(p.relative_to(root)))
    return hit


tests = refs(UPROOT, "tests")
machinery = refs(UPROOT, "src/adcp")
# machinery references from THEIR types tree are self-references, not demands on us
mach = {k: {f for f in v if "/types/" not in f} for k, v in machinery.items()}
mach = {k: v for k, v in mach.items() if v}

print(f"missing names (upstream declares, we do not) : {len(missing)}")
print(f"  ...IMPORTED by upstream's TESTS            : {len(tests)}")
print(f"  ...IMPORTED by upstream's kept MACHINERY   : {len(mach)}")
print(f"  ...referenced by NEITHER                   : {len(missing - set(tests) - set(mach))}")
print()
files = set()
for v in tests.values():
    files |= v
print(f"upstream test FILES blocked by a missing name: {len(files)}")
print()
print("the names their tests import, ranked by how many test files need each:")
for n, v in sorted(tests.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"  {len(v):4d}  {n}")
pathlib.Path("/tmp/blocking.json").write_text(
    json.dumps(
        {
            "tests": {k: sorted(v) for k, v in tests.items()},
            "machinery": {k: sorted(v) for k, v in mach.items()},
        },
        indent=0,
    )
)
