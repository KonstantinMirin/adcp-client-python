"""**THE INVENTED-DEFAULT SET, GRADED** -- ``adcp-client-python-0z0u``'s measurement and
``adcp-client-python-eknd``'s decision, held in place.

``0z0u`` measures 867 ``(upstream class, field)`` pairs over upstream's tree at
``2954b258b`` where their generator carries a default the document does not state, split
four ways: ``const-restated`` 477, ``collapsed-disjunction`` 237, ``invented-value`` 145,
``contradicts`` 8.  ``eknd`` asks what is owed over that set.  **The ruling is per KIND and
it is the same ruling three times and a different one once**, and this file is the half of
it that a future change cannot quietly undo.

**THE DECISION.**  For ``contradicts``, ``const-restated`` and ``collapsed-disjunction``
the answer is REPORT AND DO NOT REPAIR: the defect is upstream's generator's, nothing of
ours carries it, and a repair here would have to invent a subject.  For ``invented-value``
the answer is the same for 143 of its 145 rows and *different for two*, because two of them
are in this tree right now -- not emitted, but restored, in upstream's own hand-written
``canonical_creative.py``, and reachable at a public name.  So there are three gates and
the third is the only one with teeth over a live defect.

**WHY THE CLAIM IS STATED OVER ``required_at`` AND NOTHING WIDER, which is measured and not
a convenience.**  ``survey/invented_defaults.ours`` asks only about the CONJUNCTION reaching
a class's own stated pointer.  A reading that also asked about ``some_arm_requires`` has to
decide *how* a disjunction's requiredness is carried, and this compiler carries it four
ways -- a per-arm class whose field is required, a ``RequiredGroups`` rule, a
``PresenceGroups`` rule of ``Presence`` clauses, and ``BranchDispatchMixin`` dispatch.
Three successive readings during ``eknd``'s derivation reported 223, then 77, then 47 "lax"
pairs of ours and every correction moved the same way, because each had met one more
mechanism; all 223 were the reader.  A gate built on the wider predicate would therefore
go RED for a mechanism nobody had met yet, and -- far worse -- a gate built on it and then
tuned until it passed would be the fence this epic exists to refuse.  ``required_at`` is the
conjunction alone.  No mechanism can hide in it, so the answer does not depend on having
enumerated them.

**AND EVERY SET HERE IS NAMED AND ASSERTED NON-EMPTY** (``nodeset.claimed``), because the
failure this file is most likely to suffer is its own: four measurements on this epic read
green because a predicate could not match its own subject, and one of them was an earlier
draft of the join below, whose pointer column spelled ``/oneOf/0`` against a tree spelling
``#/oneOf/0`` and reported 632 of the 867 rows as having no class of ours at all.
"""

from __future__ import annotations

import collections
import csv
from pathlib import Path

from nodeset import claimed, partitions

from survey import invented_defaults

REPO = Path(__file__).resolve().parent.parent

#: ``0z0u``'s committed membership.  Read as the artifact it is; the derivation that wrote
#: it is ``survey/invented_defaults.py`` and re-running it needs upstream's whole tree out
#: of ``git archive``, which is a survey's job and not a gate's.
TABLE = REPO / "survey" / "invented-defaults-9.6.1.tsv"

#: ``0z0u``'s digest of the MEMBERSHIP ``(kind, class, field)``, not of its size.  The
#: artifact's own reason, quoted: "A COUNT THAT DOES NOT MOVE IS NOT EVIDENCE THE SET DID
#: NOT MOVE".  So this gate compares the digest and never a total, which is also why it is
#: not a census equality under ``test_every_check_names_its_set``.
DIGEST = "7d05549bb6e45d66b955"

#: The restored sites where upstream's own HAND-WRITTEN code invents a required field.
#: ``(class, validator, field)`` in ``src/adcp/types/canonical_creative.py``, which is
#: upstream's bytes byte for byte -- so this is a RECORD of a known divergence and not a
#: list of things to fix here.  ``eknd`` asks for exactly this: "a NAMED, DERIVED set ...
#: countable, and reportable beside the pass figure -- not silently absorbed into either
#: column."
RESTORED_INVENTIONS = {
    ("CreateMediaBuyResponse1._normalize_legacy_status", "status"),
    ("UpdateMediaBuyResponse1._normalize_legacy_status", "status"),
}


def _rows() -> list[dict[str, str]]:
    return list(csv.DictReader(TABLE.read_text().splitlines(), delimiter="\t"))


