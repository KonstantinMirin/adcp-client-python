# The final state, as nine readings

**A READING IS A FACT ABOUT THE ARTIFACT.** A consumer who has only the installed wheel and the
bundle can check it. That is the whole of the test for belonging here: a property of `codegen/`
that no consumer can observe is not a reading and must not be gated, because there are unboundedly
many wrong internal structures and enumerating a few proves nothing.

**EVERY READING HOLDS OR IT DOES NOT.** Never M of N. "1,952 of 1,952 exports resolve" is a
reading; "2,714 of 2,793 pairs answered" is not one — it is a cost figure about the instrument,
and the reading behind it is still unknown.

**EVERY READING CARRIES A GATE THAT IS RED TODAY**, or it carries none and says so. A gate that
passes when nothing happens is not a gate: the two structural steps of `architecture.md` §14 that
never landed are exactly the two whose only check was "the emitted tree does not change", which is
true of a no-op.

**A ROW THAT MOVES NO READING IS NOT BRIEFED.** `bd` holds the rows; this holds what they are for.

Measured on `emit/from-scratch` at `cd160fe5`, 2026-11-02.

---

## Two preconditions, which are not readings

**EMISSION IS NOT A READING, AND MISTAKING IT FOR ONE COST WEEKS.** `./check` prints
`emitted 1054 / refused 0 (deferred 0, verdict 0); accounted 1054` in 1.19 s warm. A document
emits when the walk produces a class for it. **That says nothing about whether the class states
what the document states.** It belongs here, beside "the tree compiles", and the correctness
statement is reading 1. Held by `./check` and by
`tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits`.

**THE COMMITTED TREE IS THE FRESH EMISSION.** Every reading below except 8 is measured against
`src/`, and a reading over `src/` is not a reading over a wheel: packaging decides which files
ship. Reading 8 is where that gap is closed.

## The nine readings

| # | reading | today |
|---|---|---|
| 1 | **Every class accepts every value its document admits, refuses every value it refuses, and what it dumps validates against the document again.** | **does not hold** |
| 2 | Every exception to reading 1 is a declared widening with a value proving it. | **does not hold** |
| 3 | Every union root dispatches. | **does not hold** |
| 4 | Each distinct vocabulary is one type, referenced wherever it is stated. | **does not hold** |
| 5 | The record states each distinct subtree once. | **does not hold** |
| 6 | Every class is importable at exactly one `adcp.types.<domain>.<Name>`. | **HOLDS over `src/`** |
| 7 | The package declares its types to a consumer's type checker. | **does not hold** |
| 8 | The wheel builds, installs into a clean environment, and every exported name imports. | **does not hold** |
| 9 | Every approximated fact is attributed: ours with a decision, upstream with a live issue. | **does not hold** |

---

### 1. Every class accepts what its document admits, refuses what it refuses, and its dump validates again

**This is the deliverable's correctness, it is the definition of "1,054 schemas produced classes",
and nothing has ever established it over the whole set.** 2,793 pairs, each a class or alias
against the document and pointer it names.

Three failures proved by payload:

| site | direction | row |
|---|---|---|
| `media-buy/refine-proposals-response.json#/anyOf/1` | admits `{"task_id": "0"}`; the document requires `status` | `82m.23` |
| `media-buy/buy-products-request.json#/anyOf/1/properties/account` | admits `{"account_id": "a1"}`; the document requires `brand` and `operator` | `82m.24` |
| `media-buy/request-proposals-request.json#/anyOf/1/properties/account` | the same | `82m.24` |

Six more on the promoted corpus entries (`12d`): four dropped facts, one value the document refuses
after a round trip, one unproved widening.

**WHY IT WAS NEVER GREEN, AND IT IS NOT THAT IT WAS GREEN FALSELY.** The run does not finish. The
committed floor answers 2,714 of the 2,793; **79 still draw**, at 240 s to over 2 h 57 m each.
Nobody has seen the gate's verdict over the whole set, so "every class passes" was never a reading
anything produced — it was a test id whose result was unknown. That cost is reading 5, not a
property of the work, which is why reading 5 is the critical path.

**AND THE GATE HAS THREE EXITS, which must each be read before any green is believed:**

- `tests/test_emit.py:1340` reads `if rep.accepts.outcome != "strategy_error":` — **so a
  `strategy_error` leaves the accepts assertion unexecuted.** It is then caught downstream: a
  `strategy_error` with no `no_instrument` cause becomes `accepts:strategy_error` and the final
  assertion fails. The hole is the conjunction — `strategy_error` **with** a cause — which passes
  with no accepts verdict. `harness.py:554` records the author's own worry about exactly this:
  "a cause naming every co-occurrence would admit a `strategy_error` from ANY" schema.
- `no_instrument` passes the pair when the draw was structurally impossible, asserted against a
  named cause rather than taken on trust.
- `liveness` accepts `no_payload` beside `pass`.

