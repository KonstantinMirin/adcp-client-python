# Schema patterns that resist code generation

What it costs downstream to turn the AdCP bundle into typed Python, which authoring patterns
cost the most, and what the schema could do instead.

**The population, stated once.** Every figure here is a property of bundle version **3.2**:
1,625 JSON files, of which **1,054 are portable documents** — the other 571 are `mcp/` (452) and
`bundled/` (116) projections of those, plus three bundle-level manifests. Over the 1,054 the
compiler **emits 769 modules and refuses 285 documents**. Of the 285, **176 are verdicts** — the
obstruction is in the document, in draft-07's structure, or in Pydantic — and **109 are
deferrals**, meaning we have not written that code yet. Only the verdicts are evidence about the
schema.

**The four things worth remembering.**

1. **Five patterns account for 251 of the 285 refusals**, and they trace back to only
   **118 sites** in **118 documents**. One mechanism — a plain keyword sitting beside a `oneOf`,
   at a root or nested — is **134 refusals, 47% of the total, from 75 sites**. The chaining is
   why: a `$ref` to a refused document refuses too, so one root keyword in
   `core/format-option-ref.json` blocks 14 documents.
2. **Two of the three biggest have a schema-side fix that keeps the accepted set exactly
   unchanged.** In one case the fix is deleting a keyword that is already redundant with every
   branch.
3. **The refusals are not where the ergonomic cost is.** The documents that *do* compile produce
   39 fields typed `dict[str, Any]`, 7 typed `Any`, and **85 of 157 constraint aliases named by a
   hex digest of a regex** — `currency: StrMatching43E30B32` appears in 29 emitted modules where
   the schema's own description says "ISO 4217 currency code".
4. **Faithful and ergonomic are in tension, and some patterns force a choice between them.** Our
   rule is that the model must never accept less than its document. A pattern that can only be
   rendered by widening gets refused instead of silently loosened — which is why a cheap schema
   change can convert a refusal into a named type rather than into `Any`.

**How each theme is tagged.** These are four different asks of four different people and mixing
them wastes the meeting.

| tag | meaning |
| --- | --- |
| **SCHEMA** | the bundle can change this, and the accepted set stays the same |
| **DRAFT-07** | draft-07 has no clean way to say what the document means; a newer draft or an explicit statement would |
| **PYDANTIC** | no rendering exists in Pydantic v2 |
| **OURS** | the generator has not written it yet; named here because the schema pattern is what makes it expensive |

**The measured spine.** Refusals grouped by the root of their chain:

| pattern | refusals | root sites | root documents | kind | theme |
| --- | --- | --- | --- | --- | --- |
| a plain keyword beside a **root** `oneOf`/`anyOf` | 107 | 61 | 61 | verdict | 1 |
| `allOf: [{$ref: …}]` whose target is not an object | 66 | 25 | 25 | deferred | 2 |
| `uniqueItems` on an array no class holds | 34 | 13 | 13 | verdict | 5 |
| a constraining sibling of a **nested** `oneOf`/`anyOf` | 27 | 14 | 14 | deferred | 1 |
| a conjunct restating a property neither identically nor narrowly | 17 | 5 | 5 | verdict | 4 |
| everything else (14 further patterns) | 34 | 26 | 26 | mixed | 3, 5, 6 |

---

## 1. A plain keyword beside a `oneOf` — 134 refusals from 75 sites

**SCHEMA** (cheap, exact) **+ DRAFT-07**

One mechanism at two positions: 107 refusals from 61 root sites, plus 27 from 14 nested sites.
Together, **47% of all 285 refusals**.

### What the pattern is, at a root

A document's root carries a `oneOf`/`anyOf` *and* ordinary keywords. 156 of the 1,054 portable
documents have a root union; **116 of them carry at least one non-annotation sibling** — root
`properties` at 88, root `allOf` at 55, root `additionalProperties` at 55, root `required` at 41.

`core/format-option-ref.json`, root:

```json
{
  "type": "object",
  "discriminator": { "propertyName": "scope" },
  "oneOf": [ { "…publisher branch…" }, { "…product branch…" } ],
  "additionalProperties": true
}
```

`core/creative-manifest.json`, root: `properties` + `required` + `not` + `oneOf` (two presence
branches, `format_id` vs `format_kind`) + `allOf` (two `if`/`then`/`else` conjuncts) +
`additionalProperties`.

### What it costs

