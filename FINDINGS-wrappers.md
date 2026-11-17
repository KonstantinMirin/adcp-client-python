# `core/duration.json` is one concept again, and 27 positions stopped minting a second name

Measured on 2026-11-17, worktree `/srv/ws/wt-wrappers`, branch `claude/one-duration-not-eight`,
base `e00437663`, bundle `schemas/cache/3.2` patched by `codegen.patch.BUILD` (1,059 portable
documents).

## The three numbers

| | before | after |
|---|---|---|
| `make gate` | **7 failed / 2596 passed / 2603 total** | **7 failed / 2563 passed / 2570 total** |
| `./check` | emitted 1059 / refused 0 | emitted 1059 / refused 0 |
| `./check` | approximated 805 facts in 239 documents | approximated 805 facts in 239 documents |

Read off `test-results/gate/before.json` and `test-results/gate/after.json` and nothing else.
**No new failure and no fixed failure**: the failing set is the same seven node ids, item for
item. The total falls by 33 because 34 passing pairs lose their class and one gains a name
(below); **a pair that disappears with its class is the deliverable here and is not a
regression.**

**The approximation count is the measurement that nothing was dropped.** This change collapses
a wrapper class whose only content was a `description`, so a lost sentence would show up as a
fact the package no longer attributes anywhere — 805 facts in 239 documents before and after,
unmoved.

## The change: one conjunct, at PROP

`codegen/lower/composition.py`, `declares_nothing_its_base_does_not`:

```python
and (
    node.position is Position.PROP
    or all(_carries_nothing(word, node.position) for word in node.annotations)
)
```

**The screen was VACUOUS at PROP and nobody had measured it.** `Effect.ANNOTATION` has exactly
four members at PROP — `description`, `deprecated`, `enumDescriptions`, `x-enum-descriptions` —
against `NOTHING`'s 67, and the collapse destroys the carrier of none of them:

* `description` and `deprecated` are written onto the **enclosing field** by
  `codegen/lower/objects.py`'s `fields`, off this very node (`Field(description=...)`,
  `Field(deprecated=True)`), and a field is not what removing a class removes;
* `enumDescriptions` / `x-enum-descriptions` become the enum **member** docstrings, which
  belong to the `$ref` target's own enum type and were never on the wrapper.

So at a property the position is the whole of the test. At **ELEM** there is no per-element
`Field` for a sentence to live on — the table says the same thing in its own terms, where
`default` is an `ANNOTATION` at ELEM and a `FIELD` at PROP — so the conjunct still runs there;
at **ROOT** the predicate declines on its first clause for §1 and D5's reasons.

**The decision this reverses, and the premise that refutes it.** The predicate's own census had
measured this exact population — 235 single-`$ref` `allOf` nodes, 108 at a root, 7 of the 127
non-root stating only a `NOTHING` keyword, the next largest sibling set a bare `description` at
50 — and kept the class at those 50 because §6 makes a node's own `description` authoritative at
its own pointer. The choice it assumed, *mint a class or lose the sentence*, is not the choice on
offer at a referring position: the description's home there is the field, and the emitter already
wrote it there. The artifact carried it **twice**.

## The verification the change rests on, at all 27

For each of the 27 positions `tests_emit/test_a_bare_reference_declares_no_class.py` enumerated,
read off the schema node and the emitted tree:

* **every one is at PROP** — the walk's own position, not derived from the pointer string;
* **every one states `description` and nothing else** besides its `allOf`;
* **before**: the sentence appeared twice, as the wrapper's class docstring and as
  `Field(description=...)` on the enclosing field, byte-identical;
* **after**: the wrapper is gone at all 27, and at all 27 the field still carries the document's
  description verbatim, now typed as the target.

**27 / 27. No position had to keep its class, and none lost a fact.** The shape, at
`core/frequency-cap.json`:

```python
# before
class Window(Duration):
    """Time window for the max_impressions cap …"""
window: Annotated[Window | None, Field(description='Time window for the max_impressions cap …'), OmittedNotNull] = None

# after
window: Annotated[Duration | None, Field(description='Time window for the max_impressions cap …'), OmittedNotNull] = None
```

`core/duration.json` is one concept under one name again: a `FrequencyCap.window` is a `Duration`
and goes where an `AttributionWindow.post_click` is wanted, which the document always said.

## What went, pair by pair

34 passing pairs vanished and 1 appeared, net −33.

**The 27 enumerated**, by the name each used to mint: `ParamsDoohMetrics`, `ParamsViewability`,
`PostClick`, `PostView`, `Forecast`, `Period`, `Suppress`, `Window` (×3),
`MediaBuyFeaturesBiddingPolicy`, `Bidding` (×7), `Vendor`,
`OptimizationGoalEventAttributionWindow`, `FrequencyCapSupport`, `WindowsItemTotals`,
`MediaBuysItemBidding`, `PackagesItemBidding`, `TimeBudget`, `EstimatedWait` (×2).

