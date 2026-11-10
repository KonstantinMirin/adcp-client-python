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
the answer was the same for 143 of its 145 rows and *different for two*, because two of
them were in this tree -- not emitted, but restored, in upstream's own hand-written
``canonical_creative.py``, and reachable at a public name.

**THOSE TWO ARE GONE, AND THE REPAIR IS THE ONE THE THIRD GATE NAMED.**  That gate's own
closing clause read: "RED on a third site (a new defect) and RED on zero (repaired --
update ``0z0u`` and delete this gate's record)."  ``adcp-client-python-2f52`` deleted
``src/adcp/types/canonical_creative.py``, which is where both sites lived --
``CreateMediaBuyResponse1._normalize_legacy_status`` and
``UpdateMediaBuyResponse1._normalize_legacy_status``, each writing
``{**data, "status": "completed"}`` into a payload that omitted a field our emitted arm
requires.  So ``survey/invented_defaults.restored_injections`` now reports ZERO ``status``
sites, the third gate and its live witness are deleted as that clause instructs, and the
divergence is recorded closed on ``0z0u``.  **The repair is not that the alias layer was
re-pointed one MRO hop up** -- which is what the gate proposed -- but that the lax subclass
does not exist to be pointed at, and ``adcp.types.CreateMediaBuySuccessResponse`` is now
REFUSED by name with that very reason in ``adcp.types._adapter.__adcp_refused__``: "their
``CreateMediaBuyResponse1`` pins ``{'status': 'completed'}`` and the subject it reaches
pins nothing there".  Two gates remain, and neither had teeth over a live defect of ours.

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

#: **NO RESTORED SITE INVENTS A REQUIRED FIELD, and this is the measurement rather than an
#: empty default.**  The set held two ``(class.validator, field)`` pairs, both in
#: ``src/adcp/types/canonical_creative.py``; that file is deleted and the set derives empty.
#: Kept as a NAMED set with its own gate below, because "zero" is the claim and a reader
#: cannot tell a zero that was measured from a reading that stopped matching -- which is the
#: failure mode this whole module's docstring was written about.  A restored module that
#: starts inventing a required field reddens :func:`test_no_restored_before_validator_invents_a_required_field`.
RESTORED_INVENTIONS: set[tuple[str, str]] = set()


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
# 3. the defect that WAS live, now zero -- measured, not defaulted
# --------------------------------------------------------------------------- #
def test_no_restored_before_validator_invents_a_required_field(tmp_path: Path) -> None:
    """Zero injections across the restored modules, and the reading is PERTURBED to say so.

    **WHAT THIS GATE USED TO RECORD.**  ``canonical_creative.CreateMediaBuyResponse1``
    subclassed our emitted ``CreateMediaBuySuccess``, where ``status`` is required with no
    default, and ``_normalize_legacy_status`` -- a ``model_validator(mode="before")`` three
    lines down -- wrote ``{**data, "status": "completed"}`` when the caller omitted it.  The
    field was required and the requirement unreachable, which refuted ``eknd``'s ruling
    comment ("their restored classes would subclass OUR classes, inheriting the document's
    requiredness ... Nothing is weakened anywhere") for that one field.  Two sites, both in
    that file, and the gate's own instruction for the zero case was "repaired -- update
    ``0z0u`` and delete this gate's record".  ``adcp-client-python-2f52`` deleted the file;
    the record is deleted and this is what replaced it.

    **AND A ZERO HAS TO BE A MEASUREMENT, which is the whole reason this is still a gate.**
    ``restored_injections`` now matches NOTHING in ``src/adcp/types`` -- not merely no
    ``status`` -- so "no site invents a required field" and "the reading stopped matching
    its own subject" are the same green, and the second is the failure mode this module's
    docstring was written about.  The reading is therefore run against a module written for
    the purpose, carrying the exact shape the deleted file carried, and is required to find
    it.  RED on a restored module that starts inventing a field, and RED on a reading that
    could no longer see one.
    """
    live = {(who, key) for _, who, key in invented_defaults.restored_injections()}
    status_sites = {(who, key) for who, key in live if key == "status"}
    assert status_sites == RESTORED_INVENTIONS, {
        "a restored before-validator invents `status` at a site not on record": sorted(
            status_sites - RESTORED_INVENTIONS
        ),
        "a recorded site is gone -- if repaired, record it on adcp-client-python-0z0u": sorted(
            RESTORED_INVENTIONS - status_sites
        ),
    }

    # The deleted shape, re-created, and the reading has to report it.  Written out rather
    # than read from git: what is graded is the AST predicate, not upstream's bytes.
    (tmp_path / "restored_like.py").write_text(
        "from pydantic import model_validator\n\n\n"
        "class CreateMediaBuyResponse1:\n"
        "    @model_validator(mode='before')\n"
        "    @classmethod\n"
        "    def _normalize_legacy_status(cls, data):\n"
        '        return {**data, "status": "completed"}\n'
    )
    perturbed = claimed(
        "keys a restored before-validator inserts",
        {(who, key) for _, who, key in invented_defaults.restored_injections(tmp_path)},
    )
    assert ("CreateMediaBuyResponse1._normalize_legacy_status", "status") in perturbed, sorted(
        perturbed
    )


