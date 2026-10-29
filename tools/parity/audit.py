"""Parity against another generator over the SAME bundle, in one direction.

    tools/parity/audit.py --theirs /srv/ws/wt-v92 [--ours-src /tmp/.../src]

**The question.**  ``v9.2.0`` of the upstream distribution generates its types from
``schemas/cache/3.2`` -- the bundle this compiler compiles, byte-identical.  So the
question is not "how many classes does each side have" but: **for every (document, node)
their generator represents, do we represent it?**  That direction is the only one that
can fail parity.  A shortfall in our class COUNT is expected -- theirs is known to emit
one node more than once -- and a surplus on their side is a candidate duplication, which
this script quantifies rather than asserts.

**Isolating their 3.2-derived classes.**  Their tree carries several layers and only one
of them is generated from bundle 3.2:

* ``adcp/types/domains/**`` -- datamodel-code-generator's output over
  ``schemas/cache/3.2``, one module per document, each carrying the generator's own
  ``# filename:`` header.  ``scripts/generate_types.py`` sets ``SCHEMAS_DIR`` to
  ``schemas/cache/<resolve_bundle_key(ADCP_VERSION)>`` and ``ADCP_VERSION`` is
  ``3.2.4``, so the bundle key is ``3.2``.  **This is the population.**
* ``adcp/types/domains/bundled/**`` -- the same nodes re-cut for one transport.  Their
  generator keeps exactly one such module.  ``codegen/bundle.PROJECTIONS`` excludes
  ``bundled/`` and ``mcp/`` from our population for that reason, so these classes are
  counted and reported separately, never as a coverage gap.
* ``adcp/types/versioned_bases/**`` -- ``TypedDict`` field templates for bundles 3.0,
  3.1 AND 3.2, from which named bases are built at runtime by ``create_model``.  Not
  pydantic classes, not one bundle, and 3.2's half is built from the bundled
  projections.  Excluded; reported by count.
* ``registry.py``, ``canonical_creative.py``, ``core.py``, ``projections.py``,
  ``capabilities.py``, ``base.py``, ``canonical_decl.py``, ``versioned.py``,
  ``_forward_compat.py`` -- hand-written or generated from something that is not a
  bundle document (``registry.py`` comes from ``schemas/registry-openapi.yaml`` via
  ``scripts/generate_registry_types.py``).  Excluded; reported by module.

**Provenance, and what the match runs on.**  Their tree carries NO per-node key: grep
finds no ``__adcp_schema__`` and no ``SchemaRef`` anywhere under ``src/adcp/types``.
What it carries is the generator's ``# filename:`` header, which is provenance per
MODULE -- i.e. per document.  Ours carries ``__adcp_schema__ = SchemaRef(document,
pointer)`` per class.  So the match key is **document plus a DERIVED node identity**:

* an enum node is its member VALUE set -- not its member names, because our Â§4 rule
  collapses two spellings of one identifier to a ``Literal``;
* a model node is its wire field-name set;
* a root model is the shape of its root.

All three are properties of the schema node.  **A class NAME is never matched on**, which
Â§4 requires: a branch colliding with its root loses the name, rung 2 reads every pin in
key order, and a name difference is therefore expected and is not a gap.

**Four ways a class of theirs is accounted for**, in this order:

1. ``same-document``   -- a class of ours in the same document with the same identity.
2. ``inlined``         -- a class of ours in ANOTHER document with the same identity.
   Their generator inlines some ``$ref`` targets into the referring module, so the node
   is one node of the bundle represented in two of their modules; ours names the target
   and imports it.  Covered, and counted as duplication on their side.
3. ``literal``/``alias`` -- we represent the node without a class: Â§4 emits an ``enum`` on
   an untitled union branch as a ``Literal`` and a root scalar as a module-level alias.
   Matched against the ``Literal`` pins and the module aliases of the same document.
4. ``shape-differs``   -- a class of ours in the same document whose field set overlaps
   but is not equal.  **This is not coverage.**  It is handed to ``probe.py``, which
   adjudicates it against ``Draft7Validator`` on the document payload by payload.

Anything left is ``UNEXPLAINED`` and is named individually with its document.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: Their generator renames ``brand.json`` before running, because the document shares a
#: name with the ``brand/`` directory.  ``scripts/generate_types.py``:
#: ``ROOT_DISCOVERY_SCHEMAS = {Path("brand.json"): Path("brand_discovery.py")}``.  Ours
#: emits the same pair as a package root (``codegen/bundle.package_roots``).
HEADER_REWRITES = {"_brand_discovery.json": "brand.json"}

#: Their layers that are NOT generated from a bundle-3.2 document.
NOT_SCHEMA_LAYER = {
    "adcp/types/registry.py": "generated from schemas/registry-openapi.yaml",
    "adcp/types/canonical_creative.py": "hand-written canonical creative layer",
    "adcp/types/core.py": "hand-written",
    "adcp/types/projections.py": "hand-written projection layer",
    "adcp/types/capabilities.py": "hand-written re-export of the bundled projection",
    "adcp/types/base.py": "hand-written base",
    "adcp/types/canonical_decl.py": "hand-written",
    "adcp/types/versioned.py": "hand-written versioned-extension runtime",
    "adcp/types/_forward_compat.py": "hand-written forward-compatibility layer",
}


def bundle_documents() -> dict[str, str]:
    """Every file of bundle 3.2, keyed also by its ``-``-for-``_`` normalisation.

    Their generator writes module paths with hyphens replaced, and its header echoes
    that spelling.  The normalisation is collision-free on this bundle (measured: 0
    collisions over 1,625 files), so it is a function and not a guess.
    """
    real = {str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*.json")}
    table = {d: d for d in real}
    for d in real:
        table.setdefault(d.replace("-", "_"), d)
    return table


def resolve_document(header: str | None, table: dict[str, str]) -> str | None:
    if header is None:
        return None
    header = HEADER_REWRITES.get(header, header)
    return table.get(header) or table.get(header.replace("-", "_"))


def extract(src: Path, package: str, out: Path) -> dict:
    """Run ``extract.py`` in a CHILD PROCESS, because both trees are named ``adcp``."""
    subprocess.run(
        [sys.executable, str(HERE / "extract.py"), "--src", str(src),
         "--package", package, "--out", str(out)],
        check=True,
    )
    return json.loads(out.read_text())


def key(identity: list) -> tuple:
    return (identity[0], tuple(identity[1]) if isinstance(identity[1], list) else identity[1])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theirs", type=Path, default=Path("/srv/ws/wt-v92"),
                    help="read-only checkout of the other distribution")
    ap.add_argument("--ours-src", type=Path, default=REPO / "src",
                    help="our src/ -- point this at a FRESH emit, not a stale tree")
    ap.add_argument("--work", type=Path, default=Path("/tmp/parity"))
    ap.add_argument("--reuse", action="store_true", help="reuse existing dumps")
    args = ap.parse_args(argv)
    args.work.mkdir(parents=True, exist_ok=True)

    ours_dump, theirs_dump = args.work / "ours.json", args.work / "theirs_full.json"
    if args.reuse and ours_dump.exists() and theirs_dump.exists():
        ours, theirs = json.loads(ours_dump.read_text()), json.loads(theirs_dump.read_text())
    else:
        ours = extract(args.ours_src, "adcp.types._schemas", ours_dump)
        theirs = extract(args.theirs / "src", "adcp.types", theirs_dump)

    table = bundle_documents()

    # ---- their population, and the layers held out of it -------------------------
    population, projection, held = [], [], collections.Counter()
    for cls in theirs["classes"]:
        file = cls["file"]
        if file.startswith("adcp/types/domains/bundled/"):
            projection.append(cls)
        elif file.startswith("adcp/types/domains/"):
            document = resolve_document(cls["header_document"], table)
            if document is None:
                held[f"{file} (header {cls['header_document']!r} resolves to no 3.2 file)"] += 1
                continue
            cls["document"] = document
            population.append(cls)
        else:
            held[NOT_SCHEMA_LAYER.get(file, file)] += 1

    # ---- our side ----------------------------------------------------------------
    ours_by_doc: dict[str, dict[tuple, list]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    ours_anywhere: dict[tuple, list] = collections.defaultdict(list)
    for cls in ours["classes"]:
        ref = cls["schema_ref"]
        if ref is None:
            continue
        cls["document"] = ref["document"]
        ours_by_doc[ref["document"]][key(cls["identity"])].append(cls)
        ours_anywhere[key(cls["identity"])].append(cls)

    # every Literal pinned by a field of a class of one document, and every module
    # alias of that document: Â§4's two class-free representations.
    literals: dict[str, set[tuple]] = collections.defaultdict(set)
    for cls in ours["classes"]:
        document = (cls["schema_ref"] or {}).get("document")
        for field in cls["fields"].values():
            if field["literal"]:
                literals[document].add(tuple(sorted(field["literal"])))
    aliases: dict[str, dict[str, str]] = {}
    our_modules = {}
    for module in ours["modules"]:
        document = resolve_document(module["header_document"], table)
        if document:
            aliases[document] = module["aliases"]
            our_modules[document] = module["module"]

    # ---- the one-directional match -----------------------------------------------
    verdicts = collections.Counter()
    rows = collections.defaultdict(list)
    for cls in population:
        document, identity = cls["document"], key(cls["identity"])
        if identity in ours_by_doc.get(document, {}):
            verdict = "same-document"
            cls["ours"] = ours_by_doc[document][identity][0]
        elif identity in ours_anywhere:
            verdict = "inlined"
            cls["ours"] = ours_anywhere[identity][0]
        elif identity[0] == "enum" and tuple(sorted(identity[1])) in literals.get(document, ()):
            verdict = "literal"
        elif identity[0] == "enum" and any(
            tuple(sorted(identity[1])) in pins for pins in literals.values()
        ):
            verdict = "literal-elsewhere"
        elif document not in our_modules:
            verdict = "document-absent"
        else:
            overlap = _best_overlap(cls, ours_by_doc.get(document, {}))
            if overlap is not None:
                verdict, cls["ours"] = "shape-differs", overlap
            elif identity[0] == "model" and _alias_covers(cls, aliases.get(document, {})):
                verdict = "alias"
            else:
                verdict = "UNEXPLAINED"
        verdicts[verdict] += 1
        rows[verdict].append(cls)

    # ---- duplication on their side -----------------------------------------------
    strict = collections.defaultdict(list)
    for cls in population:
        signature = (
            cls["document"],
            key(cls["identity"]),
            tuple(sorted((n, f["annotation"], f["required"]) for n, f in cls["fields"].items())),
            cls["extra"],
        )
        strict[signature].append(cls)
    intra = {s: group for s, group in strict.items() if len(group) > 1}

    shared = collections.defaultdict(list)
    for cls in population:
        shared[key(cls["identity"])].append(cls)
    fanout = {
        identity: group
        for identity, group in shared.items()
        if len(group) > 1 and len(ours_anywhere.get(identity, ())) == 1
    }

    # ---- report ------------------------------------------------------------------
    print("=" * 78)
    print("THEIR POPULATION -- what is generated from bundle 3.2, and what is not")
    print("=" * 78)
    print(f"  {len(population):5d}  adcp/types/domains/** minus bundled/  <- THE POPULATION")
    print(f"  {len(projection):5d}  adcp/types/domains/bundled/**  (a projection; "
          f"codegen/bundle.PROJECTIONS excludes it from ours)")
    for reason, count in held.most_common():
        print(f"  {count:5d}  held out: {reason}")
    print(f"  {len(population) + len(projection) + sum(held.values()):5d}  total classes "
          f"in their adcp.types")
    print(f"\n  their documents: {len({c['document'] for c in population})}"
          f"   our documents with a module: {len(our_modules)}")
    print(f"  our classes carrying __adcp_schema__: {sum(len(v) for v in ours_anywhere.values())}")

    print("\n" + "=" * 78)
    print("1. COVERAGE -- for every node theirs represents, do we represent it?")
    print("=" * 78)
    for verdict in ("same-document", "inlined", "literal", "literal-elsewhere", "alias",
                    "shape-differs", "document-absent", "UNEXPLAINED"):
        if verdicts[verdict]:
            print(f"  {verdicts[verdict]:5d}  {verdict}")
    covered = sum(verdicts[v] for v in
                  ("same-document", "inlined", "literal", "literal-elsewhere", "alias"))
    print(f"  ----- \n  {covered:5d}  COVERED of {len(population)}"
          f"   ({100 * covered / max(len(population), 1):.2f}%)")

    for verdict in ("document-absent", "UNEXPLAINED", "shape-differs"):
        if not rows[verdict]:
            continue
        print(f"\n--- {verdict}: {len(rows[verdict])} ---")
        for cls in sorted(rows[verdict], key=lambda c: (c["document"], c["name"])):
            theirs_fields = sorted(cls["fields"])
            line = f"  {cls['document']}  {cls['name']}  [{cls['identity'][0]}]"
            if verdict == "shape-differs":
                mine = set(cls["ours"]["fields"])
                line += (f"\n      ours {cls['ours']['name']} at {cls['ours']['schema_ref']['pointer']}"
                         f"\n      only-theirs {sorted(set(theirs_fields) - mine)}"
                         f"\n      only-ours   {sorted(mine - set(theirs_fields))}")
            else:
                line += f"\n      fields/members {theirs_fields or cls.get('members') or cls.get('root_shape')}"
            print(line)

    print("\n" + "=" * 78)
    print("2. DUPLICATION on their side")
    print("=" * 78)
    print(f"  {len(intra):5d} nodes emitted MORE THAN ONCE within one document with an "
          f"identical shape,\n        accounting for {sum(len(g) for g in intra.values())} "
          f"classes ({sum(len(g) for g in intra.values()) - len(intra)} redundant)")
    for signature, group in sorted(intra.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"     x{len(group)}  {signature[0]}  {[c['name'] for c in group]}")
    print(f"\n  {len(fanout):5d} nodes we represent with ONE class that theirs represents with "
          f"several,\n        accounting for {sum(len(g) for g in fanout.values())} of their classes")
    for identity, group in sorted(fanout.items(), key=lambda kv: -len(kv[1]))[:15]:
        one = ours_anywhere[identity][0]
        print(f"     x{len(group)}  ours {one['document']}#{one['schema_ref']['pointer']}"
              f" -> theirs {[c['name'] for c in group][:6]}")

    (args.work / "findings.json").write_text(json.dumps(
        {
            "population": len(population),
            "verdicts": dict(verdicts),
            "rows": {v: [{k: c.get(k) for k in
                          ("document", "name", "module", "identity", "fields", "members",
                           "root_shape", "extra", "ours")} for c in group]
                     for v, group in rows.items()
                     if v in ("UNEXPLAINED", "document-absent", "shape-differs")},
            "duplication": {
                "intra_document_identical": [
                    {"document": s[0], "names": [c["name"] for c in g],
                     "modules": sorted({c["module"] for c in g})}
                    for s, g in sorted(intra.items(), key=lambda kv: -len(kv[1]))
                ],
                "one_of_ours_many_of_theirs": [
                    {"ours": ours_anywhere[i][0]["document"] + "#" +
                             ours_anywhere[i][0]["schema_ref"]["pointer"],
                     "ours_name": ours_anywhere[i][0]["name"],
                     "theirs": [{"module": c["module"], "name": c["name"]} for c in g]}
                    for i, g in sorted(fanout.items(), key=lambda kv: -len(kv[1]))
                ],
            },
        }, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {args.work / 'findings.json'}")
    return 0


def _best_overlap(cls: dict, candidates: dict[tuple, list]) -> dict | None:
    """The class of ours in the same document whose field set overlaps theirs most.

    Only models, and only where the overlap is more than half of each side -- a weaker
    rule matches two unrelated nodes that happen to share ``id``.
    """
    if cls["identity"][0] != "model" or not cls["fields"]:
        return None
    mine = set(cls["fields"])
    best, score = None, 0.0
    for identity, group in candidates.items():
        if identity[0] != "model":
            continue
        for candidate in group:
            other = set(candidate["fields"])
            if not other:
                continue
            jaccard = len(mine & other) / len(mine | other)
            if jaccard > score:
                best, score = candidate, jaccard
    return best if score > 0.5 else None


def _alias_covers(cls: dict, aliases: dict[str, str]) -> bool:
    """Whether a module alias of the same document names the node's own fields."""
    return any(all(name in text for name in cls["fields"]) for text in aliases.values())


if __name__ == "__main__":
    sys.exit(main())
