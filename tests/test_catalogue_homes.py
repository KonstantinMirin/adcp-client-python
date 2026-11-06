"""§3a's home rule, graded as a CONSTRUCTION rather than as a count of cycles.

``docs/plan/architecture.md`` §3a asks that a reference cycle be **unrepresentable rather
than avoided by care**, and ``adcp-client-python-6qi7`` is what the other thing costs:

    ``emit.needs`` unions ``bundle.references`` with the catalogue's homes
    (``emit.py``), so a catalogue entry whose home lands inside a document that
    references the restating one closes a cycle ``emit.order`` must treat as a VERDICT.
    Measured once at *emitted 896 / refused 163 of 1,059*, 2 primary and 161 chained,
    on one home decision for one entry.

**WHAT THIS FILE GRADES, and why it is not "the run refused nothing".**  That the run
refuses nothing is a CENSUS: it says no entry of this bundle lands that way, and it cannot
say none can.  The property here is the POTENTIAL that makes the answer independent of the
bundle: with ``idx`` the index of ``emit.standing_order`` -- a topological order of the
bundle's reference graph, and of nothing else -- take ``φ(D) = idx(D)``.  Every edge of
the graph the run actually orders over must strictly decrease ``φ``.  A graph whose every
edge strictly decreases an integer potential has no cycle, for any bundle, so the three
assertions below are the derivation and ``test_the_potential_implies_the_order_finds_no_cycle``
is only its corollary.

**THE EDGES ARE READ OFF THE EMITTER'S OWN DERIVATIONS and the graph is assembled exactly
as ``emit.emit`` assembles it** -- ``emit.lowered_edges`` for the references,
``catalogue.collect`` and two ``collect_shapes`` calls for L0, L2 and L2C, and
``bundle.repeated`` for the document layer -- so a layer that stops running this way
reddens here and not in a report.  Nothing in this file reads ``codegen/`` as TEXT: a
grep over ``emit.py`` is not a gate on where a home lands.

**TWO EXEMPTIONS, BOTH NAMED BY ANOTHER SECTION AND BOTH GRADED SEPARATELY.**  A
construction with an unexamined exception is a census wearing a derivation's clothes, so
each exempt edge is enumerated and carries its own weaker assertion:

* **§1's ROOT.**  "Every portable document contributes a symbol", so a document root
  cannot become a reference to another module's class and
  ``catalogue.declared_at``/``shape_ranked`` rank a root ahead of the standing order.  A
  rooted home therefore need not be its group's earliest document.  What must hold there is
  strictly weaker and is measured per entry: the home must not REACH a restating document
  through the reference graph.
* **``bundle.repeated``'s SHALLOWEST PATH.**  That layer's home is the shallowest of two
  byte-identical paths and its docstring says why the standing order is not the rule --
  "it splits these groups 17/22 and would home 22 of them in ``core``, which is the domain
  the protocol's own union never names".  Its own measurement is what makes the edge safe:
  "nothing in the bundle references any of the 39 deep paths at all", so the home cannot
  reach the non-home member.  That sentence is asserted here rather than quoted.

**BOTH BUNDLES**, because 6qi7's 163 was reachable only on the patched one: the published
3.2 bundle is the pinned input and ``patch.for_build``'s is what the compile path reads,
and a property held by one and not the other is the defect this row was filed against --
"the measurement behind the rule has never seen a patched bundle".
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import pytest
from nodeset import claimed

from codegen import bundle, catalogue, emit, patch

REPO = Path(__file__).resolve().parent.parent
PUBLISHED = REPO / "schemas" / "cache" / "3.2"


@dataclass(frozen=True)
class Edge:
    """One edge of the graph the run orders over, with the layer that contributed it.

    ``tail`` imports a symbol ``head``'s module declares, so the run cannot write ``tail``
    before ``head``.  ``why`` is the layer and ``at`` the position or the entry it came
    from, both carried so a failure names the decision and not only the pair.
    """

    tail: str
    head: str
    why: str
    at: str


def _bundles() -> dict[str, Path]:
    """The two bundles a property about the home rule has to hold over.

    Named rather than parametrised over a directory scan: there are exactly two readings
    of this version -- the published one and the one ``patch.for_build`` hands the
    compile path -- and a test that discovered them would be a different claim.
    """
    return {"published 3.2": PUBLISHED, "patched (patch.for_build)": patch.for_build(PUBLISHED)}


@functools.lru_cache(maxsize=4)
def _graph(bundle_dir: Path) -> tuple[tuple[Edge, ...], dict[str, int], frozenset[str]]:
    """Every edge the run orders over, the standing order, and the rooted homes.

    One derivation for all four tests, memoised on the bundle: ``standing_order`` and the
    three collections each read the whole bundle, and this file asserts four properties of
    one reading rather than recollecting per test.
    """
    standing = emit.standing_order(bundle_dir)
    admitted = catalogue.Admitted(bundle_dir)
    l0 = catalogue.collect(bundle_dir, standing)
    l2 = catalogue.collect_shapes(admitted, "L2", standing)
    l2c = catalogue.collect_shapes(admitted, "L2C", standing)

    edges: list[Edge] = [
        Edge(document, site.target, "$ref", f"{document}{site.pointer}")
        for document, sites in emit.lowered_edges(bundle_dir).items()
        for site in sites
        if site.target is not None and site.target != document
    ]
    rooted: set[str] = set()
    rows: list[tuple[str, object, tuple, str]] = [
        # :class:`catalogue.Entry` carries no ``spelled`` property the way
        # :class:`catalogue.ShapeEntry` does, so L0's report string is built here rather
        # than by widening that class for one reader in a test.
        (
            "L0",
            entry.naming,
            entry.restating,
            entry.title or entry.name or f"{entry.naming.document}{entry.naming.pointer or ' /'}",
        )
        for entry in l0.entries.values()
    ]
    rows += [
        (layer, entry.at, entry.restating, entry.spelled)
        for layer, shapes in (("L2", l2), ("L2C", l2c))
        for entry in shapes.entries.values()
    ]
    for layer, home, restating, spelled in rows:
        for position in restating:
            if position.document == home.document:
                continue
            edges.append(Edge(position.document, home.document, layer, spelled))
            if home.is_a_root:
                rooted.add(f"{layer}:{spelled}")
    for member, home in bundle.repeated(bundle_dir).items():
        edges.append(Edge(member, home, "repeated", member))
    return tuple(edges), standing, frozenset(rooted)


def _reaches(bundle_dir: Path) -> dict[str, frozenset[str]]:
    """document -> every document it reaches through a ``$ref``, transitively.

    The REFERENCE graph only, which is what the two exemptions are weighed against: a
    rooted home is safe when it cannot reach a restating document, and a repeated
    document's home is safe when nothing reaches the non-home member.
    """
    direct: dict[str, set[str]] = {}
    for document, sites in emit.lowered_edges(bundle_dir).items():
        for site in sites:
            if site.target is not None and site.target != document:
                direct.setdefault(document, set()).add(site.target)
    out: dict[str, frozenset[str]] = {}
    for document in direct:
        seen: set[str] = set()
        unread = [document]
        while unread:
            for target in direct.get(unread.pop(), ()):
                if target not in seen:
                    seen.add(target)
                    unread.append(target)
        out[document] = frozenset(seen)
    return out


@pytest.mark.parametrize("named", sorted(_bundles()))
def test_every_edge_but_the_two_exempt_ones_strictly_decreases_the_potential(named: str) -> None:
    """``φ(D) = idx(D)`` strictly decreases along every non-exempt edge the run orders over.

    THE CONSTRUCTION ITSELF.  A ``$ref`` edge decreases because ``idx`` is a topological
    index of exactly those edges; a catalogue edge decreases because the home is its
    group's EARLIEST stating document in that order.  So a home inside a document that
    references the restating one is not merely absent -- it would make ``idx(home) >
    idx(restating)`` and redden this.
    """
    bundle_dir = _bundles()[named]
    edges, standing, rooted = _graph(bundle_dir)
    graded = claimed(
        f"{named}: the edges the run orders over, minus §1's rooted homes and the "
        "repeated-document layer",
        [
            edge
            for edge in edges
            if edge.why != "repeated" and f"{edge.why}:{edge.at}" not in rooted
        ],
        inside=edges,
    )
    climbing = sorted(
        f"{edge.why} edge {edge.tail} (idx {standing.get(edge.tail)}) -> {edge.head} "
        f"(idx {standing.get(edge.head)}) at {edge.at}"
        for edge in graded
        if standing.get(edge.head, len(standing)) >= standing.get(edge.tail, len(standing))
    )
    assert not climbing, (
        f"{named}: {len(climbing)} of {len(graded)} edges do not decrease φ, so a cycle is "
        f"representable and emit.order must read it as a VERDICT:\n  " + "\n  ".join(climbing[:20])
    )


@pytest.mark.parametrize("named", sorted(_bundles()))
def test_a_rooted_home_cannot_reach_a_document_that_restates_its_entry(named: str) -> None:
    """§1's exemption, graded with the weaker property that makes it safe.

    A root sorts ahead of the standing order (``catalogue.shape_ranked``) because §1
    obliges every portable document to contribute a symbol, so a rooted home need not be
    its group's earliest document and the potential above cannot cover it.  What must hold
    is that the home does not REACH a restating document: that is the only way the
    catalogue edge could close a cycle, and it is MEASURED per entry rather than counted.
    """
    bundle_dir = _bundles()[named]
    edges, _, rooted = _graph(bundle_dir)
    reaches = _reaches(bundle_dir)
    graded = claimed(
        f"{named}: the catalogue edges whose home is a document ROOT (§1's exemption)",
        [edge for edge in edges if f"{edge.why}:{edge.at}" in rooted],
        inside=edges,
    )
    closing = sorted(
        f"{edge.why} entry {edge.at}: the rooted home {edge.head} reaches {edge.tail}, "
        "which restates it"
        for edge in graded
        if edge.tail in reaches.get(edge.head, frozenset())
    )
    assert not closing, (
        f"{named}: {len(closing)} of {len(graded)} rooted homes close a reference cycle "
        "through the catalogue edge:\n  " + "\n  ".join(closing[:20])
    )


@pytest.mark.parametrize("named", sorted(_bundles()))
def test_nothing_references_a_repeated_documents_non_home_path(named: str) -> None:
    """``bundle.repeated``'s exemption, graded with its own docstring's measurement.

    That layer homes the SHALLOWEST of two byte-identical paths and declines the standing
    order for a measured reason of its own.  What makes its edge safe is the sentence
    "nothing in the bundle references any of the 39 deep paths at all": a non-home member
    nothing reaches cannot be reached from its home either, so the edge is on no cycle.
    Asserted here, so the day a document references a deep path this reddens rather than
    the run refusing 39 documents.
    """
    bundle_dir = _bundles()[named]
    edges, _, _ = _graph(bundle_dir)
    graded = claimed(
        f"{named}: the non-home paths of the repeated documents (bundle.repeated)",
        [edge.tail for edge in edges if edge.why == "repeated"],
        inside=set(bundle.portable(bundle_dir)),
    )
    referring = sorted(
        f"{document} references the non-home path {site.target}"
        for document, sites in emit.lowered_edges(bundle_dir).items()
        for site in sites
        if site.target in graded and site.target != document
    )
    assert not referring, (
        f"{named}: {len(referring)} references reach a repeated document's non-home path, "
        "so bundle.repeated's home rule is no longer safe by its own measurement:\n  "
        + "\n  ".join(referring[:20])
    )


@pytest.mark.parametrize("named", sorted(_bundles()))
def test_the_potential_implies_the_order_finds_no_cycle(named: str) -> None:
    """The COROLLARY, over the run's own order and not over a re-derivation.

    The three properties above are the derivation; this is what they predict, asked of
    ``emit.order`` over the whole portable population with both catalogue layers' edges
    unioned in exactly as ``emit.emit`` unions them.  It is here as a corollary and never
    as the gate: a run that refuses nothing says nothing about the next bundle, which is
    the mistake 6qi7 records one layer up -- the rule behind ``emit.order`` had "never
    seen a patched bundle".
    """
    bundle_dir = _bundles()[named]
    edges, _, _ = _graph(bundle_dir)
    homes: dict[str, set[str]] = {}
    for edge in edges:
        if edge.why != "$ref":
            homes.setdefault(edge.tail, set()).add(edge.head)
    reaches = emit.needs(emit.lowered_edges(bundle_dir), homes)
    population = claimed(
        f"{named}: the portable documents the order ranges over",
        bundle.portable(bundle_dir),
    )
    _, cycles = emit.order(emit.closure(sorted(population), reaches), reaches)
    assert not cycles, (
        f"{named}: {len(cycles)} of {len(population)} documents are on a cycle of the "
        f"unioned graph: {sorted(cycles)[:10]!r}"
    )
