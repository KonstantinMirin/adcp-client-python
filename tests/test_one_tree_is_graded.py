"""The two halves of every graded pair come from ONE checkout, and a mixture reddens.

**What this is about, and it is not a build failure.**  Every check in this suite grades a
pair: a class the EMITTER produced and the document it names, read through ``codegen``.
The class half lives in ``adcp`` and the compiler half lives in ``codegen``, and the two
are resolved independently by the import system.  Where they come from different
checkouts the run is still green or red for reasons that look ordinary -- it grades one
tree's emitted classes with another tree's compiler, and the verdict it prints is about
neither tree.  ``adcp-client-python-82m.43`` is the row; it was found by a lane on itself
after four batches.

**WHY IT HAPPENS, measured rather than supposed.**  A sibling worktree's ``.venv`` is the
main checkout's -- a symlink, because the pins are exact and a second 1.4 GB environment
per lane is not free -- and that environment carries an editable install:

    .venv/lib/python3.12/site-packages/__editable__.adcp_emit-0.0.0.pth
        /srv/ws/adcp-client-python/src

``site`` reads that ``.pth`` at interpreter start, so ``adcp`` resolves to the MAIN
checkout from any worktree.  ``codegen`` is not in it -- it is not under ``src`` -- so
``codegen`` resolves from the current directory, which is the worktree.  Two halves, two
trees, one verdict.

**THE PREVENTION IS CONFIGURATION AND IT IS IN ``pyproject.toml``**: ``pythonpath = [".",
"src"]`` under ``[tool.pytest.ini_options]``, which pytest applies in
``pytest_load_initial_conftests`` -- before conftest import and before collection -- and
inserts at the FRONT of ``sys.path``, ahead of the ``.pth``.  Both halves then come from
the rootdir, which is the worktree, whatever the environment holds.  The variable that
used to carry this is still correct and is no longer the only thing carrying it.

**AND THIS FILE IS THE DETECTION, which is a separate obligation from the prevention.**
``docs/plan/final-state.md``: a reading names what decides it, "and that must be something
that fails when the reading fails".  A fix with no instrument on it is one lane away from
regressing silently -- the next ``.pth``, the next ``--import-mode``, the next invocation
that beats pytest to ``sys.path``.  So the pair of halves is read back, in the process
that does the grading, off the one thing that cannot lie about where a module came from:
``__file__``.

**BOTH DIRECTIONS, because a one-directional check is satisfied by a predicate that
always passes.**  ``test_the_two_halves_come_from_one_checkout`` is the green direction and
proves nothing on its own -- ``assert True`` passes it.  The red direction is
``test_the_reading_reddens_on_a_constructed_mixture``, which BUILDS a mixture: two
checkouts in a temporary directory, one holding ``src/adcp`` and one holding ``codegen``,
a child interpreter whose ``sys.path`` resolves one half from each, and the SAME function
this file's green direction calls.  It is proved red by construction and not by argument.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import textwrap

import adcp

import codegen

#: This file, so a child interpreter can import the predicate below rather than restate
#: it.  A restated predicate proves that a copy of the check reddens, which is not the
#: claim.
HERE = pathlib.Path(__file__).resolve()


def checkout_of(module_file: str | None) -> pathlib.Path | None:
    """The checkout a module was imported from: its nearest ancestor holding a project file.

    Derived and not configured.  ``pyproject.toml`` is what makes a directory this
    project's root -- it is what pytest's own rootdir derivation reads, and it is the file
    carrying the ``pythonpath`` that this check exists to watch -- so "the tree a half came
    from" is the nearest ancestor that has one.  ``None`` where there is none, which is an
    import from somewhere that is not a checkout at all and is reported as such rather
    than silently compared equal.
    """
    if module_file is None:
        return None
    for ancestor in pathlib.Path(module_file).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    return None


def the_halves_of_the_graded_pair() -> tuple[pathlib.Path | None, pathlib.Path | None]:
    """Where the class half and the compiler half of this process came from.

    One import each and no derivation beyond ``__file__``, so the reading cannot disagree
    with the import system that produced it.
    """
    return checkout_of(adcp.__file__), checkout_of(codegen.__file__)


def one_checkout_or_the_mixture(
    halves: tuple[pathlib.Path | None, pathlib.Path | None],
) -> None:
    """Raise unless both halves of a graded pair came from the same checkout.

    The whole check, in the one place both directions call it from.
    """
    emitted, compiler = halves
    assert emitted is not None, (
        f"adcp was imported from {adcp.__file__!r}, which is under no checkout: "
        "a graded pair's class half cannot be attributed to a tree"
    )
    assert compiler is not None, (
        f"codegen was imported from {codegen.__file__!r}, which is under no checkout: "
        "a graded pair's compiler half cannot be attributed to a tree"
    )
    assert emitted == compiler, (
        "A MIXTURE OF TWO TREES IS BEING GRADED, so this run's verdict is about neither.\n"
        f"  adcp     (the emitted classes) came from {emitted}\n"
        f"  codegen  (the compiler)        came from {compiler}\n"
        "pyproject.toml's [tool.pytest.ini_options] pythonpath is what prevents this; "
        "see this file's docstring and adcp-client-python-82m.43."
    )


def test_the_two_halves_come_from_one_checkout() -> None:
    """The green direction, in the process that grades the pairs."""
    one_checkout_or_the_mixture(the_halves_of_the_graded_pair())


def _a_checkout(root: pathlib.Path, package: pathlib.Path) -> pathlib.Path:
    """A directory that ``checkout_of`` answers for, holding one importable package."""
    (root / package).mkdir(parents=True)
    (root / package / "__init__.py").write_text("")
    (root / "pyproject.toml").write_text('[project]\nname = "a-constructed-checkout"\n')
    return root


def test_the_reading_reddens_on_a_constructed_mixture(tmp_path: pathlib.Path) -> None:
    """The red direction: build the mixture, run the same check, require it to fail.

    Two checkouts and not one real one, so the proof does not depend on another worktree
    existing on the box or on this box's layout at all.  The child's ``sys.path`` puts the
    emitted half's ``src`` and the compiler half's root in front of everything, which is
    exactly the shape the ``.pth`` produces -- ``adcp`` from one tree, ``codegen`` from
    another -- and then calls this module's own function on it.
    """
    emitted = _a_checkout(tmp_path / "emitted-from-here", pathlib.Path("src/adcp"))
    compiler = _a_checkout(tmp_path / "compiled-by-here", pathlib.Path("codegen"))

    probe = textwrap.dedent(f"""
        import sys
        sys.path[:0] = [{str(emitted / "src")!r}, {str(compiler)!r}, {str(HERE.parent)!r}]
        import {HERE.stem} as check
        halves = check.the_halves_of_the_graded_pair()
        print(halves[0], halves[1], sep="\\n")
        try:
            check.one_checkout_or_the_mixture(halves)
        except AssertionError as red:
            print("REDDENED", red, sep="\\n")
            raise SystemExit(0)
        raise SystemExit("the check passed over a mixture of two trees")
    """)
    ran = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=False
    )
    reported = ran.stdout.splitlines()

    assert ran.returncode == 0, (
        "the constructed mixture did not reach the check:\n"
        f"{ran.stdout}\n{ran.stderr}"
    )
    assert reported[:2] == [str(emitted), str(compiler)], (
        "the child did not resolve the two halves from the two constructed checkouts, "
        f"so the mixture was not built: {reported!r}\n{ran.stderr}"
    )
    assert "REDDENED" in reported, (
        "the check passed over a mixture of two trees, which is the defect it is for: "
        f"{ran.stdout!r}"
    )
    assert "A MIXTURE OF TWO TREES IS BEING GRADED" in ran.stdout
