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
import collections
import functools
import importlib
import importlib.util
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
from codegen.lower import enum as lower_enum
from codegen.lower import union as lower_union
from codegen.refusal import Refusal
from codegen.harness import (
    AcceptsResult,
    check_accepts,
    check_liveness,
    ComparisonResult,
    LivenessResult,
    Pair,
    PairReport,
    _closed,  # noqa: PLC2701 -- the harness's own reading of a closed additionalProperties
    _composed,  # noqa: PLC2701 -- and its own folding of an allOf conjunct's facts
    check_pair,
    compare_schema,
    conforms,
    refusing_payload,
    violated_keywords,
)
from codegen.lower import rules

from nodeset import claimed, partitions, ratchet

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

    **A class is taken ONCE per defining module, however many names that module
    binds it under, and the ``__module__`` filter does NOT cover this.**  That filter
    answers "did this module define the class", which is a question about the
    IMPORTING module; D3's content dedup gives one class a name at every position the
    node occupies (``emit.bind_the_same_node``), and those names are in the DEFINING
    module, so ``vars(module)`` yields the same class object two or three times.
    Measured rather than reasoned: with the aliases emitted and this loop keyed on
    names, the pair count went 1,079 -> 1,085 -- six extra, which is exactly the 6 of
    the 10 collapsed nodes that are classes (the other 4 are enumerations, which carry
    no ``__adcp_schema__`` and were never pairs) -- and 5 refs were graded twice or
    three times, ``creative/preview-render.json#/oneOf/0/properties/dimensions`` among
    them.  A pair is one class against one schema, so a second name for it is not a
    second pair.

    **And 1,085 was the stale pin, so the naive reading passed.**  ``PAIRS_PIN`` was
    1085 before this row shrank the class count by 6, so grading 6 pairs twice landed
    back on the number the suite expected and nothing reddened.  The dedup check below
    is what catches it from the other side: it asserts that every name in a content
    group binds ONE object.
    """
    import adcp.types._schemas as pkg

    out: list[Graded] = []
    for info in sorted(pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."), key=lambda i: i.name):
        module = importlib.import_module(info.name)
        taken: set[int] = set()  # by IDENTITY: one class, one pair, whatever it is called
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, AdCPBaseModel)
                and "__adcp_schema__" in value.__dict__
                and value.__module__ == info.name
                and id(value) not in taken
            ):
                taken.add(id(value))
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

    ``ref`` is the same ``SchemaRef`` ``name`` is spelled from, and it is what
    ``codegen.dump_exemptions`` matches a position against.  Supplied here rather
    than parsed back out of ``name``, and not read off ``model`` -- D2's
    root-scalar row is graded as an alias, whose ``__adcp_schema__`` is on its
    module and not on the model.
    """
    return Pair(
        name=f"{g.ref.document}{g.ref.pointer}",
        schema=schema_at(g.ref),
        model=g.model,
        accept=g.accept,
        document=schema_at(SchemaRef(g.ref.document, "#")),
        ref=g.ref,
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
    """A verdict read off a set of nodes nobody named is a verdict over however many
    documents there turned out to be, including none.

    **No selector's SIZE is asserted here, and that is the correction.**  A size is one
    bundle version's reading of a set every emitting row moves: a row that takes a
    document from one row's ground to another's moves two of these totals at once while
    leaving untouched the thing the check exists for.  Section 8 asks for the set, so
    the set is what is asserted:

    * each selector names a NON-EMPTY set drawn from the bundle's own portable set, so
      no assertion over one of them holds vacuously;
    * ``population()`` is EXACTLY the union of the seven selectors, derived here rather
      than restated, so a selector that stops contributing to the denominator reddens;
    * the overlap is asserted as the FACT it is -- the union is strictly smaller than
      the sum of the parts, so a reader cannot add the selectors up -- rather than as
      one version's count of each intersection;
    * the two small selectors are named member by member, because a set of names unions
      with another row's addition where a total collides with it;
    * every selector's anchor document, by name.
    """
    whole = claimed("bundle.portable", bundle.portable(BUNDLE))
    selectors = {
        "leaves": claimed("leaves", leaves(), inside=whole),
        "referencing": claimed("referencing", referencing(), inside=whole),
        "enums": claimed("enums", enums(), inside=whole),
        # ``composes_at_the_root`` reads "a union beside the allOf" through
        # ``union_root``, so a root carrying ``allOf`` beside a PRESENCE-ONLY ``anyOf``
        # is step 4's ground rather than nobody's.
        "composing": claimed("composing", composing(), inside=whole),
        # ``union_root`` does NOT yield a root whose combinator holds ``required``
        # GROUPS: those are rules and not unions, and they are step 7's (see
        # ``test_step_sevens_population_reaches_the_object_row_and_no_other``).
        "union_roots": claimed("union_roots", union_roots(), inside=whole),
        "container_roots": claimed("container_roots", container_roots(), inside=whole),
        "object_rules": claimed("object_rules", object_rules(), inside=whole),
    }

    # The denominator is the union of the seven and nothing else.  Asserted against the
    # seven named sets rather than against a total, so dropping a selector from
    # ``population`` reddens here with the dropped documents named.
    assert claimed("population", population(), inside=whole) == set().union(*selectors.values())
    assert set(population()) < whole, "the step's population is not a part of the bundle"
    # The selectors OVERLAP by design -- a leaf object with an inline enum is step 1's
    # and step 3's alike -- and that is the fact, not any one intersection's size: the
    # union is strictly smaller than the sum, so the selectors cannot be added up.
    assert len(population()) < sum(len(s) for s in selectors.values())
    assert selectors["leaves"] & selectors["enums"]
    assert selectors["referencing"] & selectors["enums"]

    assert PAGINATION in selectors["leaves"]
    assert "error-details/creative-revision-content-mismatch.json" in selectors["referencing"]
    assert "enums/match-type.json" in selectors["enums"]
    assert "core/signal-id.json" in selectors["union_roots"]
    # 0 union roots carry BOTH keywords, so the keyword the lowering reads is unambiguous
    # for every document the selector claims.  The set it ranges over is named
    # non-empty above, so this empty part is empty over a real set of nodes.
    assert [
        d
        for d in union_roots()
        if {"oneOf", "anyOf"} <= set(bundle.read(BUNDLE, d))
        and all(isinstance(bundle.read(BUNDLE, d)[k], list) for k in ("oneOf", "anyOf"))
    ] == []
    # ``is_container_root`` excludes a root that declares a union as well, because most
    # of the bundle's mapping roots do and the union row owns them.  Named rather than
    # counted: which documents the container row claims is the fact a later row moves,
    # and a name says which one moved where a count says only that one did.
    assert selectors["container_roots"] == {
        "core/acceptance-policy-profile-ids.json",
        "core/context.json",
        "core/creative-assets.json",
        "core/ext.json",
        "core/forecast-point-dimensions.json",
        "core/product-change-map.json",
        "core/reporting-verification-profile-set.json",
        "media-buy/product-fields.json",
        "media-buy/product-refinement.json",
    }
    # Step 6's population only GROWS the named set, which is what makes the earlier
    # steps structurally safe rather than re-measured: a container root is neither a
    # leaf object nor a referencing one, so no document stops being named.
    assert not selectors["container_roots"] & (selectors["leaves"] | selectors["referencing"])
    assert selectors["object_rules"] == {
        "core/budget-range.json",
        "core/demographic-age-range.json",
        "core/forecast-range.json",
        "core/webhook-challenge-response.json",
        "media-buy/proposal-budget-constraint.json",
    }


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
    """Step 1's own document, through every check the harness has.

    The DENOMINATORS are asserted and not just the verdicts: a green mark without
    the count beside it says nothing, because a pair no instance reached reports no
    failure either.  There are two of them now and they are different questions --
    how many instances were drawn, constructed and round-tripped, and which fact the
    one refused payload broke.
    """
    rep = check_pair(pair_of(pagination()), accepts_examples=25)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.accepts.examples == 25, rep.accepts.examples
    assert rep.graded_instances == 25, rep.graded_instances  # every one dumped back out
    assert rep.liveness.outcome == "pass", (rep.liveness.how, rep.liveness.detail)
    # The document states ``additionalProperties: false`` and demands no key, so the
    # payload is a whole-instance replacement and the document bites on ``type``.
    assert rep.liveness.how == "replaces the instance with None", rep.liveness.how
    assert rep.liveness.violated == ("type",), rep.liveness.violated
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
    indistinguishable from a faithful model on every check but one: the accepts
    check passes over the SAME 25 instances, each one dumps back out to something
    the document still admits, and the refused payload is refused by both.

    **The refused payload is refused by the WIDE model too, and section 6 says that
    is the whole point of keeping exactly one.**  Pydantic is DELIBERATELY less
    strict than the schema -- D4 gives the schema the acceptance decision -- so a
    payload the schema refuses measures nothing about the class on either route:
    ``model_validate`` may accept it by design, and ``strict_validate`` refuses it
    because the document answered.  What the one refusal proves is LIVENESS, that
    this class's schema half is connected and its ref resolves to its document, and
    it proves that for the wide class exactly as for the faithful one.  The 27,791
    per-keyword sites this replaced were proving the same thing 27,791 times.

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
        accepts_examples=25,
    )
    # Both at the same explicit depth: the point of this test is that the two
    # denominators are IDENTICAL, so neither may depend on check_pair's default.
    faithful = check_pair(pair_of(pagination()), accepts_examples=25)

    assert wide.accepts.outcome == faithful.accepts.outcome == "pass"
    assert wide.liveness.outcome == faithful.liveness.outcome == "pass"
    assert wide.liveness.how == faithful.liveness.how
    assert wide.graded_instances == faithful.graded_instances == 25

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


def test_a_zero_denominator_is_not_reportable_as_a_pass() -> None:
    """The other half of the rule, and it needs its own fixture.

    The rule is right -- a pair no instance reached is graded by nothing -- and the
    test above shows it is not what catches a wide model.  So it is graded here on
    the thing that does produce a zero denominator: an entry point that refuses
    with an exception that is not pydantic's, which is what the specification's own
    probe did.  Nothing round-trips, the denominator is 0, and the pair's verdict
    names the entry point rather than passing.

    **Both halves of the harness are graded here, because a foreign exception can
    arrive at either.**  The accepts check offers an instance the document admits,
    and the liveness check offers one it refuses; an entry point raising something the
    caller cannot catch at either of them used to read as a pair with nothing wrong.
    ``check_liveness`` is asserted directly with an entry point of its own, because
    one that refuses a VALID instance and one that refuses an invalid one with the
    wrong exception are two different wirings.
    """
    schema = schema_at(SchemaRef(PAGINATION, "#"))
    model = pagination().model

    def foreign_error(payload: Any) -> Any:
        # Refuses with jsonschema's error and not pydantic's, on an instance the
        # document ADMITS -- a string schema against this document's object root.
        jsonschema.validate(payload, {"type": "string"})
        return model.model_validate(payload)

    rep = check_pair(Pair(name="foreign", schema=schema, model=model, accept=foreign_error))
    assert rep.accepts.outcome == "model_error", rep.accepts.detail
    assert "ValidationError" in rep.accepts.detail
    assert rep.graded_instances == 0
    assert rep.outcome == "accepts:model_error"

    # ... and the same exception on the liveness check's path.
    def foreign_refusal(_payload: Any) -> Any:
        raise jsonschema.ValidationError("not pydantic's error")

    live = check_liveness(schema, foreign_refusal, {"max_results": 1})
    assert live.how == "replaces the instance with None", live.how
    assert live.outcome == "model_error", (live.outcome, live.detail)
    assert live.detail.startswith("ValidationError"), live.detail
    # And the real entry point IS the refusal, over the same payload.
    assert check_liveness(schema, model.strict_validate, {"max_results": 1}).outcome == "pass"


def test_a_zero_denominator_verdict_is_never_pass() -> None:
    """The rule itself, on a report built to have a zero denominator.

    The test above reaches the zero through an entry point that errors, so the
    verdict it gets is ``accepts:model_error`` and the branch that says "nothing
    reached the model and nothing went wrong" is not exercised by it.  No document
    in this population produces that with every check healthy, so it is graded here
    on a report rather than on a pipeline, which is the right level: the rule is a
    property of ``PairReport``.

    Asserted to be something other than ``pass``, so deleting the branch fails this
    test rather than silently turning a pair nothing reached into a green mark.
    """
    fine = ComparisonResult(compared=7)
    refused = LivenessResult(how="replaces the instance with None", outcome="pass")

    nothing_round_tripped = PairReport(
        name="n",
        accepts=AcceptsResult(examples=25, outcome="pass", round_tripped=0),
        liveness=refused,
        comparison=fine,
    )
    assert nothing_round_tripped.graded_instances == 0
    assert nothing_round_tripped.outcome == "no_accepts_check_evidence"

    # ... and one instance reaching the model and coming back out is the whole
    # difference.
    reached = PairReport(
        name="r",
        accepts=AcceptsResult(examples=25, outcome="pass", round_tripped=1),
        liveness=refused,
        comparison=fine,
    )
    assert reached.graded_instances == 1
    assert reached.outcome == "pass"


def test_no_instrument_is_admitted_only_where_a_measured_position_explains_it() -> None:
    """The admissibility rule, on reports built to have each answer.

    ``no_instrument`` is the harness's one admitted non-pass outcome, and what it is
    admitted FOR is a position whose ``format`` strategy cannot satisfy the ``pattern``
    beside it -- ``salesagent-j3k2l.10``.  72 of the bundle's 73 format-beside-pattern
    positions draw, so "this document states the two keywords somewhere" does not
    identify the shape: it would speak for a generator failure from any cause at all.

    Graded here on a report rather than on a pipeline, for ``test_a_zero_denominator_
    verdict_is_never_pass``'s own reason -- the rule is a property of ``PairReport``
    and no document in this population produces the refusing cell.  The population
    side is ``test_no_instrument_is_the_designed_outcome_for_a_measured_shape``.
    """
    fine = ComparisonResult(compared=7)
    refused = LivenessResult(how="replaces the instance with None", outcome="pass")
    errored = AcceptsResult(examples=1, outcome="strategy_error", detail="Unsatisfiable: 9 of 9")

    # A generator failure a measured position explains: the admitted exit, and the
    # cause carries the position and hypothesis's own reason.
    explained = PairReport(
        name="e",
        accepts=errored,
        liveness=refused,
        comparison=fine,
        accepts_undrawable=("/p: format 'uri' beside pattern '^https://x/' [Unsatisfiable: 9]",),
    )
    assert explained.outcome == "no_instrument"
    assert explained.no_instrument == (
        "accepts: /p: format 'uri' beside pattern '^https://x/' [Unsatisfiable: 9];"
        " Unsatisfiable: 9 of 9",
    )

    # ... and the same generator failure with NOTHING explaining it is a verdict on
    # the pair.  Deleting either half of the rule fails here.
    unexplained = PairReport(name="u", accepts=errored, liveness=refused, comparison=fine)
    assert unexplained.no_instrument == ()
    assert unexplained.outcome == "accepts:strategy_error"


