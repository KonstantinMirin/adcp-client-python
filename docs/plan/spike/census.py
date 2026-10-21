"""Root-shape census over the portable bundle documents: the population each
widening slice of the rebuild plan covers, and the leaf candidates for slice 1."""

from __future__ import annotations

import json
import sys
from collections import Counter

sys.path.insert(0, "/Users/konst/projects/acp-plan")
from codegen.adapter_adcp import _portable, bundle_documents, load_store, BASE_URI  # noqa: E402

COMPOSITION = ("allOf", "oneOf", "anyOf")
CONDITIONAL = ("if", "then", "else", "not")


def walk(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            out[k] += 1
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def root_shape(doc: dict) -> str:
    if "enum" in doc:
        return "enum root"
    if any(k in doc for k in ("oneOf", "anyOf")):
        return "union root (oneOf/anyOf)" + (" + properties/allOf beside it" if ("properties" in doc or "allOf" in doc) else "")
    if "allOf" in doc:
        return "allOf root"
    t = doc.get("type")
    if t == "array":
        return "array root"
    if t == "object" or "properties" in doc:
        if "properties" in doc:
            return "object root"
        if isinstance(doc.get("additionalProperties"), dict) or "patternProperties" in doc:
            return "mapping root"
        return "object root (no properties)"
    if isinstance(t, list):
        return "multi-type root"
    if t in ("string", "integer", "number", "boolean"):
        return "scalar root"
    if "$ref" in doc:
        return "bare $ref root"
    return f"other root ({t})"


def main():
    store, bad = load_store()
    assert not bad, bad
    docs = _portable(bundle_documents())
    docs = [d for d in docs if d not in ("index.json", "manifest.json", "manifest.schema.json")]
    shapes = Counter()
    refs = Counter()
    cond = Counter()
    leaf = []
    keyword_any = Counter()
    for d in docs:
        doc = store[BASE_URI + d]
        if not isinstance(doc, dict):
            shapes["non-object document"] += 1
            continue
        kw = Counter()
        walk(doc, kw)
        shape = root_shape(doc)
        shapes[shape] += 1
        has_ref = kw["$ref"] > 0
        has_cond = any(kw[k] for k in CONDITIONAL)
        has_comp = any(kw[k] for k in COMPOSITION)
        refs[has_ref] += 1
        cond[has_cond] += 1
        for k in ("$ref", "allOf", "oneOf", "anyOf", "if", "not", "additionalProperties", "patternProperties",
                  "uniqueItems", "const", "enum", "definitions", "$defs", "items", "format", "dependencies",
                  "dependentRequired"):
            if kw[k]:
                keyword_any[k] += 1
        if shape == "object root" and not has_ref and not has_cond and not has_comp and not kw["definitions"] and not kw["$defs"]:
            leaf.append((len(json.dumps(doc)), d))
    print(f"portable documents (minus index/manifest): {len(docs)}")
    print("\nroot shape:")
    for k, v in shapes.most_common():
        print(f"  {v:5d}  {k}")
    print(f"\ncarries a $ref anywhere: {refs[True]}   none: {refs[False]}")
    print(f"carries if/then/else/not anywhere: {cond[True]}   none: {cond[False]}")
    print("\ndocuments carrying keyword anywhere:")
    for k, v in sorted(keyword_any.items(), key=lambda kv: -kv[1]):
        print(f"  {v:5d}  {k}")
    print(f"\nleaf object documents (object root, no $ref, no composition, no conditional, no definitions): {len(leaf)}")
    for size, d in sorted(leaf)[:12]:
        print(f"  {size:6d} bytes  {d}")


if __name__ == "__main__":
    main()
