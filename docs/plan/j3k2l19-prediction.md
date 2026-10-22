# `salesagent-j3k2l.19` — emit `uniqueItems`, and grade it

Written before the change and committed before it. Started from
`00c7dd4d4` (`emit/from-scratch`), clean. Every number below is over
`schemas/cache/3.2`, excluding `bundled/` and `mcp/` — **1,054 portable
documents**.

## 1. The population, measured rather than taken from the ticket

The ticket says 48 refusals and the brief says the tip census reads 56.
**Neither reproduces on this tree.** Re-measured with
`emit.emit(BUNDLE, bundle.portable(BUNDLE))`:

| | count | denominator |
|---|---|---|
| portable documents | 1,054 | the bundle |
| emitted | 401 | 1,054 |
| refused | 653 | 1,054 |
| refused on `uniqueItems` | **49** | 1,054 |
| refused on `uniqueItems` over the step population (981 named) | 47 | 981 |

So the figure the ticket's exit condition is stated over is **49**, and the
47 the committed suite asserts is the same set narrowed to the step's own
named population. The keyword itself is everywhere: **485 sites in 198
documents** (the step census counts 462 stepped sites in the same 198,
because two of the nine older steps `pop` the keyword to stay satisfiable).

## 2. The partition, because the unit is not assumed

`ROWS` dispatches on root kind. The 49 do not sit at one kind, so the
partition decides the unit.

**By the row that claims the document** (denominator 49):

| row | documents |
|---|---|
| `is_object_root` | 39 |
| `union_root` | 5 |
| `is_container_root` | 4 |
| `composes_at_the_root` | 1 |

**By where the refusing node SITS** (denominator 49):

| position | documents |
|---|---|
| an array at a `properties/<name>` slot | 45 |
| the document root (a root array) | 4 |

And over all 485 sites in the bundle, by containing slot:

| slot | sites |
|---|---|
| `properties` | 467 |
| `additionalProperties` (a mapping value) | 6 |
| the document root | 4 |
| a `oneOf`/`anyOf` branch index | 4 |
| `definitions` / `$defs` | 4 |

**So this is not one dispatch row, and it is not a row at all.** 467 of 485
sites are an array held by a class, which is exactly what D2 says:
`uniqueItems` → *a rule on the nearest class*. The keyword never appears at a
root kind `ROWS` could dispatch on except as a root array, which is already
`is_container_root`'s. `ROWS` stays at six and `codegen/bundle.py` is not
touched: `bundle.is_leaf_object` already admits a document whose only extra
keyword is `uniqueItems` (its own docstring says so), so every one of the 45
is already selected by a row.

## 3. The form: measured, then chosen

### A `set` is refuted by measurement, three times over

| probe | result |
|---|---|
| `set[str]`'s rendered schema | `{"type": "array", "items": {...}, "uniqueItems": true}` — matches the document exactly |
| `set[str]` given `["a", "a"]` | **accepted**, silently deduped to `{"a"}` |
| `set[Inner]` given `[{"a": "1"}]` | **refused**, `set_item_not_hashable` — every instance |
| `set[str]` round trip of six strings | `['v', 'x', 'u', 'z', 'y', 'w']` — order is lost |

The rendering is the only half that works. A `set` **accepts what the
document refuses** and changes the value while doing it, which is the
widening this pipeline exists to remove; and it refuses every instance at the
13 object-item and the object-valued `$ref`-item sites, which the accepts
check would report. It is out.

### A rule in step 7's existing D6 family, with the fact rendered

D6 already names `uniqueItems` as one of its six families, so the form is
decided: a frozen dataclass in `_adcp_rules`, read by the one
`model_validator(mode="after")` in `src/adcp/types/_runtime.py`.
`_runtime.py`'s docstring promises exactly this — *"adding a rule kind adds a
dataclass and renames nothing"*.

One thing D6 and §6 do not agree about, and it is the whole of the
difficulty: **`uniqueItems` is the ONE keyword of D6's six that
`harness.FACTS` compares.** `minProperties`, `maxProperties`, `dependencies`,
`oneOf`, `anyOf`, `if` and `not` are not in `FACTS` at all, so a rule-borne
fact is invisible to the comparison for the other five families. For this one
the document states `uniqueItems: true` and a `list[X]` annotation states
nothing, so the comparison reports `missing` — `model_drops_a_fact` — at
every one of the 45.

The channel for that already exists and is used for the same reason.
`compiler._field` writes `extras["json_schema_extra"] = {"format": ...}` for
a `format` that selected no type, and `Property.format`'s own docstring says
why: *"it rides as `json_schema_extra` so the fact reaches the model's schema
where the comparison grades it."* A `uniqueItems` the rule enforces is the
same case and a stronger one — the schema half enforces it, and so does the
constructor — so the rendered fact is TRUE of the model rather than excused.

