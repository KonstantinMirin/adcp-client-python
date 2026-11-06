"""THE OVERRIDE TABLE IS GRADED AGAINST THE BUNDLE, never against itself.

``docs/plan/architecture.md``, "THE JUDGMENT IS DATA, NEVER CODE": the only question
collection and generation do not answer is whether two identical-looking types are one
subject, the answer lives in a declared table, and **"every entry carries the upstream
defect it compensates for and the ask filed against it -- an entry with no named defect is
not a judgment, it is a preference, and it does not belong in the table."**

So this file asks three things of the table, and each of them is answered from the
published bundle rather than from the table's own text:

1. **every entry names a defect and an ask**, which ``codegen.patch`` refuses at load, so
   the assertion here is that the refusal is reachable and that both patch sets pass it;
2. **every entry's verdict is one the bundle's own evidence supports** -- the judgment pass
   (``tests/judgment.py``) re-derives it from ``catalogue.Admitted`` and
   ``bundle.named_nodes``, and an entry whose verdict the pass does not reach is a
   preference however well it reads;
3. **an override fails the day its ask lands.**  An extraction's clause is already graded
   by ``test_patch_8525.py``; an ADDITION has no document for that clause to range over,
   so its clause is the keyword arriving at the node, and it is checked by asking the
   published bundle for a node that already carries one.

**THE TABLE'S SIZE IS A DEBT FIGURE AND THE RATCHETS RUN THAT WAY.**  Every count below
may fall and may not rise: an entry whose ask upstream accepts is deleted, and a new entry
is a new local answer to a question the protocol should have answered.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from codegen import bundle, catalogue, emit, keywords, patch
from tests.judgment import COLLAPSE, OWNED, ask_for, judged, table
from tests.nodeset import claimed, partitions, ratchet

#: The published bundle every verdict is read off.
PUBLISHED = Path("schemas/cache/3.2")
#: Every patch set of this repository, derived from the directory and never listed: a patch
#: set a lane added and this file did not learn about is the one thing a written list here
#: could hide.
PATCH_SETS = tuple(sorted(p for p in Path("patches").iterdir() if (p / patch.MANIFEST).is_file()))


@pytest.fixture(scope="module")
def rows() -> list:
    """The judgment pass over §3a's pending sets, run once for this file."""
    return judged(catalogue.Admitted(PUBLISHED), emit.standing_order(PUBLISHED))


@pytest.fixture(scope="session")
def patched() -> Path:
    """The published bundle with the ADDITIVE patch set applied, built once.

    **Through :func:`codegen.patch.for_build`, which keys the directory on the bundle and
    on a digest of the patch set's files, and NOT on a fixed path.**  It was
    ``/tmp/adcp-patched-8735``, and ``patch.apply`` begins by deleting its output -- so two
    worktrees of this repository running this file at once deleted each other's bundle
    mid-read, which is the ``FileNotFoundError`` at a document name this fixture reports
    and which is reachable on any commit.  Three worktrees are the normal state of this
    repository.  ``for_build``'s own staging-and-rename is what makes the materialisation
    safe for concurrent readers, and keying on the patch set's bytes is what makes it the
    right bundle rather than merely a private one.
    """
    return patch.for_build(PUBLISHED, ("patches/8735",))


def test_the_judgment_pass_partitions_every_pending_entry(rows: list) -> None:
    """One outcome per pending entry, and the three parts account for all of them.

    The PENDING set is §3a's own -- the entries nothing in the bundle names -- and it is
    read off ``collect_shapes``' parts rather than re-derived (``tests/judgment.py``).  The
    claim here is that the pass reaches a verdict or an UNDECIDABLE for each of them and
    never falls through: a pass that silently skipped an entry would make the table's
    "every entry is backed by a verdict" vacuous for exactly the entries nobody looked at.
    """
    every = claimed("the pending entries of L2 and L3", rows)
    partitions(
        {f"{row.layer} {row.key}" for row in every},
        **{
            outcome: {f"{row.layer} {row.key}" for row in every if row.outcome == outcome}
            for outcome in sorted({row.outcome for row in every})
        },
    )
    ratchet(
        "pending entries of the two structural layers",
        len(every),
        at_most=353,
        because="FALLS as the bundle titles a structure it restates, which is "
        "adcontextprotocol/adcp#8735; a RISE is the bundle growing another unnamed "
        "repetition",
    )
    ratchet(
        "stating positions those entries cover",
        len(claimed("the stating positions", [p for row in every for p in row.positions])),
        at_most=1400,
        because="falls with the entries above, for the same reason and by the same ask",
    )


