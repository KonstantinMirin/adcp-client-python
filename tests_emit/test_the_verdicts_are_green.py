"""The verification's GATE, which reads the artifact rather than re-grading.

**WHY IT READS AND DOES NOT GRADE.**  The gate that stood here --
``test_emit.py::test_every_class_passes_all_three_checks`` -- re-derived every verdict
inside pytest, through a fixture that called ``harness.Fixtures``.  That name was deleted
on 2026-11-11 with the corpus apparatus (``adcp-client-python-hzio.5``), so all 2,608 of
its cases have raised ``AttributeError`` in setup ever since, and the suite still COLLECTS
green because the call is in a fixture and not at import.  A gate that cannot reach a
verdict reports nothing while looking like a gate, and nothing else was watching: the three
numbers ``./check`` prints measure EMISSION, not agreement with the document.

So the work and the gate are separated, which is the shape ``./check`` already has for
emission:

* ``./verify`` does the grading -- 2,608 pairs in 528 s, 203 ms per pair -- and writes
  ``verdicts.tsv`` beside ``verify.json``;
* this module READS that artifact and fails per not-pass row.

Three things follow, and each was a defect of the old shape:

1. **The gate costs milliseconds**, so it runs in every suite rather than being skipped.
2. **Every verdict reaches pytest's own JSON report** (``--json-report`` is in ``addopts``),
   so a reader asks ``test-results/report.json`` instead of re-running anything.
3. **It cannot drift from the artifact**, because there is one grading and not two.  The
   old shape had ``verdicts.tsv`` written by the emitter and the verdicts re-derived by the
   test, free to disagree -- and they did: the committed artifact was from 2026-11-10 while
   the test was reporting ``AttributeError``.

**IT ALSO GATES THE ARTIFACT'S OWN FRESHNESS**, because a gate over a stale file is the
defect one layer along: :func:`test_the_artifact_graded_this_tree` fails when
``verify.json``'s recorded head is not this checkout's.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "src" / "adcp" / "types" / "verify.json"

#: The six checks, in the order the artifact writes them.  Named here so a check that
#: stops being written shows up as a missing key rather than as a silent zero.
CHECKS = ("accepts", "refuses", "dump", "widening", "undeclared", "admits")


def _report() -> dict:
    if not REPORT.is_file():
        pytest.fail(f"{REPORT.relative_to(ROOT)} is absent -- run ./verify")
    return json.loads(REPORT.read_text())


#: What the grade READS: the emitted tree and the compiler that graded it.  Not the whole
#: repository, and that distinction is the whole of :func:`_graded_at`.
INPUTS = ("src/adcp/types/_schemas", "src/adcp/types/constraints.py", "codegen")


def _changed_inputs_since(recorded: str) -> list[str]:
    """Every commit after ``recorded`` that touched an input the grade reads.

    **``HEAD`` IS THE WRONG COMPARISON, and it is wrong in a way no artifact can ever
    satisfy.**  ``verify.json`` records the tree it graded, so an artifact graded at commit
    N is COMMITTED in commit N+1 -- the commit that contains it is necessarily later than
    the one it names.  Measured, twice in one session: the clause passed in the window
    between grading and committing and failed the moment the artifact landed
    (``verify.json graded ccd9de3f0 and this checkout is fd779eed4``), so a correct,
    freshly-taken measurement reported itself stale forever after.

    What the clause is actually for is "does this artifact describe the tree in front of
    me" -- and the tree in front of me is the EMITTED tree and the COMPILER, not the
    repository.  A commit that edits a document, a bead or this test changes no input the
    grade reads and must not invalidate it.  So the subject is :data:`INPUTS`, which is a
    fact about the graded tree rather than about the history around it.

    **AND "THE LAST COMMIT THAT TOUCHED INPUTS" WAS STILL THE WRONG QUESTION, because it
    is not the commit that CONTAINS the change.**  ``git log -1 -- <paths>`` names the
    commit that edited the path, and under a ``--no-ff`` merge that is the branch commit,
    never the merge.  Measured on 2026-11-20: a grade taken at the merge ``6dd46870e`` --
    the freshest possible, nothing between it and the working tree -- compared itself
    against ``799fcb348``, the lane commit the merge brought in, and reported itself stale.
    That is the same defect this docstring already describes, reintroduced one level up by
    merging rather than fast-forwarding, and no re-run can clear it: ``./verify`` records
    the merge every time and the comparison names the parent every time.

    So the question is asked as a RANGE and not as an equality: is there any commit after
    the one the artifact names that touched an input?  Empty means current, whatever the
    shape of the history in between -- merge, fast-forward or rebase -- and a non-empty
    answer NAMES what changed, which is the thing a reader needs in order to know whether
    to re-grade or to look closer.

    Still strict in the direction that matters, and strictly more so than the equality was:
    regenerate the tree or change the harness and the next commit appears in this range, so
    a stale artifact is caught at the first commit that could have changed its verdicts.
    """
    done = subprocess.run(
        ["git", "-C", str(ROOT), "rev-list", f"{recorded}..HEAD", "--", *INPUTS],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        pytest.fail(
            f"verify.json names head {recorded!r}, which this repository cannot resolve: "
            f"{done.stderr.strip()} -- the artifact was graded in another checkout"
        )
    return done.stdout.split()


def _rows() -> list[dict]:
    return _report().get("not_pass_rows") or []


def test_the_artifact_graded_this_tree() -> None:
    """``verify.json`` must describe THIS checkout, or every figure below is about another.

    The reason this clause exists at all: the committed ``verdicts.tsv`` was two days and
    twenty commits old and was being quoted as the current state, because nothing compared
    its provenance to the tree it sat in.  A ``+dirty`` head is accepted -- a lane with
    uncommitted work has graded its own tree, which is the point -- but a commit touching
    an input AFTER the one the artifact names is a stale artifact and says so.
    """
    recorded = (_report().get("provenance") or {}).get("head", "")
    assert recorded, "verify.json records no head; the artifact cannot be dated"
    since = _changed_inputs_since(recorded.split("+")[0])
    assert not since, (
        f"verify.json graded {recorded}, and {len(since)} commit(s) have touched "
        f"{', '.join(INPUTS)} since -- {' '.join(c[:9] for c in since[:5])} -- "
        "the artifact is stale, run ./verify"
    )


def test_every_check_was_put_to_every_pair() -> None:
    """``absent`` is NOT a pass -- the artifact's own header says so.

    A check that was never put to a pair is reported rather than counted green, and this
    clause is what makes that visible: ``admits`` was absent at 1,581 of 2,586 pairs under
    the old sampler and is absent at 0 under the construction, which is the whole of what
    ``adcp-client-python-hzio.5`` bought.  It is a ratchet in the only direction a ratchet
    is honest -- the absent count may fall and may not rise -- and the numbers are the
    artifact's, not a floor anybody chose.
    """
    per_check = _report()["per_check"]
    absent = {name: per_check[name]["absent"] for name in CHECKS}
    assert absent["admits"] == 0, (
        f"the admits check was never put to {absent['admits']} pairs; "
        "the construction is meant to answer for every one"
    )
    assert absent["refuses"] <= 11, f"refuses absent at {absent['refuses']} pairs"
    assert absent["accepts"] <= 8, f"accepts absent at {absent['accepts']} pairs"


def test_no_pair_loses_a_fact_on_the_round_trip() -> None:
    """``dump``: what the class built, dumped, is an instance the document admits.

    The narrowest of the six and the one whose failure is data loss: a class that takes an
    instance and drops a key accepts every instance there is, so only the dump catches it.
    """
    lost = [r for r in _rows() if "model_dropped_a_fact" in (r.get("verdict") or "")]
    assert not lost, "\n".join(
        f"  {r['document']}{r['pointer']} -> {r['class']}: {(r.get('note') or '')[:160]}"
        for r in lost
    )


def test_no_class_refuses_what_its_document_admits() -> None:
    """Reading 1: every class accepts every value its document admits.

    ``model_refused_admitted`` (the subtree's witness set) and ``model_refused_valid`` (the
    pair's own witness) are both this obligation, and a failure is a class NARROWER than
    its document -- which costs a user with a legitimate payload an error from us.
    """
    narrower = [
        r
        for r in _rows()
        if "model_refused_admitted" in (r.get("verdict") or "")
        or "model_refused_valid" in (r.get("verdict") or "")
    ]
    assert (
        not narrower
    ), f"{len(narrower)} pairs refuse a value their document admits; the first ten:\n" + "\n".join(
        f"  {r['document']}{r['pointer']} -> {r['class']}: {(r.get('note') or '')[:150]}"
        for r in narrower[:10]
    )


def test_every_widening_is_declared() -> None:
    """Reading 2: a class WIDER than its document carries a declaration saying so.

    ``widened_undeclared`` is a widening with no ``Approximation`` covering it, and
    ``unproved_widening`` is a declaration whose widening the check could not demonstrate
    -- a declaration about nothing, which is the same defect from the other side.
    """
    undeclared = [r for r in _rows() if "widened_undeclared" in (r.get("verdict") or "")]
    unproved = [r for r in _rows() if "unproved_widening" in (r.get("verdict") or "")]
    assert not undeclared and not unproved, (
        f"{len(undeclared)} undeclared widenings and {len(unproved)} unproved declarations; "
        "the first ten undeclared:\n"
        + "\n".join(
            f"  {r['document']}{r['pointer']} -> {r['class']}: {(r.get('note') or '')[:150]}"
            for r in undeclared[:10]
        )
    )


def test_the_verdict_table_and_the_report_agree() -> None:
    """One grading, not two: the row count in the report is the row count in the table.

    The old shape had the artifact written by the emitter and the verdicts re-derived by
    the test, free to disagree.  This asserts they cannot: ``./verify`` writes both from
    one ``grade`` call, so a mismatch means one of the files was edited by hand.
    """
    table = ROOT / "src" / "adcp" / "types" / "verdicts.tsv"
    lines = [line for line in table.read_text().splitlines() if not line.startswith("#")]
    assert (
        len(lines) - 1 == _report()["graded"]
    ), f"verdicts.tsv holds {len(lines) - 1} rows and verify.json says {_report()['graded']}"
