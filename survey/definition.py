"""Which projection set? Reproduce the lead's figures, then test the set's own members.

The lead's definition:  annotation keys are not part of a signature and do not make a node
declaring; a node carrying $ref plus annotations alone is a PURE REFERENCE.
The lead's set: description, title, examples, $comment, deprecated, readOnly, writeOnly,
x-entity, $schema, $id.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")
from codegen import bundle

BUNDLE = Path("schemas/cache/3.2")
DOCS = {d: bundle.read(BUNDLE, d) for d in bundle.portable(BUNDLE)}

LEAD = {"description", "title", "examples", "$comment", "deprecated", "readOnly",
        "writeOnly", "x-entity", "$schema", "$id"}

# Every keyword MEASURED to refuse nothing (0 refusals over 184,418 validations), which is
# the population a "constrains nothing" rule actually selects.
DRAFT_ANN = {"$schema", "$id", "$comment", "title", "description", "examples", "example",
             "default", "deprecated", "readOnly", "writeOnly"}
PAYLOAD = {"version", "lastUpdated", "last_updated", "mappings", "vocabulary", "governance",
           "extensions", "_generated", "_generatedAt", "adcp_version", "architecture",
           "asset_types", "baseUrl", "prerelease", "protocol_layers", "published_version",
           "stability", "usage_notes", "versioning"}
OTHER_ANN = {"notes", "enumMetadata", "enumDescriptions", "errorMessage", "discriminator"}
XNAMES = {k for d in DOCS.values() for _, n in bundle.nodes(d) for k in n if k.startswith("x-")}
CONSTRAINS_NOTHING = DRAFT_ANN | PAYLOAD | OTHER_ANN | XNAMES

# A keyword is projected out only if its own decision is INDEPENDENT of every other keyword
# at the node -- which is composition rule C5 applied to the projection itself.  Four of the
# constrains-nothing set fail that test and are named in the report.
DECIDES_ANOTHER_KEYWORD = {"title"}
RENDERED_BUT_INDEPENDENT = {"description", "default", "enumDescriptions", "x-enum-descriptions"}
PRINCIPLED = CONSTRAINS_NOTHING - DECIDES_ANOTHER_KEYWORD


def census(project: set[str], label: str) -> dict:
    sig: Counter[frozenset] = Counter()
    declaring = pure = nothing = 0
    for doc in DOCS.values():
        for _, n in bundle.nodes(doc):
            keys = set(n) - project
            if not keys:
                nothing += 1
                continue
            if keys == {"$ref"}:
                pure += 1
                continue
            declaring += 1
            sig[frozenset(keys)] += 1
    kw = {k for s in sig for k in s}
    singles = sum(1 for v in sig.values() if v == 1)
    top25 = sum(c for _, c in sig.most_common(25))
    out = dict(declaring=declaring, pure=pure, nothing=nothing, keywords=len(kw),
               signatures=len(sig), singletons=singles,
               top25=round(100 * top25 / declaring, 1))
    print(f"{label:46s} declaring={declaring:6d} pure={pure:5d} "
          f"kw={len(kw):4d} sig={len(sig):5d} singles={singles:4d} top25={out['top25']}%")
    return out | {"sig": sig}


print("TARGET (the lead's re-run)                     declaring= 17079 pure= 4139 "
      "kw=  88 sig=  356 singles= 146 top25=83.5%")
mine = census(set(), "no projection (my first report)")
lead = census(LEAD, "the LEAD'S set, 10 names")
prin = census(PRINCIPLED, "PRINCIPLED set (measured, title kept)")
allcn = census(CONSTRAINS_NOTHING, "every constrains-nothing keyword")
# The ADOPTED set: constrains-nothing MINUS the two classes where projecting CHANGES the
# answer -- `title` (D2 reads an enum by whether a name reaches it) and the 19 registry
# payload keys (whose decision is a refusal, which projection would hide).
ADOPTED = CONSTRAINS_NOTHING - {"title"} - PAYLOAD
adopted = census(ADOPTED, "ADOPTED (title and payload keys kept)")
print(f"   adopted set size: {len(ADOPTED)} names")

print(f"\nset sizes: lead {len(LEAD)}, constrains-nothing {len(CONSTRAINS_NOTHING)}, "
      f"principled {len(PRINCIPLED)}")
print(f"in the lead's set but NOT measured to constrain nothing: "
      f"{sorted(LEAD - CONSTRAINS_NOTHING)}")
print(f"measured to constrain nothing but NOT in the lead's set, by sites: ")
kwc = Counter(k for d in DOCS.values() for _, n in bundle.nodes(d) for k in n)
for k in sorted(CONSTRAINS_NOTHING - LEAD, key=lambda k: -kwc[k])[:12]:
    print(f"    {kwc[k]:5d}  {k}")

# ---------------------------------------------------------------- the title counter-example
print("\n=== does `title` decide what a node becomes?  D2: a value set no name reaches is a "
      "Literal, a NAMED enum node is a StrEnum ===")
enum_titled = enum_untitled = 0
sites_untitled = []
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        if "enum" not in n:
            continue
        if "title" in n:
            enum_titled += 1
        else:
            enum_untitled += 1
            sites_untitled.append((d, ptr))
print(f"  enum nodes carrying a title   {enum_titled}")
print(f"  enum nodes carrying none      {enum_untitled}")
print(f"  example untitled: {sites_untitled[0][0]}#{sites_untitled[0][1]}")
merged = Counter()
for d, doc in DOCS.items():
    for ptr, n in bundle.nodes(doc):
        keys = set(n) - (PRINCIPLED | {"title"})
        if "enum" in keys:
            merged[(frozenset(keys), "title" in n)] += 1
pairs = {s for s, _ in merged}
both = [s for s in pairs if (s, True) in merged and (s, False) in merged]
print(f"\n  projections holding an `enum` that exist BOTH titled and untitled: {len(both)}")
tot = sum(merged[(s, t)] for s in both for t in (True, False))
print(f"  nodes in them: {tot}  -- projecting `title` merges two D2 outcomes into one "
      f"signature at every one")
for s in sorted(both, key=lambda s: -(merged[(s, True)] + merged[(s, False)]))[:6]:
    print(f"    {sorted(s)}  titled={merged[(s,True)]} untitled={merged[(s,False)]}")

json.dump({"mine": {k: v for k, v in mine.items() if k != "sig"},
           "lead": {k: v for k, v in lead.items() if k != "sig"},
           "principled": {k: v for k, v in prin.items() if k != "sig"},
           "all_constrains_nothing": {k: v for k, v in allcn.items() if k != "sig"}},
          open("survey/definition.json", "w"), indent=1)
