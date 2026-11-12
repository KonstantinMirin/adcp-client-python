"""The drop-in tree, REBUILT from this repository and upstream's wheel -- §8a's regeneration.

    python -m survey regenerate --wheel <site-packages> --out <dir>

**WHY THIS EXISTS.**  ``docs/plan/architecture.md`` §8a rules that the tree which measures us
against upstream's behavioural suite "is regenerated from this repository and never edited
directly.  It is an instrument, not a branch."  That ruling was unexecutable: four trees
(``dropin/9.6-b``, ``sdk/moveit-drop``, ``sdk/close-drop``, ``sdk/gap``/``sdk/jgsf``) were
built BY HAND, each one merging trunk forward and carrying its own edits, and there was no
command anywhere in ``survey/`` or ``tools/parity/`` that could re-derive one.  So the figure
those trees reported -- 12,147 passed of 15,628 collected against upstream's 13,545 -- could
be quoted and could not be reproduced, which is the one property §8a exists to guarantee.

**WHAT IT PRODUCES, AND FROM WHAT.**  Two inputs and nothing else:

* **upstream's installed WHEEL** -- their machinery, byte for byte, verified against the
  ``RECORD`` their installer wrote.  Reading 8 says the wheel is the artifact; a worktree
  source tree with an editable ``.pth`` is not upstream and this command refuses one.
* **this repository** -- our types, emitted FRESH by ``python -m codegen`` (§2: "the subject
  of grading is a FRESH EMIT, never the committed tree"), plus the three hand-written
  modules beside them, plus the alias layer in ``survey/dropin/``.

Upstream's *repository-only* files -- their 577 behavioural test files, their conftest, their
compliance test vectors, their ``pyproject.toml``'s pytest configuration -- are not in the
wheel, and they come from the git revision the wheel was BUILT FROM, which is identified by
measurement: ``--rev``'s ``src/adcp/**`` is compared byte for byte against the wheel's
``adcp/**`` and a single disagreement refuses the build.  On ``v9.6.1`` the overlap is 2,166
files and **0 differ**, so "the suite from the revision" and "the suite from the wheel" are
the same suite and the claim needs no trust.

**THE FOUR THINGS §8a REQUIRES, in the order this file does them:**

1. :func:`verify_wheel` -- start from upstream's real wheel, and say how it was verified.
1b. :func:`lay_our_machinery` -- our ``src/adcp/`` over the wheel's, except ``types/``,
   with the differing modules NAMED.  What is graded is the package this repository ships
   and not a chimera of their machinery and our types: a lane's nine repairs to
   ``webhooks.py`` and ``feed_mirror.py`` moved the suite by zero tests while the tree
   executed upstream's copies of both.
2. :func:`strip_their_types` -- delete their types and their generator; KEEP their
   machinery.  The split is not a list: their 1,088 ``domains/**`` modules and 8
   ``versioned_bases/`` go, their 40 hand-written package-root modules stay.
   ``error_narrowing.narrow_union_errors`` is a FUNCTION and machinery; deleting it cost
   1,350 tests once (``verdicts/dropin-modules.md`` §2).
3. :func:`substitute_ours` and :func:`alias_layer` -- our emitted tree, and the layer that serves
   upstream's own module paths and flat spellings out of it.
4. :func:`manifest` -- a digest over every file written, beside the digests of both inputs.
   Two runs on one trunk produce one digest; that is what makes the measurement re-derivable
   rather than remembered.

**AND OUR TESTS ARE NOT SHIPPED INTO IT, which is §8a correcting the hand-built trees.**
Those trees renamed trunk's ``tests/`` to ``emit_checks/`` so upstream's could take the name,
and left 25 files importing ``tests.nodeset``, ``codegen/held.py`` pointing at a directory
that had moved, and ``./check`` raising before printing a figure
(``verdicts/jgsf.md`` §4 -- the suite that grades readings 1 to 9 had been grading NOTHING on
that branch).  §8a's answer is not to repair the rename: our gates run HERE, over our own
tree, and the drop-in grades upstream's suite and nothing else.  So no ``tests/`` of ours,
no ``codegen/``, no ``schemas/`` of ours enters the output, and the collision cannot arise.

**NOTHING IN THE OUTPUT IS AUTHORED.**  Every file in it is one of: the wheel's bytes;
upstream's revision's bytes; the wheel's or revision's bytes with ONE declared 645-byte
marker appended (:data:`MACHINERY_MARKER`); the compiler's fresh output; or a file of this
repository copied in.  :func:`audit` is the same partition read backwards over a tree that
already exists, and it is how the hand-built trees' own edits were found: 46 of upstream's
files edited, 130 alias statements, and a module layer that lived nowhere else.
"""

from __future__ import annotations

import argparse
import ast
import base64
import collections
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Where ``survey/dropin/`` holds the parts of the drop-in that are OURS and that §8a says
#: belong in this repository: the module layer, the declared population, the partition.
PAYLOAD = Path(__file__).resolve().parent / "dropin"

#: Upstream's distribution name and the one version this instrument is written against.
#: A version is an ARGUMENT nowhere here on purpose: the alias layer, the member-spelling
#: derivation and the 104-file declaration were all read off 9.6.1, so a different wheel is
#: a different measurement and must say so rather than silently reuse this one's data.
DIST = "adcp"
VERSION = "9.6.1"

#: The git revision upstream's 9.6.1 wheel was built from.  **Not trusted -- CHECKED**: see
#: :func:`verify_revision`, which compares every file the two share.
REV = "v9.6.1"

#: What upstream's generator wrote and we replace.  Paths under ``src/adcp/types/``.
THEIR_GENERATED = ("domains", "versioned_bases")

#: Their generator's entry points, which have no input in this tree -- the bundle they read
#: is not the bundle we compile and ``datamodel-code-generator`` is removed with them.
#: Derived from the revision rather than listed: every ``scripts/*.py`` whose module docstring
#: or body names ``datamodel_code_generator``, plus the manifest they share.
THEIR_GENERATOR_MANIFEST = "scripts/post_generation_manifest.json"

#: The one thing appended to a kept module of upstream's, and the only edit this instrument
#: makes to any byte of theirs.  ``_dropin._kept_machinery`` reads it as TEXT to decide which
#: modules host a flat spelling, so the rule is declared by each module rather than listed in
#: a script -- ``survey/alias_surface.MODULE_MARKER``'s pattern one layer along.
MACHINERY_MARKER = '''

#: **DECLARED BY THE MODULE AND NOT LISTED IN A SCRIPT** -- the pattern
#: `survey/alias_surface.MODULE_MARKER` already uses for `__adcp_restates_upstream__`.
#: This file is upstream adcp 9.6.1's own hand-written MACHINERY, kept because its names are
#: functions, base classes and constants that no document states and that their behavioural
#: tests exercise behaviour through.  `adcp.types._dropin` resolves a FLAT spelling through
#: the modules carrying this attribute, because upstream's flat namespace carried everything
#: its package-root modules declared.  Nothing here is a type of ours.
__adcp_upstream_machinery__ = "adcp 9.6.1"
'''

#: The three modules of ours that the compiler does not write and that the substitution needs:
#: ``__init__.py`` is §1's surface, ``_base.py`` and ``_runtime.py`` are the hand-written
#: base the emitted modules import, and ``compat.py`` is generated HERE by
#: ``survey/alias_surface.py`` from upstream's wheel and committed as that run's artifact.
OURS_BESIDE_THE_EMIT = ("__init__.py", "_base.py", "_runtime.py", "compat.py")

#: Appended to OUR ``adcp/types/__init__.py`` in the output, and nowhere else.  The finder has
#: to be installed before the first ``import adcp.types.<one of their paths>``, which may be
#: the first thing upstream's own code does; and it is ``import_module`` and not
#: ``from . import _dropin`` because the latter asks the PARENT for the attribute, enters the
#: flat ``__getattr__`` above it and binds every domain module before the finder exists --
#: measured at 3,216 of upstream's tests failing on ``adcp.types.core.TaskResult``
#: (``verdicts/dropin-modules.md`` §4.2).
TYPES_INIT_TAIL = '''

# **READING 10's ALIAS LAYER AT MODULE GRANULARITY, ACTIVATED LAST.**  ``_dropin`` serves the
# MODULE PATHS upstream's own code imports its types from, and chains the ``__getattr__``
# above so a flat name upstream's kept machinery declares resolves too.  It declares nothing,
# so reading 6 is unmoved.  It is imported HERE, at the end, for two reasons: the chain needs
# the function above to exist, and a finder has to be in place before the first
# ``import adcp.types.<one of their paths>`` -- which may be the first thing an application
# does, and which cannot happen before this module's body finishes.
# **AND IT IS `import_module` RATHER THAN `from . import _dropin`, which is not a style.**
# MEASURED: `from . import X` asks the PARENT for the attribute first, so it enters the
# `__getattr__` above, which routes an unknown name to the alias module -- importing
# `compat` and through it every domain module, BEFORE the finder below is installed.
# `adcp.types.core` was then bound without its fallback and 3,216 of upstream's tests
# failed on `adcp.types.core.TaskResult`.  `import_module` goes to the import system.
from importlib import import_module as _import_module  # noqa: E402

_import_module(__name__ + "._dropin")
'''

