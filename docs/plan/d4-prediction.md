# D4 prediction, written before any measurement of the rewritten decision

Written at base `b2fc850da` on `emit/d4-strict-validate`, after reading D4 as
rewritten at `b339d1692`, `tests/test_d4_no_per_field_null_validator.py`,
`codegen/emit.py`, `codegen/harness.py`, `codegen/adapter.py` and
`src/adcp/types/_base.py`, and **before** changing or re-emitting anything.

Starting state measured: 3 failed, 42 passed; N = 34 bindings, 51 refusals, 85
leaves, 1,054 portable.

## The three predictions

1. **N stays 34 of 1,054 portable, 51 of 85 leaves refused.** Dropping the
   `Absent[...]` wrapper changes the TEXT of an annotation already being
   produced. It touches no `Refusal` site: `_check_keywords`, the type dispatch
   in `annotation`, and `lower_object`'s guards are all upstream of the wrap and
   none of them reads the wrap's result. So no document that is lowered today
   can start refusing and no document that refuses today can start emitting.
2. **No module stops emitting.** Same reasoning. What DOES change in every
   module carrying an optional non-nullable property: the `Absent` import
   disappears and each such annotation loses one layer. A module whose only
   non-stdlib import was `Absent` keeps `AdCPBaseModel`, so no import group
   empties out.
3. **Deleting the 52-property nullability instrument loses no coverage of
   D4's obligation, and does lose a measurement of the model alone.** The
   obligation ("an optional property is absent or valid, never null") moves to
   `strict_validate`, where the schema half refuses the null on `type` — so the
   obligation is graded, and graded for EVERY keyword rather than for
   nullability only. What stops being graded is the emitted model's own accepted
   set: after the change `PaginationRequest.model_validate({"cursor": None})`
   succeeds, and nothing fails because of it. That is the decision, not a
   regression, but it is a real loss of a measurement and I expect to report it.

## A consequence I expect to have to report

Grading direction 2 through `strict_validate` makes direction 2
**schema-answered**. `check_refuses` only asserts a refusal once
`violated_keywords(original, instance)` is non-empty, and `strict_validate`
validates against that same document with the same library — so the refusal
follows from the control. After this change direction 2 grades the accepted set
of `strict_validate` (which is the stated obligation) and no longer grades the
emitted model's own refusals at all; direction 1 is the only remaining check
that the model is not NARROWER than its document.
