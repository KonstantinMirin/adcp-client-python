"""Grade the entry point D4 moves acceptance to.

``tests/test_emit.py`` grades the TREE, and every assertion there is derived
from the bundle so that nothing can pass because someone recorded what the tree
happened to hold.  This file grades a CONTRACT instead -- schema first, then
construct; the JSON Schema keyword as the error ``type``; a refusal when there
is no document to ask -- and a contract is stated, so these assertions name a
document and a property on purpose.  They are the acceptance criteria step 10 of
``docs/plan/rebuild-plan.md`` is written with, over step 1's document.

``core/pagination-request.json`` is the one document named here: an optional
``cursor`` declared ``{"type": "string"}`` and an optional ``max_results`` with
``minimum: 1``, which is one property per half of the obligation.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from adcp.types._base import AdCPBaseModel, _document_of
from adcp.types._schemas.core.pagination_request import PaginationRequest
from codegen import adapter, emit

TREE = Path(__file__).resolve().parents[1] / emit.TREE


def test_an_explicit_null_for_a_string_property_is_refused_on_type() -> None:
    """D4's null case, discharged by the schema rather than a per-field validator.

    ``{"type": "string"}`` refuses an explicit null and says so itself; the
    keyword it refuses on is what reaches ``errors()[0]["type"]``.
    """
    with pytest.raises(ValidationError) as caught:
        PaginationRequest.strict_validate({"cursor": None})
    (err,) = caught.value.errors()
    assert err["type"] == "type", err
    assert err["loc"] == ("cursor",), err


def test_the_model_alone_accepts_that_null_which_is_why_the_schema_decides() -> None:
    """The control for the test above, and the reason the docstring on
    ``AdCPBaseModel`` has to say what ``model_validate`` skips.

    The annotation is ``str | None``, so the constructor admits the null.  Were
    this to start raising, the test above would pass whether or not
    ``strict_validate`` consulted the schema at all.
    """
    assert PaginationRequest.model_validate({"cursor": None}).cursor is None


def test_a_constraint_the_annotation_carries_is_refused_on_its_own_keyword() -> None:
    """``minimum: 1`` is in the annotation too (``Field(ge=1)``), so this grades
    the keyword MAPPING: pydantic's own name for it is ``greater_than_equal``,
    and the document's is ``minimum``."""
    with pytest.raises(ValidationError) as caught:
        PaginationRequest.strict_validate({"max_results": 0})
    (err,) = caught.value.errors()
    assert err["type"] == "minimum", err
    assert err["loc"] == ("max_results",), err


def test_a_conforming_payload_is_constructed_and_an_omitted_key_stays_omitted() -> None:
    """The second half of one call: the verdict is the schema's and the value is
    pydantic's, including ``model_fields_set``, which is what makes an omitted
    optional round-trip as omitted."""
    value = PaginationRequest.strict_validate({"max_results": 7})
    assert isinstance(value, PaginationRequest)
    assert value.max_results == 7
    assert value.model_fields_set == {"max_results"}
    assert value.cursor is None


def test_a_class_bound_to_no_document_refuses_instead_of_grading_nothing() -> None:
    """A class with no row in the binding table has no schema to ask.  Accepting
    the payload anyway would be ``model_validate`` under another name, and a
    harness pointed at such a class would report a constructor as an accepted
    set."""

    class Unbound(AdCPBaseModel):
        pass

    with pytest.raises(LookupError, match="bound to no document"):
        Unbound.strict_validate({})
    with pytest.raises(LookupError, match="bound to no document"):
        AdCPBaseModel.strict_validate({})


def test_every_emitted_class_resolves_to_the_document_it_was_emitted_from() -> None:
    """The refusal above is for a class nothing emitted.  No emitted class may
    reach it, and each must land on its OWN document: a lookup that resolved to
    the wrong row would decide acceptance against another schema and still be
    green everywhere else."""
    table = adapter.bindings(TREE)
    assert len(table) > 1, len(table)
    for document, row in sorted(table.items()):
        model = getattr(importlib.import_module(row["module"]), row["symbol"])
        assert _document_of(model) == (document, row["schema"]), document
