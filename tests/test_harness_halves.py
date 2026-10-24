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

Hand-written documents and not bundle ones, because the bundle has no faithful/widened
pair to compare: these are three classes over one document, differing in one axis each.
"""

from __future__ import annotations

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
    renderer -- so the accepts half, the liveness check and the schema comparison all
    pass it.  The dump is what separates them.
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
