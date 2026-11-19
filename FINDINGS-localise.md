# The two invariants the pinned default broke: one fixed in the emission, one is the owner's

`tests_emit/test_union_dispatch.py` went from **15 passed** at `27192ec6d` to **2 failed, 13
passed** on trunk. It is now **1 failed, 14 passed**. The important one — a union's refusal
naming WHERE and not only THAT — is fixed at its own site. The other is the pinned default
itself applying exactly as `verdicts/a-pinned-default-is-the-documents-own.md` says it must,
and every narrowing that would make it pass takes a position the verdict counts, so it is
reported here rather than forced.

## 1. The keyless refusal's POSITION: fixed (`adcp-client-python-jgsf`)

**The site is `adcp.types._base.BranchDispatchMixin._undetermined`, and it is one line of
row SELECTION.** Nothing in `codegen/` moved and nothing had to: the emission, the documents
and the branch classes all still accept and refuse what they did.

What the screen does: when no branch's document admits the payload, it raises at the
document's own pointer, read off the refusal of the branch the STRUCTURE matched. It took
`refused.errors()[0]`.

**The document refuses this payload at EVERY branch, so that refusal has more than one row,
and which one came first was an accident of which branch matched.** Measured, at
`media-buy/proposal-refinement.json#/oneOf/1/anyOf/*`, payload
`{"constraints": {"total_budget": {"currency": "AAA", "min": "0"}}, "proposal_id": "a", "action": "revise"}`:

| branch | the document's refusal there |
|---|---|
| `#/oneOf/1/anyOf/0` `…ReviseConstraints` | `type` at `('constraints','total_budget','min')` |
| `#/oneOf/1/anyOf/1` … `/6` | `required` at `()` for ITS own key, **then** `type` at `('constraints','total_budget','min')` |

All seven name the fault. Six name their own absent key first.

**What the pinned default moved was WHICH BRANCH THE STRUCTURE MATCHED.**
`#/oneOf/1/anyOf/5` requires `remove_media_buy_frequency_cap`, which the document pins to
`true`, and `#/oneOf/1/anyOf/6` requires `change_kind`, pinned to `'cancellation'`. Both
classes therefore now admit a payload omitting them on the Python route, pydantic's union
prefers one of them over the branch that needs a lax `str`→`float` coercion, and `answered`
became `…ReviseRemoveMediaBuyFrequencyCap`. Its first row is the root `required`, so the
reported position fell from `('constraints','total_budget','min')` to `()`:

    ProposalRefinementRevise <- ProposalRefinementReviseConstraints
    "the keyless screen refused and named no position:
     document refuses at ('constraints', 'total_budget', 'min'), reported [()]"

**The fix is the screen this class already applies elsewhere, not a new reading.**
`_present` exists for exactly this distinction and says it in its own words: *"A branch's
`missing` names a key the payload does not carry: it is a statement about what is ABSENT and
so locates nothing in the caller's own document, while a branch's `string_type` names a key
the caller DID send and is a position they can go and look at."* `_common_position` screens
`_no_branch`'s rows that way already. So `_undetermined` now reports the first row naming a
NON-EMPTY position the payload actually has, and `errors()[0]` stands where no row does —
which is the required-group case, at the object itself, where `_common_position` also
answers `()`.

The message and the position stay ONE row, so the sentence a caller gets still quotes the
reason that belongs to the pointer it is raised at:

    anyOf at ('constraints', 'total_budget', 'min'):
      this union states no discriminator its document guarantees, so the branch is
      selected by structure, and no branch's document admits this payload; the branch
      that matched is media-buy/proposal-refinement.json#/oneOf/1/anyOf/5
      (ProposalRefinementReviseRemoveMediaBuyFrequencyCap), which the document refuses:
      '0' is not of type 'number'

