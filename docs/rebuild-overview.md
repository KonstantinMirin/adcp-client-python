# Rebuilding the type compiler: five layers, one dispatch, and zero refusals

**Status: work in progress on `emit/from-scratch`.** This document is the overview a pull request
would have carried. There is no PR, because `emit/from-scratch` shares no ancestor with `main` —
the roots differ (`a3d892c4` against `6f1f5eb4`, 495 commits against 837), `git merge-base` finds
nothing, and GitHub refuses a pull request between unrelated histories. So the explanation is
versioned with the work instead, and the integration story is still open.

---


## The decision that changes the project (2026-10-26)

**Zero refusals is the outcome.** Every schema document is represented as a Python class, root
model, enumeration or alias. Where a keyword cannot be expressed faithfully, the type **widens**:
the fact is *dropped*, never substituted, so an approximation can only ever be looser. The gap is
then declared on the emitted class, attributed (to a cell of ours or to a site-level upstream
issue), and the upstream issue is filed. `docs/plan/rebuild-plan.md` §2 states the five-rung
ladder (KEYWORD, TYPE, JOIN, CONTAINER, TOP) and §7 is now an empty set. Commit `38eef94` carries
the design; commits before it read under the old rule and will confuse you if you take them as
current.

**Why this is not a loosening.** Every emitted class carries `strict_validate`, which validates a
payload against the class's own schema document *before* constructing anything. The document
decides acceptance; the annotation does not. So a widened annotation costs **static precision**
and never runtime correctness, and the only annotation that can be wrong is a *tight* one.

This corrects a contradiction the semantics document already carried. The old refusal rule said a
partial model "would claim conformance to a document it does not enforce" — which presumes the
annotation **is** the conformance claim, the exact proposition `strict_validate` denies. The two
sentences could not both stand. Refusal survives in two places only: a narrowing (which
`strict_validate` cannot repair) and a document with no record (where there is no schema half at
all).

## The guard against the obvious failure mode

285 refusals are impossible to ignore. Declared approximations in a report are easy to. So two
equalities sit **above** the three checks of `rebuild-plan.md` §8, and neither side of either is
hand-written:

1. **The comparison's keyword set equals the set the declaration renders.** A keyword missing from
   the comparison is unexamined in both directions and passes either way.
2. **The approximated set equals the declared set, in both directions.** Every approximated fact
   has a declaration or it is *missing* (a defect); every declaration has an approximated fact or
   it is *over-declared* (also a defect, and the thing that stops declarations rotting into stale
   excuses).

The teeth are in the accepts check: for every fact an approximation drops, the draw takes **the
dropped keyword's own value classes** and the class must accept every one. A widening is therefore
*proved*, not believed — a narrowing wearing a declaration fails by value and by pointer. That is
what keeps "approximated" from being an allowlist: a declaration is a claim with two instruments
pointed at it.

`architecture.md` §14 step 8 is this instrument end to end **with zero cells widened**, and
nothing else in the directive may land before it passes.

## Which document decides what

