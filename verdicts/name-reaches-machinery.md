# A name reaches into SDK machinery in three places

**The lane:** `namereach`. `survey causes` attributes **72** of the baseline's 1,244
failures to it, over three causes: 19 + 22 + 31.

## The figures. **CORRECTED: the first baseline was another lane's artifact.**

### What was reported, and why it was not a comparison

The first measurement here was `--since /srv/ws/dropin-keyless`, and `dropin-keyless` is
the **keyless-dispatch lane's** output directory. `survey causes --since` now reads the
commit each run recorded and says so:

```
   graded 6d6c29586bea -> f7b2e64d0d7d
   !! NOT AN ANCESTOR.  These two runs graded divergent trees, so
      every figure below is the difference between TWO changes.
```

It reported **+42**, and that number is the difference between this lane's change and
whatever the keyless tree was missing. **It is withdrawn.**

The reading that survives is the per-cause one, which is why it was used for the
attribution in the first place — but one line of that attribution was also wrong, and in
the same direction. It said the asset-union cause went `28 → 2` and credited the
difference to the aliasnote lane "arriving in the rebase". On a proper baseline that cause
was **already at 2**. So the extra 24 was not another lane's fix landing between the two
artifacts; it was work **present in this lane's base and absent from the keyless tree** —
the mirror image of reading another lane's absent work as a regression. Right bottom line,
wrong mechanism, and the mechanism is the part that generalises.

### The correct comparison: a run of this lane's own merge-base

`dropin-strict-base` graded `f53fcb4476b9` — exactly the trunk commit this work branched
from, and an ancestor of trunk. It isolates this lane's single commit:

```
PYTHONPATH=.:src python -m survey causes /srv/ws/dropin-namereach --since /srv/ws/dropin-strict-base
```

```
   graded f53fcb4476b9 -> f7b2e64d0d7d          (no warning: ancestral)
   passed 10596 -> 10614  (+18)
   failed 1220 -> 1202  (-18)
   REGRESSED (ran before, passed before, fails now): 0
   newly collected and failing (never ran before): 0
   FIXED (ran before, failed before, passes now): 18
   no longer collected (was failing, absent now): 0
```

`chunks read: 4` on both sides. **+18, and all four quadrants of the split are clean.** The
per-cause table on the same ancestral pair:

| cause | lane | f53fcb447 | f7b2e64d0 | delta |
|---|---|---|---|---|
| `model_summary` keyed on `__class__.__name__` | namereach | 19 | **1** | **−18** |
| `operation_id` | namereach | 31 | 31 | 0 — write-up only, by design |
| a word resolving at no module | namereach | 22 | 22 | 0 — write-up only, by design |
| the asset union read as a structure | aliasnote | 2 | 2 | 0 — already in this base |
| owned, over 6 lanes | — | 1,007 | 989 | −18 |

So this lane's movement is **exactly −18**, measured directly rather than derived by
subtraction, and the single remaining failure in its first cause is the `_generated.py` row
documented as FINDING 1a (`tests/test_response_str.py` reads 31 passed / 1 failed, the one
being `TestBuildCreativeResponseMessage::test_error`).

**Both artifacts above collect 13,818.** The provisioning fix has since taken trunk to
**15,285** — 1,468 more tests actually running — so every per-cause count in this file is
on the smaller population and the two open causes below want re-reading on the larger one.

The other two causes are unmoved on purpose: both are measurements, and neither admits a
change inside this lane's write scope. `tests/test_postal_area_compat.py` holds at 21
failed / 10 passed and `tests/test_reporting_webhook_operation_id.py` at 25 failed / 11
passed.

`./check` is UNMOVED on all three figures: `emitted 1059 / refused 0`,
`primary 0 / chained 0`, `approximated 383 facts in 148 documents`. `make lint` reads
**255** and `make typecheck` **4,118 errors in 694 files** both before and after — verified
by swapping `base.py` for trunk's and re-running, so these files add none.

Each cause below carries the document and the pointer it rests on. Two of the three
turned out to be something other than what the brief premised, and both corrections are
stated where they arise rather than buried: **cause 2 is one member of an 81-word class
and not a single word**, and **cause 3's field is not invented — it is a declared,
document-legal SDK extension, so there is no upstream issue to file.**

