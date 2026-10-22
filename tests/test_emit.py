"""Grade the committed emitted tree against the documents it was emitted from.

Every assertion here is over something DERIVED: the population comes from the
bundle, the pairs come from the classes' own ``__adcp_schema__``, and the verdict
comes from the harness.  There is no expected class list, no snapshot and no
blessed value, so a test that passes cannot be passing because someone recorded
what the tree happened to hold (P10).

**There is no adapter and no binding table.**  Both existed to tell the harness
which document a class was generated from, and an indirection that can be aimed
at a tree can be aimed at the WRONG tree -- which is how a previous attempt came
to grade 1,602 documents green while generating nothing.  Now a class carries its
own schema reference, so ``pairs`` reads the pairing off the class and the
"grading someone else's tree" failure has no site.  What remains is a STALE
module -- one an earlier run wrote and no current document produces -- and that
is caught where P10 puts a check: ``test_the_committed_tree_is_what_a_fresh_run_emits``
compares the whole tree with a fresh emission of the derived population, so a file
no run produces is a failure at the gate.

The bundle directory is a constant here and nowhere inside ``codegen/``: step 10
derives it from ``adcp.get_adcp_spec_version()`` (D9, P9).
"""

from __future__ import annotations

import ast
import functools
import importlib
import json
import os
import pkgutil
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any, NamedTuple

import jsonschema
import pytest
from hypothesis import given, HealthCheck, Phase, settings
from hypothesis import strategies as st
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from adcp.types._base import AdCPBaseModel, REGEX_ENGINE, SchemaRef, schema_at
from codegen import bundle, emit
from codegen.harness import (
    AcceptsResult,
    check_accepts,
    ComparisonResult,
    Pair,
    PairReport,
    RefusesResult,
    check_pair,
    compare_schema,
    conforms,
    steps,
    violated_keywords,
)

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
TREE = REPO / emit.TREE


def leaves() -> list[str]:
    """Step 1's population: an object root with no reference anywhere in it."""
    return [d for d in bundle.portable(BUNDLE) if bundle.is_leaf_object(bundle.read(BUNDLE, d))]


def referencing() -> list[str]:
    """Step 2's population: every reference is a property's own schema or its items."""
    return [
        d for d in bundle.portable(BUNDLE) if bundle.references_a_property(bundle.read(BUNDLE, d))
    ]


def population() -> list[str]:
    """What the committed tree is emitted from.  A reference TARGET is not here and
    does not need to be: ``emit`` walks ``$ref`` and emits the closure."""
    return sorted(set(leaves()) | set(referencing()))


# --------------------------------------------------------------------------- #
# the pairs, read off the classes themselves
# --------------------------------------------------------------------------- #
class Graded(NamedTuple):
    ref: SchemaRef
    model: Any
    accept: Any
    module: str


def graded() -> list[Graded]:
    """Every class and alias the tree carries, with the schema each one names.

    The whole of the pairing.  A class is taken only from the module that DEFINES
    it (``__module__``), because a referencing module imports its target's symbol
    and the same class would otherwise be graded once per importer.

    An alias is D2's root-scalar row: it is not a class, so its MODULE carries
    the ``__adcp_schema__`` and the ``strict_validate``, and the model is the one
    name the module exports.  Both cases are asserted non-empty below, so neither
    is graded by an empty loop.
    """
    import adcp.types._schemas as pkg

    out: list[Graded] = []
    for info in sorted(pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."), key=lambda i: i.name):
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, AdCPBaseModel)
                and "__adcp_schema__" in value.__dict__
                and value.__module__ == info.name
            ):
                out.append(Graded(value.__adcp_schema__, value, value.strict_validate, info.name))
        ref = vars(module).get("__adcp_schema__")
        if isinstance(ref, SchemaRef) and callable(vars(module).get("strict_validate")):
            (symbol,) = module.__all__
            out.append(Graded(ref, getattr(module, symbol), module.strict_validate, info.name))
    return out


def pair_of(g: Graded) -> Pair:
    return Pair(
        name=f"{g.ref.document}{g.ref.pointer}",
        schema=schema_at(g.ref),
        model=g.model,
        accept=g.accept,
    )


PAGINATION = "core/pagination-request.json"

#: ``Field`` kwargs that state no constraint: a name (``alias``), a presence
#: default, and the two annotations the document carries and the compiler
#: transcribes.  Everything else a ``Field`` can carry narrows a value, so a
#: kwarg outside this set has to be one the document declares locally.
ANNOTATION_KWARGS = frozenset({"alias", "default", "description", "json_schema_extra"})


def pagination() -> Graded:
    return next(g for g in graded() if g.ref == SchemaRef(PAGINATION, "#"))


# --------------------------------------------------------------------------- #
# the population and the arithmetic over it
# --------------------------------------------------------------------------- #
def test_the_population_is_the_one_the_step_is_stated_over() -> None:
    """A verdict read off a population nobody counted is a verdict over however
    many documents there turned out to be, including none.

    **The bundle's size is read from the bundle**, never written here: it is a
    property of the bundle version and the directory is an argument (D11), so a
    literal total would be an assertion about one checkout of one version.  What
    IS pinned is this step's own population, because that is the denominator the
    step's result is stated over -- a silent change to the selectors would
    otherwise move the result without moving any number anyone reads.
    """
    whole = bundle.portable(BUNDLE)
    assert len(leaves()) == 85
    assert len(referencing()) == 249
    assert len(population()) == 334
    assert set(population()) < set(whole), "the step's population is not a part of the bundle"
    assert PAGINATION in leaves()
    assert "error-details/creative-revision-content-mismatch.json" in referencing()


def test_every_named_document_is_either_emitted_or_refused_by_name_and_keyword() -> None:
    out = emit.emit(BUNDLE, population())
    assert set(population()) <= set(out.emitted) | set(out.refusals)
    assert not set(out.emitted) & set(out.refusals)
    for document, row in out.refusals.items():
        assert row["keyword"] and row["pointer"], document


def test_a_reference_target_is_emitted_even_though_no_one_named_it() -> None:
    """Transitive emission, and that the walk terminates: the whole closure of a
    document's references is emitted, or the document is refused with the target
    that stopped it.  An import of a symbol from a module no run wrote is an
    ImportError, so there is no third outcome."""
    out = emit.emit(BUNDLE, population())
    pulled_in = set(out.emitted) - set(population())
    assert pulled_in, "no document was reached through a reference; the walk graded nothing"
    assert "core/creative-revision-id.json" in pulled_in
    # every reference of every emitted document resolves to a document also emitted
    known = set(bundle.portable(BUNDLE))
    for document in out.emitted:
        for _, uri in bundle.references(bundle.read(BUNDLE, document)):
            target = bundle.document_for(uri, known)
            assert target in out.emitted, (document, uri)


