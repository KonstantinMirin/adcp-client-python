# Findings — deleting tests on three decided grounds

Six files. Each failure was classified against the three grounds the owner decided,
and only a failure matching a ground was deleted. Everything else is left RED with its
measured cause, because "it fails" is not a ground and the owner's last paragraph says
so.

**THE GROUNDS, as applied.**

* **(a) DELETED LAYERS** — the test imports, or asserts on the presence of,
  `adcp.types._eager`, `_forward_compat`, `generated_poc`, `_generated_poc_alias` or
  `adcp.types.domains.bundled`. `src/adcp/types/_restored.py` records that these are
  not restorable here: *"the aggregator stays deleted along with the generator that
  wrote it."*
* **(b) `Legacy*` DIVERGENCE** — the test requires a `Legacy*` name to behave
  differently from its canonical twin where no second document exists to make a second
  class. A test asserting the alias RESOLVES stays.
* **(c) DUPLICATE JSON KEYS** — the test feeds the same key twice in one object.

**THE `Legacy*` MEASUREMENT, re-taken here.** Of the 51 `Legacy*` names on
`adcp.types.__all__`: 35 are the SAME OBJECT as their canonical twin, 12 have no
canonical twin bound at all, and 4 differ. Of those 4, three
(`LegacyBuildCreativeResponse{2,3,5}`) are a codegen numbering offset within one
document's arms, and exactly one is a real split — `LegacyFormat`
(`core/format.json`) against `Format` (`core/product-format-declaration.json`), two
documents, which is why it is real.

---

## Counts

| file | before | after | removed | ground | left red |
|---|---|---|---|---|---|
| `tests/test_lazy_types.py` | 45 items: 14 F, 31 P | 38: 7 F, 31 P | 7 | (a) 7 | 7 |
| `tests/test_migrate_v3_to_v4.py` | 80: 19 F, 61 P | 76: 15 F, 61 P | 4 | (a) 3, (b) 1 | 15 |
| `tests/test_legacy_surface_names_every_arm.py` | 55: 53 F, 1 P, 1 S | 55: 53 F, 1 P, 1 S | 0 | — | 53 |
| `tests/test_asset_aliases_stable.py` | 48: 19 F, 29 P | 48: 19 F, 29 P | 0 | — | 19 |
| `tests/test_reporting_capability_models.py` | 30: 13 F, 14 E, 3 P | 15: 12 F, 3 P | 15 | (a) 15 | 12 |
| `tests/test_targeting_overlay_errors.py` | 149: 5 F, 144 P | 147: 4 F, 143 P | 2 | (c) 2 | 4 |
| **total** | **407: 123 F, 14 E, 269 P, 1 S** | **379: 110 F, 268 P, 1 S** | **28** | **(a) 25, (b) 1, (c) 2** | **110** |

F = failed, E = collection error, P = passed, S = skipped. Counts are collected ITEMS,
so a parametrized function counts once per param. One commit per file that changed;
two files changed nothing and have no commit.

**Removed per ground: (a) 25 items, (b) 1 item, (c) 2 items.**

The only PASSING item removed is the `control` param of the duplicate-key test under
ground (c); every other removed item was failing or erroring.

---

## What was removed

### `tests/test_lazy_types.py` — (a), 4 functions / 7 items

Commit `cae7921fb`.

| removed | why |
|---|---|
| `test_importing_a_partial_module_is_lazy` | asserted `adcp.types._eager` enters `sys.modules` on first name access |
| `test_targeting_input_resolves_lazily_with_canonical_identity` (4 params) | `from adcp.types import _eager, _generated` |
| `test_lazy_types_surface_matches_eager` | `from adcp.types import _eager` |
| `test_eager_only_extras_matches_eager_namespace` | same import; `_EAGER_ONLY_EXTRAS` is that module's own constant |

The module docstring's `(adcp.types._eager)` parenthetical and the
`== eager realization` section title went with them.

**Two tests that NAME `_eager` were kept, and the distinction is load-bearing.**
`test_import_adcp_does_not_build_schema_graph` and
`test_import_adcp_types_does_not_build_schema_graph` name it only in a
*not*-in-`sys.modules` clause, which a deleted module satisfies; their subject is the
import cost of `import adcp` / `import adcp.types`, and the `_generated` half of the
second one is live. They are vacuous with respect to `_eager` and true with respect to
what they are for.

### `tests/test_migrate_v3_to_v4.py` — (a) 3, (b) 1

Commit `cea91450f`.

