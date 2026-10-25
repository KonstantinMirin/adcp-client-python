"""Positional reductions for salesagent-j3k2l.55's table, same walk and population as
kw_census.py (schemas/cache/3.2, 1,054 portable documents, tree 07c84c14a).

Each figure here answers one row's positional question by running the emitter's OWN
reduction over every site, so the row states what the code reads today and not a guess.

Run: CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python kw_measure2.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from codegen import bundle, compiler  # noqa: E402
from codegen.lower import rules  # noqa: E402

BUNDLE = Path("schemas/cache/3.2")
docs = bundle.portable(BUNDLE)
raw = {d: json.loads((BUNDLE / d).read_text()) for d in docs}
sites: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
for d in docs:
    for ptr, n in bundle.nodes(raw[d]):
        for k in n:
            sites[k].append((d, ptr, n))
out: dict = {}


def live(n: dict) -> set[str]:
    return {k for k in n if k not in compiler.ANNOTATIONS and not k.startswith("x-")}


# ---- if: how many reduce to a Match clause list -----------------------------------
c = Counter()
for d, ptr, n in sites["if"]:
    c["readable by rules._clauses" if rules._clauses(n.get("if")) is not None else "not readable (schema half)"] += 1
print("if:", dict(c)); out["if"] = dict(c)
c = Counter()
for kw in ("then", "else"):
    for d, ptr, n in sites[kw]:
        b = rules._branch(n.get(kw))
        c[f"{kw}: " + ("reduces (require/forbid)" if b is not None and any(b) else "reduces to nothing")] += 1
        if isinstance(n.get(kw), dict) and "properties" in n[kw]:
            c[f"{kw}: carries properties (ignored, schema half)"] += 1
print("then/else:", dict(c)); out["then_else"] = dict(c)

# ---- not ------------------------------------------------------------------------------
c = Counter()
for d, ptr, n in sites["not"]:
    sub = n["not"]
    if rules._required_groups(sub):
        c["required groups -> ForbiddenGroups"] += 1
    elif isinstance(sub, dict) and (live(sub) <= {"const", "type"} or live(sub) <= {"enum", "type"}) and live(sub):
        c["a value (const/enum) -> schema half (rules.ON_A_VALUE)"] += 1
    elif sub == {}:
        c["not: {} (admits nothing)"] += 1
    else:
        c["other shape -> nothing written (schema half)"] += 1
print("not:", dict(c)); out["not"] = dict(c)

# ---- oneOf / anyOf: presence-only vs shapes, by position ------------------------------
for kw in ("oneOf", "anyOf"):
    c = Counter()
    for d, ptr, n in sites[kw]:
        po = rules.presence_only({kw: n[kw]})
        pos = "root" if ptr == "" else "nested"
        c[f"{pos}: " + ("presence-only -> RequiredGroups rule" if po else "shapes -> union")] += 1
    print(kw, dict(c)); out[kw] = dict(c)

# ---- $ref siblings -------------------------------------------------------------------
c = Counter()
examples = []
for d, ptr, n in sites["$ref"]:
    sib = live(n) - {"$ref"}
    ann = {k for k in n if k in compiler.ANNOTATIONS} - set()
    if sib:
        c["constraining sibling -> refused"] += 1
        examples.append((d, ptr, sorted(sib)))
    elif ann:
        c["annotation sibling only (description etc.) -> sibling wins (§6 rule 1)"] += 1
    else:
        c["bare $ref"] += 1
print("$ref:", dict(c), examples[:5]); out["$ref"] = {"tally": dict(c), "examples": examples[:10]}
c = Counter()
for d, ptr, n in sites["$ref"]:
    head, into = bundle.split_ref(n["$ref"])
    c["local (#/...)" if not head else ("fragment of another document" if into else "another document's root")] += 1
print("$ref targets:", dict(c)); out["$ref_targets"] = dict(c)

# ---- items / type / format -----------------------------------------------------------
c = Counter(type(n["items"]).__name__ for _, _, n in sites["items"])
print("items value kinds:", dict(c)); out["items_kinds"] = dict(c)
c = Counter()
for d, ptr, n in sites["type"]:
    t = n["type"]
    c["list" if isinstance(t, list) else t] += 1
print("type values:", dict(c)); out["type_values"] = dict(c)
typeless_props = [(d, p) for d in docs for p, n in bundle.nodes(raw[d]) if "properties" in n and "type" not in n]
print("nodes with properties and no type:", len(typeless_props)); out["typeless_with_properties"] = len(typeless_props)
c = Counter(n["format"] for _, _, n in sites["format"])
print("format values:", dict(c)); out["format_values"] = dict(c)
c = Counter()
for d, ptr, n in sites["format"]:
    if n["format"] == "uri":
        c["uri: pattern ^https:// exactly" if n.get("pattern") == "^https://" else
          ("uri: other pattern" if "pattern" in n else "uri: no pattern")] += 1
        if {"minLength", "maxLength"} & set(n):
            c["uri: states a length bound (refused)"] += 1
print("uri split:", dict(c)); out["uri_split"] = dict(c)

# ---- enum ----------------------------------------------------------------------------
c = Counter()
for d, ptr, n in sites["enum"]:
    vals = n["enum"]
    kinds = {type(v).__name__ for v in vals} if isinstance(vals, list) else {"?"}
    c[("typed " if "type" in n else "typeless ") + "/".join(sorted(kinds))] += 1
    if "enumDescriptions" in n:
        c["with enumDescriptions"] += 1
print("enum:", dict(c)); out["enum"] = dict(c)

# ---- const ---------------------------------------------------------------------------
c = Counter()
for d, ptr, n in sites["const"]:
    c[("typed " if "type" in n else "typeless ") + type(n["const"]).__name__] += 1
print("const:", dict(c)); out["const"] = dict(c)

# ---- default at definitions / rule positions; required-property defaults -------------
for d, ptr, n in sites["default"]:
    if "/definitions/" in ptr or "/$defs/" in ptr or any(h in ptr.split("/") for h in ("if", "then", "else", "not")):
        print("default at", d, ptr, "node type:", n.get("type"), "keys:", sorted(live(n)))
req_default = 0
for d in docs:
    for p, n in bundle.nodes(raw[d]):
        props = n.get("properties")
        req = n.get("required")
        if isinstance(props, dict) and isinstance(req, list):
            for k in req:
                if isinstance(props.get(k), dict) and "default" in props[k]:
                    req_default += 1
print("defaults on a REQUIRED property:", req_default); out["required_defaults"] = req_default

# ---- description on a non-object branch of a NESTED union (no carrier) ----------------
c = Counter()
for d, ptr, n in sites["description"]:
    parts = ptr.split("/")
    if len(parts) >= 3 and parts[-2] in ("oneOf", "anyOf") and parts[-1].isdigit():
        root_union = len(parts) == 3
        is_obj = n.get("type") == "object" or "properties" in n or "allOf" in n
        c[("root union" if root_union else "nested union") + (" object branch" if is_obj else " non-object branch")] += 1
print("description on union branches:", dict(c)); out["branch_descriptions"] = dict(c)

# ---- uniqueItems by whether a class holds the array -----------------------------------
c = Counter()
for d, ptr, n in sites["uniqueItems"]:
    parts = ptr.split("/")
    c["under properties/<key> (a class holds it -> D6 rule)" if len(parts) >= 3 and parts[-2] == "properties" else f"no class above ({parts[-1] if parts[-1] and not parts[-1].isdigit() else parts[-2] if len(parts)>1 else 'root'})"] += 1
print("uniqueItems:", dict(c)); out["uniqueItems"] = dict(c)

# ---- minItems / maxItems by position of the ARRAY node ---------------------------------
for kw in ("minItems", "maxItems"):
    c = Counter()
    for d, ptr, n in sites[kw]:
        parts = ptr.split("/")
        if ptr == "":
            c["root array"] += 1
        elif parts[-2] == "properties":
            c["property (field holds the list)"] += 1
        elif parts[-2] in ("oneOf", "anyOf"):
            c["union branch"] += 1
        elif parts[-1] == "items":
            c["array element (list of lists)"] += 1
        elif parts[-1] == "additionalProperties":
            c["mapping value"] += 1
        elif parts[-2] in ("definitions", "$defs"):
            c["definitions entry"] += 1
        elif any(h in parts for h in ("if", "then", "else", "not", "contains")):
            c["rule position"] += 1
        else:
            c[f"other: {ptr}"] += 1
    print(kw, dict(c)); out[kw] = dict(c)

# ---- contains by node type -------------------------------------------------------------
c = Counter()
for d, ptr, n in sites["contains"]:
    c[f"type={n.get('type')!r}, keys={sorted(live(n))}"] += 1
print("contains nodes:", dict(c.most_common(8))); out["contains"] = dict(c)

# ---- the x- predicate's reach: x- keys beside a constraining key, by site ---------------
c = Counter()
for d in docs:
    for p, n in bundle.nodes(raw[d]):
        xs = [k for k in n if k.startswith("x-")]
        if xs:
            c["x- beside constraining keys" if live(n) else "x- on an annotation-only node"] += 1
print("x- nodes:", dict(c)); out["x_nodes"] = dict(c)

Path("kw_measure2.json").write_text(json.dumps(out, indent=1, default=str))
print("wrote kw_measure2.json")