---

## Cause 1 — `model_summary()` was keyed on a SPELLING. FIXED.

**Status: repaired at `f7b2e64d0`.** Moves 18 of the 19 the rule claims.

### What it was

`src/adcp/types/base.py` is upstream's module, kept as machinery, and its formatter
registry is keyed on upstream's own published class names:

```python
formatter = _RESPONSE_MESSAGE_REGISTRY.get(self.__class__.__name__)
```

Their generator emits a class per POSITION and names it from there —
`CreateMediaBuyResponse1` means "the first arm of that document's `oneOf`". This
repository emits one class per SUBJECT and names it from the subject's own document,
arriving at `CreateMediaBuySuccess`. So the registry asked for one of upstream's
spellings, an object of ours answered with a different one, and every formatter missed:
`tests/test_response_str.py` read `"CreateMediaBuySuccess response"` where
`media-buy/create-media-buy-response.json#/oneOf/0` has a message registered for it.

### The resolution, and the count the brief asked for

The relation is already held: `survey/name_table.py` resolved every one of upstream's
9.6.1 words to the class of ours denoting one subject, by rule, and
`survey/emit_legacy_names.py` emitted those rows as the alias layer `adcp.types`
consults. `base._subject_message_registry()` asks the public surface for each of
upstream's words once, on first use, and keys the formatters on `__adcp_schema__`.

| | |
|---|---|
| registry keys (upstream's words) | **19** |
| **resolved to a class of ours stating a subject** | **19** |
| **unresolved** | **0** |
| distinct subjects reached | 19 (no two words collide) |
| of those, same word on both sides | 5 |

**Zero unresolved**, so there is no finding of the "formatter for a type we do not emit"
or "word the table declines as ambiguous" kind. The five that agree are the five whose
document declares no `oneOf`, so their generator had no arm to number
(`get-products-response`, `list-creative-formats-response`, `get-signals-response`,
`list-creatives-response`, `get-media-buy-delivery-response`, each at `#`).

Keyed on the subject and not on the resolved class's `__name__` because our generated
names are generator-derived too and a numbered one can renumber on a schema bump, while
the document and pointer ARE the subject. The class-name probe is kept BEHIND the
subject probe for an object that states no subject — one of upstream's own hand-written
classes — and the generic `"<name> response"` is kept for a type with no formatter,
which is correct upstream behaviour and not a miss. `tests/test_the_summary_finds_our_class.py`
grades all three.

### FINDING 1a — the 19th is a wrong row in `_generated.py`, not a summary defect

`tests/test_response_str.py::TestBuildCreativeResponseMessage::test_error` still fails,
and `model_summary` is answering correctly. The test imports
`from adcp.types._generated import BuildCreativeResponse2`, and that row points at the
wrong subject.

`media-buy/build-creative-response.json` declares six `oneOf` arms, and the two bundles
order them differently:

| upstream's class | its required set | our class, same required set | our pointer |
|---|---|---|---|
| `BuildCreativeResponse1` | `creative_manifest` | `BuildCreativeSuccess` | `#/oneOf/0` |
| `BuildCreativeResponse2` | **`errors`** | **`BuildCreativeError`** | **`#/oneOf/4`** |
| `BuildCreativeResponse3` | `creative_manifests` | `BuildCreativeMultiSuccess` | `#/oneOf/1` |
| `BuildCreativeResponse4` | `creatives` | `BuildCreativeVariantSuccess` | `#/oneOf/2` |
| `BuildCreativeResponse5` | `estimate` | `BuildCreativeEstimate` | `#/oneOf/3` |
| `BuildCreativeResponse6` | `task_id` | `BuildCreativeResponseSubmitted` | `#/oneOf/5` |

(Upstream's column measured off the 9.6.1 wheel: `f.is_required()` over
`adcp.types.domains.media_buy.build_creative_response.BuildCreativeResponse{1..6}`. Ours
off `src/adcp/types/_schemas/media-buy/build-creative-response.json`.)

`src/adcp/types/_generated.py:51` says:

```python
from adcp.types.media_buy import BuildCreativeMultiSuccess as BuildCreativeResponse2
```

which matched by POSITION — the second arm — where upstream's `BuildCreativeResponse2`
is the arm requiring `errors`. `survey/name-table-9.6.1.json` gets it RIGHT
(`their: BuildCreativeResponse2 → ours: ...BuildCreativeError`, and
`adcp.types.BuildCreativeResponse2` resolves to `BuildCreativeError` through the alias
layer), so the two layers disagree about one of upstream's words.

`_generated.py` is generated by `survey/adapter_surface.py` and is not mine to edit. The
required change is one row: `BuildCreativeResponse2 → BuildCreativeError`, plus the three
rows the module is missing entirely (`BuildCreativeResponse3`, `4`, `5` — see the table).
A positional match is the defect; the required set is what identifies the arm.

---

## Cause 2 — `adcp.types.GeoPostalArea`. DIAGNOSED; no code change in scope.

**21 failures in `tests/test_postal_area_compat.py`** (the rule claims 22 — see
FINDING 2c, it mis-claims 4 of these and one elsewhere).

### What upstream's `GeoPostalArea` actually is

**It is not a class.** It is a single hard-coded branch in upstream's own
`adcp/types/__init__.py` module-level `__getattr__` (wheel line 1178), deliberately kept
out of `__all__` — their comment: *"Deprecated backward-compat alias (kept out of
``__all__``)"*. It resolves to `adcp.types._generated.PostalArea2`, caches itself into
`globals()` so the warning fires once, and emits a `DeprecationWarning` naming the
migration target.

