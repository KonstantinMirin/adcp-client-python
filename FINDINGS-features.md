# Findings — the two `features` clusters, and the three grounds under them

Each section names the file, what was measured, and whether it was repaired here or
left red because the repair is outside this worktree's write scope
(`tests/test_property_list_integration.py`, `tests/test_codegen_invariants.py`, this
file).

Baseline artifact: `test-results/before.json`, `failed=496 error=5 passed=14565
total=17893` — the figure the task names, matched exactly.

---

## Cluster A — `tests/test_property_list_integration.py`, 22 → 11

**The 22 were not one ground. They were three, each masking the next.**  All 22 stopped
at the first, which is a class-body construction and so ran before any test body.

### A1 — REPAIRED. The signals `Features` class handed to the media-buy field

`protocol/get-adcp-capabilities-response.json` states a `features` node under BOTH
`media_buy` and `signals`:

| node | class | what it is |
|---|---|---|
| `#/properties/media_buy/properties/features` | `GetAdCPCapabilitiesResponseMediaBuyFeatures` | narrows `core/media-buy-features.json`, adding that document's four `if`/`then` conditionals as `ConditionalRequired` rules |
| `#/properties/signals/properties/features` | `GetAdCPCapabilitiesResponseSignalsFeatures` | a separate declaration |

`adcp.decisioning.capabilities.Features` is the SIGNALS one, re-exported from
`adcp.types.capabilities` (`Features = GetAdCPCapabilitiesResponseSignalsFeatures`, two
lines apart from `SignalsFeatures`, the same object). The three sellers in this file
declare `media_buy=MediaBuy(features=…)`, so the field refuses it:

```
features
  Input should be a valid dictionary or instance of
  GetAdCPCapabilitiesResponseMediaBuyFeatures  [type=model_type]
```

Repaired by naming the media-buy class from `adcp.types.protocol`, the domain path that
exports the schema's own class. `adcp.types.capabilities` has no media-buy-side spelling
to reach for — measured, it exports `Features` and `SignalsFeatures` and nothing else
over that word.

