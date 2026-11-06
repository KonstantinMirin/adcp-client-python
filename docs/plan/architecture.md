# The compiler's structure: layers, the one dispatch, and what crosses each seam

`docs/plan/rebuild-plan.md` decides the semantics: what each keyword compiles to at each
position, which keywords are admitted, which refuse, and how the output is graded. This
document decides the structure that carries those semantics: the layers, the seam between
each pair of them, the one place a node's kind is decided, the data that crosses every
boundary, the paradigm, and what is derived from what. Where the two overlap, the semantics
document governs the meaning of a keyword and this one governs where that meaning is written
down and who reads it; §13 names the places where its wording forces a structure this
document decides differently, and the owner of the semantics decides those.

No site counts appear here.

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
  fact, which structural keywords descend into which position, and **which widening in §2's chain
  the keyword widens to where the handler cannot render it**.
- `codegen/attribution.py` — the one registry of site-level upstream
  issues, keyed by document, pointer and keyword. A second declaration module beside
  `keywords.py` and a leaf like it, read by `lower/` to attribute an approximation and by
  `verify/` to grade one. It is a declaration and not a verifier artifact, which is why it is
  here and not under `verify/`: a keyword-level decision lives in a cell, a site-level one lives
  here, and nothing else holds either.
- `codegen/refusal.py` — the one refusal type, a value and not an exception, **minted only
  by `bundle.record`**.

And one package that reads the output and the record but never the walk:
`codegen/verify/`, which is `harness.py` and `dump_exemptions.py`.

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
  The three places a walk would rewrite a node — the key schema given a `type` word, the
  extras store rebuilt as a mapping, a multi-type node cut into one member per type — are
  readings the parser makes once, at the position that implies them (§4).
- **Total functions from node to decision.** `decide(node, ctx)` returns `Lowering`, and
  nothing else. The semantics document's §2 collapsed the seam: a keyword a handler cannot
  render widens the annotation and declares an approximation, so no node is ever without a
  lowering and the union has one inhabitant.
 **The type-system guarantee that collapse gives up is replaced by a test, never merely
  dropped.** A sum type makes a caller that reads a `Lowering` field without handling the other
  branch a type error, which is the mechanical form of §9's "a crash is not an outcome". With
  one inhabitant there is no branch to force, so the obligation moves into each handler: a
  handler's match over the cases of its own node is total, its final case calls
  `approximate(node, keyword)`, and **no handler raises**. The import-rule tests carry the third
  boundary that holds it (§11), and §8 of the semantics document carries the two equalities that
  catch a widening nobody declared.
- **Composition by explicit combinators.** `Lowering` composes with `+`: a parent's declarations
  are its own followed by its children's, its imports the union, its approximations and its
  reports the concatenation. **The algebra is ADDITIVE, not absorbing.** A refusal was an
  absorbing element — anything composed with one was that one, which is how a child's refusal
  killed a document — and an approximation is additive: composition is total, the parent always
  gets a `Lowering`, and what travels upward is accumulated rather than propagated. So
  `first_refusal(results)` has exactly one caller, in
  `bundle.record`, where it returns the earliest refusal in document order over the
  references the inliner could not resolve. Its contract is unchanged; its subject is the
  record and not the walk.
- **Effects at the two ends.** `bundle.py` reads files. `emit.py` writes files and prints the
  report. Nothing between them touches a file, an environment variable, a clock or a global.
  The run's own state — which documents are lowered, which refused — is a fold in `emit.py`
  over a dependency order computed before any document is lowered (§10), so no handler ever
  calls back into the run.

**What becomes of the exception-based refusal.** `Refusal` stays in `codegen/refusal.py` and
does not subclass `Exception`. The one `try` left in the compiler is around nothing: a defect in
the compiler itself — two selectors claiming one node, two constraints deriving one alias name —
stays an exception (`BuildFailure`) that no layer catches, because it is not an outcome of any
document and the run must stop on it.

**`Refusal` has one producer and one meaning:** `bundle.record` could not build a document of
record, because a `$ref`'s target is not a bundle document or because two documents reference
each other in a cycle. `emit` is its only reader. Three consequences, each mechanical:

- **`Kind.DEFERRED` retires.** It meant "the lowering for this position has not been written",
  and unwritten code produces an approximation and not a refusal, so the
  kind has no instance left to name. The semantics document's §9 states the replacement rule,
  and `is_a_verdict` becomes a question with one answer.
- **`Kind.CHAINED` survives, and moves.** A document whose reference target has no record has no
  record either, so the inliner refuses CHAINED `through=` the target's refusal and
  `Refusal.resolved` keeps its meaning. It is minted inside
  `bundle.record`, not at the reference's lowering, because a reference the walk can see is one
  the record already inlined.
- **`Kind.VERDICT` is the only resolved kind.** With DEFERRED gone and CHAINED delegating,
  `RESOLVED_KINDS` has one member, and the figure the exit condition reads is the count of
  refused documents. The enum stays an enum rather than collapsing into a boolean: a bundle that
  grows a case neither kind covers needs somewhere to put it, and the cost of keeping the type
  is nothing.

**The handler's own obligation.** `approximate(node, keyword)` is to an approximation what
`Refusal`'s constructors were to a kind: the ONE place a widening is minted, reading the widening off
the cell (§3). A handler never chooses a widening and never writes an attribution: a
decision made at the site that needs it is a decision
nobody can audit against the table that was supposed to hold it.

---

### Where the walk's per-node entry lives

§11's table does not say, and it is the question that
keeps `lower_node` in `compiler.py`. It cannot go in `lower/names.py`: that module is a leaf of the
decision layer, and hosting the entry would make it the hub every handler recurses through and need
a second deferred import to break a second cycle. It cannot go in `lower/decide.py` either —
`decide.py` imports the handlers, so a handler recursing through it is a module cycle rather than a
deferred edge.

**It goes where the CARRIERS go.** Both the dispatch and the handlers need the entry and neither
owns it. What makes `compiler.py` the wrong home is that it also holds `Module`, `Case`, `Target`
and `Decided`. `Decided` is `ir.py`'s. As the rest follow, the entry is a thin module importing
`ir` and `decide`, with the handlers importing `ir` alone — and §11's table carries the row naming
that module and the one direction its arrow runs.

**And the seam collapse lands after §8's equalities are green.** A conversion at a position no
portable document reaches is invisible to `./check`, invisible to the byte compare, and invisible
to the equality that would catch the first document to reach one; run after, each lands against a
green equality. **The collapse also cannot be sized up front:** collapsing the dispatch alone
leaves the handlers answering the sum type, so the checker sees one ring at a time, and the figure
after each ring is the only honest estimate of the next.

### The drawn corpus is COMMITTED

**The payloads are kilobytes of content; drawing them costs minutes per pair.** In a gitignored
directory, a fresh checkout, a new worktree, a CI job and every key-space change redraw all of
them, and a held entry is the exception rather than the rule.

**The key is `bundle.source_identities`**: the document's own raw bytes, the raw bytes of its
reference closure, the example count, the format strategies and the generator version. **A
compiler edit moves nothing. Only a bundle bump does.** A key over `bundle.record` — our own
inlining — would be invalidated by any compiler edit, leaving a committed corpus permanently stale
behind a permanently red gate.

So the obligation is gradeable, and it is the gate that comes with the decision: **every graded
pair has a committed entry under the current key.** It
reddens exactly when a bundle bump or a generator bump lands without a redraw — which is a
deliberate, reviewable event and not an in-flight change — and `harness.corpus_defect` still
re-offers every held instance to the document on read, so a wrong entry cannot pass quietly.

What this buys: a payload is drawn **once per (document, draw version) in the project's history**,
not once per checkout per lane per key-space change. What it costs is a redraw step on a bundle
bump, which is the same discipline the packaged records already carry.

### The widening store's currency is the OBLIGATION, not a second gate

§8's widening obligation draws too, and those draws have a store of their own
in a separate key space and a separate directory. The accepts gate's case **does not transfer to
it**: `live_keys()` reads every
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
minted to record which keys the set asks for.** That artifact would need its own equality,
and that equality would need the same thing one level further out. Leaving the space cache-only is
also refused: the saving is real, crosses checkouts, and changes no verdict — it buys back the draw
and nothing else.

**AND "AS IT FILLS" IS NOT A DEFERRAL: A STORE THAT EVAPORATES ON CHECKOUT PROVES NOTHING.** The
proving values live in a
cross-worktree cache that a check requires to be *outside* the repository — correctly, because a
run may not write inside the checkout — so a fresh checkout and a CI job hold a
proving value for **no declaration at all**, and the half of reading 2 that says *every declaration
holds a value that demonstrates it* reads as unmet for every one of them. That is the same argument
that makes the accepts floor committed, and it applies here without modification. So the directory
is created and promoted the moment values exist for it, under two conditions reading 2 states
itself: **no entry records a budget cut**, and **every entry is a draw's own output** — never
written by hand, because a hand-written proof is an exemption the first time the document changes
under it.

**A RUN MAY NOT WRITE INSIDE THE CHECKOUT; A PROMOTION MAY.** That distinction is what lets both
rules hold at once, and it is already how the accepts floor works — the check forbidding a run to
write there is not a check against the floor existing.

A position whose draw never returns is held by nothing under any of these choices. That residue is
not a currency question. It is the document-derived construction decision.

### The wheel SHIPS `py.typed`, and the gate is the CONSUMER'S checker

The goal is an ergonomic, schema-faithful, DX-friendly SDK, and a typed SDK whose types are `Any`
to its consumer is none of the three. **So the marker ships.** Without it a consumer's checker
reports `Skipping analyzing "adcp.types.core": module is installed, but missing library stubs or
py.typed marker`, then `Revealed type is "Any"`, and a deliberate bug in the consumer's file passes
silently — so every ergonomic property the surface work establishes is invisible at the wheel
boundary.

**No internal-soundness precondition stands in front of it.** A checker running over a consumer's
code does not re-check the internals of an installed package; it reads the package's annotations
and reports errors in the consumer's own file. So the marker promises *"my annotations are usable
by your checker"*, which is exactly what the three-direction check decides, and it does not
promise *"my internals type-check"*.

**An internal error is therefore a defect we own and not a bar to shipping the marker.** Those
that sit in the GENERATED tree are a rendering defect by construction, fixed in `render.py` and
never in the tree, which §5 already settles: the committed tree is an artifact, verified by one
byte-compare, and is never the subject. The checker's scope names that exclusion explicitly rather
than omitting the directory, and the gate's own set reads the exclusion, so deleting it
pulls the whole tree in without anyone having to remember.

**The gate is the consumer's checker, not ours.** A file outside the package that misuses a field
and an enum member must FAIL a check against the installed wheel; green is both reported, by error
code. Checking our own tree proves nothing about this — the source tree is readable with or without
a marker.

### The suite's scratch goes on DISK, not in RAM

Where `/tmp` is a memory-backed filesystem, it is RAM. The suite materialises a fresh package per
`tmp_path`, and almost all of that tree is resolved JSON read through `importlib.resources`, so
at ten workers it lands in memory, and a full run can take the box to the edge of its RAM.

