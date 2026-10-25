"""What does each extension keyword CONTAIN?  The intent half of the measurement."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from codegen import bundle

BUNDLE = Path("schemas/cache/3.2")
TARGET = ["discriminator", "x-adcp-validation", "x-status", "x-mutates-state", "x-tool-summary",
          "x-added-in", "x-adcp-schema-uri", "x-canonicalization",
          "x-adcp-model-context-inline", "x-accessibility", "x-governed-commitment",
          "x-deprecated-in", "x-operation-family", "x-legacy-fallback", "x-adcp-hoist",
          "x-adcp-open-payload", "x-removed-in", "x-superseded-by", "version", "lastUpdated"]
vals = {k: Counter() for k in TARGET}
where = {k: Counter() for k in TARGET}
for d in bundle.portable(BUNDLE):
    doc = bundle.read(BUNDLE, d)
    for ptr, n in bundle.nodes(doc):
        for k in TARGET:
            if k in n:
                vals[k][json.dumps(n[k], sort_keys=True, default=str)] += 1
                where[k]["ROOT" if ptr == "" else "nested"] += 1
for k in TARGET:
    print(f"\n{'='*78}\n{k}   {sum(vals[k].values())} sites  "
          f"({where[k]['ROOT']} at a document root, {where[k]['nested']} nested)  "
          f"{len(vals[k])} distinct values")
    for v, c in vals[k].most_common(8):
        print(f"  {c:5d}  {v[:300]}")
    if len(vals[k]) > 8:
        print(f"  ... {len(vals[k]) - 8} more distinct values")
