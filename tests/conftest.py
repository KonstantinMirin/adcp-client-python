"""Suite-wide options, where the suite's SCRATCH goes, the binding that decides WHICH
TREE is graded, and the one assertion every file that grades a refusal shares.

:data:`SCRATCH` is first in the file because it has to be first in the PROCESS: it moves
every temporary directory this suite writes off ``/tmp``, which on this box is a 63 GB
tmpfs, and ``tempfile`` memoises the location on first use.  ``docs/plan/architecture.md``
("The suite's scratch goes on DISK, not in RAM", 2026-10-30) decides it;
``tests/test_scratch_is_on_disk.py`` reads it back off ``/proc/mounts``, so a suite whose
scratch returns to RAM fails a named test rather than a worker the kernel killed.

:func:`pytest_sessionstart` is not a convenience import.  ``docs/plan/architecture.md``
(2026-10-29) decides that "grading reads the tree a fresh run emits; the committed tree is
an ARTIFACT, verified by one byte-compare, and is never the subject", and importing
``tests/fresh.py`` IS the act: it materialises the generated half of ``adcp.types`` from a
fresh compile and puts it in front of ``src/adcp/types`` on ``adcp.types.__path__``.  It
has to happen HERE because a process has one ``adcp.types.constraints``: the first import
of the generated half binds it for the life of the interpreter, so the binding has to
precede every test module, and a root ``conftest`` is the only thing pytest runs before
collection.  ``tests/fresh.py`` asserts that nothing beat it to it rather than grading
whatever it finds.

:func:`refusal_from` is at the bottom: §14 step 6 makes a refusal a VALUE, so a test that
used to write ``pytest.raises(Refusal)`` reads the value a call returned, and this is the
one spelling of that for the whole suite.

One option, and it exists because the generated half of ``docs/plan/rebuild-plan.md``
is a TEST artifact (``docs/plan/architecture.md`` §3): the grids of sections 5, 6 and 7
are generated from ``codegen/keywords.py`` by ``tests/test_keywords.py``, which asserts
the committed document equals what the table generates.  ``--write-grids`` is the
affordance for a cell that has deliberately changed -- it writes the marked regions and
nothing else, so writing a cell change through to the document costs one flag rather
than a hand edit nobody can verify.

Here rather than in the test module because pytest collects options from a plugin or a
root ``conftest``, and a test module declaring one is not read in time.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from codegen.refusal import Refusal

REPO = Path(__file__).resolve().parents[1]

#: **Where every temporary directory this suite writes goes, and it is a DISK path.**
#:
#: ``docs/plan/architecture.md`` ("The suite's scratch goes on DISK, not in RAM",
#: 2026-10-30): ``/tmp`` on this box is a 63 GB TMPFS, the suite materialises a fresh
#: ``adcp`` package per ``tmp_path`` at 841 MB -- 836 MB of it the resolved JSON a
#: document's ``strict_validate`` reads through ``importlib.resources`` -- and at ten
#: workers that lands in RAM.  Available memory reached 3.1 GB of 125 during a full run
#: and two attempts at the full-suite wall clock died of worker OOM rather than of
#: anything in the code.  ``tests/test_scratch_is_on_disk.py`` is the reading.
#:
#: **BESIDE THE CHECKOUT, which is the same rule ``tests/compiled.py``'s store follows
#: and for a reason neither of them invented.**  ``REPO.parent`` is on the filesystem the
#: checkout itself is on, by construction -- so the path is a disk path wherever the
#: repository is cloned, and not because ``/srv/ws`` was hardcoded.  Per worktree
#: (``/ REPO.name``), because pytest clears a basetemp it is handed and lanes of one epic
#: share one ``pyproject.toml``: a path that did not carry the worktree's name would have
#: one lane's run delete another's live scratch.  Outside the checkout rather than in it,
#: so no run can leave an 841 MB generated package where ``git add`` reaches it, and
#: ``.gitignore`` carries ``.adcp-scratch`` as the second defence for the case
#: ``ADCP_SCRATCH`` points one back inside -- the shape
#: ``tests/test_accepts_corpus.py::test_the_store_is_a_build_artifact_and_not_a_committed_one``
#: already states for the corpus.
#:
#: **DISK HEADROOM, and the honest version of it rather than a reassuring one.**  Measured
#: 2026-10-30: ``/`` is 1.8 TB and went from **135 GB free at 92% to 96 GB free at 95%
#: across the nine hours this row took**, so the margin is not large and it is not static.
#: What this directory contributes is nonetheless bounded, and bounded by pytest rather
#: than by hope:
#: an un-given ``--basetemp`` is a NUMBERED directory under
#: ``<scratch>/pytest-of-<user>/`` and ``make_numbered_dir_with_cleanup`` keeps THREE, so
#: one worktree's steady state is the three most recent runs.  One run's basetemp is
#: **835,456 kB** (``du -sk``, one full ``tmp_path`` package), so ~2.4 GB per worktree, two
#: orders off the headroom and self-limiting with no prune of our own -- read back after
#: three runs of this suite, this whole directory was **560 kB**, because keep-3 had already
#: reclaimed the package.
#:
#: What moved the 135 GB to 96 GB is NOT this: it is the compile store beside it, which has
#: no prune at all (``bd`` row ``adcp-client-python-q3a``) -- pruned to 23 GB that morning
#: and **51 GB** by that evening, where ``tests/fresh.py``'s tree store next to it is pruned
#: at twelve hours.  A reader deciding whether this path is still safe should read THAT
#: store's size, not this one's.
#:
#: The one unbounded part here is the SEVEN bare ``tempfile.mkdtemp()`` calls in this
#: suite, none of which removes what it made: 31 such directories holding 818 MB were in
#: the tmpfs when this was written.  They now accumulate on disk, where 818 MB is nothing
#: and where it is no longer 818 MB that ten workers compete with the kernel for.
SCRATCH = Path(os.environ.get("ADCP_SCRATCH") or REPO.parent / ".adcp-scratch") / REPO.name

#: **The relocation, at MODULE SCOPE and not in a hook, because the variable has to be
#: set before anything READS it and ``tempfile`` caches.**
#:
#: ``tempfile.gettempdir()`` memoises its answer in ``tempfile.tempdir`` on first call, so
#: a ``pytest_configure`` that set only the environment variable would be overridden by
#: whatever asked first -- a plugin, or ``_pytest.tmpdir`` itself.  Both are set: the
#: module global for this interpreter, and ``TMPDIR`` for the CHILD processes
#: ``tests/test_the_tree_imports.py`` spawns over a fresh package with
#: ``env={**os.environ, ...}``.  A root ``conftest`` is imported before collection and
#: separately in every xdist worker, which is every interpreter that writes scratch.
#:
#: **pytest's ``--basetemp`` is pointed here DERIVED rather than written as a literal,
#: and the difference is not cosmetic.**  ``_pytest.tmpdir`` roots an un-given basetemp at
#: ``tempfile.gettempdir()``, so this IS the ``--basetemp`` the decision asks for -- while
#: a basetemp given EXPLICITLY is ``rm_rf``'d at session start.  A literal in
#: ``[tool.pytest.ini_options]`` is one string shared by every worktree of this
#: repository, so a lane running one test file would delete the scratch of a full run in
#: flight beside it, and the per-run numbered directory and its keep-3 cleanup would be
#: given up for it.  A derived basetemp keeps both.
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ["TMPDIR"] = str(SCRATCH)
tempfile.tempdir = str(SCRATCH)


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session) -> None:
    """Bind the generated half of ``adcp.types`` to the tree a fresh run emits.

    **The window, and both of its edges are load-bearing.**  It has to be before
    COLLECTION, because every test module is imported there and the first import of the
    generated half binds it for the life of the interpreter -- ``tests/fresh.py`` asserts
    that nothing beat it to it rather than grading whatever it finds.  And it has to be
    after hypothesis's own ``pytest_sessionstart``, because ``fresh`` reaches
    ``codegen.emit`` -> ``codegen.harness`` -> ``hypothesis``, and hypothesis warns
    (``HypothesisSideeffectWarning``) when its unicode charmap is built while its
    ``in_initialization`` counter is up, which it clears in that hook.  ``trylast`` is
    what orders the two; the warning is correct about the cost and is not suppressed.

    Run in each xdist worker as well as in the session process, because each is its own
    interpreter with its own ``adcp.types``.
    """
    import fresh  # noqa: PLC0415 -- deferred on purpose; see above


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--write-grids",
        action="store_true",
        default=False,
        help="rewrite the generated grids of docs/plan/rebuild-plan.md from "
        "codegen/keywords.py (tests/test_keywords.py owns the regions)",
    )


def refusal_from(outcome: object) -> Refusal:
    """The refusal a call RETURNED, asserted to be one and narrowed to it.

    **The shape ``pytest.raises(Refusal)`` had before §14 step 6.**  A refusal is a
    VALUE now (``docs/plan/architecture.md`` §2), so a test that used to catch one reads
    one: the call returns, and what it returns is a ``Decided | Refusal`` or a
    ``str | Refusal``.  This is the one spelling of "it refused, and here is the
    refusal" for the whole suite, so eighteen call sites do not each write their own.

    Here rather than in a test module because every file that needs it is a sibling of
    this one, and here rather than in ``populations.py`` because that module is the
    document SETS a step's result was stated over (§5) and this is an assertion.

    The ``assert isinstance`` IS the test's claim and not a branch standing in for a
    refusal's handling: the production rule §14 step 6 states is about the decision
    layer, which ``[tool.mypy]`` in ``pyproject.toml`` ranges over and this file is not
    in.  A test asserting that a call refused has to say so somehow, and saying it with
    the type is what also narrows the value for the assertions that follow.
    """
    assert isinstance(outcome, Refusal), f"expected a refusal, got {outcome!r}"
    return outcome
