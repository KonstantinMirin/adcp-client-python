"""THE OWNER'S CORRECTION OF 2026-11-07: a presence-only ``oneOf`` whose branches are an
XOR is a base plus children, and the dispatch reads the KEY SET.

``adcp-client-python-j0fr``.  The ruling reverses "a flattened presence-only ``oneOf`` is
correct", and the reason the old ruling gave was wrong rather than merely superseded: the
two children are NOT field-identical, they differ in field PRESENCE, which is the one
difference a subclass carries.  So §5's "the branches differ only in what is ``required``"
case takes the base-plus-children answer every other union takes.

**WHAT THIS FILE GRADES, and it is three claims and not one.**

1. The POPULATION is the parser's and is non-empty on both sides: the 8 nodes a base plus
   children expresses carry the hierarchy and no ``PresenceGroups``, and the 3 it cannot
   express carry the rule and no children.  **Asserted non-empty FIRST**, because a
   partition over an empty set passes every clause below while saying nothing -- which is
   the vacuity ``tests_emit/test_no_positional_name_is_public.py`` is built around and the
   same hazard here.
2. READING 1 holds per node, over the key sets the clauses range over: each branch's own
   set alone, every pair of branches' sets together, and none of them.  The DOCUMENT is
   asked through ``adcp.types._base._refuse_at`` -- the reading ``strict_validate`` makes
   -- and the MODEL through ``model_validate``, so the pair is a value on both sides and
   neither half is this file's own opinion about the schema.
3. The dispatch is a function of the PAYLOAD and not of declaration order, which is §4's
   own requirement for the ``const`` case read for a key set: the tag function is asked
   directly, the branch classes are reordered under it, and the answer does not move.

**MEASURED OFF THE COMPILER'S RECORD AND THE LOADED CLASSES, NEVER OFF EMITTED TEXT.**
The population comes from ``schema.parse.presence_branches`` over the bundle and from
``Emitted.declared``; the verdicts come from classes the materialised tree actually
imported.  A reading over module text cannot tell a class that dispatches from one that
merely spells a line.
"""

from __future__ import annotations

import importlib
import itertools
from typing import Any

import fresh
import pytest
from compiled import compiled
from nodeset import claimed, partitions
from pydantic import ValidationError

from adcp.types._base import BranchDispatchMixin, _refuse_at
from adcp.types._runtime import ForbiddenGroups, Presence, PresenceGroups, bound_rules
from codegen import bundle, emit
from codegen.keywords import Position
from codegen.schema import parse

#: One spelling of the bundle, re-exported from ``tests_emit/fresh.py``: a file that spells
#: its own path can come to range over a different bundle from the compile it reads.
BUNDLE = fresh.BUNDLE

#: A value the DOCUMENT admits for each name a clause of the 8 ranges over, plus the root's
#: own required keys.  **Hand-written, and that is the point**: these are the key sets the
#: owner's correction is about, and a drawn corpus would hide which set is which.  Every
#: one is checked against the document itself in :func:`test_reading_1_holds_at_every_key_set`
#: -- a filler the document refuses shows up there as a node with no admitted probe, which
#: that test fails on rather than passing vacuously.
_AGENT = "https://seller.example.com"
_TRAVEL = {"value": 15, "unit": "min"}
_RADIUS = {"value": 5, "unit": "km"}
_GEOMETRY = {"type": "Polygon", "coordinates": [[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]]]}
_FORMAT_ID = {"agent_url": _AGENT, "id": "display_300x250"}

