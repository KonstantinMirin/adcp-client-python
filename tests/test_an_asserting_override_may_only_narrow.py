"""**AN OVERRIDE MAY ASSERT, AND WHAT MAKES IT ADMISSIBLE IS THE DIRECTION.**

``docs/plan/rebuild-plan.md`` §8's subsection of that name, graded as behaviour over
fixture bundles and one emitted class.  The rule it implements, in the plan's own order:

* an annotation override is admissible because ``seen_by_a_validator`` is empty for it BY
  CONSTRUCTION, and that path keeps its cheaper proof unchanged;
* an asserting override may only NARROW, and **the proof is a VALUE** -- admitted by the
  published node, refused by the patched node, refused by the class, with both reasons
  named;
* **a widening assertion is refused outright** and ``load`` names the value that proves it
  widens;
* the expiry clause is unchanged: the published node already stating the keyword means
  DELETE the entry, never overwrite.

**WHY THE WIDENING CASES GO THROUGH A ``not`` AND A ``oneOf`` AND NOT THROUGH A BARE
NODE.**  Adding a keyword to a schema OBJECT cannot widen that object -- draft-07 holds
every keyword of a node against the same instance, so one more conjunct refuses a subset of
what the node refused before.  A direction test asked at the node would therefore admit
every entry ever written, which is a test that cannot fail.  What CAN widen is the
DOCUMENT, at the three positions draft-07 reads negatively, and two of them are measured
here: a ``not``, where refusing more at the node admits more at the document, and a
``oneOf``, which asserts that EXACTLY one branch matches -- so narrowing one branch can
take an instance from two matches to one and the document comes to admit it.

**AND THE THIRD HALF OF THE PROOF IS GRADED AGAINST A CLASS AND NOT ASSERTED.**  §8 asks
for a value "refused by the class, with both reasons named", and ``codegen.patch`` cannot
decide that half: it is the SOURCE layer and has no class to ask.  So this file emits the
fixture document, imports the class, and asks it -- which is the only reading of that half
that is a measurement rather than a sentence.
"""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from codegen import bundle, emit, harness, patch

#: What ``patch._judged`` requires of every entry, said once.  A fixture names no upstream
#: issue and says so in the ``ask`` rather than leaving the key blank, which ``_judged``
#: refuses -- the refusal is the mechanism's and this file is not the place to re-grade it.
JUDGED = {
    "defect": "a fixture's own defect, stated so the entry is a judgment and not a preference",
    "ask": "a fixture in tests/, which is why this names no upstream issue",
}

#: **THE NARROWING FIXTURE, and its defect is the one ``adcp-client-python-82m.65`` names.**
#: ``{"type": "string", "format": "uri", "pattern": "^https://"}`` ADMITS the eight
#: characters ``https://`` -- the pattern matches it, and RFC 3986 has nothing to say about
#: an empty authority -- and ``constraints.AdCPUrl`` refuses it with ``url_parsing``, "empty
#: host".  ``harness.matching_a_pattern``'s own docstring measures that pair at
#: ``core/https-url.json#``, so the fixture is the bundle's shape and not an invention.
#:
#: The keyword the entry adds is a ``minLength`` and not a tighter ``pattern``, because the
#: node already STATES a pattern and the expiry clause answers first -- which is itself a
#: property, graded below.
A_NARROWING_DOCUMENT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Endpoint",
    "type": "object",
    "required": ["url"],
    "properties": {"url": {"type": "string", "format": "uri", "pattern": "^https://"}},
}

#: **THE WIDENING FIXTURE, first shape: the node sits under a ``not``.**  The published
#: document refuses every string of two characters or more at ``/code``; adding a
#: ``maxLength`` inside the ``not`` makes the document ADMIT the longer ones, which is the
#: back door §8 exists to close.
A_NEGATED_DOCUMENT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Coded",
    "type": "object",
    "required": ["code"],
    "properties": {"code": {"not": {"type": "string", "minLength": 2}}},
}

#: **THE WIDENING FIXTURE, second shape: the node is a ``oneOf`` branch.**  A one-character
#: string matches BOTH branches, so the published document refuses it on the count; adding a
#: ``minLength`` to branch 0 leaves it matching only branch 1, and the document comes to
#: admit it.  Nothing about the keyword is loosened and the document still widens, which is
#: why the test is at the document and not at the node.
#:
#: ``definitions`` is held here too, as the pointer no instance of this document reaches.
A_BRANCHED_DOCUMENT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Branched",
    "oneOf": [
        {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}}},
        {
            "type": "object",
            "required": ["a"],
            "properties": {"a": {"type": "string", "maxLength": 4}},
        },
    ],
    "definitions": {"held": {"type": "string"}},
}

