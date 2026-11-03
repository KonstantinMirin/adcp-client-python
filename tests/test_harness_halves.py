"""The two halves section 6 added to the harness, graded on hand-written documents.

``tests/test_harness_steps.py`` stood here and is deleted with the machinery it graded:
every test in it asserted a property of the per-keyword step -- that a mutation is
exclusive, that a position group is rewritten together, that a witness the harness could
not build is reported rather than passed -- and section 6 removed the step sites because
"a step site asserts that ``jsonschema`` rejects a payload violating the schema it was
handed. The generated class takes no part in the outcome."

What replaced them is two halves of ``check_pair``, and this file is what grades those:

* the DUMP half of the accepts check -- construct, dump, and let the document decide on
  the dump.  It is the only thing in the harness that reads what a class DID with a
  value rather than whether it took it.
* the LIVENESS check -- one payload the document refuses, derived from an accepted
  instance and offered to the entry point, which proves that class's schema half is
  connected.

**Every fixture here differs from its control in exactly the dimension being judged**,
and the first cut of this file got that wrong in a way worth recording: ``DropsB``
originally lost a field the document declared OPTIONAL, so a dump without it was valid,
the dump half correctly passed, and the test read as the check being blind.  The
document has to DEMAND the dropped key for the fixture to judge anything.

Hand-written documents and not bundle ones, because the bundle holds no faithful/widened
pair of classes over one document: these are three, differing in one axis each.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from adcp.types._base import _refuse  # noqa: PLC2701 -- the production schema half
from codegen import harness

#: One object document that demands both of its keys and admits no others, so each
#: perturbation below has exactly one thing to break.
DOC: dict[str, Any] = {
    "type": "object",
    "required": ["a", "b"],
    "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
    "additionalProperties": False,
}


class Faithful(BaseModel):
    """The control: the document's own accepted set, and it round-trips."""

    model_config = ConfigDict(extra="forbid")
    a: str
    b: int


class NoRequired(BaseModel):
    """Widened in the one axis a class cannot be widened in silently: requiredness."""

    model_config = ConfigDict(extra="forbid")
    a: str | None = None
    b: Any = None


class DropsB(Faithful):
    """Faithful about what it ACCEPTS and lossy about what it emits.

    A hand-rolled renderer that forgets a field the document demands, which is the
    defect class the dump half exists for and which no acceptance test can see: this
    model accepts every instance the document accepts.
    """

    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return {"a": self.a}


def accept_of(cls: type[BaseModel]):
    """The production shape of an entry point: the document decides, then the class builds."""

    def accept(payload: Any) -> Any:
        _refuse(DOC, payload, cls.__name__)
        return cls.model_validate(payload)

    return accept


# --------------------------------------------------------------------------- #
# refusing_payload: a payload the DOCUMENT refuses, derived from one it accepts
# --------------------------------------------------------------------------- #
def test_the_required_drop_arm_is_reached_first_and_names_the_key() -> None:
    """The cheapest proof a schema half ran, and the order is deliberate.

    A missing required key is the plainest thing a document refuses, so it is tried
    before the whole-instance replacement.  The ``how`` names the key, because a report
    that says only "something was dropped" cannot be acted on.
    """
    assert harness.refusing_payload(DOC, {"a": "x", "b": 1}) == (
        {"b": 1},
        "drops the required key 'a'",
    )


def test_the_replacement_arm_reaches_a_document_that_demands_no_key() -> None:
    """The arm the first one cannot reach, and the shape that proves it is needed.

    An ``additionalProperties: true`` mapping root demands nothing, so there is no
    required key to drop -- and it still states ``type: object``, which ``None``
    violates.  That is why the bundle has no document the derivation gives up on.
    """
    assert harness.refusing_payload({"type": "object"}, {}) == (
        None,
        "replaces the instance with None",
    )