#: ``(module, symbol, the document's pointer, fillers, the root's own required keys)``, one
#: row per node of the 8.  The pointer is asserted against the class's own
#: ``__adcp_schema__`` below, so a row naming a node the compiler did not emit there fails
#: rather than grading another class.
THE_EIGHT: tuple[tuple[str, str, str, str, dict[str, Any], dict[str, Any]], ...] = (
    (
        "adcp.types._schemas.core.catchment",
        "Catchment",
        "core/catchment.json",
        "#",
        {"travel_time": _TRAVEL, "transport_mode": "driving", "radius": _RADIUS,
         "geometry": _GEOMETRY},
        {"catchment_id": "drive"},
    ),
    (
        "adcp.types._schemas.core.creative_asset",
        "CreativeAsset",
        "core/creative-asset.json",
        "#",
        {"format_id": _FORMAT_ID, "format_kind": "image"},
        {"creative_id": "cr_1", "name": "a creative", "assets": {}},
    ),
    (
        "adcp.types._schemas.core.creative_manifest",
        "CreativeManifest",
        "core/creative-manifest.json",
        "#",
        {"format_id": _FORMAT_ID, "format_kind": "image"},
        {"assets": {}},
    ),
    (
        "adcp.types._schemas.core.frequency_cap_impression_constraints",
        "FrequencyCapImpressionConstraints",
        "core/frequency-cap-impression-constraints.json",
        "#",
        {"allowed_values": [1, 2, 3], "minimum": 1, "maximum": 10},
        {},
    ),
    (
        "adcp.types._schemas.core.frequency_cap_interval_constraints",
        "FrequencyCapIntervalConstraints",
        "core/frequency-cap-interval-constraints.json",
        "#",
        {"allowed_intervals": [1, 2], "minimum_interval": 1, "maximum_interval": 7},
        {"unit": "days"},
    ),
    (
        "adcp.types._schemas.core.product_filters",
        "GeoProximityItem",
        "core/product-filters.json",
        "#/properties/geo_proximity/items",
        {"lat": 51.5, "lng": -0.12, "travel_time": _TRAVEL, "transport_mode": "driving",
         "radius": _RADIUS, "geometry": _GEOMETRY},
        {},
    ),
    (
        "adcp.types._schemas.core.targeting",
        "GeoProximityItem",
        "core/targeting.json",
        "#/properties/geo_proximity/items",
        {"lat": 51.5, "lng": -0.12, "travel_time": _TRAVEL, "transport_mode": "driving",
         "radius": _RADIUS, "geometry": _GEOMETRY},
        {},
    ),
    (
        "adcp.types._schemas.creative.list_creatives_response",
        "CreativesItem",
        "creative/list-creatives-response.json",
        "#/properties/creatives/items",
        {"format_id": _FORMAT_ID, "format_kind": "image"},
        {"creative_id": "cr_1", "name": "a creative", "status": "approved",
         "created_date": "2026-01-01T00:00:00Z", "updated_date": "2026-01-01T00:00:00Z"},
    ),
)

#: The 3 a base plus children CANNOT express, each failing
#: ``parse.presence_branches``' third condition twice: a ``responsive`` branch requiring one
#: of FOUR separate groups -- "at least one of these four is present", which no class says
#: by field requiredness -- and a ``none`` branch requiring nothing at all and forbidding
#: all seven keys.  They are reported rather than forced, which is reading 2's own
#: direction: a model wider than its document is permitted and a narrower one is not.
THE_THREE: tuple[str, ...] = (
    "formats/canonical/display_tag.json",
    "formats/canonical/html5.json",
    "formats/canonical/image.json",
)

#: Where the 3 state their combinator.  A CONJUNCT of the root, which is why they reach
#: ``parse._borne_by_a_conjunct`` and not ``_decide``'s own union arm.
THE_THREES_POINTER = "/allOf/1"


@pytest.fixture(scope="module")
def run() -> emit.Emitted:
    """One compile, shared: ``tests_emit/compiled.py`` holds it per document set."""
    return compiled(BUNDLE, fresh.population())


def _clauses_in_the_bundle() -> dict[tuple[str, str], tuple[Any, ...]]:
    """Every presence-only ``oneOf`` with a forbid half, read off the PARSER.

    ``parse.presence_clause`` and ``parse.presence_branches`` are the compiler's own
    classification, so the population this file grades and the population the emitter
    claimed are one reading asked twice rather than two readings that can disagree.
    """
    out: dict[tuple[str, str], tuple[Any, ...]] = {}
    for document in sorted(bundle.portable(BUNDLE)):
        doc = bundle.read(BUNDLE, document)
        for pointer, node in bundle.nodes(doc):
            if not isinstance(node, dict) or not isinstance(node.get("oneOf"), list):
                continue
            read = [parse.presence_clause(b, Position.ROOT) for b in node["oneOf"]]
            if any(c is None for c in read) or not any(c[1] for c in read):
                continue
            out[(document, pointer)] = tuple(read)
    return out


