"""The same question, answered deterministically: no generator, with a one-item control.

If a ONE-item list is accepted, the hand-built item conforms.  If the TWO-item list whose
items share the `unique_item_properties` key is also accepted, the DOCUMENT admits what the
extension keyword forbids -- so a class enforcing the keyword refuses a payload
`strict_validate`'s schema half accepts.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")
from jsonschema import Draft7Validator, FormatChecker

from codegen import bundle

B = Path("schemas/cache/3.2")
FC = FormatChecker()


def seed(sub: dict, depth: int = 0) -> object:
    """A minimal conforming value, read off the subschema itself."""
    if depth > 6 or not isinstance(sub, dict):
        return "x"
    if "const" in sub:
        return sub["const"]
    if "enum" in sub:
        return sub["enum"][0]
    t = sub.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), t[0])
    if t == "object" or "properties" in sub:
        out = {}
        for k in sub.get("required", []):
            out[k] = seed((sub.get("properties") or {}).get(k, {}), depth + 1)
        return out
    if t == "array":
        n = max(1, int(sub.get("minItems", 1)))
        return [seed(sub.get("items") or {}, depth + 1) for _ in range(n)]
    if t == "integer":
        return int(sub.get("minimum", sub.get("exclusiveMinimum", 0) + 1
                           if "exclusiveMinimum" in sub else 1))
    if t == "number":
        return float(sub.get("minimum", 1))
    if t == "boolean":
        return True
    if t == "null":
        return None
    fmt, pat = sub.get("format"), sub.get("pattern")
    if fmt == "uri":
        return "https://x.example/p"
    if fmt == "date-time":
        return "2026-01-01T00:00:00Z"
    if fmt == "date":
        return "2026-01-01"
    if fmt == "uuid":
        return "00000000-0000-4000-8000-000000000000"
    if pat:
        for cand in ("x", "abc", "x1", "a_b", "AAA", "xyz_1", "1"):
            if re.search(pat, cand):
                return cand
        return "x"
    return "x" * max(1, int(sub.get("minLength", 1)))


def sites() -> list[tuple[str, str, list[str]]]:
    out = []
    for d in bundle.portable(B):
        for ptr, n in bundle.nodes(bundle.read(B, d)):
            v = n.get("x-adcp-validation")
            if isinstance(v, dict) and isinstance(v.get("unique_item_properties"), list):
                out.append((d, ptr, v["unique_item_properties"]))
    return out


print("=== unique_item_properties: does the DOCUMENT accept two items sharing the key? ===")
tally = {"accepts the duplicate": 0, "control failed (witness not conforming)": 0,
         "refused with the duplicate": 0, "unresolvable": 0}
for doc_name, ptr, keys in sites():
    try:
        root = bundle.resolved(B, doc_name)
    except Exception:
        tally["unresolvable"] += 1
        print(f"  {doc_name}#{ptr or '/'}: unresolvable")
        continue
    node = root
    for part in [p for p in ptr.strip("/").split("/") if p]:
        node = node[part] if not isinstance(node, list) else node[int(part)]
    items = node.get("items")
    if not isinstance(items, dict):
        print(f"  {doc_name}#{ptr or '/'}: items is {type(items).__name__}")
        continue
    one = seed(items)
    if not isinstance(one, dict):
        print(f"  {doc_name}#{ptr or '/'}: item is not an object")
        continue
    for k in keys:
        one.setdefault(k, seed((items.get("properties") or {}).get(k, {})))
    v = Draft7Validator(node, format_checker=FC)
    ctrl = sorted({e.validator for e in v.iter_errors([copy.deepcopy(one)])})
    pair = [copy.deepcopy(one), copy.deepcopy(one)]
    if node.get("uniqueItems"):
        other = next((k for k, val in one.items()
                      if isinstance(val, str) and k not in keys), None)
        if other is None:
            print(f"  {doc_name}#{ptr or '/'}: uniqueItems and nothing else to vary")
            continue
        pair[1][other] = str(pair[1][other]) + "x"
    dup = sorted({e.validator for e in v.iter_errors(pair)})
    shares = all(p.get(keys[0]) == pair[0].get(keys[0]) for p in pair)
    if ctrl:
        tally["control failed (witness not conforming)"] += 1
        verdict = f"CONTROL FAILED: a one-item list is refused by {ctrl}"
    elif not dup and shares:
        tally["accepts the duplicate"] += 1
        verdict = "ACCEPTS the duplicate -> enforcing would refuse a valid payload"
    else:
        tally["refused with the duplicate"] += 1
        verdict = f"refused by {dup}"
    print(f"  {doc_name}#{ptr or '/'}")
    print(f"      unique_item_properties={keys}  uniqueItems={node.get('uniqueItems')}")
    print(f"      {verdict}")

print("\n" + json.dumps(tally, indent=1))
