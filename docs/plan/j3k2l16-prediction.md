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

Filled in after the measurement, in this file, naming which predictions were wrong.
