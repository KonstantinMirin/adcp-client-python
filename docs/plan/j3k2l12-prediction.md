# salesagent-j3k2l.12 — prediction, then the grade against it

Written BEFORE the outcome was measured, and graded in the second half of this
file. The bead's discipline: a prediction nobody wrote down cannot be wrong.

Branch `sdk/j3k2l12-constrained-type-once`, cut from `emit/from-scratch` at
`fc9a880594caac2c01ee7a663d848528c80bdb49`, worktree clean at that sha.

## What was already measured, and on which tree

These are DENOMINATORS, not predictions. All on the emitted tree at
`fc9a88059` (383 modules under `src/adcp/types/_schemas`, 448 graded pairs).
The bead body's "282 modules / 68 inline sites / 11 distinct shapes" is one
tree behind and is superseded here.

The instrument: an AST walk over every emitted module, counting each
`Annotated[T, Field(...)]` whose `Field` carries at least one kwarg that is not
`alias` / `default` / `description` / `json_schema_extra` / `title`. A shape is
`(rendered base type, sorted constraint kwargs)` with D4's trailing `| None`
branch folded out — a nullable branch is a fact about PRESENCE, so two sites of
one constrained type count as two.

| measurement | value | denominator |
|---|---|---|
| emitted modules | 383 | `src/adcp/types/_schemas/**/*.py` less `__init__.py` |
| inline constrained sites | 308 | the 383 modules |
| distinct shapes | 78 | the 308 sites |
| shapes repeating at 2+ | 31 | the 78 shapes, covering 261 of the 308 sites |
| shapes occurring once | 47 | the 78 shapes, covering 47 of the 308 sites |
| `format: uri` sites | 27 in 23 modules | the 383 modules |
| …of those, carrying a string constraint too | 1 | the 27 (`core/platform-extension-ref.json`, `pattern: '^https://'`) |

The five largest repeats, with their site counts out of 308:
`int ge=1` ×40, `float ge=0.0` ×37, `int ge=0` ×34, `str min_length=1` ×29,
`float ge=0.0 le=100.0` ×19.

The bundle-wide figures in the bead body (1,026 distinct inline signatures, 794
repeating at 2+ over 41,798 sites, 702 with no name anywhere) are over the 1,054
`bundle.portable` DOCUMENTS and are unaffected by the tree moving. Re-measured
`len(bundle.portable(schemas/cache/3.2)) == 1054`, so the 1,057 figure in the
body is the file count and the three extra are bundle metadata.

## The predictions

### P1 — distinct inline shapes remaining

**47**, down from 78, over 47 sites, down from 308. Every shape repeating at 2+
gets a name; a shape occurring once stays inline, which is the bead's own exit.
Zero shapes repeat at 2+ afterwards.

### P2 — how many aliases I declare

**30** symbols in `adcp.types.constraints`: 29 derived from a repeated
constraint, plus `AdCPUrl`.

That is 31 repeating shapes less the 2 I predict rung 2 covers with a pydantic
standard type (`NonNegativeInt` for `{integer, minimum: 0}` at 34 sites,
`NonNegativeFloat` for `{number, minimum: 0}` at 37 sites), plus `AdCPUrl`:
31 − 2 + 1 = 30.

**Rung 1 I predict covers 0 inline sites, and not because no titled root
matches.** D5 reaches rung 1 "by `$ref` as an import", and an inline
declaration has no `$ref`. Importing another document's titled root for a field
that does not reference it would invent a reference the document does not state
(P2) and would put that root's own `description` into the citing field's
rendered schema, which is a fact the citing document does not state. So rung 1
needs no work in this step and already works where a document does say `$ref`.
I predict **2 of the 31** repeating shapes are nonetheless content-equal to some
titled scalar root of the bundle (`^[A-Z]{3}$` and `min_length=1` look like the
candidates), and I will report that count as a fact rather than act on it.

### P3 — how many sites each replaces

261 sites replaced across the 31 named shapes, which is 85% of the 308. The
distribution is the table above: four shapes carry 140 of the 261, and
17 of the 31 carry 2 or 3 sites each.

### P4 — `compared`, `model_facts`, `added`

Against whatever the baseline turns out to be at the clean sha (the brief's
4,276 compared / 896 model-only / 0 added was measured on a tree with four step
tests red, so it is not yet a verified baseline):

* **`compared` — UNCHANGED.** An alias substitution changes no document fact and
  no fact the model states: pydantic flattens `Annotated`, so
  `Annotated[IntMin1, Field(description=...)]` where
  `IntMin1 = Annotated[int, Field(ge=1)]` renders the same
  `{"type": "integer", "minimum": 1, "description": ...}` the inline site
  renders. The `pattern` the one `format: uri` site states is still LOOKED FOR,
  so it still counts as compared; the new category stops it landing in
  `missing` rather than stopping it being counted.
