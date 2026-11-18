# The webhook envelope knows which branch its `result` is; the union does not

`core/mcp-webhook-payload.json#/properties/result` points at `core/async-response-data.json`,
a **42-branch untagged `anyOf`** with no `discriminator` keyword. The union is referenced at
exactly that one position in the bundle. **The emission is faithful and the lowering is not
the defect** — the document cannot discriminate, and inventing a discriminator it does not
state is the one thing the compiler must never do.

What is built: `adcp.webhook_result.resolve_result(payload)`, re-exported from
`adcp.webhooks`. A plain function over the already-validated envelope, in hand-written SDK
code. No compiler change, no patch to the generated `McpWebhookPayload`, no import-time
model patch.

---

## 1. THE DOCUMENT MANDATES THE RESOLVER. It is not a workaround.

`core/async-response-data.json`'s own `description`:

> Because this shared webhook union is not tagged with the originating task type, callers
> **MUST** also validate a terminal result against that task or event's specific schema.

So the resolver is the behaviour the spec instructs a caller to perform, and the SDK
existing to do it for the developer is exactly its job. That sentence is quoted in the
resolver's docstring and in the repointed test, as the authority for each.

It also settles the test split (§5): the bare-union half cannot work **by the document's
own statement**, so repointing it asserts what the document says rather than conceding a
limitation.

## 2. THE VACUITY, re-derived by VALIDATION: 15 of 42

Measured the way `adcontextprotocol/adcp#8964` measures it — validating `{}` against each
branch over the 3.2 bundle with a reference-resolving Draft-07 validator, not with a
structural proxy:

```
{} validates against 15 of 42 branches
  anyOf/2  GetProductsAsyncWorking          anyOf/23 UpdateMediaBuyAsyncWorking
  anyOf/3  GetProductsAsyncInputRequired    anyOf/24 UpdateMediaBuyAsyncInputRequired
  anyOf/13 CompactTaskWorking               anyOf/29 BuildCreativeAsyncWorking
  anyOf/14 CompactTaskInputRequired         anyOf/30 BuildCreativeAsyncInputRequired
  anyOf/16 GetSignalsAsyncWorking           anyOf/35 SyncCreativesAsyncWorking
  anyOf/19 CreateMediaBuyAsyncWorking       anyOf/36 SyncCreativesAsyncInputRequired
  anyOf/20 CreateMediaBuyAsyncInputRequired anyOf/39 SyncCatalogsAsyncWorking
                                            anyOf/40 SyncCatalogsAsyncInputRequired
```

The 15 are exactly the `working` and `input-required` branches, which is the shape of it: a
progress payload's schema requires nothing, so it accepts a completed response.

**THE EARLIER FIGURE OF 17 WAS A PROXY AND IS WITHDRAWN.** A structural proxy — no top-level
`required`, `additionalProperties` not `false`, no `allOf` — answers **17**, and the two it
over-counts are reproduced here exactly: `anyOf/10 MediaBuyCommitmentResponse` and
`anyOf/11 ControlMediaBuyResponse`. Both are `oneOf` parents carrying
`discriminator: {propertyName: status}` with no top-level `required` of their own, and `{}`
satisfies no branch of either because every branch requires `status`. Use **15**, and
`tests/test_manifest_response_readback.py::test_the_empty_object_satisfies_fifteen_of_the_forty_two_branches`
is where it is asserted so it cannot drift back.

## 3. HOW THE MAPPING WAS DERIVED — two readings, 42 of 42 branches, nothing hand-listed

The owner's instruction was to derive rather than type out 42 branches, and to say how.
Two readings of the bundle, each one the bundle's own statement, and each used for the one
thing it is authoritative about.

**Reading 1 — `manifest.json`'s `task_result_resolution`, which the bundle says consumers
MUST use.** `core/tasks-get-response.json#/properties/result`:

> Present when include_result was true and a **completed, failed, or rejected** task
> produced a terminal artifact; canceled tasks may omit it. Consumers and sellers **MUST
> resolve and validate the exact schema through `manifest.task_result_resolution`**: use
> `terminal_schema_overrides[task_type]` when present, otherwise
> `tools[task_type].response_schema`.

The manifest states it machine-readably:

```json
"task_result_resolution": {
  "discriminator_field": "task_type",
  "terminal_schema_pointer_template": "/tools/{task_type}/response_schema",
  "terminal_schema_overrides": {"media_buy_delivery": "media-buy/media-buy-delivery-webhook-result.json"}
}
```

