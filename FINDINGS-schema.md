# Findings — advertise the DOCUMENT's schema, not pydantic's rendering of our class

R12's four failures close. The advertised MCP `outputSchema` is derived from the document of
record now, so a root-union response publishes its branches again and `create_media_buy` can
tell a client success from error from pending.

**The defect was not in `model_json_schema()`, and it was not one path doing something odd —
it was TWO paths, one of which was already right.** `get_tools_for_handler` has always had a
version-pinned branch that advertises the bundled wire document and an unpinned branch that
advertised `model_json_schema()`. R12 is the unpinned branch, and the fix is to delete the
divergence: both now go through one renderer, `_document_discovery_schema`.

---

## 1. THE PREMISE, VERIFIED BEFORE ANYTHING WAS BUILT ON IT

TASK.md named (c) as the one that might fail and said to stop and report if it did. **It
holds, and no packaging decision is needed.** All three, measured:

| | claim | verdict |
| --- | --- | --- |
| (a) | `mcp_tools.py` publishes `model_json_schema()` and nothing fixes it up downstream | **confirmed** |
| (b) | the classes carry a usable `__adcp_schema__` | **confirmed** |
| (c) | the document of record is reachable from the shipping `src/adcp/` | **confirmed, twice over** |

**(c) in detail, because it was the one in doubt.** There are TWO independent document trees
inside the shipping package, each with its own runtime loader and its own `package-data` line:

| tree | loader | `package-data` | populated by |
| --- | --- | --- | --- |
| `adcp/types/_schemas/**/*.json` — one inlined document beside every emitted module | `adcp.types._base._document` | `types/_schemas/**/*.json` | `codegen/emit.py`, committed |
| `adcp/_schemas/{bundle}/**/*.json` — the per-tool wire bundle | `adcp.validation.schema_loader` | `_schemas/3.2/**/*.json` | `scripts/bundle_schemas.py` at build |

`schema_loader` resolves the **installed** copy first (`files("adcp") / "_schemas" / key`) and
falls back to the dev checkout's `schemas/cache/{key}/`, which is why a repo tree answers from
`schemas/cache/3.2` and a wheel answers from inside itself. `codegen/` is never consulted at
runtime. Nothing has to start shipping for this to work; it already ships.

**(b), and the one disagreement worth recording.** Of the 78 response types the publisher maps,
75 carry an `__adcp_schema__` naming exactly the document the loader serves for that tool at
pointer `#`. The exceptions:

* `list_creative_formats` — the class says `media-buy/list-creative-formats-response.json`, the
  loader says `creative/list-creative-formats-response.json`. Both files exist in the record
  tree (553,297 and 552,441 bytes). This is the legacy projection tool; the publisher is keyed
  by tool name, so it takes the loader's.
* `buy_products` and `accept_proposal` — `Annotated` union aliases, not classes, so there is no
  class-level `__adcp_schema__` to read at all. **Both are tools that advertised 160 and 174
  bytes before this change** — the degenerate shape R12 is about.

Those last two are why the publisher addresses the document **by tool name and direction**
rather than through `__adcp_schema__`: the loader answers for all 78, the class attribute for
76. Where both answer, they agree.

---

## 2. WHAT THE UNPINNED PATH USED TO PUBLISH, AND WHAT IT PUBLISHES NOW

`create_media_buy`'s `outputSchema`, before:

```
{'additionalProperties': True, 'description': 'Response payload for create_media_buy. Exactly
 one of three shapes: …', 'required': ['status'], …}        # one plain object, no branches
```

After — the document's root `oneOf`, which `_simplify_wire_schema` renders as `anyOf` (its own
long-standing decision, "also what Pydantic emits for the same unions on the unpinned path"):

```
anyOf: 3 branches — CreateMediaBuySuccess / CreateMediaBuyError / CreateMediaBuySubmitted
```

All four shapes a buyer can receive validate against it, checked with `jsonschema`:

| payload | verdict |
| --- | --- |
| 3.2 success (`status: completed`, `media_buy_id`, `packages`, `confirmed_at`, `revision`) | accepted |
| terminal error (`errors[]`) | accepted |
| submitted envelope (`status: submitted`, `task_id`) | accepted |
| negotiated 3.0 success (`status: pending_creatives`) | accepted — see §3 |

