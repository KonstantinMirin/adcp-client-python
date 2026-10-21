# Stage-C defect inventory

Derived from `salesagent-nk17x.6`'s measurements and **re-verified from first principles**.
Re-derivable, not asserted: `docs/analysis/derive_defect_inventory.py` produces every count
and every verdict below, and `docs/analysis/defect-inventory.jsonl` is its 210-row output.

```bash
git archive 281e0b4c2 src/adcp/types | tar -x      # the pre-cut emitted tree; leave UNTRACKED
env -u VIRTUAL_ENV uv sync --all-extras
env -u VIRTUAL_ENV uv run --no-sync python docs/analysis/derive_defect_inventory.py \
    --out docs/analysis/defect-inventory.jsonl
```

The model/bundle pairing transfers because `schemas/cache/3.2` is tree
`47768de9f54f7ef87a514ccaf8390dfd9662e0d0` at both `281e0b4c2` and this branch
(`git ls-tree`, verified).

## The headline, and it changes what stage C should build

**Of the 93 direction-1 rows, 10 are model defects. The other 83 are not.**

`.6` graded each document against the class the binding table pairs with it. 85 of the 93
direction-1 rows were graded on an `mcp/` or `bundled/` **projection**, and a projection is
strictly looser than the portable document the class was generated from: it drops the root
`allOf`, drops `required`, and redeclares the version-envelope fields without their
`minimum`/`maximum`. So the harness generated a payload the projection admits, the model
refused it — correctly, per the portable contract — and the row was recorded as a refusal of
a valid document.

Re-graded against the portable document (`projection_of`), **83 of the 93 payloads are
REFUSED by the schema itself**, on the very keyword the projection stripped. For those rows
the model and the portable document agree, and the row is not evidence of anything.

This contradicts one of the two facts handed to this analysis — "the 568 `mcp/` and
`bundled/` projections contribute zero unique findings". That holds for **direction 2**
(12 of 12 triples reproduce on the portable path) and fails for direction 1, where 37 of the
45 symbols are reached *only* through a projection.

| pass | what it grades against | direction 1 | direction 2 |
|---|---|---|---|
| A | the document each case was graded on | 90/93 rows | 12/12 triples |
| B — **authoritative** | the portable document | **10/93 rows, 8/45 symbols** | **12/12 triples** |

---

## Direction 1 — the model refuses a document its schema admits

### Row census, before verification (93 rows / 45 symbols)

Grouped by pydantic's error `type`, read off the row: `check_accepts` records
`f"{err['type']} at {err['loc']}: {err['msg']}"`, so the leading token is the mechanism as
pydantic named it — not a guess from the message text.

| pydantic error type | rows | symbols | graded on a projection |
|---|---|---|---|
| `allOf` | 28/93 | 11/45 | 28/28 |
| `anyOf` | 18/93 | 7/45 | 17/18 |
| `string_too_short` | 16/93 | 13/45 | 16/16 |
| `greater_than_equal` | 14/93 | 9/45 | 14/14 |
| `type` | 5/93 | 3/45 | 2/5 |
| `extra_forbidden` | 5/93 | 4/45 | 3/5 |
| `too_short` | 2/93 | 2/45 | 1/2 |
| `literal_error` | 2/93 | 1/45 | 2/2 |
| `format` | 2/93 | 1/45 | 2/2 |
| `value_error` | 1/93 | 1/45 | 0/1 |

The family the brief expected to dominate — `allOf at (): X violates a constraint its schema
states outside its properties (<doc>, root conjunct N)` — is 28/93 rows over 11/45 symbols,
and **every one of its 28 rows was graded on a projection**. Zero of them survive pass B.

### The 10 verified model defects (8 symbols)

Each was reproduced against the portable document: the schema accepts the payload, the model
refuses it. Every one was re-checked with `format` assertion enabled, because `conforms`
leaves `format` as a draft-07 annotation and a case resting only on it would be a vacuous
pass. All 10 accept with the checker on.

