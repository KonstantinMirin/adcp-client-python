# The stale tests removed, `Protocol` bound flat, the union check pointed at what is minted

Three jobs off `0f3c2381b` (*a required property the document pins to one value defaults to
it*). The owner's instruction for the first is the whole of its specification:

> "How about removing the stale tests, with no new code or docstrings. At most, it deserves
> a list of tests and reasons to remove them, with files deleted because you have git
> history for the actual history."

So nothing below was repointed, no assertion was rewritten and no docstring was added. This
file is the list.

---

## 1. THE DELETIONS — 9 removed, 4 LEFT IN PLACE

**Nine of the thirteen are deleted. Four are not, and the reason is the rule the brief gave
for exactly this case: "better one surviving stale test than a silent hole."** The four are
one parametrized function whose SECOND assertion block carries a live obligation nothing
else in the tree grades — measured, not assumed. Section 1.4 is that measurement.

| # | test | verdict |
|---|---|---|
| 1 | `test_adcp_31_rc4_surface.py::test_generic_response_payload_jws_requires_typ` | DELETED |
| 2 | `test_adcp_31_rc4_surface.py::test_verify_brand_claim_signed_payload_requires_base_metadata` | DELETED |
| 3 | `test_adcp_31_rc4_surface.py::test_verify_brand_claims_signed_payload_requires_base_metadata` | DELETED |
| 4 | `test_literal_discriminator_defaults.py::TestAssetContentDiscriminatorsAreRequired::test_text_content_requires_and_pins_asset_type` | DELETED |
| 5 | `test_literal_discriminator_defaults.py::TestVastDaastDiscriminators::test_vast_branch_omitting_a_discriminator_is_refused` | DELETED |
| 6 | `test_literal_discriminator_defaults.py::TestWireFormat::test_text_content_from_wire_dict_without_asset_type_is_refused` | DELETED |
| 7–9 | `test_targeting_overlay_errors.py::test_error_order_controls_primary_field_and_message` (one function, the 3 failing params of 10) | DELETED |
| 10–13 | `test_media_buy_actions.py::test_generated_constraint_models_require_a_portable_bound` (4 params) | **LEFT IN PLACE** |

