# Migrating from v3.x to v4.0

4.0 realigns the SDK surface with the current AdCP spec. The schema redesign
removed several types and renamed fields; this guide lists each change with
before/after code.

## Audit your exposure first

```bash
grep -rnE "BrandManifest|FormatCategory|DeliverTo|PromotedProducts|PromotedOfferings|PackageStatus|from adcp import Pricing|\.brand_manifest|adcp\.types\.generated_poc" src/
```

Each match is either an import that will now raise `ImportError`, an attribute
access that will raise `AttributeError`, or a coupling to a private module.

Update your dependency pin:

```toml
# pyproject.toml
[project]
dependencies = [
    "adcp>=4.0.0b1,<5",
]
```

## Removed types

The following types were removed from the AdCP spec and have no replacement
stubs in the SDK. Imports will fail at runtime with `ImportError`.

| Removed | Replacement |
| --- | --- |
| `BrandManifest` | `BrandReference(domain=...)` when constructing requests; inline dict when reading registry `brand` payloads |
| `FormatCategory` | Removed without replacement (previously an enum, now inferred from format metadata) |
| `DeliverTo` | Removed — use `publisher_properties` on the request |
| `PromotedProducts` / `PromotedOfferings` | Removed — use the `offerings` field shape from the current spec |
| `Pricing` | Use the discriminated `*PricingOption` types (e.g. `CpmFixedRatePricingOption`) |
| `PackageStatus` | Package status is now carried by `MediaBuyStatus`; per-package status was removed |

### `BrandManifest` → `BrandReference`

**Before (v3.x):**
```python
from adcp import CreateMediaBuyRequest, BrandManifest

request = CreateMediaBuyRequest(
    brand_manifest=BrandManifest(
        name="Coffee Co",
        brand_url="https://coffeeco.com",
        logo_url="https://coffeeco.com/logo.png",
    ),
    packages=[...],
    publisher_properties=...,
)
```

**After (v4.0):**
```python
from adcp import CreateMediaBuyRequest, BrandReference

request = CreateMediaBuyRequest(
    brand=BrandReference(domain="coffeeco.com"),
    packages=[...],
    publisher_properties=...,
)
```

The spec now resolves brand identity from `/.well-known/brand.json` at the
supplied domain, or from the AdCP registry. The SDK no longer models the
brand manifest as a typed class.

### `FormatCategory` → removed

The spec no longer models category as a separate enum. Read category
information from `Format` metadata instead.

```python
# Before
from adcp import FormatCategory
if fmt.category == FormatCategory.video: ...

# After — category info lives on Format itself
if fmt.type == "video": ...  # or fmt.channel, depending on what you were matching
```

### `DeliverTo` → `publisher_properties`

```python
# Before
request = CreateMediaBuyRequest(deliver_to=DeliverTo(...), ...)

# After
request = CreateMediaBuyRequest(
    publisher_properties=PublisherPropertiesAll(selection_type="all"),
    ...,
)
```

### `PromotedProducts` / `PromotedOfferings` → `offerings`

```python
# Before
request.promoted_offerings = PromotedOfferings(...)

# After — pass the spec-current offerings shape as a dict/model
request.offerings = [...]
```

### `Pricing` → discriminated `*PricingOption`

```python
# Before
from adcp import Pricing
pricing = Pricing(model="cpm", rate=5.0, currency="USD")

# After — each pricing model has its own class
from adcp import CpmFixedRatePricingOption
pricing = CpmFixedRatePricingOption(
    pricing_option_id="cpm_usd",
    pricing_model="cpm",
    is_fixed=True,
    currency="USD",
    rate=5.0,
)
```

### `PackageStatus` → `MediaBuyStatus`

Per-package status was removed. Status now lives on the media buy.

```python
# Before
if package.status == PackageStatus.active: ...

# After
if media_buy.status == MediaBuyStatus.active: ...
```

### `ResolvedBrand.brand_manifest` field removed

`RegistryClient.lookup_brand()` returns a `ResolvedBrand` whose
`brand_manifest` field and cross-populate validator are gone.

**Before (v3.x):**
```python
result = await registry.lookup_brand("nike.com")
manifest = result.brand_manifest  # Either `brand` or `brand_manifest` worked
```

**After (v4.0):**
```python
result = await registry.lookup_brand("nike.com")
manifest = result.brand  # Only `.brand`
```

## Numbered discriminated-union classes shifted

`datamodel-code-generator` numbers variant classes in the order they appear in
the upstream `oneOf`. When the spec reorders variants, the numbers shift.
Example: `Assets5`…`Assets14` in 3.x now correspond to higher-numbered
variants (`Assets57`…`Assets149`) across different response modules.

**Don't** import numbered classes directly:

```python
# Fragile — will break on the next spec revision:
from adcp.types.generated_poc.bundled.creative.build_creative_response import Assets9
```

**Do** import the semantic alias from `adcp.types`:

```python
from adcp.types import CreateMediaBuySuccessResponse, BuildCreativeSuccessResponse
```

Aliases for all discriminated-union success/error variants live in
`adcp/types/aliases.py`. If a variant you need isn't aliased, file an issue —
aliasing is the supported path; direct `Assets*` imports aren't.

## Public vs. internal imports

`adcp.types.generated_poc.*` is internal. Generated module paths and class
names can change with every schema regeneration. Import from `adcp.types`
instead.

**Before:**
```python
from adcp.types.generated_poc.core.context import ContextObject
from adcp.types.generated_poc.core.targeting import TargetingOverlay
```

**After:**
```python
from adcp import ContextObject, TargetingOverlay
# or
from adcp.types import ContextObject, TargetingOverlay
```

4.0 adds top-level re-exports for `TargetingOverlay`, `AdvertiserIndustry`,
`KellerType`, and `BrandSource`. If you need a type that isn't on the
top-level surface, check `from adcp.types import X` first — most generated
types are re-exported there.

## `__version__` now reflects the installed distribution

`adcp.__version__` now reads from `importlib.metadata.version("adcp")`
instead of a hardcoded constant, so it always matches `pyproject.toml`. If
you're running from a source checkout without `pip install -e .`, you'll see
`"0.0.0+unknown"` — install the package (or run `pip install -e .` in CI) to
get the real version. If your test suite asserts on `__version__`, it will
need the same install step.

## Watch for silent Pydantic field drops

`CreateMediaBuyRequest` (and most other request models) accept extra fields
without erroring. Passing `brand_manifest=...` by keyword after upgrading
won't raise at construction — the field is silently dropped, and you'll see
the failure as a server-side rejection or missing `brand` at execution time.
The `grep` in the audit section above catches these.
