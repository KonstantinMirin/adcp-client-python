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

## 1. The shape

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
    │  Lowering  =  a TypeRef plus the declarations, imports and reports it needed
lower/names.py     symbols assigned over the whole module, content dedup included
    │  Module (the intermediate representation, no text in it)
render.py          the one module that knows pydantic and the model layer it renders through
    │  text
emit.py            the run: dependency order, files, the report
```

Beside the pipeline, two modules every layer reads and none of them writes:

- `codegen/keywords.py` — the declaration §8 of the semantics document calls for: every
  keyword, at every position, with what it compiles to, whether the model renders it as a
  fact, and which structural keywords descend into which position.
- `codegen/refusal.py` — the one refusal type, a value and not an exception.

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
- **Total functions from node to decision.** `decide(node, ctx)` returns `Lowering | Refusal`.
  Every handler has that signature. A refusal is a VALUE a parent returns upward unchanged;
  nothing raises one and nothing catches one. The type checker therefore refuses a caller that
  reads a `Lowering` field off a result without handling the `Refusal` branch, which is the
  mechanical form of the semantics document's §9 rule that a crash is not an outcome.
- **Composition by explicit combinators.** `Lowering` composes with `+`: a parent's declarations
  are its own followed by its children's, its imports the union, its reports the concatenation.
  `first_refusal(results)` is the one combinator over a sequence of child results, and it
  returns the earliest refusal in document order so a refusal names the innermost node that
  carried the keyword.
- **Effects at the two ends.** `bundle.py` reads files. `emit.py` writes files and prints the
  report. Nothing between them touches a file, an environment variable, a clock or a global.
  The run's own state — which documents are lowered, which refused — is a fold in `emit.py`
  over a dependency order computed before any document is lowered (§10), so no handler ever
  calls back into the run.

**What becomes of the exception-based refusal.** `Refusal` stays in `codegen/refusal.py` and
stops subclassing `Exception`. Its constructors are the only place a kind is decided (§5). The
one `try` left in the compiler is around nothing: a defect in the compiler itself — two
selectors claiming one node, two constraints deriving one alias name — stays an exception
(`BuildFailure`) that no layer catches, because it is not an outcome of any document and the
run must stop on it.

---

## 3. The declaration: `codegen/keywords.py`

The semantics document's §5, §6 and §7 are a table of keyword × position. The code carries that
table once, as data, and four readers derive from it. Nothing else in `codegen/` names a
keyword in a set literal.

```python
class Position(StrEnum):
    ROOT, PROP, ELEM, MAPV, KEY, BRANCH, CONJ, RULE, DEF   # the positions §3 names

class Cell(NamedTuple):
    effect: Effect          # TYPE | FIELD | RULE | NAME | ANNOTATION | NOTHING | REFUSE
    rendered: bool          # does a faithful model state this keyword in model_json_schema()
    descends: Position | None   # the position of the subschema(s) this keyword holds, if any
    compiles: str           # the sentence the grid states for this keyword here

class Row(NamedTuple):
    default: Cell
    at: Mapping[Position, Cell]   # the positions where the answer differs from the default