**A BUDGET CUT IS SPELLED LIKE A VERDICT, and measured it reddens rather than greens.**
`OverBudget` is a plain `Exception`, so `accepts`'s final `except Exception` clause catches it as
`model_error` — the category meaning "the model raised something other than a `ValidationError`".
The test fails on `model_error`, so a cut is a **false red**, indistinguishable from a real defect
by anything but the clock. 43 of the fill lane's 100 outcomes were cuts spelled this way.

**Gate:** `tests/test_emit.py::test_every_class_passes_all_three_checks`, parametrised over the
2,793 pairs. Red, and it does not complete. Each payload above fails now and must pass. Two gates
are owed beside it: no pair may pass through `strategy_error`, and a budget cut must be reported as
a cut and never as a verdict.

### 2. Every exception to reading 1 is a declared widening with a value proving it

`approximated 120 facts in 53 documents`, declared in the emitted modules as
`__adcp_approximations__` and equal in both directions to what a fresh run mints. What does not
hold is the proof: the widening store serves a timeout as if it were evidence —
`[null, "OverBudget: the grade did not finish inside 30 s"]` — and **46 such entries remain**
(`pjc`). Removing the one covering `trusted-match/offer.json#` turned a pair that "graded" in 8.8 s
into one that does not finish in 600 s.

A declaration with no value behind it is an allowlist wearing a measurement.

**Gate:** `tests/test_the_declared_backlog.py` holds the set equality, green. The missing gate is
named and does not exist: **no entry of the widening store may record a budget cut rather than a
value.** Red on 46 the moment it is written.

### 3. Every union root dispatches

Built every union base's branch adapter over the committed tree: **718 build, 3 raise**, and the 3
are one root with its two branch classes inheriting the method.
`RefineProposalsResponse.model_validate(anything)` raises `PydanticUserError` before validating —
so a consumer receiving a refine-proposals response cannot use the normal entry point, while the
emission precondition calls the document emitted and unrefused.

One cause, and it is a predicate: §4's first dispatch source tests whether every branch **pins** a
shared property where it must test whether the key **determines** the branch. Pinning is not
determining — a pin on a key a branch lets an instance omit determines nothing when the key is
absent. The two predicates agree wherever the pinned key is required, which is 83 of the bundle's
84 discriminated unions, so the weaker one passes almost everywhere and this is its one
counterexample.

**Gate:** build every union base's branch adapter over the whole committed tree, 0 raises. 1.6 GB
peak, under a minute. Red on 3. A second: no union carries `Field(discriminator=)` over a key any
branch does not require.

### 4. Each distinct vocabulary is one type, referenced wherever it is stated

**128 distinct value sets are emitted more than once, across 305 classes, restating 632 member
strings.** The same enumeration written out independently at each position that states it is the
redeclaration this rewrite exists to remove, and `architecture.md` §3a's catalogue is the answer:
the value list is written once per distinct member set and the named type is constructed from it.

Of the 128: **35 collapse 79 classes** into one named type each, judged and named; **65** already
derived one name independently, so the name is settled; **13** are judged distinct and keep
separate types over one value list; **4** are refused a name because the only candidate came from
description prose, and a description states what a thing IS, not what it is CALLED.

**Gate:** `tests/test_catalogue.py`'s `xfail(strict=True)`, red by construction. It flips when the
catalogue feeds the walk, and a strict xfail that passes is an error — deliberately.

### 5. The record states each distinct subtree once

**THIS IS THE CRITICAL PATH, and it is not a performance row.** Every other reading is verified
through the record, so its cost is what has kept readings 1 and 2 unknown.

| | |
|---|---|
| bundle source, 1,054 portable documents | 5,363,667 bytes |
| records committed to `src/adcp/types/_schemas` | **797.1 MB** |
| largest single record | **112.9 MB** — `core/mcp-webhook-payload.json` |
| worst ratio | **7,912×** — `compliance/task-completion-data.json`, 998 bytes to 7,896,628 |

And it is duplication, not content: that record holds **957,187 nodes of which 6,442 dict subtrees
are distinct**, one appearing **1,957 times**. `codegen/bundle.py`'s `inline` recurses with no memo
and deep-copies every leaf, so each reference re-copies its whole target and nested references
multiply. `harness.py:306` states where it lands: *"the record is what `from_schema` is handed"* —
a strategy over 957,187 nodes instead of 6,442.

**THE SHARING LAYER IS MERGED** at `d52c3f26`, and it is output-neutral by construction: all 2,163
emitted files byte-identical by sha256 before and after, *and* byte-identical to the committed
artifact on both sides. `core/mcp-webhook-payload.json`'s 217,363 dict occurrences become **9,000
distinct objects, 24.2×**, against a 33.7× ceiling; net of a 36–39 MB process floor its inlining is
**519 ms → 46 ms** and its record memory **53 MB → 10 MB**. Whole-set cold emit 148.52 → 119.47 s
CPU.