**Per file, which of the two things was done** (the brief's question): every one of the four
files still holds live tests, so in each case only the named tests went and **no file was
deleted**. Counts after, from a run of each file:

| file | tests after | state |
|---|---|---|
| `tests/test_adcp_31_rc4_surface.py` | 4 (was 7) | 3 deleted; file kept |
| `tests/test_literal_discriminator_defaults.py` | 13 (was 16) | 3 deleted; file kept |
| `tests/test_targeting_overlay_errors.py` | 137 params (was 147) | 1 function deleted; file kept |
| `tests/test_media_buy_actions.py` | 54 | nothing deleted |

One dead symbol went with the deletions and is not an edit of anything that stayed:
`_SIGNED_PAYLOAD_BASE` in `test_adcp_31_rc4_surface.py` had its only five readers in tests
2 and 3. `tests/test_targeting_overlay_errors.py` needed no such removal — its
`_validation_error_to_invalid_request`, `narrow_union_errors` and `_SECRET` all keep other
readers.

### 1.1 The three in `test_adcp_31_rc4_surface.py`

**AND THE BRIEF'S REASON IS RIGHT FOR ONE OF THE THREE AND NOT FOR THE OTHER TWO, which is
worth having in the record because the two reasons are different decisions.** The brief
says all three "assert `typ` requiredness through the MODEL". Measured by running the file,
the failing line in tests 2 and 3 is not the `typ` block at all:

```
test_generic_response_payload_jws_requires_typ                    line 75  -> the `typ` block
test_verify_brand_claim_signed_payload_requires_base_metadata     line 110 -> the `task` block
test_verify_brand_claims_signed_payload_requires_base_metadata    line 174 -> the `task` block
```

The `typ` block in tests 2 and 3 still passes, and **it passes for a reason that is not
about `typ`**: `pytest.raises(match="typ")` is a `re.search` over the whole error string, and
a payload missing `brand_domain` renders `Field required [type=missing, ...]` — `type=`
contains `typ`. So those two assertions were matching the word `type` in pydantic's own
error metadata, and had been for as long as any field of the payload was missing.

**The documents, read at the two pointers.**

| what the test asserted | the document's own node | after `0f3c2381b` |
|---|---|---|
| test 1: `typ` required | `core/response-payload-jws-envelope.json#/definitions/response_payload/properties/typ` — `const: "adcp-response-payload+jws"` | pinned to one value → supplied |
| tests 2, 3: `task` required | `brand/verify-brand-claim{,s}-response.json#/definitions/signed_response/allOf/1/properties/payload/properties/task` — `const: "verify_brand_claim"` | pinned to one value → supplied |

`task` is NOT pinned on the generic envelope — there it is a two-member `enum`
(`verify_brand_claim`, `verify_brand_claims`) and is still refused when absent (measured,
§1.1.1 below). It is pinned only in each per-task response document, which is why tests 2
and 3 broke and test 1 broke one property over.

So tests 2 and 3 are the SAME decision as the three in §1.2 —
`verdicts/a-pinned-default-is-the-documents-own.md` — and only test 1 is the brief's
signing-surface argument.

**And that argument holds, verified rather than taken.** `src/adcp/signing/jws.py:160-163`
decodes the protected header itself and does

```python
typ = header.get("typ")
if typ != expected_typ:
    raise JwsMalformedError(f"JWS typ {typ!r} does not match expected {expected_typ!r}")
```

— byte equality, no normalisation, before `kid` resolution and before the detached
signature is verified. `ResponsePayloadJwsEnvelope` appears nowhere in that path: its only
mentions in `src/` are `adcp/__init__.py`'s exports and the `compat.py` / `_adapter.py` /
`legacy_names.py` aliases. The model's verdict cannot affect signature verification.

#### 1.1.1 Covered elsewhere — yes, in three places, and one of them is the real guard

**(a) The byte-equality guard that actually enforces `typ` is graded.**
`tests/conformance/signing/test_jws.py::test_reject_wrong_typ` signs a header with
`typ: "some-other+jws"` and asserts `JwsMalformedError, match="typ .* does not match
expected"`. Run: **passes**. An ABSENT `typ` takes the identical branch (`None != expected`)
and has no test of its own — noted, not fixed, because writing one is new code.

**(b) `make gate`'s `refuses` check puts the dropped-key witness to every one of these
properties, and the seven that are not pinned are REFUSED.** Measured at
`core/response-payload-jws-envelope.json#/definitions/response_payload` by deriving
`harness.refused_witnesses` on the node and offering each to the class:

```
[required] drops the required key 'typ'          -> ADMITTED | the marker declares it: True
[required] drops the required key 'task'         -> REFUSED
[required] drops the required key 'brand_domain' -> REFUSED
[required] drops the required key 'agent_url'    -> REFUSED
[required] drops the required key 'request_hash' -> REFUSED
[required] drops the required key 'iat'          -> REFUSED
[required] drops the required key 'exp'          -> REFUSED
[required] drops the required key 'response'     -> REFUSED
```

The one admission is DECLARED, which is why the pair is green and not excused:
`harness.the_marker_declares` answers `True` because the field carries
`adcp.types._base.PinnedDefault` (`_ThePinIsSupplied`), and §8's rule is that a fact is
declared once, at the field, rather than once per position over the bundle's
required-and-pinned sites. Same reading at the brand-claim payload, where both `typ` and
`task` carry the marker.

**(c) The document's own answer still refuses, and that is asserted by the same gate's
`accepts`/`dump` halves.** `strict_validate` — the half `model_validate` does not route
through — is unmoved:

```
ResponsePayload.strict_validate({... no typ ...})  -> 'typ' is a required property
Payload.strict_validate({... no task ...})         -> 'task' is a required property
```

**(d) The positive half tests 2 and 3 also carried** — construct the signed response from a
complete payload and read `payload.brand_domain`, `payload.request_hash`, `payload.typ`
back — is the `accepts` and `dump` contract at the pairs the gate already owns. Run:
`brand/verify-brand-claim-response.json#/definitions/signed_response SignedResponse`,
`…/properties/payload Payload`, `core/response-payload-jws-envelope.json#
ResponsePayloadJWSEnvelope` and `…#/definitions/response_payload ResponsePayload` — **4
passed**.

### 1.2 The three in `test_literal_discriminator_defaults.py`

The decision the owner reversed, `verdicts/a-pinned-default-is-the-documents-own.md`. Each
asserted that a required `const`-pinned discriminator is refused when absent:

* test 4 — `TextContent(content="hello")` raises. It also had a positive half
  (`TextContent(asset_type="text", content="hello")`, then `asset_type` and `content` read
  back), which the four surviving tests of its own class and
  `TestWireFormat::test_text_content_from_wire_dict` assert in the same shape.
* test 5 — `VASTAssetUrl(url=…)` raises with `missing == {"asset_type", "delivery_type"}`.
* test 6 — `TextContent.model_validate({"content": "hi"})` raises
  `[("missing", ("asset_type",))]`.

Measured after the change, all three are now admissions and all three are declared:

```
VASTAssetUrl(url=...)                        -> BUILT    asset_type='vast' delivery_type='url'
TextContent.model_validate({'content':'hi'}) -> BUILT    asset_type='text'
```

#### 1.2.1 Covered elsewhere — yes, by `make gate`'s `refuses` over every required key

The hand-written cases are three positions; the gate asks the same question at every
required key of every one of the 2,570 pairs. Measured:

| pair | witness | outcome |
|---|---|---|
| `core/assets/text-asset.json# TextAsset` | drops `asset_type` | ADMITTED, marker declares: **True** |
| | drops `content` | REFUSED |
| `core/assets/vast-asset.json# VASTAsset` | drops `asset_type` | ADMITTED, marker declares: **True** |
| `core/assets/vast-asset.json#/oneOf/0 VASTAssetUrl` | drops `delivery_type` | ADMITTED, marker declares: **True** |
| | drops `url` | REFUSED |

So every property the three tests named is reached by the gate, at its own pointer, with a
verdict; and `strict_validate` still answers with the document's own `required`
(`TextAsset.strict_validate({"content": "hi"})` → `'asset_type' is a required property`).
The non-pinned siblings — `content`, `url` — are still refusals, so the column is not
vacuous at these nodes.

#### 1.2.2 The union half — IT HOLDS, AND `make gate` DOES **NOT** COVER IT

The brief asked for this one to be verified rather than assumed. Both halves of the answer
are measured, and the second is not the expected one.

**It holds.** At the union whose DISPATCH tag is the pinned property:

```
AssetVariant.model_validate({'asset_type': 'text', 'content': 'hi'}) -> AssetVariantText
AssetVariant.model_validate({'content': 'hi'})                       -> REFUSED [('oneOf', ('asset_type',))]
AssetVariant.strict_validate({'content': 'hi'})                      -> 'asset_type' is a required property
```

**It is not graded by `make gate`'s `refuses` check.** The witness derivation reads the
NODE's own keywords, and `core/assets/asset-union.json#` states no `required` of its own —
the tag is required by each branch. Measured at that pair:

```
core/assets/asset-union.json # AssetVariant | node required: None
  witnesses aimed at: ['type']
```

Five `type` witnesses and nothing else. The pair is green (`accepts`, `refuses`, `dump` all
`pass`) without the absent-tag question ever being put.

**And the distinction the measurement forces is worth stating, because "a tagged union
refuses an absent tag" is true of one tag and false of another at the same document.** At
`VASTAsset` the absent `asset_type` is ADMITTED (§1.2.1) — that union dispatches on
`delivery_type`, and `asset_type` is pinned on both of its branches. At `AssetVariant` the
absent `asset_type` is REFUSED, because there it IS the dispatch tag. The sentence holds
for **the tag a union dispatches on**, not for every pinned tag a branch carries.

**NOTHING IS LOST BY THESE DELETIONS ON THAT ACCOUNT, and that is the reason none of the
three is kept for it: not one of them asserted the union.** Tests 4 and 6 are about
`TextContent`, which is no union; test 5 is about the BRANCH class `VASTAssetUrl`. The
file's union test, `TestVastDaastDiscriminators::test_the_union_parses_either_arm_from_the_
payload`, is not in the thirteen and stays.

**OPEN, AND IT PREDATES THIS CHANGE: nothing in the tree asserts that a union base refuses
a payload with no dispatch tag.** Searched `tests/` and `tests_emit/` for the shape and
found none — `tests_emit/test_union_dispatch.py` grades the opposite direction ("where the
document admits exactly ONE branch, the dispatch may not refuse"), and the gate is the
measurement above. Flagged here as a gap these deletions neither cause nor fill.

### 1.3 The three in `test_targeting_overlay_errors.py`

One function, `test_error_order_controls_primary_field_and_message`, 10 params of which 3
fail — the `json` route where no union encloses the overlay (`json-control`, `json-update`,
`json-update-new`). Measured failure:

```
assert error.field == 'packages.0.targeting_overlay.keyword_targets.0.unexpected'
                   got 'packages.0.targeting_overlay.keyword_targets.0.keyword'
```

The payload is `{"keyword_targets": [{"unexpected": <secret>}]}`, which breaks two things at
once — an extra key and two missing required ones. The test asserts WHICH of them is first,
through `_validation_error_to_invalid_request`'s choice of primary field, and one `missing`
error leaving the list is enough to change that. Same outcome, different first complaint.

**The whole function is deleted rather than its 3 params**, because 3 of 10 cannot go
without a condition in the body, and a condition is new code. So the 7 passing params go
with them, and §1.4's question has to be asked of those too.

#### 1.3.1 Covered elsewhere — yes, for every obligation except the ORDER itself

**(a) The error SET for this exact payload, on both routes, for all five tasks.**
`test_errors_match_input_schema_including_nested_unions_and_context` is parametrized with
an overlay id `missing-extra-order` whose value is
`{"keyword_targets": [{"unexpected": _SECRET}]}` — the deleted test's payload — over
`["python", "json"]` and all five `_PATHS`. It asserts the error count equals a standalone
`TypeAdapter(TargetingOverlayInput | None)`'s, and that every field of each standalone
error (`type`, `msg`, `input`, `url`, `ctx` as a subset) SURVIVES into the nested one,
matched by `loc` and `type` rather than by position. Its own comment already draws the
line: *"Order is `test_error_order_controls_primary_field_and_message`'s subject; survival
is this one's."* Run: **10 passed**.

**(b) The `INVALID_REQUEST` projection — code, field derivation, detail key-set, redaction.**
Two surviving tests in the same file, on other payloads:
`test_custom_targeting_error_becomes_invalid_request` (code, field, first error `type`,
message, and `"TargetingOverlay" not in json.dumps(error)`) and
`test_typed_caller_has_one_safe_document_error` through `_assert_error` (code, field,
message, `len(details) == 1`, `set(details[0]) == {"type", "loc", "msg"}`, `_SECRET` absent,
`TargetingOverlay` absent). Both pass.

**(c) What is NOT covered is the ORDER**, which is the stale half: no surviving test asks
which error comes first on the JSON route. That is the assertion the decision moved, and
the brief's instruction is to let it go rather than repoint it.

### 1.4 The four in `test_media_buy_actions.py` — LEFT IN PLACE

`test_generated_constraint_models_require_a_portable_bound`, 4 params
(`BudgetChangeConstraints`, `FlightChangeConstraints`, `PackageCountChangeConstraints`,
`EffectiveTimingChangeConstraints`).

**The brief's reason is right about the first of its two assertion blocks.** Measured:

```
model.model_validate({})
    asserted [('missing', ('kind',))]
    now reads [('anyOf', ())]
```

`kind` is `const`-pinned at each `media-buy/change-term-constraints.json#/oneOf/<i>`, so it
is supplied and validation proceeds to the real rule. **The payload is refused either way**
and `kind` was never the caller's omission to fix — exactly as the brief says.

**THE SECOND BLOCK IS A DIFFERENT OBLIGATION, IT STILL PASSES, AND NOTHING ELSE IN THE TREE
GRADES IT.**

```python
with pytest.raises(ValidationError) as missing_bound:
    model.model_validate({"kind": kind})
assert [(e["type"], e["loc"]) for e in errors] == [("anyOf", ())]
for bound in bounds:
    assert bound in errors[0]["msg"]
```

That is the document's `anyOf` over one-key `required` groups — the portable bounds — fired
on the generated class, with the bound NAMES in the message. Measured directly, it holds on
all four:

```
BudgetChangeConstraints.model_validate({'kind': 'budget'})                  -> REFUSED [('anyOf', ())]
FlightChangeConstraints.model_validate({'kind': 'flight'})                  -> REFUSED [('anyOf', ())]
PackageCountConstraints.model_validate({'kind': 'package_count'})           -> REFUSED [('anyOf', ())]
EffectiveTimingConstraints.model_validate({'kind': 'effective_timing'})     -> REFUSED [('anyOf', ())]
```

**And three places that might have covered it do not:**

1. **`make gate`'s `refuses` check never asks.** `harness.refused_witnesses` derives from
   the keywords `own_facts` reads, and `anyOf` is not among its derivations. Measured over
   all four pairs:

   ```
   #/oneOf/0 BudgetChangeConstraints     witnesses aimed at: ['properties', 'type']
   #/oneOf/1 FlightChangeConstraints     witnesses aimed at: ['properties', 'type']
   #/oneOf/2 PackageCountConstraints     witnesses aimed at: ['additionalProperties', 'properties', 'required', 'type']
   #/oneOf/3 EffectiveTimingConstraints  witnesses aimed at: ['properties', 'type']
   ```

   Not one witness drops a portable bound. All four pairs PASS the gate — which is the
   point: green there is not evidence about this rule.
2. **`tests_emit/test_emit.py` grades the RULE and not the wiring.** Its case table holds
   `(RequiredGroups((("a",), ("b",)), "anyOf"), set(), "anyOf")` — the mechanism on a
   synthetic two-group rule. It says nothing about whether these four classes carry the
   rule the document states, which is
   `RequiredGroups(groups=(('max_delta_amount',), ('max_delta_percent',),
   ('min_result_amount',), ('max_result_amount',)), combinator='anyOf')` on
   `BudgetChangeConstraints._adcp_rules`.
3. **Every other reader of these classes supplies a bound.** All 14 references in
   `tests/test_media_buy_actions.py` outside this test and all 6 in
   `tests/type_checks/media_buy_actions.py` construct with `max_delta_percent`,
   `max_delta_amount`, `max_additions` or `minimum_notice` present — positive construction,
   and the type-check file is not a runtime refusal at all. No population-wide check that
   every emitted `RequiredGroups` fires exists in `tests_emit/`.

So deleting this function would remove the only behavioural check that these four generated
classes enforce their document's portable-bound `anyOf`. It stays red on its first block
and is reported as such — **one surviving stale test rather than a silent hole**, which is
the brief's own instruction for this case.

### 1.5 One thing left untouched and flagged rather than fixed

`tests/test_literal_discriminator_defaults.py`'s module docstring still argues the reversed
decision in its own words — *"Upstream's generator turned every `const` into a pydantic
default... **We do not add those defaults back.**"* — and so do two of its class
docstrings. Rewriting them is a docstring, which this job is instructed not to write; the
scope admits deletions in `tests/` and nothing else. It is the owner's call whether that
prose goes in a follow-up or the file does.

---


## 2. `Protocol` BOUND FLAT, AND `__all__` NOW SAYS WHAT THE NAMESPACE BINDS

The owner's ruling on `Protocol`: *"It kinda belongs there, it is being used, and the fact
that the schema doesn't say it doesn't mean that we shouldn't use the enum in the SDK."*
**Blended in.** The principle is written into `adcp/types/__init__.py`'s docstring beside
it, because it is the line the `registry` ruling of the same day turns on from the other
side: `adcp.types` may hold a hand-written type the SDK needs; what it may not hold is
**another generator's output**.

**AND THE 21 WERE ONE SLICE. THE GAP IS 108 WORDS OVER TWO LAYERS**, which is the owner's
correction mid-job and is measured here rather than taken.

### 2.1 What was wrong, measured on the untouched HEAD tree

| layer | words | resolve at `adcp.types.<word>` | in `adcp.types.__all__` |
|---|---|---|---|
| `adcp.types.aliases` | 127 | **127** | 39 |
| `adcp.core`, via the `core` domain's `X as X` block | 21 | 20 | 1 |
| union of the two | 148 | 147 | 40 |

So **108 words were bound and advertised by nobody**. `from adcp.types import X` worked for
every one; `from adcp.types import *`, `dir()`, tab completion and a doc generator gave
none of them. `VerifyBrandClaimsPayload` is the measured case — `aliases.py:171`'s short
word for `adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload` — and
`tests/test_adcp_31_rc4_surface.py::test_rc4_symbols_are_publicly_exported` was RED on
exactly it. The gap was known, not undiscovered.

`adcp.core`'s own slice: 19 of the 21 resolved only because `survey/emit_legacy_names.py`
happens to emit a row for each. `Protocol` is the one that generator does not carry, so it
resolved at `adcp.core.Protocol` and `adcp.types.core.Protocol` and raised
`AttributeError` at `adcp.types.Protocol` — one surface answering two ways. `TaskStatus`
resolved through `_flat` to the DOCUMENT's nine-member `enums/task-status.json`
enumeration, which is deliberate.

### 2.2 CHECK 1 — does every added name RESOLVE? Yes, and `Protocol` was the only one

This is the reason the blanket union was refused before, so it was re-measured rather than
assumed: every word of both layers was offered to `getattr(adcp.types, …)` on the HEAD
tree **before** being advertised.

```
of the 148: resolve 147 | do NOT resolve 1  ->  ['Protocol']
```

**There is no second such name.** `Protocol` is bound by this same change, and
`aliases.__adcp_refused__` is `{}`, so that module declines nothing today. The screen is
kept in the code and not only in this file: `_advertised_layers()` offers each word to
`getattr` through `sys.modules[__name__]` — the chain that decides resolution — and drops
an `AttributeError`. So a word a layer starts declining leaves the advertisement with
nothing edited, and `__all__` cannot come to offer a name that raises.

### 2.3 After

| | before | after |
|---|---|---|
| `len(adcp.types.__all__)` | 4,251 | **4,359** (+108) |
| advertised words that do NOT resolve (over all of `__all__`) | — | **0** |
| `aliases.__all__` advertised | 39 / 127 | **127 / 127** |
| `adcp.core`'s 21 advertised | 1 | **21** |
| of the 21, resolving at all | 20 | **21** |
| of the 21, resolving to `adcp.core`'s own object | 19 | **20** |
| in `dir(adcp.types)` | 40 | **148** |

* `adcp.types.Protocol is adcp.core.Protocol` → **True**, members `['a2a', 'mcp']`.
* `adcp.types.VerifyBrandClaimsPayload is adcp.types.aliases.VerifyBrandClaimsPayload` → **True**.
* `from adcp.types import *` resolves every advertised word — **0 missing of 4,359**
  (`tests/test_lazy_types.py::test_star_import_from_adcp_types_resolves_all`).
* `set(adcp.types.__all__) <= set(dir(adcp.types))` holds (`::test_dir_includes_all`).

`TaskStatus` is the one word advertised without being `adcp.core`'s, and that is the
decision `adcp/types/core.py`'s docstring already records: the late consult is reached
LAST, so it can only ADD a spelling. The flat word stays the document's enumeration and
upstream's five-member one keeps `adcp.types.core.TaskStatus`. **`__all__` is a statement
that a spelling resolves, not a claim about which subject it names.**

**`legacy_names` IS A THIRD SLICE AND IS DELIBERATELY NOT INCLUDED.** Measured: 3,520
words, of which **1,726** are unadvertised — 16 times this change. It is
`survey/emit_legacy_names.py`'s generated output, whose rows `FINDINGS-sixwords.md`'s open
question 3 already records as decided by a rule the owner's ruling overrode. Advertising
1,726 generated spellings is a surface decision of its own size and was not asked for.
Named so it is not rediscovered.

### 2.4 CHECK 2 — what moved, name by name

**`tests/test_public_words_resolve.py`: 0 of its 3 failures close, and the reason is
measurable rather than a guess.** All three range over `adcp.__all__` — the top-level
package's own literal list, **745** words — and over the GENERATED refusal table in
`adcp/types/_adapter.py`. Neither is touched by this change. The two assertion figures are
identical before and after:

```
before: the refusal table and the public surface disagree about 45 of 745 advertised words.
after:  the refusal table and the public surface disagree about 45 of 745 advertised words.
before: 12 of 58 declared refusals cite a location this repository does not have.
after:  12 of 58 declared refusals cite a location this repository does not have.
```

Those three are the stale-census failures that file's own docstrings diagnose — *"`_adapter.py`
is GENERATED by `survey/adapter_surface.py`, so neither group is fixed by editing it"* —
and they need a re-derivation of the census, which is out of this job's scope and out of
its write scope. **What DID close is the test that actually asserts advertisement in
`adcp.types.__all__`**: `test_rc4_symbols_are_publicly_exported`, whose failure named
`VerifyBrandClaimsPayload`.

**One test's parametrization moved, and all of its new members pass.**
`tests/test_no_explicit_null.py::test_every_optional_field_either_carries_the_marker_or_admits_null`
draws `random.Random(1547).sample(_generated_models(), 60)`, and `_generated_models()`
reads `dir(public_types)` — so 108 more advertised words redraw the seeded sample. **54 of
the 60 members changed; all 54 new ones pass** and the collected count for that test is
unchanged. `tests/test_legacy_surface_names_every_branch.py` gained one param,
`LegacyProductFormatDeclaration` — the only would-add word starting with `Legacy`, which
enters that file's `LEGACY_NAMES` census — and it **passes**.

**Pre-existing and unmoved, each verified against HEAD rather than assumed:**

| failure | why this change does not move it |
|---|---|
| `test_public_api.py::test_public_api_surface_matches_snapshot` | already red on its FIRST assertion — the snapshot's namespace SET is stale (`adcp.types.domains.{manifest,manifest_schema,brand_discovery}` present, `…domains.common` absent) — so it never reaches the added-names check. Regenerating `tests/fixtures/public_api_snapshot.json` is a reviewed surface change and is out of scope |
| `test_lazy_types.py::test_partial_modules_are_in_types_all` | in the baseline list; asserts a MODULE name is advertised |
| `test_lazy_types.py::test_partial_module_names_all_resolve_via_adcp_types` | in the baseline list |
| `tests_emit/test_the_restored_flat_surface.py` ×2, `test_the_surface_exports_something.py[types.guards]` ×2 | run with the changes stashed: the same 4 fail at HEAD, byte-identical |

`mypy src/adcp/types/__init__.py` reports **22 errors on that file before and 22 after** —
zero delta, verified by stashing. `ruff check` and `ruff format --check` are clean on it.

---

## 3. THE UNION CHECK POINTED AT `WIDENED`

`tests_emit/test_union_dispatch.py`'s exemption for an inseparable union asked for an
`UNDERDETERMINED` approximation. **Verified rather than taken: nothing mints one.** Over
the FRESH tree this suite grades (`tests_emit/fresh.py`, not the committed one):

| | |
|---|---|
| emitted classes carrying approximations | 752 |
| approximation entries, by kind | `WIDENED` 344, `NARROWED` 476, **`UNDERDETERMINED` 0** |
| union bases declaring a branch list | 149 (131 `oneOf`, 18 `anyOf`) |
| their entries, by kind | `WIDENED` 55, `NARROWED` 86, **`UNDERDETERMINED` 0** |

Zero in the committed tree too (`grep` over `src/adcp/types/`: 714 `NARROWED`, 469
`WIDENED`, 0 `UNDERDETERMINED`). The 2026-11-16 correction pointed both minting sites of
`codegen/lower/union.py` at `ir.WIDENED` for `oneOf` and at nothing for `anyOf`, which is
§4's sentence; `codegen/ir.py` still declares the kind and `adcp.types._base.KINDS` still
holds it, so the word is live and unminted. **The escape could not fire, and the only
reason nothing reddened is that the 42 payloads landing elsewhere are all `anyOf` and leave
by `_owes_no_declaration`.**

### What was done

`_underdetermined` → `_declares_the_widening`, and the predicate is §4's whole sentence:
**a `WIDENED` approximation at the UNION's pointer where the combinator is `oneOf`**.

**The pointer clause is not decoration, and that is measured.** A union base carries every
declaration its node and conjuncts took, at `if`, `maxLength` and `properties` pointers
that say nothing about which branch a payload becomes. Of the 149 bases:

| predicate | bases it admits |
|---|---|
| `kind == "WIDENED"` anywhere on the class | 33 (27 `oneOf`, 6 `anyOf`) |
| `WIDENED` at `<the base's pointer>/<the combinator>`, keyword == the combinator | **10**, all `oneOf` |

So the kind alone would have handed the exemption to 23 more bases for a widening one
keyword away — the shape of the exemption `adcp-client-python-84a9` had REMOVED. The
pointer spelling is `codegen/lower/union.py`'s own (`<pointer>/<kw>`).

The escape is **kept, not deleted**: a genuinely inseparable `oneOf` needs a way to pass
other than being separable, which may be impossible for it. The three docstring references
and the failure message moved with the name — `wrong`'s reason now reads `"no WIDENED
declaration at the union's pointer"`, so a failure names what was actually asked. Four
stale `UNDERDETERMINED` quotations of §4 in the same file were corrected to the sentence
`docs/plan/rebuild-plan.md:1219` now carries.

`tests_emit/test_union_dispatch.py::test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from`
— **passes**.

---

## 4. THE RUNS

All taken in THIS worktree. `make test` and `make gate` write
`test-results/<suite>/report.json` as relative paths and nothing was redirected to `/tmp`.
Every intermediate question in this file was asked with a pytest node id or a derivation,
never with a full run.

**THE FIRST BASELINE WAS DISCARDED AND RE-TAKEN, which is worth recording.** It was started
before the edits and still running while they landed, so it graded a moving tree. The
baseline below was taken with the work `git stash`ed, at `0f3c2381b` exactly; the after-run
with it restored. Both in this checkout, 45 and 49 minutes.

### `make test`

| | before | after |
|---|---|---|
| failed | **81** | **71** |
| passed | 16,130 | 16,125 |
| skipped | 2,823 | 2,823 |
| deselected | 10 | 10 |
| xfailed | 1 | 1 |
| collected (json report) | 19,021 | 19,006 |

**Failure NAMES, diffed. 10 closed, 0 newly failing.**

```
CLOSED:
  tests/test_adcp_31_rc4_surface.py::test_generic_response_payload_jws_requires_typ          deleted
  tests/test_adcp_31_rc4_surface.py::test_verify_brand_claim_signed_payload_requires_base_metadata   deleted
  tests/test_adcp_31_rc4_surface.py::test_verify_brand_claims_signed_payload_requires_base_metadata  deleted
  tests/test_literal_discriminator_defaults.py::TestAssetContentDiscriminatorsAreRequired::test_text_content_requires_and_pins_asset_type  deleted
  tests/test_literal_discriminator_defaults.py::TestVastDaastDiscriminators::test_vast_branch_omitting_a_discriminator_is_refused          deleted
  tests/test_literal_discriminator_defaults.py::TestWireFormat::test_text_content_from_wire_dict_without_asset_type_is_refused             deleted
  tests/test_targeting_overlay_errors.py::test_error_order_controls_primary_field_and_message[json-control]     deleted
  tests/test_targeting_overlay_errors.py::test_error_order_controls_primary_field_and_message[json-update]      deleted
  tests/test_targeting_overlay_errors.py::test_error_order_controls_primary_field_and_message[json-update-new]  deleted
  tests/test_adcp_31_rc4_surface.py::test_rc4_symbols_are_publicly_exported                  FIXED by job 2

NEWLY FAILING:
  (none)
```

**The whole count reconciled, so nothing is absorbed:** 9 of the 13 named tests went (the
other 4 are §1.4's, still red); `test_rc4_symbols_are_publicly_exported` went from failed
to passed; and it is the ONLY surviving node id whose outcome changed at all. Node ids gone:
70 (9 failed + 61 passed) = the 16 deleted params plus the 54 redrawn sample members. Node
ids new: 55, **all passed** (54 redrawn, 1 `LegacyProductFormatDeclaration`). So
`81 − 9 − 1 = 71` and `16,130 − 61 + 55 + 1 = 16,125`.

The 4 left in place are in the after-failures list by design:

```
tests/test_media_buy_actions.py::test_generated_constraint_models_require_a_portable_bound[BudgetChangeConstraints-budget-bounds0]
tests/test_media_buy_actions.py::test_generated_constraint_models_require_a_portable_bound[FlightChangeConstraints-flight-bounds1]
tests/test_media_buy_actions.py::test_generated_constraint_models_require_a_portable_bound[PackageCountChangeConstraints-package_count-bounds2]
tests/test_media_buy_actions.py::test_generated_constraint_models_require_a_portable_bound[EffectiveTimingChangeConstraints-effective_timing-bounds3]
```

Artifacts: `test-results/{baseline-clean,after}.log`,
`test-results/{baseline,after}-failures.txt`,
`test-results/sdk/report.{baseline,after}.json`.

### `make gate`

**7 failed / 2,563 passed of 2,570**, 460.96 s — the expected figure, and job 3 does not
touch this suite (`make gate` runs `test_the_grade_is_green.py` only). The 7:

```
core/asset-group-vocabulary.json#                             AdCPAssetGroupVocabularyRegistry
core/creative-representation.json#/allOf/0                    CreativeRepresentationFormatId
core/format-shape-vocabulary.json#                            AdCPFormatShapeVocabularyRegistry
core/targeting-unknown-age-eligibility-constraint.json#       TargetingUnknownAgeEligibilityConstraint
core/targeting-verified-age-basis-constraint.json#            TargetingVerifiedAgeBasisConstraint
creative/asset-types/index.json#                              AdCPAssetTypeRegistry
extensions/index.json#                                        AdCPExtensionRegistry
```

### `./check`

```
emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059
kind: verdict 0, deferred 0, chained 0  ->  primary 0, chained 0
approximated 805 facts in 239 documents
```

All three expected figures.
