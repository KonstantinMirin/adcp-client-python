"""§3a's layer L0: what the collection reads off the bundle, and the gate it owes.

``docs/plan/architecture.md`` §3a declares the catalogue and ``codegen/catalogue.py``
implements the L0 collection.  This file holds two kinds of check and they are different
obligations:

* **the READINGS** -- that the collection partitions every vocabulary the bundle states
  more than once, that §3a's three naming cases are the bundle's own and not this
  compiler's, and that an entry's namespace is derived from the positions that state it.
  Every one of them names the set it ranges over (``tests/nodeset.py``), because a
  derivation that selects nothing passes every assertion over it.
* **the GATE** -- ``test_no_two_classes_carry_one_named_vocabulary``, which is the
  obligation §3a exists for: a vocabulary the bundle NAMES is one Python class, so a
  consumer who receives that value in two messages can pass it between them.

**THE GATE IS KEYED ON §3a's STRUCTURAL IDENTITY AND NOT ON THE MEMBER-SET, and the
difference is measured.**  The obligation as first stated was "no two emitted classes
carry the same enum member-set unless the bundle gives the field no title", and over this
bundle that cannot go green without a merge §3a itself forbids.  Measured over the 807
member-sets the bundle states:

* **5** are stated both by a vocabulary the bundle titles and by a structurally
  DIFFERENT one it does not.  The clearest is ``enums/gop-type.json`` -- title *GOP Type*,
  a Group of Pictures structure, members ``["closed", "open"]`` -- beside
  ``governance/report-plan-outcome-response.json``'s ``delivery_period_state``, members
  ``["open", "closed"]``.  One title between them, and nothing names the second; §3a's own
  sentence for the untitled case is that "without a title there is nothing to tell a
  coincidental member-set overlap from a real identity", and this is that overlap.  A gate
  on the member-set alone demands they be one class and type a governance field
  ``GOPType``.
* **3** carry conflicting titles, which §3a sends to the owner rather than collapsing.

So the gate ranges over the vocabularies the bundle NAMES -- §3a's structural identity
with exactly one title -- and the member-set reading is recorded here as the population it
would have claimed and why it is not the obligation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import fresh
import pytest
from nodeset import claimed, partitions

from codegen import bundle, catalogue, emit, vocabularies

REPO = Path(__file__).resolve().parents[1]
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

#: The script the gate runs, beside this file and NOT named ``test_*`` so pytest does not
#: collect it: it is a program and its ``main`` is the census the gate reads.
CHILD = Path(__file__).resolve().parent / "_vocabularies_in_a_tree.py"


@pytest.fixture(scope="module")
def l0() -> catalogue.Catalogue:
    """Layer L0 over the whole bundle, collected once for this module.

    The bundle and §3a's home-rule order and nothing else, which is §9's rule held by the
    call: a collection handed the RUN's document set would be the census §9 forbids.  The
    order is ``emit.standing_order``'s, which is itself a reading of the bundle alone.
    """
    return catalogue.collect(BUNDLE, emit.standing_order(BUNDLE))


def test_the_collection_partitions_every_vocabulary_stated_more_than_once(
    l0: catalogue.Catalogue,
) -> None:
    """§3a's four groups account for every repeated VALUE LIST, each exactly once.

    The arithmetic alone is not this property: two groups whose sizes sum correctly can
    both miss a value list and double-count another, which is why ``partitions`` reports
    the unaccounted and the double-counted by name.

    **Keyed on the value list, which is reading 4's own key** -- "no value list appears
    twice in the emitted tree" -- and ``catalogue.value_list`` carries the measurement that
    makes the coarser key safe.  ``test_one_value_list_is_one_set_of_admitted_values``
    below is that measurement held as a check.
    """
    stated: dict[catalogue.Vocabulary, int] = Counter(
        catalogue.value_list(position) for position in l0.positions
    )
    repeated = claimed(
        "value lists the bundle states at more than one position",
        [key for key, n in stated.items() if n > 1],
        inside=stated,
    )
    partitions(
        repeated,
        one_document=[catalogue.value_list(group[0]) for group in l0.restated],
        named=list(l0.entries),
        untitled=[catalogue.value_list(group[0]) for group in l0.untitled],
        conflicting=[conflict.vocabulary for conflict in l0.conflicting],
    )


def test_one_value_list_is_one_set_of_admitted_values(l0: catalogue.Catalogue) -> None:
    """**The measurement that lets an entry be keyed on the VALUE LIST.**

    §3a's identity is STRUCTURAL and a value list is coarser, so the two can only be
    exchanged if no group of positions sharing a value list differs in a keyword that
    NARROWS.  That is a property of this bundle and not of the key, so it is checked
    rather than asserted in a docstring: for every value list stated at more than one
    position, the admitting keywords BESIDE the ``enum`` are compared across the group,
    and the only difference admitted is a ``type`` -- which beside a closed value set of
    one JSON kind admits not one value more.

    Measured today: 169 value lists stated at more than one position, 159 with one
    structural identity and 10 with two, and in all 10 the whole of the difference is
    ``type: "string"`` beside an all-``str`` ``enum``.  **If a document ever states one
    value list twice with a differing ``pattern`` or ``minLength``, this reddens and the
    key is wrong** -- which is the fact a count would not have carried.
    """
    groups: dict[catalogue.Vocabulary, list[catalogue.Stated]] = {}
    for position in l0.positions:
        groups.setdefault(catalogue.value_list(position), []).append(position)
    repeated = claimed(
        "value lists the bundle states at more than one position",
        {key: group for key, group in groups.items() if len(group) > 1},
        inside=groups,
    )
    narrowing = {}
    for key in repeated:
        group = groups[key]
        besides = {
            tuple((word, value) for word, value in p.identity if word not in ("enum", "type"))
            for p in group
        }
        if len(besides) > 1:
            narrowing[str(key)] = sorted(str(b) for b in besides)
    assert not narrowing, json.dumps(narrowing, indent=2)


def test_the_naming_split_is_the_bundles_own(l0: catalogue.Catalogue) -> None:
    """§3a's naming cases, each read off the bundle or off a declared judgement.

    Not an equality on a count: §3a's table reads 203 / 457 / 3 and that is a census over
    the document of RECORD, where every ``$ref`` reaching a titled vocabulary carries its
    one title along.  The READING is what cannot go stale -- a name is a title the bundle
    states or a judgement ``codegen/vocabularies.py`` declares, an un-rowed untitled group
    is not collapsed, and a conflict between two ROOTS is the owner's -- so this asserts
    the reading over every member and lets the counts move.

    **A TITLED entry's title is stated at one of its own positions.**  An UNTITLED one is
    titled at none of them and is an entry only because a row judges it one subject, which
    is §3a's "one named type -- the positions are one subject and the bundle names it".
    """
    named = claimed("vocabularies the bundle names", l0.entries.values())
    for entry in named:
        titles = catalogue.titles(entry.positions)
        if entry.title is None:
            assert not titles, (entry.name, sorted(titles))
            assert vocabularies.one_subject(entry.vocabulary), entry.vocabulary
            assert not vocabularies.separate(entry.vocabulary), entry.vocabulary
        else:
            assert entry.title in titles, (entry.title, sorted(titles))
            assert entry.members == next(
                p.members for p in entry.positions if p.title == entry.title
            ), entry.title
        assert len(entry.documents) > 1, (entry.title, sorted(entry.documents))

    for group in claimed(
        "vocabularies the bundle leaves unnamed", l0.untitled, inside=l0.untitled
    ):
        assert not catalogue.titles(group), sorted(catalogue.titles(group))
        assert len({p.document for p in group}) > 1
        assert not vocabularies.one_subject(catalogue.value_list(group[0])), group[0].members

    for group in claimed(
        "vocabularies a single document restates", l0.restated, inside=l0.restated
    ):
        assert len({p.document for p in group}) == 1, sorted({p.document for p in group})


def test_a_conflicting_title_is_brought_and_never_picked(l0: catalogue.Catalogue) -> None:
    """§3a's third case: two titles, NEITHER a document root, is the OWNER's decision.

    "3 carry conflicting titles and are a decision brought to the owner."  So the check is
    that none of them became an entry and that no name was picked for one -- picking the
    commonest would mint a public name no document states for the other side of the
    conflict, which §4 refuses.  The report carries the titles and the positions, because
    that is what the decision needs.
    """
    conflicts = claimed("identities the bundle gives more than one title", l0.conflicting)
    report = []
    for conflict in conflicts:
        assert conflict.vocabulary not in l0.entries, conflict.titles
        assert len(conflict.titles) > 1, conflict.titles
        report.append(
            {
                "titles": list(conflict.titles),
                "positions": [
                    f"{p.document}#{p.pointer or '/'} title={p.title!r}"
                    for p in conflict.positions
                ],
            }
        )
    # Printed rather than asserted away: the decision is the owner's and this is where a
    # reader of the suite finds the two titles and every position that states either.
    print(json.dumps(report, indent=2))


def test_an_entrys_namespace_is_the_narrowest_containing_its_positions(
    l0: catalogue.Catalogue,
) -> None:
    """§3a's namespace rule, derived per entry and never chosen.

    One document → that document; one domain → that domain; more than one →
    ``adcp.types.common``.  The derivation is checked against the positions themselves, so
    a home that does not contain every position reddens whatever the count is.

    **It also reports the case §3a does not settle.**  An entry stated at a document ROOT
    has two decided rules pointing at two homes -- §3a's rule here, and §4's "a root keeps
    the name ... an imported symbol is fixed more firmly still: it is ANOTHER document's
    name, which this module has no standing to move".  The population is printed with the
    root each one is stated at, because the choice moves a name ``adcp.types.<domain>``
    exports today and is therefore the owner's.
    """
    named = claimed("vocabularies the bundle names", l0.entries.values())
    ambiguous = []
    for entry in named:
        where = catalogue.home(entry)
        if len(entry.documents) == 1:
            assert where in entry.documents
        elif len(entry.domains) == 1:
            assert where == next(iter(entry.domains))
        else:
            assert where == catalogue.SHARED, (entry.title, where)
        # The domain derivation is the run's own, and the two may not come apart: §11's
        # arrows forbid this layer importing the run, so the equality is held here.
        for position in entry.positions:
            assert catalogue.domain(position.document) == emit.domain(position.document)
        if entry.rooted:
            ambiguous.append(
                {
                    "title": entry.title,
                    "section 3a home": where,
                    "section 4 home": sorted(p.document for p in entry.rooted),
                }
            )
    print(json.dumps(ambiguous, indent=2))


def test_the_member_set_reading_names_the_merges_section_3a_forbids() -> None:
    """Why the gate is keyed on structural identity: the member-set reading's population.

    The obligation as first stated keys on the MEMBER-SET.  This derives the member-sets
    that reading would demand be one class and that §3a forbids collapsing, so the
    difference between the two keys is a named population and not a remark in a docstring.
    Both groups are asserted non-empty, because that is the whole claim: if either were
    empty the member-set reading would be the obligation and this file would be keyed on it.
    """
    positions = list(catalogue.states(BUNDLE))
    by_set: dict[tuple[object, ...], list[catalogue.Stated]] = {}
    for position in positions:
        by_set.setdefault(tuple(sorted(set(position.members), key=repr)), []).append(position)

    repeated = {key: group for key, group in by_set.items() if len(group) > 1}
    claimed("member-sets the bundle states at more than one position", repeated)

    titled_beside_untitled = []
    conflicting = []
    for key, group in repeated.items():
        titles = catalogue.titles(group)
        if len(titles) > 1:
            conflicting.append(key)
            continue
        if not titles:
            continue
        identities_named = {p.identity for p in group if p.title}
        if any(p.identity not in identities_named for p in group if not p.title):
            titled_beside_untitled.append(key)

    claimed(
        "member-sets a titled vocabulary shares with a structurally different untitled one",
        titled_beside_untitled,
        inside=repeated,
    )
    claimed(
        "member-sets the bundle gives more than one title",
        conflicting,
        inside=repeated,
    )


#: The hand-written half of ``src/adcp``, which a fresh tree needs beside it and which no
#: run emits.  The same three generated entries ``tests/test_the_tree_imports.py`` names,
#: and for its reason: a committed generated file left where the fresh tree expects its
#: own makes the child grade a mixture of two compilers.
GENERATED = ("_schemas", "constraints.py", "envelopes.py")


def _a_fresh_package(out: emit.Emitted, root: Path) -> Path:
    """``root/adcp``: the hand-written modules copied, every generated one FRESH."""
    import shutil

    shutil.copytree(
        REPO / "src" / "adcp",
        root / "adcp",
        ignore=shutil.ignore_patterns("__pycache__", *GENERATED),
    )
    emit.write(out, root / "adcp" / "types" / "_schemas", root / "adcp" / "types")
    for rel in GENERATED:
        assert (root / "adcp" / "types" / rel).exists(), rel
    return root


def test_no_two_classes_carry_one_named_vocabulary(
    l0: catalogue.Catalogue, tmp_path: Path
) -> None:
    """**THE GATE.**  A vocabulary the bundle NAMES is exactly one class in the tree.

    **It was ``xfail(strict=True)`` and the walk now consults L0**, which is what flips
    it: ``codegen/catalogue.py``'s ``Catalogue.restating`` is the table
    ``compiler.Module.vocabularies`` carries, and a position that restates a named
    vocabulary imports the symbol the NAMING position declares instead of minting a
    second class over the same members.  22 positions over 21 documents stop minting
    one.  The marker's reason -- "section 3a orders PASS B before the cross-document
    COLLECTION" -- is still the measurement it was, and it ordered the WORK rather than
    excusing the obligation; the strictness is what made the flip loud.

    §3a's whole claim: "a type a consumer receives in a ``media_buy`` message is the same
    object as the one in a ``governance`` message, so it can be passed between them.  That
    last property is the one nothing in the artifact provides today."  One class OBJECT per
    named vocabulary is that property, stated so that a check can read it.

    **Over the tree a FRESH run emits, in a CHILD process**, which is
    ``docs/plan/architecture.md``'s "a check may not be downstream of its own
    precondition" and ``tests/_imports_a_tree.py``'s own reason: the suite's interpreter
    has already bound the committed ``adcp.types.constraints``, so a fresh tree graded
    beside it would be graded against the committed alias module.

    **Counted by class IDENTITY and not by name.**  Two modules can bind one name to two
    classes -- measured on the committed tree, ``UpdateFrequency`` and ``PricingModel``
    each do -- and two names can bind one class, which §1's carve-out permits inside a
    module.  Neither is what a consumer experiences; one object is.
    """
    from compiled import compiled

    entries = sorted(
        claimed("vocabularies the bundle names", l0.entries.values()),
        key=lambda e: (e.title or e.name or "", e.vocabulary[0], len(e.members)),
    )
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    claimed("modules a fresh run emits", out.files)
    _a_fresh_package(out, tmp_path)

    done = subprocess.run(
        [sys.executable, str(CHILD)],
        input=json.dumps([list(entry.members) for entry in entries]),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join((str(tmp_path), str(REPO))),
        },
        cwd=REPO,
        check=False,
    )
    assert done.returncode == 0, f"{done.stdout[-2000:]}\n{done.stderr[-4000:]}"
    report = json.loads(done.stdout)
    assert report["modules"] > 1000, report["modules"]

    scattered = {
        # The entry's own evidence: a title the bundle states, the name a judgement
        # declares, or -- for ``vocabularies.AGREED``, where §4's own derivation already
        # agreed at every position -- the members, which are what identifies it.
        entries[i].title or entries[i].name or str(list(entries[i].members)): carriers
        for i, count, carriers in report["carriers"]
        if count != 1
    }
    assert not scattered, json.dumps(scattered, indent=2)


# ---------------------------------------------------------------------------
# §3a's L2 and L3, under the key decided 2026-11-03.
#
# Reading 4 "ranges over ALL FOUR of the catalogue's layers, not the first", and its
# ``Decided by`` names two halves that this section holds separately: **one census per
# layer, each keyed on that layer's own identity**, and **not every layer has a class
# population** -- an array type renders as ``list[X]`` inside an annotation and declares no
# class, so the array layer is read off the bundle's own stating positions while the object
# layer can be read off either.
#
# The KEY is ``catalogue.Admitted`` and its own docstring is the argument for what it
# contains.  What is checked here is the three things a docstring cannot be: that the
# census PARTITIONS the repeated structures, that the collapse happens wherever §3a's
# split licenses it and nowhere else, and that the L3 layer's emptiness is a derivation
# rather than a scope.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def admitted() -> catalogue.Admitted:
    """The decided key over the whole bundle, built once for this module.

    The bundle and nothing else, which is §9's rule held by the call -- the same rule
    :func:`l0` is built under.
    """
    return catalogue.Admitted(BUNDLE)


@pytest.fixture(scope="module")
def standing() -> dict[str, int]:
    """§3a's home rule's own input: the dependency order the arrows already run in.

    ``emit.standing_order`` is the one derivation of it and this is the RUN's own reading,
    handed to the collection exactly as the run hands it -- §3a's "a derived reading of
    the bundle is an argument, not something a callee recomputes", which is also what keeps
    this module's figures and the emitter's one answer.
    """
    return emit.standing_order(BUNDLE)


@pytest.fixture(scope="module")
def l2(admitted: catalogue.Admitted, standing: dict[str, int]) -> catalogue.Shapes:
    """§3a's layer L2: the OBJECT TYPES the bundle states."""
    return catalogue.collect_shapes(admitted, "L2", standing)


