# salesagent-j3k2l.22 — `not`, `dependencies` and the remaining object-size keywords

Started from `emit/from-scratch` at **62b5e7ce2d612d7a540dd6784cd45b9e9da3ba9f**
(`docs(plan): a SchemaRef names a node as the document applies it`), clean.

Branch: `sdk/j3k2l22-not-deps-objectsize`.

## 0. The baseline, re-measured on that tree

`python -m codegen.emit` over all 1,054 portable documents:

| figure | value | denominator |
|---|---|---|
| emitted | 401 | 1,054 portable |
| refused | 653 | 1,054 portable |
| graded pairs | 462 | — (450 pass, 12 `no_constraint_to_step`) |
| added / missing / differs | 0 / 0 / 0 | 4,658 document facts compared |

**This is the baseline the ticket states (401 + 653), not the one the brief states
(406 / 648, 481 pairs, 469 pass, 395 modules).** `emit/from-scratch` has not moved
past the ticket's figures; its tip is the plan-doc commit above and
`tests/test_emit.py` still pins 462 / 450 / 12. Every number below is measured on
62b5e7ce2 and nowhere else.

## 1. The population, and the partition

**69 documents**, of 653 refusals, of 1,054 portable. The ticket says ~60 and the
counts have moved: `not` 25 (not 23), `anyOf` 8 (not 5), `discriminator` 7 (not 5),
`minProperties` 6 (not 5), `maxProperties` 4 (not 3), `dependencies` 8, `oneOf` 7,
`enum` 2, `maxLength` 2.

**The keyword a refusal names is not what the population is.** Partitioned by the
POSITION the refused node sits at, which is what decides which unit owns it:

| # | family | position | docs |
|---|---|---|---|
| R1 | a D6 rule keyword at the ROOT of an `allOf` document | 20 |
| R2 | a D6 rule keyword at the ROOT of a union document | 4 |
| R3 | a D6 rule keyword on a union BRANCH | 8 |
| R4 | an `allOf` CONJUNCT that states only a rule keyword | 8 |
| M1 | `min`/`maxProperties` on a MAPPING node (object, no `properties`) | 9 |
| M2 | `propertyNames` constraining the key's own text | 2 |
| C | a combinator of SHAPES at a nested position (property / items / `definitions`) | 16 |
| E | a union root whose branches are SCALARS | 2 |
| | **total** | **69** |

Those are not one thing and **no single unit is forced onto them**:

- **R1–R3 are one unit.** D6's mechanism is already complete — `rules.lower` produces
  every constructor these nodes need (30 of the 32 reduce to a rule; the other 2 reduce
  to nothing, which D4 makes correct rather than a refusal). The defect is that only
  `compiler.lower_object` consults it. `lower_product.lower_root` and `union._plan`
  declare classes and screen the rule family out.
- **M1 is a second unit, and it is NOT D6.** D6's `PropertyCount` reads
  `__pydantic_fields_set__` of a model; a mapping is a `dict` and has no fields, so the
  rule cannot carry it. Its home is the annotation (D5), where pydantic both enforces
  and renders it.
- **M2 is M1's own `_key` arm**, not a third unit.
- **R4, C and E are not mine, and I build nothing for them.** R4 is
  `salesagent-j3k2l.18`'s stated population ("a conjunct stating a rule keyword"). C is
  D2's union row at a NESTED pointer and E is a union root of scalars; no bead owns
  either, so each gets one filed rather than a lowering written here.

## 2. The two units

### Unit 1 — D6's rules reach every class the emitter declares

The after-validator (`RuleBound`, `src/adcp/types/_runtime.py`), the six rule kinds and
`rules.lower` are untouched. Three wirings:

1. **`compiler.declare_object` lowers the node's rules.** It is the one funnel every
   class WITH FIELDS passes through, so the `allOf` row gets rules by passing through
   it rather than by repeating `lower_object`'s call.