def test_the_parser_claims_eight_of_eleven_and_the_other_three_keep_the_rule() -> None:
    """The POPULATION, off the parser, with both halves non-empty.

    11 presence-only ``oneOf`` nodes state a forbid half; ``presence_branches`` claims 8 of
    them and declines 3.  **Both sides are asserted non-empty and the two are asserted
    DISJOINT and EXHAUSTIVE** (``nodeset.partitions``), because a condition that silently
    claimed everything and one that silently claimed nothing both read green against a
    one-sided assertion.
    """
    found = _clauses_in_the_bundle()
    graded = claimed("presence-only oneOf nodes with a forbid half", found)
    expressible = {
        site
        for site in graded
        if parse.presence_branches(
            bundle.node_at(bundle.read(BUNDLE, site[0]), site[1]), Position.ROOT
        )
        is not None
    }
    partitions(set(graded), expressible=expressible, a_rule=set(graded) - expressible)
    assert {d for d, _ in expressible} == {row[2] for row in THE_EIGHT}, sorted(expressible)
    assert {d for d, _ in set(graded) - expressible} == set(THE_THREE), sorted(graded)
    assert {p for _, p in set(graded) - expressible} == {THE_THREES_POINTER}


@pytest.mark.parametrize("document", THE_THREE)
def test_a_node_no_hierarchy_expresses_keeps_its_presence_rule(
    run: emit.Emitted, document: str
) -> None:
    """The 3 are REPORTED rather than forced: the rule stays and no child is declared.

    Both halves, because either alone passes on the wrong tree: a node that lost its rule
    and gained no children would drop the exclusivity entirely, and one that kept the rule
    AND gained children would state it twice.
    """
    declared = run.declared[document]
    assert declared, document
    children = {p for p in declared if p.startswith(f"{THE_THREES_POINTER}/oneOf/")}
    assert children == set(), f"{document} declared a child the hierarchy cannot express"
    module = importlib.import_module(run.emitted[document])
    root = next(
        cls
        for cls in vars(module).values()
        if isinstance(cls, type)
        and getattr(cls, "__adcp_schema__", None) is not None
        and cls.__dict__.get("__adcp_schema__", None) is not None
        and cls.__dict__["__adcp_schema__"].document == document
        and cls.__dict__["__adcp_schema__"].pointer == "#"
    )
    kinds = [r for r in bound_rules(root) if isinstance(r, PresenceGroups)]
    assert len(kinds) == 1, (root.__name__, bound_rules(root))
    assert kinds[0].combinator == "oneOf"
    # **The clause count is DERIVED from the document and never written**
    # (``final-state.md``: "a figure in a comment or a docstring is derived, never
    # written", and ``tests_emit/test_every_check_names_its_set.py``'s first rule, which
    # a written ``== 4`` here grew the ceiling of).  One clause per branch the document
    # states at the conjunct that carries the combinator.
    stated = bundle.node_at(bundle.read(BUNDLE, document), THE_THREES_POINTER)["oneOf"]
    assert stated, f"{document} states no branch at {THE_THREES_POINTER}"
    assert len(kinds[0].clauses) == len(stated), kinds[0]
    assert not isinstance(root, BranchDispatchMixin)


