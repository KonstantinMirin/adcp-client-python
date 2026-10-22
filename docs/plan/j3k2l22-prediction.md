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

_pending_
