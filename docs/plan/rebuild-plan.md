# The AdCP types SDK: what it is, and how it is built

The AdCP schema bundle is a directory of JSON Schema draft-07 documents. This describes how we
turn it into Pydantic models: what we produce, the principles that decide every case, how we walk
a document, what we emit, and how each keyword compiles. Where a keyword compiles to nothing, or
to an annotation that says less than the keyword does, that is stated with the keyword — and no
keyword refuses a document (§2, §7).

No site counts appear here. A count is a property of one bundle version and the method has to
outlive it; the instruments under `survey/` and the test suite carry the measurements.

---

## 1. The artifact

A set of Pydantic classes, one per schema node that needs one, generated from the bundle. A
consumer reaches them through one import surface:

```python
from adcp.types.core import PaginationRequest     # the one import spelling
from adcp.types.enums import MatchType            # the domain says where it came from

req = PaginationRequest.strict_validate(payload)  # the schema decides, then construct
req = PaginationRequest(max_results=50)           # pydantic constructs, annotations only
mode = MatchType("broad")                         # a consumer uses these types directly
```

**Generated modules are private; the domain surface is public.** A document compiles to a module
at its own path under a private tree — `core/date-range.json` → `_schemas/core/date_range.py` —
and is re-exported from `adcp.types.<domain>`, where the domain is derived from the document's
own path. So `enums/match-type.json` is reachable as `adcp.types.enums.MatchType`, and a reader
of application code sees what kind of thing it is without looking it up.

There is **one import path per class**, and never a second way to reach the same class. Two
spellings for one class is two things to keep in agreement, and it makes a reader unable to tell
from the import which document a class came from. The one path is the domain surface's. A second
name bound to a class by identity (§4, two nodes of identical content) is that class and not a
second one: `X is Y` holds, and the surface exports it once.

**"ONCE" MEANS ONE NAME ON THE WHOLE SURFACE, NOT ONE PER DOMAIN.** An object reachable at two
domain paths violates this rule even though both names are legitimate derivations: the two
spellings sit in different domains, and a reader comparing them has no way to know they are one
object.

**AND FOR A SYMBOL CARRYING NO `__adcp_schema__`, THE DECLARING POSITION IS ITS CATALOGUE ENTRY'S
HOME.** Only a model class carries that attribute, so an enumeration or a constrained-scalar alias
is read through §3a instead: the entry's home is the stating position the other stating positions
reach through a reference, chosen that way because it closes no reference cycle. **So the home IS
the declaring position, the rule below applies unchanged, and nothing new has to be decided per
symbol.** Where a rooted vocabulary and a referencing position both export one object — one enum
class under two names — the root's name is the one the surface keeps, because a document root is
already a home and a position that references a type does not name it.

**AND THE NAME THE SURFACE KEEPS IS THE ONE DERIVED AT THE CLASS'S OWN DECLARING POSITION** — the
document and pointer its `__adcp_schema__` names, which is where §4 derived it from the bundle. The
other spellings are the names of positions that REFERENCE it, and a position that references a
class does not name it. That rule is derivable, unique per class, and needs no judgement; the
alternative — picking among equally legitimate derivations — would be a decision per object with
nothing deciding it.

**A gate on this counts DECLARATIONS, not `id()` and not names.**

**Counting NAMES is too weak**: two names for one class each resolve at one path, so the check is
answered `yes` while the rule is false.

**Counting `id()` is too STRONG, and it charges us for something we did not do.** Where several
documents each state the same constrained scalar, the walk emits an independent alias statement in
each — and every one of those names IS the name derived at its own declaring position, so there is
no referencing position to drop and nothing to rename. The runtime then binds them to one object
because the type system interns it, and the same happens to an interned literal. **A gate keyed on
object identity reports those as a violation with no available repair**, which makes it a gate
nobody can satisfy rather than one that finds a defect.

**So the reading is one DECLARATION per class.** A class the walk declares twice is the defect —
two statements where the bundle states one subject. Two names bound to one object by a statement
each, in documents that each state it, are two declarations of one ENTRY, and **the catalogue layer
owns that case**: a symbol the catalogue has collected is declared once by construction. So §3a's
collection is the repair there, not a rename, and the two rules must not both claim it.

**What remains for this rule is one class declared once and EXPORTED twice**, and there the surface
keeps only the declaring position's spelling. **Applying it is not purely subtractive:** where the
surface assigns no kind to a declaration at a property or element position, the name the rule keeps
is not exported at all, so the rename adds a name as well as removing ones. A check asking whether
every export resolves at exactly one path is answered `yes` by two names for one object, each
resolving cleanly, so it is green while the rule is false. The reading is that the number of export
paths equals the number of distinct objects behind them.

**That carve-out reaches across modules as well as inside one**, because a document
that is a bare `$ref` to another
document states the same node, and §4's rule for the same node stated twice does not change at a
file boundary. Where the target is a class the root is a subclass of it instead, which is one
class per name and needs no carve-out at all; the identity binding is for a target that is an
alias, an enumeration or a root model, where there is nothing to subclass.

**Every portable document of the bundle contributes a symbol** — a class, a root model, an
enumeration or an alias — because §2 admits no document without one.

**AND THE RULE'S OTHER DIRECTION.** "One import path per class" forbids two paths to one class. The
domain surface produces the INVERSE — **one path bound to two classes** — and that is forbidden too,
at the scope the surface creates: **no `adcp.types.<domain>.<Name>` may name two declarations.** §4's
collision rule settles a name inside one MODULE, and a domain is many modules. It is the same rule
at a wider scope, and its answer is unchanged: all N colliders lengthen.

**WHAT THE SURFACE EXPORTS: every document ROOT and every union BRANCH, and not every class.**

**The export set is read off the RUN's own record** — `ir.Module.exports`, written where a
position's hop and its declaration are both in hand. A reading over the emitted TEXT has to spell
"branch" as *a class one of whose bases this module declares*, and that misses every case of a
nested `A | B` union, which subclasses nothing local. The roots the record reports are exactly
this section's "every portable document contributes a symbol", read from the other end.

**Exporting every class the tree declares is refused.** It makes one domain name stand for many
unrelated declarations, most of them not identical-body. A name that means fourteen things is not
a surface, and the genuinely different classes behind such a name are inner structures of one
document each — a consumer reaches them through the field whose annotation names them, which is
the path the document itself gives.

Roots and branches are exactly the set a consumer must be able to NAME: a root to construct or
validate a message, and a branch because a union hands one back and `isinstance` is the question
the rewrite exists to answer. Their collisions are nameable and lengthen under the rule above.

A D2 `Annotated` alias is a name an application writes, so the distinct type aliases are
exported with the same rule. The per-module `strict_validate` helpers are not: a domain name
cannot stand for hundreds of functions, and a caller reaches one through the class it belongs to.

**`adagents` is a domain.** `adagents.json` sits at the tree's root with no directory
beside it, so the derivation answers one more domain than the directories suggest. It gets
`adcp.types.adagents`. §10's layout rule is untouched — that rule is
about a document whose path is ALSO a directory's, and this one has no directory.

The bundle directory is an argument (`python -m codegen.emit --bundle <dir>`). Nothing reads a
hard-coded path, so a second bundle version can be generated beside the first.

### A patched bundle is a legitimate input, and the test is the RECORD

Upstream repairs land on upstream's schedule, and some of them cost this SDK a type name at
hundreds of sites. So the bundle we hand the compiler may be a PATCHED copy of the published
one — but only under a condition that makes the patch provable rather than a judgement:

**A patch is admissible exactly when no patched document's record differs from the published
document's record at a key that decides acceptance.** A key decides acceptance when the keyword
table says it does: `bundle.is_an_annotation(keyword, position)` is the predicate, and it is the
one `record` already reads to settle a `$ref`'s sibling, so the line is the table's and not a
second judgement.

That is a mechanical check with the machinery §3 already builds. `record` inlines every
cross-document `$ref`, so extracting a repeated subschema into its own document and referencing
it is the INVERSE of what `record` does: resolve the patch and the original comes back at every
key a validator can act on, or the check names the pointer and the keyword.

**Byte-identity is not the instrument**, and the condition is not written in terms of it. `record`
inlines a reference's target WHOLE, so a site that comes to reference a **titled**
`core/currency-code.json` takes that document's `title` and `$schema` into the record where the
published site had neither — a difference no validator can act on. Byte-identity measures the
record's bytes when what it is protecting is the accepted set, and the accepted set is exactly the
keys the table calls acceptance-deciding. So **every record difference a patch introduces is a GAIN
of `$schema`, `title` or `description`, and no difference a validator can act on — nothing lost or
changed at any pointer.** A patch that adds a name is admitted; a patch that moves one acceptance
key is not.

What that admits, and it is the whole of the ergonomic win: **naming.** Extracting
`{"type": "string", "pattern": "^[A-Z]{3}$"}` into a titled `core/currency-code.json` and
referencing it at every site changes no instance's validity, so `strict_validate` still
decides exactly what the published protocol decides — and §5's `$ref` row turns those sites into
an import of one named type instead of a copy of a digest at each.

What it forbids, and this is the line the condition draws: **anything that moves the accepted
set.** Adding a `minItems: 1` a document omits changes the record, fails the check,
and must go upstream — because `strict_validate` would then accept or refuse differently from
the protocol, which is the one thing §2's first principle cannot survive. A patch that changes
acceptance is not a patch, it is a fork of the protocol.

**Every patch is also the upstream pull request.** The patch set is the diff we ask upstream to
take, so carrying one is a way of shipping the fix early rather than a way of living without it,
and the patch disappears when the backport lands. A patch with no filed issue behind it is the
same defect as an exemption with no issue behind it, which §9 already names.

---

## 2. Design principles

**THE VOCABULARY IS COMPUTER SCIENCE'S, and a word outside it is not a shorthand.** These documents
say *compile*, *emit*, *value*, *validate*, *branch*, *type*,
*structure*, *constraint*, *reference*, *position*, *keyword*, *declaration*. A word that merely
gestures at a technical idea is banned, because it lets a sentence read as decided while leaving
the decision unmade — a reader cannot check "the form it takes" against anything, and two readers
will not agree on it. **"Shape" is banned**: it stands in for *type*, *structure*, *case* and
*structural branch*, four distinct meanings behind one word, and a sentence needing one of those
says which.

**Two more are banned for the same reason.** *"Arm"* is a **branch** — a
member of a `oneOf` or `anyOf` is a branch, the class emitted for it is a branch class, and §4's
dispatch sources already say *branch*. Nothing is gained by a second word for one concept, and
`_branch_models`, `_BRANCH_DISCRIMINATOR` and `…Branch<N>` all say which word the code uses.
*"Set"* is a **set** — the portable set, the declared set, the set a check ranges over.
A count is stated over a set, and `bundle.portable` returns one.

**"RUNG" AND "LADDER" ARE BANNED, AND THE WORD NAMED A TYPE ERROR RATHER THAN A SYNONYM.** It named
**two different structures** in this tree, and naming them alike
asserts a relation between them that does not exist:

- **§2's widening order is a CHAIN — a totally ordered set — over five types, ordered by
  INCLUSION OF THE ADMITTED VALUE SET**: `KEYWORD ⊆ TYPE ⊆ JOIN ⊆ CONTAINER ⊆ TOP`. A handler
  that cannot render a fact takes the **LEAST WIDENING** it can render. `Any` is the order's
 **greatest element**, which is why no node runs out of renderings — a property of the order,
  not of a metaphor. "Monotone", "terminates", "least" and "greatest" are the words this is made
  of, and all four are checkable.
- **§4's branch naming is an ORDERED LIST OF CANDIDATE NAMES, resolved by FIRST FIT.** A
  collision means the candidate did not identify the branch, so the next candidate is taken. The
  last is the **DEFAULT CASE**, and it is the one that mints `<Base>Branch<i>`.

**Position means something different in each.** In the chain,
position means *admits at least as much*; a move along it changes what the class accepts. In the
candidate list, position means *is preferred*, and §4 already states that **a name is not an
acceptance fact** — so a move along it changes nothing an instance can observe. The two share no
code.

The ban is on the word, in these documents and in the identifiers. `Rung` is a **`Widening`**,
`LADDER` is the **`WIDENING_ORDER`**, and `spell_the_rungs` returns **candidates**.

**AND "UPSTREAM" NAMES TWO DIFFERENT ARTIFACTS, WHICH THESE DOCUMENTS DISTINGUISH AT EVERY USE.**
**The BUNDLE** is the schema repository and what it publishes: an upstream issue, an upstream ask
and an upstream attribution are all about it. **Upstream's WHEEL** is the Python package upstream
ships, which is what `final-state.md` reading 10 is stated over. A sentence about one of them says
which.

### Where the `oneOf` entailment is derived

§5's `type` row says an enclosing `oneOf` applies a type word it does not state. **The derivation
belongs in `adcp.types._base.applied_schema` and nowhere else**, and the two other readers derive
from it rather than restate it.

`bundle.constrained_to_object` already works that way and its own docstring says why: that
function is what the RUNTIME resolves a class's `__adcp_schema__` through, "so deriving the
lowering's answer from it is what makes it impossible for the emitter to admit a node whose class
would then be narrower than the schema it names. Two spellings of 'which hop keeps the instance'
is precisely how that divergence would arrive, and it would arrive silently."

So the entailment is one sentence in one function, and the walk inherits it. `harness._entails_type`
is the third reader and its combinator case must derive from the same function rather than require
a STATED word on every branch, which diverges from it.
§9 permits it: `adcp.types` is the emitted package reached as a consumer reaches it, and
`_base.applied_schema` is the runtime's, not the walk's.

Three readers, one derivation. A row that adds the entailment to a parser and leaves the other two
alone has written the second spelling, whatever the measurement says that day.

### The intersection is idempotent

`allOf` applies every conjunct to the same instance, so a conjunct already in the composed list
states nothing a second time: **A ∧ A ≡ A.** A merge that appends a base's reference appends it
only where the list does not already name it.

Idempotence is a property of the one member a merge appends and not of the base list.
Deduplicating the bases would leave a node no document states standing for §8's document-side fold
and for every refusal pointer below it, which §9 forbids — "do not decide a position the bundle
does not hold from a view of it". Two merges can each be right about their own pair while neither
asks whether the conjunct is already there, and a class whose base list names one class twice is
one Python refuses to build.

The composed list stays a LIST and not a set. Its order decides the pointer a nested class is
stamped at, so idempotence is a property of the one member a merge appends and not a set
conversion of the whole.

### A generated region of a plan document is its rendering, not an edit

Both plan documents are blob-compared on every delivery, and a lane may not edit either. **A
region between `<!-- begin generated -->` and `<!-- end generated -->` is exempt, because a
keyword decision lives in `codegen/keywords.py`'s cell and the grid is its rendering** — a lane
that moves a cell and regenerates has changed the decision in the one place §5 names for it, and
the row following is the table agreeing with itself.

The exemption is narrow and testable: the diff must lie wholly inside a generated region, and it
must be exactly what `pytest tests/test_keywords.py --write-grids` writes. A row that moves
without its cell moving, or prose outside the markers, is an edit and is refused. `test_keywords.py`
holds the equality in both directions, so a hand-written row reddens it.

Prose is hand-written. The cells are the compiler's, read by four readers, and the grid is what
they render to.

### A refusal is the document's; a broken invariant is ours

A `Refusal` names a fact about the document — a keyword it states that no row reads yet
(DEFERRED), or a thing the document itself says that admits nothing (VERDICT). **Where the
compiler cannot proceed for a reason that is not a fact about the document at all, that is not a
refusal and must not be reported as one. It raises.**

Two nodes of one document deriving one class name is a fact about `lower/names.py`. A base
ordered before its own subclass is a fact about the MRO this compiler builds. Neither is anything
the document's author could read, act on, or fix, so neither may be reported as the document's
obstruction.

The practical test is the report line. If a reader of the refusal would go to the schema to
understand it, it is a refusal. If they would go to `codegen/`, it is ours, and an exception at
the pointer is both louder and honest where a refusal is quiet and wrong.

This is why an unreachable case guarding a compiler invariant needs no `Refusal.kind`: the
question "is this a verdict or a deferral" does not apply to it, because it is neither. `kind_for`
answering DEFERRED for such a case is not the table being wrong — it is the case being the wrong
case.

### The schema decides acceptance

Every emitted class carries `strict_validate`, which validates a payload against the class's own
schema document before constructing anything. The model is not the authority on what the protocol
accepts; the document is.

*Why.* Pydantic and JSON Schema do not agree on every edge, and where they differ the document
wins — it is what the other side of the wire was written against. A model may therefore be looser
than its document without being wrong, because the schema half already refused the payload. It
must never be *tighter*, because then we refuse something the protocol permits.

This principle is what makes the widening rule at the end of this section possible, and the two
are one statement read twice: if the document decides acceptance, then a fact the annotation
drops costs precision and not correctness, and the only annotation that can be wrong is a tight
one. Every approximation below is therefore a loosening, and the check that guards it (§8's
accepts) is a check for tightness.

### Constraints bind to the type, not the field

A bound belongs to the thing it constrains:

```python
Annotated[int, Field(ge=1, le=100)]
```

not a `Field(ge=1)` sitting beside a bare `int` on one class. The constrained type is then
reusable: it nests into `list[...]`, into a mapping value, into a union branch, and into another
document's field, carrying its bound with it.

Two choices, in order of preference: a standard Pydantic type where one says exactly this
(`NonNegativeInt`); otherwise a named alias in `adcp.types.constraints`, its name derived from
the constraint and from nothing else (`StrMinLen1`, `FloatGt0`, `NonEmptyList[T]`; a `pattern`
contributes a digest of itself). An alias in `constraints` names a *constraint*, never a concept
— `NonEmptyList[T]`, not `MediaBuyStatusList`. **Every constrained scalar is named**, including
one the bundle states at a single site. A constrained container is generic over its element and
is named once for every element (`NonEmptyList[T]`); where a field holds the container the
annotation is written on that field's type.

*Why.* A bound written onto a field exists only at that field. The same bound reached through a
list, a mapping or a branch then has nowhere to live, and the usual repair is to put it on the
field holding the container — which constrains the wrong thing. On a union branch that repair is
actively wrong: the field also holds the other branch, so a bound there refuses values the
document accepts.

*Why every one.* Naming only the types that recur needs a census over the run, and a census
makes one document's module a function of which other documents the run includes: a run over
one document and a run over the bundle would emit different text for the same document. A name
that is a function of the constraint alone has no such coupling, and the cost — a name for a
constraint stated once — is a name a reader can derive from the constraint it spells.

### Rules are after-validators, written once

A keyword that spans fields, or spans a collection, has no field-level annotation that can carry
it. Those become rules: an after-validator in `src/adcp/types/_runtime.py` reading a class-level
tuple the emitter writes. The families are `oneOf`/`anyOf` over `required` or over pinned
values, `if`/`then`/`else`, `dependencies`, `minProperties`/`maxProperties`, `uniqueItems`,
`not`, and `contains`.

**Rule placement.** Declare a rule on the nearest enclosing class, which can read sibling
fields. Where no class encloses the value — a root array, a mapping value, a `definitions`
entry, a union branch — declare it as an after-validator on the value's own annotated type
(`AtLeastOne`, `NotValue`, `Distinct`).

Placement determines where a rule is declared, not which members it reads. A rule declared on a
value reads that value's own members, as a rule declared on a class reads its fields. A rule
naming keys — `ForbiddenGroups`, `RequiredGroups`, `PresenceGroups` — is therefore valid as an
after-validator wherever no class encloses the value.

**A composing DECLARATION is not a position where no class encloses the value.** A property whose
declaration is an `allOf` still sits in the class that holds the
property, so the clause above is unchanged and the rule is declared there — the reader that
writes it must see through the composition rather than the rule move to the value's own type.
A value keyword's own gate is what has to read a conjunct: carrying the rule on the composition
instead would declare it on the value's annotated type, which this clause reserves for where no
class encloses it, and one does.

The same reading answers it for every value keyword that composes, which is why it is stated here
and not per keyword. `contains` is the exception already recorded in §5's two-array clause, and
for its own reason: a declaration holds one `contains` key, so two cannot be spelled in a merged
declaration at all.

A rule's condition tests membership as well as equality: a `Match` clause reads a property's
`const` or `enum`, and also `value in field`.

