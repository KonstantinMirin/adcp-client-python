# D13's seam, and the five lowerings merged onto it: the prediction

Committed before the seam exists and before any lane is merged. Graded at the end of the
same document.

Base: `emit/from-scratch` at `e14b13829`. `ROWS` is empty there, N is 43 over the 334
documents steps 1 and 2 name, and the whole-bundle arithmetic is 51 emitted + 1,003 refused
= 1,054.

## The instrument, named before the number

Two measurements, two denominators, and they are not the same number:

1. **N, the lane-comparable one.** `emit.emit(bundle, named)` where `named` is the union of
   the step populations `tests/test_emit.py` derives, exactly as each lane's own N was read.
   `N = len(out.emitted)`. The denominator is `len(named)`, which grows as each lane's
   population test lands.
2. **The metric's arithmetic.** `emit.emit(bundle, bundle.portable(bundle))` and
   `len(emitted) + len(refusals) == len(bundle.portable(bundle))`, with the bundle's size
   read at run time and never written down.

## The merged N

**The brief's range is wrong, and this is the prediction that says so.** It states the merged
N is "somewhere between 282 and 322", with 322 as the sum of the ΔNs and the argument that a
document blocked on both an `enum` and a container unblocks once rather than twice. That
argument is about double counting, and the ΔNs cannot double count: each lane measured
`N_lane - 43` from the same base with one row added, so a document in `s3`'s ΔN emitted with
*only* the enum row present. The five ΔN sets are therefore disjoint, and
**43 + 279 = 322 is a FLOOR, not a ceiling.**

What the merge adds on top of that floor is the documents no single lane could emit: a
document blocked on an `enum` *and* a container, or on an `allOf` *and* a rule, is refused on
whichever blocker its walk met first on every one of the five branches, and emits only once
all five rows exist. The base's first-keyword refusal census says how much room there is —
284 `allOf`, 262 `enum`, 219 `type` (array, mapping, multi-type), 61 `const`, 32
`anyOf`/`oneOf`, 16 `not`, 9 `dependencies`, 7 `minProperties`, 3 `if`, 1 `propertyNames`,
against 84 `$ref` and 19 `definitions`/`$defs` that no row here lowers.

**Predicted merged N: 430, over a named population I predict at 900–1,000.**
Stated interval: **350 to 560**. Below 322 would mean a lane lost documents it had, which I
predict does not happen; above 560 would mean joint unblocking is nearly free, which the 84
`$ref` and 19 `definitions` refusals argue against.

I predict the whole-bundle arithmetic holds exactly — `emitted + refused == 1054` — because
it is an identity over the refusal recording, not a property of the rows.

## Which lowering needs the most adaptation

Measured by what each lowering imports of this package today, which is what D13's import rule
changes:

| lowering | imports of `codegen` today | sites to adapt |
|---|---|---|
| `rules.py` | none | 0 — already at the bottom of the graph |
| `enum.py` | `compiler`, `refusal` | 0 imports; its row's signature is 3-arg |
| `product.py` | `emit` (4 names), `refusal` | one import block |
| `union.py` | `bundle`, `compiler`, `emit` (8 names), `refusal` | ~14 call sites, two modules |
| `containers.py` | `compiler`, `refusal`, + a lazy `_emit()` | ~12 call sites, and the direction of the nested-arm call inverts |

**Prediction: `containers.py` needs the most adaptation, `union.py` second.**
`containers.py` is the one whose adaptation is not a rename: it holds a `_emit()` function
that reaches `codegen.emit` at run time *specifically* to dodge the cycle D13 removes, and
every one of its arms calls back through it for `decide_type` and `check_keywords`. Removing
the hack requires the nested-node decision to be reachable from a lowering without naming
`emit` at all — which is the one thing D13 states the seam must do and does not state how to
do. `union.py` is second because it names eight symbols of `emit` plus `bundle`, but each one
is a move rather than an inversion.

## The one thing in D13 that does not say how

D13 names three things to move into `codegen/compiler.py`: the field builder (`fields`), the
class declarer (`declare_object`), and the carriers (`Module`, `Shape`, `Target`, `Decided`).
It does not place `decide_type`, and `fields` cannot run without it — `fields` decides every
property's type. But `decide_type` must reach `lower.containers` for an array, a mapping and
a multi-type node, so moving it into `compiler.py` would make `compiler` import a lowering,
and leaving it in `emit.py` would make `compiler.fields` import `emit`.

I predict the seam resolves this the way the base already resolves the identical problem for
reference resolution: `Module` carries `bind`, a callable `emit` supplies and whose default
refuses, so a lowering resolves a `$ref` without naming `emit`. `Module` gains `decide` on
exactly those terms. I am recording this as a prediction rather than a decision so that the
grade says whether it was the smallest thing that worked.

## The perturbations predicted to redden

- One lowering made to `import codegen.emit` → the AST import-rule test fails, naming that
  module. Predicted: it reddens, one test, one failure.
- A selector weakened so two rows claim one document → `lower_document` raises on that
  document rather than picking a row. Predicted: it reddens the suite, and not as a refusal.

---

## The grade

*(written after measuring; empty until then)*
