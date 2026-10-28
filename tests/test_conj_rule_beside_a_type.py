"""§2's "Where a rule hangs", read at CONJ: one conjunct the TYPE, another the RULE.

``adcp-client-python-10l.21``.  §5's ``$ref`` row at CONJ says that where the target is
not a class -- a scalar, an enum, a container or a union root -- "the target is this
node's own TYPE, and the other conjuncts and the ``allOf``'s siblings constrain it, which
is §2's intersection at a node that declares no fields of its own".  ``lower_composition``
implemented the type half and refused the constraining half, with a DEFERRAL whose own
sentence said what was missing: "section 2 hangs a rule with no class above the value off
the value's own annotated type, which is ir.TypeRef.validators -- the slot and its three
kinds exist and the array and scalar rows write them, and what is unwritten is the reading
at CONJ".

**The reading is now written, and it decides nothing itself.**  ``lower.rules`` is asked
BOTH of §2's questions -- ``compiler.rules_at`` for the class half, ``rules.on_a_value``
for the value half -- and the answer is which of them came back non-empty.  That is the
rules module's own rule ("one reader decides which of the two a document's statement
reaches and the two cannot both claim it"), and it is why there is no second reading of a
``not`` in ``compiler.py``.

**Three shapes of ``not``, which §5's ``not`` row already separates**, and all three are
graded here against the bundle's own nodes:

======================  ===============================  ==================================
``not`` over           §5's ``not`` row says            what this position does
======================  ===============================  ==================================
a ``const`` / ``enum``  a ``NotValue`` after-validator   writes it onto the type
``required``            a ``ForbiddenGroups`` *rule*     refuses: there is no class
any other shape         "nothing on the model"           emits, the schema half answers
======================  ===============================  ==================================

The middle row is the one that still refuses and it is reported as ITSELF rather than
folded into the old deferral: the rule has somewhere to live -- the value's annotated type
-- and no kind to live AS, because the three kinds §2 names there (``AtLeastOne``,
``NotValue``, ``Distinct``) are each about a VALUE and this statement is about which KEYS
an instance supplied.  Whether §2 gains a fourth, value-level presence kind is a decision
for the owner, so the refusal names the gap instead of declaring a widening for it --
which is §9's first mistake and what ``7044c5ab`` withdrew for ``uniqueItems``.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, NamedTuple

import jsonschema

from adcp.types._runtime import NotValue
from compiled import compiled
from codegen import bundle, compiler, emit, ir
from codegen.keywords import Position
from codegen.lower import rules as lower_rules
from codegen.refusal import Refusal
from codegen.schema import parse as schema_parse

from nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


class Site(NamedTuple):
    """One call of §5's ``$ref`` row at CONJ, with everything the row read."""

    at: str
    symbol: str
    #: More than one conjunct resolved to a non-class: §2's intersection of two decided
    #: types, which the row refuses before it reads anything else.
    targets: int
    #: The node declares fields or composes bases, which is §14 step 10's own shape and
    #: refuses before the rule reading too.
    a_class_as_well: bool
    #: The rule keywords every contributing conjunct states, sorted.
    beside: tuple[str, ...]
    validators: tuple[Any, ...]
    refusal: Refusal | None


