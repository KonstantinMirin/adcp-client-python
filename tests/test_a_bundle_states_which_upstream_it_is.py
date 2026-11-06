"""**A BUNDLE WITH NO RECORD OF ITS UPSTREAM STATE IS RED, AND SO IS A RECORD THAT DOES NOT
MATCH ITS BUNDLE.**

``docs/plan/architecture.md``, under "AN OVERRIDE DECLARES THE DEFECT IT COMPENSATES FOR,
AND FAILS WHEN THE DEFECT IS GONE", decides the rule and this file is its instrument:

    **AND EVERY ONE OF THOSE REFUSALS IS A COMPARISON AGAINST THE PUBLISHED BUNDLE, WHICH
    MAKES THE PUBLISHED BUNDLE PART OF THE OVERRIDE.** [...] **A BUNDLE GROUNDS US ONLY
    WHILE ITS UPSTREAM STATE IS RECORDED BESIDE IT** -- the upstream commit, the command
    that built it, and a digest over the document set.  The digest is not redundant with the
    commit: a commit identifier nothing checks is a decoration, and the comparison between
    digest and documents is what turns the record from a claim into a fact.

**WHAT WAS MEASURED BEFORE THIS FILE EXISTED** (``adcp-client-python-82m.48``).  Neither
bundle named an upstream commit, a tag, or a build command; ``schemas/`` held no non-``.json``
file at all; and the fork publishes no ``3.2.x`` or ``3.3.x`` tag, so the version string
pinned nothing either.  ``codegen.patch.load`` raises where the published bundle *already*
states what an ``Addition`` adds -- that refusal is how the 90 approximated facts in 57
documents retire themselves when upstream fixes the schema -- and it fires against whatever
bytes happen to be in ``schemas/cache/``.  With no record, "the fix landed" and "the copy is
old" are the same reading, and they carry opposite instructions.

**AND THE READING IS NOT HYPOTHETICAL.**  ``patches/8735`` carries 13 additions.  Counted
against three upstream states: 0 of 13 are already stated by ``schemas/cache/3.2``; 1 of 13
by ``schemas/cache/3.3`` (``brand.json#/definitions/data_subject_contestation``); 11 of 13
by a build at ``1b84881e3``, which is a SIBLING of the 3.3 bundle's commit rather than a
descendant, so it lands the other eleven and not that one.  One patch set, three answers to
"is the defect gone", chosen entirely by which upstream the bundle is.

**WHY THE DIGEST AND NOT THE COMMIT ALONE, which is the half that is easy to drop.**  A
record naming a sha and nothing checkable is worse than no record: it reads as a fact and is
a claim.  :func:`test_the_digest_states_the_bundle_it_stands_beside` is therefore the only
test here that can fail on a day nobody edits a record -- the others grade the record's own
well-formedness, and this one grades the bundle.

**THIS GATE IS SHOWN TO BITE RATHER THAN ASSUMED TO.**  A gate over a directory that is
normally unchanged is exactly the kind that passes because nothing happened, and that shape
has been shipped in this project more than once.  ``perturb_the_bundle_pin.sh`` writes one
byte into one document of each bundle, asserts this file goes RED, reverts, and asserts it
goes green again -- the same form as ``perturb_the_wheel.sh`` and ``perturb_seam.sh``.

**IT IS NOT ``codegen/held.py``'s MECHANISM AND MUST NOT BECOME IT.**  That module's standing
claim is *a compiler edit moves no key*: the accepts corpus is keyed on what a document
ADMITS, so an acceptance-preserving rewrite of the bundle costs nothing.  The claim HERE is
the neighbouring one -- *a BUNDLE edit does not pass unnoticed* -- and it is keyed on bytes
for the reason ``tests/provenance.py`` states: an acceptance-preserving rewrite is exactly
the event that invalidates a measurement taken over these bytes, so the two keys must
disagree about it and do.
"""

from __future__ import annotations

import re

import provenance
import pytest

#: Parametrised over the bundles DISCOVERED beside the records, so a third bundle copied in
#: with no record is a red in :func:`test_a_bundle_has_a_record_beside_it` rather than a
#: directory no test mentions.
BUNDLES = provenance.bundles()
NAMES = [b.name for b in BUNDLES]


