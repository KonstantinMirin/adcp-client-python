"""A ``$ref`` that names a NODE -- inside another document, or inside this one.

`salesagent-j3k2l.14` (the absolute half) and `salesagent-j3k2l.20` (the local half).
A separate module from ``tests/test_emit.py`` because this grades one mechanism end to
end -- the ``#`` reading, the resolver's store, the name a referenced node gets, and
the import a referring module writes -- and because ``test_emit`` holds the metric
constants that are re-measured once per epic.

**One module for both halves because they are one mechanism split by the document
half.** ``bundle.split_ref`` reads the ``#`` once; ``bundle.named_nodes`` asks for a
symbol once, keyed on the document the reference RESOLVES AGAINST -- the one its
document half names, or the referrer when that half is empty; ``Module.declared`` maps
pointer to symbol once; and D3's nested rule names the node once.  They part company at
the last step and only there: an absolute reference becomes an IMPORT of a symbol the
target module declares (``emit.emit``'s binder), and a local one is a lookup in the
module being written (``compiler.local_reference``).  Grading them in two files would
be two records of one ``#``.

**The population this mechanism serves is almost entirely GATED BEHIND OTHER STEPS,
and that is why the constructed-bundle cases below exist.**  Measured at the sha this
landed on: 19 documents are named by a fragment, 18 of them are refused on a keyword
of their own, and the one that lowers -- ``core/version-envelope.json`` -- is named by
12 referrers that are each refused on another keyword.  So the real bundle exercises
the NAMING half (two aliases in the committed tree, asserted below) and reaches the
IMPORT half zero times.  Grading the import half only against the bundle would be a
pass over an empty loop, so it is graded on a bundle this file writes, which is the
same thing ``codegen`` does for every mechanism whose population a later step opens
(D5's mapping key rule says so in as many words).
"""

from __future__ import annotations

import ast
import functools
import importlib
import json
import socket
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import ValidationError

from adcp.types import _base
from adcp.types._base import applied_schema

from codegen import bundle, compiler, emit
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal
from compiled import compiled
import fresh
import populations
import compared
from conftest import refusal_from

from tests.nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: The tree a FRESH run emits, which is what every byte compare below is against
#: (``docs/plan/architecture.md``, 2026-10-29).  ``tests/fresh.py`` owns it;
#: ``tests/test_emit.py``'s ``test_the_committed_tree_is_what_a_fresh_run_emits`` is the
#: one check that reads ``src/``.
TREE = fresh.TREE

DRAFT = "http://json-schema.org/draft-07/schema#"
#: The base every reference in the 3.2 bundle is spelled under.  Written out here
#: because a CONSTRUCTED bundle has to spell its references the way a real one does
#: -- ``document_for`` matches a trailing run of path segments, so a test that
#: referenced ``other.json`` bare would grade a shorter path than the bundle uses.
BASE = "https://adcontextprotocol.org/schemas/9.9.9/"


@functools.cache
def fragment_refs() -> list[tuple[str, str, str]]:
    """``(referencing document, pointer, uri)`` for every fragment-bearing absolute
    reference in the bundle, read off the one schema-position walk."""
    return [
        (document, pointer, uri)
        for document in bundle.portable(BUNDLE)
        for pointer, uri, _ in bundle.references(bundle.read(BUNDLE, document))
        if all(bundle.split_ref(uri))
    ]


def node_at(doc: object, pointer: str) -> object:
    """The node a JSON Pointer names, or :data:`NOTHING`."""
    cur: object = doc
    for raw in [s for s in pointer.split("/") if s]:
        seg = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list) and seg.isdigit() and int(seg) < len(cur):
            cur = cur[int(seg)]
        elif isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return NOTHING
    return cur


NOTHING = object()


def kwargs_of(annotation: ast.AST) -> set[str]:
    """Every ``Field(...)`` keyword name anywhere in an annotation."""
    return {
        kw.arg
        for n in ast.walk(annotation)
        if isinstance(n, ast.Call)
        for kw in n.keywords
        if kw.arg
    }


def constraint_aliases(source: str | None = None) -> dict[str, set[str]]:
    """``adcp.types.constraints`` symbol -> the ``Field(...)`` keywords it states.

    ``source`` is the alias module's TEXT, defaulting to the committed one.  A caller
    emitting its own bundle passes that run's ``Emitted.beside`` entry instead, for the
    reason stated above about reading a fresh emission: a constructed bundle resolves a
    shape the committed module has no reason to carry, and grading against the
    committed file there would read a population this run did not emit.

    D5's rung 3 gave a constrained scalar a THIRD place to live. A node's own alias
    used to carry its constraints as kwargs; now the alias names a type in
    ``constraints`` and that type carries them, so an assertion reading only the
    alias's own kwargs reads a spelling D5 deliberately moved. Following the
    reference keeps the claim -- the constraint is reachable from the alias, and it
    is still nowhere near the property -- without weakening either half of it.
    """
    # The alias module a FRESH run writes, beside the fresh tree: it is this run's
    # output and not the checkout's, for ``TREE``'s reason one file over.
    source = (fresh.PACKAGE / "constraints.py").read_text() if source is None else source
    out: dict[str, set[str]] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                out[target.id] = kwargs_of(node.value)
    return out


def stated_by(annotation: ast.AST, named: dict[str, set[str]]) -> set[str]:
    """The keywords an annotation states, directly or through a named constrained
    type it references."""
    reached = {n.id for n in ast.walk(annotation) if isinstance(n, ast.Name)}
    return kwargs_of(annotation).union(*(named.get(n, set()) for n in reached), set())


# --------------------------------------------------------------------------- #
# the reading of the ``#``
# --------------------------------------------------------------------------- #
def test_split_ref_is_the_one_reading_of_the_hash() -> None:
    """Three callers read a ``$ref``'s two halves and they must agree.

    ``document_for`` matches the document half, ``resolved`` keys its store on it,
    and ``emit``'s binder needs both.  So the halves come from one function, and the
    two cases a caller branches on -- a LOCAL reference and an absolute one -- are
    distinguished by the document half being empty rather than by a second ``in``
    test somewhere.
    """
    assert bundle.split_ref("https://x.test/a/b.json") == ("https://x.test/a/b.json", "")
    assert bundle.split_ref("https://x.test/a/b.json#/properties/c") == (
        "https://x.test/a/b.json",
        "/properties/c",
    )
    assert bundle.split_ref("#/definitions/x") == ("", "/definitions/x")
    # A trailing ``#`` names the ROOT, which is a document reference with an empty
    # pointer and not a local one.
    assert bundle.split_ref("https://x.test/a/b.json#") == ("https://x.test/a/b.json", "")

    # ``document_for`` takes the DOCUMENT HALF and reads no ``#`` of its own, so the
    # two together are the whole resolution and there is one place the delimiter is
    # read.  Composed here the way all three callers compose them.
    known = {"core/catalog.json"}
    for uri in (
        "https://x.test/3.2.4/core/catalog.json",
        "https://x.test/3.2.4/core/catalog.json#/properties/category",
        "https://x.test/3.2.4/core/catalog.json#",
    ):
        assert bundle.document_for(bundle.split_ref(uri)[0], known) == "core/catalog.json", uri
    # A local reference names no document, which is NOT the same as an unresolvable
    # one.  The caller tells them apart on the document half being EMPTY, which is why
    # this is ``None`` and not a refusal.
    assert bundle.split_ref("#/definitions/x")[0] == ""
    assert bundle.document_for("", known) is None
    assert bundle.document_for("https://x.test/3.2.4/core/absent.json", known) is None


def test_every_fragment_reference_in_the_bundle_names_a_node_that_exists() -> None:
    """The gate this step removes was never about a missing file.

    Both halves of every site: the document half resolves to a document of this
    bundle, and the pointer half names a node that is actually in it.  The three sets
    -- sites, distinct targets, target documents -- are asserted NON-EMPTY rather than
    sized, because what the sizes were standing in for is that a selector which
    silently stopped matching would turn this into a pass over an empty loop, and this
    test's whole job is to say the references are sound.
    """
    sites = claimed("fragment reference sites", fragment_refs())
    known = set(bundle.portable(BUNDLE))
    targets = set()
    for document, pointer, uri in sites:
        head, into = bundle.split_ref(uri)
        target = bundle.document_for(head, known)
        assert target is not None, (document, pointer, uri)
        assert node_at(bundle.read(BUNDLE, target), into) is not NOTHING, (document, uri)
        targets.add((target, into))
    claimed("distinct (document, pointer) targets", targets)
    claimed("target documents", {t for t, _ in targets})
    assert ("core/catalog.json", "/properties/category") in targets


def test_no_portable_documents_reference_closure_names_a_document_this_bundle_lacks() -> None:
    """``bundle.record``'s store loop, over the whole population, with the
    inlining left off.

    **INSTRUMENT, stated because it is not the function itself.**  ``resolved`` has a
    documented O(paths) ceiling -- the bundle holds a 9,109-byte document that
    resolves to 4.8 MB -- so calling it 1,054 times does not belong in a suite.  What
    RAISES is the STORE loop, which is this; the inlining that follows cannot raise
    for a reference the store already holds.  ``resolved`` itself is exercised on a
    real fragment-bearing document in the next test, and on 13 more in the one after,
    which is where the inlining is graded.

    Measured before this step: the loop raised for 151 of the 1,054 -- 88 reaching an
    absolute fragment reference and 63 more whose only unresolvable reference was a
    pointer into THEMSELVES.  Both are zero now, and 0 is the whole point: a document
    this gate closes on can be neither emitted nor refused on a keyword of its own.
    """
    known = set(bundle.portable(BUNDLE))
    read = {d: bundle.read(BUNDLE, d) for d in known}
    unresolvable: list[tuple[str, str, str]] = []
    for document in sorted(known):
        store: dict[str, dict] = {}
        queue = [read[document]]
        while queue:
            for pointer, uri, _ in bundle.references(queue.pop()):
                head = bundle.split_ref(uri)[0]
                if not head or head in store:
                    continue
                target = bundle.document_for(head, known)
                if target is None:
                    unresolvable.append((document, pointer, uri))
                    continue
                store[head] = read[target]
                queue.append(store[head])
    assert unresolvable == [], unresolvable[:10]
    claimed("bundle.portable", known)


def test_resolved_inlines_the_node_a_fragment_names_and_not_the_whole_document() -> None:
    """The store is keyed on the DOCUMENT URI and the resolver follows the pointer.

    Keying it on the FULL URI is what this did, and it is the other half of the gate:
    probed on ``hypothesis_jsonschema``'s resolver, a store holding the target under
    ``<uri>#/properties/x`` raises ``_RefResolutionError`` ("does not fetch remote
    references") while the same target under ``<uri>`` inlines the node.  So removing
    the ``None`` alone would have left the reference unresolvable with its target
    read in -- which is why this asserts the inlined VALUE and not merely that
    nothing raised.

    On a real document, because the claim is about this bundle.
    ``core/catalog-selection.json`` names ``core/catalog.json#/properties/type``, and
    that node is ITSELF a ``$ref`` -- so this also grades the chain: a fragment to a
    reference resolves through to the node at the end of it, which is the enum.
    """
    document = "core/catalog-selection.json"
    known = set(bundle.portable(BUNDLE))
    uri = bundle.read(BUNDLE, document)["properties"]["type"]["$ref"]
    head, into = bundle.split_ref(uri)
    assert into == "/properties/type", uri
    target = bundle.document_for(head, known)
    assert target == "core/catalog.json", target
    got = bundle.record(BUNDLE, document, known)["properties"]["type"]
    assert "$ref" not in got, got
    # The NODE, resolved the way the TARGET's own document resolves it -- not the
    # document the node lives in.  A resolver that substituted the whole target would
    # put ``core/catalog.json``'s other properties and its title here.
    assert got == bundle.record(BUNDLE, target, known)["properties"][into.split("/")[-1]], got
    assert "properties" not in got, "the whole target document was inlined, not the node"
    assert "enum" in got, got


def test_a_local_reference_is_left_in_the_record_exactly_as_the_document_writes_it() -> None:
    """**ROW .3's rule, and it reverses this test's old answer.**

    Architecture §4: "a local ``$ref`` stays as written".  It names a node of the very
    document the package carries, so ``jsonschema`` resolves it against the referrer and
    fetches nothing -- and §3's "nothing else changed" means the record does not inline
    what it does not have to.  The delegated resolver inlined one, through
    ``LocalResolver(referrer=doc)``, which is why this test used to measure how many
    survived: 3 of the 13 did, the ones whose chain is RECURSIVE and has no finite
    inlining.

    Now all 13 keep every local reference they state, and that is the stronger claim,
    because it is a property of the inliner rather than of what the library could
    manage.  ``harness._normalize`` resolves a local ``$ref`` against the whole
    resolved DOCUMENT, which is the reading architecture §9 keeps for exactly
    this; and ``bundle.undecidable_references`` counts none of them, because a
    local reference is decidable at every position.

    Asserted in both directions over every document whose references are all local: the
    record's local references are the document's own, pointer for pointer and URI for
    URI, and it holds no cross-document reference at all.

    **READ THROUGH THE RECORD'S OWN STORAGE** (``docs/plan/architecture.md``, "THE
    RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT").  A record stores each distinct
    subtree once and writes a local reference of its own at every occurrence, so the
    record's reference list is the document's PLUS the storage's -- and 11 of these 13
    documents have a repeated subtree.  The claim this test makes is about the
    document's own references, so it is asked of the record with the storage put back:
    that is the text §4's rule is about, and ``bundle.expanded`` is the inverse that
    produces it.  The storage's own references are asserted separately, as the only
    others the record holds.
    """
    local = [
        d
        for d in bundle.portable(BUNDLE)
        if (rs := bundle.references(bundle.read(BUNDLE, d)))
        and all(not bundle.split_ref(u)[0] for _, u, _ in rs)
    ]
    claimed("documents whose every reference is local", local, inside=bundle.portable(BUNDLE))
    recursive = {
        "core/bidding-policy-capability.json",
        "core/placement-presentation.json",
        "governance/reported-outcome-error.json",
    }
    assert recursive <= set(local), sorted(recursive - set(local))
    known = set(bundle.portable(BUNDLE))
    for document in local:
        raw = bundle.read(BUNDLE, document)
        record = bundle.record(BUNDLE, document, known)
        assert not isinstance(record, Refusal), (document, record)
        assert bundle.references(bundle.expanded(record, record)) == bundle.references(raw), (
            document
        )
        # Every reference the STORED text holds is one the document STATES or one the
        # storage wrote, which is what makes the comparison above the whole reading.
        # Compared by URI and not by pointer, because a reference inside a subtree the
        # storage stored is at the entry's pointer and not at its own -- which is the
        # storage's whole mechanism and is exactly what the expansion above undoes.
        spelled = {u for _, u, _ in bundle.references(raw)}
        foreign = [
            (p, u)
            for p, u, _ in bundle.references(record)
            if u not in spelled and not _base.is_a_store_entry(u.rsplit("/", 1)[-1])
        ]
        assert foreign == [], (document, foreign[:5])
        assert bundle.undecidable_references(
            record, bundle.named_nodes(BUNDLE).get(document, frozenset())
        ) == [], document
    # The three whose chain is recursive are still in the set and are no longer special:
    # named here so a reading that started inlining a local reference again reddens
    # with the documents it cannot finish on.
    claimed("locally-referencing documents with a recursive chain", recursive, inside=set(local))


