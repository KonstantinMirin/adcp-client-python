# Findings — the type-surface and coercion lane

Four files, 108 pairs, all four unable to collect until this cycle. 108 → 0, by eleven
grounds. One of those grounds is a COMPILER DEFECT and is reported here rather than
written into an assertion.

## COMPILER DEFECT: `core/https-url.json`'s `pattern` is dropped from the class half with no declaration

**The document.** `patches/8525/documents/core/https-url.json`, the extraction #8525 asks
upstream for, states three things:

```json
{ "type": "string", "format": "uri", "pattern": "^https://" }
```

**The emission.** `src/adcp/types/_schemas/core/https_url.py`:

```python
__adcp_approximations__ = (
    Approximation(..., keyword='format',    kind='NARROWED', rung='TYPE', ...),
    Approximation(..., keyword='maxLength', kind='NARROWED', rung='KEYWORD', ...),
    Approximation(..., keyword='minLength', kind='NARROWED', rung='KEYWORD', ...),
)

HTTPSURL = Annotated[AdCPUrl, Field(description='A URL whose scheme is https. ...')]
```

Three declarations. **There is no `pattern` entry**, and `AdCPUrl` is
`Annotated[WireAnyUrl, UrlConstraints(max_length=2083, allowed_schemes=["https"])]`.

**The decision this rests on, and why its premise is false.** `rebuild-plan.md`'s keyword
table (§ `pattern`) and `src/adcp/types/constraints.py` both state it, the second in bold:

> `^https://` is the one exception and it is not an exception to the rule: that pattern IS
> `AdCPUrl`'s `allowed_schemes`, so the type states it.

`allowed_schemes=["https"]` does not state `^https://`. The pattern is an **anchored,
case-sensitive regex over the instance string**; `allowed_schemes` is a check on pydantic's
**parsed** scheme, and the parser lower-cases a scheme, strips leading whitespace, and
repairs `https:\\` into `https://` before the check runs.

**Measured** on `PlaceSupport.systems` / `GeographicPlaceRequirement.systems` /
`Targeting.geo_places`, whose key type reaches `AdCPUrl` through
`core/geo-place-system.json`'s `format: uri` + `pattern: "^https://"` branch — 12 pairs,
4 spellings × 3 models:

| key | `^https://` matches | `strict_validate` | `model_validate` |
|---|---|---|---|
| `HTTPS://seller.example/places` | no | refuses (`enum`) | **accepts**, key `WireAnyUrl('HTTPS://seller.example/places')` |
| `Https://seller.example/places` | no | refuses (`enum`) | **accepts**, key kept verbatim |
| `· https://seller.example/places` (leading space) | no | refuses (`enum`) | **accepts**, normalised to `https://seller.example/places` |
| `https:\seller.example/places` | no | refuses (`enum`) | **accepts**, repaired to `https://seller.example/places` |

The five other candidates in the same parametrization — `http://…`, `ftp://…`, `unknown`,
`""`, `https://` — are refused by **both** halves, so the two halves disagree at exactly
the four spellings the pattern discriminates and `allowed_schemes` does not.

**Why this is the defect and not the decision.** `CLAUDE.md`: *if a check reports a
decision as a failure, the defect is the missing DECLARATION, never the decision.* The
decision — select the URL type at `^https://` — stays. What is missing is an
`Approximation(..., keyword='pattern', kind='WIDENED', ...)` on `core/https-url.json`.

And it is the SAME widening `rebuild-plan.md`'s own keyword table records having fixed:

> The row read "selects the type instead, and the pattern stays with the schema half" and
> that was a SILENT widening at 408 positions in 115 documents: `strict_validate` applied
> it, the class did not, and no `__adcp_approximations__` entry said so
> (adcp-client-python-bgyd).

The 408 positions were the OTHER patterns; `^https://` was carved out as "the type states
it", and at that carve-out the widening is still live and still undeclared.

**The correct behaviour is already written and is not selected.**
`src/adcp/types/_geo_place_keys.py` holds `GeoPlaceSystemKey`, re-exported from
`adcp.types.base`, which applies the prefix as a string test *before* any URL parsing:

```python
# URL parsing normalizes schemes, but the schema's ^https:// pattern
# applies to the original opaque identifier, before any normalization.
if not value.startswith("https://"):
    raise ValueError("geographic place system URLs must start with https://")
```

It is the previous generator's post-generate target and is now reachable but unused — no
emitted field selects it. Nothing here is patched around: the four spellings are graded on
the document, through `strict_validate`, in
`tests/test_geo_place_system_keys.py::test_system_keys_the_pattern_refuses_are_refused_by_the_document`,
with the divergence named in its docstring.

**Scope.** `core/https-url.json` is `$ref`-ed widely and `AdCPUrl` is the type for every
`^https://` node, so the undeclared widening is not local to geo place systems. The count
over the bundle was not taken — out of this lane's write scope.

## The ten test-side grounds

Each is one commit. Counts are failing pairs removed.

### `tests/test_geo_place_system_keys.py` — 52

| n | ground | what the document says |
|---|---|---|
| 14 | the resolver fixture omitted a required property | `core/geo-place-resolver.json` requires `url`, `auth` **and** `protocol`, the last a `const` of `adcp_geo_place_resolver_v1`. Eight further pairs then reached the invalid-key check this was shadowing. |
| 2 | **DELETE** — the key-rewrite pass has no subject | Both tests drove `scripts.post_generate_fixes.preserve_geo_place_system_map_keys`, a text rewrite over the previous generator's output, in a `bundled/` second tree. The compiler lowers `core/geo-place-system.json`'s `anyOf` into the key type itself; neither the pass nor the tree exists. |
| 8 | a URI key is a URL on the python side | The `format: uri` branch selects the URL type, so a URI key validates to `WireAnyUrl`, whose `str()` is the text as received. Only the JSON side is a `str`, and the wire assertions were already right. |
| 4 | requiredness is a conjunction | `status` is required by `core/protocol-envelope.json` one `allOf` above `media-buy/get-products-response.json`. |
| 24 | the four spellings the pattern refuses | The compiler defect above. Graded on the document's half. |

