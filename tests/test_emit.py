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
import types
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, NamedTuple
from unittest import mock

import jsonschema
import pytest
from hypothesis import given, HealthCheck, Phase, settings
from hypothesis import strategies as st
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter, ValidationError

from adcp.types._base import (
    AdCPBaseModel,
    BranchDispatchMixin,
    REGEX_ENGINE,
    SchemaRef,
    schema_at,
)
from adcp.types._runtime import RuleBound
from codegen import bundle, compiler, emit, harness
from codegen import constraints as constraints_module
from codegen.lower import union as lower_union
from codegen.refusal import Refusal
from codegen.harness import (
    AcceptsResult,
    check_accepts,
    check_refuses,
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
from codegen.lower import rules

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
TREE = REPO / emit.TREE


#: Cached because each of these re-reads all 1,054 documents and the two keyword
#: selectors walk every schema position in each: over 400 tests calling them, the
#: uncached suite spends minutes re-deriving a population that is a function of the
#: bundle alone.  ``graded()`` is cached for the same reason -- it imports the whole
#: emitted tree, and a union root's ``model_rebuild(force=True)`` is not cheap.
@functools.cache
def leaves() -> list[str]:
    """Step 1's population: an object root with no reference anywhere in it."""
    return [d for d in bundle.portable(BUNDLE) if bundle.is_leaf_object(bundle.read(BUNDLE, d))]


@functools.cache
def referencing() -> list[str]:
    """Step 2's population: every reference is a property's own schema or its items."""
    return [
        d for d in bundle.portable(BUNDLE) if bundle.references_a_property(bundle.read(BUNDLE, d))
    ]


@functools.cache
def enums() -> list[str]:
    """Step 3's population: an ``enum`` at a schema position anywhere in it."""
    return [d for d in bundle.portable(BUNDLE) if bundle.carries_an_enum(bundle.read(BUNDLE, d))]


@functools.cache
def composing() -> list[str]:
    """Step 4's population: a root ``allOf`` with no union beside it."""
    return [
        d for d in bundle.portable(BUNDLE) if bundle.composes_at_the_root(bundle.read(BUNDLE, d))
    ]


@functools.cache
def union_roots() -> list[str]:
    """Step 5's population: a document whose root carries ``oneOf`` or ``anyOf``.

    Read off ``bundle.union_root``, which is also the step's DISPATCH selector, so the
    population this file counts and the population the table claims are one function.
    """
    return [d for d in bundle.portable(BUNDLE) if bundle.union_root(bundle.read(BUNDLE, d))]


@functools.cache
def population() -> list[str]:
    """What the committed tree is emitted from.  A reference TARGET is not here and
    does not need to be: ``emit`` walks ``$ref`` and emits the closure.

    The union of the steps' own selectors, which OVERLAP by design -- a leaf
    object with an inline enum belongs to step 1 and to step 3 alike, and 26
    leaves and 94 referencing documents are already inside step 3's 535.  The
    overlap is a property of the POPULATION and not of the dispatch table, whose
    rows read a document's ROOT and claim 0 documents in common (asserted below).
    """
    return sorted(
        set(leaves())
        | set(referencing())
        | set(enums())
        | set(composing())
        | set(union_roots())
        | set(container_roots())
        | set(object_rules())
    )


@functools.cache
def container_roots() -> list[str]:
    """Step 6's population: the document's ROOT is a container.

    Also step 6's row in ``emit.ROWS``, and the two being one predicate is the
    point: a row cannot claim a document its step does not count.
    """
    return [d for d in bundle.portable(BUNDLE) if bundle.is_container_root(bundle.read(BUNDLE, d))]


@functools.cache
def object_rules() -> list[str]:
    """Step 7's population: an object root whose composition is a presence rule."""
    return [
        d for d in bundle.portable(BUNDLE) if bundle.states_an_object_rule(bundle.read(BUNDLE, d))
    ]




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
    assert len(enums()) == 535
    assert len(composing()) == 287
    # Not the sum: the selectors OVERLAP, and the overlaps are counted below
    # rather than assumed.  The union is the denominator; no selector here is a
    # ROW for another's shape, so nothing is counted twice by the table.
    assert len(population()) == 981
    assert set(population()) < set(whole), "the step's population is not a part of the bundle"
    assert PAGINATION in leaves()
    assert "error-details/creative-revision-content-mismatch.json" in referencing()
    assert "enums/match-type.json" in enums()
    # The selectors overlap, and the overlap is counted rather than assumed: the
    # union is smaller than the sum, so a reader cannot add 85 + 249 + 535.
    assert len(set(leaves()) & set(enums())) == 26
    assert len(set(referencing()) & set(enums())) == 94
    # 126 and not 156: ``union_root`` now yields the 30 roots whose combinator holds
    # ``required`` GROUPS to the object row, because those are rules and not unions
    # (step 7, and ``test_step_sevens_population_reaches_the_object_row_and_no_other``).
    assert len(union_roots()) == 126
    assert "core/signal-id.json" in union_roots()
    # 0 union roots carry BOTH keywords, so the keyword the lowering reads is unambiguous
    # for every document the selector claims.
    assert [
        d
        for d in union_roots()
        if {"oneOf", "anyOf"} <= set(bundle.read(BUNDLE, d))
        and all(isinstance(bundle.read(BUNDLE, d)[k], list) for k in ("oneOf", "anyOf"))
    ] == []
    # 9 and not the 37 this lane measured alone: ``is_container_root`` now excludes a
    # root that declares a union as well, because 28 of its 32 mapping roots do and
    # the union row owns them.  5 arrays and 4 mappings are left.
    assert len(container_roots()) == 9
    assert "core/ext.json" in container_roots()
    # Step 6's population only GROWS the named set, which is what makes the earlier
    # steps' floor structurally safe rather than re-measured: a container root is
    # neither a leaf object nor a referencing one, so no document stops being named.
    assert not set(container_roots()) & (set(leaves()) | set(referencing()))
    assert len(object_rules()) == 5
    assert "core/budget-range.json" in object_rules()


def test_step_sevens_population_reaches_the_object_row_and_no_other() -> None:
    """The step-5/step-7 boundary, asserted on the selectors rather than assumed.

    Step 7 adds no ROW: a rule attaches to the nearest class, so its documents are
    lowered by the object row with ``rules.lower`` inside
    ``compiler.lower_object``.  That only works if the object row CLAIMS them, and
    it did not: a root whose ``oneOf`` holds ``required`` groups carries a union
    keyword, so ``union_root`` claimed all 5 and ``is_object_root`` claimed none --
    and step 5's row refuses a branch declaring no property, so step 7's whole
    population was selected by a row that refuses it.

    ``bundle.union_root`` now asks ``rules.presence_only`` as well, and this is the
    assertion that keeps it: every document of step 7's population is claimed by
    exactly one row, and that row is the object one.
    """
    assert object_rules(), "step 7's population is empty; this would be vacuous"
    for document in object_rules():
        doc = bundle.read(BUNDLE, document)
        claiming = [s.__name__ for s, _ in emit.ROWS if s(doc)]
        assert claiming == ["is_object_root"], (document, claiming)


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
        "core/context.json#",
        # Added by D5's alias module: `core/creative-brief.json` was refused on a
        # constrained scalar inside a container, and this nested class of it
        # states no keyword `steps()` can step.
        "core/creative-brief.json#/properties/messaging",
        "core/ext.json#",
        "core/media-buy-legacy-terms-ref.json#",
        "error-details/account-setup-required.json#",
        "error-details/audience-too-small.json#",
        "error-details/budget-too-low.json#",
        "error-details/conflict.json#",
        "error-details/creative-rejected.json#",
        "sponsored-intelligence/si-identity.json#/properties/privacy_policy_acknowledged",
        "sponsored-intelligence/si-identity.json#/properties/user/properties/shipping_address",
        "sponsored-intelligence/si-identity.json#/properties/user",
    ]
    # Step 6 added two of them and they are the two it ought to add: a mapping root
    # is ``dict[str, Any]`` over an ``additionalProperties: true`` document, which
    # states no keyword ``steps()`` can step.  The accepts check and the schema
    # comparison still grade both, which the loop below requires.
    assert {"core/context.json#", "core/ext.json#"} <= {
        f"{g.ref.document}{g.ref.pointer}" for g in excused
    }
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


def test_the_url_type_row_is_its_own_category_and_each_half_is_gated() -> None:
    """D5's URL-type row, broken on purpose at every gate it has.

    The row admits two facts and NOTHING ELSE, each gated, and it counts them in a
    field of their own (``ComparisonResult.url_typed``) rather than in ``missing``
    or in ``added`` -- because it is the one admission here that excuses a fact the
    model does not state at all, and folding it into the implied-fact rows would
    make a genuine omission look like a derivation.

    Six cells.  The first two are what the row is for; the next three are the
    perturbations that must still redden, and each of them passed before the gates
    were written as they are; the last says the counting is separate.
    """
    from pydantic import AnyUrl, UrlConstraints

    AdCPUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]
    bare = {"type": "string", "format": "uri"}
    patterned = {**bare, "pattern": "^https://"}

    # 1. the model-only ``minLength: 1`` any URL type renders, over a document
    #    that states only the type and the format.
    one = compare_schema(bare, AdCPUrl)
    assert one.outcome == "pass", (one.added, one.missing, one.differs)
    assert one.url_typed == ["/minLength: the model says 1, which any URL type renders"]
    assert one.added == [] and one.missing == []

    # 2. the document's own ``pattern``, which the annotation cannot carry at all
    #    -- ``Annotated[AnyUrl, Field(pattern=...)]`` raises when pydantic builds
    #    the schema -- and which the schema half enforces instead.
    two = compare_schema(patterned, AdCPUrl)
    assert two.outcome == "pass", (two.added, two.missing, two.differs)
    assert len(two.url_typed) == 2, two.url_typed
    assert any("the schema half enforces it" in line for line in two.url_typed)
    assert two.missing == [] and two.added == []
    # The fact was still COUNTED as looked for: the row stops it landing in
    # ``missing``, it does not stop it being graded.
    assert two.compared == one.compared + 1

    # 3. BROKEN ON PURPOSE -- a plain ``str`` cannot wear the row.  It renders the
    #    type and the format and no ``minLength``, so it is not a URL type and the
    #    dropped ``pattern`` is reported.
    plain = compare_schema(patterned, Annotated[str, Field(json_schema_extra={"format": "uri"})])
    assert plain.outcome == "model_drops_a_fact"
    assert plain.url_typed == []
    assert any("/pattern" in m for m in plain.missing), plain.missing

    # 4. BROKEN ON PURPOSE -- any OTHER keyword the document states is still
    #    reported, because the row names ``pattern`` and nothing else.  This is
    #    the gate that keeps ``emit.decide_type``'s refusal honest: a
    #    ``format: uri`` node stating a ``maxLength`` refuses at emission rather
    #    than going missing here.
    capped = compare_schema({**bare, "maxLength": 20}, AdCPUrl)
    assert capped.outcome == "model_drops_a_fact"
    assert any("/maxLength" in m for m in capped.missing), capped.missing

    # 5. BROKEN ON PURPOSE -- the ``minLength`` half is gated on the VALUE, so a
    #    bound the type did not render is a fact the model adds.
    floored = compare_schema(bare, Annotated[AnyUrl, UrlConstraints(max_length=2083)])
    assert floored.outcome == "model_adds_a_fact", floored.url_typed
    assert any("/maxLength" in a for a in floored.added), floored.added

    # 6. and a document that states the ``minLength`` ITSELF is compared, not
    #    excused: the row is about a fact the document does not state.
    stated = compare_schema({**bare, "minLength": 1}, AdCPUrl)
    assert stated.outcome == "pass"
    assert stated.url_typed == [], stated.url_typed
    assert stated.compared == one.compared + 1


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