#: **The harness result over the whole population, as pins.**  Every one of these
#: was MEASURED on this tree after the section-6 rebuild; none is carried from the
#: per-keyword harness, because three of that one's figures no longer exist to
#: re-point -- the step-site count, the refuses-check instance total, and the
#: ``no_constraint_to_step`` partition.
#:
#: Each is an EQUALITY.  The old refuses-check instance total was a floor, because
#: it counted hypothesis draws across 27,791 step sites and seven readings of it on
#: indistinguishable trees spread over 0.4%.  There is one draw per pair now and the
#: schema comparison walks a document, so every figure here is a function of
#: (bundle, emitted tree) and reproduces exactly.
#: 1055 -> 1085 at ``salesagent-j3k2l.28``: the three refusals section 6's "every fold
#: applies to both sides" names are gone, so 14 more documents emit and bring their own
#: nested pairs.  Re-measured, not derived from the document count: a document carries
#: between one and a dozen pairs.
#: 1085 -> 1079 at ``salesagent-j3k2l.38``: D3's content dedup collapses 10 nodes, and
#: the 6 of them that are CLASSES are 6 pairs that no longer exist.  The other 4 are
#: enumerations, which carry no ``__adcp_schema__`` and were never pairs -- which is why
#: this moves by 6 against that row's 10 and the two numbers are different senses.
#: 1079 -> 1090 at ``salesagent-j3k2l.21``: eleven more documents emit, each at
#: least one pair, and the StrEnum that row removed from
#: ``error-details/accessibility-violation.json`` took no pair with it -- an
#: enumeration carries no ``__adcp_schema__`` and was never one.
#: A FLOOR and not an equality, and the direction is the reason.  Every emitting row
#: ADDS pairs -- a document that lowers brings its own nested ones -- so an equality
#: here is red on two branches at once with two different correct values, which is
#: exactly the collision ``salesagent-j3k2l.47`` converted.  What a floor still refuses
#: is the failure this number exists for: a class that stopped carrying
#: ``__adcp_schema__``, or a document that stopped being emitted, takes the count DOWN.
#: The history of the equality, kept because each move names a cause: 1055 -> 1085
#: (.28, three refusals gone), 1085 -> 1079 (.38, D3's dedup collapses 6 class pairs),
#: 1079 -> 1090 (.21, eleven more documents emit).
PAIRS_FLOOR = 1090
#: **Every pair that is not ``pass``, BY NAME, and written once.**  Two tests read it:
#: the totals test derives its ``pass`` figure as the complement, and
#: ``test_the_non_pass_pairs_are_named_and_attributed`` asserts the membership and
#: attributes each one.  A count of five told the next reader nothing about which five
#: or why; a name says which, and two readings of one named set cannot drift apart the
#: way ``PAIRS_PIN`` and ``OUTCOME_PINS`` could.
#:
#: Two groups are GONE rather than smaller.  ``comparison:model_drops_a_fact`` was one
#: ``description`` each at an ``additionalProperties`` node, closed in the EMITTER by
#: ``salesagent-j3k2l.28``; ``accepts:model_dropped_a_fact``'s three pairs are EXEMPT
#: and the exemption is reported (``codegen.dump_exemptions``, and the ``exempt`` census
#: in the test named above).
NON_PASS_PAIRS: dict[str, list[str]] = {
    "no_instrument": [
        "core/reference-renderer.json#",
        "core/reference-renderer.json#/properties/provenance",
    ],
}
#: **PINNED AT ZERO ON PURPOSE AND BOTH ARE GREEN.**  Zero is the specification's
#: symmetric comparison -- a fact the model adds reddens and a fact it drops reddens --
#: and a zero does not collide between rows the way a census does.  It was pinned here
#: while ``MISSING_PIN`` was RED, because re-pointing a pin at the measurement is what
#: salesagent-j3k2l.28 said not to do; that row closed it.  The zeros are only
#: meaningful over a non-empty comparison, which the totals test asserts PER PAIR
#: rather than as a sum of ``compared``.
MISSING_PIN = 0
DIFFERS_PIN = 0
#: The pairs whose LIVENESS check has no payload, by name.  Written once and read by the
#: two tests that need it, so ``pass`` is the complement of a named set rather than an
#: arithmetic over two pins.  These are the same two pairs ``NON_PASS_PAIRS`` names and
#: the coincidence is not asserted: "the accepts check drew no instance" and "the pair's
#: verdict is ``no_instrument``" are two statements about one cause, and a row that
#: separates them should redden in one place and not both.
#: Section 8's one-way invariant, as a floor: "a step adds roots to
#: ``BranchDispatchMixin``; no step removes one."  38 before the alias dispatch, 38
#: after it, 38 after D2's Literal amendment -- and the reason it never moved is that
#: no row had yet added a base, not that an addition would be wrong.
UNION_BASE_FLOOR = 38
NO_PAYLOAD_PAIRS: tuple[str, ...] = (
    "core/reference-renderer.json#",
    "core/reference-renderer.json#/properties/provenance",
)


@functools.cache
def graded_reports() -> list[tuple[Graded, PairReport]]:
    """Every graded pair, graded ONCE.

    **One pass over the population, shared by the three tests that read a total.**
    Each of them used to grade all 1,055 pairs itself, so the suite made three
    passes and two of them were single indivisible pytest items -- xdist
    distributes BY TEST, so a test looping the population cannot be split and the
    other workers cannot help it.  Caching here makes the pole one pass instead of
    three; the per-pair test below stays parametrised, because that is the form
    xdist CAN spread.

    ``functools.cache`` and not a fixture, because ``graded()`` and ``pair_of``
    are module functions and the reports are a pure function of the emitted tree.
    """
    return [(g, check_pair(pair_of(g))) for g in graded()]


def test_a_refused_payload_is_derived_for_every_pair_an_instance_was_drawn_for() -> None:
    """``no_payload`` is the complement of the accepts check's draw, and nothing else.

    ``refusing_payload`` tries three perturbations of an accepted instance and screens
    every one against the DOCUMENT, so ``no_payload`` could in principle mean either of
    two things: the document admits all three shapes, or there was no accepted instance
    to perturb.  **Measured over the population, it only ever means the second.**  Every
    one of the 1,053 pairs the accepts check drew an instance for yielded a payload the
    document refuses, and the 2 that did not are exactly the 2 whose generator could not
    draw -- so the derivation reaches every pair it is given anything to work with.

    That is worth a test because the first reading of it was wrong, and it was mine: I
    expected ``core/context.json`` and ``core/ext.json``, the
    ``additionalProperties: true`` mapping roots, to refuse nothing.  They state
    ``type: object``, so the whole-instance replacement with ``None`` is refused and they
    are graded like everything else.  A document refusing NOTHING would have to state no
    root type at all, and this bundle has none.
    """
    reports = graded_reports()
    excused = sorted(
        f"{g.ref.document}{g.ref.pointer}" for g, r in reports if r.liveness.outcome == "no_payload"
    )
    assert excused == sorted(NO_PAYLOAD_PAIRS), excused
    # Read off the reports rather than off the list: each one is a pair whose accepts
    # check could not DRAW, and the liveness result says exactly that.
    for g, r in reports:
        if r.liveness.outcome == "no_payload":
            assert r.accepts.outcome == "strategy_error", (g.ref, r.accepts.outcome)
            assert r.liveness.detail == "the accepts check drew no instance", r.liveness.detail
            assert r.liveness.how == "", r.liveness.how
        else:
            assert r.liveness.how, (g.ref, r.liveness.outcome)
    # The two mapping roots this test's own premise got wrong, asserted the right way
    # round: they state a root type, so the replacement IS refused and they ARE graded.
    for name in ("core/context.json#", "core/ext.json#"):
        g = next(x for x in graded() if f"{x.ref.document}{x.ref.pointer}" == name)
        schema = schema_at(g.ref)
        assert schema.get("required", []) == [] and schema["type"] == "object", g.ref
        assert refusing_payload(schema, {}) == (None, "replaces the instance with None")
        rep = check_pair(pair_of(g))
        assert rep.outcome == "pass" and rep.liveness.outcome == "pass"
        assert rep.graded_instances > 0 and rep.comparison.compared > 0


def _grades_a_cause(cause: str, where: str = "") -> None:
    """A ``no_instrument`` cause has to be specific enough to ACT on.

    Graded by SHAPE and not by a sentence: the first cut asserted the substring
    ``"contradicted by"``, the gate fix reworded that half to ``"contradicts the
    step"``, and every undrawable pair then reddened on the wording while the pairs
    themselves were exactly as intended.  A test that pins prose grades the prose.

    Three obligations, each read off the structure:

    * WHICH check could not draw -- the entry names ``accepts``, and that is now the
      only check in this harness that draws at all;
    * WHERE -- the document's own format-beside-pattern positions, derived from the
      document because hypothesis raises over the whole schema and names no node;
    * WHY -- hypothesis's own exception name, which carries the filtered-draw count.
    """
    assert cause.startswith("accepts: "), (where, cause)
    assert "Unsatisfiable" in cause or "RecursionError" in cause, (where, cause)
    assert ": format " in cause, (where, cause)


@pytest.mark.parametrize("row", graded(), ids=lambda g: f"{g.ref.document}{g.ref.pointer}")
def test_every_class_passes_all_three_checks(row: Graded) -> None:
    """N: emitted AND graded green against the schema the class itself names.

    One verdict other than ``pass`` is allowed through, and it is asserted against
    its own evidence rather than taken on trust: ``no_instrument``, where the
    accepts check could not DRAW an instance, so the obstruction is ``hypothesis``
    and not the model -- asserted by requiring each cause to name a shape (a format
    beside a pattern) and not merely to exist.

    **The schema comparison is asserted for EVERY pair, including an undrawable
    one**, and that is what keeps the exit from being a hole: the comparison needs
    no generator, it runs on both of them, and it is the only check that separates a
    faithful model from a wide one.

    **Parametrised, and that is load-bearing for the suite's wall clock.** xdist
    distributes by TEST, so this is 1,055 work items that spread across the workers
    while the three tests reading a population TOTAL are one item each.
    """
    pair = pair_of(row)
    rep = check_pair(pair)
    assert rep.missing_formats == []
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.differs)
    if rep.accepts.outcome != "strategy_error":
        assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
        assert rep.graded_instances > 0, "nothing was constructed and dumped back out"
    assert rep.liveness.outcome in ("pass", "no_payload"), (rep.liveness.outcome, rep.liveness.how)
    if rep.outcome == "no_instrument":
        assert rep.no_instrument, rep.name
        for cause in rep.no_instrument:
            _grades_a_cause(cause)
    else:
        assert rep.outcome == "pass", rep.outcome


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


#: The three pointer segments a conditional is spelled with.  A node under one is a
#: CONDITION or a conditional narrowing, which D6 makes a rule on the nearest class and
#: which ``lower.rules`` declines where it narrows a value -- so nothing is lowered at
#: such a pointer and no type is selected there.  Same reading ``_base.SAME_INSTANCE``
#: excludes ``if`` for, and the one
#: ``test_the_assertion_is_inherited_down_a_chain_of_combinator_hops`` uses.
_CONDITIONAL_SEGMENTS = frozenset({"if", "then", "else"})


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
    #: The format sites the emitter never visits, by format: a position under a
    #: conditional.  Its own counter rather than a skip, so the exclusion is a figure.
    conditional: dict[str, int] = {}
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
            if any(seg in _CONDITIONAL_SEGMENTS for seg in pointer.split("/")):
                # **A position under a CONDITIONAL is not lowered at all, so no type
                # is selected there and asserting one would grade a mechanism this
                # pipeline does not have.**  D6 makes a conditional a RULE on the
                # nearest class and ``lower.rules`` declines a branch that narrows a
                # VALUE -- its module docstring records that ceiling on
                # ``core/canvas-constraint.json``'s ``if unit == "percent" then
                # x.maximum = 100``.  First reached when
                # ``sponsored-intelligence/si-ui-element.json`` emitted
                # (``salesagent-j3k2l.28``), whose ``/allOf/1/then`` states a
                # ``format: uri``.  COUNTED below rather than skipped silently, so the
                # exclusion has a size and a shrink in it is visible.
                conditional[fmt] = conditional.get(fmt, 0) + 1
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

    # WHICH formats the population reaches, as the set of format names, with every one
    # of them non-empty so no row of the table above is graded by a loop that met none
    # of it.  The per-format COUNT is not asserted: it is the number of positions one
    # emitted tree states a format at, and every row that makes a document emittable
    # moves two or three of these at once -- ``date-time`` went 190 -> 194 -> 196 and
    # ``uri`` 131 -> 133 -> 135 over two rows, each a correct move, neither predictable
    # from the other.
    assert set(seen) == {"date-time", "uri", "date", "email", "hostname"}, seen
    assert all(seen.values()), seen
    # The excluded population, named and sized -- and it is SIX sites, not the one
    # that reddened.  **The other five were passing by accident**, which is the finding:
    # the import assertion is MODULE-wide, so a conditional-position ``uri`` in a module
    # that also states one at a lowered pointer was satisfied by its neighbour's import.
    # ``si-ui-element.json``'s ``/allOf/1/then/properties/data/properties/url`` is the
    # one with no neighbour to carry it, so it is the one that showed when the document
    # emitted (``salesagent-j3k2l.28``).
    # The excluded set, named by its formats and asserted non-empty, for the same
    # reason: the finding is that a conditional position is excluded AT ALL and which
    # formats reach one, not how many sites there are in this tree.
    assert set(conditional) == {"uri", "date-time"}, conditional
    assert all(conditional.values()), conditional
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
    stated: set[tuple[SchemaRef, str]] = set()
    for g in graded():
        doc = schema_at(g.ref)
        emitted = _model_schema(g.model)
        for key, sub in (doc.get("properties") or {}).items():
            if not isinstance(sub.get("format"), str):
                continue
            mine = _rendered(emitted, key, g.model)
            assert mine.get("format") == sub["format"], (g.ref, key, mine)
            stated.add((g.ref, key))
    # The set of (pair, property) positions the loop graded, named and non-empty rather
    # than counted.  The count moved at every row that made a document emittable --
    # 326 -> 333 -> 334 over three of them -- and each move was a correct one, so an
    # equality here refuses the work it is supposed to be grading.  What it has to
    # refuse instead is a loop that graded nothing, which is what this says.
    claimed("graded properties that state a format", stated)


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

    rep = check_pair(pair_of(g))
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.comparison.outcome == "pass", (rep.comparison.missing, rep.comparison.added)