@pytest.fixture(scope="module")
def l3(admitted: catalogue.Admitted, standing: dict[str, int]) -> catalogue.Shapes:
    """§3a's layer L3: the ARRAY TYPES the bundle states."""
    return catalogue.collect_shapes(admitted, "L3", standing)


@pytest.mark.parametrize("layer", ["L2", "L3"])
def test_each_structural_layer_partitions_every_structure_stated_more_than_once(
    layer: str, l2: catalogue.Shapes, l3: catalogue.Shapes
) -> None:
    """§3a's cases account for every repeated STRUCTURE of the layer, each exactly once.

    **One census per layer, which is reading 4's own ``Decided by``**, and the six parts
    are §3a's three-way split with the three cases that split has no members in at L0: a
    structure stated in one document is §4's content dedup's, one stated at nothing but
    document ROOTS is §1's -- both obliged to declare, so there is nothing for this layer
    to stop minting -- and one stated at nothing but positions INSIDE a rule is
    ``adcp-client-python-q5g``'s, where nothing declares at all.

    ``not_collected`` is the layer that collects nothing, which is L3's by derivation and
    is empty at L2: a structure the bundle titles nowhere is NAMED FROM ITSELF at the
    object layer (``docs/plan/rebuild-plan.md``, 2026-11-04) and collected like any other.

    The arithmetic alone is not the property: two parts whose sizes sum correctly can both
    miss a structure and double-count another, which is why ``partitions`` reports the
    unaccounted and the double-claimed by name.
    """
    shapes = {"L2": l2, "L3": l3}[layer]
    stated: dict[str, int] = Counter(position.key for position in shapes.positions)
    repeated = claimed(
        f"{layer} structures the bundle states at more than one position",
        [key for key, n in stated.items() if n > 1],
        inside=stated,
    )
    partitions(
        repeated,
        one_document=[group[0].key for group in shapes.restated],
        collected=list(shapes.entries),
        not_collected=[group[0].key for group in shapes.untitled],
        conflicting=[conflict.key for conflict in shapes.conflicting],
        every_position_a_root=[group[0].key for group in shapes.duplicated],
        no_position_declares=[group[0].key for group in shapes.declaring_nothing],
    )


