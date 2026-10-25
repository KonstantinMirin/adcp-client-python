from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

BUNDLE = Path("schemas/cache/3.2")
PROJECTIONS = ("bundled", "mcp")
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")
MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas", "dependencies")
ONE = ("items", "additionalProperties", "contains", "not", "if", "then", "else",
       "propertyNames", "additionalItems", "unevaluatedProperties", "unevaluatedItems")
LIST = ("oneOf", "anyOf", "allOf", "prefixItems")
docs = sorted(str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")
              if p.relative_to(BUNDLE).parts[0] not in PROJECTIONS
              and str(p.relative_to(BUNDLE)) not in REGISTRY)
DOCS = {d: json.loads((BUNDLE / d).read_text()) for d in docs}


def w_schema(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from w_schema(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        if k in MAP and isinstance(v, dict):
            for kk, vv in v.items():
                yield from w_schema(vv, f"{ptr}/{k}/{kk}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from w_schema(v, f"{ptr}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from w_schema(v, f"{ptr}/{k}")


def w_blanket(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from w_blanket(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        yield from w_blanket(v, f"{ptr}/{k}")


def enrich_type(n, keys):
    t = n.get("type")
    return frozenset(keys | {f"type={t!r}"}) if "type" in keys else frozenset(keys)


def report(label, walk, enrich=None, drop=()):
    sig, declaring, pure = Counter(), 0, 0
    for d in docs:
        for _, n in walk(DOCS[d]):
            if not isinstance(n, dict):
                continue
            keys = set(n) - set(drop)
            if not keys:
                continue
            if keys == {"$ref"}:
                pure += 1
                continue
            declaring += 1
            sig[enrich(n, keys) if enrich else frozenset(keys)] += 1
    singles = sum(1 for v in sig.values() if v == 1)
    top25 = sum(c for _, c in sig.most_common(25))
    print(f"{label:48s} declaring={declaring:6d} pure={pure:5d} sig={len(sig):5d} "
          f"singles={singles:5d} top25={100*top25/max(declaring,1):.1f}%")


print("TARGET                                           declaring= 22659 pure= 4176 sig= 3039 singles= 2150 top25=64.4%")
report("schema + type-value signature", w_schema, enrich_type)
report("blanket + type-value signature", w_blanket, enrich_type)
report("schema, drop $schema/title/desc", w_schema, None, ("$schema", "title", "description"))
report("blanket, drop $schema/title/desc", w_blanket, None, ("$schema", "title", "description"))
report("blanket, drop description", w_blanket, None, ("description",))
report("blanket+type-val, drop description", w_blanket, enrich_type, ("description",))
