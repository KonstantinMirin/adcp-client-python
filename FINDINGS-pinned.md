# A required property the document PINS to one value now defaults to it

**The decision is `verdicts/a-pinned-default-is-the-documents-own.md` and it was taken before
this run.** It is implemented and the emission is re-taken whole. Three numbers held, one moved
the wrong way, and **six tests pin the opposite reading — they are reported here and NOT
edited**, which is the brief's own instruction.

    make gate   7 failed / 2563 passed of 2570   — trunk's figures, and the SET is identical, 0 pairs moved
    ./check     emitted 1059 / refused 0; approximated 805 facts in 239 documents — unchanged
    make test   134 failed / 16063 passed (+4 errors)   — trunk is 126 / 16071 (+4 errors): +8, not the predicted -16
    the 82      all ten (class, property) rows carry the document's default

**§8 is the part to read first**: `tests/test_literal_discriminator_defaults.py` exists to assert
that this SDK does *not* do what the verdict decided, and cites two documents for it. Nothing
in `tests/` was touched.

---

## 1. What was written

| file | what it carries |
|---|---|
| `src/adcp/types/_base.py` | `PinnedDefault`, the marker (`_ThePinIsSupplied`), `pins_default`, `the_pins`, and `AdCPBaseModel._supply_the_pins_the_document_states` — the Python-route half |
| `codegen/render.py` | the marker's `(module, name)` pair, the `pins` flag on `_OptionalMember`, and the one decision in `_field` |
| `codegen/harness.py` | `the_marker_declares` now reads a second marker, for the DROPPED-REQUIRED-KEY witness |
| `src/adcp/types/**` | whole re-emission over the 1,054 portable documents (`--tree src/adcp/types/_schemas --package src/adcp/types`); 215 files, no hand edit |

