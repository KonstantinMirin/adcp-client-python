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

import json
from typing import Any

import jsonschema
import pytest
from pydantic import BaseModel, ConfigDict

from adcp.types._base import SchemaRef, _refuse  # the production schema half
from codegen import harness
from codegen.verify import witness

#: One object document that demands both of its keys and admits no others, so each
#: perturbation below has exactly one thing to break.
DOC: dict[str, Any] = {
    "type": "object",
    "required": ["a", "b"],
    "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
    "additionalProperties": False,
}

#: **WHAT ``examples=N`` BECAME, and it is a different kind of argument.**
#: ``check_accepts`` took ``examples: int`` and DREW that many instances; it now takes
#: ``witness: Sequence[Any]`` and is handed them, because
#: :class:`codegen.verify.witness.Construction` constructs the witness and the check grades
#: it -- *"no corpus, no cache, no budget, no depth cap, no example count"*.  A count is a
#: knob that can turn a check off; a witness list is the thing being graded.
#:
#: Handed ``witness=None`` the check returns ``no_witness`` at once and never calls
#: ``accept`` at all, which is why every clause below that needed the callee to be REACHED
#: had to be re-pointed rather than left: an ``examples=`` call grades nothing now.
#: Three instances, so a clause that counts has something to count.
A_WITNESS: tuple[dict[str, Any], ...] = (
    {"a": "x", "b": 1},
    {"a": "y", "b": 2},
    {"a": "z", "b": 3},
)


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

    The instances are HANDED here (:data:`A_WITNESS`) rather than drawn; the dump half is
    unchanged and is what this clause is about.
    """
    assert harness.check_accepts(DOC, accept_of(Faithful), witness=A_WITNESS).outcome == "pass"
    lossy = harness.check_accepts(DOC, accept_of(DropsB), witness=A_WITNESS)
    assert lossy.outcome == "model_dropped_a_fact", lossy.detail
    # The CAUSE comes first, because ``detail`` is truncated and a reason behind a
    # megabyte of dumped instance is a reason nothing can read.
    assert lossy.detail.startswith("the document refuses the dump on required"), lossy.detail
    assert lossy.round_tripped == 0


def test_a_round_tripped_instance_is_counted_and_an_unreported_one_is_not() -> None:
    """The denominator the pair's verdict reads, and it counts dumps rather than draws.

    ``PairReport.graded_instances`` is this number, and ``PairReport.outcome`` turns a
    zero into a refusal: a pair handed instances that dumped none back out to something
    the document admits was graded by nothing.

    **It counts dumps rather than DRAWS, and now there are no draws to confuse it with** --
    the denominator is the witness it was handed, so ``examples`` and ``round_tripped``
    being equal says every instance offered survived the round trip.
    """
    passing = harness.check_accepts(DOC, accept_of(Faithful), witness=A_WITNESS)
    assert passing.examples == len(A_WITNESS)
    assert passing.round_tripped == len(A_WITNESS)


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
def _an_entry_point_that_raises(what: BaseException):
    def accept(payload: Any) -> Any:
        raise what

    return accept


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

    **THE CHAIN IS WHAT THE PROPERTY IS ABOUT, and only one end of it still exists.**
    ``check_accepts`` has four handlers between the caller and ``accept`` --
    ``_DumpRefused``, ``ValidationError``, the ``hypothesis`` family, and the broad
    ``Exception`` -- and the entry-point injection is raised INSIDE the body, so it crosses
    every one of them.  There was a second injection at the STRATEGY BUILD, which crossed
    the outermost handler alone; ``harness.strategy`` does not exist, because the witness is
    constructed and no strategy is built, so that half had no subject and is gone.  What is
    kept is the half that crosses the whole chain, which is the stronger of the two.

    Both halves of the original reading are kept: the cut arrives as a cut, and no enclosing
    ``except Exception`` sees it.
    """
    cut = harness.OverBudget("injected where the draw machinery would raise one")

    def reaches_the_caller(where: str, call) -> None:
        swallowed: Exception | None = None
        verdict: Any = None
        with pytest.raises(harness.OverBudget) as raised:
            try:
                verdict = call()
            except Exception as e:  # the handler under judgement
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

    # Inside the body, where ``accept`` runs: through all four of check_accepts' handlers.
    reaches_the_caller(
        "the entry point",
        lambda: harness.check_accepts(DOC, _an_entry_point_that_raises(cut), witness=A_WITNESS),
    )


