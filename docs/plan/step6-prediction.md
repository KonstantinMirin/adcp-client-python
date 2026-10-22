# Step 6 prediction: containers and mappings

Written and committed BEFORE the lowering exists. Graded in the same file afterwards,
with both halves kept.

Tree: `emit/s6-containers-v2` at `482e7bc63` (`emit/format-regex` merged clean as a
fast-forward; 72 passed before any edit of mine).

Everything below names its population and how it was selected. Where a number of mine
disagrees with the brief's, both are stated and neither is quietly adopted.

## 0. The baseline, measured

| quantity | value | how selected |
|---|---|---|
| bundle size | 1,054 | `bundle.portable` |
| step 1 population (`is_leaf_object`) | 85 | selector in `bundle.py` |
| step 2 population (`references_a_property`) | 249 | selector in `bundle.py` |
| named population today | 334 | the union of those two |
| N today | 43 emitted documents | `emit.emit(BUNDLE, population())` |
| graded pairs today | 44 | 43 roots + 1 nested class |
| refused today over the named 334 | 331 | 296 named + 35 reached by `$ref` |

## 1. What the dispatch table is keyed on, because it does not exist yet

**The brief says to add "one row in the dispatch table in `codegen/emit.py`". There is
no table.** `codegen/lower/` does not exist either, and the four sibling lanes
(`emit/s3-enum-v2`, `emit/s4-product-v2`, `emit/s5-union-v2`) are all sitting at exactly
this tip with nothing added. So this lane creates the table, and the shape it gets is a
decision the brief delegated by assuming one. It is recorded here rather than discovered
in a diff.

Two readings were available and one of them is refuted by measurement.

**Keyed on the DOCUMENT (refuted).** A row would claim a whole document, and steps 1, 2
and 6 would have to partition the bundle. Measured: 191 of the 334 named documents
declare a container node, and 95 of them have an `object+properties` root. A step-6 row
claiming those would have to lower an object root with properties — which is step 1's
lowering — so the table would hold two copies of `lower_object`. Duplication is the
defect, so this reading is out.

**Keyed on the ROOT KIND (adopted).** `lower_document` already dispatches on the root:
object-with-properties, scalar, or refuse. That is a real partition — a document's root
is exactly one kind — so a document selected by two rows is a genuine build failure
rather than a precedence puzzle, and no row duplicates another's lowering.

Under it:

- **a step's POPULATION** is which documents it names on the command line. Steps 1 and 2
  name object roots, selected by reference structure. Step 6 names **container roots**,
  and `bundle.is_container_root` is both its selector and its table row.
- **the container ARMS** (`array`, `mapping`, `multi_type`) are reached through
  `decide_type`, the per-node walk every row already shares. They are not table rows,
  for the same reason `decide_type` itself is not one.

Consequence, and it is why the floor is structurally safe: the named population only
GROWS (334 → 371), so no document stops being named and no module can be lost.

## 2. Predictions

Each is falsifiable and graded below.

**P1 — the 43 committed modules are byte-identical.** A module emits today only if no
container keyword refused in it, so none of the 43 declares a container and nothing this
step adds can reach one. Zero module texts change.

**P2 — all 44 pairs still pass**, with `graded_instances` 3758 and
`comparison.compared` 486 unchanged for them.

