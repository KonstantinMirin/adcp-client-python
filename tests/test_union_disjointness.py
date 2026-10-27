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

import importlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Literal

from pydantic import create_model

from adcp.types._base import UNDERDETERMINED, SchemaRef, schema_at
from codegen import bundle, emit, harness, keywords
from codegen.keywords import Rung
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
            # **7 -> 40 AT ``adcp-client-python-10l.20``, and the whole of the move is
            # that these roots REACH the derivation now** (§14 step 9).  Every one of
            # the 33 added states ``properties``, ``required``,
            # ``additionalProperties`` or ``allOf`` beside its combinator, and
            # ``union.ROOT_CONJUNCTS`` refused it before the dispatch was ever derived
            # -- "there is no pointer to the conjunction for a branch class to name".
            # §8's pairing rule answers that, so the root's siblings compile onto the
            # base and the walk gets as far as asking §4's question about the branches.
            # The derivation itself is unchanged in substance; what changed is its
            # denominator, which is the number this set exists to carry.
            "a2ui/bound-value.json",
            "account/get-account-financials-response.json",
            "account/sync-accounts-response.json",
            "account/sync-governance-response.json",
            "adagents.json",
            "brand.json",
            "brand/acquire-rights-response.json",
            "brand/creative-approval-response.json",
            "brand/get-brand-identity-response.json",
            "brand/get-rights-response.json",
            "brand/search-brands-response.json",
            "brand/update-rights-response.json",
            "brand/verify-brand-claim-response.json",
            "brand/verify-brand-claims-response.json",
            "compliance/comply-test-controller-response.json",
            "content-standards/calibrate-content-response.json",
            "content-standards/create-content-standards-response.json",
            "content-standards/get-content-standards-response.json",
            "content-standards/get-media-buy-artifacts-response.json",
            "content-standards/list-content-standards-response.json",
            "content-standards/validate-content-delivery-response.json",
            "core/account-ref.json",
            "core/audience-selector.json",
            "core/canonical-account-ref.json",
            "core/evaluator-spec.json",
            "core/postal-area.json",
            "core/postal-country-system.json",
            "creative/get-creative-features-response.json",
            "creative/sync-creatives-response.json",
            "media-buy/build-creative-response.json",
            "media-buy/create-media-buy-response.json",
            "media-buy/log-event-response.json",
            "media-buy/provide-performance-feedback-response.json",
            "media-buy/request-proposals-response.json",
            "media-buy/sync-audiences-response.json",
            "media-buy/sync-catalogs-response.json",
            "media-buy/sync-event-sources-response.json",
            "media-buy/update-media-buy-response.json",
            "signals/activate-signal-response.json",
            "trusted-match/provider-registration.json",
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
    # **The document's OWN refusal and not a CHAIN quoting one** -- a chained refusal's
    # detail carries its target's sentence verbatim, so a document behind an overlapping
    # root read as overlapping itself.  Measured at ``adcp-client-python-10l.20``:
    # ``core/postal-area.json`` separates its own two branches and refuses on a ``$ref``
    # into ``core/postal-country-system.json``, which overlaps -- and this predicate put
    # it in the overlapping half, which is the one claim about it the docstring above
    # says is false.
    # **READ OFF THE SET ``adcp-client-python-10l.21`` NAMES, because an overlapping root
    # no longer REFUSES.**  §4's own answer is written: "a union matching none of the
    # three emits a plain ``A | B`` over its branches and declares an UNDERDETERMINED
    # approximation at the union's pointer".  So there is no refusal detail to read the
    # overlapping half off, and the two halves are told apart by the declaration -- which
    # ``harness.underdetermined_census`` is the equality on, in both directions, and is
    # where a root joining or leaving the set reddens.
    overlapping = OVERLAPPING_ROOTS & reached
    partitions(reached, overlapping=overlapping, disjoint=reached - overlapping)
    claimed("roots the derivation cannot separate", overlapping, inside=reached)
    disjoint = claimed(
        "roots the third source dispatches", reached - overlapping, inside=reached
    )
    # Every root the derivation cannot separate either EMITS with the declaration or
    # refuses further on, on another row's keyword -- and never on the overlap.
    declaring = {
        d
        for d, declared in out.approximations.items()
        for one in declared
        if one.kind == UNDERDETERMINED
    }
    assert declaring <= overlapping, sorted(declaring - overlapping)
    assert declaring == overlapping - set(out.refusals), sorted(declaring)
    for document in sorted(reached):
        row = out.refusals.get(document, {})
        assert "branches OVERLAP" not in row.get("detail", ""), document
    assert disjoint & set(out.emitted), sorted(disjoint)


