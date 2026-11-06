"""The positions where a document refuses the SDK's own correct output.

Section 6's dump half validates what a class EMITS against the same document that
admitted the input, and it found three pairs where the document refuses the dump. **ONE
decision is re-affirmed and its positions are exempted here; the other was WRONG and its
exemption is gone**:

* **D5 stays.** ``HttpUrl`` keeps a ``format: uri`` position, the document's own
  ``pattern`` stays with the schema half, and the non-round-trip ceiling stands.  The
  DEFECT IS THE PATTERN.  ``^https://[^/?#@]+$`` is the only one of the bundle's eight
  ``uri`` patterns that anchors ``$`` immediately after the authority, and RFC 3986
  section 6.2.3 makes ``https://x.example/`` the normalized form of
  ``https://x.example`` -- so the pattern refuses the canonical spelling of a value it
  accepts, and NO conforming URL library can satisfy it.  Filed upstream as
  :data:`UPSTREAM`, which already argues that these patterns express constraints a
  ``pattern`` cannot carry; the minimal repair is ``^https://[^/?#@]+/?$``.
* **D8 DOES NOT STAY AT A NODE THAT COUNTS KEYS, and this bullet is the retraction.**  It
  read: *"D8 stays.  Absent ``additionalProperties`` means ``extra="ignore"``, so an
  undeclared key is accepted and dropped; an instance whose ONLY key is undeclared
  therefore dumps to ``{}`` and a ``minProperties`` the node states refuses it"* -- and it
  blamed the node for *"stating a property count it does not let a reader satisfy"*.  The
  node states a count over its own keys and lets a reader satisfy it exactly; what dropped
  the key was OUR extra policy.  ``docs/plan/rebuild-plan.md`` §8 sentence 4's second
  consequence (2026-11-03) settles it: *"a count keyword withheld from a class whose extra
  policy drops the keys it counts is not answered by declaring the count -- it is answered
  by the class KEEPING the keys the document counts.  Declaring it would be declaring a
  difference the walk created.  That reverses the ``absent -> ignore`` reading at exactly
  those nodes and nowhere else."*  ``lower.objects.declare_object`` takes that reversal, the one
  class resolves ``extra='allow'``, the key survives the dump, and the pair passes with no
  exemption at all.  So this registry now holds ONE kind of entry and :data:`PIN` is 0.

**D5's OWN NAMED UPGRADE PATH DOES NOT FIX THE FIRST ONE, and it is recorded here so
it is not re-proposed.**  D5 says "carry the sender's string beside the parsed value".
Measured: ``AttestationOriginIssuer(type="origin", origin="https://a.com")`` dumps
``https://a.com/``.  An instance built WITHOUT a payload has no sender bytes, so a
carrier is populated exactly when the harness constructs from a drawn payload -- the
check greens while a consumer constructing directly still emits the refused value.
That is a vacuous pass, not a fix.

**THIS IS THE MOST DANGEROUS FILE IN THE EPIC AND IT IS SHAPED FOR THAT.**  Section 6:
the dump half is the only check that reads what a class DID with a value.  Three
constraints follow, and each is enforced by the shape of this module rather than by a
reader's care:

1. **A LITERAL SET OF POSITIONS, NEVER A PREDICATE.**  D5's own reasoning about the
   https arm applies to its own exemption: a literal set can be audited where a
   predicate cannot, and "does this regex conflict with normalization" is a new
   mechanism with no falsifiable population.  So each entry names one document, one
   pointer, one keyword and THE VALUE THAT KEYWORD HOLDS -- and the value is what makes
   the set shrink on its own: when upstream repairs the pattern, the value stops
   matching at the entry's own pointer and the entry is dead by its own terms.
2. **THE SET IS SHRINK-ONLY WHERE IT IS THIS SDK'S DECISION, AND DERIVED WHERE IT IS
   NOT.**  :data:`PIN` pins the first part by count and is 0.  The second part -- every
   entry whose ``value`` is a pattern of :data:`VIOLATING` -- is an EQUALITY against the
   packaged tree, because the number of positions one upstream pattern reaches is a
   property of how much of the bundle is packaged and not of how permissive this SDK is.
   So that part grows with emission, and may grow ONLY where the new entry names the same
   upstream issue the existing ones name: the question per position is which issue it
   belongs to, never whether the list may be longer.
3. **EVERY ENTRY NAMES ITS UPSTREAM ISSUE**, so nothing here reads as this SDK's own
   decision.  An entry with no named cause is an allowlist wearing a measurement.

**The strike is per keyword at one position, and it is not a relaxation of the accepts
half.**  :func:`struck` removes only the named keyword at only the named pointer, so
every other keyword at that node and every other node still grades.  The instance is
still DRAWN from, and still validated against, the document as it stands; it is the
DUMP that is validated against the struck copy.  That split is the whole of the
exemption: nothing about what the class accepts moves.

**AN ENTRY NAMES A POSITION OF THE PACKAGED DOCUMENT'S OWN TEXT, AND THE STRIKE RESOLVES
IT THROUGH THE SAME EXPANSION THE GRADE USES.**  That sentence is the repair of a defect
this module shipped with, and it is worth stating as two spaces rather than as one
pointer.  The record's text is a DAG: ``codegen.bundle`` stores each distinct subtree
once under ``definitions/Shared<N>`` and references it at every occurrence
(``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT"), and
``adcp.types._base.store_expanded`` puts that storage back for every reader that WALKS a
node -- which is every reader the grade has.  So a node the record hoisted has two
spellings: one in the document's text, at ``/definitions/Shared11/properties/issuer/...``,
and one at each position the document APPLIES it, which is where the pair that is graded
against it reads it.

:func:`applying_to` used to compare an entry's pointer to a pair's pointer by PREFIX, in
the document's text.  A pair's pointer is in the applied space -- ``applied_schema`` takes
the storage hop and the architecture section makes the hoisting invisible to it -- so for
every hoisted position the comparison was between two different spaces and answered ``()``:
24 of the 77 positions below could not be reached from any pair, an entry at one was INERT,
and ``struck`` left the keyword exactly where it was.  **A reader keyed on a pointer whose
space is not the grade's space is green and says nothing**, which is what makes this the
dangerous shape rather than a lookup bug.

The entry keeps the TEXT's spelling, for the reason :data:`EXEMPT`'s first rule gives: the
``value`` is what makes this set shrink by itself, and a reader checks it by opening the
shipped document at the entry's pointer.  :func:`_occurrences` is the one thing that is
new -- the positions the document applies one stored position at, derived by walking the
record through :func:`adcp.types._base.through_the_store`, which is the SAME hop
``store_expanded`` and ``applied_schema`` take.  The strike and the grade therefore
dereference the storage once, in one declaration, and cannot come to disagree about where
a node is.
"""

