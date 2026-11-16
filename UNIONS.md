# The bundle's non-separable unions, measured

Bundle: `schemas/cache/3.2` (AdCP 3.2.7). Measured 2026-11-16.

## 1. The count

The instrument is `docs/plan/10l30-census.py`. Its figure:

```
PYTHONPATH=.:src ./.venv/bin/python docs/plan/10l30-census.py
```

```
authored unions of shapes: 167  ($ref inside a branch: 112, non-$ref: 55)
=== walk (lower.union.separates)
  non-$ref: 7 unions, 7 documents, 65 pairs
  $ref inside a branch: 16 unions, 16 documents, 235 pairs
=== verifier (harness.separates)
  non-$ref: 7 unions, 7 documents, 65 pairs
  $ref inside a branch: 16 unions, 16 documents, 235 pairs
```

**The two readings agree pair for pair, at all 23 unions and all 300 pairs.** §9's
equality holds; nothing below is a disagreement between the walk and the verifier.

**Of those 300 pairs, 17 are upstream defects and 283 are not.**

| | unions | pairs |
|---|---|---|
| census reports as separated by nothing | 23 | 300 |
| **verified defect** | **10** | **17** |
| verified NOT a defect (§5) | 13 | 283 |

Every one of the 17 was verified by constructing a payload and validating it against
the two branch nodes with a real draft-07 validator; every one of the 283 was verified
by finding the separator the census does not read. The witness harness:

```python
# /tmp/witness.py
from pathlib import Path
from jsonschema import Draft7Validator, RefResolver
from codegen import bundle

B = Path('schemas/cache/3.2')
DOCS = list(bundle.portable(B))
PREFIX = 'https://adcontextprotocol.org/schemas/3.2.7/'
STORE = {PREFIX + d: bundle.read(B, d) for d in DOCS}

def validator(node, home):
    base = PREFIX + home
    return Draft7Validator(node, resolver=RefResolver(base, STORE[base], store=STORE))

def node_at(doc, ptr):
    cur = bundle.read(B, doc)
    for p in [x for x in ptr.split('/') if x]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    return cur

def arms_matching(at, payload):
    doc, ptr = at.split('#')
    return [i for i, b in enumerate(node_at(doc, ptr))
            if not list(validator(b, doc).iter_errors(payload))]
```

Run as `PYTHONPATH=.:src ./.venv/bin/python -c "import sys; sys.path.insert(0,'/tmp'); from witness import *; ..."`.

**The 17 pairs are ONE defect kind, in three populations.** The groups the task
anticipated — "superset required-set", "same required set differing only in an
optional property", "branches distinguished only by a description" — have **zero
members each**. Every one of the 10 verified unions has **pairwise-disjoint `required`
sets**; what is missing in all 10 is the mutual `not`. §4 and the hypothesis are
reconciled in §3.

And the combinator splits the population cleanly: **all 10 verified defects are
`oneOf`; every `anyOf` the census reported is a false positive.** An `anyOf` whose arms
overlap is an OR, which is what an OR looks like.

## 2. The defect: disjoint `required` sets, open arms, no mutual `not`

### The shape

Each arm of a `oneOf` requires its own set of names. No two arms share a required
name. But:

* no arm pins a `const` on a shared property (no derivable discriminator);
* no arm states `not: {required: [<the other arm's name>]}`;
* every arm is open — `additionalProperties` absent or `true`.

So an instance carrying the required names of *two* arms satisfies both. Under
`oneOf` that instance is **rejected**, and the rejection is draft-07's
`"... is valid under each of {...}"` — which names no field, so the producer is told
its payload is wrong without being told which key to drop.

Nothing is unreachable and no arm is dead. What is lost is (i) any derivable
discriminator, and (ii) a usable error.

### The idiom the bundle already uses, which these 10 omit

This is not a missing feature of draft-07 or of the bundle's house style — the guard
exists, in this bundle, spelled this way:

```json
"not": {"anyOf": [{"required": ["results"]},
                  {"properties": {"status": {"const": "submitted"}},
                   "required": ["status"]}]}
```