**That is 1.24× over the set and not 11×, because removing one pole exposed the next.**
`bundle.portable()` is called **1,749 times in one emit and costs 123.0 s of it — 80 percent** —
since `record` re-runs it before inlining anything. `architecture.md` decides it: a derived reading
of the bundle is an **argument**, threaded once per run, not a cache — a cache keyed on the path is
wrong when a test builds a bundle in `tmp_path`, and one keyed on the contents must read the
contents. Row `82m.26`.

**The reading itself is the DAG layer**, and `architecture.md`'s *"the record's text is a DAG; its
pointers are not"* decides its form: each distinct subtree once under `definitions`, and **every
pointer a reader spells keeps its spelling**, because `corpus_key` hashes the pointer and a
respelling misses every committed corpus entry. Per-document hoisting is
**835,864,437 → 66,773,403 bytes, 13×, 0 collisions**, breaking **3 new declared pointers** of
2,793. Cross-document sharing is measured at **6,034,010 bytes, 95.3×** — within 12 percent of the
bundle's own source size — and deferred, because it needs a store shared across documents.

The record's own walk is a separate decision: `bundle.nodes` yields 1,374,947 pointers of which
**1,281,844 stop resolving** in the DAG form, and `applied_schema` is why — one shared definition
reached through two enclosing contexts has two applied answers.

**Gate:** byte identity across the sharing layer is **green and does not prove the reading** — it
passes on a no-op, which is why the per-document wall clock and peak RSS above are the gate that
moved. For the DAG layer: no record exceeds its source document by more than the references it
resolves. Row `82m.25`, still open on the hoisting.

### 6. Every class is importable at exactly one `adcp.types.<domain>.<Name>` — HOLDS over `src/`

**24 domain modules, 1,952 exports, 0 collisions.** `rebuild-plan.md` §1's one-path rule, over
roots, branch classes and aliases alike. The 611-of-613 unimportable branch classes that were the
whole reason for the rewrite are reachable and named.

It holds over the source tree and **not yet over a wheel**, which is reading 8.

**Gate:** `tests/test_the_domain_surface.py`, 3 tests, 17.6 s — every export resolves at exactly
one path, and importing it gives the same object as the private path. Green.

### 7. The package declares its types to a consumer's type checker

`src/adcp/py.typed` **does not exist**, and neither does `src/adcp/types/py.typed`. Without PEP 561
a consumer's checker treats the whole package as untyped, so **0 of 20,036 fields over 2,562
classes** reach it. Every annotation the compiler derives — every constraint, every branch type,
every enum member — is invisible at the boundary it was built for.

**Gate:** none exists. The named one: install the wheel into a clean environment, run a type
checker over a consumer module importing from `adcp.types.<domain>`, and require that a wrong
assignment is an error. Red today because the file is absent, and `architecture.md` records that
`py.typed` ships with its errors declared rather than waiting for zero.

### 8. The wheel builds, installs into a clean environment, and every exported name imports

**The wheel has never been built** (`82m.21`), and cannot be in this environment. So no claim about
what ships is verified — including reading 6, which is measured against `src/` and not against an
installed package. And 797 MB of records (reading 5) is what would ship today.

**Gate:** none exists. The named one: build the wheel, install it into an environment that has
never seen this repository, and import all 1,952 exported names from `adcp.types.<domain>`. Red
today because it has never run.

### 9. Every approximated fact is attributed: ours with a decision, upstream with a live issue

All **120 facts in 53 documents** read as `ours`, because `architecture.md` §14 is right that an
unfiled gap IS ours. One upstream issue is filed —
[adcontextprotocol/adcp#8698](https://github.com/adcontextprotocol/adcp/issues/8698), a question
about a pinned discriminant one branch does not require — and it attributes nothing yet, because it
is a question and not a verdict.

Separately, one narrowing is live and **unregistered**: `constraints.url_type` gives a pydantic URL
type that rewrites the value, lowercasing the host and giving an empty path a `/`, so the class's
value is not the document's. The registry that once admitted the two bounds it adds,
`harness.URL_IMPLIED`, has **0 references repo-wide**. `rebuild-plan.md` §2 withdrew the type on
that ground; `82m.19` measures both directions by payload.

**Gate:** `tests/test_the_declared_backlog.py` for the set equality, green. The named one: every
`upstream` attribution names an issue that exists, and the registry of deliberate narrowings is
compared by equality against the set of narrowings the run takes — red while `url_type` narrows and
nothing admits it.

---

## What this document replaces

`what-remains.md` is a snapshot of trunk at `b9be6d46`, three weeks and one deleted instrument ago.
Its groups E and F quote a schema-text comparison that no longer exists, and its group A measures
an exit condition against code that has since moved. **It is retired by this file**, with a banner
saying so; it is kept because it records what was true when each decision was taken.

## How to add a reading

State the fact about the artifact. Name the gate and run it, so the entry records a red. If the
gate does not exist, say "none exists" and name the one that would — a reading with an imagined
gate is a goal, and this file holds facts.