def test_the_checked_in_verdict_table_is_the_pass_that_derived_it(rows: list) -> None:
    """The table in the tree and the pass over the bundle are ONE reading, or this reddens.

    An equality between two derivations and never a pinned literal
    (``tests/test_every_check_names_its_set.py``'s rule): the left side is
    ``patches/8735/judgment.json`` as the repository ships it and the right side is the pass
    re-run against ``schemas/cache/3.2``.  So the table cannot be edited by hand into
    agreement with a verdict the bundle does not support, and a verdict that moves because
    the bundle moved has to be re-derived and re-read rather than silently kept.
    """
    checked_in = json.loads((Path("patches/8735") / "judgment.json").read_text())
    assert checked_in["entries"] == table(rows)["entries"], (
        "patches/8735/judgment.json is not the pass over schemas/cache/3.2 -- re-run "
        "`PYTHONPATH=.:src ./.venv/bin/python survey/judgment.py patches/8735/judgment.json` "
        "and read what changed"
    )


def test_every_undecidable_entry_names_what_would_decide_it(rows: list) -> None:
    """§3a's third local state is reported AS a third state, never folded into a verdict.

    "'DISTINCT' AND 'UNNAMEABLE' ARE DIFFERENT, AND ONLY ONE IS TERMINAL ... collapsing the
    two hides which of them upstream can fix."  So an entry the bundle gives no evidence
    about carries the sentence that would end it, and the sentence is the ask -- which is
    what makes the UNDECIDABLE count a measure of the bundle's silence rather than of ours.
    """
    undecided = claimed(
        "the undecidable pending entries", [row for row in rows if row.outcome != COLLAPSE
                                            and row.would_decide_it is not None]
    )
    for row in undecided:
        assert "title" in row.would_decide_it, row.evidence
    ratchet(
        "pending entries the bundle decides neither way",
        len(undecided),
        at_most=88,
        because="FALLS as upstream titles one: a title at the positions turns an "
        "UNDECIDABLE into a verdict, which is the whole of #8735's ask",
    )


def test_every_pending_entry_is_filed_bare_or_owes_no_ask(rows: list) -> None:
    """THE ASK ACCOUNTING, over all of them and in three parts that do not overlap.

    §3a: "EVERY REPEATED VALUE SET IS AN UPSTREAM QUESTION ... there is always something to
    ask".  There is one exception and it is a derivation rather than a concession: an array
    entry whose ELEMENT the bundle already names writes one ``list[X]`` by construction, so
    it records no defect and owes no ask -- which is why #8735 posts the array set in three
    comments and asks none of it.

    The three parts are asserted to PARTITION the pending set, because the figure this file
    reports is "how many entries carry a filed ask versus how many are still bare", and an
    entry in neither bucket would be missing from both halves of that sentence.
    """
    every = claimed("the pending entries", rows)
    partitions(
        {f"{row.layer} {row.key}" for row in every},
        filed={
            f"{row.layer} {row.key}"
            for row in every
            if ask_for(row).startswith("adcontextprotocol")
        },
        bare={f"{row.layer} {row.key}" for row in every if "BARE" in ask_for(row)},
        no_ask_owed={
            f"{row.layer} {row.key}" for row in every if ask_for(row).startswith("none owed")
        },
    )
    # Every one of §3a's six owning cases is read, and the owner an entry reports is one of
    # them -- so a seventh case appearing in the bundle reddens here instead of falling to a
    # default that says no ask is owed.
    for row in every:
        if row.layer == "L3":
            assert row.element in OWNED, row.element
    ratchet(
        "pending entries whose ask is still BARE",
        len({f"{row.layer} {row.key}" for row in every if "BARE" in ask_for(row)}),
        at_most=26,
        because="FALLS when adcp-client-python-q5g closes the RULE screen to §3a's depth, "
        "after which the set is either out of the pending population or inside #8735's "
        "denominator and filed with it",
    )