def test_the_three_allof_decisions_that_no_case_above_grades() -> None:
    """The scope decisions ``_composed`` makes, each one perturbed and found green.

    Breaking the fix on purpose reddened the four cases above for the ``required``
    union, the ``properties`` merge and the ``anyOf`` exclusion, and reddened
    NOTHING for three others.  A perturbation that reddens nothing is a finding
    about the test set, so each of those three is graded here:

    * **a conditional conjunct contributes nothing.**  Folding an ``if``/``then``
      conjunct's ``then`` as if it applied unconditionally changed no outcome
      anywhere, and it is the dominant conjunct shape in the bundle -- 352
      ``if``/``then`` conjuncts against 21 that state ``properties``.
    * **the view applies at every node, not only at the root.**  Restricting it to
      the root changed no outcome, because every case above composes at the root.
    * **a conjunct fills a gap and never overrides.**  Letting it override changed
      no outcome, because no case above and no measured document collides on a
      bound.  That is the ceiling ``_composed`` names, pinned here so replacing
      the gap-fill with a per-keyword intersection has to move this line.
    """

    # A conditional conjunct: `then` applies only to an instance the `if` selects,
    # so a class that declares nothing for `flagged` is faithful.
    conditional = {
        "type": "object",
        "required": ["kind"],
        "allOf": [
            {
                "if": {"properties": {"kind": {"const": "x"}}},
                "then": {"properties": {"flagged": {"type": "boolean"}}, "required": ["flagged"]},
            }
        ],
        "properties": {"kind": {"type": "string"}},
    }

    class NoConditionalField(AdCPBaseModel):
        kind: str

    assert compare_schema(conditional, NoConditionalField).outcome == "pass"

    # A PROPERTY's own node composes, and pydantic flattens the nested class the
    # same way, so the view has to apply there too.
    nested = {
        "type": "object",
        "required": ["inner"],
        "properties": {
            "inner": {
                "type": "object",
                "required": ["a"],
                "allOf": [{"type": "object", "properties": {"b": {"type": "integer"}}}],
                "properties": {"a": {"type": "string"}},
            }
        },
    }

    class InnerBase(AdCPBaseModel):
        b: int | None = None

    class Inner(InnerBase):
        a: str

    class Outer(AdCPBaseModel):
        inner: Inner

    assert compare_schema(nested, Outer).outcome == "pass"

    # The ceiling: the node's own bound wins over a conjunct's, so a class stating
    # the TIGHTER effective bound is reported as differing.  A false failure, which
    # is the safe direction, and measured at 0 documents.
    collides = {
        "type": "object",
        "allOf": [{"type": "object", "properties": {"n": {"maximum": 99}}}],
        "properties": {"n": {"type": "integer", "maximum": 100}},
    }

    class StatesTheTighter(AdCPBaseModel):
        n: int | None = Field(default=None, le=99)

    ceiling = compare_schema(collides, StatesTheTighter)
    assert ceiling.differs == [
        "/properties/n/maximum: the document says 100, the model 99"
    ], ceiling.differs


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
    (57 sites: ``date-time`` 26, ``uri`` 27, ``email`` 2, ``date`` 2), because that is the
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

    assert seen == {"date-time": 26, "uri": 27, "email": 2, "date": 2}, seen

    # Either way the fact is on the model's own schema, at the site the document
    # states it, which is what `compare_schema` reads.  Counted, so this cannot
    # pass by looking at nothing.
    #
    # Over EVERY class the tree carries, not only the root-pointer ones.  Restricted to
    # roots it graded 14 of the 18 census sites above, and the 4 it missed are the ones
    # step 5 added: a union root has no properties of its own, so every format in one of
    # those documents is on a BRANCH class, whose pointer is not ``#``.
    stated = 0
    for g in graded():
        doc = schema_at(g.ref)
        emitted = _model_schema(g.model)
        for key, sub in (doc.get("properties") or {}).items():
            if not isinstance(sub.get("format"), str):
                continue
            mine = _unwrap(emitted["properties"][compiler.field_name(key)], emitted.get("$defs", {}))
            assert mine.get("format") == sub["format"], (g.ref, key, mine)
            stated += 1
    assert stated == 57, stated


def _model_schema(model: Any) -> dict:
    """One model's own JSON schema, whichever kind of model it is.

    The same predicate ``harness.compare_schema`` uses, and it has to be the same
    one: ``isinstance(model, type)`` alone is not it, because D2's enumeration row
    emits a CLASS that is not a pydantic model and has no ``model_json_schema``.
    """
    if isinstance(model, type) and hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return TypeAdapter(model).json_schema()


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
    assert (len(distinct), sum(distinct.values())) == (24, 66), distinct

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
    assert (len(diverges), sum(diverges.values())) == (22, 63), diverges
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
    assert with_pattern == 5, with_pattern


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
    assert len(reports) == 462, len(reports)
    assert sum(1 for r in reports if r.outcome == "pass") == 450
    assert sum(1 for r in reports if r.outcome == "no_constraint_to_step") == 12
    assert sum(r.graded_instances for r in reports) == 34935  # refuses-check instances
    assert sum(r.comparison.compared for r in reports) == 4658  # document facts compared
    assert sum(r.comparison.model_facts for r in reports) == 1069  # model-only facts examined
    assert sum(len(r.comparison.added) for r in reports) == 0  # none of them narrows
    assert sum(len(r.comparison.missing) for r in reports) == 0  # and none drops one
    assert sum(len(r.comparison.differs) for r in reports) == 0
    # D5's URL-type row, the one admission that excuses a fact the model does not
    # state: 36 of the `minLength: 1` any URL type renders, and the ONE `pattern`
    # the bundle states on a `format: uri` node.  A position inside a nested class
    # is graded twice -- once at its own pair and once at its parent's -- so this
    # is larger than the 30 positions the bundle has.
    assert sum(len(r.comparison.url_typed) for r in reports) == 37


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
        if not (isinstance(row.model, type) and issubclass(row.model, AdCPBaseModel)):
            continue  # an alias and an enumeration have no model config
        declared = schema_at(row.ref).get("additionalProperties", "silent")
        want = {False: "forbid", True: "allow", "silent": "ignore"}[declared]
        if declared == "silent" and row.model.model_config["extra"] != "ignore":
            # A class that COMPOSES takes its base's value, and the resolver is why
            # the document no longer says so: ``canonicalish`` drops
            # ``additionalProperties: true`` as the vocabulary's default, so a
            # conjunct that stated it comes back silent while the BASE -- read from
            # its own document, where the key survives at a root -- still carries
            # ``allow``.  The inherited value is the document's statement about a
            # schema it composes, so it is checked against the base rather than
            # read as this document's own silence.  Measured: 1 such class
            # (``core/async-response-refs/media-buy/accept-proposal-async-response-working.json``
            # over ``core/compact-task-working.json``, whose own document says
            # ``true``), and ``allow`` is the only value this arm admits -- a
            # ``forbid`` inherited where the document is silent would be a
            # narrowing and still fails.
            assert row.model.model_config["extra"] == "allow", (row.ref, declared)
            base = row.model.__mro__[1]
            assert schema_at(base.__adcp_schema__)["additionalProperties"] is True, row.ref
            counted["allow"] += 1
            continue
        assert row.model.model_config["extra"] == want, (row.ref, declared)
        counted["silent" if declared == "silent" else want] += 1
    assert counted["forbid"] and counted["allow"], counted
    # The silent set is the two leaf objects whose documents say nothing plus the
    # union BASES, which are silent by construction: ``lower/union.py`` refuses a
    # root that states its own ``additionalProperties``, so a base never has one to
    # carry and takes this default.  The other members are mapping and container
    # roots whose own document is silent too.
    assert counted["silent"] == 16, counted


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


@functools.lru_cache(maxsize=None)
def _symbol(document: str) -> str:
    """The name the emitted module exports, read off the module itself.

    Memoized because it RUNS THE EMITTER: at step 2's 43 documents the repeated
    runs were affordable and at step 3's 282 they are not, and the two tests
    below ask for the same target's symbol once per referencing property.  The
    answer is a function of (bundle, document) alone, so the memo cannot hide a
    change.
    """
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
            got = annotated[compiler.field_name(key)]
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


# --------------------------------------------------------------------------- #
# step 5: union roots (§4)
# --------------------------------------------------------------------------- #
def emitted_unions() -> list[str]:
    """The union roots the committed tree holds, read off the tree and the selector."""
    return sorted({g.ref.document for g in graded()} & set(union_roots()))


def test_a_union_root_emits_a_base_plus_one_subclass_per_branch() -> None:
    """§4's shape, on the AST of every emitted union module.

    Four claims, each of which a previous generator got wrong at scale:

    * **the root's name binds the BASE**, never a union alias.  Censused over this
      bundle's 156 union roots, the previous tree bound 100 root names to an alias, so a
      caller had nothing to ``isinstance`` against.  Asserted as: the module's ``__all__``
      is the root's own name, that name is a CLASS, and it derives
      ``BranchDispatchMixin``;
    * **one subclass per branch**, exactly -- as many branch classes as the document has
      branches, each deriving the base, each naming its own ``#/<kw>/<i>``;
    * the base declares the three facts the mixin reads;
    * the module installs the union, because the branches do not exist while the base is
      being built.

    Everything compared is derived: the branch count from the document, the symbol from
    the module's own ``__all__``, the pointers from the classes themselves.
    """
    assert emitted_unions(), "no union root was emitted; this test grades nothing"
    for document in emitted_unions():
        doc = bundle.read(BUNDLE, document)
        kw = lower_union.keyword(doc)
        symbol = _symbol(document)
        tree = ast.parse(_source(document))
        classes = {c.name: c for c in tree.body if isinstance(c, ast.ClassDef)}

        assert symbol in classes, (document, symbol)
        bases = [b.id for b in classes[symbol].bases if isinstance(b, ast.Name)]
        assert bases == ["BranchDispatchMixin", "AdCPBaseModel"], (document, bases)

        branch_classes = sorted(
            name
            for name, node in classes.items()
            if [b.id for b in node.bases if isinstance(b, ast.Name)] == [symbol]
        )
        assert len(branch_classes) == len(doc[kw]), (document, branch_classes, len(doc[kw]))

        declared = {
            t.target.id
            for t in classes[symbol].body
            if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
        }
        assert {"__adcp_schema__", "_branch_models", "_ROOT_REQUIRED"} <= declared, (
            document,
            sorted(declared),
        )
        methods = {f.name for f in classes[symbol].body if isinstance(f, ast.FunctionDef)}
        assert "_branch_combinator" in methods, (document, sorted(methods))

        # the trailer: the union is installed after the branches are defined
        assigned = [
            ast.unparse(n)
            for n in tree.body
            if isinstance(n, ast.Assign) or isinstance(n, ast.Expr)
        ]
        assert f"{symbol}.model_rebuild(force=True)" in assigned, (document, assigned)
        assert any(a.startswith(f"{symbol}._branch_models = (") for a in assigned), (
            document,
            assigned,
        )


def test_the_base_the_root_name_binds_is_the_class_every_branch_descends_from() -> None:
    """The run-time half of the claim above, read off the live classes.

    The AST test says the module TEXT has the shape; this says the imported objects do,
    and that the three emitted facts carry the document's own values.  ``_ROOT_REQUIRED``
    is asserted EMPTY and that is reported rather than hidden: ``lower/union.py`` refuses
    a root that declares its own ``required``, so no document in this step's population
    produces a non-empty one, and the field is graded by the mixin's unit test below
    rather than by the tree.
    """
    assert emitted_unions()
    for document in emitted_unions():
        doc = bundle.read(BUNDLE, document)
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))
        branches = base._branch_models

        assert "_branch_models" in base.__dict__, document
        assert len(branches) == len(doc[lower_union.keyword(doc)]), document
        for branch in branches:
            assert issubclass(branch, base) and branch is not base, (document, branch)
            assert "_branch_models" not in branch.__dict__, (document, branch)
            assert branch.__adcp_schema__.document == document, (document, branch)
        assert base._branch_combinator() == lower_union.keyword(doc), document
        assert base._ROOT_REQUIRED == (), document


def _module_of(document: str) -> str:
    return f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}"


def test_a_payload_resolves_to_its_branch_on_all_four_paths() -> None:
    """§4's exit condition, over every emitted union root and every one of its branches.

    The four paths are not interchangeable and the specification says why: a core-schema
    hook covers the three pydantic validates THROUGH -- a nested field, a ``TypeAdapter``,
    ``model_validate`` -- and reaches ``Base(**data)`` not at all, because
    ``BaseModel.__init__`` validates with ``self_instance=self`` and the object is already
    allocated.  So all four are asserted, on the same payload, for each arm.

    The payload is DRAWN from the branch's own node rather than written, so this cannot
    pass by hand-picking an instance that happens to resolve.  ``strict_validate`` is the
    fifth path and is graded by ``check_pair``; it is included here because it is the
    production entry point and it must agree with the other four about the class.
    """
    assert emitted_unions()
    graded_arms = 0
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))

        class Holder(BaseModel):
            v: base  # type: ignore[valid-type]

        adapter = TypeAdapter(base)
        for branch in base._branch_models:
            payload = _an_instance(schema_at(branch.__adcp_schema__))
            assert type(base.model_validate(payload)) is branch, (document, branch, payload)
            assert type(adapter.validate_python(payload)) is branch, (document, branch)
            assert type(Holder.model_validate({"v": payload}).v) is branch, (document, branch)
            assert type(base(**payload)) is branch, (document, branch)
            assert type(base.strict_validate(payload)) is branch, (document, branch)
            graded_arms += 1
    assert graded_arms == sum(
        len(bundle.read(BUNDLE, d)[lower_union.keyword(bundle.read(BUNDLE, d))])
        for d in emitted_unions()
    ), graded_arms


