"""The mutation set: one violation per keyword a node states, read AT ITS LOCATION.

``adcp-client-python-hzio.2``'s DONE WHEN, one clause one test:

* **every node's stated keywords each have a mutation the document refuses** --
  :func:`test_every_keyword_with_an_isolating_mutation_has_one_and_the_rest_are_named`;
* **every refusal is asserted at the location and cause the mutation targeted** --
  :func:`test_every_mutation_is_refused_on_the_keyword_it_targets_and_nowhere_else` and
  :func:`test_the_location_the_document_names_is_the_location_the_change_was_made_at`;
* **no mutation is hand-written** --
  :func:`test_no_mutation_is_hand_written_and_every_one_names_a_keyword_the_node_states`.

**AND THE COUNT IS A SUM, NEVER A PRODUCT** --
:func:`test_the_count_is_a_sum_over_the_nodes_and_a_node_owes_one_per_keyword`.  A node
stating *k* keywords owes *k* mutations and one admitted value; a document owes the sum
over its nodes.  A combination of mutations is not owed by any reading, and this file
asserts the arithmetic rather than describing it.

**A DISCARD IS A REPORT.**  ``docs/plan/architecture.md`` §9's second check is only more
than a boolean because the refusal is read against its cause, so a candidate the document
ADMITS is a defect in the candidate and a candidate the document refuses for TWO reasons
proves nothing about either.  Both are discarded, both are counted on
:attr:`codegen.verify.witness.Counters.discards` by keyword and reason, and
:func:`test_a_discard_is_reported_by_keyword_and_reason_and_never_silent` is what makes
"reported rather than silent" a fact about the code.
"""

from __future__ import annotations

import ast
import pathlib

import constructed
import pytest
from nodeset import claimed, partitions, ratchet

from codegen import bundle, keywords
from codegen.verify import witness

MODULE = pathlib.Path(witness.__file__)

#: The keywords whose mutation this reading derives, read off the module's own producer
#: rather than written out: :func:`codegen.verify.witness._candidates` is the one place a
#: candidate is minted, so the set it can emit is the set a check may range over, and a
#: keyword added there joins this without anyone editing a list.
DERIVED = frozenset(
    node.elts[0].value
    for node in ast.walk(ast.parse(MODULE.read_text()))
    if isinstance(node, ast.Tuple)
    and len(node.elts) == 4
    and isinstance(node.elts[0], ast.Constant)
    and isinstance(node.elts[0].value, str)
) | keywords.FLOORS | keywords.CEILINGS

#: A node whose every stated keyword has an isolating mutation, written here so the
#: obligation can be read at one node rather than inferred from a total.
ONE_NODE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "size"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 8},
        "size": {"type": "integer", "minimum": 3, "maximum": 9},
        "kind": {"enum": ["a", "b", "c"]},
        "fixed": {"const": 7},
    },
}

#: A node stating a keyword the draft's own validator does not assert, which is the case
#: "the document still admits the mutation" -- and the discard the reading owes for it.
#: ``uri-template`` is not one of draft-07's defined formats, so a string violating it is a
#: string the document admits.
#: No ``type`` word beside it on purpose: a ``type`` mutation of this node WOULD be refused,
#: and the node under test here is one whose ONLY mutable keyword is the one the document
#: does not assert.
ADMITTED_MUTATION = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "format": "uri-template",
}


def _mutations() -> dict[tuple[str, str], tuple[witness.Mutation, ...]]:
    """Every node's mutation set, over the whole bundle, derived once.

    Held on the module because the counters are the subject of three checks below and a
    counter read after a partial pass is a figure about the order the tests ran in.
    """
    if not _HELD:
        built = constructed.whole()
        for document, positions in constructed.pointers().items():
            for pointer in positions:
                _HELD[(document, pointer)] = built.mutations(document, pointer)
    return _HELD


_HELD: dict[tuple[str, str], tuple[witness.Mutation, ...]] = {}


@pytest.fixture(autouse=True, scope="module")
def _warm() -> None:
    """One pass for the whole module, so no test's figures depend on the order."""
    _mutations()


