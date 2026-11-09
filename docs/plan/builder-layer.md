# The builder layer: ergonomics that cannot drift, and where they are not wanted

The generated types are exhaustive and faithful. This decides how a developer gets a
usable API on top of them without hand-writing one per class, and without weakening the
property the whole compiler is built for: drop in a new bundle, regenerate, and the types
are correct.

Every figure here names the population it is over. The population is the 1,054 portable
documents of `schemas/cache/3.2` unless a row says otherwise.

`docs/plan/rebuild-plan.md` decides the semantics and `docs/plan/architecture.md` decides
the structure. This document decides neither. Where it needs a change in one, §8 states it
as a numbered request.

---

## 1. The measurement, and what three of the figures do not mean

The prose survey reproduces exactly: 133 documents / 390 sites where a description names a
sibling property in backticks; 50 documents / 74 sites stating positional semantics; 165
documents carrying at least one; 889 (84.3%) carrying neither.

Three of those figures mean less than they look like.

**390 sites is 323.** 67 sites sit on a node that is not a property — the object's own
description naming its own members, which is documentation of the object and not a
relationship between two of them. 24 documents carry only that kind. The cross-field figure
is **323 sites in 109 documents**.

**225 of the 323 are prose about a neighbour.** Classified over all 323 sites:

| bucket | sites | documents | what it is |
| --- | --- | --- | --- |
| DERIVATION | 10 | 8 | a value computable from another value |
| CONDITIONAL | 88 | 47 | requiredness or exclusion turning on another value |
| DEPRECATION | 36 | 26 | "use `x` instead" |
| MENTION | 189 | 83 | "distinct from `x`", "supplements `x`" |

A sample of 20 read by hand agrees with the partition.

**The 88 conditionals are not this layer's work.** Draft-07 states conditional requiredness
and mutual exclusion with `if`/`then`, `oneOf` and `dependencies`. 76 of the 88 sit under a
node that already carries a conditional keyword; **13 sites in 12 documents have none
anywhere above them**. Those 13 are upstream bugs. A builder written against any of the 88
would enforce in Python what the protocol must enforce for every implementation, and that
is a defect, not an ergonomic.

*The 76 figure is coarse and overstates coverage:* "a conditional keyword somewhere above"
is not "this prose conditional is encoded". The measurement that settles it pairs each of
the 88 prose conditionals with the keyword that encodes it, which is a reading of 88 sites
and not a set operation.

**The positional 74 is 4.** Only 5 of the 74 sites sit on an integer-typed node, and
reading those 5: `core/catalog-item-availability-state.json` and
`core/catalog-item-availability-update-result.json` (`request_index`),
`core/macro-declaration.json` (`location.occurrence`) and `creative/video-brief.json`
(`segments[].order`) are indices; `pricing-options/flat-rate-option.json`'s `slot_span` is
a count.

---

## 2. The line: what is generated, what is hand-written

**The generable tier is larger than the candidate set and does not intersect its premise.**
Over the 1,054 documents, **1,079 required properties carry `const`, in 315 documents** —
counted at every object node, including nested objects and `definitions` entries. 238 of
those 315 are in the 889 that carry no prose relationship at all. A developer types
`asset_type="image"` at every one of those 1,079 sites and has no other admissible choice.
The derivation is `const` and `required`; no prose is involved.

A further **60 `const` pins sit inside an `allOf` overlay beside a `$ref`, in 28 documents**
— the url-asset shape, where the overlay narrows an inherited enum to one member. Same
derivation, read through the overlay.

**The default cannot go on the field, and the reason is measured.** A `Literal['image']`
field given a default leaves `required` in `model_json_schema()`. `required` is a fact
`harness` compares against the document of record, so a defaulted const field reports as
`differs` — the model says the property is optional where the document says it is required.
The generated class stays faithful and the default moves to a **generated `build()`
classmethod**, which no instrument in §8 of the semantics document reads. `build` is a free
name: zero documents declare a property called `build`, and it is not in `dir(BaseModel)`,
which is what `render.RESERVED` derives the reserved set from.

**The hand-written tier is 3 shapes over 9 documents.** Reading all 17 sites the derivation
detector flags: 6 documents state a computable derivation, 1 states referential integrity,
10 are mentions.

| shape | documents | sites | what is derived |
| --- | --- | --- | --- |
| occurrence of a token in a sibling text field | 7 | 10 | `location.field`, `location.occurrence`, `location.context` |
| ordinal of an element in its own array | 1 | 1 | `segments[].order` |
| index into a parallel array in the paired message | 2 | 2 | `request_index` |

The 7 for the first shape is measured structurally — documents carrying a
`macro_declarations` property — not from prose. All 7 are in the 165, but the derivation
regex flags only 2 of them, which is why §6 selects on structure.

