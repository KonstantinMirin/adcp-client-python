"""The RUN leaves a per-pair verdict table on disk, and a blank verdict is not a pass.

``docs/plan/architecture.md`` §10 requires it and ``adcp-client-python-82m.4`` says what it
replaces: *"one row per graded pair, written to a FILE by the run -- document, pointer, and
each check's verdict -- because a figure that exists only in a terminal cannot be reviewed,
and because a check that computed nothing shows up there as a blank column instead of as a
pass."*

**Two obligations, and they fail for different reasons.**

1. The RUN writes it.  ``python -m codegen`` is driven as a subprocess over one document and
   the file is read back off the path the run printed -- so what is graded is the command a
   reviewer types, not a function this file calls.  Before
   ``adcp-client-python-82m.4`` the command wrote nothing at all and printed no path.
2. A verdict that was never computed is a THIRD value.  Three checks were counted as
   passing while having never run -- one died in a first loop before the loop holding its
   assertion, one raised in its own setup, and four pairs of this very bundle name a pointer
   the document of record does not carry, so building the pair raises ``KeyError``.  Each of
   those is a blank column, and in a pass/fail summary a blank is indistinguishable from
   success.  So the table's cells are asserted to distinguish three states, and the row for a
   pair that reached no check at all is asserted to be unreadable as a pass.

Nothing here asserts a code shape: both obligations are read off an artifact the run
produced, and the second is read off the TEXT of a row rather than off the function that
built it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import fresh

from adcp.types._base import SchemaRef
from codegen import harness

REPO = Path(__file__).resolve().parents[1]
#: **The PUBLISHED bundle, taken from the ONE declaration of it, and it is the right one
#: here** -- which is the answer ``adcp-client-python-lzzj.11.1`` got by measuring instead
#: of assuming.  This module's subject is the ENTRY POINT: it runs ``python -m codegen
#: --bundle <this>`` and reads the verdict table off that run's stdout.  ``--bundle`` is
#: D9's ARGUMENT and ``codegen/__main__.py`` applies ``patch.for_build`` to whatever it is
#: handed, so the run writes a tree from the PATCHED bundle either way and handing it the
#: patched directory applies the table TWICE:
#:
#:     ValueError: core/currency-code.json: the published bundle already holds it
#:
#: So the second bundle is not an oversight here, it is the command's input, and the
#: declaration this module needs is ``fresh.PUBLISHED`` rather than a literal of its own.
#: Named in :data:`tests.test_the_bundle_a_module_reads.BY_DESIGN` for that reason.
BUNDLE = fresh.PUBLISHED

#: One document with one pair, a committed corpus entry and no declaration, so the
#: subprocess below costs an emit and no draw.  Named rather than selected: what this file
#: grades is that a table EXISTS and what its cells mean, and a selector would make the
#: run's cost a function of whatever the selector happened to reach.
DOCUMENT = "core/pagination-request.json"


def _run(tree: Path) -> tuple[str, Path]:
    """``python -m codegen`` over :data:`DOCUMENT`, and the path it named on stdout."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "codegen",
            "--bundle",
            str(BUNDLE),
            "--tree",
            str(tree / "_schemas"),
            DOCUMENT,
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": f"{REPO}:{REPO / 'src'}", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    named = [
        word
        for line in proc.stdout.splitlines()
        if line.startswith("verdicts ")
        for word in line.split()
        if word.endswith(harness_verdict_name())
    ]
    assert len(named) == 1, (
        "the run has to NAME the path it wrote on stdout; it printed: " + proc.stdout
    )
    return proc.stdout, Path(named[0])


def harness_verdict_name() -> str:
    """The artifact's file name, read off the run rather than written here twice."""
    from codegen.__main__ import VERDICTS

    return VERDICTS


