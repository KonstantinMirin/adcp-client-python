# Findings — the 53 failures across the v1 → v2 canonical-format suites

30 repaired in the tests, **23 left red because the repair is in `src/`**, and one
further `src/` defect — narrow, and on a deprecated helper — that no test in this
list grades, so it would have stayed invisible.

| file | before | after | what the red that remains is |
| --- | --- | --- | --- |
| `tests/test_canonical_formats_v1_to_v2.py` | 26 | 3 | `src/adcp/canonical_formats/v1_to_v2.py:495` |
| `tests/test_canonical_formats_roundtrip.py` | 15 | 14 | `src/adcp/canonical_formats/v2_to_v1.py:158` |
| `tests/test_preview_html.py` | 9 | 6 | `src/adcp/utils/preview_cache.py:540` and `:658` |
| `tests/test_legacy_asset_helpers.py` | 2 | 0 | — |
| `tests/test_format_assets.py` | 1 | 0 | — |
| **total** | **53** | **23** | |

---

## What the tests were asking for, and what the documents state

### 1. `params` is the branch's typed canonical model, not a dict — 23 of the 26

`core/product-format-declaration.json` has `required: ['format_kind', 'params']` and a
16-branch `oneOf`; each branch types `params` as its own canonical document. Measured:

```
project_v1_format_to_declaration({... "id": "display_300x250"}).declaration
  -> ImageFormatDeclaration          (core/product-format-declaration.json#/oneOf/0)
  .params -> CanonicalFormatImage    (formats/canonical/image.json)
```

So `result.declaration.params.get("asset_source")` raised `'CanonicalFormatImage'
object has no attribute 'get'`, and `result.declaration.params == {"width": 300,
"height": 250}` compared a model against a mapping. The comparisons now go through
`model_dump(exclude_unset=True, mode="json")` — `exclude_unset` so the comparison is
against what the projection SET rather than against every default the canonical
document declares, and `mode="json"` because that is the mode whose values are the
wire's. The single-key reads go to the attribute the document states
(`params.asset_source`, `params.vast_version`, `params.slots[0].asset_group_id`).

Each expected dict was re-measured and every one of them was already right about the
projection. Nothing was changed to agree with the code:

```
display_300x250_image_1x_2x -> {'slots': [{'asset_group_id': 'image_main', 'asset_type': 'image',
   'required': True, 'min': 2, 'max': 2, 'pixel_ratios': [1.0, 2.0],
   'required_pixel_ratios': [1.0, 2.0]}], 'width': 300, 'height': 250, 'pixel_ratios': [1.0, 2.0]}
```

`pixel_ratios` dumps as floats because the document says `number`; `[2] == [2.0]` in
python, so the literals stand as written.

### 2. The v2 → v1 link is `v1_format_ref` — the rest of the 26, and 1 of the 15

`core/product-format-declaration.json` states the seller-asserted link as
`v1_format_ref`, and every emitted branch carries it under that name.
`legacy_format_refs` is the previous generator's spelling; nothing in
`src/adcp/types/` binds it. This is the same finding `FINDINGS-surface.md` already
records — these suites are two more of its six files.

### 3. A manifest asset is a branch of the asset union — 3 of the 9

`core/creative-manifest.json` `$ref`s `core/assets/asset-union.json` for `assets`, so
an image asset in a manifest is that union's `oneOf/0`:

```
AssetVariantImage(AssetVariant, ImageAsset)     core/assets/asset-union.json#/oneOf/0
```

`ImageContent` is `core/assets/image-asset.json` standalone — the branch's PARENT, not
the branch — and pydantic named the class it wanted: *"Input should be a valid
dictionary or instance of AssetVariantImage"*. Handing the union's base
`AssetVariant(asset_type="image", ...)` constructs `AssetVariantImage` too; the
fixtures name the branch directly so three preview tests do not also depend on
dispatch.

### 4. A canonical params slot is not a v1 asset slot — 1 of the 9

`formats/canonical/_base.json#/properties/slots/items` has
`required: ['asset_group_id', 'asset_type']` and states neither `asset_id` nor
`item_type`. Those two are `core/format.json`'s v1 slot keys, and the `Format(...)`
fixture in `test_get_products_with_preview_urls` was authoring a v1 slot inside v2
`params`. (The test is still red, one frame deeper — see defect C.)

### 5. The slot vocabulary is the union's branches — 1 of the 2

`_KNOWN_BASE_INDIVIDUAL_ASSET_TYPES` was the previous generator's list of
`core/format.json`'s individual-slot vocabulary. This emission makes that `oneOf` a
base plus one branch per asset type, so the vocabulary IS the branches' `asset_type`
consts — 21 of them, `display_tag` among them. The test reads them through
`adcp.types._legacy_assets.discriminator_values`, the same derivation the helpers
themselves read, so the two sides cannot drift apart; a second list would pass today
and rot. `tests/test_legacy_asset_helpers_derivation.py` grades that derivation
against `AssetVariant`; this one grades the format slot union, which is a different
document.

### 6. "Unable to extract tag" was pydantic's tagged-union message — the other of the 2

That message comes from `Field(discriminator=...)`, which this emission does not use.
An un-normalised legacy asset now satisfies no branch and the union refuses with its
own `oneOf`: *"is not valid under any of the 21 branches [type=oneOf]"*. The test
matches that and still asserts `asset_type` is the keyword named, which is the claim
it was making.

