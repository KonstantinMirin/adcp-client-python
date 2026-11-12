# The dead patch layer

Upstream ships modules under `types/` that mutate *other* modules' generated models at
import. Nothing imports them for a return value — they are imported for the side effect,
and upstream's own `types/__init__.py` is what imports them. The drop-in replaces that
`__init__` with ours, and ours does not. **So the layer has been absent from every run we
have graded**, and the tests that exercise it failed naming something else.

Measured with `survey/upstream_machinery.py --wheel … --tree …` (new mode on the existing
instrument; the `LIVE-RESTORE` classification it already carried is untouched):

```
PYTHONPATH=.:src python -m survey upstream_machinery \
    --wheel /tmp/upwheel/lib/python3.12/site-packages --tree /srv/ws/dropin-namereach
```

It reads two trees and writes neither. **Nothing under `src/` was edited for this item.**

---

## 1. The layer, measured

### The set is derived, and it is three modules, not the documented four

A module qualifies when its own AST **stores** into another object's `model_fields` or
`__annotations__`, deletes from one, or calls `model_fields.pop`/`update`/`setdefault`. A
*read* — `if "operation_id" not in X.model_fields` — is not a patch.

| module | store sites | what it stores |
|---|---|---|
| `_forward_compat` | 7 | `model.model_fields[field_name]`, `model.__annotations__[field_name]` |
| `_ergonomic` | 1 | `model.__annotations__[field_name]` |
| `canonical_creative` | 1 | **`del cls.model_fields[name]`** |

`CLAUDE.md` names a fourth, `aliases`. **It stores nothing directly** — it calls
`defer_model_rebuild` and binds names, which is not a patch of a field. Recorded as a
difference rather than quietly reconciled.

### The AST understates the layer, so the size is measured dynamically

9 store sites, because the patches run in loops over tuples of models. The honest figure is
the model surface before and after, snapshotted in the wheel's own interpreter:

| patcher | classes touched | fields added | fields altered |
|---|---|---|---|
| `_forward_compat` | **17** | **3** | **15** |
| `_ergonomic` | 2 | 0 | 4 |
| `aliases` | 0 | 0 | 0 |
| `canonical_creative` | 0 | 0 | 0 |
| **the layer, deduplicated** | **19** | **3** | **19** |

**Two corrections are baked into that diff, and each moved the headline by ~40×.** Both are
stated in the instrument's docstring because a reader who re-derives this without them gets
a number forty times too big and no reason to doubt it:

1. **Both sides are rebuilt.** Under `defer_build=True` an untouched model's
   `FieldInfo.annotation` is still a `ForwardRef`, and importing a patcher builds models as
   a side effect — so "after" has resolved annotations "before" does not. Uncorrected: **794
   classes touched.** With `model_rebuild()` on both sides: 19.
2. **Function addresses are normalised out of the repr.** Metadata reprs as
   `BeforeValidator(func=<function as_json_schema_integer at 0x7b4b927a2>)`, and two
   snapshots are two processes. Uncorrected: **1,392 altered fields.** With ` at 0x…`
   stripped: 19.

A third correction was to the instrument itself: `PYTHONPATH=.:src`, the documented way to
invoke it, is **inherited by a subprocess**, so the wheel's interpreter imported *this*
repository's `src/adcp` and reported `No module named 'adcp.types._ergonomic'` for three of
upstream's own modules. Every probe now runs under `-I`. The same bug made the cost figure
read 652 instead of 396, by parsing a failed-import placeholder as a class name and
extracting the word `adcp`.

### The whole inventory — 22 entries

```
+bundled.protocol.get_adcp_capabilities_response.Features1.canonical_creatives
+core.media_buy_features.MediaBuyFeatures.canonical_creatives
+core.reporting_webhook.ReportingWebhook.operation_id
~bundled.protocol.get_adcp_capabilities_response.MediaBuy.acceptance_policy_discovery
~bundled.protocol.get_adcp_capabilities_response.Portfolio.primary_countries
~bundled.protocol.get_adcp_capabilities_response.Portfolio.publisher_domains
~creative.audit_observation.Details.observed_value
~creative.get_creative_delivery_response.Creative.variants
~creative.list_creative_formats_request.…CreativeAgent.disclosure_persistence
~creative.list_creative_formats_request.…CreativeAgent.disclosure_positions
~creative.preview_creative_response.PreviewCreativeResponse3.manifest
~media_buy.build_creative_response.BuildCreativeResponse1.creative_manifest
~media_buy.build_creative_response.BuildCreativeResponse3.creative_manifests
~media_buy.build_creative_response.BuildCreativeResponse4.creatives
~media_buy.list_creative_formats_request.ListCreativeFormatsRequest.disclosure_persistence
~media_buy.list_creative_formats_request.ListCreativeFormatsRequest.disclosure_positions
~media_buy.package_control.PackageControl.targeting_overlay
~media_buy.package_request.PackageRequest.targeting_overlay
~media_buy.package_update.PackageUpdate.targeting_overlay
~media_buy.product_purchase_input.ProductPurchaseInput.targeting_overlay
~trusted_match.context_match_response.…RouterPublisher.offers
~trusted_match.provider_context_match_response.…ProviderRouter.offers
```

