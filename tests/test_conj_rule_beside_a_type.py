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
``required``            a ``ForbiddenGroups`` *rule*     writes it onto the type
any other shape         "nothing on the model"           emits, the schema half answers
======================  ===============================  ==================================

**The middle row REFUSED until §2's clause of 2026-10-28, and the fix was a sentence and
not a kind** (``adcp-client-python-10l.63``).  The refusal said the rule had somewhere to
live -- the value's annotated type -- and no kind to live AS, because the three kinds §2
named there (``AtLeastOne``, ``NotValue``, ``Distinct``) are each about a VALUE and this
statement is about which KEYS an instance supplied.  §2 now answers it directly: "**a
value-level rule may state which KEYS the value supplied, and the three kinds above are
not the limit.**  The distinction §2 draws is about where a rule HANGS, not about what it
may read ... at a position with no class above it, the value *is* the object, so
``ForbiddenGroups``, ``RequiredGroups`` and ``PresenceGroups`` are admissible there as
``_runtime.ValueRule``s -- 'a callable on the value, and all it is' -- without a new
kind."  So no widening was declared and none was needed, which is what ``7044c5ab``
withdrew for ``uniqueItems`` and what §9's first mistake is.

``adcp.types._runtime.TheValueIsTheObject`` is that clause and nothing more -- one
``__call__`` over the kind's own ``errors`` -- and ``lower.rules.as_the_object`` is the
one reading of which of a class's rules the value may carry: ``isinstance(rule,
ValueRule)``, a property of the KIND, so neither ``compiler.py`` nor this file holds a
list of the three names.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Annotated, Any, NamedTuple

import jsonschema
import pytest
from pydantic import AfterValidator, TypeAdapter, ValidationError
from pydantic_core import PydanticCustomError

from adcp.types._base import AdCPBaseModel
from adcp.types._runtime import (
    ForbiddenGroups,
    NotValue,
    Presence,
    PresenceGroups,
    PropertyCount,
    RequiredGroups,
    ValueRule,
)
from compiled import compiled
from codegen import bundle, compiler, emit, ir, render
from codegen.keywords import Position
from codegen.lower import rules as lower_rules
from codegen.refusal import Refusal
from codegen.schema import parse as schema_parse

#: The ``$ref`` the constructed probes below name, and the :class:`compiler.Target` it
#: resolves to: an ANNOTATION, which is the kind that makes §5's ``$ref`` row at CONJ
#: give the node the target as its own TYPE rather than as a base.
_AN_ENUM = "https://adcontextprotocol.org/schemas/3.2.4/enums/media-type.json"
_AN_ANNOTATION = compiler.Target(
    "",
    "MediaType",
    document="enums/media-type.json",
    kind=compiler.TargetKind.ANNOTATION,
)

