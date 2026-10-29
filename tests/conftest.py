"""Suite-wide options, the binding that decides WHICH TREE is graded, and the one
assertion every file that grades a refusal shares.

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

import pytest

from codegen.refusal import Refusal


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
