"""The positions where a document refuses the SDK's own correct output.

Section 6's dump half validates what a class EMITS against the same document that
admitted the input, and it found three pairs where the document refuses the dump.
Two decisions were re-affirmed rather than amended, so those positions are exempted
here instead:

* **D5 stays.** ``HttpUrl`` keeps a ``format: uri`` position, the document's own
  ``pattern`` stays with the schema half, and the non-round-trip ceiling stands.  The
  DEFECT IS THE PATTERN.  ``^https://[^/?#@]+$`` is the only one of the bundle's eight
  ``uri`` patterns that anchors ``$`` immediately after the authority, and RFC 3986
  section 6.2.3 makes ``https://x.example/`` the normalized form of
  ``https://x.example`` -- so the pattern refuses the canonical spelling of a value it
  accepts, and NO conforming URL library can satisfy it.  Filed upstream as
  :data:`UPSTREAM`, which already argues that these patterns express constraints a
  ``pattern`` cannot carry; the minimal repair is ``^https://[^/?#@]+/?$``.
* **D8 stays.** Absent ``additionalProperties`` means ``extra="ignore"``, so an
  undeclared key is accepted and dropped; an instance whose ONLY key is undeclared
  therefore dumps to ``{}`` and a ``minProperties`` the node states refuses it.

**D5's OWN NAMED UPGRADE PATH DOES NOT FIX THE FIRST ONE, and it is recorded here so
it is not re-proposed.**  D5 says "carry the sender's string beside the parsed value".
Measured: ``AttestationOriginIssuer(type="origin", origin="https://a.com")`` dumps
``https://a.com/``.  An instance built WITHOUT a payload has no sender bytes, so a
carrier is populated exactly when the harness constructs from a drawn payload -- the
check greens while a consumer constructing directly still emits the refused value.
That is a vacuous pass, not a fix.

**THIS IS THE MOST DANGEROUS FILE IN THE EPIC AND IT IS SHAPED FOR THAT.**  Section 6:
widening the comparison removes the only check that reads the generated code, and the
dump half is the only check that reads what a class DID with a value.  Three
constraints follow, and ``tests/test_dump_exemptions.py`` enforces every one:

1. **A LITERAL SET OF POSITIONS, NEVER A PREDICATE.**  D5's own reasoning about the
   https arm applies to its own exemption: a literal set can be audited where a
   predicate cannot, and "does this regex conflict with normalization" is a new
   mechanism with no falsifiable population.  So each entry names one document, one
   pointer, one keyword and THE VALUE THAT KEYWORD HOLDS -- and the value is what makes
   the set shrink on its own: when upstream repairs the pattern, the value stops
   matching and the test reddens until the entry is removed.
2. **THE SET ONLY SHRINKS**, pinned by count.
3. **EVERY ENTRY NAMES ITS UPSTREAM ISSUE**, so nothing here reads as this SDK's own
   decision.

**The strike is per keyword at one position, and it is not a relaxation of the accepts
half.**  :func:`struck` removes only the named keyword at only the named pointer, so
every other keyword at that node and every other node still grades.  The instance is
still DRAWN from, and still validated against, the document as it stands; it is the
DUMP that is validated against the struck copy.  That split is the whole of the
exemption: nothing about what the class accepts moves.
"""

from __future__ import annotations

import copy
from typing import Any, NamedTuple

#: The upstream issue, on every entry.  Named once so an entry cannot cite a
#: different one by accident, and spelled with the repository because a bare
#: ``#8398`` does not resolve for a reader outside this tree.
UPSTREAM = "adcontextprotocol/adcp#8398"


