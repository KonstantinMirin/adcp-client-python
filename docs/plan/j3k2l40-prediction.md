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

---

# The grade

Measured on `db53576b0`, over the same 1,054 PORTABLE population and the same
instrument. Trunk did not move while this ran — `emit/from-scratch` is still
`c9bfb5133` and is an ancestor of this branch — so the before column is the
baseline above and not a re-reading of a different tree.

## The metric

| | predicted | measured |
|---|---|---|
| portable | 1054 | 1054 |
| emitted | **692** | **691** |
| verdicts | **296** | **297** |
| accounted | 988 | 988 |
| pending | 66 | 66 |
| `comparison.added` | 0 | 0 |
| the 10 union documents that clear | 9 | 9 |
| of the 39 chained, released | 12 | 12 |
| of the 12 product documents, released | 0 | 0 |

`comparison.added` is measured over every pair of the REGENERATED tree — 1,055
pairs, 36,060 document facts and 12,840 model facts compared — not carried over
from trunk.

## Four predictions were wrong, and all four in the same way

Every one of them came from grading the move by the probe that DROPS a composing
branch's conjuncts, where the implementation BINDS them. The prediction named
that asymmetry and named the four EMITS as the rows most likely to be wrong. The
direction was right and the specifics were not.

**1. 692 emitted, not 691; 296 verdicts, not 297.** Both off by the same one
document. `core/canonical-media-buy-action.json` EMITS with its conjuncts dropped
and is a VERDICT with them bound — which is the asymmetry doing exactly what was
predicted of it, on a document the prediction put on the other side.

**2. The holdout is `adagents.json`, not `brand.json`.** The prediction had
`brand.json` staying deferred on step 7's row and `adagents.json` chaining to a
verdict. Measured: `brand.json` is a VERDICT (`allOf` at
`/definitions/default_language/allOf/0` — a base that is a scalar alias), and
`adagents.json` is DEFERRED. Both moved, in opposite directions, and the net of 9
of 10 held by coincidence rather than because the composition was right.

**3. The product row's deferral GREW, 12 → 13, and nothing predicted that.**
`adagents.json` is the thirteenth. It cleared the union row — the branch composes
and is lowered — and landed on the NEXT gap, which is the conjunct-shape gap the
other 12 are on. So "0 of the 12 clear" is right and incomplete: the row they are
on gained a document from the row this change cleared. The prediction treated the
two rows as independent and they are sequential.

**4. Three pins moved in files this change does not touch, and the prediction
listed none of them.** `tests/test_applied_schema.py` (emitted 686),
`tests/test_fragment_ref.py` (a refusal inside a section, 8) and
`tests/test_emit.py`'s union census (34 / 92 and its keyword profile) each hold a
population figure this change moves. Each was re-measured in one pass and
re-pinned with the reason; `tests/test_emit_product.py`'s own N moved too (576 →
581) and is the one case where only ONE of a test's figures moved, which is what
attributes the +5 to the union row rather than to the product row.

## What the probe got right, and the comment it refutes

`union.py`'s claim that the move's reachable population is 0 is refuted either
way: 9 of 10 directly and 12 through chains, by the implementation and by the
probe. The conclusion the comment drew from it — that the move would be a
derivation matching nothing (D14) — was a measurement taken before the branch
rows landed, and it is replaced in the code by the run that refutes it.

## The reader's second caller was ungraded, and is not now

The `bases` prepend **is** a derivation matching nothing in the bundle today, and
that is a different fact from the one the comment asserted. All 3 composing
branches the bundle emits carry inline conjuncts only, so no emitted class has a
union base plus a conjunct's base and the prepend ORDER was graded by nothing.
Two tests on a hand-built bundle close it
(`tests/test_emit_product.py`):

* the order is asserted on `__bases__`, `__mro__` and the rendered class line,
  with the inherited field beside it. Probed by inverting the prepend: both
  orders give a legal MRO, so nothing refuses at import and the assertion is the
  only thing that separates them;
* **one break in the reader reddens BOTH callers** — `$ref` added to
  `compiler.ANNOTATIONS`, so a bare `$ref` conjunct carries no live keyword — each
  at its own conjunct pointer, with a control run first so a red is the break and
  not the probe.

## The 39 chained, counted apart

12 of the 39 chain onto the union row and all 12 released: 2 became emissions and
10 became verdicts. 4 of the 39 chain onto the product row's conjunct-shape
deferral and none released, which is consistent with 0 of that row clearing. The
remaining 23 chain onto other rows and did not move. **The 12 are release, not
this row's work, and are not added to the 9.**
