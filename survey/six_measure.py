"""Measurements for reading 1: the declared set today, and the if-row population."""
from __future__ import annotations
import collections, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from codegen import bundle
from adcp.types import _base

BUNDLE = Path("schemas/cache/3.2")


def declarations():
    from compiled import compiled
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    return out


def own_stated(document: str, pointer: str, keyword: str, raw_cache: dict) -> bool:
    """Does the RAW source document state ``keyword`` at ``pointer``?"""
    if document not in raw_cache:
        try:
            raw_cache[document] = bundle.read(BUNDLE, document)
        except Exception:
            raw_cache[document] = None
    doc = raw_cache[document]
    if doc is None:
        return False
    try:
        node = bundle.node_at(doc, pointer)
    except Exception:
        return False
    return isinstance(node, dict) and keyword in node


def main() -> int:
    out = declarations()
    raw: dict = {}
    rows = [(d, a) for d, aa in out.approximations.items() for a in aa]
    print(f"TOTAL declarations: {len(rows)} in {len(out.approximations)} documents")
    by_kind = collections.Counter(a["kind"] if isinstance(a, dict) else a.kind for _, a in rows)
    print(f"  by kind: {dict(by_kind)}")
    by_keyword = collections.Counter(a.keyword for _, a in rows)
    print(f"  by keyword: {dict(by_keyword)}")
    ownsites = [(d, a) for d, a in rows if own_stated(a.document, a.pointer, a.keyword, raw)]
    print(f"  at an OWN-STATED pointer: {len(ownsites)}")
    distinct = {(a.document, a.pointer, a.keyword) for _, a in rows}
    print(f"  distinct (document, pointer, keyword): {len(distinct)}")
    own_distinct = {(a.document, a.pointer, a.keyword) for _, a in ownsites}
    print(f"  distinct own-stated: {len(own_distinct)}")
    print()
    print("  own-stated detail:")
    for d, a in sorted(ownsites, key=lambda r: (r[1].document, r[1].pointer, r[1].keyword)):
        print(f"    {a.kind:16} {a.keyword:16} {a.document}{a.pointer or '/'}  (carried by {d})")
    print()
    print("  NOT own-stated, by (keyword, kind):")
    notown = collections.Counter(
        (a.keyword, a.kind) for _, a in rows if (a.document, a.pointer, a.keyword) not in own_distinct or (d, a) not in ownsites
    )
    bad = [(d, a) for d, a in rows if not own_stated(a.document, a.pointer, a.keyword, raw)]
    print(f"    {len(bad)} entries")
    for key, n in collections.Counter((a.keyword, a.kind) for _, a in bad).most_common():
        print(f"      {key}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