**And it is SMALLER than what it replaced.** Compacted, over all 78 response documents:
pydantic 2,030,399 bytes → document 1,497,429 (0.74x). The whole 78-tool unpinned surface
lists 2,846,895 bytes, 0.68x of the 4 MiB buyer budget.

---

## 3. THE LEGACY STATUS WIDENING HAD TO LEARN THE CONJUNCTION

`_widen_media_buy_output_schema_for_legacy_statuses` looks for a branch whose `required` holds
`media_buy_id` and whose `properties.status` is `{"const": "completed"}`. **On the document
shape it finds neither, and silently no-ops** — the exact failure its own comment warns of,
with the exact consequence: the advertisement rejects a legitimate negotiated-3.0
`status: "pending_creatives"`.

The reason is `CLAUDE.md`'s standing rule. Pydantic rendered a `status` on each branch. The
document states it **once**, in `core/protocol-envelope.json`, reached through the response
root's `allOf`, governing every branch. A widening that reads one branch in isolation is
reading half a conjunction.

So `_widen_media_buy_document_status_for_legacy_statuses` widens the envelope's `status`, and
**both value sets are the document's own**:

| | definition | enum |
| --- | --- | --- |
| what `status` already refs | `enums/task-status.json` | `submitted`, `working`, `input-required`, `completed`, `canceled`, `failed`, `rejected`, `auth-required`, `unknown` |
| what a 3.0 buyer sends | `enums/media-buy-status.json` | `active`, `canceled`, `completed`, `paused`, `pending_creatives`, `pending_start`, `rejected` |

The second is stated by the same document at `/anyOf/0/properties/media_buy_status` — 3.0
carried the lifecycle value in `status` because it had no `media_buy_status` field. It is also
**exactly** the set the repointed tests assert, and exactly
`MEDIA_BUY_LEGACY_STATUS_VALUES ∪ {completed}`: the hand-maintained constant was the 3.0
document's enum all along.

`status` **stays in `required`.** The document requires it and a negotiated 3.0 response sends
it; the old rendering dropped it from `required` only to make room for a per-branch widening,
and widening accepted VALUES needs no such room.

Scoped in place, not cloned: measured on bundle 3.2, `create_media_buy` and `update_media_buy`
each reference the envelope, the task-status enum and the media-buy-status enum **exactly
once**, so there is one site to widen and nothing is stranded.

---

## 4. `_inline_refs` ONLY EVER UNDERSTOOD ONE POINTER FORM

Pydantic emits `#/$defs/ClassName` and nothing else, so the inliner handled nothing else. The
documents use four forms, all measured on bundle 3.2 response documents:

| form | example |
| --- | --- |
| a whole definition, name escaped | `#/$defs/external:core~1product.json` |
| continuing into a definition | `…reporting-schedule.json/definitions/ReportingScheduleAlignment` |
| indexing a list | `…delivery-metric-aggregate.json/oneOf/0` |
| rooted at the document, not at `$defs` | `#/definitions/targeting_kvs`, `#/oneOf/0/properties/fonts/$defs/font_role` |

`_pointer_body` resolves all four (RFC 6901 §3 unescaping, list indices, and resolution against
the whole schema rather than just its `$defs`). Inlining also used to copy definition TABLES
into the output it had just resolved them out of; those are dropped from the body now, since
every local pointer is rooted and nothing in the body can reference them.

Before: 16 references survived in `create_media_buy`'s inline rendering and 24 of 78 output
schemas kept a `$ref` or a `$defs` — in the one mode that exists for clients which resolve no
references at all. After: **0 of 78.**

---

## 5. THE PRODUCTION-PROFILE ARTIFACT IS LOSSY, AND NOT IN THIS LANE TO FIX

**This is the one finding that is a defect somewhere else, and it is reported rather than
repaired.** `get_mcp_schema` prefers the bundle's `mcp/…/profiles/production/` artifact — the
pre-deduplicated copy that exists to keep discovery small. It has been pruned, and one pruning
changes validation:

```
schemas/cache/3.2/core/canonical-product.json                        39 properties, description present
  …/mcp/2026-07-28/profiles/production/media-buy/list-products-response.json
                       its inlined canonical-product                 38 properties, description GONE
```

