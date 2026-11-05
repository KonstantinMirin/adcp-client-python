"""The site-level upstream issue a widening is attributed to: one registry, a LEAF.

``docs/plan/architecture.md`` section 1 declares this module and section 3 puts it beside
``codegen/keywords.py``: "the one registry of site-level upstream issues, keyed by
document, pointer and keyword.  A second declaration module beside ``keywords.py`` and a
leaf like it, read by ``lower/`` to attribute an approximation and by ``verify/`` to
grade one.  It is a declaration and not a verifier artifact, which is why it is here and
not under ``verify/``: a keyword-level decision lives in a cell, a site-level one lives
here, and nothing else holds either."

**A cell holds what is true of a KEYWORD; this holds what is true of a SITE.**  Section 3
again, on why the ours attribution is derived and this one is not: "the attribution of a
widening the design decided is 'the row that decided it', and the cell IS that row ...
The attribution that cannot be derived is the upstream one, and it is not a keyword fact
at all -- the same keyword widens by our decision at one pointer and by an upstream
defect at another."

**It imports nothing of ``codegen/``**, which section 11 makes the point of it: "a leaf
like ``keywords.py`` and imports nothing of ``codegen/``, which is what lets both the
walk and the verifier read it without either reading the other."

**An entry with no issue reference is a build failure, not a missing field** (section 3,
which calls it "the semantics document's section 9 rule -- 'an exemption names an
upstream issue, or it is this SDK's own decision' -- made mechanical").  Two mechanisms
hold it and the first makes the second unreachable:

* :class:`Issue` cannot be CONSTRUCTED without a reference: :meth:`Issue.__post_init__`
  refuses an empty or whitespace one, so an entry with no issue is not a value this
  module can hold;
* :func:`malformed` is the registry-level reading, so a reader -- the verifier's own
  test, section 9's named grader for this -- can ask the question of the whole registry
  rather than of one entry.

*It imports ``codegen.refusal`` for ``BuildFailure``, which is the ONE sentence of section
11 this module cannot hold, and the clash is measured rather than argued.*  Sections 3 and
14 step 8 both name the class ``BuildFailure`` by name; ``tests/test_import_rule.py``'s
``MAY_RAISE`` is a committed ratchet that "may SHRINK and may not grow", so naming a
different exception here would have to grow it.  Section 11's own sentence says "imports
nothing of ``codegen/``".  The three cannot all hold, and the one that gives is section
11's wording, because its REASON survives the import exactly: "a leaf like ``keywords.py``
... which is what lets both the walk and the verifier read it without either reading the
other."  ``codegen.refusal`` imports nothing of this package at all (its own docstring:
"Nothing of this package is imported here"), it is already in section 9's permitted set
for the verifier, and it is the leaf-most module of section 11's own arrow
(``refusal <- keywords <- ir <- schema <- lower <- emit``).  So ``import
codegen.attribution`` reaches exactly one ``codegen`` module, that one, and reaches no
module of the walk --
``tests/test_import_rule.py::test_the_verifier_reaches_no_module_of_the_walk_transitively``
is what measures it.

**The registry is EMPTY, and it is not a step's exit condition any more.**  It was one:
the row that built this module widened no cell, so no widening existed to attribute --
section 14 step 8 is "the approximation, end to end, with no cell widened".  That row's
note then quoted step 10 as "the upstream issues must be filed before this step lands,
not after ... the step cannot be completed around it", and **that sentence was
WITHDRAWN** by the design owner on 2026-10-26: step 10 as it stands says the issues do
not block it, because a compiler's own completion cannot wait on a third party's issue
tracker.  The gate moved onto the WORD instead: an attribution is OURS until an issue
exists, and only an UPSTREAM one needs a live reference -- :class:`Issue` is where that
is enforced, and it raises rather than admitting a reference-less entry.  So the registry
being empty is the reading that every declared approximation is OURS, which
``python -m codegen``'s report prints as the ours/upstream split and never sums; filing an
issue reclassifies an attribution and changes no type and no emission.
``adcp-client-python-10l.22`` is the filing row and nothing waits on it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from codegen.refusal import BuildFailure


@dataclass(frozen=True)
class Issue:
    """One upstream issue, as a reference and a sentence.

    ``reference`` is how a reader REACHES the issue -- ``"adcontextprotocol/adcp#8472"``
    is the spelling the semantics document's section 6 already uses -- and ``summary``
    is what the document should state and does not.  Both are required: a reference with
    no sentence is a link a reader has to follow to learn what the widening is about, and
    section 2 wants the attribution to answer that where it is read.

    Frozen, so an entry cannot be re-pointed at another issue after import.
    """

    reference: str
    summary: str

    def __post_init__(self) -> None:
        if not self.reference.strip():
            raise BuildFailure(
                "an attribution entry names an upstream issue, or it is this SDK's own "
                "decision and belongs in the semantics document (section 9).  An entry "
                "with no reference attributes our own cost to upstream, which means "
                "waiting forever for someone else to fix it: " + repr(self.summary)
            )
        if not self.summary.strip():
            raise BuildFailure(
                "the attribution to " + repr(self.reference) + " states no summary: "
                "section 2 makes the attribution answer WHY the document does not state "
                "the fact, where it is read"
            )

    @property
    def attribution(self) -> str:
        """What an :class:`adcp.types._base.Approximation` carries for an upstream site.

        **ONE spelling, read by two halves.**  The walk writes it onto the artifact
        (``codegen.lower.approximate.attribution_for``) and the verifier recomputes it to
        check what the artifact says is what the registry holds
        (``harness.unattributed``); a second format string is how the two come to disagree
        about a declaration that is correct.
        """
        return ": ".join((self.reference, self.summary))


#: A site: the document, the JSON pointer of the node, and the keyword whose fact the
#: annotation does not carry.  The same three fields :class:`adcp.types._base.Approximation`
#: carries, because the key of this registry IS the approximation's own address.
Site = tuple[str, str, str]

#: **The registry: site -> upstream issue.**  Empty, and the module docstring says why
#: that is a READING and not a gap: an attribution is OURS until an issue exists, so an
#: empty registry means every declared approximation is ours and none is claimed as
#: upstream without a filed reference.
REGISTRY: Mapping[Site, Issue] = {}


def issue_for(document: str, pointer: str, keyword: str) -> Issue | None:
    """The upstream issue for this site, or ``None`` where the widening is OURS.

    **ONE lookup and no precedence to get wrong** (section 3): "the attribution is
    ``Ours`` at the cell's own address unless ``attribution.py`` holds an entry for this
    document, pointer and keyword, in which case it is that entry's issue.  One lookup,
    no precedence to get wrong: a site-level entry is more specific than a keyword-level
    one."

    So ``None`` is not an absence to repair: it is the answer that the design decided
    this widening and the cell that decided it is the attribution.
    """
    return REGISTRY.get((document, pointer, keyword))


def malformed(registry: Mapping[Site, object] | None = None) -> tuple[Site, ...]:
    """Every site in ``registry`` whose entry is not a well-formed :class:`Issue`.

    The registry-level half of the no-issue rule, so section 9's named grader for it --
    "an upstream attribution's issue | ``attribution.py``'s own test | an entry with no
    issue is a ``BuildFailure``" -- can ask the question of the whole registry.

    :meth:`Issue.__post_init__` already makes a malformed entry unconstructable, so over
    :data:`REGISTRY` this is empty by construction; it is not redundant, because a
    registry assembled from anything but a literal -- a later row generating entries from
    a filed-issue list, say -- can hold a value this module never constructed.  Asked of
    an arbitrary mapping for exactly that reason.
    """
    registry = REGISTRY if registry is None else registry
    return tuple(
        sorted(
            site
            for site, entry in registry.items()
            if not isinstance(entry, Issue) or not entry.reference.strip() or not entry.summary.strip()
        )
    )


#: The three things a look at upstream's tracker can find, and no fourth.
#:
#: ``ABSENT`` is a state and not a missing entry, which is the whole reason this is an
#: enumeration: a reference that does not resolve is a FACT somebody measured, and
#: recording it is what tells a reader "this was checked and there is nothing there" apart
#: from "nobody has looked".  :func:`absent` is the gate over it.
STATES = ("OPEN", "CLOSED", "ABSENT")


@dataclass(frozen=True)
class Sighting:
    """What was seen when somebody looked at one upstream reference, and when.

    ``state`` is one of :data:`STATES`, ``title`` is the issue's own title as the tracker
    prints it -- so a reader can tell whether the issue is about what the citation claims
    without following the link -- and ``seen`` is the date of the look.

    ``title`` is required for ``OPEN`` and ``CLOSED`` and must be empty for ``ABSENT``:
    there is no title to quote for an issue that does not exist, and a sentence invented
    for one would be the record claiming to have seen something it did not.

    Frozen, so an entry cannot be re-pointed after import.  ``survey/upstream_issues.py``
    is what regenerates this registry from the tracker, which is what makes "somebody
    looked" reproducible rather than asserted.
    """

    reference: str
    state: str
    title: str
    seen: str

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise BuildFailure(
                f"{self.reference!r} is recorded as {self.state!r}, which is not one of "
                f"{STATES}: a sighting records what a look at the tracker found, and a "
                "fourth state would be a reading nobody made"
            )
        if self.state == "ABSENT" and self.title.strip():
            raise BuildFailure(
                f"{self.reference!r} is recorded ABSENT and carries the title "
                f"{self.title!r}: there is no title to quote for an issue that does not "
                "exist, so this record claims to have seen something it did not"
            )
        if self.state != "ABSENT" and not self.title.strip():
            raise BuildFailure(
                f"{self.reference!r} is recorded {self.state} with no title: the title is "
                "how a reader tells whether the issue is about what the citation claims, "
                "without following the link"
            )
        if not self.seen.strip():
            raise BuildFailure(
                f"{self.reference!r} carries no date: a sighting with no date cannot go "
                "stale, which makes it an assertion rather than a measurement"
            )


#: **Every upstream reference THIS REPOSITORY CITES, with what was seen when somebody
#: looked.**  Compared against the citations in both directions.
#:
#: ``docs/plan/final-state.md`` reading 9: "Each declared fact is ours with a decision
#: recorded, or **upstream with an issue that exists**", decided by "every ``upstream``
#: attribution naming a live issue".  :class:`Issue` already refuses an entry with no
#: REFERENCE -- an empty string is not a value this module can hold -- and that is a
#: different claim: a reference is a well-formed spelling, and existence is a fact about
#: upstream's tracker.  No offline check can derive it and this package has no network in a
#: test, so what is checkable is that somebody LOOKED and recorded what they saw.
#:
#: **WHY IT RANGES OVER THE CITATIONS AND NOT OVER :data:`REGISTRY`, which is the one
#: decision in this block.**  :data:`REGISTRY` is empty, so a sighting registry keyed on it
#: is empty too and reading 9's existence clause is answered by a gate with nothing in it.
#: Meanwhile the repository makes the claim in other places: ``codegen/catalogue.py`` rests
#: a decision on ``adcontextprotocol/adcp#8735``, ``codegen/dump_exemptions.py`` on
#: ``#8398``, and ``src/adcp/types/envelopes.py`` -- which SHIPS IN THE WHEEL -- tells a
#: consumer "Upstream: adcontextprotocol/adcp#8516".  Those are the same kind of claim as
#: an attribution: a sentence of ours that rests on somebody else's backlog.  So the
#: population is every reference the repository cites, and an attribution is one way to
#: cite one.
#:
#: **WHAT IS NOT A CITATION OF OURS**: a reference inside a BUNDLE DOCUMENT.  Upstream's
#: own documents cite upstream's own issues, and those references arrive here twice -- in
#: ``schemas/cache/`` and again in the records under ``src/adcp/types/_schemas/`` -- plus a
#: third time in ``patches/``, whose payloads are candidate bundle text.  Measured: eight
#: references (2511, 3075, 3078, 3666, 3823, 3844, 3961, 7440) appear ONLY in that text and
#: are nobody's claim of ours.  ``tests/test_decision_set.py`` does not take that on trust:
#: it requires every reference it excludes to appear in the bundle, so the exclusion can
#: only ever hide upstream's own words.
#:
#: **BOTH DIRECTIONS.**  Forward: a reference the repository cites with no sighting is a
#: claim on someone else's backlog that nobody has checked (:func:`unsighted`).  Backward: a
#: sighting no citation names is a list of issues doing nothing (:func:`unnamed`).  So this
#: cannot grow ahead of a citation and cannot stay behind one -- and neither direction is
#: vacuous, which is the change: there are NINE references here where there were none.
#:
#: **THIS MODULE IS NOT IN THE POPULATION, and it cannot be.**  A sighting's entry spells
#: its own reference twice, so a census that read this file would find every entry citing
#: itself and the backward direction could never fail -- an entry nobody needs certifying
#: its own necessity.  ``tests/test_decision_set.py``'s ``REGISTRY_MODULE`` is the
#: exclusion and carries the measurement that forced it.
#:
#: **ONE WAS ABSENT AND IT WAS IN THE TREE, not planted.**  Issue number ONE of the
#: ``adcontextprotocol/adcp`` tracker was cited three times -- twice in
#: ``tests/test_approximation.py`` and once in ``tests/test_decision_set.py``, every one an
#: injected fixture meaning "a reference only has to be a non-empty string" -- and
#: ``gh issue view 1 --repo adcontextprotocol/adcp`` answers "Could not resolve to an issue
#: or pull request".  So the repository cited a non-existent upstream issue, which is
#: exactly what reading 9 forbids, and the fixtures now spell a reference that does not name
#: a real tracker at all (``example/schema#1``).  That is the rule they broke and the reason
#: this registry found it.
#:
#: **AND THAT NUMBER IS NOT SPELLED AS A REFERENCE ANYWHERE, INCLUDING HERE.**  The census
#: in ``tests/test_decision_set.py`` matches the spelling a citation uses, so a sentence
#: EXPLAINING an absent reference that spells it out is reported as the thing it explains --
#: the same failure as a suppression detector matching the prose about a suppression, which
#: ``tests/test_type_checker.py`` solves by anchoring to a comment's start.  Here the
#: explanation names the repository and the number apart, which no citation does.
#:
#: **ONE IS CLOSED**: ``adcontextprotocol/adcp#7959``, a 3.1.x backport ask, cited in
#: ``docs/schema-patterns-brief.md``.  :func:`closed` reports it, and the rule its test
#: applies is about the ATTRIBUTIONS and not about which file names a number -- a path rule
#: reddens on the sighting that records the closure and on the sentence explaining it.
#:
#: **ONE IS A PULL REQUEST AND THAT IS NOT A SECOND KIND OF THING**:
#: ``adcontextprotocol/adcp#8753``, opened for ``#8735``'s title ask.  Issues and pull
#: requests share one numbering space and ``gh issue view`` resolves either, so a citation
#: naming a PR names something that exists; ``survey/upstream_issues.py`` records a MERGED
#: PR as ``CLOSED``, because what this registry needs to know is whether the ask is live.
VERIFIED: Mapping[str, Sighting] = {
    "adcontextprotocol/adcp#7919": Sighting(
        reference="adcontextprotocol/adcp#7919",
        state="OPEN",
        title=("core/compact-task-submitted composes neither envelope and redeclares four protocol-envelope fields"),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#7959": Sighting(
        reference="adcontextprotocol/adcp#7959",
        state="CLOSED",
        title=(
            "Backport #7580, #7583 and #7617 to 3.1.x: 3.1.25 still ships the defective "
            "signing vectors and webhook_emission storyboard"
        ),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8398": Sighting(
        reference="adcontextprotocol/adcp#8398",
        state="OPEN",
        title="URL validation is over-specified: eight patterns where ^https:// is enough",
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8470": Sighting(
        reference="adcontextprotocol/adcp#8470",
        state="OPEN",
        title=(
            "The submitted-task envelope is named in core/compact-task-submitted.json and "
            "re-declared inline 16 times, each dropping task_id.minLength"
        ),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8472": Sighting(
        reference="adcontextprotocol/adcp#8472",
        state="OPEN",
        title="x-adcp-validation has 380 invented key names and 54% prose: no SDK can enforce it",
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8516": Sighting(
        reference="adcontextprotocol/adcp#8516",
        state="OPEN",
        title=(
            "Failed-response envelope {context, errors, ext} has 12 spellings across 26 "
            "documents; 5 omit errors.minItems"
        ),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8525": Sighting(
        reference="adcontextprotocol/adcp#8525",
        state="OPEN",
        title=(
            "The bundle repeats shapes it never names: 110 patterns over 830 sites, 10 "
            "titled -- extract and $ref instead of repairing in place"
        ),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8735": Sighting(
        reference="adcontextprotocol/adcp#8735",
        state="OPEN",
        title=(
            "The bundle restates 95 object shapes it never titles, over 255 positions in "
            "131 documents -- give each one a `title`"
        ),
        seen="2026-11-05",
    ),
    "adcontextprotocol/adcp#8753": Sighting(
        reference="adcontextprotocol/adcp#8753",
        state="OPEN",
        title="schemas(brand): title data_subject_contestation (#8735)",
        seen="2026-11-05",
    ),
}


def unverified(
    registry: Mapping[Site, Issue] | None = None,
    verified: Mapping[str, Sighting] | None = None,
) -> tuple[tuple[Site, str], ...]:
    """Every SITE whose upstream issue has no recorded sighting.

    Reading 9's second clause at the site level, which is where an attribution lives.  The
    site AND the reference, because the question a reader of a failure asks is "which issue
    am I being asked to believe in".

    Vacuous while :data:`REGISTRY` is empty, and :func:`unsighted` is the direction that is
    not: an attribution is one way to cite an upstream issue and the repository has others.
    """
    rows = REGISTRY if registry is None else registry
    seen = VERIFIED if verified is None else verified
    return tuple(sorted((site, entry.reference) for site, entry in rows.items() if entry.reference not in seen))


def unsighted(cited: Iterable[str], verified: Mapping[str, Sighting] | None = None) -> tuple[str, ...]:
    """Every reference ``cited`` for which nobody has recorded a look at the tracker.

    The forward direction over the whole population: a reference this repository prints is
    a claim on someone else's backlog, and a claim nobody has checked is the thing reading
    9's "an issue that exists" is about.  ``cited`` is a MEASUREMENT over the tree and is
    never written down here, which is what keeps this from being an allowlist.
    """
    seen = VERIFIED if verified is None else verified
    return tuple(sorted({one for one in cited if one not in seen}))


def unnamed(cited: Iterable[str], verified: Mapping[str, Sighting] | None = None) -> tuple[str, ...]:
    """Every sighting that no citation in ``cited`` names.

    The backward direction, and the reason :data:`VERIFIED` is a registry rather than a
    list: it holds what a citation needs and nothing else, so an entry leaves by this door
    on the day the last sentence that cited it is deleted.
    """
    seen = VERIFIED if verified is None else verified
    names = set(cited)
    return tuple(sorted(ref for ref in seen if ref not in names))


def absent(verified: Mapping[str, Sighting] | None = None) -> tuple[str, ...]:
    """Every reference whose sighting records that the issue DOES NOT EXIST.

    Reading 9's "upstream with an issue that **exists**", read off the record.  A sighting
    is not an admission: ``ABSENT`` is how a look says there is nothing there, and this
    function is what makes recording one a failure rather than a note.
    """
    seen = VERIFIED if verified is None else verified
    return tuple(sorted(ref for ref, one in seen.items() if one.state == "ABSENT"))


def closed(verified: Mapping[str, Sighting] | None = None) -> tuple[str, ...]:
    """Every reference whose sighting records a CLOSED issue.

    Reading 9's decided-by says "a **live** issue", and closed is not absent: an issue
    upstream has settled still exists and a sentence recording what was asked and answered
    is worth keeping.  What may not happen is a DECISION of ours resting on one, so the
    rule its test applies is about which kind of file cites it.
    """
    seen = VERIFIED if verified is None else verified
    return tuple(sorted(ref for ref, one in seen.items() if one.state == "CLOSED"))