#: **``test_a_grade_with_no_budget_reports_the_verdict_it_always_did`` STOOD HERE AND ITS
#: SUBJECT IS GONE.**  It asserted that a ``FlakyStrategyDefinition`` raised with no
#: :func:`harness.within` active still reports ``strategy_error`` rather than a cut, and it
#: existed so that :func:`harness.budget_expired` was not a mute -- the clause above could
#: otherwise be satisfied by reporting every error as a cut.
#:
#: Both halves of that have left.  ``check_accepts`` now carries THREE handlers --
#: ``_DumpRefused``, ``ValidationError`` and the broad ``Exception`` -- and the
#: ``hypothesis``-family handler that produced ``strategy_error`` is not among them,
#: because no strategy is built: the witness is constructed and handed in.  So the verdict
#: for that input is ``model_error``, which is the honest answer and not a regression --
#: there is no generator for the error to be attributed to.  And
#: :func:`harness.budget_expired` has **no caller anywhere in the tree**; its only
#: remaining references are a comment in ``harness.py`` and the docstring that stood here.
#:
#: The clause the budget still OWES is the one above, and it is live:
#: :class:`harness.OverBudget` is a ``BaseException`` precisely so the broad ``except
#: Exception`` does not convert a cut into a verdict about a document, and that handler is
#: still there.  See ``verdicts/gates-read-the-witness.md`` on removing the rest.


# --------------------------------------------------------------------------- #
# the DOCUMENT's own statement of a valid instance: `examples`
# --------------------------------------------------------------------------- #
def test_an_examples_member_its_own_node_REFUSES_is_not_an_instance() -> None:
    """The screen, which is the whole of the rule and is not a formality.

    **Measured over the graded population: 115 pairs' node carries ``examples`` and the
    node refuses every member of 64 of them**, because the bundle's root ``examples`` hold
    ``{"description", "data"}`` rather than the instance -- and all 64 hold a valid
    instance under ``data``, so the member is wrapped and not wrong.  The wrapper is NOT
    unwrapped: draft-07 says a member IS an instance, and reading a key out of one would
    make the harness interpret a convention the specification does not have.  So the
    member is refused, the pair draws as before, and the repair is upstream.
    """
    wrapped = {
        "type": "object",
        "required": ["a"],
        "properties": {"a": {"type": "string"}},
        "examples": [{"description": "what this shows", "data": {"a": "x"}}],
    }
    assert harness.stated_instances(wrapped) == [], (
        "a {description, data} wrapper was read as an instance"
    )
    assert harness.stated_instances({"type": "string"}) == []
    mixed = {
        "type": "object",
        "required": ["a"],
        "properties": {"a": {"type": "string"}},
        "examples": [{"nope": 1}, {"a": "good"}, {"a": 2}],
    }
    assert harness.stated_instances(mixed) == [{"a": "good"}], (
        "the screen kept a member the node refuses, or dropped one it admits"
    )


# --------------------------------------------------------------------------- #
# the PIN memo's key: what the statements ADMIT, never their text
# --------------------------------------------------------------------------- #
def test_two_statements_that_admit_alike_share_one_pin_however_they_are_annotated() -> None:
    """**An annotation-only edit must not re-bucket the fixture memo.**

    ``harness._content_key`` is the key ``Fixtures._pin`` memoises on, and the memo decides
    WHICH VALUE is pinned at a fixture position.  Keyed on the raw text -- which it was,
    ``json.dumps(list(nodes), sort_keys=True)`` -- two statements that admit exactly the
    same instances stopped sharing one derivation the moment one of them gained a
    ``description``, so a different value was drawn and pinned: ``adcp-client-python-lzzj.8``
    measured that as **two of the six pairs the patch was blamed for flipping verdict on a
    node that is byte-identical between the two bundles**.

    ``docs/plan/final-state.md`` reading 1 is the rule and it does not stop at the corpus
    key: "A stored value, a key over a document's bytes, or any artifact that must be
    re-derived when the bundle moves makes an improvement to the schema cost exactly as
    much as a regression."

    Three claims, and the third is what keeps this from being a key that cannot tell
    anything apart:

    1. a gained ``title``/``description``/``examples``/``$comment`` -- and a gained ``x-``
       extension, which §6 admits by PREFIX -- moves the key for none of them;
    2. the TEXT of those nodes really did differ, so the gate is not green on two equal
       inputs;
    3. a changed CONSTRAINT still moves it, and so does the ``kind`` beside it.
    """
    plain = {"type": "string", "maxLength": 4}
    annotated = {
        "type": "string",
        "maxLength": 4,
        "title": "A Name",
        "description": "what it is",
        "examples": ["abcd"],
        "$comment": "a note",
        "x-vendor-fact": {"anything": True},
    }
    narrower = {"type": "string", "maxLength": 3}

    assert harness._content_key([plain]) == harness._content_key([annotated]), (
        "an annotation re-bucketed the pin memo"
    )
    # 2. the gate is not green on two equal inputs.
    assert json.dumps(plain, sort_keys=True) != json.dumps(annotated, sort_keys=True)

    # 3. a constraint still moves it, and so does the kind.
    assert harness._content_key([plain]) != harness._content_key([narrower])
    assert harness._content_key([plain], kind=b"const") != harness._content_key([plain])

    # Nested, because the strike has to reach every depth: the annotation is inside a
    # properties entry here and the two objects admit identically.
    assert harness._content_key(
        [{"type": "object", "properties": {"a": plain}}]
    ) == harness._content_key([{"type": "object", "properties": {"a": annotated}}])