| # | mechanism, verified against the schema | rows | symbols | ticket |
|---|---|---|---|---|
| D1-a | **A property declared with only a `description` — no `type` — admits any JSON value, null included. `AbsentOr` refuses an explicit null.** `core/response.json` `data`, `governance/check-governance-response.json` `conditions[].required_value`, and `extensions/extension-meta.json` `additionalProperties` are each `{"description": ...}` and nothing else. | 5/93 | 3/45 — `ProtocolResponse`, `CheckGovernanceResponse` (×3 rows), `AdcpExtensionFileSchema` | **`.12`** |
| D1-b | **A named class is deduped onto a same-shaped inline object and brings its stricter `additionalProperties` with it.** `core/property.json` declares `identifiers.items` inline with `additionalProperties: true`; `core/identifier.json` is a separate document with `additionalProperties: false`, emitted as `Identifier` with `extra='forbid'`. `Property.identifiers` is typed `list[Identifier]`, so the inline schema's own `additionalProperties: true` is discarded. | 2/93 | 2/45 — `Property`, `PropertyError` (which nests it) | **`.10`** |
| D1-c | **A string-only keyword is applied to a union's non-string arm.** `core/attestation-reference.json` declares `embedded_credential.value` as `{"type": ["object","string"], "minLength": 1}`. In JSON Schema `minLength` constrains strings only; the emitter carried it onto the object arm, so `{}` is refused with `Value should have at least 1 item`. | 1/93 | 1/45 — `AttestationReference` | **`.10`** |
| D1-d | **A union branch is constrained beyond what it requires and forbids.** `AudienceCharacteristicValue` refuses `{"dimension": "age", "value": [0.0]}`, which `core/audience-characteristic.json` admits through `anyOf/0`. | 1/93 | 1/45 — `AudienceCharacteristicBranches` | **`.11`** |
| D1-e | **Not a defect — see below.** | 1/93 | 1/45 — `MediaBuyChangeTerm` | none |

### The three cases that do not reproduce, and they are the most useful rows here

**1. `MediaBuyChangeTerm` (1 row) — the model is right and the harness cannot see why.**
`change_term.py:78` raises `constraint kind is incompatible with action`. That rule is in the
schema: `media-buy/change-term.json` carries
`x-adcp-validation.verifier_constraints.constraint_action_compatibility`, whose table the
validator transcribes member for member. No JSON Schema validator reads an `x-` keyword, so
`conforms` answers True and the model looks over-strict. It is not. **Do not "fix" this, and
do not size a ticket on it.** This is the same population as the 216 `x-` sibling keywords
already ruled out as introducing no gradeable constraint — except that here the model reads
one, which is why it surfaced in this direction.

**2. `SiTerminateSessionResponse` (2 rows) and `ListCreativeFormatsRequest` (1 row) — harness
false positives from a draft mismatch.** These 3 rows do not reproduce even against the
document they were graded on: the document refuses the payload on `dependentRequired`
(`{"buyer_reason": ["recovery"]}` and `{"width": ["height"], "height": ["width"], ...}`).
399 of the `mcp/` projections declare `$schema: draft/2020-12`, so `jsonschema` picks
`Draft202012Validator` and enforces `dependentRequired`; `hypothesis_jsonschema` generates in
draft-07 terms and ignores it. Direction 1 never validates what it generated, so it could not
tell. The model refused correctly in all three.

Net: **9 candidate model defects over 7 symbols**, after removing D1-e.

### What the other 83 rows are

The portable document refuses each payload, on these keywords:

