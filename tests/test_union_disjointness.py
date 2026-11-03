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
from typing import Any, NamedTuple

from jsonschema import Draft7Validator

from adcp.types._base import UNDERDETERMINED
from compiled import compiled
from codegen import bundle, compiler, emit, harness, keywords, store
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
PINNED = "is constrained to disjoint value sets"
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
def _pinned(value: Any, **extra: Any) -> lower_union.Branch:
    """A branch constraining ``kind`` to ``value``, and REQUIRING it.

    ``required`` is part of the fixture rather than of one case because the separator is
    gated on presence: a ``properties`` entry is satisfied by the key being absent, so a
    branch that does not require ``kind`` says nothing that separates it from any other.
    :func:`test_disjoint_value_sets_do_not_separate_a_pair_that_need_not_carry_the_key`
    is the half that holds the gate.
    """
    return _branch(
        type="object", properties={"kind": value}, required=["kind"], **extra
    )


def test_a_property_constrained_to_disjoint_value_sets_separates_a_pair() -> None:
    """§4's first separator, and the half that makes it a separator: an instance whose
    ``kind`` is in one set is not in the other, so no instance satisfies both.

    **It reads SETS and not single values (decided 2026-10-29).** §4: "An ``enum`` is a
    set of pinned values and a ``not: {"enum": [...]}`` is its complement, so two
    branches whose sets do not intersect are disjoint for the same reason two different
    ``const``\\ s are -- the single-value case is the one-member set."  All four pairings
    are graded here, because each is a different comparison and only the first was ever
    written: set against set, set against a one-member set, and a set against the
    COMPLEMENT of a set that contains it.

    The perturbations are the same four with the sets INTERSECTING, which is where §4's
    "a pair the derivation cannot separate is treated as overlapping" applies -- and they
    include the pairing that can never separate, two complements, because whether two
    finite excluded sets cover the value space is not something the branches state.

    This is not :func:`union.discriminator`: that one needs the property SHARED by every
    branch, and this one needs only the pair.
    """
    separated = (
        (_pinned({"const": "a"}), _pinned({"const": "b"})),
        (_pinned({"enum": ["a", "b"]}), _pinned({"const": "c"})),
        (_pinned({"enum": ["a", "b"]}), _pinned({"enum": ["c", "d"]})),
        (_pinned({"const": "a"}), _pinned({"not": {"enum": ["a", "b"]}})),
        (_pinned({"enum": ["a", "b"]}), _pinned({"not": {"enum": ["a", "b", "c"]}})),
    )
    for one, two in separated:
        assert PINNED in (lower_union.separates(one, two, None, None) or ""), (one, two)
        assert PINNED in (lower_union.separates(two, one, None, None) or ""), (one, two)

    overlapping = (
        # the same value on both sides -- the pair the single-value reading already knew
        (_pinned({"const": "a"}), _pinned({"const": "a"})),
        # sets that share a member
        (_pinned({"enum": ["a", "b"]}), _pinned({"enum": ["b", "c"]})),
        # a set NOT contained in the complemented one: "a" is admitted by both
        (_pinned({"enum": ["a", "b"]}), _pinned({"not": {"enum": ["b"]}})),
        # two complements, which never separate
        (_pinned({"not": {"enum": ["a"]}}), _pinned({"not": {"enum": ["b"]}})),
        # a constraint that names no values at all has no set to intersect
        (_pinned({"type": "string"}), _pinned({"const": "a"})),
    )
    for one, two in overlapping:
        assert lower_union.separates(one, two, None, None) is None, (one, two)
        assert lower_union.separates(two, one, None, None) is None, (one, two)