2. **The rule keyword set moves to `compiler`**, so `lower/product.py` and
   `lower/union.py` can admit it without importing a sibling lowering (D13).
   `rules.ANNOTATIONS = compiler.ANNOTATIONS` is the precedent and the reasoning is
   verbatim its own: `compiler` sits below both `codegen.lower` and `codegen.bundle`.
3. **`RuleBound` collects `_adcp_rules` over the MRO** instead of reading one ClassVar.

(3) is not scope creep; it is **measured as required**. 3 of R2's 4 documents declare a
rule at the root AND a rule on a branch — `media-buy/list-products-response.json`,
`refine-proposals-response.json`, `request-proposals-response.json`. A branch declaring
its own ClassVar shadows its base's, so the root's `not` would stop firing SILENTLY.
§6 already names this defect from the other side: "A subclass that silently loses a
validator is the defect this catches."

### Unit 2 — a bound on a mapping's key COUNT is a constraint on its type

Measured on pydantic 2.13.5: `Annotated[dict[str, int], Field(min_length=1, max_length=4)]`
renders `{"type": "object", "minProperties": 1, "maxProperties": 4}` — the document's own
spelling, so the comparison stays symmetric with no row.

Measured on the pinned compiler: `Constraints` has **no `minProperties`/`maxProperties`
field at all**, so the document's own spelling renders bare `dict[str, int]` and the
bound is DROPPED SILENTLY. Its one length channel (`min_length`/`max_length`, reached by
the `minLength`/`maxLength` or `minItems`/`maxItems` aliases) renders
`Field(min_length=1, max_length=4)`, which is the correct annotation. So the translation
goes in `compiler._field` — the compiler's half of the seam — and is the same
translation the array row already relies on dmcg performing for `minItems`.

**This is not an open compiler gap** (§3, D10): the rendering we need IS producible from
a declaration we can state, through a channel the compiler already has. No fork.

`_key` additionally takes the length-only `propertyNames` arm D5 names, which pydantic
renders back as `propertyNames: {minLength, maxLength}` — the document's own keyword.

## 3. Predictions

Written before any code. Graded in §4.

| # | prediction |
|---|---|
| P1 | R1: 18 of 20 emit; 2 refuse on a further keyword their root also carries |
| P2 | R2: 4 of 4 emit |
| P3 | R3: 6 of 8 emit; 2 refuse elsewhere in the branch |
| P4 | M1: 5 of 9 emit. 3 refuse on a key `pattern` (the grader), 1 chains into family E through its `propertyNames` `$ref` |
| P5 | M2: 0 of 2 emit; both refuse on the key `pattern`, with a reason naming the GRADER and not a later row |
| P6 | R4 (8) + C (16) + E (2) = 26 unchanged, still refused; one bead filed for C, one for E |
| P7 | emitted 401 -> **434**, refused 653 -> **620**, of 1,054. May exceed 434: a newly emitted document is a reference target and a usable base for others |
| P8 | added / missing / differs stay **0 / 0 / 0** |
| P9 | graded pairs rise from 462 by **at least 60** |
| P10 | `ROWS` stays at **six**. No new selector, no change to `declares_its_own_root_kind`, no new row |
| P11 | A key `pattern` is measured UNGRADEABLE, not merely unimplemented: pydantic re-renders it as `patternProperties` and that key swallows `additionalProperties`, so a faithful model reports both an added and a missing fact |

### What I expect to be wrong

P1 and P3 are the two guesses with no instrument behind them — I classified by the
FIRST keyword each document refuses on, and a second keyword at the same node is
invisible to that reading. P9 is the weakest: a pair count is a function of the
nested classes each newly emitted document declares, which I did not count.

## 4. Measured (filled in after the build)

The agent that wrote §§0–3 stopped before it could fill this in, and its work was
banked uncommitted. §§5–8 are a NEW agent's, resuming from the banked branch merged
forward onto trunk `ac8a64fb1`. §§0–3 are graded in §7 against the measurements in
§6, because every figure in them was taken 77 commits behind trunk.

---

# Part two — the resumption