@functools.cache
def _reaching() -> tuple[Site, ...]:
    """Every node of the portable population that reaches §5's ``$ref``-row-at-CONJ.

    Recorded AT THE CALL rather than selected by a second reading of the bundle: the row
    holds only where the target resolves to something with no :class:`compiler.Shape`,
    which is a fact about the RUN and not about any one document's text.

    **``emit.emit`` and not ``compiled``, and the cache is this function's own.**  A spy
    observes the COMPILE, and ``tests/compiled.py``'s key covers the bundle, the
    population and every ``.py`` under ``codegen/`` -- not a monkeypatch -- so a warm
    entry serves a run this spy never saw and the site list comes back EMPTY.  Measured at
    ``adcp-client-python-10l.59``: cold, 37 sites and green; warm, 0 sites, and the
    assertions over them held vacuously until ``nodeset.claimed`` caught the empty set.
    That is the same carve-out ``compiled``'s own docstring states for a caller that
    MUTATES the result -- "call ``emit.emit`` directly and say why" -- read for a caller
    that instruments it, and the price is one uncached whole-bundle compile for this file
    (``adcp-client-python-10l.49``'s population, named there).  ``functools.cache`` keeps
    it to one per process, which is why the return is a tuple.
    """
    seen: list[Site] = []
    original = compiler._the_conjuncts_own_type  # noqa: SLF001 -- the test is the caller

    def spy(
        node: Any,
        conjoined: Any,
        *,
        fields_declared: Any,
        bases: Any,
        rule_nodes: Any,
    ) -> Any:
        answer = original(
            node,
            conjoined,
            fields_declared=fields_declared,
            bases=bases,
            rule_nodes=rule_nodes,
        )
        seen.append(
            Site(
                at=conjoined[0][0],
                # The row is handed the TARGET and not its symbol alone, because the
                # refusal for a node declaring fields names WHICH of §5's non-class
                # targets this one is (``adcp-client-python-10l.59``).  The site is still
                # identified by the symbol, which is what the pointer pairs with.
                symbol=conjoined[0][1].symbol,
                targets=len(conjoined),
                a_class_as_well=bool(fields_declared or bases),
                beside=tuple(sorted({k for one in rule_nodes for k in one})),
                validators=() if isinstance(answer, Refusal) else answer.type.validators,
                refusal=answer if isinstance(answer, Refusal) else None,
            )
        )
        return answer

    compiler._the_conjuncts_own_type = spy  # noqa: SLF001
    try:
        # ``emit.emit`` and NOT ``compiled``: this installs a SPY, so the walk has to
        # RUN.  ``tests/compiled.py``'s key is a digest of ``codegen/``'s source and
        # cannot see a runtime patch, so a cache hit unpickles a result the spy never
        # saw and ``seen`` comes back empty -- green cold, red warm, with nothing
        # changed between the runs.  Both this lane and the orchestrator reached this
        # same line independently; enforced now by
        # ``tests/test_no_cached_compile_under_a_perturbation.py``.
        emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    finally:
        compiler._the_conjuncts_own_type = original  # noqa: SLF001
    return tuple(seen)


def test_the_three_shapes_of_not_beside_a_conjoined_type_partition_the_population() -> None:
    """Every rule-beside-a-type site accounted for by exactly one of §5's three answers.

    The partition is the whole claim: a site that fell through all three would be a
    keyword lowered by nobody, and a site counted twice would mean two readings of one
    ``not``.  The sites are DERIVED from the run, so a document arriving or leaving the
    population moves the parts and not the property.

    **The population is the sites this ARM reaches**, which is narrower than every call of
    the row: a node with two non-class targets, and a node that is a class as well, both
    refuse on an earlier screen and their conjuncts are never read for a rule.  Those two
    are named parts of the outer partition rather than a filter, so a site moving between
    arms reddens.

    Measured at ``14cef36`` over the 1,054 portable documents: 30 calls, of which 25 state
    one target and no fields -- 16 with no rule beside the type and **9 with one, every one
    a ``not``**, splitting 6 / 2 / 1 across §5's three answers.

    **RE-MEASURED AT ``adcp-client-python-10l.55``: 37 calls, 32 with one target and no
    fields -- 21 with no rule and 11 with one, splitting 7 / 2 / 2.**  The row that moved
    it emits ``core/assets/asset-union.json``, so every node whose ``$ref`` conjunct
    resolves to that UNION root reaches this arm for the first time.

    **AND AT ``adcp-client-python-10l.59``: 35 calls, and ``two_non_class_targets`` is
    EMPTY.**  The two that filled it -- ``core/targeting.json`` and
    ``core/targeting-input.json``, each composing two roots that state ``if``/``then`` and
    nothing else -- take §2's intersection over DECLARATIONS instead: a target declaring
    only rule sources contributes a RULE to the composing node and never reaches this row
    (``compiler._a_rule_the_target_states``).  The other two parts are unmoved at 3 and
    32, and so is the 11 / 7 / 2 / 2 split below, which is why that part emptying is the
    whole of the change here.  Ten of the eleven
    rules are still a ``not``; the eleventh is the first CONDITIONAL at this position --
    ``core/localized-creative-asset.json`` at ``/allOf/0``, whose other conjunct is an
    ``if``/``then`` -- and §5's ``then`` cell decides it by name: "its ``properties`` ->
    nothing on the model; the schema half narrows the value."  That ``then`` states
    ``properties`` and nothing else, so it is the ``nothing_on_the_model`` part below,
    beside the one ``not`` that was already there, and the cell's ``rendered=False`` is
    why §8 compares no fact at the pointer.
    """
    sites = _reaching()
    every = claimed("calls of section 5's $ref row at CONJ", {(s.at, s.symbol) for s in sites})
    partitions(
        every,
        two_non_class_targets={(s.at, s.symbol) for s in sites if s.targets > 1},
        a_class_as_well={
            (s.at, s.symbol) for s in sites if s.targets == 1 and s.a_class_as_well
        },
        the_nodes_own_type={
            (s.at, s.symbol) for s in sites if s.targets == 1 and not s.a_class_as_well
        },
    )
    reaches = [s for s in sites if s.targets == 1 and not s.a_class_as_well]
    with_a_rule = claimed(
        "sites stating a rule beside the conjoined type",
        {(s.at, s.symbol) for s in reaches if s.beside},
    )
    # Two rule shapes reach this position, and ``ON_A_VALUE`` is still the one keyword
    # that can land ON THE VALUE: a ``not``, which that constant names and which the
    # ``a_notvalue_on_the_type`` part below is the population of.
    #
    # **An ``if``/``then`` joined at ``adcp-client-python-10l.55``**
    # (``core/localized-creative-asset.json`` at ``/allOf/0``, the first conditional this
    # arm has seen) and it reaches the OTHER part: §5's ``then`` cell says "its
    # ``properties`` -> nothing on the model; the schema half narrows the value", this
    # ``then`` states ``properties`` and nothing else, so the model carries nothing and
    # the document's own ``strict_validate`` is what enforces the conditional.  That is
    # the same answer §5's ``not`` row's last clause gives, which is why the two share a
    # part rather than needing a fourth.
    assert {s.beside for s in reaches if s.beside} == {("not",), ("if", "then")}, sorted(
        {s.beside for s in reaches if s.beside}
    )
    assert lower_rules.ON_A_VALUE == frozenset({"not"}), lower_rules.ON_A_VALUE

    wrote = {(s.at, s.symbol) for s in reaches if s.beside and s.validators}
    refused = {(s.at, s.symbol) for s in reaches if s.beside and s.refusal is not None}
    carried = {
        (s.at, s.symbol)
        for s in reaches
        if s.beside and not s.validators and s.refusal is None
    }
    partitions(
        with_a_rule,
        a_notvalue_on_the_type=wrote,
        no_kind_for_a_presence_rule=refused,
        nothing_on_the_model=carried,
    )
    # Each part named, so a part that emptied reddens with the shape named rather than
    # the partition silently holding over two of three.
    assert all(
        isinstance(v, NotValue) for s in reaches if s.beside for v in s.validators
    ), [s for s in reaches if s.beside]
    assert wrote, "no site writes a NotValue, so §2's second half is ungraded here"
    assert refused, "no site refuses, so the clause below holds vacuously"
    assert carried, "no site carries nothing, so §5's last `not` clause is ungraded here"


