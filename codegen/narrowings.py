"""The narrowings this SDK takes ON PURPOSE: one enumerated registry, and it is EMPTY.

``docs/plan/rebuild-plan.md`` section 2, under "a keyword we cannot express widens the
annotation":

    **A narrowing taken on purpose is admitted by an ENUMERATED registry and by nothing
    else.**  The registry is the authority, this sentence is not, and a narrowing absent
    from one is the defect above.  Each entry is compared by equality so it admits that
    fact and not its kind -- a rule admitting "the sort of bound a URL type adds" would
    be invisible and permanent.

A narrowing is an annotation tighter than its document: the class refuses a payload the
protocol permits, and ``strict_validate`` cannot repair it, because the schema half admits
the payload and the construction then fails.  That is the one direction section 2 forbids,
so there is exactly one door through which a narrowing may be admitted, and this is it.

**IT IS EMPTY, AND THAT IS A READING RATHER THAN A GAP** (section 2, decided 2026-11-02).
It held two facts a pydantic URL type rendered of its own -- ``minLength: 1`` and
``maxLength: 2083`` -- and those were the registered part.  The type's NORMALISATION was
never registered, and by the sentence above that is what made it the defect: a pydantic URL
lowercases the host and gives an empty path a ``/``, so two distinct strings the document
admits become one value and the value dumped is not the string supplied.

**And the normalisation could not have been registered.**  An entry here is compared by
EQUALITY so that it admits that fact and not its kind, and a normalisation is a kind: "the
sort of rewriting a URL type performs" is exactly the invisible, permanent admission the
rule forbids.  So the type was withdrawn instead, and the registry is empty because there
is no narrowing left to admit -- not because nobody has written the entries down.

**WHY A REGISTRY RATHER THAN A PREDICATE, and the measurement that settles it.**  Section
2 again: "a registry is a DECISION where no other check can report its edit, and a decision
must be read by a test.  That is the discriminator between a decision and a mechanical
lookup: a lookup's error surfaces somewhere else -- a wrong ``_TIGHTER_BOUND`` direction
loosens the composed bound and the pair reports ``added`` -- while a decision's edit is
silent everywhere."  Measured on the registry this replaces: remove ``maxLength`` from
``URL_IMPLIED`` and ``added`` over all 1,571 graded pairs was UNCHANGED -- every pair
graded exactly as it had.  A per-pair reading cannot see an edit here, which is why
``tests/test_decision_set.py`` holds the guard and why both sides of it are derived.

**WHAT READS IT.**  :func:`unadmitted` is the whole of the authority: it takes the
narrowings a RUN actually took -- read off §5's table, one graded cell at a time, which is
the reading that COMPLETES (:data:`_Site`) -- and answers which of them no entry admits.
Those are the defect.  :func:`unused` is the other direction -- an entry
admitting a narrowing no run takes is an allowlist with nothing behind it, which section 2
calls "a declaration with no value behind it is an allowlist wearing a measurement".  The
registry is therefore compared in BOTH directions against a measurement, and neither side
is written down twice.

**It is NOT consulted at the site that narrows**, for the reason section 2 gives for every
other decision in it: a handler that admitted its own narrowing would be a decision nobody
can audit.  The admission is read by the grader, once, over the whole population.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from codegen.keywords import Position


def _canonical(value: Any) -> str:
    """One spelling of a value, so equality does not depend on how it was written.

    ``json.dumps`` with sorted keys, because the values on both sides of the comparison are
    JSON instances -- a payload the document admits -- and two dicts differing only in key
    order are the same instance.  ``default=repr`` so a value no encoder reaches is still
    comparable rather than raising inside a guard.
    """
    return json.dumps(value, sort_keys=True, default=repr)


#: **WHAT AN ENTRY IS INDEXED BY, and it is the CELL rather than the document pointer**
#: (``docs/plan/final-state.md`` reading 9, re-indexed 2026-11-03).
#:
#: An entry used to be keyed ``(document, pointer, value)``.  That key obliges the
#: comparison's right-hand side to be a reading of every PAIR the run builds -- a document
#: and a pointer only a pair has -- and that reading is the draw: measured at **2h21m of
#: CPU at 20.3 GB without completing**, so the equality reading 9 asks for was cut rather
#: than answered, and a cut equality is the one thing reading 9 forbids ("a budget cut is
#: reported as a cut, and no pair passes by leaving the check unexecuted").
#:
#: Keyed on the CELL -- ``(keyword, position, canonical(value))`` -- the right-hand side is
#: §5's table instead: **289 live cells, enumerable, and it completes.**  §8 is the reason
#: that is the same measurement and not a weaker one: "a cell is one keyword at one
#: position inside a two-keyword probe, so the cost of a cell proof is a function of the
#: KEYWORD and not of any document that states it", and the cell form "reaches the 86
#: documents no draw will ever finish".
#:
#: **§2's equality-over-the-value rule survives the re-indexing unchanged**, which is what
#: makes it a re-indexing and not a relaxation: the value is still the instance the
#: document admits and the class refuses, so an entry still admits that FACT and not its
#: kind.  What moves is which coordinates locate the fact, and the cell locates it in the
#: space the obligation is actually stated over.
_Site = tuple[str, str, str]


@dataclass(frozen=True)
class Narrowing:
    """One narrowing this SDK takes on purpose, as the FACT and not as its kind.

    ``keyword`` and ``position`` are §5's CELL -- one keyword at one of §3's nine
    positions -- which is the space the obligation is stated over; :data:`_Site` carries
    the measurement that made it the key.  ``value`` is the instance the document admits
    and the class refuses, and it is the field that makes an entry a fact: a kind -- "a URI
    whose host differs only in case", "a string longer than 2,083 characters" -- has no
    value to state, so an entry that tried to admit one could not be written.

    ``decision`` is the sentence in ``docs/plan/`` that admits the narrowing.  It is for
    the reader and is not part of the comparison -- an entry whose reasoning drifted would
    otherwise stop admitting the narrowing it was written for, and the pair would redden
    with the wrong explanation.

    Frozen, so an entry cannot be re-pointed after import.
    """

    keyword: str
    position: Position
    value: Any
    decision: str

    @property
    def site(self) -> _Site:
        """What :func:`admits` compares, in one place so the two directions share it."""
        return (self.keyword, self.position.name, _canonical(self.value))


@dataclass(frozen=True)
class Taken:
    """One narrowing a RUN took, as a grader reports it.

    The same three coordinates :attr:`Narrowing.site` compares, plus the ``detail`` the
    grader wrote, so a failure names the refusal rather than only the cell.  Built by the
    guard from §5's table graded cell by cell and never written down, which is what makes
    the comparison's right-hand side a measurement.
    """

    keyword: str
    position: Position
    value: Any
    detail: str

    @property
    def site(self) -> _Site:
        return (self.keyword, self.position.name, _canonical(self.value))


#: **THE REGISTRY.**  Empty; the module docstring says why that is a reading.
#:
#: A tuple and not a mapping, because an entry is a FACT with five fields and not a lookup
#: by position: two narrowings at one pointer are two entries, and keying by position would
#: silently keep the last one written.
ADMITTED: tuple[Narrowing, ...] = ()


def admits(
    taken: Taken, admitted: Sequence[Narrowing] | None = None
) -> Narrowing | None:
    """The entry that admits ``taken``, or ``None``.

    **EQUALITY over the position AND the value**, which is section 2's own rule and the
    whole reason this is a registry: an entry admits that fact and not its kind.  An entry
    at the right pointer with a different value does not admit this narrowing, and neither
    does a predicate, because there is nowhere here to write one.
    """
    rows = ADMITTED if admitted is None else admitted
    return next((one for one in rows if one.site == taken.site), None)


def unadmitted(
    taken: Iterable[Taken], admitted: Sequence[Narrowing] | None = None
) -> tuple[Taken, ...]:
    """Every narrowing the run took that no entry admits.  **These are the defect.**

    Section 2: "an annotation tighter than its document refuses a payload the protocol
    permits, and ``strict_validate`` cannot repair it ... A narrowing is the defect the old
    sentence was reaching for, and nothing below widens into one."
    """
    rows = ADMITTED if admitted is None else admitted
    return tuple(one for one in taken if admits(one, rows) is None)


def unused(
    taken: Iterable[Taken], admitted: Sequence[Narrowing] | None = None
) -> tuple[Narrowing, ...]:
    """Every entry that admits no narrowing the run took.

    The other direction, and it is not symmetry for its own sake: an entry nothing needs is
    an allowlist wearing a measurement, and it survives exactly as long as nobody checks.
    An entry whose narrowing was repaired leaves by this door and takes its own line with
    it.
    """
    rows = ADMITTED if admitted is None else admitted
    sites = {one.site for one in taken}
    return tuple(one for one in rows if one.site not in sites)
