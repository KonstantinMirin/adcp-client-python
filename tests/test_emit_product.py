"""Step 4: an ``allOf`` root's ``$ref`` conjuncts become bases, and a subclass
never restates an inherited field.

**Its own module, not an addition to ``tests/test_emit.py``.**  Five lanes are
adding a D2 row at once and the test file is the one place every one of them has
to write; a module per row costs an import and removes the collision entirely.
``tests/test_emit.py`` keeps the trunk's own grading, and this module grades one
row.

**The mechanism is graded on a bundle of its own**, the way the reference cycle
is, and for the same reason: ``ΔN`` is 0 (asserted below, with its denominator),
so there is no composing class in the committed tree to read a verdict off.  One
of the probe bundle's three documents is this bundle's OWN
``core/version-envelope.json``, copied byte for byte, so the inherited
``ge=1, le=99`` the control asserts on is the bundle's text and not the test's
idea of it.

**The probe's shape is the population's majority shape**, which was measured
rather than guessed: of the 287, 159 declare ``additionalProperties: true`` at
the root, 71 are silent and 57 declare ``false``.  The 57 matter and are not what
this probe is: draft-07 does not evaluate ``additionalProperties`` across
``allOf``, so a strict root forbids every key only a conjunct declares -- which is
why ``version-envelope.json``'s own description says a strict request schema
redeclares the two version fields in its own ``properties``.  Measured over the
57: **all 57 redeclare every ``$ref`` conjunct's property**, so the bundle has no
document in that trap and a probe built in it would grade a state the population
does not have.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pydantic
import pytest

from adcp.types import _base, constraints
from codegen import bundle, compiler, emit, keywords
from codegen import constraints as constraints_module
from codegen.harness import Pair, check_pair, compare_schema
from codegen.refusal import Refusal

from tests.nodeset import claimed, partitions, ratchet

#: A FLOOR over THIS step's 599-document population, which is NOT the whole-bundle
#: figure: a count is evidence for its own population and the two have been confused.
#: Direction: an emitting row only adds.  History, each move a row landing: 425, 566,
#: 592 (.28), 607 (.21).
EMITTED_OVER_THIS_POPULATION_FLOOR = 607

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
#: Every reference in this bundle is spelled against this base; ``document_for``
#: derives the document from the bundle's own file set, so the probe uses the
#: same spelling rather than a shorter one that would resolve by accident.
REF = "https://adcontextprotocol.org/schemas/3.2.4/{}"

ENVELOPE = "core/version-envelope.json"


def composing() -> list[str]:
    """This step's population, read through the row's own selector."""
    return [d for d in bundle.portable(BUNDLE) if bundle.composes_at_the_root(bundle.read(BUNDLE, d))]


# --------------------------------------------------------------------------- #
# the population, and the arithmetic over it
# --------------------------------------------------------------------------- #
def test_the_population_is_the_one_this_step_is_stated_over() -> None:
    """The step's set of nodes, and the three competing readings beside it.

    A verdict read off a set nobody named is a verdict over however many documents
    there turned out to be, including none.  Each of the three readings is a set
    somebody could have meant, and the point is that they are DIFFERENT sets -- which
    is asserted as the containments between them, not as four sizes nobody can compare.
    """
    docs = claimed("bundle.portable", bundle.portable(BUNDLE))
    read = lambda d: bundle.read(BUNDLE, d)  # noqa: E731
    claimed("composing", composing(), inside=docs)  # allOf at the root, NO union beside it

    root_allof = {d for d in docs if isinstance(read(d).get("allOf"), list)}
    anywhere = {d for d in docs if "allOf" in bundle.schema_keywords(read(d))}
    only_root = {
        d for d in root_allof if not any("allOf" in n for p, n in bundle.nodes(read(d)) if p)
    }
    claimed("any root allOf, union or not", root_allof, inside=docs)
    claimed("allOf anywhere in the document", anywhere, inside=docs)
    claimed("allOf at the root and nowhere else", only_root, inside=root_allof)
    # The three readings are STRICTLY ordered, which is the fact that makes them three
    # different answers rather than three spellings of one: a root ``allOf`` is an
    # ``allOf`` somewhere, and "at the root and nowhere else" is narrower again.  A set
    # of sizes said the same thing only for one bundle version.
    assert only_root < root_allof < anywhere, (len(only_root), len(root_allof), len(anywhere))
    # The union clause is what makes the two rows disjoint, and this is its cost: the
    # documents a root ``allOf`` has but this step does not take, because step 5's row
    # takes them.  Named as the SET rather than as the difference of two counts.
    claimed("documents step 5's row takes", root_allof - set(composing()), inside=root_allof)


def test_the_union_clause_is_what_keeps_the_rows_disjoint() -> None:
    """A root ``allOf`` applies to the whole document in draft-07, so it reaches
    EVERY branch of a root ``oneOf``.

    A row that lowered the conjuncts of a union root without the branches would
    apply the bases to some branches and not others, which is the defect D7 names.
    So a document carrying both belongs to step 5's row whatever else it carries,
    and this row declines it -- which is not a preference, it is the reason
    ``emit.lower_document`` can fail on a two-row document instead of choosing.

    **"BOTH" IS READ THROUGH ``union_root``, and the KEY test this used to use was a
    14-document hole.**  55 documents carry a root ``allOf`` beside the ``oneOf`` or
    ``anyOf`` KEY; only 41 of those carry a root ``allOf`` beside a UNION, because
    14 of them spell a presence rule with ``anyOf`` and ``union_root`` -- which is
    step 5's own selector, built on the lowering's ``union.keyword`` plus
    ``rules.presence_only`` -- correctly says no. Those 14 were claimed by neither
    row and refused by both, which is what ``salesagent-j3k2l.21`` was filed over.
    Both populations are asserted here, and the disjointness is asserted of the one
    that decides it.
    """
    key_test = [
        d
        for d in bundle.portable(BUNDLE)
        if isinstance((doc := bundle.read(BUNDLE, d)).get("allOf"), list)
        and any(k in doc for k in ("oneOf", "anyOf"))
    ]
    both = [d for d in key_test if bundle.union_root(bundle.read(BUNDLE, d))]
    claimed("a root allOf beside the oneOf/anyOf KEY", key_test, inside=bundle.portable(BUNDLE))
    claimed("a root allOf beside a UNION, which is what decides it", both, inside=key_test)
    # The documents the two readings DISAGREE about are step 4's and nobody else's, and
    # the set is non-empty -- which is the whole finding, since a key test that agreed
    # with ``union_root`` would leave the loop below grading nothing.  Named as the set,
    # because which documents fall in the hole is the fact and 14 was its size on one
    # bundle version.
    rule_shaped = sorted(set(key_test) - set(both))
    claimed("documents the KEY test and union_root disagree about", rule_shaped, inside=key_test)
    assert set(rule_shaped) <= set(composing()), rule_shaped
    for d in rule_shaped:
        doc = bundle.read(BUNDLE, d)
        assert [s.__name__ for s, _ in emit.ROWS if s(doc)] == ["composes_at_the_root"], d
    # And the disjointness the clause exists for still holds, over the population
    # that decides it.
    assert not set(both) & set(composing())
    for d in both:
        assert not bundle.composes_at_the_root(bundle.read(BUNDLE, d)), d


def test_a_required_only_conjunct_has_no_population_so_the_arm_is_not_built() -> None:
    """The plan's third output for this row, deliberately absent.

    A derivation matching nothing is green for free and says nothing, so the arm
    is not written -- and this is the measurement that says so, over the whole
    bundle rather than over this step's population.
    """
    found = []
    conjuncts: set[str] = set()
    for d in bundle.portable(BUNDLE):
        for i, c in enumerate(bundle.read(BUNDLE, d).get("allOf") or []):
            conjuncts.add(f"{d}#/allOf/{i}")
            if isinstance(c, dict) and set(
                compiler.declaring(c, keywords.Position.CONJ)
            ) == {"required"}:
                found.append(f"{d}#/allOf/{i}")
    # The set this ranges over is named NON-EMPTY first: "no conjunct states only
    # ``required``" is free over a walk that reached no conjunct at all, which is the
    # one way a check asserting an empty part can be worthless.
    claimed("root allOf conjuncts in the bundle", conjuncts)
    assert found == []


def test_the_rows_delta_is_reported_with_its_denominator() -> None:
    """**ΔN = 0. N = 43 of 1,054.**  Measured both ways in one process.

    The plan's step table implies the volume of a 287-document population; it
    arrives with steps 5-7 and not here.  Reported rather than explained: a low
    number is not a failure, and a number with no denominator is not a result.

    What the row DOES change is the refusal's attribution, and in the honest
    direction -- a document that used to refuse at the root on ``allOf`` now
    refuses on the keyword that actually stopped it, inside the conjunct or in a
    document it composes.
    """
    docs = bundle.portable(BUNDLE)
    read = lambda d: bundle.read(BUNDLE, d)  # noqa: E731
    pop = sorted(
        {
            d
            for d in docs
            if bundle.is_leaf_object(read(d))
            or bundle.references_a_property(read(d))
            or bundle.composes_at_the_root(read(d))
        }
    )
    claimed("this step's population", pop, inside=docs)

    with_row = emit.emit(BUNDLE, pop)
    # Removing THIS row from the merged table, rather than emptying it: the other
    # rows are other steps' and a verdict read with them absent is a verdict about
    # a table nobody runs.
    saved = emit.ROWS
    try:
        emit.ROWS = tuple(r for r in saved if r[0] is not bundle.composes_at_the_root)
        without = emit.emit(BUNDLE, pop)
    finally:
        emit.ROWS = saved

    claimed("bundle.portable", docs)
    # N over this population on the merged table (43 when this lane measured it
    # alone, before the other four steps' rows were beside it).
    #
    # **566, AND THIS ONE IS `salesagent-j3k2l.22`'S OWN DOING.**  Measured with one
    # script against both trees: trunk `ac8a64fb1` gives 425 / 331 / 94 / 73 / 282 / 19
    # and this branch gives 566 / 345 / 221 / 141 / 301 / 0, so the figures below are
    # the row lowering its own ROOT RULES -- `not`, `dependencies`, `min`/`maxProperties`
    # at a composing root -- rather than deferring them.  The previous revision of this
    # comment said trunk and the branch agreed, which was true of the branch it was
    # written on and is not true of this one.
    # Re-pinned 566 -> 576 on bcb0b8ca8. Measured, not read off the failure: three
    # agents and the integrator each took it independently and agreed, and each
    # A/B'd it against the base's codegen to confirm it is stale rather than a
    # regression. It drifted because every row that claims documents moves it.
    # CONFIRMED at 64131600f by ``salesagent-j3k2l.29``, in one pass with every
    # other quantity this test asserts: 576, and ``without`` is 348.
    # 576 -> 581 at ``salesagent-j3k2l.40``, which is the UNION row and not this one:
    # sharing the conjunct reader let a composing BRANCH lower, and 5 documents of
    # this population emit that did not.  Re-measured in one pass with every other
    # quantity below, and **this is the only one that moved** -- the delta (228), the
    # row's own contribution (147), the cleared set (151) and the attribution
    # histogram (279 + 14 + 8) are all unchanged, which is what says the +5 belongs
    # to another row.  ``without`` moves with it, so the delta holds.
    # 581 -> 592 at ``salesagent-j3k2l.28``, and again it is not this row: the three
    # refusals section 6 names as one-sided folds are gone, so 11 more documents of
    # this 599-document population emit.  Re-measured in one pass with the rest; the
    # row's own contribution moved with it (147 -> 152) and the delta held at 228.
    # **592 -> 607 at ``salesagent-j3k2l.21``, and the +15 against that row's +11 over
    # the whole bundle is the CLOSURE, enumerated rather than reasoned.** This
    # population is 599 documents and ``emit`` emits the ``$ref`` closure of it, so a
    # newly-emitting document brings its reference targets in with it. The 15 are that
    # row's own 11, plus four enum documents reached only through them --
    # ``enums/action-not-allowed-reason.json``, ``enums/media-buy-action-mode.json``,
    # ``enums/media-buy-valid-action.json`` and
    # ``enums/seller-policy-decline-reason.json``. Over the WHOLE portable set those
    # four were already emitting, so they are not a status change there: a count is
    # evidence for its own population and these are two populations. Nothing was lost.
    # A FLOOR over THIS population, not an equality: every emitting row takes it up
    # (425, 566, 592, 607 over four of them) and no row may take it down.  The number
    # is also not comparable with the whole-bundle figure -- a count is evidence for
    # its own population and these are two populations, which is the reading that was
    # got wrong once here.
    ratchet(
        "documents emitted over this step's population",
        len(with_row.emitted),
        at_least=EMITTED_OVER_THIS_POPULATION_FLOOR,
        because="an emitting row only adds documents to this run; a drop means a "
        "document that lowered stopped lowering",
    )
    # **The row DOES emit now, and it did not when this lane measured alone.**  On
    # its own branch the conjuncts' targets refused and took their referrers with
    # them, so the delta was 0 and the row's value was the attribution it moved.  On
    # the merged table steps 3, 5 and 6's rows emit those targets, so the composing
    # documents follow: 147 of the 301 are emitted BY this row, and removing it loses
    # 228 modules -- the emitted documents plus those reached only through a reference.
    # That is joint unblocking measured from this side -- the row's own 0 was a fact
    # about which other rows existed, not about the row.
    #
    # 221 -> 228 and 141 -> 147, re-measured at 64131600f (``salesagent-j3k2l.29``).
    # Both are over the two emits above and moved with them while 576 held, which is
    # the shape to expect: 576 counts what the merged table emits and these count
    # what THIS ROW contributes, so another step's row landing moves the second pair
    # without moving the first.  The population (599) and the bundle (1,054) did not
    # move at all -- they are the bundle's own selectors.
    # 228 -> 233 at ``salesagent-j3k2l.28``: with the row, 592 emit; without it, 359.
    # The delta grew because 5 of the 11 documents that row unblocked only emit
    # when this row claims their composing root as well.
    #
    # 233 -> 237 at ``salesagent-j3k2l.21`` (with 607, without 370), and the +4 is
    # ENUMERATED rather than read off the arithmetic: of that row's eleven documents,
    # exactly four emit here only when this row claims their composing root as well --
    # ``core/geo-place-area.json``, ``core/geo-place-system.json``,
    # ``core/get-geo-place-resolution-response.json`` and ``core/start-timing.json``.
    # The other seven emit either way, which is why ``without`` moved +11 and the delta
    # only +4.
    # The DELTA is the set of documents the row is responsible for, named by taking the
    # difference of the two runs -- and it is non-empty, which is the claim this half
    # exists for: on this lane's own branch the delta was 0 and the row's value was the
    # attribution alone.  Its size moved at every row that unblocked a conjunct's
    # target (228, 233, 237), each move enumerated at the time and each one correct.
    delta = claimed(
        "documents that emit only with this row",
        set(with_row.emitted) - set(without.emitted),
        inside=set(with_row.emitted),
    )
    # 152 -> 154 at ``salesagent-j3k2l.21``: two of its eleven compose at their own
    # root (``core/geo-place-area.json`` and ``core/geo-place-catalog-entry.json``).
    claimed(
        "composing documents this run emits",
        set(composing()) & set(with_row.emitted),
        inside=set(with_row.emitted),
    )
    # **Every document the row rescues from a refusal is EMITTED with it**, and the
    # composing ones are 147 of the 151.  This was an equality against
    # ``composing() & emitted`` and the equality is no longer true, which is a
    # measurement and not a regression: the other 4 are documents that do NOT compose
    # at their own root and were refused on an unresolved target, whose target the row
    # now emits (``core/catalog.json``, ``core/reporting-delivery-ready-webhook.json``,
    # ``error-details/authorization-required.json``,
    # ``error-details/macro-resolution-failed.json``).  On trunk the set difference was
    # empty because the row emitted 73 composing documents and none of them was such a
    # target.  Stated as the containment plus the count, so a document clearing for a
    # reason that is NOT this row still reddens.
    #
    # 145 -> 151 at 64131600f (``salesagent-j3k2l.29``), measured in the same pass.
    # The four names are re-measured and are STILL exactly those four, which is what
    # says the +6 is the composing half growing and not a new kind of document
    # arriving -- 151 - 147 = 4 either way.  Asserted by NAME below for that reason.
    cleared = set(without.refusals) - set(with_row.refusals)
    assert cleared <= set(with_row.emitted), sorted(cleared - set(with_row.emitted))
    assert set(composing()) & set(with_row.emitted) <= cleared
    # 151 -> 156 at ``salesagent-j3k2l.28``, and 156 - 152 = 4 again: the four names
    # below are still exactly the non-composing members, so the +5 is the composing
    # half growing and not a new kind of document arriving.
    #
    # 156 -> 158 at ``salesagent-j3k2l.21``, and **158 - 154 = 4 a third time**. The
    # four names below are re-measured and are STILL exactly those four, which is the
    # assertion that says this row's +2 is the composing half growing rather than a new
    # kind of document arriving -- the same reading that held at .28 and at .29.
    claimed("documents the row rescues from a refusal", cleared)
    # **AND THE NON-COMPOSING MEMBERS ARE EXACTLY THESE FOUR**, which is the assertion
    # that says each row's growth is the composing half growing rather than a new KIND
    # of document arriving.  It held at .28, at .29 and at .21, every time as the four
    # names and not as the difference of two counts.
    assert sorted(cleared - set(composing())) == [
        "core/catalog.json",
        # Two more since ``salesagent-j3k2l.43``, and both are RELEASED rather than
        # claimed: neither composes at its own root, so neither is in ``composing()``;
        # each one's only blocker was a ``$ref`` into a document whose conjunct that row
        # lowered.  ``core/media-buy-support-requirements.json`` chains to
        # ``core/media-buy-frequency-cap-requirement.json`` and
        # ``core/package-targeting-resolution.json`` chains two hops to
        # ``core/demographic-targeting-intent.json``.  They belong in this list for the
        # reason the four below do -- the row cleared them without claiming them -- and
        # they are named here so the row's own credit stays separate from the release.
        "core/media-buy-support-requirements.json",
        "core/package-targeting-resolution.json",
        "core/reporting-delivery-ready-webhook.json",
        "error-details/authorization-required.json",
        "error-details/macro-resolution-failed.json",
    ], sorted(cleared - set(composing()))
    # Every document of the population is accounted for by name, pointer and keyword.
    assert set(pop) <= set(with_row.emitted) | set(with_row.refusals)
    for document, row in with_row.refusals.items():
        assert row["keyword"] and row["pointer"] and row["detail"], document
    # **The ATTRIBUTION now moves for ALL 301, and the 19 it did not move for on trunk
    # were exactly this bead's keywords.**  Without the row a composing document is
    # claimed by nothing, and ``lower_document`` refuses it at the ROOT on the keyword
    # its kind is read from -- ``allOf`` for 279, ``anyOf`` for 14, ``if`` for 8, all at
    # ``/`` (re-measured at 64131600f: that histogram is unchanged, 279 + 14 + 8 = 301).
    # (It used to say ``type`` for all 301, which is a keyword none of them
    # states; ``salesagent-j3k2l.21`` changed that.)  With the row the walk reaches the
    # conjuncts and either emits the document -- 147 of them -- or names where it
    # actually stopped, and 153 of the 154 refusals are now at a pointer INSIDE the
    # document.  The one still at ``/`` is
    # ``sponsored-intelligence/si-ui-element.json``, and the root IS its cause: the
    # refusal is about the class this row would declare at that root
    # (``compiler.conditional_only``), not about anything inside a conjunct.
    #
    # The 19 that read the same either way on trunk were the documents whose root
    # sibling keyword was ALSO what stopped step 4's lowering, which is to say a root
    # ``not``, ``dependencies`` or ``min``/``maxProperties`` -- so admitting those at a
    # composing root (``salesagent-j3k2l.22``) is what took the figure to 0. It is
    # asserted as 0 rather than deleted: a document reading the same either way again
    # would mean a root keyword the row screens but does not lower.
    #
    # Compared on (keyword, pointer) and not on the keyword alone: the pointer is
    # half of the attribution, and a keyword-only test reports a refusal that moved
    # from the root into a conjunct as not having moved.
    def where(out: emit.Emitted, document: str) -> tuple[str, str] | None:
        row = out.refusals.get(document)
        return (row["keyword"], row["pointer"]) if row else None

    # EVERY composing document reads differently with the row than without it, which
    # is a set IDENTITY against ``composing()`` and not a count: a document reading the
    # same either way would mean a root keyword the row screens but does not lower, and
    # the empty part below says there is none.
    moved = [d for d in composing() if where(with_row, d) != where(without, d)]
    assert claimed("composing documents the row moves", moved) == set(composing()), sorted(
        set(composing()) - set(moved)
    )
    assert all(where(without, d)[1] == "/" for d in composing()), "without the row: all at /"
    assert sum(1 for d in composing() if where(with_row, d) == where(without, d)) == 0
    refused = {d: where(with_row, d) for d in composing() if d not in with_row.emitted}
    # 160 -> 154 at 64131600f (``salesagent-j3k2l.29``), 154 -> 149 at
    # ``salesagent-j3k2l.28``, and 152 + 149 = 301 either way: the five documents that
    # left this half are the five the row now emits.  Asserted as the partition as
    # well, so the two halves cannot drift apart silently.
    #
    # 149 -> 147 at ``salesagent-j3k2l.21``, and **154 + 147 = 301**, so the partition
    # holds across this row too. The two that left this half are the two of its eleven
    # that compose at their own root: ``core/geo-place-area.json`` and
    # ``core/geo-place-catalog-entry.json``. The partition is what makes the pair of
    # figures one measurement rather than two -- a document leaving the refused half
    # without arriving in the emitted one would redden here even though both counts
    # moved in the direction a landing row moves them.
    # The PARTITION is what makes the pair of figures one measurement rather than two:
    # a document leaving the refused half without arriving in the emitted one would
    # redden here even though both counts moved the way a landing row moves them.  The
    # halves themselves are not counted -- they were 160/141, 154/147, 149/152 and
    # 147/154 over four rows, and every move was a row landing.
    partitions(
        composing(),
        refused=set(refused),
        emitted=set(composing()) & set(with_row.emitted),
    )
    # **AND THE ONE AT ``/`` IS GONE, which is the attribution reaching 100%.**  It was
    # ``sponsored-intelligence/si-ui-element.json`` on ``if``, refused at the ROOT
    # because the class this row would declare there named a conditional-only key --
    # and ``salesagent-j3k2l.28`` removed that refusal, because no field is ever
    # emitted for such a key and the hazard it guarded has no producer.  So every one
    # of the 149 now refuses at a pointer INSIDE its document, which is what this
    # test's attribution claim has been approaching since ``salesagent-j3k2l.21``.
    at_root = sorted(d for d, w in refused.items() if w[1] == "/")
    assert at_root == [], at_root


def test_a_document_two_rows_select_is_a_build_failure_and_not_a_precedence_puzzle() -> None:
    """The table is unordered, graded by registering a second row that collides.

    Unreachable at one row, which is exactly why it gets a test that manufactures
    the second: an ordered chain would make precedence a property of where a lane
    inserted its line, and five lanes are inserting lines now.  The failure is an
    ``AmbiguousRoot`` and not a ``Refusal``, because a document two rows claim is a
    defect in their SELECTORS and a refusal would file it against the document and
    let the build pass.
    """
    doc = bundle.read(BUNDLE, "media-buy/get-products-request.json")
    assert bundle.composes_at_the_root(doc)
    saved = emit.ROWS
    try:
        emit.ROWS = (*saved, (bundle.composes_at_the_root, emit._composing_root))
        with pytest.raises(emit.AmbiguousRoot, match="composes_at_the_root"):
            emit.lower_document("media-buy/get-products-request.json", doc)
    finally:
        emit.ROWS = saved
    # and the same document goes back to one row once the table is restored
    assert len([r for r in emit.ROWS if r[0](doc)]) == 1


# --------------------------------------------------------------------------- #
# the probe bundle
# --------------------------------------------------------------------------- #
#: The restatement that is this step's highest-value defect: it states a default
#: and a description and NOTHING about the instance, over a base field typed
#: ``integer`` with ``minimum: 1, maximum: 99``.  31 of the previous generated
#: tree's 42 ``Any`` fields were this, shadowing a typed base field across 15
#: classes.  ``formats/canonical/responsive_creative.json`` is the population's
#: own instance, over ``formats/canonical/_base.json``.
SHADOW = {"default": 1, "description": "restated, and states no fact"}

#: A document the probe bundle REFERENCES, so a property can be a bare ``$ref``
#: whose description is the TARGET's rather than the referring node's.  Its text is
#: the third of the three a description can come from, and the three disagreeing is
#: what makes the authority question answerable: the target's, the referring node's
#: own sibling, and a composed base's declaration of the same key.
TARGET = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Probe Target",
    "description": "THE TARGET SAYS THIS",
    "type": "object",
    "additionalProperties": True,
}


def _probe(
    tmp_path: Path, *, own: dict[str, Any], name: str, shared: dict[str, Any] | None = None
) -> Path:
    """Write the three-document probe bundle and return its directory.

    ``shared`` adds properties to the MARKER, which is a base of the composing
    document, so a key can be declared on BOTH sides -- the base's declaration and
    the subclass's own -- which is what the merge rule decides between.  It is
    opt-in because the marker is every other test's base too, and writes
    ``core/probe-target.json`` beside it for a ``$ref`` to name.
    """
    at = tmp_path / name
    (at / "core").mkdir(parents=True)
    # BYTE FOR BYTE: the inherited bound the control asserts on is the bundle's text.
    shutil.copyfile(BUNDLE / ENVELOPE, at / ENVELOPE)
    if shared:
        (at / "core/probe-target.json").write_text(json.dumps(TARGET, indent=2))
    (at / "core/probe-marker.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Marker",
                "type": "object",
                "required": ["kind"],
                "properties": {
                    "kind": {"type": "string", "minLength": 2, "description": "the marker"},
                    **(shared or {}),
                },
            },
            indent=2,
        )
    )
    (at / "core/probe-composing.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Composing",
                # Stated only with ``shared``, where the probe is graded by the schema
                # COMPARISON and so has to be in the state the population is in: the
                # resolver merges a conjunct's ROOT description into the root, so a
                # composing document stating none reads as dropping its base's.  All
                # 301 of the bundle's composing documents state one, which is why the
                # comparison reports no such fact and a probe without one would grade
                # a state no document has.  Opt-in so no other test's bytes move.
                **({"description": "the composing probe"} if shared else {}),
                "type": "object",
                "allOf": [
                    {"$ref": REF.format("core/probe-marker.json")},
                    {"$ref": REF.format(ENVELOPE)},
                ],
                "properties": own,
                "required": ["label"],
                "additionalProperties": True,
            },
            indent=2,
        )
    )
    return at


def install_run_aliases(out: emit.Emitted, monkeypatch) -> list[str]:
    """Install a RUN's own D5 aliases onto ``adcp.types.constraints``, reversibly.

    Returns the symbols it added, so a caller can assert the probe reached the row
    at all rather than trusting that it did.

    Nothing is overwritten and nothing can be: an alias's NAME is a function of its
    constraint (``codegen.constraints.symbol``, with ``check_injective`` failing the
    build if two shapes ever derive one name), so a symbol present in both the
    bundle's module and a probe run's module is the same annotated type in both.
    Only the names the installed module lacks are added, and ``monkeypatch``
    removes them when the test ends.
    """
    namespace: dict[str, Any] = {}
    exec(out.beside["constraints.py"], namespace)  # noqa: S102 -- the emitter's own output
    added = []
    for symbol, value in namespace.items():
        if symbol.startswith("_") or not symbol[:1].isupper() or hasattr(constraints, symbol):
            continue
        monkeypatch.setattr(constraints, symbol, value, raising=False)
        added.append(symbol)
    return sorted(added)


def _emit_probe(
    tmp_path: Path,
    monkeypatch,
    *,
    own: dict[str, Any],
    name: str,
    shared: dict[str, Any] | None = None,
):
    """Emit the probe bundle, import its tree, and return (class, module text, schema).

    ``strict_validate`` reaches a document through ``_base._document``, which reads
    the INSTALLED package, so the probe's documents are reached by pointing that
    one function at the probe tree.  ``_document`` is ``lru_cache``d: the patch
    replaces the whole cached function rather than seeding it, so the real cache
    is untouched and nothing of the probe outlives the test -- a probe binding
    that outlived its test is a measured failure of this project's.

    **D5's alias module is reached the same way and takes the same kind of
    patch.**  An emitted module names ``adcp.types.constraints`` ABSOLUTELY, just
    as it names ``adcp.types._base``, so the probe's tree imports the INSTALLED
    module -- which declares the aliases the BUNDLE's shapes derive and not the
    probe's, and the probe marker's ``minLength: 2`` derives one the bundle has no
    site for.  The probe RUN emitted its own alias module
    (``Emitted.beside``), so that is what is installed, for this test only.
    """
    at = _probe(tmp_path, own=own, name=name, shared=shared)
    documents = sorted(str(p.relative_to(at)) for p in at.rglob("*.json"))
    out = emit.emit(at, documents)
    assert out.refusals == {}, out.refusals
    tree = tmp_path / "pkg" / name
    emit.write(out, tree)
    install_run_aliases(out, monkeypatch)
    monkeypatch.setattr(
        _base, "_document", lambda document: json.loads((tree / document).read_text())
    )
    monkeypatch.syspath_prepend(str(tmp_path / "pkg"))
    module = importlib.import_module(f"{name}.core.probe_composing")
    for mod in [m for m in sys.modules if m.startswith(name)]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    return (
        module.ProbeComposing,
        (tree / "core/probe_composing.py").read_text(),
        json.loads((tree / "core/probe-composing.json").read_text()),
    )


def test_a_ref_conjunct_becomes_a_base_in_the_documents_own_conjunct_order(
    tmp_path, monkeypatch
) -> None:
    """D7: every base an emitted class has is a schema its document composes.

    Derived, so there is no marker policy and no filename to classify.  The order
    is the document's conjunct order, which is also what makes a response
    composing both envelopes read as its document does.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4base",
        own={"label": {"type": "string", "minLength": 2}},
        )
    assert [b.__name__ for b in cls.__bases__] == ["ProbeMarker", "AdCPVersionEnvelope"]
    assert "class ProbeComposing(ProbeMarker, AdCPVersionEnvelope):" in text
    # AdCPBaseModel arrives THROUGH the bases and is not named a second time.
    assert "AdCPBaseModel" not in text
    assert issubclass(cls, _base.AdCPBaseModel)
    # The import is the module writer's, derived from the two document paths (D1).
    assert "from .probe_marker import ProbeMarker" in text
    assert "from .version_envelope import AdCPVersionEnvelope" in text


