import collections
import json
import pathlib

up = json.loads(pathlib.Path("/tmp/sig_up.json").read_text())
ours = json.loads(pathlib.Path("/tmp/sig_ours.json").read_text())
blocking = {r["name"] for r in json.loads(pathlib.Path("/tmp/worklist.json").read_text())}

# index ours three ways, strongest first
by_ptr = {}
by_sig = collections.defaultdict(list)
by_name = collections.defaultdict(list)
for path, r in ours.items():
    if r["pointer"]:
        by_ptr.setdefault(r["pointer"], path)
    by_sig[(tuple(r["fields"]), tuple(r["required"]))].append(path)
    by_name[r["name"]].append(path)

# upstream names that our surface does not publish, restricted to the ones anything imports
import importlib
import sys

sys.path.insert(0, "src")
T = importlib.import_module("adcp.types")

rows, unresolved = [], []
seen = set()
for path, r in sorted(up.items()):
    n = r["name"]
    if n in seen:
        continue
    if hasattr(T, n):
        continue  # already served
    if n not in blocking:
        continue  # nothing imports it
    seen.add(n)
    how = target = None
    if r["pointer"] and r["pointer"] in by_ptr:
        how, target = "pointer", by_ptr[r["pointer"]]
    else:
        sig = (tuple(r["fields"]), tuple(r["required"]))
        cand = by_sig.get(sig) or []
        if len(cand) == 1:
            how, target = "signature", cand[0]
        elif len(cand) > 1:
            how, target = "signature-ambiguous", cand[0]
        elif by_name.get(n):
            how, target = "name", by_name[n][0]
    (rows if target else unresolved).append(
        {
            "name": n,
            "how": how,
            "target": target,
            "their_pointer": r["pointer"],
            "fields": len(r["fields"]),
        }
    )
print(f"upstream classes             : {len(up)}")
print(f"ours                         : {len(ours)}")
print(f"blocking names that are CLASSES and unserved: {len(rows) + len(unresolved)}")
print(f"  joined                     : {len(rows)}")
for h, c in collections.Counter(r["how"] for r in rows).items():
    print(f"      by {h:20s} {c}")
print(f"  NOT joined                 : {len(unresolved)}")
for r in unresolved[:12]:
    print(f"      {r['name']}  (their pointer: {r['their_pointer']})")
pathlib.Path("/tmp/alias_rows.json").write_text(json.dumps(rows, indent=1))
