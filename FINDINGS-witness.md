# FINDINGS — the witness builder and the 12 ungraded pairs

Measured 2026-11-17 on `claude/witness-builder-draws`. **Every number here is read off
`test-results/gate/before.json` and `test-results/gate/after.json`** (`make gate`,
2,609 pairs), or off the documents' own text quoted inline. Nothing here re-derives a
count from the schemas or the class graph.

    before   14 failed, 2595 passed of 2609      876.4 s
    after     9 failed, 2600 passed of 2609      546.1 s

Five pairs cleared, none newly broken. The five are `core/macro-declaration.json#` and the
four `macro_declarations/items` positions that `$ref` it.

---

## 1. WHAT WAS A BUILDER GAP: the fold was an accumulation and not a fixed point

`codegen/verify/witness.py`'s `_settled` folds the consequent of each conditional the
value's own content selects. Its rule — *"a consequent is folded in only where the value
MATCHES its condition"* — was read in one direction only: a consequent folded on one round
stayed folded (`taken`) even after the value had moved out of its condition.

`core/macro-declaration.json` states **fifteen conditionals over one object**, and they
chain. Round 0 reads `operation` at its own enum's first member (`translate_to_native`) and
`required` at the boolean floor (`true`), which selects

* `allOf/5` — *requires* `performed_by` and `translation_target`, and
* `allOf/11` — `unavailable_behavior` is `reject` by `const`;

`allOf/13` then pins `operation` to `preserve`, which selects `allOf/8` — whose `then` pins
`unavailable_behavior` to `preserve` by `const` and forbids both of those keys by `not`.
With the first two consequents still folded, the value carried `reject` **and** both keys, so the
node refused its own construction on exactly `const, not` — a value satisfying the scenario
it no longer selects and violating the one it does. That is the gate's
`accepts=fail:witness_refused` at five of its six sites; the sixth,
`CreativeRepresentationFormatId`, has a different cause and is §3.

Three changes, all inside `codegen/verify/witness.py`:

* **`_settled` recomputes the whole selected set from the current value each round** and
  rebuilds from `views` plus exactly that set. It terminates on the node's own statements,
  as before and for a sharper reason: the value is a function of the selected set and the
  set a function of the value, so the rounds are a deterministic orbit over the subsets of
  one finite list — it either reaches a set that selects itself, or revisits a set it
  has already built, and *that* is the cycle. `seen` names the back edge the way
  `through`'s own `seen` does. No round budget was added.
* **`_unmet`** reads the other half of draft-07's rule — *if the condition holds then the
  consequent holds* — by asking whether the value is one the consequent it selected admits.
  **`_refuted`** is `_decides` (the three deciders) plus `_unmet`, and it replaces
  `_decides` at the seven sites that were asking half the question. This is what the
  shallow screen cannot answer: `refusals` strikes `oneOf`/`anyOf`/`not` because no child
  can answer them and strikes `allOf` with the rest of the descent column, so a
  consequent's `const` was a fact about this instance that nothing read.
* **`_names` names a violated conditional's keys too**, off both of its halves — the
  consequent names the key it pins, the `if` names the key whose value opened the scope.
  `_recased`'s docstring had *already declared* this case (*"a key whose first `enum`
  member is the member a `not` forbids **or an `if` selects an unsatisfiable consequent
  on**"*); the `if` half was declared and never read.

`core/macro-declaration.json#`'s orbit does not settle — rounds 0–3 each violate something
and round 4 revisits round 1's set. The answer comes from the recase the third change
unlocks: `unavailable_behavior` to its own **fourth** enum member, `reject`, which closes
`allOf/13`'s scope instead of satisfying it. No reading of a `not` could have reached it,
because that node states none.

The builder's contract is unchanged: a witness is still a function of `(document, pointer)`
and nothing else. No corpus, cache, budget, depth cap or example count was added.

---

## 2. NOT A BUILDER GAP: the six `refuses=absent:no_payload` roots

**The premise that "nothing was constructed" at these six is false.** All six are
`accepts=pass`, `examples=1`, `evidence=constructed` in both `before.json` and
`after.json`. The builder answers every one of them; the note is empty because there was
nothing to report, not because there was no value.

What fails is `refuses`, and it fails on the DOCUMENTS, not on the witness. Measured
through `codegen.harness`'s own readers:

| document | assertion keywords at the root | witness | `refusing_payload` |
|---|---|---|---|
| `core/asset-group-vocabulary.json` | **none** | `null` | `None` |
| `core/format-shape-vocabulary.json` | **none** | `null` | `None` |
| `creative/asset-types/index.json` | **none** | `null` | `None` |
| `extensions/index.json` | **none** | `null` | `None` |
| `core/targeting-unknown-age-eligibility-constraint.json` | `if`, `then` | `{}` | `None` |
| `core/targeting-verified-age-basis-constraint.json` | `if`, `then` | `{}` | `None` |