**So `TMPDIR` and pytest's `--basetemp` point at disk.** The scratch is large, write-once and read
back by a child process; none of that wants a memory-backed filesystem, and the one property RAM
buys — speed — is irrelevant beside a run that cannot finish.

Two readings go with it:

* **A memory figure written into a comment goes stale and is then believed.** Every such figure
  belongs in the row that measured it.
* **A finished lane's scratch is not free.** Orphaned directories from merged, torn-down lanes
  hold tmpfs with zero open handles. Scratch under a memory-backed path is a resource the
  orchestrator owns, and the discipline that applies to a worktree applies to it: check that
  nothing holds it, then remove it.

### The subject of grading is a FRESH EMIT, never the committed tree

The schema is pinned and the drawn instances are content-addressed, so what a class is graded
against is a function of the bundle and the compiler alone. **Grading therefore reads the tree a
fresh run emits. The committed tree is an ARTIFACT, verified by one byte-compare, and is never the
subject.**

A grading path that does `import adcp.types._schemas` and walks it puts a committed artifact in
the grading path: a census over it grades a mixture of two compilers, and a parametrize-time
import means a single unimportable module errors every test in the file.

Regenerate, then grade. The order is the whole rule: a change to the compiler is followed by a
regeneration and the grading reads that, so a stale tree cannot be graded and a tree that does not
build fails one named test instead of disabling the file.

The instruments exist. `tests/compiled.py` returns the fresh emit in under a second warm, keyed on
the compiler's own source, and `tests/_imports_a_tree.py` writes a fresh tree to a
temporary directory and imports it in a child process — the child being forced rather than
convenient, because an emitted module imports `adcp.types.constraints` by ABSOLUTE name and a
fresh tree imported in the suite's own interpreter resolves its aliases through the committed
alias module.

**`tests/fresh.py` is where a reader's BUNDLE-DERIVED constants live**, beside
`BUNDLE` and `TREE` which are already there. A reader that needs to ask the emitter where a
document's module sits needs `bundle.package_roots` — a function of the bundle and never of the
run, which is what makes it a constant rather than an argument. The alternative is threading one
more parameter through every call site to carry a value none of them varies. One place holds it and
the readers import it.

### A check may not be downstream of its own precondition

**A check whose precondition is the thing it checks is not a check.** The obligation that an
emitted tree builds ranges
over the tree a fresh run EMITS, not the one committed, and it lives outside the module whose
collection it would gate. Both halves are required: fixing the set alone leaves it
uncollectable, and moving the file alone leaves it blind to anything not yet committed.

**And a base list naming one class twice RAISES.** §2 decides it — a refusal is the document's and
a broken invariant is ours — so this is the clause applied: nothing a document can state produces
a duplicate base, the reader of such a report would go to `codegen/`, and an exception at the
pointer is louder and honest where a refusal is quiet and wrong. The chokepoint is
`ir.ClassDecl`, because not every base list passes through `compiler.dispatching_bases`; a guard
there would hold two of the call sites and miss the rest.

**A CHECK THAT DIES IN ITS OWN SETUP IS THE SAME RULE REACHED A DIFFERENT WAY** — the check dies
before the line holding its claim. A check that dies before its assertion is indistinguishable
from a check that has nothing to report, and the suite's own failure summary spells them the same
way. The two are told apart only by reading the traceback for which LINE raised, so a red check is
not evidence that its subject is what failed. A check therefore builds nothing in a first loop that
can raise before the loop holding its assertion.

### An approximation's pointer is the SchemaRef spelling

`render.declared_at` attaches a declaration to a class by a prefix test, and its own docstring
fixes the rule: "the prefix test is on ONE spelling of a pointer — `SchemaRef`'s, which
`compiler.schema_ref` is the sole producer of". **An approximation declared at a different
spelling of the same node therefore attaches to the wrong class, or to none.**

The spellings differ across an `allOf` conjunct. A class's `SchemaRef` keeps the conjunct —
`#/anyOf/0/allOf/0/anyOf` — and a walk that writes the approximation at the node reached through
it writes `#/anyOf/0/anyOf`, which need not resolve in its own document even following `$ref` and
merging `allOf`.

**The approximation takes the `SchemaRef` spelling, because that is the one the reader of a
declaration uses.** §2 asks a declaration to be a fact §8 can look for in the document and
find; a pointer that resolves to nothing is not that. This is one producer and one spelling, as
`attribution.py` already says of the attribution it writes beside it, and it is also both
directions of the declared backlog's reading: a declared-but-separable site pairs with a silent
entry once the conjunct is elided — the same union counted twice under two spellings.

---

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
    widens_to: Widening | None  # the widening §2 of the semantics document drops to, where the
                            # handler cannot render this keyword here; None where the
                            # keyword states no fact and there is nothing to drop
    compiles: str           # the sentence the grid states for this keyword here

class Widening(StrEnum):        # §2's widening chain, lowest first; TOP always terminates
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

**`Effect.REFUSE` is not in the enum and `widens_to` is in the cell.** Both follow
from the semantics document's §2: no keyword's presence refuses a document, so there is no
effect for refusing; and a keyword the handler cannot render has to drop to one widening rather than
another, so something must say which.

*Why `widens_to` is a FIELD and not derived.* `effect`, `rendered` and `descends` do not
determine it. `uniqueItems` is RULE, rendered, non-descending and drops its keyword (KEYWORD);
a list-valued `items` is TYPE, rendered, descends to ELEM and drops to the union of its members
(JOIN); an unrowed key has no row at all and drops the node's whole type (TOP). Cells whose
other three fields agree take different widenings, which is the test of whether a field is needed.
It is `None` for a keyword that states no fact about an instance — `$comment`, `title`,
`errorMessage`, the registry data keys — because there is nothing to drop and a widening would be a
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
position renders its `compiles` as §6's "what it does, or why nothing". **§7's projection is the
empty one**, because `Effect.REFUSE` is gone and no row can be in it; the generator still
writes the region, and the region being empty is what makes "no keyword refuses" a fact the
document holds rather than a claim its prose makes. `errorMessage` and the registry data keys
are in §6's projection, where they belong: each is NOTHING at every position.

The table also carries the `x-` namespace rule
(§6 of the semantics document): a key with the prefix is admitted, and every such key the
bundle carries is also a row, so a prefixed key with no row is admitted and REPORTED.

**The four readers.**

| reader | module | what it derives |
| --- | --- | --- |
| admission | `schema/parse.py` | at every node, every key is looked up at the node's position: NOTHING is admitted and carried nowhere; a key with no row is admitted and marks the node for the TOP widening, naming a keyword the bundle did not use before; any other effect is a fact the node's kind consumes |
| descent | `schema/parse.py`, `bundle.py`, `verify/record.py` | the structural keywords and the position each one's subschema occupies — the one descent table |
| lowering | `lower/*` | a handler asks the table which of the keywords on its node are TYPE facts, which are RULE sources, which are annotations it carries, and — through `approximate` — which widening a keyword it cannot render drops to, so no handler holds a set of keyword names and none chooses a widening |
| grading | `verify/compare.py` | the compared set is `{k for k in TABLE if cell(k, p).rendered}`; a keyword whose effect is RULE is graded against the class's rule tuple, as §8 of the semantics document says; a compared fact the model does not state is *approximated* where the class's declaration carries it and *missing* where it does not |

**The table is the source of §5, §6 and §7's grids.** Those grids are GENERATED from
`keywords.py`; `tests/test_keywords.py` asserts the committed document matches what the table
generates, so a change to a cell that is not written through to the document fails. Generation
rather than a diff, because a diff can only compare what it can parse back out of a table: a
cell deciding one thing where the sentence beside it says another passes a membership diff and
cannot pass generation, which writes the cell. §6 is the table's rows that are NOTHING or
ANNOTATION at every position, and §7 is the rows that refuse — the EMPTY projection — so each
section is a projection and not a second list.

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

**Where the WIDENING of a dropped keyword comes from.** The table answers which widening a
keyword the handler cannot render drops to:

- the widening is `cell(keyword, node.position).widens_to`, read by `approximate` and by nothing
  else;
- a cell whose `widens_to` is `None` cannot be approximated, and a handler that asks for one is
  a `BuildFailure` — the keyword states no fact, so a widening against it would be a declaration
  with nothing to declare, and a declaration the draw cannot prove is deleted;
