# salesagent-j3k2l.21 — prediction, then the grade against it

Written BEFORE the change, and graded in the second half of this file. The
bead's discipline: a prediction nobody wrote down cannot be wrong.

Branch `sdk/j3k2l21-root-type-list`, cut from `emit/from-scratch` at
`63dc1bb68c181d5bbc233a44f42dcecb0f9efab7`, worktree clean at that sha.

## What was already measured, and on which tree

Denominators, not predictions. All at `63dc1bb68`, CPython via the worktree's
own `.venv` (pydantic 2.13.5), bundle `schemas/cache/3.2`.

| measurement | value | denominator |
|---|---|---|
| portable documents | 1,054 | `bundle.portable` |
| emitted | 401 | the 1,054 |
| refused | 653 | the 1,054 |
| emitted modules | 390 | `src/adcp/types/_schemas/**/*.py` less `__init__.py` |
| refusals whose keyword is `type` | 35 | the 653 |

The bead's own baseline (390 modules, 462 graded pairs, 401 + 653 = 1,054)
reproduces exactly.

### The 35 `type` refusals partition four ways, and the bead's row owns 24 of them

| group | n | pointer | refusal |
|---|---|---|---|
| no row claims the root | **21** | `/` | `no D2 row selects this root (a later step's row does)` |
| a declared `null` beside another type at a PROPERTY | **3** | a property | `… cannot tell a DECLARED null from D4's rendering …` |
| a branch declaring no `type` | 10 | `/oneOf/0`, `/anyOf/0` | `an object node must declare type: object` (lane .24) |
| a scalar union root | 1 | `/` | `a union root of type 'string' is step 6` (step 6) |

### THE BEAD'S PREMISE FOR THE 21 IS REFUTED, MEASURED

The bead and the brief both say the 21 are "a root declaring a type LIST".
**The 3.2 bundle contains zero nodes whose `type` is a list at a document
root.** Enumerated by walking `bundle.nodes` over all 1,054 documents: 62 nodes
declare a list `type`, in 29 documents, and **all 62 are at a non-root
pointer**. `bundle.is_container_root`'s own docstring already states the same
number from the other side ("32 mappings, 5 arrays, **0 multi-type**").

So the row the bead's title names — "emit a root type list" — ALREADY EXISTS and
is `is_container_root`, whose `isinstance(kind, list): return True` claims every
root type list there could be. Its population is empty. Adding a second row for
it would be a row that matches nothing, and `emit.lower_document` would then
raise `AmbiguousRoot` on the first document that ever did declare one.

The 21 refuse for a different reason, which splits two ways:

* **14 documents**: the root carries `allOf` AND an `anyOf` that is a
  PRESENCE-ONLY rule (a combinator of `required` groups).
  `composes_at_the_root` excludes them with a bare key test —
  `not any(k in doc for k in ("oneOf", "anyOf"))` — while `union_root` excludes
  them because `rules.presence_only` says that `anyOf` is not a union of shapes.
  **Two readings of "is there a union beside the `allOf`", and a 14-document
  hole between them.** The repo already names this defect class in
  `union_root`'s own docstring: "ONE implementation of the keyword read, and it
  is the LOWERING'S".
* **7 documents**: the root declares no schema shape at all — four data
  documents (`core/asset-group-vocabulary.json`,
  `core/format-shape-vocabulary.json`, `creative/asset-types/index.json`,
  `extensions/index.json`), one `deprecated`-only stub
  (`core/signal-pricing-option.json`) and two conditional-only roots
  (`core/targeting-{unknown-age-eligibility,verified-age-basis}-constraint.json`,
  each exactly `if`/`then`). No row can claim these and none ever will.

### The instrument defect is reproduced directly, and it has TWO halves

`compare_schema` on a hand-built document declaring
`{"type": ["string","null"], "format": "date-time"}` and
`{"type": ["number","null"], "minimum": 0, "maximum": 1}` against the model D4
renders for them (`AwareDatetime | None = None`, `float | None = None`):

```
differs 2  /properties/completed_at/type: the document says ['string','null'], the model 'string'
           /properties/rate/type:         the document says ['number','null'],  the model 'number'
added   2  /properties/completed_at/default: the model says None, the document nothing
           /properties/rate/default:         the model says None, the document nothing
```

* **Half one** is the one the bead names: `_normalize` unwraps a one-null-branch
  `anyOf` as absence, so the model's declared null is erased before the
  comparison sees it.
* **Half two the bead does not name, and it blocks the same 3 documents.**
  `_narrows_nothing`'s `default` clause reads
  `value is None and "null" not in str(doc.get("type", ""))`. The null half of
  that is a PROXY for "a model-only default here is an invention rather than
  D4's spelling of absence", and the fact it is proxying for is the `required`
  axis, which `_narrows_nothing` cannot see. It was introduced in `296175436`
  with no measurement naming it, at a time when every nullable node in the
  bundle was refused — so it has had **0 sites** and has never been graded.

