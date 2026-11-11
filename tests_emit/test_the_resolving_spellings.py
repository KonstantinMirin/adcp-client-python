"""§12 of the porting guide is EXECUTED, row by row, and never reviewed.

**WHY THIS FILE EXISTS.**  ``docs/migration-from-upstream.md``'s §12 is a table of
{upstream's word, the emitted class at its own path, the node the document states it at}
over every spelling the alias layer resolves.  Its central claim is an IDENTITY claim --
``adcp.types.<word> is adcp.types.<domain>.<Name>`` -- and an identity claim written in
prose is exactly the kind that ships false: ``tests_emit/test_prose_resolves.py``'s own
docstring records two shipped docstrings that asserted a surface which did not exist, and
"nothing failed while they were false".  A thousand of them cannot be read.  So every row
is run.

**THE ROWS ARE READ OFF THE FILE AND NOT OFF THE GENERATOR.**  The subject here is the
DOCUMENT -- what an adopter reads -- so the table is parsed out of the committed markdown
and each parsed row is executed against the tree.  Grading the generator's return value
instead would pass a stale table written by an older run of it, which is the one failure
this gate is for.

**FOUR CLAUSES.**

1. **Identity.**  For every row: the word resolves at ``adcp.types``, the path resolves at
   its own module, and the two are **the same object** -- ``is``, never ``==`` and never a
   name compare.  A row naming a class of ours whose name merely matches would pass a name
   compare and is the substitution reading 10 refuses.
2. **The count is derived.**  The figures in §12's prose are the number of rows the table
   actually carries, so a hand edit that drops a row or a figure typed by hand reddens.
3. **The table is what a fresh derivation produces.**  ``survey/alias_destinations.decide``
   is re-run and its verdicts must equal the written rows, so a bundle bump that moves an
   emitted name -- which is the whole reason the section says the emitted path is the
   future-proof spelling -- reddens rather than leaving this table quietly behind.
4. **No row asserts a deprecation, and the six failure sections keep their subjects.**  The
   owner's ruling is that §12 is not a deprecation notice: nothing in it is going away.  So
   no row may carry the word, and §1 to §6 must still be present with their own headings,
   after which §12's markers begin.

**AND THE SECTION'S LEAD RECOMMENDATION IS EXECUTED TOO**, because it is guidance rather
than a table and the rest of this file would not touch it.  ``test_the_xor_is_the_payload``
runs the four payloads §12 shows, and ``test_every_xor_node_refuses_both_and_neither``
generalises the two refusals across all eight nodes ``adcp-client-python-j0fr``'s census
names -- with the base payload derived from each base's OWN required set, because a payload
missing a required field is refused for THAT and the sentence under test never appears.
Measured: all eight carry the document's own sentence once the required set is filled, and
six of them do not before it.
"""

from __future__ import annotations

import enum
import importlib
import re
import sys
import typing
from pathlib import Path

import pytest
from nodeset import claimed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "survey"))

import alias_destinations  # noqa: E402

GUIDE = ROOT / "docs" / "migration-from-upstream.md"

#: The six sections that own the FAILING names, by the heading each one carries.  §12 may
#: not displace, renumber or absorb any of them: the owner's ruling makes it a SEPARATE
#: note, and a reader who lands on a breaking change must still land on the section that
#: owns it.
FAILURE_SECTIONS = (
    "## §1. Machinery: 360 names, and upstream's wheel still has every one",
    "## §2. 23 names that resolve nowhere on upstream's own 9.6.1 wheel",
    "## §3. On the type surface, but not a type: 13 names",
    "## §4. On the type surface, with no schema subject: 8 names",
    "## §5. Where upstream's name means something else: 7 names",
    "## §6. The instrument's undecided seven: four the bundle settles, three it does not",
)

#: The document's own sentence for a presence clause no branch satisfies.
#:
#: Asserted on rather than on an exception TYPE, because the point of the clause is that the
#: XOR is the DOCUMENT's and the refusal says so.  A ``ValidationError`` for a missing field
#: is also a ``ValidationError``.
XOR_REFUSAL = "the document admits exactly one"


def section_text() -> str:
    """§12, between its markers, refusing the case where the markers are gone."""
    text = GUIDE.read_text(encoding="utf-8")
    assert alias_destinations.BEGIN in text, "§12's opening marker is not in the guide"
    _, _, rest = text.partition(alias_destinations.BEGIN)
    body, _, _ = rest.partition(alias_destinations.END)
    assert body.strip(), "§12 is empty between its markers"
    return body


#: One written row: the word, the path, the node, and the rest of the last column.
ROW = re.compile(
    r"^\| `(?P<word>[^`]+)` \| `(?P<path>adcp\.types\.[^`]+)` \| "
    r"`(?P<node>[^`]+)` \| (?P<rest>.*) \|$"
)


