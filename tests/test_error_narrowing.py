"""narrow_union_errors — discriminated-union ValidationError narrowing.

Stability AI Emma backend test (verdict 5/10) flagged that constructing
a ``CreativeManifest`` whose asset is missing a required field (e.g.
``ImageAsset.width``) produced a 60-line pydantic ValidationError
listing every variant of the asset content union (13+ variants). The
user's actual mistake (one missing field) was buried.

This file pins the post-fix behavior:

* End-to-end: the framework's typed-dispatch path runs the
  ``CreativeManifest`` construction through ``narrow_union_errors``
  and surfaces only the variant the user matched.
* Algorithm-level: ``narrow_union_errors`` correctly identifies the
  discriminator-matched variant, the fewest-error fallback, and the
  pass-through case for non-union errors.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from adcp.types.error_narrowing import narrow_union_errors

# ---- Pass-through cases ----


def test_pass_through_empty_errors() -> None:
    """Empty input → empty output. No surprises on no-op input."""
    assert narrow_union_errors([]) == []


def test_pass_through_non_union_errors() -> None:
    """Errors with no variant in their loc (typical scalar field
    validation) pass through unchanged."""
    errors: list[dict[str, Any]] = [
        {"type": "missing", "loc": ("brief",), "msg": "Field required"},
        {"type": "string_type", "loc": ("po_number",), "msg": "Input should be a valid string"},
    ]
    assert narrow_union_errors(errors) == errors


# ---- Variant detection ----


def test_narrow_picks_discriminator_matched_variant() -> None:
    """When one variant has only field-level errors and the others
    have ``literal_error`` on what looks like the discriminator,
    keep ONLY the matched variant's errors. This is the
    Stability/AudioStack 60-line-dump fix."""
    errors: list[dict[str, Any]] = [
        # Matched variant — missing fields, no literal_error.
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "width"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "height"),
            "msg": "Field required",
        },
        # Non-matching variants — discriminator-only failure.
        {
            "type": "literal_error",
            "loc": ("assets", "hero", "VideoAsset", "asset_type"),
            "msg": "Input should be 'video'",
        },
        {
            "type": "literal_error",
            "loc": ("assets", "hero", "AudioAsset", "asset_type"),
            "msg": "Input should be 'audio'",
        },
    ]
    narrowed = narrow_union_errors(errors)
    assert len(narrowed) == 2, f"Expected 2 ImageAsset errors, got {len(narrowed)}: {narrowed}"
    assert all("ImageAsset" in err["loc"] for err in narrowed)


def test_narrow_picks_fewest_errors_when_no_discriminator_winner() -> None:
    """When NO variant has a clean discriminator match (e.g. the user
    provided an invalid discriminator value, so every variant has a
    ``literal_error`` on the discriminator field), pick the variant
    with the fewest non-discriminator errors as the closest-fit
    guess."""
    errors: list[dict[str, Any]] = [
        # ImageAsset has 2 missing fields + literal mismatch.
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "width"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "height"),
            "msg": "Field required",
        },
        {
            "type": "literal_error",
            "loc": ("assets", "hero", "ImageAsset", "asset_type"),
            "msg": "Input should be 'image'",
        },
        # VideoAsset has 4 missing fields + literal mismatch.
        {
            "type": "missing",
            "loc": ("assets", "hero", "VideoAsset", "width"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "VideoAsset", "height"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "VideoAsset", "duration_ms"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "VideoAsset", "codec"),
            "msg": "Field required",
        },
        {
            "type": "literal_error",
            "loc": ("assets", "hero", "VideoAsset", "asset_type"),
            "msg": "Input should be 'video'",
        },
    ]
    narrowed = narrow_union_errors(errors)
    # Both variants have literal_error → no discriminator winner →
    # fewest-non-literal-errors heuristic. ImageAsset: 2 non-literal,
    # VideoAsset: 4 non-literal. ImageAsset wins.
    image_errors = [e for e in narrowed if "ImageAsset" in e["loc"]]
    video_errors = [e for e in narrowed if "VideoAsset" in e["loc"]]
    assert image_errors and not video_errors


def test_narrow_falls_back_when_variants_tie() -> None:
    """When multiple variants tie on error count, the function returns
    all errors rather than guessing — surfaces the ambiguity to the
    adopter who can disambiguate via the discriminator."""
    errors: list[dict[str, Any]] = [
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "width"),
            "msg": "Field required",
        },
        {
            "type": "missing",
            "loc": ("assets", "hero", "VideoAsset", "duration_ms"),
            "msg": "Field required",
        },
    ]
    # Both variants have 1 non-literal error. Tie → keep both.
    narrowed = narrow_union_errors(errors)
    assert len(narrowed) == 2


# ---- End-to-end: CreativeManifest with missing field ----


def test_e2e_creative_manifest_missing_width_height_surfaces_actionable_errors() -> None:
    """End-to-end regression for the Stability AI Emma report case.

    Original symptom: constructing a CreativeManifest with an asset
    missing required fields produced ~26 ValidationErrors covering every
    variant of the asset-content union. The actionable mistake (one
    missing field) was buried.

    After the AdCP 3.0.2 asset-union refactor (canonical
    ``core/assets/asset-union.json``), pydantic narrows the
    discriminated-union ValidationError natively at the schema layer —
    constructing the same bad manifest now yields only the 2 missing-field
    errors directly. ``narrow_union_errors`` becomes a pass-through on
    this input.

    This test pins the integration shape: the actionable errors reach
    the adopter without amplification, and ``narrow_union_errors``
    doesn't over-narrow or corrupt already-narrow output. Algorithm-level
    coverage of the narrowing logic itself lives in the synthetic
    ``test_narrow_picks_*`` tests above.
    """
    from pydantic import ValidationError

    from adcp.types import CreativeManifest

    try:
        CreativeManifest(
            creative_id="cr-1",
            format_kind="image",
            assets={
                "hero": {
                    "asset_role": "hero",
                    "asset_type": "image",
                    "url": "https://x.png",
                }
            },
        )
    except ValidationError as exc:
        raw = exc.errors(include_input=False, include_context=False, include_url=False)
        narrowed = narrow_union_errors(raw)
        assert len(narrowed) <= 4, (
            f"too many errors reach adopter: {len(narrowed)} (raw={len(raw)})"
        )
        assert all("image" in err["loc"] for err in narrowed), (
            "errors should localize to the matched 'image' asset variant; "
            f"got: {[err['loc'] for err in narrowed]}"
        )
        missing_fields = {err["loc"][-1] for err in narrowed if err["type"] == "missing"}
        assert "width" in missing_fields and "height" in missing_fields
    else:
        pytest.fail(
            "CreativeManifest accepted invalid asset (missing width/height); "
            "regression in upstream pydantic discriminated-union behavior"
        )


# ---- Expert-review hardening (PR #340 round 2) ----


def test_narrow_handles_union_tag_invalid_as_discriminator_mismatch() -> None:
    """``union_tag_invalid`` is pydantic-2's "tag found but invalid"
    code (sibling of ``union_tag_not_found``). Must be treated as a
    discriminator-mismatch signal so a variant with that error gets
    eliminated from the candidate pool."""
    errors: list[dict[str, Any]] = [
        {
            "type": "missing",
            "loc": ("assets", "hero", "ImageAsset", "width"),
            "msg": "Field required",
        },
        # Invalid tag: pydantic found a discriminator field but its
        # value doesn't match this variant's literal.
        {
            "type": "union_tag_invalid",
            "loc": ("assets", "hero", "VideoAsset"),
            "msg": "Input tag invalid for this union",
        },
    ]
    narrowed = narrow_union_errors(errors)
    # ImageAsset wins — VideoAsset has the discriminator-mismatch signal.
    assert len(narrowed) == 1
    assert "ImageAsset" in narrowed[0]["loc"]


def test_narrow_uses_innermost_variant_for_nested_unions() -> None:
    """Nested unions: ``Union[Outer[Union[A, B]], C]``. Pydantic emits
    ``loc`` like ``("field", "Outer", "inner", "A", "subfield")``.
    The split MUST pick the LAST variant segment (innermost ``A``) so
    A and B end up in different buckets and narrow correctly. Splitting
    at the FIRST variant segment would collapse them and break the
    narrowing."""
    errors: list[dict[str, Any]] = [
        # Inner variant A — clean (no literal_error).
        {
            "type": "missing",
            "loc": ("field", "Outer", "inner", "A", "subfield"),
            "msg": "Field required",
        },
        # Inner variant B — discriminator mismatch.
        {
            "type": "literal_error",
            "loc": ("field", "Outer", "inner", "B", "kind"),
            "msg": "Input should be 'b'",
        },
    ]
    narrowed = narrow_union_errors(errors)
    # A wins; B's literal_error eliminates it from candidates.
    assert len(narrowed) == 1
    assert "A" in narrowed[0]["loc"]
    assert "B" not in narrowed[0]["loc"]


def test_narrow_returns_defensive_copies() -> None:
    """The returned list contains COPIES of the input dicts —
    mutating the returned list MUST NOT affect the input. Cheap
    insurance; matters because pydantic's ``ErrorDetails`` flows from
    user input through a wide call graph."""
    original_err: dict[str, Any] = {
        "type": "missing",
        "loc": ("assets", "hero", "ImageAsset", "width"),
        "msg": "Field required",
    }
    errors = [original_err]
    narrowed = narrow_union_errors(errors)
    # Mutate the returned dict — must not propagate to input.
    narrowed[0]["msg"] = "MUTATED"
    assert original_err["msg"] == "Field required"


def test_narrow_keeps_every_arm_of_a_six_hundred_way_tie() -> None:
    """600 arms, one ``missing`` each, all kept — because they TIE.

    This asserted a DoS cap: above 500 errors narrowing was skipped and the
    input returned unchanged. The cap is gone (salesagent-8qela.75) — it made
    quality degrade exactly when volume was highest, and narrowing measured
    linear at ~4-5us per error, so there was no amplification to guard.

    The length is still 600, which is why the removal did not turn this red:
    it now passes through the TIE path instead of the cap. Every arm has one
    ``missing``, so none gets past its own requiredness, depths are equal, and
    the count sort ties — ``_pick_winning_variant`` returns None and declines
    to guess. Same number, different reason, so the docstring is corrected
    rather than the assertion: a test passing for a mechanism that no longer
    exists is worse than one failing.
    """
    errors: list[dict[str, Any]] = [
        {
            "type": "missing",
            "loc": ("field", f"Variant{i}", "x"),
            "msg": "Field required",
        }
        for i in range(600)
    ]
    narrowed = narrow_union_errors(errors)
    assert len(narrowed) == 600


# ---------------------------------------------------------------------------
# The depth preference, pinned in BOTH directions.
#
# These use models declared HERE rather than SDK types, deliberately. The
# existing coverage of union narrowing went through generated request models,
# and the emitter change that collapsed a split root's branches took the
# behaviour out from under it -- 275 items could then no longer reach the
# preference at all, and a sweep concluded it had nothing to decide. An
# adopter-shaped fixture cannot go stale that way, and it is the path the
# module's own docstring names: "Adopter code via narrow_validation_error ...
# for adopters who construct typed models in their platform method bodies".
# ---------------------------------------------------------------------------


class ArmInner(BaseModel):
    need: int


class ShallowArm(BaseModel):
    kind: str


class DeepArm(BaseModel):
    kind: str
    inner: ArmInner


class ShallowArmHolder(BaseModel):
    choice: ShallowArm | DeepArm


class TiedArmA(BaseModel):
    value: int


class TiedArmB(BaseModel):
    value: int


class TiedHolder(BaseModel):
    choice: TiedArmA | TiedArmB


def _errors_of(model: type[BaseModel], payload: dict[str, Any]) -> list[Any]:
    with pytest.raises(ValidationError) as raised:
        model.model_validate(payload)
    return raised.value.errors(include_input=False, include_context=False, include_url=False)


def test_equal_depth_arms_both_survive() -> None:
    """Arms that fail at the SAME depth are not separable, so neither is dropped.

    The document gives no signal about which arm was meant — both declare
    ``value`` and both reject the same way — so narrowing declines to guess.
    This is the invariant against over-narrowing.
    """
    errors = _errors_of(TiedHolder, {"choice": {"value": "not-an-int"}})
    narrowed = narrow_union_errors(errors)

    assert len(narrowed) == 2
    assert {tuple(e["loc"])[-1] for e in narrowed} == {"value"}


def test_depth_differing_arms_keep_only_the_deeper_one() -> None:
    """Arms that reach DIFFERENT depths are separable, and the deeper one wins.

    This asserts a DROP on purpose, which is why it is spelled out: the arm
    discarded is the one the buyer did NOT select, and keeping it would bury
    the error they will actually hit.

    The document carries ``inner``, a key only ``DeepArm`` declares, so ``DeepArm``
    is the arm that was meant. It reports two errors (``kind`` wrong type and
    ``inner.need`` missing) at depth 4; ``ShallowArm`` reports one (``kind``) at
    depth 3. Counting errors would pick ``ShallowArm`` — fewest — and tell the
    buyer only about ``kind``, hiding ``inner.need`` until they fixed ``kind``
    and resubmitted. That is worse than not narrowing at all, and it is what
    the depth preference exists to prevent.

    Equal depth is the tie covered above; differing depth is evidence the arms
    are not equivalent, so dropping one here does not weaken that invariant.
    """
    errors = _errors_of(ShallowArmHolder, {"choice": {"kind": 5, "inner": {}}})
    narrowed = narrow_union_errors(errors)

    kept_paths = {tuple(str(part) for part in e["loc"]) for e in narrowed}
    assert all("ShallowArm" not in path for path in kept_paths), kept_paths
    # The error a count-based rule would have hidden.
    assert any(path[-1] == "need" for path in kept_paths), kept_paths
    assert len(narrowed) == 2