*Why written once.* A generated validator body is code we would generate and then be unable to
review. A hand-written validator reading generated data is reviewed once and exercised by every
document that needs it.

### Composition merges by intersection

An `allOf` of `$ref`s makes those classes the bases. Where two composed schemas constrain the
same property, the field carries the **intersection**: an enum is the intersection of members, a
bound is the tighter one.

A composed class's `required` is the union of its own and every base's. An emitted class
redeclares an inherited field in exactly two cases. Where composition makes an inherited field
required, the subclass redeclares it with the base's type and no default. Where the subclass's own
document **restates the property with a different `default`**, it redeclares it with the base's
type and that default: a default is a value and not a constraint, so it neither widens nor
narrows what the class accepts, and the schema that states it is the one that decides. A
redeclaration that changes the TYPE is a build failure.

*Why intersection.* `allOf` means every conjunct holds. A union of their constraints would accept
payloads a conjunct refuses, making the model looser than its document.

### `extra` follows the schema, and nothing else

`additionalProperties: false` → `forbid`. `true` → `allow`. A typed `additionalProperties` →
`allow` with a typed `__pydantic_extra__`. **Absent → `ignore`.**

Absent and `true` are different statements. `true` says additional properties are part of the
document, so they are retained. Silence says only that they are permitted, so they are accepted
and dropped — retaining a property the document never mentions would be the SDK adding a claim
the schema does not make.

A consumer wanting stricter or looser behaviour sets it on a subclass. No generated class carries
a policy that is not in its document, and nothing reads an environment variable to decide.

### Nothing rewrites emitted output

A defect is fixed in the schema input, or in the compiler, before the output is written. There is
no post-processing pass over generated files.

*Why.* A rewriting pass is a second source of truth for the output's structure, and the two drift. It
also hides which input produced which line.

### The compiler is pinned, and a gap in it is fixed in it

The pipeline is `f(schemas, pinned compiler)`, and both arguments are ours to change: a defect is
fixed in the schema we hand it, or in the compiler itself. A fix we carry is offered upstream as a
pull request, and a fork exists only once something needs one.

*Why.* The alternative to fixing the compiler is working around it at the call site, which means
the workaround has to be understood by everyone who later reads the output and cannot find the
rule that produced it.

### An annotation is admitted by name

A keyword that cannot constrain an instance compiles to nothing, and is admitted by an explicit
**name** — not by a pattern over its spelling, and not by ignoring whatever is unrecognised.

*Why by name.* Silence cannot distinguish "this keyword carries no acceptance meaning" from "this
keyword constrains instances and we have not implemented it". The first is correct; the second is
a model looser than its document. Naming each one makes the first auditable and leaves the second
loud.

### A keyword we cannot express widens the annotation

**ZERO REFUSALS IS THE OUTCOME. Every schema is represented as a Python class; where it cannot be,
the reason is approximated and the upstream issue is raised.** A keyword we have no compilation for
therefore widens the annotation, and it never refuses the document: the first principle of this
section is that the model is not the authority on acceptance — `strict_validate` runs the document
before anything is constructed, and the document decides. A model looser than its document claims
nothing it does not enforce, because the schema half has already refused the payload. The widened
annotation costs **static precision**, not runtime correctness.

Two cases survive, and the design keeps both.

- **A narrowing.** An annotation tighter than its document refuses a payload the protocol
  permits, and `strict_validate` cannot repair it: the schema half admits the payload and the
  construction then fails. A narrowing is the defect this rule is about, and nothing below widens
  into one.

 **A narrowing taken on purpose is admitted by an ENUMERATED registry and by nothing else.**
  The registry is the authority, this sentence is not, and a narrowing absent from one is the
  defect above. Each entry is compared by equality so it admits that fact and not its kind — a
  rule admitting "the sort of bound a URL type adds" would be invisible and permanent.

 **A registry is a DECISION where no other check can report its edit, and a decision must be
  read by a test.** That is the discriminator between a decision and a
  mechanical lookup, and it is the reason the distinction can be measured rather than argued:
  a lookup's error surfaces somewhere else — a wrong `_TIGHTER_BOUND` direction loosens the
  composed bound and the pair reports `added` — while a decision's edit is silent everywhere.
  `tests/test_decision_set.py` holds the guard, with both sides of every pin derived.

 **A per-pair reading cannot see one of these edits, which is why the guard measures REACH.**
  Removing a keyword from an admission set moves no per-pair verdict: every pair grades exactly as
  it did. So the guard switches each admission mechanism off in turn and pins which keywords
  reappear.

 **THE TWO URL TYPES STAND.**
 **THE BUNDLE IS WRONG ABOUT URLs, and that is the whole premise.** It spells "a URL" many
  different ways across its `uri` positions — a bare `format: uri`, an `^https://` pattern, a
  length bound, several combinations — for what is one concept. **Where the schema states one
  concept inconsistently, the SDK states it consistently**, and consistency across the bundle is
  what a consumer experiences. There are exactly **two** URL types and there will not be a third:
  `AdCPUrl` where the document pins `^https://`, which is the agent-facing form, and `HttpUrl`
  everywhere else, which is the identity form.

 **SO THE NORMALISATION IS A NARROWING TAKEN ON PURPOSE, not a defect**, and §2's rule about
  deliberate narrowings applies to it in full: it must be **admitted by the enumerated registry
  and by nothing else**, because an unadmitted narrowing is invisible and permanent. The
  registry's own mechanism does not express it yet — an entry is compared by equality so that it
  admits one fact and not its kind, and a normalisation is a kind — so **the mechanism is what
  changes, not the decision.** Until it does, the narrowing is live and unadmitted, which is a
  defect of the registry and not of the type.

 **A reading that finds code contradicting this section reports it and does not change either
  side.** A registry entry is a decision even though it is not in this document.
- **No document of record.** Where the record (§3) is undefined, there is no schema half at all,
  so `strict_validate` has no authority to run and the annotation is the only claim there is.
  That is the one case where a partial model really would claim conformance to a document it
  does not enforce, and it is the one refusal this compiler can still mint. §7 names its three
  cases and says what each is measured at.

#### Direction: every approximation of acceptance is a widening

A fact the annotation cannot carry is **dropped**, never substituted. Dropping a constraint
widens the admitted set and can do nothing else; substituting a "nearest expressible"
constraint could narrow, so substitution is not available. The handler takes the **least
widening** it can render in one **chain of five, totally ordered by inclusion of the admitted
value set** — finite, monotone, and terminating at its greatest element:

1. **KEYWORD** — drop the one keyword, keep the type. (`uniqueItems` where no class and no
   named type hold the rule → `list[X]`.)
2. **TYPE** — drop a type selection the constraints contradict, keep the constraints.
   (`format: uri` beside `maxLength` → the constrained `str`, the format riding as
   `json_schema_extra`.)
3. **JOIN** — replace a type with the union of the types it holds. (A list-valued `items` →
   `list[A | B | …]`, dropping position and arity.)
4. **CONTAINER** — replace the node with its bare container: `list[Any]`, `dict[str, Any]`.
5. **TOP** — `Any`.

`Any` admits everything, so `TOP` is the chain's **greatest element** and no node can run out of
renderings. **Which widening a keyword takes is the keyword's decision and lives in its cell
(§5), never at the site that widens.**

A narrowing is not discouraged here; it is a **failing check**. §8's accepts construction covers the
node's admissible space by constraint class, so a type that refuses any value the document
admits is reported with the value. Where a widening would still leave a narrowing — the type
word itself refusing what a constraint admits — the type widens by another widening, to `Any` if
nothing else carries it.

#### An approximation is declared, and it is local

A refusal propagates: a parent returns it upward unchanged and the document emits nothing. An
approximation does **not**. It is a property of one node, the document still emits, and the
approximation travels upward only to be **accumulated** — a refusal is absorbing, an
approximation is additive. Every one carries its document, its pointer, the keyword whose fact
the annotation does not carry, the widening it took, that fact in the document's own spelling, and
an **attribution**. Nothing is approximated by silence: an undeclared widening is a defect and
§8 reports it as one.

#### One kind of approximation

**There is ONE kind: WIDENED.** The annotation admits a value the document refuses. The
schema half refuses it, so acceptance is unharmed; what is lost is what the type says, and §8's
CONSTRUCTION proves each one by handing the class a value the document admits.

**A difference no construction and no dump can observe is not a fact about the artifact**, and is
therefore not a kind. A union whose branches §4's dispatch cannot separate admits exactly what the
document admits where the combinator is `anyOf`, and which branch an overlapping payload becomes is
a property of declaration order that nothing can observe. An inseparable `oneOf` is different and
stays WIDENED: there the model admits a payload the document REFUSES, and the construction shows it.

#### Attribution: ours, or upstream's, and the issue is a reference

§9's rule — "an exemption names an upstream issue, or it is this SDK's own decision and belongs
in this document" — governs every approximation, and the attribution is a choice of two and not
a free-text note:

- **Ours.** The design decided this widening; the sentence is the keyword's own row in §5, §6 or
  §7. The attribution is therefore the **cell's own address** and is derived, not stored: a
  reader goes from a widened field to the row that decided it, and that row says why.
- **Upstream.** The document could state the fact and does not, or states something no draft-07
  reading can carry. The attribution is an **issue reference**, and it is a property of a
  document and a pointer rather than of a keyword — the same keyword widens by our decision at
  one site and by an upstream defect at another. It therefore lives in one registry keyed by
  document, pointer and keyword, and an entry with no issue is a build failure rather than a
  missing field.

**Ours is work this project can do and must fall to zero. Upstream falls when an issue closes.**
Summing them would report someone else's backlog as ours, which is the second half of §9's rule.

#### What is counted, and over what

Three figures, three denominators, never summed (§8 states the grading side of each):

- **Emitted, over the set.** Every portable document of the bundle emits, and its
  complement is the one irreducible class above — no document of record. This is a partition and
  it is the exit condition: *refused* is zero.
- **Round-trip failures, over the graded pairs.** A pair where the class refuses a value the
  document admits, or where the dump is a value the document refuses. Pinned at zero, because
  either one is the defect that matters.
- **Approximations, over the declared set**, split by attribution. This count moves with
  emission, so §9 forbids pinning it; it is reported, and its `Ours` half ratchets down.

The approximation count is **not** a partition of the set the way *emitted / refused*
is: one document carries many and most carry none. The number of documents carrying at least
one is a different figure over a different denominator, and the two are never added.

---

## 3. Walking the tree

A document is walked once. Every node is reached at exactly one **position**, and a keyword's
compilation depends on the position as much as on the keyword.

| position | the node is |
| --- | --- |
| ROOT | the document root |
| PROP | a value of `properties` |
| ELEM | an array's `items` |
| MAPV | a mapping's value schema (`additionalProperties`, `patternProperties`) |
| KEY | a mapping's key schema (`propertyNames`) |
| BRANCH | a branch of `oneOf` / `anyOf` |
| CONJ | a conjunct of `allOf` |
| RULE | inside `not`, `if`, `then` or `else` |
| DEF | an entry of `definitions` / `$defs` |

RULE is the position that changes a keyword's meaning most: under a conditional, a keyword
describes what a rule *tests*, not what an instance must be, so no type is lowered from it.

A DEF entry is decided as its own kind under the name `<Root><Key>`, so a DEF answer is the
entry's own position's answer. An entry nothing references is not declared.

One dispatch seam decides a node's kind, so every position reaches the same reader for the same
case. **Every node reaches a lowering**: the seam is total, because a keyword the handler
cannot render widens the annotation by §2 rather than refusing the document. The one refusal
left is the record's own — a document whose references cannot be inlined has no record, so
there is nothing for the walk to read and nothing for `strict_validate` to validate against.
`Refusal` therefore lives with the bundle reader that mints it, not with the lowerings.

### The document of record

What the walk reads, what `strict_validate` validates against, and what §8 grades against is
one document: the bundle's document with every cross-document `$ref` replaced by a copy of its
target, and **nothing else changed**. Resolution inlines; it does not rewrite. No keyword is
dropped, derived, reordered or restated in another spelling, on the referring node or on the
inlined target.

*Why.* A resolver that canonicalises while it inlines — an `enum` of both booleans for a
`bool`, a `const` for a `null`, a bound derived from a sibling, an annotation dropped — writes a
document the bundle does not state, and every reader downstream then grades the model against
that document instead of the bundle's. A check may canonicalise its own copy of a node in order to
read it; that copy is an instrument of one check, and it is not the document.

---

## 4. The classes we emit

### What becomes what

| the node | emits |
| --- | --- |
| an object with `properties` | a model class |
| an object without `properties` | `dict[K, V]` |
| an `enum` node | `StrEnum` / `IntEnum`, base read off the members |
| an `enum` on an untitled union branch | a `Literal` of the members |
| a `const` | `Literal[value]` |
| an array at a root | `RootModel[list[X]]` |
| a scalar at a root | a module-level annotated alias, not a class |
| a `oneOf` / `anyOf` of object types | a base plus one class per branch |
| a `oneOf` / `anyOf` of PURE VALUE SETS | ONE enumeration, of the union of the arms' members — the arms stay declared |
| a `oneOf` / `anyOf` of scalars at a root | a module-level alias over the union of their types |
| a `oneOf` / `anyOf` at a root mixing a scalar branch with a class branch | a root model over the union of the branches' types |
| a root stating no schema keyword at all | a permissive root model |

A root scalar is an alias, so it has no class to carry `strict_validate`; its module binds the
same validation as a module-level function over the same schema reference, so a class and an
alias cannot disagree about what their document accepts.

A root union mixing a scalar branch with a class branch is a **root model**: its root type is the
union of the branches' types, the scalar branch is a member type and the class branch is its own
class, and the root model inherits `strict_validate` like any class. Nothing is dropped and
nothing widens — the union admits exactly what the document admits — so this row costs no
approximation. What it costs is ergonomics: a consumer writes
`X(root=…)` where a base-plus-branches root takes the payload directly. An all-scalar root
union stays an alias.

A root stating no schema keyword at all is a registry's instance data sitting at a schema root.
Read by its own declared draft it is the **empty schema**: draft-07 ignores an unknown key, so the
document admits every instance, and a permissive root model is **faithful** to it rather than
wide. That the document is not really a schema shows up where it belongs — as an approximation at
the root with an upstream attribution, asking the registry either to drop its `$schema` or to
declare a schema — and §7 says why the keyword half of that row is not a refusal either.

Every one of these cases carries `strict_validate` against its own document by one mechanism,
so a class, a root model and an alias cannot disagree about what their document accepts.

Two nodes with identical content emit one class. Two nodes with different content never do. The
class is declared under the name of the position the walk reaches first, and every later
position of the same content binds its own derived name to that class by identity, `X = Y`. A
field is therefore typed by its own position's name: typing it by a sibling position's name would
read as one branch carrying another's type, and would make a symbol depend on which key the walk
reached first.

### Names

- **Root**: `pascal_case(title)`, acronyms kept; where the title is missing or derives no
  identifier, `pascal_case` of the document's own file stem.
- **Nested**: `pascal_case(property)` — `<Property>` for a property, `<Property>Item` for an array
  element, `<Property>Value` for a mapping value, `<Key>` for a `definitions` entry. The
  module path already carries the document, so a nested name does not repeat it.

 **A `definitions` entry takes no `<Root>` prefix**, for the sentence above it: the module
  carries the document. The prefix is what the collision rule spends when two entries of one
  module need it, not what every entry pays up front. **This is a function of the one document and
  carries no dependency on a sibling set**, so it is insertion-stable.
- **Union branch**: its own `title`; else the `const`s it pins, in the document's own key order;
  else its sorted `required` set; else, where the branch is a bare `$ref`, **the TARGET's own
  derived name**; else its **index among the branches**, `<Base>Branch<i>`.

 **These five are an ORDERED LIST OF CANDIDATES RESOLVED BY FIRST FIT**, and the fifth is the
 **default case**. A collision means the candidate did not identify the branch, so the next is
  taken. Position here means *is preferred* and nothing more: **a name is not an acceptance fact**,
  so moving along this list changes nothing an instance can observe — which is what distinguishes
  it from §2's widening chain, where moving changes what the class admits.

**A MINTED NAME SAYS WHAT THE TYPE CONSTRAINS. A DIGEST FAILS THAT AND IS A DEFECT, and
insertion-stability is not the test.** `StrMatching02AE7B1E` is stable — derived from the
constraint set, so adding a scalar renames nothing — and it is still not a name: a consumer
imports it and annotates with it, and it tells that consumer nothing about what it admits.
Stability is necessary and nowhere near sufficient. `StrMaxLen100` is a name; a hash of the
pattern is the compiler declining to find one.

**The derivation, in order, and there is no fourth step:**

1. **The constraint, in words**: `StrMaxLen100`, `IntMin0Max150`, `NonEmptyList`.
2. **Else the bundle's own name for the subject**, where the bundle names **the constraint
   itself** — a titled `definitions` entry whose subject IS the constrained scalar.
3. **Else the declaring position**, which is §1's rule for a symbol carrying no
   `__adcp_schema__` — the declaring position is its catalogue entry's home. **Two constraints
   that collide at step 1 separate here**, never by a hash of either.
4. Where none of the three answers, the type is **pending a name**, and that is an upstream ask
   stated over a named set of the bundle. **A digest is what the compiler writes INSTEAD of filing
   that ask**, which is why it is a defect and not a convention.

**THE CONSTRAINT BEATS THE PROPERTY NAME.** A constrained scalar's identity *is*
its constraint, so naming it for a concept makes the symbol a function of **which position claimed
it first**: one pattern sits at a `currency` position and at an `airport_code` position, and a
property name is right for one of them and wrong for the other, which is reading 4's
own failure in a new spelling. D5 already said it: *an alias names a constraint, never a concept.*
So a domain word is admissible only where the bundle names the constraint as its subject, which
step 2 is, and not where a property happens to carry it.

### A POSITIONAL INDEX IS A DECLARED PLACEHOLDER, NOT A NAME — AND NOT A LICENCE EITHER

An index is not the same failure as a digest, which is why the absolute form of the rule — *no
name the compiler mints contains a content digest or a positional index* — does not hold:

- **A digest is derived from the thing and tells a reader nothing.** Something else always could
  have been derived — the constraint in words — so a digest is the compiler declining to look.
- **An index is derived from the POSITION, and where the position is genuinely the only thing that
  distinguishes the branch, there is nothing else to derive from.** Nothing in the bundle names it.

So an index is **step 4's state made visible**: the branch is *pending a name*, exactly as a
step-3 constrained scalar is, and exactly as that set is filed upstream. The rule is:

**A MINTED NAME CARRIES A CONTENT DIGEST NEVER, AND A POSITIONAL INDEX ONLY AS A DECLARED
PLACEHOLDER WITH THE ASK FILED.** The gate therefore does not assert the indexed set is empty — it
asserts that **the set of index-named symbols equals the set the upstream ask names**, so an index
that appears without an ask is a defect and an ask that is answered removes a name. A placeholder
nobody has filed is the same evasion as a digest, one step further on.

**A bare `$ref` branch is named for its TARGET, and the index is the candidate after that.** The
name is the target's
DISTINGUISHING REMAINDER and never the target's own symbol spelled straight: the branch's second
base IS the target, so the module imports that symbol, and `spell()`'s `occupied` keeps a
shadowing name rather than refusing it where a chain of one segment has no ancestor to spend —
which is how a class comes to name one of its own bases twice. Where the two names share nothing,
the branch takes `<Doc><Other>`. §4 already makes such a branch inherit the target's property map
for the pin candidate, and the target is a document whose own class name this section derives — so
the name is available and the index is a worse answer.

A positional name is the one outcome a consumer cannot work with: a caller writing
`isinstance(req, AssetRequirementsBranch7)` has to count the document's branches to know that it
means JavaScript. Most of the branches that reach the index are bare `$ref`s and are what that
candidate answers; the rest are other cases — a nested registry branch, an `allOf` case, a
properties-only case, and a `not`-complement branch with the copy another document inlines.

Where the root's name and the target's share a leading run, the branch takes the root's name plus
the target's distinguishing remainder, so `core/requirements/asset-requirements.json`'s branch on
`image-asset-requirements.json` is `AssetRequirementsImage` and not the target's name repeated.
Both inputs are facts about the one branch — its root and its target — so the rule is
insertion-stable, which is what §4's own criterion asks.

