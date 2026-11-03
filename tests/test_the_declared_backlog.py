"""§2's declared backlog and §8's UNDERDETERMINED equality, graded in SECONDS.

**Why these two instruments are HERE and not in the census test that used to hold them**
(``adcp-client-python-10l.109``).  ``architecture.md``'s decision of 2026-10-29 -- "a check
whose precondition is the thing it checks is not a check" -- is about the import
obligation, and these two had the same disease in a milder form, twice over:

* they were read off the COMMITTED artifact's own declarations, where §9's instruction
  ("ratchet the *ours* split down") is about what the WALK mints.  The two do not agree:
  the committed tree declares 130 sites in 59 documents and a fresh run mints 117 in 50.
* they sat behind ``graded_reports()``, which builds 2,347 pair reports and takes the best
  part of an hour -- and which **cannot complete today at all**: ``pair_of`` calls
  ``schema_at``, and ``adcp-client-python-10l.108``'s two refs of
  ``media-buy/buy-products-request.json`` raise ``KeyError: '0'`` on a synthetic ``allOf``
  pointer.  So the one check that reads both ratchets could not run, which is how
  ``DECLARED_WIDENINGS`` came to hold **11 sites against a live 117** and
  ``UNDERDETERMINED_UNIONS`` **the empty list against a live 89** with nothing red.

Neither instrument needs a pair, a draw or a dump.  The declared half is the run's own
``Emitted.approximations``; the UNDERDETERMINED equality needs the declarations and the
documents of record (``bundle.record``), which is §9's own reading of what a document
states.  Both are a warm second here.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any

from adcp.types._base import SchemaBound, SchemaRef

from codegen import bundle, harness

from compiled import compiled
from nodeset import claimed, ratchet

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


def _minted() -> dict[tuple[str, str, str], Any]:
    """Every approximation a FRESH whole-population run declares, by site."""
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    return {
        harness.site_of(one): one
        for sites in out.approximations.values()
        for one in sites
    }


def _carried() -> dict[tuple[str, str, str], Any]:
    """Every approximation the COMMITTED tree carries, by site.

    Read off the artifact the way §9 requires -- "``render.py`` writes
    ``__adcp_approximations__`` onto the class ... and ``verify/`` reads it as a consumer
    reads any other class attribute" -- and through the same two holders ``graded()`` draws
    from: the CLASS for a class and the MODULE for an alias.  **No ``schema_at``**, which is
    what keeps this readable while ``adcp-client-python-10l.108`` is open.
    """
    import adcp.types._schemas as pkg

    out: dict[tuple[str, str, str], Any] = {}
    for info in sorted(pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."), key=lambda i: i.name):
        module = importlib.import_module(info.name)
        taken: set[int] = set()
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, SchemaBound)
                and "__adcp_schema__" in value.__dict__
                and value.__module__ == info.name
                and id(value) not in taken
            ):
                taken.add(id(value))
                for one in harness.declarations_of(value):
                    out[harness.site_of(one)] = one
        ref = vars(module).get("__adcp_schema__")
        if isinstance(ref, SchemaRef) and callable(vars(module).get("strict_validate")):
            for one in harness.declarations_of(module):
                out[harness.site_of(one)] = one
    return out


#: **§2's declared widenings, NAMED and not counted**, which is what §9 asks for the
#: moment a cell widens: "Do not pin the approximation count.  It rises whenever the
#: emitted set grows ... Pin the four disagreement counts, which do not, and ratchet the
#: *ours* split down."  So this is the *ours* backlog as a SET: a site leaving reddens with
#: the site named, and a site arriving reddens with the site named, where two integers
#: would have said only that a number moved.
#:
#: Both figures §10 prints are read OFF this set rather than stated beside it, because
#: "``K`` and ``D`` are different counts over different denominators and the report never
#: adds them": ``len`` is the facts and the distinct documents are the documents.
#:
#: **RE-MEASURED AT ``adcp-client-python-10l.109``: 11 SITES IN 9 DOCUMENTS -> 117 IN 50,
#: AND THE ELEVEN WERE NOT A FLOOR -- THEY WERE A READING OF A TREE SIX ROWS AGO.**  The
#: set was pinned when the backlog was eleven and every row since has emitted more of the
#: bundle without re-reading it, so the ratchet was a number below the truth -- which is
#: the one state ``nodeset.ratchet``'s own docstring says a floor must never be in, because
#: a floor below the truth gets exempted later instead of acted on.  Nothing was caught by
#: it in either direction for six rows.  **It was invisible because the check that reads it
#: could not run**: ``tests/test_emit.py`` did not collect
#: (``adcp-client-python-10l.105``), and before that the figure it would have moved
#: against was the one ``./check`` prints -- 117 facts in 50 documents -- which nothing
#: compared to this set.
#:
#: **RE-PINNED AT ``adcp-client-python-3be.23``: 117 IN 50 -> 120 IN 53, and this time the
#: check DID run and said so.**  The three that arrived are
#: ``media-buy/proposal-refinement.json#/oneOf/1/anyOf``,
#: ``media-buy/refine-proposals-request.json#/properties/refinements/items/oneOf/1/anyOf``
#: and ``media-buy/request-proposals-request.json#/anyOf``, each an ``anyOf`` at the JOIN
#: rung the dispatch cannot separate, and nothing is pinned-and-no-longer-declared.  So
#: this is the move ``docs/plan/unimplemented.md``'s A-13 calls a RELOCATION rather than a
#: loosening: the gap was three sites of ONE shape already here eighteen times, read off a
#: run three rows after the set was written, and the figure ``./check`` prints -- 120 facts
#: in 53 documents -- is the same reading from the other end.
#:
#: **AND THE POPULATION MOVED WITH IT, which is the same decision ``10l.105`` makes about
#: the import obligation**: "the obligation ranges over the tree a fresh run EMITS, not the
#: one committed".  This set is now compared against the APPROXIMATIONS OF A FRESH
#: WHOLE-POPULATION RUN and not against the COMMITTED artifact's own declarations
#: (:func:`_carried`) -- and the two do not agree: the committed tree declares **130 sites
#: in 59 documents**, 58 of which no fresh run makes and 45 of which a fresh run makes and
#: it does not.  That gap is ``adcp-client-python-uqf``'s ("the committed tree is not what
#: a fresh run emits") and it is held BY DIRECTION below
#: (:func:`test_the_harness_result_is_counted_over_the_whole_population`) rather than as a
#: second 130-entry literal, because its obligation is that it reaches zero.
#:
#: **RE-PINNED AT ``sdk/ident``: 178 IN 70 -> 128 IN 63, BY §8 SENTENCE 2 AND THE
#: DECLARATION IT MADE AFFORDABLE.**  "A fact is
#: declared ONCE, at the node the document STATES it, and never once per pointer the record
#: inlines it to ... An approximation's identity is ``(stating document, stating pointer,
#: keyword)``, and every inlined occurrence resolves to it."  Nothing stopped widening and
#: no cell narrowed: ``emit.repointed`` carried each declaration to every pointer a
#: reference inlines its node to -- a local reference moved it to the referring pointer, a
#: remote one copied the target's to the referrer, a third pass folded it off an ``allOf``
#: conjunct -- and the record resolves references by COPYING, so one conditional reached 58
#: pointers and one cell 80.  The walk minted 37 and that machinery reported 178.
#:
#: **AND 89 OF THE 126 ARE A DECLARATION THAT COULD NOT BE AFFORDED BEFORE.**  §5's
#: ``if`` row compiles an unreadable condition to nothing, §8 sentence 3b's complement
#: does not reach one that states no ``required``, and §2's answer for a model wider
#: than its document is a declaration -- which ``lower.rules._conditional`` now writes.
#: Declaring it under the old rule minted **4,635 sites in 97 documents from 112
#: distinct conditional facts**, 3,641 of them one logo-slot ``if``; that ratio was the
#: measurement of the per-pointer defect and not of this drop.  It closes the six RULE
#: cells ``tests/test_cells.py`` excluded by a derived predicate, and that predicate is
#: deleted in the same commit.
#:
#: **THE 141 THAT LEFT ARE NOT A SET THIS FILE SHOULD HAVE HELD**, which is why this is a
#: re-pin and not a loosening: every one of them was a second entry for a fact already here,
#: at a pointer a REFERRING document spells for a node another document states.  §3a settled
#: the same question for a vocabulary -- *the entry, not the declaration site* -- and the
#: reader is what resolves an occurrence to the entry (``harness.inseparable_sites``, over
#: the origin map ``bundle.recorded`` exports).
#:
#: **SEVEN SHAPES, and the sentence that keeps each -- per SHAPE, because that is the level
#: at which a declaration is a decision.**  A site is a document's instance of one of
#: these seven and carries no argument of its own:
#:
#: * ``oneOf`` at the JOIN rung, UNDERDETERMINED -- **15 sites in 13 documents**: §4's
#:   dispatch cannot separate the branches, which is the one kind §8 gives an instrument of
#:   its own (``underdetermined_census``, below).
#: * ``anyOf`` at the JOIN rung, UNDERDETERMINED -- **10 sites in 10 documents**, the same
#:   shape under the other combinator.  ``harness.inseparable_unions`` draws no
#:   root/nested distinction and must not, so both positions are here.
#: * ``patternProperties`` at the CONTAINER rung -- **7 sites in 6 documents**, every one
#:   a ``patternProperties`` beside a non-``false`` ``additionalProperties``, whose
#:   faithful answer is a rule family for "keys matching this pattern take this type".
#:   That is a different thing from §2's three value rules and no row has written it;
#:   ``adcp-client-python-10l.12`` is the row that owns the keyword.
#: * ``else`` at the KEYWORD rung -- **4 sites in 4 documents**: a conditional nested
#:   inside another conditional's ``else`` arm compiles to nothing on the model, and
#:   ``docs/plan/final-state.md`` reading 2 makes every exception to reading 1 a DECLARED
#:   widening rather than a named ceiling.
#: * ``maxProperties`` at the KEYWORD rung -- **2 sites**, ``/properties/ext`` in
#:   ``core/account-change.json`` and its webhook twin: the class takes ``ignore`` and
#:   counts over a smaller key set than the document counts over.  Declared nowhere
#:   until ``sdk/ident``, because ``Rules.dropped`` had four producers and one
#:   consumer and ``lower_composition`` read the screen and the distinct set and
#:   never the dropped set.
#: * ``maxLength`` at the KEYWORD rung -- **1 site**, and it is the only one of the 128 that
#:   is a plain keyword rather than a structural answer:
#:   ``compliance/comply-test-controller-response.json`` at
#:   ``#/oneOf/6/properties/recorded_calls/items/properties/payload``.
#: * ``if`` at the KEYWORD rung -- **89 sites in 33 documents**, the condition §5's
#:   ``if`` row cannot reduce to a clause list and §8 sentence 3b's complement cannot
#:   reach: it states no ``required``, and a clause tests a key that is PRESENT.
#:
#: **SEVEN CAUSES, NOT 128**, which is the reading ``codegen/dump_exemptions.py``'s own
#: instrument records for the same shape: one row at 89 conditions, one derivation at 25
#: unions, one cell at 7 containers, one conditional shape at 4 nodes, one discarded drop
#: set at 2, one keyword at 1.  The pointer count and
#: the cause count are different numbers over different denominators and the report never
#: adds them.
DECLARED_WIDENINGS = {
    # if at KEYWORD: 89 sites in 33 documents
    ('aao/agent-publishers.json', '#/definitions/PublisherEntry/allOf/0', 'if'),
    ('adagents.json', '#/oneOf/1/allOf/1', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/10', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/11', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/12', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/13', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/14', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/15', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/16', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/17', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/18', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/19', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/2', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/20', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/21', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/22', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/23', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/25', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/26', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/3', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/4', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/5', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/6', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/7', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/8', 'if'),
    ('compliance/comply-test-controller-request.json', '#/allOf/9', 'if'),
    ('compliance/comply-test-controller-response.json', '#/oneOf/3/properties/forced/allOf/0', 'if'),
    ('compliance/comply-test-controller-response.json', '#/oneOf/3/properties/forced/allOf/1', 'if'),
    ('core/agent-notification-config.json', '#', 'if'),
    ('core/attestation-capabilities.json', '#/allOf/0', 'if'),
    ('core/bidding-policy-capability.json', '#/definitions/policy_profile/allOf/0', 'if'),
    ('core/bidding-policy-capability.json', '#/definitions/policy_profile/allOf/1', 'if'),
    ('core/canonical-product.json', '#/allOf/0', 'if'),
    ('core/canonical-product.json', '#/allOf/1', 'if'),
    ('core/delivery-metric-aggregate.json', '#/oneOf/0/allOf/0', 'if'),
    ('core/delivery-metric-aggregate.json', '#/oneOf/0/allOf/1', 'if'),
    ('core/delivery-metric-aggregate.json', '#/oneOf/0/allOf/2', 'if'),
    ('core/delivery-metric-aggregate.json', '#/oneOf/0/allOf/3', 'if'),
    ('core/demographic-reporting-capability.json', '#/properties/age/allOf/0', 'if'),
    ('core/demographic-reporting-capability.json', '#/properties/age/allOf/1', 'if'),
    ('core/demographic-targeting-capability.json', '#/properties/age/allOf/0', 'if'),
    ('core/demographic-targeting-capability.json', '#/properties/age/allOf/1', 'if'),
    ('core/demographic-targeting-capability.json', '#/properties/age/allOf/3', 'if'),
    ('core/demographic-targeting-resolution.json', '#/allOf/0', 'if'),
    ('core/demographic-targeting-resolution.json', '#/allOf/2', 'if'),
    ('core/package.json', '#/allOf/2', 'if'),
    ('core/product.json', '#/allOf/0', 'if'),
    ('core/product.json', '#/allOf/1', 'if'),
    ('core/product.json', '#/allOf/10', 'if'),
    ('core/product.json', '#/allOf/2', 'if'),
    ('core/product.json', '#/allOf/5', 'if'),
    ('core/product.json', '#/allOf/6', 'if'),
    ('core/product.json', '#/allOf/7', 'if'),
    ('core/product.json', '#/allOf/8', 'if'),
    ('core/product.json', '#/allOf/9', 'if'),
    ('core/reporting-delivery-capabilities.json', '#/allOf/5', 'if'),
    ('core/reporting-delivery-capabilities.json', '#/allOf/6', 'if'),
    ('core/reporting-delivery-config-state.json', '#/allOf/0', 'if'),
    ('core/reporting-delivery-config-state.json', '#/allOf/2', 'if'),
    ('core/reporting-obligation.json', '#/allOf/0', 'if'),
    ('core/reporting-reliability-statistics.json', '#/allOf/0', 'if'),
    ('core/signal-definition.json', '#/allOf/4', 'if'),
    ('core/signal-listing.json', '#/allOf/0', 'if'),
    ('core/targeting-overlay-support.json', '#/definitions/daypartSupport/anyOf/1/allOf/0', 'if'),
    ('creative/preview-creative-request.json', '#/allOf/2', 'if'),
    ('creative/preview-creative-request.json', '#/allOf/3', 'if'),
    ('formats/canonical/native_in_feed.json', '#/allOf/2', 'if'),
    ('governance/check-governance-request.json', '#/allOf/10', 'if'),
    ('governance/check-governance-request.json', '#/allOf/14', 'if'),
    ('governance/sync-plans-request.json', '#/properties/plans/items/allOf/0', 'if'),
    ('governance/sync-plans-request.json', '#/properties/plans/items/allOf/1', 'if'),
    ('media-buy/build-creative-request.json', '#/allOf/8', 'if'),
    ('media-buy/get-media-buy-delivery-response.json', '#/allOf/3', 'if'),
    ('media-buy/get-media-buys-response.json', '#/properties/media_buys/items/properties/packages/items/allOf/4', 'if'),
    ('media-buy/get-products-request.json', '#/allOf/1', 'if'),
    ('media-buy/get-products-response.json', '#/allOf/2', 'if'),
    ('media-buy/get-reporting-status-response.json', '#/allOf/6', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/10', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/15', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/16', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/4', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/5', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/8', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/allOf/9', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/properties/adcp/properties/capability_changes/allOf/0', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/properties/adcp/properties/principal/allOf/0', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/properties/creative/allOf/2', 'if'),
    ('protocol/get-adcp-capabilities-response.json', '#/properties/media_buy/allOf/1', 'if'),
    ('signals/get-signals-request.json', '#/allOf/1', 'if'),

    # oneOf at JOIN, UNDERDETERMINED: 15 sites in 13 documents
    ('adagents.json', '#/oneOf', 'oneOf'),
    ('brand.json', '#/oneOf', 'oneOf'),
    ('content-standards/calibrate-content-response.json', '#/oneOf', 'oneOf'),
    ('content-standards/create-content-standards-request.json', '#/properties/calibration_exemplars/properties/fail/items/oneOf', 'oneOf'),
    ('content-standards/create-content-standards-request.json', '#/properties/calibration_exemplars/properties/pass/items/oneOf', 'oneOf'),
    ('content-standards/create-content-standards-response.json', '#/oneOf', 'oneOf'),
    ('content-standards/get-content-standards-response.json', '#/oneOf', 'oneOf'),
    ('content-standards/get-media-buy-artifacts-response.json', '#/oneOf', 'oneOf'),
    ('content-standards/list-content-standards-response.json', '#/oneOf', 'oneOf'),
    ('content-standards/update-content-standards-request.json', '#/properties/calibration_exemplars/properties/fail/items/oneOf', 'oneOf'),
    ('content-standards/update-content-standards-request.json', '#/properties/calibration_exemplars/properties/pass/items/oneOf', 'oneOf'),
    ('content-standards/validate-content-delivery-response.json', '#/oneOf', 'oneOf'),
    ('core/evaluator-spec.json', '#/oneOf', 'oneOf'),
    ('media-buy/build-creative-response.json', '#/oneOf', 'oneOf'),
    ('registries/v1-canonical-mapping.json', '#/properties/mappings/items/properties/v1_pattern/oneOf', 'oneOf'),

    # anyOf at JOIN, UNDERDETERMINED: 10 sites in 10 documents
    ('adagents.json', '#/oneOf/1/allOf/0/anyOf', 'anyOf'),
    ('compliance/task-completion-data.json', '#/anyOf', 'anyOf'),
    ('core/async-response-data.json', '#/anyOf', 'anyOf'),
    ('core/requirements/asset-requirements.json', '#/anyOf', 'anyOf'),
    ('media-buy/buy-products-request.json', '#/anyOf', 'anyOf'),
    ('media-buy/create-media-buy-request.json', '#/anyOf', 'anyOf'),
    ('media-buy/get-media-buys-response.json', '#/properties/media_buys/items/properties/available_actions/items/anyOf', 'anyOf'),
    ('media-buy/proposal-refinement.json', '#/oneOf/1/anyOf', 'anyOf'),
    ('media-buy/request-proposals-request.json', '#/anyOf', 'anyOf'),
    ('trusted-match/provider-registration.json', '#/anyOf', 'anyOf'),

    # patternProperties at CONTAINER: 7 sites in 6 documents
    ('core/creative-asset.json', '#/properties/assets', 'patternProperties'),
    ('core/creative-assets.json', '#', 'patternProperties'),
    ('core/creative-manifest.json', '#/properties/assets', 'patternProperties'),
    ('creative/list-creatives-response.json', '#/properties/creatives/items/properties/assets', 'patternProperties'),
    ('creative/list-creatives-response.json', '#/properties/format_summary', 'patternProperties'),
    ('creative/sync-creatives-response.json', '#/oneOf/0/properties/creatives/items/properties/assignment_errors', 'patternProperties'),
    ('media-buy/get-products-response.json', '#/properties/extensions', 'patternProperties'),

    # else at KEYWORD: 4 sites in 4 documents
    ('core/reporting-schedule-offering.json', '#/allOf/0', 'else'),
    ('core/reporting-schedule.json', '#/allOf/0', 'else'),
    ('media-buy/get-products-response.json', '#', 'else'),
    ('signals/get-signals-response.json', '#', 'else'),

    # maxProperties at KEYWORD: 2 sites in 2 documents
    ('core/account-change-recorded-webhook.json', '#/properties/ext', 'maxProperties'),
    ('core/account-change.json', '#/properties/ext', 'maxProperties'),

    # maxLength at KEYWORD: 1 sites in 1 documents
    ('compliance/comply-test-controller-response.json', '#/oneOf/6/properties/recorded_calls/items/properties/payload', 'maxLength'),

}

#: **§8's UNDERDETERMINED equality, as the set the derivation cannot separate.**  "The set
#: of unions declaring one equals the set the derivation cannot separate, in both
#: directions, so a union that becomes separable loses its declaration and a union that
#: stops being separable gains one."
#:
#: It was ``[]``, and the three readings its comment gave for that zero were each a decided
#: sentence -- ``harness.inseparable_unions`` carries all three with its measurement:
#:
#: * a presence-only combinator is not a union (architecture §4's ``presence_only``
#:   reading): 185 pointers before this clause, 16 of them roots;
#: * a union at a RULE position lowers no type (semantics §3): 3 pointers;
#: * a union whose branches are not all shapes lowers to an alias over their types, so
#:   there are no branch classes for a declaration order to choose between.
#:
#: **ALL THREE STILL HOLD AND THE ZERO WAS STILL FALSE: 89 pointers,
#: ``adcp-client-python-10l.109``.**  The three clauses say which pointers are NOT in this
#: list; they never said the remainder was empty, and the remainder grew with every row
#: that emitted more of the bundle.  The comment's own defence of the zero -- "at zero the
#: list is the one form that cannot be mistaken for an allowlist" -- was true of a zero
#: that was a fact and is the reason this is a LIST of 89 and not the number 89: a pointer
#: arriving or leaving is a fact about a document and a count cannot say which.
#:
#: **BOTH SIDES ARE SETS OF §8's IDENTITY NOW, AND THE LIVE FIGURE FELL 1,081 -> 88
#: (``sdk/ident``).**  §8 sentence 2 declares a fact once, at the node the document states
#: it, so the DECLARED side is a set of ``(stating document, stating pointer)``.  The
#: derived side was not: ``harness.inseparable_unions`` reads a RECORD, and a record spells
#: one stating pointer once per path through the reference graph that reaches it -- so one
#: inseparable union owed as many declarations as it had referrers, and this list was a
#: reading of the reference graph rather than of the declarations.  With the derivation read
#: through ``harness.inseparable_sites`` -- which resolves an occurrence to the site it
#: states, over the origin map ``bundle.recorded`` exports -- the two sides are the same
#: kind of thing and the remainder is 88.
#:
#: **At ``c2d2f650`` this list was pinned at 89 against a live 1,081**, which is the same
#: disease its own history records twice over: a list below the truth gets exempted later
#: instead of acted on.  88 is a SHRINK of the pin and the first figure it has been equal
#: to since it was written.
#:
#: **Every one is a union §4's dispatch cannot separate and ``lower.union`` declares
#: nothing at**, and **none of them is a widening any row chose**: the walk declares where
#: it LOWERS a union, and these are nodes it reaches as an alias, a rule source or not at
#: all.  The row that teaches §4's dispatch a fourth separator empties most of this list in
#: one change; the row that teaches the walk to declare at a union it does not lower empties
#: the rest.
#:
#: Compared against a FRESH run's declarations and a FRESH run's documents of record, for
#: :data:`DECLARED_WIDENINGS`' reason.
#:
#: Held as ``document#pointer`` and not as ``harness``'s own sentence: the sentence is
#: constant text and the site is the fact.
UNDERDETERMINED_UNIONS: list[str] = [
    'brand.json#/definitions/data_subject_contestation/anyOf',
    'brand.json#/oneOf/3/anyOf',
    'compliance/comply-test-controller-response.json#/oneOf',
    'content-standards/artifact.json#/$defs/asset_access/oneOf',
    'content-standards/artifact.json#/properties/assets/items/oneOf',
    'core/account-ref.json#/oneOf',
    'core/activation-key.json#/oneOf',
    'core/assets/asset-union.json#/oneOf',
    'core/audience-activation-method.json#/oneOf',
    'core/audience-selector.json#/oneOf/0/anyOf',
    'core/audience-selector.json#/oneOf/1/anyOf',
    'core/audience-selector.json#/oneOf/2/anyOf',
    'core/audience-selector.json#/oneOf',
    'core/bidding-policy-capability.json#/definitions/policy_profile/anyOf',
    'core/brand-ref.json#/properties/data_subject_contestation/anyOf',
    'core/budget-range.json#/anyOf',
    'core/canonical-forecast-point.json#/properties/viewability/anyOf',
    'core/canonical-optimization-goal.json#/oneOf/0/properties/target_frequency/anyOf',
    'core/canonical-proposal.json#/properties/total_budget_guidance/anyOf',
    'core/catchment.json#/oneOf',
    'core/collection-distribution.json#/anyOf',
    'core/creative-manifest.json#/oneOf',
    'core/delivery-metric-aggregate.json#/oneOf',
    'core/demographic-age-range.json#/anyOf',
    'core/demographic-reporting-capability.json#/anyOf',
    'core/forecast-dimension-signal.json#/anyOf',
    'core/forecast-point.json#/properties/viewability/anyOf',
    'core/forecast-range.json#/anyOf',
    'core/format-option-ref.json#/oneOf',
    'core/format.json#/properties/assets/items/oneOf/0/oneOf',
    'core/format.json#/properties/assets/items/oneOf/1/properties/assets/items/oneOf',
    'core/frequency-cap-constraints.json#/anyOf',
    'core/frequency-cap.json#/anyOf',
    'core/optimization-goal.json#/oneOf/0/properties/target/oneOf',
    'core/optimization-goal.json#/oneOf/0/properties/target_frequency/anyOf',
    'core/optimization-goal.json#/oneOf/1/properties/target/oneOf',
    'core/optimization-goal.json#/oneOf/2/properties/target/oneOf',
    'core/optimization-goal.json#/oneOf',
    'core/placement-definition.json#/anyOf',
    'core/placement-definition.json#/properties/format_options/items/anyOf',
    'core/placement.json#/anyOf',
    'core/product-filters.json#/properties/budget_range/anyOf',
    'core/product-filters.json#/properties/geo_proximity/items/oneOf',
    'core/product-format-declaration.json#/oneOf',
    'core/product.json#/anyOf',
    'core/registry-event.json#/$defs/publisherAdagentsPayload/anyOf',
    'core/reporting-verification.json#/properties/physical_checksums/items/oneOf',
    'core/signal-definition-enrichment.json#/properties/data_subject_rights/properties/channels/items/anyOf',
    'core/signal-listing.json#/anyOf',
    'core/signal-pricing.json#/oneOf',
    'core/signal-targeting.json#/oneOf/0/anyOf',
    'core/signal-targeting.json#/oneOf/1/anyOf',
    'core/signal-targeting.json#/oneOf/2/anyOf',
    'core/signal-targeting.json#/oneOf',
    'core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1/anyOf',
    'core/targeting-overlay-support.json#/properties/geo_proximity/anyOf/1/anyOf',
    'core/targeting.json#/properties/geo_proximity/items/oneOf',
    'core/transformer.json#/anyOf',
    'core/wholesale-feed-event.json#/$defs/appliesTo/oneOf',
    'core/wholesale-feed-event.json#/$defs/signal/anyOf',
    'core/wholesale-feed-event.json#/oneOf/0/properties/payload/anyOf',
    'core/wholesale-feed-event.json#/oneOf/1/properties/payload/anyOf',
    'core/wholesale-feed-event.json#/oneOf',
    'creative/get-creative-features-response.json#/oneOf',
    'creative/preview-creative-request.json#/properties/requests/items/anyOf',
    'creative/sync-creatives-request.json#/anyOf',
    'creative/sync-creatives-response.json#/oneOf',
    'formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf',
    'media-buy/build-creative-response.json#/oneOf/1/properties/preview/properties/previews/items/anyOf',
    'media-buy/build-creative-response.json#/oneOf/2/properties/creatives/items/anyOf',
    'media-buy/change-term-constraints.json#/oneOf/1/anyOf',
    'media-buy/change-term-constraints.json#/oneOf/3/anyOf',
    'media-buy/control-media-buy-request.json#/anyOf',
    'media-buy/create-media-buy-response.json#/oneOf',
    'media-buy/decline-proposals-response.json#/anyOf',
    'media-buy/get-reporting-status-response.json#/oneOf',
    'media-buy/package-control.json#/anyOf',
    'media-buy/proposal-budget-constraint.json#/anyOf',
    'media-buy/proposal-refinement.json#/oneOf',
    'media-buy/refine-proposals-response.json#/anyOf',
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf',
    'media-buy/request-proposals-response.json#/anyOf',
    'media-buy/sync-audiences-response.json#/oneOf',
    'media-buy/sync-catalogs-response.json#/oneOf',
    'media-buy/sync-reporting-receipts-response.json#/properties/results/items/anyOf',
    'media-buy/update-media-buy-response.json#/oneOf',
    'pricing-options/price-breakdown.json#/properties/adjustments/items/oneOf',
    'signals/get-signals-response.json#/properties/signals/items/anyOf',

]


def test_the_declared_backlog_is_the_set_this_compiler_mints() -> None:
    """:data:`DECLARED_WIDENINGS`, against a fresh whole-population run.

    The two figures §10 prints are read OFF the set rather than stated beside it, because
    "``K`` and ``D`` are different counts over different denominators and the report never
    adds them".  A site arriving or leaving reddens with the site named.
    """
    minted = claimed("sites a fresh run declares", set(_minted()))
    assert minted == DECLARED_WIDENINGS, {
        "declared and not pinned": sorted(minted - DECLARED_WIDENINGS),
        "pinned and no longer declared": sorted(DECLARED_WIDENINGS - minted),
        "live": len(minted),
    }
    assert len({document for document, _, _ in minted}) == len(
        {document for document, _, _ in DECLARED_WIDENINGS}
    )


def test_the_underdetermined_equality_holds_in_both_directions() -> None:
    """§8's third equality: the unions declaring one are the unions §4 cannot separate.

    "The set of unions declaring one equals the set the derivation cannot separate, in both
    directions, so a union that becomes separable loses its declaration and a union that
    stops being separable gains one."

    **BOTH DIRECTIONS REPORTED TOGETHER**, which is ``architecture.md``'s decision of
    2026-10-29 applied to a pair of assertions: written as two bare asserts, the first to
    fail hides the second -- and the STALE direction is red today, so the SILENT ratchet
    would never be read and could rot exactly the way the empty list it replaces did.

    **THE STALE DIRECTION IS RED, AT 7, AND DELIBERATELY NOT PINNED
    (``adcp-client-python-10l.110``; re-measured at ``sdk/ident``).**  It was **16 at
    ``c2d2f650``** and the cause §8 sentence 2 removed is the one
    ``adcp-client-python-10l.110`` named: a declaration carried to a pointer OTHER than the
    one the document states the combinator at -- ``adagents.json#/oneOf/1/anyOf`` declared
    and separable while ``adagents.json#/oneOf/1/allOf/0/anyOf`` was inseparable and
    declared by nothing, one union under two spellings.  With the declaration at the
    stating pointer and the derivation read as identities, that pair is one site and 9 of
    the 16 go with it.

    **6 OF THE 7 THAT REMAIN ARE ONE CAUSE, AND IT IS §8 SENTENCE 3a UNBUILT HERE.**  Each
    is a union the walk lowers and declares whose branches the STORED record spells as
    references into its own section -- measured: 1 of 2 branches at each of the four
    ``calibration_exemplars`` sites and at ``available_actions/items``, 6 of 7 at
    ``media-buy/proposal-refinement.json#/oneOf/1/anyOf`` -- and
    ``inseparable_unions``' shape test reads a bare ``$ref`` branch as neither an object
    nor a node with ``properties``, so the pair is never put to ``separates`` and the union
    is absent from the derived side.  §8 sentence 3a is exactly the sentence that answers
    it: *a reader asking what the document states reads through the storage*.
    ``inseparable_unions`` is such a reader and does not yet read through it, and
    ``bundle.expanded`` is the reading it needs.

    **The seventh is ``core/async-response-data.json#/anyOf`` and it is a different
    disagreement**: 42 branches, none a bare reference, so the derivation reaches it and
    answers SEPARABLE where ``lower.union.overlapping`` answered OVERLAPPING.  Two readings
    of one node disagreeing is this equality's own point; which of them is wrong is
    unmeasured and is not this row's.

    An equality is an OBLIGATION and not a ratchet, so this stays red and names the 7.

    ``silent`` arrives as ``harness``'s own SENTENCE and :data:`UNDERDETERMINED_UNIONS`
    holds the SITE, so the site is taken off the front: the suffix is constant text and
    the site is the fact.
    """
    known = set(bundle.portable(BUNDLE))
    out = compiled(BUNDLE, sorted(known))
    # ``bundle.recorded`` and not ``bundle.record``: §8 sentence 2 makes both sides of this
    # equality sets of ``(stating document, stating pointer)``, and resolving an inlined
    # occurrence to the site it states needs the origin map the inliner exports beside the
    # record (``harness.inseparable_sites``).  The pair travels together because an
    # ``id``-keyed map is sound only while its record is alive.
    records = {
        document: got
        for document in sorted(out.emitted)
        if isinstance(got := bundle.recorded(BUNDLE, document, known), tuple)
    }
    claimed("documents of record a fresh run emits", set(records))
    stale, silent = harness.underdetermined_census(
        [one for sites in out.approximations.values() for one in sites], records
    )
    at = [one.split(": ", 1)[0] for one in silent]
    disagreements: list[Any] = []
    if at != UNDERDETERMINED_UNIONS:
        disagreements.append(
            {
                "the derivation cannot separate these and nothing declares one": sorted(
                    set(at) - set(UNDERDETERMINED_UNIONS)
                ),
                "pinned and no longer silent": sorted(set(UNDERDETERMINED_UNIONS) - set(at)),
                "live": len(at),
            }
        )
    if stale:
        disagreements.append({"declared UNDERDETERMINED and separable": stale})
    assert not disagreements, disagreements


def test_the_committed_trees_declarations_are_the_runs() -> None:
    """**THE GAP BETWEEN THE ARTIFACT AND THE RUN, held BY DIRECTION.**

    ``nodeset.ratchet``'s own shape for a quantity whose obligation is that it reaches
    zero, and ``adcp-client-python-uqf`` is the row: "the committed tree is not what a
    fresh run emits".  Measured at ``adcp-client-python-10l.109``: the artifact declares 58
    sites no fresh run mints and misses 45 a fresh run does, and both ceilings may only
    come DOWN.  Named as two numbers rather than as a 103-entry literal because neither
    set is a decision -- each entry is a file that was not rewritten.

    **This is the figure that makes the two populations' disagreement actionable**, and
    nothing held it before: the artifact's own declarations were what the backlog was
    read against, so the gap was not a quantity anywhere.
    """
    minted, carried = set(_minted()), set(_carried())
    claimed("sites a fresh run declares", minted)
    claimed("sites the committed tree carries", carried)
    ratchet(
        "declarations the committed tree carries and a fresh run does not",
        len(carried - minted),
        at_most=58,
        because="regenerating the tree (adcp-client-python-uqf) can only remove these; a "
        "rise means a row changed the walk and wrote no tree",
    )
    ratchet(
        "declarations a fresh run mints and the committed tree does not carry",
        len(minted - carried),
        at_most=45,
        because="the same row removes these; a rise means the walk moved further ahead of "
        "the artifact every pair in tests/test_emit.py is graded from",
    )
