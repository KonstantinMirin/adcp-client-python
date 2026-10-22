# Step 5 prediction, written before the lowering exists

Branch `emit/s5-union-v2`, worktree `/Users/konst/projects/acp-s5`, tip at the time of
writing **`482e7bc63`** (base `81e132aee` + the `emit/format-regex` merge, which
fast-forwarded). Venv built in this worktree with
`env -u VIRTUAL_ENV uv sync --all-extras`; every number below was taken with
`env -u VIRTUAL_ENV uv run --no-sync`.

`codegen/lower/union.py` does not exist yet, and neither does the dispatch table it needs
a row in. Nothing here is graded against an implementation, because there is none.

## The baseline, measured

| fact | value | how |
|---|---|---|
| bundle size | 1,054 | `len(bundle.portable(BUNDLE))` |
| N emitted | **43** | `len(emit.emit(BUNDLE, population()).emitted)`, in process, no `write` |
| refused | 331 of the 334 named | same run |
| graded pairs | 44 | `tests/test_emit.py::test_the_step_result_is_counted_over_the_whole_population` |
| pairs `pass` / `no_constraint_to_step` | 42 / 2 | same |
| suite | **72 passed** | `pytest tests/ -q` after the merge |

44 pairs over 43 documents, because one document carries a nested class.

## The population, measured, and how it is selected

**156 union roots**: a document whose ROOT carries `oneOf` or `anyOf` as a list. 0 carry
both. That is the selector this step's dispatch row uses, and it is the whole of the
step's population test.

The denominator for every count below is 156, out of the bundle's 1,054.

**Two selector collisions exist today and the prediction is that the table must make them
disjoint rather than ordered:**

- `bundle.references_a_property` (step 2's NAMING population) is true of 11 of the 156.
  That selector decides which documents the committed tree's command NAMES, not which
  lowering handles one, so it is not a dispatch row and I predict it needs no change.
- `emit.lower_document`'s own shape branch — `"properties" in doc and kind in (None,
  "object")` — IS the current dispatch, and it is true of **88** of the 156. So the
  existing row has to be narrowed to exclude a root carrying a union keyword, or the
  table has two rows claiming 88 documents. I predict narrowing it is the whole of the
  change to the existing row, and that it moves no emitted module: a union root reaching
  `lower_object` today refuses at `oneOf`, and under my row it refuses (or emits) under
  my own keywords.

### What blocks each of the 156, by first blocker, measured off the bundle

Screened on the root's and each branch's live keyword set (live = not an annotation, not
`x-`), against what §4's shape can carry.

| first blocker | count |
|---|---|
| root `allOf` (step 4) | 55 |
| **passes the keyword screen** | **44** |
| branch is `required`-only (step 7's rule) | 13 |
| branch `allOf` (step 4) | 10 |
| branch `not` | 8 |
| root `definitions` | 7 |
| root `not` | 6 |
| branch `anyOf` (a nested union) | 3 |
| root `if` | 2 |
| branch `enum` | 2 |
| root `$defs` | 2 |
| root `dependencies` / root `type` / root `enumMetadata` / branch `const` | 1 each |

Of those 44: **5 carry at least one bare-`$ref` branch**, **4 carry root `properties`**
(disjoint sets), leaving **35** that are a union of the root's own object nodes with no
root properties.

## What I predict

### 1. ΔN

**N = 53 of 1,054, so ΔN = +10 against the base's 43.** Interval: +6 to +14.

The 35 clean candidates are screened again by things this census did not look at — D3 has
to derive a name for every branch, and every branch property has to lower through step
1's `decide_type`, which refuses an array, a mapping, a multi-type node, a typeless node
carrying a constraint, and a `$ref` whose target refuses. Branch properties in this bundle
are heavily arrays and cross-document references, so I expect that second screen to be the
larger cut: roughly three quarters of the 35.

The previous route measured 9 emitted of 156 at base `11a9b2828` and that is in the bead,
so +10 is an informed guess and not an independent one. What makes it *not* simply 9 is
that §4 removes the old route's `partitions_by_requiredness` gate — the union is the
validator, so branch order no longer decides what a payload comes back as, and a root that
does not partition no longer has to refuse.

### 2. The refusal profile

`allOf` stays the single largest keyword, at **≥ 55** from the root alone and more from
branches. Every refusal names a document, a pointer and a keyword; `Refusal` maps an empty
pointer to `/`, so `test_every_named_document_is_either_emitted_or_refused_by_name_and_keyword`
holds.

### 3. The three checks — and the one I expect to fight

The accepts and refuses checks I expect to pass without incident: both go through
`strict_validate`, whose schema half answers first, and the schema half for a union root is
the document's own `oneOf`/`anyOf`, which `jsonschema` decides exactly.

**The schema comparison is where I predict the design is decided, and I predict a first
measurement that is RED.** `__get_pydantic_core_schema__` returning the branches' union
makes `model_json_schema()` render an `anyOf`, and an `anyOf` states none of the root's own
facts. 114 of the 156 declare `type: object` at the root and 156 of 156 declare a
`description`, so I expect `compare_schema` to report `missing` for `/type` and
`/description` on every union root the first time it is run, and `model_drops_a_fact` as the
pair's verdict.

I predict the fix is to make the base's rendered schema carry the root's own facts BESIDE
the `anyOf` rather than instead of it, because `compare_schema` reads only `FACTS` at a
pointer and `anyOf` is not one of them — so a schema stating `type`, `description`,
`additionalProperties`, `properties` and `required` next to an `anyOf` compares clean in
both directions. I do not yet know which pydantic channel does that, and finding out is
the first thing after this file is committed.

### 4. The four paths

I predict all four work as §4 states, and that the one that would be missed without being
named is `Base(**data)`: `BaseModel.__init__` validates with `self_instance=self`, so the
object is allocated before validation and no schema reaches it. I predict that without
`__new__`, `Base(**data)` returns a base instance rather than a branch, and that the nested
field / `TypeAdapter` / `model_validate` paths all three work off the core-schema hook
alone.

I predict `model_dump_json` on a base instance raises before the wrap serializer is
attached, and that attaching it to a `definitions` node rather than to the node that node
wraps leaves it still raising — §4 says the key is not consulted there, and I expect to
confirm that by putting it in the wrong place on purpose.

### 5. Bare-`$ref` branches: a decision, reported not re-decided

§7's done-when says **one subclass per branch**. A bare-`$ref` branch has no node this
module can declare a subclass from: the member would be the TARGET's class, which does not
descend from this base, so `isinstance(payload, Base)` would be false for that arm and the
done-when would be false. Declaring a subclass of both would be a second name for the
target's node (P2) and would inherit the target's `__adcp_schema__`, which points at
another document.

So **a bare-`$ref` branch refuses, at `$ref`, pointer `/<kw>/<i>`.** Measured cost: **5 of
the 44** that pass the keyword screen — `core/assets/asset-union.json` (21 branches),
`core/async-response-data.json` (42), `core/pricing-option.json` (10),
`core/requirements/asset-requirements.json` (12), `compliance/task-completion-data.json`
(4). All five are all-bare-ref, so none loses only part of itself.

### 6. Root `properties`: predicted to need no refusal of its own

A root `properties` is a conjunction with every branch in draft-07, so the base declaring
those fields and each branch inheriting them is the faithful reading, and it is what §4's
subclassing already gives. I predict no refusal is needed for it and that the 4 documents
carrying one are killed by something else anyway (two of them,
`core/assets/daast-asset.json` and `core/assets/vast-asset.json`, carry array root
properties, which are step 6's row).

If the branch's own pair turns out to report the root's inherited fields as facts
`#/<kw>/<i>` does not state, that is the measurement that forces a refusal here, and I
predict it is the second design question after the comparison.