## The predictions

### P1 — the row. 0 documents, and I add no row.

I predict I add **no new entry to `emit.ROWS` and no new selector**, because the
population of the row the bead names is 0 and the row already exists. What I
change instead is the one selector whose reading of the union keyword disagrees
with the lowering's.

### P2 — the 3, after the harness fix

All **3 of 3** documents emit (`core/delivery-metrics.json`,
`core/error.json`, `core/webhook-activity-record.json`), and both halves above
are needed: fixing only `_normalize` leaves `added` at 2 and the pair red at
`comparison:model_adds_a_fact`.

I predict the `default` fix makes `_narrows_nothing` read the `required` axis
instead of the null proxy, which **tightens one cell and loosens one**:

| document says | today | after |
|---|---|---|
| optional, not nullable | admitted | admitted |
| optional, nullable | **reported** | admitted (the fix) |
| required, nullable | reported | reported |
| required, not nullable | **admitted** | reported (tightened) |

I predict the tightened cell has **0 sites** in the emitted population — a
required property carrying `default: None` would be a model making a demanded
key omissible — so it costs no pair. This is the prediction I am least sure of.

### P3 — `added`, `missing`, `differs`

**0, 0, 0 — unchanged.** This is the invariant that binds, and if the `default`
half is wrong this is where it shows.

### P4 — N and the population

| | base `63dc1bb68` | predicted |
|---|---|---|
| graded pairs | 462 | **470** |
| emitted modules | 390 | **396** |
| portable emitted | 401 | **407** |
| portable refused | 653 | **647** |
| `type` refusals | 35 | **21** |

Reasoning: +3 from the nullable documents, +3 for documents that reference one
of them and refuse on nothing else. The 14 closed-hole documents I predict
**mostly refuse on their own keyword** rather than emit — they carry
`definitions`, `$ref`, `not` and `if` — so I predict **0 to 2 of the 14 emit**
and the rest move from a deferral to a real keyword. `type` refusals drop to 21
because the 21-document group loses its 14 (moved to another keyword) and its 7
(refused on what they declare), and the 3 nullable ones emit — leaving the 10
branch-type and the 1 scalar-union-root, plus 10 I cannot predict the keyword
of. **I predict the `type` count between 11 and 25 and name 21 as the point
estimate; this is a soft number.**

### P5 — `composes_at_the_root`

**287 → 301**, 0 documents lost, and **0 collisions with any other row** over
all 1,054. Measured as a counterfactual before writing the change, so this is a
prediction only about it surviving the suite.

### P6 — the 7, and the exit

The 7 cannot emit. I predict the exit is met for them by a refusal that names
**what the root declares** rather than promising a later row, at the keyword
`type` with pointer `/`. I predict **no row and no selector** can honestly take
them and that the suite needs no new allowance for them.

### P7 — the fire-probe

I predict that inverting the declared-null distinction (making `_normalize`
unwrap a declared null again) turns the new test RED at the `/type` assertion,
and that inverting the `required` discriminator turns it red at `added`. Both
probed by hand and the red shown.

### P8 — the baseline's own red set

I measured the baseline suite at `63dc1bb68` before writing a line of code, on
this worktree's own interpreter (CPython 3.14.6, the one `acp-fresh`'s venv
uses) with `PYTHONPATH=. python -m pytest tests/ -q -p no:randomly -n 3`. The
3-worker figure is the brief's, not the pyproject default: four lanes at ten
workers each is what the OOM killer has already taken down twice today.

I predict the branch's red set is **IDENTICAL to the baseline's, by name**, and
that any test my change reddens is one whose assertion is keyed on a refusal
this row retires or on a metric constant this row moves — never one whose
subject is a behaviour. Attributed by topology, not by anyone's word.

---

# The grade

Measured after the change. Every "before" number is `emit/from-scratch` at
`63dc1bb68c181d5bbc233a44f42dcecb0f9efab7`; every "after" number is this
branch's tip. Both on CPython 3.14.6, pydantic 2.13.5,
datamodel-code-generator 0.86.0, hypothesis 6.168.5, bundle
`schemas/cache/3.2` (1,054 portable documents).

**The baseline is GREEN — `611 passed in 607.75s` — so every red on this branch
is mine and attribution needs no argument.** That is also the one P8 input I did
not have when I wrote the prediction.