**`codegen/harness.py` is the "one other `codegen/` module the reading implicates", and it is not
a matter of taste — without it the gate loses pairs.** `check_refuses` offers, per required key,
the accepted instance with that key DROPPED, and asks the CONSTRUCTOR (`model_validate`, the
Python route) to refuse it; an admission with no declaration is `widened_undeclared`. A pinned
required property is now supplied on exactly that route, so the constructor admits exactly that
witness at every such field. `the_marker_declares` already draws this line once for
`OmittedNotNull`, and says why a per-site `Approximation` would be the wrong answer (§8: a fact
is declared once — it would write one identical record over the bundle's 22,252
required-and-pinned positions). The marker at the admitting field is the declaration; the new
clause is the same reading one witness shape over. The sentence it replaces (*"a widening about
`required` and not about this property's type, so the marker says nothing about it"*) is still
true of `OmittedNotNull` and is kept as that marker's reason.

`codegen/ir.py` was NOT touched: the walk already records the cardinality this reads
(`TypeRef.literals`, `TypeRef.members`), so there was nothing to add and no second reading of
"how many values does this node admit".

## 2. The predicate, and the one inch it covers

Asked of the DECIDED TYPE in `codegen/render.py:_field`, as a cardinality and not a pattern:

```python
pins=decided.required and len(decided.type.literals) + len(decided.type.members) == 1,
```

Measured over the re-emitted tree — **696 fields carry `PinnedDefault`**:

| the node | fields |
|---|---|
| `literals` of length 1 — D2's `const` row, and a one-member `enum` through `lower.enum.literal` | 596 |
| `members` of length 1 — §5's `enum` row at CONJ, a conjunct narrowing the vocabulary to one member | 100 |

**The `members` half is named here because it is the inch the brief warned about, and it is
inside the line rather than past it.** The verdict's test is *"does the node admit one value, or
several?"*, and a conjunct narrowing `Kind` to `Literal[Kind.NAME]` leaves a node admitting one
value by the same arithmetic a `const` does — `codegen.intersect.as_enum`'s equivalence ("a
`const` is a one-member vocabulary") is the existing reading and is what both halves are counted
through. What stays forbidden is the other side of the same `==`: a node admitting two or more
values gets nothing. That is `adcp-client-python-0z0u`'s 867 pairs and
`survey/invented_defaults.py`'s subject, and neither moved — measured in §7.

## 3. Why the FIELD is still required, and where the pin is supplied instead

**The field is emitted exactly as before plus one marker: required, no assignment, annotation
unchanged.** `model_fields[name].is_required()` is still `True` and nothing carries a pydantic
`default`.

That is not a style choice; it is the only shape that satisfies all four routes AND leaves
`tests_emit/test_the_invented_default_set.py` where it was. That file's ruling — *"no class of
ours defaults a field the conjunction requires"* — is read off `model_fields`, so an assigned
`= 'image'` would have reddened it at 696 sites, and would also have taken the property out of
`required` in `model_json_schema()` and made the JSON route accept the omission.

**So the supply cannot ride the field at all, and that is measured rather than argued.** A
missing key is visible to the MODEL and not to the field: pydantic-core asks a field's own
validator for a default and only `with-default` answers one. Probed on pydantic 2.13.5 /
pydantic-core 2.46.5,

    json_or_python(json=<literal>, python=with_default(<literal>, 'image'))

supplies the value on **neither** route — both report `Field required` — because `json_or_python`
does not delegate `default_value`. The supply is therefore one `model_validator(mode="before")`
on `AdCPBaseModel`, keyed on `info.mode`, and the marker in the annotation is the per-field
declaration it reads. One validator over one cached mapping, which is
`RuleBound._enforce_adcp_rules`' own arrangement: a class with no pinned required property reads
`the_pins`' empty answer and returns on its first line.

**The fill marks the field as SET**, which is what a `ConditionalRequired` over a pinned property
asks (`adcp.types._runtime.supplied` reads `__pydantic_fields_set__`).

**It writes no constant string key into a dict display**, and that is deliberate:
`survey/invented_defaults.restored_injections` reads `src/adcp/types/*.py` by AST for exactly
this shape — a before-validator that injects a required field — and `_base.py` is in its glob.
The fill is `{**payload, **absent}` over a comprehension, so that reading still finds nothing and
its gate stays a measurement rather than a tuned fence.

**The one cost of this position, measured: the before-validator's mere presence changes the
JSON route's error ORDER for every emitted class.** With a `mode="before"` model validator,
pydantic-core materialises a JSON object into a Python mapping before the model-fields validator
runs, and the two paths collect errors in different orders — `extra_forbidden` first for a JSON
object, `missing` first for a mapping. Measured on `ControlMediaBuyRequest` with one unexpected
key inside `packages.0.targeting_overlay.keyword_targets.0`:

| | first error on `model_validate_json` |
|---|---|
| trunk | `('extra_forbidden', '….unexpected')` |
| now | `('missing', '….keyword')` — the python route's order, on both routes |

Nothing is admitted or refused differently; `KeywordTarget` has no pinned field at all. What
moved is which error is reported first, and three tests grade it (§8, group D).
**`OmittedNotNull` is NOT affected** — probed directly: with the marker and the validator in
place, `model_validate_json('{…,"note":null}')` still refuses the explicit null with
`string_type`, so `json_or_python` keys on the validation state's input type and not on the
object it was handed.

## 4. The four routes, measured on a live class

`ImageAsset`'s shape, on `AdCPBaseModel` with the real marker:

| route | before | after |
|---|---|---|
| `Model(url=…, width=…)` | `Field required` | `asset_type='image'`, and in `model_fields_set` |
| `model_validate({…})` (mapping) | `Field required` | `asset_type='image'` |
| `model_validate_json('{…}')` | `Field required` | `Field required` — unchanged |
| `strict_validate({…})` | refused | refused — the document's screen, unchanged |
| `model_json_schema()` | `required: [asset_type, url, width]`, `{"const": "image"}`, no `default` | identical |
| `Model(asset_type='video', …)` | refused | refused |
| `ADCP_STRICT_VALIDATION=1`, both Python entries | refused | refused — the switch strikes this side too |

## 5. The 82 sites the verdict names

All ten `(class, property)` rows carry the marker after the re-emission, so all 82 of the
`Field required` failures the verdict counted are answered AT THE EMISSION:

| failures | the verdict's class | the emitted field |
|---|---|---|
| 28 | `SyncReportingReceiptsResponse.status` | `media_buy/sync_reporting_receipts_response.py:104` |
| 13 | `ContextMatchResponseRouterPublisher.type` | `trusted_match/context_match_response.py:59` |
| 13 | `ContextMatchResponseProviderRouter.type` | `trusted_match/provider_context_match_response.py:43` |
| 12 | `BuildCreativeEstimate.mode` | `media_buy/build_creative_response.py:366` |
| 7 | `ImageAsset.asset_type` | `core/assets/image_asset.py:26` |
| 3 | `ReportingDeliveryCapabilities.status_task` | `core/reporting_delivery_capabilities.py:60` |
| 3 | `ReportingDeliveryCapabilities.configuration_task` | `core/reporting_delivery_capabilities.py:59` |
| 1 | `PublisherDesignatedPreviewProvider.authority` | `core/preview_provider.py:33` |
| 1 | `IndividualImageAsset.asset_type` | `core/format.py:137` |
| 1 | `IdentityMatchResponseRouterPublisher.type` | `trusted_match/identity_match_response.py:36` |

Answering the failure is not the same as the test turning green: four of the nine R1 tests fail
on a LATER assertion now (§8, group A).

## 6. `make test`: 134, not 110, and the difference is the whole of §8

    trunk   126 failed / 16071 passed  (+4 errors)
    now     134 failed / 16063 passed  (+4 errors)

    -5   fixed      tests/test_preview_html.py — R1's five
    +13  new        all caused by this change; four groups, in §8
    ---
    +8   net

The prediction was 110 = 126 − 16 (R1's 9 and R2's 7). Neither row closed as predicted:

* **R1 closed 5 of 9.** The five `test_preview_html.py` failures are green —
  `ImageAsset(url=…, width=…, height=…)` now constructs. The four
  `tests/conformance/reporting/test_reporting_status_capabilities.py` failures are not: they
  reach a later assertion and fail there (§8, group A).
* **R2 did not close, and the brief asked for that to be confirmed rather than assumed. It is
  confirmed, and R2 is left alone.** The reason is exact: `allOf[1].then` requires
  `reporting_profile.canonicalization_contract_version` and `.canonicalization_media_type`, and
  the two properties are **`const`-pinned but OPTIONAL at their own node** —
  `core/reporting-delivery-offering.json`'s root `required` does not name them, only the
  conditional does. The emitted fields are therefore
  `Annotated[Literal['1.0'] | None, OmittedNotNull] = None`
  (`core/reporting_delivery_offering.py:63-64`), the predicate's `decided.required` is false,
  no marker is written and nothing is supplied. `src/adcp/reporting/production/offerings.py:70`
  still raises `ValueError: offering must satisfy the complete public contract`, because the
  screen there is `jsonschema` over the DUMP and the dump still omits both keys.

  A pinned property that a CONDITIONAL requires is a decision this verdict does not take. It is
  the obvious next question and it is not answered here.

## 7. The three numbers that did not move

**`make gate`: 7 failed / 2563 passed of 2570, and the SET is identical.** `before.json` against
`after.json` by node id: 0 pairs moved in either direction, the same seven failures, none added,
none dropped. A count that does not move is not evidence the set did not move, so the comparison
is per pair.

**`./check`: `emitted 1059 / refused 0`, `approximated 805 facts in 239 documents`.** Unchanged.
The brief allowed it to FALL and it did not, because R2 did not close (§6): no `Approximation`
record was added, removed or edited by this change.

**`0z0u`'s ruling is where it was.** `tests_emit/test_the_invented_default_set.py` reports the
same 2 failed / 3 passed with the change as without it — both failures are present on trunk,
byte for byte, and neither is about this decision
(`CreativeRepresentationFormatId.format_kind`, and
`adcp.types.CreateMediaBuySuccessResponse resolves`). The gate's live control also holds under
the change, measured directly: `CreateMediaBuySuccess.model_validate({…no status…})` is still
refused with `missing`, because that arm's `status` is `TaskStatus` — seven values, no pin, no
marker.

`mypy src/adcp/types/_base.py` reports the same 20 findings as trunk; `ruff` reports the same 5.

## 8. SIX TESTS PIN THE OPPOSITE READING, AND SEVEN MORE GRADE WHAT IT CHANGED

None of the thirteen was edited. All thirteen were confirmed to be caused by this change: the
four files together report **1 failure on trunk and 14 with the change**, in one 12-second run.

### Group A — `tests/test_literal_discriminator_defaults.py` (3): the decision, refused in a file written for it

The file's own docstring is the counter-argument, and it names two documents:

> Upstream's generator turned every `const` into a pydantic default, so `TextContent(content='x')`
> constructed there without the tag. **We do not add those defaults back.** Two documents say why:
> * `docs/reading-a-document.md` §3 — **a discriminator's tag is extracted BEFORE defaults
>   apply**, so a default cannot rescue an absent discriminator under a field-name discriminator
>   at all; the measurement there is 277 discriminator positions, all 277 required.
> * `docs/migration-from-upstream.md` "Worked example 2" — a class that supplies a required
>   `const` for you admits a payload the document refuses, and the branch classes exist precisely
>   so that they do not.

The three failures:

| test | asserted | now |
|---|---|---|
| `TestAssetContentDiscriminatorsAreRequired::test_text_content_requires_and_pins_asset_type` | `TextContent(content="hello")` raises | constructs, `asset_type='text'` |
| `TestWireFormat::test_text_content_from_wire_dict_without_asset_type_is_refused` | `TextContent.model_validate({"content": "hi"})` raises `missing` at `asset_type` | constructs |
| `TestVastDaastDiscriminators::test_vast_branch_omitting_a_discriminator_is_refused` | `VASTAssetUrl(url=…)` raises with `missing == {asset_type, delivery_type}` | constructs both pins |

**One half of its reasoning survives and one does not.** The discriminator-extraction half is
intact: a TAGGED union still refuses a payload with no tag, because the tag is read before any
branch validator runs — and measured, the VAST union refuses on both routes
(`VASTAsset.model_validate({"url": …})` → `required` at `asset_type`, from the root's own
`required`). What the verdict overrides is the second half, the one about the BRANCH CLASS
constructed directly: that is the position where "a class that supplies a required `const` for
you admits a payload the document refuses" and "the caller cannot have meant another" are the
same sentence read two ways. The two readings disagree about one thing only — whether the PYTHON
route may spell what the document pins — and both agree the JSON route, `strict_validate` and
the published schema may not.

### Group B — `tests/test_adcp_31_rc4_surface.py` (3): the same reading, at `typ` and `task`

| test | asserted |
|---|---|
| `test_generic_response_payload_jws_requires_typ` | `ResponsePayloadJwsEnvelope.model_validate({…no typ…})` raises |
| `test_verify_brand_claim_signed_payload_requires_base_metadata` | …and `{…no task…}` raises |
| `test_verify_brand_claims_signed_payload_requires_base_metadata` | the same, plural |

`typ: Annotated[Literal['adcp-response-payload+jws'], …, PinnedDefault]`
(`core/response_payload_jws_envelope.py:34`) is a `const` whose description is *"Type
discriminator preventing cross-profile replay"*, and
`task: Annotated[Literal['verify_brand_claim'], …]` (`brand/verify_brand_claim_response.py:77`)
is another. Both are now supplied on the Python route, so `model_validate` of a mapping that
omits them succeeds. **This is the one group where the decision's consequence has a security
sentence attached to it in the document's own words** — the pin exists to prevent cross-profile
replay, and a consumer who validates a Python dict no longer learns that the sender omitted it.
The JSON route still refuses, which is where a received document arrives.

### Group C — `tests/test_media_buy_actions.py` (4): still refused, different error

`test_generated_constraint_models_require_a_portable_bound[*]` asserts that
`model.model_validate({})` reports exactly `[('missing', ('kind',))]`. `kind` is a `const` on each
arm of `media-buy/change-term-constraints.json`, so the payload is now refused by the arm's OTHER
statement instead — the `anyOf` over the portable-bound groups — and the error list reads
`[('anyOf', ())]`. The refusal is intact; its identity moved, and the test's own docstring says
why it reads the error type rather than a message: *"the `anyOf` rule is an after-validator and
cannot run on a payload the field layer already refused"*. It can now.

### Group D — `tests/test_targeting_overlay_errors.py` (3): the JSON route's error order

`test_error_order_controls_primary_field_and_message[json-control|json-update|json-update-new]`
asserts the primary field is the extra key, because *"the JSON route reports the extra key before
the missing ones — that is pydantic-core's own ordering"*. It no longer is: §3's last paragraph
is the mechanism, the two routes now agree, and the primary field is the missing one. No
refusal moved. The class at the failing position carries no pinned field at all, so this is the
VALIDATOR'S PRESENCE and not the decision — it is the price of putting the supply on the model,
and §3 says why it cannot go on the field.

### And the four R1 tests that moved to a later assertion

`tests/conformance/reporting/test_reporting_status_capabilities.py` —
`test_raw_generated_capability_dumps_omit_unset_task_notification_and_false_flags[core|managed|reconciled]`
and `test_adopter_subclasses_and_nested_wire_models_keep_the_explicit_field_allowlist`. They now
get past construction (R1's fix) and fail on

```python
assert not any(k.endswith(("_task", "_notification")) for k in wire["reporting"])
```

because the dump of `ReportingDeliveryCapabilities` now carries `configuration_task` and
`status_task` — the two the document REQUIRES and pins. The allowlist is spelled by suffix, so
it forbids the two required keys along with the optional ones, and a dump omitting them is
invalid against `core/reporting-delivery-capabilities.json`. That is a third shape of the same
question and it is the owner's to rule on, not a defect to repair here.

## 9. What this does NOT close

* **A consumer's TYPE CHECKER still requires the argument.** PEP 681 reads a field specifier off
  the ASSIGNED value alone, and the field is deliberately not assigned (§3), so mypy and pyright
  report `ImageAsset(url=…, width=…, height=…)` as a missing argument for `asset_type` even
  though it now runs and returns `asset_type='image'`. The alternative is an assignment, and an
  assignment moves `required` in the published schema, admits the omission on the JSON route and
  reddens `0z0u`'s declarative gate at 696 sites — the three things the verdict holds fixed. No
  fixture in `tests/type_checks/` makes such a call, so nothing reddens today.
* **A pinned property a CONDITIONAL requires gets nothing** — §6, and it is why R2 is still open.
* **The JSON route's error ORDER moved for every emitted class** — §3 and §8 group D.