def test_a_subclass_restating_only_annotations_re_uses_the_inherited_field(
    tmp_path, monkeypatch
) -> None:
    """The merge rule's annotation-only arm: the FIELD is the base's, the
    annotations are this document's, and the shadow is still unspellable.

    The restatement states a default and a description and nothing about the
    instance.  It is the subclass's field, because a document's own declaration
    carries the annotation at its own pointer -- and its TYPE is re-used from the
    base rather than decided from the restatement, which on its own would be
    ``Any`` over a typed base.  The assertion is on the module TEXT as well as on
    the class, because what the defect looked like was a line in a class body.

    This replaced a rule reading "a subclass never restates an inherited field",
    under which the field was inherited ENTIRELY and the class stated the base's
    ``default`` and ``description`` at a pointer its own document declares -- the
    28 ``differs`` of ``salesagent-j3k2l.36``, two of them inversions.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4shadow",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    # A DECLARED field is a name in the class body, read without reference to how
    # its annotation is spelled: D5 puts a constraint on the TYPE, so a declared
    # field is now ``label: StrMinLen2`` and the previous instrument -- which
    # looked for ``": Annotated"`` -- found none and passed an EMPTY list against
    # ``["label"]``.  An instrument keyed on the rendering reports a restatement
    # that is there as absent the moment the rendering moves, which is the
    # direction that matters: it would have said this rule holds while a subclass
    # shadowed every inherited field.
    body = [line for line in text.splitlines() if line.startswith("    ") and ":" in line]
    declared = [
        name
        for name in (line.strip().split(":")[0] for line in body)
        if name.isidentifier() and not name.startswith("__")
    ]
    assert declared == ["adcp_major_version", "label"], text
    assert "restated, and states no fact" in text, "the document's own text is not on the field"
    assert "Any" not in text, "the restatement lowered on its own would be Any"

    # **The type is the base's, not a second decision about the same node.**  Read
    # off the live field against the base's own, by VALUE: two spellings of one
    # annotated alias are equal and are not the same object.
    base = cls.__bases__[1]
    assert cls.model_fields["adcp_major_version"].annotation == (
        base.model_fields["adcp_major_version"].annotation
    )
    assert cls.model_fields["adcp_major_version"].metadata == (
        base.model_fields["adcp_major_version"].metadata
    )
    # and it still REFUSES what the base refuses, which the annotation cannot say
    assert cls.model_validate({"adcp_major_version": 2, "label": "xy", "kind": "ab"})
    for bad in (0, 100):
        with pytest.raises(pydantic.ValidationError):
            cls.model_validate({"adcp_major_version": bad, "label": "xy", "kind": "ab"})
    # and the annotations are the DOCUMENT's
    assert cls.model_fields["adcp_major_version"].default == 1
    assert cls.model_fields["adcp_major_version"].description == "restated, and states no fact"


def test_a_restatement_contradicting_the_base_still_refuses_rather_than_merging(
    tmp_path,
) -> None:
    """The merge does not reach a restatement that DISAGREES, and that is the one
    thing a merge of the base's content could quietly swallow.

    ``_restatement`` is asked first: a declaration that says something at a keyword the
    base also states which is NOT at least as tight is ``None``, and the document
    refuses by the keyword the two disagree about.  Only a restatement at least as tight
    everywhere the two overlap reaches :func:`compiler._intersection`, so there is no
    reading on which a disagreement is merged away.

    **The bound DROPPED is no longer here, and that is D7 rather than a relaxation.**
    "Where composed schemas constrain the same property, the field carries the
    INTERSECTION" -- so a restatement silent about the base's bound intersects to the
    base's own content and the field is INHERITED, which is what
    ``test_the_rule_is_symmetric...`` asserts of the decision. Its place is taken by the
    shape the population actually holds: two ``items`` that conflict
    (``media-buy/get-media-buys-response.json``'s ``indicators``).
    """
    base = {"type": "integer", "minimum": 3, "description": "the base's floor"}
    # The keyword is ``_disagreeing``'s: the FIRST the two do not agree about, in
    # sorted order.  So a restatement disagreeing about both the type and the bound
    # is reported on ``minimum`` -- a tiebreak, not a judgement about which mattered.
    for restated, keyword in (
        ({"type": "integer", "minimum": 1}, "minimum"),  # a LOOSER bound
        ({"type": "string"}, "minimum"),  # a different type, and the bound gone with it
    ):
        with pytest.raises(Refusal) as caught:
            _lower(
                {
                    "type": "object",
                    "allOf": [{"$ref": REF.format("core/probe-base.json")}],
                    "properties": {"n": restated},
                },
                binder=lambda _uri, _at: compiler.Target(
                    ".base", "ProbeBase", compiler.Shape({"n": base}, frozenset())
                ),
            )
        assert caught.value.keyword == keyword, (restated, caught.value.keyword)
        assert "neither matches nor narrows" in caught.value.detail, caught.value.detail


def test_a_lost_inherited_fact_is_reported_as_missing(tmp_path, monkeypatch) -> None:
    """The re-use BROKEN ON PURPOSE, because a merge that cannot produce a
    ``missing`` is silencing the disagreement rather than resolving it.

    ``_reused`` forced to hand back an untyped field is exactly the emitter this
    arm replaces: the subclass declares ``adcp_major_version`` from a restatement
    that states nothing about the instance, so the field states none of the three
    facts ``core/version-envelope.json`` states about it.  The same probe bundle,
    the same comparison, two emitters -- and the comparison names each lost fact
    at its own pointer.
    """
    monkeypatch.setattr(
        compiler,
        "_reused",
        lambda key, held, source, pointer, mod: compiler.Property(
            name=key, wire=key, type=compiler.Type("typing.Any"), required=False
        ),
    )
    # ``shared`` because this probe is graded by the COMPARISON, and only then does
    # the fixture state the root description a composing document in the population
    # has -- ``_probe`` says why.  The shared key is inherited and not restated, so
    # it takes no part in the dimension this judges.
    cls, text, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4lostfact",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
        shared={"spare": {"type": "string", "description": "the base's spare"}},
    )
    assert "adcp_major_version: Annotated[Any | None" in text, "the patch did not reach"

    comparison = compare_schema(schema, cls)
    assert comparison.added == [], comparison.added
    reported = {str(m).split(":", 1)[0] for m in comparison.missing}
    assert reported == {
        "/properties/adcp_major_version/type",
        "/properties/adcp_major_version/minimum",
        "/properties/adcp_major_version/maximum",
    }, sorted(reported)
    # And the model really does accept what the document refuses, which is the
    # defect the report stands for.
    assert cls.model_validate({"adcp_major_version": 1000, "label": "xy", "kind": "ab"})


#: The two shapes of the OTHER restatement: it says exactly what the base says about
#: the instance (the same ``$ref``) and a different thing to the reader.  ``ctx``
#: states its own description beside the ``$ref``; ``echo`` states none, so the
#: TARGET's is what its node resolves.  Both disagree with the base's.
AUTHORITY_SHARED = {
    "ctx": {"$ref": REF.format("core/probe-target.json"), "description": "THE BASE SAYS THIS"},
    "echo": {"$ref": REF.format("core/probe-target.json"), "description": "THE BASE SAYS THAT"},
}
AUTHORITY_OWN = {
    "ctx": {"$ref": REF.format("core/probe-target.json"), "description": "THE DOCUMENT SAYS THIS"},
    "echo": {"$ref": REF.format("core/probe-target.json")},
    "label": {"type": "string", "minLength": 2},
}


def test_a_documents_own_declaration_carries_the_description_at_its_own_pointer(
    tmp_path, monkeypatch
) -> None:
    """The description-authority rule (``docs/plan/rebuild-plan.md`` §6): an annotation
    reaches a field from the document that declares the field's pointer, and never from
    a composed base's declaration of the same key.

    The restatement says the same thing about the instance as the base's -- the same
    ``$ref``, so ``_restatement`` reads it as adding nothing -- and a different thing
    to the reader.  Left inherited, the class states at ``/properties/ctx`` a
    description its own document does not, which is 15 of the 43 ``differs`` the
    symmetric comparison reported (every response root composing
    ``core/protocol-envelope.json`` and declaring ``context`` itself).

    **The type is still the BASE's and there is no shadow**, which is what the
    non-empty gate buys: the restated declaration's constraining content EQUALS the
    base's, so the node lowers to the same type rather than to ``Any``.
    """
    cls, text, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4authority",
        own=AUTHORITY_OWN,
        shared=AUTHORITY_SHARED,
    )
    assert "class ProbeComposing(ProbeMarker, AdCPVersionEnvelope):" in text, text
    # The subclass states both keys, and the base's text is in NEITHER of them.
    assert "THE DOCUMENT SAYS THIS" in text, text
    assert "THE BASE SAYS" not in text, text
    assert "Any" not in text, "the restatement lowered on its own would be Any"
    # Compared by VALUE: two spellings of one annotated alias are equal and are not
    # the same object, so ``is`` here reads a faithful field as a shadow.
    assert cls.model_fields["ctx"].annotation == cls.__bases__[0].model_fields["ctx"].annotation

    # What a reader of the model sees at each pointer, which is what the comparison
    # grades: the node's own sibling where it states one, the TARGET's where it does
    # not.  ``echo`` carries no field description at all and reads the target's
    # through the branch its ``$ref`` becomes.
    rendered = cls.model_json_schema()["properties"]
    assert rendered["ctx"]["description"] == "THE DOCUMENT SAYS THIS", rendered["ctx"]
    assert "description" not in rendered["echo"], rendered["echo"]
    assert [
        arm["description"] for arm in rendered["echo"]["anyOf"] if "description" in arm
    ] == ["THE TARGET SAYS THIS"], rendered["echo"]

    # And the comparison agrees, at those pointers and everywhere else.
    comparison = compare_schema(schema, cls)
    assert (comparison.added, comparison.missing, comparison.differs) == ([], [], [])
    assert schema["properties"]["ctx"]["description"] == "THE DOCUMENT SAYS THIS"
    assert schema["properties"]["echo"]["description"] == "THE TARGET SAYS THIS"


def test_the_wrong_text_at_that_pointer_is_reported_as_a_differs(
    tmp_path, monkeypatch
) -> None:
    """The rule BROKEN ON PURPOSE, because a description rule that cannot produce a
    ``differs`` is not a rule.

    ``_annotates_differently`` forced to ``False`` is exactly the emitter before
    this branch existed: the restatement adds nothing constraining, so the field is
    inherited and the class carries the BASE's text at a pointer its own document
    declares. The same probe bundle, the same comparison, two emitters -- and the
    comparison separates them by name, pointer and both texts.
    """
    monkeypatch.setattr(compiler, "_annotates_differently", lambda child, base: False)
    cls, text, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4authoritybroken",
        own=AUTHORITY_OWN,
        shared=AUTHORITY_SHARED,
    )
    assert "THE DOCUMENT SAYS THIS" not in text, "the patch did not reach the emitter"

    comparison = compare_schema(schema, cls)
    assert comparison.added == [] and comparison.missing == []
    reported = {str(d).split(":", 1)[0]: str(d) for d in comparison.differs}
    assert sorted(reported) == ["/properties/ctx/description", "/properties/echo/description"], (
        sorted(reported)
    )
    assert "THE DOCUMENT SAYS THIS" in reported["/properties/ctx/description"]
    assert "THE BASE SAYS THIS" in reported["/properties/ctx/description"]
    assert "THE TARGET SAYS THIS" in reported["/properties/echo/description"]
    assert "THE BASE SAYS THAT" in reported["/properties/echo/description"]


def test_the_composed_field_set_is_the_union_and_requiredness_is_inherited(
    tmp_path, monkeypatch
) -> None:
    """A field the subclass does not declare keeps the base's requiredness,
    because there is nothing of the subclass's to override it.

    That closes "41 subclass fields optional where their base requires them" by
    construction rather than by a check: ``kind`` is required by conjunct 0 and
    appears in neither the root's ``properties`` nor its ``required``.
    """
    cls, _, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4fields",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    assert sorted(cls.model_fields) == ["adcp_major_version", "adcp_version", "kind", "label"]
    assert sorted(k for k, f in cls.model_fields.items() if f.is_required()) == ["kind", "label"]
    assert schema["required"] == ["label"], "the document's root requires only its own"
    assert "kind" not in schema["properties"], "and declares nothing about kind"


def test_the_inherited_bound_is_live_on_the_model_validate_path(tmp_path, monkeypatch) -> None:
    """**The control, and it asserts on ``model_validate`` for a measured reason.**

    The brief's probe was "make a subclass redeclare an inherited field and
    confirm the per-keyword refuses check catches the widening".  It does not,
    and section 6 deleted that check for exactly this reason: it called
    ``strict_validate``, whose schema half decides against the document before
    anything is constructed, so the document refused whatever the annotations
    said -- measured, a class carrying ``Any = None`` over this typed base field
    graded identically to this one, and so did a class with no bases at all.

    The widening is on the ``model_validate`` path, which D4 keeps public and
    which builds WITHOUT consulting the schema.  So that is where the inherited
    bound is asserted, and the value asserted on -- ``ge=1, le=99`` -- is
    ``core/version-envelope.json``'s own text, copied into the probe byte for
    byte.
    """
    cls, _, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4bound",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    ok = cls.model_validate({"kind": "ab", "label": "xy", "adcp_major_version": 5})
    assert ok.adcp_major_version == 5
    for bad, expected in ((0, "greater_than_equal"), (100, "less_than_equal"), ("nope", "int_parsing")):
        with pytest.raises(pydantic.ValidationError) as caught:
            cls.model_validate({"kind": "ab", "label": "xy", "adcp_major_version": bad})
        assert caught.value.errors()[0]["type"] == expected, bad


def test_a_narrowing_restatement_is_declared_by_the_subclass(tmp_path, monkeypatch) -> None:
    """The other half of the rule: a restatement that NARROWS is the subclass's.

    It keeps every keyword the inherited declaration states, with the same value,
    and adds at least one -- so the subclass's declaration is the intersection and
    nothing of the base's is dropped.  2 of the population's 100 restatement
    sites are this.

    **Asserted on the live metadata, and on the symbol the constraint DERIVES.**
    D5 puts a constraint on the type, so the module no longer spells
    ``min_length=2, max_length=8`` in this class at all -- it names a type that
    carries both. Asserting the old text would pass only while the rendering
    stood still, and asserting the alias's name alone would grade a string; so
    the name is asked of ``codegen.constraints`` rather than written here (a
    literal would pin whatever the namer currently does), and the bounds
    themselves are read off the field, which is what the widening would move.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4narrow",
        own={
            "kind": {"type": "string", "minLength": 2, "maxLength": 8, "description": "the marker"},
            "label": {"type": "string", "minLength": 2},
        },
    )
    named = constraints_module.symbol("string", {"minLength": 2, "maxLength": 8})
    assert f"kind: Annotated[{named}" in text, text
    live = cls.model_fields["kind"].metadata
    bounds = {
        attr: getattr(m, attr) for m in live for attr in ("min_length", "max_length") if hasattr(m, attr)
    }
    assert bounds == {"min_length": 2, "max_length": 8}, live
    assert len(live) == 2, live  # and nothing else was invented alongside them
    assert cls.model_validate({"kind": "ab", "label": "xy"}).kind == "ab"
    for bad in ("a", "abcdefghi"):  # the base's floor, then the subclass's ceiling
        with pytest.raises(pydantic.ValidationError):
            cls.model_validate({"kind": bad, "label": "xy"})


