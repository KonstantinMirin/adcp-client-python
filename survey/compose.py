"""PART TWO: the signature survey.

Population: every distinct SET of keywords declared at one schema position, over the
1,054 portable documents.  A decision per signature is not the shape of the answer; a
decision per keyword plus a rule for how keywords COMPOSE is.  This measures how far
the composition rules reach and names every signature they do not answer.
"""
from __future__ import annotations
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, ".")
from codegen import bundle

BUNDLE = Path("schemas/cache/3.2")

# ---------------------------------------------------------------- the role table
# Each role is a decision this plan already states, or (marked) one it does not.
#: Draft-07's own annotations plus the bundle's, each MEASURED to constrain no instance.
ANNOTATION = {           # contributes nothing to the accepted set (C1 projects it out)
    "$schema", "$id", "$comment", "title", "description", "examples", "example",
    "default", "deprecated", "readOnly", "writeOnly",
    "notes", "enumMetadata", "enumDescriptions", "errorMessage",
}
#: PART ONE's decisions: every ``x-*`` and ``discriminator``, measured to refuse nothing.
DECIDED_BY_PART_ONE = {
    "discriminator",
    "x-entity", "x-adcp-validation", "x-status", "x-mutates-state", "x-tool-summary",
    "x-added-in", "x-adcp-schema-uri", "x-canonicalization", "x-adcp-model-context-inline",
    "x-accessibility", "x-governed-commitment", "x-deprecated-in", "x-operation-family",
    "x-legacy-fallback", "x-adcp-hoist", "x-adcp-open-payload", "x-removed-in",
    "x-superseded-by", "x-idempotency-key-required", "x-extensible",
    "x-deprecated-enum-values", "x-deprecated-enum-values-doc", "x-pattern",
    "x-enum-descriptions", "x-task-result-schema-overrides", "x-entity-definitions",
    "x-canonical-policy-required-params-not-enforced", "x-adcp-file-size-units",
    "x-adcp-sdk-local", "x-compatibility-projection-only",
}
import os
if os.environ.get("APPLY_PART_ONE") == "1":
    ANNOTATION = ANNOTATION | DECIDED_BY_PART_ONE
if os.environ.get("KEEP_TITLE") == "1":
    ANNOTATION = ANNOTATION - {"title"}
PAYLOAD = {              # a registry document's own INSTANCE DATA at a schema root
    "version", "lastUpdated", "last_updated", "mappings", "vocabulary", "governance",
    "extensions", "_generated", "_generatedAt", "adcp_version", "architecture",
    "asset_types", "baseUrl", "prerelease", "protocol_layers", "published_version",
    "stability", "usage_notes", "versioning",
}
SECTION = {"$defs", "definitions"}                      # the walk, not a row (.20)
KIND = {                                                # D2: what the node BECOMES
    "properties": "object", "oneOf": "union", "anyOf": "union", "allOf": "composition",
    "enum": "valueset", "const": "valueset", "items": "array", "prefixItems": "array",
    "additionalItems": "array", "$ref": "reference", "type": "typeword",
    "patternProperties": "mapping", "additionalProperties": "mapping",
}
OBJECT_FACET = {"required", "additionalProperties", "propertyNames", "patternProperties"}
VALUE = {                                               # D5: binds to the TYPE
    "minimum": "number", "maximum": "number", "exclusiveMinimum": "number",
    "exclusiveMaximum": "number", "multipleOf": "number",
    "minLength": "string", "maxLength": "string", "pattern": "string", "format": "string",
    "minItems": "array", "maxItems": "array",
}
RULE = {"required", "if", "then", "else", "dependencies", "minProperties",
        "maxProperties", "uniqueItems", "not", "contains"}
#: `title` is NOT projected out: D3 names the node from it, and D2 reads an `enum` by
#: whether a name reaches it -- a titled enum is a StrEnum and an untitled one a Literal.
#: So it has a role of its own, and projecting it would MERGE two decided outcomes.
NAMING = {"title"}
ROLED = (ANNOTATION | PAYLOAD | SECTION | set(KIND) | OBJECT_FACET | set(VALUE)
         | RULE | NAMING)

# ------------------------------------------------------------------- the walk
sig_count: Counter[frozenset] = Counter()
sig_site: dict[frozenset, tuple[str, str]] = {}
for d in bundle.portable(BUNDLE):
    doc = bundle.read(BUNDLE, d)
    for ptr, n in bundle.nodes(doc):
        keys = set(n)
        if not keys or keys == {"$ref"}:
            continue
        s = frozenset(keys)
        sig_count[s] += 1
        sig_site.setdefault(s, (d, ptr))

print(f"declaring nodes                       {sum(sig_count.values())}")
print(f"distinct signatures                   {len(sig_count)}")

# ------------------------------------------- C1: project the annotations out
proj_count: Counter[frozenset] = Counter()
proj_site: dict[frozenset, list] = defaultdict(list)
for s, c in sig_count.items():
    p = frozenset(s - ANNOTATION)
    proj_count[p] += c
    proj_site[p].append((s, c, sig_site[s]))