def test_a_definitions_section_stays_in_the_pin_key_because_nothing_resolves_it() -> None:
    """**The one place this key is NOT ``catalogue.Admitted``, and why it must not be.**

    That class drops a ``definitions`` section because it RESOLVES a ``$ref`` before
    keying, so the section is already in the key at every referring site.  The pin memo
    resolves nothing -- its nodes are statements lifted out of one already-inlined record,
    where a local ``$ref`` into the record's own storage is still a ``$ref``.  Dropping the
    section while keeping the reference string would make two nodes that spell one pointer
    and store two different subtrees under it collide, and the memo would hand one the
    other's pin: a WRONG value, not a coarse key.
    """
    one = {
        "$ref": "#/definitions/x",
        "definitions": {"x": {"type": "string", "maxLength": 4}},
    }
    other = {
        "$ref": "#/definitions/x",
        "definitions": {"x": {"type": "integer", "minimum": 7}},
    }
    assert harness._content_key([one]) != harness._content_key([other]), (
        "two nodes storing different subtrees under one pointer share a pin bucket"
    )


# --------------------------------------------------------------------------- #
# adcp-client-python-hzio.3: the validator INSTANCE, and the message nobody reads
# --------------------------------------------------------------------------- #
#: Documents whose readings are the ones ``codegen.verify.witness.QUIET`` replaces, with a
#: value each that the document REFUSES -- so the comparison below is over errors and not
#: over an empty set.  One per quieted keyword, because what is being judged is that each
#: substitution answers exactly what the library's own reading answers.
QUIETED: tuple[tuple[dict, Any], ...] = (
    ({"type": "string"}, 7),
    ({"type": ["string", "integer"]}, []),
    ({"enum": ["a", "b"]}, "c"),
    ({"const": "a"}, "b"),
    ({"not": {"type": "string"}}, "a"),
    ({"type": "array", "contains": {"type": "integer"}}, ["a"]),
    ({"anyOf": [{"type": "string"}, {"type": "integer"}]}, []),
    ({"oneOf": [{"type": "string"}, {"type": "integer"}]}, []),
    #: A value TWO branches of a ``oneOf`` admit, which is the shape whose message is the
    #: single largest allocation site in the library's half of a run
    #: (``adcp-client-python-2i99``: 12.103 GB) -- it ``repr``\ s every branch the instance
    #: satisfies.  The verdict must still be a refusal, because that is the keyword's
    #: semantics and not its sentence.
    ({"oneOf": [{"type": "string"}, {"minLength": 0}]}, "a"),
    #: Nested, so the comparison reaches an error carried in ``context`` rather than only a
    #: top-level one.
    (
        {
            "type": "object",
            "properties": {"a": {"oneOf": [{"type": "string"}, {"type": "integer"}]}},
        },
        {"a": []},
    ),
)