def test_the_accepts_and_liveness_checks_are_green_with_a_denominator(
    tmp_path, monkeypatch
) -> None:
    """The instance checks over the probe, with the denominator asserted.

    A green mark without the count beside it says nothing: a pair no instance
    reached leaves the accepts check with nothing round-tripped, and
    ``PairReport.outcome`` refuses a zero denominator for exactly that reason.
    """
    cls, _, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4checks",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    # Explicit depth: this test asserts the denominator, which is the number of
    # instances drawn, constructed AND dumped back out to something the document
    # still admits -- not the number drawn.
    rep = check_pair(Pair("probe", schema, cls, cls.strict_validate), accepts_examples=25)
    assert rep.accepts is not None and rep.accepts.outcome == "pass", rep.accepts
    assert rep.graded_instances == 25, rep.graded_instances
    # The liveness check offers one payload the document refuses, through the entry
    # point: the probe's document demands ``adcp_major_version`` in a conjunct, so
    # dropping it is what the document refuses and the schema half has to answer.
    assert rep.liveness.outcome == "pass", (rep.liveness.how, rep.liveness.detail)
    assert rep.liveness.how.startswith("drops the required key"), rep.liveness.how
    assert "required" in rep.liveness.violated, rep.liveness.violated
    # The schema comparison is NOT this test's subject and is deliberately not
    # asserted: the probe's document is a hand-built shadow of a composition, and
    # what the comparison says about it is the subject of the restatement tests
    # above.  Asserting ``rep.outcome`` here would make this test fail on theirs.