def test_the_harness_and_the_runtime_decide_a_format_the_same_way() -> None:
    """One schema, one verdict: the control and the refusal cannot disagree.

    The harness asks the ORIGINAL document which keyword bit
    (``violated_keywords``) and screens a candidate payload against it
    (``conforms``) before offering the payload to anything.
    ``strict_validate``'s schema half asks the same document.  If those two build
    validators with different vocabularies, the harness screens a payload in or
    out on the strength of a keyword the runtime cannot see -- so the harness
    passes the same ``FORMAT_CHECKER`` ``_refuse`` does, and this is what says so.

    Measured without it: the suite went fully green, because no check in the
    harness produces a ``format``-violating instance on its own -- the accepts
    check draws instances the document ADMITS and ``hypothesis_jsonschema``
    honours a format it knows, and ``refusing_payload`` perturbs requiredness and
    JSON type rather than a string's shape.  So the agreement has no instrument
    other than this one, and the violating instance is written here rather than
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
    claimed("patterns stated by a graded document", distinct)

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

    # The three buckets PARTITION the patterns the graded documents state, which is
    # what a census of each one was standing in for: the census moved with the emitted
    # population at every row that added a document, while the shape of the finding did
    # not move at all.  So the shape is what is asserted -- every pattern is in exactly
    # one bucket, each bucket is non-empty, and no pattern's SITES are lost on the way
    # into a bucket, which is the second denominator this check reports.
    partitions(distinct, no_build=no_build, diverges=diverges, agrees=agrees)
    claimed("patterns the default engine refuses to build", no_build)
    claimed("patterns the two engines disagree on", diverges)
    claimed("patterns the two engines agree on", agrees)
    assert sum(no_build.values()) + sum(diverges.values()) + sum(agrees.values()) == sum(
        distinct.values()
    ), (no_build, diverges, agrees)
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
    # ... and that set is non-empty, so the equality above is not two empty lists.
    assert [p for p in agrees if "$" in p], sorted(agrees)


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
    aliases = claimed("aliases the tree carries", [g.ref for g in graded() if not isinstance(g.model, type)])
    with_pattern: set[SchemaRef] = set()
    for g in graded():
        if isinstance(g.model, type):
            continue
        doc = schema_at(g.ref)
        pattern = doc.get("pattern")
        if not isinstance(pattern, str):
            continue
        with_pattern.add(g.ref)
        value = _matching(pattern)[0].rstrip("\n") + "\n"
        jsonschema.Draft7Validator(
            doc, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER
        ).validate(value)  # the document admits it
        assert g.accept(value) == value, (g.ref, value)  # and so does the alias
    # The set of aliases that state a pattern, named as a set and asserted non-empty
    # rather than counted: how MANY of them there are is a property of the emitted tree
    # that every row adding an alias moves, while "at least one alias was graded by the
    # loop above" is the thing that keeps the loop from passing over nothing.
    claimed("graded aliases that state a pattern", with_pattern, inside=aliases)


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


def test_the_harness_result_is_counted_over_the_whole_population() -> None:
    """One number for the harness, with its denominators, because a per-pair green
    mark does not add up to one and nobody can sum 1,055 of them by eye.

    **Every figure below was re-measured on this tree after the rebuild and none
    was carried forward.**  The harness grades one class against one schema now, so
    three of the old figures no longer exist to re-point: the step-site count, the
    refuses-check instance total, and the ``no_constraint_to_step`` partition.  What
    replaces the first two is ``graded_instances``, which counts instances DRAWN,
    CONSTRUCTED and DUMPED BACK OUT to something the document still admits -- one
    per pair at the default depth, so it is an equality and not a floor.

    Read off :func:`graded_reports`, which grades the population ONCE for the three
    tests that need a total.
    """
    pairs = {f"{g.ref.document}{g.ref.pointer}": r for g, r in graded_reports()}
    assert len(pairs) == len(graded_reports()), "two reports under one pair name"
    reports = list(pairs.values())
    claimed("graded pairs", pairs)
    ratchet(
        "graded pairs",
        len(reports),
        at_least=PAIRS_FLOOR,
        because="an emitting row only ADDS pairs; a drop means a class stopped carrying "
        "__adcp_schema__ or stopped being emitted, which is never this suite's intent",
    )

    # THE OUTCOME PARTITION, derived from the NAMED non-pass set rather than from a
    # second count of it: every pair is ``pass`` or is one of the pairs
    # ``NON_PASS_PAIRS`` names, the ``pass`` figure is the complement, and a pair
    # joining or leaving the group reddens with the DOCUMENT named instead of moving
    # two integers nobody can attribute.
    by_outcome = collections.Counter(r.outcome for r in reports)
    assert set(by_outcome) == {"pass"} | set(NON_PASS_PAIRS), dict(by_outcome)
    assert {k: n for k, n in by_outcome.items() if k != "pass"} == {
        k: len(v) for k, v in NON_PASS_PAIRS.items()
    }, dict(by_outcome)
    assert by_outcome["pass"] == len(reports) - sum(len(v) for v in NON_PASS_PAIRS.values())
    # One instance per pair at the default depth, so the round-tripped total is the
    # complement of the named non-pass set and not a number of its own: a pair whose
    # generator could not draw and a pair whose dump the document refused both
    # round-trip nothing.
    assert sum(r.graded_instances for r in reports) == len(reports) - sum(
        len(v) for v in NON_PASS_PAIRS.values()
    )

    # THE COMPARISON, graded by its own denominator PER PAIR rather than by a total.
    # The three zeros below are the specification's symmetric comparison and they are
    # free for any pair that compared nothing, so what has to be asserted is that no
    # pair compared nothing -- which is stronger than any sum of ``compared``, and does
    # not move when a row adds a document.
    assert [name for name, r in pairs.items() if r.comparison.compared == 0] == []
    # ``added`` is the other direction and its denominator is the MODEL's own facts,
    # which not every pair has -- an enumeration and an alias state none -- so this is
    # the named set of the pairs that do, asserted non-empty rather than summed.
    claimed(
        "pairs whose model states a fact of its own",
        {name for name, r in pairs.items() if r.comparison.model_facts},
        inside=set(pairs),
    )
    assert sum(len(r.comparison.added) for r in reports) == 0  # none of them narrows
    assert sum(len(r.comparison.missing) for r in reports) == MISSING_PIN
    assert sum(len(r.comparison.differs) for r in reports) == DIFFERS_PIN
    # D5's URL-type rows, the one category that excuses a fact the model does not state.
    # The claim is WHICH facts it excuses, so that is what is asserted: a URL type
    # renders ``minLength: 1`` and ``HttpUrl`` renders ``maxLength: 2083``, and the
    # bundle states one ``pattern`` on a ``format: uri`` node.  A total of them says
    # nothing about which keyword was excused, and it grows with every added document.
    excused = claimed(
        "facts excused as a URL type's own rendering",
        {line.split(": ", 1)[0].rsplit("/", 1)[1] for r in reports for line in r.comparison.url_typed},
    )
    assert excused == {"minLength", "maxLength", "pattern"}, sorted(excused)
    # The one refused payload per pair, partitioned BY NAME on the fact it broke.  A
    # partition and not three totals, because which perturbation bites is a property of
    # the DOCUMENT's own root shape: a pair moving between these groups is a fact worth
    # reading and a count cannot say which pair moved.
    how = collections.defaultdict(set)
    for name, r in pairs.items():
        how[r.liveness.how.split(" ")[0] or "no_payload"].add(name)
    partitions(pairs, **how)
    assert set(how) == {"drops", "replaces", "no_payload"}, sorted(how)
    for group in how.values():
        claimed("a liveness perturbation group", group, inside=set(pairs))


#: **The format-beside-pattern census over the bundle, and the undrawable population
#: inside it.**  Measured on the 1,054 portable documents of the 3.2 bundle by
#: ``harness.format_pattern_positions`` (the co-occurrence census, over each document's
#: own UNRESOLVED declarations) and by ``harness.undrawable_formats`` (the draw).
#:
#: The two figures are the whole of ``salesagent-j3k2l.10``'s decision and they are
#: deliberately far apart: 73 positions state the two keywords together and 72 of them
#: DRAW.  73 is section 6's own figure -- "the bundle states eight distinct patterns
#: across 73 of its 300 ``uri`` uses" -- read here off the harness rather than carried.
#: The four censuses that used to be pinned here -- positions, documents, shapes and
#: undrawable positions -- are REDUNDANT with the facts the test asserts as sets: the
#: format is ``uri`` at every position, the undrawable shape is exactly one and is named
#: with its pattern, and the one undrawable position is named with its document and
#: pointer.  A count of each added nothing those names do not say and went stale against
#: a bundle version instead.
#: The one position, by document and pointer, and the pattern that makes it undrawable.
UNDRAWABLE_POSITION = (
    "core/reference-renderer.json",
    "/properties/provenance/properties/source_repository",
)
UNDRAWABLE_PATTERN = "^https://github\\.com/"


def test_the_non_pass_pairs_are_named_and_attributed() -> None:
    """Every pair that is not ``pass``, by name, with what it is.

    **A census and not a tolerance.**  Nothing here excuses anything:
    ``test_every_class_passes_all_three_checks`` still reddens on all five of the
    first two groups, and this test exists so the failures are NAMED rather than
    counted -- a count of five tells the next reader nothing about which five or
    why, and the section-6 rebuild is the first thing to measure them.

    TWO groups now, and the attribution of each was measured rather than assumed.  The
    third was ``comparison:model_drops_a_fact`` -- one ``description`` each at an
    ``additionalProperties`` node, ``a2ui/component.json`` and ``a2ui/surface.json``,
    pre-existing at the base and proven so by ``compare_schema`` being byte-identical
    to ``7ffad8134``'s.  ``salesagent-j3k2l.28`` closed it in the EMITTER, which is
    what §6 says happens where the comparison reports a ``description``: an annotation
    on a container's CONTENTS had no carrier, and ``containers._contents`` now names
    such a node.  The group is gone rather than smaller.

    ``accepts:model_dropped_a_fact`` is gone too, and NOT because the dump half stopped
    reading what a class did with a value.  Its three pairs are EXEMPT and the
    exemption is reported: ``codegen.dump_exemptions`` strikes four named keyword
    positions for the dump validation alone, because the positions state a keyword no
    correct class can satisfy and both decisions involved stay as written.  Two
    mechanisms, one of them reached by two pairs:

    * ``^https://[^/?#@]+$`` on ``core/attestation-issuer.json``'s origin, inlined into
      ``core/attestation-capabilities.json`` as well.  Every pydantic URL type
      normalizes, and RFC 3986 S6.2.3 makes ``https://h/`` the normalized form of
      ``https://h`` -- so the pattern refuses the canonical spelling of a value it
      accepts.  Measured over all eight ``uri`` patterns the bundle states, 500 draws
      each: this one refuses 139 of 139 round-tripped values, so it is UNSATISFIABLE
      rather than violated at a rate, and no conforming URL library could satisfy it.
      D5 keeps the URL type; ``adcontextprotocol/adcp#8398`` repairs the pattern.
    * ``minProperties: 1`` at ``core/provenance.json``'s ``render_guidance``.  D8 maps a
      silent ``additionalProperties`` to ``extra="ignore"``, so an undeclared key is
      accepted and DROPPED and an instance whose only key is undeclared dumps to
      ``{}``.  Not an artifact of the dump's own keywords -- measured, the same node
      dumped WITHOUT ``exclude_unset`` is refused too, on ``type`` instead.  D8 stays.

    **Which is why the census below is now over ``dump_exempt`` as well as over
    ``outcome``.**  A group that leaves this list because it was exempted has to arrive
    somewhere else, or the census would have nothing to say about three pairs that pass
    conditionally -- and "passes with a keyword struck" is exactly the fact a reader of
    a green pair needs. ``tests/test_dump_exemptions.py`` grades the set and the
    strike; what this adds is the POPULATION: no fourth pair acquired one.

    * ``no_instrument`` -- the ``format``-beside-``pattern`` shape
      ``hypothesis_jsonschema``'s ``string_schema`` filters and cannot satisfy, which
      is an admitted exit rather than a failure (salesagent-j3k2l.10), and the
      schema comparison still grades both pairs.
    """
    reports = graded_reports()
    by_outcome: dict[str, list[str]] = {}
    for g, r in reports:
        if r.outcome != "pass":
            by_outcome.setdefault(r.outcome, []).append(f"{g.ref.document}{g.ref.pointer}")
    # SORTED, because the order ``graded()`` returns is module-walk order and a nested
    # pair precedes its root in it.  The membership is the obligation; the order is an
    # artifact of the walk, and asserting it would grade the walk.
    by_outcome = {k: sorted(v) for k, v in by_outcome.items()}
    assert by_outcome == NON_PASS_PAIRS, by_outcome
    # The pairs that pass CONDITIONALLY, by name, with the keyword each one had struck.
    # An exemption is a position in a literal set, so a fourth pair acquiring one is a
    # change to that set and reddens here as well as at its own pin.
    exempt = {
        f"{g.ref.document}{g.ref.pointer}": sorted(r.accepts.dump_exempt)
        for g, r in reports
        if r.accepts.dump_exempt
    }
    # THREE, not the eight that an exempt position lies inside: ``dump_exempt`` records
    # what a pair's dump NEEDED, so the five ancestor pairs whose drawn instance never
    # reached the node report nothing and a conditional pass stays readable among them.
    assert exempt == {
        "core/attestation-capabilities.json#": [
            "core/attestation-capabilities.json#/properties/accepted_issuers/items"
            "/properties/credential_origins/items/pattern",
            "core/attestation-capabilities.json#/properties/accepted_issuers/items"
            "/properties/issuer/oneOf/2/properties/origin/pattern",
        ],
        "core/attestation-issuer.json#/oneOf/2": [
            "core/attestation-issuer.json#/oneOf/2/properties/origin/pattern"
        ],
        "core/provenance.json#/properties/disclosure/properties/jurisdictions/items"
        "/properties/render_guidance": [
            "core/provenance.json#/properties/disclosure/properties/jurisdictions/items"
            "/properties/render_guidance/minProperties"
        ],
    }, exempt
    # Each cause is read off the report rather than taken from the list above, so a
    # pair that landed in one of these groups for a DIFFERENT reason reddens here.
    admitted = [(g, r) for g, r in reports if r.outcome == "no_instrument"]
    assert admitted, "nothing reports no_instrument: the clause below would grade nothing"
    for g, r in admitted:
        for cause in r.no_instrument:
            _grades_a_cause(cause, r.name)
        # The comparison needs no generator and still grades an undrawable pair,
        # which is what keeps this exit from being a hole.
        assert r.comparison.outcome == "pass" and r.comparison.compared > 0
        # ATTRIBUTED to the one position the bundle census measures as undrawable
        # (``test_no_instrument_is_the_designed_outcome_for_a_measured_shape``), and
        # not merely coincident with a document that happens to state the two
        # keywords: 72 of the 73 co-occurrences draw, so the position is the fact.
        assert g.ref.document == UNDRAWABLE_POSITION[0], g.ref
        assert r.accepts_undrawable, g.ref
        for named in r.accepts_undrawable:
            where, _, why = named.partition(": format ")
            assert UNDRAWABLE_POSITION[1].endswith(where), (UNDRAWABLE_POSITION, where)
            # ``repr``, because that is how the cause writes a pattern: a raw compare
            # would pass on the shorter string and stop grading the escaping.
            assert repr(UNDRAWABLE_PATTERN) in why and "Unsatisfiable" in why, named


def test_no_instrument_is_the_designed_outcome_for_a_measured_shape() -> None:
    """``salesagent-j3k2l.10``: the one admitted non-pass outcome, over its POPULATION.

    **The decision.** ``no_instrument`` is the designed outcome for a position whose
    ``format`` strategy cannot satisfy the ``pattern`` beside it, and section 6 is what
    grounds it: *"The conformance claim is carried entirely by the comparison.
    ``model_json_schema()`` equal to the document is the statement that every
    constraint reaching the model is the document's own and no other -- which is the
    only sense in which a generated class can be faithful, given that the model is not
    the validator."*  The comparison needs no generator, so a pair the generator cannot
    reach loses no conformance evidence -- and both of them are compared, asserted in
    ``test_the_non_pass_pairs_are_named_and_attributed`` and again below.

    **The alternative was excluded by measurement, not preference.**
    ``hypothesis_jsonschema``'s ``string_schema`` takes the FORMAT's strategy and
    applies the pattern as a ``.filter()``, and ``custom_formats`` is keyed on the
    format alone and never sees the node -- so no supported hook can make a format
    strategy pattern-aware.  What is left is an upstream change to ``string_schema``,
    a reimplementation of the library's string generation here, or a ``uri`` strategy
    whose output pool contains a ``github.com`` value, which is an instrument built
    from the answer and which the next bundle pinning another host would undo.

    **Four clauses, each over the whole population and each with its denominator.**

    1. THE CENSUS.  73 positions in 47 of 1,054 documents, 8 distinct
       ``(format, pattern)`` shapes, and the format is ``uri`` at every one.
    2. THE DRAW.  7 of the 8 shapes draw -- the library's ``uri`` strategy emits
       ``https://A.COM``, which matches every pattern pinning the scheme or the general
       host shape -- so 72 of the 73 positions are reachable and ONE is not.  This is
       the clause that makes the exit a shape and not a label: co-occurrence is
       overwhelmingly drawable, so a cause naming co-occurrences would admit a
       ``strategy_error`` from any cause at all.
    3. THE OBSTRUCTION IS UNCONDITIONAL.  ``source_repository`` is required by
       ``provenance`` and ``provenance`` by the root, so no instance of either document
       can omit the position and no number of examples would have reached one.  Were it
       optional this would be a sampling artifact and the answer would be more draws.
    **The fourth clause is in ``test_the_non_pass_pairs_are_named_and_attributed``**,
    because it is over the other population -- the graded REPORTS -- and that test
    already holds it.  It attributes every admitted ``no_instrument`` pair to the one
    position measured here, so the two halves of the decision meet at
    ``UNDRAWABLE_POSITION`` and neither can move alone.
    """
    docs = {d: bundle.read(BUNDLE, d) for d in claimed("bundle.portable", bundle.portable(BUNDLE))}

    # 1. THE CENSUS, as the set of positions rather than as its size: how many of them
    #    the bundle states is a property of the bundle version, and the facts this
    #    clause exists for are that the set is not empty and that the format is ``uri``
    #    at every one of them.
    positions = {
        (document, pointer): node
        for document, doc in sorted(docs.items())
        for pointer, node in harness.format_pattern_positions(doc)
    }
    claimed("positions stating format beside pattern", positions)
    shapes = collections.Counter((node["format"], node["pattern"]) for node in positions.values())
    claimed("distinct (format, pattern) shapes", shapes)
    assert {fmt for fmt, _ in shapes} == {"uri"}, sorted(shapes)
    # Every position lands in exactly one shape, so no position is lost between the two
    # readings -- the identity the two censuses were a pair of numbers for.
    assert sum(shapes.values()) == len(positions)

    # 2. THE DRAW, over the SHAPES rather than the positions: what decides drawability
    #    is the pair of keywords, so the shape is the unit and the positions are its
    #    multiplicity.  Drawn through the production function.  The undrawable shape is
    #    NAMED with its pattern and the drawable ones are the complement, which is the
    #    clause that makes the exit a shape and not a label: co-occurrence is
    #    overwhelmingly drawable, so a cause naming co-occurrences would admit a
    #    ``strategy_error`` from any cause at all.
    cannot: dict[tuple[str, str], tuple[str, ...]] = {}
    for fmt, pattern in shapes:
        why = harness.undrawable_formats({"type": "string", "format": fmt, "pattern": pattern})
        if why:
            cannot[(fmt, pattern)] = why
    assert list(cannot) == [("uri", UNDRAWABLE_PATTERN)], sorted(cannot)
    draws = claimed("shapes that draw", set(shapes) - set(cannot), inside=set(shapes))
    assert sum(shapes[s] for s in draws) == len(positions) - sum(shapes[s] for s in cannot)
    assert "Unsatisfiable" in cannot[("uri", UNDRAWABLE_PATTERN)][0]
    assert [k for k, n in positions.items() if n["pattern"] == UNDRAWABLE_PATTERN] == [
        UNDRAWABLE_POSITION
    ]

    # 3. THE OBSTRUCTION IS UNCONDITIONAL: walk the pointer and require the key at
    #    every step, so an instance that omits the node does not exist.
    document, pointer = UNDRAWABLE_POSITION
    node = docs[document]
    steps = pointer.lstrip("/").split("/")
    assert steps[::2] == ["properties"] * (len(steps) // 2), pointer
    for key in steps[1::2]:
        assert key in node.get("required", []), (pointer, key, node.get("required"))
        node = node["properties"][key]
    assert node["format"] == "uri" and node["pattern"] == UNDRAWABLE_PATTERN


def test_the_liveness_check_reaches_every_pair_the_document_refuses_anything_for() -> None:
    """The liveness check's own denominator, and what it is NOT.

    Section 6 keeps one refused payload per class and routes it through the entry
    point, so the question this answers is "how many classes' schema halves were
    shown to be connected, and was any of them silent".  ``no_payload`` is the complement and is enumerated
    by name in ``test_a_refused_payload_is_derived_for_every_pair_an_instance_was_drawn_for``.

    ``schema_half_not_connected`` is pinned at ZERO rather than tracked, because an
    acceptance there is not a tolerance: the document refuses this payload and the
    entry point did not, so either the schema half is not running for that class or
    its ``__adcp_schema__`` does not resolve to the document it names.
    """
    reports = [r for _, r in graded_reports()]
    by_outcome: dict[str, set[str]] = {}
    for g, r in graded_reports():
        by_outcome.setdefault(r.liveness.outcome, set()).add(f"{g.ref.document}{g.ref.pointer}")
    assert by_outcome.get("schema_half_not_connected", set()) == set(), [
        (r.name, r.liveness.how, r.liveness.violated) for r in reports
        if r.liveness.outcome == "schema_half_not_connected"
    ]
    # The live outcomes PARTITION the pairs -- no third one, nothing unaccounted -- and
    # ``no_payload`` is the NAMED set it is enumerated as rather than a count of 2, so
    # ``pass`` is the complement and neither has a number of its own to re-point.
    assert set(by_outcome) == {"pass", "no_payload"}, sorted(by_outcome)
    assert by_outcome["no_payload"] == set(NO_PAYLOAD_PAIRS), sorted(by_outcome["no_payload"])
    partitions({f"{g.ref.document}{g.ref.pointer}" for g, _ in graded_reports()}, **by_outcome)
    # The document decided, at every pair: a perturbation nothing bit is never
    # offered to the class, so every payload that reached one violates a keyword the
    # document names.
    assert all(r.liveness.violated for r in reports if r.liveness.outcome == "pass")


def test_extra_follows_the_schema_and_a_silent_document_takes_the_base_default() -> None:
    """D8, over the FOUR forms a document's ``additionalProperties`` can take here.

    The set of classes is partitioned by what each node's document APPLIES, derived
    from the bundle, and each part is required non-empty so none is graded by an empty
    loop.  The silent part is the one the base's own default is asserted for, which is
    why it is asserted here rather than left to follow from the classes that state it.

    **A TYPED ``additionalProperties`` is the fourth form, and it was not a case here
    until a document carrying one emitted.**  The check read the applied value through a
    three-way table of ``false`` / ``true`` / absent, so the day
    ``core/canonical-media-buy-features.json`` emitted it raised ``TypeError: cannot use
    'dict' as a dict key`` -- a check that ranged over the forms it happened to have met
    and had nothing to say about a fourth.  The forms are enumerated now, and an
    unrecognised one is refused by name rather than used as a dict key.

    ``ignore`` and not ``allow`` for the silent case, because absent and ``true``
    are different statements: ``true`` says an additional property is part of the
    document and is retained, while silence says only that one is permitted, so it
    is accepted and dropped.  Both accept the same payloads, so this is retention
    and not the accepted set.  Nothing reads an environment to decide it.
    """
    assert AdCPBaseModel.model_config["extra"] == "ignore"

    grouped: dict[str, set[str]] = {"forbid": set(), "allow": set(), "silent": set(), "typed": set()}
    classes: set[str] = set()
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
        name = f"{row.ref.document}{row.ref.pointer}"
        classes.add(name)
        declared = _closed(_composed(schema_at(row.ref)).get("additionalProperties", "silent"))
        # The four forms, named: a schema here is the TYPED row, graded in full by
        # ``test_a_typed_additional_properties_is_a_typed_pydantic_extra``.  What D8
        # decides for it is the same as for ``true`` -- an additional property is part
        # of the document and is retained -- so the retention is asserted here and the
        # typing there.
        if isinstance(declared, dict):
            assert row.model.model_config["extra"] == "allow", (row.ref, declared)
            grouped["typed"].add(name)
            continue
        assert declared in (False, True, "silent"), (row.ref, declared)
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
            grouped["allow"].add(name)
            continue
        assert row.model.model_config["extra"] == want, (row.ref, declared)
        grouped["silent" if declared == "silent" else want].add(name)

    # The four forms partition the classes: total, disjoint, and every part non-empty,
    # so no form is graded by a loop that met none of it.  The silent part is the leaf
    # objects whose documents say nothing plus the union BASES, which are silent by
    # construction -- ``lower/union.py`` refuses a root that states its own
    # ``additionalProperties``, so a base never has one to carry and takes this default
    # -- plus the mapping and container roots whose own document is silent too.  How
    # MANY are in each part is a reading of the emitted population and every row moves
    # all four, which is why none of them is asserted.
    partitions(claimed("graded classes", classes), **grouped)
    for form, members in grouped.items():
        claimed(f"classes whose document applies {form}", members, inside=classes)


# --------------------------------------------------------------------------- #
# what the schema half decides, and where it finds the schema
# --------------------------------------------------------------------------- #
def test_strict_validate_decides_acceptance_against_the_document() -> None:
    """D4.

    What nothing else in this file reaches: that the schema half of
    ``strict_validate`` runs at all, and that the keyword it refuses on is the
    DOCUMENT'S name for it.  ``check_pair`` cannot grade either -- it offers one
    perturbation of an accepted instance, and a model graded through
    ``strict_validate`` refuses whatever the document refuses whichever half
    answered.  Measured:
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

    **THE OBLIGATION IS "DECIDABLE LOCALLY", AND A LOCAL POINTER IS.**  The sentence
    above says why -- an ABSOLUTE URI has no store and goes to the network -- and a
    ``#/definitions/x`` needs no store at all, only the document as its resolution
    scope.  ``bundle.resolved`` inlines a remote reference and leaves a local one, so
    a packaged document CAN carry one, and the first ones to be packaged arrived with
    ``salesagent-j3k2l.28``: ``core/placement-presentation.json`` and
    ``core/bidding-policy-capability.json``, which were refused by name until that row.
    ``_base._refuse_at`` evolves a document-rooted validator onto the node, so the
    pointer resolves, and ``tests/test_applied_schema.py`` asserts BOTH halves of that
    -- every local reference a graded pair holds resolves, and the schema half refuses
    THROUGH it.  So the split is read with ``bundle.split_ref``, which is the one
    reading of the ``#`` this project has, rather than by looking for the key.
    """
    documents = {g.ref.document for g in graded()}
    local: dict[str, set[str]] = {}
    for document in sorted(documents):
        remote: list[tuple[str, str]] = []
        for pointer, reference in bundle.references(schema_at(SchemaRef(document, "#"))):
            if bundle.split_ref(reference)[0]:
                remote.append((pointer, reference))
            else:
                local.setdefault(document, set()).add(reference)
        assert remote == [], document
    # And the control: the bundle DOES have references, so the assertion above is
    # over documents that had something to resolve rather than over nothing.
    assert [d for d in documents if bundle.references(bundle.read(BUNDLE, d))]
    # The local set, named rather than counted: the two documents that carry one, and
    # the REFERENCES each one carries, by target.  A count per document said only how
    # many there were, so a reference changing target was invisible to it and a
    # document joining the set moved a number nobody could attribute.
    # ``tests/test_applied_schema.py`` reads the same references once per
    # (PAIR, reference) rather than once per document, which is a second denominator
    # for one fact and is why that file's figures are larger.
    assert {d: sorted(r) for d, r in local.items()} == {
        "core/bidding-policy-capability.json": [
            "#/definitions/max_bid_with_cost_per",
            "#/definitions/max_bid_with_roas",
            "#/definitions/policy_profile",
        ],
        "core/placement-presentation.json": [
            "#/definitions/color",
            "#/definitions/layer",
            "#/definitions/rectangle",
        ],
    }, {d: sorted(r) for d, r in local.items()}


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
    cross_document: set[tuple[str, str]] = set()
    graded_properties: set[tuple[str, str]] = set()
    fragment_refs: dict[tuple[str, str], str] = {}
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
            cross_document.add((document, key))
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
                fragment_refs[(document, key)] = uri
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
            graded_properties.add((document, key))
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
    # The two halves PARTITION the cross-document property references, and both are
    # NON-EMPTY, so neither the graded half nor the half handed to
    # ``tests/test_fragment_ref.py`` can go quiet.
    #
    # Asserted as sets and not as two totals, and this pin is the row that made the
    # case: it read ``graded_properties == 567`` while 586 was live on trunk and 606 on
    # a branch in flight -- red on both trees and pinned at neither, for weeks, because
    # every row that makes a document emittable moves it and no two rows move it to the
    # same place.  Re-pointing it was a deferral with a date.  The partition moves with
    # nobody: a reference joins one part or the other, and a reference that joins
    # NEITHER, or both, is the defect this is for.
    partitions(cross_document, graded_here=graded_properties, handed_on=set(fragment_refs))
    claimed("cross-document property references graded here", graded_properties)
    claimed("cross-document property references naming a fragment", fragment_refs)


# --------------------------------------------------------------------------- #
# step 5: union roots (§4)
# --------------------------------------------------------------------------- #
def emitted_unions() -> list[str]:
    """The union roots the committed tree holds, read off the tree and the selector."""
    return sorted({g.ref.document for g in graded()} & set(union_roots()))


def _alias_shaped(document: str) -> bool:
    """Which of D2's two union shapes this root takes.

    Asked of the PRODUCTION predicates (``lower_union.states_a_scalar_instance`` and
    ``lower_union.declares_a_class``) and not of a reading of its own, because the
    shape is what the tests below grade and a second reading of it is how a test comes
    to expect the shape the lowering did not emit.  What is pinned instead is the SIZE
    of each half, as a literal, in
    :func:`test_a_union_root_is_a_base_or_an_alias_and_the_document_decides_which`.
    """
    doc = bundle.read(BUNDLE, document)
    kw = lower_union.keyword(doc)
    assert kw is not None, document
    return lower_union.states_a_scalar_instance(doc, "", kw) and not any(
        lower_union.declares_a_class(branch, doc, "", kw, i)
        for i, branch in enumerate(doc[kw])
    )


def emitted_union_bases() -> list[str]:
    """The emitted union roots D2 gives a base plus one subclass per branch (§4).

    **The eight shape tests below run over THIS and not over
    :func:`emitted_unions`.**  D2 gives a union root two shapes -- the base plus
    subclasses, and, where the document says its instance is a scalar, the
    module-level alias a root scalar gets -- and an assertion about
    ``BranchDispatchMixin`` is a claim about the first only.  Over the whole
    population it would fail on a correct alias, which is a test asserting the wrong
    shape rather than a defect.
    """
    return [d for d in emitted_unions() if not _alias_shaped(d)]


def emitted_union_aliases() -> list[str]:
    """The emitted union roots D2 gives a module-level alias, because the document
    says every instance it admits is a scalar (``salesagent-j3k2l.21``)."""
    return [d for d in emitted_unions() if _alias_shaped(d)]


def test_a_union_root_is_a_base_or_an_alias_and_the_document_decides_which() -> None:
    """D2's TWO union shapes, over every union root the bundle has, with the shape
    decided by the document and the emitted artifact graded against the one it chose.

    D2 gives a ``oneOf``/``anyOf`` root a base plus one subclass per branch.  It also
    says "a root scalar or mapping -> a module-level alias", and a union every branch of
    which is a scalar IS a root scalar: every branch of a draft-07 combinator is applied
    to the SAME instance, so a branch declaring a non-object type is the document saying
    what the whole document's instance is, and there is no class for a string to be an
    instance of.  ``{"type": ["string", "null"]}`` at a root would be the same document
    at the other spelling, which is the spelling ``salesagent-j3k2l.21`` is named for.

    Five clauses, one per way the partition can go wrong, each over a population whose
    size is asserted as a LITERAL below (D14):

    1. **the two shapes are DISJOINT.**  A root that both says its instance is a scalar
       AND declares a branch with a shape is NEITHER -- no alias holds a class and no
       base is a string -- and must take neither path.  It keeps the class path, where
       the scalar branch's own ``type`` check refuses it by name.  Asserted at 0 rather
       than exempted, so the first one that appears reddens here instead of silently
       taking whichever path the predicate happens to answer first.
    2. **the two shapes are EXHAUSTIVE over the emitted roots, and BOTH are non-empty.**
       A partition one half of which is empty passes for free, which is the state this
       row's own first cut was in before the alias path emitted anything.
    3. **§8's invariant: no root LEAVES ``BranchDispatchMixin``.**  "A step adds roots to
       it; no step removes one."  The alias path could only take a root off the mixin by
       claiming one the class path was already emitting, so the base half is pinned at
       the figure it had BEFORE this row -- 38 -- and the alias half is growth.  That is
       a pin on a DIFFERENT axis from the total, which moved: a single total would
       absorb a root swapping sides.
    4. **an alias-shaped root binds an ALIAS, with §4's two halves.**  A root scalar has
       no class to carry ``strict_validate``, so "its module binds the same two halves as
       a module-level function over the same ``SchemaRef``" -- which is read off the AST
       (the name is not a ``ClassDef``, and both halves are module-scope statements) and
       then off the IMPORTED module, because whether a name is a class is a property of
       the object and the text cannot say it.
    **WHERE A THIRD SHAPE EXTENDS THIS, named so it is not a surprise.**
    ``salesagent-j3k2l.52`` gives D2 a third reading of a union root -- branches that differ
    only in permitted VALUES are a rule on one class rather than a class per branch -- and it
    is sequenced after this row. It does not collide with the dispatch: every branch of that
    shape declares the same property set, so ``declares_a_class`` answers True for each and
    the alias is not reached. What it must extend is clause 2's equality below, which says the
    two halves exhaust the emitted roots; a third half makes that equality fail by naming the
    documents in neither, which is the legible failure rather than a silent one.

    5. **where each spelling of a declared null actually lives**, so the lowering's claim
       about it cannot go stale in silence: 0 union roots carry a ``null`` branch and 0
       roots carry a ``type`` LIST, while 57 sites state ``null`` inside a ``type`` list
       BELOW a root -- ``lower.containers.multi_type``'s position, whose fold is graded
       by :func:`test_a_declared_null_is_never_read_as_absence` in both directions.  A
       null branch of a union ROOT would land in the alias half as ``str | None``, and
       this is the clause that says the bundle has none to grade.
    """
    portable = sorted(claimed("bundle.portable", bundle.portable(BUNDLE)))
    roots = [d for d in portable if bundle.union_root(bundle.read(BUNDLE, d))]
    claimed("union roots in the bundle", roots, inside=portable)

    scalar_instance, with_a_class_branch, mixed = [], [], []
    for document in roots:
        doc = bundle.read(BUNDLE, document)
        kw = lower_union.keyword(doc)
        assert kw is not None, document
        scalar = lower_union.states_a_scalar_instance(doc, "", kw)
        classed = [
            i
            for i, branch in enumerate(doc[kw])
            if lower_union.declares_a_class(branch, doc, "", kw, i)
        ]
        (mixed if scalar and classed else scalar_instance if scalar else with_a_class_branch).append(
            document
        )

    # Clause 1, and the partition it belongs to: the three shapes are total and
    # disjoint over the union roots, ``mixed`` is the part asserted EMPTY, and the
    # other two are asserted non-empty so neither clause below grades nothing.  How
    # many roots are in each is a reading of one bundle version and says nothing
    # clause 1 does not already say by name.
    assert mixed == [], mixed
    partitions(
        roots,
        scalar_instance=scalar_instance,
        with_a_class_branch=with_a_class_branch,
        mixed=mixed,
    )
    claimed("union roots whose instance is a scalar", scalar_instance, inside=roots)
    claimed("union roots with a class-shaped branch", with_a_class_branch, inside=roots)
    # Clause 2: exactly one half each, over the roots the tree actually carries.
    assert sorted(emitted_union_bases() + emitted_union_aliases()) == emitted_unions()
    assert not set(emitted_union_bases()) & set(emitted_union_aliases())
    assert emitted_union_bases(), "no class-shaped union root emitted"
    assert emitted_union_aliases(), "no alias-shaped union root emitted"
    assert set(emitted_union_aliases()) <= set(scalar_instance), emitted_union_aliases()

    # Clause 4, on both instruments.
    for document in emitted_union_aliases():
        symbol = _symbol(document)
        tree = ast.parse(_source(document))
        assert symbol not in {c.name for c in tree.body if isinstance(c, ast.ClassDef)}, document
        assigned = {
            t.id
            for node in tree.body
            if isinstance(node, ast.Assign)
            for t in node.targets
            if isinstance(t, ast.Name)
        }
        assert {symbol, "__adcp_schema__", "strict_validate"} <= assigned, (
            document,
            sorted(assigned),
        )
        module = importlib.import_module(_module_of(document))
        bound = getattr(module, symbol)
        assert not (isinstance(bound, type) and issubclass(bound, BaseModel)), (document, bound)
        assert callable(module.strict_validate), document
        assert module.__adcp_schema__.document == document, document

    # Clause 5's two populations, measured over the whole portable set.
    null_branch_roots = [
        d
        for d in roots
        if any(
            isinstance(b, dict) and b.get("type") == "null"
            for b in bundle.read(BUNDLE, d)[lower_union.keyword(bundle.read(BUNDLE, d))]
        )
    ]
    root_type_lists = [d for d in portable if isinstance(bundle.read(BUNDLE, d).get("type"), list)]
    null_in_a_type_list = {
        (d, pointer)
        for d in portable
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(node.get("type"), list) and "null" in node["type"]
    }

    # Clause 5: the two places a declared ``null`` could be and the one it IS.  The
    # empty parts are asserted empty by NAME, and the non-empty one is asserted
    # non-empty rather than counted -- what the clause claims is that the bundle has
    # sites below a root to grade and none at a root, which a census of 57 restates
    # against one bundle version and nothing else.
    assert null_branch_roots == [], null_branch_roots
    assert root_type_lists == [], root_type_lists
    claimed("sites stating null inside a type list below a root", null_in_a_type_list)

    # Clause 3, AS A FLOOR, which is what §8 actually says: "a step adds roots to
    # BranchDispatchMixin; no step removes one."  An equality also refuses the
    # ADDITION the invariant permits, which is why it was a collision -- it was 38
    # before the alias dispatch, 38 after it and 38 after D2's Literal amendment only
    # because no row had yet added a base.  A floor refuses the removal, which is the
    # invariant, and the alias half taking a root off the class path would still show
    # up here because it would take the base count DOWN.
    ratchet(
        "union roots emitted as a base over BranchDispatchMixin",
        len(emitted_union_bases()),
        at_least=UNION_BASE_FLOOR,
        because="section 8: a step adds roots to BranchDispatchMixin and no step "
        "removes one, so the alias path can never claim a root the class path emits",
    )


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
    assert emitted_union_bases(), "no union root was emitted; this test grades nothing"
    for document in emitted_union_bases():
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
    assert emitted_union_bases()
    for document in emitted_union_bases():
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
    assert emitted_union_bases()
    graded_arms = 0
    for document in emitted_union_bases():
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
        for d in emitted_union_bases()
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
    assert emitted_union_bases()
    for document in emitted_union_bases():
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
    assert emitted_union_bases()
    for document in emitted_union_bases():
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
    assert emitted_union_bases()
    assert {lower_union.keyword(bundle.read(BUNDLE, d)) for d in emitted_union_bases()} == {"anyOf", "oneOf"}
    for document in emitted_union_bases():
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
    assert emitted_union_bases()
    for document in emitted_union_bases():
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
    """The step's own arithmetic: 126 union roots, 40 emitted and 86 refused, each named.

    The by-keyword profile is asserted as a WHOLE rather than as a total, because the
    profile is the readable result of the step -- it says which later step unblocks what.

    **``allOf`` still dominates and no longer means "waiting on step 4".**  It used to:
    the keyword screen refused a root ``allOf`` with "a later D2 row does", naming step
    4's product row.  That row claims 0 of these documents -- ``composes_at_the_root``
    excludes a root carrying a union -- so the deferral named a row that was never going
    to see them.  All 51 are THIS module's own refusals: either a root where the
    ``allOf`` is a conjunction with every branch and no pointer addresses the
    conjunction (``ROOT_CONJUNCTS``).  The other half of that row is gone:
    ``salesagent-j3k2l.40`` shared the conjunct reader, so a branch that composes is
    lowered by ``compiler.lower_composition`` rather than refused, and ``allOf`` fell
    51 -> 44.  So the profile's largest row is a bill rather than a queue, which is
    what it is for.  The 37 + 9 split the previous revision quoted was measured when
    ``allOf`` was 46 and is not re-measured here; what is asserted is the row.
    """
    out = emit.emit(BUNDLE, population())
    roots = union_roots()
    emitted = [d for d in roots if d in out.emitted]
    refused = [d for d in roots if d in out.refusals]
    claimed("union roots the selector claims", roots)
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
    #
    # **34 / 92 -> 38 / 88 at ``salesagent-j3k2l.40``**, and these four are THIS
    # module's own doing rather than another row's: a composing branch is lowered now,
    # so ``core/canonical-optimization-goal.json``,
    # ``core/publisher-property-selector.json``, ``core/targeting-modification.json``
    # and ``core/canonical-media-buy-action.json`` -- 3 of the 10 that waited on the
    # shared reader, plus one reached through them -- left the refused half.
    #
    # **38 / 88 -> 40 / 86 at ``salesagent-j3k2l.21``**, and these two are this module's
    # own doing as well: a union root whose instance the DOCUMENT says is a scalar is a
    # root scalar, so it takes D2's alias instead of a base plus subclasses, and
    # ``core/start-timing.json`` and ``core/media-buy-available-action-id.json`` left the
    # refused half.  **Which half they emit into is pinned separately** --
    # ``test_a_union_root_is_a_base_or_an_alias_and_the_document_decides_which`` holds the
    # base half at 38 and the alias half at 2 -- because a single total here would absorb
    # a root swapping sides, and §8 says no step takes a root off ``BranchDispatchMixin``.
    #
    # **40 / 86 -> 42 / 84, D2's Literal amendment, in this same row.** An untitled
    # enum branch is a Literal of its members and claims no symbol, so
    # core/geo-place-system.json and core/geo-place-type.json stop colliding with
    # their own root's name and emit as aliases.
    # The two halves PARTITION the selector's roots, by name, and ``emitted`` is the
    # set the tree carries.  Neither half has a count of its own any more: which of the
    # roots emit is a function of the OTHER steps' rows, so the split moved at .29, .40
    # and .21 and every move was correct work being done -- 28/98, 34/92, 38/88, 40/86,
    # 42/84, each one a pair of numbers two lanes could not both be right about.  What
    # is asserted is the property no row may break: every root is accounted for exactly
    # once, both halves are non-empty, and the emitted half IS the emitted set.
    partitions(roots, emitted=emitted, refused=refused)
    claimed("union roots this step emits", emitted, inside=roots)
    claimed("union roots this step refuses", refused, inside=roots)
    assert emitted == emitted_unions()

    # **EVERY REFUSED ROOT, BY NAME, WITH THE KEYWORD IT REFUSES ON.**  This test's
    # title claims an accounting by name, pointer and keyword; what it held was a
    # keyword -> COUNT profile, which accounts for nothing by name -- a document moving
    # from one keyword to another left it unchanged, and every row that cleared a
    # refusal had to recompute between two and eleven integers that no other row could
    # agree with.  The mapping below is the same information as a set of names per
    # keyword, one line per document, so a row that clears a refusal DELETES ITS LINE
    # and two rows clearing different refusals merge instead of colliding.
    #
    # The POINTER is asserted present per document rather than pinned: a chained
    # refusal's pointer moves deeper as its chain resolves, which is a correct move and
    # not this check's fact.  The keyword is the attribution, and ``allOf`` is the bulk
    # of it because a root conjunct is still deferred ground.
    refused_on: dict[str, str] = {}
    for document in refused:
        row = out.refusals[document]
        assert row["keyword"] and row["pointer"], document
        refused_on[document] = row["keyword"]
    assert refused_on == {
    "account/get-account-financials-response.json": "allOf",
    "account/list-account-changes-response.json": "allOf",
    "account/sync-accounts-response.json": "allOf",
    "account/sync-governance-response.json": "allOf",
    "adagents.json": "anyOf",
    "brand.json": "allOf",
    "brand/acquire-rights-response.json": "allOf",
    "brand/creative-approval-response.json": "allOf",
    "brand/get-brand-identity-response.json": "allOf",
    "brand/get-rights-response.json": "allOf",
    "brand/search-brands-response.json": "allOf",
    "brand/update-rights-response.json": "allOf",
    "brand/verify-brand-claim-request.json": "allOf",
    "brand/verify-brand-claim-response.json": "allOf",
    "brand/verify-brand-claims-response.json": "allOf",
    "compliance/comply-test-controller-response.json": "allOf",
    "compliance/task-completion-data.json": "$ref",
    "content-standards/calibrate-content-response.json": "allOf",
    "content-standards/create-content-standards-response.json": "allOf",
    "content-standards/get-content-standards-response.json": "allOf",
    "content-standards/get-media-buy-artifacts-response.json": "allOf",
    "content-standards/list-content-standards-response.json": "allOf",
    "content-standards/update-content-standards-response.json": "allOf",
    "content-standards/validate-content-delivery-response.json": "allOf",
    "core/account-identity-change-preview.json": "$ref",
    "core/agent-reporting-destination.json": "$ref",
    "core/assets/asset-union.json": "$ref",
    "core/assets/daast-asset.json": "properties",
    "core/assets/display-tag-asset.json": "properties",
    "core/assets/vast-asset.json": "properties",
    "core/async-response-data.json": "$ref",
    "core/audience-characteristic.json": "allOf",
    "core/brand-response-authorization-result.json": "properties",
    "core/budget-allocation.json": "$ref",
    "core/canonical-media-buy-action.json": "const",
    "core/canonical-placement.json": "properties",
    "core/catchment.json": "properties",
    "core/collection-selection.json": "required",
    "core/creative-asset.json": "allOf",
    "core/creative-manifest.json": "allOf",
    "core/delivery-metric-aggregate.json": "allOf",
    "core/evaluator-spec.json": "properties",
    "core/format-option-ref.json": "additionalProperties",
    "core/frequency-cap-impression-constraints.json": "properties",
    "core/frequency-cap-interval-constraints.json": "properties",
    "core/macro-bearing-url.json": "format",
    "core/optimization-goal.json": "allOf",
    "core/placement-selection.json": "required",
    "core/postal-area.json": "$ref",
    "core/postal-country-system.json": "properties",
    "core/pricing-option.json": "$ref",
    "core/product-execution-requirement.json": "not",
    "core/product-format-declaration.json": "allOf",
    "core/registry-event.json": "properties",
    "core/requirements/asset-requirements.json": "$ref",
    # Was ``$ref`` -- "a bare $ref branch has no node to declare a subclass from" --
    # until ``salesagent-j3k2l.59`` made such a branch a class with two bases.  Its
    # three branches now name themselves off the ``kind`` pin (two of them through a
    # LOCAL ``$ref``) and the root's dispatch derives to ``kind``, so the document gets
    # past this module and refuses one pointer deeper, on a ``discriminator`` sibling of
    # the NESTED union at ``/oneOf/2/properties/per_item_bindings/items`` -- a different
    # position with a different reason (``union.nested``'s sibling screen), filed as
    # ``salesagent-j3k2l.67``.
    "core/requirements/catalog-field-binding.json": "discriminator",
    "core/tracker-execution-selector.json": "$ref",
    "core/wholesale-feed-event.json": "properties",
    "creative/get-creative-features-response.json": "allOf",
    "creative/preview-creative-response.json": "allOf",
    "creative/sync-creatives-response.json": "allOf",
    "error-details/governance-agent-not-accepted.json": "maxLength",
    "error-details/vast-version-mismatch.json": "properties",
    "media-buy/build-creative-response.json": "allOf",
    "media-buy/buy-products-request.json": "allOf",
    "media-buy/control-media-buy-response.json": "$ref",
    "media-buy/create-media-buy-request.json": "allOf",
    "media-buy/create-media-buy-response.json": "allOf",
    "media-buy/decline-proposals-response.json": "properties",
    "media-buy/get-reporting-status-response.json": "allOf",
    "media-buy/list-products-response.json": "properties",
    "media-buy/log-event-response.json": "allOf",
    "media-buy/media-buy-commitment-response.json": "$ref",
    "media-buy/proposal-refinement.json": "properties",
    "media-buy/provide-performance-feedback-response.json": "allOf",
    "media-buy/refine-proposals-response.json": "properties",
    "media-buy/request-proposals-request.json": "allOf",
    "media-buy/request-proposals-response.json": "properties",
    "media-buy/sync-audiences-response.json": "allOf",
    "media-buy/sync-catalogs-response.json": "allOf",
    "media-buy/sync-event-sources-response.json": "allOf",
    "media-buy/update-media-buy-response.json": "allOf",
    "signals/activate-signal-response.json": "allOf",
    "trusted-match/provider-registration.json": "properties",
    }, refused_on


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
    # Non-empty rather than counted: the claim is asserted OF EACH MEMBER below, so
    # what this needs is that there is a member -- an empty list asserted nothing about
    # any document, which is the state this check was in before.  The count went 7 -> 9
    # when two more ``formats/canonical`` documents emitted, which is a correct move,
    # and every later row that makes such a document emittable moves it again.
    claimed("graded documents stating properties with no root type", bare)
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
    # const-pinned branch properties whose node states only the ``const``.  THE TWO
    # KINDS are the rule's shape and are asserted exactly; the two POSITIONS -- the
    # root and a property -- partition the excused sites and both are non-empty, so
    # neither position is graded by an empty loop.  The three counts this replaces
    # (45 / 19 / 26) were a reading of one emitted tree and all three moved together
    # at every row that added a document, while the shape moved at none of them.
    assert kinds == {"object", "string"}, kinds
    sites = claimed("sites the model-only type rule excuses", excused)
    partitions(
        sites,
        at_the_root={e for e in sites if e[1] == ""},
        at_a_property={e for e in sites if e[1] != ""},
    )
    claimed("excused sites at a root", {e for e in sites if e[1] == ""}, inside=sites)
    claimed("excused sites at a property", {e for e in sites if e[1] != ""}, inside=sites)

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
    # Both arms of the loop below range over a set of nodes, and each one is named
    # non-empty: an empty bundle would run the loop zero times and say nothing about
    # either arm -- "every union root carries a keyword" and "every non-root carrying
    # one spells a presence rule" would both hold for free.
    claimed(
        "documents whose root carries oneOf or anyOf",
        [d for d in bundle.portable(BUNDLE) if bundle.union_root(bundle.read(BUNDLE, d))],
    )
    claimed(
        "documents carrying the keyword without being a union root",
        [
            d
            for d in bundle.portable(BUNDLE)
            if not bundle.union_root(bundle.read(BUNDLE, d))
            and union.keyword(bundle.read(BUNDLE, d)) is not None
        ],
    )
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
    documents = claimed("bundle.portable", bundle.portable(BUNDLE))
    by_count: dict[int, set[str]] = {}
    for document in sorted(documents):
        doc = bundle.read(BUNDLE, document)
        n = sum(1 for selector, _ in emit.ROWS if selector(doc))
        by_count.setdefault(n, set()).add(document)
    assert sorted(by_count) == [0, 1], {k: len(v) for k, v in by_count.items()}  # never two
    # The two counts PARTITION the bundle by name, and the one-row half is asserted
    # NON-EMPTY, which is what keeps the disjointness above from being satisfied by a
    # table that selects nothing.  How many documents no row claims is a function of
    # the rows -- it was 21 before ``composes_at_the_root``'s two-reading hole closed
    # and 7 after -- so it is the membership that is asserted and not the size.
    # **The documents no row claims are not waiting for a row**: they are DATA
    # documents with no schema keyword at the root, conditional-only documents and a
    # bare root ``$ref``, and ``emit.lower_document`` refuses each on the keyword its
    # kind is read from rather than on the absence of a row.
    partitions(documents, claimed_by_one_row=by_count[1], claimed_by_no_row=by_count[0])
    claimed("documents exactly one row claims", by_count[1], inside=documents)

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
    arrays: set[tuple[SchemaRef, str]] = set()
    bounded: set[tuple[SchemaRef, str, str]] = set()
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
            arrays.add((row.ref, key))
            mine = _rendered(emitted, key, row.model)
            assert mine.get("type") == "array", (row.ref, key, mine)
            for keyword in ("minItems", "maxItems"):
                assert mine.get(keyword) == sub.get(keyword), (row.ref, key, keyword, mine)
                if keyword in sub:
                    bounded.add((row.ref, key, keyword))
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
    # Stated so the set is not read as "every array".  Both halves non-empty rather
    # than counted: the per-keyword assertion inside the loop is the obligation and it
    # needs an array to have been reached, and the bounded half needs a bound to have
    # been compared.  The two counts this replaces moved together at every row that
    # added an emitted root.
    claimed("top-level array properties of an emitted root", arrays)
    claimed("array bounds compared", bounded)


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
    # named WITH ITS POINTER, which is the position the refusal is about -- D2's
    # unimplemented ``RootModel[list[X]]`` row at a root, a mapping value, a
    # ``definitions`` section's array and a union branch.  ``product.lower_root``
    # writes no rule of any D6 family, which is step 4's row and not this keyword's.
    #
    # Re-pointed here, with each move's cause read off the refusal rather than
    # inferred from the list's length.  Three documents JOINED, all three because an
    # earlier blocker of theirs cleared and the walk reached this keyword:
    # ``core/daast-tracker-constraints.json`` and ``core/vast-tracker-constraints.json``
    # at a ``definitions`` section's array, and ``error-details/requote-required.json``
    # at a ``oneOf`` branch -- each one a ``Kind.VERDICT`` on this keyword, which is
    # this row's own ground and not a deferral.  One LEFT:
    # ``media-buy/list-creative-formats-request.json`` emits now.
    out = emit.emit(BUNDLE, population())
    blocked = {d: out.refusals[d]["pointer"] for d, r in out.refusals.items() if r["keyword"] == "uniqueItems"}
    claimed("documents refused on uniqueItems", blocked)
    assert blocked == {
        "core/acceptance-policy-profile-ids.json": "/",
        "core/account-authorization.json": "/properties/field_scopes/additionalProperties",
        "core/daast-tracker-constraints.json": "/definitions/daast_versions",
        "core/forecast-point-dimensions.json": "/",
        "core/reporting-verification-profile-set.json": "/",
        "core/vast-tracker-constraints.json": "/definitions/vast_versions",
        "error-details/requote-required.json": "/properties/envelope_field/oneOf/1",
        "media-buy/product-fields.json": "/",
    }, blocked


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
    roots = claimed(
        "root arrays in the bundle",
        [d for d in bundle.portable(BUNDLE) if bundle.read(BUNDLE, d).get("type") == "array"],
        inside=bundle.portable(BUNDLE),
    )
    assert all(d in out.refusals for d in roots), [d for d in roots if d not in out.refusals]
    # The two keywords they refuse on, and the PARTITION of the roots between them by
    # name: the one that refuses inside its own ``items`` is the odd one and is named
    # below, so a count of the other group says nothing the partition does not.
    assert {out.refusals[d]["keyword"] for d in roots} == {"uniqueItems", "discriminator"}
    partitions(
        roots,
        at_the_root={d for d in roots if out.refusals[d]["keyword"] == "uniqueItems"},
        inside_its_items={d for d in roots if out.refusals[d]["keyword"] != "uniqueItems"},
    )
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
    mappings: set[tuple[str, str]] = set()
    for row in graded():
        doc = schema_at(row.ref)
        for pointer, node in bundle.nodes(doc):
            if node.get("type") == "object" and "properties" not in node:
                mappings.add((f"{row.ref.document}{row.ref.pointer}", pointer or "/"))
                if {"propertyNames", "patternProperties"} & set(node):
                    constrained.append((f"{row.ref.document}{row.ref.pointer}", pointer or "/"))
    # The mapping population is asserted NON-EMPTY rather than counted -- the claim is
    # about the one constrained key among them, which is named, and the denominator's
    # job is to say that mappings were reached at all.  A count of them is a reading of
    # one emitted tree: it was 1,528 when every pair graded here was, and 1,750 once
    # eleven more documents brought their nodes with them.
    claimed("mapping nodes of a graded pair", mappings)
    assert constrained == [("core/product-change-map.json#", "/")], constrained
    assert set(constrained) <= mappings, constrained
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
    """D8's typed row, and the EXTRAS STORE now has exactly one live document.

    Measured: 727 documents mention ``additionalProperties`` and 51 carry a typed one.
    11 of the 51 emit, and the extras store needs a node declaring ``properties`` AND
    a typed ``additionalProperties`` -- the bundle has 14 such nodes, and ONE of their
    documents emits: ``core/canonical-media-buy-features.json``, which
    ``salesagent-j3k2l.28`` unblocked.  Until then the store was reached by 0
    documents and graded only by the constructed one at the end of this test.

    **The one document is also where the store's first defect showed**, which is the
    reason to say "one" rather than to stop asserting the number: dmcg reported a
    ``typing.Dict`` import for an annotation it rendered ``dict[str, bool]``, so the
    module carried an import it does not use.  Fixed in ``compiler.render`` by the
    rule the ``ConfigDict`` line beside it already follows -- take the imports the
    rendered annotation's own names call for.  A mechanism with a population of 0 is
    green for free; this one has 1, and that is what found it.
    """
    typed = [
        d
        for d in bundle.portable(BUNDLE)
        if any(
            isinstance(n.get("additionalProperties"), dict) and n["additionalProperties"]
            for _, n in bundle.nodes(bundle.read(BUNDLE, d))
        )
    ]
    # Non-empty, and inside the bundle: how many documents carry a typed
    # ``additionalProperties`` is a property of the bundle version, and what this
    # clause needs is a population for the emitted list below to be drawn from.
    claimed("documents carrying a typed additionalProperties", typed, inside=bundle.portable(BUNDLE))
    mentions = [
        d
        for d in bundle.portable(BUNDLE)
        if "additionalProperties" in bundle.schema_keywords(bundle.read(BUNDLE, d))
    ]
    claimed("documents mentioning additionalProperties", mentions, inside=bundle.portable(BUNDLE))
    assert set(typed) <= set(mentions), sorted(set(typed) - set(mentions))
    out = emit.emit(BUNDLE, population())
    # The emitted list and the store sites are DIFFERENT facts, and both are asserted:
    # a typed ``additionalProperties`` on a node with no ``properties`` is a MAPPING,
    # which the row above lowers, while the extras store needs a node declaring BOTH.
    # The bundle has 14 of the second kind and exactly one of them is in a document
    # this run emits, so the store is graded by that document and by the constructed
    # probe at the end -- a count of emitted documents says nothing about it.
    #
    # Re-measured at 64131600f (``salesagent-j3k2l.29``).  The 14 is unchanged and is
    # over the bundle; the emitted list is over ``population()`` and grew from 1.  The
    # previous revision said the 14 "all sit under ``definitions``", which is not
    # true of this bundle -- 4 of them are at a document's own root -- so the reason
    # recorded here is now the measured one: none of the 14 is in an emitted document.
    #
    # 10 -> 11 at ``salesagent-j3k2l.21``, and the eleventh is NAMED rather than
    # counted because the cause has to be attributable: ``core/geo-place-area.json``
    # joins because its two ``$ref`` targets now emit.  ``core/geo-place-system.json``
    # and ``core/geo-place-type.json`` are each a root ``anyOf`` of SCALARS whose
    # untitled first branch carries an ``enum`` -- this row's own population -- so
    # both lower to a root alias and the document that references them is no longer
    # chained to their refusals.  Its typed ``additionalProperties`` is at
    # ``/properties/value_labels/additionalProperties``, a node with no
    # ``properties``, so it is the MAPPING path and the store assertion below is
    # unchanged by it: the one emitted store site is still
    # ``core/canonical-media-buy-features.json``.
    emitted_typed = sorted(set(typed) & set(out.emitted))
    assert emitted_typed == [
        "a2ui/component.json",
        "collection/get-collection-list-response.json",
        "core/canonical-media-buy-features.json",
        "core/geo-place-area.json",
        "core/product-change-map.json",
        "core/reporting-file-entry.json",
        "core/tasks-list-response.json",
        "error-details/vendor-error-codes.json",
        "property/property-feature-result.json",
        "protocol/list-tasks-response.json",
        "sponsored-intelligence/si-ui-element.json",
    ], emitted_typed
    store = [
        (d, pointer or "/")
        for d in bundle.portable(BUNDLE)
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(node.get("additionalProperties"), dict)
        and node["additionalProperties"]
        and "properties" in node
    ]
    claimed("nodes declaring properties beside a typed additionalProperties", store)
    # ONE of the 14, named: the store stopped being a mechanism with no document the
    # moment ``salesagent-j3k2l.28`` let this one emit, and the pointer is the root's
    # own node.  Asserted as the row rather than as a count, so a second document
    # joining it is read as a new site and not as a number going up.
    assert [row for row in store if row[0] in out.emitted] == [
        ("core/canonical-media-buy-features.json", "/")
    ], store
    # and it really does carry the store, read off the emitted module
    assert "__pydantic_extra__: dict[str, bool]" in _source(
        "core/canonical-media-buy-features.json"
    )
    # and the import it does NOT need is gone.  Read off the typing import line and
    # not off the whole module, because ``ConfigDict(`` contains ``Dict`` -- the same
    # trap the rule in ``compiler.render`` is written to avoid.
    (typing_line,) = [
        line
        for line in _source("core/canonical-media-buy-features.json").splitlines()
        if line.startswith("from typing import ")
    ]
    assert "Dict" not in typing_line.split("import ", 1)[1].split(", "), typing_line

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
    # Non-empty, which is what the loop below needs: the per-site assertion is the
    # obligation and an empty list would satisfy all of it.  The count went 2 -> 11 as
    # documents carrying a DECLARED null beside their type emitted, and it moves again
    # on every row that adds one, so the set is claimed and the size is not.
    claimed("live multi-type property sites", live)
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
    # `hypothesis_jsonschema`, which honours a format it knows).  The residual is
    # NAMED, so a document joining or leaving it is attributable; the count said only
    # that the group had changed size.
    claimed("documents still refused on a constraint inside a container", inner)
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

    # And the naming, as the SET of container positions whose INNER type is a symbol
    # the module imports from ``adcp.types.constraints``.  Both halves non-empty rather
    # than a pair of counts: the claim is that the inner type IS named at a real
    # position in a real module, and (23, 13) was a reading of one emitted tree that
    # every row adding a constrained container moves.
    positions: set[tuple[str, str]] = set()
    modules: set[str] = set()
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
                    positions.add((rel, name.id))
                    modules.add(rel)
    claimed("container positions whose inner type is a named constraint", positions)
    claimed("modules naming an inner constraint type", modules)
    assert {rel for rel, _ in positions} == modules, (sorted(positions), sorted(modules))


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
    claimed("aliases the module declares", declared)
    claimed("aliases the tree imports", imported)
    assert set(imported) - declared == set(), "imported and not declared"
    assert declared - set(imported) == set(), "declared and never named"

    # The denominators, so neither direction can pass over an empty set: every alias is
    # reachable at this one path and nowhere else (no flat root, no second spelling),
    # and the module is not a dumping ground.  Each one is the NON-EMPTINESS of a set
    # and not its size: every count here was over the committed tree, so each one moved
    # as the ``population()`` run grew -- ``declared`` was 133 and is 141 at this base,
    # red on every tree that emitted one more constrained shape -- while the two
    # DIRECTIONS above are what the test is for and they are set equalities already.
    claimed(
        "(module, alias) pairs",
        {(where, alias) for alias, wheres in imported.items() for where in wheres},
    )
    # And the two names that are a DECISION really are annotating fields: ``AdCPUrl`` is
    # ours and ``HttpUrl`` is pydantic's, and D5 points fields at both.
    claimed("modules naming AdCPUrl", imported[constraints_module.URL])
    claimed("modules naming HttpUrl", imported[constraints_module.HTTP_URL])


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
# step 7: D6's six keyword families
# --------------------------------------------------------------------------- #
# **The four tests that stood here are deleted with the machinery they graded.**
# They asserted that ``steps()`` found a site for each of D6's six families, that a
# stepped whole-instance keyword bit the document that states it, that an
# unsatisfiable step reported no_evidence rather than a harness error, and that
# ``force_path`` held a sibling ``if`` through ``then``/``else``.  Every one of them
# graded the step machinery, and section 6 removed it: "a step site asserts that
# ``jsonschema`` rejects a payload violating the schema it was handed. The generated
# class takes no part in the outcome."  So those four tests graded a property of a
# third-party validator and of a mutation helper with no consumer.
#
# **What grades D6's rules instead is immediately below, and it always did.**
# ``RULE_VIOLATIONS`` carries a hand-written payload per rule and routes it through
# ``model_validate`` -- the class's OWN validation, which is where section 6 says an
# an invalid payload reaches pydantic's own validators -- and asserts the keyword
# both halves name.  That
# is the check the deleted four were standing next to rather than doing.


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
    before = [check_pair(pair_of(g)) for g in graded()
              if g.ref.document in carriers and g.ref.pointer == "#"]
    claimed("documents carrying a rule violation fixture", carriers)
    assert len(before) == len(carriers), (len(before), carriers)
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
        assert accepted == len(RULE_VIOLATIONS), (accepted, len(RULE_VIOLATIONS))
        after = [check_pair(pair_of(g)) for g in graded()
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
#: **THE SEVEN RULE KINDS, BY NAME.**  The claim is that every kind the lowering can
#: write IS written from a real bundle node -- a kind nothing writes is dead code -- and
#: that is a statement about the NAMES.  The three counts each kind used to carry
#: (sites, documents, reachable sites) were a reading of one bundle version, and two of
#: them restated what the loop already asserts: the reachable count's own identity is
#: asserted for ``UniqueItems`` below, where it is a property of the lowering and not a
#: coincidence of this bundle.
#:
#: ``NegatedConditional`` is the one kind with NO reachable site: it is written only at
#: nodes inside an ``allOf`` conjunct, which is not a class here at all, so it is named
#: here as the part that is expected to be empty rather than read as a gap.
RULE_KINDS = frozenset(
    {
        "UniqueItems",
        "ForbiddenGroups",
        "RequiredGroups",
        "ConditionalRequired",
        "PropertyCount",
        "Dependencies",
        "NegatedConditional",
    }
)
#: The one kind the bundle gives no node a class can carry the rule at.
UNREACHABLE_RULE_KINDS = frozenset({"NegatedConditional"})


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
    # Named before anything is asserted of the members: an empty walk would make the
    # three clauses below hold over nothing, and "a rule kind nothing writes is dead
    # code" is exactly the claim that cannot be read off an empty measurement.
    claimed("rule kinds written from a bundle node", everywhere)
    measured = {
        kind: (everywhere[kind], len(documents[kind]), reachable.get(kind, 0))
        for kind in everywhere
    }
    assert set(measured) == RULE_KINDS, sorted(measured)  # one nothing writes is dead code
    for kind, (sites, docs, _reachable) in sorted(measured.items()):
        assert sites and docs, (kind, measured[kind])
    # And WHICH kinds have no node a class can carry them at, named rather than read
    # off a zero in a table of counts.
    assert {k for k, (_s, _d, r) in measured.items() if not r} == UNREACHABLE_RULE_KINDS, measured
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

    assert seen == set(RULE_KINDS), seen


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

    1. the bundle still STATES the keyword, counted off ``bundle.nodes`` (the
       population did not go quiet);
    2. the tree carries it, at a NON-EMPTY set of sites, and every one of them is a
       ``properties/<name>`` array whose holding class states ``UniqueItems`` for
       that field -- so a site the lowering missed reddens here;
    3. one of those classes REFUSES a duplicate through ``model_validate``, which is
       the only path a rule is observable on (D4 leaves acceptance to the schema).
    """
    # Direction 1, read off the bundle's own walk rather than off ``steps()``, which
    # section 6 deleted: the step census read 462 sites over these same 198 documents
    # because a step merged the positions stating ONE fact, and the occurrence count
    # is the figure that does not depend on a mutation helper existing.
    stating = [
        (document, pointer)
        for document in bundle.portable(BUNDLE)
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document))
        if isinstance(node, dict) and "uniqueItems" in node
    ]
    # Both denominators, as non-emptiness and not as two counts: the claim is that the
    # keyword has sites in the bundle for direction 2 to find in the tree, and the two
    # figures were a reading of one bundle version (the step census read 462 over these
    # same documents because a step merged the positions stating ONE fact).
    claimed("bundle nodes stating uniqueItems", stating)
    claimed("documents stating uniqueItems", {document for document, _ in stating})

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
    # which iterated that constant's KEYS; it was written at ``438240878`` when it had
    # six names and no ``UniqueItems``, and ``d50d26481`` made ``UniqueItems`` the
    # seventh rule kind and left the line standing -- so it asserted a falsehood about
    # its own module-level constant for months, with no number to re-point.
    # The fact that is true now is the one the kind was added for, and its arithmetic
    # (sites == reachable, over the bundle) is graded by
    # ``test_every_rule_kind_is_written_from_a_real_bundle_node``.
    assert "UniqueItems" in RULE_KINDS, sorted(RULE_KINDS)


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
    # The bundle's own dotted pins, non-empty: the sentence this denominator supports
    # is "the bundle HAS dotted const values while the old spelling emitted none of
    # them", and that is a statement about two sets being non-empty and empty -- the
    # second is asserted on the next line but one.  103 was one bundle version's count
    # of the first.
    claimed("bundle const values carrying a dot", set(dotted))
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
    # The row's reach, as the non-empty set of nodes and documents it covers rather
    # than as a pair of counts over one bundle version.  The facts are the four in the
    # docstring and every one of them is already a set equality or an empty part.
    claimed("bundle nodes stating const", {(d, p) for d, p, _ in nodes})
    claimed("documents stating const", {d for d, _, _ in nodes})
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