Draft-07 applies a root keyword to the same instance each branch describes, so the conjunction is
real — but **no JSON pointer names it**. `#/oneOf/0` names the branch; nothing names
"branch 0 conjoined with the root's `additionalProperties`". A branch class that carries the root
keyword therefore states a fact its own pointer does not, and our grader cannot pair the class
with a node. The refusal, verbatim:

```
refused core/creative-manifest.json (verdict) at / on allOf: a root 'allOf' is a conjunction
with every branch (draft-07), and a branch class that carries it -- as a field of its own, or as
a base inherited through the root's class -- states a fact its own #/oneOf/<i> node does not:
there is no pointer to the conjunction for it to name
```

Blast radius, measured: `core/format-option-ref.json` root `additionalProperties` → **14**
documents refused. `core/creative-manifest.json` root `allOf` → **9**.
`core/product-format-declaration.json` → **8**. `core/audience-characteristic.json` → **6**.
`core/assets/vast-asset.json` root `properties` → **5**.

### What would make it tractable

**Give the conjunction a pointer.** Move the root's own keywords inside each branch, with the
shared part behind a `$ref`:

- `{ "properties": P, "oneOf": [A, B] }`
- → `{ "oneOf": [ {"allOf": [{"$ref": "#/definitions/common"}, A]}, {"allOf": […, B]} ] }`

The accepted set is identical; every fact now sits at a pointer the document holds, and each
branch becomes a class that composes a named base.

**And one of these is free.** `core/format-option-ref.json`'s root `additionalProperties: true`
is **already restated by both branches** — `"additionalProperties": true` appears at
`#/oneOf/0` and `#/oneOf/1`. Deleting the root copy changes nothing about what the document
accepts and unblocks 14 documents. That is the cheapest single change in this note.

*An honest note on our side.* `docs/plan/architecture.md` §13 item 3 records this as an open
decision: we could extend the grader to read "branch node conjoined with the root's
same-instance keywords" as a legitimate position rather than as a derived view. If that reading
is accepted, some of the 107 clear without a schema change. The schema-side fix is still worth
making, because it is the version that needs no reader to agree with us.

### The same mechanism one level down — a further 27 refusals from 14 sites

A `oneOf`/`anyOf` at a *nested* position lowers to one Python type, `A | B`, which has no slot for
a fact of its own. **89 nested union sites in portable documents carry a constraining sibling**;
14 of them refuse, chaining to 27.

`content-standards/artifact.json`, `/$defs/asset_access`:

```json
{ "type": "object",
  "discriminator": { "propertyName": "method" },
  "oneOf": [ { "type": "object", "…" }, { "type": "object", "…" } ] }
```

```
refused content-standards/artifact.json (deferred) at /$defs/asset_access on type: a sibling of
a nested oneOf/anyOf is a CONJUNCTION with every branch (draft-07), and a nested union lowers to
one type -- A | B -- which has no slot for a fact of its own … dropping it is a model wider than
its document
```

Blast radius 5. **And here the sibling is already redundant: every branch states
`"type": "object"` itself.** At **20 of the 89 sites the only sibling is a bare `type`** — 2 of
those are provably redundant without resolving a `$ref`, and the other 18 have `$ref` branches
whose targets very likely state the same word. That is worth an upstream sweep: each redundant
copy deleted is a document that compiles.

Where the sibling is *not* redundant (26 of the 89 sites state
`additionalProperties` + `properties` + `required` + `type` beside the union), the fix is theme
1's: push the shared part into each branch behind a `$ref`, or hoist the union into its own
document so it gets a root and a base class that can carry the sibling.

---

## 2. `allOf: [{"$ref": …}]` used to attach a description — 66 refusals from 25 documents

**OURS**, driven by a **DRAFT-07** limitation

### What the pattern is

Draft-07 ignores every sibling of `$ref`. So to attach a `description` to a reference, authors
wrap it:

`core/frequency-cap.json`, `/properties/per`:

```json
{ "allOf": [ { "$ref": ".../enums/reach-unit.json" } ],
  "description": "Entity granularity for impression counting. Required when max_impressions is set." }
```

The portable documents hold **235 single-`$ref` `allOf` wrappers**; **50 of them carry nothing but
a `description`**, and a further 38 are a document root whose only other keys are `$schema` and
`title`. (Over all 1,625 files — the `bundled/` projections inline everything — the count is
1,386.)

### What it costs