# --------------------------------------------------------------------------- #
# the refusal for the overlapping remainder
# --------------------------------------------------------------------------- #
def test_a_root_whose_branches_overlap_declares_underdetermined_and_emits() -> None:
    """**§4's own answer, through the real entry point** (``adcp-client-python-10l.21``).

    Two open branches requiring different names overlap: an instance carrying both keys
    satisfies both, so a branch can only be reached by trying each and keeping the first
    that validates.  §4: "a union matching none of the three emits a plain ``A | B`` over
    its branches and declares an UNDERDETERMINED approximation at the union's pointer."
    So the document EMITS, and WHICH branch an overlapping payload becomes is the fact
    dropped -- declared, with a rung and an attribution neither of which the handler
    chose.

    The pointer is the UNION's and not the node's, because that is the spelling
    ``harness.inseparable_unions`` yields and §8's third equality compares the two sets
    pointer by pointer.
    """
    at = _fixture(_OVERLAPPING)
    try:
        out = emit.emit(at, ["root.json"])
        assert out.refusals == {}, out.refusals
        assert "root.json" in out.emitted, out.emitted
        (one,) = out.approximations["root.json"]
        assert (one.document, one.pointer, one.keyword) == ("root.json", "#/oneOf", "oneOf")
        assert one.kind == UNDERDETERMINED, one
        # The rung is the cell's and the attribution the cell's own address: §2 gives a
        # handler neither to choose.
        assert one.rung == Rung.JOIN.value, one
        assert one.attribution == keywords.address("oneOf"), one
        # The FACT is the document's own branch declarations, so §8 can look for it in
        # the document and find it (§9: never approximate on a keyword the walk inserted).
        assert list(one.fact) == _OVERLAPPING["oneOf"], one.fact
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


# --------------------------------------------------------------------------- #
# §4's SECOND dispatch source: a key the bundle's manifest states
# --------------------------------------------------------------------------- #
#: Every portable document declaring a ``task_type`` property -- the field
#: ``manifest.task_result_resolution`` names as its discriminator -- at any pointer.
#: Read off the documents, so it is the population of §4's second source and not a
#: reading of a refusal.  **By NAME and not as a count**, which is §8's rule for a set a
#: check ranges over: a census equality is one tree's reading of a quantity an emitting
#: row moves (``tests/test_every_check_names_its_set.py``).
MANIFEST_DISCRIMINATED = frozenset(
    {
        "core/mcp-webhook-payload.json",
        "core/tasks-get-response.json",
        "core/tasks-list-request.json",
        "core/tasks-list-response.json",
        "protocol/get-task-status-response.json",
        "protocol/list-tasks-request.json",
        "protocol/list-tasks-response.json",
    }
)
#: Union roots the walk cannot separate: §4's three sources all answer no, so the union
#: declares §4's UNDERDETERMINED approximation.  ``adagents.json`` and ``brand.json``
#: overlapped before §14 step 9 and the root-siblings row let the other 16 reach the
#: derivation for the first time, which reconciles the previous instalment's 16 with this
#: set.
#:
#: **TWO LEFT AT ``adcp-client-python-10l.21``, and both left because the DERIVATION got
#: them right rather than because the set was relaxed** (``adcp-client-python-10l.27``):
#: ``media-buy/sync-audiences-response.json`` separates on §4's SECOND separator once the
#: ``not``/``anyOf`` reduction keeps the disjuncts it can read, and
#: ``media-buy/sync-catalogs-response.json`` on §4's FOURTH -- one branch forbids a VALUE
#: another pins.  Both emit, and neither declares an approximation, which is the
#: direction this set is pinned for.
OVERLAPPING_ROOTS = frozenset(
    {
        "adagents.json",
        "brand.json",
        "content-standards/calibrate-content-response.json",
        "content-standards/create-content-standards-response.json",
        "content-standards/get-content-standards-response.json",
        "content-standards/get-media-buy-artifacts-response.json",
        "content-standards/list-content-standards-response.json",
        "content-standards/validate-content-delivery-response.json",
        "core/evaluator-spec.json",
        "core/postal-country-system.json",
        "creative/get-creative-features-response.json",
        "creative/sync-creatives-response.json",
        "media-buy/build-creative-response.json",
        "media-buy/create-media-buy-response.json",
        "media-buy/update-media-buy-response.json",
        "trusted-match/provider-registration.json",
    }
)