# --------------------------------------------------------------------------- #
# what refuses, by name, pointer and keyword
# --------------------------------------------------------------------------- #
def _lower(doc: dict, binder=emit._no_binder) -> str:  # noqa: SLF001 -- the test is the caller
    return compiler.lower_composition(
        doc, "Probe", "", emit.Module(document="probe.json", bind=binder), keywords.Position.ROOT
    )


def test_an_incompatible_restatement_refuses_by_name_pointer_and_keyword() -> None:
    """Under ``allOf`` BOTH declarations apply, so the effective accepted set is
    their intersection -- and an annotation carrying only the restatement would be
    WIDER than the document.

    **3 documents of the 1,054 portable ones are refused by this rule**, re-measured
    after D7's intersection rule landed, so the arm has a population and is not a guard:
    ``governance/check-governance-response.json``'s ``action_binding``,
    ``media-buy/get-media-buys-response.json``'s ``indicators`` and
    ``signals/get-signals-response.json``'s ``range``.  **None of the three is a looser
    BOUND**, which is why the fixture here is a conflicting ``items`` -- a tighter bound
    is a narrowing under D7 and a looser one has no site.  Graded on two local
    declarations of one key, which needs no binder: the rule that decides them is the
    same symmetric one.
    """
    doc = {
        "title": "Probe",
        "type": "object",
        "properties": {"n": {"type": "array", "items": {"type": "integer"}}},
        "allOf": [{"properties": {"n": {"type": "array", "items": {"type": "string"}}}}],
    }
    with pytest.raises(Refusal) as caught:
        _lower(doc)
    assert caught.value.keyword == "items"
    assert caught.value.pointer == "/allOf/0/properties/n"
    assert "neither declaration narrows the other" in caught.value.detail