# --------------------------------------------------------------------------- #
# one violation per keyword, and the cause is the document's own answer
# --------------------------------------------------------------------------- #
def test_every_mutation_is_refused_on_the_keyword_it_targets_and_nowhere_else() -> None:
    """``hzio.2``'s central clause: **the refusal is read against its CAUSE.**

    ``docs/plan/architecture.md`` §9: *"a class that refuses the mutation for the wrong
    reason has not been shown to carry the keyword"* -- which cuts both ways, because a
    candidate the DOCUMENT refuses for two reasons is a candidate neither keyword is
    isolated by.  So every surviving mutation is offered to the document again here and the
    document's answer must be exactly the one keyword the mutation targeted.
    """
    built = constructed.whole()
    held = claimed("nodes with a mutation", [key for key, ms in _mutations().items() if ms])
    bad = []
    for document, pointer in sorted(held):
        for mutation in _mutations()[(document, pointer)]:
            named = {name for name, _ in built.refusals(document, pointer, mutation.value)}
            if named != {mutation.keyword}:
                bad.append((document, pointer, mutation.keyword, sorted(named)))
    assert not bad, bad[:5]


def test_the_location_the_document_names_is_the_location_the_change_was_made_at() -> None:
    """**AND THE REFUSAL IS ASSERTED AT ITS LOCATION.**

    :attr:`codegen.verify.witness.Mutation.location` is the instance path the DOCUMENT
    named, and the change was made at the node's own value -- so the two agree, and a
    disagreement is counted under a ``relocated`` entry on
    :attr:`codegen.verify.witness.Counters.discards` rather than passing quietly.

    **What "location" MEANS here is the node's own instance location, and the nesting is
    carried by the POINTER** -- which is §9's identity rule rather than a shortcut: *"the
    subject of a check is always a node the document holds, the conjunction it is read under
    travels beside it as the applied schema, and the identity therefore stays the
    pointer's."*  A mutation of a node's own value is a change at that node's own location,
    so an empty instance path within it is the right answer and not a missing one.
    """
    built = constructed.whole()
    held = claimed("nodes with a mutation", [key for key, ms in _mutations().items() if ms])
    off = [
        (document, pointer, mutation.keyword, mutation.location)
        for document, pointer in sorted(held)
        for mutation in _mutations()[(document, pointer)]
        if mutation.location != ()
    ]
    assert not off, off[:5]
    relocated = [name for name in built.counters.discards if "relocated" in name]
    assert not relocated, relocated


def test_every_keyword_with_an_isolating_mutation_has_one_and_the_rest_are_named() -> None:
    """``hzio.2``'s first clause, with the exceptions NAMED rather than subtracted.

    Every ``(document, pointer, keyword)`` a node states falls into exactly one of three,
    and the third is the one a looser test would have swept up with the second:

    * **a mutation** -- the document refused the candidate on exactly that keyword;
    * **a discarded candidate** -- one was built and offered, and the document either
      admitted it or refused it on a second keyword as well.  Either way the counters name
      it (:func:`test_a_discard_is_reported_by_keyword_and_reason_and_never_silent`);
    * **nothing to mutate** -- the node states the keyword and states nothing a change of
      it could violate.  ``"required": []`` is the measured case: there is no key to drop,
      so there is no candidate, and calling that a discard would be claiming an offer
      nobody made.

    Read against :func:`codegen.verify.witness._candidates` -- the ONE place a candidate is
    minted -- so the three parts are exact per node rather than inferred from a global
    table.
    """
    built = constructed.whole()
    stated, mutated, discarded, barren = set(), set(), set(), set()
    named = {name.split(":")[0] for name in built.counters.discards}
    for (document, pointer), found in _mutations().items():
        if not built.value(document, pointer).held:
            continue
        node = built.node(document, pointer)
        if not isinstance(node, dict):
            continue
        got = {mutation.keyword for mutation in found}
        offered = {
            keyword
            for keyword, _, _, _ in witness._candidates(node, built.value(document, pointer).value)
        }
        for keyword in set(node) & DERIVED:
            stated.add((document, pointer, keyword))
            if keyword in got:
                mutated.add((document, pointer, keyword))
            elif keyword in offered:
                discarded.add((document, pointer, keyword))
                assert keyword in named, (document, pointer, keyword)
            else:
                barren.add((document, pointer, keyword))
    partitions(
        stated,
        with_a_mutation=mutated,
        with_a_discarded_candidate=discarded,
        stating_nothing_to_mutate=barren,
    )
    ratchet(
        "stated keywords per hundred that get an isolating mutation",
        round(100 * len(mutated) / len(stated)),
        at_least=84,
        because=(
            "a candidate that isolates a keyword a node co-states with another moves this "
            "UP; it falls when a keyword stops getting a candidate at all, which is a "
            "regression in the derivation and not a re-point"
        ),
    )


