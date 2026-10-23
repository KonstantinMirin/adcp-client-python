# `salesagent-j3k2l.37` — prediction, written before the change

A refusal's KIND becomes a required argument its producer declares, and
`refusal.is_a_verdict` reads the kind and nothing else. This file is the
prediction, committed before the implementation exists so the grade is against a
record and not against a recollection.

## Baseline, measured on `d9989750c`

Instrument: `codegen.emit.emit(BUNDLE, bundle.portable(BUNDLE))`, the whole
portable population, with `Refusal.__init__` monkeypatched to record the caller's
`file:lineno` so every refusal is attributed to the PRODUCER that raised it
rather than to its sentence.

| | |
|---|---|
| portable | 1054 |
| emitted | 686 |
| refused | 368 |
| deferred (`DEFERRED_TO_A_LATER_ROW`) | 0 |
| transitive (`UNRESOLVED_TARGET`) | 1 |
| chained, resolved to pending | 0 |
| verdicts (`is_a_verdict`) | 367 |
| **accounted** | **1053** |

29 producers fire over the population. 28 of them produce the 367 verdicts; the
29th (`emit.py:1066`) produces the 1 transitive.

## The classification, which is what is being predicted

The rule applied to every site, stated once so each row below is one line of
justification rather than a fresh reading:

> **DEFERRED** when the refusal's own reason is that the lowering for this
> position has not been written or cannot be reached from here — it names a row,
> a step, a module or a mechanism that would clear it. **VERDICT** when the
> reason is a property of the document, of pydantic, or of the pointer space
> that nothing this emitter can write changes.

`CHAINED` is neither: it takes the kind of what it is chained to, by carrying the
target refusal rather than by re-reading the target's quoted sentence.

### The 29 live producers

| producer | n | kind | why |
|---|---|---|---|
| `emit.py:973` | 171 | CHAINED | `its target X is refused: <X>` |
| `union.py:337` | 61 | VERDICT | `ROOT_CONJUNCTS`: there is no pointer to the conjunction for a branch class to name |
| `compiler.py:1148` | 19 | VERDICT | `_NESTED_SIBLING`, whose own docstring says "why it is a verdict rather than a deferral" |
| `product.py:315` | 18 | VERDICT | a restatement that neither matches nor narrows: the intersection is the document's, and no annotation carries it |
| `product.py:231` | 15 | VERDICT | a scalar root is an `Annotated` alias and subclassing one is a `TypeError` |
| `product.py:289` | 12 | **DEFERRED** | "a later D2 row lowers this one" |
| `union.py:741` | 10 | **DEFERRED** | "a branch composes once that reader is shared machinery in `codegen.compiler`" |
| `containers.py:223` | 8 | VERDICT | `_DISTINCT_HAS_NOWHERE_TO_LIVE`; the call site's own comment says "this refusal is final" |
| `union.py:688` | 7 | VERDICT | a bare `$ref` branch's member would not answer `isinstance` |
| `containers.py:389` | 7 | VERDICT | `_PATTERN_KEY`: "a keyword no row lowers rather than one a later row will" |
| `union.py:668` | 6 | **DEFERRED** | "teaching the fold ... is the harness's row" |
| `union.py:570` | 5 | **DEFERRED** | "the fix is the document-side reading in `codegen/harness.py`" |
| `emit.py:818` | 4 | VERDICT | a root declaring no schema keyword at all; the comment says "with no promise of a row" |
| `union.py:706` | 3 | **DEFERRED** | "a branch of type X is step 6" |
| `containers.py:197` | 3 | **DEFERRED** | "D5's shared alias module is the row that lowers it" |
| `emit.py:826` | 3 | VERDICT | "no D2 row lowers that kind at a root", written to replace a text that "asserts a schedule" |
| `emit.py:519` | 2 | VERDICT | pydantic refuses a string constraint on a URL type |
| `compiler.py:1219` | 2 | **DEFERRED** | "step 7's rule, not a field" |
| `union.py:506` | 2 | **DEFERRED** | "D5's alias module ... has no spelling for this shape" |
| `emit.py:1066` | 1 | UNRESOLVED | `UNRESOLVED_TARGET` |
| `emit.py:950` | 1 | VERDICT | a local reference is not a binding; the mechanism that resolves one already exists |
| `emit.py:994` | 1 | **DEFERRED** | "the step whose population reaches one decides whether the chain is followed" |
| `containers.py:275` | 1 | VERDICT | two value schemas for one mapping value type |
| `containers.py:289` | 1 | VERDICT | `_PATTERN_KEY` reached from the other spelling |
| `union.py:347` | 1 | **DEFERRED** | "a union root of type X is step 6" |
| `compiler.py:1263` | 1 | **DEFERRED** | "the step whose population reaches one decides between `json_schema_extra` and refusing" |
| `product.py:135` | 1 | VERDICT | no pointer to the conjunction of a conjunct list with a branch list |
| `product.py:174` | 1 | VERDICT | an `allOf` of type `array` composes no object |
| `compiler.py:1058` | 1 | **DEFERRED** | "a comparison row for the added fact is the harness's to write" |