#: The value the narrowing entry carries as its proof, and the one the class refuses.
AN_EMPTY_AUTHORITY = "https://"


def _a_bundle() -> Path:
    """The three fixture documents as a bundle directory.

    A directory and not a dict, because every refusal under test is reached through
    ``patch.additions``, which reads a PUBLISHED BUNDLE -- and a fixture that handed the
    mechanism a parsed object would be grading a second door.
    """
    at = Path(tempfile.mkdtemp()) / "bundle"
    at.mkdir(parents=True)
    for name, document in (
        ("endpoint.json", A_NARROWING_DOCUMENT),
        ("coded.json", A_NEGATED_DOCUMENT),
        ("branched.json", A_BRANCHED_DOCUMENT),
    ):
        (at / name).write_text(json.dumps(document, indent=2) + "\n")
    return at


def _a_set(entry: dict) -> Path:
    """A patch set carrying exactly one addition."""
    at = Path(tempfile.mkdtemp()) / "set"
    at.mkdir(parents=True)
    (at / patch.MANIFEST).write_text(json.dumps({"additions": [entry]}, indent=2))
    return at


#: The narrowing entry, as a manifest states it.
A_NARROWING_ENTRY: dict[str, Any] = {
    "document": "endpoint.json",
    "pointer": "/properties/url",
    "keyword": "minLength",
    "value": 9,
    "narrows": AN_EMPTY_AUTHORITY,
    **JUDGED,
}


def test_an_asserting_entry_that_narrows_is_admitted_and_carries_its_proving_value() -> None:
    """**The whole of the new kind: a non-annotation keyword lands, because it narrows.**

    ``minLength`` decides acceptance at a PROP position -- ``bundle.is_an_annotation`` says
    so, and the sentence this replaced refused the entry for exactly that -- so an entry
    admitted here is admitted on its DIRECTION and on nothing else.
    """
    published = _a_bundle()
    grown = patch.additions(_a_set(A_NARROWING_ENTRY), published)
    assert len(grown) == 1, grown
    (one,) = grown
    assert one.asserts is True, one
    assert one.narrows == AN_EMPTY_AUTHORITY, one
    node = bundle.node_at(bundle.read(published, one.document), one.pointer)
    assert not bundle.is_an_annotation(
        one.keyword, patch._position_of(bundle.read(published, one.document), one.pointer)
    ), f"{one.keyword} is an annotation here, so this entry is not asserting anything"
    assert one.keyword not in node, node


def test_the_proof_is_a_value_the_document_admits_the_patch_refuses_and_the_class_refuses() -> None:
    """**§8's proof, all three halves, each by value and each with its reason named.**

    The first two halves are the DOCUMENTS': ``harness.conforms`` is the run's own reading
    of "the document admits it", asked of the published document and of the patched one, and
    ``harness.violated_keywords`` names which keyword the patched document refuses on rather
    than assuming it is the one the entry added.

    The third half is the CLASS's, and it is the half ``codegen.patch`` cannot reach.  The
    fixture document is emitted, the module is imported, and the class is handed the same
    value -- so the reason beside the document's is pydantic's own error type and not a
    string this file writes.
    """
    published = _a_bundle()
    root = bundle.read(published, "endpoint.json")
    patched = patch.added_at(root, "/properties/url", "minLength", 9)
    carried = {"url": AN_EMPTY_AUTHORITY}

    assert harness.conforms(root, carried) is True, (
        "the published document must ADMIT the proving value, or the entry is not closing a "
        "gap"
    )
    assert harness.conforms(patched, carried) is False, (
        "the patched document must REFUSE it, or the entry asserts nothing"
    )
    assert "minLength" in harness.violated_keywords(patched, carried), (
        "the patched document must refuse it ON THE ADDED KEYWORD, not on a sibling"
    )

    cls, reason = _the_class_refusing(published, "endpoint.json", carried)
    assert reason is not None, (
        f"{cls} ADMITS {carried!r}: the set the override removes must be one the emitted "
        "class already refuses, and here it is not"
    )
    assert "url_parsing" in reason, reason