@pytest.mark.parametrize(
    ("path", "symbol", "document", "pointer"),
    [(m, s, d, p) for m, s, d, p, _, _ in THE_EIGHT],
    ids=[f"{d}{p}" for _, _, d, p, _, _ in THE_EIGHT],
)
def test_an_expressible_node_is_a_base_plus_children_with_no_rule_left_over(
    path: str, symbol: str, document: str, pointer: str
) -> None:
    """The hierarchy IS the exclusivity, and the rule it replaced is gone.

    * the base declares ``_branch_models`` -- which is what ``_dispatching`` reads, so
      inheriting the attribute is not being the base;
    * it carries one :class:`~adcp.types._runtime.Presence` clause per branch and NO
      :class:`~adcp.types._runtime.PresenceGroups` anywhere in its MRO, because a node that
      kept both would state one fact twice;
    * every child declares its clause's required names as REQUIRED fields of its own and
      carries its branch's own :class:`~adcp.types._runtime.ForbiddenGroups`, which is the
      forbid half's carrier AT THE CHILD -- a child declaring the forbidden name nowhere has
      none, because ``_runtime.supplied`` reads ``__pydantic_fields_set__``.
    """
    base = getattr(importlib.import_module(path), symbol)
    assert base.__dict__["__adcp_schema__"].document == document
    assert base.__dict__["__adcp_schema__"].pointer == pointer
    assert issubclass(base, BranchDispatchMixin)
    assert base.__dict__.get("_branch_models"), symbol
    assert base._BRANCH_DISCRIMINATOR == "", "a key set is not a key's value"
    assert base._branch_combinator() == "oneOf"

    clauses = base._BRANCH_PRESENCE
    assert clauses, symbol
    assert len(clauses) == len(base._branch_models)
    assert [name for name, _ in clauses] == [b.__name__ for b in base._branch_models]
    assert all(isinstance(c, Presence) for _, c in clauses)
    assert not [r for r in bound_rules(base) if isinstance(r, PresenceGroups)]

    for (name, clause), child in zip(clauses, base._branch_models):
        assert child.__name__ == name
        assert issubclass(child, base)
        assert len(clause.require) == 1 and clause.require[0], clause
        assert clause.forbid, clause
        own = set(child.__dict__.get("__annotations__", ()))
        assert set(clause.require[0]) <= own, (name, own)
        assert all(child.model_fields[key].is_required() for key in clause.require[0])
        assert [r for r in child.__dict__.get("_adcp_rules", ()) if isinstance(r, ForbiddenGroups)]


@pytest.mark.parametrize(
    ("path", "symbol", "fillers", "root"),
    [(m, s, f, r) for m, s, _, _, f, r in THE_EIGHT],
    ids=[f"{d}{p}" for _, _, d, p, _, _ in THE_EIGHT],
)
def test_reading_1_holds_at_every_key_set(
    path: str, symbol: str, fillers: dict[str, Any], root: dict[str, Any]
) -> None:
    """READING 1, per node, over the key sets the clauses range over.

    The probes are each branch's own required names alone, every PAIR of branches' names
    together, and none of them -- the bead's four values at a 2-branch node and its
    generalisation at a 3-branch one.  The document's verdict comes from ``_refuse_at`` and
    the model's from ``model_validate``, and the two must agree in both directions: a model
    admitting what the document refuses is reading 1's violation, and one refusing what the
    document admits is a narrowing §2 forbids outright.

    **AND EVERY BRANCH MUST BE REACHED BY AN ADMITTED PROBE**, asserted last.  A node whose
    every probe is refused by both halves proves AGREEMENT and says nothing about the
    exclusivity -- it is the shape a wrong filler produces, and it would read green.

    **AND THE REFUSAL NAMES THE DOCUMENT'S OWN KEYWORD**, which is where the dispatch
    mechanism shows up in a verdict rather than in a schema: a key set naming no branch is
    ``oneOf`` with :class:`~adcp.types._runtime.PresenceGroups`' own sentence over the
    clauses the base holds (``_no_clause``).  A plain union answers the same payload with
    its branches' field errors instead, so this is the clause that separates the two from
    the outside.  It is asserted only where the refusal is the DISPATCH's -- a probe the
    document refuses for a missing root key is refused on that key, by the branch, and
    names ``required``.
    """
    base = getattr(importlib.import_module(path), symbol)
    clauses = base._BRANCH_PRESENCE
    assert clauses, symbol
    groups = {name: frozenset(clause.require[0]) for name, clause in clauses}
    probes: list[frozenset[str]] = [frozenset()]
    probes += list(groups.values())
    probes += [groups[a] | groups[b] for a, b in itertools.combinations(groups, 2)]
    probes.append(frozenset().union(*groups.values()))

    admitted: set[str] = set()
    for keys in probes:
        assert keys <= set(fillers), sorted(keys - set(fillers))
        payload = {**root, **{k: fillers[k] for k in sorted(keys)}}
        holding = [n for n, c in clauses if c.holds(frozenset(payload))]
        try:
            _refuse_at(base.__dict__["__adcp_schema__"], payload, symbol, module=path)
        except ValidationError:
            with pytest.raises(ValidationError) as refused:
                base.model_validate(payload)
            if len(holding) != 1:
                row = refused.value.errors()[0]
                assert row["type"] == "oneOf", row
                assert f"{len(holding)} of these clauses hold" in row["msg"], row
                for _, clause in clauses:
                    assert clause.spelled() in row["msg"], row
            continue
        got = base.model_validate(payload)
        assert len(holding) == 1, (sorted(keys), holding)
        assert type(got).__name__ == holding[0], (sorted(keys), type(got).__name__)
        admitted.add(holding[0])
    assert admitted == set(groups), (
        "a branch no admitted probe reaches proves agreement and not the exclusivity: "
        f"{sorted(set(groups) - admitted)}"
    )