#: The conjunct NODE that named it.  The row is handed the parsed reference beside the
#: target (``adcp-client-python-10l.68``), because §5's distribution clause declares a
#: class per branch FROM it -- a node the arms below never reach, so the probes carry the
#: real one rather than a stand-in and the row's signature is exercised as the walk
#: builds it.
_THE_REFERENCE = schema_parse.parse(
    {"$ref": _AN_ENUM},
    pointer="/properties/kind/allOf/0",
    position=Position.CONJ,
    source=schema_parse.Source(document="probe.json"),
)

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
    #: §5's DISTRIBUTION clause answered: the target's branches, handed back for
    #: ``lower_composition`` to declare one subclass per branch over this node's class.
    #: ``None`` at every site the clause does not reach, which is every site that is not
    #: a union target beside declared fields -- so the row's THIRD outcome is observed
    #: here rather than inferred from a document emitting.
    distributed: tuple[str, ...] | None


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

    # **The spy FORWARDS the call rather than restating the signature**, which is the
    # correction ``adcp-client-python-10l.109`` makes.  It used to name each keyword
    # argument -- ``fields_declared``, ``bases``, ``rule_nodes`` -- and §5's ``$ref`` row
    # at CONJ then gained a fourth, ``facts`` (the ``allOf``'s own BOUNDS as siblings), so
    # every call of the row raised ``TypeError: spy() got an unexpected keyword argument
    # 'facts'`` and this file was red for a reason that is about the INSTRUMENT: the spy
    # was a second declaration of the row's parameter list, and a second declaration is
    # where two readings come apart (§3's own rule, read for a test).  ``**read`` is one
    # declaration, and what this function CLAIMS to know about the row is exactly the three
    # keys the :class:`Site` below reads out -- asserted present on every call, so a
    # renamed argument reddens here by name instead of being silently recorded as absent.
    def spy(node: Any, conjoined: Any, **read: Any) -> Any:
        answer = original(node, conjoined, **read)
        assert {"fields_declared", "bases", "rule_nodes"} <= set(read), sorted(read)
        fields_declared, bases, rule_nodes = (
            read["fields_declared"],
            read["bases"],
            read["rule_nodes"],
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
                validators=(
                    answer.type.validators if isinstance(answer, compiler.Decided) else ()
                ),
                refusal=answer if isinstance(answer, Refusal) else None,
                distributed=(
                    tuple(b.symbol for b in answer.of)
                    if isinstance(answer, compiler.TargetBranches)
                    else None
                ),
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

    **AND AT ``adcp-client-python-10l.63``: 40 calls, 36 with one target and no fields --
    25 with no rule and 11 with one, and the inner split moves 9 / 0 / 2.**  §2's clause
    of 2026-10-28 is the whole of that move: the two ``not``-over-``required`` sites now
    WRITE a ``ForbiddenGroups`` onto the value's own annotated type instead of refusing,
    so ``declined_for_want_of_a_callable`` is the part that is expected EMPTY -- named
    rather than dropped, and graded on a constructed node by
    :func:`test_a_rule_kind_that_is_no_callable_on_the_value_refuses_and_names_itself`,
    which is the same arrangement ``two_non_class_targets`` has.  ``a_class_as_well``
    grew 3 -> 4 on ``core/audience-evidence.json``, whose ``$ref`` conjunct now resolves
    to the ``AttestationSubject`` union root: that is ``adcp-client-python-10l.59``'s
    OPEN numbered request and not this row's, so the part grows and the property holds.

    **AND AT ``adcp-client-python-10l.109``, which is the first re-measurement this file
    has had since the spy went stale: 56 calls, 40 distinct sites, 32 with one target and
    no fields -- 20 with no rule and 12 with one, splitting 10 / 0 / 2.**  Nothing here was
    read between ``10l.63`` and this row, because ``compiler._the_conjuncts_own_type``
    gained a fourth keyword argument (``facts``, the ``allOf``'s own sibling bounds) and
    the spy restated its parameter list, so every call raised ``TypeError`` and the whole
    file was one of the seven failures the down gate was hiding.  Two parts moved and both
    are the SIBLING reading landing (``2cbe670c``):

    * ``a_class_as_well`` is 4 -> 8 and ALL EIGHT DISTRIBUTE, so ``refuses`` is now the
      part expected EMPTY -- named rather than dropped, which is the arrangement
      ``two_non_class_targets`` and ``declined_for_want_of_a_callable`` already have;
    * the rule shapes gained ``('contains',)`` and the kinds gained ``AtLeastOne``, each
      named below with the clause that admits it.
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
    # **§5's DISTRIBUTION clause, graded inside the ``a_class_as_well`` part**
    # (``adcp-client-python-10l.68``).  The clause of 53cb6100 gives that part a THIRD
    # outcome -- "a UNION root beside a node that DOES declare fields distributes" -- so
    # the part no longer means "refused", and its two halves are named here rather than
    # left to a document's emission to imply.  Measured over the 1,054 portable
    # documents: **4 sites, 2 distribute and 2 refuse**.  The two that distribute are the
    # nodes whose OWN declaration carries every field --
    # ``core/package-signal-targeting.json`` at ``/allOf/0`` and
    # ``core/product-filters.json`` at ``/properties/signal_targeting/items/allOf/0`` --
    # and the two that refuse carry theirs in a sibling conjunct, which is
    # ``compiler._distributes``' two screens.
    a_class = [s for s in sites if s.targets == 1 and s.a_class_as_well]
    partitions(
        claimed("sites at a node that is a class as well", {(s.at, s.symbol) for s in a_class}),
        distributes={(s.at, s.symbol) for s in a_class if s.distributed is not None},
        refuses={(s.at, s.symbol) for s in a_class if s.distributed is None},
    )
    assert all(
        s.refusal is not None for s in a_class if s.distributed is None
    ), [s.at for s in a_class if s.distributed is None and s.refusal is None]
    # Every distributing site hands back the TARGET's branches and at least two of them:
    # a union of one is not a union, and a distribution over no branch would be a class
    # with an empty ``_branch_models``.
    assert all(len(s.distributed) > 1 for s in a_class if s.distributed), [
        (s.at, s.distributed) for s in a_class if s.distributed is not None
    ]
    assert any(s.distributed for s in a_class), "no site distributes, so §5's clause is ungraded"

    reaches = [s for s in sites if s.targets == 1 and not s.a_class_as_well]
    with_a_rule = claimed(
        "sites stating a rule beside the conjoined type",
        {(s.at, s.symbol) for s in reaches if s.beside},
    )
    # Two rule shapes reach this position, and ``ON_A_VALUE`` is still the one keyword
    # whose VALUE half this module reads off the declaration: a ``not`` over a ``const``
    # or an ``enum``, which that constant names.  §2's clause of 2026-10-28 does not move
    # it, and that is the point of the clause: the other shape of ``not`` is lowered by
    # the CLASS half exactly as before and is then hung on the value because the KIND is
    # a callable on it, so ``ON_A_VALUE`` gains nothing and
    # ``lower.rules.as_the_object`` reads no keyword at all.
    #
    # **An ``if``/``then`` joined at ``adcp-client-python-10l.55``**
    # (``core/localized-creative-asset.json`` at ``/allOf/0``, the first conditional this
    # arm has seen) and it reaches the OTHER part: §5's ``then`` cell says "its
    # ``properties`` -> nothing on the model; the schema half narrows the value", this
    # ``then`` states ``properties`` and nothing else, so the model carries nothing and
    # the document's own ``strict_validate`` is what enforces the conditional.  That is
    # the same answer §5's ``not`` row's last clause gives, which is why the two share a
    # part rather than needing a fourth.
    #
    # **A ``contains`` JOINED at ``adcp-client-python-10l.109``, and it is this row's own
    # sentence arriving rather than a new reading.**  §5's ``$ref`` row at CONJ is read
    # WHOLE -- "the other conjuncts AND THE ``allOf``'s SIBLINGS constrain it" -- and
    # ``2cbe670c`` landed the siblings: the node's own ``contains`` joins the conjuncts'
    # rule sources and its own bounds ride in ``facts``.  One live site,
    # ``core/signal-coverage-forecast.json`` at
    # ``/properties/points/items/allOf/1/properties/dimensions``, which restates
    # ``dimensions`` as a bare ``contains`` over the base's ``$ref`` to
    # ``core/forecast-point-dimensions.json``; §5's ``contains`` row gives it an
    # ``AtLeastOne`` on the value's own annotated type "because no class has a kind for
    # it", which is the same half of §2 the ``not`` sites above take.
    #
    # **This assertion named two shapes and the third made the whole file a
    # ``TypeError``**, so the arrival was invisible: the spy restated the row's parameter
    # list and the row had gained ``facts``.  The pin is the READING now, and the shape it
    # gained is named with the clause that admits it.
    assert {s.beside for s in reaches if s.beside} == {
        ("not",),
        ("if", "then"),
        ("contains",),
    }, sorted({s.beside for s in reaches if s.beside})
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
        on_the_types_own_annotation=wrote,
        declined_for_want_of_a_callable=refused,
        nothing_on_the_model=carried,
    )
    # **BOTH kinds that reach the type's own annotation, named**, which is §2's clause of
    # 2026-10-28 graded over the bundle's own nodes: a statement about a VALUE takes
    # ``NotValue`` and a statement about which KEYS arrived takes ``ForbiddenGroups``, and
    # the clause is the reason the second one is here at all.  Each is asserted PRESENT
    # below, so a row that lost one reddens with the kind named rather than leaving the
    # partition green over the other.
    bound = {type(v).__name__ for s in reaches if s.beside for v in s.validators}
    # ``AtLeastOne`` is the third, and it is the ``contains`` shape's own kind -- the one
    # §5's ``contains`` row names and the one ``lower.rules.contains_predicate`` builds.
    # It joined with the sibling reading above (``adcp-client-python-10l.109``).
    assert bound == {"NotValue", "ForbiddenGroups", "AtLeastOne"}, sorted(bound)
    assert all(
        isinstance(v, ValueRule) for s in reaches if s.beside for v in s.validators
    ), [s for s in reaches if s.beside]
    assert wrote, "no site writes a value rule, so §2's second half is ungraded here"
    # EXPECTED EMPTY, and named rather than dropped: every rule this arm lowers is one of
    # the kinds §2's clause admits, so the decline is graded on a constructed node by
    # ``test_a_rule_kind_that_is_no_callable_on_the_value_refuses_and_names_itself`` --
    # the arrangement ``two_non_class_targets`` above already has.
    assert not refused, sorted(refused)
    assert carried, "no site carries nothing, so §5's last `not` clause is ungraded here"


def test_the_two_halves_of_section_2_are_one_readers_answer() -> None:
    """``lower.rules`` answers both of §2's questions and they never both answer.

    This is the property that keeps the three-way split above from being a second copy of
    §5's ``not`` row inside ``compiler.py``: for each of the three declaration shapes, at
    most one of ``rules.lower_declaration`` (the class half) and ``rules.on_a_value`` (the
    value half) returns anything, so the arm that fires is a consequence of the reading
    rather than a choice at the site.

    **§2's clause of 2026-10-28 does not move this and that is the point of it.**  The
    clause is about the POSITION a lowered rule may hang at, not about which half a
    keyword's shape takes: a ``not`` over a ``const`` is still a statement about a VALUE
    and a ``not`` over ``required`` is still lowered by the class half, and
    ``rules.as_the_object`` re-reads no keyword -- it asks whether the KIND is a callable
    on the value.  So ``on_a_value`` answers exactly what it answered before, and a
    change that made it claim ``required`` too would redden here.
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


def test_a_presence_rule_beside_a_conjoined_type_hangs_on_the_types_own_annotation() -> None:
    """The middle row, by document and pointer, now that §2's clause answers it.

    ``core/canonical-product.json`` and ``core/product.json`` state
    ``publisher_properties`` items as ``allOf: [{$ref: publisher-property-selector},
    {not: {required: ["publisher_domains"]}}]``.  The target is a union ROOT, so §5's row
    makes it the node's own type; the ``not`` is over ``required``, so §5's ``not`` row
    decides ``ForbiddenGroups`` -- a rule on a class, and the node has none.  §2's clause
    of 2026-10-28 is the half that was missing and it is not a kind: "at a position with
    no class above it, the value *is* the object", so the rule hangs on
    ``PublisherPropertySelector`` itself.

    **Three claims, and the first is the one the row was filed for**: the sentence asking
    for "a value-level presence kind that section 2 does not name" is gone from the whole
    run; the two sites carry the rule the document's own ``not`` states; and neither
    document refuses at this pointer any more.

    What neither document does yet is EMIT, and this test does not claim it: both are
    CHAINED behind ``core/tracker-execution-selector.json``
    ``/oneOf/1/properties/vast_versions``, §5(b)'s restatement row and another row's
    obstruction.  So the chain target is read off the run rather than pinned -- a row
    that clears it makes these two emit and must not redden here.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    stating = claimed(
        "documents stating a presence rule beside a conjoined type",
        {"core/canonical-product.json", "core/product.json"},
        inside=set(bundle.portable(BUNDLE)),
    )
    # (1) **Nobody asks for the kind any more.**  PRIMARY only, because a chained refusal
    # QUOTES its target's whole sentence and the substring would reach every document
    # behind a refusal that still carried it.
    assert not [
        document
        for document, row in out.refusals.items()
        if row["kind"] != "chained" and "value-level presence kind" in row["detail"]
    ], sorted(
        document
        for document, row in out.refusals.items()
        if row["kind"] != "chained" and "value-level presence kind" in row["detail"]
    )
    # (2) The rule each site carries, DERIVED from the document's own statement rather
    # than written out here, so a reading that started forbidding a different group
    # reddens.
    sites = [s for s in _reaching() if s.symbol == "PublisherPropertySelector"]
    assert len(sites) == len(stating), sites
    for document, site in zip(sorted(stating), sorted(sites), strict=True):
        node = bundle.node_at(bundle.read(BUNDLE, document), site.at.rsplit("/allOf/", 1)[0])
        forbidden = node["allOf"][1]["not"]["required"]
        assert site.at.endswith("/properties/publisher_properties/items/allOf/0"), site
        assert site.refusal is None, site.refusal
        assert site.validators == (ForbiddenGroups((tuple(forbidden),)),), site
    # (3) And no refusal of either document is this node's: the row is cleared, whatever
    # stands in front of the document next.
    for document in sorted(stating):
        row = out.refusals.get(document)
        if row is None:
            continue
        assert row["kind"] == "chained", row
        assert not row["pointer"].endswith(
            "/properties/publisher_properties/items/allOf/0"
        ), row


def test_the_presence_kinds_read_the_values_own_members_at_either_place() -> None:
    """§2's clause as the RUNTIME holds it: one kind, one ``errors``, two callers.

    ``adcp.types._runtime.TheValueIsTheObject`` is the clause and nothing more, so the
    property to grade is that the two callers AGREE: ``Rule.errors(keys, values)`` -- what
    ``RuleBound`` asks of a class's rule -- and ``ValueRule.__call__(value)`` -- what
    pydantic asks of an annotation's -- decide the same payload the same way, and the
    keyword a refusal names is the document's own either way.

    All three kinds §2's clause names, because the clause names three and only
    ``ForbiddenGroups`` has a site in this bundle: a kind admitted by the sentence and
    broken would be found by the next document and not by this suite.

    **A value that is no object is returned untouched**, which is :class:`Distinct`'s
    measured reason read for a statement about properties: the annotated type can be one
    arm of a union whose other arms are a string or a number, and draft-07 applies
    ``required`` to an object alone -- so refusing there would make the model narrower
    than its document, which §2 forbids.
    """
    forbids = ForbiddenGroups((("a", "b"),))
    requires = RequiredGroups((("a",), ("b",)), "oneOf")
    presence = PresenceGroups((Presence(("a",), (("b",),)), Presence(("b",), (("a",),))), "oneOf")
    cases: list[tuple[Any, dict[str, Any], str | None]] = [
        (forbids, {"a": 1, "b": 2}, "not"),
        (forbids, {"a": 1}, None),
        (forbids, {}, None),
        (requires, {"a": 1}, None),
        (requires, {"a": 1, "b": 2}, "oneOf"),
        (requires, {}, "oneOf"),
        (presence, {"a": 1}, None),
        (presence, {"a": 1, "b": 2}, "oneOf"),
        (presence, {}, "oneOf"),
    ]
    seen: set[str] = set()
    for rule, payload, keyword in cases:
        # The class half, which is what ``RuleBound`` evaluates.
        through_a_class = [e[0] for e in rule.errors(frozenset(payload), payload)]
        assert through_a_class == ([keyword] if keyword else []), (rule, payload)
        # The value half, on the same payload, through ``ValueRule.__call__``.
        assert isinstance(rule, ValueRule), rule
        try:
            assert rule(payload) is payload, (rule, payload)
            through_the_value = None
        except PydanticCustomError as refusal:
            through_the_value = refusal.type
        assert through_the_value == keyword, (rule, payload, through_the_value)
        seen.add(type(rule).__name__)
    assert seen == {"ForbiddenGroups", "RequiredGroups", "PresenceGroups"}, sorted(seen)
    # No object, so nothing to say about its properties -- and an EMPTY key set is not
    # the answer either, which is why ``_members`` returns ``None``: ``RequiredGroups``
    # over ``{}`` refuses above, and it must not refuse a string.
    for rule, _payload, _keyword in cases:
        for value in ("not an object", 7, None, ["a"]):
            assert rule(value) == value, (rule, value)


def test_a_presence_rule_on_a_value_is_enforced_through_a_rendered_annotation() -> None:
    """The other two halves of the path: the RENDERER and pydantic.

    The two bundle sites are in documents that do not emit yet -- both are chained behind
    §5(b)'s restatement row -- so the annotation this row writes has no module in the
    tree to be read out of, and the pipeline is graded at its two remaining seams
    instead.  Named as the gap it is: when
    ``core/tracker-execution-selector.json`` clears, ``core/product.json`` emits and
    ``tests/test_emit.py``'s ``VALUE_RULE_CARRIERS`` gains a ``ForbiddenGroups`` row at
    ``core/product.json`` / ``CONJ`` (``adcp-client-python-10l.63``).

    1. ``render.alias`` composes ``Annotated[T, AfterValidator(ForbiddenGroups(...))]``
       and REPORTS every symbol it names, which is the measured trap: a part spelled in
       the text and not passed through the model layer reaches the module as a
       ``NameError``.
    2. pydantic enforces it at the position the row writes -- a MODEL as the annotated
       type -- so the after-validator is handed a built model and :func:`supplied` reads
       the keys that arrived.  Both directions, because a narrowing is the failure that
       matters.
    """
    rule = ForbiddenGroups((("publisher_domains",),))
    rendered = render.alias(
        ir.AliasDecl(
            "PublisherPropertySelectorNoDomains",
            ir.TypeRef("PublisherPropertySelector", local=True, validators=(rule,)),
        )
    )
    assert "AfterValidator(ForbiddenGroups((('publisher_domains',),)))" in rendered.text, (
        rendered.text
    )
    assert ("adcp.types._runtime", "ForbiddenGroups") in rendered.imports, rendered.imports

    class Selector(AdCPBaseModel):
        publisher_domains: list[str] | None = None
        publisher_ids: list[str] | None = None

    adapter = TypeAdapter(Annotated[Selector, AfterValidator(rule)])
    assert adapter.validate_python({"publisher_ids": ["p"]}).publisher_ids == ["p"]
    with pytest.raises(ValidationError) as caught:
        adapter.validate_python({"publisher_domains": ["example.com"]})
    assert "not" in {e["type"] for e in caught.value.errors()}, caught.value.errors()


def test_a_rule_kind_that_is_no_callable_on_the_value_refuses_and_names_itself() -> None:
    """The decline, on a constructed node: the part of the partition above that is empty.

    §2's clause admits a class's rule onto the value "as a ``_runtime.ValueRule`` -- a
    callable on the value, and all it is" -- so a kind that is NOT one has nowhere to live
    at a position with no class, and §2 admits no drop by silence.  0 sites over the
    portable population, because every rule this arm lowers is one of the clause's three,
    which is why this is graded on a node built here.

    ``minProperties`` is the probe and the reason is the kind it lowers to:
    :class:`adcp.types._runtime.PropertyCount` counts the keys that arrived through the
    class's own field set, so it is a :class:`Rule` and no ``ValueRule``, and
    ``lower.rules.as_the_object`` declines it by asking the KIND rather than by consulting
    a list.
    """
    conjunct = {"minProperties": 1, "additionalProperties": True}
    assert lower_rules.as_the_object(
        lower_rules.lower_declaration(conjunct, Position.CONJ).rules
    ) == lower_rules.AsTheObject(declined=(PropertyCount(minimum=1, maximum=None),))
    node = schema_parse.parse(
        {"allOf": [{"$ref": _AN_ENUM}, conjunct]},
        pointer="/properties/kind",
        position=Position.PROP,
        source=schema_parse.Source(document="probe.json"),
    )
    answer = compiler._the_conjuncts_own_type(  # noqa: SLF001 -- the arm's only caller
        node,
        [("/properties/kind/allOf/0", _AN_ANNOTATION, _THE_REFERENCE)],
        fields_declared=(),
        bases=(),
        rule_nodes=[conjunct],
        # **``facts`` is the ``allOf``'s own SIBLING BOUNDS**, which §5's ``$ref`` row at
        # CONJ reads whole ("the other conjuncts AND THE ``allOf``'s SIBLINGS constrain
        # it").  Empty here because the probe states none, and passed EXPLICITLY rather
        # than defaulted: this call is the arm's only caller outside the walk, and an
        # argument the probe does not name is an argument the probe is not grading.  It
        # was absent, and the row gaining it made every call of this file a ``TypeError``
        # (``adcp-client-python-10l.109``).
        facts=(),
    )
    assert isinstance(answer, Refusal), answer
    assert (answer.keyword, answer.resolved) == ("allOf", "deferred"), answer
    # The KIND names itself, which is what keeps the decline from being a silent drop.
    assert "PropertyCount" in answer.detail, answer.detail
    assert "is a callable on the value, and this one is not" in answer.detail, answer.detail


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
                {"$ref": _AN_ENUM},
                {"not": {"const": "video"}},
                {"not": {"const": "audio"}},
            ]
        },
        pointer="/properties/kind",
        position=Position.PROP,
        source=schema_parse.Source(document="probe.json"),
    )
    # The row reads the TARGET and not a symbol (``adcp-client-python-10l.59``), so the
    # probe uses the one a ``$ref`` to an enumeration resolves to: ``_AN_ANNOTATION``,
    # the kind that makes §5's row give the node the target as its own TYPE.
    target = _AN_ANNOTATION
    answer = compiler._the_conjuncts_own_type(  # noqa: SLF001 -- the arm's only caller
        node,
        [("/properties/kind/allOf/0", target, _THE_REFERENCE)],
        fields_declared=(),
        bases=(),
        rule_nodes=[{"not": {"const": "video"}}, {"not": {"const": "audio"}}],
        # **``facts`` is the ``allOf``'s own SIBLING BOUNDS**, which §5's ``$ref`` row at
        # CONJ reads whole ("the other conjuncts AND THE ``allOf``'s SIBLINGS constrain
        # it").  Empty here because the probe states none, and passed EXPLICITLY rather
        # than defaulted: this call is the arm's only caller outside the walk, and an
        # argument the probe does not name is an argument the probe is not grading.  It
        # was absent, and the row gaining it made every call of this file a ``TypeError``
        # (``adcp-client-python-10l.109``).
        facts=(),
    )
    assert isinstance(answer, Refusal), answer
    assert (answer.keyword, answer.resolved) == ("allOf", "deferred"), answer
    assert "two conjuncts state 'not'" in answer.detail, answer.detail
    # And ONE ``not`` beside the same target is decided, so the refusal above is about the
    # second statement and not about the position.
    one = compiler._the_conjuncts_own_type(  # noqa: SLF001
        node,
        [("/properties/kind/allOf/0", target, _THE_REFERENCE)],
        fields_declared=(),
        bases=(),
        rule_nodes=[{"not": {"const": "video"}}],
        facts=(),
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