**The production-side finding attached to it, NOT repaired here.**
`docs/migration-from-upstream.md` §6 ("Four, decided by the document and not by the
word") decides this very name the other way:

> `adcp.decisioning.capabilities.Features` | `protocol/get-adcp-capabilities-response.json`
> **references** `core/media-buy-features.json` — at
> `/properties/media_buy/properties/features/allOf/0` … | **`adcp.types.core.MediaBuyFeatures`**,
> from `core/media-buy-features.json`. A reference and not a restatement, so this is one
> subject and the destination is a rename.

So the guide says `Features` names the MEDIA-BUY subject and the emitted adapter surface
binds it to the signals one. `src/adcp/types/capabilities.py` is generated
(`survey/adapter_surface.py`) and `src/` is out of scope.

Two things are owed, and the second is not the first:

1. `adcp.types.capabilities.Features` should name the media-buy subject, per §6.
2. Even then, `adcp.types.core.MediaBuyFeatures` — §6's stated destination — does **not**
   validate into `GetAdCPCapabilitiesResponseMediaBuy.features`. Measured: pydantic
   refuses a BASE instance where the field's annotation is the narrowing subclass, so
   `MediaBuy(features=MediaBuyFeatures(property_list_filtering=True))` raises the same
   `model_type` error. The class a caller needs is the document's node class, and today
   the only spelling of it is the generated
   `adcp.types.protocol.GetAdCPCapabilitiesResponseMediaBuyFeatures`.

**Two docs teach the spelling that raises**, and both are src/docs, out of scope:

- `src/adcp/decisioning/property_list.py` module docstring, lines 5 and 14: *"When an
  adopter declares ``Features(property_list_filtering=True)`` on their …
  DecisioningCapabilities"*.
- `docs/property-list-filtering.md:3`: *"Declare `Features(property_list_filtering=True)`
  to advertise seller filtering."*

An adopter following either gets the `model_type` error this cluster is made of.

### A2 — REPAIRED. A proposals request with no brand source

With A1 cleared, 18 of the 22 reached `RequestProposalsRequest.model_validate` and were
refused there. `media-buy/request-proposals-request.json` states a ROOT `anyOf`:

```json
"anyOf": [
  {"required": ["brand"]},
  {"properties": {"account": {"required": ["brand", "operator"]}}, "required": ["account"]}
]
```

The fixture supplied `account: {"account_id": "account"}` and no brand — neither branch.
`core/canonical-account-ref.json`'s `account_id` branch is `additionalProperties: false`,
so the id-keyed account cannot carry the brand and the top-level `brand` is the only
branch left. The root `allOf`'s `not` stays quiet: it forbids a top-level `brand` only
beside an account carrying `brand` + `operator`.

Repaired by adding `"brand": {"domain": "buyer.example.com"}` —
`core/brand-key.json` requires `domain` and nothing else, and the value matches the one
the same test already uses in its `commercial_terms`.

### A3 — LEFT RED, 11 pairs. `ExtensionObject.model_validate` on a typing alias

Every remaining failure in this file is `model_response=True` — the parametrization where
the platform returns a validated model rather than a dict — and every one is the same
line of PRODUCTION code:

```
src/adcp/decisioning/property_list.py:374: in maybe_apply_property_list_filter
    from adcp.types.domains.core.ext import ExtensionObject
    update["ext"] = ExtensionObject.model_validate(update["ext"])
E   AttributeError: type object 'dict' has no attribute 'model_validate'
```

`core/ext.json` is a mapping document, so this emission binds the name to a TYPE and not
to a model:

```python
# src/adcp/types/_schemas/core/ext.py  (generated)
ExtensionObject = Annotated[dict[str, Any], Field(description='Extension object for …')]
```

`adcp.types.domains.core.ext` is the compatibility mirror of that module, so the name
resolves to the same `_AnnotatedAlias` and `.model_validate` reaches
`typing.__getattr__`.

**This is not a fixture problem and the tests are grading it correctly.** The branch is
reached for `outcome in {"listed", "products_available", "proposed"}` whenever the
platform returned a model, which is the documented adopter path — so property-list
filtering raises `AttributeError` for every model-returning seller. `src/` is out of this
worktree's write scope. The repair is to stop treating `ExtensionObject` as a model at
that line: the value is already a plain `dict[str, Any]` built two lines above, and the
mapping alias validates through `TypeAdapter` if validation is wanted at all.

---

## Cluster B — `tests/test_codegen_invariants.py`, 22 → 22. LEFT RED, and the task's
premise is corrected

`test_postal_overlay_support_preserves_only_explicit_legacy_flags` asserts

```python
assert type(getattr(model, field)).model_fields[flag].deprecated is True
```

and the task states that this asserts a SIBLING document's metadata on the positive
variant, both classes being faithful to their own documents. **Measured, the two
documents are not siblings: one composes the other, and the mark is stated at the node
the test reads.**

```
core/positive-postal-area-support.json
  "allOf": [
    {"$ref": ".../core/postal-area-support.json"},          <- marks all 11 deprecated: true
    {"type": "object", "minProperties": 1,
     "properties": {"us_zip": {"const": true}, … 11 of them}}
  ]
```

Under `allOf` both conjuncts apply to the SAME instance, so `us_zip` at this node is
`{"type": "boolean", "deprecated": true, "const": true}`. The emission agrees about the
relation — it lowers `allOf[0]` to inheritance:

```python
class PositivePostalAreaSupport(PostalAreaSupport):      # src/adcp/types/_schemas/core/
    us_zip: Annotated[Literal[True] | None, OmittedNotNull] = None
```

and then redeclares the 11 flags to carry the `const`, which drops the base's
`Field(deprecated=True)`. The parent keeps it (`us_zip: Annotated[StrictBool | None,
Field(deprecated=True), OmittedNotNull]`), so the subclass is NARROWER IN METADATA than
its document, with no declaration — and `CLAUDE.md`'s rule is the one that names the
direction: *"`deprecated` is metadata, not absence"*. The class carries no
`__adcp_approximations__` and no `__adcp_refused__` entry for it, and the pair passes in
`verdicts.tsv` because an annotation is not an acceptance fact and no cell grades it.

**The site, and it is one word.** `codegen/intersect.py`:

```python
RENDERED = ("default", "description")
```

`intersection()` gap-fills exactly these from the base where a narrowing restatement is
silent (§6 clause 3, "silence inherits"). `deprecated` is renderable —
`codegen/render.py:671`, `if decided.deprecated: extras["deprecated"] = True` — but is
not in the tuple, so it is the one rendered annotation the gap-fill does not carry.

**Measured over the whole emitted tree: 21 fields on 11 classes lose a base's
`deprecated`**, two families:

| family | fields | base |
|---|---|---|
| `PositivePostalAreaSupport` | the 11 postal flags | `PostalAreaSupport` |
| 10 request roots — `ListProductsRequest`, `BuyProductsRequest`, `AcceptProposalRequest`, `ControlMediaBuyRequest`, `DeclineProposalsRequest`, `ListAccountChangesRequest`, `RefineProposalsRequest`, `RequestProposalsRequest`, `SyncReportingReceiptsRequest`, `SyncReportingStatusRequest` | `adcp_major_version` | `AdCPVersionEnvelope` |

The second family is the consumer-visible one: `core/version-envelope.json` states
`{"deprecated": true, "x-removed-in": "4.0.0", "description": "DEPRECATED in favor of
adcp_version …"}`, `AdCPVersionEnvelope.adcp_major_version` carries both, and every
request root that composes the envelope and restates the property as a bare `$ref` to it
carries neither. A buyer reading `ListProductsRequest`'s field metadata — or a JSON
schema generated from it — is not told the field is deprecated and removed in 4.0.

So the assertion stays. It is the only thing in the suite that catches this, and
`codegen/` is not this worktree's to write. The test now carries the document citation
and the site above it, so the next reader does not have to re-derive it to decide whether
to delete it.

**What still passes in that test, unchanged:** the dump round-trip (`model_dump ==
payload`, line 81, the `OmittedNotNull` contract) and the `pytest.raises` on
`{flag: False}`, which grades the `allOf[1]` `const: true` — a separate claim, and the
one half of this document the emission does carry.
