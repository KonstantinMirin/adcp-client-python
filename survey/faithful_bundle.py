"""What the compiler does with a FAITHFUL 3.2 bundle, beside what it does with ours.

``schemas/cache/3.2`` is not a build output.  ``schemas/cache/3.2.provenance.json``
records the transform: every ``$id`` removed recursively and each document re-serialised
by ``json.dumps(obj, indent=2)``, whose defaults escape every non-ASCII codepoint and
write no trailing newline.  Every figure the epic quotes -- ``emitted 1059 / refused 0``
among them -- is a reading against that transformed directory, so "emitted according to
the schema" is a claim about a directory we wrote and not about the published artifact.

This module is the measurement that closes the gap.  It does not migrate anything: it
vendors the upstream artifact UNTRANSFORMED beside the committed copy, states the
difference in the three respects the transform touches, and runs the same compile over
both so the two readings sit side by side.

::

    # 1. vendor the faithful artifact (upstream's clone is SHALLOW; the artifact is
    #    committed, so `git archive` reads it without moving anybody's HEAD)
    git -C /srv/ws/adcp-upstream archive c34931a089c52797e2c06a846bba3ea38e21b053 \
        dist/schemas/3.2.4 | tar -x -C <out> --strip-components=3

    python survey/faithful_bundle.py transform <faithful> schemas/cache/3.2
    python survey/faithful_bundle.py numbers <bundle>
    python survey/faithful_bundle.py refusals <bundle>
    python survey/faithful_bundle.py restore-id <document>   # bfqk's experiment

``ADCP_CACHE`` must name a directory of this lane's own: six lanes share the default
store and a compile keyed on a bundle outside the checkout is one nobody else wants.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _docs(root: Path) -> dict[str, Path]:
    return {str(p.relative_to(root)): p for p in root.rglob("*.json")}


def _strip(node: object) -> object:
    """Every ``$id`` removed RECURSIVELY, which is the transform's first half."""
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k != "$id"}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def _nested_ids(node: object, top: bool = True) -> int:
    found = 0
    if isinstance(node, dict):
        found += int(not top and "$id" in node)
        for value in node.values():
            found += _nested_ids(value, False)
    elif isinstance(node, list):
        for value in node:
            found += _nested_ids(value, False)
    return found


def survey(root: Path) -> tuple[int, int, int, int]:
    """``(documents, root $id, non-ASCII, trailing newline)`` over a bundle directory."""
    totals = [0, 0, 0, 0]
    for path in sorted(root.rglob("*.json")):
        raw = path.read_bytes()
        totals[0] += 1
        try:
            node = json.loads(raw)
        except ValueError:
            node = None
        totals[1] += int(isinstance(node, dict) and "$id" in node)
        totals[2] += int(not raw.isascii())
        totals[3] += int(raw.endswith(b"\n"))
    return tuple(totals)  # type: ignore[return-value]


def transform(faithful: Path, committed: Path) -> int:
    """State the difference between the artifact and our copy, in each respect."""
    print("faithful  documents %d  root $id %d  non-ASCII %d  trailing newline %d" % survey(faithful))
    print("committed documents %d  root $id %d  non-ASCII %d  trailing newline %d" % survey(committed))
    a, b = _docs(faithful), _docs(committed)
    print(f"paths only in faithful: {len(set(a) - set(b))}; only in committed: {len(set(b) - set(a))}")
    common = sorted(set(a) & set(b))
    kinds: collections.Counter[str] = collections.Counter()
    differ = reproduced = 0
    unexplained = []
    for name in common:
        raw_a, raw_b = a[name].read_bytes(), b[name].read_bytes()
        if raw_a == raw_b:
            continue
        differ += 1
        node_a, node_b = json.loads(raw_a), json.loads(raw_b)
        if "$id" in node_a and "$id" not in node_b:
            kinds["root $id removed"] += 1
        if _nested_ids(node_a) and not _nested_ids(node_b):
            kinds["nested $id removed"] += 1
        if not raw_a.isascii() and raw_b.isascii():
            kinds["non-ASCII escaped"] += 1
        if raw_a.endswith(b"\n") and not raw_b.endswith(b"\n"):
            kinds["trailing newline dropped"] += 1
        if _strip(node_a) != _strip(node_b):
            kinds["differs BEYOND the transform"] += 1
            unexplained.append(name)
        if json.dumps(_strip(node_a), indent=2) == raw_b.decode():
            reproduced += 1
    print(f"byte-different documents: {differ} of {len(common)} common")
    for kind, count in kinds.most_common():
        print(f"  {kind}: {count}")
    print(f"the transform reproduces the committed bytes exactly: {reproduced} of {len(common)}")
    print(f"not reproduced: {unexplained}")
    return 0