**No comparison row is added.** `added` stays 0 because the fact is rendered
only where the document states it, and `missing` stays 0 because it is
rendered there.

## 4. The change, in the design's own pieces

One reader, the existing carriers, no new mechanism.

* `codegen/lower/rules.py` — one more reduction, `_distinct`, reading the
  object node's own `properties` exactly as `conditional_properties` reads its
  `if`/`then`/`else`. It appends `UniqueItems('<key>')` and names the key on a
  new `Lowered.distinct`.
* `codegen/compiler.py` — `fields(..., distinct=)`, a fourth keyword argument
  in the spirit of the three that are there, strips `uniqueItems` off those
  declarations before `mod.decide` sees them and sets a new
  `Property.distinct`; `_field` renders it through the existing
  `json_schema_extra` channel; `lower_object` passes `stated.distinct`.
* `src/adcp/types/_runtime.py` — one `UniqueItems` dataclass.

**`codegen/lower/containers.py`'s screen is untouched**, and that is the
decision rather than an omission: an array with no class above it — a mapping
value, a root, a combinator branch — keeps refusing on `uniqueItems` by name,
which is the true reason (D6's rule has nowhere to live). Admitting the
keyword in `array()` instead would move the 4 root arrays onto D2's
unimplemented `RootModel[list[X]]` row and falsify that row's recorded
justification, for no document gained.

## 5. The prediction

Taken from a probe that strips `uniqueItems` at every `properties/<name>`
array slot and re-emits (`scratchpad/j19/probe.py`), corrected for
`product.lower_root` writing no D6 rule at all, which my change does not
alter.

| # | prediction |
|---|---|
| P1 | The population is **49** over 1,054 — not 48 and not 56. |
| P2 | **19 of the 49 emit.** |
| P3 | **24 of the 49 refuse on another step's keyword**: `$ref` 17, `allOf` 4, `minProperties` 1, `anyOf` 1, `const` 1, `oneOf` 1 — minus the one that moves to `$ref` only if the composing root is covered, which it is not. So 16 `$ref` + 4 `allOf` + 1 each of the other four = 24. |
| P4 | **6 of the 49 still refuse on `uniqueItems`**, by name, pointer and keyword: the 4 root arrays (D2's `RootModel` row), `core/account-authorization.json` at `/properties/field_scopes/additionalProperties` (a mapping value — no class), and `media-buy/list-creative-formats-request.json` (a composing root — `product.lower_root` writes no rule of any family). |
| P5 | N over the whole portable population rises **401 → 425 ± 2** (the probe measured 426 with the composing root also covered). |
| P6 | Emitted modules in the committed tree rise from **390**, and the graded-pair count rises from **462**. Both re-measured, not predicted to a number. |
| P7 | The comparison stays at **`added` 0, `missing` 0, `differs` 0** over every pair. |
| P8 | `ROWS` stays at **six** and `codegen/bundle.py` is unchanged. |
| P9 | The step census is unchanged — `uniqueItems` stays `(462, 198)` — because it is read over the bundle and not over the tree. |
| P10 | `test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` changes: its `carried == []` half becomes false. Its replacement asserts both directions still — the keyword is stepped, AND every site the tree now carries is on a class whose `_adcp_rules` holds a `UniqueItems` for that field, with `model_validate` refusing a duplicate there. |
| P11 | A seventh rule kind makes `RULE_KIND_POPULATION`'s `len(measured) == 6` and `seen == set(RULE_KIND_POPULATION)` false; both are extended to the new kind's own population (object nodes with an array property stating `uniqueItems: true`), not relaxed. |

## 6. The ceilings this accepts, named

* **O(n²) pairwise comparison, not a hash set.** An item can be a pydantic
  model or a `dict`, and neither is hashable — which is the same measurement
  that refutes `set`. The arrays in this bundle are small; the upgrade path is
  a hash set behind an `isinstance` test, not a weaker comparison.
* **`true` and `1`.** draft-07 says they are different values and Python says
  `True == 1`, so the comparison tests `isinstance(x, bool)` on both sides
  before `==`. That is three lines and it is the only conflation Python has
  here.
* **The rule narrows the constructor and nothing else** (D6). Acceptance is
  `strict_validate`'s, which refuses a duplicate whether or not a rule exists.
  So the rule is observable only through a direct `model_validate`, which is
  where its test goes.
* **An array at a root or a `definitions` node gets no rule even once D2's
  `RootModel` row exists**, because an alias has no constructor to narrow.
  Nothing is lost: the schema half still refuses.

## 7. Grading against this prediction

Filled in after the measurement, in this file, in a commit of its own.