def test_the_pairing_is_intrinsic_to_every_class_the_tree_carries() -> None:
    """§2: the class names its schema, so nothing aims the grader at a tree.

    Three things, all derived:

    * every class and alias in the tree names a document THIS run emitted, so no
      module survives from a run over a different population;
    * every emitted document has exactly one ROOT pair, so N is a count of
      documents and not of classes;
    * a nested class names its own node and not its document's root, because a
      nested class is a subschema (and the previous arrangement could not bind
      one at all -- a nested class had no row and so no ``strict_validate``).
    """
    emitted = set(emit.emit(BUNDLE, population()).emitted)
    rows = graded()
    assert {g.ref.document for g in rows} == emitted
    roots = [g for g in rows if g.ref.pointer == "#"]
    assert sorted(g.ref.document for g in roots) == sorted(emitted)
    nested = [g for g in rows if g.ref.pointer != "#"]
    assert nested, "no nested class was emitted; the pointer case is graded by nothing"
    for g in nested:
        assert schema_at(g.ref) != schema_at(SchemaRef(g.ref.document, "#")), g.ref
    aliases = [g for g in rows if not isinstance(g.model, type)]
    assert aliases, "no root-scalar alias was emitted; that case is graded by nothing"


# --------------------------------------------------------------------------- #
# the three checks
# --------------------------------------------------------------------------- #
def test_pagination_request_passes_all_three_checks() -> None:
    """Step 1's own document, over EVERY constraint site it has.

    The refuses check's denominator is asserted, not just the verdict: a green
    mark without the count beside it says nothing, because a pair no instance
    reached reports no failure either.
    """
    rep = check_pair(pair_of(pagination()), max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.step_sites == 3, rep.step_sites  # minimum, maximum, additionalProperties
    assert [r.outcome for r in rep.refuses] == ["pass"] * 3
    assert rep.graded_instances == 75, rep.graded_instances
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.differs)
    assert rep.comparison.compared == 10, rep.comparison.compared
    assert rep.outcome == "pass"


def test_the_compiler_carries_what_the_document_says_and_a_text_emitter_dropped() -> None:
    """By introspection, not by reading the emitted text.

    These are the facts the schema comparison exists to grade, named here one at
    a time so a failure says WHICH one moved.  All four were dropped by the
    hand-rolled renderer this step replaces, and all four come out of the
    compiler for free.
    """
    model = pagination().model
    schema = schema_at(SchemaRef(PAGINATION, "#"))

    assert model.model_fields["max_results"].default == schema["properties"]["max_results"]["default"]
    assert model.model_fields["max_results"].default == 50
    assert {
        name: field.description for name, field in model.model_fields.items()
    } == {name: node["description"] for name, node in schema["properties"].items()}
    emitted = model.model_json_schema()["properties"]["max_results"]["anyOf"][0]
    assert (emitted["minimum"], emitted["maximum"]) == (
        schema["properties"]["max_results"]["minimum"],
        schema["properties"]["max_results"]["maximum"],
    )
    assert model.model_config["extra"] == "forbid"  # D7, from additionalProperties: false
    assert model.__adcp_schema__ == SchemaRef(PAGINATION, "#")


def test_the_schema_comparison_grades_the_generated_code_and_the_other_two_do_not() -> None:
    """The measurement that forces the schema comparison, as a test not a note.

    A model with ``Any`` on every field is wider than its document in every way
    an annotation can be.  Graded through the PRODUCTION entry point -- which
    validates against the document and only then constructs, and is therefore the
    only entry point grading acceptance says anything about -- it is
    indistinguishable from a faithful model: the accepts check passes, all three
    steps of the refuses check pass, and the denominator is the SAME 75 instances
    the faithful model is graded over.  The schema half refuses every stepped
    instance, so the verdict is the schema's and the annotations are never
    consulted.

    **That is strictly worse than the specification's §6 states, and the
    correction matters.**  §6 records this as a pass "with a refuses-check
    denominator of zero instances", which would make the zero-denominator rule
    enough to catch it.  It is not: the zero came from the probe's own
    hand-rolled entry point raising ``jsonschema.ValidationError`` (which
    ``check_refuses`` does not catch, so every step reported ``harness_error``)
    while the probe's verdict read ``accepted_invalid == 0`` as green.  Measured
    both ways in the same process: the FAITHFUL model gets the same zero through
    that wrapper, so the zero was a property of the wrapper and not of the model.
    Through the real one, both models get 75.  So the schema comparison is not a
    second opinion -- it is the only thing that separates them.

    Falsifiable here: delete the comparison and a wide model passes this file.
    """
    schema = schema_at(SchemaRef(PAGINATION, "#"))

    class Wide(AdCPBaseModel):
        __adcp_schema__ = SchemaRef(PAGINATION, "#")
        model_config = {"extra": "forbid"}
        max_results: Any = None
        cursor: Any = None

    wide = check_pair(
        Pair(name="wide", schema=schema, model=Wide, accept=Wide.strict_validate), max_steps=None
    )
    faithful = check_pair(pair_of(pagination()), max_steps=None)

    assert wide.accepts.outcome == faithful.accepts.outcome == "pass"
    assert [r.outcome for r in wide.refuses] == [r.outcome for r in faithful.refuses] == ["pass"] * 3
    assert wide.graded_instances == faithful.graded_instances == 75

    assert faithful.comparison.outcome == "pass"
    assert wide.comparison.outcome == "model_drops_a_fact"
    missing = {m.split(":")[0] for m in wide.comparison.missing}
    assert {
        "/properties/max_results/type",
        "/properties/max_results/minimum",
        "/properties/max_results/maximum",
    } <= missing
    # ``Any = None`` STATES a default, it just states the wrong one, so it is a
    # difference and not an omission -- and the comparison has to tell those apart,
    # because "the model says nothing" and "the model says something else" point
    # at different defects in the walk.
    assert "/properties/max_results/default: the document says 50, the model None" in wide.comparison.differs


def test_a_zero_refuses_check_denominator_is_not_reportable_as_a_pass() -> None:
    """The other half of the rule, and it needs its own fixture.

    The rule is right -- a pair no instance reached is graded by nothing in the
    refuses check -- and the test above shows it is not what catches a wide
    model.  So it is graded here on the thing that does produce a zero
    denominator: an entry point that refuses with an exception
    ``check_refuses`` does not catch, which is what the specification's own probe
    did.  Every step reports ``harness_error``, the denominator is 0, and the
    pair's verdict is a refusal rather than a pass.
    """
    schema = schema_at(SchemaRef(PAGINATION, "#"))
    model = pagination().model

    def foreign_error(payload: Any) -> Any:
        jsonschema.validate(payload, schema)  # raises jsonschema's error, not pydantic's
        return model.model_validate(payload)

    rep = check_pair(
        Pair(name="foreign", schema=schema, model=model, accept=foreign_error), max_steps=None
    )
    assert [r.outcome for r in rep.refuses] == ["harness_error"] * 3
    assert rep.graded_instances == 0
    assert rep.outcome.startswith("refuses:harness_error")


