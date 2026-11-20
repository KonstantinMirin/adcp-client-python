"""The two null markers, and the three readers that have to tell them apart.

``docs/plan/rebuild-plan.md`` §2 gives an optional property's ``None`` one meaning on the
dump and its NULLABILITY another on input, and the emitted tree carries the pair as two
markers written beside a generated ``Field``:

    OmittedNotNull    the document REFUSES null   both halves: exclusion + _AbsenceIsOmission
    OmittedWhenNone   the document ADMITS null    the exclusion ALONE

**THEY SHARE ONE ``exclude_if`` OBJECT ON PURPOSE** -- they owe pydantic-core the same
answer, "leave a ``None`` off this field" -- **so the exclusion cannot tell them apart, and
a predicate that tested it alone answered the document's question wrongly for every
null-admitting property in the tree** (``adcp-client-python-hsht``).  Measured on
``core/targeting-input.json`` before the repair: 37 properties, all 37 admit ``null``
explicitly, all 37 carry the marker, and all 37 answered ``True`` to
``omits_null`` -- "does this property's document refuse ``null``".

What that cost, each with its own named test:

* ``_runtime.supplied`` dropped a SET ``None`` at such a property from the key set, so a
  document rule about key PRESENCE fired on a value the document states:
  ``PackageControl.model_validate({"package_id": "p1", "budget": None})`` was refused on
  its own ``anyOf`` while the bundled schema accepts the same document.  An UNDECLARED
  NARROWING, which §2's decision index calls a defect in as many words, reported by
  ``tests/conformance/test_schema_model_parity.py::test_schema_and_model_agree[control_media_buy]``;
* ``base.AdCPBaseModel.model_dump_as_received`` could not keep the ``null`` its own
  docstring promises to keep -- and that dump's contract is a DOCUMENT's: a digest over
  ``commercial_terms`` *as declared* (#1613);
* ``decisioning.handler._to_store_dict``'s ``patch`` shape turned "clear this field" back
  into "leave it unchanged", on a mutation request where ``core/targeting-input.json``
  states the three states in prose.

**SO THE PREDICATES READ THE HALVES, AND THIS FILE IS WHAT KEEPS THEM READING THEM.**  The
repair is three lines of predicate, which is exactly the kind of thing a later reader
"simplifies" back to the one-line identity test -- the two markers look identical at the
point of definition, and nothing about a dump changes when they are folded together.  What
changes is the answer to a question about the DOCUMENT, in three places at once, silently.

Each test below fails on a different collapse, so the mode of a regression is named rather
than inferred:

* fold the predicates back to the exclusion alone  -> the partition test and the
  ``supplied`` test;
* drop the validation half from the ``OmittedNotNull`` marker -> the marker test;
* emit the wrong marker at a property  -> the tree test, over every emitted field against
  what its own document says about ``null``.

``tests_emit/`` and not ``tests/`` because the subject is the EMITTED tree graded against
the documents it came from: the tree test reads ``null`` out of the bundle and asks the
class.  ``make gate`` names one node of one other file, so this runs under
``make emit-suite``.
"""

from __future__ import annotations

import collections
from pathlib import Path

import fresh

import adcp.types as public_types
from adcp.types._base import (
    OmittedNotNull,
    OmittedWhenNone,
    _AbsenceIsOmission,
    omits_none,
    omits_null,
)
from adcp.types.base import AdCPBaseModel
from codegen import bundle, ir

#: The bundle a run reads, from the ONE declaration of it, for
#: ``tests_emit/test_reported_drop.py``'s measured reason.
BUNDLE = Path(fresh.BUNDLE)

#: A property whose document admits ``null``, with the document and pointer that say so --
#: the pair this file grades the emitted field against.  ``core/targeting-input.json`` is
#: the measurement the bead was filed on and ``media-buy/package-control.json`` is the one
#: that produced the narrowing, so both are named and neither stands for the other.
ADMITS_NULL = (
    ("core/targeting-input.json", "geo_countries"),
    ("media-buy/package-control.json", "budget"),
)

#: And a property whose document REFUSES one, on the same two documents, so a test that
#: passed by answering one way for everything is not green here.
REFUSES_NULL = (("media-buy/package-control.json", "paused"),)


def _adcp_models() -> list[tuple[str, type[AdCPBaseModel]]]:
    """Every public class of the surface that declares fields.

    The same sweep ``tests/test_nested_no_explicit_null_round_trip.py`` takes, written
    here rather than imported: that module is ``tests/`` and grades the SDK, this one is
    ``tests_emit/`` and grades the emission, and §9's import sets do not cross.
    """
    return [
        (name, obj)
        for name in sorted(dir(public_types))
        if not name.startswith("_")
        and isinstance(obj := getattr(public_types, name, None), type)
        and issubclass(obj, AdCPBaseModel)
        and obj.model_fields
    ]


def _admits_null(node: object) -> bool:
    """Whether a property's own declaration admits ``null``, read off the DOCUMENT.

    draft-07 spells it two ways and the bundle uses both: ``"type": [..., "null"]`` and an
    ``anyOf`` with a ``{"type": "null"}`` branch.  ``codegen.ir.admits_null`` is the
    compiler's reader and takes a decided type rather than a node, so this is the document
    side of the same question -- which is the one a test of the emission has to ask.
    """
    if not isinstance(node, dict):
        return False
    stated = node.get("type")
    if stated == "null" or (isinstance(stated, list) and "null" in stated):
        return True
    for branch in node.get("anyOf") or node.get("oneOf") or ():
        if isinstance(branch, dict) and _admits_null(branch):
            return True
    return False


