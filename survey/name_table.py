"""THE N:1 NAME TABLE: every name upstream publishes for a document, against OUR class for it.

**THE RELATION IS N:1 AND PIGEONHOLE SAYS SO BEFORE ANY MEASUREMENT.** Upstream's tree holds
3,226 classes and ours 2,500, both generated from one bundle, so some of our classes must
answer for several of their names. Measured: 89 of ours absorb 265 of theirs, up to 16:1
(`SIComponentCatalog`), because their generator promotes every inner node of a document to a
top-level class where we emit one class per subject. A 1:1 join cannot express that, and a
1:1 join was what this project had -- which is why 265 names read as an irreducible residue
for agents rather than as a fan-out.

**THE MODULE PATH IS THE DOCUMENT, and that is the whole key for half of it.** Their
`domains/brand/verify_brand_claims_request.py` and our
`_schemas/brand/verify_brand_claims_request.py`
are one document; 767 module paths are shared. Our classes carry `__adcp_schema__`, so OUR
side already knows its subject exactly. Nothing has to be inferred about it.

So the table is five rules, each a fact and none a comparison of class definitions:

``collapse``       the module holds ONE class of ours, so every name they publish for that
                   document denotes it. 423 modules, 522 names, and nothing to choose between.
``signature``      several of ours: the field-and-required set picks one, where it is unique.
``arm-order``      their ``X1`` is arm 0, ``X2`` is arm 1 -- their ordinal IS document order,
                   and our pointers carry the same index. 348 names.
``name``           the word is the same on both sides and unique in the module.
``property-key``   their generator names an inner class from a property KEY, so ``Setup``
                   is ``properties/setup`` and our class at that pointer is the match.

Everything these five cannot place is RESIDUE and goes to judgment -- 742 of 2,574, all of
them in modules where we hold several classes and neither the signature nor the ordinal
decides. The residue is reported, never guessed at.
"""

import collections
import json
import pathlib
import re

up = json.loads(pathlib.Path("/tmp/sig_up.json").read_text())
ours = json.loads(pathlib.Path("/tmp/sig_ours.json").read_text())


def rel(p, m):
    g = re.search(rf"adcp\.types\.{m}\.(.+)\.[A-Za-z_]\w*$", p)
    return g.group(1) if g else None


theirs_by_module = collections.defaultdict(list)
ours_by_module = collections.defaultdict(list)
for p, r in up.items():
    k = rel(p, "domains")
    if k:
        theirs_by_module[k].append(r)
for p, r in ours.items():
    k = rel(p, "_schemas")
    if k:
        ours_by_module[k].append({"path": p, **r})


def snake(name):
    """their inner class name -> the property key their generator took it from"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


rows, residue = [], []
for mod in sorted(set(theirs_by_module) & set(ours_by_module)):
    theirs, mine = theirs_by_module[mod], ours_by_module[mod]
    if len(mine) == 1:
        for t in theirs:
            rows.append({"their": t["name"], "ours": mine[0]["path"], "how": "collapse"})
        continue
    by_sig = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    by_tail = collections.defaultdict(list)  # last path segment of our pointer
    arms = []  # our arm classes, in document order
    for o in mine:
        by_sig[(tuple(o["fields"]), tuple(o["required"]))].append(o)
        by_name[o["name"]].append(o)
        ptr = o["pointer"] or ""
        tail = ptr.rstrip("/").split("/")[-1] if ptr else ""
        by_tail[tail].append(o)
        g = re.search(r"#/(?:oneOf|anyOf)/(\d+)$", ptr)
        if g:
            arms.append((int(g.group(1)), o))
    arms.sort()
    for t in theirs:
        sig = (tuple(t["fields"]), tuple(t["required"]))
        pick = how = None
        cand = by_sig.get(sig) or []
        if len(cand) == 1:
            pick, how = cand[0], "signature"
        elif len(by_name.get(t["name"], [])) == 1:
            pick, how = by_name[t["name"]][0], "name"
        else:
            g = re.match(r"^(.*?)(\d+)$", t["name"])
            if g and arms:
                k = int(g.group(2)) - 1  # their X1 is arm 0
                if 0 <= k < len(arms):
                    pick, how = arms[k][1], "arm-order"
            if pick is None:
                key = snake(t["name"])
                hit = by_tail.get(key) or []
                if len(hit) == 1:
                    pick, how = hit[0], "property-key"
        if pick:
            rows.append({"their": t["name"], "ours": pick["path"], "how": how})
        else:
            residue.append(
                {"their": t["name"], "module": mod, "ours_in_module": [o["name"] for o in mine]}
            )
total = sum(len(v) for k, v in theirs_by_module.items() if k in ours_by_module)
print(f"their names in shared modules : {total}")
print(f"  MAPPED                      : {len(rows)}  ({100 * len(rows) // total}%)")
for h, c in collections.Counter(r["how"] for r in rows).most_common():
    print(f"      {h:14s} {c}")
print(f"  residue for agents          : {len(residue)}")
pathlib.Path("/tmp/nto1b.json").write_text(json.dumps({"rows": rows, "residue": residue}, indent=1))
