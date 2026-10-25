"""D3's new nested rule, measured over the WHOLE bundle rather than the emitted tree.

The rule as stated at 07c84c14a: "Nested: `pascal_case(property)`, qualified by the nearest
enclosing property only where two nodes of ONE MODULE would take the same name."

The plan measures 19 collisions in 9 modules over the emitted tree (1,062 classes, 678
modules).  The emitted tree is ~705 of 1,054 documents and excludes the shape unions, so this
re-measures over every portable document and asks the one question the qualifier's wording
leaves open: does the nearest enclosing property SEPARATE the colliding nodes, or do they
share that too?
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")
from codegen import bundle

B = Path("schemas/cache/3.2")


def pascal(s: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[^0-9A-Za-z]+", s) if p)


def nested_name(ptr: str) -> tuple[str, str] | None:
    """(name, the nearest enclosing property) for a nested node, per the new rule."""
    parts = [p for p in ptr.strip("/").split("/") if p]
    idx = None
    for i, p in enumerate(parts):
        if p == "properties" and i + 1 < len(parts):
            idx = i + 1
    if idx is None:
        return None
    name = pascal(parts[idx])
    for p in parts[idx + 1:]:
        if p == "items":
            name += "Item"
    # the NEAREST ENCLOSING property is the one before the node's own
    enclosing = None
    for i, p in enumerate(parts[:idx - 1]):
        if p == "properties" and i + 1 < len(parts):
            enclosing = parts[i + 1]
    return name, (enclosing or "")


#: Under ``not``, ``if``, ``then`` or ``else`` a keyword is a RULE (D6) and no class is
#: lowered from it, so a census counting one is mixing two populations -- the third of the
#: three counting rules in section 6.
RULE_HOPS = ("not", "if", "then", "else")


def is_model(node: dict) -> bool:
    return isinstance(node.get("properties"), dict) and bool(node["properties"])


def at_a_type_position(ptr: str) -> bool:
    return not any(p in RULE_HOPS for p in ptr.strip("/").split("/"))


per_module: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
for d in bundle.portable(B):
    doc = bundle.read(B, d)
    for ptr, n in bundle.nodes(doc):
        if ptr == "" or not is_model(n) or not at_a_type_position(ptr):
            continue
        got = nested_name(ptr)
        if got is None:
            continue
        name, enclosing = got
        per_module[d][name].append((ptr, enclosing))

classes = sum(len(v) for m in per_module.values() for v in m.values())
colliding_modules = {d: {k: v for k, v in m.items() if len(v) > 1}
                     for d, m in per_module.items()}
colliding_modules = {d: m for d, m in colliding_modules.items() if m}
coll_names = sum(len(m) for m in colliding_modules.values())
coll_nodes = sum(len(v) for m in colliding_modules.values() for v in m.values())

print("=== D3's new nested rule over all 1,054 portable documents ===")
print(f"nested model nodes taking a name      {classes}")
print(f"modules holding one or more           {len(per_module)}")
print(f"NAMES taken by two or more nodes      {coll_names}  in {len(colliding_modules)} modules")
print(f"nodes involved in a collision         {coll_nodes}")

resolved = unresolved = 0
worst: list[tuple[int, str, str, list]] = []
for d, m in colliding_modules.items():
    for name, rows in m.items():
        encl = {e for _, e in rows}
        if len(encl) == len(rows):
            resolved += 1
        else:
            unresolved += 1
            worst.append((len(rows), d, name, rows))
print(f"\ncollisions the nearest enclosing property SEPARATES   {resolved}")
print(f"collisions it does NOT separate                       {unresolved}")

worst.sort(reverse=True)
print("\n=== the collisions the qualifier does not separate, largest first ===")
for n, d, name, rows in worst[:14]:
    encl = Counter(e for _, e in rows)
    print(f"\n  {n:3d} nodes take {name!r} in {d}")
    print(f"      enclosing property values: {dict(encl)}")
    for ptr, e in rows[:4]:
        print(f"        {ptr}")
    if len(rows) > 4:
        print(f"        ... {len(rows) - 4} more")

# how many of the unresolved collisions sit under SIBLING combinator branches of one node?
print("\n=== are they siblings of one combinator? ===")
sib = other = 0
for n, d, name, rows in worst:
    stems = set()
    for ptr, _ in rows:
        stems.add(re.sub(r"/(oneOf|anyOf|allOf)/\d+", "/<branch>", ptr))
    if len(stems) == 1:
        sib += 1
    else:
        other += 1
print(f"  collisions whose members differ ONLY by a combinator index   {sib}")
print(f"  collisions with some other cause                            {other}")

json.dump({"classes": classes, "modules": len(per_module),
           "colliding_names": coll_names, "colliding_modules": len(colliding_modules),
           "resolved_by_qualifier": resolved, "not_resolved": unresolved,
           "sibling_branch_collisions": sib},
          open("survey/newd3.json", "w"), indent=1)
