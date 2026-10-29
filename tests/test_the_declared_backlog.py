"""§2's declared backlog and §8's UNDERDETERMINED equality, graded in SECONDS.

**Why these two instruments are HERE and not in the census test that used to hold them**
(``adcp-client-python-10l.109``).  ``architecture.md``'s decision of 2026-10-29 -- "a check
whose precondition is the thing it checks is not a check" -- is about the import
obligation, and these two had the same disease in a milder form, twice over:

* they were read off ``census.declared``, the COMMITTED artifact, where §9's instruction
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

What stays in ``tests/test_emit.py``'s census test is exactly what needs the pairs: §8's
two-direction equality between the DECLARED set and the APPROXIMATED set, where
*approximated* is a verdict the comparison reaches at a pointer.
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
#: **AND THE POPULATION MOVED WITH IT, which is the same decision ``10l.105`` makes about
#: the import obligation**: "the obligation ranges over the tree a fresh run EMITS, not the
#: one committed".  This set is now compared against the APPROXIMATIONS OF A FRESH
#: WHOLE-POPULATION RUN and not against ``census.declared``, which is read off the
#: COMMITTED artifact -- and the two do not agree: the committed tree declares **130 sites
#: in 59 documents**, 58 of which no fresh run makes and 45 of which a fresh run makes and
#: it does not.  That gap is ``adcp-client-python-uqf``'s ("the committed tree is not what
#: a fresh run emits") and it is held BY DIRECTION below
#: (:func:`test_the_harness_result_is_counted_over_the_whole_population`) rather than as a
#: second 130-entry literal, because its obligation is that it reaches zero.
#:
#: **FOUR SHAPES, and the sentence that keeps each -- per SHAPE, because that is the level
#: at which a declaration is a decision.**  A site is a document's instance of one of
#: these four and carries no argument of its own:
#:
#: * ``patternProperties`` at the CONTAINER rung -- **80 sites in 28 documents**, every one
#:   a ``patternProperties`` beside a non-``false`` ``additionalProperties``, whose
#:   faithful answer is a rule family for "keys matching this pattern take this type".
#:   That is a different thing from §2's three value rules and no row has written it;
#:   ``adcp-client-python-10l.12`` is the row that owns the keyword.
#: * ``oneOf`` at the JOIN rung, UNDERDETERMINED -- **18 sites in 16 documents**: §4's
#:   dispatch cannot separate the branches, which is the one kind §8 gives an instrument of
#:   its own (``underdetermined_census``, below) and the one the comparison cannot see.
#: * ``anyOf`` at the JOIN rung, UNDERDETERMINED -- **18 sites in 15 documents**, the same
#:   shape under the other combinator.  ``harness.inseparable_unions`` draws no
#:   root/nested distinction and must not, so both positions are here.
#: * ``maxLength`` at the KEYWORD rung -- **1 site**, and it is the only one of the 117 that
#:   is a plain keyword rather than a structural answer:
#:   ``compliance/comply-test-controller-response.json`` at
#:   ``#/oneOf/6/properties/recorded_calls/items/properties/payload``.
#:
#: **Grown by EMISSION and not by permissiveness**, which is the reading
#: ``codegen/dump_exemptions.py``'s own instrument records for the same shape: "the number
#: of positions one upstream pattern reaches is a property of how much of the bundle is
#: packaged, not of how permissive the SDK is".  80 of the 117 are one cell at 80
#: positions; 36 are one derivation at 36 unions; 1 is a keyword.  **Three causes, not
#: 117.**
DECLARED_WIDENINGS = {

    # anyOf at JOIN: 18 sites in 15 documents
    ('adagents.json', '#/oneOf/1/anyOf', 'anyOf'),
    ('compliance/comply-test-controller-request.json', '#/properties/params/properties/result/anyOf', 'anyOf'),
    ('compliance/task-completion-data.json', '#/anyOf', 'anyOf'),
    ('core/async-response-data.json', '#/anyOf', 'anyOf'),
    ('core/format.json', '#/properties/assets/items/oneOf/0/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('core/format.json', '#/properties/assets/items/oneOf/1/properties/assets/items/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf', 'anyOf'),
    ('core/requirements/asset-requirements.json', '#/anyOf', 'anyOf'),
    ('core/requirements/catalog-requirements.json', '#/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('core/requirements/offering-asset-constraint.json', '#/properties/asset_requirements/anyOf', 'anyOf'),
    ('creative/list-creative-formats-response.json', '#/properties/formats/items/properties/assets/items/oneOf/0/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('creative/list-creative-formats-response.json', '#/properties/formats/items/properties/assets/items/oneOf/1/properties/assets/items/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('media-buy/buy-products-request.json', '#/anyOf', 'anyOf'),
    ('media-buy/create-media-buy-request.json', '#/anyOf', 'anyOf'),
    ('media-buy/get-media-buys-response.json', '#/properties/media_buys/items/properties/available_actions/items/anyOf', 'anyOf'),
    ('media-buy/list-creative-formats-response.json', '#/properties/formats/items/properties/assets/items/oneOf/0/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('media-buy/list-creative-formats-response.json', '#/properties/formats/items/properties/assets/items/oneOf/1/properties/assets/items/oneOf/14/properties/requirements/properties/offering_asset_constraints/items/properties/asset_requirements/anyOf', 'anyOf'),
    ('trusted-match/provider-registration.json', '#/anyOf', 'anyOf'),
    # maxLength at KEYWORD: 1 sites in 1 documents
    ('compliance/comply-test-controller-response.json', '#/oneOf/6/properties/recorded_calls/items/properties/payload', 'maxLength'),
    # oneOf at JOIN: 18 sites in 16 documents
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
    ('core/async-response-data.json', '#/anyOf/27/oneOf', 'oneOf'),
    ('core/evaluator-spec.json', '#/oneOf', 'oneOf'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf', 'oneOf'),
    ('media-buy/build-creative-request.json', '#/properties/evaluator/oneOf', 'oneOf'),
    ('media-buy/build-creative-response.json', '#/oneOf', 'oneOf'),
    ('registries/v1-canonical-mapping.json', '#/properties/mappings/items/properties/v1_pattern/oneOf', 'oneOf'),
    # patternProperties at CONTAINER: 80 sites in 28 documents
    ('compliance/comply-test-controller-request.json', '#/properties/params/properties/result/anyOf/0/properties/extensions', 'patternProperties'),
    ('compliance/task-completion-data.json', '#/anyOf/0/properties/extensions', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/0/properties/extensions', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/0/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/0/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/1/properties/creative_manifests/items/properties/assets', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/1/properties/creative_manifests/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/27/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/28/oneOf/2/properties/manifest/properties/assets', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/28/oneOf/2/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/async-response-data.json', '#/anyOf/34/oneOf/0/properties/creatives/items/properties/assignment_errors', 'patternProperties'),
    ('core/creative-asset.json', '#/properties/assets', 'patternProperties'),
    ('core/creative-asset.json', '#/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/creative-assets.json', '#', 'patternProperties'),
    ('core/creative-manifest.json', '#/properties/assets', 'patternProperties'),
    ('core/creative-manifest.json', '#/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/creative-representation-set.json', '#/properties/representations/items/properties/assets', 'patternProperties'),
    ('core/creative-representation-set.json', '#/properties/representations/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/creative-representation.json', '#/properties/assets', 'patternProperties'),
    ('core/creative-representation.json', '#/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/creative-variant.json', '#/properties/manifest/properties/assets', 'patternProperties'),
    ('core/creative-variant.json', '#/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/0/properties/extensions', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/0/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/0/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/1/properties/creative_manifests/items/properties/assets', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/1/properties/creative_manifests/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/27/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/28/oneOf/2/properties/manifest/properties/assets', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/28/oneOf/2/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('core/mcp-webhook-payload.json', '#/properties/result/anyOf/34/oneOf/0/properties/creatives/items/properties/assignment_errors', 'patternProperties'),
    ('creative/get-creative-delivery-response.json', '#/properties/creatives/items/properties/variants/items/properties/manifest/properties/assets', 'patternProperties'),
    ('creative/get-creative-delivery-response.json', '#/properties/creatives/items/properties/variants/items/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/get-creative-features-request.json', '#/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('creative/get-creative-features-request.json', '#/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/list-creatives-response.json', '#/properties/creatives/items/properties/assets', 'patternProperties'),
    ('creative/list-creatives-response.json', '#/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/list-creatives-response.json', '#/properties/format_summary', 'patternProperties'),
    ('creative/preview-creative-request.json', '#/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('creative/preview-creative-request.json', '#/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/preview-creative-request.json', '#/properties/requests/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('creative/preview-creative-request.json', '#/properties/requests/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/preview-creative-response.json', '#/oneOf/2/properties/manifest/properties/assets', 'patternProperties'),
    ('creative/preview-creative-response.json', '#/oneOf/2/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/sync-creatives-request.json', '#/properties/creatives/items/properties/assets', 'patternProperties'),
    ('creative/sync-creatives-request.json', '#/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('creative/sync-creatives-response.json', '#/oneOf/0/properties/creatives/items/properties/assignment_errors', 'patternProperties'),
    ('creative/validate-input-request.json', '#/properties/manifest/properties/assets', 'patternProperties'),
    ('creative/validate-input-request.json', '#/properties/manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/build-creative-request.json', '#/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('media-buy/build-creative-request.json', '#/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/build-creative-request.json', '#/properties/creative_representation_set/properties/representations/items/properties/assets', 'patternProperties'),
    ('media-buy/build-creative-request.json', '#/properties/creative_representation_set/properties/representations/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/0/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/0/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/1/properties/creative_manifests/items/properties/assets', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/1/properties/creative_manifests/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('media-buy/build-creative-response.json', '#/oneOf/2/properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/create-media-buy-request.json', '#/anyOf/0/properties/packages/items/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/create-media-buy-request.json', '#/anyOf/0/properties/packages/items/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/create-media-buy-request.json', '#/properties/packages/items/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/create-media-buy-request.json', '#/properties/packages/items/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/get-products-response.json', '#/properties/extensions', 'patternProperties'),
    ('media-buy/package-request.json', '#/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/package-request.json', '#/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/package-update.json', '#/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/package-update.json', '#/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/update-media-buy-request.json', '#/properties/new_packages/items/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/update-media-buy-request.json', '#/properties/new_packages/items/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('media-buy/update-media-buy-request.json', '#/properties/packages/items/properties/creatives/items/properties/assets', 'patternProperties'),
    ('media-buy/update-media-buy-request.json', '#/properties/packages/items/properties/creatives/items/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('trusted-match/context-match-response.json', '#/properties/offers/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('trusted-match/context-match-response.json', '#/properties/offers/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('trusted-match/offer.json', '#/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('trusted-match/offer.json', '#/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
    ('trusted-match/provider-context-match-response.json', '#/properties/offers/items/properties/creative_manifest/properties/assets', 'patternProperties'),
    ('trusted-match/provider-context-match-response.json', '#/properties/offers/items/properties/creative_manifest/properties/component_assets/patternProperties/^[a-z][a-z0-9_]*$', 'patternProperties'),
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
#: **ONE SHAPE accounts for 70 of the 89**, so the floor is readable rather than a wall:
#: ``properties/viewability/anyOf`` -- ``core/forecast-point.json``'s and
#: ``core/canonical-forecast-point.json``'s ``viewability``, an ``anyOf`` of two branches
#: §4's dispatch cannot separate -- reached through the forecast/proposal/product closure
#: in 70 places.  The other 19 are in 14 documents and are mostly the
#: ``products``/``partial_results``/``format_options``/``transformers`` ITEM unions, plus
#: three roots (``core/product.json``, ``core/transformer.json``, ``adagents.json``'s
#: conjunct).  Each is a union §4 cannot separate and ``lower.union`` declares nothing at;
#: **none of them is a widening any row chose**, and the row that teaches §4's dispatch a
#: fourth separator empties most of this list in one change.
#:
#: Compared against a FRESH run's declarations and a FRESH run's documents of record, for
#: :data:`DECLARED_WIDENINGS`' reason.  Over the COMMITTED artifact the two directions read
#: 58 stale and 21 silent instead, and that difference is ``adcp-client-python-uqf``.
#:
#: Held as ``document#pointer`` and not as ``harness``'s own sentence, which is the
#: spelling this file already uses for a produced line (``url_typed`` below): the sentence
#: is constant text and the site is the fact.
UNDERDETERMINED_UNIONS: list[str] = [

    'adagents.json#/oneOf/1/allOf/0/anyOf',
    'adagents.json#/oneOf/1/properties/placements/items/properties/format_options/items/anyOf',
    'compliance/comply-test-controller-request.json#/properties/params/properties/result/anyOf/0/properties/products/items/anyOf',
    'compliance/comply-test-controller-request.json#/properties/params/properties/result/anyOf/0/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/comply-test-controller-request.json#/properties/params/properties/result/anyOf/0/properties/proposals/items/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/comply-test-controller-request.json#/properties/params/properties/result/anyOf/0/properties/proposals/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/comply-test-controller-request.json#/properties/params/properties/result/anyOf/1/properties/signals/items/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'compliance/task-completion-data.json#/anyOf/0/properties/products/items/anyOf',
    'compliance/task-completion-data.json#/anyOf/0/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/task-completion-data.json#/anyOf/0/properties/proposals/items/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/task-completion-data.json#/anyOf/0/properties/proposals/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'compliance/task-completion-data.json#/anyOf/1/properties/signals/items/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/0/properties/products/items/anyOf',
    'core/async-response-data.json#/anyOf/0/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/0/properties/proposals/items/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/0/properties/proposals/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/10/oneOf/0/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/15/properties/signals/items/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/3/properties/partial_results/items/anyOf',
    'core/async-response-data.json#/anyOf/3/properties/partial_results/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/5/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/5/properties/proposals/items/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/7/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/7/properties/results/items/properties/proposal/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/async-response-data.json#/anyOf/7/properties/results/items/properties/proposals/items/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/async-response-refs/media-buy/get-products-async-response-input-required.json#/properties/partial_results/items/anyOf',
    'core/async-response-refs/media-buy/get-products-async-response-input-required.json#/properties/partial_results/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/canonical-delivery-forecast.json#/properties/points/items/properties/viewability/anyOf',
    'core/canonical-forecast-point.json#/properties/viewability/anyOf',
    'core/canonical-product.json#/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/canonical-proposal.json#/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/delivery-forecast.json#/properties/points/items/properties/viewability/anyOf',
    'core/forecast-point.json#/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/0/properties/products/items/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/0/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/0/properties/proposals/items/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/0/properties/proposals/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/10/oneOf/0/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/15/properties/signals/items/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/3/properties/partial_results/items/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/3/properties/partial_results/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/5/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/5/properties/proposals/items/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/7/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/7/properties/results/items/properties/proposal/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/mcp-webhook-payload.json#/properties/result/anyOf/7/properties/results/items/properties/proposals/items/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'core/placement-definition.json#/properties/format_options/items/anyOf',
    'core/product-allocation.json#/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/product.json#/anyOf',
    'core/product.json#/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/proposal.json#/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/proposal.json#/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/signal-coverage-forecast.json#/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/transformer.json#/anyOf',
    'core/wholesale-feed-event.json#/$defs/signal/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/wholesale-feed-event.json#/oneOf/0/properties/payload/properties/canonical_product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-event.json#/oneOf/0/properties/payload/properties/product/anyOf',
    'core/wholesale-feed-event.json#/oneOf/0/properties/payload/properties/product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-event.json#/oneOf/1/properties/payload/properties/canonical_product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-event.json#/oneOf/1/properties/payload/properties/product/anyOf',
    'core/wholesale-feed-event.json#/oneOf/1/properties/payload/properties/product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/$defs/signal/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/0/properties/payload/properties/canonical_product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/0/properties/payload/properties/product/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/0/properties/payload/properties/product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/1/properties/payload/properties/canonical_product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/1/properties/payload/properties/product/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/1/properties/payload/properties/product/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/4/properties/payload/properties/signal/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'core/wholesale-feed-webhook.json#/properties/event/oneOf/5/properties/payload/properties/signal/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
    'creative/list-transformers-response.json#/properties/transformers/items/anyOf',
    'governance/check-governance-request.json#/properties/proposal/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/accept-proposal-response.json#/allOf/0/oneOf/0/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/buy-products-response.json#/allOf/0/oneOf/0/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/get-media-buys-response.json#/properties/media_buys/items/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/get-products-async-response-input-required.json#/properties/partial_results/items/anyOf',
    'media-buy/get-products-async-response-input-required.json#/properties/partial_results/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/get-products-response.json#/properties/products/items/anyOf',
    'media-buy/get-products-response.json#/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/get-products-response.json#/properties/proposals/items/properties/allocations/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/get-products-response.json#/properties/proposals/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/list-products-response.json#/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/media-buy-commitment-response.json#/oneOf/0/properties/accepted_proposal/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/refine-proposals-response.json#/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/refine-proposals-response.json#/properties/results/items/properties/proposal/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/refine-proposals-response.json#/properties/results/items/properties/proposals/items/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'media-buy/request-proposals-response.json#/properties/products/items/properties/forecast/properties/points/items/properties/viewability/anyOf',
    'media-buy/request-proposals-response.json#/properties/proposals/items/allOf/0/properties/forecast/allOf/0/properties/points/items/properties/viewability/anyOf',
    'signals/get-signals-response.json#/properties/signals/items/properties/coverage_forecast/properties/points/items/allOf/0/properties/viewability/anyOf',
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

    **THE STALE DIRECTION IS RED, AT 3, AND DELIBERATELY NOT PINNED
    (``adcp-client-python-10l.110``).**  The cause is decided and unwritten rather than
    unknown: ``architecture.md``'s "An approximation's pointer is the SchemaRef spelling"
    (2026-10-29) names exactly this -- a declaration written at the node the WALK reached,
    where the class is stamped at the ``SchemaRef`` spelling one ``allOf`` conjunct away.
    ``adagents.json#/oneOf/1/anyOf`` is declared and separable while
    ``adagents.json#/oneOf/1/allOf/0/anyOf`` is inseparable and declared by nothing: one
    union, two spellings, counted twice.  An equality is an OBLIGATION and not a ratchet,
    so it stays at ``[]`` and reddens until that lands.

    ``silent`` arrives as ``harness``'s own SENTENCE and :data:`UNDERDETERMINED_UNIONS`
    holds the SITE, so the site is taken off the front -- the spelling
    ``tests/test_emit.py`` already uses for a produced line (its ``url_typed`` read).  The
    suffix is constant text and the site is the fact.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    records = {
        document: record
        for document in sorted(out.emitted)
        if isinstance(record := bundle.record(BUNDLE, document), dict)
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
    nothing held it before: the artifact's own declarations were what the census test
    compared the backlog against, so the gap was not a quantity anywhere.
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