**Positional derivation is not a generable pattern.** 4 instances in 3 shapes. A generated
pattern costs more to write and more to grade than three functions.

What is excluded and why it matters: `core/creative-manifest.json`'s `component_assets`
keys MUST match one `params.components[].component_id`. Nothing is computed — the key is
supplied and checked. A builder can check it; it cannot derive it, so there is nothing for
an independent reader to re-derive and §4's second obligation has no subject.

---

## 3. The boundary, and the test that holds it

Three populations, not two.

**Generated wire types** — `src/adcp/types/_schemas/**`, written by `codegen`, never
hand-edited. This does not change.

**The generated builder** — `build()`, emitted onto the wire class by `render.py`. Not a
separate package: a second module per class doubles the import surface and breaks §1's "one
import path per class", and a generated artifact cannot drift from the schema by
construction, so it needs no boundary to protect it. The boundary that matters is generated
against hand-written, because only hand-written code can drift.

**The hand-written layer** — `src/adcp/build/`, **one module per SHAPE and not per class**:
`occurrence.py`, `ordinal.py`, `correlation.py`. Three shapes over nine documents; a module
per class is nine copies of three functions.

The import direction is three bans:

* nothing under `src/adcp/types/` imports `adcp.build`;
* nothing under `codegen/` imports `adcp.build` (the existing `codegen.bundle` →
  `adcp.types._base.applied_schema` edge stays, and is the reason this ban is stated rather
  than assumed);
* nothing under `src/adcp/build/` imports `codegen`.

The third is the one that is easy to get wrong and the most expensive: a builder wanting to
read the record reaches for `bundle.record`, and the shipped wheel then depends on the
compiler.

**Held by a fifth AST rule in `tests/test_import_rule.py`.** It reuses that file's
`_resolved` relative-import walker and derives its population from the tree the way
`PACKAGES` already does, so a module added later is graded without anyone remembering.
Resolved by AST and not by grep for the three reasons the file's own docstring gives; a
`TYPE_CHECKING` import is still a violation for the reason it gives there too. Each half
reddens under a named perturbation and names the offending module: `import adcp.build` in
`src/adcp/types/_base.py`, and `from codegen import bundle` in
`src/adcp/build/occurrence.py`. A rule nothing can break is a finding about the rule.

---

## 4. How a builder is pinned

The proposal is that a builder's output must pass `strict_validate` against its wire type's
own schema. **Adopt it, and be exact about what it is.** It is the drift detector. It is not
the correctness check, and a design that treats it as one grades a builder on everything
except its purpose.

What it catches: a wrong `const`, an enum member that left the vocabulary, a pattern
violation, a missing required property, an `additionalProperties: false` violation. On a
bundle bump these are the changes that break a builder silently today, and it catches them
against the document of record packaged beside the class, so there is no second source of
truth.

What it does not catch:

1. **The relationship.** `strict_validate` decides what the document decides, and the
   premise of this layer is that the document cannot state the relationship. `occurrence: 0`
   for a token at index 2 passes: it is a non-negative integer.
2. **A dropped input.** A builder that ignores an optional argument produces a valid
   document.
3. **A substituted value.** A builder writing the wrong member of a correct enum produces a
   valid document.
4. **Coverage.** It grades the payloads the test drives, which is a corpus and not the
   admissible space — the distinction §8 already draws for the accepts draw.

Three obligations, therefore.

**P1 — validity.** Every builder's output passes `strict_validate` against its class's
`__adcp_schema__`. The corpus is **derived**: drive it from §8's accepts draw over the
builder's document, and take the builder's inputs as the drawn payload minus the fields the
builder derives. No hand-written payloads, and the coverage argument is inherited from the
draw rather than re-made.

**P2 — derivation round-trip.** For every field a builder derives, an independent reader
re-derives it from the finished instance and the two must agree. For the occurrence shape:
re-scan the instance's own text field for each declaration's `token` and assert the
declaration's `occurrence` is the index of that occurrence. The reader is written from the
prose and so is the builder, and they are two bodies of code for the reason §9 gives: one
body deciding both sides agrees with itself by construction, so a defect in it is green on
both sides. **This is the obligation that grades the relationship, and it needs no schema at
all.**

**P3 — surface equality.** The set of parameters `build()` accepts equals the document's
properties at that node, minus the required properties pinned by `const`, minus the
properties the builder derives — **in both directions**, read off the packaged record. A
builder that stops offering a property the document gained fails; one offering a property
the document dropped fails. This is a set equality between two sets neither of which is
hand-written, which is the form §8 demands of its two standing checks, and it is the leg the
bundle bump actually rides on.

---

## 5. A new bundle version

