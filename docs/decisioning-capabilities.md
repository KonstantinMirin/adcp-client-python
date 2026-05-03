# Declaring capabilities for a decisioning platform

A platform tells buyers what it can do via the `get_adcp_capabilities`
response. Buyers read it once at agent discovery and use it to choose
products, target safely, and decide which protocols to call.

The SDK projects your capability declaration into a spec-conformant
response automatically — you declare in Python, the framework emits the
wire shape. This guide covers what you can declare and how.

## The shape

```python
from adcp.decisioning import DecisioningCapabilities, DecisioningPlatform
from adcp.decisioning.capabilities import (
    Account,
    Adcp,
    Execution,
    GeoMetros,
    IdempotencySupported,
    MediaBuy,
    Specialism,
    Targeting,
)


class MySeller(DecisioningPlatform):
    capabilities = DecisioningCapabilities(
        specialisms=[Specialism.sales_non_guaranteed],
        adcp=Adcp(
            major_versions=[3],
            idempotency=IdempotencySupported(supported=True, replay_ttl_seconds=86400),
        ),
        account=Account(supported_billing=["operator"]),
        media_buy=MediaBuy(
            supported_pricing_models=["cpm"],
            execution=Execution(
                targeting=Targeting(
                    geo_countries=True,
                    geo_metros=GeoMetros(nielsen_dma=True),
                ),
            ),
        ),
    )

    accounts = ...  # AccountStore impl
```

The names mirror the AdCP wire spec 1:1 — every type in
`adcp.decisioning.capabilities` corresponds to a field type in
`protocol/get-adcp-capabilities-response.json`. Read your declaration
alongside the spec; they line up.

## What to declare

### Always

- **`specialisms`** — drives the dispatch validator (it checks that
  declared specialisms have the methods they require) and feeds the
  derived `supported_protocols`. Use `Specialism.*` enum members for
  type safety; spec slugs like `"sales-non-guaranteed"` work too and
  get coerced at construction.
- **`adcp`** — `major_versions` plus an idempotency declaration. The
  spec requires `adcp.idempotency`; if you skip this block, the
  framework emits a default `{"supported": False}` so the response stays
  spec-valid, but buyers reading it will mark you unsafe for retries.
  Declare it.
- **`account.supported_billing`** — required by the spec whenever
  `media_buy` is in `supported_protocols`. Pick a subset of `operator`,
  `agent`, `advertiser`.

### When you support media buying

- **`media_buy.supported_pricing_models`** — your full portfolio.
  Individual products may support a subset.
- **`media_buy.execution.targeting`** — every dimension you actually
  honor. Buyers read this before sending targeting payloads.
  Don't claim what you can't enforce — the spec is explicit that a
  declared capability is a commitment.
- **`media_buy.reporting_delivery_methods`** — push delivery formats
  beyond polling.
- **`media_buy.features`** — `inline_creative_management`,
  `property_list_filtering`, `catalog_management` flags that gate
  buyer-side flow.

### When you support other protocols

- **`signals`**, **`governance`**, **`sponsored_intelligence`**,
  **`brand`**, **`creative`** — declare the matching block when you
  claim that protocol.

### Cross-cutting posture

- **`request_signing`** — RFC 9421 inbound signature support. Adopters
  with signed-request infrastructure declare `supported=True` plus the
  `required_for` / `warn_for` operation lists.
- **`webhook_signing`** — outbound RFC 9421 webhook profile.
- **`identity`** — operator key-scoping / compromise-response posture.
  Advisory in 3.x; useful for buyer-side onboarding decisions.
- **`compliance_testing`** — declare when you support
  `comply_test_controller`-driven scenarios.

## What you don't declare directly

The framework auto-derives a few things:

- **`supported_protocols`** — derived from the union of
  `SPECIALISM_TO_PROTOCOLS` over your declared specialisms. Override
  by setting `supported_protocols=[SupportedProtocol.media_buy, ...]`
  explicitly when claiming a protocol whose specialisms aren't all
  enumerated.
