"""Keyword census with POSITION, for salesagent-j3k2l.55.

INSTRUMENT (the same walk as salesagent-j3k2l.53's survey/census.py, so the aggregates
are comparable): walk every node of the 1,054 portable documents in schemas/cache/3.2,
excluding bundled/, mcp/ and the three registry files; count a node's OWN keys; recurse
only into schema positions.  Name->schema maps (properties, $defs, definitions,
patternProperties, dependentSchemas, dependencies) are walked by VALUE and their keys are
never counted.

What this adds over .53: every site is classified by the POSITION of the node that
carries the keyword -- root, property, array element (items), mapping value
(additionalProperties / patternProperties), propertyNames, union branch (oneOf/anyOf
member), allOf conjunct, rule position (under not/if/then/else or contains), or a
definitions-section member.  A position is read off the LAST schema hop of the pointer,
except that anything beneath a rule hop is a rule position (section 6's census rule:
under not/if/then/else a keyword is a rule and no type is lowered from it).

Run: CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python kw_census.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft7Validator

BUNDLE = Path(sys.argv[1] if len(sys.argv) > 1 else "schemas/cache/3.2")
PROJECTIONS = ("bundled", "mcp")
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")

MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas", "dependencies")
ONE = ("items", "additionalProperties", "contains", "not", "if", "then", "else",
       "propertyNames", "additionalItems", "unevaluatedProperties", "unevaluatedItems")
LIST = ("oneOf", "anyOf", "allOf", "prefixItems")
RULE_HOPS = ("not", "if", "then", "else", "contains")

DRAFT07 = frozenset(Draft7Validator.META_SCHEMA["properties"])
VOCAB = frozenset(Draft7Validator.VALIDATORS)  # the keywords jsonschema can refuse on


def portable() -> list[str]:
    return sorted(
        str(p.relative_to(BUNDLE))
        for p in BUNDLE.rglob("*.json")
        if p.relative_to(BUNDLE).parts[0] not in PROJECTIONS
        and str(p.relative_to(BUNDLE)) not in REGISTRY
    )


def nodes(node, pointer=""):
    """Yield (pointer, node) for every schema-position node, lists expanded by index."""
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
                esc = kk.replace("~", "~0").replace("/", "~1")
                yield from nodes(vv, f"{pointer}/{k}/{esc}")
        elif k in ONE and isinstance(v, (dict, list)):
            yield from nodes(v, f"{pointer}/{k}")
        elif k in LIST and isinstance(v, list):
            yield from nodes(v, f"{pointer}/{k}")


def position(pointer: str) -> str:
    """The position of the node a pointer names, by its last schema hop.

    Anything beneath a rule hop is a rule position.  `dependencies` values are
    schemas (schema-form) or name lists; only the schema form is walked, and it is
    a rule position too (D6 lists `dependencies` as a rule family).
    """
    if not pointer:
        return "root"
    parts = pointer.split("/")[1:]
    if any(p in RULE_HOPS for p in parts):
        return "rule"
    if any(p == "dependencies" for p in parts):
        return "rule"
    # last schema hop: walk backwards past list indices and map names
    i = len(parts) - 1
    while i >= 0:
        p = parts[i]
        if p.isdigit():
            i -= 1
            continue
        if p in MAP:
            # the hop BEFORE was the map keyword and this is a name under it; the
            # node is the map's value
            return {"properties": "property", "$defs": "definitions", "definitions": "definitions",
                    "patternProperties": "mapping value", "dependentSchemas": "rule",
                    "dependencies": "rule"}[p]
        if i >= 1 and parts[i - 1] in MAP:
            return {"properties": "property", "$defs": "definitions", "definitions": "definitions",
                    "patternProperties": "mapping value", "dependentSchemas": "rule",
                    "dependencies": "rule"}[parts[i - 1]]
        if p in ("oneOf", "anyOf"):
            return "union branch"
        if p == "allOf":
            return "allOf conjunct"
        if p == "items" or p == "additionalItems" or p == "prefixItems":
            return "array element"
        if p == "additionalProperties":
            return "mapping value"
        if p == "propertyNames":
            return "propertyNames"
        i -= 1
    return "root"


def main() -> None:
    docs = portable()
    kw = Counter()
    kw_docs: dict[str, set[str]] = defaultdict(set)
    kw_pos = defaultdict(Counter)
    kw_first: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    sig = Counter()
    declaring = pure_ref = total = 0
    for d in docs:
        doc = json.loads((BUNDLE / d).read_text())
        for ptr, n in nodes(doc):
            total += 1
            keys = set(n)
            if not keys:
                continue
            if keys == {"$ref"}:
                pure_ref += 1
                continue
            declaring += 1
            sig[frozenset(keys)] += 1
            pos = position(ptr)
            for k in keys:
                kw[k] += 1
                kw_docs[k].add(d)
                kw_pos[k][pos] += 1
                kw_first[k].setdefault(pos, (d, ptr or "#"))

    vocab = sorted(k for k in kw if k in DRAFT07)
    other = sorted(k for k in kw if k not in DRAFT07)
    print(f"portable documents                 {len(docs)}")
    print(f"schema-position nodes (all)        {total}")
    print(f"nodes declaring something          {declaring}")
    print(f"pure $ref nodes                    {pure_ref}")
    print(f"distinct keywords                  {len(kw)}")
    print(f"  in draft-07's meta-schema        {len(vocab)}")
    print(f"  not draft-07                     {len(other)}")
    print(f"distinct signatures                {len(sig)}  singletons {sum(1 for v in sig.values() if v == 1)}")
    print(f"draft-07 meta-schema properties    {len(DRAFT07)}; jsonschema Draft7 validators {len(VOCAB)}")
    print()
    print("keyword                         sites   docs  vocab  positions")
    for k, c in sorted(kw.items(), key=lambda x: (-x[1], x[0])):
        v = "d07" if k in DRAFT07 else "   "
        poss = ", ".join(f"{p}={n}" for p, n in kw_pos[k].most_common())
        print(f"{k:30s} {c:6d} {len(kw_docs[k]):6d}  {v}    {poss}")
    out = {
        "documents": len(docs), "total_nodes": total, "declaring": declaring, "pure_ref": pure_ref,
        "keywords": {k: {"sites": c, "documents": len(kw_docs[k]), "draft07": k in DRAFT07,
                         "positions": dict(kw_pos[k]), "first": kw_first[k]}
                     for k, c in sorted(kw.items(), key=lambda x: (-x[1], x[0]))},
        "signatures": len(sig), "singletons": sum(1 for v in sig.values() if v == 1),
    }
    Path("kw_census.json").write_text(json.dumps(out, indent=1, sort_keys=True))


main()
