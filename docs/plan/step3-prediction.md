# Step 3 prediction — enumerations, root and inline

Written and committed BEFORE the lowering exists, on branch `emit/s3-enum-v2` at base
`482e7bc63` (`81e132aee` + the merged `emit/format-regex`). Graded in the report; both kept.

Everything below is a prediction about an OUTCOME. The census numbers it rests on are
inputs, measured first and stated with their denominators in §1; they are not predictions
and are not graded.

## 1. The inputs, measured on `schemas/cache/3.2` (1,054 portable documents)

Reproduced exactly, every one of them, against the figures the brief carries forward:

| fact | measured |
|---|---|
| root enums (`enum` at the document root) | **214**, all `type: "string"` |
| documents carrying an `enum` at any schema position | **535** |
| enum nodes | **1,069** |
| nodes carrying `enumDescriptions` | **137** (1,151 entries, 10 of them multi-line) |
| nodes carrying a `default` | **66**, none of them a root |
| constraint keywords beside an `enum`, over all 1,069 | **0** |
| member-type sets | 1,066 all-`str`, 3 all-`int`; 0 mixed, 0 `bool`, 0 empty, 0 duplicated value |
| nodes where two values spell one member name | **1** — `formats/canonical/html5.json` at `/properties/clicktag_macro`, `clickTag`/`clickTAG` |
| Python keywords among member values | `pass`, `global` |
| values needing a prefix (leading digit) | 17 strings (`1.0`, `4:2:0`, `3d_render`, …) and 6 integers |
| `type` disagreeing with the member types | **0** of 1,069 |
| `enumDescriptions` entries containing `"""` | **0** of 1,151 |

Two keywords sit beside an `enum` and are in neither `ANNOTATIONS` nor `x-`:
`enumDescriptions` (137 nodes) and `enumMetadata` (3 nodes), plus `notes` at 1 node.

## 2. The population, and how it is selected

`population()` becomes `leaves ∪ referencing ∪ carries_an_enum`:

    85  leaves (step 1)
   249  referencing-a-property (step 2)
   535  carrying an enum at a schema position (step 3, the new selector)
   ---
   749  named, with 26 leaves and 94 referencing documents already inside the 535

The step-3 selector goes in `codegen/bundle.py` beside the other two. The DISPATCH row's
selector is a different predicate — what the document's ROOT is — and `is_enum_root(doc)`
(`"enum" in doc`) implies `carries_an_enum(doc)`, so the row cannot claim a document the
step does not count.

## 3. N, with both denominators

| claim | predicted |
|---|---|
| emitted documents | **282** |
| refused documents | **486** |
| emitted + refused | **768** = 749 named + 19 reached through a `$ref` |
| ΔN against the SAME 749-document population (the current emitter reaches 44) | **+238** |
| ΔN against the committed tree (43 modules) | **+239** |
| the `enum` refusal bucket | **262 → 0** |

282 is derived, not recalled: a screen that treats `enum`/`enumDescriptions` as annotations
and changes nothing else emits **279** over the same 749, and the three `enumMetadata`
documents (§5) add 3 with no cascade. It agrees with the earlier attempt's 282 on a
different trunk, which is a cross-check and not the source.

**Where I expect to be wrong:** the counter totals in
`test_the_step_result_is_counted_over_the_whole_population` (graded instances, facts
compared, model-only facts) and the pair count. The screen cannot predict those at all —
it predicts which documents refuse, not how much each surviving pair grades. I also expect
the refusal buckets to move in a way the screen already shows and I am not modelling:
`type` 95 → 142, because a document whose enum no longer stops it gets further and hits an
array, a mapping or a multi-type node instead.

## 4. The root enums

- **213 of 214 emit.**
- The one refusal is **`enums/task-type.json` at `/` on `notes`**, and its measured cascade
  cost is **0**: 7 documents reference it, 6 are in the population, and every one of those
  refuses on a keyword of its own. Widening `emit.ANNOTATIONS` by one row would emit it;
  `notes` sits at 2 schema positions in the whole bundle and that is the trunk's decision,
  not this lane's.
- `formats/canonical/html5.json`, which holds the one colliding node, refuses on **`allOf`**
  at the root before any enum is read, so **the injectivity refusal is unreachable from this
  bundle** and its cascade cost is 0. Predicted consequence: it has to be graded on a
  synthetic document, and a perturbation that deletes the check reddens only that test.

## 5. One keyword decision, reported, reversible in one line

`enumMetadata` (3 root enums: `enums/error-code.json`, `enums/media-buy-valid-action.json`,
`enums/request-signing-error-code.json`) is treated as an annotation of the enum node, in
`codegen/lower/enum.py` and NOT by widening the global `ANNOTATIONS`. It states nothing
about an instance — `enum` already closes the value set — and it has no slot in an
enumeration. Refusing it instead gives **N = 279** and **210 of 214**; that is the one line.
Named as a ceiling, because the block carries normative consumer guidance the SDK does not
surface.

