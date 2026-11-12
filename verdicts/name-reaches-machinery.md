# A name reaches into SDK machinery in three places

**The lane:** `namereach`. `survey causes` attributes **72** of the baseline's 1,244
failures to it, over three causes: 19 + 22 + 31.

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
