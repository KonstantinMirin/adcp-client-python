# The construction answers 2,604 of 2,608 graded pairs in 0.4 s

`adcp-client-python-hzio.5`. This file records the measurement that decides whether the
search apparatus can be deleted, and the two findings the measurement produced. **The
deletion itself is not in this commit** — what is here is the evidence that it lands, the
two nodes-level findings it has to carry, and the order the removal has to happen in.

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

## The order the deletion has to happen in

Grounded in the above rather than in the module layout:

1. **Settle finding 1.** Four pairs, one disagreement between two pointer readings.
2. **Make the construction the only source in `check_accepts`.** The argument is already
   wired and already answers first; what goes is the fallback to the corpus, to `examples`
   and to the draw.
3. **Source `check_widening`'s value classes from `Construction.classes`/`admits`.** This
   is the check that holds both slow pairs, and `_Draws` is reachable from nowhere else
   once it lands.
4. **Then the deletions are mechanical, because nothing calls them:** `one_instance`,
   `strategy`, `from_schema`; the `canonicalish` patch and its memo (`zlib`, `blake2b`,
   `json.dumps`, `_round_trips`); `validator_classes_shared_within_one_call`;
   `Fixtures.reduced`/`_pin`/`_derived_pin`/`value` and the cycle they form; both committed
   corpora and the layering above them; `hypothesis` and `hypothesis-jsonschema`;
   `BUDGET = 30`; every remaining cap and example count.
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