| | predicted | measured | verdict |
|---|---|---|---|
| P1 new row in `emit.ROWS` | none | **none** | right |
| P2 of the 3, how many emit | 3 | **2**; the third refuses on `allOf` | WRONG |
| P2 the `default` half is needed | yes | **yes** | right |
| P2 the tightened `required` cell | 0 sites | **0 sites** | right |
| P3 `added` / `missing` / `differs` | 0 / 0 / 0 | **0 / 0 / 0** | right |
| P4 graded pairs | 462 → 470 | 462 → **484** | wrong size, right sign |
| P4 emitted modules | 390 → 396 | 390 → **409** | wrong size, right sign |
| P4 portable emitted | 401 → 407 | 401 → **420** | wrong size, right sign |
| P4 portable refused | 653 → 647 | 653 → **634** | wrong size, right sign |
| P4 `type` refusals | 35 → 21 (11–25) | 35 → **15** | WRONG, below the range |
| P5 `composes_at_the_root` | 287 → 301, 0 lost, 0 collisions | **301, 0, 0** | right |
| P6 the 7 refuse, no new row | yes, all at `type` | **yes; 4 on `type`, 2 on `if`, 1 on `$ref`** | right in kind, wrong on the keyword |
| P7 the fire-probe reddens | 2 probes | **5 probes, 5 reds** | right |

## P2 was wrong, and the way it was wrong found a second refusal

I predicted all three documents would emit once the comparison could read a
declared null. Two do. `core/delivery-metrics.json` does not: it refuses on
`allOf` at `/properties/reach_unit`, which is another row's keyword and has
nothing to do with this one.