def test_the_two_zero_denominator_verdicts_are_never_pass() -> None:
    """The rule itself, on a report built to have a zero denominator.

    The test above reaches the zero through an entry point that errors, so the
    verdict it gets is ``refuses:harness_error`` and the two remaining branches
    -- the ones that say "nothing reached the model and nothing went wrong" --
    are not exercised by it.  No document in this population produces them with
    every step healthy, so they are graded here on a report rather than on a
    pipeline, which is the right level: the rule is a property of
    ``PairReport``.

    Both are asserted to be something other than ``pass``, so deleting either
    branch fails this test rather than silently turning a pair nothing reached
    into a green mark.
    """
    ok = AcceptsResult(examples=25, outcome="pass")
    fine = ComparisonResult(compared=7)

    nothing_to_step = PairReport(name="n", accepts=ok, comparison=fine, refuses=[], step_sites=0)
    assert nothing_to_step.graded_instances == 0
    assert nothing_to_step.outcome == "no_constraint_to_step"

    control_fired = PairReport(
        name="c",
        accepts=ok,
        comparison=fine,
        refuses=[RefusesResult(keyword="minimum", pointer="/", examples=25, control_fired=25)],
        step_sites=1,
    )
    assert control_fired.refuses[0].outcome == "no_evidence"
    assert control_fired.graded_instances == 0
    assert control_fired.outcome == "no_refuses_check_evidence"

    # ... and one instance reaching the model is the whole difference.
    reached = PairReport(
        name="r",
        accepts=ok,
        comparison=fine,
        refuses=[RefusesResult(keyword="minimum", pointer="/", examples=25, refused=1)],
        step_sites=1,
    )
    assert reached.graded_instances == 1
    assert reached.outcome == "pass"


def test_the_pairs_with_no_constraint_to_step_are_the_documents_that_state_none() -> None:
    """Which pairs take the ``no_constraint_to_step`` exit, and why.

    The population test counts them; this one says they are the documents whose
    own content leaves ``steps()`` nothing to do, read off ``steps()`` rather
    than off a list.  A pair that landed there for any other reason -- a model
    defect, a generator failure -- would not satisfy this.
    """
    excused = [g for g in graded() if check_pair(pair_of(g), max_steps=None).outcome != "pass"]
    assert [f"{g.ref.document}{g.ref.pointer}" for g in excused] == [
        "error-details/audience-too-small.json#",
        "error-details/budget-too-low.json#",
    ]
    for g in excused:
        assert steps(schema_at(g.ref)) == [], g.ref
        rep = check_pair(pair_of(g), max_steps=None)
        assert rep.outcome == "no_constraint_to_step"
        assert rep.accepts.outcome == "pass"
        assert rep.comparison.outcome == "pass"
        assert rep.comparison.compared > 0


@pytest.mark.parametrize("row", graded(), ids=lambda g: f"{g.ref.document}{g.ref.pointer}")
def test_every_class_passes_all_three_checks(row: Graded) -> None:
    """N: emitted AND graded green against the schema the class itself names.

    ``no_constraint_to_step`` is the one verdict other than ``pass`` allowed
    through, and only where the document genuinely states no keyword ``steps()``
    can step -- asserted here against ``steps()`` itself rather than taken on
    trust.  Such a pair is still graded by the accepts check and by the schema
    comparison, and the assertion below requires the comparison to have compared
    something, so it is not a pair nothing looked at.
    """
    pair = pair_of(row)
    rep = check_pair(pair, max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.differs)
    bad = [(r.keyword, r.pointer, r.outcome, r.counterexample, r.harness) for r in rep.refuses]
    assert [b for b in bad if b[2] not in ("pass", "no_evidence")] == []
    if rep.outcome != "pass":
        assert rep.outcome == "no_constraint_to_step", rep.outcome
        assert steps(pair.schema) == []
        assert rep.comparison.compared > 0


def test_the_schema_comparison_sees_a_fact_the_model_adds_as_well() -> None:
    """Both directions, because one of them was a hole of the other's shape.

    The comparison was built to catch a model WIDER than its document, which the
    accepts and refuses checks cannot see once the entry point validates the
    schema first.  One-directional, it could not see the mirror image -- a model
    NARROWER than its document -- and produced a report byte-identical to a
    faithful model's for one that states four constraints its document does not.

    Three cells, and the third is the one that matters:

    * a model stating MORE is reported, with each added fact named;
    * the accepts check also catches it, for a CONSTRAINT, by drawing an
      instance the document admits and watching the annotation refuse it;
    * a narrowing that states NO fact is invisible to both.  ``AwareDatetime``
      renders a schema identical to ``{"type": "string", "format": "date-time"}``
      and yet refuses a value that document admits, because ``jsonschema``
      asserts nothing for a draft-07 ``format`` without a checker.  That cell is
      asserted so the hole is measured rather than merely absent: a fact
      comparison cannot close it, and neither can the accepts check, whose
      generator honours the format.
    """
    from pydantic import AwareDatetime

    doc = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"u": {"type": "string"}, "n": {"type": "integer"}},
    }

    class Faithful(AdCPBaseModel):
        model_config = {"extra": "forbid"}
        u: str | None = None
        n: int | None = None

    class Narrower(AdCPBaseModel):
        model_config = {"extra": "forbid"}
        u: Annotated[str, Field(min_length=1, pattern="^x")] | None = None
        n: Annotated[int, Field(ge=5, le=9)] | None = None

    faithful, narrower = compare_schema(doc, Faithful), compare_schema(doc, Narrower)
    assert faithful.outcome == "pass"
    assert narrower.outcome == "model_adds_a_fact"
    assert faithful.compared == narrower.compared, "the two differ only in what they ADD"
    assert {a.split(": ")[0] for a in narrower.added} == {
        "/properties/n/minimum",
        "/properties/n/maximum",
        "/properties/u/minLength",
        "/properties/u/pattern",
    }

    def accept(payload: Any) -> Any:
        jsonschema.Draft7Validator(doc).validate(payload)
        return Narrower.model_validate(payload)

    assert check_accepts(doc, accept, examples=50).outcome == "model_refused_valid"

    # The third cell: a narrowing with no fact behind it -- and the two answers
    # that close it.  ``AwareDatetime``'s rendered schema IS
    # ``{"type": "string", "format": "date-time"}``, so a fact comparison can
    # never separate it from a plain annotated string, and the accepts check
    # cannot either because the generator honours the format.  What decides it is
    # whether the DOCUMENT asserts the format, and that is a property of the
    # validator the schema half builds, not of the model.
    stamp = {"type": "string", "format": "date-time"}
    assert compare_schema(stamp, AwareDatetime).outcome == "pass"
    naive = "2020-01-01T00:00:00"
    with pytest.raises(ValidationError):
        TypeAdapter(AwareDatetime).validate_python(naive)  # the type refuses it

    # The control: a validator with NO checker admits it, which is the state the
    # whole narrowing argument rested on and the reason `_refuse` passes one.
    jsonschema.Draft7Validator(stamp).validate(naive)
    # And the closure: with the draft's own checker -- what `_refuse` and the
    # harness both now build -- the document refuses it too, so the type states
    # the document's own rule rather than a stricter one.
    with pytest.raises(jsonschema.ValidationError) as refused:
        jsonschema.Draft7Validator(
            stamp, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER
        ).validate(naive)
    assert refused.value.validator == "format"


