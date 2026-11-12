"""**A SCALAR ``type`` KEYWORD IS A SET OF JSON TYPES, and the class admits that set.**

``docs/plan/final-state.md`` reading 1: the class accepts exactly what the document
accepts.  A JSON Schema ``type`` names JSON types and nothing else -- ``"1"`` is a string,
``true`` is a boolean, neither is an integer -- while pydantic's default is lax coercion,
so every numeric and boolean property in the tree admitted values its own document
refuses.  :data:`codegen.ir.STRICT_SCALAR` is the lowering that closes it and this file is
its gate.

**THE ORACLE IS ``jsonschema``'s OWN ``Draft7Validator``, asked of the keyword alone.**
Each case below reads the document's verdict from ``{"type": <word>}`` rather than from a
list written here, so the expected set is the draft's and not this file's opinion of it --
which is what makes ``1.0`` an INTEGER here (draft-07 counts a number with a zero
fractional part as one) rather than a value a reader might assume is refused.

**AND THE DIRECTION IS BOTH WAYS.**  A carrier that refuses a value the document admits is
an over-refusal and is the failure this epic has none of; the parity measurement
(``tests/conformance/test_schema_model_parity.py``) reads 0 rows in that direction and a
strict scalar is the one change most likely to open it, so every probe is asserted in both
directions rather than only on the laxity side.
"""

from __future__ import annotations

import pathlib
import re

import jsonschema
import pytest
from nodeset import claimed
from pydantic import TypeAdapter, ValidationError

from adcp.types import constraints
from codegen import ir

#: Every carrier the lowering names, by the document word it is the carrier FOR.  Read off
#: :data:`codegen.ir.STRICT_SCALAR` rather than restated, so a table edited there and not
#: here cannot pass: the keys are the builtins the renderer substitutes and the words are
#: ``codegen.schema.nodes.SCALAR``'s own.
WORDS = {
    "integer": constraints.SchemaInt,
    "number": constraints.StrictFloat,
    "boolean": constraints.StrictBool,
    #: ``string`` is in the table because its absence from ``STRICT_SCALAR`` is a MEASURED
    #: claim and not an omission: pydantic's lax ``str`` refuses every non-string, so the
    #: word is already exact and the gate proves it alongside the three that moved.
    "string": str,
}

#: The values a case probes, one per JSON type the three numeric and boolean words can be
#: confused across, plus the two that separate ``integer`` from ``number``.  ``None`` is
#: absent on purpose: a ``null`` is the PRESENCE question an optional property answers
#: (``adcp.types._base.OmittedNotNull``) and not a question about the type word.
PROBES = (1, 0, 1.0, 1.5, -1, True, False, "1", "", "x")


def _document_admits(word: str, value: object) -> bool:
    """What ``{"type": word}`` itself says, which is the only expectation this file has."""
    return jsonschema.Draft7Validator({"type": word}).is_valid(value)


def _model_admits(carrier: object, value: object) -> bool:
    try:
        TypeAdapter(carrier).validate_python(value)
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize("word", sorted(WORDS))
def test_the_carrier_for_a_type_word_admits_exactly_what_the_word_admits(word: str) -> None:
    """One case per JSON type, and the refusals are the KEYWORD'S, quoted from it.

    A row that fails names the value and both verdicts, so a reader sees which direction
    broke: ``admits`` where the carrier is wider than the document (the laxity this
    closes) and ``refuses`` where it is narrower (an over-refusal, which is worse).
    """
    carrier = WORDS[word]
    probes = claimed(f"probe values for {word}", PROBES)
    assert probes  # claimed() asserts it; named so the denominator is visible
    wrong = {
        f"{value!r}": (
            "the carrier admits it and the document refuses it"
            if _model_admits(carrier, value)
            else "the document admits it and the carrier refuses it"
        )
        for value in PROBES
        if _model_admits(carrier, value) != _document_admits(word, value)
    }
    assert not wrong, f"{{'type': {word!r}}}: {wrong}"