def test_identical_content_is_one_class_and_different_content_is_never_one() -> None:
    """D3's content dedup, over every node of every document the whole bundle emits.

    **One class, one name per position, and both halves graded.**  D3's dedup is a
    statement about classes, and D3's naming rule derives a name per POSITION, so the
    emitted shape is one class with an alias at every other position
    (``emit.bind_the_same_node``).  That has two ways to go wrong -- a second CLASS, or a
    name that does not reach the one class -- and the four clauses are one per way plus
    the two directions of the equality.  Each is computed over a population this asserts
    the size of (D14), and each was perturbed and recorded as reddening in
    salesagent-j3k2l.38's notes:

    1. a content group declares one name PER POSITION and they are all distinct, so a
       field cannot be typed by a sibling position's name and a position cannot go
       unnamed.
    2. every one of those names binds ONE OBJECT, by IDENTITY in the imported module.
       This is the clause that says an alias is an alias: if any of them were a second
       class, or an ``Annotated`` wrapper rather than the class, ``is`` would fail here.
       It is also what makes clause 1 safe -- distinct names over one object is the
       intended shape, distinct names over two objects is the defect.
    3. every ADOPTION's two nodes really are identical.  This is the direction that
       matters more than the other three: they can all be satisfied by collapsing
       everything, and this is what says the collapse never joined two nodes the
       document separates.
    4. exactly one position in a group declares the CLASS, and it is the FIRST in the
       document's own key order.  That decides which name the class is spelled with,
       which is public, so a flip in walk order reddens here instead of renaming an
       export.

    **The population is read off the walk's own two records**, ``Emitted.declared`` and
    ``Emitted.adopted``, rather than off the emitted text: a module's text has two class
    statements and no way to say which node each one lowered, which is why the defect
    this grades survived a suite that reads the tree.  The content key is
    ``emit.content_key``, the function the collapse itself is keyed on, so the check and
    the collapse cannot come to disagree about what identical means -- and §9's open
    question is about exactly that disagreement between two instruments.  The one thing
    read off the TREE is the identity in clause 2, because identity is a property of the
    imported module and of nothing else.
    """
    portable = sorted(bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, portable)
    # The document TOTAL is not restated here: it is another test's assertion and it
    # moves whenever a row admits more of the bundle, which would make this check's
    # failure read as a dedup defect.  What this one needs is only that the loop below
    # has documents to run over.
    assert out.emitted, "nothing emitted: every assertion below would pass vacuously"

    groups: set[tuple[str, str]] = set()
    adoptions: set[tuple[str, str]] = set()
    declared: set[tuple[str, str]] = set()
    identities: set[tuple[str, str]] = set()
    unverifiable: set[str] = set()
    for document in sorted(out.emitted):
        doc = bundle.read(BUNDLE, document)
        # The per-pointer facts ``content_key`` reads, built the way ``lower_document``
        # builds them, so the key here is the production key.
        mod = compiler.Module(
            document=document, object_constrained=bundle.constrained_to_object(doc)
        )
        walked = list(bundle.nodes(doc))  # ONE walk: document order, and the nodes
        order = {pointer: i for i, (pointer, _) in enumerate(walked)}
        at = dict(walked)
        by_content: dict[str, list[str]] = {}
        for pointer, node in walked:
            by_content.setdefault(emit.content_key(node, pointer, mod), []).append(pointer)

        here = out.declared[document]
        declared |= {(document, pointer) for pointer in here}
        assert set(here) <= set(at), (document, sorted(set(here) - set(at)))
        # Clause 1's other half, and the one that refuses the reading this row started
        # with: an adopted position DECLARES a name of its own.  Binding the field
        # straight to the class symbol instead leaves the position undeclared, and then
        # every clause below runs over a one-member group and passes.
        assert set(out.adopted[document]) <= set(here), (
            document,
            sorted(set(out.adopted[document]) - set(here)),
        )

        for pointer, symbol in out.adopted[document].items():
            adoptions.add((document, pointer))
            declaring = [p for p, s in here.items() if s == symbol]
            assert len(declaring) == 1, (document, symbol, declaring)
            # Clause 3: the adopting node and the node whose CLASS it took are the same
            # node, and asserted on the NODES rather than on ``content_key``.  The key is
            # the production function, so a key weakened to collapse two different nodes
            # would weaken this comparison in step and the clause would pass vacuously --
            # which is this file's own rule about a fixture derived from the thing it
            # grades.  Python's own equality over the two parsed nodes, plus the one
            # position fact the decision reads, is what the key is supposed to encode.
            assert at[pointer] == at[declaring[0]], (document, pointer, declaring[0])
            assert (pointer in mod.object_constrained) == (
                declaring[0] in mod.object_constrained
            ), (document, pointer, declaring[0])

        for key, pointers in by_content.items():
            reached = [p for p in pointers if p in here]
            if len(pointers) < 2 or not reached:
                continue
            groups.add((document, key))
            # Clause 1: one name per position, all distinct.
            symbols = [here[p] for p in reached]
            assert len(set(symbols)) == len(symbols), (document, key[:120], symbols)
            # Clause 4: exactly one of them declares the CLASS -- the rest adopted it --
            # and it is the first of the group in the document's own key order.
            owning = [p for p in reached if p not in out.adopted[document]]
            assert len(owning) == 1, (document, key[:120], owning)
            assert order[owning[0]] == min(order[p] for p in reached), (document, owning)
            # Clause 2: every one of those names is the SAME OBJECT.  Read off the
            # imported module, because identity is a property of the module and of
            # nothing else -- the text cannot say whether ``X = Y`` produced an alias or
            # a copy.  A module the committed tree does not carry would make this clause
            # silent, so the skip is counted and asserted at 0 below rather than passed
            # over: the tree is written from ``population()`` and this loop runs over the
            # whole portable set, which is the wider of the two.
            if importlib.util.find_spec(out.emitted[document]) is not None:
                module = importlib.import_module(out.emitted[document])
                bound = [getattr(module, s) for s in symbols]
                assert all(b is bound[0] for b in bound), (document, symbols)
                identities |= {(document, s) for s in symbols}
            else:
                unverifiable.add(document)

    # THE DENOMINATORS, each one a named NON-EMPTY set.  A dedup check whose population
    # reaches one instance is the defect salesagent-j3k2l.38 is about -- the ceiling it
    # replaced counted 36 bundle repeats and asserted that 0 were REACHED -- so every
    # one of them is asserted to have members and a run that collapses nothing fails
    # here rather than passing over an empty loop.  ``identities`` is the set of NAMES
    # clause 2 compared, so it is the one that says the identity check ran at all, and
    # ``unverifiable`` is the groups it could not reach, which is the part asserted
    # EMPTY.
    #
    # The five counts this replaces (1426 / 9 / 10 / 19 / 7) all moved together at every
    # row that emitted a module -- ``declared`` went 1413 -> 1426 at
    # ``salesagent-j3k2l.21`` alone -- and none of them is a fact the four clauses do
    # not already assert per member.
    assert unverifiable == set(), sorted(unverifiable)
    claimed("declared (document, pointer) names", declared)
    claimed("content groups reached", groups)
    claimed("adoptions", adoptions)
    claimed("names whose identity clause 2 compared", identities)
    claimed("documents with an adoption", {d for d in out.adopted if out.adopted[d]})


