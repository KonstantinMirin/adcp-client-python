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

import ast
import importlib
import pathlib

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


def test_a_keyword_with_no_row_is_the_only_answer_that_refuses_by_name() -> None:
    """``None`` is the WHOLE of "refused by name" now.

    It was one of two: a key with no row, and a key whose cell said ``REFUSE``.  §7 is
    empty and the effect is retired (§14 step 8), so a key the table GIVES a row is
    admitted whatever that row says -- ``errorMessage`` was the last ``REFUSE`` cell and
    is NOTHING, with its drop reported (``tests/test_reported_drop.py``).
    """
    assert cell("multipleOfNothing", Position.ROOT) is None
    # A key with no row DECLARES: the screen can refuse on it, because a keyword the
    # bundle did not use before could constrain anything.
    assert keywords.declares("multipleOfNothing", Position.ROOT)
    assert cell("errorMessage", Position.ROOT).effect is Effect.NOTHING
    assert not keywords.declares("errorMessage", Position.ROOT)
    # **And there is no effect for a cell to refuse WITH**, which is what retiring it
    # buys: a future "refuse a document on a keyword" is a name error here rather than a
    # silent path.  Asserted on the enum's own membership, so an effect added back under
    # any spelling of the old name reddens.
    assert "REFUSE" not in Effect.__members__


def test_the_folded_set_is_the_rendered_column_and_names_no_keyword_twice() -> None:
    """The set the document-side FOLD ranges over EQUALS the set the declaration renders.

    Asserted against the verifier's own reading rather than against a list here, so
    the two cannot be the same literal written twice.  ``harness.FOLDED_FACTS`` is the
    set at ROOT, which is the position every fold is entered at.
    """
    from codegen import harness

    assert set(harness.FOLDED_FACTS) == keywords.rendered_at(Position.ROOT)
    # Ordered by the DECLARATION, so a fold's reading order is the table's.
    assert list(harness.FOLDED_FACTS) == [
        k for k in keywords.TABLE if k in keywords.rendered_at(Position.ROOT)
    ]
    at_prop = claimed("keywords a faithful model renders at a property", keywords.rendered_at(Position.PROP))
    # A keyword the model RENDERS is never one it only holds: structure is read by
    # descending it, which is the descent column's job.
    for keyword in at_prop:
        answer = cell(keyword, Position.PROP)
        assert answer.effect is not Effect.NOTHING or keyword == "x-", keyword
    # A cell whose DROP IS REPORTED renders nothing: the keyword constrains no instance,
    # so there is no fact for a fold to carry and a note is the whole answer.
    # (It read "a REFUSE cell renders nothing, because no model exists for the document
    # to grade" until §7's set emptied; the population is the same one cell and the
    # reason it renders nothing is now the cell's own rather than the document's loss.)
    reported = claimed(
        "cells whose drop is reported",
        {
            (keyword, position)
            for keyword in keywords.TABLE
            for position in Position
            if (answer := cell(keyword, position)) is not None and answer.reported
        },
    )
    for keyword, position in reported:
        answer = cell(keyword, position)
        assert not answer.rendered, (keyword, position)
        assert keyword not in keywords.rendered_at(position), (keyword, position)


