"""A node's schema is the node AS THE DOCUMENT APPLIES IT, not the node read alone.

`salesagent-j3k2l.24`.  A separate module from ``tests/test_emit.py`` because this
grades one mechanism in both halves -- what the emitter will lower, and what the
runtime says a class's schema IS -- and because ``test_emit`` holds the metric
constants that are re-measured once per epic.

**The defect.**  draft-07 applies a root's assertions and its combinator branch's to
the SAME instance, so ``{"type": "object", "oneOf": [{"properties": {...}}]}`` admits
only objects and the branch at ``/oneOf/0`` does not restate it.  Read in ISOLATION
that branch admits a string, so ``lower.objects.lower_object`` refused to build a class
for it -- 10 documents of the 3.2 bundle, with 34 more chaining off them through a
``$ref`` -- and ``_base.schema_at`` returned that same isolated node as the schema a
branch class would then be graded against.  Fixing only the first turned one defect
into two reds: ``core/activation-key.json``'s two branch pairs reported
``accepts:model_refused_valid`` -- the draw produced an object and the class refused
it, because the schema the pair was graded against still said a string would do.  So the rule
is spelled ONCE, in ``_base.applied_schema``, and the emitter derives its answer from
the function the runtime resolves ``__adcp_schema__`` through.

**The distinction this file exists to keep.**  A hop that preserves the INSTANCE
LOCATION carries the enclosing assertion; a hop that moves to a different instance
does not.  Both populations are counted below, and the DIFFERENCE is asserted as a
schema fact -- ``jsonschema`` accepting a string against the bare node and refusing it
against the applied one -- rather than as a property of this project's spelling of the
rule.

**The negative half is graded on constructed documents, and that is a measurement
rather than a convenience.**  After the fix NO document in the bundle reaches
``lower_object``'s type refusal at all: every node the emitter gets to that states no
``type`` is one its own document constrains.  Grading "still refused" against the real
bundle would be a pass over an empty loop, which is what
``tests/test_fragment_ref.py`` says in as many words about its own import half.
"""

from __future__ import annotations

import contextlib
import functools
import importlib
import json
import sys
from pathlib import Path

import fresh
import jsonschema
import pytest
from compiled import compiled
from conftest import refusal_from
from pydantic import ValidationError

from adcp.types import _base
from adcp.types._base import AdCPBaseModel, SchemaRef, applied_schema, schema_at
from codegen import bundle, emit, keywords
from codegen import refusal as refusal_module
from tests.nodeset import claimed, partitions, ratchet

#: A FLOOR over the WHOLE portable set, which is not the count the committed tree holds
#: (that is the ``population()`` run, and the two have been confused in three
#: briefings).  Direction: an emitting row only adds documents.  The history, each move
#: a row doing its work: 674, 686 (bcb0b8ca8), 691 (.40), 705 (.28), 716 (.21),
#: 719 (.64, a mapping's key is a type), 731 (.41, a fact at a position with no field
#: to carry it: a dropped default on a required property, a format inside a container
#: or on a union branch, and an array's or a mapping's own bound on one), 732 (.71, a
#: remote reference inside a section entry nothing declares: a position the package's
#: own validation never reaches, so the carried document decides without it),
#: 747 (.43 and .67 merged together).
#:
#: **Three rows moved this in flight and the merged tree is MEASURED, not chosen.** On
#: their own branches .71 reached 732, .67 733 and .43 745, and the merge of all three
#: emits 747, because each row emits documents the others do not: .67 adds
#: ``media-buy/outcome-target.json`` (a ``discriminator`` beside a nested union is
#: admitted, so the union lowers), .71 adds ``a2ui/si-catalog.json``, and .43 adds
#: thirteen the conjunct reader was refusing. Taking any side would have understated the
#: floor, and the cautious-looking minimum of the three would have loosened it by
#: fourteen. A ratchet merge is a measurement.
EMITTED_FLOOR = 747

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

DRAFT = "http://json-schema.org/draft-07/schema#"

#: The documents the fix moved from refused to emitted, re-measured at 16052ffb0.
#: It began as three -- two refused at a branch their own root constrains to an
#: object, and ``core/deployment.json`` chaining off the first through a ``$ref`` --
#: and the later rows named under ``STILL_REFUSED`` have grown it to ten, then to
#: ELEVEN, which is all of them.
NOW_EMITTED = (
    # The eleventh, at ``adcp-client-python-10l.21``'s third instalment: it left
    # ``STILL_REFUSED`` below when the ``type`` word beside a nested union stopped
    # refusing its chain target.
    "error-details/governance-agent-not-accepted.json",
    "core/account-ref.json",
    "core/activation-key.json",
    "core/canonical-account-ref.json",
    "core/canonical-reporting-commitment.json",
    "core/committed-metric.json",
    "core/deployment.json",
    "core/missing-metric.json",
    "core/performance-feedback-metric.json",
    "core/reporting-write-destination.json",
    "media-buy/acceptance-policy-requirement.json",
)

#: The residue, with the keyword and pointer it reports NOW.  Each entry is a later
#: D2/D6 row -- a ``$ref`` whose target refuses, a ``maxLength`` beside a
#: ``format: uri``, a ``uniqueItems`` -- so this is the residue of OTHER steps, and
#: pinning it here means a step that closes one of them shows up as this going stale
#: rather than as a silent change of population.  It held 8, then 5, and holds 1 at
#: 16052ffb0: the four ``$ref`` rows left because each one's target emits now.
#:
#: **EMPTY at ``adcp-client-python-10l.21``'s third instalment, and the last entry left
#: by the row it was waiting on.**  It held
#: ``error-details/governance-agent-not-accepted.json``, chained through
#: ``/oneOf/0/properties/accepted_governance_agents`` to
#: ``governance/accepted-governance-agents.json``, whose own obstruction was a sibling of
#: a NESTED union.  That sibling is the ``type`` word, §5(a)'s first bullet and §14 step
#: 9's first faithful row -- the parser hands it to every branch already -- so the target
#: emits and this document emits behind it.  The residue reaching zero is what the set
#: was pinned for, and the set STAYS, empty, because a document arriving here is the
#: honest direction and has to be visible.
STILL_REFUSED: dict[str, tuple[str, str]] = {}


def _node(doc: object, pointer: str) -> dict:
    """The node a JSON Pointer names, read without :func:`applied_schema`.

    A second walk ON PURPOSE: the claims below are about the difference between the
    bare node and the applied one, so one of the two sides has to be read by
    something other than the function under test.
    """
    node: object = doc
    for part in pointer.split("/"):
        if part == "":
            continue
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]  # type: ignore[index]
    assert isinstance(node, dict), pointer
    return node


def _refuses(document: str, node: dict, value: object) -> bool:
    """Does ``node``, read as a schema AGAINST ITS OWN DOCUMENT, refuse ``value``?

    The document-rooted validator, which is the one ``_refuse`` builds and the one
    :func:`test_reading_the_node_alone_cannot_resolve_it_and_refuses_everything`
    measures directly.  A node handed to a bare ``Draft7Validator`` cannot resolve a
    document-side local ``$ref`` and RAISES instead of answering, so the bare reading
    is an ERROR at such a node and not a verdict on the value.

    **Measured on this tree (2026-11-06, ``adcp-client-python-sjzy``): 21 of the 295
    pairs below sit at such a node** --
    ``core/format.json#/properties/assets/items/oneOf/0/oneOf/{0..20}``, each an
    ``allOf`` onto ``#/$defs/baseIndividualAsset`` -- and for all 21 BOTH readings
    (``_node``'s and :func:`applied_schema`'s) raise ``_WrappedReferencingError`` under
    a bare validator.  So a loop written on the bare validator does not merely miss
    them, it errors on them.

    **Resolving a reference against the document is NOT applying the document's
    assertions**, which is what keeps this file's contrast intact: the root's ``type``
    is still absent from ``node``, and the 110/185 split below is read through this
    function on both sides so the two readings are comparable.
    """
    root = _base._document(document)
    validator = jsonschema.validators.validator_for(root, jsonschema.Draft7Validator)
    return bool(list(validator(root).evolve(schema=node).iter_errors(value)))