def test_a_document_that_refuses_nothing_yields_no_payload_rather_than_a_forced_one() -> None:
    """``None`` and not a perturbation pushed through.

    Every candidate is screened by ``conforms`` before it is offered to anything, so a
    document stating no type, no requiredness and no closure admits all three shapes and
    the honest answer is that there is nothing to offer.  Forcing one would assert a
    refusal the document does not make.
    """
    assert harness.refusing_payload({"description": "anything at all"}, {}) is None


def test_the_closed_object_arm_is_reached_last_and_adds_a_key_no_document_declares() -> None:
    """The third arm, on the one shape the first two cannot reach.

    A closed object that demands no key and admits every scalar: ``required`` is empty so
    the first arm finds nothing, and the node has no ``type`` so no alien value is
    refused either.  What it does refuse is an undeclared property.
    """
    open_to_scalars = {"properties": {"a": {}}, "additionalProperties": False}
    payload, how = harness.refusing_payload(open_to_scalars, {})
    assert how == "adds the property '__adcp_harness_not_a_property__'"
    assert harness.conforms(open_to_scalars, payload) is False


# --------------------------------------------------------------------------- #
# the liveness check: is this class's schema half connected?
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cls", [Faithful, NoRequired], ids=lambda c: c.__name__)
def test_a_connected_schema_half_refuses_whatever_the_class_is(cls: type[BaseModel]) -> None:
    """Both classes pass, and section 6 says that is the point rather than a weakness.

    Pydantic is DELIBERATELY less strict than the schema -- D4 gives the schema the
    acceptance decision and pydantic the construction -- so a payload the schema refuses
    measures nothing about the class.  What one refusal through the entry point proves is
    that the schema half is RUNNING for this class, and it proves that for a widened
    class exactly as for a faithful one.
    """
    result = harness.check_liveness(DOC, accept_of(cls), {"a": "x", "b": 1})
    assert result.outcome == "pass"
    # The DOCUMENT is asked which keyword bit, rather than the perturbation being
    # trusted to have broken what it aimed at.
    assert result.violated == ("required",)


def test_a_silent_schema_half_is_reported_and_that_is_the_whole_content_of_the_check() -> None:
    """The failing direction, which needs an entry point with no schema half at all.

    ``model_validate`` is the class's construction half alone, so a class declaring
    nothing required accepts a payload the document refuses.  Through the real entry
    point the same class passes (above), which is what makes this a check on the WIRING:
    the difference between the two is whether ``_refuse`` ran.

    **This is NOT an assertion that a correct class's ``model_validate`` must refuse a
    schema-invalid payload, and such an assertion would be wrong.**  Pydantic is
    DELIBERATELY less strict than the schema (D4): a model holds the document's types
    and emits the document's schema rather than reimplementing every JSON Schema
    keyword, which is why ``strict_validate`` exists at all.  What is asserted here is
    the harness's own reporting -- that an entry point with NO schema half is named
    rather than passed -- and the fixture is a hand-written widened class supplied for
    that purpose.  No production pair reaches this branch: ``check_pair`` passes
    ``pair.accept``, and over all 1,055 graded pairs the measured count of
    ``schema_half_not_connected`` is 0.
    """
    result = harness.check_liveness(DOC, NoRequired.model_validate, {"a": "x", "b": 1})
    assert result.outcome == "schema_half_not_connected"


def test_a_refusal_that_is_not_pydantics_is_a_verdict_and_not_a_pass() -> None:
    """Measured over 838 pairs: 0 refuse with any other exception.

    So admitting a foreign exception as a refusal would cost nothing today and would hide
    the one thing it could ever hide -- an entry point raising what the caller cannot
    catch, which is how the specification's own probe read a pair nothing graded as green.
    """
    import jsonschema

    def foreign(_payload: Any) -> Any:
        raise jsonschema.ValidationError("not pydantic's error")

    result = harness.check_liveness(DOC, foreign, {"a": "x", "b": 1})
    assert result.outcome == "model_error"
    assert result.detail.startswith("ValidationError"), result.detail


