"""The declaration, and the grids it GENERATES in the semantics document.

``docs/plan/architecture.md`` §3: sections 5, 6 and 7 of ``docs/plan/rebuild-plan.md``
are GENERATED from ``codegen/keywords.py``, and this file is both the generator and the
assertion that the committed document matches what the table generates.

**Generation rather than a diff.**  A diff can only compare what it can parse back out
of a table, so a cell deciding one thing where the sentence beside it says another
passes a membership diff.  It cannot pass generation, which WRITES the cell's sentence.
What is removed is the second copy of the *what*; the reasoning paragraphs around each
grid are hand-written, are what generation cannot produce, and are outside the markers.

**The generator lives HERE.**  Not in ``keywords.py``: §11 gives that layer positions,
keywords, cells and descent and denies it text, so a module rendering markdown is not
that layer.  Not an entry point either: §10's rule is that no module of the compiler is
ever bound as ``__main__``, so there is no ``python -m codegen.keywords`` and the
compiler does not write its own documentation.

**When a cell deliberately changes**, write the regions through:

    PYTHONPATH=. uv run --no-sync python -m pytest tests/test_keywords.py --write-grids

which rewrites the lines between each marker pair and nothing else.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from codegen import keywords
from codegen.keywords import ADMITTED, GRIDS, REFUSED, Cell, Effect, Position, cell, lowers
from tests.nodeset import claimed

PLAN = pathlib.Path(__file__).resolve().parents[1] / "docs" / "plan" / "rebuild-plan.md"

BEGIN = "<!-- generated from codegen/keywords.py -->"
END = "<!-- end generated -->"

#: The column header each grid is written under.  TEXT, so it is the generator's and
#: not the table's (§11).  Sections 6 and 7 head their one column differently because
#: they answer a different question about the same cell.
HEADERS = {
    ADMITTED: "| keyword | what it does, or why nothing |",
    REFUSED: "| keyword | why |",
}
DEFAULT_HEADER = "| keyword | compiles to |"


# --------------------------------------------------------------------------- #
# the generator: a reader of the table, and the only writer of the marked regions
# --------------------------------------------------------------------------- #
def line_of(keyword: str) -> str:
    """One row as its grid line, by §3's render rule.

    The default cell's ``compiles``, then one clause per position override in
    :class:`Position` declaration order; overrides whose ``compiles`` is identical are
    one clause and their positions are joined with ``" / "``.  A clause is the joined
    position names followed by the cell's own ``compiles``, which carries its leading
    separator -- so an irregular clause (``ROOT beside a union → …``, ``RULE: under
    `if` → …``) is the cell's sentence and not a shape imposed on it.  An override
    whose ``compiles`` is empty renders NO clause: it records a cell the default
    sentence already covers, which is what a co-occurrence that is not a position
    needs.
    """
    row = keywords.TABLE[keyword]
    order = list(Position)
    groups: dict[str, list[Position]] = {}
    for position in order:
        answer = row.at.get(position)
        if answer is None or not answer.compiles:
            continue
        groups.setdefault(answer.compiles, []).append(position)
    clauses = [
        f"{' / '.join(p.value for p in positions)}{compiles}"
        for compiles, positions in groups.items()
    ]
    return " ".join(x for x in (row.default.compiles, *clauses) if x)


def grid(name: str) -> list[str]:
    """One grid: its header and one line per group of rows that render identically.

    Rows sharing a line are ONE line with their keywords joined, which is the shape
    sections 5, 6 and 7 are already written in -- ``minLength``, ``maxLength`` under
    one answer, ``readOnly``, ``writeOnly`` under another.  :attr:`Row.label` gives
    the keyword column where it is prose rather than a list of names, which is the two
    lines that stand for a whole namespace.
    """
    lines = [HEADERS.get(name, DEFAULT_HEADER), "| --- | --- |"]
    grouped: dict[tuple[str, str | None], list[str]] = {}
    for keyword in keywords.TABLE:
        if keywords.grid_of(keyword) != name:
            continue
        grouped.setdefault((line_of(keyword), keywords.TABLE[keyword].label), []).append(keyword)
    for (rendered, label), names in grouped.items():
        column = label or ", ".join(f"`{n}`" for n in names)
        lines.append(f"| {column} | {rendered} |")
    return lines


def regions(text: str) -> list[tuple[int, int]]:
    """Every marked region in the document, as ``(first line of the body, end)``.

    The generator owns the lines BETWEEN the markers and nothing else, so the markers
    themselves are outside every slice this file writes.
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == BEGIN]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    assert len(starts) == len(ends), (starts, ends)
    return list(zip([i + 1 for i in starts], ends, strict=True))


def written(text: str) -> str:
    """The document with every marked region replaced by the grid it generates."""
    lines = text.splitlines()
    out: list[str] = []
    cut = 0
    for (start, end), name in zip(regions(text), GRIDS, strict=True):
        out += lines[cut : start]
        out += grid(name)
        cut = end
    out += lines[cut:]
    return "\n".join(out) + "\n"