print(f"\nC1  constraining projections          {len(proj_count)}   "
      f"({len(sig_count)} -> {len(proj_count)}, "
      f"{len(sig_count)-len(proj_count)} collapsed by annotations alone)")


def kinds_of(p: set[str]) -> set[str]:
    """The INDEPENDENT D2 kinds a projection names (facets fold into their owner)."""
    k = set()
    if "properties" in p:
        k.add("object")
    if {"oneOf", "anyOf"} & p:
        k.add("union")
    if "allOf" in p:
        k.add("composition")
    if {"enum", "const"} & p:
        k.add("valueset")
    if {"items", "prefixItems", "additionalItems"} & p:
        k.add("array")
    if ("patternProperties" in p) or ("additionalProperties" in p and "properties" not in p):
        k.add("mapping")
    if "$ref" in p:
        k.add("reference")
    if not k and "type" in p:
        k.add("typeword")
    if not k and not (p - RULE - set(VALUE) - SECTION - PAYLOAD):
        k.add("ruleonly" if p & RULE else "annotationonly")
    return k


def verdict(p: frozenset) -> tuple[str, str]:
    named = "title" in p
    p = frozenset(p - NAMING)
    unroled = p - ROLED
    if unroled:
        return "RESIDUE", f"keyword with no decided role: {sorted(unroled)}"
    ks = kinds_of(set(p))
    if len(ks) == 0:
        if not p:
            return "ANSWERED", "a title alone: D3 names the node, nothing else is declared"
        return "RESIDUE", "no kind: the projection names nothing D2 decides"
    if len(ks) > 1:
        # the stated exceptions: D7 composition, and D2's union-with-$ref branches
        if ks == {"composition", "reference"} or ks == {"composition", "object"} \
           or ks == {"composition", "union"} or ks == {"composition", "object", "union"} \
           or ks == {"composition", "object", "reference"}:
            return "ANSWERED", f"D7 composition over {sorted(ks - {'composition'})}"
        if ks == {"object", "mapping"} or ks == {"object", "reference"}:
            return "ANSWERED", f"one object kind with a facet: {sorted(ks)}"
        if ks == {"valueset", "typeword"}:
            return "ANSWERED", "D2 valueset, its own type restated"
        return "RESIDUE", f"two or more independent kinds: {sorted(ks)}"
    kind = next(iter(ks))
    if kind == "valueset":
        # D2 reads it by whether a NAME reaches it, and both readings are decided.
        return "ANSWERED", ("D2 valueset, named -> StrEnum" if named
                            else "D2 valueset, unnamed -> Literal")
    # C3: a value keyword must belong to the type family the kind produces
    fams = {VALUE[k] for k in p & set(VALUE)}
    if kind == "array" and fams - {"array"}:
        return "RESIDUE", f"array node carrying {sorted(fams - {'array'})} value keywords"
    if kind == "object" and fams:
        return "RESIDUE", f"object node carrying {sorted(fams)} value keywords"
    if kind in ("union", "composition", "reference", "valueset") and fams:
        return "ANSWERED", f"{kind}; value keywords {sorted(fams)} bind to the branch type (D5)"
    return "ANSWERED", f"one kind ({kind}) + value keywords {sorted(fams) or '-'} + rules " \
                       f"{sorted(p & RULE) or '-'}"


answered = {p: verdict(p) for p in proj_count}
a = {p: v for p, v in answered.items() if v[0] == "ANSWERED"}
r = {p: v for p, v in answered.items() if v[0] == "RESIDUE"}
nodes_a = sum(proj_count[p] for p in a)
nodes_r = sum(proj_count[p] for p in r)
print(f"\nANSWERED by composing per-keyword decisions   {len(a):4d} projections / "
      f"{nodes_a:6d} nodes")
print(f"RESIDUE                                      {len(r):4d} projections / "
      f"{nodes_r:6d} nodes")

# how many of the ORIGINAL signatures each covers
sig_a = sum(len(proj_site[p]) for p in a)
sig_r = sum(len(proj_site[p]) for p in r)
print(f"  of the {len(sig_count)} raw signatures: {sig_a} answered, {sig_r} residue")

print("\n================ THE RESIDUE, every member named with a site ================")
for p, (_, why) in sorted(r.items(), key=lambda x: (-proj_count[x[0]], sorted(x[0]))):
    raw = sorted(proj_site[p], key=lambda t: -t[1])[0]
    d, ptr = raw[2]
    print(f"\n[{proj_count[p]:5d} nodes] {sorted(p)}")
    print(f"          why: {why}")
    print(f"          site: {d}#{ptr or '/'}")

json.dump({
    "declaring_nodes": sum(sig_count.values()),
    "raw_signatures": len(sig_count),
    "projections": len(proj_count),
    "answered": [{"keys": sorted(p), "nodes": proj_count[p], "why": answered[p][1]} for p in a],
    "residue": [{"keys": sorted(p), "nodes": proj_count[p], "why": answered[p][1],
                 "site": list(sorted(proj_site[p], key=lambda t: -t[1])[0][2])} for p in r],
}, open(os.environ.get("OUT", "survey/compose.json"), "w"), indent=1)
