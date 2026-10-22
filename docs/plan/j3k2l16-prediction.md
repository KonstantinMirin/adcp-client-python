# salesagent-j3k2l.16 — emit a `const` node as a `Literal`: the prediction

Committed before the lowering exists, so the grading below is against a record and
not against a recollection.

Branch `sdk/j3k2l16-const-literal`, off `emit/from-scratch` at
**`63dc1bb68c181d5bbc233a44f42dcecb0f9efab7`**, clean. Every number here is
predicted against that tree.

## The baseline, measured at `63dc1bb68`

Pre-state facts, measured before this file was written. Denominators, not results.

| fact | value | instrument |
|---|---|---|
| portable documents | 1,054 | `bundle.portable(BUNDLE)` |
| emitted, whole population | 401 | `len(emit.emit(BUNDLE, bundle.portable(BUNDLE)).emitted)` |
| refused, whole population | 653 | `len(...refusals)`; 401 + 653 = 1,054 |
| refusing on `const` | 75 | that run's refusals, keyed by `keyword` |
| committed tree, modules | 390 | `tests/test_emit.py` |
| graded pairs **N** | 462 | `test_the_step_result_is_counted_over_the_whole_population` |
| of which `pass` | 450 | same test |
| of which `no_constraint_to_step` | 12 | same test |
| `added` / `missing` / `differs` | 0 / 0 / 0 | same test |