from __future__ import annotations

import copy
import functools
from typing import Any, NamedTuple

from adcp.types._base import (
    STORE_SECTION,
    _document,
    is_a_store_entry,
    through_the_store,
)

#: The upstream issue, on every entry.  Named once so an entry cannot cite a
#: different one by accident, and spelled with the repository because a bare
#: ``#8398`` does not resolve for a reader outside this tree.
UPSTREAM = "adcontextprotocol/adcp#8398"


class Exemption(NamedTuple):
    """One keyword at one position, with the reason it cannot be satisfied.

    ``document`` and ``pointer`` are the packaged document and the JSON pointer into
    ITS OWN TEXT: section 6 measures the packaged documents at 0 ``$ref``
    occurrences, so a node reached through a ``$ref`` in the bundle source is an
    inlined COPY here, at a pointer of its own.  Many entries below are the same
    authored node for exactly that reason, and that is why they are many entries
    rather than one with a clever matcher: the record's copy is a real position in a
    real packaged document, and naming it is what keeps this a set of pointers.

    **IT IS NOT ``adcp.types._base.SchemaRef``'s SPACE, and the sentence that said so
    was the defect.**  A ``SchemaRef`` pointer is in the APPLIED space -- the record's
    own storage dereferenced -- and this pointer is in the document's TEXT, where the
    storage is still a ``definitions/Shared<N>`` entry and a reference.  The two
    coincide at every position the record did not hoist, which is why the mismatch was
    invisible for 8 entries and fatal for the 24 hoisted ones.  :func:`_occurrences`
    is the crossing, and the module docstring's last two paragraphs are why it is
    here rather than in the entry.

    ``value`` is what the keyword holds today.  It is not decoration: it is the
    mechanism by which this set shrinks without anybody watching.  An entry whose
    value no longer matches the document is a repaired position, and the test
    reddens until the entry goes.

    ``latent`` says the position does not refuse a dump on the committed tree.  It is
    still in the set, because it refuses one for some draws and not others -- a site
    that passes by luck of the draw is not passing, and leaving it out would mean the
    set has to GROW on the day a draw reaches it.
    """

    document: str
    pointer: str
    keyword: str
    value: Any
    reason: str
    latent: bool = False


