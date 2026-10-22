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
