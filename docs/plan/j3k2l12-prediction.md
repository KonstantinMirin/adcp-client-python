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

<!-- GRADE BELOW THIS LINE, in the same file, naming every prediction that was wrong. -->