@functools.cache
def census() -> tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]]:
    """Every node of the bundle that declares no ``type``, split by whether the
    document applies one to it anyway.

    Keyed by document, so each half carries two denominators -- nodes and documents --
    and so a reader can see WHICH documents are in each.
    """
    constrained: dict[str, frozenset[str]] = {}
    loose: dict[str, frozenset[str]] = {}
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        yes = bundle.constrained_to_object(doc)
        no = frozenset(p for p, n in bundle.nodes(doc) if "type" not in n) - yes
        if yes:
            constrained[document] = yes
        if no:
            loose[document] = no
    return constrained, loose


def _declares_properties(doc: dict, pointer: str) -> bool:
    node = _node(doc, pointer)
    return isinstance(node.get("properties"), dict) and bool(node["properties"])


def test_the_two_halves_partition_the_bundles_typeless_nodes() -> None:
    """The denominators, because the rule is a PARTITION of one set of nodes and a
    verdict over a set nobody named is a verdict over however many nodes there turned
    out to be.

    Each half is asserted NON-EMPTY, which is the fact the two numbers carried: the
    first half alone would hold for a rule that constrains everything and the second
    alone for a rule that constrains nothing.  They are not asserted as sizes -- the
    sizes are one bundle version's reading, and the halves are DISJOINT and TOTAL over
    the typeless nodes, which is the property that cannot be true of one version only.

    The second pair is the subset the DEFECT was found on -- a node declaring a
    non-empty ``properties``, which is the only node a class can be declared at, so it
    is the subset the emitter's answer turns on, and it too is named rather than sized.
    """
    constrained, loose = census()
    both = {(d, p) for d, ps in constrained.items() for p in ps}
    neither = {(d, p) for d, ps in loose.items() for p in ps}
    claimed("typeless nodes the document constrains to an object", both)
    claimed("typeless nodes the document leaves unconstrained", neither)
    partitions(both | neither, constrained=both, loose=neither)

    def with_properties(half: dict[str, frozenset[str]]) -> set[tuple[str, str]]:
        return {
            (document, p)
            for document, pointers in half.items()
            for p in pointers
            if _declares_properties(bundle.read(BUNDLE, document), p)
        }

    claimed("constrained nodes declaring properties", with_properties(constrained))
    claimed("loose nodes declaring properties", with_properties(loose))


def test_the_difference_between_the_two_halves_is_a_schema_fact() -> None:
    """``jsonschema`` decides, so this grades the DOCUMENTS and not this project's
    reading of them.  Exhaustive over both halves, in both directions:

    * at a node the document constrains, the applied node REFUSES a non-object.  That
      is what makes a class admissible there: the class refuses the string too, so it
      is not narrower than the schema it names.  Counted beside it, the bare nodes
      that ADMIT one -- the sites where the conjoined type is the only thing refusing
      it, which is what keeps this from passing over nodes that would refuse a string
      anyway.  326 of the 1,541 are in that second group, every one of them refusing a
      non-object for a reason of its own (a ``not`` over a ``required``, which a
      non-object satisfies vacuously, so the negation fails).
    * at a node the document does not constrain to an object, the applied node's
      ``type`` is never ``"object"``, so nothing in that half can become a class.
      7,987 of the 8,000 come back as the node ITSELF -- the same object -- and the
      other 13 carry a type the document really does apply: 5 ``string`` and 8
      ``array``, each from an enclosing node that declares one.  The rule is about
      which hop carries an assertion and not about objects, which is why those 13
      exist; what this half asserts is that none of them is an object.

    **The ``jsonschema`` half runs over the constrained nodes with no ``$ref`` in
    their own subtree, 1,541 of the 2,040, and that exclusion is named rather than
    silent.**  A raw bundle node carrying an absolute ``$ref`` sends ``jsonschema``
    to the network (``bundle.record``'s docstring measures it at 4.4 s per
    validation, on a path it deprecates), and resolving all 1,054 documents to avoid
    that costs more than the claim is worth -- the same reason ``bundle.record``
    exists for the emitted population only.  The structural half below covers all
    2,040.

    A string is the probe because the fact conjoined at every CONSTRAINED node is
    ``type: "object"``, which
    :func:`test_what_is_conjoined_at_a_constrained_node_is_its_object_type_and_its_root_s_own_statement`
    is
    what establishes.
    """
    constrained, loose = census()
    checked: set[tuple[str, str]] = set()
    skipped: set[tuple[str, str]] = set()
    admitted_bare: set[tuple[str, str]] = set()
    for document, pointers in constrained.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare = _node(doc, pointer)
            if "$ref" in bare or bundle.references(bare):
                skipped.add((document, pointer))
                continue
            applied = applied_schema(doc, pointer)
            assert not jsonschema.Draft7Validator(applied).is_valid("a string"), (
                document,
                pointer,
            )
            if jsonschema.Draft7Validator(bare).is_valid("a string"):
                admitted_bare.add((document, pointer))
            checked.add((document, pointer))
    # The three are non-empty sets and they PARTITION the constrained half: a node is
    # checked or skipped, the skipped ones are exactly the referencing ones, and the
    # ``admitted_bare`` subset is what says the applied schema is doing the refusing
    # rather than the bare node already refusing on its own.  As three counts they were
    # a reading of one bundle version and said nothing more.
    partitions({(d, p) for d, ps in constrained.items() for p in ps}, checked=checked, skipped=skipped)
    claimed("constrained nodes checked", checked)
    claimed("constrained nodes skipped for a reference", skipped)
    claimed("checked nodes whose BARE node admits a string", admitted_bare, inside=checked)

    untouched: set[tuple[str, str]] = set()
    conjoined: dict[str, set[tuple[str, str]]] = {}
    asserted: dict[str, set[tuple[str, str]]] = {}
    for document, pointers in loose.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare, applied = _node(doc, pointer), applied_schema(doc, pointer)
            assert applied.get("type") != "object", (document, pointer)
            if applied is bare:
                untouched.add((document, pointer))
                continue
            # **TWO things can be conjoined now and the loop counts each** (§13 item 3,
            # settled): the ``type`` word an enclosing node applies, and the SAME-INSTANCE
            # STATEMENT it makes -- its ``properties``, ``required``,
            # ``additionalProperties`` and its own ``allOf`` -- spliced into this node's
            # conjunct list.  A node that takes only the second has no ``type`` key at
            # all, which is what the single-keyed reading here raised ``KeyError`` on.
            if "type" in applied and "type" not in bare:
                conjoined.setdefault(repr(applied["type"]), set()).add((document, pointer))
            if applied.get("allOf") != bare.get("allOf"):
                spliced = applied["allOf"][: len(applied["allOf"]) - len(bare.get("allOf") or [])]
                for one in spliced:
                    for key in one:
                        asserted.setdefault(key, set()).add((document, pointer))
    # The loose half: almost every node is handed back UNTOUCHED, and the few that are
    # not take a type that is never ``object`` -- asserted just above, per node.  Which
    # TYPES get conjoined is the fact; how many nodes each one reaches is one bundle
    # version's count of it.
    claimed("loose nodes handed back untouched", untouched)
    assert set(conjoined) == {"'string'", "'array'"}, {k: len(v) for k, v in conjoined.items()}
    assert all(conjoined.values()), conjoined
    # And WHICH keywords reach a node as an enclosing node's statement, which is the
    # set §5's union row compiles onto a base: the three it states inline, plus whatever
    # the enclosing node's own conjuncts state, which is a conjunct's whole content and
    # so is not a fixed set.  The three are asserted as a SUBSET-of relation in the
    # direction that matters -- every one of them is reached, so no arm of
    # ``_base._conjunction`` is graded by a loop that met none of it.
    assert {"properties", "required", "additionalProperties"} <= set(asserted), sorted(asserted)
    # **``title`` and ``description`` were asserted ABSENT here, and §8's annotation
    # clause moved the line** (``adcp-client-python-10l.21``'s seventh instalment).  The
    # old reading was "§6 answers an annotation at the pointer that states it and the
    # splice drops them", and the splice still does -- which
    # :func:`test_what_is_conjoined_at_a_constrained_node_is_its_object_type_and_its_root_s_own_statement`
    # now grades exhaustively over ``_base._conjunction``, where the strip is.  What
    # arrives carrying one arrives by DESCENT: an enclosing statement follows the
    # pointer to the instance each hop moves to, so a node below a branch's own property
    # carries the root's declaration OF THAT PROPERTY, and that declaration's
    # description is the document's own at the instance this node describes.
    #
    # §8: "there is no pointer at which an annotation is graded."  So the claim is
    # asserted against the TABLE and not by absence, which is the stronger direction --
    # a strip is one site that can be forgotten, and ``bundle.is_an_annotation`` reads
    # the effect column itself, at every position:
    for keyword in ("title", "description"):
        for position in keywords.Position:
            assert bundle.is_an_annotation(keyword, position), (keyword, position)
    # Non-vacuous in the direction that matters: the descent really does carry one, so
    # the two lines above are not a property of a loop that met neither key.
    assert "description" in asserted, sorted(asserted)
    assert all(asserted.values()), asserted


