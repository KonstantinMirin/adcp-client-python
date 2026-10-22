"""A node's schema is the node AS THE DOCUMENT APPLIES IT, not the node read alone.

`salesagent-j3k2l.24`.  A separate module from ``tests/test_emit.py`` because this
grades one mechanism in both halves -- what the emitter will lower, and what the
runtime says a class's schema IS -- and because ``test_emit`` holds the metric
constants that are re-measured once per epic.

**The defect.**  draft-07 applies a root's assertions and its combinator branch's to
the SAME instance, so ``{"type": "object", "oneOf": [{"properties": {...}}]}`` admits
only objects and the branch at ``/oneOf/0`` does not restate it.  Read in ISOLATION
that branch admits a string, so ``compiler.lower_object`` refused to build a class
for it -- 10 documents of the 3.2 bundle, with 34 more chaining off them through a
``$ref`` -- and ``_base.schema_at`` returned that same isolated node as the schema a
branch class would then be graded against.  Fixing only the first turned one defect
into four reds: ``core/activation-key.json``'s two branch pairs reported
``accepts:model_refused_valid`` and ``model_adds_a_fact`` at ``/type``.  So the rule
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

from adcp.types._base import AdCPBaseModel, applied_schema, schema_at
from codegen import bundle, emit
from codegen.refusal import Refusal

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

DRAFT = "http://json-schema.org/draft-07/schema#"

#: The three documents the fix moved from refused to emitted, which is its whole
#: effect on the committed tree: two were refused at a branch their own root
#: constrains to an object, and ``core/deployment.json`` chained off the first through
#: a ``$ref``.
NOW_EMITTED = (
    "core/activation-key.json",
    "core/deployment.json",
    "core/reporting-write-destination.json",
)

#: The other 8 of the 10, with the keyword and pointer each one reports NOW.  Every
#: one is a later D2/D6 row -- a ``$ref`` whose target refuses, a ``maxLength`` beside
#: a ``format: uri``, a ``uniqueItems`` -- so this is the residue of OTHER steps, and
#: pinning it here means a step that closes one of them shows up as this going stale
#: rather than as a silent change of population.
STILL_REFUSED = {
    "core/account-ref.json": ("$ref", "/oneOf/1/properties/brand"),
    "core/canonical-account-ref.json": ("$ref", "/anyOf/1/properties/brand"),
    "core/canonical-reporting-commitment.json": ("$ref", "/oneOf/1/properties/vendor"),
    "core/committed-metric.json": ("$ref", "/oneOf/1/properties/vendor"),
    "core/missing-metric.json": ("$ref", "/oneOf/1/properties/vendor"),
    "core/performance-feedback-metric.json": ("$ref", "/oneOf/1/properties/vendor"),
    "error-details/governance-agent-not-accepted.json": (
        "maxLength",
        "/oneOf/0/properties/attempted_agent_origin",
    ),
    "media-buy/acceptance-policy-requirement.json": (
        "uniqueItems",
        "/oneOf/2/properties/criteria",
    ),
}


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


def test_the_two_populations_are_counted_over_the_whole_bundle() -> None:
    """The denominators, because the rule is a PARTITION of one population and a
    verdict over a population nobody counted is a verdict over however many nodes
    there turned out to be.

    Both halves are required non-empty by being pinned to a non-zero number: the
    first alone would pass for a rule that constrains everything, the second alone for
    a rule that constrains nothing.

    The second pair of numbers is the subset the DEFECT was found on -- a node
    declaring a non-empty ``properties``, which is the only shape a class can be
    declared at, so it is the subset the emitter's answer turns on.
    """
    constrained, loose = census()
    assert sum(len(p) for p in constrained.values()) == 2040
    assert len(constrained) == 354
    assert sum(len(p) for p in loose.values()) == 8000
    assert len(loose) == 727

    def with_properties(half: dict[str, frozenset[str]]) -> tuple[int, int]:
        per = {
            document: [
                p for p in pointers if _declares_properties(bundle.read(BUNDLE, document), p)
            ]
            for document, pointers in half.items()
        }
        return sum(len(v) for v in per.values()), sum(1 for v in per.values() if v)

    assert with_properties(constrained) == (556, 151)
    assert with_properties(loose) == (833, 206)


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
    to the network (``bundle.resolved``'s docstring measures it at 4.4 s per
    validation, on a path it deprecates), and resolving all 1,054 documents to avoid
    that costs more than the claim is worth -- the same reason ``bundle.resolved``
    exists for the emitted population only.  The structural half below covers all
    2,040.

    A string is the probe because the fact conjoined at every CONSTRAINED node is
    ``type: "object"``, which
    :func:`test_the_only_fact_conjoined_at_a_constrained_node_is_its_object_type` is
    what establishes.
    """
    constrained, loose = census()
    checked = skipped = admitted_bare = 0
    for document, pointers in constrained.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare = _node(doc, pointer)
            if "$ref" in bare or bundle.references(bare):
                skipped += 1
                continue
            applied = applied_schema(doc, pointer)
            assert not jsonschema.Draft7Validator(applied).is_valid("a string"), (
                document,
                pointer,
            )
            admitted_bare += jsonschema.Draft7Validator(bare).is_valid("a string")
            checked += 1
    assert (checked, skipped) == (1541, 499), (checked, skipped)
    assert admitted_bare == 1215, admitted_bare

    untouched = 0
    conjoined: dict[str, int] = {}
    for document, pointers in loose.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare, applied = _node(doc, pointer), applied_schema(doc, pointer)
            assert applied.get("type") != "object", (document, pointer)
            if applied is bare:
                untouched += 1
            else:
                conjoined[repr(applied["type"])] = conjoined.get(repr(applied["type"]), 0) + 1
    assert untouched == 7987, untouched
    assert conjoined == {"'string'": 5, "'array'": 8}, conjoined


