# 29 refusals say nothing: `anyOf () is not valid under any of the 3 branches`

**One row, `loc=()`, no keyword, no position, no sentence** — while each branch had a
precise and different reason, and the document had one too.

## The measurement

Over upstream's behavioural suite, failures whose only error row is the bare combinator
message:

| answering class | branches | failures |
|---|---|---|
| `CreateMediaBuyRequest` | 3 | 20 |
| `PostalArea` | 2 | 3 |
| `MCPWebhookPayload` | 46 | 1 |
| `GetReportingStatusResponse` | 3 | 1 |
| `ReportingAdjustment`, `AdCPAgentsAuthorization`, `TMPProviderRegistration`, `TargetingOverlay` | 2 each | 1 each |
| **total** | | **29** |

Their test files: `test_decisioning_webhook_emit.py` 15, `test_postal_area_compat.py` 4,
`test_decisioning_handler.py` 2, and eight files with one each.

## What the refusal should have said, measured on one of the 20

Upstream's payload, from
`tests/test_decisioning_handler.py::test_create_media_buy_sync_path_returns_typed_response`:

```python
CreateMediaBuyRequest(
    account={"account_id": "acct_a"},
    brand={"domain": "example.com"},
    idempotency_key="idem_aaaa1234567890",
    start_time="2026-05-01T00:00:00Z",
    end_time="2026-05-31T23:59:59Z",
    packages=[{"buyer_ref": "pkg_1", "product_id": "prod_1", "pricing_option_id": "cpm"}],
)
```

What the caller is told:

```
1 validation error for CreateMediaBuyRequest
  anyOf  ()  is not valid under any of the 3 branches
```

What each of our three branch CLASSES says when asked on its own:

```
ExplicitPackagesWithFixedAllocation             missing @ packages.0.budget
ExplicitPackagesWithSellerOptimizedAllocation   missing @ total_budget, missing @ budget_allocation
CommittedProposalExecution                      missing @ proposal_id, missing @ total_budget
```

And what the DOCUMENT says, at the root and at each branch of
`media-buy/create-media-buy-request.json`:

```
#            refuses
#/anyOf/0    refuses at packages.0
#/anyOf/1    refuses: 'total_budget' is a required property
#/anyOf/2    refuses
```

**So the refusal is CORRECT and the message is the defect.** The payload omits a required
property under every branch, the document agrees at all four pointers, and the classes
agree with the document. These 29 are payload corrections — and they are not correctable
from the report, because the report does not say what is missing.

## Why it comes out empty

`BranchDispatchMixin._agreed` is right about what an `anyOf` refusal IS:

> An ``anyOf`` refuses a payload exactly when every branch refuses it, so the branches'
> reports are not alternatives to choose between: **their INTERSECTION is the document's
> own refusal** and their difference is each branch's own requiredness.

That holds, and the worked example in its docstring is a case where the intersection is
non-empty: `create-media-buy-request.json`'s three branches all report `string_type` at
`('packages', 0, 'targeting_overlay', 'geo_countries', 0)`, and reporting that one row is
exactly right.

The gap is the case where **the intersection is EMPTY**. Each branch refuses for its own
reason, no position is shared, and the intersection of three disjoint sets is nothing — so
the fallback emits the bare combinator row. Measured on the same class: a payload also
missing `idempotency_key`, `brand`, `start_time` and `end_time` reports FOUR useful rows,
because those four are required by all three branches and the intersection is non-empty.
Add the four and the message collapses to nothing. **A more complete payload gets a worse
error**, which is the signature of this defect.

## What it should do instead

When the intersection is empty, report **each branch's own reason, attributed to its
branch**. That is not a guess between alternatives — it is the whole truth about why an
`anyOf` refused: no branch admits, and here is what each one wanted. pydantic's native
`anyOf` does this; the collapse is ours.

The project already states the obligation, in `adcp-client-python-jgsf`, quoted in
`_undetermined`'s own docstring:

> **A GOOD SENTENCE IS NOT A LOCATION.** A caller handed "no branch is determined" with an
> empty `loc` is no better off than one handed a type error with an empty `loc`:
> `core/error.json`'s `Error.field` is derived from the `loc` and is empty either way.

Here there is neither. `Error.field` is empty and `Error.message` says only that something
is wrong.

**The shape that keeps the intersection reading intact:**

* intersection non-empty → report it, unchanged. That is the document's own refusal and the
  46-branch `MCPWebhookPayload` case is why it matters: 46 branches' union of reasons is
  noise, their intersection is the answer.
* intersection empty → report each branch's rows, each prefixed with the branch its
  document names (`#/anyOf/1 (ExplicitPackagesWithSellerOptimizedAllocation)`), at the
  `loc` the branch reported them. A caller then has both the sentence and the position, and
  `Error.field` is derivable again.
* and cap it. 46 branches × several rows each is a wall; the first few branches in
  declaration order, with a count of the rest, is a message rather than a dump. **Say the
  count** — a silent truncation reads as "that was all of it".

## The order this wants doing in

The message fix does not make any of the 29 pass: they are payload defects and will still
fail, correctly. It is what makes them CORRECTABLE — so it comes first, and the 29
corrections follow it. Attempting the corrections first means guessing which property each
payload is missing from a report that does not say.
