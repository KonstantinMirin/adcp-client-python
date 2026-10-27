"""The patch set for upstream #8525, and the evidence that it preserves acceptance.

``docs/plan/rebuild-plan.md`` §1, "A patched bundle is a legitimate input, and the test is
the RECORD".  The patch extracts five repeated subschemas into their own titled documents
and ``$ref``\\ s them at 307 sites, and the claim it makes -- the claim #8525 makes to
upstream -- is that **resolving the patch returns the published bundle.**

THIS FILE IS THE EVIDENCE, and it is worth more than the extraction.  A reviewer who does
not trust us runs it: it ranges over every one of the 1,054 portable documents, derived
from ``bundle.portable`` and never written down, and a failure names the document and the
pointer.

**It is minutes, not seconds.**  ``bundle.record`` is O(paths through the reference graph)
and the check takes 2,108 records.  The population is the bundle and there is no sampling
of it that would answer the question, so the cost is paid once, in one test, and the
differences it computes are shared by the assertions that read them.

**What it reports today, and the decision it is waiting on.**  Zero differences a
validator can act on -- no acceptance keyword moves at any pointer of any document.  But
NOT zero differences: a record inlines its target whole, so a patched site also gains the
``$schema`` and ``title`` of the document it now references, and the ``description`` where
it stated none.  §1 says byte-identical, and §1 also says "extracting it into a TITLED
``core/currency-code.json``", and those two sentences cannot both hold -- the title is
exactly what the record gains.  So this file asserts the strongest thing that is TRUE,
names the gap, and leaves the line itself for the plan to move.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from codegen import bundle, patch
from tests.nodeset import claimed, ratchet

#: The published bundle the patch is stated against.
PUBLISHED = Path("schemas/cache/3.2")
#: The patch set: a manifest and the documents it adds.
PATCH_SET = Path("patches/8525")

#: The keys a patched site gains because a record inlines its target WHOLE.  Every one of
#: them is an annotation by ``bundle.is_an_annotation`` at the position it lands at, which
#: is what :func:`test_no_record_difference_is_seen_by_a_validator` asserts mechanically;
#: this tuple is the narrower claim that no OTHER annotation moves either, so a patch
#: document growing an ``examples`` or an ``x-`` key is reported rather than absorbed.
NAMES_THE_PATCH_ADDS = ("$schema", "description", "title")


@pytest.fixture(scope="session")
def patched(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The published bundle with the patch set applied, built once."""
    out = tmp_path_factory.mktemp("patched") / "bundle"
    patch.apply(PUBLISHED, PATCH_SET, out)
    return out


@pytest.fixture(scope="session")
def differences(patched: Path) -> list[patch.Difference]:
    """Every pointer at which a patched document's record differs from the published one.

    One computation for the whole file: §1's check over all 1,054 documents, which is the
    expensive thing here and is read by three assertions.
    """
    return list(patch.differing(PUBLISHED, patched))


def test_the_measurement_8525_argues_from_is_reproducible() -> None:
    """#8525's figures, recomputed from the walk the rewrite itself descends.

    The issue argues from a census -- "110 distinct ``pattern`` values across 830 sites, and
    10 of those nodes carry a ``title``" -- and a figure in an issue that no longer
    recomputes is a figure upstream is right to discount.  So the census lives beside the
    patch (:func:`codegen.patch.census`) rather than in a script that has been deleted, and
    it descends ``bundle.subschemas``: the same descent ``record`` inlines along and
    ``rewritten`` rewrites along, so the sites counted here are the sites the patch can
    reach.

    CEILINGS, not equalities, and the direction is the same for all three: every figure
    FALLS as upstream names a shape, and a RISE is the bundle growing another unnamed
    repetition -- which is the defect #8525 reports and is worth reddening for.
    """
    census = patch.census(PUBLISHED)
    found = claimed("the pattern sites", [s for one in census.values() for s in one])
    ratchet(
        "distinct pattern values",
        len(census),
        at_most=110,
        because="falls as upstream extracts a shape; a rise is a new unnamed repetition",
    )
    ratchet(
        "pattern sites",
        len(found),
        at_most=830,
        because="falls as upstream extracts a shape; a rise is a new unnamed repetition",
    )
    titled = [
        (document, pointer)
        for one in census.values()
        for document, pointer in one
        if "title" in bundle.node_at(bundle.read(PUBLISHED, document), pointer)
    ]
    ratchet(
        "pattern sites carrying a title",
        len(titled),
        at_least=10,
        because="RISES as upstream names a shape in place, which is the repair #8525 asks "
        "for; it is the one figure here that should grow",
    )


