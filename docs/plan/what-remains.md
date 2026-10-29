# What remains, derived from the two documents

Measured on trunk at `b9be6d46`. Every figure here is read off the code or a run, not off a
docstring — this project has produced seven stale censuses and several docstrings that described
a defect as a decision.

`emitted 1054 / refused 0 (deferred 0, verdict 0); accounted 1054; primary 0, chained 0;
approximated 120 facts in 53 documents.`

The compiler represents every portable document of bundle 3.2. **Seven groups of work remain, and
only one of them is about the compiler's output being wrong.**

## A. Step 10's exit condition — 1 of 5 clauses met

§14 step 10 states it: *"`refused` is 0 over the portable population, `decide` returns `Lowering`,
`Kind.DEFERRED` is gone, `APPROXIMATED` equals the declared set in both directions, and every
upstream attribution names a live issue."*

| clause | measured |
|---|---|
| `refused == 0` | **met** |
| `decide` returns `Lowering` | **not met** — returns `Decided \| Refusal` |
| `Kind.DEFERRED` gone | **not met** — live in `refusal.py` |
| `APPROXIMATED` equals the declared set both ways | **not met** — 3 declared-but-separable, 89 inseparable-but-undeclared |
| every upstream attribution names a live issue | **vacuous** — the registry is empty, so all 120 facts are `ours` |

Step 10 also says *"`Refusal` narrows to its one producer in `bundle.record`"*: **93 `Refusal(`
mint sites remain in the walk.** This is the seam collapse, and the document is explicit that it is
a *consequence* of every reachable cell having a rung — not the mechanism that gets them there.

**Relocation, not decision.** The sum type is what makes each remaining deferral a compile error
the moment `Refusal` leaves the seam, which is how the collapse finds them all.

## B. Step 8's residue

*"add `Rung` and `widens_to` to the cell and **retire `Effect.REFUSE`**"* — `keywords.py` still
carries 21 references to it. Step 8's own correction explains why it survived: of 141 primary
refusals exactly 1 sat on an `Effect.REFUSE` cell, so retiring it early would have crashed the run
on 140 documents. That constraint is gone — `refused` is 0.

**Relocation.**

## C. The waves — not started

§14: *"A wave's exit condition was 'these keywords stop refusing documents'. After step 10 no
keyword refuses anything, so the condition becomes **'these keywords' OURS approximations reach
0'**."* And the wave ORDER *"has to be re-measured, not carried over"* — by how many approximated
facts a wave's keywords close.

All 120 facts are `ours`. Three causes:

| facts | docs | rung | kind | keyword |
|---|---|---|---|---|
| 80 | 28 | CONTAINER | WIDENED | `patternProperties` — a regex-keyed mapping renders `dict[str, Any]`; the keys are accepted, their shape is not checked |
| 18 | 16 | JOIN | UNDERDETERMINED | `oneOf` — branches the dispatch cannot prove disjoint |
| 18 | 15 | JOIN | UNDERDETERMINED | `anyOf` — same |
| 1 | 1 | KEYWORD | WIDENED | `maxLength` |

**Decisions.** Each needs a rule family or a separator the documents do not yet state. 70 of the
89 silent UNDERDETERMINED sites are one shape reached through the forecast closure, so a fourth
separator empties most of that column in one change.

## D. §1's consumer surface — not built

Observable in the artifact, which is what makes these checkable without asserting anything about
`codegen/`.

- **The domain surface.** §1: *"re-exported from `adcp.types.<domain>`, where the domain is derived
  from the document's own path."* `types/__init__.py` says it itself: *"generated from the binding
  table in step 9. Until then this is the package marker."* **Every consumer import today is the
  private `_schemas` path.** Relocation.
- **Branch classes are not exported.** `core/requirements/asset_requirements.py` has
  `__all__ = ["AssetRequirements"]` and twelve branch classes. A caller who receives an
  `AssetRequirements` cannot name the branch it got. Relocation.
- **Nineteen classes over six documents are named `…Branch<N>`** — and the target's class name is
  already in their own base list: `class AssetRequirementsBranch7(AssetRequirements,
  JavaScriptAssetRequirements)`. Decided 2026-10-29; needs a rename census.
- **One import path per class** (§1). `.111`: `core/vendor_pricing_option.py` binds five names to
  two classes each in one namespace. The §4 collision rule compares only positions within one
  module, so an import colliding with a local declaration is a gap in the rule. **Decision.**
- **Aliases for migration.** Not stated in either document. A downstream application must keep its
  import spellings while the classes underneath become ours, and §1's one-path rule has to be
  reconciled with that rather than bolted beside it. **Decision, design first.**

## E. §10's report

§14 step 8 lists *"the report's three figures"* and §10 retires the `emitted/refused (deferred,
verdict)` pair. `./check` and `__main__` still print the pair; the four defect counts are not
printed by the run and live in the verifier and tests. `__main__.py:135-148` argues for keeping
the pair — **code and document disagree, and neither was changed.** A decision for the owner.

## F. The instruments

None of these is a document the compiler cannot express. They are our ability to *prove* it.

- The full suite does not complete (`10l.96`): `_an_instance` calls `hypothesis_jsonschema.from_schema`
  directly, bypassing the canonicalisation memo, and `harness.shared` keys on a `json.dumps` with a
  `copy.deepcopy` hit path — a cache whose lookup costs as much as the miss.
- `tests/test_type_checker.py` is **red**, 6 mypy errors in `compiler.py`/`emit.py` — so §2's "the
  type checker proves the match total" is currently unproven.
- 19 standing failures at both base and tip, the same nineteen by name.
- `.108`: `_intersection` composes a restatement as `{**child, "allOf": [base]}`, so pointers below
  carry an `allOf` index the document does not have; 2 classes cannot be graded at all and 144 of
  the old 235 approximation pointers did not resolve.
- 292 red comparison pairs on a fresh tree, 196 on the committed one, against a `COMPARISON_FACTS`
  pinned empty.

## G. Upstream

Zero issues filed, so all 120 facts read as `ours`. §14: *"an unfiled gap IS ours"* — correct, and
it means the ours backlog overstates our own work by however many are genuinely upstream. Filing
reclassifies; it changes no type and no emission.

## What is NOT on this list, deliberately

`compiler.py` is 6,271 lines and was never dissolved; 12 of 13 `lower/` modules import it; the walk
recurses through the run via `compiler.lower_node`; the `Lowering` algebra was never built and the
walk accumulates into a mutable `Module`. **No consumer can observe any of it.** These are
maintainability work, to be done when they pay for themselves, and they must not be gated by tests
that assert code shape: that freezes the shape, blocks refactoring, and proves nothing, because
there are infinite ways to write the internals wrongly.

Two of them are load-bearing for group A, and that is the only reason to do them: dissolving
`compiler.py` removes the walk→run cycle, after which the seam collapse is mechanical.

## Why the architecture half stalled, in one sentence

§14 says each step *"is checked by a test that exists **or is named**"*, and steps marked *bytes*
are checked by regenerating the tree and comparing it byte for byte. **A bytes gate passes when
nothing happens.** The two structural steps that never landed are the *bytes* steps; every
report-changing step landed, because `./check` printed its number in a second and a wave that
failed to move it was visibly stalled. A gate must fail before the work and pass after.
