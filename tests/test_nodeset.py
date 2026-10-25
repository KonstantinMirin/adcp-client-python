"""``tests/nodeset.py``'s own grader, and it exists because of a failed probe.

``salesagent-j3k2l.47`` replaced roughly a hundred census equalities with calls to
``claimed`` and ``partitions``.  Fire-probing two of those conversions by NEUTERING THE
HELPER -- deleting ``claimed``'s non-emptiness assertion -- left the converted tests
GREEN, which is correct and is the point: the helper carries the assertion, so removing
it removes the assertion and there is nothing left in the caller to fail.

That makes the helper a single point every one of those conversions depends on, with
nothing grading it.  This file is what grades it.  Each test states what the helper must
REFUSE, so an edit that relaxes one reddens here rather than silently disarming the
conversions.
"""

from __future__ import annotations

import pytest

from tests.nodeset import claimed, partitions, ratchet


def test_claimed_refuses_an_empty_set() -> None:
    """The one that cannot be left out: an empty derivation passes every assertion
    over it and is indistinguishable from a working check."""
    assert claimed("two things", ["a", "b"]) == {"a", "b"}
    for empty in ([], set(), {}, (), range(0)):
        with pytest.raises(AssertionError, match="empty set of nodes"):
            claimed("nothing", empty)


def test_claimed_refuses_a_member_outside_the_set_it_claims() -> None:
    """``inside`` is the set it is drawn from, and a member outside it means the
    derivation reached something the check does not claim to range over."""
    assert claimed("a part", ["a"], inside=["a", "b"]) == {"a"}
    with pytest.raises(AssertionError, match="not drawn from the set it claims"):
        claimed("a part", ["a", "z"], inside=["a", "b"])


def test_partitions_refuses_a_member_no_part_accounts_for() -> None:
    assert partitions(["a", "b"], left=["a"], right=["b"]) == {"a", "b"}
    with pytest.raises(AssertionError) as caught:
        partitions(["a", "b", "c"], left=["a"], right=["b"])
    assert "accounted for by no part" in str(caught.value)
    assert "'c'" in str(caught.value)  # BY NAME, not as a difference of two totals


def test_partitions_refuses_a_part_member_outside_the_whole() -> None:
    with pytest.raises(AssertionError) as caught:
        partitions(["a"], left=["a"], right=["z"])
    assert "accounted for but not in the whole" in str(caught.value)
    assert "'z'" in str(caught.value)


def test_partitions_refuses_a_member_two_parts_both_claim() -> None:
    with pytest.raises(AssertionError, match="claimed by both left and right"):
        partitions(["a", "b"], left=["a", "b"], right=["b"])


def test_partitions_refuses_an_empty_whole_and_a_partition_with_no_parts() -> None:
    """Two sets whose sizes sum correctly can still both miss a member, and an empty
    whole makes every clause below it hold for free."""
    with pytest.raises(AssertionError, match="empty whole"):
        partitions([], left=[], right=[])
    with pytest.raises(AssertionError, match="accounts for nothing"):
        partitions(["a"])


def test_partitions_admits_an_empty_part_because_that_is_a_shape_the_design_asks_for() -> None:
    """"A check that partitions enumerates the cases its DECISION names and asserts an
    empty part is empty."  So an empty PART is admitted; an empty WHOLE is not."""
    assert partitions(["a"], live=["a"], dormant=[]) == {"a"}


def test_ratchet_refuses_a_fall_below_its_floor_and_a_rise_above_its_ceiling() -> None:
    """It hands the LIVE value back, so a caller can go on reading it, and it refuses a
    move in the direction ``because`` says is not allowed."""
    floor = 10
    assert ratchet("n", floor, at_least=floor, because="it only grows") == floor
    assert ratchet("n", floor + 1, at_least=floor, because="it only grows") == floor + 1
    with pytest.raises(AssertionError, match=f"is below the floor {floor}"):
        ratchet("n", floor - 1, at_least=floor, because="it only grows")
    with pytest.raises(AssertionError, match=f"is above the ceiling {floor}"):
        ratchet("n", floor + 1, at_most=floor, because="it only shrinks")


def test_ratchet_refuses_a_number_with_no_direction() -> None:
    """A floor with no stated direction is a number nobody can re-point correctly when
    it moves, which is the whole defect the ratchet shape replaces."""
    with pytest.raises(AssertionError, match="a ratchet states a direction"):
        ratchet("n", 10, because="nothing is said about which way it moves")