**AND THE FIX IS NOT "WHICHEVER BRANCH MATCHED THIS TIME".** It holds whichever branch the
structure lands on, because every branch's document refusal carries the agreed fault and the
screen drops only the rows about keys the payload does not carry. That is the difference
between this and restoring the old match, which is why the site is the row selection and not
the pin.

### The ceiling it was heading for

`test_a_union_refusal_names_the_position_it_refuses_at` carries
`the_arms_share_no_position` as a CELL under `ratchet(at_most=CELL_CEILING=18)`, measured at
13, whose `because` says it *"RISES only when the dispatch stops naming a position it could
have named"*. A position that falls from a field to the root lands there and stays green
while the ceiling has headroom. The keyless clause is what caught this one; the cell is the
place to watch if a future pin moves another.

## 2. `test_the_submitted_arm_requires_what_its_target_requires`: NOT fixed, and this is why

**The refusal that stopped happening is `Field required` at `status`, and the pinned default
is supplying it exactly where the verdict says it must.** Not repointed, not deleted, and
left RED.

`media-buy/refine-proposals-response.json#/anyOf/1` is a bare `$ref` to
`core/compact-task-submitted.json`:

```
#/anyOf/1            required: ['status', 'task_id']   properties.status: {const: 'submitted'}
#/anyOf/1/allOf/1    required: ['status']              properties.status: <TaskStatus, 9 members>
```

So `status` is required AND pinned to one value at the class's own node, which is
`codegen/render.py::_field`'s predicate verbatim —
`pins=decided.required and len(literals) + len(members) == 1` — and the field carries
`PinnedDefault`. `_supply_the_pins_the_document_states` then folds `'submitted'` in on the
Python route, so `RefineProposalsResponseSubmitted.model_validate({"task_id": "0"})`
returns an object. The other three routes are unchanged and were measured:
`model_validate_json('{"task_id":"0"}')` still reports `status Field required [type=missing]`,
`strict_validate` still refuses, `model_json_schema()` still publishes `required`.

**It is not a branch artefact.** `CompactTaskSubmitted` — the target the test says the branch
must requires what it requires — carries the SAME marker on the SAME property, so the branch
class is not wider than its target. The widening is the decision's, at **1,264** marked
fields of the tree: 663 at keyed-union branch classes, 150 at keyless-union branch classes,
451 at classes that are not a branch at all.

**And it is DECLARED, by the accounting the decision shipped with.**
`codegen/harness.py::the_marker_declares` clause 2: *"the witness DROPS one required key →
`PinnedDefault`, and only where the document pins that property to one value"*. The witness
test 1 offers is that witness, at a field carrying that marker, so `./check` counts it
declared rather than as an undeclared widening. The gate and the marker agree; it is this row
that disagrees with both.

### Every narrowing that would make it pass costs a position the verdict counts

Four were measured over the bundle and the tree. Each is reported with what it takes:

| candidate narrowing | what it costs |
|---|---|
| **(a)** pin only where EVERY node of the conjunction that requires the property also pins it | **18** positions, all of them `status` — and `media-buy/sync-reporting-receipts-response.json#` is one, which is `SyncReportingReceiptsResponse.status` = **28 of the verdict's 82** and its headline example of reading the rule off the node |
| **(b)** no pin on a union branch class | 813 of the 1,264, including `IndividualImageAsset.asset_type` and `BuildCreativeEstimate.mode` |
| **(c)** no pin on a KEYLESS union branch class | 150 of the 1,264, including `BuildCreativeEstimate.mode` = **12 of the 82** |
| **(d)** no pin where the sibling branches do not all pin the property to the same value | `BuildCreativeEstimate.mode` again — `media-buy/build-creative-response.json`'s other five branches state no `mode` at all |

