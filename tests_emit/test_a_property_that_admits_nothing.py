"""A ``properties`` entry whose subschema admits NOTHING: the key may not appear.

draft-07 lets a subschema be ``true`` or ``false``, and ``false`` admits no instance at
all.  So ``{"properties": {"k": false}}`` is a statement about PRESENCE: validation of
``k`` is reached only when the key is there, and it then always fails, which makes the
node's accepted set exactly the objects that do not carry ``k``.  ``{"not": {}}`` is the
same schema written long, and the bundle states both spellings -- ``false`` at
``core/format-option-ref.json#/oneOf/1``, whose own description says *"This branch
deliberately forbids ``publisher_domain``"*, and ``{"not": {}}`` at
``core/account.json#/properties/destination_billing_entity``, whose own description says
*"It MUST NOT appear in account read models."*

**THE CLAIM IS ABOUT AN ACCEPTED SET, so every test here states it with ``jsonschema``
first and asks the class to agree.**  The defect this row closes was invisible to any
reading of the rendering: the field was emitted as ``Any | None = None``, which is a
perfectly ordinary annotation, and the only instrument that can tell it apart from a
correct one is a payload carrying the key.  So no test here asserts a type annotation,
an absent field or a rule tuple; each offers the same payload to ``Draft7Validator`` and
to the class and requires one verdict.

**WHY THE ANSWER IS A ``ForbiddenGroups`` AND NOT ``extra='forbid'``.**  All three sites
of the bundle state ``additionalProperties: true`` beside the forbidden key, so the
document admits every OTHER undeclared key and refuses only this one.  Closing the class
would refuse payloads the document accepts, which is the one direction §2 forbids
outright, and :func:`test_the_other_extras_the_document_admits_are_still_admitted` is
what holds the distinction.

**TWO OF THE THREE SITES WERE ALREADY GREEN, BY A SECOND ROUTE, AND THAT IS WHY THE
CENSUS IS THE FIRST TEST IN THIS FILE.**  Both ``{"not": {}}`` nodes sit in a node that
ALSO states ``not: {"required": ["destination_billing_entity"]}`` at its own root -- the
bundle spelling the equivalence out for us -- and that sibling already lowered to the
rule.  Read off the one site that reddened, this row is a one-line fix to one document;
read off the rule, it is three sites and a second spelling.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import fresh
import jsonschema
import pytest
from pydantic import ValidationError

from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, emit
from codegen.schema import parse as schema
from nodeset import claimed

DRAFT = "http://json-schema.org/draft-07/schema#"
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
SOURCE = fresh.BUNDLE

#: Every site of the bundle where a ``properties`` entry admits nothing: the document,
#: the pointer of the CLASS that holds the property, the key, and a payload the document
#: admits at that pointer.
#:
#: Pinned as a set of SITES and not as a count, for §8's reason: a count over the
#: emitted population rises when the emitter emits more, and these are positions of the
#: bundle SOURCE, which does not move when a row lands.
#: :func:`test_the_bundle_population_is_the_one_this_row_claims` is the derivation that
#: this set is the whole of it -- the row was filed naming one site, and there are three.
SITES: tuple[tuple[str, str, str, dict], ...] = (
    (
        "core/format-option-ref.json",
        "#/oneOf/1",
        "publisher_domain",
        {"scope": "product", "format_option_id": "fo-1"},
    ),
    (
        "core/account.json",
        "#",
        "destination_billing_entity",
        {"account_id": "a-1", "name": "Acme", "status": "active"},
    ),
    (
        "account/sync-accounts-response.json",
        "#/oneOf/0/properties/accounts/items",
        "destination_billing_entity",
        {
            "action": "created",
            "status": "active",
            "brand": {"domain": "acme.example"},
            "operator": "op.example",
        },
    ),
)

#: The value offered for the forbidden key.  Any value at all is refused -- that is what
#: "admits nothing" means -- and the tests below say so over several JSON types rather
#: than trusting one.
VALUES: tuple[Any, ...] = ("example.com", 7, None, {"nested": [1, 2]}, [], True)


def _class_at(document: str, pointer: str) -> Any:
    """The emitted class whose ``__adcp_schema__`` names this node.

    Found by the schema reference the class carries and not by name, because the class's
    NAME is §4's derivation and this row is not about it: a renaming there must not be
    able to make this gate pass by failing to find anything.
    """
    module_name = "adcp.types._schemas." + document.removesuffix(".json").replace(
        "-", "_"
    ).replace("/", ".")
    __import__(module_name)
    module = sys.modules[module_name]
    found = [
        value
        for value in vars(module).values()
        if isinstance(value, type)
        and getattr(value, "__adcp_schema__", None)
        == SchemaRef(document=document, pointer=pointer)
    ]
    assert len(found) == 1, f"{document}#{pointer}: {len(found)} classes carry that reference"
    return found[0]


# --------------------------------------------------------------------------- #
# the population, before anything is claimed about it
# --------------------------------------------------------------------------- #
def test_the_bundle_population_is_the_one_this_row_claims() -> None:
    """Every ``properties`` entry of the bundle that admits nothing, derived.

    The row was filed naming ``core/format-option-ref.json`` because one site had been
    found, not because one exists.  The derivation walks every subschema position of all
    1,054 portable documents and asks ``schema.admits_nothing`` -- the compiler's OWN
    reading, so this test cannot agree with a census that disagrees with the compiler --
    and it finds three entries in three documents, in two spellings.

    The other positions the reading reaches are NOT this row's and are named here so the
    set this test claims is the one it ranges over: ``false`` under ``additionalProperties``
    is §5's ``extra='forbid'`` and is already decided and implemented, and ``then: false``
    at three sites is a CONDITIONAL whose consequent admits nothing, which is the ``then``
    row's cell and not the ``properties`` row's.
    """
    population = claimed("the bundle's portable documents", bundle.portable(SOURCE))

    found: set[tuple[str, str]] = set()
    for document in sorted(population):
        root = json.loads((SOURCE / document).read_text())
        _collect(root, "#", document, found)

    assert claimed(
        "properties entries of the bundle that admit nothing",
        found,
        inside={(d, f"{p}/properties/{k}" if p != "#" else f"#/properties/{k}") for d, p, k, _ in SITES},
    ) == {
        (document, f"{pointer.rstrip('/')}/properties/{key}" if pointer != "#" else f"#/properties/{key}")
        for document, pointer, key, _ in SITES
    }


def _collect(node: Any, pointer: str, document: str, out: set[tuple[str, str]]) -> None:
    """Every ``properties`` entry under ``node`` whose subschema admits nothing.

    A plain recursive descent over the keywords whose value holds subschemas, rather
    than the compiler's walk: the compiler's walk stops where a document refuses and
    declares only the ``definitions`` entries a ``$ref`` names, and a census of what the
    DOCUMENTS state must see a site the compiler never reaches.
    """
    if not isinstance(node, dict):
        return
    for keyword, value in node.items():
        if keyword == "properties" and isinstance(value, dict):
            for key, sub in value.items():
                at = f"{pointer}/properties/{key}"
                if schema.admits_nothing(sub):
                    out.add((document, at))
                _collect(sub, at, document, out)
        elif keyword in ("definitions", "$defs", "patternProperties") and isinstance(value, dict):
            for key, sub in value.items():
                _collect(sub, f"{pointer}/{keyword}/{key}", document, out)
        elif keyword in ("oneOf", "anyOf", "allOf") and isinstance(value, list):
            for i, sub in enumerate(value):
                _collect(sub, f"{pointer}/{keyword}/{i}", document, out)
        elif keyword in (
            "items",
            "additionalProperties",
            "additionalItems",
            "propertyNames",
            "contains",
            "not",
            "if",
            "then",
            "else",
        ):
            if isinstance(value, list):
                for i, sub in enumerate(value):
                    _collect(sub, f"{pointer}/{keyword}/{i}", document, out)
            else:
                _collect(value, f"{pointer}/{keyword}", document, out)


# --------------------------------------------------------------------------- #
# the gate: one payload, two verdicts
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(("document", "pointer", "key", "admitted"), SITES)
def test_a_payload_carrying_the_forbidden_key_is_refused_by_both_halves(
    document: str, pointer: str, key: str, admitted: dict
) -> None:
    """The document refuses it, so the class must refuse it.

    Four claims per site, and the third is the one that was false:

    * the payload WITHOUT the key is admitted by the document, which is what makes it a
      witness rather than a payload refused for some other reason;
    * the document REFUSES the same payload once the key is added, at every one of
      :data:`VALUES` -- "admits nothing" is a claim about every value, and one value
      would not state it;
    * the CLASS refuses it too, reported through ``model_validate`` and not read off an
      annotation;
    * and the class still admits the witness, so nothing here narrowed the model.

    The field was emitted as ``publisher_domain: Any | None = None`` before this row, so
    the third claim failed at ``core/format-option-ref.json`` and the model accepted a
    payload ``Draft7Validator`` refuses.
    """
    node = schema_at(SchemaRef(document=document, pointer=pointer))
    judge = jsonschema.Draft7Validator(node)
    assert judge.is_valid(admitted), f"{document}#{pointer}: the witness is not admitted"

    model = _class_at(document, pointer)
    assert model.model_validate(admitted) is not None

    for value in VALUES:
        payload = {**admitted, key: value}
        assert not judge.is_valid(payload), f"{document}#{pointer} admits {key}={value!r}"
        with pytest.raises(ValidationError):
            model.model_validate(payload)


@pytest.mark.parametrize(("document", "pointer", "key", "admitted"), SITES)
def test_the_other_extras_the_document_admits_are_still_admitted(
    document: str, pointer: str, key: str, admitted: dict
) -> None:
    """The forbid is about ONE key, not about extras.

    Every one of the three sites states ``additionalProperties: true``, so the document
    admits an undeclared key with any value -- which is why closing the class is the
    wrong answer even though it would make the test above pass.  Stated as the accepted
    set it is: the document admits the extra, so the class must.
    """
    node = schema_at(SchemaRef(document=document, pointer=pointer))
    assert node.get("additionalProperties") is True, node.get("additionalProperties")
    payload = {**admitted, "an_undeclared_key_the_document_admits": "value"}
    assert jsonschema.Draft7Validator(node).is_valid(payload)
    assert _class_at(document, pointer).model_validate(payload) is not None


# --------------------------------------------------------------------------- #
# the two spellings, on a probe, so the reading is graded and not just its sites
# --------------------------------------------------------------------------- #
def _write(tmp_path: Path, documents: dict[str, dict]) -> Path:
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


def _model(document: str, out: emit.Emitted, tag: str) -> Any:
    """The emitted module's root symbol, EXECUTED rather than inspected."""
    text = out.files[document.replace(".json", ".py")]
    module = types.ModuleType(f"_admits_nothing_{tag}")
    sys.modules[module.__name__] = module
    try:
        exec(  # executing the compiler's own output is the point
            "\n".join(x for x in text.splitlines() if not x.startswith("from .")),
            module.__dict__,
        )
    finally:
        del sys.modules[module.__name__]
    return module.__dict__[module.__all__[0]]