def test_the_rule_is_symmetric_so_the_order_the_declarations_are_read_in_cannot_decide() -> None:
    """There is no "last wins" to come back to.

    A generator that let the later conjunct win made its accepted set a function
    of member order, which is invisible in the output.  Asserted on the decision
    itself, over every outcome it has to distinguish, and then on the OUTPUT -- because
    under D7 the decision's answer is one half and :func:`compiler._intersection` is the
    other, and it is the pair that has to be order-independent.

    **A TIGHTER bound narrows and a looser one refuses, which is D7 in its own words:**
    "an enum is the intersection of the members, a bound is the tighter one, a ``const``
    must agree".  An earlier revision read a tighter bound as a conflict, which is the
    equality test this rule replaced.

    **And silence is not a loosening.**  A restatement saying LESS than the base and the
    same where they overlap intersects to the base's content and states no new fact, so
    the field is inherited -- ``False``, not ``None``.
    """
    typed = {"type": "integer", "minimum": 1}
    tighter = {"type": "integer", "minimum": 2}
    assert compiler._restatement({"default": 1}, typed) is False  # annotation-only: inherited
    assert compiler._restatement(dict(typed), typed) is False  # identical: inherited
    assert compiler._restatement({**typed, "maximum": 9}, typed) is True  # adds a keyword
    assert compiler._restatement(tighter, typed) is True  # D7: a bound is the tighter one
    assert compiler._restatement({"type": "string"}, typed) is None  # a different type
    # The asymmetry is the rule working, not the rule disagreeing with itself: exactly
    # one direction of a narrowing is a narrowing.  The LOOSER direction refuses -- a
    # KNOWN CEILING D7 would have carry the base's bound, measured at 0 sites -- and a
    # restatement that says less and the same is inherited.
    assert compiler._restatement(typed, tighter) is None
    assert compiler._restatement(typed, {**typed, "maximum": 9}) is False
    # And the OUTPUT does not depend on which view was read first.
    both = {"type": "integer", "minimum": 2, "maximum": 9}
    assert compiler._intersection(tighter, {**typed, "maximum": 9}) == both
    assert compiler._intersection({**typed, "maximum": 9}, tighter) == both


