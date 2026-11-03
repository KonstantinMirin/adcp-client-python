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

import pytest
from nodeset import claimed, partitions

from codegen import bundle, catalogue, emit, vocabularies

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: The script the gate runs, beside this file and NOT named ``test_*`` so pytest does not
#: collect it: it is a program and its ``main`` is the census the gate reads.
CHILD = Path(__file__).resolve().parent / "_vocabularies_in_a_tree.py"


@pytest.fixture(scope="module")
def l0() -> catalogue.Catalogue:
    """Layer L0 over the whole bundle, collected once for this module.

    The bundle and nothing else, which is §9's rule held by the call: a collection handed
    the RUN's document set would be the census §9 forbids.
    """
    return catalogue.collect(BUNDLE)


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
