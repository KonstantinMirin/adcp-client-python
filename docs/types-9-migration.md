# Generated types in 9.0: migration guide

Release 9.0 lands a batch of code-generator changes that make `adcp.types`
agree with the AdCP JSON Schemas it is generated from. Each one is a breaking
change on its own; this page collects them so a migration can be done in one
pass. The pull requests are linked for the full rationale and measurements.

| Change | PR | What breaks |
| --- | --- | --- |
| Scalar schema roots are plain `str`/`int`/`float` subclasses | #1286 | `issubclass(X, RootModel)`, `X.model_validate`/`model_dump`/`model_json_schema` on 224 scalar types |
| A composing schema root is emitted as what it composes | #1353 | `.root` on 114 union/single-model roots; `TypeName.model_validate` on a union root |
| Structural pointer refs resolve to the type they select | #1371 | 47 per-position `RootModel` wrapper names under `adcp.types._generated` |
| Generated models validate `boolean`/`integer`/`number` strictly | #1375 | Payloads that relied on `"yes"`, `"1"`, `1` coercion |
| Root-level `anyOf`/`oneOf` required groups are enforced | #1368 | Documents that omit every required group of 42 request/response models, on generated and canonical names alike |

Nothing is removed from `adcp` or `adcp.types`: every name importable before
is importable after, and the ten additions (`Issue`, `AdcpVersionEnvelope`,
seven `*Details` error models and `FormatReferenceStructuredObject` under
`adcp.types.legacy`) come with #1367. Identity changes on the public surface
are of exactly the kinds the table names and are pinned by
`tests/fixtures/public_api_snapshot.json`.

## 1. Scalar roots are the scalar (#1286)

A schema whose root is a scalar — `core/property-tag.json` is
`{"type": "string", "pattern": "^[a-z0-9_]+$"}` — generates a `str`, `int` or
`float` subclass instead of `RootModel[str]`.

```python
# before
tag = PropertyTag(root="sports")
code = country.root
PropertyTag.model_validate("sports")

# after
tag = PropertyTag("sports")          # tag == "sports", hash(tag) == hash("sports")
code = country                       # it already is a str
TypeAdapter(PropertyTag).validate_python("sports")
```

`.root` and `X(root=...)` keep working behind a `DeprecationWarning`.
`issubclass(X, RootModel)` is `False` and the `model_*` classmethods are gone,
because the type is no longer a Pydantic model: use `TypeAdapter(X)`.

Integer and number roots validate the way their fields do under #1375:
strictly, with a float carrying no fractional part narrowed to `int`.

## 2. Composing roots are what they compose (#1353)

A root that is a union of models becomes an `Annotated[A | B, Field(...)]`
alias carrying the schema's discriminator; a root that is a single model
becomes a subclass of that model.

```python
# before
event = WholesaleFeedEvent.model_validate(payload)
inner = request.start_time.root

# after
event = TypeAdapter(WholesaleFeedEvent).validate_python(payload)   # honours the discriminator
inner = request.start_time
```

A single-model root such as `CheckGovernanceRequest` keeps
`model_validate(...)` and can now be subclassed with `extra="forbid"`.

## 3. Pointer refs resolve to the selected type (#1371)

A `$ref` into another schema's `properties`/`items` no longer mints a
single-arm `RootModel` wrapper per referencing site. Request-side overlays
read like response-side ones:

```python
# before: TargetingOverlayInput.geo_countries was GeoCountries (a wrapper); len() raised
# after
for country in overlay.geo_countries:
    code: str = country
```

The removed names were reachable only under `adcp.types._generated`, which is
documented as internal; the per-name replacement table is in #1371. A pointer
to an object or enum property still resolves to the one shared class
(`targeting.AgeRestriction`, `ProductResponseField`).

## 4. Strict scalars (#1375)

`type: boolean`, `integer` and `number` fields refuse what the bundled JSON
Schema refuses:

```python
ListAccountsRequest.model_validate({"sandbox": "yes"})   # before: sandbox=True; after: ValidationError
Budget.model_validate({"amount": "100"})                 # ValidationError; send 100 or 100.0
Count.model_validate({"value": 1.0})                     # still accepted, narrowed to 1
```