def test_the_committed_grids_are_what_the_table_generates(pytestconfig) -> None:
    """§3's two directions in one test: the grids are the table's output, and the
    committed document is that output.

    ``--write-grids`` is the affordance for a cell that has DELIBERATELY changed: it
    writes the marked regions and nothing else, so a cell change that was not written
    through to the document is a failing test rather than a silent divergence, and
    writing it through costs one flag instead of a hand edit nobody can verify.
    """
    text = PLAN.read_text()
    want = written(text)
    if pytestconfig.getoption("--write-grids"):
        PLAN.write_text(want)
        return
    assert text == want, (
        "docs/plan/rebuild-plan.md's generated grids are not what codegen/keywords.py "
        "generates; run pytest tests/test_keywords.py --write-grids if the cell change "
        "is deliberate"
    )


def test_every_grid_has_a_region_and_every_region_a_grid() -> None:
    """One marker pair per grid, in the document's own order.

    The pairing is positional, so a region added or removed without a grid beside it
    reddens here rather than silently shifting every grid after it into the wrong
    section.
    """
    found = regions(PLAN.read_text())
    assert len(found) == len(GRIDS), (len(found), GRIDS)
    lines = PLAN.read_text().splitlines()
    for (start, _), name in zip(found, GRIDS, strict=True):
        assert lines[start] == HEADERS.get(name, DEFAULT_HEADER), (name, lines[start])


def test_every_row_renders_into_exactly_one_grid() -> None:
    """The three sections PARTITION the table, which is what makes them projections.

    A row reaching no grid would be a decision nothing publishes; a row reaching two
    would be the second copy generation exists to remove.
    """
    reached = claimed(
        "rows that render into a grid",
        {k for k in keywords.TABLE if keywords.grid_of(k) in GRIDS},
        inside=set(keywords.TABLE),
    )
    assert reached == set(keywords.TABLE), sorted(set(keywords.TABLE) - reached)
    # Section 5's sub-grid is DECLARED and sections 6 and 7's are derived, so a
    # section 5 row with no family is a row with no line and a section 6 or 7 row with
    # one is a declaration nothing reads.
    for keyword, row in keywords.TABLE.items():
        where = keywords.grid_of(keyword)
        if where in (ADMITTED, REFUSED):
            assert row.grid == "", (keyword, row.grid)
        else:
            assert where in keywords.SECTION_5, (keyword, where)


def test_every_keyword_the_bundle_carries_has_a_row() -> None:
    """Section 7's last rule, measured against the bundle rather than asserted.

    "A keyword in none of §5, §6 or §7 is one the bundle does not use.  The first
    document to carry one refuses by name, so a new keyword is loud rather than
    ignored."  The table is the document's, so this is the one direction worth
    checking: a key the bundle states and the table does not name would refuse every
    document carrying it, and the refusal would be the table's defect rather than the
    document's.
    """
    from pathlib import Path

    from codegen import bundle

    root = Path("schemas/cache/3.2")
    carried = claimed(
        "keys the bundle states at a schema position",
        {
            key
            for document in bundle.portable(root)
            for _, node in bundle.nodes(bundle.read(root, document))
            for key in node
        },
    )
    assert carried <= set(keywords.TABLE), sorted(carried - set(keywords.TABLE))


def test_a_prefixed_key_with_no_row_is_admitted_and_reported() -> None:
    """The ``x-`` namespace rule, both halves.

    The prefix admits by SHAPE, because a vendor extension cannot be a schema keyword;
    the names are kept as well because the prefix rule dropped ``x-enum-descriptions``
    silently once, and that key carries member docstrings.
    """
    assert keywords.admitted_by_prefix("x-whatever-nobody-has-seen")
    assert keywords.unlisted_extension("x-whatever-nobody-has-seen")
    # A listed one is admitted by NAME and is not reported: it has a row, and the row
    # is what says it carries nothing.
    assert not keywords.unlisted_extension("x-entity")
    assert cell("x-entity", Position.PROP) == Cell(
        Effect.NOTHING, False, None, keywords._X_COMPILES
    )
    # ``x-enum-descriptions`` is the leak the list exists for: it is in the namespace
    # and it CARRIES something, so it is an annotation and not metadata.
    assert cell("x-enum-descriptions", Position.ROOT).effect is Effect.ANNOTATION
    assert not keywords.unlisted_extension("x-enum-descriptions")


def test_a_keyword_with_no_row_is_the_answer_that_refuses_by_name() -> None:
    """``None`` and not a REFUSE cell: the two refuse for different reasons."""
    assert cell("multipleOfNothing", Position.ROOT) is None
    assert cell("errorMessage", Position.ROOT).effect is Effect.REFUSE


