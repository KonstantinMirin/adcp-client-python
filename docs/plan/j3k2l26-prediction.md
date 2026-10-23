# salesagent-j3k2l.26 — the keywords below a root that no row claims

Started from trunk at **84acaf6cf** (`docs(plan): correct the metric, and record
that every absolute was overstated`), clean.

Branch: `sdk/j3k2l26-below-root`.

## 0. The baseline, re-measured on that tree

`codegen.emit` over all 1,054 portable documents, classified by the constants the
refusal producers emit (`codegen.refusal.DEFERRED_TO_A_LATER_ROW`,
`UNRESOLVED_TARGET`, `is_a_verdict`) and never by matching text:

| figure | value | denominator |
|---|---|---|
| portable | 1,054 | — |
| emitted | 674 | 1,054 portable |
| refusals | 380 | 1,054 portable |
| deferred | 48 | 380 refusals |
| transitive | 1 | 380 refusals |
| chained-pending | 30 | 380 refusals |
| verdicts | 301 | 380 refusals |
| accounted (emitted + verdicts) | 975 | 1,054 portable |
| pending | 79 | 1,054 portable |
| comparison added / missing / differs | 0 / 0 / 43 | — |

The three pins on this tree already read `deferred <= 48`,
`transitive <= 1`, `chained_pending <= 31`, `accounted >= 975`
(`tests/test_emit.py`), so the brief's "pins you must move" are already AT the
measured value and what this row owes them is a tighter value, not a first one.

## 1. The 48, and where the issue's own list disagrees with the tree

**The issue's title and body name a different set, and the tree wins.** It was
filed when the deferral set was 46 and reads
`anyOf 25 / oneOf 11 / uniqueItems 6 / enum 2 / maxLength 2`. Measured here:

| keyword | docs | the issue says |
|---|---|---|
| `oneOf` | 23 | 11 |
| `anyOf` | 10 | 25 |
| `uniqueItems` | 7 | 6 |
| `contains` | 5 | — not named |
| `enum` | 2 | 2 |
| `items` | 1 | — not named |
| **total** | **48** | 46 |

Two corrections follow and both matter for what this row is:

* **`maxLength` is GONE from the deferral set entirely.** `salesagent-j3k2l.22`
  cleared it; the issue's claim that `.12`'s named-constrained-type row does not
  reach it is no longer a live fact.
* **`contains` (5) and `items` (1) have NO closed row and no row anywhere.** The
  issue asserts "This issue schedules no new keyword. Every keyword below ALREADY
  HAS A CLOSED ROW" — that is false of 6 of the 48. `contains` is a draft-07
  array keyword this pipeline has never lowered.

## 2. The pointer-shape partition, which the issue asks for first

**A root refusal spells its pointer `/`, not `""`.** Counted on that spelling:

| position | docs |
|---|---|
| ROOT (`/`) | 4 |
| below a root | 44 |

All 4 roots are `uniqueItems` on a root ARRAY, and all 4 are a root kind
`bundle.is_container_root` ALREADY CLAIMS — the same thing `.22` found of its 29.
So, as there, no selector is missing and **`ROWS` must stay six.**

The 44 below a root, by the shape of the pointer:

| shape | docs |
|---|---|
| `/properties/<k>` | 18 |
| `/properties/<k>/items` | 8 |
| `/properties/<k>/properties/<k>` | 5 |
| `/definitions/<k>` | 4 |
| `/properties/<k>/items/properties/<k>` | 2 |
| `/anyOf/<i>` (a union BRANCH) | 2 |
| `/oneOf/<i>/properties/<k>` | 1 |
| `/oneOf/<i>/properties/<k>/items` | 1 |
| `/definitions/<k>/properties/<k>/items` | 1 |
| `/propertyNames` | 1 |
| `/properties/<k>/additionalProperties` | 1 |

## 3. The partition that decides the work — FIVE mechanisms, not one

The keyword tally is not the population. Partitioned by WHICH ARM of the walk
refused, which is what says whether a lowering exists to be written:

| # | family | mechanism | docs |
|---|---|---|---|
| U | `uniqueItems` on an array NO CLASS HOLDS | `lower.containers.array`'s screen | 7 |
| N | a combinator of SHAPES at a nested pointer | `_decide` has no union arm at all | 29 |
| P | a `oneOf` of `{required, not}` groups at a nested OBJECT | `rules._required_only` admits `{required}` alone | 4 |
| C | `contains` on an array | no row, no screen entry, nowhere | 5 |
| B | a union BRANCH carrying an `enum` | `union.BRANCH_HANDLED` | 2 |
| I | an array that also COMPOSES, refused on `items` | `lower_product`'s screen | 1 |
| | **total** | | **48** |

`.22` measured families N and B already and named them exactly: "C is D2's union
row at a NESTED pointer and E is a union root of scalars; no bead owns either, so
each gets one filed rather than a lowering written here." This is that bead.

### What each family's answer is, stated before the code

* **U is a VERDICT and the design is already written down.** `lower/rules.py`'s
  own docstring states it: "an array with no class above it (a mapping value, a
  document root, a combinator branch — 18 of the 485) keeps refusing on
  `uniqueItems` by name, and that is the true reason, because a rule has nowhere
  to live there." `lower/containers.py` adds the second half: pydantic v2 removed
  `unique_items`, so a `Constraints(uniqueItems=True)` renders bare `list[str]`
  and carrying the keyword would be a model wider than its document, silently.
  Both halves are measured facts in the tree. What is wrong today is only the
  ATTRIBUTION: the generic screen answers `DEFERRED_TO_A_LATER_ROW`, which
  promises a row that the two facts above say will never be written. So U needs a
  NAMED refusal, not a lowering — and `uniqueItems` stays out of the screen, which
  is the decision `rules.py` records.
