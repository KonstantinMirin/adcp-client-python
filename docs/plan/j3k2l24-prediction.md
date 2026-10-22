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

Filled in after the measurement. (See "Graded" below.)