def test_the_compared_set_is_the_rendered_column_and_names_no_keyword_twice() -> None:
    """Section 8's one check above the three: the comparison's keyword set EQUALS the
    set the declaration renders.

    Asserted against the verifier's own reading rather than against a list here, so
    the two cannot be the same literal written twice.
    """
    from codegen import harness

    for position in Position:
        assert set(harness.compared_facts(position)) == keywords.rendered_at(position), position
        # Ordered by the DECLARATION, so a report's line order is the table's.
        assert list(harness.compared_facts(position)) == [
            k for k in keywords.TABLE if k in keywords.rendered_at(position)
        ], position
    at_prop = claimed("keywords a faithful model renders at a property", keywords.rendered_at(Position.PROP))
    # A keyword the model RENDERS is never one it only holds: structure is graded by
    # descending it, which is the descent column's job.
    for keyword in at_prop:
        answer = cell(keyword, Position.PROP)
        assert answer.effect is not Effect.NOTHING or keyword == "x-", keyword
    # A REFUSE cell renders nothing, because no model exists for the document to grade.
    for keyword in keywords.TABLE:
        for position in Position:
            answer = cell(keyword, position)
            if answer.effect is Effect.REFUSE:
                assert not answer.rendered, (keyword, position)


def test_a_refusals_kind_comes_from_the_cell_and_not_from_a_raise_site() -> None:
    """§3 of the architecture document, as the three answers the cell gives.

    A ``REFUSE`` cell is a VERDICT -- the obstruction belongs to the document.  A cell
    with a lowering effect whose handler has no code for the shape yet is a DEFERRAL,
    which is §9's first rule: minting a verdict for unwritten code reports clearable
    work as finished.  A cell that carries nothing is admitted and mints nothing.
    """
    from codegen import compiler, refusal

    assert compiler.kind_for("errorMessage", Position.ROOT) is refusal.Kind.VERDICT
    # **``version`` LEFT this assertion at ``adcp-client-python-10l.20``, and the reason
    # is the third answer rather than a looser second one.**  The registry data keys are
    # NOTHING at every position now (section 6 of the semantics document, section 3 of the
    # architecture document), so they mint NOTHING -- which is this docstring's own third
    # case -- and asking for a kind is asking a question no site asks: a NOTHING key is
    # ADMITTED by the screen and never reaches a refusal.  Asserted as the admission,
    # which is the fact that replaced the kind.
    assert cell("version", Position.ROOT).effect is Effect.NOTHING
    assert not lowers(cell("version", Position.ROOT))
    # No row at all: a keyword the bundle did not use before, which is the document's
    # own property and so a verdict.
    assert compiler.kind_for("nosuchkeyword", Position.ROOT) is refusal.Kind.VERDICT
    # A lowering effect with no handler for it: the obstruction is unwritten code.
    assert compiler.kind_for("multipleOf", Position.PROP) is refusal.Kind.DEFERRED
    assert compiler.kind_for("contains", Position.MAPV) is refusal.Kind.DEFERRED
    # And a REFUSE cell at ONE position only is a verdict THERE and a deferral where
    # the row lowers, which is the whole point of the cell being per position.
    assert compiler.kind_for("enum", Position.KEY) is refusal.Kind.VERDICT
    assert compiler.kind_for("enum", Position.PROP) is refusal.Kind.DEFERRED


def test_the_descent_column_is_the_one_the_bundles_walk_descends_by() -> None:
    """``bundle``'s walk READS the descent column, which §11 makes it the owner of.

    The row that declared the column asserted the two AGREED, because ``bundle`` then
    held three descent literals of its own.  Row .3's inliner needed the same descent
    to place a reference's target, and two descents in one module is what §11 names as
    the repetition -- so the literals are gone and ``bundle.subschemas`` reads the
    column.  What is left to assert is that the reading is the column and nothing
    beside it, in both directions, and that the walk really reaches a node at every
    keyword the column carries.

    The four draft-2019 keywords ``bundle`` used to descend and the table has no row
    for -- ``prefixItems``, ``dependentSchemas``, ``additionalItems``,
    ``unevaluatedProperties``, ``unevaluatedItems`` -- have **0 sites in the 3.2
    bundle**, measured, so dropping them changed no census.  ``dependencies`` has 27
    sites and descends in neither reading: draft-07 lets it hold a schema, this
    bundle's 27 hold a list of names, and the table gives it no descent.
    """
    from codegen import bundle

    declared = claimed(
        "keywords the table says hold a subschema",
        {k for k in keywords.TABLE if any(
            (c := cell(k, p)) is not None and c.descends is not None for p in Position
        )},
    )
    assert set(bundle._DESCENDS) == declared, sorted(set(bundle._DESCENDS) ^ declared)
    assert "dependencies" not in declared
    # Every keyword of the column is reached by the walk at a node that states it, so
    # the shape declaration (:data:`bundle._HELD_BY_NAME`, :data:`_HELD_IN_A_LIST`)
    # covers the column rather than a part of it.
    for keyword, position in bundle._DESCENDS.items():
        held = {"properties": {"x": {}}, "patternProperties": {"^x$": {}},
                "definitions": {"x": {}}, "$defs": {"x": {}}}.get(keyword)
        if held is None:
            held = [{}, {}] if keyword in bundle._HELD_IN_A_LIST else {}
        reached = list(bundle.subschemas({keyword: held}))
        assert reached, keyword
        assert {at for _, _, _, at in reached} == {position}, (keyword, reached)
