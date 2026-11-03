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
narrowings a RUN actually took, read off the graded reports, and answers which of them no
entry admits.  Those are the defect.  :func:`unused` is the other direction -- an entry
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


def _canonical(value: Any) -> str:
    """One spelling of a value, so equality does not depend on how it was written.

    ``json.dumps`` with sorted keys, because the values on both sides of the comparison are
    JSON instances -- a payload the document admits -- and two dicts differing only in key
    order are the same instance.  ``default=repr`` so a value no encoder reaches is still
    comparable rather than raising inside a guard.
    """
    return json.dumps(value, sort_keys=True, default=repr)


@dataclass(frozen=True)
class Narrowing:
    """One narrowing this SDK takes on purpose, as the FACT and not as its kind.

    ``document`` and ``pointer`` are the position, in the space
    :class:`adcp.types._base.SchemaRef` names.  ``value`` is the instance the document
    admits and the class refuses, and it is the field that makes an entry a fact: a kind --
    "a URI whose host differs only in case", "a string longer than 2,083 characters" --
    has no value to state, so an entry that tried to admit one could not be written.

    ``keyword`` is what the document states at the pointer that the annotation does not
    carry, and ``decision`` is the sentence in ``docs/plan/`` that admits the narrowing.
    Both are for the reader and neither is part of the comparison -- an entry whose
    reasoning drifted would otherwise stop admitting the narrowing it was written for, and
    the pair would redden with the wrong explanation.

    Frozen, so an entry cannot be re-pointed after import.
    """

    document: str
    pointer: str
    value: Any
    keyword: str
    decision: str

    @property
    def site(self) -> tuple[str, str, str]:
        """What :func:`admits` compares, in one place so the two directions share it."""
        return (self.document, self.pointer, _canonical(self.value))


@dataclass(frozen=True)
class Taken:
    """One narrowing a RUN took, as a grader reports it.

    The same three fields :attr:`Narrowing.site` compares, plus the ``detail`` the grader
    wrote, so a failure names the pydantic refusal rather than only the position.  Built by
    the guard from the graded reports and never written down, which is what makes the
    comparison's right-hand side a measurement.
    """

    document: str
    pointer: str
    value: Any
    detail: str

    @property
    def site(self) -> tuple[str, str, str]:
        return (self.document, self.pointer, _canonical(self.value))


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
