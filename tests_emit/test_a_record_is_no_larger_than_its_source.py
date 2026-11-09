"""READING 5'S DECIDER: no record exceeds its source document by more than the
references it resolves.

``docs/plan/final-state.md`` reading 5 states the artifact -- "A document of record stores
each distinct subtree once and references it at every occurrence" -- and names ONE thing
that decides it: **the record's own size**.  That size had no check.
``tests/test_fragment_ref.py::test_a_record_states_each_distinct_subtree_once`` grades the
reading's FIRST SENTENCE as a property of the text; this file is the sentence under it, and
the two together are the reading.  Neither implies the other: the property is blind to how
many bytes one copy costs, and a size is blind to which subtree the bytes are.

**WHY THE SIZE IS NOT REDUNDANT, measured** (``adcp-client-python-lzzj.5``).  The row was
filed on a record node of 10,286,634 bytes out of a 5.4 MB bundle, and asked whether that
is still true.  It is not: the largest record is 1,495,302 bytes and the set is 45,006,973
against 54,098,247 bytes of resolved references.  But the figure was not re-derivable from
any check in the suite -- the property above was green throughout -- so the only answer
available to the question "how big is a record" was a bead written twenty-five merges ago.
A reading whose decider is not instrumented is a reading answered from recollection.

**AND THE BOUND IS DERIVED FROM THE RAW BUNDLE, WHICH IS WHAT MAKES IT DECIDE ANYTHING.**
``bundle.resolves`` charges one copy per distinct subtree the references name -- a stating
site together with what the referring node states beside it -- and consults no record.
Charged per ``$ref`` OCCURRENCE instead, the 365,030,691-byte tree record
``bundle.recorded``'s docstring measures would have MET its bound, and
``final-state.md``'s own rule is that "a check that passes when nothing happens decides
nothing".

**AND IT PAYS FOR THE BOOKKEEPING READING 5'S OWN FIRST SENTENCE REQUIRES**, which is
``bundle.storage_bookkeeping`` and is argued there.  Measured without that term: 32 of the
1,059 records are over the bound, every one of them by its storage's own entry names and
references and NOT by a subtree stated twice -- so the decider would have been red on the
mechanism the sentence above it mandates, and reddest where that mechanism works hardest.
The term is an allowance and not a licence, which the third check below proves by
construction: a record that writes the references AND keeps the copies is still red.

**AND IT IS CHEAP, which is a requirement and not a remark.**  Measured over all 1,059
documents: 10 s, one record alive at a time.  A reading whose gate is too expensive to run
in merge verification is how a stranded floor went unnoticed through six merges.
"""

from __future__ import annotations

import json
from collections.abc import Collection
from pathlib import Path

from adcp.types import _base
from codegen import bundle
from codegen.refusal import Refusal
from fresh import BUNDLE

DRAFT = "http://json-schema.org/draft-07/schema#"

#: The base the constructed bundle below spells its references with: a version nobody
#: publishes, so a reference that escaped the resolver could not reach the network.
BASE = "https://adcontextprotocol.org/schemas/9.9.9/"


def excess(bundle_dir: Path, document: str, known: Collection[str], record: dict) -> int:
    """How many bytes ``record`` is OVER reading 5's bound.  ``<= 0`` is the reading.

    Each term is one declaration in ``codegen.bundle`` and each is the reading's own
    words: the source document, the record, :func:`bundle.resolves` for "the references it
    resolves", and :func:`bundle.storage_bookkeeping` for "stores each distinct subtree
    once under its own ``definitions`` ... and references it at every occurrence".  All of
    them in :func:`bundle.compact`'s format-neutral spelling, because ``emit`` writes the
    record at ``indent=2`` and a reading about duplication must not become a reading about
    indentation.
    """
    source = bundle.compact(bundle.read(bundle_dir, document))
    return (
        bundle.compact(record)
        - bundle.storage_bookkeeping(record)
        - (source + bundle.resolves(bundle_dir, document, known))
    )


def test_no_record_exceeds_its_source_by_more_than_the_references_it_resolves() -> None:
    """READING 5'S DECIDER, over every portable document of the bundle a run reads.

    The subject is the record a FRESH build produces (``bundle.recorded``), which is what
    ``emit`` writes into the package; the committed tree is held to that same text by
    ``test_the_committed_tree_is_what_a_fresh_run_emits``, so one byte-compare carries the
    artifact and this carries the reading.

    A :class:`Refusal` is not a failure here: a record the bundle leaves undefined has no
    size to grade, and ``emit`` is where that refusal is reported.
    """
    known = frozenset(bundle.portable(BUNDLE))
    over: list[tuple[int, float, str]] = []
    graded = 0
    for document in sorted(known):
        answer = bundle.recorded(BUNDLE, document, known)
        if isinstance(answer, Refusal):
            continue
        graded += 1
        by = excess(BUNDLE, document, known, answer[0])
        if by > 0:
            source = bundle.compact(bundle.read(BUNDLE, document))
            over.append((by, bundle.compact(answer[0]) / max(source, 1), document))
    assert graded, "no record was graded, so this check decided nothing"
    worst = "\n".join(
        f"  {by:>10,} bytes over, {ratio:6.2f}x its source: {name}"
        for by, ratio, name in sorted(over, reverse=True)[:20]
    )
    assert not over, (
        f"{len(over)} of {graded} records exceed their source document by more than the "
        f"references they resolve, by {sum(by for by, _, _ in over):,} bytes in total:\n"
        f"{worst}"
    )