def test_a_refusals_kind_comes_from_the_cell_and_not_from_a_raise_site() -> None:
    """§3 of the architecture document, as the two answers the TABLE gives.

    A key with no row is a VERDICT -- the obstruction belongs to the document, which did
    not have to carry a keyword the bundle never used.  A cell with a lowering effect
    whose handler has no code for the shape yet is a DEFERRAL, which is §9's first rule:
    minting a verdict for unwritten code reports clearable work as finished.  A cell that
    carries nothing is admitted and mints nothing.

    **There were THREE and the first one went with ``Effect.REFUSE``** (§14 step 8): "a
    key whose cell is REFUSE is a VERDICT".  ``errorMessage`` was the last cell saying it
    and left this assertion the way ``version`` left it before -- for the same reason, the
    third answer rather than a looser second one.
    """
    from codegen import compiler, refusal

    # ``errorMessage`` and ``version`` are both NOTHING now and both mint NOTHING: asking
    # for a kind is asking a question no site asks, because the screen ADMITS such a key
    # and it never reaches a refusal.  Asserted as the admission, which is the fact that
    # replaced the kind in each case.
    for admitted in ("errorMessage", "version"):
        assert cell(admitted, Position.ROOT).effect is Effect.NOTHING, admitted
        assert not lowers(cell(admitted, Position.ROOT)), admitted
    # No row at all: a keyword the bundle did not use before, which is the document's
    # own property and so a verdict.
    assert compiler.kind_for("nosuchkeyword", Position.ROOT) is refusal.Kind.VERDICT
    # A lowering effect with no handler for it: the obstruction is unwritten code.
    assert compiler.kind_for("multipleOf", Position.PROP) is refusal.Kind.DEFERRED
    assert compiler.kind_for("contains", Position.MAPV) is refusal.Kind.DEFERRED
    # A per-position override: ``enum`` LOWERS at every position the walk decides a node
    # at, so every one of them is a deferral where the handler has no code for the shape.
    # **The KEY entry was the one REFUSE cell at one position only, and
    # ``adcp-client-python-10l.20`` retired it**: §5's group (a) makes a `Literal` of the
    # members the key type, which pydantic renders back as the document's own
    # ``propertyNames: {enum: […]}``, so the cell is a TYPE there like everywhere else and
    # no position of this row refuses.  What the per-position shape is still graded on is
    # that the two positions differ in their SENTENCE, which the grid round-trip asserts.
    assert compiler.kind_for("enum", Position.KEY) is refusal.Kind.DEFERRED
    assert compiler.kind_for("enum", Position.PROP) is refusal.Kind.DEFERRED
    assert cell("enum", Position.KEY).effect is Effect.TYPE
    assert cell("enum", Position.KEY).rendered
    assert cell("enum", Position.KEY).compiles != cell("enum", Position.PROP).compiles


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
    assert set(bundle.DESCENDS) == declared, sorted(set(bundle.DESCENDS) ^ declared)
    assert "dependencies" not in declared
    # Every keyword of the column is reached by the walk at a node that states it, so
    # the shape declaration (:data:`bundle.HELD_BY_NAME`, :data:`HELD_IN_A_LIST`)
    # covers the column rather than a part of it.
    for keyword, position in bundle.DESCENDS.items():
        held = {"properties": {"x": {}}, "patternProperties": {"^x$": {}},
                "definitions": {"x": {}}, "$defs": {"x": {}}}.get(keyword)
        if held is None:
            held = [{}, {}] if keyword in bundle.HELD_IN_A_LIST else {}
        reached = list(bundle.subschemas({keyword: held}))
        assert reached, keyword
        assert {at for _, _, _, at in reached} == {position}, (keyword, reached)