@pytest.mark.parametrize("layer", ["L2", "L3"])
def test_a_structural_layers_naming_split_is_the_bundles_own(
    layer: str, l2: catalogue.Shapes, l3: catalogue.Shapes
) -> None:
    """§4's THREE STEPS, each read off the bundle or off the structure and never minted.

    * **step 1**, a titled entry, carries exactly one title, or several of which exactly
      one belongs to a document ROOT -- ``catalogue.the_name``'s rule, which §3a's
      correction of 2026-11-02 states;
    * **step 2 and step 3** carry no title at any position, which is what sends them to a
      derivation at all.  **A ``description`` is not a title**, which is §3a's own
      sentence -- "a description states what a thing IS, not what it is CALLED, so it
      mints no name" -- and is checked here because an untitled structure with a
      description is the commonest shape in this population and the one a lane is most
      tempted to name from.  **Step 2's name is the structure's own field set and nothing
      else**: every word of it is read back out of the home's own ``properties``, which is
      what makes it a name the type can PROVE -- "this is the type with these fields" --
      rather than a subject one position's property key claims.  **Step 3 mints nothing at
      all**, which is "the declaring position" held by the absence of a name: §4 spells it
      where the class is declared;
    * a CONFLICTING group carries two or more titles and no single rooted one, and no name
      is picked for it.
    """
    shapes = {"L2": l2, "L3": l3}[layer]
    for entry in claimed(f"{layer} entries this layer collects", shapes.entries.values()):
        titles = {p.title for p in entry.positions if p.title is not None}
        if entry.step == 1:
            assert entry.title in titles, (entry.title, sorted(titles))
            assert entry.name is None, (entry.title, entry.name)
            if len(titles) > 1:
                rooted = {p.title for p in entry.positions if p.is_a_root and p.title}
                assert rooted == {entry.title}, (sorted(titles), sorted(rooted))
            continue
        assert not titles, (entry.step, sorted(titles))
        assert entry.title is None, (entry.step, entry.title)
        if entry.step == 3:
            assert entry.name is None, (entry.step, entry.name)
            continue
        assert entry.name == catalogue.structure_in_words(entry.at.fields), (
            entry.name,
            entry.at.fields,
        )
    for group in claimed(f"{layer} groups this layer does not collect", [
        *shapes.untitled, *shapes.declaring_nothing
    ]):
        assert not [p.title for p in group if p.title is not None], group[0].key
    for conflict in shapes.conflicting:
        assert len(conflict.titles) > 1, conflict.titles
        rooted = {p.title for p in conflict.positions if p.is_a_root and p.title}
        assert len(rooted) != 1, (conflict.titles, sorted(rooted))


