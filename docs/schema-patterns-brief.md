# What costs us most in the schema — the 60-second version

Bundle **3.2**, over its **1,054 portable documents**. Every figure here is a population of the
bundle — sites, documents, distinct spellings — and names the population it is over. None is a
count of what our generator refuses, because a refusal count measures our unwritten code and the
schema at once and separates neither.

**Two asks, both filed. Neither changes what any document accepts.**

| | Ask | Population | Effort |
| --- | --- | --- | --- |
| [#8525][] | Name the shapes the bundle repeats, and `$ref` them | 110 patterns, 830 sites, 10 titled | patch prepared, 5 of 110 |
| [#8516][] | Give the failed-response envelope one spelling | 26 documents, 12 spellings | one new document, 26 edits |

The long version, with ten themes and a tag for whose problem each is, is
`docs/schema-patterns-that-resist-generation.md`.

---

## 1. Name the shapes the bundle repeats — [#8525][]

**The problem.** The bundle declares the same subschema over and over without ever naming it:
**110 distinct patterns across 830 sites, and only 10 carry a `title`.** A generator can see that
83 sites share one regex; it cannot know the regex means "ISO 4217 currency code", so it names the
type after a hash of the pattern.

**What it costs a consumer today.** **The hex digest is gone and the ask is not.** Until
2026-11-04 a currency field read `Annotated[StrMatching43E30B32, ...]`, and
`rebuild-plan.md` §4 now rules a digest a defect: a name must say what the type constrains.
§3a's layer L1 collects the constrained scalars over the bundle and §4's three ordered steps
name each one, so what a consumer imports today is a name — and **63 of the layer's 236
constraints take it from the POSITION THAT DECLARES THEM, because the bundle names their
subject nowhere or names it differently at different sites**:

```python
currency: Annotated[
    GetAccountFinancialsResponseSuccessCurrency,       # 86 positions, 62 documents
    Field(description='ISO 4217 currency code'),
]
```

That is a name a reader can follow to a position, and it is still not the name the field
wants. **This ask is what closes the gap**: a titled `core/currency-code.json` moves the
entry from §4's step 3 to its step 1 and the symbol becomes `CurrencyCode` — derived from
the bundle, at every one of the 86 sites, with nothing minted here. The 63 are the
population, over **752 positions in 322 documents**.

The figure this paragraph used to carry — 85 of 160 aliases digest-named — was a reading of
an older tree; at `f3b369d7` it was 114 of 228, and it is now 0 of 228.

Separately, **38 fields are `dict[str, Any]`**, because an object with no declared
`properties` can only become a mapping, and every name inside it is lost.

**The change.** Extract each repeated subschema into its own titled document and `$ref` it. We
have prepared the first five, covering **307 sites over 200 documents** — `patches/8525/` in this
repository, ready to open as a PR against the bundle:

| New document | Title | Sites | Documents |
| --- | --- | --- | --- |
| `core/currency-code.json` | Currency Code | 83 | 60 |
| `core/country-code.json` | Country Code | 65 | 45 |
| `core/idempotency-key.json` | Idempotency Key | 59 | 59 |
| `core/domain-name.json` | Domain Name | 54 | 43 |
| `core/https-url.json` | HTTPS URL | 46 | 31 |

**Two sites are deliberately held apart**, which is the part a bulk rewrite would get wrong.
`core/flight-item.json`'s `origin.airport_code` and `destination.airport_code` match the currency
regex exactly — three uppercase letters — and mean an IATA airport code. They keep their own
declaration. Ten further sites are held apart from the idempotency key for the same reason:
identical constraint, different meaning. **Naming the shape is what makes that distinction
expressible at all**; today the two are indistinguishable.

**How to verify it changes nothing.** Resolve every `$ref` the patch adds and the published
document comes back. We check that over all 1,054 portable documents and the result is **0
differences a validator can act on** — the only deltas are the `title` and `$schema` an extracted
document necessarily gains.

**Please land it on `3.2.x` and `3.3` as well as `main`.** The same backport ask as [#7959][]:
consumers pinned to 3.2 are the ones generating code against it today.

---

## 2. Give the failed-response envelope one spelling — [#8516][]

**The problem.** `{context, errors, ext}` is re-declared inline across **26 documents** in **12
different spellings**. **5 of them omit `errors.minItems`**, so a response that announces failure
may carry an empty `errors` array, and a client that trusts the schema has nothing to show the
user.

**The change.** One named envelope document, composed by all 26, with `errors.minItems: 1`
stated once. This is the same shape as [#8470][] and [#7919][] — the submitted-task envelope —
and fixing them together is cheaper than fixing either alone.

---

## 3. No action needed from you: `allOf: [{"$ref": …}]` to attach a description

Listed only so it is not mistaken for an ask. Wrapping a `$ref` in an `allOf` to hang a
`description` beside it exists because draft-07 **ignores siblings of `$ref`**. It occurs at
**53 sites over 31 documents**, and **50 of the 53** carry `description` and nothing else — so it
is a workaround for a hole in the draft, not a modelling choice, and it disappears on its own
under 2019-09 or later, where `$ref` takes siblings. **Ours to absorb.**

---

## The one rule behind all of it

**A model may be looser than its document, never tighter.** The document decides what the
protocol accepts; the model is a convenience over it, and every emitted class validates a payload
against its own schema document before it constructs anything. A loose annotation therefore costs
static precision and never correctness, while a *tight* one rejects a payload you specified as
valid.

So where a keyword cannot be expressed faithfully, our type **widens**: the fact is dropped,
never substituted, and the gap is declared on the class and attributed. We do not refuse
documents. That is why neither ask above buys us a document that compiles — both buy a **named**
type where there is an `Any` or a digest today, which is worth more than their line counts
suggest.

[#7919]: https://github.com/adcontextprotocol/adcp/issues/7919
[#7959]: https://github.com/adcontextprotocol/adcp/issues/7959
[#8470]: https://github.com/adcontextprotocol/adcp/issues/8470
[#8516]: https://github.com/adcontextprotocol/adcp/issues/8516
[#8525]: https://github.com/adcontextprotocol/adcp/issues/8525