@pytest.mark.parametrize("schema,value", QUIETED, ids=lambda x: str(x)[:48])
def test_the_quiet_reading_answers_what_the_librarys_own_reading_answers(
    schema: dict, value: Any
) -> None:
    """``hzio.3``'s message clause, and what makes it SAFE rather than merely cheap.

    ``harness._reading`` replaces the readings whose MESSAGE renders the instance or a
    subschema, because :func:`codegen.harness.conforms` returns a ``bool`` and
    :func:`codegen.harness.violated_keywords` reads ``err.validator`` -- measured at
    369,389,071 bytes of message built over the suite's grading pass of this tree, every
    byte discarded.  **What must not change is the verdict**, so the two classes are asked
    the same question and compared on the pair the callers read: the keyword and the path.
    """
    library = jsonschema.Draft7Validator(schema, format_checker=None)
    quiet = harness.quiet(jsonschema.Draft7Validator)(schema, format_checker=None)

    def read(validator: Any) -> list[tuple[Any, tuple]]:
        return sorted(
            (err.validator, tuple(err.absolute_path))
            for err in validator.iter_errors(value)
        )

    assert read(quiet) == read(library), (read(quiet), read(library))
    assert read(library), "the fixture states no refusal, so the comparison is vacuous"
    assert harness.conforms(schema, value) is False

    #: **AND THE ``context`` TOO, because that is the half the pair above does not reach.**
    #: :func:`codegen.harness.violated_keywords` reads ``err.validator`` and then every
    #: ``e.validator`` of ``err.context``, which is where an ``anyOf``'s and a ``oneOf``'s
    #: branch refusals live -- so a quiet reading that dropped the context would answer a
    #: shorter list and the attribution of a refusal would move.  Compared against the
    #: library's own answer and not against a list written here.
    def keywords(validator: Any) -> list[str]:
        out = []
        for err in validator.iter_errors(value):
            for e in [err, *err.context] if err.context else [err]:
                if isinstance(e.validator, str):
                    out.append(e.validator)
        return sorted(set(out))

    assert keywords(quiet) == keywords(library), (keywords(quiet), keywords(library))
    assert harness.violated_keywords(schema, value) == keywords(library), schema


def test_no_message_is_rendered_on_the_path_whose_caller_discards_it() -> None:
    """The saving itself, measured rather than asserted in prose.

    The subject is the ``oneOf`` shape ``adcp-client-python-2i99`` names: an instance TWO
    branches admit, whose library message is ``", ".join(repr(schema) for schema in
    more_valid)`` over whole merged subschema dicts.  The branches here are padded so that
    the library's own sentence is large and the quiet one is a constant, and the comparison
    is of the TOTAL message text each class builds for one call.
    """
    filler = {"description": "x" * 4000}
    schema = {"oneOf": [{"type": "string", **filler}, {"minLength": 0, **filler}]}
    built: list[int] = []
    original = jsonschema.exceptions.ValidationError.__init__

    def counting(self: Any, message: str, *a: Any, **k: Any) -> None:
        built.append(len(message) if isinstance(message, str) else 0)
        original(self, message, *a, **k)

    jsonschema.exceptions.ValidationError.__init__ = counting  # type: ignore[method-assign]
    try:
        built.clear()
        list(jsonschema.Draft7Validator(schema).iter_errors("a"))
        library = sum(built)
        built.clear()
        list(harness.quiet(jsonschema.Draft7Validator)(schema).iter_errors("a"))
        quiet = sum(built)
    finally:
        jsonschema.exceptions.ValidationError.__init__ = original  # type: ignore[method-assign]
    assert library > 8000, library
    assert quiet < 200, quiet


def test_the_validator_instance_is_shared_within_one_grade_and_dropped_on_the_way_out() -> None:
    """``hzio.3``'s first DONE WHEN clause on the HARNESS path, read off the counters.

    ``docs/plan/architecture.md`` §9: the registry and the resolver are the DOCUMENT's and
    not a visit's.  ``jsonschema >= 4.18`` builds both on a ROOT construction alone, so a
    validator built per call rebuilt them per call -- measured at 162,727 root constructions
    over the suite's grading pass of 2,584 pairs.

    Three obligations: the second ask of one schema REUSES, the lifetime is the block (so a
    caller outside one is answered exactly as before this row), and the memo is dropped on
    the way out including on a raise.
    """
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    harness.VALIDATOR_COUNTERS.clear()
    with harness.validator_instances_shared_within_one_grade() as memo:
        assert harness.conforms(schema, {"a": "x"}) is True
        assert harness.conforms(schema, {"a": 1}) is False
        assert harness.conforms(schema, {"a": "y"}) is True
        assert memo, "nothing was held for the grade"
        assert harness.VALIDATOR_COUNTERS["reused"] >= 2, dict(harness.VALIDATOR_COUNTERS)
    assert harness._VALIDATORS is None
    assert harness._PINNED is None
    # Outside a block the answer is what it always was: a fresh root, counted as unshared.
    harness.VALIDATOR_COUNTERS.clear()
    assert harness.conforms(schema, {"a": "x"}) is True
    assert harness.VALIDATOR_COUNTERS["unshared"] >= 1, dict(harness.VALIDATOR_COUNTERS)
    assert harness.VALIDATOR_COUNTERS["reused"] == 0, dict(harness.VALIDATOR_COUNTERS)

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with harness.validator_instances_shared_within_one_grade():
            harness.conforms(schema, {"a": "x"})
            raise Boom
    assert harness._VALIDATORS is None, "the memo outlived the grade that opened it"


