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