### 7. An individual slot with no `asset_type` satisfies no branch — the 1

`core/format.json#/$defs/baseIndividualAsset` requires
`['item_type', 'asset_id', 'asset_type', 'required']`, and each of the 21 branches
requires `asset_type` again as its own const — the conjunction, read through the
document and not through one branch. The repeatable-group fixture declared
`item_type: individual` with no `asset_type`.

---

## The `src/` defects — four, and three of them are holding 23 tests red

### A. `declaration.legacy_format_refs` — 17 of the 23 red

Already reported in `FINDINGS-surface.md`, which lists eight read sites. Two of them
are the frames these suites die in:

| frame | expression | red |
| --- | --- | --- |
| `src/adcp/canonical_formats/v2_to_v1.py:158` | `refs = list(declaration.legacy_format_refs)` | 14 × `test_v2_product_v1_outbound_round_trip` |
| `src/adcp/canonical_formats/v1_to_v2.py:495` | `refs = declaration.legacy_format_refs` | 3 × `test_group_declarations_by_product_*` |

Both files' own prose is written in terms of `v1_format_ref[]`, so the divergence is
between each file's comments and its code. Both test files now read
`v1_format_ref`, so what is left in them is purely the `src/` read.

### B. `_create_sample_asset` constructs every asset without its `asset_type` — 5 of the 23

`src/adcp/utils/preview_cache.py:658` and the four branches under it:

```python
if asset_type == "image":
    return ImageContent(url="https://via.placeholder.com/300x250.png", width=300, height=250)
```

The `asset_type` the function was just handed is used to PICK the class and then
dropped from the payload. Every one of the five documents requires it as a const:

```
core/assets/image-asset.json  required=['asset_type','url','width','height']  const='image'
core/assets/video-asset.json  required=['asset_type','url','width','height']  const='video'
core/assets/text-asset.json   required=['asset_type','content']               const='text'
core/assets/url-asset.json    required=['asset_type','url']                   const='url'
core/assets/html-asset.json   required=['asset_type','content']               const='html'
```

So `_create_sample_asset(<anything>)` raises `ValidationError: asset_type Field
required`. The same omission is at `preview_cache.py:543`/`:548` and `:628`/`:633`
(`ImageContent(url=..., width=..., height=...)` / `UrlContent(url=...)`), which are
reached when a format declares no required assets. Red: `test_create_sample_asset`,
`test_create_sample_manifest_for_format`,
`test_create_sample_manifest_for_format_with_new_assets_field`,
`test_create_sample_manifest_uses_assets_field`,
`test_list_creative_formats_with_preview_urls`.

The fix is one keyword per branch — `asset_type="image"` etc. — and it is `src/`.

### C. `_create_sample_manifest_for_format` reads typed `params` as a dict — 1 of the 23

`src/adcp/utils/preview_cache.py:540`:

```python
width = int(getattr(fmt, "params", {}).get("width", 300))
```

`params` on a canonical declaration is `CanonicalFormatImage` (defect 1 above), so
this raises `'CanonicalFormatImage' object has no attribute 'get'` for every
canonical `Format` whose required-asset list comes back empty. Red:
`test_get_products_with_preview_urls`, whose fixture is now a valid canonical
declaration and reaches this line. The `getattr(..., {})` default means the
dict-shaped read was never grading a declaration — it was grading the absence of
one.

### D. `normalize_assets_required` is bound to the image branch, not to the union — 0 red, and the NARROWEST of the four

**The binding is wrong and the consequence is a refusal, not a mis-construction.** An
earlier draft of this section said the function "constructs an image slot whatever it
is handed"; it does not, and the difference is the whole severity of the finding.

`src/adcp/utils/format_assets.py:24`:

```python
from adcp.types.domains.core.format import Assets as AssetsModel   # Assets = IndividualImageAsset
```

`Assets` is the generated member alias for the FIRST branch of the individual-slot
union — `SchemaRef(core/format.json, '#/properties/assets/items/oneOf/0/oneOf/0')` —
and not the union. Measured, what that produces at `format_assets.py:124` is a
pydantic refusal:

```
normalize_assets_required([{"asset_id": "v", "asset_type": "video", "item_type": "individual"}])
  -> ValidationError: 1 validation error for IndividualImageAsset
     asset_type  Input should be 'image' [type=literal_error, input_value='video']
```

The branch's `asset_type: Literal['image']` refuses `'video'` rather than accepting
it, so **there is no silent wrong-type data path here** — no caller receives an image
slot built from a video entry. The function fails closed on 20 of the 21 asset types
the document states.

The dispatching base is right there and answers correctly —
`AssetsItemIndividual(asset_id="v", item_type="individual", required=True,
asset_type="video")` constructs `IndividualVideoAsset`. So the fix is one import line.

**How to rank it.** `normalize_assets_required` is a DEPRECATED helper: it emits
`DeprecationWarning` on every call ("the assets_required field was removed in ADCP
3.0.0-beta.2. This function will be removed in a future version"), and all three of
its tests assert that warning. A deprecated helper that refuses non-image input is a
real but narrow defect — an availability bug on a path already scheduled for removal,
not a correctness or corruption risk, and well below A, B and C, each of which is
holding tests red.

**No test grades it.** All three `TestNormalizeAssetsRequired` cases pass
`asset_type: "image"`, so the only path the binding breaks is the one nothing asks
about — which is why it is written down rather than left to be rediscovered.