So the word HAS a schema subject, and reading 10's "a name with no schema subject takes a
migration note and never a class" does not apply. The subject is:

| | |
|---|---|
| document | `core/postal-area.json` |
| pointer | `#/anyOf/1` — the legacy arm, `{system, values}` with country-fused tokens |
| upstream's class | `adcp.types.domains.core.postal_area.PostalArea2` |
| **our class** | **`adcp.types._schemas.core.postal_area.PostalArea2`** |
| table row | `their: PostalArea2 → ours: ...postal_area.PostalArea2` (`how: name`) — present |

It is **not** in `legacy_names.__adcp_ambiguous__` (measured: 194 words are, this is not
one), so it is not a declined guess.

### Why no rule reached it — and the answer is not a rule

`survey/name_table.py` reads its population from `/tmp/bind_up.json`, a dump of
upstream's **bindings**. `GeoPostalArea` is not a binding: it exists only inside a
`__getattr__` body, is absent from `__all__`, and appears in `dir(adcp.types)` only
*after* someone has already accessed it (their `__dir__` is
`sorted(set(__all__) | set(globals()))`). My own probe had to add the word by hand to see
it at all.

**So none of the nine rules could have reached it, because the word was never in the
input.** `signature`, `collapse`, `branch-order`, `name`, `property-key`, `their-default`,
`cross-name`, `cross-subject` and `cross-required` all range over `(their name, our
candidates)` pairs drawn from that dump; a word with no row in the dump has no pair to
match. **The required change is to the INPUT, not to a rule** — the binding dump must
also carry a word upstream's own module `__getattr__` publishes.

### The required row — WAITING ON `drawcost`, which owns these files

`survey/name_table.py`, `survey/emit_legacy_names.py` and
`src/adcp/types/legacy_names.py` were removed from my write scope mid-task. The precise
instruction:

```
word:   GeoPostalArea
target: ("adcp.types._schemas.core.postal_area", "PostalArea2")
how:    upstream's own alias target, read off their __getattr__ branch — not a
        structural match. The row's provenance is their declaration, so it belongs
        to a tenth input (the __getattr__-published words) and not to a tenth rule.
why no rule fired: the word is absent from /tmp/bind_up.json. It is not a binding.
```

**Verified, not asserted.** Our `PostalArea2` satisfies every behavioural assertion in
the file, measured directly in the drop-in tree:

* all **11/11** legacy country-fused tokens construct and dump to `{system, values}`
  (`us_zip`, `us_zip_plus_four`, `gb_outward`, `gb_full`, `ca_fsa`, `ca_full`, `de_plz`,
  `fr_code_postal`, `au_postcode`, `ch_plz`, `at_plz`);
