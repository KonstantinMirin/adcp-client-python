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

import functools
import json
from pathlib import Path

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
BUNDLE = REPO / "schemas" / "cache" / "3.2"

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


def test_the_two_populations_partition_the_bundles_typeless_nodes() -> None:
    """The denominators, because the rule is a PARTITION of one set of nodes and a
    verdict over a set nobody named is a verdict over however many nodes there turned
    out to be.

    Each half is asserted NON-EMPTY, which is the fact the two numbers carried: the
    first half alone would hold for a rule that constrains everything and the second
    alone for a rule that constrains nothing.  They are not asserted as sizes -- the
    sizes are one bundle version's reading, and the halves are DISJOINT and TOTAL over
    the typeless nodes, which is the property that cannot be true of one version only.

    The second pair is the subset the DEFECT was found on -- a node declaring a
    non-empty ``properties``, which is the only shape a class can be declared at, so it
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


#: Nodes the root constrains to an object that ALSO constrain themselves, so the
#: enclosing ``type`` adds nothing and this test's bare-versus-applied contrast has no
#: content at them.  Excluded by NAME rather than derived from the assertion that would
#: fail, because deriving it from that assertion makes the loop grade its own filter.
#:
#: The three are ``core/canonical-media-buy-action.json``'s branches, which emit since
#: ``salesagent-j3k2l.43``: each one is ``{"allOf": [{"$ref":
#: core/canonical-media-buy-action-fields.json}], "properties", "required"}``, and that
#: target's own root states ``type: object`` -- so the branch node refuses a string on
#: its own, before anything enclosing it is applied.  Measured directly:
#: ``Draft7Validator(<the branch node>).is_valid("a string")`` is ``False``.
#: **ELEVEN more at ``adcp-client-python-10l.20``, and the mechanism is the one this
#: file's own earlier test already measured**: "326 of the 1,541 are in that second
#: group, every one of them refusing a non-object for a reason of its own (a ``not`` over
#: a ``required``, which a non-object satisfies vacuously, so the negation fails)".  Each
#: of these is a branch of a root union §14 step 9 unblocked, each states
#: ``not: {"required": [...]}`` -- the idiom §4's third dispatch source reads to separate
#: them -- and a string satisfies the inner ``required`` vacuously, so the negation fails
#: and the BARE node refuses the string before anything enclosing it is applied.
#: Measured directly, the same way the three below were:
#: ``Draft7Validator(<the branch node>).is_valid("a string")`` is ``False`` for all 11
#: and ``True`` for the other 43 rows.
#:
#: **TWO more at ``adcp-client-python-10l.34``, by that same mechanism at a NESTED
#: union.**  §8's composition rule reaches a union at any position, so
#: ``account/sync-accounts-request.json``'s ``/properties/accounts/items`` emits a base
#: plus one subclass per branch, and the two branches join this population because the
#: node their enclosing ``items`` constrains to an object is the one each class names.
#: Each branch's ``allOf`` conjuncts are ``not: {"required": [...]}`` and nothing else, so
#: a string satisfies each inner ``required`` vacuously, every negation fails, and the
#: BARE node refuses the string -- the same reading as the 11 above and measured the same
#: way: ``Draft7Validator(<the branch node>).is_valid("a string")`` is ``False`` for both.
#: What does hold for them, measured directly, is the clause the per-row loop is about:
#: the schema each class NAMES refuses a string and ``accept("a string")`` raises.
#:
#: **TWENTY-ONE more at ``adcp-client-python-10l.55``, and they are the FIRST members
#: whose reason is the reference itself rather than a ``not``.**
#: ``core/assets/asset-union.json`` emits -- the branch row asked whether a ``$ref``
#: branch's target had a ``compiler.Shape`` and reported "VASTAsset is not a class" of a
#: class, and it asks ``compiler.TargetKind`` now -- so its 21 branch classes join this
#: population.  Each branch's whole text is ``{"$ref": <an asset document>}`` and every
#: one of those targets states ``type: "object"`` at its root, so the BARE node refuses a
#: string through the reference, before the root's own ``type`` is applied: the enclosing
#: ``type`` adds nothing and this test's bare-versus-applied contrast has no content at
#: them.  Measured directly, the same way every member above was:
#: ``Draft7Validator(<the branch node>).is_valid("a string")`` is ``False`` for all 21.
ALREADY_AN_OBJECT_ITSELF = frozenset(
    {
        *(f"core/assets/asset-union.json#/oneOf/{i}" for i in range(21)),
        "account/sync-accounts-request.json#/properties/accounts/items/oneOf/0",
        "account/sync-accounts-request.json#/properties/accounts/items/oneOf/1",
        "core/canonical-media-buy-action.json#/oneOf/0",
        "core/canonical-media-buy-action.json#/oneOf/1",
        "core/canonical-media-buy-action.json#/oneOf/2",
        "brand/creative-approval-response.json#/oneOf/0",
        "brand/creative-approval-response.json#/oneOf/1",
        "brand/creative-approval-response.json#/oneOf/2",
        "brand/creative-approval-response.json#/oneOf/3",
        "brand/get-brand-identity-response.json#/oneOf/0",
        "brand/get-brand-identity-response.json#/oneOf/1",
        "brand/get-rights-response.json#/oneOf/0",
        "brand/get-rights-response.json#/oneOf/1",
        "brand/search-brands-response.json#/oneOf/0",
        "brand/search-brands-response.json#/oneOf/1",
        "core/brand-response-authorization-result.json#/oneOf/0",
        # ``adcp-client-python-10l.21``'s fifth instalment: the document emits now, and
        # its first branch ``not``s a ``required`` group, so a non-object satisfies the
        # negated group vacuously and the BARE node already refuses the string.  Its
        # second branch states no ``not`` and is a row.
        "account/list-account-changes-response.json#/oneOf/0",
        # ``adcp-client-python-10l.50``: the document emits now that §4's nested rule
        # names a position rather than the path to it, so the two positions that folded
        # to one class name are two names.  All SIX of its branches ``not`` a
        # ``required`` group -- each excludes the trigger inputs the other five own --
        # so a non-object satisfies every negated group vacuously and the bare node
        # already refuses the string.  The document therefore contributes no row, which
        # is why it is here in full and absent from the set of row documents above.
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/0",
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/1",
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/2",
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/3",
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/4",
        "formats/canonical/seller_rendered_stateful_display.json#/properties/transitions/items/oneOf/5",
    }
)


def test_every_class_at_a_constrained_node_refuses_a_non_object_its_own_node_admits() -> None:
    """End to end on the committed tree: the classes this made possible.

    Derived off the tree rather than listed -- every graded class whose own pointer is
    in its document's constrained set -- and pinned to a non-zero count, because this
    population did not exist before and an empty loop would pass.

    For each: the BARE node admits a string, the schema the class NAMES refuses it,
    and the class refuses it.  The middle one is the point.  The other two held before
    this change as well, and together they are exactly the state that made the branch
    unemittable.
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
    # The exclusion is asserted to BITE and to be drawn from the set it narrows, so a
    # stale entry is an allowlist nobody can shrink and reddens here instead.
    reached = {f"{g.ref.document}{g.ref.pointer}" for g in constrained}
    assert ALREADY_AN_OBJECT_ITSELF <= reached, sorted(ALREADY_AN_OBJECT_ITSELF - reached)
    rows = [
        g
        for g in constrained
        if f"{g.ref.document}{g.ref.pointer}" not in ALREADY_AN_OBJECT_ITSELF
    ]
    # The pairs at a constrained node, non-empty -- the per-row loop below is the
    # obligation and 64 is the number of rows this emitted tree gives it.  WHICH
    # documents they come from is the fact worth pinning and it is named below.
    claimed("pairs at a node its own document constrains", {g.ref for g in rows})
    assert {g.ref.document for g in rows} == {
        # **``core/assets/asset-union.json`` JOINED THE POPULATION AT
        # ``adcp-client-python-10l.55`` AND CONTRIBUTES NO ROW**, which is why it is not
        # named here: its 21 branch classes are all in ``ALREADY_AN_OBJECT_ITSELF``, each
        # for that set's own measured reason -- a branch whose whole text is a ``$ref``
        # onto an object root refuses a non-object before anything enclosing it applies.
        # **TWO more at ``adcp-client-python-10l.21``'s SEVENTH instalment**, and they
        # arrive by that row's emission rather than by anything about this mechanism:
        # ``core/assets/vast-asset.json`` and ``core/assets/daast-asset.json`` emit now
        # that §2's intersection rule writes the composition at ``items`` and the base's
        # ``$ref`` survives it as a conjunct, and each one's two branch classes sit at a
        # node its own root constrains to an object.  Neither branch ``not``s a
        # ``required`` group, so both contribute rows.  The per-row loop grades all 64
        # and reported nothing new.
        "core/assets/daast-asset.json",
        "core/assets/vast-asset.json",
        # **ONE more at ``adcp-client-python-10l.21``'s FIFTH instalment**, and it arrives
        # by that row's emission rather than by anything about this mechanism:
        # ``account/list-account-changes-response.json`` is a union root that refused on a
        # ``$ref`` §2's intersection produced at a pointer no edge of its own text carries,
        # ``emit.inherited_sites`` resolves that site now, and both of its branch classes
        # sit at a node its own root constrains.  The FIRST of the two is in
        # ``ALREADY_AN_OBJECT_ITSELF`` -- it ``not``s a ``required`` group and so refuses a
        # non-object on its own -- so the document contributes one row.  The per-row loop
        # grades all 60 and reported nothing new.
        "account/list-account-changes-response.json",
        # **SEVEN more at ``adcp-client-python-10l.21``'s third instalment**, and all
        # seven arrive by one of that row's two shapes rather than by anything about this
        # mechanism.  Six are §14 step 9's first faithful row -- a ``type`` word beside a
        # NESTED combinator is in every branch already, so the document's own worded union
        # stops refusing it -- and each contributes a class at a node its own root
        # constrains: ``brand/verify-brand-claims-request.json``,
        # ``core/performance-feedback.json``,
        # ``core/requirements/image-asset-requirements.json``,
        # ``governance/accepted-governance-agents.json``,
        # ``media-buy/product-refinement.json``,
        # ``registries/v1-canonical-mapping.json``, plus
        # ``error-details/governance-agent-not-accepted.json`` chained behind the fourth
        # of them.  The seventh is the OTHER shape: ``core/delivery-metric-aggregate.json``
        # emits because a ``not`` beside a conjoined type is now a ``NotValue`` on the
        # value's own annotated type.  The per-row loop grades all 59 and reported
        # nothing new.
        "brand/verify-brand-claims-request.json",
        "core/delivery-metric-aggregate.json",
        "core/performance-feedback.json",
        "core/requirements/image-asset-requirements.json",
        "error-details/governance-agent-not-accepted.json",
        "governance/accepted-governance-agents.json",
        "media-buy/product-refinement.json",
        "registries/v1-canonical-mapping.json",
        # **TWO more at ``adcp-client-python-10l.20``, out of six that joined and four
        # that the exclusion above takes** (§14 step 9).  Six union roots whose own
        # siblings now compile onto the base emit, each having refused as
        # ``union.ROOT_CONJUNCTS`` -- "there is no pointer to the conjunction for a
        # branch class to name" -- and §8's pairing rule is what answers it, so their
        # branch classes reach this population by the mechanism the four below reached
        # it by.  Four of the six contribute no ROW, because every one of their branches
        # states a ``not`` over a ``required`` and so refuses a non-object on its own:
        # they are in ``ALREADY_AN_OBJECT_ITSELF``, which says so and is measured there.
        # ``core/brand-response-authorization-result.json`` contributes one of its two
        # branches for that same reason, and ``brand/verify-brand-claim-request.json``
        # both.  The per-row loop grades all 40 and reported nothing new.
        "brand/verify-brand-claim-request.json",
        "core/brand-response-authorization-result.json",
        "core/activation-key.json",
        "core/reporting-write-destination.json",
        # Four more at 16052ffb0, and they are the four documents that left
        # ``STILL_REFUSED`` below: each refused on a ``$ref`` into a document that
        # now emits, so each one's two branch classes join this population.  The
        # per-row loop grades all 35 and reported nothing new.
        "core/account-ref.json",
        "core/committed-metric.json",
        "core/missing-metric.json",
        "core/performance-feedback-metric.json",
        # Third since `salesagent-j3k2l.20`: the document emits now that a
        # `definitions` section no longer refuses it, and it carries a class at a
        # node its own root constrains -- so it joins this population rather than
        # changing what the population means.
        "core/reporting-dataset-share-destination.json",
        # Three more since `salesagent-j3k2l.19`: a `uniqueItems` is lowered on the
        # class that holds the array, so these emit and each carries classes at
        # nodes its own root constrains.  `media-buy/acceptance-policy-requirement.json`
        # is the direct one -- it refused on `uniqueItems` at
        # `/oneOf/2/properties/criteria` -- and the other two chain off newly
        # emitted targets.  The POPULATION of this refusal is what grew; what it
        # means is unchanged, and the per-row loop below still grades every one.
        "core/canonical-account-ref.json",
        "core/canonical-reporting-commitment.json",
        "media-buy/acceptance-policy-requirement.json",
    }
    for g in rows:
        bare = _node(bundle.read(BUNDLE, g.ref.document), g.ref.pointer.lstrip("#"))
        assert jsonschema.Draft7Validator(bare).is_valid("a string"), g.ref
        assert not jsonschema.Draft7Validator(schema_at(g.ref)).is_valid("a string"), g.ref
        with pytest.raises(Exception):  # noqa: B017 -- either half of the entry point may answer
            g.accept("a string")


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


