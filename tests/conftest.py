"""Suite-wide options.

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


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--write-grids",
        action="store_true",
        default=False,
        help="rewrite the generated grids of docs/plan/rebuild-plan.md from "
        "codegen/keywords.py (tests/test_keywords.py owns the regions)",
    )
