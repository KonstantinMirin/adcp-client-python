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
import re
import subprocess
import sys
import tokenize
import tomllib
from pathlib import Path

import pytest

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
    """
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["mypy"]["files"]
    out: list[Path] = []
    for entry in config:
        path = ROOT / entry
        out.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return [p for p in out if "__pycache__" not in p.parts]


def test_the_decision_layer_type_checks_clean() -> None:
    """§14 step 6's gate, run.

    The invocation takes no arguments: ``[tool.mypy]`` carries the file list, so the
    command here is the command a reader runs and there is no second population.
    """
    mypy = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if "No module named mypy" in mypy.stderr:
        pytest.skip("no type checker installed; §14 step 6's gate is the checker itself")
    assert mypy.returncode == 0, mypy.stdout + mypy.stderr


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