* `TypeAdapter(PostalArea).validate_python(PostalArea2(system="gb_outward", values=["SW1A"]))`
  round-trips through the legacy arm with no injected `country`;
* `TargetingOverlay(geo_postal_areas=[...])` dumps `[{"system": "us_zip", "values": ["10001"]}]`;
* the old `{system, values}` construction shape dumps unchanged.

### FINDING 2a — a row alone fixes 15 of 17; two tests need an ACCESSOR

An alias row emits `from M import C as W` and **cannot warn**. Two tests assert the
warning:

* `test_geo_postal_area_access_emits_deprecation_warning` — `pytest.warns(DeprecationWarning, match="GeoPostalArea is deprecated")`
* `test_geo_postal_area_warning_names_postalarea_migration` — the message must contain `PostalArea`, `backward compatibility`, `future major`

and the file's `autouse` fixture pops `adcp.types.__dict__["GeoPostalArea"]` before each
test, so the warning must fire on *first access* and cache. That is a deprecating
descriptor or a `__getattr__` branch, not an alias. **Whoever lands the row should know it
closes 15 of the 17 and not all of them**, and that the remaining two want a decision on
where a warning-emitting accessor lives in our tree — our `adcp.types/__init__.py` facade
has the same PEP 562 shape upstream used.

### FINDING 2b — `GeoPostalArea` is one of 81, and the class partitions cleanly

Measured on the drop-in surface against upstream's published words
(`__all__ | _EAGER_ONLY_EXTRAS | {GeoPostalArea}`, 972 words). **Searched the whole
emitted tree** — `pkgutil.walk_packages` over `adcp.types._schemas`, not one module scope:

| | count | the answer |
|---|---|---|
| upstream's published words | 972 | |
| **unresolved on our surface** | **81** | |
| A — DECLINED as ambiguous by the table | 17 | a domain path; the refusal is deliberate |
| B — a class of ours of that NAME exists, unbound | **0** | nothing here is a missed binding of its own word |
| C — a table row exists, its target is gone | 18 | the row's class was renamed; the row is stale |
| D — no class of ours of that name, no row | 46 | each needs its own reading |

`GeoPostalArea` sits in **D** by that test — but D's criterion is the NAME, and for
`GeoPostalArea` the SUBJECT is held under a different name (`PostalArea2`). That is the
N:1 relation, and it means **D is not a single verdict**: some of its 46 are
`GeoPostalArea`'s shape (subject held, word unbound) and some are genuinely subjectless.
The 18 in C are the sharper finding — a stale row is worse than a missing one, because
the emitter skips the word silently when its target no longer imports:

```
AuthorizedAgentsByInlineProperties  AuthorizedAgentsByPropertyId  AuthorizedAgentsByPropertyTag
AuthorizedAgentsByPublisherProperties  AuthorizedAgentsBySignalId  AuthorizedAgentsBySignalTag
ComplySimulationResponse  CpmVendorPricingOption  CustomVendorPricingOption
FlatFeeVendorPricingOption  InlineDaastAsset  InlineVastAsset  PerUnitVendorPricingOption
PercentOfMediaVendorPricingOption  UrlDaastAsset  UrlVastAsset
VerifyBrandClaimsPayload  VerifyBrandClaimsSignedResponse
```

### FINDING 2c — the `causes` rule over-claims; 4 of these 21 are not this cause

`survey/causes.py:102`:

```python
lambda nid, txt: "resolves at no module" in txt or "test_postal_area" in nid,
```

The second clause claims by FILE NAME. The file's 21 failures are **17 + 4**:

* **17** are `AttributeError: adcp.types.GeoPostalArea resolves at no module` (15 raise it
  directly; 2 surface as `DID NOT WARN` because `pytest.warns` reports the missing
  warning first). These are the cause.
