"""x-entity (515), deprecated (179), discriminator (81): what are they, and what do they touch?"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from codegen import bundle

BUNDLE = Path("schemas/cache/3.2")
DOCS = {d: bundle.read(BUNDLE, d) for d in bundle.portable(BUNDLE)}

# ---- x-entity ----
vals, where, co = Counter(), Counter(), Counter()
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        if "x-entity" in n:
            vals[json.dumps(n["x-entity"], sort_keys=True, default=str)[:120]] += 1
            where["ROOT" if ptr == "" else ptr.split("/")[-2] if "/" in ptr.strip("/") else "nested"] += 1
            co[frozenset(set(n) - {"x-entity"})] += 1
print(f"=== x-entity: {sum(vals.values())} sites, {len(vals)} distinct values ===")
for v, c in vals.most_common(12):
    print(f"  {c:5d}  {v}")
print(f"  ... {max(0, len(vals)-12)} more")
print("  co-occurring key sets (top 6):")
for s, c in co.most_common(6):
    print(f"    {c:5d}  {sorted(s)}")

# ---- deprecated ----
dv, dwhere, dco = Counter(), Counter(), Counter()
dep_docs = set()
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        if "deprecated" in n:
            dv[json.dumps(n["deprecated"])] += 1
            dwhere["ROOT" if ptr == "" else "nested"] += 1
            dco[frozenset(set(n) - {"deprecated"})] += 1
            dep_docs.add(d)
print(f"\n=== deprecated: {sum(dv.values())} sites in {len(dep_docs)} documents ===")
for v, c in dv.most_common():
    print(f"  {c:5d}  value={v}")
print(f"  root={dwhere['ROOT']} nested={dwhere['nested']}")
print("  co-occurring key sets (top 5):")
for s, c in dco.most_common(5):
    print(f"    {c:5d}  {sorted(s)}")

# ---- discriminator: does the named property carry a const in EVERY branch? ----
print("\n=== discriminator: is the named property const-tagged in every branch? ===")
tally = Counter()
bad = []
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        if "discriminator" not in n:
            continue
        name = n["discriminator"].get("propertyName") if isinstance(n["discriminator"], dict) else None
        if name is None:
            tally["discriminator with no propertyName"] += 1
            continue
        branches = n.get("oneOf") or n.get("anyOf")
        if not isinstance(branches, list):
            tally["no sibling oneOf/anyOf at the node"] += 1
            bad.append((d, ptr, name, "no sibling union"))
            continue
        tagged = 0
        for b in branches:
            if not isinstance(b, dict):
                continue
            p = (b.get("properties") or {}).get(name)
            if isinstance(p, dict) and ("const" in p or "enum" in p):
                tagged += 1
        if tagged == len(branches):
            tally["every branch const/enum-tags the named property"] += 1
        elif tagged == 0:
            tally["NO branch tags it inline (every branch is a $ref)"] += 1
            bad.append((d, ptr, name, f"0/{len(branches)} inline"))
        else:
            tally["SOME branches tag it"] += 1
            bad.append((d, ptr, name, f"{tagged}/{len(branches)} inline"))
for k, v in tally.most_common():
    print(f"  {v:5d}  {k}")
for b in bad[:10]:
    print(f"     e.g. {b[0]}#{b[1] or '/'}  propertyName={b[2]!r}  {b[3]}")

# ---- x-canonicalization: does it sit beside uniqueItems? ----
print("\n=== x-canonicalization ('set', 16 sites): what else is at the node? ===")
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        if "x-canonicalization" in n:
            print(f"  {d}#{ptr}  keys={sorted(set(n)-{'description'})}  uniqueItems={n.get('uniqueItems')}")