`compiler.py:1148` is `check_keywords`, which is one raise site with THREE
reasons: `_NESTED_SIBLING` and the other caller-supplied `why` strings, the
"draft-07 defines no such keyword" verdict, and `DEFERRED_TO_A_LATER_ROW`. Its
kind therefore cannot be a property of the line — it comes from `_why` and from
the caller, which is the one place in this change where the kind travels with the
reason rather than with the site.

Lowest-confidence rows, named so a reader can audit them rather than discover
them: `emit.py:950` (1 document — the named mechanism exists, so no row is
missing, but the position is reachable and arguably should not be), and
`compiler.py:1263` (1 document directly and 5 more through chains — the detail
asserts "no rendering", while the comment above it names `json_schema_extra` and
says a later step decides; the comment is what makes it a deferral).

### The chains, measured on trunk by walking `__cause__`

171 chained refusals, attributed to the producer at the ROOT of each chain:

| root producer | n | resolves to |
|---|---|---|
| `union.py:337` | 41 | VERDICT |
| `product.py:231` | 32 | VERDICT |
| `compiler.py:1148` | 21 | VERDICT |
| `product.py:315` | 12 | VERDICT |
| `union.py:741` | 12 | DEFERRED |
| `containers.py:223` | 11 | VERDICT |
| `union.py:688` | 7 | VERDICT |
| `union.py:706` | 6 | DEFERRED |
| `compiler.py:1263` | 5 | DEFERRED |
| `containers.py:389` | 5 | VERDICT |
| `product.py:289` | 4 | DEFERRED |
| `union.py:668` | 3 | DEFERRED |
| `union.py:347` | 3 | DEFERRED |
| `union.py:570` | 3 | DEFERRED |
| `emit.py:826` | 3 | VERDICT |
| `compiler.py:1058` | 2 | DEFERRED |
| `compiler.py:1219` | 1 | DEFERRED |

39 of the 171 resolve to DEFERRED, 132 to VERDICT, 0 to UNRESOLVED.

## The prediction

**By DECLARED kind** (what the producer passed):

| kind | documents |
|---|---|
| VERDICT | 149 |
| DEFERRED | 47 |
| UNRESOLVED | 1 |
| CHAINED | 171 |
| total | 368 |

**By RESOLVED kind** (a chain takes its target's):

| resolved kind | documents |
|---|---|
| VERDICT | 281 |
| DEFERRED | 86 |
| UNRESOLVED | 1 |
| total | 368 |

**The metric:**

| | before | after |
|---|---|---|
| portable | 1054 | 1054 |
| emitted | 686 | 686 |
| verdicts | 367 | **281** |
| accounted | 1053 | **967** |
| pending | 1 | **87** |

`accounted` falls by **86** and pending rises from 1 to 87. 86 documents move out
of `verdict`: 47 directly and 39 through a chain. `emitted` does not move — this
change touches no lowering — and `comparison.added` stays 0.

The number falling is the instrument working. The pins in
`test_a_refusal_that_is_a_verdict_is_counted_apart_from_one_that_is_pending` move
WITH it (accounted grow-only `>= 1053` becomes `>= 967`, the pending pins
shrink-only at the measured values), and section 7.1 of the plan is rewritten to
these figures.

## What must grade, and how it is probed

1. **A fifth kind cannot be absorbed.** The partition is built from three named
   sets of `Kind` members — final, pending, delegating — and the test asserts
   those three sets are pairwise disjoint and their union is `set(Kind)`. Adding
   a `Kind` member reddens that assertion before any document is counted.
   Probe: add a producer raising a new `Kind`, show the assertion fails, show it
   passes once the kind is named in one of the three sets.
2. **A chain onto a newly pending kind resolves to pending, not verdict.** Probe:
   a refusal chained onto a `DEFERRED` target reports `resolved == DEFERRED`.
3. **`is_a_verdict` reads no text.** Its parameter is a `Kind`; there is no
   string in its body and no constant for it to compare against.
