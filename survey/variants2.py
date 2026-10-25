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
DATA = {"examples", "default", "const", "enum", "enumDescriptions", "enumMetadata",
        "x-deprecated-enum-values", "x-deprecated-enum-values-doc"}

docs = sorted(str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")
              if p.relative_to(BUNDLE).parts[0] not in PROJECTIONS
              and str(p.relative_to(BUNDLE)) not in REGISTRY)
DOCS = {d: json.loads((BUNDLE / d).read_text()) for d in docs}


def w_blanket_nodata(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from w_blanket_nodata(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        if k in DATA:
            continue
        yield from w_blanket_nodata(v, f"{ptr}/{k}")


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


SCHEMA_VOCAB = set()
for d in docs:
    for _, n in w_schema(DOCS[d]):
        SCHEMA_VOCAB |= set(n)


def report(label, walk, vocab=None):
    kw, sig, declaring, pure, empty = Counter(), Counter(), 0, 0, 0
    for d in docs:
        for _, n in walk(DOCS[d]):
            if not isinstance(n, dict):
                continue
            keys = set(n) if vocab is None else (set(n) & vocab)
            if not keys:
                empty += 1
                continue
            if keys == {"$ref"}:
                pure += 1
                continue
            declaring += 1
            sig[frozenset(keys)] += 1
            for k in keys:
                kw[k] += 1
    singles = sum(1 for v in sig.values() if v == 1)
    top25 = sum(c for _, c in sig.most_common(25))
    print(f"{label:44s} declaring={declaring:6d} pure={pure:5d} kw={len(kw):4d} "
          f"sig={len(sig):5d} singles={singles:5d} top25={100*top25/max(declaring,1):.1f}%")


print(f"(schema vocab size {len(SCHEMA_VOCAB)})")
print("TARGET                                       declaring= 22659 pure= 4176 kw=  88 sig= 3039 singles= 2150 top25=64.4%")
report("blanket, no filter", w_blanket)
report("blanket, vocab-filtered", w_blanket, SCHEMA_VOCAB)
report("blanket-minus-data, no filter", w_blanket_nodata)
report("blanket-minus-data, vocab-filtered", w_blanket_nodata, SCHEMA_VOCAB)
report("schema, vocab-filtered", w_schema, SCHEMA_VOCAB)