#: The ``uri`` pattern no URL library can satisfy, as a literal rather than as a rule
#: about regexes.  Measured over all eight patterns the bundle states at a ``format:
#: uri`` node, :data:`tests.test_dump_exemptions.DRAWS` strings drawn per pattern from
#: ``st.from_regex`` and round-tripped through the type ``codegen.constraints.url_type``
#: selects: this one refuses EVERY value its own type re-emits, and it is the only one
#: anchoring ``$`` immediately after the authority.
ORIGIN_ONLY = "^https://[^/?#@]+$"

#: **The SECOND violating pattern, which this module's own docstring predicted**: "a
#: second violating pattern in a later bundle is a second entry here, taken the same way
#: over the whole pattern population."  It is that entry, and it arrived the way the
#: sentence said it would -- by EMISSION, not by a draw: the pattern was already measured
#: as violating and was deliberately not exempt because it reached no emitted document
#: ("the reason it is not exempt is REACH, not rate"), and
#: ``core/agent-reporting-destination-state.json``, ``core/principal-state.json`` and the
#: two principal responses now emit.
#:
#: The defect is the same ONE as :data:`ORIGIN_ONLY`'s -- the pattern forbids a character
#: that URL normalisation PRODUCES, so the document refuses the canonical spelling of a
#: value it accepts -- and :data:`_PCT` names which character and why.  Same upstream
#: issue, which is the only ground on which this set may grow.
PERCENT_FREE = "^https://[!$&-;=@-~]+$"

_RFC = (
    "RFC 3986 S6.2.3 makes 'https://h/' the normalized form of 'https://h', so this "
    "pattern refuses the canonical spelling of a value it accepts and no conforming "
    f"URL library can satisfy it; D5 keeps the URL type, {UPSTREAM} repairs the "
    "pattern (minimally to ^https://[^/?#@]+/?$)"
)

_PCT = (
    "the class admits '{', '}' and '`' in a path and RFC 3986 S2.1 makes their "
    "percent-encoded form the canonical one, so the type re-emits '%7B' for a value "
    "this pattern accepted -- and '%' is outside the pattern's own character class, so "
    "the document refuses the normalized spelling of a value it accepts; D5 keeps the "
    f"URL type, {UPSTREAM} repairs the pattern"
)

#: **The DERIVED part of :data:`EXEMPT`, keyed by the pattern and carrying its reason.**
#: An entry whose ``value`` is one of these is a position of a pattern that refuses its
#: own type's output, and the set of such positions is a property of how much of the
#: bundle is PACKAGED rather than of how permissive this SDK is -- which is why that part
#: is a derived equality and :data:`PIN` covers the rest.
#:
#: Both directions are graded.  ``test_every_violating_uri_pattern_that_reaches_a_pair_is_exempt``
#: asserts that the patterns MEASURED to violate are exactly these, so a third one in a
#: later bundle reddens rather than passing unexempted, and a pattern upstream repairs
#: leaves this mapping with no positions to cover and its entries stale.
VIOLATING: dict[str, str] = {ORIGIN_ONLY: _RFC, PERCENT_FREE: _PCT}

# **THE ``minProperties`` EXEMPTION AND ITS REASON ARE GONE, AND THE FIX IS NOT HERE.**
# What stood here read: "D8 maps a silent additionalProperties to extra='ignore', so an
# undeclared key is accepted and DROPPED; an instance whose only key is undeclared dumps
# to {} and this minProperties refuses it.  D8 stays as written; <upstream> covers the
# node stating a property count it does not let a reader satisfy."  It exempted
# ``core/provenance.json#/properties/disclosure/properties/jurisdictions/items/properties/render_guidance``.
#
# **The node was never at fault and the exemption was describing a difference the WALK
# created** -- which is exactly what §8 sentence 4's second consequence (2026-11-03)
# settles: *"a count keyword withheld from a class whose extra policy drops the keys it
# counts is not answered by declaring the count -- it is answered by the class KEEPING the
# keys the document counts."*  ``lower.objects.declare_object`` takes that reversal, the class
# resolves ``extra='allow'``, the undeclared key SURVIVES the dump, and the document's own
# ``minProperties`` is satisfied by the instance it was always satisfied by.  So the pair
# passes on its own and the entry is removed rather than re-explained.
#
# One entry, one class, and :data:`PIN` falls from 1 to 0 with it: the shrink-only part of
# this registry is now empty, which is the one direction it is allowed to move in.

