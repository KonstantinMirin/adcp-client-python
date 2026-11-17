# A class minted at a position that states no type

**The measure is `make gate`.** `test-results/gate/before.json` is trunk, taken first;
`test-results/gate/after.json` is the same command after the change. Every figure in the
delta section below is read off those two files and from nothing else.

## 1. TASK.md's diagnosis was wrong, and the owner corrected it

TASK.md read the two not-passing pairs as a mis-keyed `__adcp_schema__` — three classes at
`media-buy/buy-products-request.json#/anyOf/1/properties/account` carrying the union
node's pointer where the branch's own pointer exists — and asked for the branch pointer to
be written instead.

That reading is void, and the compiler already says so at the site. `codegen/lower/composition.py`
carries this comment, written when the pointer was last argued about:

> **AND A MERGED ONE SAYS SO** (`nodes.Base.merged`, `adcp-client-python-8awh`, the owner's
> ruling of 2026-11-11). […] Measured: `media-buy/buy-products-request.json` at
> `#/anyOf/1/properties/account` is exactly `{"required": ["brand", "operator"]}`, its
> `allOf` is the ROOT's at `#/properties/account`, and four classes were stamped at
> `#/anyOf/1/properties/account/allOf/0/...`.

So the shared pointer is a DECISION: `#/anyOf/1/properties/account/allOf/0/anyOf/0` is a
path the document does not contain, because the `allOf` under it belongs to the root's
declaration and not to this node's text. Re-keying the children to it would have reverted
that ruling and made the gate ask its question of a pointer no document holds.

**The defect is that the classes exist at all.** `#/anyOf/1/properties/account` is exactly
`{"required": ["brand", "operator"]}`: no property, no type word, no `additionalProperties`.
It only RESTRICTS members `core/canonical-account-ref.json` declares, which
`#/properties/account` already references. A combinator branch does not admit on its own —
a payload is validated against the whole `anyOf` and never against branch 1 alone — so a
class minted there admits a set no wire position is ever validated against. That is what
the gate reported: `accepts=fail:model_refused_valid` on the `AccountId` cross, which
refuses every payload its own pointer admits.

## 2. The site, measured rather than guessed

Traced by spying on `ir.ClassDecl` through a one-document compile of
`media-buy/buy-products-request.json`:

```
codegen/emit.py:947            lower_document
codegen/lower/union.py:2431    lower_union  -> branch #/anyOf/1 composes the root's shape
codegen/lower/objects.py:235   fields       -> the property `account`
codegen/lower/composition.py:2138/2189   declare_object, then _distribute
```

and the decision that sends it there is one line up, in
`codegen/lower/inherited.py`'s `merge`: the restatement NARROWS, so the key becomes the
composing node's OWN declaration, §2's intersection of `{"required": [...]}` with the
root's `{"allOf": [{"$ref": "core/canonical-account-ref.json"}]}`. That merged node's
conjunct resolves to a UNION ROOT, so §5's distribution crosses it with every branch and
mints one class per branch — `…AccountAccountAccountId` being the cross that cannot hold an
instance.

None of the four files TASK.md's write scope listed writes the ref: `schema/parse.py`,
`lower/union.py` and `intersect.py` are all consulted on the way, and the class is declared
by `lower/composition.py` on the back of `lower/inherited.py`'s per-key verdict. The owner
put `codegen/lower/inherited.py` in scope for this lane and ruled `codegen/intersect.py`
out — `intersect.restatement` is §2's intersection at every two-base branch, pin and
conjunct merge, so changing it has the whole bundle as its blast radius.

## 3. What was written

`codegen/lower/inherited.py`, two things and nothing else.

**`_restricts_without_declaring`** — a declaration states a RULE, not a TYPE, when its every
keyword only restricts members declared elsewhere. The reading is recursive and that is the
whole of it: `{"properties": {"account": {"required": [...]}}}` states `properties` and is
STILL a rule, because the property it names declares nothing — it narrows. A test that
stopped at the keyword would call that a declaration and leave the account case exactly
where it was. `None` — "this declares a member" — is the safe answer and every uncertain
shape takes it: a declaration stating nothing, an empty `required`, an empty or non-mapping
`properties`, an entry that is anything but a restriction.

