import importlib
import json
import pathlib
import re
import sys

sys.path.insert(0, "src")

ledger = json.loads(pathlib.Path("survey/name-decisions-9.6.1.json").read_text())
joined = {r["name"]: r for r in json.loads(pathlib.Path("/tmp/alias_rows.json").read_text())}
work = json.loads(pathlib.Path("/tmp/worklist.json").read_text())
T = importlib.import_module("adcp.types")

DOTTED = re.compile(r"\badcp\.types\.(?:_schemas\.)?[A-Za-z_][\w.]*\.[A-Z]\w+")


def from_ledger(r):
    """the dotted path the ledger resolved, if it names one that imports"""
    for field in ("our_type", "use_instead"):
        v = r.get(field) or ""
        for m in DOTTED.finditer(v):
            path = m.group(0)
            mod, _, cls = path.rpartition(".")
            try:
                if hasattr(importlib.import_module(mod), cls):
                    return mod, cls
            except Exception:
                continue
    return None


rows, unresolved = [], []
byname = {r["name"]: r for r in ledger}
for w in sorted(work, key=lambda r: -(r["test_files"] * 10 + r["machinery_files"])):
    n = w["name"]
    if hasattr(T, n):
        continue
    got = None
    if n in byname:
        got = from_ledger(byname[n])
    if got is None and n in joined and joined[n]["target"]:
        mod, _, cls = joined[n]["target"].rpartition(".")
        try:
            if hasattr(importlib.import_module(mod), cls):
                got = (mod, cls)
        except Exception:
            got = None
    if got:
        rows.append(
            {
                "name": n,
                "module": got[0],
                "symbol": got[1],
                "tests": w["test_files"],
                "machinery": w["machinery_files"],
            }
        )
    else:
        unresolved.append(n)

print(f"blocking names unserved : {len(rows) + len(unresolved)}")
print(f"  RESOLVED, aliasable   : {len(rows)}")
print(f"  unresolved            : {len(unresolved)}")
for n in unresolved:
    print(f"      {n}")
pathlib.Path("/tmp/final_aliases.json").write_text(json.dumps(rows, indent=1))