# --------------------------------------------------------------------------- #
# the record's TEXT: a DAG, with its pointers unmoved
# --------------------------------------------------------------------------- #
@functools.cache
def carried() -> dict[str, dict]:
    """What the emitter writes beside every module: the record, or the document itself.

    ``emit.emit``'s own condition, read here so the pointer check below asks its question
    of the text the PACKAGE carries rather than of a second rendering of it.
    """
    return {
        document: records().get(document) or bundle.read(BUNDLE, document)
        for document in bundle.portable(BUNDLE)
    }


@functools.cache
def records() -> dict[str, dict]:
    """The RECORD of every portable document that states a reference.

    **``emit.emit``'s own condition and not a second one**, which is also the set the
    three checks below are stated over: the emitter takes the record of a document that
    STATES a reference and writes the document ITSELF otherwise, so a reference-free
    document records as itself and nothing of :func:`bundle.stored` reaches it.  The
    duplication such a document's own text holds is UPSTREAM's -- 21 of the 364 have some
    -- and reading 5 is already satisfied there, the record being the source byte for
    byte.  Including them would state a property of the bundle's authors as a property of
    this inliner.
    """
    known = set(bundle.portable(BUNDLE))
    out = {}
    for document in bundle.portable(BUNDLE):
        raw = bundle.read(BUNDLE, document)
        if not bundle.references(raw):
            continue
        record = bundle.record(BUNDLE, document, known)
        assert not isinstance(record, Refusal), (document, record)
        out[document] = record
    return out


def test_a_record_states_each_distinct_subtree_once() -> None:
    """``docs/plan/final-state.md`` reading 5, as a property of every record's TEXT.

    ``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT":
    "The record stores each distinct subtree once under its own ``definitions`` with a
    local reference at each occurrence."  So no two schema positions of one record hold
    equal content -- which is the reading stated exactly, with no byte figure in it.
    Asserted as the property rather than as a size: a ratio is one bundle's reading of
    a quantity the next upstream release moves, and the property is what the storage
    guarantees.

    **The one admitted repetition is a BARE REFERENCE**, which is
    ``bundle.stored``'s second exclusion and not a threshold: storing a node that is
    already a reference writes a reference to a reference, which is longer than the
    node it replaces and states the same thing.  So the storage's own reference nodes
    repeat, and so do a document's.

    It reads the stored text AS WRITTEN -- one pointer per occurrence, which is what
    ``bundle.nodes`` answers -- and takes no position on whether that walk should
    follow a reference.  That is the fork the architecture section defers and this
    check does not need: the question here is what the TEXT states, and the text is
    what the walk reads.

    The measured before/after of this property on the 3.2 bundle is on
    ``adcp-client-python-82m.25``: 835,864,437 bytes of record became 67,638,592, and
    ``core/mcp-webhook-payload.json``'s 112,920,473 became 2,272,167.
    """
    every = records()
    claimed("records of documents that state a reference", every, inside=bundle.portable(BUNDLE))
    for document, record in sorted(every.items()):
        seen: dict[str, str] = {}
        twice: list[tuple[str, str]] = []
        for pointer, node in bundle.nodes(record):
            if len(node) == 1 and "$ref" in node:
                continue
            key = json.dumps(node, sort_keys=True, default=str)
            if key in seen:
                twice.append((seen[key], pointer))
            else:
                seen[key] = pointer
        assert not twice, (document, len(twice), twice[:3])


def test_the_storage_states_what_the_inlined_record_states() -> None:
    """``bundle.stored`` and ``bundle.expanded`` are inverses, over every record.

    The architecture section calls the hoisting "a storage representation ... not a
    renaming", and this is that sentence as a property: putting the storage back gives
    the inlined text, and storing the inlined text again gives exactly the record the
    package carries.  Both directions, because each catches a different defect -- a
    storage that dropped a keyword fails the first, and one whose entry names moved with
    something other than the content fails the second.

    One consequence is asserted by name because a reader will ask about it: a document
    that states an empty section and also has a subtree stored comes back from the
    expansion with no section at all.  Draft-07 gives a ``definitions`` section no
    assertion behaviour, so the two state the same thing; 0 documents of this bundle
    state an empty one, which is why the round trip is exact here.

    **THE TWO DIRECTIONS RANGE OVER TWO POPULATIONS, AND THE WIDER ONE IS THE ROUND
    TRIP** (``adcp-client-python-n1t``).  ``stored(inlined) == record`` is a claim about
    the COMMITTED record, so it is only askable of a document that HAS one -- the set
    :func:`records` names, which is ``emit.emit``'s own condition.
    ``expanded(stored(x)) == x`` is not: it is a property of the two functions and of
    nothing else, true or false of any record-shaped input, so narrowing it to the same
    set narrows it for a reason that belongs to the other direction.

    The narrowing was INHERITED and its stated reason does not reach here.
    :func:`records` excludes a reference-free document because "including them would
    state a property of the bundle's authors as a property of this inliner" -- which is
    exactly right for reading 5 next door, where upstream's own duplication would be
    mis-attributed, and is not a reason to leave ``stored`` ungraded on an input.  So the
    round trip is asked of :func:`carried`, every portable document, and the 21 it adds
    on which ``stored`` does real work are claimed by name below: they are the inputs
    where ``stored`` hoists and the committed-record direction never runs it.

    **Measured at the row that widened it**, in 6.4 s and 71 MB of peak RSS over the
    whole bundle: 0 failures either direction.  20,656 entries are hoisted across the 516
    records that have storage, and the widening adds 42 more across the 21 reference-free
    documents whose own text repeats a subtree -- 537 documents hoisting in all.  Both
    figures are derived by the loops below rather than asserted, for the reason the first
    rule of ``tests/test_every_check_names_its_set.py`` gives.
    """
    every = records()
    claimed("records of documents that state a reference", every, inside=bundle.portable(BUNDLE))
    empty_sections = {
        d
        for d, raw in ((d, bundle.read(BUNDLE, d)) for d in bundle.portable(BUNDLE))
        for _, node in bundle.nodes(raw)
        for kw in bundle.DEFINITIONS
        if isinstance(node.get(kw), dict) and not node[kw]
    }
    assert empty_sections == set(), sorted(empty_sections)

    #: The ROUND TRIP first, over the wider population, and the order is not cosmetic.
    #: ``stored(expanded(r)) == r`` below is strictly DOWNSTREAM of ``expanded`` -- it
    #: consumes its output -- so every perturbation of the expansion reddens it too, and
    #: whichever of the two runs first is the one that reports.  Asked in this order, a
    #: broken expansion is reported as the property it broke rather than as a record that
    #: stopped matching, which is the difference between a verdict and a symptom.
    text = claimed(
        "the text the package carries beside every module",
        carried(),
        inside=bundle.portable(BUNDLE),
    )
    hoisted_outside_the_committed_records = []
    for document in sorted(text):
        held = carried()[document]
        inlined = bundle.expanded(held, held)
        again = bundle.stored(inlined)
        assert bundle.expanded(again, again) == inlined, (
            f"{document}: expanded(stored(x)) is not x. The storage is "
            "'a storage representation ... not a renaming', so a reader that puts it "
            "back must get the text the record stated before it existed."
        )
        if document not in every and again != inlined:
            hoisted_outside_the_committed_records.append(document)
    claimed(
        "reference-free documents whose OWN text the storage hoists",
        hoisted_outside_the_committed_records,
        inside=set(text) - set(every),
    )

    stored_at_all = []
    for document, record in sorted(every.items()):
        inlined = bundle.expanded(record, record)
        assert bundle.stored(inlined) == record, document
        if inlined != record:
            stored_at_all.append(document)
    claimed("records the storage changes", stored_at_all, inside=set(every))


def test_no_entry_under_the_store_prefix_is_a_documents_own() -> None:
    """The assumption ``is_a_store_entry`` is EXACT under, re-read off the bundle.

    ``adcp/types/_base.py`` beside :data:`adcp.types._base.STORE_PREFIX`: "**No document
    of the bundle names an entry under this prefix**, which is what keeps the predicate
    below exact rather than approximate".  Nothing re-read it
    (``adcp-client-python-n1t``), and the predicate is the one two readers agree through
    -- ``bundle.stored`` refuses to write an entry a document already holds, and
    ``bundle.expanded`` DROPS exactly the entries it matches.  So a document of its own
    naming ``Shared7`` would not merely collide: the expansion would delete a section
    entry the document states, and every reference to it would stop resolving.

    Asked of the RAW text and of the RECORDED text, because the two can diverge and only
    the first is upstream's: ``bundle.record`` inlines, so a raw document with no section
    can record with one.  In the recorded text an entry under the prefix is expected and
    is the storage's, so what is asserted there is the other half of the same exactness
    -- the storage writes its entries at the ROOT section and nowhere else, which is what
    makes dropping them at the root sufficient.

    **Measured: 0 of 168 entries across 46 ``definitions``/``$defs`` sections of the raw
    bundle match, and 0 of the recorded prefix entries sit below a root.**  A zero
    reading is the point rather than a weakness here -- the predicate is exact only while
    it is zero, and the sentence asserting it had no instrument.  The population is
    claimed so the zero cannot be the vacuous one.
    """
    sections = []
    own = []
    for document in sorted(bundle.portable(BUNDLE)):
        raw = bundle.read(BUNDLE, document)
        for pointer, node in bundle.nodes(raw):
            for kw in bundle.DEFINITIONS:
                section = node.get(kw)
                if not isinstance(section, dict):
                    continue
                sections.append((document, pointer, kw))
                own += [
                    (document, pointer, kw, key)
                    for key in section
                    if _base.is_a_store_entry(key)
                ]
    claimed("definition sections the raw bundle states", sections)
    assert not own, (
        f"a document of the bundle names {len(own)} entry/entries under "
        f"{_base.STORE_PREFIX!r}: {own[:3]}. ``bundle.expanded`` drops every entry "
        "``is_a_store_entry`` matches, so this is a section entry the expansion would "
        "delete from the document that states it."
    )

    below_a_root = []
    entries = []
    for document, record in sorted(records().items()):
        for pointer, node in bundle.nodes(record):
            section = node.get(_base.STORE_SECTION)
            if not isinstance(section, dict):
                continue
            for key in section:
                if not _base.is_a_store_entry(key):
                    continue
                entries.append((document, pointer, key))
                if pointer != "":
                    below_a_root.append((document, pointer, key))
    claimed("entries the storage wrote across every record", entries)
    assert not below_a_root, (
        f"the storage wrote {len(below_a_root)} entry/entries below a record's root: "
        f"{below_a_root[:3]}. ``store_expanded`` drops the section at every node it "
        "walks, but a reference is resolved against the ROOT, so an entry below one "
        "names a node no reader reaches."
    )


def test_a_stored_subtree_is_never_itself_a_bare_reference() -> None:
    """Why ONE storage hop suffices, as the property rather than as the bound.

    :func:`adcp.types._base.through_the_store`: "One hop suffices and the loop is bounded
    for the reason it suffices: a stored subtree is never itself a bare reference
    (``bundle.stored`` stores no node that already is one), so a storage reference
    resolves to a node that is not another.  The bound is written anyway, and raises,
    because a cycle here is a defect of the writer and the alternative to raising is a
    hang."  The bound is the DETECTION and this is the PREVENTION, and only the bound was
    ever instrumented (``adcp-client-python-n1t``) -- a loop that has never been asked to
    go round twice is a loop whose first iteration nothing has measured.

    Two readings of one property, and the second is the one a reader of the docstring
    wants.  No entry of any record's store IS a bare reference; and consequently every
    storage reference in every record resolves, in ONE hop, to a node that is not another
    storage reference -- which is what :data:`adcp.types._base._STORE_HOPS` being larger
    than one is insurance against rather than a requirement of.

    Measured over the 20,656 entries the 516 records with storage hold: 0 are a bare
    reference, and 0 references take a second hop.  The bound is therefore dead code on
    this bundle, which is the right state for it and not an argument to delete it: it is
    what turns a writer's defect into a ``LookupError`` instead of a hang.
    """
    entries = []
    bare = []
    second_hop = []
    for document, record in sorted(records().items()):
        section = record.get(_base.STORE_SECTION) or {}
        for key, held in section.items():
            if not _base.is_a_store_entry(key):
                continue
            entries.append((document, key))
            if isinstance(held, dict) and len(held) == 1 and "$ref" in held:
                bare.append((document, key, held))
        for pointer, node in bundle.nodes(record):
            if len(node) != 1 or not isinstance(node.get("$ref"), str):
                continue
            once = _base.through_the_store(node, record)
            if once is node:
                continue  # a document's OWN local reference, which the hop leaves alone
            if _base.through_the_store(once, record) is not once:
                second_hop.append((document, pointer, node["$ref"]))
    claimed("entries the storage wrote across every record", entries)
    assert not bare, (
        f"{len(bare)} stored subtree(s) are themselves a bare reference: {bare[:3]}. "
        "Storing one writes a reference to a reference, which is longer than the node "
        "it replaces and is what makes a single hop insufficient."
    )
    assert not second_hop, (
        f"{len(second_hop)} storage reference(s) need a second hop: {second_hop[:3]}. "
        "``through_the_store`` is documented as transparent at one hop; a chain means "
        "``bundle.stored`` stored a node that was already a reference."
    )