def test_the_emitted_arm_refuses_what_the_deleted_subclass_admitted() -> None:
    """The emitted arm's own refusal, and the public name that no longer reaches a lax one.

    ``0z0u`` names ``CreateMediaBuyResponse1.status = 'completed'`` at ``#/oneOf/0`` as the
    worst kind's example: the document's ``allOf[1]`` requires ``status`` and its
    ``oneOf[0]`` states no value for it, so a class that defaults it both makes a required
    field optional AND fills it with a value no reading of the document produces.  Our
    emitted arm does neither, which is the half of that sentence this tree is answerable
    for and is asserted here as behaviour.

    **AND THE OTHER HALF IS NOW A REFUSAL BY NAME.**  The lax subclass was reached at
    ``adcp.types.CreateMediaBuySuccessResponse``; with the file deleted the adapter's
    ordinal key cannot bind that word -- upstream's ``CreateMediaBuyResponse1`` pins
    ``{'status': 'completed'}`` where the subject it reaches pins nothing -- so the word
    raises from ``__getattr__`` carrying that reason.  Both are asserted, because an
    unbound name and a name over a lax type are different outcomes and only one of them is
    reading 10's.

    **AND IT STILL FIXES A TEST THAT PASSES FOR A REASON IT DOES NOT NAME.**
    ``tests/test_server_dx.py::test_typed_success_rejects_async_task_status`` exists on both
    media-buy arms and reads as though the success arm pins ``status``.  It does not: the
    document's ``oneOf[0]`` states no ``status``, so the conjunction's enum of nine governs
    and ``working`` IS admissible on the success arm -- our emitted class accepts it, which
    is correct.  Those two tests pass only because the constructions they wrap also omit
    ``revision`` and ``confirmed_at``.  That is a defect in the tests' premise and not in
    this tree; it is recorded on ``0z0u`` and ``tests/`` is not this file's to edit.
    """
    import importlib

    from adcp.types._schemas.media_buy.create_media_buy_response import CreateMediaBuySuccess

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
    else:  # pragma: no cover - the emitter would have to have regressed to reach this
        raise AssertionError(
            "the EMITTED success arm admits a payload with no `status`, which "
            "media-buy/create-media-buy-response.json's allOf[1] requires"
        )

    # The lax subclass is gone, and the public word that reached it is refused WITH the
    # reason rather than silently absent.
    assert importlib.util.find_spec("adcp.types.canonical_creative") is None, (
        "adcp.types.canonical_creative is importable again; this gate's subject is back"
    )
    adapter = importlib.import_module("adcp.types._adapter")
    why = adapter.__adcp_refused__.get("CreateMediaBuySuccessResponse")
    assert why is not None, "the word is bound again, with no record of what it reaches"
    import adcp.types

    try:
        adcp.types.CreateMediaBuySuccessResponse
    except AttributeError:
        pass
    else:  # pragma: no cover - the line above is the claim
        raise AssertionError(
            "adcp.types.CreateMediaBuySuccessResponse resolves; the adapter refuses it"
        )
    # And the refusal carries its reason at the module the verdict belongs to.
    try:
        adapter.CreateMediaBuySuccessResponse
    except AttributeError as caught:
        assert "CreateMediaBuyResponse1" in str(caught), str(caught)
    else:  # pragma: no cover - the line above is the claim
        raise AssertionError("adcp.types._adapter binds the word it records as refused")
