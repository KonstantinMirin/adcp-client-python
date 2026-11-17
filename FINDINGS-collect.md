# The files that could not collect: what was wrong, and what they found once they could

30 test files failed COLLECTION before this change, so **nothing in them had ever been
graded**. All 30 collect now: 24 were repaired and 6 were removed with the layer they
graded.

The population is the 30 the suite reports as ERRORS, and **none of them is a
`test_pg_*` file**. Measured with `.venv/bin/python -m pytest tests/ --collect-only -q`,
which `pyproject.toml`'s `pythonpath` pins to this checkout: the PostgreSQL files do not
error, they SKIP at module scope on `could not import 'psycopg_pool'`, so they never
appear in the error list. They are the source of the task's "14 are `test_pg_*`", because
they do appear in the JSON report's `collectors` list with `outcome == "skipped"` — see
the next section, where the two counts are reconciled. Nothing under `test_pg_*` was
touched.

## The two halves, separately

| | before | after |
|---|---|---|
| **collection ERRORS** (`pytest tests/ --collect-only`) | **30** | **0** |
| **collector entries not passing** (`len([c for c in report["collectors"] if c["outcome"] != "passed"])`) | **47** | **17** |
| &nbsp;&nbsp;…of those, `outcome == "error"` | 30 | **0** |
| &nbsp;&nbsp;…of those, `outcome == "skipped"` | 17 | 17 |
| tests COLLECTED | 17,893 | 18,994 |
| `passed` | 14,919 | 15,845 |
| `failed` | **141** | **316** |
| `error` | 4 | 4 |

**The second row is not all errors, and that is where the task's "14 are `test_pg_*`"
comes from.** The task's formula counts every collector whose outcome is not `passed`, and
17 of the 47 were `skipped` rather than `error` — the PostgreSQL files, each skipping at
module scope on `could not import 'psycopg_pool'`. 14 of those 17 are under
`tests/conformance/`. They are untouched and they still skip; what went to zero is the
ERROR half, 30 of 30.

**The failure count goes UP, and that is the point rather than a regression.** 141 → 316,
+175. A file that could not collect contributed ZERO failures, so 174 of those 175 are
tests that were already broken and were invisible — they are listed per file in §"The
delta", and the collection-error count is reported separately above so unhiding is not
mistaken for fixing. Measured node by node against `before.json`, **exactly one test
passed before and fails after**, and it is the one in §"Outside the write scope" item 5.
**Zero tests went the other way**: nothing that was failing before passes now, because
nothing outside the 30 files was touched.

## The delta, per file

Every file whose count moved. All but the last had never been graded at all.

| file | before (tot/pass/fail) | after (tot/pass/fail) |
|---|---|---|
| `test_account_v3_wire.py` | 0 / 0 / 0 | 30 / 27 / 3 |
| `test_adcp_3_1_14_schema_backport.py` | 0 / 0 / 0 | 3 / 3 / **0** |
| `test_adcp_3_1_27_macro_urls.py` | 0 / 0 / 0 | 191 / 191 / **0** |
| `test_canonical_formats_compatibility.py` | 0 / 0 / 0 | 36 / 36 / **0** |
| `test_canonical_formats_roundtrip.py` | 0 / 0 / 0 | 31 / 16 / 15 |
| `test_canonical_formats_v1_to_v2.py` | 0 / 0 / 0 | 41 / 15 / 26 |
| `test_composability_invariant.py` | 0 / 0 / 0 | 6 / 6 / **0** |
| `test_constrained_array_empty_branches.py` | 0 / 0 / 0 | 14 / 14 / **0** |
| `test_discriminated_unions.py` | 0 / 0 / 0 | 66 / 45 / 21 |
| `test_extra_policy.py` | 0 / 0 / 0 | 17 / 17 / **0** |
| `test_format_assets.py` | 0 / 0 / 0 | 18 / 17 / 1 |
| `test_forward_compat_assets.py` | 0 / 0 / 0 | 65 / 65 / **0** |
| `test_geo_place_system_keys.py` | 0 / 0 / 0 | 111 / 59 / 52 |
| `test_legacy_asset_helpers.py` | 0 / 0 / 0 | 16 / 14 / 2 |
| `test_nested_no_explicit_null_round_trip.py` | 0 / 0 / 0 | 35 / 27 / 8 |
| `test_preview_html.py` | 0 / 0 / 0 | 16 / 7 / 9 |
| `test_protocol_envelope_inheritance.py` | 0 / 0 / 0 | 27 / 27 / **0** |
| `test_rc6_adoption.py` | 0 / 0 / 0 | 216 / 215 / 1 |
| `test_reporting_consumer_loop.py` | 0 / 0 / 0 | 55 / 55 / **0** |
| `test_rootmodel_proxy.py` | 0 / 0 / 0 | 8 / 8 / **0** |
| `test_simple_api.py` | 0 / 0 / 0 | 9 / 8 / 1 |
| `test_targeting_overlay_schema.py` | 0 / 0 / 0 | 5 / 5 / **0** |
| `test_type_aliases.py` | 0 / 0 / 0 | 44 / 33 / 11 |
| `test_type_coercion.py` | 0 / 0 / 0 | 41 / 17 / 24 |
| `test_native_ci.py` | 8 / 8 / **0** | 8 / 7 / **1** |
| **total** | **8 / 8 / 0** | **1,109 / 934 / 175** |

