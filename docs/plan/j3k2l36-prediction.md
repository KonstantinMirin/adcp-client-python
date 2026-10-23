# salesagent-j3k2l.36 — prediction, written before the change exists

Measured on `93ec36aea` (this branch's base), comparison only (`max_steps=0`),
1034 pairs: **added 0, missing 11, differs 28**.

## The partition of the 39, per document and per property key

| document | added | missing | differs | keys |
|---|---|---|---|---|
| `a2ui/component.json` | 0 | 1 | 0 | `component`'s mapping VALUE |
| `a2ui/surface.json` | 0 | 1 | 0 | the same node, one level in |
| `formats/canonical/agent_placement.json` | 0 | 2 | 6 | `experimental`, `v1_translatable`, `slots` |
| `formats/canonical/audio_vast.json` | 0 | 0 | 2 | `slots` |
| `formats/canonical/image_carousel.json` | 0 | 1 | 4 | `v1_translatable`, `slots` |
| `formats/canonical/native_in_feed.json` | 0 | 2 | 4 | `experimental`, `v1_translatable`, `slots` |
| `formats/canonical/responsive_creative.json` | 0 | 2 | 5 | `experimental`, `v1_translatable`, `slots` |
| `formats/canonical/sponsored_placement.json` | 0 | 2 | 5 | `experimental`, `v1_translatable`, `slots` |
| `formats/canonical/video_vast.json` | 0 | 0 | 2 | `slots` |

By key: `slots` 12, `experimental` 11 (7 differs + 4 missing), `v1_translatable`
14 (9 differs + 5 missing), the a2ui mapping value 2.

## The 39 are THREE mechanisms, not one

**(1) 28 differs — the LOWERING's, and the one this issue names.**
`codegen/lower/product.py`'s restatement loop has no arm for a restatement whose
constraining content is EMPTY: it falls to `# Otherwise it adds nothing and the
field is INHERITED`, gated there by `_constraining(node)` on the clause-2 branch.
So the subclass declares no field and `model_json_schema()` renders the BASE's
`default` and `description` at a pointer the subclass's own document declares.
Two of them are inversions (`v1_translatable`: document `False`, model `True`)
because the base defaults it `true`. This is a real fidelity defect in the
generated class, not a comparison artifact: a caller constructing
`CanonicalFormatImageCarousel()` gets `slots=None` where the document states a
three-slot default.

**(2) 9 missing `enum: [False, True]` — the COMPARISON's document side, and NOT
mine (`codegen/harness.py`).** Measured: in the resolved subclass document the
inlined base's `experimental` node is `{"enum": [false, true]}` — the resolver's
finite-type rewrite, which drops the `type`. `_composed` folds that conjunct into
the restated node, so the composed node is
`{"default": ..., "description": ..., "enum": [false, true]}` with no `type`, and
`_constrains_nothing`'s correct `type == "boolean"` gate does not fire.
`_uncanonicalized` restores the `type` only when the node is EXACTLY
`{"enum": [false, true]}`, which it is not once the restatement's annotations are
folded in. **Fix (1) cannot clear these**: after it the model states
`type: boolean` (excused as model-only by `_implied_by_an_enum`) and the document
still states an `enum` the model does not. I predict these 9 remain and I report
them on the issue rather than reaching into `harness.py`.

**(3) 2 missing a2ui `additionalProperties/description` — a THIRD mechanism, and
a design question rather than a bug.** The mapping value node is
`{"type": "object", "description": "Component properties"}`; `compiler.Type` has
no slot for an annotation on an inner type and `_inner` refuses a constraint
there for exactly that reason (D5's answer is to NAME the inner type, in
`codegen/constraints.py`, which I do not own). Pydantic CAN render it —
`dict[str, Annotated[dict[str, Any], Field(description=...)]]` renders the
description into `additionalProperties` (measured on this venv) — so this is
expressible, but not without giving `Type` an inner-annotation capability. I
predict these 2 remain and I report them.

## What I will do, and what I predict it does

The change: an annotation-only restatement over an inherited key declares the
field with **the base's constraining content merged into the restated node**
(`{**_constraining(inherited[key]), **node}`), which is what keeps it from being
`.22`'s `Any` shadow. With the merge, `_constraining(node)` being non-empty stops
being the clause-2 branch's safety gate, so the branch becomes
`_annotates_differently(node, inherited[key])` alone; for the 15 `context` pairs
clause 2 already serves, the merged node EQUALS `node` (their constraining
content is non-empty and equal to the base's), so they are unchanged.

Predicted counts, over 1034 pairs:

* **added 0** — unchanged, and this is the invariant. The merged node states
  exactly what the base's declaration and the subclass's annotations state
  together, so no fact is model-only that was not model-only before.
* **differs 0** — all 28 cleared.
* **missing 9** — the enum facts of (2), after the 2 of (3) are also still there,
  so **missing 11** if I do not clear the a2ui pair, which I predict I do not.
* So the predicted end state is **0 / 11 / 0**, NOT 0/0/0, and the residue is
  two named mechanisms in files I do not own.

`emitted` 686 of 1054, `accounted` 1053, `deferred` 0 — predicted **unchanged**,
because the merge changes what a class declares and not which documents emit.

## The risk I have not resolved, named before measuring

`experimental` and `v1_translatable` merge to `{"type": "boolean", ...}`, which
lowers to a `bool` field with no nested node. `slots` merges to
`{"type": "array", "items": {<the base's raw item object>}, ...}`, and I predict
`fields` → `mod.decide` **re-lowers those items into a NEW class per canonical**,
named `CanonicalFormat<X>SlotsItem` and stamped
`__adcp_schema__ = SchemaRef('formats/canonical/<x>.json', '#/properties/slots/items')`.
That pointer does **not** resolve in the subclass's resolved document — its
`properties/slots` carries only `default` and `description`, and the items node
lives under `#/allOf/0/properties/slots/items`. So I predict:

* `pairs` RISES from 1034 to about 1041 (7 new item classes), and
* those 7 new pairs break in `pair_of`/`schema_at` rather than merely reddening,
* and `CanonicalFormat<X>SlotsItem` would not be a `CanonicalFormatBaseSlotsItem`,
  which breaks substitutability for a field a subclass is supposed to inherit.

If that is what happens, the merge is right for the two booleans and wrong for
`slots`, and the fix for `slots` is to **re-use the base's already-decided field**
rather than re-decide a node whose structure lives in another document: carry the
base's `Property` on `compiler.Shape` and build the subclass's field from it with
the restatement's `default`/`description` substituted, importing the local symbols
its `Type` tree names from the module the `$ref` conjunct bound. I will say so and
measure it, and I will flag that this re-introduces a per-property decided type to
`fields`, which was deliberately removed once for a different reason.

## Probes I will run to show the merge still REPORTS

1. A subclass restating a property with an annotation that CONTRADICTS its base's
   constraint — expected: refused by `_restatement`'s `None` arm, or reported by
   `differs`. I will show which and why that is the right report.
2. A base stating a fact the subclass and the model both lack — expected:
   `missing` names it.

---

# The grade, written after measuring

## Right

The three-mechanism partition and which file owns each. 28 `differs` cleared.
`added` stays 0. The 9 enum facts remain and belong to the comparison; the 2 a2ui
facts remain. End state **0 / 11 / 0** over 1034 pairs, and NOT 0/0/0.
`emitted` 686, `accounted` 1053, `deferred` 0, `transitive` 1 -- unchanged. The
`slots` re-lowering hazard, down to the duplicate class name, the exact pointer
`#/properties/slots/items`, `schema_at` raising `KeyError`, that the answer is to
re-use the base's decided field, and that doing so re-introduces a parameter
`fields` deliberately dropped.

## Wrong, two

**`pairs` rising to about 1041.** It never got that far. A class stamped with a
pointer its document does not have makes `pair_of` RAISE, so the simple node merge
would not have produced a count to compare at all. The hazard was right; how it
would present was wrong.

**The silence asymmetry, which I predicted the opposite of.** I wrote that the
annotations are the restatement's and are never gap-filled from the base's,
following `_annotates_differently`'s existing reasoning. That is right for a
restatement whose constraining content EQUALS the base's -- its node resolves to
annotations of its own, all 15 being a bare `$ref` -- and wrong for an
annotation-only one, whose node resolves to nothing. `_composed` gap-fills the
base's annotation on the DOCUMENT side, so taking the silence as an answer turned
one `differs` into one `missing` at
`formats/canonical/responsive_creative.json#/properties/slots/description`. Caught
by re-measuring the pair, not by reasoning about it.
