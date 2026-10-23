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
"grading someone else's tree" failure has no site.  The last site was a STALE
module -- one an earlier run wrote and no current document produces -- which is
indistinguishable from a real emission to everything that reads the tree, and
``emit.write`` now DELETES one on a whole-population run
(``test_write_removes_a_file_the_run_no_longer_intends``).  It is still checked
where P10 puts a check as well: ``test_the_committed_tree_is_what_a_fresh_run_emits``
compares the whole tree with a fresh emission of the derived population, so a file
no run produces is a failure at the gate even if it got there some other way.

The bundle directory is a constant here and nowhere inside ``codegen/``: step 10
derives it from ``adcp.get_adcp_spec_version()`` (D9, P9).
"""

from __future__ import annotations

import ast
import functools
import importlib
import inspect
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
from datamodel_code_generator.types import DataType
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
from codegen import refusal as refusal_module
from codegen.lower import const as lower_const
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
    _closed,  # noqa: PLC2701 -- the harness's own reading of a closed additionalProperties
    _composed,  # noqa: PLC2701 -- and its own folding of an allOf conjunct's facts
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
    """The pair, and the document ROOT beside the node.

    ``schema`` is the node the class names and is what the pair is graded against.
    ``document`` is the scope a LOCAL ``$ref`` on the document side is relative to,
    which a nested pair's node does not contain -- ``core/bidding-policy-capability.json``'s
    ``#/definitions/scope_capability`` references ``#/definitions/policy_profile``,
    a sibling in the root's own ``definitions`` section.  Read through the same
    ``schema_at`` as the node, so one function answers "what does this document
    say" for both.
    """
    return Pair(
        name=f"{g.ref.document}{g.ref.pointer}",
        schema=schema_at(g.ref),
        model=g.model,
        accept=g.accept,
        document=schema_at(SchemaRef(g.ref.document, "#")),
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
    # 301 and not 287: ``composes_at_the_root`` reads "a union beside the allOf"
    # through ``union_root`` now, so a root carrying ``allOf`` beside a
    # PRESENCE-ONLY ``anyOf`` is step 4's rather than nobody's -- 14 documents that
    # both this row and step 5's used to refuse.
    assert len(composing()) == 301
    # Not the sum: the selectors OVERLAP, and the overlaps are counted below
    # rather than assumed.  The union is the denominator; no selector here is a
    # ROW for another's shape, so nothing is counted twice by the table.
    assert len(population()) == 991
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
    # every CROSS-DOCUMENT reference of every emitted document resolves to a document
    # also emitted.  A LOCAL reference names a node of the document being written and
    # so has no target to emit -- ``compiler.local_reference`` resolves it against the
    # module's own declarations -- and the document half is how ``bundle.split_ref``
    # tells the two apart, which is the same one reading the walk and the binder use.
    # Asserted non-empty, so the skip is a population and not a silent hole: this loop
    # read a local reference as a document and failed on it the first time one reached
    # an EMITTED document (``core/reporting-coverage.json#/definitions/...``).
    known = set(bundle.portable(BUNDLE))
    local_seen = 0
    for document in out.emitted:
        doc = bundle.read(BUNDLE, document)
        nodes = dict(bundle.nodes(doc))
        for _, uri in bundle.references(doc):
            named, pointer = bundle.split_ref(uri)
            if not named:
                # A LOCAL reference names a node in the REFERRING document, which is
                # emitted by construction -- it is the document being walked. So the
                # closure claim does not apply to it; what does is that the pointer
                # lands, because a local reference to a node the document does not
                # hold is an ImportError in the same way a missing module is.
                #
                # This branch was unreachable until `salesagent-j3k2l.20`: a document
                # carrying a `definitions` section was REFUSED, so the loop never
                # walked its references, and `document_for` returning None for a
                # local reference could not be observed here.
                assert pointer in nodes, (document, uri)
                local_seen += 1
                continue
            target = bundle.document_for(uri, known)
            assert target in out.emitted, (document, uri)
    assert local_seen, "no local reference was reached; the local branch graded nothing"


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
    # ``refuses_examples=25`` EXPLICITLY, because this test asserts the DENOMINATOR
    # (3 sites x 25 = 75) and not just the pass mark.  check_pair defaults to 1 per
    # site since salesagent-j3k2l.27, so a test that cares about depth states it.
    rep = check_pair(pair_of(pagination()), max_steps=None, refuses_examples=25)
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
        Pair(name="wide", schema=schema, model=Wide, accept=Wide.strict_validate),
        max_steps=None,
        refuses_examples=25,
    )
    # Both at the same explicit depth: the point of this test is that the two
    # denominators are IDENTICAL, so neither may depend on check_pair's default.
    faithful = check_pair(pair_of(pagination()), max_steps=None, refuses_examples=25)

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
    graded_reports = [(g, check_pair(pair_of(g), max_steps=None)) for g in graded()]
    # Selected on the OUTCOME and no longer on "not pass", because the population has
    # a second non-pass exit now: ``no_instrument``, for a pair whose accepts or
    # refuses check could not DRAW. The assertion under the list is what keeps this a
    # selection rather than a hole -- it says those two are the only exits there are,
    # so a third could not hide behind this one.
    excused = [g for g, r in graded_reports if r.outcome == "no_constraint_to_step"]
    assert [f"{g.ref.document}{g.ref.pointer}" for g in excused] == [
        "core/context.json#",
        # Added by D5's alias module: `core/creative-brief.json` was refused on a
        # constrained scalar inside a container, and this nested class of it
        # states no keyword `steps()` can step.
        "core/creative-brief.json#/properties/messaging",
        # Added by this step: `core/creative-policy.json` was refused on a
        # `uniqueItems`, and this nested class of it states no keyword `steps()`
        # can step.
        "core/creative-policy.json#/properties/provenance_requirements",
        "core/ext.json#",
        "core/media-buy-legacy-terms-ref.json#",
        # Added by D2's const row (salesagent-j3k2l.16): each of these states a
        # `const` and nothing else `steps()` can step.
        "creative/preview-render.json#/oneOf/0/properties/embedding",
        "creative/preview-render.json#/oneOf/1/properties/embedding",
        "creative/preview-render.json#/oneOf/2/properties/embedding",
        "error-details/account-setup-required.json#",
        "error-details/audience-too-small.json#",
        "error-details/budget-too-low.json#",
        "error-details/conflict.json#",
        "error-details/creative-rejected.json#",
        "error-details/stale-response.json#/properties/upstream",
        "error-details/stale-response.json#/properties/original_error",
        "sponsored-intelligence/si-identity.json#/properties/privacy_policy_acknowledged",
        "sponsored-intelligence/si-identity.json#/properties/user/properties/shipping_address",
        "sponsored-intelligence/si-identity.json#/properties/user",
    ]
    # The two exits are the only two, so the list above is exhaustive over the
    # non-pass population rather than one slice of it.
    assert {r.outcome for _, r in graded_reports} == {
        "pass",
        "no_constraint_to_step",
        "no_instrument",
    }, {r.outcome for _, r in graded_reports}
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


def _grades_a_cause(cause: str, where: str = "") -> None:
    """A ``no_instrument`` cause has to be specific enough to ACT on.

    Graded by SHAPE and not by a sentence: the first cut asserted the substring
    ``"contradicted by"``, the gate fix reworded that half to ``"contradicts the
    step"``, and all four undrawable pairs then reddened on the wording while the
    pairs themselves were exactly as intended.  A test that pins prose grades the
    prose.

    Three obligations, each read off the structure:

    * WHICH check could not draw -- the entry names ``accepts`` or ``refuses``;
    * WHERE -- an accepts cause names the document's own format-beside-pattern
      positions (there is no single node for hypothesis to blame, so the positions
      are derived from the document), and a refuses cause names the pointer its step
      sits at;
    * WHY -- hypothesis's own exception name, which carries the filtered-draw count.
    """
    assert cause.startswith(("accepts: ", "refuses ")), (where, cause)
    assert "Unsatisfiable" in cause or "RecursionError" in cause, (where, cause)
    if cause.startswith("accepts: "):
        assert ": format " in cause, (where, cause)
    else:
        assert " at /" in cause, (where, cause)


@pytest.mark.parametrize("row", graded(), ids=lambda g: f"{g.ref.document}{g.ref.pointer}")
def test_every_class_passes_all_three_checks(row: Graded) -> None:
    """N: emitted AND graded green against the schema the class itself names.

    Two verdicts other than ``pass`` are allowed through, and each is asserted
    against its own evidence rather than taken on trust:

    * ``no_constraint_to_step``, where the document genuinely states no keyword
      ``steps()`` can step -- asserted against ``steps()`` itself;
    * ``no_instrument``, where a check could not DRAW an instance, so the
      obstruction is ``hypothesis`` and not the model -- asserted by requiring each
      cause to name a shape (a format beside a pattern, or the keyword that
      contradicts a witness) and not merely to exist.

    **The schema comparison is asserted for EVERY pair, including an undrawable
    one**, and that is what keeps the second exit from being a hole: the comparison
    needs no generator, it runs on both of them, and it is the only check that
    separates a faithful model from a wide one.
    """
    pair = pair_of(row)
    rep = check_pair(pair, max_steps=None)
    assert rep.missing_formats == []
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.differs)
    if rep.accepts.outcome != "strategy_error":
        assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    bad = [
        (r.keyword, r.pointer, r.outcome, r.counterexample, r.harness)
        for r in rep.refuses
        if not r.undrawable
    ]
    assert [b for b in bad if b[2] not in ("pass", "no_evidence")] == []
    if rep.outcome == "no_instrument":
        assert rep.no_instrument, rep.name
        for cause in rep.no_instrument:
            _grades_a_cause(cause)
    elif rep.outcome != "pass":
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
    """D5's URL-type rows, broken on purpose at every gate they have.

    The category admits THREE facts and nothing else, each in its own row and each
    gated, and it counts them in a field of its own
    (``ComparisonResult.url_typed``) rather than in ``missing`` or in ``added`` --
    because it is the one admission here that excuses a fact the model does not
    state at all, and folding it into the implied-fact rows would make a genuine
    omission look like a derivation.

    Ten cells. The first two are what the rows are for on the ``AdCPUrl`` arm; 3-5
    are the perturbations that must still redden, and each of them passed before the
    gates were written as they are; 6 says the counting is separate; and 7-10 are
    the ``HttpUrl`` arm D5's amendment added, including the one that keeps the
    second row from becoming "any bound on a URL type is admitted".
    """
    from pydantic import AnyUrl, HttpUrl, UrlConstraints

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

    # 5. BROKEN ON PURPOSE -- ``_url_typed``'s signature requires ``minLength: 1``
    #    exactly, so a model stating a DIFFERENT ``minLength`` at a ``uri`` node is
    #    not a URL type and none of the three rows reaches it.  That is the gate
    #    that keeps the category off an ordinary annotated ``str`` carrying a bound.
    floored = compare_schema(
        bare, Annotated[str, Field(min_length=2, json_schema_extra={"format": "uri"})]
    )
    assert floored.outcome == "model_adds_a_fact", floored.url_typed
    assert floored.url_typed == []
    assert any("/minLength" in a for a in floored.added), floored.added

    # 6. and a document that states the ``minLength`` ITSELF is compared, not
    #    excused: the row is about a fact the document does not state.
    stated = compare_schema({**bare, "minLength": 1}, AdCPUrl)
    assert stated.outcome == "pass"
    assert stated.url_typed == [], stated.url_typed
    assert stated.compared == one.compared + 1

    # ---- the HttpUrl arm, which D5's amendment selects at every uri position whose
    # ---- document does not restrict the scheme to https ----------------------
    assert TypeAdapter(HttpUrl).json_schema() == {
        "type": "string",
        "format": "uri",
        "minLength": 1,
        "maxLength": 2083,
    }, "the two facts the second row exists for"

    # 7. BOTH added facts are admitted, each by its own row, and `added` stays empty.
    http = compare_schema(bare, HttpUrl)
    assert http.outcome == "pass", (http.added, http.missing, http.differs)
    assert sorted(line.split(": ")[0] for line in http.url_typed) == [
        "/maxLength",
        "/minLength",
    ], http.url_typed
    assert any("HttpUrl renders" in line for line in http.url_typed)
    assert http.added == [] and http.missing == []

    # 8. BROKEN ON PURPOSE -- the second row is NOT "a bound on a URL type is
    #    admitted".  A URL type carrying any OTHER maxLength is a fact the model
    #    adds, and this is the cell that would pass under a widened row.
    other = compare_schema(bare, Annotated[AnyUrl, UrlConstraints(max_length=1024)])
    assert other.outcome == "model_adds_a_fact", other.url_typed
    assert any("/maxLength" in a for a in other.added), other.added

    # 9. BROKEN ON PURPOSE -- a document that states the maxLength ITSELF is
    #    compared, and a document stating a DIFFERENT one differs rather than being
    #    excused.  That second case is what `emit.decide_type` refuses by name: the
    #    bundle has 4 such positions, all `maxLength: 2048`.
    agrees = compare_schema({**bare, "maxLength": 2083}, HttpUrl)
    assert agrees.outcome == "pass"
    assert [line for line in agrees.url_typed if "/maxLength" in line] == []
    disagrees = compare_schema({**bare, "maxLength": 2048}, HttpUrl)
    assert disagrees.outcome == "model_drops_a_fact"
    assert any("/maxLength" in d for d in disagrees.differs), disagrees.differs

    # 10. and the pattern row serves this branch too, which is what lets a document
    #     with a non-https pattern take HttpUrl at all.
    host_only = compare_schema({**bare, "pattern": "^https://[^/?#@]+$"}, HttpUrl)
    assert host_only.outcome == "pass", (host_only.missing, host_only.added)
    assert len(host_only.url_typed) == 3, host_only.url_typed


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
    (334 sites: ``date-time`` 190, ``uri`` 131, ``date`` 5, ``email`` 5, ``hostname`` 3),
    because that is the denominator the rule is stated over.  Re-measured at
    64131600f (``salesagent-j3k2l.29``): every count here is over the documents
    ``graded()`` names, so each one moved as the emitted population grew, and
    ``hostname`` is a format the census did not use to see at all -- it has no
    ``FORMAT_TYPES`` row, so its 3 sites ride the second arm below.
    """
    checked = emit.asserted_formats(bundle.read(BUNDLE, PAGINATION))
    # The two dependencies `pyproject` names are what put these in the draft's
    # own checker; without them the gate below selects no type at all.
    assert {"date-time", "uri"} <= checked, sorted(checked)
    assert set(emit.FORMAT_TYPES) <= checked, sorted(set(emit.FORMAT_TYPES) - checked)

    seen: dict[str, int] = {}
    #: format -> the type names it actually selected over this population.  More
    #: than one means the DOCUMENT chose, which is D5's `uri` row.
    arms: dict[str, set[str]] = {}
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
            # **A MULTI-TYPE node carries a format too, and this used to RAISE on
            # one.**  ``node["type"] in emit.SCALAR`` hashes the value, and a list is
            # unhashable, so the site died with a ``TypeError`` rather than failing an
            # assertion -- latent until a document declaring ``["string", "null"]``
            # beside a ``format`` emitted (``salesagent-j3k2l.21``).  D5's rule is
            # per-ARM: ``lower.containers.multi_type`` cuts the node to one type at a
            # time carrying only what that type can hold (``ARM["string"]`` holds
            # ``format``), so the format selects the type of the arm that defines it
            # and the ``null`` arm takes none of it.  Asserted over the arms, which is
            # what the emitter actually reads.
            kinds = node["type"] if isinstance(node["type"], list) else [node["type"]]
            assert [k for k in kinds if k != "null"], (document, pointer, kinds)
            assert all(k in emit.SCALAR or k == "null" for k in kinds), (
                document,
                pointer,
                kinds,
            )
            # The chooser is asked with THIS NODE, because D5 makes a `uri` field's
            # type a function of the document's own `pattern` -- so a test that read
            # one path per format would grade only whichever arm it happened to
            # name, and would have passed unchanged while the other arm went
            # unimported.
            choose = emit.FORMAT_TYPES.get(fmt) if fmt in checked else None
            if choose is None:
                assert fmt in annotated_formats, (document, pointer, fmt)
            else:
                selected = choose(node)
                module, name = selected.rsplit(".", 1)
                assert (module, name) in imported, (document, pointer, selected)
                assert fmt not in annotated_formats, (document, pointer, fmt)
                arms.setdefault(fmt, set()).add(name)

    assert seen == {"date-time": 190, "uri": 131, "date": 5, "email": 5, "hostname": 3}, seen
    # **BOTH arms of D5's `uri` row are reached by this population**, so neither is
    # graded by an empty loop: of the 131 `uri` sites, 15 state a `^https://` pattern
    # and take `AdCPUrl` (across 12 documents, `core/platform-extension-ref.json`
    # among them) and the other 116 take `HttpUrl`.  A format whose type is a
    # function of the format alone selects exactly one.
    assert arms == {
        "date-time": {"AwareDatetime"},
        "date": {"date"},
        "uri": {"AdCPUrl", "HttpUrl"},
    }, arms

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
            mine = _rendered(emitted, key, g.model)
            assert mine.get("format") == sub["format"], (g.ref, key, mine)
            stated += 1
    assert stated == 326, stated