def test_the_integer_carrier_reads_draft_07_s_integer_and_not_python_s() -> None:
    """``1.0`` is an INTEGER to draft-07, and the narrowing is why the carrier takes it.

    Stated on its own because it is the one place a reader's intuition and the document
    disagree, and because the marker that carries it
    (:data:`codegen.ir.SCHEMA_INTEGRAL`) is the half of the carrier that does not ride on
    the hint.  ``StrictInt`` alone refuses ``1.0``; the document admits it; a tree emitted
    with the bare strict int would therefore be NARROWER than its documents at every
    integer position.
    """
    assert _document_admits("integer", 1.0), "draft-07 counts a zero-fraction number as an integer"
    assert TypeAdapter(constraints.SchemaInt).validate_python(1.0) == 1
    assert not _model_admits(constraints.SchemaInt, 1.5)
    assert not _model_admits(constraints.SchemaInt, True)
    assert not _model_admits(constraints.SchemaInt, "1")


def test_a_bound_on_an_integer_keeps_the_document_s_own_keywords_in_the_published_schema() -> None:
    """The marker TRAILS ``Field(...)``, and this is the reading that forced the order.

    Measured on pydantic 2.13.5: a validator written INSIDE the annotation leaves
    ``ge``/``le`` in ``model_json_schema()`` where the document states ``minimum`` and
    ``maximum``.  The published schema is what ``tests_emit`` grades a class's facts by,
    so the ordering is load-bearing rather than cosmetic, and the emitted alias is the
    subject here rather than a constructed example.
    """
    published = TypeAdapter(constraints.IntMin1Max100).json_schema()
    assert published == {"type": "integer", "minimum": 1, "maximum": 100}, published
    assert _model_admits(constraints.IntMin1Max100, 1.0)
    assert not _model_admits(constraints.IntMin1Max100, True)
    assert not _model_admits(constraints.IntMin1Max100, 101)


def test_no_emitted_annotation_carries_a_bare_numeric_or_boolean_builtin() -> None:
    """The structural half: the lowering reached EVERY position, not the ones a probe hit.

    ``codegen.ir.STRICT_SCALAR`` substitutes at the one place a decided type becomes a
    hint, so a bare ``int``, ``float`` or ``bool`` surviving in the emitted tree means a
    position reached the renderer by another route.  The set is named rather than counted,
    and the scan is over the EMITTED TEXT because that is where a missed route shows.

    ``bool`` inside ``Literal[True]`` is not a builtin annotation and does not match; a
    ``dict[str, int]`` value type does, and is a position the document's ``type`` keyword
    states exactly as a property's is.
    """
    tree = pathlib.Path(ir.__file__).parents[1] / "src" / "adcp" / "types" / "_schemas"
    modules = claimed("emitted modules", [p for p in tree.rglob("*.py")])
    bare = re.compile(r"(?<![\w.])(?:int|float|bool)(?![\w.])")
    found: dict[str, list[str]] = {}
    for path in sorted(modules):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            # Only the annotation half of a declaration, which is what the lowering owns:
            # a default, a docstring and a ``json_schema_extra`` literal all spell these
            # words for reasons that are not a type.
            annotation = stripped.split("=", 1)[0]
            if ":" not in annotation:
                continue
            if bare.search(annotation.split(":", 1)[1]):
                found.setdefault(str(path.relative_to(tree)), []).append(f"{number}: {stripped[:90]}")
    assert not found, found


def test_pagination_request_refuses_the_four_values_its_document_refuses() -> None:
    """The reported reproduction, as a case: ``core/pagination-request.json``.

    ``#/properties/max_results`` is ``{"type": "integer", "minimum": 1, "maximum": 100}``,
    and all four of these were ACCEPTED before the lowering -- two through
    ``model_validate`` and two through ``model_validate_json``, which is both doors.
    """
    from adcp.types.core import PaginationRequest

    for value in ("1", True):
        with pytest.raises(ValidationError):
            PaginationRequest.model_validate({"max_results": value})
    for payload in ('{"max_results":"1"}', '{"max_results":true}'):
        with pytest.raises(ValidationError):
            PaginationRequest.model_validate_json(payload)
    assert PaginationRequest.model_validate({"max_results": 1}).max_results == 1
    assert PaginationRequest.model_validate({"max_results": 1.0}).max_results == 1