@pytest.mark.parametrize(
    ("tag", "forbidding"),
    [("false", False), ("not_empty", {"not": {}}), ("not_true", {"not": True})],
)
def test_both_spellings_of_the_empty_set_schema_forbid_the_key(
    tmp_path, tag: str, forbidding: Any
) -> None:
    """``false``, ``{"not": {}}`` and ``{"not": true}`` are one schema, and one answer.

    The bundle states two of the three, and they must not come to two readings: a row
    that fixed ``false`` alone would leave the long spelling emitting the ``Any`` field
    the short one no longer does, which is the shape this project keeps paying for.
    ``{"not": true}`` is in the parametrisation because draft-07 admits it and the
    reading is about what a subschema ADMITS, not about which of its spellings the bundle
    happens to use.
    """
    document = {
        "title": "Probe",
        "type": "object",
        "properties": {"known": {"type": "string"}, "gone": forbidding},
        "required": ["known"],
        "additionalProperties": True,
    }
    judge = jsonschema.Draft7Validator(document)
    assert judge.is_valid({"known": "k"})
    assert judge.is_valid({"known": "k", "other": 1}), "the probe admits other extras"
    assert not judge.is_valid({"known": "k", "gone": "x"})

    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    model = _model("core/probe.json", out, tag)

    assert model.model_validate({"known": "k"}) is not None
    assert model.model_validate({"known": "k", "other": 1}) is not None
    for value in VALUES:
        with pytest.raises(ValidationError):
            model.model_validate({"known": "k", "gone": value})