An `allOf` of `$ref`s makes the targets *bases*. Where the target is an enum, a scalar alias, a
container or a union root, there is no class to subclass:

```
refused core/frequency-cap.json (deferred) at /properties/per/allOf/0 on allOf:
ReachUnit is not a class, so it cannot be a base (D2 makes a scalar root an Annotated alias,
and subclassing one is a TypeError at import)
```

Blast radius: `core/delivery-metrics.json` `/properties/reach_unit/allOf/0` → **14** documents;
`core/product.json` `/properties/publisher_properties/items/allOf/0` → **7**;
`core/vendor-pricing-option.json` `/allOf/1` → **6**.

### What would make it tractable

**This one is ours and we have written down the answer**: where the target is not a class, it is
the node's own *type* and the wrapper's siblings constrain it. The reason it belongs in this note
is the 235: the idiom is this prevalent precisely because draft-07 forbids the thing the author
wanted to write, so a generator meets it everywhere rather than at a handful of sites — and 25 of
those sites currently cost 66 documents.

The schema-side observation worth making to the group: in **2020-12 a `$ref` takes siblings**, so
the wrapper disappears entirely and `{"$ref": …, "description": …}` means what it reads as. If a
draft migration is ever on the table, this is the pattern it deletes.

---

## 3. Branches a reader cannot tell apart — undiscriminated `oneOf`

**SCHEMA** (cheap, and the bundle already has the idiom in one place)

### What the pattern is

The bundle declares `discriminator` at **81 sites** in portable documents, and that is the good
case. Two root unions have branches that nothing separates.

`adagents.json`, root `oneOf`:

| branch | `required` | `additionalProperties` |
| --- | --- | --- |
| `/oneOf/0` | `["authoritative_location"]` | `true` |
| `/oneOf/1` | `["authorized_agents"]` | `true` |

Neither branch forbids the other's key, so `{"authoritative_location": …, "authorized_agents": …}`
satisfies both.

`brand.json`, root `oneOf` of five titled branches. `/oneOf/1` "House Redirect" and `/oneOf/3`
"House Portfolio" both require only `house`. `/oneOf/4` "Brand Canonical Document" requires
nothing and declares nothing at the branch node, so it overlaps all four others.

### What it costs

We will not dispatch by trying branches in order, because that makes the answer a property of
declaration order rather than of the payload. So the document refuses:

```
refused brand.json (deferred) at / on oneOf: no branch dispatch is derivable and the branches
OVERLAP: … The branches confirm no such property (the properties each branch pins are
[[], [], [], [], []]), and these pairs are separated by no pinned const, no required name the
other forbids and no scalar type: ['/oneOf/0 and /oneOf/4', '/oneOf/1 and /oneOf/3',
'/oneOf/1 and /oneOf/4', '/oneOf/2 and /oneOf/4', '/oneOf/3 and /oneOf/4']
```

Separately, **4 of the 44 union bases we do emit dispatch on pairwise disjointness rather than on
a shared `const`** — `core/account-ref.json`, `core/canonical-account-ref.json`,
`core/audience-selector.json`, `a2ui/bound-value.json`. The cost there is ergonomic, not
faithfulness. From `core/account_ref.py`:

```python
class AccountReference(BranchDispatchMixin, AdCPBaseModel):
    _BRANCH_DISCRIMINATOR: ClassVar[str] = ""

class AccountReferenceAccountId(AccountReference): ...
class AccountReferenceBrandOperator(AccountReference): ...
```

With an empty discriminator there is no `Field(discriminator=…)`, so a bad payload is reported
against *every* branch instead of one; and because the branches carry no `title`, the
consumer-visible class name is derived from the sorted `required` set — adding a required
property upstream renames the class.

### What would make it tractable

Two options, both already used elsewhere in this bundle:

- **Pin a `const` on one shared property.** 81 sites already do; `core/format-option-ref.json`
  pins `scope`, `content-standards/artifact.json`'s `asset_access` pins `method`.
- **Make the branches mutually exclusive explicitly.** `core/creative-manifest.json` writes it
  out: branch 0 is `{"required": ["format_id"], "not": {"required": ["format_kind"]}}` and
  branch 1 the mirror image. Adding the same two `not` clauses to `adagents.json`'s branches
  makes them provably disjoint and changes nothing a conforming validator accepts, because
  `oneOf` already rejects an instance satisfying both.
- **Give every branch a `title`.** It costs nothing and it is the name a consumer imports.

---