| rows | pydantic error type | the keyword the portable document bites on |
|---|---|---|
| 17 | `allOf` | `required` |
| 16 | `anyOf` | `anyOf`, `required` |
| 14 | `greater_than_equal` | `minimum` |
| 8 | `string_too_short` | `minLength`, `pattern` |
| 6 | `allOf` | `dependencies` |
| 3 | `allOf` | `not` |
| 3 | `string_too_short` | `minItems`, `minLength`, `pattern` |
| 2 | `extra_forbidden` | `additionalProperties`, `oneOf`, `required` |
| 2 | `literal_error` | `const`, `oneOf`, `required` |
| 2 | `allOf` | `anyOf`, `required` |
| 2 | `format` | `minItems` |
| 2 | `string_too_short` | `additionalProperties`, `anyOf`, `minLength`, `pattern`, `required` |
| 1 | `anyOf` | `anyOf`, `minLength`, `pattern`, `required` |
| 1 | `string_too_short` | `additionalProperties`, `anyOf`, `minItems`, `minLength`, `pattern`, `required` |
| 1 | `string_too_short` | `additionalProperties`, `anyOf`, `minLength`, `required` |
| 1 | `string_too_short` | `minLength`, `minProperties`, `pattern` |
| 1 | `extra_forbidden` | `additionalProperties` |
| 1 | `too_short` | `minItems`, `minLength`, `pattern` |

(17+16+14+8+6+3+3+2+2+2+2+2 + six rows of 1 = 83.)

Worked example. `account/list-accounts-request.json` composes `core/version-envelope.json`,
whose `adcp_major_version` is `{"type": "integer", "minimum": 1, "maximum": 99}`. The
projection `mcp/2026-07-28/profiles/creative/model-context/account/list-accounts-request.json`
redeclares it as `{"type": "integer"}` — both bounds gone — and also drops the portable root
`allOf` and `required`. The harness generated `adcp_major_version: 0`; `ListAccountsRequest`
inherits `AdcpVersionEnvelope` and refuses it with `ge=1`. The model is faithful to the
portable schema. That accounts for all 14 `greater_than_equal` rows over 9 symbols.

**A pass in pass B is not proof the model is correct in general** — only that these rows are
not evidence. 71 of the 85 projection rows have a portable parent that passed direction 1 on
25 examples, and 12 have a parent that hit the 90 s budget and was never graded.

---

## Direction 2 — the model accepts a document its schema refuses

23 raw rows, **12 distinct `(symbol, keyword, pointer)` triples**. The raw count is inflated by
projections reaching triples a portable path also reaches; deduping is what the 12 is.
**All 12 reproduce, against both the graded document and the portable one** — the schema names
the violated keyword and the model accepts the payload anyway.

| keyword | triples | rows | mechanism, verified in the emitted source | ticket |
|---|---|---|---|---|
| `enum` | 5/12 | 16/23 | **A `$ref` to a standalone enum document emits bare `str`.** The enum class is emitted and never used: `core/canonical-format-kind.json` (16 members) has **18 `$ref` sites across 18 portable documents and 0 fields annotated with `CanonicalFormatKind`**. `CanonicalProjectionReference.kind` is `str`; `ListTransformersRequestCreativeAgent.input_format_kinds` is `list[str]`. Across the bundle, 212 of 214 portable standalone enum documents do bind to an `Enum` subclass — so the class exists and the reference site discards it. | **none** |
| `minimum` | 4/12 | 4/23 | **A subclass redeclares an inherited field as `Optional[Any]`, discarding the item type and every constraint on it.** The pointer says `minimum`, but `Slot.min` carries `Field(ge=0)` and refuses `-1` correctly in isolation; `CanonicalFormatResponsiveCreative.slots` is annotated `Optional[Any]`, overriding `CanonicalFormatBase.slots: Optional[list[Slot]]`. Census: 42 of 7,235 fields over 701 root classes are `Any`, **31 of them shadow a typed base field**, over 15 classes, on `composition_model`, `experimental`, `since_version`, `slots`, `v1_translatable`. | **none** |
| `maximum` | 1/12 | 1/23 | **A constraint inside an `if`/`then` is not enforced.** `core/canvas-constraint.json` `region.allOf[0]` is `if unit == "percent" then x.maximum = 100`; `CanvasConstraint` accepts `x: 101.0` with `unit: "percent"`. | **none** |
| `minItems` | 1/12 | 1/23 | **A keyword on an `additionalProperties` value schema is dropped.** `core/geo-place-support.json` `countries.additionalProperties` carries `minItems: 1`; `GeographicPlaceSystemSupport` accepts `{"AA": []}`. | **`.13`** |
| `required` | 1/12 | 1/23 | **A required `$`-prefixed property is absent from the model entirely.** `extensions/extension-meta.json` requires `['$schema','$id','title','description','valid_from','type','properties']`. `AdcpExtensionFileSchema` declares `field_schema` with `alias='$schema'` and has **no `$id` field at all**, so a document missing `$id` validates. | **none** |