# --------------------------------------------------------------------------- #
# 1. the measurement itself, which must not be able to read green while empty
# --------------------------------------------------------------------------- #
def test_the_set_is_the_membership_0z0u_recorded() -> None:
    """The committed table's membership digest is ``0z0u``'s, and the four kinds exhaust it.

    Two readings of one artifact.  The digest says WHICH pairs; the partition says every
    pair is one of the four kinds ``0z0u`` names and no pair is two of them -- so a fifth
    kind appearing, or a row losing its kind, is a failure here rather than a silent
    reshuffle under an unchanged total.
    """
    rows = _rows()
    pairs = claimed(
        "0z0u's invented-default pairs", {(r["kind"], r["upstream"], r["field"]) for r in rows}
    )
    assert len(pairs) == len(rows), "the table repeats a (kind, class, field)"

    by_kind = collections.defaultdict(set)
    for kind, upstream, field in pairs:
        by_kind[kind].add((kind, upstream, field))
    partitions(
        pairs,
        **{kind.replace("-", "_"): members for kind, members in by_kind.items()},
    )
    assert set(by_kind) == set(invented_defaults.KINDS), {
        "kinds in the table the instrument does not define": sorted(
            set(by_kind) - set(invented_defaults.KINDS)
        ),
        "kinds the instrument defines that the table has no row for": sorted(
            set(invented_defaults.KINDS) - set(by_kind)
        ),
    }

    digest = invented_defaults._digest(
        [invented_defaults.Row(*(r[f] for f in invented_defaults.Row._fields)) for r in rows]
    )
    assert digest == DIGEST, (
        f"the set's MEMBERSHIP moved: {digest} != {DIGEST}.  Re-run "
        "`python -m survey invented_defaults --table survey/invented-defaults-9.6.1.tsv` and "
        "record the new digest on adcp-client-python-0z0u -- a membership change is a "
        "finding, not drift."
    )


# --------------------------------------------------------------------------- #
# 2. the ruling, over OUR tree: three kinds are reported and none is carried
# --------------------------------------------------------------------------- #
def test_no_class_of_ours_defaults_a_field_the_conjunction_requires() -> None:
    """**THE RULING'S OWN CLAIM, and it is ``== 0`` and not a census.**

    This is what makes "report and do not repair" an honest answer for ``contradicts``,
    ``const-restated`` and ``collapsed-disjunction``: the defect is not ours to repair
    because our tree does not have it.  Stated over every class this compiler writes and
    every field the conjunction at that class's own stated pointer requires -- the pointer
    is read off ``__adcp_schema__`` and never inferred, so nothing here is matched by
    property set and no position is ambiguous.

    The witness this gate would have caught: upstream's one line
    ``ProtocolEnvelope.status: TaskStatus = TaskStatus.completed``, against a document
    stating ``required: ['status']`` with no ``default`` and no ``const``, which 116 of the
    867 rows inherit.  Ours writes the same annotation with no default.
    """
    records = invented_defaults.records_of(REPO / "src" / "adcp" / "types" / "_schemas")
    claimed("documents of record", set(records))
    lax, counts, _ = invented_defaults.ours(records)
    claimed(
        "classes of ours that state their own pointer",
        {f"{c}" for c, _ in invented_defaults.our_classes()},
    )
    assert counts["conjunction-required-fields"], (
        "no conjunction-required field was reached at all -- the predicate did not match "
        "its subject, and every assertion below holds vacuously"
    )
    assert not lax, {
        "our class carries a default for a field its own document's conjunction requires": [
            "\t".join(row) for row in lax
        ]
    }


def test_each_disjunction_base_of_ours_refuses_the_omission() -> None:
    """The eleven ``= None`` slots that are NOT invented defaults, and why -- behaviourally.

    A class at a position whose disjunction's every arm requires a field is the shared BASE
    of that disjunction; this compiler puts the slot on the base and the requirement on the
    branches, so ``model_fields`` reports a default and the document is still honoured.
    That is a claim about what the class ADMITS, so it is graded by validating an object
    that omits the field rather than by recognising the mechanism -- ``invented_defaults.
    _disjunction_base``'s second condition, surfaced here so the eleven are a named set and
    not an allowlist.  A twelfth appearing is fine; a twelfth that ACCEPTS the omission
    fails the gate above, which is where it belongs.
    """
    records = invented_defaults.records_of(REPO / "src" / "adcp" / "types" / "_schemas")
    _, _, bases = invented_defaults.ours(records)
    named = claimed("disjunction bases of ours", {(r.ours, r.field) for r in bases})
    for key, field in sorted(named):
        assert field, f"{key}: a base recorded against no field"