**P3 — the named population is 334 → 371.** My selector adds 37 container roots: 32
mapping roots, 5 array roots, 0 multi-type roots (measured — the bundle has no
multi-type root at all, so the brief's multi-type concern is a PROPERTY concern only).

**P4 — N rises to 117, and 95 ≤ N ≤ 135.**
Denominators for the bound: 98 named documents are refused today AND carry no keyword
outside steps 1+2+6's vocabulary (that vocabulary enumerated by name, not by residual);
21 of the 98 carry a `uniqueItems` array and stay refused by P7, leaving **77** as the
static upper bound on newly-emitting named documents. Of the 77, 42 refuse today on
`type` (the direct container cases) and 56 on `$ref` (their target refuses and unblocks
only if the target is itself in the 77). Point estimate: 62 of the 77 emit, +2 from my
own row (below), and +10 newly pulled `$ref` targets.

**P5 — my own table row contributes exactly 2 to N.** Of the 37 container roots, only 3
are keyword-clean: `core/acceptance-policy-profile-ids.json` (an array root carrying
`uniqueItems`, so refused by P7 and by P6), and `core/context.json` and `core/ext.json`,
both `{"type": "object", "additionalProperties": true}` — which lower to a
`dict[str, Any]` module-level alias. The other 34 refuse on `oneOf` (28), `const` (24),
`discriminator` (20), `enum` (15), `allOf` (10) and below: later steps' rows.

**P6 — all 5 root arrays refuse, and D2's `RootModel[list[X]]` row is not built.**
4 of the 5 carry `uniqueItems: true` at the root and refuse on it. The fifth,
`media-buy/product-refinement.json`, refuses at `/items` on the alphabetically-first
keyword of that node that no row handles — `_check_keywords` walks `sorted(node)`, and
that node carries `const`, `discriminator`, `enum` and `oneOf`, so the prediction is
**`const`**. The brief says `discriminator`; if `const` is what fires, the brief's
attribution is off by the sort order and I report that rather than adopt it. Per the
brief, the root-array row refuses **by name with the element type in the detail**
instead of building a class no document reaches.

**P7 — `uniqueItems` refuses, and the reason is measured rather than deferred to D6.**
`Constraints(uniqueItems=True)` populates `unique_items` on dmcg's constraints model and
the renderer emits **no `Field` at all** — `list[str]`, bare. pydantic v2 removed
`unique_items`, so carrying the keyword through `constraints=` is a model WIDER than its
document. D6 already puts `uniqueItems` in step 7's rule set; this says what the
alternative actually costs. The array arm's handled set is `{type, items, minItems,
maxItems}` and `uniqueItems` falls through `_check_keywords` with no special case.

**P8 — the key-typing mechanism has a REACHABLE POPULATION OF ZERO, and I say so rather
than report its sites as covered.** Over the 136 keyword-clean documents of the new named
set, the number of `propertyNames` or `patternProperties` sites is **0**. So every key in
every mapping this step actually emits is `str`, and that is the document's own reading
(D5: silence about keys means `str`). The key typing is still implemented, because it is
the step's stated exit condition, and it is graded on documents derived from real bundle
nodes with the later steps' keywords removed by name — the same arrangement the typed
`additionalProperties` row gets.

**P9 — my key-site census disagrees with the brief's and I cannot reproduce the brief's.**
Over `bundle.portable` (1,054 documents), counting a key-constraining site once per
`(document, pointer)`:

| key kind | brief | measured here |
|---|---|---|
| `propertyNames` `$ref` | 16 | 5 |
| `propertyNames` `anyOf` | 22 + 9 titled | 1, none titled |
| `propertyNames` `pattern` | 38 | 13 |
| `propertyNames` `minLength`/`maxLength` | 4 | 3 |
| `patternProperties` key | 86 | 14 |
| `propertyNames` `enum` | 1 | 4 |
| nothing about keys | 193 | 128 |
| **total** | **369** | **168** |

Neither of the two obvious populations reproduces 369: including the `bundled/` and
`mcp/` projections (1,625 files) gives 4,436, and no single scale factor fits the rows.
The `enum` row is the tell that the brief's population is not a superset of mine — the
brief counts 1 where I count 4, and the one it names
(`core/store-item.json#/properties/hours`) is in my 4. My 3 others sit under
`allOf/*/then`, `allOf/*/else` and `oneOf/*/allOf/*/then`, which are rule positions no
mapping is lowered at, so **at a type position the brief's 1 is right**. That
reconciles the one row where the count changes a decision. The rest I report as a
disagreement and do not re-decide.

**P10 — `propertyNames` with an `enum` is refused by name, not built as a model.** The
brief says a closed key set is a model whose keys are its fields. Its one site is
`core/store-item.json#/properties/hours`, and that document carries `enum` (step 3's
keyword), so it refuses before any mapping is lowered: the model would be a class no
document reaches, no pair grades. This is the same situation the brief itself resolves by
refusing — "refuse them by name with the element type in the detail rather than building
a class no document reaches" — so the closed-key-set row refuses by name with the key set
in the detail. **This is the one place I depart from the brief's list, and it is reported
rather than acted on silently.**

**P11 — D5's constrained-container alias is not built.** D5 resolves a constrained
container to a named type so `dict[str, Tags]` is a plain reference. Measured over the
keyword-clean named population: **0** sites where a mapping value or an array element is
itself a container carrying a bound. So the alias module would be machinery with no
population. A nested constrained container refuses by name; the alias is built by the
step whose population reaches one.

**P12 — typed `additionalProperties` emits in 0 modules**, carrying the brief's figure
forward and re-measured here: 727 documents mention `additionalProperties`, 51 carry a
typed one, and 0 typed sites sit inside a keyword-clean named document. Implemented
(it is this step's named defect) and graded on a constructed document; `__pydantic_extra__`
appears in no emitted module.

**P13 — multi-type applies each keyword to its own branch, over 3 sites**:
`["null","string"]`, `["number","string"]`, `["integer","null"]` in the keyword-clean
named population. Two carry a `null` arm, which the v1 attempt recorded as having no
population — it now has one, so the `None` arm is decided here and not left open.

## 3. Perturbations, and what each must redden

A perturbation that reddens nothing is a finding about the instrument, not a pass.

| # | perturbation | must redden |
|---|---|---|
| X1 | admit `uniqueItems` into the array arm's `constraints=` | the schema comparison, `missing` on a `uniqueItems` fact, on every document that then emits |
| X2 | put the array's `minItems` on the ELEMENT instead of the list | the comparison: `minItems` missing at the array, a length fact added at the element |
| X3 | apply a multi-type node's keywords to EVERY arm | the accepts check (`model_refused_valid`) or the comparison's `added` |
| X4 | type a constrained mapping key as plain `str` | the key-typing test — and if nothing reddens, the key type is graded by nothing and that gap gets closed before this step reports a pass |
| X5 | emit the root array as an alias instead of refusing it | the refusal arithmetic, and the `uniqueItems` refusal of the other four |
| X6 | make the table's two-row collision check a no-op | the collision test |

## 4. Grading

Filled in after the measurement. Both halves kept.
