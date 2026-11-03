"""Reading 1's §3a measurement: unreadable `if` conditions, and the storage read-through.

Over every portable document's STORED record -- the text the walk actually sees -- count
the nodes whose ``if`` the ``Match`` reduction cannot read, and split them by what
reading through the record's own ``definitions`` storage answers.
"""
from __future__ import annotations
import collections, json, sys
from pathlib import Path

from adcp.types import _base
from codegen import bundle
from codegen.keywords import Position
from codegen.lower import rules as R

BUNDLE = Path("schemas/cache/3.2")


def deref(node, root, depth=0):
    """Follow a LOCAL reference -- the storage's or the document's own -- one node deep."""
    for _ in range(8):
        if not isinstance(node, dict):
            return node
        uri = node.get("$ref")
        if not isinstance(uri, str) or not uri.startswith("#"):
            return node
        try:
            target = bundle.node_at(root, uri[1:])
        except Exception:
            return node
        if not isinstance(target, dict):
            return node
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


def readable_through(sub, root):
    """Is the condition readable once storage references are followed?"""
    if not isinstance(sub, dict):
        return None
    one = deref(sub, root)
    if not isinstance(one, dict):
        return None
    # follow a reference inside each property declaration too
    props = one.get("properties")
    if isinstance(props, dict):
        one = {**one, "properties": {k: deref(v, root) for k, v in props.items()}}
    return R._clauses(one)


def main():
    known = set(bundle.portable(BUNDLE))
    buckets = collections.Counter()
    facts: dict[str, set] = collections.defaultdict(set)
    negated_sites = collections.Counter()
    per_doc = collections.defaultdict(collections.Counter)
    for document in sorted(known):
        rec = bundle.record(BUNDLE, document, known)
        if not isinstance(rec, dict):
            continue
        for pointer, node in bundle.nodes(rec):
            if "if" not in node:
                continue
            raw = node["if"]
            if R._clauses(raw) is not None:
                buckets["readable as written"] += 1
                continue
            # it is one of the drops today
            buckets["UNREADABLE today"] += 1
            after = readable_through(raw, rec)
            one = deref(raw, rec)
            key = json.dumps(raw, sort_keys=True, default=str)
            if after is not None:
                buckets["  lowers exactly through the storage"] += 1
                per_doc[document]["through-store"] += 1
                facts["through-store"].add(json.dumps(one, sort_keys=True, default=str))
            elif isinstance(one, dict) and set(R._keys(one)) == {"not"}:
                buckets["  NEGATED -> declares"] += 1
                per_doc[document]["negated"] += 1
                facts["negated"].add(json.dumps(one, sort_keys=True, default=str))
                negated_sites[f"{document}#{pointer}"] += 1
            else:
                buckets["  other -> declares"] += 1
                per_doc[document]["other"] += 1
                facts["other"].add(json.dumps(one, sort_keys=True, default=str))
    for k, v in buckets.items():
        print(f"{k}: {v}")
    print()
    for k, v in facts.items():
        print(f"distinct facts, {k}: {len(v)}")
    print()
    print("documents with a declaring if:", len([d for d, c in per_doc.items() if c['negated'] or c['other']]))
    print("documents with a through-store if:", len([d for d, c in per_doc.items() if c['through-store']]))
    print()
    print("NEGATED sites (first 60):")
    for s, n in list(negated_sites.most_common())[:60]:
        print("   ", n, s)
    print("negated pointers total:", sum(negated_sites.values()))
    print()
    print("OTHER facts:")
    for f in sorted(facts["other"])[:10]:
        print("   ", f[:300])


if __name__ == "__main__":
    main()