def test_the_storage_moves_no_pointer_any_reader_spells() -> None:
    """**THE HARD CONSTRAINT of the architecture section**, over every declared pointer.

    "Every pointer any reader SPELLS keeps the spelling it has today ... a declared
    pointer that stops resolving is a defect of the hoisting rather than a consequence
    of it."  ``harness.corpus_key`` hashes the document's raw bytes and the POINTER, so
    a respelled pointer misses every committed corpus entry and redraws its pair at the
    cold cost; the storage is therefore invisible to the pointer, and this is the check
    that says so.

    Asked of the SchemaRef every class and alias of the tree declares, through the one
    function that resolves one -- ``_base.schema_at``, which is what ``strict_validate``
    and the harness both reach the schema half through.  Two answers per pointer: it
    resolves, and it resolves to the node the INLINED text gives at the same pointer.
    The second is the one that matters: a pointer that resolves to a bare reference
    would resolve and would state nothing, because draft-07 ignores every sibling of a
    ``$ref``.

    The four pointers that do not resolve are a DIFFERENT defect and are named rather
    than skipped: each names a node under a conjunct that is a document's OWN local
    reference, which ``applied_schema`` does not follow and which the storage does not
    touch (``adcp-client-python-82m.26``).  They fail identically with the storage and
    without it, which is what the inlined half of this check reads.
    """
    every = carried()
    refs = claimed(
        "the SchemaRefs the tree declares",
        {ref for ref, *_ in compared.pairs()},
    )
    inlined = {d: bundle.expanded(r, r) for d, r in every.items()}

    def answer(root: dict, pointer: str) -> Any:
        try:
            return applied_schema(root, pointer)
        except Exception as e:  # noqa: BLE001 -- the failure is the answer being compared
            return f"{type(e).__name__}: {e}"

    unresolved, moved = [], []
    for ref in sorted(refs):
        was = answer(inlined[ref.document], ref.pointer)
        now = answer(every[ref.document], ref.pointer)
        if isinstance(now, str):
            if not isinstance(was, str):
                unresolved.append(f"{ref.document}{ref.pointer}: {now}")
            continue
        if bundle.expanded(now, every[ref.document]) != was:
            moved.append(f"{ref.document}{ref.pointer}")
    assert unresolved == [], unresolved[:10]
    assert moved == [], moved[:10]


# --------------------------------------------------------------------------- #
# the naming: a referenced node gets a symbol in ITS OWN module
# --------------------------------------------------------------------------- #
def test_the_named_node_population_is_read_off_the_bundle_and_not_off_a_run() -> None:
    """``bundle.named_nodes`` is a function of the BUNDLE (P7).

    A module whose CONTENT varied with which other documents a run named would make
    the committed tree a function of the last population that ran, and the gate's
    byte compare would then grade whichever that was.  So the same document emitted
    ALONE and emitted with everything else produces the same module -- asserted here
    on the one named document that lowers.

    A LOCAL reference satisfies P7 for a sharper reason, and `salesagent-j3k2l.20` is
    why it is in here now: the document asking and the document asked are the same
    file, so no other document of the bundle can affect the answer at all.
    """
    named = bundle.named_nodes(BUNDLE)
    # The named nodes, in three parts that are asserted separately below: the ABSOLUTE
    # fragment references, the LOCAL ones, and the documents named by BOTH kinds.  Each
    # part is asserted non-empty, which is what the six counts were standing in for --
    # a regression that dropped either arm reddens with the arm NAMED rather than
    # moving one total.
    claimed("documents with a named node", named)
    claimed(
        "named (document, pointer) nodes",
        {(d, p) for d, ps in named.items() for p in ps},
    )
    assert named["core/version-envelope.json"] == frozenset(
        {"/properties/adcp_version", "/properties/adcp_major_version"}
    )

    # The two kinds, split by the document half the way ``split_ref`` splits it, so a
    # regression that dropped either arm reddens with the arm named rather than moving
    # one total.
    halves: dict[bool, dict[str, set[str]]] = {True: {}, False: {}}
    known = set(bundle.portable(BUNDLE))
    for document in known:
        for _, uri, _ in bundle.references(bundle.read(BUNDLE, document)):
            head, pointer = bundle.split_ref(uri)
            if not pointer:
                continue
            target = bundle.document_for(head, known) if head else document
            if target is not None:
                halves[bool(head)].setdefault(target, set()).add(pointer)
    absolute, local_refs = halves[True], halves[False]
    claimed("documents named by an ABSOLUTE fragment reference", absolute)
    claimed("documents named by a LOCAL reference", local_refs)
    claimed("(document, pointer) named absolutely", {(d, p) for d, ps in absolute.items() for p in ps})
    claimed("(document, pointer) named locally", {(d, p) for d, ps in local_refs.items() for p in ps})
    # The overlap is the fact, and it is asserted at both granularities: some documents
    # are named by each kind, and some of those are named at the SAME pointer by each.
    # Both sets non-empty, because an empty overlap would make the two arms independent
    # and the union below would say nothing about either.
    both = claimed("documents named by both kinds", set(absolute) & set(local_refs))
    claimed(
        "pointers named by both kinds",
        {(d, p) for d in both for p in absolute[d] & local_refs[d]},
    )

    # ``core/bidding-policy-capability.json`` references only itself, 4 times.  It is
    # here now, under its OWN name and its own four pointers -- which is the whole of
    # `salesagent-j3k2l.20`'s bundle-side change, and the assertion was its ABSENCE
    # before that.
    assert named["core/bidding-policy-capability.json"] == frozenset(
        {
            "/definitions/max_bid_with_cost_per",
            "/definitions/max_bid_with_roas",
            "/definitions/policy_profile",
            "/definitions/scope_capability",
        }
    ), sorted(named["core/bidding-policy-capability.json"])
    # And it is not listed as a TARGET of anything else: a local reference names its
    # own document and never another, so no absolute half resolved to it.
    assert "core/bidding-policy-capability.json" not in absolute

    document = "core/version-envelope.json"
    alone = compiled(BUNDLE, [document])
    rel = f"{emit.module_file(document, fresh.PACKAGES)}.py"
    assert alone.files[rel] == (TREE / rel).read_text()


def test_a_named_node_is_declared_once_in_its_own_module_and_the_property_uses_it() -> None:
    """D2 makes these two nodes annotations, so a fragment reference had nothing to
    import.  Now each has a symbol, named by D3's nested rule, and the node's
    constraints live on it ALONE -- the property references the symbol rather than
    restating the bound, so the module spells each fact once.

    On the one real document a fragment names that also lowers, and off a FRESH
    emission rather than the committed file: a test that parses the committed bytes
    grades whatever the last run wrote, so a regression in the emitter survives it
    until somebody re-emits.  The committed tree is tied to the fresh emission by the
    byte compare below, separately.  Read off the AST, not the text.
    """
    document = "core/version-envelope.json"
    tree = ast.parse(
        compiled(BUNDLE, [document]).files[f"{emit.module_file(document, fresh.PACKAGES)}.py"]
    )
    aliases = {
        t.target.id: t.value
        for t in tree.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    } | {
        a.targets[0].id: a.value
        for a in tree.body
        if isinstance(a, ast.Assign) and isinstance(a.targets[0], ast.Name)
    }
    # §4's nested rule names a position and not the path to it
    # (``adcp-client-python-10l.50``): the two were
    # ``AdCPVersionEnvelopeAdcpVersion`` and ``AdCPVersionEnvelopeAdcpMajorVersion``
    # while the fold concatenated every hop to the root, and the module path is what
    # carries the document.  Two names, the same two positions.
    assert "AdcpVersion" in aliases, sorted(aliases)
    assert "AdcpMajorVersion" in aliases, sorted(aliases)

    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef))
    fields = {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }
    # **Each constraint the document states is on the ALIAS and on nothing else.**  On
    # the kwarg NAMES rather than on the rendered text, because a pattern's backslashes
    # are escaped twice through ``ast.unparse`` and a text match there grades a
    # spelling.  The document's own keywords, in pydantic's names, come from the
    # document.
    for key, symbol, stated in (
        ("adcp_version", "AdcpVersion", {"pattern"}),
        ("adcp_major_version", "AdcpMajorVersion", {"ge", "le"}),
    ):
        named = constraint_aliases()
        on_alias = stated_by(aliases[symbol], named)
        on_field = kwargs_of(fields[key])
        assert stated <= on_alias, (symbol, sorted(on_alias))
        assert not stated & on_field, (key, sorted(on_field))
        assert symbol in {n.id for n in ast.walk(fields[key]) if isinstance(n, ast.Name)}, key
        # Nothing but a name and a description rides on the property: a constraint of
        # the node has nowhere else in the module to hide.
        assert on_field <= {"description", "alias", "default", "json_schema_extra"}, (
            key,
            sorted(on_field),
        )


# --------------------------------------------------------------------------- #
# the import: on a bundle this file writes, because the real one reaches it 0 times
# --------------------------------------------------------------------------- #
def write_bundle(tmp_path: Path, documents: dict[str, dict]) -> Path:
    """A bundle directory holding exactly ``documents``, references spelled the way
    the real bundle spells them."""
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


TARGET = {
    "title": "Catalog Like",
    "type": "object",
    "properties": {
        # A CONSTRAINED SCALAR: D2 makes it an annotation, so it has no symbol until
        # something names it, and the constraint is what makes "an import, not a copy"
        # falsifiable.  16 of the bundle's 76 fragment targets are this shape, and
        # ``core/version-envelope.json``'s two -- the only ones in a document that
        # lowers -- are among them.
        "category": {"type": "string", "minLength": 2, "maxLength": 9},
        # An ARRAY beside it, the commonest shape among the 76 (30 of them), so the
        # import is graded on more than one of D2's annotation rows.  Unconstrained:
        # a bound INSIDE a container is D5's named-type row and refuses until
        # ``salesagent-j3k2l.12`` lands, which is a different step's gate.
        "tags": {"type": "array", "items": {"type": "string"}},
        "label": {"type": "string"},
    },
}
REFERRER = {
    "title": "Selection Like",
    "type": "object",
    "properties": {
        "kind": {"$ref": f"{BASE}core/target.json#/properties/category"},
        "marks": {"$ref": f"{BASE}core/target.json#/properties/tags"},
    },
}


def test_a_fragment_reference_is_an_import_of_the_targets_symbol_and_not_a_copy(
    tmp_path: Path,
) -> None:
    """The exit condition, on the AST: a fragment resolves to an IMPORT of a symbol
    the TARGET module declares, never to a copy.

    Both halves, because either alone passes while the other fails: the referring
    module imports ``(relative module, symbol)``, and its field names that symbol and
    carries none of the target's constraints.  ``minLength``/``maxLength`` are the
    target's, and a copy would put them here.
    """
    root = write_bundle(
        tmp_path, {"core/target.json": TARGET, "core/selection.json": REFERRER}
    )
    out = emit.emit(root, ["core/selection.json"])
    assert out.refusals == {}, out.refusals
    # The target emits too, though nothing named it: a module cannot import from a
    # module no run wrote.
    assert sorted(out.emitted) == ["core/selection.json", "core/target.json"], out.emitted

    tree = ast.parse(out.files["core/selection.py"])
    imported = {
        ("." * n.level + (n.module or ""), a.name)
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    # A hand-built two-document bundle, so no document of it is a package root
    # (``bundle.package_roots``) and the spelling is the ordinary sibling one.
    module = emit.relative_module("core/selection.json", "core/target.json", frozenset())
    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef))
    fields = {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }
    target_tree = ast.parse(out.files["core/target.py"])
    declared = {
        a.targets[0].id for a in target_tree.body if isinstance(a, ast.Assign)
    } | {a.target.id for a in target_tree.body if isinstance(a, ast.AnnAssign)}

    # D3: ``pascal_case(property)`` for the property's OWN position, assigned by
    # ``lower/names.py`` and not here -- the module path carries the document (§4, and
    # ``adcp-client-python-10l.50``), so neither name repeats the target's title.
    for key, symbol in (("kind", "Category"), ("marks", "Tags")):
        assert (module, symbol) in imported, (key, sorted(imported))
        got = fields[key]
        assert symbol in {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}, key
        assert kwargs_of(got) <= {"description", "alias", "default", "json_schema_extra"}, (
            key,
            sorted(kwargs_of(got)),
        )
        # And the symbol the import names is really DECLARED there, by the target --
        # not merely present in its text and not imported into it from elsewhere.
        assert symbol in declared, (symbol, sorted(declared))

    # The unnamed property keeps its inline annotation: a node nothing references is
    # not given a symbol, so this mechanism does not rename the whole bundle.
    assert "CatalogLikeLabel" not in declared, sorted(declared)


def test_a_class_for_a_fragment_target_names_the_targets_document_and_pointer(
    tmp_path: Path,
) -> None:
    """A fragment target that IS a class carries ``__adcp_schema__`` naming the
    TARGET's document and the node's own pointer -- never the referring document.

    There is no binding table and no adapter: the class finds its schema through its
    own attribute, so a grader cannot be aimed at the wrong tree.
    """
    target = {
        "title": "Holder",
        "type": "object",
        "properties": {
            "inner": {
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "required": ["a"],
            }
        },
    }
    referrer = {
        "title": "Points At Inner",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/holder.json#/properties/inner"}},
    }
    root = write_bundle(tmp_path, {"core/holder.json": target, "core/pointer.json": referrer})
    out = emit.emit(root, ["core/pointer.json"])
    assert out.refusals == {}, out.refusals
    tree = ast.parse(out.files["core/holder.py"])
    inner = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == "Inner")
    ref = next(
        ast.unparse(t.value)
        for t in inner.body
        if isinstance(t, ast.AnnAssign) and getattr(t.target, "id", None) == "__adcp_schema__"
    )
    assert "core/holder.json" in ref, ref
    assert "#/properties/inner" in ref, ref
    assert "pointer.json" not in ref, ref
    # A node that is already a class is NOT given a second symbol beside it.
    assert [c.name for c in tree.body if isinstance(c, ast.ClassDef)].count("Inner") == 1
    assert "Inner = " not in out.files["core/holder.py"]


