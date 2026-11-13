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
import subprocess
from typing import Any

#: The ordered rules.  ``(owner, cause, predicate)`` over one failure's whole longrepr and
#: its nodeid; FIRST match wins, so the table partitions.  Ordered by what SUBSUMES what:
#: the ``None`` rule runs before the per-class rules because a ``None`` at a field of
#: ``GetProductsResponse`` is the route-split cause and not a ``status`` cause.
_NONE = re.compile(r"Input should be a valid \w+ \[type=\w+, input_value=None")
_STATUS = re.compile(r"^E?\s*status\n(?:E\s+)?\s*Field required", re.M)

#: **A SWALLOW DEFEATS EVERY RULE ABOVE, so the REDACTION is read instead.**  A broad
#: ``except`` that raises a typed error hides the cause from a reader AND from this table:
#: 17 failures reported ``SERVICE_UNAVAILABLE / transient`` for a ``GetPropertyListRequest``
#: refused at ``pagination.cursor`` and read here as an unowned cause, because no rule can
#: see a refusal the report does not carry.  ``adcp._redaction.refused_at`` now names the
#: fault in the warning those paths already emit, as ``loc.path [type_code]``.
#:
#: The type codes below are the ones :data:`adcp.types._base.OmittedNotNull` produces for a
#: null: it strikes the null arm, so what refuses is the TYPE's own keyword and the row
#: reads ``string_type``/``list_type``/``model_type`` rather than anything naming null.
#: That is why a redacted fault with one of them is the route-split cause -- stated here
#: because it is an INFERENCE from the marker's own documented behaviour and not, like
#: every other rule, a quotation of what the report says.
_SWALLOWED_NULL = re.compile(
    r"resolution failed: ValidationError: [^\n]*"
    r"\[(?:string_type|list_type|model_type|dict_type|bool_type|int_type|float_type)\]"
)