(a) — three tests that IMPORT the deleted module:
`test_renamed_deep_imports_resolve_to_the_same_objects`
(`importlib.import_module("adcp.types.generated_poc.brand")`),
`test_deprecation_warning_names_the_codemod_invocation_that_rewrites` (subprocess
`import adcp.types.generated_poc.core.error`, asserting that module's own
DeprecationWarning), and
`test_split_detection_uses_the_same_suffix_the_runtime_alias_serves`
(`from adcp.types import _generated_poc_alias`).

The codemod is untouched and 61 of its tests still pass, because they assert on the
TEXT `adcp.types.generated_poc`, which `src/adcp/migrate/v3_to_v4.py` matches as a
string and never imports.

(b) — `test_auto_apply_does_not_guess_colliding_source_variant`. Its docstring is the
whole claim: *"`core.product_filters.ProductFilters` is not
`adcp.types.ProductFilters` (the public name is the canonical model), so --auto-apply
must not lift it."* Measured here:

```
adcp.types.domains.core.product_filters.ProductFilters is adcp.types.ProductFilters  → True
adcp.types.ProductFilters is adcp.types.LegacyProductFilters                         → True
```

`core/product_filters.json` is one document, so there is one class and three
spellings of it. `--auto-apply` lifting the import to `from adcp.types import
ProductFilters` is correct, not a wrong guess, and the test asserted the collision it
was written to prevent.

### `tests/test_reporting_capability_models.py` — (a), 15 items

Commit `36b970c67`.

The `graph` fixture's `"bundled"` param imported
`adcp.types.domains.bundled.protocol.get_adcp_capabilities_response` to grade
codegen's self-contained per-message clone as a second graph — 14 items across four
tests, all collection ERRORS. `adcp.types.domains` here is the compat mirror of
`adcp.types._schemas` (one prefix substitution read off `__name__`, no files of its
own) and no `bundled` counterpart exists under either name. The fixture keeps its
public pair and stops being parametrized, so surviving IDs lose their `public-` prefix.

`test_post_generation_repair_is_idempotent_for_both_actual_model_layouts` copied
`domains/bundled/protocol/get_adcp_capabilities_response.py` out of the source tree.
Its other target, `domains/core/reporting_delivery_capabilities.py`, is not a file
here either — the mirror has no real directory — so there was no non-bundled half of
"both layouts" left to keep. `importlib`, `shutil` and `Path` went with it.

### `tests/test_targeting_overlay_errors.py` — (c), 1 function / 2 items

Commit `ccc286d2b`. `test_native_json_requests_preserve_repeated_key_diagnostics`,
named by the owner. Its payload is
`{"unexpected": "first", "unexpected": "last"}` — the same key twice in one object —
and it then required our nested errors to equal, row for row, what a standalone
`TypeAdapter` produces for the same bytes. Which value wins is implementation-defined
and the payload is malformed by construction.

The honest coverage it reached for survives: the raw-JSON parents still retain their
bytes, and `test_errors_match_input_schema_including_nested_unions_and_context`
compares the complete raw diagnostics across nine overlays, both modes and all five
paths — on well-formed payloads.

---

## Left RED — 110 items, none matching (a)/(b)/(c)

### The real open defect the owner named: error ORDER, 4 items

`tests/test_targeting_overlay_errors.py`:
`test_errors_match_input_schema_including_nested_unions_and_context[missing-extra-order-json-{create,buy}]`
and `test_error_order_controls_primary_field_and_message[json-{create,buy}]`.

Payload `{"keyword_targets": [{"unexpected": "<secret>"}]}` — one key, no duplication.
The first error sets `Error.field` on the wire, and our union path reorders extras
after missings, so the wire reports

```
field   purchases.0.targeting_overlay.keyword_targets.0.keyword   (type missing)
```

where the standalone adapter puts `...keyword_targets.0.unexpected`
(`extra_forbidden`) first. It is narrow: of the 10 items of
`test_error_order_controls_primary_field_and_message`, 8 pass — all five paths in
python mode, and `update` / `update-new` / `control` in json mode too. Only `create`
and `buy` in json mode reorder. **This is a real open defect, not a duplicate-key
artefact**, and is deliberately left graded.

### One cause, 53 items: the generated tree is at `_schemas`, and `domains` is a mirror

`tests/test_legacy_surface_names_every_arm.py` — **0 removed, 53 red.** The file's
`_CANONICAL_ROOT = "adcp.types.domains"`, and every class honestly reports
`adcp.types._schemas.<domain>.<document>` as its `__module__`, because the mirror binds
the private module rather than re-executing it.

* `test_a_legacy_name_is_the_generated_class_not_a_subclass_of_it` — 51 params. Probed
  with the root read as `adcp.types._schemas`: **51 of 51 pass** — 0 declared outside
  the generated tree, 0 round-trip failures (`getattr(module, qualname) is value`), 0
  same-named shadows. The obligation holds; the path spelling it is stated in does not.