def _model_schema(model: Any) -> dict:
    """One model's own JSON schema, whichever kind of model it is.

    The same predicate ``harness.compare_schema`` uses, and it has to be the same
    one: ``isinstance(model, type)`` alone is not it, because D2's enumeration row
    emits a CLASS that is not a pydantic model and has no ``model_json_schema``.
    """
    if isinstance(model, type) and hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return TypeAdapter(model).json_schema()


def _rendered(emitted: dict, key: str, model: Any) -> dict:
    """One DOCUMENT KEY's node in a model's rendered schema, unwrapped.

    **The key is the document's own, because that is the only key the rendered
    schema has.**  ``model_json_schema()`` is ``by_alias``, and a property whose
    Python name cannot be the document's key is carried under an ALIAS that IS
    the document's key (``compiler.field_name``'s own contract: "a key is carried
    as-is or it is carried under an ALIAS, never dropped").  Indexing by
    ``compiler.field_name(key)`` -- the PYTHON name -- is what both callers used
    to do, and it raised ``KeyError`` the moment an aliased property entered the
    graded population: ``trusted-match/identity-match-request.json#``'s
    ``$schema`` is ``schema_`` in Python and ``$schema`` on the wire, and it
    states ``format: uri`` so the format census reaches it.

    Measured over all 1,034 pairs at 64131600f: 6 properties are aliased, and for
    every one of them the rendered schema carries the DOCUMENT's key and not the
    Python name.  So the alias relationship is asserted here rather than assumed
    -- a model that rendered the Python name would be carrying a key its document
    does not state, which is the defect this spelling would otherwise hide.
    """
    python_name = compiler.field_name(key)
    if python_name != key:
        field = getattr(model, "model_fields", {}).get(python_name)
        assert field is not None, (key, python_name, "no field under the Python name")
        assert field.alias == key, (key, python_name, field.alias)
        assert python_name not in emitted["properties"], (key, python_name)
    return _unwrap(emitted["properties"][key], emitted.get("$defs", {}))


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
    ``python-re`` and the other 72 of 76 would take the default.  The premise
    was that the accepted sets agree for those 72, and this test is the
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
    assert (len(distinct), sum(distinct.values())) == (76, 397), distinct

    no_build: dict[str, int] = {}
    diverges: dict[str, int] = {}
    agrees: dict[str, int] = {}
    #: pattern -> whether the witness match CONSUMED the trailing newline, which is
    #: the mechanism and is what separates the two buckets (asserted below).
    consumed: dict[str, bool] = {}
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
            found = re.search(pattern, value)
            if found is None:
                continue  # the document refuses it too; nothing to diverge about
            # the document admits it, so the engine the document is compiled with
            # must admit it, and that is the one this package uses
            assert _accepts(pattern, REGEX_ENGINE, value), (pattern, value)
            consumed[pattern] = found.end() == len(value)
            if not _accepts(pattern, None, value):
                where = diverges
        where[pattern] = sites

    # Re-measured at 64131600f (``salesagent-j3k2l.29``): the census is over the
    # documents ``graded()`` names, so all four counts moved with the emitted
    # population.  The SHAPE of the finding did not move at all -- see below.
    assert (len(no_build), sum(no_build.values())) == (4, 17), no_build
    assert (len(diverges), sum(diverges.values())) == (65, 353), diverges
    assert (len(agrees), sum(agrees.values())) == (7, 27), agrees
    # **Every pattern that diverges carries a `$`, and the 7 that agree do not
    # contradict that.**  The previous revision said "the one that agrees is the one
    # with no `$` to disagree about", which was a true statement about a population
    # of one and is false now: 2 of the 7 DO carry a `$`.  Measured, the mechanism
    # is sharper than the keyword, so it is asserted instead of the keyword -- a
    # `$`-anchored pattern diverges only where Python's `$` had to match BEFORE the
    # trailing newline, which is to say where the match did not consume it.  Both
    # of the two agreeing `$` patterns end in a character class that admits `\n`
    # (`[^/?#@]+$`, and `(?:\?[^#]*)?$`), so the newline is INSIDE the match, `$`
    # sits at the end of the haystack, and Rust matches there too.
    # Every buildable pattern drew a value the document admits, so no row of either
    # bucket is graded by a witness that never existed.
    assert set(consumed) == set(diverges) | set(agrees), (
        sorted(set(diverges) | set(agrees) - set(consumed))
    )
    assert all("$" in p for p in diverges), diverges
    assert not any(consumed[p] for p in diverges), {p: consumed[p] for p in diverges}
    # Within `agrees`, "carries a `$`" and "the match consumed the newline" are the
    # SAME set of 2 -- which is the mechanism, not a coincidence of this tree.
    assert sorted(p for p in agrees if "$" in p) == sorted(p for p in agrees if consumed[p]), (
        sorted(agrees),
        {p: consumed[p] for p in agrees},
    )
    assert len([p for p in agrees if "$" in p]) == 2, sorted(agrees)


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
    # Re-measured at 64131600f (``salesagent-j3k2l.29``): 9 of the 17 aliases the tree
    # carries state a pattern.  A count over ``graded()``, so it moves with the tree.
    assert with_pattern == 9, with_pattern


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
    # **THIS ASSERTION IS RED, IT IS RED ON TRUNK TOO, AND salesagent-j3k2l.18 DID NOT
    # CLEAR IT.**  Stated here rather than left to be rediscovered:
    #
    # * the pair count is **811** on this tree and **808** at trunk ``29c553504``,
    #   measured twice as ``len(graded())``, which needs no grading run.  The 503 this
    #   line asserted is 305 out ON TRUNK, before any part of this lane existed, so it
    #   is not this branch's doing.  The +3 IS this lane's: `core/attribution-window.json`
    #   contributes its root plus its two ``allOf`` property nodes.
    # * the ``pass`` and ``no_constraint_to_step`` figures below are **NOT measured**.
    #   Getting them means grading all 811 pairs at ``max_steps=None``, which ran for
    #   over 50 minutes here without finishing.  491 and 12 are trunk's own numbers and
    #   are left exactly as trunk has them: a guessed pass count would be a number
    #   nobody measured, which is worse than a red line that says so.
    #
    # So the pair count is corrected to what was measured and the other two are
    # deliberately untouched.  Clearing this test needs the full pair grading and is
    # not this row's work.
    assert len(reports) == 811, len(reports)
    assert sum(1 for r in reports if r.outcome == "pass") == 758
    assert sum(1 for r in reports if r.outcome == "no_constraint_to_step") == 25
    assert sum(1 for r in reports if r.outcome == "no_instrument") == 9
    assert sum(1 for r in reports if r.outcome == "refuses:harness_error") == 3
    assert sum(1 for r in reports if r.outcome == "comparison:model_drops_a_fact") == 16
    # THE ONE FIGURE HERE THAT IS A FLOOR, and the only one that is not
    # reproducible. The refuses-check instance total counts hypothesis DRAWS
    # rather than schema facts, and seven careful readings of it, on trees whose
    # source I could not distinguish, gave 31,923 / 32,031 / 32,037 / 32,045 /
    # 32,045 / 32,059 / 34,935 -- the last on the named-type tree, which moved the
    # population legitimately. Ruled out against hash seed (four runs, three
    # seeds, identical over a fixed subset), enumeration order (sorted, reversed,
    # shuffled, identical), untracked emitted files (tracked == on disk), and
    # worker count. The five other figures here reproduced EXACTLY between two
    # independent instruments, which is why they are equalities and this is not.
    #
    # A floor still carries the denominator: it says the refuses check reached a
    # class at least this many times, so a collapse or a large regression still
    # reddens. An equality would assert a reproducibility the instrument does not
    # have, and a test that fails when nothing changed teaches the next reader to
    # edit the number instead of reading it.
    # Re-measured on the merged tree rather than carried over or minimised: this run
    # reads 49,766, and the floor sits ~0.7% under it -- about twice the 0.4% spread
    # the seven readings above show -- so a collapse reddens and a reread does not.
    # Re-measured at TWO TESTS PER CLASS (salesagent-j3k2l.27): ``refuses_examples``
    # defaults to 1 per step site instead of 25, so this is 9,047 on this tree against
    # a floor ~1.6% under it.  The 49,400 this line asserted was measured on a 503-pair
    # tree at 25 examples per site and was never true here.
    assert sum(r.graded_instances for r in reports) >= 8900  # refuses-check instances
    assert sum(r.comparison.compared for r in reports) == 25858  # document facts compared
    assert sum(r.comparison.model_facts for r in reports) == 9440  # model-only facts examined
    assert sum(len(r.comparison.added) for r in reports) == 0  # none of them narrows
    # **THE TWO ASSERTIONS BELOW ARE RED, DELIBERATELY, AND salesagent-j3k2l.28 OWNS
    # THEM.**  Every count above is now measured and green, so this test fails HERE and
    # the failure names the comparison rather than burying it behind a stale pin.
    #
    # Measured over all 811 pairs: ``missing`` is 10 and ``differs`` is 13, in 16 pairs.
    # NEITHER IS A SAFETY DEFECT, and ``added == 0`` above is the proof -- the model
    # narrows nothing anywhere in the population, which is the half that could admit an
    # instance the document rejects.  The 10 missing facts are 5 x ``required: []`` and
    # 5 x ``enum: [false, true]`` on a boolean, which constrain nothing; the 13 differs
    # are all ``/properties/context/description``, where the emitter takes the ``$ref``
    # target's description instead of the referring document's.
    #
    # Attribution was MEASURED, not assumed: pre-``.21`` trunk ``2b605b164`` graded 734
    # pairs with 1 discrepancy, and post-``.21`` grades 808 with 23.  So ``.21`` made 74
    # more documents emittable and they exercise a defect that was already there.
    #
    # THE FIX IS NOT TO RE-POINT THESE TO 10 AND 13.  Zero is the specification's
    # symmetric comparison: a fact the model adds reddens and a fact it drops reddens.
    # ``.28`` folds the two no-op shapes by shape (an ``enum: [false]`` on a boolean is
    # NOT a no-op and must still compare) and resolves the description divergence in the
    # emitter.
    assert sum(len(r.comparison.missing) for r in reports) == 0  # and none drops one
    assert sum(len(r.comparison.differs) for r in reports) == 0
    # D5's URL-type rows, the one category that excuses a fact the model does not
    # state, and 74 is the sum of its three: 37 `minLength: 1` (every URL type
    # renders it), 36 `maxLength: 2083` (`HttpUrl` renders it, and 36 of the 37
    # positions take that arm), and the ONE `pattern` the bundle states on a
    # `format: uri` node -- `core/platform-extension-ref.json`, which is also the
    # one position on the `AdCPUrl` arm and so the one with no `maxLength`.
    # A position inside a nested class is graded twice, at its own pair and at its
    # parent's, so it is larger than the annotation sites the tree has.
    assert sum(len(r.comparison.url_typed) for r in reports) == 76


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
        # **What the DOCUMENT APPLIES at this node, not what the node says alone.**
        # ``allOf`` conjoins, so a conjunct's ``additionalProperties`` IS the node's --
        # and ``_composed`` is the harness's own folding, the one ``compare_schema``
        # reads the document through, so there is no second reading of what a conjunct
        # contributes.  ``_closed`` folds the resolver's ``{"not": {}}`` back to
        # ``false``.  Read bare instead, a composing node comes back SILENT while its
        # class correctly carries the conjunct's value: measured on
        # ``core/attribution-window.json#/properties/post_click``, whose own node is
        # ``{"allOf": [{"$ref": "core/duration.json"}], "description": ...}`` and whose
        # one conjunct declares ``additionalProperties: false``.  The class is
        # ``forbid`` and the folded document says ``false``, which agree; the bare node
        # said nothing and this read it as the document permitting what it forbids.
        declared = _closed(_composed(schema_at(row.ref)).get("additionalProperties", "silent"))
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
            # ``true``) when this was first written, and ``allow`` is the only value this branch admits -- a
            # ``forbid`` inherited where the document is silent would be a
            # narrowing and still fails.  27 such classes at 64131600f, not 1:
            # the figure is over ``graded()`` and step 4's row brought the whole
            # ``core/async-response-refs/`` family into it.
            assert row.model.model_config["extra"] == "allow", (row.ref, declared)
            base = row.model.__mro__[1]
            assert schema_at(base.__adcp_schema__)["additionalProperties"] is True, row.ref
            counted["allow"] += 1
            continue
        assert row.model.model_config["extra"] == want, (row.ref, declared)
        counted["silent" if declared == "silent" else want] += 1
    assert counted["forbid"] and counted["allow"], counted
    # The silent set is the leaf objects whose documents say nothing plus the
    # union BASES, which are silent by construction: ``lower/union.py`` refuses a
    # root that states its own ``additionalProperties``, so a base never has one to
    # carry and takes this default.  The other members are mapping and container
    # roots whose own document is silent too.  Re-measured at 64131600f
    # (``salesagent-j3k2l.29``): 64, and the partition over the same 803 classes is
    # forbid 344 / allow 395 / silent 64 -- a count over ``graded()``, so all three
    # moved with the emitted population.
    assert counted["silent"] == 64, counted


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
    # ``__all__[0]`` AND NOT A ONE-ELEMENT UNPACK.  ``salesagent-j3k2l.31`` made a
    # module export more than its root -- the root, plus every pointer the bundle
    # names, plus the field types a composing subclass re-uses -- so 24 of the 677
    # modules now list several names and the unpack this line used to do raised
    # ``ValueError`` at all 12 call sites: ``core/catalog.json`` lists 6 names and
    # ``aao/agent-publishers.json`` lists 2.
    #
    # THE ROOT IS FIRST BY A FACT THAT IS ITSELF GRADED, which is what makes position
    # 0 safe rather than an assumption: ``tests/test_enum.py`` asserts
    # ``listed[:1] == [root]`` for every emitted module, with the expected root derived
    # from ``compiler.class_name`` over the document's own title.  So this reads index 0
    # instead of filtering by name or re-deriving the title, and if that order ever
    # changes the assertion over there fails before anything here does.
    return importlib.import_module(emit.emit(BUNDLE, [document]).emitted[document]).__all__[0]


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
    fragment_refs: list[tuple[str, str, str]] = []
    for document in documents:
        doc = bundle.read(BUNDLE, document)
        # CROSS-document only, which is what P2 is about here: a LOCAL reference
        # names a node of this same document, so it resolves to a symbol the module
        # DECLARES rather than to an import, and ``document_for`` answers ``None``
        # for it by design (``bundle.split_ref``).  Re-measured over the graded
        # documents at 64131600f: 573 property references are cross-document -- 567
        # name a whole document and are graded here, and 6 name a FRAGMENT of another
        # document and are handed on (the branch below says why) -- and the local ones
        # are excluded by this selection, reachable at all since
        # salesagent-j3k2l.20.  The local half is graded by
        # ``tests/test_fragment_ref.py``, which is .20's own instrument; selecting on
        # it here would make this test assert an import for a node that has none.
        refd = {
            key: sub["$ref"]
            for key, sub in doc.get("properties", {}).items()
            if isinstance(sub, dict) and "$ref" in sub and bundle.split_ref(sub["$ref"])[0]
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
            resolved = bundle.document_for(uri, known)
            if resolved is None:
                # **A cross-document reference to a FRAGMENT, which is a third case
                # this census did not have.**  ``split_ref`` says there is a document
                # part so the selection above admits it, and ``document_for`` answers
                # ``None`` because the uri names a node INSIDE that document rather
                # than the document.  Reachable since ``salesagent-j3k2l.20``, and
                # ``tests/test_fragment_ref.py`` is .20's own instrument for it, so
                # the import obligation for one belongs there and not here -- the
                # previous spelling passed ``None`` to ``_symbol`` and died with
                # ``FileNotFoundError: .../schemas/cache/3.2/None``.
                #
                # Counted and CHECKED rather than skipped: each unresolved target
                # must be unresolved BECAUSE it names a fragment, so a reference whose
                # target is simply absent from the bundle still reddens here.
                assert "#/" in uri, (document, key, uri)
                fragment_refs.append((document, key, uri))
                continue
            target = str(resolved)
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
    # Both denominators, so neither the graded half nor the handed-off half can go
    # quiet.  Re-measured at 64131600f (``salesagent-j3k2l.29``): 567 cross-document
    # property references graded here, and 6 fragment references handed to
    # ``tests/test_fragment_ref.py``.
    assert graded_properties == 567, graded_properties
    assert len(fragment_refs) == 6, fragment_refs


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

    **The tree now exercises both combinators, so the loop below reads each document's
    own.**  It was 6 of 6 ``oneOf``, which is why the loop hard-coded ``"oneOf"`` and
    the ``anyOf`` branch was graded only on the fixture at the end --
    ``salesagent-j3k2l.19`` emits ``core/canonical-account-ref.json``, whose root
    combinator is ``anyOf``, and the hard-coded expectation reddened on it. Asserting
    the DOCUMENT'S keyword instead is what the test claims in the first place: a
    refusal names the document's own vocabulary. The fixture stays, because it is now
    a second grader of the ``anyOf`` branch rather than the only one, and it is also
    what grades ``_ROOT_REQUIRED``.
    """
    assert emitted_unions()
    assert {lower_union.keyword(bundle.read(BUNDLE, d)) for d in emitted_unions()} == {"anyOf", "oneOf"}
    for document in emitted_unions():
        base = getattr(importlib.import_module(_module_of(document)), _symbol(document))
        with pytest.raises(ValidationError) as caught:
            base.model_validate({"__adcp_harness__": "no branch admits this"})
        assert [e["type"] for e in caught.value.errors()] == [
            lower_union.keyword(bundle.read(BUNDLE, document))
        ], (document, caught.value.errors())

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
    """The step's own arithmetic: 126 union roots, 34 emitted and 92 refused, each named.

    The by-keyword profile is asserted as a WHOLE rather than as a total, because the
    profile is the readable result of the step -- it says which later step unblocks what.

    **``allOf`` still dominates and no longer means "waiting on step 4".**  It used to:
    the keyword screen refused a root ``allOf`` with "a later D2 row does", naming step
    4's product row.  That row claims 0 of these documents -- ``composes_at_the_root``
    excludes a root carrying a union -- so the deferral named a row that was never going
    to see them.  All 51 are THIS module's own refusals: either a root where the
    ``allOf`` is a conjunction with every branch and no pointer addresses the
    conjunction (``ROOT_CONJUNCTS``), or a branch that composes and needs a conjunct
    reader D13 keeps out of this lowering's reach (``_plan``).  So the profile's
    largest row is a bill rather than a queue, which is what it is for.  The 37 + 9
    split the previous revision quoted was measured when ``allOf`` was 46 and is not
    re-measured here; what is asserted is the row.
    """
    out = emit.emit(BUNDLE, population())
    roots = union_roots()
    emitted = [d for d in roots if d in out.emitted]
    refused = [d for d in roots if d in out.refusals]
    assert len(roots) == 126
    # Roots emit only once another step's row is beside this one -- a nested ``enum``
    # (step 3), a nested container (step 6) -- and the presence-only combinators are
    # left for step 7.  Joint unblocking, which no single lane reaches.
    #
    # **34 / 92, RE-MEASURED AT 64131600f (``salesagent-j3k2l.29``).**  The 28 / 98
    # these replace were themselves a re-measurement, and the note then recorded that
    # 28 / 98 read identically at trunk ``29c553504``, so neither figure was that
    # lane's doing.  The same holds here: 126 is the SELECTOR's population and it has
    # not moved, while which of the 126 emit is a function of the other steps' rows,
    # and six more of them emit now.  Both halves are over one emit, so the two
    # numbers cannot drift apart -- the sum is asserted below.
    assert len(emitted) == 34, emitted
    assert len(refused) == 92
    assert len(emitted) + len(refused) == len(roots)
    assert emitted == emitted_unions()

    profile: dict[str, int] = {}
    for document in refused:
        row = out.refusals[document]
        assert row["keyword"] and row["pointer"], document
        profile[row["keyword"]] = profile.get(row["keyword"], 0) + 1
    assert profile == {
        # RE-MEASURED AT 64131600f (``salesagent-j3k2l.29``), in one pass with the
        # 34 / 92 above, so the dict and the totals are one measurement: the rows sum
        # to 92 by construction.
        "allOf": 51,
        "properties": 19,  # a root conjunct; see lower/union.py's docstring
        "$ref": 13,  # a bare-$ref branch, or a chain naming the target that refused
        "type": 4,  # a root stating no type whose branch states none either
        "required": 2,  # step 7 (D6)
        "additionalProperties": 1,
        "maxLength": 1,  # D5: a string bound beside a format: uri
        "not": 1,  # step 7 (D6) at a position the rules row does not reach
        # WHICH ROWS LEFT THIS PROFILE, kept as the record of why it is shaped this
        # way.  The per-row deltas each note quoted were true when its lane wrote it
        # and several are not arithmetic about the dict above, so the counts have been
        # removed where they would now read as assertions about it; what each lane DID
        # is what matters here.
        #
        # The `uniqueItems` row is GONE: `salesagent-j3k2l.19` lowers the keyword on
        # the class that holds the array, so a branch stating it reaches its NEXT
        # blocker instead of stopping here, and some of its documents emit.
        #
        # The `pattern` row is GONE: it was "a constraint inside a container", and D5's
        # alias module names that type now, so the document emits instead.
        #
        # The `definitions` and `$defs` rows are GONE: `salesagent-j3k2l.20` admits a
        # section at every node and declares the entries a `$ref` names, so each of
        # those documents now refuses on the keyword that actually stopped it -- in a
        # branch, in a conjunct, or inside the section itself.
        #
        # The `const` and `enumMetadata` rows are GONE from this profile as well; both
        # were present when the figures above were last written and neither appears in
        # the measured dict now.
        #
        # And four more rows have gone since: `anyOf` (6), `enum` (2), `if` (2) and
        # `oneOf` (1) are absent at this tree, while `not` fell from 10 to 1.  Those
        # 20 documents are among the six that now emit and the redistribution onto
        # `allOf` / `properties` / `$ref` / `type`; the attribution moved deeper, which
        # is the direction this profile exists to show.
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
    that the emitter refuses at ``type``.

    **The node here has nothing enclosing it, and that is the whole of what this test
    grades.**  A node stating no ``type`` whose ENCLOSING node constrains the instance
    to an object admits no non-object at all, so there is nothing for its class to be
    narrower than and it emits -- ``core/activation-key.json`` and
    ``core/reporting-write-destination.json`` are that case, declaring ``type: object``
    at their own root.  ``tests/test_applied_schema.py`` grades that distinction, in
    both directions and over the whole bundle.
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

    # **And no emitted document ADMITS a non-object at a root its class claims.**
    #
    # This was "no emitted document has a bare root", read off the raw document's own
    # ``type`` key, and it was an empty list until step 4's row emitted the
    # ``formats/canonical/`` family -- 7 documents whose root states ``properties``
    # and no ``type`` of its own because the type arrives through an ``allOf``
    # conjunct.  ``allOf`` CONJOINS, so a conjunct's ``type`` IS the root's, which is
    # the same reading ``_composed`` exists for above and the same mistake a bare
    # read made there (see ``test_extra_follows_the_schema_...``).
    #
    # So the population is no longer required to be empty -- it is 7 and growing --
    # and what is asserted of each member is the CLAIM: the document refuses an
    # instance of every other type, asked of ``jsonschema`` exactly as the first
    # half above asks it.  That is strictly more than the previous spelling said: an
    # empty list asserted nothing about any document, and this grades 7.
    bare = [
        d
        for d in sorted({g.ref.document for g in graded()})
        if bundle.read(BUNDLE, d).get("type") is None and "properties" in bundle.read(BUNDLE, d)
    ]
    assert len(bare) == 7, bare
    for document in bare:
        doc = schema_at(SchemaRef(document, "#"))
        assert _composed(doc).get("type") == "object", (document, _composed(doc).get("type"))
        for admitted in ("hello", 42, [1], None, True):
            assert not jsonschema.Draft7Validator(doc).is_valid(admitted), (document, admitted)


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
    # One per union base whose root states no ``type`` of its own, plus the
    # const-pinned branch properties whose node states only the ``const``.
    # Re-measured at 64131600f (``salesagent-j3k2l.29``): 45 / 19 / 26, a count over
    # ``graded()`` and so one that moves with the emitted population.  The two KINDS
    # did not move, which is the half that says the rule's shape is unchanged.
    assert len(excused) == 45, excused
    assert kinds == {"object", "string"}, kinds
    assert sum(1 for _, where, _ in excused if where == "") == 19, excused
    assert sum(1 for _, where, _ in excused if where != "") == 26, excused

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
    assert by_count[1] == 1047, by_count  # the six rows' own population
    # 7 and not 21: closing ``composes_at_the_root``'s two-reading hole moved 14 of
    # them onto step 4's row.  **The 7 that remain are not waiting for a row** -- four
    # are DATA documents with no schema keyword at the root, two are conditional-only
    # and one is a bare root ``$ref`` -- and ``emit.lower_document`` refuses each on
    # the keyword its kind is read from rather than on the absence of a row.
    assert by_count[0] == 7, by_count

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
            mine = _rendered(emitted, key, row.model)
            assert mine.get("type") == "array", (row.ref, key, mine)
            for keyword in ("minItems", "maxItems"):
                assert mine.get(keyword) == sub.get(keyword), (row.ref, key, keyword, mine)
                bounded += keyword in sub
            item = _unwrap(mine.get("items") or {}, emitted.get("$defs", {}))
            declared = sub.get("items") or {}
            # **THIS IS RED AT 64131600f AND IT IS RIGHT TO BE.**  Not a stale
            # constant: 4 mismatches over 2 properties of
            # ``core/attestation-capabilities.json``, whose elements state
            # ``{"type": "string", "format": "uri"}`` and nothing about length,
            # while the model's element carries ``minLength: 1, maxLength: 2083``.
            # Those are pydantic ``HttpUrl``'s own bounds, which D5's format row
            # brings in with the type, and they make the model NARROWER than its
            # document.  Proved through the production entry point rather than
            # inferred from the rendered schema: on an instance drawn from the
            # document by ``hypothesis_jsonschema`` with one 2,220-character https
            # URI substituted, ``jsonschema`` with the draft's own format checker
            # reports no error and ``strict_validate`` refuses with
            # ``url_too_long``.  The owner is D5's ``FORMAT_TYPES`` in
            # ``codegen/emit.py``, not this test, and re-pointing the assertion
            # would hide a live narrowing -- so it stays as written and
            # ``salesagent-j3k2l.29`` carries the finding.
            for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
                assert item.get(keyword) == declared.get(keyword), (row.ref, key, keyword, item)
    # The denominator is TOP-LEVEL array properties of an emitted root, not every
    # array node: an array nested inside another array's ``items`` has no property
    # node of its own to compare at and is graded by the schema comparison instead.
    # Stated so the number is not read as "every array".  Re-measured at 64131600f
    # (``salesagent-j3k2l.29``): 348 arrays, 231 of them bounded.
    assert arrays == 348, arrays
    assert bounded == 231, bounded


def test_unique_items_is_a_rule_on_the_holder_because_no_constraint_renders_it() -> None:
    """Why ``uniqueItems`` is D6's rule on the nearest class and not a constraint.

    The reason is a measurement and not a reading of D6: ``Constraints`` declares
    ``unique_items`` under the alias ``uniqueItems``, so the keyword is ACCEPTED and
    sets the field -- and the renderer then emits no ``Field`` at all, because
    pydantic v2 removed ``unique_items``.  Carrying it through ``constraints=`` would
    therefore be a model wider than its document, silently.

    So the keyword takes two channels, both of them the class's and neither of them
    the array's: the RULE narrows the constructor (D6), and
    ``json_schema_extra`` states the fact on the field, which is the same channel
    ``Property.format`` takes for the same reason -- the schema comparison reads
    ``uniqueItems`` off the model's rendered schema (``harness.FACTS``), so a fact
    only a validator enforces would read as ``missing``.

    Four cells: the keyword sets the constraints model, the rendering drops it, the
    class states both halves, and an array NO class holds is still refused by name.
    """
    from datamodel_code_generator.model.pydantic_v2.base_model import Constraints

    assert Constraints.model_fields["unique_items"].alias == "uniqueItems"
    assert Constraints(uniqueItems=True).model_fields_set == {"unique_items"}

    listed = compiler.Type(container="list", of=(compiler.Type("str"),))
    kept = compiler.render_alias("Kept", listed, {"minItems": 1})
    dropped = compiler.render_alias("Dropped", listed, {"uniqueItems": True})
    assert "min_length=1" in kept.text, kept.text
    assert "Field" not in dropped.text, dropped.text  # the fact has no rendering

    held = {
        "title": "U",
        "type": "object",
        "properties": {"a": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}},
    }
    mod, symbol = emit.lower_document("u.json", held)
    text = emit.render(mod, symbol)
    assert "UniqueItems('a')" in text, text
    assert "json_schema_extra={'uniqueItems': True}" in text, text

    # The array row's own screen is UNTOUCHED, which is what keeps an array with no
    # class above it refused rather than widened.  A mapping value is the shape that
    # still costs a document (`core/account-authorization.json`).
    with pytest.raises(Refusal) as caught:
        emit.lower_document(
            "v.json",
            {
                "title": "V",
                "type": "object",
                "properties": {
                    "m": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"},
                            "uniqueItems": True,
                        },
                    }
                },
            },
        )
    assert caught.value.keyword == "uniqueItems", caught.value
    assert caught.value.pointer == "/properties/m/additionalProperties", caught.value

    # And on the bundle: the keyword is down to the positions no class holds, each
    # named.  4 root arrays (D2's unimplemented `RootModel[list[X]]` row), one
    # mapping value, and one composing root -- `product.lower_root` writes no rule of
    # any D6 family, which is step 4's row and not this keyword's.
    out = emit.emit(BUNDLE, population())
    blocked = {d for d, r in out.refusals.items() if r["keyword"] == "uniqueItems"}
    assert sorted(blocked) == [
        "core/acceptance-policy-profile-ids.json",
        "core/account-authorization.json",
        "core/forecast-point-dimensions.json",
        "core/reporting-verification-profile-set.json",
        "media-buy/list-creative-formats-request.json",
        "media-buy/product-fields.json",
    ], sorted(blocked)
    assert {out.refusals[d]["pointer"] for d in blocked if d.endswith("-ids.json")} == {"/"}


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

    **ONE mapping site in the emitted population constrains its key, and D5's alias
    module names it.**  This read "no mapping site ... constrains its key", with the
    zero asserted so the key rule could not be read as covered by the bundle, and the
    zero has inverted: ``core/product-change-map.json``'s ROOT states
    ``propertyNames: {"minLength": 1}``, the document emits, and the emitted alias is
    ``dict[StrMinLen1, ProductChangeMapValue]`` -- the key carries the document's own
    bound rather than widening to ``str``.  Re-measured at 64131600f
    (``salesagent-j3k2l.29``), and asserted as the named site plus its key TYPE, which
    is strictly more than the zero said: the zero asserted that nothing was graded
    here, and this grades the one thing that is.

    Every OTHER mapping the committed tree carries is still ``dict[str, ...]``, which
    is the document's own reading rather than a default -- silence about keys means
    every string, and typing it further would be the SDK inventing a constraint.

    The one key kind that needs no name is the one that is graded behaviourally: a
    ``propertyNames`` ``$ref`` NAMES the key type, so the key is that type, the module
    IMPORTS it, and the model then refuses a key the key type refuses.  The kinds a
    NESTED mapping cannot name refuse by name below, and so does a closed key set --
    the root path and the nested path are different lowerings, which is why the one
    emitted constrained key sits at a root.
    """
    constrained: list[tuple[str, str]] = []
    mappings = 0
    for row in graded():
        doc = schema_at(row.ref)
        for pointer, node in bundle.nodes(doc):
            if node.get("type") == "object" and "properties" not in node:
                mappings += 1
                if {"propertyNames", "patternProperties"} & set(node):
                    constrained.append((f"{row.ref.document}{row.ref.pointer}", pointer or "/"))
    assert mappings == 1528, mappings
    assert constrained == [("core/product-change-map.json#", "/")], constrained
    # ... and the one that constrains its key is NAMED rather than widened.  The
    # symbol is asked of the namer rather than written here, so a rename moves this
    # with it (the precedent is ``tests/test_emit_product.py``'s narrowing case).
    named = constraints_module.symbol("string", {"minLength": 1})
    assert f"dict[{named}," in _source("core/product-change-map.json"), named
    assert (
        bundle.read(BUNDLE, "core/product-change-map.json")["propertyNames"]["minLength"] == 1
    ), "the bound the key type carries is the document's own"

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

    Measured: 727 documents mention ``additionalProperties`` and 51 carry a typed one.
    7 of the 51 emit now and every one of those is the MAPPING path; the extras store
    needs a node declaring ``properties`` AND a typed ``additionalProperties``, the
    bundle has 14 such nodes, and none of their documents is emitted -- so the store
    itself is reached by 0 documents.  The mechanism is built anyway because it is
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
    # 7 of the 51 are emitted, and every one of them is the mapping path rather than
    # the extras store: each typed ``additionalProperties`` in those 7 sits on a node
    # with NO ``properties``, so it is a mapping and the row above lowers it.  The
    # extras store needs a node with BOTH, the bundle has 14 such sites, and 0 of
    # them is in a document this run emits -- so the store is graded by the probe
    # below and by 0 documents.  Both halves are asserted, because "7 emitted" and
    # "0 of them reach the store" are different facts and the second is the claim.
    #
    # Re-measured at 64131600f (``salesagent-j3k2l.29``).  The 14 is unchanged and is
    # over the bundle; the emitted list is over ``population()`` and grew from 1.  The
    # previous revision said the 14 "all sit under ``definitions``", which is not
    # true of this bundle -- 4 of them are at a document's own root -- so the reason
    # recorded here is now the measured one: none of the 14 is in an emitted document.
    emitted_typed = sorted(set(typed) & set(out.emitted))
    assert emitted_typed == [
        "a2ui/component.json",
        "collection/get-collection-list-response.json",
        "core/product-change-map.json",
        "core/reporting-file-entry.json",
        "core/tasks-list-response.json",
        "error-details/vendor-error-codes.json",
        "protocol/list-tasks-response.json",
    ], emitted_typed
    store = [
        (d, pointer or "/")
        for d in bundle.portable(BUNDLE)
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(node.get("additionalProperties"), dict)
        and node["additionalProperties"]
        and "properties" in node
    ]
    assert len(store) == 14, store
    assert [row for row in store if row[0] in out.emitted] == [], store

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
    # 11 and not 2: core/webhook-activity-record.json and core/registry-event.json
    # carry a DECLARED null beside their type and emit now, so the live sites are no
    # longer only error-details/conflict.json's two ['number', 'string'].
    # Re-measured at 64131600f (``salesagent-j3k2l.29``): 11, a count over
    # ``graded()`` and so one that moves with the emitted population.
    assert len(live) == 11, live
    for ref, key in live:
        doc = schema_at(ref)
        model = next(r.model for r in graded() if r.ref == ref)
        # The document's own key, not ``compiler.field_name``'s: the rendered schema
        # is ``by_alias`` and an aliased property is carried under the document's
        # key.  Indexed WITHOUT ``_rendered``, because this test reads the ``anyOf``
        # branch set and ``_rendered`` folds a ``T | None`` out of it.
        node = model.model_json_schema()["properties"][key]
        declared = doc["properties"][key]["type"]
        # pydantic has no spelling for a type LIST but a union, so the document's
        # types come back as branches.  **A ``null`` the DOCUMENT DECLARES is one of
        # them**, and D4's null for a merely optional property is not -- the two are
        # the same branch and different facts, which is the conflation
        # ``test_a_declared_null_is_never_read_as_absence`` grades.  So the branch set
        # is compared against the document's own list, and the presence branch is
        # dropped only where the document declares no null to account for it.
        branches = [b["type"] for b in node["anyOf"]]
        if "null" not in declared:
            branches = [b for b in branches if b != "null"]
        assert sorted(branches) == sorted(declared), (ref, key, node)
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
    # And it costs no document: 0 multi-type node in an EMITTED document states a
    # constraint WITH TWO OR MORE LIVE ARMS, which is why this is graded on a
    # constructed one. The live count is the whole of the condition -- with one live
    # arm the node is ``T | None``, which the comparison reads exactly (see
    # ``test_a_declared_null_is_never_read_as_absence``) -- so a node with one live
    # arm and a constraint is emitted and is NOT a violation here.
    from codegen.lower import containers as lower_containers

    emitted = emit.emit(BUNDLE, population()).emitted
    carried = frozenset().union(*lower_containers.ARM.values())
    assert [
        (d, p)
        for d in emitted
        for p, node in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(node.get("type"), list)
        and set(node) & carried
        and len([k for k in node["type"] if k != "null"]) > 1
    ] == []

    # **A null arm no longer refuses: it is an ARM.** The refusal stood on the
    # grader, and the grader reads it now -- so the cell asserts the EMISSION and the
    # annotation, because a cell that only stopped asserting the refusal would pass
    # for a row that silently dropped the arm.
    mod, symbol = emit.lower_document(
        "mn.json",
        {"title": "MN", "type": "object", "properties": {"v": {"type": ["string", "null"]}}},
    )
    assert symbol == "MN"
    assert "v: str | None" in "\n".join(mod.blocks), mod.blocks

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


def test_a_declared_null_is_never_read_as_absence() -> None:
    """``["string", "null"]`` and an OPTIONAL ``{"type": "string"}`` are different
    documents, and D4 renders BOTH as ``str | None``.

    So the model's own schema does not say which document it came from, and the
    comparison used to decide by unwrapping any single ``null`` branch as absence
    -- which erased the declared fact and made the two cases one cell. A faithful
    model was reported as dropping its ``type``, and a model that DROPPED the
    declared null was reported identically, so neither could be graded.
    ``lower.containers.multi_type`` refused a ``null`` arm by name for exactly
    that reason.

    **This is the test that reddens if a declared null is ever read as absence
    again**, and it is written as the pairs the two readings disagree about rather
    than as an assertion about ``_normalize``'s internals: the fix has to keep the
    unwrap that D4 needs AND report a dropped declaration, and only a test holding
    both at once can tell a correct fold from a silencer.
    """
    declared = {
        "title": "D",
        "type": "object",
        "required": ["v"],
        "properties": {"v": {"type": ["string", "null"]}},
    }
    optional = {"title": "O", "type": "object", "properties": {"v": {"type": "string"}}}
    optional_nullable = {
        "title": "ON",
        "type": "object",
        "properties": {"v": {"type": ["string", "null"]}},
    }
    four = {
        "title": "F",
        "type": "object",
        "required": ["v"],
        "properties": {"v": {"type": ["string", "number", "boolean", "null"]}},
    }

    class ReqNullable(AdCPBaseModel):
        v: str | None

    class OptNullable(AdCPBaseModel):
        v: str | None = None

    class NullDropped(AdCPBaseModel):
        v: str

    class Four(AdCPBaseModel):
        v: str | float | bool | None

    class FourNullDropped(AdCPBaseModel):
        v: str | float | bool

    # The two documents that render the same annotation both pass, which is the
    # whole point: the comparison now tells them apart instead of conflating them.
    assert compare_schema(declared, ReqNullable).outcome == "pass"
    assert compare_schema(optional, OptNullable).outcome == "pass"
    assert compare_schema(optional_nullable, OptNullable).outcome == "pass"
    assert compare_schema(four, Four).outcome == "pass"

    # **AND THE FOLD IS NOT A SILENCER.** A model that drops the document's own
    # declared ``null`` is reported, in both shapes of the fold -- one live branch
    # beside the null, and three.
    for doc, model in ((declared, NullDropped), (optional_nullable, NullDropped),
                       (four, FourNullDropped)):
        res = compare_schema(doc, model)
        assert res.outcome == "model_drops_a_fact", (doc["title"], res)
        assert [d.split(": ")[0] for d in res.differs] == ["/properties/v/type"], res.differs

    # The SECOND half, and the one the bead does not name: the ``default`` D4
    # renders for an optional property. ``_narrows_nothing`` read the node's
    # declared null as a proxy for the REQUIRED axis, and the proxy is wrong in
    # both directions -- so it reads ``required`` now. Four cells of one rule.
    for kind in (["string", "null"], "string"):
        assert harness._narrows_nothing(  # noqa: SLF001 -- the rule under test
            "default", None, {"type": kind}, required=False
        ), kind
        assert not harness._narrows_nothing(  # noqa: SLF001 -- the rule under test
            "default", None, {"type": kind}, required=True
        ), kind
    # An invented value is still an added claim whatever the presence axis says.
    assert not harness._narrows_nothing(  # noqa: SLF001 -- the rule under test
        "default", "x", {"type": "string"}, required=False
    )

    # And the axis reaches the rule from the comparison rather than sitting there
    # inert: a model stating ``default: null`` at a key the document DEMANDS is
    # reported. ``json_schema_extra`` is how a required field renders one at all --
    # a pydantic field with a real default is not required, which is the same
    # reason ``compiler.fields`` refuses a document default on a required property.
    class ReqDefaulted(AdCPBaseModel):
        v: str | None = Field(..., json_schema_extra={"default": None})

    res = compare_schema(declared, ReqDefaulted)
    assert res.outcome == "model_adds_a_fact", res
    assert [a.split(": ")[0] for a in res.added] == ["/properties/v/default"], res.added


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
    assert (positions, len(modules)) == (23, 13), (positions, sorted(modules))


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


#: A two-document bundle for the prune: both documents emit, and the second is then
#: rewritten so that it REFUSES, which is the only way a file stops being intended.
#: Hand-built rather than cut from the 3.2 bundle, because the scenario needs a
#: document whose emission is turned OFF between two runs and no bundle document can
#: be asked to do that without editing the bundle.
def _prunable(bundle_dir: Path, name: str, extra: dict[str, Any] | None = None) -> None:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / f"{name}.json").write_text(
        json.dumps(
            {
                "title": name.title(),
                "type": "object",
                "properties": {"a": {"type": "string"}},
                **(extra or {}),
            }
        )
    )