def test_no_object_structure_emits_more_than_one_definition(l2: catalogue.Shapes) -> None:
    """**THE L2 GATE**: an object structure is written once and referenced.

    Reading 4: "a type stated at more than one position is written once and referenced,
    never restated -- and this reading ranges over ALL FOUR of the catalogue's layers".
    So for every entry this layer collects, the position that DECLARES it carries a class
    and every restating position carries none.

    **It is an INVARIANT and not a census**: "there are N of these" freezes the tree and
    "this cannot happen" survives a refactor, so nothing here counts the entries or the
    positions -- and **an ALIAS is a name and not a type**, which is why what is read is
    the ``__adcp_schema__`` a CLASS STATEMENT binds and not the names a module exports.

    **It ranges over the structures the bundle titles NOWHERE as well, since 2026-11-04**
    (``docs/plan/rebuild-plan.md``, "A STRUCTURE THE BUNDLE NEVER TITLES IS NAMED FROM
    ITSELF").  That is the whole of what widened: the obligation was already stated over
    every entry, and the untitled structures became entries.

    **Read off the CLASS STATEMENTS of a fresh emission and keyed on the pointer each one
    carries**, not off the tree's text by name and not off a rendered annotation: a class
    binds its own ``__adcp_schema__`` to the ``(document, pointer)`` it was lowered from,
    so "is there a second class over this structure" is asked of the position rather than
    of a name two modules might spell alike.  §3a's own sentence about the rendered
    annotation is why: a figure that moves when the renderer changes cannot be this gate.

    **The separate-type decisions are ENUMERATED and not counted**, which is reading 4's
    requirement of them.  They are ``Shapes.withheld``, each carrying the rule that
    withholds it -- ``of_a_root_union`` is §3's and §4's union rows, and
    ``keeps_a_named_node`` is §5's -- and this check asserts the enumeration is exactly
    what it says: every withheld position DOES still carry a class, so a reason that
    stopped applying reddens here rather than silently covering a collapse that now works.
    """
    import ast

    from compiled import compiled

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    claimed("modules a fresh run emits", out.files)
    declaring: dict[tuple[str, str], list[str]] = {}
    #: ``(document, pointer)`` -> the FIELDS the class statement there annotates, as source
    #: text.  Read in the same pass as :data:`declaring` because the clause on an entry no
    #: position of which declares a class is about the annotation a position arrives at, and
    #: the annotation is the only thing in the tree that still names the type there.
    annotated: dict[tuple[str, str], dict[str, str]] = {}
    for text in out.files.values():
        for node in ast.parse(text).body:
            if not isinstance(node, ast.ClassDef):
                continue
            at: tuple[str, str] | None = None
            fields: dict[str, str] = {}
            for statement in node.body:
                if not (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                ):
                    continue
                if statement.target.id != "__adcp_schema__":
                    if not statement.target.id.startswith("_"):
                        fields[statement.target.id] = ast.unparse(statement.annotation)
                    continue
                if not isinstance(statement.value, ast.Call):
                    continue
                said = {k.arg: k.value for k in statement.value.keywords}
                document, pointer = said.get("document"), said.get("pointer")
                if isinstance(document, ast.Constant) and isinstance(pointer, ast.Constant):
                    at = (document.value, pointer.value.lstrip("#"))
            if at is not None:
                declaring.setdefault(at, []).append(node.name)
                annotated.setdefault(at, {}).update(fields)

    def arrives_as(document: str, pointer: str) -> str | None:
        """The annotation the TREE writes at one position, through its nearest declaring
        ancestor.

        A position whose own class was collapsed away still arrives somewhere: it is a
        PROPERTY of an enclosing object, and the field that property becomes carries the
        type.  So the ancestor walk is up the pointer until a position that declares is
        reached, which is what skips a ``allOf/<n>`` conjunct -- a conjunct declares no
        class and its properties are fields of the node COMPOSING it, which is §2's own
        reading and not a second one written here.
        """
        head, _, field = pointer.rpartition("/properties/")
        if not field:
            return None
        parts = [p for p in head.split("/") if p]
        while True:
            ancestor = "/" + "/".join(parts) if parts else ""
            for name, written in annotated.get((document, ancestor), {}).items():
                # ``emit`` suffixes a field colliding with a python keyword or a pydantic
                # member, so the schema's own word is the stem.
                if name.rstrip("_") == field:
                    return written
            if not parts:
                return None
            parts.pop()

    entries = claimed("L2 entries this layer collects", l2.entries.values())
    #: entry -> the positions of it a fresh run DECLARES a class at.  **The two arms below
    #: are the two cases this map has, and splitting them is this clause's own repair**
    #: (``adcp-client-python-nuit``).
    at_a_class = {
        entry.spelled: tuple(
            p for p in entry.positions if declaring.get((p.document, p.pointer))
        )
        for entry in entries
    }
    homeless = {
        entry.spelled: f"{entry.at.document}{entry.at.pointer or ' /'}"
        for entry in entries
        if at_a_class[entry.spelled]
        and not declaring.get((entry.at.document, entry.at.pointer))
    }
    assert not homeless, json.dumps(homeless, indent=2)

    # ----------------------------------------------------------------------------- #
    # An entry NO POSITION OF WHICH declares a class, which is the OTHER case and not a
    # homeless home.  ``adcp-client-python-nlkz``'s collapse -- "a non-root node that
    # declares nothing its base does not already declare identically declares no class" --
    # lands at EVERY position of such a group at once, onto a class in a document the L2
    # key cannot reach: ``core/rights-constraint.json`` and
    # ``core/rights-attestation-evaluation.json`` each state the brand branch of
    # ``core/attestation-issuer.json`` INLINE, so the two narrowings share L2's key with
    # each other and with neither the branch nor the class.  There is no second definition
    # at either position to remove and nothing for the layer to collapse.
    #
    # **IT IS NOT A SCREEN THE LAYER COULD CARRY, MEASURED.**  The reading is §2's
    # intersection of the position with the sibling ``$ref`` conjunct, which the catalogue
    # is built before anything can perform.  Its nearest STRUCTURAL approximation -- a
    # narrowing under a sibling ``$ref`` conjunct that applies a schema at the same
    # property -- matches 11 L2 positions in 4 entries over this bundle, and the homes of
    # THREE of the four declare a class (``Location``, ``ObjTypeResourceType``,
    # ``ObjType``).  A screen that took those out would delete three live entries, so the
    # approximation is refuted and the case is decided HERE, where the build's own answer
    # is in hand.
    #
    # **AND THE OBLIGATION IS KEPT RATHER THAN EXEMPTED, which is the whole of why this is
    # two clauses and not an allowlist.**  Reading 4 asks that the structure be ONE type;
    # with no class at any position, what carries the type is the ANNOTATION each position
    # arrives at, so that is what is compared -- one spelling across every position of the
    # entry, and a class the tree declares. Measured: both positions of ``ObjTypeBrand``
    # arrive at ``AttestationBrandIssuer``, declared once at
    # ``core/attestation-issuer.json#/oneOf/0``.  Two different spellings would be the
    # split this gate exists to catch, and a spelling naming nothing would be the broken
    # reference a homeless home threatens.
    collapsed = {
        entry.spelled: {
            f"{p.document}{p.pointer}": arrives_as(p.document, p.pointer)
            for p in entry.positions
        }
        for entry in entries
        if not at_a_class[entry.spelled]
    }
    partitions(
        {entry.spelled for entry in entries},
        at_a_class={spelled for spelled, got in at_a_class.items() if got},
        no_position_declares=set(collapsed),
    )
    split = {
        spelled: row
        for spelled, row in collapsed.items()
        if len({got for got in row.values()}) != 1 or None in row.values()
    }
    assert not split, json.dumps(split, indent=2)
    #: And the entry mints NO name of its own: a spelling in a module with no class behind
    #: it is an import of something nobody wrote, which is the one consumer-visible failure
    #: a home the build does not honour can cause.
    minted = {
        spelled: sorted(name for name, text in out.files.items() if spelled in text)
        for spelled in collapsed
        if any(spelled in text for text in out.files.values())
    }
    assert not minted, json.dumps(minted, indent=2)
    dangling = {
        spelled: row
        for spelled, row in collapsed.items()
        for got in row.values()
        if got is not None and not any(got in names for names in declaring.values())
    }
    assert not dangling, json.dumps(dangling, indent=2)

    restated = {
        f"{entry.spelled} @ {p.document}{p.pointer}": declaring[(p.document, p.pointer)]
        for entry in entries
        for p in entry.restating
        if (p.document, p.pointer) in declaring
    }
    assert not restated, json.dumps(restated, indent=2)

    # The other direction: a withheld position is withheld because it MUST declare, so one
    # that stopped declaring means the reason has gone stale and the collapse is available.
    stale = {
        f"{title} @ {p.document}{p.pointer}": {
            "of_a_root_union": p.of_a_root_union,
            "keeps_a_named_node": p.keeps_a_named_node,
        }
        for title, p in claimed("L2 positions the collapse is withheld at", l2.withheld)
        if (p.document, p.pointer) not in declaring
    }
    assert not stale, json.dumps(stale, indent=2)