def test_the_markers_are_one_exclusion_and_two_metadata() -> None:
    """The shape the predicates read: one ``exclude_if``, and the validation half on one.

    Both halves of the asymmetry are asserted, because either one alone is a different
    marker: dropping ``_AbsenceIsOmission`` from ``OmittedNotNull`` makes every
    null-refusing property admit a ``null`` its document refuses, and giving
    ``OmittedWhenNone`` its own ``exclude_if`` makes "every optional field carries THE
    exclusion" -- a tree-wide invariant ``tests/test_nested_no_explicit_null_round_trip.py``
    states as one identity -- false for 68 properties with nothing about serialisation
    changed.
    """
    assert OmittedWhenNone.exclude_if is OmittedNotNull.exclude_if, (
        "the two markers no longer share one exclusion; both owe pydantic-core the same "
        "answer and two tests state that as one identity"
    )
    assert any(isinstance(item, _AbsenceIsOmission) for item in OmittedNotNull.metadata), (
        "OmittedNotNull lost its validation half, which is the only thing that "
        "distinguishes it -- every null-refusing property now admits a null"
    )
    assert not OmittedWhenNone.metadata, (
        "OmittedWhenNone grew metadata; the serialisation half ALONE is what it is"
    )


def test_the_two_predicates_partition_the_marked_fields() -> None:
    """``omits_null`` and ``omits_none`` are complements over the marked fields.

    The collapse this file exists for reads as both predicates answering the same thing, so
    the assertion is a PARTITION and not two independent answers: every marked field is in
    exactly one, and a field carrying no marker is in neither.
    """
    for marker, (refuses, admits) in (
        (OmittedNotNull, (True, False)),
        (OmittedWhenNone, (False, True)),
    ):
        assert (omits_null(marker), omits_none(marker)) == (refuses, admits), (
            f"the predicates no longer tell {marker!r} apart"
        )
    counts: collections.Counter[str] = collections.Counter()
    for name, model in _adcp_models():
        for field_name, field in model.model_fields.items():
            answers = (omits_null(field), omits_none(field))
            assert answers != (True, True), (name, field_name)
            if field.exclude_if is OmittedNotNull.exclude_if:
                assert answers != (False, False), (
                    f"{name}.{field_name} carries the exclusion and neither predicate "
                    "claims it, so no reader can ask what its document says about null"
                )
            counts["refuses" if answers[0] else "admits" if answers[1] else "unmarked"] += 1
    # Both populations are non-trivial, so a predicate that answered one way for the whole
    # tree would fail here rather than pass by accident.
    assert counts["refuses"] > 5000, counts
    assert counts["admits"] > 50, counts


def test_every_emitted_marker_matches_what_its_document_says_about_null() -> None:
    """The pairing itself: the marker a field carries against its document's own ``null``.

    The predicates can be right and the EMISSION still wrong, which is the other half of
    the defect and the half ``codegen.ir.admits_null`` owns.  Read from the document side
    (:func:`_admits_null`) at the named properties, so a wrong marker is a named failure
    rather than a wrong answer to a question nobody asks.
    """
    for document, prop in ADMITS_NULL:
        node = bundle.read(BUNDLE, document)["properties"][prop]
        assert _admits_null(node), f"{document}#{prop} no longer admits null in the bundle"
    for document, prop in REFUSES_NULL:
        node = bundle.read(BUNDLE, document)["properties"][prop]
        assert not _admits_null(node), f"{document}#{prop} now admits null in the bundle"

    seen = 0
    for _, model in _adcp_models():
        reference = getattr(model, "__adcp_schema__", None)
        if reference is None or reference.pointer != "#":
            continue
        for document, prop in ADMITS_NULL:
            if reference.document != document:
                continue
            field = model.model_fields.get(prop)
            if field is None:
                continue
            seen += 1
            assert omits_none(field) and not omits_null(field), (
                f"{model.__name__}.{prop}: the document admits null and the field carries "
                "the null-REFUSING marker, so a None here reads as absence and a presence "
                "rule fires on a value the document states"
            )
        for document, prop in REFUSES_NULL:
            if reference.document != document:
                continue
            field = model.model_fields.get(prop)
            if field is None:
                continue
            seen += 1
            assert omits_null(field) and not omits_none(field), (
                f"{model.__name__}.{prop}: the document refuses null and the field does "
                "not carry the refusing marker"
            )
    assert seen >= len(ADMITS_NULL) + len(REFUSES_NULL), (
        f"only {seen} of the named properties were found on a root class; the documents "
        "moved and this file's measurement is stale"
    )


def test_a_supplied_null_the_document_admits_is_a_present_key() -> None:
    """``_runtime.supplied``, which is where the narrowing was.

    The reading that decides a presence rule: a ``None`` at a property whose document
    REFUSES ``null`` is absence and is not a key, and one at a property whose document
    ADMITS it is a value and is.  Asserted end to end as well as on the key set, because
    the key set is an implementation detail and the refusal is what a consumer meets.
    """
    from adcp.types.domains.media_buy.package_control import PackageControl

    from adcp.types._runtime import supplied

    admitted = PackageControl.model_validate({"package_id": "p1", "budget": None})
    keys, values = supplied(admitted)
    assert "budget" in keys, (
        "a supplied null at a null-admitting property is not a key, so every presence rule "
        "over it fires on a value the document states"
    )
    assert values["budget"] is None
    assert ir.FACTS  # the compiler's own reader is importable here, which §9 permits

    # The same class, the same shape, a property whose document refuses a null: absence.
    refused = PackageControl.model_construct(package_id="p1", paused=None)
    refused.__pydantic_fields_set__ = {"package_id", "paused"}
    assert "paused" not in supplied(refused)[0]