#: What makes the second document stop emitting.  A ``required``-only ``allOf``
#: conjunct: step 4's row claims the root, reaches the conjunct, and refuses because
#: a conjunct with no ``properties`` has no base to subclass.  The test ASSERTS the
#: refusal rather than assuming it, for the reason
#: ``test_the_cli_reports_a_refusal_rather_than_raising_it`` records: that fixture
#: once used ``not: {}``, a later row lowered it, and the test went on passing over a
#: bundle with no refusal in it.  Whichever row claims this next moves the fixture,
#: and the assertion is what says so out loud.
_STOPS_EMITTING = {"allOf": [{"required": ["a"]}]}


def test_write_removes_a_file_the_run_no_longer_intends(tmp_path) -> None:
    """The prune, graded by making a document stop emitting.

    This is the defect's whole shape: a stale ``.py``/``.json`` pair is
    INDISTINGUISHABLE from a real emission to everything that reads the tree -- the
    class imports, carries ``__adcp_schema__``, and answers ``strict_validate`` --
    so the harness can grade a class the current compiler would not produce, which
    is the one thing §2's per-class schema reference exists to make impossible.

    It was caught before this only by ``test_the_committed_tree_is_what_a_fresh_run_emits``
    comparing file SETS, which fails at the GATE and leaves the operator to derive
    the stale set and delete it by hand.  Two lanes did exactly that
    (``salesagent-j3k2l.22``, 4 files, and ``.26``), so every change that added a
    refusal was a two-step job with nothing enforcing the second step.

    PROBED by removing the two lines in ``emit.write`` that delete: this test then
    fails on the last assertion with ``goes.json`` and ``goes.py`` still in the tree.
    """
    bundle_dir, tree, package = tmp_path / "bundle", tmp_path / "tree", tmp_path / "package"
    package.mkdir()

    _prunable(bundle_dir, "stays")
    _prunable(bundle_dir, "goes")
    documents = ["goes.json", "stays.json"]
    first = emit.emit(bundle_dir, documents)
    assert first.refusals == {}, first.refusals
    emit.write(first, tree, package)

    def kinds(root: Path) -> list[str]:
        return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())

    assert kinds(tree) == ["__init__.py", "goes.json", "goes.py", "stays.json", "stays.py"]

    # The document stops emitting, which is what every row that adds a refusal does
    # to some document.  Asserted, not assumed -- see ``_STOPS_EMITTING``.
    _prunable(bundle_dir, "goes", _STOPS_EMITTING)
    second = emit.emit(bundle_dir, documents)
    assert sorted(second.refusals) == ["goes.json"], second.refusals
    assert sorted(second.emitted) == ["stays.json"], sorted(second.emitted)

    emit.write(second, tree, package)
    assert kinds(tree) == ["__init__.py", "stays.json", "stays.py"]