## 4. A conjunct that restates a property neither identically nor narrowly — 17 refusals from 5 documents

**SCHEMA**

### What the pattern is

The second conjunct of an `allOf` re-declares a property in order to pin something nested inside
it, but writes only the part it cares about.

`core/assets/url-asset.json`, `/properties/macro_declarations/items`:

```json
{ "allOf": [
    { "$ref": ".../core/macro-declaration.json" },
    { "properties": { "location": { "properties": { "field": { "const": "url" } } } } } ] }
```

`core/macro-declaration.json` declares `location` fully: `type: object`, three properties,
`required: ["field","occurrence","context"]`, `additionalProperties: false`. The overlay declares
`location` as an object schema with one nested property and nothing else.

### What it costs

Draft-07 conjoins the two, so the accepted set is right. But a class has **one** field named
`location`, and the two declarations are not in a narrowing relation — the overlay states strictly
fewer keywords about `location` than the base does, so neither "take the base's" nor "take the
overlay's" is correct:

```
refused core/assets/url-asset.json (verdict) at
/properties/macro_declarations/items/allOf/1/properties/location on additionalProperties:
the restatement of 'location' neither matches nor narrows the inherited declaration:
inherited states ['additionalProperties', 'properties', 'required', 'type'],
this states ['properties']
```

Blast radius: this one pointer refuses **13** documents, including every asset type that reaches
it (`core/assets/card-asset.json`, `core/assets/pixel-tracker-asset.json`, `core/app-item.json`).

### What would make it tractable

**Restate the property as a narrowing of the inherited declaration, not as a fragment of it** —
repeat `type`, `required` and `additionalProperties`, and narrow `field` from the five-member
`enum` to `const: "url"`. That is a pure narrowing and composes to one field.

Better still, and reusable: publish the narrowed variant as its own document
(`core/macro-declaration-in-url.json` composing `macro-declaration.json` with the narrowed
`field`) and `$ref` it from `items`. That is a named type a consumer can reach, instead of an
anonymous overlay.

**The same class of problem, in a milder form, shows up in the version envelope.**
`core/version-envelope.json`'s own description names the cause:

> Strict (`additionalProperties: false`) request schemas also redeclare these two fields in their
> own `properties` via `$ref`, because draft-07 does not evaluate properties across `allOf`.

So `account/list-account-changes-request.json` has `allOf: [{$ref: version-envelope}]` *and*
`properties.adcp_version: {"$ref": "…#/properties/adcp_version"}`. After composition the
reference sits beside the base's `type`, `pattern`, `minimum` and `maximum` — and draft-07
ignores siblings of `$ref`, so those are inert. The run reports it rather than silently
honouring them:

```
carries nothing for account/list-account-changes-request.json at /properties/adcp_major_version:
minimum: a constraining sibling of $ref, which draft-07 ignores, so the keyword constrains no
instance and the document's accepted set is the target's alone
```

15 such reports over 5 documents. Nothing is wrong with what the document accepts; the point is
that **a keyword here reads as a constraint and is not one**, and anybody auditing the bundle by
eye will believe it. This is draft-07's `additionalProperties`/`allOf` gap, and it is also the
pattern a draft migration deletes.

---

## 5. A constraint with nowhere to live — 40 refusals

**PYDANTIC** mostly, with a partial **SCHEMA** route

### What the pattern is

Three variants of one shape: a keyword stated at a position where the only thing that could
carry it does not exist.

**`uniqueItems` on an array that no class holds** — 34 refusals from 13 sites. We enforce
`uniqueItems` as a rule on the class holding the array; **18 of the bundle's 485 `uniqueItems`
sites** have no class above them — a document root, a `definitions` entry, a mapping value, a
combinator branch.

`core/forecast-point-dimensions.json` is a root array: `type: array`, `minItems: 1`,
`uniqueItems: true`. `media-buy/acceptance-policy-profile.json` states it at
`/properties/region_aliases/additionalProperties` — a mapping value.
`core/vast-tracker-constraints.json` at `/definitions/vast_versions`.

**A string keyword on a union containing a non-string arm** — 4 refusals.
`core/attestation-reference.json`, `/properties/embedded_credential/properties/value`:
`{"type": ["object","string"], "minLength": 1}`. In JSON Schema `minLength` constrains strings
only, so the document is correct; a generator has to split the union to place it. This exact node
is one of the ten verified model defects in `docs/plan/defect-inventory.md` (D1-c): a previous
generator carried `minLength` onto the object arm, so `{}` was refused with
*"Value should have at least 1 item"* — a model narrower than its document.