**6 more positions the same predicate claimed**, which were not in the enumeration because
`survey/composites.py` does not classify them as a *bare* annotated `$ref` — each is the same
defect by the restatement route, and each now resolves to the target it referenced:

| position | was | now |
|---|---|---|
| `core/product-offer-filters.json#/properties/required_features` | `RequiredFeatures` | `CanonicalMediaBuyFeatures` |
| `core/registry-event.json#/oneOf/16/properties/payload` | `RegistryEventPublisherAdagentsChangedPublisherPayload` | `PublisherAdagentsPayload` |
| `media-buy/create-media-buy-request.json#/anyOf/0/properties/budget_allocation` | `ExplicitPackagesWithFixedAllocationBudgetAllocation` | `BudgetAllocationFixed` |
| `media-buy/create-media-buy-request.json#/anyOf/1/properties/budget_allocation` | `ExplicitPackagesWithSellerOptimizedAllocationBudgetAllocation` | `BudgetAllocationSellerOptimized` |
| `media-buy/list-products-request.json#/properties/push_notification_config` | `ListProductsRequestPushNotificationConfig` | `PushNotificationConfig` |
| `media-buy/product-discovery-criteria.json#/properties/outcome_target` | `ProductDiscoveryCriteriaOutcomeTarget` | `OutcomeTarget` |

**1 pair appeared and it is a RENAME, not a new class.**
`media-buy/get-media-buy-delivery-response.json#/properties/media_buy_deliveries/items/properties/totals`
was `MediaBuyDeliveriesItemTotals` and is now `Totals`: its sibling `WindowsItemTotals` went, so
the name no longer needs disambiguating, and the alias line `Totals = MediaBuyDeliveriesItemTotals`
that served the short spelling is gone with it. Same node, same pointer, same verdict.

## The committed tree was STALE, and the whole re-emission is what exposed it

**Two account wrappers also disappear from `src/`, and they are NOT this change.**
`media-buy/buy-products-request.json#/anyOf/1/properties/account` and the same pointer in
`media-buy/request-proposals-request.json` each re-declared
`core/canonical-account-ref.json`'s branches locally — `BuyProductsRequestAccountAccount`
plus two branch classes, likewise for request-proposals — and both fields now name
`CanonicalAccountReference` itself, with the node's restated `required: ['brand','operator']`
declared as a WIDENED approximation on the enclosing class instead of enforced by a cut class.

**Measured, not assumed.** Emitting those two documents with `declares_nothing_its_base_does_not`
reverted to HEAD's own text produces exactly that: no `BuyProductsRequestAccountAccount`,
`account: Annotated[CanonicalAccountReference, …]`, and the same two `Approximation(…
keyword='required', kind='WIDENED')` lines. So HEAD's compiler already collapsed them and the
committed tree had not been re-emitted since; `./check`'s 805 facts did not move because the
compiler was already counting them. Neither position is a graded pair in `before.json` or
`after.json`, which is why the gate total does not see them either.

The same staleness shows in the grade artifact: the emission command's in-process grade rewrote
`verdicts.tsv` with rows still naming classes the run had just deleted, so the table was re-taken
with `./verify` (a fresh process over the committed tree, the same command the last emission
change used). It now reads **2,570 pairs: 2,548 pass, 22 not pass**, and the five
`macro_declarations` pairs that flip `fail:accepts:witness_refused` → `pass` in it are the
witness lane's, not this one's.

## One thing outside this lane's scope

`tests_emit/test_union_dispatch.py`'s `ACCOUNT_RESTATEMENTS` pins
`BuyProductsRequestAccountAccount` and `RequestProposalsRequestAccountAccount` by name, and
**both are now AttributeErrors**:

```
FAILED tests_emit/test_union_dispatch.py::test_a_restated_required_key_is_required_of_the_class
AttributeError: module 'adcp.types._schemas.media_buy.buy_products_request' has no attribute
'BuyProductsRequestAccountAccount'. Did you mean: 'BuyProductsRequestAccount'?
```

That file is not in this lane's write scope, so it is reported here rather than edited. It is not
a gate failure — `make gate` runs `test_the_grade_is_green.py` alone — and the symbols it pins
were already absent from a fresh emission at HEAD; the pin was passing because it reads the
COMMITTED tree, which was stale. Re-emitting the tree is what makes the pin tell the truth, and
its own comment says what to do with it: *"a rename reddens here and a human says it is one
subject"* — except that here the class is gone rather than renamed, and the restated `required`
is now a declared widening, which is a decision for whoever owns that row.
