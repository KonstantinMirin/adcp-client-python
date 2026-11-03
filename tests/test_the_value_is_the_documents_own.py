"""A ``format: uri`` field carries the document's own string, and both directions of it.

``docs/plan/rebuild-plan.md`` §2 withdrew the pydantic URL type on one ground, and the
ground is value identity rather than taste:

    a pydantic URL lowercases the host and gives an empty path a ``/``, so two distinct
    strings the document admits become one value, and the value dumped is not the string
    supplied.

That damages reading 1 in both of its halves at once, which is what makes it a defect and
not a trade, and this file is the measurement of both halves:

* **The class REFUSES what the document admits.**  ``_runtime.UniqueItems`` compares the
  values it was HANDED, so two document-distinct URI strings that coerce to one value
  collide and the array is refused on its own ``uniqueItems`` -- a narrowing, which §2
  calls "the defect the old sentence was reaching for, and nothing below widens into one".
* **The document refuses OUR OWN DUMP.**  The value stored is the normalised one, so the
  dump carries a string the author never wrote, and a document whose ``pattern`` pins the
  authority exactly (``^https://[^/?#@]+$``) refuses the canonical spelling of a value it
  accepted on the way in.

**A RULE-LEVEL REPAIR IS PROVABLY WRONG and the controls below are how that stays
measured** (§2): neutralise the ``uniqueItems`` comparison and the same pair fails the
other way, because the DUMP then carries the duplicate and the document refuses it on
``uniqueItems``.  So each narrowing site is graded with the duplicate payload beside it:
the document refuses two equal strings and the class must go on refusing them.  A green
run here says the type became injective, not that the rule was turned off.

**THE PAYLOADS ARE WRITTEN DOWN, and §2 says why they have to be**: "none of the
narrowing's measured pairs appears among the failures of a whole-set grade, because a draw
does not produce two case-differing URLs by chance; the payloads had to be constructed by
hand.  An unadmitted narrowing is exactly the fact no instrument finds."  This file is
therefore a report on the sites it names and on no others -- §8's "a check that enumerates
a subset reports on that subset only, and says so" -- and the SETS it ranges over are
named rather than counted.  The population-wide reading of the same obligation is the
accepts draw (``tests/test_emit.py``), which is blind here for the reason just quoted.

**The DOCUMENT's verdict is read the way production reads it** -- the draft the document
declares, with that draft's own ``FormatChecker``, built on the record ROOT and evolved
onto the node, which is ``adcp.types._base._refuse_at``'s arrangement and is what makes a
local ``#/definitions/...`` inside a nested node resolve.  Read here rather than borrowed,
so the two halves of each assertion come from two readers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

import jsonschema
import pytest

from codegen import bundle
from tests import compared
from tests.nodeset import claimed

BUNDLE = Path("schemas/cache/3.2")

#: A digest the two ``^sha256:[a-f0-9]{64}$`` positions of the dump sites accept.  Not a
#: drawn value: these payloads are hand-built around ONE field, and every other field is
#: the cheapest thing the document admits so that a failure names the URI and nothing else.
DIGEST = "sha256:" + "a" * 64

#: The subject ``core/audience-evidence.json``'s attestation reference requires, which its
#: second ``allOf`` arm pins to the audience-evidence resource vocabulary.
AUDIENCE_EVIDENCE_SUBJECT = {
    "type": "resource",
    "resource_type": "https://adcontextprotocol.org/claims/subjects/audience-evidence",
    "namespace": "https://adcontextprotocol.org/claims",
    "id": "x",
    "content_digest": DIGEST,
}


class Narrowing(NamedTuple):
    """One site where two document-distinct URI strings coerce to one value.

    ``admitted`` is the payload the document admits and the class must construct.
    ``refused`` is the SAME payload with the two strings made equal, which the document
    refuses on its own ``uniqueItems`` -- the control that says the rule is still live.
    """

    document: str
    pointer: str
    admitted: dict[str, Any]
    refused: dict[str, Any]


class Roundtrip(NamedTuple):
    """One site where the value dumped is not the string supplied.

    ``field`` is the instance path of the URI the type rewrites, read back off the dump so
    a failure names the value rather than the pair.
    """

    document: str
    pointer: str
    payload: dict[str, Any]
    field: tuple[Any, ...]


#: §2's three ``uniqueItems`` sites, each with the pair of host-case-differing strings
#: ``adcp-client-python-82m.19`` measured it on.  ``https://A.com`` and ``https://a.com``
#: are distinct JSON strings; a pydantic URL type makes both ``https://a.com/``.
NARROWINGS = (
    Narrowing(
        document="core/attestation-capabilities.json",
        pointer="#",
        admitted={
            "accepted_claim_types": ["https://a.com/x"],
            "accepted_proof_formats": ["https://A.com", "https://a.com"],
            "supported_delivery_methods": ["credential_uri"],
            "accepted_issuers": [
                {"issuer": {"type": "agent", "agent_url": "https://a.com/"}}
            ],
        },
        refused={
            "accepted_claim_types": ["https://a.com/x"],
            "accepted_proof_formats": ["https://a.com", "https://a.com"],
            "supported_delivery_methods": ["credential_uri"],
            "accepted_issuers": [
                {"issuer": {"type": "agent", "agent_url": "https://a.com/"}}
            ],
        },
    ),
    Narrowing(
        document="core/attestation-capabilities.json",
        pointer="#/properties/accepted_issuers/items",
        admitted={
            "issuer": {"type": "agent", "agent_url": "https://a.com/"},
            "claim_types": ["https://A.com", "https://a.com"],
        },
        refused={
            "issuer": {"type": "agent", "agent_url": "https://a.com/"},
            "claim_types": ["https://a.com", "https://a.com"],
        },
    ),
    Narrowing(
        document="core/product-audience-evidence-requirements.json",
        pointer="#",
        admitted={
            "evidence_presence": "required",
            "requirement_mode": "required",
            "accepted_attestation_claim_types": ["https://A.com", "https://a.com"],
        },
        refused={
            "evidence_presence": "required",
            "requirement_mode": "required",
            "accepted_attestation_claim_types": ["https://a.com", "https://a.com"],
        },
    ),
)

#: §2's two round-trip sites.  Both documents pin the authority with no path
#: (``^https://[^/?#@]+$``), so the trailing ``/`` a URL type adds is a value the document
#: refuses -- RFC 3986 §6.2.3 makes it the normalized form, which is the upstream half of
#: the same fact and is why no rewriting of the pattern is wanted here.
ROUNDTRIPS = (
    Roundtrip(
        document="core/audience-evidence.json",
        pointer="#/properties/attestation_refs/items",
        payload={
            "issuer": {"type": "origin", "origin": "https://O.A3Y6.vacaTIonS"},
            "claim_type": "https://adcontextprotocol.org/claims/audience",
            "subject": AUDIENCE_EVIDENCE_SUBJECT,
            "locator": {
                "type": "credential_uri",
                "credential_uri": "https://issuer.example/c",
            },
        },
        field=("issuer", "origin"),
    ),
    Roundtrip(
        document="core/product-offer-filters.json",
        pointer="#",
        payload={
            "audience_evidence_requirements": {
                "requirement_mode": "required",
                "evidence_presence": "required",
                "accepted_attestation_issuers": [
                    {"type": "origin", "origin": "https://Qo1P.here"}
                ],
            }
        },
        field=("audience_evidence_requirements", "accepted_attestation_issuers", 0, "origin"),
    ),
)


def _at(record: Any, pointer: str) -> Any:
    """The node ``pointer`` names inside ``record``."""
    cur = record
    for part in [p for p in pointer.split("/") if p and p != "#"]:
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def _document_refusals(document: str, pointer: str, instance: Any) -> list[str]:
    """Which keywords the DOCUMENT refuses ``instance`` on at ``pointer``, or none.

    The draft comes off the record root, the format checker is that draft's own, and the
    validator is evolved onto the node -- ``_base._refuse_at``'s three decisions, because
    a nested node declares no ``$schema`` and its local ``$ref``\\ s point at the root.
    """
    root = bundle.record(BUNDLE, document, set(bundle.portable(BUNDLE)))
    assert isinstance(root, dict), f"{document} has no document of record"
    validator = jsonschema.validators.validator_for(root, jsonschema.Draft7Validator)
    at_the_node = validator(root, format_checker=validator.FORMAT_CHECKER).evolve(
        schema=_at(root, pointer)
    )
    return [
        error.validator if isinstance(error.validator, str) else "schema"
        for error in at_the_node.iter_errors(instance)
    ]


def _model(document: str, pointer: str) -> Any:
    """The pair of the FRESH tree at this document and pointer.

    ``tests/compared.pairs`` is the suite's one pairing and the tree is the one a fresh run
    emits, so this reaches the compiler under test rather than the committed artifact.
    """
    found = [
        pair
        for pair in compared.pairs()
        if pair.ref.document == document and pair.ref.pointer == pointer
    ]
    assert len(found) == 1, f"{document}{pointer} reached {len(found)} pairs"
    return found[0]


@pytest.mark.parametrize("site", NARROWINGS, ids=lambda s: f"{s.document}{s.pointer}")
def test_the_class_admits_two_uris_the_document_calls_distinct(site: Narrowing) -> None:
    """Reading 1's refusal half: no ``format: uri`` position narrows its document.

    Three assertions, and the middle one is the obligation.  The document admits the
    payload -- asserted rather than assumed, because a payload the document refuses would
    make the class's refusal correct and the check vacuous.  The class constructs it.  And
    the two strings SURVIVE as two: a class that accepted the payload by collapsing the
    array to one member would pass the second assertion while still having lost the fact.
    """
    assert not _document_refusals(site.document, site.pointer, site.admitted)
    value = _model(site.document, site.pointer).accept(site.admitted)
    dumped = value.model_dump(mode="json", exclude_none=True)
    assert not _document_refusals(site.document, site.pointer, dumped)


@pytest.mark.parametrize("site", NARROWINGS, ids=lambda s: f"{s.document}{s.pointer}")
def test_the_duplicate_the_document_refuses_is_still_refused(site: Narrowing) -> None:
    """The control §2 calls the proof that a rule-level repair is wrong.

    The same array with the two strings made EQUAL is refused by the document on its own
    ``uniqueItems``, and must be refused by the class too.  Without this, neutralising the
    comparison would turn the test above green and move the failure into the dump.
    """
    assert "uniqueItems" in _document_refusals(site.document, site.pointer, site.refused)
    with pytest.raises(Exception):
        _model(site.document, site.pointer).accept(site.refused)


@pytest.mark.parametrize("site", ROUNDTRIPS, ids=lambda s: f"{s.document}{s.pointer}")
def test_the_dump_carries_the_string_the_document_was_given(site: Roundtrip) -> None:
    """Reading 1's dump half: what the class dumps validates against the document again.

    The value is asserted by IDENTITY against the string supplied, not merely by the
    document's verdict on the dump, because the two are different claims: a document whose
    pattern happened to admit the normalised form would pass the verdict while the value
    had still been rewritten, and every fact that depends on value identity -- a
    ``uniqueItems``, a ``const``, an origin comparison a consumer makes -- is damaged
    either way.
    """
    assert not _document_refusals(site.document, site.pointer, site.payload)
    value = _model(site.document, site.pointer).accept(site.payload)
    dumped = value.model_dump(mode="json", exclude_none=True)
    assert _read(dumped, site.field) == _read(site.payload, site.field)
    assert not _document_refusals(site.document, site.pointer, dumped)


def _read(instance: Any, path: tuple[Any, ...]) -> Any:
    cur = instance
    for step in path:
        cur = cur[step]
    return cur


def test_every_site_this_file_grades_is_named() -> None:
    """§8: the sets are named, so a parametrisation that selected nothing is a failure.

    Both sets at once, because they are two readings of ONE cause -- §2's "one type
    decision, a narrowing and a broken round trip" -- and a file that graded the refusal
    half alone would report the withdrawal as done while the dump half still carried a
    value no author wrote.
    """
    claimed(
        "uniqueItems sites where two document-distinct URI strings coerce equal",
        {(s.document, s.pointer) for s in NARROWINGS},
    )
    claimed(
        "sites where the dump is a URI the author did not write",
        {(s.document, s.pointer) for s in ROUNDTRIPS},
    )