def test_the_population_of_document_side_local_refs_is_not_empty() -> None:
    """The DENOMINATOR, which is the one thing the outcome pins cannot say.

    ``test_the_harness_result_is_counted_over_the_whole_population`` pins
    ``accepts:model_error`` at 0, and before this row that pin was green FOR FREE: **0
    graded pairs of the committed tree held a document-side local ``$ref`` at all**,
    because every document carrying one was refused by name
    (``codegen.lower.union``'s deleted guard measured it). A green mark over an empty
    population says nothing, so this names the population and asserts it is not empty.

    Counted as (pair, reference) sites and reported per document, so a shrink is
    readable rather than a number going down.
    """
    import collections
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from test_emit import graded

    def local_refs(node: object) -> list[str]:
        if isinstance(node, dict):
            found = [node["$ref"]] if isinstance(node.get("$ref"), str) else []
            return found + [r for v in node.values() for r in local_refs(v)]
        if isinstance(node, list):
            return [r for v in node for r in local_refs(v)]
        return []

    per_document: collections.Counter[str] = collections.Counter()
    for g in graded():
        root = _base._document(g.ref.document)
        for reference in local_refs(schema_at(g.ref)):
            if not reference.startswith("#"):
                continue
            per_document[g.ref.document] += 1
            # and it resolves, which is what the scope widening is for
            assert applied_schema(root, reference), (g.ref, reference)
    # The documents, by name, each with a non-empty set of local references -- and every
    # one of them is asserted to RESOLVE in the loop above, which is the obligation.
    # Counted once per (PAIR, reference) here, where ``tests/test_emit.py`` reads the
    # same references once per document: two denominators for one fact, and naming the
    # set says which rather than how many.
    #
    # **3 -> 21 AT ``adcp-client-python-10l.3``, AND THE POPULATION IS THE ROW'S
    # PRODUCT.**  Architecture §4 decides that a local ``$ref`` stays as written in the
    # document of record; the delegated resolver it replaced INLINED one, and the three
    # named below were only the documents whose chain is RECURSIVE and therefore had no
    # finite inlining.  So the scope widening this test is the denominator for now has
    # eighteen more documents under it, and every reference in all 21 resolves through
    # ``applied_schema`` above.
    assert set(per_document) == {
        # **One more at ``adcp-client-python-10l.55``**, and it is a document that
        # EMITS: ``core/creative-localization-readback.json`` chained onto
        # ``core/assets/asset-union.json``, whose ``$ref`` branch onto the UNION root
        # ``VASTAsset`` the branch row refused for not being a class.  It is one, the
        # gate reads ``compiler.TargetKind`` now, and the document's own
        # ``#/definitions/resolvedAssets`` reference reaches this loop and resolves
        # through the widened scope exactly as the rest do.
        "core/creative-localization-readback.json",
        # **Two more at ``adcp-client-python-10l.21``'s third instalment**, both §14 step
        # 9's first faithful row: a ``type`` word beside a NESTED combinator is in every
        # branch already (``union.nested``'s screen claims it), so these two emit and the
        # pairs that reach this loop are their own nodes.
        # ``brand/verify-brand-claims-request.json`` states ``#/definitions/claim_entry``
        # and ``content-standards/artifact.json`` ``#/$defs/asset_access`` -- each the
        # very node whose worded union was being refused -- and both resolve through the
        # widened scope exactly as the rest do.
        "brand/verify-brand-claims-request.json",
        "content-standards/artifact.json",
        # **Three more at ``adcp-client-python-10l.21``'s second instalment**, and all
        # three are §5(b)'s ``uniqueItems`` row becoming a declared WIDENING rather than
        # a verdict.  ``core/daast-tracker-constraints.json`` and
        # ``core/vast-tracker-constraints.json`` are the pair whose ``*_versions``
        # section entry carried that keyword, and each states four local ``$ref``\ s
        # into its own ``definitions``; ``governance/policy-entry.json`` emits behind
        # ``media-buy/acceptance-policy-profile.json`` for the same reason.  Every
        # reference in all three resolves through the widened scope, which the loop
        # above is what asserts.
        "core/daast-tracker-constraints.json",
        "core/vast-tracker-constraints.json",
        "governance/policy-entry.json",
        # **Two more at ``adcp-client-python-10l.20``**: both are union roots §14 step 9
        # unblocked, and both state a local ``$ref`` inside a branch -- so the pairs
        # that reach this loop are their branch classes, and the references resolve
        # through the widened scope exactly as the eighteen below do.
        "brand/get-brand-identity-response.json",
        "brand/search-brands-response.json",
        "aao/agent-publishers.json",
        "core/bidding-policy-capability.json",
        "core/placement-presentation.json",
        "core/reporting-adjustment-receipt.json",
        "core/reporting-canonicalization-contract.json",
        "core/reporting-coverage.json",
        "core/reporting-dataset-share-destination.json",
        "core/reporting-delivery-config-state.json",
        "core/reporting-delivery-method.json",
        "core/reporting-delivery-offering.json",
        "core/reporting-reliability-statistics.json",
        "core/reporting-report-definition.json",
        "core/reporting-resource.json",
        "core/reporting-schedule.json",
        "core/reporting-status-issue.json",
        "core/requirements/catalog-field-binding.json",
        "core/response-payload-jws-envelope.json",
        "core/verification-token-claims.json",
        # The third of the original three joined at ``salesagent-j3k2l.41``: its
        # bounded-value definitions reference each other locally, and the array and
        # mapping branches that carry their own bound now have a named type to carry it
        # on.
        "governance/reported-outcome-error.json",
        "media-buy/change-term-constraints.json",
        "media-buy/get-reporting-status-request.json",
    }, dict(per_document)
    assert all(per_document.values()), dict(per_document)
