# `salesagent-j3k2l.40` — prediction, written before the change

The conjunct reader moves out of `codegen/lower/product.py` and into
`codegen/compiler.py`, where D13 puts machinery two rows need, and a union branch
that composes reaches it through the import it already has. This file is the
prediction, committed before the implementation exists so the grade is against a
record and not against a recollection.

## Baseline, measured on `c9bfb5133`

Instrument: `codegen.emit.emit(BUNDLE, bundle.portable(BUNDLE))`, the whole
PORTABLE population, with a refusal's kind read off `Refusal.resolved` and never
off its sentence.

| | |
|---|---|
| portable | 1054 |
| emitted | 686 |
| refused | 368 |
| verdicts | 281 |
| **accounted** | **967** |
| pending | 87 |
| pending: deferred | 47 |
| pending: chained | 39 |
| pending: unresolved | 1 |
| direct pending (not chained) | 48 |

## The 22, counted from the producers and not from the headline

| n | producer | detail |
|---|---|---|
| 12 | `product.py`, last arm of the conjunct loop | "this step lowers a `$ref` conjunct (a base) or an inline conjunct with properties; a later D2 row lowers this one" |
| 10 | `union.py`, `_plan`'s `allOf` branch | "a branch that composes needs the bases its conjuncts name as well as the union base this row gives it, and the conjunct reader that binds them is the product row's" |

22 of 48 confirmed. **The two halves are not one capability, and this is the
issue's own premise corrected rather than a design decision questioned.**

### The 12 are misattributed and this move releases none of them

The product refusal is the loop's LAST arm — a conjunct whose shape no earlier
arm admits — so it fires identically wherever the loop lives. Reading all 12
conjunct nodes:

| conjunct keys | n | documents |
|---|---|---|
| `{oneOf}` of shapes | 3 | `formats/canonical/{display_tag,html5,image}.json` |
| `{anyOf}` of shapes | 3 | `formats/canonical/seller_rendered_stateful_display.json`, `governance/check-governance-request.json`, `media-buy/build-creative-request.json` |
| `{not, properties}`, `{not, properties, type}` | 2 | `core/{product-execution-requirement,media-buy-frequency-cap-requirement}.json` |
| `{required}` alone | 2 | `core/{collection-selection,placement-selection}.json` |
| `{type, properties, allOf, additionalProperties}` | 1 | `core/demographic-targeting-intent.json` |
| `{errorMessage, not}` | 1 | `media-buy/sync-catalogs-request.json` |

Each wants a new ARM: a conjunct carrying a combinator of shapes, a conjunct that
is fields and a rule at once, a `required`-only conjunct, a nested conjunct list,
and `errorMessage` (ajv-errors, which draft-07 does not define). None wants a
reader in a different module.

The 2 `{required}`-alone sites are why the sentence reads as if it did. The
module docstring says a required-only conjunct "is NOT built: there are **0** of
them at a root" — ROOT-scoped, still true at a root, and both of these sit at
`/oneOf/0/properties/collections/items/allOf/1` and
`/oneOf/0/properties/placement_refs/items/anyOf/0/allOf/1`, which `emit._decide`
reaches. The deferral the plan deliberately left, in a position the measurement
behind it never covered.

### `union.py`'s own comment says this move releases 0, and it is stale

Lines 758-766 claim "the reachable population of that move is 0 TODAY, measured
by making this refusal fail ... over all 9 documents in this position: 0 emit",
and conclude the move would be a derivation matching nothing (D14). That probe
re-run on `c9bfb5133` — `_plan` monkeypatched to drop a composing branch's
`allOf`, which is what the move supplies, over a population that is now 10 and
not 9:

| | trunk | conjuncts dropped |
|---|---|---|
| emitted | 686 | 692 |
| verdicts | 281 | 296 |
| accounted | 967 | 988 |
| pending | 87 | 66 |

| document | under the probe |
|---|---|
| `core/canonical-media-buy-action.json` | EMITS |
| `core/canonical-optimization-goal.json` | EMITS |
| `core/publisher-property-selector.json` | EMITS |
| `core/targeting-modification.json` | EMITS |
| `core/delivery-metric-aggregate.json` | VERDICT — a base that is a scalar alias |
| `core/optimization-goal.json` | VERDICT — a base that is a scalar alias |
| `core/postal-area.json` | VERDICT — two nodes derive `PostalArea` |
| `adagents.json` | chained to a VERDICT |
| `core/tracker-execution-selector.json` | chained to a VERDICT |
| `brand.json` | still DEFERRED — a branch declaring no property, step 7's row |

The comment predates the branch rows. It is replaced in this change by the probe
above, and the conclusion it drew is inverted: the move's reachable population is
9 of 10 directly and 12 more through chains.

## The prediction

**This is the probe's number, and the probe DROPS the conjuncts where the
implementation BINDS them.** That is the one asymmetry, and it runs in one
direction: binding a conjunct can refuse (an alias base, a refused `$ref` target,
a restatement that neither matches nor narrows) where dropping it could not. So
the four EMITS are the rows most likely to be wrong, and wrong downward.

| | before | after |
|---|---|---|
| portable | 1054 | 1054 |
| emitted | 686 | **692** |
| verdicts | 281 | **296** |
| accounted | 967 | **988** |
| pending | 87 | **66** |
| `comparison.added` | 0 | **0** |

* **the 22**: 9 of the 10 union documents clear — 4 emitted, 5 accounted as
  verdicts — and `brand.json` stays deferred on step 7's row. **0 of the 12
  product documents clear**, and they are reported as their own row, not added to
  this one.
* **the 39 chained, counted SEPARATELY**: 12 release. 2 of the 12 become
  emissions and 10 become verdicts. Pending falls 87 → 66 = 9 direct + 12
  chained.

## What must grade, and how it is probed

1. **The shared reader is reached by BOTH rows.** Break it — one arm of the
   conjunct classification — and the product row and the union row must BOTH
   redden. A reader shared by two callers that only one test reaches is
   half-graded, and the probe is the only thing that says which.
2. **`comparison.added` stays 0.** A composing branch that gains its conjuncts'
   bases must not become narrower than its document at any pointer.
3. **D13 is not widened.** `codegen/lower/union.py` still imports
   `codegen.compiler` and `codegen.refusal` and nothing else of the package, and
   `tests/test_import_rule.py` is the thing that says so, unchanged.