**`maxLength` beside `format: uri`** — 2 refusals, `core/reporting-delivery-capabilities.json`
`/properties/operations_contact/properties/url` and
`error-details/governance-agent-not-accepted.json`
`/oneOf/0/properties/attempted_agent_origin`. `format: uri` selects a URL type; Pydantic refuses
to apply a string length bound to one.

### What it costs

```
refused core/forecast-point-dimensions.json (verdict) at / on uniqueItems: … this array has no
class above it -- it is a document root, a definitions entry, a mapping value or a combinator
branch, which is 18 of the bundle's 485 sites.  The one other channel is the annotation, and
pydantic v2 removed unique_items: Constraints(uniqueItems=True) renders bare list[X], so
carrying it there would be a model wider than its document and silently so.
```

Blast radius: `core/forecast-point-dimensions.json` → **8** documents;
`media-buy/acceptance-policy-profile.json` → **6**; `core/vast-tracker-constraints.json` → **4**.

### What would make it tractable

`uniqueItems` is **Pydantic's**: v2 removed `unique_items` and there is no annotation that says
it. There is no schema-side rewrite that preserves the accepted set — "unique" is the fact being
stated. The only schema-side lever is *position*: an array hoisted into its own document with a
`title` gets a `RootModel` class that can hold the rule. That is worth doing for the 13 sites
that currently block 34 documents, and it has the side benefit of giving the array a name.

For the type-list case the fix is exact and cheap: write
`{"oneOf": [{"type": "string", "minLength": 1}, {"type": "object"}]}`. Same accepted set, and
each keyword now sits on the arm it constrains.

For `maxLength` beside `format: uri`: decide which one is normative. If the length bound matters,
drop `format: uri` and keep `type: string` with `pattern` + `maxLength`; if the URI-ness matters,
drop the bound. As written, a faithful model can carry only one of the two.

---

## 6. Documents that are not types — 12 refusals

**SCHEMA** (a declaration, not a rewrite)

### What the pattern is

Three kinds of document live in the bundle alongside payload schemas, and none of them describes
a payload.

**Constraint overlays.** `core/targeting-unknown-age-eligibility-constraint.json` is, in full,
`{$schema, title, description, if, then}` — no `type`, no `properties`. It is a fragment meant to
be composed into `targeting.json` via `allOf`. Also
`core/targeting-verified-age-basis-constraint.json`. 6 refusals, blast radius 5 from the first.

**Registries.** `core/asset-group-vocabulary.json`'s root keys are
`['governance', 'lastUpdated', 'version', 'vocabulary']` — instance data, not schema keywords.
Also `core/format-shape-vocabulary.json`, `creative/asset-types/index.json`
(`['adcp_version', 'architecture', …]`), `extensions/index.json` (`['_generated', '_generatedAt',
…]`), `registries/v1-canonical-mapping.json`. 5 refusals.

**Alias documents.** `core/signal-pricing-option.json` is a bare
`{"$ref": ".../core/vendor-pricing-option.json"}` at its root.

**Meta-schemas.** `extensions/extension-meta.json` is a schema *for* schemas: its `properties`
are the keys `type`, `properties`, `required`, `additionalProperties`.

### What it costs

```
refused core/asset-group-vocabulary.json (verdict) at / on type: the root declares no kind
keyword at all: ['governance', 'lastUpdated', 'version', 'vocabulary'] are data keys, not schema
keywords, so there is no type, no properties and no composition to read -- and a class over them
would state what no part of this document declares
```

```
refused core/targeting-unknown-age-eligibility-constraint.json (verdict) at / on if:
a root is exactly one kind and this one states 'if'
```

```
refused core/signal-pricing-option.json (verdict) at / on $ref: a root that is a bare reference
to '…/core/vendor-pricing-option.json' would bind this module's own symbol to a class another
module declares, which is a second import path for one class
```

### What would make it tractable

These are not defects — the documents are doing a real job. The cost is that **a consumer of the
bundle cannot tell from the document what kind of thing it is**, so a generator either guesses or
refuses, and we refuse.

The ask is a declaration, not a rewrite: **a bundle-level statement of each document's kind** —
payload schema / constraint overlay / registry / alias / meta-schema. One key
(`x-adcp-document-kind`) or one manifest table. Then a generator skips an overlay by
declaration instead of refusing it on a keyword, and a reviewer reading the refusal report sees
12 fewer entries that are not about anything.

