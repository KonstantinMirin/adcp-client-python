"""Reproduce the four figures of the first pass, independently of codegen.bundle.

INSTRUMENT: walk every node of the portable documents; count a node's OWN keys;
recurse only into schema positions.  Name->schema maps are walked by VALUE.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

BUNDLE = Path(sys.argv[1] if len(sys.argv) > 1 else "schemas/cache/3.2")
PROJECTIONS = ("bundled", "mcp")
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")

# name -> schema: walk the VALUES, never count the KEYS
MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas", "dependencies")
ONE = ("items", "additionalProperties", "contains", "not", "if", "then", "else",
       "propertyNames", "additionalItems", "unevaluatedProperties", "unevaluatedItems")
LIST = ("oneOf", "anyOf", "allOf", "prefixItems")


def portable() -> list[str]:
    out = [str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")
           if p.relative_to(BUNDLE).parts[0] not in PROJECTIONS
           and str(p.relative_to(BUNDLE)) not in REGISTRY]
    return sorted(out)


def nodes(node, pointer=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from nodes(v, f"{pointer}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield pointer, node
    for k, v in node.items():
        if k in MAP and isinstance(v, dict):
            for kk, vv in v.items():
                yield from nodes(vv, f"{pointer}/{k}/{kk.replace('~','~0').replace('/','~1')}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from nodes(v, f"{pointer}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from nodes(v, f"{pointer}/{k}")


def main() -> None:
    docs = portable()
    kw = Counter()
    sig = Counter()
    sig_site: dict[frozenset, tuple[str, str]] = {}
    kw_sites: dict[str, list[tuple[str, str]]] = {}
    declaring = 0
    pure_ref = 0
    total_nodes = 0
    for d in docs:
        doc = json.loads((BUNDLE / d).read_text())
        for ptr, n in nodes(doc):
            total_nodes += 1
            keys = set(n)
            if not keys:
                continue
            if keys == {"$ref"}:
                pure_ref += 1
                continue
            declaring += 1
            s = frozenset(keys)
            sig[s] += 1
            sig_site.setdefault(s, (d, ptr))
            for k in keys:
                kw[k] += 1
                kw_sites.setdefault(k, []).append((d, ptr))

    print(f"portable documents              {len(docs)}")
    print(f"schema-position nodes (all)     {total_nodes}")
    print(f"nodes declaring something       {declaring}")
    print(f"pure $ref nodes                 {pure_ref}")
    print(f"DISTINCT SCHEMA KEYWORDS        {len(kw)}")
    print(f"distinct keyword SIGNATURES     {len(sig)}")
    singles = sum(1 for v in sig.values() if v == 1)
    top25 = sum(c for _, c in sig.most_common(25))
    print(f"  singletons                    {singles}")
    print(f"  top 25 cover                  {top25}/{declaring} = {100*top25/declaring:.1f}%")
    out = {
        "documents": len(docs),
        "declaring": declaring,
        "pure_ref": pure_ref,
        "keywords": {k: v for k, v in sorted(kw.items(), key=lambda x: -x[1])},
        "signatures": [
            {"keys": sorted(s), "count": c, "site": list(sig_site[s])}
            for s, c in sorted(sig.items(), key=lambda x: (-x[1], sorted(x[0])))
        ],
        "keyword_sites": {k: [list(x) for x in v[:400]] for k, v in kw_sites.items()},
    }
    Path("survey/census.json").write_text(json.dumps(out, indent=1))
    print("\n--- all 88 keywords, count ---")
    for k, v in sorted(kw.items(), key=lambda x: -x[1]):
        print(f"{v:6d}  {k}")


main()
