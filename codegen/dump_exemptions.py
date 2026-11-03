"""The positions where a document refuses the SDK's own correct output.

Section 6's dump half validates what a class EMITS against the same document that
admitted the input.  It found three pairs where the document refused the dump; **two of
the three were this SDK's defect and are fixed rather than exempted**, and what is left
here is the one that is upstream's.

* **THE ``format: uri`` POSITIONS ARE GONE, because the defect was ours** (section 2's
  withdrawal, 2026-11-02).  Eight entries stood here on one pattern,
  ``^https://[^/?#@]+$`` -- the only one of the bundle's ``uri`` patterns that anchors
  ``$`` immediately after the authority, which RFC 3986 section 6.2.3 makes unsatisfiable
  by a NORMALIZING URL library, since ``https://x.example/`` is the normalized form of
  ``https://x.example``.  The reading was that the pattern was the defect and the type
  was kept.  It is the other way round: a pydantic URL type rewrites the value, so what
  the class dumped was never the string it was handed, and the SAME type decision also
  made the class refuse two URIs the document calls distinct.  The type is withdrawn, a
  ``format: uri`` field carries the document's own string, and every one of those dumps
  satisfies its own pattern with nothing struck.
  ``tests/test_dump_exemptions.py`` re-measures that over every ``uri`` pattern the
  bundle states, so the entries cannot come back unnoticed, and
  ``tests/test_the_value_is_the_documents_own.py`` holds the payloads.
  :data:`UPSTREAM` still argues upstream that the pattern expresses a constraint a
  ``pattern`` cannot carry, and the minimal repair is still ``^https://[^/?#@]+/?$`` --
  but nothing of ours now waits on it.
* **D8 stays, and it is the one entry left.** Absent ``additionalProperties`` means
  ``extra="ignore"``, so an undeclared key is accepted and dropped; an instance whose
  ONLY key is undeclared therefore dumps to ``{}`` and a ``minProperties`` the node
  states refuses it.

**THIS IS THE MOST DANGEROUS FILE IN THE EPIC AND IT IS SHAPED FOR THAT.**  Section 6:
the dump half is the only check that reads what a class DID with a value.  Three
constraints follow, and each is enforced by the shape of this module rather than by a
reader's care:

1. **A LITERAL SET OF POSITIONS, NEVER A PREDICATE.**  A literal set can be audited
   where a predicate cannot, and "does this regex conflict with normalization" is a new
   mechanism with no falsifiable population.  So each entry names one document, one
   pointer, one keyword and THE VALUE THAT KEYWORD HOLDS -- and the value is what makes
   the set shrink on its own: when upstream repairs the position, the value stops
   matching at the entry's own pointer and the entry is dead by its own terms.
2. **THE SET ONLY SHRINKS**, pinned by count.
3. **EVERY ENTRY NAMES ITS UPSTREAM ISSUE**, so nothing here reads as this SDK's own
   decision.  The eight that left were the counter-example and the reason this rule is
   not enough on its own: they named an upstream issue and were still ours, because an
   annotation that rewrites a value is a defect no repair of the document can reach.

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

    **There is no ``latent`` flag any more.**  One entry carried it -- the position
    refused a dump for some draws and not others, so leaving it out would have meant the
    set growing on the day a draw reached it -- and that entry was a ``format: uri``
    position, withdrawn with the type (see the module docstring).  Nothing set the field
    and nothing read it, which in a module shaped this deliberately is a line a reader has
    to account for and cannot.
    """

    document: str
    pointer: str
    keyword: str
    value: Any
    reason: str


_D8 = (
    "D8 maps a silent additionalProperties to extra='ignore', so an undeclared key is "
    "accepted and DROPPED; an instance whose only key is undeclared dumps to {} and "
    f"this minProperties refuses it.  D8 stays as written; {UPSTREAM} covers the node "
    "stating a property count it does not let a reader satisfy"
)

#: **The whole exemption: ONE position.**  The ``minProperties`` node of
#: ``core/provenance.json``, which D8 cannot satisfy and upstream can.
#:
#: **It held nine.** Eight were ``format: uri`` positions on one pattern, and they are
#: gone with the type that needed them rather than with an upstream repair -- see the
#: module docstring.  Those eight were also the reason the set had a DERIVED half: the
#: number of positions one upstream pattern reaches is a property of how much of the
#: bundle is PACKAGED, not of how permissive this SDK is, so every row that emitted a
#: document carrying that authored node added a position and a shrink-only count could
#: not express it.  With them gone the whole set is pinned again (:data:`PIN`), which is
#: the stronger statement and is the one this module wanted in the first place.
#:
#: **One exposure is accepted and measured rather than papered over.**  The entry's
#: authored node is inlined at 90 positions of the packaged tree, and only the one named
#: here is a pair's own root.  At the other 89 the node is nested inside a larger pair,
#: where a refusal needs a drawn instance that gives ``render_guidance`` exactly one key
#: and that key undeclared; none does on the committed tree.  If one ever fires, that is
#: a measurement saying this exemption's SHAPE needs revisiting -- it is not an entry to
#: add, because adding one would grow the set.
EXEMPT: tuple[Exemption, ...] = (
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

#: Shrink-only, asserted by ``test_the_exempt_set_only_shrinks``, and over the WHOLE set
#: now that the derived half is gone.  A pin and not a ``len()`` read back off the tuple,
#: because a pin a test computes from the thing it grades cannot fail.
#:
#: It covered every entry, was raised to 4, then split so that the eight ``format: uri``
#: positions could be derived instead -- see :data:`EXEMPT`.  Those are withdrawn, so the
#: split has nothing left to cover and the pin is whole again at 1.
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