# --------------------------------------------------------------------------- #
# §3's monopoly: "nothing else in codegen/ names a keyword in a set literal"
# --------------------------------------------------------------------------- #
#: **Every site that still names draft-07 keywords in a collection, with the reason it is
#: not the table's to decide** (``adcp-client-python-3be.8``).  Keyed by module and by the
#: SORTED keywords, never by line number, so the gate survives an edit above it.
#:
#: §3 states the monopoly as "nothing else in ``codegen/`` names a keyword in a set
#: literal", and that sentence is FALSE at the sites below -- by construction and not by
#: neglect.  Every one of them is a HANDLER'S COVERAGE: the set it passes
#: ``compiler.check_keywords`` as ``handled``, which that function's own docstring calls
#: "the caller's own COVERAGE and no longer an admission list ... the set of cells that
#: handler writes".  The table cannot hold it, and the test of that is the table's own
#: shape: it is keyed by keyword × POSITION and carries no column for a node KIND, so
#: "which handler has code for this LOWERED cell" is not a fact in it.  ``properties`` at
#: PROP is TYPE for the object row and TYPE for the mapping row, and only one of the two
#: writes it.
#:
#: What the table DOES decide about these sites is held by the two tests below: no entry
#: may name a keyword the table admits for free, and no site may appear that is not here.
#: Both directions, because a membership check in one direction is complete with respect
#: to itself (§3's own reason for generation over diffing).
#:
#: **Ten sites left the census on this row and the removals are listed on the bead**: the
#: verifier's three descent tuples, its combinator arm and its value-class arms now read
#: the descent column; the ordering keywords are :data:`keywords.RANGES`, read by both
#: halves; ``compiler._CONTAINER_KEYWORDS`` is
#: :func:`keywords.constrains_container`; and the root-sibling tuple is written once.
_SURVIVING_SITES: dict[tuple[str, tuple[str, ...]], str] = {
    ("codegen.compiler", ("additionalProperties", "properties", "propertyNames", "required", "type")):
        "lower_object's coverage: the cells an OBJECT node's handler writes.  "
        "patternProperties, minProperties, maxProperties and dependencies are LOWERED "
        "cells at the same position that this handler has no code for, which is what "
        "makes them deferrals -- so the set is the handler's and not the position's.",
    ("codegen.compiler", ("properties", "required", "type")):
        "INLINE: what an allOf CONJUNCT may carry and still be an inline object "
        "declaring fields.  additionalProperties is absent on purpose (D8 derives extra "
        "from the root's), which is a decision about this reader and not about the "
        "keyword's cell.",
    ("codegen.compiler", ("additionalProperties", "allOf", "properties", "required", "type")):
        "COMPOSING: what the composing node itself may carry beside its conjunct list.  "
        "D6's rule families are deliberately NOT here and are added per node by "
        "rules_at, because the admissible set is a function of the node.",
    ("codegen.lower.const", ("const", "format", "type")):
        "const.CLAIMS: the cells a Constant node consumes.  format is claimed because "
        "§5's const row decides it AT THE PIN -- 'a format beside the pin compiles to "
        "NOTHING' -- and this handler is where that reading lives.",
    ("codegen.lower.containers", ("allOf", "contains", "items", "type", "uniqueItems")):
        "_ARRAY_CLAIMS: the cells the ARRAY row writes, plus the bounds it spreads in "
        "derived.  allOf is claimed because §5's $ref row at CONJ makes a container its "
        "node's own type, so an array stating an allOf is this row's to read.",
    ("codegen.lower.containers", ("additionalProperties", "patternProperties", "propertyNames", "type")):
        "containers.mapping's coverage: the cells a MAPPING node consumes.  properties "
        "is absent because a node declaring one is an Object and not a Mapping, which "
        "is the parser's classification and not a cell.",
    ("codegen.lower.containers", ("$ref", "anyOf", "enum", "maxLength", "minLength", "pattern", "type")):
        "KEY_CLAIMS: §5's propertyNames row read as a claim set -- the FIVE answers that "
        "row gives a KEY, plus the `type: string` the PARSER supplies there.  The table "
        "cannot hold it for this test's own reason: it is keyed by keyword x POSITION and "
        "carries no column for a node KIND, and the five are what the KEY arm writes "
        "while an OBJECT key node is a cell no handler has code for -- §4 derives no name "
        "at KEY for one to be declared under (adcp-client-python-zxf).",
    ("codegen.harness", ("additionalProperties", "patternProperties", "propertyNames")):
        "harness.refused_witnesses' object arm: the three keywords whose far-side witness "
        "is an UNDECLARED KEY, which is one perturbation and not three.  §9 forbids the "
        "verifier the walk and permits it the keyword table, and the table answers which "
        "cell each keyword compiles to -- not which PERTURBATION of an instance each one "
        "names, which is a fact about the witness and so is the verifier's.",
    ("codegen.lower.rules", ("properties", "required", "type")):
        "rules._clauses: the keys an `if` may carry and still reduce to a Match clause "
        "list.  A SHAPE constraint on one subschema at the RULE position -- an `if` "
        "stating anything else reduces to nothing rather than to something stronger "
        "than the document -- so it is a predicate over one node, not a claim set.",
    ("codegen.lower.union", ("additionalProperties", "allOf", "properties", "required", "type")):
        "ROOT_CLAIMS: what a ROOT union node may carry, ordered so the keyword each "
        "refused document is reported on is the one that is the reason.  Its own comment "
        "measures the misattribution at 55 of 156 documents before the four were "
        "claimed here.",
    ("codegen.lower.union", ("additionalProperties", "allOf", "const", "enum", "properties", "required", "type")):
        "BRANCH_CLAIMS: what a BRANCH may carry and still be a class this module "
        "declares.  const and enum are claimed to put the explicit refusal below in "
        "front of the screen's generic one, which is attribution and not admission.",
    ("codegen.lower.union", ("$ref", "const", "enum")):
        "_CLASSIFIED_BEFORE_AN_OBJECT: the keywords §5's ARM ORDER classifies a node on "
        "before it reads properties, so a branch stating one is not an Object node.  "
        "A fact about the parser's dispatch order (lower/decide.py), which §5 owns and "
        "the keyword table does not.",
    ("codegen.schema.nodes", ("additionalProperties", "allOf", "properties", "required")):
        "ROOT_SIBLINGS: the keywords a root states BESIDE a combinator, which §3 calls a "
        "CO-OCCURRENCE and not a position -- 'the table is keyed by position and a "
        "co-occurrence is not one' -- so the four cells carry the SENTENCE and this "
        "layer carries the shape.  Written once: parse fills Union.siblings from it and "
        "lower.union.ROOT_CONJUNCTS is it.",
}


