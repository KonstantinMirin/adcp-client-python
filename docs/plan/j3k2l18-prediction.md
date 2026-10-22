# salesagent-j3k2l.18 — the `allOf` shapes step 4's row defers

Started from `00c7dd4d47bf7fa6cb6eff1d14be8134febabff8` (`emit/from-scratch`), clean.
Baseline, re-measured in this tree rather than quoted: `emit` over all 1,054 portable
documents gives **401 emitted + 653 refused = 1,054**.

## 1. The population, measured before anything was built

The ticket says 65 documents and `41 / 15 / 9`. At this sha it is **67**, and the
split by POSITION is `41 / 10 / 16`. Both numbers are reported with the classifier
that produced them, because the ticket's did not travel with one:

* **root** — the refusal's pointer is `""`.
* **property** — the pointer is exactly `/properties/<key>`.
* **nested** — anything else (`/oneOf/0`, `/properties/x/items`, `/definitions/y`, …).

The 67 are every document `emit` refuses with keyword `allOf` and the deferral
detail `this step lowers no such keyword (a later D2 row does)` — i.e.
`compiler.check_keywords`, not `lower.product`'s own refusal. (A 68th document
refuses on `allOf` with a real reason: `VendorPricing is not a class, so it cannot
be a base`. It is not this population.)

### By position and by WHAT THE CONJUNCTS ARE

| n | position | the set of conjunct kinds at that node |
|---|---|---|
| 33 | root | bare `$ref` (a base) |
| 4 | property | bare `$ref` (a base) |
| 4 | property | a rule keyword: `if`,`then` |
| 3 | nested | a rule keyword: `else`,`if`,`then` |
| 3 | nested | a rule keyword: `else`,`if` + a rule keyword: `if`,`then` |
| 2 | nested | a rule keyword: `not` + bare `$ref` |
| 2 | nested | bare `$ref` (a base) |
| 2 | nested | a rule keyword: `if`,`then` |
| 2 | root | a rule keyword: `not` + bare `$ref` |
| 2 | root | a rule keyword: `if`,`then` + bare `$ref` |
| 1 | nested | a composition: `anyOf` + a rule keyword: `if`,`then` |
| 1 | nested | bare `$ref` + inline with `properties` |
| 1 | nested | a composition: `anyOf` + a rule keyword: `not` |
| 1 | nested | a rule keyword: `if`,`then` + bare `$ref` |
| 1 | root | a rule keyword: `if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` + a rule keyword: `if`,`then` |
| 1 | root | a rule keyword: `else`,`if`,`then` + `if`,`then` + `not` |
| 1 | property | bare `$ref` + inline `properties` + `additionalProperties`,`allOf` |
| 1 | property | bare `$ref` + inline with `properties` |

### Which ROW claims each refusing document

| n | position | claiming selector |
|---|---|---|
| 41 | root | `union_root` |
| 11 | nested | `union_root` |
| 10 | property | `is_object_root` |
| 3 | nested | `is_object_root` |
| 2 | nested | `composes_at_the_root` |

**All 41 root refusals are `union_root`'s.** Not one is `composes_at_the_root`'s:
that selector excludes a root carrying `oneOf`/`anyOf`, and `union_root` excludes
nothing, so a root carrying BOTH keywords is the union row's and `lower_union`'s
keyword screen refuses it on `allOf`. The deferral message is wrong about who defers
— step 4's row was never going to see these.

What the 41 compose: **37 conjuncts reference `core/version-envelope.json`** and
**33 reference `core/protocol-envelope.json`**. These are D7's envelope strata, on
the task-response documents D7 names.

**32 of the 41 have `allOf` as their ONLY live root conjunct** — 30 declare
`properties: {}` (present and empty) and 2 declare no `properties` at all. So for 32
documents the root `allOf` is the single thing between them and emitting.

## 2. THE UNIT, chosen from where the nodes sit

Three positions, two units, and **neither is a `ROWS` row**:

* **A nested or property-position `allOf` (26 documents) is not a root**, so it has
  no row and no selector — the bead's own note. The unit is **one arm on
  `emit._decide`**, beside the `$ref`, `enum`, typeless, null, multi-type, object,
  array and scalar arms, delegating to the lowering step 4 already has.
  `lower.product.lower_root` is already position-neutral: it takes `(doc, name,
  pointer, mod)`, reads the pointer, and `declare_object` names the node it is given.
  Nothing new is built; the function is renamed `lower_composition` because it is no
  longer only a root's.
* **A root `allOf` beside a root union (41 documents)** is a change in
  `lower/union.py`: `allOf` joins `ROOT_CONJUNCTS`, the mechanism that module already
  has for `properties` / `required` / `additionalProperties`.
* `ROWS` stays six rows. `bundle`'s selectors are unchanged.

## 3. WHY the 41 refuse rather than emit, and the probe that decides it

`lower_union` already refuses a root `properties`, `required` or
`additionalProperties`, for a reason about the GRADER and not about a missing
lowering: such a keyword is a conjunction with every branch, a branch class carrying
it states a fact its own `#/<kw>/<i>` node does not, and **there is no JSON pointer to
the conjunction for the branch to name**.

A root `allOf` is in that position exactly. If the conjuncts became bases of the
union base, every branch would inherit them (the branches subclass the base — §4), so
each branch class would carry `adcp_version`, `adcp_major_version`, `status`,
`context`, … while its own `#/oneOf/<i>` node states none of them.

This is a conflict between two parts of the closed plan, so it is measured and not
argued. **PROBE P1:** bind the root `allOf`'s bare-`$ref` conjuncts as bases on the
union base, emit `media-buy/create-media-buy-response.json` (one of the 32), and grade
the pair.

## 4. PREDICTIONS

Written before any code was changed or any probe run.

| # | prediction |
|---|---|
| P1 | The probe reddens. Every BRANCH class of `create-media-buy-response.json` reports `comparison:` with `added` > 0 — one `added` entry per inherited envelope property — and the branch's accepts check reports `model_refused_valid` as well, because `strict_validate` against `#/oneOf/0` draws an instance with no `status` while the class requires one. Two independent checks, both red. The BASE class (naming `#`) grades fine. |
| P2 | So 0 of the 41 emit. All 41 refuse on `allOf`, with `union_root`'s conjunction reason rather than the deferral message. `allOf` goes FIRST in `ROOT_CONJUNCTS`, so the keyword each of the 41 is reported on does not change and the by-keyword refusal profile keeps `allOf` at 68. |
| P3 | Of the 26 property/nested documents, the 8 whose conjunct kinds are a subset of {bare `$ref`, inline with `properties`} reach the lowering. I predict **5 of those 8 emit end to end** and 3 refuse on another keyword elsewhere in their own document. |
| P4 | The other 18 refuse on a non-deferral keyword: `if` for 12, `not` for 3, `anyOf` for 2, `additionalProperties` for 1. |
| P5 | N goes 401 → **406**; refused 653 → **648**; the sum stays 1,054. |
| P6 | `added` stays **0**, `missing` 0, `differs` 0 over the whole graded set. Graded pairs 462 → about **470** (the 5 documents' own classes plus any nested class a composition node declares). |
| P7 | No `ROWS` row is added and no `bundle` selector changes. Rows stay disjoint: 1,033 claimed once, 21 by none, 0 twice. |
| P8 | `tests/test_import_rule.py` stays green: the arm lives in `emit`, which already imports `lower.product`, and `product.py` gains no import. |

## 5. GRADE (filled in after measurement)

<!-- grade -->