#: The bundle this repository compiles, relative to its root.  An argument with a default,
#: because D9 keeps the version out of ``codegen/`` and this is not ``codegen/``.
BUNDLE = Path("schemas") / "cache" / "3.2"

#: Where the output's own record of what produced it goes.  Beside the tree, at its root.
RECORD = "REGENERATED.json"


# --------------------------------------------------------------------------- 1. the wheel


@dataclass(frozen=True)
class Wheel:
    """Upstream's installed wheel, verified.  ``say`` is the sentence a verdict quotes."""

    package: Path
    dist_info: Path
    version: str
    files: int
    hashed: int
    say: str


def verify_wheel(package: Path) -> Wheel:
    """Upstream's real wheel, or a refusal that names what was handed over instead.

    **THE VERIFICATION IS THE INSTALLER'S OWN ``RECORD``, not a version string.**  Three
    directories on this box answer ``import adcp`` and only one is upstream: ``venv-dropin96``
    and ``venv-drop2`` resolve it through an editable ``.pth`` into a WORKTREE, so the
    "9.6.1" in their ``dist-info`` describes a package whose files are a lane's source tree.
    A ``RECORD`` hash disagrees the moment that happens, and a tree carrying
    ``types/_schemas`` disagrees before the first hash is computed, so both screens are here:
    the cheap structural one for the common mistake, the complete one for the rest.
    """
    package = package.resolve()
    if package.name != DIST:
        package = package / DIST
    site = package.parent
    found = sorted(site.glob(f"{DIST}-*.dist-info"))
    if not found:
        raise SystemExit(
            f"not an install of {DIST}: no {DIST}-*.dist-info beside {package}. "
            f"The genuine {VERSION} install on this box is "
            f"/srv/ws/.adcp-scratch/flat-derive/up/lib/python3.12/site-packages/adcp."
        )
    dist_info = found[-1]
    meta = dict(
        line.split(": ", 1)
        for line in (dist_info / "METADATA").read_text(encoding="utf-8").splitlines()
        if ": " in line and not line.startswith(" ")
    )
    version = meta.get("Version", "")
    if version != VERSION:
        raise SystemExit(
            f"{dist_info.name} declares version {version!r} and this instrument's alias "
            f"layer, member-spelling derivation and 104-file declaration were all read off "
            f"{VERSION}.  A different wheel is a different measurement."
        )
    # The structural screen: ours and theirs cannot both be the generated tree.
    if (package / "types" / "_schemas").exists():
        raise SystemExit(
            f"{package} carries types/_schemas, which is OURS -- this is a worktree source "
            f"tree reached through an editable .pth, not upstream's wheel."
        )
    if not (package / "types" / "domains").is_dir():
        raise SystemExit(
            f"{package} carries no types/domains, which is upstream's own generated layout. "
            f"Whatever this is, it is not an unmodified {DIST} {VERSION}."
        )
    hashed = bad = 0
    for row in (dist_info / "RECORD").read_text(encoding="utf-8").splitlines():
        name, _, rest = row.partition(",")
        digest, _, _size = rest.partition(",")
        if not digest.startswith("sha256=") or not name.startswith(DIST + "/"):
            continue
        path = site / name
        if not path.is_file():
            bad += 1
            continue
        want = digest[len("sha256=") :]
        got = (
            base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest())
            .decode()
            .rstrip("=")
        )
        hashed += 1
        bad += want != got
    if bad:
        raise SystemExit(
            f"{bad} of {hashed + bad} files under {package} disagree with the sha256 in "
            f"{dist_info.name}/RECORD.  This install has been written to since it was "
            f"installed and is not upstream's artifact."
        )
    files = sum(1 for p in package.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    say = (
        f"{dist_info.name} (installer {_read(dist_info / 'INSTALLER')}, "
        f"{_read(dist_info / 'direct_url.json')}): {files} files under {package}, "
        f"{hashed} carrying a sha256 in RECORD, 0 disagreeing; types/domains present and "
        f"types/_schemas absent, so the tree is upstream's generated layout and not ours."
    )
    return Wheel(package, dist_info, version, files, hashed, say)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else "(absent)"


# ------------------------------------------------------------------------ 2. the revision


@dataclass(frozen=True)
class Revision:
    """The git revision the wheel was built from, identified by byte agreement."""

    rev: str
    sha: str
    shared: int
    differ: int
    wheel_only: int
    rev_only: int
    say: str


def verify_revision(rev: str, wheel: Wheel) -> Revision:
    """That ``rev``'s ``src/adcp/**`` IS the wheel's ``adcp/**``, file by file.

    **THIS IS WHAT LICENSES TAKING THE TEST SUITE FROM GIT.**  A wheel carries no tests, no
    conftest and no compliance vectors, so a tree that measures upstream's behaviour needs a
    second source for them -- and a second source is a second thing to be wrong.  Comparing
    every file the two SHARE turns the provenance into a measurement: 0 disagreements means
    the revision's ``tests/`` is the wheel's own suite, and one disagreement means it is not
    and the build stops.
    """
    sha = _git("rev-parse", rev + "^{commit}").strip()
    paths = _git("ls-tree", "-r", "--name-only", sha, "src/adcp/").split()
    shared = differ = rev_only = 0
    worst: list[str] = []
    for path in paths:
        rel = path[len("src/adcp/") :]
        theirs = wheel.package / rel
        if not theirs.is_file():
            rev_only += 1
            continue
        shared += 1
        if theirs.read_bytes() != _git_blob(sha, path):
            differ += 1
            worst.append(rel)
    if differ:
        raise SystemExit(
            f"{differ} of {shared} files disagree between {rev} ({sha[:9]}) and the wheel: "
            f"{', '.join(worst[:5])}.  The revision is not what the wheel was built from, so "
            f"its tests are not the wheel's suite."
        )
    wheel_only = wheel.files - shared
    say = (
        f"{rev} = {sha[:9]}; {shared} files shared with the wheel and {differ} differ. "
        f"{rev_only} tracked files the wheel does not ship (upstream's "
        f"src/adcp/_compliance test vectors, excluded by their MANIFEST) are taken from the "
        f"revision; {wheel_only} files the wheel ships and git does not (their build-time "
        f"adcp/_schemas bundles) are taken from the wheel."
    )
    return Revision(rev, sha, shared, differ, wheel_only, rev_only, say)


def _git(*argv: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *argv], capture_output=True, text=True, check=True
    ).stdout


def _git_blob(rev: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "blob", f"{rev}:{path}"],
        capture_output=True,
        check=True,
    ).stdout


# ------------------------------------------------------------------------ 3. laying it out