class Exemption(NamedTuple):
    """One keyword at one position, with the reason it cannot be satisfied.

    ``document`` and ``pointer`` are the packaged document and the JSON pointer
    into it -- the same space ``adcp.types._base.SchemaRef`` names, which is the
    only space the harness ever sees: section 6 measures the packaged documents at
    0 ``$ref`` occurrences, so a node reached through a ``$ref`` in the bundle
    source is an inlined COPY here, at a pointer of its own.  Two entries below are
    the same authored node for exactly that reason, and that is why they are two
    entries rather than one with a clever matcher: the record's copy is a real
    position in a real packaged document, and naming it is what keeps this a set of
    pointers.

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


#: The one ``uri`` pattern no URL library can satisfy, as a literal rather than as a
#: rule about regexes.  Measured over all eight patterns the bundle states at a
#: ``format: uri`` node, 40 strings drawn per pattern from ``st.from_regex`` and
#: round-tripped through the type ``codegen.constraints.url_type`` selects: this is
#: the only one whose own type's OUTPUT it refuses, and it is the only one anchoring
#: ``$`` immediately after the authority.  ``tests/test_dump_exemptions.py`` re-takes
#: that measurement over the whole pattern population, so a second violating pattern
#: in a later bundle reddens rather than arriving silently.
ORIGIN_ONLY = "^https://[^/?#@]+$"

_RFC = (
    "RFC 3986 S6.2.3 makes 'https://h/' the normalized form of 'https://h', so this "
    "pattern refuses the canonical spelling of a value it accepts and no conforming "
    f"URL library can satisfy it; D5 keeps the URL type, {UPSTREAM} repairs the "
    "pattern (minimally to ^https://[^/?#@]+/?$)"
)

_D8 = (
    "D8 maps a silent additionalProperties to extra='ignore', so an undeclared key is "
    "accepted and DROPPED; an instance whose only key is undeclared dumps to {} and "
    f"this minProperties refuses it.  D8 stays as written; {UPSTREAM} covers the node "
    "stating a property count it does not let a reader satisfy"
)

#: **The whole exemption.**  Six positions: five on :data:`ORIGIN_ONLY`, which are
#: DERIVED against the packaged tree, and one on ``minProperties``, which is pinned.
#:
#: Three of the four are one authored node, ``core/attestation-issuer.json``'s
#: ``AttestationOriginIssuer.origin``, which the record inlines into
#: ``core/attestation-capabilities.json`` and into
#: ``core/audience-evidence-requirements.json`` as well.
#:
#: **The ORIGIN_ONLY part is not a count any more**, and the reason is the failure that
#: changed it.  It read "the bundle SOURCE states ORIGIN_ONLY at four positions and the
#: packaged tree carries three of them", naming two missing SOURCE positions in documents
#: the emitter does not emit -- ``core/product-audience-evidence-requirements.json`` and
#: ``error-details/governance-agent-not-accepted.json``, both still unemitted.  That
#: enumeration counted SOURCE positions, so an INLINED copy of an already-exempted node
#: had nowhere to be counted: when ``salesagent-j3k2l.43`` made
#: ``core/audience-evidence-requirements.json`` emit, its packaged form inlined the node a
#: third time, the position reached a pair, and a shrink-only count was one short of the
#: positions it exists to cover with no way to say so.
#:
#: So ``test_the_origin_only_part_is_the_packaged_positions`` asserts the equality
#: instead: the ORIGIN_ONLY entries ARE the positions of the packaged tree whose
#: ``pattern`` is that exact string.  Both sides derived, neither a literal count.  It
#: reddens when a position is MISSED rather than when a number moves, it shrinks on its
#: own when upstream repairs the pattern (the value stops matching and both sides fall
#: together), and it grows only with emission -- growth explained by one upstream issue
#: rather than by a judgement call.  It is still a literal SET of positions compared
#: against one exact string, not a predicate over regexes, which is the constraint this
#: module's first rule states.
#:
#: **One exposure is accepted and measured rather than papered over.**  Entry four's
#: authored node is inlined at 90 positions of the packaged tree, and only the one
#: named here is a pair's own root.  At the other 89 the node is nested inside a
#: larger pair, where a refusal needs a drawn instance that gives ``render_guidance``
#: exactly one key and that key undeclared; none does on the committed tree.  If one
#: ever fires, that is a measurement saying this exemption's SHAPE needs revisiting --
#: it is not an entry to add, because adding one would grow the set.
EXEMPT: tuple[Exemption, ...] = (
    Exemption(
        document="core/attestation-issuer.json",
        pointer="/oneOf/2/properties/origin",
        keyword="pattern",
        value=ORIGIN_ONLY,
        reason=_RFC,
    ),
    Exemption(
        # The resolver's inlined copy of the entry above, which is why the two are
        # separate entries: this pointer is a position of attestation-capabilities'
        # own packaged document and the pair graded against it is a different pair.
        document="core/attestation-capabilities.json",
        pointer="/properties/accepted_issuers/items/properties/issuer/oneOf/2/properties/origin",
        keyword="pattern",
        value=ORIGIN_ONLY,
        reason=_RFC,
    ),
    Exemption(
        document="core/attestation-capabilities.json",
        pointer="/properties/accepted_issuers/items/properties/credential_origins/items",
        keyword="pattern",
        value=ORIGIN_ONLY,
        reason=_RFC,
        latent=True,
    ),
    Exemption(
        # A THIRD packaged copy of entry one's authored node, and the same mechanism as
        # entry two: the record inlines ``core/attestation-issuer.json``'s origin
        # branch here, so this is a position of audience-evidence-requirements' own
        # packaged document and the pair graded against it is a different pair.  The
        # bundle SOURCE does not state the pattern at this document at all.
        #
        # It reached a pair when ``salesagent-j3k2l.43`` made the document EMIT -- a
        # composition merges by intersection, so the restatement its root composes is no
        # longer refused.  The comment above anticipated the shape and mis-categorised
        # it: the two positions it names as missing are SOURCE positions in documents
        # still unemitted, and it was counting source positions, so an inlined copy of an
        # already-exempted node had nowhere to be counted.
        document="core/audience-evidence-requirements.json",
        pointer=(
            "/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"
        ),
        keyword="pattern",
        value=ORIGIN_ONLY,
        reason=_RFC,
    ),
    Exemption(
        # A FOURTH packaged copy of entry one's authored node, at the same pointer shape
        # as the entry above, in a different document.
        #
        # It reaches a pair only on the MERGED compiler.  Neither ``salesagent-j3k2l.43``
        # nor ``.67`` emits this document alone; the composition rule and the
        # nested-union sibling rule together clear its last refusal, so the first tree
        # that carries it is the one a merge of the two emits.  That is the case the
        # derived check exists for: under an absolute count this position would have
        # obliged a second rise of a shrink-only pin within the hour, and the pin could
        # not have said WHICH position was missing.
        document="core/product-audience-evidence-requirements.json",
        pointer=(
            "/properties/accepted_attestation_issuers/items/oneOf/2/properties/origin"
        ),
        keyword="pattern",
        value=ORIGIN_ONLY,
        reason=_RFC,
    ),
    Exemption(
        document="core/provenance.json",
        pointer=(
            "/properties/disclosure/properties/jurisdictions/items/properties/render_guidance"
        ),
        keyword="minProperties",
        value=1,
        reason=_D8,
    ),
)

#: Shrink-only, asserted by ``test_the_exempt_set_only_shrinks``, and over the entries
#: that are NOT :data:`ORIGIN_ONLY` -- one, the ``minProperties`` position.  A pin and not
#: a ``len()`` read back off the tuple, because a pin a test computes from the thing it
#: grades cannot fail.
#:
#: It covered every entry and was 4.  An absolute count over the ORIGIN_ONLY part had no
#: denominator: the number of positions one upstream pattern reaches is a property of how
#: much of the bundle is PACKAGED, not of how permissive this SDK is, so every row that
#: emits a document carrying that node has to raise it -- which is the one thing a
#: shrink-only pin may not do.  That part is derived now (see :data:`EXEMPT`), and what
#: is left here is the part that genuinely is not a function of emission.
PIN = 1


def applying_to(ref_document: str, ref_pointer: str) -> tuple[Exemption, ...]:
    """The entries that fall inside the node ``(document, pointer)`` names.

    A pair's own node is a subtree, so an entry applies when its pointer IS that
    pointer or lies under it -- which is how one entry covers both the union root
    ``core/attestation-issuer.json#`` and the branch pair ``#/oneOf/2`` without being
    written twice.  ``#`` is the root pointer and names the whole document.
    """
    at = _path(ref_pointer)
    return tuple(
        e
        for e in EXEMPT
        if e.document == ref_document and _path(e.pointer)[: len(at)] == at
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
    """
    found = applying_to(ref_document, ref_pointer)
    if not found:
        return schema
    out = copy.deepcopy(schema)
    at = _path(ref_pointer)
    for entry in found:
        node = _at(out, _path(entry.pointer)[len(at) :])
        if isinstance(node, dict) and node.get(entry.keyword, _MISSING) == entry.value:
            del node[entry.keyword]
    return out


#: A sentinel, because an entry's ``value`` may legitimately be ``None`` and
#: ``node.get(kw)`` cannot then tell absence from it.
_MISSING = object()


def _path(pointer: str) -> tuple[str, ...]:
    """A JSON pointer as its segments, with ``#`` and ``#/`` both meaning the root."""
    return tuple(p for p in pointer.lstrip("#").split("/") if p)


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