def _an_instance(schema: dict) -> Any:
    """One instance the schema admits, drawn rather than written."""
    drawn: list[Any] = []

    @settings(
        max_examples=1,
        deadline=None,
        database=None,
        derandomize=True,
        phases=[Phase.generate],
        suppress_health_check=list(HealthCheck),
    )
    @given(st.data())
    def body(data: st.DataObject) -> None:
        from hypothesis_jsonschema import from_schema

        drawn.append(data.draw(from_schema(schema)))

    body()
    return drawn[0]


def test_a_consumers_subclass_of_a_union_base_keeps_its_own_schema() -> None:
    """§4's declaring-class test, and the thing membership cannot express.

    The base is the class that DECLARES ``_branch_models``.  A subclass declared
    elsewhere -- which is how D7 says a consumer refines an emitted class -- inherits the
    attribute and so is NOT the base, and gets its own model shape back.  Membership
    (``cls in cls._branch_models``) admits both "is a branch" and "is an unrelated
    subclass", and it is only the second that matters once the schema is being replaced:
    under membership a consumer's refinement would be validated as the union and come
    back as a BRANCH, discarding the consumer's own fields.

    Asserted on every emitted union root, with the refinement declared here -- outside the
    generated module, which is the position the rule is about.
    """
    assert emitted_unions()
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))
        branch = base._branch_models[0]

        class Refinement(base):  # type: ignore[misc, valid-type]
            mine: int | None = None

        assert "_branch_models" not in Refinement.__dict__
        arm = _an_instance(schema_at(branch.__adcp_schema__))
        got = Refinement.model_validate({**arm, "mine": 7})
        assert type(got) is Refinement, (document, type(got))
        assert got.mine == 7, document
        # and the branches still get their own shape, which is the other half of the rule.
        # The arm's OWN payload, because a branch whose node declares
        # ``additionalProperties: false`` refuses ``mine`` -- correctly, and that is a fact
        # about the branch's document rather than about the dispatch.
        assert type(branch.model_validate(arm)) is branch, document


def test_model_dump_json_on_a_union_base_instance_does_not_raise() -> None:
    """§4's fourth part: the union is the validator and never the serializer.

    Put it in the serialization slot and the class has no serializer for an instance of
    itself -- the union's serializer matches no branch, infers a model, finds the same
    union and recurses.  Measured on a fixture while this was being built:
    ``model_dump_json`` raises ``PydanticSerializationError: Circular reference detected``
    and ``model_dump()`` silently returns the model INSTANCE instead of a dict, which is
    the worse of the two because nothing reports it.

    Both halves are asserted, on a BASE instance (reached through ``model_construct``,
    since every validating path returns a branch) and on a BRANCH reached through a
    base-typed field -- the second is what fails if the wrap serializer holds the base's
    model schema ALONE rather than the branches' union with the base last.
    """
    assert emitted_unions()
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))

        class Holder(BaseModel):
            v: base  # type: ignore[valid-type]

        assert json.loads(base.model_construct().model_dump_json()) == {}
        assert base.model_construct().model_dump() == {}

        branch = base._branch_models[0]
        payload = _an_instance(schema_at(branch.__adcp_schema__))
        instance = base.strict_validate(payload)
        # the arm's own fields survive the base-typed field, which is what the union in
        # the serialization slot buys and the base's model schema alone loses
        dumped = json.loads(Holder(v=instance).model_dump_json())["v"]
        assert set(payload) <= set(dumped), (document, sorted(payload), sorted(dumped))


def test_a_payload_no_branch_admits_is_refused_in_the_documents_own_vocabulary() -> None:
    """``_branch_combinator()``, and why it is a fact the emitter has to write.

    A document satisfying no branch fails each branch at FIELD validation, where pydantic
    reports ``missing`` -- a keyword the document does not use.  The mixin re-labels that
    with the document's own combinator, which is not recoverable at run time from the
    branches.

    Graded two ways, because the tree does not exercise both arms: every emitted union
    root is ``oneOf`` (6 of 6), so the ``anyOf`` arm is graded on a fixture.  Said rather
    than left to be discovered: hard-coding ``"oneOf"`` in the lowering would redden
    nothing in the population and only the fixture below.
    """
    assert emitted_unions()
    assert {lower_union.keyword(bundle.read(BUNDLE, d)) for d in emitted_unions()} == {"oneOf"}
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))
        with pytest.raises(ValidationError) as caught:
            base.model_validate({"__adcp_harness__": "no branch admits this"})
        assert [e["type"] for e in caught.value.errors()] == ["oneOf"], (
            document,
            caught.value.errors(),
        )

    # the anyOf arm, and the _ROOT_REQUIRED split, neither of which the population reaches
    class AnyOfBase(BranchDispatchMixin, AdCPBaseModel):
        __adcp_schema__ = SchemaRef("fixture.json", "#")
        _branch_models: ClassVar[tuple[type, ...]] = ()
        _ROOT_REQUIRED: ClassVar[tuple[str, ...]] = ("root_key",)

        @classmethod
        def _branch_combinator(cls) -> str:
            return "anyOf"

        root_key: str | None = None

    class Arm(AnyOfBase):
        __adcp_schema__ = SchemaRef("fixture.json", "#/anyOf/0")
        tag: Literal["arm"]

    AnyOfBase._branch_models = (Arm,)
    AnyOfBase.model_rebuild(force=True)

    with pytest.raises(ValidationError) as caught:
        AnyOfBase.model_validate({"root_key": "present", "tag": "wrong"})
    assert [e["type"] for e in caught.value.errors()] == ["anyOf"]

    # ... and ``_ROOT_REQUIRED`` is what separates the two kinds on that same path: the
    # payload below also satisfies no branch, and the reason the DOCUMENT refuses it is a
    # field the root requires, not the choice of arm.  pydantic reports neither -- it
    # reports one ``missing`` per field per branch -- which is why the root's required set
    # has to be written onto the class.
    with pytest.raises(ValidationError) as caught:
        AnyOfBase.model_validate({"tag": "wrong"})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("required", ("root_key",))]
    # The control: a payload that DOES satisfy the arm is accepted, so the two refusals
    # above are not a base that refuses everything.
    assert type(AnyOfBase.model_validate({"root_key": "p", "tag": "arm"})) is Arm


def test_the_serializer_is_set_on_the_schema_the_wrapper_holds_and_not_on_a_definitions_node() -> None:
    """§4's last sentence, which the emitted population does not reach.

    §4 says the ``serialization`` key goes on the schema the wrapper HOLDS because "most
    roots come back as a ``definitions`` node wrapping the ``function-wrap``", and a
    ``serialization`` key on a ``definitions`` node is not consulted.  **Measured on this
    step's own output, none of the 6 bases does**: ``handler(source)`` returns
    ``{"type": "model"}`` for all six, because ``lower/union.py`` refuses a root that
    declares its own properties, so an emitted base has no field to reference anything and
    its schema has no definitions to hoist.

    So the clause is live code with 0 sites in the tree, and it is graded here instead --
    by handing the hook a handler that returns a ``definitions`` node and asserting where
    the key landed.  Said rather than left implicit: perturbing the unwrap reddens this
    test and nothing else.
    """
    from pydantic_core import core_schema

    model_node = core_schema.model_schema(
        A2UIBoundValueStub := type("A2UIBoundValueStub", (), {}), core_schema.any_schema()
    )
    wrapped_in_definitions = core_schema.definitions_schema(model_node, [core_schema.int_schema()])

    class Handler:
        def __call__(self, source: Any) -> Any:
            return json.loads(json.dumps(wrapped_in_definitions, default=str)) or wrapped_in_definitions

        def generate_schema(self, obj: Any) -> Any:
            return core_schema.any_schema()

    class Fixture(BranchDispatchMixin):
        _branch_models: ClassVar[tuple[type, ...]] = (A2UIBoundValueStub,)

    got = Fixture.__get_pydantic_core_schema__(Fixture, Handler())
    assert got["type"] == "definitions", got["type"]
    assert "serialization" not in got, "a serialization key on a definitions node is not consulted"
    assert got["schema"]["type"] == "function-wrap", got["schema"]["type"]
    assert got["schema"]["serialization"]["type"] == "function-wrap"

    # and the other arm: a plain model schema comes back as the function-wrap itself
    class PlainHandler(Handler):
        def __call__(self, source: Any) -> Any:
            return core_schema.model_schema(A2UIBoundValueStub, core_schema.any_schema())

    plain = Fixture.__get_pydantic_core_schema__(Fixture, PlainHandler())
    assert plain["type"] == "function-wrap", plain["type"]
    assert plain["serialization"]["type"] == "function-wrap"

    # the measurement the docstring states, re-taken here so it cannot go stale silently
    assert emitted_unions()
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))
        assert base.model_fields == {}, (document, sorted(base.model_fields))


def test_a_branch_with_no_derivable_name_refuses_its_document_by_name_and_pointer() -> None:
    """D3's last rule, which is to refuse.

    A branch is named by its ``title``, else by the discriminator ``const``, else by its
    sorted required set.  A branch with none of those has no identity, and the rule a
    previous generator reached for -- name the sole classed branch after its PARENT --
    makes a class name a function of what its siblings happen to be, so adding a branch
    renames an unrelated class.

    Graded on a bundle of its own, because the refusal has to be reachable with every
    OTHER keyword satisfied: in the 3.2 bundle a nameless branch always sits beside a
    keyword that refuses first, so a test over the bundle would assert the wrong refusal.
    The control is the same document with a title added, which emits.
    """
    nameless = {
        "title": "Nameless",
        "type": "object",
        "oneOf": [
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]},
        ],
    }
    (BUNDLE_FIXTURE := Path(tempfile.mkdtemp())) / "x.json"
    (BUNDLE_FIXTURE / "x.json").write_text(json.dumps(nameless))
    out = emit.emit(BUNDLE_FIXTURE, ["x.json"])
    assert out.emitted == {}
    assert out.refusals["x.json"]["keyword"] == "title", out.refusals
    assert out.refusals["x.json"]["pointer"] == "/oneOf/0", out.refusals

    titled = json.loads(json.dumps(nameless))
    titled["oneOf"][0]["title"] = "The First Arm"
    (BUNDLE_FIXTURE / "x.json").write_text(json.dumps(titled))
    control = emit.emit(BUNDLE_FIXTURE, ["x.json"])
    assert control.refusals == {}, control.refusals
    assert "TheFirstArm" in control.files["x.py"], control.files["x.py"]
    shutil.rmtree(BUNDLE_FIXTURE)


def test_every_union_root_the_step_does_not_emit_is_refused_by_name_pointer_and_keyword() -> None:
    """The step's own arithmetic: 126 union roots, 10 emitted and 116 refused, each named.

    The by-keyword profile is asserted as a WHOLE rather than as a total, because the
    profile is the readable result of the step -- it says which later step unblocks what.
    ``allOf`` dominating is the measurement that says this step is not the bottleneck:
    64 of the 150 are waiting on step 4.
    """
    out = emit.emit(BUNDLE, population())
    roots = union_roots()
    emitted = [d for d in roots if d in out.emitted]
    refused = [d for d in roots if d in out.refusals]
    assert len(roots) == 126
    # 10 and not the 6 this lane measured alone, over a population of 126 and not
    # 156: roots emit only once another step's row is beside this one -- a nested
    # ``enum`` (step 3), a nested container (step 6) -- and the 30 presence-only
    # combinators left for step 7.  Joint unblocking, which no single lane reaches.
    assert len(emitted) == 10, emitted
    assert len(refused) == 116
    assert len(emitted) + len(refused) == len(roots)
    assert emitted == emitted_unions()

    profile: dict[str, int] = {}
    for document in refused:
        row = out.refusals[document]
        assert row["keyword"] and row["pointer"], document
        profile[row["keyword"]] = profile.get(row["keyword"], 0) + 1
    assert profile == {
        "allOf": 51,  # step 4
        "type": 11,  # a node with properties and no type admits a non-object
        "$ref": 10,  # a bare-$ref branch has no node to declare a subclass from
        "properties": 10,  # a root conjunct; see lower/union.py's docstring
        "definitions": 7,
        "not": 7,  # step 7 (D6) at a position the rules row does not reach
        "uniqueItems": 5,  # step 7 (D6)
        "anyOf": 3,  # a nested union
        "enum": 2,  # a member type no enumeration base exists for
        "if": 2,  # step 7 (D6)
        "$defs": 2,
        "const": 2,
        "oneOf": 1,
        "additionalProperties": 1,
        "enumMetadata": 1,
        "pattern": 1,  # D5's alias module (a constraint inside a container)
    }, profile


