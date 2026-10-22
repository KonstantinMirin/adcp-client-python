# Step 1 prediction, written before the spine was measured

Committed before any of it was built, so the grade below is a grade and not a
recollection.  Written at `028447726`, against `docs/plan/rebuild-plan.md` §1-§5.

## The scope I am predicting over

The rebuild plan's step-1 row names ONE document, `core/pagination-request.json`.
The tree at this base holds 43 emitted modules, because step 2 (a cross-document
`$ref` is an import) is already merged at `11a9b2828` and its documents are in
the committed population.  Replacing the renderer for one document and leaving 42
on the old text emitter would put two renderers in the tree, so I predict I will
move the whole committed population across and keep the population derivation
exactly as it is: 1,054 portable, 85 leaf objects, 249 referencing a property,
334 named, 43 emitted, 331 refused.

## N

**N stays 43.**  The walk's refusal rules are what select the population and I am
not touching them — only the text generation moves.  A document that lowered
before lowers now.

The risk that would move it: the compiler refuses to render something the text
emitter wrote by hand.  The two candidates are the `alias=` spelling for a
property key Python cannot carry (`core/truncation-sentinel.json`'s
`_truncation`) and the root-scalar alias, which is not a class at all and so has
no model for the compiler to render.  I predict the alias module stays ours (§1
already says a module-level statement beside an alias has no slot in any
compiler template) and that the `alias=` field renders through
`DataModelField.alias`.

## What leg 3 catches that legs 1 and 2 cannot

Legs 1 and 2 go through `strict_validate`, whose schema half answers first, so
they grade the entry point and not the annotations.  I predict leg 3 goes red on
the tree as committed at this base, on exactly two fact classes:

- **3 dropped defaults.**  3 sites across the 43 documents carry `default`, and
  `ANNOTATIONS` in the old emitter lists `default` as read-and-not-transcribed.
- **142 dropped descriptions.**  142 nodes across the 43 documents carry
  `description`; the old emitter carries a description only for an object node,
  as the class docstring, so every property-level one is dropped.

I predict leg 3 finds NOTHING else on this population: types, formats and the
eight scalar constraints were already carried, and `additionalProperties` →
`extra` was already derived.

I also predict leg 3 is the only leg that moves when a constraint is widened,
because that is the measurement the plan records (`Any` on every field grades
green in both directions with a direction-2 denominator of 0).

## Whether the two gates bite differently than stated

No.  I reproduced both before writing this, on dmcg 0.86.0:
`Constraints(ge=1, le=100).model_fields_set` is empty and
`Constraints(minimum=1, maximum=100)` renders `Field(ge=1, le=100)`.  I predict
one gate the brief does not name will bite: **`class_body_lines` is reserved**.
`extra_template_data` refuses the key outright (`Error: class_body_lines is
reserved for generator-owned built-in template data`), so the `__adcp_schema__`
line reaches the class body only through `_append_internal_template_data`, which
is dmcg-private, or through a vendored template.  I predict I use the private
method and that a dmcg upgrade dropping it fails loudly rather than silently,
because a class with no `__adcp_schema__` cannot be graded at all.

## The perturbations, and what I predict each reddens

| perturbation | prediction |
|---|---|
| widen `ge=1, le=100` off `max_results` | leg 3 only.  Legs 1 and 2 stay green. |
| drop `default: 50` | leg 3 only. |
| drop both descriptions | leg 3 only. |
| point `__adcp_schema__` at another document | all three legs. |
| delete the `extra="forbid"` config | leg 2 (`additionalProperties` step) and leg 3. |
| `Any` on every field | leg 3 only, which is why leg 3 exists. |

## Leg 3's soundness, predicted before implementing it

I predict `model_json_schema()` is NOT directly comparable to the source
document and that a normalization step is required, on three keywords:

1. **`anyOf` with a `null` arm.**  D4 renders an optional `T | None`, so pydantic
   emits `{"anyOf": [{...T...}, {"type": "null"}], "default": ..., "description":
   ...}` where the document emits `{...T..., "default": ..., "description": ...}`.
   This is forced by our own rendering decision, not by pydantic.
2. **`$ref` into `$defs`.**  A referencing module imports its target's symbol, so
   the model's schema carries `{"$ref": "#/$defs/X"}` with the facts under
   `$defs`, while the document (resolved at emit time) carries them inline.
3. **`title`.**  pydantic derives a title for the class and for every property;
   the documents carry one only at the root.

I predict the comparison therefore runs one direction — every constraint fact
the DOCUMENT states, the model states at the corresponding position — and that
the reverse direction needs no leg because direction 1 already fails a model
narrower than its document.

---

# The grade, written after

Measured at `8aa308a21`.  Each row says what the prediction was and what the
measurement says.  Both are kept; nothing above was edited.

## Scope and N — RIGHT

The whole committed population moved across, the population derivation is
untouched, and **N = 43 documents emitted, 331 refused, over 334 named**, with
the refusal keyword histogram identical to the text emitter's (`$ref` 68, `enum`
67, `type` 61, `const` 51, `allOf` 39, `not` 13, `anyOf` 8, `minProperties` 6,
`dependencies` 6, `definitions` 5, `oneOf` 4, `if` 2, `required` 1).  The walk
selects the population and the walk did not change, so nothing moved.

The two risks I named did not bite: `alias=` renders through
`DataModelField.alias` and the root-scalar alias is written by the module writer
around the compiler's own field rendering.

## What leg 3 catches — RIGHT on the two classes, and it found two more

Predicted: 3 dropped defaults and 142 dropped property descriptions, and nothing
else.  Measured on the tree as committed at the base, leg 3 is red on **8 of 44
pairs**, over four fact classes rather than two:

| dropped fact | sites | predicted |
|---|---|---|
| `default` | 3 (2 documents) | yes |
| property `description` | 142 nodes | yes |
| root `description` on a scalar-root ALIAS | 5 documents | no |
| `format` beside a `pattern` | 1 (`core/platform-extension-ref.json`'s `uri`) | no |

The two I missed are the two where there was nowhere obvious to put the fact: an
`Annotated` alias has no docstring slot (it has a `Field(description=...)`), and
a `format` whose Python type the walk declines to use because a constraint sits
beside it has no type to carry it (it has `json_schema_extra`).  Both are now
carried and both are graded.

## The blindness measurement — WRONG, and the correction is the finding

Predicted, from the plan's §4: a widened model passes legs 1 and 2 **with a
direction-2 denominator of 0**, so a zero-denominator rule would catch it.

Measured, in one process, both entry points side by side
(`test_leg_3_grades_the_generated_code_and_the_acceptance_legs_do_not`):

| model | entry point | direction 1 | direction 2 | denominator |
|---|---|---|---|---|
| faithful | production `strict_validate` | pass | pass ×3 | **75** |
| `Any` everywhere | production `strict_validate` | pass | pass ×3 | **75** |
| faithful | the probe's hand-rolled strict | pass | harness_error ×3 | **0** |
| `Any` everywhere | the probe's hand-rolled strict | pass | harness_error ×3 | **0** |
| faithful | annotations only | pass | pass ×3 | 75 |
| `Any` everywhere | annotations only | pass | **model_accepted_invalid ×2** | 75 |

The `0` is a property of the probe's wrapper, not of the model: it raises
`jsonschema.ValidationError`, which `check_refuses` does not catch, so every step
reports `harness_error` -- and the probe's verdict read `accepted_invalid == 0` as
green.  The faithful model scores the same `0` through it.

So the blindness is **worse** than §4 states: through the production entry point
a wide model and a faithful one are graded identically, over the same 75
instances, and no denominator rule separates them.  Leg 3 is the only thing that
does.  The zero-denominator rule is still right and is still structural
(`PairReport.outcome` never returns `pass` for one), but it is not the guard
against a widening -- it is the guard against a pair nothing reached, and it is
graded on an entry point that raises a foreign exception, which is the one thing
that actually produces a zero.

## The two gates — RIGHT, and the third one bit as predicted

Both gates are as the brief states them, reproduced on dmcg 0.86.0 before any
code was written.  `class_body_lines` is reserved, as predicted, and the
`__adcp_schema__` line goes through `_append_internal_template_data`.

Two gates the prediction did not name:

- **`is_custom_type` buys an unasked-for config.**  A local symbol handed over as
  a custom type makes dmcg add `arbitrary_types_allowed=True` to the class's
  `ConfigDict`.  A local symbol is a `Reference` to another model, which is what
  it actually is, and the relaxation goes away.
- **dmcg renders a config of its own.**  A class with a look-around `pattern`
  gets `regex_engine="python-re"`, independently reaching the decision
  `AdCPBaseModel` makes.  The import filter has to read the rendered text rather
  than the config we asked for; deciding it from the argument left
  `core/sla-window.json` one perturbation away from a `NameError` (fixed at
  `8aa308a21`).

## The perturbations — one row wrong

| perturbation | predicted | measured |
|---|---|---|
| widen `ge=1, le=100` (drop `minimum`) | leg 3 only | **leg 3 only**, on 13 pairs; legs 1-2 green |
| drop `default: 50` | leg 3 only | **leg 3 only**, on the 2 documents that carry one |
| drop every property `description` | leg 3 only | **leg 3 only**, on 38 of 44 pairs |
| point `__adcp_schema__` at another document | all three legs | **direction 1 on 35 pairs, leg 3 on 7**; 53 tests red |
| delete the `extra` derivation | direction 2 and leg 3 | **leg 3 only**, on 38 pairs -- WRONG |
| `Any` on every field | leg 3 only | leg 3 only (above) |
| drop every `pattern` | not predicted | leg 3; direction 2 only through the annotations |
| drop the `format` annotation | not predicted | leg 3, on its 1 site |
| no `__adcp_schema__` at all | not predicted | 10 named tests red, every pair gone |
| plant a stale module | not predicted | the tree compare |

The wrong row is instructive: I expected direction 2's
`additionalProperties false -> an extra property` step to catch a model that
forgot `extra="forbid"`.  It does not, for the same reason the wide model passes
-- `strict_validate` asks the document first and the document forbids the key, so
the model is never asked.  That is a third independent instance of the same
blindness.

No perturbation was inert.

## Leg 3's soundness — RIGHT, and the normalization list is exactly the three

`model_json_schema()` is not directly comparable and needs normalization on the
three keywords predicted, each forced by a decision this pipeline made:

1. **`anyOf` with a `null` arm** -- D4 renders an optional `T | None`, so the
   type facts sit inside the union and `default` / `description` outside it.
   Unwrapped only for a two-member union with exactly one `null` arm, so a
   document that genuinely admits null (a later step's row) is not flattened.
2. **`$ref` into `$defs`** -- a nested class and an imported target are both
   hoisted by pydantic; the document is resolved, so the facts are inline there.
3. **`title`** -- pydantic derives one per class and per property; the documents
   carry one only at a root.  Not compared, because it is a name the compiler
   makes up rather than a fact about a value.

A fourth was needed and was not predicted: **`additionalProperties: false`
becomes `{"not": {}}`** in a document with references, because the resolver
(`hypothesis_jsonschema`'s, used deliberately so the runtime and the harness
decide with the same schema) canonicalizes while inlining.  One site,
`core/operator-identity.json`'s `operator_unit`.  The two forms refuse the same
instances, so it is folded out in `harness._closed`.

Direction: one, document -> model.  The reverse needs no leg, as predicted --
direction 1 generates an instance the schema admits and a narrower annotation
refuses it there.
