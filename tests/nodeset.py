"""The shapes a check in this suite is allowed to take, one function each.

Section 8's last paragraph: *"A check is exhaustive over the set of nodes it claims, or
it does not exist.  A check that enumerates a subset reports on that subset only, and
says so."*

Three shapes satisfy that, and everything here is one of them:

``claimed``
    name the set of nodes a check ranges over, and refuse an empty one.  **This is the
    one that cannot be skipped.**  A derivation that selects nothing passes every
    assertion over it and is indistinguishable from a working check -- measured twice
    on this epic, once where 0 graded pairs held the shape a fold was gated on, and
    once where a census of 90 copies reddened when the population grew to 92.

``partitions``
    the derived property: total and disjoint, every member of the whole accounted for
    by exactly one named part, with the unaccounted and the double-counted members
    REPORTED BY NAME rather than as a difference of two totals.

``ratchet``
    a number, where a number is genuinely the obligation, with its DIRECTION stated.
    An equality on a count is the shape this module exists to replace: it is one bundle
    version's reading of a quantity every emitting row moves, so two rows in flight
    compute two different correct values for it and no merge resolves that by picking a
    side.  A floor says what may not happen.

What is NOT here, deliberately: no registry, no decorator and no rule table.  A check
names its own set at the point it ranges over it, because a set named somewhere else is
a second place to go stale.

**AND BECAUSE THE SETS ARE NAMED HERE, THEIR SIZES CAN BE READ HERE.**  ``NODESET_CENSUS``
(:data:`_CENSUS`) writes the size of every set a run claims, which is the only reason a
verdict needs for quoting a number: before it existed, a lane wanting one of these
figures wrote a second derivation beside the check and quoted THAT, and two derivations
of one number is how a verdict comes to disagree with the gate it cites.  It asserts
nothing -- a census is not an obligation, and ``ratchet`` is the shape for a number that
is one.
"""

from __future__ import annotations

import itertools
import os
import sys
from collections.abc import Hashable, Iterable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T", bound=Hashable)

#: **THE SIZE OF EVERY SET A CHECK CLAIMS, where a lane asks for it and nowhere else.**
#: :func:`claimed` and :func:`partitions` already know every number a verdict wants to
#: state -- how many union bases a reading ranged over, how many branch positions the
#: floor answered for, how many of them each outcome holds for -- and until this existed a
#: lane wanting one of those figures wrote a second derivation beside the check and quoted
#: THAT.  Two derivations of one number is how a verdict comes to disagree with the gate
#: it cites.  So the check is the instrument: point ``NODESET_CENSUS`` at a file and every
#: set named in the run is appended to it as ``size<TAB>check<TAB>name``.
#:
#: **OFF BY DEFAULT AND IT ASSERTS NOTHING.**  A census is not an obligation
#: (:func:`ratchet` is the shape for a number that is one), so this writes and never
#: compares: an equality on a count is the thing this module exists to replace
#: (``tests/test_every_check_names_its_set.py``).  Unset, the only cost is one ``is None``
#: per claim.
_CENSUS = os.environ.get("NODESET_CENSUS")


def _record(name: str, size: int) -> None:
    """Append one claimed set's size, with the check that claimed it.

    The CHECK is read off the calling frame rather than passed in, because a name passed
    in is a name that can disagree with the function it sits in -- and the whole point of
    reading a census off the check is that there is one derivation.  Two frames up:
    this function, then :func:`claimed` or :func:`partitions`, then the test.  Appended
    line by line so a parallel run interleaves whole rows rather than truncating one.
    """
    if _CENSUS is None:
        return
    with Path(_CENSUS).open("a") as fh:
        fh.write(f"{size}\t{sys._getframe(2).f_code.co_name}\t{name}\n")


def claimed(name: str, members: Iterable[T], *, inside: Iterable[T] | None = None) -> set[T]:
    """The set of nodes a check ranges over, named and asserted non-empty.

    ``inside`` is the set it is drawn from, when there is one: a selector over the
    bundle is inside ``bundle.portable``, and a set of emitted documents is inside the
    emitter's own output.  A member outside it means the derivation reached something
    the check does not claim to range over, which no assertion about the members can
    detect.
    """
    got = set(members)
    _record(name, len(got))
    assert got, f"{name}: empty set of nodes -- every assertion over it holds vacuously"
    if inside is not None:
        outside = got - set(inside)
        assert not outside, f"{name}: not drawn from the set it claims: {sorted(outside)!r}"
    return got


def partitions(whole: Iterable[T], **parts: Iterable[T]) -> set[T]:
    """Every member of ``whole`` accounted for by exactly one named part.

    The arithmetic alone is not this property and has been green while it was false:
    two sets whose sizes sum correctly can still both miss a member and double-count
    another.  So the two failures are reported separately and by name.
    """
    everything = set(whole)
    named = {k: set(v) for k, v in parts.items()}
    for part in sorted(named):
        _record(part, len(named[part]))
    assert everything, "empty whole -- the partition below holds vacuously"
    assert named, "a partition with no parts accounts for nothing"

    union: set[T] = set().union(*named.values())
    assert union == everything, {
        "accounted for by no part": sorted(everything - union),
        "accounted for but not in the whole": sorted(union - everything),
    }
    for left, right in itertools.combinations(sorted(named), 2):
        both = named[left] & named[right]
        assert not both, f"claimed by both {left} and {right}: {sorted(both)!r}"
    return everything


def ratchet(
    name: str,
    live: int,
    *,
    at_least: int | None = None,
    at_most: int | None = None,
    because: str,
) -> int:
    """A count with its direction stated, and never an equality.

    ``because`` is the direction's reason -- what kind of change may move this number
    and which way -- and it is required, because a floor with no stated direction is a
    number nobody can re-point correctly when it moves.
    """
    assert at_least is not None or at_most is not None, f"{name}: a ratchet states a direction"
    if at_least is not None:
        assert live >= at_least, f"{name}: {live} is below the floor {at_least} -- {because}"
    if at_most is not None:
        assert live <= at_most, f"{name}: {live} is above the ceiling {at_most} -- {because}"
    return live
