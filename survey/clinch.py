"""Is the first pass's 3,039 signatures a count of INSTANCE DATA shapes?"""
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
                yield from w_schema(vv, f"{ptr}/{k}/{kk.replace('~','~0').replace('/','~1')}")
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


VOCAB = set()
for d in docs:
    for _, n in w_schema(DOCS[d]):
        VOCAB |= set(n)

sig_schema, sig_blanket = Counter(), Counter()
blanket_only_nodes = 0
blanket_sig_no_vocab = Counter()
for d in docs:
    sch = {p for p, _ in w_schema(DOCS[d])}
    for p, n in w_blanket(DOCS[d]):
        keys = set(n)
        if not keys or keys == {"$ref"}:
            continue
        sig_blanket[frozenset(keys)] += 1
        if p not in sch:
            blanket_only_nodes += 1
            if not (keys & VOCAB):
                blanket_sig_no_vocab[frozenset(keys)] += 1
    for p, n in w_schema(DOCS[d]):
        keys = set(n)
        if not keys or keys == {"$ref"}:
            continue
        sig_schema[frozenset(keys)] += 1

print(f"blanket declaring nodes NOT at a schema position     {blanket_only_nodes}")
print(f"distinct signatures, blanket                         {len(sig_blanket)}")
print(f"distinct signatures, schema positions                {len(sig_schema)}")
print(f"signatures present ONLY under the blanket walk       {len(set(sig_blanket) - set(sig_schema))}")
print(f"  ...of those, containing NO schema keyword at all   {len(blanket_sig_no_vocab)}")
print("\nexamples of blanket-only signatures (these are instance data, not schemas):")
for s, c in Counter({s: sig_blanket[s] for s in set(sig_blanket) - set(sig_schema)}).most_common(12):
    print(f"  {c:5d}  {sorted(s)[:9]}")