- **Wire-level `specialisms` field** — emitted from spec-known entries
  in your `specialisms` list. Novel/typo strings stay diagnostic-only at
  the dispatch validator and don't leak into the wire.

## Targeting capabilities — claim what you honor

The wire schema has fine-grained targeting-capability declarations:

```python
from adcp.decisioning.capabilities import (
    GeoMetros, GeoPostalAreas, Targeting,
)

targeting = Targeting(
    geo_countries=True,
    geo_regions=True,
    geo_metros=GeoMetros(nielsen_dma=True, eurostat_nuts2=True),
    geo_postal_areas=GeoPostalAreas(us_zip=True, gb_outward=True),
    language=True,
)
```

The dispatch validator walks each declared dimension at runtime when a
buyer sends a targeting payload — claiming `geo_countries=True` while
your adapter ignores the field is the kind of bug the validator
catches. Be honest in declarations.

## Common mistakes

### Declaring `account.required_for_products=True` without OAuth

If you require operator credentials before letting buyers list
products, also declare `authorization_endpoint` so the buyer's agent
can drive the operator through OAuth. Otherwise the buyer sees
`required_for_products=True` and has nowhere to send the operator.

### Mixing legacy and structured forms

```python
DecisioningCapabilities(
    pricing_models=["cpm"],                            # legacy
    media_buy=MediaBuy(supported_pricing_models=["cpcv"]),  # structured
)
```

When both are set, the structured form wins. The legacy field still
fires a `DeprecationWarning` at projection time, telling you to remove
it. Pick one.

### Claiming a protocol you don't fully implement

Each protocol claim commits you to passing the baseline storyboard at
`/compliance/{version}/protocols/{protocol}/`. If you can't run the
storyboard end-to-end, don't claim the protocol — buyers will hold you
to it.

## Migration from the flat shortcuts

The flat fields `pricing_models`, `supported_billing`, `channels` are
deprecated. The mapping is direct:

| Legacy | Structured equivalent |
|---|---|
| `pricing_models=["cpm"]` | `media_buy=MediaBuy(supported_pricing_models=["cpm"])` |
| `supported_billing=["operator"]` | `account=Account(supported_billing=["operator"])` |
| `channels=["display"]` | `media_buy=MediaBuy(portfolio=Portfolio(primary_channels=["display"], publisher_domains=[...]))` |

The `channels` migration path is special — the spec's
`portfolio.primary_channels` requires `publisher_domains` alongside,
which the flat field can't carry. The legacy field hasn't been emitted
to the wire since the projection rewrite. Adopters with channels
declarations should construct a full `Portfolio` block or remove the
declaration.

## Where capabilities run

- **Construction time** — `DecisioningCapabilities.__post_init__`
  coerces spec-known specialism strings to `Specialism` enum members.
  Novel slugs pass through unchanged so the dispatch validator can
  surface them.
- **Server boot** — `validate_capabilities_response_shape` runs the
  full projection synchronously and validates the output against
  `protocol/get-adcp-capabilities-response.json`. Boot-time errors here
  are the cleanest possible — fix the declaration or override the
  projection on a `PlatformHandler` subclass.
- **Discovery time** — every `get_adcp_capabilities` call reads the
  declaration once and projects. There's no per-call I/O; the projection
  is pure.

## Custom blocks

For vendor-specific capability fields the spec doesn't define, use
`config={"vendor_extension": ...}` — surfaced under `config` in the
projection. Don't reach into the structured blocks for vendor data;
their shapes are spec-bound and may break under regeneration when the
spec evolves.

## See also

- `examples/v3_reference_seller/src/platform.py` — the canonical
  motivating example. Declares `specialisms`, `account`, `media_buy`.
- `tests/test_decisioning_capabilities_submodule.py` — round-trips for
  every block including a fully-populated schema-validated response.
- AdCP spec — `protocol/get-adcp-capabilities-response.json` defines
  every field the structured blocks mirror. Read both in parallel.