def written_rows() -> list[dict[str, str]]:
    """Every row of §12's table, parsed out of the committed markdown."""
    rows = [
        match.groupdict()
        for match in (ROW.match(line) for line in section_text().splitlines())
        if match is not None
    ]
    return rows


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    """The written rows, CLAIMED -- an empty table would satisfy every clause below.

    The set is named by its WORDS, which is also the uniqueness assertion: a flat namespace
    cannot hold one word twice, so a table carrying a word twice is a derivation defect and
    the count would be read off a set smaller than the rows.
    """
    parsed = sorted(written_rows(), key=lambda row: row["word"])
    words = claimed("rows written in §12 of the porting guide", [row["word"] for row in parsed])
    assert len(words) == len(parsed), "§12 carries one word on two rows"
    return parsed


@pytest.fixture(scope="module")
def derived() -> dict[str, object]:
    """One fresh derivation, shared: ``decide`` imports the whole generated tree."""
    return alias_destinations.decide()


def test_every_row_is_one_object_under_two_names(rows: list[dict[str, str]]) -> None:
    """Clause 1: the word, the path, and ``is``.

    The two halves are resolved INDEPENDENTLY -- ``getattr`` on the flat facade, which runs
    ``adcp.types.__getattr__``'s whole precedence order, and an import of the domain module
    named in the row -- and then compared by identity.  Nothing about the derivation is
    consulted: this is the claim a reader of the row would check.
    """
    types_module = importlib.import_module("adcp.types")
    failures: list[str] = []
    for row in rows:
        try:
            through_alias = getattr(types_module, row["word"])
        except AttributeError:
            failures.append(f"{row['word']}: does not resolve at adcp.types")
            continue
        module_path, _, name = row["path"].rpartition(".")
        try:
            at_path = getattr(importlib.import_module(module_path), name)
        except (ImportError, AttributeError) as error:
            failures.append(f"{row['word']}: {row['path']}: {type(error).__name__}: {error}")
            continue
        if through_alias is not at_path:
            failures.append(
                f"{row['word']}: adcp.types.{row['word']} is not {row['path']} "
                f"({through_alias!r} vs {at_path!r})"
            )
    assert not failures, "\n".join(failures)


def test_every_row_names_the_node_the_compiler_recorded(rows: list[dict[str, str]]) -> None:
    """Clause 1, second half: the document and pointer are the compiler's own record.

    A row's third column is not decoration -- it is what makes the right-hand spelling "the
    document's" rather than another word of ours -- so it is read back off the object the
    row resolves to, through the same two readings the generator uses.
    """
    types_module = importlib.import_module("adcp.types")
    failures: list[str] = []
    for row in rows:
        obj = getattr(types_module, row["word"])
        record, _ = alias_destinations.record_of(obj)
        if record is None:
            failures.append(f"{row['word']}: no __adcp_schema__ of its own")
            continue
        node = record.document + record.pointer
        if node != row["node"]:
            failures.append(f"{row['word']}: row says {row['node']}, the record says {node}")
    assert not failures, "\n".join(failures)


def test_the_row_count_in_the_prose_is_the_number_of_rows(rows: list[dict[str, str]]) -> None:
    """Clause 2: every figure §12 states for its own size is the table's own size.

    Three sentences carry it, and all three are read rather than one: a generator writing
    the heading from one derivation and a sentence from another is the drift this catches.
    """
    body = section_text()
    stated = f"{len(rows):,}"
    for claim in (
        f"**{stated} that WORK**",
        f"### How the {stated} rows were derived",
        f"**{stated} reach a class this compiler emitted**",
    ):
        assert claim in body, f"§12 does not state its own size as {stated!r} at: {claim!r}"


def test_the_written_table_is_what_a_fresh_derivation_produces(
    rows: list[dict[str, str]], derived: dict[str, object]
) -> None:
    """Clause 3: the committed table equals the derivation, in both directions.

    Reported as the two differences BY NAME rather than as a count mismatch, because "1,077
    != 1,076" tells a reader nothing about which spelling moved.
    """
    claimed("rows a fresh derivation produces", [row["word"] for row in derived["rows"]])
    fresh = {row["word"]: (row["path"], row["node"]) for row in derived["rows"]}
    written = {row["word"]: (row["path"], row["node"]) for row in rows}
    assert not (set(fresh) - set(written)), (
        "the derivation produces rows §12 does not carry: "
        f"{sorted(set(fresh) - set(written))[:20]}"
    )
    assert not (set(written) - set(fresh)), (
        "§12 carries rows the derivation does not produce: "
        f"{sorted(set(written) - set(fresh))[:20]}"
    )
    moved = {word: (written[word], fresh[word]) for word in written if written[word] != fresh[word]}
    assert not moved, f"rows whose path or node moved: {sorted(moved)[:20]}"