def test_every_table_entry_names_its_defect_and_its_ask() -> None:
    """The architecture's sentence, enforced where the entries are read rather than written.

    Both kinds, over every patch set the directory holds, and the ASSERTION IS THAT THE
    LOAD SUCCEEDS: ``codegen.patch`` raises on an entry naming neither, so a table that
    loads is a table whose every entry named both.  The strings are then checked for the
    one property a reviewer needs and a key name cannot give -- that the defect is a
    sentence about the BUNDLE, which is what separates "the bundle states this twice" from
    "we would rather it were called this".
    """
    sets = claimed("the patch sets of this repository", PATCH_SETS)
    entries = []
    for patch_set in sets:
        entries += list(patch.load(patch_set, PUBLISHED))
        entries += list(patch.additions(patch_set, PUBLISHED))
    # Claimed by IDENTITY and not by value: an ``Extraction`` carries the subschema it
    # extracts, which is a dict and is not hashable, and the set a check names is a set of
    # the nodes it ranges over -- which here is one pointer per entry.
    claimed(
        "the override table's entries",
        [(entry.document, entry.pointer) for entry in entries],
    )
    for entry in entries:
        assert entry.defect.strip(), entry
        assert entry.ask.strip(), entry
        assert "the bundle" in entry.defect, entry.defect
    ratchet(
        "subjects the override table answers locally",
        len(subjects_of(entries)),
        at_most=10,
        because="the table's size IS the debt figure: an entry whose ask upstream accepts "
        "is DELETED, so this falls to zero for a well-defined bundle and a rise is a new "
        "local answer to a question the protocol should have answered.  10 because the "
        "ceiling rose by 4 on 2026-11-05 (adcp-client-python-6h1): URL Macro Declaration, "
        "Explicit Collection Selector, Publisher Placement Reference and Unlocalized "
        "Creative Asset, each filed on adcontextprotocol/adcp#8735 with the branch "
        "prepared.  It is the SUBJECT count and not the row count, and that is the figure "
        "the direction is about: a title has to be at EVERY stating position of its "
        "structure or the layer declines to collect it (codegen.catalogue.shape_states, "
        "L2C), so the rows per subject are a function of the BUNDLE and counting them "
        "would read one subject stated at twelve positions as twelve debts and one stated "
        "once as one",
    )


def test_an_entry_naming_no_defect_is_refused(tmp_path: Path) -> None:
    """The refusal above, shown to be reachable, in both kinds.

    Written as a perturbation of the REAL manifests rather than of a fixture, so the thing
    proved refusable is the thing the repository ships: drop one key from one entry and the
    door the entries come through closes.
    """
    for patch_set, reader, key in (
        (Path("patches/8525"), patch.load, "extractions"),
        (Path("patches/8735"), patch.additions, "additions"),
    ):
        manifest = json.loads((patch_set / patch.MANIFEST).read_text())
        for dropped in ("defect", "ask"):
            broken = tmp_path / f"{patch_set.name}-{key}-{dropped}"
            (broken / patch.DOCUMENTS).mkdir(parents=True)
            held = json.loads(json.dumps(manifest))
            held[key][0].pop(dropped)
            (broken / patch.MANIFEST).write_text(json.dumps(held))
            for document in (patch_set / patch.DOCUMENTS).rglob("*.json"):
                at = broken / patch.DOCUMENTS / document.relative_to(patch_set / patch.DOCUMENTS)
                at.parent.mkdir(parents=True, exist_ok=True)
                at.write_text(document.read_text())
            with pytest.raises(ValueError, match="preference|names no ask"):
                reader(broken, PUBLISHED)


