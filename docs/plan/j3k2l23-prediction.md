# salesagent-j3k2l.23 — a bundle annotation is not an unlowered schema keyword

Branch `sdk/j3k2l23-annotation-v2`, off `emit/from-scratch` at
`5d92cf2c058e2ee3560918e201dbeb5025e61e06`.

A previous run of this bead delivered `sdk/j3k2l23-annotation-not-keyword`
(`cecf6b6c2`) off `62b5e7ce2` and was stopped for machine load. **This branch starts
from the trunk, not from that branch**, for three reasons: `62b5e7ce2` predates the
merge `5d92cf2c0` and the `.20`/`.24`/`.16` work under it, so every figure that branch
states is a figure of a tree nobody will merge into; its emitted-module commit and its
test constants have to be re-derived on the new tree anyway; and the trunk's
`compiler.lower_object` changed under it (`object_constrained`), which is in the same
file the change touches. The codegen diff, the census and the probes of that branch are
REUSED verbatim where the new measurement agrees with them, and this file says where it
does not.

## The base, re-measured on `5d92cf2c0` by a run and not read off the tree

`emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))` over `schemas/cache/3.2`:

| figure | value | denominator |
|---|---|---|
| portable documents | 1,054 | the bundle |
| emitted | 406 | of 1,054 |
| refused | 648 | of 1,054 |
| committed emitted modules | 395 | `src/adcp/types/_schemas/**/*.py`, tracked |
| graded pairs | 481 | `test_emit.py:1406` |
| pass / no_constraint_to_step | 469 / 12 | of 481 |
| added / missing / differs | 0 / 0 / 0 | over 481 |

**None of the bead's own figures still hold.** The bead states 390 modules, 462 pairs
(450 pass, 12 no_constraint) and 401 emitted + 653 refused; the prior branch's base
measured 401/653 and 390 modules. The trunk now measures 406/648, 395 modules and 481
pairs. Every number below is stated against the `5d92cf2c0` run.

## Why this bead matters more than four documents — verified, and the verification
## refutes half the claim

Of the bundle's **179** `-request`/`-response` documents, **12 emit and 167 refuse**.
Following each refused one's `$ref` cascade down to the leaf document and the keyword
that actually stopped it:

| leaf document | keyword | gates |
|---|---|---|
| `core/protocol-envelope.json` | `notes` at `/` | **35** of 167 |
| `core/brand-ref.json` | `uniqueItems` at `/properties/countries` | 30 of 167 |
| `media-buy/media-buy-commitment-response.json` | `not` at `/oneOf/0` | 3 of 167 |
| `content-standards/artifact.json` | `discriminator` | 2 of 167 |
| 97 others | — | 1 each |

So the leverage claim's FIRST half is confirmed on `5d92cf2c0`: `notes` on
`core/protocol-envelope.json` is the reported leaf gate of 35 of the 167, more than any
document except `brand-ref`, and `notes` appears in exactly 2 documents bundle-wide.

**The second half does not follow, and I predict the measurement will show it.**
`core/protocol-envelope.json` has a SECOND blocker underneath its `notes`: it
references `core/error.json`, which refuses on its own tree at
`/properties/issues/items/properties/discriminator/items/properties/value` for a
`['boolean','null','number','string']` type list. `notes` sorts before `$ref` in the
keyword screen, so `notes` is the keyword the refusal REPORTS while the `$ref` is the
keyword that BINDS. Admitting `notes` therefore does not emit protocol-envelope and
does not emit any of the 35 — it moves their reported gate from a name no row can ever
lower to a keyword a scheduled step owns, which is the bead's actual exit condition and
not a document count.

That is worth saying plainly: **the cheapest 35 request/response documents on the board
are not cheap, and this change does not buy them.** What it buys is that their refusal
stops lying about what is scheduled.

## The population, enumerated with its denominator

Over all **1,054** portable documents, every key at a schema position (`bundle.nodes`)
that draft-07 does not define and that is not `x-*`. All 1,054 declare
`http://json-schema.org/draft-07/schema#`, so one draft decides the vocabulary.
**27 distinct names at 436 sites** — identical to the prior branch's census, so the
landed `.20`/`.24`/`.16` work moved no bundle fact:

| name | sites | documents | at a root |
|---|---|---|---|
| `deprecated` | 179 | 95 | 16 |
| `enumDescriptions` | 137 | 135 | 131 |
| `discriminator` | 81 | 73 | 51 |
| `$defs` | 5 | 5 | 5 |
| `enumMetadata` | 4 | 4 | 4 |
| `version` | 4 | 4 | 4 |
| `lastUpdated` | 3 | 3 | 3 |
| `errorMessage` | 2 | 1 | 0 |
| `notes` | 2 | 2 | 2 |
| `vocabulary` | 2 | 2 | 2 |
| `_generated`, `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning` | 1 each | 1 each | 1 each |
| `writeOnly` | 1 | 1 | 0 |