def _bundle(tmp_path: Path, documents: dict[str, dict]) -> tuple[Path, frozenset[str]]:
    """A bundle directory holding exactly ``documents``, and its document set."""
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root, frozenset(documents)


#: A subtree big enough that a reference to it is the shorter text, which is what makes
#: duplicating it visible in the bytes at all.
BIG = {
    "type": "object",
    "properties": {
        "alpha": {"type": "string", "minLength": 3, "maxLength": 64},
        "beta": {"type": "integer", "minimum": 0, "maximum": 1000},
        "gamma": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
    },
    "required": ["alpha"],
    "additionalProperties": False,
}

#: Eight properties naming ONE target, so a tree-shaped record holds eight copies of it
#: and the bound charges one.
HOST = {
    "type": "object",
    "properties": {f"held{i}": {"$ref": f"{BASE}core/big.json"} for i in range(8)},
    "additionalProperties": False,
}


def _tree_shaped(doc: dict, target: dict) -> dict:
    """``doc`` with every reference replaced by its own copy of ``target``: the record
    this reading refuses, built here rather than argued about."""
    return {
        key: {name: dict(target) if "$ref" in sub else sub for name, sub in value.items()}
        if key == "properties"
        else value
        for key, value in doc.items()
    }


def test_the_reading_reddens_on_a_record_that_states_one_subtree_twice(
    tmp_path: Path,
) -> None:
    """THE RED DIRECTION, and it is proved by construction rather than by argument.

    One document naming one target from eight properties.  The record this package builds
    holds that target ONCE and references it at the other seven occurrences; a record that
    copied it eight times is the 365,030,691-byte tree in miniature.  Both are handed to
    the same :func:`excess`, and the reading separates them.
    """
    root, known = _bundle(tmp_path, {"core/host.json": HOST, "core/big.json": BIG})
    answer = bundle.recorded(root, "core/host.json", known)
    assert not isinstance(answer, Refusal), answer
    assert excess(root, "core/host.json", known, answer[0]) <= 0, (
        "the record this package builds is already over the bound, so the construction "
        "below would prove nothing"
    )
    duplicated = _tree_shaped(bundle.read(root, "core/host.json"), {"$schema": DRAFT, **BIG})
    by = excess(root, "core/host.json", known, duplicated)
    assert by > 0, (
        "a record stating one subtree eight times is inside reading 5's bound, so the "
        f"bound admits the duplication it exists to refuse (excess {by})"
    )


def test_the_bookkeeping_allowance_does_not_buy_a_duplicated_subtree(
    tmp_path: Path,
) -> None:
    """``bundle.storage_bookkeeping`` IS AN ALLOWANCE AND NOT A LICENCE.

    The bound forgives the bytes a record spends naming and referencing its stored
    subtrees, because reading 5's first sentence requires both.  The question that leaves
    open is whether a record can BUY duplication with it -- write the section and the
    references, and keep the copies anyway.  It cannot, and the reason is arithmetic rather
    than a convention: every byte the allowance forgives is a byte the record spent, so a
    reference is worth exactly what it costs and the copy it failed to remove is charged in
    full.  Constructed here instead of argued: a tree-shaped record with a storage section
    bolted on top of it is MORE over the bound than the same record without one, not less.
    """
    root, known = _bundle(tmp_path, {"core/host.json": HOST, "core/big.json": BIG})
    duplicated = _tree_shaped(bundle.read(root, "core/host.json"), {"$schema": DRAFT, **BIG})
    plain = excess(root, "core/host.json", known, duplicated)
    entry = _base.store_entry(0)
    padded = {
        **duplicated,
        "properties": {
            **duplicated["properties"],
            "padding": {"$ref": _base.store_ref(entry)},
        },
        _base.STORE_SECTION: {entry: {"type": "string"}},
    }
    bought = excess(root, "core/host.json", known, padded)
    assert plain > 0, "the construction is not over the bound, so it proves nothing"
    assert bought > 0, (
        "a record bought its way inside reading 5's bound by writing storage it does not "
        f"use, so the allowance is a licence (excess {bought})"
    )
    assert bought >= plain, (
        "writing an unused storage entry made a duplicating record LOOK smaller, so the "
        f"allowance pays more than it costs ({bought} < {plain})"
    )