def test_one_node_written_here_owes_one_mutation_per_keyword_it_states() -> None:
    """The same obligation at ONE node, where every number is visible.

    A total over 215,019 nodes can hide a keyword that never gets a mutation anywhere; one
    node whose keywords are all stated here cannot.  :data:`ONE_NODE` states ``type``,
    ``required`` and ``additionalProperties`` at its root and a bound pair at two of its
    properties, and every one of them is owed a mutation the document refuses.
    """
    built = witness.Construction({"one.json": ONE_NODE})
    at_root = claimed("the root's mutations", {m.keyword for m in built.mutations("one.json", "")})
    assert at_root == {"type", "required", "additionalProperties"}, at_root
    name = claimed(
        "the string property's mutations",
        {m.keyword for m in built.mutations("one.json", "/properties/name")},
    )
    assert name == {"type", "minLength", "maxLength"}, name
    size = claimed(
        "the integer property's mutations",
        {m.keyword for m in built.mutations("one.json", "/properties/size")},
    )
    assert size == {"type", "minimum", "maximum"}, size
    kind = claimed(
        "the enum property's mutations",
        {m.keyword for m in built.mutations("one.json", "/properties/kind")},
    )
    assert kind == {"enum"}, kind
    fixed = claimed(
        "the const property's mutations",
        {m.keyword for m in built.mutations("one.json", "/properties/fixed")},
    )
    assert fixed == {"const"}, fixed


# --------------------------------------------------------------------------- #
# the count is a sum
# --------------------------------------------------------------------------- #
def test_the_count_is_a_sum_over_the_nodes_and_a_node_owes_one_per_keyword() -> None:
    """``hzio.2``: *"THE COUNT IS A SUM, NEVER A PRODUCT."*

    Two readings, and the second is the one a product would break: the document's total is
    the sum over its nodes, and a node's own count is at most the number of keywords it
    states.  A reading that crossed two keywords -- or two branches, or two conjuncts --
    would put a node above its own keyword count and would be caught here by name.
    """
    built = constructed.whole()
    held = claimed("nodes asked for a mutation set", _mutations())
    over = []
    for document, pointer in sorted(held):
        node = built.node(document, pointer)
        if not isinstance(node, dict):
            continue
        if len(_mutations()[(document, pointer)]) > len(set(node)):
            over.append((document, pointer, len(_mutations()[(document, pointer)]), sorted(node)))
    assert not over, over[:5]
    total = sum(len(found) for found in _mutations().values())
    assert total == sum(
        len(_mutations()[(document, pointer)])
        for document, positions in constructed.pointers().items()
        for pointer in positions
    ), total
    ratchet(
        "mutations the bundle owes",
        total,
        at_least=170_000,
        because=(
            "it is a SUM over nodes and keywords, so it rises with the bundle and with a "
            "keyword gaining a derivation; a fall means a node stopped being asked"
        ),
    )


def test_a_mutation_is_the_admitted_value_with_exactly_one_fact_changed() -> None:
    """*"The invalid witness is a MUTATION of the valid one rather than an arbitrary
    non-conforming value."*

    §9's reason is the isolation: *"changing exactly one stated fact isolates the keyword
    under test from every other keyword at the node."*  Read structurally at a node written
    here -- a dropped required key leaves every other key at its admitted value, and a
    bound exceeded by one leaves the rest of the object alone.
    """
    built = witness.Construction({"one.json": ONE_NODE})
    admitted = built.value("one.json", "").value
    dropped = [m for m in built.mutations("one.json", "") if m.keyword == "required"]
    assert dropped, "a node stating required owes a dropped key"
    assert set(dropped[0].value) < set(admitted), (dropped[0].value, admitted)
    for key, value in dropped[0].value.items():
        assert admitted[key] == value, (key, value, admitted[key])