def test_the_two_halves_of_section_2_are_one_readers_answer() -> None:
    """``lower.rules`` answers both of §2's questions and they never both answer.

    This is the property that keeps the three-way split above from being a second copy of
    §5's ``not`` row inside ``compiler.py``: for each of the three declaration shapes, at
    most one of ``rules.lower_declaration`` (the class half) and ``rules.on_a_value`` (the
    value half) returns anything, so the arm that fires is a consequence of the reading
    rather than a choice at the site.
    """
    shapes: dict[str, dict[str, Any]] = {
        "a const": {"not": {"const": "x"}},
        "an enum": {"not": {"enum": ["x", "y"]}},
        "required": {"not": {"required": ["p"]}},
        "another shape": {
            "not": {"properties": {"t": {"properties": {"k": {"enum": ["a"]}}}}, "required": ["t"]}
        },
    }
    claimed("not shapes", set(shapes))
    on_a_class: set[str] = set()
    on_a_value: set[str] = set()
    on_neither: set[str] = set()
    for name, declaration in shapes.items():
        klass = lower_rules.lower_declaration(declaration, Position.CONJ).rules
        value = lower_rules.on_a_value(declaration)
        assert not (klass and value), (name, klass, value)
        (on_a_class if klass else on_a_value if value else on_neither).add(name)
    partitions(
        set(shapes),
        a_class_rule=on_a_class,
        a_value_rule=on_a_value,
        neither=on_neither,
    )


