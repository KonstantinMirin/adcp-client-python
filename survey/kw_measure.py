"""Per-keyword measurements for salesagent-j3k2l.55, over the census kw_census.py took.

Every figure here states its run (this tree, 07c84c14a; schemas/cache/3.2, 1,054 portable
documents), its sense and its instrument.  Instruments:

A. BOUNDARY WITNESS, for the three vocabulary keywords the plan never decided
   (minItems, exclusiveMinimum, exclusiveMaximum): at every site derive the witness from
   the keyword's own value, validate it against the node as the DOCUMENT applies it
   (bundle.resolved + applied_schema) and against the same node with the keyword deleted.
   CONSTRAINS iff refused with and accepted without.  salesagent-j3k2l.53's instrument A.

B. ONE-KEYWORD SCHEMA, for every keyword jsonschema's Draft7Validator has no validator for
   and that does not act through a sibling (then/else act through if; definitions/$defs
   through $ref): at every site the keyword's own value becomes {k: value} and judges a
   13-instance corpus.  0 refusals => the keyword cannot refuse any instance at any site.
   salesagent-j3k2l.53's instrument B, extended from its 23 keywords to all of them.

C. DISCRIMINATOR: at each of the 81 sites, do the branches of the node's own union
   const/enum-tag discriminator.propertyName inline (D3 rung 2 reads the branch's own
   const), are they all $ref (rung 1, the title), or mixed?  And at how many sites does a
   branch pin MORE than one const, which is the only case lower/union._const_pin consults
   the keyword?

D. WHO NAMES WHAT: which of the 41 draft-07 keywords codegen/ names as a literal, and
   which docs/plan/rebuild-plan.md names at all.

E. THE EMITTED SET: codegen.emit.emit over the portable bundle; which emitted documents
   carry `deprecated`, so the deprecated diagnosis has its population.

Run: CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python kw_measure.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from adcp.types._base import applied_schema  # noqa: E402
from codegen import bundle  # noqa: E402

BUNDLE = Path("schemas/cache/3.2")
VALIDATORS = frozenset(Draft7Validator.VALIDATORS)
DRAFT07 = frozenset(Draft7Validator.META_SCHEMA["properties"]) | {"writeOnly"}  # §10.3 of the
# draft-07 validation spec defines writeOnly beside readOnly; jsonschema's bundled copy of the
# meta-schema lists 45 properties and omits it.
THROUGH_A_SIBLING = frozenset({"then", "else", "definitions", "$defs"})
CORPUS = [None, True, False, 0, -1, 1, 1e9, "", "x", [], [1, 2], {}, {"a": 1, "b": [None]}]

census = json.loads(Path("kw_census.json").read_text())
keywords = census["keywords"]
docs = bundle.portable(BUNDLE)
raw: dict[str, dict] = {d: json.loads((BUNDLE / d).read_text()) for d in docs}

# ---- every site of every keyword, with the raw node ---------------------------------
sites: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
for d in docs:
    for ptr, n in bundle.nodes(raw[d]):
        for k in n:
            sites[k].append((d, ptr, n))

out: dict = {"tree": "07c84c14a", "bundle": str(BUNDLE), "documents": len(docs)}

# ---- instrument B --------------------------------------------------------------------
print("=== B: one-keyword schema over a 13-instance corpus ===")
b_targets = sorted(k for k in keywords if k not in VALIDATORS and k not in THROUGH_A_SIBLING)
b_rows = {}
total_validations = total_refused = 0
for k in b_targets:
    values = set()
    refused = 0
    for d, ptr, n in sites[k]:
        v = n[k]
        values.add(json.dumps(v, sort_keys=True, default=str)[:200])
        val = Draft7Validator({k: v}, format_checker=FormatChecker())
        refused += sum(1 for x in CORPUS if not val.is_valid(x))
    n_sites = len(sites[k])
    b_rows[k] = {"sites": n_sites, "distinct_values": len(values),
                 "validations": n_sites * len(CORPUS), "refused": refused}
    total_validations += n_sites * len(CORPUS)
    total_refused += refused
print(f"  {len(b_targets)} keywords, {total_validations} validations, {total_refused} refused")
for k in b_targets:
    r = b_rows[k]
    print(f"  {k:48s} sites={r['sites']:5d} values={r['distinct_values']:4d} refused={r['refused']}")
out["B"] = {"keywords": len(b_targets), "validations": total_validations, "refused": total_refused,
            "rows": b_rows}

# ---- instrument A --------------------------------------------------------------------
print("\n=== A: boundary witness against the applied node ===")


def witness(k: str, node: dict):
    v = node[k]
    if k == "minItems":
        return ([None] * (v - 1)) if isinstance(v, int) and v >= 1 else None
    if k == "maxItems":
        return [None] * (v + 1) if isinstance(v, int) else None
    if k in ("exclusiveMinimum", "exclusiveMaximum"):
        return v if isinstance(v, (int, float)) else None
    return None


a_rows = {}
resolved_cache: dict[str, dict] = {}
for k in ("minItems", "exclusiveMinimum", "exclusiveMaximum"):
    tally: Counter = Counter()
    artifacts: list = []
    for d, ptr, _ in sites[k]:
        if d not in resolved_cache:
            resolved_cache[d] = bundle.read(BUNDLE, d)
        root = resolved_cache[d]
        if "__unresolved__" in root:
            tally["document unresolvable"] += 1
            artifacts.append((d, ptr, "unresolvable"))
            continue
        try:
            node = applied_schema(root, ptr)
        except Exception:
            tally["pointer did not resolve after inlining"] += 1
            artifacts.append((d, ptr, "pointer"))
            continue
        if k not in node:
            tally["keyword gone after inlining"] += 1
            artifacts.append((d, ptr, "gone"))
            continue
        w = witness(k, node)
        if w is None:
            tally["no derivable witness"] += 1
            artifacts.append((d, ptr, f"no witness for {node[k]!r}"))
            continue
        minus = {kk: vv for kk, vv in node.items() if kk != k}
        try:
            with_kw = Draft7Validator(node, format_checker=FormatChecker()).is_valid(w)
            without = Draft7Validator(minus, format_checker=FormatChecker()).is_valid(w)
        except Exception:
            tally["validator raised (unresolved $ref at the node)"] += 1
            artifacts.append((d, ptr, "validator raised"))
            continue
        if not with_kw and without:
            tally["CONSTRAINS"] += 1
        elif with_kw and without:
            tally["accepted both ways"] += 1
            artifacts.append((d, ptr, "accepted both ways"))
        elif not with_kw and not without:
            cause = "sibling contains" if "contains" in minus else (
                "element type refuses the filler" if "items" in minus else "another keyword refused it")
            tally[f"refused both ways ({cause})"] += 1
            artifacts.append((d, ptr, cause))
        else:
            tally["IMPOSSIBLE"] += 1
    a_rows[k] = {"sites": len(sites[k]), "tally": dict(tally), "artifacts": artifacts}
    print(f"  {k} ({len(sites[k])} sites): " + "; ".join(f"{c} {n}" for n, c in tally.most_common()))
out["A"] = a_rows

# ---- money shapes: exclusiveMinimum against minimum on amount-like fields -----------
print("\n=== exclusiveMinimum sites by document ===")
by_doc: dict[str, list] = defaultdict(list)
for d, ptr, n in sites["exclusiveMinimum"]:
    by_doc[d].append((ptr, n.get("type"), n["exclusiveMinimum"]))
for d in sorted(by_doc):
    print(f"  {d}: " + ", ".join(f"{p} ({t} > {v})" for p, t, v in by_doc[d]))
out["exclusiveMinimum_sites"] = {d: v for d, v in by_doc.items()}
money_titles = {}
for d in docs:
    t = str(raw[d].get("title", ""))
    if re.search(r"money|amount|budget|price|cost|spend", t, re.I) and isinstance(raw[d].get("properties"), dict):
        bounds = {}
        for key, sub in raw[d]["properties"].items():
            if isinstance(sub, dict) and ({"minimum", "exclusiveMinimum"} & set(sub)):
                bounds[key] = {kk: sub[kk] for kk in ("minimum", "exclusiveMinimum") if kk in sub}
        if bounds:
            money_titles[d] = {"title": t, "bounds": bounds}
print("\n=== titled money-like roots stating a lower bound on a property ===")
for d, v in sorted(money_titles.items()):
    print(f"  {d} [{v['title']}]: {v['bounds']}")
out["money_like"] = money_titles

# ---- instrument C: discriminator -----------------------------------------------------
print("\n=== C: discriminator ===")
c_tally: Counter = Counter()
c_multi_pin = 0
c_sites = []
for d, ptr, n in sites["discriminator"]:
    prop = (n.get("discriminator") or {}).get("propertyName")
    branches = n.get("oneOf") or n.get("anyOf") or []
    inline_tagged = all_ref = 0
    multi = False
    for b in branches:
        if not isinstance(b, dict):
            continue
        live = {k for k in b if not k.startswith("x-") and k not in ("title", "description", "$comment")}
        if live == {"$ref"}:
            all_ref += 1
            continue
        props = b.get("properties") or {}
        decl = props.get(prop) if isinstance(props, dict) else None
        if isinstance(decl, dict) and ("const" in decl or "enum" in decl):
            inline_tagged += 1
        pinned = [k for k, v in props.items() if isinstance(v, dict) and "const" in v] if isinstance(props, dict) else []
        if len(pinned) > 1:
            multi = True
    nb = len([b for b in branches if isinstance(b, dict)])
    if nb and inline_tagged == nb:
        kind = "every branch tags it inline"
    elif nb and all_ref == nb:
        kind = "every branch is a bare $ref"
    elif nb == 0:
        kind = "no union at the node"
    else:
        kind = "mixed"
    c_tally[kind] += 1
    if multi:
        c_multi_pin += 1
    c_sites.append((d, ptr, prop, kind, multi))
for kind, c in c_tally.most_common():
    print(f"  {c:3d}  {kind}")
print(f"  sites where a branch pins MORE than one const (the only case _const_pin reads the keyword): {c_multi_pin}")
for d, ptr, prop, kind, multi in c_sites:
    if kind in ("mixed", "no union at the node") or multi:
        print(f"     {d}#{ptr or '/'} [{prop}] {kind}{' MULTI-PIN' if multi else ''}")
out["C"] = {"tally": dict(c_tally), "multi_pin": c_multi_pin, "sites": c_sites}

# ---- dependencies: list form vs schema form ------------------------------------------
dep = Counter()
for d, ptr, n in sites["dependencies"]:
    for trig, req in n["dependencies"].items():
        dep["list" if isinstance(req, list) else "schema"] += 1
print(f"\n=== dependencies entries: {dict(dep)} ===")
out["dependencies_forms"] = dict(dep)

# ---- additionalProperties on an allOf conjunct ---------------------------------------
print("\n=== additionalProperties on an allOf conjunct ===")
ap_conj = []
for d, ptr, n in sites["additionalProperties"]:
    parts = ptr.split("/")
    if len(parts) >= 3 and parts[-2] == "allOf" and parts[-1].isdigit():
        ap_conj.append((d, ptr, sorted(k for k in n if not k.startswith("x-"))))
for d, ptr, keys in ap_conj:
    print(f"  {d}#{ptr} {keys}")
out["ap_on_conjunct"] = ap_conj

# ---- x-canonicalization siblings; x-adcp-validation values ---------------------------
xc = Counter()
for d, ptr, n in sites["x-canonicalization"]:
    xc[(n["x-canonicalization"], n.get("uniqueItems"), "minItems" in n)] += 1
print(f"\n=== x-canonicalization (value, uniqueItems, has minItems): {dict(xc)} ===")
xv = {json.dumps(n["x-adcp-validation"], sort_keys=True) for _, _, n in sites["x-adcp-validation"]}
print(f"=== x-adcp-validation: {len(sites['x-adcp-validation'])} sites, {len(xv)} distinct values ===")
out["x_canonicalization"] = [[list(k), v] for k, v in xc.items()]
out["x_adcp_validation_distinct"] = len(xv)

# ---- x-enum-descriptions / readOnly / writeOnly / $comment sites --------------------
for k in ("x-enum-descriptions", "readOnly", "writeOnly", "enumMetadata", "notes", "errorMessage", "$defs"):
    print(f"\n=== {k} sites ===")
    for d, ptr, n in sites[k]:
        print(f"  {d}#{ptr or '/'}  value={json.dumps(n[k], default=str)[:120]}")

# ---- instrument D: who names what ----------------------------------------------------
print("\n=== D: which draft-07 keywords codegen/ names, and which the plan names ===")
code = "\n".join(p.read_text() for p in [*Path("codegen").glob("*.py"), *Path("codegen/lower").glob("*.py")])
plan = Path("docs/plan/rebuild-plan.md").read_text()
d07_in_bundle = sorted(k for k in keywords if k in DRAFT07)
code_names = [k for k in d07_in_bundle if f'"{k}"' in code]
plan_names = [k for k in d07_in_bundle if f"`{k}`" in plan or re.search(rf"(?<![\w$`]){re.escape(k)}(?![\w`])", plan)]
plan_never = [k for k in d07_in_bundle if k not in plan_names]
print(f"  draft-07 keywords in the bundle: {len(d07_in_bundle)}")
print(f"  named as a literal in codegen/: {len(code_names)} of {len(d07_in_bundle)}; missing: {sorted(set(d07_in_bundle)-set(code_names))}")
print(f"  named anywhere in the plan: {len(plan_names)} of {len(d07_in_bundle)}; never: {plan_never}")
out["D"] = {"draft07_in_bundle": d07_in_bundle, "code_names": code_names, "plan_never": plan_never}

# ---- instrument E: the emitted set ---------------------------------------------------
print("\n=== E: the emitted set (codegen.emit.emit over the portable bundle) ===")
from codegen import emit as emit_module  # noqa: E402

run = emit_module.emit(BUNDLE, docs)
emitted = sorted(run.emitted) if hasattr(run, "emitted") else []
refused = run.refusals if hasattr(run, "refusals") else {}
print(f"  portable {len(docs)}  emitted {len(emitted)}  refused {len(refused)}")
dep_docs = sorted({d for d, _, _ in sites["deprecated"]})
dep_emitted = [d for d in dep_docs if d in set(emitted)]
print(f"  documents carrying `deprecated`: {len(dep_docs)}; of them EMITTED today: {len(dep_emitted)}")
for d in dep_emitted[:12]:
    ptrs = [ptr for dd, ptr, _ in sites["deprecated"] if dd == d]
    print(f"     {d}: {ptrs}")
disc_docs = sorted({d for d, _, _ in sites["discriminator"]})
print(f"  documents carrying `discriminator`: {len(disc_docs)}; EMITTED today: {len([d for d in disc_docs if d in set(emitted)])}")
disc_refused = [(d, r) for d, r in refused.items() if d in disc_docs and getattr(r, 'keyword', None) == 'discriminator']
print(f"  refusals naming `discriminator` as the keyword: {len(disc_refused)}")
sv = "enums/signal-value-type.json"
print(f"  {sv} emitted: {sv in set(emitted)}")
out["E"] = {"emitted": len(emitted), "refused": len(refused), "deprecated_docs": len(dep_docs),
            "deprecated_emitted": dep_emitted, "discriminator_refusals": len(disc_refused),
            "signal_value_type_emitted": sv in set(emitted)}
first_refusal_kw = Counter(getattr(r, "keyword", "?") for r in refused.values())
out["E"]["refusal_keywords"] = dict(first_refusal_kw)
print("  refusal keywords: " + ", ".join(f"{k}={c}" for k, c in first_refusal_kw.most_common(25)))

Path("kw_measure.json").write_text(json.dumps(out, indent=1, default=str))
print("\nwrote kw_measure.json")