def test_what_is_conjoined_at_a_constrained_node_is_its_object_type_and_its_root_s_own_statement() -> None:
    """``applied_schema`` adds the enclosing ``type`` word and the enclosing node's own
    SAME-INSTANCE STATEMENT, it adds nothing else, and it changes no fact the node
    already states but its conjunct list.

    The structural half of the check above, over all 2,040 rather than the 1,541 a
    ``jsonschema`` call can reach offline -- and the reason the probe there may be a
    string.  ``bundle.constrained_to_object`` asks for the literal ``"object"``, so an
    enclosing ``["object", "null"]`` is not one and lands in the loose half; if a
    document ever states a different enclosing type this reports it rather than
    letting the string probe go quietly vacuous.

    **This test said "``type: object`` is the ONLY fact conjoined" and §13 item 3
    retires that sentence**, which ``_base.applied_schema``'s own KNOWN CEILING
    forecast: "a row whose root asserts more than a type about the same instance needs
    this extended".  §14 step 9 is that row, and §8's pairing rule is what the
    extension is graded by -- "a branch class of a root union is paired with its branch
    node read UNDER THE ROOT'S SIBLINGS".  So what this grades is the SHAPE of the
    conjunction rather than its absence:

    * the keys ADDED are ``type`` (always ``'object'`` at a constrained node, which is
      what the string probe above depends on) and ``allOf``, the conjunct list;
    * every other fact the node states is returned UNCHANGED, which is the half that
      says the node's own statement always wins;
    * the conjunct list is the node's OWN conjuncts with the enclosing statements
      PREPENDED, so nothing of the node's is dropped or reordered;
    * **the SPLICE drops a ``title`` and a ``description``, graded where the splice is
      made rather than over its output** -- ``_base._conjunction``, exhaustively over
      every node of every portable document and every keyword it can be reached
      through.  §6 answers an annotation at the pointer that states it, and the
      enclosing node is that pointer.

    **The per-statement form of that last clause moved at
    ``adcp-client-python-10l.21``'s seventh instalment, and the reason is §8's
    annotation clause.**  It read "no spliced conjunct carries a ``title`` or a
    ``description``", asserted over every statement arriving at a node -- and an
    enclosing statement DESCENDS by key now instead of being dropped at the first hop
    that moves to another instance, so a node below a branch's own property carries the
    root's declaration of that property with the document's own description on it.  That
    is not a spliced conjunct and §6 does not answer it: it is the document's
    declaration at the instance this node describes.  §8 settles what it means -- "there
    is no pointer at which an annotation is graded" -- and the check above asserts it
    against the TABLE's effect column rather than against the splice.  So this clause
    keeps the claim it can keep, over the function that makes the splice, where it is
    exhaustive.
    """
    constrained, _ = census()
    added: dict[str, set[str]] = {}
    spliced_at: set[tuple[str, str]] = set()
    for document, pointers in constrained.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare, applied = _node(doc, pointer), applied_schema(doc, pointer)
            for key in set(applied) - set(bare):
                added.setdefault(key, set()).add(key if key == "allOf" else repr(applied[key]))
            own = bare.get("allOf") or []
            if applied.get("allOf") != bare.get("allOf"):
                spliced_at.add((document, pointer))
                # The node's own conjuncts are the TAIL, untouched and in order.
                assert applied["allOf"][len(applied["allOf"]) - len(own) :] == own, (
                    document,
                    pointer,
                )
            assert {k: v for k, v in applied.items() if k in bare and k != "allOf"} == {
                k: v for k, v in bare.items() if k != "allOf"
            }, (document, pointer)
    assert added == {"type": {"'object'"}, "allOf": {"allOf"}}, added
    # Non-empty, so the ``allOf`` arm is not graded by a loop that met none of it: the
    # population is a branch of a root union whose root states a sibling, which is
    # exactly what §14 step 9 made emittable.
    claimed("constrained nodes a root's own statement is spliced into", spliced_at)

    # **The splice's own strip, over every node the splice can be made at** -- every
    # node of every portable document, asked at each keyword a same-instance hop
    # descends through.  Both of ``_conjunction``'s arms are reached: the statement it
    # builds out of ``SAME_INSTANCE_FACTS``, whose keys are those three and so can never
    # hold an annotation, and the conjuncts it splices off the node's own ``allOf``,
    # which it strips.  Counted, so neither arm is graded by a loop that met none of it.
    built, spliced_conjuncts = 0, 0
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        for _, node in bundle.nodes(doc):
            for through in (*_base.SAME_INSTANCE_LIST, *_base.SAME_INSTANCE_ONE):
                for one in _base._conjunction(node, through):
                    assert not {"title", "description"} & set(one), (document, through, one)
                    if set(one) <= set(_base.SAME_INSTANCE_FACTS):
                        built += 1
                    else:
                        spliced_conjuncts += 1
    assert built and spliced_conjuncts, (built, spliced_conjuncts)


