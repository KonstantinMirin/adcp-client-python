# FINDINGS — del1: removing the previous generator's naming-surface tests

Scope was five test files. Removal test applied per assertion: it goes if what it
asserts is a NAME, a `__module__`, an `__all__` membership, or a class identity; it
stays if it constructs a payload and asserts the model accepts or refuses it, or
asserts a dump's content.

## Counts

| file | before | after | removed | still red |
|---|---|---|---|---|
| `tests/test_collision_aliases.py` | 208 (207F / 1P) | 1 (1P) | **207** | 0 |
| `tests/test_authorized_agents_public_surface.py` | 29 (29F / 0P) | 1 (1F) | **28** | 1 |
| `tests/test_mixed_legacy_projection_regression.py` | 35 (26F / 9P) | 35 (26F / 9P) | **0** | 26 |
| `tests/test_postal_area_compat.py` | 31 (21F / 10P) | 27 (18F / 9P) | **4** | 18 |
| `tests/test_scalar_roots.py` | 24 (16F / 8P) | 20 (11F / 9P) | **4** | 11 |
| **total** | **327** | **84** | **243** | **56** |

One commit per file, except `test_mixed_legacy_projection_regression.py`, which
needed no edit.

### What kind of assertion came out, per file

- **`test_collision_aliases.py` — 207 items.** 67 aliases × 3: alias-identity
  (`alias is <Base>N from <module>`), public-surface name presence + `__all__`
  membership, and `aliases.__all__` membership. Plus 6 singles: a DurationUnit
  alias-identity compat check, an alias-table name-uniqueness check, a
  distinct-class identity sweep, an `is_required()` field-shape check, a
  `ListCreativesCreative` identity/`__all__` check, and a TmpxMacro alias-shape
  check. Subjects were addressed by the previous generator's ordinal spellings
  (`AccountReference1`, `VendorPricingOption3`, `UpdateMediaBuyResponse2`,
  `Creatives1`).
- **`test_authorized_agents_public_surface.py` — 28 items.** 7 class-identity, 7
  name-promise (checking a resolved class's `authorization_type` default rather
  than any payload), 6 facade-agreement identity, 1 union-membership
  (`__args__` is variants 1–6 in order), 7 import-order probes asserting each
  name's `__module__` + `__qualname__` string in a subprocess.
- **`test_postal_area_compat.py` — 4 items.** 1 name-resolution
  (`adcp.types.GeoPostalArea is not None`), 2 deprecation-warning-on-attribute-access,
  1 negative name assertion. Also dropped the `_reset_geopostalarea_cache` autouse
  fixture, which existed only for the two warning tests.
- **`test_scalar_roots.py` — 4 items + 1 line.** A `__module__`/cross-surface
  identity sweep, an `issubclass(..., RootModel)` check keyed on old spellings, an
  `issubclass`/allowed-keyword population sweep, a `repr` type-name check, and the
  `type(restored) is PropertyTag` line inside the copy/pickle test.

Nothing was removed from `test_mixed_legacy_projection_regression.py`: every test
there drives a request through `create_tool_caller` and asserts on the response,
the params the seller received, or the error raised. No test in it asserts a name,
a `__module__`, an `__all__` membership, or a class identity.

---

## Left red, with why

56 items. All construct a payload or assert a dump's content, so all are outside
the removal mandate. Grouped by cause, most serious first.

### 1. `PropertyTag` and the scalar roots are `Annotated` aliases, so constraints no longer bind at construction

`tests/test_scalar_roots.py` — 11 red.

`adcp.PropertyTag` is now `typing.Annotated[str, FieldInfo(...pattern='^[a-z0-9_]+$'...)]`,
a `typing._AnnotatedAlias`, not a `str` subclass. Calling it is calling `str()`:

```
PropertyTag("Invalid-Tag")  -> 'Invalid-Tag'     (expected ValidationError)
PropertyTag(5)              -> '5'               (expected ValidationError)
PropertyTag()               -> ''                (expected TypeError)
```