@pytest.mark.parametrize(
    ("path", "symbol", "fillers", "root"),
    [(m, s, f, r) for m, s, _, _, f, r in THE_EIGHT],
    ids=[f"{d}{p}" for _, _, d, p, _, _ in THE_EIGHT],
)
def test_the_branch_is_a_function_of_the_payload_and_not_of_declaration_order(
    path: str, symbol: str, fillers: dict[str, Any], root: dict[str, Any]
) -> None:
    """§4's requirement, read for a key set: **selection must be a function of the payload,
    never of the order the classes happen to be declared in.**

    Asked of the tag function rather than of an outcome, because that is where the property
    lives: it is a total function from the key set to a branch name, computed before any
    branch is tried.  The probe REVERSES ``_BRANCH_PRESENCE`` and asserts the answer does
    not move -- which a plain ``A | B`` cannot satisfy, since pydantic there keeps the first
    branch whose class admits.

    And the two failing counts answer with NO TAG: zero clauses holding is a payload no
    branch describes, and two or more is one the document refuses for satisfying two.

    **THE ADAPTER THE BASE INSTALLED IS READ, AND THAT IS WHAT MAKES THIS CLAUSE BITE.**
    Measured: with ``_branch_adapter`` perturbed to build a plain ``Union`` over the same
    branch classes, every other clause in this file stays GREEN -- the children inherit
    their forbidden name from the base and carry their branch's own ``ForbiddenGroups``, so
    each one refuses the both-keys payload on its own and reading 1 survives either
    dispatch at these 8 nodes.  That is precisely the bead's point and not a reason to
    relax: a plain union's correctness there is a property of ``additionalProperties`` and
    of the branches happening to be disjoint, neither of which is the exclusivity, so the
    MECHANISM is the thing to assert.  So this reads the installed core schema -- a
    ``tagged-union`` whose ``discriminator`` is :meth:`_presence_tag` itself and whose
    ``choices`` are keyed by the branch names -- and the REFUSAL's own keyword, which is
    the document's ``oneOf`` with ``PresenceGroups``' sentence and which a plain union
    reports as "is not valid under any of the N branches" instead.
    """
    base = getattr(importlib.import_module(path), symbol)
    clauses = base._BRANCH_PRESENCE
    assert clauses, symbol
    groups = {name: frozenset(clause.require[0]) for name, clause in clauses}

    installed = base._branch_adapter().core_schema
    inner = installed["schema"] if installed["type"] == "definitions" else installed
    assert inner["type"] == "tagged-union", inner["type"]
    assert inner["discriminator"].__func__ is BranchDispatchMixin._presence_tag.__func__
    assert sorted(inner["choices"]) == sorted(groups)

    class Reversed(base):  # type: ignore[misc, valid-type]
        """``base`` with the branch order reversed and nothing else changed."""

        _BRANCH_PRESENCE = tuple(reversed(clauses))
        _branch_models = tuple(reversed(base.__dict__["_branch_models"]))

    for name, keys in groups.items():
        payload = {**root, **{k: fillers[k] for k in sorted(keys)}}
        assert base._presence_tag(payload) == name, sorted(keys)
        assert Reversed._presence_tag(payload) == name, sorted(keys)

    assert base._presence_tag({**root}) is None, "no clause holds and the tag is none"
    if len(groups) >= 2:
        both = frozenset().union(*list(groups.values())[:2])
        payload = {**root, **{k: fillers[k] for k in sorted(both)}}
        assert base._presence_tag(payload) is None, "two keys name no branch"