def test_every_class_at_a_constrained_node_refuses_a_non_object_its_own_node_admits() -> None:
    """End to end on the committed tree: the classes this made possible.

    Derived off the tree rather than listed -- every graded class whose own pointer is
    in its document's constrained set -- and floored, because this set did not exist
    before and an empty loop would pass.

    **THE OBLIGATION IS UNIVERSAL AND HAS NO EXCEPTION LIST.**  For every one of them:
    the schema the class NAMES refuses a non-object, and the class refuses it.  Read
    through :func:`_refuses`, which is the document-rooted reading, because a bare
    validator ERRORS at 21 of them rather than answering.

    **THE CONTRAST IS A PARTITION BY MEASUREMENT, NOT A FILTER.**  At some of these
    nodes the bare node refuses a non-object on its own, so the enclosing ``type`` adds
    nothing and the bare-versus-applied contrast has no content there.  Which ones is a
    FACT ABOUT THE BUNDLE and it is read off the bundle, not listed: the two parts are
    named, closed with :func:`partitions`, and the contentful part is floored so it
    cannot empty out.

    **The clause this replaces, and why its own argument is what removed it.**  The
    excluded set used to be spelled as 44 pointers under ``ALREADY_AN_OBJECT_ITSELF``
    with the reason *"excluded by NAME rather than derived from the assertion that would
    fail, because deriving it from that assertion makes the loop grade its own filter"*,
    and the set of contributing DOCUMENTS as a frozen equality of 23 names.  The
    no-self-filter rule is right about FILTERS and the answer to it is to have none:
    nothing is excluded from the obligation above, so there is no filter for it to
    grade, and the derived split is REPORTED as a partition instead of narrowing an
    assertion.  Measured at ``1ade87e90`` (2026-11-06, ``adcp-client-python-sjzy``),
    which is what made re-pointing the two literals the wrong repair:

    * 295 graded classes sit at a node their own document constrains to an object.
    * 110 of them have a bare node that refuses a non-object by itself; 44 were named
      in the list, so **45 were not** -- each one a row the loop's first assertion
      would have failed on.
    * 21 are ``core/format.json``'s individual-asset branches, at which BOTH bare
      readings raise ``_WrappedReferencingError`` under a bare validator (see
      :func:`_refuses`) -- so the loop would have ERRORED there, not failed.
    * the document equality was stale in BOTH directions: 32 documents had arrived and
      **3 had left** (``brand/verify-brand-claims-request.json``,
      ``core/performance-feedback.json``, ``media-buy/product-refinement.json``, each
      carrying a comment asserting it contributed a row).  So "a set that grew" was
      half the reading, and re-pasting it would have deleted three recorded facts
      silently and left 66 pairs red.

    What the two literals were FOR is kept: the obligation now ranges over all 295
    instead of 251-minus-44, and the floors below say what may not happen.  The
    universal half is weak at the 110 (a node that refuses on its own makes the
    conjunction refuse trivially) and carries its whole content at the 185, which is
    exactly why that part and not the other one is floored.
    """
    import test_emit  # the tree reader, one reading for the whole suite

    constrained = [
        g
        for g in test_emit.graded()
        if isinstance(g.model, type)
        and issubclass(g.model, AdCPBaseModel)
        and g.ref.pointer.lstrip("#")
        in bundle.constrained_to_object(bundle.read(BUNDLE, g.ref.document))
    ]
    at = claimed(
        "graded classes at a node their own document constrains to an object",
        {f"{g.ref.document}{g.ref.pointer}" for g in constrained},
    )
    assert len(at) == len(constrained), "one pointer reached twice"

    # THE OBLIGATION, over every one of them, with nothing excluded.
    for g in constrained:
        assert _refuses(g.ref.document, schema_at(g.ref), "a string"), g.ref
        with pytest.raises(Exception):  # noqa: B017 -- either half of the entry point may answer
            g.accept("a string")

    # THE CONTRAST, split by what the BARE node does and reported as a partition.  Both
    # sides of the split are read by ``_node``, a second walk, so the side that decides
    # the split is not the function under test.
    bare_refuses: set[str] = set()
    bare_admits: set[str] = set()
    for g in constrained:
        bare = _node(bundle.read(BUNDLE, g.ref.document), g.ref.pointer.lstrip("#"))
        key = f"{g.ref.document}{g.ref.pointer}"
        (bare_refuses if _refuses(g.ref.document, bare, "a string") else bare_admits).add(key)
    partitions(at, bare_refuses_a_non_object_alone=bare_refuses, bare_admits_one=bare_admits)

    # The contentful part: the enclosing root's ``type`` is the whole of what refuses
    # here, so this is the part the obligation above is a statement about.  Floored and
    # never equal: every emitting row adds graded pairs and none removes one, so a
    # merge of two lanes takes the LARGER reading -- the same decision
    # ``EMITTED_FLOOR`` records in this file.  43 documents contribute at 1ade87e90.
    claimed("pairs where only the enclosing root's type refuses a non-object", bare_admits)
    ratchet(
        "graded classes at a node their own document constrains",
        len(at),
        at_least=295,
        because=(
            "an emitting row adds graded pairs and removes none, so this only grows; "
            "a drop is a document or a class that stopped emitting"
        ),
    )
    ratchet(
        "pairs where only the enclosing root's type refuses a non-object",
        len(bare_admits),
        at_least=185,
        because=(
            "this grows with the pairs above and shrinks only if a bundle node starts "
            "refusing a non-object by itself, which empties this test of content; the "
            f"live split by document is {sorted({k.split('#')[0] for k in bare_admits})}"
        ),
    )


def test_all_eleven_emit_and_the_residue_is_empty() -> None:
    """The outcome, and the residue is now empty.

    11 documents were refused at a node their own root constrains to an object, and
    **all 11 named here emit**.  "Every document whose root constrains the instance to an
    object emits" is therefore true without qualification, which it was not before.

    It was 3 and 8, then 6 and 5 once `salesagent-j3k2l.19` lowered `uniqueItems` on
    the class holding the array, then 10 and 1 at 16052ffb0 when the four `$ref` rows
    left, and it is 11 and 0 at ``adcp-client-python-10l.21``'s third instalment: the
    last entry's chain target was refused for a ``type`` word beside a NESTED union, which
    §14 step 9's first faithful row answers.  The residue reaching zero is what a later
    row landing looks like from here, which is why this is pinned by NAME rather than by a
    count alone -- and the test's own name carries the two numbers, so it moved with them.

    The partition is closed below rather than left as two subset checks: a document
    the emitter neither built nor refused would otherwise satisfy both halves.  The
    residue is still a PART of it, empty, so a document arriving in it reddens here.
    """
    eleven = sorted(set(NOW_EMITTED) | set(STILL_REFUSED))
    # The two named sets are DISJOINT and together are the population this test grades,
    # so a document moving from one to the other is caught by the partition rather than
    # by a count that stays 11 either way.
    partitions(eleven, now_emitted=NOW_EMITTED, still_refused=set(STILL_REFUSED))
    out = compiled(BUNDLE, eleven)
    assert set(NOW_EMITTED) <= set(out.emitted), sorted(set(NOW_EMITTED) - set(out.emitted))
    for document, (keyword, pointer) in STILL_REFUSED.items():
        row = out.refusals[document]
        assert (row["keyword"], row["pointer"]) == (keyword, pointer), (document, row)
    # Restricted to the eleven: ``emit`` walks the ``$ref`` closure, so
    # ``out.emitted`` carries targets that were never in this population.
    assert [d for d in eleven if d in out.emitted or d in out.refusals] == eleven, [
        d for d in eleven if d not in out.emitted and d not in out.refusals
    ]


