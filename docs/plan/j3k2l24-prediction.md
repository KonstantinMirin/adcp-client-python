# Prediction: reading a branch's type from the node that encloses it

`salesagent-j3k2l.24`. Written and committed BEFORE the change, so the grade at
the bottom is a grade and not a recollection. Graded in this same file
afterwards, naming every prediction that was wrong.

Started from `emit/from-scratch` at `63dc1bb68`, clean.

## What is wrong today

`compiler.lower_object` refuses a node that declares `properties` and no `type`:

> an object node must declare type: object; this one declares '<absent>', so the
> document admits a non-object that no class can represent

It reads the node IN ISOLATION. `core/account-ref.json` declares `type: object`
at its root and the refused node is `/oneOf/0`, a branch of the root's own
combinator. draft-07 applies the root's assertions AND the branch's to the SAME
instance, so the instance a branch class is built for is already an object and
the branch does not need to restate it.

## Measured before predicting

Baseline, over the 1,054 portable documents of `schemas/cache/3.2`, from
`emit.emit(BUNDLE, bundle.portable(BUNDLE))`: **401 emitted + 653 refused =
1,054**.

**44 documents** of those 653 refuse with this detail, not 10. Classified by
whether an enclosing node at the SAME INSTANCE LOCATION constrains the instance
to an object — the hops that preserve the instance location being `allOf/<i>`,
`anyOf/<i>`, `oneOf/<i>`, `then` and `else`:

| | documents |
|---|---|
| the enclosing node constrains the instance to an object (OUR BUG) | **11** |
| nothing does: the node is a property's own schema (GENUINELY LOOSE) | **33** |

The 11 are the bead's 10 plus `media-buy/provide-performance-feedback-request.json`
at `/allOf/1` — a root `allOf`, so the product row rather than the union row.
Every one of the 11 has the constraint on the DOCUMENT ROOT, declared as the
literal `type: "object"`, and every refused node is exactly one combinator hop
below it (`/oneOf/0` ×9, `/anyOf/0` ×1, `/allOf/1` ×1). No deeper chain occurs.

The 33 are all a property's own node — 29 at `/properties/account` or
`/properties/<name>`, 2 at `.../items`, 1 at `/oneOf/0/properties/activation_key`,
1 at `/properties/accounts/items`. A `properties` hop CHANGES the instance
location, so nothing there says the value is an object and the document really
does admit a non-object. **Those stay refused and are not this lane's work.**

Structural census over the whole bundle, independent of what refuses first:
**1,390 nodes** declare a non-empty `properties` without `type: "object"`; **556**
of them (151 documents) are constrained by an enclosing same-instance node and
**834** (206 documents) are not.

## The change

One derivation, in `codegen/bundle.py` beside `named_nodes`, read off the one
walk (`bundle.nodes`) so no second descent table exists to disagree with it:
the pointers of a document whose instance an ENCLOSING node constrains to
`type: "object"`. `Module` carries that frozenset exactly as it carries `named`,
and `compiler.lower_object` refuses only when the node declares a type that is
not `object`, or declares none AND the set does not hold its pointer.

## Prediction 1 — the refusal at those 11 nodes

All **11** stop refusing on `type` at that pointer. The 33 loose ones refuse
exactly as they do now, same keyword, same pointer.

## Prediction 2 — how many of the 11 then EMIT

Not all 11. The recorded refusal is the FIRST one the document hits, so branch 0
clearing only moves the question to branch 1..n, and these are union roots whose
later branches can be a bare `$ref`, can declare no property, or can carry a
keyword of a later row. **Predicted: between 4 and 9 of the 11 emit**, and N goes
from 401 to between 405 and 410.

## Prediction 3 — the new pairs will NOT be green as they stand

This is the prediction I am least sure of and the one that decides whether the
change is one commit or three.

A branch class renders `type: "object"` in its own `model_json_schema()`, and
the branch NODE states no `type`. The graded document side for that class is
`_base.schema_at(__adcp_schema__)`, a plain pointer walk returning the bare node.
So I predict BOTH of these fire on the new branch pairs:

- **the schema comparison** reports `added` at `/type` — "the model says
  'object', the document nothing" — because `harness._narrows_nothing` sends a
  model-only `type` to `_entails_type`, which decides from the NODE (a `const`,
  or a combinator whose every branch names the type) and the branch node has
  neither. `added` must stay 0, so this would break the invariant.
- **the accepts check** reports `model_refused_valid` on a drawn non-object,
  because the bare node admits one.

Predicted resolution if they fire: the honest reading is that `schema_at` returns
the schema the ref NAMES and a nested node's meaning includes what its enclosing
same-instance ancestors assert about the same instance, so the conjunction
belongs there — one place, and both checks then see one document side. Predicted
risk, named now: conjoining the whole enclosing node would drag in the root's
`properties`, `required` and `description` and move grading for every nested
pair in the tree, which is a plan-level change (§4, D4) and would be reported
rather than taken.