# --------------------------------------------------------------------------- #
# the refusals: by name, pointer and keyword, with the fragment named
# --------------------------------------------------------------------------- #
def refusal_for(root: Path, document: str) -> dict[str, str]:
    out = emit.emit(root, [document])
    assert document in out.refusals, out.emitted
    return out.refusals[document]


def test_a_fragment_naming_a_node_the_walk_never_reaches_is_refused_with_it_named(
    tmp_path: Path,
) -> None:
    """A pointer into a section the lowering does not descend has no symbol, and the
    document is refused by name, pointer and keyword rather than bound to the root.

    Binding it to the root instead would import a class for the WHOLE document where
    the document names one node of it -- a model wider than its schema, silently.
    17 of the bundle's 76 fragment targets are ``definitions`` entries, which is
    exactly this case (their documents refuse on ``definitions`` first today).
    """
    target = {
        "title": "Has A Def",
        "type": "object",
        "properties": {"a": {"type": "string"}},
    }
    referrer = {
        "title": "Names A Missing Node",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/hasadef.json#/properties/nope"}},
    }
    root = write_bundle(tmp_path, {"core/hasadef.json": target, "core/names.json": referrer})
    r = refusal_for(root, "core/names.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    assert "/properties/nope" in r["detail"], r
    assert "core/hasadef.json" in r["detail"], r


def test_a_fragment_whose_node_is_itself_a_ref_imports_from_the_declaring_module(
    tmp_path: Path,
) -> None:
    """The chain is FOLLOWED to the module that declares the symbol (``_declaring_site``).

    §5's ``$ref`` row reads "a fragment of another document → an import of a symbol the
    target DECLARES", and the node a fragment names may be itself a ``$ref``: the middle
    module then IMPORTS that symbol and declares nothing at the pointer, so the row's
    sentence names no symbol at that site.  Binding the middle module's imported name
    would be a re-export and §1's second way to reach one class; following the chain is
    one import path per class, taken FROM THE DECLARER.

    Both halves are asserted, because either alone passes while the other fails: the
    referrer imports from the DECLARING module (not the middle one), and the middle
    module is still the one whose node supplies the field's own ``description`` -- §5's
    ``$ref`` row gives an annotation sibling of a ``$ref`` the answer "the sibling's
    description wins", and ``bundle.record`` inlines exactly that text at the referring
    pointer, so a chain that dropped it would report *missing* at a pointer it reached.
    """
    root = write_bundle(
        tmp_path,
        {
            "enums/leaf.json": {
                "title": "Leaf Kind",
                "type": "string",
                "enum": ["a", "b"],
                "description": "The declarer's own text.",
            },
            "core/middle.json": {
                "title": "Middle",
                "type": "object",
                "properties": {
                    "kind": {
                        "$ref": f"{BASE}enums/leaf.json",
                        "description": "The middle node's sibling, which wins.",
                    }
                },
            },
            "core/head.json": {
                "title": "Head",
                "type": "object",
                "properties": {"kind": {"$ref": f"{BASE}core/middle.json#/properties/kind"}},
            },
        },
    )
    out = emit.emit(root, ["core/head.json"])
    assert out.refusals == {}, out.refusals
    text = out.files["core/head.py"]
    tree = ast.parse(text)
    # FROM THE DECLARER: the import names the enums module, never ``core/middle``.
    frm = {
        ("." * n.level + (n.module or ""), a.name)
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    assert ("..enums.leaf", "LeafKind") in frm, frm
    assert not any("middle" in module for module, _ in frm), frm

    # The description the RECORD states at the referring pointer is the middle node's
    # sibling, and that is the one the field carries.
    record = bundle.record(root, "core/head.json", set(bundle.portable(root)))
    assert (
        record["properties"]["kind"]["description"] == "The middle node's sibling, which wins."
    ), record["properties"]["kind"]
    assert "The middle node's sibling, which wins." in text, text


def test_a_fragment_whose_target_document_is_refused_names_the_targets_own_keyword(
    tmp_path: Path,
) -> None:
    """The chain, which is what the four gate refusals in the real bundle become.

    Before this step the referrer refused on "names no document of this bundle",
    which was FALSE -- the document exists, and all four of its targets are refused
    on a keyword of their own (``pattern``, ``allOf``, ``definitions``, and a chain).
    A refusal that names the wrong cause sends the next reader to the wrong file.
    """
    # The refusing keyword is ``allOf``, which is one of the four real causes above.
    # It was ``const`` until D2's ``const`` row landed (salesagent-j3k2l.16) and the
    # fixture stopped refusing -- a fixture built on a keyword the emitter is about to
    # lower grades the chain only until that happens, and then grades nothing.
    target = {
        "title": "Refuses",
        "type": "object",
        "properties": {"a": {"allOf": [{"type": "string"}]}},
    }
    referrer = {
        "title": "Chains",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/refuses.json#/properties/a"}},
    }
    root = write_bundle(tmp_path, {"core/refuses.json": target, "core/chains.json": referrer})
    r = refusal_for(root, "core/chains.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    # The FRAGMENT is named, not only the document: the chain fires before the node is
    # looked up, and a message naming only the file does not say which of its nodes
    # was wanted.
    assert "core/refuses.json#/properties/a is refused" in r["detail"], r
    assert "allOf" in r["detail"], r

    # A reference with NO fragment names the document alone, unchanged -- which is
    # every one of the bundle's 214 existing chain refusals.
    plain = {
        "title": "Chains Plainly",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/refuses.json"}},
    }
    root = write_bundle(tmp_path / "b", {"core/refuses.json": target, "core/plain.json": plain})
    assert "core/refuses.json is refused" in refusal_for(root, "core/plain.json")["detail"]


def test_a_local_pointer_naming_no_node_of_this_document_is_refused_with_it_named(
    tmp_path: Path,
) -> None:
    """A local reference resolves against the REFERRER, so a pointer naming nothing in
    the referrer names nothing at all.

    This is :func:`compiler.local_reference`'s own "no such node", and it is the local
    twin of ``test_a_fragment_naming_a_node_the_walk_never_reaches_is_refused_with_it_named``
    above.  It must not fall back to the root: binding a pointer to the document's own
    root class would hand the property a model for the WHOLE document where the
    document names one node of it -- wider than its schema, and silent.

    The document carries NO section at all, which is the whole of the fixture: the
    pointer is spelled as if one existed, so the only thing this document cannot lower
    is the reference.
    """
    doc = {
        "title": "Points At Itself",
        "type": "object",
        "properties": {"x": {"$ref": "#/definitions/inner"}},
    }
    root = write_bundle(tmp_path, {"core/selfref.json": doc})
    r = refusal_for(root, "core/selfref.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    assert "#/definitions/inner" in r["detail"], r
    assert "names no node of this document" in r["detail"], r

    # And a section that exists without the entry reads the same way: the section is
    # not what is missing, the NODE is.
    doc = {**doc, "definitions": {"other": {"type": "string"}}}
    root = write_bundle(tmp_path / "b", {"core/selfref.json": doc})
    assert "names no node of this document" in refusal_for(root, "core/selfref.json")["detail"]


def test_two_symbols_at_one_pointer_is_refused_rather_than_ordered() -> None:
    """A pointer names ONE node, so two symbols at one pointer would make a fragment
    reference import whichever the walk declared last.

    The population is 0, so this grades the guard on a ``Module`` directly -- the
    symmetric case to the duplicate-NAME refusal beside it.

    **It has been 1, and the measurement is why the guard stays**
    (``adcp-client-python-857``): ``brand.json`` at ``/definitions/colors`` declared an
    ``AliasDecl`` and then a ``ClassDecl`` at one pointer, because §4 parses a class's
    extras store at the CLASS's own pointer and the store was reaching the walk's
    per-node entry -- which names
    the node at a pointer the bundle's ``$ref``\\ s name.  ``compiler.declare_object``
    sends the store to THE DISPATCH now, so the only node that does not own the pointer
    it carries makes no statement about it, and the test below reads 0 again.

    **The two halves are checked in two places now, because §14 step 7 split them.**
    ``Module.declare`` keeps the POINTER check, which is a fact about the walk; the
    duplicate-SYMBOL check is ``lower/names.py``'s, because the walk computes no symbol
    and "two nodes in this document derive the class name X" is a statement about §4's
    rules.  Both are VERDICTS and both name the pointer that collided.
    """
    from codegen import ir
    from codegen.compiler import Module
    from codegen.lower import names

    mod = Module(document="x.json")
    one = ir.AliasDecl("/properties/a", ir.TypeRef("int"))
    assert mod.declare("/properties/a", one) is None
    first = refusal_from(
        mod.declare("/properties/a", ir.AliasDecl("/properties/a", ir.TypeRef("str")))
    )
    assert first.keyword == "$ref"
    assert first.pointer == "/properties/a"
    assert "AliasDecl" in first.detail

    # The SYMBOL half: two pointers whose hops derive one name.
    other = Module(document="x.json")
    assert other.declare("/properties/a", ir.AliasDecl("/properties/a", ir.TypeRef("int"))) is None
    assert other.declare("/properties/b", ir.AliasDecl("/properties/b", ir.TypeRef("str"))) is None
    other.hops[""] = names.Root("X")
    other.hops["/properties/a"] = names.Property("", "same")
    other.hops["/properties/b"] = names.Property("", "same")
    second = refusal_from(names.assign(other))
    assert second.keyword == "title"
    assert second.pointer == "/properties/b"
    assert "derive the class name 'XSame'" in second.detail, second.detail


def test_no_document_of_the_bundle_declares_two_symbols_at_one_pointer() -> None:
    """And the guard above is not firing in the real bundle: every pointer the whole
    population declares at carries exactly one symbol, which is what makes
    ``Module.declared`` a map a reference can read."""
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    double = {
        d: r
        for d, r in out.refusals.items()
        if "two nodes are declared at this pointer" in r["detail"]
    }
    assert double == {}, double


def test_the_committed_tree_is_the_fresh_emission_of_the_derived_population() -> None:
    """The byte compare, scoped to this change: the one module a named node lands in
    is the one the emitter writes, and nothing else in the tree moved.

    ``test_emit`` owns the whole-tree compare and the metric constants; this asserts
    the file THIS step touches, so a regression here names this step.
    """
    document = "core/version-envelope.json"
    rel = f"{emit.module_file(document, fresh.PACKAGES)}.py"
    assert compiled(BUNDLE, [document]).files[rel] == (TREE / rel).read_text()


def test_the_emitted_module_imports_and_the_aliased_fields_still_decide() -> None:
    """The aliases are real Python and the module still imports and still VALIDATES.

    No AST assertion above catches either: an annotation can be syntactically valid
    and fail at import, and a field whose type moved to an alias can import and then
    accept what the document refuses.  So both bounds are exercised in both
    directions, through ``strict_validate`` (the schema half, D4) and through the
    constructor (the annotation).  The package is installed, so this imports it by
    name rather than putting ``src`` on the path.
    """
    mod = importlib.import_module("adcp.types._schemas.core.version_envelope")
    cls = mod.AdCPVersionEnvelope
    assert cls.strict_validate({"adcp_version": "3.1", "adcp_major_version": 3})

    # Each refusal names the FIELD whose constraint moved onto the alias, so none of
    # these can pass on an incidental error.  Both halves fire and each uses its own
    # vocabulary -- ``jsonschema``'s "does not match" and pydantic's "should match".
    for refuse, key in (
        (lambda: cls.strict_validate({"adcp_version": "3"}), "adcp_version"),
        (lambda: cls(adcp_version="3"), "adcp_version"),
        (lambda: cls.strict_validate({"adcp_major_version": 100}), "adcp_major_version"),
        (lambda: cls(adcp_major_version=100), "adcp_major_version"),
    ):
        with pytest.raises(ValidationError) as err:
            refuse()
        assert key in str(err.value), (key, str(err.value)[:200])


# --------------------------------------------------------------------------- #
# the LOCAL half (`salesagent-j3k2l.20`): a pointer into the document being written
# --------------------------------------------------------------------------- #
#: A document whose root references its own ``definitions`` entries, in the three
#: shapes the bundle's 157 local-section entries take: an object (which D2 makes a
#: class), a constrained scalar (an annotation, so it needs a name of its own), and one
#: nothing references at all.
#:
#: The constrained scalar is the same ``{string, minLength: 2, maxLength: 9}`` shape
#: :data:`TARGET` uses for the absolute half, deliberately: the two halves then grade
#: one node shape, so a divergence between them is a divergence in the mechanism rather
#: than in the fixture.
SECTIONS = {
    "title": "Catalog",
    "type": "object",
    "properties": {
        "slot": {"$ref": "#/definitions/slot"},
        "code": {"$ref": "#/definitions/code"},
        # A SECOND reference to one entry: the memo answers it, so no second symbol
        # appears for one node.
        "also_code": {"$ref": "#/definitions/code"},
        "plain": {"type": "string"},
    },
    "required": ["slot"],
    "definitions": {
        "slot": {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
        "code": {"type": "string", "minLength": 2, "maxLength": 9},
        "unused": {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]},
    },
}


def binds(stmt: ast.stmt) -> list[str]:
    """The module-level names one top-level statement binds, with no deduplication.

    ``declared_in`` is a mapping and so cannot report that a module bound one name
    TWICE, which is the fact "one symbol for one node" is about.  Only the statement's
    own targets, never a walk into it: a class body's annotated fields are ``Store``
    names too, and counting those would make a field sharing an entry's key look like a
    second binding of it.
    """
    if isinstance(stmt, ast.ClassDef):
        return [stmt.name]
    if isinstance(stmt, ast.AnnAssign):
        return [stmt.target.id] if isinstance(stmt.target, ast.Name) else []
    if isinstance(stmt, ast.Assign):
        return [t.id for t in stmt.targets if isinstance(t, ast.Name)]
    return []


def declared_in(source: str) -> dict[str, ast.AST]:
    """Every module-level name a rendered module BINDS, in body order.

    A class, an ``Annotated`` alias and an annotated assignment alike, because D2 makes
    a referenced node any of the three and the claims below are about the SYMBOL rather
    than about which shape it took.
    """
    out: dict[str, ast.AST] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = node.value if node.value is not None else node
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            out[node.targets[0].id] = node.value
    return out


def fields_of(source: str, name: str) -> dict[str, ast.AST]:
    """``field -> annotation`` for the class ``name`` of a rendered module."""
    cls = next(
        c for c in ast.parse(source).body if isinstance(c, ast.ClassDef) and c.name == name
    )
    return {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }


def schema_ref_of(source: str, name: str) -> str:
    """The ``__adcp_schema__`` expression in the class ``name``'s own body."""
    cls = next(
        c for c in ast.parse(source).body if isinstance(c, ast.ClassDef) and c.name == name
    )
    return next(
        ast.unparse(t.value)
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and getattr(t.target, "id", None) == "__adcp_schema__"
    )


def test_a_local_reference_is_a_symbol_this_module_declares_and_not_an_import(
    tmp_path: Path,
) -> None:
    """The exit condition for the local half, and every claim here is load-bearing.

    A local reference resolves against the REFERRER, so there is no module to import
    from: the symbol is one THIS module declares, the property NAMES it, and no import
    is written for it.  Each half passes while another fails -- a symbol nothing names
    is dead code, a property restating the entry's bound spells the fact twice, and an
    import of a local symbol is an ``ImportError`` no AST assertion sees.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    assert out.refusals == {}, out.refusals
    # The closure is this document ALONE: a local reference names no other document.
    assert sorted(out.emitted) == ["core/catalog.json"], out.emitted

    source = out.files["core/catalog.py"]
    declared = declared_in(source)
    # §4's nested rule, in the spelling that section now states: ``<Key>`` for a
    # ``definitions`` entry, because "the module path already carries the document".
    # These read ``CatalogSlot`` / ``CatalogCode`` until 2026-11-03: the ``<Root>``
    # prefix the names section dropped on 2026-10-28, the same stale spelling
    # ``adcp-client-python-10l.50`` removed from the absolute half one file over.
    assert "Slot" in declared, sorted(declared)
    assert "Code" in declared, sorted(declared)
    assert isinstance(declared["Slot"], ast.ClassDef), "an object entry is a class"

    imported = {
        a.name
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    assert not {"Slot", "Code"} & imported, sorted(imported)

    fields = fields_of(source, "Catalog")
    for key, symbol in (
        ("slot", "Slot"),
        ("code", "Code"),
        ("also_code", "Code"),
    ):
        got = fields[key]
        assert symbol in {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}, key
        # Nothing but a name and an annotation rides on the property: the entry's own
        # bound has nowhere else in the module to hide.
        extra = kwargs_of(got) - {"description", "alias", "default", "json_schema_extra"}
        assert extra == set(), (key, sorted(extra))
    # One symbol for one node, though two properties name it.  Read off the module's own
    # top-level BINDINGS rather than off the text: ``declared_in`` is a dict and cannot
    # report a second binding of one name, and ``source.count("Code = ")`` grades a
    # spelling now that the name is unprefixed and a substring of other identifiers.
    bound = [name for stmt in ast.parse(source).body for name in binds(stmt)]
    assert bound.count("Code") == 1, bound
    # The bound IS reachable from the alias -- here through the type D5 names it once
    # as, read off THIS run's alias module rather than the committed one.
    named = constraint_aliases(out.beside["constraints.py"])
    assert {"min_length", "max_length"} <= stated_by(declared["Code"], named), named

    # Each entry's symbol is bound BEFORE the root class that uses it, which is what
    # declaring on demand buys: the module is valid Python read top to bottom.
    names = list(declared)
    assert names.index("Slot") < names.index("Catalog"), names
    assert names.index("Code") < names.index("Catalog"), names


def test_a_local_entry_that_is_a_class_names_its_own_pointer_and_not_the_roots(
    tmp_path: Path,
) -> None:
    """Section 2's rule, at a pointer no pair had ever named before this step.

    A declared node carries ``__adcp_schema__`` naming ITS OWN node -- this document,
    and the pointer of the entry -- never the root's ``#``.  There is no binding table
    and no adapter, so the class finds its schema through its own attribute and a
    grader cannot be aimed at the wrong node.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    entry = schema_ref_of(out.files["core/catalog.py"], "Slot")
    assert "core/catalog.json" in entry, entry
    assert "#/definitions/slot" in entry, entry
    # And the root's is the ROOT's, so the two are not one string.
    root_ref = schema_ref_of(out.files["core/catalog.py"], "Catalog")
    assert "#/definitions" not in root_ref, root_ref
    assert root_ref != entry

    # The pointer LANDS in the document the run writes beside the module, which is what
    # ``strict_validate`` reads: a ref naming a node the package cannot resolve would
    # be a class that raises on every validation instead of grading.
    #
    # **Read the way :func:`adcp.types._base.schema_at` reads it, which is
    # ``store_expanded(applied_schema(root, pointer), root)``, and not off the record's
    # raw text.**  The record states each distinct subtree ONCE and references it at
    # every occurrence (``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS
    # POINTERS ARE NOT"), so ``{"type": "string"}`` -- stated twice in this fixture, at
    # ``/definitions/slot/properties/a`` and at ``/properties/plain`` -- is hoisted and
    # the raw text holds ``{"$ref": "#/definitions/Shared0"}`` at both.  A text read
    # here asserted the absence of a storage the architecture section requires, and the
    # section makes the hoisting INVISIBLE to every pointer a reader spells: so the
    # claim is about what the accessor hands a grader, and that is where it is asked.
    written = json.loads(out.files["core/catalog.json"])
    assert node_at(written, "/definitions/slot") is not NOTHING
    through = _base.store_expanded(applied_schema(written, "#/definitions/slot"), written)
    assert through["properties"] == {"a": {"type": "string"}}
    # And the storage is what stands between the two readings, so the raw text at that
    # pointer is NOT the expansion -- which is what keeps the line above a dereference
    # rather than a longer spelling of ``node_at``.
    assert node_at(written, "/definitions/slot") != through


def test_an_entry_nothing_references_is_not_declared(tmp_path: Path) -> None:
    """**`salesagent-j3k2l.20`'s deliberate decision, asserted in both directions.**

    ``definitions`` and ``$defs`` assert nothing about an instance, so an entry no
    reference reaches cannot change what the document accepts or refuses -- and
    declaring it would emit a class no field names, nothing imports and ``__all__``
    does not export.  Its only reachable effect is the wrong one: a keyword inside a
    DEAD section would refuse the whole document.

    Measured on the bundle: 11 of the 157 entries in the 40 documents this step
    unblocks are referenced by nothing, and all 11 sit in ``a2ui/si-catalog.json``,
    whose 24 ``$ref``\\ s are all inside that dead section -- so declaring them would
    also pull that target's whole closure into a module no instance reaches.  Those
    same 24 are why that document is refused once D2's ``const`` row lets the walk
    reach it: ``bundle.record`` does not descend a section, so the document the
    package would carry is not locally decidable (``codegen.emit``).

    The second direction is what makes the first non-vacuous: the same keyword in a
    REFERENCED entry still refuses, so the pass below is the skip and not a hole in the
    keyword screen.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    # ``Unused`` and not ``CatalogUnused``: §4's names section dropped the ``<Root>``
    # prefix, so the prefixed spelling was a name the emitter could not produce under
    # any outcome and this assertion held whatever the walk did with a dead entry.
    assert "Unused" not in declared_in(out.files["core/catalog.py"])
    assert "Unused" not in out.files["core/catalog.py"]

    dead = {
        **SECTIONS,
        "definitions": {
            **SECTIONS["definitions"],
            # A shape the emitter refuses SOMEWHERE inside, which is all this fixture
            # needs: the dead half asserts no refusal, the live half asserts one, and
            # the contrast is the measurement.
            #
            # **The keyword is deliberately no longer pinned, because pinning it has
            # broken this fixture twice.**  It was ``const`` until D2's ``const`` row
            # landed (salesagent-j3k2l.16); it became ``allOf`` on the ground that
            # ``allOf`` was "a keyword no row lowers at a property", and
            # salesagent-j3k2l.18 then lowered exactly that.  The shape still refuses
            # -- one level deeper, at the conjunct's own ``type`` -- so the fixture is
            # still live, but a fixture that names the keyword a row is about to claim
            # grades the skip only until that row lands.  No keyword is immune to the
            # next row, so the assertions below grade the thing this test is named for:
            # whether the entry was WALKED, read off the refusal's pointer.
            "unused": {
                "type": "object",
                "properties": {"b": {"allOf": [{"type": "string"}]}},
                "required": ["b"],
            },
        },
    }
    root = write_bundle(tmp_path / "b", {"core/catalog.json": dead})
    assert emit.emit(root, ["core/catalog.json"]).refusals == {}

    live = {
        **SECTIONS,
        "definitions": {
            **SECTIONS["definitions"],
            "slot": {
                "type": "object",
                "properties": {"a": {"allOf": [{"type": "string"}]}},
                "required": ["a"],
            },
        },
    }
    root = write_bundle(tmp_path / "c", {"core/catalog.json": live})
    r = refusal_for(root, "core/catalog.json")
    # The SAME shape, in a referenced entry, refuses -- and the refusal is INSIDE the
    # entry, which is what says the walk reached it.  Whichever keyword the emitter
    # stops on, and however deep inside the property it stops, the pointer still names
    # the entry; that is the fact the dead half's silence is contrasted against.
    assert r["keyword"], r
    assert r["pointer"].startswith("/definitions/slot/properties/a"), r


def test_a_local_reference_to_an_entry_declared_later_costs_nothing(tmp_path: Path) -> None:
    """Declared ON DEMAND, so a FORWARD reference needs no topological order.

    20 of the bundle's local references name an entry their own document lists after
    the one referring to it, across 4 documents (``brand.json`` 7,
    ``core/placement-presentation.json`` 5, ``core/registry-event.json`` 4,
    ``core/bidding-policy-capability.json`` 4).  An eager pass over the section in
    document order would need a sort over the reference graph to put each symbol in the
    module before its user; asking for the symbol is what orders them instead.
    """
    doc = {
        "title": "Chain",
        "type": "object",
        "properties": {"a": {"$ref": "#/definitions/first"}},
        "required": ["a"],
        "definitions": {
            # ``first`` is listed FIRST and references ``second``.
            "first": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/second"}},
                "required": ["x"],
            },
            "second": {
                "type": "object",
                "properties": {"y": {"type": "string"}},
                "required": ["y"],
            },
        },
    }
    root = write_bundle(tmp_path, {"core/chain.json": doc})
    out = emit.emit(root, ["core/chain.json"])
    assert out.refusals == {}, out.refusals
    names = list(declared_in(out.files["core/chain.py"]))
    # ``First`` / ``Second`` and not ``ChainFirst`` / ``ChainSecond``: §4's names
    # section spells a ``definitions`` entry ``<Key>``, the module path carrying the
    # document.  What this test is about is the ORDER, which the rename does not touch.
    assert {"First", "Second", "Chain"} <= set(names), names
    assert names.index("Second") < names.index("First") < names.index("Chain"), names


def test_a_local_reference_cycle_refuses_rather_than_recurring(tmp_path: Path) -> None:
    """Two entries naming each other is a recursive type, and nothing here spells one.

    0 documents of the bundle are in that position, which is why this refuses rather
    than growing a forward-declaration scheme -- the same answer, and the same
    in-flight shape, ``emit.emit`` already gives a cross-DOCUMENT reference cycle.
    Probed by making it fail: with ``Module.resolving`` removed, both halves below
    recurse to Python's own limit, which is a ``RecursionError`` at the gate rather
    than a document refused by name.
    """
    doc = {
        "title": "Loop",
        "type": "object",
        "properties": {"a": {"$ref": "#/definitions/one"}},
        "required": ["a"],
        "definitions": {
            "one": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/two"}},
                "required": ["x"],
            },
            "two": {
                "type": "object",
                "properties": {"y": {"$ref": "#/definitions/one"}},
                "required": ["y"],
            },
        },
    }
    root = write_bundle(tmp_path, {"core/loop.json": doc})
    r = refusal_for(root, "core/loop.json")
    assert r["keyword"] == "$ref", r
    # The whole chain is named, so the reader does not have to find the loop again.
    assert "local reference cycle" in r["detail"], r
    assert "#/definitions/one" in r["detail"] and "#/definitions/two" in r["detail"], r

    # A SELF reference is the one-hop case and reads the same way.
    doc = {
        **doc,
        "definitions": {
            "one": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/one"}},
                "required": ["x"],
            }
        },
    }
    root = write_bundle(tmp_path / "b", {"core/loop.json": doc})
    assert "local reference cycle" in refusal_for(root, "core/loop.json")["detail"]


#: A local pointer reached through an ``allOf`` CONJUNCT, which is
#: ``adcp-client-python-10l.43``'s shape: the conjunct arm of ``compiler.lower_composition``
#: is the one caller that meets a reference without going through
#: ``nodes.Reference.head``, so it asked the binder for a pointer that is not a binding at
#: all.  Both halves of the live population are here -- a conjunct that restates a property
#: (``core/account-identity-change-preview.json``) and one that states only ``required``
#: (``core/registry-event.json``) -- because the second reaches ``compiler._reused``, whose
#: import screen is about crossing a module boundary and this does not cross one.
CONJUNCT_LOCAL = {
    "title": "Preview",
    "type": "object",
    "properties": {
        # The restating half: the conjunct declares a property the BASE declares, so
        # section 2's restatement rule reads the local base's Shape.
        "narrowed": {
            "allOf": [
                {"$ref": "#/definitions/impact"},
                {"properties": {"effect": {"enum": ["kept", "redone"]}}},
            ]
        },
        # The ANNOTATION-ONLY half: the conjunct restates a key the base declares with
        # nothing but a ``description``, so the subclass re-uses the base's DECIDED field
        # (``compiler._reused``) -- whose type names a POINTER this module declares
        # (``#/definitions/area``) and imports from nowhere.  Probed by making it fail:
        # with the screen asked of ``source is None`` alone, this refuses with "symbols no
        # document this run lowered declares" of a symbol in its own module.
        "stricter": {
            "allOf": [
                {"$ref": "#/definitions/impact"},
                {
                    "type": "object",
                    "required": ["reason"],
                    "properties": {"area": {"description": "Which area."}},
                },
            ]
        },
    },
    "required": ["narrowed", "stricter"],
    "definitions": {
        "impact": {
            "type": "object",
            "properties": {
                "area": {"$ref": "#/definitions/area"},
                "effect": {"type": "string", "enum": ["kept", "redone", "blocked"]},
                "reason": {"type": "string", "minLength": 1},
            },
            "required": ["effect"],
            "additionalProperties": False,
        },
        "area": {"type": "string", "enum": ["account_id", "billing"]},
    },
}


def test_a_local_pointer_as_an_allOf_conjunct_resolves_through_the_local_resolver(
    tmp_path: Path,
) -> None:
    """``adcp-client-python-10l.43``: the conjunct arm asks the RESOLVER, not the binder.

    A local pointer as an ``allOf`` conjunct is an ordinary draft-07 document, and the walk
    already has the one resolver for it -- ``compiler.local_reference``, which
    ``lower.references.lower`` reaches by branching on the document half.
    ``compiler.lower_composition``'s conjunct arm asked ``Module.target`` for every
    reference instead, so a local one got ``emit.answer``'s loud "this is not a binding at
    all" as the DOCUMENT's verdict -- charging two documents for a routing gap in the
    compiler.

    Four facts, and each fails on its own:

    * the document EMITS, which is the routing;
    * the composed class's BASE is a class this module DECLARES, so the base came from the
      local resolver and not from a binder;
    * no import is written for it, which is what a binding would have produced -- a local
      :class:`compiler.Target` carries an EMPTY module, so recording one would name ``""``
      as the module to import from;
    * the re-used field's type names the entry's OWN pointer-derived symbol, which is
      ``compiler._reused``'s "the base is in this module" arm reached through a
      :class:`compiler.Target` rather than through its absence.
    """
    root = write_bundle(tmp_path, {"core/preview.json": CONJUNCT_LOCAL})
    out = emit.emit(root, ["core/preview.json"])
    assert out.refusals == {}, out.refusals
    # The closure is this document ALONE: a local pointer names no other document.
    assert sorted(out.emitted) == ["core/preview.json"], out.emitted

    source = out.files["core/preview.py"]
    declared = declared_in(source)
    # §4's nested rule: the entry is a class of this module, named for its own key --
    # ``Impact``, not ``PreviewImpact``, the ``<Root>`` prefix having been dropped on
    # 2026-10-28 because the module path already carries the document.
    assert isinstance(declared.get("Impact"), ast.ClassDef), sorted(declared)
    # The two composing nodes are classes of this module whose base is that entry's
    # class -- which is what says the conjunct became a BASE through the local resolver.
    # Named and not counted: a count says nothing about WHICH node composed, and a
    # fixture that stopped composing one of the two would hold the count by accident.
    composed = [
        c
        for c in ast.parse(source).body
        if isinstance(c, ast.ClassDef) and [b.id for b in c.bases] == ["Impact"]
    ]
    assert {c.name for c in composed} == {"Narrowed", "Stricter"}, [c.name for c in composed]

    imported = {
        a.name
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    assert "Impact" not in imported, sorted(imported)
    # No import is written from an EMPTY module, which is what a local Target's
    # ``module`` is and what ``Target.where`` would have handed ``Module.importing``.
    assert "from  import" not in source, source

    # The annotation-only restatement re-uses the base's decided field, whose type names
    # the entry this module declares for ``#/definitions/area`` -- so ``_reused``'s "the
    # base is in this module" arm was reached through a :class:`compiler.Target` rather
    # than through its absence, and the document's own description rides on it.
    reusing = next(c for c in composed if "area" in fields_of(source, c.name))
    area = fields_of(source, reusing.name)["area"]
    assert "Area" in {n.id for n in ast.walk(area) if isinstance(n, ast.Name)}, (
        ast.unparse(area)
    )
    assert "Which area." in ast.unparse(area), ast.unparse(area)
    assert "Area" not in imported, sorted(imported)


def test_the_bundles_two_conjunct_local_pointers_emit_and_their_chains_clear() -> None:
    """The LIVE half of ``adcp-client-python-10l.43``, over the whole portable set.

    ``core/account-identity-change-preview.json`` at
    ``/definitions/nonblocking_impacts/items/allOf/0`` (``#/definitions/impact``) and
    ``core/registry-event.json`` at ``/oneOf/0/properties/payload/allOf/0``
    (``#/$defs/propertyPayload``) were the two sites in the bundle where a local pointer is
    reached through a conjunct, both reported as VERDICTS, and each blocked one more
    document through the chain.  All four emit.

    Asserted as EMISSION and not as the absence of a sentence: a chained refusal quotes its
    target's detail, so a grep over the text counts one obstruction once per quoting
    document, which is the mistake ``refusal.Kind``'s docstring records four of.
    """
    portable = claimed("bundle.portable", bundle.portable(BUNDLE))
    out = compiled(BUNDLE, sorted(portable))
    freed = claimed(
        "documents the conjunct-local routing gap held",
        [
            "core/account-identity-change-preview.json",
            "core/registry-event.json",
            # The two the group blocked transitively.
            "account/sync-accounts-response.json",
            "core/registry-feed-response.json",
        ],
        inside=portable,
    )
    assert freed <= set(out.emitted), sorted(freed - set(out.emitted))
    # And no document is left reporting that sentence at all, in either direction: it is
    # the run's answer at a site only ``lower.union._targeted`` now reaches, and that
    # caller reads it as "this branch names no class" rather than refusing on it.
    said = {
        d: r["pointer"]
        for d, r in out.refusals.items()
        if "is a pointer into this document" in r["detail"]
    }
    assert said == {}, said


def test_two_entry_keys_deriving_one_name_fail_the_build(tmp_path: Path) -> None:
    """``class_name`` strips punctuation, so ``a_b`` and ``a.b`` derive one symbol.

    This is why ``compiler.local_reference`` writes no identifier check of its own: an
    identifier root concatenated with ``class_name``'s alphanumerics is always an
    identifier, and what CAN go wrong is a collision, which ``Module.declare`` already
    fails the build for by naming the symbol.  Probed by making it fail, because a rule
    nothing can break is a finding about the rule.
    """
    doc = {
        "title": "Collide",
        "type": "object",
        "properties": {
            "p": {"$ref": "#/definitions/a_b"},
            "q": {"$ref": "#/definitions/a.b"},
        },
        "required": ["p", "q"],
        "definitions": {
            "a_b": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            "a.b": {"type": "object", "properties": {"y": {"type": "string"}}, "required": ["y"]},
        },
    }
    root = write_bundle(tmp_path, {"core/collide.json": doc})
    r = refusal_for(root, "core/collide.json")
    assert r["keyword"] == "title", r
    assert "CollideAB" in r["detail"], r


def test_no_document_of_the_bundle_refuses_on_a_definition_section_any_more() -> None:
    """`salesagent-j3k2l.20`'s exit condition, over the whole population.

    ``definitions`` and ``$defs`` were 40 of the 653 refusals -- 35 and 5, every one at
    the root, every one answering "a later D2 row does" with no such row scheduled
    anywhere.  Each of the 40 now either emits or refuses on a keyword D2 NAMES and a
    scheduled step owns, which is what a refusal is allowed to say.

    The POPULATION is derived here rather than listed, because a keyword census alone
    cannot tell a document that moved from one the selectors stopped claiming.
    """
    portable = claimed("bundle.portable", bundle.portable(BUNDLE))
    out = compiled(BUNDLE, sorted(portable))
    partitions(portable, emitted=set(out.emitted), refused=set(out.refusals))
    on_sections = {
        d: r for d, r in out.refusals.items() if r["keyword"] in ("definitions", "$defs")
    }
    assert on_sections == {}, on_sections

    roots = [
        d
        for d in bundle.portable(BUNDLE)
        if any(isinstance(bundle.read(BUNDLE, d).get(k), dict) for k in bundle.DEFINITIONS)
    ]
    claimed("documents carrying a definitions section", roots, inside=portable)
    for document in roots:
        r = out.refusals.get(document)
        if r is None:
            continue
        assert r["keyword"] not in ("definitions", "$defs"), (document, r)
        assert r["keyword"] and r["pointer"] and r["detail"], (document, r)


def test_the_bundles_own_sections_are_walked_and_the_closure_follows() -> None:
    """The POSITIVE path on the real bundle, which the committed tree cannot grade.

    15 of the 45 documents emit at 0130e5fc9 -- it was 6 at 16052ffb0 and 0 of 40
    when this was written -- and the other 30 are each held by a keyword another
    step owns (``$ref`` 9, ``oneOf`` 5, ``allOf`` 4, ``anyOf`` 4,
    ``discriminator`` 3, ``properties`` 3, ``uniqueItems`` 2).  The constructed
    bundles above are what grade the declaration itself.  What the real bundle
    grades is the WALK, in the two places it is observable:

    * a refusal at a pointer INSIDE a section is proof the walk descended one.  9
      documents are in that position, and none was before: every pointer under
      ``definitions`` used to be unreachable.
    * a refusal that moved from the root to a property means the walk got FURTHER, and
      the closure then reaches what those earlier properties name.
      ``governance/policy-entry.json`` is the case: it refused at ``/`` on ``$defs``
      before any of its 8 property references was read, and now refuses at
      ``/properties/acceptance_profile`` -- so the three enum documents its earlier
      properties name are emitted over step 1, 2 and 4's population, and no member of
      that population references two of the three from anywhere else.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    inside = {
        d: r["pointer"]
        for d, r in out.refusals.items()
        if r["pointer"].lstrip("/").split("/")[0] in bundle.DEFINITIONS
    }
    # 8 -> 9 at ``salesagent-j3k2l.40``, and the ninth is the walk getting FURTHER
    # rather than a new kind of refusal: ``brand.json`` refused at ``/oneOf/4`` on the
    # branch that composes, and now that a composing branch is lowered it refuses at
    # ``/definitions/default_language/allOf/0`` -- a verdict, on a base that is an
    # alias, three hops inside a section.  No member left; the other 8 are unchanged.
    #
    # 9 -> 7 at ``salesagent-j3k2l.28``, and BOTH halves of the move are the walk
    # finishing rather than stopping earlier.  Two documents LEFT because they emit:
    # ``core/bidding-policy-capability.json`` (refused at
    # ``/definitions/policy_profile/properties/supported_combinations/items/oneOf/0``)
    # and ``core/targeting-overlay-support.json`` (at
    # ``/definitions/countrySupport/anyOf/0``) -- both on the local-``$ref`` branch
    # guard that row removed.  And ``governance/reported-outcome-error.json``'s
    # pointer went DEEPER, ``/definitions/bounded_value/anyOf/0`` ->
    # ``/definitions/bounded_value_level_3/anyOf/1``, for the same reason: the first
    # branch lowers now and the walk reaches the third level.  No member joined.
    #
    # 7 -> 8 at ``salesagent-j3k2l.21``, and the eighth is the walk getting FURTHER
    # for the third time in this test's history rather than a document becoming
    # unrepresentable.  ``core/geo-place-requirement.json`` joined, and the cause is
    # MEASURED on trunk rather than inferred from the count: at 8c021bffa it refused
    # at ``/properties/systems/propertyNames`` on ``$ref``, kind ``deferred``,
    # CHAINED to ``core/geo-place-system.json``'s own refusal -- "a branch of type
    # 'string' is step 6", which is this row's ground.  That target is a root
    # ``anyOf`` of scalars and now lowers, so the chain clears and the walk descends
    # into the section, where it meets ``pattern`` on
    # ``/definitions/catalogRequirement/properties/countries/propertyNames``.
    #
    # That surviving refusal was not that row's: its detail was
    # ``salesagent-j3k2l.64``'s ground verbatim -- a constrained-str key pydantic
    # renders back as ``patternProperties``, which that row had no reading for -- and
    # section 5's ``propertyNames`` row decides that position: ``pattern`` -> an
    # annotated ``str`` key.
    #
    # **``.64`` emitted that key and the document stayed, which is the walk getting
    # FURTHER a fourth time rather than the count holding still.**  It was predicted
    # here that .64 would take the count 8 -> 7; it did not, and the measurement is
    # why: with the key lowered, the walk descends ONE MORE HOP into the same
    # property and meets ``uniqueItems`` on the array inside the mapping's VALUE --
    # ``/definitions/catalogRequirement/properties/countries/additionalProperties``,
    # a verdict on an array with no class above it (``lower.containers``'s
    # ``_DISTINCT_HAS_NOWHERE_TO_LIVE``).  So the member is unchanged, the count is
    # unchanged, and the POINTER is what moved -- which is exactly why this test pins
    # pointers and not a total.
    #
    # NAMED, NOT COUNTED: the count went 7 -> 8 -> 9 -> 8 over four rows, each move a
    # document joining or leaving for a cause measured at the time, and a number going
    # back down says nothing about which document moved.  The two pointers asserted
    # below are what make this evidence of a DESCENT into the section rather than of
    # the section being read, and they are what a count could never say.
    #
    # **8 -> 7 AT ``adcp-client-python-10l.21``'s SECOND INSTALMENT, and the pointer
    # this test pinned is the one that LEFT.**  §5(b)'s ``uniqueItems`` row is a declared
    # WIDENING now rather than a verdict, so ``core/geo-place-requirement.json`` emits
    # and leaves this population -- which is the fourth time the pointer it carried
    # moved and the first time it cleared.  ``governance/policy-entry.json`` emits for
    # the same reason and its own pin below went with it.
    #
    # The replacement pin is ``core/creative-localization-readback.json``, which is
    # deeper than either and reads INSIDE a section through three further hops -- a
    # section entry, a ``patternProperties`` expression, a combinator branch -- so it
    # still says what this test exists to say: the walk DESCENDS into a section rather
    # than reading the section's name.  ``brand.json`` joined at ``/definitions/colors``
    # and that is ``adcp-client-python-857``, a latent collision the overlap used to
    # stand in front of.
    #
    # **AND THAT REPLACEMENT PIN CLEARED AT ``adcp-client-python-10l.55``, THE FIFTH
    # TIME THIS POINTER HAS MOVED AND THE SECOND TIME BY EMITTING.**
    # ``core/creative-localization-readback.json`` refused at that pointer because the
    # branch there is a ``$ref`` onto ``core/localized-creative-asset.json``, chained to
    # ``core/assets/asset-union.json``, whose own ``$ref`` branch onto the UNION root
    # ``VASTAsset`` the branch row refused for not being a class.  It is one, the gate
    # reads ``compiler.TargetKind`` now, and the whole chain emits.
    #
    # The pin moves to ``brand/verify-brand-claim-response.json``, which is the same
    # depth claim through the same number of hops -- a section entry, an ``allOf``
    # conjunct, a property -- so what this assertion says is unchanged: the walk
    # DESCENDS into a section rather than reading the section's name.
    claimed("documents refusing inside a definitions section", inside)
    assert inside["brand/verify-brand-claim-response.json"] == (
        "/definitions/signed_response/allOf/1/properties/payload"
    )
    # Pinned by name because a count alone cannot say the pointer went INTO a
    # section.  This was ``core/response-payload-jws-envelope.json`` at
    # ``/definitions/response_payload/properties/typ``; that document EMITS as of
    # 16052ffb0, so it left this population and the pin moved to the deepest
    # section pointer the bundle still refuses at -- three hops past the section
    # name, which is what makes it evidence of a descent rather than of the
    # section being read.  It held across 0130e5fc9, where the membership of the
    # other seven changed and the count went 7 -> 8, and across
    # ``salesagent-j3k2l.40``, where ``brand.json`` joined and took it 8 -> 9.
    #
    # **AND IT CLEARED AT ``adcp-client-python-10l.43``, THE THIRD TIME THIS SECOND PIN
    # HAS MOVED AND THE SECOND TIME BY EMITTING.**
    # ``core/account-identity-change-preview.json`` refused at
    # ``/definitions/nonblocking_impacts/items/allOf/0`` because the conjunct there is a
    # LOCAL ``$ref`` -- ``#/definitions/impact``, a pointer into its own document -- and
    # ``lower_composition``'s conjunct arm asked the binder for it.  It asks
    # ``compiler.local_reference`` now (``compiler._conjunct_base``) and the document
    # emits, which is the same clearing as the first pin's: a routing gap charged to a
    # document, not a fact about the document.
    #
    # The pin moves to ``brand/verify-brand-claims-response.json``, the SIBLING of the
    # first pin at the same pointer -- a section entry, an ``allOf`` conjunct, a property,
    # three hops past the section name -- so what this assertion says is unchanged, and
    # the two pins are now two independently-named documents rather than two depths.
    # There are 3 members left and ``brand.json``'s pointer is two hops, so these two are
    # the whole of the deep evidence.
    assert inside["brand/verify-brand-claims-response.json"] == (
        "/definitions/signed_response/allOf/1/properties/payload"
    )

    # ``governance/policy-entry.json`` EMITS at ``adcp-client-python-10l.21``'s second
    # instalment -- its ``/properties/acceptance_profile`` chained to
    # ``media-buy/acceptance-policy-profile.json``, whose ``region_aliases`` mapping
    # value carries the ``uniqueItems`` §5(b) now declares -- so what this half asserts
    # is the half that was always the point: the three enum documents its own
    # references name are reached over the population below.  A document that emits
    # reaches MORE of them, not fewer.
    assert "governance/policy-entry.json" in out.emitted, out.refusals.get(
        "governance/policy-entry.json"
    )
    read = lambda d: bundle.read(BUNDLE, d)  # noqa: E731
    pop = sorted(
        {
            d
            for d in bundle.portable(BUNDLE)
            if bundle.is_leaf_object(read(d))
            or bundle.references_a_property(read(d))
            or populations.composes_at_the_root(read(d))
        }
    )
    reached = set(compiled(BUNDLE, pop).emitted)
    known = set(bundle.portable(BUNDLE))
    for document in (
        "enums/governance-domain.json",
        "enums/policy-category.json",
        "enums/policy-enforcement.json",
    ):
        assert document in reached, document
        # And the reference that reaches it is one of policy-entry's own.
        assert document in {
            bundle.document_for(bundle.split_ref(u)[0], known)
            for _, u, _ in bundle.references(read("governance/policy-entry.json"))
            if bundle.split_ref(u)[0]
        }, document


# --------------------------------------------------------------------------- #
# what the carried document owes a reference under a section
# (`salesagent-j3k2l.71`)
# --------------------------------------------------------------------------- #
#: A dead section holding a REMOTE reference, which is ``a2ui/si-catalog.json``'s shape
#: reduced to one entry: the root asserts something of its own, the section asserts
#: nothing, and the only reference in the document sits inside the dead entry.  The
#: second fixture below is this one with a ``$ref`` naming the entry, so the pair
#: differs in the one dimension the rule reads and in nothing else.
DEAD_SECTION_REMOTE = {
    "title": "Dead Section Catalog",
    "type": "object",
    "properties": {"label": {"type": "string"}},
    "definitions": {
        "Widget": {
            "type": "object",
            "properties": {"body": {"$ref": f"{BASE}core/target.json"}},
            "required": ["body"],
        }
    },
}


def _remote_under_a_section() -> dict[str, list[tuple[str, str]]]:
    """``document -> [(pointer, uri)]`` for every REMOTE reference the bundle spells
    inside a ``definitions`` / ``$defs`` entry.

    Read off the raw documents and off the one schema-position walk, so this is the
    whole set the rule below splits rather than a set some run happened to reach.
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        entries = bundle.section_entries(doc)
        for pointer, uri, _ in bundle.references(doc):
            if bundle.split_ref(uri)[0] and bundle.pointers_above(pointer, entries):
                out.setdefault(document, []).append((pointer, uri))
    return out


def test_a_remote_reference_under_a_section_is_owed_where_its_entry_is_declared() -> None:
    """Section 5's on-demand rule, read on the SCHEMA half.

    ``strict_validate`` decides against the document the emitter writes beside the
    module, so what the carried document owes a reference is whatever the package's own
    validation can reach.  Section 5 makes a section "nothing by itself", each entry
    "declared on demand when a ``$ref`` names it"; section 3 adds "an entry nothing
    references is not declared".  So the obligation follows DECLARATION: an entry some
    ``$ref`` names has a class at its pointer and a reference under it is reached, and
    an entry nothing names has none and is reached by nothing.

    Both halves are named here and asserted non-empty, because a rule whose admitted
    half is empty admits nothing and a rule whose counted half is empty refuses
    nothing -- and either way it reads as working.
    """
    sites = _remote_under_a_section()
    every = claimed(
        "remote references the bundle spells inside a section entry",
        {(d, p) for d, ps in sites.items() for p, _ in ps},
    )
    named = bundle.named_nodes(BUNDLE)

    counted, admitted = set(), set()
    for document, refs in sites.items():
        # The RAW document and not ``bundle.record``: the predicate is a function of
        # (document, named) and the references are at their own pointers either way, so
        # resolving 1,054 documents to ask a positional question would cost the whole
        # bundle's resolution for an answer that does not depend on it.
        owed = set(
            bundle.undecidable_references(
                bundle.read(BUNDLE, document), named.get(document, frozenset())
            )
        )
        for pointer, uri in refs:
            (counted if (pointer, uri) in owed else admitted).add((document, pointer))

    partitions(every, owed_resolution=counted, reached_by_nothing=admitted)
    claimed("remote references under a DECLARED entry", counted, inside=every)
    claimed("remote references under an entry nothing declares", admitted, inside=every)

    # And the split is the DECLARATION and not the document, pointer depth or spelling:
    # every admitted reference sits in an entry no ``$ref`` of the bundle names, and
    # every counted one in an entry some ``$ref`` does.
    for document, pointer in sorted(admitted):
        doc = bundle.read(BUNDLE, document)
        entries = bundle.pointers_above(pointer, bundle.section_entries(doc))
        assert entries, (document, pointer)
        assert not bundle.pointers_above(pointer, named.get(document, frozenset())), (
            document,
            pointer,
            sorted(named.get(document, frozenset())),
        )
    for document, pointer in sorted(counted):
        assert bundle.pointers_above(pointer, named.get(document, frozenset())), (
            document,
            pointer,
        )


def test_a_remote_reference_in_a_dead_section_leaves_the_document_decidable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The POSITIVE half on a bundle this file writes, and the measurement is a
    validation with the network removed.

    **ROW .3 MOVED THIS FROM "decidable with the reference left in" to "no reference
    left".**  The delegated resolver descended its own ``SCHEMA_KEYS`` and
    ``SCHEMA_OBJECT_KEYS``, and ``definitions``/``$defs`` were in neither, so a
    reference under a section survived it and the question was whether the document
    could still be decided with one in it.  ``bundle.record`` descends by the table's
    descent column, where a section entry is a subschema at a DEF position, so "every
    cross-document ``$ref``" (architecture §4) means every one -- including a dead
    section's.  The claim this test exists for is unchanged and now holds a fortiori:
    the document the package carries DECIDES, with the network removed, and
    ``jsonschema`` accepts and refuses instances through it while ``socket.socket`` is
    a constructor that raises.
    """
    root = write_bundle(
        tmp_path, {"a2ui/catalog.json": DEAD_SECTION_REMOTE, "core/target.json": TARGET}
    )
    out = emit.emit(root, ["a2ui/catalog.json"])
    assert "a2ui/catalog.json" in out.emitted, out.refusals

    # The entry is dead, so no class is declared at its pointer -- which is what makes
    # the position unreachable, and it is asserted rather than assumed.
    source = out.files["a2ui/catalog.py"]
    assert "Widget" not in declared_in(source), sorted(declared_in(source))

    carried = json.loads(out.files["a2ui/catalog.json"])
    # The record holds NO cross-document reference, at any position, which is what the
    # inliner's own contract says and is asserted here rather than at the dead entry.
    assert [p for p, u, _ in bundle.references(carried) if bundle.split_ref(u)[0]] == [], carried
    left = claimed(
        "pointers of the dead section's entries in the carried document",
        list(bundle.section_entries(carried)),
    )
    entries = bundle.section_entries(carried)
    assert all(bundle.pointers_above(p, entries) for p in left), (
        sorted(left),
        sorted(entries),
    )

    # THE NETWORK IS REMOVED, not mocked out at the resolver: anything that tried to
    # fetch the target would have to open a socket, and this one raises on
    # construction.  So the two validations below are the measurement of "decidable
    # locally" rather than a restatement of the predicate under test.
    class Refuses(socket.socket):
        def __init__(self, *a: object, **k: object) -> None:
            raise AssertionError("the validator opened a socket")

    monkeypatch.setattr(socket, "socket", Refuses)
    jsonschema.validate({"label": "x"}, carried)
    with pytest.raises(jsonschema.ValidationError) as err:
        jsonschema.validate({"label": 1}, carried)
    assert err.value.validator == "type", err.value.validator


def test_a_remote_reference_in_a_declared_entry_is_inlined_and_no_longer_refused(
    tmp_path: Path,
) -> None:
    """The other half of the same fixture, and **row .3 is what changed its answer.**

    A ``$ref`` names the entry, so section 5 declares it, a class grades at
    ``#/definitions/Widget`` and ``_refuse_at`` evolves a validator onto that pointer --
    which descends the entry's ``properties`` and meets the reference.  Under the
    delegated resolver that reference SURVIVED resolution, because
    ``resolve_all_refs`` descends neither ``definitions`` nor ``$defs``, so the document
    the package carried was one it could not decide with and the run refused it
    UNRESOLVED.  ``bundle.record`` descends a section entry like any other subschema
    position (architecture §4, §11), so the reference is inlined, the carried document
    decides locally, and the document emits.

    **This is an EMISSION delta of row .3 and not a check relaxed to fit**: nothing
    here is narrower, the record is wider.  The check that refused it is still in
    ``emit`` and still ranges over the same predicate -- it simply has no survivor to
    find, and firing again would mean the inliner left a reference at a position the
    package's own validation decides through.  On the real bundle the one document it
    refused was ``core/requirements/catalog-field-binding.json``, at
    ``/definitions/ScalarBinding/properties/ext``.
    """
    live = {
        **DEAD_SECTION_REMOTE,
        "properties": {
            **DEAD_SECTION_REMOTE["properties"],
            "widget": {"$ref": "#/definitions/Widget"},
        },
    }
    root = write_bundle(tmp_path, {"a2ui/catalog.json": live, "core/target.json": TARGET})
    out = emit.emit(root, ["a2ui/catalog.json"])
    assert "a2ui/catalog.json" in out.emitted, out.refusals
    carried = json.loads(out.files["a2ui/catalog.json"])
    # The entry a ``$ref`` NAMES, with the cross-document reference under it inlined --
    # the one thing the old answer turned on.
    assert "/definitions/Widget" in bundle.section_entries(carried), carried
    assert [p for p, u, _ in bundle.references(carried) if bundle.split_ref(u)[0]] == [], carried
    assert bundle.undecidable_references(carried, bundle.named_nodes(root).get(
        "a2ui/catalog.json", frozenset()
    )) == []


def test_a_property_named_definitions_is_a_property_and_not_a_section(tmp_path: Path) -> None:
    """``section_entries`` reads the WALK, so a segment is a section only where the
    keyword is.

    A property may legitimately be named ``definitions`` -- ``harness.formats_used``
    carries the same caution for ``default``, where a bundle met 95 of them -- and the
    pointer ``/properties/definitions/properties/body`` is then a property's property,
    which no reading of the pointer's TEXT can tell from a section entry.  The 3.2
    bundle holds 0 such properties, so this is graded on a bundle this file writes.

    What the two readings differ on is observable here and nowhere else: a reference at
    that position is REACHED by the resolver -- ``properties`` is one of the keys it
    descends, twice over -- so it is inlined and the document emits with no reference
    left to classify.  A text reading would call the position a section entry, and the
    only place that answer could still be read is a RAW document, which is what this
    file's own census and ``test_emit``'s naming of the admitted entries read.
    """
    doc = {
        "title": "Names A Property Definitions",
        "type": "object",
        "properties": {
            "definitions": {
                "type": "object",
                "properties": {"body": {"$ref": f"{BASE}core/target.json"}},
            }
        },
    }
    assert bundle.section_entries(doc) == frozenset(), bundle.section_entries(doc)
    claimed(
        "references the document spells",
        [p for p, _, _ in bundle.references(doc)],
    )

    root = write_bundle(tmp_path, {"a2ui/odd.json": doc, "core/target.json": TARGET})
    out = emit.emit(root, ["a2ui/odd.json"])
    assert "a2ui/odd.json" in out.emitted, out.refusals
    # The carried document READ THROUGH ITS OWN STORAGE: the record stores each distinct
    # subtree once and references it at every occurrence
    # (``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT"),
    # and this document's inlined target repeats ``{"type": "string"}``.  The claim here
    # is that the CROSS-DOCUMENT reference at a property named ``definitions`` was
    # reached and inlined, so the text that claim is about is the inlined one.
    stored_text = json.loads(out.files["a2ui/odd.json"])
    carried = bundle.expanded(stored_text, stored_text)
    assert bundle.references(carried) == [], bundle.references(carried)
    body = carried["properties"]["definitions"]["properties"]["body"]
    assert "$ref" not in body, body
    assert set(body["properties"]) == set(TARGET["properties"]), body


# --------------------------------------------------------------------------- #
# §5(a)'s bare-`$ref` ROOT: a subclass where the target is a class
# --------------------------------------------------------------------------- #
#: Every portable document whose ROOT is a bare ``$ref`` -- the whole population of
#: §5(a)'s bare-``$ref`` root row, read off the document rather than off a refusal, so
#: it stays the population once the row stops refusing.  ``1`` at §14 step 9.
BARE_REF_ROOTS = 1

#: A document whose ROOT is a bare ``$ref`` and a title, which is the live site's own
#: shape (``core/signal-pricing-option.json`` states ``title``, ``description`` and the
#: reference).  The title is not optional: §4 names a root off it and a document stating
#: none refuses on ``title`` before this row is reached.
BARE_REF_ROOT = {
    "title": "Alias Like",
    "description": "A deprecated alias of the target.",
    "$ref": f"{BASE}core/target.json",
}


def bare_ref_roots() -> list[str]:
    """The portable documents whose root states a ``$ref`` and nothing constraining.

    ``compiler.declaring`` at ROOT is the one reading of "which keys does this node
    state about an instance", so the population is the screen's own answer and not a
    second list of annotation keys.
    """
    return sorted(
        document
        for document in bundle.portable(BUNDLE)
        if set(compiler.declaring(bundle.read(BUNDLE, document), Position.ROOT)) == {"$ref"}
    )


def written(at: Path, out: object) -> Any:
    """Write an emitted run as a package under ``at``, import it, and return the module
    namespace -- ``tests/test_ref_branch_union.py``'s own helper, for its reason: a
    subclass across a module boundary is exactly the shape that can render and not
    import, and that is not visible in a string."""
    package = at / "pkg"
    emit.write(out, package, None)
    sys.path.insert(0, str(at))
    try:
        for name in [n for n in sys.modules if n == "pkg" or n.startswith("pkg.")]:
            del sys.modules[name]
        return (
            importlib.import_module("pkg.core.alias"),
            importlib.import_module("pkg.core.target"),
        )
    finally:
        sys.path.remove(str(at))


def test_a_bare_ref_root_is_a_subclass_of_its_target(tmp_path: Path) -> None:
    """§5(a): "Where the target is a class the answer is a **subclass** of it."

    "Refused because binding this module's symbol to another module's class would be a
    second way to reach one class, against §1.  Where the target is a class the answer
    is a subclass of it, which is one class per name and accepts exactly what the base
    accepts, so §1 is untouched."

    Graded on a constructed bundle because the one live site's TARGET refuses on a
    keyword of its own -- see the live half below -- so the bundle reaches the emitting
    path zero times.  Three facts, and each one fails on its own:

    * the root symbol is a class this module DECLARES, whose base is the imported
      symbol: ``X is Y`` does NOT hold, which is the §1 objection the refusal stood on;
    * it declares no field: the target supplies every one of them by inheritance and
      nothing of the target is copied (P2);
    * it accepts exactly what the target accepts, through its own
      ``strict_validate`` -- which is what makes the subclass faithful rather than a
      second name for a looser class.
    """
    root = write_bundle(
        tmp_path,
        {"core/target.json": TARGET, "core/alias.json": BARE_REF_ROOT},
    )
    out = emit.emit(root, ["core/alias.json"])
    assert out.refusals == {}, out.refusals
    assert sorted(out.emitted) == ["core/alias.json", "core/target.json"], out.emitted

    tree = ast.parse(out.files["core/alias.py"])
    imported = {
        a.name
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    assert "CatalogLike" in imported, imported
    declared = [c for c in tree.body if isinstance(c, ast.ClassDef)]
    assert [c.name for c in declared] == ["AliasLike"], [c.name for c in declared]
    assert [b.id for b in declared[0].bases] == ["CatalogLike"], ast.dump(declared[0])
    # No field of its own, and the ``__adcp_schema__`` of its OWN document: the class
    # grades against the document of record, where §3 inlines the target unchanged, so
    # there is a pointer for every inherited fact.
    assert [
        t.target.id for t in declared[0].body if isinstance(t, ast.AnnAssign)
    ] == ["__adcp_schema__"], ast.dump(declared[0])
    assert "core/alias.json" in out.files["core/alias.py"]


#: The target for the RUN, as opposed to the one for the text: its facts are a
#: ``required`` and a closed object, so the written package imports nothing from
#: ``constraints.py`` -- D5's alias module is a whole-run artifact and a part-run does
#: not write it, so a constrained scalar in a fixture target makes the import fail on
#: a name the installed module does not carry.
RUN_TARGET = {
    "title": "Target Like",
    "type": "object",
    "properties": {"label": {"type": "string"}, "n": {"type": "integer"}},
    "required": ["label"],
    "additionalProperties": False,
}


def test_a_bare_ref_root_accepts_exactly_what_its_target_accepts(tmp_path: Path) -> None:
    """The subclass's accepted set, RUN rather than read: §1 is untouched because the
    two classes accept the same payloads and are still two classes.

    Written as a package and imported, for ``test_ref_branch_union``'s reason: a
    subclass across a module boundary is exactly the shape that can render and not
    import, and that is not visible in a string.
    """
    root = write_bundle(
        tmp_path,
        {
            "core/target.json": RUN_TARGET,
            "core/alias.json": {**BARE_REF_ROOT, "$ref": f"{BASE}core/target.json"},
        },
    )
    out = emit.emit(root, ["core/alias.json"])
    assert out.refusals == {}, out.refusals
    alias, target_module = written(tmp_path, out)
    subclass, target = alias.AliasLike, target_module.TargetLike
    # One class per name, and it is NOT the target: that is the §1 objection the
    # refusal stood on, and a subclass answers it.
    assert issubclass(subclass, target) and subclass is not target
    assert subclass.model_validate({"label": "x", "n": 1}).label == "x"
    # Every fact the target states is enforced through the subclass, and nothing of the
    # target is copied: the ``required`` and the closed object are the TARGET's.
    for payload in ({"n": 1}, {"label": "x", "beyond": 1}):
        with pytest.raises(ValidationError):
            subclass.model_validate(payload)
    # ``model_validate`` and not ``strict_validate``: the schema half reads the
    # PACKAGED document off the installed ``adcp.types._schemas`` resource, and a
    # fixture bundle has no installed package -- which is why every constructed-bundle
    # test here grades the annotation half (``test_ref_branch_union`` does the same).
    # The schema half is graded over the real bundle by the three checks.


def test_a_bare_ref_root_whose_target_is_no_class_is_bound_by_identity(
    tmp_path: Path,
) -> None:
    """§5(a)'s OTHER half, WRITTEN: "bound to the target **by identity**".

    "Where the target is an alias, an enumeration or a root model there is nothing to
    subclass and the symbol is bound to the target by identity, which §1's own carve-out
    already admits inside a module and now admits across one: ``X is Y`` holds and the
    domain surface exports it once."

    The TYPE is the imported symbol and the root wrapper is what binds it, which is the
    whole of the arm: ``emit.lower`` turns a root that declared no class into
    ``ir.AliasDecl`` beside ``__adcp_schema__`` and ``strict_validate``, the same two
    statements a scalar root and an enumeration root bind.  So three facts are asserted
    and each fails on its own -- the module imports the target's symbol, the root alias
    names it and copies none of its facts, and the binding names THIS document.

    The node's own ``description`` rides on the alias and the target's does not: §5's
    ``$ref`` row gives an annotation sibling the other answer -- "the sibling's
    description wins" -- so a document that says why it is deprecated says it here.
    """
    root = write_bundle(
        tmp_path,
        {
            "core/scalar.json": {
                "title": "Scalar",
                "type": "string",
                "description": "The target's own text, which the sibling beats.",
            },
            "core/alias.json": {**BARE_REF_ROOT, "$ref": f"{BASE}core/scalar.json"},
        },
    )
    out = emit.emit(root, ["core/alias.json"])
    assert out.refusals == {}, out.refusals
    assert sorted(out.emitted) == ["core/alias.json", "core/scalar.json"], out.emitted

    tree = ast.parse(out.files["core/alias.py"])
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "Scalar" in imported, imported
    # No class at all: a target that is not a class has nothing to subclass, which is
    # the sentence this arm implements.
    assert [c.name for c in tree.body if isinstance(c, ast.ClassDef)] == [], out.files[
        "core/alias.py"
    ]
    (bound,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "AliasLike"
    ]
    names = {n.id for n in ast.walk(bound.value) if isinstance(n, ast.Name)}
    assert "Scalar" in names, ast.unparse(bound)
    # Nothing of the target is copied (P2): the alias states the type and the node's own
    # description, and no constraint of the target's.
    assert kwargs_of(bound.value) <= {"description"}, ast.unparse(bound)
    assert BARE_REF_ROOT["description"] in ast.unparse(bound), ast.unparse(bound)
    assert "core/alias.json" in out.files["core/alias.py"]


def test_the_one_bare_ref_root_in_the_bundle_is_an_identity_binding_onto_a_union_root(
    tmp_path: Path,
) -> None:
    """The LIVE half, and it is the IDENTITY arm rather than the subclass one.

    ``core/signal-pricing-option.json`` is a deprecated alias of
    ``core/vendor-pricing-option.json`` and the only bare-``$ref`` root in the portable
    set.  Its target EMITS -- §5's ``$ref`` distribution clause landed -- and the root it
    declares is a UNION: ``core/vendor-pricing-option.json`` composes an inline object
    with ``core/signal-pricing.json``, whose root is a ``oneOf``, so the target is a
    :attr:`compiler.TargetKind.UNION` and not the flat class the subclass arm wants.

    **A subclass of it would accept none of the branches, and that is measured in
    ``BranchDispatchMixin`` rather than reasoned**: "the base is the class that DECLARES
    ``_branch_models`` (``"_branch_models" not in cls.__dict__``); a class that inherits
    it gets its own shape back".  So §5's ``$ref`` row at CONJ is the clause that decides
    this one -- "a scalar, an enum, a container, or a union root ... is not a class a
    model can extend: the target is this node's own TYPE" -- and a bare ``$ref`` root is
    a composing node with one ``$ref`` conjunct and no properties of its own.

    Asserted as the READING and not as a census: the document emits, its module binds the
    root to the target's own symbol, and ``target_kind`` answers ``UNION`` for that
    target.  The number of bare-``$ref`` roots is the one pin, and it is derived.
    """
    assert len(bare_ref_roots()) == BARE_REF_ROOTS, bare_ref_roots()
    assert bare_ref_roots() == ["core/signal-pricing-option.json"], bare_ref_roots()
    out = compiled(BUNDLE, bare_ref_roots())
    assert "core/signal-pricing-option.json" not in out.refusals, out.refusals
    assert out.emitted["core/signal-pricing-option.json"].endswith(
        "core.signal_pricing_option"
    ), out.emitted

    files = emit.emit(BUNDLE, bare_ref_roots()).files
    # The TARGET's root is a union, which is what puts this site in the identity arm:
    # ``BranchDispatchMixin`` is the base ``render`` writes for a root whose instance is
    # one of its branches, and ``_branch_models`` is the tuple it dispatches over.
    target = ast.parse(files["core/vendor_pricing_option.py"])
    (declared,) = [
        c
        for c in target.body
        if isinstance(c, ast.ClassDef) and c.name == "VendorPricingOption"
    ]
    assert "BranchDispatchMixin" in {
        b.id for b in declared.bases if isinstance(b, ast.Name)
    }, ast.dump(declared)

    # And the referrer declares no class: the root symbol IS the target's, bound beside
    # this document's own ``__adcp_schema__``.
    tree = ast.parse(files["core/signal_pricing_option.py"])
    assert [c.name for c in tree.body if isinstance(c, ast.ClassDef)] == [], files[
        "core/signal_pricing_option.py"
    ]
    (bound,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "SignalPricingOption"
    ]
    assert "VendorPricingOption" in {
        n.id for n in ast.walk(bound.value) if isinstance(n, ast.Name)
    }, ast.unparse(bound)
    assert "core/signal-pricing-option.json" in files["core/signal_pricing_option.py"]