# --------------------------------------------------------------------------- #
# the dump half of the accepts check
# --------------------------------------------------------------------------- #
def test_the_dump_half_catches_a_class_that_loses_a_key_the_document_demands() -> None:
    """The defect no acceptance test can see, and the control beside it.

    ``DropsB`` accepts every instance ``Faithful`` accepts -- it IS ``Faithful`` plus a
    renderer -- so the acceptance half of the draw and the liveness check both pass it.
    The dump is what separates them.
    """
    assert harness.check_accepts(DOC, accept_of(Faithful), examples=10).outcome == "pass"
    lossy = harness.check_accepts(DOC, accept_of(DropsB), examples=10)
    assert lossy.outcome == "model_dropped_a_fact", lossy.detail
    # The CAUSE comes first, because ``detail`` is truncated and a reason behind a
    # megabyte of dumped instance is a reason nothing can read.
    assert lossy.detail.startswith("the document refuses the dump on required"), lossy.detail
    assert lossy.round_tripped == 0


def test_a_round_tripped_instance_is_counted_and_an_unreported_one_is_not() -> None:
    """The denominator the pair's verdict reads, and it counts dumps rather than draws.

    ``PairReport.graded_instances`` is this number, and ``PairReport.outcome`` turns a
    zero into a refusal: a pair that drew ten instances and dumped none back out to
    something the document admits was graded by nothing.
    """
    passing = harness.check_accepts(DOC, accept_of(Faithful), examples=7)
    assert passing.examples == 7
    assert passing.round_tripped == 7


# --------------------------------------------------------------------------- #
# the BUDGET, which is a statement about the instrument and never about a document
# --------------------------------------------------------------------------- #
# **THE PROPERTY IS PROPAGATION AND IT IS NOT THE CLOCK**, which is what the fixture these
# two checks replace had wrong (``adcp-client-python-82m.34``).
#
# It was a 1 s ``within`` around ``check_accepts`` over a schema commented "nothing about it
# is unsatisfiable -- an ``Unsatisfiable`` or a ``strategy_error`` here would be a different
# reading": 2,000 objects of 200 demanded 120-character strings.  **The comment is refuted
# by the draw.**  Run with NO budget at all, five times, that schema returns on its own in
# 15.5, 20.7, 24.7, 24.8 and 25.9 s with ``outcome='strategy_error'`` and the detail
# "Unsatisfiable: ... 459 of 459 test cases were too large to finish generating".
# ``hypothesis``'s buffer is 8,192 bytes and the instance is 400,000 strings, so every one
# of its 459 generation attempts overruns and the library gives up -- the draw was never
# unbounded, it was slow.
#
# So the check was a race between two non-deterministic terminations, and NEITHER of them is
# the property.  Measured: the ``check_accepts`` form failed 0 of 30 runs alone and **2 of 30
# under 48-way CPU load**, the ``_Draws`` form in ``tests/test_widening_corpus.py`` **1 of 20
# under 24-way load** and 1 of 6 at ``-n 4`` in a four-file set; every failure is
# ``DID NOT RAISE OverBudget`` with the whole test taking 1.1 s.  The mechanism is the one
# ``within``'s own docstring already names: the alarm's first firing lands in
# ``hypothesis``'s ``gc_callback``, where Python DISCARDS the exception, ``hypothesis``
# concludes ``Unsatisfiable`` at ~1.1 s, the block exits NORMALLY, and ``within``'s
# ``finally`` clears the timer before a retry can land.
#
# **AND WIDENING THE BUDGET MAKES IT WORSE, which is why that was not the fix.**  The margin
# is not clock-against-contention, it is clock-against-a-draw-that-ends-itself: at any budget
# over ~26 s the library wins the race every time and the check fails on an idle box.
#
# What replaces it is two checks with the division the property deserves.  The one the
# property depends on INJECTS the raise and has no clock in it at all; the one that covers
# the end-to-end path uses the real alarm over a draw that cannot end on its own, so there
# is no termination for contention to bring forward.

