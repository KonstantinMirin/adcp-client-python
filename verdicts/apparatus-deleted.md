# The construction answers 2,604 of 2,608 graded pairs in 0.4 s

`adcp-client-python-hzio.5`. This file records the measurements that decide whether the
search apparatus can be deleted and which source builds the payload, and the findings they
produced. **The deletion itself is not in this commit** — what is here is the evidence
that it lands, the source it should be built from, the node-level findings it has to carry,
and the order the removal has to happen in.

## The measurement

`witness.Construction.value` and `.mutations` asked for every pair the committed tree
pairs. No draw, no corpus, no `hypothesis`, nothing warmed:

| over 2,608 graded pairs | count |
| --- | --- |
| a VALID constructed value | **2,604** |
| …and at least one INVALID one beside it | 2,329 |
| …valid but with nothing to violate | 275 |
| no value at all | **4** |
| wall clock, whole set, cold | **0.4 s** |

Against the apparatus it replaces: 604–750 s warm for the same set, and one pair that
does not finish cold at any bound. That is the whole argument for the row, and it is a
measurement rather than a projection — the construction is already written, already
graded, and already answers.

## Why the apparatus costs what it costs — measured, then abandoned

`adcp-client-python-zb82` asked for the canonicalisation memo's key to be made cheap. The
measurement taken before that was stopped is worth keeping, because it is the clearest
statement of why the layer should not exist rather than be tuned. On
`media-buy/get-media-buys-response.json#` alone, cold:

* **357,656 calls** into the memo, over **8,430 distinct schemas**, presented as **307,697
  distinct object identities**;
* to answer them the key rendered **5.01 GB of text**;
* content hit rate 97.6%; identity hit rate 14.0%, sound (0 ids ever held two contents).

So the identity key the row proposed would have collapsed the hit rate, and the content
key costs 5 GB of rendering per document. Attributed by caller over the same run, JSON and
zlib leaf time is 56.7% (184.4 s of 325 s), of which `shared` itself is 104.0 s —
63.4 s parsing the value back on hits and 40.6 s rendering the key. A cache that pays a
full serialise-and-parse to discover it already has the answer is not a cache to tune.

## Two findings, named rather than covered

The row's rule: *if something genuinely cannot be constructed from a node's keywords, that
is a FINDING about the node — name the document and pointer and report it.*

### 1. Four pairs where the construction's pointer walk disagrees with the tree's

```
media-buy/buy-products-request.json#/anyOf/1/properties/account/allOf/0/anyOf/0
media-buy/buy-products-request.json#/anyOf/1/properties/account/allOf/0/anyOf/1
media-buy/request-proposals-request.json#/anyOf/1/properties/account/allOf/0/anyOf/0
media-buy/request-proposals-request.json#/anyOf/1/properties/account/allOf/0/anyOf/1
```

Each raises `KeyError: 'allOf'` from `witness.Construction._settles` →
`bundle.node_at(record, at)`. **This is not the known `schema_at` defect** that
`codegen/__main__.py` records for these two documents: `schema_at` resolves all four
pointers without raising. So the two readings of "where is the node at this pointer"
disagree — `_base.applied_schema` reaches it and the construction's own segment walk does
not — and that is a defect in one of the two readings, not a node that states too little.
It must be settled before the construction is the only source, because these four would
otherwise go from graded to ungraded.

### 2. Two hundred and seventy-five pairs state nothing an invalid payload can violate

A valid value is constructed for all of them; `mutations` returns none. Mostly union
branches and `additionalProperties` subjects — `adagents.json#/oneOf/1/properties/formats/
items/allOf/0/oneOf/{0..15}`, `adagents.json#/oneOf/1/properties/tags/additionalProperties`,
`brand.json#`, `a2ui/bound-value.json#`.

A node that states no keyword refuses nothing, so "no invalid payload" may be the correct
answer rather than a gap — but it is 10.5% of the set and the refuses check has nothing to
offer at any of them, so it is a coverage figure that has to be stated and carried, not
discovered later. `adcp-client-python-hzio.8` is the coverage-accounting row and this is
its input.

## Which source builds the valid payload — picked on merit, with the measurement

The library was never the defect; calling it at grade time was. So the builder's source is
chosen by asking both the same question about the same depth-two node, once per document,
and screening both answers with the document's own validator. Depth two here is every
enclosure pinned to `Construction.floor` and the subject's own members left as stated.

