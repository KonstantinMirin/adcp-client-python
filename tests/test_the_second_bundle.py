"""THE SECOND BUNDLE IS GRADED, and until this file nothing in the suite read it.

The owner's standing goal is one sentence: *the SDK is emitted according to the schema, no
duplication, faithful checks -- and the same must be true for 3.3 as for 3.2.*  Bundle
3.3.0-beta.0 was committed at ``2f5a7af3b`` as "the second bundle the goal is verified
against" and then verified by nothing: an AST sweep for a test module naming it found
``tests/test_cells.py``'s DOCSTRING and no code anywhere.  So the one claim the second
bundle makes on the compiler -- that it compiles -- was carried by a lane's terminal and
would have gone red silently.

**WHAT WENT RED WHILE NOTHING READ IT, which is this file's whole subject.**  At
``2f5a7af3b`` the compiler read bundle 3.3 as

::

    emitted 946 / refused 192 (deferred 3, verdict 189); accounted 1135
    primary 6, chained 186

and **189 of those 192 were one loop**.  Three documents carried the primary verdict

::

    $ref at /: a reference cycle:
    core/brand-ref.json -> brand.json -> core/identity-relying-party.json -> core/brand-ref.json

and 186 more refused through the chain.  **Two of the loop's three hops are the bundle's
own ``$ref``s and the third is not in the bundle at all.**  A three-colour DFS over bundle
3.3's own reference graph -- 4,862 absolute and 458 local ``$ref``s over 1,138 portable
documents -- finds 0 cycles.  The closing hop was OURS: §3a's catalogue placed the L2 entry
titled *Data Subject Contestation* -- stated at ``brand.json#/definitions/`` and at
``core/brand-ref.json#/properties/data_subject_contestation`` -- in ``brand.json``, because
the home order was TITLE-FIRST and only ``brand.json``'s position carries the title.  That
made ``core/brand-ref.json`` import from ``brand.json``, which already reached
``core/brand-ref.json`` through ``core/identity-relying-party.json``; ``emit.needs`` unions
the catalogue edge with the ``$ref`` edges, and ``emit.order`` makes a cycle a verdict for
every document on it.

``catalogue.shape_ranked`` is where that was fixed and its docstring carries the
measurement.  **This file is the part that was missing**: the rule went from one that could
produce a cycle to one that is much less able to, and nothing graded the difference on a
bundle that had realised it.

**IT GRADES THE OUTCOME AND NOT THE RULE**, which is deliberate.  The relation
``emit.order`` ranges over is assembled inside ``emit.emit`` from four catalogue layers; a
check that rebuilt it here would be a second statement of that assembly and would pass a
day when the two diverged.  What a refusal's own ``detail`` says is the compiler's answer
and nothing else's, so that is what is read.
"""

from __future__ import annotations

import fresh
from compiled import compiled
from nodeset import claimed, ratchet

from codegen import bundle

#: The second bundle, taken from the ONE declaration (``tests/fresh.py``) rather than
#: spelled here -- ``adcp-client-python-lzzj.11``'s rule.
SECOND = fresh.SECOND

#: Every document of bundle 3.3 the compiler refuses, and the row that owns each.
#:
#: **MEASURED over the 1,138 portable documents of ``schemas/cache/3.3``**: 6 refusals, 4
#: primary over 4 keywords and 2 chained behind two of them.  Each primary is named by the
#: keyword the compiler reports and the pointer it reports it at, so a reader can re-derive
#: the row with ``./check --why``.
#:
#: **THIS SET MAY SHRINK AND MAY NOT GROW.**  It is a refusal INVENTORY and not a
#: permission: a document leaving it is the work landing, and a document joining it is a
#: regression this file exists to name.  A new refusal is therefore a failure here and not
#: an edit to this constant.
#:
#: **SIX DOCUMENTS LEFT IT, and they are the whole of the bundle's VERDICT count**
#: (``adcp-client-python-82m.59``).  3.3's only hard verdict was ``title`` at
#: ``core/targeting-overlay-requirements.json#/definitions/daypartRequirement`` -- two
#: positions of one union deriving ``TargetingOverlayRequirementsDaypartRequirement``, and
#: a MEMBER TYPE has no rung to fall to -- with five documents chained behind it:
#: ``media-buy/list-products-request.json``,
#: ``media-buy/product-discovery-criteria.json``, ``media-buy/proposal-refinement.json``,
#: ``media-buy/refine-proposals-request.json`` and
#: ``media-buy/request-proposals-request.json``.  What closed all six is §4's LAST branch
#: rung (``lower.names.REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT``): the branch states one
#: level down that it requires one of ``timezone_modes`` and ``time_granularity``, so it
#: has a name to fall to and takes ``DaypartRequirementTimeGranularityTimezoneModes``.
#: **The bundle's VERDICT count is now 0** -- every refusal below is DEFERRED, which is a
#: row of ours that is not written rather than a defect of the bundle's.
#:
#: ``adcp-client-python-23cs`` is the row that measured the 192 and named the loop; the
#: residue below is filed under ``adcp-client-python-ps1h``.
REFUSES = {
    # PRIMARY, one per keyword, and all four are DEFERRED.
    "compliance/comply-test-controller-request.json",  # required, deferred: no row lowers it
    "core/escalation-sla.json",  # pattern, deferred: a restatement that neither matches nor narrows
    "media-buy/package-forecast-input.json",  # $ref, deferred: the target declares no symbol at /allOf/1
    "trust/v1/trust.json",  # allOf, deferred: a $ref at a conjunct to a non-field-set target
    # CHAINED, each through one of the two above it quotes.
    "media-buy/get-products-request.json",
    "trust/v1/trust-acknowledgements.json",
}