Most of this is set arithmetic. Each claim is graded.

**"Builders whose packaged record changed need review."** Correct, and a set operation —
under-scoped as stated. The compare runs over the builder's **transitive record closure**,
not its own record: the occurrence builder binds `core/assets/url-asset.json` and derives a
field declared in `core/macro-declaration.json`, reached by `$ref`. `bundle.edges` and
`emit.closure` already compute that closure, so the set is
`{B : closure(doc(B)) ∩ changed ≠ ∅}`. Machine.

**"Builders naming a field or enum member that no longer exists are already broken via
mypy."** **False today, and measured.** `src/adcp` is absent from `[tool.mypy] files`; the
package ships no `py.typed`; `[[tool.mypy.overrides]] module = ["adcp.*"]` with
`follow_untyped_imports = false` resolves the whole package to `Any`. A standalone run over
`ImageAsset(bogus=1)` reports `import-untyped` and nothing else. The mechanism works once
packaging allows it: pydantic v2's `dataclass_transform` makes mypy synthesize `__init__`
with no plugin, and an inline model reports both `Unexpected keyword argument` and `Missing
named argument`. One row makes the claim true — ship `py.typed`, add `src/adcp` to `files`,
drop `adcp.*` from the override. `pyproject.toml` already reserves `py.typed` as "a decision
for the row that owns the shipped package"; this is that row. Until it lands, the leg is
carried by P3 alone.

**"Newly-emitted documents inside the candidate set with no builder are candidates."**
Correct as a set operation, with two corrections. The candidate set is **re-derived** from
the new bundle and never carried over, because it is a function of prose and prose changes.
And the selector is not the prose set — see §6.

**Three sets the list is missing**, all machine:

* **a derived field left the document** — `{B : derived(B) ⊄ properties(record(B))}`. P3
  reddens, but nothing says *delete*; this set does.
* **a relationship became machine-readable** — detected by the JSON type of the
  `x-adcp-validation` value that states it. This is the deletion trigger §7 is built on.
* **a prose conditional became a keyword** — the generated type now enforces it, and any
  builder-side check for it is dead code. Detected by the keyword set at the node.

**The one judgement, and its bound.** Reading the prose at the sites whose record changed,
to decide whether the *relationship* changed. A record diff says the bytes moved; it does
not say whether "zero-based occurrence" became "one-based". That is a human or an agent,
over a set the machine produces, bounded by the number of builders whose closure record
changed — at most 3. Everything else above is a set operation. The judgement is small
because the builder count is small, and the builder count is small because of §6.

---

## 6. How a candidate is chosen

**The 165 is not the population.** The generated tier is not scoped by it: 315 documents
carry a `const` pin, 238 of them outside the candidate set. And the hand-written tier is 6
documents, which needs a list, not a ranking — a score over 6 items invents precision it
does not have.

The rule that survives the next bundle is a **predicate**, and its clauses are derived from
what the obligations in §4 can grade:

1. **A description states that a value is computable from another value in the same
   message.** Machine-detectable as a first cut (10 sites / 8 documents), confirmed by
   reading. The reading is the judgement and it is over at most 20 sites.
2. **Draft-07 cannot state it.** If the relationship is conditional requiredness, mutual
   exclusion or a value dependency, draft-07 can, and the answer is an upstream pull request
   and never a builder. This clause alone removes 47 of the 109 cross-field documents.
3. **The document emits.** Otherwise it is a compiler row. 56 of the 165 fail this today.
4. **The computation has a single correct answer an independent reader can re-derive.** This
   is what makes P2 writable. It excludes `core/creative-manifest.json` (checked, not
   computed) and `media-buy/sync-event-sources-request.json` (`action_source` "aligned with"
   `surface` through a mapping nobody enumerated).

**Select on structure, not on prose.** The derivation regex flags 2 of the 7 documents
carrying the macro shape; the structural signal — a `$ref` to `core/macro-declaration.json`
beside an `allOf` overlay pinning `location.field` — finds all 7 and finds them exactly. The
prose set is the debt register (§7). The work list is derived from structure.

For the record, the generated tier ranked by `pins(D) × (1 + indegree(D))` is led by
`core/product-format-declaration.json` (180), `content-standards/artifact.json` (98),
`core/optimization-goal.json` (66), `core/product.json` (66) and
`protocol/get-adcp-capabilities-response.json` (57). It is reported and then discarded:
`build()` is emitted for every class, so there is nothing to rank. A ranking is only needed
where the work is per-class, and this design is arranged so that it is not.

---

## 7. The metric

The hand-written layer is a debt register and not an asset. That is right. The single number
is wrong, because two debts with different creditors and different closing moves are being
added together.