def test_the_comparison_reads_a_root_allof_the_way_the_schema_half_reads_it() -> None:
    """A conjunct's facts are the document's, and the check still refuses.

    ``allOf`` conjoins: draft-07 applies every conjunct to the whole instance, and
    a composing class flattens every inherited field into its own ``properties``
    and its own ``required``.  So a comparison that walks only the document's own
    root reads a FAITHFUL composing class as both dropping and adding facts, and
    reads the facts a conjunct DOES state against nothing.

    **Measured on the document below, against the code before ``_composed``: 0 of
    these four cases were graded right**, including case 3, whose verdict looked
    right.  Case 1 reported ``model_drops_a_fact`` with its real row buried among
    three false ones; case 2's omission appeared nowhere at all, in no list and in
    no ``compared`` count; case 3 reported the right outcome off the false
    ``/required`` row while its own ``maximum`` was never compared; case 4, the
    faithful class, failed.  After: four outcomes, each with exactly the row its
    axis names, and ``compared`` 3 -> 7.

    The reason all four are here and not just the faithful one: widening a check
    until the composing class passes is how the check stops returning the other
    answer, and the three failing cases are what forbids that.  Each model differs
    from the faithful one in exactly ONE axis -- no docstring, which would become a
    ``description`` the document does not state, and no second deviation -- so a
    row names the axis it was built to name.
    """
    doc = {
        "type": "object",
        "required": ["label"],
        "allOf": [
            {"type": "object", "properties": {"kind": {"type": "string"}}, "required": ["kind"]},
            {
                "type": "object",
                "properties": {
                    "adcp_major_version": {"type": "integer", "minimum": 1, "maximum": 99}
                },
            },
        ],
        "properties": {"label": {"type": "string"}},
    }

    class Base(AdCPBaseModel):
        kind: str

    class Faithful(Base):
        adcp_major_version: int | None = Field(default=None, ge=1, le=99)
        label: str

    class StatesWhatNobodyStates(Base):
        adcp_major_version: int | None = Field(default=None, ge=1, le=99)
        label: str = Field(min_length=3)  # no view of the document states this

    class OmitsAConjunctFact(AdCPBaseModel):
        adcp_major_version: int | None = Field(default=None, ge=1, le=99)
        label: str  # the conjunct's `kind` is gone

    class DisagreesWithTheConjunct(Base):
        adcp_major_version: int | None = Field(default=None, ge=1, le=100)  # conjunct says 99
        label: str

    faithful = compare_schema(doc, Faithful)
    assert faithful.outcome == "pass", (faithful.missing, faithful.differs, faithful.added)
    assert faithful.compared == 7, faithful.compared  # the conjuncts' facts are COUNTED

    adds = compare_schema(doc, StatesWhatNobodyStates)
    assert adds.outcome == "model_adds_a_fact"
    assert [a.split(": ")[0] for a in adds.added] == ["/properties/label/minLength"]

    omits = compare_schema(doc, OmitsAConjunctFact)
    assert omits.outcome == "model_drops_a_fact"
    assert omits.missing == ["/properties/kind: the model declares no such property"]
    assert [d.split(": ")[0] for d in omits.differs] == ["/required"]

    differs = compare_schema(doc, DisagreesWithTheConjunct)
    assert differs.outcome == "model_drops_a_fact"
    assert differs.differs == [
        "/properties/adcp_major_version/maximum: the document says 99, the model 100"
    ]

    # A branch is NOT a conjunct, and the same document read as a union must not
    # fold: `anyOf` is satisfied by SOME branch, so a branch's properties are not
    # unconditionally the document's.  "Left alone" is asserted as what it is --
    # both branch properties still read as model-only -- rather than as an
    # outcome, because the faithful class fails a union document on the
    # `/required` axis too and that would pass for the wrong reason.
    as_union = {("anyOf" if k == "allOf" else k): v for k, v in doc.items()}
    branches = compare_schema(as_union, Faithful)
    assert {a.split(":")[0] for a in branches.added} == {
        "/properties/kind",
        "/properties/adcp_major_version",
    }


def test_a_format_selects_a_type_where_the_schema_half_asserts_it() -> None:
    """D5's format rule, over every format site the population has.

    ``format: date-time`` references RFC 3339, where the offset is MANDATORY, so
    the document requires a timezone and ``AwareDatetime`` states the document's
    own rule.  That only holds because the schema half passes a format checker:
    a draft-07 ``format`` that nothing checks asserts nothing, and a type derived
    from one would be narrower than its document as graded.  So the rule has two
    sides and this grades both, over a population selected off the bundle:

    * a format the document's own draft can DECIDE and for which a type is named
      selects that type, asserted on the AST by the type's import being present
      and by no ``json_schema_extra`` carrying that format in the same module --
      so the fact lives in exactly one place;
    * every other format rides as an annotation on the node's own scalar type,
      so the first side cannot be satisfied by dropping the format.

    And in both cases the format reaches the model's OWN schema, asserted site by
    site against the document, which is where the schema comparison grades it.

    ``emit.FORMAT_TYPES`` is read rather than restated, so a row added or removed
    moves this test's expectation with it; what is pinned is the population
    (14 sites: ``date-time`` 7, ``uri`` 5, ``date`` 2), because that is the
    denominator the rule is stated over.
    """
    checked = emit.asserted_formats(bundle.read(BUNDLE, PAGINATION))
    # The two dependencies `pyproject` names are what put these in the draft's
    # own checker; without them the gate below selects no type at all.
    assert {"date-time", "uri"} <= checked, sorted(checked)
    assert set(emit.FORMAT_TYPES) <= checked, sorted(emit.FORMAT_TYPES - checked)

    seen: dict[str, int] = {}
    for document in sorted({g.ref.document for g in graded()}):
        tree = ast.parse(_source(document))
        imported = {
            ("." * n.level + (n.module or ""), a.name)
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            for a in n.names
        }
        annotated_formats = {
            value.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Dict)
            for key, value in zip(n.keys, n.values, strict=True)
            if isinstance(key, ast.Constant) and key.value == "format"
            if isinstance(value, ast.Constant)
        }
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            fmt = node.get("format")
            if not isinstance(fmt, str):
                continue
            seen[fmt] = seen.get(fmt, 0) + 1
            assert node["type"] in emit.SCALAR, (document, pointer)
            selected = emit.FORMAT_TYPES.get(fmt) if fmt in checked else None
            if selected is None:
                assert fmt in annotated_formats, (document, pointer, fmt)
            else:
                module, name = selected.rsplit(".", 1)
                assert (module, name) in imported, (document, pointer, selected)
                assert fmt not in annotated_formats, (document, pointer, fmt)

    assert seen == {"date-time": 7, "uri": 5, "date": 2}, seen

    # Either way the fact is on the model's own schema, at the site the document
    # states it, which is what `compare_schema` reads.  Counted, so this cannot
    # pass by looking at nothing.
    stated = 0
    for g in graded():
        if g.ref.pointer != "#":
            continue
        doc = schema_at(g.ref)
        emitted = g.model.model_json_schema() if isinstance(g.model, type) else TypeAdapter(
            g.model
        ).json_schema()
        for key, sub in (doc.get("properties") or {}).items():
            if not isinstance(sub.get("format"), str):
                continue
            mine = _unwrap(emitted["properties"][emit.field_name(key)], emitted.get("$defs", {}))
            assert mine.get("format") == sub["format"], (g.ref, key, mine)
            stated += 1
    assert stated == 14, stated