def test_every_repeated_array_type_is_owned_by_a_layer_beneath_it(
    admitted: catalogue.Admitted, l3: catalogue.Shapes, l2: catalogue.Shapes
) -> None:
    """**Why L3 collects nothing of its own, as a derivation rather than as a scope.**

    Reading 4's ``Decided by``: an array type "renders as ``list[X]`` inside an annotation
    and declares no class".  ``list[X]`` is written once in Python by construction, so the
    only thing an array position can write twice is its ELEMENT -- and this check is that
    every cross-document array group of this bundle has an element some layer BENEATH L3
    owns:

    * a ``$ref`` element is already written once and referenced (§5's ``$ref`` row);
    * an inline OBJECT element is an L2 stating position, asserted by key equality against
      L2's own population rather than by inspection;
    * an ``enum`` element is L0's, a constrained scalar is L1's, a composition is the union
      row's, and a bare scalar has no type to write at all.

    **If an array group ever appears whose element is none of those, this reddens** -- and
    that is the case where L3 would need a collection of its own.  The sentence in
    ``emit`` that says L3 is censused and not collected is only true while this is green.
    """
    import collections as _collections

    groups: dict[str, list[catalogue.Shaped]] = {}
    for position in l3.positions:
        groups.setdefault(position.key, []).append(position)
    cross = claimed(
        "array types the bundle states in more than one document",
        {
            key: group
            for key, group in groups.items()
            if len(group) > 1 and len({p.document for p in group}) > 1
        },
        inside=groups,
    )
    l2_keys = {position.key for position in l2.positions}
    owners: _collections.Counter[str] = _collections.Counter()
    unowned = {}
    for key in cross:
        position = groups[key][0]
        element = bundle.node_at(
            admitted.document(position.document), position.pointer
        )["items"]
        if "$ref" in element:
            owners["a reference (§5)"] += 1
        elif isinstance(element.get("properties"), dict) and element["properties"]:
            owners["an object (L2)"] += 1
            if admitted.key(position.document, element) not in l2_keys:
                unowned[f"{position.document}{position.pointer}"] = "object, not an L2 position"
        elif "enum" in element:
            owners["an enumeration (L0)"] += 1
        elif any(word in element for word in bundle.COMPOSITION + bundle.CONDITIONAL):
            owners["a composition (§4's union row)"] += 1
        elif [
            word
            for word in element
            if word not in catalogue.ANNOTATIONS and word != "type"
        ]:
            owners["a constrained scalar (L1)"] += 1
        elif "type" in element or not element:
            # An EMPTY element schema admits every instance, so the array is ``list[Any]``
            # and there is no element type to write even once:
            # ``core/feature-requirement.json``'s ``allowed_values`` is this bundle's one.
            owners["a bare or empty scalar (no type to write)"] += 1
        else:
            unowned[f"{position.document}{position.pointer}"] = sorted(element)
    assert not unowned, json.dumps(unowned, indent=2)
    assert sum(owners.values()) == len(cross), (dict(owners), len(cross))