* **4 are a different defect entirely** — the error MESSAGE for a country/postal-system
  mismatch:
  * `test_native_postal_country_system_mismatches_fail_closed[US-plz]`
  * `test_native_postal_country_system_mismatches_fail_closed[DE-zip]`
  * `test_native_postal_country_system_mismatches_fail_closed[NL-plz]`
  * `test_targeting_overlay_rejects_mismatched_postal_pair`

  All four expect `postal system .* is not valid for country`. Our tree **fails closed
  correctly** — `TypeAdapter(PostalArea).validate_python({"country": "US", "system":
  "plz", ...})` raises — but with the generic branch message
  `is not valid under any of the 2 branches [type=anyOf]`. No name is unresolved here;
  it is an error-message fidelity question over `core/postal-area.json`'s country↔system
  pairing, and it belongs to whichever lane owns conditional messages, not to `namereach`.

A fifth, `tests/test_freezegun_models.py`, matches the first clause
(`resolves at no module`) for a word that is not `PostalArea` — that one the rule claims
correctly. **Suggested rule:** drop the `or "test_postal_area" in nid` clause and keep
the signature match; the 4 then fall to the residue, where they can be read.

---

## Cause 3 — `ReportingWebhook.operation_id`. THE PREMISE IS WRONG, AND THERE IS NO ISSUE TO FILE.

**31 failures claimed by the rule; 17 name both `ReportingWebhook` and `operation_id`,
25 of the 36 in `tests/test_reporting_webhook_operation_id.py` fail.**

The brief's reading was: *"our class is right and their class carries a field its document
does not state"*, with instructions to write it up, leave the tests failing, and draft an
upstream issue. The first half of the measurement confirms the document. **The second
half overturns the conclusion.**

### Step 1 — the document, and it is the same one

| | |
|---|---|
| document | `core/reporting-webhook.json`, title `"Reporting Webhook"` |
| properties | `url`, `token`, `authentication`, `reporting_frequency`, `requested_metrics` — **five** |
| required | `authentication`, `reporting_frequency`, `url` — **three** |
| `operation_id` | **absent** |
| `additionalProperties` | **`true`** |

Upstream's class is at `adcp/types/domains/core/reporting_webhook.py`, and their generator
derives that module path from the document path, so the pairing is
`core/reporting-webhook.json` → `domains/core/reporting_webhook.py`. There is **exactly
one** `class ReportingWebhook` in the whole wheel (`grep -rn "class ReportingWebhook"`
over `types/domains/`), so **this is not a naming collision.**

Nor is it a bundle-version difference. Upstream's wheel ships its own schemas, and
`operation_id` is absent from `core/reporting-webhook.json` in **all four** of them —
`3.0`, `3.1`, `3.1.15`, `3.2` — each with the same five properties and same three
required, identical to our pin.

### Step 2 — but the field is NOT in their generated class, and NOT invented

Upstream's generated source declares exactly the document's five fields. `operation_id`
is installed at import by `adcp/types/_forward_compat.py:505`:

```python
# 3.2.x permits additional registration fields but does not declare this ID.
# Keep the extension outside generated code so a schema refresh cannot drop
# it again. AdCP 3.3 adds the same optional field with the same constraints
# (adcp#7895); once a bundle declares it, this guard makes the patch a no-op.
if "operation_id" not in ReportingWebhook.model_fields:
    ...
```

So the field is:

* **document-legal** — `additionalProperties: true`; the schema *permits* it;
* **optional and `NoExplicitNull`** — the class is not narrower than its document and
  admits every document-valid payload;
* **declared, versioned and self-retiring** — it names its forward spec (AdCP 3.3,
  `adcp#7895`) and the guard makes the patch a no-op once a bundle declares the field;
* **deliberately kept out of generated code**, in their words, "so a schema refresh
  cannot drop it again".

### The conclusion, corrected