def test_an_object_node_with_properties_and_no_type_refuses_because_it_admits_a_non_object() -> None:
    """The narrowing step 5's branches were the first population to reach.

    JSON Schema applies ``properties`` only to objects and asserts nothing about anything
    else, so ``{"properties": {...}, "required": [...]}`` with no ``type`` ADMITS a
    string and a number.  No class can, so the model is narrower than its document -- and
    it is the accepts check that reports it, as ``model_type`` on a valid instance.

    ``lower_object`` read ``type in (None, "object")`` until this step, and 0 of the 43
    documents emitted before it exercise the ``None`` arm, so the tolerance was latent.
    Both halves are asserted here: that the document really does admit a non-object, and
    that the emitter now refuses at ``type``.

    Two union roots left the emitted set when this was fixed --
    ``core/activation-key.json`` and ``core/reporting-write-destination.json``, whose
    branches declare no ``type`` -- and both were reporting
    ``accepts:model_refused_valid`` before it.
    """
    node = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    for admitted in ("hello", 42, [1], {"a": "x"}):
        assert jsonschema.Draft7Validator(node).is_valid(admitted), admitted

    into = Path(tempfile.mkdtemp())
    (into / "x.json").write_text(json.dumps({"title": "X", **node}))
    out = emit.emit(into, ["x.json"])
    assert out.refusals["x.json"]["keyword"] == "type", out.refusals
    (into / "x.json").write_text(json.dumps({"title": "X", "type": "object", **node}))
    assert emit.emit(into, ["x.json"]).refusals == {}  # the control: type: object emits
    shutil.rmtree(into)

    # and no document emitted before this step relied on the tolerance
    assert [d for d in sorted({g.ref.document for g in graded()})
            if bundle.read(BUNDLE, d).get("type") is None and "properties" in bundle.read(BUNDLE, d)] == []


def test_a_model_only_type_is_excused_only_where_the_document_forces_it() -> None:
    """``harness._entails_type``, in both directions, and why it is not a tolerance.

    §4's base is a pydantic model, so it renders ``type: object``; 7 of this bundle's
    union roots state their branches' type and not their own, and a ``const`` property
    renders ``{"const": ..., "type": ...}`` where the document states only the ``const``.
    Both are facts the model states and the document does not, which the symmetric
    comparison reports as a narrowing -- correctly, as a rule, and wrongly for these,
    because the document's own node already admits only instances of that type.

    So the predicate is asked of the DOCUMENT and this grades it three ways:

    * every site the rule excuses in the committed tree really does have a document that
      refuses an instance of every other type -- asserted against ``jsonschema``, not
      asserted of the rule;
    * a typeless node with nothing forcing a type is still reported;
    * the two derivations are each reached, so neither is dead.
    """
    from codegen.harness import _entails_type

    # Direction 1: every site the rule excuses in the committed tree, with the DOCUMENT
    # asked whether it really refuses an instance of every other type.  The sites are
    # enumerated off the tree rather than listed, so a new one is graded by itself.
    excused: list[tuple[SchemaRef, str, str]] = []
    for g in graded():
        if not isinstance(g.model, type):
            continue
        doc = schema_at(g.ref)
        nodes = [("", doc), *sorted((doc.get("properties") or {}).items())]
        for where, node in nodes:
            if not isinstance(node, dict) or "type" in node:
                continue
            for kind in sorted(_NOT_OF_TYPE):
                if not _entails_type(node, kind):
                    continue
                excused.append((g.ref, where, kind))
                for other in _NOT_OF_TYPE[kind]:
                    assert not jsonschema.Draft7Validator(node).is_valid(other), (
                        g.ref,
                        where,
                        kind,
                        other,
                    )
    kinds = {k for _, _, k in excused}
    # One per union base whose root states no ``type`` of its own, plus the 2
    # const-pinned branch properties of ``core/destination.json`` whose node states
    # only the ``const``.
    assert len(excused) == 10, excused
    assert kinds == {"object", "string"}, kinds
    assert sum(1 for _, where, _ in excused if where == "") == 8, excused
    assert sum(1 for _, where, _ in excused if where != "") == 2, excused

    # direction 2: nothing forcing a type is still reported
    assert _entails_type({"properties": {"a": {"type": "string"}}}, "object") is False
    assert _entails_type({}, "string") is False
    assert _entails_type({"minLength": 1}, "string") is False
    # a combinator whose branches disagree, or which leaves one typeless, forces nothing
    assert _entails_type({"oneOf": [{"type": "object"}, {"type": "string"}]}, "object") is False
    assert _entails_type({"oneOf": [{"type": "object"}, {}]}, "object") is False
    # ... and the comparison still reddens for a model that invents one
    narrower = compare_schema(
        {"properties": {"a": {}}},
        TypeAdapter(Annotated[str, Field(min_length=1)]),
    )
    assert narrower.outcome != "pass", narrower

    # direction 3: both derivations are reached
    assert _entails_type({"const": "platform"}, "string") is True
    assert _entails_type({"const": 3}, "integer") is True
    assert _entails_type({"const": True}, "boolean") is True  # and not "integer"
    assert _entails_type({"const": True}, "integer") is False
    assert _entails_type({"oneOf": [{"type": "object"}, {"type": "object"}]}, "object") is True
    assert _entails_type({"anyOf": [{"type": "object"}, {"type": "object"}]}, "object") is True


#: A value of every type other than the keyed one, for the refusal check above.
_NOT_OF_TYPE = {
    "string": [1, True, {}, [], None],
    "object": ["s", 1, True, [], None],
    "integer": ["s", {}, [], None, 1.5],
    "number": ["s", {}, [], None],
    "boolean": ["s", {}, [], None],
    "array": ["s", 1, True, {}, None],
    "null": ["s", 1, True, {}, []],
}


def test_the_dispatch_table_is_unordered_so_two_rows_claiming_one_document_is_a_build_failure() -> None:
    """§ Layout: a document selected by two rows is a build failure, not a precedence
    puzzle.

    The rows in the table are disjoint -- which is what the union clause in
    ``bundle.declares_its_own_root_kind`` is for: without it ``is_object_root`` and
    ``union_root`` both claim 35 documents and ``is_scalar_root`` and ``union_root`` both
    claim 1.  That disjointness is asserted over the whole bundle below, and the failure
    ITSELF is graded on a table built to collide, because no bundle document can reach it.
    """
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        selecting = [low.__name__ for selector, low in emit.ROWS if selector(doc)]
        assert len(selecting) <= 1, (document, selecting)
    # the control: every row of the table selects something, so the assertion above is not
    # satisfied by a table nothing matches
    claimed = {low.__name__: 0 for _, low in emit.ROWS}
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        for selector, low in emit.ROWS:
            if selector(doc):
                claimed[low.__name__] += 1
    assert all(claimed.values()), claimed

    from codegen.lower import union

    collides = ((lambda d: True, emit._object_root), (lambda d: True, emit._union_root))
    with mock.patch.object(emit, "ROWS", collides):
        with pytest.raises(emit.AmbiguousRoot, match="all select this root"):
            emit.lower_document(PAGINATION, bundle.read(BUNDLE, PAGINATION))


def test_a_union_lowering_is_reached_only_through_the_table_and_the_table_is_the_population() -> None:
    """A row cannot claim a document its step does not count.

    The selector IS the population test -- ``bundle.union_root`` is both the dispatch row's
    predicate and what ``union_roots()`` counts here -- and the lowering reads its keyword
    through ``lower.union.keyword``, which is where it lives and which the selector is
    built ON -- D13's import rule makes the lowering own the read and ``bundle`` read it.  So
    there is no second definition of "is a union root" for the two to disagree through.
    """
    from codegen.lower import rules, union

    assert union.keyword is not None
    rows = [low for selector, low in emit.ROWS if selector is bundle.union_root]
    assert rows == [emit._union_root], rows
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        # The row's selector is the lowering's own read NARROWED by step 7's: a
        # combinator of ``required`` groups carries the keyword and is a rule, not a
        # union, and ``bundle.union_root`` is where the two steps' readings meet
        # (a lowering cannot import another lowering, D13).  So the selector implies
        # the keyword and not the reverse, and the gap is exactly the presence-only
        # roots -- asserted in both directions, so neither can drift.
        if bundle.union_root(doc):
            assert union.keyword(doc) is not None, document
        elif union.keyword(doc) is not None:
            kw = union.keyword(doc)
            assert rules.presence_only({kw: doc[kw]}), document


def _pydantic_names(json_schema_keywords: set[str]) -> set[str]:
    """The ``Field`` kwarg each JSON Schema constraint renders as.

    Derived from the compiler's own ``Constraints`` model, which declares every
    field under its JSON-Schema alias -- so this mapping is the compiler's and
    not a second copy of it that could drift.
    """
    from datamodel_code_generator.model.pydantic_v2.base_model import Constraints

    by_alias = {f.alias: name for name, f in Constraints.model_fields.items() if f.alias}
    # ``minItems``/``maxItems`` are the one place the alias table is a step short of
    # the rendering: pydantic v2 bounds a LIST with ``min_length``/``max_length``,
    # and dmcg renders ``Field(min_length=1)`` for a document's ``minItems: 1`` --
    # measured on ``brand/get-brand-identity-request.json``'s ``fields``, which step
    # 6's array row is what made reachable.  Both spellings are admitted for those
    # two keywords, so the test still refuses a kwarg no keyword of the document
    # renders.
    extra = {"minItems": "min_length", "maxItems": "max_length"}
    out = {by_alias[k] for k in json_schema_keywords if k in by_alias}
    return out | {extra[k] for k in json_schema_keywords if k in extra}


def test_a_scalar_root_emits_an_annotated_alias_and_not_a_class() -> None:
    """D2's root-scalar row: a node with no field to hang itself on is an alias.

    A wrapper class would be a second name for the same node (P2), and every
    referencing model would then carry an object where the document carries a
    string.  The alias carries its document's own ``description``, which an
    earlier rendering dropped at all five of this population's scalar roots
    because an alias has no docstring slot -- a ``Field(description=...)`` does.

    The population is ``bundle.is_scalar_root`` itself and not ``type in SCALAR``,
    because those are two different sets: all 214 of the bundle's root enums
    declare ``type: "string"``, and D2 makes them CLASSES.  Reading the row's own
    selector is what keeps this test from asserting the scalar row's outcome over
    the enumeration row's documents.
    """
    graded_aliases = 0
    for document in sorted({g.ref.document for g in graded()}):
        doc = bundle.read(BUNDLE, document)
        if not bundle.is_scalar_root(doc):
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
# step 6: containers and mappings
# --------------------------------------------------------------------------- #
def _constructed(doc: dict, *, binds: dict[str, Any] | None = None) -> tuple[Any, str]:
    """Lower a document written HERE, and return its model and the module text.

    A constructed document is not in the shipped package, so ``_document`` cannot
    read it and ``strict_validate`` has no schema -- which is why a constructed pair
    is graded by ``compare_schema`` and by an ``accept`` the test builds from the same
    document, exactly as the narrowing fixture above is.  Everything else is the real
    pipeline: the walk decides, the compiler renders, and the text is executed rather
    than inspected, so a test cannot pass on a rendering that does not run.

    ``binds`` supplies a symbol for a ``$ref``, keyed by the target's document path.
    The import the walk emits names a sibling MODULE, which does not exist here, so
    the symbol is pre-bound in the namespace instead -- the import itself is asserted
    separately, off ``mod.imports``.
    """
    targets = binds or {}

    def bind(uri: str, pointer: str) -> compiler.Target:
        for path, (name, _type) in targets.items():
            if uri.endswith(path):
                module = f".{path.rsplit('/', 1)[-1].removesuffix('.json')}"
                return compiler.Target(module, name)
        raise AssertionError(f"the fixture binds no target for {uri}")

    mod, symbol = emit.lower_document("constructed.json", doc, bind)
    text = emit.render(mod, symbol)
    module = types.ModuleType("_constructed_fixture")
    module.__dict__.update({name: type_ for name, type_ in targets.values()})
    # D5's aliases are reached by an ABSOLUTE import, so they survive the strip
    # below -- and a constructed document can derive a shape the INSTALLED module
    # has no site for, which is an ``ImportError`` here rather than a test failure
    # anyone can read.  The RUN's own alias module is the emitter's output, so it is
    # executed into this namespace and its import line dropped: the same pre-binding
    # a ``$ref`` target gets, for the same reason, and the annotation stays the
    # compiler's.
    if mod.aliases:
        exec(constraints_module.declare(mod.aliases), module.__dict__)  # noqa: S102
    alias_import = f"from {constraints_module.MODULE} import"
    # Registered, because ``from __future__ import annotations`` makes every
    # annotation a string and pydantic resolves it against the defining module's
    # globals -- a bare ``exec`` dict has no module to be found through.
    sys.modules[module.__name__] = module
    try:
        exec(  # noqa: S102 -- executing the compiler's own output is the point
            "\n".join(
                line
                for line in text.splitlines()
                if not line.startswith("from .") and not line.startswith(alias_import)
            ),
            module.__dict__,
        )
    finally:
        del sys.modules[module.__name__]
    return module.__dict__[symbol], text