#: How long a non-terminating draw body spins before it gives up and FAILS.  Far wider than
#: any budget here, so a budget that does not cut is a loud red rather than a hung suite:
#: the failsafe is the test's own patience and never the instrument.
_FAILSAFE_SECONDS = 120.0


def _an_entry_point_that_does_not_finish():
    """An ``accept`` that spins in ORDINARY PYTHON until something cuts it.

    **A draw with no termination of its own, which is what the old fixture only claimed to
    be.**  The spin is pure Python, so the alarm lands between bytecodes in a frame this
    file owns and propagates immediately -- and it is reached through the real
    ``check_accepts``, the real ``hypothesis`` ``given`` machinery and the real draw, so the
    end-to-end path is the one under test.  There is nothing here for load to finish early:
    a loop that does not stop cannot be beaten to the exit.
    """

    def accept(payload: Any) -> Any:
        until = time.monotonic() + _FAILSAFE_SECONDS
        while time.monotonic() < until:
            pass
        raise AssertionError(
            f"the entry point spun for {_FAILSAFE_SECONDS} s and nothing cut it, so the "
            "budget did not bound the draw"
        )

    return accept


def _an_entry_point_that_raises(what: BaseException):
    def accept(payload: Any) -> Any:
        raise what

    return accept


def _raising(what: BaseException):
    """A stand-in for any callable on the path to the draw, raising ``what`` when reached."""

    def instead(*args: Any, **kwargs: Any) -> Any:
        raise what

    return instead


def test_a_budget_cut_reaches_the_caller_as_itself_and_never_as_a_verdict() -> None:
    """**The reading ``adcp-client-python-pjc``'s third part moves**, with no clock in it.

    ``check_accepts``' last clause catches "a model that raises something other than a
    ``ValidationError``" and spells it ``model_error``.  A budget cut used to arrive there
    like any other exception, so the verdict said the MODEL raised when what had happened
    was that this process stopped asking -- measured over the whole graded population at a
    20 s budget: 73 pairs reported ``accepts:model_error`` and every one of the 73 was a
    cut, which is 73 false reds in the column a reader scans for real ones.

    **An injected raise establishes exactly that, and a wall clock cannot.**  What the
    property says is that a :class:`harness.OverBudget` raised anywhere inside the draw
    machinery reaches the caller AS ITSELF, is held by nothing, and is never converted into
    a verdict about a document.  Where the exception comes from is immaterial to that
    sentence, and making it come from a timer adds a race and no coverage: on the old code
    an injected raise fails exactly as a timed one did, because what was wrong was
    ``OverBudget`` being an ``Exception``.

    **Both ENDS of the handler chain, because the chain is what the property is about.**
    ``check_accepts`` has four handlers between the caller and the draw -- ``_DumpRefused``,
    ``ValidationError``, the ``hypothesis`` family, and the broad ``Exception`` -- and
    ``hypothesis`` has its own between the body and the strategy.  The entry-point injection
    is raised INSIDE the drawn body, so it crosses every one of them; the strategy-build
    injection never reaches a draw at all, so it crosses the outermost only.  Either alone
    would pass over a defect in the other.

    Both halves of the original reading are kept: the cut arrives as a cut, and no enclosing
    ``except Exception`` sees it.
    """
    cut = harness.OverBudget("injected where the draw machinery would raise one")

    def reaches_the_caller(where: str, call) -> None:  # noqa: ANN001
        swallowed: Exception | None = None
        verdict: Any = None
        with pytest.raises(harness.OverBudget) as raised:
            try:
                verdict = call()
            except Exception as e:  # noqa: BLE001 -- the handler under judgement
                swallowed = e
        assert raised.value is cut, (
            f"the cut injected at {where} did not reach the caller as itself: "
            f"{raised.value!r}"
        )
        assert swallowed is None, (
            f"a budget cut injected at {where} was caught by an `except Exception` and "
            f"would have been reported as a verdict about the document: "
            f"{type(swallowed).__name__}: {swallowed}"
        )
        assert verdict is None, (
            f"a budget cut injected at {where} was turned into a verdict: {verdict}"
        )

    # Inside the drawn body: through hypothesis and all four of check_accepts' handlers.
    reaches_the_caller(
        "the entry point",
        lambda: harness.check_accepts(DOC, _an_entry_point_that_raises(cut), examples=1),
    )

    # At the strategy build, which is the first thing check_accepts does inside its try --
    # so the cut crosses the outermost handler without a draw happening at all.
    built = harness.strategy
    harness.strategy = _raising(cut)
    try:
        reaches_the_caller(
            "the strategy build",
            lambda: harness.check_accepts(DOC, lambda payload: payload, examples=1),
        )
    finally:
        harness.strategy = built