def test_a_refusals_kind_is_declared_by_its_producer_and_a_chain_takes_its_targets() -> None:
    """``Refusal``'s own contract, which is what makes the partition unanswerable by grep.

    Four assertions, one per way the kind could go back to being a reading of
    English:

    * ``kind`` has no default, so a producer cannot omit it and inherit whatever
      the default happens to say.
    * a delegating kind REQUIRES the refusal it delegates to, and a self-answering
      kind refuses one -- so a chained refusal cannot be constructed without the
      target, and ``resolved`` is never a guess.
    * ``resolved`` follows a chain of any depth, by carrying the object and not by
      parsing the sentence the producer writes for the reader.
    * ``is_a_verdict`` refuses a delegating kind rather than answering for it: a
      caller holding one has read ``kind`` where it meant ``resolved``.

    The LAST one is the fix for the instance that reddened the metric by 86: a
    chain onto a DEFERRED target is pending, and the only thing that can say so is
    the target's own declared kind.
    """
    from codegen.refusal import Kind

    with pytest.raises(TypeError):
        Refusal("x", "/", "no kind passed")  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="needs"):
        Refusal("x", "/", "chained with no target", kind=Kind.CHAINED)
    with pytest.raises(TypeError, match="takes no"):
        Refusal(
            "x",
            "/",
            "a target it does not delegate to",
            kind=Kind.VERDICT,
            through=Refusal("y", "/", "t", kind=Kind.VERDICT),
        )

    deferred = Refusal("allOf", "/allOf/0", "a later D2 row lowers this one", kind=Kind.DEFERRED)

    def chain(target: Refusal, at: str) -> Refusal:
        """One link, written once, so a three-link chain has one spelling."""
        return Refusal(
            "$ref", at, f"its target x.json is refused: {target}", kind=Kind.CHAINED, through=target
        )

    one = chain(deferred, "/p")
    two = chain(one, "/q")
    assert (one.kind, one.resolved) == (Kind.CHAINED, Kind.DEFERRED)
    assert (two.kind, two.resolved) == (Kind.CHAINED, Kind.DEFERRED)
    assert refusal_module.is_a_verdict(two.resolved) is False

    final = Refusal("oneOf", "/", "there is no pointer to the conjunction", kind=Kind.VERDICT)
    onto_final = chain(final, "/p")
    assert onto_final.resolved is Kind.VERDICT
    assert refusal_module.is_a_verdict(onto_final.resolved) is True

    with pytest.raises(ValueError, match="delegates"):
        refusal_module.is_a_verdict(Kind.CHAINED)


