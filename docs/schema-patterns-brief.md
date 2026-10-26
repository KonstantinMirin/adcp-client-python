# What costs us most in the schema — the 60-second version

Bundle **3.2**, measured over its **1,054 portable documents**. We emit **769** typed modules
and refuse **285**. Of those 285, **176 are verdicts** — the obstruction is in the document or in
draft-07 — and **109 are ours**, code we have not written. Only the 176 are about the schema.

Every figure below says what population it is over. The long version is
`docs/schema-patterns-that-resist-generation.md`.

---

## 1. A plain keyword beside a `oneOf` — 134 of the 285 refusals

**47% of everything we refuse**, from 75 sites: 107 at a document root, 27 nested.

Draft-07 applies a root's own keywords to *every* branch, so the conjunction has no pointer of
its own. A branch class either carries a fact its own node does not state, or drops one. We
refuse rather than guess.

```json
{ "type": "object",
  "additionalProperties": true,      ← applies to every branch, names no pointer
  "oneOf": [ {...}, {...} ] }
```

**The illustration, and the cheapest fix in the whole list.** In
`core/format-option-ref.json` that root `additionalProperties: true` is **already restated
verbatim by both branches**. Deleting the root line cannot change what the document accepts —
and it unblocks **14 documents**.

---

## 2. Branches a reader cannot tell apart

We derive which branch a payload is from the bundle, never from a hand-written map — a map is
complete with respect to itself, so a branch added upstream leaves it silently wrong. Three
sources: a shared `const`, the manifest, or provable disjointness. A union matching none refuses.

**The illustration.** `adagents.json` has two `oneOf` branches, both bare `type: object` with
overlapping properties and nothing separating them. Meanwhile `core/creative-manifest.json`
already writes the idiom that would fix it:

```json
"oneOf": [ { "not": {"required": ["format_kind"]} },
           { "not": {"required": ["format_id"]} } ]
```

Each branch forbids a name the other requires, so disjointness is provable. **The fix is a
copy from elsewhere in your own bundle.**

---

## 3. `allOf: [{"$ref": …}]` used to attach a description — 66 refusals

Wrapping a `$ref` in an `allOf` to hang a `description` beside it only exists because draft-07
**ignores siblings of `$ref`**. When the target is not an object, there is no class to extend,
and the wrapper becomes a composition over something uncomposable.

This one is **ours to absorb**, not yours to fix — but it is worth knowing that a workaround for
a draft-07 hole is our third-largest refusal class.

---

## 4. A conjunct that restates a property neither identically nor narrowly

`allOf` means every conjunct holds, so a restated property must intersect. A restatement that
widens, or that changes the type, admits payloads a conjunct refuses — we refuse instead of
emitting a model looser than its document.

**The illustration.** One pointer in `url-asset.json` accounts for **13 refusals**.

---

## 5. The refusals are not where the ergonomic cost is

This is the part that does not show up as a refusal at all. Measured on the **committed emitted
tree**:

- **85 of 160** constraint aliases are named by a **hex digest of a regex**, because the schema
  names the pattern nowhere. A currency field reads:

  ```python
  currency: Annotated[StrMatching43E30B32, Field(description='ISO 4217 currency code')]
  ```

  in **20 modules**. The description knows what it is. The type cannot say so.

- **38 fields are `dict[str, Any]`** — an object with no `properties` can only become a mapping,
  and every name inside it is lost to the consumer.

A `title` on a pattern, or declared `properties` on an object, turns each of these into a named
type at no cost to what the document accepts.

---

## The one rule behind all of it

**A model may be looser than its document, never tighter.** The document decides what the
protocol accepts; the model is a convenience over it. So where a pattern can only be rendered by
narrowing, we refuse it instead of silently accepting less than you specified. That is why a
cheap schema change often converts a refusal into a *named type* rather than into `Any` — and
why the four items above are worth more than their line counts suggest.

**Four different asks, which is why the long note tags every theme.** Items 1, 2 and 4 are
schema-side and keep the accepted set identical. Item 5 is a schema-side *statement*, not a
rewrite. Item 3 is ours.