# --------------------------------------------------------------------------- #
# 3. the one live defect, NAMED -- and it is upstream's hand-written file, not our emitter
# --------------------------------------------------------------------------- #
def test_the_restored_invented_defaults_are_exactly_the_two_on_record() -> None:
    """``canonical_creative.py``'s two ``status`` injections, and no third.

    **THE SHAPE THE DECLARATIVE READING CANNOT SEE.**  ``CreateMediaBuyResponse1``
    subclasses our emitted ``CreateMediaBuySuccess``, where ``status`` is required with no
    default, and ``_normalize_legacy_status`` -- a ``model_validator(mode="before")`` in the
    same file -- writes ``{**data, "status": "completed"}`` when the caller omitted it.  So
    the field is required and the requirement is unreachable, and ``eknd``'s own ruling
    comment ("their restored classes would subclass OUR classes, inheriting the document's
    requiredness ... Nothing is weakened anywhere") is refuted for this one field.

    **THIS GATE RECORDS A DEFECT RATHER THAN FORBIDDING ONE, which is deliberate and is the
    only honest shape available here.**  The file is upstream's bytes byte for byte --
    ``test_the_adapter_writer_owns_its_paths`` grades that against live blob identity and
    ``adcp-client-python-knnw`` states it as "not one byte of upstream's source may change"
    -- so the repair is NOT an edit to this file.  It is at the alias layer, where
    ``src/adcp/types/aliases.py`` binds ``CreateMediaBuySuccessResponse`` to upstream's lax
    subclass instead of to the correct class one MRO hop above it.  Until that is decided,
    this gate is what keeps the divergence counted: RED on a third site (a new defect) and
    RED on zero (repaired -- update ``0z0u`` and delete this gate's record).
    """
    found = claimed(
        "keys a restored before-validator inserts",
        {(who, key) for where, who, key in invented_defaults.restored_injections()},
    )
    status_sites = {(who, key) for who, key in found if key == "status"}
    assert status_sites == RESTORED_INVENTIONS, {
        "a restored before-validator invents `status` at a site not on record": sorted(
            status_sites - RESTORED_INVENTIONS
        ),
        "a recorded site is gone -- if repaired, record it on adcp-client-python-0z0u": sorted(
            RESTORED_INVENTIONS - status_sites
        ),
    }


def test_the_emitted_arm_refuses_what_the_restored_subclass_admits() -> None:
    """The live witness, as behaviour rather than as a table row.

    ``0z0u`` names ``CreateMediaBuyResponse1.status = 'completed'`` at ``#/oneOf/0`` as the
    worst kind's example: the document's ``allOf[1]`` requires ``status`` and its
    ``oneOf[0]`` states no value for it, so a class that defaults it both makes a required
    field optional AND fills it with a value no reading of the document produces.  This
    grades both halves of that sentence against the two classes at that one pointer.

    **AND IT FIXES A TEST THAT PASSES FOR A REASON IT DOES NOT NAME.**
    ``tests/test_server_dx.py::test_typed_success_rejects_async_task_status`` exists on both
    media-buy arms and reads as though the success arm pins ``status``.  It does not: the
    document's ``oneOf[0]`` states no ``status``, so the conjunction's enum of nine governs
    and ``working`` IS admissible on the success arm -- our emitted class accepts it, which
    is correct.  Those two tests pass only because the constructions they wrap also omit
    ``revision`` and ``confirmed_at``.  That is a defect in the tests' premise and not in
    this tree; it is recorded on ``0z0u`` and ``tests/`` is not this file's to edit.
    """
    from adcp.types._schemas.media_buy.create_media_buy_response import CreateMediaBuySuccess
    from adcp.types.canonical_creative import CreateMediaBuyResponse1

    assert CreateMediaBuySuccess in CreateMediaBuyResponse1.__mro__, (
        "the restored arm no longer subclasses the emitted one; this gate's subject moved"
    )
    whole = {
        "media_buy_id": "mb-123",
        "packages": [],
        "revision": 1,
        "confirmed_at": "2026-05-27T12:00:00Z",
    }

    emitted = CreateMediaBuySuccess.model_validate({**whole, "status": "completed"})
    assert emitted.status.value == "completed"
    try:
        CreateMediaBuySuccess.model_validate(whole)
    except Exception:  # noqa: BLE001 -- any refusal is the claim; the error shape is not
        pass
    else:  # pragma: no cover -- the emitter would have to have regressed to reach this
        raise AssertionError(
            "the EMITTED success arm admits a payload with no `status`, which "
            "media-buy/create-media-buy-response.json's allOf[1] requires"
        )

    # The restored subclass admits it, and invents `completed`.  Recorded, not asserted
    # away: see this module's third gate for why the repair is not an edit to that file.
    restored = CreateMediaBuyResponse1.model_validate(whole)
    assert restored.status.value == "completed", (
        "the restored subclass no longer invents `completed` for an absent `status` -- "
        "if that was repaired, update adcp-client-python-0z0u and this module's record"
    )
