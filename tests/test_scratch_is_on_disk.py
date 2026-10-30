"""Every scratch directory this suite writes lands on DISK, and this is the reading.

``docs/plan/architecture.md`` ("The suite's scratch goes on DISK, not in RAM",
2026-10-30):

    ``/tmp`` on this machine is a **63 GB tmpfs -- it is RAM.**  The suite materialises a
    fresh package per ``tmp_path``, the tree is 841 MB of which 836 MB is the resolved
    JSON read through ``importlib.resources``, and at ten workers that lands in memory.
    [...] **So ``TMPDIR`` and pytest's ``--basetemp`` point at disk.**

**WHY A TEST AND NOT A SETTING.**  The relocation is three lines in ``tests/conftest.py``
and nothing about those three lines is visible in a green run: a suite whose scratch is
back in RAM passes every other check in this directory and fails only as a worker the
kernel killed, which arrives as a truncated run with no verdict attached to it.  Two of
the three attempts at this project's full-suite wall clock died that way, and the reason
was read off ``free`` afterwards rather than off any mark.  So the property is asserted
where a failure is a named red test: BEFORE the run that would OOM, not after.

**WHAT MAKES IT A REAL GATE.**  The assertion is over the filesystem ``/proc/mounts``
reports for the path, not over the path's spelling -- a check that the string is not
``/tmp`` would pass on a box that mounts a tmpfs anywhere else, and the hazard is the
mount and never the name.  On the unmodified suite the three readings below are ``/tmp``
and the test is RED with ``tmpfs`` in its message; that is the state it was written in.

Three readings and not one, because the suite reaches a temporary directory by three
routes and they are configured by two different mechanisms:

* ``tempfile.gettempdir()`` -- the seven bare ``tempfile.mkdtemp()`` calls in
  ``tests/test_emit.py``, ``test_union_disjointness.py``, ``test_ref_branch_union.py``
  and ``test_nested_union_sibling.py``, none of which removes what it made.  Measured
  while this row ran: 31 such directories left in the tmpfs holding 818 MB;
* ``TMPDIR`` -- what a CHILD process inherits.  ``tests/test_the_tree_imports.py`` runs
  ``tests/_imports_a_tree.py`` as a subprocess over a fresh package, and a child that
  reads the variable rather than our ``tempfile.tempdir`` is the half a module-level
  assignment alone would miss;
* ``tmp_path`` -- pytest's own, which is ``<basetemp>/<test name><N>`` and which
  ``_a_fresh_package`` writes the 841 MB package into.  This is the big one and it is
  derived from the other two (``_pytest.tmpdir`` roots an un-given basetemp at
  ``tempfile.gettempdir()``), so asserting it is what says the derivation held.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from conftest import SCRATCH

REPO = Path(__file__).resolve().parents[1]

#: Filesystems whose pages ARE the page cache: a byte written to one is a byte of RAM
#: that no eviction reclaims and that counts against every worker at once.  ``tmpfs`` is
#: the one this box mounts ``/tmp`` with; the other three are listed because the property
#: being asserted is "not memory-backed" and a reader meeting ``ramfs`` here should not
#: have to ask whether it was overlooked.  Not a census -- a predicate's domain.
IN_MEMORY = frozenset({"tmpfs", "ramfs", "devtmpfs", "hugetlbfs"})


def filesystem_of(path: Path) -> tuple[str, str]:
    """``(mount point, fstype)`` for the mount ``path`` lives on, off ``/proc/mounts``.

    The LONGEST mount point that is a prefix of the path, because mount points nest:
    ``/`` is a prefix of every path on the box and would answer ``ext4`` for a file in a
    tmpfs mounted under it, which is the exact mistake that makes this instrument useless.

    Resolved first, so a symlink into a tmpfs is read as the tmpfs it reaches.  The path
    need not exist: ``Path.resolve`` is non-strict, and the mount a directory WOULD be
    created in is the one the question is about.
    """
    path = path.resolve()
    where, kind = Path("/"), "unknown"
    for line in Path("/proc/mounts").read_text().splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        # ``/proc/mounts`` octal-escapes a space, a tab and a backslash in the mount
        # point.  Decoded rather than skipped, so a mount under a path with a space in it
        # is compared and not silently dropped to ``/``.
        at = Path(fields[1].encode().decode("unicode_escape"))
        if path.is_relative_to(at) and len(at.parts) >= len(where.parts):
            where, kind = at, fields[2]
    return str(where), kind


def test_no_route_to_a_temporary_directory_lands_in_memory(tmp_path: Path) -> None:
    """The three routes, each asserted against the filesystem it actually reaches.

    The message carries the mount point and the fstype because that is what a reader
    needs to act: "``/tmp`` is tmpfs" names the thing to change, where "scratch is in
    RAM" names only the symptom.
    """
    for route, path in (
        ("tempfile.gettempdir()", Path(tempfile.gettempdir())),
        ("TMPDIR", Path(os.environ.get("TMPDIR", tempfile.gettempdir()))),
        ("pytest's tmp_path", tmp_path),
    ):
        where, kind = filesystem_of(path)
        assert kind not in IN_MEMORY, (
            f"{route} is {path}, which is on {where} ({kind}) -- a memory-backed "
            f"filesystem. A fresh package is 841 MB and ten workers write their own, so "
            f"this is the OOM that killed two attempts at the full-suite wall clock. "
            f"tests/conftest.py's SCRATCH is what points all three at disk."
        )


def test_the_scratch_directory_is_outside_the_checkout_and_ignored_by_name() -> None:
    """The two defences ``tests/corpus.py``'s store already carries, for the same reason.

    ``tests/test_accepts_corpus.py::test_the_store_is_a_build_artifact_and_not_a_committed_one``
    states the shape: the primary claim is that no run writes inside this repository, and
    the ``.gitignore`` half is still graded because the location is OVERRIDABLE --
    ``ADCP_SCRATCH`` can point the scratch back inside a checkout, and the name is then
    the only thing keeping 841 MB of generated package out of a commit.

    Graded here rather than beside the corpus store's because what is ignored is a
    different name, and a test that asserted both would report one defect for two.
    """
    assert not SCRATCH.is_relative_to(REPO), (
        f"the suite writes its scratch inside the checkout: {SCRATCH}"
    )
    #: What ``ADCP_SCRATCH`` names -- the directory a scratch pointed back inside a
    #: checkout would be rooted at, which is therefore the name ``.gitignore`` must carry.
    name = SCRATCH.parent.name
    ignored = {line.strip().rstrip("/") for line in (REPO / ".gitignore").read_text().splitlines()}
    assert name in ignored, name
    done = subprocess.run(
        ["git", "check-ignore", "-q", f"{name}/x"], cwd=REPO, capture_output=True, check=False
    )
    assert done.returncode == 0, "git does not ignore a scratch directory inside the checkout"