The bead's "4 refusals at a root — `notes` 2, `enumMetadata` 1, `last_updated` 1" is
CONFIRMED on `5d92cf2c0`, and it is 4 of **11** refusals on a non-keyword: the other
7 are `discriminator`.

- `core/protocol-envelope.json` — `notes` at `/`
- `enums/task-type.json` — `notes` at `/`
- `core/media-buy-available-action-id.json` — `enumMetadata` at `/`
- `registries/v1-canonical-mapping.json` — `last_updated` at `/`

## Which names are admitted, and why the other 25 are not

Admitted, **two names**, by name and never by a prefix: `notes`, `enumMetadata`.

- `notes` holds a list of English sentences in both of its documents. It annotates the
  document for a reader and states nothing about an instance.
- `enumMetadata` is ALREADY admitted by `lower.enum.HANDLED`, on exactly this
  reasoning, which `codegen/lower/enum.py` writes down: it states nothing about an
  instance, the `enum` having already closed the value set. That is the precedent the
  bead points at. Its fourth document is a UNION root, which the enum row's set does not
  reach, so admitting it once globally is the same decision in one place instead of two.

Not admitted:

- `deprecated`, `writeOnly`, `$defs` are not new decisions: `compiler._DRAFT_ANNOTATIONS`
  and `compiler.DEFINITION_SECTIONS` already name them. They are in the census because
  the census is "not a draft-07 name", not "refused".
- `enumDescriptions` (137 sites) is **carried**, not ignored — the enum row reads it
  into the member docstrings. Admitting it here would delete a fact the SDK emits.
- `discriminator` (81 sites, 7 refusals) **could constrain an instance**: in OpenAPI it
  selects which branch a payload resolves to, a job §4 gives to
  `DataType.discriminator`. A class emitted while ignoring it would be quietly wider
  than its author meant. It keeps refusing, and that is the half of this change that
  matters.
- `errorMessage` (2 sites, 1 document) constrains nothing, but its document refuses on
  `if` first, so admitting it would change no outcome. Nothing is admitted on no
  evidence.
