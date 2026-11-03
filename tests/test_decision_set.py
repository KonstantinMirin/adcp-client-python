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

**WHAT IS VACUOUS AND WHAT IS NOT, said plainly rather than left to a reader.**  Three of
the assertions below range over an empty set today and three do not, and the division is
stated at each one:

* ``unadmitted`` over the whole graded population is a MEASUREMENT.  It ranges over every
  pair the suite grades, it is empty because the run takes no narrowing, and it is the
  direction that reddens when one appears.  Not vacuous.
* ``unused`` is vacuous: the registry is empty, so no entry can fail to be used.  Stated,
  and it is what stops an entry outliving its defect.
* the MECHANISM is graded by injection, which is the only way an empty registry's
  behaviour can be read at all.  Not vacuous: it asserts that an entry admits that fact
  and NOT its kind, which is the sentence the whole registry rests on.
* both directions of the upstream half are vacuous, because there are zero ``upstream``
  attributions.  That is asserted rather than assumed -- the count comes off the artifact's
  own declarations -- so "vacuous" is itself a measurement here and stops being true the
  moment an attribution is filed.

**Nothing here asserts a code shape.**  Both registries are read through the functions
their own modules expose, both right-hand sides come off graded reports or off emitted
declarations, and no assertion names a module, a line or an import.
"""

from __future__ import annotations

import json
from pathlib import Path

from cells import grade, live  # §5's table, graded one cell at a time
from compiled import compiled  # the run's own declarations

from codegen import attribution, bundle, narrowings
from codegen.attribution import Issue
from codegen.keywords import Position
from codegen.narrowings import ADMITTED, Narrowing, Taken
from tests.nodeset import claimed

BUNDLE = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"


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
        f"{one.keyword}@{one.position.name}: {one.detail}"
        for one in narrowings.unadmitted(taken)
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
    taken = Taken(
        "uniqueItems", Position.PROP, ["https://A.com", "https://a.com"], "refused"
    )
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
    reworded = Narrowing(
        taken.keyword, taken.position, entry.value, "a different sentence"
    )
    assert narrowings.admits(taken, (reworded,)) is reworded


def test_every_upstream_attribution_names_an_issue_that_exists() -> None:
    """**Reading 9's first clause, and it is VACUOUS TODAY.**

    Three statements, and the third is what makes the first two readable:

    * no ``upstream`` attribution lacks a recorded verification that its issue exists;
    * no verified issue goes unnamed by an attribution, so the record cannot become a list
      of issues doing nothing;
    * **the set is EMPTY**, measured off the artifact's own declarations rather than
      asserted about the registry -- every declared fact a run mints reads as ``ours``,
      because an unfiled gap is ours.

    So this gate passes because its set is empty, and that is stated here rather than left
    for someone to discover.  It stops being vacuous on the day an attribution is filed:
    the first statement then has a reference to check, and an attribution arriving without
    its verification reddens in the same diff.

    **One upstream issue exists and attributes nothing.**
    `adcontextprotocol/adcp#8698 <https://github.com/adcontextprotocol/adcp/issues/8698>`_
    is a question and not a verdict, so no site is attributed to it and nothing records it
    -- an entry for it would be the second statement's own failure.

    Existence cannot be derived offline and this file has no network, so what is checked is
    that somebody looked and wrote down what they saw.  ``codegen/attribution.py`` carries
    the reasoning for that being a registry compared in both directions rather than a list.
    """
    assert attribution.unverified() == (), attribution.unverified()
    assert attribution.unnamed() == (), attribution.unnamed()
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
        {
            (one.document, one.pointer, one.keyword)
            for facts in out.approximations.values()
            for one in facts
        },
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
    """The upstream half's mechanism, by injection, for the reason the narrowing half is.

    With zero upstream attributions neither direction above can fail, so the two functions
    are put to registries built here: a site whose issue is not recorded is reported, the
    same site with its issue recorded is not, and a recorded issue no site names is
    reported by the other direction.  A reference that merely LOOKS right is not enough --
    which is the whole difference between this gate and ``Issue.__post_init__``, where a
    non-empty string is all a reference has to be.
    """
    site = ("core/x.json", "#/properties/a", "patternProperties")
    issue = Issue("adcontextprotocol/adcp#1", "the document cannot state this")
    registry = {site: issue}
    assert attribution.unverified(registry, {}) == ((site, issue.reference),)
    assert attribution.unverified(registry, {issue.reference: "seen 2026-11-03"}) == ()
    assert attribution.unnamed(registry, {issue.reference: "seen"}) == ()
    assert attribution.unnamed({}, {issue.reference: "seen"}) == (issue.reference,)