Merged forward at `0cfb5b6cb` (`git merge --no-ff ac8a64fb1`, never a rebase), with
one integration fix at `853384791`: trunk grew `Lowered.distinct` while the lane was
off trunk, the lane's `Rules` carrier was written against the three-field `Lowered`
that preceded it, both sides merged clean and `lower_object` then read
`stated.distinct` off a carrier with no such field — 27 of the gate's 45 tests failed
with one `AttributeError`. That is what "internally consistent one trunk behind"
costs, and it was the first thing re-measured rather than the last.

## 5. The two baselines, re-measured on this tree

Both by the constants the refusal producers emit (`refusal.DEFERRED_TO_A_LATER_ROW`,
`refusal.UNRESOLVED_TARGET`), never by matching text. Denominator throughout: the
**1,054 portable documents**.

| figure | trunk `ac8a64fb1` | merged `853384791` |
|---|---|---|
| emitted | 580 | 670 |
| refusals | 474 | 384 |
| — deferred (pending) | 102 | 63 |
| — transitive (pending) | 1 | 1 |
| — verdicts | 371 | 320 |
| **accounted** (emitted + verdicts) | **951** | **990** |

The two pins in `tests/test_emit.py` stand at `deferred <= 102` and
`accounted >= 951` on trunk, which is where trunk measured them.

### This issue's population, by POINTER SHAPE and not by keyword tally

Trunk's 102 deferrals name 12 keywords. The four this issue owns are **44 documents**
(`not` 22, `dependencies` 10, `minProperties` 7, `maxProperties` 5), and the position
each states its keyword at is what decides the unit:

| position | `not` | `dependencies` | `minProperties` | `maxProperties` | total |
|---|---|---|---|---|---|
| a ROOT (pointer `/`) | 18 | 9 | 2 | 0 | **29** |
| a `oneOf` BRANCH | 3 | 0 | 0 | 0 | **3** |
| a property, or deeper, or inside a section | 1 | 1 | 5 | 5 | **12** |
| total | 22 | 10 | 7 | 5 | **44** |

**A root refusal spells its pointer `/`, not `""`.** 29 of the 44 are at a root, and
reading the empty string would have reported 0.

### What the banked work (Unit 1) already does to those 44

| outcome on the merged tree | `not` | `dependencies` | `minProperties` | `maxProperties` | total |
|---|---|---|---|---|---|
| EMITTED | 4 | 2 | 1 | 0 | **7** |
| VERDICT | 15 | 8 | 0 | 0 | **23** |
| still deferred, on one of these four | 1 | 0 | 6 | 5 | **12** |
| still deferred, on another row's keyword | 2 | 0 | 0 | 0 | **2** |

So Unit 1 accounts for 30 of the 44 and leaves 14, of which **12 are still this
issue's** (`not` 1, `minProperties` 6, `maxProperties` 5) and 2 moved to another row
(`anyOf` → `salesagent-j3k2l.26`, `maxLength`).

The 12 are one family and it is not Unit 1's: **11 are a MAPPING node** — `type:
object` with an `additionalProperties` schema and no `properties`, so there is no
class for a rule to attach to and `containers.mapping`'s keyword screen refuses the
bound. The 12th is `core/account.json#/properties/destination_billing_entity`, whose
whole schema is `{"not": {}}`.

## 6. What is still to build, with the measurements that decide it

Measured on pydantic 2.13.5 and on the pinned `datamodel-code-generator`, before
writing anything:

* `Annotated[dict[str, int], Field(min_length=1, max_length=4)]` renders
  `{"type": "object", "minProperties": 1, "maxProperties": 4}` — **the document's own
  spelling** — and enforces it (`{}` refused, one key accepted, five refused). So the
  bound is lowerable with no comparison row.
* dmcg's `Constraints` has **no `minProperties` field**, and `Constraints(minProperties=1)`
  silently sets nothing. Its length channel does render it:
  `Constraints(minLength=1, maxLength=4)` on a `dict[str, int]` renders
  `Field(min_length=1, max_length=4)`. So the translation is the COMPILER's, beside
  the array row's reliance on dmcg rendering `minItems` as `min_length`.