This is the precise construct the module's own docstring names as the reason the
type must be a subclass: *"an annotated alias only enforces its constraints inside
a Pydantic field, so `PropertyTag("Invalid-Tag")` would succeed."* It does succeed.
Issue #1277 is the history here, and the generated-tree rewrite
(`post_generate_fixes.rewrite_scalar_rootmodels`) has not run: the exported
scalar-root population is **3**, and those 3 are the `ScalarStr` / `ScalarInt` /
`ScalarFloat` bases themselves, not generated types.

Secondary measurements on the same cause:

- `ViewThreshold` is not importable from `adcp.types` (3 of the 11).
- `TypeAdapter(PropertyTag).json_schema()` keeps `type`, `pattern` and
  `description`, and **drops `title` and `examples`**.
- The `RootModel` compat shims are gone: `root=` is now an invalid `str()` keyword
  argument, and `.root` raises `AttributeError`.

**Two kept tests pass but no longer grade anything.** Flagging both rather than
leaving them as false assurance:

- `test_no_scalar_rootmodels_remain_in_generated_tree` passes because nothing wraps
  a scalar in a `RootModel` any more — the types became annotated aliases instead.
  It cannot distinguish "rewritten correctly" from "never emitted".
- `test_every_scalar_root_example_round_trips` passes while sweeping a population
  of 3 bases. It is vacuous.

### 2. `src/` imports two names the generated surface does not provide

`tests/test_mixed_legacy_projection_regression.py` — 26 red. Both causes are in
`src/`, outside this task's write scope, so the file was not touched.

- **50 of the 52 failure lines:** `cannot import name 'SyncCreativeResult' from
  'adcp.types'`, raised from `src/adcp/server/_creative_batch.py:31`.
  `src/adcp/types/aliases.py:270` deliberately refuses that name with a
  `DOCUMENT-NO-WORD-NO-IDENTITY` marker pointing at
  `adcp.types.domains.creative.sync_creatives_response.Creative`, while
  `src/adcp/__init__.py` still exports it. Server code and the alias layer
  disagree about whether the name exists.
- **2 failure lines:** `'ImageFormatDeclaration' object has no attribute
  'legacy_format_refs'`. `src/adcp/canonical_formats/{v1_to_v2,v2_to_v1,format_options}.py`
  read `declaration.legacy_format_refs`; the generated declaration states
  **`v1_format_ref`**, which is also the document's word and the spelling
  `CLAUDE.md` uses for the seller-asserted v2 → v1 mapping. `legacy_format_refs`
  is a name no document states.

### 3. The `GeoPostalArea` compat name is gone; the wire shape it aliased is not

`tests/test_postal_area_compat.py` — 14 of the 18 red.

Old-shape construction, the 11 legacy fused tokens, the union legacy-arm check and
the overlay acceptance check all construct through `adcp.types.GeoPostalArea`,
which no longer resolves.

The legacy arm itself is unaffected:
`test_raw_legacy_value_round_trips_through_postalarea_adapter` passes, validating
`{"system": "us_zip", "values": ["10001"]}` straight through `PostalArea` and back.
So what was removed is the deprecated compat name, not the wire contract.

### 4. The postal country/system refusal still fails closed, but lost its message

`tests/test_postal_area_compat.py` — the other 4 red.

These assert `match="postal system .* is not valid for country"`. The refusal is
intact — `US`/`plz`, `DE`/`zip` and `NL`/`plz` are all rejected — but now as a
generic 9-to-10-error union mismatch with no cross-field message. The safety
property holds; only the diagnostic regressed.
`test_schema_validation_rejects_mismatched_postal_pair` still passes and still
pins the pointer `/targeting_overlay/geo_postal_areas/0`.

### 5. `adcp.types.AuthorizedAgents` is gone, and `property_ids` items are no longer scalar roots

`tests/test_authorized_agents_public_surface.py` — 1 red.

`adcp.types.AuthorizedAgents` no longer resolves; the surface directs callers to
`adcp.types.<domain>`. The subject is now
`AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPropertyIds`,
and it accepts the test's exact fragment with `authorization_type ==
"property_ids"`.

There is a second, independent delta underneath the renaming: `property_ids` items
come back as plain `str`, so the kept assertion
`[p.root for p in agent.property_ids]` fails there too with `'str' object has no
attribute 'root'`. That is the same unwrapping as finding 1, reached from a
different direction, and it is a behavioural change rather than a rename.
