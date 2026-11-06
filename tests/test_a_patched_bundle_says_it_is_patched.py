"""**A DIRECTORY THAT HAS BEEN PATCHED SAYS SO, AND A SECOND APPLICATION IS A NO-OP THAT
SAYS SO TOO.**

``docs/plan/architecture.md``, under "AND A BUNDLE DIRECTORY MUST SAY WHETHER IT IS PATCHED,
BECAUSE A CALLER CANNOT TELL", decides the rule and this file is its instrument:

    **SO THE PATCHED DIRECTORY CARRIES ITS OWN RECORD OF WHAT WAS APPLIED, AND APPLYING THE
    SAME SET AGAIN IS A NO-OP THAT SAYS SO.**  Then a double application is answerable from
    the value instead of from the caller's memory, the expiry refusal means only what it
    says, and the reading that makes a bundle groundable -- the record beside it naming its
    upstream state -- is the same record doing both jobs.

**WHAT WAS MEASURED BEFORE THIS FILE EXISTED.**  A published bundle and the directory
``patch.for_build`` materialises are both *a directory of documents*, and nothing in either
distinguished them.  ``codegen/__main__.py`` applies the BUILD's table to whatever
``--bundle`` names, so handing it an already-patched directory applied the table twice and
raised on the first entry whose defect the first pass had fixed::

    ValueError: core/currency-code.json: the published bundle already holds it

**That sentence is the EXPIRY rule's.**  It means an override's defect is gone upstream and
the entry should be DELETED -- the mechanism by which the approximated facts retire
themselves when upstream fixes the schema -- and it was indistinguishable from a double
application, whose instruction is the opposite: delete nothing, pass the published bundle.
A refusal that can mean either of two things means neither.  Three readers decided it wrong
in one day: ``./check <document>`` (``adcp-client-python-ywff``), the determinism clause of
``tests/test_emit.py`` (``adcp-client-python-qzx.17``), and a re-emit by hand.

**SO THE TWO REFUSALS ARE GRADED TOGETHER**
(:func:`test_a_double_application_and_an_expiry_are_two_refusals_with_two_messages`), because
what was wrong was never that either one fired -- it is that one sentence served both, and a
test that only showed the new one firing would leave exactly the ambiguity in place.  The
expiry refusal is required to still fire, against ``schemas/cache/3.3``'s
``brand.json#/definitions/data_subject_contestation``, which upstream's own ``9c32fa997``
titled.

**AND THE RECORD IS NOT A 1,626TH DOCUMENT**, which is why it stands BESIDE the directory:
``codegen.bundle.portable`` enumerates ``rglob("*.json")`` under the bundle root, so a record
written inside would be compiled, graded and counted among the documents.  The published
bundles' records already sit beside them for that reason and this one takes the same
spelling, from the same function.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import fresh
import pytest

from codegen import bundle, patch, store
from tests.nodeset import claimed

REPO = Path(__file__).resolve().parents[1]

#: **The bundle a RUN reads**, which is the subject here: it is the directory
#: ``patch.for_build`` materialises, and the whole claim is that it can be ASKED what it is.
BUNDLE = fresh.BUNDLE

#: One document with a committed corpus entry, so the entry-point clause below costs an emit
#: and no draw.  The same one ``tests/test_the_run_writes_its_verdicts.py`` names, and for
#: its reason: what is graded is that the COMMAND gets through, not which document it reaches.
DOCUMENT = "core/pagination-request.json"

#: The markers of the expiry refusal and of the double-application refusal, as SENTENCES the
#: reader acts on rather than as exception types -- both are ``ValueError``, which is exactly
#: why the message is the thing that had to become unambiguous.
EXPIRY_SAYS = ("already states", "defect is gone", "delete it")
DOUBLE_SAYS = ("DOUBLE APPLICATION", "already applied", "NOT an expiry")


def test_the_patched_bundle_carries_a_record_of_what_was_applied() -> None:
    """The value answers "which sets do you hold?", and answers it grounded.

    One record, both jobs: the sets applied AND the upstream state the published bundle
    states.  The upstream half is compared against the published bundle's OWN record rather
    than against a literal, so the forwarding is graded and no commit sha is written here --
    a sha in a test is the decoration the provenance rule already refuses.
    """
    assert patch.sets_applied(BUNDLE) == patch.BUILD, (
        "the bundle a run reads does not say which sets it holds, so every caller is back "
        f"to remembering: {patch.record_beside(BUNDLE)}"
    )
    record = patch.record_beside(BUNDLE)
    assert record is not None and record["patched"] is True, record

    upstream = patch.record_beside(fresh.PUBLISHED)
    assert upstream is not None, "the published bundle's own record is the grounding"
    fields = claimed("what the patched record carries forward", {"published", "digest", "upstream"})
    assert record["published"] == upstream["bundle"], (fields, record["published"])
    assert record["published_digest"] == upstream["digest"], record["published_digest"]
    assert record["upstream"] == upstream["upstream"], record["upstream"]
    assert record["grounded"] is True, record


def test_the_record_stands_beside_the_bundle_and_is_not_a_document_of_it() -> None:
    """The record is not compiled, graded or counted -- it is outside the walk.

    Graded over the walk the compiler itself does (``bundle.portable``) and over the glob
    that walk is built on, because the cost of getting this wrong is not an error: it is a
    1,626th "document" that emits a module and lands in the figures.
    """
    documents = claimed("the patched bundle's portable documents", bundle.portable(BUNDLE))
    record = patch.record_path(BUNDLE)
    assert record.is_file(), record
    assert record.parent == BUNDLE.parent and record.name.startswith(BUNDLE.name), record
    assert str(record.resolve()) not in {str((BUNDLE / d).resolve()) for d in documents}
    inside = [p for p in BUNDLE.rglob("*.json") if p.name.endswith(patch.RECORD_SUFFIX)]
    assert not inside, (
        "a provenance record is inside the bundle, so bundle.portable reads it as a schema "
        f"and the compiler grades it: {inside}"
    )


def test_applying_the_same_sets_to_the_patched_bundle_is_a_no_op() -> None:
    """``for_build`` handed its own output returns it, rather than applying the table twice.

    The identity the three defects needed and none of them had.  Asserted on the DIRECTORY
    and on the record after it, so a no-op that quietly rebuilt something would be red here
    too: the answer has to be the same bundle, not an equal one.
    """
    again = patch.for_build(BUNDLE)
    assert again == BUNDLE, (again, BUNDLE)
    assert patch.sets_applied(again) == patch.BUILD
    assert patch.for_build(again) == BUNDLE


def test_a_double_application_and_an_expiry_are_two_refusals_with_two_messages() -> None:
    """**The whole point: the two readings are now distinguishable from the message.**

    Both are ``ValueError`` and both arise from applying a table, so the type cannot tell
    them apart and never could.  What is graded is that each message carries the markers of
    its own reading and NONE of the other's -- because the instructions are opposite.  An
    expiry says *the defect is gone, delete the entry*; a double application says *delete
    nothing, you applied the table twice*.

    And the expiry refusal is required to still FIRE, which is the half a test of the new
    refusal alone would quietly drop: ``patches/8735``'s entry for
    ``brand.json#/definitions/data_subject_contestation`` is already titled in
    ``schemas/cache/3.3`` by upstream's own commit, so that is where the mechanism is read.
    """
    with pytest.raises(ValueError) as double:
        patch.apply(BUNDLE, Path(patch.BUILD[0]), Path("/tmp/never-written-by-this-clause"))
    with pytest.raises(ValueError) as expiry:
        patch.additions(Path(patch.BUILD[1]), fresh.SECOND)

    said = {"a double application": str(double.value), "an expiry": str(expiry.value)}
    claimed("the two refusals a patched directory used to collapse into one", set(said))
    assert all(marker in said["a double application"] for marker in DOUBLE_SAYS), said
    assert all(marker in said["an expiry"] for marker in EXPIRY_SAYS), said
    assert not any(marker in said["an expiry"] for marker in DOUBLE_SAYS), said
    assert not any(marker in said["a double application"] for marker in EXPIRY_SAYS), said
    # And the sentence that served both is gone from the one it did not belong to.
    assert "already holds it" not in said["a double application"], said


def test_for_build_refuses_a_patched_directory_asked_for_a_different_set() -> None:
    """A set that is not the one the directory holds is a double application, not a build.

    ``sets`` composes inside one derivation, so a caller that wants two sets names two; a
    second derivation stacked onto a materialisation has no reading under which it is what
    anybody meant, and the one it used to produce was the expiry sentence.
    """
    with pytest.raises(ValueError) as refused:
        patch.for_build(BUNDLE, (patch.BUILD[0],))
    assert "already a patched bundle" in str(refused.value), str(refused.value)
    assert "DOUBLE APPLICATION" in str(refused.value), str(refused.value)
    assert "already holds it" not in str(refused.value), str(refused.value)


def test_a_published_bundle_states_that_nothing_has_been_applied_to_it() -> None:
    """Every committed bundle reads "not patched", and reads it off a record that EXISTS.

    The absence of the key is the statement, which is what let the two shipped records stay
    as they are -- so the clause that matters is this one: a bundle with a record and no
    ``applied`` key is not patched, and is therefore still patchable.  Were it the other way
    round, the no-op above would swallow the real build.
    """
    published = claimed("the committed bundles", {fresh.PUBLISHED, fresh.SECOND})
    for directory in sorted(published):
        record = patch.record_beside(directory)
        assert record is not None, f"{directory} has no provenance record at all"
        assert "applied" not in record, record
        assert patch.sets_applied(directory) is None, directory


def _a_bundle_of_one_document(at: Path) -> Path:
    """A two-file bundle with a node that states no ``title``, so a patch set can add one."""
    at.mkdir(parents=True)
    (at / "thing.json").write_text(
        json.dumps({"type": "object", "properties": {"a": {"type": "string"}}}, indent=2)
    )
    (at / "other.json").write_text(json.dumps({"type": "object"}, indent=2))
    return at


def _a_patch_set_adding_a_title(at: Path, title: str) -> Path:
    """One addition, with the defect and the ask ``patch._judged`` requires of every entry."""
    at.mkdir(parents=True)
    (at / patch.MANIFEST).write_text(
        json.dumps(
            {
                "additions": [
                    {
                        "document": "thing.json",
                        "pointer": "",
                        "keyword": "title",
                        "value": title,
                        "defect": "the document's root states no title, so its class is named "
                        "after the position it was reached at",
                        "ask": "a fixture, which is why this names no upstream issue",
                    }
                ]
            },
            indent=2,
        )
    )
    return at


def test_an_edit_to_the_patch_table_moves_the_patched_bundles_name_and_its_compile_key(
    tmp_path: Path,
) -> None:
    """**The compile-key property the record must not cost us, graded as behaviour.**

    ``patch.for_build``'s directory name is a digest and the patch table's digest is IN it,
    so an edit to a patch set moves the directory -- and the compile store beneath keys on
    that directory's path, which is how an edit to the override table invalidates the
    compiles made before it.  The ``sdk/store`` lane established that collapsing the patched
    name onto the published identity would drop the decision table out of the compile key,
    and ``tests/test_the_compile_store.py``'s third clause forbids it from the other side.

    Read over a bundle of two documents and a patch set of one addition, so the property is
    graded on an edit to the TABLE'S BYTES rather than on a change of which sets are named:
    the manifest's defect sentence is what moves, the documents it produces are identical,
    and the name still moves.  A reading over the real 1,625-document bundle would pay two
    cold builds to say the same thing about the same digest.
    """
    published = _a_bundle_of_one_document(tmp_path / "published")
    patch_set = _a_patch_set_adding_a_title(tmp_path / "set", "A Thing")
    sets = (str(patch_set),)

    before = patch.for_build(published, sets)
    assert patch.sets_applied(before) == sets
    assert bundle.read(before, "thing.json")["title"] == "A Thing"

    manifest = json.loads((patch_set / patch.MANIFEST).read_text())
    manifest["additions"][0]["defect"] += " (said again, in one more clause)"
    (patch_set / patch.MANIFEST).write_text(json.dumps(manifest, indent=2))
    after = patch.for_build(published, sets)

    claimed("the patched directories the two tables materialise", {before, after})
    assert before != after, (
        "an edit to the patch table moved no directory, so a compile made against the old "
        f"table answers a caller reading the new one: {before}"
    )
    documents = claimed("the fixture bundle's documents", bundle.portable(after))
    keys = {
        "before the edit": store.key(before, documents),
        "after the edit": store.key(after, documents),
        "the published bundle": store.key(published, documents),
    }
    collided = sorted(
        (one, other)
        for one in keys
        for other in keys
        if one < other and keys[one] == keys[other]
    )
    assert not collided, (
        "two of these are held under ONE compile key, so the decision table is not in the "
        f"key and an edit to it would move nothing: {collided} out of {keys}"
    )


def test_the_command_a_lane_types_gets_through_an_already_patched_bundle(tmp_path: Path) -> None:
    """``adcp-client-python-ywff`` closing, graded through the entry point it broke.

    ``./check <document>`` shells ``python -m codegen --bundle <BUNDLE> --tree ...``, where
    ``BUNDLE`` is ``patch.for_build``'s output -- so the documented loop, the second line of
    that command's own docstring, raised the expiry sentence and had not run since
    ``for_build`` was wired in.  This is that command: the patched directory as ``--bundle``,
    one document, and the child's EXIT STATUS read.

    **The status is the assertion and not the output**, which is ``adcp-client-python-qzx.17``'s
    second half: the clause that found this defect shelled the same command and never read the
    return code, so a run that refused everything and a run that emitted nothing were the same
    observation to it.

    ``./check`` itself is not shelled here, and the reason is a path rather than a principle:
    it writes its tree to ``/tmp/check-tree`` and its verdict table to a fixed name, so a
    clause that ran it would race every lane using the fast loop while the suite is running.
    """
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "codegen",
            "--bundle",
            str(BUNDLE),
            "--tree",
            str(tmp_path / "_schemas"),
            DOCUMENT,
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": f"{REPO}:{REPO / 'src'}", "PATH": "/usr/bin:/bin"},
    )
    assert done.returncode == 0, (
        "the command a lane types does not get through an already-patched bundle:\n"
        f"{done.stdout[-2000:]}\n{done.stderr[-4000:]}"
    )
    assert "Traceback" not in done.stderr, done.stderr[-4000:]
    # And the no-op SAYS SO, off the record rather than off the caller's intent.
    said = [line for line in done.stdout.splitlines() if line.startswith("already patched:")]
    assert len(said) == 1, (
        "the run read an already-patched bundle and said nothing about it, so two runs over "
        f"the same input differ by a line a reader cannot account for: {done.stdout[:2000]}"
    )
    assert all(name in said[0] for name in patch.BUILD), said
    assert re.search(r"emitted 1 / refused 0", done.stdout), done.stdout[-2000:]