def test_an_addition_fails_the_day_the_node_carries_the_keyword(tmp_path: Path) -> None:
    """THE REMOVABILITY GUARANTEE OF THE ADDITIVE KIND, and it is not a warning.

    An extraction fails when the published bundle comes to hold the document it names, and
    ``test_patch_8525.py`` grades that clause.  An addition adds no document, so its clause
    is the KEYWORD arriving at the node -- and the architecture names this exact form as the
    dangerous one: "an additive override that silently wins over a published value is the
    one form of this mechanism that could outlive its cause invisibly, and it would do so
    while looking like success."

    The node asked for is DERIVED from the published bundle and not written down: the first
    node of the first document that already states a ``title``.  So the day the bundle stops
    titling anything, this test says so instead of passing over an empty set.
    """
    titled = claimed(
        "published nodes already stating a title",
        [
            (document, pointer)
            for document in sorted(bundle.portable(PUBLISHED))
            for pointer, node in bundle.nodes(bundle.read(PUBLISHED, document))
            if isinstance(node.get("title"), str)
        ],
    )
    document, pointer = sorted(titled)[0]
    held = tmp_path / "already-titled"
    held.mkdir()
    (held / patch.MANIFEST).write_text(
        json.dumps(
            {
                "additions": [
                    {
                        "document": document,
                        "pointer": pointer,
                        "keyword": "title",
                        "value": "Ours",
                        "defect": "the bundle titles nothing here, said the entry's author",
                        "ask": "adcontextprotocol/adcp#8735",
                    }
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="already states"):
        patch.additions(held, PUBLISHED)


def test_an_addition_declaring_no_direction_may_only_add_an_annotation(tmp_path: Path) -> None:
    """The second refusal, and the predicate is the record check's own.

    An addition that declares NO direction -- no ``narrows`` value -- has
    ``seen_by_a_validator`` and not byte-identity as its admissibility line, and that line
    is only available for a keyword a validator does not act on.  So a manifest asking for
    one that does is refused at LOAD rather than reported after apply -- the difference
    being that a patched bundle nobody looked at the report of would have forked the
    protocol.

    **AND THE REFUSAL IS NOW CONDITIONAL ON THE ENTRY'S DECLARED KIND AND NOT ON THE
    KEYWORD'S** (``docs/plan/rebuild-plan.md`` §8, "AN OVERRIDE MAY ASSERT, AND WHAT MAKES
    IT ADMISSIBLE IS THE DIRECTION"), which is why this test's name gained a clause.  An
    entry that means to assert declares a proving value and is graded on direction instead;
    that path is graded in ``tests/test_an_asserting_override_may_only_narrow.py``, and this
    one holds the sentence for the kind that still cannot.

    The keyword is drawn from ``codegen.keywords`` rather than named here, so a keyword
    whose cell changes what it decides changes this test's input by its own cell.
    """
    at = ("brand.json", "/definitions/data_subject_contestation")
    node = bundle.node_at(bundle.read(PUBLISHED, at[0]), at[1])
    # The keyword must be one the node does NOT already state, or the removability clause
    # answers first -- which it does, and that ordering is itself a property: a node that
    # already carries the keyword is refused before anyone asks what the keyword decides.
    acceptance = claimed(
        "keywords a validator acts on at a PROP position and this node omits",
        [
            keyword
            for keyword in sorted(bundle.DESCENDS)
            if not bundle.is_an_annotation(keyword, keywords.Position.PROP)
            and keyword not in node
        ],
    )
    held = tmp_path / "not-an-annotation"
    held.mkdir()
    (held / patch.MANIFEST).write_text(
        json.dumps(
            {
                "additions": [
                    {
                        "document": at[0],
                        "pointer": at[1],
                        "keyword": sorted(acceptance)[0],
                        "value": {},
                        "defect": "the bundle omits a constraint we would like it to state",
                        "ask": "adcontextprotocol/adcp#8735",
                    }
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="decides acceptance"):
        patch.additions(held, PUBLISHED)


def test_the_additive_patch_set_moves_one_keyword_at_one_node(patched: Path) -> None:
    """What the patched bundle differs from the published one BY, stated over every document.

    The raw half of the claim, as ``test_patch_8525.py`` splits it: this one says the
    addition touched what it meant to touch, and the record check below says what it
    touched decides nothing.  A patch set that had grown a second entry nobody reviewed
    reddens here with the document named.
    """
    grown = patch.additions(Path("patches/8735"), PUBLISHED)
    claimed(
        "the additive patch set's entries",
        [(entry.document, entry.pointer, entry.keyword) for entry in grown],
    )
    assert patch.added(PUBLISHED, patched) == []
    assert patch.removed(PUBLISHED, patched) == []
    moved = {entry.document for entry in grown}
    for document in claimed("the portable documents", bundle.portable(PUBLISHED)):
        same = bundle.read(PUBLISHED, document) == bundle.read(patched, document)
        assert same is (document not in moved), document
    for entry in grown:
        before = bundle.node_at(bundle.read(PUBLISHED, entry.document), entry.pointer)
        after = bundle.node_at(bundle.read(patched, entry.document), entry.pointer)
        assert entry.keyword not in before, entry
        assert after[entry.keyword] == entry.value, entry
        assert {k: v for k, v in after.items() if k != entry.keyword} == before, entry


def test_no_addition_is_seen_by_a_validator(patched: Path) -> None:
    """THE CHECK for the additive kind: it moves no keyword that decides an instance.

    §1 asks for byte-identity and an addition cannot have it -- it moves the record by
    exactly the annotation it adds, which is ``adcp-client-python-nn3``'s own finding.  What
    holds is the condition byte-identity was reached for, over all 1,054 portable
    documents, and it is the same function ``test_patch_8525.py`` reads.

    Every remaining difference is a GAIN of the one keyword the manifest names, at the
    pointers a record reaches it through -- a record is expanded per path through the
    reference graph, so one patched node inside a referenced document is reported from each
    referrer.
    """
    grown = patch.additions(Path("patches/8735"), PUBLISHED)
    differences = list(patch.differing(PUBLISHED, patched))
    seen = patch.seen_by_a_validator(differences)
    assert seen == [], "\n".join(str(d) for d in seen[:20])
    for difference in claimed("the record differences the addition makes", differences):
        assert "loses []" in difference.detail, str(difference)
        assert set(difference.keys) <= {entry.keyword for entry in grown}, str(difference)


def subjects_of(entries: Iterable) -> set:
    """The SUBJECTS a set of override entries answers for, which is the debt figure.

    An extraction's subject is the document it gives the structure; an addition's is the
    (keyword, value) pair it adds, because one title is one name for one subject however
    many positions the bundle states that subject at.  See the ratchet in
    :func:`test_every_table_entry_names_its_defect_and_its_ask` for why the rows are not
    the figure.
    """
    return {
        (entry.keyword, entry.value) if hasattr(entry, "keyword") else ("document", entry.document)
        for entry in entries
    }


def composed_base(bundle_dir: Path, document: str, pointer: str) -> str | None:
    """The TITLE of the document a composed node narrows, or ``None`` where it narrows none.

    A node whose ``allOf`` holds exactly one ``$ref`` to another document's ROOT and at
    least one other conjunct is a NARROWING of that document: the bundle names the base and
    the narrowing is anonymous.  This is the reading
    ``codegen.catalogue.shape_states``' L2C layer collects over, asked of one node, and it
    answers the one thing a name for such a subject can be graded against -- the base's own
    title, which is a string the BUNDLE states.

    ``None`` where the node states no ``allOf``, where its conjuncts hold no reference or
    more than one, where the reference names a fragment rather than a document root, or
    where the base states no title.  Each of those is a node this reading cannot speak for,
    and :func:`test_every_addition_is_backed_by_a_collapse_the_bundle_evidences` partitions
    on the answer rather than branching inside it.
    """
    node = bundle.node_at(bundle.read(bundle_dir, document), pointer)
    conjuncts = node.get("allOf") if isinstance(node, dict) else None
    if not isinstance(conjuncts, list) or len(conjuncts) < 2:
        return None
    documents = set(bundle.portable(bundle_dir))
    named = [
        bundle.document_for(head, documents)
        for conjunct in conjuncts
        if isinstance(conjunct, dict)
        and isinstance(uri := conjunct.get("$ref"), str)
        and not (head := bundle.split_ref(uri)[0]) == ""
        and bundle.split_ref(uri)[1] == ""
    ]
    reached = [name for name in named if name is not None]
    if len(reached) != 1 or len(reached) == len(conjuncts):
        return None
    title = bundle.read(bundle_dir, reached[0]).get("title")
    return title if isinstance(title, str) and title.strip() else None


def test_every_addition_is_backed_by_a_collapse_the_bundle_evidences(rows: list) -> None:
    """THE ENTRY IS NOT A PREFERENCE, and the bundle is what says so.

    An addition states a name for a structure.  §4 "refuses to mint a public name no
    document states", so every entry owes a reading of the bundle that its string answers
    TO -- and there are two such readings, because there are two shapes of anonymous
    structure and the evidence available at them is not the same.  **The two are a
    PARTITION of the table and the assertion below includes that**, so an entry that
    answers to neither reading cannot sit in a gap between them.

    **A TRANSCRIPTION: the bundle writes the word and the entry copies it.**  The judgment
    pass reaches COLLAPSE at the entry's position, which means the bundle names every
    stating position of the structure with one and the same word, and the string must be
    that word -- *"the property name the positions share | stated | take it"*, which is
    what §3a licenses and all it licenses.

    **A NARROWING: the bundle names the BASE and the entry names the restriction.**  The
    node composes one ``$ref`` to a titled document plus at least one narrowing conjunct
    (:func:`composed_base`), so the subject is "that document, restricted" -- and a
    property name cannot be its name, because the property names the FIELD's role.  Two
    things are therefore asserted and they are the two halves a name of this kind has:

    * **the HEAD is the bundle's own**: the string ENDS WITH the base document's own
      ``title``, so the noun a reader meets is the noun the bundle already uses for the
      thing being narrowed, and no subject is renamed;
    * **the string is not that title ALONE**, because a narrowing that took the base's name
      unchanged would give one subject two names -- which is the hazard every entry's
      ``why_not_an_extraction`` is about -- and because the modifier is the whole of what
      distinguishes the narrowing from the base.

    What the modifier should BE is a judgment and is not assertable here; what IS assertable
    is that it is a word and not a transcription of the structure, so the string is required
    to carry none of ``codegen.catalogue``'s placeholder form.  The argument for the word
    itself is the entry's ``why_this_string``, which is required to be present and is for a
    reviewer rather than for this test.
    """
    collapsed = {
        row.one_name: row
        for row in claimed("the COLLAPSE verdicts of the judgment pass",
                           [row for row in rows if row.outcome == COLLAPSE])
    }
    grown = patch.additions(Path("patches/8735"), PUBLISHED)
    claimed(
        "the additive entries", [(entry.document, entry.pointer) for entry in grown]
    )
    transcriptions, narrowings = {}, {}
    for entry in grown:
        at = (entry.document, entry.pointer)
        assert entry.keyword == "title", entry
        mine = [
            row
            for row in collapsed.values()
            if any((p.document, p.pointer) == at for p in row.positions)
        ]
        base = composed_base(PUBLISHED, entry.document, entry.pointer)
        if mine:
            transcriptions[at] = (entry, mine)
        elif base is not None:
            narrowings[at] = (entry, base)
    partitions(
        {(entry.document, entry.pointer) for entry in grown},
        **{
            "a word the bundle writes at every position": set(transcriptions),
            "a narrowing of a document the bundle titles": set(narrowings),
        },
    )
    for at, (entry, mine) in transcriptions.items():
        assert len(mine) == 1, f"{at}: the judgment pass reaches two COLLAPSE rows here"
        row = mine[0]
        # And the backing row must record a DEFECT, not merely a verdict: an array entry
        # whose element the bundle names reaches COLLAPSE and owes nothing, so an override
        # standing on one would be a preference wearing a verdict's clothes.
        assert not row.defect.startswith("NONE"), row.defect
        assert entry.value == " ".join(
            part.capitalize() for part in row.one_name.split("_")
        ), f"{entry.value!r} is not {row.one_name!r} as the bundle writes it"
    for at, (entry, base) in narrowings.items():
        assert complaints_about_a_narrowing(entry.value, base) == [], (
            at,
            complaints_about_a_narrowing(entry.value, base),
        )


def complaints_about_a_narrowing(value: str, base: str) -> list[str]:
    """What is wrong with ``value`` as a name for ``base`` narrowed, or an empty list.

    A function and not three inline asserts, so
    :func:`test_a_narrowing_named_anything_but_the_base_qualified_reddens` can call the
    SAME reading rather than a copy of it.  See
    :func:`test_every_addition_is_backed_by_a_collapse_the_bundle_evidences` for why these
    three and no others.
    """
    found = []
    if not value.endswith(base):
        found.append(
            f"{value!r} does not end with {base!r}, which is the title the bundle gives "
            f"the document this node narrows -- so the string renames the subject instead "
            f"of qualifying it"
        )
    if value == base:
        found.append(
            f"{value!r} IS the base's own title, so the entry gives one subject a second "
            f"name rather than naming the narrowing"
        )
    if catalogue.OBJECT_WORD in value:
        found.append(
            f"{value!r} carries the compiler's own placeholder form "
            f"{catalogue.OBJECT_WORD!r}, which is a transcription of the structure and "
            f"not a name"
        )
    return found


def test_a_narrowing_named_anything_but_the_base_qualified_reddens() -> None:
    """The red direction of the narrowing rule, over the strings the table actually ships.

    ``test_every_addition_is_backed_by_a_collapse_the_bundle_evidences`` is the green
    direction and an empty list passes it.  This perturbs each shipped narrowing title in
    the three ways the rule is about -- the base's own title alone, the property name the
    positions share, and the compiler's placeholder form -- and requires the same function
    to object to every one of them, while the shipped string itself draws no objection.

    **The population is the table's, not a fixture's**: a red direction over an invented
    pair would prove that a rule reddens on invented input, which is not the claim.
    """
    grown = patch.additions(Path("patches/8735"), PUBLISHED)
    pairs = claimed(
        "the narrowing entries of the override table",
        {
            (entry.value, base)
            for entry in grown
            if (base := composed_base(PUBLISHED, entry.document, entry.pointer)) is not None
        },
    )
    for value, base in sorted(pairs):
        assert complaints_about_a_narrowing(value, base) == []
        # The base's own title alone: one subject, two names.
        assert complaints_about_a_narrowing(base, base)
        # The property name the positions share, which is the FIELD's role and is what the
        # tree calls these classes today -- MacroDeclarations, Collections, PlacementRefs,
        # Creatives.  Spelled from the pointer the entry names rather than written down, so
        # this cannot drift from the table: the segment after the last ``properties``.
        for entry in (e for e in grown if e.value == value):
            word = entry.pointer.split("/properties/")[-1].split("/")[0]
            role = "".join(part.capitalize() for part in word.split("_"))
            assert complaints_about_a_narrowing(role, base), (role, base)
        # The compiler's placeholder form, which §4 rules a defect.
        assert complaints_about_a_narrowing(f"{catalogue.OBJECT_WORD}{base}", base)
