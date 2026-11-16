# Findings — 86 tests that asked for a name this emission does not bind flat

Each section names what was asked for, what the document states instead, and where
the repair lands. The three groups that are **left red** are left red because the
repair is in `src/`, `survey/` or `examples/`, all outside this task's write scope.

The baseline is `test-results/before.json`, taken on this worktree's tree at
`3e09d6c70` in a sibling checkout: **failed=496, error=5, passed=14565,
total=17893** — the trunk numbers `TASK.md` states.

---

## Left red — the repair is in `src/`, and it is one attribute

### `declaration.legacy_format_refs` — 23 failures across 6 files

**The emission is right and the SDK's own code is reading a name the document does
not state.** `core/product-format-declaration.json` states the v2 → v1 link as
**`v1_format_ref`**, and every emitted declaration branch carries it under exactly
that name:

```
ImageFormatDeclaration.model_fields -> [..., 'v1_format_ref']
SchemaRef(document='core/product-format-declaration.json', pointer='#/oneOf/0')
```

`legacy_format_refs` was the previous generator's spelling of it. `src/` reads the
old name at **eight** sites, and every one of them raises
`AttributeError: 'ImageFormatDeclaration' object has no attribute
'legacy_format_refs'` the moment a declaration reaches it:

| file | line | expression |
| --- | --- | --- |
| `src/adcp/canonical_formats/projection.py` | 787 | `if declaration.legacy_format_refs:` |
| `src/adcp/canonical_formats/projection.py` | 788 | `return list(declaration.legacy_format_refs)` |
| `src/adcp/canonical_formats/projection.py` | 836 | `for ref in declaration.legacy_format_refs` |
| `src/adcp/canonical_formats/v2_to_v1.py` | 158 | `refs = list(declaration.legacy_format_refs)` |
| `src/adcp/canonical_formats/v1_to_v2.py` | 495 | `refs = declaration.legacy_format_refs` |
| `src/adcp/canonical_formats/format_options.py` | 185 | `refs = decl.legacy_format_refs` |
| `src/adcp/client.py` | 2103 | `getattr(declaration, "legacy_format_refs", ())` |

The prose in those same files already says `v1_format_ref` — `v2_to_v1.py`'s module
docstring is written entirely in terms of ``v1_format_ref[]`` — so the divergence is
between that file's comments and its code.

**The repair is one of two, and it is the owner's call:**

1. **Rename the eight reads to `v1_format_ref`.** This is what the document says and
   what the file's own prose already says. `client.py:2103`'s `getattr(..., ())`
   silently returns `()` today, so that site is currently *wrong without raising* —
   it reports "no v1 link" for a declaration that has one.
2. **Bind `legacy_format_refs` as a populate-by-name alias** on the sixteen
   declaration branches. This keeps upstream's ergonomic spelling, at the cost of a
   second name for one field.

Nothing in `src/adcp/types/` provides the old name today: `grep -rn
"legacy_format_refs" src/adcp/types/` is empty, and there is no `_ergonomic.py` or
`_forward_compat.py` in this emission to patch it in.

The 23 failures, by file:

| file | failures | the frame that raises |
| --- | --- | --- |
| `tests/test_mixed_legacy_projection_regression.py` | 19 | `projection.py:836` in `declaration_fingerprint` |
| `tests/test_seller_agent_dual_emit.py` | 1 | `v2_to_v1.py:158` in `project_declaration_to_v1` |
| `tests/test_seller_agent_storyboard.py` | 1 | `projection.py:787` in `resolve_legacy_format_refs` |
| `tests/test_server_builder.py` | 1 | `projection.py:787` |
| `tests/test_version_client_boundaries.py` | 1 | `projection.py:787` |

`tests/test_typescript_rc3_corpus.py` was the ONE of the six where the read was in
the test rather than in `src/`, and it is repaired: it now reads
`declaration.v1_format_ref` and asserts the fixture's refs survive the Product
boundary verbatim.