| once per document, over 1,020 of the bundle's documents | constructor | hypothesis |
| --- | --- | --- |
| the DOCUMENT admits it | **1,019 (99.9%)** | 916 (89.8%) |
| seconds, whole bundle | **0.22** | 380.7 |
| root properties the payload carries | **1,615 / 5,452** | 1,532 / 5,452 |
| documents where it is the ONLY answer | **103** | **0** |

So the constructor is the source: it wins on admission, on cost by three orders of
magnitude, and on aggregate coverage, and there is **no document hypothesis answers that
it does not**. The 103 are mostly `Unsatisfiable` — hypothesis declining a node the
constructor builds from its own keywords.

**And hypothesis still earns a place in the builder, on 25 documents.** Where both are
admitted, hypothesis carries strictly more of the subject's own root than the constructor
does on 25 of 1,020:

```
core/canonical-pricing-option.json          3 of 15  ->  12 of 15
core/reporting-status-issue.json            5 of 20  ->  11 of 20
core/attestation-evaluation.json            6 of 13  ->  10 of 13
core/product-format-declaration.json        0 of 15  ->   3 of 15
formats/canonical/native_in_feed.json       0 of 19  ->   2 of 19
```

The constructor builds what a node STATES — `required` keys, `const`, `enum`, bounds — and
omits optional members no keyword demands. Hypothesis populates them. An accepts check
learns nothing about a member the payload omits, so a richer admitted payload is a better
one, and this is the measured case for keeping the library.

**The builder therefore runs both, once per document, and keeps the constructor's payload
unless hypothesis's is admitted AND strictly richer.** That costs ~381 s once for the whole
bundle, written to a cache keyed on the file hash — which is precisely the cost that is
fine to pay once and was never fine to pay 509 times per pair at grade time.

### A coverage figure that has to be carried either way

Both sources leave most of the subject's root untouched: 1,615 and 1,532 of 5,452 declared
root properties, under 30% each. Even taking the better of the two per document, a majority
of declared optional members appear in no payload. That is not a defect in either source —
nothing in the document demands those members — but it is the honest coverage statement
owed to `adcp-client-python-hzio.8`, and it is larger than the 275 pairs with no invalid
payload.

## The order the deletion has to happen in

Grounded in the above rather than in the module layout:

1. **Settle finding 1.** Four pairs, one disagreement between two pointer readings.
2. **Make the construction the only source in `check_accepts`.** The argument is already
   wired and already answers first; what goes is the fallback to the corpus, to `examples`
   and to the draw.
3. **Source `check_widening`'s value classes from `Construction.classes`/`admits`.** This
   is the check that holds both slow pairs, and `_Draws` is reachable from nowhere else
   once it lands.
4. **Then the deletions are mechanical, because nothing calls them:** `one_instance` and
   `strategy` AT GRADE TIME and every grade-time call site; the `canonicalish` patch and
   its memo (`zlib`, `blake2b`, `json.dumps`, `_round_trips`) — nothing is canonicalised
   509 times if it is canonicalised once; `validator_classes_shared_within_one_call` if
   nothing else needs it; `Fixtures.reduced`/`_pin`/`_derived_pin`/`value` and the cycle
   they form, whose whole purpose was making one sampled draw affordable; both committed
   corpora, which a cache keyed on the file hash replaces; `BUDGET = 30` and every
   remaining cap, example count and wall-clock bound.

   **`hypothesis` and `hypothesis_jsonschema` STAY**, as build-time dependencies of the
   cache builder, and so does `_padded_string` — it closes a real gap where the library
   refuses to draw at a length floor above its own buffer, and it reaches one declaration
   of the 1,054. The acceptance test is not a grep: it is that profiling a graded pair
   shows no `from_schema`, no `canonicalish` and no `iterencode` anywhere in it.
5. **The cache key becomes the hash of the file.** A document is a file; it changes when
   the file changes. Nothing is committed; a missing or stale entry is rebuilt.

Step 4 cannot be verified except after 2 and 3, because until then the deleted names still
have callers.

## What is NOT done

The deletion. This commit carries the measurement, the two findings and the order — not
the removal. Stating that plainly is the point: a half-landed deletion of a 10,041-line
module with six checks interlocked through it would leave the tree neither searching nor
constructing, and the row's own standard is that *a run that still carries a corpus has not
landed this change, whatever its timings say*. The converse holds too — a run that has
lost the corpus and cannot grade has not landed it either.

`./check` is unmoved by this commit: `emitted 1059 / refused 0`, `primary 0 / chained 0`,
`approximated 383 facts in 148 documents`.