def test_disjoint_value_sets_do_not_separate_a_pair_that_need_not_carry_the_key() -> (
    None
):
    """The PRESENCE gate, which the single-value reading never had and needed.

    A ``properties`` entry constrains the value a key carries and says nothing about an
    instance that omits the key, so two branches naming disjoint sets for a key neither
    requires are both satisfied by ``{}``.  Measured under ``Draft7Validator``: ``{}`` is
    valid against ``{"type": "object", "properties": {"kind": {"const": "a"}}}`` and
    against its ``"b"`` sibling, so the pair genuinely overlaps and reporting it disjoint
    would be exactly the unproven disjointness §4's third source exists to refuse.

    Three ways to satisfy the gate and each is asserted, because §4 applies a root
    keyword to every branch: EITHER branch requiring the key is enough -- an instance of
    that one always carries a value the other refuses -- and so is the ROOT requiring it
    of every branch, which is the form the bundle actually uses.
    """
    bare = (
        _branch(type="object", properties={"kind": {"const": "a"}}),
        _branch(type="object", properties={"kind": {"const": "b"}}),
    )
    schema = {"type": "object", "properties": {"kind": {"const": "a"}}}
    assert Draft7Validator(schema).is_valid({}), "draft-07 admits the absent key"
    assert lower_union.separates(*bare, None, None) is None, bare
    assert lower_union.separates(*bare[::-1], None, None) is None, bare

    for one, two in (
        (_pinned({"const": "a"}), bare[1]),
        (bare[0], _pinned({"const": "b"})),
    ):
        assert PINNED in (lower_union.separates(one, two, None, None) or ""), (one, two)

    assert PINNED in (
        lower_union.separates(*bare, None, None, root_required=frozenset({"kind"})) or ""
    ), bare


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
    """§4's hand-off, DERIVED on both sides: every root reaching the derivation is either
    separated by it or declared UNDERDETERMINED, and an independent reading of the same
    document agrees about which.

    **THIS CHECK WAS TWO PINNED CENSUSES UNTIL 2026-11-03.**  It named 48 document paths
    by hand as "the roots whose first-source dispatch is expected to be empty" and
    asserted that set EQUAL to what the walk handed the derivation, and it took the
    overlapping half from a second hand-written set, ``OVERLAPPING_ROOTS``.  Both
    had drifted, and the drift is what a census does -- it is one tree's reading of a
    quantity every emitting row moves:

        reaching the derivation, derived          49
          not in the hand-written list             2  core/async-response-data.json
                                                      compliance/task-completion-data.json
          in the list and no longer reaching       1  governance/check-governance-request.json
        declaring UNDERDETERMINED at a root      17
          not in OVERLAPPING_ROOTS                 5
          in OVERLAPPING_ROOTS and not declaring   4

    The INVARIANT the first equality stood in for is written in its own comment:
    "a hand-written list alone would still be partitioned cleanly by a derivation that
    had stopped running".  That is a claim about the DERIVATION RUNNING, not about which
    48 documents reach it, and it is held by deriving the population instead of pinning
    it -- ``_reaching`` records the document now, so there is no titles-to-paths bridge
    for a list to be.

    The INVARIANT the second stood in for is §8's third equality, and it is an agreement
    between two independent readings rather than a census: the walk decides separability
    off the branch NODES (``lower.union.separates``) and ``harness.separates`` decides it
    again off the DOCUMENT OF RECORD, which §9 keeps as a second spelling on purpose --
    "if the verifier asked the walk which unions it could not separate, the equality
    below would compare the walk's answer with itself."  Measured over the 49: 17 either
    side, and both directions empty.

    ``core/postal-area.json`` used to be the named case of "disjoint and still refuses,
    on a ``$ref`` of its own", which is why the disjoint half is not "the emitted half".
    At ``refused 0`` no reached root refuses at all, so that is asserted as the figure it
    now is rather than carried as a claim about one document.
    """
    out, reaching = _reaching(sorted(bundle.portable(BUNDLE)))
    # DERIVED and not named: the roots that actually reach the derivation in the walk,
    # recorded at the call by the document being lowered.
    reached = claimed(
        "union roots the walk hands §4's third source",
        reaching,
        inside=bundle.portable(BUNDLE),
    )

    # **READ OFF THE DECLARATION, because an overlapping root no longer REFUSES.**  §4's
    # own answer is written (``adcp-client-python-10l.21``): "a union matching none of the
    # three emits a plain ``A | B`` over its branches and declares an UNDERDETERMINED
    # approximation at the union's pointer".
    # **At a ROOT pointer, for :func:`_reaching`'s reason**: ``lower.union._undetermined``
    # declares §4's row at a NESTED union as well, and this module's sets are roots.
    overlapping = claimed(
        "roots the derivation cannot separate, read off the run's declarations",
        {
            d
            for d, declared in out.approximations.items()
            for one in declared
            if one.kind == UNDERDETERMINED and one.pointer in ("#/oneOf", "#/anyOf")
        },
        inside=reached,
    )
    disjoint = claimed(
        "roots the third source dispatches", reached - overlapping, inside=reached
    )
    partitions(reached, overlapping=overlapping, disjoint=disjoint)

    # **THE SECOND READING, and this is the assertion the hand-written set was standing
    # in front of.**  ``harness.separates`` decides §4's four separators again off the
    # DOCUMENT OF RECORD, which §9 keeps a second spelling of ``lower.union.separates``
    # on purpose; so this compares the walk's answer with a reading that does not come
    # from the walk, in BOTH directions and with the disagreeing documents NAMED.
    known = set(bundle.portable(BUNDLE))
    unrecorded = sorted(
        d for d in reached if not isinstance(bundle.recorded(BUNDLE, d, known), tuple)
    )
    assert unrecorded == [], unrecorded
    independently = {
        d
        for d in reached
        if any(
            at in ("#/oneOf", "#/anyOf")
            for at in harness.inseparable_unions(bundle.recorded(BUNDLE, d, known)[0])
        )
    }
    assert independently == overlapping, {
        "the record says inseparable and the walk declared nothing": sorted(
            independently - overlapping
        ),
        "the walk declared UNDERDETERMINED and the record separates": sorted(
            overlapping - independently
        ),
    }

    # And never on the overlap: §4's answer REPLACED that refusal, so a reached root
    # refusing with that sentence is the old behaviour coming back.
    overlap_refusals = sorted(
        d
        for d in reached
        if "branches OVERLAP" in out.refusals.get(d, {}).get("detail", "")
    )
    assert overlap_refusals == [], overlap_refusals
    # The disjoint half is not "the emitted half" -- a root can separate and still refuse
    # on a keyword of its own, which ``core/postal-area.json`` did.  Asserted as the
    # figure it now is: at ``refused 0`` no reached root refuses, and the two halves are
    # told apart by the declaration and never by the emission.
    assert disjoint <= set(out.emitted), sorted(disjoint - set(out.emitted))
    assert overlapping <= set(out.emitted), sorted(overlapping - set(out.emitted))


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