| Path | Decides |
| --- | --- |
| [`docs/plan/rebuild-plan.md`](https://github.com/KonstantinMirin/adcp-client-python/blob/38eef94abdd1c7c5b89ed218cce6b5f0be0d6f4e/docs/plan/rebuild-plan.md) | **Semantics.** What each keyword compiles to at each position (§5), which keywords are admitted and compile to nothing (§6), the empty refusal set (§7), how the output is graded (§8). |
| [`docs/plan/architecture.md`](https://github.com/KonstantinMirin/adcp-client-python/blob/38eef94abdd1c7c5b89ed218cce6b5f0be0d6f4e/docs/plan/architecture.md) | **Structure.** The five layers and the one data type crossing each seam (§1), the paradigm (§2), the one dispatch (§5–6), the IR (§7), the layer rules (§11), and in **§14 the migration path these commits follow**. |
| [`docs/schema-patterns-brief.md`](https://github.com/KonstantinMirin/adcp-client-python/blob/38eef94abdd1c7c5b89ed218cce6b5f0be0d6f4e/docs/schema-patterns-brief.md) | The 60-second version of what in the bundle resists generation. Written for a conversation with the spec authors. |
| [`docs/schema-patterns-that-resist-generation.md`](https://github.com/KonstantinMirin/adcp-client-python/blob/38eef94abdd1c7c5b89ed218cce6b5f0be0d6f4e/docs/schema-patterns-that-resist-generation.md) | The long version: ten themes, each with measured evidence and a tag for whose problem it is. |

Where the two plan documents overlap, the semantics document governs a keyword's meaning and the
architecture document governs where that meaning is written down and who reads it.
`architecture.md` §13 names every place the first forces a structure the second decides
differently.

## How to read the branch

`git log --oneline` on this branch reads as `architecture.md` §14's migration path, in order. Review the commits
against the numbered steps, not as one diff. Each step says whether it changes the emitted tree,
the report, or neither; a step marked *bytes* is a relocation, proved by regenerating the tree and
comparing byte for byte.

What the branch carries, by area:

- **`codegen/`** (25 files, +8,065/−3,524) — the new layering: `keywords.py` (the keyword ×
  position declaration), `schema/nodes.py` and `schema/parse.py` (the one parser), `lower/decide.py`
  (the one dispatch) with a handler per node kind, `ir.py` and `render.py` (the IR and the one
  module that knows pydantic).
- **`src/adcp/types/_schemas/**/*.json`** (403 files) — the packaged documents of record,
  re-saved by our own `$ref` inliner. The large line counts are reformatting and de-canonicalisation,
  not schema changes.
- **`src/adcp/types/_schemas/**/*.py`** (25 files) — the emitted modules that actually moved, each
  attributable to a sentence in the semantics document the old output violated.
- **`tests/`** (15 files, +4,308/−1,056) — `test_keywords.py`, `test_type_checker.py`,
  `populations.py`, and the per-row re-measurements.
- **`docs/`** (4 files) — the two plan documents and the two schema-pattern notes.

## Where the work stands

Nine rows of `adcp-client-python-10l` are closed. The six structure rows (`.1`–`.6`) ran in §14
order, each merged `--no-ff` only after its emitted tree was re-measured:

1. an entry-point module, so no module of the compiler is ever bound as `__main__`;
2. the keyword × position declaration, which makes one keyword decision live in one place — the
   keyword screen and the verifier's compared set became its first two readers;
3. our own `$ref` inliner, replacing a delegated resolver that canonicalised while inlining, so a
   comparison failure stops being excused by a fold;
4. a complete IR, so nothing before the renderer holds a string of Python;
5. one parser that assigns position when it builds the node, with one exhaustive dispatch — position
   stops being recovered by parsing pointer strings;
6. refusal as a value rather than an exception, with the type checker as the test.

Three verifier rows closed alongside (`.17`, `.18`, `.19`).

**Not done, and a reviewer should not read the closed rows as more than they are:**

- `.7` (naming and content dedup as one pass over the finished module) is in progress.
- `.8`, the approximation instrument, is **not built**. Nothing else in the directive can land first.
- `.20` the faithful rows, `.21` the widened rows, `.22` the upstream issues, `.16` `deprecated` —
  all open.
- Seven keyword waves, all open, and **their ordering is void**: a wave was ordered by how many
  documents a keyword set *completes*, and once every document emits, nothing completes anything.
  The new ordering quantity is approximated facts closed, and it cannot be measured until `.8`,
  `.20` and `.21` land. Do not carry a figure from the old wave table.

9 of 22 rows closed. Most of the directive is ahead of this branch, not in it.

## Figures

All over bundle **3.2**'s **1,054 portable documents** (of 1,625 `.json` files in the bundle).
Every count here is one bundle version's property; `rebuild-plan.md` §1 is why none of them is
written into a plan document.

| | |
| --- | --- |
| emitted | **769** |
| refused | **285** |
| refusals by `resolved` (what counts) | **176** verdict (permanent), **109** deferred (our unwritten code) |
| refusals by `kind` (whose problem it is) | **144** chained, **92** verdict, **49** deferred |
| documents with a problem of their own | **141** — the other 144 are refused only because a `$ref` target is |

Reproduce:

```bash
PYTHONPATH=.:src uv run --no-sync python -c "
from pathlib import Path; from codegen import bundle
print('\n'.join(sorted(bundle.portable(Path('schemas/cache/3.2')))))" > /tmp/portable.txt
PYTHONPATH=.:src uv run --no-sync python -m codegen \
    --bundle schemas/cache/3.2 --tree /tmp/t $(cat /tmp/portable.txt) | tail -1
```

**Session movement, as two numbers that are never added.** Refusals went from `verdict 290 /
deferred 16` to `verdict 176 / deferred 109`. That is **not 114 documents fixed — it is 114
re-labelled**, from "permanently blocked" to "clearable work", which is what the structure phase
is for: a verdict minted for code nobody has written reports clearable work as finished. Emission
moved **+22** over the same period. An emission delta and a verdict-minting delta measure
different things and summing them produces a number that means nothing.

**Nothing is irreducible on this bundle.** `rebuild-plan.md` §7 names the one refusal the compiler
can still mint — a document with no defined accepted set — in three shapes, and all three are
empty here: 0 `$ref` targets outside the bundle, 0 cross-document reference cycles, 0 meta-schema
failures. No refusal in the run carries that kind. Beside them: 0 titleless roots, 0 list-valued
`items` at a schema position (the eight occurrences in the bundle are all under `/examples/`,
which is instance data), 0 `multipleOf`. That is why zero refusals is reachable for 3.2 rather
than aspirational — and it is the first thing to re-measure on the next bundle version.

## The suite is red on purpose

Last full run: **`1 failed, 1637 passed`** (650s).

The one failure is `test_an_arrays_bound_is_the_lists_and_not_its_elements`. For
`core/attestation-capabilities.json`, property `accepted_claim_types`, the schema element states
`{"type": "string", "format": "uri"}` and nothing about length, while the emitted element carries
`minLength: 1, maxLength: 2083` — pydantic's `HttpUrl` bounds, which the schema never states. The
model is therefore **tighter** than its document, which is the one defect the design says must
never happen, and `strict_validate` cannot repair it: the document admits a 2,220-character URI
and the construction then fails. The owner is `FORMAT_TYPES`, now in `codegen/lower/scalars.py`;
it is tracked on row `.10` (wave 2, which carries `format`); the test states its own diagnosis in
place and was
left red deliberately. Narrowing its assertion to go green would pin the defect. The gate for this
branch is "this one and no others".

🤖 Generated with [Claude Code](https://claude.com/claude-code)
