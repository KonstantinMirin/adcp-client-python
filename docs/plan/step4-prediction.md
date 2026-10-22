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

---

# The grade, written after measuring. Branch tip `8fc31f127`.

| § | predicted | measured | verdict |
|---|---|---|---|
| 0 | no dispatch table on the base; the foundation changes no emitted byte | confirmed; `git rev-parse <sha>:src` identical at `9db08a2ab` and at the base | **right** |
| 1 | population 287; the others 342 / 401 / 257 | 287; 342, 401, 257 | **right** |
| 2 | ΔN = 0, N = 43 of 1,054 | ΔN = 0, N = 43 of 1,054 | **right** |
| 2 | `emit/format-regex` moves no document from refused to emitted | confirmed: the emitted set is identical with and without the row | **right** |
| 2 | 4 documents change refusal keyword | **286 of 287 did** | **wrong, and the prediction named the wrong comparison** |
| 3 | 0 `required`-only conjuncts at a root | 0 | **right** |
| 3 | ~100 restatement sites: ~51 / ~31 / ~16 / ~2 | 100 sites in 61 documents: 51 identical, 31 annotation-only, 12 a `$ref`, 4 incompatible, 2 narrowing | **right on 100 / 51 / 31 / 2; wrong on the `$ref` arm** |
| 4 | checks 1 and 2 do not catch the shadow; the control belongs on `model_validate` | confirmed by perturbation 1: `model_validate({"adcp_major_version": 0})` accepted with the shadow, refused without | **right** |
| 5 | four perturbations, each reddening something specific | five run; one of the four was not distinct | **mostly right** |
| 6 | no module's text changes; the suite goes 72 → up | `src/` tree hash unchanged; 72 → 91; 44 pairs still pass | **right** |

## Where it was wrong, and what the right number is

**"4 documents change refusal keyword" named a comparison this branch does not make.** That
4 came from a v1 measurement of *table dispatch against an if/elif chain*, both of which had
the lowering. The comparison available here is *with the row against without it*, and against
that **286 of the 287 move** — from `allOf` or `type` at the root, which is "the first keyword
the lowering that ran does not handle", to the keyword that actually stopped it inside a
conjunct or in a document it composes. No verdict moved: no document stopped refusing, none
started, and refusals over the 587-document population went 582 → 596, the 14 new ones being
documents reached for the first time through a conjunct's `$ref`. Carrying a number forward
without re-deriving which two states it compares is how a correct measurement becomes a wrong
claim.

**The `$ref`-into-a-fragment arm is 12, not 16, and the residue is 4 incompatible
restatements.** The prediction put ~0 on the incompatible arm, which would have made that arm
a guard rather than a measured behaviour. It has a population of 4.

**Perturbation 2 as predicted was not distinct from perturbation 1.** "Bind no base" was
written as "record no inherited shape", which reddens the same two assertions the
always-restate perturbation does, because the class still subclasses its bases through Python
and only forgets what it inherits. The distinct perturbation is to append no base at all
(P2b below), which reddens two more.

## The five perturbations, and what each reddened

Each was applied with file tools and reversed with file tools; `git status --short` and
`git diff --stat` are both empty afterwards and the suite is back at 91.

| # | perturbation | reddened |
|---|---|---|
| 1 | always keep a restatement (`own[key] = node` unconditionally) | `test_a_subclass_never_restates_an_inherited_field`, `test_the_inherited_bound_is_live_on_the_model_validate_path` — `model_validate({"adcp_major_version": 0})` ACCEPTED |
| 2 | bind the base, record no inherited shape | the same two. **Not a distinct perturbation**, and that is a finding about the test set: the class still inherits through Python and only forgets what it inherits, which is the same defect as 1 in another spelling |
| 2b | resolve the conjunct, append no base | 4: the two above plus `test_a_ref_conjunct_becomes_a_base_in_the_documents_own_conjunct_order` and `test_the_composed_field_set_is_the_union_and_requiredness_is_inherited` |
| 3 | merge the base's own constraints into the restatement | `test_a_subclass_never_restates_an_inherited_field`. Measured on the module text: `ge=1` and `le=99` appear a SECOND time, in the subclass |
| 4 | unregister the row | 8 of 19 |
| 5 | drop the union clause from the selector | 4, across both test modules: this step's population reads 342 and `test_the_union_clause_is_what_keeps_the_rows_disjoint` fails on the 55 documents it would then share with step 5 |

Perturbation 3 is also the measurement behind the report-and-stop below: its rendering
RECOVERS the `default` and the restated `description` that the merge rule drops, at the price
of a second spelling of the base's bound. The two rules are in genuine tension and the
comparison is what reveals it.
