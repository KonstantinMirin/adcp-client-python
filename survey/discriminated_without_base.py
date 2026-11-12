import importlib
import json
import pkgutil
import sys

import pydantic

sys.path.insert(0, "tests_emit")
import fresh
from codegen import bundle

# every node stating a discriminator beside a oneOf/anyOf
sites = []


def walk(n, doc, ptr):
    if isinstance(n, list):
        for i, x in enumerate(n):
            walk(x, doc, f"{ptr}/{i}")
        return
    if not isinstance(n, dict):
        return
    if isinstance(n.get("discriminator"), dict) and (n.get("oneOf") or n.get("anyOf")):
        sites.append((doc, ptr, n["discriminator"].get("propertyName")))
    for k, v in n.items():
        if k in ("properties", "patternProperties", "$defs", "definitions") and isinstance(v, dict):
            for pk, pv in v.items():
                walk(pv, doc, f"{ptr}/{k}/{pk}")
        elif k in ("items", "additionalProperties", "contains", "not", "if", "then", "else"):
            walk(v, doc, f"{ptr}/{k}")
        elif k in ("anyOf", "oneOf", "allOf", "prefixItems") and isinstance(v, list):
            for i, x in enumerate(v):
                walk(x, doc, f"{ptr}/{k}/{i}")


for d in sorted(bundle.portable(fresh.BUNDLE)):
    walk(json.loads((fresh.BUNDLE / d).read_text()), d, "#")

# which pointers have a class of ours
stamped = {}
import adcp.types._schemas as S

for mi in pkgutil.walk_packages(S.__path__, S.__name__ + "."):
    try:
        m = importlib.import_module(mi.name)
    except Exception:
        continue
    for n, o in vars(m).items():
        if (
            isinstance(o, type)
            and issubclass(o, pydantic.BaseModel)
            and getattr(o, "__adcp_schema__", None) is not None
        ):
            r = o.__adcp_schema__
            stamped.setdefault((r.document, r.pointer), []).append(n)

missing = [(d, p, k) for d, p, k in sites if (d, p) not in stamped]
print(f"nodes stating a discriminator beside a oneOf/anyOf : {len(sites)}")
print(f"  with a class of ours AT THE NODE                 : {len(sites) - len(missing)}")
print(f"  with NO class at the node                        : {len(missing)}")

# WHICH CASE EACH SITE IS, read off the branches rather than assumed.  Case A is the one
# the compiler already implements: every branch PINS the named property to a const, and
# the consts are distinct, so the dispatch is a mapping the document wrote down.  Where
# the key is named and the branches do not pin it, no const exists to key on and the base
# needs a callable discriminator instead -- which is a different emission, so the split
# decides whether this is one fix or two.
nodes = {}


def collect(n, doc, ptr):
    if isinstance(n, list):
        for i, x in enumerate(n):
            collect(x, doc, f"{ptr}/{i}")
        return
    if not isinstance(n, dict):
        return
    nodes[(doc, ptr)] = n
    for k, v in n.items():
        if k in ("properties", "patternProperties", "$defs", "definitions") and isinstance(v, dict):
            for pk, pv in v.items():
                collect(pv, doc, f"{ptr}/{k}/{pk}")
        elif k in ("items", "additionalProperties", "contains", "not", "if", "then", "else"):
            collect(v, doc, f"{ptr}/{k}")
        elif k in ("anyOf", "oneOf", "allOf", "prefixItems") and isinstance(v, list):
            for i, x in enumerate(v):
                collect(x, doc, f"{ptr}/{k}/{i}")


known = sorted(bundle.portable(fresh.BUNDLE))
for d in known:
    collect(json.loads((fresh.BUNDLE / d).read_text()), d, "#")


def _target(ref, doc):
    """The node a ``$ref`` names, LOCAL or CROSS-DOCUMENT.

    Following the cross-document one is not a nicety: at
    ``core/assets/card-asset.json#/properties/media`` and
    ``core/offering-asset-group.json#/properties/items/items`` every branch is a ``$ref``
    to another document and the const that discriminates them is stated THERE.  Read with
    local refs only, those two sites report "no branch pins the key" -- which is a fact
    about the reader and not about the documents, and it is the difference between
    reporting one fix and reporting two.
    """
    if ref.startswith("#"):
        return nodes.get((doc, "#" + ref.split("#")[-1]))
    path, _, fragment = ref.partition("#")
    #: The bundle-relative path, which is what follows the version segment of the
    #: published URI.  Matched against the documents the bundle actually holds rather than
    #: parsed, so a URI this reader does not understand resolves to nothing instead of to
    #: a guess.
    for candidate in known:
        if path.endswith("/" + candidate):
            return nodes.get((candidate, "#" + fragment if fragment else "#"))
    return None


def pinned(branch, key, doc):
    """The const ``branch`` pins ``key`` to, or None."""
    seen = 0
    while isinstance(branch, dict) and isinstance(branch.get("$ref"), str) and seen < 8:
        where = doc if branch["$ref"].startswith("#") else None
        target = _target(branch["$ref"], doc)
        if target is None:
            return None
        if where is None:
            for candidate in known:
                if branch["$ref"].partition("#")[0].endswith("/" + candidate):
                    doc = candidate
                    break
        branch, seen = target, seen + 1
    if not isinstance(branch, dict):
        return None
    for holder in [branch, *(c for c in branch.get("allOf", []) if isinstance(c, dict))]:
        about = holder.get("properties")
        if isinstance(about, dict) and isinstance(about.get(key), dict):
            own = about[key]
            if "const" in own:
                return own["const"]
            members = own.get("enum")
            if isinstance(members, list) and len(members) == 1:
                return members[0]
    return None


def case_of(doc, ptr, key):
    node = nodes.get((doc, ptr)) or {}
    branches = node.get("oneOf") or node.get("anyOf") or []
    if not key:
        return "C: no propertyName", []
    pins = [pinned(b, key, doc) for b in branches]
    if all(p is not None for p in pins) and len(set(map(repr, pins))) == len(pins):
        return "A: every branch pins the key to a distinct const", pins
    if any(p is not None for p in pins):
        return "B: the key is named, some branches pin it", pins
    return "C: the key is named, no branch pins it", pins


import collections

split = collections.Counter()
rows = []
for d, p, k in missing:
    verdict, pins = case_of(d, p, k)
    split[verdict.split(":")[0]] += 1
    rows.append((verdict, k, d, p, pins))
print("\n--- WHICH CASE EACH OF THE MISSING SITES IS")
for kind, n in sorted(split.items()):
    print(f"  case {kind}: {n}")
for verdict, k, d, p, pins in sorted(rows):
    print(f"   [{verdict[0]}] propertyName={k!r:20s} pins={pins}")
    print(f"       {d}{p}")

# and the SAME reading over the 56 that DO have a base, so the comparison is like for like
have = collections.Counter()
for d, p, k in sites:
    if (d, p) in stamped:
        have[case_of(d, p, k)[0].split(":")[0]] += 1
print("\n--- the same reading over the 56 that ALREADY have a class")
for kind, n in sorted(have.items()):
    print(f"  case {kind}: {n}")