def _unwrap(node: dict, defs: dict) -> dict:
    """One property node of a model's schema, with D4's ``T | None`` folded out.

    The same two folds ``harness._normalize`` does and for the same reasons -- an
    optional property renders as a two-branch ``anyOf`` and a referenced type is
    hoisted into ``$defs``.  Written here rather than imported because the
    harness's is private to the comparison; both are three lines and neither is a
    decision.
    """
    if "$ref" in node:
        outer = {k: v for k, v in node.items() if k != "$ref"}
        return {**_unwrap(defs[str(node["$ref"]).rsplit("/", 1)[-1]], defs), **outer}
    branches = node.get("anyOf")
    if isinstance(branches, list):
        live = [b for b in branches if isinstance(b, dict) and b.get("type") != "null"]
        if len(live) == 1 and len(branches) == 2:  # noqa: PLR2004 -- T | None only
            return {**_unwrap(live[0], defs), **{k: v for k, v in node.items() if k != "anyOf"}}
    return node


def test_a_date_time_with_no_offset_is_refused_by_the_schema_half() -> None:
    """The format assertion, proved on a real emitted class and in both halves.

    A previous lane backed ``AwareDatetime`` and friends out at 14 sites because
    they were narrower than their documents AS GRADED, and that was the right
    call against a grader that asserted nothing for ``format``.  Re-adopting them
    is only correct if the SCHEMA now refuses what the type refuses, so that is
    what is asserted here rather than the type's own behaviour:

    * ``strict_validate`` refuses an offsetless timestamp, and the error's
      ``type`` is ``format`` -- the DOCUMENT's keyword, so the refusal came from
      the schema half and not from the constructor, which would report
      ``datetime_from_date_parsing``;
    * the two halves agree on the whole corpus, in both directions, including
      a leap second (RFC 3339 syntax admits ``23:59:60`` and
      ``rfc3339-validator`` refuses it, as pydantic does);
    * and the accepts check still passes on that pair, because the generator
      honours the format -- so the re-adoption costs no instance.
    """
    g = next(r for r in graded() if r.ref == SchemaRef("core/datetime-range.json", "#"))
    model, doc = g.model, schema_at(g.ref)
    assert doc["properties"]["start"]["format"] == "date-time"

    aware = "2020-06-01T12:00:00Z"
    naive = "2020-06-01T12:00:00"
    model.strict_validate({"start": aware, "end": aware})  # the document admits it
    with pytest.raises(ValidationError) as caught:
        model.strict_validate({"start": naive, "end": aware})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("format", ("start",))]

    # Both halves, over the same corpus, in both directions.  The type is read
    # off the model rather than named here, so this grades what was emitted.
    stamp = TypeAdapter(model.model_fields["start"].annotation)
    checker = jsonschema.Draft7Validator.FORMAT_CHECKER
    corpus = [
        aware,
        naive,
        "2020-06-01t12:00:00z",
        "2020-06-01T12:00:00+05:30",
        "2020-06-01T12:00:00.123456789Z",
        "2020-06-01T23:59:60Z",
        "2020-06-01",
        "not a timestamp",
    ]
    verdicts = []
    for value in corpus:
        schema_says = checker.conforms(value, "date-time")
        try:
            stamp.validate_python(value)
            type_says = True
        except ValidationError:
            type_says = False
        assert schema_says == type_says, (value, schema_says, type_says)
        verdicts.append(schema_says)
    assert True in verdicts and False in verdicts, verdicts  # not vacuous either way

    rep = check_pair(pair_of(g), max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.added)


def test_the_harness_and_the_runtime_decide_a_format_the_same_way() -> None:
    """One schema, one verdict: the control and the refusal cannot disagree.

    The refuses check asks the ORIGINAL document which keyword bit
    (``violated_keywords``) and treats an instance nothing bit as grading nothing
    (``conforms``, the control).  ``strict_validate``'s schema half asks the same
    document.  If those two build validators with different vocabularies, a step
    is excused on the strength of a keyword one of them cannot see -- so the
    harness passes the same ``FORMAT_CHECKER`` ``_refuse`` does, and this is what
    says so.

    Measured without it: the suite went fully green, because the one place a
    format reaches the control is the ``pattern`` step's candidate screen and the
    corpus now clears that screen either way.  So the agreement had no instrument
    at all and this is it.  A ``format``-violating instance is the one case
    ``steps()`` cannot produce on its own, so it is written here rather than
    drawn.
    """
    g = next(r for r in graded() if r.ref == SchemaRef("core/datetime-range.json", "#"))
    doc = schema_at(g.ref)
    aware = "2020-06-01T12:00:00Z"
    naive = {"start": "2020-06-01T12:00:00", "end": aware}

    # the control's two predicates
    assert conforms(doc, naive) is False
    assert violated_keywords(doc, naive) == ["format"]
    # ... and the runtime's, on the same document, naming the same keyword
    with pytest.raises(ValidationError) as caught:
        g.accept(naive)
    assert [e["type"] for e in caught.value.errors()] == ["format"]

    # The control also has to stay able to say YES, or the agreement above is
    # satisfied by a harness that refuses everything.
    assert conforms(doc, {"start": aware, "end": aware}) is True
    assert violated_keywords(doc, {"start": aware, "end": aware}) == []


def test_the_regex_engine_is_the_documents_and_the_two_engines_do_not_agree() -> None:
    """Which engine every pattern is compiled with, and WHY it is not derivable.

    The engine was going to be derived per class: pydantic's default is Rust,
    which is faster and refuses to build a pattern it cannot honour rather than
    mis-matching one, and its only gap was understood to be look-around -- so a
    class carrying one of the bundle's 4 look-around patterns would take
    ``python-re`` and the other 102 of 106 would take the default.  The premise
    was that the accepted sets agree for those 102, and this test is the
    assertion of it rather than the assumption.  **It does not hold.**

    Python's ``$`` matches at the end of the string OR just before a trailing
    newline; Rust's ``$`` matches only at the end of the haystack.  The document
    is validated by ``jsonschema``, which compiles with Python ``re``, so for
    every ``$``-anchored pattern the document admits a value ending in ``\\n``
    that a Rust-engine model refuses -- a model NARROWER than its own document,
    and invisible to all three checks: ``compare_schema`` sees the same
    ``pattern`` fact on both sides, and the accepts check has to draw the
    trailing newline to see it.

    So ``python-re`` stays on the base, because it is the engine whose accepted
    set is the document's, and this test is what will redden if the split is
    tried again without answering ``$``.  Measured here over the population's own
    patterns, and reported with both denominators.
    """
    assert AdCPBaseModel.model_config["regex_engine"] == REGEX_ENGINE == "python-re"

    distinct: dict[str, int] = {}
    for document in sorted({g.ref.document for g in graded()}):
        for _, node in bundle.nodes(bundle.read(BUNDLE, document)):
            pattern = node.get("pattern")
            if isinstance(pattern, str):
                distinct[pattern] = distinct.get(pattern, 0) + 1
    assert (len(distinct), sum(distinct.values())) == (11, 19), distinct

    no_build: dict[str, int] = {}
    diverges: dict[str, int] = {}
    agrees: dict[str, int] = {}
    for pattern, sites in sorted(distinct.items()):
        if not _default_engine_builds(pattern):
            # It refuses to BUILD rather than mis-matching, which is the one
            # thing about the default engine that was right -- and the document's
            # engine compiles the same pattern, so the schema half still decides.
            no_build[pattern] = sites
            assert _pattern_model(pattern, "python-re") is not None, pattern
            continue
        where = agrees
        for drawn in _matching(pattern):
            value = drawn.rstrip("\n") + "\n"
            if re.search(pattern, value) is None:
                continue  # the document refuses it too; nothing to diverge about
            # the document admits it, so the engine the document is compiled with
            # must admit it, and that is the one this package uses
            assert _accepts(pattern, REGEX_ENGINE, value), (pattern, value)
            if not _accepts(pattern, None, value):
                where = diverges
        where[pattern] = sites

    assert (len(no_build), sum(no_build.values())) == (1, 2), no_build
    assert (len(diverges), sum(diverges.values())) == (9, 16), diverges
    assert (len(agrees), sum(agrees.values())) == (1, 1), agrees
    # The one that agrees is the one with no `$` to disagree about.
    assert "$" not in next(iter(agrees)), agrees
    assert all("$" in p for p in diverges), diverges