**Candidate 2 reads EVERY pin the branch states, and a candidate that collides has not identified
the branch.** Both clauses are functions of the one branch, which is
the insertion-stability criterion this section already states for the nested rule — a rule
reading "the property the most branches pin" would rename every sibling when a branch is
inserted, which is forbidden.

A branch pinning a `const` on several properties derives from all of them, in the order the
document writes the keys; declining to choose between two pins gives the positional name to the
most heavily identified branches in the bundle. A branch pinning one property keeps that one pin,
because one pin in key order is that one pin.

**A boolean pin contributes no segment, because `true` names nothing.**
This is not a carve-out from the key-order rule — it is the same sentence this
section already states two paragraphs down, that `true` on both branches "names neither", applied
per pin instead of per branch. A pin identifies a branch by its VALUE, and a boolean's two values
are the same two for every property in the bundle. Where a branch pins something identifying
beside a `true`, reading every pin appends a segment that identifies nothing:
`PackageSignalTargetingBinary` becomes `PackageSignalTargetingBinaryTrue`.

It subsumes the collision case rather than sitting beside it. A branch whose pins are all boolean
contributes no segment at all, so candidate 2 answers nothing for it and it falls through, by one
rule rather than two.

Where a candidate derives one name for two branches it has not identified either, so **both fall to
the next candidate** — the collision rule above lengthens a chain, and these chains are one segment
with nothing to lengthen by. Where two branches each pin a property to `true`, the value is the
same on both and names neither, so candidate 2 answers nothing and candidate 3's `required` set
answers: what identifies those branches is WHICH property is present, which is the fact candidate 3
reads.

Candidate 2 is not narrowed to unions that derive a dispatch discriminator. That reading takes
working names away from a union no property of which is shared by every branch, and the strict
reading would send each of its branches to its index.

**A branch colliding with its own document ROOT: the root keeps the name and the branch falls to
the next candidate.** The collision rule lengthens a chain, and a root has no
chain to lengthen — D5 fixes its symbol, because a document exports one importable symbol named
for the document. So the branch is the side that moves, and it moves the same way any colliding
candidate does: to the next candidate that answers.

A document refuses for no derivable name: candidate 4 always answers, because a branch always has
an index. Minting a verdict instead is the case §2 forbids most plainly — a refusal must name a
fact about the document, and "two nodes of this document derive one class name" is a fact about
`lower/names.py`.

**AND AN IMPORTED SYMBOL IS THE SAME CASE.** A module that imports a name and then declares a
class under it leaves the name
meaning the subclass, so a consumer importing it from the two modules gets two classes with
different `__adcp_schema__` pointers. The reasoning above transfers exactly and is stronger: a
root keeps the name because D5 fixes its symbol, and an imported symbol is fixed more firmly
still — it is ANOTHER document's name, which this module has no standing to move. **So the
colliding branch falls, and the import keeps the name.**

**The rule reaches both of §4's axes.** A position whose name is occupied is colliding when
deciding whether to LENGTHEN *and* when deciding whether to FALL; honouring it on the first axis
alone reads "cannot lengthen" as "resolved", which is exactly what a bare-`$ref` branch at
candidate 1 hits — it is a chain of one with no ancestor to prepend, and it has three candidates
still underneath.

**Collision.** The nested rule above is the LAST path segment, so two positions
of one module can derive one name — `brand.properties.context` and
`artifacts.items.brand.properties.context` both derive `Context`. Folding every hop to the root
and concatenating makes a name unique by construction, which is not what this section asks for:
the module path already carries the document.

The rule is:

1. Every position derives its short name by the rules above.
2. Where **N positions of one module derive the same name, ALL N lengthen** — each prepends its
   own nearest ancestor segment — and the step repeats until every name in the module is unique.
3. A position whose short name collides with nothing keeps it.

**All N lengthen, and that is the whole of why this is order-independent.** Lengthening only the
later collider would make the public symbol a function of which position the walk reached first,
which §9 forbids and which `names.adopt` already refuses for the same reason: a field must never
be typed by a *sibling* position's name. Lengthening all of them makes each name a function of
the SET of colliding positions, and that set is a function of the one document — so the name is
recomputable after the walk, and no census over the run enters.

The DEDUP is confined to one module, never compared across modules, because a name's module is
its namespace.

**The COLLISION rule is not, for a name §1 exports.** §9's prohibition is about the RUN and the
collision scope is the BUNDLE. So: one module for every position, and **the domain
for a position the surface exports**, read off the bundle and never off the run's document set.
`names.COLLISION_SCOPE` states it beside `names.SCOPE`, which keeps the dedup's scope unchanged.

*What this costs:* a long name becomes the exception it was meant to be, arising only where one
document genuinely says `context` twice. The failure it avoids is the one the upstream v9 SDK
shows: numbered variants, `WholesaleFeedEvent1` through `WholesaleFeedEvent9`, because a numeric
suffix carries no information about which position it names, where an ancestor segment does.

**The two fallbacks neither widen nor narrow.** A symbol is not something a document states about
an instance, so deriving one from the document's own path or from its own branch order costs no
approximation. Both are functions of the one document — the file stem is the
same whichever documents the run includes, and the branch index is document order — so §9's rule
against deciding a document's output by a census over the run holds. A title is still preferred
wherever one exists, because a derived name reads worse; its absence is not fatal.

### A union root: the base, the branches, and how a payload reaches its branch

A `oneOf`/`anyOf` root emits a **base** carrying `BranchDispatchMixin` plus **one class per
branch**, and the base's name is what every referrer imports. A branch whose schema is a `$ref` is
a class with **two bases**: the target, which supplies the fields, and the union's base, which
supplies the dispatch.

**AND WHERE THE TARGET IS ITSELF A UNION ROOT, THE BRANCH DISTRIBUTES — THE SAME RULE §5's `$ref`
ROW ALREADY DERIVES AT CONJ, APPLIED AT BRANCH.** "The target supplies the fields" is true exactly
while the target declares fields of its own. A dispatch root declares none: every property sits on
its branches, so a two-base class over it inherits an empty field set, dispatches nothing — the
union is carried by the class that *declares* `_branch_models` and the derived class does not — and
`extra: ignore` then drops the whole payload. A class that admits a value and dumps `{}` is the
observable form of it.

Conjunction distributes over disjunction, so this branch is not one class but **one per branch of
the target**: `(A | B | C) and D` is `(A and D) | (B and D) | (C and D)`, each product a class
whose bases are one of the target's branches and the enclosing union's base. Every product
declares fields, every one dispatches, and `isinstance` holds against both bases — which the
alternative of binding `_branch_models` onto the derived class does not, and which is why that
one-line form is refused.

**This is not a new rule and it owes no approximation.** §5's `$ref` row states the distribution
for a union root beside a node that declares fields, including that a product whose intersection is
empty is DROPPED and that the node refuses only where every product is. BRANCH differs from CONJ in
one respect only: the other side contributes the dispatch rather than a field set. The names come
from §4's branch candidates with the enclosing conjunction as the parent, so each product is named
for what distinguishes it and not for its position.

**The condition is the target's own field set, not whether it dispatches**: a target root that
dispatches AND declares properties of its own is the ordinary case and the two-base rule is right
for it.

**THE PRODUCTS ARE NAMED FROM §4's BRANCH CANDIDATES WITH THE BRANCH AS PARENT**, and the first
candidate falls past the symbol the product's own base import already holds — so a product whose
target branch is titled is named by the **`const` it pins**, which is what distinguishes it both
from its sibling product and from the class it subclasses. No new naming rule and no index.

**AND THE DISTRIBUTION IS RESOLVED AFTER THE DISPATCH DERIVATION AND BEFORE THE NAMES.** §4's
derivation and §8's third equality range over the branches **the document writes**, so a union that
distributes keeps whatever separability declaration its own branch list earned. Distributing first
would re-derive dispatch over classes the document does not state and move a declaration no
document changed.

Four mechanics make it work, each because one of the others does not reach a path:

- **`__get_pydantic_core_schema__` on the mixin returns the branches' union**, which covers every
  path Pydantic validates *through*: a nested field, a `TypeAdapter`, `model_validate`.
- **`__new__` on the mixin covers `Base(**data)`**, which no schema can reach, because
  `BaseModel.__init__` validates with the object already allocated. Direct construction therefore
  validates twice and is idempotent; `model_validate` stays single-pass.
- **The class that gets the union is the one that *declares* `_branch_models`.** A class that
  inherits it keeps its own schema, which is the whole of subclass support: a branch keeps its own
  schema, and so does a consumer's refinement declared elsewhere.
- **The union is the validator, not the serializer.** In the serializer slot the class has no
  serializer for an instance of itself: the union's serializer matches no branch, infers a model,
  finds the same union and recurses. So the serialization slot carries a wrap serializer built
  from the plain model schema the class would otherwise have had, which terminates.

 **The serialiser dispatches on the instance's own class, and each class serialises through its
  own plain model schema.** A branch serialises the branch's fields; a base serialises the base's.
  That is not a union in the serializer slot at all, which is why it terminates — there is no
  case to fail to match and nothing to infer. Neither reading that loses data is available: the
  base's plain schema alone drops a branch's own fields where a BRANCH is reached through a
  base-typed field, and a union of the branches plus that schema leaves a BASE instance matching
  no case under a smart union and falling through to the circular reference the mechanic exists to
  avoid. The invariant both break in one direction is that **a value serialises as what it is.** A
  base instance is a legitimate value, because `__new__` covers `Base(**data)` and validates it,
  so the slot owes it an answer rather than treating it as unreachable.