@pytest.fixture(scope="module")
def l2c(admitted: catalogue.Admitted, standing: dict[str, int]) -> catalogue.Shapes:
    """§3a's layer L2C: the object type a node states through its CONJUNCTS."""
    return catalogue.collect_shapes(admitted, "L2C", standing)


@pytest.fixture(scope="module")
def l2a(
    admitted: catalogue.Admitted, standing: dict[str, int], l2c: catalogue.Shapes
) -> catalogue.Applied:
    """§3a's layer L2A: the positions a DOCUMENT applies an already-named type at."""
    return catalogue.collect_applied(admitted, l2c, standing)


def test_the_applied_layer_joins_only_a_type_the_bundle_already_names(
    admitted: catalogue.Admitted, l2c: catalogue.Shapes, l2a: catalogue.Applied
) -> None:
    """**L2A's census PARTITIONS, and every position it collects joins a NAMED entry.**

    The layer reads a position as the type the DOCUMENT APPLIES there rather than as the
    node's own text (``catalogue.applied_conjunction``), which is the only reading under
    which a ``oneOf`` branch narrowing a property its root also states is one type with the
    position that spells the composition inline.  The two obligations are the ones the
    reading cannot carry by itself:

    **ONE.  THE CENSUS PARTITIONS**, so no position is quietly dropped: a censused position
    either already states the type in its own text and is a position of the entry already,
    or it declares no class, or the type it applies is one no entry names, or it is
    COLLECTED.  Four parts and no fifth.

    **TWO.  A COLLECTED POSITION JOINS AN ENTRY THE BUNDLE NAMES AT EVERY POSITION THAT CAN
    CARRY A TITLE**, which is what licenses collapsing onto it without minting anything.
    L2C's own evidence rule is untouched and is what this reads: that layer collects a group
    only where the bundle titles EVERY position whose own text states the type, so an entry
    reached here carries a ``title`` the bundle states -- ``ShapeEntry.step == 1`` -- and
    reading 4's *"a name is minted per ENTRY and never per position"* is why the applied
    position owes none of its own.  A derived name (step 2 or 3) would be a placeholder, and
    §4 forbids a collapse onto one.

    **AND A COLLECTED POSITION'S OWN TEXT DOES NOT STATE THE TYPE**, which is what keeps
    this a layer and not a second answer to L2C's question: where a position states the
    composition itself, L2C has it already and this layer must add nothing.
    """
    censused = claimed(
        "positions the document applies a composed type at",
        [f"{p.document}{p.pointer}" for p in l2a.positions],
    )
    already = {
        f"{p.document}{p.pointer}"
        for entry in l2c.entries.values()
        for p in entry.positions
    }
    partitions(
        censused,
        **{
            "collected: the document applies a named type here": {
                f"{document}{pointer}" for document, pointer in l2a.collected
            },
            "already a position of the entry in its own text": already & censused,
            "declares no class": {f"{p.document}{p.pointer}" for p in l2a.undeclared},
            "applies a type no entry names": {
                f"{p.document}{p.pointer}" for p in l2a.unmatched
            },
        },
    )
    unnamed = {
        f"{document}{pointer}": (entry.spelled, entry.step)
        for entry in l2a.entries.values()
        for document, pointer in l2a.collected
        if (document, pointer) in {(p.document, p.pointer) for p in entry.positions}
        and (entry.step != 1 or not entry.title)
    }
    assert not unnamed, json.dumps(unnamed, indent=2, default=repr)
    #: **AND THE APPLIED READING IS NOT THE NODE'S OWN**, which is the layer's reason for
    #: existing stated as a property of what it collected: at every collected position the
    #: document applies a conjunction the node's own text does not state, so the two keys
    #: differ and L2C could not have seen the position.  A collected position whose own
    #: text already keys into the entry would mean this layer answering a question L2C
    #: answers, and the partition above could not tell that apart from a real join.
    its_own_text = {
        f"{position.document}{position.pointer}": entry.spelled
        for entry in l2a.entries.values()
        for position in entry.positions
        if (position.document, position.pointer) in l2a.collected
        and admitted.key(
            position.document,
            bundle.node_at(admitted.document(position.document), position.pointer),
        )
        == entry.key
    }
    assert not its_own_text, json.dumps(its_own_text, indent=2)
    #: **AND A POSITION THAT DECLARES NO CLASS IS NOT COLLECTED**, which the partition above
    #: cannot report on its own: ``declares_no_class`` positions are screened out again
    #: downstream -- ``ShapeEntry.restating`` drops them and ``shape_declared_at`` ranks them
    #: last -- so collecting one moves no emitted byte and the partition would still
    #: partition.  What it DOES move is ``collected``, which is L2's ``applied`` screen, so a
    #: CONJ position admitted here is a position struck from L2's census for no reason.  §5's
    #: ``allOf`` row is the reason it is not collected: a conjunct's properties are declared
    #: on the node holding the ``allOf``, so the conjunct's own pointer declares nothing and
    #: there is nothing at it to collapse.
    consumed = claimed(
        "censused positions whose subschema the node holding it consumes",
        [f"{p.document}{p.pointer}" for p in l2a.positions if p.declares_no_class],
    )
    assert not consumed & {f"{document}{pointer}" for document, pointer in l2a.collected}
    # :attr:`Applied.undeclared` is the part of that set which reached an ENTRY -- the rest
    # apply a type no entry names and are reported as such, which is the earlier question.
    assert {f"{p.document}{p.pointer}" for p in l2a.undeclared} <= consumed