def test_no_document_in_the_bundle_reaches_the_refusal_any_more() -> None:
    """The refusal's population is 0, which is why the perturbations below exist.

    Stated as a measurement and not as a claim that the refusal is dead code: it is
    the designed outcome for a node nothing constrains, the probes under it are what
    reach it, and a bundle that gains such a document gains it here.
    """
    portable = claimed("bundle.portable", bundle.portable(BUNDLE))
    out = compiled(BUNDLE, sorted(portable))
    partitions(portable, emitted=set(out.emitted), refused=set(out.refusals))
    # Re-pinned 674 -> 686 on bcb0b8ca8, and this is the EMITTED count over all
    # 1,054 portable documents -- NOT the 682 the committed tree holds, which is
    # the population() run. Those two populations have been confused in three
    # briefings; read 691 as a module count and the tree looks stale by nine.
    # 686 -> 691 at ``salesagent-j3k2l.40``: a union BRANCH that composes is lowered
    # by ``lower.composition.lower_composition`` now, so 3 of the 10 documents waiting on the
    # shared conjunct reader emit and 2 chained onto them follow.
    # 691 -> 705 at ``salesagent-j3k2l.28``: three refusals are gone -- two whose
    # stated reason was a claim about a harness ``.32``/``.33`` had already changed,
    # and one whose
    # hazard no emitter produces -- so the 9 + 8 + 3 documents they held emit, less
    # the 6 that refuse on a second keyword once the first refusal is lifted.
    # 705 -> 716 at ``salesagent-j3k2l.21``, in two steps of one row: a union root whose
    # instance the DOCUMENT says is a scalar is an alias rather than a base plus
    # subclasses (+5, of which 2 are alias roots and 3 released through their ``$ref``),
    # and then D2's amendment renders a value set no name reaches as a ``Literal`` (+6,
    # of which 2 are the geo-place pair and 4 released through their ``$ref``).
    #
    # A FLOOR, not an equality, and the direction is the reason: every emitting row
    # takes this number UP and no row may take it down, so an equality is red on two
    # branches at once with two different correct values.  The history above is six
    # re-pointings of it (674, 686, 691, 705, 716) and every one was a row doing its
    # work.
    ratchet(
        "documents emitted over the whole portable set",
        len(out.emitted),
        at_least=EMITTED_FLOOR,
        because="an emitting row only adds documents; a drop means a document that "
        "lowered stopped lowering, which is a regression and never a row's intent",
    )
    assert [d for d, r in out.refusals.items() if "nothing enclosing it" in r["detail"]] == []


# --------------------------------------------------------------------------- #
# the perturbations: the distinction, broken on purpose in each direction
# --------------------------------------------------------------------------- #
def _write(tmp_path: Path, documents: dict[str, dict]) -> Path:
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


def _union(root_type: str | None, combinator: str = "oneOf") -> dict:
    """A union root whose branches declare no ``type`` of their own."""
    doc: dict = {
        "title": "Probe",
        combinator: [
            {"properties": {"kind": {"const": "a"}, "a": {"type": "string"}}, "required": ["kind"]},
            {"properties": {"kind": {"const": "b"}, "b": {"type": "string"}}, "required": ["kind"]},
        ],
    }
    if root_type is not None:
        doc["type"] = root_type
    return doc


def test_a_typeless_branch_emits_only_while_its_root_constrains_the_instance(tmp_path) -> None:
    """The one distinction, run three ways on documents that differ in one key.

    The ``jsonschema`` lines are what make this a measurement rather than a
    restatement, and they are asked of the BRANCH, because the branch node is the
    schema a branch class is paired with.  Where the root constrains the instance the
    branch refuses a string; where nothing does, the branch admits one and a class
    there would be narrower than the schema it names.

    **WHICH ROOTS CONSTRAIN IT IS NOT ONLY THE ONES THAT SAY SO, and the third arm is
    that** (``_base.entailed_types``, decided 2026-10-29).  A ``oneOf`` of two or more
    branches that each admit every non-object VACUOUSLY -- ``properties`` and
    ``required`` are ignored for a non-object -- admits no non-object at all: a string
    satisfies BOTH branches, ``oneOf`` demands exactly one, so the document refuses it.
    The word is then the document's statement about the instance as surely as a stated
    one, and the branch class is faithful rather than narrow.  The typeless ``oneOf``
    probe was this test's "does not constrain" arm and it is its SECOND CONSTRAINING
    arm now; the last two assertions of the old reading -- that it refuses and that the
    branch admits a string -- were a true measurement of the document read two
    incompatible ways, which is what the clause settles.

    **The arm that really does not constrain is the same branch list under ``anyOf``**,
    and that is the exclusivity the clause rests on rather than a second probe shape:
    satisfying all is satisfying at least one, so the ``anyOf`` document ADMITS a
    string -- asserted below, on the document and not only on the branch -- and a class
    at its branch would refuse what the document accepts.
    """
    with_type, entailing = _union("object"), _union(None)
    no_word = _union(None, "anyOf")
    # Nothing constrains the ``anyOf`` branch, and nothing constrains the DOCUMENT
    # either: both admit a string, which is why a class there is the narrowing §2 forbids.
    assert jsonschema.Draft7Validator(applied_schema(no_word, "/anyOf/0")).is_valid("a string")
    assert jsonschema.Draft7Validator(no_word).is_valid("a string")
    # The stated word and the entailed one, each refusing the string at the branch and at
    # the document -- the second of them on ``oneOf`` rather than on ``type``.
    for probe, hop in ((with_type, "/oneOf/0"), (entailing, "/oneOf/0")):
        assert not jsonschema.Draft7Validator(applied_schema(probe, hop)).is_valid("a string")
        assert not jsonschema.Draft7Validator(probe).is_valid("a string")

    for name, probe in (("a", with_type), ("c", entailing)):
        out = emit.emit(
            _write(tmp_path / name, {"core/probe.json": probe}), ["core/probe.json"]
        )
        assert out.refusals == {}, out.refusals
        assert "core/probe.json" in out.emitted

    out = emit.emit(_write(tmp_path / "b", {"core/probe.json": no_word}), ["core/probe.json"])
    assert "core/probe.json" not in out.emitted
    row = out.refusals["core/probe.json"]
    assert (row["keyword"], row["pointer"]) == ("type", "/anyOf/0"), row
    assert "nothing enclosing it constrains the instance to an object" in row["detail"]


