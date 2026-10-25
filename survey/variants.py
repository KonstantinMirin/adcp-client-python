"""Which walk produces 22,659 / 4,176 / 88 / 3,039?  Sweep the plausible variants."""
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


def portable(include_registry=False, include_projections=False):
    out = [str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")
           if (include_projections or p.relative_to(BUNDLE).parts[0] not in PROJECTIONS)
           and (include_registry or str(p.relative_to(BUNDLE)) not in REGISTRY)]
    return sorted(out)


def walk_schema(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_schema(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        if k in MAP and isinstance(v, dict):
            for kk, vv in v.items():
                yield from walk_schema(vv, f"{ptr}/{k}/{kk}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from walk_schema(v, f"{ptr}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from walk_schema(v, f"{ptr}/{k}")


def walk_blanket(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_blanket(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        yield from walk_blanket(v, f"{ptr}/{k}")


def walk_map_keys(node, ptr=""):
    """The 'wrong' instrument: ALSO yield the map containers' key dicts as nodes."""
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_map_keys(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        if k in MAP and isinstance(v, dict):
            yield f"{ptr}/{k}", v        # the container itself counts as a node
            for kk, vv in v.items():
                yield from walk_map_keys(vv, f"{ptr}/{k}/{kk}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from walk_map_keys(v, f"{ptr}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from walk_map_keys(v, f"{ptr}/{k}")


def report(label, walk, docs):
    kw, sig, declaring, pure = Counter(), Counter(), 0, 0
    for d in docs:
        doc = json.loads((BUNDLE / d).read_text())
        for _, n in walk(doc):
            if not isinstance(n, dict):
                continue
            keys = set(n)
            if not keys:
                continue
            if keys == {"$ref"}:
                pure += 1
                continue
            declaring += 1
            sig[frozenset(keys)] += 1
            for k in keys:
                kw[k] += 1
    print(f"{label:46s} docs={len(docs):5d} declaring={declaring:6d} pure_ref={pure:5d} "
          f"kw={len(kw):4d} sig={len(sig):5d}")


docs = portable()
docs_reg = portable(include_registry=True)
docs_proj = portable(include_projections=True)
docs_all = portable(True, True)
report("schema walk / portable 1054", walk_schema, docs)
report("blanket walk / portable 1054", walk_blanket, docs)
report("map-container walk / portable 1054", walk_map_keys, docs)
report("schema walk / +registry", walk_schema, docs_reg)
report("blanket walk / +registry", walk_blanket, docs_reg)
report("schema walk / +projections", walk_schema, docs_proj)
report("blanket walk / +projections", walk_blanket, docs_proj)
report("schema walk / everything", walk_schema, docs_all)