@pytest.mark.parametrize(
    ("conjunct", "keyword"),
    [
        # a $ref with a sibling is not a base, and the SIBLING is the cause
        ({"$ref": "x", "minimum": 1}, "minimum"),
        ({"enum": ["a", "b"]}, "enum"),  # the enum narrowing: step 3's row
        # A combinator of SHAPES: D7's own third case, and the one conjunct part this
        # row still does not lower.  ``{"required": [...], "not": {...}}`` used to sit
        # here and is now READ -- the requiredness is this node's and the ``not`` is
        # this node's rule -- so a conjunct stating one refuses on ``required`` naming
        # no property instead, which is ``fields``' own refusal and not this arm's.
        (
            {
                "oneOf": [
                    {"properties": {"a": {"type": "string"}}},
                    {"properties": {"b": {"type": "string"}}},
                ]
            },
            "oneOf",
        ),
        ({"type": "object", "properties": {"a": {}}, "additionalProperties": False}, "additionalProperties"),
    ],
)
def test_a_conjunct_this_row_does_not_lower_refuses_by_its_own_keyword(
    conjunct: dict, keyword: str
) -> None:
    """A conjunct is a ``$ref`` (a base) or an inline object with ``properties``.

    Everything else is a later D2 row and refuses on the keyword that stopped it,
    at the conjunct's own pointer -- not on ``allOf``, which would name the
    position rather than the cause.  The ``enum`` case is the population's §4.3
    narrowing (``media-buy/media-buy-commitment-response.json``, and
    ``formats/canonical/image.json``'s ``motion_level``): the intersection of an
    enum with a referenced enum needs step 3's lowering and cannot be stated here.
    """
    doc = {"title": "Probe", "type": "object", "allOf": [conjunct]}
    with pytest.raises(Refusal) as caught:
        _lower(doc)
    assert caught.value.keyword == keyword, caught.value.detail
    assert caught.value.pointer == "/allOf/0"