RULES: tuple[tuple[str, str, Any], ...] = (
    (
        "presence",
        "a None where the document admits a value or the key's absence",
        lambda nid, txt: bool(_NONE.search(txt)) or "test_no_explicit_null" in nid,
    ),
    (
        "presence",
        "a swallowed refusal whose redacted fault is a struck null arm",
        lambda nid, txt: bool(_SWALLOWED_NULL.search(txt)),
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


def _graded(out: pathlib.Path) -> str | None:
    """The commit of THIS repository the run graded, from its own manifest.

    ``survey.regenerate`` already records it as ``this repository: {head, dirty}``, and
    reading it here is what lets a comparison say whether it is a comparison at all.
    """
    try:
        record = json.loads((out / "REGENERATED.json").read_text())
    except (OSError, ValueError):
        return None
    repo = record.get("this repository") or {}
    head = repo.get("head")
    return f"{head}{'+dirty' if repo.get('dirty') else ''}" if head else None


def _is_ancestor(older: str, newer: str) -> bool | None:
    """Is ``older`` an ancestor of ``newer``?  ``None`` where git cannot say."""
    try:
        done = subprocess.run(
            ["git", "merge-base", "--is-ancestor", older.split("+")[0], newer.split("+")[0]],
            capture_output=True,
        )
    except OSError:
        return None
    return done.returncode == 0 if done.returncode in (0, 1) else None


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


def read(
    out: pathlib.Path,
) -> tuple[collections.Counter, list[tuple[str, str]], set[str]]:
    """``(outcomes, failures, every nodeid)`` from every ``junit/chunk-*.json`` under ``out``.

    **THE THIRD VALUE IS WHAT MAKES A REGRESSION DISTINGUISHABLE FROM AN ARRIVAL.**  A
    nodeid absent from a previous run did not regress in this one, however red it is; it
    was not there.  Without the full set, ``now - was`` reads a newly COLLECTED failure as
    a regression, which is how a provisioning fix worth 1,468 more collected tests was
    reported as "+887 passed, 221 newly failing".

    A run writes one report per chunk and the chunks partition the population, so the four
    are read together and never one as a sample.  A missing or unparsable file is REPORTED
    rather than skipped: a chunk that did not write its report is a chunk whose tests are
    absent from every number below, which is the shape of defect that let a dead run be
    reported as "still running" for an hour.
    """
    outcomes: collections.Counter = collections.Counter()
    failures: list[tuple[str, str]] = []
    every: set[str] = set()
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
            every.add(test["nodeid"])
            if test["outcome"] in ("failed", "error"):
                failures.append((test["nodeid"], _longrepr(test)))
    outcomes["chunks read"] = len(reports)
    return outcomes, failures, every


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
    outcomes, failures, seen = read(out)
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
        was_outcomes, was_failures, was_seen = read(pathlib.Path(ns.since))
        was = {nodeid for nodeid, _ in was_failures}
        now = {nodeid for nodeid, _ in failures}
        print(f"\n== against {ns.since}")

        # **AND THE TWO RUNS MUST HAVE GRADED THE SAME LINE OF WORK, which is the second
        # thing to get wrong and the harder one to see.**  Measured: a lane compared its
        # branch against another lane's artifact and read 152 REGRESSIONS, every one in
        # tests/conformance/signing/ -- which were not its regressions at all but the
        # absence of the OTHER lane's route split from its own tree.  A run records the
        # commit it graded; if the previous one is not an ancestor of this one, the
        # difference is the difference between two changes and is attributable to neither.
        then, here = _graded(pathlib.Path(ns.since)), _graded(out)
        if then and here and then != here:
            print(f"   graded {then[:12]} -> {here[:12]}")
            ancestor = _is_ancestor(then, here)
            if ancestor is False:
                print("   !! NOT AN ANCESTOR.  These two runs graded divergent trees, so")
                print("      every figure below is the difference between TWO changes.")
                print("      Re-run the baseline from this run's own merge-base, or")
                print("      compare against a run of trunk.")
            elif ancestor is None:
                print("      (git could not say whether one precedes the other)")

        # **THE POPULATIONS MUST MATCH OR THE DIFFERENCE IS NOT ATTRIBUTABLE**, and that is
        # the first thing printed because it is the first thing to get wrong.  Measured: a
        # provisioning fix that installed three missing dev dependencies took the collected
        # count from 13,817 to 15,285, and the 1,468 newly COLLECTED tests include 221 that
        # fail -- which the old reading printed as "newly failing: 221" beside "+887
        # passed", reading as a large gain with a large regression when it was neither.
        # And two runs built from DIFFERENT TREES cannot be subtracted at all: a lane
        # comparing its branch against another lane's artifact attributes its own change
        # the difference between two other changes.
        was_total = sum(was_outcomes[k] for k in ("passed", "failed", "error", "skipped"))
        total = sum(outcomes[k] for k in ("passed", "failed", "error", "skipped"))
        if was_total != total:
            print(f"   !! COLLECTED {was_total} -> {total} ({total - was_total:+d}).")
            print("      The populations differ, so passed/failed are NOT subtractable:")
            print("      a test that did not run before cannot have regressed, and one")
            print("      that no longer runs did not start passing.  The split below is")
            print("      the only honest reading of a run against a different population.")

        was_red = was_outcomes["failed"] + was_outcomes["error"]
        red = outcomes["failed"] + outcomes["error"]
        print(
            f"   passed {was_outcomes['passed']} -> {outcomes['passed']}"
            f"  ({outcomes['passed'] - was_outcomes['passed']:+d})"
        )
        print(f"   failed {was_red} -> {red}  ({red - was_red:+d})")

        # **A REGRESSION IS A TEST THAT RAN BEFORE AND PASSED.**  Everything else in
        # ``now - was`` is a test the previous run never saw, and calling it a regression
        # is the instrument inventing one.
        regressed = sorted(n for n in now - was if n in was_seen)
        arrived = sorted(n for n in now - was if n not in was_seen)
        fixed = sorted(n for n in was - now if n in seen)
        gone = sorted(n for n in was - now if n not in seen)
        print(f"   REGRESSED (ran before, passed before, fails now): {len(regressed)}")
        for nodeid in regressed[:14]:
            print(f"      {nodeid}")
        if len(regressed) > 14:
            print(f"      … and {len(regressed) - 14} more")
        print(f"   newly collected and failing (never ran before): {len(arrived)}")
        for nodeid in arrived[:6]:
            print(f"      {nodeid}")
        if len(arrived) > 6:
            print(f"      … and {len(arrived) - 6} more")
        print(f"   FIXED (ran before, failed before, passes now): {len(fixed)}")
        print(f"   no longer collected (was failing, absent now): {len(gone)}")
        for nodeid in gone[:6]:
            print(f"      {nodeid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
