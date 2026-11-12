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
for d, p, k in missing:
    print(f"      propertyName={k!r:12s} {d}{p}")