def test_resolving_a_reference_is_memoised_and_the_keys_are_the_same(
    standing: dict[str, int]
) -> None:
    """**THE KEY IS THE SAME KEY WITH THE MEMO AND WITHOUT IT, over every censused position
    of every structural layer.**

    ``catalogue.Admitted._targets`` holds the key of a ``$ref``'s TARGET, which the same few
    referenced documents are re-keyed for once per position that names them; the layers read
    5,428 positions of this bundle between them and the collection cost 22 s of it.  A memo
    is the one optimisation that can silently become a second answer -- a stale entry is
    indistinguishable from a different identity -- so the equality is asserted rather than
    argued, in the only form that means anything here: BOTH readings, side by side, over
    every position each layer censuses and over the entry each one lands in.

    The memo is disabled by a mapping that keeps nothing, so the second reading takes the
    uncached path at every reference and not merely a cold cache.
    """

    class _Nothing(dict):
        """A mapping that accepts every write and holds nothing."""

        def __setitem__(self, key: object, value: object) -> None:
            return None

    def censused(*, memoised: bool) -> dict[str, object]:
        admitted = catalogue.Admitted(BUNDLE)
        if not memoised:
            admitted._targets = _Nothing()
        out: dict[str, object] = {
            layer: sorted(
                (p.document, p.pointer, p.key)
                for p in catalogue.shape_states(admitted, layer)
            )
            for layer in ("L2", "L2C", "L3")
        }
        composed = catalogue.collect_shapes(admitted, "L2C", standing)
        applied = catalogue.collect_applied(admitted, composed, standing)
        out["L2A"] = sorted((p.document, p.pointer, p.key) for p in applied.positions)
        out["entries"] = sorted(
            (key, entry.title, entry.at.document, entry.at.pointer)
            for key, entry in applied.entries.items()
        )
        return out

    with_memo = censused(memoised=True)
    claimed(
        "positions the structural layers key",
        [
            f"{layer} {at[0]}{at[1]}"
            for layer in ("L2", "L2C", "L3", "L2A")
            for at in with_memo[layer]  # type: ignore[union-attr]
        ],
    )
    without = censused(memoised=False)
    moved = {layer: rows for layer, rows in with_memo.items() if rows != without[layer]}
    assert not moved, sorted(moved)


# ---------------------------------------------------------------------------
# §3a's L1: the CONSTRAINED SCALARS, and the name each one takes.
#
# Reading 4 ranges over all four layers and L1 is the one that was HALF built: the layer
# already wrote each constraint once and referenced it -- ``constraints.symbol`` is a pure
# function of the shape, so reading 4's identity obligation held -- and named 114 of them
# with eight hex digits of the pattern's SHA-256.  ``docs/plan/rebuild-plan.md`` §4 rules
# that a defect: "a minted name says what the type constrains.  A digest fails that and is
# a defect, and insertion-stability is not the test."
#
# So the obligations here are a NAMING obligation and not a collapsing one, and they are
# two: that every symbol the layer mints is a name (the GATE), and that the name each one
# takes is the step of §4's derivation the bundle licenses (the READINGS).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def l1() -> catalogue.Scalars:
    """§3a's layer L1: the CONSTRAINED SCALARS the bundle states.

    The bundle and nothing else, which is :func:`l0`'s own rule and §9's.
    """
    from codegen import constraints

    return catalogue.collect_scalars(
        BUNDLE,
        frozenset(keyword for keyword, _ in constraints.SPELLING),
        constraints.symbol,
    )


def test_the_scalar_layer_knows_the_type_words_its_own_module_spells(
    l1: catalogue.Scalars,
) -> None:
    """``catalogue.SCALAR_WORDS`` is ``constraints.BASE``'s key set and cannot drift.

    The two are restated rather than imported because §11's arrows run
    ``catalogue <- constraints``, and ``catalogue.domain``'s own docstring names the price:
    "the DERIVATION is one sentence and the two cannot come apart without
    ``tests/test_catalogue.py``'s own equality reddening".  This is that equality for this
    layer, and the layer censuses nothing outside the set either way.
    """
    from codegen import constraints

    assert frozenset(constraints.BASE) == catalogue.SCALAR_WORDS
    assert {position.kind for position in l1.positions} <= catalogue.SCALAR_WORDS


def test_the_scalar_layer_partitions_into_section_fours_three_steps(
    l1: catalogue.Scalars,
) -> None:
    """§4's three derivation steps account for every entry, each exactly once.

    "**The derivation, in order, and there is no fourth step**", so the three parts are a
    PARTITION of the layer and a fourth bucket cannot appear without this reddening.  The
    arithmetic alone is not the property -- ``partitions`` reports the unaccounted and the
    double-claimed by name, so two parts whose sizes sum correctly cannot both miss an
    entry and double-count another.
    """
    entries = claimed("L1 entries the bundle states", l1.entries)
    partitions(
        entries,
        the_bundles_own_name=[e.key for e in l1.named_by_the_bundle],
        the_constraint_in_words=[e.key for e in l1.named_by_the_constraint],
        the_declaring_position=[e.key for e in l1.pending_a_name],
    )


def test_a_constraints_name_is_the_bundles_only_where_the_bundle_names_one_subject(
    l1: catalogue.Scalars,
) -> None:
    """§4's step 1, and §3a's own argument for why it is stricter here than at L0.

    §3a: "What tells a shared subject from a coincidental overlap is that an object's key
    holds the property NAMES, while an array's key over a scalar element holds no name at
    all -- which is why the object layer can collapse on identity and the array layer must
    not."  **A constrained scalar's key holds no name either**: it is the constraint, and
    nothing in it says what the constraint is ABOUT.  So one position's title names THAT
    POSITION's subject and says nothing about the constraint's, and step 1 answers only
    where every stating position names the same subject.

    Both directions are checked, because the loose reading is the tempting one:

    * a step-1 entry's name IS that one subject, and every position agrees on it;
    * an entry the bundle does NOT name one subject for took a later step -- so an entry
      whose positions disagree can never be named after one of them.
    """
    for entry in claimed("L1 entries named by the bundle", l1.named_by_the_bundle):
        assert entry.subjects == (entry.name,), (entry.name, entry.subjects)
        assert all(p.subject == entry.name for p in entry.positions), entry.name
    disagreeing = claimed(
        "L1 entries whose positions name more than one subject, or none",
        [e for e in l1.entries.values() if len(e.subjects) != 1 or any(
            p.subject is None for p in e.positions
        )],
        inside=l1.entries.values(),
    )
    for entry in disagreeing:
        assert entry.step != 1, (entry.name, entry.subjects)
        # ... and where such a name DOES coincide with a subject it is the HOME's own and
        # never a sibling's, which is the half that matters: a name taken from a position
        # the entry does not declare at is the lie this rule exists to stop.  Measured,
        # one entry of this bundle is in that condition --
        # ``core/reporting-control-total.json``'s two titled branches both state a
        # ``name`` pattern, and the home's subject already carries its branch's title, so
        # ``IntegerReportingControlTotalName`` is the position and not the subject.
        assert entry.name not in set(entry.subjects) - {entry.at.subject}, (
            entry.name,
            entry.subjects,
        )