def _the_class_refusing(
    published: Path, document: str, payload: dict
) -> tuple[Any, str | None]:
    """The class the fixture document emits, and why it refuses ``payload`` -- or ``None``.

    ``emit.emit`` and ``emit.write`` over the fixture bundle, then an IMPORT, which is
    ``tests/test_ref_branch_union.py``'s own reading: a class that renders and does not
    import is exactly the shape a rendered string is blind to, and the reason this half is
    asked of an object rather than of text.
    """
    out = emit.emit(published, [document])
    assert not out.refusals, out.refusals
    package = published.parent / "pkg"
    emit.write(out, package, None)
    sys.path.insert(0, str(published.parent))
    try:
        for name in [n for n in sys.modules if n == "pkg" or n.startswith("pkg.")]:
            del sys.modules[name]
        # The module's own LAST segment, because ``emitted`` states where the module lands
        # in the shipped package (``adcp.types._schemas.endpoint``) and the fixture writes
        # it under ``pkg`` instead.
        module = importlib.import_module(f"pkg.{out.emitted[document].rsplit('.', 1)[-1]}")
    finally:
        sys.path.remove(str(published.parent))
    cls = module.Endpoint
    # **THE CONSTRUCTOR AND NOT ``strict_validate``**, because the half being graded is the
    # CLASS's.  ``strict_validate`` applies the document first and would report the
    # document's verdict wherever the two agree -- which is the whole question here, and
    # asking it that way would make the answer unreadable.
    try:
        cls.model_validate(payload)
    except Exception as refused:  # noqa: BLE001 -- the REASON is what §8 asks to be named
        return cls, str(refused)
    return cls, None


def test_a_widening_under_a_not_is_refused_outright_and_the_refusal_names_the_value() -> None:
    """**The back door, closed, with the value in the message.**

    §8: *"a compiler that cannot represent a constraint could otherwise delete the
    constraint and report agreement"*.  The entry below is a perfectly good narrowing of its
    NODE and a widening of its DOCUMENT, which is the only shape this refusal has to catch.
    """
    published = _a_bundle()
    held = _a_set(
        {
            "document": "coded.json",
            "pointer": "/properties/code/not",
            "keyword": "maxLength",
            "value": 3,
            "narrows": "aaaa",
            **JUDGED,
        }
    )
    with pytest.raises(ValueError, match="WIDENS") as refused:
        patch.additions(held, published)
    said = str(refused.value)
    assert "WIDENS" in said, said
    # The VALUE and not merely the verdict: a refusal naming no value cannot be checked
    # against the document by the reader it is addressed to.
    assert '"aaaa"' in said or "'aaaa'" in said, said
    assert harness.conforms(bundle.read(published, "coded.json"), {"code": "aaaa"}) is False
    assert (
        harness.conforms(
            patch.added_at(
                bundle.read(published, "coded.json"), "/properties/code/not", "maxLength", 3
            ),
            {"code": "aaaa"},
        )
        is True
    )


def test_a_widening_through_a_one_of_count_is_refused_and_names_the_value() -> None:
    """**The second negative context, and the one no node-level reading can see at all.**

    Nothing is loosened anywhere: branch 0 gains a ``minLength`` and refuses strictly more.
    The DOCUMENT widens because ``oneOf`` counts matches, which is why the test validates
    whole instances against whole documents.
    """
    published = _a_bundle()
    held = _a_set(
        {
            "document": "branched.json",
            "pointer": "/oneOf/0/properties/a",
            "keyword": "minLength",
            "value": 5,
            "narrows": "a",
            **JUDGED,
        }
    )
    with pytest.raises(ValueError, match="WIDENS") as refused:
        patch.additions(held, published)
    said = str(refused.value)
    assert "WIDENS" in said, said
    root = bundle.read(published, "branched.json")
    assert harness.conforms(root, {"a": "a"}) is False, "two branches match, so oneOf refuses"
    assert (
        harness.conforms(
            patch.added_at(root, "/oneOf/0/properties/a", "minLength", 5), {"a": "a"}
        )
        is True
    ), "one branch matches, so the patched document admits what the published one refused"


def test_a_proving_value_the_two_documents_do_not_reproduce_is_refused() -> None:
    """**A stale proof is deleted and not carried**, which is §9's rule for a declaration.

    The entry below adds a real narrowing and attaches a value the narrowing does not
    remove.  Admitting it would make the ``narrows`` key decoration: the mechanism would be
    taking the author's word for the direction, which is the thing the value exists to stop.
    """
    published = _a_bundle()
    held = _a_set({**A_NARROWING_ENTRY, "narrows": "https://example.com/a"})
    with pytest.raises(ValueError, match="does not prove a narrowing"):
        patch.additions(held, published)