The emitter writes three facts onto the base that are not recoverable at runtime: `_ROOT_REQUIRED`,
the fields the root requires as opposed to the ones that select a branch; `_BRANCH_DISCRIMINATOR`,
the property every branch pins a `const` on (the first dispatch source below), which the mixin
reads to build the discriminated union, and which is empty where dispatch is the third source or
is declaration order; and `_branch_combinator()`, `anyOf` or `oneOf`, because a **validation
error** has to name a JSON Schema keyword and a payload satisfying no branch fails each branch at
field validation, where Pydantic reports `missing`. (That is a runtime refusal of a payload, not
§2's refusal of a document — the compiler refuses no document for a union.)

Branches subclass the base, so they do not exist while the base is built: the hook returns the
base's own schema then, and the declaring module calls `model_rebuild(force=True)` afterwards.

**Every keyword beside the combinator compiles onto the base, and every branch inherits it**, with
the four exceptions §8 names. Draft-07 applies a root's `properties`, `required`,
`additionalProperties`, `allOf` and rule
keywords to the same instance a branch describes, so they compile as they would on any class —
fields, `extra`, bases, rules — onto the base, and a branch composes its own with them. A root
`properties: {}` beside a union declares no field and contributes nothing. §8 says how a branch
class is then compared: against its branch node read under the root's siblings, so an inherited
field is a fact the branch's node states.

**Which branch a payload is, is derived from bundle data, never from a hand-written map.** Three
sources, in order:

1. **A `const` every branch pins on one shared property AND every branch REQUIRES.** The union
   carries `Field(discriminator=<property>)` and the key alone selects
   the branch, so Pydantic reports against that branch rather than against all of them.

  **PINNING IS NOT DETERMINING, and the requiredness half is the whole of the rule.** A
   discriminator is a total function from the instance to one branch. A pin on a key the branch
   lets an instance OMIT determines nothing when the key is absent, so such a key is not a
   discriminator and this source does not apply — the union falls to source 3. Pydantic raises
   `PydanticUserError: needs field <key> to be of type Literal` on an `Optional[Literal[...]]`
   discriminator for exactly that reason; it is refusing an undefined function, not imposing a
   limitation of its own, and there is nothing to work around. Reading the key ourselves in
   `BranchDispatchMixin._dispatch` fails identically: an absent key cannot be read.

  **The two predicates agree wherever the pinned key is required**, so testing the weaker one
   passes nearly everywhere and fails only where a document pins a key one branch lets an instance
   omit.

   A `oneOf` whose branches pin distinct values requires the key by implication — absent, the
   instance matches several branches and `oneOf` admits none — so the entailment, not the
   `required` list alone, is what this source reads.
2. **A key the bundle's manifest states.** `manifest.task_result_resolution` names the
   discriminator field and a template resolving a schema from it, and `manifest.tools` is the
   table. Such a union emits as a mapping keyed by that field: its discriminant is in the
   envelope, not in the payload.

   **THE KEY MUST BE READABLE AT THE UNION'S OWN NODE, AND THAT IS WHAT THIS SOURCE APPLIES TO.**
   The manifest naming a field is not the condition — a document whose branches ARE the documents
   the template resolves still has to state the key where the dispatch happens. Where the union's
   own node neither declares the field nor is itself a document the template resolves, the
   manifest names a discriminant that is in the ENVELOPE and not in this payload, and **source 2
   does not apply**: the branch is selected by the caller's envelope, so a class dispatching on it
   would read a key no instance it validates carries.

   That distinction is the whole of this source's set. A root whose branches are the resolved
   documents, which does not itself declare the key, reaches source 2 — the key selects the
   BRANCH. A root that is merely named in the table does not.

   **AND WHERE SOURCE 2 APPLIES, THE UNION OWES NO SEPARABILITY DECLARATION.** A declaration
   says the derivation could not separate the branches; the manifest separates them. A root
   carrying both is stating two incompatible things about itself, and the declaration is the one
   to go.
3. **Branches no instance satisfies twice.** Where the branches are pairwise disjoint, the
   payload selects its own branch and the order they are tried in cannot change which one it
   reaches. Disjointness is derived from the branches themselves: one property pinned to
  **disjoint value SETS**, a `required` name one branch declares and another forbids, **one
   branch forbidding a VALUE another pins**, or scalar branches of different `type`.

  *The first separator reads SETS and not single values.* An `enum` is a
   set of pinned values and a `not: {"enum": [...]}` is its complement, so two branches whose
   sets do not intersect are disjoint for the same reason two different `const`s are — the
   single-value case is the one-member set. A pair the
   derivation cannot separate is treated as overlapping, because admitting a union on an unproven
   disjointness is the defect this source exists to avoid.

  *The third separator is one branch forbidding a VALUE another pins.* Every instance of the
   pinning branch carries a value the forbidding branch refuses, so the two are disjoint in fact,
   and neither of the others reaches it: the pinned-`const` separator needs BOTH branches to pin,
   while the required/forbidden separator needs the NAME forbidden outright and the forbidding
   branch forbids only the value.

   **A singleton `required` under a `not` does not forbid the NAME.**
   `{"properties": {"k": {"const": v}}, "required": ["k"]}` under a `not` forbids the pair, and
   reading it as forbidding `k` by name separates pairs that overlap — which is wrong in both
   directions at a branch pinning some other value. That over-reading is a defect whether or not
   the third separator lands.

A union matching none of the three emits a plain `A | B` over its branches and **declares an
WIDENED approximation at the union's pointer where the combinator is `oneOf`, and nothing at all where it is `anyOf`.**

A branch is never chosen by trying each and keeping the first that validates, because overlapping
branches make that answer a property of declaration order rather than of the payload — which is
exactly what the approximation records. `A | B` admits the union of the branches, which
is what the document admits, so **nothing widens and nothing narrows** — **for `anyOf`.**

**For `oneOf` it is false, and the model is wider than the document.** `oneOf` admits an instance
satisfying exactly one branch; `A | B` admits one
satisfying two. "The schema half still enforces exclusivity" is
true only of a caller who invokes `strict_validate`: the class carries
`strict_validate` and `model_validate` does not route through it, so the type is wider than the
document for every caller who uses pydantic's own entry point.

**AND THE DECLARATION IS NOT THE ANSWER: `oneOf` MEANS EXACTLY ONE AND THE CLASS SAYS SO.** A
declared widening is honest, and honest is not correct. `oneOf` states a
constraint and the model layer can carry it, so carrying it is what §2's direction requires — a
fact is DROPPED only where the annotation cannot hold it, and here a rule can.

**THE COST IS BOUNDED BY DISJOINTNESS, WHICH IS WHY THIS IS CHEAP.** Where the branches are
provably disjoint, `A | B` is ALREADY exactly-one — at most one branch can match an instance, so
the union is exact and there is nothing to add and nothing to declare. Every union that dispatches
on a determining key is in that set. **What is left is the residue where disjointness could not be
proved**, and that residue is the set that carries this declaration.

So the rule is: **a non-separable `oneOf` carries a rule that counts the branches an instance
satisfies and refuses unless exactly one does.** It costs one validation per branch at those sites
and nothing anywhere else — never a general cost, because the separable case is untouched.

**AND THE DECLARATION RETIRES WITH IT**, which is the test of whether this landed: reading 2's set
shrinks by exactly these, and a `oneOf` exclusivity declaration surviving the change is a site the
rule failed to reach.

So, until that lands, the dropped exclusivity is a WIDENED fact and is declared as one. **It is ONE
declaration and not two.** The two losses — which branch an
overlapping payload lands in, and that it is admitted at all — are both real and are
**coextensive**: the branch question arises only for the payloads the widening admits, at the same
pointer, over the same values. Two declarations therefore say one thing twice, and saying it twice
costs four changes to §8's instruments — a site key that carries a kind, a pointer in two places
at once, a split of a shared §5 cell, and an upstream issue that does not exist. Two declarations
also collide on a `(document, pointer, keyword)` site, and which kind survives is path-dependent,
which is a substitution and §2 forbids it.

**The kind is the fact §8 grades, and the other loss is the REASON carried on it.** An inseparable
`oneOf` declares WIDENED, because the model admits values the document refuses and a consumer sees
that through `model_validate`; its reason also states that such a payload's branch is decided by
declaration order, which the document does not decide. Nothing is dropped — the kind is the one
§8's CONSTRUCTION can prove, by handing the class a value the document refuses.

**And the `anyOf` case declares NOTHING.**
`anyOf` admits an instance satisfying at least one branch and so does `A | B`, so the model is not
wider and nothing is owed but the branch choice — invisible to all three checks, as §2 says.

**The attribution is OURS until an issue exists.** A union whose branches are
not separable is a defect in the union — the bundle already writes the idiom that separates them,
each branch forbidding a name the other requires, so the fix is a copy from elsewhere in the same
bundle. That makes it a candidate for an upstream attribution and not an upstream attribution:
§2 keys one to an entry of `codegen/attribution.py` naming an issue, an entry with no issue is a
build failure, and §10's fifth clause is that every upstream attribution names a LIVE issue.
Minting a number for an unfiled gap creates exactly the defect that clause prevents, so §14's rule
governs — **an unfiled gap IS ours.** Filing the issue reclassifies these sites and changes no
type, no emission and no count.

Where nothing overlaps there is no order to depend on and no approximation, which is why the third
source is a dispatch and not a relaxation.

A hand-written map per document is still not a dispatch source: it is complete with respect to
itself, so a branch added upstream leaves it silently wrong — and unlike declaration order it
would be wrong without saying so, where an approximation says so by construction.

---

## 5. How each keyword compiles

The draft-07 keywords the bundle uses. An answer is given per position where the positions differ.

**The grids in this section are generated from `codegen/keywords.py`.** *"The widening each row
takes"* at the end of this section is the hand-written half and states the cell each row reading
"→ refused" takes; the generator writes those sentences into the grids when the cells change, and
until then the grids and that subsection are read together. Nothing hand-edits a grid: a cell
is the one place a keyword decision lives, and a grid is its rendering.

### Structure

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `type` | A scalar word → `str` / `int` / `float` / `bool`, unless a constrained type or `format` selects one. `object` with `properties` → a class; without → `dict[K, V]`. `array` → `list[X]`. `null` → `None`. A LIST of words → `A \| B`, each sibling keyword going to the one type word that can carry it. Absent → `Any`; absent beside `properties` → an object, where an enclosing node applies `type: object` to the same instance, and refused otherwise. An enclosing `oneOf` APPLIES a type word it does not state, where TWO OR MORE of its branches admit that type vacuously: `oneOf` admits an instance satisfying exactly one branch, so an instance two branches both admit is refused by the combinator, and the type is excluded by the document itself. This is EXACT and not a widening — it reads a constraint the document imposes rather than relaxing one — so it owes no declaration and no rung. It holds at `oneOf` ALONE: at `anyOf` an instance one branch admits is admitted, so the same derivation there would state a constraint the document does not (`adcp-client-python-10l.69`, decided 2026-10-29). |
| `properties` | A class with one field per key. An entry whose subschema ADMITS NOTHING — `false`, or `{"not": {}}`, which draft-07 makes the same schema — is NOT a field: draft-07 validates a `properties` entry only where the key is PRESENT and that entry then always fails, so the document's statement is that the key MAY NOT APPEAR and it says nothing at all about a value. The accepted set is the accepted set of `not: {required: [key]}`, which the `not` row already compiles to a `ForbiddenGroups` rule, so the key joins that rule on the nearest enclosing class and no field is declared. EXACT, not wide: nothing is dropped reaching it and no declaration is owed. `extra` is NOT the carrier — all three sites of the bundle state `additionalProperties: true` beside the forbidden key, so closing the class would refuse the other extras the document admits. Where `required` ALSO names the key the document admits nothing, and so does the class without an arm of its own: the `required` row's undeclared-name field refuses a payload omitting the key and this rule refuses one carrying it. ROOT beside a union → fields on the base, inherited by every branch. PROP / ELEM / MAPV / DEF → a nested class. BRANCH → the branch class. CONJ → fields of the composed class. A property two conjuncts declare is one field: its constraints intersect by §2, and two object declarations compose as an `allOf` of the two at that property; an empty intersection — two type words, disjoint enums — refuses, because the document admits nothing there. A `default` or a `description` is not a constraint, and the document's own statement wins over a base's. RULE: under `if` → the values a `Match` clause tests, read only where `const` or `enum`; under `then` / `else` / `not` → nothing. |
| `required` | The named fields are required: no `\| None`, no default. Naming a property NO declaration declares → a required field of type `Any`, and it is EXACT rather than wide: `required: ['x']` with no entry for `x` admits an object carrying `x` with any value, which is what the `type` row already gives an absent type word, so nothing is dropped and no declaration is owed. The model-only `properties` entry it renders is the empty schema, which states nothing the document does not. `required: []` → nothing. ROOT beside a union → required on the base's fields, and the names recorded in `_ROOT_REQUIRED`, so a refusal can separate a field the root requires from one that selects a branch. BRANCH → the branch class's requiredness, and the third of the branch-naming choices. CONJ → unioned into the composed class's `required`; a `required`-only conjunct → the overlay. RULE → a presence rule: `RequiredGroups`, `ForbiddenGroups` under `not`, the keys a `Match` clause tests under `if`, `ConditionalRequired` / `NegatedConditional` under `then` / `else`. |
| `definitions`, `$defs` | Nothing by itself: a bag of named subschemas. Each entry is declared on demand when a `$ref` names it, as the node's own kind, under `<Root><Key>`. |
| `$ref` | Another document's root → an IMPORT of that module's symbol; nothing of the target is copied into the module, and in the document of record (§3) the target is inlined unchanged. A fragment of another document → an import of a symbol the target declares. Local `#/…` → the entry decided on demand in this module; a cycle refuses. An annotation sibling → the sibling's description wins. A CONSTRAINING sibling → nothing, and REPORTED: draft-07 ignores every sibling of `$ref`, so the keyword constrains no instance and the document's accepted set is the target's alone. The record keeps the key, because §3 drops none; the declaration's cell says it compiles to nothing at this co-occurrence; and the report names it, because a key that reads as a constraint and is inert is worth reading once. Refusing it instead would refuse a document whose accepted set its own draft decides, and letting the referring value win would make the record state an acceptance fact the bundle does not — §9's last rule. KEY → the key type. BRANCH of a root union → a class with two bases; of a nested union → a member type. CONJ → a BASE where the target is a class declaring fields. Where it is not — a scalar, an enum, a container, or a union root — it is not a class a model can extend: the target is this node's own TYPE, and the other conjuncts and the `allOf`'s siblings constrain it, which is §2's intersection at a node that declares no fields of its own. A UNION root beside a node that DOES declare fields distributes: conjunction distributes over disjunction, so `(A | B) and C` is `(A and C) | (B and C)`, and the node is a union whose branches each take one of the target's branches as a base and add the node's own fields. Each branch of a union root is a class declaring fields, so this is the CONJ rule above applied once per branch and not a second answer. A property the node and the target's branch BOTH declare is one field taking §2's intersection, exactly as the `properties` row at CONJ states it for two conjuncts — the node's declaration does not shadow the branch's, and two `const`s intersect to the pin where they agree and to nothing where they differ. A distributed branch whose intersection is EMPTY is DROPPED, and the node refuses only where every branch is: `(A \| B \| C) and D` with `A and D` empty is exactly `(B and D) \| (C and D)`, so the accepted set is unchanged and nothing is approximated. The emptiness must be PROVED from the pins the two sides state — disjoint `const`s, disjoint `enum`s, disjoint type words — which is the same test the empty-intersection row names; an intersection this compiler cannot compute is the restatement row and not this one. |
<!-- end generated -->

### Values

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `const` | `Literal[value]`; the type word is not restated, since Pydantic renders it. A `format` beside the pin compiles to NOTHING and the pin alone is rendered, because a fixed value either satisfies the format or the node admits nothing: the pin is checked against the format, and where it satisfies it the `Literal` is already strictly tighter than any type the format would select, while where it does not the node is §5's empty intersection and refuses upstream. So no fact is dropped, and the cell declares the `format` as rendering nothing at this co-occurrence (`adcp-client-python-10l.70`, decided 2026-10-29). A `str`, `bool` or `int` value; an object, array, `null` or float refuses. On a branch's property → also the second of the branch-naming choices. AT a branch node, pinning the whole branch → the branch is a scalar: a `Literal` member of the union. Where EVERY branch of a root union is a scalar there are no branch classes to declare, so the root emits as an alias over the union of their types — `Literal['asap'] | AwareDatetime` — and not as a base with branches. A root union with a scalar branch beside a class branch → refused by name: the root symbol is a class or an alias, no shape in §4 carries both, and the first document to state one decides it rather than taking a rendering nothing has exercised. RULE: under `if` → a `Match` clause's value; under `then` / `else` / `not` → nothing. |
| `enum` | A named node → `StrEnum` / `IntEnum`, base read off the members; `enumDescriptions` → member docstrings. An untitled BRANCH of a root union → a `Literal` of the members. Mixed member types, an empty list, or a duplicate member → refused. Two members whose spellings yield one Python name → a `Literal` of the members and NOT an enum class (decided 2026-10-29). The collision exists only because an enum mints a Python IDENTIFIER per member; a `Literal` needs none, so both values are carried exactly as the document spells them and nothing is dropped. This is the same answer the row already gives an untitled branch of a root union, reached by a second route. Refusing instead cost **21 of the 95 refusals** for one node — `formats/canonical/html5.json`'s `clicktag_macro`, whose `clickTag` and `clickTAG` both spell `CLICKTAG` — including `core/product.json`. The cost is that one node gives a string-literal union rather than an enum class, which is a DX difference and not a correctness one; dropping a member, which the old clause rightly refused to do, remains forbidden. ROOT → the enum with a module-level `strict_validate`. PROP → a nested enum. KEY → a `Literal` of the members as the mapping's KEY type, which pydantic renders back as `propertyNames: {enum: […]}` — the document's own keyword, rendered and gradable; where the key node carries a `title` the `StrEnum` is the key type and renders the same way. CONJ beside a `$ref` whose target is an enumeration → §2's intersection of the two vocabularies, rendered as a `Literal` over the TARGET's MEMBERS and not over their raw values. The two dump identically — `{"enum": [the members], "type": "string"}` — so they state the same fact either way, and the member form keeps the imported symbol a caller can name: where two renderings state one fact, DX decides. A vocabulary the target does not contain is the empty intersection and refuses, by the same rule that refuses a member the node's own constraints exclude. RULE: under `if` → `Match` values; else nothing. |
| `default` | On a REQUIRED property → dropped and reported, because no rendering makes a field both required and defaulted. On a node that becomes an alias → no slot. PROP → the field's default; `None` is a default, absence is not. |
<!-- end generated -->

### Strings

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `pattern` | `pattern` on the type, as a named alias. On `format: uri` → **both**: the format selects a type only where that type STATES the pattern, which is `^https://` and `AdCPUrl`'s `allowed_schemes` alone, and the node takes the constrained `str` with `json_schema_extra={"format": "uri"}` at every other pattern. The row read "selects the type instead, and the pattern stays with the schema half" and that was a SILENT widening at 408 positions in 115 documents: `strict_validate` applied it, the class did not, and no `__adcp_approximations__` entry said so (adcp-client-python-bgyd). The regex engine is derived per class, because a pattern using look-around needs Python's engine rather than Rust's. ROOT → the root alias over it. ELEM / BRANCH → the alias as the element or member type. KEY → an annotated `str` key. RULE → nothing. |
| `format` | Selects a TYPE where the document's draft asserts the format and a type is named: `date-time` → `AwareDatetime`, `date` → `datetime.date`, `uri` → a URL type chosen by `pattern`. Otherwise rides as `json_schema_extra={"format": …}` on the field. **A `uri` beside any assertion the URL type does not itself state → the constrained `str`, and the format rides**: a URL type carries no string constraint, so the type is given up and both of the document's facts are kept. Where a constraint is there to join it the format joins the NAMED TYPE rather than the field, because an ELEM, a MAPV and a BRANCH have no field to ride on. ELEM / MAPV with no type selected → a named alias carries it. BRANCH → the selected type as the member. |
| `minLength`, `maxLength` | `min_length` / `max_length` on the type, as a named alias. On a URL type → refused, not representable. A node stating the bound and **no `type`** is `Any` (§5's `type` row, "absent → `Any`"), which carries no bound: the keyword is dropped at rung KEYWORD — the type is unchanged, which is what that rung is — and the drop is declared. Selecting the type the bound implies instead would NARROW, because a typeless node admits an instance of every type and the bound constrains only one of them. ROOT → the root alias. ELEM / MAPV → the alias inside the container. KEY → the key type, which Pydantic renders back as `propertyNames.minLength`. RULE → nothing. |
<!-- end generated -->

### Numbers

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `minimum`, `maximum` | `ge` / `le` on the type: a standard Pydantic type where one says exactly this, a named alias otherwise. ELEM / MAPV → the alias inside the container. BRANCH → the alias as the member type. RULE → nothing. |
| `exclusiveMinimum`, `exclusiveMaximum` | `gt` / `lt` on the type, **never `ge` / `le`**. The bundle distinguishes `minimum: 0` from `exclusiveMinimum: 0`, and the two differ on exactly one instance, so rendering either as the other makes a field accept a zero its document refuses or refuse a zero its document accepts. |
| `multipleOf` | Unused by the bundle. The first document to carry one refuses by name, rather than taking a rendering nothing has exercised. |
<!-- end generated -->

### Arrays

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `items` | `list[X]`, X decided by the same walk and named where it needs a symbol. A list-valued `items` → refused: that is tuple validation. ROOT array → `RootModel[list[X]]`. RULE → nothing. |
| `minItems`, `maxItems` | `min_length` / `max_length` on the annotation of the **array's own type**, at every position. `minItems: 0` states nothing. `constraints` declares it once, generically, as `type NonEmptyList[T] = Annotated[list[T], Field(min_length=1)]`. A node stating the bound and **no `type`** is `Any` (§5's `type` row, "absent → `Any`"), which carries no bound: the keyword is dropped at rung KEYWORD — the type is unchanged, which is what that rung is — and the drop is declared. Selecting the type the bound implies instead would NARROW, because a typeless node admits an instance of every type and the bound constrains only one of them. PROP → on the field. ELEM / MAPV / DEF → the container's type must be named to carry it. BRANCH → on the branch's own type, never on the field holding the union. RULE → nothing. |
| `uniqueItems` | A `UniqueItems` rule on the class holding the array, plus `json_schema_extra={"uniqueItems": true}` on the field so it is graded, and the keyword is stripped off the array's own declaration. Where no class encloses the array → a `Distinct` after-validator on its own annotated type, beside the same `json_schema_extra`. |
| `contains` | An existential quantifier — `items` constrains every element, `contains` says at least one matches — and the model states the **predicate**, not a transcription of the subschema. Every position → an `AtLeastOne` after-validator on the array's own annotated type, because no class has a kind for it: `AtLeastOne(pinned=((property, const), …))` where the subschema requires properties pinned to a const, `AtLeastOne(values=(value,))` where it is a bare `const` or a one-member `enum`. A property KEY is not required to be a Python identifier, so the predicate is a tuple of pairs and not keyword arguments. Any other predicate — a bound, a pattern, a nested `contains`, a `$ref` — → the keyword is CARRIED and the schema half answers alone: a transcription of the subschema is the thing this row declines to emit, and the first document to state such a predicate decides its rendering. RULE position → a `Match` MEMBERSHIP clause, `value in field`, and no validator. |
<!-- end generated -->

### Objects

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `additionalProperties` | The empty schema `{}` IS `true` and is read as `true` everywhere below, never as a typed value schema. On a class: `false` → `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; absent → `ignore`. **A class DECLARES the `extra` the document gives it and never inherits it** (decided 2026-10-29): pydantic merges `model_config` along the MRO, so a branch composing TWO bases takes whichever value the later base happens to carry, and `absent → ignore` on that base silently overrides an `allow` the document states. Measured on `content-standards/get-content-standards-response.json#/oneOf/0`, where the union base states `allow` from the root's envelope conjunct and the composed target's default `ignore` wins the merge, so the model drops keys the document admits. The value is read from what the document states at the class's own pointer after the document-side fold — which is where the root's conjunct arrives — and written on the class, so MRO order decides nothing a document states. On a mapping (no `properties`) → the VALUE type; `true` or `{}` → `Any`; `false` → refused, it admits only the empty object. Beside `patternProperties` → refused, two value schemas. `false` on an `allOf` overlay would reject the fields its sibling conjunct contributes, which is why `true` is the only value an overlay can carry. ROOT beside a union → the same, on the base, inherited by every branch; a branch stating its own composes with it by the CONJ rule below. CONJ → `true` is the identity and contributes nothing, `false` on any conjunct closes the composed object, and two typed ones intersect their value schemas; a typed conjunct beside a `true` one is a widening and refuses. |
| `patternProperties` | A mapping whose KEY carries the pattern: `dict[Annotated[str, StringConstraints(pattern=…)], V]`, which Pydantic renders back as `patternProperties` — the document's own keyword. More than one pattern → refused: that is a value schema per key shape. Beside a non-`false` `additionalProperties` → refused. |
| `propertyNames` | The mapping's KEY type: a `$ref` → that type; `minLength` / `maxLength` → a length-bounded `str`; `pattern` → an annotated `str`; `enum` → a `Literal` of the members, which pydantic renders back as this very keyword; `anyOf` → a union of key types. Beside `patternProperties` → the key type carries both, by §2's intersection: each states a constraint on the same key. On a CLASS with declared `properties` → checked against the declared names when the class is emitted and carried nowhere, because those names are fixed and known; a declared name the constraint refuses is a contradiction in the document and refuses by name. Where that class also admits extras, a key beyond the declared names is checked by the schema half alone, and the model is looser than its document there, which §2 permits. RULE position → nothing on the model: a rule position constrains which keys a conditional *tests*, so there is no key type to annotate and no value to annotate. |
| `minProperties`, `maxProperties` | On a class → a `PropertyCount` rule. `minProperties` is written only where `additionalProperties` is stated, because a dropped key would make the rule refuse what the document accepts; `maxProperties` needs no such gate, since a dropped key only lowers the count. On a mapping → `Field(min_length / max_length)` on the dict's type, because a `PropertyCount` rule counts declared fields and a dict has none. |
| `dependencies` | The list form → a `Dependencies` rule: if A is present, B is required. The schema form refuses by name on the first occurrence, rather than being skipped. |
<!-- end generated -->

### Combinators and conditionals

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `allOf` | ROOT with no union beside → `$ref` conjuncts are BASES, inline conjuncts are fields and rules of this class; beside a union → the same, onto the base: `$ref` conjuncts are the base's bases and inline conjuncts are its fields and rules, and every branch inherits them. PROP / ELEM / DEF → the same reader at the node's own pointer. BRANCH → the branch class composes, with the union base first. CONJ → the same rule applied to the conjunct's own conjuncts. RULE: under `not` → single-group conjuncts merge into one group; else nothing. |
| `oneOf`, `anyOf` | Presence-only, every branch `required`-only → a `RequiredGroups` rule naming the combinator. Presence-only where a branch also `not`s a group of `required` → a `PresenceGroups` rule naming the combinator, whose clauses are the branches: each clause carries its OWN required group and its own forbidden groups, because the `not` is per branch — a `ForbiddenGroups` over the union of them forbids every group unconditionally and refuses a payload the document admits. Shapes at ROOT → the base plus one class per branch. Shapes nested, with nothing beside the combinator → one type `A \| B`. A sibling a CLASS carries → that same base-plus-branches shape, at a union in ANY position: the siblings become the base, each branch becomes a subclass narrowing what it narrows, and the union is over the subclasses. A sibling no class carries refuses, because it is a conjunction with every branch and `A \| B` has no slot for a fact of its own. **A bare combinator every arm of which is a PURE VALUE SET is ONE enumeration, of the union of the arms' members** (`codegen.lower.union.one_value_set`, 2026-11-10): draft-07 admits an instance only through an arm, so a union every arm of which admits exactly the members it names admits exactly the union of those lists — the same entailment this document already makes for "a union every branch of which declares an object has declared an object", read for a value set instead of a container. It is EXACT: nothing widens and nothing narrows, so it owes no declaration and no rung. An arm is PURE when its declaration — read through a bare `$ref`, which is how the one site in bundle 3.2 spells its first arm — states nothing but its own `enum` and the `type` word those members already satisfy; a `pattern`, a `minLength`, a `format`, a `not` or an `allOf` beside the members makes the arm's accepted set a question its own `enum` row decides and the rule declines, and an ANNOTATION is declined too because admitting it would drop it. A `const` arm is draft-07's one-member value set and WOULD be sound; it is left out because the bundle states no such arm. **The merge decides the node's TYPE and does not unmake its arms**: an arm is a node the document states, §1 exports every union BRANCH, and each arm keeps its own `__adcp_schema__` and its own graded pair — which also makes §4's fourth rung reachable where the arm used to fall back to the union's own derived name, now taken. Measured over bundle 3.2: 299 union nodes asked, ONE fires (`media-buy/get-products-request.json#/properties/fields/items`, 38 ∪ 17 = 53), and the rule is worth stating because it is the correct general rule and costs nothing — not because it is a family. For `oneOf`, `A \| B` admits an instance satisfying two branches and the schema half enforces exclusivity. A union whose branches declare the same properties with the same `required`, and differ only in the `const` or `enum` each pins on some of them → one class: each such field admits the union of the branches' values, and one rule whose clauses are the branches themselves — one clause per branch pinning that branch's values, satisfied when the instance matches at least one clause. A branch that differs in a type, a bound, a format, a nested shape or its `required` is a branch of shapes and takes the base-plus-branches answer. For `oneOf` the schema half enforces exclusivity, as it does for `A \| B`. KEY → a union of key types. CONJ → one class per branch over the composed bases. RULE: nothing, and the schema half answers. The `not` clause this row carried — the union of the branches' groups — is WITHDRAWN (§8, 2026-11-03): `not oneOf` admits an instance satisfying ZERO branches or TWO OR MORE, and a forbidden group over the union refuses an instance satisfying two, which the document admits. A forbidden-group list cannot say "not exactly one", so such a node DECLARES rather than lowers. |
| `if` | A `Match` clause list where it states `required` plus `properties` with `const` or `enum` values; otherwise nothing, and the schema half answers. With `then` / `else` → a rule on the nearest class. |
| `then`, `else` | `ConditionalRequired` / `NegatedConditional` from its `required` and a single-name `not`. Its `properties` → nothing on the model; the schema half narrows the value. |
| `not` | `not: {required: …}`, and `anyOf` / `allOf` of those → a `ForbiddenGroups` rule. Over a `const` or `enum` → a `NotValue` after-validator on the value's own annotated type. Any other shape → nothing on the model; the schema half answers and the ceiling is named. `not: {}` admits nothing, which the typeless `Any` carries — at a node whose OWN accepted set is the thing being typed. As a `properties` entry it is not that node: the enclosing object still admits every instance without the key, and the `properties` row answers it there with the `ForbiddenGroups` this row already decides for the keyword's other spelling. |
<!-- end generated -->

**`oneOf` AND `anyOf` KEEP ONE CELL**, because what differs between them is not the lowering. There
is no document-side disjointness fold either.

**What the two combinators do differ in is a fact about the artifact, and the construction proves it.** An
inseparable `oneOf` admits a payload the document refuses — one satisfying two of its branches,
which `Draft7Validator` refuses and `model_validate` accepts as the first matching branch. That is
a WIDENED declaration and §8's construction hands the class exactly such a value. A cell reading "the
schema half enforces exclusivity" is true only of a caller who invokes `strict_validate`, and
correcting that sentence is a cell edit and not this rendering's.

**ONE VOCABULARY IS ONE TYPE, COLLECTED BEFORE EMISSION.** The bundle
states the same value set at many positions and says so in many spellings, and compiling each
position independently turns one protocol concept into several Python types that are not
interchangeable. The census that reads this is keyed on the value list, and the three-way split
below is what it feeds.

One member set emitted under several names, in several classes, is several classes, several names,
one concept. A function annotated with one refuses the others and
`isinstance` fails across them, so a consumer meeting the same protocol value in two messages
cannot pass it between them. §4's identity rule does not reach this: it collapses nodes of
IDENTICAL CONTENT, and these are the same vocabulary spelled independently.

**So the walk COLLECTS vocabularies before it names anything, and every position references the
one type.** The alias is the emission's single declaration of that value set; a position holds a
reference to it and never a copy.

**The NAME comes from the bundle and from nowhere else**, which is §4's standing rule and is what
makes this derivable rather than a mint:

- **the bundle gives exactly one `title`.** That title is the name, and it need not be stated at
  every position: one title anywhere in the set and no conflicting one is enough.
- **the bundle gives no title anywhere.** These are **NOT collapsed across
  documents.** Nothing names the concept, and §4 already refuses to mint a public name no document
  states. Two fields sharing a member set by coincidence are not one type, and without a title
  there is nothing to tell coincidence from identity.
- **the bundle gives conflicting titles.** A decision, brought to the owner with
  the titles and the positions. Not resolved by picking the commonest.

**And this fixes the `const` override by construction rather than by a second rule.** Where the
root's `enum` and a branch's `const` are the same vocabulary, both positions reference the one
alias, so the branch's pin is `Literal[Alias.MEMBER]` because there is no other member to name.
The rule below stands as the general case — a pin whose field has no collected alias.

**TWO RENDERINGS THAT DO NOT TYPE-CHECK, and both are cells.** A rendering a consumer's checker
rejects is a rendering the wheel cannot honestly ship `py.typed` for (`architecture.md`), because
the checker then sees `Any` instead of any of this. Each has one cause and neither costs the
architecture anything.

**A `const` pinning an enum member emits the MEMBER, not the raw value.** Where a document states
an `enum` at a root's property and a `const` on the same property at a branch, the
`enum` cell gives a `StrEnum` and the `const` cell gives a `str` literal. **Those are not
narrower-and-wider, they are different vocabularies for one field** —
`str` is not a subtype of the enum, so the branch is an INCOMPATIBLE OVERRIDE rather than a
refinement.

The fix keeps base-plus-branch inheritance, which this section does not reopen:
**where a `const`'s value is a member of an enum the same field's enclosing
declaration compiles to, the pin is that member.** An enum-member literal IS a subtype of its enum,
so the override is legal; `isinstance` is unaffected; and pydantic still accepts the raw wire string,
because the enum is a `StrEnum`.

**The stronger rule — "a `const` compiles to a StrEnum of its own" — is refused, and by two facts
rather than a preference.** First, Python forbids it from working: an enum carrying members cannot
be subclassed (`TypeError: <enum 'Sub'> cannot extend <enum 'E'>`), so a branch's own StrEnum could
never be a SUBTYPE of the root's, and the override would stay incompatible with a one-member class
added per pin. Second, **many of the `const` positions in the bundle have nothing to
enumerate** — they sit at a field whose declaration carries no enum, and many pin a `bool` or an
`int`. A boolean pin has no string vocabulary to join.

So the condition is necessary and not a convenience, and it is exactly the declaration being
overridden — not "an enum appears somewhere in the document", which is a looser reading and would
pin a member of an enum the field does not take. Where no enclosing declaration gives the field an
enum there is no override to conflict with, and `Literal[value]` stands as §5 already has it.

**A `default` is emitted through its annotation's OWN TYPE, and the document's `default` survives
it.** The field must carry a value of the type it declares; a raw JSON literal against a model or
an enum annotation is the defect, **and it reaches callers and not only checkers**: pydantic does
not validate a plain default, so a field annotated as a list of models hands back a `dict` and an
attribute read off it raises. The disagreeing sites are a list of models and, far more of them, a
plain enum — `asset_source: AssetSource | None = 'buyer_uploaded'`. Both belong to this rule rather
than to §3a's catalogue.

**And `default_factory` alone is NOT the mechanism, because it drops the document's fact.**
A field carrying `default_factory` renders `model_json_schema()` with **no `default` at all**,
where a plain default renders it. A document's `default` is a fact §8
grades, so the factory must be accompanied by `json_schema_extra={'default': …}` carrying the
document's own JSON — through the one channel `render` already merges `format` and `uniqueItems`
into, not a second one.

**THE VALUE IS CONSTRUCTED THROUGH A `TypeAdapter`, NOT BY CALLING THE CARRIER.** Calling it is
undecidable where the decision has to be made: the renderer cannot
tell an imported enumeration from an imported `Annotated` alias. Two defaulted fields can produce
**byte-identical `TypeRef`s** where one carrier is a `StrEnum` and the other is `Annotated[…]` and
**not callable**. `ir.Module` carries no kind for an imported symbol, and many
defaulted sites name a symbol from another module, so a rule reading "call the carrier" emits
`LanguageTag('en')` and the package fails at import. The kind
exists at lowering time and the reference lowering drops it at PROP.

So the field renders `default_factory=lambda: TypeAdapter(X | None).validate_python(<the
document's value>)`, which needs no kind, and the same spelling serves the scalar and both list
positions rather than a per-position discriminator that would be a bet.

**And a site whose carrier is an `Annotated` alias must NOT be converted**, which no error count
will tell anyone: those carriers produce no mypy error at all. The gate names them by hand, so the
set it converts and the set it leaves are both stated rather than derived from an error list.

**The factory is not for mutability.** Pydantic deep-copies a plain mutable default per instance,
so two instances already receive distinct objects and mutating one does not reach the other. What
the factory buys is no shared object behind `model_fields[…].default`, and no model instances
constructed at import time.

**A NARROWED `enum` INSIDE AN INHERITED VOCABULARY NAMES ITS MEMBERS.** This
is the `const` rule above generalised from one value to several. Where a base declares a field as a
vocabulary and a branch narrows it to a subset of that vocabulary's members, minting a
**separate** `StrEnum` for the branch gives two unrelated enum classes, so the branch is an
incompatible override — exactly the defect the `const` case had, with a set in place of a single
value. **The branch's members must be a strict SUBSET of the base's, verified.**

Python forbids the obvious repair, as it did before: an enum carrying members cannot be
subclassed. So the branch pins `Literal[Base.MEMBER, …]` —
a literal over the base vocabulary's own members, which IS a subtype of that enum, and the
one-member form is the `const` rule's own answer.

It is also the better surface. A consumer reads the base vocabulary's members at the branch
instead of meeting a second two-member class that exists only because a branch narrowed.

### The widening each row takes

Every "→ refused" clause above becomes one of three answers, and **the largest group is neither
a refusal nor an approximation.** The rows sort as follows.

**(a) Rows whose answer is already decided here.** These cost no
approximation at all: the sentence that grades them exists, and what is owed is honouring it.

- **A plain keyword beside a `oneOf` / `anyOf`.** §4's union section already decides it — "every
  keyword beside the combinator compiles onto the base, and every branch inherits it" — and §8
  already decides how the result is graded, against the branch node read under the root's
  siblings. A refusal reading "there is no pointer to the conjunction for it to name" is answered
  by that pairing rule. No widening; the keyword compiles.
- **`propertyNames` with an `enum`, and `enum` at KEY.** A `Literal` of the members is the key
  type, and Pydantic renders `dict[Literal[…], V]`
  back as `propertyNames: {enum: […]}` — the document's own keyword, rendered and gradable.
  Faithful, not wide. Where the key node is named, the `StrEnum` is the key type and renders the
  same way.
- **`format` beside another string constraint.** The `format` row refuses a `uri` beside a
  string constraint because a URL type carries none. The row's own fallback already answers it:
  the type is the constrained `str` and the `format` rides as
  `json_schema_extra={"format": "uri"}`. Both facts are kept and neither half narrows; what is
  given up is the URL type's parsing, which is not an acceptance fact.
- **A local `$ref` cycle.** The `$ref` row says "a cycle refuses". A cycle is not an obstruction
  in Python: a forward reference under a string annotation plus `model_rebuild()` after the
  module's declarations represents it exactly, and §4 already calls `model_rebuild(force=True)`
  for union branches. The cell's answer becomes the forward reference. A *cross-document* cycle
  is a different thing and is not this row's: the record cannot be built for it, so it is §2's
  one irreducible refusal, and the difference between the two cycles is the record and not the
  type.
- **A root that is a bare `$ref`.** Binding this module's symbol to another
  module's class would be a second way to reach one class, against §1. Where the target is a
  class the answer is a **subclass** of it, which is one class per name and accepts exactly what
  the base accepts, so §1 is untouched. Where the target is an alias, an enumeration or a root
  model there is nothing to subclass and the symbol is bound to the target **by identity**, which
  §1's own carve-out already admits inside a module and now admits across one: `X is Y` holds and
  the domain surface exports it once.
- **A scalar, enum, container or union target as a conjunct of an `allOf`.** The `$ref` row
  already decides it — "the target is this node's own TYPE, and the other conjuncts and the
  `allOf`'s siblings constrain it" — and a refusal reading "*X* is not a class, so it cannot
  be a base" is the unimplemented half of that sentence.
- **`uniqueItems` and `contains` where no class holds the value.** §2 already decides it: where
  no class encloses the value, the rule is an after-validator on the value's own annotated type. A root array
  is a root model, and a root model carries a rule tuple exactly as a class does, so `Distinct`
  and `AtLeastOne` reach it. The keyword is enforced, not dropped. `Annotated[list[X],
  AfterValidator(…)]` carries a rule, and nothing about a named alias prevents it, so the
  distinction is between a rule having nowhere to LIVE, which is never the case, and a predicate
  having no decided RENDERING, which is a different row.
- **A root stating only `if` / `then`.** The conditional is a rule, and §2 declares a rule with no
  enclosing class on the
  value's own type: the root is a permissive root model carrying `ConditionalRequired`. The
  document states a conditional and nothing else, and so does the model.
- **A root stating no schema keyword.** A permissive root model over a document that constrains
  nothing DROPS nothing, so there is no fact to declare, and a declaration the construction cannot prove
  is deleted rather than carried. A document declaring draft-07 whose keys are not schema keywords
  admits every instance under `Draft7Validator`, so the permissive model is exactly as wide as the
  document. The upstream issue stands — the schema should say more than it does — but **an
  upstream issue is not an approximation**, and filing one is the issue list's job, not a
  declaration's.

**(b) Rows whose answer is a declared widening.** Each names its widening (§2's chain) and its
attribution.

- **`patternProperties` beside a non-`false` `additionalProperties`.** The
  `patternProperties` row refuses this case as "two value schemas". **It is
  not the document's obstruction:** under `Draft7Validator`, keys matching the pattern take the
  pattern's schema and every other key is unconstrained. So §9's test fails on all three counts:
  the obstruction is not the document's,
  not the pointer space's, and not Pydantic's either, since a key-pattern check is expressible as
  a rule.

  Widening CONTAINER: the mapping is `dict[str, Any]`, the pattern's value typing is the fact
  dropped, and `strict_validate` still enforces it from the document. Attribution ours, and the
  one sentence is that a faithful answer is a rule family for "keys matching this pattern take
  this type", which no row has written.

- **A `contains` predicate no `AtLeastOne` carries.** The row declines to transcribe a `contains`
  subschema into a validator, and that decision stands — what it may not do is refuse the document
  for it. Dropping the keyword widens the array (a list with no matching element is accepted by
  the model and refused by the schema half) and transcribes nothing, so the row gets both of the
  things it wanted. `AtLeastOne` takes the predicate §5's `contains` row decides
  (`AtLeastOne(**{property: const})`, or `AtLeastOne(value)` for a bare `const` or a one-member
  `enum`); a richer predicate widens rather than being transcribed. `AtLeastOne`, `NotValue` and
  `Distinct` are declared in `src/adcp/types/_runtime.py` beside the other rule kinds, and each is
  declared on the value's own annotated type where no class encloses it.
- **A list-valued `items`.** Widening JOIN: `list[A | B | …]` over the positional schemas, dropping
  position and arity, with the element type collapsing to `Any` where `additionalItems` is
  absent or `true`. **The arity bound is not derived.** `additionalItems: false` implies
  `maxItems: len(items)`, and §3 forbids deriving a keyword the bundle does not state, so the
  bound stays with the schema half and the model does not restate it. Attribution ours.
  Unexercised: the bundle states no list-valued `items` and no `additionalItems`, so this row
  decides a case before it arrives rather than after.
- **An `allOf` restatement that neither matches nor narrows.** §2's intersection is the document's
  own accepted set, and the refusal exists where the intersection of two object or two array
  declarations is not computable. Widening KEYWORD: the field takes the base's declaration and the
  restatement's extra facts are dropped. That widens relative to the intersection and cannot
  narrow, because the base is one conjunct and the intersection is a subset of it. Attribution
  ours.
- **An empty intersection** — two disjoint type words, two disjoint enums. The node admits
  nothing, which is a contradiction in the document. Widening TOP, and this is the answer the `not`
  row already gives for `not: {}`: "admits nothing, which the typeless `Any` carries", with the
  schema half refusing every payload. Attribution upstream, because a conjunction admitting
  nothing is a defect in the conjunction. This row is about a node whose WHOLE accepted set is
  empty. One empty DISJUNCT of a union that still admits something is not that node: §5's `$ref`
  distribution clause drops the branch, the document's accepted set is unchanged, and no
  declaration is owed.
- **A keyword in none of §5, §6 or §7.** Widening TOP: the node is `Any`. Draft-07 ignores an
  unknown key, so the document may be narrower than `Any` but can never be wider, which makes
  `Any` the one safe widening when the keyword's reach is unknown. §2's by-name principle is intact
  — the key is not silently ignored, it costs a declared approximation at the TOP widening and a loud
  report line — and the node losing its whole type is exactly as visible as a refusal was.
  Attribution ours.
- **A union whose branches §4's dispatch cannot separate.** Declares a WIDENED fact where the
  combinator is `oneOf` and nothing where it is `anyOf`; §4 states it.

**(c) Rows that refuse nothing because there is no fact to approximate.** `errorMessage` and the
registry data keys constrain no instance, so no annotation drops anything for them. They belong to
§6 — admitted by name, compiling to nothing, reported.

### A union of presence-only branches that also forbid

The `oneOf`/`anyOf` row's presence clause reads "every branch `required`-only", and the bundle
holds unions whose branches constrain presence only and are NOT `required`-only. They go to
different places, and the generated cell is written by the row that implements each.

**Group A — every branch is `required` plus a `not` of required groups. This is FAITHFUL, and
it needs one new rule kind.**

Every branch constrains which keys are present and nothing else, so it is a rule on the root's
class and not a branch class. **The answer is ONE rule whose clauses are the branches, each
clause carrying its own required group AND its own forbidden group, with the combinator deciding
how many clauses an instance may satisfy.**

Widening `_required_only` to admit `not` is WRONG: the `not`
is per BRANCH, so branch *i* reads "every name in R*ᵢ* present and no group of F*ᵢ* present". A
`RequiredGroups` over the R*ᵢ* beside a root-level `ForbiddenGroups` over the F*ᵢ* forbids every
F*ᵢ* unconditionally, which refuses a payload the document admits. The two
halves must stay paired per clause, and neither `RequiredGroups` (groups and a combinator) nor
`ForbiddenGroups` (groups alone) has a slot for the other half. So `_runtime.py` declares the
new kind and `lower/rules.py` writes it. Nothing is dropped.

**Group B — the union MIXES case branches with presence-only ones. This is a WIDENING.**

A presence-only branch admits ANY object carrying those keys, which is wider than any of the
case branches' classes. So no type over the case classes covers the instances the presence
branch admits, and there is no faithful type for the union: the case branches give classes, the
presence branch gives a rule, and an instance satisfying only the rule is none of the classes.
That is the asymmetry Group A does not have, and it is why the two cases separate. The fact
dropped is the case precision of the branches, the type widens along §2's chain, and the gap is
declared and attributed.

### The dispatch mixin is named where no base already carries it

`BranchDispatchMixin` has to come FIRST so the MRO finds its `__get_pydantic_core_schema__`,
and a union base that composes already carries it — so naming it beside such a base puts a
class before its own subclass and Python refuses to build the module.

**The suppression is a function of the BASE LIST and not of the route that reached it.** That is
the whole decision, and it is the one reading both routes can ask: at the point the base list is
built, the mixin is named where no base in it already carries the mixin, and omitted where one
does. `base_if_none_composes` is the same case at the same seam — "what the base would be if
nothing composed" — and this is "what the mixin is if nothing already carries it".

A guard keyed to the route is the alternative and it is wrong. `Enclosing` is constructed at one
place, inside the enclosing union's branch loop, under the case that claims a branch the parser
classified `nodes.Union`. A nested union reaching `lower_union` through the DISPATCH instead —
because it declares `properties` beside its own combinator, so the enclosing loop's case does not
claim it — arrives with no carrier, and a second guard there would be a second copy of the
reading `Enclosing` was built to hold once (§11).

`Enclosing` keeps its other job. It carries the enclosing base and that base's `Case` so a
property both declare takes §2's restatement rule, which no base list states and which the
dispatch route genuinely does not have.

### A STRUCTURE THE BUNDLE NEVER TITLES IS NAMED FROM ITSELF, AND THE UPSTREAM ASK STAYS FILED

**"Pending a name" does not mean "pending upstream". It waits for nothing.**
§3a's third answer says a structure nothing names is an upstream ask and not a local answer, and
that sentence is about the *concept* and does not forbid the *type*.

**THE KEY ALREADY SETTLES IT. Two positions sharing a layer's identity ADMIT IDENTICALLY** — the
key recurses through every `$ref`, drops annotations, and keeps every constraining keyword, so it
is the admitted-set key and nothing weaker. **Collapsing them cannot change what the SDK
accepts**, which is the only thing reading 1 is about. There is no faithfulness argument for
emitting them twice; there is only a naming argument, and the naming argument has an answer.

**THE ANSWER IS THE ONE L1 ALREADY SHIPS.** `StrMaxLen100` and `IntMin0Max150` are not in the
bundle either — they are **derived from the constraint**, because a constrained scalar's identity
*is* its constraint. An object structure's identity is its field set, so the same derivation
applies one layer up: **where the bundle does not name a structure, the name is derived FROM THE
STRUCTURE**, by §4's steps in order — the bundle's own title where it states one, else the
structure in words, else the declaring position.

**A DERIVED NAME IS NOT AN INVENTED CONCEPT, and that distinction is the whole of the rule.** A
name derived from the fields claims only what it can prove: *this is the type with these fields.*
A name taken from one position's property key claims a subject, and that is what §3a refuses — one
constraint at a `currency` position and at an `airport_code` position is the case, one layer down.

**AND WHERE THE POSITIONS ARE GENUINELY DIFFERENT SUBJECTS, ONE DEFINITION CARRIES SEVERAL
NAMES.** That is §3a's second answer, and it is what makes this safe: the type is written once and
each position that needs its own spelling gets an alias to it. Zero duplicate definitions, and a
caller still reads the word the protocol uses at the position they are at. A consumer's
`isinstance` holds across every spelling.

**THE UPSTREAM ASK IS NOT WITHDRAWN AND IS NOT A BLOCKER.** A `title` from the bundle is strictly
better than a derived name — it is the protocol's own word — so the ask stays filed and an answer
*replaces* a derived name with a stated one. What changes is that the derived name ships in the
meantime, because a pinned bundle is not going to grow titles and the SDK is for the bundle we
have.

### A FRAGMENT REFERENCE STATES WHAT THE NODE STATES, NEVER WHAT ITS DOCUMENT'S ROOT ADDS

A `$ref` to `other.json#/oneOf/0` resolves to **that subschema and nothing else**. Where the target
document's root composes — `{"oneOf": […], "allOf": [{"$ref": "…envelope.json"}]}` — the envelope
applies to an instance validated against the ROOT and not to one validated against the fragment.
Carrying it into the fragment states a requirement the referring document does not, which is a
**NARROWING**, and §2 forbids a model tighter than its document outright.

**So the rule is positional and it is the draft's own: an `allOf` sibling of a `oneOf` is a
statement about the node that holds both, and a pointer into one of them reaches past it.** A
reader asking what a fragment admits reads the subschema at the pointer; the root's siblings are a
fact about the root. The question is always *which node states a fact about which instance*, and a
document whose other branches reference ROOTS while one references a FRAGMENT is where the two
readings diverge.

**RELAXING THE SURPLUS REQUIREDNESS IS AVAILABLE AT THE REFERRING CLASS; CARRYING THE TARGET'S TYPE
FOR IT IS NOT.** A surplus field's type can name a symbol two hops from the target's module — an
envelope's `status` names an enumeration a third document declares — and `Target.imports` can place
no module for it, which D1 forbids a lowering to go looking for. So the field states **what the
fragment states about the key, which is nothing** — §5's required-with-no-declaration answer at a
second position.

**This is not `narrowings.py`'s door.** That registry is keyed by a §5 table cell and holds
keywords this compiler cannot express; the keyword here is expressible and is simply applied at a
node that does not state it.

### An `enum` conjunct beside a `$ref` to an enum

§2 decides the semantics already — "an enum is the intersection of the members" — and what is
unwritten is the RENDERING. A cell carrying effect `TYPE` with an empty `compiles` string says the
keyword lowers while no handler claims it, which is a defect in its own right.

**The intersection renders as a `Literal` over the TARGET's members, not over their raw values.**
`Literal[CreativeApprovalStatus.PENDING_REVIEW, …]` and `Literal['pending_review', …]` dump
identically — `{"enum": [the three], "type": "string"}` — so §8 compares the same fact either
way, and the member form keeps the imported symbol a caller can name. Where §8 cannot tell two
renderings apart, DX decides, and a caller reaching the enum class is worth more than a bare
string.

The cell is where this belongs, and the grid row is its rendering.

### Two ARRAY declarations under one `allOf`

§5's `properties` row at CONJ states the `allOf` spelling for two OBJECT declarations and says
nothing for two arrays, which is what the `$ref` row's own "the other conjuncts **and the
`allOf`'s siblings** constrain it" runs into at an array target.

**Two array declarations intersect, member by member, as two object declarations do.** `items`
intersects as a declaration and is handed back to the parser as one node, which is §2's rule
unchanged. The bounds take the tighter end — the greater `minItems`, the lesser `maxItems` — and
a `minItems` above a `maxItems` is an empty intersection and refuses. `uniqueItems` holds where
either conjunct states it, because a conjunction of constraints is satisfied only by an instance
satisfying both. Every `contains` is kept: two `contains` predicates are two independent
`AtLeastOne` rules over the same value, never merged into one, because `contains: A` and
`contains: B` demand a member satisfying each and a single merged predicate would demand one
member satisfying both.

That last clause is the only place the array case is not symmetric with the object case, and the
reason is that `properties` is keyed and `contains` is not: two declarations of one KEY are one
field, while two `contains` are two facts about the list.

### A presence clause whose required half is a disjunction of groups

Group A's clause carries "its OWN required group" — one group, read as a conjunction of names.
The bundle also spells that half as a DISJUNCTION: one branch states an `anyOf`
of `required` groups where the others state `required` directly.

**A clause's required half is a disjunction of GROUPS, which is what its forbidden half already
is.** `Presence.forbid` holds groups because `not: {"required": [a, b]}` forbids the PAIR and
says nothing about either name alone. The same reading of the required half makes
`required: [a, b]` the single group `((a, b),)` and an `anyOf` over `required` the groups it
states. A clause holds when at least one of its groups is present in full, and a clause stating
no group states no requirement and holds. One field means one thing — the groups this branch's
requiredness admits — where a second field beside it would make one clause carry two readings of
one keyword.

Both halves derive from `schema.required_groups`, which already reads `required` and a
combinator over `required` into groups. That is §11's one reading with two readers: the `not`
half and the required half reach the same derivation from the two sides of one branch.

Dropping the disjunct is not available. Where a document's modes include an empty one — no key
present — a rule with the disjunct dropped rejects it, so the model is TIGHTER than its document.
§2 admits a widening and never a narrowing.

`RequiredGroups` reads the same document fact as a RULE and stays separate, for the reason
`Presence` states itself: a clause has no `errors` because a branch is not violated on its own,
and only the combinator above it decides how many branches an instance may satisfy.

**A conjunction of a group with a disjunction of groups DISTRIBUTES into a disjunction of
groups**, which is the same principle the `$ref` row's distribution clause states one row above:
conjunction distributes over disjunction. `required_groups` reads an `allOf` of single-group
conjuncts as one group, the union of their names; an `allOf` whose conjuncts each give a LIST of
groups is the product of those lists with the names unioned per combination, and the single-group
case is that product over one-element lists. So
`allOf: [{"required": [g]}, {"anyOf": [{"required": [a]}, {"required": [b]}]}]` is the two groups
`((g, a), (g, b))`, which is what the document says.

The product case never takes `partial`, for the reason the `allOf` case already does not: dropping an
unreadable conjunct from a product leaves FEWER names in each group, which under a `not` forbids
MORE, and a rule stronger than its document is the narrowing §2 refuses.

---

## 6. Keywords we admit and do not compile

None of these can constrain an instance, so none compiles to a type, a rule or a base. Each is
admitted **by name**. Several carry something anyway, and the table says what.

**`errorMessage` and the registry data keys belong to this section.** Neither
constrains an instance — `errorMessage` customises an `ajv-errors` message and the registry keys
are a registry's own instance data — so no annotation drops a fact for them and there is nothing
to widen. They are admitted by name and compile to nothing. **Whether the reader is TOLD is a separate
column of the cell, and the two rows answer it differently**: a dropped
`errorMessage` is reported, the registry data keys are not, and neither is `$comment`. Three
cells settle it by agreeing in every other field and differing here — a comment is manifestly a
note and a registry's own data is manifestly data, so a reader who is not told has lost nothing,
while `errorMessage` sits BESIDE a constraint and a reader who is not told has no way to see that
the class carries nothing for it. `errorMessage` is the only reported cell in the table.

<!-- generated from codegen/keywords.py -->
| keyword | what it does, or why nothing |
| --- | --- |
| `$schema` | Nothing on the class, but it selects the **validator** the schema half runs, and through it the format checkers a type may be selected for. The one annotation that decides a behaviour, and it decides it on the schema half. |
| `$id` | Nothing. draft-07's URI for the document, and the base a reference in it would resolve against — so it identifies and does not constrain, and an annotation that omits it omits no fact. It cannot redirect a reference here either: the bundle states it at document roots and at no node below one, every non-local `$ref` is an absolute URI, and the resolver matches a reference's trailing path segments against the bundle's own file set rather than against any `$id` — which is why a document whose `$id` names a path other than its own is still reached at the path it is written at. Bundle 3.2 states it nowhere and 3.3 states it at every document root, and that is the whole of the difference it makes. |
| `title` | Nested → nothing: a nested node is named by its property or entry key. Its presence selects `StrEnum` over `Literal` for an enum node. Never rendered. ROOT → the symbol. BRANCH → the branch class's name. |
| `description` | A `$ref` sibling's description wins over the target's; a composed base's loses to the document's own. ROOT class → the docstring; ROOT alias → `Field(description=…)`; ROOT enum → the enum's docstring. PROP → `Field(description=…)`. ELEM / MAPV → the named alias carries it. BRANCH that is a class → its docstring; a non-object branch of a nested union → its own annotated type. CONJ / RULE → nothing. |
| `examples` | Nothing on the model. The accepts check replays every one, at every position: a ROOT example constructs the class, and an example at a nested node is validated against that node's own annotated type. A payload the document refuses is a spec defect, reported by document and pointer; one the document accepts and the class refuses is ours. |
| `$comment` | Nothing. A note to a reader. |
| `readOnly`, `writeOnly` | Nothing. Pydantic can render them, but the SDK has one model per document and no read/write split for them to state. |
| `deprecated` | A `false` → nothing. Rendered, so graded. ROOT / BRANCH → the class's `json_schema_extra`. PROP → `Field(deprecated=True)`. |
| `enumDescriptions`, `x-enum-descriptions` | Member docstrings on the enumeration, keyed by the member's value. Two spellings of one keyword; both are read. |
| `enumMetadata` | Nothing: recovery and action metadata for a reader. The `enum` beside it has already closed the value set. |
| `notes` | Nothing: English sentences for a reader. |
| `docs_url`, `valid_from` | Nothing. An extension manifest's own header at a schema root: where a reader goes for the extension's prose, and the protocol version it became valid at. Neither says anything about an instance — draft-07 says the same by ignoring an unknown key — so an annotation that omits them omits no fact. `extensions/adcp.json` is the one document stating them at a schema position, and it states a real schema beside them, so it emits normally with the two compiling to nothing. |
| `discriminator` | Nothing on the class. It names a branch where that branch pins more than one `const`, and separately it **confirms** a dispatch key the branches already state — it does not establish one. A union whose branches pin a distinct const dispatches on that property whether or not the keyword is present, and a declared keyword the branches do not confirm is not a dispatch source. |
| the `x-` namespace | Nothing, and **still listed by name** — see below. |
| `x-max-length-4.0`, `x-max-items-4.0`, `x-max-properties-4.0` | Nothing **at this version**, and the keys are listed apart from the namespace line because each one reads as a bound. Each sits beside the `type` word it would bound — `x-max-length-4.0` beside a `string`, `x-max-items-4.0` beside an `array`, `x-max-properties-4.0` beside an `object` — and names the bound **version 4.0** will impose, which is what the suffix says. A 3.3 document is not bounded by it: 3.3's validator ignores the key, so a value exceeding the number is a value the document ADMITS, and a class carrying it as a constraint would refuse a payload its own document accepts — the narrowing §1 and §2 forbid outright. So these annotate **by the version the bundle is**, not by how they are spelled. Promoting them is a 4.0 row: each becomes the cell its unprefixed keyword already has — `maxLength`, `maxItems`, `maxProperties` — and this line is the reason it had not happened yet. |
| `errorMessage` | Nothing. An `ajv-errors` extension customising a validator's message, so it constrains no instance and an annotation that omits it omits no fact. It has no Pydantic rendering and never needed one. **The drop is reported**, at every position the document states it at. |
| `version`, `lastUpdated`, `vocabulary`, and the registry payload keys | Nothing. A registry's own instance data sitting at a schema root: `_generated`, `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning`. None of them constrains an instance, and draft-07 says the same thing by ignoring an unknown key, so an annotation that omits one omits no fact and admitting it by name says only what is true of instance data. A root stating only these keys is the empty schema and emits as a permissive root model; a document stating them BESIDE a real schema emits normally, with the data keys compiling to nothing. |
<!-- end generated -->

### The `x-` namespace is admitted by prefix AND listed by name

A vendor extension cannot be a schema keyword, so the `x-` prefix is sufficient to admit one.
That is the one place the by-name principle has an exception — and the exception is leaky, which
is why the names are kept as well: a key like `x-enum-descriptions` carries member docstrings, and
the prefix rule alone drops it silently.

So a key matching the prefix is admitted, and every key the bundle carries is also listed. A key
in the namespace but not on the list is admitted and **reported**, so it gets read once rather
than assumed to be metadata.

Carrying only organisational metadata: `x-accessibility`, `x-added-in`,
`x-adcp-file-size-units`, `x-adcp-hoist`, `x-adcp-model-context-inline`, `x-adcp-schema-uri`,
`x-adcp-sdk-local`, `x-canonical-policy-required-params-not-enforced`,
`x-compatibility-projection-only`, `x-deprecated-enum-values`, `x-deprecated-enum-values-doc`,
`x-deprecated-in`, `x-entity`, `x-entity-definitions`, `x-governed-commitment`,
`x-idempotency-key-required`, `x-legacy-fallback`, `x-mutates-state`, `x-operation-family`,
`x-removed-in`, `x-status`, `x-superseded-by`, `x-task-result-schema-overrides`,
`x-tool-summary`.

Four need a reason beyond that:

- `x-adcp-validation` constrains in intent and not in the document, so a model enforcing it would
  be narrower than its document (upstream: `adcontextprotocol/adcp#8472`).
- `x-extensible` and `x-pattern` describe an open vocabulary in a namespace the validator ignores,
  so the document's accepted set is the closed `enum` beside them and a closed `StrEnum` is
  faithful to it.
- `x-canonicalization` reads `"set"` beside the document's own `uniqueItems` and `minItems`, so
  the duplicate half is already the document's own keyword and the order half is not an
  acceptance statement.
- `x-adcp-open-payload` sits beside `additionalProperties: true`, or on a typeless node, so
  `allow` and `Any` already carry it.

---

## 7. Keywords we refuse — the set is empty

**No keyword's presence refuses a document.** The section stays, with its membership still a
projection of the declaration, because a reader looking for "which keywords refuse" has to find
the answer, and because the one refusal left in the compiler is not a keyword's at all.

**`Effect.REFUSE` does not exist**, so "refuse a document on a keyword" is a name error rather
than a path the compiler can take. Both of the rows that once refused belong to §6, each for a
reason that was never about the document's accepted set:

- **`errorMessage`** has no Pydantic rendering, and never needed one: it customises a validator's
  message and constrains no instance, so an annotation that omits it omits no fact. The drop is
  reported.
- **The registry data keys** — `version`, `lastUpdated`, `vocabulary`, `_generated`,
  `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`,
  `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`,
  `stability`, `usage_notes`, `versioning` — are a registry's own instance data at a schema root.
  Admitting a key by name says it carries no acceptance meaning, which for instance data is simply
  true, and draft-07 says the same thing by ignoring it. **A refusal is the wrong instrument for a
  signal**, because it costs the document its type to carry it; the signal that a document is a
  registry rather than a schema lives in the approximation record — a root stating only these keys
  is a permissive root model (§4) with an upstream attribution asking the registry either to drop
  its `$schema` or to declare a schema. A document that states these keys *beside* a real schema —
  a `type` and `properties` at its root — emits normally, with the data keys compiling to nothing.

**The one refusal the compiler can still mint is not a keyword's.** Where the document of record
(§3) is undefined, there is no schema for `strict_validate` to validate against and no document
for §8 to grade against, so §2's partial-model objection applies with nothing to answer it. The
principle is that **the document has no defined accepted set**, and three cases reach it:

- a `$ref` whose target is not a bundle document;
- a cross-document reference cycle, which the inliner cannot resolve. A LOCAL cycle is not one
  of these — it is never inlined and renders as a forward reference (§5);
- a document that fails its own declared draft's meta-schema, so it is not a schema at all and
  has no accepted set to be faithful to.

Whether any of the three is non-empty is a property of one bundle version and is re-measured on
each. **The refusal stays in the compiler regardless**, because a bundle that grows one must
report it rather than crash on it (§9).

<!-- generated from codegen/keywords.py -->
| keyword | why |
| --- | --- |
<!-- end generated -->

The grid above is generated and is **EMPTY**, because no cell can say `REFUSE` any more. The
section's title is therefore a fact the artifact holds rather than a claim its prose makes, which
is the only form in which this document is worth reading.

**The drop is reported at every position the keyword occupies, and not only where a conjunct
encloses it.** A keyword's effect is a decision about the keyword at a position;
a report that reaches one position and not another is a defect in the channel, not a second
decision. **So the channel is a function of the DOCUMENT** — `bundle.reported_drops` over the one
descent walk, which carries the position the column assigned and cannot privilege one. A `/then`
is a RULE source the rule lowering reads raw, so a channel screening `CONJ` never sees it.

A keyword in none of §5, §6 or §7 is one the bundle does not use. The first document to carry one
**widens its node to `Any`** — §5's widening TOP — and declares the approximation, so a new keyword
is loud rather than ignored. `Any` and not a narrower widening, because an unrowed keyword's reach is
unknown: draft-07 ignores it, so the document may be narrower than `Any` and can never be wider,
and `Any` is the one widening that is safe without knowing what the keyword does. A node that loses
its whole type is as visible in the report and in the emitted module as a refused document was.

---

## 8. How we know the output is right

**THREE checks and one declared set**, run once per emitted class against the schema document it
names. All three are payload checks: a value is CONSTRUCTED from the node's own keywords, and the
class and the document are asked about the same value. Nothing here reads one schema against
another, and nothing here grades a rendering. **Anything that is not one of these three checks or
the widening set they prove does not belong in this section.**

- **Accepts.** Construct the values the document admits and build the class from each. A refusal
  here means the model is tighter than its document, which is the defect that matters.

- **Refuses.** Violate one keyword the node states and offer the result. An acceptance here means
  the model is wider than its document, and the refusal is read AT THE LOCATION the violation was
  made — a class refusing for some other reason has not been shown to carry the keyword.

- **Dumps.** Instantiate from the accepted value, dump, and validate the dump against the same
  document.

 **An approximation is a claim about the first check, and that check is what proves it.** §2 says
  every approximation of acceptance is a widening. A widening is therefore not a thing a
  declaration asserts and a reader believes: for every fact an approximation drops, the
  construction takes the values that keyword distinguishes — the same coverage classes below — and
  the class must accept every one of them. An approximation that still refuses a value the document
  admits is a NARROWING wearing a declaration, and it fails here, by value and by pointer. This is
  what keeps "approximated" from being an allowlist.

 **THE CONSTRUCTION COVERS THE NODE'S ADMISSIBLE SPACE BY CONSTRAINT CLASS; IT DOES NOT SAMPLE
  IT.** "Never tighter" is a claim about every value the document admits, and a sampler reports only
  the values it happened to produce — so it can run green forever against a type that refuses a
  whole class of admissible value. For each keyword the node states, the construction takes the
  classes that keyword distinguishes: every member of an `enum`, both sides of each bound and the
  bound itself, and for a `format` every case the format's own checker admits rather than the case a
  generator finds most likely. A Python type chosen for a node admits everything the node admits, or
  the choice is a narrowing and this check names it with the value.

 **AND THE COVERAGE IS WHY CONSTRUCTION IS THE ONLY INSTRUMENT THAT CAN ANSWER.** The classes a
  keyword distinguishes are enumerable from the keyword itself, so they are built, not found; a
  search over the space the keyword admits is both more expensive and weaker, because it cannot
  report which class it failed to reach. **The witness set of a node is therefore a function of its
  keywords: one admitted value, and one violation per keyword stated.** A node stating _k_ keywords
  owes _k_+1 payloads, and a document owes the sum over its nodes — never a product, and never a
  count chosen by a parameter.

 **A REFERENCE CONTRIBUTES ITS TARGET'S WITNESS, AND A CYCLE CLOSES ON THE POINTER.** A `$ref` takes
  the value already constructed for the pointer it names, so no subtree is constructed twice. A
  reference reaching a pointer whose construction is in progress is a back edge: it is omitted where
  the document makes it optional and takes the target's minimal value where the document requires
  it. The memo that makes the walk linear is the memo that closes the cycle, so **no depth parameter
  exists to be chosen.**

 **Every position a widening can land at has an instance location.** The
  construction places a value at the instance location the node's pointer names, and a position with no
  location makes a widening UNPROVABLE — which that check counts as a failure, correctly, since
  an unproved widening is a claim with no instrument on it.

  - **A mapping value** — `#/properties/x/additionalProperties`, and the same for
    `patternProperties`. The location is `x` then any key the mapping admits; a key is a free
    choice and the construction makes one, so the location exists and must be read.
  - **A `definitions` entry** — `#/definitions/x`. This one has no location of its own and never
    will: an entry is reachable only through a `$ref` that names it, and §5 declares no entry
    nothing references. **It needs no new reading, because the rule that a declaration travels
    with the fact already re-points it to the referring pointer**, which is a `properties`
    segment the construction already places. The two settlements compose: one gives the declaration a
    pointer the declaration names, and that same pointer is one the construction can reach.
- **Dump.** Serialize the instance and validate the dump against the document. A failure means we
  emit something our own schema refuses.
### THE THREE CHECKS ARE APPLIED COMPOSITIONALLY, AND CERTAINTY COMES FROM THE TABLE

**SAMPLING NAMES A DEFECT; IT NEVER ESTABLISHES THE ABSENCE OF ONE.** A sampled value that
disagrees is a defect with a witness, which is why a sampler is a fine instrument of record for one.
But *"the class is faithful to its document"* is a claim about every value the document admits, and
no sample delivers it at any budget. **Construction delivers it for the classes the keywords
distinguish**, because those classes are enumerable from the keywords themselves — which is why the
construction is the instrument here and the sampler is not an instrument of this section at all.
Two consequences, and both are rules.

**A REFERENCED DOCUMENT IS GRADED BY ITS OWN PAIR, SO AT A REFERRING POSITION IT IS A FIXTURE.**

A class under grade varies **its own** payload. Every subtree it reaches through a reference is a
document with a pair of its own, graded there — so at the referring position the instrument needs
**one instance that document admits and one it refuses**, not a generated space. Three properties
over a reference holding fifteen branches is **three plus fifteen, never three times fifteen**: the
product becomes a sum because nothing is re-derived that is already decided elsewhere. **This is the
whole of why the cost is a sum**, and it is the same rule the reference memo states structurally:
one witness per pointer, reused wherever that pointer is reached.

**AND THE SAME RULE GOVERNS A WIDENING'S PROVING VALUE: IT IS A QUESTION ABOUT A DECLARATION AND A
DOCUMENT, NOT ABOUT THE PAIR THAT ASKED.** A declaration sits at one pointer in one document and
the value that demonstrates it is a property of that pair of facts alone. Keying the held answer on
the *asking* pair's pointer gives one subject several keys — three pairs deriving an identical
multi-megabyte subject are given three, and each pays the construction again — where the narrowest pair's
answer already serves every one of them.

So **the key is the declaration**: the document, the declared pointer, the keyword and the class
label, which are a function of the declaration and not of who reached it. That is the same "product
becomes a sum" one layer over, and it is what makes a value constructed once at the cheapest
position the proof for every position that contains it.

**AND THE KEY IS A POINTER IN BOTH PLACES, WHICH IS WHAT MAKES THE TWO MEMOS ONE RULE.** The witness
memo is keyed on the node's pointer and the proof memo on the declaration's; neither is keyed on
text, neither is held between runs, and neither needs to be, because the thing they avoid repeating
is a walk and not a search.

### A DECLARATION IN A `definitions` SECTION IS PROVED BY THAT ENTRY'S OWN CLASS, AND BY NOTHING
THAT REFERENCES IT

A section entry has **no instance location in a referring document**. The referrer's instance tree
contains the entry's *content* at whatever position references it, not a slot named
`definitions/<key>` — so a value placed at the declared pointer is a value at a location no
instance of the referrer has, and the obligation can never discharge it there.

**A containment rule that carries such a declaration to the referring root is claiming an
obligation nothing can satisfy**, which is worse than claiming none: it reads as coverage. The
declaration belongs to the entry's own pair, which does have an instance location for it, and that
pair is where the proving value lives. Containment therefore **stops at a reference boundary** — a
declaration travels within one document's instance tree and not across a `$ref`.

### THE VALUE CLASS FOR A CONDITIONAL PARTITIONS ON THE CONDITION

"A value the node admits" does not exercise what a dropped `if`/`then` was constraining, because an
instance that fails the condition satisfies the conditional vacuously. A single class over the node
therefore proves nothing about the widening: it can be an instance the document would have admitted
with the keyword in place.

**So a conditional's subject is TWO classes — the condition matching and the condition not
matching** — which is the same split the bound rows already take, where a bound's subject is both
sides and the bound itself. **Only the matching one exercises the fact the widening dropped**, and
it is the one the proof requires; the other is what shows the vacuous case is still admitted.

**AND THIS IS A RULE ABOUT THE CONSTRUCTION, NOT ABOUT THE RECORD.** The explosion is in generating into an
inlined subtree, so substituting a fixture collapses it **whether or not the record inlined the
bytes** — which makes it a change to how we grade rather than a change to the artifact. It is the
cheap half of what un-inlining would buy.

**A REFERRING POSITION IS WHERE A REFERENCE LANDS IN THE NODE BEING GRADED, AND NEVER WHERE A
`$ref` STRING APPEARS IN THE RAW DOCUMENT.** The record's own text cannot say a subtree came from
elsewhere — that is a fact about the record, and not a reason the GRADED NODE cannot be asked.
`applied_schema` conjoins what the enclosing nodes assert about the same instance, so a reference
routinely arrives at a pointer **the document does not spell**: a raw branch holding no `$ref` at
all can be graded as a node almost all of whose bytes sit in one spliced `allOf` conjunct.

**AND A FIXTURE POSITION IS EVERY INSTANCE LOCATION THE NODE DECIDES, WITH ITS VALUE CONSTRUCTED FROM THE
CONJUNCTION OF EVERY STATEMENT ABOUT IT.** Several conjuncts can each state part of what one key or
one element must satisfy, so **one value for the location** is the answer that cannot be empty,
where a fixture per conjunct is the empty intersection this section already names.

- **A CONSEQUENT IS A SCOPE OF ITS OWN AND NOT A CONJUNCT.** A `then` or an `else` states its part
  only when its condition matches. Read as a conjunct, a document's thirty consequents demand a
  single value satisfying all thirty scenarios at once, and none exists.
- **A UNION BRANCH IS AN ALTERNATIVE, so no single value answers for it** — what is substituted is
  the branch's own reduction. Pinning a union from the union node alone yields
  `{"allOf": [{"oneOf": [{"const": null}]}, {"type": "object", …}]}`: an empty strategy, with the
  node left untouched.
- **NOTHING UNDER `not` OR `if` IS SUBSTITUTED AT ALL**, because there a restriction WIDENS, so a
  pin would narrow the admitted set rather than sample it.
- `patternProperties` and `contains` are conjoined and never replaced — read as a conflict with
  `items`, `contains` leaves its frontier empty.

**AND A PIN IS KEYED ON THE INSTANCE LOCATION AND NEVER ON THE POINTER THAT STATES IT.** The three
rules above name three *kinds* of statement, and reading them as three *scopes* is the defect:
a consequent, a union branch and the conjuncts beside them can all decide **one** location, so they
are one group and get one value. Grouping by the pointer instead hands the same location two
independent pins, and two pins on one location do not narrow the node — **they empty it.**

**AND WHERE THERE IS NO ONE VALUE, THE UNCONDITIONAL POSITION IS LEFT EXACTLY AS THE DOCUMENT STATES
IT.** Not restricted, not reordered, not constructed against a narrowing of itself: left standing. A
statement left standing cannot contradict a value constructed from a conjunction that contains it, and
**no restriction of that position and no ordering of two independent constructs preserves satisfiability.**

**AND A REDUCTION THAT YIELDS AN EMPTY NODE IS A DEFECT, NEVER A LOST SAVING.** The fail-safe then
pays the unreduced construction the reduction exists to avoid, and an empty reduction is indistinguishable
from a reduction that found nothing to do, so the budget it overruns gets read as the work being
inherently large. **A reduction reports emptiness as a failure, loudly, and
a pair whose reduction came back empty is a defect report and not a slow pair.**

**AND THE SUBSTITUTION IS A STATEMENT ABOUT GENERATION ONLY.** Every instance a substitution
produced is screened against the pair's own node before the class sees it, so no pair is graded on
a value its document does not admit, and no pair stops being graded on a value it is graded on
today, and the comparison is over EVERY pair: a change to generation is sound when pairs gain a
verdict and none loses or changes one.

**A REFERENCED DOCUMENT'S OWN INSTANCE IS SUBSTITUTED WHERE IT DESCRIBES AN INSTANCE OF ITS OWN, AND
NOWHERE ELSE.** PROP, ELEM, MAPV, KEY, DEF, and a whole `anyOf`/`oneOf` branch are such positions:
the referenced document is the entire answer about one value, and one value it admits is a fixture.

**A reference at an `allOf` conjunct, inside `if`/`then`/`else`, under `not`, or anywhere else that
CO-DESCRIBES THE ENCLOSING INSTANCE IS NOT ONE.** There, two or more documents each state part of
what one value must satisfy, so a fixture per conjunct is two documents answering one question and
**the intersection is empty** — the construction then yields nothing at all rather than yielding too much.

**At a co-describing position the reference is TRANSPARENT: the walk reads through it and keeps
looking below**, which is the reading `architecture.md` already applies to the record's storage.
The fixtures then land inside the conjunct, at positions that do not meet each other.

**A BARE `oneOf`/`anyOf` DECLARES THE CONTAINER ITS BRANCHES AGREE ON.** Draft-07 admits an
instance only through a branch, so **a union every branch of which declares an object has declared
an object** as surely as `type: object` does — the same entailment the keyword reading already makes
for `contains` implying an array. This is what lets "two object declarations compose as an `allOf`"
reach a DISPATCH ROOT, whose every property sits on its branches and whose own node therefore
states no type word at all. Without it the composition rule is written, correct, and never reached:
the conjunct is dropped and the class carries the keys as `Any`.

**AND AN `Any` WHERE A TYPE IS DERIVABLE IS A WIDENING NOBODY DECLARED.** It PASSES all three checks — a
model wider than its document is permitted by §2 — so no verdict moves when it is wrong, and the
only thing that reports it is a reading over the annotation itself. A dropped conjunct is therefore
invisible to the construction at exactly the positions where it costs the most.

**AND THE RESIDUAL EMPTINESS IS REPORTED, NEVER SWALLOWED.** Two fixtures can still meet on one
instance through `uniqueItems` or a tuple-valued `items`. That is a non-pass with a name — a
`strategy_error` attributable to its pair — and never a silent green, because a pair the instrument
cannot grade is not a pair that passes.

**Two costs, stated rather than discovered.** A fixture is one instance where a construction is many, so a
defect reachable only by an unusual value *inside* a referenced subtree is found by **that
subtree's own pair or not at all** — which is correct, and is the whole content of "graded there",
but it must be said out loud because it moves where a defect is found. And **the fixture is DERIVED
from the referenced document, never hand-written**: a hand-written one is a thousand files to
maintain and a silent exemption the first time a document changes under it.

**AND THE BUNDLE ALREADY STATES ITS OWN INSTANCES: `examples` IS THE SOURCE, AND THE HARNESS USES
IT.** `examples` is JSON Schema's keyword for *this is a valid instance of
this schema* — the author's own declaration, living in the schema and maintained with it.

**So the instance lookup is: the committed store, then `examples`, then a construction.** An `examples`
member is screened exactly as a held instance is, and one the document REFUSES is an upstream
defect to be filed — never a reason to bypass the mechanism. It is better than a constructed value as
well as cheaper: a realistic payload rather than a generated one, and at a referring position the
referenced document's own `examples` is the natural fixture with no construction at all.

**AND WHERE A NODE CARRIES NONE AND A CONSTRUCTION CANNOT PRODUCE ONE, THE ANSWER IS TO PATCH THE SCHEMA
AND SEND THE PATCH UPSTREAM** — not to keep an instance of our own. §1 already decides what a patch
is: *"Every patch is also the upstream pull request … carrying one is a way of shipping the fix
early rather than a way of living without it, and the patch disappears when the backport lands."*
An `examples` keyword is the protocol's own statement, reviewed by the people who own the schema
and useful to every other implementation; **an instance in our store is ours alone to maintain and
means nothing to anyone else.** The maintenance question below does not arise for a patch, because
there is nothing of ours to maintain.

**THE HAND-WRITTEN INSTANCE IS THEREFORE THE LAST RESORT AND NOT THE ANSWER** — reached only where
a node has no `examples`, no terminating construction, and no upstream answer yet. Its allowance stands, on
the reasoning below, and it is expected to be empty.

**AND THAT REASON IS ABOUT SCALE AND SILENCE, SO IT DOES NOT REACH A HANDFUL.** The hazard named
above is a thousand files drifting invisibly. Neither half holds for a few: an instance the store
holds is **re-offered to its own document on every read**, so one that stops being admitted
**reddens with that document's name**. The drift the rule exists to prevent is self-reporting at
this size, which is the whole difference.

So where a CONSTRUCTION CANNOT PRODUCE AN INSTANCE AT ALL — a strategy builder that will not terminate on
the document's own form — **a hand-written instance is admissible for that document, screened, and
counted**: it is admitted by its own document, its pair passes all three checks, it records no
budget cut, and the commit names it as hand-written so no reader mistakes it for a constructed one.
**It is the generator's defect that is being worked around, and the stopgap is not the fix**: the
next document of the same form hits the same wall, and a hand-written entry is replaced by a constructed
one the moment a construction can produce it.

**WHAT MAKES THIS NOT AN EXEMPTION is that nothing is excused.** The pair is graded, by the same
three checks, against the same document; only the *provenance of the value* changes, and that is
recorded rather than hidden. An exemption would be the pair passing without being graded.

**A COMBINATOR ROOT IS NOT GRADED BY CONSTRUCTION THE POWER SET OF ITS STATEMENTS, AND THE COMBINATOR
THAT COSTS THAT IS THE CONJUNCTION, NOT THE UNION.**

**A `oneOf` root is already a sum.** Its branches each emit a class, each carries a pair, and the
generator takes one branch at a time. There is no power set there to avoid.

**An `allOf` root is the one that is 2^n, and the cost is in the SEARCH rather than the
intersection.** The only way to generate from an intersection is to intersect the statements first,
and finding which of them will intersect is what enumerates subsets. So the rule is about that
search: **the statements are covered by one greedy pass, each group is constructed from its own
intersection and screened by every statement, and the cost is n² intersections and never 2^n.**
Nothing is re-keyed onto a branch, no class is added, and no pair moves. A conjunct is not an
alternative, so it carries no pair of its own: a value for one conjunct is not a value for the root.

**AND THE REFUSES DIRECTION KEEPS THE ROOT, AT NO COST.** The refusal witness is not generated — it
is the accepted instance perturbed one keyword at a time, screened against the root. So
`oneOf`'s "an instance two branches admit is refused" is decided by the root's own
validator, and no reduction of what the GENERATOR is offered can weaken it.

A union's branches are each verified on their own, so the root's own construction re-derives what is
already decided — and it does so by enumerating **every SUBSET
of the branches**, because the canonicaliser must merge each combination to know what the union
admits. That is `2^n`, not a product, and it is why no constant factor reaches it: an eighteen-branch
site is a quarter of a million subsets, and a generous budget completes a fraction of one percent
of them. **A speedup is not available at any multiple.**

**So a composite root is discharged by finite obligations and never by one unbounded search:**

1. **every branch pair green** — which is the existing check, at the existing cost;
2. **the dispatch resolves** — §4's sources, and a root that cannot name the branch a payload is
   fails that check already;
3. **disjointness proved or declared** — an inseparable `oneOf`'s own declaration is exactly this
   obligation's negative answer.

A branch that is itself a combinator root recurses by the same obligations. **And the recursion
does not reach every root:** a pair the construction cannot finish may carry no combinator anywhere, and
those are the table's to discharge and not this section's.

**A RESTRICTION MAY NOT BE REMOVED TO MAKE A NODE CONSTRUCTIBLE.** Removing one **widens** the
admissible set, so instances constructed from the stripped node are not instances the document admits —
nearly every one is refused by the pair's own entry point and fails to conform to the full node, so
an obligation written that way reports almost every root as refusing a valid value. Screening by
the full node restores soundness and reintroduces the product as rejection sampling. And the
product is not at the root to be removed in the first place: most roots state `properties` beside
the combinator and those values carry combinators of their own. **The sound form is the table
below, and there is no shortcut around it.**

**AND FOUR KEYWORDS DO NOT COMPILE ONTO A UNION BASE AS A PER-BRANCH COPY.** `additionalProperties`
is scoped to the node's own
`properties` and cannot see a branch's, so a per-branch copy of it means something else entirely;
and `not`, `if`/`then`/`else` and `dependencies` each state a condition over the whole instance
that no per-branch copy reproduces. A check built on "strip the combinator and grade what is left"
cannot be stated for a keyword whose meaning changes when it is moved.

**AND THESE FACTS DO REACH THE CLASS**, though the renderer carries none of them in a `_ROOT_*`
attribute. `additionalProperties`
arrives as the model's extra-field policy, and every combinator root that forbids
extras has a class that forbids them. A root-level `not` is enforced too, checked
by offering the class the instance that `not` forbids beside a control the document admits. **So
the four are a reason an obligation cannot be WRITTEN, not evidence of a fact dropped.** A claim
that any of them is dropped needs the payload, as every claim here does.

**AND CERTAINTY ITSELF COMES FROM §5's TABLE, NOT FROM THE CONSTRUCTION.** §5 is a keyword × position
decision table: each cell says what one keyword at one position compiles to. **Prove each cell
once** — the annotation it emits admits exactly the values that keyword admits at that position,
against the boundary values the keyword itself names — and **prove each composition rule once** —
`allOf` intersects, `anyOf` unions, a restatement merges — and faithfulness over any document
follows **by structural induction on the document**. The obligation becomes the table's cells plus
the composition rules, which is finite and terminates, and it covers documents no construction will ever
reach.

**The construction is then a cross-check on the table rather than the proof**, and that is the role it can
actually fill: a constructed disagreement means a cell is wrong or the walk applied the wrong cell, and
either is a located defect rather than a mystery. **The carve-outs are already written down** — the
declared approximations and the narrowings the registry admits — so "faithful except where
recorded" is a statement the induction can quote rather than a hedge.

**THE INDUCTION HAS FOUR PREMISES.** Three are checked: the positions are closed under descent;
nothing outside the table reaches the output, which is *why* nothing is refused; and the walk
applies the cell the table names, of which §5's grid equality is half.

**The fourth is that a cell is a function of `(keyword, position)`. It is not.** It is a function
of `(keyword, position, CO-OCCURRENCE)` — what else the node states — and §5's own table says so:
*"the table is keyed by position and a co-occurrence is not one, so it belongs to the sentence of
the cell it qualifies."* Most live cells condition their answer on something other than the
position: *where* this, *beside* that, *ALSO*, *enclosing*, *unless*. `const` reads the same field's
enclosing declaration. `additionalProperties` is read after the document-side fold. §3a's catalogue
collects vocabularies before emission, so one position's annotation is a function of every other
position stating the same value set.

**So "prove each cell once" has no denominator.** A probe proves ONE answer per cell — the one its
own co-occurrence selects — and nothing says how many answers a cell has. The induction's step is
not local, which is the property the whole argument rests on.

**THE FIX IS TO THE TABLE'S FORM, NOT TO THE PROOF: a cell that conditions must state its
conditions as DATA.** A co-occurrence written in English cannot be enumerated, so the obligation
cannot be counted and the equality cannot close. Written as a condition the table carries, each
cell's answers are a finite enumerable set, the live-cell count becomes a live-ANSWER count, and
the induction's step is local again. Until then the cell proofs are sound and incomplete, and they
must be reported that way — **complete only up to the co-occurrence each probe selects**, never as
coverage of the table.

**THERE IS NO THIRD CHECK.** A comparison of the class's
`model_json_schema()` against the document is **deleted** — code, tests, pins,
prose, as if it had never existed. It was not a check on the artifact; it diffed schema TEXT, and
it existed as a proxy for coverage the construction had stopped providing.

**A fact no payload can demonstrate is not a fact about the artifact.** A consumer meets these
classes through validation and construction, so a disagreement a constructed value cannot expose is a
disagreement in rendering, and §2's "nothing rewrites emitted output" already says rendering is
not ours to grade. Where the construction provably cannot reach a keyword, the honest answer is to NAME
that residue and raise the example count until the pile stops shrinking — not to diff text and
count the difference as a defect.

**THE WIDENING SET, which is the one thing beside the three checks.** §2 makes every keyword the
model cannot express a WIDENING rather than a refusal, so the artifact is deliberately looser than
its document in a declared, enumerated set of places. That set needs proving, and the proof is
the construction and nothing else: for every fact an approximation drops, the construction takes the values that
keyword distinguishes and **the class must accept every one of them.** An approximation that
still refuses a value the document admits is a NARROWING wearing a declaration, and it fails
here, by value and by pointer. That is what keeps the declared set from being an allowlist, and
it is why the widening set belongs to the round trip rather than beside it.

**AN APPROXIMATION EARNS ITS PLACE IN EITHER DIRECTION, AND IS DECLARED AT THE NODE THAT STATES
IT.**

**1. The criterion has two directions.** A dropped constraint's witness is *"a payload the document
admits and the class now admits"* — the ACCEPTS direction. A dropped CONDITIONAL's witness is the
opposite: a value the document **refuses** and the class admits. Both are the same defect — the
model is wider — so **both earn a declaration, and a widening whose only witness is a refusal is
earned exactly as one whose witness is an acceptance.** The refuses-check is the instrument that
produces it, and it must not be offered the value through any path that consults the document first.

**2. A fact is declared ONCE, at the node the document STATES it, and never once per pointer the
record inlines it to.**

**THE IDENTITY IS READ OFF THE NODE WHOSE KEYWORD THE FACT IS.** Where the
dropped fact is itself a subschema — a condition, a branch — the fact object carries its own origin
and the stating site is read off it directly. Where it is not — a count, a length, a pattern map,
an inseparability — **the identity is the ENCLOSING node's**, because that is the node whose keyword
was dropped and the only schema node in play. So the parser's node types must each carry the raw
node they were built from, as the conjunct type already does, and the inliner must export the
origin of a node by identity rather than by pointer: the walk folds a conjunct into the enclosing
node's pointer space, so a declared pointer is routinely at no pointer the record spells, and a
pointer-keyed origin map cannot answer.

**AND A FACT IS DECLARED ONLY BY THE STATING DOCUMENT'S OWN MODULE**, not merely deduplicated
within each module — the report sums per document, so per-module deduplication leaves one entry per
referring document and the figure cannot fall. **The risk this takes on is named rather than
hedged:** a stating document whose own walk never reaches that pointer would declare the fact
nowhere. That failure is already caught, by the equality this section requires in both directions —
a fact minted and declared nowhere reddens it — so the risk is detected rather than silent, which
is the condition on which it is accepted. One
conditional in one document reaches thousands of pointers because the record resolves references
by copying, so a declaration per pointer turns a hundred-odd facts into tens of thousands and the
declared set stops being readable — which §8 already forbids by name. §3a settles the same question
for a vocabulary: *the entry, not the declaration site.* **An approximation's identity is
`(stating document, stating pointer, keyword)`, and every inlined occurrence resolves to it.**

**3a. §5's `if` ROW READS THROUGH A LOCAL REFERENCE THE RECORD MINTED.** Reading the document
through its own storage is right wherever it applies: `architecture.md` already decides that *a
reader asking what the document states reads through the storage*, because a reference to a storage
entry is not a fact the document states but where the fact is kept. The `if` row is such a reader.
Most unreadable conditions are unreadable for one reason: the record stores each distinct subtree
once, so the condition — or a property declaration inside it — was replaced by a reference to the
record's own `definitions`. **Read through that reference and the condition is readable and lowers
exactly, declaring nothing.**

**3b. A NEGATED PRESENCE-AND-VALUE CONDITION IS ONE COMPLEMENTED MATCH, AND `Match` CARRIES THE
COMPLEMENT.**

The condition the bundle writes most often is `not: {required: [k], properties: {k: {const: v}}}` —
the inner schema being *"k is present AND equals v"*. By De Morgan its negation is *"k is absent OR
k differs from v"*, which is not a disjunction no clause list can state. It is not a disjunction of
independent facts about different keys; it is **one predicate about one
key** — *k is not v, whether by absence or by value* — and a single clause says it the moment the
clause can say *not*.

**What the rule vocabulary lacks is a complement, not a disjunction.** The match primitive carries
a key, a two-state presence flag and a POSITIVE value set, so absence and a differing value cannot
both satisfy it: requiring presence fails the absent instance, requiring absence fails the present
one. **Presence becomes three-state — must be present, must be absent, immaterial — and the value
set gains its complement.** The condition above is then one clause: the key, presence immaterial,
value forbidden to be `v`. Absent satisfies it, present-and-different satisfies it,
present-and-equal does not — which is the negation exactly.

**THE THREE PRESENCE STATES AND THE VALUE SET'S COMPLEMENT ARE PROPERTIES OF THE PRIMITIVE, NOT OF
THE DIRECTION THEY WERE DERIVED FROM.** They are stated above by way of a negated condition, and
the immaterial state is not confined to the De Morgan step: a clause can say *absent, or one of
these*, because the primitive is built to.

Two conditions reduce to them **with no negation anywhere:**

- **A `properties` entry for a key NO `required` LIST NAMES IS THE IMMATERIAL STATE READ
  POSITIVELY.** Draft-07 reaches such an entry only where the key arrived, so the entry already
  says *absent, or present and in this set* — which is exactly that state, stated forwards.
- **A `not` over a `const` or an `enum` AT A PROPERTY DECLARATION is the complement read at a
  CLAUSE** rather than at a whole condition: the key, presence as the declaration gives it, and
  that value forbidden.

**AND THE COMPLEMENT NEGATES WHICHEVER PRESENCE STATE THE INNER CLAUSE CARRIES — three negations,
not one.** Reading the new inner state as the old one makes the condition hold at the ABSENT
instance where the document's negation does not, which is a **narrowing** and is the one error
worse than the widening being removed.

**AN ILLUSTRATION IS NOT A SCOPE, AND THIS DOCUMENT CANNOT MARK THE DIFFERENCE FOR THE READER — SO
THE RULE IS STATED OVER THE PRIMITIVE AND THE EXAMPLE IS MARKED AS ONE.** A capability introduced
beside the case that motivated it will be read as belonging to that case; every sentence here that
gives a mechanism must say what it ranges over, independently of where it was found.

Under the complement, these conditions **lower exactly and declare nothing**.

**A condition whose negation genuinely spans two keys still declares**, under sentence 1 — an
`anyOf` of requirements, or a negated conjunction over different keys, is a disjunction of clauses
and the vocabulary is right not to express it. The test is whether the disjunction is inside one
key's predicate or across several.

**4. `not oneOf` IS NOT EXPRESSIBLE AS A FORBIDDEN GROUP OVER THE UNION, and the attempt is a
narrowing in a rule rather than a gap.** `not oneOf` admits an
instance satisfying ZERO branches or TWO OR MORE, and a forbidden group over the union refuses an
instance satisfying two — which the document admits. **So the row's clause is withdrawn, and such a
node declares rather than lowers.** A rule that refuses what its document admits is the one outcome
§2 forbids outright.

**And the same cause has one more consequence, which is a WALK defect rather than a rule one:** a
count keyword withheld from a class whose extra policy drops the keys it counts is not answered by
declaring the count — it is answered by the class KEEPING the keys the document counts. Declaring
it would be declaring a difference the walk created. That reverses the `absent → ignore` reading at
exactly those nodes and nowhere else.

**A declaration earns its place by a value**: either a payload exists that
the document admits and the class now admits, or one exists that the document refuses and the class
admits, or the declaration is describing a difference no consumer can reach and it is deleted
rather than counted. Where nothing widens — the annotation admits exactly what the document admits,
and the only loss is which branch an overlapping payload becomes, which
no construction and no dump can observe — there is no declaration. §4's inseparable `oneOf` is a WIDENED
fact, because the model admits a payload the document refuses, and the construction shows it.

**A declaration is proved by the construction and by nothing else**: by a value the document admits and the
class accepts, at the pointer the declaration names. A declaration no value can prove is deleted
rather than graded. No derived keyword set, no equality between a declaration and what it renders,
and no pointer-translation rule stands beside that.

**The VERDICT count is not pinned, and a ceiling on it is the wrong instrument.** It is not
monotone under progress, in either direction: a row that clears unwritten code moves it DOWN
because documents' real obstruction turns out to be ours, and a row that unblocks documents moves
it UP because they get further and land on a verdict already decided elsewhere. Both moves are
documents progressing, and a ceiling that forbids the second while rewarding the first is §9's pin
with no denominator — it would oblige a row that unblocks a document to loosen it. What is pinned
instead is the SET, named by document, so a verdict arriving is attributable and a verdict arriving
for a NEW reason reddens. The figure to drive to zero is `refused`, and the verdict column is a
reading of it.

**What else is pinned, and what is only reported.** §9's rule that a pin with no denominator is
not a ratchet decides this. A round-trip failure in either direction is pinned at zero:
none of them moves with emission, because each is a disagreement between a model and its document
and a correct emitter produces none however many documents it emits. The approximation count is
**not pinned** — it rises when a document starts emitting, which would oblige every later change
to loosen the pin, the opposite of a ratchet — and is instead reported with its denominator (the
declared set) and split by attribution, with the *ours* half ratcheting down as §5's cells
land. **The split is necessary rather than tidy**: without it one keyword's gap moves *missing* by
every site that keyword occupies, every keyword's gap does that at once, and the pin is abandoned
on the first wave. With it, those facts are *approximated* against one cell-level attribution,
*missing* stays 0, and the figure that moves is the one that is supposed to move.

Pydantic is deliberately less strict than JSON Schema, so a payload the *document* refuses tells
us nothing about the generated class on either route. There is therefore no "refuses" check on
the model; the equivalent check confirms the schema half is wired to the class at all.

Every class, root model and alias the tree carries is paired with the schema node it names, and
all three checks run over that pairing. **The set every check ranges over is every
portable document of the bundle**, and under §2 every one of them emits, so there is no second
set to reason about: a document that does not appear in the pairing is a defect in the run.

A branch class of a union is paired with its branch node read
under the union's siblings: draft-07 applies every keyword beside the combinator to the same
instance the branch describes, so a field the branch inherits from the base is a fact its node
states and not one it added. A pair no value can be constructed for still has to pass the
construction, and names the case that blocked it.

**At a union in ANY position, not only a root one.** The reason above is draft-07's evaluation
rule, which does not care where the union sits.

So a sibling beside a union lowers by COMPOSITION and nothing is approximated: the siblings
become a base class, each branch becomes a subclass narrowing what it narrows, and the union is
over the subclasses. Where a branch also restates a property the siblings declare, the
restatement composes by the conjunct rule below — composition and intersection are the same
operation reached from two directions.

**The dual of that rule, for a node whose `type` is a LIST.** A class cut
out of a type list is paired with its node read at **its own type word**, not at the whole list.
The union-branch rule above adds the root's siblings because the branch describes the same
instance the root does; this one subtracts the list's other words for the mirror reason — the
class describes one member of the union and the other members are carried by the field holding
it, not by this class. Without it the same fact is counted twice and reported as a defect once:
the model is faithful at both pointers and only the pairing is wrong.

**A `properties` entry whose subschema is the EMPTY SCHEMA is not a fact these checks grade.**
§5's `additionalProperties` row already fixes the reading — "the empty
schema `{}` IS `true` and is read as `true` everywhere below" — and a `properties` entry stating
`{}` therefore constrains nothing. A document with no entry for a key and a model carrying
`properties: {key: {}}` admit exactly the same instances, so the entry is vacuous and reporting it
`added` counts a non-fact as a defect. One reading of the empty schema, two readers.

**The field half is the right one for `required` naming a property no declaration declares, and it
is EXACT.** `required: ["x"]` with no declaration for `x`
admits an object carrying `x` with any value, which is precisely a required field of type `Any` —
`Any` being what §5's `type` row already gives an absent type word. Nothing is widened, nothing is
dropped, and no declaration is owed. The rule half would report `differs /required`, because a rule
renders no `required` in a model's JSON schema, and the field half an `added` `properties` entry;
neither is a document's fault.

So a `null` member of a type list is the FIELD's fact, graded where the field is, and a member
class is graded against the case it actually describes.

**The third pairing rule, for a node at a CONJUNCT of an `allOf`.** A class, root model or
alias cut out at `…/allOf/N` is paired with its node read **as the composition** — the
intersection of every conjunct of that `allOf`, taken with the keywords stated beside the
`allOf`. Not with the conjunct's own text.

Draft-07's `allOf` holds every conjunct against the same instance, so a fact a sibling conjunct
states is a fact this node's instance must satisfy, not one this class added. Pairing against the
conjunct's own text instead reads every such fact as one this class ADDED, i.e. as a model
NARROWER than its document — so a reader pairing that way reports the faithful model as the defect.
A fact a sibling conjunct states is therefore never declarable.

This rule is what makes §5's `properties` row at CONJ gradable.

**A declaration is counted at the `SchemaRef` spelling of its pointer, and at no other.** A node
reached through an `allOf` conjunct has two spellings — the one the document
writes and the one §2's intersection produces, `{**child, "allOf": [base]}`, which puts an index
below every pointer the document has no `allOf` at. `render.declared_at` tests a prefix on ONE
spelling, `compiler.schema_ref`'s, and `compiler.schema_ref` is its sole producer; a declaration
written at the other spelling therefore attaches to the wrong class or to none.

**This is one rule and it settles several separate readings**, which is why it is stated here rather
than per site: one union reached under two spellings is one spelling question, not two defects — an
over-count in the declared backlog and an approximation instance no strict walk can resolve.

The reading that follows: §2 asks a declaration to be a fact §8 can look for in the document and
find. A pointer that resolves to nothing is not that, whatever it is counted against.

**An ANNOTATION is not a fact these three checks grade, at any pointer.** The predicate is
`bundle.is_an_annotation(keyword, position)` — §1's own, the one `record` already reads to settle
a `$ref`'s sibling. An annotation is a key whose cell compiles to no type, no field and no rule,
which is what "states nothing about acceptance" IS; so `added`, `missing` or `differs` on one
reports a difference that cannot change what a payload is accepted as, and these checks grade
acceptance.

Annotation COVERAGE is its own obligation, graded with §5's ergonomic rows and not among these
three: every description the document states reaches some emitted class. A check that mixes
acceptance with ergonomics reports a defect in one as a defect in the other.

### AN OVERRIDE MAY ASSERT, AND WHAT MAKES IT ADMISSIBLE IS THE DIRECTION

An annotation override is admissible because `seen_by_a_validator` is empty for it **by
construction** — it cannot change what a payload is accepted as, so byte-identity of the validator's
view is available as evidence. **An override that adds an ASSERTION gives that up: it changes
acceptance, which is the whole reason to add it.** So it needs its own admissibility, and the
evidence is not identity but **direction**.

**AN ASSERTING OVERRIDE MAY ONLY NARROW, AND THE SET IT REMOVES MUST BE ONE THE EMITTED CLASS
ALREADY REFUSES.** Then the override closes a gap between the document and the class **in the
document's favour**, which is the only direction that can be right: the schema was admitting what
nothing should accept, the class already said so, and the patch makes the document say it too. The
proof is a value — one the published node admits, the patched node refuses, and the class refuses —
with the class's reason named beside the document's.

**AND A WIDENING ASSERTION IS REFUSED OUTRIGHT, because it would let a class be called faithful by
loosening the schema under it.** That is the back door this whole ordering exists to close: a
compiler that cannot represent a constraint could otherwise delete the constraint and report
agreement. `load` refuses an entry whose patched node admits any value the published node refuses,
and the refusal names the value.

**THE ENTRY STILL DECLARES ITS DEFECT AND STILL FAILS WHEN THE DEFECT IS GONE.** Nothing about
asserting relaxes that: the published node already stating the keyword is an expired entry to
delete, not a conflict to overwrite. **An asserting entry is a schema defect written down with a
value attached, and the value is what distinguishes it from an opinion.**

A check is exhaustive over the set of nodes it claims, or it does not exist. A check that
enumerates a subset reports on that subset only, and says so.

---

## 9. Mistakes to avoid

Each is one sentence and its reason.

- **Code nobody has written is an APPROXIMATION, never a refusal.** Minting a permanent refusal
  for unwritten code reports clearable work as finished. §2 says unwritten code costs a declared
  widening and never a document, so the only refusal that survives is the record's own (§7). Do
  not charge a document for work we have not done — and *clearable* work stays visible, as the
  *ours* half of the approximation count, which ratchets down.
- **An approximation that narrows is not an approximation.** It is a model tighter than its
  document wearing a declaration, and §8's accepts construction is pointed at exactly that. Widen by
  another widening — to `Any` if nothing else carries it — rather than declaring the narrowing.
- **A declared approximation the model does not make is a stale excuse.** The construction cannot prove
  it — no value the document admits is newly accepted at that pointer — so it is deleted, because
  a declaration that outlives its widening hides the next real gap at the same pointer.
- **Do not pin the approximation count.** It rises whenever the emitted set grows, which is the
  next rule in this list. Pin the round-trip failures, which do not, and ratchet the *ours* split
  down.
- **Do not hand-write the set a generic check ranges over.** Derive it from the declaration the
  tables are read against (§8). A hand-written set is complete with respect to itself, so what it
  omits passes in both directions and nothing says so.
- **A keyword handled in code but named in none of §5, §6 or §7 is an invented rule.** Those
  tables are exhaustive by intent, and a rendering no section decided departs from the design as
  far as a decision nothing implements.
- **An exemption names an upstream issue, or it is this SDK's own decision and belongs in this
  document.** Attributing our own cost to upstream means waiting forever for someone else to fix
  it.
- **A pin with no denominator is not a ratchet.** A count that rises whenever the emitted set
  grows obliges every later change to loosen it, which is the opposite of what a
  ratchet is for. Pin what does not move with emission and derive the rest.
- **Never approximate on a keyword the walk itself inserted.** An approximation must name
  something the document states, or the document is blamed for the compiler's own rewriting —
  and the declaration then cannot be checked, because §8 looks for the fact in the document and
  does not find it.
- **A crash is not an outcome.** Every node reaches a lowering, and the document reaches emission
  or the one refusal §7 names. An unhandled type error names nothing and stops the run. Under §2
  the walk is total, and `approximate` is the one function a
  handler calls when it cannot render, reached by its own final case. A handler that raises
  instead is the defect this rule is about.
- **Do not decide one document's output by a census over the run.** A name, a case or an
  import that depends on which other documents the run includes makes a one-document emission
  and a whole-bundle emission disagree about the same document; §2 names every constrained
  scalar from its constraint alone for this reason.

 **THE RUN IS NOT THE BUNDLE, and that distinction is what §1's domain-scope collision rule
  rests on.** This prohibition is about the run's DOCUMENT SET — the argument list,
  which varies between `./check --why one-document.json` and a whole-bundle emission. The
  BUNDLE is neither: it is pinned, declared, and an input to every run alike, so a name derived
  from a bundle-wide reading is the SAME name in both, which is exactly the property this rule
  protects. So a census over the RUN is forbidden and a reading of the BUNDLE is not.

  What that costs is stated plainly: resolving a collision at domain scope needs the domain's
  other exported names, so naming can no longer be a function of one document and its reference
  closure. It becomes a function of the bundle, and the one-document path has to read the domain's
  exported names before it can name its own.

 **And the alternative is refused.** Making it a function of the
  run instead is one line, and the shipped artifact would be identical because the committed tree
  is always a whole-bundle run — but it leaves
  `test_one_documents_module_is_the_same_text_alone_as_with_the_whole_bundle` GREEN while the
  property it names is false for the documents behind the collisions, because its set does
  not include one of them. A test green on a false property is the defect that is never worth
  buying with one line.

 **THE ROOT AXIS IS A PARSE; A NESTED NAME IS A WALK.** A ROOT's name is a title and parse
  gives it, which is why the root axis is free. A NESTED name needs
  which positions exist and what kind each one is, and that is the WALK's decision, not the
  parse's: an untitled `enum` branch becomes a `Literal` and declares no class, §5's widenings drop
  a position outright, and §4's bare-`$ref` candidate takes its target's distinguishing remainder, which
  needs the target already named in §10's dependency order. A parse answering that would
  re-implement every one of those decisions, which is the second derivation §3 forbids.

  So the case is **two passes: walk and name with an empty surface, collect the exported symbols,
  walk and name again with the real one** — with **pass one ranging over
  the DOMAIN, not the bundle**, because the collision scope is the domain and a domain's membership
  is a function of the bundle, so the pass stays bundle-derived and §9 stays true.

  Where that still costs too much on the one-document path, the answer is a CACHE and not a
  shortcut: the export symbols are a function of the bundle, so they key on the bundle's content
  exactly as `tests/compiled.py` keys a compile. A miss costs the walk, a hit costs nothing, and a
  content address cannot go stale — which is why this is not a second derived artifact.
- **Do not decide a position the bundle does not hold from a view of it.** A case that appears
  only in a canonicalised or otherwise rewritten copy of a document is the copy's, and a row
  deciding it decides nothing the bundle states; the document of record (§3) is what the tables
  decide over.