### 7. What must not move

The 43 modules stay byte-identical and the 44 pairs stay green. Every edit to
`codegen/emit.py` and `codegen/compiler.py` is additive with a default that leaves the
existing call sites unchanged, so I predict
`test_the_committed_tree_is_what_a_fresh_run_emits` passes on the 43 and
`test_the_step_result_is_counted_over_the_whole_population`'s three sums move only by what
the new documents add.

### 8. The perturbations, and what each must redden

Named before they are run. A perturbation that reddens nothing is a finding about the
instrument.

| # | perturbation | must redden |
|---|---|---|
| P1 | drop `__get_pydantic_core_schema__` from the mixin | the nested-field, `TypeAdapter` and `model_validate` paths — a payload comes back as a base |
| P2 | drop `__new__` from the mixin | only the `Base(**data)` path |
| P3 | change the declaring test to `cls in cls._branch_models` | the consumer-subclass assertion, and nothing else |
| P4 | put the union in the serializer slot instead of the validator | `model_dump_json` on a base instance |
| P5 | set `serialization` on the `definitions` node rather than on the node it wraps | `model_dump_json` again, and nothing else |
| P6 | emit `_ROOT_REQUIRED` as the union of root-required and branch-selecting fields | the assertion that separates the two kinds |
| P7 | hard-code `_branch_combinator` to `oneOf` | an `anyOf` root's refusal naming the wrong keyword |
| P8 | widen one branch property's annotation to `Any` | the schema comparison on that branch, and neither of the other two checks |
| P9 | let a branch with no derivable name be named after its parent | the refuse-by-name-and-pointer assertion |

P8 is the control for the specification's §6 claim that the comparison is the only check
that grades the generated code, re-measured on this step's own population rather than
inherited from step 1's.

## What I am most likely to be wrong about

The comparison. If the root's facts cannot be put beside the `anyOf` through any channel
that is not the emitter copying the document into the model, then either the base is not
the graded model for the document or this step emits nothing, and both are findings worth
more than the +10.
