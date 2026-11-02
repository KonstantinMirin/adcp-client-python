# The compiler's structure: layers, the one dispatch, and what crosses each seam

`docs/plan/rebuild-plan.md` decides the semantics: what each keyword compiles to at each
position, which keywords are admitted, which refuse, and how the output is graded. This
document decides the structure that carries those semantics: the layers, the seam between
each pair of them, the one place a node's kind is decided, the data that crosses every
boundary, the paradigm, and what is derived from what. Where the two overlap, the semantics
document governs the meaning of a keyword and this one governs where that meaning is written
down and who reads it; §13 names the places where its wording forces a structure this
document decides differently, and the owner of the semantics decides those.

No site counts appear here. Evidence for the state of the code is in
`docs/reviews/architecture-2026-10-25.html` and `docs/reviews/codegen-vs-design-2026-10-25.html`;
§12 says which of their findings this structure answers and which of the present structure
it keeps.

---

## 1. The case

A bundle document is read once into a typed node tree. One function decides what every node
becomes. The decisions compose into a module of declarations, which one renderer writes as
Python. A verifier grades each emitted class against the document it names, without reading
the walk. Five layers, one data type crossing each seam:

```
bundle.py          reads a document and builds the document of record
    │  raw mapping
schema/parse.py    ONE parser: keys and type select the node kind; position is assigned here
    │  Node (typed, positioned, immutable)
lower/decide.py    ONE dispatch: an exhaustive match over the node kinds
lower/<kind>.py    one handler per kind, reading keywords.py for every keyword it meets
    │  Lowering  =  a TypeRef plus the declarations, imports, approximations and
    │               reports it needed — and ONLY a Lowering: this seam is total
lower/names.py     symbols assigned over the whole module, content dedup included
    │  Module (the intermediate representation, no text in it)
render.py          the one module that knows pydantic and the model layer it renders through
    │  text
emit.py            the run: dependency order, files, the report
```

Beside the pipeline, three modules every layer reads and none of them writes:

- `codegen/keywords.py` — the declaration §8 of the semantics document calls for: every
  keyword, at every position, with what it compiles to, whether the model renders it as a
  fact, which structural keywords descend into which position, and **which rung of §2's ladder
  the keyword widens to where the handler cannot render it**.
- `codegen/attribution.py` — **new (2026-10-26)**: the one registry of site-level upstream
  issues, keyed by document, pointer and keyword. A second declaration module beside
  `keywords.py` and a leaf like it, read by `lower/` to attribute an approximation and by
  `verify/` to grade one. It is a declaration and not a verifier artifact, which is why it is
  here and not under `verify/`: a keyword-level decision lives in a cell, a site-level one lives
  here, and nothing else holds either.
- `codegen/refusal.py` — the one refusal type, a value and not an exception, **now minted only
  by `bundle.record`**.

And one package that reads the output and the record but never the walk:
`codegen/verify/`, which is today's `harness.py` and `dump_exemptions.py`.

---

## 2. Paradigm: functional, and where the effects are

The compiler is written as total functions over immutable values. Each layer's entry point is a
function from one data type to the next; nothing between the file read and the file write
mutates shared state.

*Why this and not objects.* The question a paradigm answers is what varies and what stays
closed. Here the node kinds are closed: draft-07 fixes them and the semantics document's §4
table lists every one. The operations over a node are closed too: a node is lowered, and that
is all a node is ever asked. The axis that does vary is the content of the keyword × position
cells — which of them have a compilation written, and what a cell says — and that is data,
not behaviour. Polymorphism earns its cost when kinds are open and operations are fixed; a
visitor earns its cost when operations are open and kinds are fixed. With both closed and one
operation, a class hierarchy with a `lower` method on each node spreads one function over one
file per kind and drags the intermediate representation and the keyword table into the layer
that reads JSON, while buying no extension point anything will use. A sum type and one
exhaustive function state the same thing in one place, and the type checker proves the
function covers every kind.

Four rules follow, and each is held strictly:

- **Immutable node representations.** `codegen/schema/nodes.py` declares the node kinds as
  frozen dataclasses. A handler reads fields; it never reads a dict and never rewrites a node.
  The three places the walk rewrites a node today — the key schema given a `type` word, the
  extras store rebuilt as a mapping, a multi-type node cut into one member per type — are
  readings the parser makes once, at the position that implies them (§4).
- **Total functions from node to decision.** `decide(node, ctx)` returns `Lowering`, and
  nothing else. *This was `Lowering | Refusal` and the semantics document's §2 collapsed it on
  2026-10-26:* a keyword a handler cannot render widens the annotation and declares an
  approximation, so no node is ever without a lowering and the union has one inhabitant left.
  **What that costs is a type-system guarantee, and it has to be replaced rather than mourned.**
  The sum type used to make a caller that read a `Lowering` field without handling the other
  branch a type error, which was the mechanical form of §9's "a crash is not an outcome". With
  one inhabitant there is no branch to force, so the obligation moves into each handler: a
  handler's match over the cases of its own node is total, its final arm calls
  `approximate(node, keyword)`, and **no handler raises**. The import-rule tests gain the third
  boundary that holds it (§11), and §8 of the semantics document gains the two equalities that
  catch a widening nobody declared. A guarantee the type checker held is now held by a test, and
  saying so is better than pretending the trade did not happen.
- **Composition by explicit combinators.** `Lowering` composes with `+`: a parent's declarations
  are its own followed by its children's, its imports the union, its approximations and its
  reports the concatenation. **The algebra changed with the seam.** A refusal was an ABSORBING
  element — anything composed with one was that one, which is how a child's refusal killed a
  document — and an approximation is an ADDITIVE one: composition is total, the parent always
  gets a `Lowering`, and what travels upward is accumulated rather than propagated. So
  `first_refusal(results)` loses every caller in `lower/` and keeps exactly one, in
  `bundle.record`, where it still returns the earliest refusal in document order over the
  references the inliner could not resolve. Its contract is unchanged; its subject is now the
  record and not the walk.
- **Effects at the two ends.** `bundle.py` reads files. `emit.py` writes files and prints the
  report. Nothing between them touches a file, an environment variable, a clock or a global.
  The run's own state — which documents are lowered, which refused — is a fold in `emit.py`
  over a dependency order computed before any document is lowered (§10), so no handler ever
  calls back into the run.

**What becomes of the exception-based refusal.** `Refusal` stays in `codegen/refusal.py` and
stops subclassing `Exception`. The one `try` left in the compiler is around nothing: a defect in
the compiler itself — two selectors claiming one node, two constraints deriving one alias name —
stays an exception (`BuildFailure`) that no layer catches, because it is not an outcome of any
document and the run must stop on it.

**What becomes of the refusal itself, 2026-10-26.** The directive narrows `Refusal` to one
producer and one meaning: `bundle.record` could not build a document of record, because a
`$ref`'s target is not a bundle document or because two documents reference each other in a
cycle. `emit` is its only reader. Three consequences, each mechanical:

- **`Kind.DEFERRED` retires.** It meant "the lowering for this position has not been written",
  and under the directive unwritten code produces an approximation and not a refusal, so the
  kind has no instance left to name. The semantics document's §9 rule that minted it is replaced
  there, and `is_a_verdict` becomes a question with one answer.
- **`Kind.CHAINED` survives, and moves.** A document whose reference target has no record has no
  record either, so the inliner refuses CHAINED `through=` the target's refusal and
  `Refusal.resolved` keeps its meaning. What changes is where it is minted: inside
  `bundle.record`, not at the reference's lowering, because a reference the walk can see is one
  the record already inlined.
- **`Kind.VERDICT` is the only resolved kind.** With DEFERRED gone and CHAINED delegating,
  `RESOLVED_KINDS` has one member, and the figure the exit condition reads is just the count of
  refused documents. The enum stays an enum rather than collapsing into a boolean: a bundle that
  grows a case neither kind covers needs somewhere to put it, and the cost of keeping the type
  is nothing.

**The handler's own obligation.** `approximate(node, keyword)` is to an approximation what
`Refusal`'s constructors were to a kind: the ONE place a widening is minted, reading the rung off
the cell (§3). A handler never chooses a rung and never writes an attribution, for the reason the
reviews recorded for refusal kinds — a decision made at the site that needs it is a decision
nobody can audit against the table that was supposed to hold it.

---

### The seam collapse goes AFTER the declared-backlog equality, and the walk's per-node entry goes with the carriers (decided 2026-10-30)

**Order.** §2 collapsed this seam in writing and stated the trade: *"A guarantee the type checker
held is now held by a test, and saying so is better than pretending the trade did not happen."* It
named three replacements, and one of them is §8's *"two equalities that catch a widening nobody
declared"*. **That equality is red today**, off by three `anyOf` sites in `media-buy/`.

So the collapse waits on it, and the reason is not tidiness. Every one of the 93 sites sits at a
position no portable document reaches — that is what `refused == 0` means — so each conversion is
invisible to `./check`, invisible to the byte compare, **and invisible to the equality that would
catch the first document to reach one.** Run first, the collapse moves 93 answers from an instrument
that works to one that does not yet; run after, each lands against a green equality. A red test
cannot fail more.

**And the collapse cannot be sized up front.** Collapsing the dispatch alone yields 12 type errors,
not 93: the handlers still answer the sum type, so the checker sees one ring at a time. The work is
ring by ring and the figure after each ring is the only honest estimate of the next.

**Where the walk's per-node entry lives.** §11's table does not say, and it is the question that
kept `lower_node` in `compiler.py`. It cannot go in `lower/names.py`: that module is a leaf of the
decision layer, and hosting the entry would make it the hub every handler recurses through and need
a second deferred import to break a second cycle. It cannot go in `lower/decide.py` either —
`decide.py` imports the handlers, so a handler recursing through it is a module cycle rather than a
deferred edge.

**It goes where the CARRIERS go.** Both the dispatch and the handlers need the entry and neither
owns it, which is what `compiler.py` accidentally is today; what makes that accidental rather than
designed is that `compiler.py` also holds `Module`, `Case`, `Target` and `Decided`. `Decided` is
now `ir.py`'s. As the rest follow, the entry is a thin module importing `ir` and `decide`, with the
handlers importing `ir` alone — and §11's table gains the row it is missing, naming that module and
the one direction its arrow runs.

### The drawn corpus is COMMITTED (decided 2026-10-30)

**The payloads for all 1,054 documents are 3,317 entries and 0.4 MB of content, mean 131 bytes.**
Drawing them costs 151 to 2,356 seconds per pair. They live in a gitignored directory, so a fresh
checkout, a new worktree, a CI job and every key-space change redraw all of them — and at the last
reading **1,740 of 2,793 pairs held no entry at all.**

`tests/corpus.py` recorded the reason not to commit them, and the reason was sound when it was
written:

> *"a committed corpus is a second derived artifact whose currency has no instrument … the gate for
> it would have to redden on any in-flight record change, which is correct work."*

**That clause is the load-bearing one and it is now false.** The key was `bundle.record` — our own
inlining — so any compiler edit invalidated every entry and a committed corpus would have been
permanently stale with a permanently red gate. The key is now `bundle.source_identities`: the
document's own raw bytes, the raw bytes of its reference closure, the example count, the format
strategies and the generator version. **A compiler edit moves nothing. Only a bundle bump does.**

So the obligation the old argument said nothing could grade is now gradeable, and it is the gate
that comes with the decision: **every graded pair has a committed entry under the current key.** It
reddens exactly when a bundle bump or a generator bump lands without a redraw — which is a
deliberate, reviewable event and not an in-flight change — and `harness.corpus_defect` still
re-offers every held instance to the document on read, so a wrong entry cannot pass quietly.

What this buys: a payload is drawn **once per (document, draw version) in the project's history**,
not once per checkout per lane per key-space change. What it costs is 0.4 MB in the tree and a
redraw step on a bundle bump, which is the same discipline the packaged records already carry.

### The widening store's currency is the OBLIGATION, not a second gate (decided 2026-10-30)

§8's widening obligation draws too, at three sites, and those draws now have a store of their own
in a separate key space and a separate directory. The accepts gate's case **does not transfer to
it**, and the reason is worth stating because it looks like an omission: `live_keys()` reads every
graded pair's accepts key with no draw at all, where the widening space's live set depends on
which borrowed base hosted each declaration's location — decided by placement attempts against the
pair's own accepts instance. So the exact set is knowable only by RUNNING the obligation, and on a
cold floor that costs the very draws the gate would be reporting are owed. A gate over the cheap
superset would demand entries for draws that never happen.

**The accepts gate exists to close a hole that does not exist here.** A stale accepts entry is
*silently* correct: its key stops matching, the pair redraws, and nothing reddens. A stale widening
entry cannot be silent, because every held base is placed and offered to the DOCUMENT before the
entry point sees it — so it either still hosts the location, in which case the check is real, or it
fails placement and the declaration is reported `unproved`, which §8 treats as **as much a failure
as a narrowing.** Staleness here is self-reporting. The obligation is the currency gate.

So the floor is committed as it fills, graded on its STRUCTURE, and **no second derived artifact is
minted to record which keys the population asks for.** That artifact would need its own equality,
and that equality would need the same thing one level further out — the regress `tests/corpus.py`'s
original argument was right to fear. Leaving the space cache-only is also refused: the saving is
real and crosses checkouts, measured at 233.75 s against 0.47 s over 17 pairs with 0 verdicts
changed.

A position whose draw never returns is held by nothing under any of these choices — two of them
exceed 900 s on an 8,145,255-byte conjunction and one exceeds 600 s on a 6,832,209-byte node. That
residue is not a currency question. It is the document-derived construction decision, and it is
open.

### The wheel SHIPS `py.typed`, and 350 internal errors are its precondition (decided 2026-11-02)

**Nothing this project built reaches a consumer's type checker today.** Measured against the
INSTALLED package rather than the source tree: `Skipping analyzing "adcp.types.core": module is
installed, but missing library stubs or py.typed marker`, then `Revealed type is "Any"` — and
**two deliberate bugs in the consumer file pass silently.** So **0 of 14,570 fields, 0 of 991
`Literal`s, 0 of 244 `StrEnum`s and 0 of 582 union arms** are visible to the tool a consumer
actually runs. Every ergonomic property the surface work established is invisible at the wheel
boundary.

`pyproject.toml` names the absence and defers it: *"Adding one is a change to the WHEEL's public
surface — it promises every annotation in `src/adcp` to every consumer's checker — so it is a
decision for the row that owns the shipped package."* **No row owned it.** The goal is an
ergonomic, schema-faithful, DX-friendly SDK, and a typed SDK whose types are `Any` to its
consumer is none of the three. So the marker ships.

**And pyproject is right about what it promises, which makes the precondition non-negotiable.**
A `py.typed` marker asserts that every annotation in `src/adcp` is sound, and the same mypy run
reports **350 errors in 80 files inside the SDK — 260 `[assignment]`, 74 `[list-item]`**.
Shipping the marker over those promises something false, so they are resolved first and the
ordering is part of this decision rather than a follow-up.

**The gate is the consumer's checker, not ours.** A file outside the package that misuses a field
and an enum member must FAIL a check against the installed wheel. The audit measured both of those
passing silently, which is the red state; green is both reported, by error code. Checking our own
tree proves nothing about this — the source tree is readable with or without a marker, which is
exactly why the gap survived.

### The suite's scratch goes on DISK, not in RAM (decided 2026-10-30)