def test_a_scalar_root_cannot_be_a_base_and_refuses_rather_than_writing_the_module() -> None:
    """D2 makes a scalar root an ``Annotated`` alias, and subclassing an alias is
    a ``TypeError`` at import.

    ``Target.shape`` is ``None`` for a target that is not a class, which is the
    whole of the test: the binder answers with the shape it wrote, so a lowering
    cannot mistake an alias for a class.
    """
    doc = {"title": "Probe", "type": "object", "allOf": [{"$ref": "x"}]}
    with pytest.raises(Refusal) as caught:
        _lower(doc, lambda uri, pointer: emit.Target("..core.brand_id", "BrandID", None))
    assert caught.value.keyword == "allOf"
    assert "cannot be a base" in caught.value.detail


def test_a_keyword_at_the_root_beside_the_conjunct_list_refuses() -> None:
    """The root may carry its own ``properties``, ``required``, ``type``,
    ``additionalProperties`` and D6's rule keywords beside ``allOf``, and nothing else.

    ``if``, ``not`` and ``min``/``maxProperties`` were in the refusing list and are NOT
    keywords this row reports any more: ``salesagent-j3k2l.22`` admits D6's families at
    a composing root, where the rule attaches to the class this row declares
    (``compiler.declare_object`` writes the tuple).  They are asserted on the admitting
    side below, so the keywords that moved are graded rather than merely dropped.

    ``definitions`` left the list before them, at `salesagent-j3k2l.20`: a section is
    admitted at every node by ``compiler.check_keywords`` -- it asserts nothing about an
    instance, and the entries a ``$ref`` names are declared when it asks -- so the 15
    documents refusing on it now refuse on whatever is inside the conjunct or the
    section, which is this row's own honest-attribution point one level deeper.

    **The screen is a function of the NODE and not a flat set**, which is the half a
    membership test would miss: a ``oneOf`` of SHAPES is a nested union this row still
    refuses, while a ``oneOf`` of ``required`` groups is a rule and is admitted.  One
    predicate decides both (``rules.presence_only``), so both arms are graded here.
    """
    # Still refused, each at the root, and each for its own reason: a draft-07 keyword
    # no row lowers, and a combinator of SHAPES, which is a union and not a rule.
    for keyword, value in (
        ("propertyNames", {"type": "string"}),
        ("contains", {"type": "string"}),
        ("oneOf", [{"type": "object", "properties": {"a": {"type": "string"}}}]),
    ):
        doc = {"title": "Probe", "type": "object", "allOf": [{"$ref": "x"}], keyword: value}
        with pytest.raises(Refusal) as caught:
            _lower(doc)
        assert caught.value.keyword == keyword, (keyword, caught.value.keyword)
        assert caught.value.pointer == "/"

    # Admitted, and the rule REACHES THE CLASS -- the point of the change, and what a
    # bare "does not raise" would not say.  Asserted on the emitted text, because that
    # is where a rule tuple either appears or silently does not.
    # ``minProperties`` carries ``additionalProperties`` beside it because
    # ``rules._count`` writes the MINIMUM only where the class keeps every key the
    # document would count -- a silent ``additionalProperties`` is D8's ``ignore``, and
    # a minimum counted over kept keys alone refuses an instance the document accepts.
    # The probe states what the rule needs rather than asserting the gate away.
    for keyword, value, also in (
        ("not", {"required": ["a"]}, {}),
        ("minProperties", 1, {"additionalProperties": False}),
        ("maxProperties", 4, {}),
        ("dependencies", {"a": ["b"]}, {}),
        # A conditional with no branch states nothing, so ``rules._conditional`` writes
        # no rule for one: the probe carries the ``then`` the rule is made of.
        ("if", {"required": ["a"]}, {"then": {"required": ["b"]}}),
        ("oneOf", [{"required": ["a"]}, {"required": ["b"]}], {}),
    ):
        mod = emit.Module(
            document="probe.json",
            bind=emit._no_binder,  # noqa: SLF001 -- the test is the caller
        )
        doc = {
            "title": "Probe",
            "type": "object",
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "allOf": [{"type": "object", "properties": {"c": {"type": "string"}}}],
            keyword: value,
            **also,
        }
        compiler.lower_composition(doc, "Probe", "", mod, keywords.Position.ROOT)
        assert mod.declared[""] == "Probe", (keyword, mod.declared)
        assert [b for b in mod.blocks if "_adcp_rules" in b], keyword


# --------------------------------------------------------------------------- #
# the reader's SECOND caller: a union branch that composes
# --------------------------------------------------------------------------- #
#: A two-document bundle whose union branch 0 composes a ``$ref`` conjunct AND
#: declares a property of its own, so one probe reaches both arms of the reader's
#: classification.  Hand-built, because the reachable population of the ``$ref``
#: arm at a BRANCH is **0 today**: all 3 composing branches the 3.2 bundle emits
#: carry inline conjuncts only, so the committed tree has no class whose bases are
#: a union base plus a conjunct's and a test over the bundle would grade the
#: prepend by reading nothing.  That number is why this is here and not a
#: `# measured 0` note: `salesagent-j3k2l.40` added the ``bases`` argument and the
#: bundle does not yet exercise it, so the probe is the only thing that says the
#: order is the one `isinstance` needs.
def _union_probe(tmp_path: Path, name: str) -> Path:
    at = tmp_path / name
    (at / "core").mkdir(parents=True)
    (at / "core/probe-marker.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Marker",
                "type": "object",
                "required": ["kind"],
                "properties": {"kind": {"type": "string", "description": "the marker"}},
            },
            indent=2,
        )
    )
    (at / "core/probe-union.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Union",
                "description": "the union probe",
                "type": "object",
                "oneOf": [
                    {
                        "title": "Composing Arm",
                        "type": "object",
                        "allOf": [
                            {"$ref": REF.format("core/probe-marker.json")},
                            {"type": "object", "properties": {"inline": {"type": "string"}}},
                        ],
                        "properties": {"label": {"type": "string"}},
                        "required": ["label"],
                    },
                    # CLOSED, and the composing arm beside it is not.  §4's third
                    # dispatch source reached this fixture at ``salesagent-j3k2l.67``:
                    # with both arms open and each requiring a name the other does not
                    # declare, ``{"label": ..., "other": ...}`` satisfies BOTH, so the
                    # branches overlap and the dispatch refuses at ``/`` before the
                    # composing arm this probe is about is ever read.  Closing THIS arm
                    # makes it forbid the ``label`` the other requires, which separates
                    # the pair; the composing arm stays open, so no
                    # ``additionalProperties: false`` sits beside an ``allOf``.
                    {
                        "title": "Plain Arm",
                        "type": "object",
                        "properties": {"other": {"type": "string"}},
                        "required": ["other"],
                        "additionalProperties": False,
                    },
                ],
            },
            indent=2,
        )
    )
    return at


def _emit_union_probe(tmp_path: Path, monkeypatch, name: str):
    """Emit the union probe, import its tree, and return (base, branch, marker, text)."""
    at = _union_probe(tmp_path, name)
    documents = sorted(str(p.relative_to(at)) for p in at.rglob("*.json"))
    out = emit.emit(at, documents)
    assert out.refusals == {}, out.refusals
    tree = tmp_path / "pkg" / name
    emit.write(out, tree)
    monkeypatch.setattr(
        _base, "_document", lambda document: json.loads((tree / document).read_text())
    )
    monkeypatch.syspath_prepend(str(tmp_path / "pkg"))
    module = importlib.import_module(f"{name}.core.probe_union")
    marker = importlib.import_module(f"{name}.core.probe_marker")
    for mod in [m for m in sys.modules if m.startswith(name)]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    return (
        module.ProbeUnion,
        module.ComposingArm,
        marker.ProbeMarker,
        (tree / "core/probe_union.py").read_text(),
    )


