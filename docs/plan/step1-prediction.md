# Step 1 prediction, written before any measurement of the leaf population

Written at base `a3d892c48` on `emit/s1-leaf-object`, after running the spike
(`grade.py b`: 3/3 green, direction 2 13 sites 13 pass) and reading
`core/pagination-request.json`, and **before** running any census over the leaf
set or emitting anything.

Step 1's lowering covers, per D2: an object root with `properties`; a scalar
property with the 12 constraint keywords and a `format`; a nested object
property (recursive, named by D3); a typeless property -> `Any` (D2's row, which
the plan assigns here as defect D1-a). Everything else is a later step's row and
**refuses by name and keyword**: `enum`/`const` (step 3), `items`/array/typed
`additionalProperties`/`patternProperties`/multi-type (step 6), `uniqueItems`/
`dependencies`/`min`/`maxProperties` (step 7).

## The two predictions

1. **N = 30 of 85** leaf object documents emitted and graded green in both
   directions. Reasoning: the leaf filter removes `$ref`, composition and
   conditionals but not inline `enum`s or arrays, and those are the two most
   common property shapes in this bundle (the plan counts 535 documents with an
   `enum` anywhere and 727 with `additionalProperties`). I expect the majority of
   the 85 to carry one of them in at least one property, and a leaf refuses on
   its first unlowered keyword.
2. **The first keyword to refuse is `enum`**, for the same reason: it is the
   most widely carried of the keywords step 1 does not own.

Both are graded in the report. A refusal is named with its document and its
keyword, never counted alone.