The registries have a second option worth considering: they are data, and data served from a
`schemas/` tree will keep being read as schema.

---

## 7. An object with no `properties`, and a property with no type

**SCHEMA** where the value set is knowable. This is the whole of the ergonomic cost, and none of
it shows up in the refusal report.

### What the pattern is

`type: object` with no `properties` can only become `dict[K, V]`, which loses every name.
Over the 1,054 portable documents: **97 such nodes with an open value schema** and **71 with a
typed one**.

Separately, **43 property declarations in 24 documents state nothing but annotations** — a
`description`, or only a `default`. In JSON Schema that admits any JSON value, null included.

`core/response.json`:

```json
"data": { "description": "AdCP task-specific response data (see individual task response schemas)" }
```

`protocol/get-task-status-response.json`, `/properties/result`, whose description says:

> Consumers and sellers MUST resolve and validate the exact schema through
> `manifest.task_result_resolution`: use `terminal_schema_overrides[task_type]` when present,
> otherwise `tools[task_type].response_schema`.

### What it costs

39 fields typed `dict[str, Any]` and 7 typed `Any` in the emitted tree. Verbatim:

```python
# protocol/get_task_status_response.py
result: Annotated[dict[str, Any] | None, Field(description='Canonical task-specific terminal payload. …')] = None

# core/response.py
data: Annotated[Any | None, Field(description='AdCP task-specific response data …')] = None

# governance/policy_ref.py
config: Annotated[dict[str, Any] | None, Field(description="Brand-specific parameter overrides for configurable policies. The accepted shape depends on the policy's config_schema.")] = None
```

Each of these is **faithful** — the document really does admit any object there — and each is the
exact opposite of **ergonomic**. The consumer reaches `Any` and the type system stops helping.
And the annotation-only form is actively dangerous: `docs/plan/defect-inventory.md` D1-a is three
verified model defects from exactly this shape, because a generator read "no type" as "optional
string" and refused an explicit `null` the document accepts.

### What would make it tractable

Three cases, three answers:

- **The value set is a closed set of documents** (`get_task_status.result`,
  `core/async-response-data.json`). Say so: a `oneOf` of `$ref`s to the concrete response
  documents, or a `discriminator` on `task_type`. That turns `dict[str, Any]` into a
  discriminated union the consumer can `match` on. The bundle's own
  `manifest.task_result_resolution` already holds the table — the schema just does not reference
  it from the field.
- **The value set is genuinely open** (`policy_ref.config`, `si_capabilities.extensions`). Then
  `additionalProperties: true` *with* a `description` saying so is already the right document,
  and `dict[str, Any]` is the honest rendering. Say it explicitly so the gap reads as a decision
  rather than an omission.
- **A property declaring only a `description`.** Add `type` — or, where any JSON value really is
  admitted, state it (`"type": ["object","array","string","number","boolean","null"]`) so no
  generator has to infer it. 43 sites, 24 documents.

---

## 8. A real constraint in a namespace no validator reads — 179 sites, 135 documents

**SCHEMA** (a statement about normativity)

### What the pattern is

`x-adcp-validation` carries constraints JSON Schema cannot express.
`core/forecast-point-dimensions.json` says so in the keyword itself:

```json
"x-adcp-validation": {
  "unique_item_properties": ["kind"],
  "description": "`dimensions[]` is an array for readable intersection syntax, but `kind` is a
    logical set key. JSON Schema draft-07 cannot express unique-by-property for this array shape,
    so conformance tooling should reject repeated `kind` values."
}
```

**179 sites in 135 of the 1,054 portable documents.** Alongside it: `errorMessage`, an
`ajv-errors` extension, at 2 sites (`media-buy/sync-catalogs-request.json` `/allOf/1` and
`/then`), which we refuse by name and report.

### What it costs

A model cannot enforce an `x-` keyword without becoming **narrower than its document**, because
no conforming validator reads one — so the model would refuse payloads the protocol admits.
We therefore compile all 179 to nothing.

And when a generator *does* enforce one, the grading breaks. From the defect inventory, on a
previous output:

> `change_term.py:78` raises `constraint kind is incompatible with action`. That rule is in the
> schema: `media-buy/change-term.json` carries
> `x-adcp-validation.verifier_constraints.constraint_action_compatibility`, whose table the
> validator transcribes member for member. No JSON Schema validator reads an `x-` keyword, so
> `conforms` answers True and the model looks over-strict. **It is not.**

