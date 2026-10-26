"""§6's ``discriminator`` row at a NESTED union, and the sibling screen that admits it.

``salesagent-j3k2l.67``.  ``union.ROOT_CLAIMS`` admitted the keyword at a root union
with the reason written beside it -- it constrains nothing, so ignoring it cannot make
the model wider than its document, and it is READ there as the property §4 "Names" takes
a branch's name from.  ``union.nested``'s screen refused it, on a sentence whose stated
mechanism is a CONSTRAINING sibling's: the fact has nowhere to go on a
``ir.TypeRef``, and dropping it is reported ``missing`` by the comparison.

That mechanism does not reach this keyword, and both halves are graded here:

* the keyword constrains nothing, which §6's own row states -- "Nothing on the class.
  It names a branch where that branch pins more than one ``const``, and separately it
  CONFIRMS a dispatch key the branches already state -- it does not establish one";
* the comparison does not look for it, so a model whose node is a bare ``oneOf`` is
  reported ``missing`` nothing at that pointer.  That is asserted BY RUNNING the
  comparison over a real pair, not by reading the compared set.

A constraining sibling still refuses, which is the perturbation under each assertion: the
screen was narrowed by one name and not opened.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from codegen import bundle, compiler, emit, harness
from codegen.lower import union as lower_union

from nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
DRAFT = "http://json-schema.org/draft-07/schema#"

#: The two union keywords, read off the module under test rather than retyped.
UNION = lower_union.UNION


def _sites(document: dict) -> list[str]:
    """Every pointer of a document that is a union carrying a ``discriminator``."""
    found: list[str] = []

    def walk(node: Any, pointer: str) -> None:
        if isinstance(node, dict):
            if (
                any(isinstance(node.get(kw), list) for kw in UNION)
                and "discriminator" in node
            ):
                found.append(pointer or "/")
            for key, value in node.items():
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{pointer}/{i}")

    walk(document, "")
    return found


def _nested_sites() -> dict[str, list[str]]:
    """The bundle's NESTED ``discriminator``-beside-a-union sites, by document.

    A ROOT site is left out: the table already admits the keyword there, and this
    row is about the other position.
    """
    out = {}
    for document in sorted(bundle.portable(BUNDLE)):
        nested = [p for p in _sites(bundle.read(BUNDLE, document)) if p != "/"]
        if nested:
            out[document] = nested
    return out


def test_the_position_this_row_is_about_is_a_real_population() -> None:
    """The sites and the documents, named and non-empty, so the assertions below are not
    a derivation that selects nothing.

    Partitioned by what the keyword's admission does for each document, because the two
    outcomes are different and their sum is not a number: one document EMITS, and the
    rest refuse one pointer deeper on keywords other rows own.  Which keyword each waits
    on is those rows' fact and moves when they land, so it is not pinned here.
    """
    sites = _nested_sites()
    documents = claimed("documents carrying a nested discriminator", set(sites))
    claimed(
        "nested discriminator sites", [(d, p) for d, ps in sites.items() for p in ps]
    )
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    partitions(
        documents,
        emits=documents & set(out.emitted),
        refuses_elsewhere=documents - set(out.emitted),
    )
    # NOT on this keyword, anywhere in the run, chains included: that is the whole of
    # what the admission changes about the report.
    assert [d for d, r in out.refusals.items() if r["keyword"] == "discriminator"] == []
    assert [
        d
        for d, r in out.refusals.items()
        if "discriminator: a sibling of a nested" in r["detail"]
    ] == []


def test_the_comparison_does_not_look_for_the_keyword_at_the_pointer_it_sits_at() -> (
    None
):
    """The exit condition's harness half, RUN rather than read off the compared set.

    ``media-buy/outcome-target.json`` is the one document of the population that emits,
    and its union sits at ``/properties/goal`` with the keyword beside it.  The pair is
    built the way the tree's own pairs are -- the document's own node against the class
    that names it -- and the obligation is that nothing is reported ``missing`` or
    ``differs`` at that pointer.  A keyword the comparison DID look for would be reported
    there, which is the sentence the screen refused on and the half that does not hold.
    """
    document = "media-buy/outcome-target.json"
    read = bundle.read(BUNDLE, document)
    at = claimed(f"{document}'s discriminator sites", _sites(read))
    assert at == {"/properties/goal"}, sorted(at)

    out = emit.emit(BUNDLE, [document])
    assert document in out.emitted, out.refusals.get(document)
    resolved = bundle.record(BUNDLE, document)
    classes = _declared(out, document)
    root = claimed(
        "classes naming the document root",
        [c for c in classes if c.__adcp_schema__.pointer in ("#", "#/")],
    )
    (base,) = root
    report = harness.compare_schema(resolved, base, document=resolved)
    assert report.compared, report
    assert not report.missing, report.missing
    assert not report.differs, report.differs
    assert not report.added, report.added
    # The keyword's own pointer, named, so a green report over a node that never reached
    # the union cannot pass for this assertion.
    assert "goal" in base.model_fields, sorted(base.model_fields)
    assert "discriminator" in resolved["properties"]["goal"], sorted(
        resolved["properties"]["goal"]
    )


def test_a_constraining_sibling_of_a_nested_union_still_refuses() -> None:
    """The perturbation: the screen was narrowed by ONE NAME.

    The same node with a ``minLength`` beside the union states a fact about the instance
    with nowhere to go on an ``ir.TypeRef``, so it refuses on
    :data:`union._NESTED_SIBLING` -- and it refuses on THAT keyword, not on the
    ``discriminator`` beside it, which is the attribution a refusal report is for.
    """
    admitted = _fixture(_NESTED)
    refused = _fixture(_constrained(_NESTED))
    try:
        out = emit.emit(admitted, ["root.json"])
        assert not out.refusals, out.refusals

        blocked = emit.emit(refused, ["root.json"])
        assert "root.json" in blocked.refusals, blocked.emitted
        row = blocked.refusals["root.json"]
        assert (row["keyword"], row["pointer"]) == ("minLength", "/properties/goal"), (
            row
        )
        assert "no slot for a fact of its own" in row["detail"], row
    finally:
        shutil.rmtree(admitted)
        shutil.rmtree(refused)


def test_the_keyword_is_read_at_this_position_and_not_merely_tolerated() -> None:
    """§4 "Names"'s ``const`` choice reads ``discriminator.propertyName`` HERE too.

    Two properties pinned on every branch is the case where the keyword decides, because
    :func:`union._const_pin` takes a single pin without it and refuses to choose between
    two by spelling.  So the branch names are a function of what the keyword names: with
    ``propertyName: "kind"`` the arms are named off ``kind``, and the same branches with
    the keyword gone have no identity at all.

    :func:`union.branch_identity` is the one reading of those rules and :func:`union.nested`
    is one of its two callers, so this is the nested position's naming and not the root's.
    """
    branches = [
        {
            "type": "object",
            "properties": {"kind": {"const": "a"}, "shape": {"const": "round"}},
        },
        {
            "type": "object",
            "properties": {"kind": {"const": "b"}, "shape": {"const": "square"}},
        },
    ]
    keyed = {"discriminator": {"propertyName": "kind"}, "oneOf": branches}
    named = claimed(
        "branch identities under the keyword",
        [lower_union.branch_identity(b, "X", keyed) for b in branches],
    )
    assert named == {"XA", "XB"}, sorted(named)
    assert {
        lower_union.branch_identity(b, "X", {"oneOf": branches}) for b in branches
    } == {None}


# --------------------------------------------------------------------------- #
# the fixtures and the two helpers, all through the production pipeline
# --------------------------------------------------------------------------- #
#: A document whose one nested union carries the keyword and nothing else.  Object root
#: with a ``title``, so the root is a class the comparison has a pair for.
_NESTED: dict[str, Any] = {
    "$schema": DRAFT,
    "title": "Goal Holder",
    "type": "object",
    "additionalProperties": False,
    "required": ["goal"],
    "properties": {
        "goal": {
            "description": "The outcome to plan against.",
            "discriminator": {"propertyName": "kind"},
            "oneOf": [
                {
                    "type": "object",
                    "title": "Metric Goal",
                    "additionalProperties": False,
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string", "const": "metric"}},
                },
                {
                    "type": "object",
                    "title": "Event Goal",
                    "additionalProperties": False,
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string", "const": "event"}},
                },
            ],
        }
    },
}


def _constrained(document: dict) -> dict:
    """The same document with a CONSTRAINING sibling beside the same union."""
    out = json.loads(json.dumps(document))
    out["properties"]["goal"]["minLength"] = 3
    return out


def _fixture(document: dict) -> Path:
    """A bundle directory holding one ``root.json``."""
    at = Path(tempfile.mkdtemp())
    (at / "root.json").write_text(json.dumps(document))
    return at


def _declared(out: emit.Emitted, document: str) -> list[Any]:
    """Every class the run wrote for ``document``, by importing what it wrote.

    The WRITTEN package rather than the rendered text, for ``test_ref_branch_union``'s
    reason: a class carrying a union is exactly the shape that can render and not import.
    """
    at = Path(tempfile.mkdtemp())
    try:
        emit.write(out, at / "pkg", None)
        sys.path.insert(0, str(at))
        try:
            for name in [n for n in sys.modules if n == "pkg" or n.startswith("pkg.")]:
                del sys.modules[name]
            module = importlib.import_module(
                "pkg." + emit.module_path(document).replace("/", ".")
            )
        finally:
            sys.path.remove(str(at))
        return [
            value
            for value in vars(module).values()
            if isinstance(value, type)
            and getattr(value, "__adcp_schema__", None) is not None
            and value.__adcp_schema__.document == document
        ]
    finally:
        shutil.rmtree(at)


def test_the_refusal_sentence_names_no_owner_for_the_position() -> None:
    """A verdict needs no row, and the sentence that said it did sent a reader looking
    for an owner that does not exist.

    :data:`union._NESTED_SIBLING` is the detail text 44 documents carry, so the sentence
    was the most-read text in the module's refusals.  It is complete without the clause,
    and this asserts the clause is gone rather than trusting the edit.
    """
    assert "needs a row" not in lower_union._NESTED_SIBLING
    assert "ROOT_CONJUNCTS" not in lower_union._NESTED_SIBLING
    assert lower_union._NESTED_SIBLING.endswith("missing fact at this very pointer")


def test_the_screen_admits_exactly_the_one_name() -> None:
    """The narrowing is one name, and the TABLE is where it is written.

    This module used to carry a ``NESTED_HANDLED`` set naming ``discriminator`` here,
    beside ``compiler.ANNOTATIONS`` naming every other member of §6's table -- one
    decision in two places, differing only in the position each reached.  §6's own row
    carries no position split, so ``codegen.keywords`` admits the keyword at every
    position and this module names nothing: asserted as the CELL, in both directions.
    """
    from codegen import keywords
    from codegen.keywords import Effect, Position

    for position in Position:
        answer = keywords.cell("discriminator", position)
        assert answer is not None and answer.effect is Effect.NOTHING, position
        assert not answer.rendered, position
    # The other direction: this module holds no keyword set for a screen to read, so
    # there is no second place for §6's row to drift to.
    assert not [name for name in vars(lower_union) if name.endswith("_HANDLED")]
