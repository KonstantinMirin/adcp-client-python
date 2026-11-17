# The files that could not collect: what was wrong, and what they found once they could

30 test files failed COLLECTION before this change, so **nothing in them had ever been
graded**. All 30 collect now. The population is the 30 the suite reported, not the 30
`TASK.md` describes: measured with `.venv/bin/python -m pytest tests/ --collect-only -q`,
which `pyproject.toml`'s `pythonpath` pins to this checkout, **none** of the 30 is a
`test_pg_*` file. `addopts` carries `-m 'not integration'` and the PostgreSQL conformance
tests are marked `integration`, so they are deselected before collection and never appear.
The task's "14 are `test_pg_*`" is a count from a run without that filter.

## The two halves, separately

| | before | after |
|---|---|---|
| **collection errors** (`pytest tests/ --collect-only`) | **30** | **0** |
| **collector entries not passing** (`len([c for c in report["collectors"] if c["outcome"] != "passed"])`) | **47** | **0** |
| tests COLLECTED | 17,893 | 18,994 |
| `failed` | 141 | see §"The delta" |
| `error` | 4 | see §"The delta" |

The two collection-error rows count the same event differently and both are reported
because the task asks for the second. `--collect-only` prints one line per file that
raised; the JSON report's `collectors` list also marks every ANCESTOR of such a file, so
one broken file in `tests/` shows up as the file plus its directory. 30 files, 47 entries.

**The failure count goes UP, and that is the point rather than a regression.** A file that
could not collect contributed ZERO failures, so every failure the table in §"The delta"
shows as new is a test that was already broken and was invisible. The collection-error
count is reported above, separately, so unhiding is not mistaken for fixing.

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
`test_forward_compat_assets.py` and `test_rootmodel_proxy.py`. The `arm` in the EMITTED
tree and in the schemas is the document's own property name and is untouched.

## Outside the write scope — for the owner

`src/`, `codegen/`, `scripts/` and `tests_emit/` are out of scope here. Four things found
from inside `tests/` that belong there.

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

**3. Removing `tests/test_task_message_lattice.py` leaves a claim ungraded in `tests/`** —
that every task message in the registry resolves to a root class in the
`AdcpRequest`/`AdcpResponse` lattice. There may be an equivalent under `tests_emit/`; I did
not add one, because both trees are out of scope.

**4. Three words that look like `aliases.py` gaps, offered as questions and not as
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