def test_a_partial_run_prunes_nothing(tmp_path) -> None:
    """The other half, and the reason a prune was tried here once and removed.

    ``write`` is the same function the README's ONE-DOCUMENT command reaches.  A
    one-document run intends one document's files, so a prune that did not ask the
    run's scope would delete the other 676 modules of the committed tree -- and a
    command whose demonstration wipes the tree gets run once.  ``package`` is the
    discriminator already present for D5's alias module, which is a whole-run
    artifact for the same reason, so the two whole-run effects are gated on one
    fact and there is no second flag to forget.

    Without this test the prune's gate is ungraded and the obvious "simplification"
    -- prune unconditionally -- passes the test above.
    """
    bundle_dir, tree = tmp_path / "bundle", tmp_path / "tree"
    _prunable(bundle_dir, "stays")
    _prunable(bundle_dir, "goes")
    emit.write(emit.emit(bundle_dir, ["goes.json", "stays.json"]), tree, tmp_path / "package")

    # The whole population is still both documents and ``goes`` still emits; what
    # changes is that this run NAMES one of them, so it intends one document's files.
    partial = emit.emit(bundle_dir, ["stays.json"])
    assert sorted(partial.emitted) == ["stays.json"], sorted(partial.emitted)
    emit.write(partial, tree)

    survived = sorted(str(p.relative_to(tree)) for p in tree.rglob("*") if p.is_file())
    assert survived == ["__init__.py", "goes.json", "goes.py", "stays.json", "stays.py"]


