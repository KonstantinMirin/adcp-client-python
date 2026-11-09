# Step 2 prediction, written before anything was measured

Committed at the step-1 trunk (`66001eaa5`) on `emit/s2-crossref`, before running any
census over the `$ref` population and before writing a line of the mechanism. Graded in
the bead note.

Step 2 lowers a cross-document `$ref` into an IMPORT. N is 34 of 1,054 going in.

## 1. N after this step

**130 of 1,054**, so ΔN ≈ +96.

The plan predicts ΔN ≈ +100 over a population of 176. I am predicting slightly under it,
for one reason I can name now: a document whose only `$ref` use is a property or its items
can still carry an `enum`, a `const` or a composition SOMEWHERE ELSE, and step 1's keyword
check refuses it there. The 51 refusals step 1 recorded over 85 leaves is a 60% emit rate
on documents with no reference at all; the reference-bearing documents are larger, so their
rate should be no better.

## 2. Refusals out of the 176

**70 refused**, each naming its document, pointer and keyword.

Expected buckets, in the same shape step 1 recorded: `type` (an array or mapping property,
step 6), `enum` (step 3), `const` (step 3), and a new `$ref` bucket for a reference this
step does not lower — a fragment reference (`#/definitions/x`, or a URI with a fragment),
which names a node inside a document rather than a document, and so needs a name that D3's
nested rule gives it in a later step.

## 3. Do I need `resolved_cache` or `node_graph`?

**Neither.** Prediction: I copy in nothing.

An import edge is `$ref` URI -> document path -> module path, which is a function of two
paths (D1) and of the bundle's own file set. Resolution substitutes a target's CONTENTS for
the reference, which is the opposite of an import: a resolved document has no `$ref` left to
emit an import from, so an emitter that resolved first could not emit step 2 at all.

What I do need is the ref GRAPH, twice: once to emit a document's targets before the
document (transitive emission), and once to hand the harness a resolved schema, because
`check_pair` requires `$ref` already resolved. Both are the same walk of `$ref` strings, and
`harness.resolve` already does the inlining given a store. So the walk is mine and small;
`node_graph.py` (499 lines) and `resolved_cache.py` (290) are each larger than the whole of
`emit.py`'s reference handling will be, and `resolved_cache`'s memo buys a cost reduction
over a population that resolves in one shot at this size.

The risk I am accepting, named: `harness.resolve` inlines a fresh copy per path through the
graph, which is why `resolved_cache` exists. If a step-2 document does not resolve at a
practical budget, the measurement says so and the copy becomes justified. I predict none
does, because this population's references are one property deep by construction.

## 4. Where I expect to be wrong

The mapping from an absolute `$ref` URI to a bundle document. Every reference in the bundle
is spelled `https://adcontextprotocol.org/schemas/3.2.4/<path>`, and D9 forbids a version
literal in `codegen/`. So the rule has to be derived from the bundle's own file set rather
than from the URI's shape, and I expect to find at least one URI where the derivation is
ambiguous or misses.