- a key with no row takes TOP, because an unrowed keyword's reach is unknown and TOP is the one
  widening that is safe without knowing it (the semantics document's §7);
- the attribution is `Ours` at the cell's own address unless `attribution.py` holds an entry for
  this document, pointer and keyword, in which case it is that entry's issue. One lookup, no
  precedence to get wrong: a site-level entry is more specific than a keyword-level one.

*Why derived.* A handler that chose its own widening would choose the one that makes its own
output look best, and nothing could audit it against the table that was supposed to hold the
decision. A widening read off the table cannot say that, because the table is where the decision
that the keyword compiles was made. A kind assigned by hand at a raise site comes out inverted in
bulk, and the widening is the same hazard one step further on.

**What is left of the refusal's kind.** `bundle.record` mints VERDICT where a reference's target
is not a bundle document, and CHAINED `through=` the target's refusal where the target has no
record of its own. `Kind.DEFERRED` retires with the outcome it named (§2). Nothing in `lower/`
imports `codegen.refusal`, which is the import-graph half of the seam being total.

---

## 3a. The CATALOGUE: one pass collects every type, and the walk emits against it

**A CATALOGUE IS A READING OF THE BUNDLE, AND §9's CENSUS RULE PERMITS IT.** §9 forbids a census
over the RUN — the argument list, which differs between a one-document command and a
whole-bundle emission. The bundle is pinned and is an input
to every run alike, so a catalogue yields the same answer in both and is exactly what that rule
protects. Those are different things, and a clause fencing cross-module identity to a single
module on §9's authority has misread it. Without the catalogue the compiler reproduces the defect
it was built to escape.

### §3a's ENTRY KEY IS THE VALUE LIST, AND AN UNTITLED ENTRY IS NAMED FROM ITS HOME

**A RULE POSITION MINTS NO TYPE, so a node inside an `if`, `then`, `else` or `not` is not a stating
position of any layer.** A conditional states a RULE on the nearest class; it does not state a
type.

**A `definitions` SECTION IS OUT OF THE KEY.** An entry no reference names admits nothing, so it is
not a stating position at all; an entry that is named is already in the key at every referring
site, so carrying the section too would make two nodes admitting the same set differ on a side-car.
The same reasoning takes ORDER out wherever it appears — a `required` list's order, and a
combinator's branch order, because an instance reads those as sets. An enumeration's member order
stays in, for the reason the value-list rule already records.

**AND THE ARRAY LAYER COLLECTS NOTHING, BY DERIVATION RATHER THAN BY MEASUREMENT.** `list[X]` is
written once in Python by construction, so the only thing an array position can write twice is its
ELEMENT — and an element is owned by a layer beneath: a reference, an object, a constrained scalar,
an enumeration, a composition, or a scalar with no type to write. **So the array layer's obligation
is a check and not a collection**: it reddens if a repeated array type ever appears whose element
belongs to none of those, which is exactly the case where it would need one.

**What tells a shared subject from a coincidental overlap is that an object's key holds the property
NAMES, while an array's key over a scalar element holds no name at all** — which is why the object
layer can collapse on identity and the array layer must not.

**A LAYER'S KEY CONTAINS EXACTLY WHAT CHANGES THE SET OF ADMITTED INSTANCES, AND NOTHING ELSE.**
§3a settles the recursion and the order — an object's identity is the
identity of its property types, collected L0 upward — but not what the key CONTAINS.

**The test is admission-equivalence, and it is the one L0 already used.** Two nodes are one entry
exactly when no instance distinguishes them. So the key holds the property NAMES (a different name
admits different instances), `required`, `additionalProperties`, and every narrowing keyword — each
changes what is admitted. It does not hold a `title`, a `description`, an `examples`, or the ORDER
of the properties — none changes what is admitted, and order is the axis a census must be explicitly
blind to or it reports a difference no payload can see.

**And this reconciles the two precedents that look opposed.** L0 leaves `type: "string"` out of its
key beside an all-string enum because it *"admits not one value more"*. The narrowing keywords go
IN because they admit strictly less. **Both are the same rule**: in the key if and only if some
instance turns on it. Nothing here is a judgement about which keywords matter — the question is
always whether a payload can tell.

**A key read off the RENDERED ANNOTATION is not this key**, and must not be mistaken for it: a
rendered annotation carries a `description`, so a census over it moves when the renderer does, and
a figure that moves when the renderer changes cannot be a layer's identity. The key is computed
over the catalogue entries beneath, which is what §3a's "rather than over raw JSON" asks for, and
references are resolved to what they name before keying — an unresolved key UNDERCOUNTS, measurably
so at the array layer.

**THE KEY IS THE VALUE LIST, not the structural identity §3a named.** The reading is *"each
distinct vocabulary is one type"*, and a vocabulary is a set of admitted values. Where two
structural identities appear over one value list, the whole of the difference is a redundant
`type: "string"` beside an all-string enum — a keyword that
admits not one value more. Keying on structural identity therefore splits entries that are one
vocabulary, on a distinction no payload can see.

**And the guard that makes this safe rather than loose is the converse:** a group whose members
differ in a keyword that **narrows** must redden a check, not collapse in the compiler. Two value
lists that look alike and admit differently are two vocabularies, and the compiler must never be
the thing that decides they are one.

**AN UNTITLED ENTRY WITH NO NAMING POSITION LIVES IN A MODULE WITH NO DOCUMENT**, which the export
record permits now that it is keyed on the module. The module sits in the namespace §3a's
scope rule names — the domain's where every reference is within one domain, the shared one
otherwise — and is re-exported from the matching consumer namespace like any other.

**ITS HOME IS THE CATALOGUE'S OWN LAYER AND NEVER A STATING POSITION INSIDE A DOCUMENT.** A home
chosen among the stating positions is a home inside a document module, and a shared type inside a
document module is the one arrangement that makes a reference cycle possible at all — which the
catalogue's layering exists to forbid. **No order over the stating positions is sound, including the
one that closes no cycle on the bundle in front of it**: it is cycle-free by inspection of this
input and not by derivation, so it cannot be proved for the next one, and the escape clause such a
rule needs — refuse and report rather than answer wrongly — is a schema improvement costing a
hundred-odd refusals. §3a asks that a cycle be **unrepresentable rather than avoided by care**, and
only a home outside every document module is that.

**AND THE ORDER THE ENTRY'S NAME LENGTHENS BY IS STILL DERIVED, because the home no longer supplies
one.** Where the home was a stating position it ranked them; now the rank is the dependency order
the layers already state, which is a function of the bundle and not of a walk.

**AND ITS NAME LENGTHENS BY ITS HOME'S CHAIN, NEVER BY AN ARBITRARY STATING POSITION.** §4 lengthens
a collision by the nearest ancestor segment, and an entry stated at six positions has six such
segments — so without this sentence the name is a function of which position a walk happened to
visit. Untitled entries do collide inside the namespace the scope rule sends them to — distinct
value lists deriving one short noun.
Because the home is unique and derived, lengthening by the home's chain is order-independent, and
where two entries share both a home and a derived name §4's own axes decide as they already do for
every other position.

### A document root, a class statement, and the export record's key

**A DOCUMENT ROOT BEATS A RESTATING TITLE, so a CONFLICT with a rooted vocabulary is not one.**
Where one of two titles over one member set belongs to a **document of its own**, §1 has
already given that vocabulary an exported symbol and §3a's own rule says a document root is
already a home. There is nothing to mint, because the bundle named it. The other title is then a
restating position that happens to carry a title of its own, and a local title does not create a
second type over an identical member set, because no value
distinguishes them. **So the conflict rule applies only where NEITHER title is a document root.**
Where one is, that root is the home and the rest reference it. A restated title that a consumer
needs is an alias at its position, never a second class.

**EVERY NAMED TYPE IS A CLASS STATEMENT. THE FUNCTIONAL FORM IS WITHDRAWN ENTIRELY,
including for two types sharing one value list.**

§3a's *"the value list is written once per distinct member set and the named type is constructed
from it"* **mandates no `StrEnum('<Name>', …)` call: the functional call is one way to construct a
type from a list and it is not the only one.** A class statement
whose member VALUES are read out of the shared list satisfies the rule exactly — the strings appear
in one place and only the member's own index is repeated, and the index is its position in the
document's own order:

```python
_VALUES_… = ("created", "updated", "unchanged", "failed", "deleted")   # written ONCE

class CatalogAction(StrEnum):
    """Action taken on a catalog during sync operation"""
    CREATED = _VALUES_…[0]
    UPDATED = _VALUES_…[1]
```

**Three costs are measured against the functional call, and the third is why the form is
withdrawn rather than narrowed.** A functionally-built enum has no slot for the class docstring
pydantic renders as `description`; a name bound by assignment is invisible to a guard that reads
class statements; and **a member access on it is an attribute error to a CONSUMER's type checker** —
a checker cannot execute the call, so it never learns the member names. That third one is a
regression in the reading that says the package's annotations reach a consumer's checker.

**The class-statement form gives up none of the three and satisfies the rule, so there is no case
left where the functional call is the right answer.** Where two types are judged distinct over one
value list, each is its own class statement reading the same list, and each keeps its own docstring.

**AND A GUARD THAT READS CLASS STATEMENTS GOES BLIND TO AN ASSIGNMENT, so it reads the NAMESPACE.**
A collision guard exists to answer what a consumer meets when importing the module, and a consumer
meets the module's namespace, not its syntax. Reading the emitted module's own bindings is both
stricter and not a structural assertion — it stops caring how a name came to be bound, which is the
property that lets the functional form slip past it.

**THE EXPORT RECORD IS KEYED ON THE MODULE, NOT ON THE DOCUMENT.** A
vocabulary with no naming position needs a module of its own, and that module has no document
behind it. **A pseudo-document path is refused**: it names a file the bundle does not contain, and
every reader that resolves a record from a key would then be lying about where the schema came
from. The honest relocation is one level up — every document already maps to the module it
produced, so the key becomes that module and a catalogue module is simply one with no document.
The readers that take a document to answer a domain or a path take the module instead, which is
what they were always asking about.

### THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT

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

**A READER ASKING WHAT THE DOCUMENT STATES READS THROUGH THE STORAGE.** The
hoisting is a storage representation, so a reference to a storage entry is not a fact the document
states — it is where the fact is kept. **Any reader whose question is semantic therefore
dereferences**, and a reader that walks the stored text raw is answering a different question and
must say so.

It follows that the dereference belongs at the seam every semantic reader already passes through,
and that a check written against a record must go through that seam rather than re-deriving the
walk. A helper that walks the record raw is the thing to fix, never the stored form.

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

### A DERIVED READING OF THE BUNDLE IS AN ARGUMENT, NOT SOMETHING A CALLEE RECOMPUTES

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

Without the catalogue the compiler reproduces the defect it was built to escape.
`datamodel-code-generator` emitted a type per position and the result was duplicate classes and
unions nobody could name; a hand-written walk that also emits a type per position arrives at the
same place with more effort.
**Faithfulness per node is not consistency across the bundle**, and only the second is what a
consumer experiences.

### Which reading a layer's figures are over

**L0 is counted over STATING POSITIONS**, and which reading a figure is over is stated with the
figure: the raw reading and the record reading name different numbers of entries over the same
bundle, because the record has inlined what the raw document references. A title is stated once and
every `$ref` carries it along, so inlining multiplies the titled and untitled groups and leaves the
conflicting titles untouched — which is the tell that a figure is a record reading presented as a
bundle reading. §3a's readings over the TREE are unaffected, because a class exists or it does not.

Which reading L0 collects over is its own decision, and it is not a detail.

### The gate is worded PER TITLE, never per member-set

"No two classes carry one member-set unless the bundle gives the field no title" cannot go green.
A value set titled at one document's root for one subject and stated untitled at unrelated
positions IS a titled group under member-set identity, so satisfying the gate types the unrelated
field by the first subject's name: the coincidental overlap the untitled rule exists to refuse,
arriving through the IDENTITY instead of through the name. A member-set reading is unfixable at
that entry; a per-title reading is fixable.

### A CONFLICTING TITLE NEVER COLLAPSES, and the reason is §4's

Two concepts over one value set keep both names: the values and the semantics coincide and the
SUBJECT does not. One concept stated twice — a canonicalisation left beside its original — is the
BUNDLE's duplication. The descriptions settle which of the two a conflict is.

**Neither case collapses, and the rule is one sentence: a conflicting title is not a question
about which name wins.** Where the bundle states two concepts, both names are right and merging
types one subject with the other's name. Where it states one concept twice, the duplication is the
BUNDLE's and removing it is an upstream report, not a rename we perform — and a merge would hide
the evidence the report needs. In neither case is there a third name to collapse to, and minting
one is what §4 refuses.

So the three-way naming split's third case is **decided, not deferred**: a conflict is reported and
left alone, and the only judgement is whether to file it upstream. **Nothing about the conflicting
titles motivates machinery**; the scale is entirely in the untitled sets.

### A DOCUMENT ROOT IS ALREADY A HOME

Most nameable entries are stated at a document ROOT. **§4 governs and the
narrowest-namespace rule does not reach a root**: a root is not an entry looking for a home,
because §1's "every portable document contributes a symbol" means a rooted vocabulary already
exports its own name from its own domain. There is nothing to relocate.

**So L0's job for those is not to move them — it is to stop every other position minting a
copy.** The other positions reference the existing symbol, which is what §5's `$ref` row already
does for a position that spells the reference; the defect is the positions that restate the
vocabulary inline instead. That is a smaller and better-defined change than a relocation, and it
is why the shared namespace holds almost nothing for L0.

### PASS B RUNS FIRST, and it needs no catalogue at all

Pass B — a `const` pin naming its enum's member — carries the largest share of the type errors,
and at nearly every one of its sites the base's enum is either declared in the same module or
imported into it. In both cases the class that types the base's field already exists and is already
one object; the pin has only to name its member. `ir.TypeRef`
already carries the members, and the compiler already renders `Literal[Symbol.MEMBER, …]` for the
`$ref`-target case. Pydantic renders `Literal[E.A]` as `{"const": …, "type": "string"}`,
**byte-identical** to `Literal['…']`, so no accepts verdict and no dump moves.

L0's cross-document collapse reaches far fewer sites. So the normalisation is both the larger win
and the one with no namespace question, no new ordering edge and no relocation — it goes first, and
the collection follows it.

### THE VALUE LIST IS WRITTEN ONCE; THE NAMED TYPE IS PER POSITION

An identical value set must not be emitted repeatedly: **one value set under several names, in
several classes, restating member strings the bundle states once each** is the cost of
compiling a position without asking what already exists.

**But collapsing them into one type is the wrong repair**, and the reason is the untitled rule:
nothing names those sets, so two positions sharing a member set may be two concepts that coincide.
Merging would type one with the other's name.

So the two halves separate:

- **the VALUE LIST is a module-level constant in the catalogue layer, written once per distinct
  member set;**
- **the NAMED TYPE is constructed from it at each position that needs one**, keeping the name §4
  derives and keeping the types distinct.

Two class statements reading one list are two
types that are not assignable to each other and share one definition of the values. Nothing is
restated, nothing is merged, and a reader sees the vocabulary in one place.

**Where a title exists the stronger rule still applies**: one type, named for the title,
referenced by every position. A title is a human string and the type is an identifier, so the
title is rendered in the tree's own convention — `Account Status` names `AccountStatus` — and the
convention is not a second decision per entry. The construction above is for the untitled sets,
which are the set.

### EVERY REPEATED VALUE SET IS AN UPSTREAM QUESTION

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

Identical members over two subjects is the second row, not an outcome that closes. **The filing
asks the question rather than asserting the answer**, because the specification's authors know
which they meant and we are inferring it from two descriptions.

**The filings are consolidated before they are sent.** A large set filed one at a time is noise
that buries the finding; the same set analysed into the families it falls into is a case the
specification can act on. So the analysis completes first, the filings are grouped by family, and
nothing is sent per set.

### WHEN A NAME IS THE BUNDLE'S, AND WHEN IT IS MINTED

§4 refuses to mint a public name no document states. The line is per TOKEN: **a name is the
bundle's when every token in it is stated at that vocabulary's own positions.**

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

A set left separate because no name could be found is not the same verdict as a set left separate
because the subjects differ, and collapsing the two hides which of them upstream can fix.

So the local state is one of three:

- **one named type** — the positions are one subject and the bundle names it;
- **separate types, one value list** — the positions are genuinely different subjects;
- **separate types pending a name** — the positions are plausibly one subject and nothing in the
  bundle names it. The filing asks for the name, and the local answer changes when it arrives.

The third is where the bundle's silence costs us, and it is the row most worth filing, because the
answer is a word the specification's authors already have.

### WHAT THE CATALOGUE DOES TO AN APPROXIMATION'S DENOMINATOR

An approximation is counted at the declaration SITE where each position derives its own
type and a dropped fact is dropped at that position. **Under a catalogue the denominator becomes
the ENTRY**: a constrained scalar appearing at thousands of positions and dropping one fact is one
approximation, not thousands. A per-site reading of the declared facts does not survive the change
— whatever they become must be re-derived and reported as a changed denominator rather than as
progress.

**And the near-duplicate constraint question is a different kind, not a smaller one.** A
`format: uri` position carrying a
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

**Pass A is DETERMINISTIC**: structural identity. It is reproducible and needs no judgement.

**Pass B is NORMALISING** — the same concept spelled two ways, which Pass A cannot see because
the two spellings are genuinely different JSON. The known cases, each a separate decision with
its own measurement:

- **`const` against `enum`.** A document states `enum: [...]` at its root's property and
  `const: "…"` at its branch's. One vocabulary, two keywords.
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

**THE CATALOGUE IS NOT CONSULTED AT ONE SEAM WHILE HANDLERS DECIDE A TYPE LOCALLY. THAT INVERSION
IS THE SINGLE CAUSE OF DUPLICATION.** The algorithm is four steps and no gate: **collect every type
the bundle states, deduplicate, name each subject once, place it — and then emission is a
PROJECTION of that catalogue.** Emitting a type per position, consulting the catalogue where a
handler happens to ask, and relying on a census afterwards to find what leaked is the inversion,
and every duplication it produces is found by a different instrument after the fact.

**A GATE THAT FINDS DUPLICATION IS EVIDENCE THE ORDER IS WRONG.** Deduplication is not a property
to be checked; it is a consequence of deciding a type once. Where the decision is made once, a
census over the output can only ever confirm it — which is what a regression guard is for, and is
all these gates should be.

**SO THE ORDER IS FIXED AND IT IS NOT NEGOTIABLE BY A HANDLER:**

1. **The catalogue is built COMPLETE, over the whole bundle, before any lowering** — every layer,
   including the repeated-document layer above L3.
2. **Every node asks it. Not one seam, every node.** A node's type is a reference to an entry, or
   a fresh type where the node is genuinely unique, and "genuinely unique" is the catalogue's
   answer rather than a handler's assumption.
3. **A name is minted per ENTRY and never per position.** This is what makes a role word claiming
   a subject's name impossible by construction: a position has a role, an entry has a subject, and
   only a subject gets a name.
4. **Emission projects the catalogue.** Nothing rewrites emitted output — §2 already forbids that,
   and post-hoc deduplication is the same thing wearing a census.

### The NAME comes from the bundle, so a catalogue entry is derived and not minted

§4's standing rule. A vocabulary carrying exactly one `title` the bundle gives takes that title as
its name; one carrying none is **not** collapsed across documents, because nothing names the
concept and without a title there is nothing to tell a coincidental member-set overlap from an
identity; one carrying conflicting titles is a decision brought to the owner. **The same three-way
split is the rule for L1, L2 and L3, and each layer's counts are to be measured rather than assumed
from L0's.**

### THE JUDGMENT IS DATA, NEVER CODE — AND THE DATA IS A MEASURE OF UPSTREAM'S DEFECTS

**COLLECTION IS DETERMINISTIC AND SO IS GENERATION. THE ONLY THING THAT IS NOT IS WHETHER TWO
IDENTICAL-LOOKING TYPES ARE THE SAME SUBJECT, and that question exists ONLY
because of schema composition, schema duplication and outright schema defects.** Two nodes can
carry the same admitted-set key and be different concepts; two nodes can describe one concept and
differ because one of them states a constraint the other forgot. Neither is decidable from the key,
and nothing in this compiler should pretend otherwise.

**SO THE JUDGMENT LIVES IN A DECLARED TABLE THAT THE PIPELINE READS, AND NEVER IN A HANDLER'S
LOGIC.** Two kinds of entry, each keyed on schema nodes and never on a name:

- **COLLAPSE** — the keys differ and the subject is one. The bundle restates one concept twice, or
  one statement of it is missing a constraint the other has.
- **SPLIT** — the keys agree and the subjects are two. A coincidental overlap, which is why a
  vocabulary with no `title` is not collapsed across documents.

**EVERY ENTRY CARRIES THE UPSTREAM DEFECT IT COMPENSATES FOR AND THE ASK FILED AGAINST IT.** An
entry with no named defect is not a judgment, it is a preference, and it does not belong in the
table.

**AND THE TABLE'S SIZE IS A DEBT FIGURE, NOT A DESIGN FEATURE. IT MUST SHRINK AS THE SCHEMA IS
FIXED, AND AN ENTRY WHOSE ASK UPSTREAM ACCEPTS IS DELETED RATHER THAN KEPT.** A table that only
ever grows has stopped recording the schema's defects and started recording ours. **For a
well-defined bundle it is EMPTY and the whole process is mechanical** — that is the target state,
and the distance to it is exactly the number of entries.

**THE CORRESPONDING OBLIGATION IS TO DELETE.** Because the decision is made once from a table and
a complete catalogue, the machinery that generated duplicates and the machinery that hunted them
afterwards are both dead code — not refactored, removed. **A change implementing this order that
adds more lines than it deletes has misread it.**

### A READER DERIVES ITS KEY FROM THE ACCESSOR THE GRADE READS THROUGH

**THE RECORD CARRIES EACH SUBSCHEMA IN TWO FORMS** — the text it is **stored** as, and the node the
document **applies** — and `adcp.types._base.schema_at` is the one crossing between them.

**ANY READER THAT SELECTS, KEYS OR MEMOISES BY POSITION OR BY CONTENT DERIVES ITS KEY FROM THAT
ACCESSOR, NEVER FROM THE TEXT THAT PRODUCED IT.** A reader keyed on the other form does not
*disagree* with the grade — **it matches NOTHING, and a check that matches nothing is green.**

**SO THE TEST FOR SUCH A READER IS NEVER "DOES IT FIND THE RIGHT THING" BUT "CAN IT FAIL AT ALL".**
Assert the match is **non-empty** at a position where the two forms differ, and **inject** an entry
there to prove the effect lands. A reader whose matched set is empty passes every assertion over it.

**AND A DERIVED EQUALITY RANGES OVER THE SET THE GRADE ACTS IN, NEVER THE SET THE ARTIFACT
CONTAINS.** The same defect one layer out: a census answering "is in the package" over every
document, where the tree grades a subset, is an equality between two different questions.

### AN OVERRIDE THE BUILD DOES NOT APPLY IS A LIE, AND THE GATE IS ON THE ARTIFACT

**A PATCH SET THAT NO COMPILE PATH READS MUST FAIL.** A test that proves the function transforms a
bundle in a temporary directory says nothing about whether the run calls it, and a patch set whose
documents do not exist in the bundle the compiler reads moves no emitted class.

**AN INVARIANT THAT HOLDS WHETHER OR NOT THE WORK HAPPENED CANNOT BE THE ACCEPTANCE TEST FOR THE
WORK.** `./check`'s three figures are *designed* to be unmoved by a correct change, so "unmoved" is
as much proof of no effect as proof of no harm. The acceptance test is a measurement that MOVES:
here the count of field sets emitted more than once, read off the emitted tree.

So:

- **THE ACCEPTANCE TEST FOR ANY OVERRIDE IS THE EMITTED ARTIFACT**, never the mechanism, never a
  table, never a filed ask. A judgment table nothing consumes is instrumentation, and §11's rule
  applies to it: an instrument is not product.
- **A NON-EMPTY PATCH SET WITH NO EFFECT ON THE TREE IS RED.** Not a warning, not a scope note. If
  `patches/` states an entry and the emitted tree carries no trace of it, the run is wrong.
- **AND THE SENTENCE "IT MOVES ONLY IN A BUNDLE NOTHING COMPILES YET" IS A DEFECT REPORT.** Any
  phrase of that kind — *prepared*, *ready*, *applies cleanly*, *green in a fixture* — names the
  gap between a mechanism and a deliverable, and is to be read as the gap rather than as progress.

### AN OVERRIDE DECLARES THE DEFECT IT COMPENSATES FOR, AND FAILS WHEN THE DEFECT IS GONE

The entry above says the table must shrink. **This says the shrinking is not a discipline anyone
has to remember: an override that is no longer needed must BREAK THE BUILD.** A table that merely
*ought* to shrink is a fork with good intentions, and the day the bundle is fixed properly the
override would quietly keep preferring our answer to the protocol's.

`codegen/patch.py` is the mechanism and states the rule in its own terms, so this
subsection names the properties:

- **AN OVERRIDE IS AN OVERLAY AND NEVER AN EDIT.** It does not rewrite a published document. It
  adds a new one holding the subschema and rewrites each matching site to `$ref` it. A patch
  *replacing* a published document is a different operation, and `load` refuses it, **because the
  record check cannot tell the two apart.**
- **AN OVERRIDE FAILS THE DAY ITS ASK LANDS.** `load` raises where the published bundle already
  holds the document the manifest names. So the fix arriving upstream breaks the run and the
  instruction is to delete the entry — never to shadow a published answer with ours.
- **AND AN EXCLUSION CANNOT ROT.** Where a site matches by structure and differs in MEANING, the
  exclusion is written down with the reason, and `stale` fails if it stops matching anything —
  because an exclusion that excludes nothing silently widens the patch the day its site moves, and
  the next site to *gain* the structure there is rewritten with nobody having read what it means.

**AND EXTRACTION IS WORTH MORE THAN A TITLE, WHICH IS WHY IT IS THE DEFAULT FORM.** Naming a node
in place tells the catalogue what to call one entry. Extracting it gives the structure **a document
path, which IS its name**, and turns every site into a reference — so the entries collapse **by the
reference the bundle now states**, not by an identity we inferred. The judgment is made once, in
data, and the compiler afterwards reads a fact rather than repeating a guess.

**AN ADDITIVE OVERRIDE INHERITS ALL OF IT, AND THE FAILURE CLAUSE IS THE PART THAT IS EASY TO
DROP.** Where extraction is wrong — a structure stated once that merely wants naming — the override
adds the keyword in place. It must then **raise once the node carries that keyword itself**, rather
than overwriting it. An additive override that silently wins over a published value is the one form
of this mechanism that could outlive its cause invisibly, and it would do so while looking like
success.

### WHERE A CATALOGUE ENTRY LIVES, which is what makes the fencing unnecessary

The clause that forbade cross-module identity was guarding something real: shared types reached
for across document modules create import cycles, and the bundle's own design invites them — one
vocabulary is stated in several different domains, and sharing is the main case rather than an
edge.

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
concept in several places; we decide the layers we emit it into, and the layering removes the
hazard the prohibition was written for.

**AND WHERE AN ENTRY'S HOME IS, THE RULE L0 STATES IS NOT STRONG ENOUGH — IT IS GROUP-RELATIVE,
AND THAT IS THE DEFECT.** "The stating position the other stating positions reach through a
reference" is read inside ONE entry, so two entries over one pair of documents answer in opposite
directions and the import arrows meet.

**THE HOME IS THE GROUP'S EARLIEST DOCUMENT IN THE DEPENDENCY ORDER THAT ALREADY EXISTS** — the
graph the walk has, every reference it lowers plus every edge the collection adds. Each new edge
then runs backwards along a topological order of all the others, so **a cycle is unrepresentable
rather than avoided.**

**AND THE ORDER MUST BE OVER THE EDGES THE COLLECTION ADDS, NOT THE REFERENCES ALONE.** A
catalogue edge is not a reference edge, so an order built from references only points against the
extension of it that the collection produces, and documents refuse.

**THE TEST OF THIS RULE IS THAT IT NEEDS NO TEST.** Every other candidate order — the first stating
position, the most-reached document, the smallest transitive reach — is acyclic only where the
bundle happens to allow it, and each one refuses documents. A rule whose soundness has to be
MEASURED for cycles is the wrong rule; the right one cannot produce them.

**AND "A RULE POSITION MINTS NO TYPE" NAMES TWO MORE POSITIONS THAN IT SAYS.** A CONJ position
mints none either — §5 is explicit that inline conjuncts are the fields and rules of *this* class —
and neither does a position beneath a `contains`, whose own cell already decides that the model
states **the predicate** and not a transcription of the subschema. **A layer that collects a
position no class is emitted at has collected a home that cannot declare.**

**An entry lives in the NARROWEST namespace that contains every position referencing it**, which
keeps a consumer's import close to where they met the concept and is derived rather than chosen:

- referenced from one document → that document's module;
- from one domain → that domain;
- from more than one domain → the shared namespace.

**The shared namespace is `adcp.types.common`, one place and not one per layer.** A consumer who
does not know which domain a type belongs to has exactly one place to look, and does not have to
guess whether `AuthenticationScheme` is a "value" or a "case". The LAYERS are the private
module structure beneath it — the same split the tree already makes, `_schemas` private and the
domain modules public — so the acyclic order is a property of the emission and the public surface
stays flat.

**And this is the reuse the design is for.** A vocabulary stops being re-derived per domain;
a scalar case that appears at thousands of positions is declared once; and a type a consumer
receives in a `media_buy` message is the same object as the one in a `governance` message, so it
can be passed between them.

### Upstream

The bundle spelling one vocabulary as `enum` in one place and `const` in another is a defect in
the SCHEMA, not only in our reading of it, and Pass B exists to absorb something upstream should
not be emitting. It is worth filing against the specification.

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

**This is the one refusal the compiler mints (§2 of the semantics document).** The
principle that unifies its structures is that **the document has no defined accepted set**: there is
no schema half for `strict_validate` to run and nothing for §8 to grade against, which is the
one place the partial-model objection still bites. Three cases reach it — a reference whose
target is not a bundle document, a cross-document cycle, and a document that **fails its own
declared draft's meta-schema** (the case failures `parse` validates for below, which are
this class rather than a second one, since a document that
is not a schema under its own draft has no accepted set to be faithful to). Whether any of the
three is non-empty is a property of one bundle version, and the class stays in the compiler so a
bundle that grows one reports it instead of crashing on it.

