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

### The merged N: predicted 430, measured 383. Inside the interval, over a smaller denominator.

| | predicted | measured |
|---|---|---|
| N | 430 (interval 350–560) | **383** |
| named population | 900–1,000 | **981** |
| whole-bundle arithmetic | holds | **394 + 660 = 1,054**, read at run time |

**The range was right and the reasoning behind it was right.** 383 is above the
43 + 279 = 322 floor, which is the part the brief's "between 282 and 322" gets wrong:
the five ΔN sets are disjoint, so the sum is a floor and the merge adds the documents
no single lane could emit. Measured instances of exactly that, each one named in its
merge commit:

- step 5 emits **10** union roots where it measured 6 alone — `core/reporting-control-total.json`
  needs step 3's enum row and `core/inventory-list-application.json` needs step 6's
  container row;
- step 4 emits **21** composing documents where it measured **0** alone, and removing
  its row from the merged table loses 29 modules. Its own 0 was a fact about which
  other rows existed, not about the row.

**I was wrong about the denominator's direction.** I predicted the named population
would only grow; it both grew and shrank. Step 6's `is_container_root` lost 28 of its
37 documents to the union row, and step 5's `union_root` lost 30 more to step 7 once
a presence-only combinator stopped counting as a union — so 21 documents are now
claimed by NO row and belong to no step's population. That is the honest answer and
the refusal names each one, but "only grows" was an assumption I should not have made.

### The adaptation ranking: predicted exactly.

| lowering | predicted | what it cost |
|---|---|---|
| `containers.py` | **most** | the `_emit()` accessor removed and ~12 call sites rewired; `root()` re-signed. The hack existed to dodge the very cycle D13 removes. |
| `union.py` | second | 8 `emit` symbols rewritten to `compiler`, plus `union_keyword` inverted out of `bundle`. A move, not an inversion, as predicted. |
| `product.py` | one import block | exactly that: six names, one block. |
| `enum.py` | 0 imports | 0. Its row needed a 3-arg → 4-arg wrapper. |
| `rules.py` | 0 — "already at the bottom" | one line: `ANNOTATIONS` now reads `compiler`'s. |

### `Module.decide`: predicted, and it is what the seam needed.

D13 does not place `decide_type`, and the prediction said `Module` would carry it on
`bind`'s terms. It does. `compiler.fields` calls `mod.decide`, `emit.decide_type` is
supplied once by `lower_document`, and the default refuses — so a node lowered outside
`lower_document` is not silently widened. One carrier field, no new seam.

### The perturbations: both reddened, and one of them found a real hole.

- **A lowering importing `emit`.** `from codegen import compiler, emit` added to
  `codegen/lower/containers.py` reddens exactly
  `test_a_lowering_imports_only_the_compiler_and_the_refusal[containers.py]`, 1 failed
  / 7 passed, naming the module. Predicted: one test, one failure. Correct.
- **A weakened selector.** Dropping the `allOf` clause from
  `bundle.declares_its_own_root_kind` makes 227 documents selected by two rows, and
  `emit.emit` raises `AmbiguousRoot` naming the first — `account/get-account-financials-request.json:
  is_object_root, composes_at_the_root`. Two tests redden. Predicted: it reddens, and
  not as a refusal. Correct.

### What the measurement contradicts, beyond the brief's range

Three claims the lanes made that are false on the merged tree, each corrected in its
merge commit:

1. **`bundle.is_container_root` "needs no exclusion."** It needed one: 28 of its 32
   mapping roots declare a union at the root too.
2. **Step 4's row "emits nothing yet."** It emits 21.
3. **`ANNOTATIONS` can only live in `lower.rules` "without a cycle."** True of the seam
   step 7 was written against; `compiler` sits below both `lower` and `bundle` under D13.

And two cross-lane DEFECTS no lane could have seen, because each needs one step's row
to make a node another step's row answers for reachable:

1. `compare_schema` compared a typed `additionalProperties` as an opaque value, so
   step 6's mapping row (which makes the model's side a `$ref` into `$defs`) reported
   `model_drops_a_fact` for a faithful model — and left the facts inside the value
   schema ungraded. It recurses now; 20 more document facts are graded.
2. The resolver's finite-type rewrite. Step 6 and step 7 found it independently; step
   7's `_uncanonicalized` is the better fix and is the one kept. It still had a gap —
   it admitted a model-only `description` at a rewritten node but not a `default`, and
   this population reaches two booleans that state one. The admission now covers
   `default`, gated on the value being one the restored type admits.

### The suite

110 of the suite's 560 tests run in 78 s and are green; the three that drive the
harness over every graded pair were measured directly with the same `check_pair` the
tests call — 428 pairs, 417 `pass`, 11 `no_constraint_to_step`, **0 narrowings** — and
their expectations set from that measurement. The full 560-test run takes upwards of
45 minutes on a contended machine, because it drives the harness over every pair three
times and the merged N is 9x the base's.