The bundled schema validator additionally checks `format: uri` and
`format: hostname`, so a malformed URL in a response fails response validation.

## 5. Root required groups (#1368)

42 models enforce the root-level `anyOf`/`oneOf` their schema declares.
`CreateMediaBuyRequest` needs packages, a budget, or a proposal; a document
with none raises `ValidationError` naming the groups. The rule reaches the
canonical names in `adcp.types` too: a canonical model is a subclass of the
generated class, so it inherits every validator that class declares and
`adcp.CreateMediaBuyRequest` and the generated class agree.

```python
CreateMediaBuyRequest.model_validate({**unconditional_fields})
# ValidationError: CreateMediaBuyRequest requires at least one of these field groups:
#   packages | total_budget+proposal_id | ...
```

Presence is what counts: an explicit `null` satisfies a group, a default the
caller never sent does not.

## Also in this batch (not breaking)

* `adcp.types.domains.<domain>[.<schema>]` and `adcp.types.error_details`
  (#1367) give every generated class a public path, and the public API
  snapshot records what each name resolves to.

  The generator writes there directly now, so the private
  `adcp.types.generated_poc` tree is gone. Every module stem moved unchanged,
  which makes the migration a prefix rename:

  ```python
  -from adcp.types.generated_poc.media_buy.package_request import PackageRequest
  +from adcp.types.domains.media_buy.package_request import PackageRequest
  ```

  `adcp migrate v3-to-v4` rewrites those lines. The old path also still
  resolves through the whole 9.x line, emitting a `DeprecationWarning` that
  names the new one — #1360 measured 110 such imports in a single production
  seller, and 9.0 does not break all of them at once. **It is removed in
  v10.** What the old path returns is the *same module object*, so
  `adcp.types.generated_poc.core.format_id.FormatReferenceStructuredObject is
  adcp.types.domains.core.format_id.FormatReferenceStructuredObject` — an
  `isinstance` check cannot start failing because a class was reached by its
  old name. Prefer the flat `adcp.types` surface where the name you need is
  bound there, as `docs/type-surface.md` describes.
* `scripts/generate_types.py --check` runs in CI, grades every post-generation
  fix against `scripts/post_generation_manifest.json`, and the generator's
  input order is total, so a regeneration is byte-identical on every
  filesystem (#1374).
* `canonical_creative.pyi` is gone (#1366). Every canonical model is now a real
  subclass of the generated wire model it refines, so there is nothing left to
  declare by hand: mypy reads `canonical_creative.py` and sees the actual
  inherited fields. The stub is not regenerated — it was deleted, because the
  thing it was transcribing is ordinary source. A program that type-checked
  against the old stub while constructing `CreateMediaBuyRequest` without
  `brand`, `start_time`, `end_time` or `idempotency_key` now fails mypy, as it
  always failed at runtime.

  One static-typing consequence comes with that. The runtime still coerces the
  wire string for an enum-typed parameter — `PackageRequest(product_id="p1",
  pricing_option_id="po1", pacing="even")` returns `Pacing.even` — but mypy and
  pyright now read the generated `Pacing | None` and reject the `str`. An
  adopter constructing a canonical model directly passes the enum member
  (`pacing=Pacing.even`) or goes through `model_validate`, which takes the wire
  document unchanged. This is not a regression against the hand-written stub:
  that stub did not declare `pacing` at all, so the same call was refused there
  too, as an unexpected keyword rather than a wrong type.

  The legacy-identity fields the canonical models remove — `format_id`,
  `format_ids`, `format_ids_pending`, `format_ids_to_provide` — are declared in
  a `TYPE_CHECKING` block with `init=False`, so a type checker refuses the
  keyword the runtime refuses instead of offering a constructor argument that
  raises `ValidationError`. Read them and you get `None`.
* A format reference's `agent_url` is carried as the wire string, validated
  as a URL (#1384). `ref.agent_url` is a `str`, not an `AnyUrl`, so
  `migrated_…` option IDs derived from a model match those derived from the
  wire mapping.
* `adcp.__all__` and `adcp.types.__all__` name each export once (#1380).