def test_no_row_asserts_a_deprecation(rows: list[dict[str, str]]) -> None:
    """Clause 4, first half: the owner's ruling, as a check.

    "Nothing here is going away, and an adopter who changes nothing keeps working."  A row
    carrying the word would say the opposite of the section it is in, and the last column
    is where such a mark would land.
    """
    offenders = [
        row["word"]
        for row in rows
        if "deprecat" in (row["rest"] + row["path"] + row["node"]).lower()
    ]
    assert not offenders, f"rows reading as a deprecation: {offenders}"


def test_the_six_failure_sections_keep_their_subjects() -> None:
    """Clause 4, second half: §12 is a separate note and displaces nothing."""
    text = GUIDE.read_text(encoding="utf-8")
    for heading in claimed("the six failure-section headings", FAILURE_SECTIONS):
        assert heading in text, f"a failure section lost its heading: {heading!r}"
    assert text.index(alias_destinations.BEGIN) > max(
        text.index(heading) for heading in FAILURE_SECTIONS
    ), "§12 is written before one of the six sections it is separate from"


def _required_payload(base: type) -> dict[str, object]:
    """A payload carrying every field the BASE requires and no branch key.

    **DERIVED FROM THE MODEL'S OWN REQUIRED SET**, which is how the owner measured it, and
    the reason it is derived rather than written: a payload missing a required field is
    refused FOR THAT, with pydantic's sentence and not the document's, so the clause under
    test would never be reached.  Measured on six of the eight nodes.
    """
    out: dict[str, object] = {}
    for name, field in base.model_fields.items():
        if not field.is_required():
            continue
        annotation = field.annotation
        if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            out[name] = next(iter(annotation)).value
        elif annotation is str:
            out[name] = "x"
        elif typing.get_origin(annotation) is dict:
            out[name] = {}
        elif "datetime" in getattr(annotation, "__name__", str(annotation)).lower():
            out[name] = "2026-01-01T00:00:00Z"
        else:  # pragma: no cover -- a new required annotation is a finding, not a skip
            raise AssertionError(f"{base.__name__}.{name}: no value for {annotation!r}")
    return out


def test_the_xor_is_the_payload_and_not_the_caller(derived: dict[str, object]) -> None:
    """§12's lead recommendation, executed: the four payloads it prints.

    ``creative/list-creatives-response.json#/properties/creatives/items`` is the node the
    section shows, and this is that code block run.  The two keys are read off the base's
    own ``_BRANCH_PRESENCE`` rather than typed, so a document that renames one moves this
    test with it.
    """
    bases = alias_destinations.presence_classes()["bases"]
    node = "creative/list-creatives-response.json#/properties/creatives/items"
    base = claimed("the node §12's recommendation is written from", [bases.get(node)]).pop()
    assert base is not None
    branches = dict(base._BRANCH_PRESENCE)
    payload = _required_payload(base)
    values = {
        "format_id": {"agent_url": "https://creative.example.com", "id": "banner_300x250"},
        "format_kind": "image",
    }
    for branch, clause in branches.items():
        key = clause.require[0][0]
        got = base.model_validate({**payload, key: values[key]})
        assert type(got).__name__ == branch, f"{key} alone selected {type(got).__name__}"
    with pytest.raises(Exception) as both:
        base.model_validate({**payload, **values})
    assert XOR_REFUSAL in str(both.value)
    with pytest.raises(Exception) as neither:
        base.model_validate(payload)
    assert XOR_REFUSAL in str(neither.value)


def test_every_xor_node_refuses_both_and_neither() -> None:
    """The same clause over all eight nodes, which is what makes it the DATA MODEL's.

    The admitting half needs a valid value per branch key and those are the document's
    business; the two REFUSALS need no branch value at all, so they generalise across the
    set and are the half worth stating once for AdCP 3.2-3.3 rather than for one node.
    """
    bases = alias_destinations.presence_classes()["bases"]
    found = claimed(
        "presence XOR nodes", sorted(bases), inside=alias_destinations.PRESENCE_XOR_NODES
    )
    # **A SET IDENTITY AND NOT A COUNT**, which `nodeset.py` is explicit about: "an equality
    # on a count is one bundle version's reading of a quantity every emitting row moves."
    # The members are the obligation here -- j0fr's census names eight NODES, and the claim
    # is that each of those eight dispatches this way, reported by name when one does not.
    missing = set(alias_destinations.PRESENCE_XOR_NODES) - found
    assert not missing, f"nodes j0fr's census names that do not dispatch on a key set: {missing}"
    for node, base in sorted(bases.items()):
        payload = _required_payload(base)
        keys = sorted(
            {
                key
                for _, clause in base._BRANCH_PRESENCE
                for group in clause.require
                for key in group
            }
        )
        for label, extra in (("every branch key", dict.fromkeys(keys)), ("no branch key", {})):
            with pytest.raises(Exception) as refusal:
                base.model_validate({**payload, **extra})
            assert XOR_REFUSAL in str(refusal.value), (
                f"{node}: {label} was not refused by the clause"
            )