def test_a_properties_hop_carries_nothing_because_it_names_another_instance(tmp_path) -> None:
    """The hop distinction, which is what keeps a property's own schema refused.

    The node is one ``properties`` hop BELOW a branch the root does constrain, which is
    the shape that grades the rule: the chain is live at ``/oneOf/0``, so clearing it
    at the next hop is a decision the rule makes rather than a state it never left.
    ``core/deployment.json#/oneOf/0/properties/activation_key`` is the real instance of
    it, and a rule that read the nearest enclosing ``type`` without asking whether the
    hop preserved the instance would emit a class there.

    A root declaring ``type: object`` says nothing about the value at one of its keys,
    and ``jsonschema`` agrees -- the document admits ``"inner": "a string"``.

    The keyword asserted is the one that actually fires, and it is ``type``.

    **It read ``properties`` until ``adcp-client-python-10l.35``, and that WAS the
    defect** rather than a code path worth pinning.  A typeless node carrying
    ``properties`` does not reach ``lower_object`` -- the typeless row is screened at its
    own node first -- and the screen's own sentence for a lowering cell is "this step
    lowers no such keyword (a later D2 row does)".  There is no later row: ``properties``
    lowers at every position a class is reached, so the refusal named a keyword that is
    not the reason and promised a row nobody would write.  The docstring's own words for
    the old state were "the emitter refuses this node twice over".

    The typeless row answers for it now, on ``type``, in ``lower_object``'s own direction
    -- "the document admits a non-object that no class can", §5's ``type`` row read at
    its last clause -- so the node is refused ONCE, on the keyword that is the reason, at
    the same pointer it always named.  The two rows keep separate WORDING on purpose, and
    ``test_no_document_in_the_bundle_reaches_the_refusal_any_more`` above is why: it
    identifies ``lower_object``'s arm by its text and measures its population at 0.
    """
    inner = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    doc = {
        "title": "Probe",
        "type": "object",
        "oneOf": [
            {"properties": {"kind": {"const": "a"}, "inner": inner}, "required": ["kind"]},
            {"properties": {"kind": {"const": "b"}, "b": {"type": "string"}}, "required": ["kind"]},
        ],
    }
    assert jsonschema.Draft7Validator(doc).is_valid({"kind": "a", "inner": "a string"})
    constrained = bundle.constrained_to_object(doc)
    assert "/oneOf/0" in constrained  # the chain is live one hop up
    assert "/oneOf/0/properties/inner" not in constrained
    assert applied_schema(doc, "/oneOf/0/properties/inner") is inner

    out = emit.emit(_write(tmp_path, {"core/probe.json": doc}), ["core/probe.json"])
    row = out.refusals["core/probe.json"]
    assert (row["keyword"], row["pointer"]) == ("type", "/oneOf/0/properties/inner"), row
    # The reason, and not a row waiting to be written: the screen's "a later D2 row does"
    # is what this assertion used to read, for a keyword that already lowers everywhere.
    assert "admits a non-object that no class can" in row["detail"], row
    assert refusal_module.DEFERRED_TO_A_LATER_ROW not in row["detail"], row


def test_a_node_declaring_another_type_is_refused_whatever_encloses_it() -> None:
    """The node's own fact wins, and a contradiction is refused rather than rewritten.

    A branch declaring ``type: "string"`` under a root declaring ``type: "object"``
    admits nothing at all, and a class for it would accept what the document refuses.
    The branch row refuses it before ``lower_object`` is reached, so the keyword and
    pointer are asserted rather than the function: either refusal is correct and the
    one that fires is the row's own.
    """
    doc = _union("object")
    doc["oneOf"][0] = {**doc["oneOf"][0], "type": "string"}
    assert "/oneOf/0" not in bundle.constrained_to_object(doc)
    assert applied_schema(doc, "/oneOf/0")["type"] == "string"
    caught = refusal_from(emit.lower_document("core/probe.json", doc))
    assert (caught.keyword, caught.pointer) == ("type", "/oneOf/0"), caught


@pytest.mark.parametrize("keyword", ["if", "not"])
def test_a_conditional_or_negated_position_carries_nothing(keyword: str) -> None:
    """``if`` and ``not`` are not same-instance hops, and the exclusion only refuses.

    A subschema in either position is not something an instance is REQUIRED to
    satisfy: ``if`` decides whether ``then`` applies and ``not`` is negated.  So the
    schema returned for such a node states only what the node itself states, and
    carrying an outer assertion in would make the returned schema claim a requirement
    that does not hold at that position.

    Asserted as the absence plus its justification, and NOT as a change in any
    document's accepted set -- measured, there is none to assert: an assertion the
    enclosing node already makes at the same location cannot change that node's own
    verdict, so conjoining here would be harmless and merely wrong about what the
    position means.  What makes the exclusion safe is the direction it errs in, and
    what makes it cost nothing is the second assertion: D6 makes both keywords a rule,
    so no class in the committed tree is declared at or under one.
    """
    import test_emit

    inner = {"properties": {"a": {"type": "string"}}}
    doc = {"title": "Probe", "type": "object", keyword: inner}
    assert f"/{keyword}" not in bundle.constrained_to_object(doc)
    assert applied_schema(doc, f"/{keyword}") is doc[keyword]

    # Over the pairs the tree carries, which is named non-empty first: "no pair sits at
    # a conditional position" is free over an empty set of pairs, and the tree is
    # imported at module scope so an import that half-failed would give exactly that.
    #
    # **A SEGMENT and not a substring, fixed at ``adcp-client-python-10l.21``.**  The
    # reading was ``f"/{keyword}" in ref.pointer``, and ``not`` is a prefix of a property
    # name: ``protocol/sync-agent-notification-configs-request.json`` began emitting and
    # its pair at ``#/properties/notification_configs/items`` read as a pair sitting
    # under a ``not``.  The test one row below already splits the pointer into segments
    # for the same four keywords, so this is the two readings agreeing rather than a new
    # one.
    pairs = claimed("graded pairs", {g.ref for g in test_emit.graded()})
    at = [ref for ref in pairs if keyword in ref.pointer.split("/")]
    assert at == [], at


def test_the_assertion_is_inherited_down_a_chain_of_combinator_hops() -> None:
    """Two hops, because the rule is stated as inheritance and one hop does not grade
    it.

    ``/anyOf/0/oneOf/1`` under a root declaring ``type: object``, with the node in
    between declaring none.  Every one of the bundle's 10 real sites is ONE hop below
    its root, so a constructed document is the only grader for the second -- and
    ``then``/``else`` reach it over the real bundle, where 639 of the 2,040 constrained
    pointers run through one of the four conditional segments.
    """
    inner = {"properties": {"a": {"type": "string"}}}
    doc = {"title": "Probe", "type": "object", "anyOf": [{"oneOf": [inner, inner]}]}
    constrained = bundle.constrained_to_object(doc)
    assert "/anyOf/0" in constrained
    assert "/anyOf/0/oneOf/0" in constrained
    assert applied_schema(doc, "/anyOf/0/oneOf/1")["type"] == "object"

    # Non-empty: the claim is that the bundle HAS nodes constrained through a
    # conditional for the reading above to be about, and 639 was one bundle version's
    # count of them.
    claimed(
        "nodes constrained to an object through a conditional",
        {
            (document, p)
            for document in bundle.portable(BUNDLE)
            for p in bundle.constrained_to_object(bundle.read(BUNDLE, document))
            if any(seg in ("if", "not", "then", "else") for seg in p.split("/"))
        },
    )


# --------------------------------------------------------------------------- #
# the RESOLUTION SCOPE of a nested node's schema (salesagent-j3k2l.28)
#
# `applied_schema` says WHICH assertions a nested node's schema carries;  this is
# the other half of the same question -- what a `$ref` inside that node resolves
# AGAINST.  `bundle.record` inlines a REMOTE reference and leaves a LOCAL one, so
# a node at `#/definitions/box_decoration` can say `{"$ref": "#/definitions/
# rectangle"}`: a pointer relative to the DOCUMENT ROOT.  Handed the node alone as
# its own schema, `jsonschema` resolves `#/` within the node and raises
# `PointerToNowhere`, so `strict_validate` refused EVERY payload -- 5 pairs,
# reporting `accepts:model_error` rather than a verdict about any value.  0 such
# pairs existed before, because every document carrying one was refused by name.
# --------------------------------------------------------------------------- #
#: A payload `core/placement-presentation.json#/definitions/box_decoration` ACCEPTS,
#: whose every constraint but `kind` is reached through a local `$ref`: `layer` and
#: `fill_color` name `#/definitions/{layer,color}` and `bounds` names
#: `#/definitions/rectangle`, whose own `minimum: 1` is two references deep.
THROUGH_A_LOCAL_REF = (
    "core/placement-presentation.json",
    "#/definitions/box_decoration",
    {
        "kind": "box",
        "layer": "behind_creative",
        "bounds": {"x": 0, "y": 0, "width": 1, "height": 1},
        "fill_color": "#ffffff",
    },
)


