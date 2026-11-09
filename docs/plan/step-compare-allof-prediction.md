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

---

# The grade

Written after the measurement. Fix at `9361e1b10`, graders at `dd474cdca`.

## Prediction 1 — right

Zero of the 44 pairs moved. Base `emit/from-scratch` and the fix both run **72
passed** on the unchanged test file; with the two new tests the branch is **74
passed**. `git rev-parse HEAD:src` is `0854370` on both, so no emitted module
moved either.

## Prediction 2 — wrong on three of four labels, and wrong in the same direction

I predicted which outcome the current code reports. Measured, with each model
differing from the faithful one in exactly one axis:

| # | case | predicted TODAY | **measured TODAY** | measured AFTER |
|---|---|---|---|---|
| 1 | states a fact nobody states | `model_adds_a_fact` | `model_drops_a_fact` | `model_adds_a_fact` |
| 2 | omits a conjunct fact | `pass` | `model_adds_a_fact` | `model_drops_a_fact` |
| 3 | disagrees with the conjunct's `maximum` | `model_adds_a_fact` | `model_drops_a_fact` | `model_drops_a_fact` |
| 4 | the faithful composing class | `model_drops_a_fact` | `model_drops_a_fact` | `pass` |

One label of four right. The error was the same every time: I predicted each
case's outcome from its OWN axis and forgot that the composing noise outranks it.
`/required` differs on every model that inherits, so `model_drops_a_fact` wins
the outcome whatever else the model does, and case 2's model is non-composing so
only the other property's `added` row survives.

**The brief asked which of the four the current code gets right. The answer is
none, and that is not what either the brief or this prediction expected.** Case 3
was going to be the one that looked right — the brief predicted `model_adds_a_fact`,
I predicted the same, and in fact it reports the brief's own expected
`model_drops_a_fact`. But `compared` is 3 in all four cases, and no row anywhere
in case 3's report names `maximum`: the verdict is produced entirely by the false
`/required` row while the fact the case exists to grade is compared against
nothing. A right verdict off a wrong row grades nothing.

After the fix, `compared` is 7 in all four, and each case reports exactly the row
its axis names: case 1 one `added` row, case 2 the missing `/properties/kind`
plus `/required`, case 3 the single `maximum` difference, case 4 nothing.

## Prediction 3 — right on the rules, wrong on two measurements

The three merge rules are what shipped, unchanged. Two sub-predictions were
measured false:

- I predicted a property declared in both a root and a conjunct would occur **0
  times**. It occurs **6 times** in 61 documents. The `properties`-by-key merge
  was already planned, so nothing changed, but the rule is load-bearing rather
  than theoretical.
- I predicted the gap-fill rule's false failure would occur 0 times. It still
  measures 0 times *for a bound* — no ordering keyword is stated in two views at
  a root — but within those 6 collided properties `description` disagrees 3
  times, and there the node winning is the right answer, not a tolerated loss:
  the class's field description comes from the root's own declaration.

Confirmed rather than assumed: the caller hands a **resolved** document
(`codegen.bundle.resolved` writes it beside the module, `schema_at` reads it
back), and **0** conjuncts in the 61-document sample still carry a `$ref`. Also
measured and not predicted: `description` on a conjunct occurs 62 times and
gap-fills **0** of them, so the one keyword whose merge would have been
questionable is inert; and a conjunct carrying `additionalProperties: false` —
the draft-07 trap the bundle's own `version-envelope` description warns about —
occurs in **0** documents of the sample, so no special case was needed.

Max `allOf` nesting measured is **2**, so the recursion is used and the depth cut
is a backstop.

## Prediction 4 — right about the two it named, and it missed one

| perturbation | predicted | measured before the second commit | after |
|---|---|---|---|
| drop the `required` union | the four cases redden | **1 red** | 1 red |
| drop the `properties` merge | cases 2, 3, 4 redden | **1 red** (one test holds all four) | 2 red |
| fold an `if`/`then` conjunct's `then` | reddens nothing | **0 red** — as predicted | 1 red |
| let a conjunct override the node | reddens nothing | **0 red** — as predicted | 1 red |
| fold `anyOf`/`oneOf` like `allOf` | not predicted | **1 red** | 1 red |
| apply the view at the root only | **not predicted at all** | **0 red** | 1 red |

The miss is the last row: the fix's own comment claims the view applies at every
node, and nothing graded that claim. All three green perturbations now redden,
through `test_the_three_allof_decisions_that_no_case_above_grades`.

## What this contradicts in §6

Nothing in §6 is contradicted. One sentence of it is now measured at a second
site: *"The schema comparison is what grades the generated code."* It did not
grade a composing class at all — it reported one, which is a different thing, and
the §6 argument that a green mark without a denominator says nothing has a mirror
image here. **A RED mark with the wrong denominator says nothing either.** Case 3
failed, for a reason that had no relation to the defect it was built to find, and
`compared` was the only number that showed it.

§9's open question about where a reference-cycle comparison cuts is untouched:
`_composed` cuts at `allOf` nesting depth 16, the same constant and the same
shape as `_normalize`'s, over an already-inlined finite tree whose deepest
measured nesting is 2.