So, per member of `enums/task-type.json`: a terminal status names
`terminal_schema_overrides[task_type]` where present and `tools[task_type].response_schema`
otherwise; and each entry of `tools[task_type].async_response_schemas` names the status its
own filename ends in — `-async-response-input-required.json`, `-submitted`, `-working` —
matched against `enums/task-status.json` so the suffix is **a status value and not a guess
at one**. That reading alone reaches **41 of the 42 branches**.

**Reading 2 — the ENVELOPE's own `if`/`then`, which reaches the 42nd.**
`core/mcp-webhook-payload.json` carries an `allOf` of conditional clauses, and this is the
**only place in the bundle** where the dependency the union lacks is written down:

```json
{"if":   {"properties": {"task_type": {"const": "get_products"},
                         "result": {"properties": {"status": {"const": "rejected"}},
                                    "required": ["status"]}},
          "required": ["task_type", "result"]},
 "then": {"properties": {"result": {"$ref": ".../media-buy/get-products-rejected.json"}}}}
```

`task_result_resolution` never names `media-buy/get-products-rejected.json` at all, because
a terminal status resolves to the task's `response_schema` and that is
`get-products-response.json`. **This clause is both the 42nd branch and the fix shape #8964
asks for, already applied once by upstream's own hand** for one of the 42 positions. It is
read rather than re-stated here, so more clauses after the issue lands need no edit.

Reading 2 **replaces** reading 1 where it speaks. That is the one precedence in the
derivation and the only one the bundle states: a clause naming ONE pair is a more specific
statement than a template over every `task_type`.

**Then: document → class, off `__adcp_schema__`.** Each named document is followed through
`allOf`/`$ref` to the nearest branch of the union, and the branch's root class read off the
mro. Each of the union's branch classes carries its own position
(`SchemaRef('core/async-response-data.json', '#/anyOf/<i>')`) and inherits the referenced
document's root class, which carries `SchemaRef(document, '#')` — so walking the mro for
that root turns a branch POSITION into a branch DOCUMENT. Measured: **42 documents, each
with exactly one root class, from 46 branch classes** (two positions are themselves
three-branch `oneOf`s, which is where the extra four come from).

The `allOf` hop matters for four branches. `media-buy/buy-products-response.json` is a title
and a description over `allOf: [media-buy/media-buy-commitment-response.json]`, and the
union holds the inner one; the compact lifecycle's async schemas
(`buy-products-async-response-working.json` and friends) are titles over
`core/compact-task-{working,submitted,input-required}.json`. Longest chain measured on 3.2:
**one hop**.

**THE ONE DECLARATION, and it is three status values rather than 42 branches.**
`TERMINAL_STATUSES = ("completed", "failed", "rejected")`, from the
`core/tasks-get-response.json` sentence quoted above. Nothing in the bundle states the
terminal set machine-readably, so this is cited prose read once rather than derived — and it
is three values with one citation, not a table that can go stale per-branch.

**The root class and not the position subclass is what gets validated**, because the
document's own `oneOf` is what finally picks the shape — the repo's own rule, *a consumer
does not pick the branch at a reference position; pydantic does*. A `preview_creative`
result comes back as `PreviewCreativeVariantResponse`, a `build_creative` one as
`BuildCreativeSuccess` / `BuildCreativeMultiSuccess` / `BuildCreativeVariantSuccess`, with
no help from the caller.

## 4. WHAT THE DERIVATION COVERS, and what happens to a pair it does not

`task_type x status` is 38 x 9 = **342** pairs against 42 branches, so most pairs cannot
resolve and the useful question is which.

| population | n |
|---|---|
| branch documents the derivation reaches | **42 of 42** |
| distinct branch classes reached | **42** |
| pairs the derivation NAMES a document for | **153 of 342** |
| — resolve to exactly one branch of the union | **87** |
| — name a schema the union DOES NOT CONTAIN | **66** |
| — name MORE THAN ONE branch | **0** |
| task types with at least one resolvable pair | **16 of 38** |
| pairs named by reading 2 (the envelope) | **1** |

**A pair the derivation does not cover raises `WebhookResultUnresolvedError` and never
guesses.** Picking one of the 15 branches that admit any object is exactly the behaviour
being replaced. Three refusals, each carrying its measurement:

* **Unnamed pair.** `canceled`, `auth-required`, `unknown`, and every status a task's
  manifest entry omits. For `canceled` the bundle says so itself — "canceled tasks may omit
  it". The error names the pair and the procedure that did not answer.
* **Named, but outside the union** — the 66. The error carries the schema, because that is a
  schema the caller can still validate against; `resolve_result({'task_type':
  'sync_accounts', 'status': 'completed', ...})` raises with
  `document='account/sync-accounts-response.json'`.
