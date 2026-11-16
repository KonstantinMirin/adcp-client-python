# The 27 names `adcp.__all__` promised and nothing bound

**The measurement, taken first and taken again.**

```
.venv/bin/python -c "import adcp; m=[n for n in adcp.__all__ if not hasattr(adcp,n)]; print(len(adcp.__all__), len(m))"
before   748 27
after    745  0
```

**24 BIND, 3 DROP, 0 for the owner.** Every one of the 27 was decided by the pointer its
subject carries, never by the spelling, and the ground is below. `./check` is unmoved at
`emitted 1059 / refused 0`, which is the gate on not having touched the compiler.

---

## 1. The 27 decisions

Option per `docs/plan/rebuild-plan.md` §4 and `CLAUDE.md`'s `Format` / `LegacyFormat`
worked example. **BIND** = one emitted class (or, where the walk emits no union root, our
own field annotation restated) is unambiguously the subject, bound in
`src/adcp/types/aliases.py`. **DROP** = no node of the pinned bundle states the subject,
so the promise leaves `adcp/__init__.py` and the import BREAKS rather than redirecting.

| # | name | option | document | pointer | bound to |
|---|---|---|---|---|---|
| 1 | `AcceptedLoss` | BIND | `media-buy/legacy-purchase-continuation-input.json` | `#/properties/accepted_losses/items` | `adcp.types.media_buy.RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem` |
| 2 | `PrincipalReadResult` | BIND | `protocol/get-principal-response.json` | `#/properties/result` (`oneOf/0..3`) | union: `CurrentPrincipalConfiguration \| RecognizedPrincipalWithoutStandingConfiguration \| UnconfiguredPrincipal \| FailedPrincipalRead` |
| 3 | `PrincipalSyncResult` | BIND | `protocol/sync-principal-response.json` | `#/properties/result` (`oneOf/0..2`) | union: `AppliedPrincipalConfiguration \| ValidatedPrincipalDryRun \| FailedPrincipalSync` |
| 4 | `VerifyBrandClaimsPayload` | BIND | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response/allOf/1/properties/payload` | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload` |
| 5 | `VerifyBrandClaimsSignedResponse` | BIND | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response` | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponse` |
| 6 | `LegacyProductFormatDeclaration` | BIND | `core/product-format-declaration.json` | `#` | `adcp.types.core.ProductFormatDeclaration` |
| 7 | `AssetInstance` | BIND | `core/assets/asset-union.json` | `#` | `adcp.types.core.AssetVariant` |
| 8 | `AssetInstanceType` | **DROP** | — no node | — | — |
| 9 | `BrandIdentity` | BIND | `brand.json` | `#/definitions/brand` | `adcp.types.brand.BrandDiscoveryBrand` |
| 10 | `MediaBuyPackage` | BIND | `media-buy/get-media-buys-response.json` | `#/properties/media_buys/items/properties/packages/items` | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItemPackagesItem` |
| 11 | `Refine` | BIND | `media-buy/get-products-request.json` | `#/properties/refine/items` (`oneOf/0..2`) | union: `ObjScopeAsk \| ObjScopeProductIdActionAsk \| ObjScopeProposalIdActionAsk` |
| 12 | `IdentityMatchTmpxMacro` | **DROP** | `trusted-match/identity-match-response.json` states `tmpx_macros` only at `#/not/anyOf/2` | a PROHIBITION, not a node | — |
| 13 | `ProviderRegistrationTmpxMacro` | **DROP** | `trusted-match/provider-registration.json` | no pointer; `additionalProperties: false` and no such property | — |
| 14 | `AuthorizedAgent` | BIND | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items` (`oneOf/0..5`) | union over rows 15–20 |
| 15 | `AuthorizedAgentsByPropertyId` | BIND | `adagents.json` | `…/authorized_agents/items/oneOf/0` | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds` |
| 16 | `AuthorizedAgentsByPropertyTag` | BIND | `adagents.json` | `…/oneOf/1` | `…AuthorizedAgentsItemPropertyTags` |
| 17 | `AuthorizedAgentsByInlineProperties` | BIND | `adagents.json` | `…/oneOf/2` | `…AuthorizedAgentsItemInlineProperties` |
| 18 | `AuthorizedAgentsByPublisherProperties` | BIND | `adagents.json` | `…/oneOf/3` | `…AuthorizedAgentsItemPublisherProperties` |
| 19 | `AuthorizedAgentsBySignalId` | BIND | `adagents.json` | `…/oneOf/4` | `…AuthorizedAgentsItemSignalIds` |
| 20 | `AuthorizedAgentsBySignalTag` | BIND | `adagents.json` | `…/oneOf/5` | `…AuthorizedAgentsItemSignalTags` |
| 21 | `UrlVastAsset` | BIND | `core/assets/vast-asset.json` | `#/oneOf/0` | `adcp.types.core.VASTAssetUrl` |
| 22 | `InlineVastAsset` | BIND | `core/assets/vast-asset.json` | `#/oneOf/1` | `adcp.types.core.VASTAssetInline` |
| 23 | `UrlDaastAsset` | BIND | `core/assets/daast-asset.json` | `#/oneOf/0` | `adcp.types.core.DAASTAssetUrl` |
| 24 | `InlineDaastAsset` | BIND | `core/assets/daast-asset.json` | `#/oneOf/1` | `adcp.types.core.DAASTAssetInline` |
| 25 | `SyncAudiencesAudience` | BIND | `media-buy/sync-audiences-request.json` | `#/properties/audiences/items` | `adcp.types.media_buy.SyncAudiencesRequestAudiencesItem` |
| 26 | `SyncCatalogResult` | BIND | `media-buy/sync-catalogs-response.json` | `#/oneOf/0/properties/catalogs/items` | `adcp.types.media_buy.SyncCatalogsSuccessCatalogsItem` |
| 27 | `SyncCreativeResult` | BIND | `creative/sync-creatives-response.json` | `#/oneOf/0/properties/creatives/items` | `adcp.types.creative.SyncCreativesSuccessCreativesItem` |

