"""A PATCH SET, and the patched bundle applying one produces.

``docs/plan/rebuild-plan.md`` §1, "A patched bundle is a legitimate input, and the test
is the RECORD": the bundle handed to the compiler may be a patched copy of the published
one, and **a patch is admissible exactly when every patched document's record is
byte-identical to the published document's record.**  That is this module's whole reason
to exist in the SOURCE layer beside :mod:`codegen.bundle`: a patched bundle is an INPUT,
not a compiler decision, so nothing downstream of here learns that a patch was applied.

**What a patch set is.**  New documents, plus a manifest naming the node in each new
document that the sites come to reference.  It is not a forked bundle: the 1,054 published
documents stay where they are and the patch is the upstream diff, literally -- for #8525,
six files and a rewrite rule, reviewable in one sitting.

**MEASURED, and the measurement is this module's own finding.**  Byte-identity does NOT
hold for the extraction #8525 asks upstream for, and the reason is structural rather than a
defect in the patch: ``record`` inlines a reference's target WHOLE, so a site that comes to
reference a TITLED document also takes that document's ``title`` and ``$schema`` into the
record, where the published site had neither.  §1 asks for byte-identity in one sentence
and for a titled document in the next, and the two cannot both hold.  What DOES hold, over
all 1,054 documents, is the condition byte-identity was reached for: no keyword that
decides acceptance differs at any pointer (:func:`seen_by_a_validator`).  Both figures are
reported; which of the two is the admissibility line is the plan's call and not this
module's.

**The one rewrite.**  :func:`rewritten` replaces a subschema with a ``$ref`` to the node
the manifest names, and leaves every other key of that subschema where it was.  It is the
INVERSE of :func:`codegen.bundle.record`, which inlines a reference's target and keeps the
referring node's keys beside it, and the two descend and rebuild by the same pair of
functions (:func:`codegen.bundle.subschemas`, :func:`codegen.bundle.rebuilt`) so they
cannot disagree about which node a pointer names.

**Why the match is so narrow.**  A site is rewritten only when the manifest's node accounts
for every key of it that is not an ANNOTATION, and ``is_an_annotation`` is
:func:`codegen.bundle.record`'s own predicate rather than a list of key names.  Draft-07
IGNORES every sibling of a ``$ref``, so a CONSTRAINING key left beside one is a key the
patched document no longer asserts -- the record would still show it, because ``_beside``
keeps it, and the check would pass over a patch that had quietly widened the protocol.
Requiring the node to account for all of them closes that gap at the only place it can be
closed, which is the match.

**EVERY ENTRY NAMES THE DEFECT IT COMPENSATES FOR AND THE ASK FILED AGAINST IT**, and
:func:`load` and :func:`additions` REFUSE one that does not.
``docs/plan/architecture.md``, "THE JUDGMENT IS DATA, NEVER CODE": *"an entry with no named
defect is not a judgment, it is a preference, and it does not belong in the table"*.  Two
strings per entry rather than one, because they answer different questions -- the defect is
what the bundle does, the ask is where we said so -- and a table whose rows carry only the
second is a list of issue numbers nobody can check against the schema.

**THE ADDITIVE KIND, and its failure clause is the part that is easy to drop.**  An
:class:`Addition` is one published document, one pointer and one keyword: *"where extraction
is wrong -- a structure stated once that merely wants naming -- the override adds the
keyword in place"*.  It inherits every property of the extraction and replaces exactly one,
because it has no document of its own for :func:`load`'s refusal to range over:

* an extraction FAILS the day its ask lands because the published bundle comes to hold the
  document the manifest names;
* an addition fails the day its ask lands because **the node comes to carry the keyword
  itself**, and :func:`additions` raises there rather than overwriting.  An additive
  override that silently won over a published value is the one form of this mechanism that
  could outlive its cause invisibly, and it would do so while looking like success.

**AN ADDITION THAT ADDS AN ANNOTATION IS ADMISSIBLE BECAUSE ITS PROOF IS FREE**, by the
same predicate the record check reads.  §1's admissibility line is byte-identity and an
addition moves the record by exactly the annotation it adds, so what holds for it is the
condition byte-identity was reached for (:func:`seen_by_a_validator`) -- and for an
annotation that condition is empty BY CONSTRUCTION, because the keyword decides no
acceptance anywhere.  That path is unchanged and it keeps its cheaper proof.

**AND AN ADDITION MAY ALSO ASSERT, IN WHICH CASE THE EVIDENCE IS DIRECTION AND NOT
IDENTITY** (``docs/plan/rebuild-plan.md`` §8, "AN OVERRIDE MAY ASSERT, AND WHAT MAKES IT
ADMISSIBLE IS THE DIRECTION").  An asserting entry changes what the document accepts, which
is the whole reason to write one, so byte-identity of the validator's view is not available
to it and the refusal that used to read *"this keyword decides acceptance, so adding it
forks the protocol"* was refusing the kind rather than the direction.  What replaces it:

* **it may only NARROW**, and the set it removes must be one the emitted class already
  refuses, so the patch closes the gap in the DOCUMENT's favour;
* **the proof is a VALUE** the entry carries (``narrows``), admitted by the published
  document and refused by the patched one -- *"an asserting entry is a schema defect written
  down with a value attached, and the value is what distinguishes it from an opinion"*;
* **a widening assertion is refused outright** and the refusal names the value that proves
  it widens (:func:`_direction`), because a compiler that cannot represent a constraint
  could otherwise delete the constraint and report agreement.

The expiry clause is untouched by all of it: the published node already stating the keyword
is an entry to DELETE and never a value to overwrite.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

from codegen import bundle, keywords, store

#: The manifest's filename inside a patch set directory.
MANIFEST = "manifest.json"
#: The directory inside a patch set holding the new documents, laid out at the paths they
#: take in the bundle.
DOCUMENTS = "documents"

#: **THE SUFFIX OF THE RECORD THAT STANDS BESIDE A BUNDLE DIRECTORY**, published or patched.
#:
#: ``docs/plan/architecture.md``, under "AND A BUNDLE DIRECTORY MUST SAY WHETHER IT IS
#: PATCHED, BECAUSE A CALLER CANNOT TELL": *the patched directory carries its own record of
#: what was applied, and applying the same set again is a no-op that says so.*
#:
#: **BESIDE THE DIRECTORY AND NEVER INSIDE IT.**  ``bundle.portable`` enumerates
#: ``bundle.rglob("*.json")``, so a record written under the bundle root would be a
#: DOCUMENT -- compiled, graded and counted among the 1,625.  The published bundles already
#: spell it this way (``schemas/cache/3.2.provenance.json``), and ``tests/provenance.py``
#: takes this constant rather than restating it: a convention spelled twice is tested by how
#: many readers obey it, which is a count that only ever goes down.
RECORD_SUFFIX = ".provenance.json"

#: **THE PATCH SETS THE BUILD APPLIES, in the order they are applied** -- paths relative to
#: the checkout, which is where a patch set lives.
#:
#: This is the one declaration of it, and :func:`for_build` is the one way to the bundle a
#: run reads.  **Measured before this existed: ``grep 'patch.apply\\|patch.additions'
#: codegen/*.py`` matched NOTHING** -- this module was read by two test files and by no
#: compile path, ``codegen/__main__`` read the published bundle raw, and the override table
#: was therefore measured, written, reviewed and consumed by nothing.  An override the
#: emitter never sees compensates for no defect.
#:
#: **A TUPLE AND NOT A PATH, because the two kinds compose**: ``patches/8525`` extracts and
#: ``patches/8735`` annotates, each is applied to the output of the one before it, and
#: :func:`load`'s and :func:`additions`' refusals then range over the bundle as the previous
#: set left it -- so a set whose ask has landed upstream breaks the BUILD and not a test.
#:
#: **THE EXTRACTIONS ARE FIRST AND THEY ARE WHERE A CLASS MOVES.**  An addition adds an
#: annotation, so it can move a NAME; an extraction adds a document and rewrites each
#: matching site to ``$ref`` it, so it moves a class from the site to the new document and
#: turns every other site into an import.  ``patches/8525`` carries five such documents and
#: none of them was in the bundle any run read: the whole point of the set -- "extraction
#: gives the structure a document path, which IS its name" -- had never reached the tree.
BUILD = ("patches/8525", "patches/8735")


def record_path(bundle_dir: Path) -> Path:
    """The record that stands beside ``bundle_dir``: ``<bundle_dir><RECORD_SUFFIX>``.

    One spelling of the convention, for both kinds of bundle.  ``tests/provenance.py``
    reads the published bundles' records through this function and :func:`for_build`
    materialises the patched one's beside the directory it names.
    """
    return bundle_dir.with_name(f"{bundle_dir.name}{RECORD_SUFFIX}")


def record_beside(bundle_dir: Path) -> dict | None:
    """The record beside ``bundle_dir``, parsed, or ``None`` where there is none.

    ``None`` and not a raise, because a bundle with no record is the ordinary case for
    every bundle assembled in a test: the suite builds two-document directories in
    ``tmp_path`` and patches them, and requiring a record of those would make this
    mechanism a tax on every fixture rather than a reading of the two bundles that are
    shipped.  What a missing record costs is stated at :func:`sets_applied`.
    """
    path = record_path(bundle_dir)
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def sets_applied(bundle_dir: Path) -> tuple[str, ...] | None:
    """**The patch sets ``bundle_dir`` ALREADY HOLDS, read off the record beside it**, or
    ``None`` where no record says.

    This is the reading the architecture rule exists for.  A published bundle and the
    directory :func:`for_build` materialises are both *a directory of documents*: before
    this function there was nothing to ask, so :func:`for_build` applied the table to
    whatever it was handed and the second application raised :func:`load`'s *"the published
    bundle already holds it"* -- **the expiry refusal, firing for a reason that is not
    expiry.**  Three readers got that wrong in one day (``adcp-client-python-ywff``,
    ``adcp-client-python-qzx.17``, and a re-emit of my own), which is an interface inviting
    the error rather than three careless callers.

    ``None`` is *"no record says"* and is treated as a published bundle, which is what it
    was before this existed.  A published bundle's own record (``schemas/cache/3.2.
    provenance.json``) states no ``applied`` key and reads ``None`` here too -- the key's
    ABSENCE is the statement, so the two shipped records needed no edit and a bundle that
    has been patched cannot be mistaken for one that has not.
    """
    record = record_beside(bundle_dir)
    if record is None or "applied" not in record:
        return None
    return tuple(str(name) for name in record["applied"])


def _ground_of(source: Path) -> dict | None:
    """The PUBLISHED bundle's own record, as reached from ``source`` -- which may itself be a
    patched step of the same build, in which case it already carries the answer forward.

    ``None`` is *"not groundable"*: ``source`` is a bundle with no record of its own, or a
    patched copy of one.  Said once here because both writers of a patched record need it and
    the two must not disagree about what grounds a bundle.
    """
    beside = record_beside(source)
    if sets_applied(source) is None:
        return beside
    beside = beside or {}
    if not beside.get("grounded"):
        return None
    return {
        "bundle": beside.get("published"),
        "digest": beside.get("published_digest"),
        "upstream": beside.get("upstream"),
    }


def _a_patched_record(ground: dict | None, applied: Sequence[str]) -> dict:
    """What the record beside a patched directory says, as a function of its inputs alone.

    **ONE RECORD, BOTH JOBS**, which is the rule's last clause: *"the reading that makes a
    bundle groundable -- the record beside it naming its upstream state -- is the same
    record doing both jobs."*  So this states what was applied AND carries the published
    bundle's own upstream state forward, by REFERENCE to the record beside it rather than by
    re-deriving it: the ``digest`` here is the digest that record states, and
    ``tests/test_a_bundle_states_which_upstream_it_is.py`` is what keeps that claim a fact
    about the bytes rather than a decoration.  Re-digesting 125 MB to copy a gated figure
    would buy nothing and would be paid on every cold build.

    **A FUNCTION OF ITS INPUTS AND NOT OF THE DIRECTORY IT SITS BESIDE**, which is what makes
    it safe to rename: :func:`for_build` stages a patched bundle under a temporary name and
    ``os.replace``\\ s it onto its key, and a record naming its own directory would be wrong
    for half of that. The directory's name is already a digest of these same inputs, so
    stating it here would be a second, staler copy of the answer.

    **AND THE PUBLISHED BUNDLE IS NAMED THE WAY ITS OWN RECORD NAMES IT**, which is the
    checkout-relative spelling ``store.key`` normalises to -- taken from the record rather
    than re-derived, so the two cannot drift and this module needs no second normalisation
    of a path.  ``grounded`` is false where the published bundle carries no record at all --
    a patched copy of a fixture, which is groundable in nothing and says so rather than
    reading as upstream-less.

    **``applied`` IS CUMULATIVE, because the sets compose.**  ``apply`` is called once per set
    over the output of the one before it, so each step's record states every set applied so
    far and the LAST step's record is the whole BUILD's.  ``patch_set_digest`` ranges over
    that cumulative list, which is exactly the digest :func:`for_build` keys the directory
    on, so the record and the directory's name are a function of one thing.

    **TWO WRITERS AND ONE DERIVATION**, which is why ``ground`` is an argument rather than a
    path to read: :func:`apply` writes a step's record and :func:`for_build` writes a missing
    one back beside a directory it finds already built, and the two reach the published
    bundle differently (:func:`_ground_of`) while owing the same answer.
    """
    named = (ground or {}).get("bundle")
    return {
        "patched": True,
        "applied": list(applied),
        "patch_set_digest": _patch_set_digest([Path(name) for name in applied]),
        "published": named,
        "grounded": ground is not None,
        "published_digest": (ground or {}).get("digest"),
        "upstream": (ground or {}).get("upstream"),
        "says": (
            f"This directory is {named or 'a bundle carrying no provenance record'} with "
            f"{', '.join(applied)} already applied. Applying the same sets again is a "
            "no-op; applying one of them again is a DOUBLE APPLICATION and is refused "
            "here, not by the expiry rule -- which means only that an override's defect "
            "is gone."
        ),
    }


def _patch_set_digest(sets: Sequence[Path]) -> str:
    """A digest over every file of every patch set, path and bytes alike.

    The patched bundle is a function of the published bundle, these files, and the code that
    applies them; :func:`for_build` keys on all three and this is the middle one.  The PATH
    is in the digest beside the bytes, so adding an empty file changes the answer and
    renaming one does too -- ``store.compiler_digest``'s own rule, for the same reason.
    """
    h = hashlib.sha256()
    for patch_set in sets:
        for path in sorted(patch_set.rglob("*")):
            if not path.is_file():
                continue
            h.update(path.relative_to(patch_set).as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def for_build(published: Path, sets: Sequence[str] = BUILD) -> Path:
    """**The bundle a RUN reads: ``published`` with every patch set of ``sets`` applied.**

    ``docs/plan/rebuild-plan.md`` §1, "A patched bundle is a legitimate input": the patch is
    an INPUT and not a compiler decision, so this is the one seam between the published
    bundle and everything downstream, and nothing downstream learns a patch was applied.
    Every entry point goes through it -- ``codegen.__main__``, ``./check``,
    ``tests/fresh.py`` and ``tests/test_emit.py`` -- so **there is one patched bundle and
    not one per reader.**  Two readers of two bundles would report two sets of figures over
    two different inputs, which is exactly the defect of a patch set applied only in a test.

    **MATERIALISED ON DISK AND KEYED ON WHAT IT IS A FUNCTION OF**, because every reader
    downstream takes a bundle DIRECTORY -- ``bundle.read`` opens files, ``bundle.portable``
    walks them -- and an in-memory overlay would be a second reading of the bundle that the
    record check could not range over.  The key is ``store.key``'s, which already covers the
    compiler's own source and the published bundle's name, plus a digest of the patch set's
    files (:func:`_patch_set_digest`); so an edit to the override table moves the directory,
    there is nothing to invalidate by hand, and the compile store beneath keys on this
    directory's own path and cannot be handed a compile of the other bundle.

    **An EMPTY ``sets`` is ``published`` itself**, unmaterialised: a caller that applies no
    patch is reading the published bundle, and copying it to say so would be 125 MB of
    answer to a question nobody asked.

    **AND THE SAME SETS APPLIED TO AN ALREADY-PATCHED DIRECTORY IS A NO-OP THAT SAYS SO**
    (``docs/plan/architecture.md``, "AND A BUNDLE DIRECTORY MUST SAY WHETHER IT IS PATCHED,
    BECAUSE A CALLER CANNOT TELL"; ``adcp-client-python-ywff``, ``adcp-client-python-qzx.17``).
    ``sets`` is part of the BUILD and the bundle is an ARGUMENT, so this function applied the
    table to whatever it was handed -- and handed its own OUTPUT it applied the table twice
    and raised :func:`load`'s *"the published bundle already holds it"*, which is the EXPIRY
    rule's sentence about a defect upstream has fixed.  One refusal with two meanings means
    neither, and three readers decided it wrong in one day.  So the question is now asked of
    the VALUE: :func:`sets_applied` reads the record beside the directory, and a directory
    that already holds exactly these sets is returned unchanged.

    **A DIFFERENT set against a patched directory RAISES, and the message is about the
    double application.**  There is no reading under which stacking a second table onto a
    materialisation is what a caller meant -- ``sets`` composes HERE, in one derivation, so
    a caller wanting both names both -- and a refusal that stays silent about the real cause
    is how this defect lasted.

    Written to a staging directory and renamed, because two xdist workers race for the same
    key and a half-copied bundle read by a sibling would be a document set with holes rather
    than a miss.  A rename onto an existing directory is not atomic, so the loser of the
    race keeps its own copy and discards it -- the worst a race costs is 0.8 s and 125 MB,
    never a different answer.

    **THE RECORD TRAVELS BEFORE THE DIRECTORY IT DESCRIBES**, which is the one ordering that
    makes the reading above safe under that race: a sibling worker polls ``at.is_dir()``, so
    a directory that arrived before its record would be read as PUBLISHED for as long as the
    gap lasted, and that is the exact state this function exists to make unobservable.  The
    record is a file, so ``os.replace`` of it IS atomic, and it is a function of the inputs
    alone (:func:`_a_patched_record`) -- so the loser of the race overwrites the
    winner's with identical bytes.
    """
    held = [Path(name) for name in sets]
    done = sets_applied(published)
    if done is not None:
        if done == tuple(str(name) for name in sets):
            return published
        raise ValueError(
            f"{published} is already a patched bundle: the record beside it says "
            f"{', '.join(done) or '(nothing)'} was applied to "
            f"{(record_beside(published) or {}).get('published')}, and this asks for "
            f"{', '.join(str(name) for name in sets) or '(nothing)'}. Applying a set to a "
            "patched directory is a DOUBLE APPLICATION, not an expiry -- name the PUBLISHED "
            "bundle, which is what a --bundle argument is, and let one derivation apply the "
            "whole BUILD"
        )
    if not held:
        return published
    key = store.key(published, (_patch_set_digest(held),))
    at = store.CACHE_ROOT / "patched-bundle" / key
    at.parent.mkdir(parents=True, exist_ok=True)
    if not at.is_dir():
        staged = at.with_name(f"{key}.{os.getpid()}.tmp")
        source = published
        for index, patch_set in enumerate(held):
            step = staged if index == len(held) - 1 else Path(f"{staged}.{index}")
            apply(source, patch_set, step)
            source = step
        os.replace(record_path(staged), record_path(at))
        try:
            os.replace(staged, at)
        except OSError:
            shutil.rmtree(staged, ignore_errors=True)
        for index in range(len(held) - 1):
            shutil.rmtree(f"{staged}.{index}", ignore_errors=True)
            record_path(Path(f"{staged}.{index}")).unlink(missing_ok=True)
    elif not record_path(at).is_file():
        # **THE RECORD IS WRITTEN BACK RATHER THAN MISSED**, because the invariant this
        # function now rests on is *"the directory exists, so the record does"* -- and a
        # directory built here is the only thing that can be at this key, so what it holds is
        # known without reading it.  Without this line a record deleted by hand would leave
        # the directory indistinguishable from a published bundle again, which is one
        # ``rm`` between here and the defect.  The derivation is the same one.
        record_path(at).write_text(
            json.dumps(
                _a_patched_record(_ground_of(published), [str(name) for name in sets]), indent=2
            )
            + "\n"
        )
    return at


class Extraction(NamedTuple):
    """One repeated subschema, the document it moves into, and where the sites point.

    ``subschema`` is READ from the new document at ``pointer`` and is never written in the
    manifest, so the thing the sites must match and the thing they resolve to are one
    object.  A manifest that stated it separately would be a second copy of the patch, and
    a patch whose two copies drifted would pass the record check at the sites it still
    matched and silently skip the rest.

    ``apart`` is the one thing a walk cannot decide: a site whose SHAPE matches and whose
    MEANING does not.  ``^[A-Z]{3}$`` is a currency code at 83 sites and an IATA airport
    code at two, and a document named for one of those asserts, at the other, something
    the bundle never said.  So the exclusions are written down, each with the reason the
    reviewer needs, and :func:`load` refuses one that matches nothing -- a stale exclusion
    would silently widen the patch the day the site it named moved.
    """

    #: Bundle-relative path of the new document.
    document: str
    #: JSON Pointer into that document naming the node the sites reference; ``""`` is its
    #: root.
    pointer: str
    #: The ``$ref`` URI the sites are given, in the published bundle's own spelling.
    uri: str
    #: The node at ``pointer``.
    subschema: dict
    #: ``(document, pointer)`` of each shape-matching site that means something else.
    apart: frozenset[tuple[str, str]]
    #: **What the BUNDLE does that this entry compensates for**, as a sentence about the
    #: published documents.  The module docstring's rule, and :func:`load` refuses an entry
    #: stating none.
    defect: str = ""
    #: **Where we said so**: the ask filed against the defect.
    ask: str = ""


class Dissent(NamedTuple):
    """One absolute reference whose base URI is not the one its bundle publishes under.

    Named rather than counted, because a count is a majority vote and a majority vote is
    exactly how the SECOND such reference would arrive unseen.  Each of these is an
    upstream defect with a document, a pointer and a one-line change: a cross-version
    absolute ``$ref`` either names a frozen schema the bundle does not carry -- in which
    case the bundle is incomplete -- or it names the bundle's OWN document and should be
    spelled as such, which is what ``bundle.document_for`` resolves it to today.
    """

    #: Bundle-relative path of the referring document.
    document: str
    #: JSON Pointer of the referring node.
    pointer: str
    #: The reference, as the document spells it.
    uri: str
    #: The base URI it states, which is not :attr:`Base.prefix`.
    prefix: str

    def __str__(self) -> str:
        return (
            f"{self.document}#{self.pointer or '/'} states base {self.prefix!r} and its "
            f"bundle publishes under another: {self.uri}"
        )


#: **THE SHARE OF A BUNDLE'S RESOLVING ABSOLUTE REFERENCES THAT HAVE TO AGREE** for a
#: prefix to be the bundle's own (:func:`bases`).
#:
#: **Why a threshold at all, and why this one.**  The prefix exists to spell a NEW
#: reference the bundle would recognise as its own, and a bundle publishes under ONE base.
#: So the question a share answers is not "which prefix wins" -- ``max()`` answers that and
#: answers it for a bundle assembled out of two publications, where the new reference would
#: be right for one half and wrong for the other.  It is "does this bundle have ONE
#: publication base, with the disagreements being defects in individual references".
#:
#: At ``0.99`` a prefix is the bundle's own when all but a hundredth of its references
#: spell it, and the rest are named (:class:`Dissent`).  Not ``1.0``, which is what this
#: refused at before and is **measured wrong on bundle 3.3**: 4,163 of its 4,164 resolving
#: absolute references spell ``.../schemas/3.3.0-beta.0/`` (99.976%) and ONE spells
#: ``.../schemas/3.2.1/``, so the whole bundle was unpatchable over a single stale literal
#: in upstream's own source.  And not a bare majority, because a 51/49 split is precisely
#: the two-publication bundle this refusal exists for -- a line drawn at "more than half"
#: would admit it and hand a new reference a prefix two-fifths of the bundle disowns.
#:
#: **The share is over EDGES and not documents**, because an edge is what a new reference
#: is one more of.  Bundle 3.2 states 3,795 resolving references over 677 documents and
#: dissents nowhere; bundle 3.3 states 4,164 over 732 and dissents once.  On a bundle of
#: 3.3's size the line admits up to 41 dissenting references -- a list a reviewer reads one
#: by one, which is the condition under which calling them defects is honest -- and refuses
#: any split a reviewer would have to call a second base.
BASE_URI_AGREEMENT = 0.99


class Base(NamedTuple):
    """The prefix a bundle's absolute references AGREE on, and every reference that does not.

    Two fields and not one, because the disagreement is a FINDING and the prefix is an
    answer: :func:`load` needs the string, and the run needs the names
    (``codegen.__main__``, which prints one line per dissent exactly as section 5's
    ``default`` row is "dropped and REPORTED").
    """

    #: The bundle's own base URI.
    prefix: str
    #: Every resolving absolute reference stating a different one, in document order.
    dissenting: tuple[Dissent, ...]

    def report(self) -> str:
        """One line per dissenting reference, or ``""`` where the bundle agrees with itself."""
        return "\n".join(str(d) for d in self.dissenting)


def bases(bundle_dir: Path) -> Base:
    """The prefix the bundle's own absolute ``$ref``\\ s put before a document path, and
    every reference of it that states a different one.

    DERIVED from the published bundle rather than written down, for ``bundle.document_for``'s
    reason: every reference in 3.2 is spelled ``.../schemas/3.2.4/<path>``, and a literal
    here would be a version in ``codegen/`` (D9) and would be wrong for a bundle publishing
    under a different base.  Read off the references that already resolve: the prefix a URI
    has left once the document path it names is taken off its end.

    **A DISAGREEMENT IS REPORTED AND NOT FATAL**, which is the whole of this function's
    revision, and :data:`BASE_URI_AGREEMENT` carries the reason and the measurement.  It
    refused a bundle whose references stated more than one prefix, full stop; that refusal
    ranges over the bundle rather than over a patch entry, so **one stale literal made
    bundle 3.3 unpatchable in full** -- ``apply`` calls :func:`load`, :func:`load` asked for
    the prefix, and ``python -m codegen --bundle schemas/cache/3.3`` raised with it.

    Raises ``ValueError`` still, and for the two cases that leave a new reference with no
    spelling to take:

    * the bundle states NO resolving absolute reference, so there is no prefix to read;
    * no prefix reaches :data:`BASE_URI_AGREEMENT`, so the bundle does not have one
      publication base -- the refusal names every prefix with its share, because "which two
      are they" is the first thing a reader of that refusal needs.
    """
    documents = set(bundle.portable(bundle_dir))
    found: dict[str, list[Dissent]] = {}
    for edge in bundle.edges(bundle_dir):
        head, _ = bundle.split_ref(edge.uri)
        if not head:
            continue
        named = bundle.document_for(head, documents)
        if named is not None and head.endswith(named):
            prefix = head[: len(head) - len(named)]
            found.setdefault(prefix, []).append(
                Dissent(edge.document, edge.pointer, edge.uri, prefix)
            )
    if not found:
        raise ValueError(
            f"{bundle_dir}: it states no absolute reference that resolves to a document of "
            "its own, so a new reference has no spelling to take"
        )
    total = sum(len(one) for one in found.values())
    prefix, agreeing = max(found.items(), key=lambda kv: (len(kv[1]), kv[0]))
    if len(agreeing) < BASE_URI_AGREEMENT * total:
        shares = ", ".join(
            f"{one} ({len(found[one])}/{total})" for one in sorted(found, key=lambda p: -len(found[p]))
        )
        raise ValueError(
            f"{bundle_dir}: no base URI is stated by {BASE_URI_AGREEMENT:.0%} of its "
            f"{total} resolving absolute references, so it does not publish under one base "
            f"and a new reference has no spelling to take -- {shares}"
        )
    dissenting = sorted(
        (d for one in found.values() for d in one if d.prefix != prefix),
        key=lambda d: (d.document, d.pointer),
    )
    return Base(prefix, tuple(dissenting))


def base_uri(bundle_dir: Path) -> str:
    """The prefix alone: :attr:`Base.prefix` of :func:`bases`.

    Kept as its own name because a caller spelling a URI wants the string and has nothing
    to do with the dissent -- :func:`load` is that caller.  The reporting side takes
    :func:`bases` and reads both fields, so neither reader has to know the other's business
    and there is one derivation of the prefix.
    """
    return bases(bundle_dir).prefix


def _judged(entry: Mapping, at: str) -> tuple[str, str]:
    """The ``defect`` and the ``ask`` of one manifest entry, or raise.

    The module docstring's rule, enforced at the one door every entry comes through: an
    entry with no named defect is a preference and not a judgment, and an entry with no ask
    is a fork nobody upstream has been told about.  Blank counts as absent -- a key present
    with an empty string is the same preference with a key over it.
    """
    defect = str(entry.get("defect") or "").strip()
    ask = str(entry.get("ask") or "").strip()
    if not defect:
        raise ValueError(f"{at}: the entry names no upstream defect, so it is a preference")
    if not ask:
        raise ValueError(f"{at}: the entry names no ask filed against its defect")
    return defect, ask


def load(patch_set: Path, published: Path) -> tuple[Extraction, ...]:
    """The patch set's extractions, in manifest order, with each subschema read.

    Raises ``ValueError`` for a manifest entry naming a document the patch set does not
    carry, a pointer naming no node of it, a document path the published bundle already
    holds -- a patch REPLACING a published document is a different operation from this one
    and the record check could not tell the two apart -- or an entry naming no upstream
    defect and no ask (:func:`_judged`).

    **THE BASE URI IS READ ONLY WHERE AN EXTRACTION NEEDS ONE**, and that is a property of
    the mechanism rather than a saved call.  An extraction's :attr:`Extraction.uri` is the
    one thing here that has to be spelled in the BUNDLE's own idiom, so a manifest holding
    extractions is gated on the bundle having a base and a manifest holding none is gated on
    nothing.  Read eagerly, ``patches/8735`` -- thirteen additions and **zero** extractions,
    which add a keyword at a published pointer and reference nothing -- was refused on
    bundle 3.3 for a spelling it never asks the bundle for.
    """
    manifest = json.loads((patch_set / MANIFEST).read_text())
    entries = tuple(manifest.get("extractions", ()))
    prefix = bases(published).prefix if entries else ""
    held = set(bundle.portable(published))
    out = []
    for entry in entries:
        document, pointer = entry["document"], entry["pointer"]
        defect, ask = _judged(entry, f"{document}#{pointer}")
        if document in held:
            raise ValueError(f"{document}: the published bundle already holds it")
        path = patch_set / DOCUMENTS / document
        if not path.is_file():
            raise ValueError(f"{document}: the patch set carries no such document")
        node = bundle.node_at(json.loads(path.read_text()), pointer)
        if not isinstance(node, dict):
            raise ValueError(f"{document}#{pointer} names no schema node")
        apart = frozenset((a["document"], a["pointer"]) for a in entry.get("apart", ()))
        # The bundle spells a WHOLE-DOCUMENT reference with no ``#`` at all -- 738 of its
        # 814 absolute references -- and the trailing ``#`` is not cosmetic: ``split_ref``
        # reads the delimiter, so the two spellings put the reference down different rows,
        # and the fragment row binds a SYMBOL where the document row binds the target's
        # whole shape.  Spell it the way the bundle does, or the patch is not the diff.
        uri = f"{prefix}{document}" + (f"#{pointer}" if pointer else "")
        out.append(Extraction(document, pointer, uri, node, apart, defect, ask))
    return tuple(out)


class Addition(NamedTuple):
    """One PUBLISHED node, one keyword it does not state, and the value to add there.

    The second kind of override and the smaller one: where extraction is wrong -- a
    structure stated once that merely wants naming -- there is no new document and no
    rewrite, only a keyword the bundle omits at a node it already has a path and a pointer
    for.  Extracting such a node would give the structure a SECOND name, which is the one
    thing naming it was for.

    **Its failure clause is :attr:`keyword` carried by the node itself**, which is
    :func:`load`'s "the published bundle already holds it" read for a kind that adds no
    document.  See :func:`additions`.
    """

    #: Bundle-relative path of the PUBLISHED document the keyword is added to.
    document: str
    #: JSON Pointer naming the node; ``""`` is the document's root.
    pointer: str
    #: The keyword added there.  Either an ANNOTATION by ``bundle.is_an_annotation`` at
    #: that node's position -- whose proof is :func:`seen_by_a_validator` being empty by
    #: construction -- or an ASSERTION, whose proof is :attr:`narrows` and whose direction
    #: is checked by :func:`_direction`.
    keyword: str
    #: Its value.
    value: object
    #: **What the BUNDLE does that this entry compensates for.**
    defect: str
    #: **Where we said so**: the ask filed against the defect.
    ask: str
    #: **THE PROVING VALUE OF AN ASSERTING ENTRY**, and ``None`` for an annotation.
    #:
    #: A value the PUBLISHED document admits and the PATCHED document refuses, stated at
    #: the node's own pointer.  :func:`additions` checks both halves against a draft-07
    #: validator before the entry is returned, so this is a measurement the manifest
    #: carries rather than a claim it makes.  The third half -- *the emitted class refuses
    #: it too* -- is the grader's, because this module is the SOURCE layer and has no class
    #: to ask.
    narrows: object = None
    #: **Does this entry change what the document accepts?**
    #:
    #: A STATED field and not a read off :attr:`narrows`, because a manifest stating
    #: ``"narrows": null`` is a proving value of JSON null and absence is not: one sentinel
    #: standing for both is how a kind comes to be decided by a value's spelling.  It is
    #: also not a read off the keyword -- the keyword's kind is exactly what the refusal
    #: this replaced mistook for the question -- so the manifest DECLARES which of the two
    #: proofs it offers and :func:`additions` refuses a mismatch in either direction.
    asserts: bool = False


#: The property key and the string filler :func:`_carriers` and :func:`_an_instance` reach
#: for where a document leaves them free.
#:
#: Spelled to collide with nothing a schema author writes, for ``harness._ALIEN_KEY``'s
#: reason: a probe key that happened to BE a declared property would be screened by the
#: document as that property and the carrier would stop reaching the pointer.
_PROBE_KEY = "__adcp_direction_probe__"

#: How deep :func:`_an_instance` descends a node's own ``properties`` and ``items``.
#:
#: **A BUDGET, and it is the only place this search can fail to terminate.**  A document
#: whose ``properties`` cycle through a ``$ref`` is not reached at all (see
#: :func:`_carriers`' limits), but a deeply nested object is, and filling its ``required``
#: keys is recursive.  Past the budget the fill is ``None`` -- a carrier the published
#: document then refuses, which costs a finding and can never manufacture one, because
#: every candidate is screened against BOTH documents and a widening needs the published
#: one to refuse while the patched one admits.
_FILL_DEPTH = 6

#: How many (carrier, candidate) pairs :func:`_direction` screens for one entry.
#:
#: Reported in the refusal when it is reached, so an entry admitted after the budget ran
#: out is not read as an entry proved inside it.  Measured on the two shapes the suite
#: builds: a widening under a ``not`` is found at pair 2 of 14 and a narrowing at a
#: ``properties`` leaf is proved at pair 1 of 11, so the budget is far above the shapes and
#: is not tuned to them.
_DIRECTION_BUDGET = 4000


def _screen() -> tuple[Callable[..., bool | None], Any]:
    """The run's own reading of *"the document admits this value"*, and its witnesses.

    ``harness.conforms`` and ``harness.refused_witnesses``, reached by a FUNCTION-LOCAL
    import, which is a layering statement and not a saved millisecond.  A patch is an
    INPUT (§1), so this module sits in the SOURCE layer beside :mod:`codegen.bundle` and
    nothing in the compile path may depend on the grader at module scope.  What the
    direction test needs, though, is exactly the grader's reading: ``conforms`` runs the
    draft the document declares WITH that draft's own format checker
    (``harness._validating``), which is the same screen ``check_accepts`` puts every
    instance through.  A second validator spelled here would be a second answer to *"does
    the document admit it"*, and this epic has already paid for one of those.
    """
    from codegen import harness

    return harness.conforms, harness


def _an_instance(node: object, depth: int = 0) -> object:
    """A value ``node`` plausibly admits, built from the node's own keywords.

    **Plausibly, and the word is load-bearing**: nothing here claims the document admits
    the result.  The claim is made by ``conforms`` in :func:`_direction`, which is
    ``harness.refused_witnesses``' own split -- *"a keyword whose far side this cannot
    build contributes no witness and costs no verdict"*.  A fill this gets wrong produces a
    carrier the published document refuses, and a carrier the published document refuses
    cannot produce a false widening: a widening needs the published document to refuse and
    the patched one to ADMIT, and the patched document refuses everything the published one
    does except at the node this entry touches.

    The node's own statements come first -- a ``const``, an ``enum`` member, a ``default``,
    an ``examples`` entry -- because those are values the AUTHOR says the node admits.  A
    ``format`` takes the first of ``harness.FORMAT_SHAPES``' shapes for it and a ``pattern``
    is drawn from with ``harness.matching_a_pattern``, so neither is a witness written down
    here: this module states no value per format and no value per regex.
    """
    if not isinstance(node, Mapping):
        return 0
    if "const" in node:
        return copy.deepcopy(node["const"])
    for key in ("enum", "examples"):
        stated = node.get(key)
        if isinstance(stated, list) and stated:
            return copy.deepcopy(stated[0])
    if "default" in node:
        return copy.deepcopy(node["default"])
    word = node.get("type")
    if isinstance(word, list):
        word = next((w for w in word if isinstance(w, str)), None)
    if word is None:
        word = _implied_word(node)
    if word == "boolean":
        return True
    if word == "null":
        return None
    if word in ("integer", "number"):
        return _a_number(node, word)
    if word == "array":
        return _a_list(node, depth)
    if word == "object":
        return _an_object(node, depth)
    if word == "string":
        return _a_string(node)
    return 0


def _implied_word(node: Mapping) -> str | None:
    """The ``type`` word a typeless node's own constraint keywords imply, or ``None``.

    A node stating ``maxLength`` and no ``type`` admits an instance of every type, so any
    word is a correct answer to "build a value this admits"; the STRING word is the useful
    one, because it is the only type the stated keyword can be crossed on.  This is a
    reading of §5's typeless row from the other side and it decides nothing about
    acceptance -- ``conforms`` still does that.
    """
    for keyword, implied in (
        ("minLength", "string"),
        ("maxLength", "string"),
        ("pattern", "string"),
        ("format", "string"),
        ("properties", "object"),
        ("required", "object"),
        ("minProperties", "object"),
        ("maxProperties", "object"),
        ("items", "array"),
        ("minItems", "array"),
        ("maxItems", "array"),
        ("minimum", "number"),
        ("maximum", "number"),
    ):
        if keyword in node:
            return implied
    return None


def _a_string(node: Mapping) -> str:
    """A string the node's ``format``, ``pattern`` and length bounds point at."""
    _, harness = _screen()
    fmt = node.get("format")
    shapes = harness.FORMAT_SHAPES.get(fmt) if isinstance(fmt, str) else None
    if shapes:
        return str(shapes[0][1])
    pattern = node.get("pattern")
    if isinstance(pattern, str):
        drawn = harness.matching_a_pattern(pattern, 1)
        if drawn:
            return str(drawn[0])
    least = node.get("minLength")
    length = int(least) if isinstance(least, int) else 1
    most = node.get("maxLength")
    if isinstance(most, int):
        length = min(length, most)
    return "a" * max(length, 1)


def _a_number(node: Mapping, word: str) -> int | float:
    """A number inside whatever bounds the node states."""
    low = node.get("minimum", node.get("exclusiveMinimum"))
    high = node.get("maximum", node.get("exclusiveMaximum"))
    value: int | float = 0
    if isinstance(low, (int, float)) and not isinstance(low, bool):
        value = low + 1 if "exclusiveMinimum" in node else low
    if isinstance(high, (int, float)) and not isinstance(high, bool) and value > high:
        value = high - 1 if "exclusiveMaximum" in node else high
    factor = node.get("multipleOf")
    if isinstance(factor, (int, float)) and not isinstance(factor, bool) and factor:
        value = factor * max(round(value / factor), 1)
    return int(value) if word == "integer" else float(value)


def _a_list(node: Mapping, depth: int) -> list:
    """A list of the node's ``minItems`` elements, each built from its ``items`` node."""
    least = node.get("minItems")
    want = max(int(least) if isinstance(least, int) else 1, 1)
    items = node.get("items")
    if isinstance(items, list):
        return [_an_instance(one, depth + 1) for one in items[:want]] or [0]
    one = _an_instance(items if isinstance(items, Mapping) else {}, depth + 1)
    return [copy.deepcopy(one) for _ in range(want)]


def _an_object(node: Mapping, depth: int) -> dict:
    """An object carrying every key the node REQUIRES and nothing else.

    Nothing else, because an undeclared key is what an ``additionalProperties: false``
    refuses -- the carrier has to be the object the document is least likely to refuse for
    a reason this entry says nothing about.
    """
    return _required_fill(node, depth)


def _required_fill(node: Mapping, depth: int, *, besides: str | None = None) -> dict:
    """``node``'s ``required`` keys, each filled from its own declaration."""
    if depth >= _FILL_DEPTH:
        return {}
    declared = node.get("properties") if isinstance(node.get("properties"), Mapping) else {}
    out: dict[str, object] = {}
    for key in node.get("required") or []:
        if not isinstance(key, str) or key == besides:
            continue
        out[key] = _an_instance(declared.get(key, {}), depth + 1)
    return out


def _route(root: Mapping, pointer: str) -> tuple[tuple[tuple[str, str, Mapping], ...], Mapping] | None:
    """Each ``(keyword, suffix, parent)`` step from ``root`` down to ``pointer``, and the node.

    A DESCENT and never a parse of the pointer's text, which is :func:`_position_of`'s own
    rule read one level further: ``bundle.subschemas`` is what says that ``/properties/x``
    is a step through ``properties`` at all, and it is the function :func:`added_at` and
    :func:`rewritten` descend by -- so the direction test and the rewrite cannot disagree
    about which node a pointer names.

    ``None`` where the pointer names no node, which :func:`additions` already refuses on.
    """
    steps: list[tuple[str, str, Mapping]] = []
    node: object = root
    rest = pointer
    while rest:
        if not isinstance(node, Mapping):
            return None
        for keyword, suffix, sub, _ in bundle.subschemas(node):
            if rest == suffix or rest.startswith(f"{suffix}/"):
                steps.append((keyword, suffix, node))
                node, rest = sub, rest[len(suffix) :]
                break
        else:
            return None
    if not isinstance(node, Mapping):
        return None
    return tuple(steps), node


def _carriers(root: Mapping, pointer: str) -> tuple[tuple[str, Callable[[object], object]], ...]:
    """Ways to build an instance of the WHOLE document that reaches ``pointer``.

    **THE DIRECTION TEST IS AT THE DOCUMENT AND NOT AT THE NODE, and this function is why
    that distinction is the whole test rather than a nicety.**  Adding a keyword to a
    schema OBJECT cannot widen that object: draft-07 holds every keyword of a node against
    the same instance, so the node's keywords are a conjunction and one more conjunct
    refuses a subset of what the node refused before.  A direction test asked at the node
    would therefore pass every entry ever written -- *a test that cannot find a widening is
    not a test*.  What CAN widen is the DOCUMENT, because the node may sit in a position
    draft-07 reads negatively:

    * under a ``not``, where refusing more at the node admits more at the document;
    * as the ``if`` of a conditional with an ``else``, where moving the condition moves
      which arm an instance is held to;
    * as a branch of a ``oneOf``, which asserts that EXACTLY one branch matches -- so a
      narrowed branch can take an instance from two matches to one and the document comes
      to admit it.

    All three are reachable only by validating a whole instance against both documents,
    which is what this builds the instance for.

    **ITS LIMITS, because a search that does not state them is a declaration.**  Each is a
    lost finding and never a false pass, since every candidate is screened against both
    documents and a widening needs the published one to REFUSE:

    * **a pointer reached only through a ``$ref``** -- anything under ``definitions`` or
      ``$defs`` -- has no carrier at all, because the instance that reaches it is the
      REFERRER's and this walks one document's own structure.  :func:`_direction` refuses
      such an entry as unprovable rather than admitting it unchecked;
    * **a ``patternProperties`` key is drawn from the regex** (``harness.matching_a_pattern``)
      and a regex it cannot draw from loses the step;
    * **a ``propertyNames`` step is reached only by a string candidate**, since the
      candidate IS the key there;
    * **the fill is per-node and not a solver** (:func:`_an_instance`): a document whose
      acceptance couples two properties -- an ``if``/``then`` across them, a
      ``dependencies`` -- may refuse every carrier this builds, and the entry is then
      unprovable and refused.

    Two variants per route and not one: with every level's ``required`` keys filled and
    with none of them, because a level stating ``additionalProperties: false`` beside a
    ``required`` it does not declare in ``properties`` is refused with the fill and admitted
    without it, and neither variant is right for both.
    """
    routed = _route(root, pointer)
    if routed is None:
        return ()
    steps, _ = routed
    return tuple(
        (f"required {'filled' if fill else 'left out'}", _placing(steps, fill=fill))
        for fill in (True, False)
    )


def _placing(
    steps: Sequence[tuple[str, str, Mapping]], *, fill: bool
) -> Callable[[object], object]:
    """One carrier: the composition of :func:`_wrapped` over ``steps``, innermost first.

    Answers :data:`_UNREACHED` for a candidate no step of this route can carry -- a
    ``definitions`` step, which carries nothing at all, or a ``propertyNames`` step handed
    a candidate that is not a string.  The decision is PER CANDIDATE and not per route
    because the second of those depends on the candidate: a route pre-tested with one value
    would discard every ``propertyNames`` pointer in the bundle.
    """

    def place(value: object) -> object:
        carried = value
        for keyword, suffix, parent in reversed(steps):
            if carried is _UNREACHED:
                return _UNREACHED
            carried = _wrapped(keyword, suffix, parent, carried, fill=fill)
        return carried

    return place


#: What :func:`_wrapped` answers where a step has no instance form at all.  A sentinel and
#: not ``None``, because ``None`` IS an instance -- a ``type: null`` node's only one -- and
#: a carrier that read the JSON null as "unreachable" would silently skip every pointer
#: under one.
_UNREACHED: Any = object()


def _wrapped(
    keyword: str, suffix: str, parent: Mapping, child: object, *, fill: bool
) -> Any:
    """``child`` as the instance its PARENT sees, for one step of a pointer.

    Draft-07's applicator-to-instance relation, which is the one thing the keyword table
    does not state: it says where a keyword holds a subschema and at what POSITION, and
    this says what an instance of that subschema is an instance OF.  Six of the twelve
    cases are the identity, because a combinator's branch describes the same instance the
    combinator does -- which is §8's own union-branch pairing rule arriving here.
    """
    segments = [bundle.unescape_key(s) for s in suffix.split("/")[1:]]
    tail = segments[1] if len(segments) > 1 else None
    if keyword in ("allOf", "anyOf", "oneOf", "not", "if", "then", "else"):
        return child
    if keyword == "properties" and tail is not None:
        return {tail: child, **(_required_fill(parent, 0, besides=tail) if fill else {})}
    if keyword == "additionalProperties":
        return {_PROBE_KEY: child, **(_required_fill(parent, 0) if fill else {})}
    if keyword == "patternProperties" and tail is not None:
        _, harness = _screen()
        drawn = harness.matching_a_pattern(tail, 1)
        if not drawn:
            return _UNREACHED
        return {drawn[0]: child, **(_required_fill(parent, 0) if fill else {})}
    if keyword == "propertyNames":
        return {child: 1} if isinstance(child, str) else _UNREACHED
    if keyword == "dependencies" and tail is not None:
        return {**child, tail: 1} if isinstance(child, dict) else _UNREACHED
    if keyword == "contains":
        return [child]
    if keyword == "items":
        held = parent.get("items")
        if isinstance(held, list) and tail is not None and tail.isdigit():
            index = int(tail)
            return [*(_an_instance(one, 1) for one in held[:index]), child]
        return [child]
    if keyword == "additionalItems":
        held = parent.get("items")
        prefix = [_an_instance(one, 1) for one in held] if isinstance(held, list) else []
        return [*prefix, child]
    return _UNREACHED


def _candidates(published: Mapping, patched: Mapping, witness: object) -> tuple[object, ...]:
    """The values :func:`_direction` offers at the pointer, nearest cause first.

    **Derived from the two nodes and from the entry, and nothing is listed per keyword
    here.**  ``harness.refused_witnesses`` is §8's own witness derivation -- *"both sides
    of each bound and the bound itself, every member of an enum, the value no enum member
    is"* -- and it is asked TWICE, once of each node, because the two directions want
    opposite halves:

    * the values the PATCHED node refuses are the ones a narrowing removes, so they are
      where the entry's own proof lives and, under a ``not``, where a widening does;
    * the values the PUBLISHED node refuses are the complement, and a widening is by
      definition one of them -- the search is for one the patched document then admits.

    Each is a perturbation of :func:`_an_instance`'s value for the node, which is the same
    *"reduce an instance the node admits"* shape ``refused_witnesses`` is built on, so no
    value here is written down per format or per regex.  The entry's declared ``narrows``
    goes first because it is the value a reader of a refusal is owed.
    """
    _, harness = _screen()
    base = _an_instance(published)
    seen: list[object] = []
    for candidate in (
        witness,
        base,
        *(v for v, _, _ in harness.refused_witnesses(dict(patched), base)),
        *(v for v, _, _ in harness.refused_witnesses(dict(published), base)),
        *(v for v, _, _ in harness.refused_witnesses(dict(patched), _an_instance(patched))),
    ):
        if not any(_same(candidate, held) for held in seen):
            seen.append(candidate)
    return tuple(seen)


def _same(one: object, other: object) -> bool:
    """Two candidates that are the same JSON value, compared as text."""
    try:
        return _canonical(one) == _canonical(other)
    except TypeError:
        return one is other


class Widening(NamedTuple):
    """A value proving a patched document admits what the published one refuses."""

    #: The value at the entry's own pointer.
    value: object
    #: The whole instance it was offered inside.
    instance: object
    #: How the carrier reached the pointer.
    how: str


def _direction(
    at: str, root: Mapping, pointer: str, keyword: str, value: object, witness: object, ask: str
) -> None:
    """**THE ADMISSIBILITY OF AN ASSERTING ENTRY: it may only NARROW, proved by value.**

    ``docs/plan/rebuild-plan.md`` §8: *"``load`` refuses an entry whose patched node admits
    any value the published node refuses, and the refusal names the value."*  Three
    refusals, and each one is a property of the mechanism rather than input validation:

    * **the pointer is unreachable**, so no value can prove anything about it.  An asserting
      entry nothing can place is an opinion with a pointer on it, and :func:`_carriers`
      names which pointers those are;
    * **the entry WIDENS**, named by the value -- the one refusal §8 calls the back door
      this ordering exists to close: *"a compiler that cannot represent a constraint could
      otherwise delete the constraint and report agreement"*;
    * **the entry's own value does not narrow**, i.e. the published document does not admit
      it or the patched one does not refuse it.  That is the stale-declaration rule from
      §9 arriving for a patch: a proof the measurement cannot reproduce is deleted rather
      than carried.

    The search is :func:`_carriers` crossed with :func:`_candidates`, every pair screened
    against BOTH documents by ``harness.conforms``, and it is bounded by
    :data:`_DIRECTION_BUDGET`.  What it cannot find is stated at :func:`_carriers`; what it
    cannot do at all is decide the THIRD half of §8's proof -- *the emitted class refuses
    the value too* -- because that half needs a class and this module is the source layer.
    The grader owns it and
    ``tests/test_an_asserting_override_may_only_narrow.py`` is where it is read.
    """
    conforms, _ = _screen()
    patched_root = added_at(dict(root), pointer, keyword, value)
    routed = _route(root, pointer)
    published_node = routed[1] if routed else {}
    patched_node = {**published_node, keyword: value}
    carriers = _carriers(root, pointer)
    candidates = _candidates(published_node, patched_node, witness)
    widening: Widening | None = None
    proved = False
    screened = 0
    for how, place in carriers:
        for candidate in candidates:
            if screened >= _DIRECTION_BUDGET:
                break
            instance = place(copy.deepcopy(candidate))
            if instance is _UNREACHED:
                continue
            screened += 1
            before = conforms(dict(root), instance)
            after = conforms(patched_root, instance)
            if after is True and before is False and widening is None:
                widening = Widening(candidate, instance, how)
            if before is True and after is False and _same(candidate, witness):
                proved = True
    if not screened:
        raise ValueError(
            f"{at}: {keyword!r} ASSERTS, so its evidence is a value -- and no instance of "
            f"this document reaches {pointer or '/'}, so no value can prove the direction. "
            f"An asserting entry nothing can place is an opinion with a pointer on it ({ask})"
        )
    if widening is not None:
        raise ValueError(
            f"{at}: adding {keyword!r} here WIDENS the document, so it is refused outright "
            f"-- the published document REFUSES {_canonical(widening.value)} at "
            f"{pointer or '/'} and the patched one ADMITS it, inside "
            f"{_canonical(widening.instance)} ({widening.how}). An override may only "
            f"narrow: a widening would let a class be called faithful by loosening the "
            f"schema under it ({ask})"
        )
    if not proved:
        raise ValueError(
            f"{at}: the entry's own 'narrows' value {_canonical(witness)} does not prove a "
            f"narrowing -- the published document must ADMIT it at {pointer or '/'} and the "
            f"patched document must REFUSE it, and over {screened} screened candidates it "
            f"does not. A proof the measurement cannot reproduce is deleted, not carried "
            f"({ask})"
        )


def additions(patch_set: Path, published: Path) -> tuple[Addition, ...]:
    """The patch set's additions, in manifest order, each checked against the published node.

    Raises ``ValueError``, and each refusal is one of the mechanism's declared properties
    rather than input validation:

    * **the node already carries the keyword.**  THE REMOVABILITY GUARANTEE, and the reason
      this kind needs one of its own: an extraction fails the day the published bundle holds
      the document it names, and an addition has no document, so what fails is the keyword
      arriving at the node.  The instruction is then to DELETE the entry -- never to prefer
      our value to the protocol's, which is the one way an override here could outlive its
      cause while looking like success;
    * **the entry's declared kind and its keyword's kind disagree.**  An ANNOTATION entry
      (no ``narrows`` key) whose keyword decides acceptance at that position is the old
      refusal, unweakened: by :func:`codegen.bundle.is_an_annotation`, the predicate
      ``record`` itself reads, so there is no second list of which keyword matters, and
      such an entry's only available admissibility line is :func:`seen_by_a_validator` --
      which is unreachable for a keyword a validator acts on.  An ASSERTING entry (a
      ``narrows`` key) whose keyword is an annotation EVERYWHERE is refused the other way
      round: it is claiming a direction nothing can move, so the value it carries proves
      nothing and the cheaper proof is the one it should be taking;
    * **the entry WIDENS, or its own value does not narrow** (:func:`_direction`), which is
      the whole of an asserting entry's admissibility;
    * **the document or the pointer names nothing**, which for this kind is the published
      bundle's own document set and not the patch set's;
    * **the entry names no defect or no ask** (:func:`_judged`).

    **WHAT THE REFUSAL IS NOW CONDITIONAL ON IS THE DIRECTION AND NO LONGER THE KEYWORD'S
    KIND**, which is ``docs/plan/rebuild-plan.md`` §8's new subsection and the one change
    here.  The annotation path is byte-for-byte what it was, because it has a cheaper proof
    and should keep using it.
    """
    manifest = json.loads((patch_set / MANIFEST).read_text())
    held = set(bundle.portable(published))
    out = []
    for entry in manifest.get("additions", ()):
        document, pointer = entry["document"], entry["pointer"]
        keyword = entry["keyword"]
        at = f"{document}#{pointer or '/'}"
        defect, ask = _judged(entry, at)
        if document not in held:
            raise ValueError(f"{document}: the published bundle holds no such document")
        root = bundle.read(published, document)
        node = bundle.node_at(root, pointer)
        if not isinstance(node, dict):
            raise ValueError(f"{at} names no schema node")
        if keyword in node:
            raise ValueError(
                f"{at}: the published node already states {keyword!r}, so this entry's "
                f"defect is gone -- delete it rather than overwrite {node[keyword]!r} "
                f"({ask})"
            )
        asserts = "narrows" in entry
        position = _position_of(root, pointer)
        annotates = position is not None and bundle.is_an_annotation(keyword, position)
        if not asserts and not annotates:
            raise ValueError(
                f"{at}: {keyword!r} decides acceptance at a {position} position, so adding "
                "it forks the protocol rather than annotating it -- an entry that means to "
                "fork it ON PURPOSE declares a 'narrows' value and is graded by direction "
                f"instead ({ask})"
            )
        if asserts and all(
            bundle.is_an_annotation(keyword, every) for every in keywords.Position
        ):
            raise ValueError(
                f"{at}: {keyword!r} states nothing about acceptance at any position, so "
                f"this entry's 'narrows' value cannot be the thing that proves it -- drop "
                f"the key and take the annotation's own proof ({ask})"
            )
        if asserts:
            _direction(at, root, pointer, keyword, entry["value"], entry["narrows"], ask)
        out.append(
            Addition(
                document, pointer, keyword, entry["value"], defect, ask,
                entry.get("narrows"), asserts,
            )
        )
    return tuple(out)


def added_at(node: dict, pointer: str, keyword: str, value: object) -> dict:
    """``node`` with ``keyword`` added at ``pointer``, and nothing else moved.

    Rebuilt rather than mutated, by the same pair of functions
    (:func:`codegen.bundle.subschemas`, :func:`codegen.bundle.rebuilt`) that
    :func:`rewritten` descends and that :func:`codegen.bundle.record` inlines along, so the
    two kinds of override cannot disagree about which node a pointer names.

    The keyword lands LAST in the node's key order, which is the one latitude RFC 8259
    gives an object's members and the latitude :func:`differing` already takes over the
    canonical serialisation.
    """
    if pointer == "":
        return {**copy.deepcopy(node), keyword: copy.deepcopy(value)}
    done: dict[str, object] = {}
    for _, suffix, sub, _ in bundle.subschemas(node):
        if isinstance(sub, dict) and (pointer == suffix or pointer.startswith(f"{suffix}/")):
            done[suffix] = added_at(sub, pointer[len(suffix) :], keyword, value)
    descended = {keyword_ for keyword_, _, _, _ in bundle.subschemas(node)}
    return {
        key: bundle.rebuilt(key, value_, done) if key in descended else copy.deepcopy(value_)
        for key, value_ in node.items()
    }


def _matches(node: Mapping, position: keywords.Position, held: Extraction) -> bool:
    """Does ``held``'s node account for every ACCEPTANCE keyword ``node`` states?

    Both halves are draft-07's, read through the one predicate ``record`` itself reads
    (:func:`codegen.bundle.is_an_annotation`), so there is no second list of which keyword
    decides acceptance:

    * every constraining keyword of the TARGET is already stated at the site, with the same
      value.  A target stating one the site does not would narrow the site;
    * every key of the SITE that the target does not state is an annotation.  Draft-07
      IGNORES a ``$ref``'s siblings, so a constraining key left beside one is a key the
      patched document stops asserting -- and ``_beside`` keeps it in the record, so the
      record check alone would pass over exactly that widening.

    An ANNOTATION on either side is free in both directions: the target's reaches the
    record only where the site states none, and the site's always wins.  That asymmetry is
    the one difference between the patched record and the published one, and it is
    reported rather than hidden -- see :func:`differing`.
    """
    if "$ref" in node:
        return False
    for key, value in held.subschema.items():
        if bundle.is_an_annotation(key, position):
            continue
        if key not in node or node[key] != value:
            return False
    return all(key in held.subschema or bundle.is_an_annotation(key, position) for key in node)


def rewritten(
    document: str,
    node: dict,
    extractions: Sequence[Extraction],
    pointer: str = "",
    position: keywords.Position = keywords.Position.ROOT,
) -> dict:
    """``node`` with every subschema an extraction accounts for replaced by a ``$ref``.

    The ROOT is never rewritten, at any depth: a document whose whole text became a
    reference would stop being the document the bundle publishes under that path, and no
    site this patch set extracts is a root.
    """
    done: dict[str, object] = {}
    for _, suffix, sub, at in bundle.subschemas(node):
        if not isinstance(sub, dict):
            continue
        here = f"{pointer}{suffix}"
        held = next(
            (
                e
                for e in extractions
                if (document, here) not in e.apart and _matches(sub, at, e)
            ),
            None,
        )
        if held is None:
            done[suffix] = rewritten(document, sub, extractions, here, at)
        else:
            # Every key the target does not ALREADY STATE IDENTICALLY stays at the site.
            # Dropping a key merely because the target also spells it would hand the
            # record the TARGET's value -- and a site's own ``description`` is the whole
            # reason the site is worth reading, so a rewrite that silently replaced 307
            # of them with one generic sentence would be a worse document than the one it
            # patched.  Keeping it is also what ``_beside`` expects: an annotation
            # sibling's value wins, so the site's text comes back out of the record.
            rest = {
                key: copy.deepcopy(value)
                for key, value in sub.items()
                if key not in held.subschema or held.subschema[key] != value
            }
            done[suffix] = {"$ref": held.uri, **rest}
    descended = {keyword for keyword, _, _, _ in bundle.subschemas(node)}
    return {
        key: bundle.rebuilt(key, value, done) if key in descended else copy.deepcopy(value)
        for key, value in node.items()
    }


def sites(published: Path, extractions: Sequence[Extraction]) -> list[tuple[str, str, str]]:
    """Every ``(document, pointer, uri)`` the patch turns into a reference, sorted.

    A function of the published bundle and the manifest, which is what makes the patch a
    handful of files rather than an 800-line list of pointers: the sites are DERIVED by the
    same match that rewrites them, so the manifest cannot name a site the rewrite misses or
    miss one it rewrites.
    """
    out = []
    for document in bundle.portable(published):
        doc = bundle.read(published, document)
        after_doc = rewritten(document, doc, extractions)
        for pointer, before in bundle.nodes(doc):
            after = bundle.node_at(after_doc, pointer)
            if isinstance(after, dict) and after.get("$ref") != before.get("$ref"):
                out.append((document, pointer, after["$ref"]))
    return sorted(out)


def stale(published: Path, extractions: Sequence[Extraction]) -> list[tuple[str, str]]:
    """Exclusions naming a site the shape no longer matches, sorted.

    A stale exclusion is the one way this manifest can rot silently: the day the site it
    names loses the shape, the entry stops excluding anything, and the next site to GAIN
    the shape at that pointer is rewritten with no one having looked at what it means.
    So the check asks for exactly what the exclusion claims -- that there IS a
    shape-matching site here and that it means something else.
    """
    out = []
    for held in extractions:
        bare = Extraction(held.document, held.pointer, held.uri, held.subschema, frozenset())
        for document, pointer in sorted(held.apart):
            doc = bundle.read(published, document) if (published / document).is_file() else None
            node = None if doc is None else bundle.node_at(doc, pointer)
            at = _position_of(doc, pointer) if isinstance(node, dict) else None
            if at is None or not isinstance(node, dict) or not _matches(node, at, bare):
                out.append((document, pointer))
    return sorted(out)


def _position_of(root: dict | None, pointer: str) -> keywords.Position | None:
    """The position the node at ``pointer`` occupies, by the one descent.

    A walk and not a reading of the pointer's text: the table decides what position a
    keyword holds its subschemas at, and ``/properties/x`` spells a PROP only because the
    table's row for ``properties`` says so.
    """
    if root is None:
        return None
    found: dict[str, keywords.Position] = {"": keywords.Position.ROOT}

    def walk(node: dict, at: str) -> None:
        for _, suffix, sub, position in bundle.subschemas(node):
            if isinstance(sub, dict):
                found[f"{at}{suffix}"] = position
                walk(sub, f"{at}{suffix}")

    walk(root, "")
    return found.get(pointer)


def apply(published: Path, patch_set: Path, out: Path) -> tuple[Extraction, ...]:
    """Write the patched bundle to ``out``: every published file, rewritten, plus the new ones.

    ``bundled/`` and ``mcp/`` are copied as they stand.  They are PROJECTIONS of the
    documents this rewrites, regenerated upstream from the same sources, so patching them
    here would state a second answer to a question the published bundle answers once --
    and nothing reads them (``bundle.portable`` excludes them, which is the population the
    record check ranges over).

    **The ADDITIONS land after the rewrite**, on the node the rewrite left at that pointer.
    Both orders are defensible and this one is checkable: a keyword added before the
    rewrite would be a sibling the match reads as an annotation, so the entry that asked for
    it would silently decide whether its own site still matched an extraction.

    **A DOCUMENT THE PATCH DOES NOT REWRITE KEEPS THE PUBLISHED BYTES, and the write is
    skipped rather than made identical.**  ``copytree`` above has already put the published
    file there, so a document the rewrite and the additions both leave alone is already
    correct on disk and re-serialising it can only change it.  Measured over the BUILD's
    1,625 files before this line existed: 571 identical (``bundled/`` and ``mcp/``, which
    this loop never visits), **854 differing by a trailing newline alone** -- re-serialised,
    semantically untouched -- and 200 differing in content.

    **AND THE TRAILING NEWLINE WAS NOT COSMETIC**, which is the whole reason this is a
    decision and not a tidy-up.  ``bundle.source_identities`` digests a document's own RAW
    BYTES and its reference closure's, so each of those 854 moved its own key and dragged
    every referrer's with it: source identity moved for 1,054 of 1,054 documents, every
    accepts-corpus entry in the repository missed, and the whole graded population drew cold
    -- for one byte of whitespace in documents the patch says nothing about.  With the write
    skipped the moved set is 434 of 1,054 and 873 of 2,598 graded pairs keep their committed
    floor entry.

    It is the class ``docs/plan/rebuild-plan.md`` §9 already names -- *"I re-serialised
    brand.json with json.dumps to insert one key"* -- arriving inside the build instead of
    inside a review: **edit, or copy, the text; never round-trip the parsed object for its
    own sake.**  The gate is
    ``tests/test_patch_8525.py::test_a_document_the_patch_leaves_alone_keeps_the_published_bytes``,
    which equates the set that moved by BYTES with the set that moved by CONTENT --
    ``test_the_measurement_8525_argues_from_is_reproducible`` compares parsed objects and is
    blind to this by construction.

    **AND APPLYING A SET THIS DIRECTORY ALREADY HOLDS IS REFUSED HERE, BY A MESSAGE ABOUT THE
    DOUBLE APPLICATION** (``docs/plan/architecture.md``, "AND A BUNDLE DIRECTORY MUST SAY
    WHETHER IT IS PATCHED").  This is the exact line where the defect used to raise
    :func:`load`'s *"the published bundle already holds it"* -- the EXPIRY sentence, which
    means an override's defect is gone upstream and the entry should be deleted.  The
    mechanism was right and the message was about the wrong thing, and the two readings carry
    opposite instructions.  :func:`sets_applied` makes the state a property of the VALUE, so
    the refusal arrives before :func:`load` is asked a question it would answer ambiguously.

    **THE EXPIRY REFUSAL IS NOT WEAKENED BY IT, and must not be.**  This one ranges over
    *"this set is in the record beside ``published``"* and nothing else: a set NOT in that
    record still reaches :func:`load` and :func:`additions`, which still raise where the
    published bundle already holds an extraction's document or already states an addition's
    keyword.  That is how an override retires itself when upstream fixes the schema, and it
    still fires -- against ``schemas/cache/3.3``'s ``brand.json#/definitions/
    data_subject_contestation``, which upstream's own ``9c32fa997`` titled.

    **The output carries a record of what it holds** (:func:`_a_patched_record`),
    written beside the directory and never inside it -- ``bundle.portable`` enumerates
    ``rglob("*.json")`` under the bundle root, so a record written there would be a 1,626th
    document, compiled and graded like a schema.
    """
    done = sets_applied(published)
    if done is not None and str(patch_set) in done:
        raise ValueError(
            f"{patch_set} is already applied to {published}: the record beside it says "
            f"{', '.join(done)}. This is a DOUBLE APPLICATION and NOT an expiry -- the "
            "entry's defect is not gone upstream, the table has simply been applied twice, "
            "so do not delete anything; hand the PUBLISHED bundle to one derivation "
            "(`for_build`) instead"
        )
    extractions = load(patch_set, published)
    grown = additions(patch_set, published)
    if out.exists():
        shutil.rmtree(out)
        # The record goes with the directory it describes.  A record outliving its bundle
        # would be read as a statement about whatever is written there next, which is the
        # ambiguity this whole mechanism exists to remove, one level up.
        record_path(out).unlink(missing_ok=True)
    shutil.copytree(published, out)
    for document in bundle.portable(published):
        before = bundle.read(published, document)
        doc = rewritten(document, before, extractions)
        for grows in grown:
            if grows.document == document:
                doc = added_at(doc, grows.pointer, grows.keyword, grows.value)
        if doc == before:
            continue
        (out / document).write_text(json.dumps(doc, indent=2) + "\n")
    for held in extractions:
        destination = out / held.document
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(patch_set / DOCUMENTS / held.document, destination)
    record_path(out).write_text(
        json.dumps(
            _a_patched_record(_ground_of(published), [*(done or ()), str(patch_set)]),
            indent=2,
        )
        + "\n"
    )
    return extractions


def census(published: Path, keyword: str = "pattern") -> dict[object, list[tuple[str, str]]]:
    """Every node stating ``keyword``, grouped by the value it states, over ``portable``.

    The measurement #8525 is built on, kept beside the patch it argues for so the figures
    in the issue are reproducible from the same walk the rewrite uses rather than from a
    script that no longer exists.
    """
    out: dict[object, list[tuple[str, str]]] = {}
    for document in bundle.portable(published):
        doc = bundle.read(published, document)
        for pointer, node in bundle.nodes(doc):
            if keyword in node:
                value = node[keyword]
                if isinstance(value, (str, int, float, bool)) or value is None:
                    out.setdefault(value, []).append((document, pointer))
    return out


class Difference(NamedTuple):
    """One pointer at which the published record and the patched one disagree.

    ``keys`` is what the disagreement IS ABOUT -- the keys one side states and the other
    does not, or the single key whose value changed -- and ``position`` is the position the
    node holding them occupies.  Together they are what :func:`seen_by_a_validator` reads,
    so classifying a difference needs no second list of which keyword decides acceptance.
    """

    document: str
    pointer: str
    keys: tuple[str, ...]
    position: keywords.Position | None
    detail: str

    def __str__(self) -> str:
        return f"{self.document}#{self.pointer or '/'}: {self.detail}"


def differing(published: Path, patched: Path) -> Iterator[Difference]:
    """Every pointer at which the two bundles' records disagree.

    THE ADMISSIBILITY CHECK of §1, and it is the patch's whole evidence.  Empty means the
    patch is byte-identical where it matters most: ``record`` inlines every cross-document
    reference, so resolving the patch returns the published document or this names the
    pointer at which it does not.

    Over ``bundle.portable(published)`` and never a written list (§9: a generic check does
    not hand-write the set it ranges over), so a document the patch touches and the author
    forgot cannot escape it.

    Byte-identity is taken over the CANONICAL serialisation -- object keys sorted, which is
    exactly the latitude RFC 8259 gives an object's members, and the one difference a
    rewrite is entitled to: an inlined target's keys arrive before the referring node's,
    where the published document wrote them in its own order.  Every other difference,
    including a list's order, is reported.

    **AND THE RECORD'S OWN STORAGE IS PUT BACK BEFORE THE COMPARISON**
    (:func:`codegen.bundle.expanded`), because the hoisting is NUMBERED IN WALK ORDER and a
    patch that adds a keyword at one node changes which subtrees are identical.
    ``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT": *"The
    hoisting is a storage representation and the readers dereference through it; it is not a
    renaming."*  So a comparison made THROUGH it is comparing two different nodes wherever an
    index has shifted.

    **Measured, and it is why this line exists.**  The first run of this check over an
    override table of 162 additions reported **2,648 differences** in
    ``compliance/comply-test-controller-request.json`` alone -- ``#/definitions/Shared479``
    gaining an ``enum`` and losing its ``properties``, ``Shared512`` becoming ``Shared511``
    at every referrer -- and :func:`seen_by_a_validator` was non-empty on every one of them.
    Not one was a keyword the patch moved: one more distinct subtree shifted the whole
    numbering by one, and the check compared each stored entry against its neighbour.  A
    check that reddens on a storage index is a check that cannot be read.

    KNOWN COST: :func:`codegen.bundle.record` is O(paths through the reference graph) and
    this takes 2,108 of them, which is minutes rather than seconds.  The population is the
    whole bundle and the check is the deliverable, so the cost is paid rather than sampled.
    What is NOT paid 2,108 times any more is the directory scan each one used to open with:
    the two document sets are read once below and threaded in, which is ``record``'s own
    docstring and ``docs/plan/architecture.md``'s rule.
    """
    # The two document sets, read ONCE each and threaded into every ``record`` below:
    # ``docs/plan/architecture.md``, "a set derived from the directory is also an
    # argument".  TWO of them here and not one, because this check reads two bundles and
    # a reference's head resolves against the bundle it was found in -- which is the
    # second thing threading makes visible that a cache keyed on a path would have to be
    # trusted to get right.
    in_published = set(bundle.portable(published))
    in_patched = set(bundle.portable(patched))
    for document in sorted(in_published):
        # THE EXPANSION IS BOUND TO ITS OWN NAME and does not overwrite the record's.
        # ``bundle.record`` answers ``dict | Refusal`` and ``bundle.expanded`` answers
        # ``object`` -- an HONEST return type for a generic recursive walk and not an
        # imprecision to suppress, because the walk dereferences THROUGH the storage, so
        # what comes back at a storage reference is whatever that root's own section holds,
        # and the walk carries no table of which keys hold a subschema.  Writing the
        # expansion back onto the narrowed name would claim the narrowing survived a call
        # that does not promise it.  So the record is read under ``stored_*`` -- which is
        # the form it arrives in -- the expansion is declared at the type ``expanded``
        # actually states, and the screen below is what establishes mapping-ness from here.
        # That screen is the one the rest of this loop relies on and it CAN still fail: a
        # refused record reaches it and is reported as a difference, unexpanded.
        stored_before = bundle.record(published, document, in_published)
        stored_after = bundle.record(patched, document, in_patched)
        before: object = (
            bundle.expanded(stored_before, stored_before)
            if isinstance(stored_before, Mapping)
            else stored_before
        )
        after: object = (
            bundle.expanded(stored_after, stored_after)
            if isinstance(stored_after, Mapping)
            else stored_after
        )
        if not isinstance(before, Mapping) or not isinstance(after, Mapping):
            if type(before) is not type(after) or before != after:
                yield Difference(
                    document, "", (), None,
                    f"the record is {before!r} published and {after!r} patched",
                )
            continue
        yield from _disagreements(document, "", before, after, _positions(after))


def seen_by_a_validator(found: Iterable[Difference]) -> list[Difference]:
    """Those differences a draft-07 validator can act on.

    The ACCEPTANCE half of the check, and it reads the same predicate ``record`` reads to
    decide a ``$ref``'s sibling (:func:`codegen.bundle.is_an_annotation`): a difference
    confined to keys whose cell compiles to no type, no field and no rule is a difference
    in what the document SAYS ABOUT ITSELF, and a difference at any other key is a
    difference in what it accepts.

    A patch leaving this empty has not forked the protocol.  It is strictly weaker than
    §1's byte-identity and is NOT a substitute for it -- both are reported, because which
    of the two is the admissibility line is a decision for the plan and not for its
    implementation.
    """
    return [
        d
        for d in found
        if d.position is None
        or not d.keys
        or any(not bundle.is_an_annotation(key, d.position) for key in d.keys)
    ]


def _positions(root: Mapping) -> dict[str, keywords.Position]:
    """Every pointer of ``root`` that holds a subschema, and the position it holds it at."""
    found: dict[str, keywords.Position] = {"": keywords.Position.ROOT}

    def walk(node: Mapping, at: str) -> None:
        for _, suffix, sub, position in bundle.subschemas(node):
            if isinstance(sub, dict):
                found[f"{at}{suffix}"] = position
                walk(sub, f"{at}{suffix}")

    walk(root, "")
    return found


def _canonical(node: object) -> str:
    return json.dumps(node, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _disagreements(
    document: str,
    pointer: str,
    before: object,
    after: object,
    at: Mapping[str, keywords.Position],
) -> Iterator[Difference]:
    """The deepest pointers at which two records disagree, and what differs there.

    A whole-record byte compare answers the question, and answers it as one unreadable
    diff; this walks into the mappings that agree on their key set so the failure names a
    POINTER, which is what a reviewer who does not trust us needs in order to check one.
    """
    if _canonical(before) == _canonical(after):
        return
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        gained, lost = sorted(set(after) - set(before)), sorted(set(before) - set(after))
        if gained or lost:
            yield Difference(
                document,
                pointer,
                tuple(gained + lost),
                at.get(pointer),
                f"the patched node gains {gained} and loses {lost}",
            )
        # The SHARED keys are compared whether or not the key sets agreed.  Returning on
        # a key-set difference is how a changed VALUE hides behind an added key: the
        # rewrite that dropped a site's own ``description`` and let the target's stand in
        # its place reported here as a gain of ``$schema`` and ``title``, and the
        # substituted sentence was never looked at.
        for key in before.keys() & after.keys():
            yield from _disagreements(
                document, f"{pointer}/{bundle.escape_key(key)}", before[key], after[key], at
            )
        return
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        for index, (one, other) in enumerate(zip(before, after, strict=True)):
            yield from _disagreements(document, f"{pointer}/{index}", one, other, at)
        return
    head, _, key = pointer.rpartition("/")
    yield Difference(
        document,
        pointer,
        (bundle.unescape_key(key),),
        at.get(head),
        f"{_canonical(before)} becomes {_canonical(after)}",
    )


def added(published: Path, patched: Path) -> list[str]:
    """The documents the patched bundle holds and the published one does not."""
    return sorted(set(bundle.portable(patched)) - set(bundle.portable(published)))


def removed(published: Path, patched: Path) -> list[str]:
    """The documents the published bundle holds and the patched one does not."""
    return sorted(set(bundle.portable(published)) - set(bundle.portable(patched)))


def report(published: Path, extractions: Collection[Extraction]) -> str:
    """One line per extraction: how many sites it takes, over how many documents."""
    found = sites(published, tuple(extractions))
    lines = []
    for held in extractions:
        mine = [s for s in found if s[2] == held.uri]
        lines.append(
            f"{len(mine):4d} sites  {len({d for d, _, _ in mine}):3d} docs  "
            f"{held.document}#{held.pointer}  {_canonical(held.subschema)}"
        )
    return "\n".join(lines)
