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
from compiled import compiled
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
    """The population, named and partitioned: 46 roots reach the hand-off from §4's first
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
            # **One more at ``adcp-client-python-10l.21``'s third instalment**: §14 step
            # 9's first faithful row -- a ``type`` word beside a NESTED combinator is in
            # every branch already -- freed the chain this root sat behind, so it reaches
            # the derivation now.  It refused one pointer on, at ``/anyOf/0`` on
            # ``title``, and **it EMITS at ``adcp-client-python-10l.41``**: §4's fourth
            # branch rung names its 12 identity-less branches by their index.  Its
            # membership here is unchanged, because this set is about the FIRST dispatch
            # source being empty and not about emitting -- which is the same reason
            # ``core/postal-area.json`` is in the disjoint half and still refuses.
            "core/requirements/asset-requirements.json",
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
            # **5 MORE AT ``adcp-client-python-10l.58``, and they are GROWTH: the set read
            # 41 and reads 46, with nothing removed.**  Each of the five states a branch
            # whose whole declaration is a ``required`` (and, in four of them, a ``not``
            # over ``required`` groups), which ``union._plan`` refused before any branch
            # was planned -- so the root never got as far as §4's question about its
            # branches and this derivation's DENOMINATOR did not count it.  §5's
            # ``oneOf``/``anyOf`` row makes such a branch a branch of SHAPES ("a branch
            # that differs in ... its ``required``") and §5's ``required`` row at BRANCH
            # makes its class the base's requiredness narrowed, so the branches plan and
            # the root reaches the derivation.  All five are in the DISJOINT half: none
            # joins ``OVERLAPPING_ROOTS`` and none declares an UNDERDETERMINED, which is
            # the partition below asserting it rather than this comment.
            "error-details/vast-version-mismatch.json",
            "media-buy/build-creative-response.json",
            "media-buy/buy-products-request.json",
            "media-buy/create-media-buy-request.json",
            "media-buy/create-media-buy-response.json",
            "media-buy/decline-proposals-response.json",
            "media-buy/log-event-response.json",
            "media-buy/provide-performance-feedback-response.json",
            "media-buy/request-proposals-request.json",
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
    # **At a ROOT pointer, for :func:`_reaching`'s reason**: ``lower.union._undetermined``
    # declares §4's row at a NESTED union as well, and this module's sets are roots.
    declaring = {
        d
        for d, declared in out.approximations.items()
        for one in declared
        if one.kind == UNDERDETERMINED and one.pointer in ("#/oneOf", "#/anyOf")
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

    **``emit.emit`` and NOT ``compiled``, which is this function's whole correctness
    argument** (``adcp-client-python-10l.58``).  ``tests/compiled.py`` returns a RESULT and
    not a run -- a hit unpickles one and the walk does not execute -- so the trace below
    recorded nothing whenever some earlier test in the same worker had already compiled
    this population, and the set this function exists to derive came back EMPTY.  The
    assertion then read "the derivation reaches no root at all", which is green against no
    pinned set and red against every one, so the test's outcome was a function of which
    worker compiled first.  ``compiled``'s own docstring names the escape hatch for the
    other caller that cannot take a shared value ("a test that needs to mutate one must
    call ``emit.emit`` directly and say why"); a caller that needs to OBSERVE the walk is
    the same category, and this is the reason.
    """
    seen: set[str | None] = set()
    real = lower_union.overlapping

    def traced(planned: Any, node: Any) -> list[str]:
        # **ROOTS ONLY, and the scoping arrived with a caller rather than with this
        # test** (``adcp-client-python-10l.21``'s third instalment).  §4's derivation is
        # asked at a NESTED union too now -- ``lower.union._undetermined``, which is §4's
        # UNDERDETERMINED row at the other position -- so the raw call set is no longer
        # the roots this module is about, and a nested union inside an untitled node put
        # a ``None`` in a set of titles.  The node knows its own position (§6), so this
        # reads it rather than inferring it from the pointer.
        if node.position is keywords.Position.ROOT:
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
#:
#: **ONE MORE LEFT AT ``adcp-client-python-10l.55``, AND ITS MEMBERSHIP WAS NEVER
#: MEASURED.**  ``creative/sync-creatives-response.json`` REFUSED while it was listed
#: here -- chained behind ``core/assets/asset-union.json``, whose ``$ref`` branch onto a
#: union root the branch row refused -- so the walk returned on branch 0 before
#: :func:`union.overlapping` was ever called, and the two assertions this set feeds both
#: exempt a refusing document (``declaring == overlapping - set(out.refusals)``).  With
#: the branch row fixed the document emits, the derivation runs, and it SEPARATES: each
#: of the three branches carries a ``not``/``anyOf`` forbidding the names the other two
#: require -- ``creatives``, ``errors``, and ``status``/``task_id`` -- which is §4's
#: third source.  ``harness.inseparable_unions`` reads the same document independently
#: and answers ``()``, so §8's third equality holds in both directions; the entry was a
#: claim about a derivation that had not run, and dropping it puts one more root under
#: the ``declaring <= overlapping`` bound rather than outside it.
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
    # **At a ROOT pointer, for :func:`_reaching`'s reason**: ``lower.union._undetermined``
    # declares §4's row at a NESTED union as well, and this module's sets are roots.
    declaring = {
        d
        for d, declared in out.approximations.items()
        for one in declared
        if one.kind == UNDERDETERMINED and one.pointer in ("#/oneOf", "#/anyOf")
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
    # **``creative/sync-creatives-response.json`` left with its entry in
    # :data:`OVERLAPPING_ROOTS``** (``adcp-client-python-10l.55``): this list is that set
    # intersected with what the manifest resolves, so a root the derivation separates is
    # not in it.  The manifest still resolves the document -- what changed is that the
    # document is no longer claimed to overlap.
    assert set(resolved_overlaps) == {
        "content-standards/calibrate-content-response.json",
        "content-standards/create-content-standards-response.json",
        "content-standards/get-content-standards-response.json",
        "content-standards/get-media-buy-artifacts-response.json",
        "content-standards/list-content-standards-response.json",
        "content-standards/validate-content-delivery-response.json",
        "creative/get-creative-features-response.json",
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


# --------------------------------------------------------------------------- #
# WHERE each separator is read, widened 2026-10-28 (``adcp-client-python-10l.30``)
# --------------------------------------------------------------------------- #
#: What the widened arms' answers say, so a test can tell which reading decided a pair
#: without a second copy of the rules.
GROUPED = "requires one of"
ELEMENTS = "are arrays whose elements are"


def _planned(document: str, pointer: str, raw: Any) -> lower_union.Branch:
    """One branch of a REAL document, planned the way :func:`union._plan` plans it.

    The forbidden names come from ``union.forbidden_names``, which is the walk's one
    reading of them, so what these tests ask is what the walk asks.  Nothing here
    resolves a reference: a branch that is or contains a ``$ref`` is read exactly as the
    derivation reads it, which is the whole of why its facts can be out of reach.
    """
    parsed = schema_parse.parse(
        raw,
        pointer=pointer,
        position=keywords.Position.BRANCH,
        source=schema_parse.Source(document=document),
    )
    return lower_union.Branch(
        pointer=pointer,
        node=raw,
        parsed=parsed,
        forbids=lower_union.forbidden_names(parsed, raw),
    )


def _branches(document: str, pointer: str, keyword: str) -> list[lower_union.Branch]:
    """Every branch of one authored union, planned.  ``pointer`` addresses the node."""
    node = bundle.node_at(bundle.read(BUNDLE, document), pointer)
    assert isinstance(node, dict), (document, pointer)
    return [
        _planned(document, f"{pointer}/{keyword}/{i}", raw)
        for i, raw in enumerate(node[keyword])
    ]


def test_a_not_guard_inside_an_allOf_conjunct_forbids_a_name_for_the_branch() -> None:
    """GAP 1: draft-07 conjoins an ``allOf`` conjunct with the node that holds it, so a
    ``not`` a conjunct states forbids a name for the BRANCH.

    ``account/sync-accounts-request.json#/properties/accounts/items/oneOf`` is the
    measured case and it is the bundle's own idiom: ``ProvisioningMode`` requires
    ``[brand, operator, billing]`` and forbids ``account`` in ``allOf[0]``;
    ``SettingsUpdateMode`` requires ``account`` and forbids ``brand`` in its own.  So
    each branch forbids a name the other requires -- which is the sentence §4 writes --
    and read off the branch node alone each forbids NOTHING.

    The PERTURBATION is the conjunct list removed and nothing else, and it has to leave
    the pair inseparable: that is what says the conjuncts are the reason rather than
    something else about these two branches.  Both directions, because
    :func:`union.separates` asks the question each way round.
    """
    one, two = _branches(
        "account/sync-accounts-request.json", "/properties/accounts/items", "oneOf"
    )
    assert lower_union.forbidden_names(one.parsed, one.node) == frozenset(
        {"account", "revision", "operator_identity", "destination_billing_entity"}
    ), lower_union.forbidden_names(one.parsed, one.node)
    assert GROUPED in (lower_union.separates(one, two, "object", "object") or ""), one
    assert GROUPED in (lower_union.separates(two, one, "object", "object") or ""), two

    flat = [
        _planned(
            "probe.json",
            plan.pointer,
            {k: v for k, v in plan.node.items() if k != "allOf"},
        )
        for plan in (one, two)
    ]
    assert lower_union.separates(*flat, "object", "object") is None, flat
    assert lower_union.separates(*flat[::-1], "object", "object") is None, flat


def test_a_presence_group_counts_toward_what_a_branch_requires() -> None:
    """GAP 2: a branch stating ``anyOf: [{"required": [a]}, {"required": [b]}]`` DOES
    require one of them, so a sibling forbidding both is disjoint from it.

    Two measured cases and they take the two halves of §4's second separator:

    * ``formats/canonical/display_tag.json``, ``html5.json`` and ``image.json`` separate
      their "responsive" branch from their "none" branch, the first requiring one of four
      bound names through an ``anyOf`` and the second forbidding all seven by name;
    * ``brand.json``'s branch 3 requires one of ``brands`` / ``brand_refs`` and its
      branch 1 is CLOSED over a map declaring neither.

    The quantity is a set of SETS and that is the point: no single name is required by the
    "responsive" branch, so a reading over names alone requires nothing of it and the pair
    is inseparable -- which is what the document does not say.  The perturbation is the
    presence combinator removed, and each pair has to go back to inseparable.
    """
    for document in (
        "formats/canonical/display_tag.json",
        "formats/canonical/html5.json",
        "formats/canonical/image.json",
    ):
        planned = _branches(document, "/allOf/1", "oneOf")
        titles = [plan.node.get("title") for plan in planned]
        responsive, none = (planned[titles.index(t)] for t in ("responsive", "none"))
        assert GROUPED in (lower_union.separates(responsive, none, None, None) or ""), (
            document
        )
        bare = _planned(
            document,
            responsive.pointer,
            {k: v for k, v in responsive.node.items() if k != "anyOf"},
        )
        assert lower_union.separates(bare, none, None, None) is None, document

    house, portfolio = (_branches("brand.json", "", "oneOf")[i] for i in (1, 3))
    assert FORBIDDEN in (lower_union.separates(portfolio, house, "object", "object") or ""), (
        portfolio
    )
    bare = _planned(
        "brand.json",
        portfolio.pointer,
        {k: v for k, v in portfolio.node.items() if k != "anyOf"},
    )
    assert lower_union.separates(bare, house, "object", "object") is None, bare


def test_a_closed_conjunct_separates_by_what_it_does_not_declare() -> None:
    """GAP 3: ``additionalProperties: false`` puts an instance's members inside THAT
    view's own ``properties``, and a conjunct is a view of the branch.

    The arm at the branch NODE is not new and decides the ``brand.json`` pair the test
    above names.  What is new is that it is asked of each closed VIEW, so a branch whose
    closure and whose property map sit in an ``allOf`` conjunct is read -- and the
    bundle's own count of pairs decided by THAT is derived here rather than claimed:
    ``0`` branches of 3.2 close the instance in a conjunct and nowhere else, so the
    widening is written for the first document that does and graded on a constructed pair.
    """
    closed = _planned(
        "probe.json",
        "/oneOf/0",
        {"type": "object", "allOf": [{"additionalProperties": False, "properties": {"a": {}}}]},
    )
    demanding = _planned(
        "probe.json", "/oneOf/1", {"type": "object", "required": ["b"], "properties": {"b": {}}}
    )
    assert lower_union.closures_of(closed) == (frozenset({"a"}),), closed
    assert FORBIDDEN in (lower_union.separates(demanding, closed, "object", "object") or "")
    assert FORBIDDEN in (lower_union.separates(closed, demanding, "object", "object") or "")
    # And the same two branches with the conjunct's closure taken back by a pattern: the
    # view admits names this cannot enumerate, so it is not a closed view at all.
    patterned = _planned(
        "probe.json",
        "/oneOf/0",
        {
            "type": "object",
            "allOf": [
                {
                    "additionalProperties": False,
                    "patternProperties": {"^x_": {}},
                    "properties": {"a": {}},
                }
            ],
        },
    )
    assert lower_union.closures_of(patterned) == (), patterned
    assert lower_union.separates(demanding, patterned, "object", "object") is None

    # The bundle's own count, DERIVED over the set it ranges over and named: every
    # branch of every authored union of 3.2 that does NOT close at its own node, paired
    # with whether a CONJUNCT of it closes.  None of them does, which is why the
    # per-view descent decides no pair of this bundle and is graded on the constructed
    # pair above -- and the first document to state one reddens the assertion by name.
    conjunct_closures = claimed(
        "branches of an authored union that do not close at their own node",
        [
            (
                f"{document}#{pointer}/{keyword}/{i}",
                bool(schema_parse.closed_maps(raw, keywords.Position.BRANCH)),
            )
            for document in sorted(bundle.portable(BUNDLE))
            for doc in [bundle.read(BUNDLE, document)]
            for pointer, node in harness._rule_free_nodes(doc)
            for keyword in ("oneOf", "anyOf")
            if isinstance(node.get(keyword), list)
            for i, raw in enumerate(node[keyword])
            if isinstance(raw, dict) and raw.get("additionalProperties") is not False
        ],
    )
    assert [at for at, closes in sorted(conjunct_closures) if closes] == []


def test_two_array_branches_separate_on_their_element_type() -> None:
    """GAP 4: §4's type separator at the position an ARRAY branch states what its
    instance is -- ``items``, which describes every member.

    Two halves and the second is what makes it sound.  ``[]`` satisfies ``items``
    vacuously, so two arrays of disjoint element types both admit it and the pair is NOT
    disjoint on the element word alone; ``minItems`` of at least 1 on either branch is
    what refuses it.  A pair where neither refuses it overlaps at exactly that one value,
    and §4's "a pair the derivation cannot separate is treated as overlapping" is what
    the arm then does.

    **The bundle's own case does NOT fire, and the reason is derived here rather than
    left to be discovered.**  ``brand.json#/definitions/localized_string_list`` is two
    ``type: array`` branches, one of strings and one of entries -- and the second states
    its element type as ``items: {"$ref": "#/definitions/localized_string_list_entry"}``,
    so the fact is in the TARGET.  ``schema.element_word`` reads the word off the node and
    answers ``None``.  Resolving a local reference is what ``compiler.local_reference``
    DECLARES, which a derivation may not do, so the pair stays unseparated and the
    document says the word one hop away from where the arm can read it.
    """
    strings = _planned("probe.json", "/oneOf/0", {"type": "array", "items": {"type": "string"}})
    objects = _planned(
        "probe.json", "/oneOf/1", {"type": "array", "items": {"type": "object"}, "minItems": 1}
    )
    assert ELEMENTS in (lower_union.separates(strings, objects, "array", "array") or "")
    assert ELEMENTS in (lower_union.separates(objects, strings, "array", "array") or "")
    empty_too = _planned("probe.json", "/oneOf/1", {"type": "array", "items": {"type": "object"}})
    assert lower_union.separates(strings, empty_too, "array", "array") is None
    assert lower_union.separates(strings, objects, "array", "object") is None

    reference, = [
        raw
        for raw in bundle.node_at(
            bundle.read(BUNDLE, "brand.json"), "/definitions/localized_string_list"
        )["oneOf"]
        if isinstance(raw.get("items"), dict) and "$ref" in raw["items"]
    ]
    assert schema_parse.element_word(reference, keywords.Position.BRANCH) == (None, True)
    held = _planned("brand.json", "/definitions/localized_string_list/oneOf/1", reference)
    assert lower_union.separates(strings, held, "array", "array") is None


def test_eight_open_branches_requiring_one_name_separate_on_their_nested_nots() -> None:
    """``compliance/comply-test-controller-response.json``, the reference case: eight
    branches all ``additionalProperties: true`` and all requiring ``success``.

    Nothing closes and no two pin a value, so the whole of the separation is the second
    separator read through ``not: {"anyOf": [...]}`` -- ``SeedSuccess`` forbids all seven
    siblings' discriminants that way, and each of the other seven forbids the names its
    siblings require.  Every pair of the 28 separates, which is asserted over the pairs
    rather than on a sample.
    """
    planned = _branches("compliance/comply-test-controller-response.json", "", "oneOf")
    pairs = claimed(
        "the pairs of the eight-branch controller response",
        [(i, j) for i in range(len(planned)) for j in range(i + 1, len(planned))],
    )
    # Every branch is OPEN and requires ``success``, and the one property every branch
    # PINS is pinned to two values over eight branches -- so there is no dispatch key and
    # closure separates nothing.  All derived, so the claim about what does separate them
    # is about these branches and not about a reading of their titles.
    for plan in planned:
        assert plan.node["additionalProperties"] is True, plan
        assert frozenset({"success"}) in lower_union.demands(plan), plan
        assert lower_union.closures_of(plan) == (), plan
    shared = set.intersection(*(set(lower_union.pins(p.properties)) for p in planned))
    assert shared == {"success"}, shared
    assert {lower_union.pins(p.properties)["success"] for p in planned} == {True, False}
    assert lower_union.discriminator(planned, None) == "", planned
    # The pin separates the error branch from the seven successes and nothing else, so
    # the pairs AMONG the successes are the ``not: {"anyOf": [...]}`` reading's alone.
    successes = [i for i, p in enumerate(planned) if lower_union.pins(p.properties)["success"]]
    among = claimed(
        "pairs among the seven branches pinning success to one value",
        [(i, j) for i in successes for j in successes if i < j],
    )
    assert among < pairs, sorted(among - pairs)
    for i, j in sorted(among):
        assert GROUPED in (
            lower_union.separates(planned[i], planned[j], "object", "object") or ""
        ), (i, j)
    unseparated = [
        (i, j)
        for i, j in sorted(pairs)
        if lower_union.separates(planned[i], planned[j], "object", "object") is None
    ]
    assert unseparated == [], unseparated


#: Every authored union of 3.2 whose branches are all shapes and that states no ``$ref``
#: anywhere inside a branch, and that the two readings of §4's third source still cannot
#: separate.  **Named and not counted**, because what each one is matters: a union a
#: separator could reach would leave this set, and a new one joining it is a document the
#: derivation has stopped reading.
#:
#: Every member but one is an ``anyOf`` the document states as a CONSTRAINT -- branches
#: that narrow one shape rather than alternating between shapes, which §4 compiles to a
#: rule (``AtLeastOne`` / ``PresenceGroups``) and not to a discriminated union, so no
#: separator is owed one.  ``adagents.json#/oneOf/1/allOf/0/anyOf`` says so in its own
#: ``$comment``: "Each arm asserts non-emptiness directly."  The two ``viewability``
#: nodes state one branch that forbids four metrics and one that requires ``standard``;
#: ``core/postal-country-system.json`` narrows ``country`` and ``system`` ten ways; and
#: the last three are "at least one of these two keys".
_INSEPARABLE_CONSTRAINTS = frozenset(
    {
        "adagents.json#/oneOf/1/allOf/0/anyOf",
        "core/canonical-forecast-point.json#/properties/viewability/anyOf",
        "core/forecast-point.json#/properties/viewability/anyOf",
        "core/postal-country-system.json#/anyOf",
        "media-buy/buy-products-request.json#/anyOf",
        "media-buy/request-proposals-request.json#/anyOf",
        "trusted-match/provider-registration.json#/anyOf",
    }
)
#: The union whose branches GENUINELY overlap: both open, each requiring a name the other
#: neither forbids nor fails to declare, so ``{"format_id_glob": …, "structural": …}``
#: satisfies both.  §4's UNDERDETERMINED row and no separator reaches it -- the fact
#: dropped is which branch an overlapping payload becomes, and the declaration says so.
_GENUINELY_OVERLAPPING = frozenset(
    {
        "registries/v1-canonical-mapping.json"
        "#/properties/mappings/items/properties/v1_pattern/oneOf",
    }
)


def test_a_fact_a_ref_conjunct_holds_is_out_of_the_derivations_reach() -> None:
    """``brand.json``'s pair 2/4, named here because the document DOES separate it and
    neither reading can say so.

    Branch 2 is closed over a map declaring neither ``id`` nor ``names``; branch 4
    requires both, through ``allOf[1]``, which is ``$ref: "#/definitions/brand"``.  So
    the separating fact is in the target and :func:`schema_parse.applies_to_one_instance`
    contributes nothing for a ``$ref`` conjunct -- the conservative direction §4 names,
    because resolving a local reference is what ``compiler.local_reference`` DECLARES and
    a derivation may not declare anything.

    Both halves are derived: that the conjunct is a reference, and that the target states
    the two names.  Written so that a row which teaches the derivation to read a
    conjunct's target reddens here and takes the pair with it.
    """
    document = bundle.read(BUNDLE, "brand.json")
    closed, catchall = (_branches("brand.json", "", "oneOf")[i] for i in (2, 4))
    (reference,) = [c for c in catchall.node["allOf"] if "$ref" in c]
    assert reference["$ref"] == "#/definitions/brand", reference
    target = bundle.node_at(document, "/definitions/brand")
    assert set(target["required"]) == {"id", "names"}, target["required"]
    assert not set(target["required"]) & set(closed.node["properties"]), closed.node
    assert lower_union.closures_of(closed), closed
    assert lower_union.demands(catchall) == frozenset(), catchall
    assert lower_union.separates(closed, catchall, "object", "object") is None


def _authored_unions() -> list[tuple[str, str, list[dict], list[Any]]]:
    """Every authored union of 3.2 whose branches are all SHAPES, with the applied type.

    The GATE is the one both halves of §8's third equality already apply -- a branch is a
    shape where its node under the enclosing ``type`` is an object -- because that is the
    set where branch CLASSES exist and a declaration order has something to choose
    between.  A presence-only combinator is excluded for the same reason: it lowers to a
    rule on the enclosing class (``schema.presence_only``, the parser's own reading).
    """
    out = []
    for document in sorted(bundle.portable(BUNDLE)):
        doc = bundle.read(BUNDLE, document)
        for pointer, node in harness._rule_free_nodes(doc):
            for keyword in ("oneOf", "anyOf"):
                branches = node.get(keyword)
                if not isinstance(branches, list) or len(branches) < 2:
                    continue
                if not all(isinstance(b, dict) for b in branches):
                    continue
                if schema_parse.presence_only({keyword: branches}, keywords.Position.ROOT):
                    continue
                applied = [b.get("type") or node.get("type") for b in branches]
                if not all(
                    t == "object" or (t is None and b.get("properties"))
                    for t, b in zip(applied, branches, strict=True)
                ):
                    continue
                base = "" if pointer == "/" else pointer
                out.append((f"{document}#{base}/{keyword}", keyword, branches, applied))
    return out


def _states_a_reference(node: Any) -> bool:
    """Does this branch state a ``$ref`` anywhere inside it?

    The population §4's derivation is measured over EXCLUDES these, and the exclusion is
    a statement about where the facts are: a separator of such a branch may live in the
    target, which neither reading resolves.  Asked of the whole subtree and not of the
    branch's top level, because a conjunct, a property or an element carries one too.
    """
    if isinstance(node, dict):
        return "$ref" in node or any(_states_a_reference(v) for v in node.values())
    if isinstance(node, list):
        return any(_states_a_reference(v) for v in node)
    return False


def test_the_two_readings_of_separability_agree_over_every_authored_union() -> None:
    """§8's third equality asked of the DERIVATION itself rather than of its declarations.

    The walk reads a branch through ``compiler.rules_at`` and ``codegen.schema.parse``;
    the verifier reads the document node.  Section 9 keeps them separate spellings on
    purpose -- "one body of code deciding what the model states and what the document
    states agrees with itself by construction, so a defect in it is green on both sides"
    -- and this is what says the two spellings answer the same question: over every
    authored union of shapes, pair by pair, the two agree on every pair.

    Asserted on the PAIRS and not on a count, so a reading that separated a different
    pair of the same union reddens.
    """
    unions = claimed("authored unions of 3.2 whose branches are all shapes", {
        at for at, _, _, _ in _authored_unions()
    })
    assert len(unions) == len(_authored_unions()), "two unions at one pointer"
    disagreed = []
    for at, _, branches, applied in _authored_unions():
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                walk = lower_union.separates(
                    _planned(at, f"{at}/{i}", branches[i]),
                    _planned(at, f"{at}/{j}", branches[j]),
                    applied[i],
                    applied[j],
                )
                record = harness.separates(branches[i], branches[j], applied[i], applied[j])
                if (walk is None) != (record is None):
                    disagreed.append((at, i, j, walk, record))
    assert disagreed == [], disagreed


def test_every_union_the_derivation_cannot_separate_is_named_and_partitioned() -> None:
    """The census the row is graded on, DERIVED on both sides and partitioned by name.

    The population is the authored unions of shapes that state no ``$ref`` inside a
    branch -- 112 of the 169 do, and §4's reading of one of those may live in the target,
    which is a separate measurement and not this one's.  What is asserted is that every
    union of the remainder the derivation cannot separate is one of three named things,
    and that both readings produce the same remainder:

    * an ``anyOf`` the document states as a CONSTRAINT, which §4 compiles to a rule and
      not to a discriminated union, so it needs no separator at all;
    * a union whose branches GENUINELY overlap -- open, each requiring a name the others
      neither forbid nor fail to declare -- which is §4's UNDERDETERMINED row.

    A union LEAVING the remainder is the row working and reddens here by name, which is
    what the row's own four readings did to ``account/sync-accounts-request.json``.
    """
    population = claimed(
        "authored unions of shapes stating no $ref inside a branch",
        [
            (at, keyword, tuple(range(len(branches))))
            for at, keyword, branches, _ in _authored_unions()
            if not any(_states_a_reference(b) for b in branches)
        ],
    )
    inseparable = {
        at: [
            (i, j)
            for i in range(len(branches))
            for j in range(i + 1, len(branches))
            if harness.separates(branches[i], branches[j], applied[i], applied[j]) is None
        ]
        for at, keyword, branches, applied in _authored_unions()
        if not any(_states_a_reference(b) for b in branches)
    }
    remainder = claimed(
        "unions of the non-$ref population the derivation cannot separate",
        {at for at, pairs in inseparable.items() if pairs},
        inside={at for at, _, _ in population},
    )
    partitions(
        remainder,
        a_constraint=_INSEPARABLE_CONSTRAINTS,
        genuinely_overlapping=_GENUINELY_OVERLAPPING,
    )
