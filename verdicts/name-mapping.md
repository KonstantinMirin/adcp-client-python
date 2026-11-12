# The name mapping: 113 names upstream's own code imports and our surface does not hold

`survey/name_census.py` measured 1,105 class-shaped names upstream 9.6.1 declares and this
tree does not. 104 of them are imported by upstream's TESTS and 31 by their kept MACHINERY
— **113 distinct names, blocking 73 of their test files** (`survey/blocking_names.py`, run
against upstream at `4ed0bce87`). The other 992 are referenced by neither and cost nothing.

**THIS PASS DECIDED 73 OF THE 113 ONE AGENT PER NAME, AND THE TWO NEW COLUMNS ARE WHY IT
EXISTS.** The previous version of this file said, per name, which document and pointer
states its subject. The owner could not tell from it where upstream's symbol CAME FROM —
whether the word was hand-written on their flat surface, minted by their generator, built
by a factory at import, or a module constant that is not a type at all — nor what their code
actually hands to it. Those are now two columns of their own, `origin` and `what passes to
it`, and every verdict below turns on them: a name whose code passes a whole response
document is not the same debt as the same word over one row of an items array, and §6 is a
list of places where upstream's own two answers to that question disagree.

Each row was decided by one agent that did five things in order and recorded all five:

1. **read upstream's declaration at its file and line** — not the name, the statement;
2. **followed every rename to its end**, through `from M import X as Y`, `Y = X`,
   `Y: TypeAlias = X` and a `try/except ImportError` pair, until it reached a `ClassDef`, a
   literal, a factory call, or an expression that declares its own shape;
3. **read every call site, including string literals** — `__all__` entries, lazy-export
   tables, `src/adcp/__init__.py`'s routing maps and `src/adcp/migrate/v3_to_v4.py`'s
   dotted-path map, which no import walk sees;
4. **probed our class** with payloads the document admits and payloads it refuses, and
   recorded both directions;
5. **said plainly where the previous pass was wrong**, which is §4.

**WHICH 73, AND WHY THOSE.** The previous pass graded each row `measured` or `joined`.
**All 69 of its `joined` rows are re-decided here** — a `joined` row was a document+word
match with nothing offered to a class — **plus the 4 `measured` rows whose category was
suspect** (`AssetInstanceType`, `GetProductsResponseUnion`, `IdentityMatchTmpxMacro`,
`ProviderRegistrationTmpxMacro`). The remaining **40 rows, every one of them previously
`measured`**, carry forward unchanged in §1b and are listed as not re-decided. 73 + 40 = 113.

**Three additions to the vocabulary, all forced by measurement.**

* **`origin`** — what upstream's symbol IS at the end of its rename chain. `GENERATED` (36)
  is a `ClassDef` datamodel-code-generator wrote under `adcp/types/domains/`, its word
  derived from a property key, a `$defs` key or a traversal ordinal. `TYPE_ALIAS` (29) is
  hand-written in `aliases.py` / `canonical_creative.py` / `legacy.py` / `error_details.py`,
  usually with its own docstring, on upstream's deliberate flat `__all__`. `FACTORY_BUILT`
  (4) is selected at import by a scan over `vars(module)` — `_format_asset_class`,
  `_repeatable_asset_group_class` — or injected into a generated file as source text by
  `scripts/post_generate_fixes.py`. `CONSTANT` (3) is a module-level value that is not a type
  and validates nothing. `HAND_WRITTEN` (1) is a class authored by a human inside a file
  whose header says it was generated.
* **`what passes to it`** — the thing their code actually offers the name: a whole response
  document, one row of an items array, one property's sub-object, a bare scalar, or nothing
  at all. **28 of the 73 rows open with "nothing": no payload is validated with the name
  anywhere in upstream's `src/`** — it is re-exported, snapshotted and identity-asserted
  there, and where anything is offered to it at all, a test offers it. For those the subject
  is fixed by the field position of the class the rename chain ends at, and the row says so
  instead of inventing a call site.
* **`LEGACY_LAYER`** — a new ACTION, between `ALIAS` and `MIGRATION_NOTE`. Four rows need an
  EXPRESSION over our emitted types rather than a re-export of one of them: a `Literal` of
  arm consts, an `Annotated[str, AfterValidator(...)]` carrier, a four-arm union over
  document roots, a roster derived from the tree at access time. An alias cannot carry them
  because there is no single object to point at, and a migration note alone leaves a name
  upstream's own docs tell adopters to import raising `AttributeError`. §5 is where it lives
  and what separates it from an alias.

Reading 10 is still the rule every row is decided by: **a name with no schema subject gets a
migration note and never a class.** Nothing here mints a class to satisfy an import, and
§5's preamble is the sentence that keeps `LEGACY_LAYER` from becoming one.

## 1. The table

Sorted by `used in production` first, then by name. **70 of the 73 are used in production**
— which is itself a correction: the previous pass recorded several of these with zero
machinery demand, and the demand was there in string literals (`src/adcp/__init__.py`'s lazy
routing table, `src/adcp/migrate/v3_to_v4.py`'s rename map, a module's own `__all__`), which
an import-only AST walk cannot see. `upstream declaration` is the END of the rename chain,
with the file and line the chain starts at. `what passes to it` is what their code offers
the name, not what the name could accept.