def audit_modules() -> dict[str, pathlib.Path]:
    """Every first-party module under audit, by the AUDIT's own enumeration."""
    from survey import arch_audit

    return arch_audit.modules()


def _census() -> list[tuple[str, int, bool, tuple[str, ...]]]:
    """The census, from the AUDIT's own derivation and not a second one.

    ``survey/arch_audit.py keywords`` is the instrument §3 is measured by, and a census
    printed by one reader and gated by another is how seven of this epic's censuses went
    stale.  So the audit exports the derivation and this test is a reader of it.
    """
    from survey import arch_audit

    return arch_audit.keyword_collections()


def test_the_keyword_set_literal_census_is_the_sites_named_here() -> None:
    """§3's monopoly, as the census the architecture audit derives -- in BOTH directions.

    A new set literal of keywords anywhere under ``codegen/`` fails here, and so does a
    site in :data:`_SURVIVING_SITES` that no longer exists: the entry has to be deleted
    with the code, or the reason outlives the thing it was about.  Line numbers are not
    part of the key, so an edit above a site does not redden it.
    """
    found: dict[tuple[str, tuple[str, ...]], int] = {}
    for module, _line, _keys, hits in _census():
        found[(module, tuple(sorted(hits)))] = found.get((module, tuple(sorted(hits))), 0) + 1
    sites = claimed("keyword collections outside codegen/keywords.py", found)
    unnamed = sites - set(_SURVIVING_SITES)
    assert not unnamed, (
        "a new site names keywords in a collection outside codegen/keywords.py; §3 says "
        "the table is the one place a keyword decision lives.  Derive it from a reader of "
        "codegen.keywords, or add it to _SURVIVING_SITES with the reason the table cannot "
        f"hold it: {sorted(unnamed)}"
    )
    gone = set(_SURVIVING_SITES) - sites
    assert not gone, (
        "_SURVIVING_SITES names a site that no longer exists -- delete the entry with the "
        f"code it was about: {sorted(gone)}"
    )
    doubled = {k: n for k, n in found.items() if n > 1}
    assert not doubled, (
        "one module names the same keywords in two collections, which is the repetition "
        f"inside a single reader: {sorted(doubled)}"
    )


#: The two screens ``codegen/compiler.py`` exposes, whose ``handled`` argument IS a
#: handler's claim set.  Named because the derivation below has to find the CALLS, and
#: there are exactly two functions §3's lowering reader goes through.
_SCREENS = {"check_keywords": 1, "check_declaration": 3}


def _claimed_at_every_screen() -> dict[tuple[str, int], frozenset[str]]:
    """Every keyword named in a ``handled`` argument, per call site -- from the SOURCE.

    AST for the call sites and the live module for the names they pass, so a claim set
    reaches this whether it is spelled inline (``{"type"}``), as a module constant
    (``ROOT_CLAIMS``), or as both with a derived set spread beside it
    (``ROOT_CLAIMS | {kw} | stated.screen``).  A derived operand nothing can resolve
    statically -- ``stated.screen``, ``node.facts`` -- contributes nothing and needs to:
    it is already a reader of the table (``compiler.rules_at``, ``parse.value_facts``),
    which is the thing this test is checking FOR.

    Derived and not listed, because a claim set the test does not reach is a claim set
    with no gate, and a list of call sites is the second place to go stale.
    """
    out: dict[tuple[str, int], set[str]] = {}
    for name, path in sorted(audit_modules().items()):
        if not name.startswith("codegen"):
            continue
        tree = ast.parse(path.read_text())
        live = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            spelled = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            at = _SCREENS.get(spelled)
            if at is None or len(node.args) <= at:
                continue
            if live is None:
                live = importlib.import_module(name)
            found: set[str] = set()
            for sub in ast.walk(node.args[at]):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    found.add(sub.value)
                    continue
                held = None
                if isinstance(sub, ast.Name):
                    held = getattr(live, sub.id, None)
                elif isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name):
                    owner = getattr(live, sub.value.id, None)
                    held = getattr(owner, sub.attr, None) if owner is not None else None
                if isinstance(held, (set, frozenset, tuple, list)) and all(
                    isinstance(x, str) for x in held
                ):
                    found |= set(held)
            if found:
                out.setdefault((name, node.lineno), set()).update(found)
    return {site: frozenset(kws) for site, kws in out.items()}