That repair also corrected the test's other half. It asserted
`not _legacy_identity_paths(dumped)` over a set that included `v1_format_ref` and
`agent_url` — i.e. that a canonical product carries NO v1 link on the wire. The
document states `v1_format_ref` as the seller's own authoritative link, so
suppressing it would make the class narrower than its document. The helper now
flags only a **synthesized** `format_id`/`format_ids`, which is the thing
`registries/v1-canonical-mapping.json` forbids ("v2 → v1 projection MUST rely on
`v1_format_ref`"), and the test additionally asserts the dumped refs equal the
fixture's.

### `registration.operation_id` — 2 failures in one file

Same shape, different field. `core/reporting-webhook.json` in bundle 3.2 states five
properties — `url, token, authentication, reporting_frequency, requested_metrics` —
and `operation_id` is **not** one of them; it rides as an extra under the document's
own `additionalProperties: true`. `src/adcp/webhooks.py:378` reads it as an
attribute:

```python
if not webhook.operation_id:          # AttributeError when the key was not supplied
```

reached from `src/adcp/webhook_sender.py:851` (`prepare_media_buy_delivery`) and
`:813` (`send_media_buy_delivery`).

**The repair is `getattr(webhook, "operation_id", None)`** — or
`webhook.model_extra.get("operation_id")`, which is the same answer and says why.
The function's intent is unchanged: a registration without the key is suppressed and
flagged, never given a minted ID.

Failing: `test_scheduled_sends_skip_and_flag_registrations_without_operation_id`,
`test_typed_registration_without_operation_id_is_refused`.

The other 9 failures in that file were in the test and are repaired — see below.

### `adcp.types._adapter`'s census — 3 failures in `tests/test_public_words_resolve.py`

These three are **gates reporting a real inconsistency**, and their own messages say
where the repair is: *"`_adapter.py` is generated by `survey/adapter_surface.py`, so
neither group is fixed by editing it"* and *"Re-derive the census against the tree as
it is."* Both files are outside this write scope. Measured:

* `test_every_declared_refusal_cites_a_location_that_exists` — eight refusals cite a
  module that no longer imports: seven cite `adcp.types.canonical_creative`
  (`Format`, `UpdateMediaBuyResponse1`, `UpdateMediaBuyResponse3`,
  `UpdateMediaBuySuccessResponse`, `is_canonical_format_kind`,
  `require_canonical_format_kind`) and `adcp.types.validation` (`validate_union`);
  one is `adcp.types.buyer.__adcp_refused__['BrandIdentity']`, citing
  `adcp.types.domains.brand_discovery.Brand` — the mirror path is
  `adcp.types.domains.brand`, and the class is `adcp.types.brand.BrandDiscoveryBrand`.
* `test_the_refusal_table_and_the_public_surface_agree` — words that are both bound
  and refused (`AcceptProposalResponse`, the `VerifyBrandClaims*` family, `aliases`).
* `test_our_own_source_does_not_import_a_word_the_package_refuses` — our own source
  imports refused words at `src/adcp/decisioning/types.py:47` (`CreditLimit`),
  `src/adcp/types/legacy_names.py:3410/3411/3443/3450/3554`,
  `src/adcp/compat/versions.py:394`, `src/adcp/types/_adapter.py:394/395`,
  `src/adcp/types/projections.py:36`.

### `examples/v3_reference_seller/src/platform.py:139` — 1 failure

`tests/test_validate_platform_warnings.py::test_v3_reference_seller_passes_with_no_warnings`
fails at `ImportError: cannot import name 'LegacyFormat' from 'adcp.types.legacy'`.

**The name exists** — `adcp.types.core.LegacyFormat`, from `core/format.json#`,
exactly as `CLAUDE.md`'s Formats section states. The example imports it from
`adcp.types.legacy`, which publishes `LegacyFormatId`,
`LegacyListCreativeFormatsRequest` and `LegacyListCreativeFormatsResponse` but not
this one. The repair is one import line in `examples/`, outside this write scope.

### Not of the named class — `tests/conformance/reporting/test_reporting_notification_packaging.py`

`TASK.md` lists 4 failures here. Measured against `before.json`, none of the four is
an `ImportError`, `ModuleNotFoundError` or `has no attribute`: all four are
`AssertionError: notification distribution base-import-without-pg: exit 1 ... stderr
{"trace":[[33,["module_missing"]]],"classification":"recognized"}` — a built wheel
and sdist that fail to import a module. The same import list runs clean from a source
checkout, so this is a packaging question (`[tool.setuptools.package-data]` in
`pyproject.toml`) and not a test asking for a name. It is left untouched.

---

## Repaired — what each name resolved to

### `GeoPostalArea` → `adcp.types.core.PostalAreaWithFusedSystem` (14)

`tests/test_postal_area_compat.py`. `core/postal-area.json#/anyOf/1` is the legacy
country-fused branch — `{system, values}`, fields measured — and the surface names
it from that position. All eleven fused tokens construct, the branch survives the
`PostalArea` union with no injected `country`, and `TargetingOverlay` accepts it.
There is no deprecating-alias layer in this emission, so the
`warnings.catch_warnings` helper that suppressed a `DeprecationWarning` went with
the word; it asserted nothing.

### `ReportingWebhook.operation_id` → an EXTRA, not a field (9 of 11)

`tests/test_reporting_webhook_operation_id.py`. The document states five properties
and `additionalProperties: true`. So:

* the key is read off `model_extra`, and is absent when it was not supplied;
* an explicit `None` is a *supplied* extra and rides the wire as `null` — the
  `None`-is-absence rule governs a property the document STATES, and this is not one;
* a JSON null is **not** refused, because there is no field to refuse at; the test
  now grades the refusal where it does exist, on `PushNotificationConfig`, whose
  document states `operation_id` with the 1–255 `[A-Za-z0-9_.:-]` form;
* the parity test became an asymmetry test: one of the two registration documents
  states the key, and only one.

### Scalar roots are aliases, not subclasses (8)

`tests/test_scalar_roots.py` (4 named + 4 siblings of one subject),
`tests/test_backward_compat.py`, `tests/test_decisioning_capabilities_submodule.py`,
`tests/test_reporting_reconciliation.py`, the two conformance reconciliation suites,
`tests/test_authorized_agents_public_surface.py`.

`rebuild-plan.md` §4: *a scalar at a root* emits *"a module-level annotated alias,
not a class"*. `PropertyTag` IS `Annotated[str, ...]`, so:

* there is no constructor to refuse at, and no `ViewThreshold`/`MajorVersion` class —
  the 0..1 number branch of `pricing-options/cpv-option.json`'s `view_threshold` is
  `adcp.types.constraints.FloatMin0Max1`, and the bounds are graded at a field;
* `instance.root` reads nothing: a property id, a native version ref, a rejection
  code and a major version are each their own `str`/`int`;
* the three `RootModel` back-compat shims (`X(root=...)`, `X.root`, the "not both"
  conflict) have no class to live on and are removed;
* `TypeAdapter(PropertyTag).json_schema()` carries `type`, `pattern` and
  `description` but not `title` or `examples`, and §5's grid is why: `title` ROOT →
  *"the symbol ... Never rendered"*, `examples` → *"Nothing on the model. The accepts
  check replays every one."*

### `Status` is DECLINED, not resolved (2)

`tests/test_backward_compat.py`. Three domains publish a `Status`, and
`adcp.types._surface._flat` declines the flat word rather than picking a winner —
its own docstring: *"picking one would hand a consumer a class whose document they
did not name."* The decline is recorded with its three candidates, which the test now
reads; the subject the old alias meant is graded at its own path,
`adcp.types.media_buy.MediaBuyDeliveryWebhookResultMediaBuyDeliveriesItemStatus`.

### `BrandIdentity` has one path, and it is not `adcp.types.buyer` (1)

`brand.json#/definitions/brand` → `adcp.types.brand.BrandDiscoveryBrand`, with
`adcp.types.BrandIdentity` and `adcp.types.domains.brand.Brand` the same object.

### Modules that left with the previous generator (6)

| asked for | verdict |
| --- | --- |
| `scripts.post_generate_fixes` | removed in `639134c75`. What its `_CANCELED_FIELD_RE` widened is now the walk's own output; the test reads the document (`canceled` is an optional `const: true`) and the emitted annotation instead. |
| `scripts/generate_versioned_bases.py` | removed in `639134c75` with `adcp/types/versioned_bases/`. `tests/test_versioned_bases_codegen.py` deleted — its only subject was that generator. |
| `adcp.types.response_dispatch` | removed in `639134c75`, *"the seam their behavioural code reaches types through"*. Two private pydantic-kwargs helpers; deleted. |
| `adcp.types.seller` | names no module here and none upstream either. Dropped from `PARTIAL_MODULES`. |
| `adcp.types.generated_poc` | the previous mirror. `adcp.types.domains` is this emission's, and registers the same module object under a second `sys.modules` key — the exact shape #1619's lazy-export walk had to survive — so the regression is re-pointed at it, not deleted. |
| `adcp.types.canonical_creative` | `CreateMediaBuyResponse3` is `media-buy/create-media-buy-response.json#/oneOf/2`, named `CreateMediaBuyResponseSubmitted` from its own title. |

### Names the walk derives differently (6)

| asked for | the branch's own name | derived from |
| --- | --- | --- |
| `ComplyListScenariosResponse` | `adcp.types.compliance.ListScenariosSuccess` | `#/oneOf/0`'s `title` |
| `LegacyBuildCreativeResponse6` | `adcp.types.media_buy.BuildCreativeResponseSubmitted` | `#/oneOf/5`'s `title` |
| `AuthorizedAgents` | `…AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds` | the declaring position |
| `TotalBudget` | the field's own type, `#/definitions/money` | one class per SUBJECT (§4) |
| `CanonicalParameters` | nothing — `core/format.json` contributes no root model. The deferred-rebuild test now names two roots that are composing roots. | |
| `GetProductsResponseUnion` / `GetSignalsResponseUnion` | nothing — each async response is its OWN document root and no node states a `oneOf` over them. The tests grade which documents each tool ships. | |

### Two shapes that are not what they were (3)

* **`ContextObject` is a `dict`, not a model.** `core/context.json` is
  `{"type": "object", "additionalProperties": true}` with no stated properties, so
  it compiles to an alias and has no `model_validate`. The #1575 contract — a null
  INSIDE the opaque context survives every dump path — is graded on the response that
  carries it, plus the alias module's own `strict_validate`.
* **`reporting_delivery` has one class, not a bundled/canonical pair.**
  `MediaBuy.__bases__[0]` is `AdCPBaseModel`, which states no such field.
  `core/reporting-delivery-capabilities.json` requires six properties (two of them
  `const`) and gives `managed_delivery`, `reconciled_billing` and
  `supports_webhook_activity` a `default: false`. A default is a value, not a `None`,
  so the dump keeps it whether or not the caller supplied it — `model_fields_set` is
  what still tells supplied from defaulted, and the test asserts both.

---

## Owed, outside this scope

Two tests in `tests/test_scalar_roots.py` now pass **vacuously** and say so nowhere:
`test_no_scalar_rootmodels_remain_in_generated_tree` walks
`src/adcp/types/domains/`, which is a `sys.meta_path` mirror with no files on disk,
and `test_every_scalar_root_example_round_trips` ranges over
`_generated_scalar_roots()`, which is empty because no generated class subclasses
`ScalarStr`/`ScalarInt`/`ScalarFloat` any more. Both are green for the wrong reason.
Re-pointing the first at `src/adcp/types/_schemas/` and the second at the alias
population is a wider repair than the named failure class, and `src/adcp/types/_scalar.py`
itself is now reachable by nothing the walk emits.