(a) is the one the conjunction reading points at, and it is the one that lands hardest. The
18 are:

    core/compact-task-submitted.json                             #
    core/async-response-refs/media-buy/*-async-response-submitted.json  #/allOf/0   (6)
    media-buy/*-async-response-submitted.json                    #/allOf/0          (6)
    media-buy/get-products-rejected.json                         #
    media-buy/refine-proposals-response.json                     #/anyOf/1   <- this row
    media-buy/request-proposals-response.json                    #/anyOf/3
    media-buy/sync-reporting-receipts-response.json              #   <- the verdict's 28
    media-buy/sync-reporting-status-response.json                #

`refine-proposals-response.json#/anyOf/1` and `sync-reporting-receipts-response.json#` are
the SAME SHAPE: `required` plus a `const` at their own node, and `core/protocol-envelope.json`
requiring the same property with its nine-member `TaskStatus` one `allOf` up. No predicate
over the node separates them, and `verdicts/a-pinned-default-is-the-documents-own.md` cites
the second by name as the measurement the rule exists to get right.

**So this is a decision and not a defect**, per `CLAUDE.md`'s opening rule and the task's own
instruction: the only fixes visible from here take positions the owner has already ruled on.
The two shapes available to the owner, neither taken here:

1. **Keep the pin and this row goes.** `status` on a submitted envelope is a pinned required
   property like the other 1,263, and "a branch class is no wider than its node" is no longer
   true of the Python route anywhere the decision applies — which `_ThePinIsSupplied` says in
   its own four-routes table. The row would then be asserted through `strict_validate` or
   `model_validate_json`, which both still refuse, and that is a REPOINT this lane was told
   not to make.
2. **Take narrowing (a) and the verdict loses `SyncReportingReceiptsResponse.status`.** 18
   positions stop supplying the pin; the 28 `Field required` failures the verdict removed from
   the correction set come back. The argument FOR it is in `core/protocol-envelope.json`'s own
   words — *"Agents shipping responses without a top-level `status` are non-conformant
   regardless of whether the task body schema would otherwise validate"* — which is the
   document saying the caller may not omit it. That is an argument the owner has not been
   shown, and it reverses part of a ruling, so it is not one to take in a lane.

## 3. `tests_emit/test_refuses_check.py`'s 10: a DIFFERENT cause, and left alone

**One fix does not close all twelve. It closes one of them.** Asked whether the 10 are the
mechanism this lane is on, the answer is no, and it is measured rather than argued:

**THE 10 FAIL IDENTICALLY WITH BOTH OF THE PINNED DEFAULT'S `codegen/` HALVES REVERTED.**
`git diff 27192ec6d..HEAD -- codegen/` is exactly two functions — `harness.the_marker_declares`
(plus its `pins_default` import) and `render._field`'s `pins` flag. With both files checked
out at `27192ec6d`, the commit where `test_union_dispatch.py` is 15 passed,
`tests_emit/test_refuses_check.py` is **10 failed, 23 passed** — the same ten node ids. The
test side cannot have moved either: `git diff --stat 27192ec6d..HEAD` is EMPTY for
`tests_emit/test_refuses_check.py`, `tests_emit/test_emit.py` and `codegen/verify/witness.py`.
So all ten were red at the green commit, and the pinned default is not in their history.

They are two causes, neither of them a refusal losing its position:

**(1) Nine of the ten: a fixture naming apparatus that was deleted on 2026-11-11.**
`AttributeError: module 'codegen.harness' has no attribute 'Fixtures'`, raised at
`tests_emit/test_emit.py:557` before any class is built or any payload offered.
`21c371d37` *"delete(apparatus): the construction grades 2,608 of 2,608, and there is no
budget"* took 2,194 lines out of `harness.py` including that class — *"The corpus branch, the
examples branch and the draw branch are gone with their parameters"* — and
`tests_emit/test_emit.py`'s `fixtures()` still calls it. Measured, it is the ONLY name in that
call that is missing: `fixtured`, `FORMAT_STRATEGIES`, `conforms` all still resolve. This is a
stale test-side fixture in another lane's file and it is not mine to repoint.

**(2) One of the ten: `check_refuses`'s `entered` filter asks a different question than the
reason it deletes.** `test_a_conditional_no_value_was_offered_for_is_not_a_pass` fails at
`assert result.unreached == unreached`, with `()` where
`harness.unreached_conditionals` — asked directly, two lines earlier in the same test, and
passing — answers
`('the instance is outside the region {"required": ["authentication"]} selects and the node
states no else, so no arm is in force and no value was offered',)`. The reason is built and
then dropped by `codegen/harness.py::check_refuses`:

```python
entered = _entered_conditionals(schema, instance, validator_cls=cls)
res.unreached = tuple(r for r in res.unreached if not any(k in r for k in entered))
```

The two functions ask different things. `unreached_conditionals(schema, instance)` asks
whether **the drawn instance** sits outside the conditional's region — a fact about the draw,
which is what the `absent` verdict is about. `_entered_conditionals(schema, instance)` asks
whether **a purpose-built value** can put the conditional in force — a fact about the
builder's reach over the node, and it ignores its own `instance` argument when it answers.
Measured on `WVOD_SHAPE` with `{"subscriber_id": "s", "event_types": ["capabilities.changed"]}`:
`unreached_conditionals` names the `authentication` boundary, `_entered_conditionals` returns
BOTH conditions, the filter erases the reason, and `_undeclared_verdict` reads `pass` where
the row exists to make it read `absent:1_of_2_conditionals_unreached`.

**And it is class-independent, which is what rules the pinned default out on its own.**
Both functions take `(schema, instance)` and read no class; and the class this row grades is
`CarriesWhatWasOffered`, a plain `pydantic.BaseModel` declared in the test body, so
`AdCPBaseModel._supply_the_pins_the_document_states` — where the pin is folded in — is not
even in its MRO.

So (2) is a real defect, in a file this lane may write, and it is NOT widened into: a filter
conflating the builder's reach with the draw's position is one fix, the row selection inside
one refusal's error list is another, and the only thing they share is that an empty tuple was
reported. Shape is not cause. It wants its own row, its own measurement of how many of the
326 `absent` pairs it moves, and a lane that is not holding a ruling open.

## 4. The numbers

| | before | after |
|---|---|---|
| `tests_emit/test_union_dispatch.py` | 2 failed, 13 passed | **1 failed, 14 passed** |
| `tests_emit/test_refuses_check.py` | 10 failed, 23 passed | **10 failed, 23 passed** — §3, a different cause, untouched |
| `make gate` | 7 failed / 2563 passed of 2570 | **7 failed / 2563 passed of 2570** — unmoved |
| `./check` | emitted 1059 / refused 0; approximated 805 facts in 239 documents | **identical** |
| `make test` | 71 failed / 16125 passed / 2809 skipped / 0 errors | **71 / 16125 / 2809 / 0 — identical** |

`make test` does NOT improve, and the figures are read off
`test-results/sdk/report.json` rather than the terminal tally: that line says
`2823 skipped` where the report says 2809, and the report is the number the task states.
A refusal that localises again closed nothing else, which is consistent with where the
change sits — one row chosen out of a report that already carried it, on a path reached
only when every branch's document has already refused.

`make lint` and `mypy` were compared before and after on the changed file: 0 ruff findings
in it either way (the tree's 305 are elsewhere and pre-existing) and the same 20 mypy
findings in it either way.

`./check` is unmoved because no fact was being dropped here: the position a refusal names is
not a fact a class declares, and the change is on the refusal path only. It could not RISE —
nothing in `codegen/` was touched, so the compiler emitted the same tree, and the emission was
not re-run for that reason.

**Changed:** `src/adcp/types/_base.py` alone. It is the hand-written half of the package
(`codegen/emit.py`: *"`package` holds the hand-written `_base.py`"`), it is a
`codegen/store.py::_PACKAGE_INPUTS` entry rather than emitter output, and it is the site
`verdicts/a-pinned-default-is-the-documents-own.md` itself names for the Python-side half of
this decision. No generated file was hand-edited and no re-emission was needed.