## 6. What the emitted code looks like, and the one invariant I predict I must read differently

- An `enum` node becomes `StrEnum`/`IntEnum` (D2), base chosen by exact member type, `bool`
  excluded on purpose.
- **Member names are UPPER-CASED, and that is correctness.** `pass` and `global` are live
  values; lower-casing emits `pass = "pass"`, a module that does not parse. Upper-casing is
  also why no `keyword.iskeyword` branch is needed — every Python keyword is lower-case —
  and why no member is ever suffixed.
- **The injectivity check binds to the function that actually runs.** dmcg's `Enum` model
  renders `{{ field.name }}` verbatim, so the naming function is OURS. Predicted and
  asserted: every `field.name` handed to the compiler appears as an assignment target in the
  rendered text, so the check is not vacuous.
- **`enumDescriptions` is carried by the compiler's own enum printer**, as a per-member
  docstring (`use_inline_field_description` + `extras["description"]`). The multi-line case
  renders a properly indented triple-quoted block. Predicted: 137 nodes / 1,151 entries
  carried, 0 dropped.
- **`__adcp_schema__` cannot go in an enum's class body.** `Enum.jinja2` has no
  `class_body_lines` slot, and a post-generation patch is forbidden. So a root enum's
  MODULE carries the ref and binds `strict_validate` through `strict_alias` — the same two
  halves, through the same `_refuse`, as D2's root-scalar row, which is the same situation
  (a node with no `AdCPBaseModel` to hang a classmethod on). Predicted: `graded()` needs no
  change, because its module-level arm already grades exactly this shape; and the Enum class
  is still the model the harness grades.
- `requires-python` 3.10 → **3.11**, because `StrEnum` is 3.11. `compiler.TARGET` stays
  `PY_310` unless moving it is byte-neutral on the 43 committed modules.

## 7. The 43 modules and the 44 pairs

Predicted **byte-unchanged**, all 43. A module among them cannot contain an enum node:
if it did, the document would have refused on `enum` and would not be one of the 43.
`core/locale-tag.json` is NEW at the 749-document population (the current emitter already
reaches 44 there, against 43 committed) and is not a change to an existing module.

## 8. The dispatch table — reported, because it does not exist yet

The specification's §5 Layout states a `(selector, lowering)` table and the brief tells me
to add one row to it. **There is no table in the trunk**: `lower_document` is an
`if`/`elif`/`else` over two root kinds. I predict I must build it, minimally, and that the
four sibling lanes adding "one row" will each build one too — so the integrator takes one
lane's table and cherry-picks four rows onto it. The table I predict:

    (is_object_root, _lower_object_root)
    (is_scalar_root, _lower_scalar_root)   # "+ and no enum", which is the load-bearing word
    (is_enum_root,   lower_enum_root)

and that it is UNORDERED, with a document two rows claim raising a build failure rather than
taking a precedence. Measured already, as an input: the three selectors claim **0** documents
in common over all 1,054, and **214** in common if the scalar row drops `"enum" not in doc`.

## 9. The perturbations, and what each one must redden

| # | perturbation | predicted to redden |
|---|---|---|
| P1 | lower-case the member names | the emitted tree does not IMPORT (`pass = "pass"` is a syntax error), so the gate fails at collection, plus the upper-case test |
| P2 | drop `enumDescriptions` | **nothing in the three checks.** `enumDescriptions` is not in `harness.FACTS` and changes no accepted set. Only my own test. Predicted in advance, so a green harness here is a finding about the instrument and not a pass |
| P3 | widen the lowering so an enum node emits the scalar its `type` names (the defect inventory's enum widening, reintroduced) | **the schema comparison, `model_drops_a_fact`.** This CONTRADICTS the earlier attempt's carried-forward finding that "nothing in the harness can grade this step": `enum` is in `FACTS` on this trunk, so a plain `str` annotation states no `enum` where the document states one. If it comes back green, the instrument is the finding |
| P4 | delete the injectivity refusal | only the synthetic test. `formats/canonical/html5.json` refuses on `allOf` first, so no bundle document reaches it (§4) |
| P5 | drop `"enum" not in doc` from the scalar row's selector | 214 documents claimed by two rows → the build failure, and the disjointness test |
| P6 | mangle one member's VALUE | the accepts check, direction 1 (`model_refused_valid`), on every pair whose document names that enum |

A perturbation that reddens nothing is a finding about the instrument, and P2 and P4 are
predicted to be exactly that before either is run.