* **B is a VERDICT and an attribution fix of the shape `ROOT_HANDLED` already
  carries.** A branch `{"type": "string", "enum": [...]}` is a SCALAR branch, which
  `union.py`'s docstring already lists among the branches that refuse by design.
  It is reported on `enum` only because `check_keywords` walks `sorted(node)` and
  reaches `enum` before `_plan`'s own `type` check — the identical misattribution
  the `ROOT_HANDLED` comment measured at 55 of 156 and fixed by admitting the
  keyword so the explicit refusal below is what reports it.
* **N is the one real lowering, and the GRADER is what decides whether it emits.**
  A nested union needs a TYPE, not a base plus one subclass per branch: that shape
  exists because a document ROOT must be one importable class that answers
  `isinstance`. `lower.containers.multi_type` already builds exactly the needed
  thing for a `type` LIST (`compiler.Type(container="union", ...)`). What is not
  known is whether `harness.compare_schema` READS that shape at a nested pointer:
  `oneOf`/`anyOf` are not in `FACTS`, `compare` descends only into `properties` and
  `items`, and `_normalize` folds a model's `anyOf` into a `type` LIST wherever
  every branch is a bare `{"type": X}` — at which point a document stating no
  `type` of its own reads the model's folded list as an `added` fact, because
  `_entails_type` only admits a type every branch SHARES. **`codegen/harness.py` is
  not this lane's file.** So where a position is ungradeable, N refuses by name with
  the measurement — the same stand `multi_type`'s constrained-arm refusal takes —
  rather than emitting a node no check reads.
* **P is NOT mine and I build nothing for it.** `rules._required_only` deciding that
  a `{required, not}` branch is not presence-only is what sends these 4 to the
  union reading. Widening it changes `rules.presence_only`, which
  `bundle.states_an_object_rule` is BUILT ON as a row's selector — and
  `codegen/bundle.py` is not this lane's file and a selector's population is exactly
  what the issue forbids moving. One bead, not a lowering here.
* **C is a statement about VALUES, and `ON_A_VALUE` is the precedent.** `contains`
  says at least one element matches a subschema. It renders nothing, is not in
  `FACTS`, and `strict_validate` enforces it against the document's own schema —
  which is verbatim the ground D4 and `rules.py` admit `not` on. So it is carried,
  not refused, and the array row admits it.
* **I is one document and is measured, not designed.**

## 4. Predictions

Written before any code exists. Graded in §5.

| # | prediction |
|---|---|
| P1 | U: **0 of 7 emit, 7 become verdicts.** No array of the 7 gains a lowering |
| P2 | B: **0 of 2 emit, 2 become verdicts**, each reported on `type` with "a branch of type 'string' is step 6" |
| P3 | N: of 29, **8 emit** and **21 become verdicts**. The 8 are the positions whose model keeps an `anyOf` that `_normalize` does NOT fold (a `$ref` or object branch beside a scalar one) and whose document node states no keyword in `FACTS` |
| P4 | N's 21: the dominant blocker is `added`, from `_normalize`'s bare-type fold meeting a document that states no `type`. I expect **at least 2** (`property-feature-value.json`, and one of the `status_filter` pair) to be blocked exactly there |
| P5 | P: **4 of 4 unchanged, still DEFERRED**, and one bead filed. This row moves them not at all |
| P6 | C: **2 of 5 emit**; 3 chain onto family N through an `anyOf` inside their own `items` and clear only if N clears that position |
| P7 | I: **0 of 1 emits**, 1 verdict |
| P8 | deferred **48 → 4** (family P alone). NOT 0: P is out of this lane |
| P9 | accounted **975 → 1,020** (674 + 10 emitted = 684; 301 + 35 = 336; 684 + 336 = 1,020) |
| P10 | chained-pending **30 → 24**: 6 of the 30 release behind the 10 documents that emit |
| P11 | `comparison.added` stays **0**. Any position whose lowering would move it is refused instead, and that is the decision rather than a pin to re-point |
| P12 | `ROWS` stays at **six** and `codegen/bundle.py` is not touched. No new selector; every one of the 48 sits at a root kind an existing selector already claims or at a position no root selector sees |
| P13 | The pins become `deferred <= 4`, `transitive <= 1`, `chained_pending <= 24`, `accounted >= 1020`, each fire-probed one step tighter |
| P14 | `emit.write` leaves stale `.py`/`.json` behind for no document, because no document STOPS emitting here — emissions only grow (salesagent-j3k2l.30) |

### What I expect to be wrong

**P3 and P6 are the two guesses with no instrument behind them.** I classified
family N by the FIRST keyword each document refuses on and by its branch shapes
read off the JSON; a second blocker inside a branch is invisible to that reading,
and every previous lane's equivalent prediction was optimistic. P9 and P10 are
arithmetic over P1–P7 and fall with them.

**P8 is the prediction I most expect to be called a miss**, because the brief
asked for `deferred <= 0` implicitly ("the 48 are all yours"). I am predicting 4
survive, and the reason is a file-ownership boundary rather than a measurement:
family P's fix is in a selector's predicate and `codegen/bundle.py` is another
lane's file.
