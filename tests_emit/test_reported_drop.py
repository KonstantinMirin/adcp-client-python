"""§7's reported drop, at EVERY position the keyword occupies.

``docs/plan/rebuild-plan.md`` §7, 2026-10-26: ``errorMessage`` moves to §6 -- "it
customises a validator's message and constrains no instance, so an annotation that omits
it omits no fact.  The drop is reported, as it was." -- and the position rule beside it:

    **The drop is reported at every position the keyword occupies, and not only where a
    conjunct encloses it.** [...] A keyword's effect is a decision about the keyword at a
    position; a report that reaches one position and not another is a defect in the
    channel, not a second decision, and the reading that settles it is the count of
    reported drops naming the keyword -- two, where it is one today.

**Its own module, not an addition to ``tests/test_emit.py``**, for the reason
``tests/test_emit_product.py`` gives: a module per row costs an import and removes the
collision between lanes that would all be editing one file.

**The reading, not a bare count.**  ``media-buy/sync-catalogs-request.json`` is the one
portable document stating ``errorMessage`` and it states it TWICE -- at ``/allOf/1``
beside a ``not``, and at ``/then`` beside a ``required``.  The pointers are read off
``bundle.nodes_at`` -- the one walk -- rather than written here, so a bundle that moves
the keyword moves the expectation with it; what is written here is the KEYWORD, which is
a fact about the corpus and the one name §7 is about.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import fresh
from compiled import compiled

from codegen import bundle, keywords, render
from codegen.lower import names
from nodeset import claimed

#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE

#: The one name §7's row is about.  A fact about the CORPUS -- the bundle states it in one
#: document -- and not a reading of the table: the table's own side of this check is
#: :attr:`keywords.Cell.reported`, asserted over every cell below.
SECTION_7 = "errorMessage"


def _stated(documents: list[str], keywords_wanted: set[str]) -> set[tuple[str, str, str]]:
    """Every ``(document, pointer, keyword)`` the corpus states one of these keys at.

    Over ``bundle.nodes_at`` -- the ONE walk, which carries the position the descent
    column assigned rather than recovering it from a pointer segment -- so a key at
    ``/then`` is found at RULE and a key at ``/allOf/1`` at CONJ, and neither position is
    privileged by the reading.
    """
    return {
        (document, pointer or "/", key)
        for document in documents
        for pointer, node, _ in bundle.nodes_at(bundle.read(BUNDLE, document))
        for key in node
        if key in keywords_wanted
    }


def test_a_reported_drop_reaches_every_position_the_keyword_occupies() -> None:
    """The count of reported drops naming the keyword equals the count of occurrences.

    §7's own settling reading.  Before this row the channel was
    ``lower.composition.lower_composition``'s, which screens CONJ, so the ``/allOf/1`` occurrence
    was reported and the ``/then`` one was reported nowhere -- one note for two
    occurrences, with no reader able to see that the class carries nothing for the
    second.
    """
    documents = sorted(bundle.portable(BUNDLE))
    out = compiled(BUNDLE, documents)
    stated = _stated(documents, {SECTION_7})
    claimed(f"schema positions the corpus states {SECTION_7} at", stated)

    # One note per occurrence, at that occurrence's own pointer, naming that key.  The
    # prefix is the channel's own line shape (``"<pointer>: <name>: <why>"``) and is all
    # this reads: the sentence is the channel's to write.
    notes = {
        (document, line.split(":", 2)[0], line.split(":", 2)[1].strip())
        for document, lines in out.carries_nothing.items()
        for line in lines
        if line.split(":", 2)[1].strip() == SECTION_7
    }
    assert notes == stated, (sorted(notes), sorted(stated))

    # **And the drop is a DROP: nothing on the class answers to the name.**  §2's "a fact
    # is dropped, never substituted" in the direction that can be read off the product --
    # a note saying the class carries nothing for a key is worth nothing if a field
    # carries it anyway.  Over every class each of these documents declared, by the
    # emitter's own field-name rule rather than by the keyword spelled as an attribute.
    #
    # Here rather than in ``test_emit``'s conjunct-contribution clause, which reads the
    # same pair at a CONJ and reaches no document stating ``errorMessage``: its clause 1
    # refuses at ``adagents.json``, which sorts first, so the loop never arrives.
    for document in sorted({d for d, _, _ in stated}):
        module = importlib.import_module(out.emitted[document])
        field = names.field_name(SECTION_7, render.RESERVED)
        for pointer, symbol in sorted(out.declared[document].items()):
            declared = getattr(module, symbol, None)
            fields = getattr(declared, "model_fields", {})
            assert field not in fields, (document, pointer, symbol)
            assert SECTION_7 not in fields, (document, pointer, symbol)


def test_every_cell_whose_drop_is_reported_is_reported_wherever_the_corpus_states_it() -> None:
    """The same reading, over every cell the TABLE says the drop is reported for.

    The declaration's side of the row: ``Cell.reported`` is where the decision lives
    (§7's "a keyword decision lives in the cell"), so the check ranges over the cells and
    not over the one name -- a second keyword given the flag is graded the day it is
    given it.
    """
    reported = {
        keyword
        for keyword in keywords.TABLE
        for position in keywords.Position
        if (answer := keywords.cell(keyword, position)) is not None and answer.reported
    }
    assert reported == {SECTION_7}, sorted(reported)
    # A reported cell states no fact about an instance: the drop is a REPORT and not an
    # approximation, so there is no rung and nothing widens (§2, and `states_a_fact`).
    for keyword in reported:
        for position in keywords.Position:
            answer = keywords.cell(keyword, position)
            assert answer is not None and not keywords.lowers(answer), (keyword, position)
            assert answer.widens_to is None, (keyword, position)

    documents = sorted(bundle.portable(BUNDLE))
    out = compiled(BUNDLE, documents)
    stated = _stated(documents, reported)
    notes = {
        (document, line.split(":", 2)[0], line.split(":", 2)[1].strip())
        for document, lines in out.carries_nothing.items()
        for line in lines
        if line.split(":", 2)[1].strip() in reported
    }
    assert notes == stated, (sorted(notes), sorted(stated))


def test_no_cell_refuses_a_document_on_a_keyword() -> None:
    """§7's title, as a fact the declaration holds rather than a claim its prose makes.

    ``docs/plan/architecture.md`` §3: "§7's projection is now the empty one, because
    ``Effect.REFUSE`` is gone and no row can be in it."  So the member is not merely
    unused -- it does not exist, which is what makes a future "refuse a document on a
    keyword" a compile error instead of a silent path.
    """
    assert not hasattr(keywords.Effect, "REFUSE")
    assert keywords.grid_of(SECTION_7) == keywords.ADMITTED
    assert {keywords.grid_of(k) for k in keywords.TABLE}.isdisjoint({keywords.REFUSED})