So the check cannot grade it in either direction: enforce it and the harness calls the model
wrong; drop it and nothing notices the constraint was lost. Upstream:
`adcontextprotocol/adcp#8472`.

`errorMessage` has no Pydantic rendering at all:

```
carries nothing for media-buy/sync-catalogs-request.json at /allOf/1: errorMessage: section 7
refuses this keyword, so it constrains no instance and the class carries nothing for it
```

**A related, smaller finding worth one sentence.** We admit the `x-` namespace by prefix, which
seems safe because a vendor extension cannot be a schema keyword. It is not safe:
`x-enum-descriptions` (1 site, `enums/signal-value-type.json`) carries **member documentation**,
and the prefix rule dropped it silently until the names were enumerated. One `x-` key in this
bundle carries content a model should render, and the prefix rule cannot tell which.

### What would make it tractable

**Partition the namespace and say which part is normative.** Three buckets:

1. **Expressible in draft-07 after all.** Several of the 179 are `if`/`then`, `dependencies` or a
   `const` written as prose. Move those into the document and a generator enforces them for free.
2. **Not expressible, but normative.** Keep them, and mark them — `x-adcp-validation` with a flag
   that says "a conforming implementation MUST enforce this". That is the statement that lets a
   generator decide: today we cannot tell a normative rule from a note, so we treat all 179 as
   notes.
3. **Documentation.** `x-enum-descriptions`, `x-tool-summary`, `x-accessibility`. A distinct
   prefix (`x-doc-…`) would let a generator render these and ignore the rest, instead of
   maintaining a list of 30 names.

---

## 9. A `pattern` asked to carry what a regex cannot — and a constraint the schema never names

**SCHEMA** (one of these is a correctness bug; the other is the cheapest ergonomic win in the
bundle)

### 9a. The pattern no conforming implementation can satisfy

`^https://[^/?#@]+$`, stated at 5 pointers beside `format: uri`. RFC 3986 §6.2.3 makes
`https://x.example/` the normalized form of `https://x.example` — so **the pattern refuses the
canonical spelling of a value it accepts**, and no conforming URL library can emit a string that
satisfies it.

This is one of only **6 positions in `codegen/dump_exemptions.py`** — the places where the
serialise-and-validate check has to strike a keyword because the model and the document cannot
agree. 5 of the 6 are this pattern. Upstream `adcontextprotocol/adcp#8398`; the minimal repair
is `^https://[^/?#@]+/?$`.

A second instance of the same class: `core/reference-renderer.json`
`/properties/provenance/properties/source_repository` states
`{"format": "uri", "pattern": "^https://github\\.com/"}` — a host allowlist written as a regex.
That is **the one position in the whole bundle from which the accepts check can draw no
instance**, which makes `core/reference-renderer.json` one of the three pairs in the tree that do
not grade at all. The bundle states 8 distinct patterns across 73 of its ~300 `format: uri`
positions, and 72 of the 73 draw; this is the one that does not.

The sixth exemption is a different shape worth naming: a node with a `minProperties` and a
silent `additionalProperties`. An undeclared key is accepted and dropped, so an instance whose
*only* key is undeclared serialises to `{}` and the node's own `minProperties` refuses it — the
document states a property count it does not let a reader satisfy.

**What would make it tractable.** Repair the one pattern (`/?$`). For host allowlists, a regex is
the wrong carrier: say it in `x-adcp-validation` with a normativity flag (theme 8) or in
`description`, and leave `pattern` for lexical facts. A `pattern` that a conforming
implementation's own output violates is a bug in any consumer, not just in a generator.

### 9b. 117 patterns, 840 sites, and not one of them has a name

The bundle states **117 distinct `pattern` values across 840 sites** in portable documents. The
top eight account for 465 of them:

| sites | pattern | what it means |
| --- | --- | --- |
| 86 | `^[A-Z]{3}$` | ISO 4217 currency code |
| 71 | `^[A-Z]{2}$` | ISO 3166-1 alpha-2 country |
| 69 | `^[A-Za-z0-9_.:-]{16,255}$` | long opaque identifier |
| 62 | `^[A-Za-z0-9_.:-]{1,255}$` | identifier |
| 55 | `^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]…)*$` | domain name |
| 47 | `^https://` | https URL |
| 41 | `^sha256:[a-f0-9]{64}$` | content digest |
| 34 | `^[A-Za-z0-9_.:-]{1,64}$` | short identifier |

