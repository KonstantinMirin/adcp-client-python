# The STALE TEST rows: what was repointed, what was not, and why

Input: `FINDINGS-126.md`'s STALE TEST rows. Scope: `tests/**` and
`examples/seller_agent.py`. Nothing under `src/adcp/`, `codegen/`, `tests_emit/`,
`survey/`, `verdicts/`, `scripts/` or the `Makefile` was touched, and
`examples/seller_agent.py` turned out not to need an edit (see R4 below).

## The two runs, both mine

| | failed | passed | skipped | errors |
|---|---|---|---|---|
| before (`9647244af`, clean tree) | **126** | 16071 | 2821 | **4** |
| after | **91** | 16108 | 2823 | **0** |

Both `make test`, 10 deselected and 1 xfailed in each, 25:08 apiece. The before
run reproduces the figure `TASK.md` quotes exactly, so the delta below is
measured against the same tree the classification was made on. `make gate` is
unmoved at **7 failed / 2563 passed of 2570**.

**35 failures closed and all 4 errors closed. No new failure: the after set is a
subset of the before set** (`comm` over the two sorted `FAILED` lists reports
nothing on the after-only side). The two skips are the packaging module's own,
reached for the first time now that its fixture builds.

Of the 38 failures `TASK.md` lists as mine, **35 are closed and 3 are not** —
R7's `_to_store_dict` and `model_dump_as_received` tests, reported below as a
real gap rather than asserted over. The one permitted piece of a mixed row
(R16's snapshot) could not be done at all; its row's claim does not hold, and
that is reported too.

## Closed, by row

| row | n | what the test now asserts, and the decision it names |
|---|---|---|
| **R4** | 10 | `status` is required on every response, by the envelope conjunction. Four in-test payloads state it; two handler-output tests apply `adcp.server.mcp_tools._normalize_response_envelope`, which is where the SDK states it on the wire path; one reads the array rule out of a refusal that is no longer shadowed by `missing ('status',)`; one asserts the coordinator ECHOES the seller's `status` instead of listing it among invented defaults. Cites `CLAUDE.md` → "REQUIREDNESS IS A CONJUNCTION". |
| **R7** | 4 of 7 | the exclusion is on every OPTIONAL field and on no required one — §2's dump row, "serialisation keys on `required`, validation still keys on nullability". The marker test moved to the emitted `OmittedNotNull` (both halves, and why `is_no_explicit_null` is a membership test over two spellings); the tree sweep now asserts the invariant in all three directions; the two nullable-keeps-null tests became "a nullable optional is omitted too" plus a new test that the CLEAR survives through `adcp._null_clear.preserve_explicit_nulls`. |
| **R8** | 3 | §4's "What becomes what": a property-less object is `dict[K, V]` (so `ctx.context["correlation_id"]`), and a `$ref`ed scalar at a root is an alias, not a class (so no `.root`). |
| **R9** | 2 | §4's union root: the referring field is annotated with the BASE, the discriminator is `_BRANCH_DISCRIMINATOR`, and `CreativeRepresentation`'s `format_kind` sits on the distributed `format_kind` branch. The second test also stops asserting an OPEN `format_kind` vocabulary — see R24, which deletes the declaration that said so. |
| **R10** | 1 | a union base is reached by handing it the PAYLOAD; `model_construct` bypasses the dispatch, so the instance it returns is a member of no branch and the base-annotated field refuses it. |
| **R17** | 2 | each adopter-facing capability word is checked against the document position it serves (`__adcp_schema__`), not against the generator's collision-resolved spelling — §4, "a name is not an acceptance fact". |
| **R18** | 2 | the root `anyOf` is BRANCH CLASSES: the refusal names each branch's own missing requirement. The e2e fixture that carried `proposal_id` AND `packages` is refused at request validation, which the document's own `not` requires — with the consequence recorded below. |
| **R19** | 1 | `RequiredGroups`' new wording, matched in full. |
| **R20** | 4 | the postal country/system mismatch is refused BY THE BRANCH UNION: `anyOf` errors at the two fields that disagree, with the branch named, instead of a hand-written validator's sentence. |
| **R24** | 1 | the three declared divergences that no longer occur are deleted, each with the reason it became unreachable. The set only shrinks, which is what the suite itself says. |
| **R30** | 1 | a first type access realizes the graph through the EMITTED module (`adcp.types._schemas.core.product`), asserted absent-then-present in one subprocess. `_generated` is not on that path. |
| **R31** | 1 | the two httpcore generations' call SHAPE (names, kinds, defaults) plus the resolved origin of `socket_options`; not the annotation spelling, which differs by idiom and whose return type is each package's own class. |
| **R32** | 1 | the version envelope is carried where the document states it (the response branch) and NOT invented on the nested array-item classes. |
| **R33** | 2 | a `format: uri` node holds a URL object, so the comparison is against `str(...)`. |
| **the 4 ERRORs** | — | the built-distribution filter excluded any path component named `_schemas` and so dropped the emitted tree, which moved to `src/adcp/types/_schemas/`. Narrowed to the one directory it meant, `src/adcp/_schemas`, as a PREFIX test — in both places that had the component test (the fingerprint list and the `copytree` ignore). The four now pass (8 passed, 2 skipped in that file). |

The three remaining failures in `tests/test_nested_no_explicit_null_round_trip.py`
and the eight in `tests/test_manifest_response_readback.py` are R3, R5 and R11 —
not this lane's.

## Mixed rows: untouched, as instructed

**R3 (6 stale of 12), R5 (4 of 6)** — every failure left alone. For the record,
`TASK.md` uses R5's `test_forward_compat_reporting_operation_id_is_left_off_when_unset`
as the worked example of "repoint, don't delete" while also naming R5 as a mixed
row to leave alone. I took the explicit scope statement as governing, because the
collision risk it describes is with the lane holding `src/adcp/webhooks.py` —
the SDK half of the same row. The repoint it describes is still owed; it is one
edit in `tests/test_nested_no_explicit_null_round_trip.py` once that lane lands.

**R16 (1 of 4) — PERMITTED BUT NOT POSSIBLE, and the row's claim does not hold.**
The row says the snapshot is "regenerated with
`python scripts/regenerate_public_api_snapshot.py`". That command raises:

    AttributeError: module 'adcp.types._schemas.a2ui' has no attribute '__all__'
      scripts/export_resolution.py:114, in snapshot_entry
        for name in sorted(module.__all__):

**22 of the 28 namespaces the snapshot covers have no `__all__`** — every
`adcp.types.domains.<domain>` package module, which the mirror resolves to
`adcp.types._schemas.<domain>`. So does the TEST's own comparison loop, which
reads `module.__all__` for each of them outside its `try`, meaning no content
written into the fixture can make `test_public_api_surface_matches_snapshot`
pass. Its first assertion fails before that anyway, on the namespace SET:

    Extra items in the left set:   'adcp.types.domains.manifest_schema',
                                   'adcp.types.domains.brand_discovery',
                                   'adcp.types.domains.manifest'
    Extra items in the right set:  'adcp.types.domains.common'

That part IS a stale fixture. But the fixture is not the only stale thing, and
the piece that is mine cannot be written without `scripts/export_resolution.py`
— either the emitted domain packages export `__all__`, or that module derives a
module's exports some other way. **Both are outside this lane's write scope, so
the fixture was left untouched rather than hand-authored into a shape the named
command does not produce.**

## R7: three failures are a real gap wearing a stale test's clothes

`FINDINGS-126.md` flagged this and it holds. Decision 2 omits an optional
property's `None` on serialisation — and three tests grade contracts that were
built on `exclude_none=False` putting it back. **The new behaviour was not
asserted over them; they still fail.**

**1. `_to_store_dict`'s patch/response split, both halves
(`tests/test_rc3_media_buy_runtime.py`, 2 failures).** The function's own
docstring in `src/adcp/decisioning/handler.py:1189` states the contract:

> `patch=True` … Explicit nulls survive where the schema admits `null`, because
> the merge contract below treats `None` as "clear this field" …
> `patch=False` (a platform *response*) keeps every field, including unset ones.

With the omission on the FIELD, neither is expressible: `exclude_unset=True,
exclude_none=False` now emits no `null` at all, so an explicit clear reaches the
adopter store as "leave unchanged", and a response snapshot drops the model
default it promised to land. This is the silent failure `adcp._null_clear`'s
module docstring exists to prevent — *"The request succeeds, the cap stays on,
and nothing anywhere says so"* — on the store path instead of the wire path.
`preserve_explicit_nulls` is the mechanism that already solves it (verified: it
reinstates `budget_cap_timezone` and `daily_budget_cap` from `model_fields_set`
plus the request schema), and `_to_store_dict` does not call it. **The fix is in
`src/adcp/decisioning/handler.py` and is not this lane's.**

**2. `model_dump_as_received` no longer reproduces an admitted `null`
(`tests/test_wire_types.py`, 1 failure).** Measured:

    TargetingOverlayInput.model_validate_json('{"signal_targeting_groups": null}')
      .model_dump_as_received()  ->  {}          (the test asserts the document)

`model_dump_as_received` sets `exclude_none=False` deliberately and
`src/adcp/types/base.py:884`'s docstring states why: `terms_digest` binds to the
JCS form of `commercial_terms` **as declared**, and *"a reader treats those as
the same document; a digest does not"*. An optional-and-nullable property now
carries `OmittedWhenNone`, whose exclusion fires here too, so a received
document carrying an explicit `null` does not round-trip —
`tests/conformance/test_wire_round_trip.py`'s byte-for-byte claim holds only
because no fixture in it carries one. Asserting `== {}` here would delete the
only check of the digest contract, so it was left failing. **Two stated
decisions conflict and the resolution is the owner's: either `as_received`
reinstates nulls the way `preserve_explicit_nulls` does, or the digest contract
is restated.**

## Two consequences found while checking a row, neither of them mine to fix

**1. § D4's create-path gate over BUYER-SUPPLIED packages is unreachable through
a valid document** (found under R18). `maybe_hydrate_recipes_for_create_media_buy`
returns early without `proposal_id` (`src/adcp/decisioning/proposal_dispatch.py:727`),
and `create-media-buy-request.json#/anyOf/2` forbids `packages` beside one — so
on create, only DERIVED packages ever reach `validate_capability_overlap`. The
`update_media_buy` route is alive but its package patch forbids `product_id` and
`pricing_option_id`, the two fields the pricing check reads. The rule itself stays
graded by `tests/test_proposal_lifecycle.py` (6 tests, including the exact field
path and the update prefix), so nothing is ungraded; what is gone is the e2e
path. The repointed test records this in its docstring.

**2. `CreativeRepresentationFormatId` may be a product §4 says to DROP** (found
under R9). `core/creative-representation.json` is `allOf[0]` → the
`CreativeManifest` union, `allOf[1]` → `required: ['format_kind']` with
`not: {anyOf: [{required: ['format_id']}, …]}`. Distributing the branch over the
target's two branches gives one product whose conjuncts require `format_id` and
forbid it — an empty intersection, which §4's distribution rule says is DROPPED.
It is emitted. No payload can reach it (measured: a `format_id` payload is
refused at the root `oneOf`), so nothing is wrong on the wire; the class is a
name for an uninhabitable branch. **Emission, not a stale test.**

## One classification correction

**R4 names `examples/seller_agent.py` as a producer that omits `status`. It is
not one.** The two `test_discovery_payload_size.py` failures are
`create_media_buy` (empty `packages` → `adcp_error(...)`) and `list_creatives`
(→ `list_creatives_response(...)`), and both helpers are the SDK's
(`adcp.server.adcp_error`, `adcp.server.responses.list_creatives_response`).
Measured, each returns a pre-envelope payload:

    adcp_error(...)              -> {"errors": [...]}
    list_creatives_response(...) -> {"creatives": [], "pagination": {...}, ...}

That is the architecture, not a defect: the handler answers with its task's
payload and `_normalize_response_envelope` states the envelope at the transport
boundary. The stale part was the test, which graded a handler's raw dict against
the advertised schema of a whole response. Routed through the normalizer, all
seven parameters pass and the five that already passed are unchanged. **So no
edit to `examples/seller_agent.py` was needed, and none was made.**

One prose reference survives the R24 deletion and needed no edit:
`docs/types-9-migration.md:454` names
`format_kind_is_an_open_vocabulary_by_decision` and says in the same paragraph
that *"the entry is deleted automatically by
`test_every_declared_divergence_still_occurs` once it stops matching"* — which
is what happened. `docs/` is outside this lane's write scope in any case.

## Checks

* `make gate`: 7 failed / 2563 passed of 2570 — unmoved, as required.
* `ruff check` over the 17 touched files: identical to the pre-change output
  (3 pre-existing findings, 0 new).
* `black`: the three files my edits made unformatted were reformatted; the two
  that were already unformatted at `9647244af`
  (`tests/conformance/_schema_parity.py`,
  `tests/test_manifest_response_readback.py`) were left alone rather than
  churned, since black's complaint there is about pre-existing lines.