A **local** `$ref` cycle is not in this class: it is never inlined, and it renders as a forward
reference under a string annotation with a `model_rebuild()` after the module's declarations
(§6). The difference between the two cycles is the record and not the type.

*Why our own.* The record is what `strict_validate` validates against and what the draw
grades against. A resolver that canonicalises while it inlines writes a document the bundle
does not state, and every reader downstream then needs a fold to undo each rewriting. An
inliner that changes nothing needs none.

**AN INLINER IS KEYED ON THE NODE'S IDENTITY, NEVER ON ITS TEXT.** A key or a copy made of a
subtree's text costs **the text times the depth** at which it appears, because every ancestor
serialises its descendants again; a key made of the node's identity costs **the DAG**.
`bundle.stored` exists because the record's text is a DAG, and **every reader of the record has to
be one too** — a reader that walks it as the tree the DAG unfolds to pays the unfolding, and the
unfolding is what the storage was written to avoid.

**The figure to keep is not a total but a ratio taken *before* anything resolves**: a single stored
entry can be many times its own document's distinct content when written out as text, and resolving
two references to it costs that again per occurrence.

**AND THIS RULE HAS A BOUNDARY, WHICH IS THAT THE WALK MUST PRESERVE ITS CHILDREN'S IDENTITY.** It
holds for a walk over a structure whose repeated subtrees are held BY REFERENCE — that is what makes
the text key quadratic and the identity key linear. **It inverts for a function that REBUILDS its
argument**, because then every child it recurses on is a fresh object sharing identity with nothing,
and an identity key cannot hit what no two call sites hold in common. A strategy builder whose
first statement rebuilds its argument through text is such a function, and there the text key is
the effective one. So the discriminator is not
which key is cheaper to compute — it is **whether the walk hands the same object twice**, and that
is a property of the callee rather than of the data. Ask it before applying this rule anywhere.