What the prediction missed is that **two of the three never reached the null
check at all** — they stopped one clause later, at the CONSTRAINED-ARM refusal in
the same function, on `maximum` and on `format`. That refusal's stated reason is
the same instrument blindness ("the comparison folds a model's `anyOf` back into
a type LIST only where every branch is a bare type"), and it is TRUE for two or
more live arms and FALSE for one. With exactly one live arm beside the null the
node is `T | None`, which is case 1 of the fold rather than case 2, and case 1
keeps the live branch's own keys. Measured in both directions rather than
assumed:

| document node | faithful model | a model that drops it | a model that widens it |
|---|---|---|---|
| `{type: [number, null], minimum: 0, maximum: 1}` | pass | `/minimum`, `/maximum` | `/maximum` |
| `{type: [string, null], format: date-time}` | pass | `/format` | — |
| `{type: [string, integer], minLength: 4}` | **`model_drops_a_fact`** | — | — |
| the same with a `null` beside it | **`model_drops_a_fact`** | — | — |

So the refusal is narrowed to `len(live) > 1` and the blind shape still refuses.
Had I only removed the null clause, 2 of my 3 documents would still refuse and
the row would have looked finished.

## P4's numbers were all wrong in size and all right in sign

The mechanism was predicted correctly and the magnitude was not: I reasoned about
the three documents and a handful of referrers, and `core/error.json` is
referenced far more widely than "a handful". 18 documents emit because of the
null arm and one more because of the lone constrained arm.

| | base `63dc1bb68` | this branch |
|---|---|---|
| portable emitted / refused | 401 / 653 | **420 / 634** |
| emitted modules | 390 | **409** |
| graded pairs | 462 | **484** |
| document facts compared | 4,658 | **5,966** |
| model-only facts examined | 1,104 | **1,600** |
| `missing` | 0 | **0** |
| `differs` | 0 | **0** |
| `added` | **0** | **0** |
| `url_typed` | 72 | **74** |
| comparison-red pairs | 0 | **0** |
| rows claiming exactly one document | 1,033 | **1,047** |
| rows claiming none | 21 | **7** |
| rows claiming two | 0 | **0** |

**`added == 0` is the invariant that bound and it held.** It is also the number
the `default` half was about: with `_normalize` fixed and `_narrows_nothing` left
alone, the two optional nullable properties report `added` at
`/properties/*/default` and the pairs are red at `comparison:model_adds_a_fact`.
Both halves are needed and neither is a widened rule — the `default` clause reads
the `required` axis it was already proxying for, which TIGHTENS one cell (a
model-only `default: null` on a key the document demands is now reported, where
the proxy admitted it) and loosens exactly the D4 cell.

**The harness change is a no-op on the base population, measured both ways.** On
the base tree's 462 pairs, before and after the harness commit: compared 4,658,
model-only 1,104, missing 0, differs 0, added 0, url_typed 72 — identical. That
is the right outcome (no pair the base tree emits has a declared null) and it is
also why the change needs the probes below rather than a population number.

## P4's `type` count was wrong below its own range

I named 21 and a range of 11–25, and measured **15**. The 35 break up as: 21
roots no row claimed, of which 14 moved to `anyOf`/`if` and 7 stayed as roots no
row describes — but 2 of those 7 refuse on `if` and 1 on `$ref` now, so only 4
are left on `type`; 3 nullable properties, of which 2 emit and 1 moved to
`allOf`; 10 branch-type refusals and 1 scalar union root, both other rows'. So
4 + 10 + 1 = 15. The range was wrong because I assumed the 7 would all land on
`type`, and `ROOT_KIND` names `$ref` and `if` ahead of it.

## P6 was right in kind and wrong on the keyword, which is the better answer

I predicted the 7 would refuse at `type` with pointer `/`. They refuse at
pointer `/` and on the keyword their kind is READ FROM, which is `$ref` for
`core/signal-pricing-option.json` (a bare root reference), `if` for the two
`core/targeting-*-age-*-constraint.json` (conditional-only roots) and `type` for
the four data documents, where the absence of a kind keyword IS the fact. A
refusal naming `type` on a document that states no `type` would have been the
same defect the old message had, one step quieter.

## The EXIT, graded over the bead's own 24 documents by name

All 24 emit or refuse on a non-deferral keyword, and **0 carry a deferral**:

* **2 emit** — `core/error.json`, `core/webhook-activity-record.json`.
* **14 refuse on `anyOf`** at `/` — the closed selector hole; the keyword is real
  and present at the pointer named.
* **1 refuses on `allOf`** at `/properties/reach_unit` —
  `core/delivery-metrics.json`.
* **4 refuse on `type`** at `/` with the absence of a kind keyword stated.
* **2 refuse on `if`**, **1 on `$ref`**, at `/`.

## The fire-probe: five planted, five red

Each probe is a distinct way to lose the distinction, and each reddens
`test_a_declared_null_is_never_read_as_absence` at a different assertion. The
file was restored byte-identical after each (`diff` clean) and the test re-run
green.

| probe | the break | reddens at |
|---|---|---|
| 1 | `_declares_null` returns `False` — a declared null read as absence again | the faithful required-nullable pair |
| 2 | `_declares_null` returns `True` — the fold made unconditional, the "silencer" fix | D4's optional non-nullable pair |
| 3 | the old `"null" not in str(doc["type"])` proxy restored | the optional NULLABLE pair, at `added` |
| 4 | `_narrows_nothing` ignores `required` | the `required=True` cell of the rule |
| 5 | `compare` stops passing `required` down — the parameter inert | the end-to-end required cell |

Probe 5 is the one that matters most and the one I nearly did not write: a wired
parameter nothing passes is a rule that reads a default forever, and every other
probe stays green through it.

## One arm I wrote, measured, and removed

`_normalize` recurses through a `$ref`, and I propagated `declared_null` through
it on the reasoning that the target IS the node. Then I counted the sites: over
the 484 graded pairs, **5 positions have a document declaring `null` and all 5
render as an `anyOf`, 0 as a `$ref`** — pydantic names a nested CLASS that way,
and a class is not a null arm. So the propagation was an arm with no site, which
is green for free; it is removed, and re-measuring the comparison totals with and
without it gives the identical 5,966 / 1,600 / 0 / 0 / 0 / 74. It also fails safe
without it: such a position would not fold, the document's `type` would read as
missing, and the pair would redden.

The 5 live positions, named: `core/error.json`'s discriminator `value`, and
`core/webhook-activity-record.json`'s `completed_at`, `error_message`,
`http_status_code` and `response_time_ms` — the last three were not in the bead's
population at all and came with the document.

## The invariant the brief names, measured rather than assumed

A required-nullable field whose value is `None` **does** survive to the wire:
`ErrorIssuesItemDiscriminatorItem.model_validate({"property_name": "kind",
"value": None})` dumps `{'property_name': 'kind', 'value': None}` and
`model_dump_json` gives `{"property_name":"kind","value":null}`. I did not touch
a serializer.

**But the mechanism the brief names is not in this tree.** There is no
`@model_serializer` in `src/adcp/types/_base.py` and no required-nullable
retention rule: the null survives because the DEFAULT dump keeps it, and nothing
in `src/`, `codegen/` or `tests/` passes `exclude_none` (grepped, 0 hits). Under
`exclude_none=True` a required-nullable `None` IS dropped. That is a real gap and
it is not this row's — reported rather than fixed, because fixing it means
writing the serializer the brief says already exists.

## Two things I found and did not act on

* **`union_root`'s docstring says 156 and the bundle measures 126.** The
  committed test asserts 126 (`tests/test_emit.py`), so the prose is stale and the
  assertion is right. Untouched: it is another row's number and nothing reads the
  prose.
* **`_narrows_nothing`'s `"null" not in str(doc.get("type", ""))`** was a
  substring test over the `repr` of a `type` value, so it also matched a type
  named `"null"` anywhere in a list and would have matched a string type whose
  text contained "null". It is gone rather than corrected; noting it because the
  shape — a type test written as a substring search — is worth grepping for
  elsewhere.