def test_an_assertion_with_no_proving_value_is_still_refused_by_the_old_sentence() -> None:
    """**The refusal that was there is still there for an entry that declares nothing.**

    An entry with no ``narrows`` key is an ANNOTATION entry, whose only admissibility line
    is ``seen_by_a_validator`` -- unreachable for a keyword a validator acts on.  So the old
    message still fires, and what changed is that it now says what to do instead.
    """
    published = _a_bundle()
    held = _a_set({k: v for k, v in A_NARROWING_ENTRY.items() if k != "narrows"})
    with pytest.raises(ValueError, match="decides acceptance") as refused:
        patch.additions(held, published)
    assert "narrows" in str(refused.value), str(refused.value)


def test_an_annotation_entry_claiming_a_direction_is_refused_the_other_way_round() -> None:
    """A ``title`` cannot narrow anything, so a value offered as its proof proves nothing.

    The predicate is ``bundle.is_an_annotation`` over EVERY position, not over this node's:
    a keyword that states nothing about acceptance anywhere has no direction to have, and an
    entry carrying a value for one has misread which kind it is writing.
    """
    published = _a_bundle()
    held = _a_set(
        {**A_NARROWING_ENTRY, "keyword": "title", "value": "An endpoint", "narrows": "x"}
    )
    with pytest.raises(ValueError, match="states nothing about acceptance"):
        patch.additions(held, published)


def test_a_pointer_no_instance_of_the_document_reaches_is_refused_as_unprovable() -> None:
    """**A ``definitions`` node is reached by a ``$ref`` and not by an instance.**

    The proof is a value, so an entry at a pointer no value can be placed at is an opinion
    with a pointer on it.  Refusing it is the conservative direction and the limit is
    stated at ``patch._carriers``: the instance that reaches such a node is the REFERRER's,
    and the direction test walks one document's own structure.
    """
    published = _a_bundle()
    held = _a_set(
        {
            "document": "branched.json",
            "pointer": "/definitions/held",
            "keyword": "maxLength",
            "value": 4,
            "narrows": "aaaaa",
            **JUDGED,
        }
    )
    with pytest.raises(ValueError, match="no instance of this document reaches"):
        patch.additions(held, published)


def test_the_expiry_refusal_fires_for_an_asserting_entry_exactly_as_for_an_annotation() -> None:
    """**The removability guarantee is not relaxed by asserting**, which §8 says in a clause.

    The published node already stating the keyword is an entry to DELETE, and the refusal
    must arrive BEFORE the direction test -- an entry whose defect is gone would otherwise
    be graded on a direction it no longer has, and a patch that overwrote a published value
    is the one failure of this mechanism that looks like success.
    """
    published = _a_bundle()
    held = _a_set({**A_NARROWING_ENTRY, "keyword": "pattern", "value": "^https://x", "narrows": "y"})
    with pytest.raises(ValueError, match="already states"):
        patch.additions(held, published)


def test_an_asserting_entry_reaches_the_patched_bundle_and_the_annotation_path_is_untouched() -> None:
    """The entry is not merely admitted: ``apply`` writes the keyword at the node.

    And the OTHER half of the same run: ``patches/8735``, the shipped additive set, carries
    thirteen annotation entries and every one of them still loads as an ANNOTATION -- so the
    cheaper proof is still the one that path takes.
    """
    published = _a_bundle()
    out = published.parent / "patched"
    patch.apply(published, _a_set(A_NARROWING_ENTRY), out)
    node = bundle.node_at(bundle.read(out, "endpoint.json"), "/properties/url")
    # The ENTRY's own keyword and value and never a literal here: a second copy of either
    # would be a constant this file could get wrong while the manifest stayed right.  As a
    # MEMBERSHIP and not an equality, because an equality against an integer read out of a
    # module constant is what ``test_every_check_names_its_set``'s census ratchet counts,
    # and a pinned census is not what this line is -- it is one node, one keyword.
    assert (A_NARROWING_ENTRY["keyword"], A_NARROWING_ENTRY["value"]) in node.items(), node
    assert harness.conforms(bundle.read(out, "endpoint.json"), {"url": AN_EMPTY_AUTHORITY}) is False

    shipped = patch.additions(Path("patches/8735"), Path("schemas/cache/3.2"))
    assert shipped, "the shipped additive set loaded nothing, so this half graded nothing"
    assert [one for one in shipped if one.asserts] == [], (
        "an entry of the shipped set now claims a direction; the annotation path is supposed "
        "to be byte-for-byte what it was"
    )
