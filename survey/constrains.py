"""Does each of the 23 keywords CONSTRAIN AN INSTANCE?  Ask the document through jsonschema.

TWO INSTRUMENTS, both differential and self-controlling.

A. VOCABULARY KEYWORDS (minItems, exclusiveMinimum, exclusiveMaximum).  At every site,
   derive the boundary witness from the keyword's OWN VALUE, validate it against the node
   as the DOCUMENT APPLIES IT (resolved + applied_schema), and against the same node with
   the keyword deleted.  CONSTRAINS iff refused with and accepted without -- which is what
   rules out some other keyword at the node having done the refusing.

B. NON-VOCABULARY KEYWORDS (the other 20).  At every site, take the keyword's own value as
   it appears there and validate a 13-instance corpus against the one-keyword schema
   {k: <that value>}.  Nothing refuses => the keyword cannot refuse anything at that site,
   for any instance, whatever its value is.
"""
from __future__ import annotations
import json, sys
sys.stdout.reconfigure(line_buffering=True)
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

sys.path.insert(0, ".")
from adcp.types._base import applied_schema
from codegen import bundle

BUNDLE = Path("schemas/cache/3.2")
VOCAB = set(Draft7Validator.VALIDATORS)
TARGET = ["minItems", "discriminator", "exclusiveMinimum", "exclusiveMaximum",
          "x-adcp-validation", "x-status", "x-mutates-state", "x-tool-summary", "x-added-in",
          "x-adcp-schema-uri", "x-canonicalization", "x-adcp-model-context-inline",
          "x-accessibility", "x-governed-commitment", "x-deprecated-in", "x-operation-family",
          "x-legacy-fallback", "x-adcp-hoist", "x-adcp-open-payload", "x-removed-in",
          "x-superseded-by", "version", "lastUpdated"]
CORPUS = [None, True, False, 0, -1, 1, 1e9, "", "x", [], [1, 2], {}, {"a": 1, "b": [None]}]

docs = bundle.portable(BUNDLE)
sites = defaultdict(list)
for d in docs:
    doc = bundle.read(BUNDLE, d)
    for ptr, n in bundle.nodes(doc):
        for k in TARGET:
            if k in n:
                sites[k].append((d, ptr))

# ---------- instrument B: the 20 non-vocabulary keywords ----------
print("=== INSTRUMENT B: a non-vocabulary keyword alone, over a 13-instance corpus ===")
b_rows = {}
for k in TARGET:
    if k in VOCAB:
        continue
    values, refused_any, n_sites = set(), 0, len(sites[k])
    for d, ptr in sites[k]:
        doc = bundle.read(BUNDLE, d)
        node = doc
        for part in [p for p in ptr.lstrip("/").split("/") if p]:
            node = node[int(part)] if isinstance(node, list) else node[part.replace("~1", "/").replace("~0", "~")]
        v = node[k]
        values.add(json.dumps(v, sort_keys=True, default=str)[:160])
        val = Draft7Validator({k: v}, format_checker=FormatChecker())
        refused_any += sum(1 for x in CORPUS if not val.is_valid(x))
    b_rows[k] = dict(sites=n_sites, distinct_values=len(values),
                     instances=n_sites * len(CORPUS), refused=refused_any)
    print(f"  {k:32s} sites={n_sites:5d} distinct values={len(values):4d} "
          f"instances={n_sites*len(CORPUS):6d} REFUSED={refused_any}")

# ---------- instrument A: the 3 vocabulary keywords ----------
print("\n=== INSTRUMENT A: boundary witness at every site, against the applied node ===")


def witness(k, node):
    v = node[k]
    if k == "minItems":
        return ([None] * (v - 1)) if isinstance(v, int) and v >= 1 else None
    if k in ("exclusiveMinimum", "exclusiveMaximum"):
        return v if isinstance(v, (int, float)) else None
    return None


a_rows = {}
for k in ("minItems", "exclusiveMinimum", "exclusiveMaximum"):
    tally = Counter()
    bad_sites = []
    cache: dict[str, dict] = {}
    for d, ptr in sites[k]:
        if d not in cache:
            cache[d] = bundle.read(BUNDLE, d)
        root = cache[d]
        if "__unresolved__" in root:
            tally["document unresolvable"] += 1
            continue
        try:
            node = applied_schema(root, ptr)
        except Exception:
            tally["pointer did not resolve after inlining"] += 1
            continue
        if k not in node:
            tally["keyword gone after inlining"] += 1
            continue
        w = witness(k, node)
        if w is None:
            tally["no derivable witness"] += 1
            continue
        minus = {kk: vv for kk, vv in node.items() if kk != k}
        try:
            with_kw = Draft7Validator(node, format_checker=FormatChecker()).is_valid(w)
            without = Draft7Validator(minus, format_checker=FormatChecker()).is_valid(w)
        except Exception:
            tally["validator raised (an unresolved $ref at the node)"] += 1
            continue
        if not with_kw and without:
            tally["CONSTRAINS (refused with, accepted without)"] += 1
        elif with_kw and without:
            tally["constrains nothing (accepted both ways)"] += 1
            bad_sites.append((d, ptr, "accepted both ways"))
        elif not with_kw and not without:
            tally["inconclusive (another keyword refused it too)"] += 1
            bad_sites.append((d, ptr, "refused both ways"))
        else:
            tally["IMPOSSIBLE (accepted with, refused without)"] += 1
            bad_sites.append((d, ptr, "accepted with, refused without"))
    a_rows[k] = dict(tally)
    print(f"\n  {k}  ({len(sites[k])} sites)")
    for kk, vv in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"      {vv:6d}  {kk}")
    for s in bad_sites[:6]:
        print(f"         e.g. {s[0]}#{s[1]}  [{s[2]}]")

Path("survey/constrains.json").write_text(json.dumps({"A": a_rows, "B": b_rows}, indent=1))