`additionalProperties: false` is kept either way. So **a product with a `description` — which
the reference seller actually returns — is a real response the advertised schema rejects.** The
shape of the mistake is familiar: `description` was dropped as though it were the annotation
keyword of that name rather than a property called that. `tests/test_discovery_payload_size.py
::test_advertised_output_schemas_still_describe_real_responses[list_products-params1]` is the
test that catches it, and it catches it only because it grades against real handler output.

The split that follows, and it is a **size decision with a known correctness cost**:

| path | reads | why |
| --- | --- | --- |
| unpinned | the source document | it is graded against real handler output and fails on the profile |
| pinned | the production profile | 0.56x the source compacted (842 KB against 1,497 KB over 78 documents); the pinned 78-tool listing is 0.84x of the half-budget headroom `test_discovery_payload_size` guards, and 1.27x of it on the source |

Both publish the document; they differ in which published rendering of it. Moving the pinned
path onto the source document would fix its latent copy of this bug and break its byte headroom
in the same commit, which is the owner's trade to make and not mine. **The repair belongs in
the artifact generator**, which is outside `src/adcp/`.

---

## 6. THE `const`-PINNED REQUIRED PROPERTY — THE RESULT THAT UNBLOCKS THE PINNED BRANCH

**On the advertised `outputSchema`: YES, it is in `required`.** Measured on the document-derived
advertisement:

```
get_products    core/assets/image-asset.json      const=image     default=<none>   in required: True
get_products    core/assets/video-asset.json      const=video     default=<none>   in required: True
sync_creatives  core/assets/audio-asset.json      const=audio     default=<none>   in required: True
sync_creatives  core/assets/vast-asset.json       const=vast      default=<none>   in required: True
```

The document lists the property in `required` and states **no `default` at all** — the default
is our compilation's, and the advertisement no longer reads our compilation. The pydantic rule
that caused the objection is real and reproduces exactly as TASK.md measured it:

```
class WithoutDefault:  asset_type: Literal['image']            → required=['asset_type','url']
class WithDefault:     asset_type: Literal['image'] = 'image'  → required=['url']
                                                                  asset_type={'const':'image','default':'image'}
```

**That rule can no longer reach the advertised output schema.** Adopting the pinned default on
the class — `verdicts/a-pinned-default-is-the-documents-own.md` — cannot change what `required`
advertises for outputs, because the advertisement is a function of the document.

**One caveat, stated plainly: this is settled for `outputSchema` and NOT for `inputSchema`.**
The unpinned input path still renders `model_json_schema()`, and its `allow_root_union=False`
contract (MCP clients need an object root to draw a form) makes moving it a separate change with
its own blast radius — `create_media_buy`'s request document has a root `anyOf`, which that
contract rejects outright. The pinned input path already publishes the document. So if the
pinned-default branch needs the same guarantee on the input side, that is a second lane, and
§5's size question sits in front of it.

---

## 7. MEASUREMENTS

| | before | after |
| --- | --- | --- |
| `make test` | 91 failed / 16108 passed / 2823 skipped / 0 errors | **87 failed / 16112 passed / 2823 skipped / 0 errors** |
| `make gate` | 7 failed / 2563 passed of 2570 | **7 failed / 2563 passed — unmoved** |
| R12's four failures | 4 red | **0 red** |
| output schemas compacted, all 78 | 2,030,399 bytes | 1,497,429 (0.74x) |
| output schemas with a surviving ref in `inline` mode | 24 of 78 | **0 of 78** |
| unpinned 78-tool `tools/list` | — | 2,846,895 bytes (0.68x buyer budget) |
| pinned 78-tool `tools/list` | — | 1,770,192 bytes (0.84x of half-budget) |

The delta is exactly −4 failed / +4 passed, and the only failures left in the four test files
this lane touches are `test_server_dx.py`'s two
`test_typed_success_normalizes_legacy_status` — **FINDINGS-126.md's R6**, "legacy media-buy
lifecycle status no longer widened", a runtime-normalisation cause in another lane that was red
before this change and is red in the same way after it.

Files written: `src/adcp/server/mcp_tools.py`, `src/adcp/validation/schema_loader.py` (the
publishing path's own loader — `get_derived_portable_schema`, the memoized source-document
counterpart of `get_derived_mcp_schema`), and four tests repointed with the decision named in
each docstring. Nothing in `codegen/`, `src/adcp/types/**`, `tests_emit/`, `survey/` or
`Makefile`; the emitter was not asked to write anything new.