def test_a_nested_nodes_schema_resolves_a_local_ref_against_its_document() -> None:
    """The schema half ACCEPTS what the document accepts, and REFUSES through the
    reference -- which is what says the scope was widened and not the schema.

    Both halves on one pair, because a scope that resolved and asserted nothing would
    pass the first assertion alone: a reading that answered a ``$ref`` with the empty
    schema accepts every payload and is indistinguishable from this one until a
    constraint BEHIND the reference is asked to bite.
    """
    import test_emit  # the tree reader, one reading for the whole suite

    document, pointer, accepted = THROUGH_A_LOCAL_REF
    (cls,) = [
        g.model
        for g in test_emit.graded()
        if (g.ref.document, g.ref.pointer) == (document, pointer)
    ]
    assert cls.strict_validate(accepted)

    # each refusal is a constraint the node reaches only through a local `$ref`
    for payload, keyword, loc in [
        ({**accepted, "bounds": {**accepted["bounds"], "width": 0}}, "minimum", ("bounds", "width")),
        ({**accepted, "layer": "sideways"}, "enum", ("layer",)),
        ({**accepted, "fill_color": "ffffff"}, "pattern", ("fill_color",)),
    ]:
        with pytest.raises(ValidationError) as caught:
            cls.strict_validate(payload)
        (error,) = caught.value.errors()
        assert (error["type"], error["loc"]) == (keyword, loc), error


def test_reading_the_node_alone_cannot_resolve_it_and_refuses_everything() -> None:
    """The BREAK, and it is the emitter's own state before this change: ``_refuse``
    handed the node as its own schema.

    It is not a near miss -- the node is unvalidatable, so the pair reports nothing
    about any value.  Asserted as the raise ``jsonschema`` makes rather than as an
    outcome string, so a later change that merely relabels it still fails here.
    """
    document, pointer, accepted = THROUGH_A_LOCAL_REF
    node = schema_at(SchemaRef(document=document, pointer=pointer))
    validator = jsonschema.validators.validator_for(node, jsonschema.Draft7Validator)
    with pytest.raises(jsonschema.exceptions._WrappedReferencingError):
        list(validator(node).iter_errors(accepted))

    # and the document-rooted validator, which is what `_refuse` builds, resolves it
    root = _base._document(document)
    rooted = jsonschema.validators.validator_for(root, jsonschema.Draft7Validator)
    assert list(rooted(root).evolve(schema=node).iter_errors(accepted)) == []


def test_every_document_side_local_ref_resolves_and_the_set_of_sites_is_not_empty() -> None:
    """The DENOMINATOR, which is the one thing the outcome pins cannot say.

    ``tests/test_emit.py``'s one harness total pins
    ``accepts:model_error`` at 0, and before this row that pin was green FOR FREE: **0
    graded pairs of the committed tree held a document-side local ``$ref`` at all**,
    because every document carrying one was refused by name
    (``codegen.lower.union``'s deleted guard measured it). A green mark over an empty
    set says nothing, so this names the set and asserts it is not empty.

    **THE OBLIGATION IS THE LOOP, AND IT IS EVERY SITE.**  Each (pair, reference) site
    the derivation reaches is asserted to RESOLVE through :func:`applied_schema`
    against its own document's root, and the ones that do not are reported BY SITE.
    Counted as (pair, reference) sites and keyed by document, where
    ``tests/test_emit.py`` reads the same references once per document: two
    denominators for one fact.

    **THE SET OF DOCUMENTS IS DERIVED AND IS NOT A LIST OF NAMES.**  It used to be a
    frozen equality of 29 document names, re-pasted at each of
    ``adcp-client-python-10l.{3,20,21,55}`` with the arrivals annotated in place -- a
    ratchet spelled as an equality, which reddens whenever the corpus grows CORRECTLY
    and whose only repair is to paste the new reading in.  ``tests/nodeset`` says the
    same thing of counts and the same argument settles a set of names: it is one bundle
    version's reading of a quantity every emitting row moves, so two rows in flight
    compute two different correct values and no merge resolves that by picking a side.
    Measured at ``1ade87e90`` (2026-11-06, ``adcp-client-python-sjzy``): 45 documents
    live against 29 pinned, 16 arrived, **none left**, and all 774 sites resolve -- so
    the equality carried no fact the loop does not, and reddened on 16 correct
    arrivals.  The floor below is what it meant.

    A shrink stays readable by name: the floor's reason carries the live reading keyed
    by document, so a breach prints which documents hold what rather than one number
    going down.
    """
    import collections

    import test_emit  # the tree reader, one reading for the whole suite

    def local_refs(node: object) -> list[str]:
        if isinstance(node, dict):
            found = [node["$ref"]] if isinstance(node.get("$ref"), str) else []
            return found + [r for v in node.values() for r in local_refs(v)]
        if isinstance(node, list):
            return [r for v in node for r in local_refs(v)]
        return []

    per_document: collections.Counter[str] = collections.Counter()
    sites: set[tuple[str, str]] = set()
    unresolved: list[tuple[str, str]] = []
    for g in test_emit.graded():
        root = _base._document(g.ref.document)
        for reference in local_refs(schema_at(g.ref)):
            if not reference.startswith("#"):
                continue
            per_document[g.ref.document] += 1
            sites.add((f"{g.ref.document}{g.ref.pointer}", reference))
            # and it resolves, which is what the scope widening is for
            if not applied_schema(root, reference):
                unresolved.append((f"{g.ref.document}{g.ref.pointer}", reference))
    assert not unresolved, unresolved

    # The denominator, named at the point it is ranged over.  ``claimed`` and not
    # ``assert all(per_document.values())``, which was the line here before and could
    # never fail: a ``Counter`` holds a key only because something incremented it, so
    # every value it holds is at least 1 and the assertion was a gate that passes when
    # nothing happens.
    claimed("graded (pair, document-side local reference) sites", sites)
    ratchet(
        "documents holding a document-side local reference",
        len(per_document),
        at_least=45,
        because=(
            "a document arrives here by EMITTING and an emitting row removes none, so "
            "this only grows and a merge of two lanes takes the larger reading; the "
            f"live reading keyed by document is {sorted(per_document.items())}"
        ),
    )
    ratchet(
        "(pair, document-side local reference) sites",
        sum(per_document.values()),
        at_least=774,
        because=(
            "one emitted document contributes one site per reference per graded pair, "
            "so this grows with the documents above; a drop with the document count "
            "held is a reference that stopped being reached"
        ),
    )


# --------------------------------------------------------------------------- #
# WHICH TREE the record comes from: the one the class was emitted into
# --------------------------------------------------------------------------- #
def _tree_with(root: Path, document: str, record: dict, module: str, symbol: str) -> str:
    """A module and its record, written into ``root`` as an emitted tree writes them.

    The module is written the way ``codegen.render`` writes one -- ``__adcp_schema__``
    naming a bundle-relative document, ``strict_validate`` off the base -- so what the
    test exercises is the production entry point and not a hand-built stand-in.
    """
    (root / document).parent.mkdir(parents=True, exist_ok=True)
    (root / document).write_text(json.dumps(record))
    (root / f"{module}.py").write_text(
        "from adcp.types._base import AdCPBaseModel, SchemaRef\n\n\n"
        f"class {symbol}(AdCPBaseModel):\n"
        f"    __adcp_schema__ = SchemaRef({document!r}, '#')\n"
    )
    return f"{_base.PACKAGE}.{module}"