---

## 2. The three DROPs, each with what was measured

### `IdentityMatchTmpxMacro` — the only node that mentions the key FORBIDS it

`tmpx_macros` occurs in exactly two documents of the pinned bundle, and in both it occurs
inside a `not`:

```
trusted-match/identity-match-response.json#/not/anyOf/2  ->  {"required": ["tmpx_macros"]}
trusted-match/provider-identity-match-response.json      ->  the same clause
```

A `not/anyOf` branch asserting `required` is a PROHIBITION. There is no node at that
position for a class to be emitted from, so no class can be bound and none should be
invented. §4 step 4 would make this *pending a name*, except that there is no subject
pending either — the document says the field may not be present.

The two replacements, for a migration note: the chunk VALUE is
`adcp.types.trusted_match.TMPXChunk.value` (`trusted-match/tmpx-chunk.json#/properties/value`),
and the ad-server macro NAME is publisher-local deployment config
(`trusted-match/publisher-tmpx-config.json`'s `tmpx_macro_mapping`) that never travels the
wire.

### `ProviderRegistrationTmpxMacro` — the document positively refuses the key

`trusted-match/provider-registration.json` has no `tmpx_macros` property and the root
carries `additionalProperties: false`. What a provider registers is `tmpx_slots` —
"provider-local slot identifiers … **NOT ad-server macro names**", the document's own
words. So the name asks for a subject 3.2 split in two and assigned to neither this
document nor the wire.

### `AssetInstanceType` — the vocabulary exists, a node stating it does not

Upstream's symbol was `Literal['image', 'video', …, 'daast_tracker']`, 20 values. In the
pinned bundle that vocabulary exists only as **one `const` per branch** of
`core/assets/asset-union.json#/oneOf/{0..20}` — 21 of them, one wider than upstream's 20
(`#/oneOf/4` is `display_tag`, which upstream's hand-written union omitted). No node states
the set, so:

* there is no emitted class to re-export, and a search of every enumeration our walk emits
  finds none whose value set equals those 20. The two nearest are
  `adcp.types.formats.CanonicalFormatBaseSlotsItemAssetType` and
  `…CoordinatedPlacementsSharedSlotsItemAssetType`, both proper SUPERSETS including
  `object` — the format-SLOT declaration vocabulary, a different subject;
* writing `AssetInstanceType: TypeAlias = Literal[…]` into the alias layer would declare a
  **second type**, which that module's own rule ("an alias is a name and never a second
  type") forbids, and would be the compiler minting a subject from 21 separate statements.

The discriminator a narrowing adopter actually wants is each branch's own `asset_type`
field, whose `Literal` the branch class carries —
`tests/type_checks/asset_instance_narrowing.py` now pins exactly that.

---

## 3. The BINDs that needed more than a lookup

### `LegacyProductFormatDeclaration` — "Legacy" is upstream's MODULE, not v1 addressing

This is the one with a real risk of the failure `CLAUDE.md` names: *a public word that
changes meaning while staying importable*. It does not happen here, and the reason is
upstream's own chain:

```
upstream legacy.py:153   LegacyProductFormatDeclaration = LegacyGeneratedProductFormatDeclaration
upstream legacy.py:22    from adcp.types.domains.core.product_format_declaration
                             import ProductFormatDeclaration as LegacyGeneratedProductFormatDeclaration
```

So upstream's word already meant `core/product-format-declaration.json#` — the **v2
canonical** declaration. The `Legacy` prefix in that file distinguishes the GENERATED class
from the hand-written subclass that used to shadow it, which is a fact about upstream's
module layout and not about v1 format addressing. Binding it to
`adcp.types.core.ProductFormatDeclaration` therefore preserves the meaning; nothing
redirects from v1 to v2. The v1 named-format definition keeps its own separate word,
`adcp.types.core.LegacyFormat` (`core/format.json#`), exactly as `CLAUDE.md` states.

### `BrandIdentity` — the survey said "document we do not compile" and we do compile it

`survey/adapter-surface-9.6.1.tsv:51` records `DOCUMENT-WE-DO-NOT-COMPILE`, citing
upstream's `adcp.types.domains.brand_discovery.Brand`. That reading is now wrong. There is
no `brand-discovery.json` in the bundle because the document is **`brand.json`**, whose own
`title` is "Brand Discovery"; we compile it to `adcp.types._schemas.brand` and export
`#/definitions/brand` as `adcp.types.brand.BrandDiscoveryBrand`. Measured, the field sets
are identical member for member — 29 names, `agents … voice_synthesis` — against upstream's
class. Same subject, so BIND.

### `AcceptedLoss` — an enumeration, catalogued away from its stating position

`#/properties/accepted_losses/items` is a `string` + `enum` of three values, not an object.
Per §3a the catalogue's home for it is `media-buy/request-proposals-response.json`, which is
why the public spelling reads `RequestProposals…LossesItem`; the object is the same
`StrEnum` the `CompatibilityPurchaseCoordinatorInput.accepted_losses` annotation names, and
it carries no `__adcp_schema__` because only model classes do.

### The four unions the walk emits no root for

`PrincipalReadResult`, `PrincipalSyncResult`, `Refine` and `AuthorizedAgent` are positions
where the document states a `oneOf` and our walk emits the branches but no root class. Each
is bound as the **bare union our own field annotation already carries at that position**,
measured branch for branch and in the document's own `oneOf` order:

```
GetPrincipalResponse.model_fields['result'].annotation      == PrincipalReadResult
SyncPrincipalResponse.model_fields['result'].annotation     == PrincipalSyncResult
GetProductsRequest.model_fields['refine'].annotation        == list[Refine] | None
```

No discriminator keyword is re-attached even where upstream's expression pinned one
(`Refine` was `Annotated[…, Field(discriminator='scope')]`): `Annotated[…, Field(…)]` is a
validator, i.e. the second TYPE the alias module forbids. The branches dispatch on their own
`const`s.

### `AuthorizedAgent` — ONE WORD, TWO SUBJECTS ON THE SURFACE. A QUESTION FOR THE OWNER

This is the only row I bound with a reservation, and the reservation is not about the
pointer — it is about the word being taken twice:

| spelling | object | subject |
|---|---|---|
| `adcp.AuthorizedAgent` (this change) | the 6-branch union | `adagents.json#/oneOf/1/properties/authorized_agents/items` |
| `adcp.types.AuthorizedAgent` (pre-existing) | `adcp.types.registry.AuthorizedAgent` | the restored registry model — **no bundle document** |

`src/adcp/types/legacy_names.py:3443` binds the registry class flat and lists it in that
module's `__all__`, so `adcp.types.AuthorizedAgent` resolves to it today, independently of
anything here. I bound `adcp`'s word to the union because that is what upstream's word
meant (`_eager.py:567`, `from adcp.types.aliases import AuthorizedAgent`), and repointing it
at the registry class would be precisely the meaning-change-while-importable that §4 calls
the worst outcome. But the result is two subjects under one word on one public surface,
which §1 forbids, and **neither half of it is mine to settle**: `legacy_names.py` is
generated and the registry model is restored machinery. Flagged rather than decided.

---

## 4. The tests, and which of the two kinds each was

The standing instruction: a test whose point is the previous generator's surface is
REMOVED; a test that imports the name incidentally gets its import repointed.

| file | what was done | which kind |
|---|---|---|
| `tests/test_literal_discriminator_defaults.py` | **class `TestUpstreamsArmNamesHaveNoSubject` deleted** (4 parametrised cases) | *previous generator's surface.* Its whole body was `pytest.raises(AttributeError, match="no subject in the pinned bundle")` over the four VAST/DAAST words. The refusal it pinned is the one this measurement overturned — all four pointers are emitted — so the test asserted a verdict that is false. Nothing else in the class. |
| `tests/test_public_api.py::test_a_media_buys_package_is_named_by_the_document_that_declares_it` | refusal assertions removed, `adcp.MediaBuyPackage is <the pointer's class>` put in their place; docstring restated | *incidental.* The test's real half — that the class at `…/packages/items` carries that document and pointer — is our own naming rule and nothing else grades it. Only the two lines encoding the overturned refusal (`"MediaBuyPackage" in __adcp_refused__`, `not hasattr(adcp, …)`) went. |
| `tests/test_public_api.py::test_vast_and_daast_delivery_branches_are_named_by_their_documents` | same treatment | *incidental.* Keeps the root/branch pointer and `issubclass` assertions; drops the four `in __adcp_refused__` lines. |
| `tests/type_checks/asset_instance_narrowing.py` | rewritten | *both.* `AssetInstanceType` is DROPPED, so the `accepts_discriminator` function went with it. The narrowing half was ALSO the previous generator's shape: it narrowed by the asset document's own class (`ImageContent`), which worked against upstream's flat union of 20 asset roots and narrows nothing against a dispatch root. Repointed at the branch classes (`AssetVariantImage`), where union membership and the asset document's fields meet. The file now passes `mypy --strict` clean; it was 10 errors before. |

`tests/test_public_words_resolve.py` mentions `AcceptedLoss` and `SyncCreativeResult` in
prose only and was left alone.

Whole-suite effect of the test edits, measured:

```
mypy --strict tests/type_checks/     335 errors / 31 files  ->  323 / 30
ruff check src/                      310 errors             ->  308
```

---

## 5. What I could not do inside the write scope

### (a) The task's premise about collection errors is not what the suite reports

TASK says the 27 "block **31** test files from COLLECTING". Measured, before any change,
**2** of the 31 collection errors were caused by one of the 27 — `test_discriminated_unions.py`
and `test_type_aliases.py`, both `ImportError: cannot import name 'InlineDaastAsset' from
'adcp'`. The other 29 have 25 distinct unrelated causes. After this change **none** of the
31 names any of the 27, and the count is still 31 because those two files now stop on the
next missing word:

```
test_discriminated_unions.py   ImportError: cannot import name 'AuthorizedAgents' from 'adcp.types._generated'
test_type_aliases.py           ModuleNotFoundError: No module named 'adcp.types.canonical_creative'
```

The remaining causes, by frequency: `adcp.types.canonical_creative` absent (6),
`LegacyFormat` absent from `adcp.types.legacy` (3), `scripts/sync_schemas.py` absent (2),
a `ReportingRevision` validation failure (1), and one each of `scripts.generate_types`,
`scripts.post_generate_fixes`, `adcp.types.domains.bundled`,
`adcp.types._generated_poc_alias`, `adcp.types.domains.DOMAINS`, and eleven single missing
words (`CreditLimit`, `BadgeRole`, `v31`, `is_canonical_format_kind`, `PublisherDomain`,
`RefineProposalsResponse1`, `FormatAssetUnion`, `coerce_legacy_asset`,
`CpmVendorPricingOption`, `SyncAccountsAccount`, `is_adcp_error`,
`VendorPricingOptionUnion`). Every one needs a file outside this task's write scope.
**So the "0 collection errors" gate cannot be met by deciding these 27 names, and it is not
met.** The gate that belongs to this task — no collection error naming one of the 27 — is.

### (b) `adcp.types.SyncCreativeResult` — one flat spelling our own code imports and the alias layer cannot serve

`adcp.types.__getattr__` resolves through `compat`, `_adapter`, `_restored`, `_surface._flat`
and `legacy_names`. **It does not consult `adcp.types.aliases`.** So this change makes
`from adcp import <name>` work for all 24, and `from adcp.types import <name>` still raises
for them. That matters at exactly one site, which
`tests/test_public_words_resolve.py::test_every_word_our_source_imports_from_adcp_types_resolves_or_is_declared`
now reports:

```
adcp.types.SyncCreativeResult        imported at: src/adcp/server/_creative_batch.py:31
```

That test passed before this change **only because the word was declared refused** — and
that test's own docstring calls the state it was in the worst case: *"A function-scope
import of a refused word is the worst case: the package imports, this gate's other checks
pass, and the failure waits for a caller."* The refusal was wrong (the pointer is emitted),
so deleting the row is right and the red is the gate finally telling the truth about a live
latent outage at that line. The one-line repair is a row in a layer `adcp.types` DOES
consult:

```python
# src/adcp/types/compat.py  (or _adapter.py / legacy_names.py — all three are generated)
from adcp.types.creative import SyncCreativesSuccessCreativesItem as SyncCreativeResult
```

`survey/adapter_surface.py` is what derives those files, so the real repair is a
re-derivation of the census, not a hand edit. `SyncAudiencesAudience` is the same shape at
`src/adcp/decisioning/specialisms/audience.py:31` and is not reported only because
`adcp.types._adapter.__adcp_refused__` still carries its row — which, by the same
measurement, is now also stale.

### (c) `_adapter.py`'s twin rows are stale and I may not touch them

`adcp.types._adapter.__adcp_refused__` carries its own rows for several of the 24 now bound
(`MediaBuyPackage`, `SyncAudiencesAudience`, `AssetInstanceType`, `BrandIdentity`,
`VerifyBrandClaims*`, …). Each one is now group (B) of
`test_the_refusal_table_and_the_public_surface_agree` — refused and bound, so the ROW is
what is wrong. `_adapter.py` and `adcp/types/buyer.py`'s own `__adcp_refused__['BrandIdentity']`
are generated and outside the write scope; the aliases-side rows, which are in scope, are
all deleted.

### (d) `tests/fixtures/public_api_snapshot.json`

`__all__` went 748 -> 745, so the snapshot is three words stale. The snapshot is not a file
that fails to collect, so it is outside the write scope, and
`test_public_api_surface_matches_snapshot` already failed before this change for an
unrelated reason — `scripts/export_resolution.py:49`, `module 'adcp.types.domains' has no
attribute 'DOMAINS'` — which has to be fixed before the regeneration
(`scripts/regenerate_public_api_snapshot.py`) can run at all.

### (e) Two `tests/type_checks/` fixtures still fail, for words outside the 27

`brand_identity_imports.py` wants `adcp.types.buyer.BrandIdentity` and
`authorized_agents_variants.py` wants the bare `adcp.types.AuthorizedAgents` — neither is
one of the 27, and both are the flat-surface layer of (b). Left as found.

---

## 6. Where each change landed

| file | change |
|---|---|
| `src/adcp/types/aliases.py` | 24 bindings added (20 re-exports + 4 restated unions); `__all__` 104 -> 127; `__adcp_refused__` emptied — all 14 rows were overturned by pointer |
| `src/adcp/__init__.py` | 3 words out of `__all__` (748 -> 745); the 10 bound words that pointed at `adcp.types` repointed to the existing `adcp.types.aliases` group in `_LAZY_MODULES` and in the `TYPE_CHECKING` block |
| `tests/test_literal_discriminator_defaults.py` | one class deleted |
| `tests/test_public_api.py` | two tests' refusal assertions replaced by identity assertions |
| `tests/type_checks/asset_instance_narrowing.py` | rewritten; now clean under `mypy --strict` |

Not touched: `codegen/`, `src/adcp/types/_schemas/`, `tests_emit/`, and every generated
layer of the flat surface.
