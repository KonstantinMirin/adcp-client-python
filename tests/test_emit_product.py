"""Step 4: an ``allOf`` root's ``$ref`` conjuncts become bases, and a subclass
never restates an inherited field.

**Its own module, not an addition to ``tests/test_emit.py``.**  Five lanes are
adding a D2 row at once and the test file is the one place every one of them has
to write; a module per row costs an import and removes the collision entirely.
``tests/test_emit.py`` keeps the trunk's own grading, and this module grades one
row.

**The mechanism is graded on a bundle of its own**, the way the reference cycle
is, and for the same reason: ``ΔN`` is 0 (asserted below, with its denominator),
so there is no composing class in the committed tree to read a verdict off.  One
of the probe bundle's three documents is this bundle's OWN
``core/version-envelope.json``, copied byte for byte, so the inherited
``ge=1, le=99`` the control asserts on is the bundle's text and not the test's
idea of it.

**The probe's shape is the population's majority shape**, which was measured
rather than guessed: of the 287, 159 declare ``additionalProperties: true`` at
the root, 71 are silent and 57 declare ``false``.  The 57 matter and are not what
this probe is: draft-07 does not evaluate ``additionalProperties`` across
``allOf``, so a strict root forbids every key only a conjunct declares -- which is
why ``version-envelope.json``'s own description says a strict request schema
redeclares the two version fields in its own ``properties``.  Measured over the
57: **all 57 redeclare every ``$ref`` conjunct's property**, so the bundle has no
document in that trap and a probe built in it would grade a state the population
does not have.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pydantic
import pytest

from adcp.types import _base, constraints
from codegen import bundle, compiler, emit
from codegen import constraints as constraints_module
from codegen.harness import Pair, check_pair, steps
from codegen.lower import product
from codegen.refusal import Refusal

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
#: Every reference in this bundle is spelled against this base; ``document_for``
#: derives the document from the bundle's own file set, so the probe uses the
#: same spelling rather than a shorter one that would resolve by accident.
REF = "https://adcontextprotocol.org/schemas/3.2.4/{}"

ENVELOPE = "core/version-envelope.json"


def composing() -> list[str]:
    """This step's population, read through the row's own selector."""
    return [d for d in bundle.portable(BUNDLE) if bundle.composes_at_the_root(bundle.read(BUNDLE, d))]


# --------------------------------------------------------------------------- #
# the population, and the arithmetic over it
# --------------------------------------------------------------------------- #
def test_the_population_is_the_one_this_step_is_stated_over() -> None:
    """**287**, and the definition is what lands on that number.

    A verdict read off a population nobody counted is a verdict over however many
    documents there turned out to be, including none.  The three competing
    readings are asserted beside it, because each one is a number somebody could
    have meant and each gives a different answer.
    """
    docs = bundle.portable(BUNDLE)
    read = [bundle.read(BUNDLE, d) for d in docs]
    assert len(composing()) == 287  # allOf at the root, NO union beside it

    root_allof = [d for d in read if isinstance(d.get("allOf"), list)]
    anywhere = [d for d in read if "allOf" in bundle.schema_keywords(d)]
    only_root = [
        d
        for d in root_allof
        if not any("allOf" in n for p, n in bundle.nodes(d) if p)
    ]
    assert len(root_allof) == 342, "any root allOf, union or not"
    assert len(anywhere) == 401, "allOf anywhere in the document"
    assert len(only_root) == 257, "allOf at the root and nowhere else"
    # The union clause is what makes the two rows disjoint, and this is its cost.
    assert len(root_allof) - len(composing()) == 55, "documents step 5's row takes"


def test_the_union_clause_is_what_keeps_the_rows_disjoint() -> None:
    """A root ``allOf`` applies to the whole document in draft-07, so it reaches
    EVERY branch of a root ``oneOf``.

    A row that lowered the conjuncts of a union root without the branches would
    apply the bases to some branches and not others, which is the defect D7 names.
    So the 55 documents carrying both belong to step 5's row whatever else they
    carry, and this row declines them -- which is not a preference, it is the
    reason ``emit.lower_document`` can fail on a two-row document instead of
    choosing.
    """
    both = [
        d
        for d in bundle.portable(BUNDLE)
        if isinstance((doc := bundle.read(BUNDLE, d)).get("allOf"), list)
        and any(k in doc for k in ("oneOf", "anyOf"))
    ]
    assert len(both) == 55
    assert not set(both) & set(composing())
    for d in both:
        assert not bundle.composes_at_the_root(bundle.read(BUNDLE, d)), d


def test_a_required_only_conjunct_has_no_population_so_the_arm_is_not_built() -> None:
    """The plan's third output for this row, deliberately absent.

    A derivation matching nothing is green for free and says nothing, so the arm
    is not written -- and this is the measurement that says so, over the whole
    bundle rather than over this step's population.
    """
    found = []
    for d in bundle.portable(BUNDLE):
        for i, c in enumerate(bundle.read(BUNDLE, d).get("allOf") or []):
            if isinstance(c, dict) and {
                k for k in c if k not in compiler.ANNOTATIONS and not k.startswith("x-")
            } == {"required"}:
                found.append(f"{d}#/allOf/{i}")
    assert found == []


def test_the_rows_delta_is_reported_with_its_denominator() -> None:
    """**ΔN = 0. N = 43 of 1,054.**  Measured both ways in one process.

    The plan's step table implies the volume of a 287-document population; it
    arrives with steps 5-7 and not here.  Reported rather than explained: a low
    number is not a failure, and a number with no denominator is not a result.

    What the row DOES change is the refusal's attribution, and in the honest
    direction -- a document that used to refuse at the root on ``allOf`` now
    refuses on the keyword that actually stopped it, inside the conjunct or in a
    document it composes.
    """
    docs = bundle.portable(BUNDLE)
    read = lambda d: bundle.read(BUNDLE, d)  # noqa: E731
    pop = sorted(
        {
            d
            for d in docs
            if bundle.is_leaf_object(read(d))
            or bundle.references_a_property(read(d))
            or bundle.composes_at_the_root(read(d))
        }
    )
    assert len(pop) == 587

    with_row = emit.emit(BUNDLE, pop)
    # Removing THIS row from the merged table, rather than emptying it: the other
    # rows are other steps' and a verdict read with them absent is a verdict about
    # a table nobody runs.
    saved = emit.ROWS
    try:
        emit.ROWS = tuple(r for r in saved if r[0] is not bundle.composes_at_the_root)
        without = emit.emit(BUNDLE, pop)
    finally:
        emit.ROWS = saved

    assert len(docs) == 1054
    # N over this population is 188 on the merged table (43 when this lane measured
    # it alone, before the other four steps' rows were beside it), and the row moves
    # it by 0.
    # 217 and not 214: `salesagent-j3k2l.20` moved `governance/policy-entry.json`'s
    # refusal off the root -- it stopped at `$defs` before any of its 8 property
    # references was read -- so the closure now reaches the three enum documents its
    # earlier properties name. The row itself still moves N by 0.
    # 218 and not 217, and the one gained is `enums/reach-unit.json`:
    # `salesagent-j3k2l.18` lowers a composition BELOW a root through
    # `emit._decide`, so `core/frequency-cap.json` -- reached transitively, not in this
    # population -- no longer stops at `/properties/suppress` (a bare-`$ref` `allOf` at
    # a property) and the walk reaches `/properties/per`, where binding that conjunct
    # emits its target. The document itself still refuses, at
    # `/properties/per/allOf/0`, because `ReachUnit` is D2's root-scalar ALIAS and
    # subclassing one is a TypeError -- so this is a refused document's target being
    # emitted, which is what the transitive walk has always done. The row itself still
    # moves N by 0.
    assert len(with_row.emitted) == 218, "N, over a bundle of 1,054"
    # **The row DOES emit now, and it did not when this lane measured alone.**  On
    # its own branch the conjuncts' targets refused and took their referrers with
    # them, so the delta was 0 and the row's value was the attribution it moved.  On
    # the merged table steps 3, 5 and 6's rows emit those targets, so the composing
    # documents follow: 22 of the 287 are emitted BY this row, and removing it loses
    # 31 modules -- the emitted documents plus those reached only through a reference.
    # That is joint unblocking measured from this side -- the row's own 0 was a fact
    # about which other rows existed, not about the row.
    #
    # 34 and not 31: the three documents `salesagent-j3k2l.20` added to N above are
    # reached through `governance/policy-entry.json`, which this row's own population
    # is what reaches, so removing the row loses them too.
    # 35 and not 34: the same `enums/reach-unit.json`. `core/frequency-cap.json` is
    # reached only through a document this row emits, so with the row removed the walk
    # never arrives at it and never binds that conjunct's target -- the without-row
    # count is unchanged at 183, measured, so the whole of the move is on the with-row
    # side.
    assert len(with_row.emitted) - len(without.emitted) == 35
    assert len(set(composing()) & set(with_row.emitted)) == 22
    assert set(without.refusals) - set(with_row.refusals) == set(composing()) & set(
        with_row.emitted
    )
    # Every document of the population is accounted for by name, pointer and keyword.
    assert set(pop) <= set(with_row.emitted) | set(with_row.refusals)
    for document, row in with_row.refusals.items():
        assert row["keyword"] and row["pointer"] and row["detail"], document
    # The ATTRIBUTION moved for all 287.  Without the row a composing document is
    # claimed by nothing and refuses at the root on ``type``; with it, the walk
    # reaches the conjuncts and either emits the document or names the keyword that
    # actually stopped it.
    moved = [
        d
        for d in composing()
        if with_row.refusals.get(d, {}).get("keyword")
        != without.refusals.get(d, {}).get("keyword")
    ]
    assert len(moved) == 287


def test_a_document_two_rows_select_is_a_build_failure_and_not_a_precedence_puzzle() -> None:
    """The table is unordered, graded by registering a second row that collides.

    Unreachable at one row, which is exactly why it gets a test that manufactures
    the second: an ordered chain would make precedence a property of where a lane
    inserted its line, and five lanes are inserting lines now.  The failure is an
    ``AmbiguousRoot`` and not a ``Refusal``, because a document two rows claim is a
    defect in their SELECTORS and a refusal would file it against the document and
    let the build pass.
    """
    doc = bundle.read(BUNDLE, "media-buy/get-products-request.json")
    assert bundle.composes_at_the_root(doc)
    saved = emit.ROWS
    try:
        emit.ROWS = (*saved, (bundle.composes_at_the_root, product.lower_composition))
        with pytest.raises(emit.AmbiguousRoot, match="composes_at_the_root"):
            emit.lower_document("media-buy/get-products-request.json", doc)
    finally:
        emit.ROWS = saved
    # and the same document goes back to one row once the table is restored
    assert len([r for r in emit.ROWS if r[0](doc)]) == 1


# --------------------------------------------------------------------------- #
# the probe bundle
# --------------------------------------------------------------------------- #
#: The restatement that is this step's highest-value defect: it states a default
#: and a description and NOTHING about the instance, over a base field typed
#: ``integer`` with ``minimum: 1, maximum: 99``.  31 of the previous generated
#: tree's 42 ``Any`` fields were this, shadowing a typed base field across 15
#: classes.  ``formats/canonical/responsive_creative.json`` is the population's
#: own instance, over ``formats/canonical/_base.json``.
SHADOW = {"default": 1, "description": "restated, and states no fact"}


def _probe(tmp_path: Path, *, own: dict[str, Any], name: str) -> Path:
    """Write the three-document probe bundle and return its directory."""
    at = tmp_path / name
    (at / "core").mkdir(parents=True)
    # BYTE FOR BYTE: the inherited bound the control asserts on is the bundle's text.
    shutil.copyfile(BUNDLE / ENVELOPE, at / ENVELOPE)
    (at / "core/probe-marker.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Marker",
                "type": "object",
                "required": ["kind"],
                "properties": {
                    "kind": {"type": "string", "minLength": 2, "description": "the marker"}
                },
            },
            indent=2,
        )
    )
    (at / "core/probe-composing.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Probe Composing",
                "type": "object",
                "allOf": [
                    {"$ref": REF.format("core/probe-marker.json")},
                    {"$ref": REF.format(ENVELOPE)},
                ],
                "properties": own,
                "required": ["label"],
                "additionalProperties": True,
            },
            indent=2,
        )
    )
    return at


def install_run_aliases(out: emit.Emitted, monkeypatch) -> list[str]:
    """Install a RUN's own D5 aliases onto ``adcp.types.constraints``, reversibly.

    Returns the symbols it added, so a caller can assert the probe reached the row
    at all rather than trusting that it did.

    Nothing is overwritten and nothing can be: an alias's NAME is a function of its
    constraint (``codegen.constraints.symbol``, with ``check_injective`` failing the
    build if two shapes ever derive one name), so a symbol present in both the
    bundle's module and a probe run's module is the same annotated type in both.
    Only the names the installed module lacks are added, and ``monkeypatch``
    removes them when the test ends.
    """
    namespace: dict[str, Any] = {}
    exec(out.beside["constraints.py"], namespace)  # noqa: S102 -- the emitter's own output
    added = []
    for symbol, value in namespace.items():
        if symbol.startswith("_") or not symbol[:1].isupper() or hasattr(constraints, symbol):
            continue
        monkeypatch.setattr(constraints, symbol, value, raising=False)
        added.append(symbol)
    return sorted(added)


def _emit_probe(tmp_path: Path, monkeypatch, *, own: dict[str, Any], name: str):
    """Emit the probe bundle, import its tree, and return (class, module text, schema).

    ``strict_validate`` reaches a document through ``_base._document``, which reads
    the INSTALLED package, so the probe's documents are reached by pointing that
    one function at the probe tree.  ``_document`` is ``lru_cache``d: the patch
    replaces the whole cached function rather than seeding it, so the real cache
    is untouched and nothing of the probe outlives the test -- a probe binding
    that outlived its test is a measured failure of this project's.

    **D5's alias module is reached the same way and takes the same kind of
    patch.**  An emitted module names ``adcp.types.constraints`` ABSOLUTELY, just
    as it names ``adcp.types._base``, so the probe's tree imports the INSTALLED
    module -- which declares the aliases the BUNDLE's shapes derive and not the
    probe's, and the probe marker's ``minLength: 2`` derives one the bundle has no
    site for.  The probe RUN emitted its own alias module
    (``Emitted.beside``), so that is what is installed, for this test only.
    """
    at = _probe(tmp_path, own=own, name=name)
    documents = sorted(str(p.relative_to(at)) for p in at.rglob("*.json"))
    out = emit.emit(at, documents)
    assert out.refusals == {}, out.refusals
    tree = tmp_path / "pkg" / name
    emit.write(out, tree)
    install_run_aliases(out, monkeypatch)
    monkeypatch.setattr(
        _base, "_document", lambda document: json.loads((tree / document).read_text())
    )
    monkeypatch.syspath_prepend(str(tmp_path / "pkg"))
    module = importlib.import_module(f"{name}.core.probe_composing")
    for mod in [m for m in sys.modules if m.startswith(name)]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    return (
        module.ProbeComposing,
        (tree / "core/probe_composing.py").read_text(),
        json.loads((tree / "core/probe-composing.json").read_text()),
    )


def test_a_ref_conjunct_becomes_a_base_in_the_documents_own_conjunct_order(
    tmp_path, monkeypatch
) -> None:
    """D7: every base an emitted class has is a schema its document composes.

    Derived, so there is no marker policy and no filename to classify.  The order
    is the document's conjunct order, which is also what makes a response
    composing both envelopes read as its document does.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4base",
        own={"label": {"type": "string", "minLength": 2}},
        )
    assert [b.__name__ for b in cls.__bases__] == ["ProbeMarker", "AdCPVersionEnvelope"]
    assert "class ProbeComposing(ProbeMarker, AdCPVersionEnvelope):" in text
    # AdCPBaseModel arrives THROUGH the bases and is not named a second time.
    assert "AdCPBaseModel" not in text
    assert issubclass(cls, _base.AdCPBaseModel)
    # The import is the module writer's, derived from the two document paths (D1).
    assert "from .probe_marker import ProbeMarker" in text
    assert "from .version_envelope import AdCPVersionEnvelope" in text