* **`model_facts` — +27.** `AdCPUrl` renders `minLength: 1`, which no
  `format: uri` document states, at every one of the 27 sites.
* **`added` — 0, unchanged.** All 27 of those `minLength: 1` facts are admitted
  by the new comparison category, and nothing else in this change states a fact
  the document does not.

### P5 — N

**448 → 452.** N must not drop and I predict it GROWS, because `_inner` in
`codegen/lower/containers.py` refuses a `format` on a node inside a container,
and once `uri` selects a type the format is IN the type, so `decided.format` is
`None` there and the refusal stops firing — the same way `date-time` already
passes through a container. I predict a handful of documents stop refusing. I
am least confident in this number of the five.

### P6 — the one prediction that could stop the uri half

**The accepts check goes RED at the 26 `format: uri` sites whose document
states no `^https://`.** `check_accepts` hands `strict_validate` an instance
`hypothesis_jsonschema` drew from the document, the document states only
`{"type": "string", "format": "uri"}`, and `format: uri` admits
`http://x.example` and `urn:isbn:0451450523`. `AdCPUrl` refuses both, so the
constructor raises after the schema half passed and the outcome is
`model_refused_valid`.

D5's passage addresses the WIDENING direction ("nothing widens, because
`strict_validate` validates against the document first") and the ceiling it
names is round-tripping. Neither is this. If this prediction measures true, the
model is NARROWER than its document at 26 sites, which is the defect the
accepts check exists to report — and per the brief I record the measurement on
the bead and STOP rather than implement around it. The alias half of this step
is independent of it and ships either way.

---

# The grade

Measured after the change, on this branch. Every "before" number is the emitted
tree at `fc9a880594caac2c01ee7a663d848528c80bdb49`; every "after" number is this
branch's tip. The whole-population figures are
`check_pair(pair_of(g), max_steps=None) for g in graded()`, run on each tree in
turn with the same interpreter (CPython 3.14.6), the same pins
(pydantic 2.13.5, datamodel-code-generator 0.86.0, hypothesis 6.168.5) and the
same bundle (`schemas/cache/3.2`, 1,054 portable documents).

**Three of six predictions were wrong. P6 was wrong in the direction that
decided whether the uri half ships at all.**

| | predicted | measured | verdict |
|---|---|---|---|
| P1 distinct inline shapes remaining | 47 | **0** scalar, 29 container | WRONG |
| P2 aliases declared | 30 | **59** (58 derived + `AdCPUrl`) | WRONG |
| P3 sites replaced | 261 | **278** scalar sites, all of them | wrong, same reason as P2 |
| P4 `compared` | unchanged (4,276) | **4,658** (+382) | WRONG |
| P4 `model_facts` | +27 (923) | **1,069** (+173) | WRONG |
| P4 `added` | 0 | **0** | right |
| P5 N | 448 → 452 | 448 → **462** pairs, 383 → **390** modules | wrong number, right sign |
| P6 accepts check at a bare `uri` | RED at 26 sites | **PASSES at all of them** | WRONG |

## P1, P2 and P3 were one mistake, and it was in the plan reading

I predicted the census version: name the 29 shapes that repeat, leave the 28
that occur once inline. I then measured a reason not to, and it is not a
preference. **A census makes one module's text a function of which OTHER
documents are in the run.** The README's documented one-document command would
emit `Annotated[int, Field(ge=1)]` where the full run emits `IntMin1`, for the
same document and the same bundle. P7 permits that — the document set is an
input — but only the full population is byte-compared, so the disagreement
would be latent. D5's own sentence is "the walk resolves **every** constrained
scalar and container it meets to one type", so naming every shape is also the
plan's literal rule and needs no census at all.

So the measured population is not 47 remaining and 30 declared; it is:

| | before | after |
|---|---|---|
| emitted modules | 383 | 390 |
| SCALAR inline sites | 278 | **0** |
| SCALAR distinct shapes | 57 | **0** |
| …repeating at 2+ | 29 (250 of the 278 sites) | **0** |
| …occurring once | 28 | **0** |
| CONTAINER inline sites | 30 | 41 |
| CONTAINER distinct shapes | 21 | 29 |
| …repeating at 2+ | 2 (11 sites) | 4 (16 sites) |
| symbols in `adcp.types.constraints` | 0 | **59** |