def test_a_constraint_pending_a_name_is_named_for_the_position_that_declares_it(
    l1: catalogue.Scalars,
) -> None:
    """§4's step 3, which is §1's rule and is simultaneously the upstream ASK.

    §1: "for a symbol carrying no ``__adcp_schema__`` the declaring position is its
    catalogue entry's home."  So a step-3 name is read off ``ScalarEntry.at`` -- a position
    of the bundle -- and the check is that it IS: the home's own document name is in the
    symbol, so a reader meets a position they can go and read rather than a subject the
    bundle never claimed.

    **The home is a function of the bundle and not of the run**, which is what makes the
    symbol the same for a one-document command and for a whole-population emission (§9).
    """
    for entry in claimed("L1 entries pending a name", l1.pending_a_name):
        assert entry.at in entry.positions, entry.name
        assert entry.name.startswith(catalogue._home_name(BUNDLE, entry.at)[:1]), entry.name
        assert entry.name == catalogue._home_name(BUNDLE, entry.at) or entry.name.startswith(
            catalogue._home_name(BUNDLE, entry.at)
        ), (entry.name, entry.at.document, entry.at.pointer)


def test_no_symbol_this_compiler_mints_carries_a_digest_or_an_index(
    l1: catalogue.Scalars,
) -> None:
    """**THE L1 GATE**: §4's one rule for a digest and for a positional index.

    "A digest and an index are the same failure at different layers, so they are one rule
    and not two: **no name the compiler mints contains a content digest or a positional
    index.**"

    Read off the SYMBOLS a fresh run declares in ``adcp.types.constraints`` -- the module a
    consumer imports from and annotates with -- and not off this layer's collection, so a
    second path that minted a name without consulting the layer would redden here too.

    **It is an INVARIANT and not a count.**  "There are 0 digests" freezes nothing: the
    statement is that a run cannot declare a symbol whose tail is a hexadecimal run or a
    bare integer, and it survives every rename, every new constraint and every bundle.
    """
    import ast
    import re

    from compiled import compiled

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    module = ast.parse(out.beside["constraints.py"])
    assignments = {
        target.id: ast.unparse(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    declared = claimed(
        "symbols a fresh run declares in adcp.types.constraints", assignments
    )
    # **A CONTENT DIGEST**: a trailing run of eight or more UPPERCASE hexadecimal
    # characters, which is what the retired ``constraints._digest`` wrote and is a form no
    # bound this bundle states reaches -- its widest is ``maxLength: 1048576``, seven
    # decimal digits.  Asked of every declared symbol, because a digest minted by any path
    # at all is the defect.
    digested = sorted(name for name in declared if re.search(r"[0-9A-F]{8,}$", name))
    assert not digested, digested
    # **A POSITIONAL INDEX**: a trailing digit run that is not the value of a bound.  Asked
    # of the names this MODULE spells rather than of all of them, and that is the sound
    # scope rather than a narrowed one: a step-1 or step-3 name is made of the bundle's own
    # words, so a digit in it is the bundle's (``...ObservedAdjustmentSha256``), while a
    # step-2 name is spelled here from the constraint and every bound it spells follows its
    # own keyword word.  A digit run reached without one is an index.
    from codegen import constraints

    spelled_here = claimed(
        "symbols this module spells from the constraint itself",
        [e.name for e in l1.named_by_the_constraint] + list(constraints.NAMED_CONTAINERS.values()),
    )
    words = "|".join(
        word for _, word in constraints.SPELLING
    ) + "|" + "|".join(
        word for spelling in constraints.CONTAINER_SPELLING.values() for _, word in spelling
    )
    indexed = sorted(
        name
        for name in spelled_here & declared
        if (found := re.search(r"([A-Za-z]*)[\dp.]+$", name))
        and not re.search(rf"({words})$", found.group(1))
    )
    assert not indexed, indexed
    # **AND THE LAYER IS WHAT NAMED THEM**, so the gate cannot go green because a second
    # path minted a name without consulting it.  Asked of the symbols carrying a
    # ``pattern``, which is exactly the population the retired digest named: every one of
    # them is a name this layer derived over the bundle.
    minted = {entry.name for entry in l1.entries.values()}
    patterned = claimed(
        "symbols a fresh run declares for a constraint carrying a pattern",
        [name for name, value in assignments.items() if "pattern=" in value],
        inside=declared,
    )
    assert patterned <= minted, sorted(patterned - minted)


def test_no_declared_name_claims_a_subject_the_bundle_gave_another_document() -> None:
    """**§3a STEP 3's REGRESSION GUARD**: a name the bundle gave a document ROOT is that
    subject's, and no other position declares a type under it.

    §3a: "A name is minted per ENTRY and never per position.  This is what makes a role
    word claiming a subject's name impossible by construction: a position has a role, an
    entry has a subject, and only a subject gets a name."

    **IT CONFIRMS AND CANNOT ESTABLISH, which is the only thing a census over the output
    is for** (§3a: "a gate that finds duplication is evidence the order is wrong ...  where
    the decision is made once, a census over the output can only ever confirm it -- which
    is what a regression guard is for, and is all these gates should be").  The decision is
    ``emit.rooted_subjects`` read before any name is derived and spent as one axis of §4's
    collision rule (``lower/names.SUBJECT_SCOPE``); the claim is not among the names left
    available, so this check has nothing to find unless that axis stops being asked.

    **An ALIAS is not what this is about and must not be swept in.**  §3a's answer at a
    restating position a consumer needs the protocol's word at is "an alias at its
    position, never a second class", so the question is asked of the pointers a type is
    DECLARED at -- ``Emitted.declared`` -- and a binding is on the other side of the
    subtraction ``lower/names.assign`` already makes.

    **The measurement this replaced** (``adcp-client-python-53b``, and the row said "no
    gate catches it"): 31 sites, 26 distinct symbols, every one of them a nested object
    named ``pascal_case(property)`` where the property KEY is the role the subobject plays
    in its parent -- an untitled capabilities block keyed ``media_buy`` publishing
    ``MediaBuy`` for a thing that is media-buy CAPABILITIES, beside the entity
    ``core/media-buy.json`` titles "Media Buy".  Reading 6 could not see it because it
    counts objects per name per NAMESPACE and these land in different domains, which §1
    permits and is right to.

    ``AudienceSource`` is why the exemption is read per SYMBOL: two home documents
    (``core/audience-source.json`` and ``enums/audience-source.json``) root that one
    symbol, §1 permits the two paths, and neither may be pushed off a name the bundle gave
    it.  So a position is exempt exactly where the symbol is its OWN document's root.
    """
    from compiled import compiled

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    subjects = emit.rooted_subjects(BUNDLE)
    claimed("subjects the bundle names at a document root", subjects)

    claiming = {
        f"{symbol} @ {document}{pointer}": sorted(subjects[symbol])
        for document, rows in out.declared.items()
        for pointer, symbol in rows.items()
        if symbol in subjects and document not in subjects[symbol]
    }
    assert not claiming, json.dumps(claiming, indent=2)