| name | origin | upstream declaration (end of chain) | what passes to it | prod | category | our type | use instead | document | pointer | probed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AcceptedLoss` | GENERATED | `domains/media_buy/legacy_purchase_continuation_input.py:22` `class AcceptedLoss(StrEnum)`, 3 members | ONE array element — a loss token | yes | ARTIFACT | `adcp.types.media_buy.RequestProposalsResponsePurchaseContinuationLegacyCreateLossesItem` | that class (= the public `adcp.types.Loss`) | `media-buy/legacy-purchase-continuation-input.json` | `#/properties/accepted_losses/items` | yes |
| `AssetInstance` | TYPE_ALIAS | `aliases.py:361-383` → hand-written `Annotated[20-arm union, Discriminator("asset_type")]` | ONE asset object | yes | SPELLING | `adcp.types.AssetVariant`, 21 branches, `_BRANCH_DISCRIMINATOR='asset_type'` | the document's 21 arms as `Annotated[…, Field(discriminator="asset_type")]` | `core/assets/asset-union.json` | `#` | yes |
| `AssetInstanceType` | TYPE_ALIAS | `aliases.py:384-404` → `Literal[` 20 strings `]` | ONE `asset_type` string, in an adopter's exhaustive match | yes | SAME_BUT_NOT | `adcp.types.core.AssetVariant`'s 21 arm consts; no flat vocabulary of ours is this node | a 21-value `Literal` in the legacy layer (§5) | `core/assets/asset-union.json` | `#/oneOf/{0..20}/properties/asset_type/const` | yes |
| `AuthorizedAgents` | GENERATED | `_eager.py:996` `AuthorizedAgents1 as AuthorizedAgents` → `domains/adagents.py:254` `class AuthorizedAgents1` | ONE `authorized_agents[]` row, `authorization_type="property_ids"` | yes | ARTIFACT | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPropertyIds` | that class; delete the refusal at `_adapter.py:292` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/0` | yes |
| `AuthorizedAgents1` | TYPE_ALIAS | `_generated.py:3696` `= _GeneratedAuthorizedAgents2` → `domains/adagents.py:327` (`property_tags`) — **shifted by one** | ONE `authorized_agents[]` row, `property_tags` | yes | ARTIFACT | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPropertyTags` | that class — NOT `…ItemPropertyIds`, which is the shifted-number trap | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/1` | yes |
| `AuthorizedAgents3` | TYPE_ALIAS | `_generated.py:3698` `= _GeneratedAuthorizedAgents4` → `domains/adagents.py:400` (`publisher_properties`) — **shifted by one** | ONE `authorized_agents[]` row, `publisher_properties` | yes | ARTIFACT | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPublisherProperties` | that class; the ordinal is a shifted generator index, not a document word | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/3` | yes |
| `AuthorizedAgentsByPropertyId` | TYPE_ALIAS | `aliases.py:1326` `= _AuthorizedAgentsPropertyIds` → `domains/adagents.py:254` | ONE row, built field by field | yes | SPELLING | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPropertyIds` | that class; delete `__adcp_refused__` at `aliases.py:259` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/0` | yes |
| `AuthorizedAgentsByPropertyTag` | GENERATED | `aliases.py:1351` `= _AuthorizedAgentsPropertyTags` → `domains/adagents.py:327` | ONE row, `property_tags` | yes | SPELLING | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPropertyTags` | that class; delete the refusal at `aliases.py:260` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/1` | yes |
| `AuthorizedAgentsByPublisherProperties` | TYPE_ALIAS | `aliases.py:1402` `= _AuthorizedAgentsPublisherProperties` → `domains/adagents.py:400` | ONE row, validated as an adagents fragment | yes | SPELLING | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemPublisherProperties` | that class; delete `aliases.py:261` and `_adapter.py:296` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/3` | yes |
| `AuthorizedAgentsBySignalId` | TYPE_ALIAS | `aliases.py:1435` `= _AuthorizedAgentsSignalIds` → `domains/adagents.py:475` | ONE row, `signal_ids` | yes | SPELLING | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemSignalIds` | that class | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/4` | yes |
| `AuthorizedAgentsBySignalTag` | TYPE_ALIAS | `aliases.py:1448` `= _AuthorizedAgentsSignalTags` → `domains/adagents.py:492` | ONE row, `signal_tags` | yes | SPELLING | `adcp.types.adagents.AdCPAgents…AuthorizedAgentsItemSignalTags` | that class; drop `_adapter.py:298` and `aliases.py:263` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/5` | yes |
| `BadgeRole` | GENERATED | `domains/core/registry_event.py:271` `class BadgeRole(AdCPRootModel[AdcpProtocol])` — a RootModel box | a BARE protocol string (`"measurement"`) | yes | ARTIFACT | `adcp.types.enums.AdCPProtocol` | that enum, as the emitted `BadgeRole = AdCPProtocol` in `core/registry_event`; read the member, not `.root` | `enums/adcp-protocol.json` | `#` (two `$ref` hops from `core/registry-event.json#/$defs/badgeRole`) | yes |
| `CanonicalFormatKindStr` | TYPE_ALIAS | `canonical_creative.py:264` `Annotated[str, AfterValidator(require_canonical_format_kind())]` | ONE `format_kind` string, on an ADOPTER's boundary model | yes | MACHINERY | `adcp.types.core.CanonicalFormatKind` (the vocabulary, 16 values) | the three-line carrier over our enum (§5) — never the enum itself | `core/canonical-format-kind.json` | `#` | yes |
| `CanonicalParameters` | GENERATED | `domains/core/format.py:2614` `class CanonicalParameters(AdCPRootModel[16 arms])`, each arm mixing an EMPTY `CanonicalParameters17` | ONE v1 format's `canonical_parameters` value | yes | ARTIFACT | no class at the pointer: we lower it in place on `Format.canonical_parameters` as `Annotated[ProductFormatDeclaration, AfterValidator(ForbiddenGroups(…))]` | `adcp.types.ProductFormatDeclaration`, through `adcp.types.Format.canonical_parameters` | `core/format.json` | `#/properties/canonical_parameters` | yes |
| `CoreAccount` | GENERATED | `aliases.py:1986` `Account as CoreAccount` → `domains/core/account.py:130` `class Account` | nothing — a disambiguating spelling of a document root | yes | SPELLING | `adcp.types.core.Account` | that class | `core/account.json` | `#` | yes |
| `CreateMediaBuySubmittedResponse` | TYPE_ALIAS | `aliases.py:638` `= CreateMediaBuyResponse3` → `domains/media_buy/create_media_buy_response.py:92` | a WHOLE response document, submitted arm | yes | SPELLING | `adcp.types.media_buy.CreateMediaBuyResponseSubmitted` | that class, aliased beside its served siblings in `aliases.py` | `media-buy/create-media-buy-response.json` | `#/oneOf/2` | yes |
| `CreateMediaBuySuccessResponse` | TYPE_ALIAS | `aliases.py:632` `= CreateMediaBuyResponse1` → `domains/media_buy/create_media_buy_response.py:33` | a WHOLE response document, success arm | yes | SPELLING | `adcp.types.media_buy.CreateMediaBuySuccess` | that class; delete the refusal at `aliases.py:264` | `media-buy/create-media-buy-response.json` | `#/oneOf/0` | yes |
| `DEPRECATED_ROOT` | CONSTANT | `_generated_poc_alias.py:104` `= "adcp.types.generated_poc"` — a `str` literal | nothing — a module-path string; both readers do prefix arithmetic | yes | MACHINERY | `adcp.migrate.v3_to_v4.DEPRECATED_TYPES_ROOT` (same value, already in tree) | RESTATE the literal in a restored `adcp.types._generated_poc_alias` and pin the equality; never `adcp.types.domains.MIRROR` | — (no document: a Python dotted path) | — | yes |
| `DOMAINS` | CONSTANT | `domains/__init__.py:22` — a 26-element tuple of strings, itself written by `consolidate_exports.py:1035` | nothing — each element is interpolated into a module path and imported | yes | MACHINERY | none, and none is owed: what is owed is a module ATTRIBUTE on our mirror | `adcp.types.domains.DOMAINS`, derived from `_surface` at access time (§5) — 23 names, not 26 | — (no node states a roster of generator output directories) | — | no |
| `DaastAsset1` | GENERATED | `domains/core/assets/asset_union.py:1660` `class DaastAsset1` (the inlined-`$ref` duplicate of `DaastAsset3`) | ONE DAAST asset object, url delivery | yes | ARTIFACT | `adcp.types.core.DAASTAssetUrl` (bound there as `DaastAsset3`); NO class of ours at the asset-union copy — that is the hole | that class, and fix the distribution gate at `codegen/lower/union.py:3283` (§7) | `core/assets/daast-asset.json` | `#/oneOf/0` (= `asset-union.json#/oneOf/12/oneOf/0`, a bare `$ref`) | yes |
| `DaastAsset2` | GENERATED | `domains/core/assets/asset_union.py:1793` `class DaastAsset2` → aliased `InlineDaastAsset` | ONE DAAST asset object, inline delivery | yes | ARTIFACT | `adcp.types.core.DAASTAssetInline` (also bound `DaastAsset4`) | that class, and the same distribution fix (§7) | `core/assets/daast-asset.json` | `#/oneOf/1` | yes |
| `FIELDS` | CONSTANT | `versioned_bases/_v32.py:27245` `FIELDS: dict[str, dict[str, tuple[Any, Any]]] = {` — a 197-entry dict literal | nothing — it is subscripted, never called; one production read builds `create_model` | yes | MACHINERY | — (nothing owed; `adcp.types.versioned_bases` does not exist here and need not) | do not import it; address the class at its document, e.g. `_schemas.media_buy.package_request.PackageRequest` | — | — | yes |
| `File` | GENERATED | `domains/brand/get_brand_identity_response.py:50` `class File(AdcpVersionEnvelope)` | ONE row — a font-file object | yes | ARTIFACT | `adcp.types._schemas.brand.ObjUrlWeightWeightRangeStyle` (public `adcp.types.brand.BrandDiscoveryFontFile`) | `adcp.types.brand.BrandDiscoveryFontFile`, and fix the published-word join (§7) | `brand/get-brand-identity-response.json` | `#/oneOf/0/properties/fonts/definitions/font_role/oneOf/1/properties/files/items` (= `brand.json#/definitions/font_file`) | yes |
| `FormatAssetUnion` | TYPE_ALIAS | `domains/core/format.py:2730`, EMITTED by `post_generate_fixes.py:8260` `_OPEN_ASSET_UNIONS` — 23 Tag'd arms + `UnknownFormatAsset` | ONE asset ROW — the element type of `Format.assets` | yes | SPELLING | `adcp.types.AssetsItemIndividual \| adcp.types.RepeatableGroupAsset` (+ fallback `adcp.types.UnknownFormatAsset`) | that three-arm expression (measured to reproduce all three outcomes); drop the fallback for the closed, document-faithful reading | `core/format.json` | `#/properties/assets/items` | yes |
| `GeographicPlaceIdentifierSystem1` | GENERATED | `domains/core/geo_place_system.py:14` `class GeographicPlaceIdentifierSystem1(StrEnum)`, 3 members | nothing is validated — their one use ITERATES it for `.value` | yes | ARTIFACT | `adcp.types.core.GeographicPlaceIdentifierSystem` is the CONTAINING `anyOf`; no declaration of ours sits at the arm | note both halves: validate with the containing union (or `GeoPlaceSystemKey` for a map key); enumerate with `get_args(...)` | `core/geo-place-system.json` | `#/anyOf/0` | yes |
| `GetProductsResponseUnion` | TYPE_ALIAS | `aliases.py:684` a 4-arm `TypeAlias`; **declared twice** — `_eager.py:946` rebinds it over different objects | nothing — no `model_validate`, no `TypeAdapter`; it is an ANNOTATION callers pattern-match on | yes | NO_SUBJECT | `GetProductsResponse \| GetProductsSubmitted \| GetProductsWorking \| GetProductsInputRequired` (all `adcp.types.media_buy`) | that expression, bound in the legacy layer (§5); do NOT use it to classify an arbitrary wire payload | `manifest.json` + the four documents it names | `#/tools/get_products/{response_schema,async_response_schemas[0..2]}` — a tool entry, not a node | yes |
| `GetProductsSubmittedResponse` | TYPE_ALIAS | `aliases.py:665` `: TypeAlias = GetProductsSubmitted` → `…/get_products_async_response_submitted.py:17` | a WHOLE document root — the async submitted envelope | yes | SPELLING | `adcp.types.media_buy.GetProductsSubmitted` | that class; one line serves it and its two `Working`/`InputRequired` siblings | `media-buy/get-products-async-response-submitted.json` | `#` | yes |
| `GetSignalsSubmittedResponse` | TYPE_ALIAS | `aliases.py:699` `: TypeAlias = GetSignalsSubmitted` → `domains/signals/get_signals_async_response_submitted.py:17` | a WHOLE response document — the submitted envelope | yes | SPELLING | `adcp.types.signals.GetSignalsSubmitted` | that class (ours folds upstream's two byte-identical copies into one object) | `signals/get-signals-async-response-submitted.json` | `#` | yes |
| `GetSignalsWorkingResponse` | TYPE_ALIAS | `aliases.py:705` `: TypeAlias = GetSignalsWorking` → `…/get_signals_async_response_working.py:16` | nothing — one identity assertion against the verb union | yes | SPELLING | `adcp.types.signals.GetSignalsWorking` | that class | `signals/get-signals-async-response-working.json` | `#` | yes |
| `GroupFormatAssetUnion` | TYPE_ALIAS | `domains/core/format.py:669`, EMITTED by `post_generate_fixes.py:8246` — 21 Tag'd arms + `UnknownGroupAsset` | ONE group-asset ROW inside a repeatable group | yes | SPELLING | the 21-arm union our tree states ONLY as an annotation on `RepeatableGroupAsset.assets`; **0 symbols carry the pointer** | declare the node (`RepeatableGroupAssetAssets`) and bind the word to it (§7); interim, spell the 21 `Group…Asset` arms | `core/format.json` | `#/properties/assets/items/oneOf/1/properties/assets/items` | yes |
| `IdentityMatchTmpxMacro` | FACTORY_BUILT | `aliases.py:2163` `TmpxMacro as IdentityMatchTmpxMacro` → `domains/trusted_match/identity_match_response.py:22`, itself INJECTED as source text by `post_generate_fixes.py:4728` | NOTHING — no construction, no validation, no annotation anywhere | yes | ARTIFACT | — (the only node mentioning the key FORBIDS it) | a note: `value` → `TMPXChunk.value`; `name` → `PublisherTMPXMacroMapping` — a JOIN of two documents, not one node | `trusted-match/identity-match-response.json` | `#/not/anyOf/2` — a PROHIBITION, not a node | yes |
| `ImageFormatAsset` | FACTORY_BUILT | `aliases.py:1741` ← `:1713` `_format_asset_class("image")`, a factory scanning `vars(domains.core.format)` by `model_fields["asset_type"].default` | ONE asset-slot ROW of `Format.assets` | yes | SPELLING | `adcp.types.IndividualImageAsset` | bind `ImageFormatAsset = IndividualImageAsset` directly; do NOT port the factory (our const has no default, so it finds nothing and raises at import) | `core/format.json` | `#/properties/assets/items/oneOf/0/oneOf/0` | yes |
| `ImageFormatGroupAsset` | FACTORY_BUILT | `aliases.py:1854` ← `:1728` `_format_asset_class("image", group=True)` → `domains/core/format.py:456` `class Assets31` | ONE row of a repeatable group's `assets` | yes | SPELLING | `adcp.types.core.GroupImageAsset` | `from adcp.types.core import GroupImageAsset as ImageFormatGroupAsset` in `_adapter.py`; same shape for its 13 siblings | `core/format.json` | `#/properties/assets/items/oneOf/1/properties/assets/items/oneOf/0` | yes |
| `InlineVastAsset` | TYPE_ALIAS | `aliases.py:1040` `: TypeAlias = VastAsset2` → `domains/core/assets/asset_union.py:2437` | ONE VAST asset object, inline delivery | yes | ARTIFACT | `adcp.types.core.VASTAssetInline` | that class; delete the false refusal at `aliases.py:267` | `core/assets/vast-asset.json` | `#/oneOf/1` | yes |
| `Invoice` | GENERATED | `domains/account/get_account_financials_response.py:50` `class Invoice(AdcpVersionEnvelope)` | ONE row of the `invoices` array | yes | ARTIFACT | `adcp.types.account.GetAccountFinancialsSuccessInvoicesItem` | that class, with a `compat.__adcp_provisional__` entry naming the node (the word is minted from structure) | `account/get-account-financials-response.json` | `#/oneOf/0/properties/invoices/items` | yes |
| `LegacyProductFormatDeclaration` | TYPE_ALIAS | `legacy.py:153` `= LegacyGeneratedProductFormatDeclaration` → `domains/core/product_format_declaration.py:1854`, a 16-arm `Annotated[…, discriminator='format_kind']` | ONE whole format-declaration object; one production STRING LITERAL in the v3→v4 codemod map | yes | SPELLING | `adcp.types.ProductFormatDeclaration` (`BranchDispatchMixin` over 16 branches) | that class | `core/product-format-declaration.json` | `#` | yes |
| `ListCreativesCanonicalCreative` | GENERATED | `aliases.py:2121` `Creatives1 as ListCreativesCanonicalCreative` → `list_creatives_response.py:504` `Creatives1 = Creative` | ONE `creatives[]` row (a `format_kind` row) | yes | SPELLING | `adcp.types.creative.ListedCreativeCanonicalFormatKind` | that arm class; the item union is `ListedCreativeNamedFormatReference \| ListedCreativeCanonicalFormatKind` | `creative/list-creatives-response.json` | `#/properties/creatives/items/oneOf/1` | yes |
| `ListCreativesLegacyCreative` | GENERATED | `aliases.py:2117` `Creatives as ListCreativesLegacyCreative` → `list_creatives_response.py:503` `Creatives = Creative` | ONE `creatives[]` row, either arm | yes | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | that items class (reproduces their behaviour exactly); name the ARM when you mean one | `creative/list-creatives-response.json` | `#/properties/creatives/items` | yes |
| `MajorVersion` | GENERATED | `domains/protocol/get_adcp_capabilities_response.py:65` `class MajorVersion(ScalarInt)`, `_constraints={'ge':1}` | ONE integer — it IS the `major_versions` items type | yes | ARTIFACT | `adcp.types.constraints.IntMin1` | `int`, or `IntMin1` when annotating; write `3`, never `MajorVersion(3)` | `protocol/get-adcp-capabilities-response.json` | `#/properties/adcp/properties/major_versions/items` | yes |
| `Pass` | GENERATED | `domains/content_standards/create_content_standards_request.py:54` `class Pass`; a byte-identical twin in the update request | ONE exemplar row of `calibration_exemplars.pass[]` | yes | ARTIFACT | `adcp.types.content_standards.PassItemUrl` | nothing is owed: the name resolves at NO spelling upstream (`_generated.__all__` claims it, the facade raises) | `content-standards/create-content-standards-request.json` | `#/properties/calibration_exemplars/properties/pass/items/oneOf/0` | yes |
| `Pattern` | GENERATED | `domains/protocol/get_adcp_capabilities_response.py:123` `class Pattern(StrEnum)`, 3 members | nothing — one field annotation inside its own generated module | yes | ARTIFACT | `adcp.types.GetAdCPCapabilitiesResponseAdcpPrincipalReportingDestinationOfferingsItemPattern` | that class (or the domain path); NOT `ReportingDeliveryOfferingReportingDeliveryPattern` — same values, different node | `protocol/get-adcp-capabilities-response.json` | `#/properties/adcp/properties/principal/properties/reporting_destination_offerings/items/properties/pattern` | yes |
| `PrincipalReadResult` | TYPE_ALIAS | `aliases.py:942-947` a hand-written 4-arm `TypeAlias` over `domains/protocol/get_principal_response.py:99-102` | nothing — no call site; the subject is fixed by the arms their generated union holds | yes | SPELLING | `CurrentPrincipalConfiguration \| RecognizedPrincipalWithoutStandingConfiguration \| UnconfiguredPrincipal \| FailedPrincipalRead` | that expression (identical to `GetPrincipalResponse.model_fields["result"].annotation`) | `protocol/get-principal-response.json` | `#/properties/result` (arms `/oneOf/0..3`) | yes |
| `PrincipalSyncResult` | TYPE_ALIAS | `aliases.py:948-950` a hand-written 3-arm `TypeAlias` over `sync_principal_response.py:102-104` | nothing — measured from the right-hand side, not a call site | yes | SPELLING | `AppliedPrincipalConfiguration \| ValidatedPrincipalDryRun \| FailedPrincipalSync` | that expression (identical to `SyncPrincipalResponse.model_fields['result'].annotation`) | `protocol/sync-principal-response.json` | `#/properties/result` (arms `/oneOf/0..2`) | yes |
| `ProviderRegistrationTmpxMacro` | HAND_WRITTEN | `aliases.py:2166` `TmpxMacro as ProviderRegistrationTmpxMacro` → `provider_registration.py:23` `class TmpxMacro(ScalarStr)`, HAND-WRITTEN source injected by `post_generate_fixes.py:4782` | a bare macro-name STRING, in one test; nothing in src/ | yes | ARTIFACT | — (no pointer: the root is `additionalProperties: false` and states no macro name) | a note: register `tmpx_slots`; map `(provider_id, slot_id)` through `PublisherTMPXMacroMapping` — neither is an alias target | `trusted-match/provider-registration.json` | none — no node states a macro name, in any of 30 cached copies | yes |
| `PublisherDomain` | GENERATED | `domains/core/canonical_product.py:47` `class PublisherDomain(ScalarStr)` + 3 byte-identical siblings + 1 bundled clone | a bare domain-name STRING, the items type of `publisher_domains` | yes | ARTIFACT | `adcp.types.core.DomainName` | that class | `core/domain-name.json` | `#` (in the patched bundle every `publisher_domains` items node is a `$ref` to it) | yes |
| `PublisherPreviewRoute` | GENERATED | `aliases.py:2061` `Route as PublisherPreviewRoute` → `domains/core/preview_provider.py:13` `class Route` | ONE row of `routes[]` (their own code passes it as a bare dict to the parent) | yes | SPELLING | `adcp.types.core.PublisherDesignatedPreviewProviderRoutesItem` | that class | `core/preview-provider.json` | `#/properties/routes/items` | yes |
| `PurchaseContinuation1` | GENERATED | `domains/media_buy/request_proposals_response.py:109` `class PurchaseContinuation1`, `kind='legacy_create'` | ONE `purchase_continuation` object of kind `legacy_create` | yes | ARTIFACT | `adcp.types.media_buy.PurchaseContinuationLegacyCreate` | that class (also the target for their `PurchaseContinuation3/5/7` clones) | `media-buy/request-proposals-response.json` | `#/properties/purchase_continuation/oneOf/1` | yes |
| `PushNotificationAuthentication` | GENERATED | `aliases.py:2067` `Authentication as PushNotificationAuthentication` → `domains/core/push_notification_config.py:15` | the inline `authentication` sub-object of a push config | yes | SPELLING | `adcp.types.core.PushNotificationConfigAuthentication` | that class, in `compat.py` AND in `aliases.py` (their test imports `adcp.types.aliases`) | `core/push-notification-config.json` | `#/properties/authentication` | yes |
| `RefineProposalsResponse1` | GENERATED | `domains/media_buy/refine_proposals_response.py:585` `class RefineProposalsResponse1` | a WHOLE response document, the completed arm | yes | ARTIFACT | `adcp.types.media_buy.RefineProposalsResponseCompleted` | that class — EMIT the admissible ordinal `RefineProposalsResponse1 = RefineProposalsResponseCompleted`, do not hand-write it (§7) | `media-buy/refine-proposals-response.json` | `#/anyOf/0` | yes |
| `RefineProposalsResponse2` | GENERATED | `domains/media_buy/refine_proposals_response.py:620` `class RefineProposalsResponse2(AdcpResponse, CompactTaskSubmitted)` | nothing by name — their code reaches the arm only through the union | yes | ARTIFACT | `adcp.types.media_buy.RefineProposalsResponseSubmitted` | that class; for the whole document use `adcp.types.media_buy.RefineProposalsResponse`, which dispatches | `media-buy/refine-proposals-response.json` | `#/anyOf/1` | yes |
| `RepeatableAssetGroup` | FACTORY_BUILT | `aliases.py:1845` ← `:1727` `_repeatable_asset_group_class()`, a factory selecting on `model_fields["item_type"].default` → `domains/core/format.py:701` `class Assets29` | ONE row of `Format.assets` — a repeatable-group item | yes | SPELLING | `adcp.types.RepeatableGroupAsset` | `RepeatableAssetGroup = adcp.types.RepeatableGroupAsset` | `core/format.json` | `#/properties/assets/items/oneOf/1` | yes |
| `RequestProposalsResponse4` | GENERATED | `domains/media_buy/request_proposals_response.py:359` `class RequestProposalsResponse4(AdcpResponse, CompactTaskSubmitted)` | nothing by name (one `model_fields` reflection); whole documents reach it through the union | yes | ARTIFACT | `adcp.types.media_buy.RequestProposalsResponseSubmitted` | that class — the alias is owed; the EMIT_CHANGE is the hole chasing it found (§7) | `media-buy/request-proposals-response.json` | `#/anyOf/3` | yes |
| `Row` | GENERATED | `domains/a2ui/si_catalog.py:174` `class Row(AdCPBaseModel)` | NOTHING — a leaf class with no incoming edge in their own model graph | yes | ARTIFACT | — (no class: the entry is in the bundle's one DEAD `definitions` section, named by no `$ref`) | a note: the NAME survives as `adcp.types.Component.Row`; the body is `A2UIComponent.component = {'Row': {...}}`. Do NOT alias the class onto the enum member | `a2ui/si-catalog.json` | `#/definitions/Row` | yes |
| `ScopeFromBillingNotSupported` | GENERATED | `error_details.py:85-88` `Scope as ScopeFromBillingNotSupported` → `domains/error_details/billing_not_supported.py:16` `class Scope(StrEnum)` | a member ACCESS (`.account`) used as a field value; it must BE the field's annotation | yes | SPELLING | `adcp.types.error_details.BillingNotSupportedDetailsScope` | that enum, at TWO spellings: `adcp.types.compat` and `adcp.types.error_details` | `error-details/billing-not-supported.json` | `#/properties/scope` | yes |
| `ScopeFromRateLimited` | GENERATED | `error_details.py:110-113` `Scope as ScopeFromRateLimited` → `domains/error_details/rate_limited.py:14` `class Scope(StrEnum)` | a member access and a `list[…]` annotation — one scalar enum member | yes | SPELLING | `adcp.types.error_details.RateLimitedDetailsScope` | that enum; member spellings carry over (`.account`, `.tool`, `.global_`) | `error-details/rate-limited.json` | `#/properties/scope` | yes |
| `SyncAccountsCreditLimit` | GENERATED | `aliases.py:1970` `CreditLimit as SyncAccountsCreditLimit` → `domains/account/sync_accounts_response.py:40` | ONE `{amount, currency}` object at a field of one `accounts[]` row | yes | SPELLING | `adcp.types.core.AccountCreditLimit` | that class (their own production code reaches the same object under the bare `CreditLimit`) | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items/properties/credit_limit` | yes |
| `SyncAccountsSetup` | GENERATED | `aliases.py:1973` `Setup as SyncAccountsSetup` → `domains/account/sync_accounts_response.py:33` | nothing — two identity assertions; subject fixed by the field position | yes | SPELLING | `adcp.types.core.AccountSetup` | that class | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items/properties/setup` | yes |
| `SyncAudiencesAudience` | TYPE_ALIAS | `aliases.py:1589` `= SyncAudiencesAudienceInternal` → `domains/media_buy/sync_audiences_request.py:34` `class Audience` | ONE REQUEST row — it is the adopter-facing protocol signature's element type | yes | SPELLING | `adcp.types.media_buy.SyncAudiencesRequestAudiencesItem` | that class | `media-buy/sync-audiences-request.json` | `#/properties/audiences/items` | yes |
| `SyncCatalogResult` | TYPE_ALIAS | `aliases.py:774` `: TypeAlias = SyncCatalogResultInternal` → `aliases.py:531-538` `try: Catalog … except ImportError: _g.SyncCatalogsResponse`; the try branch is live | ONE catalog ROW — their docstrings name the row type and the response type as two things | yes | SPELLING | `adcp.types.media_buy.SyncCatalogsSuccessCatalogsItem` | that class | `media-buy/sync-catalogs-response.json` | `#/oneOf/0/properties/catalogs/items` | yes |
| `SyncCreativeResult` | TYPE_ALIAS | `aliases.py:733` `: TypeAlias = SyncCreativeResultInternal` → `aliases.py:514-519` `try: Creative … except ImportError: _g.SyncCreativesResponse`; the try branch is live | ONE creative ROW, per element of a failure list (`_creative_batch.py:40`) | yes | SPELLING | `adcp.types.creative.SyncCreativesSuccessCreativesItem` | that class, in `compat.py` and `aliases.py`; drop `__adcp_refused__` at `aliases.py:270` | `creative/sync-creatives-response.json` | `#/oneOf/0/properties/creatives/items` | yes |
| `SyncCreativesCreative` | GENERATED | `aliases.py:2124` `Creative as SyncCreativesCreative` → `domains/creative/sync_creatives_response.py:28` | ONE per-creative result row | yes | SPELLING | `adcp.types.creative.SyncCreativesSuccessCreativesItem` | that class | `creative/sync-creatives-response.json` | `#/oneOf/0/properties/creatives/items` | yes |
| `SyncGovernanceGovernanceAgent` | GENERATED | `aliases.py:1983` `GovernanceAgent as SyncGovernanceGovernanceAgent` → `domains/account/sync_governance_request.py:37` | nothing — their governance path validates the whole request instead | yes | SPELLING | `adcp.types.account.SyncGovernanceRequestAccountsItemGovernanceAgentsItem` | that class (also bound by the catalogue pass as `adcp.types.GovernanceAgent`) | `account/sync-governance-request.json` | `#/properties/accounts/items/properties/governance_agents/items` | yes |
| `UpdateMediaBuyErrorResponse` | TYPE_ALIAS | `aliases.py:850` then REBOUND at `:2219` → `canonical_creative.py:1233` → `domains/media_buy/update_media_buy_response.py:81` | a WHOLE response document, error arm (a `TypeGuard` narrowing target) | yes | SPELLING | `adcp.types.media_buy.UpdateMediaBuyError` | that class, with `status` supplied: `{"status": "failed", "errors": [...]}` | `media-buy/update-media-buy-response.json` | `#/oneOf/1` | yes |
| `UpdateMediaBuySuccessResponse` | TYPE_ALIAS | `aliases.py:847` `: TypeAlias = UpdateMediaBuyResponse1` → `canonical_creative.py:1212` → `domains/media_buy/update_media_buy_response.py:33` | a WHOLE response document, success arm | yes | SPELLING | `adcp.types.media_buy.UpdateMediaBuySuccess` | that class, plus the `Legacy…` sibling spelling (the v3→v4 table names it as a literal) | `media-buy/update-media-buy-response.json` | `#/oneOf/0` | yes |
| `UrlDaastAsset` | TYPE_ALIAS | `aliases.py:1044` `: TypeAlias = DaastAsset1` → `domains/core/assets/asset_union.py:1660` | ONE DAAST asset row, url delivery | yes | SPELLING | `adcp.types.core.DAASTAssetUrl` | that class — **and §7: the alias alone cannot make `isinstance` hold on the asset-union path** | `core/assets/daast-asset.json` | `#/oneOf/0` | yes |
| `UrlVastAsset` | TYPE_ALIAS | `aliases.py:1037` `: TypeAlias = VastAsset1` → `domains/core/assets/asset_union.py:2296` | ONE VAST asset object, url delivery | yes | SPELLING | `adcp.types.core.VASTAssetUrl` | that class; construct `VASTAssetUrl(asset_type='vast', delivery_type='url', url=…)` | `core/assets/vast-asset.json` | `#/oneOf/0` | yes |
| `VastAsset1` | GENERATED | `domains/core/assets/asset_union.py:2296` `class VastAsset1` — one of TWO generated copies of one node (`VastAsset3` is the other, and wins their flat namespace) | ONE VAST asset object, url delivery | yes | ARTIFACT | `adcp.types.core.VASTAssetUrl` | that class (already reachable as `adcp.types.VastAsset3`) | `core/assets/vast-asset.json` | `#/oneOf/0` | yes |
| `VendorPricingOptionUnion` | TYPE_ALIAS | `aliases.py:155` `VendorPricingOption as VendorPricingOptionUnion` → the generated `Annotated[5 arms, title+description only]` | ONE pricing-option object; a production STRING LITERAL at `migrate/v3_to_v4.py:418` | yes | SPELLING | `adcp.types.core.VendorPricingOption` | that class; fix or drop the false reason at `_adapter.py:323` | `core/vendor-pricing-option.json` | `#` | yes |
| `ViewThreshold` | GENERATED | `domains/pricing_options/cpv_option.py:18` `class ViewThreshold(ScalarFloat)`, `_constraints={'ge':0.0,'le':1.0}` | a float VALUE (`ViewThreshold(0.5) * 2`); as a type, the numeric arm of an inline `oneOf` | yes | ARTIFACT | `adcp.types.constraints.FloatMin0Max1` | that constraint; the whole field is `FloatMin0Max1 \| ViewThresholdDurationSeconds`. For construction-time refusal, subclass `ScalarFloat` | `pricing-options/cpv-option.json` | `#/properties/parameters/properties/view_threshold/oneOf/0` | yes |
| `WholesaleFeedSignal` | GENERATED | `aliases.py:2107` `Signal as WholesaleFeedSignal` → `domains/core/wholesale_feed_event.py:401` `class Signal(SignalListing)` | ONE per-signal row nested in an event payload | yes | SPELLING | `adcp.types.core.WholesaleFeedEventSignal` | that class, as the contextual spelling beside `_adapter.py:97`'s bare `Signal` | `core/wholesale-feed-event.json` | `#/$defs/signal` | yes |
| `AuthorizedAgents2` | GENERATED | `_generated.py:3697` `= _GeneratedAuthorizedAgents3` → `domains/adagents.py:629` (`inline_properties`) — **shifted by one** | ONE `authorized_agents[]` row, `inline_properties` | no | ARTIFACT | `adcp.types._schemas.adagents.AdCPAgents…AuthorizedAgentsItemInlineProperties` | that class; ours requires `authorization_type` where theirs defaults it | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/2` | yes |
| `SyncAccountsAccount` | GENERATED | `aliases.py:1968` `Account as SyncAccountsAccount` → `domains/account/sync_accounts_response.py:46` | ONE per-account row (their test validates the response AND the bare element, with two names) | no | SPELLING | `adcp.types.account.SyncAccountsSuccessAccountsItem` | that class | `account/sync-accounts-response.json` | `#/oneOf/0/properties/accounts/items` | yes |
| `SyncEventSourcesSetup` | GENERATED | `aliases.py:2136` `Setup as SyncEventSourcesSetup` → `domains/media_buy/sync_event_sources_response.py:24` | the nested `setup` object of one `event_sources` row; nothing is passed to the NAME | no | SPELLING | `adcp.types.media_buy.SyncEventSourcesSuccessEventSourcesItemSetup` | that class | `media-buy/sync-event-sources-response.json` | `#/oneOf/0/properties/event_sources/items/properties/setup` | yes |

Reading the `our type` column: an em dash means **no class of ours carries that pointer**,
and the row says in `use instead` whether that is a decision (`Row`, `Pass`,
`IdentityMatchTmpxMacro`, `ProviderRegistrationTmpxMacro`, `FIELDS`, `DOMAINS`) or a hole
(`GroupFormatAssetUnion`, `CanonicalParameters` — §7).

### 1b. Carried forward unchanged: the 40 rows this pass did not re-read

**NOT RE-DECIDED, AND NOT RE-DERIVED EITHER.** These are the previous pass's rows verbatim,
with its own columns — they carry no `origin` and no `what passes to it` because nobody
measured those, and their `basis` column is the previous pass's own. Every one of them was
graded `measured` there, which is why they were not re-run first; §8 says what would settle
them to the standard of §1. Where one of them is named in §4, §6 or §7 as contradicted by a
row of §1 (`InlineDaastAsset`, `VastAsset2`, `AuthorizedAgentsByInlineProperties`,
`ListCreativesCreative`, `ListCreativesCreativeItem`, `Refine`), the §1 row is the
measurement and this table is the older reading.

| upstream name | category | our dotted path | document | pointer | action | blocks tests | blocks machinery | basis (previous pass) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CanonicalBoundaryModel` | MACHINERY | — | — | — | **NONE** | 8 | 0 | measured |
| `DeliveryCreative` | SPELLING | `adcp.types.creative.GetCreativeDeliveryResponseCreativesItem` | `creative/get-creative-delivery-response.json` | `#/properties/creatives/items` | **ALIAS** | 4 | 0 | measured |
| `PRIMARY_CANONICAL_MODELS` | MACHINERY | — | — | — | **NONE** | 4 | 0 | measured |
| `CANONICAL_ROOT` | MACHINERY | `adcp.migrate.v3_to_v4.CANONICAL_TYPES_ROOT` | — | — | **ALIAS** | 2 | 0 | measured |
| `InlineDaastAsset` | SPELLING | `adcp.types.core.DAASTAssetInline` | `core/assets/daast-asset.json` | `#/oneOf/1` | **ALIAS** | 2 | 1 | measured |
| `SupportedMajor` | ARTIFACT | `adcp.types.constraints.IntMin1` | `error-details/version-unsupported.json` | `#/properties/supported_majors/items` | **ALIAS** | 2 | 0 | measured |
| `SupportedVersion` | ARTIFACT | `adcp.types.constraints.AdCPVersionEnvelopeAdcpVersion` | `error-details/version-unsupported.json` | `#/properties/supported_versions/items` | **ALIAS** | 2 | 0 | measured |
| `UpdateMediaBuySubmittedResponse` | SPELLING | `adcp.types.media_buy.UpdateMediaBuyResponseSubmitted` | `media-buy/update-media-buy-response.json` | `#/oneOf/2` | **ALIAS** | 2 | 0 | measured |
| `AuthorizedAgentsByInlineProperties` | SPELLING | `adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemInlineProperties` | `adagents.json` | `#/oneOf/1/properties/authorized_agents/items/oneOf/2` | **ALIAS** | 1 | 1 | measured |
| `CatalogGroupBinding` | SPELLING | `adcp.types.core.CatalogFieldBindingCatalogGroup` | `core/requirements/catalog-field-binding.json` | `#/oneOf/2` | **ALIAS** | 1 | 1 | measured |
| `ComplyListScenariosResponse` | SPELLING | `adcp.types.compliance.ListScenariosSuccess` | `compliance/comply-test-controller-response.json` | `#/oneOf/0` | **ALIAS** | 1 | 0 | measured |
| `CoreCreditLimit` | SPELLING | `adcp.types.core.AccountCreditLimit` | `core/account.json` | `#/properties/credit_limit` | **ALIAS** | 1 | 0 | measured |
| `CoreGovernanceAgent` | SPELLING | `adcp.types.core.AccountGovernanceAgentsItem` | `core/account.json` | `#/properties/governance_agents/items` | **ALIAS** | 1 | 0 | measured |
| `CoreMediaBuy` | SPELLING | `adcp.types.core.MediaBuy` | `core/media-buy.json` | `#` | **ALIAS** | 1 | 0 | measured |
| `CoreSetup` | SPELLING | `adcp.types.core.AccountSetup` | `core/account.json` | `#/properties/setup` | **ALIAS** | 1 | 0 | measured |
| `CpmVendorPricingOption` | ARTIFACT | `adcp.types.core.CpmPricing` | `core/signal-pricing.json` | `#/oneOf/0` | **ALIAS** | 1 | 0 | measured |
| `GetMediaBuysMediaBuy` | SPELLING | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItem` | `media-buy/get-media-buys-response.json` | `#/properties/media_buys/items` | **ALIAS** | 1 | 0 | measured |
| `GetProductsInputRequiredResponse` | SPELLING | `adcp.types.media_buy.GetProductsInputRequired` | `media-buy/get-products-async-response-input-required.json` | `#` | **ALIAS** | 1 | 0 | measured |
| `GetProductsWorkingResponse` | SPELLING | `adcp.types.media_buy.GetProductsWorking` | `media-buy/get-products-async-response-working.json` | `#` | **ALIAS** | 1 | 0 | measured |
| `GetSignalsResponseUnion` | MACHINERY | union over GetSignalsResponse \| GetSignalsSubmitted \| GetSignalsWorking | `signals/get-signals-response.json (+2 async documents)` | `# of each; no node states the union` | **ALIAS** | 1 | 0 | measured |
| `GetSignalsSignal` | SPELLING | `adcp.types.signals.GetSignalsResponseSignalsItem` | `signals/get-signals-response.json` | `#/properties/signals/items` | **ALIAS** | 1 | 0 | measured |
| `LegacyProposalTotalBudgetGuidance` | SPELLING | `adcp.types.core.ProposalTotalBudgetGuidance` | `core/proposal.json` | `#/properties/total_budget_guidance` | **ALIAS** | 1 | 0 | measured |
| `ListCreativesCreative` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | measured |
| `ListCreativesCreativeItem` | SPELLING | `adcp.types.creative.ListCreativesResponseCreativesItem` | `creative/list-creatives-response.json` | `#/properties/creatives/items` | **ALIAS** | 1 | 0 | measured |
| `ListCreativesSort` | SPELLING | `adcp.types.creative.ListCreativesRequestSort` | `creative/list-creatives-request.json` | `#/properties/sort` | **ALIAS** | 1 | 0 | measured |
| `OverlayUnit` | SPELLING | `adcp.types.core.OverlayBoundsUnit` | `core/overlay.json` | `#/properties/bounds/properties/unit` | **ALIAS** | 1 | 0 | measured |
| `REMOVED_IN_MAJOR` | MACHINERY | — | — | — | **NONE** | 1 | 0 | measured |
| `RealEstateUnit` | ARTIFACT | `adcp.types.core.RealEstateItemAreaUnit` | `core/real-estate-item.json` | `#/properties/area/properties/unit` | **ALIAS** | 1 | 0 | measured |
| `RefineProposalsTotalBudgetGuidance` | ARTIFACT | `adcp.types.core.CanonicalProposalTotalBudgetGuidance` | `core/canonical-proposal.json` | `#/properties/total_budget_guidance` | **ALIAS** | 1 | 0 | measured |
| `ReportingDelivery` | ARTIFACT | `adcp.types.core.ReportingDeliveryCapabilities` | `core/reporting-delivery-capabilities.json` | `#` | **MIGRATION_NOTE** | 1 | 0 | measured |
| `SyncGovernanceAccount` | SPELLING | `adcp.types.account.SyncGovernanceRequestAccountsItem` | `account/sync-governance-request.json` | `#/properties/accounts/items` | **ALIAS** | 1 | 0 | measured |
| `TasksListSort` | SPELLING | `adcp.types.core.TasksListRequestSort` | `core/tasks-list-request.json` | `#/properties/sort` | **ALIAS** | 1 | 0 | measured |
| `VastAsset2` | ARTIFACT | `adcp.types.core.VASTAssetInline` | `core/assets/vast-asset.json` | `#/oneOf/1` | **ALIAS** | 1 | 0 | measured |
| `VehicleUnit` | SPELLING | `adcp.types.core.VehicleItemMileageUnit` | `core/vehicle-item.json` | `#/properties/mileage/properties/unit` | **ALIAS** | 1 | 0 | measured |
| `VerifyBrandClaimsSignedResponse` | SPELLING | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponse` | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response` | **ALIAS** | 1 | 1 | measured |
| `Encoding` | ARTIFACT | `adcp.types.core.MacroEncoding` | `core/macro-encoding.json` | `#` | **MIGRATION_NOTE** | 0 (raw 6) | 1 | measured |
| `MediaBuyPackage` | SPELLING | `adcp.types.media_buy.GetMediaBuysResponseMediaBuysItemPackagesItem` | `media-buy/get-media-buys-response.json` | `#/properties/media_buys/items/properties/packages/items` | **ALIAS** | 0 | 1 | measured |
| `Path` | ARTIFACT | `adcp.types.core.RemoveTargetingSetValuesPath` | `core/targeting-modification.json` | `#/oneOf/1/properties/path` | **MIGRATION_NOTE** | 0 (raw 3) | 0 | measured |
| `Refine` | ARTIFACT | — | `media-buy/get-products-request.json` | `#/properties/refine/items` | **EMIT_CHANGE** | 0 | 1 | measured |
| `VerifyBrandClaimsPayload` | SPELLING | `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload` | `brand/verify-brand-claims-response.json` | `#/definitions/signed_response/allOf/1/properties/payload` | **ALIAS** | 0 | 1 | measured |

## 2. Two cross-tabs, two independent readings of the same 73 rows

**These are two readings, not one list.** The first asks what the NAME is relative to our
surface; the second asks what upstream's SYMBOL is in their own source. They are
independent, and the second is new — the previous pass had no `origin` column, so the
`EMIT_CHANGE` and `LEGACY_LAYER` concentrations below could not be seen at all.

### 2a. category × action — what the name is relative to our surface

| category | ALIAS | LEGACY_LAYER | EMIT_CHANGE | MIGRATION_NOTE | NONE | total |
| --- | --- | --- | --- | --- | --- | --- |
| **SPELLING** | 38 | 0 | 3 | 0 | 0 | **41** |
| **ARTIFACT** | 15 | 0 | 6 | 4 | 1 | **26** |
| **MACHINERY** | 1 | 2 | 0 | 0 | 1 | **4** |
| **SAME_BUT_NOT** | 0 | 1 | 0 | 0 | 0 | **1** |
| **NO_SUBJECT** | 0 | 1 | 0 | 0 | 0 | **1** |
| **total** | **54** | **4** | **9** | **4** | **2** | **73** |

Read it this way: **`SPELLING` is the mass of the work and it is nearly all alias** (38 of
41) — upstream has a different word for a node we already emit, and a re-export settles it.
**`ARTIFACT` is where the emission holes are** (6 of the 9 `EMIT_CHANGE`): a generator
ordinal usually means an anonymous node, and an anonymous node is where our compiler was
likeliest to have skipped a declaration or widened one. The three non-`ARTIFACT`,
non-`SPELLING` categories hold five rows between them, and four of those five are
`LEGACY_LAYER` or `NONE` — which is the shape reading 10 predicts: a name with no node
behind it never becomes a class.

### 2b. origin × action — what upstream's symbol is in their own source

| origin | ALIAS | LEGACY_LAYER | EMIT_CHANGE | MIGRATION_NOTE | NONE | total |
| --- | --- | --- | --- | --- | --- | --- |
| **GENERATED** | 27 | 0 | 6 | 2 | 1 | **36** |
| **TYPE_ALIAS** | 23 | 3 | 3 | 0 | 0 | **29** |
| **FACTORY_BUILT** | 3 | 0 | 0 | 1 | 0 | **4** |
| **CONSTANT** | 1 | 1 | 0 | 0 | 1 | **3** |
| **HAND_WRITTEN** | 0 | 0 | 0 | 1 | 0 | **1** |
| **total** | **54** | **4** | **9** | **4** | **2** | **73** |

Read it this way, and it is the finding the column was added for: **`GENERATED` origin
concentrates every `EMIT_CHANGE` but three** (6 of 9), because a name their generator minted
from an ordinal is a name whose node has no title — and an untitled node is what our
compiler either declines to declare (`GroupFormatAssetUnion`) or declares with a keyword
dropped (`DaastAsset1/2`, `CanonicalParameters`, `RequestProposalsResponse4`). **Every
`LEGACY_LAYER` row is `TYPE_ALIAS` or `CONSTANT`** — a hand-written expression upstream
composed for itself, which is precisely the thing that has no single object to alias onto.
And **`FACTORY_BUILT` is the origin that most changed the verdict**: all four of these rows
were `NO_SUBJECT` before, because the previous pass could not follow a `vars()` scan to a
class, and three of them turned out to be an ordinary alias once an agent ran the factory.

## 3. The probed count

**72 of 73 rows were probed. One was not: `DOMAINS`.**

A probe means payloads were offered in BOTH directions — one the document admits and one it
refuses — and the class's answer recorded. **65 of the 72 probed a class of ours found at
the document's pointer.** Seven rows have no class there and say what they probed instead,
rather than claiming a class they do not have; two further rows (`DaastAsset1`, `Pass`) do
have one and probed something additional, because the class alone does not answer the name:

| row | what was probed, where no class at the pointer could answer |
| --- | --- |
| `GroupFormatAssetUnion` | the 21-arm union our tree carries as an inline ANNOTATION on `RepeatableGroupAsset.assets`, plus the document itself at the pointer: it admits the 21 declared `asset_type`s and refuses `vendor_widget`, and so does our annotation. 0 symbols carry the pointer — §7. |
| `CanonicalParameters` | the field, `Format.canonical_parameters`, which is where we lower the node in place. That probe is what found the silent widening (§7). |
| `GeographicPlaceIdentifierSystem1` | the CONTAINING `anyOf` (`core.GeographicPlaceIdentifierSystem`) and `get_args` over it, because the arm is untitled and has no symbol of its own. |
| `DaastAsset1` | `DAASTAssetUrl` at the sibling pointer (clean in both directions) AND `AssetVariantDaast` at the arm upstream's name actually targets, which accepts three payloads the document refuses. |
| `Row` | the absence, measured: no class at `#/definitions/Row`, the entry named by no `$ref` in the bundle, and `adcp.types.Component.Row` confirmed to be the component NAME and not its props. |
| `Pass` | reachability on upstream's own wheel — `adcp.types.Pass` raises `AttributeError` — plus our `PassItemUrl` refusing their invented `type` default. |
| `IdentityMatchTmpxMacro`, `ProviderRegistrationTmpxMacro` | the two live documents the 3.1-era pair split into (`TMPXChunk.value`, `PublisherTMPXMacroMapping`), each probed and each shown NOT to be an alias target — the mapping admits lowercase, which upstream's only call site requires to raise. |
| `FIELDS` | the absence: `adcp.types.versioned_bases`, `._v32` and `.versioned` all raise `ModuleNotFoundError` here, and nothing is owed. |

**`DOMAINS` is the one row that could not be probed, and the reason is in its own column:
there is no document and no pointer, so there is no payload a document admits and none it
refuses.** It is a tuple of 26 strings naming generator output directories; a constant
cannot be offered one. What was measured instead is operational and is in the row: the live
`AttributeError` on `adcp.types.domains.DOMAINS`; the candidate expression evaluating to 23
names; `importlib.import_module` succeeding for 23 of 23 through our mirror; the three
upstream-only entries (`brand_discovery`, `manifest`, `manifest_schema`) having no directory
in `schemas/cache/3.2`; and `pkgutil.iter_modules` over `_schemas` yielding 24 children —
the 23 domains plus `common`, our catalogue home — against `_surface`'s exact 23, which is
what decides the namespace the expression must read.

**No row is still `joined`.** The previous pass's `joined` basis meant a document+word match
with nothing offered to a class; all 69 such rows are re-decided above and 68 of them are
now `measured` by probe, `DOMAINS` being the single row whose subject admits no probe at all.

## 4. The corrections — what moved, and what moved it

**This section is the evidence that one agent per name was worth its cost.** 30 of the 73
rows changed category, action or both; 17 rows changed their stated SUBJECT — the document,
the pointer or the dotted path — 2 of them while keeping their verdict; and 41 rows had both
verdict and subject confirmed by probe rather than by join. The previous pass's 17 `NO_SUBJECT` rows are the single
largest block of error, and they were not a vocabulary quibble: a `NO_SUBJECT` row gets a
migration note, so **12 names that are an ordinary re-export of a class we already emit were
on their way to being answered with a paragraph of prose.**

### 4a. Every row whose verdict moved

| name | category: was → is | action: was → is | what moved it |
| --- | --- | --- | --- |
| `AssetInstance` | NO_SUBJECT → SPELLING | ALIAS → ALIAS | The document's ROOT *is* the union: `core/assets/asset-union.json#` carries a 21-arm `oneOf`, `discriminator: {propertyName: "asset_type"}` and `x-adcp-hoist: true`, and we emit it as `AssetVariant` with 21 branch classes. The old pointer — "`#/oneOf` (members, not the union)" — denied a node the document states at `#`. |
| `AssetInstanceType` | NO_SUBJECT → SAME_BUT_NOT | MIGRATION_NOTE → LEGACY_LAYER | The vocabulary IS schema-stated, once per arm, as each branch's `asset_type` `const` — 21 values. Upstream's 20 are the key set of a DATA registry (`creative/asset-types/index.json`), and the nearest flat enum of ours is a DIFFERENT subject (the format-SLOT vocabulary, 22 values including `object`, which no asset payload can carry). Same values, not the same thing: `SAME_BUT_NOT`. |
| `CanonicalFormatKindStr` | NO_SUBJECT → MACHINERY | MIGRATION_NOTE → LEGACY_LAYER | `core/canonical-format-kind.json#` is the 16-value vocabulary and we emit it as `core.CanonicalFormatKind`. The name is three lines of validator machinery over that enum, and upstream's own `MIGRATION_v8_to_v9.md:18` and `docs/canonical-format-kinds-migration.md:25` instruct adopters to import it — a prose note leaves those instructions broken. |
| `CanonicalParameters` | ARTIFACT (confirmed) | UNDECIDED → EMIT_CHANGE | A probe. `Format.model_validate` ACCEPTS a `canonical_parameters` carrying `tracker_execution_contract_digest`, which the document's `not` refuses, and the key is silently dropped — our class is wider than its document and records no `Approximation` for it (§7). |
| `DOMAINS` | MACHINERY (confirmed) | NONE → LEGACY_LAYER | "Nothing owed" was refuted by measurement: 3 kept test files and `scripts/export_resolution.py` read it, two of our own verdict files already record the resulting collection error as open, and the roster is derivable from our emission (23 names, 23/23 importing through the mirror). |
| `DaastAsset1` | ARTIFACT (confirmed) | ALIAS → EMIT_CHANGE | Chasing the name to the arm it actually targets. `AssetVariantDaast` subclasses the `$ref` target's root, so the target's own `oneOf`/`discriminator` is SHADOWED through the MRO: `delivery_type`, `url` and `content` are not fields at all and `{"asset_type":"daast"}` is accepted. The alias is still owed. |
| `DaastAsset2` | ARTIFACT (confirmed) | ALIAS → EMIT_CHANGE | The same hole from the inline side, with the population bounded: exactly 4 `$ref`-only arms in the bundle whose target states its own combinator, all in `asset-union.json` (`#/oneOf/3`, `/4`, `/12`, `/16`). |
| `File` | ARTIFACT (confirmed) | ALIAS → EMIT_CHANGE | `from adcp.types.domains.brand.get_brand_identity_response import File` — the exact import their kept test writes — raises `ImportError`, while ten sibling words in that module bind. Two causes, both measured: the published-word join reads only the module's OWN declarations, and the structural key treats a hoisted `StrEnum` and an inline `Literal` as different structures. |
| `FormatAssetUnion` | NO_SUBJECT → SPELLING | MIGRATION_NOTE → ALIAS | The node is `core/format.json#/properties/assets/items`, with its own `discriminator: {propertyName: "item_type"}` — not "a union over numbered `Assets*`", which named their arm classes. Our `AssetsItemIndividual \| RepeatableGroupAsset \| UnknownFormatAsset` reproduces all three of their measured outcomes. |
| `GetProductsResponseUnion` | NO_SUBJECT (confirmed) | MIGRATION_NOTE → LEGACY_LAYER | The category stands — `manifest.json#/tools/get_products` is a tool entry and no node states the union — but the name's whole function is to be an ANNOTATION their caller pattern-matches on, and that is an expression over four document roots we emit. A note would break `typing.get_args`. |
| `GroupFormatAssetUnion` | NO_SUBJECT → SPELLING | MIGRATION_NOTE → EMIT_CHANGE | The node is at `#/properties/assets/items/oneOf/1/properties/assets/items`, probed in both directions; our tree states it ONLY as an inline annotation and **0 symbols carry the pointer**, which is why this is an emit change and not an alias. Our own `survey/probes/sitecustomize.py:121` already recorded the pointer. |
| `IdentityMatchTmpxMacro` | NO_SUBJECT → ARTIFACT | MIGRATION_NOTE (confirmed) | `origin`. The class is not generated and not hand-written on their surface: `post_generate_fixes.py:4728` INJECTS it into a generated file as a source string, and its word comes from the forbidden key `tmpx_macros`. The note stands, and the row now says why an alias is impossible rather than only that it is. |
| `ImageFormatAsset` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | Running the factory. `_format_asset_class("image")` resolves to `core.format:Assets` — their own fixture says so — which is the slot at `#/properties/assets/items/oneOf/0/oneOf/0`, and we emit it as `IndividualImageAsset`. "Factory-built, no node located" was a failure to execute one import. |
| `ImageFormatGroupAsset` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | The same factory with `group=True` → `Assets31` → our `GroupImageAsset` at `…/oneOf/1/properties/assets/items/oneOf/0`. Its 13 siblings follow mechanically. |
| `LegacyProductFormatDeclaration` | NO_SUBJECT → SPELLING | MIGRATION_NOTE → ALIAS | The DOCUMENT was wrong, not just the verdict: following `legacy.py:153` to its end lands on `core/product-format-declaration.json#`, a live 16-arm discriminated union we emit — not `core/format.json`, which is the deprecated v1 document the previous pass named. |
| `Pass` | ARTIFACT (confirmed) | ALIAS → NONE | Reachability, measured on their own wheel: `_generated.py:5473` declares `"Pass"` in `__all__` and `adcp.types.Pass` raises `AttributeError`. The only path that resolves is the underscore-private one their own layering forbids importing, so no consumer contract rides on the spelling and nothing is owed. |
| `PrincipalReadResult` | NO_SUBJECT → SPELLING | ALIAS → ALIAS | The `result` property IS a node — `protocol/get-principal-response.json#/properties/result`, a 4-arm `oneOf` — and the previous pass pointed at the *sync* document while describing the *read* union. |
| `PrincipalSyncResult` | NO_SUBJECT → SPELLING | ALIAS → ALIAS | Same correction, 3 arms at `protocol/sync-principal-response.json#/properties/result`; measured equal to `SyncPrincipalResponse.model_fields['result'].annotation`, arm for arm and in order. |
| `ProviderRegistrationTmpxMacro` | NO_SUBJECT → ARTIFACT | MIGRATION_NOTE (confirmed) | `origin` HAND_WRITTEN, and the strongest evidence in the set: all 30 cached copies of `provider-registration.json` were enumerated and none ever carried a macro-name property, so the class is a shim for a node that never existed in any version upstream itself caches. |
| `PublisherDomain` | ARTIFACT (confirmed) | UNDECIDED → ALIAS | "Two instruments disagree" was four byte-identical scalar classes of upstream's own making. In the bundle a run reads, every `publisher_domains` items node is a `$ref` to `core/domain-name.json`, and upstream's own test asserts the four classes have the identical JSON schema. There was nothing to be undecided about. |
| `RefineProposalsResponse1` | ARTIFACT (confirmed) | ALIAS → EMIT_CHANGE | The ordinal is ADMISSIBLE (it is upstream's published word) yet unbound: `Emitted.unbound[…]['RefineProposalsResponse1'] == 'unmatched'` because we pin `const` as a `Literal` over an enum MEMBER and the structural key records no pin for it. 55 published words bind once that one reader resolves the member's value. |
| `RepeatableAssetGroup` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | Running `_repeatable_asset_group_class()`: it returns `Assets29` at `core/format.json#/properties/assets/items/oneOf/1`, which we emit as `RepeatableGroupAsset`. |
| `RequestProposalsResponse4` | ARTIFACT (confirmed) | ALIAS → EMIT_CHANGE | A probe of the arm class: the root states `additionalProperties: false` over 16 properties, the arm takes `CompactTaskSubmitted` as a second base, and 7 keys the root closes become declared fields — so `context_id` and `timestamp` are accepted where the document refuses them. Population exactly 3, all public. |
| `Row` | ARTIFACT (confirmed) | EMIT_CHANGE → MIGRATION_NOTE | `#/definitions/Row` is an entry in the bundle's one DEAD `definitions` section — 11 entries that no `$ref` in 3.2 names. No instance location is governed by it, so no class can be wider or narrower than it, and emitting one is forbidden by our own decision. An emit change would have minted a class for nothing. |
| `SyncCatalogResult` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | Asking the interpreter which branch of `try: … except ImportError:` is live. The `try` wins, so the subject is the generated per-catalog ROW at `#/oneOf/0/properties/catalogs/items` — not a "hand-written union". |
| `SyncCreativeResult` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | The same `try/except` read to its end (see 4c). |
| `UpdateMediaBuyErrorResponse` | SPELLING (confirmed) | ALIAS → EMIT_CHANGE | A probe: `{'status':'submitted','errors':[…]}` is ACCEPTED by our error arm and refused by the document. The arm's `not.anyOf` has five disjuncts; the fifth conjoins `required` with a `const`, contributes no group to `ForbiddenGroups`, and is dropped with no `Approximation` recorded. 62 nodes in 46 documents share the shape. |
| `UrlDaastAsset` | ARTIFACT → SPELLING | ALIAS → EMIT_CHANGE | Two moves in one row. SPELLING because the word is hand-written in `aliases.py` from the document's own title and the arm's own `const`, on their deliberate flat surface — the ordinal is its TARGET, which the table carries separately. EMIT_CHANGE because the arm class at the pointer their alias names is wider than the document, undeclared. |
| `UrlVastAsset` | ARTIFACT → SPELLING | ALIAS → ALIAS | The same category argument; the alias target itself was right and probes clean. |
| `VendorPricingOptionUnion` | NO_SUBJECT → SPELLING | UNDECIDED → ALIAS | See 4c. The document's own ROOT is the union; "no node states the union" was false of `core/vendor-pricing-option.json#`, which upstream's own generator reads to build the five-arm `Annotated`. |

### 4b. The 17 `NO_SUBJECT` rows, and what they actually were

`NO_SUBJECT` means **the schema states no node for this name, so no class is owed and the
answer is prose.** It is the one category that decides an action by itself, which is why
getting it wrong is expensive. Of the previous pass's 17:

* **12 are `SPELLING`** — an ordinary second word for a node we already emit:
  `AssetInstance`, `FormatAssetUnion`, `ImageFormatAsset`, `ImageFormatGroupAsset`,
  `LegacyProductFormatDeclaration`, `PrincipalReadResult`, `PrincipalSyncResult`,
  `RepeatableAssetGroup`, `SyncCatalogResult`, `SyncCreativeResult`,
  `VendorPricingOptionUnion` (11 of them now `ALIAS`), and `GroupFormatAssetUnion`, whose
  node exists and whose declaration does not (`EMIT_CHANGE`).
* **2 are `ARTIFACT`** — `IdentityMatchTmpxMacro` and `ProviderRegistrationTmpxMacro`, both
  still `MIGRATION_NOTE`. These are the rows the category was *written* for, and they are
  the two where it held.
* **1 is `MACHINERY`** — `CanonicalFormatKindStr`: the vocabulary is a document, the carrier
  is machinery over it.
* **1 is `SAME_BUT_NOT`** — `AssetInstanceType`: a vocabulary that exists per-arm in the
  schema, whose nearest flat spelling of ours is a different subject.
* **1 is `NO_SUBJECT` confirmed** — `GetProductsResponseUnion`. Exactly one of the
  seventeen survived.

**Four of the twelve were mis-decided for one mechanical reason: nobody ran the code.**
`ImageFormatAsset`, `ImageFormatGroupAsset` and `RepeatableAssetGroup` are built by a
factory that scans `vars(adcp.types.domains.core.format)` at import; `SyncCatalogResult` and
`SyncCreativeResult` are behind a `try/except ImportError` whose live branch only an
interpreter can tell you. "Factory-built, no node located" and "hand-written union; members
not resolved" are both descriptions of an unexecuted import.

### 4c. The three rows whose verdict contradicted itself, and the two that were plainly wrong

**`NO_SUBJECT` + `ALIAS` cannot both hold.** An alias is a second NAME for one of our
classes; if no node is stated there is no class to name, which is why `NO_SUBJECT`'s action
is a note. Three rows carried the pair: `AssetInstance` ("union over our 11 asset classes"),
`PrincipalReadResult` ("union over our 4 principal-result classes") and `PrincipalSyncResult`
("union over our 3"). The giveaway is in the cells themselves — each names classes of ours
to alias onto while the category says there is nothing to alias. All three are `SPELLING`
here, with the node they denied: `core/assets/asset-union.json#` (a `oneOf` with a
`discriminator` and `x-adcp-hoist: true`), `protocol/get-principal-response.json#/properties/result`
and `protocol/sync-principal-response.json#/properties/result`. `AssetInstance`'s arm count
also moved, from "our 11 asset classes" to the document's 21.

**`SyncCreativeResult` — both subjects exist and the previous pass named neither.** It was
`NO_SUBJECT` / `UNDECIDED`, reason "hand-written union; members not resolved". There is no
union: `aliases.py:733` is a one-line `TypeAlias` onto `SyncCreativeResultInternal`, bound
218 lines earlier by a `try/except ImportError` pair, and the `try` branch resolves on their
shipped wheel to the generated row class `domains/creative/sync_creatives_response.Creative`.
The row is stated at `creative/sync-creatives-response.json#/oneOf/0/properties/creatives/items`
and we emit a class there. Their own production consumer validates one row per loop
iteration with it (`src/adcp/server/_creative_batch.py:40`), and their own fixture records
the terminus (`public_api_snapshot.json:566`). **The brief this pass was given also
overstated the defect, and the row corrects it:** upstream as shipped is RIGHT — alias,
docstring and usage all mean the row. What is wrong is the `except ImportError` fallback at
`aliases.py:519`, which silences a missing subject into a DIFFERENT subject one level up
(the response ROOT), so a module rename would start validating rows against a three-arm
envelope with no import error to say why. That is latent, not live, and it is the defect
§6 records.

**`VendorPricingOptionUnion` — the subject is the document's own root.** It was `NO_SUBJECT`
/ `UNDECIDED`, reason "no node states the union". `core/vendor-pricing-option.json#` states
exactly that union: an `allOf` of one object (`required: ['pricing_option_id']`) and a `$ref`
to `core/signal-pricing.json`, a five-arm `oneOf` with `discriminator: {propertyName:
'model'}`. Upstream's own generator reads that document and writes the five-arm `Annotated`;
their `aliases.py:155-160` then publishes it under BOTH spellings with the comment "Both
public spellings refer to the schema's union." We emit it as `core.VendorPricingOption` with
`__adcp_schema__ = SchemaRef(document='core/vendor-pricing-option.json', pointer='#')`. The
row also found the production demand the previous pass missed: `src/adcp/migrate/v3_to_v4.py:418`
maps `("core.vendor_pricing_option", "VendorPricingOption")` to the string
`"adcp.types.VendorPricingOptionUnion"`, so the v3→v4 codemod WRITES this dotted path into
adopters' source — a public destination no import walk sees, and our tree carries the
identical line.

### 4d. Two rows whose verdict stood while the subject moved

* **`AcceptedLoss`** — previously `media-buy/request-proposals-response.json#/properties/purchase_continuation/oneOf/1/properties/losses/items`.
  Upstream declares it in `domains/media_buy/legacy_purchase_continuation_input.py` and uses
  it there, so the stating document is `media-buy/legacy-purchase-continuation-input.json#/properties/accepted_losses/items`.
  Same vocabulary, same alias target, different document — and the note should say so,
  because the two positions are two documents and only one of them declares the enum.
* **`ListCreativesCanonicalCreative`** — previously aliased onto the ITEMS class
  (`ListCreativesResponseCreativesItem`). The name denotes the arm, and we emit the arm:
  `ListedCreativeCanonicalFormatKind` at `#/properties/creatives/items/oneOf/1`. Upstream's
  own two aliases collapse to one class (§6), so aliasing onto the items node would have
  reproduced their defect instead of recording it. Its sibling `ListCreativesLegacyCreative`
  keeps the items class, because that is the node their test actually isinstance-checks.

## 5. The legacy layer

**WHAT IT IS AND WHERE IT LIVES.** Four rows need an EXPRESSION over our emitted types, not
a re-export of one of them. They go in **`src/adcp/types/compat.py`** — the one hand-written
module reading 10 allows for a flat legacy spelling — except `DOMAINS`, which is a module
ATTRIBUTE and belongs in the emitted mirror's authoring home, `codegen/mirror/domains.py`.
Two of the four additionally owe a line in `src/adcp/types/aliases.py`, because upstream's
own kept machinery and tests import `from adcp.types.aliases import <Name>` at module scope.
Both of those files are GENERATED (`survey/adapter_surface.py`), so a row is driven from
`survey/adapter-surface-9.6.1.tsv` and regenerated — never hand-edited.

**THE CONSTRAINT THIS SECTION EXISTS TO HOLD — `final-state.md` reading 10's preamble.** A
legacy entry **must not become a permanent public commitment to a name the protocol never
had**, and it **must not reshape an emitted class to be convenient**. So every entry below
obeys three rules:

1. **It declares no class.** Each is a `TypeAlias`, an `Annotated[...]`, or a module
   `__getattr__` — a NAME over types the compiler emitted, and never a second type.
2. **It is derived, not kept.** Each expression is computed from the emitted tree (arm
   consts read off `_branch_models`, the roster read off `_surface`), so a schema bump moves
   it and no hand-maintained list can fall behind the document the way upstream's 20-value
   `Literal` and 26-name tuple did.
3. **It carries a migration note naming what the protocol does and does not state**, so the
   name is documented as a compatibility spelling with an expiry, not as protocol
   vocabulary.

**HOW A READER TELLS A LEGACY ENTRY FROM AN ALIAS.** An alias has a single `__adcp_schema__`
behind it: `X = Y` where `Y` is one emitted class, so `X is Y` holds, `isinstance` works, and
`X.__adcp_schema__` names the document and pointer the name resolves to. A legacy entry has
NO single object: `typing.get_args` on it returns several classes or several strings, there
is no `__adcp_schema__` to read, and `isinstance(x, X)` either fails or means something
weaker than membership of one node. Mechanically: **if it lives in `compat.py` and has no
`__adcp_schema__`, it is a legacy expression, and the entry must say which nodes it was
composed from.** The four:

| name | the expression, over our types | why no alias is possible |
| --- | --- | --- |
| `AssetInstanceType` | `Literal[` the `asset_type` const of each arm of `adcp.types.core.AssetVariant`, in `#/oneOf` order `]` — 21 strings, derived from `AssetVariant._branch_models` | There is no symbol for a vocabulary that the schema states 21 times, once per arm. The one flat enum with these values (`CanonicalFormatBaseSlotsItemAssetType`) is a different node and admits `object`, which no asset payload can carry. |
| `CanonicalFormatKindStr` | `Annotated[str, AfterValidator(require_canonical_format_kind())]`, where the factory closes over `adcp.types.core.CanonicalFormatKind` | The subject is a validator, not a type: aliasing the name onto the enum passes every runtime assertion of theirs and breaks their static contract, and their own docs say the annotation "is still a `str`". |
| `GetProductsResponseUnion` | `GetProductsResponse \| GetProductsSubmitted \| GetProductsWorking \| GetProductsInputRequired`, all from `adcp.types.media_buy` | No node states the union — `manifest.json#/tools/get_products` is a tool entry. Their only consumer runs `typing.get_args` over it, which a note cannot serve and a single class cannot answer. |
| `DOMAINS` | a module `__getattr__` on `adcp.types.domains` returning `tuple(sorted(m.name for m in pkgutil.iter_modules(adcp.types._surface.__path__) if not m.name.startswith("_")))` — measured: 23 names, 23/23 importing | It is not a type at all. `_surface` and not `_schemas`, measured: `_schemas` yields 24 children, the 24th being `common`, our catalogue home, which the mirror would then advertise as a domain. |

**Two things the legacy layer must SAY, not silently absorb.** `AssetInstanceType` is 21
values where upstream's is 20: it is one value WIDER, so nothing they pass is refused, and
the extra value is `display_tag`, an arm the document declares and their `Literal` refuses
(§6). `DOMAINS` is 23 names where upstream's tuple is 26: `brand_discovery`, `manifest` and
`manifest_schema` have no directory in `schemas/cache/3.2` and no module in `_schemas`, so
`tests/test_generated_poc_alias.py:139`'s `assert len(domains.DOMAINS) == 26` cannot be
satisfied by any honest binding over a 3.2 closure. The note must say 23-not-26 and why, or
that assertion turns a collection error into a mystery failure.

**And one finding larger than the row it was found in.** Binding `DOMAINS` is necessary and
not sufficient: our mirror's domain ROOTS are empty. `adcp.types.domains.core` resolves to a
0-byte `_schemas/core/__init__.py`, so `from adcp.types.domains.core import DomainBreakdown`
raises `ImportError` while `adcp.types.core.__all__` holds 1,540 names including it. Four
kept test files import from a domain root at module scope. Fixing `DOMAINS` without fixing
root resolution converts one honest collection error into 23 parametrised failures; both
halves belong in one change to `codegen/mirror/`.

## 6. Where upstream contradicts itself

**32 of the 73 rows have `upstream_is_wrong` filled, and the rule for all 32 is the same:
let their code keep working through an alias onto what their CODE actually uses — never onto
what their comment says — and record the defect in the migration note.** We do not port a
defect to be compatible with it and we do not loosen an emitted class to make a lax call
site pass. Where our class is stricter, the note gives the corrected pattern.

The 32 split into two kinds, and the distinction matters because only the first kind is a
contradiction they could find themselves:

* **6a — their own two statements disagree** (a comment, docstring or test against their own
  binding or their own usage): 18 rows.
* **6b — their class disagrees with the document they generate it from** (a `const` turned
  into a default, a `not` dropped, a base widening a closed key set): 14 rows. Their words
  are consistent; the schema is the witness.

`ImageFormatGroupAsset` and `RepeatableAssetGroup` appear under both headings, because their
rows record both kinds. 18 + 14 = 32 with those two counted once each.

### 6a. Their own two statements disagree

**`AssetInstance`** — the comment calls it the inner union; the binding is one arm short.
* `aliases.py:358` — "``AssetVariant`` remains the generated Pydantic RootModel used for runtime validation; ``AssetInstance`` is the inner union …"
* `aliases.py:361-383` — 20 arms, `DisplayTagAsset` absent, against `domains/core/assets/asset_union.py:3239`'s own 21-arm `AssetVariant`, `DisplayTagAsset` among them.
`core/assets/asset-union.json#/oneOf/4` is `display-tag-asset.json`, not deprecated, `const: "display_tag"` — a wire value their public union rejects, and `grep DisplayTagAsset` over their `aliases.py`/`__init__.py` returns nothing, so adopters have no name for it either. Their own `tests/test_public_api.py:44-65` codifies the 20 as a set EQUALITY. We bind the document's 21 and record the defect; the same comment's second claim ("the generated Pydantic RootModel") is also false — `AssetVariant` is an `Annotated` union there, not a `RootModel`.

**`AssetInstanceType`** — the comment claims exhaustiveness the binding does not have.
* `tests/type_checks/asset_instance_narrowing.py:10` — "# AssetInstanceType alias supplies the exhaustive discriminator values."
* `aliases.py:384` — a `Literal` of 20 strings with `"display_tag"` absent.
Root cause is in the bundle and not invented by them: `asset-union.json`'s own text says "Add new asset types here and to the creative/asset-types registry", and `display_tag` was added to the union but not to `creative/asset-types/index.json`, so their 20 faithfully tracks a stale registry. The legacy layer is one value WIDER, so nothing they pass is refused (§5).

**`AuthorizedAgents`** — the comment says a union of four; the binding and every call site say one arm of six.
* `aliases.py:1304-1305` — "The AdCP adagents.json schema defines AuthorizedAgents as a discriminated union with four variants based on the `authorization_type` field", enumerating exactly four.
* `_eager.py:996` — `from adcp.types.domains.adagents import AuthorizedAgents1 as AuthorizedAgents`, a single `property_ids` arm, while the document states SIX arms at that items pointer (`signal_ids` and `signal_tags` are the two the comment omits — and their own `aliases.py:1283-1287` imports both).
We alias onto the arm their code uses. The note must say that in `adcp.types` the PLURAL `AuthorizedAgents` is one `property_ids` row while the SINGULAR `AuthorizedAgent` is the six-arm union, and that the correct way to name an arm is its pointer, not a generator ordinal that shifts when an arm is added at the front.

**`AuthorizedAgentsByPropertyTag`** — the governing comment block is stale against its own sibling binding.
* `aliases.py:1302` — "a discriminated union with four variants", then four names.
* `aliases.py:1501-1508` — `AuthorizedAgent = …ByPropertyId | …ByPropertyTag | …ByInlineProperties | …ByPublisherProperties | …BySignalId | …BySignalTag` — six, which is what `items.oneOf` states.
The binding for this name is right; the count in the note must be six.

**`AuthorizedAgents3`** — one spelling, two different arms, in their own tree.
* `_generated.py:3698` — `AuthorizedAgents3 = _GeneratedAuthorizedAgents4` → `publisher_properties`.
* `domains/adagents.py:629` — `class AuthorizedAgents3(…): authorization_type: Literal['inline_properties']`.
Their own fixture pins both readings side by side (`public_api_snapshot.json:2268` `"AuthorizedAgents3": "adagents:AuthorizedAgents4"` against `:106` `"AuthorizedAgentsByInlineProperties": "adagents:AuthorizedAgents3"`), and their `aliases.py:1272-1281` names the hazard itself — binding through the shifted window "made every documented constructor call fail ``mypy --strict``". Their test imports from `_generated` and builds `publisher_properties`, so the alias goes to `#/oneOf/3`. **A join on the name alone lands on `inline_properties`, and that is what our own census does** (`codegen/published.json` records one `AuthorizedAgents3`, module `adagents`, element `authorization_type="inline_properties"`) — the note must carry that sentence or the next pass re-derives the wrong arm.

**`DOMAINS`** — the roster contradicts its own comment and their own production imports.
* `domains/__init__.py:21` — `#: Every domain in this package.`
* `consolidate_exports.py:426` — the generator excludes one of the package's 24 directories: `and m.relative_to(DOMAINS_DIR).parts[0] != "bundled"`.
Their own HAND-WRITTEN machinery imports from the excluded domain at module scope (`capabilities.py:45`, `_forward_compat.py:68-80`), and `scripts/export_resolution.py` builds the public-API snapshot's namespace list FROM `DOMAINS` — so the snapshot never covers the one domain their non-generated code depends on, which is the exact failure that script's docstring says it exists to catch. Ours derives the roster from the tree at access time, so no domain their code imports can fall out of it.

**`GetProductsResponseUnion`** — one name, two different types depending on import path.
* `adcp.types.GetProductsResponseUnion` — first arm is `adcp.types.canonical_creative.GetProductsResponse`.
* `adcp.types.aliases.GetProductsResponseUnion` — first arm is `adcp.types.domains.media_buy.get_products_response.GetProductsResponse`.
Measured: the two are not `==`, and the former is a SUBCLASS of the latter (`canonical_creative.py:1157`, which retypes `products`). Their own docstring at `aliases.py:681-683` says "The public ``GetProductsResponse`` name remains the success class" while `:685` binds the base — so a value matched against the `aliases` spelling is not an instance of the public spelling's success arm. Their one test imports from `adcp.types` only and never sees the split. **Ours does not reproduce it**: we emit one class per document, so all three spellings resolve to the same four objects. Record it; do not re-create the subclass to mirror it.

**`IdentityMatchTmpxMacro`** — their injector calls the class dead; their only test presents it as the live wire value.
* `post_generate_fixes.py:4737` — "Retain those helpers as compatibility models; they are intentionally not referenced by the 3.1.10 response fields."
* `tests/test_collision_aliases.py:401-403` — "TMPX macro aliases distinguish emitted values from registered names. The emitted value is an object with ``name``/``value``."
Both cannot hold, and the pinned document settles it against the second: the emitted value is `{slot_id, value}` (`trusted-match/tmpx-chunk.json`, forwarded at `tmpx_providers[provider_id].chunks[]`) and `tmpx_macros` appears at the response root only inside a `not`. Nothing in their code passes data to the class, so an alias has nothing to alias and the defect belongs in the note.

**`ImageFormatGroupAsset`** — their own test refuses to trust the attribute their import-time resolver depends on.
* `aliases.py:1698` — `if field is not None and field.default == asset_type:`
* `tests/test_asset_aliases_stable.py:62-66` — "Parses the field's ``annotation`` … rather than reading ``FieldInfo.default`` — several generated discriminator fields declare the literal as the annotation without also setting a default, which would make ``FieldInfo.default`` return ``PydanticUndefined`` and any equality comparison vacuously pass."
If their generator ever stops emitting the default, `import adcp.types` raises `ImportError("Could not find generated format asset class for 'image'")`. This is also exactly why the factory must not be ported: our const has no default.

**`ListCreativesCanonicalCreative`** and **`ListCreativesLegacyCreative`** — the "split" they document does not exist in their bindings, and it makes their own test vacuous.
* `domains/creative/list_creatives_response.py:503-504` — `Creatives = Creative` / `Creatives1 = Creative`.
* `tests/test_collision_aliases.py:297-301` — "AdCP 3.1.8 split list_creatives response rows into legacy and canonical branches … the new item alias exposes the response union explicitly", and `:318` `assert a.ListCreativesCreativeItem == (Creatives | Creatives1)`.
Measured: `ListCreativesLegacyCreative is ListCreativesCanonicalCreative` is True, the "union" collapses to one class, and both `isinstance` asserts pass for either row — the test cannot fail on the branch it claims to check. `ListCreativesLegacyCreative.model_validate(canonical_row)` succeeds and returns a row with `format_kind` set. What they hold correctly is the XOR, hand-rolled as a `model_validator` rather than as the document's `oneOf`. So: the Legacy spelling aliases onto the ITEMS node their test isinstance-checks, the Canonical spelling onto the ARM it names, and the note gives the discriminating pattern (`isinstance(row, ListedCreativeCanonicalFormatKind)`, item union `ListedCreativeNamedFormatReference | ListedCreativeCanonicalFormatKind`).

**`MajorVersion`** — their own class graph contradicts the name.
* `domains/protocol/get_adcp_capabilities_response.py:65` — `class MajorVersion(ScalarInt)`, `_constraints = {'ge': 1}`.
* `domains/bundled/protocol/get_adcp_capabilities_response.py:3760` and `:4356` — `class AllowedValue(MajorVersion)` and `class AllowedInterval(MajorVersion)`.
A frequency-cap allowed value IS-A major version, because their generator reuses the first class it minted for `integer, minimum 1`. The name denotes the constraint, not the concept, which is our `constraints.py` rule stated from the other side. Secondary: `MajorVersion(root=3)`, written at three of their call sites, works only behind their own `DeprecationWarning`.

**`Pass`** — their own `__all__` claims an export their own facade refuses.
* `_generated.py:5473` — `"Pass"` in `__all__`.
* `import adcp.types; adcp.types.Pass` → `AttributeError`, and `hasattr(adcp.types._eager, "Pass")` is False.
The name is unreachable at every spelling a consumer was invited to write, which is why the action is `NONE`.

**`ProviderRegistrationTmpxMacro`** — the docstring asserts a node that never existed.
* `provider_registration.py:24` (written by `post_generate_fixes.py:4786`) — """Deprecated 3.1.8 registered macro-name compatibility model."""
* `trusted-match/provider-registration.json`, in all 30 cached copies — `"additionalProperties": false` with no macro-name property, ever; `tmpx_slots` appears from 3.1 with items pattern `^[a-zA-Z][a-zA-Z0-9_]*$`, never the uppercase macro pattern.
Their own schema text contradicts the concept too: `tmpx-chunk.json` says `slot_id` is an "opaque provider-namespaced token; … NOT an ad-server macro name."

**`PublisherDomain`** — the defect is stated as one of their own invariants.
* `tests/test_composability_invariant.py:91-92` — `assert canonical_model is not bundled_model` and `assert TypeAdapter(canonical_model).json_schema() == TypeAdapter(bundled_model).json_schema()`.
One scalar, five identity-distinct classes (4 in `domains/` + 1 bundled), held together at runtime by `_patch_equivalent_model_field` and by `scripts/collision_allowlist.json:218`. A duplication defect, not a mis-binding: the binding matches the usage and the alias is onto what their code uses.

**`RepeatableAssetGroup`** — the comment names a back-compat rename, not the class.
* `aliases.py:1680` — "``RepeatableAssetGroup`` (``Assets94``). Aliased as ``<Type>FormatGroupAsset``."
* `domains/core/format.py:2912` — `Assets94 = Assets29`, and their own `public_api_snapshot.json:1596` says `core.format:Assets29`.
The comment and the codemod table at `migrate/v3_to_v4.py:539` are stale by one renumber window — which is the renumber hazard this repository's own CLAUDE.md describes, visible in their tree.

**`SyncCreativeResult`** — the fallback branch names a different subject one level up.
* `aliases.py:519` — `except ImportError: SyncCreativeResultInternal = _g.SyncCreativesResponse`.
* `aliases.py:737` — `type SyncCreativeResult = SyncCreativesSuccessResponse["creatives"][number]`.
The live branch is the `try`, so this is latent rather than live; it is still a defect, because a missing row class would be silenced into a response ROOT with no import error to say why, and the response class is loose enough to take the row. The correct pattern is a per-row import with no envelope fallback — an unbound name a reader can act on.

**`UpdateMediaBuyErrorResponse`** — their binding accepts exactly the payload their own guard's docstring assigns to another branch.
* `guards.py:234-236` — """Returns False for the submitted (async) envelope, even if it carries advisory (non-blocking) errors. Use ``is_update_media_buy_submitted`` for that branch."""
* Measured: `UpdateMediaBuyErrorResponse.model_validate({'status':'submitted','task_id':'t','errors':[…],'media_buy_id':'mb_1'})` SUCCEEDS.
Our class refuses `media_buy_id` here and — after the §7 fix — the submitted envelope too.

### 6b. Their class disagrees with the document it is generated from

These need no quotation of two opinions: one side is the generated line, the other is the
pinned bundle. **The pattern behind 9 of the 15 is one generator pass** —
`inject_literal_discriminator_defaults`, which appends a default to every single-value
`Literal` and reads `required` nowhere (1,083 required-const properties affected;
`survey/invented-defaults-9.6.1.tsv` records 477 `const-restated` pairs). The consequence is
always the same and always in the same direction: **their class admits a payload the document
refuses, and ours does not**, so an alias makes a lax call site raise and the note must give
the corrected call.

| name | their line | the document | consequence for the alias |
| --- | --- | --- | --- |
| `AuthorizedAgentsByPropertyId` | `domains/adagents.py:257-259` `authorization_type: Literal['property_ids'] … = 'property_ids'` | `required: ['authorization_type', 'property_ids']` at that pointer | theirs fills the discriminator for a payload omitting it; ours requires it. Pass the discriminator. |
| `AuthorizedAgents2` † | `= 'inline_properties'` default on the same const | same `required` + `const` | identical; an adopter who omitted the keyword gets `Field required`. |
| `CoreAccount` | `destination_billing_entity: Annotated[Any \| None, …] = None` | `core/account.json#/properties/destination_billing_entity` is `{"not": {}}` — "Request-only staging field. It MUST NOT appear in account read models." | theirs round-trips a value its own description forbids; ours refuses that one key while still admitting other undeclared keys. The alias is an upgrade, not a like-for-like. |
| `CreateMediaBuySubmittedResponse` | `extra='allow'`, no rule for the arm's `not` | `#/oneOf/2` `not: {anyOf: [{required:['media_buy_id']},{required:['packages']},{required:['warnings']}]}` | their own docstring says "the ``media_buy_id`` is issued later on the completion artifact, not here" and their class returns it; ours raises. |
| `CreateMediaBuySuccessResponse` | `status: Literal['completed'] = 'completed'` | arm 0 declares NO `status` property; `status` reaches it only through the root's `allOf → core/protocol-envelope.json`, as the unconstrained 9-value `TaskStatus` | here theirs is NARROWER: `{"status":"failed", …}` validates at the root and at `/oneOf/0` and is refused by their `Literal`. Their pin encodes the document's PROSE; ours is the wider and faithful reading. |
| `UpdateMediaBuySuccessResponse` | `status: Literal['completed'] = 'completed'` (`update_media_buy_response.py:35`) | arm 0 declares no `status`; the envelope makes it REQUIRED over the whole enum, with no `default` anywhere | both an invented default and a narrowed enum. Correct pattern: pass `status='completed'`; carry a lifecycle value in `media_buy_status`. |
| `GetSignalsSubmittedResponse` | `status: Annotated[Literal['submitted'], Field(description='Task-level status literal. Discriminates this async envelope …')] = 'submitted'` | `required: ['status','task_id']`, plus a root `not` over `signals`/`result` | a field whose own description says it DISCRIMINATES accepts a payload omitting it, and the envelope retains the `signals` array it exists to say is absent. Ours refuses both. |
| `GetProductsSubmittedResponse` † | same injected default | `required: ['status','task_id']` and `not: {anyOf:[{required:['products']},{required:['proposals']},{required:['result']}]}` | measured: theirs accepts `{'task_id':'t'}` and keeps `products` as an extra; ours raises on both. |
| `UrlVastAsset` | `asset_union.py:2305` `= 'vast'`, `:2347` `= 'url'` | root `required: ['asset_type']`, `#/oneOf/0` `required: ['delivery_type','url']`, `const` with no `default` | `UrlVastAsset(url=…)` constructs there and raises two `missing` here. Correct pattern: `VASTAssetUrl(asset_type='vast', delivery_type='url', url=…)`. Do not add defaults to make their calls pass. |
| `UrlDaastAsset` | `asset_union.py:1664`/`:1698` the same two defaults (`survey/invented-defaults-9.6.1.tsv:302-303`, kind `const-restated`) | the same two `required` sets in `daast-asset.json` | one of their three test files cannot be made green by an alias, by decision: `REPORT AND DO NOT REPAIR` is the ruling for `const-restated`. |
| `DaastAsset2` | `aliases.py:1047` `InlineDaastAsset: TypeAlias = DaastAsset2` | — | their alias names a class their own public root never produces: `adcp.types.DaastAsset` is the `daast_asset.py` copy, so `isinstance(root.root, adcp.types.InlineDaastAsset)` is False. Ours serves one class per node, so the alias works on every route. |
| `ImageFormatGroupAsset` | `asset_type='image'` default | `required` on both the arm and `$defs/baseGroupAsset` | theirs accepts `{'asset_id':'img','required':True}`; ours requires the const. |
| `RepeatableAssetGroup` | `item_type: Literal['repeatable_group'] = 'repeatable_group'` | `#/properties/assets/items/oneOf/1` `required: ['item_type', …]` | same shape, measured both ways. |
| `RefineProposalsResponse2` | `refine_proposals_response.py:620` overrides its own base: `status: Status \| None = None`, `task_id: str \| None = None` | `#/anyOf/1` is a bare `$ref` to `core/compact-task-submitted.json`, `required: ['status','task_id']`, `status: {const: 'submitted'}` | the arm has ZERO required fields: `model_validate({})` succeeds, and `{"status":"completed"}` validates as the SUBMITTED arm. Their own test inspects this class and asserts only that `adcp_version` survived. We alias anyway — their code reaches the arm only through the union. |
| `RequestProposalsResponse4` | `request_proposals_response.py:402-403`, the same two restatements over `CompactTaskSubmitted` | same base document | `model_validate({})` and `{"status":"completed"}` both succeed; our own `verdicts/invented-defaults.md:1094,1213` already names the pair. Bind our stricter class; do not loosen it. |
| `CanonicalParameters` | `format.py:197` `class CanonicalParameters17(AdCPBaseModel): pass` — the `not` rendered as an EMPTY mixin, mixed into all 16 arms | `#/properties/canonical_parameters` `allOf: [$ref, {not: {anyOf: [{required:['tracker_execution_contract']},{required:['tracker_execution_contract_digest']}]}}]` | their own description says the two keys "are forbidden" and their class accepts both. Ours refuses one of them and silently drops the other — which is §7's row, and the only place in this section where ours is also wrong. |
| `Invoice` | `class Invoice(AdcpVersionEnvelope)` — `adcp_version` and `adcp_major_version` as declared fields, `extra='allow'` | the items node states six properties and refs no envelope; `core/version-envelope.json` is `allOf`-ref'd at the DOCUMENT ROOT only | their own test premise ("Schema-derived response arms should not widen structured fields") is graded on a class their generator widened by two keys. Neither direction is exercised by their call site. |
| `VendorPricingOptionUnion` | `class Metadata(AdCPBaseModel)` with `extra='allow'` and no property-count check | `core/signal-pricing.json#/oneOf/4/properties/metadata` states `"minProperties": 1` | their own test asserts the laxity (`{"model":"custom","description":"Usage tier","metadata":{}}`); ours refuses `metadata={}` with `PropertyCount(minimum=1)`. An upstream caller relying on it was relying on a codegen hole. |

† These two rows record the defect in their `use instead` column rather than in
`upstream is wrong`, because the agent read it as a behaviour delta the migration note owes
rather than as an upstream error. They are listed here so the pattern is complete; they are
NOT part of the 32. `CanonicalParameters` is the one row in this section where the document
convicts both sides — theirs for dropping the forbid entirely, ours for dropping one half of
it silently (§7).

## 7. Every `EMIT_CHANGE`, with its document, its pointer and the keyword we misread

**Nine rows are `EMIT_CHANGE`, and in every one the alias is ALSO owed.** `EMIT_CHANGE` does
not mean "withhold the name": it means chasing the name found a hole in OUR emission that is
recorded nowhere else, and the hole must not go unrecorded because an alias happens to make
upstream's test green. Four distinct keywords are involved, and three of the nine share one.

| # | name | document | pointer | the keyword we misread |
| --- | --- | --- | --- | --- |
| 1 | `DaastAsset1` | `core/assets/daast-asset.json` | `#/oneOf/0`, reached as `asset-union.json#/oneOf/12/oneOf/0` | the `oneOf` + `discriminator` of a document reached through a **bare `$ref` arm** of an outer union |
| 2 | `DaastAsset2` | `core/assets/daast-asset.json` | `#/oneOf/1` | the same |
| 3 | `UrlDaastAsset` | `core/assets/daast-asset.json` | `#/oneOf/0` | the same, found from the alias side |
| 4 | `GroupFormatAssetUnion` | `core/format.json` | `#/properties/assets/items/oneOf/1/properties/assets/items` | a nested union node — `oneOf` at an `items` position with nothing beside it but `discriminator` — whose SUBJECTHOOD we misread, not its contents |
| 5 | `RefineProposalsResponse1` | `media-buy/refine-proposals-response.json` | `#/anyOf/0` | `const` at `#/anyOf/0/properties/status`, lowered as a `Literal` over an enum MEMBER, which the structural key cannot pin |
| 6 | `RequestProposalsResponse4` | `media-buy/request-proposals-response.json` | `#/anyOf/3` | the ROOT's `additionalProperties: false` under a bare-`$ref` `anyOf` arm |
| 7 | `UpdateMediaBuyErrorResponse` | `media-buy/update-media-buy-response.json` | `#/oneOf/1` | `not` — a `not.anyOf` disjunct that conjoins `required` with `properties`/`const` |
| 8 | `CanonicalParameters` | `core/format.json` | `#/properties/canonical_parameters` | `not` over `anyOf`/`required` whose required name is **not a declared property** of the `$ref` target |
| 9 | `File` | `brand/get-brand-identity-response.json` | `#/oneOf/0/properties/fonts/definitions/font_role/oneOf/1/properties/files/items` | `enum` — the structural key treats a hoisted `StrEnum` and an inline `Literal` as different structures |

**1–3, the bare-`$ref` arm whose target dispatches.** `asset-union.json#/oneOf/12` is a lone
`{"$ref": ".../core/assets/daast-asset.json"}`, so the arm and the target root are one node
after resolution. We emit the arm as `class AssetVariantDaast(AssetVariant, DAASTAsset)`, and
`BranchDispatchMixin` rule 3 says the base is the class that DECLARES `_branch_models` — so
the target's own branch set is SHADOWED through the MRO: `AssetVariantDaast._BRANCH_DISCRIMINATOR`
is `'asset_type'` with 21 branches where `DAASTAsset`'s own is `'delivery_type'` with 2, and
`delivery_type`, `url` and `content` are not fields at all. Measured: `AssetVariantDaast.model_validate({'asset_type':'daast'})`
ACCEPTS, as do `{'asset_type':'daast','delivery_type':'url'}` with no `url` and
`delivery_type='bogus'` — three payloads the document refuses — while `strict_validate` and
our `DAASTAsset` root refuse all of them. The gate is `codegen/lower/union.py:3283`:
`distributes = … and not bound.declares.properties`, whose own comment claims "THE CONDITION
IS THE TARGET'S OWN FIELD SET AND NOT WHETHER IT DISPATCHES". `daast-asset.json` declares 8
properties AND dispatches, so it falls outside the gate and takes the two-base route that
`composition._distribute`'s docstring says is wrong for a dispatch root. **Population is
bounded: exactly 4 `$ref`-only arms in the bundle whose target states its own combinator**,
all in `asset-union.json` — `#/oneOf/3` (vast), `/4` (display-tag), `/12` (daast), `/16`
(published-post); three are measured pydantic-ACCEPT / document-REFUSE on the bare
`{'asset_type': …}`. It is reachable in production and not only through the exported
`AssetVariant`: `_schemas/core/localized_creative_asset.py:14` binds
`LocalizedCreativeAsset = Annotated[AssetVariant, …]`, and 47 bundle documents `$ref`
`asset-union.json`. Neither class carries `__adcp_approximations__`, so this is an
UNDECLARED widening and the declared-backlog ratchet cannot see it. **It also bounds the
alias's promise**: `isinstance(AssetVariant.model_validate(url_daast_payload), DAASTAssetUrl)`
is FALSE, while `DAASTAsset.model_validate(same)` dispatches and is True — upstream has no
such split, because their `DaastAsset1` IS the asset-union arm's url branch.

**4, the nested union node that gets no declaration.** The node's only keywords are
`discriminator` and a 21-arm `oneOf`. `rebuild-plan.md` §5's cell is "Shapes nested, with
nothing beside the combinator → one type `A | B`", and `discriminator`'s effect is
`Effect.NOTHING`, so the accepted SET is right — probed in both directions, 21 arms admitted
and `vendor_widget` refused, agreeing with the document — and what is misread is the node's
SUBJECTHOOD. Measured in the committed tree and in a fresh run of `python -m codegen`:
`_schemas/core/format.py:541` writes the same inline 21-arm union and **0 occurrences of the
pointer exist in either tree**. The consequence is shipped and is a false sentence handed to
a caller: `_adapter.py:309` refuses the word with "NO-DOCUMENT-NO-SUBJECT: upstream's
expression carries Annotated metadata to port", when the document, the pointer and our own
statement of the node all exist. Fixing it settles four names — `GroupFormatAssetUnion`,
`FormatAssetUnion`, `Refine` and `RefinementApplied` — and upstream's `aliases`, `_eager`,
`creative` and `domains/core/__init__` all import this word at MODULE SCOPE, so a drop-in
that cannot serve it fails at import, not at use.

**5, `const` pinned as an enum member.** `adcp.types.RefineProposalsResponse1` is unbound
(`Emitted.unbound['media_buy/refine_proposals_response']['RefineProposalsResponse1'] ==
'unmatched'`) even though the ordinal is ADMISSIBLE — the one admissible ordinal is
upstream's own published word. Cause: we lower the arm's `status` to
`Annotated[Literal[Status.COMPLETED] | None, OmittedNotNull] = None`, and
`codegen/structure._shape_and_pin` records a pin only when the `Literal`'s single element is
an `ast.Constant`, else returns `("literal", ())`. So our element reads
`['status','literal','','opt']` against upstream's `['status','','"completed"','']`, the
digests differ and `structure.bind` answers `unmatched`. **Counterfactual measured: resolve
the member to its value and the digests are EQUAL, `bind` returns the pair, and the
uniqueness checks still hold. Census over the committed tree: 55 published upstream words
bind once that one reader resolves the member** — including `RequestProposalsResponse1/2/3`,
all 20 `RegistryEvent<N>`, all 9 `WholesaleFeedEvent<N>` and 7 `ProposalRefinement<N>`. The
module already holds the machinery (`_value_lists`/`_member_value`); `_shape_and_pin` just
takes no vocabulary argument. Hand-writing the alias would patch 1 of 55 inside a generated
file.

**6, a closed root re-opened by an arm's base.** The root states 16 properties and
`additionalProperties: false`; `#/anyOf/3` is a bare `$ref` to `core/compact-task-submitted.json`,
and in draft-07 a sibling `anyOf` arm grants no exemption. Our arm class takes
`CompactTaskSubmitted` as a second base, so 7 keys the root closes become DECLARED fields —
`adcp_error`, `adcp_major_version`, `context_id`, `governance_context`, `payload`,
`push_notification_config`, `timestamp` — and `extra='forbid'` can no longer see them.
Measured: `{"status":"submitted","task_id":"t","context_id":"ctx_1","timestamp":"…"}` is
refused by the document and accepted by ours; entering through the root is still correct.
**Population is exactly 3, all public, all with `core/compact-task-submitted.json` as the
arm**: `RequestProposalsResponseSubmitted`, `RefineProposalsResponseSubmitted`,
`DeclineProposalsResponseSubmitted`. The grading missed it at the same keyword:
`applied_schema(doc, '#/anyOf/3')` returns a schema whose top level is `$ref`, so draft-07
ignores the conjoined root facts and the harness grades the arm alone —
`docs/plan/architecture.md` §13 item 3 already states the intent being missed.

**7, a `not.anyOf` disjunct that conjoins `required` with a `const`.** The arm's `not.anyOf`
has FIVE disjuncts; the fifth is `{"properties": {"status": {"const": "submitted"}},
"required": ["status"]}`. `codegen/lower/rules.py:676` `_negated` reduces the `not` through
`_required_groups`, which answers `[('media_buy_id',),('affected_packages',),('sandbox',),('warnings',)]`
partially and `None` strictly; the fifth disjunct contributes no group, so the fact is simply
gone from the class. **And it is UNDECLARED, which is the defect**: the conditional path has
exactly this gate (`_arm_carried` answers False when "the arm's `not` is read only in part …
a difference, and so a declaration") and `_negated` has none —
`grep -c Approximation …/update_media_buy_response.py` is 0. **Population: 62 nodes in 46
portable 3.2 documents** have a `not` whose partial reduction yields groups while the strict
one yields `None` (88 counting `bundled/`); the same disjunct sits byte for byte on
`create-media-buy-response.json#/oneOf/1` and `sync-creatives-response.json#/oneOf/1`, and
`SyncCreativesError.model_validate({'status':'submitted','errors':[…]})` is ACCEPTED. The
union ROOT grades it correctly and names the branch, so only `model_validate` on the leaf —
the call shape upstream's guards and tests use — is wide. An expressible fix needs no new
kind: `NotValue(('submitted',))` on the `status` annotation states the conjunct exactly.

**8, a forbidden name the annotated class does not declare.** The node is
`allOf: [{$ref: product-format-declaration}, {not: {anyOf: [{required:['tracker_execution_contract']},
{required:['tracker_execution_contract_digest']}]}}]`, and `product-format-declaration.json`
declares the first key but NOT the digest. We emit the group — so the lowering LOOKS exact —
but `ForbiddenGroups.errors` tests membership against `_runtime.supplied(model)`, which is
`__pydantic_fields_set__` plus extras kept only under `extra="allow"`;
`ProductFormatDeclaration` is `extra='ignore'`, so the undeclared forbidden name is ERASED
before the rule can see it and that group can never fire. Measured: `Format.strict_validate`
REFUSES the digest payload and `Format.model_validate` ACCEPTS it, dropping the key
(`model_fields_set == {'format_kind','params'}`, `__pydantic_extra__ is None`), and
`Format.__adcp_approximations__` carries one entry for an unrelated `if` and nothing for
this `not` — **neither refused nor recorded**. Breadth: of the 6 `AfterValidator(ForbiddenGroups(…))`
sites in the emitted tree, 4 name a group that is not a declared field of the class it
annotates; the second unreachable instance of this exact group is
`_schemas/core/transformer.py:92`. The fix is a choice between evaluating the group
pre-validation, on the raw mapping where the key still exists, and recording a `WIDENED`
`Approximation` for any `ForbiddenGroups` name the annotated class neither declares nor
retains.

**9, a hoisted enum against an inline `Literal`.** `from adcp.types.domains.brand.get_brand_identity_response
import File` — the exact import their kept test writes — raises `ImportError`, while ten
sibling words in that module bind (one of them, `FontRole2`, three lines from where `File`
should be). Two compounding causes, both measured: (a) `codegen/lower/names.py:2537` computes
`mine = structure.from_declarations(declarations)` from THIS module's declarations only, and
our class for the node is declared at the dedup home (`brand.json`'s module) and merely
imported here, so the module-local candidate set is empty; (b) even globally no candidate
matches, because the element shape slot keys upstream's inline `Literal['normal','italic','oblique']`
as `"literal"` and our hoisted `StrEnum` as `""` (a named ref), so the digests differ. Scale:
22 upstream model words carry a literal-shaped element and 6 are refused `unmatched`;
separately **345 upstream words refused `unmatched` have exactly one structurally identical
class elsewhere in our tree, and 124 of those are already imported by the refusing module**
— so the module-local scope of `mine` is a general blind spot, not a one-off. The remedy
belongs in the pass that already mints `FontRole2`: let the join see a module's imported
carriers, and make the structural key enum-hoist-insensitive.

## 8. Remaining undecided

**Nothing in §1 is undecided — all 73 rows carry a category, an action, a subject and a
probe.** Four things remain open, and they are listed because the previous version of this
file was unreadable precisely where it padded.

**1. The 40 rows of §1b, which this pass did not re-read.** Every one was graded `measured`
by the previous pass, so none is a blind join — but none has `origin`, none has `what passes
to it`, and none was probed in both directions by an agent that followed its rename chain.
**What would settle them: the same five-step pass, one agent per name.** The expected yield
is low and is not zero: of the 4 previously-`measured` rows this pass DID re-read, all 4
moved (`AssetInstanceType`, `GetProductsResponseUnion`, `IdentityMatchTmpxMacro`,
`ProviderRegistrationTmpxMacro`), and `measured` there meant "a class was found and offered a
payload", not "the declaration was followed to its end". Six of the 40 are already
contradicted in part by a §1 row and should be re-read first:
`InlineDaastAsset` and `VastAsset2` (the ARTIFACT→SPELLING category argument of §4a, and the
`$ref`-arm emission hole of §7), `AuthorizedAgentsByInlineProperties` (the shifted-ordinal
trap), `ListCreativesCreative` and `ListCreativesCreativeItem` (the collapsed 3.1.8 split),
and `Refine` (settled by the same emission fix as `GroupFormatAssetUnion`).

**2. One category disagreement inside §1, recorded rather than averaged: `InlineVastAsset`.**
Its own agent returned ARTIFACT. The `UrlDaastAsset` and `UrlVastAsset` agents each argued
that all four delivery-variant names are SPELLING — hand-written in `aliases.py` from the
document's own title and the arm's own discriminator `const`, with their own docstrings, on
upstream's deliberate flat `__all__`, and the ordinal name is their TARGET (`VastAsset1`,
`DaastAsset1`), which this table already carries as its own ARTIFACT row. Three of the four
now read SPELLING and `InlineVastAsset` reads ARTIFACT, which is the inconsistency.
**What would settle it: one reading of `aliases.py:1037-1048` — four consecutive lines, one
construction — applied to all four names at once, plus `InlineDaastAsset` from §1b.** The
category does not change what is owed: all four are an alias onto a probe-confirmed class of
ours.

**3. One probe deliberately left unfinished, named by the agent that could not reach it.**
`PublisherPropertySelector`'s `ForbiddenGroups((('publisher_domains',),))` (`core/product.py:291`,
`core/canonical_product.py:81`) is `extra='ignore'` over a document with no `properties` at
all, so it is a candidate for the §7 item-8 erasure. The `CanonicalParameters` agent flagged
it and did not confirm it, because a different rule — the `selection_type` `oneOf` — refused
the payload first. **What would settle it: a payload that satisfies `selection_type` and then
carries `publisher_domains`.** It is one of the 4 unreachable-group sites and belongs in the
same fix either way.

**4. `tests/test_generated_poc_alias.py:139`'s `assert len(domains.DOMAINS) == 26`, which no
honest binding can satisfy.** Upstream's three extra names (`brand_discovery`, `manifest`,
`manifest_schema`) have no directory in `schemas/cache/3.2` and no module in `_schemas`; our
roster is 23 and all 23 import. This is not undecided as a VERDICT — the legacy layer is owed
and §5 states its expression — but **whether that kept assertion is deselected or rewritten
is not this file's call to make**, and it must be answered before the layer lands or one
collection error becomes one mystery failure.

---

**One generator change is a precondition for most of §1, and ten rows measured it
independently.** `src/adcp/types/aliases.py`, `compat.py` and `_adapter.py` are GENERATED by
`survey/adapter_surface.py`, so no row above is served by hand-editing them. The keying
failure those rows name is at `survey/adapter_surface.py:1800`: the binder tries
document+word (our word differs by design) and a scalar-constraint pointer join (useless for
an object), and **never tries the document+pointer join that settles them** — which is why
`SyncCreativeResult`, `SyncCatalogResult`, `SyncAudiencesAudience`, `DeliveryCreative` and
the six `AuthorizedAgentsBy*` arms sit in `__adcp_refused__` under
`DOCUMENT-NO-WORD-NO-IDENTITY` with a reason that is false of every one of them. Two of our
own survey tables already disagree about a single name (`ScopeFromBillingNotSupported`:
`alias-surface-9.6.1.tsv:2630` grades it `ABSENT-SUBJECT-NO-WORD`, `adapter-surface-9.6.1.tsv:412`
resolves it `BOUND` to the right class), and the adapter table is the right one.
