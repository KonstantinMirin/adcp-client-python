"""``required`` naming a property NO declaration declares: the field, and the fold.

§5's ``required`` row and §8's empty-schema clause, graded together, because neither
half is correct on its own and that is the whole history of this row: the row called
such a name "a presence rule with no field", a rule renders no ``required`` into a
model's JSON schema while the keyword's own cell is ``rendered=True``, so the rule half
reported ``differs`` at the node's ``/required`` -- and the field half reported the
model-only ``properties`` entry as ``added``, which §8 had no fold for.  Both halves
were red, so the handler refused and **27 of the 95 refusals, 5 of them primary**, stood
on a conflict between two of this compiler's own decisions with no document at fault.

**The claim is about an ACCEPTED SET, so every test here states it with
``jsonschema``.**  "``required: ['x']`` with no declaration for ``x`` admits an object
carrying ``x`` with any value" is a claim about the document, not about the rendering, so
the document's own validator says it first and the model is then asked to agree -- in
both directions, because a field that made the model refuse a payload the document
admits is the narrowing §2 forbids outright, and ``Any`` is only exact if it refuses
nothing.

The negative case -- a required name the BRANCHES of a union declare, which is
``_ROOT_REQUIRED`` and not a field -- lives in
``tests/test_inner_facts.py::test_a_root_required_the_branches_declare_is_root_required_and_not_a_field``
and is not repeated here.  It is the one thing that keeps this answer off a union base,
and ``compiler.fields``' ``carried`` argument is the seam between the two.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import ValidationError

from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, compiler, emit, harness
from tests.nodeset import claimed

DRAFT = "http://json-schema.org/draft-07/schema#"
SOURCE = Path("schemas/cache/3.2")

#: The five documents of the bundle whose ``required`` names a key no declaration
#: declares at a position a CLASS is cut at, and the six nodes they state it at.
#: Derived below rather than trusted: this is the value pin, and
#: :func:`test_the_bundle_population_is_the_one_this_row_claims` is the derivation.
#:
#: Pinned as a SET of sites and not as a count, for §8's reason: a count over the
#: emitted population rises when the emitter emits more, and these are positions of the
#: bundle SOURCE, which does not move when a row lands.
SITES = {
    ("core/format.json", "#/$defs/baseGroupAsset", ("asset_type",)),
    ("core/format.json", "#/$defs/baseIndividualAsset", ("asset_type",)),
    (
        "core/rights-attestation-evaluation.json",
        "#/properties/reference/allOf/1/properties/subject",
        ("namespace", "id", "content_digest"),
    ),
    (
        "core/rights-constraint.json",
        "#/properties/attestation_refs/items/allOf/1/properties/subject",
        ("namespace", "id", "content_digest"),
    ),
    ("creative/validate-input-result.json", "#/properties/warnings/items", ("field",)),
    ("extensions/extension-meta.json", "#", ("$id",)),
}


def _write(tmp_path: Path, documents: dict[str, dict]) -> Path:
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


def _model(document: str, out: emit.Emitted, tag: str) -> Any:
    """The emitted module's root symbol, EXECUTED rather than inspected.

    ``tests/test_inner_facts.py``'s reading, and for its reason: a test that inspects
    the rendered text passes on a rendering that does not run, and this row's claim is
    about an accepted set.  The relative import lines go because the sibling modules do
    not exist here, and these fixtures reference nothing.
    """
    text = out.files[document.replace(".json", ".py")]
    module = types.ModuleType(f"_required_no_declaration_{tag}")
    sys.modules[module.__name__] = module
    try:
        exec(  # noqa: S102 -- executing the compiler's own output is the point
            "\n".join(x for x in text.splitlines() if not x.startswith("from .")),
            module.__dict__,
        )
    finally:
        del sys.modules[module.__name__]
    return module.__dict__[module.__all__[0]]


def _probe(**extra: Any) -> dict:
    """One object root requiring a key its ``properties`` does not declare.

    ``extensions/extension-meta.json``'s own shape at ``/``, minus the size: a declared
    property, a required name with no entry anywhere in the document, and silence about
    ``additionalProperties`` -- which §2 reads as ``ignore``, so the key is permitted and
    the document says nothing else about its value.
    """
    return {
        "title": "Probe",
        "type": "object",
        "properties": {"known": {"type": "string"}},
        "required": ["known", "undeclared"],
        **extra,
    }


# --------------------------------------------------------------------------- #
# the field, and that it is EXACT
# --------------------------------------------------------------------------- #
def test_a_required_name_no_declaration_declares_is_a_required_any_field(tmp_path) -> None:
    """The document's accepted set, then the model's, then that they are the same one.

    Three claims, and the middle one is the row:

    * the DOCUMENT admits an object carrying the key with ANY value and refuses one
      omitting it -- stated with ``jsonschema`` over four values of three JSON types,
      because "any value" is the fact ``Any`` is chosen for and one value would not say
      it;
    * the model carries a REQUIRED FIELD for the key, under the document's own spelling,
      and the field's annotation states nothing;
    * the model accepts each of those four payloads and refuses the one the document
      refuses, reporting the absence on the DOCUMENT's own key.

    A model that dropped the name instead would accept the payload the document refuses,
    which is the widening this row declines to take because an exact answer exists.
    """
    document = _probe()
    judge = jsonschema.Draft7Validator(document)
    admitted = [
        {"known": "k", "undeclared": "a string"},
        {"known": "k", "undeclared": 7},
        {"known": "k", "undeclared": None},
        {"known": "k", "undeclared": {"nested": [1, 2]}},
    ]
    for payload in admitted:
        assert judge.is_valid(payload), payload
    assert not judge.is_valid({"known": "k"}), "the document demands the key"

    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    model = _model("core/probe.json", out, "field")

    rendered = model.model_json_schema()
    assert sorted(rendered["required"]) == ["known", "undeclared"], rendered["required"]
    # The field states NOTHING: the entry pydantic renders for it is the empty schema
    # plus a title, which is what ``harness._states_no_graded_fact`` folds and what makes
    # the answer exact rather than a widening with a declaration.
    assert set(rendered["properties"]["undeclared"]) <= {"title"}, rendered["properties"]
    assert out.approximations == {}, "an exact answer owes no declaration"

    for payload in admitted:
        assert model.model_validate(payload) is not None, payload
    with pytest.raises(ValidationError) as err:
        model.model_validate({"known": "k"})
    assert {(e["type"], e["loc"]) for e in err.value.errors()} == {("missing", ("undeclared",))}


def test_the_field_takes_the_documents_own_spelling_through_an_alias(tmp_path) -> None:
    """``$id`` is not a Python identifier, and the WIRE key is the only accepted one.

    ``extensions/extension-meta.json`` requires ``$id`` at its root, so the name this
    row most needs a field for is one pydantic cannot carry under its own spelling.
    ``compiler.fields`` runs it through ``names.field_name`` exactly as a declared
    property's key is, so the alias channel the rest of the tree already uses carries it
    -- and nothing sets ``populate_by_name``, so the attribute spelling is NOT accepted,
    which is what keeps the model's accepted set equal to the document's.
    """
    document = _probe(properties={"known": {"type": "string"}}, required=["$id"])
    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    model = _model("core/probe.json", out, "alias")

    assert model.model_json_schema()["required"] == ["$id"]
    assert model.model_validate({"$id": "urn:x"}) is not None
    with pytest.raises(ValidationError):
        model.model_validate({})


def test_a_required_name_colliding_with_a_declared_one_is_a_verdict(tmp_path) -> None:
    """Two spellings of one field is a VERDICT, as it already is between two declared
    properties.

    ``$id`` and ``id`` both spell the field ``id``, and a class cannot carry two.  The
    declared-property loop above this answer already refuses that collision by name,
    because "a silent collision would drop a property the document admits"; a
    synthesised field reaching the same collision gets the same answer rather than
    silently overwriting the declared field's type with ``Any``.  A VERDICT and not a
    deferral: it is a property of the document, not of unwritten code.
    """
    document = {
        "title": "Probe",
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id", "$id"],
    }
    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    refusal = out.refusals["core/probe.json"]
    assert refusal["keyword"] == "required", refusal
    assert str(refusal["resolved"]).endswith("verdict"), refusal
    assert "both spell the field" in refusal["detail"], refusal["detail"]


# --------------------------------------------------------------------------- #
# the fold, through the instrument that would have reported the field as a defect
# --------------------------------------------------------------------------- #
def test_the_pair_passes_and_the_vacuous_entry_is_reported_rather_than_folded_away(
    tmp_path,
) -> None:
    """§8's three checks over the shape, and the fold REPORTS rather than disappears.

    The second half is the point.  ``url_typed`` and ``constrains_nothing`` are counted
    apart from ``missing`` because "a fold that disappears into a green bucket is
    invisible and permanent", and this is the first such list on the ``added`` side --
    the half that can make a faithful SDK refuse valid traffic.  So the pair passes AND
    the line is there to be read, naming the key and the subschema it folded.
    """
    document = _probe()
    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    model = _model("core/probe.json", out, "pair")
    result = harness.compare_schema(document, model, document=document, at="#")

    assert result.outcome == "pass", (result.missing, result.differs, result.added)
    assert result.added == [], result.added
    assert result.missing == [] and result.differs == []
    assert len(result.vacuous_entry) == 1, result.vacuous_entry
    assert "'undeclared'" in result.vacuous_entry[0], result.vacuous_entry
    assert "the empty schema" in result.vacuous_entry[0], result.vacuous_entry


def test_without_the_fold_the_very_same_pair_reports_added(tmp_path) -> None:
    """The fold's NECESSITY, derived by switching it off rather than asserted.

    This is the half of the row's history a reader cannot otherwise check: the claim is
    that the field answer was unreachable until §8 gained the fold, and the way to show
    it is to take the fold away and watch the faithful model be reported as a defect at
    ``added`` -- "the comparison's word for a model NARROWER than its document", which
    this model is not.

    ``tests/test_decision_set.py`` takes the same perturbation over the whole graded
    population and pins the KEYWORD it admits; this one takes it over one node and reads
    the sentence, so the two cover the mechanism's reach and its message.
    """
    from unittest import mock

    document = _probe()
    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    model = _model("core/probe.json", out, "nofold")
    with mock.patch.object(harness, "_states_no_graded_fact", lambda *a, **k: False):
        result = harness.compare_schema(document, model, document=document, at="#")

    assert result.outcome == "model_adds_a_fact", result.outcome
    assert len(result.added) == 1, result.added
    assert result.added[0].startswith("/properties:"), result.added[0]
    assert "'undeclared'" in result.added[0], result.added[0]
    assert result.vacuous_entry == [], result.vacuous_entry


# --------------------------------------------------------------------------- #
# the bundle population this row claims
# --------------------------------------------------------------------------- #
def test_the_bundle_population_is_the_one_this_row_claims() -> None:
    """:data:`SITES`, derived over the bundle SOURCE by asking the handler's question.

    The question is ``compiler.fields``' own -- a ``required`` name that is in neither
    the node's ``properties`` nor anything an enclosing class holds -- asked at the
    positions a CLASS is cut at, which is what makes this a population and not a grep:
    129 raw nodes of the bundle state a ``required`` naming a key their own
    ``properties`` do not declare, and all but these six are at a RULE position where
    §5's ``required`` row compiles the keyword to a presence rule and no field is owed.

    Derived through ``emit`` and not re-read off the JSON for that reason: the position
    is the compiler's judgement, and a second reading of it here would be a second
    answer to the question the row is about.
    """
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    real = compiler.fields

    def spy(props, required, pointer, mod, **kw):
        held = (*kw.get("inherited", ()), *kw.get("carried", ()))
        undeclared = tuple(r for r in required if r not in props and r not in held)
        if undeclared:
            seen.add((mod.document, pointer or "#", undeclared))
        return real(props, required, pointer, mod, **kw)

    from unittest import mock

    with mock.patch.object(compiler, "fields", spy):
        emit.emit(SOURCE, sorted(bundle.portable(SOURCE)))

    claimed("nodes whose required names a key no declaration declares", seen)
    assert seen == SITES, sorted(seen ^ SITES)


@pytest.mark.parametrize(
    ("document", "pointer", "names"),
    sorted(SITES),
    ids=[f"{d}{p}" for d, p, _ in sorted(SITES)],
)
def test_every_site_is_a_node_whose_own_properties_declare_none_of_the_names(
    document: str, pointer: str, names: tuple[str, ...]
) -> None:
    """The pin read back against the bundle, which is the half the derivation cannot be.

    :func:`test_the_bundle_population_is_the_one_this_row_claims` asserts the compiler
    reaches exactly these nodes; this asserts that each one is the shape the row claims
    -- the names are in the node's ``required`` and in none of its ``properties`` -- so a
    pin that drifted onto a node of some other shape reddens against the document rather
    than against the compiler that produced it.
    """
    node = schema_at(SchemaRef(document, pointer))
    assert set(names) <= set(node["required"]), (names, node.get("required"))
    assert not set(names) & set(node.get("properties") or {}), names