def test_the_sharing_is_reentrant_so_one_grade_holds_one_memo() -> None:
    """A nested opening joins the outer memo rather than starting a second one.

    Two memos inside one grade would make the sharing a function of which frame asked, and
    the inner frame would re-build every validator the outer one already holds -- which is
    the defect, one level down.
    """
    with harness.validator_instances_shared_within_one_grade() as outer:
        with harness.validator_instances_shared_within_one_grade() as inner:
            assert inner is outer
        # And the inner exit did not drop the outer memo.
        assert harness._VALIDATORS is outer
    assert harness._VALIDATORS is None


def test_the_grade_opens_the_validator_sharing_for_every_pair_it_checks() -> None:
    """``check_pair`` is the frame that knows a grade has begun, so it is where it opens.

    Read off the SHARING and not off a count: a pair graded with no sharing open would
    report every ask as ``unshared``, which is exactly the shape the row repairs.

    **AND THE PAIR MUST BE GIVEN A CONSTRUCTION, or the grade asks for no validator at
    all.**  This clause measured ``reused == 0`` and read as a defect in the sharing.  It
    is not one: handed no ``construction=``, ``check_accepts`` returns ``no_witness``
    before it validates anything and the admits check reports *"no construction was
    supplied, so there is no witness set"*, so a pair graded without one does almost
    nothing and shares nothing because nothing was asked.  The sharing is live; what had
    gone stale was the FIXTURE, which still described a grade that drew its own instances.

    A one-document construction rather than the bundle's, because what is under test is the
    lifetime of the memo and not any document's content -- and a clause that needed the
    whole bundle warmed would be measuring ``tests_emit/constructed.py``.
    """
    document = "one.json"
    schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}}}

    class One(BaseModel):
        a: str

    harness.VALIDATOR_COUNTERS.clear()
    harness.check_pair(
        harness.Pair(
            name="shared",
            schema=schema,
            model=One,
            accept=One.model_validate,
            ref=SchemaRef(document, "#"),
        ),
        construction=witness.Construction({document: schema}),
    )
    assert harness.VALIDATOR_COUNTERS["reused"] > 0, dict(harness.VALIDATOR_COUNTERS)
    assert harness._VALIDATORS is None, "check_pair left its memo open"


def test_the_quiet_class_is_built_once_per_draft_and_not_once_per_call() -> None:
    """The defect the first cut of ``hzio.3`` introduced, read back as a gate.

    ``jsonschema.validators.extend`` is 0.295 ms against 0.0026 ms for a plain validator
    instance -- 113x -- so a ``quiet`` that rebuilt the class per call would add about 14 s
    to the 48,287 ``conforms`` asks this suite makes outside any grade.  Asserted as
    IDENTITY and not as a timing, because identity is what the saving is.
    """
    first = harness.quiet(jsonschema.Draft7Validator)
    assert harness.quiet(jsonschema.Draft7Validator) is first
    with harness.validator_instances_shared_within_one_grade():
        assert harness.quiet(jsonschema.Draft7Validator) is first
    assert harness.quiet(jsonschema.Draft7Validator) is first
    # And the cache is bounded by the DRAFT, so it holds no document and cannot grow with
    # the population -- which is the property section 6's rule is actually about.
    assert len(harness._QUIET_CLASSES) <= 4, sorted(
        getattr(c, "__name__", repr(c)) for c in harness._QUIET_CLASSES
    )
    assert all(isinstance(key, type) for key in harness._QUIET_CLASSES)