* `test_the_derived_sets_are_not_empty` — `len(ARMS) > 12` got 0. `ARMS` comes from
  `Path(adcp.types.domains.__file__).parent.rglob("*_response.py")`, and the mirror
  directory holds one file, its own `__init__.py`. The `LEGACY_NAMES > 40` and
  `LEGACY_CLASSES > 35` halves of the same test pass (51 and 51).
* Consequence worth naming: `test_every_arm_of_a_response_on_the_legacy_surface_is_publicly_nameable`
  is the 1 SKIP in the counts — an empty parametrization. That silent skip is exactly
  what `test_the_derived_sets_are_not_empty` exists to make loud, and it is doing its
  job.
* `test_the_format_reference_is_reachable_under_a_public_name` — **kept deliberately
  under ground (b)'s carve-out.** It is a test that the alias RESOLVES, and it does:
  `core/format_id.FormatReferenceStructuredObject` is reachable at four public
  spellings here, `['FormatId', 'FormatReferenceStructuredObject', 'LegacyFormatId',
  'LegacyFormatReferenceStructuredObject']`, against an expected exact list of the two
  `Legacy*` ones. The failure is surface BREADTH, not a demanded divergence. If the
  owner reads "only the `Legacy*` spelling may resolve" as itself a ground-(b)
  divergence demand, this one item goes; it was not deleted on my reading.

### `tests/test_asset_aliases_stable.py` — 0 removed, 19 red

* `test_content_type_resolves_to_generated_payload_class` (9) — same single cause as
  above: expects `__module__ == "adcp.types.domains.core.assets.<x>_asset"`, gets
  `adcp.types._schemas.core.assets.<x>_asset`. The alias resolution itself holds.
* `test_format_category_module_raises_migration_pointer` (1) — expects
  `ImportError` matching `MIGRATION_v3_to_v4`; gets a bare
  `ModuleNotFoundError: No module named 'adcp.types.domains.enums.format_category'`.
  `ModuleNotFoundError` IS an `ImportError`, so it is the guided MESSAGE that is
  missing: the mirror returns `None` from `find_spec` for a name with no private
  counterpart, and nothing on the way raises the pointer.
* `test_legacy_asset_names_not_on_public_surface` (9) — **a judgement call, recorded
  rather than acted on.** It requires the pre-4.0 `<Type>Asset` names to be absent
  from `adcp.types`. Measured, all nine resolve AND each is the same object as its
  canonical twin:

  ```
  AudioAsset is AudioContent → True        (adcp.types._schemas.core.assets.audio_asset.AudioAsset)
  ... 9 of 9, all True, all in adcp.types.__all__
  ```

  So this is structurally ground (b) — a legacy spelling required to behave
  differently from its canonical twin where one document makes one class. It was NOT
  deleted, because the owner's ground names a `Legacy*` name and `AudioAsset` does not
  carry that prefix, and because the subject it grades is a 4.0 REMOVAL that
  `test_renames_all_nine_asset_content_types` (passing, same scope) still treats as
  live. **If the owner intends (b) to cover legacy spellings without the `Legacy*`
  prefix, these 9 go and the decision is one line.**

### `tests/test_lazy_types.py` — 7 red

| item | measured cause |
|---|---|
| `test_schema_symbol_triggers_build` | `from adcp import Product` does not put `adcp.types._generated` in `sys.modules`. `_generated` EXISTS here (it is not a deleted layer) but the lazy facade reaches a class through `compat` / `_adapter` / `_restored` / `_surface._flat`, not through it. |
| `test_partial_modules_never_import_generated_layer[seller]` | `src/adcp/types/seller.py` does not exist — `FileNotFoundError` on the `ast.parse`. The other five params pass. |
| `test_partial_modules_avoid_numbered_codegen_names[seller]` | same absence: `No module named 'adcp.types.seller'`. |
| `test_partial_modules_are_in_types_all` | the six partial-module NAMES (`media_buy`, ...) are not members of `adcp.types.__all__`; that list is the union of the alias/adapter/restored/flat surfaces and carries class names only. |
| `test_partial_module_names_all_resolve_via_adcp_types` | `sorted(dir(module)) == sorted(module.__all__)` — `dir()` carries 9 more entries (`__all__`, `__name__`, the rest of the module dunders). Every name in `__all__` DID resolve to the same object as on `adcp.types`; only the exact-set equality on `dir()` failed. |
| `test_star_import_from_adcp_resolves_all` | `adcp.__all__` advertises `IdentityMatchTmpxMacro`, which no layer binds; `adcp.types.__getattr__` raises its migration `AttributeError`. |
| `test_geopostalarea_deprecation_warns_once_then_caches` | `adcp.types.GeoPostalArea` is not bound at all, so the one-warning-then-cached behaviour has nothing to fire on. The test also wants `PostalArea2` while its own docstring says `PostalArea5` — a pre-existing disagreement inside the test, not caused by this tree. |