def test_a_forbidden_key_owes_no_declared_widening(tmp_path) -> None:
    """The answer is EXACT, so it costs no approximation.

    ``properties: {k: false}`` and ``not: {"required": [k]}`` have the same accepted set
    in draft-07, and §5 already decides the second -- "``not: {required: …}`` … → a
    ``ForbiddenGroups`` rule".  Nothing is dropped reaching it, so this row must not add
    a row to the declared backlog; an approximation here would be the answer "we cannot
    express it" standing in for "nobody wrote it".
    """
    document = {
        "title": "Probe",
        "type": "object",
        "properties": {"known": {"type": "string"}, "gone": False},
        "required": ["known"],
        "additionalProperties": True,
    }
    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert out.approximations == {}, out.approximations


def test_a_required_key_whose_declaration_admits_nothing_admits_nothing(tmp_path) -> None:
    """The document admits no object at all, and so does the class -- by composition.

    ``required: ["gone"]`` beside ``properties: {"gone": false}`` is a contradiction the
    document states, and it needs no arm of its own: the ``required`` row's
    undeclared-name field makes the class refuse a payload OMITTING the key, and this
    row's ``ForbiddenGroups`` makes it refuse one CARRYING it.  The two together are
    exactly the document's empty accepted set, which is why no refusal is minted for a
    shape the bundle does not state.

    The probe is silent about ``additionalProperties`` and still refuses both ways, and
    the reason is the REQUIRED field rather than the rule: under ``extra='ignore'``
    pydantic drops the key, so the field it is required at is missing and the class
    refuses for that.  Named here because the test above states the general case and
    this one must not be read as evidence for it.
    """
    document = {
        "title": "Probe",
        "type": "object",
        "properties": {"known": {"type": "string"}, "gone": False},
        "required": ["known", "gone"],
    }
    judge = jsonschema.Draft7Validator(document)
    assert not judge.is_valid({"known": "k"})
    assert not judge.is_valid({"known": "k", "gone": "x"})

    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    model = _model("core/probe.json", out, "contradiction")
    for payload in ({"known": "k"}, {"known": "k", "gone": "x"}, {"known": "k", "gone": None}):
        with pytest.raises(ValidationError):
            model.model_validate(payload)