Counter-prediction, the way this could be free: `hypothesis_jsonschema`'s
`canonicalish` infers `type: object` from `properties`/`required`, so the accepts
check may draw only objects and never fire; and the document written beside the
module is `bundle.resolved(...)`, which runs through the same canonicalisation
and may already carry `type: object` on the branch node. If both hold,
predictions 3's two bullets are both **wrong** and the lowering change is the
whole of it. I put this at about even money.

## Prediction 4 — the numbers in `tests/test_emit.py`

The committed tree is regenerated, so the metric constants move. Predicted:
`390` modules goes up by about 2 per emitted document (its own module plus its
`$ref` closure, several of which are already in the tree); `462` graded pairs
goes up by 1 per new root class plus 1 per new branch class, which for 4–9
documents with 2–4 branches each is **+12 to +45**; `450` pass moves with it and
`12 no_constraint_to_step` is unchanged, because a union root states constraints
to step. `added`/`missing`/`differs` stay **0** — if they cannot, prediction 3
decides the shape and this change does not ship with them non-zero.

## Prediction 5 — the disjointness of `emit.ROWS`

Unchanged: **1,033 claimed once, 21 by none, 0 twice**. This lane adds no row and
touches no selector, so every selector is byte-identical. The bead's "add your
keyword to `bundle.declares_its_own_root_kind`" does not apply — the 11 documents
are already claimed by the union row and the product row, and the defect is
inside the lowering those rows call.

## Fire-probe

The new derivation is probed by breaking it on purpose, in both directions: a
document whose root declares `type: object` with a typeless `oneOf` branch must
EMIT and must refuse once the enclosing fact is taken away, and a document whose
branch sits under a `properties` hop must still refuse. The test that reddens if
the distinction is lost grades both halves over the bundle's own 11 and 33.

---

# Grade

Branch `sdk/j3k2l24-branch-root-type`. Three of the five predictions were wrong,
and the one that was right is the one that decided the shape of the change.

| # | prediction | outcome |
|---|---|---|
| 1 | 11 real sites; 33 genuinely loose documents | **WRONG**, in the mechanism and in both counts |
| 2 | 4–9 of them emit; N 401 → 405..410 | **WRONG**: 3 emit, N 401 → 404 |
| 3 | the new pairs are not green: `added` at `/type` and `accepts:model_refused_valid` | **RIGHT**, exactly, and the counter-prediction was wrong |
| 4 | the metric constants move by about these amounts | **WRONG on the sizes**, right that `no_constraint_to_step` and `added` do not move |
| 5 | `ROWS` disjointness unchanged at 1,033 / 21 / 0 | **RIGHT** |

## 1 was wrong, and the way it was wrong is the finding

**The real sites are 10, which is the bead's own figure, and NOT ONE of them is
genuinely loose.** All 10 declare the literal `type: "object"` at their own root,
and every refused node is one combinator hop below it — `/oneOf/0` nine times,
`/anyOf/0` once.

The other 34 documents carrying that refusal detail are `$ref` **chain**
refusals: they reference one of the 10, and `emit.emit`'s binder re-raises the
target's refusal with the REFERENCE SITE as the pointer. My classifier walked
that pointer in the REFERRING document, found a `properties` hop, and reported 33
of them as "genuinely loose" — and reported
`media-buy/provide-performance-feedback-request.json` at `/allOf/1` as an
eleventh real site, when its `/allOf/1` is a `$ref` whose target refuses.

So the answer to the question the bead asks is: **no document in the measured
population is loose. 0 of 44.** Nothing was forced to emit, and the 8 of the 10
that still refuse do so on another row's keyword, listed in
`tests/test_applied_schema.py::STILL_REFUSED`.

Measured once the fix landed, the loose population is empty in a stronger sense:
**no document in the bundle reaches `lower_object`'s type refusal at all** — the
refusal's population went from 10 to 0 — which is why the negative half is graded
on constructed documents and why the suite asserts that emptiness rather than
assuming it.

Two census figures quoted above are also corrected. The split of nodes declaring
a non-empty `properties` without `type: "object"` is **556 constrained / 833 not
/ 1 declaring a type that is not `object`**, not 556 / 834: the earlier count
read "its type is not object" where the live rule reads "it states no type".

## 3 was right, and it is why the change is in two places

The lowering change alone produced **4 red pairs**: `core/activation-key.json`
and `core/reporting-write-destination.json`, both branches each, reporting
`accepts:model_refused_valid` and one `added` fact — `/type: the model says
'object', the document nothing`. `added` must stay 0, so that was not shippable.