def test_the_only_fact_conjoined_at_a_constrained_node_is_its_object_type() -> None:
    """Every fact ``applied_schema`` conjoins at a CONSTRAINED node is
    ``type: "object"``, it conjoins no other keyword, and it changes no fact the node
    already states.

    The structural half of the check above, over all 2,040 rather than the 1,541 a
    ``jsonschema`` call can reach offline -- and the reason the probe there may be a
    string.  ``bundle.constrained_to_object`` asks for the literal ``"object"``, so an
    enclosing ``["object", "null"]`` is not one and lands in the loose half; if a
    document ever states a different enclosing type this reports it rather than
    letting the string probe go quietly vacuous.
    """
    constrained, _ = census()
    added: dict[str, set[str]] = {}
    for document, pointers in constrained.items():
        doc = bundle.read(BUNDLE, document)
        for pointer in pointers:
            bare, applied = _node(doc, pointer), applied_schema(doc, pointer)
            for key in set(applied) - set(bare):
                added.setdefault(key, set()).add(repr(applied[key]))
            assert {k: v for k, v in applied.items() if k in bare} == bare, (document, pointer)
    assert added == {"type": {"'object'"}}, added


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

    rows = [
        g
        for g in test_emit.graded()
        if isinstance(g.model, type)
        and issubclass(g.model, AdCPBaseModel)
        and g.ref.pointer.lstrip("#")
        in bundle.constrained_to_object(bundle.read(BUNDLE, g.ref.document))
    ]
    assert len(rows) == 6, [g.ref for g in rows]
    assert {g.ref.document for g in rows} == {
        "core/activation-key.json",
        "core/reporting-write-destination.json",
        # Third since `salesagent-j3k2l.20`: the document emits now that a
        # `definitions` section no longer refuses it, and it carries a class at a
        # node its own root constrains -- so it joins this population rather than
        # changing what the population means.
        "core/reporting-dataset-share-destination.json",
    }
    for g in rows:
        bare = _node(bundle.read(BUNDLE, g.ref.document), g.ref.pointer.lstrip("#"))
        assert jsonschema.Draft7Validator(bare).is_valid("a string"), g.ref
        assert not jsonschema.Draft7Validator(schema_at(g.ref)).is_valid("a string"), g.ref
        with pytest.raises(Exception):  # noqa: B017 -- either half of the entry point may answer
            g.accept("a string")