def test_no_claim_set_names_a_keyword_the_table_admits_for_free() -> None:
    """Every keyword a handler CLAIMS has a cell the screen could have refused on.

    This is the half of §3 the table CAN hold about a handler's coverage, and it is the
    bead's "every keyword a module screens is read from the table" in the one direction a
    claim set can be read in.  ``compiler._screen`` asks ``handled`` FIRST and then the
    cell, so a claimed keyword whose cell does not LOWER at any position is an
    entry the screen would have passed over anyway: a leftover from when these sets were
    ADMISSION lists, which §14 step 5 says is "the table's answer now and is gone from all
    of them".  Such an entry reads as a decision about the keyword, and the table has
    already made the only one there is.

    **The predicate had a second clause until §14 step 8** -- "neither LOWERS nor
    REFUSES" -- and it covered one claim: ``lower_composition`` handed the screen the
    names whose cell said ``REFUSE``, so that the drop it had just reported was not then
    refused on.  §7 is empty and no cell can refuse, so LOWERING is the whole of what a
    claim can be about.

    **It found one**: ``lower.enum.CLAIMS`` claimed ``default``, whose cell is ANNOTATION
    everywhere and FIELD at PROP -- never TYPE or RULE -- while the comment beside it said
    the parent carries it ("all 66 of the bundle's enum defaults are inline").  The entry
    is gone and this is what forbids its return.

    It ranges over the SCREEN CALLS and not over the census, which is the difference that
    matters: the census has a floor of three names
    (:data:`survey.arch_audit.FLOOR`) and ``enum.CLAIMS`` is two names now, so a census
    reader would have stopped seeing it exactly when the defect was removed.
    """
    sites = _claimed_at_every_screen()
    claimed("screen call sites with a resolvable claim set", sites)
    free: list[tuple[str, int, str, list[str]]] = []
    for (module, line), keywords_claimed in sorted(sites.items()):
        for keyword in sorted(keywords_claimed):
            answers = [cell(keyword, p) for p in Position]
            if any(a is not None and lowers(a) for a in answers):
                continue
            effects = sorted({str(a.effect).split(".")[-1] for a in answers if a is not None})
            free.append((module, line, keyword, effects or ["NO ROW"]))
    assert not free, (
        "a handler claims a keyword the table admits at every position, so claiming it "
        "decides nothing and compiler._screen passes it over either way; delete the "
        f"entry: {free}"
    )


def test_the_census_is_blind_to_a_collection_naming_an_unlisted_keyword() -> None:
    """**The instrument's own reach, asserted so it is read rather than assumed.**

    ``survey/arch_audit.py``'s census counts a collection only where EVERY element is in
    its ``DRAFT07`` list, so one element outside that list drops the whole site -- and the
    list is incomplete: it has no ``multipleOf``, ``additionalItems``, ``contentMediaType``
    or ``contentEncoding``.  Measured on this tree, two sites are invisible for that reason
    (``codegen.ir:FACTS``, whose own comment already admits §11 wants it derived, and
    ``harness._PAD_FORBIDS``), and a third was at the base of this row
    (``compiler._CONTAINER_KEYWORDS``'s array set, which named ``additionalItems``).

    Completing ``DRAFT07`` would move the census number every lane reads off that command,
    so it is not done here: this test is the blind spot WRITTEN DOWN, and it reddens if the
    list is completed -- which is the point at which the sites it hides need rows of their
    own.  ``adcp-client-python-3be.8`` reports it.
    """
    from survey import arch_audit

    missing = claimed(
        "draft-07 keywords the census's own list does not carry",
        {k for k in keywords.TABLE if k not in arch_audit.DRAFT07}
        & {"multipleOf", "additionalItems", "contentMediaType", "contentEncoding"},
    )
    assert missing == {"multipleOf"}, (
        "the census's DRAFT07 list changed; re-measure which collections it now sees and "
        f"name them in _SURVIVING_SITES or derive them: {sorted(missing)}"
    )
    hidden = sorted(
        {
            module
            for module, path in arch_audit.modules().items()
            if module.startswith("codegen") and module != "codegen.keywords"
            for node in ast.walk(ast.parse(path.read_text()))
            if (elements := getattr(node, "elts", None) or getattr(node, "keys", None))
            and (
                vals := [
                    e.value
                    for e in elements
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
            )
            and len([v for v in vals if v in arch_audit.DRAFT07]) >= arch_audit.FLOOR
            and len([v for v in vals if v in arch_audit.DRAFT07]) != len(vals)
        }
    )
    assert hidden == ["codegen.harness", "codegen.ir"], hidden