The 75, by where the refusing node sits: **74 at a property** (72 directly at
`/properties/<k>`, 2 deeper inside a property's own object) and **1 at a `oneOf`
branch's property**. All 75 carry the same detail, `this step lowers no such keyword
(a later D2 row does)`, and no later row exists.

## The whole-bundle `const` census, measured at `63dc1bb68`

Over all 1,054 documents, at every schema position `bundle.nodes` reaches:

| fact | value |
|---|---|
| `const` nodes | 1,486, in 347 documents |
| **`const` at a document ROOT** | **0** |
| nodes carrying both `const` and `enum` | 0 |
| distinct key sets | `const` 826, `const type` 397, `const description type` 257, `const description` 6 |
| keywords beside `const` needing a decision | **none** — every one of the 1,486 states only `const`, `type` and `description` |
| `const` value types | `str` 1,310, `bool` 161, `int` 15; no `null`, no object, no array |
| nodes whose `type` word disagrees with the `const`'s own JSON type | 0 |

**0 roots is why this row is not an entry in `emit.ROWS`.** The bead's dispatch
paragraph is the epic's standing instruction; it binds a row that claims a ROOT
KIND, and `const` claims none. No selector goes into `codegen.bundle`, nothing is
added to `declares_its_own_root_kind`, and the "1,033 claimed once, 21 by none, 0
twice" partition is untouched by construction rather than by a check. If a root ever
carries one, `is_scalar_root` already selects it (its `type` names a scalar and it
declares no kind of its own) and D2's alias row lowers it through the same
`decide_type` arm — so the upgrade path is an exclusion clause, not a new row.

## What pydantic renders for a `Literal`, measured not assumed

On the pinned `pydantic==2.13.5`, `TypeAdapter(T).json_schema()`:

| `T` | rendered |
|---|---|
| `Literal["collection_list_changed"]` | `{"const": "collection_list_changed", "type": "string"}` |
| `Literal[3]` | `{"const": 3, "type": "integer"}` |
| `Literal[True]` | `{"const": true, "type": "boolean"}` |
| `Literal[1.5]` | `{"const": 1.5, "type": "number"}` |
| `Literal["a", "b"]` | `{"enum": ["a", "b"], "type": "string"}` |

So a one-member `Literal` renders **`const`, not `enum`, and not both** — and it
renders **the type word of its own accord**. Both halves matter:

* `const` is already in `harness.FACTS`, so the comparison grades it in both
  directions with no change. Probed on a toy pair: a model dropping the `const`
  reports `missing`, a model pinning a different value reports `differs`.
* **the document's `type` word must NOT be restated beside the `Literal`, because
  restating it is what would add a fact.** There is nothing to restate: the
  rendering already carries it, and the only spelling that could add one
  (`Annotated[Literal[...], WithJsonSchema(...)]`) would be the emitter writing the
  model's schema by hand.

## Why no hand-written comparison row is predicted

`added` has to stay 0. The rendering states exactly two keywords, and each is
already accounted for:

* `const` — the document states it at all 1,486 positions. Compared, not added.
* `type` — stated by the document at 654 of the 1,486 positions and absent at 832.
  Where it is absent the model states one the document does not, and
  `harness._entails_type` already derives it **from the document's own `const`**
  (`_JSON_TYPE.get(type(doc["const"])) == value`), reached through
  `_narrows_nothing`. Its docstring was written for exactly this rendering. It is a
  DERIVATION gated on the value, not a widening and not a list of excused sites: a
  model claiming `integer` over a string `const` still reddens.

The resolver does not undo this either. `canonicalish` reduces an **enum** node to
its `enum` alone, dropping `type` and `description`; measured on four const shapes
and on the real `collection/collection-list-changed-webhook.json`, it leaves a
**const** node whole — `type` and `description` both survive into the resolved
document the package carries. So no `_uncanonicalized` arm is needed either.

**Prediction: 0 new hand-written comparison rows, 0 changes to `harness.py`.** If
that is wrong, the row goes in `harness.py` naming itself, one keyword and one value
per row, in D5's URL-row shape — never a widened or derived rule.

## What I am building

One arm in `emit._decide`, before `type` is read, in the shape the `enum` arm
already has:

```python
if "const" in node:
    check_keywords(node, pointer, {"type", "const"})
    ...
    return Decided(Type(f"Literal[{value!r}]", local=True))
```

`local=True` for the reason every other local type has it: the compiler adds no
import and the module writer adds `from typing import Literal`.

**And `codegen/lower/union.py`'s `_literal` is DELETED, not left beside it.** It is
D2's `const` row scoped to a branch property, written there because nothing claimed
the keyword in full; this claims it in full, so two copies of one lowering is the
duplicate the project treats as a defect. `compiler.fields(decided=)` and
`compiler.lower_object(decided=)` exist for that one caller and go with it. The
union row's branch properties are then decided by the same arm, so **the committed
tree's union modules are predicted byte-identical** — graded by the byte compare the
suite already runs.

## The predicted numbers

| quantity | baseline | predicted | reasoning |
|---|---|---|---|
| the 75 lower their `const` node | — | 75 of 75 | the arm is unconditional; every one of the 1,486 nodes carries only `const`/`type`/`description` |
| of the 75, EMIT | 0 | **35** (range 25–50) | 11 of the 75 carry no keyword that refuses anybody today; the other 64 carry at least one of `$ref`, `allOf`, `uniqueItems`, `if`/`not`, `oneOf`, `dependencies`, `minProperties`/`maxProperties`, `discriminator`, and a property-level `$ref` to an emitting target is fine while the rest are later steps |
| of the 75, refuse on a NEXT keyword | 0 | **40** (range 25–50) | the complement; chiefly `$ref` chains to still-refused targets, `uniqueItems`, `allOf`, `if`/`not` |
| chain unlocks outside the 75 | — | **+1 to +3** | exactly 1 of the 219 `$ref`-chain refusals names a const-refused target directly; the rest are transitive |
| emitted, whole population | 401 | **437** (range 426–453) | 401 + 35 + 1 |
| refused, whole population | 653 | **617** | 1,054 − 437; the sum stays 1,054 |
| graded pairs **N** | 462 | **520** (range 490–570) | one pair per new root plus its nested classes; the new documents are webhooks and assets, which are shallow |
| `added` | 0 | **0** | the whole point; see above |
| `missing` / `differs` | 0 / 0 | **0 / 0** | `const` is in `FACTS` and the model states it |
| `no_constraint_to_step` | 12 | **22** (range 14–40) | `const` is not a keyword `steps()` can step (`harness`'s own docstring says so), so a new document whose only constraint is a `const` has nothing to step |
| committed tree, modules | 390 | **~430** | tracks the emitted count plus the per-document JSON |
| new hand-written comparison rows | — | **0** | |
| `emit.ROWS` entries added | — | **0** | 0 const roots |
| union modules' bytes | — | **unchanged** | `_literal` and the `_decide` arm decide identically |

## Fire probes I will land

Each new check made to FAIL before it is trusted:

1. the `const`/`type` disagreement refusal — a node whose `const` its own `type`
   refuses (population 0 in this bundle, so a hand-built node);
2. the non-`Literal` `const` refusal — an object, an array and a `null` `const`
   (population 0, hand-built);
3. the keyword screen — a `const` node carrying a `minLength` beside it
   (population 0, hand-built), which must refuse rather than drop it;
4. `_entails_type`'s `const` arm with its value gate dropped — it must then admit a
   model claiming the WRONG type, which is the probe that says the gate is the thing
   doing the work and not the row's existence;
5. the union byte-identity claim — perturb the `_decide` arm's rendering and watch
   the committed-tree byte compare redden.

## Grading

Branch tip `0267b1be9`. Every number measured on that tree.

| quantity | predicted | measured | verdict |
|---|---|---|---|
| the 75 lower their `const` node | 75 of 75 | **75 of 75** | right |
| of the 75, EMIT | 35 (range 25–50) | **26** | right, at the bottom of the range |
| of the 75, refuse on a NEXT keyword | 40 (range 25–50) | **49** — `$ref` 30, `uniqueItems` 8, `allOf` 4, `type` 3, `maxProperties`/`discriminator`/`anyOf`/`oneOf` 1 each | right |
| chain unlocks outside the 75 | +1 to +3 | **+1** (`core/authorized-agent-base.json`) | right |
| emitted, whole population | 437 (range 426–453) | **428** | **WRONG** — below the range, because the EMIT estimate was 9 high |
| refused, whole population | 617 | **626**; 428 + 626 = 1,054 | wrong by the same 9 |
| refusals naming `const` | 0 | **0** | right |
| refusals whose detail is the generic deferral and whose keyword is `const` | 0 | **0**; and 0 of the 248 `$ref` chains quotes a const deferral | right |
| documents that used to emit and now refuse | 0 | **0** | right |
| previously emitted modules changed by a byte | 0 | **0 of 390** | right |
| new hand-written comparison rows | **0** | **1** | **WRONG — the central prediction** |
| `added` | 0 | **0 of 4,942 facts compared, over 283 pairs** — but only WITH that row; 3 without it | right only after the row |
| `missing` / `differs` | 0 / 0 | **0 / 0** | right |
| `emit.ROWS` entries added | 0 | **0** | right |
| union modules' bytes | unchanged | **unchanged** | right |
| committed tree, modules | ~430 | **418 emitted documents** (390 + 28); 29 new `.py` (28 modules + one package `__init__`) | low by 12 |
| graded pairs **N** | 520 (range 490–570) | **507** | right |
| of which `pass` | — | **not measured** — `test_the_step_result_is_counted_over_the_whole_population` fails on its FIRST assertion (`len(reports)`), so the two counts behind it were never reached | — |
| `no_constraint_to_step` | 22 (range 14–40) | **not measured**, same reason; the SET changed (`test_the_pairs_with_no_constraint_to_step...` reports a different list) | — |
| comparison over the 283 class pairs | — | **4,942 facts compared, 283 of 283 `pass`, added/missing/differs 0/0/0** | the row's own grade |

### The two predictions that were wrong, and why

**1. "0 new hand-written comparison rows."** The reasoning was sound as far as it
went and the measurement behind it was real: a one-member `Literal` renders
`{"const": v, "type": t}`, `const` is already in `FACTS`, and `_entails_type`'s
`const` arm already derives the `type`. What it missed is a THIRD party — the
resolver. `canonicalish` reduces a node whose value set is FINITE to that set
alone and drops every annotation at it, and **it does that to a `const` node only
when the node is INLINED THROUGH A `$ref`.** The probe that produced the "0 rows"
prediction resolved four hand-built const nodes and one real document whose const
node has no `$ref` above it, so every one of them came back whole — a probe that
could not have returned the other answer. Measured the correct way, both ways
round on the live pair: `core/agent-encryption-key.json`'s `kty` keeps its `type`
and its `description` in its own resolved document and keeps **neither** inside
`core/authorized-agent-base.json`, which references it.

So the row exists and it is one keyword with one gate: a model-only `description`
at a node the document gives a `const`. `type` stays with `_entails_type`
deliberately, so that derivation is still the thing under test and its
value-gate probe still reddens. 3 facts at 1 pair, 0 elsewhere.

**2. "emitted 437."** 26 of the 75 emit, not 35. The structural predictor (11 of
the 75 carry no keyword that refuses anybody today) was too crude in the honest
direction: a property-level `$ref` is lowerable, but 30 of the 49 still refuse
because their TARGET refuses, and a target refusing is not visible in a keyword
census of the referrer.

### The brief's own shape was wrong, and this is the refutation

The brief said: **"THIS IS ONE DISPATCH ROW. Add it to ROWS in `codegen/emit.py`
with its selector in `codegen.bundle`."** Measured over the whole bundle:

> **0 of the 1,054 portable documents carries a `const` at its ROOT.** 1,486 const
> nodes over 347 documents, and every one of them is below the root.

`ROWS` dispatches on ROOT KIND and is a partition by it; `const` is not a root
kind in this bundle, so there is no root for a row to claim, nothing to add to
`bundle.declares_its_own_root_kind`, and no selector to write. The change belongs
in the WALK — `emit._decide`, beside the `$ref`, `enum`, typeless, `null`, array,
mapping and scalar arms that are already there and are already not rows. `ROWS`
stays at six and the partition (1,033 claimed once, 21 by none, 0 twice) is
untouched by construction rather than by a check.

This is the same refutation `salesagent-j3k2l.20` reported an hour earlier, and
for the same reason: a keyword that is not a root kind has no row in a table keyed
on root kind.

### What the design did not take into consideration

Three things, each measured, each a gap in the design rather than in a lane's work.

**(a) `compiler.Type` had no slot for a pinned VALUE, so the only way to express a
`Literal` was to spell the annotation text in the walk.** §1 puts the text on the
compiler's side, and `lower.union._literal` had to break that to exist: it built
`Type(f"Literal[{value!r}]", local=True)`, which reaches dmcg as a `Reference`
PATH, where `treat_dot_as_module` reads a dot as a module qualifier and keeps the
last segment. `Literal['account.status_changed']` rendered as `status_changed']`
and the module did not parse. **The defect was latent from the day that function
was written**: 0 of the 25 distinct Literals it actually emitted carries a dot,
while 103 of the bundle's const values, over 37 documents, do. The fix is inside
the design, not around it — `Type.literals` carries the value and dmcg's own
`literals` slot renders it, escapes it (`"it's"` comes back `Literal["it's"]`) and
reports the `typing.Literal` import. What the design was missing was one arm on
the carrier, not a mechanism.

**(b) The resolver-canonicalization folds were written for `enum` and not for its
one-member spelling.** `_narrows_nothing`'s enum bullet and `_uncanonicalized` both
name the enum case. `canonicalish` applies the same rewrite to a `const` node, and
the design has no statement about it. That is where the one new comparison row
came from, and it is a gap of the same shape as the two the design already folds
out.

**(c) "all three checks green" is not reachable for three documents this row
unlocks, and the obstruction is in the HARNESS, not in the walk or the compiler.**
Both are refusals the emitter must not make: the documents are perfectly lowerable
and there is no keyword to refuse them on, so refusing to dodge an instrument gap
would be inventing a refusal.

* **`format: uri` beside a restrictive `pattern`.** `core/reference-renderer.json`
  states `{"type": "string", "format": "uri", "pattern": "^https://github\\.com/"}`
  at `/properties/provenance/properties/source_repository`.
  `hypothesis_jsonschema`'s `string_schema` takes the FORMAT strategy and applies
  the pattern as a `.filter()`, with its own source comment reading *"This isn't
  really supported, but we'll do our best with a filter"*. Measured: 459 of 459
  draws filtered out, at 10, 25 and 50 examples alike, so the accepts check reports
  `strategy_error` for 2 pairs. `custom_formats` cannot fix it — a custom format
  strategy is per-format and cannot see the sibling pattern, and no random-host URI
  strategy will emit `github.com`. The intersection has to run the other way (draw
  from the pattern, screen by the format checker), which is a change to the
  generator seam `harness.strategy` owns. **That is `salesagent-j3k2l.10`'s
  instrument gap, already named twice in `harness.py` and in `emit.FORMAT_TYPES`.**
* **A `required` beneath `/not/anyOf/<i>`.**
  `creative/get-creative-features-async-response-submitted.json` and its
  `core/async-response-refs/` twin state `not: {anyOf: [{required: [...]}, ...]}`
  over seven keys. `steps()` emits a step per `required`, and the refuses check
  cannot draw an instance that violates exactly that keyword — the document refuses
  such an instance on `not`, so `contradicting()` reports "nothing at this instance
  location" and the strategy is Unsatisfiable. 7 steps on each of 2 pairs. The
  harness docstring already knows a position beneath a `not` "states no fact ABOUT
  the instance"; `_NO_FACT` does not reach a `required` two hops down.

**What I think should be done differently.** The step table's done-when is "emitted
AND graded green on all three checks", and these three documents show that a
document can be faithfully lowered and still be ungradeable — the obstruction being
a generator, not a model. The exit condition needs a fourth outcome beside `pass`
and `no_constraint_to_step`: **`no_instrument`, for a pair whose accepts or refuses
check cannot DRAW**, recorded with its document, pointer and cause, counted in the
population metric, and only ever shrinking. That is the shape
`test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` already
uses for a bad probe ("a bad probe, recorded as one"), raised from one test to the
metric. Without it, the only two ways to a green gate are to invent a refusal or to
weaken a check, and the design forbids both — correctly.

## The full final suite line, and what is red in it

```
23 failed, 641 passed in 1147.62s (0:19:07)
```

`tests/ -n 3`, measured at the tree one commit before the tip (the comparison row
and the fixture repair below are not in it). The 23 split into three groups and
only one of them is a defect:

**1 — fixed since that run (2 failures).**
`test_every_class_passes_all_three_checks[core/authorized-agent-base.json#]`, which
is the comparison row above, and
`test_fragment_ref.py::test_a_fragment_whose_target_document_is_refused_names_the_targets_own_keyword`,
whose fixture used `const` as its unlowerable keyword. Both green at the tip, with
`tests/test_fragment_ref.py` 16 passed and the eight const tests 8 passed.

**2 — the two HARNESS instrument gaps (4 failures), diagnosed above, not fixed.**
`[core/reference-renderer.json#]`, `[core/reference-renderer.json#/properties/provenance]`,
`[creative/get-creative-features-async-response-submitted.json#]`,
`[core/async-response-refs/creative/get-creative-features-async-response-submitted.json#]`.

**3 — metric constants that MOVED and are NOT updated (17 failures).** Deliberately
left, because every one of them is a count over the emitted tree and the tree's
membership depends on what is decided about group 2 — three documents in, or three
documents out, changes most of these numbers again. The measured target values, so
nothing has to be re-derived:

| file:line | asserted | measured |
|---|---|---|
| `test_emit.py:550` | the `no_constraint_to_step` document list | a different list (contents in the run log) |
| `test_emit.py:1057` | the format census | `{'date-time': 42, 'uri': 37, 'date': 4, 'email': 2}` |
| `test_emit.py:1253` | the pattern census | a longer dict (contents in the run log) |
| `test_emit.py:1390` | `len(reports) == 462` | **507** |
| `test_emit.py:1476` | the `extra` census | `{'forbid': 105, 'allow': 153, 'silent': 25}` |
| `test_emit.py:2086` | the union roots not emitted | a shorter list |
| `test_emit.py:2199` | `_entails_type`'s excused sites `== 11` | a longer list |
| `test_emit.py:2519` | a count | **68** |
| `test_emit.py:2562` | an alias/document list | a longer list |
| `test_emit.py:2622` | a count | **134** |
| `test_emit.py:3138` | a count | **72** |
| `test_emit_product.py:173` | `N == 214` over step 4's population | **254** |
| `test_enum.py:196` | a count | **275** |
| `test_enum.py:249` | a count | **1980** |
| `test_enum.py:306` | a count | **275** |
| `test_enum.py:412` | a pair | **(39, 27)** |
| `test_enum.py:806` | a count | **193** |

Every one of the 23 is in group 1, 2 or 3; there is no fourth group.
