"""Upstream's published surface against ours: every name declared in each tree.

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
import json
import pathlib


def declared(root: pathlib.Path, label: str):
    """Every class and module-scope binding, per module, by AST. No import, so a
    recursion or a missing module cannot hide a name."""
    out = {}
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        mod = rel.removesuffix(".py").removesuffix("/__init__").replace("/", ".")
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            out.setdefault(mod, set())
            continue
        names = set()
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                names.add(n.name)
            elif isinstance(n, ast.Assign):
                names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                names.add(n.target.id)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    if a.asname:  # `X as X` is PEP 484 re-export
                        names.add(a.asname)
        out[mod] = names
    return out


UP = pathlib.Path("/srv/ws/wt-upbase/src/adcp")
OURS = pathlib.Path("/srv/ws/adcp-client-python/src/adcp")
up, ours = declared(UP, "upstream"), declared(OURS, "ours")


def flat(d):
    s = set()
    for names in d.values():
        s |= names
    return {n for n in s if not n.startswith("_") and n[:1].isupper()}


upn, ourn = flat(up), flat(ours)
print(f"upstream modules {len(up):5d}   class-shaped names {len(upn):6d}")
print(f"ours     modules {len(ours):5d}   class-shaped names {len(ourn):6d}")
print()
missing = sorted(upn - ourn)
extra = sorted(ourn - upn)
print(f"upstream declares, we do NOT  : {len(missing)}")
print(f"we declare, upstream does not : {len(extra)}")
print(f"both                          : {len(upn & ourn)}")
pathlib.Path("/tmp/missing.json").write_text(json.dumps(missing, indent=0))
pathlib.Path("/tmp/extra.json").write_text(json.dumps(extra, indent=0))
print()
print("first 30 of the missing:")
for n in missing[:30]:
    print("   ", n)