def test_a_node_whose_every_declaration_admits_nothing_is_not_a_node_declaring_none(
    tmp_path,
) -> None:
    """It admits every object without the key, so it must not be refused.

    "An object node with no property declared" is a VERDICT the compiler already minted,
    and dropping the forbidden property from the FIELDS put a node that declares one
    inside that refusal's reach -- where its own sentence is false and its verdict is
    wrong, because the accepted set is every object not carrying the key and is not
    empty.  The bundle states no such node, so this test decides nothing about the
    artifact; it holds the refusal's gate on what the DOCUMENT declares.

    **The probe states ``additionalProperties: true``, as all three sites of the bundle
    do, and that is load-bearing rather than incidental.**  A ``ForbiddenGroups`` reads
    the keys the instance SUPPLIED, so it can only see a key pydantic kept: under
    ``extra='allow'`` the key lands in ``__pydantic_extra__`` and the rule refuses it,
    and under ``extra='ignore'`` -- a document silent about
    ``additionalProperties`` -- pydantic drops the key before any validator runs and the
    class accepts a payload the document refuses.  That shape is the same gate
    ``minProperties`` already has for the same reason ("a dropped key would make the
    rule refuse what the document accepts", §5), read in the other direction.  **No node
    of the bundle states it** -- :func:`test_the_bundle_population_is_the_one_this_row_claims`
    is the tripwire that reddens if one arrives, and
    ``adcp-client-python-82m.14`` carries the shape -- so nothing is dropped today and
    nothing is declared for it.
    """
    document = {
        "title": "Probe",
        "type": "object",
        "properties": {"gone": False},
        "additionalProperties": True,
    }
    judge = jsonschema.Draft7Validator(document)
    assert judge.is_valid({})
    assert judge.is_valid({"other": 1})
    assert not judge.is_valid({"gone": 1})

    out = emit.emit(_write(tmp_path, {"core/probe.json": document}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    model = _model("core/probe.json", out, "only_forbidden")
    assert model.model_validate({}) is not None
    assert model.model_validate({"other": 1}) is not None
    with pytest.raises(ValidationError):
        model.model_validate({"gone": 1})