Eleven of the 24 repaired files pass completely. The six removed files
(`test_type_guards.py`, `test_type_validation_helpers.py`, `test_generated_poc_alias.py`,
`test_sync_schemas.py`, `test_sync_schemas_signed_release.py`,
`test_task_message_lattice.py`) contribute no rows, because they contributed no tests
before either.

`ruff check tests/` moved 99 → 79 over the same change, and `./check` is unmoved:
**emitted 1059 / refused 0**.

## The rule applied, per missing name

`TASK.md` allows exactly one of RE-POINT or DELETE per name. Here is every one.

### RE-POINTED — the subject exists, under the name its document gives

| name as imported | where the subject is | why the import was wrong |
|---|---|---|
| `adcp.types.CreditLimit` | `adcp.types.domains.core.account.CreditLimit` | two documents declare the word, so the flat namespace binds neither; `__adcp_refused__` declares the flat spelling DOCUMENT-NO-WORD-NO-IDENTITY against *upstream's* subject (`account/sync-accounts-response.json`), and this file builds `core/account.json`'s |
| `adcp.types.domains.core.registry_event.BadgeRole` | `AdCPProtocol`, via the payload's `role` field | the pinned bundle inlines `$defs/badgeRole`'s target, so the entry IS the enum and has no `.root` |
| `adcp.types.v31` | `adcp.types` | UNRESOLVABLE-UPSTREAM: one bundle is pinned, so there is one class per subject and no per-version namespace |
| `adcp.types.canonical_creative.Format` (×3 files) | `adcp.types.Format` | UNRESOLVABLE-UPSTREAM; the value built is `format_kind` + `params`, the canonical declaration |
| `adcp.types.canonical_creative.CreateMediaBuyResponse1` / `2` | `adcp.types._generated` | same module refused; the branches resolve beside their eight siblings |
| `adcp.types.legacy.LegacyFormat` (×4 files) | `adcp.types.core.LegacyFormat` | `adcp.types.legacy` is the `Legacy`-prefixed surface over v1 DOCUMENTS; the v1 named-format DEFINITION is not one |
| `adcp.types.legacy.coerce_legacy_asset` + 2 siblings | `adcp.types` | a normalisation helper is not a document either |
| `adcp.types.is_canonical_format_kind` | `CanonicalFormatKind` membership | NO-DOCUMENT-NO-SUBJECT: a document states the enum, not a predicate over a value |
| `adcp.types.SyncAccountsAccount` | `adcp.types.domains.account.sync_accounts_response.AccountsItem` | §4 names a nested node for its property alone, because the module path carries the document |
| `adcp.types.CpmVendorPricingOption` | `…core.vendor_pricing_option.VendorPricingOptionCpm` | the `model: cpm` branch |
| `adcp.types.VendorPricingOptionUnion` | `…core.vendor_pricing_option.VendorPricingOption` | the union base; the `*Union` word is an Annotated expression with no document |
| `adcp.types.FormatAssetUnion` / `GroupFormatAssetUnion` | `BaseIndividualAsset` / `BaseGroupAsset` | an `asset_type` union IS its base in this emission, so the union and the fallback are one class |
| `adcp.types._generated.AuthorizedAgents` … `AuthorizedAgents3` | `…AuthorizedAgentsItemPropertyIds`, `…PropertyTags`, `…InlineProperties`, `…PublisherProperties` | §4 emits no positional name; the three trailing comments in the old import block were the branch count written down |
| `…refine_proposals_response.RefineProposalsResponse1` | `RefineProposalsResponseCompleted` | positional |
| `…request_proposals_response.PurchaseContinuation1` | `PurchaseContinuationLegacyCreate` | positional, and the branch the `kind: legacy_create` fixture selects |
| `…core.geo_place_system.GeographicPlaceIdentifierSystem1` | the token `Literal` inside `GeographicPlaceIdentifierSystem` | the `oneOf` of tokens and an HTTPS URI lowers to one `Annotated` union |
| `adcp.types.domains.bundled.*` (×2 files) | the one tree, `adcp.types.domains.*` | there was a SECOND generated tree; §4's one-class-per-subject leaves no copy to grade |
| `adcp.types.domains.core.format.Format` | `LegacyFormat` | that module is `core/format.json`, whose root is the v1 definition |