The four registry / vocabulary / index documents carry `$schema` and then only annotations
(`title`, `description`) and their own DATA keys (`vocabulary`, `asset_types`,
`extensions`, `version`, `governance`, …). As schemas they are the empty schema: offered
`null`, `true`, `0`, `""`, `[]`, `{}` and `{"x": 1}`, **the document refuses none of the
seven**. There is no document-invalid payload to find, which is
`test_a_document_that_refuses_nothing_yields_no_payload_rather_than_a_forced_one`'s
deliberate outcome. No witness can change that, because `refusing_payload`'s three
perturbations are each screened by the document before being offered.

The two `if`/`then` constraint documents are the more interesting half, and they are still
not the builder's. They **do** refuse payloads:

```
core/targeting-unknown-age-eligibility-constraint.json
  {"demographics": {"age": {"include_unknown": false}}, "age_restriction": {}}   conforms
  {"demographics": {"age": {"include_unknown": true}},  "age_restriction": {}}   refused on const

core/targeting-verified-age-basis-constraint.json
  {"demographics": {"age": {"accepted_bases": ["verified"]}},
   "age_restriction": {"verification_required": true}}                           conforms
  {"demographics": {"age": {"accepted_bases": ["self_declared"]}},
   "age_restriction": {"verification_required": true}}                           refused on contains
```

But `refusing_payload` derives its refusal from an admitted payload by exactly three
perturbations — drop a key the **root** `required` names, replace the instance with another
JSON type, add an undeclared property — and neither document states a root `required` or a
root `type`, so all three conform. `refusing_payload(…, admitted)` is `None` even when
handed the richer conforming payload above, which is measured and not assumed.

**So the gap is in the derivation, not in the witness.** What would close these two is a
fourth perturbation that negates a `const`/`contains` the consequent the payload SELECTS
pins — the same reading `_unmet` now performs on the construction side. That lives in
`codegen/harness.py::refusing_payload`, which this lane may not write; the four
unconstrained registry roots are not closable at all and want a decision from the owner
about what `refuses` should say for a document that asserts nothing.

---

## 3. AN EMISSION DEFECT, NOT A BUILDER GAP: `CreativeRepresentationFormatId`

`core/creative-representation.json#/allOf/0` stamps **two** classes, and they do not share
a verdict: `CreativeRepresentationFormatKind` passes the contract, and
`CreativeRepresentationFormatId` fails it identically in `before.json` and `after.json`
(`accepts=fail:witness_refused … on not … at allOf/1/not, allOf/5/not`).

**Its subject admits nothing, and the two documents say so in their own words.**
`core/creative-representation.json#/allOf/0` is a `$ref` to `core/creative-manifest.json`,
whose `oneOf` is the v1/v2 addressing choice:

    core/creative-manifest.json#/oneOf/0   "Named-format manifest"      required: ["format_id"]
    core/creative-manifest.json#/oneOf/1   "Canonical-format manifest"  required: ["format_kind"]

and `core/creative-representation.json` states, at its own root and at `allOf/1`:

    required: ["representation_id", "source", "format_kind"]
    allOf[1]: {"required": ["format_kind"],
               "not": {"anyOf": [{"required": ["format_id"]},
                                 {"required": ["format_option_ref"]},
                                 {"required": ["representation_selection"]}]}}

`CreativeRepresentationFormatId` is `oneOf/0` distributed into that node, so its subject
**requires `format_id` and forbids `format_id`**. That is empty by inspection, not by
search: `{"allOf": [{"required": ["format_id"]}, {"not": {"anyOf": [{"required":
["format_id"]}]}}]}` is valid for no instance. It is why the harness also reports *"the
document admits none of the 425 classes the construction builds over this"* — an empty
subject has no witness and no witness set, and the builder is right to have none.

Per the task this is reported and **not fixed**: the repair is to stop emitting a class for
a branch the referring document closes, which is `codegen/lower/` or the emission, both
outside this lane. `core/creative-representation.json` is one of the seven documents
`CLAUDE.md` lists as stating a deprecated-but-present `format_id`, so the branch itself is
not the error — distributing it into a node whose `not` forbids it is.

---

## 4. ALREADY-REPORTED EMISSION DEFECTS: the two `account` pairs

`media-buy/buy-products-request.json#/anyOf/1/properties/account` and
`media-buy/request-proposals-request.json#/anyOf/1/properties/account` fail
`accepts=fail:model_refused_valid` in both reports, unchanged. The gate's own note is the
whole finding: the document admits `{"brand": {"domain": "a"}, "operator": "a"}` and
`BuyProductsRequestAccountAccountAccountId` / `RequestProposalsRequestAccountAccountAccountId`
refuse it with *"account_id Field required"* — the class is **narrower than its document**
at `('account_id',)`. The witness is correct and the class is not; nothing here touches it.

---

## The nine that remain

| pair | why it is not a witness gap |
|---|---|
| 4 × registry / vocabulary / index roots | the document asserts nothing, so it refuses nothing — §2 |
| 2 × targeting `if`/`then` constraints | `refusing_payload`'s three perturbations cannot reach what the document refuses — §2 |
| `CreativeRepresentationFormatId` | the subject requires and forbids `format_id` — §3 |
| 2 × `…/properties/account` | the class is narrower than its document — §4 |
