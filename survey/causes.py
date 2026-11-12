"""Group a drop-in run's failures by CAUSE, reading pytest's own JSON report and nothing else.

    PYTHONPATH=.:src ./.venv/bin/python -m survey causes /srv/ws/dropin-keyless
    PYTHONPATH=.:src ./.venv/bin/python -m survey causes <out> --since <previous out>

**IT READS AND IT DOES NOT RUN.**  The owner's instruction, and it is the whole contract of
this module: *"can you just configure the normal JUnit JSON? pytest should produce JSON
reports.  We should be reading those JSON reports and never guessing whatever that fuck
is."*  ``pyproject.toml``'s ``addopts`` carries ``--junitxml`` and ``--json-report``, so a
run writes ``<out>/junit/chunk-*.json`` with one entry per test -- its ``nodeid``, its
``outcome`` and its ``longrepr``.  This module opens those files.  It never invokes pytest,
never re-runs a test to find out what it did, and never decides an outcome: an outcome is a
field, read.  What it adds is the GROUPING, which is the thing a reader was doing by hand
four times over and getting slightly different numbers for each time.

**A CAUSE IS A RULE OVER THE REPORT'S OWN TEXT, AND EVERY RULE NAMES ITS OWNER.**  The
rules are ordered and the FIRST that matches wins, so the table partitions: every failure
lands in exactly one cause, and what matches nothing is the RESIDUE -- printed with its
signature and its files, because an unowned failure is the only kind that needs a decision.
The owner is a lane, so "what is this lane's number" and "what is left" are the same
reading rather than two.

**AND THE RAISING CALL SITE IS WHOSE IT IS.**  A frame in ``src/adcp/`` means the SDK
constructed a document its own schema refuses, which is ours; a frame only in ``tests/``
means the payload is upstream's premise.  The split is reported per cause because it is
what decides whether a repair is a code change or a payload correction, and reading it off
the traceback is cheaper and more honest than remembering it.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
from typing import Any

#: The ordered rules.  ``(owner, cause, predicate)`` over one failure's whole longrepr and
#: its nodeid; FIRST match wins, so the table partitions.  Ordered by what SUBSUMES what:
#: the ``None`` rule runs before the per-class rules because a ``None`` at a field of
#: ``GetProductsResponse`` is the route-split cause and not a ``status`` cause.
_NONE = re.compile(r"Input should be a valid \w+ \[type=\w+, input_value=None")
_STATUS = re.compile(r"^E?\s*status\n(?:E\s+)?\s*Field required", re.M)

RULES: tuple[tuple[str, str, Any], ...] = (
    (
        "presence",
        "a None where the document admits a value or the key's absence",
        lambda nid, txt: bool(_NONE.search(txt)) or "test_no_explicit_null" in nid,
    ),
    (
        "nocanon",
        "status: core/protocol-envelope.json requires it and the payload omits it",
        lambda nid, txt: bool(_STATUS.search(txt)) or "status\n    Field required" in txt,
    ),
    (
        "nocanon",
        "a conditional the document states and the payload does not satisfy",
        lambda nid, txt: "required when " in txt,
    ),
    (
        "nocanon",
        "the drop-in venv is missing a dependency upstream's suite imports",
        lambda nid, txt: "No module named" in txt,
    ),
    (
        "drawcost",
        "Format: the v1 definition answering where the canonical declaration is meant",
        lambda nid, txt: bool(re.search(r"errors? for Format\b", txt)),
    ),
    (
        "drawcost",
        "the format family: declaration, projection and the v1/v2 conversion",
        lambda nid, txt: any(
            w in nid
            for w in (
                "test_product_format_declaration",
                "canonical_formats",
                "test_mixed_legacy_projection",
            )
        ),
    ),
    (
        "distinct",
        "schema/model parity: the model accepts what the bundled schema refuses",
        lambda nid, txt: "test_schema_model_parity" in nid,
    ),
    (
        "aliasnote",
        "the asset union read as a structure rather than as a branch registry",
        lambda nid, txt: "_legacy_assets" in txt or "test_legacy_asset_helpers" in nid,
    ),
    (
        "aliasnote",
        "STATUS_READ_FAILED masking the code that names the defect",
        lambda nid, txt: "STATUS_READ_FAILED" in txt,
    ),
    (
        "namereach",
        "a word upstream publishes that resolves at no module of ours",
        lambda nid, txt: "resolves at no module" in txt or "test_postal_area" in nid,
    ),
    (
        "namereach",
        "model_summary keyed on __class__.__name__, which is a spelling",
        lambda nid, txt: "model_summary" in txt or "test_response_str" in nid,
    ),
    (
        "namereach",
        "operation_id: a field upstream's class states and its document does not",
        lambda nid, txt: "operation_id" in txt,
    ),
)


#: ``pytest-xdist`` appends the worker's banner to every longrepr it reports, sometimes
#: twice.  It is not part of what the test said, and left in it becomes a SIGNATURE: 24
#: residue failures grouped under ``n[gw3] linux -- Python 3.12.13 /srv/ws/...``, which
#: names the worker that ran them and nothing about why they failed.
#: The path is matched WITHOUT ``[``: two banners are reported back to back with no
#: separator, so a greedy ``\S+`` eats the next one's ``[gw`` and leaves half a banner
#: behind -- which read as a signature for 18 more failures.
_WORKER = re.compile(r"\[gw\d+\] \w+ -- Python [\d.]+ [^\s\[]+")


def _longrepr(test: dict) -> str:
    return _WORKER.sub(
        "",
        "".join(
            str((test.get(phase) or {}).get("longrepr") or "")
            for phase in ("call", "setup", "teardown")
        ),
    )


def _sites(txt: str) -> tuple[str, str]:
    """``(ours, theirs)`` -- the deepest frame in ``src/adcp/`` and in ``tests/``.

    Both, and never one: a failure whose traceback passes through both is a payload of
    theirs reaching a construction of ours, and which of the two to repair is a reading of
    the document rather than of the traceback.  Reporting only the innermost frame hid that
    -- 97 failures answered ``src/adcp/types/_base.py:1816``, the model ``__init__``, which
    names no caller at all.
    """
    ours = [
        f"{f}:{line}"
        for f, line in re.findall(r"^(src/adcp/[\w/\.\-]+\.py):(\d+):", txt, re.M)
        if "types/_base.py" not in f
    ]
    theirs = re.findall(r"^(tests/[\w/\.\-]+\.py):(\d+):", txt, re.M)
    return (
        ours[-1] if ours else "",
        f"{theirs[-1][0]}:{theirs[-1][1]}" if theirs else "",
    )


def read(out: pathlib.Path) -> tuple[collections.Counter, list[tuple[str, str]]]:
    """``(outcomes, failures)`` from every ``junit/chunk-*.json`` under ``out``.

    A run writes one report per chunk and the chunks partition the population, so the four
    are read together and never one as a sample.  A missing or unparsable file is REPORTED
    rather than skipped: a chunk that did not write its report is a chunk whose tests are
    absent from every number below, which is the shape of defect that let a dead run be
    reported as "still running" for an hour.
    """
    outcomes: collections.Counter = collections.Counter()
    failures: list[tuple[str, str]] = []
    reports = sorted((out / "junit").glob("chunk-*.json"))
    if not reports:
        raise SystemExit(f"no chunk reports under {out / 'junit'}; was the run given --run?")
    for report in reports:
        try:
            tests = json.loads(report.read_text()).get("tests", [])
        except (OSError, ValueError) as why:
            raise SystemExit(f"{report} is not a readable report: {why}") from None
        for test in tests:
            outcomes[test["outcome"]] += 1
            if test["outcome"] in ("failed", "error"):
                failures.append((test["nodeid"], _longrepr(test)))
    outcomes["chunks read"] = len(reports)
    return outcomes, failures


def classify(
    failures: list[tuple[str, str]],
) -> tuple[collections.Counter, dict[str, set[str]], list[tuple[str, str]]]:
    """``(per cause, nodeids per owner, residue)``.  First rule wins, so this partitions."""
    counts: collections.Counter = collections.Counter()
    by_owner: dict[str, set[str]] = collections.defaultdict(set)
    residue: list[tuple[str, str]] = []
    for nodeid, txt in failures:
        for owner, cause, matches in RULES:
            if matches(nodeid, txt):
                counts[(owner, cause)] += 1
                by_owner[owner].add(nodeid)
                break
        else:
            residue.append((nodeid, txt))
    return counts, by_owner, residue


def _signature(nodeid: str, txt: str) -> str:
    """One line naming what a residue failure says, for a reader deciding an owner."""
    validated = re.search(r"validation errors? for (\w+)", txt)
    if validated:
        fields = re.findall(r"^E\s+(\w[\w\.\d\[\]]*)\n(?:E\s+)?\s*(\w[^\[\n]{0,36})", txt, re.M)
        at, why = fields[0] if fields else ("?", "")
        return f"{validated.group(1)}.{at}: {why.strip()[:40]}"
    said = re.search(r"^E\s+(\w*(?:Error|Exception)(?:: )?.{0,56}|assert.{0,56})", txt, re.M)
    if said:
        return said.group(1).strip()
    # No ``E`` line at all, which is a failure reported by something other than an
    # assertion -- a collection error, a subprocess verdict, a fixture raising.  The LAST
    # non-empty line is what it ended on, and slicing the text by offset instead cut words
    # in half and signed eight failures as ``erty list resolution failed``.
    lines = [line.strip() for line in txt.splitlines() if line.strip()]
    return lines[-1] if lines else "(the report carries no longrepr)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", help="a drop-in run's output directory")
    parser.add_argument("--since", help="a previous run, to report what moved")
    parser.add_argument("--residue", type=int, default=24, help="residue signatures to print")
    ns = parser.parse_args(argv)

    out = pathlib.Path(ns.out)
    outcomes, failures = read(out)
    counts, by_owner, residue = classify(failures)

    print(f"== {out}")
    for name in ("passed", "failed", "error", "skipped", "xfailed", "chunks read"):
        if name in outcomes:
            print(f"   {outcomes[name]:6d}  {name}")
    print(f"   {sum(outcomes[k] for k in ('passed', 'failed', 'error', 'skipped')):6d}  collected")

    print("\n== owned, by cause (first rule wins, so this partitions)")
    for (owner, cause), n in counts.most_common():
        print(f"   {n:5d}  {owner:10s} {cause}")
    print(f"   {sum(counts.values()):5d}  == owned, over {len(by_owner)} lanes")

    print(f"\n== RESIDUE: {len(residue)} failures no rule claims")
    signatures: collections.Counter = collections.Counter()
    files: collections.Counter = collections.Counter()
    whose: collections.Counter = collections.Counter()
    for nodeid, txt in residue:
        signatures[_signature(nodeid, txt)] += 1
        files[nodeid.split("::")[0]] += 1
        ours, theirs = _sites(txt)
        where = (
            "a frame in src/adcp/ (OURS)"
            if ours
            else "tests/ only (THEIRS)"
            if theirs
            else "neither named"
        )
        whose[where] += 1
    for where, n in whose.most_common():
        print(f"   {n:5d}  {where}")
    print()
    for signature, n in signatures.most_common(ns.residue):
        print(f"   {n:4d}  {signature[:96]}")
    print()
    for name, n in files.most_common(12):
        print(f"   {n:4d}  {name}")

    if ns.since:
        was_outcomes, was_failures = read(pathlib.Path(ns.since))
        was = {nodeid for nodeid, _ in was_failures}
        now = {nodeid for nodeid, _ in failures}
        print(f"\n== against {ns.since}")
        was_red = was_outcomes["failed"] + was_outcomes["error"]
        red = outcomes["failed"] + outcomes["error"]
        print(
            f"   passed {was_outcomes['passed']} -> {outcomes['passed']}"
            f"  ({outcomes['passed'] - was_outcomes['passed']:+d})"
        )
        print(f"   failed {was_red} -> {red}  ({red - was_red:+d})")
        print(f"   newly failing: {len(now - was)}")
        for nodeid in sorted(now - was)[:12]:
            print(f"      {nodeid}")
        print(f"   newly passing: {len(was - now)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
