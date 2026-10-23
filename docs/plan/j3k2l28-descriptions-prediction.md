# salesagent-j3k2l.28, second half — the `description` divergence

Started from trunk **9e9da67e1c7c6dc885c096aad238330a2043bf32**
(`Merge sdk/j3k2l26-below-root: the deferral set is empty, 1053 of 1054 accounted`),
clean. Branch `sdk/j3k2l28-descriptions`.

The issue's first half — the fifth resolver canonicalization, folding `required: []`
and `enum: [false, true]` at a declared boolean — is on this base already
(`harness._constrains_nothing`, `tests/test_comparison_folds.py`). It is not
re-opened here. `codegen/harness.py` is another lane's and is not touched.

## 0. The baseline, re-measured on that tree

The comparison alone, `max_steps=0`, over the whole graded population:

| figure | value | denominator |
|---|---|---|
| graded pairs | 1,034 | — |
| added | 0 | — |
| missing | 11 | — |
| differs | 43 | — |
| emitted | 686 | 1,054 portable |
| accounted | 1,053 | 1,054 portable |

**The issue's figures are stale and the population moved.** It states `missing 10`
and `differs 13` over 808 pairs; this tree grades 1,034 pairs with `missing 11` and
`differs 43`. The brief's claim that the first half took `missing` to 0 does not hold
on this base either: 11 remain, in two shapes neither of which is this half's —
9 `enum: [False, True]` that the fifth canonicalization's `type == "boolean"` gate
does not reach, and 2 `additionalProperties/description`.

## 1. The partition of the 43, by pointer — MEASURED, not predicted

| facts | pointer | family |
|---|---|---|
| 15 | `/properties/context/description` | **C** |
| 5 | `/properties/slots/description` | F |
| 5 | `/properties/v1_translatable/description` | F |
| 4 | `/properties/experimental/description` | F |
| 7 | `/properties/slots/default` | F |
| 4 | `/properties/v1_translatable/default` | F |
| 3 | `/properties/experimental/default` | F |

Two families, not one, and the keyword does not name them:

- **C — 15 facts, and this half's whole scope.** 15 response documents whose root
  composes `core/protocol-envelope.json` as an `allOf` base AND declares `context`
  in their own `properties` as a bare `$ref` to `core/context.json`. The field is
  INHERITED (`lower_product._restatement` reads the restatement as saying the same
  thing, correctly — both declarations' constraining content is the same `$ref`), so
  the class carries the BASE's `Field(description=...)`: the long envelope text, which
  `core/protocol-envelope.json` states as a SIBLING of its own `$ref`. The document
  states, at the pointer the comparison grades, the TARGET's own short text.
- **F — 28 facts, 14 `description` and 14 `default`, and NOT this half's.** 7
  `formats/canonical/*.json` documents restate an inherited property with nothing but
  a `default` and a `description`; `_constraining` is empty, so the restatement says
  nothing, the field is inherited, and the subclass's own two annotations are dropped.
  This is `salesagent-j3k2l.22`'s measured mechanism (it reports the `default` half,
  including two inversions where the model's boolean default is the opposite of the
  document's), and the `description` half is the same sites in the same files through
  the same branch. Splitting it would put two lanes in one `elif`.

## 2. The decision

Recorded in `docs/plan/rebuild-plan.md` §6. In short:

**A description a document states at a pointer governs what the model renders at that
pointer. It reaches the field from the node the document declares there — the node's
own sibling where it states one, the `$ref` target's where it does not — and never
from a composed base's declaration of the same key.**

The sub-question the ticket poses — a referring document's own `description` beside a
`$ref` versus the target's — is already answered in the tree and is CONFIRMED rather
than changed: the sibling wins. `compiler.fields` reads the node's own `description`,
the resolver the harness grades through merges a `$ref`'s siblings with the outer keys
winning, and `core/protocol-envelope.json`'s own pair is green on exactly that reading.
Draft-07's "a `$ref` ignores its siblings" is why a CONSTRAINT sibling refuses by name
(`emit.decide_type`); for an annotation the bundle plainly intends it, and no accepted
set moves either way.

## 3. The change

One branch in `lower_product.lower_composition`'s merge. A restatement that
`_restatement` reads as `False` splits in two:

- its constraining content is EMPTY (family F) — unchanged, the field is inherited;
- its constraining content EQUALS the base's and is non-empty, and the two declarations
  render a different field annotation — the SUBCLASS states the field. The type is
  decided from a node with the base's own constraining content, so it is the base's
  type and there is no shadow; what changes is only which document's annotation
  reaches the field.

## 4. The prediction

| figure | before | predicted after |
|---|---|---|
| graded pairs | 1,034 | 1,034 |
| added | 0 | **0** |
| missing | 11 | **11** |
| differs | 43 | **28** |
| emitted | 686 | 686 |
| accounted | 1,053 | 1,053 |

- The 15 C facts clear; the 28 F facts stay, every one of them.
- No document starts or stops emitting, so no `.py` or `.json` goes stale and
  `emit.write`'s write-only behaviour (`salesagent-j3k2l.30`) costs nothing here.
- 15 emitted modules change, each gaining one `context` field line. No module loses one.
- The per-change gate stays green at 27 passed, plus the negative tests added here.
- The risk I can name: a re-emitted field whose requiredness or nullability differs
  from the base's would move `added` off 0. I predict it does not, because `context`
  is optional in every one of the 15 and `fields` re-unions the inherited required set.
- The probe: a fixture document stating a `description` beside a `$ref` that disagrees
  with its target's, emitted with the WRONG text, must report a `differs` at that
  pointer. A description rule that cannot produce one is not a rule.