def _accept_of(doc: dict, model: Any) -> Any:
    """The entry point a constructed pair is offered instances through.

    The schema half first and the constructor second, which is the order
    ``strict_validate`` uses -- so the accepts check here measures the same thing it
    measures on a shipped class.
    """

    def accept(payload: Any) -> Any:
        jsonschema.Draft7Validator(
            doc, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER
        ).validate(payload)
        return model.model_validate(payload) if isinstance(model, type) else payload

    return accept


def test_the_dispatch_table_is_a_partition_and_a_collision_is_a_build_failure() -> None:
    """``emit.ROWS`` is unordered, so disjointness is the property that makes it work.

    Both halves, because the first alone passes for a table whose rows happen not to
    overlap on THIS bundle and the second alone passes for a table nothing selects:

    * over the whole bundle, no document is selected by more than one row -- and the
      count selected by exactly one is asserted, so the partition is not satisfied by
      a table that selects nothing;
    * a document two rows DO select raises rather than picking one, which is the
      difference between a build failure and a precedence puzzle.

    The second is graded on a selector added here, because the bundle has no document
    that collides -- which is the whole claim of the first half, so a fixture is the
    only way to reach the branch.
    """
    documents = bundle.portable(BUNDLE)
    by_count: dict[int, int] = {}
    for document in documents:
        doc = bundle.read(BUNDLE, document)
        n = sum(1 for selector, _ in emit.ROWS if selector(doc))
        by_count[n] = by_count.get(n, 0) + 1
    assert sorted(by_count) == [0, 1], by_count  # never two
    assert by_count[1] == 1033, by_count  # the six rows' own population
    assert by_count[0] == 21, by_count  # no row yet: a later step's

    both = {"title": "Both", "type": "object", "properties": {"a": {"type": "string"}}}
    assert bundle.is_object_root(both)
    rows = (*emit.ROWS, (lambda _doc: True, emit._object_root))  # noqa: SLF001 -- the collision fixture
    with patch.object(emit, "ROWS", rows), pytest.raises(emit.AmbiguousRoot) as caught:
        emit.lower_document("both.json", both)
    assert "all select this root" in str(caught.value)
    assert "is_object_root" in str(caught.value)


def test_an_arrays_bound_is_the_lists_and_not_its_elements() -> None:
    """Step 6's first defect, over every array site the emitted population has.

    The generator this pipeline replaces read ``minItems`` on a named property and
    carried it and read the same keyword on a mapping value and dropped it.  So the
    assertion is on WHICH NODE the bound landed on, site by site, derived from the
    document rather than from a list:

    * the document's ``minItems``/``maxItems`` reach the model's own schema at the
      ARRAY, where pydantic spells them ``minItems``/``maxItems`` again;
    * the element's node carries no length fact the document does not state there,
      which is what "not on its elements" means -- a bound moved down renders
      ``minLength`` on the item and the array unbounded.

    Both denominators are asserted, so neither half can pass by looking at nothing.
    """
    arrays = 0
    bounded = 0
    for row in graded():
        if row.ref.pointer != "#" or not isinstance(row.model, type):
            continue
        if not hasattr(row.model, "model_json_schema"):
            continue  # D2's enumeration row emits a class that is not a model
        doc = schema_at(row.ref)
        emitted = row.model.model_json_schema()
        for key, sub in (doc.get("properties") or {}).items():
            if sub.get("type") != "array":
                continue
            arrays += 1
            mine = _unwrap(emitted["properties"][compiler.field_name(key)], emitted.get("$defs", {}))
            assert mine.get("type") == "array", (row.ref, key, mine)
            for keyword in ("minItems", "maxItems"):
                assert mine.get(keyword) == sub.get(keyword), (row.ref, key, keyword, mine)
                bounded += keyword in sub
            item = _unwrap(mine.get("items") or {}, emitted.get("$defs", {}))
            declared = sub.get("items") or {}
            for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
                assert item.get(keyword) == declared.get(keyword), (row.ref, key, keyword, item)
    # The denominator is TOP-LEVEL array properties of an emitted root, not every
    # array node: an array nested inside another array's ``items`` has no property
    # node of its own to compare at and is graded by the schema comparison instead.
    # Stated so the number is not read as "every array".
    assert arrays == 46, arrays
    assert bounded == 24, bounded


def test_unique_items_refuses_because_the_compiler_renders_nothing_for_it() -> None:
    """Why ``uniqueItems`` is step 7's rule (D6) and not this row's constraint.

    The reason is a measurement and not a reading of D6: ``Constraints`` declares
    ``unique_items`` under the alias ``uniqueItems``, so the keyword is ACCEPTED and
    sets the field -- and the renderer then emits no ``Field`` at all, because
    pydantic v2 removed ``unique_items``.  Carrying it through ``constraints=`` would
    therefore be a model wider than its document, silently.

    Three cells: the keyword sets the constraints model, the rendering drops it, and
    the walk refuses rather than emitting the drop.  The first two are what make the
    third the only safe answer, so deleting any of them leaves the reason unstated.
    """
    from datamodel_code_generator.model.pydantic_v2.base_model import Constraints

    assert Constraints.model_fields["unique_items"].alias == "uniqueItems"
    assert Constraints(uniqueItems=True).model_fields_set == {"unique_items"}

    listed = compiler.Type(container="list", of=(compiler.Type("str"),))
    kept = compiler.render_alias("Kept", listed, {"minItems": 1})
    dropped = compiler.render_alias("Dropped", listed, {"uniqueItems": True})
    assert "min_length=1" in kept.text, kept.text
    assert "Field" not in dropped.text, dropped.text  # the fact has no rendering

    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "u.json",
            {
                "title": "U",
                "type": "object",
                "properties": {"a": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}},
            },
        )
    assert (caught.value.keyword, caught.value.pointer) == ("uniqueItems", "/properties/a")

    # And it is load-bearing on the bundle: these documents are refused for this
    # keyword and no other, so admitting it would emit them wide.
    out = emit.emit(BUNDLE, population())
    blocked = {d for d, r in out.refusals.items() if r["keyword"] == "uniqueItems"}
    assert len(blocked) == 45, sorted(blocked)
    assert "core/acceptance-policy-profile-ids.json" in out.refusals


def test_a_root_array_refuses_by_name_with_the_element_type_it_would_have_wrapped() -> None:
    """D2's ``RootModel[list[X]]`` row, and why it is a refusal rather than a class.

    All five root arrays of the bundle refuse on a keyword of a later step, so a
    ``RootModel`` base would be a class no document reaches and no pair grades.  The
    row therefore refuses -- and it lowers the ELEMENT first, so a real document
    reports its own blocker rather than the shape.

    Asserted on all five by name, with the keyword each one actually refuses on read
    off the run.  The shape refusal underneath is reached only by a document built to
    have nothing else wrong with it, which is the second half.
    """
    out = emit.emit(BUNDLE, population())
    roots = [d for d in bundle.portable(BUNDLE) if bundle.read(BUNDLE, d).get("type") == "array"]
    assert len(roots) == 5, roots
    assert all(d in out.refusals for d in roots), [d for d in roots if d not in out.refusals]
    assert {out.refusals[d]["keyword"] for d in roots} == {"uniqueItems", "discriminator"}
    # 4 of 5 on `uniqueItems` at the root; the fifth inside its own `items`.
    assert sum(out.refusals[d]["keyword"] == "uniqueItems" for d in roots) == 4
    (odd,) = [d for d in roots if out.refusals[d]["keyword"] != "uniqueItems"]
    assert odd == "media-buy/product-refinement.json"
    assert out.refusals[odd]["pointer"].startswith("/items"), out.refusals[odd]

    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "r.json", {"title": "R", "type": "array", "items": {"type": "string"}}
        )
    assert (caught.value.keyword, caught.value.pointer) == ("type", "/")
    assert "RootModel[list[X]]" in caught.value.detail
    assert "str is the element type" in caught.value.detail


def test_a_mapping_is_a_dict_whose_key_comes_from_the_document() -> None:
    """D5's key rule, and the honest denominator for it.

    **No mapping site in the emitted population constrains its key.** Measured over
    the whole emitted set: every mapping the committed tree carries is
    ``dict[str, ...]``, and that is the document's own reading rather than a default
    -- silence about keys means every string, and typing it further would be the SDK
    inventing a constraint.  So the key rule is graded on constructed documents, and
    the zero is asserted rather than left for a reader to infer from a green mark.

    The one key kind that needs no name is the one that is graded behaviourally: a
    ``propertyNames`` ``$ref`` NAMES the key type, so the key is that type, the module
    IMPORTS it, and the model then refuses a key the key type refuses.  The kinds that
    would need D5's alias module refuse by name, and so does a closed key set.
    """
    constrained = 0
    mappings = 0
    for row in graded():
        doc = schema_at(row.ref)
        for pointer, node in bundle.nodes(doc):
            if node.get("type") == "object" and "properties" not in node:
                mappings += 1
                constrained += bool({"propertyNames", "patternProperties"} & set(node))
                del pointer
    assert mappings == 124, mappings
    assert constrained == 0, constrained

    # A $ref key: the key IS that type, imported, and it refuses what the type
    # refuses.  The bound symbol is an ``Annotated`` alias because that is what a
    # root-scalar reference TARGET actually is in this pipeline -- and a key type has
    # to be hashable, which a ``RootModel`` wrapper is not.
    Tag = Annotated[str, Field(pattern="^[a-z]+$")]
    doc = {
        "title": "Keyed",
        "type": "object",
        "properties": {
            "m": {
                "type": "object",
                "propertyNames": {"$ref": "https://x/core/tag.json"},
                "additionalProperties": {"type": "integer"},
            }
        },
    }
    model, text = _constructed(doc, binds={"core/tag.json": ("Tag", Tag)})
    assert "dict[Tag, int]" in text, text
    mod, _ = emit.lower_document(
        "constructed.json", doc, lambda *_: compiler.Target(".tag", "Tag")
    )
    assert (".tag", "Tag") in mod.imports
    model.model_validate({"m": {"abc": 1}})  # the key type admits it
    with pytest.raises(ValidationError):
        model.model_validate({"m": {"ABC": 1}})  # and refuses what it refuses

    # A constrained key would need D5's alias module, which this row does not build.
    for key_node, keyword in (
        ({"type": "string", "pattern": "^a"}, "pattern"),
        ({"type": "string", "minLength": 2}, "minLength"),
        ({"anyOf": [{"pattern": "^a"}, {"$ref": "https://x/core/tag.json"}]}, "anyOf"),
    ):
        with pytest.raises(Refusal) as caught:
            emit.lower_document(
                "k.json",
                {
                    "title": "K",
                    "type": "object",
                    "properties": {"m": {"type": "object", "propertyNames": key_node}},
                },
            )
        assert caught.value.keyword == keyword, (key_node, caught.value.keyword)

    # A ``patternProperties`` key carries the pattern that selected it, which is the
    # same annotated ``str`` and so the same refusal -- one owner for the key rule, so
    # a ``propertyNames`` pattern and a ``patternProperties`` pattern cannot come to be
    # read two different ways.
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "pp.json",
            {
                "title": "PP",
                "type": "object",
                "properties": {
                    "m": {"type": "object", "patternProperties": {"^x_": {"type": "integer"}}}
                },
            },
        )
    assert caught.value.keyword == "pattern", caught.value.keyword
    # Two patterns are two key types with two value types, which is not a dict[K, V].
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "pp2.json",
            {
                "title": "PP2",
                "type": "object",
                "properties": {
                    "m": {
                        "type": "object",
                        "patternProperties": {"^x_": {"type": "integer"}, "^y_": {"type": "string"}},
                    }
                },
            },
        )
    assert caught.value.keyword == "patternProperties", caught.value.keyword

    # A closed key set is a MODEL and not a mapping (D5), and its one type-position
    # site in this bundle sits in a document that refuses on `enum` first.
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "e.json",
            {
                "title": "E",
                "type": "object",
                "properties": {
                    "m": {"type": "object", "propertyNames": {"enum": ["mon", "tue"]}}
                },
            },
        )
    assert caught.value.keyword == "enum"
    assert "MODEL whose keys are its fields" in caught.value.detail
    hours = bundle.read(BUNDLE, "core/store-item.json")
    assert "enum" in hours["properties"]["hours"]["propertyNames"]
    # The document is refused, and on an even earlier blocker than its key set -- a
    # ``$ref`` whose target carries an ``enum``.  Which keyword fires first is not the
    # claim; that no document reaches the closed-key-set row is.
    assert "core/store-item.json" in emit.emit(BUNDLE, ["core/store-item.json"]).refusals


