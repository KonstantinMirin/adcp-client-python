"""§14 step 6's own gate: **the type checker IS the test** for the decision layer.

``docs/plan/architecture.md`` §14 step 6 is "Refusal as a value.  ``Refusal`` stops
subclassing ``Exception``; every handler returns ``Lowering | Refusal``; ``first_refusal``
replaces the try/except in ``lower_document``; ``lower_document`` returns a value to the
run.  **The type checker is the test.**"  §2 says what it tests: "The type checker
therefore refuses a caller that reads a ``Lowering`` field off a result without handling
the ``Refusal`` branch, which is the mechanical form of the semantics document's §9 rule
that a crash is not an outcome."

So the gate is not "the handlers were converted" -- that is what
``tests/test_import_rule.py``'s AST guard grades -- it is that NO CALLER anywhere in the
decision layer reads a decision off a result that may be a refusal.  No review and no
structural guard can say that: it is a question about every expression in 5,000 lines,
and a checker is the instrument for it.

**``mypy`` is an instrument and not a dependency**, which is why this skips rather than
fails where it is absent: the artifact this project produces is a function of the bundle
and of a PINNED compiler (D10), and a checker is in neither argument.  Where it IS
installed this is a hard gate -- the configuration it reads is ``[tool.mypy]`` in
``pyproject.toml``, which names the files and the two missing type surfaces it is allowed
not to know, so the run here and a run by hand grade the same thing.

**The second clause is what makes the first mean anything.**  A checker with every error
suppressed is green for free, so the three suppressions §14 step 6 names -- ``cast``,
``type: ignore`` and an ``assert isinstance`` standing in for a branch -- are counted over
the same files and asserted to be zero.  The third is counted by AST and not by grep,
because ``isinstance`` in an ``if`` IS the branch the design asks for and only an
``assert`` of one is the stand-in.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tokenize
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: An inline suppression, by the spelling a checker reads: the pattern is anchored to the
#: START of a comment, which is where a checker looks for it.  ``type: ignore`` is mypy's
#: and ``pyright: ignore`` is the other checker's, named so that swapping instruments does
#: not swap which suppressions are counted.
#:
#: Anchored, and read off COMMENT TOKENS rather than off the text, because this repository
#: writes the rule down: a module explaining why it no longer carries one quotes the
#: spelling in prose, and a detector matching anywhere in a file reports the explanation
#: as the thing it forbids.  ``tokenize`` is what tells a comment from a docstring, and
#: the anchor is what tells a suppression from a sentence about one.
SUPPRESSIONS = (re.compile(r"^#\s*type:\s*ignore"), re.compile(r"^#\s*pyright:\s*ignore"))


def _graded() -> list[Path]:
    """The files ``[tool.mypy]`` ranges over, read from the configuration itself.

    Read rather than restated, so the checker's population and this test's cannot come
    apart: a row that adds a module to the gate adds it in one place.

    ``exclude`` is applied for the same reason ``files`` is read: it is the other half of
    the one statement of what the checker ranges over, and a population computed from
    ``files`` alone would report the emitted tree as graded when the checker does not
    crawl it.
    """
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["mypy"]
    excluded = re.compile(config["exclude"]) if "exclude" in config else None
    out: list[Path] = []
    for entry in config["files"]:
        path = ROOT / entry
        out.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return [
        p
        for p in out
        if "__pycache__" not in p.parts
        and not (excluded and excluded.search(p.relative_to(ROOT).as_posix()))
    ]


#: The documented invocation's environment, and it is LOAD-BEARING rather than a
#: convenience.  mypy builds its search path from ``sys.path``, so ``src`` on
#: ``PYTHONPATH`` is what makes ``adcp.*`` resolve to this checkout -- and this is a
#: worktree whose ``.venv`` carries an editable install pointing at a DIFFERENT one, so
#: without it the package the gate reads is not the package in the tree.  Measured both
#: ways on the same commit: with it, clean over 60 files; without it, 216 errors, all of
#: them in the emitted tree that ``exclude`` keeps out of the crawl.  Set here rather than
#: inherited from however pytest was launched, so the gate's verdict is a function of the
#: tree and not of the shell.
INVOCATION = {"PYTHONPATH": f".{os.pathsep}src"}


def test_the_decision_layer_type_checks_clean() -> None:
    """§14 step 6's gate, run.

    The invocation takes no arguments: ``[tool.mypy]`` carries the file list, so the
    command here is the command a reader runs and there is no second population.

    **An absent checker is an ERROR and not a skip**, and the sentence is
    ``docs/plan/final-state.md``'s: no check is marked expected-to-fail, skipped, or
    scoped away from the code it is about.  ``mypy`` is still not a dependency and is
    still not pinned -- the artifact is a function of the bundle and of a PINNED compiler
    (D10), and a checker is in neither argument -- but a gate that disappears together
    with its own instrument REPORTS GREEN, which is the one failure mode this project
    bans everywhere else.  The two statements are compatible: the checker is not needed
    to BUILD the artifact and is needed to GRADE it, so its absence is a missing
    instrument rather than a passing run.
    """
    mypy = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **INVOCATION},
    )
    assert "No module named mypy" not in mypy.stderr, (
        "no type checker installed, and §14 step 6's gate IS the checker: "
        "`pip install mypy` and run `PYTHONPATH=.:src python -m mypy --no-incremental`"
    )
    assert mypy.returncode == 0, mypy.stdout + mypy.stderr


def test_the_package_declares_its_types_to_a_consumer() -> None:
    """Reading 7: "The package declares its types to a consumer's type checker."

    PEP 561 is a two-part promise and BOTH parts are read here, because either one alone
    is worse than neither: a marker in the tree that packaging drops makes the promise to
    every reader of the repository and keeps it for no consumer, and a ``package-data``
    entry naming a file that does not exist builds a wheel with nothing in it.

    What the absence cost was measured against the INSTALLED package and not the source
    tree, which is the only place it is visible: ``Skipping analyzing
    "adcp.types.core": module is installed, but missing library stubs or py.typed
    marker``, then ``Revealed type is "Any"``, and a consumer file misusing a field and
    an enum member passing silently.  The source tree is readable with or without the
    marker, which is exactly why the gap survived every check this suite already had.
    """
    assert (ROOT / "src" / "adcp" / "py.typed").is_file(), (
        "PEP 561's marker is absent, so a consumer's checker resolves every annotation "
        "this compiler derives to `Any`"
    )
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["setuptools"][
        "package-data"
    ]
    assert "py.typed" in declared.get("adcp", ()), (
        "`py.typed` is in the tree and not in [tool.setuptools.package-data], so the "
        "wheel is built without it and the promise is made to readers alone"
    )


def test_the_decision_layer_holds_no_suppression_the_gate_would_hide() -> None:
    """The control: a clean checker over suppressed code says nothing.

    Three spellings, each one §14 step 6 names:

    * ``cast`` -- asserting a type the checker cannot see, which is how a ``Refusal``
      branch gets asserted away rather than handled.  Counted as a CALL, so the word in
      a docstring or in a comment about the rule is not a hit.
    * ``type: ignore`` / ``pyright: ignore`` -- an error declared uninteresting.
    * ``assert isinstance(...)`` -- the branch written as an assertion.  An ``if
      isinstance(...)`` is the branch the design asks for and is not counted; an
      ``assert`` of one says "this cannot be the other branch", which is the claim §9
      forbids ("a crash is not an outcome": an assertion that fails names nothing).
    """
    casts: dict[str, int] = {}
    ignores: dict[str, int] = {}
    asserted: dict[str, list[int]] = {}
    for path in _graded():
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        with path.open("rb") as handle:
            comments = [
                token.string
                for token in tokenize.tokenize(handle.readline)
                if token.type is tokenize.COMMENT
            ]
        found = sum(
            1 for comment in comments for pattern in SUPPRESSIONS if pattern.match(comment)
        )
        if found:
            ignores[rel] = found
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                named = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                    node.func, "id", ""
                )
                if named == "cast":
                    casts[rel] = casts.get(rel, 0) + 1
            if (
                isinstance(node, ast.Assert)
                and isinstance(node.test, ast.Call)
                and getattr(node.test.func, "id", "") == "isinstance"
            ):
                asserted.setdefault(rel, []).append(node.lineno)

    assert casts == {}, f"{casts}: §14 step 6 admits no cast over the decision layer"
    assert ignores == {}, f"{ignores}: §14 step 6 admits no inline suppression"
    assert asserted == {}, (
        f"{asserted}: an `assert isinstance` stands in for the branch §2 asks for -- a "
        "handler that may have been handed a Refusal returns it, and an assertion that "
        "it was not names no document, pointer or keyword when it fails"
    )


def test_the_gate_ranges_over_the_decision_layer_and_not_a_corner_of_it() -> None:
    """The second control: a checker over three files is green for free too.

    So the configured population is asserted to CONTAIN the layer the row is about --
    ``codegen/refusal.py``, the one dispatch, every handler under ``codegen/lower/``, the
    parser, the shared machinery and the run.  By path and not by count, because the
    handlers are a closed set (§4's node table) and a count would go stale the first time
    one is added.
    """
    graded = {str(p.relative_to(ROOT)) for p in _graded()}
    required = {
        "codegen/refusal.py",
        "codegen/compiler.py",
        "codegen/emit.py",
        "codegen/schema/parse.py",
        "codegen/schema/nodes.py",
        "codegen/lower/decide.py",
        *(
            f"codegen/lower/{m}.py"
            for m in (
                "composition",
                "const",
                "containers",
                "enum",
                "objects",
                "references",
                "rules",
                "scalars",
                "union",
            )
        ),
    }
    assert required <= graded, sorted(required - graded)


def test_the_gate_ranges_over_the_shipped_PACKAGE_and_cannot_be_narrowed_back() -> None:
    """The third control, and it is the one the configuration failed.

    ``[tool.mypy] files`` omitted ``src/adcp`` ENTIRELY while the test above asserted a
    required set naming only ``codegen`` paths -- so a guard written against exactly this
    evasion left the shipped package free to sit outside the gate, which it did.  **The
    shipped package is in scope by definition: it is the artifact every reading is
    about**, and an annotation a consumer's checker cannot be shown to read is not a
    derived type, it is a comment.

    Computed from the TREE and not restated, for the reason the ``codegen`` set gives and
    one more: a domain module per bundle domain is a closed set the bundle decides, so a
    list here would go stale the first time upstream adds a domain, and the module would
    enter the package OUTSIDE the gate -- which is the same hole one level down.

    ``src/adcp/types/_schemas`` is the one subtraction and it is not a corner of the
    package, it is the EMITTED TREE: ``architecture.md``'s "The subject of grading is a
    FRESH EMIT, never the committed tree" -- "The committed tree is an ARTIFACT, verified
    by one byte-compare, and is never the subject."  A type error in a generated module is
    a defect of ``codegen/render.py``, which IS graded here, and ``pyproject.toml``
    carries the count, the breakdown and the row that owns it rather than treating the
    exclusion as free.
    """
    graded = {str(p.relative_to(ROOT)) for p in _graded()}
    emitted = ROOT / "src" / "adcp" / "types" / "_schemas"
    required = {
        str(p.relative_to(ROOT))
        for p in (ROOT / "src" / "adcp").rglob("*.py")
        if "__pycache__" not in p.parts and emitted not in p.parents
    }
    assert required, "src/adcp holds no hand-written module, which cannot be right"
    assert required <= graded, sorted(required - graded)
