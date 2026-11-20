"""§4's domain-collision repetition settles in a small number of rounds, or FAILS BY NAME.

``adcp-client-python-wckn``.  ``emit._the_domains_exports`` was ``while True:`` with one
exit, and ``emit.domain_exports`` asserted in prose that the repetition "stops after three
rounds".  Nothing read the round count, so a change that stopped the census settling
produced **a hang** -- measured at 26 rounds and still climbing over a 92-document closure
after a lowering change minted 187 colliding nested-union names.  Each round runs
``decidable`` and ``bundle.record`` once per document, which took those two from 1,706 calls
to 12,607 and produced 25,067,171 ``bundle.subschemas`` calls; nothing inside a round was
wrong, which is why no profile found it and no cache fixed it.

**THE THIRD INVARIANT STATED IN PROSE AND FALSE IN FACT**, after
``compiler.branches_of``'s "one level deep by construction" (corrected, measured at depth 3)
and ``emit.asserted_formats``' "one set and cannot drift" (measured at 266 nodes).  So this
file grades the two halves a prose invariant cannot:

1. **The count is what the docstring says.**  A number in a docstring that nothing reads is
   the defect, so the number is read here.
2. **A census that cannot settle REDDENS.**  Not a warning, because a warning in a compile
   that writes a tree is a tree written with the wrong names; and not a silent cap, because
   a partial census returns names that are wrong with nothing saying so.

A hang is the one outcome a reader cannot act on, and that is the whole reason the failure
is named rather than the loop made more careful.
"""

from __future__ import annotations

import dataclasses

import fresh
import pytest

from codegen import bundle, emit
from codegen.refusal import BuildFailure

#: The bundle a run reads, re-exported from ``tests_emit/fresh.py`` so this file cannot come
#: to range over a different one from the compile it grades.
BUNDLE = fresh.BUNDLE

#: What the repetition costs on this bundle, measured 2026-11-20 over all 23 domains and
#: 3,217 published symbols.  Asserted rather than quoted: this is the figure
#: ``_CENSUS_ROUNDS`` is generous against, so a silent drift in it is a silent drift in how
#: much headroom the bound actually has.
SETTLES_IN = 2


def test_the_census_settles_in_the_number_of_rounds_the_docstring_claims() -> None:
    """The round count is READ, which is the whole difference from asserting it in prose.

    Counted by wrapping ``emit.emit`` -- a round IS a call carrying a ``naming_census``, so
    this counts the thing the loop does rather than a proxy for it.
    """
    rounds = 0
    original = emit.emit

    def counted(bundle_dir, documents, *, naming_census=None):
        nonlocal rounds
        if naming_census is not None:
            rounds += 1
        return original(bundle_dir, documents, naming_census=naming_census)

    domains = frozenset(emit.domain(document) for document in bundle.portable(BUNDLE))
    assert len(domains) >= 23, f"only {len(domains)} domains; the measurement ranged over 23"

    emit.emit = counted
    try:
        census = emit._the_domains_exports(BUNDLE, domains)
    finally:
        emit.emit = original

    assert rounds == SETTLES_IN, (
        f"§4's repetition took {rounds} rounds over {len(domains)} domains; it took "
        f"{SETTLES_IN} when `_CENSUS_ROUNDS` was set. That bound is "
        f"{emit._CENSUS_ROUNDS}, so this is not yet a failure -- but the headroom is now "
        f"{emit._CENSUS_ROUNDS - rounds} rounds instead of "
        f"{emit._CENSUS_ROUNDS - SETTLES_IN}, and a schema bump that halves it again "
        "should be a decision and not a surprise. Re-measure, update `SETTLES_IN`, and say "
        "in the commit why the count moved."
    )
    assert rounds < emit._CENSUS_ROUNDS, "the bound is at or below the measured cost"
    assert sum(len(symbols) for symbols in census.values()) >= 3000, (
        "the census settled over a surface far smaller than the 3,217 symbols measured, so "
        "the round count above is a figure about a different population"
    )


def test_a_census_that_cannot_settle_fails_by_name_rather_than_running() -> None:
    """The failure path, exercised -- with the round count and the contested names in it.

    **The divergence is injected at the SURFACE and not by patching the loop**, because what
    is being graded is that the loop reacts to a census it cannot settle. Two documents of
    one domain are made to want one name on every round, which is exactly the condition
    §4's repetition exists to resolve and exactly what it cannot resolve when the name is
    forced: the rule spends a prefix, and here the forced answer ignores it.
    """
    domains = frozenset({"signals"})
    wanted = sorted(d for d in bundle.portable(BUNDLE) if emit.domain(d) in domains)
    assert len(wanted) >= 2, f"the signals domain holds {len(wanted)} documents; need 2"
    first, second = wanted[0], wanted[1]

    original = emit.emit

    def irreducible(bundle_dir, documents, *, naming_census=None):
        """Every round, both documents publish one word and neither moves off it."""
        round_of = original(bundle_dir, documents, naming_census=naming_census)
        forced = dict(round_of.surface)
        for document in (first, second):
            forced[emit.module_path(document)] = {"TheSameWord": "#"}
        return dataclasses.replace(round_of, surface=forced)

    emit.emit = irreducible
    try:
        with pytest.raises(BuildFailure) as raised:
            emit._the_domains_exports(BUNDLE, domains)
    finally:
        emit.emit = original

    message = str(raised.value)
    assert f"did not settle in {emit._CENSUS_ROUNDS} rounds" in message, message
    assert "TheSameWord" in message, (
        "the failure does not name the word still contested, so a reader has the round "
        f"count and nothing to act on: {message}"
    )
    for document in (first, second):
        assert document in message, (
            f"the failure does not name {document}, which is one of the two documents "
            f"wanting the word: {message}"
        )
    assert "Collisions left per round" in message, (
        "the failure does not carry the per-round trail, which is what distinguishes a "
        f"census converging slowly from one that cannot settle: {message}"
    )


def test_the_bound_is_generous_against_the_measurement_and_not_tuned_to_it() -> None:
    """A bound equal to the cost reddens on the first legitimate schema bump.

    Stated as a ratio rather than a number so that re-measuring ``SETTLES_IN`` cannot
    quietly turn the bound into a tripwire: the point of the bound is to name a census that
    cannot settle, never to cap one that can.
    """
    assert emit._CENSUS_ROUNDS >= SETTLES_IN * 4, (
        f"_CENSUS_ROUNDS is {emit._CENSUS_ROUNDS} against a measured {SETTLES_IN} rounds. "
        "A bound within a small multiple of the cost will redden on a schema bump that "
        "legitimately needs more rounds, which is a false failure in the one check meant "
        "to catch a real one."
    )