def test_a_typed_additional_properties_is_a_typed_pydantic_extra() -> None:
    """D8's typed row, graded on a constructed document because 0 reach it.

    Measured: 727 documents mention ``additionalProperties`` and 51 carry a typed one,
    and every one of the 51 also carries a keyword of step 3, 4, 5 or 7 -- so no
    document this step can emit has one.  The mechanism is built anyway because it is
    this row's named defect, and the zero is asserted so the row cannot be read as
    covered by the bundle.
    """
    typed = [
        d
        for d in bundle.portable(BUNDLE)
        if any(
            isinstance(n.get("additionalProperties"), dict) and n["additionalProperties"]
            for _, n in bundle.nodes(bundle.read(BUNDLE, d))
        )
    ]
    assert len(typed) == 51, len(typed)
    mentions = [
        d
        for d in bundle.portable(BUNDLE)
        if "additionalProperties" in bundle.schema_keywords(bundle.read(BUNDLE, d))
    ]
    assert len(mentions) == 727, len(mentions)
    out = emit.emit(BUNDLE, population())
    # 1 of the 51 is emitted, and it is the mapping path rather than the extras
    # store: ``error-details/vendor-error-codes.json``'s typed
    # ``additionalProperties`` sits on a node with NO ``properties``, so it is a
    # mapping and the row above lowers it.  The extras store needs a node with BOTH,
    # and all 14 of the bundle's sites with both sit under ``definitions``, which no
    # row descends into -- so the store is graded by the probe below and by 0
    # documents.
    assert sorted(set(typed) & set(out.emitted)) == ["error-details/vendor-error-codes.json"]

    doc = {
        "title": "Typed",
        "type": "object",
        "properties": {"a": {"type": "string"}},
        "additionalProperties": {"type": "integer"},
    }
    model, text = _constructed(doc)
    assert model.model_config["extra"] == "allow"
    assert "__pydantic_extra__: dict[str, int]" in text, text
    model.model_validate({"a": "x", "extra": 3})
    with pytest.raises(ValidationError):
        model.model_validate({"a": "x", "extra": "not an int"})


def test_a_multi_type_property_applies_each_keyword_to_its_own_branch() -> None:
    """Step 6's second defect: draft-07 applies a constraint to its own type only.

    Two live sites, both ``["number", "string"]`` on ``error-details/conflict.json``
    and both carrying no other keyword -- so the per-arm SPLIT has no live site and is
    graded on a constructed document.  Both denominators stated.

    Three cells, and the middle one is the defect:

    * a keyword lands on the arm whose type defines it, and the arm beside it is
      unconstrained -- the model admits a short string where the document does;
    * the same keyword applied to every arm makes the model NARROWER, which the
      accepts check sees;
    * a keyword no arm can carry constrains nothing and refuses by name, rather than
      being dropped into a model wider than its document.
    """
    live = [
        (row.ref, key)
        for row in graded()
        if row.ref.pointer == "#" and isinstance(row.model, type)
        for key, sub in (schema_at(row.ref).get("properties") or {}).items()
        if isinstance(sub.get("type"), list)
    ]
    assert len(live) == 2, live
    for ref, key in live:
        doc = schema_at(ref)
        model = next(r.model for r in graded() if r.ref == ref)
        node = model.model_json_schema()["properties"][compiler.field_name(key)]
        # pydantic has no spelling for a type LIST but a union, so the document's
        # ``["number", "string"]`` comes back as branches.  Compared on the branch
        # types, with D4's null branch (presence, not a type claim) dropped.
        branches = [b["type"] for b in node["anyOf"] if b.get("type") != "null"]
        assert sorted(branches) == sorted(doc["properties"][key]["type"]), (ref, key, node)
        # ... and the harness's own normalization folds it to the document's spelling,
        # which is what makes the schema comparison pass on these two.
        assert compare_schema(doc, model).outcome == "pass", compare_schema(doc, model).missing

    # **THE FOLD IS NOT A SILENCER**, and this is the assertion of it rather than the
    # argument.  A normalization that makes a red pair green is only correct if it
    # still reports the two ways a model can be wrong about a type list, so both are
    # measured against the same document: a model offering a type the document does
    # not is reported, and one offering fewer is reported too.  Without this a fold
    # that simply dropped the ``type`` comparison would pass every test above.
    listed = {"type": "object", "properties": {"v": {"type": ["number", "string"]}}}

    class Wider(AdCPBaseModel):
        v: float | str | bool | None = None

    class Narrower(AdCPBaseModel):
        v: float | None = None

    assert compare_schema(listed, Wider).outcome == "model_drops_a_fact"
    assert compare_schema(listed, Narrower).outcome == "model_drops_a_fact"
    # And a branch carrying more than a type is NOT folded, so a union of constrained
    # types keeps its branches and its constraints are still compared.
    assert harness._normalize(  # noqa: SLF001 -- the normalization under test
        {"anyOf": [{"type": "string", "minLength": 2}, {"type": "integer"}]}, {}
    ) == {"anyOf": [{"type": "string", "minLength": 2}, {"type": "integer"}]}

    # The bare case renders as a union of the document's own types, and nothing else.
    doc = {
        "title": "Multi",
        "type": "object",
        "required": ["v"],
        "properties": {"v": {"type": ["number", "string"]}},
    }
    model, text = _constructed(doc)
    assert "v: float | str" in text, text
    accept = _accept_of(doc, model)
    assert check_accepts(doc, accept, examples=50).outcome == "pass"
    assert compare_schema(doc, model).outcome == "pass", compare_schema(doc, model).missing

    # **A CONSTRAINED arm is NAMED, and this is the rendering that forces it to be.**
    # The split needs the bound on the ARM; the compiler's ``DataType`` carries no
    # constraint, so a keyword left on the node reaches the FIELD and bounds the whole
    # union -- the string's ``minLength`` applied to the integer arm. Measured here on
    # the compiler directly, so the alternative has its own evidence rather than a
    # reference to it.
    escaped = compiler.render_alias(
        "Escaped",
        compiler.Type(container="union", of=(compiler.Type("str"), compiler.Type("int"))),
        {"minLength": 4},
    )
    assert "Annotated[str | int, Field(min_length=4)]" in escaped.text, escaped.text

    # **D5's alias module removed that obstacle, and the node STILL refuses -- on the
    # grader rather than on the rendering.**  Both halves are asserted, because the
    # refusal's reason changed and a test that only re-asserted the refusal would not
    # have noticed.
    armed = {
        "title": "MS",
        "type": "object",
        "required": ["v"],
        "properties": {"v": {"type": ["string", "integer"], "minLength": 4}},
    }
    named = constraints_module.symbol("string", {"minLength": 4})

    # Half one: the arm IS nameable now, and that model's accepted set is the
    # document's -- the integer arm takes no string bound. Built by hand from the
    # alias the emitter would have used, because the emitter refuses to reach it.
    arm_alias = {"StrMinLen4": None}
    exec(constraints_module.declare({named: ("string", {"minLength": 4})}), arm_alias)  # noqa: S102

    class Armed(AdCPBaseModel):
        v: arm_alias[named] | int  # type: ignore[name-defined,valid-type]

    assert Armed.model_validate({"v": 1}).v == 1
    assert Armed.model_validate({"v": "abcd"}).v == "abcd"
    with pytest.raises(ValidationError):
        Armed.model_validate({"v": "abc"})  # the string arm keeps its own bound

    # Half two, and the reason the row refuses anyway: the comparison folds a model's
    # ``anyOf`` into a document's type LIST only where every branch is a bare type, so
    # it reads this FAITHFUL model as dropping both facts.  Emitting a node no check
    # can grade is what the refusal prevents.
    blind = compare_schema(armed, Armed)
    assert blind.outcome == "model_drops_a_fact", blind
    assert {m.split(": ")[0] for m in blind.missing} == {
        "/properties/v/type",
        "/properties/v/minLength",
    }, blind.missing

    with pytest.raises(Refusal) as caught:
        emit.lower_document("ms.json", armed)
    assert caught.value.keyword == "minLength", caught.value.keyword
    assert "every branch is a bare type" in caught.value.detail, caught.value.detail
    # And it costs no document: 0 multi-type node in an EMITTED document states
    # anything beyond its ``type``, which is why this is graded on a constructed one.
    from codegen.lower import containers as lower_containers

    emitted = emit.emit(BUNDLE, population()).emitted
    carried = frozenset().union(*lower_containers.ARM.values())
    assert [
        (d, p)
        for d in emitted
        for p, node in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(node.get("type"), list) and set(node) & carried
    ] == []

    # A null arm refuses too, and for the grader rather than the rendering.
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "mn.json",
            {
                "title": "MN",
                "type": "object",
                "properties": {"v": {"type": ["string", "null"]}},
            },
        )
    assert caught.value.keyword == "type"
    assert "cannot tell a DECLARED null" in caught.value.detail

    # A keyword no arm can carry constrains nothing, so it refuses by name.
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "m.json",
            {
                "title": "M",
                "type": "object",
                "properties": {"v": {"type": ["boolean", "null"], "minLength": 1}},
            },
        )
    assert caught.value.keyword in ("minLength", "type"), caught.value.keyword


def test_a_constraint_inside_a_container_is_named_and_a_format_still_refuses() -> None:
    """D5's alias module, read from the side it was built for, and the residual.

    A constraint on what is INSIDE a container has no slot in the compiler's
    ``DataType``, so putting the node in ``list[...]`` would drop the fact and widen
    the model.  **This test used to assert the REFUSAL that stood in for the answer**
    -- 15 documents over 8 distinct inner constraints, with the detail naming what
    D5's alias module would have to name -- and the alias module is what retires it.
    Naming the inner type is the whole of the fix: once the constraint is on the
    type, ``dict[str, StrMinLen1]`` and ``list[StrMatchingEFC12812]`` are plain
    references and ``_inner`` sees nothing to carry.

    Three halves, because the row did not disappear:

    * the inner type IS named, at 10 container positions in 7 modules;
    * the two documents the previous revision of this test named BY NAME as refused
      on an inner ``^[A-Z]{2}$`` now emit;
    * and what still refuses is a ``format`` no type is selected for, which would
      be DROPPED rather than carried -- 3 documents, all three on
      ``format: hostname`` inside an array's ``items``.

    That the inner fact survives into the model's rendered schema is graded by
    ``test_an_arrays_bound_is_the_lists_and_not_its_elements``, which compares the
    document's ``items`` keywords against the model's at every array property, so
    it is not restated here.
    """
    out = emit.emit(BUNDLE, population())
    inner = {
        d: r
        for d, r in out.refusals.items()
        if "D5" in r["detail"] and "no constraint inside a container" in r["detail"]
    }
    # Down from 15, and every survivor is a FORMAT rather than a constraint keyword:
    # a format with no selected type has nowhere to go inside a container, and the
    # comparison would not see it go (the accepts check draws through
    # `hypothesis_jsonschema`, which honours a format it knows).
    assert len(inner) == 3, sorted(inner)
    assert {r["keyword"] for r in inner.values()} == {"format"}
    for document, row in inner.items():
        node = bundle.read(BUNDLE, document)
        for part in row["pointer"].strip("/").split("/"):
            node = node[part]
        assert node["format"] == "hostname", (document, node)
        assert node["format"] not in emit.FORMAT_TYPES, "a selected type would not refuse"
        assert "hostname" in row["detail"], row

    # The two the previous revision asserted as REFUSED, now emitted -- read off the
    # run rather than off the tree, so this cannot pass on a stale file.
    for was_refused in ("brand/rights-terms.json", "property/property-list-filters.json"):
        assert was_refused in out.emitted, was_refused
        assert was_refused not in out.refusals, out.refusals.get(was_refused)

    # And the naming, counted: a container position whose INNER type is a symbol the
    # module imports from `adcp.types.constraints`.
    positions, modules = 0, set()
    for rel, text in sorted(out.files.items()):
        if not rel.endswith(".py"):
            continue
        parsed = ast.parse(text)
        aliases = {
            alias.name
            for n in ast.walk(parsed)
            if isinstance(n, ast.ImportFrom) and n.module == constraints_module.MODULE
            for alias in n.names
        }
        for n in ast.walk(parsed):
            if not (
                isinstance(n, ast.Subscript)
                and isinstance(n.value, ast.Name)
                and n.value.id in ("list", "dict")
            ):
                continue
            for name in ast.walk(n.slice):
                if isinstance(name, ast.Name) and name.id in aliases:
                    positions += 1
                    modules.add(rel)
    assert (positions, len(modules)) == (10, 7), (positions, sorted(modules))


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
    # The alias module is written BESIDE the tree, because an alias belongs to no
    # document and so has no domain to live under (D5), and it is public where
    # ``_schemas`` is not.  ``write`` takes that directory explicitly and has no
    # default for it, so a run over part of the population cannot replace the
    # committed module with a shorter one -- see ``emit.write``.
    emit.write(out, tmp_path / "_schemas", tmp_path)

    def tree(root: Path) -> dict[str, str]:
        return {
            str(p.relative_to(root)): p.read_text()
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }

    committed, fresh = tree(TREE), tree(tmp_path / "_schemas")
    assert sorted(fresh) == sorted(committed)
    for rel in sorted(fresh):
        assert fresh[rel] == committed[rel], rel
    assert sorted(out.beside) == ["constraints.py"], sorted(out.beside)
    for rel in sorted(out.beside):
        assert (tmp_path / rel).read_text() == (TREE.parent / rel).read_text(), rel