# --------------------------------------------------------------------------- #
# derived, never hand-written; and a discard is a report
# --------------------------------------------------------------------------- #
def test_no_mutation_is_hand_written_and_every_one_names_a_keyword_the_node_states() -> None:
    """``hzio.2``'s last clause: *"no mutation is hand-written."*

    Two readings together, because either alone passes while the clause is false.  A node
    stating NOTHING a mutation can target gets none -- so there is no table of mutations
    keyed on a document or a pointer anywhere -- and every mutation a node does get names a
    keyword that node itself states, so none is minted from a list of known shapes.
    """
    silent = witness.Construction(
        {"bare.json": {"$schema": "http://json-schema.org/draft-07/schema#", "title": "bare"}}
    )
    assert silent.mutations("bare.json", "") == ()
    built = constructed.whole()
    held = claimed("nodes with a mutation", [key for key, ms in _mutations().items() if ms])
    foreign = [
        (document, pointer, mutation.keyword)
        for document, pointer in sorted(held)
        for mutation in _mutations()[(document, pointer)]
        if mutation.keyword not in built.node(document, pointer)
    ]
    assert not foreign, foreign[:5]


def test_a_discard_is_reported_by_keyword_and_reason_and_never_silent() -> None:
    """*"With the discard REPORTED rather than silent."*

    Every discard names the keyword it targeted and which of the two reasons applied, and
    the two totals agree: the counter that counts discards and the table that names them
    sum to the same figure.  A table that named fewer than the counter counted would be the
    silent half this clause forbids.
    """
    built = constructed.whole()
    named = claimed("discard reasons", built.counters.discards)
    assert sum(built.counters.discards.values()) == built.counters.discarded
    for reason in sorted(named):
        keyword, _, why = reason.partition(": ")
        assert keyword in DERIVED, reason
        assert why == "the document admits it" or why.startswith("not isolated, also "), reason
    assert built.counters.mutations > built.counters.discarded, (
        built.counters.mutations,
        built.counters.discarded,
    )


def test_a_mutation_the_document_admits_is_discarded_at_the_node_that_states_it() -> None:
    """The discard at ONE node, where the reason is visible rather than aggregated.

    ``uri-template`` is not one of draft-07's defined formats, so the draft's own checker
    asserts nothing about it and a string violating it is a string the document ADMITS.
    That is a defect in the mutation and not a finding about any subject -- so the candidate
    is built, offered, discarded, and named.
    """
    built = witness.Construction({"fmt.json": ADMITTED_MUTATION})
    assert built.mutations("fmt.json", "") == ()
    named = claimed("discards at this node", built.counters.discards)
    assert named == {"format: the document admits it"}, named


def test_the_set_of_documents_the_mutations_range_over_is_the_whole_bundle() -> None:
    """The denominator, named, because a pass over a shrunken set is green and says nothing.

    ``tests/nodeset.py``: *"a derivation that selects nothing passes every assertion over it
    and is indistinguishable from a working check."*  The same holds for a derivation that
    selects a tenth of the bundle, so the set is named against
    :func:`tests.constructed.records` and the documents contributing a mutation are reported
    as a proportion of it.
    """
    documents = claimed("documents", {document for document, _ in _mutations()})
    assert documents == set(constructed.records()), sorted(
        set(constructed.records()) - documents
    )
    contributing = claimed(
        "documents contributing at least one mutation",
        {document for (document, _), found in _mutations().items() if found},
        inside=documents,
    )
    ratchet(
        "documents per hundred contributing a mutation",
        round(100 * len(contributing) / len(documents)),
        at_least=95,
        because=(
            "a document contributes nothing only when no node of it has an admitted value; "
            "this rises as the construction reaches further and falls only on a regression"
        ),
    )


def test_the_mutation_reading_descends_by_the_one_descent_table() -> None:
    """The nodes a mutation is owed at are the nodes the compiler's own census reads.

    ``codegen.bundle.nodes`` descends by the table's descent column
    (``docs/plan/architecture.md`` §11: the descent column is the one owner), so "every node"
    means the same set of nodes to both halves of the pipeline.  A second descent here would
    be a second reading of one grammar, and the two would come to disagree about what a
    schema position is.
    """
    asked = claimed("nodes asked", set(_mutations()))
    walked = claimed(
        "nodes the one walk reaches",
        {
            (document, pointer)
            for document, record in constructed.records().items()
            for pointer, _ in bundle.nodes(record)
        },
    )
    assert asked == walked, sorted(walked - asked)[:5]