#: **The whole exemption, as a literal table of POSITIONS.**  77 of them, every one on a
#: pattern of :data:`VIOLATING` and every one DERIVED against the packaged tree: the
#: entries ARE the positions of the documents this tree grades whose ``pattern`` is one of
#: those two exact strings.  Nothing here is pinned and :data:`PIN` is 0.
#:
#: **THE REPEATED FIELDS ARE FACTORED AND THE POSITIONS ARE NOT**, which is this module's
#: first rule followed rather than relaxed: "a literal set of positions, never a
#: predicate".  ``keyword``, ``value`` and ``reason`` are not a judgement about a position
#: -- they are the PATTERN's, one per key of :data:`VIOLATING` -- so writing them out 77
#: times would put 77 copies of one decision in front of a reader who has to audit 77
#: pointers.  What is literal is what a reader checks: one ``(document, pointer)`` per
#: line, resolvable by opening the shipped document, which is what
#: ``test_every_entry_resolves_and_still_states_its_value`` does for every one of them.
#:
#: **IT WAS 8 AND IS 77, AND EVERY ONE OF THE 69 NEW ENTRIES NAMES THE SAME UPSTREAM
#: ISSUE** -- the one growth this set admits, because "the number of positions one
#: upstream pattern reaches is a property of how much of the bundle is PACKAGED, not of
#: how permissive the SDK is".  65 of them are :data:`ORIGIN_ONLY` positions the derived
#: equality had been reporting as MISSED, which is what that equality is built to do; 4
#: are :data:`PERCENT_FREE`'s, a second pattern that reached an emitted document for the
#: first time.  The 8 that were here are among the 77 unchanged.
#:
#: **AND 24 OF THEM COULD NOT HAVE BEEN ADDED BEFORE THE MECHANISM MOVED**, which is why
#: the population is not the whole of this row.  Those pointers are
#: ``/definitions/Shared<N>/...`` -- the record's own storage -- and until
#: :func:`_occurrences` existed, :func:`applying_to` compared them to a pair's pointer in
#: the applied space, answered ``()``, and :func:`struck` left the pattern in place.  An
#: entry at one of them was INERT.  The module docstring's last two paragraphs are the
#: repair; ``test_an_entry_at_a_hoisted_position_lands_where_the_pair_reads_it`` is the
#: direction that was structurally unfailable and now fails on demand.
#:
#: Three shapes account for every position, and the shape is readable off the pointer:
#:
#: * the AUTHORED node, in the document that states the pattern in the bundle source --
#:   ``core/attestation-issuer.json#/oneOf/2/properties/origin`` and the handful like it;
#: * an INLINED copy of one, at a pointer of its own, because ``codegen.bundle.record``
#:   resolves a remote ``$ref`` and section 6 measures the packaged documents at 0
#:   ``$ref`` occurrences.  The bundle source states the pattern at none of these
#:   documents;
#: * a HOISTED copy, which is an inlined copy the record then STORED once and referenced
#:   at each occurrence.  Same text, same authored node; the only difference is that the
#:   document's own text spells it under ``definitions/``.
#:
#: One position of the packaged tree is deliberately NOT here:
#: ``core/async-response-refs/media-buy/get-products-async-response-input-required.json``
#: states :data:`ORIGIN_ONLY` and the tree grades no pair for that document, so the
#: position reaches no dump and an entry at it could never act.  "Reaches a pair" is the
#: population both derived equalities range over, for that reason.
_POSITIONS: dict[str, tuple[tuple[str, str], ...]] = {
    # 73 positions, 24 of them HOISTED by the record.
    ORIGIN_ONLY: (
        ("brand/acquire-rights-response.json", "/oneOf/0/properties/rights_constraint/allOf/0/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("brand/update-rights-response.json", "/oneOf/0/properties/rights_constraint/allOf/0/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("compliance/comply-test-controller-request.json", "/definitions/Shared463/properties/issuer/oneOf/2/properties/origin"),
        ("compliance/task-completion-data.json", "/definitions/Shared439/properties/issuer/oneOf/2/properties/origin"),
        ("core/async-response-data.json", "/definitions/Shared147/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/async-response-data.json", "/definitions/Shared758/properties/issuer/oneOf/2/properties/origin"),
        ("core/attestation-capabilities.json", "/properties/accepted_issuers/items/properties/credential_origins/items"),
        ("core/attestation-capabilities.json", "/properties/accepted_issuers/items/properties/issuer/oneOf/2/properties/origin"),
        ("core/attestation-issuer.json", "/oneOf/2/properties/origin"),
        ("core/attestation-reference.json", "/properties/issuer/oneOf/2/properties/origin"),
        ("core/audience-evidence-requirements.json", "/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/audience-evidence-selection.json", "/definitions/Shared11/properties/issuer/oneOf/2/properties/origin"),
        ("core/audience-evidence.json", "/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/canonical-proposal.json", "/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/creative-asset.json", "/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/creative-manifest.json", "/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/creative-representation-set.json", "/properties/representations/items/allOf/0/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/creative-representation.json", "/allOf/0/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/creative-variant.json", "/allOf/1/properties/manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/mcp-webhook-payload.json", "/definitions/Shared147/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/mcp-webhook-payload.json", "/definitions/Shared758/properties/issuer/oneOf/2/properties/origin"),
        ("core/media-buy.json", "/definitions/Shared98/properties/issuer/oneOf/2/properties/origin"),
        ("core/package.json", "/definitions/Shared49/properties/issuer/oneOf/2/properties/origin"),
        ("core/product-audience-evidence-requirements.json", "/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/product-filters.json", "/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/product-offer-filters.json", "/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("core/product.json", "/definitions/Shared220/properties/issuer/oneOf/2/properties/origin"),
        ("core/rights-attestation-evaluation.json", "/properties/reference/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/rights-constraint.json", "/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("core/wholesale-feed-event.json", "/definitions/Shared436/properties/issuer/oneOf/2/properties/origin"),
        ("core/wholesale-feed-webhook.json", "/definitions/Shared465/properties/issuer/oneOf/2/properties/origin"),
        ("creative/get-creative-delivery-response.json", "/properties/creatives/items/properties/variants/items/allOf/1/properties/manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/get-creative-features-request.json", "/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/list-creatives-response.json", "/definitions/Shared35/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/preview-creative-request.json", "/definitions/Shared11/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/preview-creative-response.json", "/oneOf/2/properties/manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/sync-creatives-request.json", "/properties/creatives/items/allOf/0/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("creative/validate-input-request.json", "/properties/manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("error-details/governance-agent-not-accepted.json", "/oneOf/0/properties/attempted_agent_origin"),
        ("governance/check-governance-request.json", "/properties/proposal/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("governance/check-governance-request.json", "/properties/runtime_attestations/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("governance/get-plan-audit-logs-response.json", "/properties/plans/items/properties/entries/items/properties/runtime_attestations/items/properties/reference/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/accept-proposal-response.json", "/allOf/0/oneOf/0/properties/accepted_proposal/allOf/0/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/build-creative-request.json", "/definitions/Shared9/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/build-creative-response.json", "/definitions/Shared22/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/buy-products-request.json", "/properties/purchases/items/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/buy-products-response.json", "/allOf/0/oneOf/0/properties/accepted_proposal/allOf/0/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/commercial-terms.json", "/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/create-media-buy-request.json", "/definitions/Shared61/oneOf/2/properties/origin"),
        ("media-buy/create-media-buy-response.json", "/definitions/Shared134/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/get-media-buys-response.json", "/properties/media_buys/items/properties/accepted_proposal/allOf/0/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/get-products-async-response-input-required.json", "/definitions/Shared220/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/get-products-request.json", "/properties/filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/get-products-response.json", "/definitions/Shared301/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/list-products-request.json", "/properties/criteria/properties/offer_filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/media-buy-commitment-response.json", "/oneOf/0/properties/accepted_proposal/allOf/0/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/package-request.json", "/definitions/Shared15/oneOf/2/properties/origin"),
        ("media-buy/package-update.json", "/properties/creatives/items/allOf/0/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("media-buy/product-discovery-criteria.json", "/properties/offer_filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/product-purchase-input.json", "/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/product-purchase.json", "/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/proposal-refinement.json", "/properties/criteria/properties/offer_filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/refine-proposals-request.json", "/properties/refinements/items/properties/criteria/properties/offer_filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/refine-proposals-response.json", "/definitions/Shared8/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/request-proposals-request.json", "/properties/criteria/properties/offer_filters/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/request-proposals-response.json", "/properties/proposals/items/allOf/0/properties/commercial_terms/properties/purchases/items/allOf/0/properties/audience_evidence_requirements/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"),
        ("media-buy/update-media-buy-request.json", "/definitions/Shared92/oneOf/2/properties/origin"),
        ("media-buy/update-media-buy-response.json", "/definitions/Shared79/properties/issuer/oneOf/2/properties/origin"),
        ("protocol/get-adcp-capabilities-response.json", "/properties/adcp/properties/attestations/properties/accepted_issuers/items/properties/credential_origins/items"),
        ("protocol/get-adcp-capabilities-response.json", "/properties/adcp/properties/attestations/properties/accepted_issuers/items/properties/issuer/oneOf/2/properties/origin"),
        ("trusted-match/context-match-response.json", "/properties/offers/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("trusted-match/offer.json", "/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
        ("trusted-match/provider-context-match-response.json", "/properties/offers/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/2/properties/origin"),
    ),
    # 4 positions, 0 of them HOISTED by the record.
    PERCENT_FREE: (
        ("core/agent-reporting-destination-state.json", "/properties/setup/properties/setup_url"),
        ("core/principal-state.json", "/properties/reporting_destinations/items/properties/setup/properties/setup_url"),
        ("protocol/get-principal-response.json", "/properties/result/oneOf/0/properties/configuration/properties/reporting_destinations/items/properties/setup/properties/setup_url"),
        ("protocol/sync-principal-response.json", "/properties/result/oneOf/0/properties/configuration/properties/reporting_destinations/items/properties/setup/properties/setup_url"),
    ),
}

#: The positions a pair's dump actually needs on the committed tree, which is the whole of
#: what :attr:`Exemption.latent` is NOT.  Two, and they are the two pairs
#: ``tests.test_dump_exemptions.REFUSED_TODAY`` names -- that file asserts the document
#: still refuses those dumps, so this is the same reading from the position's side rather
#: than a second measurement.
#:
#: Declared in this direction because the field's default is the CLAIM: ``latent=False``
#: says "this position refuses a dump today", and that is a statement about a draw which
#: cannot be made for 75 positions without taking 75 draws.  So the two that are known are
#: named and the rest are latent, which is what the field's own rule asks for -- "a site
#: that passes by luck of the draw is not passing", so it is still in the set.
_REFUSES_A_DUMP_TODAY: frozenset[tuple[str, str]] = frozenset(
    {
        ("core/attestation-issuer.json", "/oneOf/2/properties/origin"),
        (
            "core/attestation-capabilities.json",
            "/properties/accepted_issuers/items/properties/issuer/oneOf/2/properties/origin",
        ),
    }
)

EXEMPT: tuple[Exemption, ...] = tuple(
    Exemption(
        document=document,
        pointer=pointer,
        keyword="pattern",
        value=pattern,
        reason=VIOLATING[pattern],
        latent=(document, pointer) not in _REFUSES_A_DUMP_TODAY,
    )
    for pattern, positions in _POSITIONS.items()
    for document, pointer in positions
)

#: Shrink-only, asserted by ``test_the_exempt_set_only_shrinks``, and over the entries
#: whose ``value`` is NOT a pattern of :data:`VIOLATING`.  A pin and not a ``len()`` read
#: back off the tuple, because a pin a test computes from the thing it grades cannot fail.
#:
#: It covered every entry and was 4.  An absolute count over the derived part had no
#: denominator: the number of positions one upstream pattern reaches is a property of how
#: much of the bundle is PACKAGED, not of how permissive this SDK is, so every row that
#: emits a document carrying that node has to raise it -- which is the one thing a
#: shrink-only pin may not do.  That part is derived now (see :data:`EXEMPT`), and what
#: was left here was the part that genuinely is not a function of emission.
#:
#: **THE PARTITION IS KEYED ON :data:`VIOLATING` AND NOT ON :data:`ORIGIN_ONLY`, which is
#: what kept this at 0 when the second violating pattern arrived.**  It read ``e.value !=
#: ORIGIN_ONLY``, and under that reading :data:`PERCENT_FREE`'s four positions would have
#: been four pinned entries and this pin would have had to rise from 0 to 4 -- for four
#: positions that are a function of EMISSION in exactly the way the split exists to take
#: out of the pin.  ``ORIGIN_ONLY``'s own declaration had already decided it: "a second
#: violating pattern in a later bundle is a second entry here, taken the same way over the
#: whole pattern population."  So the mechanism names the KIND -- a pattern measured to
#: refuse its own type's output -- and the pin keeps counting the part that is this SDK's
#: own decision.
#:
#: **IT IS ZERO**, which is "this part is empty" and not a census: the one
#: ``minProperties`` entry it covered is gone because the pair passes, and §8 sentence 4
#: is what made it pass.  A later row that needs an exemption for a reason that is NOT a
#: violating pattern raises this, and raising it is what ``test_the_exempt_set_only_shrinks``
#: forbids -- so such a row brings the sentence first, which is the whole point of the pin
#: being shrink-only.  At zero it carries its own content: *this SDK exempts no dump for a
#: reason of its own.*
PIN = 0


def applying_to(ref_document: str, ref_pointer: str) -> tuple[Exemption, ...]:
    """The entries that fall inside the node ``(document, pointer)`` names.

    A pair's own node is a subtree, so an entry applies when the document APPLIES its
    position at that pointer or under it -- which is how one entry covers both the union
    root ``core/attestation-issuer.json#`` and the branch pair ``#/oneOf/2`` without being
    written twice.  ``#`` is the root pointer and names the whole document.

    **"Applies at" and not "is spelled under", which is the whole of this module's
    repair.**  An entry's pointer is in the packaged document's own TEXT and a pair's is
    in the applied space, so for a position the record HOISTED the two are different
    strings for one node and a prefix comparison between them answers ``()``.
    :func:`_occurrences` crosses the two, through the same storage hop the grade's own
    accessor takes.  One entry may be applied at several positions inside one pair; it is
    reported here ONCE, in :data:`EXEMPT`'s order, because this answers which entries
    apply and :func:`_strikes` answers where.
    """
    applies = {entry for entry, _ in _strikes(ref_document, ref_pointer)}
    return tuple(e for e in EXEMPT if e in applies)


def _strikes(
    ref_document: str, ref_pointer: str
) -> tuple[tuple[Exemption, tuple[str, ...]], ...]:
    """Each entry inside the node ``(document, pointer)`` names, with WHERE inside it.

    The path is RELATIVE to ``ref_pointer`` and is in the APPLIED space, which is the
    space :func:`struck`'s argument is in: the schema a pair is graded against is
    ``adcp.types._base.schema_at``'s, so the record's storage is already put back in it
    and a ``definitions/Shared<N>`` segment names nothing there.

    One pair per OCCURRENCE and not per entry, because a stored subtree the document
    applies twice inside one pair is two positions of that pair's schema -- which
    ``test_the_strike_removes_only_the_named_keywords`` compares against the difference
    the strike actually made.
    """
    here = [e for e in EXEMPT if e.document == ref_document]
    if not here:  # the pairs with no entry pay nothing, not even the walk
        return ()
    at = _path(ref_pointer)
    applied = _occurrences(ref_document)
    return tuple(
        (entry, occurrence[len(at) :])
        for entry in here
        for occurrence in applied.get(_path(entry.pointer), ())
        if occurrence[: len(at)] == at
    )


def labels(ref_document: str, ref_pointer: str) -> list[str]:
    """What the harness REPORTS for this pair: one label per exemption in force.

    ``"<document>#<pointer>/<keyword>"``, which names the position and the keyword
    together because the position alone does not say what was excused.  Derived from
    the same :func:`applying_to` the strike uses, so the report and the strike cannot
    disagree about which entries applied -- the one failure mode a separately-passed
    list of labels would have.
    """
    return [f"{e.document}#{e.pointer}/{e.keyword}" for e in applying_to(ref_document, ref_pointer)]


def struck(schema: dict, ref_document: str, ref_pointer: str) -> dict:
    """``schema`` with every applicable exempt keyword removed, or ``schema`` itself.

    **Returned by identity when nothing applies**, so a caller can tell an exempted
    pair from an ordinary one without consulting this module twice, and so the
    1,051 pairs that have no entry pay no copy.

    An entry whose pointer does not resolve in ``schema``, or whose keyword is absent
    or holds a different value, is left alone rather than forced: a stale entry is a
    thing for the test to report, not for this function to hide by striking whatever
    it finds at the pointer.

    **The copy keeps the record's own SHARING, and that is deliberate rather than
    incidental.**  ``store_expanded`` places ONE object per stored subtree at every
    occurrence and ``copy.deepcopy`` preserves aliasing, so deleting the keyword at one
    occurrence of a stored node deletes it at all of them.  That is correct and not
    over-reach: every occurrence of one stored subtree is the same authored node holding
    the same keyword, so they are covered by the same entry or by none.  What it means for
    the loop is that the second occurrence finds the keyword already gone, reads a
    ``_MISSING`` that does not equal the entry's value, and does nothing.
    """
    found = _strikes(ref_document, ref_pointer)
    if not found:
        return schema
    out = copy.deepcopy(schema)
    for entry, where in found:
        node = _at(out, where)
        if isinstance(node, dict) and node.get(entry.keyword, _MISSING) == entry.value:
            del node[entry.keyword]
    return out


@functools.cache
def _occurrences(ref_document: str) -> dict[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """Where the document APPLIES each position an entry names, by the position's own path.

    **The crossing between this module's pointer space and the grade's**, and the one
    thing in this file that reads a document.  The record's text is a DAG: a repeated
    subtree is stored once under ``definitions/Shared<N>`` and referenced at each
    occurrence, so a position of the TEXT may be applied at many positions of the schema a
    pair is graded against -- and a position the record did not hoist is applied at
    exactly itself, which is why 8 entries worked and 24 could not.

    Derived by walking the record and taking the storage hop with
    :func:`adcp.types._base.through_the_store`, which is the hop ``store_expanded`` takes
    when it builds the text the grade walks and the hop ``applied_schema`` takes when it
    resolves a pair's pointer.  **The same function and not a second reading of the same
    rule**: a reader keyed on a pointer whose space is not the grade's space is green and
    says nothing, and two derivations of one storage format is how that happens.

    Walked over every VALUE rather than over the schema positions, for
    ``store_expanded``'s own reason: this is not the module that declares which keys hold
    a subschema (``codegen.keywords`` is), and what makes the walk sound is the PREDICATE
    -- ``through_the_store`` hops only for a mapping whose one key is a ``$ref`` naming an
    entry of this root's section, which is the only node the hoisting writes.  The store
    entries are dropped from the section the same way ``store_expanded`` drops them, so no
    answer here is ever a path THROUGH ``definitions/Shared<N>``.

    Cached per document and computed only for the documents :data:`EXEMPT` names -- 72 of
    them, 2.8 s of walking for the whole set, once per process.  A pair whose document has
    no entry never reaches this function at all (:func:`_strikes` returns first).
    """
    wanted = {_path(e.pointer) for e in EXEMPT if e.document == ref_document}
    if not wanted:
        return {}
    root = _document(ref_document)
    found: dict[tuple[str, ...], list[tuple[str, ...]]] = {}

    def visit(node: Any, applied: tuple[str, ...], text: tuple[str, ...]) -> None:
        hopped = through_the_store(node, root)
        if hopped is not node:
            # The occurrence stays where it is and the TEXT moves to the section entry:
            # that is what "the hoisting is a storage representation" means for a pointer.
            entry = str(node["$ref"]).rsplit("/", 1)[-1]
            visit(hopped, applied, (STORE_SECTION, entry))
            return
        if text in wanted:
            found.setdefault(text, []).append(applied)
        if isinstance(node, dict):
            for key, value in node.items():
                if key == STORE_SECTION and isinstance(value, dict):
                    for name, held in value.items():
                        if not is_a_store_entry(name):  # a document's own definition
                            visit(held, (*applied, key, name), (*text, key, name))
                    continue
                visit(value, (*applied, key), (*text, key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, (*applied, str(index)), (*text, str(index)))

    visit(root, (), ())
    return {position: tuple(at) for position, at in found.items()}


#: A sentinel, because an entry's ``value`` may legitimately be ``None`` and
#: ``node.get(kw)`` cannot then tell absence from it.
_MISSING = object()


def _path(pointer: str) -> tuple[str, ...]:
    """A JSON pointer as its segments, with ``#`` and ``#/`` both meaning the root.

    ``~1`` and ``~0`` are RFC 6901's escapes for ``/`` and ``~`` in a key, decoded here
    exactly as ``adcp.types._base.applied_schema`` decodes them: the segments are compared
    against a document's own KEYS -- by :func:`_at`, and by :func:`_occurrences`, which
    builds its paths out of them -- so an escaped segment left encoded would be a segment
    that resolves nowhere.  0 positions of this bundle need it; it is decoded anyway,
    because the alternative is a pointer space that silently cannot name a key with a
    slash in it.
    """
    return tuple(
        p.replace("~1", "/").replace("~0", "~") for p in pointer.lstrip("#").split("/") if p
    )


def _at(node: Any, path: tuple[str, ...]) -> Any:
    """The node ``path`` names, or ``None`` where it does not resolve.

    ``None`` rather than a raise: a pointer that stopped resolving is a stale entry,
    which the test reports by name.  Raising here would turn it into a failure of
    whatever pair happened to be graded first.
    """
    for part in path:
        if isinstance(node, list):
            if not part.isdigit() or int(part) >= len(node):
                return None
            node = node[int(part)]
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node