* A key's own LENGTH is faithful too: `dict[Annotated[str, StringConstraints(min_length=1)], int]`
  renders `{"additionalProperties": ..., "propertyNames": {"minLength": 1}}` — the
  document's own keyword, with `additionalProperties` retained.
* A key's own PATTERN is **not**: `dict[Annotated[str, StringConstraints(pattern=...)], int]`
  renders `{"patternProperties": {"<expr>": ...}}` — an `added` fact, and
  `propertyNames` AND `additionalProperties` both go `missing`. It still enforces, so
  it is ungradeable rather than unimplemented, which is a VERDICT and not a deferral.

Two changes follow, and neither is a row:

1. **`containers.mapping` admits the key-count bound** and carries it as the node's
   own constraints, the way `containers.array` carries `minItems`/`maxItems`;
   `compiler._field` translates `min`/`maxProperties` onto the length channel.
2. **`containers._key` routes a key's TEXT constraint through the walk**, so D5's
   existing rung-3 alias names it (`constraints.resolve`, `constraints.record`) —
   except `pattern`, which gets the verdict the fourth measurement above earns.

## 7. Predictions

Written before either change exists, and graded in §8.

| # | prediction |
|---|---|
| R1 | Of the 11 mapping documents, **7 EMIT**: `a2ui/component.json`, `core/account-change.json`, `core/account-change-recorded-webhook.json`, `core/reporting-file-entry.json`, `core/geo-place-requirement.json`, `core/product-change-map.json`, `governance/reported-outcome-error.json` |
| R2 | The other **4 become VERDICTS on a key `pattern`**: `core/geo-place-support.json`, `core/geo-region-requirement.json`, `core/geo-region-support.json`, `core/creative-localization.json` (whose `patternProperties` expression is read as the key's pattern) |
| R3 | `core/account.json` becomes a **VERDICT** on `not`: a property whose schema admits no instance forbids the key, and no field — nor D8's `extra` — states that |
| R4 | R3 does **not** unlock `core/media-buy.json`, which chains on it and is already counted as a verdict |
| R5 | **ROWS stays at six.** No new row, no new selector, no change to `bundle.declares_its_own_root_kind`: 1 of the 12 is at a root (`core/product-change-map.json`, a mapping root an existing selector already claims), 10 at a property or deeper, 1 inside a section |
| R6 | The pins become **`deferred <= 51`** (63 − 12) and **`accounted >= 1002`** (990 + 12), and both are fire-probed one step tighter |
| R7 | `added` / `missing` / `differs` stay **0 / 0 / 0**: every new fact is rendered in the document's own keyword, measured above |
| R8 | The gate's failing set goes from **3 to 1**. `tests/test_emit_product.py::test_the_rows_delta_is_reported_with_its_denominator` and `::test_a_keyword_at_the_root_beside_the_conjunct_list_refuses` are cleared — both pin behaviour Unit 1 changes, and both are re-pointed at what this tree measures. `tests/test_fragment_ref.py::test_the_bundles_own_sections_are_walked_and_the_closure_follows` is left red: it is **red on trunk** (7 against an asserted 8), it belongs to another row, and this branch only changes its symptom |
| R9 | The committed tree is regenerated, and **existing modules change bytes** as well as new ones appearing: a class whose node states a rule gains an `_adcp_rules` line it did not carry |

### What I expect to be wrong

R1 and R2 are read off the nine node texts and not off a run, so the split between
them is the guess. `core/product-change-map.json` is the one I would bet against: its
`propertyNames` carries `x-entity` beside `minLength`, and I have not probed whether
the scalar arm's own screen passes an `x-` key at that position.

R6 assumes nothing else unlocks. A newly emitted mapping is a reference target, so
the floor may be beaten rather than hit — which is why both pins are re-measured on
the finished tree rather than computed from this arithmetic.

## 8. Measured (filled in after the build)

_pending_