#: The three documents the title-first home order refused, in the order the cycle named
#: them.  They are asserted to EMIT, which is the strongest thing a reader can ask of the
#: fix: the loop is gone from the relation, not merely reported differently.
ON_THE_LOOP = (
    "core/brand-ref.json",
    "brand.json",
    "core/identity-relying-party.json",
)


def _population() -> list[str]:
    """The set every check below ranges over: bundle 3.3's portable documents.

    Named through :func:`tests.nodeset.claimed` because three of the four checks are
    NEGATIVE -- no cycle, no new refusal, no cycle in the bundle's own graph -- and a
    negative over an empty set is the one shape section 8 forbids outright.
    """
    population = sorted(bundle.portable(SECOND))
    claimed("bundle 3.3 portable documents", population)
    return population


def _compiled():
    """One compile of the second bundle's whole portable population, shared on disk.

    ``tests.compiled`` holds it under a digest over the bundle's bytes, the population and
    every ``.py`` of ``codegen/``, so the figure below is what the loop pays per compiler
    revision and not per test: **72.0 s cold over 1,138 portable documents**, a stat warm.
    """
    return compiled(SECOND, _population())


def test_no_document_of_the_second_bundle_refuses_on_a_reference_cycle() -> None:
    """The regression guard: 189 of 192 refusals were one loop, and it was ours.

    Read off the refusals' own ``detail``, which is the only place the compiler says a
    reference cycle stopped it (``emit.order``, ``bundle.record``'s two cycle guards).  A
    cycle the BUNDLE states would be an upstream ask and would be named here with its
    document and pointer; bundle 3.3 states none, so every member of this set is ours.
    """
    out = _compiled()
    cyclic = {document: refusal["detail"] for document, refusal in out.refusals.items() if "cycle" in refusal["detail"]}
    assert cyclic == {}, (
        f"{len(cyclic)} of {len(out.refusals)} refusals over bundle 3.3 report a reference "
        f"cycle. Bundle 3.3's own $ref graph is acyclic, so a cycle in the relation "
        f"emit.order ranges over is one the catalogue added: {cyclic}"
    )


def test_the_three_documents_on_the_loop_emit() -> None:
    """The loop is gone from the relation, stated as the three modules it cost.

    ``brand.json`` and ``core/brand-ref.json`` carried the verdict on both bundles the loop
    has been seen on -- bundle 3.3 published, and bundle 3.2 as ``patches/8525`` rewrites it
    (``adcp-client-python-6qi7``) -- and ``core/identity-relying-party.json`` is 3.3's own
    addition (``x-added-in: 3.3.0``), which is the hop that closed the loop without a patch.
    """
    out = _compiled()
    on_the_loop = claimed("the documents the loop named", ON_THE_LOOP, inside=_population())
    missing = {d: out.refusals.get(d, {}).get("detail") for d in sorted(on_the_loop) if d not in out.emitted}
    assert missing == {}, missing


def test_the_second_bundle_s_refusal_set_may_only_shrink() -> None:
    """No document joins the inventory, and the ones that left are named.

    Two directions and they are not the same claim: a document that JOINS is a regression
    and fails, and a document that LEFT is work landing and is reported so the constant can
    be shrunk rather than left to describe a state that has passed.
    """
    out = _compiled()
    joined = sorted(set(out.refusals) - REFUSES)
    assert joined == [], f"{len(joined)} document(s) of bundle 3.3 refuse and are not in REFUSES: " + ", ".join(
        f"{d} ({out.refusals[d]['keyword']} at {out.refusals[d]['pointer']})" for d in joined
    )
    ratchet(
        "bundle 3.3 refusals",
        len(out.refusals),
        at_most=len(REFUSES),
        because="REFUSES is an inventory that may only shrink; a document joining it is red above",
    )
    assert len(out.emitted) + len(out.refusals) == len(_population()), (
        len(out.emitted),
        len(out.refusals),
    )


def test_the_second_bundle_s_own_reference_graph_is_acyclic() -> None:
    """WHOSE defect the loop was, as a reading of the bundle rather than of the compiler.

    The decision in ``adcp-client-python-23cs`` turns entirely on this: if 3.3 STATED a
    recursive reference then a compiler refusing it would be our defect to fix in the
    compiler, and if 3.3 stated a loop no instance could satisfy it would be an upstream ask
    with a document and a pointer.  It states neither -- so the third hop of the loop was
    added by us and there is nothing to file upstream.

    Over ``bundle.edges``, which is the compiler's own reading of what a reference edge is,
    so this and ``emit.needs`` cannot disagree about the ``$ref`` half.
    """
    read = bundle.edges(SECOND)
    claimed("bundle 3.3 reference edges", {(e.document, e.pointer) for e in read})
    edges: dict[str, set[str]] = {}
    for edge in read:
        if edge.target is not None and edge.target != edge.document:
            edges.setdefault(edge.document, set()).add(edge.target)
        edges.setdefault(edge.document, set())
    colour: dict[str, int] = {}
    found: list[list[str]] = []

    def walk(at: str, path: list[str]) -> None:
        colour[at] = 1
        path.append(at)
        for onward in sorted(edges.get(at, ())):
            if onward not in edges:
                continue
            if colour.get(onward) == 1:
                found.append([*path[path.index(onward) :], onward])
            elif colour.get(onward) is None:
                walk(onward, path)
        path.pop()
        colour[at] = 2

    for document in sorted(edges):
        if colour.get(document) is None:
            walk(document, [])
    assert found == [], [" -> ".join(cycle) for cycle in found]
    assert edges, "no reference edge was read, so the acyclicity above is vacuous"