Because a constraint must bind to a type rather than to a field, each distinct pattern needs a
name — and the schema supplies none, so the name is a digest of the regex. **85 of the 157
aliases in `src/adcp/types/constraints.py` are digest-named.** The rendered result:

```python
# pricing_options/cpm_option.py — one of 34 annotation uses across 29 emitted modules
currency: Annotated[StrMatching43E30B32, Field(description='ISO 4217 currency code')]

# core/account_ref.py
operator: Annotated[StrMatching32F5291C, Field(description="Domain of the entity operating on the brand's behalf.")]
```

The schema *knows* what these are — the description says "ISO 4217 currency code" — and gives a
generator nothing to name the type with.

**What would make it tractable, and this is a one-line change per pattern.** The bundle already
has 300+ documents under `enums/` that name closed *value sets*. It has no documents that name
*lexical* types. Publish the top eight as documents with a `title` — `core/currency-code.json`,
`core/country-code.json`, `core/domain-name.json`, `core/content-digest.json` — and `$ref` them.
Nothing about what the protocol accepts changes. 465 of the 840 sites become:

```python
currency: Annotated[CurrencyCode, Field(description='ISO 4217 currency code')]
```

That is the single highest ratio of consumer-visible improvement to schema-authoring effort
anywhere in this note.

---

## 10. Faithful and ergonomic, and why they pull apart

Our two rules are: **the model never accepts less than its document**, and **a consumer reaches a
named type with a bound on it**. Every theme above is a place where one keyword makes those two
rules point in different directions.

- **Faithful but not ergonomic.** `dict[str, Any]` for an object with no `properties` (theme 7);
  `StrMatching43E30B32` for a nameless regex (theme 9b); a union with no discriminator whose
  errors name every branch (theme 3). Each is correct about acceptance and useless as a type.
- **Ergonomic but not faithful**, which is the trade we refuse. Carrying `minLength` onto the
  object arm of `type: ["object","string"]` gives a clean `str` field and refuses `{}` — a
  measured defect in a previous output. Rendering `uniqueItems` as a bare `list[X]` gives a clean
  list and silently accepts duplicates. We refuse the document instead, which is why the refusal
  count is a *feature* of this pipeline rather than a backlog.
- **Neither**, where a pattern is unsatisfiable (theme 9a) or a constraint sits in a namespace
  nobody reads (theme 8). These are the ones to fix first, because nothing downstream can
  compensate.

The practical consequence for this call: **a schema change that gives a thing a name or a pointer
converts a refusal into a type, not into `Any`.** Theme 1's root-keyword fix, theme 3's `const`
or `not` clauses, theme 4's full restatement, theme 6's document-kind declaration and theme 9b's
eight named patterns each have that shape — identical accepted set, strictly better generated
code. Theme 5's `uniqueItems` is the one place where the honest answer is that no schema change
helps and the limitation is Pydantic's; theme 2 is the one place where the honest answer is that
the remaining work is ours.

---

## Reproducing every figure

```bash
PYTHONPATH=.:src uv run --no-sync python -c "
from pathlib import Path; from codegen import bundle
print('\n'.join(sorted(bundle.portable(Path('schemas/cache/3.2')))))" > /tmp/portable.txt
PYTHONPATH=.:src uv run --no-sync python -m codegen \
    --bundle schemas/cache/3.2 --tree /tmp/t $(cat /tmp/portable.txt) > /tmp/report.txt 2>&1
tail -1 /tmp/report.txt
# emitted 769 / refused 285 (deferred 109, verdict 176); accounted 945; 1054 named,
# the rest reached through a $ref
```

Per-theme counts are groupings of the 285 `refused` lines by the root of each refusal chain; the
keyword censuses are walks over the 1,054 portable documents; the rendered-Python figures are
`grep` over `/tmp/t` and `src/adcp/types/constraints.py`. The design rules each refusal cites
are in `docs/plan/rebuild-plan.md` §2 (what faithful and ergonomic mean), §4 (unions and the
three dispatch sources), §5 (per-keyword compilation), §6 (admitted and compiles to nothing) and
§7 (refused); the structural costs are in `docs/plan/architecture.md` §13; the verified defects
from a previous output are in `docs/plan/defect-inventory.md`; the strike list is
`codegen/dump_exemptions.py`.