- The other **19** — `version`, `lastUpdated`, `last_updated`, `mappings`,
  `vocabulary`, `governance`, `extensions`, `_generated`, `_generatedAt`,
  `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `prerelease`,
  `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning` —
  **are not annotations.** They are a document's own INSTANCE DATA at a schema root:
  five registry, vocabulary and index documents carry their payload beside their
  schema. `registries/v1-canonical-mapping.json` says so itself — it declares
  `last_updated`, `mappings` and `version` as its own `properties`. Admitting them
  would call a registry's 300-line `mappings` payload an annotation, which is the
  blanket allowance in another shape, and the set would then grow by a data field name
  per registry. That document stays refused, by decision.

## What changes

1. `codegen/compiler.py` — `ANNOTATIONS` splits by PROVENANCE and the halves are
   unioned, so every existing reader keeps one name: `_DRAFT_ANNOTATIONS` (unchanged)
   and `BUNDLE_ANNOTATIONS` (`notes`, `enumMetadata`), with the census as its reason.
2. `codegen/compiler.py` — `check_keywords`'s default reason splits on whether the key
   is a name draft-07 defines, read off `jsonschema.Draft7Validator.META_SCHEMA` rather
   than typed. Today every unknown key says "this step lowers no such keyword (a later
   D2 row does)", which promises an unscheduled row for a name no row can ever lower.
3. `codegen/lower/enum.py` — `enumMetadata` leaves `HANDLED`: two places admitting one
   name is two places for one decision to drift.
4. `tests/test_emit.py` — the census with its denominators, the partition, the four
   documents individually, and both halves of the fire probe.
5. The metric constants and the committed tree, each in its own commit.

**No ROW is added.** `notes` and `enumMetadata` sit at 6 roots and not one of them is a
root KIND, so there is nothing for a selector to select. The note on the bead refuting
"this is one dispatch row" applies here: the unit is a change to `check_keywords` and
to one frozenset, in the WALK.

## Predictions

| # | prediction |
|---|---|
| P1 | `enums/task-type.json` EMITS — it is the one of the four held by nothing but its `notes` |
| P2 | `core/protocol-envelope.json` does **not** emit: it refuses on `$ref` at `/properties/adcp_error` naming `core/error.json`, so **0 of the 35 request/response documents it gates become emittable** |
| P3 | `core/media-buy-available-action-id.json` does **not** emit: `enumMetadata` admitted, and the union row then refuses its bare `$ref` branch at `/anyOf/0` |
| P4 | `registries/v1-canonical-mapping.json` stays refused on `last_updated` at `/`, with the new reason and not the old promise |
| P5 | The 7 `discriminator` refusals keep their keyword and pointer and take the new reason |
| P6 | Net emitted **407** of 1,054, interval 406–410; net refused **647**, interval 644–648 |
| P7 | `added` stays **0** over every graded pair, and `missing`/`differs` stay **0** |
| P8 | Graded pairs rise from 481 to **482**, interval 481–484; pass from 469 to **470** |
| P9 | Committed emitted modules rise from 395 to **396** — `enums/task_type.py` and its `.json`, nothing else |
| P10 | After the change, **0** refusals promise a row for a non-keyword, and **8** refusals ARE on one (`discriminator` 7, `last_updated` 1), so the honest branch is reached rather than dead |
| P11 | A PLANTED document carrying an admitted annotation, at a root and at a nested node, EMITS |
| P12 | A PLANTED unknown keyword that could constrain an instance — five of a later draft, the OpenAPI `discriminator`, and a name nobody defines — still REFUSES by name, pointer and keyword, at a root and at a nested node |
| P13 | The census is unchanged by the change: 27 names at 436 sites either way, because it is a fact about the bundle and not about the emitter |
| P14 | No existing test expectation needs editing except the metric constants (emitted/refused/pairs/modules) and the committed tree. **Named risk**: a test asserting the OLD reason text for a `notes`/`enumMetadata`/`discriminator` refusal, or `test_enum.py` asserting `enumMetadata in lower_enum.HANDLED` |

## Grading

Measured on `0964a8157`, bundle `schemas/cache/3.2`, and compared against the
`5d92cf2c0` run above. **13 of 14 right, and the one that was wrong was wrong about
the suite rather than about the emitter.**

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | `enums/task-type.json` emits | emits; `class TaskType(StrEnum)`, 38 members | RIGHT |
| P2 | protocol-envelope does not emit; refuses `$ref` at `/properties/adcp_error` naming `core/error.json`; 0 of the 35 | exactly that; request/response emitted stays **12 of 179** | RIGHT |
| P3 | `core/media-buy-available-action-id.json` refuses `$ref` at `/anyOf/0`, bare-`$ref` branch | exactly that | RIGHT |
| P4 | registry stays refused on `last_updated` at `/` with the new reason | exactly that | RIGHT |
| P5 | the 7 `discriminator` refusals keep keyword and pointer, take the new reason | 7, new reason | RIGHT |
| P6 | emitted **407** (406–410), refused **647** (644–648) | **407 / 647** of 1,054 | RIGHT, point estimate exact |
| P7 | added / missing / differs stay 0 | 0 / 0 / 0 over 482 pairs | RIGHT |
| P8 | pairs **482** (481–484), pass **470** | **482 / 470** | RIGHT, point estimate exact |
| P9 | modules 395 → **396**, only `enums/task_type.py` and its `.json` | 396; those two files and no other byte of the tree moved | RIGHT |
| P10 | 0 refusals promise a row for a non-keyword; **8** are on one | 0 and 8 (`discriminator` 7, `last_updated` 1), against 639 on a draft-07 name | RIGHT |
| P11 | a planted admitted annotation emits, at a root and nested | emits | RIGHT |
| P12 | a planted unknown constraining keyword still refuses, 7 cases, root and nested | refuses by name, pointer and keyword | RIGHT |
| P13 | census unchanged by the change: 27 names at 436 sites | 27 / 436 either side | RIGHT |
| P14 | no existing expectation needs editing except the metric constants and the tree | **WRONG** — 8 assertions in 4 modules | WRONG |

### P14, and what it got wrong

The named risk fired (`test_enum` asserted `enumMetadata in lower_enum.HANDLED`), but
naming a risk is not predicting it, and the SHAPE was wrong as well. Emitting ONE
document moved eight assertions in four modules, because this suite counts the emitted
tree from four directions:

- `tests/test_emit.py` — pairs 481→482, pass 469→470, compared 4,859→4,862, and the
  union row's keyword profile (`$ref` 16→17, the `enumMetadata` row gone);
- `tests/test_enum.py` — root enums 213→214 with the refusal branch emptied, the
  `enumMetadata` decision's location, enum classes 270→271, injective enum nodes
  270→271, member names 1,954→1,992, `enumDescriptions` (132, 1097, 10)→(133, 1135, 10);
- `tests/test_applied_schema.py` — 406→407 emitted of 1,054;
- `tests/test_emit_product.py` — N over its 587-document population 218→219.

Each one is the same document counted again. "The metric constants" named one of the
four places; the cost of emitting a document in this suite is a count in every module
that has a denominator, and that is the figure to predict next time.

### What the measurement says about the leverage, which the bead does not

The 35 request/response documents that reported `notes` on `core/protocol-envelope.json`
now report **`core/error.json`, `type` at
`/properties/issues/items/properties/discriminator/items/properties/value`** — a
`['boolean','null','number','string']` type list beside a declared `null`. That is a
keyword a SCHEDULED step owns, which is the bead's exit condition met. It also makes
that one node the single highest-leverage item left on the request/response surface:
**35 of the 167 refused documents, 21%, behind one `type` list in one document.**
`core/brand-ref.json`'s `uniqueItems` at `/properties/countries` is second at 30.