def test_the_real_alarm_cuts_a_draw_that_cannot_END_and_the_cut_is_still_a_cut() -> None:
    """The END-TO-END path, with the real ``SIGALRM`` -- and it is not the check above.

    The property is already established without a clock; this one exists so the wiring that
    delivers a cut in production is covered too: :func:`harness.within`'s repeating
    ``setitimer``, its handler, the restore on the way out, and ``OverBudget`` crossing the
    same handler chain when a TIMER rather than a test raises it.

    **The draw cannot end on its own, which is the whole of why this does not flake.**  The
    entry point spins in ordinary Python, so there is no ``Unsatisfiable``, no buffer
    overrun and no early return for load to bring forward -- the only thing that can end
    this call is the alarm.  Measured at 30 of 30 under 48-way CPU load, propagating in
    2.01 s every time, against the 2-in-30 of the fixture this replaces.

    The budget is small ON PURPOSE and the failsafe is what makes that safe: a budget that
    fails to cut costs ``_FAILSAFE_SECONDS`` and then reddens, rather than hanging.  Nothing
    here is a margin against contention -- see this section's note.
    """
    swallowed: Exception | None = None
    started = time.monotonic()
    with pytest.raises(harness.OverBudget):
        try:
            with harness.within(2):
                harness.check_accepts(DOC, _an_entry_point_that_does_not_finish(), examples=1)
        except Exception as e:  # noqa: BLE001 -- the handler under judgement
            swallowed = e
    assert swallowed is None, (
        f"a budget cut was caught by an `except Exception` and would have been reported as "
        f"a verdict about the document: {type(swallowed).__name__}: {swallowed}"
    )
    assert time.monotonic() - started < _FAILSAFE_SECONDS, (
        "the alarm did not cut the draw; the entry point's own failsafe did"
    )


def test_an_exception_raised_after_a_swallowed_cut_is_a_cut_and_not_a_verdict() -> None:
    """The door ``OverBudget``'s TYPE cannot close, and what came through it.

    Making a cut a ``BaseException`` stops an enclosing ``except Exception`` from reading
    the cut ITSELF as a verdict.  It does nothing when a frame between the alarm and the
    handler swallows the cut and raises its OWN exception in its place -- and
    ``hypothesis`` does that: the first cut lands inside a draw, ``hypothesis`` re-runs the
    strategy to see whether the failure reproduces, the second run diverges because the
    first was interrupted, and ``FlakyStrategyDefinition`` -- an ordinary ``Exception`` in
    the ``HypothesisException`` family -- is what reaches ``check_accepts``.

    **Measured, not supposed.**  Over all 2,793 graded pairs at a 20 s budget, single
    process: 2 pairs reported ``accepts:strategy_error``, both at 20.2 s against the 20 s
    budget, both with ``FlakyStrategyDefinition: Inconsistent data generation!`` as the
    whole of their detail -- ``core/signal-coverage-forecast.json#`` and
    ``media-buy/media-buy-commitment-response.json#/oneOf/0``.  Two facts about this
    process's clock, in the column that means the generator produced nothing for the
    schema.

    **The REAL alarm, and the swallow is the entry point's rather than a race.**  The entry
    point waits for the cut and catches it exactly as ``hypothesis``'s own
    ``except BaseException`` frames do, then raises a ``HypothesisException`` -- the
    sequence end to end, with the failsafe of this section making a budget that never
    fires cost ``_FAILSAFE_SECONDS`` and redden rather than hang.  It fails on the old code
    for the reason the figures above record and not for a timing reason.
    """
    from hypothesis.errors import FlakyStrategyDefinition

    swallowed_the_cut = [False]

    def entry_point(payload: Any) -> Any:
        until = time.monotonic() + _FAILSAFE_SECONDS
        while not swallowed_the_cut[0] and time.monotonic() < until:
            try:
                time.sleep(0.05)
            except harness.OverBudget:
                swallowed_the_cut[0] = True
        raise FlakyStrategyDefinition("Inconsistent data generation!")

    verdict: Any = None
    started = time.monotonic()
    with pytest.raises(harness.OverBudget):
        with harness.within(1):
            verdict = harness.check_accepts(DOC, entry_point, examples=1)
    assert swallowed_the_cut[0], "the fixture never reached the swallow it is about"
    assert verdict is None, (
        f"an exception raised after the cut was swallowed became a verdict about the "
        f"document: {verdict}"
    )
    assert time.monotonic() - started < _FAILSAFE_SECONDS, (
        "the alarm did not cut the draw; the entry point's own failsafe did"
    )