Reading them: the 3 additions are **optional extensions a bundle does not yet declare**
(`operation_id`, `canonical_creatives` ×2). The 19 alterations are **widenings** — an
annotation retargeted to a readback facade that accepts a legacy shape
(`CreativeManifest` → `_ReadbackCreativeManifest`, `Offer` → `_ReadbackOffer`,
`CreativeVariant` → `_DeliveryVariant`), a `TargetingOverlayInput` wrapped in a coercing
validator, a unique-enum-list coercer added to four `disclosure_*` fields, and one union
arm reordered. **Every one admits strictly more than the generated class did.**

### And two patchers do their work by defining CLASSES, not by editing fields

The zeros above are not idleness:

| module | model classes it defines | exported by `adcp.types` under that name |
|---|---|---|
| `canonical_creative` | 35 | **26** |
| `_forward_compat` | 7 | 0 (private `_Readback*` / `_Delivery*` models) |
| `_ergonomic` | 0 | 0 |

---

## 2. THE FINDING THAT REFRAMES THE WHOLE ITEM

**`canonical_creative`'s 26 public facades do not widen. Ten of them NARROW, by deleting
the v1 `format_id`/`format_ids` fields their documents state.** Measured by diffing each
facade against its own generated base:

| public facade | its generated base | fields the facade REMOVES |
|---|---|---|
| `Creative` | `creative.list_creatives_response.Creative` | `format_id` |
| `CreativeAsset` | `core.creative_asset.CreativeAsset` | `format_id` |
| `CreativeManifest` | `core.creative_manifest.CreativeManifest` | `format_id` |
| `CreativeFilters` | `core.creative_filters.CreativeFilters` | `format_ids` |
| `Product` | `core.product.Product` | `format_ids` |
| `ProductFilters` | `core.product_filters.ProductFilters` | `format_ids` |
| `Placement` | `core.placement.Placement` | `format_ids` |
| `Package` | `core.package.Package` | `format_ids`, `format_ids_pending`, `format_ids_to_provide` |
| `PackageRequest` | `media_buy.package_request.PackageRequest` | `format_ids` |

The other 16 are field-set-neutral; `Format` and `ProductFormatDeclaration` have no
generated base at all.

**That list is this repository's own prohibition, item for item.** `CLAUDE.md`:

> **And `deprecated` is metadata, not absence.** A document stating `format_ids` with
> `deprecated: true` STATES the field; suppressing it from a class (`format_ids = None` at
> class level) makes the class narrower than its document, which reading 1 forbids. Seven
> documents state one of these fields as deprecated-but-present: `core/product.json`,
> `core/package.json`, `core/placement.json`, `core/product-filters.json`,
> `core/creative-filters.json`, `core/creative-manifest.json`, `core/creative-asset.json`.

All seven are in the table above, plus `list-creatives-response.json` and
`package-request.json`. And `format_id` is not even on a removal schedule — `CLAUDE.md`
measures it as naming a removal version at **no** site, with 3 sites not marked deprecated
at all.

**So the withdrawal of `canonical_creative` was deliberate and is CORRECT by this
repository's own reading. It is not an accident to repair.** That is the opposite of what
"a withdrawal broke the patch layer" suggests on its face, and it is why option 2 below is
not simply "fix the harness".

### The coupling, which is the actual problem

`_forward_compat` imports **exactly five names** from `canonical_creative`, at module scope,
line 63–67:

```python
from adcp.types.canonical_creative import CreateMediaBuyRequest as _PublicCreateMediaBuyRequest
from adcp.types.canonical_creative import GetProductsRequest  as _PublicGetProductsRequest
from adcp.types.canonical_creative import PackageRequest      as PublicPackageRequest
from adcp.types.canonical_creative import PackageUpdate       as PublicPackageUpdate
from adcp.types.canonical_creative import UpdateMediaBuyRequest as _PublicUpdateMediaBuyRequest
```