def test_a_presence_rule_beside_a_conjoined_type_refuses_and_names_the_gap() -> None:
    """The middle row, by document and pointer, with the sentence a reader needs.

    ``core/canonical-product.json`` and ``core/product.json`` state
    ``publisher_properties`` items as ``allOf: [{$ref: publisher-property-selector},
    {not: {required: ["publisher_domains"]}}]``.  The target is a union ROOT, so §5's row
    makes it the node's own type; the ``not`` is over ``required``, so §5's ``not`` row
    decides ``ForbiddenGroups`` -- a rule on a class, and the node has none.

    The refusal is a DEFERRAL and names the missing KIND rather than the missing row,
    because what obstructs it is a decision about §2's own list of value-rule kinds.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    named = claimed(
        "documents refused for a presence rule beside a conjoined type",
        {
            document
            for document, row in out.refusals.items()
            # PRIMARY only: a chained refusal QUOTES its target's whole sentence, so the
            # substring reaches every document behind these two.
            if row["kind"] != "chained" and "value-level presence kind" in row["detail"]
        },
    )
    assert named == {"core/canonical-product.json", "core/product.json"}, sorted(named)
    for document in sorted(named):
        row = out.refusals[document]
        assert row["keyword"] == "allOf", row
        assert row["resolved"] == "deferred", row
        assert row["pointer"].endswith("/properties/publisher_properties/items/allOf/0"), row
        assert "ForbiddenGroups" in row["detail"], row
        # The document's own statement, so the sentence is about this node and not a
        # neighbour's.
        node = bundle.node_at(
            bundle.read(BUNDLE, document), row["pointer"].rsplit("/allOf/", 1)[0]
        )
        assert node["allOf"][1] == {"not": {"required": ["publisher_domains"]}}, node["allOf"]


def test_two_conjuncts_stating_one_rule_keyword_refuse_rather_than_drop_one() -> None:
    """The arm with no population, exercised on a constructed node.

    §2 forbids an undeclared drop, so reading either of two ``not``s and ignoring the
    other is not available -- the merge is §2's intersection of two rule statements and no
    row writes it.  0 sites over the portable population, which is why this is graded on a
    document built here rather than selected from the bundle.
    """
    node = schema_parse.parse(
        {
            "allOf": [
                {"$ref": "https://adcontextprotocol.org/schemas/3.2.4/enums/media-type.json"},
                {"not": {"const": "video"}},
                {"not": {"const": "audio"}},
            ]
        },
        pointer="/properties/kind",
        position=Position.PROP,
        source=schema_parse.Source(document="probe.json"),
    )
    # The row reads the TARGET and not a symbol (``adcp-client-python-10l.59``), so the
    # probe builds the one a ``$ref`` to an enumeration resolves to: an ANNOTATION, which
    # is the kind that makes §5's row give the node the target as its own TYPE.
    target = compiler.Target(
        "",
        "MediaType",
        document="enums/media-type.json",
        kind=compiler.TargetKind.ANNOTATION,
    )
    answer = compiler._the_conjuncts_own_type(  # noqa: SLF001 -- the arm's only caller
        node,
        [("/properties/kind/allOf/0", target)],
        fields_declared=(),
        bases=(),
        rule_nodes=[{"not": {"const": "video"}}, {"not": {"const": "audio"}}],
    )
    assert isinstance(answer, Refusal), answer
    assert (answer.keyword, answer.resolved) == ("allOf", "deferred"), answer
    assert "two conjuncts state 'not'" in answer.detail, answer.detail
    # And ONE ``not`` beside the same target is decided, so the refusal above is about the
    # second statement and not about the position.
    one = compiler._the_conjuncts_own_type(  # noqa: SLF001
        node,
        [("/properties/kind/allOf/0", target)],
        fields_declared=(),
        bases=(),
        rule_nodes=[{"not": {"const": "video"}}],
    )
    assert isinstance(one, compiler.Decided), one
    assert one.type == ir.TypeRef("MediaType", local=True, validators=(NotValue(("video",)),)), one


def test_the_document_decides_both_payloads_at_the_notvalue_site() -> None:
    """D4's direction at the new position: the model refuses exactly what the document does.

    ``core/delivery-metric-aggregate.json``'s ``metric_id`` is the CONJ ``NotValue`` site
    ``tests/test_emit.py``'s ``VALUE_RULE_CARRIERS`` names, and the two payloads are
    graded against ``Draft7Validator`` FIRST -- so an admitted payload the model refuses
    is a narrowing and reddens here, which is the failure a value rule can cause and the
    one §2 forbids.
    """
    document = "core/delivery-metric-aggregate.json"
    record = bundle.record(BUNDLE, document)
    assert not isinstance(record, Refusal), record
    validator = jsonschema.Draft7Validator(record)
    admitted = {"scope": "standard", "metric_id": "impressions", "value": 1.0}
    refused = {"scope": "standard", "metric_id": "viewability", "value": 1.0}
    assert list(validator.iter_errors(admitted)) == [], list(validator.iter_errors(admitted))
    assert list(validator.iter_errors(refused)) != []
    # The document's own ``not``, at the pointer this row reads it from, so the pair is
    # not two payloads that happen to differ.
    at = record["oneOf"][0]["properties"]["metric_id"]["allOf"]
    assert at[1]["not"]["enum"][0] == "viewability", json.dumps(at)[:200]