The counter-prediction, at "about even money", was **wrong in both halves**:
`resolve_all_refs` leaves the branch nodes typeless, and
`hypothesis_jsonschema` drew a non-object against them.

The cause is one level above the check. `_base.schema_at` resolved a `SchemaRef`
by a bare pointer walk, so the schema a branch class NAMED was the branch read
alone — which admits a string. Given that schema the old refusal was CORRECT: a
class there really would have been narrower than the schema it names. So
"the check reads the branch in isolation" is true of the check and also of the
resolution the check's verdict has to agree with, and fixing only the check turns
one defect into four.

`applied_schema` is therefore where the rule lives: one function, in the package,
spelling which pointer hop carries an enclosing assertion. `schema_at` resolves
through it and `codegen.bundle.constrained_to_object` derives the emitter's
answer from it, so the two halves cannot come to disagree — a divergence there
would be the emitter admitting a node whose class is narrower than its own
schema, silently.

After it: **472 pairs, 460 pass, 12 `no_constraint_to_step`, 0 anything else,
`added`/`missing`/`differs` all 0.**

## 4: the sizes

`390 → 393` modules and not the +6 predicted — each of the three documents'
`$ref` closure was already in the tree. `462 → 472` graded pairs, below the
predicted +12..+45: three documents of two branches each is 3 bases + 6 branches
+ 1 nested class. `compared` 4,658 → 4,757, model-only facts 1,104 → 1,116,
`url_typed` 72 → 74, `graded_instances` 36,419 against a floor of 34,900.

## What the design did not take into consideration

D4 and §4 fix the pairing at `(document, JSON pointer)` and say a nested class
"answers for its own node rather than the whole document". Neither D1–D14 nor §4
says how that pointer is RESOLVED, and the bare walk it got is not the schema the
document applies at that pointer: under a combinator, draft-07 applies the
enclosing node's assertions to the same instance. For every class emitted before
this lane the two coincided — each one either declares its own `type` or sits
under a `properties` hop — so the gap was latent, and §4's union branches are the
first population to reach it.

This is not a re-decision of a D. Nothing was added that the design does not
have: no pre-pass, no document rewritten, no flag, no table, and no new artifact.
`Module` carries a per-document frozenset of pointers derived from the bundle,
which is exactly what `Module.named` already is, and `schema_at` is the same
function it was with the walk reading one more fact. What the design should say,
and does not, is that a `SchemaRef` names a node AS THE DOCUMENT APPLIES IT —
because the alternative reading makes a correct class unbuildable at every
combinator branch whose root carries the type.

## Fire-probe

Five perturbations, each run against the suite and each reddening a named test,
with the tree verified clean after every restore:

| perturbation | reddens |
|---|---|
| `if` becomes a same-instance hop | the populations, the `if` case, the schema-fact check, the inheritance check |
| `then`/`else` stop being one | the populations, the schema-fact check, the inheritance check |
| the inherited assertion is never cleared (any hop carries) | the above plus the `properties`-hop case |
| the enclosing type overwrites the node's own | the contradiction case |
| `lower_object` reads the node alone again | the 3-emitted case, both perturbation cases, the refusal-is-empty case |
| `schema_at` returns the bare node again | the class case, and `test_the_step_result_is_counted_over_the_whole_population` |

## The suite

`python -m pytest tests -q -n 3`, at `-n 3` rather than the `addopts` default
because four lanes at ten workers each get killed by the OOM killer:

```
633 passed in 578.86s (0:09:38)
```

611 before, 633 after: 12 are this lane's new module and 10 are parametrised
cases that scale with the tree.

## Is this in line with the design

Asked as a question because the answer is a judgement and the brief says to stop
rather than improvise. Nothing was added that D1–D14 does not already have:

- no pre-pass, no document rewritten on disk, no flag, no table, no allowlist,
  no new artifact in the package, and no new row — `emit.ROWS` and every selector
  in `codegen.bundle` are byte-identical, and the partition is still 1,033 / 21 / 0;
- `Module` carries a per-document frozenset of pointers derived from the bundle,
  which is what `Module.named` already is (`bundle.named_nodes`), read the same
  way and empty by the same default;
- `schema_at` is the function it was, resolving the same `SchemaRef`, with the
  walk reading one more fact on the way down.

What it does change is what `schema_at` RETURNS for a node under a combinator,
and that is a change to the runtime contract rather than to a build-time
detail — so it is named here rather than buried. The smaller change, the check
alone, is not merely less elegant: it is wrong, and the measurement is the 4 red
pairs above. Given a bare-node schema the old refusal was CORRECT, so a fix that
admits the node without fixing the resolution ships a class narrower than the
schema it names — which is the relaxation the brief forbids, arrived at from the
other side.
