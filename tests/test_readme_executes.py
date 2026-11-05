"""A README is executable documentation: every example it prints is RUN, never reviewed.

**Why this file exists, and it is a defect report rather than a preference.**  The README
is the only document in this tree addressed to someone who has not read the plan, and it
was the only document nothing graded.  ``tests/test_prose_resolves.py`` grades the prose of
``src/adcp`` and ``codegen`` -- its ``_dotted`` population is those two trees and no other
-- so every claim the README made was settled by reading it.  Four were false at the same
time, and each is the control of one clause below:

* its second command, the first thing a reader is told to run, raised
  ``TypeError: Pair.__init__() missing 1 required positional argument: 'accept'``
  (``adcp-client-python-5x5``) -- **clause 1**;
* the branch its "Merging back" section said the work merges into, ``sdk/generator-rebuild``,
  does not exist: ``git rev-parse`` reports ``fatal: Needed a single revision``
  -- **clause 2**;
* it attributed the ten migration steps to ``docs/plan/rebuild-plan.md``, which has nine
  sections and is the semantics document; the ten steps are ``architecture.md`` §14
  -- the file existed, so only clause 2 would have caught the pointer, and it did not,
  which is stated in :func:`test_what_these_clauses_do_not_grade`;
* it said the spike was "65 lines of emitter, 93 lines of emitted Python" against an
  emitter of 93 lines and an emitted module of 44 -- a FIGURE, which no clause here
  grades, and the answer was to stop printing figures a reader cannot check.

So the rule is the one ``test_prose_resolves`` already states for shipped docstrings,
applied to the document with the widest audience: **the claims a machine can settle are
settled.**  A fence either runs or it does not; a path either exists or it does not; a
dotted ``adcp`` path either imports or it does not.

**Clause 1 -- every ``python`` fence runs, against an INSTALLED package.**  Not against the
source tree: the failure this clause exists for is an example that works on
``PYTHONPATH=.:src`` from the repository root and fails for the reader who installed the
wheel.  So each fence runs in a subprocess from a working directory that is not the
repository, against ``src/adcp`` copied into a directory of its own -- which is what a
wheel unpacks to.  :func:`_installed` does that copy and is ``test_type_checker``'s,
imported rather than reimplemented so that "installed" has one meaning for both gates.

**The environment is not simply SCRUBBED, and the difference is measured.**  Scrubbing
``PYTHONPATH`` the way ``test_type_checker`` does is right for a checker, which is handed
the environment and reads it; it is wrong for RUNNING, because that venv is built
``--without-pip`` and holds no ``pydantic``, so every fence fails on the import of the
dependency rather than on anything the README said.  What this gate does instead is point
``PYTHONPATH`` at the unpacked copy ALONE: the dependencies resolve from the interpreter
running the suite, ``adcp`` resolves to the copy, and ``src`` is reachable by nothing.
:func:`test_the_consumer_environment_is_the_installed_copy_and_not_the_source_tree` asserts
that outcome directly off ``adcp.__file__`` rather than trusting the construction -- this
worktree's ``.venv`` carries an editable install pointing into the tree, so "the copy won"
is a claim that has to be read back.

**Clause 2 -- every slash-shaped backticked token either exists as a path or resolves as a
git ref.**  One clause and two resolutions, because a README names both kinds and they are
not distinguishable by shape: ``docs/plan/spike/grade.py`` is a path, ``sdk/readme`` is a
branch, and ``sdk/generator-rebuild`` was neither.  Harvested from the prose AND from the
``bash`` fences, so a command's arguments are checked even where the command is not run.

**Clause 3 -- every ``adcp``-rooted dotted path the README's PROSE spells either imports
from the installed package, or is DEMONSTRATED ABSENT by a fence clause 1 executed.  And
none is a TEMPLATE.**

The absent half is not a loophole, it is the reading.  This document's subject is which
names resolve and which do not, so it has to name ``adcp.server`` and ``adcp.decisioning``
-- and a clause requiring every spelled path to import would forbid the sentence that makes
the document honest.  The alternative a lane reaches for is an allowlist of "paths we mean
to be missing", which grows and is never read again.  So the rule is that an absence must
be SHOWN: a path the prose names and does not offer appears in a ``python`` fence, and
clause 1 has already run that fence, so the fence's own
``except ModuleNotFoundError`` is the evidence.  If the machinery ever ships, the fence
fails and the prose must change -- which is the direction a stale README fails in now.

``adcp.types.<domain>`` is the exact shape that shipped false in ``constraints.py`` and that
``test_prose_resolves``'s ``PLACEHOLDERS_ALLOWED`` exists to keep at zero.  A README
describing the surface names the modules; it does not print a path a reader will type with
a placeholder still in it.

**What is NOT graded, measured rather than asserted**: see
:func:`test_what_these_clauses_do_not_grade`.  The short of it is that the ``bash`` fences
are RESOLVED and not RUN -- ``pytest tests/test_emit.py`` is over twenty minutes and
``uv sync`` mutates the environment the suite is running in -- so the README prints its
measurements' commands and this file grades their arguments.

Perturbed, each clause separately, in :func:`test_each_clause_catches_the_prose_it_is_for`.
A rule nothing can break is a finding about the rule.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from test_type_checker import _installed

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

#: A fenced block and its language tag.  ``re.MULTILINE`` with ``^`` anchors so an indented triple
#: backtick inside a fence does not close it.
FENCE = re.compile(r"^```([A-Za-z]*)\n(.*?)^```", re.MULTILINE | re.DOTALL)

#: A token holding a ``/`` and nothing a path or a ref cannot hold: the shape of both a
#: repository path and a git ref, which clause 2 resolves as either.  A trailing ``/`` is
#: kept so a directory reads as one.
#:
#: **The character class is a denial and not a guess**, because the first version of this
#: harvest used ``str.split()`` over the bash fences and reported
#: ``emit.emit(Path("schemas/cache/3.2"),`` as an unresolvable path -- the README's
#: whole-tree command is Python inside ``python -c``, so a word-split harvest reads source
#: as filenames.  Excluded for that reason: quotes, parentheses and commas (Python source
#: in a shell fence), whitespace (prose in backticks), ``#`` (a JSON Pointer or an issue
#: anchor), ``$`` (a schema keyword or a shell variable), ``*`` (a glob), ``:`` (a URL or a
#: pytest node id, whose resolution is clause 1's business) and ``<`` (clause 3's
#: placeholder, reported there so one defect is reported once).
SLASHED_CHARS = r"A-Za-z0-9._/@~+-"
SLASHED = re.compile(rf"([{SLASHED_CHARS}]*/[{SLASHED_CHARS}]*)")
BACKTICKED = re.compile(r"`([^`]+)`")

#: The two directories a path in this README is relative to, and the second is not a
#: convenience.  D9 makes the bundle directory an ARGUMENT with no default, so the
#: emitter's document argument is bundle-relative by decision:
#: ``--bundle schemas/cache/3.2 core/pagination-request.json`` names one path from the
#: repository root and one from inside it, in the same fence.  Resolving against the root
#: alone reports the second as missing, which is a defect in the reader and not in the
#: README.
BASES = (ROOT, ROOT / "schemas" / "cache" / "3.2")

#: An ``adcp``-rooted dotted path, placeholder segments included so clause 3 can see them.
#: The spelling is ``test_prose_resolves.PATH``'s, deliberately: one definition of "a path
#: a reader will type" over two populations.
ADCP_PATH = re.compile(r"\badcp(?:\.(?:<[^>`\s]+>|[A-Za-z_]\w*))+")

#: Tokens clause 2 harvests that are NEITHER a path nor a ref and are not meant to be.
#: **EMPTY, and it may shrink and never grow** -- the same rule
#: ``test_prose_resolves.PLACEHOLDERS_ALLOWED`` states, for the same reason: an entry here
#: is a sentence a reader can act on wrongly, kept.
NOT_RESOLVED: frozenset[str] = frozenset()


def _fences(text: str, language: str) -> list[str]:
    return [body for tag, body in FENCE.findall(text) if tag == language]


def _resolves_as_git_ref(token: str) -> bool:
    done = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", token],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode == 0


def _slashed(text: str) -> set[str]:
    """Clause 2's harvest: slash-shaped tokens from backticked prose and from ``bash`` fences.

    **The fences are REMOVED before the prose is read, and that is a defect this harvest
    had.**  An inline span is a backtick pair, and a fence is three backticks -- so a
    pair-matching regex run over the whole document pairs a fence's backticks with each
    other and with the next inline span's, and the spans between fences vanish.  Measured
    on the README this file was written for: 47 "spans" were matched and
    ``sdk/generator-rebuild``, the one token clause 2 exists to catch, was not among them.
    The clause was green because its harvest was empty of the thing it was looking for,
    which is the failure mode the whole file is about, one level down.
    """
    tokens: set[str] = set()
    for quoted in BACKTICKED.findall(FENCE.sub("", text)):
        tokens |= set(SLASHED.findall(quoted))
    for body in _fences(text, "bash"):
        tokens |= set(SLASHED.findall(body))
    # A leading ``-`` is an option's value run together with the option.  A token needs a
    # non-empty component on both sides of a ``/`` to be a path or a ref at all: a bare
    # ``/`` is the prose separator in "``emitted`` / ``refused``" and names nothing.
    out = set()
    for token in tokens:
        if token.startswith("-"):
            continue
        trailing = "/" if token.endswith("/") else ""
        stem = token.strip("/.")
        head, _, tail = stem.partition("/")
        if head and tail:
            out.add(stem + trailing)
    return out


def _unresolved_tokens(text: str) -> list[str]:
    """Clause 2 over arbitrary text, returned rather than asserted so it can be perturbed."""
    bad = []
    for token in sorted(_slashed(text)):
        if token in NOT_RESOLVED:
            continue
        if any((base / token).exists() for base in BASES):
            continue
        if _resolves_as_git_ref(token):
            continue
        bad.append(token)
    return bad


def _consumer(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A working directory off the repository, and the environment that resolves the copy.

    Returns ``(where, env)``.  ``where`` is not the repository, so a fence that only works
    from the root fails here -- which is half of what clause 1 is for.  ``env`` points
    ``PYTHONPATH`` at the unpacked copy's parent and at nothing else, which is the other
    half: ``adcp`` is the copy and ``src`` is unreachable, while the dependencies the
    package declares still resolve from the interpreter running the suite.
    """
    venv = _installed(tmp_path).parents[1]
    (site,) = venv.glob("lib/python*/site-packages")
    where = tmp_path / "consumer"
    where.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(site)
    return where, env