`/tmp` on this machine is a **63 GB tmpfs — it is RAM.** The suite materialises a fresh package per
`tmp_path`, the tree is 841 MB of which 836 MB is the resolved JSON read through
`importlib.resources`, and at ten workers that lands in memory. Measured during a full run:
available RAM reached **3.1 GB of 125**, and the two earlier attempts at the same measurement died
of worker OOM rather than of anything in the code.

**So `TMPDIR` and pytest's `--basetemp` point at disk.** The scratch is large, write-once and read
back by a child process; none of that wants a memory-backed filesystem, and the one property RAM
buys — speed — is irrelevant beside a run that cannot finish.

Two readings go with it, and both were measured rather than assumed:

* **`pyproject.toml`'s memory paragraph is stale by an order of magnitude.** It records a `-n 24`
  peak of 10.35 GB across 25 processes with a 1,211 MB worst worker. At `-n 10` over the
  2,793-pair tree the same measurement is **73.4 GB summed, worst worker 13.7 GB.**
* **A finished lane's scratch is not free.** Four orphaned directories from merged, torn-down lanes
  held 5 GB of tmpfs with zero open handles. Scratch under a memory-backed path is a resource the
  orchestrator owns, and the discipline that applies to a worktree applies to it: check that
  nothing holds it, then remove it.

### The subject of grading is a FRESH EMIT, never the committed tree (decided 2026-10-29)

The schema is pinned and the drawn instances are content-addressed, so what a class is graded
against is a function of the bundle and the compiler alone. **Grading therefore reads the tree a
fresh run emits. The committed tree is an ARTIFACT, verified by one byte-compare, and is never the
subject.**

`tests/test_emit.py`'s `graded()` does `import adcp.types._schemas` and walks it, which puts a
committed artifact in the grading path and causes three failures this project reported as
unrelated:

* the committed tree was **39 documents stale and 35 more differed byte for byte**, so every
  census over it graded a mixture of two compilers — three import-path collisions and one stale
  decision were invisible in `src/` and visible in a fresh run;
* `test_emit.py` **cannot collect** when one committed module fails to import, because `graded()`
  runs at parametrize time, so a single bad base list errors ~2,400 tests;
* the import obligation is downstream of its own precondition, which is the clause above.

Regenerate, then grade. The order is the whole rule: a change to the compiler is followed by a
regeneration and the grading reads that, so a stale tree cannot be graded and a tree that does not
build fails one named test instead of disabling the file.

The instruments exist. `tests/compiled.py` returns the fresh emit in under a second warm, keyed on
the compiler's own source, and `tests/_imports_a_tree.py` already writes a fresh tree to a
temporary directory and imports it in a child process — the child being forced rather than
convenient, because an emitted module imports `adcp.types.constraints` by ABSOLUTE name and a
fresh tree imported in the suite's own interpreter resolves its aliases through the committed
alias module.

**`tests/fresh.py` is where a reader's BUNDLE-DERIVED constants live (decided 2026-10-30)**, beside
`BUNDLE` and `TREE` which are already there. A reader that needs to ask the emitter where a
document's module sits needs `bundle.package_roots` — a function of the bundle and never of the
run, which is what makes it a constant rather than an argument. The alternative, measured when it
came up, is threading one more parameter through 21 call sites in four files to carry a value none
of them varies. One place holds it and the readers import it.

### A check may not be downstream of its own precondition (decided 2026-10-29)

`tests/test_emit.py`'s `test_every_module_of_the_tree_imports_and_every_class_of_it_is_defined`
is the obligation that an emitted tree builds, and its docstring names the failure mode it
missed. It could not run, for two independent reasons, and both are structural:

* it lives in the file whose COLLECTION the defect disables — `graded()` imports the tree at
  parametrize time, so an unimportable module errors the check that exists to report it;
* its population is `emit.TREE`, the COMMITTED tree, so a document absent from `src/` is
  invisible. That is how the second of the two sites hid entirely.

**A check whose precondition is the thing it checks is not a check.** The import obligation ranges
over the tree a fresh run EMITS, not the one committed, and it lives outside the module whose
collection it would gate. Both halves are required: fixing the population alone leaves it
uncollectable, and moving the file alone leaves it blind to anything not yet committed.

**And a base list naming one class twice RAISES.** §2 decides it — a refusal is the document's and
a broken invariant is ours — so this is the clause applied: nothing a document can state produces
a duplicate base, the reader of such a report would go to `codegen/`, and an exception at the
pointer is louder and honest where a refusal is quiet and wrong. The chokepoint is
`ir.ClassDecl`, because not every base list passes through `compiler.dispatching_bases`; a guard
there would hold two of the call sites and miss the rest.

**ANOTHER INSTANCE (2026-10-30).** The rule above was written about a precondition; this is the
same rule reached a different way — the check dies in its own setup, before the line holding its
claim.

* `test_the_emitted_tree_still_declares_every_module_it_imports` built its export table in a first
  loop that raised at `brand.json`, so the second loop — the one holding the assertion — never
  ran. Repaired, it reddens immediately on a real defect: nine modules understate their `__all__`
  against what other modules import from them, 44 names, every one a union-branch module.

A check that dies before its assertion is indistinguishable from a check that has nothing to
report, and the suite's own failure summary spells them the same way. The two are told apart only
by reading the traceback for which LINE raised, so a red check is not evidence that its subject
is what failed.

### An approximation's pointer is the SchemaRef spelling (decided 2026-10-29)

`render.declared_at` attaches a declaration to a class by a prefix test, and its own docstring
fixes the rule: "the prefix test is on ONE spelling of a pointer — `SchemaRef`'s, which
`compiler.schema_ref` is the sole producer of". **An approximation declared at a different
spelling of the same node therefore attaches to the wrong class, or to none.**

The spellings differ across an `allOf` conjunct. A class's `SchemaRef` keeps the conjunct —
`#/anyOf/0/allOf/0/anyOf` — and the walk writes the approximation at the node reached through
it, `#/anyOf/0/anyOf`. Measured: **144 of 235 declared pointers do not resolve in their own
document**, even following `$ref` and merging `allOf`, and in `adagents.json` four `minItems`
declarations land on the root and on an intermediate branch rather than on the class whose field
actually drops the fact.

**The approximation takes the `SchemaRef` spelling, because that is the one the reader of a
declaration uses.** §2 asks a declaration to be a fact §8 can look for in the document and
find; a pointer that resolves to nothing is not that. This is one producer and one spelling, as
`attribution.py` already says of the attribution it writes beside it, and it is also both
directions of the declared backlog's reading: of 118 declared-but-separable sites, 116 pair with
a silent entry once the conjunct is elided — the same union counted twice under two spellings.

## 3. The declarations: `codegen/keywords.py`, and `codegen/attribution.py` beside it

The semantics document's §5, §6 and §7 are a table of keyword × position. The code carries that
table once, as data, and four readers derive from it. Nothing else in `codegen/` names a
keyword in a set literal. **A keyword-level decision lives in a cell of that table; a
site-level one — the upstream issue a widening at one document, pointer and keyword is
attributed to — lives in `attribution.py`, and nothing holds either twice.**

```python
class Position(StrEnum):
    ROOT, PROP, ELEM, MAPV, KEY, BRANCH, CONJ, RULE, DEF   # the positions §3 names

class Cell(NamedTuple):
    effect: Effect          # TYPE | FIELD | RULE | NAME | ANNOTATION | NOTHING
    rendered: bool          # does a faithful model state this keyword in model_json_schema()
    descends: Position | None   # the position of the subschema(s) this keyword holds, if any
    widens_to: Rung | None  # the rung §2 of the semantics document drops to, where the
                            # handler cannot render this keyword here; None where the
                            # keyword states no fact and there is nothing to drop
    compiles: str           # the sentence the grid states for this keyword here

class Rung(StrEnum):        # §2's ladder, lowest first; TOP always terminates
    KEYWORD, TYPE, JOIN, CONTAINER, TOP

class Row(NamedTuple):
    default: Cell
    at: Mapping[Position, Cell]   # the positions where the answer differs from the default

TABLE: Mapping[str, Row]
def cell(keyword: str, position: Position) -> Cell | None   # None: no row, which refuses by name
```

A row is written per keyword with a default cell and an override per position that differs,
because that is the case of the semantics document's own tables: most rows give one answer
and name the positions that depart from it.

**`Effect.REFUSE` leaves the enum and `widens_to` enters the cell (2026-10-26).** Both follow
from the semantics document's §2: no keyword's presence refuses a document, so there is no
effect for refusing; and a keyword the handler cannot render has to drop to one rung rather than
another, so something must say which.

*Why `widens_to` is a FIELD and not derived.* `effect`, `rendered` and `descends` do not
determine it. `uniqueItems` is RULE, rendered, non-descending and drops its keyword (KEYWORD);
a list-valued `items` is TYPE, rendered, descends to ELEM and drops to the union of its members
(JOIN); an unrowed key has no row at all and drops the node's whole type (TOP). Cells whose
other three fields agree take different rungs, which is the test of whether a field is needed.
It is `None` for a keyword that states no fact about an instance — `$comment`, `title`,
`errorMessage`, the registry data keys — because there is nothing to drop and a rung would be a
decision about a non-decision.

*Why the ATTRIBUTION of an `Ours` widening is derived and not a field.* The attribution of a
widening the design decided is "the row that decided it", and the cell IS that row: the
generator already knows a cell's section and keyword, because it writes the grid from them. A
field holding it would be a second copy of the cell's own address. The attribution that cannot
be derived is the upstream one, and it is not a keyword fact at all — the same keyword widens by
our decision at one pointer and by an upstream defect at another — so it lives in
`codegen/attribution.py`, keyed by document, pointer and keyword. **A cell holds what is true of
a keyword; the registry holds what is true of a site.** An entry in the registry with no issue
reference is a `BuildFailure` and not a missing field, which is the semantics document's §9 rule
("an exemption names an upstream issue, or it is this SDK's own decision") made mechanical.

The widening clause also belongs in the cell's `compiles` SENTENCE, for the reason the rest of
the sentence is there: the grid is the sentence's rendering, and a widening stated beside the
grid instead of in it is the second copy of the what that generation exists to remove.

**`compiles` is why generation is possible at all.** The grid's "compiles to" column is
English, and `effect`, `rendered` and `descends` do not determine it: no triple of them writes
"`ge` / `le` on the type: a standard Pydantic type where one says exactly this, a named alias
otherwise." Without the sentence in the cell, generation can only produce a matrix of effects
beside the prose grid, which leaves the second copy of the what standing — the thing §3 says
generation removes. So the sentence IS the cell's, the grid is its rendering, and the prose a
reader keeps honest against the cells is the reasoning around the grid rather than the grid.

**How a row renders to a grid line.** The line is the default cell's `compiles`, followed by
one clause per position override, in `Position` declaration order; overrides whose `compiles`
is identical are one clause and their positions are joined with ` / `. That is already the
case the semantics document's rows are written in — "`min_length` / `max_length` on the type,
as a named alias. KEY → the key type … ELEM / MAPV → the alias inside the container. ROOT → the
root alias. RULE → nothing." — so the rule is read off the existing grids rather than imposed on
them. A co-occurrence that is not a position (`pattern` beside `format: uri`, an `enum` beside
`type`) belongs to the sentence of the cell it qualifies, because the table is keyed by position
and a co-occurrence is not one.

§6's grid is a membership projection and needs no join: a row NOTHING or ANNOTATION at every
position renders its `compiles` as §6's "what it does, or why nothing". **§7's projection is now
the empty one**, because `Effect.REFUSE` is gone and no row can be in it; the generator still
writes the region, and the region being empty is what makes "no keyword refuses" a fact the
document holds rather than a claim its prose makes. `errorMessage` and the registry data keys
move into §6's projection, where they always belonged: each is NOTHING at every position.

The table also carries the `x-` namespace rule
(§6 of the semantics document): a key with the prefix is admitted, and every such key the
bundle carries is also a row, so a prefixed key with no row is admitted and REPORTED.

**The four readers.**

| reader | module | what it derives |
| --- | --- | --- |
| admission | `schema/parse.py` | at every node, every key is looked up at the node's position: NOTHING is admitted and carried nowhere; a key with no row is admitted and marks the node for the TOP rung, naming a keyword the bundle did not use before; any other effect is a fact the node's kind consumes |
| descent | `schema/parse.py`, `bundle.py`, `verify/record.py` | the structural keywords and the position each one's subschema occupies — the one descent table, where today there are three |
| lowering | `lower/*` | a handler asks the table which of the keywords on its node are TYPE facts, which are RULE sources, which are annotations it carries, and — through `approximate` — which rung a keyword it cannot render drops to, so no handler holds a set of keyword names and none chooses a rung |
| grading | `verify/compare.py` | the compared set is `{k for k in TABLE if cell(k, p).rendered}`; a keyword whose effect is RULE is graded against the class's rule tuple, as §8 of the semantics document says; a compared fact the model does not state is *approximated* where the class's declaration carries it and *missing* where it does not |

**The table is the source of §5, §6 and §7's grids.** Those grids are GENERATED from
`keywords.py`; `tests/test_keywords.py` asserts the committed document matches what the table
generates, so a change to a cell that is not written through to the document fails. Generation
rather than a diff, because a diff can only compare what it can parse back out of a table: a
cell deciding one thing where the sentence beside it says another passes a membership diff and
cannot pass generation, which writes the cell. §6 is the table's rows that are NOTHING or
ANNOTATION at every position, and §7 is the rows that refuse — the EMPTY projection since
2026-10-26 — so each section is a projection and not a second list.

The reasoning paragraphs in those sections are written by hand and are what generation cannot
produce. A cell decides WHAT; the sentence beside it says WHY, and a reader still has to keep
those two honest. What is removed is the second copy of the what.

**Where a generated grid begins and ends, and who writes it.** Each grid sits between two
markers, and the generator owns the lines between them and nothing else:

```markdown
<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
...
<!-- end generated -->
```

The markers are necessary rather than decorative. Without them a generator either rewrites a
whole section — and the reasoning paragraphs, which it cannot produce, are what it would
destroy — or it cannot locate its own output at all. With them the region is addressable, the
prose around it is outside the generator's reach, and a reader can see which half of the
section is derived.

**The generator is a reader of the table and lives in `tests/test_keywords.py`.** It is not in
`keywords.py`: §11 gives the declaration layer positions, keywords, cells and descent, and
denies it text, so a module that renders markdown is not that layer. It is not an entry point
either — §10's rule is that no module of the compiler is ever bound as `__main__`, so there is
no `python -m codegen.keywords`, and the compiler does not write its own documentation.
The test holds both directions: it renders each grid from the cells and asserts the committed
document's marked region equals it, and `--write-grids` on the test writes the region when a
cell has deliberately changed. So the generated half of the semantics document is a test
artifact, which is what makes a cell change that was not written through to the document a
failing test rather than a silent divergence.

This is the one place a row may write `docs/plan/rebuild-plan.md`, and it may write only
between the markers. Editing a cell's MEANING — a grid line outside what the table generates,
or a reasoning paragraph — is a change to a decision, which §13's rule covers: the row reports
it and stops.

**Where the RUNG of a widening comes from.** *This subsection said "where the kind of a refusal
comes from" and the directive rewrote its subject on 2026-10-26.* The question the table answers
is no longer which of two kinds a refusal is — §2 leaves one kind, and `bundle.record` is its
only producer — but which rung a keyword the handler cannot render drops to. The mechanism is
unchanged and so is its reason:

- the rung is `cell(keyword, node.position).widens_to`, read by `approximate` and by nothing
  else;
- a cell whose `widens_to` is `None` cannot be approximated, and a handler that asks for one is
  a `BuildFailure` — the keyword states no fact, so a widening against it would be a declaration
  with nothing to declare, and a declaration the draw cannot prove is deleted;
- a key with no row takes TOP, because an unrowed keyword's reach is unknown and TOP is the one
  rung that is safe without knowing it (the semantics document's §7);
- the attribution is `Ours` at the cell's own address unless `attribution.py` holds an entry for
  this document, pointer and keyword, in which case it is that entry's issue. One lookup, no
  precedence to get wrong: a site-level entry is more specific than a keyword-level one.

*Why derived.* The reviews record the two refusal kinds assigned by hand at a raise site and the
assignment coming out inverted in bulk: a cell the semantics document decides, written up as a
verdict against the document. The rung is the same hazard one step further on — a handler that
chose its own rung would choose the one that makes its own output look best, and nothing could
audit it against the table that was supposed to hold the decision. A rung read off the table
cannot say that, because the table is where the decision that the keyword compiles was made.

**What is left of the refusal's kind.** `bundle.record` mints VERDICT where a reference's target
is not a bundle document, and CHAINED `through=` the target's refusal where the target has no
record of its own. `Kind.DEFERRED` retires with the outcome it named (§2). Nothing in `lower/`
imports `codegen.refusal` any more, which is the import-graph half of the seam going total.

---

## 3a. The CATALOGUE: one pass collects every type, and the walk emits against it

**This layer was not omitted. It was PROHIBITED, in writing, with a reason — and that is why a
dozen rows touched the code it would have changed and none of them built it.** The semantics
document's §4 gained a collision rule at `8b38e963` which closed with:

> *"The resolution is also confined to one module, never compared across modules, because a name's
> module is its namespace and §9's rule is that a document's output may not depend on which other
> documents the run includes."*

So the one mechanism that did exist — §4's "two nodes of identical content are one class" — was
fenced to a single module by explicit instruction, and a cross-document type catalogue was
forbidden by the same sentence. Every lane obeyed it, correctly.

**And the reason it said that was a misreading of §9 that stood for weeks.** §9 forbids a census
over the RUN — the argument list, which differs between a one-document command and a
whole-population emission. A catalogue is a reading of the BUNDLE, which is pinned and is an input
to every run alike, so it yields the same answer in both and is exactly what that rule protects.
Those are different things. Nobody separated them until 2026-10-30, when §1's domain-scope
collision rule hit the same wall and the distinction had to be ruled on — and **that ruling
widened the clause by one case instead of recognising the general principle underneath it**, which
is the second miss and the more expensive one.

The cost of the prohibition is that the compiler reproduces the defect it was built to escape.

### THREE CORRECTIONS TO §3a, EACH FROM A LANE THAT REFUSED TO DECIDE IT (2026-11-02)

**A DOCUMENT ROOT BEATS A RESTATING TITLE, so a CONFLICT with a rooted vocabulary is not one.**
§3a said of two titles over one member set that *"in neither case is there a third name to collapse
to, and minting one is what §4 refuses"*. That is right about minting and wrong about the
population it ranges over: where one of the titles belongs to a **document of its own**, §1 has
already given that vocabulary an exported symbol and §3a's own rule says a document root is
already a home. There is nothing to mint, because the bundle named it. The other title is then a
restating position that happens to carry a title of its own — a case §3a did not cover — and a
local title does not create a second type over an identical member set, because no value
distinguishes them. **So the conflict rule applies only where NEITHER title is a document root.**
Where one is, that root is the home and the rest reference it. A restated title that a consumer
needs is an alias at its position, never a second class.

**ONE TYPE IS A CLASS STATEMENT; THE FUNCTIONAL FORM IS FOR TWO TYPES SHARING ONE VALUE LIST.**
§3a's *"the value list is written once per distinct member set and the named type is constructed
from it"* was read as mandating `StrEnum('<Name>', …)` everywhere, which costs two things that were
measured rather than argued: a functionally-built enum has no slot for the class docstring pydantic
renders as `description`, and a name bound by assignment is invisible to a guard that reads class
statements. **Where the vocabulary is one type, its members ARE the value list and a normal class
statement writes it once** — the rule is satisfied with nothing lost. The functional form is needed
only where the bundle states one member set under names judged genuinely distinct, which is the
narrow case, and there the docstring is written as its own statement.

**AND A GUARD THAT READS CLASS STATEMENTS GOES BLIND TO AN ASSIGNMENT, so it reads the NAMESPACE.**
A collision guard exists to answer what a consumer meets when importing the module, and a consumer
meets the module's namespace, not its syntax. Reading the emitted module's own bindings is both
stricter and not a structural assertion — it stops caring how a name came to be bound, which is the
property that let the functional form slip past it.

**THE EXPORT RECORD IS KEYED ON THE MODULE, NOT ON THE DOCUMENT (decided 2026-11-02).** A
vocabulary with no naming position needs a module of its own, and that module has no document
behind it. **A pseudo-document path is refused**: it names a file the bundle does not contain, and
every reader that resolves a record from a key would then be lying about where the schema came
from. The honest relocation is one level up — every document already maps to the module it
produced, so the key becomes that module and a catalogue module is simply one with no document.
The readers that take a document to answer a domain or a path take the module instead, which is
what they were always asking about.

### THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT (decided 2026-11-02)

The record stores each distinct subtree once under its own `definitions` with a local reference at
each occurrence. **Every pointer any reader SPELLS keeps the spelling it has today.** The hoisting
is a storage representation and the readers dereference through it; it is not a renaming.

**WHY THE POINTERS MAY NOT MOVE.** `harness.corpus_key` walks no pointer — it hashes the document's
raw bytes and its closure's, plus the pointer, deliberately off our rendering and onto the static
upstream fact. But the pointer **is** in that identity, so respelling a declared pointer as
`#/definitions/Shared<N>` discards every held value and redraws the pair at its cold cost. The
store that makes the first reading affordable is exactly what a renaming destroys. So the hoisting
is invisible to every pointer any reader spells, and a declared pointer that stops resolving is a
defect of the hoisting rather than a consequence of it.

**THE RECORD'S OWN WALK IS A FORK AND NOT A PORT, and it is a SEPARATE DECISION** that must not be
taken inside the hoisting. `bundle.nodes` enumerates a pointer per occurrence. Either the walk
follows references and re-derives one per occurrence — which hands back every occurrence, so the
record shrinks and the walk does not — or it walks the DAG and yields one pointer per definition,
and then every census derived from it means something different. Both are defensible; neither is
implied by the hoisting.

`_base.applied_schema` is what makes that a decision rather than a relocation. It does not merely
walk: it carries the enclosing `type` through the same-instance hops, conjoins
`SAME_INSTANCE_FACTS` with the enclosing `allOf`, and applies §8's sibling-conjunct cut. Following
a local reference makes its answer stop being a function of `(document, pointer)` — **one shared
definition reached through two enclosing contexts has two applied answers.** So the conjoined facts
must accumulate ACROSS the hop, the definition may never be read alone, and a `definitions/Shared<N>`
segment is not an instance-bearing hop and must be transparent to the cut.

**SHARING ACROSS DOCUMENTS IS A DIFFERENT DECISION, and it is not taken.** Hoisting within a record
needs no new artifact. Hoisting across records needs one store every record references, which
breaks §1's *"a document compiles to a module at its own path"* and the record sitting beside it.
The floor it reaches is the bundle's own size, because that is what the bundle states once. Take
the within-record form first; decide the cross-record form against a weighed wheel.

### A DERIVED READING OF THE BUNDLE IS AN ARGUMENT, NOT SOMETHING A CALLEE RECOMPUTES (decided 2026-11-02)

§1 and §3 already say *"the bundle directory is an argument and nothing reads a hard-coded path"*.
**That rule extends one level: a set derived from the directory is also an argument.**

A callee that needs the set of a bundle's documents — to resolve a reference's head against the
documents that exist — must be **told** it, not go and find it. Finding it is a directory scan, and
a callee reached once per node performs that scan once per node.

**The answer is not a cache, and the staleness question that a cache raises is the reason.** A
cache keyed on the directory path is wrong the moment a test builds a bundle in `tmp_path` and adds
a document between calls; a cache keyed on the directory's contents has to read the contents, which
is the cost. **So the set is computed once per run, by the caller that knows the run, and threaded
to every reader that needs it.** `record` needs it only to resolve a reference's head against the
documents that exist, which is exactly the kind of fact a callee must be told rather than go and
find. A test building a bundle in `tmp_path` then gets whatever it passes, by construction, and
there is nothing to invalidate.

This is the same rule as §9's: **the RUN is not the BUNDLE**, and a reading of the bundle is stable
precisely because it does not depend on which documents the run names. Threading it makes that
visible in the signature instead of leaving it to a comment.

Without it the compiler reproduces the defect it was built to escape. `datamodel-code-generator`
emitted a type per position and the result was duplicate classes and unions nobody could name; a
hand-written walk that also emits a type per position arrives at the same place with more effort.
**Faithfulness per node is not consistency across the bundle**, and only the second is what a
consumer experiences.

### What is there to collect, and WHICH READING is the open question

| layer | distinct identities | repeated | positions covered | widest |
|---|---|---|---|---|
| **L1** constrained scalars | 1,776 | 1,315 | 59,516 | 4,127 |
| **L2** object types, 2+ properties | 13,453 | 1,368 | 13,151 | 450 |
| **L3** array types | 6,712 | 1,808 | 11,746 | 1,242 |

**L0 is counted over STATING POSITIONS (decided 2026-11-02).** Three readings of the bundle are
reproducible and they disagree by more than an order of magnitude, so the row names which one
governs:

| reading | positions | identities | repeated | titled / untitled / conflicting | cross-domain |
|---|---|---|---|---|---|
| stating positions, raw | 1,069 | 822 | 165 | **15 / 124 / 3** | 61 |
| the inlined record | 171,331 | 805 | 623 | 209 / 411 / 3 | 550 |
| declaration + one `$ref` hop | 1,999 | 805 | 371 | 211 / 157 / 3 | 245 |

My figure came from a record reading presented as a bundle reading. **The tell is that 3
conflicting titles reproduce in every one of them**: a title is stated once and every `$ref`
carries it along, so inlining multiplies the titled and untitled groups and leaves the conflicts
untouched. The nameable population is therefore on the order of **15 entries, not 203** — a
thirteenfold overstatement, and the kind this document exists to prevent rather than produce.

**Which reading L0 collects over is not yet decided, and it is the first question of the row.** It
is not a detail: the raw reading names 15 entries and the record reading names 209, over the same
bundle. §3a's TREE figures are unaffected and reproduce exactly — 897 enum classes carrying 715
distinct member-sets, 128 of those emitted more than once across 310 classes.

### What the catalogue does NOT fix, measured before it was built

The 457 mypy errors in the generated tree were presented as the catalogue's headline. They are
not. The 362 `[assignment]` decompose as **145** an enum base against a `Literal` pin, **44**
`dict[str, Any]`, **31** object, **23** container, **21** an enum against a different enum class;
and of the 166 enum-base errors, **108 are stated at a single position** so a cross-document
collection never reaches them, **41 are untitled cross-document** which this section expressly
refuses to collapse, 5 are same-document restatements §4 already owns, and 2 are the conflicts.

**So L0 reaches roughly 10 of the 264.** The 145 belong to Pass B — `const` against `enum` — and
**89 of those are single-document**, needing no catalogue at all. Pass B is therefore both the
larger win and the cheaper one, which reorders the work: the normalisation comes first and the
cross-document collection second.

### The gate is worded PER TITLE, never per member-set

"No two classes carry one member-set unless the bundle gives the field no title" cannot go green,
and the reason is instructive. `{closed, open}` is stated at `enums/gop-type.json`'s root, titled
**'GOP Type'** for video Group-of-Pictures, and at four untitled positions —
`core/opportunity-context.json`'s `status` and three governance `delivery_period_state`. Under
member-set identity that group IS titled, so satisfying the gate types a governance reporting
field as `GOPType`: the coincidental overlap the untitled rule exists to refuse, arriving through
the IDENTITY instead of through the name. Measured both ways: the member-set reading gives 17
titled member-sets under 42 names and is unfixable at that entry; a per-title reading gives 12 of
15 entries under more than one name, 29 classes for 15 entries, and is fixable.

### A CONFLICTING TITLE NEVER COLLAPSES, and the reason is §4's (decided 2026-11-02)

All three conflicts in the bundle resolve the same way, and the descriptions settle them:

- **`Catalog Action` / `Creative Action`**, both `['created','updated','unchanged','failed','deleted']`
  — *"Action taken on a catalog during sync operation"* against *"Action taken on a creative during
  sync operation"*. **Two concepts over one value set.** The values and the semantics coincide; the
  SUBJECT does not.
- **`Delivery Recipient Cloud` / `Reporting Cloud`**, both `['aws','azure','gcp']` — the cloud
  hosting a delivery recipient's account against the cloud a reporting dataset is shared into.
  **Two concepts over one value set.**
- **`Canonical Media Buy Action Mode` / `Media Buy Action Mode`**, identical members and nearly
  identical descriptions. **One concept stated twice** — a canonicalisation left beside its
  original.

**Neither case collapses, and the rule is one sentence: a conflicting title is not a question
about which name wins.** Where the bundle states two concepts, both names are right and merging
types one subject with the other's name. Where it states one concept twice, the duplication is the
BUNDLE's and removing it is an upstream report, not a rename we perform — and a merge would hide
the evidence the report needs. In neither case is there a third name to collapse to, and minting
one is what §4 refuses.

So the three-way naming split's third arm is **decided, not deferred**: a conflict is reported and
left alone, and the only judgement is whether to file it upstream.

### A DOCUMENT ROOT IS ALREADY A HOME (decided 2026-11-02)

13 of the 15 nameable entries are stated at a document ROOT. **§4 governs and the
narrowest-namespace rule does not reach a root**: a root is not an entry looking for a home,
because §1's "every portable document contributes a symbol" means `enums/gop-type.json` already
exports `GOPType` from `adcp.types.enums`. There is nothing to relocate.

**So L0's job for those 13 is not to move them — it is to stop every other position minting a
copy.** The other positions reference the existing symbol, which is what §5's `$ref` row already
does for a position that spells the reference; the defect is the positions that restate the
vocabulary inline instead. That is a smaller and better-defined change than a relocation, and it
explains the measurement that looked wrong: **`adcp.types.common` holds 1 entry for L0, not 653**,
because 13 of 15 are already at home.

### PASS B RUNS FIRST, and it needs no catalogue at all (decided 2026-11-02)

The order in this section is reversed on measurement. Pass B — a `const` pin naming its enum's
member — carries **145 of the 457** type errors, and of its 145 sites **97 have the base's enum
declared in the same module and 48 import it**. In both cases the class that types the base's
field already exists and is already one object; the pin has only to name its member. `ir.TypeRef`
already carries the members, and the compiler already renders `Literal[Symbol.MEMBER, …]` for the
`$ref`-target case. Pydantic renders `Literal[E.A]` as `{"const": …, "type": "string"}`,
**byte-identical** to `Literal['…']`, so no accepts verdict and no dump moves.

L0's cross-document collapse reaches about **10**. So the normalisation is both the larger win and
the one with no namespace question, no new ordering edge and no relocation — it goes first, and
the collection follows it.

### THE VALUE LIST IS WRITTEN ONCE; THE NAMED TYPE IS PER POSITION (decided 2026-11-02)

An identical value set is emitted repeatedly today. Measured over the tree: **128 value sets are
emitted more than once, across 305 classes under 189 distinct names, restating 632 member strings
that the bundle states once each.** That is the cost of compiling a position without asking what
already exists.

**But collapsing them into one type is the wrong repair**, and the reason is the untitled rule:
nothing names those sets, so two positions sharing a member set may be two concepts that coincide.
Merging would type one with the other's name.

So the two halves separate:

- **the VALUE LIST is a module-level constant in the catalogue layer, written once per distinct
  member set;**
- **the NAMED TYPE is constructed from it at each position that needs one**, keeping the name §4
  derives and keeping the types distinct.

`StrEnum('CatalogAction', …)` and `StrEnum('CreativeAction', …)` built from one list are two
types that are not assignable to each other and share one definition of the values. Nothing is
restated, nothing is merged, and a reader sees the vocabulary in one place.

**Where a title exists the stronger rule still applies**: one type, named for the title,
referenced by every position. A title is a human string and the type is an identifier, so the
title is rendered in the tree's own convention — `Account Status` names `AccountStatus` — and the
convention is not a second decision per entry. The construction above is for the untitled sets, which are the
population.

### THE SAME VALUES UNDER TWO NAMES IS A POPULATION OF THREE

Measured across the whole bundle, one member set carrying more than one title happens exactly
three times:

| titles | members |
|---|---|
| `Delivery Recipient Cloud` / `Reporting Cloud` | `aws, azure, gcp` |
| `Canonical Media Buy Action Mode` / `Media Buy Action Mode` | identical four |
| `Catalog Action` / `Creative Action` | `created, deleted, failed, unchanged, updated` |

Two are two concepts over one value set and keep both names. The third states one concept twice
and is an upstream report. **None of them motivates machinery**: three cases and twelve member
strings. The scale is entirely in the untitled 128.

### EVERY REPEATED VALUE SET IS AN UPSTREAM QUESTION (decided 2026-11-02)

"One concept stated twice" and "one concept we should name" are the same finding, so they are not
two verdicts. A value set stated at more than one position is a defect in the SPECIFICATION
whatever we do about it locally: either the bundle defines one thing twice, or it defines two
things that coincide on their values and says nothing about why. **Both are questions for the
specification, and both are filed.**

So the verdict space has two axes and they are independent.

**What we emit** — one named type serving every position, or several types sharing one value list.
That is the local decision and it is settled by whether the positions are about one subject.

**What we ask upstream** — and there is always something to ask:

| the positions are | we emit | the filing asks |
|---|---|---|
| one subject | one named type | you define this twice; define it once and `$ref` it |
| different subjects | one type per subject, one value list | these have identical values — do you mean different things? If yes, say so; if no, define it once |

`Catalog Action` against `Creative Action` is the second row, not an outcome that closes. Identical
five members, one about a catalog and one about a creative — which is a reasonable thing for the
bundle to mean and an unreasonable thing for it to leave implicit. **The filing asks the question
rather than asserting the answer**, because the specification's authors know which they meant and
we are inferring it from two descriptions.

**The filings are consolidated before they are sent.** 128 sets filed one at a time is noise that
buries the finding; the same 128 analysed into the families they fall into is a case the
specification can act on. So the analysis completes first, the filings are grouped by family, and
nothing is sent per set.

### WHEN A NAME IS THE BUNDLE'S, AND WHEN IT IS MINTED (decided 2026-11-02)

§4 refuses to mint a public name no document states, and judging 63 sets produced four distinct
ways of arriving at one. The line is per TOKEN: **a name is the bundle's when every token in it is
stated at that vocabulary's own positions.**

| how the name was reached | stated? | ruling |
|---|---|---|
| a `title` the set carries at some position | yes | **take it** |
| a `title` plus a discriminator the positions state — `US` + `Postal Code System` | both tokens | **take it** |
| the property name the positions share | yes | **take it** |
| a stated name lengthened to avoid an existing class | yes, plus §4's own rule | **take it** — that is the collision rule, not a mint |
| a noun phrase lifted from a `description` | **no** | **refuse** — prose is not a name |

A `description` states what a thing IS; it does not state what it is CALLED. `VariantAxisDimension`
and `FeatureValueType` read well and neither is in the bundle, and a reader cannot check them
against anything — which is the whole of §4's objection. **A set whose name can only be composed
from prose is not nameable, and the filing asks upstream to name it.**

### "DISTINCT" AND "UNNAMEABLE" ARE DIFFERENT, AND ONLY ONE IS TERMINAL

Of thirteen sets left separate, four were left separate because no name could be found rather than
because the subjects differ — the judgement recorded one of them as "arguably one notion" and
unnameable. **That is not the same verdict**, and collapsing the two hides which of them upstream
can fix.

So the local state is one of three:

- **one named type** — the positions are one subject and the bundle names it;
- **separate types, one value list** — the positions are genuinely different subjects;
- **separate types pending a name** — the positions are plausibly one subject and nothing in the
  bundle names it. The filing asks for the name, and the local answer changes when it arrives.

The third is where the bundle's silence costs us, and it is the row most worth filing, because the
answer is a word the specification's authors already have.

### WHAT THE CATALOGUE DOES TO AN APPROXIMATION'S DENOMINATOR

An approximation is counted today at the declaration SITE, because each position derives its own
type and a dropped fact is dropped at that position. **Under a catalogue the denominator becomes
the ENTRY**: a constrained scalar appearing 4,127 times and dropping one fact is one approximation,
not 4,127. The 120 declared facts are a per-site reading and will not survive the change —
whatever they become must be re-derived and reported as a changed denominator rather than as
progress.

**And the near-duplicate constraint question is a different kind, not a smaller one.** 1,775
distinct constrained-scalar types cover 59,873 positions. A `format: uri` position carrying a
`pattern` is not two rules that nearly agree — it is one rule compiled to a non-injective type,
which is a NARROWING and already decided in the semantics document's §2. Two types differing in a
single constraint keyword are a separate question, and **the census for it does not exist**: a
reading keyed on "same value-carrying keyword, differing constraint" is what would answer it, and
a cruder key counts two unrelated vocabularies as a near miss. That census is owed before any rule
about near-duplicates is written.

### The layers are BOTTOM-UP, and that is why they are layers

An object type's identity is the identity of its property types, and an array's is its item
type's. So L2 cannot be collected before L1 and L0, and a single sweep cannot do it: the same
object spelled with an inline scalar in one document and a `$ref` to the same scalar in another is
one type only once the scalar below it has been collapsed. **Collect L0, then L1, then L2, then
L3**, each layer's identity computed over the catalogue entries beneath it rather than over raw
JSON.

### Two passes, and the second is where the schema's own inconsistency is absorbed

**Pass A is DETERMINISTIC**: structural identity, as measured above. It is reproducible, needs no
judgement, and is where the figures in the table come from.

**Pass B is NORMALISING** — the same concept spelled two ways, which Pass A cannot see because
the two spellings are genuinely different JSON. The known cases, each a separate decision with
its own measurement:

- **`const` against `enum`.** `core/registry-event.json` states `enum: [...]` at its root's
  `event_type` and `const: "property.created"` at its branch's. One vocabulary, two keywords.
  This is the case that produced 362 of the generated tree's 440 type errors.
- **a single-member `enum` against a `const`** — the same fact from the other side.
- **`format` against `pattern`.** `{type: string, format: uri}` and
  `{type: string, pattern: "^https://..."}` constrain overlapping sets by different keywords.

Pass B runs AFTER Pass A and only over what Pass A left distinct, so a normalisation can never
merge two types that structural identity already told apart.

### The catalogue is an INPUT to the walk, never a pass over its output

The walk consults it: a node's type is a REFERENCE to a catalogue entry, or a fresh type where
the node is genuinely unique. Rewriting emitted output to deduplicate it afterwards is the
post-processing this project exists to refuse (§2 of the semantics document: "nothing rewrites
emitted output"), and it is also where the previous generator's patches lived.

This places the catalogue before naming, which §9's census rule permits and §1's domain-scope
collision rule already requires: both read the BUNDLE, which is pinned and is an input to every
run alike, and neither reads the run's document set.

### The NAME comes from the bundle, so a catalogue entry is derived and not minted

§4's standing rule. For L0 this is already decided and measured: 203 vocabularies carry exactly
one `title` the bundle gives and that title is the name; 457 carry none and are **not** collapsed
across documents, because nothing names the concept and without a title there is nothing to tell
a coincidental member-set overlap from an identity; 3 carry conflicting titles and are a decision
brought to the owner. **The same three-way split is the rule for L1, L2 and L3, and each layer's
counts are to be measured rather than assumed from L0's.**

### What this does to the defects already open

The `const` override dissolves rather than being patched: where a root's `enum` and a branch's
`const` are one vocabulary, both reference the one entry, so the pin is `Literal[Entry.MEMBER]`
because no other member exists to name. `82m.10`'s 44 names crossing as a BASE become a question
about one catalogue entry rather than 44 export decisions. And the wheel can honestly ship
`py.typed`, which today it cannot.

### WHERE A CATALOGUE ENTRY LIVES, which is what makes the fencing unnecessary

The clause that forbade cross-module identity was guarding something real: shared types reached
for across document modules create import cycles, and the bundle's own design invites them — one
vocabulary is stated in up to **five different domains**. Measured over 807 vocabularies: **154
are confined to one domain and 653 cross more than one.** Sharing is the main case, not an edge.

**But a cycle is only possible if the shared type lives INSIDE a document module.** Put the
catalogue in its own layer beneath every document module and the dependency arrows point one way,
so a cycle is not avoided by care — it is unrepresentable:

```
L0 vocabularies      → depends on nothing
L1 constrained scalars → L0
L2 object types       → L0, L1
L3 array types        → L0, L1, L2
document modules       → any catalogue layer, and each other by §10's existing order
```

That is the whole of the answer to the fencing. We cannot fix the schema's habit of restating a
concept in five places; we decide the layers we emit it into, and the layering removes the hazard
the prohibition was written for.

**An entry lives in the NARROWEST namespace that contains every position referencing it**, which
keeps a consumer's import close to where they met the concept and is derived rather than chosen:

- referenced from one document → that document's module, which is what happens today;
- from one domain → that domain;
- from more than one domain → the shared namespace, which is the 653.

**The shared namespace is `adcp.types.common`, one place and not one per layer.** A consumer who
does not know which domain a type belongs to has exactly one place to look, and does not have to
guess whether `AuthenticationScheme` is a "value" or a "case". The LAYERS are the private
module structure beneath it — the same split the tree already makes, `_schemas` private and the
domain modules public — so the acyclic order is a property of the emission and the public surface
stays flat.

**And this is the reuse the design was for.** 653 vocabularies stop being re-derived per domain;
one scalar case that appears 4,127 times is declared once; and a type a consumer receives in a
`media_buy` message is the same object as the one in a `governance` message, so it can be passed
between them. That last property is the one nothing in the artifact provides today.

### Upstream

The bundle spelling one vocabulary as `enum` in one place and `const` in another is a defect in
the SCHEMA, not only in our reading of it, and Pass B exists to absorb something upstream should
not be emitting. It is worth filing against the specification — the owner reports that part of
this normalisation has already landed in the 3.3 bundle, which is evidence the report would be
accepted rather than argued.

---

## 4. How the JSON is read

### The bundle and the document of record

`codegen/bundle.py` owns every file read. It exposes the document set (`portable`), one
document as a raw mapping (`read`), the one reading of a `$ref` URI (`split_ref`,
`document_for`), the reference graph over the bundle (`edges`: every `(document, pointer,
target document, target pointer)`, read off the raw mappings by the table's descent column),
and the **document of record** (`record(bundle, document)`).

`record` is this package's own inliner, and it does what §3 of the semantics document says and
nothing else: every cross-document `$ref` is replaced by a deep copy of its target node, with
the referring node's own annotation keys kept beside the copy and the referring node's value
winning where both state one; a local `$ref` stays as written; no key is dropped, derived,
reordered or respelled on either side. A copy taken from document D has its own local
references inlined from D before it is placed, because it is leaving D's root scope. A
reference whose target is not a bundle document, and a cross-document cycle, make the record
undefined for that document, and `record` returns a `Refusal` (VERDICT) rather than a mapping.
The payload generator's resolver (`hypothesis_jsonschema`) is confined to drawing payloads in
`verify/accepts.py` and never writes a document anything else reads.

**This is the one refusal the compiler mints (2026-10-26, §2 of the semantics document).** The
principle that unifies its structures is that **the document has no defined accepted set**: there is
no schema half for `strict_validate` to run and nothing for §8 to grade against, which is the
one place the partial-model objection still bites. Three cases reach it — a reference whose
target is not a bundle document, a cross-document cycle, and a document that **fails its own
declared draft's meta-schema** (the case failures `parse` validates for below, which were
VERDICT refusals of their own and are this class rather than a second one, since a document that
is not a schema under its own draft has no accepted set to be faithful to). Measured over bundle
3.2's 1,054 portable documents, all three are **empty**: 0 undefined records, 0 meta-schema
failures. That measurement is why "zero refusals" is reachable for this bundle rather than
aspirational, and the class stays in the compiler so a bundle that grows one reports it instead
of crashing on it.

A **local** `$ref` cycle is not in this class: it is never inlined, and it renders as a forward
reference under a string annotation with a `model_rebuild()` after the module's declarations
(§6). The difference between the two cycles is the record and not the type.

*Why our own.* The record is what `strict_validate` validates against and what the draw
grades against. A resolver that canonicalises while it inlines writes a document the bundle
does not state, and every reader downstream then needs a fold to undo each rewriting — the
verifier carries folds of that kind today. An inliner that changes nothing needs none.

### The node, and the parser that is the one reading

`codegen/schema/nodes.py` declares the in-memory form, and it is a **typed representation of a
schema node, not the raw mapping**. One frozen dataclass per kind, each carrying exactly the
keywords its kind can consume, already validated for case:

| node kind | selected by | carries |
| --- | --- | --- |
| `Reference` | `$ref` | document half, pointer half, annotation siblings |
| `Enumeration` | `enum` | members, member descriptions (both spellings), the applied type word |
| `Constant` | `const` | the value |
| `Composition` | `allOf` | conjuncts at CONJ, own properties and required, extra policy, rule sources |
| `Union` | `oneOf` / `anyOf` whose branches are cases | combinator, branches at BRANCH, the root's siblings when at ROOT |
| `Object` | `type: object` (stated or applied) with `properties` | properties at PROP, required, extra policy, key schema at KEY, rule sources |
| `Mapping` | `type: object` without `properties` | value schema at MAPV, key schema at KEY, key-count bounds |
| `Array` | `type: array` | element at ELEM, bounds, distinct, contains predicate |
| `Scalar` | one scalar type word | constraint facts in the document's spelling, format |
| `MultiType` | a `type` list | one `Scalar`/`Array`/`Mapping`/`Null` member per word, each holding only the keywords that word can carry |
| `Null` | `type: null` | nothing |
| `Typeless` | no type and no kind keyword | a `not` over a value, or nothing |

Every node also carries `pointer`, `position`, `applied` (the type word an enclosing node
asserts about the same instance, read by the rule `adcp.types._base.applied_schema` already
states), and `annotations` (`title`, `description`, `default`, `deprecated`, `examples`, and
the admitted `x-` keys). `pointer` and `position` are excluded from equality, so two nodes are
equal exactly when they state the same thing about an instance — which is §4's content dedup
read off the type system rather than off a JSON serialisation with a position bit appended.

`codegen/schema/parse.py` is the one function that reads a raw mapping:

```python
def parse(raw: Mapping, *, document: str, pointer: str, position: Position,
          applied: str | None) -> Node
```

**`parse` is total too (2026-10-26).** It returned `Node | Refusal` and the refusals it minted
were the case failures below. A document that fails its own meta-schema has no accepted set and
is `bundle.record`'s refusal before `parse` is ever called, so by the time a mapping reaches
`parse` its structure is a draft-07 schema's and a failure here is the compiler disagreeing with the
meta-schema — a `BuildFailure`, not a document outcome. The checks stay; what changes is who they
blame.

It does four things at every node. It screens every key against the table at
`position` (§3's admission reader). It classifies the node: the kind-determining keywords
present select the kind, and the co-occurrences the semantics document decides are decided
here and nowhere else — a `$ref` beside a constraining key refuses on the sibling; an `enum`
beside `type` is an enumeration whose base the members decide; `allOf` beside `properties` is a
composition with fields of its own; a combinator whose every branch is `required`-only is not a
`Union` but a rule source of the enclosing object (the `presence_only` reading, read once
here); a `type: object` beside `oneOf` is a union whose branches inherit the applied word. It
descends by the table's descent column, assigning each child its position and the applied
word for a same-instance hop. And it validates case: `required` is a list of names,
`properties` is a mapping of schemas, and so on, each failure a `BuildFailure` by the paragraph
above. **`items` is no longer among them**: a list-valued `items` is draft-07's tuple validation,
and the semantics document's §5 now lowers it to `list[A | B | …]` at the JOIN rung rather than
refusing it, so the parser builds an `Array` whose element is the join and records the
approximation. Unexercised in bundle 3.2, which states no list-valued `items`.

*The screen and the classification INTERLEAVE, and this said "in this order" (2026-10-26).*
They cannot be strictly sequenced, because the admission arms do not all answer from the cell
alone. Two of them do — a key with no row and a NOTHING cell are decided by
`cell(keyword, position)` and nothing else, so they run before anything is classified. The
third does not: §3's reader ends "any other effect is a fact the node's kind consumes", and
whether a lowering effect is CLAIMED or is WIDENED is a question about which kind owns the
node. So that arm runs after the classification it depends on. *(The REFUSE arm was a third
cell-only one and retired with `Effect.REFUSE` on 2026-10-26; the dependency this paragraph
settles is unchanged, since it was never that arm's.)*

The four jobs and their contents stand; what is wrong is the claim that they are four sequential
passes. A node is classified once and screened once, and the dependency runs one way: admission
that reads only a cell, then classification, then admission that reads the kind. Nothing is
screened twice and no mapping is traversed twice, which is what §4 is actually protecting.

A node at RULE is parsed like any other, kept on the enclosing node as a rule source, and is
never handed to `decide`: under a conditional a keyword describes what a rule tests, so no type
is lowered from it, and `lower/rules.py` is its only reader.

*Why the parser decides the kind.* The owner's model is that reading a node's keys and its
type selects the entity that knows how to represent that thing. Constructing the node of that
kind IS that selection, and it happens once, before any lowering. Everything downstream is
type-directed and cannot disagree with it.

---

## 5. Where the decision is made

The decision has two inputs, the node's kind and its position, and the structure separates
them because they vary independently: the kind decides WHICH handler; the position decides
what that handler's answer is where the semantics document gives a position-dependent cell.

The kind is decided in `parse` (§4). The dispatch on it is `codegen/lower/decide.py`:

```python
def decide(node: Node, ctx: Context) -> Lowering:
    match node:
        case Reference():    return references.lower(node, ctx)
        case Enumeration():  return enums.lower(node, ctx)
        case Constant():     return constants.lower(node, ctx)
        case Composition():  return composition.lower(node, ctx)
        case Union():        return unions.lower(node, ctx)
        case Object():       return objects.lower(node, ctx)
        case Mapping():      return containers.mapping(node, ctx)
        case Array():        return containers.array(node, ctx)
        case Scalar():       return scalars.lower(node, ctx)
        case MultiType():    return containers.multi_type(node, ctx)
        case Null():         return scalars.null(node, ctx)
        case Typeless():     return scalars.typeless(node, ctx)
        case _:              assert_never(node)
```

This is the one place a node's kind is routed, it contains no decision beyond the route, and
`assert_never` makes the type checker refuse a kind the match does not cover. A handler takes
its node and the context and returns a `Lowering` — always, by §2. It reads the table for every
keyword on its node, consults the position through `node.position`, and where it meets a case
of its own kind it has no rendering for, its final arm calls `approximate(node, keyword)` and
composes the result like any other child. **A handler has no second return type and no raise**,
so there is one case of answer at this seam and `assert_never` is the only exhaustiveness the
type checker still proves here.

**The form, against the alternatives.**

- *A mapping from (position, kind) to a handler.* Rejected. The position changes the handler's
  ANSWER at a few cells — a bound rides on the field at PROP and on the named type at ELEM,
  MAPV and BRANCH; a root alias gains a module-level binding; a DEF entry takes the
  `<Root><Key>` name — and changes the HANDLER nowhere except RULE, where nothing is lowered.
  A product table is therefore mostly copies of one row, which is the repetition this document
  exists to remove, and it hides the one real position dependency (the cell) behind copies of
  one row.
- *A polymorphic hierarchy with `lower` on each node.* Rejected for §2's reason: with one
  operation over a closed set, a method per class is the match spread across the files that
  read JSON, and those files then import the IR and the keyword table. The node classes stay
  data.
- *A tagged union and an exhaustive match.* Chosen. The kinds are a closed sum, the match is
  total by construction, and the handlers are plain functions testable with a hand-built node
  and a context — no module object, no callables threaded through a dataclass.

**Root and non-root are one path.** There is no second table of root selectors. A document is
`parse(raw, position=ROOT)` followed by `decide`. The only thing ROOT adds is the module
wrapper — a class carries `strict_validate` by inheritance, and a root whose lowering is an
alias or an enumeration gets a `RootBinding` declaration from `lower_document`, which is the
one function that knows a root is a root. The document-set predicates a step's result was
stated over are the tests' business and live under `tests/`.

**The committed tree's own population is not one of those predicates (added 2026-10-29).** It
is `bundle.portable` — every document of the bundle that can be emitted at all — because the
tree is an ARTIFACT and not a phase. The steps' selectors grade their steps and are untouched by
this; written from their union the tree omits documents that emit, and which ones it happens to
carry depends on what a past run reached through `$ref` closure, which is not a derivation.

**The context.** `Context` is a frozen value built once per document by `lower_document` and
passed down unchanged:

| field | what it is |
| --- | --- |
| `document` | the bundle-relative path, for `SchemaRef` |
| `root_symbol` | `pascal_case(title)`, the parent of every derived name |
| `targets` | `Mapping[document, Lowered]`: every document this one references, already lowered by the run in dependency order (§7), so a cross-document reference is a lookup and never a callback |
| `named` | the pointers of this document a `$ref` anywhere in the bundle names, so a node that is otherwise an annotation gets a symbol |
| `asserted_formats` | the formats the document's own draft has an installed checker for |
| `resolving` | the local-reference pointers in flight, innermost last, for cycle refusal |

---

## 6. How descent works

**Who walks.** The parser walks the raw document once and builds the whole tree; after it, no
layer walks a mapping. `decide` recurses over the tree: a handler calls `decide` on each child
node it lowers — a property, an element, a value, a branch, a conjunct — and composes the
results.

**Who carries the position.** The node does. The parser assigned it from the structural keyword
it descended through, so a handler never derives position from a pointer string, and the one
place that did is `enum.resolves_no_name`, reading `hops[-2]`.

*What that one place becomes, settled 2026-10-26.* This said `node.position is BRANCH` and that
is the wrong fact. `position is BRANCH` says "this node is a branch of some union", while the
predicate it replaces answers "this node is a branch of a ROOT union" — and the two differ.
Taking the shorter sentence literally turns `error-details/accessibility-violation.json`'s
`StrEnum` into a `Literal`, which changes a module where a document emitted before and so breaks
§14 step 5's own check; the row measured it rather than reasoning about it.

The fact belongs to the UNION, not to the enum. §5 of the semantics document writes the row as
"an untitled BRANCH of a root union → a `Literal` of the members", and "of a root union" is a
statement about the enclosing union. §4 already gives the `Union` node the root's siblings when
it is at ROOT, so the union knows its own position; the branch lowering is told by its parent
rather than inferring it from itself. So the enum handler reads a fact it is HANDED, the union
handler reads `node.position`, and no node parses a pointer. The rule generalises: where a
lowering needs to know something about the node ENCLOSING it, the enclosing handler passes it
down — a child never reconstructs its parent.

**How a child's result composes.** `Lowering` is:

```python
@dataclass(frozen=True)
class Lowering:
    type: TypeRef                       # what the parent writes where it holds this node
    declarations: tuple[Declaration, ...] = ()
    imports: frozenset[Import] = frozenset()
    aliases: frozenset[ConstraintCase] = frozenset()   # for adcp.types.constraints
    approximations: tuple[Approximation, ...] = ()      # §2's widenings, accumulated
    reports: tuple[Report, ...] = ()    # a dropped default, a name the class carries nothing for
```

A parent takes `child.type` for its field, element, value or branch, and adds the rest to its
own. An object handler, for instance, is `Lowering(type=Local(pointer),
declarations=(ClassDecl(...), *children_declarations), ...)` — with no guard before it, because
every child answered.

**What an approximation does to the walk, 2026-10-26.** *This said "what a refusal does to the
walk" and the directive replaces the whole mechanism.* It said: a handler that receives a
`Refusal` from a child returns it unchanged and immediately, the refusal reaches
`lower_document` naming the innermost pointer and keyword that produced it, and the document
produces no declarations at all.

An approximation does the opposite at every step. It is **local** — it belongs to the node that
could not render a keyword and says nothing about the node above it — so a parent composes it
like any other part of a child's lowering and keeps building. The document emits. What reaches
`lower_document` is therefore not one approximation but all of them, in document order, because
`+` concatenates and the children were lowered in the order the document states them. The
report is still a function of the document and not of the walk's iteration, by the same
property that made `first_refusal`'s answer one: the parser built each node's children in
document order, and concatenation preserves it.

**The partial model is still unrepresentable, and for a better reason than before.** It used to
be unrepresentable because a `Lowering` and a `Refusal` are different types; now it is
unrepresentable because there is no partial model to represent — a document either has no
accepted set at all (§4's one refusal, and then it has no module) or it emits a complete
module for every node of itself, some of whose annotations say less than their document does and
each of those declared.

**References.** A cross-document `Reference` lowers to an import: `ctx.targets[document]` holds
the target's `Module`, whose symbol table answers the pointer half. **A pointer the target
declared no symbol at widens**, to the target's own root symbol where the fragment is reachable
under it and to TOP otherwise, and declares the approximation naming the fragment — it was a
DEFERRAL. A target with no record of its own is not reached at all: the run never lowers a
document whose record is undefined, and a document referencing one has no record either (§4).

A local `Reference` (`#/definitions/x`) lowers to the declaration of that `definitions` entry:
the entry was parsed at DEF, `decide` is called on it with `ctx.resolving` extended, and the
entry's own lowering is the symbol. **A pointer already in `resolving` is a cycle, and a cycle
is a forward reference, not a refusal (2026-10-26).** The declaration takes the entry's symbol
as a string annotation and the module calls `model_rebuild()` after its declarations — the
mechanism §4 of the semantics document already uses for union branches, which do not exist while
their base is built. So `ctx.resolving` stops being a refusal trigger and becomes what it always
described: the pointers in flight, which is how the lowering knows to write a forward reference
rather than recurse. Unexercised in bundle 3.2, which states no local cycle; the row is decided
before one arrives rather than after.

An entry nothing references is never decided, which is the §5 rule that a `definitions` section
is nothing by itself.

**Composition.** A `Composition` handler lowers each `$ref` conjunct to a base — the target's
`ClassDecl` is read off `ctx.targets` for its field case — and merges inline conjuncts' fields
and rule sources into its own by the intersection rule, which moves from `compiler.py` to
`lower/composition.py` unchanged in substance: `restatement`, `intersection` and
`at_least_as_tight` are pure functions over two nodes and stay so. A conjunct carrying its own
`allOf` is a `Composition` node at CONJ and the handler recurses.

**Unions.** A `Union` at ROOT whose branches are all cases lowers to a base `ClassDecl` carrying
the branch-dispatch facts and one `ClassDecl` per branch, each branch a class with the base first
among its bases; the root's siblings compile onto the base as §5 of the semantics document says.
A `Union` at ROOT whose branches are all scalars lowers to an `AliasDecl` and a `RootBinding`.
**A `Union` at ROOT mixing the two lowers to a `RootModelDecl`** over the union of the branches'
types, with the class branches declared beside it and the dispatch facts on the root model —
§4 of the semantics document's new row, which replaces a refusal and costs no approximation,
because the union admits exactly what the document admits. A `Union` below the root lowers to a
`TypeRef.union` of its branches' types, each branch's bound carried on the branch's own named
type.

A union whose branches §4 of the semantics document cannot separate lowers the same way it would
if they were separable. Where the combinator is `oneOf` it declares a WIDENED `Approximation` at
the union's own pointer, because the model then admits a payload the document refuses and the draw
proves it. Where it is `anyOf` it declares **nothing**: the model admits exactly what the document
admits, and the only loss — which branch an overlapping payload becomes — is observable by no draw
and no dump. That is why UNDERDETERMINED and its set equality are retired (2026-10-30).

---

## 7. The intermediate representation: `codegen/ir.py`

There is an IR between a decided node and emitted text, and it is complete: nothing before
`render.py` holds a string of Python.

| declaration | what it carries |
| --- | --- |
| `TypeRef` | a Python type as a value: a `Symbol(module, name)`, a `Local(pointer)` resolved by the module's symbol table, a `Literal(values)`, a `List(of)`, `Dict(key, of)`, `Union(members)`, or an `Applied(alias, args)` for a generic constraint alias; plus `facts` (the constraint keywords in the document's spelling), `format`, and `validators` (rules bound to the type where no class holds it: `AtLeastOne`, `NotValue`, `Distinct`) |
| `Field` | wire name, Python name, `TypeRef`, required, default (with the absent/`None` distinction), description, deprecated, distinct |
| `ClassDecl` | pointer, `SchemaRef`, fields, bases (`TypeRef`s), description, extra policy, extras-store type, rules, and for a union base: `root_required`, `discriminator`, `combinator`, `branches` |
| `EnumDecl` | pointer, base word, members with descriptions, description |
| `AliasDecl` | pointer, `TypeRef`, description, format — a node another document names, or a root that is not a class |
| `RootBinding` | the `SchemaRef` and the symbol a module-level `strict_validate` binds, for a root that is an alias or an enumeration |
| `RootModelDecl` | pointer, `SchemaRef`, the root `TypeRef`, description, rules, and for a mixed root union the dispatch facts — a root that is an array, a mixed union, or a document stating no schema keyword |
| `UnionInstall` | the base and its branches, which the renderer writes as the `_branch_models` assignment and the rebuild |
| `Approximation` | document, pointer, keyword, kind (WIDENED, the only one), rung, the fact the annotation does not carry in the document's own spelling, and the attribution |
| `Module` | document, root symbol, declarations in declaration order, imports, approximations, the symbol table pointer → name, the adoption table pointer → declaring pointer |

**An approximation is a DECLARATION and not a report, and it is written into the emitted
module (2026-10-26).** A `Report` is a line the run prints and nothing reads — a dropped default,
a key that carries nothing. An approximation is read by the GRADER, and §9 forbids the verifier
reading the walk, so there are only two ways for it to get there: a side channel the run hands
the verifier, or the emitted artifact. It is the artifact: `render.py` writes
`__adcp_approximations__` onto the class, the root model or the enumeration, and beside the
module for an alias — exactly the split §4 of the semantics document already makes for
`strict_validate` — and `verify/` reads it as a consumer reads any other class attribute.

*Why the artifact and not a side channel.* `__adcp_schema__` is already there for the same
reason, and the review that put it there recorded it: a verifier handed its facts by the run
grades the run's account of the output instead of the output. A side channel also makes a
one-document run and a whole-bundle run disagree about what the verifier can see, which the
semantics document's §9 forbids for names and cases and which has no better claim here.

*Where it must NOT go.* Not into `Field(json_schema_extra=…)`. A declaration is a record of what
the model DROPPED, so writing it into `model_json_schema()` would put it into the very payload
contract it is a note about. The declaration is a class attribute: the verifier reads it, and
nothing a consumer validates against carries it.

**Rules are the runtime's own dataclasses.** A `ClassDecl.rules` tuple holds instances of
`adcp.types._runtime.RequiredGroups`, `ConditionalRequired`, `Dependencies`, `PropertyCount`,
`UniqueItems`, `ForbiddenGroups`, `NegatedConditional`, built by `lower/rules.py` from the rule
sources on the node. The renderer writes each one as a **constructor expression over the rule's
own `dataclasses.fields`**, so the names and the order are read off the declaration and not
restated. One declaration of what a rule is, written once as §2 of the semantics document asks,
and the walk composes values rather than formatting strings.

*This sentence said `repr` and now does not, settled 2026-10-25.* `repr` is one way to spell a
constructor expression and it was named here as the mechanism rather than the goal. It is
keyword-form, while the committed tree's rule calls are positional, so taking it literally
rewrites 432 of the tree's 444 rule lines across 169 modules — measured on §14 step 4's branch.
That step is marked *bytes* precisely because it is the largest relocation in the plan, and a
cosmetic argument spelling that moves text in 169 modules would blind the one check able to
prove the relocation decided nothing. Keyword and positional arguments to a frozen dataclass
construct the same object, so the spelling carries no meaning to trade for that.

What the structure requires is therefore the obligation and not the spelling: the call is
derived from the dataclass's own fields, and the one rule for spelling it lives in `render.py`
and nowhere else. Normalising that spelling later is legitimate as a DELIBERATE, stated text
delta with its own row; it is not something a relocation does on the way past.

*Why a complete IR and not the present economy.* Today the decision layer produces class-body
lines, rule tuples and module trailers as text, and a `Module` accumulates text blocks beside
its decision memo. That is not an IR with render concerns beside it; it is two layers sharing
a mutable object, and the review's symptom — one module holding the renderer, the keyword sets,
the name rules, the field builder and the composition reader — is the cost. With the IR
complete, the renderer is the only reader of the model layer it renders through, and a change
of rendering (a dmcg upgrade, a different spelling of an optional) touches one module.

**Naming is a pass over the module, not a thread through the walk.** `codegen/lower/names.py`
takes a `Module` whose declarations are keyed by pointer and whose `TypeRef`s name local
declarations by pointer, and returns the module with a symbol table, by §4 of the semantics
document's rules: the root by title; a nested declaration by its position — `<Parent><Property>`
at PROP, `<Parent>Item` at ELEM, `<Parent>Value` at MAPV, `<Root><Key>` at DEF; a branch by
title, then by the `const` it pins on the dispatch property, then by its sorted `required`
set. Content dedup is this pass: declarations whose nodes are equal are one class, declared
under the first pointer in document order, and every later pointer binds its own derived name
to it by identity. Two pointers deriving one name is a VERDICT refusal of the document, because
the document states two things one symbol cannot carry.

*A branch with no identity is NOT a refusal, corrected 2026-10-26.* This sentence said it was,
and §13 item 7 — closed the same day — gives §4 the fourth rule that retires it: a branch with
no title, no pinned `const` and no `required` set takes its index among the branches,
`<Base>Branch<i>`, and a missing or non-identifier root title takes the document's own file stem.
A name is not an acceptance fact, so a fallback name neither widens nor narrows. The two
sentences could not both stand, and row `.7` found them disagreeing in the sentence it was
implementing. `<Base>Branch<i>` is the answer; the population is 0 today.

The walk computes no name, which is the semantics document's own
rule that a name is an input to a lowering and is never computed inside one — read strictly,
it is not an input either: it is assigned after.

---

## 8. Rendering, and the one-way boundary with Pydantic

`codegen/render.py` is the only module under `codegen/` outside `verify/` that imports
`pydantic` or `datamodel_code_generator`. It takes a `Module` and returns the module's text; it
takes the run's union of `ConstraintCase`s and returns `adcp/types/constraints.py`. It renders
through the model layer of the pinned code generator and never its parser, for the reason the
present code gives: the parser decides names and structure, which is this compiler's half.

The boundary is one-way and a test enforces it (`tests/test_import_rule.py`, extended):
nothing in `schema/`, `lower/`, `ir.py`, `keywords.py` or `bundle.py` imports `pydantic`,
`pydantic_core` or `datamodel_code_generator`. A `TypeRef.Symbol("pydantic", "AwareDatetime")`
is a Python symbol the semantics document names in its `format` row, and naming a symbol is
not a Pydantic idiom; constructing a `Field`, a `ConfigDict`, an `Annotated` or a `DataType`
is, and only `render.py` does it. `codegen/constraints.py` keeps its naming rule — a pure
function from a constraint case to a `TypeRef` — and stops importing the renderer.

The runtime package `src/adcp/types/_base.py` and `_runtime.py` is the other side of the
boundary: `SchemaRef`, `applied_schema`, `strict_validate`, `strict_alias`,
`BranchDispatchMixin` and the rule validator are correct and the semantics document's §4 pins
them. Two extensions, and no replacement.

**`applied_schema`** gains the same-instance keywords §13 item 3 names.

**`AdCPRootModel`, new on 2026-10-26.** The semantics document's §4 now gives three cases to a
root model — an array, a union mixing a scalar branch with a class branch, and a document stating
no schema keyword — and each must carry `__adcp_schema__`, `strict_validate` and a rule tuple
exactly as a class does, or a root model and a class disagree about what their document accepts.
So `class AdCPRootModel(RootModel, RuleBound)` joins `AdCPBaseModel`, and **`strict_validate` and
`__adcp_schema__` factor out of `AdCPBaseModel` into a mixin both take** — one body, for the
reason `strict_alias` exists: a second implementation of the schema half is a second answer to
the one question. Measured on the committed runtime: that MRO resolves, the rule validator fires
on a root model, and `model_json_schema()` renders the root type's own schema, so a reader
pairs a root model as it pairs a class.

---

## 9. The verifier: `codegen/verify/`

The verifier grades an emitted class against the document it names, and it does so without
reading the walk. Its import set is the whole of that rule, and `tests/test_import_rule.py`
asserts it: `codegen.keywords` (for the compared set and the rungs), `codegen.attribution` (to
grade an approximation's issue reference), `codegen.bundle` (for the record and the document
set), `adcp.types` (the emitted package, reached as a consumer reaches it), `codegen.refusal`
(to read a refusal the run recorded), and its libraries. Never `codegen.schema`,
`codegen.lower`, `codegen.ir`, `codegen.render`, `codegen.emit`.

**`codegen.attribution` joins the set and `codegen.ir` does not**, which is the whole of why the
approximation is written into the emitted module (§7). The verifier reads the DECLARATION off the
class, as a consumer; it reads the registry to check the declaration's issue exists; it never
reads the value the walk built. Sharing the registry is sharing DATA, which is the same division
that already lets both halves read the keyword table.

*Why.* One body of code deciding what the model states and what the document states agrees
with itself by construction, so a defect in it is green on both sides. The verifier's reading
of the document — `_composed`, `_normalize`, the key-schema reading — stays its own, and the
intersection rule it carries stays a second spelling of the one in `lower/composition.py` on
purpose. Sharing DATA is a different matter from sharing a READING: the keyword table is the
declared semantics, and both halves must read the same declaration or the grade means nothing.

Its three checks are the semantics document's §8 and keep today's case: `accepts.py` draws
from the record and constructs; `dump.py` serialises and validates against the record,
striking the exemptions `exemptions.py` lists; `compare.py` compares `model_json_schema()`
against the record over the table's rendered column, fact by fact and in both directions. Every
fold that undoes a rewriting of the delegated resolver is deleted when the record is this
package's own (§4): the finite-type restoration, the derived `maxItems`, the `{"not": {}}`
closure, the dropped `additionalProperties: true`, the one-member `enum` respelling and the
same-title lift. What remains of normalisation is the readings this pipeline's own output
forces — a nested class hoisted to `$defs`, D4's `| None` for an optional property, a type list
rendered as a union — and each is applied to both sides.

**The approximation's grader, rewritten 2026-10-30.** There was one, not three: the draw. The two
comparison outcomes and two set equalities that stood here are deleted with the comparison, and
nothing replaced them, because a declaration either names a value the document admits and the class
now accepts, or it does not belong in the declared set.

| what is checked | where | how it fails |
| --- | --- | --- |
| an approximation's claim that the model is WIDER there | `accepts.py` | the draw takes the classes the dropped keyword distinguishes; a value the document admits and the class refuses is a narrowing wearing a declaration |
| an upstream attribution's issue | `attribution.py`'s own test | an entry with no issue is a `BuildFailure` |

The two equalities are what keep "approximated" from being an allowlist, and the reason they are
equalities rather than membership tests is the one §3 already gives for generation over diffing:
a set checked in one direction is complete with respect to itself, and what it omits passes.

**Pairing.** Every class, root model and alias is paired with the node its `__adcp_schema__`
names, read through `applied_schema`, so a branch class is graded against its branch node under
the root's same-instance keywords. That is the semantics document's §8 pairing rule and it is
also what `strict_validate` validates against, so the two cannot disagree. **The population is
every portable document**, and under §2 every one of them is in the pairing, so a document
absent from it is a defect in the run rather than a refusal with a reason.

**The record is read by the verifier's own walk**, `verify/record.py`, over the descent column
of the table. The verifier never calls `schema.parse`; it reads the document of record as a
mapping, because what it grades is what the document states and not what the walk made of it.

---

## 10. The run: `codegen/emit.py` and `codegen/__main__.py`

`emit(bundle_dir, documents)` is a fold over a dependency order. It reads the reference edges
off the bundle (`bundle.edges`), takes the transitive closure of the named documents over them
(a module cannot import from a module no run wrote), orders the closure so every document
follows the documents it references, refuses every document on a cross-document cycle as a
VERDICT, and then for each document in that order: `record` → `parse` → `decide` → `names` →
`render`, with `ctx.targets` holding the already-finished modules. A document whose target
refused is CHAINED without being parsed. The per-document `named` set is `bundle.named(edges)`,
a function of the bundle and not of the run's document set, so one document's module is the
same text whether it is emitted alone or with the whole bundle.

`write` writes the modules, the records beside them, the package `__init__` files and the
constraints module, and prunes stale emitted files on a whole-bundle run, as today. `main` lives
in `codegen/__main__.py`, so `python -m codegen` is the command and no module of the compiler is
ever bound as `__main__`.

**The layout, and a document whose path is also a directory's (decided 2026-10-29).** A
document's module is its bundle path with hyphens as underscores — `emit.module_path`, whose
one-line docstring was the only record of it until now. Where the bundle holds both a document
at path `P` and a directory at path `P`, **the two are one namespace and the document is its
root**: the document emits `P/__init__.py` and the directory's documents are its submodules.
`brand.json` beside `brand/` is the one such pair in bundle 3.2.

The alternative that was measured and rejected is writing both — `brand.py` holding 113 classes
beside a `brand/__init__.py` of 0 bytes, where Python resolves the name to the package and the
module is UNIMPORTABLE. A written module no import can reach is the artifact defect §14's tree
population row exists to remove, and it is silent: the run reports the document as emitted.

A distinguishing suffix is not taken, because it mints a public name no document states, and §4
derives every name from the document. Calling the bundle at fault is not taken either: the
layout is draft-07-legal and the bundle is pinned, so refusing it relocates the defect into a
document that emits.

This makes one `__init__.py` carry content where the others are markers. That is the cost, and
it is a smaller one than an unimportable module: `emit.relative_module`'s hop arithmetic has to
agree with it, which is a check a test can hold.

**What the report prints, 2026-10-26, with the pair's retirement REVERSED 2026-10-30.** It
printed `emitted N / refused M (deferred …, verdict …)`, and the 2026-10-26 reading retired that
pair on the ground that "`M` goes to zero over this bundle and the pair stops partitioning
anything", and `M` did go to zero. **The pair is not a partition and was never doing that work —
it is the KIND split, and the kind is what names who owns a refusal.** `emitted N / population N` moves
one number when a document stops emitting and says nothing about which kind moved, so a reader
cannot tell a document the bundle broke from a row nobody has written — which is the confusion
that let `emitted + refused == 1054` read green over 385 documents waiting on unwritten rows. The
delivery report reads `emitted`, `refused` with its deferred/verdict split, `accounted`, and
primary/chained off `Refusal.kind`, never off a sentence and never summed; the replacement drops
the split, and dropping it narrows the report.

So the figures are these, each over its own denominator and never summed, by the semantics
document's §2:

- **`emitted N / refused M (deferred …, verdict …)`, with `accounted`** — kept, for the reason
  above. `population` is not printed beside it: `emitted` and `refused` already carry it, and a
  third number next to them invites exactly the sum the protocol forbids.
- **the round-trip failures, per pair and by name** — a pair where the class refuses a value the
  document admits, or where the dump is a value the document refuses. Printed whether or not the
  count is zero, so a reader sees the pin being met rather than inferring it from silence. **The
  four text-diff defect counts that stood here are deleted with the comparison (2026-10-30)**,
  along with the 1,086 facts over 155 pairs they were reporting: not one of them was a value any
  payload had demonstrated, and they were read as the SDK's correctness for weeks. What replaces
  them is not a count. It is **one row per graded pair, written to a FILE by the run** — document,
  pointer, and each check's verdict — because a figure that exists only in a terminal cannot be
  reviewed, and because a check that computed nothing shows up there as a blank column instead of
  as a pass.
- **`approximated K facts in D documents`**, split by attribution (ours / upstream), with the
  upstream half listing its issues. There is one kind now, WIDENED. `K` and `D` are
  different counts over different denominators and the report never adds them. Neither is
  pinned: both rise when a document starts emitting, and the semantics document's §9 forbids
  pinning a figure that moves with emission. The **ours** half is the one that ratchets down,
  and it is the figure a wave's exit condition reads (§14).

The drops and carries-nothing lines stay as today. An approximation is NOT one of them: a
carries-nothing line says a keyword constrained nothing, and an approximation says a keyword
constrained something the annotation does not carry. Printing them in one list would sum two
different things.

*Why the entry-point module matters structurally.* The double binding under `runpy` is the one
reason the present code carries `decide`, `bind` and `name_constraint` as callables on a
dataclass, keeps the composition reader in the renderer's module, and enforces an import rule
on the lowerings. With an entry point no lowering can name, a lowering imports `decide`
directly, the context carries data and not functions, and the import rule shrinks to the two
boundaries that are about design: no Pydantic in the walk, no walk in the verifier.

---

## 11. Layers: what each knows, what it may not, what crosses

| layer | modules | knows | may not know | crosses outward as |
| --- | --- | --- | --- | --- |
| declaration | `keywords.py`, `attribution.py` | positions, keywords, cells, descent, rungs; the upstream issue at a document, pointer and keyword | nodes, documents, types, text | `Cell`, `Issue` |
| refusal | `refusal.py` | the kinds, and that a document may have no accepted set | everything else | `Refusal` |
| source | `bundle.py` | files, paths, `$ref` URIs, edges, the record | kinds, cells' effects, types | raw mapping, `edges`, `record` |
| reading | `schema/nodes.py`, `schema/parse.py` | raw mapping → `Node`; admission; applied type; positions; pointers | the IR, Python types, text, the run | `Node` |
| decision | `lower/decide.py`, `lower/<kind>.py`, `lower/rules.py`, `lower/names.py`, `constraints.py` | `Node` → `Lowering`; the table's cells and rungs; the attributions; naming; the runtime's rule classes | mappings, text, the renderer, files, the run | `Module` |
| representation | `ir.py` | the declarations and `TypeRef` | text, pydantic, nodes | — |
| render | `render.py` | `Module` → text through the pinned model layer | `Node`, mappings, the table | text |
| run | `emit.py`, `__main__.py` | order, closure, files, the report | kinds, cells, nodes | files |
| verify | `verify/*` | emitted classes, the record, the rendered column | the walk, the IR, the renderer | reports |

The import graph is acyclic and the arrows point one way: `refusal ← keywords ← ir ← schema ←
lower ← emit`, `ir ← render ← emit`, `ir ← constraints ← lower`,
`{keywords, attribution} ← lower`, `keywords ← bundle ← emit`,
`{keywords, attribution, bundle} ← verify`. `attribution.py` is a leaf like `keywords.py`, which
is what lets both the walk and the verifier read it without either reading the other.

*It imports `codegen.refusal`, and "imports nothing of `codegen/`" was too strong
(2026-10-26).* §3 requires an attribution entry with no upstream issue to be a `BuildFailure`,
and that type lives in `refusal.py` — so this module cannot satisfy the ban, the `BuildFailure`
rule and the `MAY_RAISE` ratchet at once. The row that built it wrote the alternative first, a
local `MissingIssue`, and that reddened the ratchet, which is how the clash was found rather
than argued. `refusal.py` imports nothing itself, so a leaf importing a leaf keeps the property
the ban was protecting: one module reached, and no module of the walk. The rule is therefore
*imports no module of the walk*, and `refusal` is named as the one thing it may reach.

**`refusal` is imported by `bundle`, `emit` and `attribution`, and by nothing in `lower/`**
once step 10 lands: the lowering seam is total then, so a handler has no refusal to name. Until
it does, `lower/` still names `Refusal` at 141 sites, which step 8's own note explains.

Four AST tests hold the graph, where there were three: no
`pydantic`/`datamodel_code_generator` import outside `render.py` and `verify/`; no
`codegen.{schema,lower,ir,render,emit}` import inside `verify/`; no
`codegen.{render,emit,verify}` import inside `schema/` or `lower/`; and **no `raise` of anything
but `BuildFailure` inside `schema/` or `lower/`**. The fourth is new and it is the test that
replaces the type-system guarantee §2 gave up: with one inhabitant at the seam the type checker
can no longer force a handler to answer for the other branch, so the thing it was preventing — a
node reaching no outcome — is prevented by banning the only other way out.

**Nothing repeats: where each of today's repetitions has one owner.**

| repeated today | one owner |
| --- | --- |
| three descent tables (`bundle.nodes`, `harness._nodes`, the walk's implicit descent) | the table's `descends` column, read by `parse`, `bundle.edges`, `verify/record.py` |
| keyword screens with a hand-written set at every lowering | admission in `parse`, from the table |
| the kind read in `lower.decide.decide`, in the root selectors, in `union.keyword`, in `rules.presence_only` | `parse`'s classification |
| the annotation set, the rule-keyword set, the constraint spelling in three modules | rows of the table; `constraints.SPELLING` keeps the alias WORD per keyword, which is a naming fact and not a decision |
| the applied type (`constrained_to_object`, `object_constrained`, `applied_type`) | `Node.applied`, set by `parse` through `applied_schema`'s rule |
| node rewrites (key schema, extras store, multi-type members, `uniqueItems` stripped before the array row) | positions and node fields: `Mapping.key` at KEY, `Object.extras`, `MultiType.members`, `Array.distinct` |
| name derivation at six call sites | `lower/names.py` |
| text produced in the walk (rule tuples, body lines, union trailers, root bindings) | `ir.py` declarations, written by `render.py` |
| the compared set in the verifier beside the handled sets in the walk | the table's `rendered` column |
| the kind of a refusal at every raise site | `Refusal`'s constructors, and `bundle.record` is the one site |
| the resolver's canonicalisation and its inverse folds | `bundle.record`, with no inverse |
| the rung a handler widens to, chosen where it widens | the cell's `widens_to`, read by `approximate` |
| the upstream issue for a widening, written as prose in a comment | `attribution.py`, keyed by document, pointer and keyword |
| the exempted facts listed once per check that strikes them | still two lists, and deliberately: `attribution.py` holds why a MODEL says less than its document, `verify/exemptions.py` holds which DUMP facts a check strikes. One registry for both would sum two different things |

What stays two by design: the intersection rule, once in `lower/composition.py` for the model
and once in `verify/compare.py` for the document (§9 says why); the `applied_schema` rule,
once in the runtime and read by the parser rather than restated.

---

## 12. What stands and what changes

The reviews are the evidence for the present state; this section says what this structure
keeps of it and what it replaces, so the two can be read as one judgement.

**Kept, because it is correct.** The spine — a document read, a decision, a declaration,
a rendering through the pinned model layer, no post-processing, every class carrying
`__adcp_schema__` and the record written beside it. The runtime package in full. The constraint
naming rule and the one public constraints module. The refusal that names document, pointer
and keyword with a kind that is an argument and not a reading of English — kept, with the
argument now derived. The verifier's three checks, its both-sides normalisation, and its
refusal to share the walk's reading. The content dedup, the on-demand `definitions` entry, the
cross-document import derived from two paths, the dependency-ordered transitive emission. The
semantics of composition (intersection, the requiredness overlay, the reused inherited field),
of union dispatch (derived from the branches, three sources), and of every keyword row the code
already implements faithfully.

**Replaced, because the evidence says the case is not right there.** The reviews' first
finding — one declaration missing, with the admission, the lowering and the grading as three
hand-written copies of it — is answered by `keywords.py` and its four readers (§3). The absence
of a position type, with position recovered from pointer strings and nodes rewritten to reach
the right screen, is answered by the parser assigning positions and building typed nodes (§4).
The root dispatch table beside the node dispatch is removed: one path (§5). The decision and
the rendering sharing one module and one mutable object is answered by a complete IR and one
renderer (§7, §8). The import graph following the entry point's double binding is answered by
`codegen/__main__.py` and a context that carries data (§10). The delegated resolver and its
inverse folds are answered by `bundle.record` (§4, §9). The kind of a refusal chosen at the
raise site is answered by deriving it from the cell (§3).

**Replaced by the owner's directive of 2026-10-26, which is a change of PRODUCT and not of
evidence.** The refusal as the outcome of a keyword nobody has compiled is replaced by the
widening and the approximation declaration (§2, §3, §6, §7). The sum type at the lowering seam
collapses to one inhabitant and the guarantee it carried moves to an import-rule test (§2, §11).
`Effect.REFUSE` and `Kind.DEFERRED` retire (§3). The verifier gains
two set equalities, and reads a declaration off the emitted class rather than off the walk (§7,
§9). The report's `emitted / refused` pair becomes three figures over three denominators (§10).
None of this is answering a review finding; it is answering a decision, and the reviews' own
findings are unaffected by it — which is worth saying, because a restructure and a product change
landing in one document is how each gets blamed for the other's cost.

This is a restructure of `codegen/` rather than an adjustment of it: `compiler.py` and
`emit.py` dissolve into `schema/`, `lower/`, `ir.py`, `render.py`, `emit.py` and
`__main__.py`; `harness.py` and `dump_exemptions.py` become `verify/`. The emitted tree is the
same tree, and the migration path in §14 orders the steps so that most of them are checked by
regenerating it and comparing bytes.

---

## 13. Where the semantics document forces a structure this document decides differently

Each item names the sentence, the structure it forces as written, and what this document
decides instead. The owner of the semantics document decides each.

1. **§3, "What the walk reads … is one document", the inlined one.** Read literally, the walk
   reads the record and so never sees a cross-document `$ref`; §5's `$ref` row needs the walk
   to see the reference in order to emit an import. This document has the walk read the raw
   document and the verifier read the record. The two agree at every node the walk lowers,
   because inlining changes nothing else — which is what §3's sentence is protecting. The
   proposed wording: the walk reads the bundle's document; `strict_validate` and §8 read its
   record; the record differs from it only where a reference is inlined unchanged.

2. **§3, "nothing else changed", beside §5's "an annotation sibling of `$ref` → the sibling's
   description wins".** The record has to say what an inlined node looks like when the
   referring node carries a `description`. This document keeps the referring node's annotation
   keys beside the copy, with the referring node's value winning; the alternative — dropping
   them — drops a key, which §3 forbids. The owner confirms the reading.

   **Settled 2026-10-25, and it extends only to ANNOTATION siblings.** A CONSTRAINING sibling
   is a different case and the owner has decided it in §5's `$ref` row: draft-07 ignores every
   sibling of `$ref`, so letting the referring node's value win would have the inliner decide
   an acceptance fact the bundle's own draft does not hold — which is the canonicalisation §3
   exists to forbid, and §9's "do not decide a position the bundle does not hold from a view of
   it". So the copy is placed, the sibling's key is KEPT in the record (§3 drops none), the
   sibling compiles to nothing, and the run reports it. An annotation sibling has no such
   conflict, because an annotation states nothing about acceptance and so cannot disagree with
   the draft. What makes this expressible without a second copy of the rule is the cell: the
   keyword's row says NOTHING and `rendered=False` at a `$ref` co-occurrence, so the record
   carries the key, no check grades it, and no handler holds a set of
   "keywords that are inert beside a `$ref`".

3. **§8, "a branch class is paired with its branch node read under the root's siblings", and
   §9, "do not decide a position the bundle does not hold from a view of it".** The pairing
   needs `applied_schema` to conjoin the root's `properties`, `required`,
   `additionalProperties` and `allOf` into a branch node, where today it conjoins `type`
   alone. This document extends `applied_schema` in `_base.py` to every same-instance keyword
   §5's union row compiles onto the base, and reads the result as draft-07's own semantics
   applied at a pointer the document holds rather than as a view. If the owner reads it as a
   view, the union row's "fields on the base, inherited by every branch" has no gradable
   pairing and the row has to change instead.

4. **§3, "`Refusal` lives in the package every lowering imports, so any step can raise one".**
   The structure returns a refusal and never raises one (§2). The sentence's reason — one
   module, one class, no import cycle — holds unchanged; "raise" becomes "return".

   **Settled and then superseded, 2026-10-26.** No lowering imports `Refusal` at all now: the
   seam is total and the only producer is `bundle.record`. The semantics document's §3 says so
   directly, so this item is closed — not by the owner conceding the wording, but by the
   directive removing the thing the wording was about.

5. **§2's refusal kinds, counted separately.** The semantics document names two kinds and
   describes a third in §9 (a chained target). The structure derives the kind from the table's
   cell rather than taking it as an argument, which the document does not forbid and does not
   state. UNRESOLVED, which the code carries today, is not in the document and is retired by
   the resolver in §4.

   **Closed 2026-10-26.** The directive leaves one resolved kind — VERDICT, for a document with
   no accepted set — and CHAINED delegating to it from `bundle.record`. DEFERRED retires with
   the outcome it named, and the semantics document's §9 states the replacement rule ("code
   nobody has written is an APPROXIMATION, never a refusal"). There are no longer two kinds to
   count separately, so the item has nothing left to disagree about; what the rule became is
   that the three APPROXIMATION figures are never summed (§10).

6. **§8's diff test is replaced by generation, and §8 now says so.** Markdown is not a machine
   source for a cell's meaning, and a membership diff admits a cell that decides one thing beside
   a sentence saying another. The grids of §5, §6 and §7 are generated from the table instead, so
   the second copy of the what does not exist to drift. The reasoning paragraphs stay hand-written
   and are the part a reader must keep honest against the cells.

7. **§4 "Names", a branch with no identity.** The present code refuses it as a VERDICT, and
   this document keeps that, since §4 gives no fourth rule. The untitled `enum` branch of a root
   union whose only other branch is a constrained string is the case that reaches it, and it
   needs a naming rule in §4 or stays refused.

   **Closed 2026-10-26: §4 now has the fourth rule.** A branch with no title, no pinned `const`
   and no `required` set takes its index among the branches, `<Base>Branch<i>`. A name is not an
   acceptance fact, so the fallback neither widens nor narrows and costs no approximation, and
   the index is a function of document order, so it does not depend on which documents the run
   includes. The same reasoning gives a missing or non-identifier root title the document's own
   file stem, which closes the other half of the refusal.

---

## 14. Migration path

Each step can be taken alone, is checked by a test that exists or is named, and says whether
the emitted tree or the report changes. Steps marked *bytes* are checked by regenerating the
tree and comparing it byte for byte with the committed one.

**What a *bytes* mark forbids, and what it does not (2026-10-26).** It exists to prove a step
is a RELOCATION and not a decision, so what it forbids is an UNDECLARED change: text that moved
because the step chose something, with no sentence in either document behind the choice. It does
not forbid fixing a defect the semantics document has already decided. Where a step's correct
implementation makes the emitted tree conform to a sentence it was violating, the tree moves,
and the step reports the change with the document, the pointer and the sentence that decides
it — enumerated, never aggregated.

The two cases are told apart by asking what is on the other side of the trade. Step 4 met a
rendering whose spelling no sentence decides — keyword against positional arguments to a frozen
dataclass, the same object either way — so *bytes* won and §7 gave up the word `repr`. Step 5
meets `enum.decide` reading `enumDescriptions` alone while §6 of the semantics document says
"two spellings of one keyword; both are read", so `enums/signal-value-type.json` emits with no
member docstrings. That is a defect against a decided sentence, the fix changes one module where
a document emitted before, and the fix wins. A gate that forbade it would be pinning the defect.

**What the owner's directive does to this sequence (2026-10-26).** It does not reorder steps 1
to 7, which are relocations the directive does not touch, and step 7 stays next because every
step after it needs the module pass and the dependency order. It **splits step 8 into three**,
and the split is forced rather than tidy: *the instrument has to exist before the first cell
widens.* A cell that widens while no draw yet reaches the values the keyword distinguishes
produces a flood the pin cannot survive, and the project then either abandons the pin or stops
believing the grader — which is the semantics document's §8 failure mode, reached on the first
commit. So step 8 becomes the approximation end to end with **no cell widened**, step 9 is the
rows the directive makes FAITHFUL (which need no approximation at all and are the larger half),
and step 10 is the rows that genuinely widen. The waves then follow with a changed exit
condition, below.

1. **`codegen/__main__.py`.** Move `main` there; `python -m codegen` is the command. Delete the
   `__main__` re-entry in `emit.py`, the `decide`/`bind`/`name_constraint` callables on
   `Module` (lowerings import `decide` and `constraints.resolve` directly), and the lazy
   imports that existed for the cycle. Narrow `tests/test_import_rule.py` to the two design
   boundaries (§8, §9). *Bytes.* Unblocks every later move of a function between modules.

2. **`codegen/keywords.py` and its first two readers.** Declare `Position`, `Cell`, `Row`,
   `TABLE`. Make `check_keywords` read the table at a position its callers pass (the position
   is known at every call site today, as a structural fact of the caller). Derive the
   verifier's compared set from the rendered column. Derive the kind of every refusal minted by
   `check_keywords` from the cell. Add `tests/test_keywords.py` (§3). *Report changes:* the
   keywords the semantics document renders and the verifier does not compare today start being
   compared, and refusals minted as verdicts for cells the document decides re-mint as
   deferrals. *Tree unchanged.* Unblocks every cell fix after it, because a cell is then
   written once.

3. **`bundle.record`.** Replace the delegated resolver with this package's inliner (§4) for the
   packaged documents and for the verifier; keep the delegated resolver inside
   `verify/accepts.py` for drawing. Delete the inverse folds in the verifier. Regenerate the
   packaged documents. *Report changes:* every packaged `.json` changes where a target was
   canonicalised; a new round-trip failure is a real finding and not a fold's absence.
   *Modules unchanged.* Unblocks the verifier being a reader of the document and nothing else.

4. **`codegen/ir.py` and `codegen/render.py`.** Move `Type`, `Property`, `Class`,
   `Enumeration`, `Member` and the `render*` functions out of `compiler.py`; replace
   `body_lines`, `rules.block` text, the union trailer and the root-binding text with
   `ClassDecl.rules` (runtime dataclasses), `UnionInstall` and `RootBinding`; make `Module` a
   value with `declarations` and let `render.py` write every string. Add the Pydantic import
   ban test. *Bytes.* Unblocks §7 and §8; the decision layer no longer imports the model
   layer.

5. **`codegen/schema/`.** Declare the node kinds and write `parse`, with positions, the applied
   type and admission from the table. Rewrite each handler to take its node: `lower_object`,
   `lower_composition`, the containers, the union, the enum and const rows become
   `lower/<kind>.py`, and `decide` becomes the exhaustive match. Remove the three node
   rewrites and `object_constrained`, `content_key`, the HANDLED sets and the root selectors in
   `bundle.py`. *Report changes:* a refusal's keyword and pointer may move to the node that
   carries it where today they name a rewritten node; the key-schema union and the empty-schema
   `additionalProperties` on a class stop refusing or crashing. *Tree unchanged where a
   document emitted before.* Unblocks §5 and §6 in full.

   *How the conversion is STAGED, settled 2026-10-26 after two attempts measured the surface.*
   The end state above is not negotiable: `parse` is the only reader of a raw mapping, and a
   handler reads node fields. But the conversion to it is not one commit's worth of work — the
   surface is 11 screen sites, 7 descent sites, roughly 2,100 lines of handler code and 32 test
   call sites, all under a byte-exact check over the emitted tree. Two attempts each read the
   gate as making the whole conversion atomic, landed valuable adjacent work, and stopped.

   It is not atomic, and the reason is that §4's rule is about the WALK and not about field
   access. "One parser is the one reading" forbids a second traversal of the raw document; it
   does not forbid a half-migrated handler being handed the mapping its own node was built
   from. So during this step a node may carry its originating mapping, `parse` performs the one
   traversal, and each handler converts to node fields one kind at a time — each conversion its
   own commit, each checked by the byte compare. **The step is not complete until that carrier
   is deleted**, and its deletion is the step's last commit: a tree that still has it has not
   finished step 5, and no later step may read it. Staging a refactor is not the same as
   softening its end state.

   *The refusal ORDER is document order, and that settles what this step owes the old report
   (2026-10-26).* The first attempt at this step stalled on trying to reproduce the sequence six
   handlers happen to screen in — `lower_composition` checking `type` before its screen,
   `union.ROOT_CLAIMS` claiming four keywords so its own refusal reports after them — and
   concluded the parser could not be written without preserving all six. It does not owe them
   that. §2 and §6 both state the rule: `first_refusal` returns the earliest refusal in DOCUMENT
   order, "which keeps the report a function of the document and not of the walk's iteration".
   The present sequence IS the walk's iteration, and it is what this step exists to remove.

   So where a refusal moves because document order puts a different node first, that is this
   step's "report changes" and not a regression. What must NOT change is which documents refuse
   and with which `resolved` kind; the pointer and keyword within a refused document may move to
   the node document order reaches first. Measure both: the refused SET with its kinds, which
   holds, and the moved pointers, which are enumerated and explained.

6. **Refusal as a value.** `Refusal` stops subclassing `Exception`; every handler returns
   `Lowering | Refusal`; `first_refusal` replaces the try/except in `lower_document`;
   `lower_document` returns a value to the run. The type checker is the test. *No change in
   outcomes.* Unblocks §2's totality.

   *Done, and step 8 takes the second half of it (2026-10-26).* This step made the seam a sum
   type, which is what made the next move possible: a seam that raises cannot be collapsed,
   because there is no inhabitant to collapse to. Step 8 collapses the sum to `Lowering` alone.
   The intermediate state is not wasted work — the sum type is what turns every present
   deferral into a compile error the moment `Refusal` leaves the seam, which is how step 8
   finds them all.

7. **`lower/names.py` and the dependency-ordered run.** Move naming and dedup into the pass
   over the module; compute `edges`, the closure and the order in `emit.py` and pass `targets`
   through the context; delete the binder closure and `inflight`. *Bytes*
   for the modules; the report's refusal order may change and must stay sorted by document.
   Completes §6, §7 and §10.

   *This said "delete … `resolving` on `Module`" and that does not follow, corrected 2026-10-26.*
   The dependency order is over DOCUMENTS; `resolving` guards a LOCAL cycle inside one document,
   so computing the order retires nothing about it. §6 — settled the same day — gives
   `ctx.resolving` an explicit job as a forward-reference marker rather than a refusal trigger, so
   the step as written would have deleted a field two other sections rely on. It stays, as data.
   The step's real content is that no CALLABLE survives on the context, and that is what the row
   delivered.

   *What the run WRITES is the set it owes, not the static closure (settled 2026-10-26).* §10's
   justification is that a module cannot import from a module no run wrote. The static closure of
   every `$ref` satisfies that and overshoots it: measured over the 991-document population, it
   writes 11 modules nothing imports and nobody named, and adds two aliases to the public
   `constraints.py`. So the run writes the documents it was named plus what an attempted lowering
   actually referenced, as a fixed point over `Module.asked` — which satisfies §10's sentence
   exactly, because every import resolves and nothing else is written. The closure is still what
   the ORDER is computed over; it is not what the run emits.

8. **The approximation, end to end, with no cell widened.** The instrument before the change.
   Add `Rung` and `widens_to` to the cell and retire `Effect.REFUSE`; add `Approximation` and
   `RootModelDecl` to the IR and `approximations` to `Lowering` and `Module`; add
   `codegen/attribution.py` and its no-issue-is-a-`BuildFailure` test; make `render.py` write
   `__adcp_approximations__`; add the
   accepts obligation over a dropped keyword's classes and the
   report's three figures. Add the fourth import-rule test (§11). *Exit condition: every count
   unchanged — the same documents emit, the same documents refuse — with `APPROXIMATED` 0 and
   `OVER_DECLARED` 0.* The tree changes by one line per module (`__adcp_approximations__ = ()`),
   which is a declared text delta and not a decision. **Nothing else in the directive may land
   before this step passes.**

   *The seam collapse is NOT in this step, corrected 2026-10-26.* This step originally also said
   "collapse the lowering seam to `Lowering` and retire `Kind.DEFERRED`, which is what makes every
   present deferral a compile error until its handler calls `approximate`". That cannot hold
   beside this step's own exit condition, and the row proved it by measurement rather than
   argument: `approximate` reads the rung off the cell, a `None` rung is a `BuildFailure`, and of
   the **141 primary refusals exactly 1 sits on an `Effect.REFUSE` cell** — so 140 have no rung
   yet. A total seam today therefore either widens those cells, which moves the counts this step
   forbids moving, or crashes the run on 140 documents. The two sentences were written in one
   step and only one of them can be true at a time.

   So the seam stays a sum type until the last cell has a rung, which is **step 10**, and
   `Kind.DEFERRED` retires with it. The instrument is complete without the collapse: the rung
   field, the declaration, the registry, the two outcomes and both equalities all exist and are
   proved here, and the fourth import-rule test passes unchanged. What the collapse buys —
   turning every remaining deferral into a compile error — is worth having exactly when there is
   a rung for each one to reach, and not before.

9. **The faithful rows.** The rows the directive forces to a FAITHFUL answer rather than to an
   approximation, which is the larger half of the refused set and costs no declaration at all:
   root siblings onto a union base (and the `applied_schema` extension of §13 item 3); a scalar,
   enum, container or union target as the type of a composing node; the root model, which brings
   root arrays, `uniqueItems` and `contains` at a root array, and the mixed root union; a
   `Literal` or `StrEnum` key for `propertyNames`/`enum` at KEY; `format` beside a string
   constraint keeping both halves; a local `$ref` cycle as a forward reference; a bare-`$ref`
   root as a subclass or an identity binding; a root stating only `if`/`then` as a root model
   with the conditional as a rule; the fallback names for a missing title and an identity-less
   branch; a union whose branches differ only in their pinned values as one class and one rule;
   the manifest dispatch source. *Exit condition: `APPROXIMATED` still 0, the four defect counts
   still 0, and the refused set down to the rows step 10 owns.* Each one moves refusals to
   emissions and is graded by the verifier at the pairs it unblocks.

10. **The widened rows.** What is left, each with the rung and attribution the semantics
    document's §5 states: an `allOf` restatement whose intersection is not computable; an empty
    intersection; a union whose branches cannot be separated; a `contains`
    predicate no `AtLeastOne` carries; a keyword with no row; a list-valued `items`; a root
    stating no schema keyword.

    *One more case, added 2026-10-27, because `refused == 0` had no answer for it.* **A `$ref`
    conjunct whose target is NOT a class, beside a node that declares fields of its own.** §5's
    `$ref` row at CONJ says the target becomes this node's own TYPE where it is a scalar, an
    enum, a container or a union root — and that clause is scoped, in its own words, to "a node
    that declares no fields of its own". These nodes declare some, so the node is at once a class
    (it has fields) and a type (the target), and §5 answers neither. Row `.20` found it by
    landing the bare-`$ref` root and reported it rather than choosing; measured at **3 documents**,
    all verdicts, all on `allOf`: `core/package-signal-targeting.json`,
    `core/product-filters.json`, `core/vendor-pricing-option.json`.

    It is a WIDENED row and not a faithful one. Carrying it faithfully means the instance must
    satisfy the node's fields AND one of the target union's branches, and "also satisfies this
    imported union" is not one of §2's rule families — adding one is a larger decision than this
    case earns at three sites. So the conjunct's union membership is DROPPED, the class emits
    with its own fields, and the gap is declared. The widening is safe in the usual way:
    `strict_validate` still enforces the union from the document, so only the annotation loosens.

    *The upstream issues do NOT block this step, corrected 2026-10-26.* This said they must be
    filed first, because `attribution.py` admits no entry without a reference. That makes the
    compiler's own completion wait on a third party's issue tracker, and the thing being built
    is a compiler that represents every schema — it cannot have an external calendar in its exit
    condition.

    So the gate moves off the step and onto the WORD "upstream". Every approximation is
    attributed, and an attribution is OURS until an issue exists: `Attribution.ours(reason)` needs
    no reference and says in one sentence what the schema would have to state for the gap to
    close. Only `Attribution.upstream(issue)` requires a live reference, and that constructor
    keeps its `BuildFailure` — so nothing is ever *claimed* as upstream without a filed issue,
    which is the honesty property the original gate was protecting. Filing an issue later
    reclassifies the attribution from ours to upstream and the *ours* backlog falls by that much;
    it does not change a type or an emission.

    What this costs: the *ours* figure reads higher until the issues are filed, which is correct
    — an unfiled gap IS ours. What it buys: `refused == 0` is reachable without waiting on
    anyone outside this repository.

    **The seam collapse lands here, moved from step 8 on 2026-10-26.** Once this step has given
    every reachable cell a rung, `decide` collapses to `Lowering`, `Refusal` narrows to its one
    producer in `bundle.record`, and `Kind.DEFERRED` retires — which is what turns any remaining
    deferral into a compile error rather than a report line. It belongs at the end rather than
    the beginning for the reason step 8 records: a total seam over cells with no rung is a
    `BuildFailure` on every one of them, and 140 of 141 primary refusal sites were in that state
    when the instrument was built. The collapse is the *consequence* of the rungs being complete,
    not the mechanism that completes them.

    *Exit condition: `refused` is 0 over the portable population, `decide` returns `Lowering`,
    `Kind.DEFERRED` is gone, `APPROXIMATED` equals the declared set in both directions, and every
    upstream attribution names a live issue.*

**Then the waves, with a changed exit condition and an unknown order.** A wave's exit condition
was "these keywords stop refusing documents". After step 10 no keyword refuses anything, so the
condition becomes **"these keywords' OURS approximations reach 0"** — the upstream half is not a
wave's to close. And the wave ORDER has to be re-measured, not carried over: the waves were
ordered by how many documents each keyword set *completes*, and after step 10 every document is
complete, so the ordering quantity no longer exists. The new quantity is how many *approximated
facts* a wave's keywords close, which is a different number over a different denominator and
will not produce the same order. The upstream half is not a wave at all; it is the issue list,
and it closes when upstream closes.

**NO STEP OF THIS SECTION OWNS THE CONSUMER SURFACE, and that is deliberate rather than an
omission (decided 2026-10-30).** `src/adcp/types/__init__.py` used to say its public surface was
"generated from the binding table in step 9". Step 9 has landed, it owns no binding table, and
**nothing anywhere owns one** — `codegen/emit.py` says so in as many words. The question that
docstring was answering is a real one and this section is the wrong place for it: §14 is the
COMPILER's migration path, and every step here is checked against the emitted tree or the report.
What a domain module exports is not a property of the compiler's internals; it is the artifact a
consumer imports, so it is graded by census against that artifact and not by a step's *bytes*
mark. `docs/plan/surface-goal.md` owns that goal, `docs/plan/unimplemented.md` A-2 owns the gap,
and the row is P4-09.

That boundary is why the compiler reaching `refused 0` did not deliver a usable SDK, and saying it
here is cheaper than rediscovering it: a reader who looks for the consumer surface among these
steps will not find it, and the honest answer is that it was never one of them.