def test_the_patch_set_loads_and_no_exclusion_is_stale() -> None:
    """Every manifest entry names a document of the patch set, and every exclusion a site.

    A stale exclusion is how this manifest rots silently: the day the site it names loses
    the shape, the entry stops excluding anything, and the next site to GAIN that shape at
    that pointer is rewritten without anyone having looked at what it means.
    """
    extractions = patch.load(PATCH_SET, PUBLISHED)
    assert [held.document for held in extractions] == [
        "core/currency-code.json",
        "core/country-code.json",
        "core/domain-name.json",
        "core/https-url.json",
        "core/idempotency-key.json",
    ]
    assert patch.stale(PUBLISHED, extractions) == []


def test_the_patch_adds_documents_and_replaces_none(patched: Path) -> None:
    """The patch is ADDITIVE over the document set, which is what makes it a patch.

    A patch that replaced a published document would be a different operation: the record
    check compares the two bundles document by document, so a document the patch had
    rewritten in place would be graded against its own replacement.
    """
    assert patch.added(PUBLISHED, patched) == [
        "core/country-code.json",
        "core/currency-code.json",
        "core/domain-name.json",
        "core/https-url.json",
        "core/idempotency-key.json",
    ]
    assert patch.removed(PUBLISHED, patched) == []


def test_every_site_the_patch_rewrites_is_a_reference_and_nothing_else_moves(
    patched: Path,
) -> None:
    """The patched bundle differs from the published one at exactly the matched sites.

    Stated over the RAW documents rather than the records, so the two halves of the claim
    are separable: this one says the rewrite touched what it meant to touch, and the record
    check says what it touched resolves back.
    """
    extractions = patch.load(PATCH_SET, PUBLISHED)
    found = claimed("sites the patch rewrites", patch.sites(PUBLISHED, extractions))
    for held in extractions:
        mine = claimed(f"sites of {held.document}", [s for s in found if s[2] == held.uri])
        ratchet(
            f"sites of {held.document}",
            len(mine),
            at_least=20,
            because="a document extracted for fewer than a score of sites is not a "
            "repetition worth naming; the figure FALLS as upstream takes the patch and "
            "the sites stop being inline, and the patch set retires with it",
        )
    moved = {document for document, _, _ in found}
    for document in claimed("the portable documents", bundle.portable(PUBLISHED)):
        same = bundle.read(PUBLISHED, document) == bundle.read(patched, document)
        assert same is (document not in moved), document


def test_no_record_difference_is_seen_by_a_validator(
    differences: list[patch.Difference],
) -> None:
    """THE CHECK: the patch moves no keyword that decides what an instance is.

    Mechanical, and the predicate is ``bundle.is_an_annotation`` -- the one ``record``
    itself reads to decide a ``$ref``'s sibling -- so nothing here is a judgement about
    which keyword matters and there is no second list to drift from.

    This is what makes the patch a refactor rather than a fork of the protocol.  A patch
    that added the ``minItems: 1`` five documents omit would land here, named, with the
    document and the pointer.
    """
    seen = patch.seen_by_a_validator(differences)
    assert seen == [], "\n".join(str(d) for d in seen[:20])


def test_every_record_difference_is_a_name_the_patch_adds(
    differences: list[patch.Difference],
) -> None:
    """The residue of §1's byte-compare, stated exactly.

    §1 asks for byte-identity and the patch does not have it: ``record`` inlines a
    reference's target WHOLE, so a site referencing ``core/currency-code.json`` also takes
    that document's ``$schema`` and ``title`` -- and its ``description`` where the site
    stated none, since a sibling only wins where it exists.

    **That is the whole of the difference**, and the assertion is written so that it stays
    the whole of it: every difference is a GAIN, of keys drawn from
    :data:`NAMES_THE_PATCH_ADDS`, and nothing is lost or changed at any pointer of any
    document.  A patch document growing another key, or a rewrite touching a site it
    should not have, breaks this test rather than disappearing into a tolerance.

    The count is the number of POINTERS, not of sites: a record is expanded per path
    through the reference graph, so one patched site inside a document twenty other
    documents reference is reported from each of them.
    """
    gains = Counter()
    for difference in differences:
        assert "loses []" in difference.detail, str(difference)
        assert set(difference.keys) <= set(NAMES_THE_PATCH_ADDS), str(difference)
        gains[difference.keys] += 1
    assert set(gains) == {("$schema", "title"), ("$schema", "description", "title")}