### DELETED — the only subject is a layer this release does not have

| file / test | the layer |
|---|---|
| `tests/test_type_guards.py` (whole file, 17 predicates) | `adcp.types.guards` binds nothing: `__all__` is empty and all 17 names are refused NO-DOCUMENT-NO-SUBJECT. `src/adcp/__init__.py` states the reason where it declines to route them — a response-shape predicate is not something a document says about an instance |
| `tests/test_type_validation_helpers.py` (whole file) | `adcp.types.validation` is UNRESOLVABLE-UPSTREAM; what the file graded is that module's adapter cache, its reuse, and `monkeypatch` on its `TypeAdapter` symbol. `tests/conftest.py` has a `validate_union` of its own, and pointing the tests at it would grade the test helper instead of the SDK |
| `tests/test_generated_poc_alias.py` (whole file) | `adcp.types._generated_poc_alias` — an import finder serving `adcp.types.generated_poc` under its new name — plus `scripts.generate_types` |
| `tests/test_sync_schemas.py`, `tests/test_sync_schemas_signed_release.py` | `scripts/sync_schemas.py`; the bundles are vendored under `schemas/cache/` and pinned by `src/adcp/ADCP_VERSION` |
| `tests/test_task_message_lattice.py` (whole file) | `scripts.generate_types` and `scripts.post_generate_fixes`. See §"Outside the write scope" — the third import, `scripts.task_message_lattice`, exists and returns NOTHING against this tree |
| 5 tests in `tests/test_extra_policy.py` | `scripts.post_generate_fixes`'s text surgery: `_set_class_extra_allow`, `_ensure_configdict_import`, `_inline_typed_extra_annotations`, `_open_payload_class_names`, `_first_generated_class_name`. §2: nothing rewrites emitted output |
| 7 tests in `tests/test_protocol_envelope_inheritance.py` | `adcp.types.canonical_creative`'s `CanonicalBoundaryModel` policy, its deleted `.pyi` stub and its clone-versus-subclass ancestry |
| 1 test in `tests/test_canonical_formats_compatibility.py` | `canonical_creative.sanitize_canonical_schema`; the test asserts what the sanitizer's hand-written key list covers, which is a claim about no document |
| 5 tests in `tests/test_forward_compat_assets.py` | the open-union widening — see §"The open union was a widening" |

## What they found once they collected

### The open union was a widening, and it is gone

Issue #742 made an asset slot TOLERATE an `asset_type` this pin has no class for: the
undeclared value landed on a fallback class and kept its unknown keys as extras.
`core/format.json` states the slot as a CLOSED `oneOf` over the 21 individual and 21 group
asset types it declares, so the tolerance admitted a value the document refuses. §2
licenses a widening only where a keyword cannot be expressed, and a `oneOf` can be — which
is why the old one needed a hand-written frozenset in `aliases.py`, the same frozenset that
fell 7 behind the individual classes and 9 behind the group ones. Five acceptance tests
asserted that widening and are replaced by its negation, measured at the slot.

