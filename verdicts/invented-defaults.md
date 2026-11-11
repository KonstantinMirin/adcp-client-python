# 0z0u / eknd — whose each of the 867 invented defaults is, and the floor it puts on the suite

`adcp-client-python-0z0u` and `adcp-client-python-eknd`, the same subject from two sides.
Branch `claude/issue-b2pm-alias-note`, cut from `ours/9.6.1` at `bfeaf7eec`. Nothing in
`src/`, nothing in `codegen/`, and **nothing under upstream's `tests/` — their suite stays
byte-identical**. The instrument is
`survey/invented_defaults.py`, extended rather than replaced; the per-pair table is at the end
of this file and `--attribute` writes it as a TSV anywhere a reader wants one.

```bash
PYTHONPATH=.:src ./.venv/bin/python survey/invented_defaults.py --attribute $S/whose.tsv
PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --write --collect
```

`--attribute` writes the per-pair table as a TSV wherever it is pointed; the 867 rows are also
written out in full at the end of this file, so the attribution is readable without a run.

The set reproduces exactly before anything is added to it: **867 pairs, digest
`7d05549bb6e45d66b955`**, 237 collapsed-disjunction / 477 const-restated / 8 contradicts /
145 invented-value, over 624 classes and 177 fields.

---

## THE ANSWER

| | | |
|---|---|---|
| **(a) OUR DEFECT** — the document states the default and we failed to read it | **0** | of 867 |
| **(b) THEIR ARTIFACT** — upstream's generator invented it | **867** | of 867 |
| **(c) STATED ELSEWHERE** — an enclosing `allOf`, a `$ref` target, a sibling `if`/`then` | **0** | of 867 |

**Every one of the 867 is upstream's.** Not one of them is a `default` this compiler failed to
read, and not one of them is a `default` the document states anywhere the instance can reach.

So the drop list is derived from this and from nothing else:

| | |
|---|---|
| tests declined, every one on a (b) pair | **72** functions / **257** collected items |
| of them in the **577 behavioural** files | **31** |
| of them in the **104 generator-grading** files | 41 |
| raw denominator / graded denominator | **18,157** / **17,900** collected |

**31 behavioural test functions is the hard floor this cause contributes.**
`adcp-client-python-7xmt` put the whole unreachable set at ~2,200 without separating the
causes; this cause is **31 of them**, not 2,200, so the invented defaults are a small part of
that number and the rest is owed to the other causes — which this row does not touch.

---

## How (a) was decided, and why 0 is not vacuous

For a pair to be (a), the document must state a `default` for the property somewhere the
conjunction reaching the position holds against the same instance, and our class must not
carry it. The instrument already reads that: `stated_value` looks for `const` first and
`default` second across every node `conjoined` reaches — the position's own node, every member
of every `allOf`, transitively, and through the record's own storage.

**Over all 867 pairs the `document_states` column is `const` (485) or `nothing` (382), and
never `default`.** The reading is live, not asleep: `stated_value([{"default": "x"}])`
answers `('default', '"x"')`, and `stated_value([{"const": "c", "default": "c"}])` answers
`('const', '"c"')`, which is the documented precedence.

**The 477 `const-restated` rows are the ones worth saying out loud, because they look like
(a) and are not.** The document pins the value with `const` and upstream's default equals it,
so the VALUE is the document's — but a `const` constrains a value that is present; it does not
supply one that is absent, and it does not make a required property optional. Where the
conjunction requires the property, upstream's default admits an object the document refuses.
The value being right does not make the default right.

---

## How (c) was decided, and the perturbation that says it is not vacuous

`default_elsewhere` widens the search to the three places the row names, in this order, so the
nearest statement is the one reported:

1. **a branch of a disjunction** the conjunction reaches — every branch, and every `allOf`
   member of every branch, through the store;
2. **an `if` / `then` / `else`** of the conjunction, read as a separate place and never folded
   into the conjunction, because draft-07 applies `then` only to an instance the `if` accepts;
3. **any other position of the same document** that declares the property.

It found **nothing, for any of the 867**. That is a real zero and not a search that never
fires:

* the bundle states **2,862 property `default`s across 330 documents** — `core/async-response-data.json`
  alone states 89 — so there was plenty for it to find;
* **perturbed**: a `default` planted under the first branch at `core/postal-area.json#/anyOf/0`
  is found and reported as `branch-of-a-disjunction` at that pointer; the unplanted control answers
  `('', '', '')`.

---

## What our own side does with the same 867 fields

Read off our emitted classes by each class's own `__adcp_schema__`, at the same position:

| | rows |
|---|---|
| ours declares the field **required** | 354 |
| ours leaves it optional and a **RULE** carries the requirement | 91 |
| ours has **no such field at that position** | 398 |
| ours leaves it optional with **no rule naming it** | 24 |

**The 91 are correct and the mechanism is measured, not asserted.** Where the document states
a disjunction and SOME branch requires a property, the requirement cannot sit on the
annotation — no branch is the whole position — so this compiler puts it in a rule.
`core/attestation-evaluation.json#/properties/action_binding` is the worked case: our
`ActionBinding` carries
`RequiredGroups(groups=(('action_id',), ('action_digest',)), combinator='anyOf')` and
`ActionBinding.strict_validate({"action_type": "x"})` is **REFUSED**, while upstream's class
admits the same object. That is the whole difference between the two trees at these 867 rows,
in one call.

**The 24 are a finding of OURS and they are named rather than folded in.** All 24 are
`collapsed-disjunction`, over 7 positions — `core/product-filters.json` and
`core/targeting.json` at `/properties/geo_proximity/items` (6 each),
`formats/canonical/seller_rendered_stateful_display.json` at
`/properties/states/items/properties/breakpoints/items` (6),
`core/demographic-targeting-intent.json#/properties/age` (2),
`creative/list-creatives-response.json#/properties/creatives/items` (2), and the two
`viewability` nodes (1 each). At those our class is optional with no rule naming the field,
which is the same laxness this verdict charges upstream with — **a smaller instance of the
same defect, on our side, and it is not in the 867 because the 867 is a set over UPSTREAM's
classes.** It is a row of its own and is reported here so it is not lost.

The instrument's own reading of our tree agrees and is the authoritative one for "is a class of
ours lax", because it asks at OUR class's stamped pointer: `--ours` reports **6,724
required-no-default, 142 field-not-declared-here, 11 disjunction-base, and 1 invented-by-us**
over 6,878 conjunction-required fields. That one is
`adcp.types._schemas.core.creative_representation.CreativeRepresentationFormatId.format_kind`
at `core/creative-representation.json#/allOf/0/oneOf/0`, and it is **not** one of the 867. The
bead's note records this figure as 0 of 6,812; the tree has grown and it is now 1 of 6,878.

---

## THE DROP: 72 tests declined, and every one on a (b) pair

**The rule, and nothing else qualifies:** a test is declined ONLY where it asserts on a (b)
pair. Never because it is red, never because it is slow, never because it is hard. The input
is the classification above and nothing else — `survey/dropin/deselect.py` reads no test
result, no duration and no traceback. **A red test that is not on a (b) pair stays in the
denominator, and a green one that is on one is still declined**, because the question is what
the test GRADES, not what it currently does.

| | |
|---|---|
| tests declined | **72** functions, **257** collected items |
| of them, in the 577 **behavioural** files | **31** |
| of them, in the 104 files that already **grade their generator** | 41 |
| `(test, pair)` reasons, over 26 files | 214 |

The two units are the same drop: a node id names a FUNCTION and pytest collects one ITEM per
parametrised case of it. Measured, not inferred — a collect-only run matches 257 collected ids
against these 72 prefixes.

Reasons by the set's own kind — 173 `const-restated`, 26 `collapsed-disjunction`, 13
`invented-value`, 2 `contradicts` — and by idiom: 192 keyword constructions, 22
`model_validate` dict literals.

**41 of the 72 change no behavioural figure**, and the column says so rather than letting the
drop look bigger than it is: those files are on this repository's own declared list of the 104
that grade upstream's generator, already outside the behavioural denominator.

Every row of `survey/dropin/deselected-9.6.1.tsv` carries, in one line: the node id, the
`(model, field)` it asserts, the document and pointer that refutes the default, upstream's
default, what the document states there, the idiom, and the kind. A reader can check any
single row against the bundle without running anything.

### What the list does not see, and it is a floor on purpose

A call carrying `**` is skipped outright — the field may be in the mapping, and a site the
reading cannot decide must not put a test on the list. A payload built in one place and
validated in another has no keys at the call site, so it is not read either. **Both omissions
fail in the safe direction**: a test the list misses stays in the denominator and counts
against us.

---

## THE MECHANISM: generated, and upstream's suite stays byte-identical

`survey/dropin/deselect.py` writes `survey/dropin/deselected-9.6.1.tsv` from the
classification. It is not a hand-edited file and it is not an edit to upstream's tests — **we
do not fork their suite, we decline to count it, and the reason is attached to each node id.**
If the classification moves, the list regenerates.

The runner consumes it directly:

```bash
./.venv/bin/python -m pytest tests/ \
    $(PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --pytest-args)
```

`--pytest-args` prints one `--deselect=<node id>` per line. Nothing under `tests/` is touched
by any mode of the generator, and `--write` only ever writes its own table.

The generator REFUSES rather than writing an empty list: a classification that selected
nothing, or one with no (b) pair, would produce a file that reads exactly like "nothing needed
dropping", which is the one failure that would pass unnoticed.

---

## THE TWO NUMBERS, reported together

Collected on this tree, `tests/` being upstream's own suite:

| | |
|---|---|
| **raw** — upstream's whole suite | **18,157** collected |
| **declined** — every one on a (b) pair | **257** items (72 functions) |
| **graded** — the suite minus the declined set | **17,900** collected |

**These are DENOMINATORS and not pass figures.** The pass half needs a full run of upstream's
suite with the list applied, which is the drop-in lane's measurement and not this row's; this
row supplies the list and the two denominators it is read over. Stating a pass figure here
without that run would be exactly the invention this verdict charges upstream with.

Target 4 is **"every test that grades the PROTOCOL passes"**, not "upstream's suite passes".
The second is unachievable without reproducing their bugs: 257 collected items assert on a
default the document refutes, and the only way to turn them green is to put the default back.

---

## The one line that carries the whole `status` family

`adcp.types.domains.core.protocol_envelope.ProtocolEnvelope` writes

```python
status: Annotated[TaskStatus, Field(description='... REQUIRED on every task response envelope ...')] = TaskStatus.completed
```

and **116 of upstream's generated classes inherit it**. `core/protocol-envelope.json` states
`required: ['status']` and an enum of nine values, with no `default` and no `const`. So
upstream's own field description says REQUIRED and upstream's own generator made it optional
with an invented value. 118 of the 867 rows are a `status`; 116 come from that one line.

This is the clearest case in the set of why the answer is (b) and not (a) or (c): the document
is unambiguous, it is stated at the position, and both readings of "somewhere else" find
nothing because there is nothing to find.

---

---

## THE UPSTREAM ASK: one comment, one new issue

