# Step 4's prediction, written before the lowering exists

Branch `emit/s4-product-v2`, base `81e132aee` with `emit/format-regex` merged (`482e7bc63`).
Nothing below is measured yet. Graded in the note at the end of the step; both halves kept.

## 0. What the base does NOT have, and what that costs

The brief says the only shared edit is "one row in the dispatch table in `codegen/emit.py`".
**There is no dispatch table on this base, and no `codegen/lower/` package.** `git log --all
--diff-filter=A -- 'codegen/lower/*'` finds it added on six lane branches
(`emit/s3-enum`, `emit/s4-product`, `emit/s5-union`, `emit/s6-containers`, `emit/s7-rules`
and the v1 foundation `77c8e1c0d`), none of which is an ancestor of `81e132aee`. The four
sibling v2 branches are all sitting at `482e7bc63` with no commits of their own, so none has
built it either.

So this step delivers the table as well, in its own behaviour-neutral commit, exactly as the
v1 lane did. **Prediction: the foundation commit changes no emitted byte** — 43 modules
identical, N unchanged, the table empty, and the full suite green at that commit with
`codegen/lower/` holding nothing but the table.

## 1. The population

**287 documents**: a root carrying `allOf` with no `oneOf`/`anyOf` beside it. A union root is
step 5's row whatever else it carries. Predicted exactly, carried from the v1 measurement on
this same bundle (`schemas/cache/3.2`, untouched since), and asserted in the suite before any
verdict is read off it. The competing readings predicted to land at 342 (any `allOf`
anywhere), 257 (`allOf` nowhere but the root) and 279 (root `allOf` with root `properties`).

## 2. ΔN

**ΔN = 0. N stays 43 of 1,054.** The plan's step table implies the volume of the composing
population; the v1 lane predicted +19 and measured 0. Predicting 0 again, for the reason v1
measured rather than for caution: 213 of the 287 carry a keyword of their own that steps 3, 6
and 7 lower, and the other 74 lose a reference — 47 of them a BASE — to a cascade six
documents root-cause (`core/protocol-envelope.json`, `core/account-ref.json`,
`core/context.json`, `core/compact-task-input-required.json`, `core/delivery-metrics.json`,
`formats/canonical/_base.json`).

A specific risk against that: `emit/format-regex` landed since v1 measured, and it makes
`format` select a type. It never made a format refuse, so it is predicted to move no document
from refused to emitted. If ΔN comes back non-zero, the cause is predicted to be format and
not `allOf`.

**Refusal attribution is predicted to MOVE for 4 documents** —
`core/creative-manifest.json`, `core/forecast-dimension-signal.json`,
`core/product-format-declaration.json`, `core/signal-listing.json` — each carrying a union
BESIDE its `allOf`, so this row's selector declines them and the default object lowering
reports them on `allOf` instead of on the keyword a chain would have reached first. That is a
changed keyword, not a changed verdict.

## 3. What the lowering does

- A conjunct that is a `$ref` and nothing else is a BASE (D7).
- A conjunct carrying `properties` declares fields of this node.
- A `required`-only conjunct is **not built**: predicted 0 occurrences at a root bundle-wide,
  so the arm would be a derivation matching nothing.
- Anything else refuses by name, pointer and keyword.

**A subclass never restates an inherited field.** A restatement is admitted only when it
NARROWS — keeps every keyword the inherited declaration states with the same value, and adds
at least one. Symmetric, so no last-wins. Predicted over the 287: ~100 restatement sites,
~51 identical, ~31 annotation-only (the shadow), ~16 a `$ref` into a fragment, ~2 narrowing.

## 4. The checks, and what the probe has to be

Predicted, from the v1 measurement, and this is the part a reader should disbelieve until it
is re-measured here: **the accepts and refuses checks do NOT catch the shadow.** They call
`strict_validate`, whose schema half decides before anything is constructed, so a class
carrying `Any = None` over a typed base field grades identically to a faithful one, and so
does a class with no bases at all. Predicting `check_pair` green in both directions for the
shadowed rendering.

So the control asserts on `model_validate`, which builds without consulting the schema:
with the shadow, `model_validate({"adcp_major_version": 0})` is predicted ACCEPTED; without
it, refused by the inherited `ge=1`.

The mechanism is graded on a three-document probe bundle, one document of which is this
bundle's own `core/version-envelope.json` copied byte for byte, so the inherited `ge=1, le=99`
is the bundle's text and not the test's idea of it.

## 5. The perturbations, and what each is predicted to redden

1. **Always restate an inherited field** → the inherited bound is gone:
   `model_validate({"adcp_major_version": 0})` accepted. Predicted to redden the control's
   inheritance assertion and nothing else.
2. **Bind no base** (drop the `$ref` conjunct arm) → the composed field set collapses to the
   node's own properties. Predicted to redden a field-count assertion.
3. **Copy the base's constraints into the subclass** → `ge=1` appears a second time in the
   module text. Predicted to redden P2's no-second-spelling assertion.
4. **Unregister the row** → the composing document is no longer emitted at all. Predicted to
   redden the emission assertion.

Each must redden something SPECIFIC. A perturbation that reddens nothing is a finding about
the instrument, and is reported as one.

## 6. The floor

43 emitted modules and every passing pair are the floor. Predicted: no module's text changes
at either commit, and the suite's count goes from 72 up, never down.