`core/canonical-account-ref.json`'s own two `anyOf` branches are untouched by it, and twice
over: each states `additionalProperties`, which is not in the restricting set, and each
states `properties` whose entries carry real declarations. `CanonicalAccountReferenceAccountId`
and `…BrandOperator` are correct classes and this reading never reaches them.

**The narrowing row now leaves such a key INHERITED** — the base's DECIDED field, re-used,
which is the treatment §2's requiredness overlay already gives the shape next to it — and
DECLARES the dropped fact: `Approximation(kind='WIDENED', rung='KEYWORD')` at the node's own
pointer, carrying the document's own spelling of the restriction.

The declaration is not a nicety. No rule kind in `adcp.types._runtime` reaches into a
child's members — `RequiredGroups`, `PresenceGroups`, `ForbiddenGroups`, `Dependencies`,
`Match`, `ConditionalRequired` are each about the class's OWN keys — so "account must carry
brand and operator" has no carrier, and leaving the key inherited makes the class WIDER than
its document there: `BuyProductsRequestAccount` now accepts `{"account": {"account_id": "x"}}`
with no top-level `brand`, which the document refuses because neither branch is then
satisfied. §2 permits that only as a declared widening.

What the emission now reads at the site:

```python
class BuyProductsRequestAccount(BuyProductsRequest):
    __adcp_schema__ = SchemaRef(document='media-buy/buy-products-request.json', pointer='#/anyOf/1')
    __adcp_approximations__ = (
        Approximation(document='media-buy/buy-products-request.json',
                      pointer='#/anyOf/1/properties/account', keyword='required',
                      kind='WIDENED', rung='KEYWORD', fact=['brand', 'operator'], …),
    )
    account: Annotated[CanonicalAccountReference, Field(description=…)]
```

## 4. BRANCH, never CONJ — the position kind is the line

A first cut of the reading above fired wherever a restatement declared no member, and it
took a **third** node with it. The emission diff named it at once, and the owner's ruling of
2026-11-17 settled it: the line is the POSITION KIND, and the compiler already draws it.

| node | declaration | nearest combinator |
|---|---|---|
| `media-buy/buy-products-request.json#/anyOf/1/properties/account` | `{"required": ["brand", "operator"]}` | `anyOf` → **BRANCH** |
| `media-buy/request-proposals-request.json#/anyOf/1/properties/account` | the same | `anyOf` → **BRANCH** |
| `core/signal-coverage-forecast.json#/properties/points/items/allOf/1/properties/metrics` | `{"required": ["coverage_rate"]}` | `allOf` → **CONJ** |

**The argument was never "it declares no member" on its own — it was that A BRANCH DOES NOT
ADMIT ON ITS OWN.** A payload is validated against the whole `anyOf`, so a class minted for
one branch describes a set no wire position is ever checked against. That holds at BRANCH
and it does NOT hold at CONJ: every conjunct of an `allOf` must be satisfied by every
instance reaching that position, so a restriction-only conjunct genuinely narrows. By §3a's
own admission test the two differ and a payload can tell them apart — `{}` satisfies
`core/forecast-point.json`'s `metrics` and is refused at the signal-coverage-forecast
position, which is a distinct admitted set and therefore a TYPE. The narrowing subclass
there was CORRECT, and it is untouched: that module re-emits byte-identical and its pair is
back in the grade.

`bundle.DESCENDS` maps `anyOf`/`oneOf` to `Position.BRANCH` and `allOf` to `Position.CONJ`,
so `_nearest_combinator` reads the walk's own descent step backwards off the pointer the
walk spelled, rather than inventing a test: a segment is a keyword only where that table
holds a subschema under it, `properties` spends the name beside its word and a combinator
spends an index — which is what keeps a property NAMED `allOf` a property.

For the record, the knob that was NOT taken. "Fire only where the base DISTRIBUTES — where
it is a union root" separates the same three nodes and is the wrong reading: it makes the
answer a property of what the base happens to be, where the argument is about what the
POSITION admits. A restriction-only conjunct over a union root would still be a genuine
narrowing, and a restriction-only branch over a plain class would still describe a set
nothing is validated against. The position kind answers both; the base's kind answers
neither.