* **Named more than once.** Zero on 3.2. **Reported, not silently resolved**, as the owner
  asked: the derivation ACCUMULATES candidate documents instead of overwriting them, so
  `ambiguous_pairs()` is a measurement a reader takes rather than an emptiness assumed, and
  `resolve_result` refuses rather than choosing between two documents the bundle gives no
  precedence between.

And `result` absent is not an error at all: the member is optional on the envelope, and
`resolve_result` returns `None`.

**THE 66 ARE THE OTHER HALF OF #8964, and they are worth naming.** The manifest knows
exactly which schema a `sync_accounts` webhook carries; `core/async-response-data.json` has
no branch for it. So the vacuous branches accept the payload and nothing notices. 22 of the
38 task types are in this state:

`acquire_rights`, `activate_signal`, `create_property_list`, `delete_property_list`,
`get_account_financials`, `get_brand_identity`, `get_creative_delivery`, `get_principal`,
`get_property_list`, `get_rights`, `list_property_lists`, `log_event`, `search_brands`,
`sync_accounts`, `sync_agent_notification_configs`, `sync_audiences`, `sync_event_sources`,
`sync_principal`, `sync_reporting_receipts`, `sync_reporting_status`, `update_property_list`,
`update_rights`

One measured oddity, recorded rather than smoothed. `media-buy/decline-proposals-response.json`
is the `response_schema` the manifest puts in `decline_proposals`' TERMINAL slot, and that
document states `status: {const: "submitted"}`. So `(decline_proposals, completed)` resolves
to `DeclineProposalsResponse` and a `completed` payload is then refused by the branch's own
`status`:

```
status  Input should be 'submitted' [type=literal_error, input_value='completed']
```

The resolver surfaces that rather than reaching for a different branch — a pair that names
a branch has its answer, and a payload the branch refuses is a finding. (The same task's
`submitted` resolves cleanly, through the async slot, to `CompactTaskSubmitted`.)

## 5. THE TEST SPLIT — two claims, one of them impossible

`tests/test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip`
did two different things, which is why it read as one failure.

**The bare-union half asked for something no conforming consumer can do.** It asserted
`isinstance(TypeAdapter(AdcpAsyncResponseData).validate_json(payload),
PreviewCreativeVariantResponse)`; what it got was `GetProductsAsyncWorking` — `anyOf/2`, one
of the 15. Repointed to assert what the document DOES guarantee, with the §1 MUST sentence
and the 15-of-42 measurement in the docstring so the next reader does not re-file it. Three
things hold and are now checked:

1. the union **accepts** the payload — the emission is faithful;
2. the branch it returns is **uninformative** — `type(result).model_validate({})` succeeds,
   so the match carries no information;
3. the payload **survives whole** — `extra='allow'` keeps every member the vacuous branch
   does not declare, which is what lets the second validation recover the branch afterwards.

**The envelope half is a real requirement and is what the resolver serves.** It now reads
the branch through `resolve_result`, against the validated `McpWebhookPayload`, against the
re-parsed dump, and against the raw mapping a receiver holds — all three name the same
branch.

`test_public_completed_task_parser_keeps_manifest_readback` carried the same impossible
`isinstance` through `ADCPClient.handle_webhook_legacy`, whose result is typed
`TaskResult[AdcpAsyncResponseData]` — the bare union again, and that parser is not handed the
`task_type` to resolve with. Repointed the same way: the parse succeeds, nothing is lost, and
the envelope it was handed resolves to the task's branch.

Six tests were added for the resolver itself, in the same file (the derivation's census, the
42-of-42 reach, seven spot checks each exercising a different clause, the three refusals, and
the `ValidationError` propagation), so the figures in §3 and §4 are asserted and not just
written here.

## 6. `FINDINGS-126.md` row R11 — 8 of 11 close

Read off the two suites' own artifacts and not off a count: the before-set from the
baseline run's `test-results/sdk/junit.xml`, the after-set from this lane's, diffed by
test id.

| test | n | state |
|---|---|---|
| `test_manifest_response_readback.py::test_async_response_union_and_webhook_round_trip` | 4 | **closed** |
| `test_manifest_response_readback.py::test_public_completed_task_parser_keeps_manifest_readback` | 4 | **closed** |
| `test_legacy_only_creative_surfaces.py::test_primary_webhook_sanitizes_every_status_and_activity[failed, working, input-required]` | 3 | **open — out of this scope** |

The diff is those 8 and nothing else: **0 failures appear that were not there before, and
0 errors in either run.**