**Debt 1 — expressible, stated in prose.** 88 conditional sites in 47 documents; 13 sites in
12 documents with no conditional keyword anywhere above. Creditor: upstream. Closing move: a
pull request that writes the `if`/`then`. **No builder is ever written against this debt.**
Target zero, and reachable by us.

**Debt 2 — inexpressible in draft-07.** 3 shapes over 9 documents. Creditor: the vocabulary.
Closing move: `x-adcp-validation` gains structure (`adcontextprotocol/adcp#8472`). Target
zero, and only upstream can move it.

Measured on 3.2: **179 `x-adcp-validation` sites in 135 of the 1,054 documents**; within the
110 `verifier_constraints` objects, **197 of 270 values are prose strings (73%)**, against 56
objects, 10 booleans and 7 arrays. *This does not reconcile with #8472's "380 keys, 54%
prose" — a different population and probably a different bundle version — so it is reported
over its own population rather than claimed as agreement.* What it establishes is the thing
the thesis needs: the vocabulary is **already partly structured** — `unique_item_properties`
(6), `unique_by` (5), `subset_of` (4), `tier_boundaries` (3) — so structure is not a
hypothetical ask.

**The closing criterion for the flagship builder is a test, not an intention.**
`core/macro-declaration.json`'s `x-adcp-validation.verifier_constraints.token_occurrence` is
today the string *"location must identify the declared zero-based occurrence of token in
location.field"*. Assert that the value is a string. The day upstream gives it structure, the
assertion fails, the derivation is machine-readable, and `adcp/build/occurrence.py` is
deleted.

**A third number, without which the register is unfalsifiable: deletions.** A register where
nothing is repaid is a ledger of assets wearing the word debt. The tracked triple is (debt 1,
debt 2, deletions), each over its named population, and only the third proves the first two
are being worked.

---

## 8. Requests to the two plan documents

1. **`rebuild-plan.md` §1.** Its code block names two constructors. Add one sentence for the
   generated `build()`: it takes every property the document declares except the required
   ones pinned with `const`, supplies those, constructs through the same path as direct
   construction, and changes no accepted set. *Without it:* emitting `build()` is a decision
   taken in `render.py` with no sentence behind it, which §14's *bytes* note calls an
   undeclared change, and the row cannot land under the existing gate.
2. **`rebuild-plan.md` §8.** A classmethod is invisible to all three checks, so `build()`
   ships ungraded. Add a fourth, in the set-equality form §8 already uses: the parameters
   `build()` accepts equals the document's properties minus the `const`-pinned required ones,
   in both directions. *Without it:* `build()` drops a property on a bundle bump and every
   check stays green — exactly what §8's "a hand-written list beside a check is blind beyond
   itself" rule exists to prevent.
3. **`architecture.md` §11.** Add a tenth row to the layer table: `| build |
   src/adcp/build/* | the emitted classes, and the relationships no keyword carries | codegen,
   the record, the walk | a constructed instance |`, with one sentence naming the fifth AST
   test. *Without it:* `tests/test_import_rule.py` grows a rule no document decides, which is
   what that file's docstring refuses to be.
4. **`architecture.md` §14.** Place this layer: the hand-written tier follows step 10; the
   generated `build()` needs only the class and may land beside the waves. *Without it:* the
   pilot gets scheduled against documents that do not emit — 56 of the 165 — which is the
   error this design exists to avoid.

---

## 9. What blocks this, in order

`adcp-client-python-97w` — "two object declarations of one property compose as an `allOf` of
the two" — gates the pilot entirely. Measured at HEAD over the 1,054: 885 emitted, 169
refused, 60 primary and 109 transitive; **34 of the 60 primary refusals are the restatement
arm**, and all 7 macro-bearing assets are among them, at the overlay that pins
`location.field`.

*That 34 is contested.* The orchestrator measured 13 primary restatements plus 21 chained
refusals quoting them — the same population read two ways. The audit on
`docs/plan/reasons-vs-rows.md` settles it; do not quote either figure until it does.

Two corrections 97w needs: its price, and its refusal message, which cites §5(b)'s widened
row — step 10, needing a rung and a §8 direction — where the code's own comment names the
correct cause as §5's unimplemented `properties` row, which is faithful and belongs to step
9. `const: "url"` intersected with `enum: [url, markup, …]` is `const: "url"`; the
intersection is computable and the answer needs no approximation. A reader of the report
schedules it in the wrong step.

The sequence follows from that:

1. the generated `build()` — unblocked, serves 315 documents, costs nothing per class;
2. the fifth import rule and P3 — the machinery the hand-written tier needs, written before
   there is anything to break it;
3. `py.typed` and the checker — makes the bundle-bump argument's second leg true;
4. the occurrence pilot — behind 97w.