### `.14` (`uniqueItems`) is not graded by this measurement, in either direction

**0 of 5,545 site rows carry `kw: "uniqueItems"`.** `harness.steps()` emits a step for exactly
nine keywords — `additionalProperties`, `enum`, `maxItems`, `maxLength`, `maximum`,
`minItems`, `minLength`, `minimum`, `required` — and `uniqueItems` is not one of them; two of
the nine rewrites actively `pop` it to keep the stepped schema satisfiable. So this inventory
neither supports nor refutes `.14`'s own figure of 9,693 occurrences against 4 hand-written
`len(set(...))` validators. **`.14` needs its own instrument.**

### Which direction-2 keywords have no ticket

`.13` covers 1 triple. `.14` covers 0. **11 of the 12 triples (22 of the 23 rows) have no
ticket of their own**, and `enum` is the largest class: 5 triples, 16 rows, and the fix is a
reference-site resolution change, not a new constraint mapping.

---

## Ticket coverage, measured

| ticket | direction-1 rows (verified) | direction-2 triples | note |
|---|---|---|---|
| `.10` — emit through the dmcg model layer, no patch pass | 3/93 (3 symbols) | 0/12 | D1-b, D1-c. The 28 `allOf` root-conjunct rows it was expected to own do **not** survive verification. |
| `.11` — base plus one class per branch | 1/93 (1 symbol) | 0/12 | D1-d. The 18 `anyOf` + 2 `literal_error` rows do not survive. |
| `.12` — accept an explicit null, remove the `AbsentOr` hooks | 5/93 (3 symbols) | 0/12 | D1-a. The largest verified direction-1 family, and the cause is precise: a `description`-only property declaration. |
| `.13` — array constraints on a typed `additionalProperties` | 0/93 | 1/12 | Reproduced on `core/geo-place-support.json`. |
| `.14` — enforce `uniqueItems` | 0/93 | 0/12 | **Ungraded by this probe**, not passing. |
| **no ticket** | 1/93 (D1-e, and it is not a defect) | **11/12** | `enum` (5), `minimum`-as-`Any`-shadowing (4), `maximum` in `if`/`then` (1), `required` `$`-prefixed (1). |

## Caveats a brief should carry

- **Pass B is the authority; pass A is not.** A direction-1 row graded on a projection says
  nothing about the model until it is re-graded on `projection_of`.
- **`conforms` does not assert `format`.** Every verified case was re-checked with the checker
  on; a future case resting only on `format` is a vacuous pass.
- **The projections are not one draft.** 399 `mcp/` documents declare draft/2020-12, 53 declare
  nothing, 116 `bundled/` and 1,056 portable declare draft-07. `hypothesis_jsonschema`
  generates in draft-07 terms, so any 2020-12-only keyword in a projection is a false-positive
  generator for direction 1 — measured: 3 rows, on `dependentRequired`.
- **Every payload verified here parsed.** The recorded `counterexample` is capped at 600
  characters; no case in this inventory was lost to truncation, and the script reports
  `UNVERIFIABLE` rather than skipping if one ever is.
- **A direction-1 `pass` is 25 examples, not a proof.** 12 of the portable parents were never
  graded at all (90 s budget).