**Measured both ways.** With the reading unconditioned, `./check` read
`approximated 806 facts in 239 documents` and the gate lost seven pairs — the six below plus
`core/signal-coverage-forecast.json#/…/metrics Metrics`, which had been PASSING. With it
gated on BRANCH, `./check` reads 805 facts in 239 documents, the metrics module re-emits
byte-identical, and the gate loses six.

## 5. Follow-up: the carrier that would enforce instead of declare

A nested-requiredness rule, which is the correct long-term fix and bigger than this lane.
What it would have to express, and where:

* **a rule kind** in `src/adcp/types/_runtime.py` holding `(key, groups)` — "the value at
  `key` carries every name of some group" — validated against the child mapping before the
  child's own class is built, so it holds whether the child's type is a class or a union
  base;
* **the lowering** in `codegen/lower/rules.py`, written from the same reading added here:
  `_restricts_without_declaring` already returns the facts in the document's own spelling,
  so the rule's value is in hand at the point the declaration is minted today;
* **the renderer** in `codegen/render.py`, which spells rule literals into the class body;
* **the grader** in `codegen/harness.py`, so a pair carrying the rule is graded on it
  instead of on a `WIDENED` declaration — the two BRANCH sites in §4 are its whole
  population today.

With that carrier those two nodes keep their restriction and need no declaration at all,
and neither needs a class either way. The CONJ site needs nothing: its narrowing subclass
already enforces the restriction, which is the whole of §4's distinction.

## 6. Out of scope, and therefore NOT written

**`src/adcp/types/_surface/{core,media_buy,_flat}.py`.** Removing six classes removes six
re-exports, and those files are the re-export surface. `src/adcp/types/_schemas/**` is in
this lane's write scope and the surface is not, and a PARTIAL re-emission is the exact defect
TASK.md warns about — the committed tree would import names no module defines any more. So
the committed tree is left ENTIRELY untouched: stale against this compiler, and coherent.
The owner confirmed that call and will re-emit the whole tree on trunk after this lands, so
**the next reader should not "fix" the staleness here.** The gate is unaffected, because
`tests_emit/fresh.py` materialises a tree from the compiler and binds it in front of the
committed one, keyed on a digest over `codegen/` — nothing grades the committed tree.

The two `_schemas` modules the change rewrites are
`media_buy/buy_products_request.py` and `media_buy/request_proposals_request.py`.
`core/signal_coverage_forecast.py`, `constraints.py` and `envelopes.py` all re-emit
byte-identical.

`src/adcp/types/domains/__init__.py` also differs from what a fresh run writes — it carries a
`mirrored()` helper and a `pkgutil` import the emitter does not write. That divergence is
not this change's and was not touched.

## 7. The delta, from before.json and after.json only

| | before.json | after.json |
|---|---|---|
| passed | 2595 | 2591 |
| failed | 14 | 12 |
| total | 2609 | 2603 |

**No pair flipped and no pair is new.** Six pairs are GONE and that is the whole of the
movement — all six at the two pointers this lane was opened for, because the three classes
each of them carried no longer exist:

| verdict in before.json | pair |
|---|---|
| **FAILED** | `media-buy/buy-products-request.json#/anyOf/1/properties/account BuyProductsRequestAccountAccountAccountId` |
| **FAILED** | `media-buy/request-proposals-request.json#/anyOf/1/properties/account RequestProposalsRequestAccountAccountAccountId` |
| passed | `media-buy/buy-products-request.json#/anyOf/1/properties/account BuyProductsRequestAccountAccount` |
| passed | `media-buy/buy-products-request.json#/anyOf/1/properties/account BuyProductsRequestAccountAccountBrandOperator` |
| passed | `media-buy/request-proposals-request.json#/anyOf/1/properties/account RequestProposalsRequestAccountAccount` |
| passed | `media-buy/request-proposals-request.json#/anyOf/1/properties/account RequestProposalsRequestAccountAccountBrandOperator` |

The two failures the lane was opened for are gone. The other four are the union base and
the inhabitable cross at those same two pointers: a position that states no type now
carries no class at all, so it carries no pair either. The twelve remaining failures are
twelve of before.json's fourteen, unchanged.

## 8. `./check`

`emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059`, unchanged, with
`approximated 805 facts in 239 documents` against trunk's 803 in 238 — the two declarations
of §3, one of them in a document that carried no approximation before. These are the
COMPILER's counts and are not a result.