def test_a_composing_branch_gains_the_union_base_and_its_conjuncts_bases(
    tmp_path, monkeypatch
) -> None:
    """The ``bases`` argument, graded on the one thing it decides: the ORDER.

    A branch class's identity is the union base -- ``isinstance(payload, Base)`` is
    what §4 is for, and ``BranchDispatchMixin``'s dispatch is reached through it --
    and a composing branch wants that base AND whatever its conjuncts name.  Both
    orders give a legal MRO, so neither is refused at import and a test that only
    asserted membership would pass on either; what this asserts is that the union
    base comes FIRST, so the mixin's methods are the ones the branch answers with.

    The inherited field is asserted beside it, because bases in the right order
    with no inheritance would be the reader having run and bound nothing.
    """
    base, branch, marker, text = _emit_union_probe(tmp_path, monkeypatch, name="s4union")

    assert branch.__bases__ == (base, marker), branch.__bases__
    assert branch.__mro__.index(base) < branch.__mro__.index(marker), branch.__mro__
    assert f"class ComposingArm({base.__name__}, {marker.__name__}):" in text, text

    # The conjuncts BOUND, from both arms: ``kind`` is inherited through the ``$ref``
    # conjunct's base, ``inline`` is declared by the inline conjunct as a field of
    # this node, and ``label`` is the branch's own.
    assert {"kind", "inline", "label"} <= set(branch.model_fields), sorted(branch.model_fields)
    assert "kind" not in branch.__annotations__, branch.__annotations__  # inherited, not restated

    # And the identity the order exists for still answers, through the root's name.
    payload = {"kind": "k", "label": "l"}
    assert isinstance(base.model_validate(payload), branch)
    assert base.model_validate(payload).kind == "k"


def test_breaking_the_shared_reader_reddens_the_product_row_and_the_union_row(
    tmp_path, monkeypatch
) -> None:
    """ONE break, BOTH callers, which is the whole claim of ``salesagent-j3k2l.40``.

    The reader moved to ``compiler`` so that two rows could read one; a reader two
    rows call and one test reaches is half-graded, and the half nobody reaches is
    the half that rots.  So the ``$ref``-conjunct arm is broken once -- ``$ref``
    added to ``compiler.ANNOTATIONS``, which makes a bare-``$ref`` conjunct carry no
    live keyword at all -- and both callers must LOSE THE BASE the conjunct names.

    Broken in the READER and not in either caller on purpose: a break either caller
    could absorb would say nothing about the other.

    **What the break shows is the lost base, not a refusal, and that changed with D7's
    conjunct contribution rule.**  A conjunct with no constraining key contributes
    nothing and the document still emits -- which is correct, and has a population of
    one (``creative/sync-creatives-response.json``'s ``x-adcp-validation`` conjunct) --
    so the reader's last arm is no longer reached by this break and asserting a refusal
    would be asserting the old arm structure.  The class statement is the stronger
    reading anyway: it says the base was BOUND, where a refusal only said the arm was
    entered.
    """
    product_at = _probe(tmp_path, own={"label": {"type": "string"}}, name="brkprod")
    union_at = _union_probe(tmp_path, "brkunion")
    documents = lambda at: sorted(str(p.relative_to(at)) for p in at.rglob("*.json"))  # noqa: E731

    # The control, so a red below is the break and not the probe.
    assert emit.emit(product_at, documents(product_at)).refusals == {}
    assert emit.emit(union_at, documents(union_at)).refusals == {}

    # The control reads the BASE each row binds, so the red below is a base that stopped
    # being bound and not a probe that never bound one.
    whole = emit.emit(product_at, documents(product_at))
    assert "class ProbeComposing(ProbeMarker, AdCPVersionEnvelope):" in (
        whole.files["core/probe_composing.py"]
    ), whole.files["core/probe_composing.py"]
    arm = emit.emit(union_at, documents(union_at))
    assert "class ComposingArm(ProbeUnion, ProbeMarker):" in (
        arm.files["core/probe_union.py"]
    ), arm.files["core/probe_union.py"]

    # The break: ``$ref`` stops being a DECLARATION, so a bare-``$ref`` conjunct reads
    # as carrying nothing.  Patched in the TABLE rather than in a set beside it, which
    # is the one place the answer is written now.
    monkeypatch.setitem(
        keywords.TABLE,
        "$ref",
        keywords.Row(
            keywords.Cell(keywords.Effect.NOTHING, False, None, ""),
            grid=keywords.STRUCTURE,
        ),
    )
    product = emit.emit(product_at, documents(product_at))
    union = emit.emit(union_at, documents(union_at))

    # ONE break, BOTH rows: the conjunct's class is no longer a base of either.
    assert product.refusals == {}, product.refusals  # it emits, wrongly, which is the point
    assert "ProbeMarker" not in product.files["core/probe_composing.py"], (
        product.files["core/probe_composing.py"]
    )
    assert union.refusals == {}, union.refusals
    assert "ProbeMarker" not in union.files["core/probe_union.py"], (
        union.files["core/probe_union.py"]
    )


#: The a2ui shape exactly: a mapping whose VALUE is a schema of its own carrying a
#: ``description`` and nothing the compiler's ``DataType`` can hold.  ``minProperties``
#: and ``maxProperties`` ride the FIELD, so the only fact at the value's own pointer is
#: the annotation.
ANNOTATED_VALUE = {
    "component": {
        "type": "object",
        "description": "Component definition (keyed by component type)",
        "minProperties": 1,
        "maxProperties": 1,
        "additionalProperties": {"type": "object", "description": "Component properties"},
    },
    "tags": {
        "type": "array",
        "description": "a list whose ELEMENT carries one too",
        "items": {"type": "object", "description": "one tag"},
    },
    "label": {"type": "string", "minLength": 2},
}


def test_an_annotation_on_a_containers_contents_reaches_the_wire(tmp_path, monkeypatch) -> None:
    """``docs/plan/rebuild-plan.md`` §6: a ``description`` is never folded, and where
    the comparison reports one the EMITTER is what changes (``salesagent-j3k2l.28``).

    An annotation on a node INSIDE a container had nowhere to go, and unlike a
    constraint it was dropped in SILENCE: ``containers._inner`` refuses a constraint
    and a ``format`` by name because dropping one would widen the model, while a
    ``description`` narrows nothing and so was dropped with no refusal and no
    rendering.  It was the whole of ``comparison.missing`` -- 4 facts over 4 pairs,
    every one ``.../additionalProperties/description`` and every one
    ``'Component properties'``.

    ``containers._contents`` now NAMES such a node, through the same
    ``compiler.name_the_node`` a fragment-referenced node already goes through, so the
    annotation has one spelling.  Both inner positions the comparison reads are probed
    -- a mapping's value and an array's element -- and the real emitter and the real
    comparison are what grade it.
    """
    # ``shared`` because this probe is graded by the COMPARISON, and only then does
    # the fixture state the root description a composing document in the population
    # has -- ``_probe`` says why.  It takes no part in the dimension this judges.
    cls, text, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4innerann",
        own=ANNOTATED_VALUE,
        shared={"spare": {"type": "string", "description": "the base's spare"}},
    )

    # The alias is named by D3's nested rule and the field references it, so the
    # annotation is not restated inline.
    assert (
        "ProbeComposingComponentValue = Annotated[dict[str, Any], "
        "Field(description='Component properties')]" in text
    ), text
    assert "component: Annotated[dict[str, ProbeComposingComponentValue]" in text, text
    assert "ProbeComposingTagsItem = Annotated[dict[str, Any], Field(description='one tag')]" in text, text
    assert "tags: Annotated[list[ProbeComposingTagsItem] | None" in text, text

    comparison = compare_schema(schema, cls)
    assert (comparison.added, comparison.missing, comparison.differs) == ([], [], []), comparison
    # and the fact really is on the wire.  The field is optional, so D4 renders it
    # ``T | None`` and pydantic states the mapping in the live arm of an ``anyOf`` --
    # which is the arm ``harness._normalize`` unwraps and the arm the assertion reads.
    rendered = cls.model_json_schema()["properties"]["component"]
    (live,) = [a for a in rendered["anyOf"] if a.get("type") != "null"]
    assert live["additionalProperties"]["description"] == "Component properties", rendered


def test_breaking_the_inner_annotation_carrier_reddens_the_comparison(
    tmp_path, monkeypatch
) -> None:
    """The same probe with the carrier BROKEN, because a rendering that cannot be
    missed is not graded.

    ``_contents`` reduced to the ``_inner`` call it replaced IS the emitter before this
    change: the decided type is handed up and the node's own annotation goes nowhere.
    The comparison then names each lost annotation at its own pointer, and nothing
    else moves -- which is what says the two positions are the whole of the defect.
    """
    from codegen.lower import containers  # noqa: PLC0415

    monkeypatch.setattr(
        containers,
        "_contents",
        lambda node, pointer, symbol, what, mod, position: containers._inner(
            compiler.decide(node, pointer, symbol, mod, position), pointer, what, mod
        ),
    )
    cls, text, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4innerbrk",
        own=ANNOTATED_VALUE,
        shared={"spare": {"type": "string", "description": "the base's spare"}},
    )
    assert "ProbeComposingComponentValue" not in text, "the patch did not reach"

    comparison = compare_schema(schema, cls)
    assert comparison.added == [], comparison.added
    assert {str(m).split(":", 1)[0] for m in comparison.missing} == {
        "/properties/component/additionalProperties/description",
        "/properties/tags/items/description",
    }, sorted(comparison.missing)