def _run(where: Path, env: dict[str, str], body: str, index: int) -> str:
    """``""`` when the fence runs, else the report for it."""
    script = where / f"fence{index}.py"
    script.write_text(body)
    done = subprocess.run(
        [sys.executable, str(script)],
        cwd=where,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if done.returncode == 0:
        return ""
    return f"python fence {index} exited {done.returncode}:\n{body}\n--- stderr ---\n{done.stderr}"


def test_every_python_fence_in_the_readme_runs_against_the_installed_package(tmp_path) -> None:
    """Clause 1.  Every ``python`` fence of the README executes, exit code 0.

    **The population is asserted non-empty first, and that assertion is the point.**  A
    README with no executable example passes a clause that executes examples, and this
    reading is about a document promising a surface a reader cannot reach -- so a gate that
    is green because the promise moved into prose is the defect wearing the gate's badge.
    """
    text = README.read_text()
    fences = _fences(text, "python")
    assert fences, (
        "README.md prints no `python` fence, so clause 1 grades nothing. The README's "
        "claim about what imports is the claim this file exists to execute: state it as "
        "an import a reader can copy, not as prose."
    )
    where, env = _consumer(tmp_path)
    reports = [r for i, body in enumerate(fences) if (r := _run(where, env, body, i))]
    assert not reports, "\n\n".join(reports)


def test_the_consumer_environment_is_the_installed_copy_and_not_the_source_tree(
    tmp_path,
) -> None:
    """Clause 1's environment, read back rather than trusted.

    This worktree's ``.venv`` carries an editable install pointing into a checkout, and the
    suite itself runs on ``PYTHONPATH=.:src``.  Either one resolves ``adcp`` to the source
    tree, and clause 1 would then be green on an example that no reader who installed the
    package can run -- which is the exact failure this whole file is about, arriving inside
    the gate against it.  So the fact is asserted on ``adcp.__file__``.
    """
    where, env = _consumer(tmp_path)
    probe = (
        "import adcp, pathlib, sys\n"
        "print(pathlib.Path(adcp.__file__).resolve())\n"
        "import pydantic\n"  # the dependency has to resolve too, or clause 1 grades imports
    )
    report = _run(where, env, probe, 99)
    assert not report, report
    resolved = subprocess.run(
        [sys.executable, str(where / "fence99.py")],
        cwd=where,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout.strip()
    assert resolved.startswith(str(tmp_path)), (
        f"clause 1 would run against {resolved}, which is not the unpacked copy under "
        f"{tmp_path} -- so it is grading the source tree"
    )
    assert not resolved.startswith(str(ROOT / "src")), resolved


def test_every_path_and_ref_the_readme_names_resolves() -> None:
    """Clause 2.  A slash-shaped token is a file in this tree or a ref in this repository.

    The control is ``sdk/generator-rebuild``: a branch the "Merging back" section named as
    the destination of the whole rebuild, which no ref resolves and no path holds.
    """
    bad = _unresolved_tokens(README.read_text())
    assert not bad, (
        "README.md names these, and they are neither a path in this tree nor a ref in "
        f"this repository: {bad}"
    )


def test_every_adcp_path_the_readme_spells_imports_or_is_shown_absent(tmp_path) -> None:
    """Clause 3.  Every ``adcp.…`` in the PROSE imports, or a fence shows it absent.

    Three findings in one clause because they are one defect at three stages: a template
    cannot be imported at all; a concrete path that does not import is the same sentence
    after the placeholder was filled in wrongly; and a path the document names as missing
    is a claim about the artifact exactly like the others, so it is executed rather than
    asserted.
    """
    text = README.read_text()
    spelled = sorted(set(ADCP_PATH.findall(text)))
    assert spelled, (
        "README.md spells no `adcp` path. The surface a reader imports from is the "
        "subject of this document; name it."
    )
    templates = [p for p in spelled if "<" in p]
    assert not templates, (
        "README.md spells a path with a placeholder segment, which is the shape that "
        f"shipped false in constraints.py and cannot be checked by importing: {templates}. "
        "Name the modules."
    )
    #: Paths a fence names.  Clause 1 has already EXECUTED every fence, so a path here is
    #: one whose behaviour -- importing, or raising -- the document demonstrates.
    demonstrated = {
        p for body in _fences(text, "python") for p in ADCP_PATH.findall(body)
    }
    prose_only = sorted(set(ADCP_PATH.findall(FENCE.sub("", text))) - demonstrated)
    spelled = prose_only
    if not spelled:
        return  # every path the prose names is one a fence demonstrates
    where, env = _consumer(tmp_path)
    # One subprocess for all of them: each path is resolved as a module import, and a
    # trailing capitalised segment as an attribute of the module it is named under --
    # test_prose_resolves clause 1's rule, over this document's population.
    probe = where / "probe.py"
    probe.write_text(
        "import importlib, sys\n"
        f"paths = {spelled!r}\n"
        "bad = []\n"
        "for p in paths:\n"
        "    try:\n"
        "        importlib.import_module(p)\n"
        "        continue\n"
        "    except ImportError:\n"
        "        pass\n"
        "    head, _, tail = p.rpartition('.')\n"
        "    try:\n"
        "        mod = importlib.import_module(head)\n"
        "    except ImportError as exc:\n"
        "        bad.append(f'{p}: {exc}')\n"
        "        continue\n"
        "    if not hasattr(mod, tail):\n"
        "        bad.append(f'{p}: {head} has no attribute {tail}')\n"
        "print('\\n'.join(bad))\n"
        "sys.exit(1 if bad else 0)\n"
    )
    done = subprocess.run(
        [sys.executable, str(probe)],
        cwd=where,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert done.returncode == 0, (
        "README.md's prose names these, they do not resolve against the installed "
        "package, and no `python` fence demonstrates their absence -- so a reader is "
        f"told about a path with nothing behind the sentence:\n{done.stdout}{done.stderr}"
    )


def test_each_clause_catches_the_prose_it_is_for(tmp_path) -> None:
    """Every clause is shown a defect of its own kind and must report it.

    Perturbed rather than trusted, because each clause's value is exactly its power to
    redden -- and three of the four defects this file was written for were invisible to a
    reader who had read the document many times.
    """
    where, env = _consumer(tmp_path)

    # Clause 1: a fence that imports a name the installed package does not export.
    broken = "from adcp.types.core import NoSuchClassAnywhere\n"
    assert _run(where, env, broken, 900), (
        "clause 1 passed a fence that cannot import -- it is not executing the fence"
    )
    # ... and one that DOES run, so the clause is not simply always red.
    works = "from adcp.types.core import PaginationRequest\n"
    assert not _run(where, env, works, 901), (
        "clause 1 failed a fence that imports cleanly -- the installed package is wrong"
    )

    # Clause 2: the branch that was named and does not exist, and a path that does not.
    assert _unresolved_tokens("merges into `sdk/generator-rebuild` once green") == [
        "sdk/generator-rebuild"
    ]
    assert _unresolved_tokens("see `docs/plan/no-such-file.md`") == [
        "docs/plan/no-such-file.md"
    ]
    # ... and both kinds of real token pass, so the clause is not always red.
    #
    # **THE REF IN THIS CONTROL MUST OUTLIVE EVERY LANE.**  This read `sdk/readme` --
    # the branch the clause was written on -- and went red the moment that branch was
    # deleted at teardown, which is the same defect the clause exists to catch
    # (`sdk/generator-rebuild`, named by the prose and gone) arriving in the control
    # that proves the clause works.  A control citing a transient ref expires on a
    # schedule nobody wrote down.  `main` is the repository's default branch and is the
    # one ref a teardown cannot take.
    assert _unresolved_tokens("see `docs/plan/architecture.md` on `main`") == []

    # Clause 3: the template, by the regex that harvests it.
    assert [p for p in ADCP_PATH.findall("`adcp.types.<domain>`") if "<" in p] == [
        "adcp.types.<domain>"
    ]
    assert ADCP_PATH.findall("`adcp.types.core`") == ["adcp.types.core"]


def test_what_these_clauses_do_not_grade() -> None:
    """The gaps, named with the measurement, so a later reader does not mistake green here
    for "every README claim is checked".

    **A FIGURE IS NOT GRADED.**  "1,625 documents", "503 distinct names", "1,519 of 1,520"
    are re-derived by running an instrument, not by importing something, and a check that
    recomputed them here would be a second implementation of the instrument -- which is
    the duplication that makes two numbers drift.  The README's answer is to name the
    instrument and the population beside every figure, so a reader re-derives rather than
    trusts.  The measured cost of not grading them: the figure that was wrong when this
    file was written was the spike's line count, wrong in both numbers.

    **A POINTER'S CORRECTNESS IS NOT GRADED, only its existence.**  The README attributed
    the ten migration steps to ``docs/plan/rebuild-plan.md``; the file exists, so clause 2
    is green on it, and the ten steps are in ``docs/plan/architecture.md`` §14.  Telling
    those apart needs a reading of what the document is about, which no clause has.

    **A PATH A FENCE CREATES CANNOT BE RESOLVED, and the README is written so none is
    named.**  Clause 2 reads the tree as it stands, so ``uv venv consumer-venv`` followed
    by ``consumer-venv/bin/python`` reports the interpreter as missing -- correctly, in the
    sense that it is missing, and uselessly, in the sense that the line before it is what
    creates it.  Teaching the clause to track what a fence creates is a parser for shell,
    which is a worse thing to own than the rule it would relax.  So the install fence names
    a venv by DIRECTORY (``--python consumer-venv``) and the wheel by GLOB (``dist/*.whl``),
    neither of which is a path claim, and the clause stays strict.

    **A ``bash`` FENCE IS RESOLVED, NOT RUN.**  Measured on this tree:
    ``pytest tests/test_emit.py`` runs over twenty minutes, ``uv sync --all-extras``
    mutates the environment the suite is executing in, and the whole-population emit
    rewrites ``src/adcp/types``.  A gate that did any of those is a gate nobody runs.
    What IS graded is every path those commands name (clause 2), and the import surface
    they produce (clauses 1 and 3).

    This test asserts the one of the three that can be asserted at all: that the bash
    fences are present and were harvested, so "resolved, not run" describes a population
    that exists rather than an empty set.
    """
    text = README.read_text()
    bash = _fences(text, "bash")
    assert bash, "README.md prints no command, so clause 2's harvest over fences is empty"
    harvested = _slashed("".join(f"```bash\n{b}```\n" for b in bash))
    assert harvested, (
        "the bash fences name no path, so nothing in them is resolved by clause 2 and "
        f"this docstring's claim is false: {bash!r}"
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
