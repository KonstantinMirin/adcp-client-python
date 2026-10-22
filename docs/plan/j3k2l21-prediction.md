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
