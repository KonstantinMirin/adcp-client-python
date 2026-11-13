# The branch-dispatch census, revived

What the four dead gates say now that they run. Branch `claude/gates-read-the-witness`,
from trunk `11272fdd5`.

The census had been red since the accepts corpus was deleted: three gates in
`tests_emit/test_union_dispatch.py` called `harness.corpus_key` and raised
`AttributeError` at their first line, and a fourth in `tests_emit/test_emit.py` wrapped the
same call in `except Exception` and fell silently through to a fresh draw. Two further
modules could not be collected at all. Nobody noticed, which is architecture.md §9's own
warning arriving: **a gate that cannot run reports nothing while looking like a gate.**

## The three figures, unmoved

| | cold | warm |
|---|---|---|
| `emitted 1059 / refused 0` (deferred 0, verdict 0); accounted 1059 | same | same |
| `kind: verdict 0, deferred 0, chained 0 -> primary 0, chained 0` | same | same |
| `approximated 383 facts in 148 documents` | same | same |
| **wall time** | **1 m 20.652 s** (command's own 72.40 s) | **5.091 s** (own 0.36 s) |

Run twice from a cold `ADCP_CACHE=/tmp/coldcache1`. All three figures are exactly those
measured on trunk.

**Cold is not warm here, and that is the COMPILE and not the grading.** The 72 s is the
one cache `./check` reads — `tests_emit/compiled.py`, one compile per population keyed on
the compiler's own source. `cold == warm` is a property of the WITNESS path, which
`./check` does not exercise: it compiles and counts. The construction's own cost is a
separate 45 s whole-bundle walk, paid once per process and shared by every reader through
`tests_emit/constructed.py`.

## `tests_emit/` collects

**9482 tests collected, 0 errors** — against trunk's `9482 tests collected, 2 errors`. The
two error modules contributed no tests, which is why deleting them moves no count.

## The four gates, by name

| gate | before | after | what it claims |
|---|---|---|---|
| `test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from` | `AttributeError` | **PASS** | 151 bases, 552 positions, 539 naming one branch, 472 admitted, **430 reached their branch**, 42 elsewhere, 0 refused |
| `test_a_union_refusal_names_the_position_it_refuses_at` | `AttributeError` | **PASS** | 510 perturbable, 479 bitten, **463 named the position**, 13 keyless cell, 3 lax bases, 136 bases |
| `test_a_keyless_dispatch_refusal_names_the_position_the_document_refuses_at` | `AttributeError` | **PASS** | 58 keyless bases, **16 positions reach the screen, 16 of 16 name it** |
| `test_emit.py` `_an_instance` (the committed-floor read) | silently drew | **reads the construction** | **454 of 454 arms answered, every one `Source.CONSTRUCTED`, all 454 pass the loud screen** |

`tests_emit/test_union_dispatch.py` whole module: **4 failed / 11 passed → 1 failed / 14
passed.** The three census gates went red to green. The one that remains is named below.

`wrong` is `{}` and `nameless` is `{}` in all three. The counts above are the first real
reading of this census since the deletion.

## What the shape lost and what it gained

A floor MISS was `unheld` — a pair the store had never been given, a legitimate "not
offered". A construction does not miss that way: it builds a witness or it names a reason,
and both are answers about the node. So `unheld` is gone and the reason is **asserted** in
`without_a_witness` with document, pointer and cause. It is **0 of 539**, and it is not a
partition cell, because a cell that grows absorbs a regression.

What takes the cell is a fact about the **stamp**, not about the data.

## Finding 1 — 13 positions carry more than one branch class

`_branch_sites` counts branch classes per `(document, pointer)`. Measured: 151 bases
declare **609 branch models over 552 distinct positions**, and 13 positions carry several:

```
adagents.json                        #/oneOf/1/properties/formats/items/allOf/0   (16)
core/package-format-snapshot.json    #/allOf/0                                    (16)
core/postal-area.json                #/anyOf/0/allOf/0                            (10)
core/vendor-pricing-option.json      #/allOf/1                                     (5)
core/async-response-data.json        #/anyOf/10, #/anyOf/11                     (3 each)
core/package-signal-targeting.json   #/allOf/0                                     (3)
core/product-filters.json            #/properties/signal_targeting/items/allOf/0   (3)
media-buy/build-creative-request.json #/properties/signal_conditions/items/allOf/0 (3)
core/creative-representation.json    #/allOf/0                                     (2)
creative/sync-creatives-request.json #/properties/creatives/items/allOf/0          (2)
media-buy/buy-products-request.json  #/anyOf/1/properties/account                  (2)
media-buy/request-proposals-request.json #/anyOf/1/properties/account               (2)
```

`core/package-format-snapshot.json#/allOf/0` is the instructive one. That node is the
Product Format Declaration, carrying `discriminator: {propertyName: format_kind}` and a
**16-arm `oneOf`** whose arms the document titles "Image Format Declaration", "HTML5 Format
Declaration", and so on at `#/allOf/0/oneOf/0..15`. All sixteen emitted branch classes are
stamped at the **parent**, `#/allOf/0`, and none at its own arm.

**This is why those 33 rows are not dispatch defects.** The construction builds one witness
at that one position — correctly, memoised once — and one value cannot resolve to sixteen
classes. Graded naively, exactly one of the sixteen comes back and the other fifteen are
recorded as "no UNDERDETERMINED declared"; 33 rows arose that way, all 33 inside these 12
bases. The dispatch is right: the base dispatches on `format_kind` and lands where the
witness's `format_kind` says. The derivation was asking a question the position cannot
answer, because *"the branch it was drawn from"* presupposes the position names one branch.

**The stamp is already graded and already red at exactly these pointers:**
`tests_emit/test_one_node_is_one_declaration.py::test_one_schema_node_is_declared_by_at_most_one_class`
fails on them (`2 failed, 14 passed` in that module). So the three census gates name the
cell, report it in their partition, and leave the assertion where it lives — re-asserting
it would be the two-derivations-of-one-number defect `tests_emit/nodeset.py` warns about.

This is a reading-1 question for whoever owns the stamping (`codegen/ir.py`,
`codegen/render.py` — the `distinct` lane): **a `oneOf` arm's class should carry its arm's
pointer, not its parent's.** It is also the root cause of the one remaining failure in the
module (see Finding 3).

## Finding 2 — `_document_path` misread a correct refusal (fixed, in the gate)

`core/wholesale-feed-event.json#/oneOf/6`. The perturbation puts the fault at
`('payload','pricing_options',0,'pricing_option_id')` and the dispatch refuses at

```
('signal.priced', 'payload', 'pricing_options', 0, 'cpm', 'pricing_option_id')
```

— the fault's exact position, with two pydantic arm labels interleaved: `signal.priced`
(the outer tag) and `cpm` (the inner pricing-option arm's tag). The payload **does** carry a
`cpm` key at `pricing_options[0]`, worth `0`.

The reduction searched `for drop in (0, 1)` — every segment a document step, then one
*leading* label dropped — so it walked into `cpm`, could not find `pricing_option_id` under
a number, and returned `('payload','pricing_options',0,'cpm')`: **the wrong position,
reported of a refusal that had named the right one.** The function's own docstring already
says a label "can land anywhere along the path -- not only in front"; the code only
implemented the front.

The search is now over *which* segments are labels — fewest first, earliest first, which is
that docstring's own whole-`loc` rule generalised. It reproduces every example the docstring
measures (`('cpm','pricing_option_id')` → `('pricing_option_id',)`,
`('binary','signal_ref','data_provider','signal_id')` → the last three,
`('daast_tracker','url','str')` → `('url',)`, and the plain nested case unchanged) and moves
only this row, from `nameless` into `named_the_position` — which is why that count is 463
and not 462. **A defect in the instrument, not in the tree it grades.**

## Finding 3 — the one remaining module failure, pre-existing

```
test_a_restated_required_key_is_required_of_the_class[
    media-buy/buy-products-request.json-#/anyOf/1/properties/account-...-BuyProductsRequestBranch1Account]
AttributeError: module 'adcp.types._schemas.media_buy.buy_products_request' has no
attribute 'BuyProductsRequestBranch1Account'. Did you mean: 'BuyProductsRequestAccount'?
```

Red on trunk, red now, untouched. The parametrize row names a class that no longer exists.
Its position — `media-buy/buy-products-request.json#/anyOf/1/properties/account` — is **one
of Finding 1's 13**, so it is the same stamping subject reaching a different gate: two
classes at that pointer, and the name the row was written against is gone.

## Finding 4 — `_an_instance`'s two consumers were already red, and now fail further on

Both were red on trunk with `AttributeError` at the dead corpus rung. Both are still red,
for two **different** pre-existing reasons the dead rung was shadowing:

* `test_a_consumers_subclass_of_a_union_base_keeps_its_own_schema` — at
  `core/postal-area.json`, `assert type(branch.model_validate(arm)) is branch` gets
  `PostalAreaUS` where it expects `PostalAreaCountrySystemValues`. That branch is **itself a
  dispatching base** (10 branch models), so §5's nested row applies and the hook fires again
  inside it — the relation `_dispatched_to` encodes and this assertion does not. A
  test-side reading error of the same kind as Finding 2, left alone because it is outside
  what this lane was sent to re-point.
* `test_a_union_base_instance_and_a_branch_each_serialise_as_what_they_are` — at
  `account/get-account-financials-response.json`, `set(held.model_dump()) ==
  set(held.__dict__)` gets `{'replayed'}` against the envelope's own field set. **This
  assertion is three lines above the first `_an_instance` call**, so it is reached only
  because the rung now works, and it has nothing to do with the witness. A base whose
  `model_dump()` yields one key named `replayed` is a serialiser bound to the wrong model;
  that is the `presence`/`_base.py` subject, not this one.

## Finding 5 — there is more dead machinery than the four gates

Running the corpus-adjacent modules turns up **57 failures / 36 passed** in
`test_harness_halves.py` and `test_no_cap_is_on_the_grading_path.py` alone, every one the
same rot as `corpus_key` — gates calling harness names the draw deletion removed:

```
20  AttributeError: harness has no attribute 'the_canonical_encoding_is_not_rebuilt_in_python'
12  AttributeError: harness has no attribute '_round_trips'
 8  TypeError: check_accepts() got an unexpected keyword argument 'examples'
 4  AttributeError: harness has no attribute 'a_combinator_is_covered_and_never_enumerated'
 2  AttributeError: harness has no attribute 'canonicalisation_shared_within_one_call'
 2  AttributeError: harness has no attribute 'Fixtures'
 1  AttributeError: harness has no attribute 'shared_within_one_grade'   (and others)
```

Also red and not mine: `test_every_check_names_its_set.py::test_no_check_pins_a_census_as_an_equality_beyond_the_ratchet`
(flags 5 files, none of them touched here — `test_no_cap_is_on_the_grading_path.py`,
`test_the_adapter_writer_owns_its_paths.py`, `test_the_compat_mirror.py`,
`test_the_member_spelling_is_emitted.py`, `test_upstream_states_the_binding.py`) and
`test_scratch_is_on_disk.py::test_the_scratch_directory_is_outside_the_checkout_and_ignored_by_name`
(`.adcp-scratch` absent from `.gitignore`). The four gates were the ones named; they were
not the only ones.

## What was deleted, and what was not

Deleted: `tests_emit/test_accepts_corpus.py` (1,419 lines) and
`tests_emit/test_widening_corpus.py` (851 lines) — **2,270 lines, 120,326 bytes**. They
grade the corpus's own key stability, round-trip declining and warm-vs-cold hit rate; the
mechanism does not exist, and a gate over a deleted mechanism is not repairable into a gate
over the live one.

**Kept, because they are still read — 0 files removed from `tests_emit/accepts-corpus/`:**

* `tests_emit/corpus.py` is now a thin re-export of `codegen/held.py`, imported by
  `tests_emit/test_emit.py` **and** `tests_emit/test_immaterial_presence.py`.
* `tests_emit/accepts-corpus/` (256 files, 470,663 bytes) is reachable as
  `held.FLOOR` through `corpus.STORE`, which both those modules pass to
  `harness.check_pair`.

**But `codegen/harness.py` never reads either store.** Checked by AST rather than grep:
the only live references to the parameter are the guard at `harness.py:4350` and two
dataclass fields, and there is no attribute access to `.corpus` anywhere in the module.
The parameter is accepted, validated, and ignored — the construction replaced it. So both
directories are dead weight behind a live import, and `tests_emit/widening-corpus/` (175
files, 878,671 bytes) with them.

Clearing that is a change to the `graded_report` call shape in `test_emit.py` and to
`tests_emit/conftest.py`'s `--write-corpus` flag, **whose only consumer was
`test_accepts_corpus.py`, deleted here**. `conftest.py` is not in this lane's write scope;
naming it instead.

## Changes outside this lane's write scope that are wanted

* `codegen/ir.py` / `codegen/render.py` (`distinct`) — Finding 1: stamp a `oneOf` arm's
  class at its arm's pointer, not its parent's. 13 positions, 609 branch models over 552.
* `tests_emit/conftest.py` — drop `--write-corpus`; its only consumer is deleted.
* `src/adcp/types/_base.py` (`presence`) — Finding 4's second row, a base whose
  `model_dump()` yields `{'replayed'}`.

## On the two mid-turn instruments

`survey causes` and the `--out/junit/chunk-*.json` count both read a **drop-in behavioural
run**, which this lane was told not to run and did not run. No figure in this file comes
from that suite, so there is no `chunks read` to check and no residue to attribute. The
three figures above come from `./check` and from `pytest` over `tests_emit/`, which
`survey causes` does not grade. Not rebased onto `274021e6d`/`f53fcb447`: every figure here
is measured against the stated trunk `11272fdd5`, and moving the base mid-verification
would move the three numbers this file is asked to report unmoved.

---

# Round 2 — the 57 more dead gates, and what they were hiding

Trunk `18857f167`, rebased before measuring. The two modules named as P0 went
**57 failed / 36 passed → 38 passed, 0 failed.**

## The split

| | deleted | re-pointed |
|---|---|---|
| `test_harness_halves.py` | 18 | 5 |
| `test_no_cap_is_on_the_grading_path.py` | 2 | 1 |

**Deleted — 20, each over a mechanism that no longer exists:**

| mechanism | gone because | gates |
|---|---|---|
| the combinator COVER (`a_combinator_is_covered_and_never_enumerated`, `harness.strategy`) | §8's power-set replacement for a hypothesis draw; no draw | 4 |
| the CANONICAL ENCODING (`the_canonical_encoding_is_not_rebuilt_in_python`, `_c_encoder_is_canonical`, `_CANONICAL_ENCODING_SITES`) | existed to make the corpus KEY reproducible | 5 |
| the memo's copy clause (`_round_trips`) | same | 1 (×12 params) |
| the CANONICALISATION memo (`canonicalisation_shared_within_one_call`) | a within-one-call memo over `canonicalish` | 2 |
| the STORE, and the document's-own-`examples` rung | `check_accepts` climbs no ladder; the caller hands it the witness | 2 |
| §8's fixture SUBSTITUTION (`draw_from=`, `harness.Fixtures`) | replaced by `Construction` | 2 |
| a budget cut landing inside the draw | handed `witness=None` the check returns `no_witness` before calling `accept` at all | 2 |
| `harness.Fixtures.reduced`'s `depth: int = 8` | the sampler is gone | 2 |

**Re-pointed — 6, each over a mechanism that is live.** What they say now:

1. **the DUMP half** — `examples=N` became `witness: Sequence[Any]`, which is a different
   *kind* of argument: a count is a knob that can turn a check off, a witness list is the
   thing being graded. `DropsB` is still caught, still on `required`, still with
   `round_tripped == 0`.
2. **the round-trip count** — `examples == round_tripped == 3` over a handed witness. It
   counts dumps rather than draws, and now there are no draws to confuse it with.
3. **`OverBudget` crossing the handler chain** — injected through `accept`, it crosses all
   three of `check_accepts`' handlers as itself and is never converted to a verdict. The
   second injection point (the strategy build) is deleted; the surviving half is the
   stronger of the two.
4. **the validator sharing** — this measured `reused == 0` and read as a defect in the
   sharing. **It is not one.** A pair graded with no `construction=` does almost nothing:
   accepts returns `no_witness` and admits reports *"no construction was supplied, so there
   is no witness set"*, so nothing asks for a validator and nothing is shared. The FIXTURE
   was stale; it now supplies a one-document `Construction` and `reused > 0`.
5. **the no-cap gate, clause 3** — see below. This is the one that matters.

## Finding 6 — the no-cap gate read one module, and the grading path is in two

`test_no_cap_is_on_the_grading_path.py` gates one of the five standing targets. It was red
on its own first assertion:

```
AssertionError: ['reduced', '_pin', '_derived_pin', 'value'] is named here
and is not a function of harness.py
```

Those four are the frames of `harness.Fixtures.reduced`'s `depth: int = 8` — the fifth
bound the file removed. `harness.Fixtures` no longer exists.

**That redness was the file telling the truth and nobody reading it.** `UNBOUNDED` is
asserted to be a list of LIVE functions precisely so a rename reddens here instead of
silently emptying the population, and it did exactly that. What it could not say, because
it died at line one, is the thing that matters: **clause 3 ranged over
`codegen/harness.py` alone, while the three checks now derive every witness in
`codegen/verify/witness.py`.** The target has been unguarded for the module that does the
work ever since the sampler was replaced.

Clause 3 now reads both — `UNBOUNDED` over `harness.py`, and **every function** of the
verifier, since §9's *"the verifier reads nothing but its arguments"* makes that descent
its whole content and "every function" is the population a rename cannot empty.

**And the target holds on the live path.** Measured: **10 named harness readings + 89
verifier functions, and 0 of the 99** declares a parameter spelled `depth` or reads a
constant ending `_DEPTH`. The 89 had no gate at all.

## Finding 7 — the PRIMARY grading pass is dead, and this is the biggest thing here

`tests_emit/test_emit.py::graded_report` is the pass that `test_every_class_passes_all_three_checks`
reads over 2,584 pairs. It raises for **every** pair:

```
File "tests_emit/test_emit.py", line 1488, in graded_report
    fixtures=fixtures(),
AttributeError: module 'codegen.harness' has no attribute 'Fixtures'
```

Doubly dead: `harness.Fixtures` is gone, **and** `check_pair` no longer takes `fixtures=`
at all. What replaced it is `construction=`, and without one `check_pair` reports
`admits_absent = "no construction was supplied, so there is no witness set"` — the first
check is `unrun` for every pair.

Measured with the repair applied by hand (`construction=constructed.whole()`), on the four
pairs the old docstrings named as most expensive:

| pair | was (cold, with the draw) | now |
|---|---|---|
| `media-buy/get-media-buy-delivery-response.json#` | 2,356.66 s | **0.192 s** |
| `media-buy/refine-proposals-response.json#` | did not finish | **8.149 s** |
| `media-buy/get-media-buys-response.json#` | did not finish | **0.262 s** |
| `core/macro-declaration.json#` | 151.51 s | **7.034 s** |

**I have not landed that repair**, and the reason is in the verdicts it produces: three of
those four report `admits=model_refused_admitted` and one reports
`accepts=witness_refused`. Reviving the pass flips the primary census, and reporting a
census I have not read would be the thing this project's own standard forbids. It wants
one lane of its own: re-point `graded_report` at `construction=`, then read all 2,584 rows
and report the outcome table. **That is the next lane, and it is worth more than anything
in this one.**

## Finding 8 — the budget is dormant and now has no live caller at all

`harness.within`, `OverBudget`, `budget_expired` and `_BUDGET_RETRY` are fully implemented.
The standing target says **no budget**. Three measurements:

* **its justification is gone.** `within`'s own docstring grounds it in *"a draw over a
  multi-megabyte node has no bound of its own -- measured at 2 h 57 m and 32 GB of RSS on
  one 44 MB node"*. There is no draw.
* **it is dormant.** Worst of the four pairs above: **8.149 s against `PAIR_BUDGET = 300`.**
* **it has no live caller.** Its one call site is `test_emit.graded_report`, which raises
  `AttributeError` before reaching it (Finding 7). And `harness.budget_expired` has **no
  caller anywhere in the tree** — its only remaining references are a comment in
  `harness.py` and the docstring of the clause deleted for it.

Also dead and declared: `check_pair` and `_check_pair` still take `accepts_examples`,
forwarded one hop and read nowhere. That is *"a knob whose setting can turn a check off"*
in the words of the rule the no-cap gate cites — dead text today, but the standing target
says it should not be declared. **I did not add a clause for it**: the removal is a
`harness.py` change, which is not in this lane's scope, and a new red gate naming
someone else's file is a worse way to say this than a sentence here.

## Finding 9 — item 3, proved and acted on

| | result |
|---|---|
| files importing `tests_emit/corpus.py` | **2** — `test_emit.py`, `test_immaterial_presence.py` |
| attribute accesses on the module | **4**, all of them `corpus=`/`widening_corpus=` kwargs to a harness call |
| `.get` / `.put` on either store, in either file | **0** |
| `_check_pair`'s use of its `corpus` parameter | the name does not appear in its body |
| attribute reads of `_Draws.corpus` in `harness.py` | **0** |

So the imports are dead text and the directories are dead bytes.

**Deleted:** `tests_emit/accepts-corpus/` — **2,585 tracked files, 470,663 bytes** — and
`--write-corpus` from `conftest.py`, which has no invoker anywhere and whose only consumer
was deleted in round 1.

**Kept, with the one-line decision stated:** `tests_emit/corpus.py` (176 lines, 10,519
bytes) needs two lines removed from `test_immaterial_presence.py` — `import corpus` (65)
and `corpus=corpus.STORE` (327) — which is not in this lane's scope. That call cannot
execute anyway: it passes `examples=`, `corpus=` and `identity=` to `check_accepts`, which
takes none of them. **The last reference to the store is inside a call that always raises.**

**Kept, out of scope:** `tests_emit/widening-corpus/` — 290 tracked files, 878,671 bytes,
reached only through the same dead `_Draws.corpus`.

## Finding 10 — the disease is in a third module

`tests_emit/test_immaterial_presence.py::test_each_form_refuses_a_payload_its_document_refuses_and_admits_one_it_admits`
fails with `TypeError: check_accepts() got an unexpected keyword argument 'examples'` —
the identical rot, in a module neither round's scope covers. Verified pre-existing: it
fails the same way with `accepts-corpus/` restored, so it is not a consequence of the
deletion.

## Changes wanted outside this lane

* **`tests_emit/test_emit.py`** — Finding 7, and it is the next lane: `graded_report` →
  `construction=`, then read the 2,584-row census.
* **`codegen/harness.py`** — Finding 8: remove `within`, `OverBudget`, `budget_expired`,
  `_BUDGET_RETRY`, the `accepts_examples` parameter, the `corpus`/`widening_corpus`
  parameters and `_Draws.corpus`. All dead, all declared.
* **`tests_emit/test_immaterial_presence.py`** — Findings 9 and 10: three dead kwargs, and
  the two lines that free `corpus.py`.
* **`codegen/ir.py` / `codegen/render.py`** (`distinct`) — round 1's Finding 1, dispatched.