def _declares(node: Any, field: str, pointer: str = "") -> list[str]:
    """Every pointer at which ``node`` declares ``field`` as a property."""
    found = []
    if isinstance(node, dict):
        if field in (node.get("properties") or {}):
            found.append(pointer or "/")
        for key, value in node.items():
            found += _declares(value, field, f"{pointer}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += _declares(value, field, f"{pointer}/{i}")
    return found


def test_the_manifests_dispatch_source_has_no_union_to_dispatch_in_this_bundle() -> None:
    """§4's SECOND source, measured rather than left looking unattempted (§14 step 9).

    "A key the bundle's manifest states.  ``manifest.task_result_resolution`` names the
    discriminator field and a template resolving a schema from it, and ``manifest.tools``
    is the table.  Such a union emits as a mapping keyed by that field: its discriminant
    is in the envelope, not in the payload."

    **Its population over bundle 3.2 is 0, and the reason is the SHAPE of the
    resolution rather than the count.**  The template is
    ``/tools/{task_type}/response_schema``: it resolves a DOCUMENT from a task field.  So
    the manifest's key is spent selecting the document, and a union INSIDE the document it
    selects has no discriminant left in the envelope to be told apart by.  Measured three
    ways here, each of which fails on its own:

    * every document declaring the manifest's discriminator field states NO union at
      all, at any pointer -- so there is nothing for the second source to dispatch;
    * no branch of any overlapping root declares that field, and no branch of one is a
      ``$ref`` to a schema the manifest resolves;
    * 13 of the 18 overlapping roots ARE a schema the manifest's own template resolves,
      which is the measurement that settles it: the manifest names the document and the
      overlap is a union inside it.

    So the overlapping set is **step 10's UNDERDETERMINED row** and not this one's.  §4
    decides what becomes of it -- "a union matching none of the three emits a plain
    ``A | B`` over its branches and declares an UNDERDETERMINED approximation at the
    union's pointer, attributed upstream" -- and the DECLARATION is what puts it there:
    the faithful rows cost none.
    """
    manifest = bundle.read(BUNDLE, "manifest.json")
    resolution = manifest["task_result_resolution"]
    field = resolution["discriminator_field"]
    key = resolution["terminal_schema_pointer_template"].strip("/").split("/")[-1]
    # The set the template can name, derived from the manifest's own table and overrides
    # rather than listed: a tool added upstream moves it.
    resolves = {tool[key] for tool in manifest["tools"].values() if key in tool}
    resolves |= set(resolution["terminal_schema_overrides"].values())
    assert (field, key) == ("task_type", "response_schema"), resolution
    claimed("manifest tools", manifest["tools"])
    claimed("schemas the manifest's template resolves", resolves)

    # 1. Every document carrying the manifest's key, and whether it states a union.
    carrying = [
        document
        for document in bundle.portable(BUNDLE)
        if _declares(bundle.read(BUNDLE, document), field)
    ]
    named = claimed(
        "documents declaring the manifest's discriminator field",
        carrying,
        inside=bundle.portable(BUNDLE),
    )
    assert named == set(MANIFEST_DISCRIMINATED), sorted(named)
    for document in sorted(named):
        # A combinator ANYWHERE in the document, read off the text: the claim is that
        # there is no union here at any pointer, and a walk that descended only the
        # positions a union root can sit at would be making the weaker claim.
        stated = [kw for kw in ("oneOf", "anyOf") if f'"{kw}"' in json.dumps(bundle.read(BUNDLE, document))]
        assert stated == [], (document, stated)

    # 2 and 3. The overlapping set, and what the manifest says about each one.
    #
    # **READ OFF THE DECLARATION AND NOT OFF A REFUSAL, because §4's own answer is now
    # written** (``adcp-client-python-10l.21``): "a union matching none of the three emits
    # a plain ``A | B`` over its branches and declares an UNDERDETERMINED approximation at
    # the union's pointer".  So an overlapping root no longer refuses on the overlap; it
    # EMITS and declares, or it refuses FURTHER ON, on another row's keyword, and the set
    # is the two halves together -- each half derived from the run and neither from the
    # other.
    out, _ = _reaching(sorted(bundle.portable(BUNDLE)))
    declaring = {
        d
        for d, declared in out.approximations.items()
        for one in declared
        if one.kind == UNDERDETERMINED
    }
    assert not any("branches OVERLAP" in r.get("detail", "") for r in out.refusals.values())
    deeper = {d for d in OVERLAPPING_ROOTS if d in out.refusals}
    overlapping = sorted(OVERLAPPING_ROOTS)
    assert declaring == set(OVERLAPPING_ROOTS) - deeper, sorted(declaring)
    # Every one of the rest reaches the derivation and reports its OWN next obstruction,
    # which is neither the overlap nor nothing: a document that silently stopped
    # refusing would be read here as the set going stale.
    for document in sorted(deeper):
        row = out.refusals[document]
        assert row["keyword"] != document, row
        assert "branches OVERLAP" not in row["detail"], (document, row)
    resolved_overlaps = [d for d in overlapping if d in resolves]
    for document in overlapping:
        # The union is the document's ROOT combinator, read off the document itself: an
        # overlapping root no longer refuses ON the overlap, so the refusal's pointer is
        # its own next obstruction and says nothing about where the union is.
        node = bundle.read(BUNDLE, document)
        stated = [kw for kw in ("oneOf", "anyOf") if isinstance(node.get(kw), list)]
        assert len(stated) == 1, (document, stated)
        branches = [b for b in node[stated[0]] if isinstance(b, dict)]
        assert branches, (document, stated)
        # No branch carries the envelope's key, and no branch is one of the schemas the
        # manifest resolves -- the two shapes the second source would read.
        assert not any(field in (b.get("properties") or {}) for b in branches), document
        assert not {
            b["$ref"].rsplit("/", 1)[-1] for b in branches if "$ref" in b
        } & {r.rsplit("/", 1)[-1] for r in resolves}, document
    # The decisive one: most of them ARE what the manifest resolves TO, so the key is
    # spent before the branch choice is reached.  Partitioned BY NAME, because the two
    # halves are different facts and their sum is not one: the resolved half is where
    # the manifest's key is spent on the document, and the other five are documents the
    # manifest does not name at all.
    partitions(
        set(overlapping),
        the_manifest_resolves_the_document=set(resolved_overlaps),
        the_manifest_does_not_name_it=set(overlapping) - set(resolved_overlaps),
    )
    claimed(
        "overlapping roots the manifest's template resolves",
        resolved_overlaps,
        inside=overlapping,
    )
    assert set(resolved_overlaps) == {
        "content-standards/calibrate-content-response.json",
        "content-standards/create-content-standards-response.json",
        "content-standards/get-content-standards-response.json",
        "content-standards/get-media-buy-artifacts-response.json",
        "content-standards/list-content-standards-response.json",
        "content-standards/validate-content-delivery-response.json",
        "creative/get-creative-features-response.json",
        "creative/sync-creatives-response.json",
        "media-buy/build-creative-response.json",
        "media-buy/create-media-buy-response.json",
        "media-buy/update-media-buy-response.json",
    }, sorted(resolved_overlaps)


# --------------------------------------------------------------------------- #
# §5's PINNED-VALUE clause: one class and one rule, and why it is not landed
# --------------------------------------------------------------------------- #
#: Annotation keys: a branch differing in one of these does NOT "differ only in the
#: `const` or `enum` each pins", and collapsing it would drop a fact §6 gives the
#: document authority over -- a branch `title` is a class NAME (§4) and a branch
#: `description` is its DOCSTRING.  The ``x-`` namespace joins them by prefix (§6).
_ANNOTATIONS = frozenset(
    {"title", "description", "$comment", "examples", "deprecated", "enumDescriptions"}
)
#: Sites where the branches differ in NOTHING but the pins: §5's pinned-value clause's
#: whole population over the portable set.
PINNED_VALUE_SITES = frozenset({"core/canonical-media-buy-action.json#"})
#: Sites that match once annotations are ignored.  The difference between the two sets is
#: the clause's own word "only", and both are named rather than counted: a reading that
#: widened the clause to the other three would redden on a NAME here.
PINNED_VALUE_SITES_IGNORING_ANNOTATIONS = PINNED_VALUE_SITES | {
    "core/creative-localization-readback.json#/properties/variants/items",
    "core/optimization-goal.json#/oneOf/0/properties/target",
    "core/optimization-goal.json#/oneOf/2/properties/target",
}


def _constraining(declaration: dict) -> dict:
    """``declaration`` without the keys that annotate rather than constrain."""
    return {
        k: v
        for k, v in declaration.items()
        if k not in _ANNOTATIONS and not k.startswith("x-")
    }


def _pins_only(branches: list[Any], *, annotations_count: bool) -> list[str] | None:
    """The properties whose PIN is the only thing the branches differ in, or ``None``.

    §5: "A union whose branches declare the same properties with the same ``required``,
    and differ only in the ``const`` or ``enum`` each pins on some of them."  Read as
    written: what the clause tests is DIFFERENCE, so a keyword every branch states
    identically -- the three branches of ``core/canonical-media-buy-action.json`` state
    one and the same ``allOf`` -- is not a difference and does not exclude the site.
    """
    read = (lambda d: d) if annotations_count else _constraining
    views = [read(b) for b in branches]
    if any(set(v) != set(views[0]) for v in views):
        return None
    for key in set(views[0]) - {"properties"}:
        stated = [json.dumps(v.get(key), sort_keys=True) for v in views]
        if any(s != stated[0] for s in stated):
            return None
    maps = [read(v.get("properties") or {}) for v in views]
    if not maps[0] or any(set(m) != set(maps[0]) for m in maps):
        return None
    pinned = []
    for key in sorted(maps[0]):
        declarations = [read(m[key]) for m in maps]
        rest = [{k: v for k, v in d.items() if k not in ("const", "enum")} for d in declarations]
        if any(json.dumps(r, sort_keys=True) != json.dumps(rest[0], sort_keys=True) for r in rest):
            return None
        pins = [{k: v for k, v in d.items() if k in ("const", "enum")} for d in declarations]
        if not all(pins):
            if any(pins):
                return None
            continue
        if any(json.dumps(p, sort_keys=True) != json.dumps(pins[0], sort_keys=True) for p in pins):
            pinned.append(key)
    return pinned or None


def _union_sites(document: str) -> list[tuple[str, str, list[Any]]]:
    """``(pointer, keyword, branches)`` for every combinator in ``document``."""
    sites: list[tuple[str, str, list[Any]]] = []

    def walk(node: Any, pointer: str) -> None:
        if isinstance(node, dict):
            for keyword in ("oneOf", "anyOf"):
                branches = node.get(keyword)
                if (
                    isinstance(branches, list)
                    and len(branches) > 1
                    and all(isinstance(b, dict) for b in branches)
                ):
                    sites.append((f"#{pointer}", keyword, branches))
            for key, value in node.items():
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{pointer}/{i}")

    walk(bundle.read(BUNDLE, document), "")
    return sites


def test_the_pinned_value_clauses_population_is_one_site_and_the_exclusion_is_measured() -> (
    None
):
    """§5's pinned-value clause, measured at ``adcp-client-python-10l.20``'s close-out.

    "A union whose branches declare the same properties with the same ``required``, and
    differ only in the ``const`` or ``enum`` each pins on some of them → one class: each
    such field admits the union of the branches' values, and one rule whose clauses are
    the branches themselves."

    **NOT LANDED, and filed as adcp-client-python-6zg** -- §8 has no pairing rule for a
    class that is the union of its branches, and the companion test below measures what
    collapsing the one site costs.  This one is the population, because the count is what
    the previous instalment got wrong: it read 3 DOCUMENTS off nearby refusals, and the
    clause's own shape holds at one site.

    The exclusion is the interesting half and it is the clause's own word "only": 4 sites
    match when annotations are ignored and 3 of them have branches differing in a
    ``title``, a ``description`` or a ``deprecated``.  Those are facts §6 gives the
    document authority over -- a branch ``title`` is a class NAME under §4 and a branch
    ``description`` is its docstring -- so a branch carrying one does not differ ONLY in
    its pin, and collapsing it would drop the fact.  Both counts are asserted, so a
    reading that widened the clause to the other 3 would redden here rather than
    silently drop two class names and two docstrings.
    """
    both = {}
    for document in sorted(bundle.portable(BUNDLE)):
        for pointer, keyword, branches in _union_sites(document):
            ignoring = _pins_only(branches, annotations_count=False)
            if ignoring is None:
                continue
            both[f"{document}{pointer}"] = (
                keyword,
                ignoring,
                _pins_only(branches, annotations_count=True),
            )
    loose = claimed("pinned-value sites when annotations are ignored", both)
    assert loose == set(PINNED_VALUE_SITES_IGNORING_ANNOTATIONS), sorted(loose)
    strict = {site for site, (_, _, exact) in both.items() if exact is not None}
    excluded = loose - strict
    partitions(loose, differ_only_in_the_pin=strict, differ_in_an_annotation=excluded)
    assert strict == set(PINNED_VALUE_SITES), sorted(strict)
    # Each exclusion, with the annotation that makes it one -- named, so the three are
    # not a residue.
    assert excluded == set(PINNED_VALUE_SITES_IGNORING_ANNOTATIONS) - set(
        PINNED_VALUE_SITES
    ), sorted(excluded)
    for site in sorted(excluded):
        document, _, pointer = site.partition("#")
        branches = next(b for p, _, b in _union_sites(document) if p == f"#{pointer}")
        differing = {
            key
            for key in set().union(*(set(b) for b in branches))
            if len({json.dumps(b.get(key), sort_keys=True) for b in branches}) > 1
        }
        assert differing & (_ANNOTATIONS | {"properties"}) - {"properties"}, (site, differing)


def test_collapsing_the_one_pinned_value_site_reports_three_added_facts() -> None:
    """What landing §5's clause costs TODAY, measured rather than forecast.

    ``core/canonical-media-buy-action.json`` emits as a base and three branches and all
    of its pairs pass all three checks.  Handed the merged class the clause asks for --
    each pinned field admitting the union of the branches' values -- the comparison
    reports ``model_adds_a_fact`` with three ``added`` facts, because the document's ROOT
    states ``oneOf`` and no ``properties`` of its own.

    That is not a defect in the comparison and ``harness._composed`` says why in as many
    words: "``anyOf``/``oneOf`` at a root are left alone, and must be.  A branch's
    properties are satisfied by SOME branch, not by every instance, so folding one in the
    way a conjunct is folded would state a fact the document does not state."  What is
    missing is the THIRD of §8's pairing rules for a class cut out of a combinator -- it
    has the branch-under-the-root's-siblings rule and its type-list dual, and none for a
    class that is the union of its branches.  **adcp-client-python-6zg**, reported rather
    than chosen, which is what this row did for §4's fourth mechanic.

    This test is what reddens when that sentence lands.
    """
    document = "core/canonical-media-buy-action.json"
    doc = bundle.record(BUNDLE, document)
    branches = doc["oneOf"]
    tasks = tuple(b["properties"]["task"]["const"] for b in branches)
    actions = tuple(sorted({a for b in branches for a in b["properties"]["action"]["enum"]}))
    merged = create_model(
        "CanonicalMediaBuyAction",
        __doc__=doc["description"],
        task=(Literal[tasks], ...),
        action=(Literal[actions] | None, None),
    )
    res = harness.compare_schema(
        doc, merged, document=doc, position=keywords.Position.ROOT, at="#"
    )
    assert res.outcome == "model_adds_a_fact", (res.outcome, res.detail)
    assert sorted(f.split(":")[0] for f in res.added) == [
        "/properties/action",
        "/properties/task",
        "/required",
    ], res.added
    assert (res.missing, res.differs) == ([], []), res

    # The control: as a base and three branches, every pair the document emits PASSES.
    for symbol in (
        "CanonicalMediaBuyAction",
        "CanonicalMediaBuyActionControlMediaBuy",
        "CanonicalMediaBuyActionRefineProposals",
        "CanonicalMediaBuyActionSyncCreatives",
    ):
        cls = getattr(
            importlib.import_module("adcp.types._schemas.core.canonical_media_buy_action"),
            symbol,
        )
        ref = cls.__adcp_schema__
        node = schema_at(ref)
        got = harness.compare_schema(
            node, cls, document=schema_at(SchemaRef(ref.document, "#")), at=ref.pointer
        )
        assert got.outcome == "pass", (symbol, got)