### `tests/test_migrate_v3_to_v4.py` — 15 red

Two causes, neither a deleted layer.

**Flat names the codemod's target map wants and this surface does not bind** (10
items). `v3_to_v4._replacement_is_identical` requires
`adcp.types.domains.<module>.<symbol> is adcp.types.<public>`; where `<public>` is
absent or a different object the lift degrades to a bare prefix rename and the hint to
`None`. Measured:

```
CpmVendorPricingOption               absent  (this tree spells it VendorPricingOptionCpm)
PercentOfMediaVendorPricingOption    absent
CoreGovernanceAgent                  absent
ListCreativesSort                    absent
LegacyProductFormatDeclaration       absent
ProductFilterCountry                 absent
GetSignalsSignal                     present, NOT identical to signals.get_signals_response.Signal
PropertyIdentifier                   present, NOT identical to core.property.Identifier
```

Affected: `test_generated_poc_import_hint_covers_every_symbol_on_the_line`,
`test_generated_poc_symbol_map_covers_publicly_exported_names`,
`test_auto_apply_uses_source_scoped_semantic_alias`,
`test_auto_apply_preserves_crlf_after_source_scoped_import`,
`test_auto_apply_rewrites_multi_symbol_all_known_line`, and 6 of the 9
`test_auto_apply_uses_beta5_source_scoped_aliases` params. The other 3 params pass
(`LegacyCreativeAsset`, `LegacyCreativeFilters`,
`LegacyUpdateMediaBuySuccessResponse`).

**The `brand` split does not exist here** (3 items, plus 2 of the above overlap).
`v3_to_v4._split_halves` asks `find_spec("adcp.types.domains.brand_discovery")`;
measured, neither that name nor `adcp.types._schemas.brand_discovery` resolves, so
every `brand` import is treated as a whole-stem move and is renamed where the test
wants it flagged. Affected:
`test_apply_renames_deep_generated_poc_imports_including_the_brand_split`,
`test_import_path_rename_preserves_crlf`,
`test_split_stem_with_an_unknown_name_is_flagged_not_guessed`,
`test_split_stem_sharing_its_line_with_other_code_is_flagged`.

### `tests/test_reporting_capability_models.py` — 12 red

Two causes, both on the public graph.

* **JSON-schema shape** (4 items, `test_core_attributes_...[flags0-3]`):
  `schema["properties"]["receipt_task"]["anyOf"]` → `KeyError`. The nullable promise
  renders as a flat `type` with `"default": None` rather than an `anyOf` carrying a
  `{"type": "null"}` arm. Every assertion ABOVE it passes — `field.default is None`,
  `NoneType in get_args(annotation)`, `getattr(value, name) is None`,
  `schema[...]["default"] is None` — so the promise is nullable, explicit and absent
  from every dump; it is the schema SPELLING of nullability that differs.
* **Validator message wording and conditional requiredness** (8 items): the models
  emit the document's own `required when <tier>` / `required when <tier>=True` at the
  REQUIRED field's own `loc`, where the tests `match=` upstream's prose
  `"<field> requires <tier>"` at the promise's `loc`. Two params
  (`test_each_explicit_...[receipt_task, readiness_notification]`) fail earlier still,
  on `managed_delivery=True` pulling in `resource_retention_days` and
  `authorization_revocation_seconds` as conditionally required — a stricter document
  reading than the fixture builds for. The refusal happens in every case; what differs
  is which field it is reported against and in what words.

---

## Two notes on the gate

**`ruff format` is not this repo's formatter, so `black` was used.** `make format` runs
`black src/ tests/ scripts/`, and `ruff format --check tests/` reports **88 of 801
files would be reformatted** on an unmodified tree — a pre-existing, tree-wide
black-vs-ruff disagreement about implicit string concatenation and assert-message
wrapping. Running it would have rewritten lines no commit here touches. Every file
committed passes `ruff check` and `black --check`.

**One pre-existing `ruff check` error was left alone.**
`tests/test_targeting_overlay_errors.py` carries an `I001` on its import block, present
at `HEAD` before any edit here; ruff's own fix moves
`from adcp.types.domains.core.targeting_input import TargetingOverlayInput` up into the
third-party group, which is wrong, so it was not applied.
