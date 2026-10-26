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

**The registry is EMPTY today, and that is the row's exit condition rather than an
omission.**  This row widens no cell, so no widening exists to attribute: section 14 step
8 is "the approximation, end to end, with no cell widened", and step 10 is where the
entries arrive -- "the upstream issues must be filed before this step lands, not after:
``attribution.py`` admits no entry without one, so an unfiled issue is a build failure and
the step cannot be completed around it."  ``adcp-client-python-10l.22`` is the row that
files them.
"""

from __future__ import annotations

from collections.abc import Mapping
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

#: **The registry: site -> upstream issue.**  Empty, by section 14 step 8's exit
#: condition; the module docstring says which row fills it and why it cannot be filled
#: around an unfiled issue.
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
            if not isinstance(entry, Issue)
            or not entry.reference.strip()
            or not entry.summary.strip()
        )
    )