def test_a_refusal_that_is_a_verdict_is_counted_apart_from_one_that_is_pending() -> None:
    """The exit condition is ``emitted + VERDICTS``, and it is not ``emitted + refused``.

    ``test_every_portable_document_is_emitted_or_refused_by_name`` proves the
    partition is total and disjoint.  It cannot tell a refusal apart from a
    placeholder, and ``emitted + refused == 1054`` is green while nothing does.

    **THE KIND IS AN ARGUMENT ITS PRODUCER PASSES, AND THIS TEST READS NOTHING
    ELSE.**  Four times the number this computes was wrong, always optimistically,
    and every time because the kind of a refusal was decided by reading its
    English.  ``refusal.Kind``'s docstring carries all four.  The first three were
    each fixed by reading the sentence more carefully -- a constant instead of a
    regex, then a recursion through the quoted chain -- and the fourth was the same
    bug again, so the fix is to stop reading it: every producer declares a
    ``Kind``, ``refusal.is_a_verdict`` takes one and holds no string, and this test
    partitions by ``resolved`` rather than by any spelling it could invent.

    Measured on the tree that shared the conjunct reader: of 363 refusals, **155**
    declare ``VERDICT``, **38** declare ``DEFERRED``, **1** declares
    ``UNRESOLVED`` and **169** declare ``CHAINED``; resolving the chains through
    ``through=`` gives **297 VERDICT**, **65 DEFERRED** and **1 UNRESOLVED**.  So
    the exit condition stands at 691 + 297 = **988 of 1054**, with 66 pending.

    **A FIFTH KIND CANNOT BE ABSORBED, which is the thing this test exists for.**
    It asserted ``deferred + transitive + chained_pending + verdicts == total``
    over four buckets it named itself, and that assertion was green through every
    one of the four instances -- a new category just landed in whichever bucket
    its sentence happened not to match.  The partition is now built from the three
    named sets of ``Kind`` members, and the FIRST assertion below is that those
    three cover ``Kind`` exactly.  A new member reddens there before a single
    document is counted, and nothing can route around it, because a ``Kind`` is
    the only thing a producer can pass.
    """
    portable = bundle.portable(BUNDLE)
    out = emit.emit(BUNDLE, portable)

    # **The grading assertion, and it comes first.**  Every ``Kind`` is final,
    # pending or delegating, and no member is two of those -- so a fifth kind is a
    # red test and not a silent reclassification.  Probed by adding a member: this
    # fails, with the member named, before anything below runs.
    named = (
        refusal_module.FINAL_KINDS,
        refusal_module.PENDING_KINDS,
        refusal_module.DELEGATING_KINDS,
    )
    assert set().union(*named) == set(refusal_module.Kind), {
        "a Kind no set names": sorted(set(refusal_module.Kind) - set().union(*named)),
        "named but not a Kind": sorted(set().union(*named) - set(refusal_module.Kind)),
    }
    for i, one in enumerate(named):
        for other in named[i + 1 :]:
            assert one & other == set(), sorted(one & other)
    assert (
        refusal_module.RESOLVED_KINDS
        == refusal_module.FINAL_KINDS | refusal_module.PENDING_KINDS
    )

    assert out.refusals, "no refusals: every assertion below would pass vacuously"

    declared = collections.Counter(r["kind"] for r in out.refusals.values())
    resolved = collections.Counter(r["resolved"] for r in out.refusals.values())

    # A producer cannot emit a kind this partition does not name, and a DELEGATING
    # kind never survives to be counted: ``Refusal.resolved`` follows it at
    # construction.  Both halves are asserted over the population rather than
    # trusted, because both are what the four instances got wrong.
    assert set(declared) <= set(refusal_module.Kind), sorted(
        set(declared) - set(refusal_module.Kind)
    )
    assert set(resolved) <= refusal_module.RESOLVED_KINDS, sorted(
        set(resolved) - refusal_module.RESOLVED_KINDS
    )
    assert sum(resolved.values()) == len(out.refusals), (dict(resolved), len(out.refusals))

    verdicts = {d for d, r in out.refusals.items() if refusal_module.is_a_verdict(r["resolved"])}
    assert len(verdicts) == sum(resolved[k] for k in refusal_module.FINAL_KINDS), len(verdicts)

    # **The chain is graded by what it RESOLVES TO, and both answers must occur.**
    # The old reading took a chained refusal's outer sentence and called all 171 of
    # them verdicts; the reading before that recursed into the quoted text.  Neither
    # is here: the producer passes ``through=`` the target's own refusal and
    # ``Refusal.resolved`` carries the target's answer.  Measured on this tree, 169
    # refusals are chained and they split **142 verdict / 27 deferred** -- so a
    # ``through=`` dropped at that producer would make all 169 resolve to
    # ``CHAINED``, which the assertion above refuses, and a ``through=`` pointed at
    # the wrong refusal would move this split.
    #
    # All three moved with ``salesagent-j3k2l.40``, and the DIRECTIONS are the point:
    # 2 chained refusals became emissions (171 -> 169), and 12 that resolved to
    # DEFERRED now resolve elsewhere -- 10 to VERDICT (132 -> 142) and 2 of them out
    # of the refusal set entirely (39 -> 27).  A chain's floor on the DEFERRED side
    # falls as rows land, so it is re-measured rather than held; what it grades is
    # that both answers still occur, with a denominator beside each.
    #
    # Re-measured again at ``salesagent-j3k2l.28``, in the directions this paragraph
    # already names: 169 -> 166 chained, because 3 more chained refusals became
    # emissions, and the DEFERRED side fell hardest (27 -> 20) because the three
    # refusals that row closed were deferrals that others chained to.  142 -> 146 on
    # the verdict side.
    chained = {d: r for d, r in out.refusals.items() if r["kind"] == refusal_module.Kind.CHAINED}
    # **166 -> 158, 146 -> 144 and 20 -> 14 at ``salesagent-j3k2l.21``, and the
    # DIRECTION is the point these floors exist for.** They fall as rows land: seven
    # of this row's eleven emissions were chained refusals, and
    # ``core/geo-place-requirement.json`` stopped being chained at all -- its target
    # cleared, so it now refuses directly on its own ``pattern``. Eight chains left
    # the refusal set. The deferred side fell hardest again (20 -> 14) because what
    # this row cleared were deferrals that others chained to.
    assert len(chained) >= 158, len(chained)
    split = collections.Counter(r["resolved"] for r in chained.values())
    assert split[refusal_module.Kind.VERDICT] >= 144, dict(split)
    assert split[refusal_module.Kind.DEFERRED] >= 14, dict(split)
    # and the chains run deep enough that the propagation is exercised more than once
    assert (
        max(r["detail"].count(refusal_module.CHAINED_TO_A_REFUSED_TARGET) for r in chained.values())
        >= 5
    ), "no chain deeper than one link: the propagation through through= grades nothing"

    # Shrink-only: a row lands, deferrals become emissions, these fall.
    #
    # **1053 -> 967 and 1 -> 87, moved by `salesagent-j3k2l.37`, and the number
    # FALLING is the instrument working.**  Nothing about what emits changed -- 686
    # before and after, `comparison.added` 0 before and after -- and 86 documents
    # moved out of `verdict` because their producers say in their own text that the
    # lowering for the position has not been written.  47 directly and 39 through a
    # chain.  The rule applied to every one of the 29 live producers, and the table
    # of which producer got which kind, is `docs/plan/j3k2l37-prediction.md`; the
    # three biggest movers are `product.py`'s "a later D2 row lowers this one" (12),
    # `union.py`'s "a branch composes once that reader is shared" (10) and
    # `compiler.py`'s default-on-a-required-property (1 directly, 5 through chains).
    #
    # **967 -> 988 and 87 -> 66, moved by `salesagent-j3k2l.40`**, which shared the
    # conjunct reader: a union BRANCH that composes is lowered by
    # `compiler.lower_composition` with the union base as `bases`, so all 10
    # documents waiting on "a branch composes once that reader is shared" cleared
    # that row -- 3 emitted, 6 accounted as verdicts, and 1 (`adagents.json`) moved
    # on to the NEXT gap, which is why the product row's deferral reads 13 here and
    # 12 before.  12 chained refusals released with them.  `comparison.added` is 0
    # on both trees, measured over every pair of the regenerated tree.
    # `docs/plan/j3k2l40-prediction.md` carries the prediction and its grade.
    #
    # Each pin is the value MEASURED on this tree and each was fire-probed one step
    # tighter (`deferred <= 64`, `unresolved <= 0`, `accounted >= 989`,
    # `chained >= 170`, and the two chain floors at 143 and 28), so each is known to
    # grade rather than to sit loose.  Probed as six separate runs and not as
    # arithmetic over one measurement: the assertions are ORDERED, so a tightened pin
    # that an earlier one pre-empts is never reached and the arithmetic cannot say so.
    assert resolved[refusal_module.Kind.DEFERRED] <= 65, resolved[refusal_module.Kind.DEFERRED]
    assert resolved[refusal_module.Kind.UNRESOLVED] <= 1, resolved[refusal_module.Kind.UNRESOLVED]

    # Grow-only: what the exit condition actually counts.
    accounted = len(out.emitted) + len(verdicts)
    assert accounted >= 988, (accounted, len(out.emitted), len(verdicts))

    # And the gap between the two readings, stated so it cannot be read as closed.
    pending = sum(resolved[k] for k in refusal_module.PENDING_KINDS)
    assert accounted + pending == len(portable), (accounted, pending, len(portable))

    # **A document the pending count loses has to turn up in the EMITTED count**
    # (§6, "and the emitted count never decreases", and the paragraph beginning
    # "The second term exists because the first one makes refusing a legal way to
    # finish a row").  ``accounted >= 988`` counts a verdict and a class alike, so a
    # row that emits its common case and refuses its edge satisfies it either way:
    # `salesagent-j3k2l.40` moved pending 87 -> 66 while emitted rose 686 -> 691 and
    # verdicts 281 -> 297, sixteen of its twenty-one documents resolved by deciding
    # never to generate them, and the figure read that row as the day's largest step.
    #
    # The two terms are COUPLED and that is the whole content of this pin.  Held
    # apart -- ``emitted >= 691`` beside ``pending <= 66`` -- they are both satisfied
    # by refusing a document, because emitted stays 691 while pending falls to 65;
    # the signs are only opposite once clearing a pending document COSTS an emission.
    # ``max(0, ...)`` is the never-decreases half: a bundle that grows the pending set
    # cannot buy back room under the emitted floor.
    #
    # Fire-probed as five runs of this test on this tree, swapping the two literals
    # and nothing else, so each half is perturbed on its own: ``691, 66`` passes (the
    # tree as delivered), ``686, 87`` fails -- that is .40's own trade, 21 cleared for
    # 5 emitted, and it is the instance this pin exists for -- ``691, 76`` fails (ten
    # cleared with emitted flat, a row finished entirely by refusing), ``686, 71``
    # passes (five cleared for the five .40 really emitted), and ``692, 66`` fails on
    # the floor alone with pending unmoved.  The three failures all land HERE and not
    # on an earlier assertion, which the ordering makes worth stating.
    #
    # **RE-POINTED 691, 66 -> 705, 48 BY ``salesagent-j3k2l.28``, AND THE FOUR IT DID
    # NOT EMIT ARE NAMED HERE, which is the only form a re-point may take.**  That row
    # cleared 18 pending: 14 by emitting, and 4 by reaching a VERDICT.  It minted none
    # of those four.  Each is a CHAINED refusal whose first blocker was one of the
    # three one-sided-fold deferrals the row removed, and whose SECOND blocker was a
    # verdict already being produced for its target at ``760e898c6`` -- so the walk got
    # FURTHER and found the real refusal, which is the opposite of the trade this pin
    # exists to refuse.  Measured by A/B against the base's ``codegen/``, with each
    # target's verdict read off its own refusal:
    #
    #   core/targeting-overlay-requirements.json -> core/geo-region-requirement.json
    #       /properties/countries/propertyNames on ``pattern`` (containers._PATTERN_KEY)
    #   core/targeting-overlay-support.json      -> core/geo-region-support.json
    #       the same verdict at the same pointer
    #   media-buy/package-control.json -> core/targeting-input.json ->
    #       core/targeting-unknown-age-eligibility-constraint.json at ``/`` on ``if``:
    #       a root is exactly one kind and this one's is read from ``if``
    #   media-buy/package-update.json  -> core/optimization-goal.json at
    #       /oneOf/0/properties/standard/allOf/0 on ``allOf``: ViewabilityStandard is
    #       an alias, so it cannot be a base (D2)
    #
    # Four producers, none of them that row's, and all four already firing at the base.
    # A re-point whose 4 could not be named and attributed would be the trade wearing
    # this pin's clothes; these can, so the pin moves and the names stay here.
    emitted_pin, pending_pin = 705, 48
    assert len(out.emitted) >= emitted_pin + max(0, pending_pin - pending), {
        "emitted, and its pin": (len(out.emitted), emitted_pin),
        "pending, and its pin": (pending, pending_pin),
        "pending cleared since the pin": pending_pin - pending,
        "emitted gained since the pin": len(out.emitted) - emitted_pin,
        "cleared by refusing instead of emitting": max(0, pending_pin - pending)
        - (len(out.emitted) - emitted_pin),
    }