def lay_upstream(out: Path, rev: Revision, wheel: Wheel) -> dict[str, int]:
    """Upstream's revision checked out, then its package REPLACED by the wheel's bytes.

    The replacement is a no-op by :func:`verify_revision`'s measurement and is done anyway,
    because "the machinery is the wheel's" must be true by construction and not by a
    comparison a reader has to go and find.
    """
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    archive = subprocess.Popen(
        ["git", "-C", str(ROOT), "archive", "--format=tar", rev.sha],
        stdout=subprocess.PIPE,
    )
    subprocess.run(["tar", "-x", "-C", str(out)], stdin=archive.stdout, check=True)
    archive.wait()
    package = out / "src" / DIST
    laid = 0
    for src in sorted(wheel.package.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        dst = package / src.relative_to(wheel.package)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        laid += 1
    return {"from the wheel": laid, "tracked by the revision only": rev.rev_only}


def lay_our_machinery(out: Path) -> dict[str, object]:
    """**OUR ``src/adcp/`` OVER THE WHEEL'S, EXCEPT ``types/``, AND THE DIFFERENCE REPORTED.**

    **THE SUBSET WAS THE DEFECT, ONE LEVEL UP FROM WHERE IT WAS FOUND.**
    :func:`_copy_ours_beside` already carries the argument -- "any predicate over it is a
    selection and a selection is what went wrong" -- and it is stated there about our
    ``types/`` directory.  The same predicate was applied to the PACKAGE: the tree laid
    upstream's whole ``src/adcp/`` from the wheel and substituted only ``types/``, so
    every other module a run executed was THEIRS.  Measured: a lane repaired nine
    construction sites in ``webhooks.py``, ``feed_mirror.py``, ``canonical_formats/`` and
    ``server/principal.py``, and the suite moved by ZERO tests -- the tracebacks still
    cited ``webhooks.py:272``, a line its source no longer had, because the file the run
    executed was upstream's.  177 failures were unverifiable and 5 lanes were grading a
    tree nobody ships.

    **WHAT THE OLD SHAPE WAS FOR, AND WHY REPORTING BEATS EXCLUDING.**
    :func:`lay_upstream` states it: "the machinery is the wheel's must be true BY
    CONSTRUCTION and not by a comparison a reader has to go and find".  That was sound
    while the only thing this repository changed was the type layer -- the behavioural
    difference was then attributable to the types alone.  It stops being sound the moment
    a defect is found in code we SHIP: ``core/protocol-envelope.json`` requires ``status``
    and ``src/adcp/decisioning/dispatch.py`` emitted a task response without one, which
    any conforming peer refuses.  A tree that excludes our repair of that cannot observe
    it.  So the attribution is kept by MEASUREMENT instead -- every module laid here is
    counted, and the ones whose bytes DIFFER from the wheel's are named -- and the
    exclusion is gone.

    ``types/`` is not laid here because the pipeline's later steps own it:
    :func:`strip_their_types` moves their colliding modules aside and
    :func:`substitute_ours` emits ours fresh, both of which assume upstream's layout is
    what they are handed.
    """
    package = out / "src" / DIST
    mine = ROOT / "src" / DIST
    laid: list[str] = []
    differing: list[str] = []
    for src in sorted(mine.rglob("*.py")):
        rel = src.relative_to(mine)
        if rel.parts[0] == "types" or "__pycache__" in rel.parts:
            continue
        dst = package / rel
        if dst.is_file() and dst.read_bytes() != src.read_bytes():
            differing.append(str(rel))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        laid.append(str(rel))
    return {
        "modules of ours laid over the wheel's": len(laid),
        "whose bytes DIFFER from the wheel's": len(differing),
        "differing": differing,
    }


def strip_their_types(out: Path, ours: frozenset[str]) -> dict[str, object]:
    """Delete their TYPES and their GENERATOR; keep their MACHINERY, marked as theirs.

    **THE SPLIT IS WHERE A MODULE LIVES, NOT WHAT IT IS, AND THAT WAS MEASURED THE HARD WAY**
    (``verdicts/dropin-modules.md`` §2).  The first pass deleted ``types/**`` entire, on the
    reading that the whole namespace is the one we replace.  ``error_narrowing.py`` holds
    ``narrow_union_errors`` -- a FUNCTION; 1,350 tests failed on that one name.  ``base.py``
    holds ``AdCPBaseModel``, ``projections.py`` holds ``project_geo_postal_areas``,
    ``_legacy_assets.py`` holds three coercers.  Reading 10 is right that a name with no
    schema subject takes a migration note and never a class, and a function was never a
    candidate for a class: their behavioural tests exercise behaviour THROUGH these exactly
    as through ``adcp.server``.

    **AND THE SIX THAT MOVE ARE DERIVED FROM THE COLLISION AND NOT LISTED.**  ``core``,
    ``creative``, ``error_details``, ``media_buy``, ``protocol`` and ``signals`` are each a
    hand-written module of theirs AND a domain module of ours.  Ours is the surface, so
    theirs goes to ``types/_upstream/<word>`` -- private, no export path of ours, invisible
    to reading 6 -- and ``_dropin._resolver`` asks it AFTER ours and BEFORE the flat surface.
    The set is ``their package-root stems ∩ our emitted stems``, computed here, so a domain
    gained or lost by the emitter cannot leave this layer stale.
    """
    types = out / "src" / DIST / "types"
    deleted = kept = moved = 0
    for name in THEIR_GENERATED:
        target = types / name
        if target.is_dir():
            deleted += sum(1 for p in target.rglob("*") if p.is_file())
            shutil.rmtree(target)
    for stub in sorted(types.glob("*.pyi")):
        stub.unlink()
        deleted += 1
    upstream = types / "_upstream"
    upstream.mkdir()
    (upstream / "__init__.py").write_text("")
    withdrawn = _withdrawn_by_this_repository()
    collisions = []
    for module in sorted(types.glob("*.py")):
        if module.name == "__init__.py":
            module.unlink()
            deleted += 1
            continue
        text = module.read_text(encoding="utf-8").rstrip("\n") + "\n" + MACHINERY_MARKER
        if module.stem in withdrawn:
            module.unlink()
            deleted += 1
        elif module.stem in ours:
            collisions.append(module.stem)
            (upstream / module.name).write_text(text)
            module.unlink()
            moved += 1
        else:
            module.write_text(text)
            kept += 1
    patched = _carry_the_patch_a_withdrawal_needs(out, withdrawn)
    generator = _their_generator(out)
    for path in generator:
        (out / path).unlink()
    _drop_their_generator_dependency(out / "pyproject.toml")
    orphaned = _tests_naming(out, generator)
    return {
        "their generated modules deleted": deleted,
        "their machinery kept at its own path": kept,
        "theirs WITHDRAWN -- this repository carried it and deleted it": sorted(withdrawn),
        "their SDK modules the withdrawal broke, replaced by ours": patched,
        "their machinery moved to types/_upstream (name collides with a domain of ours)": moved,
        "the collisions, derived": collisions,
        "their generator entry points deleted": sorted(generator),
        "retained test files naming one of them (must be empty)": orphaned,
    }


def _withdrawn_by_this_repository() -> frozenset[str]:
    """Modules of upstream's that this repository CARRIED and then deleted on purpose.

    **THE SECOND HALF OF ``adcp-client-python-l1r3``, and the measurement that settles it.**
    The substituted tree still held ``types/canonical_creative.py`` after ``2c714c881``
    deleted ours.  It is not a stale source read: the file in the tree is upstream's wheel
    bytes plus the one declared :data:`MACHINERY_MARKER`, so :func:`strip_their_types` put
    it there.  It did that because its keep/move rule asks only ``module.stem in ours`` --
    and a module we DELETED has no name left to collide with, so it fell through to "keep as
    machinery".  A module we removed on purpose then came back through the wheel.

    **DERIVED FROM THE CLASSIFICATION THIS REPOSITORY ALREADY COMMITS, not from a list.**
    ``survey/upstream-machinery-9.6.1.tsv`` carries a ``verdict`` per module of upstream's
    ``types/``: ``LIVE-RESTORE`` is this repository saying "their hand-written file is one
    we must carry".  Read beside the live tree, the pair that can only mean a deliberate
    withdrawal is ``verdict == LIVE-RESTORE`` AND no ``src/adcp/types/<stem>.py`` here.
    Measured on this trunk it names exactly one module, ``canonical_creative``; every other
    module upstream has and we do not is ``LIVE-TRANSITIVELY``, ``TEST-ONLY-DELETE`` or
    ``GENERATED-STAYS-DELETED`` -- the record never claimed those, so theirs is genuine
    machinery and stays (``validation``, ``coercion``, ``seller``, ``response_dispatch``,
    ``versioned`` and the rest keep their bytes).

    Restoring such a module makes the pair stop matching and the build keeps it again, with
    nothing edited here; deleting another ``LIVE-RESTORE`` module withdraws it the same way.
    """
    table = PAYLOAD.parent / "upstream-machinery-9.6.1.tsv"
    rows = [
        line.split("\t")
        for line in table.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    header = rows[0]
    module, verdict = header.index("module"), header.index("verdict")
    here = ROOT / "src" / DIST / "types"
    found = {
        row[module]
        for row in rows[1:]
        if len(row) > verdict
        and row[verdict] == "LIVE-RESTORE"
        and "." not in row[module]
        and not (here / f"{row[module]}.py").is_file()
    }
    return frozenset(found)


def _carry_the_patch_a_withdrawal_needs(out: Path, withdrawn: frozenset[str]) -> list[str]:
    """Upstream SDK modules that import a WITHDRAWN module, replaced by this repository's.

    **"DROP-IN PLUS A PATCH", MADE REPRODUCIBLE INSTEAD OF REMEMBERED.**  Withdrawing
    ``canonical_creative`` is not free: upstream's own kept SDK imports it at module scope
    -- ``src/adcp/client.py`` line 188 and ``src/adcp/server/responses.py`` twice -- so the
    withdrawal alone breaks ``adcp.client``, and MEASURED on this tree that is **128 of
    upstream's test files failing at collection**, every one of them on an import that has
    nothing to do with what the test asserts.  ``adcp-client-python-2f52`` already made
    exactly this patch in this repository and the owner accepted it in those words: "Means
    drop-in is impossible and we STILL DELETE THEM ... drop-in and a patch then."  What was
    missing is that the substituted tree never carried it.

    **THE SET IS THE DAMAGE, DERIVED TWICE OVER AND NOT LISTED.**  A module qualifies only
    when all three hold: upstream's copy IMPORTS a withdrawn module (read by AST, not by
    text, so a comment naming it is not an import); this repository has a module at the same
    path; and OURS does not import it.  The third clause is what makes the swap a repair
    rather than a preference -- it carries only the modules whose patch is the removal of
    that very import, and a module of ours that merely differs is left alone, so the
    substitution does not creep from ``types/`` into upstream's SDK.
    """
    if not withdrawn:
        return []
    names = {f"{DIST}.types.{stem}" for stem in withdrawn}

    def imports_withdrawn(path: Path) -> bool:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            return False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module in names:
                return True
            if isinstance(node, ast.Import) and any(a.name in names for a in node.names):
                return True
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == f"{DIST}.types"
                and any(a.name in withdrawn for a in node.names)
            ):
                return True
        return False

    package = out / "src" / DIST
    carried = []
    for path in sorted(package.rglob("*.py")):
        if (package / "types") in path.parents or not imports_withdrawn(path):
            continue
        rel = path.relative_to(out)
        mine = ROOT / rel
        if not mine.is_file() or imports_withdrawn(mine):
            continue
        path.write_text(mine.read_text(encoding="utf-8"), encoding="utf-8")
        carried.append(str(rel))
    return carried


def _tests_naming(out: Path, deleted: list[str]) -> list[str]:
    """Which retained ``test_*.py`` names a script this instrument deleted.

    **THE GATE THAT MAKES THE DERIVATION SAFE TO PREFER OVER A LIST.**  The hand-built trees
    deleted TWELVE scripts, chosen by reading them; :func:`_their_generator`'s rule lands on
    nine -- it takes ``fix_schema_refs.py`` and ``task_message_lattice.py`` that they kept and
    keeps five that they took.  That difference may only be allowed to stand because it
    CANNOT move a figure, and the way to know is to ask the retained population, which is
    what this does: a behavioural file naming a deleted module would fail here and pass
    there, and the two trees' totals would stop being comparable.  Measured on 9.6.1: empty.
    """
    modules = {Path(path).stem for path in deleted if path.endswith(".py")}
    about_their_generator = set(
        _declared_lines(PAYLOAD / "upstream-tests-about-their-generator.txt")
    )
    named = []
    for test in sorted((out / "tests").rglob("test_*.py")):
        if str(test.relative_to(out)) in about_their_generator:
            continue  # going anyway, by the declared population
        text = test.read_text(encoding="utf-8", errors="replace")
        if any(module in text for module in modules):
            named.append(str(test.relative_to(out)))
    return named


def _their_generator(out: Path) -> list[str]:
    """Their generator's entry points, read off the scripts themselves.

    **DERIVED AND NOT LISTED**, because a list goes stale against the next upstream version
    and this instrument would then delete eleven of twelve files and say nothing.  A script
    of theirs is a generator entry point when it names ``datamodel_code_generator`` or writes
    into ``adcp/types/domains``; the manifest they share is named beside them because a JSON
    file states no imports.
    """
    scripts = out / "scripts"
    found = []
    for path in sorted(scripts.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "datamodel_code_generator" in text or "datamodel-code-generator" in text:
            found.append(str(path.relative_to(out)))
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        doc = (ast.get_docstring(tree) or "") + text[:0]
        if "types/domains" in text or "types/domains" in doc:
            found.append(str(path.relative_to(out)))
    if (out / THEIR_GENERATOR_MANIFEST).is_file():
        found.append(THEIR_GENERATOR_MANIFEST)
    return found


def _drop_their_generator_dependency(pyproject: Path) -> None:
    """``datamodel-code-generator`` out of every dependency group, and our two formats in.

    The generator is gone, so a group that still asks for it describes a tree that does not
    exist.  The two additions are the other half of the same honesty: our ``strict_validate``
    decides acceptance through ``jsonschema``, and ``jsonschema`` asserts NOTHING for a
    draft-07 ``format`` unless its checker is installed -- so without them ``date-time`` and
    ``uri`` are ungraded and the suite would be measuring a weaker model than we ship.
    """
    text = pyproject.read_text(encoding="utf-8")
    keep = []
    for line in text.splitlines(keepends=True):
        if "datamodel-code-generator" in line:
            continue
        keep.append(line)
        if '"jsonschema>=4.20.0",' in line:
            indent = line[: len(line) - len(line.lstrip())]
            keep.append(f'{indent}"rfc3339-validator>=0.1.4",\n')
            keep.append(f'{indent}"rfc3987>=1.3.8",\n')
    pyproject.write_text("".join(keep))


def drop_their_generator_tests(out: Path) -> dict[str, object]:
    """Upstream's 104 test files that grade their generator, by the declared population.

    **THE DECLARATION IS DATA AND THE CHECK IS A RULE.**  Every path in
    ``survey/dropin/upstream-tests-about-their-generator.txt`` must name a file upstream's
    revision actually carries; a stale row means the denominator this instrument reports is
    not the denominator it believes, so a stale row refuses the build.
    """
    declared = _declared_lines(PAYLOAD / "upstream-tests-about-their-generator.txt")
    missing = [p for p in declared if not (out / p).is_file()]
    if missing:
        raise SystemExit(
            f"{len(missing)} declared generator tests are not files of this revision: "
            f"{', '.join(missing[:5])}.  The declaration is stale and the population it "
            f"defines would be wrong."
        )
    for path in declared:
        (out / path).unlink()
    return {"their generator tests deleted": len(declared)}


def deselect_the_declined(out: Path) -> dict[str, object]:
    """ONE table, TWO layers, each row keeping its own reason -- written into the tree.

    **THIS IS THE FILE-LEVEL REMOVAL ABOVE, CARRIED DOWN TO THE FUNCTION.**
    :func:`drop_their_generator_tests` takes 104 whole files whose SUBJECT is their
    generator.  Two readings then decline individual test functions inside the files that
    remain, and they are different readings of different evidence -- neither subsumes the
    other, so both write rows here:

    ``delete-set``
        ``survey/upstream_test_character.py``'s DELETE verdict: the ASSERTION is about
        upstream's own representation -- ``__module__``, ``__all__``, ``model_fields``, the
        annotation object, ``sys.modules``, pydantic's private attributes.  No payload, no
        envelope, no value a document admits or refuses, so no replacement generator can
        pass it.  Classified HERE, against the tree just laid, so the rows are over the
        files that are THERE -- the discipline :func:`population` already follows.

    ``invented-default``
        ``survey/dropin/deselect.py``'s classification: the test leans on a default
        upstream's generator invented, which makes a required field optional and admits a
        payload the document REFUSES.  Read from that module's committed table, because
        re-deriving it inside a build would put this repository's classification downstream
        of a measurement that reads it.

    **AND THE MERGE IS WHY THIS FUNCTION CHANGED** (``adcp-client-python-l1r3``).  There
    were two tables and the runner read one: ``deselect_plugin.py`` read ``deselect.tsv``
    and ``deselect.py`` wrote ``deselected-9.6.1.tsv``, which nothing in a built tree ever
    opened.  So the invented-default classification declined nothing and every figure taken
    from such a tree counted tests it had already judged uncountable.  One table now, with a
    ``layer`` column, and a row's ``reason`` is its own layer's sentence -- the character
    classifier's quoted assertion, or the model, field, document and pointer that refutes
    the default.

    **AND IT DESELECTS RATHER THAN EXCISES, which §8a decides.**  :func:`audit` calls any
    retained file that is not byte-identical to upstream's ``UPSTREAM EDITED``, and an edit
    in a disposable tree is a fork beginning.  Deselecting leaves every retained file
    byte-identical and still takes the rows out of the count.
    """
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import upstream_test_character as character

    spec = importlib.util.spec_from_file_location(
        "_dropin_deselect", PAYLOAD / "deselect.py"
    )
    invented_source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(invented_source)

    rows: list[dict] = []
    for path in sorted((out / "tests").rglob("test_*.py")):
        for row in character.classify(path):
            row["file"] = str(path.relative_to(out))
            rows.append(row)

    declined: dict[tuple[str, str], tuple[str, str]] = {}
    for row in sorted(
        (r for r in rows if r["verdict"] == "DELETE"), key=lambda r: (r["file"], r["test"])
    ):
        why = f"{row['why']} -- {' '.join(row['assertion'].split())}"
        declined[(row["file"], row["test"])] = ("delete-set", why)
    from_defaults = 0
    for path, test, why in invented_source.committed_rows():
        if not (out / path).is_file():
            continue  # its file is one of the 104 already removed; nothing to decline
        key = (path, test)
        if key in declined:
            layer, existing = declined[key]
            declined[key] = ("delete-set+invented-default", f"{existing} || {why}")
        else:
            declined[key] = ("invented-default", why)
        from_defaults += 1

    lines = [
        "# DERIVED -- do not edit.  Two layers, one table, each row with its own reason:",
        "#   delete-set        survey/upstream_test_character.py, classified over THIS tree",
        "#   invented-default  survey/dropin/deselect.py's committed classification",
        "# survey/dropin/deselect_plugin.py deselects exactly these at collection, so they",
        "# leave the denominator with no file of upstream's changed.",
        "path\ttest\tlayer\treason",
    ]
    for (path, test), (layer, why) in sorted(declined.items()):
        lines.append(f"{path}\t{test}\t{layer}\t{why}")
    (out / "deselect.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "deselect.py").write_text(
        (PAYLOAD / "deselect_plugin.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    by_layer = collections.Counter(layer for layer, _ in declined.values())
    return {
        "test functions declined": len(declined),
        "by layer": dict(sorted(by_layer.items())),
        "invented-default rows whose file survives the 104": from_defaults,
        "files they are spread over": len({path for path, _ in declined}),
        "PORT (kept, re-pointed by the finder)": sum(1 for r in rows if r["verdict"] == "PORT"),
        "BEHAVIOUR (kept, must pass)": sum(1 for r in rows if r["verdict"] == "BEHAVIOUR"),
    }


def _declared_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def correct_the_payloads(out: Path) -> dict[str, object]:
    """The payloads that contradict their own envelope, corrected from committed DATA.

    **`core/protocol-envelope.json` requires `status` and every task response composes it
    through an `allOf`**, so a payload that omits the field contradicts its document.
    Upstream's suite is full of such payloads and green anyway, because their generator
    wrote ``status: Literal['completed'] = 'completed'`` -- a default the document states
    nowhere, which is exactly what this repository does not reproduce.

    **THE CORRECTION IS DATA AND THE BUILD IS WHAT APPLIES IT.**  A drop-in tree is
    disposable (§8a) and ``--audit`` reports an edited file as a fork beginning, so the
    rows live in ``survey/dropin/payload_fixes.py``, each carrying the document and pointer
    that justifies it and the value the document admits.  Nothing is hand-edited in the
    tree and the tree stays regenerable.

    Runs here, after the files are laid and the declined rows are written, and before the
    substitution -- the corrections are to upstream's test payloads, not to our types.
    """
    spec = importlib.util.spec_from_file_location(
        "_dropin_payload_fixes", PAYLOAD / "payload_fixes.py"
    )
    fixes = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec: ``@dataclass`` resolves its own module out of
    # ``sys.modules`` to read string annotations, and a module that is not there yet
    # fails with an AttributeError on ``None``.
    sys.modules[spec.name] = fixes
    spec.loader.exec_module(fixes)
    return fixes.apply(out)


# ----------------------------------------------------------------------------- 4. the substitution


def substitute_ours(out: Path, bundle: Path) -> dict[str, object]:
    """Our types: a FRESH EMIT, plus the three modules the compiler does not write.

    **§2's rule, applied to the one tree that is not graded here.**  "The subject of grading
    is a FRESH EMIT, never the committed tree": a drop-in built by copying
    ``src/adcp/types/`` would report on whatever happened to be committed, which is the
    drift §8a's fork measured.  So the compiler runs, over ``bundle.portable(BUNDLE)`` -- the
    bundle's own population, read by the one predicate ``codegen`` already has and never
    listed -- and the output is compared against the committed tree so the run SAYS whether
    the two agree instead of leaving a reader to assume it.

    ``emit``+``write`` are called directly rather than through ``python -m codegen``, because
    that entry point also GRADES what it wrote (``__main__.grade``, 40 s warm and 2,015 s
    cold) and a grade is this repository's business, not the drop-in's.  The numbers it would
    print are ``./check``'s, which §8a says regeneration must not move.
    """
    from codegen import bundle as bundle_mod
    from codegen import patch
    from codegen.emit import emit, write

    directory = patch.for_build(ROOT / bundle)
    population = sorted(bundle_mod.portable(directory))
    started = time.time()
    out_emit = emit(directory, population)
    types = out / "src" / DIST / "types"
    write(out_emit, types / "_schemas", types)
    elapsed = time.time() - started
    if out_emit.refusals:
        raise SystemExit(
            f"{len(out_emit.refusals)} documents refused by this emit; ./check reads "
            f"'refused 0' on trunk, so the tree this would substitute is not the tree the "
            f"repository states."
        )
    agree, differ = _against_the_committed_tree(types, out_emit.files, out_emit.beside)
    return {
        "bundle": str(bundle),
        "documents in the population": len(population),
        "modules emitted": len(out_emit.emitted),
        "refusals": len(out_emit.refusals),
        "emit seconds": round(elapsed, 1),
        "files written by the emitter": agree + len(differ),
        "byte-identical to the committed tree": agree,
        "differing from the committed tree": differ,
        "beside the emit, copied from this repository": _copy_ours_beside(types),
    }


def _against_the_committed_tree(
    types: Path, written: dict[str, str], beside: dict[str, str]
) -> tuple[int, list[str]]:
    """How many of this emit's files the committed tree already holds, byte for byte.

    A zero in the second column is the determinism statement §8a asks for, stated over the
    artifact rather than over a hash of the inputs: the compiler is a function of the bundle
    and its own source, so a fresh emit here and the tree committed there are the same bytes
    or the committed tree is stale.

    **RANGED OVER WHAT THE EMITTER WROTE AND NOT OVER THE DIRECTORY, which is the difference
    between a comparison and a coincidence.**  By the time this runs the same directory also
    holds upstream's 34 kept machinery modules and the four of ours copied in beside the
    emit; walking it reported 41 files "differing from the committed tree" that the compiler
    never wrote and the committed tree was never meant to hold.  ``Emitted.files`` is the
    run's own record of its output, so the set compared is the set produced.
    """
    committed = ROOT / "src" / DIST / "types"
    root = types / "_schemas"
    agree, differ = 0, []
    for name in sorted(written):
        here = root / name
        mirror = committed / "_schemas" / name
        if not mirror.is_file() or not here.is_file():
            differ.append(name)
        elif mirror.read_bytes() == here.read_bytes():
            agree += 1
        else:
            differ.append(name)
    for name in sorted(beside):
        here = types / name
        mirror = committed / name
        if mirror.is_file() and here.is_file() and mirror.read_bytes() == here.read_bytes():
            agree += 1
        else:
            differ.append(name)
    return agree, differ


def _copy_ours_beside(types: Path) -> list[str]:
    """EVERY module this repository holds at ``src/adcp/types/*.py``.  Not a selection.

    **THE SELECTION WAS THE DEFECT** (``adcp-client-python-l1r3``).  This copied four named
    modules, then the public paths that compose ``_surface`` -- and both readings are a
    SUBSET of our type layer, so the substituted tree was missing 14 modules of ours:
    ``_adapter``, ``_restored``, ``aliases``, ``base``, ``buyer``, ``capabilities``,
    ``error_narrowing``, ``guards``, ``legacy``, ``media_buy_status_helpers``,
    ``projections``, ``registry``, ``v32``, ``variants``.  Twelve of those are words
    :func:`strip_their_types` had just MOVED out of the way -- upstream's own module went to
    ``types/_upstream/<word>`` because the name collides with one of ours, and then ours
    never arrived, so the path held nothing at all.  ``adcp.types.base`` is the one the
    import dies on first: our ``_base.py`` reads ``from adcp.types.base import
    AdCPBaseModel``, which is the restored upstream base our emitted models derive from.

    **AND THE RULE IS THE WHOLE DIRECTORY, because any predicate over it is a selection and a
    selection is what went wrong.**  ``codegen/emit.py`` writes into ``_schemas/`` and
    ``_surface/`` -- both subdirectories -- so every ``*.py`` sitting directly in
    ``src/adcp/types/`` is ours by hand or ours by a survey, and all of it is the layer the
    substitution puts in place of theirs.  A module added there arrives with no edit here,
    which is what :func:`strip_their_types`' own collision rule already assumes when it asks
    ``module.stem in ours``: the two halves now read the same directory.

    ``compat.py`` is generated in THIS repository by ``survey/alias_surface.py``, whose input
    is upstream's wheel surface and whose gate is
    ``tests/test_the_alias_layer_is_names.py``; it is committed here as that run's artifact
    and copied, not re-derived, because re-deriving it inside a build would put this
    repository's alias decisions downstream of a measurement that reads them.
    """
    copied = []
    source_dir = ROOT / "src" / DIST / "types"
    for name in OURS_BESIDE_THE_EMIT:
        if not (source_dir / name).is_file():
            raise SystemExit(f"this repository has no src/{DIST}/types/{name} to substitute")
    for source in sorted(source_dir.glob("*.py")):
        text = source.read_text(encoding="utf-8")
        if source.name == "__init__.py":
            text = text.rstrip("\n") + "\n" + TYPES_INIT_TAIL
        (types / source.name).write_text(text)
        copied.append(source.name)
    public = [n for n in copied if not n.startswith("_")]
    if not public:
        raise SystemExit(
            "this repository publishes no module at src/{DIST}/types/<name>.py, so the "
            "substituted tree would have no public type path at all."
        )
    copied += _copy_the_package_root_modules_they_lack(types.parent)
    return copied


def _copy_the_package_root_modules_they_lack(package: Path) -> list[str]:
    """Every ``adcp/<name>.py`` a substituted ``types/`` module imports that upstream has not.

    **MEASURED AND NOT LISTED, and on this trunk it is exactly one.**  Our
    ``adcp/types/core.py`` re-exports the SDK's own client types -- ``TaskResult``,
    ``AgentConfig``, ``Protocol``, ``TaskStatus``, ``DebugInfo`` -- with ``from ..core
    import ...``, because the ruling that keeps ``adcp.types`` schema-derived moved them to
    ``adcp.core``, the SDK's own public namespace.  Upstream has no ``adcp/core.py`` at all,
    so nothing collides and nothing of theirs is overwritten: the rule is "ours, where
    theirs has no module at that path", and a name they DO carry is left alone and stays
    their bytes.

    Without this the substitution lands a ``types/core.py`` whose first import raises, and the
    whole public surface goes with it.
    """
    source_dir = ROOT / "src" / DIST
    wanted: set[str] = set()
    for path in sorted((package / "types").glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 2 and node.module:
                wanted.add(node.module.split(".")[0])
    copied = []
    for name in sorted(wanted):
        if (package / f"{name}.py").exists() or (package / name).is_dir():
            continue  # upstream carries it; theirs stands
        source = source_dir / f"{name}.py"
        if not source.is_file():
            raise SystemExit(
                f"a substituted types module imports `adcp.{name}`, upstream has no module at "
                f"that path, and neither does this repository: the substitution would land a "
                f"surface that cannot import."
            )
        (package / f"{name}.py").write_text(source.read_text(encoding="utf-8"))
        copied.append(f"../{name}.py")
    return copied


def alias_layer(out: Path) -> dict[str, object]:
    """``_dropin.py``: upstream's module paths and flat spellings, served out of our tree.

    **IT LIVES IN THIS REPOSITORY AND IS COPIED IN, WHICH IS THE POINT.**  The hand-built
    trees authored this file inside the drop-in -- 562 lines with four measured defects
    repaired in it across four lanes, reachable from nowhere else and regenerable by nothing.
    §8a: "a defect in our types or our compiler is fixed HERE".  A file that serves upstream's
    spellings is not part of our wheel either, so its home is ``survey/dropin/``, beside the
    population and the partition it is measured with.
    """
    types = out / "src" / DIST / "types"
    source = (PAYLOAD / "_dropin.py").read_text(encoding="utf-8")
    (types / "_dropin.py").write_text(source)
    marker = "__adcp_upstream_machinery__"
    hosts = sorted(
        p.name
        for p in list(types.glob("*.py")) + list((types / "_upstream").glob("*.py"))
        if marker in p.read_text(encoding="utf-8")
    )
    return {
        "modules hosting a flat spelling (declared by the module, read as text)": len(hosts),
        "served module prefixes": ["adcp.types.domains.<domain>.<document>", "adcp.types.<word>"],
    }


# ------------------------------------------------------------------------------ 5. the probe


# **THERE IS NO PROBE, AND ``adcp.types._generated`` IS SERVED BY THE FILE THAT GENERATES IT.**
# A ``sitecustomize.py`` stood here and shadowed that module with a ``MetaPathFinder``, serving
# each name lazily from ``gen_bind.json`` -- 2,971 rows read by AST out of upstream's own
# ``_generated.py``, so every row carried THEIR module and THEIR class name as the target. The
# module side resolved by accident of path and the attribute side was never joined against what
# this compiler emits, which is why ``gen.VerifyBrandClaimsRequest`` raised while our class sat
# there as ``VerifyBrandClaimsRequestBulk`` -- the name its document's own title
# ("Verify Brand Claims Request (Bulk)") gives it. One row of 2,971, and it took 13,822 of
# 13,825 tests down with it, because the lookup ran in a fixture every test uses.
#
# Its stated purpose was to MEASURE: lazy so that "only the names the SDK and its tests actually
# ASK for have to resolve, and the count of those is what this probe is measuring". A measuring
# device became the mechanism, and then mistranslated.
#
# ``survey/adapter_surface.py`` already writes ``_generated.py`` from the join -- our names,
# resolved by pointer -- and eager is the better failure: an absent name raises AT IMPORT and
# names itself, instead of a table answering with a name that does not exist. ``probe_map.json``
# stays in ``survey/probes/``; ``survey/node_keyed_aliases.py`` reads it and it is a different
# artifact with its own committed rules.

def population(out: Path) -> list[str]:
    """Upstream's behavioural files: every ``test_*.py`` their revision carries, less the 104.

    Derived from the tree that was just laid, so the figure a run reports is over the files
    that are THERE -- not over a list of what was expected to be.
    """
    tests = out / "tests"
    return sorted(
        str(p.relative_to(out))
        for p in tests.rglob("test_*.py")
        if p.is_file()
    )


def chunks(out: Path) -> dict[str, list[str]]:
    """The four disjoint exhaustive chunks, gated against the derived population.

    A total summed over a partition is comparable to another total summed over the SAME
    partition and merely similar to one summed over a different one -- and ``collected`` is
    not a constant here: it moved 15,399 -> 15,628 between two lanes as files that had been
    aborting began to collect.  So the partition is declared in ``survey/dropin/chunks.tsv``
    and checked here: disjoint, and exactly the population.
    """
    rows = [row.split("\t") for row in _declared_lines(PAYLOAD / "chunks.tsv")]
    by_chunk: dict[str, list[str]] = collections.defaultdict(list)
    for chunk, path in rows:
        by_chunk[chunk].append(path)
    declared = [path for _, path in rows]
    if len(set(declared)) != len(declared):
        raise SystemExit("survey/dropin/chunks.tsv is not disjoint: a file appears twice")
    have = set(population(out))
    if set(declared) != have:
        extra = sorted(set(declared) - have)[:5]
        short = sorted(have - set(declared))[:5]
        raise SystemExit(
            f"the partition is not the population: {len(declared)} declared against "
            f"{len(have)} present; declared-not-present {extra}, present-not-declared {short}"
        )
    directory = out / "chunks"
    directory.mkdir(exist_ok=True)
    for chunk, paths in by_chunk.items():
        (directory / chunk).write_text("\n".join(paths) + "\n")
    return dict(by_chunk)


# ------------------------------------------------------------------- 6a. the run, automated


#: **ONE RUN AT A TIME, ACROSS EVERY WORKTREE ON THE MACHINE**, which is why the path is
#: outside any of them.  A run is four ``pytest -n auto`` invocations over 13,818 tests
#: with two packages installed, and several lanes measure at once by design.  Measured with
#: three concurrent: load average 47, 92 of 125 GiB resident, swap exhausted and
#: ``/proc/vmstat`` at ``oom_kill 75`` -- so a chunk's workers are killed, its report is
#: never written, and ``survey.causes`` reads the surviving chunks as if they were the
#: population.  That is the shape of defect that let a DEAD run be reported as "still
#: running" for an hour: the failure is silent and looks like progress.
#:
#: **IT QUEUES, IT DOES NOT REFUSE.**  A lock that failed would make a lane's measurement a
#: function of who else happened to be measuring, and the answer to "two lanes want the
#: same machine" is that the second one waits.  The wait is ANNOUNCED, because a queued run
#: and a hung one look identical from outside and one of them is fine.
RUN_LOCK = Path("/srv/ws/.adcp-dropin-run.lock")


@contextlib.contextmanager
def one_run_at_a_time() -> Iterator[None]:
    """Hold :data:`RUN_LOCK` for the provision-and-run phase, waiting if another run has it.

    Only that phase: the BUILD is cheap and parallel-safe (it writes into its own ``--out``),
    so serialising it too would make every lane wait on work that costs nothing shared.
    """
    RUN_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_LOCK, "a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.seek(0)
            holder = handle.read().strip() or "another run"
            print(f"\n== waiting for the machine: {holder} holds {RUN_LOCK}")
            print("   (queued, not hung -- three concurrent runs exhaust 125 GiB and the")
            print("    OOM killer takes a chunk's workers, leaving a report nobody wrote)")
            waited = time.monotonic()
            fcntl.flock(handle, fcntl.LOCK_EX)
            print(f"== the machine is ours after {time.monotonic() - waited:.0f} s\n")
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid {os.getpid()} in {Path.cwd()}\n")
        handle.flush()
        try:
            yield
        finally:
            handle.seek(0)
            handle.truncate()
            handle.flush()
            fcntl.flock(handle, fcntl.LOCK_UN)

def _their_test_extra(pyproject: Path) -> str | None:
    """Which of upstream's own extras declares their test dependencies.

    **A HAND-LISTED SET GOES STALE SILENTLY.**  Provisioning named four packages --
    ``pytest``, ``pytest-xdist``, ``pytest-asyncio``, ``pytest-json-report`` -- and
    upstream's suite imports more than that: 41 files died on ``asgi_lifespan``, 5 on
    ``respx``, 3 on ``freezegun``, and every one of those was counted as a FAILURE rather
    than as a missing package.  Appending three names fixes today and breaks on the next
    bump, so the set is read out of THEIR declaration instead.

    The extra is identified by what it contains, not by its name: the one that declares
    ``pytest``.  Returns ``None`` when no extra does, which the caller reports -- a tree
    whose test dependencies are undeclared is a finding, not something to paper over.
    """
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - 3.10 runs this file rarely
        return None
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    extras = (declared.get("project") or {}).get("optional-dependencies") or {}
    for name, requirements in sorted(extras.items()):
        if any(str(req).split("[")[0].split(">")[0].split("=")[0].strip() == "pytest"
               for req in requirements):
            return name
    return None


def provision(out: Path) -> dict[str, object]:
    """The tree's own venv, with the tree and its sibling package installed into it.

    **THE REPOSITORY IS TWO PACKAGES AND INSTALLING ONLY THE ROOT REPORTS A PLAUSIBLE
    NUMBER.**  Measured on upstream's own tree: with only the root installed the suite
    collects 16,480 and 15 test modules fail to import on
    ``ModuleNotFoundError: adcp_reporting_storage``; with ``packages/adcp-reporting-storage``
    installed it collects 21,668.  The 5,188 difference is silent -- no error names the
    missing package at the top level -- so provisioning belongs in the build and not in a
    reader's memory.
    """
    venv = out / ".venv"
    python = str(venv / "bin" / "python")
    siblings = [
        path
        for path in sorted((out / "packages").glob("*"))
        if (path / "pyproject.toml").is_file()
    ]
    extra = _their_test_extra(out / "pyproject.toml")
    root = "." if extra is None else f".[{extra}]"
    steps: list[list[str]] = [
        ["uv", "venv", str(venv), "--python", "3.12"],
        ["uv", "pip", "install", "-q", "--python", python, "-e", root],
    ]
    steps += [
        ["uv", "pip", "install", "-q", "--python", python, "-e", str(path)]
        for path in siblings
    ]
    # ``pytest-json-report`` is OURS and is named here on purpose: it is the reporter this
    # harness reads its figures out of, not a dependency upstream's suite has.  Everything
    # their tests import comes from their own extra above.
    steps.append(
        ["uv", "pip", "install", "-q", "--python", python, "pytest-json-report"]
    )
    for step in steps:
        done = subprocess.run(  # noqa: S603
            step, cwd=out, capture_output=True, text=True, check=False
        )
        if done.returncode:
            raise SystemExit(
                f"provisioning failed: {' '.join(step)}\n"
                f"{done.stdout[-2000:]}{done.stderr[-2000:]}"
            )
    return {
        "venv": str(venv),
        "siblings installed": len(siblings),
        "their test extra": extra or "NONE DECLARED -- their suite's imports are not covered",
    }


def run_chunks(out: Path, junit: Path) -> dict[str, object]:
    """Run every chunk and return what the REPORTS say, not what the terminal said.

    The commands are :func:`run_lines`' own, so what runs here and what a reader runs by hand
    are one string.  The result is read back from ``report.json`` -- pytest's own output, one
    entry per test with its outcome and its ``longrepr`` -- because a figure scraped from
    stdout is a figure that cannot be re-read.
    """
    junit.mkdir(parents=True, exist_ok=True)
    for line in run_lines(out, out / ".venv", junit):
        subprocess.run(line, shell=True, cwd=out, check=False)  # noqa: S602
    total: collections.Counter = collections.Counter()
    for found in sorted(junit.glob("*.json")):
        try:
            body = json.loads(found.read_text())
        except ValueError:
            continue
        for key, value in (body.get("summary") or {}).items():
            total[key] += value
    return dict(total) or {"no report": "pytest wrote no json; read the chunk logs"}


def run_lines(out: Path, venv: Path, junit: Path) -> list[str]:
    """The command per chunk, printed so the measurement is a command and not a procedure.

    **BOTH REPORT FORMATS, BECAUSE THE TREE TAKES ITS PYTEST CONFIGURATION FROM UPSTREAM'S
    ``pyproject.toml`` AND THAT FILE CONFIGURES NEITHER.**  Our own `pyproject.toml` sets them
    in `addopts`, so a bare `pytest` here writes both; the drop-in cannot inherit that, so the
    flags belong on the command the build prints rather than on whatever a reader remembers to
    type.  ``--junitxml`` was already here.  ``--json-report`` is the one that carries a
    ``longrepr`` per test, which is what enumerating a failure needs without running the suite
    a second time.
    """
    return [
        f"sudo systemd-run --scope --uid=1002 --gid=1002 -p MemoryMax=20G -q -- env "
        f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={out} "
        f"{venv}/bin/python -m pytest $(cat {out}/chunks/{chunk}) -q "
        "-p no:cacheprovider -p deselect "
        f"--continue-on-collection-errors -n 4 --junitxml={junit}/{chunk}.xml "
        f"--json-report --json-report-file={junit}/{chunk}.json"
        for chunk in ("chunk-00", "chunk-01", "chunk-02", "chunk-r159")
    ]


# ------------------------------------------------------------------------- 7. the record


def manifest(out: Path, facts: dict[str, object]) -> str:
    """A digest over every file of the output, beside the digests of both inputs.

    **THIS IS WHAT "RE-RUNNABLE AND DETERMINISTIC" MEANS AS A MEASUREMENT.**  Two runs on one
    trunk and one wheel produce the same ``digest``, and a reader who wants to know whether a
    tree is the tree this repository states compares one line.  The three inputs are named in
    the record: the wheel's ``RECORD``, the revision's commit, and this repository's ``HEAD``
    with its dirty flag -- because a build off a dirty worktree is not reproducible and the
    record has to say so rather than imply otherwise.
    """
    digest = hashlib.sha256()
    files = 0
    for path in sorted(out.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == RECORD:
            continue
        digest.update(str(path.relative_to(out)).encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        files += 1
    record = {
        "files": files,
        "digest": digest.hexdigest(),
        "this repository": {
            "head": _git("rev-parse", "HEAD").strip(),
            "dirty": bool(_git("status", "--porcelain").strip()),
        },
        **facts,
    }
    (out / RECORD).write_text(json.dumps(record, indent=2, sort_keys=False) + "\n")
    return record["digest"]


# --------------------------------------------------------------------------- 8. the audit


#: What a file of a drop-in tree can honestly be.  Anything else is an edit, and the whole
#: point of §8a is that an edit there has nowhere to go.
PROVENANCE = (
    "upstream verbatim",
    "upstream plus the machinery marker",
    "ours verbatim",
    "ours plus the drop-in activation tail",
    "UPSTREAM EDITED",
    "OURS EDITED",
    "AUTHORED THERE",
)


def audit(tree: str, rev: str, ours: str) -> dict[str, object]:
    """Classify every file of an existing drop-in tree against upstream and this repository.

    **THE SAME PARTITION AS THE BUILD, READ BACKWARDS.**  A regeneration is only a rule if a
    tree can be checked against it, and this is the check: each path is upstream's bytes,
    ours, one of the two plus the one declared marker, or an EDIT -- and an edit in a
    disposable tree is a fork beginning, which §8a says can only be deleted and regenerated.

    Takes git revisions rather than directories because the hand-built trees are branches,
    and a branch's bytes are the thing to compare: ``--audit sdk/jgsf``.
    """
    theirs = _tree(rev)
    mine = _tree(ours)
    subject = _tree(tree)
    marker = MACHINERY_MARKER.encode()
    verdicts: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(subject):
        blob = subject[path]
        # A module moved to `types/_upstream/<word>` is still upstream's file: the collision
        # rule MOVED it, so it is compared at the path it came from and not reported as new.
        theirs_path = path
        leaf = path.rsplit("/", 1)[-1]
        if path.startswith("src/adcp/types/_upstream/") and leaf != "__init__.py":
            theirs_path = "src/adcp/types/" + path[len("src/adcp/types/_upstream/") :]
        if theirs_path in theirs and theirs[theirs_path] == blob:
            verdicts["upstream verbatim"].append(path)
        elif path in mine and mine[path] == blob:
            verdicts["ours verbatim"].append(path)
        elif theirs_path in theirs and _blob(blob) == _blob(theirs[theirs_path]).rstrip(
            b"\n"
        ) + b"\n" + marker:
            verdicts["upstream plus the machinery marker"].append(path)
        elif path in mine and _blob(blob) == _blob(mine[path]).rstrip(
            b"\n"
        ) + b"\n" + TYPES_INIT_TAIL.encode():
            verdicts["ours plus the drop-in activation tail"].append(path)
        elif path == "src/adcp/types/_upstream/__init__.py" and not _blob(blob).strip():
            verdicts["ours verbatim"].append(path)
        elif theirs_path in theirs:
            verdicts["UPSTREAM EDITED"].append(path)
        elif path in mine:
            verdicts["OURS EDITED"].append(path)
        else:
            verdicts["AUTHORED THERE"].append(path)
    return {
        "tree": tree,
        "against": {"upstream": rev, "ours": ours},
        "counts": {k: len(verdicts[k]) for k in PROVENANCE if k in verdicts},
        "UPSTREAM EDITED": verdicts["UPSTREAM EDITED"],
        "OURS EDITED": verdicts["OURS EDITED"],
    }


def _tree(rev: str) -> dict[str, str]:
    found = {}
    for line in _git("ls-tree", "-r", rev).splitlines():
        meta, path = line.split("\t", 1)
        found[path] = meta.split()[2]
    return found


def _blob(sha: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "blob", sha], capture_output=True, check=True
    ).stdout


# ------------------------------------------------------------------------------- the command


@dataclass
class Report:
    """What the build says it did, in the order it did it."""

    sections: list[tuple[str, object]] = field(default_factory=list)

    def say(self, title: str, body: object) -> None:
        self.sections.append((title, body))
        print(f"\n== {title}")
        if isinstance(body, str):
            print(f"   {body}")
            return
        for key, value in body.items():
            if isinstance(value, list) and len(value) > 6:
                print(f"   {key}: {len(value)} ({', '.join(map(str, value[:4]))}, ...)")
            else:
                print(f"   {key}: {value}")

    def as_dict(self) -> dict[str, object]:
        return dict(self.sections)


def build(ns: argparse.Namespace) -> int:
    out = Path(ns.out).resolve()
    report = Report()
    wheel = verify_wheel(Path(ns.wheel))
    report.say("1. upstream's wheel, verified", wheel.say)
    rev = verify_revision(ns.rev, wheel)
    report.say("2. the revision it was built from, by byte agreement", rev.say)
    report.say("3. the tree laid out", lay_upstream(out, rev, wheel))
    report.say("3b. our machinery laid over theirs, except types/", lay_our_machinery(out))
    ours = frozenset(
        p.stem for p in (ROOT / "src" / DIST / "types").glob("*.py") if not p.name.startswith("_")
    )
    report.say("4. their types and their generator removed", strip_their_types(out, ours))
    report.say("5. their generator's tests removed", drop_their_generator_tests(out))
    report.say("5b. the declined tests, both layers, derived", deselect_the_declined(out))
    report.say("5c. the payloads that contradict the envelope", correct_the_payloads(out))
    report.say("6. our types substituted, FRESH", substitute_ours(out, Path(ns.bundle)))
    report.say("7. the alias layer", alias_layer(out))
    report.say(
        "9. the population and the partition",
        {chunk: len(paths) for chunk, paths in sorted(chunks(out).items())}
        | {"behavioural files": len(population(out))},
    )
    digest = manifest(
        out,
        {
            "wheel": {"dist_info": wheel.dist_info.name, "files": wheel.files},
            "upstream revision": rev.sha,
            "sections": report.as_dict(),
        },
    )
    print(f"\n== 10. the record\n   {out / RECORD}\n   digest {digest}")
    print(f"\n{out}\n")
    junit = Path(ns.junit or out / "junit")
    if ns.run:
        # **THE PIPELINE IS ONE COMMAND.**  Printing the commands kept "the measurement is a
        # command and not a procedure" true and made the procedure a reader's to remember:
        # build, then make a venv, then install two packages, then four pytest invocations.
        # Every step of that was performed by hand, and the one that was forgotten -- the
        # sibling package -- cost 5,188 silently uncollected tests.  `--run` does all of it
        # and reads the result back out of pytest's own report.
        with one_run_at_a_time():
            print("== 11. provisioning")
            print(f"   {provision(out)}")
            print("== 12. the run")
            said = run_chunks(out, junit)
        print(f"   {said}")
        print(f"\n   reports: {junit}/*.json and {junit}/*.xml\n")
        return 0
    for line in run_lines(out, Path(ns.venv or out / ".venv"), junit):
        print(line)
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m survey regenerate", description=__doc__)
    ap.add_argument(
        "--wheel",
        default="/srv/ws/.adcp-scratch/flat-derive/up/lib/python3.12/site-packages/adcp",
        help="upstream's INSTALLED wheel: the site-packages directory or the adcp package "
        "inside it.  Verified against its own dist-info RECORD; a worktree source tree "
        "reached through an editable .pth is refused.",
    )
    ap.add_argument("--out", help="where the drop-in tree is written (deleted and rebuilt)")
    ap.add_argument("--rev", default=REV, help="the git revision the wheel was built from")
    ap.add_argument("--bundle", default=str(BUNDLE), help="the bundle our types are emitted from")
    ap.add_argument("--venv", default=None, help="the interpreter the printed run commands use")
    ap.add_argument("--junit", default=None, help="where the run writes junit and json")
    ap.add_argument(
        "--run",
        action="store_true",
        help="provision the tree's venv and RUN every chunk, instead of printing the commands",
    )
    ap.add_argument(
        "--audit",
        default=None,
        metavar="REV",
        help="classify every file of an existing drop-in tree (a git revision) against "
        "upstream and this repository, and name every file that is an EDIT",
    )
    ap.add_argument("--ours", default="HEAD", help="which revision of ours --audit compares to")
    ns = ap.parse_args(argv)
    if ns.audit:
        print(json.dumps(audit(ns.audit, ns.rev, ns.ours), indent=2))
        return 0
    if not ns.out:
        ap.error("--out is required (or pass --audit)")
    return build(ns)


if __name__ == "__main__":
    raise SystemExit(main())
