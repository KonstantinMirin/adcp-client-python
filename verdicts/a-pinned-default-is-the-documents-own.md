# A required property the document PINS to one value may default to it

**82 of 559 `Field required` failures are at such a property, and 28 of them are in the
payload-correction set where they do not belong.**

## The line, and it is the whole of the decision

A default on a generated field has been treated as one thing — an **invented default** —
and `adcp-client-python-0z0u` measured 867 such pairs over 624 classes, with
`status: Literal['completed'] = 'completed'` as the example. That reading is right wherever
the document admits several values at the property: a default then picks one of them, the
SDK rather than the document decides which, and a payload omitting the key is accepted as
if it had said something it never said.

It is wrong wherever the document admits **exactly one**. A `const`, or a single-member
`enum`, states the value. A default equal to it decides nothing:

```
core/assets/image-asset.json
  required: ['asset_type', 'url', 'width', 'height']
  properties.asset_type: {"type": "string", "const": "image",
                          "description": "Discriminator identifying this as an image asset."}
```

There is no second value `asset_type` could carry. `ImageAsset(url=…, width=300, height=250)`
cannot mean anything but `asset_type="image"`, and requiring a caller to write it is asking
them to repeat the document back to it.

**So the test is: does the node admit one value, or several?** `const` and a one-member
`enum` admit one. `TaskStatus` admits seven. That is the difference between a default that
is the DOCUMENT'S and a default that is the SDK'S, and it is a property of the node — read,
not judged.

## The measurement

Over the pinned bundle, counting property positions:

| | positions |
|---|---|
| properties the document pins to one value (`const`, or a 1-member `enum`) | 36,535 |
| of those, **`required` at their own node** | 22,252 |

By name, the required-and-pinned positions are the discriminators: `kind` 3,176,
`asset_type` 2,343, `type` 1,468, `scope` 1,142, `operation` 1,113, `dialect` 1,086,
`format_kind` 958, `unavailable_behavior` 663, `mode` 602, `mapping_status` 543,
`status` 541, `value_type` 523.

Over upstream's behavioural suite, taking every `Field required` failure and asking the
answering class's own document whether it pins that property at that node:

| | failures |
|---|---|
| `Field required` in total | 559 |
| **the document PINS the property at the class's node** | **82** |
| the document admits several values there | 475 |
| no class, or the node did not resolve | 2 |

The 82, by `(class, property, the one value)`:

```
28  SyncReportingReceiptsResponse.status        = 'completed'
13  ContextMatchResponseRouterPublisher.type    = 'context_match_response'
13  ContextMatchResponseProviderRouter.type     = 'context_match_response'
12  BuildCreativeEstimate.mode                  = 'estimate'
 7  ImageAsset.asset_type                       = 'image'
 3  ReportingDeliveryCapabilities.status_task    = 'get_reporting_status'
 3  ReportingDeliveryCapabilities.configuration_task = 'sync_accounts'
 1  PublisherDesignatedPreviewProvider.authority = 'publisher_designated'
 1  IndividualImageAsset.asset_type             = 'image'
 1  IdentityMatchResponseRouterPublisher.type   = 'identity_match_response'
```

And the 475 that stay as they are, which is the control: `Format.name` 118 and
`Format.format_id` 118 (the `drawcost` rename), `GetProductsResponse.status` 50 and
`GetAdCPCapabilitiesResponse.status` 38 — `status` typed `TaskStatus`, seven members, where
`'completed'` is one choice among them and the invented-default reading holds exactly.

**`SyncReportingReceiptsResponse.status` is pinned and `GetProductsResponse.status` is not,
in the same bundle.** That pair is why the rule has to be read off the node rather than off
the property's name: the first document's arm states `const: 'completed'`, the second's
states the enum.

## It is the route split again, not a second principle

`adcp.types._base.OmittedNotNull` already draws this line once, for an OPTIONAL property
whose document does not admit `null`: the JSON route refuses the null, the Python route
reads `None` as absence, `ADCP_STRICT_VALIDATION` refuses both, and `strict_validate` — the
document's screen — refuses either way. The same shape answers here:

* **JSON route** (`model_validate_json`): a document omitting a required property is
  refused, with the document's own `required` keyword. Unchanged.
* **Python route** (`Model(…)` and `model_validate` on a dict): the pinned value is
  supplied, because it is the only value the document admits and the caller cannot have
  meant another.
* **`strict_validate`**: the document's screen, unchanged — it refuses the omission.
* **`model_json_schema()`**: publishes `required` as the document states it.

So the accepted set over DOCUMENTS does not move, which is what reading 1 claims and what
`./check` and `tests/conformance/test_schema_model_parity.py` measure. One principle, two
applications, and the second needs no new vocabulary.

## What must NOT be done with this

* **Not a default where the node admits several values.** That is `0z0u` and it stays
  refused. The predicate is `const`, or an `enum` of length exactly 1 — nothing else, and
  in particular not "an enum with an obvious member".
* **Not a hand-written list of the 82.** The predicate is over the node; a list goes stale
  on the next bump and the first stale row is a class accepting a value its document
  dropped.
* **Not read off the property's NAME.** `status` is pinned at 541 positions and unpinned at
  many more.
* **Not a `Literal` narrowing that changes the annotation.** The annotation already states
  the pin; what changes is only whether the Python side supplies it.

## Where it goes

In the emitter, at the one place a `required` property's field is rendered —
`codegen/render.py` with `codegen/ir.py`'s reading of the node — and the Python-side half
beside `OmittedNotNull` in `src/adcp/types/_base.py`, since that marker already owns "the
two routes differ and here is why". One marker, two states: a pinned-and-required property
and an optional non-nullable one are the two cases where the Python spelling of a value is
not the JSON one.

**The gate** is a census, not an example: every required-and-pinned position in the bundle,
asserting the class supplies the value on the Python route and refuses the omission on the
JSON route, and that no UNPINNED required property gained a default — the second half being
what keeps `0z0u` closed.

## Also: this removes 28 payloads from the correction set

`SyncReportingReceiptsResponse.status` is pinned to `'completed'`. Correcting those 28
payloads by writing `"status": "completed"` into them would be writing the document back
into its own instances — correct, and noise. They are not payload defects.