def test_a_root_scalar_alias_is_compiled_with_the_same_engine_as_a_class() -> None:
    """The regression for a live narrowing the engine measurement found.

    ``regex_engine`` is a MODEL config, so D2's root-scalar alias has nowhere to
    carry one: ``strict_alias`` built a bare ``TypeAdapter``, which took
    pydantic's default Rust engine, while every emitted CLASS took ``python-re``
    off ``AdCPBaseModel``.  So the two halves of ``strict_validate`` disagreed on
    an alias: ``core/brand-id.json`` states ``pattern: ^[a-z0-9_]+$``, its
    document ADMITS ``"abc\\n"``, the schema half admitted it and the constructor
    then refused it with ``string_pattern_mismatch``.

    Graded over every alias the tree carries rather than on the one document that
    showed it, with the admitting value DERIVED from each alias's own pattern,
    and with the document asked each time -- so this cannot pass by asserting
    what the model happens to do.
    """
    aliases = [g for g in graded() if not isinstance(g.model, type)]
    assert aliases, "no alias was graded"
    with_pattern = 0
    for g in aliases:
        doc = schema_at(g.ref)
        pattern = doc.get("pattern")
        if not isinstance(pattern, str):
            continue
        with_pattern += 1
        value = _matching(pattern)[0].rstrip("\n") + "\n"
        jsonschema.Draft7Validator(
            doc, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER
        ).validate(value)  # the document admits it
        assert g.accept(value) == value, (g.ref, value)  # and so does the alias
    assert with_pattern == 2, with_pattern  # core/brand-id.json, core/property-id.json


@functools.lru_cache(maxsize=None)
def _pattern_model(pattern: str, engine: str | None) -> type[BaseModel]:
    """A one-field carrier for ``pattern`` under ``engine``.

    A model and not a bare ``TypeAdapter``, because ``regex_engine`` is a MODEL
    config -- which is the whole reason the engine is a per-class decision and
    not a per-field one.  ``engine=None`` sets nothing and so takes pydantic's
    default, which is the Rust engine; naming ``"rust-regex"`` explicitly would
    grade a spelling rather than the default.
    """
    config = ConfigDict(regex_engine=engine) if engine else ConfigDict()

    class Carrier(BaseModel):
        model_config = config
        v: Annotated[str, Field(pattern=pattern)]

    return Carrier


def _default_engine_builds(pattern: str) -> bool:
    """Can pydantic's DEFAULT engine compile this pattern?

    The real predicate, asked of the engine itself.  A textual look-around test
    would be a second implementation of the incompatibility, and the thing worth
    knowing is not whether a pattern contains ``(?!`` but whether the engine
    refuses it -- which is the behaviour that makes the default the one to want.
    """
    try:
        _pattern_model(pattern, None)
    except Exception:  # pydantic-core refuses to build it
        return False
    return True


def _accepts(pattern: str, engine: str | None, value: str) -> bool:
    try:
        _pattern_model(pattern, engine)(v=value)
    except ValidationError:
        return False
    return True


def _matching(pattern: str, examples: int = 2) -> list[str]:
    """Strings the pattern matches, DRAWN rather than written.

    Written candidates for 11 patterns would be 11 guesses about what each one
    means, and a wrong guess shows up as a pattern graded only on misses -- which
    is why the comparison above requires both verdicts to appear.
    """
    out: list[str] = []

    @settings(
        max_examples=examples,
        deadline=None,
        database=None,
        derandomize=True,
        phases=[Phase.generate],
        suppress_health_check=list(HealthCheck),
    )
    @given(st.from_regex(pattern))
    def body(value: str) -> None:
        out.append(value)

    body()
    return out


def test_the_step_result_is_counted_over_the_whole_population() -> None:
    """One number for the step, with its denominators, because a per-pair green
    mark does not add up to one and nobody can sum 44 of them by eye."""
    reports = [check_pair(pair_of(g), max_steps=None) for g in graded()]
    assert len(reports) == 44, len(reports)
    assert sum(1 for r in reports if r.outcome == "pass") == 42
    assert sum(1 for r in reports if r.outcome == "no_constraint_to_step") == 2
    assert sum(r.graded_instances for r in reports) == 3758  # refuses-check instances
    assert sum(r.comparison.compared for r in reports) == 486  # document facts compared
    assert sum(r.comparison.model_facts for r in reports) == 57  # model-only facts examined
    assert sum(len(r.comparison.added) for r in reports) == 0  # none of them narrows


def test_extra_follows_the_schema_and_a_silent_document_takes_the_base_default() -> None:
    """D8, over the three cases the population actually contains.

    The population is partitioned by what each object node SAYS, derived from the
    bundle, and each part is required non-empty so none is graded by an empty
    loop.  The silent part has exactly one member (``core/version-envelope.json``),
    which is the whole reason the base's own default is asserted here rather than
    left to follow from 43 classes that state their own.

    ``ignore`` and not ``allow`` for the silent case, because absent and ``true``
    are different statements: ``true`` says an additional property is part of the
    document and is retained, while silence says only that one is permitted, so it
    is accepted and dropped.  Both accept the same payloads, so this is retention
    and not the accepted set.  Nothing reads an environment to decide it.
    """
    assert AdCPBaseModel.model_config["extra"] == "ignore"

    counted = {"forbid": 0, "allow": 0, "silent": 0}
    for row in graded():
        if not isinstance(row.model, type):
            continue  # an alias has no class config
        declared = schema_at(row.ref).get("additionalProperties", "silent")
        want = {False: "forbid", True: "allow", "silent": "ignore"}[declared]
        assert row.model.model_config["extra"] == want, (row.ref, declared)
        counted["silent" if declared == "silent" else want] += 1
    assert counted["forbid"] and counted["allow"], counted
    assert counted["silent"] == 1, counted