**AND THE ACCEPTS RESOLVER INLINES AND DOES NOT CANONICALISE**, which is a statement about where a
cost belongs rather than about correctness. The draw's own strategy builder canonicalises whatever
it is handed, so **a draw pays canonicalisation inside the draw, over the schema it will generate
from, and resolution pays it never.** A resolver that canonicalises pays it once per inlined
occurrence and then hands the draw something it will canonicalise again.

**A ONE-SHOT `signal.alarm` DOES NOT BOUND ANYTHING**, which is why a timeout is not the fix for
it: the signal can land where Python DISCARDS the exception it raises — a
garbage-collection callback or a `__del__`, and `hypothesis` installs one — so the alarm fires, is
ignored, and nothing is left to fire again. `harness.within`'s timer repeats for exactly that
reason, so a swallowed signal costs the interval and not the bound.

**A phase that cannot be preempted must be made to terminate, not bounded** — and a bound whose
delivery is probabilistic must repeat, or it is reporting a guarantee it does not have.

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

**`parse` is total.** A document that fails its own meta-schema has no accepted set and
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
above. **`items` is not among them**: a list-valued `items` is draft-07's tuple validation,
and the semantics document's §5 lowers it to `list[A | B | …]` at the JOIN widening rather than
refusing it, so the parser builds an `Array` whose element is the join and records the
approximation. Unexercised in a bundle that states no list-valued `items`.

*The screen and the classification INTERLEAVE.*
They cannot be strictly sequenced, because the admission cases do not all answer from the cell
alone. Two of them do — a key with no row and a NOTHING cell are decided by
`cell(keyword, position)` and nothing else, so they run before anything is classified. The
third does not: §3's reader ends "any other effect is a fact the node's kind consumes", and
whether a lowering effect is CLAIMED or is WIDENED is a question about which kind owns the
node. So that case runs after the classification it depends on.

The four jobs are not four sequential passes. A node is classified once and screened once, and
the dependency runs one way: admission that reads only a cell, then classification, then admission
that reads the kind. Nothing is screened twice and no mapping is traversed twice, which is what §4
is actually protecting.

A node at RULE is parsed like any other, kept on the enclosing node as a rule source, and is
never handed to `decide`: under a conditional a keyword describes what a rule tests, so no type
is lowered from it, and `lower/rules.py` is its only reader.

*Why the parser decides the kind.* Reading a node's keys and its
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
of its own kind it has no rendering for, its final case calls `approximate(node, keyword)` and
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

### A HANDLER MODULE HOLDS ITS ROW'S DECISION, AND `compiler.py` HOLDS NO ROW

**A module whose body delegates to another module is not a module. It is a name for one**, and
it satisfies this section's layout while leaving the structure the layout describes unbuilt. A
reader who opens `lower/composition.py` to learn what an `allOf` lowers to must find the answer
there — not a call into a module that also holds the object row, the intersection rule, the
field builder and the walk's context.

Nothing is to be invented: no new
abstraction, no new indirection, no pattern adopted to justify a move. **Where a façade module
and a god module both exist, the code moves into the façade and the god module shrinks to what
only it can hold.**

**What only `compiler.py` can hold is the CONTEXT** — the one value the handlers share, which
is the walk's state and belongs to no row. Everything else has a home that names its subject:

- **a row's decision** lives in that row's `lower/<kind>.py`, whole.
- **a collaborator several rows share** lives with its PRIMARY subject and is imported by the
  others. The field builder and the class declarer are the object row's — every class with
  fields passes through them, and the composing row and a union branch are callers.
- **a pure function over two declarations** lives in a module of its own, because purity is
  exactly the property that makes it gradeable alone, and §6 already classifies the
  intersection rule that way.

**THE TEST OF THE BOUNDARY IS WHAT A READER OPENS, NEVER A LINE COUNT.** A module states one
subject; a function answers one question about it. Both are judgements, and neither is a
threshold — which is why the sentence above is about where a reader looks and not about how much
is there.

**A CEILING ON COMPLEXITY OR LENGTH IS SET AFTER THE DECOMPOSITION, NEVER BEFORE IT, AND THE TWO
ARE SET TOGETHER.** Before: the number is the debt, frozen, and it is satisfiable by moving
statements — a long function becomes two in the same module and nothing is separated. After: the
number is the structure's own, and it is a tripwire against the next drift rather than a
description of the present one. Together, because each alone has an escape: a complexity limit is
met by splitting a function inside the module, a length limit by splitting a module without
separating a concern. **This is the one place a count is admitted in this project, and it is
admitted as a regression guard on a structure already reached — never as the instrument that
reaches it.**

**Root and non-root are one path.** There is no second table of root selectors. A document is
`parse(raw, position=ROOT)` followed by `decide`. The only thing ROOT adds is the module
wrapper — a class carries `strict_validate` by inheritance, and a root whose lowering is an
alias or an enumeration gets a `RootBinding` declaration from `lower_document`, which is the
one function that knows a root is a root. The document-set predicates a step's result was
stated over are the tests' business and live under `tests/`.

**The committed tree's own set is not one of those predicates.** It is `bundle.portable` — every
document of the bundle that can be emitted at all — because the
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
it descended through, so a handler never derives position from a pointer string.

*What a predicate that did becomes.* `node.position is BRANCH` is the wrong fact:
`position is BRANCH` says "this node is a branch of some union", while the
predicate it replaces answers "this node is a branch of a ROOT union" — and the two differ.

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

**What an approximation does to the walk.** It is **local** — it belongs to the node that
could not render a keyword and says nothing about the node above it — so a parent composes it
like any other part of a child's lowering and keeps building. The document emits. What reaches
`lower_document` is therefore not one approximation but all of them, in document order, because
`+` concatenates and the children were lowered in the order the document states them. The
report is still a function of the document and not of the walk's iteration, by the same
property that makes `first_refusal`'s answer one: the parser built each node's children in
document order, and concatenation preserves it.

