"""§4's third dispatch source: branches no instance satisfies twice.

``salesagent-j3k2l.67``.  §4's dispatch paragraph names three sources and the third is
"Where the branches are pairwise disjoint, the payload selects its own branch and the
order they are tried in cannot change which one it reaches.  Disjointness is derived from
the branches themselves: one property pinned to different ``const`` values, a ``required``
name one branch declares and another forbids, or scalar branches of different ``type``.  A
pair the derivation cannot separate is treated as overlapping, because admitting a union
on an unproven disjointness is the defect this source exists to avoid."

Two things are graded here and they are separate claims:

* the DERIVATION -- each of the three separators, on the pairs it decides in the bundle
  and on a constructed pair, so a separator that decides nothing in the bundle is still
  shown to work rather than taken on trust;
* the REFUSAL for the overlapping remainder -- a root matching none of the three sources,
  refused on OVERLAP, naming the pairs, and DEFERRED because §4's second source is
  unwritten.

The derivation comes first in both the module and this file, because it is what keeps the
refusal small: of the 7 roots that reach it, 5 separate and get past the dispatch and the
refusal claims the other 2.  Getting past the dispatch is not the same as emitting --
``core/postal-area.json`` separates and then refuses on a ``$ref`` of its own -- so the
assertions below are on the dispatch and not on the emitted set.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from codegen import bundle, emit, keywords
from codegen.lower import union as lower_union
from codegen.refusal import Kind
from codegen.schema import nodes, parse as schema_parse

from nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
DRAFT = "http://json-schema.org/draft-07/schema#"

#: What each separator's answer says, so a test can tell which one decided a pair without
#: a second copy of the three rules.
PINNED = "is pinned to"
FORBIDDEN = "and the other declares no such property"
SCALAR = "are scalars of type"


def _branch(**node: Any) -> lower_union.Branch:
    """One planned branch at a throwaway pointer.

    The derivation reads the branch's DECLARATION -- §4 "Names" and the dispatch sources
    are readings of one (:attr:`codegen.schema.nodes.Union.branch_raw`) -- and the parsed
    node beside it is what a branch's CLASS row takes, which no separator asks for.  It
    is built by the production parse at BRANCH so that the planned branch here is the
    shape ``_plan`` returns.
    """
    declaration = dict(node)
    return lower_union.Branch(
        pointer="/oneOf/0",
        node=declaration,
        parsed=schema_parse.parse(
            declaration,
            pointer="/oneOf/0",
            position=keywords.Position.BRANCH,
            source=schema_parse.Source(document="probe.json"),
        ),
    )


# --------------------------------------------------------------------------- #
# the derivation, separator by separator
# --------------------------------------------------------------------------- #
def test_a_property_pinned_to_different_consts_separates_a_pair() -> None:
    """§4's first separator, and the half that makes it a separator: an instance
    carrying one value fails the branch pinning the other, so no instance satisfies both.

    The same two branches pinning the SAME value are not separated by it, which is the
    perturbation -- and it is also why this is not :func:`union.discriminator`: that one
    needs the property SHARED by every branch, and this one needs only the pair.
    """
    one = _branch(type="object", properties={"kind": {"const": "a"}})
    two = _branch(type="object", properties={"kind": {"const": "b"}})
    same = _branch(type="object", properties={"kind": {"const": "a"}})
    assert PINNED in (lower_union.separates(one, two, None, None) or ""), one
    assert lower_union.separates(one, same, None, None) is None


def test_a_required_name_the_other_branch_forbids_separates_a_pair() -> None:
    """§4's second separator.  "Forbids" is a closed branch that declares no such
    property: an instance carrying the name fails it, and one without the name fails the
    branch that requires it.

    Asked in BOTH directions, and the perturbations have to break both: one branch
    forbidding the other's required name separates the pair whichever of the two is read
    first.  Three ways for it to stop separating -- each branch declares the other's name
    after all, neither is closed, or the closure is taken back by a ``patternProperties``
    -- and the pair really does overlap in each: ``{"account_id": …, "brand": …}``
    satisfies both.
    """

    def pair(mine: str, theirs: str, **extra: Any) -> lower_union.Branch:
        declared = {
            name: {"type": "string"} for name in (mine, *([theirs] if theirs else []))
        }
        return _branch(type="object", properties=declared, required=[mine], **extra)

    closed = {"additionalProperties": False}
    separated = (pair("account_id", "", **closed), pair("brand", "", **closed))
    assert FORBIDDEN in (lower_union.separates(*separated, None, None) or ""), separated
    assert FORBIDDEN in (lower_union.separates(*separated[::-1], None, None) or ""), (
        separated
    )

    for one, other in (
        (pair("account_id", "brand", **closed), pair("brand", "account_id", **closed)),
        (pair("account_id", ""), pair("brand", "")),
        (
            pair(
                "account_id",
                "",
                additionalProperties=False,
                patternProperties={"^x_": {}},
            ),
            pair(
                "brand", "", additionalProperties=False, patternProperties={"^x_": {}}
            ),
        ),
    ):
        assert lower_union.separates(one, other, None, None) is None, (one, other)
        assert lower_union.separates(other, one, None, None) is None, (one, other)


def test_scalar_branches_of_different_type_separate_a_pair_and_the_walk_delivers_none() -> (
    None
):
    """§4's third separator, graded on a constructed pair BECAUSE its set in the bundle
    is empty -- and the emptiness is derived here rather than asserted as a count.

    Two checks upstream make it empty: ``lower_union`` refuses a root whose own ``type``
    is neither absent nor ``"object"``, and ``_plan`` refuses a branch whose own ``type``
    is neither.  So every pair the derivation is handed has both applied types in
    ``{None, "object"}``, which is asserted over the whole portable set.  A union whose
    branches really are scalars is a root scalar and reaches ``_alias``, which declares no
    branch classes and needs no dispatch.
    """
    one, two = _branch(type="string"), _branch(type="integer")
    assert SCALAR in (lower_union.separates(one, two, "string", "integer") or ""), one
    assert lower_union.separates(one, two, "string", "string") is None
    assert lower_union.separates(one, two, None, "integer") is None

    # The walk's own branches, over every union root of the bundle: both halves of the
    # clause's guard are false for all of them, which is WHY the separator decides none.
    # Through the production parse, so the node asked is the node the walk asks: the
    # applied word is a field the PARSER assigned (``nodes.Union.word`` handed down at
    # the hop), not a second derivation over the document.
    applied = claimed(
        "applied types over the branches of every union root",
        [
            lower_union.applied_type(root, i)
            for document in sorted(bundle.portable(BUNDLE))
            for doc in [bundle.read(BUNDLE, document)]
            if lower_union.keyword(doc) is not None and doc.get("type") in (None, "object")
            for root in [
                schema_parse.parse(
                    doc,
                    pointer="",
                    position=keywords.Position.ROOT,
                    source=schema_parse.Source(
                        document=document, applied_at=bundle.constrained_to_object(doc)
                    ),
                )
            ]
            if isinstance(root, nodes.Union)
            for i, branch in enumerate(root.branch_raw)
            if isinstance(branch, dict) and branch.get("type") in (None, "object")
        ],
    )
    assert applied <= {None, "object"}, sorted(
        t for t in applied if t not in (None, "object")
    )


def test_the_derivation_decides_the_roots_that_reach_it_and_the_refusal_takes_the_rest() -> (
    None
):
    """The population, named and partitioned: 7 roots reach the hand-off from §4's first
    source, and each one is either pairwise disjoint or refused on overlap.

    The partition is the assertion, because the two outcomes are different facts and
    their sum is not a number.  ``core/postal-area.json`` is disjoint and still refuses,
    on a ``$ref`` of its own, which is why the disjoint half is not "the emitted half".
    """
    named = claimed(
        "union roots whose first-source dispatch is expected to be empty",
        {
            "a2ui/bound-value.json",
            "adagents.json",
            "brand.json",
            "core/account-ref.json",
            "core/audience-selector.json",
            "core/canonical-account-ref.json",
            "core/postal-area.json",
        },
        inside=bundle.portable(BUNDLE),
    )
    # DERIVED and not just named: the roots that actually reach the derivation in the
    # walk, recorded at the call.  A hand-written list alone would still be partitioned
    # cleanly by a derivation that had stopped running, and the titles are what the
    # function is handed -- the document path is the walk's and not this call's.
    out, titles = _reaching(sorted(bundle.portable(BUNDLE)))
    assert titles == {bundle.read(BUNDLE, d).get("title") for d in named}, sorted(
        titles
    )
    reached = named
    overlapping = {
        d
        for d in reached
        if "branches OVERLAP" in out.refusals.get(d, {}).get("detail", "")
    }
    partitions(reached, overlapping=overlapping, disjoint=reached - overlapping)
    claimed("roots refused on overlap", overlapping, inside=reached)
    disjoint = claimed(
        "roots the third source dispatches", reached - overlapping, inside=reached
    )
    # Every disjoint root got PAST the dispatch: it emits, or it refuses on something
    # else entirely.  Asserted as "not on overlap" rather than "emits", because what each
    # one then waits on is another row's fact.
    for document in sorted(disjoint):
        assert "branches OVERLAP" not in out.refusals.get(document, {}).get(
            "detail", ""
        ), document
    assert disjoint & set(out.emitted), sorted(disjoint)


# --------------------------------------------------------------------------- #
# the refusal for the overlapping remainder
# --------------------------------------------------------------------------- #
def test_a_root_whose_branches_overlap_refuses_on_overlap_and_defers() -> None:
    """§4's refusal sentence, through the real entry point.

    Two open branches requiring different names overlap: an instance carrying both keys
    satisfies both, so a branch could only be reached by trying each and keeping the
    first that validates.  The refusal names the keyword, the root pointer, the PAIRS and
    §4's three sources, and its kind is a DEFERRAL -- the second source is a key the
    bundle's manifest states, which is ``salesagent-j3k2l.60``'s unwritten row, and a
    verdict would count a clearable document as finally refused.
    """
    at = _fixture(_OVERLAPPING)
    try:
        out = emit.emit(at, ["root.json"])
        assert "root.json" not in out.emitted, out.emitted
        row = out.refusals["root.json"]
        assert (row["keyword"], row["pointer"]) == ("oneOf", "/"), row
        assert row["kind"] is Kind.DEFERRED, row
        assert row["resolved"] is Kind.DEFERRED, row
        assert "OVERLAP" in row["detail"], row
        # The pairs by pointer, so a reader of a 15-branch root does not have to re-run
        # the emitter to find which two.
        assert "/oneOf/0 and /oneOf/1" in row["detail"], row
        assert "salesagent-j3k2l.60" in row["detail"], row
    finally:
        shutil.rmtree(at)


def test_closing_the_same_two_branches_separates_them_and_the_root_emits() -> None:
    """The perturbation on the refusal: the SAME two branches, closed.

    Each one then forbids the name the other requires, so the pair separates on §4's
    second separator and the root emits with no dispatch key at all -- which is the third
    source being a dispatch rather than a relaxation.  ``_BRANCH_DISCRIMINATOR`` is empty
    on the base, and that is the observable difference from a first-source root.
    """
    document = json.loads(json.dumps(_OVERLAPPING))
    for branch in document["oneOf"]:
        branch["additionalProperties"] = False
    at = _fixture(document)
    try:
        out = emit.emit(at, ["root.json"])
        assert not out.refusals, out.refusals
        assert '_BRANCH_DISCRIMINATOR: ClassVar[str] = ""' in out.files["root.py"], (
            out.files["root.py"]
        )
    finally:
        shutil.rmtree(at)


#: Two branches an instance can satisfy at once: both open, each requiring a name the
#: other does not declare, so neither forbids anything.
_OVERLAPPING: dict[str, Any] = {
    "$schema": DRAFT,
    "title": "Either Way",
    "type": "object",
    "oneOf": [
        {
            "type": "object",
            "title": "By Location",
            "required": ["authoritative_location"],
            "properties": {"authoritative_location": {"type": "string"}},
        },
        {
            "type": "object",
            "title": "By House",
            "required": ["house"],
            "properties": {"house": {"type": "string"}},
        },
    ],
}


def _fixture(document: dict) -> Path:
    """A bundle directory holding one ``root.json``."""
    at = Path(tempfile.mkdtemp())
    (at / "root.json").write_text(json.dumps(document))
    return at


def _reaching(population: list[str]) -> tuple[Any, set[str | None]]:
    """Emit, and record which roots reached :func:`union.overlapping`.

    Recorded AT THE CALL, so the set is what the walk produced rather than what a reader
    believes it produces.  By ``title``, because that is the only name of the document in
    scope there -- the function is handed the union NODE, whose title is its own
    annotation (:attr:`codegen.schema.nodes.Base.title`).
    """
    seen: set[str | None] = set()
    real = lower_union.overlapping

    def traced(planned: Any, node: Any) -> list[str]:
        seen.add(node.annotations.get("title"))
        return real(planned, node)

    lower_union.overlapping = traced  # type: ignore[assignment]
    try:
        return emit.emit(BUNDLE, population), seen
    finally:
        lower_union.overlapping = real  # type: ignore[assignment]