**There is no upstream issue to file, and I have not drafted one.** The brief's branch 3
("if it is the same document, write the finding up and LEAVE THE TESTS FAILING — a test
whose EXPECTATION contradicts its document is a finding") does not trigger, because the
expectation does **not** contradict its document: a document with
`additionalProperties: true` does not forbid the property, and upstream has not claimed
it is a spec field. Filing it would report a deliberate, documented extension as an
invented field.

The tests are LEFT FAILING — but as a gap on our side, not an upstream defect, and not
because a test is wrong.

### FINDING 3a — the real cause: the drop-in never RUNS upstream's `_forward_compat`

Measured in the drop-in tree:

```
adcp.types._forward_compat  → ModuleNotFoundError: No module named 'adcp.types.canonical_creative'
adcp.types._ergonomic       → ImportError: cannot import name 'NotificationType' from
                              'adcp.types._schemas.media_buy.get_media_buy_delivery_response'
adcp.types._eager           → (same NotificationType)
```

`_forward_compat.py` is present in the tree — kept as machinery — and **dies at module
scope on line 63**, importing `adcp.types.canonical_creative`. That is *exactly* the one
module `survey/regenerate._withdrawn_by_this_repository()` names: this repository carried
upstream's `canonical_creative.py` and deliberately deleted it, so `strip_their_types`
unlinks upstream's copy too.

The harness already knows a withdrawal breaks importers —
`_carry_the_patch_a_withdrawal_needs` replaces upstream's `src/adcp/client.py` and
`src/adcp/server/responses.py` with ours for this reason — but it **explicitly skips
`types/`**:

```python
if (package / "types") in path.parents or not imports_withdrawn(path):
    continue
```

with the stated reason "so the substitution does not creep from `types/` into upstream's
SDK". The consequence is that upstream's whole import-time patch layer is dead in the
drop-in, and `ReportingWebhook.operation_id` is one of its patches. `canonical_creative`
is named in **29** failures.

Not repairable inside my write scope (`survey/regenerate.py` is not in it), and it is a
POLICY question before it is a code one, so it is stated rather than guessed at:

1. **Carry the extension ourselves** — an optional `operation_id` on our
   `ReportingWebhook`, document-legal under `additionalProperties: true`, with upstream's
   constraints (`^[A-Za-z0-9_.:-]{1,255}$`, `NoExplicitNull`) and upstream's own
   retirement condition. This is what closes the 25 tests. It is **not** a field added to
   a generated class in the prohibited sense — the document admits it — but it is still a
   widening and wants the owner's word.
2. **Make the withdrawal's repair reach `types/`** — give `_forward_compat` a path that
   does not import `canonical_creative`. This revives patches beyond `operation_id` and
   changes more than one lane's numbers.
3. **Leave it** — accept that the drop-in does not grade upstream's opt-in extensions,
   and record these 25 as attributable to the withdrawal rather than to our types.

### FINDING 3b — `NotificationType` is Cause 1's architecture at the MODULE layer

`_ergonomic` and `_eager` die on a different name, and it is the same N:1 relation:

| | |
|---|---|
| upstream's import | `adcp.types.domains.media_buy.get_media_buy_delivery_response.NotificationType` |
| their emission | an inline enum per POSITION, in the delivery-response module |
| our emission | one class per SUBJECT: `enums/notification-type.json` → `adcp.types._schemas.enums.notification_type.NotificationType` |

`_dropin`'s module layer redirects `domains/...` to our `_schemas/...` module, and that
module does not bind the word — so the module-path access raises even though
**`adcp.types.NotificationType` resolves fine** through the flat surface (measured; it is
*not* in `__adcp_ambiguous__`). The redirected module is handed back unwrapped, so there
is no fallback from a module path to the flat surface.

**Measured consequence: ~0 test movement.** Nothing in upstream's suite imports
`_ergonomic`, `_forward_compat` or `_eager` (0 failures name any of the three) — their
tests reach types through `adcp.types`, which in the drop-in is OUR facade, and our facade
does not run upstream's patchers. So repairing this unblocks three imports nobody makes.
Recorded because it is the same defect as Cause 1 one layer along, and because it is the
mechanism behind FINDING 3a's second option: any attempt to revive `_forward_compat` hits
`NotificationType` next.

---

## What FINDING 3a turned into

`_forward_compat` dying on the `canonical_creative` withdrawal is not one module's import
error: it is a whole layer of upstream's behaviour absent from every run graded so far.
Measured separately, with an instrument, in **`verdicts/the-dead-patch-layer.md`** — 19
classes, 3 fields added, 19 altered, 4 of 5 patchers not loading, up to 396 failures in
reach — and with the finding that reframes it: `canonical_creative`'s facades do not widen,
they **delete `format_id`/`format_ids` from nine public classes across seven documents this
repository has ruled must keep them. The withdrawal was correct.**