def test_the_emitter_writes_only_the_file_kinds_the_prune_removes() -> None:
    """``emit.EMITTED_SUFFIXES`` bounds what ``write`` will delete, and it is a
    DECLARATION -- so this grades it against the emitter's actual output.

    Derived from ``Emitted.files`` instead, the bound has a hole exactly where it
    matters: a whole-population run that emitted nothing derives ``{".py"}`` from
    its lone ``__init__.py`` and silently leaves every stale document behind.  So
    the constant is written down, and this is what keeps it in step.  Both
    directions redden: a third file kind in the tree, and a narrowed constant.

    The committed tree is the emitter's output byte for byte -- the test above
    asserts exactly that -- so reading the kinds off it costs nothing, where a
    second whole-population emit costs the run again.
    """
    kinds = {p.suffix for p in TREE.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert kinds == emit.EMITTED_SUFFIXES, sorted(kinds)


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
    because ``FORMAT_TYPES`` points 12 modules' fields at it.
    """
    imported: dict[str, set[str]] = {}
    for module in sorted(TREE.rglob("*.py")):
        tree = ast.parse(module.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == constraints_module.MODULE:
                assert not node.level, (module, "an alias is imported absolutely")
                for alias in node.names:
                    imported.setdefault(alias.name, set()).add(str(module.relative_to(TREE)))

    # A name this module provides is one it ASSIGNS or one it RE-EXPORTS.  D5's two
    # URL arms are one of each: ``AdCPUrl`` is ours and is an assignment, and
    # ``HttpUrl`` is pydantic's, re-exported here with no assignment so that nothing
    # in this package restates what pydantic defines -- the import IS the
    # declaration, and both arms are then named in the one module a consumer reads.
    module = ast.parse((TREE.parent / "constraints.py").read_text())
    declared = {
        node.targets[0].id
        for node in module.body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    }
    reexported = {
        alias.asname or alias.name
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "pydantic"
        for alias in node.names
    }
    assert constraints_module.HTTP_URL in reexported, reexported
    declared |= {constraints_module.HTTP_URL}
    assert declared, "the alias module declares nothing"
    assert set(imported) - declared == set(), "imported and not declared"
    assert declared - set(imported) == set(), "declared and never named"

    # The denominators, so neither direction can pass over an empty set: every
    # alias is reachable at this one path and nowhere else (no flat root, no
    # second spelling), and the module is not a dumping ground.
    # Re-measured at 64131600f (``salesagent-j3k2l.29``): every count here is over the
    # committed TREE, which is the ``population()`` run (991 named documents, 677
    # emitted), so each one moves as that run grows.  The two DIRECTIONS above are
    # what the test is for and they are set equalities, not counts.
    assert len(declared) == 133, len(declared)  # the derived shapes + AdCPUrl + HttpUrl
    # (module, alias) pairs, which is NOT the site count: a module importing one
    # alias for five of its fields contributes one pair.
    assert sum(len(where) for where in imported.values()) == 684, imported
    # And the one name that is a decision really is annotating fields.
    assert len(imported[constraints_module.URL]) == 12, sorted(imported[constraints_module.URL])
    assert len(imported[constraints_module.HTTP_URL]) == 75, sorted(imported[constraints_module.HTTP_URL])


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
    "uniqueItems": (462, 198),
    "not": (439, 192),
    "then": (582, 186),
    "else": (58, 44),
    "anyOf": (444, 200),
    "oneOf": (212, 165),
    "dependencies": (85, 27),
    "minProperties": (47, 40),
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
    assert sum(census[k][0] for ks in families.values() for k in ks) == 2348


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
    #: The one kind whose keyword sits BELOW the node that carries the rule: an array
    #: a property holds.  So its reachable count equals its site count by
    #: construction -- a node with a ``properties`` map is the only node it is read
    #: off at all -- and that identity is the assertion, not a coincidence.
    "UniqueItems": (464, 188, 464),
    "ForbiddenGroups": (398, 171, 167),
    "RequiredGroups": (297, 161, 70),
    "ConditionalRequired": (294, 128, 12),
    #: 57 and not 61: ``_count`` writes the MINIMUM only where the document states
    #: ``additionalProperties``, because under D8's ``ignore`` a dropped key makes
    #: the rule refuse an instance the document ACCEPTS.  4 nodes state a
    #: ``minProperties`` and nothing else countable, so they now write no rule.
    "PropertyCount": (57, 40, 27),
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
    ``Rule.errors`` takes ``keys`` and ``values`` and never a model.

    ``UniqueItems`` is the opposite case and the reason it is a seventh kind rather
    than a seventh ambition: its keyword is read off a property's own declaration, so
    every node it is written at HAS a ``properties`` map and its reachable count
    equals its site count -- asserted below rather than remarked on.
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
    assert len(measured) == 7, "a rule kind nothing writes is dead code"
    # ``uniqueItems``'s own identity, stated so a lowering that started reading the
    # keyword off a node with no ``properties`` map would redden here: the kind is
    # read off a property's declaration, so every site it is written at is reachable.
    sites, _documents, reachable = measured["UniqueItems"]
    assert sites == reachable, measured["UniqueItems"]


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
        UniqueItems,
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

    # ``UniqueItems`` is judged on the VALUE and not on which keys arrived, so its
    # fixture is a values map.  Six rows, each a reading this kind has to get right:
    # distinct, repeated, draft-07's ``true != 1`` against Python's ``True == 1``,
    # the unhashable items that rule ``set[X]`` out as an annotation, a non-array
    # value (a union arm the keyword says nothing about), and an absent key.
    for rule, values, keyword in [
        (UniqueItems("t"), {"t": ["a", "b"]}, None),
        (UniqueItems("t"), {"t": ["a", "a"]}, "uniqueItems"),
        (UniqueItems("t"), {"t": [True, 1, 1.0]}, "uniqueItems"),  # 1 == 1.0, true != 1
        (UniqueItems("t"), {"t": [True, 1]}, None),
        (UniqueItems("t"), {"t": [{"a": 1}, {"a": 1}]}, "uniqueItems"),
        (UniqueItems("t"), {"t": "not an array"}, None),
        (UniqueItems("t"), {}, None),
    ]:
        got = [e[0] for e in rule.errors(frozenset(values), values)]
        assert got == ([keyword] if keyword else []), (rule, values, got)
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
    # **THE DOCUMENT EMITS NOW, so the claim is graded on a CLASS.**  This line
    # asserted the document was refused -- "so the pair above is a harness control
    # rather than a class: it refuses on `enum`, which is step 3's row" -- and step
    # 3's row emits it at 64131600f (``salesagent-j3k2l.29``), refusals ``{}``.  The
    # inversion hands the test a strictly better instrument than the refusal was: the
    # ceiling D6 accepts is now observable on the emitted class, so it is asserted
    # there.  ``model_validate`` ACCEPTS the violating payload, because no rule
    # observes a statement about a VALUE, and the schema half refuses the same
    # payload on ``maximum`` -- which is the whole of what this test claims, now
    # measured on the production entry point instead of on a document's absence.
    assert emit.emit(BUNDLE, [document]).refusals == {}, "it refused once; see above"
    emitted = next(g for g in graded() if g.ref == SchemaRef(document, "#"))
    assert [type(r).__name__ for r in emitted.model.__dict__.get("_adcp_rules", ())] == [
        "Dependencies"
    ], emitted.model.__dict__.get("_adcp_rules")
    assert emitted.model.model_validate(violating), "a value rule is not a rule"
    with pytest.raises(ValidationError) as caught:
        emitted.accept(violating)
    assert [e["type"] for e in caught.value.errors()] == ["maximum"], caught.value.errors()


def test_the_uniqueItems_step_grades_an_emitted_class_and_its_rule_holds_it() -> None:
    """The keyword is stepped, the tree now carries it, and a rule holds every site.

    This test replaces one that recorded a BAD PROBE: ``uniqueItems`` was stepped at
    462 sites over 198 documents and 0 of them was on an emitted pair, so breaking
    the step's duplicate forcing reddened only its own exclusivity assertion.  Both
    halves of that recording are kept and the second is inverted rather than
    dropped -- the keyword is still stepped, and every site the tree now carries is
    held by a class whose rule refuses a duplicate.

    Three directions, because the second alone would pass for a class that renders
    the fact and enforces nothing:

    1. the step census still finds the keyword (the instrument did not go quiet);
    2. the tree carries it, at a NON-EMPTY set of sites, and every one of them is a
       ``properties/<name>`` array whose holding class states ``UniqueItems`` for
       that field -- so a site the lowering missed reddens here;
    3. one of those classes REFUSES a duplicate through ``model_validate``, which is
       the only path a rule is observable on (D4 leaves acceptance to the schema).
    """
    census = _step_census()
    assert census["uniqueItems"] == (462, 198)

    carried = [
        f"{document}{pointer or '/'}"
        for document in sorted({g.ref.document for g in graded()})
        for pointer, node in bundle.nodes(schema_at(SchemaRef(document, "#")))
        if isinstance(node, dict) and "uniqueItems" in node
    ]
    assert carried, "the tree emits no document carrying the keyword; the step is unreached"

    # Direction 2, over EVERY class the tree ships rather than over the carried sites:
    # the ``UniqueItems`` keys a class states and the keys its own node's properties
    # declare distinct are the SAME SET.  Read off the raw bundle document at the
    # class's own pointer, not off the packaged one -- a resolved document inlines a
    # ``$ref``'s nodes, so a site at ``/properties/vendor/properties/countries`` there
    # belongs to the TARGET's class and is graded on the target's own pair (14 of the
    # carried sites are that).  The gate is spelled here rather than called, so a
    # lowering that stopped reading the keyword reddens.
    # **Read off each class's OWN declaration (``__dict__``) and not through the
    # MRO.**  ``_adcp_rules`` is a class attribute, so ``getattr`` on a SUBCLASS
    # answers its base's tuple, and the two sides of this comparison were then at
    # different scopes: the document side is this class's own node, and the class side
    # was its node's rules plus every base's.  Measured at 64131600f over all 1,034
    # pairs, that is exactly one disagreement -- ``core/assets/catalog-asset.json#``,
    # whose root is ``allOf: [{$ref: core/catalog.json}]`` and whose class declares no
    # rules of its own, so ``getattr`` reported ``Catalog``'s
    # ``UniqueItems('conversion_events')`` against a document that declares no such
    # property.  Reading the class's own declaration gives 0 disagreements, and it is
    # the same attribution rule the raw-document read above is chosen for: a site
    # belongs to the class that DECLARES it and is graded on that class's own pair.
    # 173 of the tree's classes declare a rule tuple, so this is not an empty read.
    wrong: list[str] = []
    for g in graded():
        if not isinstance(g.model, type):
            continue  # D2's root-scalar alias: no class, and no rule tuple to read
        raw = dict(bundle.nodes(bundle.read(BUNDLE, g.ref.document)))
        node = raw.get(g.ref.pointer.removeprefix("#"))
        if not isinstance(node, dict):
            continue  # a class at a pointer the raw walk does not reach
        want = sorted(
            key
            for key, declaration in (node.get("properties") or {}).items()
            if isinstance(declaration, dict)
            and declaration.get("type") == "array"
            and declaration.get("uniqueItems") is True
        )
        got = sorted(
            r.key
            for r in g.model.__dict__.get("_adcp_rules", ())
            if type(r).__name__ == "UniqueItems"
        )
        if got != want:
            wrong.append(f"{g.ref.document}{g.ref.pointer}: states {got}, the document {want}")
    assert wrong == [], wrong
    held = [
        g
        for g in graded()
        if isinstance(g.model, type)
        and any(
            type(r).__name__ == "UniqueItems" for r in g.model.__dict__.get("_adcp_rules", ())
        )
    ]
    # 87 at 64131600f, declared by the classes themselves; >= so the test states a
    # floor rather than a count over the emitted population, which moves every merge.
    assert len(held) >= 19, len(held)  # the keyword's own population, not an empty loop

    # Direction 3: the rule, on the constructor, on a class the tree ships.
    from adcp.types._schemas.core.property import Property as PropertyModel

    ok = {"property_type": "website", "name": "n", "identifiers": [{"type": "domain", "value": "a"}]}
    assert PropertyModel.model_validate({**ok, "tags": ["a", "b"]}).tags == ["a", "b"]
    with pytest.raises(ValidationError) as caught:
        PropertyModel.model_validate({**ok, "tags": ["a", "a"]})
    assert caught.value.errors()[0]["type"] == "uniqueItems", caught.value.errors()

    assert "uniqueItems" in rules.KEYWORDS, "the keyword must not block an object lowering"
    # **This line used to assert the OPPOSITE and the design reversed under it.**  It
    # read ``not any("UniqueItems" in source for source in RULE_KIND_POPULATION)``,
    # which iterates that dict's KEYS; it was written at ``438240878`` when the dict
    # had six keys and no ``UniqueItems``, and ``d50d26481`` made ``UniqueItems`` the
    # seventh rule kind and left the line standing -- so it has asserted a falsehood
    # about its own module-level constant ever since, with no number to re-point.
    # The fact that is true now is the one the kind was added for, and its arithmetic
    # (sites == reachable, over the bundle) is graded by
    # ``test_every_rule_kind_is_written_from_a_real_bundle_node``.
    assert "UniqueItems" in RULE_KIND_POPULATION, sorted(RULE_KIND_POPULATION)


# --------------------------------------------------------------------------- #
# D2's `const` row: a pinned value is a `Literal` (salesagent-j3k2l.16)
# --------------------------------------------------------------------------- #
def _const_nodes() -> list[tuple[str, str, dict]]:
    """Every ``const`` node in the bundle, at a schema position, with its pointer.

    Derived from ``bundle.nodes`` rather than from a key search, for that walk's own
    reason: a ``const`` holds INSTANCE data, so a value inside one may itself be an
    object with a property named ``const``.
    """
    return [
        (document, pointer, node)
        for document in bundle.portable(BUNDLE)
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document))
        if "const" in node
    ]


def test_a_const_node_is_a_literal_over_the_value_it_pins() -> None:
    """The row, end to end on a document written here, and graded in both directions.

    The value's own JSON type is what the node admits, so the three shapes the bundle
    writes are all here -- a ``const`` with the document's ``type`` word beside it,
    one without, and a boolean -- and the pair is graded by ``compare_schema``, which
    is the check that says the model neither drops nor adds a fact.
    """
    doc = {
        "title": "Pinned",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "typed": {"type": "string", "const": "collection_list_changed"},
            "typeless": {"const": "asap"},
            "flag": {"type": "boolean", "const": True},
        },
        "required": ["typed", "typeless", "flag"],
    }
    model, text = _constructed(doc)
    # the import is the COMPILER's: the row adds none, and dmcg reports the one its
    # own rendering needs.
    assert "from typing import ClassVar, Literal" in text, text
    assert "typed: Literal['collection_list_changed']" in text, text
    assert "typeless: Literal['asap']" in text, text
    assert "flag: Literal[True]" in text, text

    comparison = compare_schema(doc, model)
    assert comparison.outcome == "pass", comparison
    assert comparison.added == [], comparison.added
    assert comparison.missing == [], comparison.missing
    assert comparison.differs == [], comparison.differs

    # and the Literal is the accepted set, not an annotation: the pinned value in,
    # anything else out.
    accept = _accept_of(doc, model)
    assert accept({"typed": "collection_list_changed", "typeless": "asap", "flag": True})
    with pytest.raises(Exception):  # noqa: B017, PT011 -- either half may refuse first
        accept({"typed": "something_else", "typeless": "asap", "flag": True})


def test_a_pinned_value_carrying_a_dot_renders_whole() -> None:
    """The regression this row was built on top of, and it is the compiler's seam.

    The annotation used to be spelled in the WALK -- ``Type(f"Literal[{value!r}]",
    local=True)``, in ``lower.union._literal`` -- and reached dmcg as a ``Reference``
    PATH, where ``treat_dot_as_module`` reads a dot as a module qualifier and keeps
    the last segment.  ``Literal['account.status_changed']`` rendered as
    ``status_changed']`` and ``core/account_status_changed_webhook.py`` did not parse.
    Measured the other way on the same type manager: ``data_type(literals=[...])``
    renders the value whole, escapes it, and reports its own import.

    **0 of the 25 distinct Literals the old spelling actually emitted carries a dot**,
    which is why the defect was latent -- while **103 of the bundle's ``const``
    values, over 37 documents, do**.  Both denominators are asserted, because the
    first alone reads as a claim about the bundle and the second alone does not say
    why nothing caught it.
    """
    dotted = [v for _, _, n in _const_nodes() if isinstance(v := n["const"], str) and "." in v]
    assert len(dotted) == 103, len(dotted)
    emitted_dotted = [
        node["const"]
        for g in graded()
        for _, node in bundle.nodes(schema_at(SchemaRef(g.ref.document, "#")))
        if isinstance(node.get("const"), str) and "." in node["const"]
    ]
    assert emitted_dotted, "no dotted pin reaches the tree; this regression is ungraded"

    model, text = _constructed(
        {
            "title": "Dotted",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "notification_type": {"type": "string", "const": "account.status_changed"}
            },
            "required": ["notification_type"],
        }
    )
    assert "Literal['account.status_changed']" in text, text
    assert (
        model.model_json_schema()["properties"]["notification_type"]["const"]
        == "account.status_changed"
    )
    # the quoting is the compiler's too, which a hand-built f-string would also own
    _, quoted = _constructed(
        {
            "title": "Quoted",
            "type": "object",
            "additionalProperties": False,
            "properties": {"k": {"type": "string", "const": "it's"}},
            "required": ["k"],
        }
    )
    assert 'Literal["it\'s"]' in quoted, quoted


def _const_refusal(node: dict) -> Refusal:
    """The refusal a document whose one property is ``node`` lowers to."""
    doc = {"title": "Bad", "type": "object", "properties": {"k": node}, "required": ["k"]}
    with pytest.raises(Refusal) as caught:
        emit.lower_document("bad.json", doc)
    return caught.value


def test_a_const_that_cannot_be_a_literal_is_refused_by_name() -> None:
    """Fire probe for both of the row's refusals, each made to fail.

    Both have a population of 0 in this bundle
    (``test_the_const_row_claims_no_root_and_lowers_every_const_node`` asserts the
    value types), so a hand-built node is the only way to reach either -- and a
    refusal nothing reaches is a refusal nobody has read.

    ``codegen.lower.const.LITERALS`` is also graded against the COMPILER's own slot
    rather than taken on trust, because that is where it comes from: a pin bump that
    widened or narrowed ``DataType.literals`` would otherwise leave the row refusing
    a value the compiler can now spell, or admitting one it cannot.
    """
    annotation = str(DataType.model_fields["literals"].annotation)
    assert {t.__name__ for t in lower_const.LITERALS} == {
        name for name in ("bool", "int", "str", "float", "bytes") if f"[{name}," in annotation
    }, annotation

    # the four types the slot has no spelling for: without the refusal each of these
    # is a pydantic ValidationError raised inside dmcg, naming no document.
    for value, name in (({}, "dict"), ([], "list"), (None, "NoneType"), (1.5, "float")):
        node = {"const": value} if value is not None else {"type": "null", "const": None}
        r = _const_refusal(node)
        assert r.keyword == "const", r
        assert r.pointer == "/properties/k", r
        assert f"a const of {name} has no Literal" in r.detail, r

    # ... and the null node written the other way round IS answered, by the branch that
    # owns that node kind
    _, text = _constructed(
        {
            "title": "Nulled",
            "type": "object",
            "properties": {"k": {"type": "null"}},
            "required": ["k"],
        }
    )
    assert "k: None" in text, text

    # a const its own type REFUSES: the node admits nothing, so a Literal of the
    # value would be a model wider than its schema.
    r = _const_refusal({"type": "string", "const": 3})
    assert r.keyword == "const", r
    assert "the node admits nothing" in r.detail, r
    # ... and the same node with an agreeing type word does NOT refuse
    model, _ = _constructed(
        {
            "title": "Agrees",
            "type": "object",
            "properties": {"k": {"type": "integer", "const": 3}},
            "required": ["k"],
        }
    )
    assert model.model_json_schema()["properties"]["k"]["const"] == 3


def test_a_keyword_beside_a_const_refuses_rather_than_being_dropped() -> None:
    """The row's screen, probed by making it fail.

    :data:`codegen.lower.const.HANDLED` is two keywords because two is the whole
    vocabulary the bundle writes beside a ``const``, asserted over all 1,486 nodes
    below.  A third would be a constraint applied to a value the ``Literal`` has
    already pinned, and dropping it silently is the defect P3 removes -- so it
    refuses, by the keyword's own name.
    """
    assert lower_const.HANDLED == frozenset({"type", "const"})
    r = _const_refusal({"type": "string", "const": "x", "minLength": 2})
    assert r.keyword == "minLength", r
    assert r.pointer == "/properties/k", r


def test_the_const_row_claims_no_root_and_lowers_every_const_node() -> None:
    """The row's population, and why it is NOT an entry in ``emit.ROWS``.

    Four facts, each asserted over the whole bundle rather than over the emitted
    tree, because the claim is about the row's reach and not about today's tree:

    * **0 of the 1,054 documents carries a ``const`` at its ROOT**, so there is no
      root kind for a row to claim, nothing goes into
      ``bundle.declares_its_own_root_kind``, and the table's partition is untouched;
    * the vocabulary beside a ``const`` is ``type`` and ``description`` and nothing
      else, which is what makes ``HANDLED`` two keywords;
    * no node writes both an ``enum`` and a ``const``, so ``_decide``'s two branches do
      not overlap and their order there is not a precedence;
    * **0 documents refuse on ``const``** over the whole portable population -- the
      row claims D2's keyword in full, so there is no deferral left.
    """
    nodes = _const_nodes()
    assert len(nodes) == 1486, len(nodes)
    assert len({d for d, _, _ in nodes}) == 347
    assert [(d, p) for d, p, _ in nodes if p == ""] == []

    beside: set[str] = set()
    for _, _, node in nodes:
        beside |= {k for k in node if k != "const" and not k.startswith("x-")}
    assert beside == {"type", "description"}, beside
    assert [(d, p) for d, p, n in nodes if "enum" in n] == []

    portable = bundle.portable(BUNDLE)
    out = emit.emit(BUNDLE, portable)
    assert len(out.emitted) + len(out.refusals) == len(portable)
    on_const = {d: r for d, r in out.refusals.items() if r["keyword"] == "const"}
    assert on_const == {}, on_const


def test_every_portable_document_is_emitted_or_refused_by_name() -> None:
    """The epic's exit condition, asserted at run time against the BUNDLE'S OWN SIZE.

    The arithmetic alone is not the condition and has been green while it was false:
    two sets whose sizes sum correctly can still both miss a document and double-count
    another.  So this asserts the PARTITION -- total and disjoint, by name -- and it
    derives the population from ``bundle.portable`` rather than restating a count.
    A literal here (it read ``1054``) stops being the bundle's size the moment the
    bundle changes, and then the assertion says only that the number is still that
    number.

    Each refusal additionally names its pointer and the keyword it refused on, which
    is the rest of the condition: a document is accounted for by NAME, POINTER and
    KEYWORD, never by a tally.
    """
    portable = set(bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, sorted(portable))
    emitted, refused = set(out.emitted), set(out.refusals)

    assert portable, "empty population: the assertion below would pass vacuously"
    assert emitted | refused == portable, {
        "neither emitted nor refused": sorted(portable - (emitted | refused)),
        "accounted for but not portable": sorted((emitted | refused) - portable),
    }
    assert emitted & refused == set(), sorted(emitted & refused)
    assert len(emitted) + len(refused) == len(portable)

    unnamed = {
        d: r for d, r in out.refusals.items() if not r.get("keyword") or r.get("pointer") is None
    }
    assert unnamed == {}, unnamed


def test_a_refusal_that_is_a_verdict_is_counted_apart_from_one_that_is_pending() -> None:
    """The exit condition is ``emitted + VERDICTS``, and it is not ``emitted + refused``.

    ``test_every_portable_document_is_emitted_or_refused_by_name`` proves the
    partition is total and disjoint.  It cannot tell a refusal apart from a
    placeholder, and ``emitted + refused == 1054`` is green while nothing does.
    Measured here by the producers' own constants: of 380 refusals, **48** say
    "a later D2 row does", **1** waits on one of those through a ``$ref``, and
    **331** name a keyword this emitter will not lower.  So the exit condition
    stands at 674 + 331 = **1005 of 1054**, with 49 pending.

    A REGEX OVER THE DETAIL STRING GAVE 404 / 41 / 31, AND ALL THREE WERE WRONG.
    It matched ``"D2 row"`` inside the VERDICT sentence "draft-07 defines no such
    keyword, so no D2 row lowers it and none is scheduled", reclassifying 268
    verdicts as deferrals and making the project look 268 documents further from
    its exit than it is.  That is exactly why this reads the constants and never
    the text.

    Each kind is recognised by the CONSTANT ITS PRODUCER EMITS
    (``refusal.DEFERRED_TO_A_LATER_ROW``, ``refusal.UNRESOLVED_TARGET``), not by a
    spelling this test invents, so a reworded message moves the constant and this
    test with it rather than silently reclassifying 404 documents as verdicts.

    The two pending counts are pinned SHRINK-ONLY and the accounted-for count
    GROW-ONLY.  A new row converts deferrals into emissions, so all three move in
    one direction; any other movement is a regression and reddens here.
    """
    portable = bundle.portable(BUNDLE)
    out = emit.emit(BUNDLE, portable)

    deferred = {d: r for d, r in out.refusals.items() if r["detail"] == refusal_module.DEFERRED_TO_A_LATER_ROW}
    transitive = {
        d: r
        for d, r in out.refusals.items()
        if d not in deferred and refusal_module.UNRESOLVED_TARGET in r["detail"]
    }
    verdicts = {d: r for d, r in out.refusals.items() if refusal_module.is_a_verdict(r["detail"])}

    # The FOURTH kind, and the reason the partition below has four terms: a refusal
    # reading ``its target X is refused: <X's own sentence>`` is pending or final
    # according to X, not according to itself.  ``is_a_verdict`` resolves that chain,
    # so these are the chained refusals it resolved to PENDING -- in no other bucket.
    chained_pending = {
        d: r
        for d, r in out.refusals.items()
        if d not in deferred
        and d not in transitive
        and d not in verdicts
    }

    assert out.refusals, "no refusals: every assertion below would pass vacuously"
    assert len(deferred) + len(transitive) + len(chained_pending) + len(verdicts) == len(
        out.refusals
    ), {
        "deferred": len(deferred),
        "transitive": len(transitive),
        "chained_pending": len(chained_pending),
        "verdicts": len(verdicts),
        "refusals": len(out.refusals),
    }
    assert set(deferred) & set(verdicts) == set()
    assert set(transitive) & set(verdicts) == set()
    assert set(chained_pending) & set(verdicts) == set()
    # **The chained KIND must not be empty, and it is no longer the PENDING bucket that
    # carries it.**  This read ``assert chained_pending``, because a term asserting that
    # a kind which demonstrably exists has no members is how the bug it covers hid.
    # ``salesagent-j3k2l.26`` emptied that bucket legitimately -- every chained refusal
    # now resolves to a verdict -- so the non-emptiness moves onto the thing that must
    # stay graded, which is ``is_a_verdict`` RESOLVING a chain rather than reading its
    # outer sentence.  Measured on this tree: **171 refusals quote a target's refusal,
    # all 171 resolve to VERDICT, and the chains run to depth 5** (121 at depth 1, 39 at
    # 2, 6 at 3, 3 at 4, 2 at 5), so the recursion is exercised by 171 documents and the
    # bug that read only the outer sentence would still redden the ``accounted`` pin
    # below by 171.  The PENDING bucket is pinned at 0 with the other two.
    chained = {
        d: r
        for d, r in out.refusals.items()
        if refusal_module.CHAINED_TO_A_REFUSED_TARGET in r["detail"]
        and r["detail"].startswith("its target ")
    }
    assert len(chained) >= 171, len(chained)
    assert set(chained) - set(verdicts) == set(chained_pending), "a chain is in one bucket"
    assert max(r["detail"].count(refusal_module.CHAINED_TO_A_REFUSED_TARGET) for r in chained.values()) >= 5, (
        "no chain deeper than one link: the recursion in is_a_verdict grades nothing"
    )

    # Shrink-only: a row lands, deferrals become emissions, these fall.
    #
    # **102 -> 48 and 951 -> 1005, moved by `salesagent-j3k2l.22`.**  The four keywords
    # that bead owns -- `not` 22, `dependencies` 10, `minProperties` 7, `maxProperties`
    # 5, which is 44 of the 102 -- are gone from the deferred set ENTIRELY, and 10 more
    # deferrals on other keywords cleared with them (a key `pattern` became a verdict
    # for 2, a `maxLength` for 3, and 5 cleared through a reference to a document that
    # now emits).  Of the 44: **3 emit**, **29 became verdicts**, and **12 moved to
    # another row's keyword or cleared transitively**.
    #
    # The two halves it took, both measured rather than designed: D6's rules reach the
    # composing row and the union row (the rule mechanism was complete and only the
    # object row consulted it), and a mapping's key COUNT is an annotation rather than a
    # rule, because `PropertyCount` reads `__pydantic_fields_set__` and a mapping is a
    # `dict` with no fields.
    #
    # Both pins are set to the value MEASURED on this tree rather than left loose, and
    # both were fire-probed one step tighter (`<= 47` and `>= 1006`) so they are known to
    # grade: a loose pin is a ratchet that grades nothing.
    # **CORRECTED: 1005 WAS OVERSTATED BY 30 AND 48 UNDERSTATED BY 31.**  Reading only
    # a chained refusal's OUTER sentence called all 170 of them verdicts, so the figures
    # this test asserted were wrong on every tree the epic has reported -- the deltas
    # between rows were right and the absolutes were not.  Measured on this tree with
    # ``is_a_verdict`` resolving the chain:
    #
    #     accounted  1005 -> 975      pending  48 -> 79
    #
    # which two independent instruments agree on: the function here, and a separate
    # walk that resolved every chain to its root (301 verdict, 78 deferred, 1
    # transitive).
    #
    # **48 -> 0, 30 -> 0 and 975 -> 1053, moved by `salesagent-j3k2l.26`.**  All 48 of
    # the deferred set were that bead's, and they were SIX mechanisms rather than the
    # one its title names.  Partitioned by WHICH ARM of the walk refused -- which is
    # what says whether a lowering exists to be written -- and not by the keyword tally:
    #
    #      7  uniqueItems on an array no class holds     ->  0 emit,  7 verdict
    #     32  a combinator of SHAPES at a nested pointer ->  8 emit, 24 verdict
    #      1  a combinator beside an allOf (composing)   ->  0 emit,  1 verdict
    #      5  contains on an array                       ->  2 emit,  3 verdict
    #      2  an enum on a union BRANCH                  ->  0 emit,  2 verdict
    #      1  a composing ARRAY, refused on items        ->  0 emit,  1 verdict
    #     48                                                10 emit, 38 verdict
    #
    # The row's whole gain is 12 documents: those 10, plus 2 of the 30 chained-pending
    # refusals that cleared into emissions.  The other 28 chained-pending refusals became
    # verdicts, because every target they chain onto is now a verdict or an emission.
    #
    # `ROWS` stayed SIX and `codegen/bundle.py` was not touched: 4 of the 48 sat at a
    # root, all 4 on `uniqueItems` at a root ARRAY, a kind `bundle.is_container_root`
    # already claims, and 0 of the 32 deferred nested combinator NODES sit at a root --
    # so no root selector sees one and a row would have claimed none.  Asked of the
    # DOCUMENT instead the answer is 2 and 14 (`union_root`, `composes_at_the_root`),
    # which is why the measurement is of the position.
    #
    # All four pins are set to the value MEASURED on this tree and each was fire-probed
    # one step tighter (`deferred <= -1` is not expressible, so the probe was
    # `len(deferred) < 0`; `transitive <= 0`, `chained_pending <= -1` likewise, and
    # `accounted >= 1054`), so each is known to grade rather than to sit loose.
    assert len(deferred) <= 0, len(deferred)
    assert len(transitive) <= 1, len(transitive)
    assert len(chained_pending) <= 0, len(chained_pending)

    # Grow-only: what the exit condition actually counts.
    accounted = len(out.emitted) + len(verdicts)
    assert accounted >= 1053, (accounted, len(out.emitted), len(verdicts))

    # And the gap between the two readings, stated so it cannot be read as closed.
    pending = len(deferred) + len(transitive) + len(chained_pending)
    assert accounted + pending == len(portable), (accounted, pending, len(portable))


def test_the_document_type_word_is_not_restated_beside_the_literal() -> None:
    """Measured on the pinned compiler, because the comparison is SYMMETRIC.

    A one-member ``Literal`` renders ``const`` AND the type word of its own accord --
    not a one-member ``enum``, and not the ``const`` alone -- so there is nothing for
    the row to restate and restating it is what would add a fact.  Asserted against
    pydantic here rather than assumed, because which of the three it renders is a
    function of the version and the whole admission below rests on it.

    The 832 TYPELESS const nodes are then the only place the model states a fact the
    document does not, and ``harness._entails_type`` already derives that one from the
    document's own ``const``.  Both halves are asserted: the derivation fires at every
    one of them, and it is gated on the VALUE rather than on the keyword -- a model
    claiming the wrong type over a ``const`` still reddens.
    """
    from codegen.harness import _entails_type

    assert TypeAdapter(Literal["x"]).json_schema() == {"const": "x", "type": "string"}
    assert TypeAdapter(Literal[3]).json_schema() == {"const": 3, "type": "integer"}
    assert TypeAdapter(Literal[True]).json_schema() == {"const": True, "type": "boolean"}

    typeless = [(d, p, n) for d, p, n in _const_nodes() if "type" not in n]
    assert len(typeless) == 832, len(typeless)

    # the derivation fires for every one of them, read off the DOCUMENT
    for document, pointer, node in typeless:
        rendered = TypeAdapter(Literal[node["const"]]).json_schema()["type"]
        assert _entails_type(node, rendered) is True, (document, pointer, rendered)

    # and it is the VALUE gate doing the work: with the gate dropped the rule would
    # admit a model claiming any type at all, which is what this asserts it does not.
    assert _entails_type({"const": "x"}, "integer") is False
    assert _entails_type({"const": True}, "integer") is False
    narrower = compare_schema(
        {"type": "object", "properties": {"k": {"const": "x"}}, "required": ["k"]},
        TypeAdapter(Annotated[int, Field(ge=0)]),
    )
    assert narrower.outcome != "pass", narrower

    # In its OWN document the resolver leaves a const node whole, unlike an enum
    # node -- so the ``description`` and the ``type`` are still there to compare.
    node = bundle.resolved(BUNDLE, "collection/collection-list-changed-webhook.json")
    event = node["properties"]["event"]
    assert event["const"] == "collection_list_changed"
    assert event["type"] == "string"
    assert event["description"]


def test_a_const_node_inlined_through_a_ref_loses_its_annotations() -> None:
    """The one hand-written comparison row this step adds, and why it is one row.

    ``canonicalish`` reduces a node whose value set is FINITE to that set alone and
    drops every annotation at it.  That is already folded out for an ``enum`` node
    (``harness._narrows_nothing``'s third bullet); a ``const`` is a ONE-MEMBER enum
    and gets the same rewrite -- but only when the node is INLINED through a
    ``$ref``, which is why the test above sees a whole node and this one does not.

    Both halves of the drop are measured here, and they are decided in two
    different places on purpose: the ``type`` half by ``_entails_type``'s existing
    ``const`` arm (a DERIVATION from the document's own value), the ``description``
    half by the new row.  The row is gated on the document stating a ``const`` at
    that node, and the gate is probed by asking the rule about a node that states
    none.
    """
    from codegen.harness import _narrows_nothing

    # the resolver, measured both ways round on the live pair
    own = bundle.resolved(BUNDLE, "core/agent-encryption-key.json")["properties"]["kty"]
    assert own["const"] == "OKP"
    assert own["type"] == "string"
    assert own["description"]
    through = bundle.resolved(BUNDLE, "core/authorized-agent-base.json")
    inlined = through["properties"]["encryption_keys"]["items"]["properties"]["kty"]
    assert inlined == {"const": "OKP"}, inlined

    # the row fires, and the gate is what makes it fire
    assert _narrows_nothing("description", "any text", {"const": "OKP"}) is True
    assert _narrows_nothing("description", "any text", {"type": "string"}) is False
    assert _narrows_nothing("description", "any text", {}) is False
    # it excuses the DESCRIPTION and nothing else at the same node
    assert _narrows_nothing("default", "OKP", {"const": "OKP"}) is False
    assert _narrows_nothing("minLength", 1, {"const": "OKP"}) is False
    # and the type half is still the derivation's, not this row's
    assert _narrows_nothing("type", "string", {"const": "OKP"}) is True
    assert _narrows_nothing("type", "integer", {"const": "OKP"}) is False

    # the other direction is untouched: a model that DROPS the document's own
    # description still reddens, which is the defect that matters
    dropped = compare_schema(
        {
            "type": "object",
            "properties": {"k": {"const": "OKP", "description": "d"}},
            "required": ["k"],
            "additionalProperties": False,
        },
        _constructed(
            {
                "title": "NoDoc",
                "type": "object",
                "additionalProperties": False,
                "properties": {"k": {"type": "string", "const": "OKP"}},
                "required": ["k"],
            }
        )[0],
    )
    assert dropped.outcome == "model_drops_a_fact", dropped
    assert any("description" in m for m in dropped.missing), dropped.missing


def test_the_const_row_has_exactly_one_lowering() -> None:
    """DRY, as a structural claim rather than as a reading.

    ``lower.union._literal`` was D2's ``const`` row scoped to one branch property,
    written there because nothing claimed the keyword in full.  This claims it in
    full, so the second copy is gone and so is the ``decided=`` plumbing that existed
    for its one caller -- a keyword with two lowerings is two places for the refusal
    set and the rendered annotation to disagree, and they did disagree: the dot
    mangling above was in one of them.
    """
    assert not hasattr(lower_union, "_literal")
    assert "decided" not in inspect.signature(compiler.fields).parameters
    assert "decided" not in inspect.signature(compiler.lower_object).parameters
    # union still NAMES the keyword, and only in its branch screen: that row is an
    # attribution row (a bare const branch is a scalar branch) and not a lowering.
    # Asserted by resolving the name rather than by grepping for the word, which
    # "constrains" would match: the one place a Literal can be BUILT is the row.
    assert "const" in lower_union.BRANCH_HANDLED
    builds = [
        name
        for name, module in (("compiler", compiler), ("union", lower_union), ("const", lower_const))
        for node in ast.walk(ast.parse(inspect.getsource(module)))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Type"
        and any(k.arg == "literals" for k in node.keywords)
    ]
    assert builds == ["const"], builds
    # and the one document it attributes refuses on its own keyword, not on a deferral
    r = emit.emit(BUNDLE, ["core/start-timing.json"]).refusals["core/start-timing.json"]
    assert (r["keyword"], r["pointer"]) == ("type", "/oneOf/0"), r
    assert "a branch of type 'string' is step 6" in r["detail"], r