def test_two_constraints_deriving_one_alias_name_fail_the_build(monkeypatch) -> None:
    """Broken on purpose, because the guard cannot otherwise be reached.

    An alias's name is DERIVED, so two distinct constraints colliding is possible
    in principle -- a SHA-256 prefix collision is the realistic way -- and the
    damage is the worst kind: one alias annotating two fields, stating on one of
    them a constraint its own document does not. No bundle input can produce the
    collision, so the digest is forced to a constant and the real emitter is run.

    The ``_digest`` patch is also the control for the opposite mistake. The
    collision is caught at the ASSIGNMENT: a dict keyed by name cannot catch it
    afterwards, because the second write replaces the first and any later check
    re-derives the survivor and agrees with itself. Before ``record`` existed
    this run emitted a tree with one alias at two shapes and a GREEN suite.
    """
    monkeypatch.setattr(constraints_module, "_digest", lambda pattern: "C0111DED")
    with pytest.raises(constraints_module.AliasCollision) as caught:
        emit.emit(BUNDLE, population())
    assert "StrMatchingC0111DED" in str(caught.value), str(caught.value)
    assert "two distinct constraints" in str(caught.value)

    # The control: with the real digest, the same run resolves the same shapes and
    # does not raise -- so the guard is firing on the collision and not on the run.
    monkeypatch.undo()
    assert len(emit.emit(BUNDLE, population()).beside) == 1