def _out(bundle: Path):
    sys.path.insert(0, str(REPO / "tests"))
    from codegen import bundle as bundle_module
    from codegen import patch

    from compiled import compiled  # type: ignore[import-not-found]

    read = patch.for_build(bundle)
    population = sorted(bundle_module.portable(read))
    print(f"bundle {bundle} -> patched {read}")
    print(f"portable {len(population)} of {len(_docs(read))} documents")
    return compiled(read, population), population


def numbers(bundle: Path) -> int:
    """``./check``'s three numbers, over a bundle named on the command line.

    ``./check`` hard-codes ``schemas/cache/3.2`` and is the fast loop; this is the same
    reading with the bundle as an argument, so the faithful artifact and our copy are
    graded by one function and the two figures are comparable.
    """
    out, _ = _out(bundle)
    kinds = collections.Counter(str(r["kind"]).split(".")[-1] for r in out.refusals.values())
    resolved = collections.Counter(str(r["resolved"]).split(".")[-1] for r in out.refusals.values())
    facts = sum(len(v) for v in out.approximations.values())
    chained = kinds["chained"]
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
        f"(deferred {resolved['deferred']}, verdict {resolved['verdict']}); "
        f"accounted {len(out.emitted) + resolved['verdict']}"
    )
    print(f"primary {len(out.refusals) - chained}, chained {chained}")
    print(f"approximated {facts} facts in {len(out.approximations)} documents")
    return 0


def refusals(bundle: Path) -> int:
    """Every refusal with its document, pointer, keyword and kind, for attribution."""
    out, _ = _out(bundle)
    for document, r in sorted(out.refusals.items()):
        kind = str(r["kind"]).split(".")[-1]
        print(f"{kind:9} {document} at {r['pointer'] or '/'} on {r['keyword']}")
        print(f"          {str(r['detail'])[:400]}")
    return 0


def restore_id(out: Path, committed: Path, faithful: Path, documents: list[str]) -> int:
    """``committed`` copied to ``out`` with the ROOT ``$id`` put back on ``documents``.

    **ONE VARIABLE, which is the whole point of this command.**  The faithful artifact
    differs from our copy in three respects at once; a bundle that differs in all three
    cannot attribute a flipped verdict to any one of them.  This copies the committed
    bundle verbatim -- same escaping, same absent trailing newline -- and puts back only
    the root ``$id`` of the named documents, read from the artifact rather than written
    here.  A verdict that moves between ``out`` and ``committed`` moved on the ``$id``
    and on nothing else.

    ``adcp-client-python-bfqk``'s own predicted experiment: "ADD ``$id`` back to a 3.2
    document and the same failure should appear there.  If that second half reproduces on
    3.2, this row is not about 3.3 at all."
    """
    import shutil

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(committed, out)
    for name in documents:
        node = json.loads((out / name).read_bytes())
        stated = json.loads((faithful / name).read_bytes()).get("$id")
        if stated is None:
            print(f"{name}: the artifact states no root $id; nothing to restore")
            continue
        #: FIRST, because draft-07 reads the identifier off the object and not off the
        #: key order -- but a reader diffing the two files should see the one added line
        #: where the artifact has it.
        (out / name).write_text(json.dumps({"$id": stated, **node}, indent=2))
        print(f"{name}: restored root $id {stated!r}")
    print(f"bundle with the root $id put back on {len(documents)} of "
          f"{len(_docs(out))} documents -> {out}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    command, *rest = argv
    if command == "transform":
        return transform(Path(rest[0]), Path(rest[1]))
    if command == "numbers":
        return numbers(Path(rest[0]))
    if command == "refusals":
        return refusals(Path(rest[0]))
    if command == "restore-id":
        return restore_id(Path(rest[0]), Path(rest[1]), Path(rest[2]), rest[3:])
    print(f"unknown command {command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