def test_three_of_the_ten_emit_and_the_other_eight_refuse_on_another_rows_keyword() -> None:
    """The outcome, with the honest residue.

    10 documents were refused at a node their own root constrains to an object.
    **2 of them now emit, 1 more emits because it chained off one of those two, and 8
    still refuse** -- every one on a keyword of a later row, measured here by name.
    "Every document whose root constrains the instance to an object emits" is
    therefore true of THIS refusal and not of those 8 documents, and that distinction
    is the content of this assertion.
    """
    out = emit.emit(BUNDLE, sorted(set(NOW_EMITTED) | set(STILL_REFUSED)))
    assert set(NOW_EMITTED) <= set(out.emitted), sorted(set(NOW_EMITTED) - set(out.emitted))
    for document, (keyword, pointer) in STILL_REFUSED.items():
        row = out.refusals[document]
        assert (row["keyword"], row["pointer"]) == (keyword, pointer), (document, row)


def test_no_document_in_the_bundle_reaches_the_refusal_any_more() -> None:
    """The refusal's population is 0, which is why the perturbations below exist.

    Stated as a measurement and not as a claim that the refusal is dead code: it is
    the designed outcome for a node nothing constrains, the probes under it are what
    reach it, and a bundle that gains such a document gains it here.
    """
    out = emit.emit(BUNDLE, bundle.portable(BUNDLE))
    assert len(out.emitted) + len(out.refusals) == 1054
    assert len(out.emitted) == 435
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


def _union(root_type: str | None) -> dict:
    """A union root whose branches declare no ``type`` of their own."""
    doc: dict = {
        "title": "Probe",
        "oneOf": [
            {"properties": {"kind": {"const": "a"}, "a": {"type": "string"}}, "required": ["kind"]},
            {"properties": {"kind": {"const": "b"}, "b": {"type": "string"}}, "required": ["kind"]},
        ],
    }
    if root_type is not None:
        doc["type"] = root_type
    return doc


def test_a_typeless_branch_emits_only_while_its_root_constrains_the_instance(tmp_path) -> None:
    """The one distinction, run both ways on two documents that differ in one key.

    The ``jsonschema`` lines are what make this a measurement rather than a
    restatement, and they are asked of the BRANCH, because the branch node is the
    schema a branch class is paired with.  With the root's ``type`` the branch refuses
    a string; without it the branch admits one, and a class there would be narrower
    than the schema it names.

    Measured aside, and the reason the document is not the unit: the typeless
    DOCUMENT refuses a string too, but on ``oneOf`` -- ``properties`` and ``required``
    are both vacuous for a non-object, so every branch matches it and none matches
    uniquely.  A document-level probe would therefore pass for both arms and grade
    nothing.
    """
    with_type, without = _union("object"), _union(None)
    assert jsonschema.Draft7Validator(applied_schema(without, "/oneOf/0")).is_valid("a string")
    assert not jsonschema.Draft7Validator(applied_schema(with_type, "/oneOf/0")).is_valid(
        "a string"
    )
    assert not jsonschema.Draft7Validator(with_type).is_valid("a string")
    assert not jsonschema.Draft7Validator(without).is_valid("a string")  # on oneOf, not on type

    out = emit.emit(_write(tmp_path / "a", {"core/probe.json": with_type}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert "core/probe.json" in out.emitted

    out = emit.emit(_write(tmp_path / "b", {"core/probe.json": without}), ["core/probe.json"])
    assert "core/probe.json" not in out.emitted
    row = out.refusals["core/probe.json"]
    assert (row["keyword"], row["pointer"]) == ("type", "/oneOf/0"), row
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

    The keyword asserted is the one that actually fires, and it is not ``type``: a
    typeless node carrying ``properties`` never reaches ``lower_object``, because
    ``emit._decide``'s typeless arm screens the keyword first.  So the emitter refuses
    this node twice over, and asserting ``type`` would be asserting a code path this
    document does not take.
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
    assert (row["keyword"], row["pointer"]) == ("properties", "/oneOf/0/properties/inner"), row


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
    with pytest.raises(Refusal) as caught:
        emit.lower_document("core/probe.json", doc)
    assert (caught.value.keyword, caught.value.pointer) == ("type", "/oneOf/0"), caught.value


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

    at = [g.ref for g in test_emit.graded() if f"/{keyword}" in g.ref.pointer]
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

    through_a_conditional = sum(
        1
        for document in bundle.portable(BUNDLE)
        for p in bundle.constrained_to_object(bundle.read(BUNDLE, document))
        if any(seg in ("if", "not", "then", "else") for seg in p.split("/"))
    )
    assert through_a_conditional == 639, through_a_conditional