def test_every_alias_the_tree_names_is_declared_and_every_declared_alias_is_named() -> None:
    """D5's alias module, in BOTH directions, with its denominators.

    ``test_the_emitted_tree_still_declares_every_module_it_imports`` (in
    ``tests/test_enum.py``) holds this obligation for a RELATIVE import and skips
    an absolute one, and an emitted module names ``adcp.types.constraints``
    absolutely -- so that test does not cover this edge and this one does. The
    failure it exists for is real and was met: a run whose alias module was not
    written left every module importing a symbol that did not exist, and the
    probe trees raised ``ImportError`` on ``StrMinLen2``.

    PROBED, by deleting one declared alias: the import direction reddens, but as
    an ``ImportError`` while this MODULE is collected rather than here -- the
    tree is imported at module scope to build the pairing. So that direction is
    a second statement of something already loud, and what this test adds is the
    REVERSE direction, the absolute-import spelling, and the denominators.

    The reverse direction is the one that catches the opposite defect: a module
    holding an alias no document needs. It is EMPTY today, and ``AdCPUrl`` is
    the one name that could legitimately sit in it -- D5 declares that one
    whatever the run met, so a consumer can import it -- but it does not,
    because ``FORMAT_TYPES`` points 23 modules' fields at it.
    """
    imported: dict[str, set[str]] = {}
    for module in sorted(TREE.rglob("*.py")):
        tree = ast.parse(module.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == constraints_module.MODULE:
                assert not node.level, (module, "an alias is imported absolutely")
                for alias in node.names:
                    imported.setdefault(alias.name, set()).add(str(module.relative_to(TREE)))

    declared = {
        node.targets[0].id
        for node in ast.parse((TREE.parent / "constraints.py").read_text()).body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    }
    assert declared, "the alias module declares nothing"
    assert set(imported) - declared == set(), "imported and not declared"
    assert declared - set(imported) == set(), "declared and never named"

    # The denominators, so neither direction can pass over an empty set: every
    # alias is reachable at this one path and nowhere else (no flat root, no
    # second spelling), and the module is not a dumping ground.
    assert len(declared) == 59, len(declared)
    # (module, alias) pairs, which is NOT the site count: a module importing one
    # alias for five of its fields contributes one pair.
    assert sum(len(where) for where in imported.values()) == 190, imported
    # And the one name that is a decision really is annotating fields.
    assert len(imported[constraints_module.URL]) == 23, sorted(imported[constraints_module.URL])


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
    # ``allOf`` and not ``not``: this fixture used ``not: {}``, which step 7 now
    # LOWERS (a ``not`` is a rule or the schema's own statement, never a refusal),
    # so the fixture stopped refusing anything and the test passed on a bundle
    # with no refusal in it.  ``allOf`` is step 4's row and still refuses, and
    # whichever row claims it next will move this fixture again -- which is the
    # point: the fixture has to name a keyword the tree genuinely cannot lower.
    (tmp_path / "no.json").write_text(
        json.dumps(
            {
                "title": "No",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "allOf": [{"required": ["a"]}],
            }
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
    # ``on required:`` and not ``on allOf:``: step 4's row claims this root now, so
    # the walk reaches the conjunct and names the keyword that actually stopped it --
    # a ``required``-only conjunct, which has no base to subclass and no properties to
    # declare.  The fixture still refuses, which is all this test needs; the keyword
    # moves with whichever row claims the root, and the comment above says so.
    assert "on required:" in done.stdout, done.stdout
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


# --------------------------------------------------------------------------- #
# step 7: D6's six keyword families
# --------------------------------------------------------------------------- #
#: One reference-free bundle document per step-7 keyword, chosen by SEARCHING the
#: bundle for the first document that carries the keyword and no ``$ref`` -- so
#: each is cheap to read and self-contained, and the selection is recorded here
#: rather than re-run, because a pinned case is what a later bundle change can be
#: seen to move.  ``then`` and ``else`` are listed separately because they are two
#: steps with two different rewrites, not one keyword with two spellings.
STEP7_CASES = {
    "uniqueItems": "core/acceptance-policy-profile-ids.json",
    "not": "core/account-timezone-capability.json",
    "then": "core/account-timezone-capability.json",
    "else": "core/reporting-consumer-status.json",
    "anyOf": "core/account-authorization.json",
    "oneOf": "a2ui/bound-value.json",
    "dependencies": "core/canvas-constraint.json",
    "minProperties": "a2ui/component.json",
    "maxProperties": "a2ui/component.json",
}

#: Step 7's EXIT condition, as a number per family: how many sites ``steps()``
#: finds over the whole 1,054-document portable population.  **Every one of these
#: was 0** before this step -- the nine keywords the harness stepped were wholly
#: disjoint from D6's six families, so every rule the step lowers would have been
#: graded by nothing in either direction.
STEP7_SITES = {
    "uniqueItems": (479, 198),
    "not": (469, 192),
    "then": (585, 186),
    "else": (58, 44),
    "anyOf": (450, 200),
    "oneOf": (212, 165),
    "dependencies": (85, 27),
    "minProperties": (48, 40),
    "maxProperties": (19, 10),
}


@functools.lru_cache(maxsize=1)
def _step_census() -> dict[str, tuple[int, int]]:
    """``keyword -> (sites, documents)`` over every portable document.

    Read off ``steps()`` itself, over the bundle, so a family that stopped being
    stepped shows as a 0 rather than as a test nobody noticed had gone quiet.
    """
    sites: dict[str, int] = {}
    documents: dict[str, set[str]] = {}
    for document in bundle.portable(BUNDLE):
        for s in steps(bundle.read(BUNDLE, document)):
            sites[s.keyword] = sites.get(s.keyword, 0) + 1
            documents.setdefault(s.keyword, set()).add(document)
    return {k: (v, len(documents[k])) for k, v in sites.items()}


def test_the_harness_steps_every_one_of_d6s_six_families() -> None:
    """The step's exit condition, with both denominators for each family.

    D6 names six families and the harness stepped NONE of them: its nine keywords
    were ``min``/``maxItems``, ``min``/``maxLength``, ``minimum``, ``maximum``,
    ``required``, ``additionalProperties``, ``pattern`` and ``enum``, and step 7's
    set is disjoint from that one.  So a rule could be emitted, carried, and wrong
    in either direction with nothing to report it -- the bundle's 485
    ``uniqueItems`` occurrences were 0 of 5,545 site rows.

    Pinned per family rather than summed: a total can stay put while one family
    falls to zero, and the family is the unit D6 is stated in.
    """
    census = _step_census()
    for keyword, (expected_sites, expected_documents) in STEP7_SITES.items():
        assert census.get(keyword) == (expected_sites, expected_documents), (
            keyword,
            census.get(keyword),
        )
    families = {
        "oneOf/anyOf over required": ("oneOf", "anyOf"),
        "if/then/else": ("then", "else"),
        "dependencies": ("dependencies",),
        "min/maxProperties": ("minProperties", "maxProperties"),
        "uniqueItems": ("uniqueItems",),
        "not": ("not",),
    }
    assert len(families) == 6
    for family, keywords in families.items():
        assert sum(census[k][0] for k in keywords) > 0, family
    assert sum(census[k][0] for ks in families.values() for k in ks) == 2405


def test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it() -> None:
    """The step as an INSTRUMENT: does it produce an instance the document refuses?

    Graded without any model, because that is the question: ``check_refuses``
    calls ``violated_keywords`` on the ORIGINAL document and counts an instance it
    does not refuse as the control firing.  ``accept`` here refuses nothing, so
    everything the step pushed out is read off ``examples - control_fired``.

    One family is deliberately NOT exclusive and is asserted as such.  Forcing a
    duplicate is the one thing draft-07 cannot say, so where the item schema's
    value set is not countable the ``uniqueItems`` step draws two elements from one
    schema and most draws differ: 6 of 20 bite on the pinned case and the control
    counts the other 14.  One refusal is enough to grade a site; reporting that as
    exclusive would be the claim that is false.
    """
    bit: dict[str, tuple[int, int]] = {}
    for keyword, document in STEP7_CASES.items():
        schema = bundle.read(BUNDLE, document)
        chosen = [s for s in steps(schema) if s.keyword == keyword]
        assert chosen, (keyword, document)
        examples = fired = 0
        for s in chosen:
            r = check_refuses(schema, lambda _instance: None, s, examples=20)
            assert not r.harness, (keyword, s.pointer, r.harness)
            examples += r.examples
            fired += r.control_fired
        bit[keyword] = (examples - fired, examples)
    assert bit == {
        "uniqueItems": (6, 20),  # two draws from one schema: not exclusive, by design
        "not": (60, 60),
        "then": (80, 80),
        "else": (20, 20),
        "anyOf": (20, 20),
        "oneOf": (20, 20),
        "dependencies": (20, 20),
        "minProperties": (20, 20),
        "maxProperties": (20, 20),
    }, bit


def test_an_unsatisfiable_step_is_no_evidence_and_not_a_harness_error() -> None:
    """A step with no violating instance graded nothing; it did not break.

    The two families that NEGATE part of a document can produce an unsatisfiable
    stepped document -- an ``if`` whose condition implies its branch, a
    combinator exhaustive over its type.  ``hypothesis`` raises ``Unsatisfiable``
    and ``check_refuses`` records it as the zero-denominator verdict, because
    reporting it as a harness error reddens the whole PAIR and a class with no
    violating instance at one site is not thereby unfaithful.

    Screening those sites out of ``steps()`` was tried and removed: asking
    ``canonicalish`` about the rewritten node cost 63.7 s against 0.0 s over 120
    documents and rejected 0 of 2,205 sites, so it was 500x the cost for no
    decision.  The classification is where the knowledge is cheap.
    """
    exhaustive = {
        "title": "Exhaustive",
        "type": "object",
        "properties": {"a": {"type": "string"}},
        "anyOf": [{"required": ["a"]}, {"not": {"required": ["a"]}}],
    }
    (s,) = [x for x in steps(exhaustive) if x.keyword == "anyOf"]
    r = check_refuses(exhaustive, lambda _instance: None, s, examples=10)
    assert r.unsatisfiable, r
    assert not r.harness, r.harness
    assert r.outcome == "no_evidence"
    assert r.refused + r.accepted_invalid == 0


def test_force_path_holds_a_sibling_if_through_then_and_else() -> None:
    """A site under a ``then`` is reachable only if its sibling ``if`` matches.

    Nothing made it match: ``hypothesis_jsonschema`` draws the minimal object and
    the condition is a ``const`` on an optional key, so the four ``maximum`` sites
    under ``core/canvas-constraint.json``'s ``then`` were graded by the control
    rather than by the model.  ``force_path`` now adds the condition as a conjunct
    of the node holding it, negated for an ``else``.

    Both rates, from the same inputs in the same process, which is what
    ``force=False`` exists for.

    **The forced side is pinned exactly and the unforced side is bounded**, and
    that asymmetry is measured rather than cautious: the unforced rate is 26 of 80
    in a fresh process and 32 of 80 under the suite, because
    ``hypothesis``'s derandomized stream is not identical across the two contexts.
    The forced rate is 0 of 80 in both, which is the hop's actual claim -- it
    makes the site reachable on EVERY example, so there is nothing left for the
    context to move.  Pinning 26 would be pinning the context.
    """
    document = "core/canvas-constraint.json"
    raw = bundle.read(BUNDLE, document)
    schema = bundle.resolved(BUNDLE, document) if bundle.references(raw) else raw
    under = [s for s in steps(schema) if "/then/" in s.pointer]
    assert len(under) == 4, [s.pointer for s in under]
    assert {s.keyword for s in under} == {"maximum"}
    rates = {}
    for forced in (False, True):
        examples = fired = 0
        for s in under:
            r = check_refuses(
                schema, lambda _instance: None, s, examples=20, force_path_to_site=forced
            )
            examples += r.examples
            fired += r.control_fired
        rates[forced] = (fired, examples)
    assert rates[True] == (0, 80), rates
    assert rates[False][1] == 80, rates
    assert 20 <= rates[False][0] <= 60, rates  # a substantial minority, both contexts


#: Every emitted class that carries a rule, with a payload that violates exactly
#: that rule and the JSON Schema keyword both halves must name.  The payloads are
#: written here and not drawn, because a rule is about key PRESENCE and no
#: generator draws from the document's complement.
RULE_VIOLATIONS = (
    ("core/format-id.json", {"agent_url": "https://a.example/", "id": "x", "width": 1},
     "dependencies"),
    ("core/budget-range.json", {"currency": "USD"}, "anyOf"),
    ("core/webhook-challenge-response.json", {"challenge": "A" * 40, "token": "A" * 40}, "not"),
)


def _root(document: str) -> Any:
    return next(g for g in graded() if g.ref == SchemaRef(document, "#")).model


def test_a_rule_narrows_the_constructor_and_both_halves_name_one_keyword() -> None:
    """D6 and D4 together, on the classes that carry a rule.

    A rule narrows ``model_validate``; the document decides acceptance through
    ``strict_validate``.  Both must refuse the same payload and both must report
    the DOCUMENT'S OWN keyword as the error ``type`` -- which is why
    ``_base._refuse`` and the after-validator raise through one function.  Two
    error shapes for one keyword is what that shares away.
    """
    for document, payload, keyword in RULE_VIOLATIONS:
        model = _root(document)
        for how in ("model_validate", "strict_validate"):
            with pytest.raises(ValidationError) as caught:
                getattr(model, how)(payload)
            assert [e["type"] for e in caught.value.errors()] == [keyword], (
                document,
                how,
                caught.value.errors(),
            )


def test_only_the_model_validate_path_observes_a_rule() -> None:
    """A rule is INVISIBLE to the three checks, measured by removing it.

    Every pair is offered its instance through ``strict_validate``, whose schema
    half validates against the document -- so the refusal is implied by the
    control whatever the rules say, and ``compare_schema`` reads
    ``model_json_schema()``, which a ``ClassVar`` does not reach.  With the
    after-validator returning before it evaluates anything, each payload above is
    ACCEPTED by the constructor and every rule-carrying pair still grades green.

    That is the whole justification for a rule being class data rather than a
    schema fragment, and it is the reason the tests above are the only instrument
    that can see one.

    **The short-circuit is the module-level ``refuse`` and NOT the validator
    method**, and that is measured rather than chosen: pydantic compiles a
    ``model_validator`` into the class's core schema at class creation, so
    assigning over ``RuleBound._enforce_adcp_rules`` renames something nothing
    calls -- probed, and ``model_validate`` still refused.  The compiled validator
    looks ``refuse`` up in ``_runtime``'s globals on every call, so patching that
    name disables exactly the rule half.  ``_base._refuse`` holds its own
    reference from an ``import ... from``, so the SCHEMA half keeps refusing,
    which is what lets the two be separated at all.
    """
    carriers = sorted({document for document, _payload, _keyword in RULE_VIOLATIONS})
    before = [check_pair(pair_of(g), max_steps=None) for g in graded()
              if g.ref.document in carriers and g.ref.pointer == "#"]
    assert len(before) == len(carriers) == 3
    assert all(r.outcome == "pass" for r in before), [(r.name, r.outcome) for r in before]

    runtime = sys.modules[RuleBound.__module__]
    original = runtime.refuse
    try:
        runtime.refuse = lambda _name, _errors: None
        accepted = 0
        for document, payload, keyword in RULE_VIOLATIONS:
            _root(document).model_validate(payload)  # the rule half is gone: it builds
            with pytest.raises(ValidationError) as caught:
                _root(document).strict_validate(payload)  # the schema half still refuses
            assert caught.value.errors()[0]["type"] == keyword, document
            accepted += 1
        assert accepted == 3
        after = [check_pair(pair_of(g), max_steps=None) for g in graded()
                 if g.ref.document in carriers and g.ref.pointer == "#"]
        assert [r.outcome for r in after] == [r.outcome for r in before]
    finally:
        runtime.refuse = original

    for document, payload, keyword in RULE_VIOLATIONS:
        with pytest.raises(ValidationError) as caught:
            _root(document).model_validate(payload)
        assert caught.value.errors()[0]["type"] == keyword, document


#: Every rule kind, with the population of nodes the LOWERING writes it from and
#: how many of those are a node ``lower_object`` can reach today (an object node
#: with ``properties``).  The second number is why three kinds have no emitted
#: carrier in this tree: a node inside an ``allOf`` conjunct is not a class here.
RULE_KIND_POPULATION = {
    "ForbiddenGroups": (398, 171, 167),
    "RequiredGroups": (297, 161, 70),
    "ConditionalRequired": (294, 128, 12),
    "PropertyCount": (61, 44, 29),
    "Dependencies": (60, 27, 58),
    "NegatedConditional": (42, 37, 0),
}


def test_every_rule_kind_is_written_from_a_real_bundle_node() -> None:
    """The lowering, graded over the bundle rather than over an invented fixture.

    Three of the six rule kinds have NO emitted carrier in this tree, and the
    reason is structural rather than an oversight: every document in the bundle
    that states a ``min``/``maxProperties`` or a conditional ALSO states an array
    property or an ``enum``, which are steps 6 and 3 -- measured document by
    document on all ten of them.  A ``NegatedConditional`` is written only at
    nodes inside an ``allOf`` conjunct, which is not a class here at all.

    So they are graded where they CAN be: the lowering against real nodes (here),
    and each dataclass against two plain arguments (below), which is exactly why
    ``Rule.errors`` takes ``keys`` and ``values`` and never a model.  That is a
    different situation from ``uniqueItems``, which has no rule kind at all
    because there is no array lowering to carry one -- a rule nothing writes is
    dead code, and a rule written from 294 real nodes with no class to sit on yet
    is a rule waiting for step 6.
    """
    everywhere: dict[str, int] = {}
    documents: dict[str, set[str]] = {}
    reachable: dict[str, int] = {}
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        for _pointer, node in bundle.nodes(doc):
            if not isinstance(node, dict):
                continue
            for source in rules.lower(node).rules:
                kind = source.split("(", 1)[0]
                everywhere[kind] = everywhere.get(kind, 0) + 1
                documents.setdefault(kind, set()).add(document)
                if "properties" in node:
                    reachable[kind] = reachable.get(kind, 0) + 1
    measured = {
        kind: (everywhere[kind], len(documents[kind]), reachable.get(kind, 0))
        for kind in everywhere
    }
    assert measured == RULE_KIND_POPULATION, measured
    assert len(measured) == 6, "a rule kind nothing writes is dead code"


def test_each_rule_kind_refuses_on_two_plain_arguments() -> None:
    """Each dataclass, graded without pydantic and without a document.

    ``Rule.errors(keys, values)`` is the whole protocol, which is what makes the
    three kinds with no emitted carrier gradeable at all.  Each row is the rule,
    the keys that arrived, and the JSON Schema keyword it must name -- or ``None``
    where the instance satisfies it, so each kind is exercised in both directions
    and a rule that refuses everything could not pass this.
    """
    from adcp.types._runtime import (
        ConditionalRequired,
        Dependencies,
        ForbiddenGroups,
        Match,
        NegatedConditional,
        PropertyCount,
        RequiredGroups,
    )

    cases = [
        (Dependencies("width", ("height",)), {"width"}, "dependencies"),
        (Dependencies("width", ("height",)), {"width", "height"}, None),
        (Dependencies("width", ("height",)), {"height"}, None),
        (PropertyCount(minimum=2), {"a"}, "minProperties"),
        (PropertyCount(minimum=2), {"a", "b"}, None),
        (PropertyCount(maximum=1), {"a", "b"}, "maxProperties"),
        (PropertyCount(maximum=1), {"a"}, None),
        (ForbiddenGroups((("a", "b"),)), {"a", "b"}, "not"),
        (ForbiddenGroups((("a", "b"),)), {"a"}, None),
        (RequiredGroups((("a",), ("b",)), "anyOf"), set(), "anyOf"),
        (RequiredGroups((("a",), ("b",)), "anyOf"), {"b"}, None),
        (RequiredGroups((("a",), ("b",)), "oneOf"), {"a", "b"}, "oneOf"),
        (RequiredGroups((("a",), ("b",)), "oneOf"), {"a"}, None),
        (RequiredGroups((("a",), ("b",)), "oneOf"), set(), "oneOf"),
        (ConditionalRequired((Match("u", True, ("p",)),), require=("x",)), {"u"}, "required"),
        (ConditionalRequired((Match("u", True, ("p",)),), require=("x",)), {"u", "x"}, None),
        (ConditionalRequired((Match("u", True, ("p",)),), forbid=("x",)), {"u", "x"}, "not"),
        (NegatedConditional((Match("u", True, ("p",)),), require=("x",)), {"u"}, None),
        (NegatedConditional((Match("u", True, ("p",)),), require=("x",)), set(), "required"),
    ]
    seen: set[str] = set()
    for rule, keys, keyword in cases:
        values = {k: "p" for k in keys}
        got = [e[0] for e in rule.errors(frozenset(keys), values)]
        assert got == ([keyword] if keyword else []), (rule, keys, got)
        seen.add(type(rule).__name__)
    assert seen == set(RULE_KIND_POPULATION), seen


def test_a_conditional_that_narrows_a_value_is_the_schemas_and_not_a_rules() -> None:
    """The ceiling D6 accepts, measured rather than written in a docstring.

    A rule is expressible only as a statement about key PRESENCE.
    ``core/canvas-constraint.json``'s ``if unit == "percent" then x.maximum = 100``
    is a statement about a VALUE, so it gets no rule: the constructor builds the
    violating payload and the schema half refuses the same payload on ``maximum``.

    Refusing the document for it instead would cost the whole ``if`` population --
    186 documents state one -- for a constraint the accepted set already enforces.
    """
    document = "core/canvas-constraint.json"
    schema = bundle.read(BUNDLE, document)
    violating = {
        "constraint": "safe_area",
        "region": {"x": 101, "y": 0, "width": 1, "height": 1, "unit": "percent"},
    }
    assert conforms(schema, violating) is False
    assert violated_keywords(schema, violating) == ["maximum"]
    # The root's own rules are the dependency and nothing else: the conditional
    # sits at /properties/region/allOf/0 and says `x.maximum = 100`, which is a
    # statement about a VALUE and so reduces to no rule at all.
    assert rules.lower(schema).rules == [
        "Dependencies('breakpoint_id', ('state_id',))"
    ], rules.lower(schema).rules
    region = schema["properties"]["region"]
    assert isinstance(region["allOf"][0]["if"], dict)
    assert rules.lower(region).rules == [], rules.lower(region).rules
    # and the document is not emitted at all, so the pair above is a harness
    # control rather than a class: it refuses on `enum`, which is step 3's row.
    assert document in emit.emit(BUNDLE, [document]).refusals


def test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded() -> None:
    """A bad probe, recorded as one.

    ``uniqueItems`` is 479 stepped sites over 198 documents and **0 of them is on
    an emitted pair**: every host is an array node, which is step 6's row, or sits
    behind an ``allOf``.  So breaking the step's duplicate forcing reddens its own
    exclusivity assertion and leaves every binding grade green -- which is a
    finding about the instrument's REACH and not a pass, and the reason there is
    no ``UniqueItems`` rule kind to write.

    Asserted both ways so the claim cannot go stale silently: the keyword is
    stepped, and no document the tree emits carries it.
    """
    census = _step_census()
    assert census["uniqueItems"] == (479, 198)
    carried = [
        f"{document}{pointer or '/'}"
        for document in sorted({g.ref.document for g in graded()})
        for pointer, node in bundle.nodes(schema_at(SchemaRef(document, "#")))
        if isinstance(node, dict) and "uniqueItems" in node
    ]
    assert carried == [], carried
    assert "uniqueItems" in rules.KEYWORDS, "the keyword must not block an object lowering"
    assert not any("UniqueItems" in source for source in RULE_KIND_POPULATION)