def test_the_run_writes_a_verdict_row_for_the_pair_it_graded(tmp_path: Path) -> None:
    """The command a reviewer types leaves a table, at the path it printed.

    The whole of obligation 1.  Read back off the path the run named, so a run that wrote
    a file and printed nothing fails here too: a path nobody is told is a path nobody
    diffs.
    """
    stdout, path = _run(tmp_path)
    assert path.exists(), f"the run named {path} and wrote nothing there; stdout: {stdout}"
    text = path.read_text()
    rows = [line for line in text.splitlines() if not line.startswith("#")]
    header, body = rows[0], rows[1:]
    assert header.split("\t")[0] == "document", header
    assert len(body) == 1, body
    cells = dict(
        cell.split("=", 1) for cell in body[0].split("\t") if "=" in cell and " " not in cell
    )
    assert body[0].split("\t")[0] == DOCUMENT, body[0]
    # The four checks §10 names, each with a verdict of its own.  Asserted as a SET so the
    # column order is free and a check added later arrives here rather than passing.
    assert set(harness.CHECKS) <= set(cells), sorted(cells)
    assert cells["accepts"] == "pass" and cells["dump"] == "pass", body[0]
    assert cells["refuses"] == "pass", body[0]
    assert cells["verdict"] == "pass", body[0]
    # Which run paid for the evidence, which is §10's other half of the row.
    assert cells["evidence"] in ("drawn", "replayed", "mixed"), body[0]
    assert cells["examples"].isdigit() and int(cells["examples"]) >= 1, body[0]


def test_a_verdict_that_was_never_computed_reads_as_neither_pass_nor_fail() -> None:
    """Obligation 2, on the three states a cell can take.

    A pair that reached no check -- the pairing raised building it, which four pairs of
    this bundle do -- has to produce a ROW with a cause, because a pair missing from the
    table is the blank column one level up.  And its cells must be readable as neither a
    pass nor a failure of the class: ``absent`` says the obligation was never put to the
    pair, which is a fact about the instrument.

    The three rows are compared as TEXT, which is what a reviewer greps and what a diff
    reads.  A reader asking "every pair that fails dump" must not be answered with a pair
    nothing asked, and a reader asking "every pair that passes" must not be answered with
    it either.
    """
    ref = SchemaRef("core/pagination-request.json", "#")
    never = harness.verdict_row(ref, None, model="X", error="pairing: KeyError: '0'")
    for check in harness.CHECKS:
        assert f"{check}={harness.ABSENT}" in never, (check, never)
        assert f"{check}={harness.PASS}" not in never, (check, never)
        assert f"{check}={harness.FAIL}" not in never, (check, never)
    # The CAUSE travels with the row, so the blank column names what produced it.
    assert "KeyError" in never, never
    # And the three states are three distinct tokens, asserted against each other rather
    # than by inspection: a rename that collapsed two of them would pass every assertion
    # above and make the artifact unreadable.  Pairwise and not as a count, because a count
    # of distinct names is a census and this is three statements about three names.
    assert harness.PASS != harness.FAIL != harness.ABSENT != harness.PASS
    # And no token is a PREFIX of another, which is what makes a reader's grep for one
    # state unable to match a different one.
    for state in (harness.FAIL, harness.ABSENT):
        assert not state.startswith(harness.PASS) and not harness.PASS.startswith(state)


def test_the_table_counts_absent_cells_apart_from_passing_ones() -> None:
    """The preamble a reader meets first partitions the cells three ways, not two.

    A summary with two columns is the instrument ``adcp-client-python-82m.4`` is about: it
    reported two never-run checks as successes.  So the table's own header is asserted to
    carry three figures per check, and the row that was never graded is asserted to land
    in the third.
    """
    ref = SchemaRef("core/pagination-request.json", "#")
    graded = harness.verdict_row(
        ref,
        harness.PairReport(
            name="p",
            accepts=harness.AcceptsResult(examples=1, outcome="pass", round_tripped=1),
            liveness=harness.LivenessResult(outcome="pass", how="x"),
        ),
        model="Graded",
    )
    never = harness.verdict_row(ref, None, model="Never", error="pairing: KeyError")
    table = harness.verdict_table([graded, never])
    preamble = [line for line in table.splitlines() if line.startswith("#")]
    counts = next(line for line in preamble if "(pass/fail/absent)" in line)
    # One pass, no failure and one absent for each of the two checks the graded row ran.
    assert "accepts 1/0/1" in counts, counts
    assert "dump 1/0/1" in counts, counts
    assert "refuses 1/0/1" in counts, counts
    # And the file says, in the file, what the third state means -- so a reader who greps
    # the artifact out of context cannot read a blank as a pass.
    assert any("absent is NOT a pass" in line for line in preamble), preamble