# --------------------------------------------------------------------------- #
# what the schema half decides, and where it finds the schema
# --------------------------------------------------------------------------- #
def test_strict_validate_decides_acceptance_against_the_document() -> None:
    """D4.

    What nothing else in this file reaches: that the schema half of
    ``strict_validate`` runs at all, and that the keyword it refuses on is the
    DOCUMENT'S name for it.  ``check_pair`` cannot grade either -- ``steps()``
    has no nullability step, and a model graded through ``strict_validate``
    refuses whatever the control already says the document refuses.  Measured:
    with the schema check deleted from ``strict_validate``, this is the only test
    in the suite that goes red.
    """
    model = pagination().model

    with pytest.raises(ValidationError) as caught:
        model.strict_validate({"cursor": None})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("type", ("cursor",))]

    # ``minimum: 1`` is in the annotation too, as ``Field(ge=1)``, so the second
    # half is the keyword MAPPING: pydantic's own name for it is
    # ``greater_than_equal`` and the document's is ``minimum``.
    with pytest.raises(ValidationError) as caught:
        model.strict_validate({"max_results": 0})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("minimum", ("max_results",))]


def test_a_class_pointed_at_another_document_grades_red() -> None:
    """``__adcp_schema__`` decides what is validated, and is not decoration.

    The same class body, pointed at a different document, must fail -- otherwise
    the reference is a comment and ``strict_validate`` is deciding acceptance
    against something nobody chose.  The other document is picked by its own
    property: the first emitted document whose root forbids what this one's root
    requires.
    """
    other = next(
        g.ref.document
        for g in sorted(graded(), key=lambda g: g.ref.document)
        if g.ref.pointer == "#"
        and g.ref.document != PAGINATION
        and schema_at(g.ref).get("additionalProperties") is False
        and schema_at(g.ref).get("required")
    )

    class Misaimed(AdCPBaseModel):
        __adcp_schema__ = SchemaRef(other, "#")
        model_config = {"extra": "forbid"}
        max_results: int | None = 50
        cursor: str | None = None

    with pytest.raises(ValidationError):
        Misaimed.strict_validate({"max_results": 50})
    assert compare_schema(schema_at(SchemaRef(other, "#")), Misaimed).outcome == "model_drops_a_fact"


def test_a_pointer_names_one_node_of_a_document() -> None:
    """The pointer half of ``SchemaRef``, on the document step 1 is stated over.

    A nested class grades against its own node, and that only works if the
    pointer resolves to the node rather than to the file.  Graded on
    ``pagination-request`` even though it has no nested class, so the mechanism
    is checked where the step's own document is: the property node it names is
    not the root, and a pointer that names nothing raises.
    """
    root = schema_at(SchemaRef(PAGINATION, "#"))
    node = schema_at(SchemaRef(PAGINATION, "#/properties/max_results"))
    assert node == root["properties"]["max_results"]
    assert node != root
    with pytest.raises(KeyError):
        schema_at(SchemaRef(PAGINATION, "#/properties/no_such_property"))


def test_no_schema_the_package_carries_has_an_unresolved_reference() -> None:
    """``strict_validate`` has to be able to DECIDE with the document it reads.

    A ``$ref`` left in one is not decidable locally: ``jsonschema`` finds no
    store for an absolute URI and retrieves it OVER THE NETWORK, on a code path
    it deprecates and says "will shortly become an error".  Measured before this
    was fixed: 4.4 s per validation against a live URL, and a
    ``RefResolutionError`` offline.  So the emitter writes each document resolved
    (``bundle.resolved``).

    This is the runtime half of step 2.  The module half is the opposite and is
    graded below: a reference is an IMPORT in the generated module (P2) and is
    never inlined there.  The two are not in tension -- one is where a type LIVES
    and the other is what a document MEANS.
    """
    documents = {g.ref.document for g in graded()}
    for document in sorted(documents):
        assert bundle.references(schema_at(SchemaRef(document, "#"))) == [], document
    # And the control: the bundle DOES have references, so the assertion above is
    # over documents that had something to resolve rather than over nothing.
    assert [d for d in documents if bundle.references(bundle.read(BUNDLE, d))]


# --------------------------------------------------------------------------- #
# the emitted text
# --------------------------------------------------------------------------- #
def _source(document: str) -> str:
    return (TREE / f"{emit.module_path(document)}.py").read_text()


def _symbol(document: str) -> str:
    """The name the emitted module exports, read off the module itself."""
    (symbol,) = importlib.import_module(emit.emit(BUNDLE, [document]).emitted[document]).__all__
    return symbol


def test_a_cross_document_reference_is_an_import_and_not_a_copy() -> None:
    """P2, on the AST of the emitted module rather than on its text.

    The previous attempt's whole premise was that three generators all flatten a
    ``$ref`` into a COPY of its target, so "it emits an import" is the claim this
    step has to make falsifiable.  Two halves, because either alone passes while
    the other fails:

      * the referencing field's annotation NAMES the target's symbol and carries
        no CONSTRAINT -- a copy of the target's constraints is a ``Field(ge=...,
        min_length=...)``, and a copy that replaced the reference does not name
        the symbol at all;
      * no ``Field`` kwarg ANYWHERE in the module is one this document does not
        declare locally -- so a constraint of the target has nowhere else in the
        module to hide either.

    The first half used to assert the annotation contained no CALL, which was the
    same claim only while the renderer dropped the property's own
    ``description``.  draft-07 says a ``$ref`` ignores its siblings and
    ``resolve_all_refs`` MERGES them, so the resolved document the class names
    carries the sibling description -- and a renderer that drops it drops a fact
    the document states.  The compiler carries it, as ``Field(description=...)``,
    which is a call in the annotation and not a copy of anything.  So the
    assertion is on the kwarg NAMES, which is what "copies no constraint" means.

    Deliberately says nothing about HOW an optional property is wrapped.  That is
    D4's, it has been re-decided once already, and a test naming the wrapper's
    spelling would have to be edited by the lane that changes it -- which is how
    a P2 instrument comes to be adjusted by someone who is not grading P2.

    Everything compared is derived: the import module from ``relative_module``,
    the symbol from the target module's own ``__all__``, the local constraint set
    from the document's non-reference nodes.
    """
    known = set(bundle.portable(BUNDLE))
    documents = sorted({g.ref.document for g in graded()})
    graded_properties = 0
    for document in documents:
        doc = bundle.read(BUNDLE, document)
        refd = {
            key: sub["$ref"]
            for key, sub in doc.get("properties", {}).items()
            if isinstance(sub, dict) and "$ref" in sub
        }
        if not refd:
            continue
        tree = ast.parse(_source(document))
        imported = {
            ("." * n.level + (n.module or ""), a.name)
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            for a in n.names
        }
        root = next(
            c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == _symbol(document)
        )
        annotated = {
            t.target.id: t.annotation
            for t in root.body
            if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
        }
        for key, uri in sorted(refd.items()):
            target = str(bundle.document_for(uri, known))
            symbol = _symbol(target)
            module = emit.relative_module(document, target)
            assert (module, symbol) in imported, (document, key, module, symbol)
            got = annotated[emit.field_name(key)]
            named = {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}
            assert symbol in named, (document, key, ast.unparse(got))
            carried = {
                kw.arg for n in ast.walk(got) if isinstance(n, ast.Call) for kw in n.keywords
            }
            assert carried <= ANNOTATION_KWARGS, (document, key, ast.unparse(got))
            graded_properties += 1
        local = {
            k
            for _, node in bundle.nodes(doc)
            if "$ref" not in node
            for k in node
            if k in emit.CONSTRAINTS
        }
        used = {
            kw.arg
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Field"
            for kw in n.keywords
        }
        assert used <= _pydantic_names(local) | ANNOTATION_KWARGS, (document, sorted(used))
    assert graded_properties, "no referencing property was graded"