@contextlib.contextmanager
def _bound_in_front(root: Path):
    """``root`` in front of the records package's ``__path__``, as a run binds its tree.

    ``codegen/__main__.py`` does exactly this -- an emitted module says
    ``from adcp.types.constraints import ...``, an absolute name, so the modules have to
    be imported under the package's own name and cannot be loaded from a path.  Undone on
    the way out, with the modules it bound dropped from ``sys.modules``, so no later test
    inherits the binding.
    """
    package = importlib.import_module(_base.PACKAGE)
    before = set(sys.modules)
    package.__path__.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        yield
    finally:
        package.__path__.remove(str(root))
        for name in sorted(set(sys.modules) - before):
            del sys.modules[name]
        importlib.invalidate_caches()


def test_a_class_resolves_its_record_from_the_tree_it_was_emitted_into(tmp_path) -> None:
    """**THE SILENT CASE, AND IT IS THE ONE THAT SHIPS** (``adcp-client-python-ir3l``).

    ``_base._document`` resolved every record through ``importlib.resources.files`` over
    the IMPORTED package, which answers from wherever that package's ``__init__`` was
    loaded and never from the directories its ``__path__`` currently names.  A run that
    writes a tree binds it in FRONT and imports the modules it just wrote, so the class
    came from the new tree and its record came from the committed one.  Measured while
    grading bundle 3.3: 1,806 pairs, 0 pass, 1,806 absent -- 107 ``FileNotFoundError``
    where a 3.3-only document has no record in the committed tree, 28
    ``KeyError``/``IndexError`` at a pointer that is not 3.3's -- **and a document present
    in BOTH trees was served the 3.2 text with no error at all.**  So a class emitted from
    3.3 carried a ``__adcp_schema__`` naming a 3.3 document and validated payloads against
    the installed 3.2 record: a consumer getting a verdict from the wrong version of the
    protocol, with nothing to tell it so.

    This is that case, with the two trees differing in what they ACCEPT so the defect is
    visible as a verdict and not only as a path: the front tree admits ``{"a": "x"}`` and
    the back tree requires ``b``.  Both halves are asserted -- what ``schema_at`` returns
    and what the production ``strict_validate`` does with a payload -- because the record
    is read on both paths and §4 of the semantics document requires the two to agree.

    ``docs/plan/final-state.md`` reading 1 is the rule: "BOTH CHECKS ARE A FUNCTION OF
    (class, document) AND OF NOTHING ELSE."
    """
    document = "scratch/two-trees.json"
    back = tmp_path / "back"
    front = tmp_path / "front"
    name = _tree_with(
        back,
        document,
        {"type": "object", "required": ["b"], "properties": {"b": {"type": "string"}}},
        "two_trees_back",
        "TwoTreesBack",
    )
    with _bound_in_front(back):
        behind = importlib.import_module(name)
        assert schema_at(behind.TwoTreesBack.__adcp_schema__, module=name)["required"] == ["b"]

    name = _tree_with(
        front,
        document,
        {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}}},
        "two_trees_front",
        "TwoTreesFront",
    )
    # The BACK tree stays bound as well, so the document exists under both roots and the
    # front one is not answering by being the only answer.
    with _bound_in_front(back), _bound_in_front(front):
        ahead = importlib.import_module(name)
        held = schema_at(ahead.TwoTreesFront.__adcp_schema__, module=name)
        assert held["required"] == ["a"], (
            "the class was emitted into the front tree and read the record behind it"
        )
        # And the production entry point, which is the half that ships: the front tree's
        # record accepts ``{"a": ...}`` and the one behind it refuses it for a missing
        # ``b``, so a wrong read is a wrong VERDICT and not a cosmetic difference.
        assert ahead.TwoTreesFront.strict_validate({"a": "x"})
        with pytest.raises(ValidationError):
            ahead.TwoTreesFront.strict_validate({"b": "x"})


def test_a_record_the_classs_own_tree_does_not_carry_is_an_error_and_not_a_fallback(
    tmp_path,
) -> None:
    """**An absent record raises, naming the tree -- it is never served from another one.**

    This is the 107 of ``adcp-client-python-ir3l``'s 1,806, inverted into the shape that
    makes the rule testable: the document exists in the tree BEHIND and not in the tree the
    class was emitted into.  Reaching back for it is exactly the fallback that made a
    3.3-emitted class validate against a 3.2 record, and "the next root happened to have a
    file of that name" is not a weaker version of the right answer -- it is a different
    document.

    The error names the tree, because a reader who gets this has to know which tree was
    searched; asserted on the message, so a later change that raises somewhere else for
    some other reason does not read as this rule holding.
    """
    document = "scratch/only-behind.json"
    back = tmp_path / "back"
    front = tmp_path / "front"
    _tree_with(back, document, {"type": "string"}, "only_behind_back", "OnlyBehindBack")
    front.mkdir(parents=True, exist_ok=True)
    (front / "only_behind_front.py").write_text(
        "from adcp.types._base import AdCPBaseModel, SchemaRef\n\n\n"
        "class OnlyBehindFront(AdCPBaseModel):\n"
        f"    __adcp_schema__ = SchemaRef({document!r}, '#')\n"
    )
    name = f"{_base.PACKAGE}.only_behind_front"
    with _bound_in_front(back), _bound_in_front(front):
        ahead = importlib.import_module(name)
        # The control: the document IS resolvable from the tree behind, so the raise below
        # is the rule and not an absent file.
        assert _base._document(document, str(back))["type"] == "string"
        with pytest.raises(FileNotFoundError) as caught:
            schema_at(ahead.OnlyBehindFront.__adcp_schema__, module=name)
        assert str(front) in str(caught.value), caught.value
        with pytest.raises(FileNotFoundError):
            ahead.OnlyBehindFront.strict_validate("anything")


def test_an_alias_takes_the_module_it_is_defined_in_and_not_its_callers(tmp_path) -> None:
    """D2's root SCALAR has no class to carry a module, so the module is the CALLER's.

    ``codegen.render`` writes ``strict_validate = strict_alias(__adcp_schema__, "X", X)``
    at module scope, so the frame calling ``strict_alias`` IS the emitted module -- the
    same fact a class reads off ``cls.__module__``, by the only name an alias has for it.
    Read at import and not inside the returned closure, which is the distinction this test
    is for: the closure's caller is a CONSUMER, in some other module entirely, and a
    module read there would resolve the record against whatever tree the consumer lives
    in.  So the alias is called from THIS test module after the tree is bound, and the
    record it refuses by must still be the tree's.
    """
    document = "scratch/alias-tree.json"
    front = tmp_path / "front"
    (front / document).parent.mkdir(parents=True, exist_ok=True)
    (front / document).write_text(json.dumps({"type": "string", "maxLength": 2}))
    (front / "alias_tree.py").write_text(
        "from typing import Annotated\n\n"
        "from adcp.types._base import SchemaRef, strict_alias\n\n"
        f"__adcp_schema__ = SchemaRef({document!r}, '#')\n"
        "AliasTree = Annotated[str, None]\n"
        '__all__ = ["AliasTree"]\n'
        'strict_validate = strict_alias(__adcp_schema__, "AliasTree", AliasTree)\n'
    )
    name = f"{_base.PACKAGE}.alias_tree"
    with _bound_in_front(front):
        module = importlib.import_module(name)
        assert module.strict_validate("ab") == "ab"
        # The tree's record bounds the string at 2, so this refusal is proof the alias
        # read the record beside its own module and not the committed package's.
        with pytest.raises(ValidationError):
            module.strict_validate("abc")