**The partial model is unrepresentable**, because there is no partial model to represent — a
document either has no accepted set at all (§4's one refusal, and then it has no module) or it
emits a complete module for every node of itself, some of whose annotations say less than their
document does and each of those declared.

**References.** A cross-document `Reference` lowers to an import: `ctx.targets[document]` holds
the target's `Module`, whose symbol table answers the pointer half. **A pointer the target
declared no symbol at widens**, to the target's own root symbol where the fragment is reachable
under it and to TOP otherwise, and declares the approximation naming the fragment. A target with
no record of its own is not reached at all: the run never lowers a
document whose record is undefined, and a document referencing one has no record either (§4).

A local `Reference` (`#/definitions/x`) lowers to the declaration of that `definitions` entry:
the entry was parsed at DEF, `decide` is called on it with `ctx.resolving` extended, and the
entry's own lowering is the symbol. **A pointer already in `resolving` is a cycle, and a cycle
is a forward reference, not a refusal.** The declaration takes the entry's symbol
as a string annotation and the module calls `model_rebuild()` after its declarations — the
mechanism §4 of the semantics document already uses for union branches, which do not exist while
their base is built. So `ctx.resolving` is not a refusal trigger but what it always
described: the pointers in flight, which is how the lowering knows to write a forward reference
rather than recurse. Unexercised in a bundle that states no local cycle, so the rule is decided
before one arrives.

An entry nothing references is never decided, which is the §5 rule that a `definitions` section
is nothing by itself.

**Composition.** A `Composition` handler lowers each `$ref` conjunct to a base — the target's
`ClassDecl` is read off `ctx.targets` for its field case — and merges inline conjuncts' fields
and rule sources into its own by the intersection rule, which lives in
`lower/composition.py`: `restatement`, `intersection` and
`at_least_as_tight` are pure functions over two nodes and stay so. A conjunct carrying its own
`allOf` is a `Composition` node at CONJ and the handler recurses.

**Unions.** A `Union` at ROOT whose branches are all cases lowers to a base `ClassDecl` carrying
the branch-dispatch facts and one `ClassDecl` per branch, each branch a class with the base first
among its bases; the root's siblings compile onto the base as §5 of the semantics document says.
A `Union` at ROOT whose branches are all scalars lowers to an `AliasDecl` and a `RootBinding`.
**A `Union` at ROOT mixing the two lowers to a `RootModelDecl`** over the union of the branches'
types, with the class branches declared beside it and the dispatch facts on the root model —
§4 of the semantics document's row, which replaces a refusal and costs no approximation,
because the union admits exactly what the document admits. A `Union` below the root lowers to a
`TypeRef.union` of its branches' types, each branch's bound carried on the branch's own named
type.

A union whose branches §4 of the semantics document cannot separate lowers the same way it would
if they were separable. Where the combinator is `oneOf` it declares a WIDENED `Approximation` at
the union's own pointer, because the model then admits a payload the document refuses and the draw
proves it. Where it is `anyOf` it declares **nothing**: the model admits exactly what the document
admits, and the only loss — which branch an overlapping payload becomes — is observable by no draw
and no dump.

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
| `Approximation` | document, pointer, keyword, kind (WIDENED, the only one), widening, the fact the annotation does not carry in the document's own spelling, and the attribution |
| `Module` | document, root symbol, declarations in declaration order, imports, approximations, the symbol table pointer → name, the adoption table pointer → declaring pointer |

**An approximation is a DECLARATION and not a report, and it is written into the emitted
module.** A `Report` is a line the run prints and nothing reads — a dropped default,
a key that carries nothing. An approximation is read by the GRADER, and §9 forbids the verifier
reading the walk, so there are only two ways for it to get there: a side channel the run hands
the verifier, or the emitted artifact. It is the artifact: `render.py` writes
`__adcp_approximations__` onto the class, the root model or the enumeration, and beside the
module for an alias — exactly the split §4 of the semantics document already makes for
`strict_validate` — and `verify/` reads it as a consumer reads any other class attribute.

*Why the artifact and not a side channel.* `__adcp_schema__` is already there for the same
reason: a verifier handed its facts by the run
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

**The obligation is the derivation and not the spelling: the call is derived from the dataclass's
own fields, and the one rule for spelling it lives in `render.py` and nowhere else.** `repr` is one
way to spell a constructor expression and is not the goal — it is keyword-form while a positional
rule call is equally correct, and keyword and positional arguments to a frozen dataclass construct
the same object, so the spelling carries no meaning to trade for a text delta across the tree.
Normalising that spelling is legitimate as a DELIBERATE, stated text
delta with its own row; it is not something a relocation does on the way past.

*Why a complete IR.* A decision layer that produces class-body
lines, rule tuples and module trailers as text, with a `Module` accumulating text blocks beside
its decision memo, is not an IR with render concerns beside it; it is two layers sharing
a mutable object, and one module holding the renderer, the keyword sets,
the name rules, the field builder and the composition reader is the cost. With the IR
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
to it by identity.

**A branch with no identity is not a refusal.** A branch with no title, no pinned `const` and no
`required` set takes its index among the branches, `<Base>Branch<i>`, and a missing or
non-identifier root title takes the document's own file stem. A name is not an acceptance fact, so
a fallback name neither widens nor narrows.

The walk computes no name, which is the semantics document's own
rule that a name is an input to a lowering and is never computed inside one — read strictly,
it is not an input either: it is assigned after.

---

## 8. Rendering, and the one-way boundary with Pydantic

`codegen/render.py` is the only module under `codegen/` outside `verify/` that imports
`pydantic` or `datamodel_code_generator`. It takes a `Module` and returns the module's text; it
takes the run's union of `ConstraintCase`s and returns `adcp/types/constraints.py`. It renders
through the model layer of the pinned code generator and never its parser: the parser decides
names and structure, which is this compiler's half.

The boundary is one-way and a test enforces it (`tests/test_import_rule.py`):
nothing in `schema/`, `lower/`, `ir.py`, `keywords.py` or `bundle.py` imports `pydantic`,
`pydantic_core` or `datamodel_code_generator`. A `TypeRef.Symbol("pydantic", "AwareDatetime")`
is a Python symbol the semantics document names in its `format` row, and naming a symbol is
not a Pydantic idiom; constructing a `Field`, a `ConfigDict`, an `Annotated` or a `DataType`
is, and only `render.py` does it. `codegen/constraints.py` keeps its naming rule — a pure
function from a constraint case to a `TypeRef` — and does not import the renderer.

The runtime package `src/adcp/types/_base.py` and `_runtime.py` is the other side of the
boundary: `SchemaRef`, `applied_schema`, `strict_validate`, `strict_alias`,
`BranchDispatchMixin` and the rule validator are correct and the semantics document's §4 pins
them. Two extensions, and no replacement.

**`applied_schema`** gains the same-instance keywords §13 item 3 names.

**`AdCPRootModel`.** The semantics document's §4 gives three cases to a
root model — an array, a union mixing a scalar branch with a class branch, and a document stating
no schema keyword — and each must carry `__adcp_schema__`, `strict_validate` and a rule tuple
exactly as a class does, or a root model and a class disagree about what their document accepts.
So `class AdCPRootModel(RootModel, RuleBound)` joins `AdCPBaseModel`, and **`strict_validate` and
`__adcp_schema__` factor out of `AdCPBaseModel` into a mixin both take** — one body, for the
reason `strict_alias` exists: a second implementation of the schema half is a second answer to
the one question. That MRO resolves, the rule validator fires
on a root model, and `model_json_schema()` renders the root type's own schema, so a reader
pairs a root model as it pairs a class.

---

## 9. The verifier: `codegen/verify/`

The verifier grades an emitted class against the document it names, and it does so without
reading the walk. Its import set is the whole of that rule, and `tests/test_import_rule.py`
asserts it: `codegen.keywords` (for the compared set and the widenings), `codegen.attribution` (to
grade an approximation's issue reference), `codegen.bundle` (for the record and the document
set), `adcp.types` (the emitted package, reached as a consumer reaches it), `codegen.refusal`
(to read a refusal the run recorded), and its libraries. Never `codegen.schema`,
`codegen.lower`, `codegen.ir`, `codegen.render`, `codegen.emit`.

**`codegen.attribution` is in the set and `codegen.ir` is not**, which is the whole of why the
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

Its checks are the semantics document's §8: `accepts.py` draws
from the record and constructs; `dump.py` serialises and validates against the record,
striking the exemptions `exemptions.py` lists. Every
fold that undoes a rewriting of the delegated resolver is deleted when the record is this
package's own (§4): the finite-type restoration, the derived `maxItems`, the `{"not": {}}`
closure, the dropped `additionalProperties: true`, the one-member `enum` respelling and the
same-title lift. What remains of normalisation is the readings this pipeline's own output
forces — a nested class hoisted to `$defs`, D4's `| None` for an optional property, a type list
rendered as a union — and each is applied to both sides.

**The approximation's grader is the draw**, and there is one rather than three: a declaration
either names a value the document admits and the class now accepts, or it does not belong in the
declared set.

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
also what `strict_validate` validates against, so the two cannot disagree. **The set is
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
constraints module, and prunes stale emitted files on a whole-bundle run. `main` lives
in `codegen/__main__.py`, so `python -m codegen` is the command and no module of the compiler is
ever bound as `__main__`.

**The layout, and a document whose path is also a directory's.** A
document's module is its bundle path with hyphens as underscores — `emit.module_path`.
Where the bundle holds both a document
at path `P` and a directory at path `P`, **the two are one namespace and the document is its
root**: the document emits `P/__init__.py` and the directory's documents are its submodules.

The alternative that is rejected is writing both — `brand.py` beside an empty
`brand/__init__.py`, where Python resolves the name to the package and the
module is UNIMPORTABLE. A written module no import can reach is an artifact defect and it is
silent: the run reports the document as emitted.

A distinguishing suffix is not taken, because it mints a public name no document states, and §4
derives every name from the document. Calling the bundle at fault is not taken either: the
layout is draft-07-legal and the bundle is pinned, so refusing it relocates the defect into a
document that emits.

This makes one `__init__.py` carry content where the others are markers. That is the cost, and
it is a smaller one than an unimportable module: `emit.relative_module`'s hop arithmetic has to
agree with it, which is a check a test can hold.

**What the report prints.** The `emitted / refused` pair is not a partition — **it is the KIND
split, and the kind is what names who owns a refusal.** `emitted N / set N` moves
one number when a document stops emitting and says nothing about which kind moved, so a reader
cannot tell a document the bundle broke from a row nobody has written. The
delivery report reads `emitted`, `refused` with its deferred/verdict split, `accounted`, and
primary/chained off `Refusal.kind`, never off a sentence and never summed.

So the figures are these, each over its own denominator and never summed, by the semantics
document's §2:

- **`emitted N / refused M (deferred …, verdict …)`, with `accounted`**. `set` is not printed
  beside it: `emitted` and `refused` already carry it, and a
  third number next to them invites exactly the sum the protocol forbids.
- **the round-trip failures, per pair and by name** — a pair where the class refuses a value the
  document admits, or where the dump is a value the document refuses. Printed whether or not the
  count is zero, so a reader sees the pin being met rather than inferring it from silence. What
  the deleted text-diff counts are replaced by is not a count. It is **one row per graded pair,
  written to a FILE by the run** — document,
  pointer, and each check's verdict — because a figure that exists only in a terminal cannot be
  reviewed, and because a check that computed nothing shows up there as a blank column instead of
  as a pass.
- **`approximated K facts in D documents`**, split by attribution (ours / upstream), with the
  upstream half listing its issues. There is one kind, WIDENED. `K` and `D` are
  different counts over different denominators and the report never adds them. Neither is
  pinned: both rise when a document starts emitting, and the semantics document's §9 forbids
  pinning a figure that moves with emission. The **ours** half is the one that ratchets down,
  and it is the figure a wave's exit condition reads (§14).

The drops and carries-nothing lines stay. An approximation is NOT one of them: a
carries-nothing line says a keyword constrained nothing, and an approximation says a keyword
constrained something the annotation does not carry. Printing them in one list would sum two
different things.

*Why the entry-point module matters structurally.* A double binding under `runpy` is the one
reason a compiler would carry `decide`, `bind` and `name_constraint` as callables on a
dataclass, keep the composition reader in the renderer's module, and enforce an import rule
on the lowerings. With an entry point no lowering can name, a lowering imports `decide`
directly, the context carries data and not functions, and the import rule shrinks to the two
boundaries that are about design: no Pydantic in the walk, no walk in the verifier.

---

## 11. Layers: what each knows, what it may not, what crosses

| layer | modules | knows | may not know | crosses outward as |
| --- | --- | --- | --- | --- |
| declaration | `keywords.py`, `attribution.py` | positions, keywords, cells, descent, widenings; the upstream issue at a document, pointer and keyword | nodes, documents, types, text | `Cell`, `Issue` |
| refusal | `refusal.py` | the kinds, and that a document may have no accepted set | everything else | `Refusal` |
| source | `bundle.py` | files, paths, `$ref` URIs, edges, the record | kinds, cells' effects, types | raw mapping, `edges`, `record` |
| reading | `schema/nodes.py`, `schema/parse.py` | raw mapping → `Node`; admission; applied type; positions; pointers | the IR, Python types, text, the run | `Node` |
| decision | `lower/decide.py`, `lower/<kind>.py`, `lower/rules.py`, `lower/names.py`, `constraints.py` | `Node` → `Lowering`; the table's cells and widenings; the attributions; naming; the runtime's rule classes | mappings, text, the renderer, files, the run | `Module` |
| representation | `ir.py` | the declarations and `TypeRef` | text, pydantic, nodes | — |
| render | `render.py` | `Module` → text through the pinned model layer | `Node`, mappings, the table | text |
| run | `emit.py`, `__main__.py` | order, closure, files, the report | kinds, cells, nodes | files |
| verify | `verify/*` | emitted classes, the record, the rendered column | the walk, the IR, the renderer | reports |

The import graph is acyclic and the arrows point one way: `refusal ← keywords ← ir ← schema ←
lower ← emit`, `ir ← render ← emit`, `ir ← constraints ← lower`,
`{keywords, attribution} ← lower`, `keywords ← bundle ← emit`,
`{keywords, attribution, bundle} ← verify`. `attribution.py` is a leaf like `keywords.py`, which
is what lets both the walk and the verifier read it without either reading the other.

*`attribution.py` imports `codegen.refusal`, and no module of the walk.* §3 requires an
attribution entry with no upstream issue to be a `BuildFailure`,
and that type lives in `refusal.py` — so this module cannot satisfy a total ban, the
`BuildFailure` rule and the `MAY_RAISE` ratchet at once, and a
local `MissingIssue` reddens the ratchet. `refusal.py` imports nothing itself, so a leaf importing
a leaf keeps the property the ban was protecting: one module reached, and no module of the walk.
The rule is therefore *imports no module of the walk*, and `refusal` is named as the one thing it
may reach.

**`refusal` is imported by `bundle`, `emit` and `attribution`, and by nothing in `lower/`**:
the lowering seam is total, so a handler has no refusal to name.

Four AST tests hold the graph: no
`pydantic`/`datamodel_code_generator` import outside `render.py` and `verify/`; no
`codegen.{schema,lower,ir,render,emit}` import inside `verify/`; no
`codegen.{render,emit,verify}` import inside `schema/` or `lower/`; and **no `raise` of anything
but `BuildFailure` inside `schema/` or `lower/`**. The fourth is the test that
replaces the type-system guarantee §2 gave up: with one inhabitant at the seam the type checker
can no longer force a handler to answer for the other branch, so the thing it was preventing — a
node reaching no outcome — is prevented by banning the only other way out.

**Nothing repeats: where each repetition has one owner.**

| repeated | one owner |
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
| the widening a handler takes, chosen where it widens | the cell's `widens_to`, read by `approximate` |
| the upstream issue for a widening, written as prose in a comment | `attribution.py`, keyed by document, pointer and keyword |
| the exempted facts listed once per check that strikes them | two lists, deliberately: `attribution.py` holds why a MODEL says less than its document, `verify/exemptions.py` holds which DUMP facts a check strikes. One registry for both would sum two different things |

What stays two by design: the intersection rule, once in `lower/composition.py` for the model
and once in `verify/compare.py` for the document (§9 says why); the `applied_schema` rule,
once in the runtime and read by the parser rather than restated.

---

## 12. The restructure

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
   them — drops a key, which §3 forbids.

  **It extends only to ANNOTATION siblings.** A CONSTRAINING sibling
   is a different case and §5's `$ref` row decides it: draft-07 ignores every
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
   `additionalProperties` and `allOf` into a branch node, where it conjoins `type`
   alone. This document extends `applied_schema` in `_base.py` to every same-instance keyword
   §5's union row compiles onto the base, and reads the result as draft-07's own semantics
   applied at a pointer the document holds rather than as a view. If the owner reads it as a
   view, the union row's "fields on the base, inherited by every branch" has no gradable
   pairing and the row has to change instead.

4. **§3, "`Refusal` lives in the package every lowering imports, so any step can raise one".**
   Closed: no lowering imports `Refusal` at all, the seam is total, and the only producer is
   `bundle.record`.

5. **§2's refusal kinds, counted separately.** Closed: one resolved kind — VERDICT, for a
   document with no accepted set — and CHAINED delegating to it from `bundle.record`. DEFERRED
   retires with the outcome it named, and the semantics document's §9 states the replacement
   rule. What the rule became is that the three APPROXIMATION figures are never summed (§10).

6. **§8's diff test is replaced by generation, and §8 says so.** Markdown is not a machine
   source for a cell's meaning, and a membership diff admits a cell that decides one thing beside
   a sentence saying another. The grids of §5, §6 and §7 are generated from the table instead, so
   the second copy of the what does not exist to drift. The reasoning paragraphs stay hand-written
   and are the part a reader must keep honest against the cells.

7. **§4 "Names", a branch with no identity.** Closed: a branch with no title, no pinned `const`
   and no `required` set takes its index among the branches, `<Base>Branch<i>`. A name is not an
   acceptance fact, so the fallback neither widens nor narrows and costs no approximation, and
   the index is a function of document order, so it does not depend on which documents the run
   includes. The same reasoning gives a missing or non-identifier root title the document's own
   file stem.

---

## 14. Migration path

Each step can be taken alone, is checked by a test that exists or is named, and says whether
the emitted tree or the report changes. Steps marked *bytes* are checked by regenerating the
tree and comparing it byte for byte with the committed one.

**What a *bytes* mark forbids, and what it does not.** It exists to prove a step
is a RELOCATION and not a decision, so what it forbids is an UNDECLARED change: text that moved
because the step chose something, with no sentence in either document behind the choice. It does
not forbid fixing a defect the semantics document has already decided. Where a step's correct
implementation makes the emitted tree conform to a sentence it was violating, the tree moves,
and the step reports the change with the document, the pointer and the sentence that decides
it — enumerated, never aggregated.

The two cases are told apart by asking what is on the other side of the trade. A rendering whose
spelling no sentence decides — keyword against positional arguments to a frozen
dataclass, the same object either way — loses to *bytes*. A reading that contradicts a decided
sentence, where the fix changes one module in which a document emitted before, wins over it: a
gate that forbade it would be pinning the defect.

**The order.** Steps 1 to 7 are relocations. Step 8 is the approximation end to end with **no
cell widened**, step 9 is the rows the directive makes FAITHFUL, and step 10 is the rows that
genuinely widen. The split is forced rather than tidy: *the instrument has to exist before the
first cell widens.* A cell that widens while no draw yet reaches the values the keyword
distinguishes produces a flood the pin cannot survive, and the project then either abandons the
pin or stops believing the grader — which is the semantics document's §8 failure mode. The waves
follow, with the exit condition below.

1. **`codegen/__main__.py`.** Move `main` there; `python -m codegen` is the command. Delete the
   `__main__` re-entry in `emit.py`, the `decide`/`bind`/`name_constraint` callables on
   `Module` (lowerings import `decide` and `constraints.resolve` directly), and the lazy
   imports that existed for the cycle. Narrow `tests/test_import_rule.py` to the two design
   boundaries (§8, §9). *Bytes.* Unblocks every later move of a function between modules.

2. **`codegen/keywords.py` and its first two readers.** Declare `Position`, `Cell`, `Row`,
   `TABLE`. Make `check_keywords` read the table at a position its callers pass (the position
   is known at every call site, as a structural fact of the caller). Derive the
   verifier's compared set from the rendered column. Derive the kind of every refusal minted by
   `check_keywords` from the cell. Add `tests/test_keywords.py` (§3). *Report changes:* the
   keywords the semantics document renders and the verifier does not compare start being
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

  *How the conversion is STAGED.*
   The end state above is not negotiable: `parse` is the only reader of a raw mapping, and a
   handler reads node fields. The conversion to it is not one commit's worth of work, and it is
   not atomic: §4's rule is about the WALK and not about field
   access. "One parser is the one reading" forbids a second traversal of the raw document; it
   does not forbid a half-migrated handler being handed the mapping its own node was built
   from. So during this step a node may carry its originating mapping, `parse` performs the one
   traversal, and each handler converts to node fields one kind at a time — each conversion its
   own commit, each checked by the byte compare. **The step is not complete until that carrier
   is deleted**, and its deletion is the step's last commit: a tree that still has it has not
   finished step 5, and no later step may read it. Staging a refactor is not the same as
   softening its end state.

  *The refusal ORDER is document order, and that settles what this step owes the old report.*
   It does not owe the sequence the handlers happen to screen in. §2 and §6 both state the rule:
   `first_refusal` returns the earliest refusal in DOCUMENT
   order, "which keeps the report a function of the document and not of the walk's iteration".
   A present screening sequence IS the walk's iteration, and it is what this step exists to
   remove.

   So where a refusal moves because document order puts a different node first, that is this
   step's "report changes" and not a regression. What must NOT change is which documents refuse
   and with which `resolved` kind; the pointer and keyword within a refused document may move to
   the node document order reaches first. Measure both: the refused SET with its kinds, which
   holds, and the moved pointers, which are enumerated and explained.

6. **Refusal as a value.** `Refusal` stops subclassing `Exception`; every handler returns
   `Lowering | Refusal`; `first_refusal` replaces the try/except in `lower_document`;
   `lower_document` returns a value to the run. The type checker is the test. *No change in
   outcomes.* Unblocks §2's totality.

  *Step 8 takes the second half of it.* This step makes the seam a sum
   type, which is what makes the next move possible: a seam that raises cannot be collapsed,
   because there is no inhabitant to collapse to. Step 8 collapses the sum to `Lowering` alone.
   The intermediate state is not wasted work — the sum type is what turns every present
   deferral into a compile error the moment `Refusal` leaves the seam, which is how step 8
   finds them all.

7. **`lower/names.py` and the dependency-ordered run.** Move naming and dedup into the pass
   over the module; compute `edges`, the closure and the order in `emit.py` and pass `targets`
   through the context; delete the binder closure and `inflight`. *Bytes*
   for the modules; the report's refusal order may change and must stay sorted by document.
   Completes §6, §7 and §10.

  *`resolving` on `Module` stays, as data.*
   The dependency order is over DOCUMENTS; `resolving` guards a LOCAL cycle inside one document,
   so computing the order retires nothing about it. §6 gives
   `ctx.resolving` an explicit job as a forward-reference marker rather than a refusal trigger.
   The step's real content is that no CALLABLE survives on the context.

  *What the run WRITES is the set it owes, not the static closure.* §10's
   justification is that a module cannot import from a module no run wrote. The static closure of
   every `$ref` satisfies that and overshoots it: it
   writes modules nothing imports and nobody named, and adds aliases to the public
   `constraints.py`. So the run writes the documents it was named plus what an attempted lowering
   actually referenced, as a fixed point over `Module.asked` — which satisfies §10's sentence
   exactly, because every import resolves and nothing else is written. The closure is still what
   the ORDER is computed over; it is not what the run emits.

  **AND "WHAT AN ATTEMPTED LOWERING REFERENCED" MEANS EVERY EDGE A MODULE IMPORTS ALONG, NOT THE
   `$ref` EDGES ALONE.** §3a's catalogue gives a position a type by IMPORTING the symbol the
   naming position
   declares — a vocabulary collected across documents, a restating title, an object type whose
   home is elsewhere — and **none of those is a `$ref` in the source document.** So a run named
   over a subset writes a module importing from a module it did not write, and the package does
   not import.

   **The rule is one sentence and it is about imports, not about references: a run writes every
   module that any module it writes imports from.** The closure is the transitive closure of the
   IMPORT relation the lowering actually produces, and `$ref` is one contributor to it.

   This is green over the whole bundle and false over any subset, which is what a defect
   looks like when every instrument for it ranges only over the full set — **and the fix is to the
   closure, not to the gate's set**: a gate that only ever runs over everything proves nothing
   about the mechanism it is named for.

8. **The approximation, end to end, with no cell widened.** The instrument before the change.
   Add `Widening` and `widens_to` to the cell and retire `Effect.REFUSE`; add `Approximation` and
   `RootModelDecl` to the IR and `approximations` to `Lowering` and `Module`; add
   `codegen/attribution.py` and its no-issue-is-a-`BuildFailure` test; make `render.py` write
   `__adcp_approximations__`; add the
   accepts obligation over a dropped keyword's classes and the
   report's three figures. Add the fourth import-rule test (§11). *Exit condition: every count
   unchanged — the same documents emit, the same documents refuse — with `APPROXIMATED` 0 and
   `OVER_DECLARED` 0.* The tree changes by one line per module (`__adcp_approximations__ = ()`),
   which is a declared text delta and not a decision. **Nothing else in the directive may land
   before this step passes.**

  *The seam collapse is NOT in this step.* A total seam here cannot hold beside this step's own
   exit condition: `approximate` reads the widening off the cell, a `None` widening is a
   `BuildFailure`, and all but one primary refusal sits on a cell that is not `Effect.REFUSE`, so
   they have no widening yet. A total seam therefore either widens those cells, which moves the
   counts this step forbids moving, or crashes the run on every document holding one.

   So the seam stays a sum type until the last cell has a widening, which is **step 10**, and
   `Kind.DEFERRED` retires with it. The instrument is complete without the collapse: the widening
   field, the declaration, the registry, the two outcomes and both equalities all exist and are
   proved here, and the fourth import-rule test passes unchanged. What the collapse buys —
   turning every remaining deferral into a compile error — is worth having exactly when there is
   a widening for each one to reach, and not before.

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

10. **The widened rows.** What is left, each with the widening and attribution the semantics
    document's §5 states: an `allOf` restatement whose intersection is not computable; an empty
    intersection; a union whose branches cannot be separated; a `contains`
    predicate no `AtLeastOne` carries; a keyword with no row; a list-valued `items`; a root
    stating no schema keyword.

   *One more case, because `refused == 0` has no answer for it.* **A `$ref`
    conjunct whose target is NOT a class, beside a node that declares fields of its own.** §5's
    `$ref` row at CONJ says the target becomes this node's own TYPE where it is a scalar, an
    enum, a container or a union root — and that clause is scoped, in its own words, to "a node
    that declares no fields of its own". These nodes declare some, so the node is at once a class
    (it has fields) and a type (the target), and §5 answers neither.

    It is a WIDENED row and not a faithful one. Carrying it faithfully means the instance must
    satisfy the node's fields AND one of the target union's branches, and "also satisfies this
    imported union" is not one of §2's rule families — adding one is a larger decision than this
    case earns. So the conjunct's union membership is DROPPED, the class emits
    with its own fields, and the gap is declared. The widening is safe in the usual way:
    `strict_validate` still enforces the union from the document, so only the annotation loosens.

   *The upstream issues do NOT block this step.* Requiring them first makes the
    compiler's own completion wait on a third party's issue tracker, and the thing being built
    is a compiler that represents every schema — it cannot have an external calendar in its exit
    condition.

    So the gate is on the WORD "upstream". Every approximation is
    attributed, and an attribution is OURS until an issue exists: `Attribution.ours(reason)` needs
    no reference and says in one sentence what the schema would have to state for the gap to
    close. Only `Attribution.upstream(issue)` requires a live reference, and that constructor
    keeps its `BuildFailure` — so nothing is ever *claimed* as upstream without a filed issue,
    which is the honesty property that gate protects. Filing an issue later
    reclassifies the attribution from ours to upstream and the *ours* backlog falls by that much;
    it does not change a type or an emission.

    What this costs: the *ours* figure reads higher until the issues are filed, which is correct
    — an unfiled gap IS ours. What it buys: `refused == 0` is reachable without waiting on
    anyone outside this repository.

   **The seam collapse lands here.** Once this step has given
    every reachable cell a widening, `decide` collapses to `Lowering`, `Refusal` narrows to its one
    producer in `bundle.record`, and `Kind.DEFERRED` retires — which is what turns any remaining
    deferral into a compile error rather than a report line. It belongs at the end rather than
    the beginning for the reason step 8 records: a total seam over cells with no widening is a
    `BuildFailure` on every one of them. The collapse is the *consequence* of the widenings being
    complete, not the mechanism that completes them.

   *Exit condition: `refused` is 0 over the portable set, `decide` returns `Lowering`,
    `Kind.DEFERRED` is gone, `APPROXIMATED` equals the declared set in both directions, and every
    upstream attribution names a live issue.*

**Then the waves.** A wave's exit condition is **"these keywords' OURS approximations reach 0"**
— the upstream half is not a wave's to close. And the wave ORDER is measured rather than carried
over: ordering by how many documents each keyword set *completes* has no quantity after step 10,
because every document is complete. The new quantity is how many *approximated
facts* a wave's keywords close, which is a different number over a different denominator and
will not produce the same order. The upstream half is not a wave at all; it is the issue list,
and it closes when upstream closes.

**NO STEP OF THIS SECTION OWNS THE CONSUMER SURFACE, and that is deliberate rather than an
omission.** §14 is the
COMPILER's migration path, and every step here is checked against the emitted tree or the report.
What a domain module exports is not a property of the compiler's internals; it is the artifact a
consumer imports, so it is graded by census against that artifact and not by a step's *bytes*
mark. `docs/plan/surface-goal.md` owns that goal, `docs/plan/unimplemented.md` A-2 owns the gap,
and the row is P4-09.