def test_a_grade_with_no_budget_reports_the_verdict_it_always_did() -> None:
    """The other side of :func:`harness.budget_expired`, so the clause is not a mute.

    A caller grading with no :func:`harness.within` around it -- every direct caller in
    this file -- must still get ``strategy_error`` for a generator that errors, because
    there is no clock for the exception to be an artefact of.  Without this the clause
    above could be satisfied by reporting every error as a cut.
    """
    from hypothesis.errors import FlakyStrategyDefinition

    def entry_point(payload: Any) -> Any:
        raise FlakyStrategyDefinition("Inconsistent data generation!")

    res = harness.check_accepts(DOC, entry_point, examples=1)
    assert res.outcome == "strategy_error", (
        f"with no budget active the generator's own error is still the verdict, "
        f"not a cut: {res.outcome}"
    )


# --------------------------------------------------------------------------- #
# the canonicalisation sharing, whose whole correctness is its lifetime
# --------------------------------------------------------------------------- #
def test_the_sharing_is_installed_for_one_call_and_restored_even_on_a_raise() -> None:
    """What separates this from the process-global memo section 6 deleted.

    The memo's defect was that it was unbounded, process-global and retained for the life
    of the process -- roughly 340 entries per pair across 1,055 pairs and ten workers,
    which pushed a run into a kernel kill.  The only thing keeping this from being that
    is its LIFETIME, so the lifetime is what is asserted, in both exits.
    """
    import hypothesis_jsonschema._canonicalise as canon  # noqa: PLC2701 -- the patched name

    before = canon.canonicalish
    with harness.canonicalisation_shared_within_one_call() as memo:
        assert canon.canonicalish is not before
        canon.canonicalish({"type": "string"})
        canon.canonicalish({"type": "string"})
        assert len(memo) == 1, "two identical calls, one entry"
    assert canon.canonicalish is before

    with pytest.raises(RuntimeError):
        with harness.canonicalisation_shared_within_one_call():
            raise RuntimeError("the body raised")
    assert canon.canonicalish is before, "a raise must not leave the library patched"


def test_a_hit_hands_back_a_copy_because_the_library_mutates_what_it_is_given() -> None:
    """The one thing a naive memo gets wrong, and it corrupts every later call.

    ``hypothesis_jsonschema`` mutates the nodes it is handed, so returning the held
    object would let one call's rewrite reach the next one's.  Graded by mutating the
    first result and asking for the same key again.
    """
    import hypothesis_jsonschema._canonicalise as canon  # noqa: PLC2701 -- the patched name

    with harness.canonicalisation_shared_within_one_call():
        first = canon.canonicalish({"type": "string", "minLength": 2})
        first["__scribbled_on__"] = True
        second = canon.canonicalish({"type": "string", "minLength": 2})
    assert "__scribbled_on__" not in second