### `tests/test_type_coercion.py` — 24

| n | ground | what the document says |
|---|---|---|
| 7 | `context`/`ext` are MAPPINGS | `core/context.json` and `core/ext.json` state no `properties` and `additionalProperties: true`, so §4 gives each a `dict[str, Any]`. `ContextObject`/`ExtensionObject` are annotated aliases: no class to `isinstance`, no attribute to read, and no identity across validation. |
| 5 | `'name'` is the one member with no second spelling | Members are `UPPER_SNAKE` with a lower-case `MemberAlias` beside each. `name` is refused an alias under the compiler's counted `TAKEN_BY_THE_BASE` reason — the class-body line would shadow `enum.Enum.name`. `.NAME` is the attribute; the wire value is `'name'`. |
| 4 | `uniqueItems` refuses a repeat | `creative/list-creative-formats-request.json` states `uniqueItems: true` on both disclosure filters. The tests asserted a silent de-duplication, which returns a filter the caller did not send. |
| 4 | an extension derives from the BRANCH | §4 emits `core/creative-asset.json`'s stated choice as `CreativeAsset` plus `V1CreativeNamedFormatReference`/`V2CreativeCanonicalFormatKind`; the base dispatches and no field accepts a subclass of it alone. Likewise `create-media-buy-request.json#/anyOf/0/properties/packages/items` is `PackagesItem`. |
| 3 | a previous-generator name | `LegacyFormat` is on `core/format.json`'s own module (`adcp.types.core`), not in `adcp.types.legacy`; `MediaBuyDelivery` is `MediaBuyDeliveriesItem` by §4's `<Property>Item`. |
| 1 | the branch, not the target document's root | `core/pricing-option.json#/oneOf/0` is a bare `$ref`, so §4 names the branch for the target's distinguishing remainder: `PricingOptionCpm`, with `CPMPricingOption` (public `CpmPricingOption`) as its second base. |

One incidental re-point rides with the branch ground: the union base selects its branch by
applying the document, which states `type: string` at `format: date-time`, so a python
`datetime` handed to the base is refused. Every other test in the suite passes the ISO
string; this one now does too.

### `tests/test_discriminated_unions.py` — 21

| n | ground | what the document says |
|---|---|---|
| 5 | a root constrained scalar is an ALIAS | `core/property-id.json` / `core/property-tag.json` are scalars at a root, so §4 gives a module-level annotated alias: an item is the `str`, there is no `.root`, and calling the alias calls `str` and validates nothing. The pattern is asked of the module's `strict_validate`. |
| 3 | an alias has no `__module__` of its own | `typing` owns the object, so the declaring module is the one whose symbol it IS, read with `is` plus that module's `__adcp_schema__`. The collision claim reads the same way: each consumer imports the module's symbol by path. |
| 3 | requiredness is a conjunction | `status` from `core/protocol-envelope.json`, one `allOf` above `media-buy/create-media-buy-response.json`. |
| 5 | requiredness is a conjunction, at the ROOT | `asset_type` is required at `core/assets/vast-asset.json`'s and `core/assets/daast-asset.json`'s own roots, as a `const`, while the `oneOf` branches add `delivery_type` + `url`/`content`. |
| 5 | a base plus branches is what #155 asked for | #155 asked to be rid of the `RootModel` wrapper, because pydantic 2 forbids a `model_config` override on a `RootModel` subclass. §4's answer is not a type alias: the base dispatches, `isinstance` holds against it, each branch is an ordinary model. `SignalRef` still refuses a payload naming no `scope`; only the error name moved, to the JSON Schema keyword. |

### `tests/test_type_aliases.py` — 11

| n | ground | what the document says |
|---|---|---|
| 1 | the module states its own rule | The generated docstring says *AN ALIAS IS A NAME AND NEVER A SECOND TYPE* and does not use the word "semantic", which nothing in this surface is named for. |
| 1 | an alias validates nothing | As above — `strict_validate` is the entry point for a type with no class. |
| 1 | §4 mints no positional name | `VastAsset1`, `DaastAsset1`, `PreviewRender1` have no node behind them. The branches are `VASTAssetUrl`, `DAASTAssetInline`, `PreviewRenderBoth` and the rest, on their own documents' modules rather than on the asset union, which only references them. |
| 6 | a base plus branches, so `get_args` answers nothing | `PricingOption`, `Deployment` and `Destination` are bases; the parts are `__subclasses__()`. The pricing list also named NINE of the document's TEN branches, omitting revenue share. |
| 2 | the wrong module, not a missing name | All six `Legacy*` response spellings exist, in `adcp.types.legacy_names` — the module binding one of upstream's words per POSITION to the one class the compiler emits per SUBJECT. `adcp.types.legacy` is upstream's own `adcp.types.legacy` re-served and carries the response roots. |

## What the collected count does

52 → 0 removes 14 pairs from the geo file (111 → 97): two deleted tests, and twelve from
dropping the `from_json` axis on the pattern-refusal set, because `strict_validate` has no
JSON entry point and `model_validate_json` is the class half on both paths alike.
`test_type_coercion.py` gains four (41 → 45) from splitting the `uniqueItems` claim in two.