`isinstance(asset, UnknownFormatAsset)` can no longer distinguish a branch from the
fallback, because the fallback IS the base and `isinstance` holds against a parent by
construction. Both directions are identity checks now. This is the "test asserting the old
FLAT class graph" cause, in the form it takes when the base is also a usable class.

### Three sweeps were reading an empty directory

`adcp.types.domains` is a compatibility MIRROR: `src/adcp/types/domains/` holds one
`__init__.py` and the compiler writes the tree at `src/adcp/types/_schemas/`. Three
whole-tree sweeps walked the mirror and so graded nothing while passing:

* `test_constrained_array_empty_branches.py` — no empty model branch beside a list;
* `test_extra_policy.py::test_no_spurious_extra_allow`;
* (and `test_task_message_lattice.py`'s, which could not be repaired by changing a path).

All three read `_schemas` now. The first two still pass against the real tree.

### A pin in an annotation is not a pin in a default

`_declared_asset_types` derived the `asset_type` vocabulary from each branch's field
DEFAULT. The document states the discriminator with a `const`, which this emission lowers
to `Literal["image"]` and leaves REQUIRED, so the pin is in the annotation. Reading the
default found nothing at all, and the function's own assert-non-empty guard then took the
whole module at import — a derivation that matches nothing passing everything, caught by
the guard that was put there for exactly that.

### Fixtures short a key the document requires

Three files, and in each the key is required by a node the fixture's own branch did not
state. REQUIREDNESS IS A CONJUNCTION:

* `test_extra_policy.py` — `check-governance-request.json` `allOf[3]` states
  `if {required: [payload]} then {required: [plan_id, tool, target_agent]}`, and the
  fixture carried only `plan_id`.
* `test_reporting_consumer_loop.py` — the revision fixture ran at MODULE scope, so its
  `ValidationError` *was* the collection error. Short five keys: `schema_dialect` and
  `schema_ref_policy` (on the document's own `required` list, each a `const`), `value_type`
  on a control-total item (also what the item's two-branch `oneOf` is keyed on, so without
  it the total satisfied neither branch), and — under `finality='official'` —
  `finality_basis` and `finality_policy_id` with `finalized_at`.
* `test_protocol_envelope_inheritance.py` —
  `SyncCreativesSuccessResponse.model_validate({"creatives": []})` expected `status` to
  default. The success branch of `creative/sync-creatives-response.json` states no `status`
  of its own, so the field is the envelope's full `TaskStatus` enum one `allOf` up, and the
  decision index is explicit that a multi-member `enum` gets no default.

### Two claims came out STRONGER than they were pinned

* **`test_targeting_overlay_schema.py`** pinned ten targeting fields as advertising no
  `description`. Measured bare at the field node: 32 of 37. The descriptions are not lost —
  an optional nullable field advertises as an `anyOf` over the shape and `null`, and the
  shape's description travels on its branch. Read at both positions, **0 of 37** are
  undocumented, so the exception list is deleted rather than regrown.
* **`test_composability_invariant.py`** pinned four reviewed public/bundled name clashes,
  matching only the NAMES — so a clash between two classes of the SAME subject, the thing
  §4 forbids, would have passed as long as somebody wrote the name down. Each class carries
  `__adcp_schema__`, so "different concept" is measurable: the sweep admits a clash exactly
  when the two pointers differ and refuses one where they agree. Three of the four rows are
  gone because the nested class IS the public one now.

### Vocabulary

A union's parts are BRANCHES. `tests/test_constrained_array_empty_arms.py` is
`git mv`-ed to `tests/test_constrained_array_empty_branches.py`, and the word is gone from
that file, from `test_protocol_envelope_inheritance.py`,
`test_forward_compat_assets.py`, `test_rootmodel_proxy.py`,
`test_discriminated_unions.py`, `test_geo_place_system_keys.py` and
`test_targeting_overlay_schema.py`. The `arm` in the EMITTED
tree and in the schemas is the document's own property name and is untouched.

## Outside the write scope — for the owner

`src/`, `codegen/`, `scripts/` and `tests_emit/` are out of scope here. Five things found
from inside `tests/` that belong there, the third of which is a one-line fix that a CI job
needs.

**1. A required property the document PINS with a `const` does not default to it.** The
decision index states the opposite, citing
`verdicts/a-pinned-default-is-the-documents-own.md`:

> `ImageAsset(url=…, width=…, height=…)` supplies `asset_type="image"` itself, because
> `const` states it. A multi-member `enum` gets no default.

Measured: `core/assets/image-asset.json` states `asset_type` with
`{"const": "image", "type": "string"}` and lists it in `required`, and
`ImageAsset.model_fields["asset_type"]` is `annotation=Literal['image'] required=True` with
no default. `core/reporting-revision.json`'s `schema_dialect` and `schema_ref_policy`
behave the same way, as does every `core/format.json` asset branch.

This is the whole cause of **9 failures in `tests/test_preview_html.py`**, and they cannot
be fixed from `tests/`: the construction is inside
`src/adcp/utils/preview_cache.py:658`, which calls
`ImageContent(url=…, width=…, height=…)` and gets `asset_type Field required`. Either the
index row or the emission is wrong, and which one is the owner's call.

**2. `scripts/task_message_lattice.py` is dead code against this tree.** It maps a schema to
its module by the `filename:` comment the old generator wrote into each file;
`generated_module_by_schema(Path("src/adcp/types/_schemas"))` finds **0 of them**. Its
docstring names three consumers and two of them are deleted modules.

**3. `scripts/ci/run_native_tests.py` names a file this change deleted, and that is the
one true regression in the suite.** `COMPATIBILITY_TESTS` lists
`"tests/test_type_guards.py"`, which went with `adcp.types.guards`, so
`tests/test_native_ci.py::test_compatibility_suite_checks_runtime_on_every_interpreter_without_adopter_rebuilds`
— which asserts every path in that tuple `is_file()` — now fails. It is the only test in
the suite that passed before this change and fails after it.

The fix is deleting one line from `scripts/ci/run_native_tests.py`. This task's write scope
is `tests/` plus this file, so it is recorded here rather than applied. It is also worth
deciding whether `tests/test_type_aliases.py` should stay in that tuple: it is listed
beside the deleted one, and 11 of its 44 tests fail.

**4. Removing `tests/test_task_message_lattice.py` leaves a claim ungraded in `tests/`** —
that every task message in the registry resolves to a root class in the
`AdcpRequest`/`AdcpResponse` lattice. There may be an equivalent under `tests_emit/`; I did
not add one, because both trees are out of scope.

**5. Three words that look like `aliases.py` gaps, offered as questions and not as
defects.** Each has a plausible reading on which it is a decision, which is why none is
filed as a bug:

* **`BadgeRole`.** §4 names a `definitions` entry `<Key>`, and `core/registry-event.json`'s
  `$defs/badgeRole` has no class — the pinned bundle inlines its target and the compiler
  binds the one `AdCPProtocol`. One object under two names is what the alias layer is for.
  Against it: §8 says such an entry is proved by its own class "and by nothing that
  references it", and an entry that IS another document's enum may have no second identity
  to name.
* **`LegacyFormat` is absent from `adcp.types.legacy`** while `LegacyFormatId` is present.
  Four test files reached for it there, which is some evidence about where a reader expects
  it. Against it: CLAUDE.md pins `adcp.types.core.LegacyFormat` as the one address *on
  purpose*, and a second spelling is the thing §4 spends names avoiding.
* **`FormatAssetUnion` / `GroupFormatAssetUnion`** are refused, and the objects they named
  — `BaseIndividualAsset`, `BaseGroupAsset` — are bound, as `UnknownFormatAsset` and
  `UnknownGroupAsset`. Those two words now name the union AND the fallback, which is
  accurate for this emission and reads oddly. Against a rename: both are the document's
  `$defs` nodes and neither word is the document's.
