# Prediction: making the schema comparison read a root `allOf`

Written and committed BEFORE the fix, so the grade below is a grade and not a
recollection. Graded in the same file afterwards.

## What is being changed

`codegen.harness.compare_schema` walks the document's own `properties`, `items`
and `FACTS` keys. It does not descend into `allOf`. A subclass's
`model_json_schema()` flattens every inherited field into its own `properties`
and its own `required`, so a faithful composing class reads as stating facts its
document does not state, and the facts a conjunct DOES state are compared
against nothing.

## Prediction 1 — how many of the 44 pairs move

**Zero.**

Measured before predicting, because the number is a property of the committed
tree and not of the fix: `graded()` is 44 pairs, and over the documents those 44
pairs name there are **0 `allOf` nodes at any position** (root or nested).
`src/adcp/types/_schemas` carries 43 JSON documents and none of them contains the
string `allOf`. The population the committed tree is emitted from is step 1's
leaf objects plus step 2's property-referencing documents; a document whose root
composes is refused today and arrives with step 4.

So the existing 44 pairs cannot grade this fix in either direction, and a
perturbation of the new code will redden none of them. That is a finding about
the test set, not a licence to ship ungraded: the four cases below are added as
tests and they are the graders.

## Prediction 2 — which of the four cases the current code already catches

| # | case | predicted outcome TODAY | predicted after |
|---|---|---|---|
| 1 | model states a constraint the document states nowhere — not root, not a conjunct, not a `$ref` target | `model_adds_a_fact` — **already right** | `model_adds_a_fact` |
| 2 | model omits a fact the document states in a CONJUNCT | `pass` — **wrong, and invisible**: the conjunct is never walked, so the fact is not even counted in `compared` | `model_drops_a_fact`, the fact in `missing` |
| 3 | model's inherited field disagrees with the conjunct's `maximum: 99` by stating `100` | **reported, but mislabelled**: the root declares no such property, so the model's property reads as `added` and the outcome is `model_adds_a_fact`. The `maximum` itself is compared against nothing | `model_drops_a_fact`, the `maximum` in `differs` |
| 4 | the faithful composing class | `model_drops_a_fact` — **wrong**: `/required` differs (root says `['label']`, the model says `['kind','label']`) and `/properties/kind` reads as added | `pass` |

So: 1 of the 4 right outright, 1 right-for-the-wrong-reason with the wrong
label, 2 wrong. The delta the fix has to produce is 3 rows, and case 1 is the row
that must NOT move.

## Prediction 3 — the shape of the fix

A conjunct's unconditional facts ARE the document's, so the document side is read
through a merged view before it is compared, at EVERY node rather than only the
root (a property's own node can compose too, and applying the view in the
recursion costs nothing extra).

Predicted merge rules:

- `required` composes by **union** — it is a set, and draft-07 conjoins.
- `properties` composes by **key**, recursing into a key declared in more than
  one view with the same rules.
- every other `FACTS` keyword: a conjunct **fills a gap, it never overrides**.
  Predicted cost of that choice: where a node and a conjunct state the same
  ordering keyword with different bounds the effective constraint is the tighter
  one, and this rule would report the looser one as expected — a FALSE FAILURE,
  which is the safe direction, and predicted to occur 0 times in the bundle.
- `if` / `then` / `else` / `not` / `anyOf` / `oneOf` inside a conjunct state
  nothing unconditional and are predicted to need no code at all: none of them is
  in `FACTS`, so a conjunct holding only those contributes nothing by
  construction.

Predicted to be the dominant conjunct shape in the bundle, and therefore the
thing most likely to be wrong about this plan: a bare `{"$ref": ...}` conjunct,
which states no fact of its own. Predicted resolution: the CALLER resolves (the
packaged document is `bundle.resolved`'s output), so a `$ref` conjunct is inline
by the time `compare_schema` sees it. To be confirmed by measurement, not
assumed.

## Prediction 4 — what each perturbation reddens

- dropping the `required` union → case 4 reddens, cases 1-3 unaffected.
- dropping the `properties` merge → cases 2, 3 and 4 redden.
- merging from an `if`/`then` conjunct as if it were unconditional → predicted to
  redden nothing in the four cases, because none of them has one; a fifth case is
  predicted to be needed to grade that choice.
- letting a conjunct override the node → predicted to redden nothing, for the
  same reason the rule costs nothing: no case and no document has the collision.