The bead's exit is "the emitted tree's inline repeat count drops to the shapes
that genuinely occur once". The scalar repeat count is **0**, and so is the
scalar inline count — the exit is met and then some, in the sense that nothing
is left inline for a repeat to be counted over.

**The 41 remaining container sites are the residual and they are named, not
hidden.** A bound on a list is a bound on the FIELD holding it — that is
`codegen/lower/containers.py`'s own rule and `compiler.Type` carries no
constraints for a container at all — so `Annotated[list[str], Field(min_length=1)]`
is already D5's correct form. Naming it would need the ELEMENT type in the
symbol, because `list[RightUse]` and `list[str]` are different types, and an
element type is a domain word, which D5's naming rule forbids. The bead's own
denominator agrees: its bundle-wide census counts "1,026 distinct inline
constrained-**scalar** signatures", so the scalar and container populations are
reported apart above rather than summed.

Two of the 29 scalar shapes went to rung 2, `NonNegativeInt` for
`{integer, minimum: 0}` (34 sites) and `NonNegativeFloat` for
`{number, minimum: 0}` (37 sites). **Both measurements, re-measured on
pydantic 2.13.5 rather than taken from the bead:** `NonNegativeInt` renders
`{"type": "integer", "minimum": 0}` and accepts 0, 1, 7 while refusing −1;
`NonNegativeFloat` renders `{"type": "number", "minimum": 0}` and accepts 0.0,
0.5, 7.0 while refusing −0.5. Both halves hold for both. The two banned
precedents also reproduce: `PositiveInt` renders `exclusiveMinimum: 0` (half one
fails) and `PositiveFloat` renders the same **and accepts 0.5, which the
document refuses** (half two fails, a widening).

**P2's rung-1 sub-prediction was right about the count and right for the wrong
reason.** I predicted 2 of 31 repeating shapes would be content-equal to a
titled scalar root and said I would report rather than act. Rung 1 is reached
`by $ref as an import` and an inline declaration has no `$ref`, so the question
does not arise and I did not measure the content equality — the number is
unmeasured and I am not claiming it.

## P4 was wrong because it forgot the growth P5 predicted

I predicted `compared` unchanged and `model_facts` +27, reasoning only about
what happens at a site that already existed. Both hold at those sites — an
alias substitution renders the same schema, because pydantic flattens
`Annotated` — but 14 more pairs now exist and they bring their own facts. Stated
over the population:

| | base `fc9a88059` | this branch |
|---|---|---|
| pairs | 448 | 462 |
| `pass` | 437 | 450 |
| `no_constraint_to_step` | 11 | 12 |
| refuses-check instances | 32,037 | 34,935 |
| document facts compared | 4,276 | 4,658 |
| model-only facts examined | 896 | 1,069 |
| `added` (narrowings) | **0** | **0** |
| `missing` | 0 | **0** |
| `differs` | 0 | **0** |
| `url_typed` (D5's new row) | — | **37** |

450 + 12 = 462, so every pair is `pass` or `no_constraint_to_step` and nothing
is red. `added == 0` held, which was the invariant that bound.

`url_typed` is 37 and I predicted 28: 36 `minLength` admissions and the ONE
`pattern` the bundle states on a `format: uri` node
(`core/platform-extension-ref.json#/properties/uri`). 36 rather than 27 because
a position inside a nested class is graded twice — once at its own pair and once
at its parent's — so `core/overlay.json` contributes its three `visual` URLs at
both `#` and `#/properties/visual`.

**The brief's baseline numbers: two reproduced, one did not.** `compared` 4,276
and `model_facts` 896 and `added` 0 are exactly what the base tree measures. The
refuses-check instance count does not: the brief says 32,031, the committed test
asserted 31,923, and the base tree measures **32,037**. Hypothesis runs
`derandomize=True` here, so that figure is deterministic for a given (code,
tree, bundle) — three different values mean three different code states, not
flakiness. It is the number the four red step tests sit on, so it is yours; I
pinned what my tree measures and nothing else.

## P5 was right in sign and wrong in size

448 → 462 pairs, not 452, and 383 → 390 modules. The mechanism was predicted
correctly: once the constraints are on the TYPE, `lower.containers._inner` has
nothing left to refuse, so a bound inside `list[...]` has somewhere to go. Seven
documents stop refusing, and two of them are the two that module's own docstring
named as refused on an inner `^[A-Z]{2}$` — `brand/rights-terms.json` and
`property/property-list-filters.json` — which now emit `list[StrMatchingEFC12812]`.
The other five are `core/creative-brief.json`,
`core/data-provider-signal-selector.json`,
`core/requirements/audio-asset-requirements.json`,
`core/requirements/video-asset-requirements.json` and
`error-details/version-unsupported.json`.

## P6 was wrong, and the way it was wrong is the finding

I predicted the accepts check would go RED at the 26 bare `format: uri` sites,
because the document admits `http://x.example` and `AdCPUrl` refuses it. **It
passes.** `hypothesis_jsonschema`'s own `uri` strategy drew a `https://` URL in
**40 of 40 distinct instances**, so the generator never produces a value the
type refuses.

The narrowing it would have caught is nonetheless real, and measured by hand on
a document stating exactly `{"type": "string", "format": "uri"}`:

| value | the document | `str` + annotation | `AdCPUrl` |
|---|---|---|---|
| `https://x.test/ext` | accepts | accepts | accepts |
| `http://x.example` | **accepts** | accepts | **REFUSES** |
| `urn:isbn:0451450523` | **accepts** | accepts | **REFUSES** |
| `file:///etc/passwd` | **accepts** | accepts | **REFUSES** |

`format: uri` references RFC 3986, which admits every scheme, so at the 29 of
this population's 30 `uri` positions whose document states no `pattern`, the SDK
is NARROWER than its document — and **no check in this harness reports it.** The
accepts check is blind for the reason above, which is the same blindness
`harness._validating` already records for `date-time`; the comparison is blind
because the fact is not a keyword either side states.

This does not reverse the decision and I have not implemented around it. D5 is
explicit — every `format: uri` field is `AdCPUrl`, and the two settled decisions
on the bead say the same — and the plan names round-tripping as the ceiling it
accepts. What I am reporting is a SECOND ceiling the plan does not name: the
accepted set at 29 of 30 positions, ungraded. It is recorded in
`emit.FORMAT_TYPES` and in `harness._schema_half_enforces` beside the row, so a
later lane finds it at the code rather than in this file.

## The suite

`pytest tests/ -q -p no:randomly`, final line verbatim:

```
4 failed, 590 passed in 973.61s (0:16:13)
```

The four are the harness STEP path and are present at `fc9a88059`:
`test_the_harness_steps_every_one_of_d6s_six_families`,
`test_a_step_of_a_whole_instance_keyword_bites_the_document_that_states_it`,
`test_the_uniqueItems_step_grades_no_emitted_class_and_that_is_recorded` and
`tests/test_harness_steps.py::test_an_unsteppable_site_is_reported_rather_than_passed`.

**Attributed by topology, not by anyone's word.** Two of them assert
`uniqueItems == (479, 198)`; the base tree and this branch both measure
`(462, 198)`, and `not` and `then` are identical on both too — `_step_census`
walks every portable document through `harness.steps`, so it has no dependency on
the emitted population at all. The fourth asserts `harness_error` and both trees
return `no_evidence`. This branch's `codegen/harness.py` change is 88 insertions
and 0 deletions, none of them in `steps`.

## Two tests whose instrument this change invalidated

Neither was weakened to pass, and both had the same shape: an assertion keyed on
the old RENDERING.

* `test_a_subclass_never_restates_an_inherited_field` found a declared field by
  grepping the class body for `": Annotated"`. A declared field is now
  `label: StrMinLen2`, so the grep matched nothing and the test compared an
  EMPTY list against `["label"]` — it would have reported the no-restatement rule
  as holding while a subclass shadowed every inherited field. It reads the class
  body's names instead.
* `test_a_narrowing_restatement_is_declared_by_the_subclass` asserted
  `"max_length=8" in text`. It now asks `codegen.constraints` for the symbol the
  constraint derives — a literal would pin whatever the namer currently does —
  and reads the bounds off the live field.

And two tests that asserted a REFUSAL this step was built to retire:
`test_a_constraint_inside_a_container_refuses_rather_than_being_dropped` became
`..._is_named_and_a_format_still_refuses`, and
`test_a_multi_type_property_applies_each_keyword_to_its_own_branch` kept its
refusal with a NEW reason — the rendering obstacle is gone, but
`harness._normalize` folds a model's `anyOf` into a document's `type` list only
where every branch is bare, so a constrained branch reads as dropping two facts
and the node would be emitted ungraded. 0 multi-type node in an emitted document
states anything beyond its `type`, so the refusal costs nothing.

## One thing the prediction did not anticipate at all

**`Annotated[AnyUrl, Field(pattern=...)]`
does not merely drop the pattern, it fails to BUILD.** pydantic raises "Unable to
apply constraint 'pattern' … for schema of type 'function-wrap'" while
constructing the model, so `core/platform_extension_ref.py` did not import on
the first emission. That is the loud failure the bead's note predicted, and it is
why `decide_type` now drops `pattern` deliberately and refuses by name on any
other string constraint at such a node.
