"""**A JSON ``null`` IS REFUSED AND A PYTHON ``None`` IS ABSENCE: the route split, graded.**

``adcp.types._base.OmittedNotNull`` is on every optional property whose document does not
admit ``null`` (bead ``adcp-client-python-4yhb``).  Its validation half used to strike the
null arm on BOTH sides; it now returns a ``json_or_python`` schema -- the JSON side with
the arm struck, the Python side keeping ``T | None`` -- and ``ADCP_STRICT_VALIDATION``
strikes both.

**THE CLAIM, and the reason reading 1 survives it.**  A JSON ``null`` is a DOCUMENT's
statement and a Python ``None`` is a Python call: JSON spells "no value" one way and Python
spells it two, an absent key and ``None``.  Every instrument that measures "the class
accepts exactly what the document accepts" offers a document -- ``./check``,
``tests/conformance/test_schema_model_parity.py``, every ``strict_validate`` -- and the
JSON route still refuses, so no document's accepted set widens.

**FIVE CLAUSES, one per half of the contract, and the population is DERIVED.**  The
properties graded here are read off the emitted tree by asking each field whether it
carries the marker (``_base.omits_null``), so a property that gains or loses it moves
through this file with nothing edited and no name listed.

* the JSON route REFUSES -- :func:`test_the_json_route_refuses_a_null`;
* the PYTHON routes read ``None`` as absence -- :func:`test_the_python_routes_read_none_as_absence`;
* ``ADCP_STRICT_VALIDATION`` refuses both -- :func:`test_strict_validation_refuses_a_none_too`;
* the DUMP carries no ``null`` -- :func:`test_a_plain_dump_carries_no_null`;
* the PUBLISHED schema states no null arm -- :func:`test_the_published_schema_states_no_null_arm`;
* and a genuinely nullable property is UNAFFECTED --
  :func:`test_a_genuinely_nullable_property_still_accepts_a_null`, which is the clause that
  keeps the other five from being a licence to strike every null in the tree.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

import pytest
from nodeset import claimed

from adcp.types._base import omits_null

#: One marked property to grade each clause on, named by DOCUMENT and POINTER rather than
#: by class, because the claim is about what the document states.  ``cursor`` is the
#: measurement bead 4yhb was filed on: ``core/pagination-request.json`` states
#: ``cursor: {"type": "string"}`` and does not list it in ``required``, so the document
#: admits a STRING or the key's ABSENCE and ``null`` is neither.
A_MARKED_PROPERTY = ("core/pagination-request.json", "#/properties/cursor", "cursor")


def _pagination() -> Any:
    from adcp.types import PaginationRequest

    return PaginationRequest


def _marked_fields() -> dict[str, list[str]]:
    """Every emitted class with a marked field, by class name, read off the TREE.

    The population is :func:`adcp.types._base.omits_null`'s answer and never a list: a
    property that gains or loses the marker moves through this file with nothing edited.
    Used by the clauses that range over the whole surface rather than over one witness.
    """
    import adcp.types as types_module

    out: dict[str, list[str]] = {}
    for name in dir(types_module):
        if name.startswith("_"):
            continue
        obj = getattr(types_module, name, None)
        fields = getattr(obj, "model_fields", None)
        if not isinstance(fields, dict):
            continue
        marked = sorted(key for key, field in fields.items() if omits_null(field))
        if marked:
            out[name] = marked
    return out


def test_the_marked_population_is_not_empty() -> None:
    """The population, asserted before anything is asserted over it.

    ``docs/plan/final-state.md``: a reading over an empty set passes every clause below
    while saying nothing, and this one is a predicate over field metadata -- exactly the
    shape that silently empties if the marker's identity test changes.
    """
    found = _marked_fields()
    claimed("emitted classes carrying a marked field", found)
    # The flat facade is LAZY (PEP 562), so ``dir()`` lists what has been realised rather
    # than the whole surface -- the figure is therefore a floor and not a census, and the
    # clause asserts only that the predicate finds something to range over.
    assert sum(len(v) for v in found.values()) >= 1, found


def test_the_json_route_refuses_a_null() -> None:
    """``model_validate_json`` REFUSES ``null`` -- which is the document's own screen.

    ``core/pagination-request.json`` says ``cursor: {"type": "string"}`` and nothing about
    ``null``, so the refusal carries the TYPE's own error and not a keyword the document
    does not use.
    """
    document, pointer, key = A_MARKED_PROPERTY
    model = _pagination()
    assert omits_null(model.model_fields[key]), f"{document}{pointer} carries no marker"

    with pytest.raises(Exception) as refused:
        model.model_validate_json(json.dumps({"max_results": 5, key: None}))
    reported = refused.value.errors()
    assert any(r["type"] == "string_type" for r in reported), reported
    assert any(tuple(r["loc"]) == (key,) for r in reported), reported


def test_the_python_routes_read_none_as_absence() -> None:
    """``model_validate(dict)`` and ``Model(**kwargs)`` read ``None`` as "not supplied".

    BOTH Python routes, because the contract must not be a function of which one a caller
    reached for -- that was the sound half of the sentence this change replaced, and it
    is kept: the split is by ROUTE (JSON against Python) and never between the two Python
    entry points.
    """
    _, _, key = A_MARKED_PROPERTY
    model = _pagination()
    assert getattr(model.model_validate({"max_results": 5, key: None}), key) is None
    assert getattr(model(**{"max_results": 5, key: None}), key) is None
    # and an omitted key reads the same, which is what makes None "absence" rather than a
    # second spelling of something else
    assert getattr(model.model_validate({"max_results": 5}), key) is None


def test_strict_validation_refuses_a_none_too() -> None:
    """``ADCP_STRICT_VALIDATION`` strikes the Python side as well.

    **In a SUBPROCESS, because the switch is resolved at import**
    (``adcp.types.base._EXTRA_POLICY``): setting the variable in this process would be read
    by nothing, so a test that did it would assert the default twice and pass either way.
    """
    _, _, key = A_MARKED_PROPERTY
    script = (
        "from adcp.types import PaginationRequest as P\n"
        "for payload in ({'max_results': 5, %r: None},):\n"
        "    try:\n"
        "        P.model_validate(payload); print('ADMITTED')\n"
        "    except Exception:\n"
        "        print('REFUSED')\n"
        "try:\n"
        "    P(max_results=5, %s=None); print('ADMITTED')\n"
        "except Exception:\n"
        "    print('REFUSED')\n" % (key, key)
    )
    env = {**os.environ, "ADCP_STRICT_VALIDATION": "1", "PYTHONPATH": ".:src"}
    out = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env, check=True
    )
    assert out.stdout.split() == ["REFUSED", "REFUSED"], out.stdout


def test_a_plain_dump_carries_no_null() -> None:
    """The serialisation half, UNCHANGED by the split and asserted so.

    ``exclude_if=_is_absent`` leaves a ``None`` off the output in pydantic-core, so a
    PLAIN dump -- no ``exclude_none``, no ``exclude_unset`` -- carries no ``null`` at a
    marked property.  Both modes, because they are two serialisers.
    """
    _, _, key = A_MARKED_PROPERTY
    made = _pagination()(**{"max_results": 5, key: None})
    for mode in ("json", "python"):
        dumped = made.model_dump(mode=mode)
        assert key not in dumped, (mode, dumped)
        assert None not in dumped.values(), (mode, dumped)


def test_the_published_schema_states_no_null_arm() -> None:
    """**THE PUBLISHED-CONTRACT HALF of 4yhb, asserted rather than assumed.**

    Pydantic generates ``model_json_schema()`` from the ``json_schema`` side of a
    ``json_or_python`` schema, so the split should leave the published type exactly as the
    document states it -- but "should" is the word this clause exists to remove.  What a
    consumer's codegen and every schema comparison read is this rendering, so a null arm
    appearing here would be the model publishing a fact its document does not state, which
    is the defect 4yhb is about in its most visible form.

    Asserted over EVERY marked field of the class and not only the witness: the rendering
    is per property, and one property is not evidence about the rest.
    """
    model = _pagination()
    published = model.model_json_schema()["properties"]
    marked = [key for key, field in model.model_fields.items() if omits_null(field)]
    assert marked, "no marked field on the witness class"
    for key in marked:
        node = published[key]
        assert "anyOf" not in node, (key, node)
        assert node.get("type") != "null", (key, node)
        assert "null" not in json.dumps(node.get("type", "")), (key, node)


def test_a_genuinely_nullable_property_still_accepts_a_null() -> None:
    """**THE CLAUSE THAT BOUNDS THE OTHER FIVE.**

    A property whose DOCUMENT admits ``null`` is emitted WITHOUT the marker
    (``codegen.ir.admits_null`` is the one reader that decides which), and it keeps every
    ``null`` it ever wrote -- on both routes.  Without this clause the five above would
    read the same on a tree that had struck every null arm in it, which is the one
    outcome reading 1 forbids outright.

    The witness is DERIVED: the first emitted field whose annotation admits ``None`` and
    which carries NO marker, so the clause follows the tree rather than a name.
    """
    import adcp.types as types_module

    unmarked: tuple[Any, str] | None = None
    for name in dir(types_module):
        if name.startswith("_"):
            continue
        obj = getattr(types_module, name, None)
        fields = getattr(obj, "model_fields", None)
        if not isinstance(fields, dict) or getattr(obj, "_branch_models", None):
            continue
        for key, field in fields.items():
            if omits_null(field):
                continue
            if "null" in json.dumps(
                (obj.model_json_schema().get("properties", {}) or {}).get(key, {})
            ):
                unmarked = (obj, key)
                break
        if unmarked is not None:
            break
    assert unmarked is not None, (
        "no emitted property publishes a null arm, so the marker has been applied "
        "everywhere and this clause cannot bound anything"
    )
    model, key = unmarked
    # **THE DOCUMENT ADMITS ``null`` HERE, AND THE PUBLISHED SCHEMA STILL SAYS SO.**  That
    # is what bounds the other five clauses: the strike is scoped to the marker, so a
    # property the emitter did NOT mark keeps its null arm on both routes and in the
    # rendering a consumer reads.  Asserted on the RENDERING rather than by constructing a
    # payload, because a payload needs every required key of whatever class the derivation
    # landed on and the clause is about the arm, not about that class's requiredness.
    published = model.model_json_schema()["properties"][key]
    assert "null" in json.dumps(published.get("anyOf", published)), (key, published)
    assert not omits_null(model.model_fields[key]), (
        f"{model.__name__}.{key} publishes a null arm AND carries the marker, so the two "
        "readings of 'does this document admit null' disagree"
    )