def test_the_cache_holds_at_least_the_two_bundles_the_goal_compares() -> None:
    """The parametrisation has a non-empty subject, asserted and not assumed.

    Every other test here is parametrised over :data:`BUNDLES`, and an empty parametrisation
    collects zero tests and reports success -- the failure mode that makes a gate over a
    discovered population worthless.  The goal's own acceptance test is "verify that the
    same is true for 3.3 schemas as it is for 3.2", so both names are required here by name.
    """
    assert {"3.2", "3.3"} <= set(NAMES), NAMES


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_a_bundle_has_a_record_beside_it(bundle) -> None:
    """Every directory under ``schemas/cache/`` has a provenance record, naming itself."""
    path = provenance.record_path(bundle)
    assert path.exists(), (
        f"{bundle.relative_to(provenance.REPO)} has no provenance record. "
        f"Write {path.relative_to(provenance.REPO)}: a bundle grounds us only while its "
        f"upstream state is recorded beside it."
    )
    record = provenance.read(bundle)
    assert record["bundle"] == bundle.relative_to(provenance.REPO).as_posix()


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_the_digest_states_the_bundle_it_stands_beside(bundle) -> None:
    """**THE COMPARISON.  The recorded digest equals the digest over the documents.**

    This is the test that turns the record into a fact, and the only one here that a change
    to the BUNDLE can fail.  Its message names the three readings a red has, because they
    carry different instructions: the bundle was re-copied (re-measure, then rewrite the
    record), a document was edited in place (an edit to a published bundle is not a thing
    this repository does -- use ``patches/``), or the record was written against a different
    directory.
    """
    recorded = provenance.read(bundle)["digest"]
    assert provenance.digest(bundle) == recorded, (
        f"{bundle.relative_to(provenance.REPO)} does not match the digest its record "
        f"states.  Either the bundle moved -- in which case re-measure what the record "
        f"claims and rewrite it, do not just paste the new digest -- or a document was "
        f"edited in place, which an override must never do: an override is an overlay, and "
        f"`patches/` is where one goes."
    )


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_the_record_counts_the_documents_it_digests(bundle) -> None:
    """The count in the record is the count the digest ranges over.

    Beside the digest rather than instead of it: the digest says *which* bytes and the count
    says *how many*, and the count is the figure every cost reading in this repository is
    divided by -- "1,054 portable of 1,625 documents".  A record whose count is wrong makes
    every such figure describe a population that is not there.
    """
    record = provenance.read(bundle)
    assert len(provenance.files(bundle)) == record["documents"]


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_the_bundle_holds_nothing_but_json_documents(bundle) -> None:
    """Every file the digest ranges over is a ``.json`` document.

    :func:`provenance.files` digests every regular file rather than every ``*.json``,
    because a stray file under a bundle root is either a document ``codegen.bundle``'s walk
    will compile or a note nobody reads, and the record cannot tell which.  This states the
    property that makes the two sets equal, so the arrival of a non-document is a named red
    here rather than a silent widening of the digest's subject.
    """
    strays = [name for name in provenance.files(bundle) if not name.endswith(".json")]
    assert strays == [], strays


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_the_record_names_a_commit_and_the_commands_that_made_the_bundle(bundle) -> None:
    """A 40-hex upstream commit, a build command, and a vendor command -- each non-empty.

    The architecture names three things a record carries and the digest is only one of them.
    A sha of the wrong SHAPE is the cheapest way for a record to be wrong while looking
    right, so it is matched rather than merely required to be present; abbreviations are
    refused because a 9-character prefix is ambiguous in a repository nobody here controls.
    """
    record = provenance.read(bundle)
    upstream = record["upstream"]
    assert re.fullmatch(r"[0-9a-f]{40}", upstream["commit"]), upstream["commit"]
    assert upstream["repository"].startswith("https://")
    assert upstream["artifact"]
    assert record["build_command"].strip()
    assert record["vendor_command"].strip()


@pytest.mark.parametrize("bundle", BUNDLES, ids=NAMES)
def test_a_document_excepted_from_the_reproduction_claim_is_in_the_bundle(bundle) -> None:
    """Every document the record excepts from byte reproduction is a document it holds.

    The records do not claim full byte reproduction: a ``--release`` build stamps wall-clock
    time into 4 of the 1,141 documents of 3.3 and into 1 of the 1,625 of 3.2, so those are
    named with the field that moves.  **An exception that names no document is the rot
    ``codegen/patch.py`` already refuses in its exclusions** -- it reads as a known
    limitation and is a stale note, and the next document to arrive at that path inherits a
    waiver nobody read.  The count is asserted against the list for the same reason.
    """
    record = provenance.read(bundle)
    reproduction = record["reproduction"]
    held = set(provenance.files(bundle))
    for exception in reproduction["exceptions"]:
        assert exception["document"] in held, exception["document"]
        assert exception["reason"].strip()
    assert reproduction["of"] == record["documents"]
    assert reproduction["documents_byte_identical"] + len(reproduction["exceptions"]) == reproduction["of"]