TABLE: Mapping[str, Row]
def cell(keyword: str, position: Position) -> Cell | None   # None: no row, which refuses by name
```

A row is written per keyword with a default cell and an override per position that differs,
because that is the shape of the semantics document's own tables: most rows give one answer
and name the positions that depart from it.

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
shape the semantics document's rows are written in — "`min_length` / `max_length` on the type,
as a named alias. KEY → the key type … ELEM / MAPV → the alias inside the container. ROOT → the
root alias. RULE → nothing." — so the rule is read off the existing grids rather than imposed on
them. A co-occurrence that is not a position (`pattern` beside `format: uri`, an `enum` beside
`type`) belongs to the sentence of the cell it qualifies, because the table is keyed by position
and a co-occurrence is not one.

§6 and §7's grids are membership projections and need no join: a row NOTHING or ANNOTATION at
every position renders its `compiles` as §6's "what it does, or why nothing", and a REFUSE row
renders it as §7's "why".

The table also carries the `x-` namespace rule
(§6 of the semantics document): a key with the prefix is admitted, and every such key the
bundle carries is also a row, so a prefixed key with no row is admitted and REPORTED.

**The four readers.**

| reader | module | what it derives |
| --- | --- | --- |
| admission | `schema/parse.py` | at every node, every key is looked up at the node's position: NOTHING is admitted and carried nowhere; REFUSE refuses the document as a VERDICT; a key with no row refuses the document as a VERDICT naming a keyword the bundle did not use before; any other effect is a fact the node's kind consumes |
| descent | `schema/parse.py`, `bundle.py`, `verify/record.py` | the structural keywords and the position each one's subschema occupies — the one descent table, where today there are three |
| lowering | `lower/*` | a handler asks the table which of the keywords on its node are TYPE facts, which are RULE sources, which are annotations it carries, so no handler holds a set of keyword names |
| grading | `verify/compare.py` | the compared set is `{k for k in TABLE if cell(k, p).rendered}`; a keyword whose effect is RULE is graded against the class's rule tuple, as §8 of the semantics document says |

**The table is the source of §5, §6 and §7's grids.** Those grids are GENERATED from
`keywords.py`; `tests/test_keywords.py` asserts the committed document matches what the table
generates, so a change to a cell that is not written through to the document fails. Generation
rather than a diff, because a diff can only compare what it can parse back out of a table: a
cell deciding one thing where the sentence beside it says another passes a membership diff and
cannot pass generation, which writes the cell. §6 is the table's rows that are NOTHING or
ANNOTATION at every position and §7 its REFUSE rows, so each section is a projection and not a
second list.

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

**Where the kind of a refusal comes from.** A refusal's kind is derived from the cell and never
chosen at a raise site:

- a key whose cell is REFUSE, or a document that contradicts itself (a `const` its own `type`
  refuses, a `required` name no property declares, a title that derives no identifier) is a
  VERDICT: the obstruction belongs to the document;
- a key whose cell is a lowering effect and whose handler has no code for this shape yet is a
  DEFERRAL: `Refusal.unwritten(node, keyword)` is the one constructor for it, and it asserts
  the cell is not REFUSE;
- a reference whose target refused is CHAINED and carries the target's refusal;
- UNRESOLVED disappears. It named a reference the delegated resolver did not reach, and the
  resolver in §4 reaches every position.

*Why derived.* The reviews record the two kinds assigned by hand at a raise site and the
assignment coming out inverted in bulk: a cell the semantics document decides, written up as a
verdict against the document. A kind read off the table cannot say that, because the table is
where the decision that the keyword compiles was made.

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

*Why our own.* The record is what `strict_validate` validates against and what the comparison
grades against. A resolver that canonicalises while it inlines writes a document the bundle
does not state, and every reader downstream then needs a fold to undo each rewriting — the
verifier carries folds of that kind today. An inliner that changes nothing needs none.

### The node, and the parser that is the one reading

`codegen/schema/nodes.py` declares the in-memory form, and it is a **typed representation of a
schema node, not the raw mapping**. One frozen dataclass per kind, each carrying exactly the
keywords its kind can consume, already validated for shape:

| node kind | selected by | carries |
| --- | --- | --- |
| `Reference` | `$ref` | document half, pointer half, annotation siblings |
| `Enumeration` | `enum` | members, member descriptions (both spellings), the applied type word |
| `Constant` | `const` | the value |
| `Composition` | `allOf` | conjuncts at CONJ, own properties and required, extra policy, rule sources |
| `Union` | `oneOf` / `anyOf` whose branches are shapes | combinator, branches at BRANCH, the root's siblings when at ROOT |
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
          applied: str | None) -> Node | Refusal
```

It does four things at every node, in this order. It screens every key against the table at
`position` (§3's admission reader). It classifies the node: the kind-determining keywords
present select the kind, and the co-occurrences the semantics document decides are decided
here and nowhere else — a `$ref` beside a constraining key refuses on the sibling; an `enum`
beside `type` is an enumeration whose base the members decide; `allOf` beside `properties` is a
composition with fields of its own; a combinator whose every branch is `required`-only is not a
`Union` but a rule source of the enclosing object (the `presence_only` reading, read once
here); a `type: object` beside `oneOf` is a union whose branches inherit the applied word. It
descends by the table's descent column, assigning each child its position and the applied
word for a same-instance hop. And it validates shape: `required` is a list of names,
`properties` is a mapping of schemas, `items` is one schema and not a list, and so on, each
failure a VERDICT refusal because a malformed document is a property of the document.

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
def decide(node: Node, ctx: Context) -> Lowering | Refusal:
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
its node and the context and returns a `Lowering` or a `Refusal`. It reads the table for every
keyword on its node and consults the position through `node.position`.

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
place that did (`enum.resolves_no_name` reading `hops[-2]`) becomes `node.position is BRANCH`.

**How a child's result composes.** `Lowering` is:

```python
@dataclass(frozen=True)
class Lowering:
    type: TypeRef                       # what the parent writes where it holds this node
    declarations: tuple[Declaration, ...] = ()
    imports: frozenset[Import] = frozenset()
    aliases: frozenset[ConstraintShape] = frozenset()   # for adcp.types.constraints
    reports: tuple[Report, ...] = ()    # a dropped default, a name the class carries nothing for
```

A parent takes `child.type` for its field, element, value or branch, and adds the rest to its
own. An object handler, for instance, is `first_refusal(children) or Lowering(type=Local(pointer),
declarations=(ClassDecl(...), *children_declarations), ...)`.

**What a refusal does to the walk.** A handler that receives a `Refusal` from a child returns
it, unchanged, immediately. The parent of that parent does the same, so the refusal reaches
`lower_document` naming the innermost pointer and keyword that produced it, and the document
produces no declarations at all — the partial model §2 of the semantics document forbids is
unrepresentable, because a `Lowering` and a `Refusal` are different types and nothing holds
both. A document refused by a child's refusal is refused once, on the earliest refusal in
document order, which keeps the report a function of the document and not of the walk's
iteration.

**References.** A cross-document `Reference` lowers to an import: `ctx.targets[document]`
holds the target's `Module`, whose symbol table answers the pointer half; a pointer the target
declared no symbol at is a DEFERRAL naming the fragment, and a target that is itself a
`Refusal` makes this one CHAINED. A local `Reference` (`#/definitions/x`) lowers to the
declaration of that `definitions` entry: the entry was parsed at DEF, `decide` is called on it
with `ctx.resolving` extended, a pointer already in `resolving` is a cycle and a VERDICT, and
the entry's own lowering is the symbol. An entry nothing references is never decided, which is
the §5 rule that a `definitions` section is nothing by itself.

**Composition.** A `Composition` handler lowers each `$ref` conjunct to a base — the target's
`ClassDecl` is read off `ctx.targets` for its field shape — and merges inline conjuncts' fields
and rule sources into its own by the intersection rule, which moves from `compiler.py` to
`lower/composition.py` unchanged in substance: `restatement`, `intersection` and
`at_least_as_tight` are pure functions over two nodes and stay so. A conjunct carrying its own
`allOf` is a `Composition` node at CONJ and the handler recurses.

**Unions.** A `Union` at ROOT lowers to a base `ClassDecl` carrying the branch-dispatch facts
and one `ClassDecl` per branch, each branch a class with the base first among its bases; the
root's siblings compile onto the base as §5 of the semantics document says. A `Union` below the
root lowers to a `TypeRef.union` of its branches' types, each branch's bound carried on the
branch's own named type.

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
| `UnionInstall` | the base and its branches, which the renderer writes as the `_branch_models` assignment and the rebuild |
| `Module` | document, root symbol, declarations in declaration order, imports, the symbol table pointer → name, the adoption table pointer → declaring pointer |

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
to it by identity. Two pointers deriving one name, or a branch with no identity, are VERDICT
refusals of the document. The walk computes no name, which is the semantics document's own
rule that a name is an input to a lowering and is never computed inside one — read strictly,
it is not an input either: it is assigned after.

---

## 8. Rendering, and the one-way boundary with Pydantic

`codegen/render.py` is the only module under `codegen/` outside `verify/` that imports
`pydantic` or `datamodel_code_generator`. It takes a `Module` and returns the module's text; it
takes the run's union of `ConstraintShape`s and returns `adcp/types/constraints.py`. It renders
through the model layer of the pinned code generator and never its parser, for the reason the
present code gives: the parser decides names and structure, which is this compiler's half.

The boundary is one-way and a test enforces it (`tests/test_import_rule.py`, extended):
nothing in `schema/`, `lower/`, `ir.py`, `keywords.py` or `bundle.py` imports `pydantic`,
`pydantic_core` or `datamodel_code_generator`. A `TypeRef.Symbol("pydantic", "AwareDatetime")`
is a Python symbol the semantics document names in its `format` row, and naming a symbol is
not a Pydantic idiom; constructing a `Field`, a `ConfigDict`, an `Annotated` or a `DataType`
is, and only `render.py` does it. `codegen/constraints.py` keeps its naming rule — a pure
function from a constraint shape to a `TypeRef` — and stops importing the renderer.

The runtime package `src/adcp/types/_base.py` and `_runtime.py` is the other side of the
boundary and is unchanged by this document: `SchemaRef`, `applied_schema`, `strict_validate`,
`strict_alias`, `BranchDispatchMixin` and the rule validator are correct and the semantics
document's §4 pins them. The one extension §13 asks for is in `applied_schema`.

---

## 9. The verifier: `codegen/verify/`

The verifier grades an emitted class against the document it names, and it does so without
reading the walk. Its import set is the whole of that rule, and `tests/test_import_rule.py`
asserts it: `codegen.keywords` (for the compared set), `codegen.bundle` (for the record and
the document set), `adcp.types` (the emitted package, reached as a consumer reaches it),
`codegen.refusal` (to read a refusal the run recorded), and its libraries. Never
`codegen.schema`, `codegen.lower`, `codegen.ir`, `codegen.render`, `codegen.emit`.

*Why.* One body of code deciding what the model states and what the document states agrees
with itself by construction, so a defect in it is green on both sides. The verifier's reading
of the document — `_composed`, `_normalize`, the key-schema reading — stays its own, and the
intersection rule it carries stays a second spelling of the one in `lower/composition.py` on
purpose. Sharing DATA is a different matter from sharing a READING: the keyword table is the
declared semantics, and both halves must read the same declaration or the grade means nothing.

Its three checks are the semantics document's §8 and keep today's shape: `accepts.py` draws
from the record and constructs; `dump.py` serialises and validates against the record,
striking the exemptions `exemptions.py` lists; `compare.py` compares `model_json_schema()`
against the record over the table's rendered column, fact by fact and in both directions. Every
fold that undoes a rewriting of the delegated resolver is deleted when the record is this
package's own (§4): the finite-type restoration, the derived `maxItems`, the `{"not": {}}`
closure, the dropped `additionalProperties: true`, the one-member `enum` respelling and the
same-title lift. What remains of normalisation is the readings this pipeline's own output
forces — a nested class hoisted to `$defs`, D4's `| None` for an optional property, a type list
rendered as a union — and each is applied to both sides.

**Pairing.** Every class is paired with the node its `__adcp_schema__` names, read through
`applied_schema`, so a branch class is graded against its branch node under the root's
same-instance keywords. That is the semantics document's §8 pairing rule and it is also what
`strict_validate` validates against, so the two cannot disagree.

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
constraints module, and prunes stale emitted files on a whole-bundle run, as today. The report
prints refusals by kind, drops and carries-nothing lines, as today. `main` lives in
`codegen/__main__.py`, so `python -m codegen` is the command and no module of the compiler is
ever bound as `__main__`.

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
| declaration | `keywords.py` | positions, keywords, cells, descent | nodes, documents, types, text | `Cell` |
| refusal | `refusal.py` | the kinds and the constructors that derive them | everything else | `Refusal` |
| source | `bundle.py` | files, paths, `$ref` URIs, edges, the record | kinds, cells' effects, types | raw mapping, `edges`, `record` |
| reading | `schema/nodes.py`, `schema/parse.py` | raw mapping → `Node`; admission; applied type; positions; pointers | the IR, Python types, text, the run | `Node` |
| decision | `lower/decide.py`, `lower/<kind>.py`, `lower/rules.py`, `lower/names.py`, `constraints.py` | `Node` → `Lowering`; the table's cells; naming; the runtime's rule classes | mappings, text, the renderer, files, the run | `Module` |
| representation | `ir.py` | the declarations and `TypeRef` | text, pydantic, nodes | — |
| render | `render.py` | `Module` → text through the pinned model layer | `Node`, mappings, the table | text |
| run | `emit.py`, `__main__.py` | order, closure, files, the report | kinds, cells, nodes | files |
| verify | `verify/*` | emitted classes, the record, the rendered column | the walk, the IR, the renderer | reports |

The import graph is acyclic and the arrows point one way: `refusal ← keywords ← ir ← schema ←
lower ← emit`, `ir ← render ← emit`, `ir ← constraints ← lower`, `keywords ← bundle ← emit`,
`{keywords, bundle} ← verify`. Three AST tests hold it: no `pydantic`/`datamodel_code_generator`
import outside `render.py` and `verify/`; no `codegen.{schema,lower,ir,render,emit}` import
inside `verify/`; no `codegen.{render,emit,verify}` import inside `schema/` or `lower/`.

**Nothing repeats: where each of today's repetitions has one owner.**

| repeated today | one owner |
| --- | --- |
| three descent tables (`bundle.nodes`, `harness._nodes`, the walk's implicit descent) | the table's `descends` column, read by `parse`, `bundle.edges`, `verify/record.py` |
| keyword screens with a hand-written set at every lowering | admission in `parse`, from the table |
| the kind read in `_decide`, in the root selectors, in `union.keyword`, in `rules.presence_only` | `parse`'s classification |
| the annotation set, the rule-keyword set, the constraint spelling in three modules | rows of the table; `constraints.SPELLING` keeps the alias WORD per keyword, which is a naming fact and not a decision |
| the applied type (`constrained_to_object`, `object_constrained`, `applied_type`) | `Node.applied`, set by `parse` through `applied_schema`'s rule |
| node rewrites (key schema, extras store, multi-type members, `uniqueItems` stripped before the array row) | positions and node fields: `Mapping.key` at KEY, `Object.extras`, `MultiType.members`, `Array.distinct` |
| name derivation at six call sites | `lower/names.py` |
| text produced in the walk (rule tuples, body lines, union trailers, root bindings) | `ir.py` declarations, written by `render.py` |
| the compared set in the verifier beside the handled sets in the walk | the table's `rendered` column |
| the kind of a refusal at every raise site | `Refusal`'s constructors, from the cell |
| the resolver's canonicalisation and its inverse folds | `bundle.record`, with no inverse |

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

**Replaced, because the evidence says the shape is not right there.** The reviews' first
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
   carries the key, the comparison does not grade it, and no handler holds a set of
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

5. **§2's refusal kinds, counted separately.** The semantics document names two kinds and
   describes a third in §9 (a chained target). The structure derives the kind from the table's
   cell rather than taking it as an argument, which the document does not forbid and does not
   state. UNRESOLVED, which the code carries today, is not in the document and is retired by
   the resolver in §4.

6. **§8's diff test is replaced by generation, and §8 now says so.** Markdown is not a machine
   source for a cell's meaning, and a membership diff admits a cell that decides one thing beside
   a sentence saying another. The grids of §5, §6 and §7 are generated from the table instead, so
   the second copy of the what does not exist to drift. The reasoning paragraphs stay hand-written
   and are the part a reader must keep honest against the cells.

7. **§4 "Names", a branch with no identity.** The present code refuses it as a VERDICT, and
   this document keeps that, since §4 gives no fourth rule. The untitled `enum` branch of a root
   union whose only other branch is a constrained string is the case that reaches it, and it
   needs a naming rule in §4 or stays refused.

---

## 14. Migration path

Each step can be taken alone, is checked by a test that exists or is named, and says whether
the emitted tree or the report changes. Steps marked *bytes* are checked by regenerating the
tree and comparing it byte for byte with the committed one.

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
   packaged documents and for the verifier's comparison; keep the delegated resolver inside
   `verify/accepts.py` for drawing. Delete the inverse folds in the verifier. Regenerate the
   packaged documents. *Report changes:* every packaged `.json` changes where a target was
   canonicalised; a new comparison failure is a real finding and not a fold's absence.
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

6. **Refusal as a value.** `Refusal` stops subclassing `Exception`; every handler returns
   `Lowering | Refusal`; `first_refusal` replaces the try/except in `lower_document`;
   `lower_document` returns a value to the run. The type checker is the test. *No change in
   outcomes.* Unblocks §2's totality.

7. **`lower/names.py` and the dependency-ordered run.** Move naming and dedup into the pass
   over the module; compute `edges`, the closure and the order in `emit.py` and pass `targets`
   through the context; delete the binder closure, `inflight`, `resolving` on `Module`. *Bytes*
   for the modules; the report's refusal order may change and must stay sorted by document.
   Completes §6, §7 and §10.

8. **The cells.** With the slots in place, each unwritten cell the reviews list is a handler
   edit against an existing declaration: root siblings onto a union base (and the
   `applied_schema` extension of §13, item 3); a scalar or alias target as the type of a
   composing node; the type-bound validators for `uniqueItems`, `contains` and `not` where no
   class holds the value; a union whose branches differ only in their pinned values as one
   class and one rule; the manifest dispatch source. Each one moves refusals to emissions and
   is graded by the verifier at the pairs it unblocks.