`creative/get-creative-features-response.json`, `media-buy/decline-proposals-response.json`,
`media-buy/refine-proposals-response.json`, `media-buy/request-proposals-response.json`
and arms 4 and 5 of `media-buy/build-creative-response.json` all carry it, and all of
them separate (see §5.A, §5.B). The 10 below are the sites where it was not written.

---

### Group 2.1 — success-vs-error arms of a task response (6 unions, 6 pairs)

**This is one repeated pattern, and the task's guess that "several of the 16
content-standards/* rows look like one repeated pattern" is confirmed: it is the same
pattern six times, in six files, with only the success arm's payload name changing.**

| union | arm 0 `required` | arm 1 `required` |
|---|---|---|
| `content-standards/calibrate-content-response.json#/oneOf` | `['verdict']` | `['errors']` |
| `content-standards/create-content-standards-response.json#/oneOf` | `['standards_id']` | `['errors']` |
| `content-standards/get-content-standards-response.json#/oneOf` | `['standards_id']` *(via `$ref` to `content-standards/content-standards.json`)* | `['errors']` |
| `content-standards/get-media-buy-artifacts-response.json#/oneOf` | `['media_buy_id', 'artifacts']` | `['errors']` |
| `content-standards/list-content-standards-response.json#/oneOf` | `['standards']` | `['errors']` |
| `content-standards/validate-content-delivery-response.json#/oneOf` | `['summary', 'results']` | `['errors']` |

In all six: `additionalProperties` is absent from both arms, neither arm states `not`,
and both arms declare `context` and `ext` and nothing else shared.

**Representative, verified by hand — `content-standards/list-content-standards-response.json#/oneOf`:**

```json
[0] { "type": "object",
      "description": "Success response - returns array of content standards",
      "properties": { "standards": {"type": "array", ...},
                      "pagination": {"$ref": ".../core/pagination-response.json"},
                      "context": {"$ref": ".../core/context.json"},
                      "ext": {"$ref": ".../core/ext.json"} },
      "required": ["standards"] }

[1] { "type": "object",
      "description": "Error response",
      "properties": { "errors": {"type": "array", "items": {"$ref": ".../core/error.json"}},
                      "context": {"$ref": ".../core/context.json"},
                      "ext": {"$ref": ".../core/ext.json"} },
      "required": ["errors"] }
```

Arm 0 says nothing about `errors`; arm 1 says nothing about `standards`; both are open.
A partial-success payload — "here are the standards I could read, here is what failed" —
satisfies both.

**Smallest payload matching more than one branch:**

```json
{"standards": [], "errors": []}
```

`arms_matching('content-standards/list-content-standards-response.json#/oneOf', {"standards": [], "errors": []})` → `[0, 1]`.
`errors` states no `minItems`, so `[]` suffices at the branch nodes. On the wire the
envelope adds `status` (`core/protocol-envelope.json` requires it), and the whole
document then rejects with `"... is valid under each of ..."`.

**The other five, each witnessed the same way:**

```
calibrate                 {"verdict": "pass", "errors": []}                               -> [0, 1]
create-content-standards  {"standards_id": "s", "errors": []}                             -> [0, 1]
get-content-standards     {"standards_id": "s", "errors": []}                             -> [0, 1]
get-media-buy-artifacts   {"media_buy_id": "m", "artifacts": [], "errors": []}            -> [0, 1]
validate-content-delivery {"summary": {"total_records": 0, "passed_records": 0,
                            "failed_records": 0}, "results": [], "errors": []}            -> [0, 1]
```

**Recommended upstream fix.** Add the bundle's own guard to the error arm of each of
the six — one line per file, no change to the success arm:

```json
"not": {"required": ["<the success arm's required name>"]}
```

i.e. `["verdict"]`, `["standards_id"]`, `["standards_id"]`, `["media_buy_id"]`,
`["standards"]`, `["summary"]`. This is byte-for-byte the idiom
`media-buy/refine-proposals-response.json` already uses (`"not": {"required": ["task_id"]}`).
Where upstream intends partial success to be *legal*, the fix is the opposite one —
a single arm with `anyOf: [{required: [<payload>]}, {required: ["errors"]}]` — but that
is a semantic change and a question for the owner, not a defect.

---

### Group 2.2 — sibling success shapes, guard applied to only some arms (1 union, 6 pairs)

`media-buy/build-creative-response.json#/oneOf` — arms **0,1 / 0,2 / 0,3 / 1,2 / 1,3 / 2,3**.

Six arms. The four producing/estimate arms do not forbid each other; the error and
submitted arms do.

| arm | title | `required` | `not` |
|---|---|---|---|
| 0 | `BuildCreativeSuccess` | `['creative_manifest']` | — |
| 1 | `BuildCreativeMultiSuccess` | `['creative_manifests']` | — |
| 2 | `BuildCreativeVariantSuccess` | `['creatives']` | — |
| 3 | `BuildCreativeEstimate` | `['mode', 'estimate']` | — |
| 4 | `BuildCreativeError` | `['errors']` | forbids `creative_manifest`, `creative_manifests`, `creatives`, `estimate`, `status: "submitted"` |
| 5 | `BuildCreativeSubmitted` | `['status', 'task_id']` | forbids `creative_manifest`, `creative_manifests`, `creatives`, `estimate` |

**The finding is the asymmetry.** Arms 4 and 5 carry a `not` naming exactly the keys
of arms 0–3. Arms 0–3 carry no `not` at all. The exclusion is one-directional: the
document knows which four names discriminate, and only two of its six arms say so.
All six arms are `additionalProperties: true`.

The document's own prose asserts the exclusion the arms do not state. Root:
*"Exactly one of six shapes"*. Arm 3: *"Mutually exclusive with the
success/error/submitted shapes (discriminated by `mode:"estimate"` + the estimate
object)"* — but arms 0, 1 and 2 declare no `mode` and are open, so `mode: "estimate"`
passes them. Arm 2: *"Mutually exclusive with the other success/error/submitted shapes"*
— and it forbids none of them.

**Representative, verified by hand — pair 0,3:**

```json
[0] { "title": "BuildCreativeSuccess", "type": "object",
      "properties": { "creative_manifest": {"$ref": ".../core/creative-manifest.json", ...},
                      "build_variant_id": {...}, "recipe_hash": {...}, ... },
      "required": ["creative_manifest"],
      "additionalProperties": true }

[3] { "title": "BuildCreativeEstimate", "type": "object",
      "properties": { "mode": {"type": "string", "const": "estimate",
                               "description": "Echoes the request mode; discriminates
                                 this dry-run envelope from the producing shapes."},
                      "estimate": {"type": "object",
                                   "required": ["currency","cost_low","cost_high","basis"], ...} },
      "required": ["mode", "estimate"],
      "additionalProperties": true }
```

Arm 3's `mode` const is the discriminator the description names — but it discriminates
nothing, because arm 0 never declares `mode` and admits it as an additional property.

**Smallest payload matching more than one branch (pair 0,3):**

```json
{"creative_manifest": {"format_kind": "image", "assets": {}},
 "mode": "estimate",
 "estimate": {"currency": "USD", "cost_low": 1, "cost_high": 2, "basis": "fixed"}}
```
→ arms `[0, 3]`; with `"status": "completed"` added, the whole document rejects with
the `oneOf` double-match.

**All six pairs witnessed** (`M = {"format_kind":"image","assets":{}}`,
`E = {"mode":"estimate","estimate":{"currency":"USD","cost_low":1,"cost_high":2,"basis":"fixed"}}`,
`C = [{"errors":[{"code":"x","message":"m"}]}]`):

```
0,1  {"creative_manifest": M, "creative_manifests": [M]}  -> [0, 1]
0,2  {"creative_manifest": M, "creatives": C}             -> [0, 2]
0,3  {"creative_manifest": M, **E}                        -> [0, 3]
1,2  {"creative_manifests": [M], "creatives": C}          -> [1, 2]
1,3  {"creative_manifests": [M], **E}                     -> [1, 3]
2,3  {"creatives": C, **E}                                -> [2, 3]
```

All six, plus `"status": "completed"`, are rejected by the document as `oneOf`
double-matches.

**Recommended upstream fix.** Give arms 0–3 the `not` their own descriptions already
assert, by the same construction arms 4 and 5 use — each arm forbids the other three
producing keys:

```json
"not": {"anyOf": [{"required": ["creative_manifests"]},
                  {"required": ["creatives"]},
                  {"required": ["estimate"]}]}
```

on arm 0, and the corresponding three on arms 1, 2 and 3. After that the four
`required` names are a derivable discriminator and the response has a real six-way
dispatch.

---

### Group 2.3 — "either / or" document and value shapes with no exclusion (3 unions, 5 pairs)

The same mechanism, but the arms are not success/error — they are alternative *forms*
of one value, and the prose says "either … or" or "Exactly one".

| union | arms | pairs |
|---|---|---|
| `adagents.json#/oneOf` | `['authoritative_location']` vs `['authorized_agents']` | 0,1 |
| `core/evaluator-spec.json#/oneOf` | `['exemplars']` / `['evaluator_id']` / `['agent_url']` | 0,1 0,2 1,2 |
| `registries/v1-canonical-mapping.json#/properties/mappings/items/properties/v1_pattern/oneOf` | `['format_id_glob']` vs `['structural']` | 0,1 |

**Representative, verified by hand — `core/evaluator-spec.json#/oneOf`:**

```json
[0] { "type": "object",
      "description": "Exemplar form: inline pass/fail examples that CALIBRATE a single
                      agent-defined prediction feature …",
      "properties": { "exemplars": {"type": "object", ...} },
      "required": ["exemplars"],
      "additionalProperties": true }

[1] { "type": "object",
      "description": "Identifier form: an account-scoped house evaluator preset that
                      produces creative-feature values for each leaf …",
      "properties": { "evaluator_id": {"type": "string", ...} },
      "required": ["evaluator_id"],
      "additionalProperties": true }

[2] { "type": "object",
      "description": "Agent form: an external judge agent the seller calls via the
                      get_creative_features contract …",
      "properties": { "agent_url": {"type": "string", ...} },
      "required": ["agent_url"],
      "additionalProperties": true }
```

Three "forms", three disjoint required names, three open arms, no `not` anywhere. Note
`exemplars` states no `required` of its own, so `{}` satisfies it.

**Smallest payloads matching more than one branch:**

```
{"exemplars": {}, "evaluator_id": "e"}                      -> [0, 1]
{"exemplars": {}, "agent_url": "https://x.example.com"}     -> [0, 2]
{"evaluator_id": "e", "agent_url": "https://x.example.com"} -> [1, 2]
```

`{"exemplars": {}, "evaluator_id": "e", "agent_url": "https://x.example.com"}` matches
all three.

**The other two, witnessed:**

`adagents.json#/oneOf` — arm 0 is the *"URL reference variant"* (`required:
['authoritative_location']`, `additionalProperties: true`); arm 1 the *"Inline structure
variant"* (`required: ['authorized_agents']`, `additionalProperties: true`). The root
description says *"Can either contain the full structure inline or reference an
authoritative URL"* — and neither arm forbids the other's key.

```json
{"authoritative_location": "https://cdn.example.com/adagents.json",
 "authorized_agents": [{"authorization_type": "property_ids",
                        "property_ids": ["p1"],
                        "url": "https://sales.example.com",
                        "authorized_for": "all"}]}
```
→ arms `[0, 1]`; the document rejects it as a `oneOf` double-match. A publisher who
moves to a pointer file and leaves the old inline block in place gets
`"is valid under each of"` and no indication that `authorized_agents` is the key to
remove.

`registries/v1-canonical-mapping.json#/…/v1_pattern/oneOf` — arm 0 `required:
['format_id_glob']` ("Glob pattern matched against v1 `format_id.id`"), arm 1
`required: ['structural']` ("Structural match against the format's slot shape, asset
types, and version constraints"). Neither forbids the other.

```json
{"format_id_glob": "x", "structural": {}}
```
→ arms `[0, 1]`. A registry entry that wants both a glob and a structural narrowing is
silently unexpressible, and a producer that writes both is told only that its entry is
valid under each.

**Recommended upstream fix.** Add the reciprocal `not` to each arm:

* `adagents.json` — arm 0 `"not": {"required": ["authorized_agents"]}`, arm 1
  `"not": {"required": ["authoritative_location"]}`. Arm 0 is already the narrower
  shape — it declares only `$schema`, `authoritative_location` and `last_updated` —
  so closing it with `"additionalProperties": false` is the stronger alternative and
  also fixes it.
* `core/evaluator-spec.json` — each arm forbids the other two names, or (better,
  since the three forms are a closed set named by the descriptions) add a
  `spec_kind` const — `"exemplar"` / `"identifier"` / `"agent"` — required by each
  arm. That makes the union a *declared* discriminated union, which
  `core/assets/asset-union.json` and `adagents.json`'s `authorized_agents` items both
  already do (`discriminator: {propertyName: …}` + a per-arm `const`).
* `registries/v1-canonical-mapping.json` — each arm forbids the other name. The
  arms are small and closed-shaped, so `"additionalProperties": false` on both also
  works.

---

## 3. Why no "superset" group, and no "description-only" group

The task's worked example was
`media-buy/create-media-buy-request.json#/anyOf` pair 0,1, read as a superset
required-set:

```
[0] "Explicit packages with fixed allocation"             required ['packages']
[1] "Explicit packages with seller-optimized allocation"  required ['packages','total_budget','budget_allocation']
```

**That reading is wrong and the pair is not a defect.** Arm 0 *does* pin a const — one
level down, on `budget_allocation.mode`:

```json
[0] { "title": "Explicit packages with fixed allocation",
      "properties": {
        "budget_allocation": {"properties": {"mode": {"const": "fixed"}},
                              "required": ["mode"]},
        "packages": {"items": {"allOf": [{"$ref": ".../media-buy/package-request.json"},
                                         {"required": ["budget"]},
                                         {"not": {"required": ["min_spend_target"]}}]}} },
      "required": ["packages"],
      "not": {"required": ["proposal_id"]} }

[1] { "title": "Explicit packages with seller-optimized allocation",
      "properties": {
        "budget_allocation": {"properties": {"mode": {"const": "seller_optimized"}},
                              "required": ["mode"]} },
      "required": ["packages", "total_budget", "budget_allocation"],
      "not": {"required": ["proposal_id"]} }
```

Arm 1 requires `budget_allocation` at the top level and pins `mode` to
`"seller_optimized"`; arm 0 pins the same `mode` to `"fixed"`. So every instance of arm
1 *has* `budget_allocation.mode == "seller_optimized"`, which arm 0 refuses. **No
instance satisfies both** — this is a proof, not a sampled witness: arm 1 forces
presence, and presence forces the contradiction.

Measured:

```
{"idempotency_key": "k", "account": {}, "brand": "b",
 "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-02-01T00:00:00Z",
 "packages": [], "total_budget": {}, "budget_allocation": {"mode": "seller_optimized"}}
  arm 0: no     'fixed' was expected
  arm 1: MATCH
  arm 2: no     'proposal_id' is a required property

… the same payload without budget_allocation and total_budget:
  arm 0: MATCH
  arm 1: no     'total_budget' is a required property
```

The census misses it because `harness._value_sets` and `lower.union.value_sets` read
`node["properties"][key]["const"]` and do not descend into a property's own
`properties` — a nested pin at `budget_allocation.mode` is invisible to both readings.
That is false-positive class **5.D** below.

So: of the 17 verified pairs, **the `required` sets are pairwise disjoint in all 17**.
There is no superset pair, no same-required-set pair, and no pair whose only difference
is a `description` or `title`. The hypothesised groups are empty, and the single real
group is the one in §2.

## 4. The two readings, and the three corrections, measured

Each correction is a reading the census does not take, applied on top of it. Applied in
sequence to the verifier's side:

| reading | unions | pairs |
|---|---|---|
| census as shipped | 23 | 300 |
| \+ conjoin the ancestors' `required` (`adcp.types._base.applied_schema`) | 21 | 254 |
| \+ resolve `$ref` into the branch (hoisting `properties`/`required`) | 15 | 36 |
| \+ hand verification (§5.C, §5.D, §5.E) | **10** | **17** |

The first two corrections are mechanical and reproducible; the third is the five
documents of §5.C–E, each read by hand. The walk's side gives the same numbers at
every row.

## 5. Verified NOT a defect — 13 unions, 283 pairs

All 283 are artefacts of what the two `separates` readings deliberately do not read.
Four of the five classes are the instrument's own stated limits; the fifth is the
population gate.

### 5.A — The separator is in the `$ref` target (6 unions, 218 pairs)

`harness._views`: *"A `$ref` conjunct contributes NOTHING: the fact is in the target,
and §4's 'a pair the derivation cannot separate is treated as overlapping' is what that
costs."* The census docstring says the same and reports the `$ref` half rather than
fixing it. These are that cost, now paid.

**`core/assets/asset-union.json#/oneOf` — 210 pairs, all of them, and the single
largest entry in the census.** 21 branches, each a bare `$ref`:

```json
"discriminator": {"propertyName": "asset_type"},
"oneOf": [{"$ref": ".../core/assets/image-asset.json"},
          {"$ref": ".../core/assets/video-asset.json"}, …]
```

Measured over all 21 targets: every one declares `asset_type` with a `const`, every one
lists `asset_type` in `required`, and **all 21 consts are distinct** (`image`, `video`,
`audio`, `vast`, `display_tag`, `text`, `url`, `html`, `javascript`, `zip`, `webhook`,
`css`, `daast`, `markdown`, `brief`, `catalog`, `published_post`, `card`,
`pixel_tracker`, `vast_tracker`, `daast_tracker`). This is a textbook declared
discriminated union — `discriminator` keyword and all — and all 210 pairs separate on
§4's first separator once the target is read. **No payload matches two branches.**

The other five:

| union | pairs | the separator, in the target |
|---|---|---|
| `creative/get-creative-features-response.json#/oneOf` | 0,1 0,2 | arm 0 `$ref`s `creative/get-creative-features-terminal-success.json`, whose `required` is `['results']`; arms 1 and 2 both carry `not: {anyOf: [{required: ['results']}, …]}` — forbidden by name |
| `media-buy/decline-proposals-response.json#/anyOf` | 0,1 | arm 1 `$ref`s `core/compact-task-submitted.json` (`required: ['status','task_id']`); arm 0's `not: {anyOf: [{required: ['status']}, {required: ['task_id']}]}` forbids both |
| `media-buy/refine-proposals-response.json#/anyOf` | 0,1 | same pair; arm 0's `not: {required: ['task_id']}` |
| `media-buy/request-proposals-response.json#/anyOf` | 0,3 1,3 2,3 | arm 3 is the same `compact-task-submitted` `$ref`; arms 0–2 each forbid `task_id` by name |
| `brand.json#/oneOf` | 2,4 | arm 2 (`Brand Agent`) is `additionalProperties: false` over `{$schema, version, agents, brand_agent, contact, data_subject_contestation, last_updated}`; arm 4 `$ref`s `#/definitions/brand`, whose `required` is `['id','names']` — neither name is in arm 2's closed map, so arm 2 refuses every instance of arm 4 |

**Why this is not a hole to be plugged in the instrument.** Resolving `$ref` to decide
disjointness means the derivation's answer depends on a document it is not reading at
that pointer, and §9's "do not decide a position the bundle does not hold from a view of
it" is the reason both spellings decline. The deferral is correct; the measurement above
is the thing that was missing, not the resolution.

### 5.B — The ancestors' `required` is not conjoined (2 unions, 46 pairs)

The census calls `separates(...)` without its `root_required` argument, so the
presence gate — *"the key has to be present in every instance of one of the two
branches"* — is evaluated with an empty set. CLAUDE.md's rule, **requiredness is a
conjunction**, is exactly this.

**`core/postal-country-system.json#/anyOf` — 45 pairs, all of them.** Root:

```json
"properties": {"country": {"type": "string", "pattern": "^[A-Z]{2}$"},
               "system":  {"$ref": ".../enums/postal-system.json"}},
"required": ["country", "system"]
```

Ten branches, each constraining `country`:

```
0 {"const": "US"}   1 {"const": "GB"}   2 {"const": "CA"}   3 {"enum": ["DE","CH","AT"]}
4 {"const": "FR"}   5 {"const": "AU"}   6 {"const": "BR"}   7 {"const": "IN"}
8 {"const": "ZA"}   9 {"not": {"enum": ["US","GB","CA","DE","CH","AT","FR","AU","BR","IN","ZA"]}}
```

The ten sets are pairwise disjoint (branch 9 is the complement of the union of the
other nine) and `country` is required by the **root**, so the presence gate is
satisfied for every pair. All 45 separate; **no payload matches two branches.** The
`lower.union.separates` docstring already names this document as the case that drove
the set-valued reading — the remaining gap was never the sets, it was the gate's
argument.

**`creative/preview-creative-response.json#/oneOf/1/properties/results/items/oneOf` —
1 pair.** The two arms pin `success`:

```json
[0] {"title": "PreviewBatchResultSuccess", "properties": {"success": {"const": true}},
     "required": ["response"]}
[1] {"title": "PreviewBatchResultError",   "properties": {"success": {"const": false}},
     "required": ["errors"]}
```

Neither arm requires `success` — and the enclosing `items` node does:
`"required": ["success", "creative_id"]`. This is the case CLAUDE.md names in so many
words: *"`success` looks optional on `creative/preview-creative-response.json`'s batch
arms and is required by their parent."* Two disjoint one-member sets on a key the
parent requires: separated. **No payload matches both.**

### 5.C — The exclusion is a sibling of the combinator (2 unions, 2 pairs)

`separates` takes the ancestors' `required`, but not the ancestors' `not`. Two
documents state the mutual exclusion there.

| union | pair |
|---|---|
| `media-buy/buy-products-request.json#/anyOf` | 0,1 |
| `media-buy/request-proposals-request.json#/anyOf` | 0,1 |

Both have the same two arms, and in both the arms genuinely overlap:

```json
[0] {"required": ["brand"]}
[1] {"properties": {"account": {"required": ["brand", "operator"]}}}      // buy-products
[1] {"properties": {"account": {"required": ["brand", "operator"]}},
     "required": ["account"]}                                              // request-proposals
```

And both documents' prose says the overlap is forbidden — `buy-products-request`:
*"Brand source required when account is ID-only. **Omit when account already contains
brand and operator**"* and *"A natural-key account is the single brand source and **MUST
NOT be combined with top-level brand**"*; `request-proposals-request`: *"Provide either
top-level brand or a natural-key account containing brand and operator, **not both**."*

**The prose is enforced** — at `allOf/1`, in both documents, identically:

```json
{"not": {"properties": {"account": {"required": ["brand", "operator"]}},
         "required": ["account", "brand"]}}
```

Measured against that guard:

```
both                       -> REFUSED
top-level brand only       -> passes
account natural key only   -> passes
```

and the whole `request-proposals-request.json` document rejects the both-payload with
`"should not be valid under …"`. So the overlap region is empty for every instance that
reaches the `anyOf`; the pair is separated, by a statement about the same instance that
is neither branch's. **Not a defect** — though it is worth noting to the owner that the
two documents state the same rule twice in two places (the `anyOf` and the `allOf/1`
`not`), which is why the arms look permissive read alone.

### 5.D — The pin is nested one level below `properties` (1 union, 1 pair)

`media-buy/create-media-buy-request.json#/anyOf` pair 0,1 — §3 above, in full. Arms 0
and 1 pin `budget_allocation.mode` to `"fixed"` and `"seller_optimized"`, and arm 1
requires `budget_allocation`, so the pair is disjoint. Both `_value_sets` readings stop
at the top-level property declaration and never see it. **Not a defect.**

### 5.E — The `anyOf` is a cardinality or capability guard, not a dispatch (2 unions, 16 pairs)

These two are false positives of the census's **population gate**, not of `separates`.
`unions()` admits a combinator whose arms each state `properties`, and excludes only
`schema_parse.presence_only` ones. An arm that states both `properties` and a
constraint (a `minItems`, a `const`) passes the gate while being a constraint on one
key rather than an alternative shape. The arms of these two unions overlap by design,
there is nothing to dispatch to, and the overlap is accepted by the document.

**`adagents.json#/oneOf/1/allOf/0/anyOf` — 15 pairs, all of them.** Six arms. The
document says what it is, in its own `$comment` on that very node:

> *"A file MUST carry either sales authorization or catalog content. `authorized_agents`
> MAY be empty (`[]`) for a catalog-only community mirror that publishes
> formats/properties/placements/collections/signals …; a file with neither sales
> authorization nor non-empty catalog content is rejected. **Each arm asserts
> non-emptiness directly** so the guard does not depend on the per-field minItems of the
> catalog arrays."*

```json
[0] {"properties": {"authorized_agents": {"minItems": 1}}}
[1] {"properties": {"formats": {"minItems": 1}},     "required": ["formats"]}
[2] {"properties": {"properties": {"minItems": 1}},  "required": ["properties"]}
[3] {"properties": {"placements": {"minItems": 1}},  "required": ["placements"]}
[4] {"properties": {"collections": {"minItems": 1}}, "required": ["collections"]}
[5] {"properties": {"signals": {"minItems": 1}},     "required": ["signals"]}
```

This is "at least one of these six arrays is non-empty" — an OR, and a publisher with
both sales authorization and catalog content satisfies two arms by design. Arm 0 states
no `required` because the enclosing `oneOf/1` already requires `authorized_agents`
(the `applied_schema` conjunction supplies it), so arm 0 reads as "non-empty", not as a
vacuous truth. Measured — a file with non-empty `authorized_agents` *and* non-empty
`properties` matches arms 0 and 1, **and the whole document accepts it**:

```json
{"authorized_agents": [{"authorization_type": "property_ids", "property_ids": ["p1"],
                        "url": "https://sales.example.com", "authorized_for": "all"}],
 "properties": [{"property_id": "p1", "property_type": "website", "name": "N",
                 "identifiers": [{"type": "domain", "value": "example.com"}],
                 "publisher_domain": "example.com"}]}
```
→ `VALID`. **Not a defect.**

**`trusted-match/provider-registration.json#/anyOf` — 1 pair.**

```json
[0] {"properties": {"context_match":  {"const": true}}, "required": ["context_match"]}
[1] {"properties": {"identity_match": {"const": true}}, "required": ["identity_match"]}
```

`context_match` is *"Provider handles Context Match requests (POST /context)"* and
`identity_match` is *"Provider handles Identity Match requests (POST /identity)"* — two
independent capability booleans. The `anyOf` means "declare at least one capability". A
provider that handles both satisfies both arms, which is the intent:

```json
{"provider_id": "p", "endpoint": "https://x.example.com",
 "context_match": true, "identity_match": true,
 "countries": ["US"], "uid_types": ["uid2"]}
```
→ `VALID` against the whole document (the `countries`/`uid_types` requirement comes from
the document's own `if`/`then` on `identity_match`). **Not a defect.**

**Worth raising with the owner, as a measurement rather than a defect:** these two
unions declare no branch classes a consumer could choose between, so admitting them to
the population costs 16 of the census's 300 pairs and makes the headline figure look
worse than the bundle is. A population gate that also excluded an arm whose
`properties` entries state only a `minItems` or a `const` on a single key — "an arm
that narrows one key rather than describing a shape" — would drop both. That is a
change to `docs/plan/10l30-census.py`'s `unions()`, which is outside this task's write
scope and is the owner's call.

## 6. Summary by group

| group | kind | unions | pairs |
|---|---|---|---|
| 2.1 | success-vs-error arms, no mutual `not` (one repeated pattern, 6 files) | 6 | 6 |
| 2.2 | sibling success shapes, `not` on only 2 of 6 arms | 1 | 6 |
| 2.3 | "either/or" forms with no exclusion at all | 3 | 5 |
| | **verified defect** | **10** | **17** |
| 5.A | separator in the `$ref` target | 6 | 218 |
| 5.B | ancestors' `required` not conjoined | 2 | 46 |
| 5.C | exclusion is a sibling `not` of the combinator | 2 | 2 |
| 5.D | pin nested one level below `properties` | 1 | 1 |
| 5.E | `anyOf` is a cardinality/capability guard, not a dispatch | 2 | 16 |
| | **verified NOT a defect** | **13** | **283** |
| | census total | 23 | 300 |

All 17 defects are `oneOf`; all 10 have pairwise-disjoint `required` sets; in all 10 the
missing statement is the same one, and the bundle already spells it five other places.