def test_the_document_type_word_is_not_restated_beside_the_literal() -> None:
    """Measured on the pinned compiler, because the comparison is SYMMETRIC.

    A one-member ``Literal`` renders ``const`` AND the type word of its own accord --
    not a one-member ``enum``, and not the ``const`` alone -- so there is nothing for
    the row to restate and restating it is what would add a fact.  Asserted against
    pydantic here rather than assumed, because which of the three it renders is a
    function of the version and the whole admission below rests on it.

    The TYPELESS const nodes are then the only place the model states a fact the
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
    # Non-empty, which is what the loop below needs: the derivation is asserted at
    # every member, so the denominator's job is to say there are members.  832 was one
    # bundle version's count of them.
    claimed("typeless const nodes", {(d, p) for d, p, _ in typeless})

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
        for name, module in (
            ("compiler", compiler),
            ("union", lower_union),
            ("const", lower_const),
            # ADDED AT ``salesagent-j3k2l.21``, and adding it is the point rather than
            # bookkeeping: ``lower.enum.literal`` builds a ``Literal`` too, and without
            # this entry the walk below could not see it -- the assertion would have gone
            # on reading ``["const"]`` while a second row built the same annotation.
            ("enum", lower_enum),
        )
        for node in ast.walk(ast.parse(inspect.getsource(module)))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Type"
        and any(k.arg == "literals" for k in node.keywords)
    ]
    # **THE INVARIANT IS ONE LOWERING PER KEYWORD, not one builder of ``Literal``**, and
    # D2's amendment is what makes the distinction visible: a ``const`` is a one-member
    # value set and an ``enum`` no name reaches is the same construct with more members,
    # so both render a ``Literal`` and each keyword still has exactly one lowering. Two
    # rows, two keywords; what this refuses is a THIRD builder, or either keyword
    # acquiring a second.
    assert builds == ["const", "enum"], builds
    # The document this row attributes used to be ``core/start-timing.json``, refused on
    # ``type`` at ``/oneOf/0`` for being a scalar branch. It EMITS now -- a union root of
    # scalars is an alias (``salesagent-j3k2l.21``) and its ``const`` branch is the
    # ``Literal`` arm of one -- so the attribution row has no refused document left to
    # point at. Measured over all 1,054 portable documents: **0** are refused on a
    # branch's own non-object type. The row stays, asserted above by resolving the name
    # in ``BRANCH_HANDLED``; what is asserted here instead is the emitted shape, which is
    # the same claim read off the artifact rather than off a refusal.
    module = emit.lower_document("core/start-timing.json", bundle.read(BUNDLE, "core/start-timing.json"))[0]
    assert "Literal['asap']" in "\n".join(b for b in module.blocks), module.blocks
