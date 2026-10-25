"""Sites for the 23 keywords, with the carrying node, and draft-07's own vocabulary."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
from jsonschema import Draft7Validator

BUNDLE = Path("schemas/cache/3.2")
PROJECTIONS = ("bundled", "mcp")
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")
MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas", "dependencies")
ONE = ("items", "additionalProperties", "contains", "not", "if", "then", "else",
       "propertyNames", "additionalItems", "unevaluatedProperties", "unevaluatedItems")
LIST = ("oneOf", "anyOf", "allOf", "prefixItems")
TARGET = ["minItems", "discriminator", "exclusiveMinimum", "exclusiveMaximum",
          "x-adcp-validation", "x-status", "x-mutates-state", "x-tool-summary", "x-added-in",
          "x-adcp-schema-uri", "x-canonicalization", "x-adcp-model-context-inline",
          "x-accessibility", "x-governed-commitment", "x-deprecated-in", "x-operation-family",
          "x-legacy-fallback", "x-adcp-hoist", "x-adcp-open-payload", "x-removed-in",
          "x-superseded-by", "version", "lastUpdated"]

docs = sorted(str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")
              if p.relative_to(BUNDLE).parts[0] not in PROJECTIONS
              and str(p.relative_to(BUNDLE)) not in REGISTRY)


def nodes(node, ptr=""):
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from nodes(v, f"{ptr}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield ptr, node
    for k, v in node.items():
        if k in MAP and isinstance(v, dict):
            for kk, vv in v.items():
                yield from nodes(vv, f"{ptr}/{k}/{kk.replace('~','~0').replace('/','~1')}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from nodes(v, f"{ptr}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from nodes(v, f"{ptr}/{k}")


sites: dict[str, list] = {k: [] for k in TARGET}
for d in docs:
    doc = json.loads((BUNDLE / d).read_text())
    for ptr, n in nodes(doc):
        for k in TARGET:
            if k in n:
                sites[k].append((d, ptr, n))

print("=== draft-07 vocabulary, as jsonschema implements it ===")
vocab = set(Draft7Validator.VALIDATORS)
print(f"{len(vocab)} keywords jsonschema's Draft7Validator can refuse on:")
print("  " + " ".join(sorted(vocab)))
print()
print("=== which of the 23 are in it ===")
for k in TARGET:
    print(f"{'IN VOCAB ' if k in vocab else 'not in   '}  {len(sites[k]):5d} sites  {k}")

print("\n=== one representative node per keyword (truncated) ===")
for k in TARGET:
    d, ptr, n = sites[k][0]
    body = json.dumps({kk: vv for kk, vv in n.items()}, default=str)
    print(f"\n--- {k}  ({len(sites[k])} sites)  first: {d}#{ptr or '/'}")
    print("    " + (body[:600] + (" ...TRUNC" if len(body) > 600 else "")))

json.dump({k: [[d, p] for d, p, _ in v] for k, v in sites.items()},
          open("survey/sites.json", "w"), indent=1)
