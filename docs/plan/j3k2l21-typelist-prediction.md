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

(filled in after the change, in this same file)
