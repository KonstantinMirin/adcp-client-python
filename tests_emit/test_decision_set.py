"""The two registries reading 9 names, each compared against a measurement.

``docs/plan/final-state.md`` reading 9:

    Each declared fact is ours with a decision recorded, or upstream with an issue that
    exists.  An unfiled gap is ours.  And every narrowing taken deliberately is admitted by
    an enumerated registry compared by equality against the narrowings the run actually
    takes -- admitted by nothing else, because a predicate waiver is invisible and
    permanent.

    **Decided by** every ``upstream`` attribution naming a live issue, and by that
    registry's equality in both directions.

``docs/plan/rebuild-plan.md`` section 2 names this file as the holder of the second half:
"``tests/decision_set.py`` holds the guard, with both sides of every pin derived."  It did
not exist, and the registry it was to guard -- ``harness.URL_IMPLIED`` -- had 0 references
repo-wide, so the clause was false where it mattered most: a narrowing was LIVE and nothing
admitted it (``adcp-client-python-82m.19``).

**WHY THIS FILE COMES AFTER THE WITHDRAWAL AND NOT BEFORE IT.**  Section 2: "the order is
forced and it is two commits.  The withdrawal lands first and moves the emitted tree; the
registry lands second, EMPTY, with its equality in both directions.  Registry-first cannot
be done: this section already says a normalisation cannot be registered, because an entry is
compared by equality so that it admits one fact and not its kind -- so a registry-first
commit would land a gate whose only green path is the withdrawal, which is a marker by
another name."  So this file is green from the start, and what it does is make the withdrawal
STAY withdrawn: a URL type returning anywhere brings its narrowings back, and they arrive
here with no entry to admit them.

**WHAT IS VACUOUS AND WHAT IS NOT, said plainly rather than left to a reader**, and the
division moved on 2026-11-05 because the upstream half was vacuous in BOTH directions and
no longer is:

* ``unadmitted`` over the whole graded population is a MEASUREMENT.  It ranges over every
  pair the suite grades, it is empty because the run takes no narrowing, and it is the
  direction that reddens when one appears.  Not vacuous.
* ``unused`` is vacuous: the registry is empty, so no entry can fail to be used.  Stated,
  and it is what stops an entry outliving its defect.
* the MECHANISM is graded by injection, which is the only way an empty registry's
  behaviour can be read at all.  Not vacuous: it asserts that an entry admits that fact
  and NOT its kind, which is the sentence the whole registry rests on.
* the SITE-LEVEL upstream half is vacuous, because there are zero ``upstream``
  attributions.  That is asserted rather than assumed -- the count comes off the artifact's
  own declarations -- so "vacuous" is itself a measurement here and stops being true the
  moment an attribution is filed.
* **the CITATION-LEVEL upstream half is not vacuous and is the change.**  Reading 9's
  existence clause was decided over :data:`attribution.REGISTRY` alone, which is empty, so
  it was a gate with nothing in it -- while the repository cited NINE upstream references
  elsewhere, including one in a generated module that ships in the wheel, and one that
  does not exist.  The population is now every reference the repository cites, measured
  off ``git ls-files``, and :data:`attribution.VERIFIED` is compared against it in both
  directions.

**Nothing here asserts a code shape.**  Both registries are read through the functions
their own modules expose, every right-hand side comes off graded reports, off emitted
declarations or off the repository's own file list, and no assertion names a module, a line
or an import.

**SHOWN RED.**  ``perturb_the_attribution.sh`` is the banked evidence for the upstream
half: it plants an attribution naming a non-existent issue, plants a sighting of one,
removes a sighting a citation needs, adds one nothing cites, and writes a citation of ours
into an emitted record where the exclusion would hide it.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import fresh
import pytest
from cells import grade, live  # §5's table, graded one cell at a time
from compiled import compiled  # the run's own declarations

from codegen import attribution, bundle, narrowings
from codegen.attribution import Issue, Sighting
from codegen.keywords import Position
from codegen.narrowings import ADMITTED, Narrowing, Taken
from codegen.refusal import BuildFailure
from tests.nodeset import claimed

ROOT = Path(__file__).resolve().parents[1]
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE


def _taken() -> list[Taken]:
    """**The narrowings the run actually takes**, off §5's TABLE and one cell at a time.

    ``cells.grade``'s ``narrowed`` is exactly this registry's fact, in §2's own words: "A
    value the document ADMITS and the class refuses is a NARROWING, which §2 forbids
    outright".  One ``Taken`` per such row, carrying the cell it was found at and the
    grader's OWN spelling of the instance it offered.

    **THIS SIDE USED TO BE THE DRAW AND IT DID NOT COMPLETE**, which is the whole of why
    the index moved (``codegen/narrowings.py``'s ``_Site``).  It read
    ``test_emit.graded_reports`` -- every pair of a class and its document -- measured at
    2h21m of CPU at 20.3 GB without finishing, so reading 9's equality was CUT, and reading
    9 is the clause that forbids a cut standing in for an answer.  §5's table is a
    **289-member enumeration** whose cost is a function of the keyword rather than of any
    document, so the equality completes and covers the 86 pairs no draw reaches.

    The RIGHT-HAND SIDE OF THE EQUALITY IS STILL A MEASUREMENT and is not written down
    anywhere: it is whatever grading every live cell reported.  An entry in the registry is
    written by copying a line from here, which is also why the value is the grader's
    spelling and not a second rendering of it.
    """
    out: list[Taken] = []
    for keyword, position in sorted(live(), key=lambda c: (c[0], c[1].name)):
        verdicts = grade(keyword, position)
        out += [
            Taken(keyword, position, json.loads(instance), detail)
            for instance, by_document, by_class in verdicts.narrowed
            for detail in (
                f"{keyword} at {position.name}: the document admits {instance} "
                f"(document={by_document}, class={by_class}) and the class refuses it",
            )
        ]
    return out


def test_no_narrowing_the_run_takes_is_unadmitted() -> None:
    """**The direction that is a measurement**, over every live cell of §5's table.

    Section 2: "an annotation tighter than its document refuses a payload the protocol
    permits, and ``strict_validate`` cannot repair it: the schema half admits the payload
    and the construction then fails.  A narrowing is the defect the old sentence was
    reaching for, and nothing below widens into one."  So a narrowing the registry does not
    admit is a defect, by name and by value.

    **NOT VACUOUS, AND NOT CUT.**  The population is named non-empty first -- a pass over
    no cells would be the exact failure mode this file exists against -- and the assertion
    is over the narrowings those cells reported.  It is green because the run takes none,
    which is the withdrawal's own consequence: the three ``uniqueItems`` sites and the two
    rewritten dumps ``adcp-client-python-82m.19`` measured are gone, and
    ``tests/test_the_value_is_the_documents_own.py`` holds their payloads.
    """
    cells = claimed("§5's live cells", {f"{k}@{p.name}" for k, p in live()})
    assert cells  # named above; restated so the denominator is visible at the assertion
    taken = _taken()
    assert narrowings.unadmitted(taken) == (), [
        f"{one.keyword}@{one.position.name}: {one.detail}" for one in narrowings.unadmitted(taken)
    ]


def test_no_entry_admits_a_narrowing_the_run_does_not_take() -> None:
    """The other direction: an entry nothing needs is an allowlist wearing a measurement.

    **VACUOUS TODAY, and that is said rather than hidden**: :data:`ADMITTED` is empty, so
    there is no entry that could fail to be used, and this assertion cannot fail until one
    is written.  It is here because of what it does on that day -- an entry whose narrowing
    was repaired stops being used and takes its own line out with it, which is the mechanism
    every other registry in this build relies on to shrink without anybody watching.

    The emptiness is asserted BESIDE the direction, so a reader of a green run knows which
    of the two facts they are looking at.
    """
    assert ADMITTED == (), ADMITTED
    assert narrowings.unused(_taken()) == ()


def test_an_entry_admits_that_fact_and_not_its_kind() -> None:
    """**The mechanism, exercised by injection, which is the sentence the registry rests on.**

    Section 2: "each entry is compared by equality so it admits that fact and not its kind
    -- a rule admitting 'the sort of bound a URL type adds' would be invisible and
    permanent."  An empty registry cannot show that by passing, so the admission is put to
    four entries built here:

    * the entry EQUAL to the narrowing admits it;
    * an entry at another CELL does not, so an admission cannot spread from one keyword to
      another or from one position to another;
    * an entry with another VALUE does not, which is the half that makes an entry a fact:
      "a URI whose host differs only in case" is a kind, has no value to state, and
      therefore cannot be written here at all;
    * the ``decision`` is NOT compared, so an entry whose reasoning was reworded goes on
      admitting the narrowing it was written for rather than reddening the pair with the
      wrong explanation.  The ``keyword`` IS compared now that it is half the cell, which
      is the re-indexing's one visible consequence here.

    This is also the REACH reading section 2 asks for -- "the guard switches each admission
    mechanism off in turn and pins which keywords reappear."  There is one mechanism and it
    is this function; switched off, the narrowing below is unadmitted, which is what the
    first and last assertions are.
    """
    taken = Taken("uniqueItems", Position.PROP, ["https://A.com", "https://a.com"], "refused")
    entry = Narrowing(
        keyword=taken.keyword,
        position=taken.position,
        value=["https://A.com", "https://a.com"],
        decision="a decision that does not exist, written here to exercise the door",
    )
    assert narrowings.unadmitted([taken], ()) == (taken,)
    assert narrowings.admits(taken, (entry,)) is entry
    assert narrowings.unadmitted([taken], (entry,)) == ()
    elsewhere = [
        Narrowing(taken.keyword, Position.ELEM, entry.value, entry.decision),
        Narrowing(taken.keyword, taken.position, ["https://a.com"], entry.decision),
        Narrowing("minLength", taken.position, entry.value, entry.decision),
    ]
    for other in elsewhere:
        assert narrowings.admits(taken, (other,)) is None, other
        assert narrowings.unadmitted([taken], (other,)) == (taken,), other
        assert narrowings.unused([taken], (other,)) == (other,), other
    reworded = Narrowing(taken.keyword, taken.position, entry.value, "a different sentence")
    assert narrowings.admits(taken, (reworded,)) is reworded


def test_every_upstream_attribution_names_an_issue_that_exists() -> None:
    """**Reading 9's first clause AT THE SITE LEVEL, and it is VACUOUS TODAY.**

    Two statements, and the second is what makes the first readable:

    * no ``upstream`` attribution lacks a recorded sighting that its issue exists;
    * **the set is EMPTY**, measured off the artifact's own declarations rather than
      asserted about the registry -- every declared fact a run mints reads as ``ours``,
      because an unfiled gap is ours.

    So this gate passes because its set is empty, and that is stated here rather than left
    for someone to discover.  It stops being vacuous on the day an attribution is filed:
    the first statement then has a reference to check, and an attribution arriving without
    its sighting reddens in the same diff.

    **AND THE SITE LEVEL IS NOT THE WHOLE OF READING 9's CLAUSE**, which is why the test
    below exists: an attribution is one way for this repository to rest a sentence on
    somebody else's backlog, and ``codegen/catalogue.py``,
    ``codegen/dump_exemptions.py`` and ``src/adcp/types/envelopes.py`` -- which ships in
    the wheel -- do it another way.  Keeping this gate's population at :data:`REGISTRY`
    alone is how the existence clause came to be answered by an empty set while the
    repository cited nine upstream references, one of which did not exist.

    Existence cannot be derived offline and this file has no network, so what is checked is
    that somebody looked and wrote down what they saw.  ``codegen/attribution.py`` carries
    the reasoning for that being a registry compared in both directions rather than a list,
    and ``survey/upstream_issues.py`` is what makes the looking reproducible.
    """
    assert attribution.unverified() == (), attribution.unverified()
    # The VACUITY, measured off the artifact the run wrote rather than off the registry:
    # a declaration is attributed UPSTREAM exactly when the registry holds its site, so
    # the upstream half of the split is the sites ``issue_for`` answers for.  The declared
    # set is named first, so "none of them is upstream" is a statement about the facts the
    # run mints and not about an empty walk.
    #
    # **Read off the RUN's own approximations and not off the graded pairs**, for
    # ``_taken``'s reason: a reading per pair is the draw, and the draw does not complete.
    # ``Emitted.approximations`` IS the declared set -- it is what ``./check``'s third line
    # counts -- so this is the artifact's own record read directly.
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    declared = claimed(
        "declared facts the artifact carries",
        {(one.document, one.pointer, one.keyword) for facts in out.approximations.values() for one in facts},
    )
    upstream = [site for site in declared if attribution.issue_for(*site) is not None]
    # **STATED, NOT MERELY GREEN** (reading 9, and §8's rule that a cut is reported as a
    # cut): both directions of this half range over an empty set today, and the words are
    # here so a reader of a green run knows that is what they are looking at.  There are
    # ZERO upstream attributions over the whole declared set, so ``unverified`` and
    # ``unnamed`` above are VACUOUS and this line is the measurement that says so.
    assert upstream == [], upstream
    assert len(upstream) == 0, "the upstream half is VACUOUS: zero upstream attributions"


def test_an_attribution_whose_issue_is_unverified_is_reported() -> None:
    """The site-level half's mechanism, by injection, for the reason the narrowing half is.

    With zero upstream attributions :func:`attribution.unverified` cannot fail over
    :data:`REGISTRY`, so it is put to a registry built here: a site whose issue is not
    recorded is reported, and the same site with its issue recorded is not.  A reference
    that merely LOOKS right is not enough -- which is the whole difference between this
    gate and ``Issue.__post_init__``, where a non-empty string is all a reference has to be.

    **The fixture's reference does NOT name a real tracker, and that is a rule rather than
    a style.**  It used to be issue number ONE of ``adcontextprotocol/adcp`` -- here and at
    two sites in ``tests/test_approximation.py`` -- meaning "a well-formed spelling".  That
    issue DOES NOT EXIST: ``gh issue view 1 --repo adcontextprotocol/adcp`` answers "Could
    not resolve to an issue or pull request".  So the repository cited a non-existent
    upstream issue in three places, which is exactly what reading 9 forbids, and the
    citation census below is what found it.

    The number is named apart from the repository in this docstring on purpose: the census
    matches the spelling a CITATION uses, and prose that spells out the reference it is
    explaining gets reported as the citation it is about.
    """
    site = ("core/x.json", "#/properties/a", "patternProperties")
    issue = Issue("example/schema#1", "the document cannot state this")
    registry = {site: issue}
    sighting = Sighting(issue.reference, "OPEN", "a fixture, not a claim", "2026-11-05")
    assert attribution.unverified(registry, {}) == ((site, issue.reference),)
    assert attribution.unverified(registry, {issue.reference: sighting}) == ()


#: **Where a reference this repository cites can be found**, as a regular expression over
#: the spellings a citation actually uses.  ``#8472`` is the form ``codegen/attribution.py``
#: documents; the issue and pull URLs are the form a docstring uses when it wants to be
#: clickable, and both reach the same tracker.
CITATION = re.compile(r"adcontextprotocol/adcp(?:#|/(?:issues|pull)/)(\d+)")

#: **The trees whose text is UPSTREAM's and not ours**, so a reference in them is upstream
#: citing upstream and no claim of this repository's.
#:
#: ``schemas/cache/`` is the bundle.  ``src/adcp/types/_schemas/`` is the same documents
#: carried through the emitter -- the records, and the generated modules whose docstrings
#: are the documents' own ``description``s.  **There is no third tree, and ``patches/`` was
#: wrongly in this list once**: its payload documents are bundle-shaped, but its
#: ``manifest.json`` and ``judgment.json`` are OURS and name the very issues the patch set
#: addresses -- #8398, #8525 and #8735, none of which the bundle cites.  The check below is
#: what caught that, which is the whole reason the exclusion is measured.
#:
#: **THE EXCLUSION IS CHECKED AND IS NOT TAKEN ON TRUST**, which is what stops it being an
#: allowlist.  The bundle is the AUTHORITY for what upstream's own text says, and the other
#: two trees are DERIVED from it -- the records by the emitter, the patch payloads by hand
#: from a bundle document -- so
#: :func:`test_every_upstream_reference_this_repository_cites_has_a_sighting` requires every
#: reference the records cite to appear in the bundle as well.  A reference of OURS written
#: into a record is then not hidden: it is reported, because the bundle does not state it.
#: Measured: eight references appear only in this text (2511, 3075, 3078, 3666, 3823, 3844,
#: 3961, 7440) and three appear in both halves.
BUNDLE_TEXT = "schemas/cache/"
DERIVED_TEXT = ("src/adcp/types/_schemas/",)
CARRIED = (BUNDLE_TEXT, *DERIVED_TEXT)

#: **The module that DECLARES the registry, which is not a citation of anything.**
#:
#: A sighting's entry spells its own reference twice -- the key and the ``reference`` field
#: -- so a census that reads this module finds every sighting citing itself, and the
#: BACKWARD direction can never fail: an entry nobody needs certifies its own necessity.
#: Measured: it did.  ``perturb_the_attribution.sh``'s "a sighting no sentence of ours
#: cites" case printed STAYED GREEN for exactly that reason, and it had looked red earlier
#: only because the script was spelling a second, unsighted reference beside it.
#:
#: So the registry's own module is out of the population: it RECORDS citations and makes
#: none.  Derived from the module object rather than written as a path, so the two cannot
#: come apart if the file moves.
#:
#: **AND THE MODULE'S OWN SENTENCE ABOUT #8698 IS WHY THIS IS THE RIGHT RULE RATHER THAN A
#: CONVENIENCE.**  Its docstring already said: "One upstream issue exists and is
#: deliberately NOT here: [issue 8698] attributes nothing, because it is a question and not
#: a verdict -- and an entry for it would be exactly the backward-direction defect above."
#: A census that read the module counted that very sentence as a claim and gave the issue a
#: sighting, which is the defect the sentence describes.  With the module out, nothing else
#: cites it and the registry does not hold it.
#:
#: The number is written in brackets rather than as a reference, for the reason the
#: docstrings in this file already give twice: prose that spells out the citation it is
#: explaining gets reported as the citation.
REGISTRY_MODULE = str(Path(attribution.__file__).resolve().relative_to(ROOT))


def _cited() -> dict[str, list[str]]:
    """Every upstream reference this repository CITES, and the files that cite it.

    ``git ls-files`` and not a glob: the population is what the repository COMMITS, so an
    untracked note of somebody's cannot add a claim and a build leftover cannot either --
    the same reason ``tests/test_the_wheel_is_the_artifact.py`` compares the wheel against
    ``git ls-files src/``, and the same failure the bd memory on an untracked file records.
    """
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.split("\n")
    out: dict[str, list[str]] = {}
    for name in files:
        if not name or name.startswith(CARRIED) or name == REGISTRY_MODULE:
            continue
        try:
            text = (ROOT / name).read_text(errors="ignore")
        except OSError:
            continue
        for number in sorted(set(CITATION.findall(text))):
            out.setdefault(f"adcontextprotocol/adcp#{number}", []).append(name)
    return out


def _carried(under: tuple[str, ...] | str) -> set[str]:
    """Every upstream reference the files ``under`` cite -- upstream citing itself."""
    out: set[str] = set()
    for name in subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.split(
        "\n"
    ):
        if not name or not name.startswith(under):
            continue
        try:
            text = (ROOT / name).read_text(errors="ignore")
        except OSError:
            continue
        out |= {f"adcontextprotocol/adcp#{n}" for n in CITATION.findall(text)}
    return out


def test_every_upstream_reference_this_repository_cites_has_a_sighting() -> None:
    """**Reading 9's existence clause over the whole population, and it is NOT vacuous.**

    "Each declared fact is ours with a decision recorded, or upstream with an issue that
    exists", decided by "every ``upstream`` attribution naming a live issue, and by that
    registry's equality in both directions".  An attribution is one way this repository
    rests a sentence on upstream's backlog; the census above finds every way.

    Four readings:

    * **forward** -- a reference the repository CLAIMS with no recorded sighting is a claim
      nobody has checked.  "Claims" is the census plus the references
      :data:`attribution.REGISTRY`'s own entries name: the registry's MODULE is out of the
      census because a sighting spells its own reference, and an attribution is a claim, so
      the entries go back in programmatically;
    * **backward** -- a sighting no citation names is a list of issues doing nothing, which
      is what keeps the registry from growing into an allowlist;
    * **no sighting records an ABSENT issue**, which is reading 9's own word "exists".  This
      is the one that was RED when it was first run: issue number ONE of the
      ``adcontextprotocol/adcp`` tracker was cited
      three times as an injected fixture and does not exist;
    * **the exclusion is a measurement** -- every reference :data:`CARRIED` hides appears in
      the bundle, so the rule hides upstream's own citations and nothing else.

    Both populations are named through ``tests/nodeset.py``'s ``claimed``, so a census that
    selected nothing fails rather than passing.
    """
    # **AN ATTRIBUTION IS A CLAIM AND IS ADDED BACK PROGRAMMATICALLY**, which is the other
    # half of excluding the registry's own module (:data:`REGISTRY_MODULE`).  The module's
    # TEXT makes no citation -- a sighting spells its own reference and would certify
    # itself -- but an ENTRY of :data:`attribution.REGISTRY` is exactly the kind of claim
    # reading 9 names.  Read off the entries and not off the file, so the sightings cannot
    # come back in beside them.
    cited = claimed(
        "upstream references this repository claims",
        set(_cited()) | {entry.reference for entry in attribution.REGISTRY.values()},
    )
    sighted = claimed("references with a recorded sighting", attribution.VERIFIED)
    assert attribution.unsighted(cited) == (), (
        "this repository cites an upstream issue that nobody has looked up: "
        + ", ".join(
            f"{ref} ({', '.join(_cited().get(ref, ['an attribution in the registry']))})"
            for ref in attribution.unsighted(cited)
        )
        + ". Run survey/upstream_issues.py and record what it finds."
    )
    assert attribution.unnamed(cited) == (), (
        f"{list(attribution.unnamed(cited))} have a recorded sighting and no sentence in "
        "this repository cites them: a sighting holds what a citation needs and nothing "
        "else, so an entry leaves when the last citation does"
    )
    assert attribution.absent() == (), (
        f"{list(attribution.absent())} are cited by this repository and DO NOT EXIST "
        "upstream, which is reading 9's own clause: an attribution is ours until an issue "
        "exists, and a reference to nothing is not an attribution at all"
    )
    assert sighted <= cited, sorted(sighted - cited)
    # **THE EXCLUSION, measured.**  The bundle is the authority for upstream's own text and
    # the other two trees are derived from it, so a reference they cite and the bundle does
    # not is not upstream's citation -- it is ours, written where this rule would hide it.
    authored = claimed("references the bundle itself cites", _carried(BUNDLE_TEXT))
    derived = claimed("references the emitted records cite", _carried(DERIVED_TEXT))
    assert derived <= authored, (
        f"{sorted(derived - authored)} are cited by an emitted record and NOT by the "
        "bundle, so CARRIED would hide a citation of ours rather than upstream's own"
    )


def test_no_upstream_attribution_rests_on_an_issue_upstream_has_closed() -> None:
    """**Reading 9's decided-by says a LIVE issue, and closed is not the same as absent.**

    An issue upstream has settled still EXISTS, so reading 9's first clause -- "upstream
    with an issue that exists" -- is satisfied by one, and :func:`attribution.absent` above
    is the gate for the clause it is not.  What a closed issue cannot carry is an
    ATTRIBUTION: an attribution says "the document does not state this fact and here is the
    open ask that would make it", and upstream closing the ask takes that sentence's reason
    away while leaving the widening in place.  So the rule is about the attributions and not
    about every sentence that mentions a number.

    **AND IT IS DELIBERATELY NOT A RULE ABOUT WHICH FILE CITES ONE**, which was tried and
    was wrong in the way this repository already has a name for.  A path rule ("code may not
    cite a closed issue") reddened on ``codegen/attribution.py`` and on this very file --
    because the SIGHTING that records #7959 as closed names it, and so does the sentence
    explaining that it is closed.  That is the same failure as a suppression detector
    matching the prose that explains why a suppression is absent: the explanation gets
    reported as the thing it forbids.

    **VACUOUS TODAY and said so**: :data:`REGISTRY` is empty, so no attribution can name
    anything.  The mechanism is therefore put to a registry built here, and the MEASUREMENT
    beside it is not vacuous -- one sighting records a closed issue
    (``adcontextprotocol/adcp#7959``, a 3.1.x backport ask, cited once in
    ``docs/schema-patterns-brief.md``), which is what makes "no attribution names a closed
    issue" a statement about a real closed set rather than about an empty one.
    """
    shut = claimed("sightings recording a closed issue", attribution.closed())
    attributed = {entry.reference for entry in attribution.REGISTRY.values()}
    assert attributed & shut == set(), (
        f"{sorted(attributed & shut)} carry an attribution and upstream has CLOSED them: "
        "the ask that was the attribution's reason is settled, so either the fact is now "
        "stated and the widening goes, or the widening is OURS and needs its own sentence"
    )
    assert attributed == set(), "VACUOUS: zero upstream attributions, so nothing to clash"
    # The mechanism, by injection, since the population above is empty.
    site = ("core/x.json", "#", "patternProperties")
    on_closed = {site: Issue(next(iter(shut)), "the document should state this")}
    injected = {entry.reference for entry in on_closed.values()}
    assert injected & shut == {next(iter(shut))}, injected


def test_the_sighting_registry_refuses_a_record_nobody_could_have_made() -> None:
    """``Sighting`` is where "somebody looked" stops being a sentence and becomes a value.

    Four refusals, each for a record that would claim a look nobody made: a state outside
    the three a look can find, an ABSENT issue carrying a title there was none of, an
    existing issue with no title -- which is how a reader tells whether the issue is about
    what the citation claims without following the link -- and a sighting with no date,
    which cannot go stale and is therefore an assertion rather than a measurement.

    ``survey/upstream_issues.py`` is the other half: it rebuilds this registry from the
    tracker, so a hand-written entry for a number that does not exist is caught by re-running
    it rather than by believing it.
    """
    assert Sighting("a/b#1", "ABSENT", "", "2026-11-05").state == "ABSENT"
    with pytest.raises(BuildFailure, match="not one of"):
        Sighting("a/b#1", "PROBABLY", "a title", "2026-11-05")
    with pytest.raises(BuildFailure, match="claims to have seen something it did not"):
        Sighting("a/b#1", "ABSENT", "a title for an issue that does not exist", "2026-11-05")
    with pytest.raises(BuildFailure, match="with no title"):
        Sighting("a/b#1", "OPEN", "   ", "2026-11-05")
    with pytest.raises(BuildFailure, match="no date"):
        Sighting("a/b#1", "OPEN", "a title", " ")
