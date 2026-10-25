"""A fact at a position with no field to carry it, and what section 5 does with each.

Three positions in this file, and they are one question asked three ways: a document
states a keyword at a node whose Python rendering has no slot for it, so either the
fact reaches the WRONG thing, or it is dropped in silence, or the walk refuses.

* a ``default`` on a REQUIRED property -- **dropped and reported** (section 5's
  ``default`` row).  Dropping it changes no accepted set: the key is in every instance
  the document admits, so the default can never be applied.  Reported because an
  emitter that discards a document's fact in silence is the one defect nothing else
  here catches.
* a ``format`` with no type selected, at an ELEM, a MAPV or a BRANCH -- **a named
  alias carries it** (section 5's ``format`` row).  On a FIELD it rides as
  ``json_schema_extra``; inside a container there is no field, and on a union branch
  the field holds the other branches too, so a bound written there refuses values the
  document accepts (section 2, "Constraints bind to the type, not the field").
* an array's or a mapping's own bound at a BRANCH -- **on the branch's own type, never
  on the field holding the union** (section 5's ``minItems``/``maxItems`` and
  ``minProperties``/``maxProperties`` rows).

Every perturbation here is a PAIR of documents differing in the one key being judged,
so a passing arm and a failing arm are separated by the judged dimension and by
nothing else.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from codegen import bundle, emit

from tests.nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
DRAFT = "http://json-schema.org/draft-07/schema#"


def _write(tmp_path: Path, documents: dict[str, dict]) -> Path:
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


def _defaulted(required: list[str]) -> dict:
    """One object root with a defaulted boolean property, required or not."""
    return {
        "title": "Probe",
        "type": "object",
        "properties": {"active": {"type": "boolean", "default": True}},
        "required": required,
    }


# --------------------------------------------------------------------------- #
# a default on a required property: dropped, and reported
# --------------------------------------------------------------------------- #
def test_a_default_is_dropped_where_the_property_is_required_and_kept_where_it_is_not(
    tmp_path,
) -> None:
    """The one distinction, run both ways on two documents differing in ``required``.

    The ``jsonschema`` lines are what make this a measurement rather than a
    restatement of the code: with the key required the document refuses the empty
    object, so no admitted instance omits the key and the default has no instance to
    apply to; without it the empty object is admitted and the default is the value the
    document then means.  That is why one is dropped and the other is rendered.
    """
    demanded, optional = _defaulted(["active"]), _defaulted([])
    assert not jsonschema.Draft7Validator(demanded).is_valid({})
    assert jsonschema.Draft7Validator(optional).is_valid({})

    out = emit.emit(_write(tmp_path / "a", {"core/probe.json": demanded}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert out.drops == {"core/probe.json": {"/properties/active": True}}, out.drops
    assert "    active: bool\n" in out.files["core/probe.py"], out.files["core/probe.py"]

    out = emit.emit(_write(tmp_path / "b", {"core/probe.json": optional}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert out.drops == {}, out.drops
    assert "    active: bool | None = True\n" in out.files["core/probe.py"], out.files[
        "core/probe.py"
    ]


def _defaults_on_required_properties() -> set[tuple[str, str]]:
    """Every (document, pointer) in the bundle where a property's own node states a
    ``default`` and its enclosing object REQUIRES the key.

    Read off the documents rather than off the run, so the set this check ranges over
    is a property of the bundle and the emitter's own record is what gets compared to
    it.  One level of ``properties`` only: the drop is reported at the pointer
    ``compiler.fields`` is handed, and a nested object's own properties are reached
    through their own node at their own pointer, which this enumerates too by walking
    every node the bundle yields.
    """
    found = set()
    for document in bundle.portable(BUNDLE):
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            props = node.get("properties") if isinstance(node, dict) else None
            demanded = node.get("required") if isinstance(node, dict) else None
            if not isinstance(props, dict) or not isinstance(demanded, list):
                continue
            for key, sub in props.items():
                if isinstance(sub, dict) and "default" in sub and key in demanded:
                    found.add((document, f"{pointer}/properties/{key}"))
    return found


def test_every_drop_the_run_reports_is_a_default_on_a_property_its_document_requires()\
        -> None:
    """The reported drops are exactly the shape section 5's row names, over the whole
    portable set, and the set is not empty.

    Both directions matter and only one of them is obvious.  A drop the bundle does
    not state at that shape would be the emitter discarding something else under this
    row's name; and the DOCUMENTS with the shape that this run never reached are
    reported as their own part rather than left in a difference of two totals, because
    a document refused on another row's keyword never reaches ``compiler.fields`` at
    all and its default is neither dropped nor rendered.
    """
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    reported = claimed(
        "drops the run reported",
        {(d, p) for d, sites in out.drops.items() for p in sites},
    )
    stated = claimed("defaults the bundle states on a required property",
                     _defaults_on_required_properties(), inside=None)
    assert reported <= stated, sorted(reported - stated)
    partitions(stated, reported=reported, never_reached=stated - reported)
    for document, pointer in sorted(reported):
        node = bundle.read(BUNDLE, document)
        for step in [s for s in pointer.split("/") if s]:
            node = node[step] if not isinstance(node, list) else node[int(step)]
        assert out.drops[document][pointer] == node["default"], (document, pointer)