**The remaining 3 are a different claim and need a file this scope excludes.** They assert
that `ADCPClient.handle_webhook` SANITIZES legacy format identity out of the result; the
vacuous branch is why it cannot, because `extra='allow'` carries `format_id` straight
through and the v1→v2 projection that would strip it never recognises the payload as the
task's. The `[completed]` case passes, which locates it exactly: the fork is in
`src/adcp/client.py`'s `_canonicalize_*` path (around `client.py:2419`), and routing it
through `resolve_result` is the fix. `src/adcp/client.py` is not in this task's write scope,
so it is left and reported rather than half-done.

## 7. MEASUREMENTS

Taken in this worktree, this lane only, and read out of this worktree's own
`test-results/` rather than any shared path.

| | before | after |
|---|---|---|
| `make test` | **91 failed / 16108 passed / 2823 skipped / 0 errors** | **83 failed / 16128 passed / 2823 skipped / 0 errors** |
| `make gate` | 7 failed / 2563 passed of 2570 | **7 failed / 2563 passed of 2570** |
| `./check` | emitted 1059 / refused 0, approximated 805 facts in 239 documents | **emitted 1059 / refused 0, approximated 805 facts in 239 documents** |

**Both runs are on base `9505d5a58`**, and the baseline matches the trunk figure TASK.md
states, so no other lane had landed under this one at the time it was taken. Trunk has
since moved on and reads a different number; the eight closures in §6 are independent of
what landed, so the delta is re-measured on a rebase rather than carried forward from
here. `make gate` and `./check` do not move, because nothing here touches the emission.

**The arithmetic closes exactly, which is the check worth having.** Collected tests go
19,023 -> 19,035: **+12**, the six tests added for the resolver, one of them parametrized
over seven rows (5 + 7). Failures go 91 -> 83: **-8**, the eight named in §6. Passes go
16,108 -> 16,128: **+20 = 8 + 12**. Nothing else moved.

**A NOTE ON HOW THIS WAS MEASURED, because the first attempt was wrong twice over.** The
before/after pair here is two full runs; every intermediate question was answered with a
node-id run (`pytest tests/test_manifest_response_readback.py -q`, seconds) rather than a
24-minute suite. And both figures are read from `test-results/sdk/junit.xml` in THIS
worktree, which `make test` already writes there as a relative path. An earlier attempt
piped the suite through a shell redirect to a shared scratch path; that is the one thing
that can collide between lanes, there were three concurrent lanes on this box, and it is
not needed for anything — the artifact already exists, per-worktree, for free. The baseline
junit is kept at `test-results/baseline/` so the failure-name diff in §6 is reproducible
rather than a remembered count.

## 8. TWO THINGS LEFT, both outside the write scope

**The sighting registry owes `adcontextprotocol/adcp#8964` an entry.**
`tests_emit/test_decision_set.py::test_every_upstream_reference_this_repository_cites_has_a_sighting`
requires every upstream reference this repository cites to have a recorded sighting in
`codegen/attribution.py`'s `VERIFIED`, and #8964 is now cited by this file, by
`src/adcp/webhook_result.py` and by `tests/test_manifest_response_readback.py` and has none.
`codegen/attribution.py` is not in this task's write scope. Neither `make test` nor
`make gate` reads that census, so neither figure in §7 is affected; the entry is still owed.
The row to add, as `survey/upstream_issues.py` would print it:

```python
'adcontextprotocol/adcp#8964': Sighting(
    reference='adcontextprotocol/adcp#8964',
    state='OPEN',
    title='3.2: core/async-response-data.json admits every object -- 15 of its 42 anyOf '
          'branches admit {}',
    seen='2026-11-12',
),
```

**And nothing was filed or posted.** The defect was already open upstream before this work
started; it is cited, not re-reported.

**Four `import-not-found` errors under mypy**, from
`src/adcp/webhook_result.py`'s four `adcp.types.domains.*` imports. `adcp.types.domains` is
a runtime mirror with no files behind it, so a checker cannot resolve it — the identical
errors already stand on `src/adcp/webhook_receiver.py`'s five imports of the same tree, and
that sibling is what set the convention this module follows. `CLAUDE.md` makes a domain path
the supported public address; the flat `adcp.types` facade is lazy and binds these names as
variables, so annotating against it produces `Variable "adcp.types.McpWebhookPayload" is not
valid as a type` instead — which is the shape `webhooks.py` and `src/adcp/compat/*` already
carry. Matching the sibling means one tree-wide `domains`-stub fix repairs both.