**Checked first, as instructed.** [#1678](https://github.com/adcontextprotocol/adcp-client-python/issues/1678)
is OPEN and its latest comment is already this subject one level finer — *"the fields arrived,
the `required` did not"*, with 45 of their generated `*Response` classes carrying `status` as
optional and the note that *"the model emits a `status` the caller never set"*.
[#1684](https://github.com/adcontextprotocol/adcp-client-python/issues/1684) is CLOSED and is
the accepted precedent for the class: `Signals.data_provider_domains_complete` defaults to
`True` and fails the schema's own `dependencies` rule at boot.

So the ask splits, and the split is the document's rather than a matter of taste:

* **the envelope `status` family — 118 of the 867, 116 from one line — belongs as a COMMENT on
  #1678.** It is that thread's current subject and this is the measurement it is missing: the
  count of inheriting classes and the one line they inherit.
* **the other 749 are NOT the envelope** — 624 classes, 177 fields, three further mechanisms —
  and belong in a NEW issue, with #1684 cited as the accepted precedent.

### Draft comment for #1678

> **The 45 optional `status` fields are one line, and it is `ProtocolEnvelope`'s**
>
> Measured on the PyPI wheel `adcp 9.6.1` against its own bundle copy, by resolving each
> generated class's defaults against the document the module header names.
>
> `adcp/types/domains/core/protocol_envelope.py` writes
>
> ```python
> status: Annotated[TaskStatus, Field(description='... REQUIRED on every task response envelope ...')] = TaskStatus.completed
> ```
>
> and **116 generated classes inherit it**. `core/protocol-envelope.json` states
> `required: ["status"]` and an enum of nine values, with **no `default` and no `const`**. So
> the field's own description says REQUIRED and the generated class makes it optional, with a
> value the document does not state.
>
> That is why the regeneration this issue tracks will not close it on its own: composing the
> envelope supplies the FIELD, and the default is what drops the `required`. The two halves
> are independent, and only the first has landed.
>
> The consequence is the one the thread already names — `model_dump` emits a `status` the
> caller never set — plus a second: `GetProductsResponse.model_validate({"products": []})` is
> ACCEPTED while `jsonschema` against the wheel's own bundled document reports
> `['allOf', 1, 'required']`. The class and the bundle it ships disagree about the same
> payload.
>
> Suggested fix, in the generator rather than per class: where a property is in a
> `required` list the conjunction reaching the node states, emit no default — whatever the
> enum's first member is. A `const` is not a default either: it constrains a value that is
> present and does not supply one that is absent.

### Draft body for the new issue

> **Title:** Generated classes default 867 required fields the schemas do not default
>
> **Observed (adcp 9.6.1)**
>
> Across the generated tree, **867 `(class, field)` pairs** carry a `default` for a property
> the document's own conjunction **requires**, over **624 classes** and **177 fields**. A
> default makes a required field optional, so each of those classes admits a payload the
> bundled schema refuses — measured against the wheel's own `adcp/_schemas/3.2`.
>
> The pairs fall in four kinds:
>
> | kind | pairs | what it is |
> |---|---|---|
> | `const-restated` | 477 | the document pins the value with `const` and the default equals it. The VALUE is the document's; the OPTIONALITY is not |
> | `collapsed-disjunction` | 237 | the document states `oneOf`/`anyOf` and SOME branch requires the property; one class was emitted for the whole position, so the requirement had nowhere to live and was defaulted. The class admits an instance satisfying no branch |
> | `invented-value` | 145 | the document states neither a `default` nor a `const`, and the class both drops the requirement and pins a value the document never states |
> | `contradicts` | 8 | the document states a `default` or `const` and the generated default is a different value |
>
> **The worked case**, which is the clearest:
>
> `media-buy/create-media-buy-response.json` is `allOf[2]` + `oneOf[3]`. `allOf[1]` declares
> `status` and lists it in `required`, so the conjunction requires `status` for every branch;
> only `oneOf[2]` narrows it to `const: 'submitted'`. The generated
> `CreateMediaBuyResponse1` writes `status: Literal['completed'] = 'completed'` — a value the
> document states nowhere for that branch, on a field it requires.
>
> **Expected**
>
> No default on a property the conjunction reaching the node lists in `required`. The check is
> cheap and belongs in the generator: resolve the node's `allOf` chain, take the union of the
> `required` lists, and emit no default for any name in it. A `const` is not a default: it
> constrains a value that is present and does not supply one that is absent.
>
> **Precedent**
>
> #1684 is the same class of defect, accepted and closed:
> `Signals.data_provider_domains_complete` defaults to `True` and fails the schema's
> `dependencies` rule at boot. This is that bug 867 times, derived rather than found by
> hand.
>
> **Why it matters beyond validation**
>
> Tests written against these classes encode the defect. We measured 72 of your own test
> functions that construct one of these classes without the field and rely on the default to
> fill it in; against any implementation that honours the schema they cannot pass. The list
> and the per-pair derivation are available if useful.

---

## What this means for the two rows

For **eknd**: the named, derived set it asked for exists, is attributed, and is now ACTED ON —
72 tests declined with a reason each, upstream's suite untouched. The pass figure can be read
as "every test that grades the protocol", with 18,157 and 17,900 as the two denominators and
the 257-item difference itemised.

For **0z0u**: the measurement stands unchanged and gains the attribution. No emitter change is
owed by this row — 0 of the 867 is ours — and the one thing it does turn up on our side is the
24 collapsed-disjunction positions above, which is a separate row and not this one.

And the sentence `survey/structural_signature.RELAXATIONS['const-default']` states is still
refuted exactly as 0z0u says: its stated cost of "none that can be named" is true of the
property's admissible set and false of the object's, and **477 of the 867** are that case.

---

## The 867, named

The `the document states` column is the instrument's own emitted value, quoted verbatim so
this table and what `--attribute` writes cannot disagree.

Every pair, with the document and pointer it is read at. `whose` is the attribution above;
`kind` is the set's own; `ours` is what our emitted class at the same position does with the
same field. Re-derivable in 30 s with `--attribute <path>`, which writes these as a TSV.

| whose | kind | upstream class | field | the node it is read at | upstream's default | the document states | ours |
|---|---|---|---|---|---|---|---|
| THEIRS | collapsed-disjunction | `brand.search_brands_response.SearchBrandsResponse` | `brands` | `brand/search-brands-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `brand.search_brands_response.SearchBrandsResponse` | `errors` | `brand/search-brands-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.assets.published_post_asset.PublishedPostAsset` | `platform_post_id` | `core/assets/published-post-asset.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.assets.published_post_asset.PublishedPostAsset` | `post_url` | `core/assets/published-post-asset.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.attestation_evaluation.ActionBinding` | `action_digest` | `core/attestation-evaluation.json#/properties/action_binding` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.attestation_evaluation.ActionBinding` | `action_id` | `core/attestation-evaluation.json#/properties/action_binding` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.attestation_reference.AttestationReference` | `embedded_credential` | `core/attestation-reference.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.attestation_reference.AttestationReference` | `locator` | `core/attestation-reference.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.audience_evidence.AttestationRef` | `embedded_credential` | `core/audience-evidence.json#/properties/attestation_refs/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_evidence.AttestationRef` | `locator` | `core/audience-evidence.json#/properties/attestation_refs/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_member.AudienceMember` | `hashed_email` | `core/audience-member.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.audience_member.AudienceMember` | `hashed_phone` | `core/audience-member.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.audience_member.AudienceMember` | `uids` | `core/audience-member.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector1` | `signal_id` | `core/audience-selector.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector1` | `signal_ref` | `core/audience-selector.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector2` | `signal_id` | `core/audience-selector.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector2` | `signal_ref` | `core/audience-selector.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector3` | `signal_id` | `core/audience-selector.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.audience_selector.AudienceSelector3` | `signal_ref` | `core/audience-selector.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.brand_ref.DataSubjectContestation` | `email` | `core/brand-ref.json#/properties/data_subject_contestation` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.brand_ref.DataSubjectContestation` | `url` | `core/brand-ref.json#/properties/data_subject_contestation` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.budget_allocation.TargetFrequency` | `max` | `core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items/allOf/0/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.budget_allocation.TargetFrequency` | `min` | `core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items/allOf/0/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.budget_range.BudgetRange` | `max` | `core/budget-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.budget_range.BudgetRange` | `min` | `core/budget-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.canonical_forecast_point.Viewability` | `standard` | `core/canonical-forecast-point.json#/properties/viewability` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.canonical_optimization_goal.TargetFrequency` | `max` | `core/canonical-optimization-goal.json#/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.canonical_optimization_goal.TargetFrequency` | `min` | `core/canonical-optimization-goal.json#/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.canonical_product.PublisherProperty7` | `publisher_domain` | `core/canonical-product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.canonical_product.PublisherProperty7` | `publisher_domains` | `core/canonical-product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.canonical_proposal.TotalBudgetGuidance` | `max` | `core/canonical-proposal.json#/properties/total_budget_guidance` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.canonical_proposal.TotalBudgetGuidance` | `min` | `core/canonical-proposal.json#/properties/total_budget_guidance` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.canonical_proposal.TotalBudgetGuidance` | `recommended` | `core/canonical-proposal.json#/properties/total_budget_guidance` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.catchment.Catchment` | `geometry` | `core/catchment.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.catchment.Catchment` | `radius` | `core/catchment.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.catchment.Catchment` | `transport_mode` | `core/catchment.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.catchment.Catchment` | `travel_time` | `core/catchment.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.collection_distribution.CollectionDistribution` | `identifiers` | `core/collection-distribution.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.collection_distribution.CollectionDistribution` | `property_ids` | `core/collection-distribution.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.demographic_age_range.DemographicAgeRange` | `max` | `core/demographic-age-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.demographic_age_range.DemographicAgeRange` | `min` | `core/demographic-age-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.demographic_reporting_capability.DemographicReportingCapability` | `age` | `core/demographic-reporting-capability.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.demographic_reporting_capability.DemographicReportingCapability` | `demographic_systems` | `core/demographic-reporting-capability.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.demographic_targeting_intent.Age` | `max` | `core/demographic-targeting-intent.json#/properties/age` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.demographic_targeting_intent.Age` | `min` | `core/demographic-targeting-intent.json#/properties/age` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.forecast_point.Viewability` | `standard` | `core/forecast-point.json#/properties/viewability` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.forecast_range.ForecastRange` | `high` | `core/forecast-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.forecast_range.ForecastRange` | `low` | `core/forecast-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.forecast_range.ForecastRange` | `mid` | `core/forecast-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.forecast_rate_range.ForecastRateRange` | `high` | `core/forecast-rate-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.forecast_rate_range.ForecastRateRange` | `low` | `core/forecast-rate-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.forecast_rate_range.ForecastRateRange` | `mid` | `core/forecast-rate-range.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `max_impressions_constraints` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `mutable_fields` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `supported_control_modes` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `supported_per_units` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `suppression_constraints` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_constraints.FrequencyCapConstraints` | `window_constraints` | `core/frequency-cap-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_impression_constraints.FrequencyCapImpressionConstraints` | `allowed_values` | `core/frequency-cap-impression-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_impression_constraints.FrequencyCapImpressionConstraints` | `maximum` | `core/frequency-cap-impression-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap_impression_constraints.FrequencyCapImpressionConstraints` | `minimum` | `core/frequency-cap-impression-constraints.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap.FrequencyCap` | `max_impressions` | `core/frequency-cap.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap.FrequencyCap` | `suppress` | `core/frequency-cap.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.frequency_cap.FrequencyCap` | `suppress_minutes` | `core/frequency-cap.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.get_geo_place_resolution_request.GetGeographicPlaceResolutionRequest` | `q` | `core/get-geo-place-resolution-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.get_geo_place_resolution_request.GetGeographicPlaceResolutionRequest` | `value` | `core/get-geo-place-resolution-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_capability.MediaBuyFrequencyCapCapability` | `mutable_fields` | `core/media-buy-frequency-cap-capability.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_capability.MediaBuyFrequencyCapCapability` | `suppression_constraints` | `core/media-buy-frequency-cap-capability.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `max_impressions_constraints` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `mutable_fields` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `supported_control_modes` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `supported_per_units` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `suppression_constraints` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap_support.MediaBuyFrequencyCapSupport` | `window_constraints` | `core/media-buy-frequency-cap-support.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap.MediaBuyFrequencyCap` | `suppress` | `core/media-buy-frequency-cap.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.media_buy_frequency_cap.MediaBuyFrequencyCap` | `suppress_minutes` | `core/media-buy-frequency-cap.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.optimization_goal.TargetFrequency` | `max` | `core/optimization-goal.json#/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.optimization_goal.TargetFrequency` | `min` | `core/optimization-goal.json#/oneOf/0/properties/target_frequency` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.package_signal_targeting.PackageSignalTargeting7` | `max_value` | `core/package-signal-targeting.json#/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.package_signal_targeting.PackageSignalTargeting7` | `min_value` | `core/package-signal-targeting.json#/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.placement_definition.PlacementDefinition` | `property_ids` | `core/placement-definition.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.placement_definition.PlacementDefinition` | `property_tags` | `core/placement-definition.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_filters.BudgetRange` | `max` | `core/product-filters.json#/properties/budget_range` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_filters.BudgetRange` | `min` | `core/product-filters.json#/properties/budget_range` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `geometry` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `lat` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `lng` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `radius` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `transport_mode` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.GeoProximityItem` | `travel_time` | `core/product-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.product_filters.RequiredVendorMetric` | `metric_id` | `core/product-filters.json#/properties/required_vendor_metrics/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.RequiredVendorMetric` | `vendor` | `core/product-filters.json#/properties/required_vendor_metrics/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem5` | `signal_id` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem5` | `signal_ref` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem6` | `signal_id` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem6` | `signal_ref` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem7` | `signal_id` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_filters.SignalTargetingItem7` | `signal_ref` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `geometry` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `lat` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `lng` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `radius` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `transport_mode` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.GeoProximityItem` | `travel_time` | `core/product-offer-filters.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.RequiredVendorMetric` | `metric_id` | `core/product-offer-filters.json#/properties/required_vendor_metrics/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product_offer_filters.RequiredVendorMetric` | `vendor` | `core/product-offer-filters.json#/properties/required_vendor_metrics/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.product.PublisherProperty87` | `publisher_domain` | `core/product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.product.PublisherProperty87` | `publisher_domains` | `core/product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.publisher_property_selector.PublisherPropertySelector1` | `publisher_domain` | `core/publisher-property-selector.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.publisher_property_selector.PublisherPropertySelector1` | `publisher_domains` | `core/publisher-property-selector.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.publisher_property_selector.PublisherPropertySelector3` | `publisher_domain` | `core/publisher-property-selector.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.publisher_property_selector.PublisherPropertySelector3` | `publisher_domains` | `core/publisher-property-selector.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.rights_attestation_evaluation.Reference` | `embedded_credential` | `core/rights-attestation-evaluation.json#/properties/reference` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.rights_attestation_evaluation.Reference` | `locator` | `core/rights-attestation-evaluation.json#/properties/reference` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.rights_constraint.AttestationRef` | `embedded_credential` | `core/rights-constraint.json#/properties/attestation_refs/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.rights_constraint.AttestationRef` | `locator` | `core/rights-constraint.json#/properties/attestation_refs/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_definition_enrichment.Channel` | `email` | `core/signal-definition-enrichment.json#/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.signal_definition_enrichment.Channel` | `url` | `core/signal-definition-enrichment.json#/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.signal_definition.Channel` | `email` | `core/signal-definition.json#/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_definition.Channel` | `url` | `core/signal-definition.json#/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting_expression.SignalTargetingExpression3` | `max_value` | `core/signal-targeting-expression.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting_expression.SignalTargetingExpression3` | `min_value` | `core/signal-targeting-expression.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting1` | `signal_id` | `core/signal-targeting.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting1` | `signal_ref` | `core/signal-targeting.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting2` | `signal_id` | `core/signal-targeting.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting2` | `signal_ref` | `core/signal-targeting.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting3` | `signal_id` | `core/signal-targeting.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.signal_targeting.SignalTargeting3` | `signal_ref` | `core/signal-targeting.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `geometry` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `lat` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `lng` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `radius` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `transport_mode` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_input.GeoProximityItem` | `travel_time` | `core/targeting-input.json#/properties/geo_proximity/anyOf/0/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_requirements.GeoProximity` | `geometry` | `core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_requirements.GeoProximity` | `radius` | `core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_requirements.GeoProximity` | `transport_modes` | `core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_requirements.GeoProximity` | `travel_time` | `core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_support.GeoProximity` | `geometry` | `core/targeting-overlay-support.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_support.GeoProximity` | `radius` | `core/targeting-overlay-support.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_support.GeoProximity` | `transport_modes` | `core/targeting-overlay-support.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting_overlay_support.GeoProximity` | `travel_time` | `core/targeting-overlay-support.json#/properties/geo_proximity/anyOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `geometry` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `lat` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `lng` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `radius` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `transport_mode` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.targeting.GeoProximityItem` | `travel_time` | `core/targeting.json#/properties/geo_proximity/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `core.transformer.Transformer` | `output_capability_ids` | `core/transformer.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.transformer.Transformer` | `output_format_ids` | `core/transformer.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `click_id` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `client_ip` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `client_user_agent` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `hashed_email` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `hashed_phone` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.user_match.UserMatch` | `uids` | `core/user-match.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.webhook_challenge_response.WebhookChallengeResponse` | `challenge` | `core/webhook-challenge-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.webhook_challenge_response.WebhookChallengeResponse` | `token` | `core/webhook-challenge-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Signal` | `signal_id` | `core/wholesale-feed-event.json#/$defs/signal` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Signal` | `signal_ref` | `core/wholesale-feed-event.json#/$defs/signal` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload17` | `canonical_product` | `core/wholesale-feed-event.json#/oneOf/0/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload17` | `product` | `core/wholesale-feed-event.json#/oneOf/0/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload18` | `canonical_product` | `core/wholesale-feed-event.json#/oneOf/1/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload18` | `product` | `core/wholesale-feed-event.json#/oneOf/1/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload` | `canonical_pricing_options` | `core/wholesale-feed-event.json#/oneOf/2/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `core.wholesale_feed_event.Payload` | `pricing_options` | `core/wholesale-feed-event.json#/oneOf/2/properties/payload` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `creative.list_creatives_response.Creative` | `format_id` | `creative/list-creatives-response.json#/properties/creatives/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `creative.list_creatives_response.Creative` | `format_kind` | `creative/list-creatives-response.json#/properties/creatives/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `creative.preview_creative_request.Request` | `creative_id` | `creative/preview-creative-request.json#/properties/requests/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `creative.preview_creative_request.Request` | `creative_manifest` | `creative/preview-creative-request.json#/properties/requests/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `creative.sync_creatives_request.Creative` | `format_id` | `creative/sync-creatives-request.json#/properties/creatives/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `creative.sync_creatives_request.Creative` | `format_kind` | `creative/sync-creatives-request.json#/properties/creatives/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params2` | `height` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/1/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params2` | `sizes` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/1/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params2` | `width` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/1/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `height` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `height_range` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `viewport_height_percent` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `width` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `width_mode` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Breakpoint` | `width_range` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/12/properties/params/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params3` | `height` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/2/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params3` | `sizes` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/2/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.coordinated_placements.Params3` | `width` | `formats/canonical/coordinated_placements.json#/properties/components/items/anyOf/1/oneOf/2/properties/params` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `height` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `height_range` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `viewport_height_percent` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `width` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `width_mode` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `formats.canonical.seller_rendered_stateful_display.Breakpoint` | `width_range` | `formats/canonical/seller_rendered_stateful_display.json#/properties/states/items/properties/breakpoints/items` | `null` | nothing (required by some arm) | default=null |
| THEIRS | collapsed-disjunction | `governance.check_governance_response.ActionBinding` | `action_digest` | `governance/check-governance-response.json#/properties/runtime_attestation_evaluations/items/allOf/0/properties/action_binding` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.acceptance_policy_catalog.AcceptancePolicyCatalog` | `profiles` | `media-buy/acceptance-policy-catalog.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.acceptance_policy_catalog.AcceptancePolicyCatalog` | `registry_profiles` | `media-buy/acceptance-policy-catalog.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.acceptance_policy_profile.Scope` | `jurisdiction_groups` | `media-buy/acceptance-policy-profile.json#/properties/scope` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.acceptance_policy_profile.Scope` | `jurisdictions` | `media-buy/acceptance-policy-profile.json#/properties/scope` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.build_creative_request.BuildCreativeRequest` | `refine_from_build_variant_id` | `media-buy/build-creative-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.build_creative_request.BuildCreativeRequest` | `target_capability_ids` | `media-buy/build-creative-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.build_creative_request.BuildCreativeRequest` | `target_format_id` | `media-buy/build-creative-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.build_creative_request.BuildCreativeRequest` | `target_format_ids` | `media-buy/build-creative-request.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.build_creative_response.Creative` | `variants` | `media-buy/build-creative-response.json#/oneOf/2/properties/creatives/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints1` | `max_delta_amount` | `media-buy/change-term-constraints.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints1` | `max_delta_percent` | `media-buy/change-term-constraints.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints1` | `max_result_amount` | `media-buy/change-term-constraints.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints1` | `min_result_amount` | `media-buy/change-term-constraints.json#/oneOf/0` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints2` | `earliest_result` | `media-buy/change-term-constraints.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints2` | `latest_result` | `media-buy/change-term-constraints.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints2` | `max_change` | `media-buy/change-term-constraints.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints2` | `minimum_notice` | `media-buy/change-term-constraints.json#/oneOf/1` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints3` | `max_additions` | `media-buy/change-term-constraints.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints3` | `max_removals` | `media-buy/change-term-constraints.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints3` | `max_result_count` | `media-buy/change-term-constraints.json#/oneOf/2` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints4` | `earliest_effective_at` | `media-buy/change-term-constraints.json#/oneOf/3` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints4` | `latest_effective_at` | `media-buy/change-term-constraints.json#/oneOf/3` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints4` | `minimum_notice` | `media-buy/change-term-constraints.json#/oneOf/3` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.decline_proposals_response.DeclineProposalsResponse1` | `status` | `media-buy/decline-proposals-response.json#` | `submitted` | const="submitted" (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.decline_proposals_response.DeclineProposalsResponse1` | `task_id` | `media-buy/decline-proposals-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.outcome_target.OutcomeTarget` | `cost_per` | `media-buy/outcome-target.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.outcome_target.OutcomeTarget` | `volume` | `media-buy/outcome-target.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.proposal_budget_constraint.ProposalBudgetConstraint` | `max` | `media-buy/proposal-budget-constraint.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.proposal_budget_constraint.ProposalBudgetConstraint` | `min` | `media-buy/proposal-budget-constraint.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.proposal_refinement.Flight` | `end_no_earlier_than` | `media-buy/proposal-refinement.json#/properties/constraints/properties/flight` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.proposal_refinement.Flight` | `start_no_later_than` | `media-buy/proposal-refinement.json#/properties/constraints/properties/flight` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `media_buy.refine_proposals_response.RefineProposalsResponse1` | `task_id` | `media-buy/refine-proposals-response.json#` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.refine_proposals_response.TotalBudgetGuidance` | `max` | `media-buy/refine-proposals-response.json#/definitions/Shared8/properties/total_budget_guidance` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.refine_proposals_response.TotalBudgetGuidance` | `min` | `media-buy/refine-proposals-response.json#/definitions/Shared8/properties/total_budget_guidance` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `media_buy.refine_proposals_response.TotalBudgetGuidance` | `recommended` | `media-buy/refine-proposals-response.json#/definitions/Shared8/properties/total_budget_guidance` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `pricing_options.price_breakdown.Adjustment` | `amount` | `pricing-options/price-breakdown.json#/properties/adjustments/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `pricing_options.price_breakdown.Adjustment` | `rate` | `pricing-options/price-breakdown.json#/properties/adjustments/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `bundled.protocol.get_adcp_capabilities_response.DataSubjectContestation` | `email` | `protocol/get-adcp-capabilities-response.json#/definitions/Shared113` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `bundled.protocol.get_adcp_capabilities_response.DataSubjectContestation` | `url` | `protocol/get-adcp-capabilities-response.json#/definitions/Shared113` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `bundled.protocol.get_adcp_capabilities_response.MaxImpressionsConstraints` | `allowed_values` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/aggregate_frequency_capping/allOf/0/properties/max_impressions_constraints` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `bundled.protocol.get_adcp_capabilities_response.MaxImpressionsConstraints` | `maximum` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/aggregate_frequency_capping/allOf/0/properties/max_impressions_constraints` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `bundled.protocol.get_adcp_capabilities_response.MaxImpressionsConstraints` | `minimum` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/aggregate_frequency_capping/allOf/0/properties/max_impressions_constraints` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `signals.get_signals_response.Signal` | `signal_id` | `signals/get-signals-response.json#/properties/signals/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `signals.get_signals_response.Signal` | `signal_ref` | `signals/get-signals-response.json#/properties/signals/items` | `null` | nothing (required by some arm) | carried-by-a-rule |
| THEIRS | collapsed-disjunction | `signals.get_signals_response.Channel` | `email` | `signals/get-signals-response.json#/properties/signals/items/allOf/1/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | collapsed-disjunction | `signals.get_signals_response.Channel` | `url` | `signals/get-signals-response.json#/properties/signals/items/allOf/1/properties/data_subject_rights/properties/channels/items` | `null` | nothing (required by some arm) | not-declared-here |
| THEIRS | const-restated | `brand.acquire_rights_response.AcquireRightsResponse1` | `rights_status` | `brand/acquire-rights-response.json#/oneOf/0` | `acquired` | const="acquired" | required |
| THEIRS | const-restated | `brand.acquire_rights_response.AcquireRightsResponse2` | `rights_status` | `brand/acquire-rights-response.json#/oneOf/1` | `pending_approval` | const="pending_approval" | required |
| THEIRS | const-restated | `brand.acquire_rights_response.AcquireRightsResponse3` | `rights_status` | `brand/acquire-rights-response.json#/oneOf/2` | `rejected` | const="rejected" | required |
| THEIRS | const-restated | `brand.creative_approval_response.CreativeApprovalResponse1` | `approval_status` | `brand/creative-approval-response.json#/oneOf/0` | `approved` | const="approved" | required |
| THEIRS | const-restated | `brand.creative_approval_response.CreativeApprovalResponse2` | `approval_status` | `brand/creative-approval-response.json#/oneOf/1` | `rejected` | const="rejected" | required |
| THEIRS | const-restated | `brand.creative_approval_response.CreativeApprovalResponse3` | `approval_status` | `brand/creative-approval-response.json#/oneOf/2` | `pending_review` | const="pending_review" | required |
| THEIRS | const-restated | `collection.base_collection_source.BaseCollectionSource1` | `selection_type` | `collection/base-collection-source.json#/oneOf/0` | `distribution_ids` | const="distribution_ids" | required |
| THEIRS | const-restated | `collection.base_collection_source.BaseCollectionSource2` | `selection_type` | `collection/base-collection-source.json#/oneOf/1` | `publisher_collections` | const="publisher_collections" | required |
| THEIRS | const-restated | `collection.base_collection_source.BaseCollectionSource3` | `selection_type` | `collection/base-collection-source.json#/oneOf/2` | `publisher_genres` | const="publisher_genres" | required |
| THEIRS | const-restated | `collection.collection_list_changed_webhook.CollectionListChangedWebhook` | `event` | `collection/collection-list-changed-webhook.json#` | `collection_list_changed` | const="collection_list_changed" | not-declared-here |
| THEIRS | const-restated | `content_standards.artifact.AssetAccess1` | `method` | `content-standards/artifact.json#/$defs/asset_access/oneOf/0` | `bearer_token` | const="bearer_token" | required |
| THEIRS | const-restated | `content_standards.artifact.AssetAccess2` | `method` | `content-standards/artifact.json#/$defs/asset_access/oneOf/1` | `service_account` | const="service_account" | required |
| THEIRS | const-restated | `content_standards.artifact.AssetAccess3` | `method` | `content-standards/artifact.json#/$defs/asset_access/oneOf/2` | `signed_url` | const="signed_url" | required |
| THEIRS | const-restated | `content_standards.artifact.Assets1` | `type` | `content-standards/artifact.json#/properties/assets/items/oneOf/0` | `text` | const="text" | required |
| THEIRS | const-restated | `content_standards.artifact.Assets2` | `type` | `content-standards/artifact.json#/properties/assets/items/oneOf/1` | `image` | const="image" | required |
| THEIRS | const-restated | `content_standards.artifact.Assets3` | `type` | `content-standards/artifact.json#/properties/assets/items/oneOf/2` | `video` | const="video" | required |
| THEIRS | const-restated | `content_standards.artifact.Assets4` | `type` | `content-standards/artifact.json#/properties/assets/items/oneOf/3` | `audio` | const="audio" | required |
| THEIRS | const-restated | `core.account_change_recorded_webhook.AccountChangeRecordedWebhook` | `notification_type` | `core/account-change-recorded-webhook.json#` | `account.change_recorded` | const="account.change_recorded" | not-declared-here |
| THEIRS | const-restated | `core.account_identity_change_preview.AccountIdentityChangePreview3` | `outcome` | `core/account-identity-change-preview.json#/oneOf/2` | `blocked` | const="blocked" | required |
| THEIRS | const-restated | `core.account_identity_change.AccountIdentityChange1` | `status` | `core/account-identity-change.json#/oneOf/0` | `pending_approval` | const="pending_approval" | required |
| THEIRS | const-restated | `core.account_identity_change.AccountIdentityChange2` | `status` | `core/account-identity-change.json#/oneOf/1` | `rejected` | const="rejected" | required |
| THEIRS | const-restated | `core.account_status_changed_webhook.AccountStatusChangedWebhook` | `notification_type` | `core/account-status-changed-webhook.json#` | `account.status_changed` | const="account.status_changed" | not-declared-here |
| THEIRS | const-restated | `core.activation_key.ActivationKey1` | `type` | `core/activation-key.json#/oneOf/0` | `segment_id` | const="segment_id" | required |
| THEIRS | const-restated | `core.activation_key.ActivationKey2` | `type` | `core/activation-key.json#/oneOf/1` | `key_value` | const="key_value" | required |
| THEIRS | const-restated | `core.agent_encryption_key.AgentEncryptionKey` | `crv` | `core/agent-encryption-key.json#` | `X25519` | const="X25519" | not-declared-here |
| THEIRS | const-restated | `core.agent_encryption_key.AgentEncryptionKey` | `kty` | `core/agent-encryption-key.json#` | `OKP` | const="OKP" | not-declared-here |
| THEIRS | const-restated | `core.agent_encryption_key.AgentEncryptionKey` | `use` | `core/agent-encryption-key.json#` | `enc` | const="enc" | not-declared-here |
| THEIRS | const-restated | `core.agent_reporting_destination.AgentReportingDestination1` | `pattern` | `core/agent-reporting-destination.json#/oneOf/0` | `file_transfer` | const="file_transfer" | required |
| THEIRS | const-restated | `core.agent_reporting_destination.AgentReportingDestination2` | `pattern` | `core/agent-reporting-destination.json#/oneOf/1` | `warehouse_materialization` | const="warehouse_materialization" | required |
| THEIRS | const-restated | `core.agent_reporting_destination.AgentReportingDestination3` | `pattern` | `core/agent-reporting-destination.json#/oneOf/2` | `dataset_share` | const="dataset_share" | required |
| THEIRS | const-restated | `core.agent_webhook_challenge.AgentWebhookChallenge` | `scope` | `core/agent-webhook-challenge.json#` | `agent` | const="agent" | not-declared-here |
| THEIRS | const-restated | `core.agent_webhook_challenge.AgentWebhookChallenge` | `type` | `core/agent-webhook-challenge.json#` | `webhook.challenge` | const="webhook.challenge" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.ImageAsset` | `asset_type` | `core/assets/asset-union.json#/definitions/Shared0` | `image` | const="image" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.VideoAsset` | `asset_type` | `core/assets/asset-union.json#/definitions/Shared1` | `video` | const="video" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.MacroTranslationTarget` | `next_operation` | `core/assets/asset-union.json#/definitions/Shared31/properties/translation_target` | `resolve_value` | const="resolve_value" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.WebhookAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/10` | `webhook` | const="webhook" | required |
| THEIRS | const-restated | `core.assets.asset_union.CssAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/11` | `css` | const="css" | required |
| THEIRS | const-restated | `core.assets.asset_union.DaastAsset1` | `asset_type` | `core/assets/asset-union.json#/oneOf/12/oneOf/0` | `daast` | const="daast" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DaastAsset1` | `delivery_type` | `core/assets/asset-union.json#/oneOf/12/oneOf/0` | `url` | const="url" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DaastAsset2` | `asset_type` | `core/assets/asset-union.json#/oneOf/12/oneOf/1` | `daast` | const="daast" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DaastAsset2` | `delivery_type` | `core/assets/asset-union.json#/oneOf/12/oneOf/1` | `inline` | const="inline" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.MarkdownAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/13` | `markdown` | const="markdown" | required |
| THEIRS | const-restated | `core.assets.asset_union.BriefAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/14` | `brief` | const="brief" | required |
| THEIRS | const-restated | `core.assets.asset_union.CatalogAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/15` | `catalog` | const="catalog" | required |
| THEIRS | const-restated | `core.assets.asset_union.CardAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/17` | `card` | const="card" | required |
| THEIRS | const-restated | `core.assets.asset_union.UrlAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/17/properties/landing_page_url` | `url` | const="url" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.PixelTrackerAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/18` | `pixel_tracker` | const="pixel_tracker" | required |
| THEIRS | const-restated | `core.assets.asset_union.VastTrackerAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/19` | `vast_tracker` | const="vast_tracker" | required |
| THEIRS | const-restated | `core.assets.asset_union.AudioAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/2` | `audio` | const="audio" | required |
| THEIRS | const-restated | `core.assets.asset_union.DaastTrackerAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/20` | `daast_tracker` | const="daast_tracker" | required |
| THEIRS | const-restated | `core.assets.asset_union.VastAsset1` | `asset_type` | `core/assets/asset-union.json#/oneOf/3/oneOf/0` | `vast` | const="vast" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.VastAsset1` | `delivery_type` | `core/assets/asset-union.json#/oneOf/3/oneOf/0` | `url` | const="url" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.VastAsset2` | `asset_type` | `core/assets/asset-union.json#/oneOf/3/oneOf/1` | `vast` | const="vast" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.VastAsset2` | `delivery_type` | `core/assets/asset-union.json#/oneOf/3/oneOf/1` | `inline` | const="inline" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset1` | `asset_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/0` | `display_tag` | const="display_tag" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset1` | `delivery_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/0` | `tag_url` | const="tag_url" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset2` | `asset_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/1` | `display_tag` | const="display_tag" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset2` | `delivery_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/1` | `inline_markup` | const="inline_markup" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset3` | `asset_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/2` | `display_tag` | const="display_tag" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.DisplayTagAsset3` | `delivery_type` | `core/assets/asset-union.json#/oneOf/4/oneOf/2` | `paired_redirect` | const="paired_redirect" | not-declared-here |
| THEIRS | const-restated | `core.assets.asset_union.TextAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/5` | `text` | const="text" | required |
| THEIRS | const-restated | `core.assets.asset_union.HtmlAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/7` | `html` | const="html" | required |
| THEIRS | const-restated | `core.assets.asset_union.JavascriptAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/8` | `javascript` | const="javascript" | required |
| THEIRS | const-restated | `core.assets.asset_union.ZipAsset` | `asset_type` | `core/assets/asset-union.json#/oneOf/9` | `zip` | const="zip" | required |
| THEIRS | const-restated | `core.assets.audio_asset.AudioAsset` | `asset_type` | `core/assets/audio-asset.json#` | `audio` | const="audio" | not-declared-here |
| THEIRS | const-restated | `core.assets.brief_asset.BriefAsset` | `asset_type` | `core/assets/brief-asset.json#` | `brief` | const="brief" | not-declared-here |
| THEIRS | const-restated | `core.assets.card_asset.CardAsset` | `asset_type` | `core/assets/card-asset.json#` | `card` | const="card" | not-declared-here |
| THEIRS | const-restated | `core.assets.catalog_asset.CatalogAsset` | `asset_type` | `core/assets/catalog-asset.json#` | `catalog` | const="catalog" | not-declared-here |
| THEIRS | const-restated | `core.assets.css_asset.CssAsset` | `asset_type` | `core/assets/css-asset.json#` | `css` | const="css" | not-declared-here |
| THEIRS | const-restated | `core.assets.daast_asset.DaastAsset3` | `asset_type` | `core/assets/daast-asset.json#/oneOf/0` | `daast` | const="daast" | required |
| THEIRS | const-restated | `core.assets.daast_asset.DaastAsset3` | `delivery_type` | `core/assets/daast-asset.json#/oneOf/0` | `url` | const="url" | required |
| THEIRS | const-restated | `core.assets.daast_asset.DaastAsset4` | `asset_type` | `core/assets/daast-asset.json#/oneOf/1` | `daast` | const="daast" | required |
| THEIRS | const-restated | `core.assets.daast_asset.DaastAsset4` | `delivery_type` | `core/assets/daast-asset.json#/oneOf/1` | `inline` | const="inline" | required |
| THEIRS | const-restated | `core.assets.daast_tracker_asset.DaastTrackerAsset` | `asset_type` | `core/assets/daast-tracker-asset.json#` | `daast_tracker` | const="daast_tracker" | not-declared-here |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset4` | `asset_type` | `core/assets/display-tag-asset.json#/oneOf/0` | `display_tag` | const="display_tag" | required |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset4` | `delivery_type` | `core/assets/display-tag-asset.json#/oneOf/0` | `tag_url` | const="tag_url" | required |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset5` | `asset_type` | `core/assets/display-tag-asset.json#/oneOf/1` | `display_tag` | const="display_tag" | required |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset5` | `delivery_type` | `core/assets/display-tag-asset.json#/oneOf/1` | `inline_markup` | const="inline_markup" | required |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset6` | `asset_type` | `core/assets/display-tag-asset.json#/oneOf/2` | `display_tag` | const="display_tag" | required |
| THEIRS | const-restated | `core.assets.display_tag_asset.DisplayTagAsset6` | `delivery_type` | `core/assets/display-tag-asset.json#/oneOf/2` | `paired_redirect` | const="paired_redirect" | required |
| THEIRS | const-restated | `core.assets.html_asset.HtmlAsset` | `asset_type` | `core/assets/html-asset.json#` | `html` | const="html" | not-declared-here |
| THEIRS | const-restated | `core.assets.image_asset.ImageAsset` | `asset_type` | `core/assets/image-asset.json#` | `image` | const="image" | not-declared-here |
| THEIRS | const-restated | `core.assets.javascript_asset.JavascriptAsset` | `asset_type` | `core/assets/javascript-asset.json#` | `javascript` | const="javascript" | not-declared-here |
| THEIRS | const-restated | `core.assets.markdown_asset.MarkdownAsset` | `asset_type` | `core/assets/markdown-asset.json#` | `markdown` | const="markdown" | not-declared-here |
| THEIRS | const-restated | `core.assets.pixel_tracker_asset.PixelTrackerAsset` | `asset_type` | `core/assets/pixel-tracker-asset.json#` | `pixel_tracker` | const="pixel_tracker" | not-declared-here |
| THEIRS | const-restated | `core.assets.published_post_asset.PublishedPostAsset` | `asset_type` | `core/assets/published-post-asset.json#` | `published_post` | const="published_post" | not-declared-here |
| THEIRS | const-restated | `core.assets.text_asset.TextAsset` | `asset_type` | `core/assets/text-asset.json#` | `text` | const="text" | not-declared-here |
| THEIRS | const-restated | `core.assets.url_asset.UrlAsset` | `asset_type` | `core/assets/url-asset.json#` | `url` | const="url" | not-declared-here |
| THEIRS | const-restated | `core.assets.vast_asset.VastAsset3` | `asset_type` | `core/assets/vast-asset.json#/oneOf/0` | `vast` | const="vast" | required |
| THEIRS | const-restated | `core.assets.vast_asset.VastAsset3` | `delivery_type` | `core/assets/vast-asset.json#/oneOf/0` | `url` | const="url" | required |
| THEIRS | const-restated | `core.assets.vast_asset.VastAsset4` | `asset_type` | `core/assets/vast-asset.json#/oneOf/1` | `vast` | const="vast" | required |
| THEIRS | const-restated | `core.assets.vast_asset.VastAsset4` | `delivery_type` | `core/assets/vast-asset.json#/oneOf/1` | `inline` | const="inline" | required |
| THEIRS | const-restated | `core.assets.vast_tracker_asset.VastTrackerAsset` | `asset_type` | `core/assets/vast-tracker-asset.json#` | `vast_tracker` | const="vast_tracker" | not-declared-here |
| THEIRS | const-restated | `core.assets.video_asset.VideoAsset` | `asset_type` | `core/assets/video-asset.json#` | `video` | const="video" | not-declared-here |
| THEIRS | const-restated | `core.assets.webhook_asset.WebhookAsset` | `asset_type` | `core/assets/webhook-asset.json#` | `webhook` | const="webhook" | not-declared-here |
| THEIRS | const-restated | `core.assets.zip_asset.ZipAsset` | `asset_type` | `core/assets/zip-asset.json#` | `zip` | const="zip" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.creative.get_creative_features_async_response_submitted.GetCreativeFeaturesSubmitted` | `status` | `core/async-response-refs/creative/get-creative-features-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.creative.sync_creatives_async_response_submitted.SyncCreativesSubmitted` | `status` | `core/async-response-refs/creative/sync-creatives-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.accept_proposal_async_response_submitted.AcceptProposalSubmitted` | `status` | `core/async-response-refs/media-buy/accept-proposal-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.build_creative_async_response_submitted.BuildCreativeSubmitted` | `status` | `core/async-response-refs/media-buy/build-creative-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.buy_products_async_response_submitted.BuyProductsSubmitted` | `status` | `core/async-response-refs/media-buy/buy-products-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.control_media_buy_async_response_submitted.ControlMediaBuySubmitted` | `status` | `core/async-response-refs/media-buy/control-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.create_media_buy_async_response_submitted.CreateMediaBuySubmitted` | `status` | `core/async-response-refs/media-buy/create-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.decline_proposals_async_response_submitted.DeclineProposalsSubmitted` | `status` | `core/async-response-refs/media-buy/decline-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.get_products_async_response_submitted.GetProductsSubmitted` | `status` | `core/async-response-refs/media-buy/get-products-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.refine_proposals_async_response_submitted.RefineProposalsSubmitted` | `status` | `core/async-response-refs/media-buy/refine-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.request_proposals_async_response_submitted.RequestProposalsSubmitted` | `status` | `core/async-response-refs/media-buy/request-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.sync_catalogs_async_response_submitted.SyncCatalogsSubmitted` | `status` | `core/async-response-refs/media-buy/sync-catalogs-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.media_buy.update_media_buy_async_response_submitted.UpdateMediaBuySubmitted` | `status` | `core/async-response-refs/media-buy/update-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.async_response_refs.signals.get_signals_async_response_submitted.GetSignalsSubmitted` | `status` | `core/async-response-refs/signals/get-signals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.attestation_issuer.AttestationIssuer1` | `type` | `core/attestation-issuer.json#/oneOf/0` | `brand` | const="brand" | required |
| THEIRS | const-restated | `core.attestation_issuer.AttestationIssuer2` | `type` | `core/attestation-issuer.json#/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.attestation_issuer.AttestationIssuer3` | `type` | `core/attestation-issuer.json#/oneOf/2` | `origin` | const="origin" | required |
| THEIRS | const-restated | `core.attestation_reference.Locator` | `type` | `core/attestation-reference.json#/properties/locator/oneOf/0` | `credential_uri` | const="credential_uri" | required |
| THEIRS | const-restated | `core.attestation_reference.Locator1` | `type` | `core/attestation-reference.json#/properties/locator/oneOf/1` | `issuer_credential_id` | const="issuer_credential_id" | required |
| THEIRS | const-restated | `core.attestation_subject.AttestationSubject1` | `type` | `core/attestation-subject.json#/oneOf/0` | `brand` | const="brand" | required |
| THEIRS | const-restated | `core.attestation_subject.AttestationSubject2` | `type` | `core/attestation-subject.json#/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.attestation_subject.AttestationSubject3` | `type` | `core/attestation-subject.json#/oneOf/2` | `resource` | const="resource" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod1` | `pattern` | `core/audience-activation-method.json#/oneOf/0` | `sync_audiences` | const="sync_audiences" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod2` | `pattern` | `core/audience-activation-method.json#/oneOf/1` | `tmp_identity_match` | const="tmp_identity_match" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod3` | `pattern` | `core/audience-activation-method.json#/oneOf/2` | `file_transfer` | const="file_transfer" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod4` | `pattern` | `core/audience-activation-method.json#/oneOf/3` | `dataset_query` | const="dataset_query" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod5` | `pattern` | `core/audience-activation-method.json#/oneOf/4` | `clean_room` | const="clean_room" | required |
| THEIRS | const-restated | `core.audience_activation_method.AudienceActivationMethod6` | `pattern` | `core/audience-activation-method.json#/oneOf/5` | `platform_distribution` | const="platform_distribution" | required |
| THEIRS | const-restated | `core.audience_evidence_selection.ActionBinding` | `action_type` | `core/audience-evidence-selection.json#/properties/attestation_evaluations/items/properties/evaluation/allOf/0/properties/action_binding` | `https://adcontextprotocol.org/actions/audience-evidence-evaluation` | const="https://adcontextprotocol.org/actions/audience-evidence-evaluation" | not-declared-here |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector1` | `type` | `core/audience-selector.json#/oneOf/0` | `signal` | const="signal" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector1` | `value_type` | `core/audience-selector.json#/oneOf/0` | `binary` | const="binary" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector2` | `type` | `core/audience-selector.json#/oneOf/1` | `signal` | const="signal" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector2` | `value_type` | `core/audience-selector.json#/oneOf/1` | `categorical` | const="categorical" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector3` | `type` | `core/audience-selector.json#/oneOf/2` | `signal` | const="signal" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector3` | `value_type` | `core/audience-selector.json#/oneOf/2` | `numeric` | const="numeric" | required |
| THEIRS | const-restated | `core.audience_selector.AudienceSelector4` | `type` | `core/audience-selector.json#/oneOf/3` | `description` | const="description" | required |
| THEIRS | const-restated | `core.audience_source.AudienceSource1` | `kind` | `core/audience-source.json#/oneOf/0` | `dataset` | const="dataset" | required |
| THEIRS | const-restated | `core.audience_source.AudienceSource2` | `kind` | `core/audience-source.json#/oneOf/1` | `platform_segment` | const="platform_segment" | required |
| THEIRS | const-restated | `core.bidding_policy_capability.MaxBidWithCostPer` | `kind` | `core/bidding-policy-capability.json#/definitions/max_bid_with_cost_per` | `max_bid_with_cost_per` | const="max_bid_with_cost_per" | required |
| THEIRS | const-restated | `core.bidding_policy_capability.MaxBidWithRoas` | `kind` | `core/bidding-policy-capability.json#/definitions/max_bid_with_roas` | `max_bid_with_roas` | const="max_bid_with_roas" | required |
| THEIRS | const-restated | `core.budget_allocation.BudgetAllocation1` | `mode` | `core/budget-allocation.json#/oneOf/0` | `fixed` | const="fixed" | required |
| THEIRS | const-restated | `core.budget_allocation.BudgetAllocation2` | `mode` | `core/budget-allocation.json#/oneOf/1` | `seller_optimized` | const="seller_optimized" | required |
| THEIRS | const-restated | `core.budget_allocation.OptimizationGoal5` | `kind` | `core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items/allOf/0/oneOf/0` | `metric` | const="metric" | not-declared-here |
| THEIRS | const-restated | `core.budget_allocation.OptimizationGoal6` | `kind` | `core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items/allOf/0/oneOf/1` | `event` | const="event" | not-declared-here |
| THEIRS | const-restated | `core.budget_allocation.OptimizationGoal7` | `kind` | `core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items/allOf/0/oneOf/2` | `vendor_metric` | const="vendor_metric" | not-declared-here |
| THEIRS | const-restated | `core.canonical_budget_allocation.CanonicalBudgetAllocation1` | `mode` | `core/canonical-budget-allocation.json#/oneOf/0` | `fixed` | const="fixed" | required |
| THEIRS | const-restated | `core.canonical_budget_allocation.CanonicalBudgetAllocation2` | `mode` | `core/canonical-budget-allocation.json#/oneOf/1` | `seller_optimized` | const="seller_optimized" | required |
| THEIRS | const-restated | `core.canonical_optimization_goal.CanonicalOptimizationGoal1` | `kind` | `core/canonical-optimization-goal.json#/oneOf/0` | `metric` | const="metric" | required |
| THEIRS | const-restated | `core.canonical_optimization_goal.CanonicalOptimizationGoal2` | `kind` | `core/canonical-optimization-goal.json#/oneOf/1` | `event` | const="event" | required |
| THEIRS | const-restated | `core.canonical_optimization_goal.Target10` | `kind` | `core/canonical-optimization-goal.json#/oneOf/1/properties/target` | `maximize_value` | const="maximize_value" | required |
| THEIRS | const-restated | `core.canonical_optimization_goal.CanonicalOptimizationGoal3` | `kind` | `core/canonical-optimization-goal.json#/oneOf/2` | `vendor_metric` | const="vendor_metric" | required |
| THEIRS | const-restated | `core.canonical_product.PublisherProperty6` | `selection_type` | `core/canonical-product.json#/properties/publisher_properties/items/allOf/0/oneOf/1` | `by_id` | const="by_id" | not-declared-here |
| THEIRS | const-restated | `core.canonical_product.PublisherProperty7` | `selection_type` | `core/canonical-product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `by_tag` | const="by_tag" | not-declared-here |
| THEIRS | const-restated | `core.canonical_reporting_commitment.CanonicalReportingCommitment1` | `scope` | `core/canonical-reporting-commitment.json#/oneOf/0` | `standard` | const="standard" | required |
| THEIRS | const-restated | `core.canonical_reporting_commitment.CanonicalReportingCommitment2` | `scope` | `core/canonical-reporting-commitment.json#/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `core.capabilities_changed_webhook.CapabilitiesChangedWebhook` | `notification_type` | `core/capabilities-changed-webhook.json#` | `capabilities.changed` | const="capabilities.changed" | not-declared-here |
| THEIRS | const-restated | `core.catalog_item_reference_not_found_error.CatalogItemReferenceNotFoundError` | `code` | `core/catalog-item-reference-not-found-error.json#` | `REFERENCE_NOT_FOUND` | const="REFERENCE_NOT_FOUND" | not-declared-here |
| THEIRS | const-restated | `core.catalog_item_reference_not_found_error.CatalogItemReferenceNotFoundError` | `message` | `core/catalog-item-reference-not-found-error.json#` | `Catalog item not found` | const="Catalog item not found" | not-declared-here |
| THEIRS | const-restated | `core.catalog_item_reference_not_found_error.CatalogItemReferenceNotFoundError` | `recovery` | `core/catalog-item-reference-not-found-error.json#` | `correctable` | const="correctable" | not-declared-here |
| THEIRS | const-restated | `core.collection_selection.CollectionSelection1` | `mode` | `core/collection-selection.json#/oneOf/0` | `selected` | const="selected" | required |
| THEIRS | const-restated | `core.collection_selection.CollectionSelection2` | `mode` | `core/collection-selection.json#/oneOf/1` | `default` | const="default" | required |
| THEIRS | const-restated | `core.committed_metric.CommittedMetric1` | `scope` | `core/committed-metric.json#/oneOf/0` | `standard` | const="standard" | required |
| THEIRS | const-restated | `core.committed_metric.CommittedMetric2` | `scope` | `core/committed-metric.json#/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `core.compact_task_submitted.CompactTaskSubmitted` | `status` | `core/compact-task-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `core.creative_item.CreativeItem1` | `asset_kind` | `core/creative-item.json#/oneOf/0` | `media` | const="media" | required |
| THEIRS | const-restated | `core.creative_item.CreativeItem2` | `asset_kind` | `core/creative-item.json#/oneOf/1` | `text` | const="text" | required |
| THEIRS | const-restated | `core.creative_localization_readback.CreativeLocalizationReadback` | `locale_matching` | `core/creative-localization-readback.json#` | `rfc4647_lookup` | const="rfc4647_lookup" | not-declared-here |
| THEIRS | const-restated | `core.data_provider_signal_selector.DataProviderSignalSelector1` | `selection_type` | `core/data-provider-signal-selector.json#/oneOf/0` | `all` | const="all" | required |
| THEIRS | const-restated | `core.data_provider_signal_selector.DataProviderSignalSelector2` | `selection_type` | `core/data-provider-signal-selector.json#/oneOf/1` | `by_id` | const="by_id" | required |
| THEIRS | const-restated | `core.data_provider_signal_selector.DataProviderSignalSelector3` | `selection_type` | `core/data-provider-signal-selector.json#/oneOf/2` | `by_tag` | const="by_tag" | required |
| THEIRS | const-restated | `core.delivery_metric_aggregate.DeliveryMetricAggregate2` | `scope` | `core/delivery-metric-aggregate.json#/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `core.demographic_targeting_resolution.Execution` | `type` | `core/demographic-targeting-resolution.json#/properties/execution/oneOf/0` | `continuous_bounds` | const="continuous_bounds" | required |
| THEIRS | const-restated | `core.demographic_targeting_resolution.Execution1` | `type` | `core/demographic-targeting-resolution.json#/properties/execution/oneOf/1` | `enumerated_intervals` | const="enumerated_intervals" | required |
| THEIRS | const-restated | `core.demographic_targeting_resolution.Execution2` | `type` | `core/demographic-targeting-resolution.json#/properties/execution/oneOf/2` | `signals` | const="signals" | required |
| THEIRS | const-restated | `core.deployment.Deployment1` | `type` | `core/deployment.json#/oneOf/0` | `platform` | const="platform" | required |
| THEIRS | const-restated | `core.deployment.Deployment2` | `type` | `core/deployment.json#/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.destination.Destination1` | `type` | `core/destination.json#/oneOf/0` | `platform` | const="platform" | required |
| THEIRS | const-restated | `core.destination.Destination2` | `type` | `core/destination.json#/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.forecast_dimension_audience.AudienceForecastDimension` | `kind` | `core/forecast-dimension-audience.json#` | `audience` | const="audience" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_device_platform.DevicePlatformForecastDimension` | `kind` | `core/forecast-dimension-device-platform.json#` | `device_platform` | const="device_platform" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_device_type.DeviceTypeForecastDimension` | `kind` | `core/forecast-dimension-device-type.json#` | `device_type` | const="device_type" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_geo.GeoForecastDimension` | `kind` | `core/forecast-dimension-geo.json#` | `geo` | const="geo" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_placement.PlacementForecastDimension` | `kind` | `core/forecast-dimension-placement.json#` | `placement` | const="placement" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_signal.SignalForecastDimension` | `kind` | `core/forecast-dimension-signal.json#` | `signal` | const="signal" | not-declared-here |
| THEIRS | const-restated | `core.forecast_dimension_time.TimeForecastDimension` | `kind` | `core/forecast-dimension-time.json#` | `time` | const="time" | not-declared-here |
| THEIRS | const-restated | `core.format.BaseIndividualAsset` | `item_type` | `core/format.json#/$defs/baseIndividualAsset` | `individual` | const="individual" | required |
| THEIRS | const-restated | `core.format.Assets29` | `item_type` | `core/format.json#/properties/assets/items/oneOf/1` | `repeatable_group` | const="repeatable_group" | required |
| THEIRS | const-restated | `core.geo_place_resolver.GeographicPlaceResolver` | `protocol` | `core/geo-place-resolver.json#` | `adcp_geo_place_resolver_v1` | const="adcp_geo_place_resolver_v1" | not-declared-here |
| THEIRS | const-restated | `core.indicators_changed_webhook.IndicatorsChangedWebhook` | `notification_type` | `core/indicators-changed-webhook.json#` | `indicators.changed` | const="indicators.changed" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset2` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/0` | `image` | const="image" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset3` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/1` | `video` | const="video" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset12` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/10` | `webhook` | const="webhook" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset13` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/11` | `css` | const="css" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset15` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/13` | `markdown` | const="markdown" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset16` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/14` | `brief` | const="brief" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset17` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/15` | `catalog` | const="catalog" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset19` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/17` | `card` | const="card" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset8` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/17/properties/landing_page_url` | `url` | const="url" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset20` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/18` | `pixel_tracker` | const="pixel_tracker" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset21` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/19` | `vast_tracker` | const="vast_tracker" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset4` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/2` | `audio` | const="audio" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset22` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/20` | `daast_tracker` | const="daast_tracker" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset7` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/5` | `text` | const="text" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset9` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/7` | `html` | const="html" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset10` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/8` | `javascript` | const="javascript" | not-declared-here |
| THEIRS | const-restated | `core.localized_creative_asset.LocalizedCreativeAsset11` | `asset_type` | `core/localized-creative-asset.json#/allOf/0/oneOf/9` | `zip` | const="zip" | not-declared-here |
| THEIRS | const-restated | `core.macro_translation_target.MacroTranslationTarget` | `next_operation` | `core/macro-translation-target.json#` | `resolve_value` | const="resolve_value" | not-declared-here |
| THEIRS | const-restated | `core.missing_metric.MissingMetric1` | `scope` | `core/missing-metric.json#/oneOf/0` | `standard` | const="standard" | required |
| THEIRS | const-restated | `core.missing_metric.MissingMetric2` | `scope` | `core/missing-metric.json#/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `core.optimization_goal.OptimizationGoal8` | `kind` | `core/optimization-goal.json#/oneOf/0` | `metric` | const="metric" | required |
| THEIRS | const-restated | `core.optimization_goal.OptimizationGoal9` | `kind` | `core/optimization-goal.json#/oneOf/1` | `event` | const="event" | required |
| THEIRS | const-restated | `core.optimization_goal.Target17` | `kind` | `core/optimization-goal.json#/oneOf/1/properties/target/oneOf/2` | `maximize_value` | const="maximize_value" | required |
| THEIRS | const-restated | `core.optimization_goal.OptimizationGoal10` | `kind` | `core/optimization-goal.json#/oneOf/2` | `vendor_metric` | const="vendor_metric" | required |
| THEIRS | const-restated | `core.package_delivery_metric_value.PackageDeliveryMetricValue` | `scope` | `core/package-delivery-metric-value.json#` | `standard` | const="standard" | not-declared-here |
| THEIRS | const-restated | `core.package_signal_targeting.PackageSignalTargeting5` | `value_type` | `core/package-signal-targeting.json#/allOf/0/oneOf/0` | `binary` | const="binary" | required |
| THEIRS | const-restated | `core.package_signal_targeting.PackageSignalTargeting6` | `value_type` | `core/package-signal-targeting.json#/allOf/0/oneOf/1` | `categorical` | const="categorical" | required |
| THEIRS | const-restated | `core.package_signal_targeting.PackageSignalTargeting7` | `value_type` | `core/package-signal-targeting.json#/allOf/0/oneOf/2` | `numeric` | const="numeric" | required |
| THEIRS | const-restated | `core.performance_feedback_metric.PerformanceFeedbackMetric1` | `scope` | `core/performance-feedback-metric.json#/oneOf/0` | `standard` | const="standard" | required |
| THEIRS | const-restated | `core.performance_feedback_metric.PerformanceFeedbackMetric2` | `scope` | `core/performance-feedback-metric.json#/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `core.performance_feedback.Metric` | `scope` | `core/performance-feedback.json#/properties/metric/oneOf/0` | `standard` | const="standard" | not-declared-here |
| THEIRS | const-restated | `core.performance_feedback.Metric7` | `scope` | `core/performance-feedback.json#/properties/metric/oneOf/1` | `vendor` | const="vendor" | not-declared-here |
| THEIRS | const-restated | `core.placement_identity.PlacementIdentity1` | `kind` | `core/placement-identity.json#/oneOf/0` | `publisher_ref` | const="publisher_ref" | required |
| THEIRS | const-restated | `core.placement_identity.PlacementIdentity2` | `kind` | `core/placement-identity.json#/oneOf/1` | `seller_inline` | const="seller_inline" | required |
| THEIRS | const-restated | `core.placement_presentation.PlacementPresentationDocument` | `schema_version` | `core/placement-presentation.json#` | `1.0` | const="1.0" | not-declared-here |
| THEIRS | const-restated | `core.placement_presentation.BoxDecoration` | `kind` | `core/placement-presentation.json#/definitions/box_decoration` | `box` | const="box" | required |
| THEIRS | const-restated | `core.placement_presentation.ImageDecoration` | `kind` | `core/placement-presentation.json#/definitions/image_decoration` | `image` | const="image" | required |
| THEIRS | const-restated | `core.placement_presentation.TextDecoration` | `kind` | `core/placement-presentation.json#/definitions/text_decoration` | `text` | const="text" | required |
| THEIRS | const-restated | `core.placement_selection.PlacementSelection1` | `mode` | `core/placement-selection.json#/oneOf/0` | `selected` | const="selected" | required |
| THEIRS | const-restated | `core.placement_selection.PlacementSelection2` | `mode` | `core/placement-selection.json#/oneOf/1` | `default` | const="default" | required |
| THEIRS | const-restated | `core.presentation_ref.PlacementPresentationReference` | `media_type` | `core/presentation-ref.json#` | `application/vnd.adcp.placement-presentation+json` | const="application/vnd.adcp.placement-presentation+json" | not-declared-here |
| THEIRS | const-restated | `core.presentation_ref.PlacementPresentationReference` | `schema_version` | `core/presentation-ref.json#` | `1.0` | const="1.0" | not-declared-here |
| THEIRS | const-restated | `core.preview_provider.PublisherDesignatedPreviewProvider` | `authority` | `core/preview-provider.json#` | `publisher_designated` | const="publisher_designated" | not-declared-here |
| THEIRS | const-restated | `core.principal_changed_webhook.PrincipalChangedWebhook` | `notification_type` | `core/principal-changed-webhook.json#` | `principal.changed` | const="principal.changed" | not-declared-here |
| THEIRS | const-restated | `core.product_audience_evidence_requirements.AcceptedAttestationIssuers1` | `type` | `core/product-audience-evidence-requirements.json#/properties/accepted_attestation_issuers/items/oneOf/0` | `brand` | const="brand" | required |
| THEIRS | const-restated | `core.product_audience_evidence_requirements.AcceptedAttestationIssuers2` | `type` | `core/product-audience-evidence-requirements.json#/properties/accepted_attestation_issuers/items/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.product_audience_evidence_requirements.AcceptedAttestationIssuers3` | `type` | `core/product-audience-evidence-requirements.json#/properties/accepted_attestation_issuers/items/oneOf/2` | `origin` | const="origin" | not-declared-here |
| THEIRS | const-restated | `core.product_execution_requirement.ProductExecutionRequirement1` | `kind` | `core/product-execution-requirement.json#/oneOf/0` | `event_source` | const="event_source" | required |
| THEIRS | const-restated | `core.product_execution_requirement.ProductExecutionRequirement2` | `kind` | `core/product-execution-requirement.json#/oneOf/1` | `catalog` | const="catalog" | required |
| THEIRS | const-restated | `core.product_execution_requirement.ProductExecutionRequirement3` | `kind` | `core/product-execution-requirement.json#/oneOf/2` | `downstream_connection` | const="downstream_connection" | required |
| THEIRS | const-restated | `core.product_filters.AudienceActivationMethods` | `pattern` | `core/product-filters.json#/properties/audience_activation_methods/items/oneOf/0` | `sync_audiences` | const="sync_audiences" | not-declared-here |
| THEIRS | const-restated | `core.product_filters.AudienceActivationMethods1` | `pattern` | `core/product-filters.json#/properties/audience_activation_methods/items/oneOf/1` | `tmp_identity_match` | const="tmp_identity_match" | required |
| THEIRS | const-restated | `core.product_filters.AudienceActivationMethods2` | `pattern` | `core/product-filters.json#/properties/audience_activation_methods/items/oneOf/2` | `file_transfer` | const="file_transfer" | required |
| THEIRS | const-restated | `core.product_filters.SignalTargetingItem5` | `value_type` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/0` | `binary` | const="binary" | required |
| THEIRS | const-restated | `core.product_filters.SignalTargetingItem6` | `value_type` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/1` | `categorical` | const="categorical" | required |
| THEIRS | const-restated | `core.product_filters.SignalTargetingItem7` | `value_type` | `core/product-filters.json#/properties/signal_targeting/items/allOf/0/oneOf/2` | `numeric` | const="numeric" | required |
| THEIRS | const-restated | `core.product.PublisherProperty86` | `selection_type` | `core/product.json#/properties/publisher_properties/items/allOf/0/oneOf/1` | `by_id` | const="by_id" | not-declared-here |
| THEIRS | const-restated | `core.product.PublisherProperty87` | `selection_type` | `core/product.json#/properties/publisher_properties/items/allOf/0/oneOf/2` | `by_tag` | const="by_tag" | not-declared-here |
| THEIRS | const-restated | `core.publisher_property_selector.PublisherPropertySelector1` | `selection_type` | `core/publisher-property-selector.json#/oneOf/0` | `all` | const="all" | required |
| THEIRS | const-restated | `core.publisher_property_selector.PublisherPropertySelector2` | `selection_type` | `core/publisher-property-selector.json#/oneOf/1` | `by_id` | const="by_id" | required |
| THEIRS | const-restated | `core.publisher_property_selector.PublisherPropertySelector3` | `selection_type` | `core/publisher-property-selector.json#/oneOf/2` | `by_tag` | const="by_tag" | required |
| THEIRS | const-restated | `core.reference_renderer.ReferenceRenderer` | `runtime` | `core/reference-renderer.json#` | `browser-esm` | const="browser-esm" | not-declared-here |
| THEIRS | const-restated | `core.reporting_canonical_content_digest.ReportingCanonicalContentDigest` | `algorithm` | `core/reporting-canonical-content-digest.json#` | `sha256` | const="sha256" | not-declared-here |
| THEIRS | const-restated | `core.reporting_canonicalization_contract.ReportingCanonicalizationContract` | `algorithm` | `core/reporting-canonicalization-contract.json#` | `adcp_jcs_rows_v1` | const="adcp_jcs_rows_v1" | not-declared-here |
| THEIRS | const-restated | `core.reporting_canonicalization_contract.ReportingCanonicalizationContract` | `contract_version` | `core/reporting-canonicalization-contract.json#` | `1.0` | const="1.0" | not-declared-here |
| THEIRS | const-restated | `core.reporting_canonicalization_contract.ReportingCanonicalizationContract` | `media_type` | `core/reporting-canonicalization-contract.json#` | `application/vnd.adcp.reporting-canonicalization+json` | const="application/vnd.adcp.reporting-canonicalization+json" | not-declared-here |
| THEIRS | const-restated | `core.reporting_dataset_share_destination.ReportingDatasetShareDestination1` | `mode` | `core/reporting-dataset-share-destination.json#/oneOf/0` | `existing` | const="existing" | required |
| THEIRS | const-restated | `core.reporting_dataset_share_destination.ReportingDatasetShareDestination2` | `mode` | `core/reporting-dataset-share-destination.json#/oneOf/1` | `provision` | const="provision" | required |
| THEIRS | const-restated | `core.reporting_delivery_method.ReportingDeliveryMethod1` | `pattern` | `core/reporting-delivery-method.json#/oneOf/0` | `file_transfer` | const="file_transfer" | required |
| THEIRS | const-restated | `core.reporting_delivery_offering.ReportingProfile` | `schema_dialect` | `core/reporting-delivery-offering.json#/properties/reporting_profile` | `https://json-schema.org/draft/2020-12/schema` | const="https://json-schema.org/draft/2020-12/schema" | required |
| THEIRS | const-restated | `core.reporting_delivery_offering.ReportingProfile` | `schema_ref_policy` | `core/reporting-delivery-offering.json#/properties/reporting_profile` | `local_fragment_only` | const="local_fragment_only" | required |
| THEIRS | const-restated | `core.reporting_delivery_ready_webhook.ReportingDeliveryReadyWebhook` | `notification_type` | `core/reporting-delivery-ready-webhook.json#` | `reporting.delivery_ready` | const="reporting.delivery_ready" | not-declared-here |
| THEIRS | const-restated | `core.reporting_file_manifest.ReportingFileManifest` | `manifest_version` | `core/reporting-file-manifest.json#` | `1.0` | const="1.0" | not-declared-here |
| THEIRS | const-restated | `core.reporting_ledger_changed_webhook.ReportingLedgerChangedWebhook` | `notification_type` | `core/reporting-ledger-changed-webhook.json#` | `reporting.ledger_changed` | const="reporting.ledger_changed" | not-declared-here |
| THEIRS | const-restated | `core.reporting_report_definition.ReportingReportDefinition` | `media_type` | `core/reporting-report-definition.json#` | `application/vnd.adcp.reporting-definition+json` | const="application/vnd.adcp.reporting-definition+json" | not-declared-here |
| THEIRS | const-restated | `core.reporting_report_definition.FinalityPolicies` | `basis` | `core/reporting-report-definition.json#/properties/finality_policies/items/oneOf/0` | `source_final` | const="source_final" | required |
| THEIRS | const-restated | `core.reporting_report_definition.FinalityPolicies1` | `basis` | `core/reporting-report-definition.json#/properties/finality_policies/items/oneOf/1` | `contractual_cutoff` | const="contractual_cutoff" | required |
| THEIRS | const-restated | `core.reporting_report_definition.FinalityPolicies2` | `basis` | `core/reporting-report-definition.json#/properties/finality_policies/items/oneOf/2` | `stabilized` | const="stabilized" | required |
| THEIRS | const-restated | `core.reporting_revision.ReportingRevision` | `schema_dialect` | `core/reporting-revision.json#` | `https://json-schema.org/draft/2020-12/schema` | const="https://json-schema.org/draft/2020-12/schema" | not-declared-here |
| THEIRS | const-restated | `core.reporting_revision.ReportingRevision` | `schema_ref_policy` | `core/reporting-revision.json#` | `local_fragment_only` | const="local_fragment_only" | not-declared-here |
| THEIRS | const-restated | `core.reporting_status_changed_webhook.ReportingStatusChangedWebhook` | `notification_type` | `core/reporting-status-changed-webhook.json#` | `reporting.status_changed` | const="reporting.status_changed" | not-declared-here |
| THEIRS | const-restated | `core.reporting_write_destination.ReportingWriteDestination1` | `mode` | `core/reporting-write-destination.json#/oneOf/0` | `existing` | const="existing" | required |
| THEIRS | const-restated | `core.reporting_write_destination.ReportingWriteDestination2` | `mode` | `core/reporting-write-destination.json#/oneOf/1` | `provision` | const="provision" | required |
| THEIRS | const-restated | `core.requirements.catalog_field_binding.AssetPoolBinding` | `kind` | `core/requirements/catalog-field-binding.json#/definitions/AssetPoolBinding` | `asset_pool` | const="asset_pool" | required |
| THEIRS | const-restated | `core.requirements.catalog_field_binding.ScalarBinding` | `kind` | `core/requirements/catalog-field-binding.json#/definitions/ScalarBinding` | `scalar` | const="scalar" | required |
| THEIRS | const-restated | `core.requirements.catalog_field_binding.CatalogFieldBinding1` | `kind` | `core/requirements/catalog-field-binding.json#/oneOf/2` | `catalog_group` | const="catalog_group" | required |
| THEIRS | const-restated | `core.rights_attestation_evaluation.ActionBinding` | `action_type` | `core/rights-attestation-evaluation.json#/properties/evaluation/allOf/0/properties/action_binding` | `https://adcontextprotocol.org/actions/rights-grant-evaluation` | const="https://adcontextprotocol.org/actions/rights-grant-evaluation" | not-declared-here |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Reference` | `claim_type` | `core/rights-attestation-evaluation.json#/properties/reference` | `https://adcontextprotocol.org/claims/rights/grant` | const="https://adcontextprotocol.org/claims/rights/grant" | required |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Issuer` | `type` | `core/rights-attestation-evaluation.json#/properties/reference/allOf/0/properties/issuer/oneOf/0` | `brand` | const="brand" | not-declared-here |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Subject10` | `resource_type` | `core/rights-attestation-evaluation.json#/properties/reference/allOf/0/properties/subject/oneOf/0` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Subject` | `resource_type` | `core/rights-attestation-evaluation.json#/properties/reference/allOf/0/properties/subject/oneOf/1` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Subject19` | `resource_type` | `core/rights-attestation-evaluation.json#/properties/reference/allOf/0/properties/subject/oneOf/2` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_attestation_evaluation.Subject19` | `type` | `core/rights-attestation-evaluation.json#/properties/reference/allOf/0/properties/subject/oneOf/2` | `resource` | const="resource" | not-declared-here |
| THEIRS | const-restated | `core.rights_constraint.AttestationRef` | `claim_type` | `core/rights-constraint.json#/properties/attestation_refs/items` | `https://adcontextprotocol.org/claims/rights/grant` | const="https://adcontextprotocol.org/claims/rights/grant" | required |
| THEIRS | const-restated | `core.rights_constraint.Issuer` | `type` | `core/rights-constraint.json#/properties/attestation_refs/items/allOf/0/properties/issuer/oneOf/0` | `brand` | const="brand" | not-declared-here |
| THEIRS | const-restated | `core.rights_constraint.Subject20` | `resource_type` | `core/rights-constraint.json#/properties/attestation_refs/items/allOf/0/properties/subject/oneOf/0` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_constraint.Subject` | `resource_type` | `core/rights-constraint.json#/properties/attestation_refs/items/allOf/0/properties/subject/oneOf/1` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_constraint.Subject29` | `resource_type` | `core/rights-constraint.json#/properties/attestation_refs/items/allOf/0/properties/subject/oneOf/2` | `https://adcontextprotocol.org/claims/subjects/rights-grant` | const="https://adcontextprotocol.org/claims/subjects/rights-grant" | not-declared-here |
| THEIRS | const-restated | `core.rights_constraint.Subject29` | `type` | `core/rights-constraint.json#/properties/attestation_refs/items/allOf/0/properties/subject/oneOf/2` | `resource` | const="resource" | not-declared-here |
| THEIRS | const-restated | `core.signal_coverage_forecast.SignalCoverageForecast` | `forecast_range_unit` | `core/signal-coverage-forecast.json#` | `availability` | const="availability" | not-declared-here |
| THEIRS | const-restated | `core.signal_id.SignalId8` | `source` | `core/signal-id.json#/oneOf/0` | `catalog` | const="catalog" | required |
| THEIRS | const-restated | `core.signal_id.SignalId9` | `source` | `core/signal-id.json#/oneOf/1` | `agent` | const="agent" | required |
| THEIRS | const-restated | `core.signal_pricing.VendorPricing1` | `model` | `core/signal-pricing.json#/oneOf/0` | `cpm` | const="cpm" | required |
| THEIRS | const-restated | `core.signal_pricing.VendorPricing2` | `model` | `core/signal-pricing.json#/oneOf/1` | `percent_of_media` | const="percent_of_media" | required |
| THEIRS | const-restated | `core.signal_pricing.VendorPricing3` | `model` | `core/signal-pricing.json#/oneOf/2` | `flat_fee` | const="flat_fee" | required |
| THEIRS | const-restated | `core.signal_pricing.VendorPricing4` | `model` | `core/signal-pricing.json#/oneOf/3` | `per_unit` | const="per_unit" | required |
| THEIRS | const-restated | `core.signal_pricing.VendorPricing5` | `model` | `core/signal-pricing.json#/oneOf/4` | `custom` | const="custom" | required |
| THEIRS | const-restated | `core.signal_ref.SignalRef1` | `scope` | `core/signal-ref.json#/oneOf/0` | `product` | const="product" | required |
| THEIRS | const-restated | `core.signal_ref.SignalRef2` | `scope` | `core/signal-ref.json#/oneOf/1` | `data_provider` | const="data_provider" | required |
| THEIRS | const-restated | `core.signal_ref.SignalRef3` | `scope` | `core/signal-ref.json#/oneOf/2` | `signal_source` | const="signal_source" | required |
| THEIRS | const-restated | `core.signal_targeting_expression.SignalTargetingExpression1` | `value_type` | `core/signal-targeting-expression.json#/oneOf/0` | `binary` | const="binary" | required |
| THEIRS | const-restated | `core.signal_targeting_expression.SignalTargetingExpression2` | `value_type` | `core/signal-targeting-expression.json#/oneOf/1` | `categorical` | const="categorical" | required |
| THEIRS | const-restated | `core.signal_targeting_expression.SignalTargetingExpression3` | `value_type` | `core/signal-targeting-expression.json#/oneOf/2` | `numeric` | const="numeric" | required |
| THEIRS | const-restated | `core.signal_targeting.SignalTargeting1` | `value_type` | `core/signal-targeting.json#/oneOf/0` | `binary` | const="binary" | required |
| THEIRS | const-restated | `core.signal_targeting.SignalTargeting2` | `value_type` | `core/signal-targeting.json#/oneOf/1` | `categorical` | const="categorical" | required |
| THEIRS | const-restated | `core.signal_targeting.SignalTargeting3` | `value_type` | `core/signal-targeting.json#/oneOf/2` | `numeric` | const="numeric" | required |
| THEIRS | const-restated | `core.targeting_modification.TargetingModification1` | `operation` | `core/targeting-modification.json#/oneOf/0` | `replace` | const="replace" | required |
| THEIRS | const-restated | `core.targeting_modification.TargetingModification2` | `operation` | `core/targeting-modification.json#/oneOf/1` | `remove_values` | const="remove_values" | required |
| THEIRS | const-restated | `core.tracker_execution_selector.TrackerExecutionSelector1` | `asset_type` | `core/tracker-execution-selector.json#/oneOf/0` | `pixel_tracker` | const="pixel_tracker" | required |
| THEIRS | const-restated | `core.tracker_execution_selector.TrackerExecutionSelector1` | `method` | `core/tracker-execution-selector.json#/oneOf/0` | `img` | const="img" | required |
| THEIRS | const-restated | `core.tracker_execution_selector.TrackerExecutionSelector2` | `asset_type` | `core/tracker-execution-selector.json#/oneOf/1` | `vast_tracker` | const="vast_tracker" | required |
| THEIRS | const-restated | `core.tracker_execution_selector.TrackerExecutionSelector3` | `asset_type` | `core/tracker-execution-selector.json#/oneOf/2` | `daast_tracker` | const="daast_tracker" | required |
| THEIRS | const-restated | `core.transformer.InputFormat18` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/0` | `image` | const="image" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat19` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/1` | `html5` | const="html5" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat28` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/10` | `native_in_feed` | const="native_in_feed" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat29` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/11` | `responsive_creative` | const="responsive_creative" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat30` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/12` | `agent_placement` | const="agent_placement" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat31` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/13` | `seller_rendered_stateful_display` | const="seller_rendered_stateful_display" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat32` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/14` | `coordinated_placements` | const="coordinated_placements" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat33` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/15` | `custom` | const="custom" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat20` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/2` | `display_tag` | const="display_tag" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat21` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/3` | `image_carousel` | const="image_carousel" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat22` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/4` | `video_hosted` | const="video_hosted" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat23` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/5` | `video_vast` | const="video_vast" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat24` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/6` | `audio_hosted` | const="audio_hosted" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat25` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/7` | `audio_vast` | const="audio_vast" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat26` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/8` | `audio_daast` | const="audio_daast" | not-declared-here |
| THEIRS | const-restated | `core.transformer.InputFormat27` | `format_kind` | `core/transformer.json#/properties/input_formats/items/allOf/0/oneOf/9` | `sponsored_placement` | const="sponsored_placement" | not-declared-here |
| THEIRS | const-restated | `core.vendor_pricing_option.VendorPricingOption7` | `model` | `core/vendor-pricing-option.json#/allOf/1/oneOf/0` | `cpm` | const="cpm" | required |
| THEIRS | const-restated | `core.vendor_pricing_option.VendorPricingOption8` | `model` | `core/vendor-pricing-option.json#/allOf/1/oneOf/1` | `percent_of_media` | const="percent_of_media" | required |
| THEIRS | const-restated | `core.vendor_pricing_option.VendorPricingOption9` | `model` | `core/vendor-pricing-option.json#/allOf/1/oneOf/2` | `flat_fee` | const="flat_fee" | required |
| THEIRS | const-restated | `core.vendor_pricing_option.VendorPricingOption10` | `model` | `core/vendor-pricing-option.json#/allOf/1/oneOf/3` | `per_unit` | const="per_unit" | required |
| THEIRS | const-restated | `core.vendor_pricing_option.VendorPricingOption11` | `model` | `core/vendor-pricing-option.json#/allOf/1/oneOf/4` | `custom` | const="custom" | required |
| THEIRS | const-restated | `core.verification_token_claims.AgenticadvertisingOrgVerificationTokenClaims` | `aud` | `core/verification-token-claims.json#` | `aao-verification` | const="aao-verification" | not-declared-here |
| THEIRS | const-restated | `core.verification_token_claims.AgenticadvertisingOrgVerificationTokenClaims` | `iss` | `core/verification-token-claims.json#` | `https://aao.org` | const="https://aao.org" | not-declared-here |
| THEIRS | const-restated | `core.webhook_challenge.WebhookChallenge` | `type` | `core/webhook-challenge.json#` | `webhook.challenge` | const="webhook.challenge" | not-declared-here |
| THEIRS | const-restated | `core.wholesale_feed_event.AppliesTo2` | `scope` | `core/wholesale-feed-event.json#/$defs/appliesTo/oneOf/1` | `account` | const="account" | required |
| THEIRS | const-restated | `creative.creative_assignment_changed_webhook.CreativeAssignmentChangedWebhook` | `notification_type` | `creative/creative-assignment-changed-webhook.json#` | `creative.assignment_changed` | const="creative.assignment_changed" | not-declared-here |
| THEIRS | const-restated | `creative.creative_purged_webhook.CreativePurgedWebhook` | `notification_type` | `creative/creative-purged-webhook.json#` | `creative.purged` | const="creative.purged" | not-declared-here |
| THEIRS | const-restated | `creative.creative_status_changed_webhook.CreativeStatusChangedWebhook` | `notification_type` | `creative/creative-status-changed-webhook.json#` | `creative.status_changed` | const="creative.status_changed" | not-declared-here |
| THEIRS | const-restated | `creative.get_creative_features_async_response_submitted.GetCreativeFeaturesSubmitted` | `status` | `creative/get-creative-features-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `creative.get_creative_features_response.GetCreativeFeaturesResponse3` | `status` | `creative/get-creative-features-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `creative.preview_creative_response.PreviewCreativeResponse1` | `response_type` | `creative/preview-creative-response.json#/oneOf/0` | `single` | const="single" | required |
| THEIRS | const-restated | `creative.preview_creative_response.PreviewCreativeResponse2` | `response_type` | `creative/preview-creative-response.json#/oneOf/1` | `batch` | const="batch" | required |
| THEIRS | const-restated | `creative.preview_creative_response.PreviewCreativeResponse3` | `response_type` | `creative/preview-creative-response.json#/oneOf/2` | `variant` | const="variant" | required |
| THEIRS | const-restated | `creative.preview_creative_response.PreviewCreativeResponse4` | `response_type` | `creative/preview-creative-response.json#/oneOf/3` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `creative.preview_creative_response.PreviewCreativeResponse4` | `status` | `creative/preview-creative-response.json#/oneOf/3` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `creative.preview_render.PreviewRender1` | `output_format` | `creative/preview-render.json#/oneOf/0` | `url` | const="url" | required |
| THEIRS | const-restated | `creative.preview_render.PreviewRender2` | `output_format` | `creative/preview-render.json#/oneOf/1` | `html` | const="html" | required |
| THEIRS | const-restated | `creative.preview_render.PreviewRender3` | `output_format` | `creative/preview-render.json#/oneOf/2` | `both` | const="both" | required |
| THEIRS | const-restated | `creative.sync_creatives_async_response_submitted.SyncCreativesSubmitted` | `status` | `creative/sync-creatives-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `creative.sync_creatives_request.AssignmentOperations1` | `operation` | `creative/sync-creatives-request.json#/properties/assignment_operations/items/oneOf/0` | `assign` | const="assign" | required |
| THEIRS | const-restated | `creative.sync_creatives_request.AssignmentOperations2` | `operation` | `creative/sync-creatives-request.json#/properties/assignment_operations/items/oneOf/1` | `unassign` | const="unassign" | required |
| THEIRS | const-restated | `creative.sync_creatives_request.AssignmentOperations3` | `operation` | `creative/sync-creatives-request.json#/properties/assignment_operations/items/oneOf/2` | `replace` | const="replace" | required |
| THEIRS | const-restated | `creative.sync_creatives_response.SyncCreativesResponse3` | `status` | `creative/sync-creatives-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `error_details.agent_permission_denied.AgentPermissionDeniedDetails` | `scope` | `error-details/agent-permission-denied.json#` | `agent` | const="agent" | not-declared-here |
| THEIRS | const-restated | `error_details.governance_agent_not_accepted.GovernanceAgentNotAcceptedDetails1` | `disclosure` | `error-details/governance-agent-not-accepted.json#/oneOf/0` | `disclosed` | const="disclosed" | required |
| THEIRS | const-restated | `error_details.governance_agent_not_accepted.GovernanceAgentNotAcceptedDetails2` | `disclosure` | `error-details/governance-agent-not-accepted.json#/oneOf/1` | `opaque` | const="opaque" | required |
| THEIRS | const-restated | `extensions.extension_meta.AdcpExtensionFileSchema` | `$schema` | `extensions/extension-meta.json#` | `http://json-schema.org/draft-07/schema#` | const="http://json-schema.org/draft-07/schema#" | not-declared-here |
| THEIRS | const-restated | `extensions.extension_meta.AdcpExtensionFileSchema` | `type` | `extensions/extension-meta.json#` | `object` | const="object" | not-declared-here |
| THEIRS | const-restated | `governance.accepted_governance_agents.AnyOf1` | `kind` | `governance/accepted-governance-agents.json#/properties/any_of/items/oneOf/0` | `agent_url` | const="agent_url" | required |
| THEIRS | const-restated | `governance.accepted_governance_agents.AnyOf2` | `kind` | `governance/accepted-governance-agents.json#/properties/any_of/items/oneOf/1` | `verification` | const="verification" | required |
| THEIRS | const-restated | `governance.check_governance_request.Subject4` | `resource_type` | `governance/check-governance-request.json#/properties/runtime_attestations/items/allOf/0/properties/subject/oneOf/0` | `https://adcontextprotocol.org/claims/subjects/signal` | const="https://adcontextprotocol.org/claims/subjects/signal" | not-declared-here |
| THEIRS | const-restated | `governance.check_governance_response.ActionBinding` | `action_type` | `governance/check-governance-response.json#/properties/runtime_attestation_evaluations/items/allOf/0/properties/action_binding` | `https://adcontextprotocol.org/actions/governance-check` | const="https://adcontextprotocol.org/actions/governance-check" | not-declared-here |
| THEIRS | const-restated | `media_buy.accept_proposal_async_response_submitted.AcceptProposalSubmitted` | `status` | `media-buy/accept-proposal-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement1` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/0` | `category_declaration` | const="category_declaration" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement2` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/1` | `advertiser_verification` | const="advertiser_verification" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement11` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/10` | `targeting_restriction` | const="targeting_restriction" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement14` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/13` | `format_restriction` | const="format_restriction" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement15` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/14` | `time_restriction` | const="time_restriction" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement17` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/16` | `custom` | const="custom" | required |
| THEIRS | const-restated | `media_buy.acceptance_policy_requirement.AcceptancePolicyRequirement10` | `kind` | `media-buy/acceptance-policy-requirement.json#/oneOf/9` | `disclosure` | const="disclosure" | required |
| THEIRS | const-restated | `media_buy.build_creative_async_response_submitted.BuildCreativeSubmitted` | `status` | `media-buy/build-creative-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.build_creative_response.BuildCreativeResponse6` | `status` | `media-buy/build-creative-response.json#/oneOf/5` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.buy_products_async_response_submitted.BuyProductsSubmitted` | `status` | `media-buy/buy-products-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints1` | `kind` | `media-buy/change-term-constraints.json#/oneOf/0` | `budget` | const="budget" | required |
| THEIRS | const-restated | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints2` | `kind` | `media-buy/change-term-constraints.json#/oneOf/1` | `flight` | const="flight" | required |
| THEIRS | const-restated | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints3` | `kind` | `media-buy/change-term-constraints.json#/oneOf/2` | `package_count` | const="package_count" | required |
| THEIRS | const-restated | `media_buy.change_term_constraints.MediaBuyChangeTermConstraints4` | `kind` | `media-buy/change-term-constraints.json#/oneOf/3` | `effective_timing` | const="effective_timing" | required |
| THEIRS | const-restated | `media_buy.control_media_buy_async_response_submitted.ControlMediaBuySubmitted` | `status` | `media-buy/control-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.control_media_buy_response.ControlMediaBuyResponse1` | `status` | `media-buy/control-media-buy-response.json#/oneOf/0` | `completed` | const="completed" | required |
| THEIRS | const-restated | `media_buy.control_media_buy_response.ControlMediaBuyResponse2` | `status` | `media-buy/control-media-buy-response.json#/oneOf/1` | `failed` | const="failed" | required |
| THEIRS | const-restated | `media_buy.control_media_buy_response.ControlMediaBuyResponse3` | `status` | `media-buy/control-media-buy-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.create_media_buy_async_response_submitted.CreateMediaBuySubmitted` | `status` | `media-buy/create-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.create_media_buy_response.CreateMediaBuyResponse3` | `status` | `media-buy/create-media-buy-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.decline_proposals_async_response_submitted.DeclineProposalsSubmitted` | `status` | `media-buy/decline-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.decline_proposals_response.DeclineProposalsResponse2` | `status` | `media-buy/decline-proposals-response.json#/anyOf/1` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.get_products_async_response_submitted.GetProductsSubmitted` | `status` | `media-buy/get-products-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.get_products_rejected.GetProductsRejected` | `status` | `media-buy/get-products-rejected.json#` | `rejected` | const="rejected" | not-declared-here |
| THEIRS | const-restated | `media_buy.get_products_request.Refine1` | `scope` | `media-buy/get-products-request.json#/properties/refine/items/oneOf/0` | `request` | const="request" | required |
| THEIRS | const-restated | `media_buy.get_products_request.Refine2` | `scope` | `media-buy/get-products-request.json#/properties/refine/items/oneOf/1` | `product` | const="product" | required |
| THEIRS | const-restated | `media_buy.get_products_request.Refine3` | `scope` | `media-buy/get-products-request.json#/properties/refine/items/oneOf/2` | `proposal` | const="proposal" | required |
| THEIRS | const-restated | `media_buy.get_products_response.RefinementApplied1` | `scope` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/0` | `request` | const="request" | required |
| THEIRS | const-restated | `media_buy.get_products_response.RefinementApplied2` | `scope` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/1` | `product` | const="product" | required |
| THEIRS | const-restated | `media_buy.get_products_response.RefinementApplied3` | `scope` | `media-buy/get-products-response.json#/properties/refinement_applied/items/oneOf/2` | `proposal` | const="proposal" | required |
| THEIRS | const-restated | `media_buy.media_buy_commitment_response.MediaBuyCommitmentResponse1` | `status` | `media-buy/media-buy-commitment-response.json#/oneOf/0` | `completed` | const="completed" | required |
| THEIRS | const-restated | `media_buy.media_buy_commitment_response.MediaBuyCommitmentResponse2` | `status` | `media-buy/media-buy-commitment-response.json#/oneOf/1` | `failed` | const="failed" | required |
| THEIRS | const-restated | `media_buy.media_buy_commitment_response.MediaBuyCommitmentResponse3` | `status` | `media-buy/media-buy-commitment-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.outcome_target.Goal` | `kind` | `media-buy/outcome-target.json#/properties/goal/oneOf/0` | `metric` | const="metric" | required |
| THEIRS | const-restated | `media_buy.outcome_target.Goal1` | `kind` | `media-buy/outcome-target.json#/properties/goal/oneOf/1` | `event` | const="event" | required |
| THEIRS | const-restated | `media_buy.package_request.CommittedMetrics1` | `scope` | `media-buy/package-request.json#/properties/committed_metrics/items/oneOf/0` | `standard` | const="standard" | not-declared-here |
| THEIRS | const-restated | `media_buy.package_request.CommittedMetrics2` | `scope` | `media-buy/package-request.json#/properties/committed_metrics/items/oneOf/1` | `vendor` | const="vendor" | required |
| THEIRS | const-restated | `media_buy.product_refinement.ProductRefinementRequests2` | `scope` | `media-buy/product-refinement.json#/items/oneOf/0` | `request` | const="request" | not-declared-here |
| THEIRS | const-restated | `media_buy.product_refinement.ProductRefinementRequests3` | `scope` | `media-buy/product-refinement.json#/items/oneOf/1` | `product` | const="product" | not-declared-here |
| THEIRS | const-restated | `media_buy.product_refinement.ProductRefinementRequests4` | `scope` | `media-buy/product-refinement.json#/items/oneOf/2` | `proposal` | const="proposal" | not-declared-here |
| THEIRS | const-restated | `media_buy.refine_proposals_async_response_submitted.RefineProposalsSubmitted` | `status` | `media-buy/refine-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.request_proposals_async_response_submitted.RequestProposalsSubmitted` | `status` | `media-buy/request-proposals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.sync_audiences_response.SyncAudiencesResponse3` | `status` | `media-buy/sync-audiences-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.sync_catalogs_async_response_submitted.SyncCatalogsSubmitted` | `status` | `media-buy/sync-catalogs-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.sync_catalogs_response.SyncCatalogsResponse3` | `status` | `media-buy/sync-catalogs-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `media_buy.sync_reporting_receipts_response.SyncReportingReceiptsResponse` | `status` | `media-buy/sync-reporting-receipts-response.json#` | `completed` | const="completed" | not-declared-here |
| THEIRS | const-restated | `media_buy.sync_reporting_receipts_response.Results` | `result` | `media-buy/sync-reporting-receipts-response.json#/properties/results/items/anyOf/4` | `failed` | const="failed" | required |
| THEIRS | const-restated | `media_buy.sync_reporting_status_response.SyncReportingStatusResponse` | `status` | `media-buy/sync-reporting-status-response.json#` | `completed` | const="completed" | not-declared-here |
| THEIRS | const-restated | `media_buy.sync_reporting_status_response.Results27` | `result` | `media-buy/sync-reporting-status-response.json#/properties/results/items/oneOf/2` | `failed` | const="failed" | required |
| THEIRS | const-restated | `media_buy.update_media_buy_async_response_submitted.UpdateMediaBuySubmitted` | `status` | `media-buy/update-media-buy-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `media_buy.update_media_buy_response.UpdateMediaBuyResponse3` | `status` | `media-buy/update-media-buy-response.json#/oneOf/2` | `submitted` | const="submitted" | required |
| THEIRS | const-restated | `pricing_options.cpa_option.CpaPricingOption` | `pricing_model` | `pricing-options/cpa-option.json#` | `cpa` | const="cpa" | not-declared-here |
| THEIRS | const-restated | `pricing_options.cpc_option.CpcPricingOption` | `pricing_model` | `pricing-options/cpc-option.json#` | `cpc` | const="cpc" | not-declared-here |
| THEIRS | const-restated | `pricing_options.cpcv_option.CpcvPricingOption` | `pricing_model` | `pricing-options/cpcv-option.json#` | `cpcv` | const="cpcv" | not-declared-here |
| THEIRS | const-restated | `pricing_options.cpm_option.CpmPricingOption` | `pricing_model` | `pricing-options/cpm-option.json#` | `cpm` | const="cpm" | not-declared-here |
| THEIRS | const-restated | `pricing_options.cpp_option.CppPricingOption` | `pricing_model` | `pricing-options/cpp-option.json#` | `cpp` | const="cpp" | not-declared-here |
| THEIRS | const-restated | `pricing_options.cpv_option.CpvPricingOption` | `pricing_model` | `pricing-options/cpv-option.json#` | `cpv` | const="cpv" | not-declared-here |
| THEIRS | const-restated | `pricing_options.flat_rate_option.FlatRatePricingOption` | `pricing_model` | `pricing-options/flat-rate-option.json#` | `flat_rate` | const="flat_rate" | not-declared-here |
| THEIRS | const-restated | `pricing_options.flat_rate_option.Parameters` | `type` | `pricing-options/flat-rate-option.json#/properties/parameters` | `dooh` | const="dooh" | required |
| THEIRS | const-restated | `pricing_options.revenue_share_option.RevenueSharePricingOption` | `pricing_model` | `pricing-options/revenue-share-option.json#` | `revenue_share` | const="revenue_share" | not-declared-here |
| THEIRS | const-restated | `pricing_options.time_option.TimeBasedPricingOption` | `pricing_model` | `pricing-options/time-option.json#` | `time` | const="time" | not-declared-here |
| THEIRS | const-restated | `pricing_options.vcpm_option.VcpmPricingOption` | `pricing_model` | `pricing-options/vcpm-option.json#` | `vcpm` | const="vcpm" | not-declared-here |
| THEIRS | const-restated | `property.base_property_source.BasePropertySource1` | `selection_type` | `property/base-property-source.json#/oneOf/0` | `publisher_tags` | const="publisher_tags" | required |
| THEIRS | const-restated | `property.base_property_source.BasePropertySource2` | `selection_type` | `property/base-property-source.json#/oneOf/1` | `publisher_ids` | const="publisher_ids" | required |
| THEIRS | const-restated | `property.base_property_source.BasePropertySource3` | `selection_type` | `property/base-property-source.json#/oneOf/2` | `identifiers` | const="identifiers" | required |
| THEIRS | const-restated | `property.property_list_changed_webhook.PropertyListChangedWebhook` | `event` | `property/property-list-changed-webhook.json#` | `property_list_changed` | const="property_list_changed" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.MaxBidWithCostPer` | `kind` | `protocol/get-adcp-capabilities-response.json#/definitions/Shared76` | `max_bid_with_cost_per` | const="max_bid_with_cost_per" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.MaxBidWithRoas` | `kind` | `protocol/get-adcp-capabilities-response.json#/definitions/Shared77` | `max_bid_with_roas` | const="max_bid_with_roas" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.ChangeFeed` | `event_type` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `account.change_recorded` | const="account.change_recorded" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.ChangeFeed` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `list_account_changes` | const="list_account_changes" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.ChangeFeed` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.ChangeFeed` | `event_type` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `account.change_recorded` | const="account.change_recorded" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.ChangeFeed` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `list_account_changes` | const="list_account_changes" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.ChangeFeed` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/change_feed/oneOf/0` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Notifications6` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/notifications/oneOf/0` | `list_accounts` | const="list_accounts" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Notifications6` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/notifications/oneOf/0` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.Notifications2` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/notifications/oneOf/0` | `list_accounts` | const="list_accounts" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.Notifications2` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/account/properties/notifications/oneOf/0` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Issuer` | `type` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/attestations/properties/accepted_issuers/items/properties/issuer/oneOf/0` | `brand` | const="brand" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Issuer1` | `type` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/attestations/properties/accepted_issuers/items/properties/issuer/oneOf/1` | `agent` | const="agent" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Issuer2` | `type` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/attestations/properties/accepted_issuers/items/properties/issuer/oneOf/2` | `origin` | const="origin" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.AnyOf` | `kind` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/governance_enforcement/properties/accepted_governance_agents/properties/any_of/items/oneOf/0` | `agent_url` | const="agent_url" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.AnyOf5` | `kind` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/governance_enforcement/properties/accepted_governance_agents/properties/any_of/items/oneOf/1` | `verification` | const="verification" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Principal` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/principal` | `get_principal` | const="get_principal" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Principal` | `sync_task` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/principal` | `sync_principal` | const="sync_principal" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.Principal` | `read_task` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/principal` | `get_principal` | const="get_principal" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.Principal` | `sync_task` | `protocol/get-adcp-capabilities-response.json#/properties/adcp/properties/principal` | `sync_principal` | const="sync_principal" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Localization` | `locale_matching` | `protocol/get-adcp-capabilities-response.json#/properties/creative/properties/localization` | `rfc4647_lookup` | const="rfc4647_lookup" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.Localization` | `locale_matching` | `protocol/get-adcp-capabilities-response.json#/properties/creative/properties/localization` | `rfc4647_lookup` | const="rfc4647_lookup" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.MeasurementGateway` | `delivery_task` | `protocol/get-adcp-capabilities-response.json#/properties/measurement_gateway` | `get_media_buy_delivery` | const="get_media_buy_delivery" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.MeasurementGateway` | `feedback_task` | `protocol/get-adcp-capabilities-response.json#/properties/measurement_gateway` | `provide_performance_feedback` | const="provide_performance_feedback" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.MeasurementGateway` | `delivery_task` | `protocol/get-adcp-capabilities-response.json#/properties/measurement_gateway` | `get_media_buy_delivery` | const="get_media_buy_delivery" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.MeasurementGateway` | `feedback_task` | `protocol/get-adcp-capabilities-response.json#/properties/measurement_gateway` | `provide_performance_feedback` | const="provide_performance_feedback" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.SupportedActivationMethods1` | `pattern` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/audience_targeting/properties/supported_activation_methods/items/oneOf/1` | `tmp_identity_match` | const="tmp_identity_match" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.SupportedActivationMethods2` | `pattern` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/audience_targeting/properties/supported_activation_methods/items/oneOf/2` | `file_transfer` | const="file_transfer" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.SupportedActivationMethods3` | `pattern` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/audience_targeting/properties/supported_activation_methods/items/oneOf/3` | `dataset_query` | const="dataset_query" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.SupportedActivationMethods4` | `pattern` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/audience_targeting/properties/supported_activation_methods/items/oneOf/4` | `clean_room` | const="clean_room" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.SupportedActivationMethods5` | `pattern` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/audience_targeting/properties/supported_activation_methods/items/oneOf/5` | `platform_distribution` | const="platform_distribution" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.Resolver2` | `protocol` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/execution/properties/targeting/properties/geo_places/additionalProperties/properties/catalog/properties/resolver` | `adcp_geo_place_resolver_v1` | const="adcp_geo_place_resolver_v1" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.RelationshipNotifications` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/relationship_notifications` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `protocol.get_adcp_capabilities_response.RelationshipNotifications` | `registration_task` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/relationship_notifications` | `sync_accounts` | const="sync_accounts" | required |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.ReportingProfile` | `schema_dialect` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/reporting_delivery/properties/offerings/items/properties/reporting_profile` | `https://json-schema.org/draft/2020-12/schema` | const="https://json-schema.org/draft/2020-12/schema" | not-declared-here |
| THEIRS | const-restated | `bundled.protocol.get_adcp_capabilities_response.ReportingProfile` | `schema_ref_policy` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/reporting_delivery/properties/offerings/items/properties/reporting_profile` | `local_fragment_only` | const="local_fragment_only" | not-declared-here |
| THEIRS | const-restated | `protocol.get_principal_response.Result2` | `kind` | `protocol/get-principal-response.json#/properties/result/oneOf/0` | `current` | const="current" | required |
| THEIRS | const-restated | `protocol.get_principal_response.Result3` | `kind` | `protocol/get-principal-response.json#/properties/result/oneOf/1` | `recognized` | const="recognized" | required |
| THEIRS | const-restated | `protocol.get_principal_response.Result5` | `kind` | `protocol/get-principal-response.json#/properties/result/oneOf/3` | `failed` | const="failed" | required |
| THEIRS | const-restated | `protocol.sync_principal_response.Result13` | `kind` | `protocol/sync-principal-response.json#/properties/result/oneOf/0` | `applied` | const="applied" | required |
| THEIRS | const-restated | `protocol.sync_principal_response.Result` | `kind` | `protocol/sync-principal-response.json#/properties/result/oneOf/1` | `validated` | const="validated" | required |
| THEIRS | const-restated | `protocol.sync_principal_response.Result15` | `kind` | `protocol/sync-principal-response.json#/properties/result/oneOf/2` | `failed` | const="failed" | required |
| THEIRS | const-restated | `signals.get_signals_async_response_submitted.GetSignalsSubmitted` | `status` | `signals/get-signals-async-response-submitted.json#` | `submitted` | const="submitted" | not-declared-here |
| THEIRS | const-restated | `trusted_match.context_match_request.ContextMatchRequest` | `type` | `trusted-match/context-match-request.json#` | `context_match_request` | const="context_match_request" | not-declared-here |
| THEIRS | const-restated | `trusted_match.context_match_response.ContextMatchResponseRouterPublisher` | `type` | `trusted-match/context-match-response.json#` | `context_match_response` | const="context_match_response" | not-declared-here |
| THEIRS | const-restated | `trusted_match.error.TmpError` | `type` | `trusted-match/error.json#` | `error` | const="error" | not-declared-here |
| THEIRS | const-restated | `trusted_match.identity_match_request.IdentityMatchRequest` | `type` | `trusted-match/identity-match-request.json#` | `identity_match_request` | const="identity_match_request" | not-declared-here |
| THEIRS | const-restated | `trusted_match.identity_match_response.IdentityMatchResponseRouterPublisher` | `type` | `trusted-match/identity-match-response.json#` | `identity_match_response` | const="identity_match_response" | not-declared-here |
| THEIRS | const-restated | `trusted_match.provider_context_match_response.ContextMatchResponseProviderRouter` | `type` | `trusted-match/provider-context-match-response.json#` | `context_match_response` | const="context_match_response" | not-declared-here |
| THEIRS | const-restated | `trusted_match.provider_identity_match_response.IdentityMatchResponseProviderRouter` | `type` | `trusted-match/provider-identity-match-response.json#` | `identity_match_response` | const="identity_match_response" | not-declared-here |
| THEIRS | contradicts | `core.reporting_delivery_capabilities.ReportingDeliveryCapabilities` | `configuration_task` | `core/reporting-delivery-capabilities.json#` | `null` | const="sync_accounts" | not-declared-here |
| THEIRS | contradicts | `core.reporting_delivery_capabilities.ReportingDeliveryCapabilities` | `status_task` | `core/reporting-delivery-capabilities.json#` | `null` | const="get_reporting_status" | not-declared-here |
| THEIRS | contradicts | `media_buy.acceptance_policy_profile.Scope` | `all_jurisdictions` | `media-buy/acceptance-policy-profile.json#/properties/scope` | `null` | const=true (required by some arm) | carried-by-a-rule |
| THEIRS | contradicts | `media_buy.refine_proposals_response.RefineProposalsResponse2` | `status` | `media-buy/refine-proposals-response.json#/anyOf/1` | `null` | const="submitted" | required |
| THEIRS | contradicts | `media_buy.request_proposals_response.RequestProposalsResponse4` | `status` | `media-buy/request-proposals-response.json#/anyOf/3` | `null` | const="submitted" | required |
| THEIRS | contradicts | `media_buy.sync_catalogs_response.SyncCatalogsResponse1` | `status` | `media-buy/sync-catalogs-response.json#/oneOf/0` | `null` | const="completed" | required |
| THEIRS | contradicts | `bundled.protocol.get_adcp_capabilities_response.ReportingDelivery` | `configuration_task` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/reporting_delivery` | `null` | const="sync_accounts" | not-declared-here |
| THEIRS | contradicts | `bundled.protocol.get_adcp_capabilities_response.ReportingDelivery` | `status_task` | `protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/reporting_delivery` | `null` | const="get_reporting_status" | not-declared-here |
| THEIRS | invented-value | `account.get_account_financials_response.GetAccountFinancialsResponse1` | `status` | `account/get-account-financials-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `account.get_account_financials_response.GetAccountFinancialsResponse2` | `status` | `account/get-account-financials-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `account.list_accounts_response.ListAccountsResponse` | `status` | `account/list-accounts-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `account.report_usage_response.ReportUsageResponse` | `status` | `account/report-usage-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `account.sync_accounts_response.SyncAccountsResponse1` | `status` | `account/sync-accounts-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `account.sync_accounts_response.SyncAccountsResponse2` | `status` | `account/sync-accounts-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `account.sync_governance_response.SyncGovernanceResponse` | `status` | `account/sync-governance-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `account.sync_governance_response.SyncGovernanceResponse1` | `status` | `account/sync-governance-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `account.sync_governance_response.SyncGovernanceResponse2` | `status` | `account/sync-governance-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `adagents.AdcpAgentsAuthorization21` | `authorized_agents` | `adagents.json#/oneOf/1` | `null` | nothing | required |
| THEIRS | invented-value | `brand.acquire_rights_response.AcquireRightsResponse1` | `status` | `brand/acquire-rights-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.acquire_rights_response.AcquireRightsResponse2` | `status` | `brand/acquire-rights-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.acquire_rights_response.AcquireRightsResponse3` | `status` | `brand/acquire-rights-response.json#/oneOf/2` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.acquire_rights_response.AcquireRightsResponse4` | `status` | `brand/acquire-rights-response.json#/oneOf/3` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.creative_approval_response.CreativeApprovalResponse1` | `status` | `brand/creative-approval-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.creative_approval_response.CreativeApprovalResponse2` | `status` | `brand/creative-approval-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.creative_approval_response.CreativeApprovalResponse3` | `status` | `brand/creative-approval-response.json#/oneOf/2` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.creative_approval_response.CreativeApprovalResponse4` | `status` | `brand/creative-approval-response.json#/oneOf/3` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.get_brand_identity_response.GetBrandIdentityResponse1` | `status` | `brand/get-brand-identity-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.get_brand_identity_response.GetBrandIdentityResponse2` | `status` | `brand/get-brand-identity-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.get_rights_response.GetRightsResponse1` | `status` | `brand/get-rights-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.get_rights_response.GetRightsResponse2` | `status` | `brand/get-rights-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.search_brands_response.SearchBrandsResponse` | `status` | `brand/search-brands-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `brand.update_rights_response.UpdateRightsResponse1` | `generation_credentials` | `brand/update-rights-response.json#/oneOf/0` | `` | nothing | required |
| THEIRS | invented-value | `brand.update_rights_response.UpdateRightsResponse1` | `rights_constraint` | `brand/update-rights-response.json#/oneOf/0` | `null` | nothing | required |
| THEIRS | invented-value | `brand.update_rights_response.UpdateRightsResponse1` | `status` | `brand/update-rights-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.update_rights_response.UpdateRightsResponse2` | `status` | `brand/update-rights-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.verify_brand_claim_response.VerifyBrandClaimSuccessResponse` | `status` | `brand/verify-brand-claim-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.verify_brand_claim_response.VerifyBrandClaimErrorResponse` | `status` | `brand/verify-brand-claim-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.verify_brand_claims_response.VerifyBrandClaimsResponseBulk` | `status` | `brand/verify-brand-claims-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `brand.verify_brand_claims_response.VerifyBrandClaimsErrorResponse` | `status` | `brand/verify-brand-claims-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `collection.create_collection_list_response.CreateCollectionListResponse` | `status` | `collection/create-collection-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `collection.delete_collection_list_response.DeleteCollectionListResponse` | `status` | `collection/delete-collection-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `collection.get_collection_list_response.GetCollectionListResponse` | `status` | `collection/get-collection-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `collection.list_collection_lists_response.ListCollectionListsResponse` | `status` | `collection/list-collection-lists-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `collection.update_collection_list_response.UpdateCollectionListResponse` | `status` | `collection/update-collection-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `compliance.comply_test_controller_request.ComplyTestControllerRequest` | `account` | `compliance/comply-test-controller-request.json#` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse` | `status` | `compliance/comply-test-controller-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse1` | `status` | `compliance/comply-test-controller-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse2` | `status` | `compliance/comply-test-controller-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse3` | `status` | `compliance/comply-test-controller-response.json#/oneOf/2` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse4` | `status` | `compliance/comply-test-controller-response.json#/oneOf/3` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse5` | `status` | `compliance/comply-test-controller-response.json#/oneOf/4` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse6` | `status` | `compliance/comply-test-controller-response.json#/oneOf/5` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse7` | `status` | `compliance/comply-test-controller-response.json#/oneOf/6` | `completed` | nothing | required |
| THEIRS | invented-value | `compliance.comply_test_controller_response.ComplyTestControllerResponse8` | `status` | `compliance/comply-test-controller-response.json#/oneOf/7` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.calibrate_content_response.CalibrateContentResponse1` | `status` | `content-standards/calibrate-content-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.calibrate_content_response.CalibrateContentResponse2` | `status` | `content-standards/calibrate-content-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.create_content_standards_response.CreateContentStandardsResponse` | `status` | `content-standards/create-content-standards-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `content_standards.create_content_standards_response.CreateContentStandardsResponse1` | `status` | `content-standards/create-content-standards-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.create_content_standards_response.CreateContentStandardsResponse2` | `status` | `content-standards/create-content-standards-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.get_content_standards_response.GetContentStandardsResponse1` | `status` | `content-standards/get-content-standards-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.get_content_standards_response.GetContentStandardsResponse2` | `status` | `content-standards/get-content-standards-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.get_media_buy_artifacts_response.GetMediaBuyArtifactsResponse1` | `status` | `content-standards/get-media-buy-artifacts-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.get_media_buy_artifacts_response.GetMediaBuyArtifactsResponse2` | `status` | `content-standards/get-media-buy-artifacts-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.list_content_standards_response.ListContentStandardsResponse` | `status` | `content-standards/list-content-standards-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `content_standards.list_content_standards_response.ListContentStandardsResponse1` | `status` | `content-standards/list-content-standards-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.list_content_standards_response.ListContentStandardsResponse2` | `status` | `content-standards/list-content-standards-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.update_content_standards_response.UpdateContentStandardsResponse` | `status` | `content-standards/update-content-standards-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `content_standards.update_content_standards_response.UpdateContentStandardsResponse1` | `status` | `content-standards/update-content-standards-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.update_content_standards_response.UpdateContentStandardsResponse2` | `status` | `content-standards/update-content-standards-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.validate_content_delivery_response.ValidateContentDeliveryResponse1` | `status` | `content-standards/validate-content-delivery-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `content_standards.validate_content_delivery_response.ValidateContentDeliveryResponse2` | `status` | `content-standards/validate-content-delivery-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `core.assets.daast_tracker_asset.MacroDeclaration` | `location` | `core/assets/daast-tracker-asset.json#/properties/macro_declarations/items` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `core.assets.pixel_tracker_asset.MacroDeclaration` | `location` | `core/assets/pixel-tracker-asset.json#/properties/macro_declarations/items` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `core.assets.url_asset.MacroDeclaration` | `location` | `core/assets/url-asset.json#/properties/macro_declarations/items` | `null` | nothing | required |
| THEIRS | invented-value | `core.assets.vast_tracker_asset.MacroDeclaration` | `location` | `core/assets/vast-tracker-asset.json#/properties/macro_declarations/items` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `core.audience_evidence_requirements.MaximumAge` | `unit` | `core/audience-evidence-requirements.json#/properties/maximum_age` | `null` | nothing | required |
| THEIRS | invented-value | `core.media_buy_frequency_cap.MediaBuyFrequencyCap` | `max_impressions` | `core/media-buy-frequency-cap.json#` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `core.package_signal_targeting_groups.PackageSignalTargetingGroups` | `operator` | `core/package-signal-targeting-groups.json#` | `all` | nothing | not-declared-here |
| THEIRS | invented-value | `core.product_audience_evidence_requirements.MaximumAge` | `unit` | `core/product-audience-evidence-requirements.json#/properties/maximum_age` | `null` | nothing | required |
| THEIRS | invented-value | `core.protocol_envelope.ProtocolEnvelope` | `status` | `core/protocol-envelope.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `core.rights_attestation_evaluation.Reference` | `issuer` | `core/rights-attestation-evaluation.json#/properties/reference` | `null` | nothing | required |
| THEIRS | invented-value | `core.rights_attestation_evaluation.Reference` | `subject` | `core/rights-attestation-evaluation.json#/properties/reference` | `null` | nothing | required |
| THEIRS | invented-value | `core.rights_constraint.AttestationRef` | `issuer` | `core/rights-constraint.json#/properties/attestation_refs/items` | `null` | nothing | required |
| THEIRS | invented-value | `core.rights_constraint.AttestationRef` | `subject` | `core/rights-constraint.json#/properties/attestation_refs/items` | `null` | nothing | required |
| THEIRS | invented-value | `core.tasks_list_response.TasksListResponse` | `status` | `core/tasks-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.audit_observation.CreativeAuditObservation` | `code` | `creative/audit-observation.json#` | `OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.audit_observation.CreativeAuditObservation` | `recovery` | `creative/audit-observation.json#` | `informational` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.audit_observation.CreativeAuditObservation` | `severity` | `creative/audit-observation.json#` | `audit-worthy` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.get_creative_delivery_response.GetCreativeDeliveryResponse` | `status` | `creative/get-creative-delivery-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.get_creative_features_response.GetCreativeFeaturesResponse1` | `status` | `creative/get-creative-features-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.get_creative_features_response.GetCreativeFeaturesResponse2` | `status` | `creative/get-creative-features-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.list_creative_formats_response.ListCreativeFormatsResponseCreativeAgent` | `status` | `creative/list-creative-formats-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.list_creatives_response.ListCreativesResponse` | `status` | `creative/list-creatives-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.list_creatives_response.Purge` | `kind` | `creative/list-creatives-response.json#/properties/creatives/items/properties/purge` | `soft` | nothing | required |
| THEIRS | invented-value | `creative.list_transformers_response.ListTransformersResponseCreativeAgent` | `status` | `creative/list-transformers-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `creative.preview_creative_response.PreviewCreativeResponse1` | `status` | `creative/preview-creative-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.preview_creative_response.PreviewCreativeResponse2` | `status` | `creative/preview-creative-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.preview_creative_response.PreviewCreativeResponse3` | `status` | `creative/preview-creative-response.json#/oneOf/2` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.sync_creatives_response.SyncCreativesResponse1` | `status` | `creative/sync-creatives-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.sync_creatives_response.SyncCreativesResponse2` | `status` | `creative/sync-creatives-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `creative.validate_input_response.ValidateInputResponse` | `status` | `creative/validate-input-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `error_details.agent_permission_denied.AgentPermissionDeniedDetails` | `reason` | `error-details/agent-permission-denied.json#` | `sandbox_only` | nothing | not-declared-here |
| THEIRS | invented-value | `governance.get_plan_audit_logs_response.GetPlanAuditLogsResponse` | `status` | `governance/get-plan-audit-logs-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `governance.sync_plans_response.SyncPlansResponse` | `status` | `governance/sync-plans-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.accept_proposal_response.Warning` | `code` | `media-buy/accept-proposal-response.json#/allOf/0/oneOf/0/properties/warnings/items` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.build_creative_response.BuildCreativeResponse1` | `status` | `media-buy/build-creative-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.build_creative_response.BuildCreativeResponse2` | `status` | `media-buy/build-creative-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.build_creative_response.BuildCreativeResponse3` | `status` | `media-buy/build-creative-response.json#/oneOf/2` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.build_creative_response.BuildCreativeResponse4` | `status` | `media-buy/build-creative-response.json#/oneOf/3` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.build_creative_response.BuildCreativeResponse5` | `status` | `media-buy/build-creative-response.json#/oneOf/4` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.buy_products_response.Warning` | `code` | `media-buy/buy-products-response.json#/allOf/0/oneOf/0/properties/warnings/items` | `null` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.create_media_buy_response.CreateMediaBuyResponse1` | `status` | `media-buy/create-media-buy-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.create_media_buy_response.CreateMediaBuyResponse2` | `status` | `media-buy/create-media-buy-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.decline_proposals_response.DeclineProposalsResponse2` | `task_id` | `media-buy/decline-proposals-response.json#/anyOf/1` | `null` | nothing | required |
| THEIRS | invented-value | `media_buy.get_media_buy_delivery_response.GetMediaBuyDeliveryResponse` | `status` | `media-buy/get-media-buy-delivery-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.get_media_buys_response.GetMediaBuysResponse` | `status` | `media-buy/get-media-buys-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.list_creative_formats_response.ListCreativeFormatsResponse` | `status` | `media-buy/list-creative-formats-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `media_buy.log_event_response.LogEventResponse1` | `status` | `media-buy/log-event-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.log_event_response.LogEventResponse2` | `status` | `media-buy/log-event-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.media_buy_commitment_response.Warning` | `code` | `media-buy/media-buy-commitment-response.json#/oneOf/0/properties/warnings/items` | `null` | nothing | required |
| THEIRS | invented-value | `media_buy.provide_performance_feedback_response.ProvidePerformanceFeedbackResponse1` | `status` | `media-buy/provide-performance-feedback-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.provide_performance_feedback_response.ProvidePerformanceFeedbackResponse2` | `status` | `media-buy/provide-performance-feedback-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.refine_proposals_response.RefineProposalsResponse2` | `task_id` | `media-buy/refine-proposals-response.json#/anyOf/1` | `null` | nothing | required |
| THEIRS | invented-value | `media_buy.request_proposals_response.RequestProposalsResponse4` | `task_id` | `media-buy/request-proposals-response.json#/anyOf/3` | `null` | nothing | required |
| THEIRS | invented-value | `media_buy.sync_audiences_response.SyncAudiencesResponse1` | `status` | `media-buy/sync-audiences-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.sync_audiences_response.SyncAudiencesResponse2` | `status` | `media-buy/sync-audiences-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.sync_catalogs_response.SyncCatalogsResponse2` | `status` | `media-buy/sync-catalogs-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.sync_event_sources_response.SyncEventSourcesResponse1` | `status` | `media-buy/sync-event-sources-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.sync_event_sources_response.SyncEventSourcesResponse2` | `status` | `media-buy/sync-event-sources-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.update_media_buy_response.UpdateMediaBuyResponse1` | `status` | `media-buy/update-media-buy-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `media_buy.update_media_buy_response.UpdateMediaBuyResponse2` | `status` | `media-buy/update-media-buy-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `property.create_property_list_response.CreatePropertyListResponse` | `status` | `property/create-property-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `property.delete_property_list_response.DeletePropertyListResponse` | `status` | `property/delete-property-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `property.get_property_list_response.GetPropertyListResponse` | `status` | `property/get-property-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `property.list_property_lists_response.ListPropertyListsResponse` | `status` | `property/list-property-lists-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `property.update_property_list_response.UpdatePropertyListResponse` | `status` | `property/update-property-list-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `property.validate_property_delivery_response.ValidatePropertyDeliveryResponse` | `status` | `property/validate-property-delivery-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `protocol.get_adcp_capabilities_response.GetAdcpCapabilitiesResponse` | `status` | `protocol/get-adcp-capabilities-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `protocol.get_principal_response.GetPrincipalResponse` | `status` | `protocol/get-principal-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `protocol.list_tasks_response.ListTasksResponse` | `status` | `protocol/list-tasks-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `protocol.sync_agent_notification_configs_response.SyncAgentNotificationConfigsResponse` | `status` | `protocol/sync-agent-notification-configs-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `protocol.sync_principal_response.SyncPrincipalResponse` | `status` | `protocol/sync-principal-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `signals.activate_signal_response.ActivateSignalResponse1` | `status` | `signals/activate-signal-response.json#/oneOf/0` | `completed` | nothing | required |
| THEIRS | invented-value | `signals.activate_signal_response.ActivateSignalResponse2` | `status` | `signals/activate-signal-response.json#/oneOf/1` | `completed` | nothing | required |
| THEIRS | invented-value | `signals.get_signals_response.GetSignalsResponse` | `status` | `signals/get-signals-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `sponsored_intelligence.si_get_offering_response.SiGetOfferingResponse` | `status` | `sponsored-intelligence/si-get-offering-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `sponsored_intelligence.si_initiate_session_response.SiInitiateSessionResponse` | `status` | `sponsored-intelligence/si-initiate-session-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `sponsored_intelligence.si_send_message_response.SiSendMessageResponse` | `status` | `sponsored-intelligence/si-send-message-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `sponsored_intelligence.si_terminate_session_response.SiTerminateSessionResponse` | `status` | `sponsored-intelligence/si-terminate-session-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `trusted_match.context_match_response.ContextMatchResponseRouterPublisher` | `status` | `trusted-match/context-match-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `trusted_match.identity_match_response.IdentityMatchResponseRouterPublisher` | `status` | `trusted-match/identity-match-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `trusted_match.provider_context_match_response.ContextMatchResponseProviderRouter` | `status` | `trusted-match/provider-context-match-response.json#` | `completed` | nothing | not-declared-here |
| THEIRS | invented-value | `trusted_match.provider_identity_match_response.IdentityMatchResponseProviderRouter` | `status` | `trusted-match/provider-identity-match-response.json#` | `completed` | nothing | not-declared-here |