def _reaching(population: list[str]) -> tuple[Any, set[str]]:
    """Emit, and record which roots reached :func:`union.overlapping`, BY DOCUMENT.

    Recorded AT THE CALL, so the set is what the walk produced rather than what a reader
    believes it produces.

    **BY DOCUMENT AND NOT BY ``title``, and that change is what retired a pinned census**
    (2026-11-03).  The derivation is handed the union NODE, whose only name of its own is
    its ``title`` annotation (:attr:`codegen.schema.nodes.Base.title`), so this used to
    return titles -- and a caller that needs a document path then had to supply the
    bridge, which it did as a hand-written list of 48 document names asserted EQUAL to
    the titles the walk produced.  That equality is a census: a document joining or
    leaving §4's hand-off moves it, and three had (``core/async-response-data.json`` and
    ``compliance/task-completion-data.json`` reach the derivation now,
    ``governance/check-governance-request.json`` no longer does).  The walk already
    knows which document it is lowering, so the bridge is read off the walk instead and
    the list is gone.

    ``emit.lower_document`` is the seam: it is the per-document entry point and it has
    exactly one caller inside ``emit.emit``, so the document in scope at a ``ROOT``
    position is the one that function was most recently handed.  A nested union of an
    imported target is attributed to the document being LOWERED and not to the target,
    which is the attribution §8 sentence 2 wants anyway -- but the ``ROOT`` screen below
    makes that moot, since a root position belongs to the document being lowered.

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
    seen: set[str] = set()
    real = lower_union.overlapping
    real_document = emit.lower_document
    lowering: list[str] = []

    def one_document(document: str, *a: Any, **k: Any) -> Any:
        lowering.append(document)
        try:
            return real_document(document, *a, **k)
        finally:
            lowering.pop()

    def traced(planned: Any, node: Any) -> list[str]:
        # **ROOTS ONLY, and the scoping arrived with a caller rather than with this
        # test** (``adcp-client-python-10l.21``'s third instalment).  §4's derivation is
        # asked at a NESTED union too now -- ``lower.union._undetermined``, which is §4's
        # UNDERDETERMINED row at the other position -- so the raw call set is no longer
        # the roots this module is about.  The node knows its own position (§6), so this
        # reads it rather than inferring it from the pointer.
        if node.position is keywords.Position.ROOT and lowering:
            seen.add(lowering[-1])
        return real(planned, node)

    lower_union.overlapping = traced  # type: ignore[assignment]
    emit.lower_document = one_document  # type: ignore[assignment]
    try:
        # ``store.perturbed()``: both patches above are run-time changes to a walk module,
        # and ``codegen/store.py`` holds §1's export census on disk under a digest of
        # ``codegen/``'s SOURCE, which a patch does not move.  So without this the walk
        # takes the census off disk and pass one never runs -- which is the whole thing
        # this function exists to make happen -- and ``tests/test_no_cached_compile_under_
        # a_perturbation.py`` is the guard that says so.  It has always been true of the
        # ``lower_union.overlapping`` patch and the guard could not SEE it: its ``WALK``
        # tuple is matched against the local name, and ``lower_union`` is this module's
        # alias for ``codegen.lower.union``.  The ``emit.`` patch is spelled with a name
        # the guard knows, so adding it is what made the omission visible.
        with store.perturbed():
            return emit.emit(BUNDLE, population), seen
    finally:
        lower_union.overlapping = real  # type: ignore[assignment]
        emit.lower_document = real_document  # type: ignore[assignment]


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
#: **``OVERLAPPING_ROOTS`` STOOD HERE AND IS GONE** (2026-11-04,
#: ``adcp-client-python-99m``).  It was a hand-written frozenset of the union roots the
#: walk cannot separate, and it was a CENSUS: the two checks reading it asserted it
#: EQUAL to what the run declares, and that equality moves whenever the derivation
#: learns to separate one more root or an upstream release adds one.  Its own docstring
#: recorded three documents leaving it one row at a time, each with a paragraph; by
#: 2026-11-04 it named 16 while the run declared 17, five of those not in it and four of
#: it not declaring, and the red was hiding ``adcp-client-python-82m.44``.
#:
#: Both readers derive the set from ``Emitted.approximations`` now -- an UNDERDETERMINED
#: declaration at ``#/oneOf`` or ``#/anyOf`` is the run saying "I could not separate
#: this", which is the fact the list was a copy of.  The claim that the derivation is
#: RIGHT about it is §8's third equality, asserted against ``harness.separates``'s
#: independent reading of the document of record in
#: ``test_the_derivation_decides_the_roots_that_reach_it_and_the_refusal_takes_the_rest``.


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

    The thesis was that its population over bundle 3.2 is 0, and that the reason is the
    SHAPE of the resolution rather than the count: the template is
    ``/tools/{task_type}/response_schema``, so it resolves a DOCUMENT from a task field,
    the manifest's key is spent selecting the document, and a union INSIDE the document
    it selects has no discriminant left in the envelope to be told apart by.  Measured
    three ways here, each of which fails on its own:

    * every document declaring the manifest's discriminator field states NO union at
      all, at any pointer -- so there is nothing for the second source to dispatch;
    * no branch of an inseparable root declares that field, and no branch of one is a
      reference to a schema the manifest resolves;
    * most of the inseparable roots ARE a schema the manifest's own template resolves,
      which is the measurement that was meant to settle it: the manifest names the
      document and the overlap is a union inside it.

    **THE SECOND MEASUREMENT IS FALSE, AND THE POPULATION THIS CHECK'S THESIS NEEDS TO
    BE 0 IS 2** (``adcp-client-python-82m.44``, filed 2026-11-04).  Two roots have
    branches that ARE references to documents the manifest resolves, neither root is
    itself a resolved schema, and neither declares the field at any pointer -- so the
    key is not spent on the document, it selects the BRANCH, which is §4's second-source
    sentence verbatim:

        compliance/task-completion-data.json      4 branches,  3 resolved
        core/async-response-data.json            42 branches, 14 resolved

    **WHAT HID IT WAS THIS CHECK'S OWN CENSUS.**  The population was the hand-written
    frozenset ``OVERLAPPING_ROOTS``, which named 16 documents while the run declares
    UNDERDETERMINED at a root for 17; the equality on it was RED
    (``adcp-client-python-99m``) and it failed BEFORE the three measurements ran, so the
    second measurement was being asked of the stale 16 and never saw the two roots that
    refute it.  Deriving the population is what made the real finding visible, and it is
    the reason that red mattered.

    So the population is derived now, the stale equality is gone, and the second
    measurement is asserted UNNARROWED and NAMES its offenders.  It is red, and that red
    is ``adcp-client-python-82m.44``: §4's second source has code nowhere, both roots
    fall through to the third source, and both carry an UNDERDETERMINED declaration the
    document does not owe them.  Fixing it moves what the walk emits and ``./check``'s
    third figure, so it is that row's and not this check's -- and no scope here is
    narrowed to go green, which is what would put it back out of sight.

    The REST of the inseparable set is **§4's UNDERDETERMINED row** and not this one's.
    §4 decides what becomes of it -- "a union matching none of the three emits a plain
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
    # DERIVED, and the hand-written ``OVERLAPPING_ROOTS`` is gone with the equality on
    # it: that set named 16 documents while the run declares 17, and the census failing
    # here was what kept the three measurements below from ever running on the current
    # population (``adcp-client-python-82m.44``).
    overlapping = sorted(
        claimed(
            "roots the derivation cannot separate, read off the run's declarations",
            declaring,
            inside=bundle.portable(BUNDLE),
        )
    )
    # Every one that refuses reports its OWN next obstruction, which is neither the
    # overlap nor nothing.  At ``refused 0`` the set is empty and the loop is a floor
    # rather than a check -- which is why the overlap sentence is asserted over ALL
    # refusals one line above, where it is not conditional on this set.
    for document in sorted(d for d in overlapping if d in out.refusals):
        row = out.refusals[document]
        assert row["keyword"] != document, row
        assert "branches OVERLAP" not in row["detail"], (document, row)
    resolved_overlaps = [d for d in overlapping if d in resolves]
    # **MEASUREMENT 2, UNNARROWED, WITH ITS OFFENDERS NAMED.**  Collected over the whole
    # set and asserted once, so the message is the POPULATION of §4's second source and
    # not the first document that happens to be visited.  Red as of 2026-11-04, and the
    # red is ``adcp-client-python-82m.44``: the key selects the BRANCH at these two
    # roots, which is the second source's own sentence, and no code implements it.
    carries_the_key: list[str] = []
    branches_the_manifest_resolves: list[tuple[str, int, str]] = []
    known = set(bundle.portable(BUNDLE))
    for document in overlapping:
        # The union is the one the PARSER classified at the root, and the branches are
        # the field it set: an overlapping root no longer refuses ON the overlap, so the
        # refusal's pointer is its own next obstruction and says nothing about where the
        # union is.  **Read off the classification and not off the root's own keys**
        # (``adcp-client-python-10l.37``): ``governance/check-governance-request.json``
        # writes its combinator in an ``allOf`` conjunct, which draft-07 applies to the
        # same instance, so the root states no combinator key at all and a reading of
        # those keys would miss the union the walk built.
        raw = bundle.read(BUNDLE, document)
        node = schema_parse.parse(
            raw,
            pointer="",
            position=keywords.Position.ROOT,
            source=schema_parse.Source(
                document=document, applied_at=bundle.constrained_to_object(raw)
            ),
        )
        assert isinstance(node, nodes.Union), (document, type(node).__name__)
        branches = [b for b in node.branch_raw if isinstance(b, dict)]
        assert branches, (document, node.stated_at)
        # The two shapes the second source would read: a branch carrying the envelope's
        # key, and a branch that IS one of the schemas the manifest resolves.  Collected
        # and not asserted here, for the reason above the loop.
        #
        # **Resolved by DOCUMENT and not by basename**: ``bundle.document_for`` is the
        # one reading of a reference's document half, and a basename match would report
        # a collision between two domains as a resolution.
        carries_the_key += [
            document for b in branches if field in (b.get("properties") or {})
        ]
        for i, b in enumerate(branches):
            if "$ref" not in b:
                continue
            head, _ = bundle.split_ref(b["$ref"])
            target = bundle.document_for(head, known) if head else document
            if target in resolves:
                branches_the_manifest_resolves.append((document, i, target))
    assert carries_the_key == [], sorted(set(carries_the_key))
    assert branches_the_manifest_resolves == [], {
        "§4's second source names these roots and no code dispatches them "
        "(adcp-client-python-82m.44)": sorted(
            {d for d, _, _ in branches_the_manifest_resolves}
        ),
        "branch -> the resolved document it references": branches_the_manifest_resolves,
    }

    # The decisive one: most of them ARE what the manifest resolves TO, so the key is
    # spent before the branch choice is reached.  Partitioned BY NAME, because the two
    # halves are different facts and their sum is not one: the resolved half is where
    # the manifest's key is spent on the document, and the rest are documents the
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
    claimed(
        "overlapping roots the manifest does not name at all",
        set(overlapping) - set(resolved_overlaps),
        inside=overlapping,
    )
    # **THE NINE-DOCUMENT EQUALITY THAT STOOD HERE IS GONE** (2026-11-04).  It pinned
    # ``set(resolved_overlaps)`` to a list of nine, which is this set intersected with
    # what the manifest resolves -- a census twice over: a root the derivation learns to
    # separate leaves it, and an upstream tool added to ``manifest.tools`` joins it.  The
    # two comments below it recorded exactly that happening twice, once per row.  The
    # partition above says the property instead: every inseparable root is accounted for
    # by exactly one of the two halves, both halves are non-empty and named, and which
    # documents are in which is the run's answer rather than this file's.


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
    class that is the union of its branches.  What is graded here is the POPULATION,
    because the count is what the previous instalment got wrong: it read 3 DOCUMENTS off
    nearby refusals, and the clause's own shape holds at one site.

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
#: Every member is an ``anyOf`` the document states as a CONSTRAINT -- branches that
#: narrow one shape rather than alternating between shapes, which §4 compiles to a rule
#: (``AtLeastOne`` / ``PresenceGroups``) and not to a discriminated union, so no
#: separator is owed one.  ``adagents.json#/oneOf/1/allOf/0/anyOf`` says so in its own
#: ``$comment``: "Each arm asserts non-emptiness directly."
#:
#: **``core/postal-country-system.json#/anyOf`` LEFT THIS SET on 2026-11-04, and it left
#: because the READING of the population was corrected rather than because the set was
#: relaxed.**  It was described here as narrowing ``country`` and ``system`` ten ways
#: with the last three being "at least one of these two keys", and it was in this set
#: because the two readers above asked ``harness.separates`` the question WITHOUT the
#: enclosing node's ``required``.  §4's first separator reads the entailment, the walk
#: has always handed it that list (``lower/union.py``'s ``root_required``), and §4's own
#: paragraph names this very document as the case the weak reading got wrong: "Reading
#: only single values made ``core/postal-country-system.json#/anyOf`` inseparable on 12
#: pairs ... while all ten branches are pairwise disjoint in fact and the emitted classes
#: dispatch deterministically."  With the question asked properly the derivation
#: separates all ten branches, and the walk already agreed -- it declares no
#: UNDERDETERMINED for this document.  Removing the entry is the pin FOLLOWING the
#: behaviour, the same move the two ``viewability`` nodes needed.
#:
#: **The two ``viewability`` nodes LEFT this set, and the set is where the departure is
#: recorded** (``adcp-client-python-10l.64``, corrected at ``10l.76``).
#: ``core/canonical-forecast-point.json`` and ``core/forecast-point.json`` at
#: ``/properties/viewability/anyOf`` state one branch that forbids four metrics and one
#: that requires ``standard``, and they were named here as constraints a separator is not
#: owed.  They are no longer in the population this set partitions at all:
#: ``schema.presence_clause`` reads a branch stating ONLY a ``not`` over required groups
#: as a presence clause with an empty required group, so both nodes are presence-only and
#: :func:`_authored_unions`' own gate excludes them -- "a presence-only combinator is
#: excluded ... it lowers to a rule on the enclosing class".  The entries went stale in
#: the commit that made the sentence above literally true of them, which is the one place
#: a census of a derived population can go stale: the derivation moved and the name did
#: not move with it.  Removing them is the pin FOLLOWING the behaviour, and the partition
#: is what reported the gap.
_INSEPARABLE_CONSTRAINTS = frozenset(
    {
        "adagents.json#/oneOf/1/allOf/0/anyOf",
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


def _authored_unions() -> list[tuple[str, str, list[dict], list[Any], frozenset[str]]]:
    """Every authored union of 3.2 whose branches are all SHAPES, with the applied type
    and the ENCLOSING NODE'S ``required``.

    The GATE is the one both halves of §8's third equality already apply -- a branch is a
    shape where its node under the enclosing ``type`` is an object -- because that is the
    set where branch CLASSES exist and a declaration order has something to choose
    between.  A presence-only combinator is excluded for the same reason: it lowers to a
    rule on the enclosing class (``schema.presence_only``, the parser's own reading).

    **THE ENCLOSING ``required`` IS RETURNED BECAUSE §4's FIRST SEPARATOR READS THE
    ENTAILMENT AND NOT THE BRANCH'S OWN LIST** (2026-11-04).  §4's first source is "a
    ``const`` every branch pins on one shared property AND every branch REQUIRES", and
    the plan's own paragraph beneath it says the question is whether the document
    GUARANTEES the key's presence -- which it does "through the root's own ``required``
    or through every branch's".  ``lower.union.dispatch`` reads it that way
    (``lower/union.py``: ``root_required = frozenset(node.required)``, handed to
    ``separates`` one line down), and the two callers in this file did NOT: they asked
    both readings the weaker question, so the two agreed with each other while neither
    agreed with the walk.  27 of the authored unions state a non-empty ``required`` at
    the enclosing node, and two of them are separable only through it.
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
                out.append(
                    (
                        f"{document}#{base}/{keyword}",
                        keyword,
                        branches,
                        applied,
                        frozenset(node.get("required") or ()),
                    )
                )
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
        at for at, _, _, _, _ in _authored_unions()
    })
    assert len(unions) == len(_authored_unions()), "two unions at one pointer"
    disagreed = []
    for at, _, branches, applied, root_required in _authored_unions():
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                # **BOTH READINGS TAKE THE ENCLOSING ``required``**, which is the question
                # §4 asks and the one ``lower.union.dispatch`` hands the walk.  Omitting it
                # on both sides kept this equality green while neither side answered the
                # walk's question (see :func:`_authored_unions`).
                walk = lower_union.separates(
                    _planned(at, f"{at}/{i}", branches[i]),
                    _planned(at, f"{at}/{j}", branches[j]),
                    applied[i],
                    applied[j],
                    root_required=root_required,
                )
                record = harness.separates(
                    branches[i],
                    branches[j],
                    applied[i],
                    applied[j],
                    root_required=root_required,
                )
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
            for at, keyword, branches, _, _ in _authored_unions()
            if not any(_states_a_reference(b) for b in branches)
        ],
    )
    inseparable = {
        at: [
            (i, j)
            for i in range(len(branches))
            for j in range(i + 1, len(branches))
            # ``root_required``: §4's first separator reads the ENTAILMENT, so the
            # enclosing node's ``required`` is part of the question (see
            # :func:`_authored_unions`).  Without it this reading called two pairs
            # inseparable that the walk separates.
            if harness.separates(
                branches[i],
                branches[j],
                applied[i],
                applied[j],
                root_required=root_required,
            )
            is None
        ]
        for at, keyword, branches, applied, root_required in _authored_unions()
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


# --------------------------------------------------------------------------- #
# §5's oneOf/anyOf row at CONJ (``adcp-client-python-10l.37``)
# --------------------------------------------------------------------------- #
#: Every node of bundle 3.2 whose combinator of SHAPES is written in one of its own
#: ``allOf`` conjuncts, by the pointer the document writes the keyword at.  **Named and
#: not counted**, because the row's whole claim is about these sites and a census
#: equality over a number says nothing about which ones.
#:
#: The two under an ``if`` are not here and could not be: §4 keeps a subschema at RULE as
#: a rule SOURCE and never hands it to :func:`codegen.schema.parse.parse`, so no node is
#: ever classified there.  They are ``governance/check-governance-request.json`` at
#: ``/allOf/13/if/allOf/1`` and ``protocol/get-adcp-capabilities-response.json`` at
#: ``/allOf/11/if/allOf/1``, and ``lower/rules.py`` is what reads them.
class Borne(NamedTuple):
    """One union the walk classified from a CONJUNCT's combinator, as the walk built it."""

    document: str
    #: The composing node's own pointer -- what the class is declared at.
    pointer: str
    #: The pointer the combinator is WRITTEN at, which is one of this node's conjuncts.
    stated_at: str
    combinator: str
    #: Each branch's pointer, in the document's own order.
    branches: tuple[str, ...]
    #: The conjuncts that still compose, at the indices the document gives them.
    conjuncts: tuple[str, ...]

    @property
    def at(self) -> str:
        """``document`` and ``stated_at``, for a report a reader can open."""
        return f"{self.document}#{self.stated_at}"


def _borne(population: list[str]) -> list[Borne]:
    """Every union the WALK built whose combinator is borne by a conjunct, recorded at
    the parse.

    **THIS FUNCTION IS THE MEASUREMENT AND NOTHING ELSE NAMES THE SET**
    (``adcp-client-python-10l.79``).  A hand-listed census stood beside it -- five
    documents and their pointers -- and it went stale the day two §5 rulings landed
    after the row that wrote it: the presence clause's disjunction half and its empty
    required half made three of the five a RULE, so the census claimed five where the
    derivation found two.  ``tests/nodeset.py`` says why that was the wrong shape in the
    first place: "a check names its own set at the point it ranges over it, because a
    set named somewhere else is a second place to go stale."  So the tests below range
    over what this returns and assert the READINGS, and the only count any of them
    states is :func:`nodeset.claimed`'s refusal of an empty one.

    Derived from the production classifier and not from a second walk of the raw
    mappings: the claim the row makes is that ``schema.parse`` decides this, so the
    instrument has to be that function and the carrier has to be the fields it sets
    (:attr:`codegen.schema.nodes.Union.stated_at`, :attr:`~.Union.conjuncts`).  A node
    whose combinator sits at its own pointer is not one of these and does not appear.
    """
    seen: dict[tuple[str, str], Borne] = {}
    real = schema_parse.parse

    def traced(raw: Any, **kw: Any) -> Any:
        node = real(raw, **kw)
        if isinstance(node, nodes.Union) and node.stated_at != node.pointer:
            seen[(node.document, node.stated_at)] = Borne(
                document=node.document,
                pointer=node.pointer,
                stated_at=node.stated_at,
                combinator=node.combinator,
                branches=tuple(b.pointer for b in node.branches),
                conjuncts=tuple(c.pointer for c in node.conjuncts),
            )
        return node

    schema_parse.parse = traced  # type: ignore[assignment]
    try:
        emit.emit(BUNDLE, population)
    finally:
        schema_parse.parse = real  # type: ignore[assignment]
    return sorted(seen.values())


def test_a_conjuncts_combinator_of_shapes_is_a_union_at_the_pointer_it_is_written_at() -> (
    None
):
    """§5's ``oneOf``/``anyOf`` row at CONJ: "one class per branch over the composed
    bases".

    Draft-07 conjoins an ``allOf`` conjunct with the node that holds it -- which is the
    reading ``schema.applies_to_one_instance`` already makes for §4's disjointness
    derivation -- so a conjunct stating a combinator of shapes states it about the
    composed node's instance.  ``schema.parse`` is the one classifier (§11), so it is
    what decides this, and :attr:`nodes.Union.stated_at` carries WHERE the keyword is
    written.

    **Every assertion here is a READING and none is a count** (``10l.79``): the set is
    :func:`_borne`'s, named at the point this ranges over it, and what is asserted of
    each member is what the classification claims -- the keyword is written at one of
    this node's own conjuncts, that conjunct declares the combinator and NOTHING else,
    it is not presence-only (so the rule reading has already declined it), the branches
    sit at ``<conjunct>/<kw>/<i>``, and every other conjunct keeps the index the
    document gives it.  A document entering or leaving the set moves nothing here.
    """
    borne = _borne(sorted(bundle.portable(BUNDLE)))
    claimed(
        "unions the parser classified from a conjunct's combinator",
        [one.at for one in borne],
    )
    for one in borne:
        raw = bundle.read(BUNDLE, one.document)
        # The COMPOSING node, which is not always the document root: a conjunct-borne
        # union can sit at a BRANCH of another union (``adagents.json`` does).
        enclosing = bundle.node_at(raw, one.pointer)
        # WHERE: the keyword is written at a conjunct of this very node, and the node's
        # own pointer is where the class is declared.
        assert one.stated_at.startswith(f"{one.pointer}/allOf/"), one
        index = one.stated_at[len(f"{one.pointer}/allOf/") :]
        assert index.isdigit(), one
        conjunct = bundle.node_at(raw, one.stated_at)
        # THE GATE: the conjunct contributes the branch list and nothing else, so
        # nothing of it is dropped by being read as the node's combinator.
        declared = {k for k in conjunct if keywords.declares(k, keywords.Position.CONJ)}
        assert declared == {one.combinator}, (one, sorted(declared))
        # SEQUENCED AFTER THE RULE READING, which is the same gate ``parse.parse`` asks
        # of a node's own combinator: a conjunct whose branches are presence groups is a
        # rule on the composed class and never reaches this classification.
        assert not schema_parse.presence_only(conjunct, keywords.Position.CONJ), one
        # THE BRANCHES: at the conjunct's own pointer, one per branch, in order.
        assert one.branches == tuple(
            f"{one.stated_at}/{one.combinator}/{i}"
            for i in range(len(conjunct[one.combinator]))
        ), one
        # THE OTHER CONJUNCTS: the document's own indices, with the carrier removed and
        # nothing re-pointed -- which is what a list rebuilt by ``enumerate`` would do.
        assert one.conjuncts == tuple(
            f"{one.pointer}/allOf/{i}"
            for i in range(len(enclosing["allOf"]))
            if i != int(index)
        ), one


def test_the_classification_declines_rather_than_guessing(tmp_path) -> None:
    """The three ways :func:`parse._borne_by_a_conjunct` declines, graded on PROBES.

    Each leaves the node a :class:`nodes.Composition`, so its refusal stays exactly
    where it was.  Graded on constructed documents and not on the bundle, because the
    bundle states none of the three -- which is the measurement, and a decline arm with
    no population is still an arm a reader has to be able to see work.
    """
    def classify(raw: dict) -> Any:
        return schema_parse.parse(
            raw,
            pointer="",
            position=keywords.Position.ROOT,
            source=schema_parse.Source(document="probe.json"),
        )

    shapes = {"oneOf": [{"properties": {"a": {"type": "string"}}}, {"required": ["b"]}]}
    # It CLASSIFIES where exactly one conjunct carries one and states nothing else.
    one = classify({"type": "object", "allOf": [{"$ref": "x.json"}, dict(shapes)]})
    assert isinstance(one, nodes.Union) and one.stated_at == "/allOf/1", one

    # 1. TWO conjuncts carry one: the instance is described by two branch lists and
    #    there is no single class-per-branch answer.
    two = classify({"type": "object", "allOf": [dict(shapes), dict(shapes)]})
    assert isinstance(two, nodes.Composition), two
    # 2. The node states one of its own beside a conjunct that does: its own arm has
    #    already answered, and this one must not answer again.
    beside = classify({"type": "object", "allOf": [dict(shapes)], **shapes})
    assert isinstance(beside, nodes.Union) and beside.stated_at == "", beside
    # 3. The conjunct states something ELSE beside the combinator, so it contributes to
    #    the composed class as well and the conjunction of the two has no pointer.
    alongside = classify(
        {"type": "object", "allOf": [{**shapes, "required": ["c"]}]}
    )
    assert isinstance(alongside, nodes.Composition), alongside


def test_the_conjunct_borne_combinator_separates_or_names_the_pair() -> None:
    """§4's THIRD source, asked of a conjunct-borne union, and the finding where it
    cannot answer.

    The derivation takes a branch LIST and a node; where the keyword was written is not
    one of its inputs, so nothing about it needed widening for this position -- which is
    this test's claim, made by running the production :func:`union.separates` over the
    branches the production parse built.

    **The PARTITION is the assertion and neither half is listed** (``10l.79``).  §4's
    first source derives no key at any of these -- asserted of every member, with the
    pins it did read reported -- so the third is what decides them, and each site either
    separates every pair or NAMES the pairs it cannot.  Where it cannot, the shape is
    asserted rather than the document: some branch of an overlapping site demands no name
    at all, which is what makes it an ``anyOf`` the document states as a CONSTRAINT
    rather than an alternation of shapes.  That is ``adcp-client-python-10l.30``'s
    partition, derived again at this position, and rows .29 / onq own the rule it wants.
    """
    borne = _borne(sorted(bundle.portable(BUNDLE)))
    claimed("conjunct-borne unions the derivation is asked about", [one.at for one in borne])
    overlaps: dict[str, list[str]] = {}
    planned_at: dict[str, list[lower_union.Branch]] = {}
    for one in borne:
        raw = bundle.read(BUNDLE, one.document)
        # The node is reached at ITS OWN pointer, which is not always the root: a
        # conjunct-borne union can sit at a BRANCH of another union.  Parsed through the
        # production classifier either way, so the branches asked about are the walk's.
        enclosing = bundle.node_at(raw, one.pointer)
        node = schema_parse.parse(
            enclosing,
            pointer=one.pointer,
            position=(
                keywords.Position.ROOT if one.pointer == "" else keywords.Position.BRANCH
            ),
            source=schema_parse.Source(
                document=one.document, applied_at=bundle.constrained_to_object(raw)
            ),
            objectish=one.pointer != "",
        )
        assert isinstance(node, nodes.Union), (one, type(node).__name__)
        assert node.stated_at == one.stated_at, (one, node.stated_at)
        planned = [
            _planned(one.document, parsed.pointer, branch)
            for parsed, branch in zip(node.branches, node.branch_raw, strict=True)
        ]
        planned_at[one.at] = planned
        # §4's FIRST source derives no key, which is what sends the question to the
        # third.  Reported with the pins it DID read, so a site that starts pinning one
        # is readable rather than merely red.
        assert lower_union.discriminator(planned, lower_union.dispatch_key(node)) == "", (
            one.at,
            lower_union._why_no_pin(planned),
        )
        overlaps[one.at] = lower_union.overlapping(planned, node)

    partitions(
        {one.at for one in borne},
        disjoint={at for at, pairs in overlaps.items() if not pairs},
        overlapping={at for at, pairs in overlaps.items() if pairs},
    )
    for at, pairs in sorted(overlaps.items()):
        if not pairs:
            # Every pair separated: §4's third source names the branches and the union
            # dispatches without a key.
            continue
        # The pairs are NAMED, which is what makes an overlap a finding a reader can open
        # rather than a verdict about the derivation -- and each name is two POINTERS of
        # this very union, not prose.
        branches = {plan.pointer for plan in planned_at[at]}
        for pair in pairs:
            left, _, right = pair.partition(" and ")
            assert left in branches and right in branches, (at, pair)
        # THE SHAPE, derived: an ``anyOf`` stated as a CONSTRAINT has a branch that
        # demands no name at all, so no separator §4 names can tell it from any sibling.
        # Asserted of the branches rather than of the document, so a site joining or
        # leaving this half carries its own reason.
        assert any(not lower_union.demands(plan) for plan in planned_at[at]) or any(
            not plan.forbids and not lower_union.closures_of(plan)
            for plan in planned_at[at]
        ), (at, pairs)


def test_a_union_of_shapes_reaching_the_composing_row_without_a_caller_refuses() -> None:
    """A :class:`nodes.Union` handed to ``compiler.lower_composition`` with no
    ``UnionBase`` would build the composed class with the branch list DROPPED, so it
    refuses -- by the keyword, at the pointer the document writes it at.

    **Its population is 0 and the test grades BOTH halves, because that is what a
    backstop is.**  ``adagents.json`` at ``/oneOf/1`` was the one node that reached it;
    ``adcp-client-python-10l.66`` landed §5's own answer for a branch that is ITSELF a
    union -- ``union.lower_union``'s branch loop recurses with the enclosing base -- and
    that arm is read BEFORE the composing one, so no document arrives here any more.  The
    arm is not a duplicate of it: one is the cell's answer and this is the assertion that
    the answer was TAKEN.  A fact dropped with nothing to report it is the one outcome §2
    does not permit at any rung, so the guard is graded directly rather than deleted for
    having no population.

    The DECISION is graded at :func:`compiler._refuse_a_combinator_of_shapes`, which is
    the whole of it, and the POPULATION by tracing every call the walk makes.
    """
    node = schema_parse.parse(
        bundle.node_at(bundle.read(BUNDLE, "adagents.json"), "/oneOf/1"),
        pointer="/oneOf/1",
        position=keywords.Position.BRANCH,
        source=schema_parse.Source(document="adagents.json"),
        objectish=True,
    )
    assert isinstance(node, nodes.Union), type(node).__name__
    # The keyword is NOT in the node's own declares -- the conjunct states it -- which is
    # exactly why the screen reading could not see it and the kind has to be the subject.
    assert "anyOf" not in node.declares, node.declares
    refusal = compiler._refuse_a_combinator_of_shapes(node, frozenset())
    assert refusal is not None
    assert (refusal.keyword, refusal.pointer) == ("anyOf", "/oneOf/1/allOf/0"), refusal
    assert "the branch list would be dropped" in refusal.detail, refusal
    # The kind is the CELL's and not this site's (``docs/plan/architecture.md`` §3).
    assert refusal.kind == compiler.kind_for("anyOf", keywords.Position.BRANCH), refusal

    # And no document of the bundle reaches it, traced at the call rather than asserted
    # from the refusal set: a stale guard is one whose population a reader cannot see.
    reached: list[tuple[str, str]] = []
    real = compiler.lower_composition

    def traced(node: Any, mod: Any, **kw: Any) -> Any:
        if isinstance(node, nodes.Union) and kw.get("union") is None:
            reached.append((mod.source.document, node.stated_at))
        return real(node, mod, **kw)

    compiler.lower_composition = traced  # type: ignore[assignment]
    lower_union.compiler.lower_composition = traced  # type: ignore[assignment]
    try:
        # ``store.perturbed()``: ``emit.emit`` holds §1's census on disk under a digest of
        # ``codegen/``'s source (``codegen/store.py``), which this reassignment does not
        # move, so pass one would be unpickled and the tracer would see the final walk
        # alone -- and this check's whole claim is that NO document of the bundle reaches
        # the site, over every walk the run makes.
        with store.perturbed():
            emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    finally:
        compiler.lower_composition = real  # type: ignore[assignment]
        lower_union.compiler.lower_composition = real  # type: ignore[assignment]
    assert reached == [], sorted(set(reached))
