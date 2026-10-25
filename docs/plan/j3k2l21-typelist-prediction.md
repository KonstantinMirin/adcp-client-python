# `salesagent-j3k2l.21`, second dispatch: a union root whose branches are not objects

Written and committed BEFORE the change, graded against measurement in the same file.
Base: `7efac56cb` on `emit/from-scratch`. Branch: `sdk/j3k2l21-typelist`.

## The row's filed population is not the population, and the figure had to be re-measured

The row was filed over **24 documents**: 21 refused at a root on `type`, plus 3 refusing
because they declare `null` beside another type at a PROPERTY. The first dispatch on this row
landed — `49a818a64` and the staged merge `e92a5d11a` are both ancestors of this base, and
the merge was `--no-ff`, which is the only reason ancestry answers it — so that 24 predates
the tree I start from.

Re-measured here, by `codegen.emit.emit` over `bundle.portable(schemas/cache/3.2)`,
**1,054 portable documents**:

| family | denominator | count |
|---|---|---|
| roots whose `type` is a LIST | 1,054 portable documents | **0** |
| nodes anywhere whose `type` is a list containing `null` | 1,054 portable documents | 57 sites in 26 documents |
| of those 26 documents, emitted | 26 | 7 |
| of those 26 documents, pending | 26 | 3 (all on another document's `$ref` chain) |
| union roots (`bundle.union_root`) | 1,054 portable documents | 126 |
| of those, with at least one non-object branch | 126 | **4** |
| union roots carrying a `null` BRANCH | 126 | **0** |

So the row's literal title — a root `type` LIST — has **0 sites in this bundle**, and the
declared-`null`-at-a-property half is cleared: `core/webhook-activity-record.json`, the
document the row's description names as its example, EMITS here, and `compare_schema` reports
`added 0 / missing 0 / differs 0` over the graded pairs. **A `null` member of a `type` list is
already a type fact and not an absence at every one of those 57 sites**, which is D4's reading
and is what the first dispatch landed.

What is left of the row at this tree is the same job at the other spelling.
`{"type": ["string", "null"]}` and `{"anyOf": [{"type": "string"}, {"type": "null"}]}` are one
document, and a union OF SCALARS at a root is what `type`-list-at-a-root would have been. Four
documents sit there, all four PENDING on `type`:

| document | position | what it states | current refusal |
|---|---|---|---|
| `core/geo-place-system.json` | `/anyOf/0` | branch `{type: string, enum: [...]}`, branch `{type: string, format: uri, pattern: ^https://}` | `type`, DEFERRED, "a branch of type 'string' is step 6" |
| `core/geo-place-type.json` | `/anyOf/0` | the same shape | `type`, DEFERRED, same |
| `core/start-timing.json` | `/oneOf/0` | branch `{type: string, const: asap}`, branch `{type: string, format: date-time}` | `type`, DEFERRED, same |
| `core/macro-bearing-url.json` | `/` | root `type: string` beside `anyOf` of three typeless branches carrying only `format`/`pattern` | `type`, DEFERRED, "a union root of type 'string' is step 6" |

## What D2 decides, which is why this needs no decision of its own

D2: "A `oneOf`/`anyOf` → a base, one subclass per branch, and a union alias. Everything else is
an annotation or a rule: scalar → an annotation; … a root scalar or mapping → a module-level
alias." And: "A `RootModel` is avoided wherever anything else will do … so a scalar root is an
`Annotated` alias and never `RootModel[str]`."

Every instance all four of these documents admit is a **scalar**. By D2 that makes each one a
root scalar, and a root scalar is a module-level alias — §4 states the mechanism in those words:
"A root scalar is an annotation and not a class (D2), so it has no class to carry
`strict_validate`. Its module binds the same two halves as a module-level function over the same
`SchemaRef`." That is `compiler.declare_alias`, which `emit._scalar_root` already uses for the
bundle's five plain scalar roots.

The TYPE of that alias is the union of the branches' own decisions, which is
`lower.union.nested` — the function that already builds `A | B` for the identical keyword below
a root, and which `emit._decide` already reaches for every nested union. Nothing new is built:
the root case stops insisting on classes where the branches cannot be classes, and hands the
node to the reader that is already right for it.

**Where the `null` branch would land, stated although the bundle has none.** A `{"type": "null"}`
branch decides to `compiler.Type("None")` through `_decide`'s existing `kind == "null"` arm, so
such a root would alias to `str | None`. At a root that `| None` can only be a TYPE FACT — there
is no key for an absence to be the absence of — which is the half of D4 the row's title names,
and `_decide`'s own docstring states the other half: the `| None` the compiler adds to an
OPTIONAL PROPERTY is a fact about presence and not a claim that the document admits an explicit
null. Both halves are graded below.

**ROWS does not change and neither does any selector.** `bundle.union_root` already claims all
four; the question "class or alias" is a question about the BRANCHES, which only the lowering
reads. A seventh row would need a new root kind in `bundle.declares_its_own_root_kind`, and
`oneOf`/`anyOf` is already there. Rows stay six and the partition is unchanged.

## THE PREDICTION

| # | claim | predicted |
|---|---|---|
| P1 | `core/geo-place-system.json` emits | EMITS, as an alias |
| P2 | `core/geo-place-type.json` emits | EMITS, as an alias |
| P3 | `core/start-timing.json` emits | EMITS, as an alias |
| P4 | `core/macro-bearing-url.json` emits | **DOES NOT emit.** Its root `type: string` conjoins with every branch, and two of the three branches then state a `format`/`pattern` that `compiler.Type` has no slot for — `nested`'s own named refusal, DEFERRED to D5's alias module (the row that owns the 3 `format: hostname`, 2 `minItems` and 1 `maxItems` deferrals). It moves from a `type` deferral promising step 6 to the keyword that is the reason. |
| P5 | emitted, over 1,054 portable | 705 → **708** (+3) |
| P6 | verdicts, over 1,054 portable | 301 → **301** (+0). Nothing I do mints a verdict. |
| P7 | pending | 48 → **40** (−8): the 3 roots, plus 5 of their 9 chained dependents released |
| P8 | accounted (`emitted + verdicts`) | 1,006 → **1,009** |
| P9 | `compare_schema` over the graded pairs: `added` | **0**, unchanged. A fact the model ADDS is the direction that admits an invalid instance. |
| P10 | `compare_schema`: `missing` / `differs` | **0 / 0**, unchanged |
| P11 | graded pairs | 1,079 → grows. An alias root is one pair; the enum class each `geo-place-*` branch declares is another. Predicted **1,079 → 1,084**. |
| P12 | which clearances are CHAINED rather than my own emissions | of the released dependents, every one is chained: `core/geo-place-area.json`, `core/geo-place-requirement.json` (both on geo-place-system), `core/geo-place-catalog-entry.json`, `core/get-geo-place-resolution-request.json`, `core/get-geo-place-resolution-response.json` (on geo-place-type), `media-buy/update-media-buy-request.json` (on start-timing). The three that stay pending are the macro-bearing-url chain: `core/assets/pixel-tracker-asset.json`, `core/assets/url-asset.json`, `core/product-card-reference-asset.json`. |

P7 and P12 disagree by one on purpose: 6 chained dependents are named and 5 are predicted to
release, because `core/get-geo-place-resolution-response.json` chains through
`get-geo-place-resolution-request.json` and a two-link chain may or may not resolve in one pass.
That is the prediction I expect to be wrong, and it is written so the measurement says which way.

## MEASURED

Instrument: `codegen.emit.emit` over `bundle.portable(schemas/cache/3.2)` for the emit
numbers, and `codegen.harness.compare_schema` over `tests.test_emit.graded()` of the
REGENERATED tree for the comparison. Measured at `877516f66` (the lowering) with the tree
regenerated at `e467796f2`. The trunk merge `7950da42a` is docs-only, so these transfer.

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | `core/geo-place-system.json` EMITS | **VERDICT on `title` at `/`** | **WRONG** |
| P2 | `core/geo-place-type.json` EMITS | **VERDICT on `title` at `/`** | **WRONG** |
| P3 | `core/start-timing.json` EMITS | EMITS, as `Annotated[Literal['asap'] \| AwareDatetime, ...]` | right |
| P4 | `core/macro-bearing-url.json` does NOT emit; moves to a `format` deferral naming D5's alias module | DEFERRED on `format` at `/anyOf/0`, detail naming D5's alias module | right |
| P5 | emitted 705 → 708 | **705 → 710** | **WRONG, and low** |
| P6 | verdicts 301 → 301 | **301 → 305** | **WRONG** |
| P7 | pending 48 → 40 | **48 → 39** | **WRONG by one** |
| P8 | accounted 1,006 → 1,009 | **1,006 → 1,015** | **WRONG, and low** |
| P9 | `added` 0, unchanged | **0** over 1,084 pairs | right |
| P10 | `missing` / `differs` 0 / 0 | **0 / 0** | right |
| P11 | graded pairs 1,079 → 1,084 | **1,079 → 1,084** | right |
| P12 | 6 chained dependents named, 5 predicted to release | **7 chained documents moved, every one of them named in P12** | the caveat resolved the other way: the two-link chain DID release in one pass |

### The three things the prediction got wrong, and why

**1. A FIFTH DOCUMENT was in the population and the table had four.**
`core/media-buy-available-action-id.json` is a union of a bare `$ref` to an enum document and
a `{"type": "string", "const": ...}` branch — a scalar root by exactly the reading above — but
its refusal fired on `$ref` at `/anyOf/0` rather than on `type`, so partitioning the pending
set by KEYWORD did not show it. I found it by reading the 126 union roots for a non-object
branch rather than by reading the keyword profile, which is the instrument that should have
built the population in the first place: **the row is about a SHAPE and I enumerated it by the
keyword its refusal happened to name.** It was found before the change was written and after
the prediction was committed, and the prediction is left as committed.

It is the most interesting of the five. Its bare `$ref` branch is refused on the class path
for a reason that is TRUE there and false on the alias path — "the member would be the target's
own class, which does not descend from this base, so the arm would not answer isinstance" —
and on the alias path that arm is simply an import of the target's symbol. Three more
documents released through it, which is why emitted is +5 against a predicted +3.

**2. The two `geo-place-*` documents refuse, and D3 says they must.** Both branches lower to
annotations, so the alias is available; but branch 0 is an untitled `enum` node, which D2
makes a class, and D3 derives no name for it — title, discriminator `const`, required set, and
none applies. It takes the root's own name as its hint, the alias then wants the same name, and
`compiler.Module.declare` refuses the document with "two nodes in this document derive the
class name 'GeographicPlaceIdentifierSystem'". That is a VERDICT and the right answer; what it
reports is the collision rather than the gap, which the lowering's docstring records with the
measurement.

**Trunk confirmed this independently and after the fact.** Four commits landed on
`docs/plan/rebuild-plan.md` while this row was in flight, one of which gives D3's ladder a
fourth rung — the branch's own root type word — before its refusal, and states that the rung
"names a branch only where the root types differ". Both branches of both documents state
`string`, so the new rung refuses them too. Implementing rung 4 would not clear these two.

**3. The prediction treated a verdict as something the row would not mint.** P6 said verdicts
would not move. They moved by +4, which is +8 minus the 4 documents that stopped being
verdicts and emitted. Of the +8, 2 are the `geo-place-*` pair and 6 are chained refusals whose
target became a verdict rather than staying pending. A row that turns a DEFERRAL into a
VERDICT has done its job — the document is accounted for — and the prediction was written as
if only emissions counted.

### Emission and verdict-minting, stated apart and never added

| | |
|---|---|
| **emitted, re-measured** | 705 → 710 over 1,054 portable documents |
| of which THIS row's own emissions | **2**: `core/start-timing.json`, `core/media-buy-available-action-id.json` |
| of which CHAINED releases | **3**: `core/media-buy-available-action.json`, `core/product-allowed-action.json`, `error-details/action-not-allowed.json` — each a `$ref` to `media-buy-available-action-id` |
| **verdicts, re-measured** | 301 → 305 |
| of which THIS row's own | **2**: `core/geo-place-system.json`, `core/geo-place-type.json` |
| of which CHAINED | **6**: `core/geo-place-area.json`, `core/geo-place-requirement.json` (on geo-place-system); `core/geo-place-catalog-entry.json`, `core/get-geo-place-resolution-request.json`, `core/get-geo-place-resolution-response.json` (on geo-place-type); `media-buy/update-media-buy-request.json` (start-timing cleared, and its next blocker is a verdict) |
| less the 4 that LEFT the verdict set by emitting | −4 |
| **pending** | 48 → 39 |
| **accounted** | 1,006 → 1,015 |
| **graded pairs** | 1,079 → 1,084, `added 0 / missing 0 / differs 0` |

The 3 documents chained to `core/macro-bearing-url.json` stay pending and only their detail
text moves, because they quote their target's refusal: `core/assets/pixel-tracker-asset.json`,
`core/assets/url-asset.json`, `core/product-card-reference-asset.json`.

### The union-root population, which is what the check grades

| | denominator | count |
|---|---|---|
| union roots (`bundle.union_root`) | 1,054 portable documents | 126 |
| alias-shaped (the document says its instance is a scalar) | 126 | 5 |
| class-shaped | 126 | 121 |
| MIXED — a scalar instance AND a branch with a shape | 126 | **0** |
| union roots the committed tree carries | 126 | 40 (was 38) |
| of those, carrying `BranchDispatchMixin` | 40 | **38 — unchanged, which is §8** |
| of those, a module-level alias | 40 | 2 |
| union roots with a `null` BRANCH | 126 | 0 |
| roots whose `type` is a LIST | 1,054 | 0 |
| sites stating `null` inside a `type` list, below a root | 1,054 | 57 |

### Perturbation, one row per clause

Run by `perturb.sh`, which classifies by pytest's exit code and prints the first assertion
that fired, so an ERRORED run is never read as a caught perturbation. Baseline green.

| probe | what was broken | result |
|---|---|---|
| P-A | `declares_a_class` answers True for every branch | RED, clause 1: `['core/media-buy-available-action-id.json'] == []` |
| P-B | no root is alias-shaped | RED, clause 2: "no alias-shaped union root emitted" |
| P-C | one alias root moved back into the base half (39 / 1) | RED, clause 3: `39 == 38` — the pin the 40 total cannot absorb |
| P-D | clause 4 pointed at the BASE half | RED: `'A2UIBoundValue' not in {...}` — it is a ClassDef |
| P-E1 | the null-site count moved by one | RED, clause 5: `57 == 56` |
| P-E2 | the null-BRANCH test relaxed to any typed branch | RED, clause 5: the population asserted empty is not |
| P-F | **the alias dispatch removed from the lowering** | RED on this row's check (a `KeyError` from `_symbol` running the emitter against a tree that still carries the module — a red, and an error rather than an assertion) and RED on the step's arithmetic with `38 == 40`, which is the legible one |

### What moved in the suite besides the new check

`test_a_union_root_emits_a_base_plus_one_subclass_per_branch` and the seven shape tests beside
it asserted `BranchDispatchMixin` over every emitted union root, which is a claim about one of
D2's two shapes. They run over `emitted_union_bases()` now. That is the only behavioural change
to an existing test; the rest is three re-pointed pins in
`test_every_union_root_the_step_does_not_emit_is_refused_by_name_pointer_and_keyword`
(38 → 40, 88 → 86, and the refusal profile losing its `type` row), each named in place.