def test_a_subclass_never_restates_an_inherited_field(tmp_path, monkeypatch) -> None:
    """The one merge rule, and the shadow it makes unspellable.

    The restatement states a default and a description and nothing about the
    instance, so it adds nothing: the field is INHERITED and the subclass declares
    no field for it.  The assertion is on the module TEXT as well as on the class,
    because what the defect looked like was a line in a class body.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4shadow",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    # A DECLARED field is a name in the class body, read without reference to how
    # its annotation is spelled: D5 puts a constraint on the TYPE, so a declared
    # field is now ``label: StrMinLen2`` and the previous instrument -- which
    # looked for ``": Annotated"`` -- found none and passed an EMPTY list against
    # ``["label"]``.  An instrument keyed on the rendering reports a restatement
    # that is there as absent the moment the rendering moves, which is the
    # direction that matters: it would have said this rule holds while a subclass
    # shadowed every inherited field.
    body = [line for line in text.splitlines() if line.startswith("    ") and ":" in line]
    declared = [
        name
        for name in (line.strip().split(":")[0] for line in body)
        if name.isidentifier() and not name.startswith("__")
    ]
    assert declared == ["label"], text
    assert "adcp_major_version" not in text, "the inherited field is restated"
    # P2: no second spelling of anything the base states.
    assert "ge=1" not in text and "le=99" not in text and "99" not in text, text
    assert "Any" not in text, "the restatement lowered on its own would be Any"
    # and the field is still THERE, with the base's own declaration
    assert cls.model_fields["adcp_major_version"].annotation is not Any


def test_the_composed_field_set_is_the_union_and_requiredness_is_inherited(
    tmp_path, monkeypatch
) -> None:
    """A field the subclass does not declare keeps the base's requiredness,
    because there is nothing of the subclass's to override it.

    That closes "41 subclass fields optional where their base requires them" by
    construction rather than by a check: ``kind`` is required by conjunct 0 and
    appears in neither the root's ``properties`` nor its ``required``.
    """
    cls, _, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4fields",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    assert sorted(cls.model_fields) == ["adcp_major_version", "adcp_version", "kind", "label"]
    assert sorted(k for k, f in cls.model_fields.items() if f.is_required()) == ["kind", "label"]
    assert schema["required"] == ["label"], "the document's root requires only its own"
    assert "kind" not in schema["properties"], "and declares nothing about kind"


def test_the_inherited_bound_is_live_on_the_model_validate_path(tmp_path, monkeypatch) -> None:
    """**The control, and it asserts on ``model_validate`` for a measured reason.**

    The brief's probe was "make a subclass redeclare an inherited field and
    confirm the refuses check catches the widening".  It does not.  Both of the
    first two checks call ``strict_validate``, whose schema half decides against
    the document before anything is constructed, so the document refuses whatever
    the annotations say: measured, a class carrying ``Any = None`` over this
    typed base field grades identically to this one, and so does a class with no
    bases at all.

    The widening is on the ``model_validate`` path, which D4 keeps public and
    which builds WITHOUT consulting the schema.  So that is where the inherited
    bound is asserted, and the value asserted on -- ``ge=1, le=99`` -- is
    ``core/version-envelope.json``'s own text, copied into the probe byte for
    byte.
    """
    cls, _, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4bound",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    ok = cls.model_validate({"kind": "ab", "label": "xy", "adcp_major_version": 5})
    assert ok.adcp_major_version == 5
    for bad, expected in ((0, "greater_than_equal"), (100, "less_than_equal"), ("nope", "int_parsing")):
        with pytest.raises(pydantic.ValidationError) as caught:
            cls.model_validate({"kind": "ab", "label": "xy", "adcp_major_version": bad})
        assert caught.value.errors()[0]["type"] == expected, bad


def test_a_narrowing_restatement_is_declared_by_the_subclass(tmp_path, monkeypatch) -> None:
    """The other half of the rule: a restatement that NARROWS is the subclass's.

    It keeps every keyword the inherited declaration states, with the same value,
    and adds at least one -- so the subclass's declaration is the intersection and
    nothing of the base's is dropped.  2 of the population's 100 restatement
    sites are this.

    **Asserted on the live metadata, and on the symbol the constraint DERIVES.**
    D5 puts a constraint on the type, so the module no longer spells
    ``min_length=2, max_length=8`` in this class at all -- it names a type that
    carries both. Asserting the old text would pass only while the rendering
    stood still, and asserting the alias's name alone would grade a string; so
    the name is asked of ``codegen.constraints`` rather than written here (a
    literal would pin whatever the namer currently does), and the bounds
    themselves are read off the field, which is what the widening would move.
    """
    cls, text, _ = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4narrow",
        own={
            "kind": {"type": "string", "minLength": 2, "maxLength": 8, "description": "the marker"},
            "label": {"type": "string", "minLength": 2},
        },
    )
    named = constraints_module.symbol("string", {"minLength": 2, "maxLength": 8})
    assert f"kind: Annotated[{named}" in text, text
    live = cls.model_fields["kind"].metadata
    bounds = {
        attr: getattr(m, attr) for m in live for attr in ("min_length", "max_length") if hasattr(m, attr)
    }
    assert bounds == {"min_length": 2, "max_length": 8}, live
    assert len(live) == 2, live  # and nothing else was invented alongside them
    assert cls.model_validate({"kind": "ab", "label": "xy"}).kind == "ab"
    for bad in ("a", "abcdefghi"):  # the base's floor, then the subclass's ceiling
        with pytest.raises(pydantic.ValidationError):
            cls.model_validate({"kind": bad, "label": "xy"})


def test_the_accepts_and_refuses_checks_are_green_with_a_denominator(
    tmp_path, monkeypatch
) -> None:
    """Checks 1 and 2 over the probe, with the refuses check's count asserted.

    A green mark without the count beside it says nothing: a pair no instance
    reached leaves every step unrun, and ``PairReport.outcome`` refuses a zero
    denominator for exactly that reason.
    """
    cls, _, schema = _emit_probe(
        tmp_path,
        monkeypatch,
        name="s4checks",
        own={"adcp_major_version": SHADOW, "label": {"type": "string", "minLength": 2}},
    )
    rep = check_pair(Pair("probe", schema, cls, cls.strict_validate))
    assert rep.accepts is not None and rep.accepts.outcome == "pass", rep.accepts
    assert [r.outcome for r in rep.refuses] == ["pass"] * 4, [
        (r.keyword, r.outcome, r.harness) for r in rep.refuses
    ]
    assert rep.graded_instances == 100, rep.graded_instances
    assert rep.step_sites == 7
    # The document states a constraint in BOTH halves -- its own properties and
    # its conjuncts -- and the step list reaches both, which is what says the
    # composed document was graded and not just the root.  ``_spread`` takes one
    # step per keyword, and ``minLength`` is stated in both halves, so the four
    # it chose all happen to sit in a conjunct.
    assert {s.pointer.split("/")[1] for s in steps(schema)} == {"", "allOf", "properties"}
    assert {r.pointer.split("/")[1] for r in rep.refuses} == {"allOf"}


# --------------------------------------------------------------------------- #
# what refuses, by name, pointer and keyword
# --------------------------------------------------------------------------- #
def _lower(doc: dict, binder=emit._no_binder) -> str:  # noqa: SLF001 -- the test is the caller
    return product.lower_composition(doc, "Probe", "", emit.Module(document="probe.json", bind=binder))


def test_an_incompatible_restatement_refuses_by_name_pointer_and_keyword() -> None:
    """Under ``allOf`` BOTH declarations apply, so the effective accepted set is
    their intersection -- and an annotation carrying only the restatement would be
    WIDER than the document.

    4 of the population's 100 restatement sites are incompatible, so this arm has
    a population and is not a guard.  Graded on two local declarations of one key,
    which needs no binder: the rule that decides them is the same symmetric one.
    """
    doc = {
        "title": "Probe",
        "type": "object",
        "properties": {"n": {"type": "integer", "minimum": 1}},
        "allOf": [{"properties": {"n": {"type": "integer", "minimum": 2}}}],
    }
    with pytest.raises(Refusal) as caught:
        _lower(doc)
    assert caught.value.keyword == "minimum"
    assert caught.value.pointer == "/allOf/0/properties/n"
    assert "neither declaration narrows the other" in caught.value.detail


def test_the_rule_is_symmetric_so_the_order_the_declarations_are_read_in_cannot_decide() -> None:
    """There is no "last wins" to come back to.

    A generator that let the later conjunct win made its accepted set a function
    of member order, which is invisible in the output.  Asserted on the decision
    itself, over the four outcomes it has to distinguish.
    """
    typed = {"type": "integer", "minimum": 1}
    assert product._restatement({"default": 1}, typed) is False  # annotation-only: inherited
    assert product._restatement(dict(typed), typed) is False  # identical: inherited
    assert product._restatement({**typed, "maximum": 9}, typed) is True  # narrows
    assert product._restatement({"type": "integer", "minimum": 2}, typed) is None  # conflicts
    # symmetric: swapping the arguments of a conflict is still a conflict, and
    # swapping a narrowing reports the other direction rather than agreeing
    assert product._restatement(typed, {"type": "integer", "minimum": 2}) is None
    assert product._restatement(typed, {**typed, "maximum": 9}) is None


@pytest.mark.parametrize(
    ("conjunct", "keyword"),
    [
        # a $ref with a sibling is not a base, and the SIBLING is the cause
        ({"$ref": "x", "minimum": 1}, "minimum"),
        ({"enum": ["a", "b"]}, "enum"),  # the enum narrowing: step 3's row
        ({"required": ["a"], "not": {}}, "not"),
        ({"type": "object", "properties": {"a": {}}, "additionalProperties": False}, "additionalProperties"),
    ],
)
def test_a_conjunct_this_row_does_not_lower_refuses_by_its_own_keyword(
    conjunct: dict, keyword: str
) -> None:
    """A conjunct is a ``$ref`` (a base) or an inline object with ``properties``.

    Everything else is a later D2 row and refuses on the keyword that stopped it,
    at the conjunct's own pointer -- not on ``allOf``, which would name the
    position rather than the cause.  The ``enum`` case is the population's §4.3
    narrowing (``media-buy/media-buy-commitment-response.json``, and
    ``formats/canonical/image.json``'s ``motion_level``): the intersection of an
    enum with a referenced enum needs step 3's lowering and cannot be stated here.
    """
    doc = {"title": "Probe", "type": "object", "allOf": [conjunct]}
    with pytest.raises(Refusal) as caught:
        _lower(doc)
    assert caught.value.keyword == keyword, caught.value.detail
    assert caught.value.pointer == "/allOf/0"


def test_a_scalar_root_cannot_be_a_base_and_refuses_rather_than_writing_the_module() -> None:
    """D2 makes a scalar root an ``Annotated`` alias, and subclassing an alias is
    a ``TypeError`` at import.

    ``Target.shape`` is ``None`` for a target that is not a class, which is the
    whole of the test: the binder answers with the shape it wrote, so a lowering
    cannot mistake an alias for a class.
    """
    doc = {"title": "Probe", "type": "object", "allOf": [{"$ref": "x"}]}
    with pytest.raises(Refusal) as caught:
        _lower(doc, lambda uri, pointer: emit.Target("..core.brand_id", "BrandID", None))
    assert caught.value.keyword == "allOf"
    assert "cannot be a base" in caught.value.detail


def test_a_keyword_at_the_root_beside_the_conjunct_list_refuses() -> None:
    """The root may carry its own ``properties``, ``required``, ``type`` and
    ``additionalProperties`` beside ``allOf``, and nothing else.

    64 of the 287 refuse first on ``if`` at the root: that is step 7's keyword, and
    this row reports it rather than lowering a document whose conditional it ignores.

    ``definitions`` was in this list and is NOT a keyword this row reports any more.
    15 of the 287 refused on it here; since `salesagent-j3k2l.20` a section is admitted
    at every node by ``compiler.check_keywords`` -- it asserts nothing about an
    instance, and the entries a ``$ref`` names are declared when it asks -- so the 15
    now refuse on whatever is inside the conjunct or the section, which is this row's
    own honest-attribution point one level deeper.
    """
    for keyword in ("if", "not", "minProperties"):
        doc = {"title": "Probe", "type": "object", "allOf": [{"$ref": "x"}], keyword: {}}
        with pytest.raises(Refusal) as caught:
            _lower(doc)
        assert caught.value.keyword == keyword
        assert caught.value.pointer == "/"