Of those five, **four are field-set-neutral** and one — `PackageRequest` — is a narrowing
facade. So the widening layer is held hostage by the narrowing layer through a single
import, and four fifths of that import is harmless.

---

## 3. Does it load in the drop-in, and what did it cost

Measured on `/srv/ws/dropin-namereach` (the tree behind the `+42 / 0 newly failing` run):

| module | verdict |
|---|---|
| `adcp.types._ergonomic` | **BROKEN** at `adcp/types/_ergonomic.py:98` — `ImportError: cannot import name 'NotificationType' from 'adcp.types._schemas.media_buy.get_media_buy_delivery_response'` |
| `adcp.types._forward_compat` | **BROKEN** at `adcp/types/_forward_compat.py:63` — `ModuleNotFoundError: No module named 'adcp.types.canonical_creative'` |
| `adcp.types.canonical_creative` | **BROKEN** — absent; withdrawn by this repository |
| `adcp.types._eager` | **BROKEN** — via `_ergonomic:98` |
| `adcp.types.aliases` | OK |

**4 of 5 do not load, so their patches never run.** And the two causes are *independent*:

* `canonical_creative` — the withdrawal. Kills `_forward_compat` (17 classes, +3, ~15).
* `NotificationType` — a NAME. Kills `_ergonomic` (2 classes, ~4) and `_eager`. This is
  cause 1's architecture one layer along: their generator emits the enum inline per
  POSITION, ours emits one per SUBJECT at `enums/notification-type.json`, and `_dropin`'s
  module layer hands back the redirected module unwrapped, so a module-path access cannot
  fall through to the flat surface — which answers `adcp.types.NotificationType` fine.

### The cost

| | |
|---|---|
| failing in this run | 1,202 |
| **failing tests naming a patched class or field** | **396** |

**UPPER BOUND on attribution, LOWER BOUND on reach.** Naming a patched class is not proof
the missing patch caused the failure, and a failure the patch would have prevented need not
name the class. By file:

```
  86  tests/test_manifest_response_readback.py        25  tests/test_reporting_webhook_operation_id.py
  25  tests/test_mixed_legacy_projection_regression   18  tests/test_reporting_exact_request_models.py
  17  tests/test_webhooks_deliver.py                  17  tests/conformance/signing/test_webhook_receiver.py
  16  tests/test_no_explicit_null.py                  15  tests/test_decisioning_webhook_emit.py
  14  tests/conformance/test_schema_model_parity.py    10  tests/test_targeting_overlay_errors.py
```

`test_manifest_response_readback.py` at 86 is the `_ReadbackCreativeManifest` annotation
swap; `test_reporting_webhook_operation_id.py` at 25 is the one already written up.