def _pydantic_names(json_schema_keywords: set[str]) -> set[str]:
    """The ``Field`` kwarg each JSON Schema constraint renders as.

    Derived from the compiler's own ``Constraints`` model, which declares every
    field under its JSON-Schema alias -- so this mapping is the compiler's and
    not a second copy of it that could drift.
    """
    from datamodel_code_generator.model.pydantic_v2.base_model import Constraints

    by_alias = {f.alias: name for name, f in Constraints.model_fields.items() if f.alias}
    return {by_alias[k] for k in json_schema_keywords if k in by_alias}


def test_a_scalar_root_emits_an_annotated_alias_and_not_a_class() -> None:
    """D2's root-scalar row: a node with no field to hang itself on is an alias.

    A wrapper class would be a second name for the same node (P2), and every
    referencing model would then carry an object where the document carries a
    string.  The alias carries its document's own ``description``, which an
    earlier rendering dropped at all five of this population's scalar roots
    because an alias has no docstring slot -- a ``Field(description=...)`` does.
    """
    graded_aliases = 0
    for document in sorted({g.ref.document for g in graded()}):
        doc = bundle.read(BUNDLE, document)
        if doc.get("type") not in emit.SCALAR:
            continue
        tree = ast.parse(_source(document))
        assigned = {
            t.id
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
        }
        assert _symbol(document) in assigned, document
        assert [n for n in tree.body if isinstance(n, ast.ClassDef)] == [], document
        graded_aliases += 1
    assert graded_aliases, "no scalar root was graded"

    control = "core/creative-revision-id.json"
    doc = bundle.read(BUNDLE, control)
    schema = __import__(
        "adcp.types._schemas.core.creative_revision_id", fromlist=["strict_validate"]
    )
    emitted = TypeAdapter(getattr(schema, _symbol(control))).json_schema()
    assert emitted["minLength"] == doc["minLength"]
    assert emitted["maxLength"] == doc["maxLength"]
    assert emitted["description"] == doc["description"]


# --------------------------------------------------------------------------- #
# the run itself
# --------------------------------------------------------------------------- #
def test_the_committed_tree_is_what_a_fresh_run_emits(tmp_path) -> None:
    """P10, and D8's compare: the tree equals f(bundle, emitter, pinned compiler),
    so a defect is fixed in one of those and nothing rewrites the output.

    It compares the whole file set and every byte of it.  The previous revision of
    this test compared against a recorded earlier output of the same emitter,
    which P10 forbids for the reason this step demonstrates: the renderer changed
    and the recorded text was the OLD renderer's, so the comparison graded the
    change rather than the inputs.
    """
    out = emit.emit(BUNDLE, population())
    emit.write(out, tmp_path)

    def tree(root: Path) -> dict[str, str]:
        return {
            str(p.relative_to(root)): p.read_text()
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }

    committed, fresh = tree(TREE), tree(tmp_path)
    assert sorted(fresh) == sorted(committed)
    for rel in sorted(fresh):
        assert fresh[rel] == committed[rel], rel


def test_the_output_is_a_function_of_its_inputs_and_of_nothing_else() -> None:
    """P7: determinism is a precondition of grading, not a fix.

    Argument order is NOT what this grades, and a test that compared a forward
    run with a reversed one was kept here until it was probed: ``emit`` sorts its
    documents, so no permutation of its arguments can change the output and the
    comparison could not fail.  P7 holds for order by construction.

    What CAN vary between runs is set iteration -- the import lines come out of a
    ``set[tuple[str, str]]`` -- and that varies by hash seed, not by anything a
    caller passes.  So the two runs are two processes with different
    ``PYTHONHASHSEED`` values, which is the perturbation this property has.
    """
    cmd = [sys.executable, "-m", "codegen.emit", "--bundle", str(BUNDLE), "--tree"]
    outs = []
    for seed in ("0", "12345"):
        into = Path(tempfile.mkdtemp())
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(REPO)}
        subprocess.run(
            [*cmd, str(into), *population()], check=False, cwd=REPO, env=env, capture_output=True
        )
        outs.append({str(p.relative_to(into)): p.read_text() for p in sorted(into.rglob("*.py"))})
        shutil.rmtree(into)
    assert outs[0] and outs[0] == outs[1]


def test_the_cli_reports_a_refusal_rather_than_raising_it(tmp_path) -> None:
    """D12, graded through the entry point that breaks it.

    ``python -m codegen.emit`` runs the emitter as ``__main__``.  With ``Refusal``
    defined in that module, a lowering that imports ``codegen.emit`` to raise one
    raises a DIFFERENT class from the one ``main``'s ``except`` names, so every
    refusal escapes as an unhandled traceback and the run writes nothing -- while
    the in-process path, which imports the module once, stays green.  Three lanes
    measured that independently.

    So this runs the CLI, over a bundle whose two documents are one emittable and
    one refused, and requires the refusal to be REPORTED: exit 1, the document
    and its keyword on stdout, no traceback, and the other document written.
    """
    (tmp_path / "ok.json").write_text(
        json.dumps({"title": "Ok", "type": "object", "properties": {"a": {"type": "string"}}})
    )
    (tmp_path / "no.json").write_text(
        json.dumps(
            {"title": "No", "type": "object", "properties": {"a": {"type": "string"}}, "not": {}}
        )
    )
    into = tmp_path / "out"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "codegen.emit",
            "--bundle",
            str(tmp_path),
            "--tree",
            str(into),
            "ok.json",
            "no.json",
        ],
        check=False,
        cwd=REPO,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in done.stderr, done.stderr
    assert done.returncode == 1, (done.returncode, done.stdout, done.stderr)
    assert "refused no.json" in done.stdout, done.stdout
    assert "on not:" in done.stdout, done.stdout
    assert (into / "ok.py").exists()
    assert not (into / "no.py").exists()


def test_a_reference_cycle_refuses_rather_than_recurring(tmp_path) -> None:
    """The walk terminates, graded on a bundle built so that it would not.

    The 3.2 bundle's reference graph is acyclic -- a three-colour DFS over its
    3,094 document-to-document edges finds 0 cycles -- so this branch is
    unreachable from it, which is exactly why it gets a bundle of its own instead
    of a comment saying it cannot happen.  Two modules importing each other's
    symbol at module scope is an ImportError, not a type, so a cycle has to refuse
    before it is written.
    """
    ref = "https://example.org/whatever/{}.json"
    for name, other in (("a", "b"), ("b", "a")):
        (tmp_path / f"{name}.json").write_text(
            json.dumps(
                {
                    "title": name.upper(),
                    "type": "object",
                    "required": [other],
                    "properties": {other: {"$ref": ref.format(other)}},
                }
            )
        )
    out = emit.emit(tmp_path, ["a.json", "b.json"])
    assert out.emitted == {}
    assert sorted(out.refusals) == ["a.json", "b.json"]
    for document, row in out.refusals.items():
        assert row["keyword"] == "$ref", (document, row)
        assert "cycle" in row["detail"], (document, row)