**And two of the 81 unresolved words from the earlier measurement close here:**
`is_canonical_format_kind` and `require_canonical_format_kind` were group D ("no class of
ours, no row"). `_eager.py:926–928` reads both off `canonical_creative`. They are not
missing names — they are casualties of the same withdrawal.

---

## 4. The three options, with costs. **Not a recommendation.**

Carrying an extension is a widening (reading 2), so whether we carry it is an owner-level
decision. Each option below states what breaks if we do it, what stays broken if we do not,
and the test count either way.

### Option A — carry the 22 widenings ourselves; do not revive their modules

**Do:** install the 3 optional fields and 19 annotation widenings from the inventory in a
patcher of ours, under upstream's own constraints and upstream's own retirement guards.

* **Document-legal throughout.** Every one of the 22 admits strictly more than the
  generated class; `core/reporting-webhook.json` carries `additionalProperties: true`, and
  the `canonical_creatives` additions are capability booleans. Nothing is narrowed, so
  reading 1 is not engaged.
* **Breaks:** nothing structurally. But it is still a widening and a *divergence from the
  bundle* — 22 places where our class accepts something no pinned document states. It
  needs the owner's word and a retirement condition per entry, exactly as upstream wrote
  one (`adcp#7895`).
* **Does not fix** `_ergonomic`'s 4 alterations unless they are carried too (they are in
  the 22; `_ergonomic`'s share is the four `disclosure_*` coercers).
* **Test count:** bounded above by **396**; the firmly attributable part is the 25 in
  `test_reporting_webhook_operation_id.py` plus the 86 in
  `test_manifest_response_readback.py` that name the readback facades. Expect well under
  396 and comfortably over 100.
* **Cost:** the largest implementation of the three, and the only one that does not import
  a line of upstream's `types/`.

### Option B — make the withdrawal's repair reach `types/`, via a shim

**Do:** extend `_carry_the_patch_a_withdrawal_needs` to cover `types/`, and give
`_forward_compat` a `canonical_creative` that exposes only the five names it imports —
four of which are field-set-neutral and can simply *be* our generated classes.

* **The trap, and it is the reason this is not the obvious choice:** restoring upstream's
  `canonical_creative` wholesale **re-imports 10 narrowing facades** and deletes
  `format_id`/`format_ids` from nine public classes across seven documents this repository
  has explicitly ruled must keep them. That is reading 1 violated by construction, and it
  would silently reverse the drawcost lane's subject.
* So the shim must bind four names to our classes and decide `PackageRequest` — which
  `_forward_compat` then patches (`~package_request.PackageRequest.targeting_overlay`).
  Binding it to our un-narrowed class is the document-faithful answer and means
  `_forward_compat` patches a class upstream never patched.
* **Breaks:** `_eager` still dies on `NotificationType`, so `is_canonical_format_kind`,
  `require_canonical_format_kind` and the `_ergonomic` share stay absent until the module
  layer gains a fallback.
* **Test count:** the `_forward_compat` share — 17 classes, +3, ~15 — so most of the 396's
  attributable part. `test_manifest_response_readback.py` (86) and
  `test_reporting_webhook_operation_id.py` (25) are both in it.
* **Cost:** smallest code change, highest risk of silently undoing a ruling. It also puts
  upstream's module in the execution path, which is the thing `lay_our_machinery` was
  changed to stop.

### Option C — leave it, and record the attribution

**Do:** nothing, but have `survey/causes.py` own these failures under a cause that names
the withdrawal rather than naming our types.

* **Breaks:** nothing.
* **Stays broken:** up to 396 failures, and — the real cost — they keep being *misread*.
  `operation_id` was already investigated twice as an upstream defect and once as an
  invented field before this measurement; a dead layer does not fail loudly, it fails
  while pointing at something else. Option C is only honest if the cause table says so.
* **Test count:** 0 moved.
* **Cost:** free, and it is the status quo made legible instead of invisible.

---

## 5. The required change to `survey/regenerate.py`, and whose it is

**`survey/regenerate.py` is outside this lane's write scope and the owner is not moving it
— `nocanon` and `drawcost` both hold it.** The instruction, precisely:

> In `_carry_the_patch_a_withdrawal_needs`, the guard
> `if (package / "types") in path.parents or not imports_withdrawn(path): continue`
> excludes `types/` wholesale. Its stated reason — "so the substitution does not creep from
> `types/` into upstream's SDK" — is sound for a module of OURS replacing one of theirs, but
> it also excludes the case where theirs imports a withdrawn module and we have no module at
> that path at all. `types/_forward_compat.py` is that case: it imports
> `adcp.types.canonical_creative` at line 63 and dies, and the function's third clause
> ("ours does not import it") cannot even be evaluated because we have no
> `src/adcp/types/_forward_compat.py`.
>
> The change is NOT to drop the `types/` guard. It is to make the withdrawal's *reach* a
> reported figure: every module in the output that `imports_withdrawn()` and for which this
> repository has no replacement should be COUNTED and NAMED in `strip_their_types`' return
> dict, beside `"their SDK modules the withdrawal broke, replaced by ours"`. Measured on
> this trunk that set is `{types/_forward_compat.py}` — one module, which the build has been
> silently shipping broken.
>
> Whether to then repair it is Option B above and is a separate decision.

**Lane: `drawcost`.** Not `nocanon`: the blocking facade is `canonical_creative`, the
narrowings are `format_id`/`format_ids`, and the seven documents are the ones `drawcost`'s
subject already ranges over. Reviving that module is a decision about the v1 addressing
form, which is that lane's.

**Second instruction, and it needs an owner named** — the `NotificationType` fallback lives
in `_dropin`'s module layer, whose payload source is `survey/dropin/_dropin.py` (there is no
`src/adcp/types/_dropin.py` in this repository). A module path redirected from
`domains/…` to our `_schemas/…` should fall through to the flat surface for a word the
redirected module does not bind, because the N:1 relation guarantees such words exist: their
generator emits a class per position, ours one per subject. No lane currently claims that
file.
